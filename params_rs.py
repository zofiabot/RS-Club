###################################################
# DISCORD                                         #
###################################################
DEBUG_MODE = True
SPLIT_CHANNELS = True
SERVER_DEBUG_CHANNEL_ID = 806307634000166922 #log
SERVER_BUG_CHANNEL_ID = 808499006510596166 #bug reporting
SERVER_DISCORD_ID = 760481068959662081
SERVER_DISCORD_NAME = ''
SERVER_DISCORD_ICON = 'https://cdn.discordapp.com/icons/760481068959662081/12ed9c2aa500b992332a630dac7d101d.png?size=512'

BOT_DISCORD_ICON = SERVER_DISCORD_ICON

QUEUE_EMBED_ICON = ''
QUEUE_EMBED_TITLE = ''

RS_ICON = '<:redstar:807239811068329985>'

# CHANNEL IDs
SERVER_RS_CHANNEL_ID = 806307789147602994

RS_CHANNELS = {
'rs4': 807270877011116113,
'rs5': 807270800583163975,
'rs6': 760481958928187442,
'rs7': 760481915622260767,
'rs8': 760481821531701309,
'rs9': 760481766179340288,
'rs10': 760481703071973388,
'rs11': 760481388440453190
}

SUPPORTED_RS_LEVELS_MIN = 8
SUPPORTED_RS_LEVELS_MAX = 11

SUPPORTED_RS_LEVELS = range(SUPPORTED_RS_LEVELS_MIN, SUPPORTED_RS_LEVELS_MAX + 1)

###################################################
# TIME CONSTANTS (in sec)                         #
###################################################
TIME_BOT_AFK_TASK_RATE = 30 #check for afk
TIME_BOT_QUEUE_TASK_RATE = 20
TIME_BOT_JOB_TASK_RATE =  3 # (TIME_BOT_QUEUE_TASK_RATE/len(SUPPORTED_RS_LEVELS))*0.9


TIME_SPAM_BRAKE = 15
TIME_AFK_WARN = 60 * 10  # afk warning as ping; afk_flag set in checker task after warning!
TIME_AFK_KICK = 60 * 15  # kick if warning ignored. must be bigger than TIME_AFK_WARN!
TIME_Q_REPOST = 10
TIME_Q_REPOST_COOLDOWN = 0.1
MSG_DELETION_DELAY = 7
MSG_DISPLAY_TIME = 7
RULES_DELETION_DELAY = 60
HELP_DELETION_DELAY = 15
INFO_DISPLAY_TIME = 60 * 1
PING_COOLDOWN = 60 # time that has to pass before ping_all_role can be mentioned again

###################################################
# ROLES                                           #
###################################################

SERVER_MEMBER_ROLE = 'rs'
SERVER_MEMBER_ROLE_ID = 760976687068217375
SERVER_RS_ROLE_ID = SERVER_MEMBER_ROLE_ID

SERVER_MODERATOR_ROLE = 'moderator'
SERVER_MODERATOR_ROLE_ID = 760483507075153920

SERVER_ADMIN_ROLES = 'admin'
SERVER_ADMIN_ROLE_ID = 760483671877746738

SERVER_MEMBER_ROLES = ['rs']
SERVER_ALLY_ROLES = ['rs']
SERVER_MODERATOR_ROLES = ['moderator']
SERVER_ADMIN_ROLES = ['admin']

RS4_ROLE = 'vrs4'
RS5_ROLE = 'vrs5'
RS6_ROLE = 'vrs6'
RS7_ROLE = 'vrs7'
RS8_ROLE = 'vrs8'
RS9_ROLE = 'vrs9'
RS10_ROLE = 'vrs10'
RS11_ROLE = 'vrs11'

RS_ROLES = [RS4_ROLE, RS5_ROLE, RS6_ROLE, RS7_ROLE, RS8_ROLE, RS9_ROLE, RS10_ROLE, RS11_ROLE]

RESTRICTING_ROLES =  ['no4','no5','no6','no7','no8','no9','no10','no11'] # for players who can't make it in given RS level

SERVER_RS_ACCESS_ROLES_IDS = ['807272608130138122','807272531006193684','807265218404941854','807265401481592913','807265512727904306','807265593912852510','807265647674523690','807265734278512671'] #aka VRS roles

