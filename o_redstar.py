import asyncio
import re
import time
from queue import Queue
from queue import Empty
from typing import Union, List, Dict, Tuple, Callable, Coroutine, Awaitable, Any, TypeVar
import logging
logger = logging.getLogger()

import discord
from discord.ext import tasks

import params_rs as params
import player
from player import Player
from queue_manager import QueueManager
# from util import Util

# module reference to Bot instance
bot: discord.Client
star_range = params.SUPPORTED_RS_LEVELS
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

def convert_emoji_to_int(reaction: str):
  e2i={}
  for i in Rs.star_range :
    e = (f'RS{i}_EMOJI')
    e2i[getattr(params,e)] = i
  return e2i[reaction]

def convert_int_to_icon(number: int):
  i2e={}
  for i in Rs.star_range :
    n = (f'RS{i}_EMOJI')
    i2e[i] = [getattr(params,n)]
  return i2e[number]

class Rs:

    qms = []
    queue_embeds = {}
    afk_warned_players = []
    afk_check_messages = {}
    time_last_queue_post = time.time()
    queue_status_embed = None
    last_help_message = None
    stats = {}
    rs_roles = {}
    guild: discord.Guild = None
    star_range = params.SUPPORTED_RS_LEVELS

    # dict to handle open user dialogues (expecting a reaction to be closed)
    # key: discord.Message.id
    # value: discord.Member.id, discord.Channel.id and a
    #   List of Tuples, containing supported reaction emojis and their respective callback
    dialogues: Dict[int, Tuple[int, int,
                               List[Tuple[str,
                                          Callable[[discord.Member],
                                                   Awaitable[None]]]]]] = {}

    # job queue: callback and its args as list
    jobs = Queue()
    #Callable[..., Awaitable[None]], Tuple[Any, ...]]

    @staticmethod
    def init(bot_ref):
        global bot
        bot = bot_ref
        Rs.guild = bot.get_guild(params.SERVER_DISCORD_ID)
        #get the discord.Role(s) for people who are allowed to join
        for emoji, role_name in zip(params.RS_EMOJIS[-8:], params.RS_ROLES[-8:]):
            role = discord.utils.get(Rs.guild.roles, name=role_name)
            if role:
                Rs.rs_roles[emoji] = role
            else:
                logger.error(f"unable to retrieve role {role_name}, bot will NOT operate as intended")
                raise Exception(f"unable to retrieve role {role_name}, bot will NOT operate as intended")
        
        # rs queue management (data storage)        
        for i in range(4, 12) :
            role = discord.utils.get(
              Rs.guild.roles, name = getattr ( params, f'RS{i}_ROLE' )
              ).mention
            globals()[f'qm{i}'] = QueueManager( f'RS{i}', i, 0xff3300, role)
        RSqms = [ 0, 1, 2, 3, qm4, qm5, qm6, qm7, qm8, qm9, qm10, qm11 ]
        Rs.qms = RSqms [min(star_range) : max(star_range)+1]

        # queue status embed(s)
        for i in Rs.star_range :
            Rs.queue_embeds [i - min(Rs.star_range)] = (f'RS{i} : None')
        
        Rs.queue_status_embed = None

        # message refs
        Rs.time_last_queue_post = time.time()
        # Rs.prev_disp_msgs = []
        # Rs.role_pick_messages = {}  # dict: key=discord_id, value=msg_id

        # afk handling
        Rs.afk_warned_players = []  # list of Player objects
        Rs.afk_check_messages = {}  # dict: key=discord_id, value=msg_id

        # rs run stats
        for i in Rs.star_range :
            Rs.stats[i-min(Rs.star_range)] = (f'RS{i} : 0')

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
                await Rs.queue_status_embed.delete(
                    delay=params.MSG_DELETION_DELAY)
        except discord.NotFound:
            pass

    @staticmethod
    async def handle_reaction(user: discord.Member,
                              reaction: discord.Reaction):
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
                        print(
                            f'Rs.handle_reaction(): {emo}: calling: {callback}'
                        )
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
          
            player_own_queue = None
            #player_own_queue = Rs.qms[convert_emoji_to_int(str(reaction.emoji))].find_player_in_queue_by_discord(user)

            if reaction.emoji == params.LEAVE_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to leave all queues via reaction'
                )
                Rs.add_job(Rs.leave_queue, [user, 0, True, False, False, None])

            elif player_own_queue != None : # not working can't check if player already in queue, see commented above
                Rs.add_job(Rs.leave_queue, [user, 0, False, False, False, None])
                await msg.channel.send(f"` {user.display_name} has left RS{convert_emoji_to_int(str(reaction.emoji))} queue `", delete_after = params.MSG_DELETION_DELAY)
                
            elif params.RS_ROLES[convert_emoji_to_int(str(reaction.emoji)) - 4 ] not in [ro.name for ro in user.roles]:
                await msg.channel.send(f"` {user.display_name}, you haven't set ping level for RS{convert_emoji_to_int(str(reaction.emoji))} `", delete_after = params.MSG_DELETION_DELAY)
                
            elif params.RESTRICTING_ROLES[convert_emoji_to_int(str(reaction.emoji)) - 4 ] in [ro.name for ro in user.roles]:
                await msg.channel.send(f"` We are sorry {user.display_name}, but you can't join RS{convert_emoji_to_int(str(reaction.emoji))} queue `", delete_after = params.MSG_DELETION_DELAY)
            
            elif reaction.emoji == params.RS4_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to join RS4 via reaction'
                )
                # await Rs.enter_queue(user, level=4, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 4, '', True, False])

            elif reaction.emoji == params.RS5_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to join RS5 via reaction'
                )
                # await Rs.enter_queue(user, level=5, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 5, '', True, False])

            elif reaction.emoji == params.RS6_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to join RS6 via reaction'
                )
                # await Rs.enter_queue(user, level=6, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 6, '', True, False])

            elif reaction.emoji == params.RS7_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to join RS7 via reaction'
                )
                # await Rs.enter_queue(user, level=7, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 7, '', True, False])

            elif reaction.emoji == params.RS8_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to join RS8 via reaction'
                )
                # await Rs.enter_queue(user, level=8, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 8, '', True, False])

            elif reaction.emoji == params.RS9_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to join RS9 via reaction'
                )
                # await Rs.enter_queue(user, level=9, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 9, '', True, False])
            elif reaction.emoji == params.RS10_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to join RS10 via reaction'
                )
                # await Rs.enter_queue(user, level=10, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 10, '', True, False])

            elif convert_emoji_to_int(str(reaction.emoji)) == 11 :
                print( 
                    f'Rs.handle_reaction(): {user} trying to join RS11 via reaction'
                )
                # await Rs.enter_queue(user, level=11, caused_by_reaction=True)
                Rs.add_job(Rs.enter_queue, [user, 11, '', True, False])

            await Rs.queue_status_embed.remove_reaction(reaction.emoji, user)

    @staticmethod
    def get_qm(level: int):
        if level in params.SUPPORTED_RS_LEVELS:
            return Rs.qms[ level - min(star_range) ]
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
        dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
        try:
            await asyncio.sleep(0.1)

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
        except discord.DiscordException as e:
            await dbg_ch.send(f':warning: **ERROR**: Rs.task_process_queue(): generic discord exception {str(e)}')
        except Exception as e:
            await dbg_ch.send(f':warning: **ERROR**: Rs.task_process_queue(): generic exception: {str(e)}')

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_AFK_TASK_RATE)
    async def task_check_afk():
        """
        Cyclic afk check for all queued players
        :return: never returns
        """
        dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
        try:
            # for each RS queue
            for qm in Rs.qms:
                # ask QM for afk players
                afks = qm.get_and_update_afk_players()
                if len(afks) > 0:
                    print(
                        f'task_check_afk(): {qm.name}: '
                        f'afk list: {[[a.discord_name, str(a.afk_timer)+"s"] for a in afks]}'
                    )

                # for each afk player
                for p in afks:

                    # not flagged as afk yet and no active warning -> flag and start timer
                    if p.afk_flag is False:
                        print(
                            f'task_check_afk(): {qm.name}: warning player {p.discord_name}'
                        )
                        p.afk_flag = True

                        # sanity checks: if warning already exists -> delete and repost / deregister player
                        await Rs._delete_afk_check_msg(p.discord_id)
                        if p in Rs.afk_warned_players:
                            Rs.afk_warned_players.remove(p)

                        # send afk check msg
                        msg = await bot.get_channel(
                            params.SERVER_RS_CHANNEL_ID).send(
                            f'` ⚠️ {p.discord_mention} still around? Confirm below. `'
                        )
                        await msg.add_reaction(params.CONFIRM_EMOJI)

                        # create user dialogue
                        Rs.dialogues[msg.id] = (p.discord_id,
                                                params.SERVER_RS_CHANNEL_ID, [
                                                    (params.CONFIRM_EMOJI,
                                                     Rs._reset_afk)
                                                ])
                        # mark player as afk
                        Rs.afk_warned_players.append(p)
                        Rs.afk_check_messages[p.discord_id] = msg.id
                        print(
                            f'task_check_afk(): new active warnings across all queues: '
                            f'{[a.discord_name for a in Rs.afk_warned_players]}'
                        )

                        # await Rs.display_queues(repost=True)
                        Rs.add_job(Rs.display_queues, [True])

                    # already flagged and counting -> keep counting
                    elif p.afk_timer < params.TIME_AFK_KICK:
                        print(
                            f'task_check_afk(): {qm.name}: {p.discord_name} has been afk for {p.afk_timer}s (kicking after {params.TIME_AFK_KICK}s)'
                        )
                        p.afk_timer = p.afk_timer + params.TIME_BOT_AFK_TASK_RATE

                    # already flagged and timer reached -> kick
                    else:
                        # kick this player
                        print(
                            f'task_check_afk(): {qm.name}: kicking player {p.discord_name}'
                        )
                        # await Rs.leave_queue(caller=None, caused_by_afk=True, player=p)
                        Rs.add_job(Rs.leave_queue,
                                   [None, 0, False, True, False, p])

                        # reset afk trackers
                        if p in Rs.afk_warned_players:
                            Rs.afk_warned_players.remove(p)
                        await Rs._delete_afk_check_msg(p.discord_id)
        
        except discord.errors.HTTPException:
            print(f'task_check_afk(): discord.errors.HTTPException')
        except discord.DiscordException as e:
            await dbg_ch.send(f':warning: **ERROR**: Rs.task_process_queue(): generic discord exception {str(e)}')
        except Exception as e:
            await dbg_ch.send(f':warning: **ERROR**: Rs.task_process_queue(): generic exception: {str(e)}')
            
    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_Q_TASK_RATE)
    async def task_repost_q():
        """
        Cyclic reposting of running queues
        :return: never returns
        """
        dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
        try:
            print(f'Rs.task_repost_q(): executing...')
            Rs.add_job(Rs.display_queues, [])
        except discord.errors.HTTPException:
            print(f'Rs.task_repost_q(): discord.errors.HTTPException')
            pass
        except discord.DiscordException as e:
            await dbg_ch.send(f':warning: **ERROR**: Rs.task_process_queue(): generic discord exception {str(e)}')
            pass
        except Exception as e:
            await dbg_ch.send(f':warning: **ERROR**: Rs.task_process_queue(): generic exception: {str(e)}')

    @staticmethod
    async def start_queue(
        caller: discord.Member,
        level: int = 0,
    ):
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
            m = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID).send(f'` {caller.mention} Invalid queue "RS{level}" `')
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
                if r.name in params.SERVER_ADMIN_ROLES + params.SERVER_MODERATOR_ROLES:
                    authorized = True
                    print(
                        f'Rs.start_queue(): {caller} is authorized (moderator)'
                    )
                    break
        # player in queue -> authorized
        else:
            authorized = True
            print(f'Rs.start_queue(): {caller} is authorized (member)')

        # start the queue
        if authorized is True and len(q) > 0:
            await Rs._queue_ready(level)
        elif len(q) == 0:
            m = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID
            ).send(f'` {caller.mention} No RS{level} queue found! `')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
        else:
            print(f'Rs.start_queue(): {caller} is not authorized')
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
                f'` {caller.mention} Only queued players or @Moderators can force a start. `'
            )
            await m.delete(delay=params.MSG_DISPLAY_TIME)

    @staticmethod
    async def clear_queue(caller: discord.Member, level: int = 1):

        print(f'Rs.clear_queue(): called by {caller}')

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            m = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID
            ).send(f'` {caller.mention} Invalid queue "RS{level}" `')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        p = qm.find_player_in_queue_by_discord(caller)
        q = qm.queue
        authorized = False

        # not in queue: check if admin or mod
        if p is None:
            for r in caller.roles:
                if r.name in (params.SERVER_ADMIN_ROLES +
                              params.SERVER_MODERATOR_ROLES):
                    authorized = True
                    print(
                        f'Rs.clear_queue(): {caller} is authorized (admin/mod)'
                    )
                    if len(q) == 0:
                        m = await bot.get_channel(
                            params.SERVER_RS_CHANNEL_ID
                        ).send(f'` {caller.mention} No RS{level} queue found! `')
                        await m.delete(delay=params.MSG_DISPLAY_TIME)
                        print(
                            f'Rs.clear_queue(): no rs{level} queue found. aborting'
                        )
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
                m = await bot.get_channel(
                    params.SERVER_RS_CHANNEL_ID
                ).send(f'` {caller.mention} RS{level} queue cleared! `')
                await m.delete(delay=params.MSG_DISPLAY_TIME)
                await Rs.display_queues(True)
            else:
                m = await bot.get_channel(
                    params.SERVER_RS_CHANNEL_ID
                ).send(f'` {caller.mention} No RS{level} queue found! `')
                await m.delete(delay=params.MSG_DISPLAY_TIME)
        else:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
                f'` {caller.mention} Only queued players or administrators can clear a queue. `'
            )
            await m.delete(delay=params.MSG_DISPLAY_TIME)

    @staticmethod
    async def enter_queue(caller: discord.Member,
                          level: int = 0,
                          comment: str = '',
                          caused_by_reaction: bool = False,
                          caused_by_mate_addition: bool = False):
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
            m = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID
            ).send(f'RS{level}? Not in this galaxy. Try again!')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        auto_detect_rs = False

        # no level specified: check callers roles and auto detect highest RS level
        if level == 0:
            auto_detect_rs = True
            level = Rs.get_level_from_rs_role(caller)
            # couldn't find any RS roles
            if level == 0:
                m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
                    f'` Sorry {caller.mention}, it appears you don\'t have an RS role yet. `'
                )
                await m.delete(delay=params.MSG_DISPLAY_TIME)
                return

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            m = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID
            ).send(f'{caller.mention} Invalid queue "RS{level}"')
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

        if queue_len in params.PING_THRESHOLDS and (
                time.time() - qm.last_role_ping >= params.PING_COOLDOWN):
            ping_string = qm.role_mention
            qm.last_role_ping = time.time()
        else:
            ping_string = f'@rs{level}'

        # new in this queue -> standard join
        if res == QueueManager.PLAYER_JOINED:
            m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(
                f'` {player.discord_nick} joined {ping_string} ({queue_len}/4). `'
            )
            await m.delete(delay=0)
            await Rs.display_queues(True)

        # open afk warning -> always reset when enter_queue is called
        for qmg in Rs.qms:
            player = qmg.find_player_in_queue_by_discord(caller)
            # player found -> reset their afk status for other queues than the one joined
            if player is not None and qmg.level != qm.level:  # and player.afk_flag is True:
                print(
                    f'Rs.enter_queue(): {caller} resetting all queue timers via enter_queue()'
                )
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
                          player: Player = None):
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
                    print(
                        f'Rs.leave_queue(): {player.discord_name} leaving {qm.name} via afk_kick'
                    )
                    m = await bot.get_channel(
                        params.SERVER_RS_CHANNEL_ID
                    ).send(
                        f'` {player.discord_nick} timed out for {qm.name} ({len(q)}/4) `'
                    )
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
                    print(
                        f'Rs.leave_queue(): {player.discord_name} leaving {qm.name} via other_queue_finished'
                    )
                    m = await bot.get_channel(
                        params.SERVER_RS_CHANNEL_ID
                    ).send(
                        f'` {player.discord_nick} removed from {qm.name} ({len(q)}/4) `'
                    )
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
                    print(
                        f'Rs.leave_queue(): {player.discord_name} leaving {qm.name} via reaction'
                    )
                    m = await bot.get_channel(
                        params.SERVER_RS_CHANNEL_ID
                    ).send(
                        f'` {player.discord_nick} left {qm.name} ({lq}/4) `'
                    )
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
                if player is None or (qm.level != level
                                      and not leaving_all_queues):
                    continue
                # remove player
                res, q = qm.player_left(player)
                lq = len(q)
                if res == QueueManager.PLAYER_LEFT:
                    print(
                        f'Rs.leave_queue(): {caller} leaving {qm.name} via command'
                    )
                    m = await bot.get_channel(
                        params.SERVER_RS_CHANNEL_ID
                    ).send(
                        f'` {player.discord_nick} left {qm.name} ({lq}/4) `')
                    await m.delete(delay=params.MSG_DISPLAY_TIME)
                    await Rs._delete_afk_check_msg(player.discord_id)

        await Rs.display_queues(True)

    @staticmethod
    async def display_queues(force_update: bool = False, footer_text: str = params.TEXT_FOOTER_TEXT):
        """

        :param force_update: force reposting the embed
        :return:
        """

        secs_since_last_call = round(time.time() - Rs.time_last_queue_post)
        if force_update is False and secs_since_last_call < params.TIME_Q_REPOST_COOLDOWN:
            print(
                f'Rs.display_queues(): skipping due to spam (last update: {secs_since_last_call}s ago)'
            )
            return

        embed = discord.Embed(color=params.EMBED_QUEUE_COLOR)
        embed.set_author(name='', icon_url='')
        embed.set_footer(text=footer_text)
        inl = True
        any_queue_active = False

        # process all rs queues
        for j, qm in enumerate(Rs.qms):

            # queue is populated
            if len(qm.queue) > 0:
                any_queue_active = True

            # fetch the queue and add to embed
            q = qm.queue
            team = ''

            # for each player: make entry in embed
            for i, p in enumerate(q):

                # AFK warning
                if p.afk_flag is True:
                    warn_text = ' ⚠️ '
                else:
                    warn_text = ''

                if p.note != '':
                    note_text = f' ~ "_{p.note}_"'
                else:
                    note_text = ''

                # print player
                team = team + f'\x7f\x7f\x7f {p.discord_nick + warn_text + note_text} ' \
                              f':watch: {convert_secs_to_time(seconds=time.time() - p.timer)}\n'

            # add the entry to embed
            if team != '':
                if '♾' in team:
                    team = team.replace('♾', '\\♾')
                embed.add_field(
                    name=f'{params.RS_ICON}  {(qm.level)} ({len(q)}/4)',
                    value=team,
                    inline=inl)
                inl = False

        # all queues empty -> post with message
        if not any_queue_active:
            fch = bot.get_channel(params.SERVER_BUG_CHANNEL_ID)
            embed.description = f'Start a new queue by typing `!in` or reacting below!\n Questions? `!help`\nBugs or Ideas? Please report them in {fch.mention}!'

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
                await Rs.queue_status_embed.delete(
                    delay=params.MSG_DELETION_DELAY)
                await Rs._post_status_embed(embed)
            else:
                await Rs.queue_status_embed.edit(embed=embed)
                print('Rs.display_queues(): updated')

        Rs.time_last_queue_post = time.time()

    @staticmethod
    async def _post_status_embed(embed: discord.Embed):
        Rs.queue_status_embed = await bot.get_channel(
            params.SERVER_RS_CHANNEL_ID).send(embed=embed)
        dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
        try:
            e2i={}
            for i in Rs.star_range :
              e = (f'RS{i}_EMOJI')
              await Rs.queue_status_embed.add_reaction(getattr(params,e))
            await Rs.queue_status_embed.add_reaction(params.LEAVE_EMOJI)
                
        except discord.errors.NotFound:
            print('Rs._post_status_embed(): lost message handle (NotFound)')
            Rs.queue_status_embed = None
        except discord.DiscordException as e:
            await dbg_ch.send(f':warning: **ERROR**: Rs.task_process_queue(): generic discord exception {str(e)}')
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

        print(
            f'Rs._reset_afk(): pending afk warning for {discord_user} was reset'
        )

    @staticmethod
    async def _delete_afk_check_msg(player_id):

        if player_id in Rs.afk_check_messages.keys():
            try:
                msg = await bot.get_channel(
                    params.SERVER_RS_CHANNEL_ID
                ).fetch_message(Rs.afk_check_messages[player_id])
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
            m = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID
            ).send(f'` Oops! Invalid queue "RS{level}". Call for help! `')
            await m.delete(delay=params.MSG_DISPLAY_TIME)
            return

        # ping all players
        pings = [p.discord_mention for p in qm.queue]
        msg = ', '.join(pings)
        msg = f'**RS**{convert_int_to_icon(qm.level)} ready! ' + msg + ' Meet where?\n'
        m = await bot.get_channel(params.SERVER_RS_CHANNEL_ID).send(msg)
        
        # remove players from other queues and/or remove any pending afk checks if applicable
        for p in qm.queue:
            await Rs._delete_afk_check_msg(p.discord_id)
            await Rs.leave_queue(None,
                                 level=level,
                                 caused_by_other_queue_finished=True,
                                 player=p)

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
            # role must be 3 or 4 chars long, start with anycase "VRS" followed by one or two digits
            if len(r.name) in range(3, 5) and re.match('[vR][rR][sS][14-9][0-1]?',
                                                       r.name):
                # extract rs level as integer and update highest if applicable
                rsr = int(re.match('[14-9][0-1]?', r.name[2:]).string)
                if rsr > level:
                    level = rsr
        return level

    @staticmethod
    def get_level_from_rs_roles(caller) -> list:
        player_roles = caller.roles
        levels = []
        for r in player_roles:
            # role must be 3 or 4 chars long, start with anycase "VRS" followed by one or two digits
            if len(r.name) in range(3, 5) and re.match('[vR][rR][sS][14-9][0-1]?',
                                                       r.name):
                # extract rs level as integer and update highest if applicable
                rsr = int(re.match('[14-9][0-1]?', r.name[2:]).string)
                levels.append(rsr)
        return levels

    @staticmethod
    async def display_queues_individually(name: str = '',
                                          level: int = 0,
                                          add_reactions: bool = True):
        """

        :param name: name of the queue_manager (e.g. 'RS7')
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
                    await Rs.queue_embeds[
                        qm.name].delete(delay=params.MSG_DELETION_DELAY)
                    Rs.queue_embeds[qm.name] = None
                # skip posting any embeds
                continue

            # specific queue requested -> skip if this qm is not the specified one
            if (name != '' and name != qm.name) or (
                    level in params.SUPPORTED_RS_LEVELS and level != qm.level):
                continue
                pass

            # make sure that the placeholder for "all queues empty" is removed
            if Rs.queue_embeds['empty'] is not None:
                await Rs.queue_embeds['empty'].delete(
                    delay=params.MSG_DELETION_DELAY)
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
                    warn_text = ' ⚠️ '
                else:
                    warn_text = ''

                if p.note != '':
                    note_text = f' - "_{p.note}_"'
                else:
                    note_text = ''

                # print player
                team = team + f'        {p.discord_nick + warn_text + note_text}  ' \
                              f':watch: {convert_secs_to_time(seconds=time.time()-p.timer)}\n'

            queue_age = qm.get_queue_age(q)
            embed.description = team
            embed.set_footer(
                text=
                f'Queue started {convert_secs_to_time(seconds=time.time()-queue_age)} ago.'
            )

            # update queue embed
            if Rs.queue_embeds[qm.name] is not None:
                await Rs.queue_embeds[qm.name
                                      ].delete(delay=params.MSG_DELETION_DELAY)
            Rs.queue_embeds[qm.name] = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID).send(embed=embed)

            # reactive queue system
            if add_reactions:
                try:
                    await Rs.queue_embeds[qm.name
                                          ].add_reaction(params.JOIN_EMOJI)
                    await Rs.queue_embeds[qm.name
                                          ].add_reaction(params.LEAVE_EMOJI)
                    await Rs.queue_embeds[qm.name
                                          ].add_reaction(params.START_EMOJI)
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
            embed.description = 'Start a new one by typing `!in` or reacting below!\n' \
                                'Questions? `!help` or ask a `@Server Admin`!\n' \
                                'Bugs or Ideas? Please report them to `@Bot Dev`!'
            # update embed
            if Rs.queue_embeds['empty'] is not None:
                await Rs.queue_embeds['empty'].delete(
                    delay=params.MSG_DELETION_DELAY)
            m = Rs.queue_embeds['empty'] = await bot.get_channel(
                params.SERVER_RS_CHANNEL_ID).send(embed=embed)
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
        embed.set_author(name='RS Queue Help',
                         icon_url=params.BOT_DISCORD_ICON)
        embed.set_footer(
            text=f'Called by {ctx.author.display_name}\nDeleting in 2 min.')
        embed.add_field(name="`!rs`",
                        value="Hide (mute) or unhide this channel.",
                        inline=False)
        embed.add_field(name="`!in`",
                        value="Sign up for your highest RS level.",
                        inline=False)
        embed.add_field(name="`!in X [note]`",
                        value="Sign up for RS level X (optional: with note).",
                        inline=False)
        embed.add_field(name="`!out`", value="Leave all queues.", inline=False)
        embed.add_field(name="`!out X`",
                        value="Leave queue of RS level X.",
                        inline=False)
        embed.add_field(name="`!q`",
                        value="Display running queues.",
                        inline=False)
        embed.add_field(name="`!start X`",
                        value="Early start RS level X queue.",
                        inline=False)
        embed.add_field(name="`!clear X`",
                        value="Clear queue for RS level X.",
                        inline=False)
        Rs.last_help_message = await ctx.channel.send(content=None,
                                                      embed=embed)
        await Rs.last_help_message.delete(delay=2 * 60)

    @staticmethod
    def _record_rs_run(rs_level: int, queue: List[player.Player]):
        if rs_level not in params.SUPPORTED_RS_LEVELS:
            print(f'record_rs_run(): {rs_level} not a valid level, skipping')
            return

        plist = ''
        for p in queue:
            plist = plist + f'{p.discord_name} ({p.discord_id}); '
        line = f'{time.asctime()}\tRS{rs_level}:\t{len(queue)}/4:\t{plist}'

        completed_queues_file = open("rs/completed_queues.txt",
                                     "a",
                                     encoding="utf-8")
        completed_queues_file.write(line + '\n')
        completed_queues_file.flush()
        completed_queues_file.close()

        Rs.stats[f'RS{rs_level}'] += 1

    @staticmethod
    def _read_rs_records():

        completed_queues_file = open("rs/completed_queues.txt",
                                     "r",
                                     encoding="utf-8")
        queues = completed_queues_file.readlines()

        for q in queues:
            tokens = q.split('\t')
            qm_name = tokens[1].replace(':', '')
            q_len = int(tokens[2].split('/')[1].replace(':', ''))
            if q_len > 0:
                Rs.stats[qm_name] += 1

        completed_queues_file.close()