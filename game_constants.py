import os
from enum import Enum

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
TEMP_MAP_FILE = os.path.join(MAPS_DIR, "__temp.mapx")
DEFAULT_MAP_FILE = os.path.join(MAPS_DIR, "__default.mapx")

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
# At 100, you sometimes run out, so let's be safe
# (I doubt this is is gonna significantly fill up anyone's RAM)
MAX_DELTAS = 1000

# The size of a spot on the board
MESH = 30

DISPLAY_WIDTH = 23
DISPLAY_HEIGHT = 15
CENTER_PADDINGX = (WINDOW_WIDTH - DISPLAY_WIDTH*MESH)//2
CENTER_PADDINGY = (WINDOW_HEIGHT - DISPLAY_HEIGHT*MESH)//2
EDIT_PADDING = 10

# "Coordinates" of the center of the screen
DISPLAY_CX = (DISPLAY_WIDTH - 1)//2
DISPLAY_CY = (DISPLAY_HEIGHT - 1)//2

EDITOR_RECT = Rect(EDIT_PADDING, EDIT_PADDING, DISPLAY_WIDTH*MESH, DISPLAY_HEIGHT*MESH)

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
LAVENDER = (130, 100, 150)

# Switch Colors
SW_RED1 = (250, 180, 180)
SW_BLUE1 = (180, 220, 250)
SW_GREEN1 = (200, 240, 180)
SW_PURPLE1 = (220, 180, 250)

OUT_OF_BOUNDS_COLOR = LIGHT_BLUE

class ColorEnum(Enum):
    Black = BLACK
    Red = RED
    Blue = BLUE
    Green = GREEN
    Purple = PURPLE
    Gold =  GOLD
    Grey = GREY
    LightGrey = LIGHT_GREY
    NavyBlue = NAVY_BLUE

    SwRed = SW_RED1
    SwBlue = SW_BLUE1
    SwGreen = SW_GREEN1
    SwPurple = SW_PURPLE1