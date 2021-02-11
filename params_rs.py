###################################################
# DISCORD                                         #
###################################################
DEBUG_MODE = False
SERVER_DEBUG_CHANNEL_ID = 806307634000166922 #log
SERVER_BUG_CHANNEL_ID = 808499006510596166 #bug reporting
SERVER_DISCORD_ID = 760481068959662081
SERVER_DISCORD_NAME = "RS Club"
SERVER_DISCORD_ICON = "https://cdn.discordapp.com/icons/760481068959662081/12ed9c2aa500b992332a630dac7d101d.png?size=128"

BOT_DISCORD_ICON = SERVER_DISCORD_ICON
RS_ICON = '<:redstar:807239811068329985>'

# CHANNEL IDs
SERVER_RS_CHANNEL_ID = 806307789147602994 if DEBUG_MODE is False else SERVER_DEBUG_CHANNEL_ID

SUPPORTED_RS_LEVELS_MIN = 6
SUPPORTED_RS_LEVELS_MAX = 10

SUPPORTED_RS_LEVELS = range(SUPPORTED_RS_LEVELS_MIN, SUPPORTED_RS_LEVELS_MAX + 1)

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

###################################################
# TIME CONSTANTS (in sec)                         #
###################################################
TIME_BOT_AFK_TASK_RATE = 50
TIME_BOT_Q_TASK_RATE = 30

TIME_SPAM_BRAKE = 10
TIME_AFK_WARN = 60 * 10  # afk warning as ping; afk_flag set in checker task after warning!
TIME_AFK_KICK = 60 * 15  # kick if warning ignored. must be bigger than TIME_AFK_WARN!
TIME_Q_REPOST = 60
TIME_Q_REPOST_COOLDOWN = 1
MSG_DELETION_DELAY = 7
RULES_DELETION_DELAY = 60 * 3
MSG_DISPLAY_TIME = 7
INFO_DISPLAY_TIME = 60 * 5
PING_COOLDOWN = 60 * 5  # time that has to pass before ping_all_role can be mentioned again

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

SERVER_PING_ROLES = ['rs4','rs5','rs6','rs7','rs8','rs9','rs10','rs11'] # 3/4 4/4
SERVER_SOFT_PING_ROLES = ['rs4s','rs5s','rs6s','rs7s','rs8s','rs9s','rs10s','rs11s'] # 3/4 4/4
SERVER_SOFT_NO_ROLES = ['rs4n','rs5n','rs6n','rs7n','rs8n','rs9n','rs10n','rs11n'] # 3/4 4/4

SERVER_PING_ROLES_IDS = ['806315919311765524','806315873677606932','760783110006112286','760869215094833163','760869271273209866','760869324541263934','760869611867471943','760869649297440829'] # 1/4 2/4 3/4 4/4
SERVER_SOFT_PING_ROLES_IDS = ['807273643947196426','807273555506233374','760876265321922581','760876269473890314','760876272716087306','760876284238102548','760876287584632893','760876291024486410'] # 3/4 4/4
SERVER_NO_PING_ROLES_IDS = ['807273699975757844','807273767050936320','760876294593970178','760876307939721247','760876311500554271','760876315359445042','760876318979522590','760876322393686046'] # 4/4)

###################################################
# COMMAND ALIASES                                 #
###################################################
help_aliases = ['h', 'H', 'Help']

# RS
rs_help_aliases = ['rsh']
rs_aliases = ['rsc', 'Rs', 'rS', 'RS', 'RSC', 'Rsc']
rs_stats_aliases = []
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
EMBED_QUEUE_COLOR = 0x2f3136

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
JOIN_EMOJI = "🆕"
LEAVE_EMOJI = "❎"
START_EMOJI = "▶"
CONFIRM_EMOJI = "✅"
CANCEL_EMOJI = "❎"
GO_BACK_EMOJI = "🔙"
DOWN_EMOJI = "⬇" 

PING_THRESHOLDS = [1, 2, 3] # ping at these queue sizes only

MAX_RS_NOTE_LENGTH = 50

MAX_RS_NOTE_LENGTH = 50

MAX_RS_NOTE_LENGTH = 50

MAX_RS_NOTE_LENGTH = 50

# TEXTS 

RULES_CHANNEL_ID = 805568314998784002
RULES_MESSAGE_ID = 805569774822096916
RULES_MESSAGE_ID_FR = 805569774822096916

TEXT_EMPTY_QUEUE = 'Start a new queue by typing `!in` or reacting below!\n' \
                                'Questions? `!help`, Hide/Restore channel: `!rs`\n' \
                                f'Bugs or Ideas? Please report them in '

TEXT_RULES_TITLE = 'Club Rules'

TEXT_RULES_EN = f'Don’t be a…\n' \
           f'**`D`**oes not communicate.\n' \
           f'**`I`**s unaware of teammates\' builds and strategies.\n' \
           f'**`C`**lears without focusing planet sectors.\n' \
           f'**`K`**ills teammates with thoughtless play.'
TEXT_RULES = TEXT_RULES_EN

# @zofia: careful with mobile version of discord!
# @BenSmith30: I think this is exactly what fits on mobile... No?
#TEXT_FOOTER_TEXT = '___________________________________________________\n' \
#+ DOWN_EMOJI +'Join.Unirse.Вступать.加入 Quit.Dejar.Уехать.退出'+ LEAVE_EMOJI
TEXT_FOOTER_TEXT = '\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f' #this is a stupid Zofia's hack to keep the minimal width od embedd sensible
