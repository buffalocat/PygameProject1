import pygame
from enum import IntEnum, auto

from pygame.rect import Rect
from game_constants import *

# Rendering Constants
RIDE_CIRCLE_THICKNESS = 2
STICKY_OUTLINE_THICKNESS = 2


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

    def __init__(self, map, pos, color=None, layer=None,
                 rideable=False, pushable=False, sticky=False,
                 is_player=False, is_switch=False, is_switchable=False,
                 dynamic=False):
        #If we were passed no map, this isn't a "real" object
        self.virtual = map is None

        self.map = map
        self.pos = pos
        # Get layer automatically, unless we're told
        if layer is None:
            self.layer = OBJ_TYPE[str(self)]["layer"]
        else:
            self.layer = Layer(layer)
        self.color = color

        self.rideable = rideable
        self.pushable = pushable
        self.sticky = sticky

        self.is_player = is_player
        self.is_switch = is_switch
        self.is_switchable = is_switchable

        # Does this object need to receive signals when anything changes
        # We could demand that virtual objects aren't dynamic,
        # but they never get put on the map so it shiouldn't matter.
        self.dynamic = dynamic

        # Real objects get groups and IDs
        if not self.virtual:
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
        x, y = pos
        offset = 0
        if self.sticky:
            offset = STICKY_OUTLINE_THICKNESS
            pygame.draw.rect(surf, LIGHT_GREY, Rect((x, y), (MESH, MESH)))
        pygame.draw.rect(surf, self.color, Rect((x + offset, y + offset), (MESH - 2*offset, MESH - 2*offset)))
        if self.rideable:
            center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
            pygame.draw.circle(surf, BLACK, center,
                               MESH // 4 + RIDE_CIRCLE_THICKNESS//2,
                               RIDE_CIRCLE_THICKNESS)

    def destroy(self):
        pass

    def check_consistency(self):
        """Make sure the state makes sense after changing properties"""
        pass

    def display_str(self):
        return f"{self} {self.pos}"

    def __str__(self):
        return self.__class__.__name__

    def __bytes__(self):
        name = str(self)
        attrs = [name.encode(encoding="utf-8")]
        attrs += [bytes(getattr(self, x[0])) for x in OBJ_TYPE[name]["args"]]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)


class Wall(GameObj):
    def __init__(self, map, pos):
        super().__init__(map, pos, color=BLACK)


class Box(GameObj):
    def __init__(self, map, pos, color, sticky):
        super().__init__(map, pos, color=color,
                         pushable=True,
                         sticky=sticky)


class Car(GameObj):
    def __init__(self, map, pos, color, sticky):
        super().__init__(map, pos, color=color, rideable=True,
                         pushable=True,
                         sticky=sticky)


