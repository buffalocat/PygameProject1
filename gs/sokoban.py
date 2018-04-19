import pygame
from enum import IntEnum

from pygame.rect import Rect

from game_constants import *
from game_state import GameState

PADDING = 20
ROOM_WIDTH = 24
ROOM_HEIGHT = 18
# The size of a spot on the board
MESH = 30
# How thick the board lines are
LINE_WIDTH = 1

DIR = {K_RIGHT: (1, 0), K_DOWN: (0, 1), K_LEFT: (-1, 0), K_UP: (0, -1)}

class GSSokoban(GameState):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.root.set_color(PURPLE)
        # The background of the room is distinct from that of the window
        self.bg = WHITE
        self.room_load()

    def draw(self):
        super().draw()
        self.draw_room()

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.type == KEYDOWN:
                if event.key in DIR.keys():
                    if self.try_move(DIR[event.key], self.player, None):
                        self.room[self.player.pos] = self.player
                    break


    def try_move(self, dpos, entity, replace):
        print(f"TRYING TO MOVE {entity}")
        if not entity.pushable:
            print("Hit something not pushable")
            return False
        x, y = entity.pos
        dx, dy = dpos
        new_pos = (x+dx, y+dy)
        if self.room[new_pos] is None:
            # If this space is empty, move us and the replacing object
            print("GOT TO AN EMPTY SPACE")
            self.room[new_pos] = entity
            entity.pos = new_pos
            if replace is not None:
                replace.pos = (x,y)
            self.room[(x,y)] = replace
            return True
        if self.try_move(dpos, self.room[new_pos], entity):
            # If the thing that was in the way can move, then the
            # replacement can move too
            print("Recursive pushing!")
            if replace is not None:
                replace.pos = (x,y)
            self.room[(x,y)] = replace
            return True
        return False

    # Later this will take an argument,
    # but for now it's just a "default room"
    def room_load(self):
        self.room = {(x, y): None for x in range(ROOM_WIDTH) for y in range(ROOM_HEIGHT)}
        self.player = Player((4,5))
        self.room[self.player.pos] = self.player
        for pos in [(1,1), (2,2), (2,3), (2, 4), (16,10)]:
            self.room[pos] = Wall(pos)
        for pos in [(7,7), (8,8), (13,10)]:
            self.room[pos] = Box(pos)

    @staticmethod
    def real_pos(x, y):
        return x*MESH + PADDING, y*MESH + PADDING

    def draw_room(self):
        for x in range(ROOM_WIDTH):
            for y in range(ROOM_HEIGHT):
                tile = self.room[(x,y)] # In a more sophisticated version: .color
                color = self.bg if tile is None else tile.color
                pygame.draw.rect(self.surf, color,
                                 Rect(self.real_pos(x, y), (MESH, MESH)))


class Entity:
    def __init__(self, pos):
        self.pos = pos
        self.pushable = False
        self.sticky = False
        self.color = None


class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = BLUE


class Wall(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.color = BLACK


class Box(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.pushable = True
        self.color = GREEN