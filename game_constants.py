import os

from pygame.constants import *
import numpy as np

# This prints shit to the screen
from pygame.constants import K_RIGHT, K_DOWN, K_LEFT, K_UP
from pygame.rect import Rect

DEBUG = True

# System Constants
FPS = 60
FRAME_TIME = 1000.0 / FPS

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

MAIN_DIR = os.getcwd()
MAPS_DIR = os.path.join(MAIN_DIR, "maps")
TEMP_MAP_FILE = os.path.join(MAPS_DIR, "__temp.map")
DEFAULT_MAP_FILE = os.path.join(MAPS_DIR, "__default.map")

# I/O
FILE_CHUNK_SIZE = 4096

DEFAULT_PORT = 2233
MAX_PORT = 3000
SOCKET_BUFFER_SIZE = 256

# Some input related constants
MB_LEFT = 1
MB_MIDDLE = 2
MB_RIGHT = 3
MOUSE_BUTTONS = [1,2,3]

# Sokoban Specific Constants

INPUT_KEYS = [K_RIGHT, K_DOWN, K_LEFT, K_UP, K_z]
DIR = {K_RIGHT: (1, 0), K_DOWN: (0, 1), K_LEFT: (-1, 0), K_UP: (0, -1)}
ADJ = [(1, 0), (0, 1), (-1, 0), (0, -1)]

# This is a tradeoff between convenience and wasting the user's memory
# Probably around 100 is a sane value
MAX_DELTAS = 100

PADDING = 10
DISPLAY_WIDTH = 24
DISPLAY_HEIGHT = 16
# "Coordinates" of the center of the screen
DISPLAY_CX = (DISPLAY_WIDTH - 1)//2
DISPLAY_CY = (DISPLAY_HEIGHT - 1)//2

# The size of a spot on the board
MESH = 30

EDITOR_RECT = Rect(PADDING, PADDING, DISPLAY_WIDTH*MESH, DISPLAY_HEIGHT*MESH)

# Colors
DIM_FILTER = (0, 0, 0, 50)

RED = (200, 50, 50)
GREEN = (50, 200, 50)
MAROON = (50, 0, 0)
BLACK = (0, 0, 0)
GREY = (100, 100, 100)
LIGHT_GREY = (200, 200, 200)
LIGHT_BLUE = (100, 160, 255)
WHITE = (255, 255, 255)
BLUE = (50, 50, 200)
PURPLE = (200, 50, 200)
NAVY_BLUE = (40, 40, 80)
GOLD = (200, 200, 0)
LIGHT_BROWN = (240, 200, 120)
HOT_PINK = (255, 0, 200)
NEON_GREEN = (150, 255, 0)
BRIGHT_ORANGE= (255, 150, 0)

OUT_OF_BOUNDS_COLOR = LIGHT_BLUE