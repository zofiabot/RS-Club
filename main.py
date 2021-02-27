import os
import re
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sys
from params import params
from redstar import Rs
from keep_awake import keep_awake  # used to keep the server awake otherwise it goes to sleep after 1h of inactivity
import dotenv

intents = discord.Intents.default()
intents.typing = False  #spammy
intents.presences = False  #spammy
Last_help_message: discord.Message = None
bot = discord.ext.commands.Bot(command_prefix=['!', '+', '-'], intents=intents)
bot.remove_command('help')
bot_ready = True
dbg_ch = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)

# Helper functions

# Clean dead embedds
async def clean_dead_embeds(channel=False):
	try:
		mgs = []  #Empty list to put all the messages in the log
		if not channel:
			channel = bot.get_channel(params.SERVER_RS_CHANNEL_ID)
			if params.SPLIT_CHANNELS:
				for channel in Rs.channels.values():
					await clean_dead_embeds(channel)

		async for message in channel.history(limit=100):
			if message.author == bot.user and (
			    message.embeds or params.WARNING_EMOJI in message.content):
				mgs.append(message)
		await channel.delete_messages(mgs)
		return

	except discord.errors.NotFound:
		print('    Starting up: Queue  Messages already deleted')


# Clean logs older than given hours
async def clean_logs(period=24):
	try:
		mgs = []  #Empty list to put all the messages in the log
		channel = bot.get_channel(params.SERVER_DEBUG_CHANNEL_ID)
		time_differennce = timedelta(hours=period)
		init_time = datetime.now()

	except discord.errors.NotFound:
		print('    Starting up: Log Messages already deleted')

	async for message in channel.history(limit=100):
		if init_time - message.created_at > time_differennce and message.author == bot.user:
			mgs.append(message)
	await channel.delete_messages(mgs)
	mgs = []  #Empty list to avoid trouble with other code


# Help command


@bot.command(name='help',
             help='general help page',
             aliases=params.help_aliases)  #TODO languages, params
async def cmd_help(ctx: discord.ext.commands.Context):
	"""
    General help command
    :param ctx:
    :return:
    """
	# standard handling of commands
	await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
	print(
	    f'cmd_help(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}'
	)

	last_help_message = globals()['Last_help_message']

	if last_help_message is not None:
		await last_help_message.delete()

	embed = discord.Embed(color=params.EMBED_COLOR)
	embed.set_author(name='RS Queue Help', icon_url=params.BOT_DISCORD_ICON)
	embed.set_footer(
	    text=
	    f'Called by {ctx.author.display_name}\nDeleting in {params.HELP_DELETION_DELAY} sec'
	)
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
	embed.add_field(name="`!q`", value="Display running queues.", inline=False)
	embed.add_field(name="`!start X`",
	                value="Early start RS level X queue.",
	                inline=False)
	embed.add_field(name="`!clear X`",
	                value="Clear queue for RS level X.",
	                inline=False)
	last_help_message = await ctx.channel.send(embed=embed)
	await last_help_message.delete(delay=params.HELP_DELETION_DELAY)

	globals()['Last_help_message'] = last_help_message


@bot.command(name='rsstats',
             help='RS statistics',
             aliases=params.rs_stats_aliases)
async def cmd_rs_stats(ctx: discord.ext.commands.Context):
	"""
    Display RS statistics
    :param ctx: discord context
    :return:
    """

	# standard handling of commands
	await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
	print(
	    f'cmd_rs_stats(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}'
	)

	embed = discord.Embed(color=params.EMBED_COLOR)
	embed.set_author(
	    name=
	    'RS Counter \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800   \u2800',
	    icon_url=params.SERVER_DISCORD_ICON)
	embed.set_footer(
	    text=
	    f'Called by {ctx.author.display_name}\nDeleting in {params.HELP_DELETION_DELAY} sec'
	)

	text = 'Total Runs \n'  # in {rs_chan.mention}
	total = sum(Rs.stats.values())

	for rs, cnt in Rs.stats.items():
		lvl = int(rs.replace('rs', ''))
		if lvl == params.SUPPORTED_RS_LEVELS_MAX + 1: break
		text += f'**{rs}**: {cnt} _({round(cnt/total*100)}%)_\n'

	embed.description = text
	m = await ctx.send(embed=embed)
	await m.delete(delay=params.HELP_DELETION_DELAY)


@bot.command(name='rsrules', help='rsrules', aliases=params.rs_rules_aliases)
async def cmd_rs_rules(ctx: discord.ext.commands.Context):  #TODO languages
	await ctx.message.delete()

	print(f'cmd_rs_rules(): requested by {ctx.author} in #{ctx.channel.name}')

	text = params.TEXT_RULES  # rules hardcoded in bot params

	if params.TEXT_RULES_FORMAT == 'Message':  # rules from message on server
		channel = bot.get_channel(params.RULES_CHANNEL_ID)
		message = await channel.fetch_message(params.RULES_MESSAGE_ID
		                                      )  #.content
		text = message.content

	embed = discord.Embed(color=params.EMBED_COLOR,
	                      delete_after=params.RULES_DELETION_DELAY)
	embed.set_author(name=f'{params.TEXT_RULES_TITLE}',
	                 icon_url=params.SERVER_DISCORD_ICON)
	embed.set_footer(
	    text=
	    f'Called by {ctx.author.display_name}\nDeleting in {int("{:.0f}".format(params.RULES_DELETION_DELAY/60))} min'
	)

	embed.description = text
	m = await ctx.send(embed=embed)
	await m.delete(delay=params.RULES_DELETION_DELAY)
	return


