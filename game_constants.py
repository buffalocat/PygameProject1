import os

from pygame.constants import *
import numpy as np

# This prints shit to the screen
DEBUG = True

# System Constants
FPS = 60
FRAME_TIME = 1000.0 / FPS

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

MAIN_DIR = os.getcwd()
MAPS_DIR = os.path.join(MAIN_DIR, "maps")
TEMP_MAP_FILE = os.path.join(MAPS_DIR, "__temp.map")

# I/O
FILE_CHUNK_SIZE = 4096

DEFAULT_PORT = 2233
MAX_PORT = 3000
SOCKET_BUFFER_SIZE = 256

# Some input related constants
MB_LEFT = 1
MB_RIGHT = 3
MOUSE_BUTTONS = [1,3]

KEYS = [K_LEFT, K_RIGHT, K_UP, K_DOWN]

# Sokoban Specific Constants

PADDING = 20
ROOM_WIDTH = 20
ROOM_HEIGHT = 15
# The size of a spot on the board
MESH = 30

# Colors
DIM_FILTER = (0, 0, 0, 50)

RED = (200, 50, 50)
GREEN = (50, 200, 50)
MAROON = (50, 0, 0)
BLACK = (0, 0, 0)
GREY = (100, 100, 100)
WHITE = (255, 255, 255)
BLUE = (50, 50, 200)
PURPLE = (200, 50, 200)
NAVY_BLUE = (40, 40, 80)
GOLD = (200, 200, 0)
LIGHT_BROWN = (240, 200, 120)