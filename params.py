#from dataclasses import dataclass, make_dataclass
import os
from dotenv import load_dotenv
load_dotenv()

class params:
    a = os.environ
    b = os.environ.values()
    c = zip(a,b)
    for x,y in c:
      try:
        b = f"{x} = {y}"
        exec(b)
        
      except Exception:
        continue
    
    JOIN_EMOJI = '➕'
    UNQUEUE_EMOJI = '✖️'
    UNJOIN_EMOJI = '➖'
    START_EMOJI = '✔️'
    LEAVE_EMOJI = '❎'
    CONFIRM_EMOJI = '✅'
    CANCEL_EMOJI = '❎'
    GO_BACK_EMOJI = '🔙'
    DOWN_EMOJI = '⬇'
    WARNING_EMOJI = '⚠️'
    RS0_EMOJI = '0️⃣'
    RS1_EMOJI = '1️⃣'
    RS2_EMOJI = '2️⃣'
    RS3_EMOJI = '3️⃣'
    RS4_EMOJI = '4️⃣'
    RS5_EMOJI = '5️⃣'
    RS6_EMOJI = '6️⃣'
    RS7_EMOJI = '7️⃣'
    RS8_EMOJI = '8️⃣'
    RS9_EMOJI = '9️⃣'
    RS10_EMOJI = '🔟'
    RS11_EMOJI = '<:eleven:760869824036601939>'
    RS11_EMOJI_ID = 760869824036601939
    
    TEXT_RULES_FORMAT = 'Message'
    TEXT_RULES_TITLE = 'Club Rules'
    TEXT_RULES_EN = 'Lorem ipsum sit amet...'
    TEXT_RULES = TEXT_RULES_EN
    TEXT_MEET_WERE = '...meet where?'
    TEXT_NOROLESET = "you didn't select ping level for"
    TEXT_STILL_AROUND = 'still around? Confirm below.'
    TEXT_FOOTER_TEXT = '\u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800   \u2800'
    TEXT_FOOTER_SINGLE_Q_TEXT = ''
    SERVER_DISCORD_NAME = ''
    QUEUE_EMBED_ICON = ''
    QUEUE_EMBED_TITLE = ''
    RS_ICON = '<:redstar:807239811068329985>'
    help_aliases = ['h', 'H', 'Help', 'rsh']
    # rs_aliases = ['rsc', 'Rs', 'rS', 'RS', 'RSC', 'Rsc']
    rs_stats_aliases = ['st', 't']
    rs_rules_aliases = ['r', 'rsr', 'rsrule', 'rule', 'rules']
    display_queue_aliases = ['q', 'Q', 'queue', 'Queue']
    enter_queue_aliases = ['i', 'I', 'in', 'In', 'IN', 'iN', 'join', 'Join']
    leave_queue_aliases = ['o', 'O', 'out', 'Out', 'OUT']
    start_queue_aliases = ['s', 'S', 'Start']
    clear_queue_aliases = ['c', 'C', 'Clear']
    SERVER_DISCORD_ICON = 'https://cdn.discordapp.com/icons/760481068959662081/12ed9c2aa500b992332a630dac7d101d.png?size:512'
    BOT_DISCORD_ICON = SERVER_DISCORD_ICON

    CUSTOM_Q_EMOJI = False

    if SERVER_RS_CHANNEL_ID == 814879133230301184:
        RS11_EMOJI_ID = 814898233922945064
        RS11_EMOJI = f'<:eleven:{RS11_EMOJI_ID}>'
        RS_ICON = '<:redstar:814987855079669821>'
    else:
        JOIN_EMOJI = '<:join_add:815660817541365761>'
        UNQUEUE_EMOJI = '<:leave:815660817592614924>'
        UNJOIN_EMOJI = '<:remove:815660817479106591>'
        START_EMOJI = '<:start_early:815660818205114428>'
            
        JOIN_EMOJI_ID = 815660817541365761
        UNQUEUE_EMOJI_ID = 815660817592614924
        UNJOIN_EMOJI_ID = 815660817479106591
        START_EMOJI_ID = 815660818205114428
        CUSTOM_Q_EMOJI = True

    RS_EMOJIS =  [RS4_EMOJI, RS5_EMOJI, RS6_EMOJI, RS7_EMOJI, RS8_EMOJI, RS9_EMOJI, RS10_EMOJI, RS11_EMOJI]
    TEXT_EMPTY_QUEUE = f'Start a new queue by reacting with {JOIN_EMOJI}\nLeave by reacting with {UNJOIN_EMOJI}\nStart queue without full squad using {START_EMOJI}\nRules? `!r` Questions? `!h`\nBugs or Ideas? Please report in '
    TEXT_EMPTY_QUEUE_DASH = 'Start a new queue by reacting below!\nLeave **all queues** by reacting with ❎\nBugs or Ideas? Please report them in '