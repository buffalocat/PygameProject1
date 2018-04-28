"""Abstract base class for game states"""

import pygame

from game_constants import *
from widget import Root


class GameState:
    def __init__(self, mgr, parent=None):
        # We always need a reference to the manager, so we can switch states
        self.mgr = mgr
        # Upon creation, a state becomes the current state
        # If this behavior is not wanted, overwrite it in the subclass constructor
        self.take_control()
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
        self.parent.reinit()

    def reinit(self):
        """Perform any necessary steps when becoming active again"""
        pass

    def take_control(self):
        """Become the current state"""
        self.mgr.state = self

    def previous_state(self):
        """Return control to the current state's parent state."""
        if self.parent is not None:
            self.quit()
            self.parent.take_control()
        # If we were already at the top of the state stack, just quit
        else:
            self.mgr.terminate()

    def top_state(self):
        """Return control to the top state on the stack"""
        if self.parent is not None:
            self.quit()
            self.parent.take_control()
            self.parent.top_state()