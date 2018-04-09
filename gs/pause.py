import pygame

from font import FONT_MEDIUM
from game_constants import *
from game_state import GameState
from widget import Menu


class GSPause(GameState):
    FLICKER = 15

    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.root.add(PauseMenu(self, (325, 350)))
        self.font = FONT_MEDIUM
        self.frames = 0
        self.flicker = False

    def update(self):
        super().update()
        self.frames = (self.frames + 1) % (GSPause.FLICKER * 2)

    def draw(self):
        self.surf.blit(self.parent.surf, (0, 0))
        # We can have a cute flashing on the pause screen!! Very optional
        if not self.flicker or self.frames < GSPause.FLICKER:
            self.surf.blit(self.font.render("PAUSED", True, (100,100,0)), (325, 250))
        super().draw()


class PauseMenu(Menu):
    def __init__(self, parent, pos):
        super().__init__(parent, pos)
        self.add_item("Unpause", "kill_state")
        self.add_item("Quit Level", "parent.kill_state")
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 80
        self.font = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 60)