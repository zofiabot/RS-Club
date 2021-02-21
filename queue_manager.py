from typing import List

from player import Player
import time
from params import params
import jsonpickle


class QueueManager:

    PLAYER_JOINED = 0
    PLAYER_RESET_AFK_FLAG = 1
    PLAYER_ALREADY_IN_QUEUE = 2
    PLAYER_LEFT = 3
    PLAYER_JOINED_WITH_MATES = 4
    PLAYER_MATE_LEFT = 5
    PLAYER_MATE_JOINED = 6
    PLAYER_CANNOT_JOIN_MATE = 7
    QUEUE_FULL = 8

    NOTHING = 10

    def __init__(self, queue_name: str, queue_level: int, queue_color: int):
        self.name = queue_name  # the rs_level (int) must be part of this string
        self.level = queue_level  # rs as integer
        self.color = queue_color

        # backed up in file as tuple:
        self.last_role_ping = 0
        self.age = time.time()
        self.queue: List[Player] = []

        # was queue updated (join, leave by backup_queue + restore_queue, set flag)
        self.updated: bool = False

        # load from file
        self.restore_queue()

    def new_player(self, player: Player):
        # check if this player is already in a queue

        q = self.queue
        for p in q:
            # player found
            if p == player:
                p.timer = time.time()
                # afk reset
                if p.afk_flag is True:
                    p.afk_flag = False
                    self.backup_queue()
                    return self.PLAYER_RESET_AFK_FLAG, p, q
                # do nothing
                else:
                    return self.PLAYER_ALREADY_IN_QUEUE, p, q

        if len(self.queue) == 0:
            self.age = time.time()

        # simply put the player in the queue
        if len(self.queue) < 4:
            self.queue.append(player)
            self.backup_queue()
            return self.PLAYER_JOINED, player, self.queue
        # two joins in very short time may cause this
        else:
            return self.QUEUE_FULL, None, q

    def player_left(self, player: Player):
        # check queue and remove the player
        q = self.queue
        for p in q:
            if p == player:
                q.remove(p)
                self.backup_queue()
                return self.PLAYER_LEFT, q
        # player not found
        return self.NOTHING, q

    def get_queue_ready(self):
        if len(self.queue) == 4:
            self.updated = True
            return self.queue
        return False

    def clear_queue(self):
        self.queue.clear()
        self.backup_queue()

    def get_and_update_afk_players(self):
        now = time.time()
        afk = []
        updated = False
        for p in self.queue:
            p.afk_timer = int(round(now - p.timer))
            if p.afk_timer > params.TIME_AFK_WARN:
                afk.append(p)
                updated = True
        if updated: self.backup_queue()
        return afk

    def get_queue_age(self):
        return self.age

    def set_queue_age(self, time_set):
        self.age = time_set

    def get_queue_updated(self):
        return self.updated

    def set_queue_displayed(self):
        self.updated = False

    def find_player_in_queue_by_discord(self, author, id: int = 0):
        for p in self.queue:
            if p.discord_id == id or (author is not None
                                      and p.discord_id == author.id):
                return p
        return None

    def backup_queue(self):
        self.updated = True
        data = jsonpickle.encode((self.age, self.last_role_ping, self.queue))
        file = open(f'rs/{self.name}.txt', 'w')
        file.write(data)
        file.close()
        print(f'qm{self.level:>2} backup: done')

    def restore_queue(self):
        try:
            file = open(f'rs/{self.name}.txt', 'r')
            data = jsonpickle.decode(file.read())
            self.age = data[0]
            self.last_role_ping = data[1]
            self.queue = data[2]
            file.close()
            print(f'       queue {self.level:>2}: restored')
            self.updated = True
        except FileNotFoundError:
            print(f'       queue {self.level:>2}: file not found')
    