class Player(GameObj):
    def __init__(self, map, pos):
        super().__init__(map, pos, color=GREY, is_player=True)
        self.riding = None

    def draw(self, surf, pos):
        center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
        pygame.draw.circle(surf, self.color, center, MESH // 4, 0)


class GateBase(GameObj):
    def __init__(self, map, pos, default):
        super().__init__(map, pos, color=LIGHT_GREY, is_switchable=True, dynamic=True)
        # Is the Gate up right now
        self.active = False
        # Is the Gate up by default
        self.default = default
        # Have we been told to go up
        self.signal = False
        # Is the Gate trying to go up, but is blocked
        self.waiting = False
        self.wall = GateWall(self.map, self.pos)
        if not self.virtual:
            self.set_signal(False)

    def set_signal(self, signal):
        self.signal = signal
        self.check_consistency()

    def check_consistency(self):
        # Reverse the signal if the gate should be up by default
        signal = self.signal if not self.default else not self.signal
        # The gate doesn't want to be up; stop waiting
        if not signal:
            self.waiting = False
            self.active = False
            if self.map[self.pos][Layer.SOLID] is self.wall:
                self.map[self.pos][Layer.SOLID] = None
        # Try to raise the gate
        else:
            if self.map[self.pos][Layer.SOLID] is None:
                self.map[self.pos][Layer.SOLID] = self.wall
                self.active = True
                self.waiting = False
            elif self.map[self.pos][Layer.SOLID] is not self.wall:
                self.active = False
                self.waiting = True

    def update(self):
        if self.waiting:
            if self.map[self.pos][Layer.SOLID] is None:
                self.check_consistency()

    def destroy(self):
        if self.active:
            self.map[self.pos][Layer.SOLID] = None


# Maybe include something to ensure that GateWalls are ignored during level saving?
class GateWall(GameObj):
    def __init__(self, map, pos):
        super().__init__(map, pos, color=NAVY_BLUE)


class Switch(GameObj):
    def __init__(self, map, pos, persistent):
        super().__init__(map, pos, color=LIGHT_BROWN, is_switch=True, dynamic=True)
        self.persistent = persistent
        self.pressed = False
        # These don't actually HAVE to be gates; any switchable object works
        self.gates = []

    # If opposite, then the gate goes up when the switch is pressed
    def add_gate(self, gate):
        self.gates.append(gate)

    def send_signal(self):
        for gate in self.gates:
            gate.set_signal(self.pressed)

    def update(self):
        if not self.pressed and self.map[self.pos][Layer.SOLID] is not None:
            self.pressed = True
            self.send_signal()
        if not self.persistent and self.pressed and self.map[self.pos][Layer.SOLID] is None:
            self.pressed = False
            self.send_signal()

    def draw(self, surf, pos):
        x, y = pos
        super().draw(surf, pos)
        pygame.draw.line(surf, BLACK, (x+MESH//2, y+MESH//8), (x+MESH//2, y+7*MESH//8), 3)
        pygame.draw.line(surf, BLACK, (x+MESH//8, y+MESH//2), (x+7*MESH//8, y+MESH//2), 3)
        if self.pressed:
            pygame.draw.rect(surf, BLACK, Rect(x + MESH // 4, y + MESH // 4, MESH // 2 + 1, MESH // 2 + 1), 0)
        elif self.persistent:
            pygame.draw.rect(surf, BLACK, Rect(x + MESH // 4, y + MESH // 4, MESH // 2 + 1, MESH // 2 + 1), 1)


# keys must exactly match the corresponding class name
# args is a list of (attr, type)s
# attr should exactly match the actual attribute of the class
OBJ_TYPE = {"Wall":
                {"type": Wall,
                 "layer": Layer.SOLID,
                 "args": []},
            "Box":
                {"type": Box,
                 "layer": Layer.SOLID,
                 "args": [("color", "color"), ("sticky", "bool")]},
            "Car":
                {"type": Car,
                 "layer": Layer.SOLID,
                 "args": [("color", "color"), ("sticky", "bool")]},
            "Player":
                {"type": Player,
                 "layer": Layer.PLAYER,
                 "args": []},
            "Switch":
                {"type": Switch,
                 "layer": Layer.FLOOR,
                 "args": [("persistent", "bool")]},
            "GateBase":
                {"type": GateBase,
                 "layer": Layer.FLOOR,
                 "args": [("default", "bool")]},
            "GateWall":
                {"type": GateWall,
                 "layer": Layer.SOLID,
                 "args": []}}

DEPENDENT_OBJS = ["GateWall"]

for x in OBJ_TYPE:
    OBJ_TYPE[x]["save"] = True
for x in DEPENDENT_OBJS:
    OBJ_TYPE[x]["save"] = False

# Produce a list of key strings for each layer
OBJ_BY_LAYER = {}

for layer in Layer:
    OBJ_BY_LAYER[layer] = []
for name in OBJ_TYPE:
    OBJ_BY_LAYER[OBJ_TYPE[name]["layer"]].append(name)

OBJ_COLORS = {"Red": RED,
              "Blue": BLUE,
              "Green": GREEN,
              "Purple": PURPLE,
              "Gold": GOLD}