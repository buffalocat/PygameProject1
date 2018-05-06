import pygame
from enum import IntEnum, auto

from pygame.rect import Rect
from game_constants import *

# Rendering Constants
RIDE_CIRCLE_THICKNESS = 2
NONSTICK_OUTLINE_THICKNESS = 2


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

    def __init__(self, state, pos, color=None, layer=None,
                 rideable=False, pushable=False, sticky=False,
                 is_player=False, is_switch=False, is_switchable=False,
                 dynamic=False):
        # If we were passed no map, this isn't a "real" object
        # Any object in the editor is virtual
        self.virtual = state is None

        self.state = state
        self.pos = pos
        # Get layer automatically, unless we're told
        if layer is None:
            self.layer = OBJ_TYPE[self.name()]["layer"]
        else:
            self.layer = Layer(layer)
        self.color = color

        self.rideable = rideable
        self.pushable = pushable
        self.sticky = sticky

        self.is_player = is_player
        self.is_switch = is_switch
        self.is_switchable = is_switchable

        # Dynamic objects are alerted when anything moves
        self.dynamic = dynamic

        # Real objects get groups and IDs
        if not self.virtual:
            self.group = Group(state, {self})
            self.id = GameObj.ID_COUNT
            GameObj.ID_COUNT += 1
            self.real_init()

    def real_init(self):
        pass

    def draw(self, surf, pos):
        x, y = pos
        offset = 0
        if self.pushable and not self.sticky:
            offset = NONSTICK_OUTLINE_THICKNESS
            pygame.draw.rect(surf, LIGHT_GREY, Rect((x, y), (MESH, MESH)))
        pygame.draw.rect(surf, self.color, Rect((x + offset, y + offset), (MESH - 2*offset, MESH - 2*offset)))
        if self.rideable:
            center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
            pygame.draw.circle(surf, BLACK, center,
                               MESH // 4 + RIDE_CIRCLE_THICKNESS//2,
                               RIDE_CIRCLE_THICKNESS)

    def undo_delta(self, delta):
        pass

    def destroy(self):
        pass

    def display_str(self):
        return f"{self} {self.pos}"

    def name(self):
        return self.__class__.__name__

    def __bytes__(self):
        name = self.name()
        attrs = [name.encode(encoding="utf-8")]
        attrs += [bytes(getattr(self, x[0])) for x in OBJ_TYPE[name]["args"]]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)


# This is basically a structure, but we don't treat it that way
# because Groups aren't actually saved to the .map
class Group:
    def __init__(self, state, objs):
        self.state = state
        self.map = state.objmap
        self.checked = True
        self.objs = objs

    def update_delta(self):
        """Find all adjacent groups to merge with"""
        seen = self.find_adjacent_groups()
        if len(seen) > 1:
            self.state.delta.add_group_merge(seen)

    def find_adjacent_groups(self):
        seen = {self}
        to_check = [self]
        while to_check:
            for obj in to_check.pop().objs:
                for dx, dy in ADJ:
                    x, y = obj.pos
                    adj = self.map[(x + dx, y + dy)][Layer.SOLID]
                    if (adj is not None and adj.group not in seen
                            and obj.sticky and adj.sticky and obj.color is adj.color):
                        seen.add(adj.group)
                        to_check.append(adj.group)
        for group in seen:
            group.checked = True
        return seen


class Wall(GameObj):
    def __init__(self, state, pos):
        super().__init__(state, pos, color=BLACK)


class Box(GameObj):
    def __init__(self, state, pos, color, sticky):
        super().__init__(state, pos, color=color,
                         pushable=True,
                         sticky=sticky)


class Car(GameObj):
    def __init__(self, state, pos, color, sticky):
        super().__init__(state, pos, color=color, rideable=True,
                         pushable=True,
                         sticky=sticky)


class Player(GameObj):
    def __init__(self, state, pos):
        super().__init__(state, pos, color=GREY, is_player=True)

    def real_init(self):
        self.riding = None

    def draw(self, surf, pos):
        center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
        pygame.draw.circle(surf, self.color, center, MESH // 4, 0)


class GateBase(GameObj):
    def __init__(self, state, pos, default):
        # Is the Gate up by default
        self.default = default
        if pos == (23, 16):
            self.special = True
        else:
            self.special = False
        super().__init__(state, pos, color=LIGHT_GREY, is_switchable=True, dynamic=True)

    def real_init(self):
        self.map = self.state.objmap
        # Is the Gate up right now
        self.active = False
        # Have we been told to go up
        self.signal = False
        # Is the Gate trying to go up, but is blocked
        self.waiting = False
        self.wall = GateWall(self.state, self.pos)
        self.set_signal(False)

    def set_signal(self, signal):
        self.signal = signal
        self.check_consistency()

    def check_consistency(self):
        # Reverse the signal if the gate should be up by default
        signal = self.signal if not self.default else not self.signal
        # The gate doesn't want to be up; stop waiting
        before = (self.active, self.signal, self.waiting)
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
        if before != (self.active, self.signal, self.waiting):
            self.state.delta.add_dynamic(self, before)

    def undo_delta(self, delta):
        """delta = (bool active, bool signal, bool waiting)"""
        self.active, self.signal, self.waiting = delta
        if self.active:
            self.map[self.pos][Layer.SOLID] = self.wall
        else:
            if self.map[self.pos][Layer.SOLID] is self.wall:
                self.map[self.pos][Layer.SOLID] = None

    def update(self):
        if self.waiting:
            if self.map[self.pos][Layer.SOLID] is None:
                self.check_consistency()

    def destroy(self):
        if self.active:
            self.map[self.pos][Layer.SOLID] = None


# Maybe include something to ensure that GateWalls are ignored during level saving?
class GateWall(GameObj):
    def __init__(self, state, pos):
        super().__init__(state, pos, color=NAVY_BLUE)


class Switch(GameObj):
    def __init__(self, state, pos, persistent):
        self.pressed = False
        self.persistent = persistent
        super().__init__(state, pos, color=LIGHT_BROWN, is_switch=True, dynamic=True)

    def real_init(self):
        # These don't actually HAVE to be gates; any switchable object works
        self.links = []
        self.map = self.state.objmap

    # If opposite, then the gate goes up when the switch is pressed
    def add_link(self, link):
        self.links.append(link)

    def send_signal(self):
        for link in self.links:
            link.set_signal(self, self.pressed)

    def update(self):
        pressed_before = self.pressed
        if not self.pressed and self.map[self.pos][Layer.SOLID] is not None:
            self.pressed = True
            self.send_signal()
        if not self.persistent and self.pressed and self.map[self.pos][Layer.SOLID] is None:
            self.pressed = False
            self.send_signal()
        if self.pressed != pressed_before:
            self.state.delta.add_dynamic(self, pressed_before)

    def undo_delta(self, delta):
        """delta = bool pressed"""
        self.pressed = delta
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
    if name not in DEPENDENT_OBJS:
        OBJ_BY_LAYER[OBJ_TYPE[name]["layer"]].append(name)

OBJ_COLORS = {"Red": RED,
              "Blue": BLUE,
              "Green": GREEN,
              "Purple": PURPLE,
              "Gold": GOLD}