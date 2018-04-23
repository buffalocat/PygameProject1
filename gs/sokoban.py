import os
from queue import Queue
from tkinter import filedialog

import pygame
from enum import IntEnum

from pygame.rect import Rect

from background import BGCrystal
from font import FONT_SMALL, FONT_MEDIUM
from game_constants import *
from game_state import GameState
from widget import TextLines

MAIN_DIR = os.getcwd()

PADDING = 20
ROOM_WIDTH = 20
ROOM_HEIGHT = 15
# The size of a spot on the board
MESH = 30
# How thick the board lines are
LINE_WIDTH = 1

DIR = {K_RIGHT: (1, 0), K_DOWN: (0, 1), K_LEFT: (-1, 0), K_UP: (0, -1)}

# Later we'll want a more robust method for storing level data...

class Tile(IntEnum):
    EMPTY = 0
    WALL = 1
    BOX = 2
    PLAYER = 3
    STICKY = 4

ADJ = [(1, 0), (0, 1), (-1, 0), (0, -1)]

VERBOSE = False


class GSSokoban(GameState):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.root.set_bg(BGCrystal(WINDOW_HEIGHT, WINDOW_WIDTH, PURPLE))
        # The background of the room is distinct from that of the window
        self.bg = WHITE
        self.create_mode = Wall
        self.set_sample()
        self.room_load_default()
        self.create_text()

    def draw(self):
        super().draw()
        self.draw_room()
        # Show what item we can create
        self.sample.draw(self.surf, (PADDING, ROOM_HEIGHT*MESH + PADDING * 3 // 2))
        self.text.draw(self.surf, (2 * PADDING + MESH, ROOM_HEIGHT*MESH + PADDING * 3 // 2))

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.type == KEYDOWN:
                if event.key in DIR.keys():
                    if self.try_move(DIR[event.key], self.player):
                        self.room[self.player.pos] = self.player
                    break
                elif event.key in CREATE.keys():
                    self.create_mode = CREATE[event.key]
                    self.set_sample()
                elif event.key == K_s:
                    self.save()
                elif event.key == K_l:
                    self.load()
        for event in pygame.event.get(MOUSEBUTTONDOWN):
            pos = self.grid_pos(*pygame.mouse.get_pos())
            if self.in_bounds(pos):
                if event.button == MB_LEFT:
                    if self.create_mode == Player:
                        self.move_player(pos)
                    elif pos != self.player.pos:
                        self.create(pos)
                elif event.button == MB_RIGHT:
                    if pos != self.player.pos:
                        self.destroy(pos)

    def create(self, pos, type=None):
        if self.room[pos] is not None:
            return False
        if type is None:
            obj = self.create_mode(pos)
        else:
            obj = type(pos)
        self.room[pos] = obj
        if obj.sticky:
            self.update_group(obj)
        if VERBOSE:
            self.print_objs()
        return True

    def destroy(self, pos):
        obj = self.room[pos]
        self.room[pos] = None
        # Reevaluate stickiness relations now that obj is "gone"
        if obj is not None and obj.sticky:
            group = obj.root.group - {obj}
            # Ensure everyone has a clean slate before rebuilding
            for child in group:
                child.root = child
                child.group = frozenset([child])
            for child in group:
                self.update_group(child)

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.w and 0 <= pos[1] < self.h

    def create_wall_border(self):
        for y in [-1, self.h]:
            for x in range(self.w):
                self.room[(x, y)] = Wall((x, y))
        for x in [-1, self.w]:
            for y in range(self.h):
                self.room[(x, y)] = Wall((x, y))

    def set_sample(self):
        # An "object" at a fake position, not recorded on the grid
        self.sample = self.create_mode((-1, -1))

    def try_move(self, dpos, entity):
        # The set of all groups influenced by the motion
        seen = {entity.root}
        to_check = [entity.root]
        can_move = True
        dx, dy = dpos
        while can_move and to_check:
            # Grab the next group to check
            for cur in to_check.pop().group:
                x, y = cur.pos
                # adj is the tile that cur is trying to move into
                adj = self.room[(x+dx, y+dy)]
                if adj is None:
                    continue
                # Tell the adjacent object that something is
                # trying to move into it
                adj.replace_with_none = False
                if adj.root in seen:
                    continue
                elif adj.pushable:
                    seen.add(adj.root)
                    to_check.append(adj.root)
                else:
                    # We're trying to push something we can't push
                    can_move = False
                    break
        if can_move:
            for tile in seen:
                for obj in list(tile.group):
                    x, y = obj.pos
                    if obj.replace_with_none:
                        self.room[obj.pos] = None
                    obj.pos = (x+dx, y+dy)
                    self.room[obj.pos] = obj
                    if obj.sticky:
                        self.update_group(obj)
        # In any case, reset the "replace" flags
        for tile in seen:
            for obj in tile.group:
                obj.replace_with_none = True
        if VERBOSE:
            self.print_objs()
        return can_move

    def update_group(self, obj):
        x, y = obj.pos
        for dx, dy in ADJ:
            adj = self.room[(x+dx, y+dy)]
            if adj is not None and adj.sticky and obj.color == adj.color and obj.root is not adj.root:
                obj.merge_group(adj)

    def create_text(self):
        self.text = TextLines()
        self.text.color = BLACK
        self.text.font = FONT_MEDIUM
        self.text.height = 40
        self.text.add_line("Press S to Save and L to Load")
        self.text.add_line("ZXCV change block type")
        self.text.add_line("Left/Right click to Create/Destroy")

    def room_load_default(self):
        self.w = ROOM_WIDTH
        self.h = ROOM_HEIGHT
        self.room = {(x, y): None for x in range(ROOM_WIDTH) for y in range(ROOM_HEIGHT)}
        self.player = Player((2,2))
        self.room[self.player.pos] = self.player
        self.create_wall_border()

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
        for x in range(self.w):
            for y in range(self.h):
                tile = self.room[(x,y)]
                if tile is not None:
                    tile.draw(self.surf, self.real_pos(x, y))

    def move_player(self, pos):
        if self.player is not None:
            self.room[self.player.pos] = None
        self.player = Player(pos)
        self.room[pos] = self.player

    def save(self):
        filename = filedialog.asksaveasfilename(initialdir=MAIN_DIR, filetypes=["map .map"])
        if filename is None or filename == "":
            return
        if filename[-4:] != ".map":
            filename += ".map"
        try:
            with open(filename, "wb") as file:
                file.write(bytes([self.w, self.h]))
                tile_data = []
                for y in range(self.h):
                    for x in range(self.w):
                        tile = self.room[(x,y)]
                        code = 0 if tile is None else tile.type
                        tile_data.append(code)
                file.write(bytes(tile_data))
        except IOError:
            print("Failed to write to file")

    def load(self):
        filename = filedialog.askopenfilename(initialdir=MAIN_DIR, filetypes=["map .map"])
        if filename is None:
            return
        try:
            with open(filename, "rb") as file:
                room_size = file.read(2)
                self.w = int(room_size[0])
                self.h = int(room_size[1])
                self.room = {(x,y): None for x in range(self.w) for y in range(self.h)}
                self.player = None
                x, y = 0, 0
                tile_data = file.read(self.w * self.h)
                for byte in tile_data:
                    code = int(byte)
                    # We're gonna do this the dumbest way possible, for now
                    if code == Tile.WALL:
                        self.create((x, y), type=Wall)
                    elif code == Tile.BOX:
                        self.create((x, y), type=Box)
                    elif code == Tile.STICKY:
                        self.create((x, y), type=StickyBox)
                    elif code == Tile.PLAYER:
                        self.move_player((x,y))
                    x += 1
                    if x >= self.w:
                        x = 0
                        y += 1
                self.create_wall_border()
        except IOError:
            print("Failed to read file")

    def print_objs(self):
        for x in range(self.w):
            for y in range(self.h):
                o = self.room[(x, y)]
                if o is not None:
                    print(f"{o} with root {o.root}, in {o.group}")
        print("")


class Entity:
    ID_COUNT = 0

    def __init__(self, pos):
        self.pos = pos
        self.pushable = False
        self.color = None
        self.type = None

        self.sticky = False
        self.root = self
        self.group = frozenset([self])

        self.id = Entity.ID_COUNT
        Entity.ID_COUNT += 1

        # Just for keeping track of what happens when moving
        self.replace_with_none = True

    def merge_group(self, obj):
        self.root.group |= obj.root.group
        for child in obj.root.group:
            child.root = self.root
            child.group = None

    def draw(self, surf, pos):
        pygame.draw.rect(surf, self.color, Rect(pos, (MESH, MESH)))

    def __repr__(self):
        return f"{self.id} at {self.pos}"


class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = RED
        self.type = Tile.PLAYER

    def draw(self, surf, pos):
        super().draw(surf, pos)
        center = (pos[0] + MESH//2, pos[1] + MESH//2)
        pygame.draw.circle(surf, BLACK, center, MESH//4, 0)

    def __repr__(self):
        return "Player " + super().__repr__()


class Wall(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.color = BLACK
        self.type = Tile.WALL

    def __repr__(self):
        return "Wall " + super().__repr__()


class Box(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = GREEN
        self.type = Tile.BOX

    def __repr__(self):
        return "Box " + super().__repr__()


class StickyBox(Entity):
    def __init__(self, pos, color=BLUE):
        super().__init__(pos)
        self.pushable = True
        self.grouped = True
        self.color = color
        self.sticky = True
        self.type = Tile.STICKY

    def __repr__(self):
        return "StickyBox " + super().__repr__()


CREATE = {K_z: Wall, K_x: Box, K_c: Player, K_v: StickyBox}