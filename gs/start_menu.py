"""The main menu. In most games, it's the top state on the stack"""

import pygame

from background import BGGrid, BGColorChangeGrid, BGCrystal
from font import FONT_LARGE
from game_constants import *
from game_state import GameState
from gs.color_select import GSColorSelect
from gs.connection_setup import GSConnectionSetup
from gs.go import GSGo
from gs.sokoban import GSSokoban
from widget import Menu


class GSStartMenu(GameState):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.root.set_bg(BGCrystal(WINDOW_HEIGHT, WINDOW_WIDTH, (200,100,200)))
        self.root.add(StartMenu(self, (10, 10)))

    def play_go(self):
        GSGo(self.mgr, self)

    def play_sokoban(self):
        GSSokoban(self.mgr, self)

    def connection_setup(self):
        GSConnectionSetup(self.mgr, self)

    def color_select(self):
        GSColorSelect(self.mgr, self)


# Note: the parent of StartMenu is the StateManager, because
# all of the methods involve switching states.
# If later we make GSStartMenu be the parent instead,
# we have to append "mgr." to the beginning of each method
class StartMenu(Menu):
    def __init__(self, parent, pos):
        super().__init__(parent, pos)
        self.add_item("Play Go (Local)", "play_go")
        self.add_item("Play Sokoban", "play_sokoban")
        self.add_item("Quit", "terminate")
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 80
        self.font = FONT_LARGE