import pygame
from enum import IntEnum, auto

from pygame.rect import Rect
from game_constants import *

# Rendering Constants
RIDE_CIRCLE_THICKNESS = 2
STICKY_OUTLINE_THICKNESS = 5


# A tile can have one of each type of object
# - Solid objects are things like blocks and walls
# - Objects in the Player layer collide with each other
# but not solid things
# - Floor objects are mostly passive and stationary
# and they don't really "get in the way"
# This may not be enough layers

class Layer(IntEnum):
    FLOOR = auto()
    SOLID = auto()
    PLAYER = auto()

    def __bytes__(self):
        return bytes([self])

NUM_LAYERS = 3

class GameObj:
    ID_COUNT = 0

    def __init__(self, pos, layer, color=None,
                 pushable=False,
                 sticky=False,
                 mimic=False,
                 rideable=False):
        self.pos = pos
        # layer can either be an int or a Layer
        self.layer = Layer(layer)
        self.color = color

        self.pushable = pushable
        self.sticky = sticky
        self.mimic = mimic
        self.rideable = rideable

        # These may only be useful for pushable objects
        self.root = self
        self.group = frozenset([self])

        self.id = GameObj.ID_COUNT
        GameObj.ID_COUNT += 1


    def merge_group(self, obj):
        self.root.group |= obj.root.group
        for child in obj.root.group:
            child.root = self.root
            child.group = None

    def draw(self, surf, pos):
        pygame.draw.rect(surf, self.color, Rect(pos, (MESH, MESH)))
        if self.rideable:
            center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
            pygame.draw.circle(surf, BLACK, center,
                               MESH // 4 + RIDE_CIRCLE_THICKNESS//2,
                               RIDE_CIRCLE_THICKNESS)
        """if self.sticky:
            pygame.draw.rect(surf, GREY, Rect(pos, (MESH, MESH)),
                             STICKY_OUTLINE_THICKNESS)"""


class Wall(GameObj):
    def __init__(self, pos):
        super().__init__(pos, Layer.SOLID, BLACK)

    def __bytes__(self):
        attrs = [b"Wall"]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)

class Box(GameObj):
    def __init__(self, pos, color, sticky):
        super().__init__(pos, Layer.SOLID, color,
                         pushable=True,
                         sticky=sticky)

    def __bytes__(self):
        attrs = [b"Box", bytes(self.color), bytes(self.sticky)]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)


class Car(GameObj):
    def __init__(self, pos, color, sticky):
        super().__init__(pos, Layer.SOLID, color=color,
                         pushable=True,
                         sticky=sticky,
                         rideable=True)

    def __bytes__(self):
        attrs = [b"Car", bytes(self.color), bytes(self.sticky)]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)


class Player(GameObj):
    def __init__(self, pos):
        super().__init__(pos, Layer.PLAYER, color=GREY)
        self.riding = None

    def draw(self, surf, pos):
        center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
        pygame.draw.circle(surf, self.color, center, MESH // 4, 0)

    def __bytes__(self):
        attrs = [b"Player"]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)


OBJ_TYPE = {"Wall": Wall,
            "Box": Box,
            "Car": Car,
            "Player": Player}