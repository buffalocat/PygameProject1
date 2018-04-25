from tkinter import filedialog

import pygame
from enum import IntEnum, Enum

from pygame.rect import Rect

from background import BGCrystal
from game_constants import *
from game_state import GameState


PADDING = 20
ROOM_WIDTH = 20
ROOM_HEIGHT = 15
# The size of a spot on the board
MESH = 30
# How thick the board lines are
LINE_WIDTH = 1

DIR = {K_RIGHT: (1, 0), K_DOWN: (0, 1), K_LEFT: (-1, 0), K_UP: (0, -1)}

ADJ = [(1, 0), (0, 1), (-1, 0), (0, -1)]

# We can probably do something very "clever" here to avoid retyping words...

ATTR = ["pushable", "sticky"]

class Attr(Enum):
    solid = b"solid"
    pushable = b"pushable"
    sticky = b"sticky"

class Tile(IntEnum):
    EMPTY = 0
    WALL = 1

class GSSokoban(GameState):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.root.set_bg(BGCrystal(WINDOW_HEIGHT, WINDOW_WIDTH, GOLD))
        # The background of the room is distinct from that of the window
        self.bg = WHITE
        self.load()

    def draw(self):
        super().draw()
        self.draw_room()

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.type == KEYDOWN:
                if event.key in DIR.keys():
                    if self.try_move(DIR[event.key], self.player):
                        break

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.w and 0 <= pos[1] < self.h

    def create_wall_border(self):
        for y in [-1, self.h]:
            for x in range(self.w):
                self.objmap[(x, y)] = [Wall((x, y))]
        for x in [-1, self.w]:
            for y in range(self.h):
                self.objmap[(x, y)] = [Wall((x, y))]

    def get_solid(self, pos):
        """Return the solid object at pos, if it exists"""
        if pos in self.objmap:
            return next((obj for obj in self.objmap[pos] if obj.solid), None)
        return None

    def try_move(self, dpos, obj):
        # The set of all groups influenced by the motion
        seen = {obj.root}
        to_check = [obj.root]
        can_move = True
        dx, dy = dpos
        while can_move and to_check:
            # Grab the next group to check
            for cur in to_check.pop().group:
                x, y = cur.pos
                # adj is the tile that cur is trying to move into
                adj = self.get_solid((x+dx, y+dy))
                # There was no solid object there
                if adj is None:
                    continue
                # There is a solid object, and we're already considering it
                if adj.root in seen:
                    continue
                # It's new, but we can push it
                elif adj.pushable:
                    seen.add(adj.root)
                    to_check.append(adj.root)
                # We're trying to push something we can't push
                else:
                    can_move = False
                    break
        if can_move:
            for tile in seen:
                for obj in list(tile.group):
                    self.objmap[obj.pos].remove(obj)
                    x, y = obj.pos
                    obj.pos = (x+dx, y+dy)
                    self.put_obj(obj, obj.pos)
            for tile in seen:
                for obj in list(tile.group):
                    if obj.sticky:
                        self.update_group(obj)
        return can_move

    def update_group(self, obj):
        x, y = obj.pos
        for dx, dy in ADJ:
            adj = self.get_solid((x+dx, y+dy))
            if adj is not None and adj.sticky and obj.color == adj.color and obj.root is not adj.root:
                obj.merge_group(adj)

    @staticmethod
    def real_pos(x, y):
        return x * MESH + PADDING, y * MESH + PADDING

    @staticmethod
    def grid_pos(x, y):
        return (x - PADDING) // MESH, (y - PADDING) // MESH

    def draw_room(self):
        # This will need to be changed significantly
        # once we have a "camera" object
        pygame.draw.rect(self.surf, WHITE, Rect(PADDING, PADDING, MESH*ROOM_WIDTH, MESH*ROOM_HEIGHT))
        for pos in self.objmap:
            if self.in_bounds(pos):
                x, y = pos
                for obj in self.objmap[(x,y)]:
                    obj.draw(self.surf, self.real_pos(x, y))

    def move_player(self, pos):
        if self.player is None:
            self.player = Player(pos)
        else:
            self.objmap[self.player.pos].remove(self.player)
        self.objmap[pos].append(self.player)

    def save(self):
        filename = filedialog.asksaveasfilename(initialdir=MAPS_DIR, filetypes=["map .map"])
        if filename is None or filename == "":
            return
        if filename[-4:] != ".map":
            filename += ".map"
        try:
            with open(filename, "w+b") as file:
                # IF NOT BIGMAP
                file.write(bytes([self.w, self.h]))
                objdata = {}
                for pos in self.objmap:
                    if not self.in_bounds(pos):
                        continue
                    for obj in self.objmap[pos]:
                        attrs = []
                        if obj.solid:
                            attrs.append(b"solid")
                        if obj.pushable:
                            attrs.append(b"pushable")
                        if obj.sticky:
                            attrs.append(b"sticky")
                        if obj.is_player:
                            attrs.append(b"is_player")
                        color = bytes(obj.color)
                        s = b" ".join(attrs) + b":" + color + b"\n"
                        if s not in objdata:
                            objdata[s] = []
                        objdata[s].append(obj.pos)
                for s in objdata:
                    # We write:
                    # 1) The object type, followed by newline
                    # 2) The number of occurences
                    # 3) The positions
                    file.write(s)
                    # IF NOT BIGMAP
                    file.write(len(objdata[s]).to_bytes(2, byteorder="little"))
                    pos_list = []
                    for pos in objdata[s]:
                        if self.in_bounds(pos):
                            # IF NOT BIGMAP
                            pos_list.extend(pos)
                    file.write(bytes(pos_list))
        except IOError:
            print("Failed to write to file")

    def load(self):
        filename = filedialog.askopenfilename(initialdir=MAPS_DIR, filetypes=["map .map"])
        if filename is None:
            return
        try:
            with open(filename, "r+b") as file:
                # IF NOT BIGMAP
                room_size = file.read(2)
                self.w = int(room_size[0])
                self.h = int(room_size[1])
                self.objmap = {}
                self.player = None
                x, y = 0, 0
                self.create_wall_border()
                for line in file:
                    if len(line) <= 1:
                        break
                    spl = line.rstrip(b"\n").split(b":")
                    # A list of attributes that the object has
                    attr = spl[0].split(b" ")
                    solid = b"solid" in attr
                    pushable = b"pushable" in attr
                    sticky = b"sticky" in attr
                    is_player = b"is_player" in attr
                    # The color of the object in rgb format
                    color = tuple(map(int, spl[1]))
                    # The positions at which this object appears
                    # IF NOT BIGMAP
                    n = int.from_bytes(file.read(2), byteorder="little")
                    pos_str = file.read(2*n)
                    # IF NOT BIGMAP
                    for i in range(n):
                        pos = tuple(map(int, pos_str[2*i:2*i + 2]))
                        obj = Entity(pos)
                        obj.solid = solid
                        obj.pushable = pushable
                        obj.sticky = sticky
                        obj.color = color
                        obj.is_player = is_player
                        self.put_obj(obj, pos)
                for pos in self.objmap:
                    for obj in self.objmap[pos]:
                        if obj.sticky:
                            self.update_group(obj)
        except IOError:
            print("Failed to read file")

    def put_obj(self, obj, pos):
        """Push obj into the objmap at pos"""
        if obj.is_player:
            self.player = obj
        if pos not in self.objmap:
            self.objmap[pos] = []
        self.objmap[pos].append(obj)


