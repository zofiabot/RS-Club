import os
import re
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import params_rs as params
from redstar import Rs
from keep_awake import keep_awake # used to keep the server awake otherwise it goes to sleep after 1h of inactivity

#intents = discord.Intents.default()
#intents.members = True

bot = discord.ext.commands.Bot(command_prefix=['!']) #, intents=intents)
bot.remove_command('help')
bot_ready = True
dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
# Last_help_message = None


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

    # last_help_message = Last_help_message
    last_help_message = None

    if last_help_message is not None:
        await last_help_message.delete()

    embed = discord.Embed(color=params.EMBED_COLOR)
    embed.set_author(name='RS Queue Help',
                      icon_url=params.BOT_DISCORD_ICON)
    embed.set_footer(text=f'Called by {ctx.author.display_name}\nDeleting in {params.HELP_DELETION_DELAY} sec')
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
    last_help_message = await ctx.channel.send(embed=embed)
    await last_help_message.delete(delay=params.HELP_DELETION_DELAY)

    globals()['Last_help_message'] = last_help_message


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

    embed = discord.Embed(color=params.EMBED_COLOR)
    embed.set_author(name='RS Counter \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800   \u2800', icon_url= params.SERVER_DISCORD_ICON)
    embed.set_footer(text=f'Called by {ctx.author.display_name}\nDeleting in {params.HELP_DELETION_DELAY} sec')

    rs_chan = bot.get_channel(params.SERVER_RS_CHANNEL_ID)
    text = f'Total Runs \n' # in {rs_chan.mention}
    total = sum(Rs.stats.values())

    for rs, cnt in Rs.stats.items():
        lvl = int(rs.replace('RS', ''))
        if lvl == params.SUPPORTED_RS_LEVELS_MAX +1 : break
        text += f'**{rs}**: {cnt} _({round(cnt/total*100)}%)_\n'

    embed.description = text
    m = await ctx.send(embed=embed)
    await m.delete(delay=params.HELP_DELETION_DELAY)

@bot.command(name='rsrules', help='rsrules', aliases=params.rs_rules_aliases)
  

async def cmd_rs_rules(ctx: discord.ext.commands.Context):
    await ctx.message.delete()

    print(f'cmd_rs_rules(): requested by {ctx.author} in #{ctx.channel.name}')
    text = params.TEXT_RULES
    if params.TEXT_RULES_FORMAT == 'Message' :
      channel = bot.get_channel(params.RULES_CHANNEL_ID)
      message = await channel.fetch_message(params.RULES_MESSAGE_ID) #.content
      text = message.content
    embed = discord.Embed(color=params.EMBED_COLOR, delete_after = params.RULES_DELETION_DELAY)
    embed.set_author(name= f'{params.TEXT_RULES_TITLE}', icon_url=params.SERVER_DISCORD_ICON)
    embed.set_footer(text=f'Called by {ctx.author.display_name}\nDeleting in {int("{:.0f}".format(params.RULES_DELETION_DELAY/60))} min')

    
    embed.description = text
    m = await ctx.send(embed=embed)
    await m.delete(delay=params.RULES_DELETION_DELAY)

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

    # skip event if: msg from bot itself or debug_mode / debug_channel
    if message.author == bot.user or message.guild.id != params.SERVER_DISCORD_ID:
        return

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


    # Clean dead embedds
    mgs = [] #Empty list to put all the messages in the log
    channel = bot.get_channel(params.SERVER_RS_CHANNEL_ID) 

    async for message in channel.history(limit=100):
      if message.author == bot.user :
        mgs.append(message)
    await channel.delete_messages(mgs)

    
    # Clean logs older than 24h
    mgs = [] #Empty list to put all the messages in the log
    channel = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID) 
    time_differennce = timedelta(hours=24)
    init_time = datetime.now()
    
    async for message in channel.history(limit=100):
      if init_time - message.created_at > time_differennce and message.author == bot.user :
        mgs.append(message)
    await channel.delete_messages(mgs) 
    mgs = [] #Empty list to avoid trouble with other code  
      
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
        f'**INFO**: on_ready(): Initialization complete')


@bot.event
async def on_connect():
    print(f'on_connect(): {bot.user.name} has connected')
    
    if params.DEBUG_MODE is False:
        if dbg_ch:
            await dbg_ch.send(
            f'**INFO**: on_connect(): Connection (re-)established')

@bot.event
async def on_disconnect():
    print(f'on_disconnect(): {bot.user.name} has disconnected')
    await dbg_ch.send(f':warning: **ERROR**: on_disconnect(): Connection lost')


@bot.event
async def on_resumed():
    print(f'on_resumed(): {bot.user.name} has resumed')
    # if params.DEBUG_MODE is False:
    #     
    #     await dbg_ch.send(
    #         f'**INFO**: on_resumed(): Connection recovered')


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

    
    print(f'**ERROR**\n{error}\n**REASON**\n"{ctx.message.content}" sent by {ctx.author.name} in #{ctx.channel.name}')

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
