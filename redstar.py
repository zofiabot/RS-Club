#import asyncio
from concurrent.futures import ProcessPoolExecutor
import re
import time
# import jsonpickle
#from time import gmtime, strftime
#from queue import Queue
#from queue import Empty
#from typing import Union, List, Dict, Tuple, Callable, Coroutine, Awaitable, Any, TypeVar
from typing import Union, List, Dict #, Tuple, Callable, Awaitable
from pathlib import Path
import discord

# lumberjack: sys, traceback, colorama
import sys, traceback
import colorama as cr
cr.init(autoreset=True)

import discord 
from discord.ext import tasks

from params import params
from player import Player
from queue_manager import QueueManager

# module reference to Bot instance
bot: discord.Client

#  HELPER FUNCTIONS
def secs2time(seconds: int) -> str:
    if seconds < 60:
        seconds = int(round(seconds))
        return str(seconds) + 's'
    elif seconds < 3600:
        minutes = int(round(seconds / 60))
        return str(minutes) + 'm'
    else:
        hours = int(round(seconds / 3600))
        return str(hours) + 'h'

def emoji2int(reaction: str) -> int:
    e2i = {}
    for i in Rs.star_range:
        e = (f'RS{i}_EMOJI')
        e2i[getattr(params, e)] = i
    return e2i[reaction]

def int2emoji(number: int) -> str:
    i2e = {}
    for i in Rs.star_range:
        n = (f'RS{i}_EMOJI')
        i2e[i] = getattr(params, n)
    return i2e[number]

def strip_flags(message: str = ''):
    #TODO Strip flag emoji from first line
    return message

def s_(num: int = 0, num2: int = 0):
    string =''
    for i in range(0,num):
        if i <= num2 : string += ' '
        if i <= num : string += '\u2800'
    return string

