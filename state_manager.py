import sys
import tkinter as tk

import pygame

from game_constants import *
from gs.start_menu import GSStartMenu
# Still need to make a game state for the actual game !!!

class StateManager:
    def __init__(self, root):
        self.state = None
        self.pause_timer = 0
        self.root = root

        GSStartMenu(self)

    def update(self):
        self.check_for_quit()
        self.state.handle_input()
        # This should finish executing as quickly as possible, so as to not drop input
        pygame.event.clear()
        # All of the "work" should go in update()
        self.state.update()

    def draw(self):
        self.state.draw()

    def check_for_quit(self):
        """Check the event queue for something trying to quit the program."""
        for event in pygame.event.get(QUIT):
            self.terminate()
        # Escape key just returns up one state
        for event in pygame.event.get(KEYDOWN):
            if event.key == K_ESCAPE:
                self.state.previous_state()
            # If it wasn't the escape key, put that event back in the event queue
            pygame.event.post(event)

    def terminate(self):
        """Safely quit pygame."""
        # This ensures that the quit function of every GameState
        # on the stack is called
        self.state.top_state()
        pygame.quit()
        sys.exit()
