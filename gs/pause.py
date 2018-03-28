import pygame

from game_constants import *
from gs.game_state import GameState, Menu


class GSPause(GameState):
    FLICKER = 15

    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.frames = 0
        self.flicker = False
        self.menu = PauseMenu(self)
        self.font = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 50)

    def update(self):
        self.menu.update()
        for event in pygame.event.get(KEYDOWN):
            if event.key == K_p:
                self.mgr.unpause()
                return
            elif event.key == K_s:
                self.mgr.step_frame()
                return
        pygame.event.clear()
        self.frames = (self.frames + 1) % (GSPause.FLICKER * 2)

    def draw(self, surf):
        self.surf.blit(self.parent.surf, (0, 0))
        # We can have a cute flashing on the pause screen!! Very optional
        if not self.flicker or self.frames < GSPause.FLICKER:
            self.surf.blit(self.font.render("PAUSED", True, (100,100,0)), (325, 250))
        self.menu.draw(self.surf, (325, 350))
        super().draw(surf)


class PauseMenu(Menu):
    def __init__(self, parent):
        super().__init__(parent)
        self.add_item("Unpause", "kill_state")
        self.add_item("Quit Level", "parent.kill_state")
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 80
        self.font = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 60)