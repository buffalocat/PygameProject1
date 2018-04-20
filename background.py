"""A place to experiment with making pretty images"""
import pygame
from pygame.rect import Rect

from game_constants import *

from random import random
from scipy.spatial import Delaunay

class Background:
    def draw(self, surf):
        pass

    def update(self):
        pass


class BGSolid(Background):
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
    def __init__(self, w, h, colors):
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


COLOR_SHIFT = 15
POINT_RAD = 2

class BGColorChangeGrid(Background):
    def __init__(self, h, w, color):
        self.h = h
        self.w = w
        self.mesh = MESH_MIN + (MESH_MAX - MESH_MIN)*random()
        self.wn = int(w//self.mesh + 2)
        self.hn = int(h//self.mesh + 2)
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

    def shift_color(self):
        for c in self.colors.values():
            c.update()

    def draw(self, surf):
        for i in range(self.wn):
            i_fixed = (i + self.xoff) % self.wn
            for j in range(self.hn):
                j_fixed = (j + self.yoff) % self.hn
                pygame.draw.rect(surf, self.colors[(i_fixed, j_fixed)].color(),
                                 Rect(self.x + (i - 1)*self.mesh,
                                      self.y + (j - 1)*self.mesh,
                                      self.mesh + 1, self.mesh + 1), 0)


COLOR_VAR = 20
COLOR_VEL = 10

class SineColor:
    """A class with a color that oscillates in value over time"""
    def __init__(self, color, amp):
        self.rgb = list(color)
        self.randomize(COLOR_VAR)
        self.angle = 2*np.pi*random()
        self.amp = amp*random()
        self.vel = COLOR_VEL*random()/100

    def randomize(self, var):
        for i in range(3):
            self.rgb[i] += var*(2*random() - 1)

    def update(self):
        self.angle = (self.angle + self.vel) % (2*np.pi)

    def color(self):
        return tuple(clamp_rgb(c + self.amp*np.cos(self.angle)) for c in self.rgb)

def clamp_rgb(x):
    if x < 0:
        return 0
    elif x > 255:
        return 255
    return x


CORNERS = np.array([[0, 0], [WINDOW_WIDTH, 0], [0, WINDOW_HEIGHT], [WINDOW_WIDTH, WINDOW_HEIGHT]])


class BGCrystal(Background):
    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        self.color = color
        self.points = np.concatenate((point_cluster(250, (400, 300),500), CORNERS))
        self.tri = Delaunay(self.points).simplices
        self.colors = [SineColor(color, COLOR_SHIFT) for t in self.tri]

    def update(self):
        for c in self.colors:
            c.update()

    def draw(self, surf):
        surf.fill(BLACK)
        for p in self.points:
            pygame.draw.circle(surf, self.color, p, POINT_RAD, 0)
        for i in range(len(self.tri)):
            pygame.draw.polygon(surf, self.colors[i].color(), [self.points[j] for j in self.tri[i]], 0)


def point_cluster(n, center, radius):
     angle_r = np.random.rand(n) * (2 * np.pi)
     radius_r = (np.random.rand(n) ** 0.5) * radius
     points = np.zeros((n, 2))
     points[:] = np.array(center)
     points[:, 0] += np.cos(angle_r) * radius_r
     points[:, 1] += np.sin(angle_r) * radius_r
     return points.astype(int)