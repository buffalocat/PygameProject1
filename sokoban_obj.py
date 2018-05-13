import pygame
from enum import IntEnum, auto, Enum

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

        try:
            self.color = ColorEnum(color).value
        except:
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
        pygame.draw.rect(surf, self.color, Rect((x + offset, y + offset), (MESH - 2 * offset, MESH - 2 * offset)))
        if self.rideable:
            center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
            pygame.draw.circle(surf, BLACK, center,
                               MESH // 4 + RIDE_CIRCLE_THICKNESS//2,
                               RIDE_CIRCLE_THICKNESS)

    def push_delta(self, delta):
        self.state.delta.add_dynamic(self, delta)

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
    def __init__(self, state, pos, color=ColorEnum.Black):
        super().__init__(state, pos, color)


class Box(GameObj):
    def __init__(self, state, pos, color, sticky, rideable):
        super().__init__(state, pos, color=color, rideable=rideable,
                         pushable=True,
                         sticky=sticky)


class Player(GameObj):
    def __init__(self, state, pos, color=ColorEnum.Grey):
        super().__init__(state, pos, color=color, is_player=True)

    def real_init(self):
        self.riding = None

    def draw(self, surf, pos):
        center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
        pygame.draw.circle(surf, self.color, center, MESH // 4, 0)


class GateBase(GameObj):
    def __init__(self, state, pos, color, wall_color, default):
        # Is the Gate up by default
        self.default = default
        self.wall_color = ColorEnum(wall_color).value
        super().__init__(state, pos, color=color, is_switchable=True, dynamic=True)

    def real_init(self):
        self.map = self.state.objmap
        # Is the Gate up right now
        self.up = False
        # Have we been told to go up
        self.active = False
        # Is the Gate trying to go up, but is blocked
        self.waiting = False
        self.wall = GateWall(self.state, self.pos, self.wall_color)
        self.set_signal(False)

    def set_signal(self, signal):
        self.active = signal
        self.check_consistency()

    def check_consistency(self):
        # Reverse the signal if the gate should be up by default
        signal = self.active if not self.default else not self.active
        # The gate doesn't want to be up; stop waiting
        before = (self.up, self.active, self.waiting)
        if not signal:
            self.waiting = False
            self.up = False
            if self.map[self.pos][Layer.SOLID] is self.wall:
                self.map[self.pos][Layer.SOLID] = None
        # Try to raise the gate
        else:
            if self.map[self.pos][Layer.SOLID] is None:
                self.map[self.pos][Layer.SOLID] = self.wall
                self.up = True
                self.waiting = False
            elif self.map[self.pos][Layer.SOLID] is not self.wall:
                self.up = False
                self.waiting = True
        if before != (self.up, self.active, self.waiting):
            self.push_delta(before)

    def undo_delta(self, delta):
        """delta = (bool active, bool signal, bool waiting)"""
        self.up, self.active, self.waiting = delta
        if self.up:
            self.map[self.pos][Layer.SOLID] = self.wall
        else:
            if self.map[self.pos][Layer.SOLID] is self.wall:
                self.map[self.pos][Layer.SOLID] = None

    def update(self):
        if self.waiting:
            if self.map[self.pos][Layer.SOLID] is None:
                self.check_consistency()

    def destroy(self):
        if self.up:
            self.map[self.pos][Layer.SOLID] = None

    def draw(self, surf, pos):
        x, y = pos
        if self.virtual and self.default:
            pygame.draw.rect(surf, self.wall_color, Rect(x, y, MESH, MESH))
        else:
            pygame.draw.rect(surf, self.color, Rect(x, y, MESH, MESH))


# Maybe include something to ensure that GateWalls are ignored during level saving?
class GateWall(GameObj):
    def __init__(self, state, pos, color):
        super().__init__(state, pos, color=color)


class Switch(GameObj):
    def __init__(self, state, pos, color):
        self.semi = False
        self.active = False
        self.persistent = False
        super().__init__(state, pos, color=color, is_switch=True, dynamic=True)
        self.init_colors()

    def init_colors(self):
        r, g, b = self.color
        self.semi_color = (r-50, g-50, b-50)
        self.active_color = (r-120, g-120, b-120)

    def real_init(self):
        self.links = []
        self.semi_links = []
        self.map = self.state.objmap

    def add_link(self, link):
        self.links.append(link)
        self.semi_links.append(all(link.active))

    def send_signal(self):
        for link in self.links:
            link.set_signal(self, self.active)

    def set_persistent(self, signal):
        before = (self.semi, self.active, self.persistent)
        self.persistent = signal
        if (self.semi, self.active, self.persistent) != before:
            self.push_delta(before)

    def set_semi_signal(self, link, signal):
        before = (self.semi, self.active, self.persistent)
        i = self.links.index(link)
        self.semi_links[i] = signal
        self.semi = any(self.semi_links)
        if (self.semi, self.active, self.persistent) != before:
            self.push_delta(before)

    def update(self):
        before = (self.semi, self.active, self.persistent)
        if not self.active and self.map[self.pos][Layer.SOLID] is not None:
            self.active = True
            self.send_signal()
        if not self.persistent and self.active and self.map[self.pos][Layer.SOLID] is None:
            self.active = False
            self.send_signal()
        if (self.semi, self.active, self.persistent) != before:
            self.push_delta(before)

    def undo_delta(self, delta):
        """delta = (bool semi, bool active, bool persistent)"""
        self.semi, self.active, self.persistent = delta
        self.send_signal()

    def draw(self, surf, pos):
        x, y = pos
        super().draw(surf, pos)
        if self.active:
            color = self.active_color
        elif self.semi:
            color = self.semi_color
        else:
            color = self.color
        pygame.draw.rect(surf, color, Rect((x+MESH//4, y+MESH//4), (MESH//2, MESH//2)))
        pygame.draw.rect(surf, BLACK, Rect((x+MESH//4, y+MESH//4), (MESH//2+1, MESH//2+1)), 1)
        pygame.draw.line(surf, BLACK, (x+MESH//2-1, y+MESH//4), (x+MESH//2-1, y+3*MESH//4), 2)
        pygame.draw.line(surf, BLACK, (x+MESH//4, y+MESH//2-1), (x+3*MESH//4, y+MESH//2-1), 2)

STANDARD_COLORS = ["Red", "Blue", "Green", "Purple", "Gold"]
SWITCH_COLORS = ["SwRed", "SwBlue", "SwGreen", "SwPurple"]
GATE_COLORS = ["LightGrey", "NavyBlue"]

# keys must exactly match the corresponding class name
# args is a list of (attr, type)s
# attr should exactly match the actual attribute of the class
OBJ_TYPE = {"Wall":
                {"type": Wall,
                 "layer": Layer.SOLID,
                 "args": [("color", "color")],
                 "color": ["Black"]},
            "Box":
                {"type": Box,
                 "layer": Layer.SOLID,
                 "args": [("color", "color"), ("sticky", "bool"), ("rideable", "bool")],
                 "color": STANDARD_COLORS},
            "Player":
                {"type": Player,
                 "layer": Layer.PLAYER,
                 "args": [("color", "color")],
                 "color": ["Grey"]},
            "Switch":
                {"type": Switch,
                 "layer": Layer.FLOOR,
                 "args": [("color", "color")],
                 "color": SWITCH_COLORS},
            "GateBase":
                {"type": GateBase,
                 "layer": Layer.FLOOR,
                 "args": [("color", "color"), ("wall_color", "color"), ("default", "bool")],
                 "color": GATE_COLORS},
            "GateWall":
                {"type": GateWall,
                 "layer": Layer.SOLID,
                 "args": [("color", "color")],
                 "color": GATE_COLORS}}

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
