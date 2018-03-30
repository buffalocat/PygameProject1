import sys

import pygame

from game_constants import *
from gs.color_select import GSColorSelect
from gs.connection_setup import GSConnectionSetup
from gs.pause import GSPause
from gs.start_menu import GSStartMenu
# Still need to make a game state for the actual game !!!

class StateManager:
    def __init__(self):
        self.state = None
        self.surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.pause_timer = 0
        self.start_menu()

    def update(self):
        self.check_for_quit()
        self.state.update()

    def draw(self):
        self.state.draw(self.surf)

    # Note: state change methods COULD be unified, but we'll keep them separate
    # You never know what information you might need to pass to a new state

    def start_menu(self):
        self.state = GSStartMenu(self)

    def connection_setup(self):
        self.state = GSConnectionSetup(self, self.state)

    def color_select(self):
        self.state = GSColorSelect(self, self.state)

    # Pausing may be completely meaningless in your game
    def pause(self):
        self.state = GSPause(self, self.state)

    def previous_state(self):
        """Return control to the current state's parent state."""
        if self.state.parent is not None:
            self.state.quit()
            self.state = self.state.parent
        # If we were already at the top of the state stack, just quit
        else:
            self.terminate()

    def top_state(self):
        """Return control to the top state on the stack"""
        while self.state.parent is not None:
            self.state = self.state.parent

    def check_for_quit(self):
        """Check the event queue for something trying to quit the program."""
        for event in pygame.event.get(QUIT):
            self.terminate()
        # There are two valid ways to terminate
        for event in pygame.event.get(KEYUP):
            if event.key == K_ESCAPE:
                self.terminate()
            # If it wasn't the escape key, put that event back in the event queue
            pygame.event.post(event)

    def terminate(self):
        """Safely quit pygame."""
        self.state.quit()
        pygame.quit()
        sys.exit()