@bot.command(name='enter',
             help='Join the RS queue',
             aliases=params.enter_queue_aliases)
async def cmd_enter_rs_queue(ctx: discord.ext.commands.Context,
                             level_arg: str = '0',
                             *,
                             comment: str = ''):
	"""
    Join RS queue
    :param comment:
    :param ctx: discord context
    :param level_arg: rs levels to start
    :return:
    """
	# handle rs commands outside of channels
	if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID and ctx.message.channel.name not in params.RS_CHANNELS.keys(
	):
		bot.get_channel(
		    ctx.message.channel.id).send("I am sorry, this won't work")
		return

	# handle rs commands in single rs channels
	elif ctx.message.channel.name in params.RS_CHANNELS:
		levels = [int(ctx.message.channel.name[2:])]

	# handle rs commands in unified rs channel
	else:
		levels = level_arg.replace(',', ' ').split(' ')

	# relay command to module (module checks for playable levels)
	for level in levels:
		if int(level) in Rs.star_range:
			  await Rs.enter_queue(ctx.author, int(level), comment, False, False)
			# Rs.add_job(
			#     Rs.enter_queue,
			#     [ctx.author, int(level), comment, False, False])

	# standard handling of commands
	await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
	print(
	    f'_enter_rs_queue: called by {ctx.author} using `{ctx.message.content}` in{ctx.channel.name}'
	)

	return


@bot.command(name='leave',
             help='Leave the RS queue',
             aliases=params.leave_queue_aliases)
async def cmd_leave_rs_queue(ctx: discord.ext.commands.Context,
                             level_arg: str = '0'):
	"""
    Leave RS queue(s)
    :param ctx: discord context
    :param level_arg: rs levels to start
    :return:
    """
	# handle rs commands outside of channels
	if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID and ctx.message.channel.name not in params.RS_CHANNELS.keys(
	):
		bot.get_channel(
		    ctx.message.channel.id).send("I am sorry, this won't work")
		return

	# handle rs commands in single rs channels
	elif ctx.message.channel.name in params.RS_CHANNELS.keys():
		levels = [int(ctx.message.channel.name[2:])]
	# handle rs commands in unified rs channel
	else:
		levels = level_arg.replace(',', ' ').split(' ')

	# relay commands to module
	for level in levels:
		if int(level) == 0:  # 0 leaves all queues
			  await Rs.leave_queue(ctx.author, int(level), False, False, False, None)
			  break
			# Rs.add_job(
			#     Rs.leave_queue,
			#     [ctx.author, int(level), False, False, False, None])
			# break

		if int(level) in Rs.star_range:
			await Rs.leave_queue(ctx.author, int(level), False, False, False,
			                     None)

	# standard handling of commands
	await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
	print(
	    f'_leave_rs_queue: called by {ctx.author} using `{ctx.message.content}` in{ctx.channel.name}'
	)

	return


@bot.command(name='display',
             help='Display the current RS queues',
             aliases=params.display_queue_aliases)
async def cmd_display_rs_queues(ctx: discord.ext.commands.Context):
    """
      Display current queues that contain at least one player
      :param ctx: discord context
      :param level: rs level to display
      :return:
      """
    # only handle rs commands in the rs channels
    if ctx.message.channel.id not in Rs.channels:
      return
    else:
      level = Rs.get_level_from_rs_string(ctx.message.channel.name)
      Rs.display_individual_queue(level)
    # standard handling of commands
    await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
    # relay command to module
    # Rs.add_job(Rs.display_individual_queue, [level])


@bot.command(name='start',
             help='Start a queue early',
             aliases=params.start_queue_aliases)
async def cmd_start_rs_queue(ctx: discord.ext.commands.Context,
                             level_arg: str = '0'):
	"""
    Start a certain queue
    :param ctx: discord context
    :param level_arg: rs levels to start
    :return:
    """
	# handle rs commands outside of channels
	if ctx.message.channel.id != params.SERVER_RS_CHANNEL_ID and ctx.message.channel.name not in params.RS_CHANNELS.keys(
	):
		bot.get_channel(
		    ctx.message.channel.id).send("I am sorry, this won't work")
		return

	# handle rs commands in single rs channels
	elif ctx.message.channel.name in params.RS_CHANNELS.keys():
		levels = [int(ctx.message.channel.name[2:])]

	# handle rs commands in unified rs channel
	else:
		levels = level_arg.replace(',', ' ').split(' ')

	# relay command to module

	counter = 0
	for level in levels:
		if int(level) in Rs.star_range:
			await Rs.start_queue(ctx.author, int(level))
			# Rs.add_job(Rs.start_queue, [ctx.author, int(level)])
			counter += 1
		if counter == 2:
			await bot.get_channel(
			    ctx.message.channel.id
			).send("You can only start one star with this command")
			break

	# standard handling of commands
	await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
	print(
	    f'_start_rs_queue: called by {ctx.author} using `{ctx.message.content}` in{ctx.channel.name}'
	)

	return