######################################################
# THE RS CLASS                                       #
######################################################
class Rs:

    star_range = range(params.SUPPORTED_RS_LEVELS_MIN, params.SUPPORTED_RS_LEVELS_MAX +1)
    qms = []
    afk_warned_players = []
    afk_check_messages = {}
    time_last_dashboard_post = time.time()
    time_last_queues_post = {}
    single_queue_messages = {}
    dashboard_embed = None
    dashboard_updated = True
    dashboard_queue_displayed = {}
    stats = {}
    rs_roles = {}
    guild: discord.Guild = None
    bugs_ch = None
    channel = None #RS single channel or dash object
    channels = {} #RS channel objects
    teams = {} # current teams for each level
    ping_mentions = {} # all pings
    soft_ping_mentions = {} # 3/4 pings
    Last_help_message: {int : discord.Message} = {0 : None} # for no split queues
    relays: { int : discord.channel } = {}
    relay_embeds = {int : discord.Message }

    # dict to handle open user dialogues (expecting a reaction to be closed)
    # key: discord.Message.id
    # value: discord.Member.id, discord.Channel.id and a
    # Tuple containing supported reaction emoji and their respective callback
    # dialogues={discord.message.id, [discord.user.id, discord.channel.id, [str, Awaitable]]}
    # Dict[[int], List[[[int], [int], Tuple[str,Awaitable]]]]
    dialogues: Dict = {}

    
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
            Rs.qms.append(QueueManager(f'rs{i}', i, 0xff3300))
            Rs.teams.update({ i : {} })
            Rs.dashboard_queue_displayed.update({ i : False })
            # all pings
            role =  params.SERVER_PING_ROLES[i-4]
            Rs.ping_mentions.update({ i : discord.utils.get(Rs.guild.roles, name=role).mention }) 
            # 3/4 pings
            role = params.SERVER_SOFT_PING_ROLES[i-4]
            Rs.soft_ping_mentions.update({ i : discord.utils.get(Rs.guild.roles, name=role).mention })
            Rs.Last_help_message.update({ i : None})

        if params.SPLIT_CHANNELS:

          # record queues update time
          for i in Rs.star_range: Rs.time_last_queues_post.update({i : 0})

          # queue status embeds rsx=active_queue i=placeholder
          for i in Rs.star_range: Rs.single_queue_messages.update({f'rs{i}' : None, i : None})

          #  get RS channel objects
          Rs.channels[0] = Rs.channel # for compatibility
          for i in Rs.star_range:
              Rs.channels[i] = bot.get_channel(params.SERVER_RS_CHANNELS.get(f'rs{i}'))

        # Rs.dashboard_embed = None # alredy set

        # message refs
        Rs.time_last_dashboard_post = time.time()
        # Rs.prev_disp_msgs = []
        # Rs.role_pick_messages = {}  # dict: key=discord_id, value=msg_id

        # afk handling
        Rs.afk_warned_players = []  # list of Player objects
        Rs.afk_check_messages = {}  # dict: key=discord_id, value=msg_id

        # rs run stats
        for i in Rs.star_range:
            Rs.stats[f'rs{i}'] = 0
        if params.OLD_STARS:  # if present add earlier stats
            for o in params.OLD_STARS:
                Rs.stats[o] = params.OLD_STARS.get(o)

        Rs._read_RS_records()

        Rs.restore_relays()
        for channel in Rs.relays.values():
          Rs.relay_embeds.update({channel.id : None})

    @staticmethod
    async def exit():
        return
        try:
            # delete any open afk checks
            for acm in Rs.afk_check_messages.values():
                await acm.delete()
            # delete the main queue embed
            if Rs.dashboard_embed is not None:
                await Rs.dashboard_embed.delete()
            for i in Rs.star_range:
                await Rs.single_queue_messages[i].delete()
        except discord.NotFound:
            pass


    @staticmethod
    async def handle_dialogue_reaction(user: discord.Member,
                              reaction: discord.Reaction):
        """
        Reaction handler of Rs dashboard embed
        :param user:
        :param reaction:
        :return:
        """

        msg_id = reaction.message.id
        user_id, chan_id, emoji_callback = Rs.dialogues[msg_id]
        # check if the user reacting is the dialogue owner
        
        if user_id == user.id:
            # check supported emojis for this message
            for emo, callback in emoji_callback:
                print(emo)
                # emoji found -> call its callback function and close the dialogue
                if reaction.emoji == emo:
                    print(f'handle reaction: {emo}')
                    await callback(*[user])
                    await reaction.message.delete()
                    Rs.dialogues.pop(msg_id)
                    Rs.dashboard_updated = True
                    break

    @staticmethod
    async def handle_reaction(user: discord.Member,
                              reaction: discord.Reaction):
        """
        Reaction handler of Rs dashboard embed
        :param user:
        :param reaction:
        :return:
        """
        try:

            msg = reaction.message
            msg_id = reaction.message.id
            if user is None: 
              users = await reaction.users().flatten()
              if users[0].id == bot.user.id:
                user=users[1]
              else:
                user=users[0]


            if Rs.dashboard_embed is not None and msg_id == Rs.dashboard_embed.id:

                # player_own_queue = None

                if reaction.emoji == params.LEAVE_EMOJI:
                    print(
                        f'handle reaction: {user} trying to leave all queues'
                    )
                    await Rs.leave_queue(user, 0, True, False, False, None)

                else:
                    level = emoji2int(str(reaction.emoji))

                    if params.RS_ROLES[level - 4] not in [ro.name for ro in user.roles]:
                        await msg.channel.send(
                            f"` {user.display_name}, {params.TEXT_NOROLESET} rs{level} role `",
                            delete_after=params.MSG_DISPLAY_TIME)

                    elif params.RESTRICTING_ROLES[level - 4] in [ro.name for ro in user.roles]:
                        await msg.channel.send(
                            f"` We are sorry {user.display_name}, but you can't join rs{level} queue `",
                            delete_after=params.MSG_DISPLAY_TIME)

                    elif level in Rs.star_range:
                        qm = Rs.get_qm(level)
                        p = qm.find_player_in_queue_by_discord(user)

                        if p not in qm.queue:
                            # check if player has mates
                            #   # if yes unqueue mate
                            #   # else
                            
                            await Rs.enter_queue(user, level, '', True, False)
                            print(f'handle reaction: {user} trying to join rs{level}')

                        else:
                            await Rs.leave_queue(user, level, True, False, False, p)
                            print(f'handle reaction: {user} trying to leave {qm.name} (toggle)')


            await Rs.dashboard_embed.remove_reaction(reaction.emoji, user)
            Rs.dashboard_updated = True

        except Exception as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}:handle_reaction: generic exception: {str(e)}'
            )
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}:handle_reaction: generic exception: {str(e)}'
            )
            Rs.lumberjack(sys.exc_info())
            await Rs.dashboard_embed.remove_reaction(reaction.emoji, user)
            Rs.dashboard_updated = True
            pass

    @staticmethod
    async def handle_single_queue_reaction(user: discord.Member, reaction: discord.Reaction, level: int, name: str):
        """
        Reaction handler of Rs dashboard embed
        :param user:
        :param reaction:
        :param level: star level
        :param name: channel name
        :return:
        """

        msg = reaction.message
        # msg_id = reaction.message.id
        qm = Rs.get_qm(level)

        if msg in [Rs.single_queue_messages[qm.level], Rs.single_queue_messages[qm.name]] :

            Rs.dashboard_updated = True

            if str(reaction.emoji) == params.UNQUEUE_EMOJI:
                print(f'handle reaction: {user} trying to leave ({qm.name}) queue')
                await Rs.leave_queue(user, level, True, False, False, None)
                            
            elif str(reaction.emoji) == params.UNJOIN_EMOJI:
                p = qm.find_player_in_queue_by_discord(user)
                if p is not None:
                    # check if player has mates
                    #   # if yes unqueue mate
                    #   # else
                    print(
                        f'handle reaction: {user} trying to leave {qm.name} queue')
                    await Rs.leave_queue(None, level, True, False, False, p)
                        
            elif str(reaction.emoji) == params.START_EMOJI:
                if qm.find_player_in_queue_by_discord(user) is not None:
                    # check if player has mates
                    #   # if yes unqueue mate
                    #   # else
                        print(
                            f'handle reaction: {user} trying to start {qm.name} queue'
                        )
                        if len(qm.queue) > 1 :
                          await Rs.start_queue(user, level)
                        else:
                          await Rs.channels[level].send(f"{user.mention} you can only start queue early if you are not alone")

            elif str(reaction.emoji) == params.CROID_EMOJI:
                if qm.find_player_in_queue_by_discord(user) is not None:
                    # check if player has mates
                        print(
                            f'handle reaction: {user} adding croid in {qm.name} run'
                        )


            else: # equivent to elif reaction.emoji == params.JOIN_EMOJI:
                # this case is already handled (impossibe to react on something you can't see)
                # if params.RS_ROLES[level - 4] not in [ro.name for ro in user.roles]:
                #     await msg.channel.send(
                #         f"` {user.display_name}, {params.TEXT_NOROLESET} rs{level} role `",
                #         delete_after=params.MSG_DISPLAY_TIME)

                if params.RESTRICTING_ROLES[level - 4] in [ro.name for ro in user.roles]:
                    await msg.channel.send(
                        f"` We are sorry {user.display_name}, but you can't join rs{level} queue `",
                        delete_after=params.MSG_DISPLAY_TIME)


                elif level in Rs.star_range:
                    # check if player has mates
                    #   # if yes unqueue mate
                    #   # else
                    ##### alternatively can be dealt with by Rs.enter_queue
                    ##### this would mean we are allowing for players to 
                    ##### add mates in dashboard
                    print(
                        f'handle reaction: {user} trying to join rs{level} via reaction'
                    )
                    await Rs.enter_queue(user, level, '', True, False)

            await msg.remove_reaction(reaction.emoji, user)
            return

    @staticmethod
    def get_qm(level: int):
        if level in Rs.star_range:
            return Rs.qms[level - min(Rs.star_range)]
        else:
            raise ValueError

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_AFK_TASK_RATE*10)
    async def task_invite_ranking():
        """
        Cyclic task to refresh invite ranking
        :return: never returns
        """
        await Rs.invite_ranking()
            

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_AFK_TASK_RATE)
    async def task_check_afk():
        """
        Cyclic afk check for all queued players
        :return: never returns
        """
        try:
            afk_msgs = {}
            # for each rs queue
            for qm in Rs.qms:
                # ask QM for afk players
                afks = qm.get_and_update_afk_players()

                # if len(afks) > 0:
                #     msg = (f' task_check_afk: {qm.name} existing afk list\n')
                #     for a in afks:
                #        msg += f'                 {a.discord_nick} {secs2time(a.afk_timer)}\n'
                    
                #     print(msg)

                
                # for each afk player
                for p in afks:

                    # already flagged and timer reached -> kick
                    if params.TIME_AFK_KICK < p.afk_timer:
                        # kick this player
                        Rs.set_queue_updated(qm.level)
                        # print(f' task check_afk: {qm.name}: kicking player {p.discord_name}')
                        await Rs.leave_queue(None, 0, False, True, False, p)

                        # reset afk trackers
                        if p in Rs.afk_warned_players:
                            Rs.afk_warned_players.remove(p)
                        Rs._delete_afk_check_msg(p.discord_id)
                    
                    # not flagged as afk yet and no active warning -> flag and start timer
                    elif p.afk_flag is False:
                        #print(f' task_check_afk: {qm.name} flagging player {p.discord_nick}')
                        p.afk_flag = True
                        # Rs.set_queue_updated(qm.level)

                        # sanity checks: if warning already exists -> delete and repost / deregister player
                        Rs._delete_afk_check_msg(p.discord_id)
                        if p in Rs.afk_warned_players:
                            Rs.afk_warned_players.remove(p)

                        # prepare or relplace afk check msg for player
                        msg = f' {params.WARNING_EMOJI} {p.discord_mention} ` {params.TEXT_STILL_AROUND} `'

                        # don't warn Klaus
                        if p.discord_id not in params.NO_AFK_DIALOGUE:
                            afk_msgs[p.discord_id] = [qm.level, msg , (params.TIME_AFK_KICK-params.TIME_AFK_WARN)]
                            # mark player as afk
                            Rs.afk_warned_players.append(p)

                    # already flagged and counting -> keep counting
                    else: # p.afk_timer < params.TIME_AFK_KICK
                        Rs.set_queue_updated(qm.level) # might not be neccesary
                        # print(
                        #     f' task check_afk: {qm.name}: {p.discord_nick} afk for {secs2time(p.afk_timer)}\n                 kicking after {secs2time(params.TIME_AFK_KICK - p.afk_timer)})'
                        # )
                        p.afk_timer = p.afk_timer + params.TIME_BOT_AFK_TASK_RATE

            # finally dispatch dialogue warnings
            for p in afk_msgs:
                  lvl, msg, delay =  afk_msgs[p]
                  message = await Rs.channels[lvl].send(msg,delete_after=delay)
                  await message.add_reaction(params.CONFIRM_EMOJI)
                  # create user dialogue
                  Rs.dialogues[message.id] = [ p, (Rs.channels[lvl].id),[[params.CONFIRM_EMOJI, Rs._reset_afk]]]

                  Rs.afk_check_messages[p] = message.id

        except discord.errors.HTTPException:
            print(f'task_check_afk(): {discord.errors.HTTPException}')
        except discord.DiscordException as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}:[task_check_afk]: generic discord exception {str(e)}'
            )
        except Exception as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}:[task_check_afk]: generic exception: {str(e)}'
            )
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}:[task_check_afk]: generic exception: {str(e)}'
            )
            Rs.lumberjack(sys.exc_info())

    @staticmethod
    @tasks.loop(seconds=params.TIME_BOT_QUEUE_TASK_RATE)
    async def task_repost_queues():
        """
        Cyclic reposting of running queues
        :return: never returns
        """
        try:
            await Rs.display_dashboard()
            if params.SPLIT_CHANNELS: await Rs.display_individual_queues()

        except discord.errors.HTTPException:
            print(f'Rs.task_repost_queues(): {discord.errors.HTTPException}')
            pass
        except discord.DiscordException as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}:[task_repost_queues] generic discord exception {str(e)}'
            )
            pass
        except Exception as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}:[task_repost_queues]: generic exception: {str(e)}'
            )
            Rs.lumberjack(sys.exc_info())

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
            p = qm.find_player_in_queue_by_discord(caller)
            q = qm.queue
            authorized = False
            if params.SPLIT_CHANNELS: # multiplayer for channel broadcast level or..
              split=1
            else :                    # ... 0 (channels[0] is RS_Channel)
              split=0

            # player not in queue
            if p is None:
                # check this user's roles
                for r in caller.roles:
                    # has admin/mod powers
                    if r.name in (params.SERVER_ADMIN_ROLES + params.SERVER_MODERATOR_ROLES):
                        authorized = True
                        print(f'    start_queue: {caller} is authorized (moderator)')
                        break
            # player in queue -> authorized
            else:
                authorized = True
                print(f'    start_queue: {caller} is authorized (queue member)')

            # start the queue
            if authorized and len(q) > 0:
                await Rs._queue_ready(level)
                # Rs.set_queue_updated(level) set by _queue_ready
            elif len(q) == 0:
                await Rs.channels[level*split].send(
                    f'{caller.mention} ` No rs{level} queue found! `',
                    delete_after=params.MSG_DISPLAY_TIME)
            else:
                print(f'    start_queue: {caller} is not authorized')
                msg = f'{caller.mention} ` Only queued players or @Moderators can force a start. `' 
                await Rs.channels[level*split].send(msg, delete_after = params.MSG_DISPLAY_TIME)

        except ValueError:
            await Rs.channels[level*split].send(
                f'{caller.mention} ` Invalid queue `',
                delete_after=params.MSG_DISPLAY_TIME)
            return
        except discord.errors.HTTPException as e:
            print(f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[start_queue]: discord.errors.HTTPException {str(e)}')
        except discord.DiscordException as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[start_queue]: generic discord exception {str(e)}'
            )
        except Exception as e:
            print(f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[start_queue]: generic exception {str(e)}') 
            Rs.lumberjack(sys.exc_info())

    @staticmethod
    async def clear_queue(caller: discord.Member, level: int = 1):
      
        print(f'    clear queue: called by {caller}')

        # try to fetch QM for this level
        try:
            qm = Rs.get_qm(level)
        except ValueError:
            await Rs.channel.send(
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
                        f'    clear_queue: {caller} is authorized (admin/mod)'
                    )
                    if len(q) == 0:
                        await Rs.channel.send(
                            f'{caller.mention} ` No rs{level} queue found! `',
                            delete_after=params.MSG_DISPLAY_TIME)
                        print(f'{cr.Fore.CYAN}    clear_queue: no rs{level} queue found. aborting')
                        return
                    break
        else:
            authorized = True
            print(f'    clear_queue: {caller} is authorized (member)')

        # clear the queue
        if authorized is True:
            if len(q) > 0:
                # remove potential afk check msgs
                for p in qm.queue:
                    Rs._delete_afk_check_msg(p.discord_id)
                qm.clear_queue()
                await Rs.channel.send(
                    f'{caller.mention} ` rs{level} queue cleared! `',
                    delete_after=params.MSG_DISPLAY_TIME)
                Rs.set_queue_updated(level)

            else:
                await Rs.channel.send(
                    f'{caller.mention} ` No rs{level} queue found! `',
                    delete_after=params.MSG_DISPLAY_TIME)
        else:
            await Rs.channel.send(
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
            await Rs.channel.send(
                f'rs{level}? Not in this galaxy. Try again!',
                delete_after=params.MSG_DISPLAY_TIME)
            return
        
        qm = Rs.get_qm(level)
        queue = None
        queue_len = 0
        res = QueueManager.NOTHING
        player = None

        # next try to join this player
        print(f'    enter_queue: {caller.display_name} joining {qm.name}')
        res, player, queue = qm.new_player(Player(caller, note=comment))

        if queue is not None:
            queue_len = len(queue)

        ping_string = f'@rs{level}'
        ping_cooldown = ((time.time()-qm.last_role_ping) >= params.PING_COOLDOWN) # we are on cooldown if False
        if queue_len in params.PING_THRESHOLDS and ping_cooldown:
            if queue_len < 3: ping_string = [Rs.ping_mentions[qm.level], '']
            else: 
              ping_string = [ Rs.ping_mentions[qm.level], Rs.soft_ping_mentions[qm.level] ]
              qm.last_role_ping = time.time()

        # new in this queue -> standard join
        if res == QueueManager.PLAYER_JOINED:
            Rs.set_queue_updated(level)
            msg = f'` {player.discord_nick} joined ` {ping_string[0]} ` ({queue_len}/4) `{ping_string[1]}'
            if params.SPLIT_CHANNELS:
                await Rs.channels[level].send(msg, delete_after=params.MSG_DISPLAY_TIME)
            else:
                await Rs.channel.send(
                    msg, delete_after=params.MSG_DISPLAY_TIME)


        # open afk warning -> always reset when enter_queue is called
        for qmg in Rs.qms:
            player = qmg.find_player_in_queue_by_discord(caller)
            # player found -> reset their afk status for other queues than the one joined
            if player is not None and qmg.level != qm.level:  # and player.afk_flag is True:
                print(
                    f'    enter_queue: resetting timers for {caller.display_name}'
                )
                await Rs._reset_afk(caller)
                res = QueueManager.PLAYER_RESET_AFK_FLAG
                break

        # ping all once queue hits 3/4 only
        #if queue_len in params.PING_THRESHOLDS:  # or queue_is_new is True:
        #await ctx.send(f'{ping_string} {queue_len}/4')

        # check if queue full
        if qm.get_queue_ready():
            Rs.set_queue_updated(level) # could be set by _queue_ready
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
            print('  [leave_queue]: invalid input')
            return

        # player handle might be provided or built from the user calling
        if player is None:
            player = Player(caller)
        
        # leaving all or specific queue only
        if level != 0: 
            leaving_all_queues = False
        else:
            leaving_all_queues = True

        # reaction used
        if caused_by_reaction:

            # try all queues and check if player can be removed from it
            for qm in Rs.qms:
                if leaving_all_queues or qm.level == level:
                    res, q = qm.player_left(player)
                    lq = len(q)
                    if res == QueueManager.PLAYER_LEFT: 
                        Rs.set_queue_updated(qm.level)
                        print(
                            f'    {player.discord_nick} leaving {qm.name} (reaction)'
                        )
                        await Rs.channels[level].send(
                            f'` {player.discord_nick} left {qm.name} ({lq}/4) `',
                            delete_after=params.MSG_DISPLAY_TIME)
                        Rs._delete_afk_check_msg(player.discord_id)

            return
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
                    Rs.set_queue_updated(qm.level)
                    print(
                        f'{player.discord_name} leaving {qm.name} other q starting'
                    )
                    await Rs.channels[level].send(
                        f'` {player.discord_nick} removed from {qm.name} ({len(q)}/4) `',
                        delete_after=params.MSG_DISPLAY_TIME)
            return

        # afk timeout
        elif caused_by_afk is True:
            # try all queues and check if player can be removed from it
            msg = [] # message for dashboard
            for qm in Rs.qms:
                res, q = qm.player_left(player)
                if res == QueueManager.PLAYER_LEFT:
                    Rs.set_queue_updated(qm.level)
                    print(
                        f'    {player.discord_nick} leaving {qm.name} (afk_kick)'
                    )
                    await Rs.channels[qm.level].send(
                        f'` {player.discord_nick} timed out for {qm.name} ({len(q)}/4) `',
                        delete_after=params.MSG_DISPLAY_TIME)
                    msg.append(qm.name)
                    Rs._delete_afk_check_msg(player.discord_id)
            if not params.SPLIT_CHANNELS:
              await Rs.channel.send(f'` {player.discord_nick} timed out for {", ".join(msg)}`',delete_after=params.MSG_DISPLAY_TIME)
            return

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
                    Rs.set_queue_updated(qm.level)
                    print(
                        f'    {caller.discord_nick} leaving {qm.name} (command)'
                    )
                    if not params.SPLIT_CHANNELS: 
                      await Rs.channel.send(
                        f'` {player.discord_nick} left {qm.name} ({lq}/4) `',
                        delete_after=params.MSG_DISPLAY_TIME)
                    Rs._delete_afk_check_msg(player.discord_id)
        return

    @staticmethod
    async def display_dashboard(force_update: bool = False,
                             footer_text: str = params.TEXT_FOOTER_TEXT):
        """
        :param force_update: force reposting the embed not used anymore
        :param footer_text: optional footer text
        :return:
        """

        last_posted = round(time.time() - Rs.time_last_dashboard_post)

        # if it is not yet time to reresh, ebed exists and nothing changed
        if last_posted < params.TIME_SPAM_BRAKE and Rs.dashboard_embed is not None and not Rs.dashboard_updated:
            # print(f'dashboard embed: skipping')
            return

        embed = discord.Embed(color=params.QUEUE_EMBED_COLOR)
        embed.set_author(name=params.QUEUE_EMBED_TITLE, icon_url=params.QUEUE_EMBED_ICON)
        embed.set_footer(text=footer_text)
        inl = True
        no_players = True

        for qm in Rs.qms:  
        # process all rs queues

            # await asyncio.sleep(0)

            if not Rs.dashboard_queue_displayed[qm.level]: 
                
                  if len(qm.queue) > 0: 
                  # if there is queue fetch the queue and add to embed
                      team = ''
                      no_players = False #there are players -> no placeholder embed

                      for i, p in enumerate(qm.queue):
                      # for each player: make entry in embed

                          player_desc = p.discord_nick
                          # AFK warning
                          if p.afk_flag:
                              player_desc += ' ⚠️ ' + p.note

                          # print player
                          team = team + f'{s_(3,0)} {player_desc}\n'
                          # :watch: {secs2time(time.time() - p.timer)}\n'

                      # add the entry to embed
                      if '♾' in team:
                          team = team.replace('♾', '\\♾') # do we need this?
                      rs_name=f'{int2emoji(qm.level)}{s_(1,2)}{len(qm.queue)}/4'
                      inl = False
                      Rs.teams.update({qm.level : {'name' : rs_name, 'value' : team, 'inline' : inl}})
                      embed.add_field(**Rs.teams[qm.level])

                  else: 
                  # set empty team
                      Rs.teams.update({qm.level:{}})
                  
                  Rs.dashboard_queue_displayed.update({ qm.level : True })

            elif Rs.teams[qm.level]: 
            # if not updated queue exists
                  no_players = False
                  embed.add_field(**Rs.teams[qm.level])

        # all queues empty -> post with placeholder message
        if no_players:
            embed.description = f'{params.TEXT_EMPTY_QUEUE_DASH} {Rs.bugs_ch.mention}!'

        # post embed (first time)
        if Rs.dashboard_embed is None:
            await Rs._post_dashboard_embed(embed)
            await Rs.display_relay_embeds(embed)
        
        else:
        # edit or repost
            
            # if we are running split channels no need to repost
            if params.SPLIT_CHANNELS:
                await Rs.dashboard_embed.edit(embed=embed)
                await Rs.display_relay_embeds(embed)
                #print('dashboard embed: updated')

            else:
            # last message is not the embed -> delete and repost, otherwise just edit
                if Rs.channel.last_message.author.id != bot.user.id:
                    #print('dashboard embed: reposting')
                    await Rs.dashboard_embed.delete
                    await Rs._post_dashboard_embed(embed)

        Rs.time_last_dashboard_post = time.time()
        Rs.dashboard_updated = False


    @staticmethod
    async def display_individual_queues(force_repost: bool = False):

        with ProcessPoolExecutor(max_workers=8) as executor:
            for qm in Rs.qms:
                # check if last message in channel belongs to bot, force upddate otherwise
                message = Rs.channels[qm.level].last_message

                last_posted = round(time.time() - Rs.time_last_queues_post[qm.level])

                if message is not None and message.author.id != bot.user.id: 
                    qm.set_queue_updated()
                    force_repost = True

                if qm.updated or last_posted > params.TIME_SPAM_BRAKE: 
                    executor.submit(await Rs.display_individual_queue(qm, force_repost))

    @staticmethod
    async def display_relay_embeds(embed: discord.Embed = None):
      try:
        # check if we got an embed
        if embed is None: return

        # if all queues empty display relay invite
        if params.TEXT_EMPTY_QUEUE_DASH in str(embed.description):
            embed.description = params.TEXT_EMPTY_R_DASH + '\n' + s_(1,0) + params.TEXT_CHECKOUT_DEMO
            embed.set_image(url=params.SERVER_DISCORD_ICON)
            #embed.add_field(name = '\u2800', value =, inline = True)
            embed.set_footer(text='')
        #else put invite in footer
        else:
            embed.set_thumbnail(url=params.SERVER_DISCORD_ICON)
            footer = params.TEXT_R_FOOTER + '\n' + params.TEXT_CHECKOUT_DEMO
            embed.add_field(name = '\u2800', value = footer, inline = False)
            embed.set_footer(text='')

        servers = len(Rs.relays)
        if servers < 1 : servers = 1 # max_workers must be greater than 0
        with ProcessPoolExecutor(max_workers=servers) as r_executor:
            for channel in Rs.relays.values():
               r_executor.submit(await Rs._post_relay_embed(embed, channel))
        
      except Exception as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[display_relay_embeds]: generic exception {str(e)}'
            )
            Rs.lumberjack(sys.exc_info())
            pass
    @staticmethod
    async def display_individual_queue(qm: QueueManager, force_repost: bool = False):
        """
        :param name: the queue_manager
        :param force_repost: force embed reposting
        :return:
        """

        level = qm.level

        try:

            queue_len = len(qm.queue)

            # queue is empty -> send special placeholder embed
            if queue_len == 0:

                embed_to_post = discord.Embed(color=params.QUEUE_EMBED_COLOR)
                embed_to_post.title = f':regional_indicator_r::regional_indicator_s:{int2emoji(qm.level)} empty? {s_(10,8)}'
                embed_to_post.description = f'{params.TEXT_EMPTY_QUEUE} {Rs.bugs_ch.mention}!'

                if Rs.single_queue_messages[qm.level] is not None:
                # placeholder embed alredy displayed ---- can this be skipped?
                    Rs.single_queue_messages[qm.level] = await Rs._post_individual_queue_embed(embed_to_post, level, Rs.single_queue_messages[qm.level], force_repost)    

                # replace normal queue embed
                elif Rs.single_queue_messages[qm.name] is not None:
                    Rs.single_queue_messages[qm.level] = await Rs._post_individual_queue_embed(embed_to_post, level, Rs.single_queue_messages[qm.name], force_repost)
                    Rs.single_queue_messages.update({qm.name : None})

                # post fresh placeholder queue embed
                else:
                    Rs.single_queue_messages[qm.level] = await Rs._post_individual_queue_embed(embed_to_post, level, None, True)  

                # something was posted, so remember the time
                Rs.time_last_queues_post[level] = time.time()
                Rs.set_queue_displayed(level)

            # populated queue
            else:
                # fetch the queue and build embed
                embed_to_post = discord.Embed(
                    color=params.QUEUE_EMBED_COLOR)
                embed_to_post.set_author(name='', icon_url='')
                embed_to_post.title = f':regional_indicator_r::regional_indicator_s:{int2emoji(qm.level)}\u2800{queue_len}/4 {s_(10,9)}'
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
                                  f':watch: {secs2time(time.time()-p.timer)}\n'

                embed_to_post.description = team
                embed_to_post.set_footer(text=params.TEXT_FOOTER_SINGLE_Q_TEXT)

                if Rs.single_queue_messages[qm.name] is not None:
                # update queue embed
                    Rs.single_queue_messages[qm.name] = await Rs._post_individual_queue_embed(embed_to_post, level, Rs.single_queue_messages[qm.name],force_repost)

                elif Rs.single_queue_messages[qm.level] is not None:
                # replace the placeholder for "all queues empty"
                    Rs.single_queue_messages[qm.name] = await Rs._post_individual_queue_embed(embed_to_post, level, Rs.single_queue_messages[qm.level],force_repost)
                    Rs.single_queue_messages[qm.level] = None

                else:
                # post new queue embed
                    Rs.single_queue_messages[qm.name] = await Rs._post_individual_queue_embed(embed_to_post, level, None, True) # force_repost = True

                # something was posted, so remember the time
                Rs.time_last_queues_post[level] = time.time()
                Rs.set_queue_displayed(level)
        
        except discord.errors.NotFound:
            print('[display_individual_queue]: lost message handle (NotFound)')
            Rs.single_queue_messages[qm.level] = None
            Rs.single_queue_messages[qm.name] = None
            Rs.display_individual_queue(qm)

        except Exception as ex:
            print(f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[display_individual_queue]: generic exception: {str(ex)}\n exception type: {type(ex).__name__} ')
            Rs.lumberjack(sys.exc_info())
        return

    @staticmethod
    async def _post_dashboard_embed(embed: discord.Embed):

        try:

            if Rs.dashboard_embed == None:
                Rs.dashboard_embed = await Rs.channel.send(embed=embed)

                for i in Rs.star_range:
                    e = (f'RS{i}_EMOJI')
                    await Rs.dashboard_embed.add_reaction(getattr(params, e))

                await Rs.dashboard_embed.add_reaction(params.LEAVE_EMOJI)

            else:
                await Rs.channel.edit(embed=embed)

        except discord.errors.NotFound:
            print('_post_dashboard_embed: lost message handle (NotFound)')
            Rs.dashboard_embed = None
            Rs._post_dashboard_embed(embed)
        
        except discord.DiscordException as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[_post_dashboard_embed]: generic discord exception {str(e)}'
            )
            pass

    @staticmethod
    async def _post_relay_embed(embed: discord.Embed, channel: discord.channel = None):

        if channel == None:
            return
        try:

            if Rs.relay_embeds[channel.id] == None:
                Rs.relay_embeds.update({channel.id : await channel.send(embed=embed)})

                # for i in Rs.star_range:
                #     e = (f'RS{i}_EMOJI')
                #     await Rs.dashboard_embed.add_reaction(getattr(params, e))

                # await Rs.dashboard_embed.add_reaction(params.LEAVE_EMOJI)

            else:
                message = Rs.relay_embeds[channel.id]
                await message.edit(embed=embed)

        except discord.errors.NotFound:
            print('    _post_relay_embed: lost message handle (NotFound)')
            Rs.relay_embeds[channel.id] = None
            pass
        
        except discord.DiscordException as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[_post_relay_embed]: generic discord exception {str(e)}'
            )
            pass
        
        except Exception as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[_post_relay_embed]: generic exception {str(e)}'
            )
            Rs.lumberjack(sys.exc_info())
            pass

    @staticmethod
    async def _post_individual_queue_embed(embed_to_post: discord.Embed,level: int, old_embed: discord.Embed = None, force_repost: bool = False):

        try:

            if force_repost or old_embed is None:
            # delete old embed and post a new one or post for first time
                #print(f' queue {level:>2} embed: reposting')
                if old_embed != None: await old_embed.delete()
                return_embed = await Rs.channels[level].send(embed=embed_to_post)

            elif embed_to_post.description == old_embed.embeds[0].description:
            # if embed is the same, do nothing, return old one
                #print(f' queue {level:>2} embed: skipping')
                return old_embed

            else:
            # new embed is diferent than the old one: update (edit)
                await old_embed.edit(embed=embed_to_post)
                #print(f' queue {level:>2} embed: updated')
                return await Rs.channels[level].fetch_message(old_embed.id)

            await return_embed.add_reaction(params.JOIN_EMOJI)
            # await return_embed.add_reaction(params.UNJOIN_EMOJI) # for mate system
            await return_embed.add_reaction(params.UNQUEUE_EMOJI)
            await return_embed.add_reaction(params.START_EMOJI)

            return return_embed

        except discord.errors.NotFound as e:
            print(f'[_post_individual_queue_embed]: lost message handle (NotFound)\n{str(e)}')
            return_embed = None
            return return_embed
        except discord.DiscordException as e:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[_post_individual_queue_embed]: generic discord exception {str(e)}'
            )
            pass
        except Exception as ex:
            print(
                f'{cr.Fore.RED}⚠️ {cr.Style.BRIGHT}[_post_individual_queue_embed]: generic exception: {str(ex)}\nexception type: {type(ex).__name__}')
            Rs.lumberjack(sys.exc_info())

        

    @staticmethod
    def set_queue_displayed(level: int = 0):
        if level != 0:
            qm = Rs.get_qm(level)
            qm.set_queue_displayed()
        else:
            Rs.dashboard_updated = False

    @staticmethod
    def set_queue_updated(level: int = 0):
        Rs.dashboard_updated = True
        if level != 0:
            qm = Rs.get_qm(level)
            qm.set_queue_updated()
            Rs.dashboard_queue_displayed.update({ level : False })

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
                    Rs.set_queue_updated(qm.level)
                Rs._delete_afk_check_msg(p.discord_id)
                # collect all affected queues
                players_queues.append(qm.name)
                Rs.dashboard_queue_displayed.update({ qm.level : False })

        print(
            f'\n     _reset_afk: pending afk warning for {discord_user.display_name} was reset'
        )
        Rs.dashboard_updated = True #TODO liquidate dialogue as well

    @staticmethod
    def _delete_afk_check_msg(player_id):

        if player_id in Rs.afk_check_messages.keys():
            try:
                #msg = await Rs.channel.fetch_message(Rs.afk_check_messages[player_id])
                Rs.afk_check_messages.pop(player_id)
                #await msg.delete()
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
            Rs.time_last_queues_post[level] = time.time()  #reset queue timer
        except ValueError:
            await Rs.channel.send(
                f'` Oops! Invalid queue "rs{level}". Call for help! `',
                delete_after=params.MSG_DISPLAY_TIME)
            return
        except Exception as e:
            print(f'[_queue_ready](1): generic exception {str(e)}')
            Rs.lumberjack(sys.exc_info())

        # ping all players
        pings = [p.discord_mention for p in qm.queue]
        msg = ', '.join(pings)
        msg = f':regional_indicator_r::regional_indicator_s:{int2emoji(qm.level)} ready! ' + msg + f' {params.TEXT_MEET_WERE}'
        if params.SPLIT_CHANNELS:
            await Rs.channels[level].send(msg)
        else:
            await Rs.channel.send(msg)

        # remove players from other queues and/or remove any pending afk checks if applicable
        for p in qm.queue:
            Rs._delete_afk_check_msg(p.discord_id)
            await Rs.leave_queue(None, level=level, caused_by_other_queue_finished=True, player=p)

        # record & reset queue
        Rs._record_RS_run(level, qm.queue)

        qm.clear_queue()

        # update embed
        Rs.set_queue_updated(level)

    @staticmethod
    def get_max_level_from_RS_roles(caller) -> int: # currently unused
        player_roles = caller.roles
        level = 0

        for r in player_roles:
            # role must be 3 or 5 chars long, start with anycase "Vrs" followed by one or two digits
            rsr = Rs.get_level_from_rs_string(r.name)
            if rsr > level:
                level = rsr
        return level

    @staticmethod
    def get_level_from_RS_roles(caller) -> list:
        player_roles = caller.roles
        levels = []
        for r in player_roles:
            # role must be 3 or 5 chars long, start with anycase "Vrs" followed by one or two digits
            rsr = Rs.get_level_from_rs_string(r.name)
            levels.append(rsr)
        return levels

    @staticmethod
    def get_level_from_rs_string(role: str) -> int:

        level = 0 # return 0 for dashboard
        # role must be 3 or 5 chars long, start with anycase "Vrs" followed by one or two digits
        if len(role) in range(4, 6) and re.match( # VRSxx
                '[vV][rR][sS][14-9][0-1]?', role):
            # extract rs level as integer and update highest if applicable
            level = int(re.match('[1-9]*', role[2:]).string)
        elif len(role) in range(3, 5) and re.match( # RSxx
                '[rR][sS][14-9][0-1]?', role):
            # extract rs level as integer and update highest if applicable
            level = int(re.match('[1-9]*', role[2:]).string)
        return level

    @staticmethod
    def _record_RS_run(rs_level: int, queue: List):

        if rs_level not in Rs.star_range:
            print(f'record_RS_run(): {rs_level} not a valid level, skipping')
            return

        plist = ''
        for p in queue:
            plist += f'{p.discord_name} ({p.discord_id}); '
        
        line = f'{time.asctime()}\trs{rs_level}\t{len(queue)}/4\t{plist}'

        with open("completed_queues.txt", "a", encoding="utf-8") as completed_queues_file:
          completed_queues_file.write(line + '\n')
          completed_queues_file.flush()
        

        Rs.stats[f'rs{rs_level}'] += 1

    @staticmethod
    def _read_RS_records():

        completed_queues_path = Path("completed_queues.txt")
        if not completed_queues_path.exists():
            completed_queues_path.touch()
        with open(completed_queues_path, "r", encoding="utf-8") as completed_queues_file: 
          queues = completed_queues_file.readlines()

        for q in queues:
            tokens = q.split('\t')
            qm_name = tokens[1]
            q_len = int(tokens[2].split('/')[1])

            if q_len > 0 and qm_name:
                Rs.stats[qm_name] += 1

    @staticmethod
    async def add_relay(guild: discord.Guild = None, channel : discord.channel = None, caller : discord.User = None):

        if guild.id in Rs.relays.keys(): return
        Rs.relays.update( { guild.id : channel } )
        Rs.relay_embeds.update( { channel.id : None } )
        Rs.save_relay(guild.id, guild.name, channel.id, guild.owner_id, caller.id, caller.name)
        await channel.send(content = params.TEXT_R_SET, delete_after = 15)
        try:
            for role in guild.roles: #make channel read only
              overwrite = discord.PermissionOverwrite()
              overwrite.send_messages = False
              overwrite.read_messages = True
              await channel.set_permissions(role, overwrite=overwrite)
        except Exception as e:
            print(f'       relays: {guild.name} \n       relays: {e}')
            pass
        return

    @staticmethod
    def save_relay(guild_id, guild_name, channel_id, guild_ownerid, caller_id, caller_name):
        with open('relays.txt', 'a+') as file:
          data = f'{guild_id}\t{guild_name}\t{channel_id}\t{guild_ownerid}'
          file.write(data + '\n')
          file.flush()
        print(f' relays added: {guild_name}')

    @staticmethod
    async def delete_relay(guild_id):
        with open('relays.txt', 'r') as file:
          servers = file.readlines()
        with open('relays.txt', 'w+') as file:
          for server in servers:
            if str(guild_id) in server:
              del Rs.relays[guild_id]
              continue
            file.write(server)
          file.flush()

        print(' relay remove: done')

    @staticmethod
    def restore_relays():
        try:
            with open('relays.txt', 'r') as file:
                servers = file.readlines()
                count = 0
                relays = ''
                for server in servers:
                    tokens = server.split('\t')
                    guild_id = int(tokens[0])
                    guild = bot.get_guild(guild_id)
                    if guild is None: continue
                    channel : discord.channel = guild.get_channel(int(tokens[2]))
                    if channel is None: continue
                    relays += f"               {(str(guild))}\n"
                    Rs.relays.update( { guild_id : channel } )
                    count += 1
                file.flush()
                            
            print(f'       relays: connecting {count} servers')
            print(relays)
            return

        except FileNotFoundError:
            print('       relays: backup file not found')

    async def invite_ranking(channel_id: int = params.INVITE_RANKING_CH):
        channel = bot.get_channel(channel_id)
        guild = bot.get_guild(params.SERVER_DISCORD_ID)
        invites_o = await guild.invites()
        invites: dict = { 'SWARM' : 15 }
        embed = discord.Embed(color=params.QUEUE_EMBED_COLOR)
        space = '\u2800'*12
        embed.title = (f'Invite Contest {space} 🏆')
        embed.description = (params.INVITE_RANKING_DESC+ '\n')

        for invite in invites_o:
            if 0 == invite.max_age:
              if invite.inviter.display_name in invites.keys():
                uses = invite.uses + invites[invite.inviter.display_name]
                invites.update({invite.inviter.display_name : uses })
              elif invite.inviter.display_name == 'Red Star Club':
                uses = invite.uses + invites['Zofia']
                invites.update({ 'Zofia' : uses })
              else:
                invites.update({invite.inviter.display_name : invite.uses })
        i = 1
        c = 'Current standings'
        embed.description +=  f"\n ```{' '*(28)} "
        embed.description +=  f"\n {' '*int((23-len(c)))}{c}\n"
        sorted_invites = sorted(invites.items(), key=lambda kv: kv[1], reverse=True)
        for a in sorted_invites:
          if a[0] in params.INVITES_NO_REWARDS:
              embed.description +=  f"\n{' '*3}  {a[0]} {' '*(18-len(a[0]))} {a[1]:>4}  "
                      
          elif int(a[1]) > 0:
              embed.description +=  f"\n{i:>3}. {a[0]} {' '*(18-len(a[0]))} {a[1]:>4}  "
              i += 1

        embed.description +=  f"\n {' '*(28)}  ``` "
        try:
          message = await channel.fetch_message(params.CONTEST_MESSAGE_ID)
          await message.edit(embed=embed)
        except Exception:
          await channel.send(embed=embed)
          print('Posting new Invite message')
        return

    async def welcome_message(channel_id: int = params.SERVER_WELCOME_CHANNEL):
        channel = bot.get_channel(channel_id)
        embed = discord.Embed(color=params.QUEUE_EMBED_COLOR)

        welcomes = ''
        styles = ['***', '', '*', '**', '`']

        for i, welcome in enumerate(params.WELCOME_STRINGS):
          welcomes += styles[i%5] + welcome + styles[i%5] + ' \u00A0'
        
        embed.description = welcomes + '\n\n'

        for i, language in enumerate(params.LANGUAGES):
          flag = f':flag_{(language).lower()}:'
          text = getattr(params, f'RULES_MESSAGE_LABEL_{language}')
          id = getattr(params, f'RULES_MESSAGE_ID_{language}')
          rules_ch = bot.get_channel(params.RULES_CHANNEL_ID)
          msg = await rules_ch.fetch_message(id)
          link = msg.jump_url
          embed.description += f'{flag}\u2009\u2009[{text}]({link})'
          if not i%2: 
            embed.description += ' ' 
          else:
            embed.description += ' '

        embed.description += '\n'
        embed.set_footer(text='confirm\u2009👍\u2009confirmar\u2009👍\u2009confirme\u2009👍\u2009confirmer\u2009👍\u2009bestätige\u2009👍\u2009potwierdź\u2009👍\u2009подтвердить')
        embed.set_image(url=params.REMEMBER_TO_CONFIRM_IMG)

            
        # try:
        #     mgs = []  #Empty list to put all the messages in the log

        #     async for message in channel.history(limit=100):
        #             mgs.append(message)
        #     await channel.delete_messages(mgs)

        # except discord.errors.NotFound:
        #     print('        Welcome: Messages already deleted')

        # await channel.send(embed=embed)

        msg = await channel.fetch_message(820976946866815049)
        await msg.edit(embed=embed)
        print('Posting new Welcome message')
        return


    # Rs.lumberjack(sys.exc_info())
    def lumberjack(info):
        exc_type, exc_value, exc_traceback = info
        print( f"\n{cr.Fore.YELLOW} print_tb:")
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        print( f"\n{cr.Fore.YELLOW}Exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)
        print( f"\n{cr.Fore.CYAN}Line: {exc_traceback.tb_lineno}\n") 