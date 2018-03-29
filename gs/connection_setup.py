"""A menu state for setting up a connection with a friend"""
from random import random
from time import sleep

import pygame
import tkinter as tk
import threading
import socket

from font import FONT_MEDIUM
from game_constants import *
from game_state import GameState, Menu


class GSConnectionSetup(GameState):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.bg = RED
        self.menu = ConnectionSetupMenu(self)

    def update(self):
        self.menu.update()
        #debugging threads
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_p:
                    print("lol")
        pygame.event.clear()

    def draw(self, surf):
        self.surf.fill(self.bg)
        self.menu.draw(self.surf, (10, 10))
        super().draw(surf)

    def host(self):
        """Become the host of a room"""

    def change_bg(self):
        thread1 = threading.Thread(target=self.spawn_thread)
        thread1.start()

    def spawn_thread(self):
        sleep(2)
        self.bg = int(random()*(256**3))

"""def test_threads():
    print(f"there are {threading.active_count()} threads alive!")
    n = 1
    # Let's waste some time lol
    for x in range(10 ** 8):
        n += 1
    print(f"n is {n}")"""


class ConnectionSetupMenu(Menu):
    def __init__(self, parent):
        super().__init__(parent)
        self.add_item("Host Session", "host")  # Not implemented
        self.add_item("Change BG (after a delay)", "change_bg")
        self.add_item("Return to Menu", "mgr.previous_state")
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 40
        self.font = FONT_MEDIUM