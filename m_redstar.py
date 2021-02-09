import asyncio
import re
import time
from queue import Queue
from queue import Empty
from typing import Union, List, Dict, Tuple, Callable, Coroutine, Awaitable, Any, TypeVar

import discord
from discord.ext import tasks

import params_rs as params
import player
from player import Player
from queue_manager import QueueManager

# module reference to Bot instance
bot: discord.Client

# DIRTY HACK
def convert_secs_to_time(seconds: int) -> str:
    if seconds < 60:
        seconds = int(round(seconds))
        return str(seconds) + 's'
    elif seconds < 3600:
        minutes = int(round(seconds / 60))
        return str(minutes) + 'm'
    else:
        hours = int(round(seconds / 3600))
        return str(hours) + 'h'

def convert_int_to_icon(number: int):
    if number == 1:
        return ':one:'
    elif number == 2:
        return ':two:'
    elif number == 3:
        return ':three:'
    elif number == 4:
        return '4' #params.RS4_EMOJI
    elif number == 5:
        return '5' #params.RS5_EMOJI
    elif number == 6:
        return '6' #params.RS6_EMOJI
    elif number == 7:
        return '7' #params.RS7_EMOJI
    elif number == 8:
        return '8' #params.RS8_EMOJI
    elif number == 9:
        return '9' #params.RS9_EMOJI
    elif number == 10:
        return '10' #params.RS10_EMOJI
    elif number == 11:
        return '11' #params.RS11_EMOJI
    else:
        return ':question:'

