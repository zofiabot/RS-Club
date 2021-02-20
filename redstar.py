import asyncio
import re
import time
from queue import Queue
from queue import Empty
from typing import Union, List, Dict, Tuple, Callable, Coroutine, Awaitable, Any, TypeVar
from pathlib import Path
#import logging
#logger = logging.getLogger()

import discord
from discord.ext import tasks

import params_rs as params
import player
from player import Player
from queue_manager import QueueManager
# from util import Util
from pprint import pprint

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

def emoji_to_int(reaction: str):
    e2i = {}
    for i in Rs.star_range:
        e = (f'RS{i}_EMOJI')
        e2i[getattr(params, e)] = i
    return e2i[reaction]

def int_to_emoji(number: int):
    i2e = {}
    for i in Rs.star_range:
        n = (f'RS{i}_EMOJI')
        i2e[i] = getattr(params, n)
    return i2e[number]

class Rs:

    star_range = params.SUPPORTED_RS_LEVELS
    qms = []
    afk_warned_players = []
    afk_check_messages = {}
    time_last_queue_post = time.time()
    time_last_queues_post = {}
    queue_embeds = {}
    queue_status_embed = None
    stats = {}
    rs_roles = {}
    guild: discord.Guild = None
    bugs_ch = None
    channel = None #RS single channel or dash object
    channels = {} #RS channel objects

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
        Rs.bugs_ch = bot.get_channel(params.SERVER_BUG_CHANNEL_ID)
        Rs.channel = bot.get_channel(params.SERVER_RS_CHANNEL_ID)

        for emoji, role_name in zip(params.RS_EMOJIS[-8:],
                                    params.RS_ROLES[-8:]):
            role = discord.utils.get(Rs.guild.roles, name=role_name)
            if role:
                Rs.rs_roles[emoji] = role
            else:
                print(
                    f"unable to retrieve role {role_name}, bot will NOT operate as intended"
                )
                raise Exception(
                    f"unable to retrieve role {role_name}, bot will NOT operate as intended"
                )

        # rs queue management (data storage)
        for i in (Rs.star_range):
            role = discord.utils.get(Rs.guild.roles,
                                     name=getattr(params,
                                                  f'RS{i}_ROLE')).mention
            Rs.qms.append(QueueManager(f'rs{i}', i, 0xff3300, role))

        if params.SPLIT_CHANNELS:
          # record queues *display* update
          for i in Rs.star_range: Rs.time_last_queues_post.update({i : 0})
          # queue status embeds rsx=active_queue i=placeholder
          for i in Rs.star_range: Rs.queue_embeds.update({f'rs{i}' : None, i : None})
          #  get RS channel objects
          Rs.channels[0] = Rs.channel #compatibility
          for i in Rs.star_range:
              Rs.channels[i] = bot.get_channel(params.RS_CHANNELS.get(f'rs{i}'))

        Rs.queue_status_embed = None

        # message refs
        Rs.time_last_queue_post = time.time()
        # Rs.prev_disp_msgs = []
        # Rs.role_pick_messages = {}  # dict: key=discord_id, value=msg_id

        # afk handling
        Rs.afk_warned_players = []  # list of Player objects
        Rs.afk_check_messages = {}  # dict: key=discord_id, value=msg_id

        # rs run stats
        if params.OLD_STARS:  # if present add earlier stats
            for o in params.OLD_STARS:
                Rs.stats[o] = params.OLD_STARS.get(o)
        else:
            for i in Rs.star_range:
                Rs.stats[f'rs{i}'] = 0

        Rs._read_RS_records()

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
        Reaction handler of Rs dashboard module
        :param user:
        :param reaction:
        :return:
        """

        msg = reaction.message
        msg_id = reaction.message.id
        channel = reaction.message.channel.id  # hmmm

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

        if Rs.queue_status_embed is not None and msg_id == Rs.queue_status_embed.id:

            # player_own_queue = None

            if reaction.emoji == params.LEAVE_EMOJI:
                print(
                    f'Rs.handle_reaction(): {user} trying to leave all queues via reaction'
                )
                Rs.add_job(Rs.leave_queue, [user, 0, True, False, False, None])

            else:
                level = emoji_to_int(str(reaction.emoji))

                if params.RS_ROLES[level - 4] not in [ro.name for ro in user.roles]:
                    await msg.channel.send(
                        f"` {user.display_name}, {params.TEXT_NOROLESET} rs{level} role `",
                        delete_after=params.MSG_DELETION_DELAY)

                elif params.RESTRICTING_ROLES[level - 4] in [ro.name for ro in user.roles]:
                    await msg.channel.send(
                        f"` We are sorry {user.display_name}, but you can't join rs{level} queue `",
                        delete_after=params.MSG_DELETION_DELAY)

                elif level in Rs.star_range:
                    print(
                        f'Rs.handle_reaction(): {user} trying to join rs{level} via reaction'
                    )
                    Rs.add_job(Rs.enter_queue, [user, level, '', True, False])

            await Rs.queue_status_embed.remove_reaction(reaction.emoji, user)

    @staticmethod
    def get_qm(level: int):
        if level in Rs.star_range:
            return Rs.qms[level - min(Rs.star_range)]
        else:
            raise ValueError

    @staticmethod
    def add_job(callback, args):
        if params.DEBUG_MODE: call_info = f'call:{callback} args:{args}'
        # most rs commands have discord.Member as first arg -> add as additional log info
        if len(args) > 0 and isinstance(args[0], discord.Member):
            call_info = 'for ' + args[0].name + '#' + args[0].discriminator
            print(f'Rs.add_job(): scheduled {callback.__name__}() {call_info}')

        # schedule job via queue
        Rs.jobs.put((callback, args))
        print(f'Rs.add_job(): {Rs.jobs.qsize()} job(s) left')

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_JOB_TASK_RATE)
    async def task_process_job_queue():

        try:
            #await asyncio.sleep(0.1)

            # call to retrieve next job
            job = Rs.jobs.get_nowait()
            callback, args = job

            print(f'\n\n[task_process_job_queue]: executing {callback.__name__}()')
            await callback(*args)

            print(f'Rs.task_process_job_queue(): {Rs.jobs.qsize()} job(s) left')

        except Empty:
            pass
        except discord.errors.HTTPException as e:
            print(
                f'Rs.task_process_job_queue(): discord.errors.HTTPException {str(e)}'
            )
        except discord.DiscordException as e:
            print(
                f'**ERROR**:[task_process_job_queue]: generic discord exception {str(e)}'
            )
        except Exception as e:
            print(
                f'[task_process_job_queue]: generic exception {str(e)} call:{callback} arg: {args}\njob: {job}\n'
            )

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_AFK_TASK_RATE)
    async def task_check_afk():
        """
        Cyclic afk check for all queued players
        :return: never returns
        """
        try:
            # for each rs queue
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
                        msg = await Rs.channel.send(
                            f' {p.discord_mention} {params.WARNING_EMOJI} ` {params.TEXT_STILL_AROUND} `',
                            delete_after=params.TIME_AFK_KICK -
                            params.TIME_AFK_WARN)
                        await msg.add_reaction(params.CONFIRM_EMOJI)
                        # await asyncio.sleep(0.001)

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

                        await Rs.display_queues(True)

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
            print(
                f'**ERROR**:[task_check_afk]: generic discord exception {str(e)}'
            )
        except Exception as e:
            print(
                f'**ERROR**:[task_check_afk]: generic exception: {str(e)}'
            )
            print(
                f'**ERROR**:[task_check_afk]: generic exception: {str(e)}'
            )

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_QUEUE_TASK_RATE)
    async def task_repost_queues():
        """
        Cyclic reposting of running queues
        :return: never returns
        """
        # await asyncio.sleep(0.1)
        try:
            print(f'Rs.task_repost_queues(): executing...')
            Rs.add_job(Rs.display_queues, [True])

        except discord.errors.HTTPException:
            print(f'Rs.task_repost_queues(): discord.errors.HTTPException')
            pass
        except discord.DiscordException as e:
            print(
                f'**ERROR**:[task_repost_queues] generic discord exception {str(e)}'
            )
            pass
        except Exception as e:
            print(
                f'**ERROR**:[task_repost_queues]: generic exception: {str(e)}'
            )

    @staticmethod
    async def start_queue( caller: discord.Member, level: int = 0 ):
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
            if params.SPLIT_CHANNELS: l=level 
            else: l=0
            m = await Rs.channels[l].send(
                f'{caller.mention} ` Invalid queue "rs{level}" `',
                delete_after=params.MSG_DISPLAY_TIME)
            return
        except discord.errors.HTTPException as e:
            print(f'Rs.start_queue(): discord.errors.HTTPException {str(e)}')
        except discord.DiscordException as e:
            print(
                f'**ERROR**:[start_queue] Rs.start_queue(): generic discord exception {str(e)}'
            )
        except Exception as e:
            print(f'Rs.start_queue(1): generic exception {str(e)}')

        p = qm.find_player_in_queue_by_discord(caller)
        q = qm.queue
        authorized = False

        # player not in queue
        if p is None:
            # check this user's roles
            for r in caller.roles:
                # has admin/mod powers
                if r.name in (params.SERVER_ADMIN_ROLES + params.SERVER_MODERATOR_ROLES):
                    authorized = True
                    print(
                        f'Rs.start_queue(): {caller} is authorized (moderator)'
                    )
                    break
        # player in queue -> authorized
        else:
            authorized = True
            print(f'Rs.start_queue(): {caller} is authorized (queue member)')

        # start the queue
        if authorized and len(q) > 0:
            await Rs._queue_ready(level)
        elif len(q) == 0:
            m = await Rs.channel.send(
                f'{caller.mention} ` No rs{level} queue found! `',
                delete_after=params.MSG_DISPLAY_TIME)
        else:
            print(f'Rs.start_queue(): {caller} is not authorized')
            msg = f'{caller.mention} ` Only queued players or @Moderators can force a start. `'
            if params.SPLIT_CHANNELS: l=level 
            else: l=0
            m = await Rs.channels[level].send(msg, delete_after = params.MSG_DISPLAY_TIME)


    @staticmethod
    async def clear_queue(caller: discord.Member, level: int = 1):

        print(f'Rs.clear_queue(): called by {caller}')

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            m = await Rs.channel.send(
                f'{caller.mention} ` Invalid queue "rs{level}" `',
                delete_after=params.MSG_DISPLAY_TIME)
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
                        m = await Rs.channel.send(
                            f'{caller.mention} ` No rs{level} queue found! `',
                            delete_after=params.MSG_DISPLAY_TIME)
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
                m = await Rs.channel.send(
                    f'{caller.mention} ` rs{level} queue cleared! `',
                    delete_after=params.MSG_DISPLAY_TIME)
                await Rs.display_queues(True)
            else:
                m = await Rs.channel.send(
                    f'{caller.mention} ` No rs{level} queue found! `',
                    delete_after=params.MSG_DISPLAY_TIME)
        else:
            m = await Rs.channel.send(
                f'{caller.mention} ` Only queued players or administrators can clear a queue. `',
                delete_after=params.MSG_DISPLAY_TIME)

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
        if level not in Rs.star_range:
            m = await Rs.channel.send(
                f'rs{level}? Not in this galaxy. Try again!',
                delete_after=params.MSG_DISPLAY_TIME)
            return
        
        qm = Rs.get_qm(level)
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
            if queue_len < 3: ping_string = params.SERVER_PING_ROLES[level-4]
            elif  queue_len == 3: ping_string = params.SERVER_SOFT_PING_ROLES[level-4]
            qm.last_role_ping = time.time()
        else:
            ping_string = f'RS{level}'

        # new in this queue -> standard join
        if res == QueueManager.PLAYER_JOINED:
            msg = f'` {player.discord_nick} joined ` {ping_string} ` ({queue_len}/4) `'
            if params.SPLIT_CHANNELS:
                m = await Rs.channels[level].send(msg, delete_after=params.MSG_DISPLAY_TIME)
            else:
                m = await Rs.channel.send(
                    msg, delete_after=params.MSG_DISPLAY_TIME)
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
        if level not in Rs.star_range and level != 0:
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
                    m = await Rs.channel.send(
                        f'` {player.discord_nick} timed out for {qm.name} ({len(q)}/4) `',
                        delete_after=params.MSG_DISPLAY_TIME)
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
                    m = await Rs.channel.send(
                        f'` {player.discord_nick} removed from {qm.name} ({len(q)}/4) `',
                        delete_after=params.MSG_DISPLAY_TIME)
                    await Rs.display_queues(True)

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
                    m = await Rs.channel.send(
                        f'` {player.discord_nick} left {qm.name} ({lq}/4) `',
                        delete_after=params.MSG_DISPLAY_TIME)
                    await Rs._delete_afk_check_msg(player.discord_id)
                await Rs.display_queues(True)

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
                    m = await Rs.channel.send(
                        f'` {player.discord_nick} left {qm.name} ({lq}/4) `',
                        delete_after=params.MSG_DISPLAY_TIME)
                    await Rs._delete_afk_check_msg(player.discord_id)

        await Rs.display_queues(True)

    @staticmethod
    async def display_queues(force_update: bool = False,
                             footer_text: str = params.TEXT_FOOTER_TEXT):
        """

        :param force_update: force reposting the embed
        :return:
        """

        last_posted = round(time.time() - Rs.time_last_queue_post)
        if force_update is False and last_posted < params.TIME_Q_REPOST_COOLDOWN:
            print(
                f'Rs.display_queues(): skipping due to spam (last update: {last_posted}s ago)'
            )
            return

        embed = discord.Embed(color=params.QUEUE_EMBED_COLOR)
        embed.set_author(name=params.QUEUE_EMBED_TITLE,
                         icon_url=params.QUEUE_EMBED_ICON)
        embed.set_footer(text=footer_text)
        inl = True
        queue_active = False

        if params.SPLIT_CHANNELS:
             await Rs.display_individual_queues()

        # process all rs queues
        for j, qm in enumerate(Rs.qms):

            # queue is populated
            if len(qm.queue) > 0:
                queue_active = True

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
                    note_text = f'~ "_{p.note}_"'
                else:
                    note_text = ''

                # print player
                team = team + f' \u2800 \u2800{p.discord_nick + warn_text + note_text} ' \
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
        if not queue_active:
            embed.description = f'{params.TEXT_EMPTY_QUEUE_DASH} {Rs.bugs_ch.mention}!'

        # post embed (first time)
        if Rs.queue_status_embed is None:
            await Rs._post_status_embed(embed)
        # edit or repost
        else:
            rs_chan = Rs.channel

            # last message is not the embed -> delete and repost, keep as is otherwise and just edit
            #TODO remove repost for dash
            if rs_chan.last_message is not None and rs_chan.last_message.author.id != bot.user.id:
                print('Rs.display_queues(): reposting')
                await Rs._post_status_embed(embed)
                await Rs.queue_status_embed.delete
            else:
                await Rs.queue_status_embed.edit(embed=embed)
                print('Rs.display_queues(): updated')

        Rs.time_last_queue_post = time.time()

    @staticmethod
    async def display_individual_queues():

        for i in Rs.star_range:
            # await asyncio.sleep(0.01)
            await Rs.display_individual_queue(i, True, False)


    @staticmethod
    async def display_individual_queue(level: int = 0,
                                       add_reactions: bool = True,
                                       force_update: bool = False):
        """
        :param name: name of the queue_manager (e.g. 'rs7')
        :param level: level of the queue to be displayed
        :return:
        """

        last_posted = round(time.time() - Rs.time_last_queues_post[level])

        if force_update is False and last_posted < params.TIME_Q_REPOST_COOLDOWN:
            print(
                f'Rs.display_queues(): skipping due to spam (last update: {last_posted}s ago)'
            )
            return

        else:
            # process queue
            qm = Rs.get_qm(level)

            if qm.get_queue_updated or last_posted > params.TIME_Q_REPOST:

                try:

                    queue_len = len(qm.queue)

                    # queue is empty -> send special embed
                    if queue_len == 0:
                        embed = discord.Embed(color=params.QUEUE_EMBED_COLOR)
                        embed.title = f':regional_indicator_r::regional_indicator_s:{int_to_emoji(qm.level)} empty?'
                        embed.description = f'{params.TEXT_EMPTY_QUEUE} {Rs.bugs_ch.mention}!'
                        # delete normal queue embed
                        if Rs.queue_embeds[qm.name] is not None:
                            await Rs.queue_embeds[qm.name].delete()
                            await Rs.queue_embeds.update({qm.name : None})

                        # post placeholder queue embed
                        Rs.queue_embeds[qm.level] = await Rs._post_individual_embed(embed, level, Rs.queue_embeds[qm.level])
                        Rs.time_last_queues_post[level] = time.time()

                        qm.set_queue_displayed()

                    # populated queue
                    else:
                        # fetch the queue and build embed
                        active_embed = discord.Embed(
                            color=params.QUEUE_EMBED_COLOR)
                        active_embed.set_author(name='', icon_url='')
                        active_embed.title = f':regional_indicator_r::regional_indicator_s:{int_to_emoji(qm.level)} ({queue_len}/4) \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800  \u2800 '
                        team = ''

                        # for each player: make entry in embed
                        for i, p in enumerate(qm.queue):

                            # AFK warning
                            if p.afk_flag is True:
                                warn_text = ' ⚠️ '
                            else:
                                warn_text = ''

                            if p.note != '':
                                note_text = f' · {p.note}'
                            else:
                                note_text = ''

                            # print player
                            team = team + f'{p.discord_nick + warn_text + note_text}  ' \
                                          f':watch: {convert_secs_to_time(seconds=time.time()-p.timer)}\n'

                        queue_age = qm.get_queue_age()
                        active_embed.description = team
                        active_embed.set_footer(
                            text=
                            f'Queue updated {convert_secs_to_time(seconds=time.time()-queue_age)} ago.'
                        )

                        # make sure that the placeholder for "all queues empty" is removed
                        if Rs.queue_embeds[qm.level] is not None:
                            await Rs.queue_embeds[qm.level].delete()
                            Rs.queue_embeds[qm.level] = None

                        # update queue embed
                        Rs.queue_embeds[qm.name] = await Rs._post_individual_embed(
                                active_embed, qm.level, Rs.queue_embeds[qm.name])

                        # something was posted, so remember the time
                        Rs.time_last_queues_post[level] = time.time()
                        qm.set_queue_age(time.time()) # hmmm
                        qm.set_queue_displayed()
                
                except discord.errors.NotFound:
                    print('[display_individual_queue]: lost message handle (NotFound)')
                    Rs.queue_embeds[qm.level] = None

                except Exception as ex:
                    exception_type = type(ex).__name__
                    print(
                        f'**ERROR**:[display_individual_queue]: generic exception: {str(ex)}'
                    )
                    print(f'\nexception type: {exception_type}')
        return

    @staticmethod
    async def _post_status_embed(embed: discord.Embed):
        Rs.queue_status_embed = await Rs.channel.send(embed=embed)

        try:
            e2i = {}
            for i in Rs.star_range:
                e = (f'RS{i}_EMOJI')
                await Rs.queue_status_embed.add_reaction(getattr(params, e))
            await Rs.queue_status_embed.add_reaction(params.LEAVE_EMOJI)

        except discord.errors.NotFound:
            print('Rs._post_status_embed(): lost message handle (NotFound)')
            Rs.queue_status_embed = None
        except discord.DiscordException as e:
            print(
                f'**ERROR**:[_post_status_embed]: generic discord exception {str(e)}'
            )
            pass

    @staticmethod
    async def _post_individual_embed(embed_to_post: discord.Embed,
                                     level: int, old_embed: discord.Embed = None):
                
        # last message is not the embed -> delete and repost, keep as is otherwise and just edit
        if (Rs.channels[level].last_message is not None and Rs.channels[level].last_message.author.id != bot.user.id) or old_embed == None:

            print('inividual_queue: reposting')
            current_embed = await Rs.channels[level].send(embed=embed_to_post)
            if old_embed != None: await old_embed.delete()
            # Rs.queue_status_embeds.update({channel : current_embed})

        else:
            await old_embed.edit(embed=embed_to_post)
            current_embed = old_embed
            print('inividual_queue: updated')

        try:
            await current_embed.add_reaction(params.JOIN_EMOJI)
            await current_embed.add_reaction(params.UNJOIN_EMOJI)
            await current_embed.add_reaction(params.START_EMOJI)

        except discord.errors.NotFound:
            print('[_post_individual_embed]: lost message handle (NotFound)')
            current_embed = None
        except discord.DiscordException as e:
            print(
                f'**ERROR**:[_post_individual_embed]: generic discord exception {str(e)}'
            )
            pass
        except Exception as ex:
            exception_type = type(ex).__name__
            print(
                f'**ERROR**:[_post_individual_embed]: generic exception: {str(ex)}'
            )
            print(f'\nexception type: {exception_type}')
            print(f'\n{Rs.queue_embeds}')

        finally:
            return current_embed

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
        Rs.add_job(Rs.display_queues, [True])

        print(
            f'Rs._reset_afk(): pending afk warning for {discord_user} was reset'
        )

    @staticmethod
    async def _delete_afk_check_msg(player_id):

        if player_id in Rs.afk_check_messages.keys():
            try:
                msg = await Rs.channel.fetch_message(Rs.afk_check_messages[player_id])
                await msg.delete()
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
            Rs.time_last_queues_post.update({level : time})  #reset queue timer
            qm.set_queue_age(0)
        except ValueError:
            m = await Rs.channel.send(
                f'` Oops! Invalid queue "rs{level}". Call for help! `',
                delete_after=params.MSG_DISPLAY_TIME)
            return
        except Exception as e:
            print(f'[_queue_ready](1): generic exception {str(e)}')

        # ping all players
        pings = [p.discord_mention for p in qm.queue]
        msg = ', '.join(pings)
        msg = f':regional_indicator_r::regional_indicator_s:{int_to_emoji(qm.level)} ready! ' + msg + f' {params.TEXT_MEET_WERE}'
        if params.SPLIT_CHANNELS:
            m = await Rs.channels[level].send(msg)
        else:
            m = await Rs.channel.send(msg)

        # remove players from other queues and/or remove any pending afk checks if applicable
        for p in qm.queue:
            await Rs._delete_afk_check_msg(p.discord_id)
            await Rs.leave_queue(None, level=level, caused_by_other_queue_finished=True, player=p)

        # record & reset queue
        Rs._record_RS_run(level, qm.queue)

        qm.clear_queue()

        # update embed
        Rs.add_job(Rs.display_queues, [True])


    @staticmethod
    def get_level_from_RS_role(caller) -> int:
        player_roles = caller.roles
        level = 0
        for r in player_roles:
            # role must be 3 or 5 chars long, start with anycase "Vrs" followed by one or two digits
            if len(r.name) in range(3, 5) and re.match(
                    '[vR][rR][sS][14-9][0-1]?', r.name):
                # extract rs level as integer and update highest if applicable
                rsr = int(re.match('[14-9][0-1]?', r.name[2:]).string)
                if rsr > level:
                    level = rsr
        return level

    @staticmethod
    def get_level_from_RS_roles(caller) -> list:
        player_roles = caller.roles
        levels = []
        for r in player_roles:
            # role must be 3 or 5 chars long, start with anycase "Vrs" followed by one or two digits
            if len(r.name) in range(3, 5) and re.match(
                    '[vR][rR][sS][14-9][0-1]?', r.name):
                # extract rs level as integer and update highest if applicable
                rsr = int(re.match('[14-9][0-1]?', r.name[2:]).string)
                levels.append(rsr)
        return levels

    @staticmethod
    def _record_RS_run(rs_level: int, queue: List):

        if rs_level not in Rs.star_range:
            print(f'record_RS_run(): {rs_level} not a valid level, skipping')
            return

        plist = ''
        for p in queue:
            plist += f'{p.discord_name} ({p.discord_id}); '
        
        line = f'{time.asctime()}\trs{rs_level}\t{len(queue)}/4\t{plist}'

        completed_queues_file = open("completed_queues.txt", "a", encoding="utf-8")
        completed_queues_file.write(line + '\n')
        completed_queues_file.flush()
        completed_queues_file.close()

        Rs.stats[f'rs{rs_level}'] += 1

    @staticmethod
    def _read_RS_records():

        completed_queues_path = Path("completed_queues.txt")
        if not completed_queues_path.exists():
            completed_queues_path.touch()
        completed_queues_file = open(completed_queues_path,
                                     "r",
                                     encoding="utf-8")
        queues = completed_queues_file.readlines()

        for q in queues:
            tokens = q.split('\t')
            qm_name = tokens[1]
            q_len = int(tokens[2].split('/')[1])

            if q_len > 0:
                Rs.stats[qm_name] += 1

        completed_queues_file.close()
