import os
import re
import discord
from discord.ext import commands
import params_rs as params
from o_redstar import Rs
from keep_awake import keep_awake # used to keep the server awake otherwise it goes to sleep after 1h of inactivity

#intents = discord.Intents.default()
#intents.members = True

bot = discord.ext.commands.Bot(command_prefix=['!']) #, intents=intents)
bot.remove_command('help')
bot_ready = True


# Help command  

@bot.command(name='help', help='general help page', aliases=params.help_aliases)
async def cmd_help(ctx: discord.ext.commands.Context):
    """
    General help command
    :param ctx:
    :return:
    """
    # standard handling of commands
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    print(f'cmd_help(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

    # relay
    Rs.add_job(Rs.show_help, [ctx])


# RS queue commands
# module: m_redstar.py

@bot.command(name='rshelp', help='rs help page', aliases=params.rs_help_aliases)
async def cmd_rs_help(ctx: discord.ext.commands.Context):
    """
    General help command
    :param ctx:
    :return:
    """
    # standard handling of commands
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    print(f'cmd_rs_help(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

    #await Rs.show_help(ctx)
    Rs.add_job(Rs.show_help, [ctx])


@bot.command(name='rsstats', help='RS statistics', aliases=params.rs_stats_aliases)
async def cmd_rs_stats(ctx: discord.ext.commands.Context):
    """
    Display RS statistics
    :param ctx: discord context
    :return:
    """

    # standard handling of commands
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    print(f'cmd_rs_stats(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

    embed = discord.Embed(color=params.EMBED_QUEUE_COLOR)
    embed.set_author(name='RS Counter', icon_url= params.SERVER_DISCORD_ICON)
    embed.set_footer(text=f'Called by {ctx.author.display_name}\nDeleting in 1min')

    rs_chan = bot.get_channel(params.SERVER_RS_CHANNEL_ID)
    text = f'Total Runs in {rs_chan.mention}\n\n'
    total = sum(Rs.stats.values())
    for rs, cnt in Rs.stats.items():
        lvl = int(rs.replace('RS', ''))
        if lvl == 11:
            break
        text += f'**{rs}**: {cnt} _({round(cnt/total*100)}%)_\n'

    embed.description = text
    m = await ctx.send(embed=embed)
    await m.delete(delay=60 * 1)


@bot.command(name='rsrules', help='rsrules', aliases=params.rs_rules_aliases)
async def cmd_rs_rules(ctx: discord.ext.commands.Context):
    await ctx.message.delete()

    print(f'cmd_rs_rules(): requested by {ctx.author} in #{ctx.channel.name}')

    channel = bot.get_channel(params.RULES_CHANNEL_ID)
    message = await channel.fetch_message(params.RULES_MESSAGE_ID) #.content

    embed = discord.Embed(color=params.EMBED_COLOR, delete_after = params.RULES_DELETION_DELAY)
    embed.set_author(name='RS Club Rules', icon_url=params.SERVER_DISCORD_ICON)
    # text = params.TEXT_RULES
    embed.description = message.content
    await ctx.send(embed=embed)


@bot.command(name='enter', help='Join the RS queue', aliases=params.enter_queue_aliases)
async def cmd_enter_rs_queue(ctx: discord.ext.commands.Context, level_arg: str = '0', *, comment: str = ''):
    """
    Join RS queue
    :param comment:
    :param ctx: discord context
    :param level_arg: rs level(s) to join, separated by comma
    :return:
    """
    # only handle rs commands in the rs channel
    if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID:
        return

    async with ctx.channel.typing():

        # standard handling of commands
        await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
        print(f'cmd_enter_rs_queue(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

        # relay command to module
        levels = level_arg.replace(',', ' ').split(' ')
        for level in levels:
            Rs.add_job(Rs.enter_queue, [ctx.author, int(level), comment, False, False])


@bot.command(name='leave', help='Leave the RS queue', aliases=params.leave_queue_aliases)
async def cmd_leave_rs_queue(ctx: discord.ext.commands.Context, *, level_arg: str = '0'):
    """
    Leave RS queue(s)
    :param ctx: discord context
    :param level_arg: rs level(s) to join, separated by comma
    :return:
    """
    # only handle rs commands in the rs channel
    if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID:
        return

    async with ctx.channel.typing():

        # standard handling of commands
        await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
        print(f'cmd_leave_rs_queue(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

        # relay command to module
        levels = level_arg.replace(',', ' ').split(' ')
        for level in levels:
            Rs.add_job(Rs.leave_queue, [ctx.author, int(level), False, False, False, None])


@bot.command(name='display', help='Display the current RS queues', aliases=params.display_queue_aliases)
async def cmd_display_rs_queues(ctx: discord.ext.commands.Context):
    """
    Display current queues that contain at least one player
    :param ctx: discord context
    :param level: rs level to display
    :return:
    """
    # only handle rs commands in the rs channel
    if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID:
        return

    # standard handling of commands
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    print(f'cmd_display_rs_queues(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

    # relay command to module
    Rs.add_job(Rs.display_queues, [False])


@bot.command(name='start', help='Start a queue early', aliases=params.start_queue_aliases)
async def cmd_start_rs_queue(ctx: discord.ext.commands.Context, level: str):
    """
    Start a certain queue
    :param ctx: discord context
    :param level: rs level to start
    :return:
    """
    # only handle rs commands in the rs channel
    if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID:
        return

    # standard handling of commands
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    print(f'cmd_start_rs_queue(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

    # relay command to module
    # await Rs.start_queue(caller=ctx.author, level=int(level))
    Rs.add_job(Rs.start_queue, [ctx.author, int(level)])


@bot.command(name='clear', help='Clear a queue', aliases=params.clear_queue_aliases)
async def cmd_clear_rs_queue(ctx: discord.ext.commands.Context, level: str):
    """
    Clear a certain queue
    :param ctx: discord context
    :param level: rs level to start
    :return:
    """
    # only handle rs commands in the rs channel
    if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID:
        return

    # standard handling of commands
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    print(f'cmd_clear_rs_queue(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')

    # relay command to module
    # await Rs.clear_queue(caller=ctx.author, level=int(level))
    Rs.add_job(Rs.clear_queue, [ctx.author, int(level)])

#################################
# System commands module:
#################################
@bot.command(name='ping', help='ping')
async def cmd_ping(ctx):
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    print(f'cmd_ping(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}')
    await ctx.send(f'Pong! Latency = {round(bot.latency, 3)}s.')

@bot.command(name='shutdown', help='persist current state and shutdown')
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    pass

@bot.command(name='settings', help='Debug')
@commands.has_permissions(administrator=True)
async def settings(ctx):
    pass

#################################
# Bot events
#################################
@bot.event
async def on_message(message):

    #global bot_ready
    #if not bot_ready:
    #return

    # print(f'on_message(): {message.author} in #{message.channel}: "{message.content}"')

    # skip event if: msg from bot itself or debug_mode / debug_channel
    if message.author == bot.user or message.guild.id != params.SERVER_DISCORD_ID:
        #        or (message.channel.id == params.SERVER_DEBUG_CHANNEL_ID and #params.DEBUG_MODE is False)\
        #        or (message.channel.id != params.SERVER_DEBUG_CHANNEL_ID and #params.DEBUG_MODE is True):
        return

    # echo as debug
    # await message.channel.send(message.content)

    # allow '+' and '-' as soft prefixes inside rs channel
    if message.channel.id == params.SERVER_RS_CHANNEL_ID and message.content[0] in '+-':
        message.content = '!' + message.content

    # hack to understand commands like "! cmd" (ignore space)
    if len(message.content) > 2 and message.content[0] == '!' and message.content[1] == ' ':
        message.content = message.content.replace(' ', '', 1)

    # hack to understand commands like "!in6" (ignore missing space)
    if re.match('^![a-z]{1,3}[1-9]+', message.content):
        message.content = message.content.replace('!in', '!in ', 1)

    await bot.process_commands(message)


@bot.event
async def on_ready():

    # initialize all command modules
    Rs.init(bot)        # red star
    print(f'on_ready(): modules initialized')

    # launch loop tasks
    if not Rs.task_process_queue.is_running() and params.DEBUG_MODE is False:
        Rs.task_process_queue.start()
        print(f'on_ready(): launching Rs.task_process_queue...')
    if not Rs.task_check_afk.is_running() and params.DEBUG_MODE is False:
        Rs.task_check_afk.start()
        print(f'on_ready(): launching Rs.task_check_afk...')
    if not Rs.task_repost_q.is_running() and params.DEBUG_MODE is False:
        Rs.task_repost_q.start()
        print(f'on_ready(): launching Rs.task_repost_q...')

    # other stuff
    if not params.DEBUG_MODE:
        Rs.add_job(Rs.display_queues, [True])

    global bot_ready
    bot_ready = True
    print(f'on_ready(): {bot.user.name} is ready')

    dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
    await dbg_ch.send(
        f'**INFO**\non_ready(): Initialization complete')


@bot.event
async def on_connect():
    print(f'on_connect(): {bot.user.name} has connected')
    if params.DEBUG_MODE is False:
        dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
        if dbg_ch:
            await dbg_ch.send(
            f'**INFO**\non_connect(): Connection (re-)established')

@bot.event
async def on_disconnect():
    print(f'on_disconnect(): {bot.user.name} has disconnected')
    # if params.DEBUG_MODE is False:
    #     dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
    #     await dbg_ch.send(
    #         f':warning: **ERROR**\non_disconnect(): Connection lost')


@bot.event
async def on_resumed():
    print(f'on_resumed(): {bot.user.name} has resumed')
    # if params.DEBUG_MODE is False:
    #     dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
    #     await dbg_ch.send(
    #         f'**INFO**\non_resumed(): Connection recovered')

#@bot.event
#async def on_member_join(guest: discord.Member):
#
#    global bot_ready
#    if not bot_ready or params.DEBUG_MODE:
#        return
#
#    print(
#        f'on_member_join(): {guest.display_name} ({guest}) has joined the server'
#    )
#
#    new_user_nick = '[] ' + guest.display_name
#
#    if len(new_user_nick) > 32:
#        print(
#            f'on_member_join(): nickname cannot support ally tags (length would exceed 32)'
#        )
#    else:
#        await guest.edit(nick=new_user_nick,
#                         reason=f"automatic ally tag on join")
#        print(f'on_member_join(): ally tags added: {new_user_nick}')
#
#    guest_role = None
#    # uih_rs_role = guest.guild.get_role(params.SERVER_RS_ROLE_ID)
#    #await guest.add_roles(guest_role, reason='automatic Guest role on join')
#    # await guest.add_roles(uih_rs_role, reason='automatic Guest + UIH-RS role on join')
#    print(f'on_member_join(): assigned @Guest to {guest.display_name}')


#@bot.event
#async def on_member_remove(member: discord.Member):
#
#    global bot_ready
#    if not bot_ready or params.DEBUG_MODE:
#        return
#
#    print(f'on_member_remove(): {member.display_name} has left the server')

# @bot.event
# async def on_error(event, *args, **kwargs):
#     print(f'Unhandled message: event={event} message.content={args[0].content}\n')
#     print(event)
#     #print(f'Unhandled message: {args[0]}\n')
#     return


@bot.event
async def on_reaction_add(reaction, user):

    global bot_ready
    if not bot_ready:
        return

    # early catch for own reactions
    if user.id == bot.user.id:
        return

    # print(f'on_reaction_add(): {reaction.emoji} by {user}')

    chan_id = reaction.message.channel.id

    # DEBUG
    if chan_id == params.SERVER_DEBUG_CHANNEL_ID:
        await Rs.handle_reaction(user, reaction)
        return

    # RS reactive queue system
    if chan_id == params.SERVER_RS_CHANNEL_ID:
        await Rs.handle_reaction(user, reaction)


@bot.event
async def on_command_error(ctx, error):

    print(f'on_command_error(): {error}')
    print(f'on_command_error(): message was: "{ctx.message.content}" sent by {ctx.author.name} in #{ctx.channel.name}')

    dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
    await dbg_ch.send(f'**ERROR**\n{error}\n**REASON**\n"{ctx.message.content}" sent by {ctx.author.name} in #{ctx.channel.name}')

    try:
        await ctx.message.add_reaction('🤖')
        await ctx.message.add_reaction('❔')
    except discord.errors.NotFound:
        print(f'on_command_error(): message was deleted -> no reaction')
    except Exception:
        pass

    if isinstance(error, commands.errors.CheckFailure):
        m = await ctx.send(f'{ctx.author.mention} You do not have the correct role for this command!')
        await m.delete(delay=params.MSG_DISPLAY_TIME)
    elif isinstance(error, commands.errors.MissingPermissions):
        m = await ctx.send(f'{ctx.author.mention} I\'m missing permissions to do that!')
        await m.delete(delay=params.MSG_DISPLAY_TIME)


# kill handler to trigger a clean exit (e.g. to clear up any open chat clutter)
def handle_exit():
    pass

# kill handler -> cleanup before exiting
# atexit.register(handle_exit)
# signal.signal(signal.SIGTERM, handle_exit)
# signal.signal(signal.SIGINT, handle_exit)

# start
keep_awake()
print('main: connecting...')
bot.run(os.getenv("DISCORD_TOKEN"))
