from game_constants import *
from game_state import GameState

class GSPlaying(GameState):
    def __init__(self, mgr, parent, room, game):
        super().__init__(mgr, parent)
        self.root.set_color(LIGHT_BROWN)
        self.room = room
        self.game = game

    def update(self):
        pass




class Player:
    def __init__(self, id, name, address):
        pass


class Game:
    def __init__(self):
        pass
