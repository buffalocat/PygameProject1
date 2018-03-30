"""Abstract classes for building a GUI"""

import pygame

from game_constants import *


class GameState:
    def __init__(self, mgr, parent=None):
        # We always need a reference to the manager, so we can switch states
        self.mgr = mgr
        # Parent is the state that we came from
        self.parent = parent
        # Each gamestate print
        self.surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pass

    def update(self):
        pass

    def draw(self, surf):
        surf.blit(self.surf, (0,0))

    def quit(self):
        """Perform any necessary clean-up before leaving a state for good"""
        pass


class Menu:
    """A widget which displays a list of menu items"""
    def __init__(self, parent):
        # The parent object is the thing which calls the methods stored in this menu
        # Frequently either the current state or the state manager
        self.parent = parent
        self.items = []
        self.index = 0
        # Font things, which must be overwritten by the subclass constructor
        self.height = 0
        self.color_def = None   # Default text color
        self.color_high = None  # Highlighted text color
        self.font = None

    def add_item(self, name, method):
        """Add an item 'name' to the menu, which calls self.parent.method() when activated"""
        self.items.append({"name": name, "method": method})

    def update(self):
        """Check for menu movement or activation"""
        for event in pygame.event.get(KEYDOWN):
            if event.key == K_UP:
                self.prev()
            if event.key == K_DOWN:
                self.next()
            # This is slightly magic
            if event.key == K_RETURN:
                # By default, we're calling a method of self.parent
                caller = self.parent
                # But we might have to go through some attributes first, separated by periods
                for attr in self.items[self.index]["method"].split("."):
                    caller = getattr(caller, attr)
                caller()

            pygame.event.post(event)

    def next(self):
        """Move the menu cursor forward"""
        self.index = (self.index + 1) % len(self.items)

    def prev(self):
        """Move the menu cursor backward"""
        self.index = (self.index + len(self.items) - 1) % len(self.items)

    # As it is, menu text is always left aligned and fixed size/spacing
    def draw(self, surf, pos):
        """Draw the menu on a surface at the given (relative) position"""
        x, y = pos
        for i in range(len(self.items)):
            if i == self.index:
                surf.blit(self.font.render(self.items[i]["name"], True, self.color_high), (x, y + self.height * i))
            else:
                surf.blit(self.font.render(self.items[i]["name"], True, self.color_def), (x, y + self.height * i))


class TextLines:
    """A very simple class for displaying lines of text"""
    # Basically a nonfunctional menu
    def __init__(self):
        self.lines = []
        # Font things, which must be overwritten by the subclass constructor
        self.height = 0
        self.color = None
        self.font = None

    def add_line(self, line):
        self.lines.append(line)

    def set_line(self, index, line):
        if index in range(len(self.lines)):
            self.lines[index] = line

    def draw(self, surf, pos):
        x, y = pos
        for i in range(len(self.lines)):
            surf.blit(self.font.render(self.lines[i], True, self.color), (x, y + self.height * i))

# Note: we haven't had need for this yet!  And we might not for a while.
class Panel:
    """A rectangular widget which contains relatively placed child widgets"""
    def __init__(self, width, height, color=(0,0,0)):
        self.color = color
        self.surf = pygame.Surface((width, height))
        self.children = [] # A list of widgets in this panel

    def add(self, widget, pos):
        """Add a child widget with a relative position"""
        self.children.append((widget, pos))

    def set_color(self, color):
        self.color = color

    # A panel has no behavior, so it just updates its children
    def update(self):
        for child in self.children:
            child[0].update()

    def draw(self, surf, pos):
        # First fill the panel's surface with its background color
        self.surf.fill(self.color)
        # Now draw all of its child objects on top
        for child in self.children:
            child[0].draw(self.surf, child[1])
        # When we're done, draw this panel onto the surface we were given, at the appropriate relative position
        surf.blit(self.surf, pos)
