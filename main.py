import time
import tkinter as tk
import pygame

from game_constants import *
from state_manager import StateManager

# Game Initialization

def main():
    # initialize tk window for embedding pygame
    root = tk.Tk()
    embed = tk.Frame(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    embed.pack(side=tk.LEFT)
    os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
    root.update()
    # initialize pygame
    pygame.init()
    # These are the only events we care about handling
    pygame.event.set_allowed([KEYUP, KEYDOWN, MOUSEBUTTONDOWN, ACTIVEEVENT])
    pygame.mouse.set_visible(True)
    manager = StateManager(root)

    root.protocol("WM_DELETE_WINDOW", manager.set_quit)

    # Main game loop
    # We put root.update() in here so that pygame.display.update()
    # doesn't interrupt tkinter's event handling
    while not manager.quit:
        t = time.clock()
        manager.update()
        manager.draw()
        pygame.display.update()
        root.update()
        dt = 1000*(time.clock() - t)
        REAL_FPS = round(1000.0 / dt)
        root.title(f"FPS: {min(REAL_FPS, FPS)}/{FPS}")

    manager.terminate()

# This line makes it so main() only runs when we run THIS file directly
if __name__ == '__main__':
    main()
