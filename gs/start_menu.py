import pygame

from game_constants import *
from gs.game_state import GameState, Menu


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

class StartMenu(Menu):
    def __init__(self, parent):
        super().__init__(parent)
        # We need to give state_manager a play method!
        # self.add_item("Play", "play")
        self.add_item("Quit", "terminate")
        self.add_item("Color Select", "color_select")  # Remove this item when the menu is fuller
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 80
        self.font = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 60)