"""The main menu. In most games, it's the top state on the stack"""

import pygame

from font import FONT_LARGE
from game_constants import *
from game_state import GameState, Menu


class GSStartMenu(GameState):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.bg = GREEN
        self.menu = StartMenu(mgr)

    def update(self):
        self.menu.update()
        pygame.event.clear()

    def draw(self, surf):
        self.surf.fill(self.bg)
        self.menu.draw(self.surf, (10, 10))
        super().draw(surf)


# Note: the parent of StartMenu is the StateManager, because
# all of the methods involve switching states.
# If later we make GSStartMenu be the parent instead,
# we have to append "mgr." to the beginning of each method
class StartMenu(Menu):
    def __init__(self, parent):
        super().__init__(parent)
        # We need to give state_manager a play method!
        # self.add_item("Play", "play")
        self.add_item("Quit", "terminate")
        self.add_item("Play", "connection_setup")
        self.add_item("Color Select", "color_select")
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 80
        self.font = FONT_LARGE