@bot.command(name='clear',
             help='Clear a queue',
             aliases=params.clear_queue_aliases)
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
	print(
	    f'cmd_clear_rs_queue(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}'
	)

	# relay command to module
	await Rs.clear_queue(ctx.author, int(level))
  # Rs.add_job(Rs.clear_queue, [ctx.author, int(level)])


#################################
# System commands module:
#################################
@bot.command(name='pig', help='ping')
async def cmd_ping(ctx):
	await ctx.message.delete(delay=params.MSG_DELETION_DELAY)
	print(
	    f'cmd_ping(): called by {ctx.author} using "{ctx.message.content}" in #{ctx.channel.name}'
	)
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
	if message.channel.id == params.SERVER_RS_CHANNEL_ID and message.content[
	    0] in '+-':
		message.content = '!' + message.content

	# hack to understand commands like "! cmd" (ignore space)
	if len(message.content
	       ) > 2 and message.content[0] == '!' and message.content[1] == ' ':
		message.content = message.content.replace(' ', '', 1)

	# hack to understand commands like "!in6" (ignore missing space)
	if re.match('^![a-z]{1,3}[1-9]+', message.content):
		message.content = message.content.replace('!in', '!in ', 1)

	await bot.process_commands(message)


dotenv.load_dotenv(verbose=True)


@bot.event
async def on_ready():

	# initialize all command modules
	Rs.init(bot)  # red star

	print('    Starting up: modules initialized')

	await clean_dead_embeds()
	await clean_logs()

	# launch loop tasks

	# if not Rs.task_process_job_queue.is_running():
	# 	Rs.task_process_job_queue.start()
	# 	print('    Starting up: launching task process_job_q')

	if not Rs.task_check_afk.is_running():
		Rs.task_check_afk.start()
		print('    Starting up: launching task check_afk')

	if not Rs.task_repost_queues.is_running():
		Rs.task_repost_queues.start()
		print('    Starting up: launching task repost_queues')


	global bot_ready
	bot_ready = True
	print(f'    Starting up: {bot.user.name} is ready')
	if dbg_ch:
		await dbg_ch.send('ℹ️ on_ready(): Bot Initialization complete')


@bot.event
async def on_connect():
	print(f'    Starting up: {bot.user.name} has connected')
	if dbg_ch:
		await dbg_ch.send('ℹ️ on_connect(): Connection (re-)established')


@bot.event
async def on_disconnect():
	print('on_disconnect(): Bot has disconnected')


@bot.event
async def on_resumed():
	print(f'\non_resumed(): {bot.user.name} has resumed\n')


@bot.event
async def on_reaction_add(reaction, user):

    global bot_ready
    if not bot_ready:
        return

    # early catch for own reactions
    elif user.id == bot.user.id:
        return
    
    try:
        if reaction.custom_emoji: emo = '⑾' 
        else: emo = reaction.emoji
        print(f'on_reaction_add: {emo} by {user.display_name}')
        name = str(reaction.message.channel.name)
        level = int(Rs.get_level_from_rs_string(name))      

        # dashboard
        if level == 0:
          await Rs.handle_reaction(user, reaction)

        # single que
        elif level in Rs.star_range:
            await Rs.handle_single_queue_reaction(user, reaction, level, name)
            return

    except discord.errors.HTTPException as e:
        print(f'on_reaction_add: discord.errors.HTTPException {str(e)}')
    except discord.DiscordException as e:
        print(f'⚠️ [on_reaction_add]: generic discord exception {str(e)}')
    except Exception as e:
        print(f'⚠️ [on_reaction_add]: generic exception {str(e)} reaction:{reaction}')
        Rs.lumberjack(sys.exc_info())


@bot.event
async def on_command_error(ctx, error):

	print(f'on_command_error(): {error}')
	print(
	    f'on_command_error(): message was: "{ctx.message.content}" sent by {ctx.author.name} in #{ctx.channel.name}'
	)

	print(
	    f'**ERROR**\n{error}\n**REASON**\n"{ctx.message.content}" sent by {ctx.author.name} in #{ctx.channel.name}'
	)

	try:
		await ctx.message.add_reaction('🤖')
		# await ctx.message.add_reaction('❔')
	except discord.errors.NotFound:
		print('on_command_error(): message was deleted -> no reaction')
	except Exception:
		pass

	if isinstance(error, commands.errors.CheckFailure):
		await ctx.send(f'{ctx.author.mention} You do not have the correct role for this command!', delete_after=params.MSG_DISPLAY_TIME)
	
	elif isinstance(error, commands.errors.MissingPermissions):
		await ctx.send(f'{ctx.author.mention} I\'m missing permissions to do that!', delete_after=params.MSG_DISPLAY_TIME)

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
# dotenv.load_dotenv(verbose=True)
bot.run(os.getenv("DISCORD_TOKEN"))