class Rs:

    qms = []
    queue_embeds = {}
    afk_warned_players = []
    afk_check_messages = {}
    time_last_queue_post = time.time()
    queue_status_embed = None
    last_help_message = None
    stats = {}

    # dict to handle open user dialogues (expecting a reaction to be closed)
    # key: discord.Message.id
    # value: discord.Member.id, discord.Channel.id and a
    #   List of Tuples, containing supported reaction emojis and their respective callback
    dialogues: Dict[int, Tuple[int, int, List[Tuple[str, Callable[[discord.Member], Awaitable[None]]]]]] = {}

    # job queue: callback and its args as list
    jobs = Queue()
    #Callable[..., Awaitable[None]], Tuple[Any, ...]]

    @staticmethod
    def init(bot_ref):
        global bot
        bot = bot_ref


        #r = (bot.get_guild(params.SERVER_DISCORD_ID).roles)
        #for role in r:
        #  print(role.name)

        # rs queue management (data storage)
        Rs.qm4 = QueueManager('rs4', 4, 0x000000,
                              discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                name=params.RS4_ROLE).mention)
        Rs.qm5 = QueueManager('rs5', 5, 0x000000,
                              discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                name=params.RS5_ROLE).mention)
        Rs.qm6 = QueueManager('rs6', 6, 0x000000,
                              discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                name=params.RS6_ROLE).mention)
        Rs.qm7 = QueueManager('rs7', 7, 0x000000,
                              discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                name=params.RS7_ROLE).mention)
        Rs.qm8 = QueueManager('rs8', 8, 0x000000,
                              discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                name=params.RS8_ROLE).mention)
        Rs.qm9 = QueueManager('rs9', 9, 0x000000,
                              discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                name=params.RS9_ROLE).mention)
        Rs.qm10 = QueueManager('rs10', 10, 0x000000,
                               discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                 name=params.RS10_ROLE).mention)
        Rs.qm11 = QueueManager('rs11', 11, 0x000000,
                               discord.utils.get(bot.get_guild(params.SERVER_DISCORD_ID).roles,
                                                 name=params.RS11_ROLE).mention)

        Rs.qms = [Rs.qm4, Rs.qm5, Rs.qm6, Rs.qm7, Rs.qm8, Rs.qm9, Rs.qm10, Rs.qm11]

        # queue status embed(s)
        Rs.queue_embeds = {'rs4': None, 'rs5': None, 'rs6': None, 'rs7': None, 'rs8': None,
                           'rs9': None, 'rs10': None, 'rs11': None, 'empty': None}
        Rs.queue_status_embed = None

        # message refs
        Rs.time_last_queue_post = time.time()
        # Rs.prev_disp_msgs = []
        # Rs.role_pick_messages = {}  # dict: key=discord_id, value=msg_id

        # afk handling
        Rs.afk_warned_players = []  # list of Player objects
        Rs.afk_check_messages = {}  # dict: key=discord_id, value=msg_id

        # rs run stats
        Rs.stats = {'rs4': 0, 'rs5': 0, 'rs6': 0, 'rs7': 0, 'rs8': 0,
                    'rs9': 0, 'rs10': 0, 'rs11': 0}
        Rs._read_rs_records()

    @staticmethod
    async def exit():
        return
        try:
            # delete any open afk checks
            for acm in Rs.afk_check_messages.values():
                await acm.delete(delay=params.MSG_DELETION_DELAY)
            # delete the main queue embed
            if Rs.queue_status_embed is not None:
                await Rs.queue_status_embed.delete(delay=params.MSG_DELETION_DELAY)
        except discord.NotFound:
            pass

    @staticmethod
    async def handle_reaction(user: discord.Member, reaction: discord.Reaction):
        """
        Reaction handler of Rs module
        :param user:
        :param reaction:
        :return:
        """

        msg = reaction.message
        msg_id = reaction.message.id

        # message is a dialogue message
        if msg_id in Rs.dialogues.keys():
            # check if the user reacting is the dialogue owner
            owner_id, chan_id, emoji_callbacks = Rs.dialogues[msg_id]
            if owner_id == user.id:
                # check supported emojis for this message
                for emo, callback in emoji_callbacks:
                    # emoji found -> call its callback function and close the dialogue
                    if reaction.emoji == emo:
                        print(f'Rs.handle_reaction(): {emo}: calling: {callback}')
                        #await callback(user)
                        Rs.add_job(callback, [user])
                        Rs.dialogues.pop(msg_id)
                        break

        # reactive queue system
        # for rs in Rs.queue_embeds.keys():
        #     rsqemb = Rs.queue_embeds[rs]
        #     if rsqemb is not None and rsqemb.id == msg_id:
        #         if reaction.emoji == params.START_EMOJI:
        #             print(f'Rs.handle_reaction(): {user} trying to start {rs} via reaction')
        #             await Rs.start_queue(user, level=int(str.replace(rs, 'RS', '')))
        #             pass
        #         elif reaction.emoji == params.JOIN_EMOJI:
        #             print(f'Rs.handle_reaction(): {user} trying to join {rs} via reaction')
        #             await Rs.enter_queue(user, level=int(str.replace(rs, 'RS', '')), caused_by_reaction=True)
        #             pass
        #         elif reaction.emoji == params.LEAVE_EMOJI:
        #             print(f'Rs.handle_reaction(): {user} trying to leave {rs} via reaction')
        #             await Rs.leave_queue(user, level=int(str.replace(rs, 'RS', '')), caused_by_reaction=True)

        # check if the reaction was added to a queue embed
        # for (rs, qemb) in Rs.queue_embeds.items():
        # if it was a queue embed
        # if qemb is not None and msg_id == qemb.id:
        if Rs.queue_status_embed is not None and msg_id == Rs.queue_status_embed.id:
            print(str(reaction.emoji))
            if reaction.emoji == params.LEAVE_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to leave all queues via reaction')
                # await Rs.leave_queue(user, caused_by_reaction=True)
                Rs.add_job(Rs.leave_queue, [user, 0, True, False, False, None])
            elif reaction.emoji == params.RS4_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to join RS4 via reaction')
                # await Rs.enter_queue(user, level=4, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 4, '', True, False])
            elif reaction.emoji == params.RS5_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to join RS5 via reaction')
                # await Rs.enter_queue(user, level=5, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 5, '', True, False])
            elif reaction.emoji == params.RS6_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to join RS6 via reaction')
                # await Rs.enter_queue(user, level=6, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 6, '', True, False])
            elif reaction.emoji == params.RS7_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to join RS7 via reaction')
                # await Rs.enter_queue(user, level=7, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 7, '', True, False])
            elif reaction.emoji == params.RS8_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to join RS8 via reaction')
                # await Rs.enter_queue(user, level=8, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 8, '', True, False])
            elif reaction.emoji == params.RS9_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to join RS9 via reaction')
                # await Rs.enter_queue(user, level=9, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 9, '', True, False])
            elif reaction.emoji == params.RS10_EMOJI:
                print(f'Rs.handle_reaction(): {user} trying to join RS10 via reaction')
                # await Rs.enter_queue(user, level=10, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 10, '', True, False])
            elif reaction.emoji == bot.get_emoji(params.RS11_EMOJI_ID):
                print(f'Rs.handle_reaction(): {user} trying to join RS11 via reaction')
                # await Rs.enter_queue(user, level=11, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 11, '', True, False])
            await Rs.queue_status_embed.remove_reaction(reaction.emoji, user)

    @staticmethod
    def get_qm(level: int):
        if level in params.SUPPORTED_RS_LEVELS:
            return Rs.qms[level-4]
        else:
            raise ValueError

    @staticmethod
    def add_job(callback, args):
        call_info = ''
        # most rs commands have discord.Member as first arg -> add as additional log info
        if len(args) > 0 and isinstance(args[0], discord.Member):
            call_info = 'for ' + args[0].name + '#' + args[0].discriminator
        print(f'Rs.add_job(): scheduled {callback.__name__}() {call_info}')

        # schedule job via queue
        Rs.jobs.put((callback, args))
        print(f'Rs.add_job(): {Rs.jobs.qsize()} job(s) left')

    @staticmethod
    @tasks.loop(seconds=0.2)
    async def task_process_queue():
        #while True:
        try:
            #await asyncio.sleep(0.1)

            # call to retrieve next job
            job = Rs.jobs.get_nowait()
            callback, args = job

            print(f'Rs.task_process_queue(): executing {callback.__name__}()')
            await callback(*args)

            print(f'Rs.task_process_queue(): {Rs.jobs.qsize()} job(s) left')

        except Empty:
            pass
        except discord.errors.HTTPException:
            print(f'Rs.task_process_queue(): discord.errors.HTTPException')
        except discord.DiscordException:
            print(f'Rs.task_process_queue(): generic discord exception')
        except Exception:
            print(f'Rs.task_process_queue(): generic exception {Exception}')

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_AFK_TASK_RATE)
    async def task_check_afk():
        """
        Cyclic afk check for all queued players
        :return: never returns
        """
        try:
            # for each RS queue
            for qm in Rs.qms:
                # ask QM for afk players
                afks = qm.get_and_update_afk_players()
                if len(afks) > 0:
                    print(f'task_check_afk(): {qm.name}: '
                             f'afk list: {[[a.discord_name, str(a.afk_timer)+"s"] for a in afks]}')

                # for each afk player
                for p in afks:

                    # not flagged as afk yet and no active warning -> flag and start timer
                    if p.afk_flag is False:
                        print(f'task_check_afk(): {qm.name}: warning player {p.discord_name}')
                        p.afk_flag = True

                        # sanity checks: if warning already exists -> delete and repost / deregister player
                        await Rs._delete_afk_check_msg(p.discord_id)
                        if p in Rs.afk_warned_players:
                            Rs.afk_warned_players.remove(p)

                        # send afk check msg
                        msg = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
                            f':warning: {p.discord_mention} still around? React ✅ below.')
                        await msg.add_reaction(params.CONFIRM_EMOJI)

                        # create user dialogue
                        Rs.dialogues[msg.id] = (p.discord_id, params.SERVER_RS_CHANNEL_ID,
                                                [(params.CONFIRM_EMOJI, Rs._reset_afk)])
                        # mark player as afk
                        Rs.afk_warned_players.append(p)
                        Rs.afk_check_messages[p.discord_id] = msg.id
                        print(f'task_check_afk(): new active warnings across all queues: '
                                 f'{[a.discord_name for a in Rs.afk_warned_players]}')

                        # await Rs.display_queues(repost=True)
                        Rs.add_job(Rs.display_queues, [True])

                    # already flagged and counting -> keep counting
                    elif p.afk_timer < params.TIME_AFK_KICK:
                        print(
                            f'task_check_afk(): {qm.name}: {p.discord_name} has been afk for {p.afk_timer}s (kicking after {params.TIME_AFK_KICK}s)')
                        p.afk_timer = p.afk_timer + params.TIME_BOT_AFK_TASK_RATE

                    # already flagged and timer reached -> kick
                    else:
                        # kick this player
                        print(f'task_check_afk(): {qm.name}: kicking player {p.discord_name}')
                        # await Rs.leave_queue(caller=None, caused_by_afk=True, player=p)
                        Rs.add_job(Rs.leave_queue, [None, 0, False, True, False, p])

                        # reset afk trackers
                        if p in Rs.afk_warned_players:
                            Rs.afk_warned_players.remove(p)
                        await Rs._delete_afk_check_msg(p.discord_id)

        except discord.errors.HTTPException:
            print(f'task_check_afk(): discord.errors.HTTPException')
        except discord.DiscordException:
            print(f'task_check_afk(): generic discord exception')
        except Exception:
            print(f'Rs.task_check_afk(): generic exception')


    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_Q_TASK_RATE)
    async def task_repost_q():
        """
        Cyclic reposting of running queues
        :return: never returns
        """
        try:
            print(f'Rs.task_repost_q(): executing...')
            Rs.add_job(Rs.display_queues, [])

        except discord.errors.HTTPException:
            print(f'Rs.task_repost_q(): discord.errors.HTTPException')
            pass
        except discord.DiscordException:
            print(f'Rs.task_repost_q(): generic discord exception')
            pass
        except Exception:
            print(f'Rs.task_repost_q(): generic exception')


    @staticmethod
    async def start_queue(caller: discord.Member, level: int = 0, ):
        """
        Force start of a queue (early start)
        :param caller:
        :param level: rs level of the queue to start
        :return:
        """

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} Invalid queue "RS{level}"')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        p = qm.find_player_in_queue_by_discord(caller)
        q = qm.queue
        authorized = False

        # player not in queue
        if p is None:
            # check this user's roles
            for r in caller.roles:
                # has admin/mod powers
                if r.name in params.SERVER_ADMIN_ROLES + params.SERVER_OFFICER_ROLES:
                    authorized = True
                    print(f'Rs.start_queue(): {caller} is authorized (moderator)')
                    break
        # player in queue -> authorized
        else:
            authorized = True
            print(f'Rs.start_queue(): {caller} is authorized (member)')

        # start the queue
        if authorized is True and len(q) > 0:
            await Rs._queue_ready(level)
        elif len(q) == 0:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} No RS{level} queue found!')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
        else:
            print(f'Rs.start_queue(): {caller} is not authorized')
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} Only queued players or @Moderators can force a start.')
            await m.delete(delay=params.MSG_DISPLAY_TIME)

    @staticmethod
    async def clear_queue(caller: discord.Member, level: int = 1):

        print(f'Rs.clear_queue(): called by {caller}')

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} Invalid queue "RS{level}"')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        p = qm.find_player_in_queue_by_discord(caller)
        q = qm.queue
        authorized = False

        # not in queue: check if admin or mod
        if p is None:
            for r in caller.roles:
                if r.name in (params.SERVER_ADMIN_ROLES + params.SERVER_OFFICER_ROLES):
                    authorized = True
                    print(f'Rs.clear_queue(): {caller} is authorized (admin/mod)')
                    if len(q) == 0:
                        m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} No RS{level} queue found!')
                        await m.delete(delay=params.MSG_DISPLAY_TIME)
                        print(f'Rs.clear_queue(): no rs{level} queue found. aborting')
                        return
                    break
        else:
            authorized = True
            print(f'Rs.clear_queue(): {caller} is authorized (member)')

        # clear the queue
        if authorized is True:
            if len(q) > 0:
                # remove potential afk check msgs
                for p in qm.queue:
                    await Rs._delete_afk_check_msg(p.discord_id)
                qm.clear_queue()
                m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} RS{level} queue cleared!')
                await m.delete(delay=params.MSG_DISPLAY_TIME)
                await Rs.display_queues(True)
            else:
                m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} No RS{level} queue found!')
                await m.delete(delay=params.MSG_DISPLAY_TIME)
        else:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
                f'{caller.mention} Only queued players or administrators can clear a queue.')
            await m.delete(delay=params.MSG_DISPLAY_TIME)

    @staticmethod
    async def enter_queue(caller: discord.Member,
                          level: int = 0,
                          comment: str = '',
                          caused_by_reaction: bool = False,
                          caused_by_mate_addition: bool = False
                          ):
        """
        Let a player join a queue
        :param comment:
        :param caller: the discord user calling the command
        :param level: [optional] the rs level
        :param caused_by_reaction: [optional] command was called via reaction
        :param caused_by_mate_addition:
        :param player: [optional] if already existing, the player object of this user
        :return:
        """

        # arg check: valid rs level
        if level not in params.SUPPORTED_RS_LEVELS and level != 0:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'rs{level}? Not in this galaxy. Try again!')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        auto_detect_rs = False

        # no level specified: check callers roles and auto detect highest RS level
        if level == 0:
            auto_detect_rs = True
            level = Rs.get_level_from_rs_role(caller)
            # couldn't find any RS roles
            if level == 0:
                m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'Sorry {caller.mention}, it appears you don\'t have an RS role yet.')
                await m.delete(delay=params.MSG_DISPLAY_TIME)
                return

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{caller.mention} Invalid queue "RS{level}"')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        queue = None
        queue_len = 0
        res = QueueManager.NOTHING
        player = None

        # next try to join this player
        print(f'Rs.enter_queue(): {caller} joining {qm.name}')
        res, player, queue = qm.new_player(Player(caller, note=comment))

        if queue is not None:
            queue_len = len(queue)

        if queue_len in params.PING_THRESHOLDS and (time.time() - qm.last_role_ping >= params.PING_COOLDOWN):
            ping_string = qm.role_mention
            qm.last_role_ping = time.time()
        else:
            ping_string = f'@rs{level}'

        # new in this queue -> standard join
        if res == QueueManager.PLAYER_JOINED:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{player.discord_nick} joined {ping_string} ({queue_len}/4).')
            await m.delete(delay=60)
            await Rs.display_queues(True)

        # open afk warning -> always reset when enter_queue is called
        for qmg in Rs.qms:
            # print(qmg.name)
            player = qmg.find_player_in_queue_by_discord(caller)
            # player found -> reset their afk status for other queues than the one joined
            if player is not None and qmg.level != qm.level:  # and player.afk_flag is True:
                print(f'Rs.enter_queue(): {caller} resetting all queue timers via enter_queue()')
                await Rs._reset_afk(caller)
                #res = QueueManager.PLAYER_RESET_AFK_FLAG
                break

        # ping all once queue hits 3/4 only
        #if queue_len in params.PING_THRESHOLDS:  # or queue_is_new is True:
            #await ctx.send(f'{ping_string} {queue_len}/4')

        # check if queue full
        if qm.get_queue_ready():
            await Rs._queue_ready(level)


    @staticmethod
    async def leave_queue(caller: Union[discord.Member, None],
                          level: int = 0,
                          caused_by_reaction: bool = False,
                          caused_by_afk: bool = False,
                          caused_by_other_queue_finished: bool = False,
                          player: Player = None
                          ):
        """

        :param caller: the discord user calling this command
        :param level: [optional] rs_level to leave. not specified: leave all levels
        :param caused_by_reaction:
        :param caused_by_afk:
        :param caused_by_other_queue_finished: if set, reverses the meaning of level (removing player from all queues EXCEPT level)
        :param player:
        :return:
        """

        # invalid input
        if level not in params.SUPPORTED_RS_LEVELS and level != 0:
            return

        # leaving specific queue only
        leaving_all_queues = True
        if level != 0:
            leaving_all_queues = False

        # player handle might  be provided or built from the user calling
        if player is None:
            player = Player(caller)

        # afk timeout
        if caused_by_afk is True:
            # try all queues and check if player can be removed from it
            for qm in Rs.qms:
                res, q = qm.player_left(player)
                if res == QueueManager.PLAYER_LEFT:
                    print(f'Rs.leave_queue(): {player.discord_name} leaving {qm.name} via afk_kick')
                    m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f':x: {player.discord_nick} timed out for {qm.name} ({len(q)}/4)')
                    await m.delete(delay=params.MSG_DISPLAY_TIME)
                    await Rs._delete_afk_check_msg(player.discord_id)

        # automatic removal due to another queue finishing [in this case, <rs> will be skipped!]
        elif caused_by_other_queue_finished is True:
            # try all queues and check if player can be removed from it
            for qm in Rs.qms:
                # invert level -> remove from all queues EXCEPT this one
                if level == qm.level:
                    continue
                # try to remove the player and report it
                res, q = qm.player_left(player)
                if res == QueueManager.PLAYER_LEFT:
                    print(f'Rs.leave_queue(): {player.discord_name} leaving {qm.name} via other_queue_finished')
                    m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
                        f':x: {player.discord_nick} removed from {qm.name} ({len(q)}/4)')
                    await m.delete(delay=params.MSG_DISPLAY_TIME)
                    #await Rs.display_queues()

        # reaction used
        elif caused_by_reaction:
            # try all queues and check if player can be removed from it
            for qm in Rs.qms:
                if leaving_all_queues is False and qm.level != level:
                    continue
                res, q = qm.player_left(player)
                lq = len(q)
                if res == QueueManager.PLAYER_LEFT:
                    print(f'Rs.leave_queue(): {player.discord_name} leaving {qm.name} via reaction')
                    m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'{params.LEAVE_EMOJI} {player.discord_nick} left {qm.name} ({lq}/4).')
                    await m.delete(delay=params.MSG_DISPLAY_TIME)
                    await Rs._delete_afk_check_msg(player.discord_id)
                   # await Rs.display_queues()

        # command used
        else:
            # lookup player in all queues
            for qm in Rs.qms:
                # try to find player in this queue
                player = qm.find_player_in_queue_by_discord(caller)
                # player not found OR specified rs level not matched -> retry
                if player is None or (qm.level != level and not leaving_all_queues):
                    continue
                # remove player
                res, q = qm.player_left(player)
                lq = len(q)
                if res == QueueManager.PLAYER_LEFT:
                    print(f'Rs.leave_queue(): {caller} leaving {qm.name} via command')
                    m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f':x: {player.discord_nick} left {qm.name} ({lq}/4).')
                    await m.delete(delay=params.MSG_DISPLAY_TIME)
                    await Rs._delete_afk_check_msg(player.discord_id)

        await Rs.display_queues(True)

    @staticmethod
    # async def display_queues(levels: List[int], force_update: bool = False):
    async def display_queues(force_update: bool = False):
        """

        :param force_update: force reposting the embed
        :return:
        """

        queues_to_display = []
        # no argument: print all queues
        if len(levels) == 0:
          queues_to_display = Rs.qms7
        # else only print selected queues
        else:
          queues_to_display = [Rs.get_qm(r) for r in levels]



        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name='', icon_url='') #params.BOT_DISCORD_ICON)
        embed.set_footer(text= params.TEXT_FOOTER_TEXT)
        inl = True
        any_queue_active = False

        # process all rs queues
        for j, qm in enumerate(Rs.qms):
        # for j, qm in enumerate(queues_to_display):

            secs_since_last_call = round(time.time() - Rs.time_last_queue_post[qm.name])
            if force_update is False and secs_since_last_call < params.TIME_Q_REPOST_COOLDOWN:
              print(f'Rs.display_queues(): skipping due to spam (last update: {secs_since_last_call}s ago)')
            return

            # queue is populated
            if len(qm.queue) > 0:
                queue_active = True

            # fetch the queue and add to embed
            q = qm.queue
            chan = bot.get_channel(params.SERVER_RS_CHANNEL_ID)
            # chan = bot.get_channel(params.RS_CHANNELS[qm.name])
            team = ''

            # for each player: make entry in embed
            for i, p in enumerate(q):

                # AFK warning
                if p.afk_flag is True:
                    warn_text = ' :warning: '
                else:
                    warn_text = ''

                if p.note != '':
                    note_text = f' ~ "_{p.note}_"'
                else:
                    note_text = ''

                # print player
                team = team + f'<0x7f><0x7f><0x7f><0x7f><0x7f> {p.discord_nick + warn_text + note_text} ' \
                              f':watch: {convert_secs_to_time(seconds=time.time() - p.timer)}\n'

            # build embed for this RS
            if team != '':
                #embed.add_field(name=f'rs{convert_int_to_icon(qm.level)} ({len(q)}/4)', value=team, inline=inl)
                #embed.add_field(name=f'{params.RS_ICON} {qm.level} ({len(q)}/4) ', #value=team, inline=inl)
                #inl = False
                embed.description = team

            # queue empty -> post with message
            if not queue_active:
                fch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
                embed.description = params.TEXT_EMPTY_QUEUE + fch.mention + '!'

            # post embed (first time)
            if Rs.queue_status_embed is None:
                await Rs._post_status_embed(embed)
            # edit er repost
            else:
                rs_chan = bot.get_channel(params.SERVER_RS_CHANNEL_ID)

                # last message is not the embed -> delete and repost, keep as is otherwise and just edit
                if rs_chan.last_message is not None and \
                        rs_chan.last_message.author.id != bot.user.id:
                    print('Rs.display_queues(): reposting')
                    await Rs.queue_status_embed.delete(delay=params.MSG_DELETION_DELAY)
                    await Rs._post_status_embed(embed)
                else:
                    await Rs.queue_status_embed.edit(embed=embed)
                    print('Rs.display_queues(): updated')

            Rs.time_last_queue_post[qm.name] = time.time()

    @staticmethod
    async def _post_status_embed(embed: discord.Embed):
        Rs.queue_status_embed = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(embed=embed)
        try:
            await Rs.queue_status_embed.add_reaction(params.RS4_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.RS5_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.RS6_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.RS7_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.RS8_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.RS9_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.RS10_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.RS11_EMOJI)
            await Rs.queue_status_embed.add_reaction(params.LEAVE_EMOJI)
        # already got deleted (discord)
        except discord.errors.NotFound:
            print('Rs._post_status_embed(): lost message handle (NotFound)')
            Rs.queue_status_embed = None
        except discord.DiscordException:
            print('Rs._post_status_embed(): generic DiscordException')
            pass

    @staticmethod
    async def _reset_afk(discord_user: discord.Member):

        players_queues = []

        # try all queues
        for qm in Rs.qms:
            # if player in queue
            p = qm.find_player_in_queue_by_discord(discord_user)
            if p is not None:
                # reset afk state
                p.afk_flag = False
                p.afk_timer = 0
                p.timer = time.time()
                if p in Rs.afk_warned_players:
                    Rs.afk_warned_players.remove(p)
                await Rs._delete_afk_check_msg(p.discord_id)
                # collect all affected queues
                players_queues.append(qm.name)

        # update all affected queues
        #for pq in players_queues:
        # await Rs.display_queues(True)
        Rs.add_job(Rs.display_queues, [True])
        # m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
        #     f':white_check_mark: {discord_user.display_name} you are in for {", ".join(players_queues)}!')
        # await m.delete(delay=params.MSG_DISPLAY_TIME)

        print(f'Rs._reset_afk(): pending afk warning for {discord_user} was reset')

    @staticmethod
    async def _delete_afk_check_msg(player_id):

        if player_id in Rs.afk_check_messages.keys():
            try:
                msg = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).fetch_message(Rs.afk_check_messages[player_id])
                await msg.delete(delay=params.MSG_DELETION_DELAY)
                Rs.afk_check_messages.pop(player_id)
            except discord.errors.NotFound:
                pass

    @staticmethod
    async def _queue_ready(level: int):
        """
        Handles the communication and clean-up of a completed queue.
        :param level: the rs level to start
        :return:
        """

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(f'Oops! Invalid queue "RS{level}". Call for help!')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        # ping all players
        pings = [p.discord_mention for p in qm.queue]
        msg = ', '.join(pings)
        msg = f'**RS**{convert_int_to_icon(qm.level)} ready! ' + msg + ' Meet where?\n'
        m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(msg)
        #await m.delete(delay=params.INFO_DISPLAY_TIME)

        # remove players from other queues and/or remove any pending afk checks if applicable
        for p in qm.queue:
            await Rs._delete_afk_check_msg(p.discord_id)
            await Rs.leave_queue(None, level=level, caused_by_other_queue_finished=True, player=p)

        # record & reset queue
        Rs._record_rs_run(level, qm.queue)
        qm.clear_queue()

        # update embed
        await asyncio.sleep(1)
        await Rs.display_queues(True)

    @staticmethod
    def get_level_from_rs_role(caller) -> int:
        player_roles = caller.roles
        level = 0
        for r in player_roles:
            # role must be 3 or 4 chars long, start with anycase "RS" followed by one or two digits
            if len(r.name) in range(3, 5) and re.match('[rR][sS][14-9][0-1]?', r.name):
                # extract rs level as integer and update highest if applicable
                rsr = int(re.match('[14-9][0-1]?', r.name[2:]).string)
                if rsr > level:
                    level = rsr
        return level

    @staticmethod
    async def display_queues_individually(name: str = '', level: int = 0, add_reactions: bool = True):
        """

        :param name: name of the queue_manager (e.g. 'rs7')
        :param level: level of the queue to be displayed
        :return:
        """

        # no arguments: display all
        if name == '' and level not in params.SUPPORTED_RS_LEVELS:
            pass

        any_queue_active = False

        # process all rs queues
        for qm in Rs.qms:

            # queue is populated
            if len(qm.queue) > 0:
                any_queue_active = True

            # empty queue: player just left -> delete embed
            else:
                # delete old embed of this qm
                if Rs.queue_embeds[qm.name] is not None:
                    await Rs.queue_embeds[qm.name].delete(delay=params.MSG_DELETION_DELAY)
                    Rs.queue_embeds[qm.name] = None
                # skip posting any embeds
                continue

            # specific queue requested -> skip if this qm is not the specified one
            if (name != '' and name != qm.name) or (level in params.SUPPORTED_RS_LEVELS and level != qm.level):
                continue
                pass

            # make sure that the placeholder for "all queues empty" is removed
            if Rs.queue_embeds['empty'] is not None:
                await Rs.queue_embeds['empty'].delete(delay=params.MSG_DELETION_DELAY)
                Rs.queue_embeds['empty'] = None

            # fetch the queue and build embed
            q = qm.queue
            embed = discord.Embed(color=params.EMBED_QUEUE_COLOR)
            embed.title = qm.name + f' Queue ({len(q)}/4)'
            team = ''

            # for each player: make entry in embed
            for i, p in enumerate(q):

                # AFK warning
                if p.afk_flag is True:
                    warn_text = ' :warning: '
                else:
                    warn_text = ''

                if p.note != '':
                    note_text = f' - "_{p.note}_"'
                else:
                    note_text = ''

                # print player
                team = team + f'{convert_int_to_icon(i+1)}\t {p.discord_nick + warn_text + note_text}  ' \
                              f':watch: {convert_secs_to_time(seconds=time.time()-p.timer)}\n'

            queue_age = qm.get_queue_age(q)
            embed.description = team
            embed.set_footer(text=f'Queue started {convert_secs_to_time(seconds=time.time()-queue_age)} ago.')

            # update queue embed
            if Rs.queue_embeds[qm.name] is not None:
                await Rs.queue_embeds[qm.name].delete(delay=params.MSG_DELETION_DELAY)
            Rs.queue_embeds[qm.name] = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(embed=embed)

            # reactive queue system
            if add_reactions:
                try:
                    await Rs.queue_embeds[qm.name].add_reaction(params.JOIN_EMOJI)
                    await Rs.queue_embeds[qm.name].add_reaction(params.LEAVE_EMOJI)
                    await Rs.queue_embeds[qm.name].add_reaction(params.START_EMOJI)
                # already got deleted (discord)
                except discord.errors.NotFound:
                    pass
                # already got deleted (srv object)
                except AttributeError:
                    pass

        # all queues empty -> send special embed
        if not any_queue_active:
            embed = discord.Embed(color=params.EMBED_QUEUE_COLOR)
            embed.title = 'No running queues!'
            embed.description = params.TEXT_EMPTY_QUEUE
            # update embed
            if Rs.queue_embeds['empty'] is not None:
                await Rs.queue_embeds['empty'].delete(delay=params.MSG_DELETION_DELAY)
            m = Rs.queue_embeds['empty'] = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(embed=embed)
            await m.delete(delay=params.INFO_DISPLAY_TIME)

        # spam brake
        time.sleep(params.TIME_SPAM_BRAKE)

        # in any case: something was posted, so remember the time
        Rs.time_last_queue_msg = time.time()

    @staticmethod
    async def show_help(ctx):

        await ctx.message.delete(delay=params.MSG_DELETION_DELAY)

        if Rs.last_help_message is not None:
            await Rs.last_help_message.delete(delay=params.MSG_DELETION_DELAY)

        embed = discord.Embed(color=params.EMBED_COLOR)
        embed.set_author(name='RS Queue Help', icon_url=params.BOT_DISCORD_ICON)
        embed.set_footer(text=f'Called by {ctx.author.display_name}\nDeleting in 2 min.')
        embed.add_field(name="`!rs`", value="Hide (mute) or unhide this channel.", inline=False)
        embed.add_field(name="`!in`", value="Sign up for your highest RS level.", inline=False)
        embed.add_field(name="`!in X [note]`", value="Sign up for RS level X (optional: with note).", inline=False)
        embed.add_field(name="`!out`", value="Leave all queues.", inline=False)
        embed.add_field(name="`!out X`", value="Leave queue of RS level X.", inline=False)
        embed.add_field(name="`!q`", value="Display running queues.", inline=False)
        embed.add_field(name="`!start X`", value="Early start RS level X queue.", inline=False)
        embed.add_field(name="`!clear X`", value="Clear queue for RS level X.", inline=False)
        Rs.last_help_message = await ctx.channel.send(content=None, embed=embed)
        await Rs.last_help_message.delete(delay=2*60)

    @staticmethod
    def _record_rs_run(rs_level: int, queue: List[player.Player]):
        if rs_level not in params.SUPPORTED_RS_LEVELS:
            print(f'record_rs_run(): {rs_level} not a valid level, skipping')
            return

        plist = ''
        for p in queue:
            plist = plist + f'{p.discord_name} ({p.discord_id}); '
        line = f'{time.asctime()}\tRS{rs_level}:\t{len(queue)}/4:\t{plist}'

        print(line)

        #completed_queues_file = open("rs/completed_queues.txt", "a", encoding="utf-8")
        #completed_queues_file.write(line + '\n')
        #completed_queues_file.flush()
        #completed_queues_file.close()

        Rs.stats[f'rs{rs_level}'] += 1


    @staticmethod
    def _read_rs_records():

        #completed_queues_file = open("rs/completed_queues.txt", "r", encoding="utf-8")
        queues = [] #completed_queues_file.readlines()

        for q in queues:
            tokens = q.split('\t')
            qm_name = tokens[1].replace(':', '')
            q_len = int(tokens[2].split('/')[1].replace(':', ''))
            if q_len > 0:
                Rs.stats[qm_name] += 1

        #completed_queues_file.close()
