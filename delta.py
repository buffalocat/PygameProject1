"""Measures the difference in game state from one frame to the next"""

from game_constants import *


class Delta:
    def __init__(self):
        self.reset_moves()
        self.group_merges = []

    def add_move(self, obj, dpos):
        self.moves[dpos].append((obj.pos, obj.layer))

    def reset_moves(self):
        self.moves = {dir: [] for dir in DIR.values()}

    def add_group_merge(self, groups):
        self.group_merges.append(groups)

    def __str__(self):
        return f"{self.moves}\n{self.group_merges}\n"