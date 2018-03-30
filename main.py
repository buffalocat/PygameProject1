import pygame
import tkinter as tk

from game_constants import *

# Main Game Loop

def main():
    # Get things started
    pygame.init()
    pygame.font.init()
    # These are the only events we care about handling
    pygame.event.set_allowed([KEYUP, KEYDOWN, MOUSEBUTTONDOWN, ACTIVEEVENT])
    # This makes sure we run at a consistent FPS
    FPSCLOCK = pygame.time.Clock()
    # Some cosmetic settings
    pygame.display.set_caption('Game')
    pygame.mouse.set_visible(True)

    # We need tkinter for making certain GUI things easy, later
    root = tk.Tk()
    root.withdraw()

    # Everything interesting is controlled by the game state manager
    # We delay the import so that we can initialize pygame.font
    from state_manager import StateManager
    manager = StateManager()

    # update() handles events since the previous frame and makes necessary changes
    # draw() puts everything on the drawing surface
    # Finally we have to actually update the display on the screen
    # tick(FPS) makes sure the right amount of time has passed
    while True:
        manager.update()
        manager.draw()
        pygame.display.update()

        FPSCLOCK.tick(FPS)


# This line makes it so main() only runs when we run THIS file directly
if __name__ == '__main__':
    main()
