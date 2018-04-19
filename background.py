"""A place to experiment with making pretty images"""
import math

import pygame
from pygame.rect import Rect

from game_constants import *
from random import random

class Background:
    def draw(self, surf):
        pass

    def update(self):
        pass


class BGSolid:
    def __init__(self, color):
        self.color = color

    def draw(self, surf):
        surf.fill(self.color)


MESH_MIN = 20
MESH_MAX = 50
VX_MAX = 1
VY_MAX = 1
THICKNESS = 3

# len(colors) >= 2
class BGGrid(Background):
    def __init__(self, h, w, colors):
        self.h = h
        self.w = w
        self.colors = colors
        self.mesh = MESH_MIN + (MESH_MAX - MESH_MIN)*random()
        self.x = 0
        self.y = 0
        self.vx = VX_MAX*(2*random() - 1)
        self.vy = VY_MAX*(2*random() - 1)
        self.thickness = THICKNESS

    def update(self):
        """Make sure the base coordinates are just outside the top left"""
        self.x += self.vx
        self.x %= self.mesh
        self.y += self.vy
        self.y %= self.mesh

    def draw(self, surf):
        bgcolor, linecolor = self.colors[0:2]
        surf.fill(bgcolor)
        x, y = self.x - self.mesh, self.y - self.mesh
        while x <= self.w + self.mesh:
            pygame.draw.line(surf, linecolor, (x, 0), (x, self.h), self.thickness)
            x += self.mesh
        while y <= self.h + self.mesh:
            pygame.draw.line(surf, linecolor, (0, y), (self.w, y), self.thickness)
            y += self.mesh


COLOR_SHIFT = 10

class BGColorChangeGrid(Background):
    def __init__(self, h, w, color):
        self.h = h
        self.w = w
        self.mesh = MESH_MIN + (MESH_MAX - MESH_MIN)*random()
        self.wn = int(w//self.mesh + 2)
        self.hn = int(h//self.mesh + 2)
        print(self.hn)
        self.xoff = 0
        self.yoff = 0
        self.colors = {(x,y): SineColor(color, COLOR_SHIFT)
                       for x in range(self.wn) for y in range(self.hn)}
        self.x = 0
        self.y = 0
        self.vx = VX_MAX*(2*random() - 1)
        self.vy = VY_MAX*(2*random() - 1)

    def update(self):
        """Make sure the base coordinates are just outside the top left"""
        self.shift_color()
        self.x += self.vx
        if self.x >= self.mesh:
            self.x -= self.mesh
            self.xoff -= 1
            if self.xoff < 0:
                self.xoff += self.wn
        elif self.x < 0:
            self.x += self.mesh
            self.xoff += 1
            if self.xoff >= self.wn:
                self.xoff -= self.wn
        self.y += self.vy
        if self.y >= self.mesh:
            self.y -= self.mesh
            self.yoff -= 1
            if self.yoff < 0:
                self.yoff += self.hn
        elif self.y < 0:
            self.y += self.mesh
            self.yoff += 1
            if self.yoff >= self.hn:
                self.yoff -= self.hn
        print(f"xoff: {self.xoff}, yoff: {self.yoff}")

    def shift_color(self):
        for c in self.colors.values():
            c.shift()

    def draw(self, surf):
        for i in range(self.wn):
            i_fixed = (i + self.xoff) % self.wn
            for j in range(self.hn):
                j_fixed = (j + self.yoff) % self.hn
                pygame.draw.rect(surf, self.colors[(i_fixed, j_fixed)].color(),
                                 Rect(self.x + (i - 1)*self.mesh,
                                      self.y + (j - 1)*self.mesh,
                                      self.mesh, self.mesh), 0)


COLOR_VAR = 30
COLOR_VEL = 20

class SineColor:
    def __init__(self, color, amp):
        self.rgb = list(color)
        self.randomize(COLOR_VAR)
        self.angle = 2*math.pi*random()
        self.amp = amp*random()
        self.vel = COLOR_VEL*random()/100

    def randomize(self, var):
        for i in range(3):
            self.rgb[i] += var*(2*random() - 1)
            if self.rgb[i] < 0:
                self.rgb[i] = 0
            elif self.rgb[i] > 255:
                self.rgb[i] = 255

    def shift(self):
        self.angle = (self.angle + self.vel) % (2*math.pi)

    def color(self):
        return tuple(c + self.amp*math.cos(self.angle) for c in self.rgb)