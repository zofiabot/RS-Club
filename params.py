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
        param = f"{x} = {y}"
        exec(param)
        
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
    SERVER_DISCORD_NAME = 'Red Star Club'
    QUEUE_EMBED_ICON = ''
    QUEUE_EMBED_TITLE = ''
    RS_ICON = '<:redstar:807239811068329985>'
    help_aliases = ['h', 'H', 'Help', 'rsh']
    # rs_aliases = ['rsc', 'Rs', 'rS', 'RS', 'RSC', 'Rsc']
    rs_stats_aliases = ['st', 't']
    rs_rules_aliases = ['r', 'rsr', 'rsrule', 'rule', 'rules']
    display_queue_aliases = ['q', 'Q', 'queue', 'Queue']
    enter_queue_aliases = ['i', 'I', 'in', 'In', 'IN', 'iN', 'join', 'Join', '1']
    leave_queue_aliases = ['o', 'O', 'out', 'Out', 'OUT']
    start_queue_aliases = ['s', 'S', 'Start']
    clear_queue_aliases = ['c', 'C', 'Clear']
    SERVER_DISCORD_ICON = 'https://cdn.discordapp.com/icons/760481068959662081/12ed9c2aa500b992332a630dac7d101d.png?size=512'
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

    RS_EMOJIS = [RS4_EMOJI, RS5_EMOJI, RS6_EMOJI, RS7_EMOJI, RS8_EMOJI, RS9_EMOJI, RS10_EMOJI, RS11_EMOJI]
    TEXT_EMPTY_QUEUE = f'Start a new queue by reacting with {JOIN_EMOJI}\nLeave by reacting with {UNQUEUE_EMOJI}\nStart queue without full squad using {START_EMOJI}\nRules? `!r` Questions? `!h`\nBugs or Ideas? Please report in '
    TEXT_EMPTY_QUEUE_DASH = 'Start a new queue by reacting below!\nLeave **all queues** by reacting with ❎\nBugs or Ideas? Please report them in '
    TEXT_R_NOMSG = "I'm sorry, but no messages are allowed in relay channel.\nPlease ask <@{}> to secure the chnnel or remove relay with `relayremove`"
    TEXT_R_SET = '` Setting up ` Your Relay will display here soon'
    TEXT_R_REMOVE = 'Sorry to see you go.\nPlease remember to uninvite the bot. **Leaving it connected to your server while not using it might have unintended consequences**.'
    TEXT_R_FOOTER = f'[Join the {SERVER_DISCORD_NAME} to join the queue!](https://discord.gg/m8BSBfpj8J)'
    TEXT_EMPTY_R_DASH = f'[Join the {SERVER_DISCORD_NAME} server to join the queue!](https://discord.gg/m8BSBfpj8J)'
    TEXT_CHECKOUT_DEMO = 'Go to [demo server](https://discord.gg/39PQUNwR95) to install on your server'
    TEXT_WELCOME_MESSAGES = [':flag_gb:\u2800Hi', ':flag_tr:\u2800Selam', ':flag_pl:\u2800Cześć', ':flag_es:\u2800¡Hola', ':flag_th:\u2800หวัดดี', ':flag_hu:\u2800Szia', ':flag_ru:\u2800Привет', ':flag_fr:\u2800Salut', ':flag_pt:\u2800Oi', ':flag_nl:\u2800Hoi!', ':flag_vn:\u2800Chào!', ':flag_it:\u2800Ciao', ':flag_cn:\u2800你好', ':flag_kr:\u2800안녕', ':flag_gr:\u2800\u2800Γεια', ':flag_il:\u2800היי', ':flag_ir:\u2800سلام', ':flag_de:\u2800Hallo', ':flag_ro:\u2800Bună']
    TEXT_SPECIAL_WELCOME = 'Oh.. Hi {}! You have finally arrived!\nThe next round of rum is on you!'
    INVITE_RANKING = True

    
    INVITE_RANKING_DESC = 'The contest ends on March 31ˢᵗ ᴳᴹᵀ\nTo participate, create an invite link\n(never expiring, no limit of users)\nand spread the word wherever you can.\n Please obey other server\'s rules,\nreasonable complaints will result\nin disqualification.\n\n'
    INVITE_RANKING_DESC += f'\u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 \u2800 **Rewards**\n :first_place:` 20 level 10 and 9 artifacts (40) `\n :second_place:` 10 level 10 and 9 artifacts (20) `\n :third_place:` \u28005 level 10 and 9 artifacts (10) `\n\u2800\u2800 \u2800\u2800 \u2800 (thank you @madman89)'


    REMEMBER_TO_CONFIRM_IMG = 'https://media.discordapp.net/attachments/805642819980754944/819677453315342406/remember-to-confirm.png'

    LANGUAGE_LABEL_GB = 'English'
    LANGUAGE_LABEL_ES = 'Español'
    LANGUAGE_LABEL_BR = 'Português'
    LANGUAGE_LABEL_FR = 'Français'
    LANGUAGE_LABEL_DE = 'Deutsch'
    LANGUAGE_LABEL_PL = 'Polski'
    LANGUAGE_LABEL_RU = 'Русский'
    LANGUAGE_LABEL_TR = 'Türkçe'
    RULES_MESSAGE_LABEL_GB = 'Rules in English\u2009 \u2800 \u2800\u2800'
    RULES_MESSAGE_LABEL_ES = 'Reglas en español'
    RULES_MESSAGE_LABEL_BR = 'Regras em português'
    RULES_MESSAGE_LABEL_FR = 'Règles en français\u2009 '
    RULES_MESSAGE_LABEL_DE = 'Regeln auf Deutsch\u2800 '
    RULES_MESSAGE_LABEL_PL = 'Zasady po polsku'
    RULES_MESSAGE_LABEL_RU = 'Правила на русском'
    RULES_MESSAGE_LABEL_TR = 'Türkçe Kurallar'
    
    WELCOME_STRINGS = [ 'ciao', 'bem-vinda', 'Willkommen', 'ようこそ', 'bienvenida', 'dobrodošli', 'karibu', 'приве́т', 'chào mừng', 'hosgeldiniz', 'witamy', 'καλως ΗΡΘΑΤΕ', '欢迎', 'merhba', '환영', 'bine ati venit' ]

