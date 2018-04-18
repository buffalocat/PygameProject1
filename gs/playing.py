"""A generic game state (not yet implemented)"""

# Note: multiplayer doesn't really exist yet,
# and this would require online/local rooms to be unified

import pygame
from enum import IntEnum

from game_constants import *
from game_state import GameState
from room import Signal


class GSPlaying(GameState):
    def __init__(self, mgr, parent, room, game):
        super().__init__(mgr, parent)
        self.root.set_color(LIGHT_BROWN)
        self.room = room
        self.room.state = self
        self.game = game(self, self.room.id)

    def handle_input(self):
        self.game.handle_input()

    def update(self):
        super().update()
        self.room.check_q()

    def draw(self):
        super().draw()
        self.game.draw_board(self.surf)

    def quit(self):
        self.room.state = self.parent

    def send_move(self, move):
        self.room.send_all(Signal.GAME_MOVE, list(move))



class Game:
    def __init__(self, state):
        self.state = state