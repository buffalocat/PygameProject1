"""Abstract base class for game states"""

import pygame

from game_constants import *
from widget import Root


class GameState:
    def __init__(self, mgr, parent=None):
        # We always need a reference to the manager, so we can switch states
        self.mgr = mgr
        # Parent is the state that we came from
        self.parent = parent
        # The widget
        self.root = Root()
        # Each gamestate has its own surface to print to
        self.surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pass

    def handle_input(self):
        self.root.handle_input()
        pygame.event.clear()

    def update(self):
        self.root.update()

    def draw(self):
        self.root.draw(self.surf)

    def quit(self):
        """Perform any necessary clean-up before leaving a state for good"""
        pass