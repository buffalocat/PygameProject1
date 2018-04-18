import pygame

from font import FONT_SMALL
from game_constants import *
from game_state import GameState
from widget import Panel, TextLines

TOP = 10
LEFT = 10

BLOCK = 64
WIDTH = BLOCK * 6
HEIGHT = 256

DSAT_L = 32
DSAT = 4

class GSColorSelect(GameState):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.root.set_color(WHITE)
        self.color_panel = ColorChooser((WIDTH, HEIGHT), (LEFT, TOP))
        self.root.add(self.color_panel)
        self.preview = Panel((50, 50), (0, WINDOW_HEIGHT - 50))
        self.root.add(self.preview)
        self.sat = 256
        self.x = 0
        self.y = 0
        self.color = 0
        self.text = TextLines()
        self.set_text()
        self.font = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 20)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == MOUSEMOTION:
                x, y = pygame.mouse.get_pos()
                if LEFT <= x < LEFT + WIDTH and TOP <= y < TOP + HEIGHT:
                    self.x = x
                    self.y = y
                    self.get_current_color()
            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    self.sat = min(self.sat + DSAT_L, 256)
                    self.color_panel.draw_once(self.sat)
                    self.get_current_color()
                elif event.key == K_DOWN:
                    self.sat = max(self.sat - DSAT_L, 0)
                    self.color_panel.draw_once(self.sat)
                    self.get_current_color()
                elif event.key == K_RIGHT:
                    self.sat = min(self.sat + DSAT, 256)
                    self.color_panel.draw_once(self.sat)
                    self.get_current_color()
                elif event.key == K_LEFT:
                    self.sat = max(self.sat - DSAT, 0)
                    self.color_panel.draw_once(self.sat)
                    self.get_current_color()
                elif event.key == K_RETURN:
                    self.mgr.previous_state()

    def get_current_color(self):
        pixels = pygame.PixelArray(self.surf)
        self.color = pixels[self.x][self.y]
        del pixels
        self.preview.set_color(self.color_rgb())

    def color_rgb(self):
        r = (self.color >> 16) % 256
        g = (self.color >> 8) % 256
        b = self.color % 256
        return (r,g,b)

    def set_text(self):
        self.text.color = NAVY_BLUE
        self.text.font = FONT_SMALL
        self.text.height = 20
        self.text.add_line("Use the arrow keys to change saturation (This may take a moment)")
        self.text.add_line("")
        self.text.add_line("Press Enter to return to menu")

    def draw(self):
        super().draw()
        self.text.set_line(1, f"Current color is 0x{self.color:x} = {self.color_rgb()}")
        self.text.draw(self.surf, (60, WINDOW_HEIGHT - 65))

class ColorChooser(Panel):
    def __init__(self, dims, pos):
        super().__init__(dims, pos)
        # Do the initial drawing
        self.hue = [get_hue(x, BLOCK) for x in range(WIDTH)]
        self.lum = [(HEIGHT - 1 - y) / HEIGHT for y in range(HEIGHT)]
        self.draw_once(256)

    # This function is called every time the saturation changes.  It's not very efficient!
    def draw_once(self, sat):
        pixels = pygame.PixelArray(self.surf)
        for x in range(WIDTH):
            r, g, b = apply_sat(*self.hue[x], sat)
            for y in range(HEIGHT):
                lum = self.lum[y]
                pixels[x][y] = (r * lum, g * lum, b * lum)
        del pixels

    # Override the superclass method so that we're not repainting the surface black every frame
    def draw(self, surf):
        surf.blit(self.surf, self.pos)


def get_hue(x, size):
    block = x//size
    rem = x % size
    if block == 0:
        r = 256
        g = (rem*256)//size
        b = 0
    elif block == 1:
        r = ((size-rem)*256)//size
        g = 256
        b = 0
    elif block == 2:
        r = 0
        g = 256
        b = (rem * 256) // size
    elif block == 3:
        r = 0
        g = ((size - rem) * 256) // size
        b = 256
    elif block == 4:
        r = (rem * 256) // size
        g = 0
        b = 256
    elif block == 5:
        r = 256
        g = 0
        b = ((size - rem) * 256) // size
    else:
        r, g, b = 0, 0, 0
    return r, g, b

def apply_sat(r, g, b, sat):
    r = r * sat // 256 + (256 - sat)
    g = g * sat // 256 + (256 - sat)
    b = b * sat // 256 + (256 - sat)
    return r, g, b