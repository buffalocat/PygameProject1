import os
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

class Tile(IntEnum):
    EMPTY = 0
    WALL = 1
    BOX = 2
    PLAYER = 3


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
                    if self.try_move(DIR[event.key], self.player, None):
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
                        self.room[pos] = self.create_mode(pos)
                elif event.button == MB_RIGHT:
                    if pos != self.player.pos:
                        self.room[pos] = None

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.w and 0 <= pos[1] < self.h

    def create_wall_border(self):
        for y in [-1, self.h]:
            for x in range(self.w):
                self.room[(x,y)] = Wall((x,y))
        for x in [-1, self.w]:
            for y in range(self.h):
                self.room[(x,y)] = Wall((x,y))

    def set_sample(self):
        # An "object" at a fake position, not recorded on the grid
        self.sample = self.create_mode((-1, -1))

    def try_move(self, dpos, entity, replace):
        if VERBOSE: print(f"TRYING TO MOVE {entity}")
        if not entity.pushable:
            if VERBOSE: print("Hit something not pushable")
            return False
        x, y = entity.pos
        dx, dy = dpos
        new_pos = (x+dx, y+dy)
        if self.room[new_pos] is None:
            # If this space is empty, move us and the replacing object
            if VERBOSE: print("GOT TO AN EMPTY SPACE")
            self.room[new_pos] = entity
            entity.pos = new_pos
            if replace is not None:
                replace.pos = (x,y)
            self.room[(x,y)] = replace
            return True
        if self.try_move(dpos, self.room[new_pos], entity):
            # If the thing that was in the way can move, then the
            # replacement can move too
            if VERBOSE: print("Recursive pushing!")
            if replace is not None:
                replace.pos = (x,y)
            self.room[(x,y)] = replace
            return True
        return False

    def create_text(self):
        self.text = TextLines()
        self.text.color = BLACK
        self.text.font = FONT_MEDIUM
        self.text.height = 40
        self.text.add_line("Press S to Save and L to Load")
        self.text.add_line("Use Z, X, C to change block")
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
                        code = 0 if tile is None else tile.id
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
                self.room = {}
                x, y = 0, 0
                tile_data = file.read(self.w * self.h)
                for byte in tile_data:
                    code = int(byte)
                    # We're gonna do this the dumbest way possible, for now
                    if code == Tile.EMPTY:
                        self.room[(x,y)] = None
                    elif code == Tile.WALL:
                        self.room[(x,y)] = Wall((x,y))
                    elif code == Tile.BOX:
                        self.room[(x,y)] = Box((x,y))
                    elif code == Tile.PLAYER:
                        self.move_player((x,y))
                    x += 1
                    if x >= self.w:
                        x = 0
                        y += 1
                self.create_wall_border()
        except IOError:
            print("Failed to read file")


class Entity:
    def __init__(self, pos):
        self.pos = pos
        self.pushable = False
        self.sticky = False
        self.color = None

    def draw(self, surf, pos):
        pygame.draw.rect(surf, self.color, Rect(pos, (MESH, MESH)))


class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = RED
        self.id = Tile.PLAYER

    def draw(self, surf, pos):
        super().draw(surf, pos)
        center = (pos[0] + MESH//2, pos[1] + MESH//2)
        pygame.draw.circle(surf, BLACK, center, MESH//4, 0)


class Wall(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.color = BLACK
        self.id = Tile.WALL


class Box(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = GREEN
        self.id = Tile.BOX


CREATE = {K_z: Wall, K_x: Box, K_c: Player}