# 4/4 pings just users in queue (by nick)
SERVER_PING_ROLES = ['rs4','rs5','rs6','rs7','rs8','rs9','rs10','rs11'] # 1/4 2/4
SERVER_SOFT_PING_ROLES = ['rs4s','rs5s','rs6s','rs7s','rs8s','rs9s','rs10s','rs11s'] # 3/4
SERVER_SOFT_NO_ROLES = ['rs4n','rs5n','rs6n','rs7n','rs8n','rs9n','rs10n','rs11n'] # none

PING_THRESHOLDS = [1, 2, 3] # ping at these queue sizes only

OLD_STARS = {'rs6' : 0, 'rs7' : 0, 'rs8' : 1, 'rs9' : 118, 'rs10' : 0, 'rs11' : 0}

###################################################
# COMMAND ALIASES                                 #
###################################################
help_aliases = ['h', 'H', 'Help','rsh']

# RS
#rs_help_aliases = ['rsh']
rs_aliases = ['rsc', 'Rs', 'rS', 'RS', 'RSC', 'Rsc']
rs_stats_aliases = ['st', 't']
rs_rules_aliases = ['r', 'rsr', 'rsrule', 'rule', 'rules']
display_queue_aliases = ['q', 'Q', 'queue', 'Queue']
enter_queue_aliases = ['i', 'I', 'in', 'In', 'IN', 'iN', 'join', 'Join']
leave_queue_aliases = ['o', 'O', 'out', 'Out', 'OUT']
start_queue_aliases = ['s', 'S', 'Start']
clear_queue_aliases = ['c', 'C', 'Clear']

###################################################
# APPEARANCE                                      #
###################################################
EMBED_COLOR = 0xff6600
QUEUE_EMBED_COLOR = 0x2f3136

# rs emojis
RS0_EMOJI = "0️⃣"
RS1_EMOJI = "1️⃣"
RS2_EMOJI = "2️⃣"
RS3_EMOJI = "3️⃣"
RS4_EMOJI = "4️⃣"
RS5_EMOJI = "5️⃣"
RS6_EMOJI = "6️⃣"
RS7_EMOJI = "7️⃣"
RS8_EMOJI = "8️⃣"
RS9_EMOJI = "9️⃣"
RS10_EMOJI = "🔟"
RS11_EMOJI = "<:eleven:760869824036601939>"
RS11_EMOJI_ID = 760869824036601939

RS_EMOJIS =  [RS4_EMOJI, RS5_EMOJI, RS6_EMOJI, RS7_EMOJI, RS8_EMOJI, RS9_EMOJI, RS10_EMOJI, RS11_EMOJI]

# dialogues
JOIN_EMOJI = "➕"
UNJOIN_EMOJI = "➖"
LEAVE_EMOJI = "❎"
START_EMOJI = "✔️"
CONFIRM_EMOJI = "✅"
CANCEL_EMOJI = "❎"
GO_BACK_EMOJI = "🔙"
DOWN_EMOJI = "⬇" 
WARNING_EMOJI = "⚠️"


MAX_RS_NOTE_LENGTH = 20


# TEXTS 

RULES_CHANNEL_ID = 805568314998784002
RULES_MESSAGE_ID = 805569774822096916
RULES_MESSAGE_ID_FR = 805569774822096916

TEXT_EMPTY_QUEUE = 'Start a new queue by typing `!in` or reacting below!\n'\
                                'Leave by reacting with ❎\n'\
                                'Questions? `!help`\n'\
                                f'Bugs or Ideas? Please report them in '
TEXT_EMPTY_QUEUE_DASH = 'Start a new queue by reacting below!\n'\
                                'Leave **all queues** by reacting with ❎\n'\
                                f'Bugs or Ideas? Please report them in '

TEXT_RULES_FORMAT = 'Message'
TEXT_RULES_TITLE = 'Club Rules'
TEXT_RULES_EN = 'Lorem ipsum sit amet...'
TEXT_RULES = TEXT_RULES_EN

TEXT_MEET_WERE = '...meet where?'
TEXT_NOROLESET = "you didn't sellect ping level for"
TEXT_STILL_AROUND = 'still around? Confirm below.'

TEXT_FOOTER_TEXT = '\u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800   \u2800' #Zofia's magic works on mobile and pc
