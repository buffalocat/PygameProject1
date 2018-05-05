"""Measures the difference in game state from one frame to the next"""

from game_constants import *


class Delta:
    def __init__(self):
        self.reset_moves()
        self.group_merges = []
        # Deltas for dynamic objects and structures are input "backwards":
        # Tell it the state you want it to REVERT to, not the state that it changed to
        self.dynamic = []
        self.structure = []

    def add_move(self, obj, dpos):
        self.moves[dpos].append((obj.pos, obj.layer))

    def reset_moves(self):
        self.moves = {dir: [] for dir in DIR.values()}

    def add_group_merge(self, groups):
        self.group_merges.append(groups)

    def add_dynamic(self, obj, delta):
        self.dynamic.append((obj, delta))

    def add_structure(self, obj, delta):
        self.structure.append((obj, delta))