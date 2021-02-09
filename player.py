import time
import re
import discord

import params_rs as params


class Player:

    def __init__(self, user: discord.Member, note: str = '', mates=0):
        # clean version for logs
        self.discord_name = re.sub('[^0-9a-zA-Z# ]+', '', user.name + '#' + user.discriminator)
        self.discord_nick = user.display_name

        self.discord_mention = user.mention
        self.discord_id = user.id
        self.note = note[0:params.MAX_RS_NOTE_LENGTH] + '...' \
            if len(note) > params.MAX_RS_NOTE_LENGTH else note
        self.mates = mates

        self.afk_flag = False
        self.timer = time.time()
        self.afk_timer = 0

    def __eq__(self, other):
        return self.discord_id == other.discord_id