class Entity:
    ID_COUNT = 0

    def __init__(self, pos=None):
        self.pos = pos
        self.solid = True
        self.pushable = False
        self.is_player = False
        self.color = None

        self.sticky = False
        self.root = self
        self.group = frozenset([self])

        self.id = Entity.ID_COUNT
        Entity.ID_COUNT += 1


    def merge_group(self, obj):
        self.root.group |= obj.root.group
        for child in obj.root.group:
            child.root = self.root
            child.group = None

    def draw(self, surf, pos):
        pygame.draw.rect(surf, self.color, Rect(pos, (MESH, MESH)))
        if self.is_player:
            center = (pos[0] + MESH // 2, pos[1] + MESH // 2)
            pygame.draw.circle(surf, BLACK, center, MESH // 4, 0)

    def __repr__(self):
        return f"Color {self.color} obj at Pos {self.pos}"


class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = RED
        self.is_player = True


class Wall(Entity):
    def __init__(self, pos=None):
        super().__init__(pos)
        self.color = BLACK


class Box(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = GREEN


class StickyBox(Entity):
    def __init__(self, pos, color=BLUE):
        super().__init__(pos)
        self.pushable = True
        self.grouped = True
        self.color = color
        self.sticky = True


class PurpleBox(StickyBox):
    def __init__(self, pos):
        super().__init__(pos, color=PURPLE)


CREATE = {K_z: Wall, K_x: Box, K_c: Player, K_v: StickyBox, K_b: PurpleBox}