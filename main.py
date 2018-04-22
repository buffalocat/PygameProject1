import os
import time
import tkinter as tk
import pygame

from game_constants import *

# Game Initialization

def main():
    # initialize tk window for embedding pygame
    root = tk.Tk()
    embed = tk.Frame(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    embed.pack()

    os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
    # Is this necessary?
    #os.environ['SDL_VIDEODRIVER'] = 'windib'

    root.update()

    # initialize pygame
    pygame.init()

    # These are the only events we care about handling
    pygame.event.set_allowed([KEYUP, KEYDOWN, MOUSEBUTTONDOWN, ACTIVEEVENT])
    # This makes sure we run at a consistent FPS
    FPSCLOCK = pygame.time.Clock()
    # Some cosmetic settings
    pygame.display.set_caption('Game')
    pygame.mouse.set_visible(True)

    # Everything interesting is controlled by the game state manager
    # We delay the import so that we can initialize pygame.font
    from state_manager import StateManager
    manager = StateManager(root)

    FRAME_TIME = 1000.0/FPS

    def pygame_update():
        t = time.clock()
        manager.update()
        manager.draw()
        pygame.display.update()
        dt = 1000*(time.clock() - t)
        REAL_FPS = round(1000.0 / dt) if dt > FRAME_TIME else FPS
        root.title(f"FPS: {REAL_FPS}/{FPS}")
        root.update()
        embed.after(round(max(FRAME_TIME - dt, 1)), pygame_update)

    pygame_update()

    root.mainloop()



# This line makes it so main() only runs when we run THIS file directly
if __name__ == '__main__':
    main()
