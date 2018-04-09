"""A collection of classes for building a GUI"""

import pygame
from game_constants import *


class Widget:
    """A very generic GUI element"""
    def __init__(self, pos):
        self.pos = pos

    def handle_input(self):
        pass

    def update(self):
        pass

    def draw(self, surf):
        pass


class Panel(Widget):
    """A rectangular widget which contains relatively placed child widgets"""
    def __init__(self, dims, pos, color=None):
        super().__init__(pos)
        self.color = color
        self.surf = pygame.Surface(dims, flags=SRCALPHA)
        self.children = []  # A list of widgets in this panel
        self.focus = None  # Does one child have the focus?
        self.dim_filter = pygame.Surface(dims, flags=SRCALPHA)
        self.dim_filter.fill(DIM_FILTER)

    def add(self, child):
        """Add a child widget with a relative position"""
        self.children.append(child)

    def remove(self, child):
        try:
            self.children.remove(child)
        except KeyError:
            print("Attempted to remove a nonexistent widget")

    def set_color(self, color):
        self.color = color

    def set_focus(self, child=None):
        if child is not None and child not in self.children:
            self.add(child)
        self.focus = child

    def handle_input(self):
        if self.focus is None:
            for child in self.children:
                child.handle_input()
        else:
            self.focus.handle_input()

    # A panel has no behavior, so it just updates its children
    def update(self):
        for child in self.children:
            child.update()

    def draw(self, surf):
        # First fill the panel's surface with its background color
        if self.color is not None:
            self.surf.fill(self.color)
        # Now draw all of its child objects on top
        if self.focus is None:
            for child in self.children:
                child.draw(self.surf)
        else:
            for child in self.children:
                if child is not self.focus:
                    child.draw(self.surf)
            self.surf.blit(self.dim_filter, (0,0))
            self.focus.draw(self.surf)
        # When we're done, draw this panel onto the surface we were given
        surf.blit(self.surf, self.pos)


class Root(Panel):
    def __init__(self=None):
        super().__init__((WINDOW_WIDTH, WINDOW_HEIGHT), (0, 0))

# Note: we haven't had need for this yet!  And we might not for a while.
class Menu(Widget):
    """A widget which displays a list of menu items"""
    def __init__(self, parent, pos):
        # The parent object is the thing which calls the methods stored in this menu
        # Frequently either the current state or the state manager
        super().__init__(pos)
        self.parent = parent
        self.items = []
        self.index = 0
        # Font things, which must be overwritten by the subclass constructor
        self.height = 0
        self.color_def = None   # Default text color
        self.color_high = None  # Highlighted text color
        self.font = None

    def add_item(self, name, method):
        """Add an item 'name' to the menu,
        which calls self.parent.method() when activated"""
        self.items.append({"name": name, "method": method})

    def handle_input(self):
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
    def draw(self, surf):
        """Draw the menu on a surface at the given (relative) position"""
        x, y = self.pos
        for i in range(len(self.items)):

            if i == self.index:
                surf.blit(self.font.render(self.items[i]["name"], True, self.color_high), (x, y + self.height * i))
            else:
                surf.blit(self.font.render(self.items[i]["name"], True, self.color_def), (x, y + self.height * i))

# Should this class be reconciled with Menu somehow...?
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

    # If you have a line which changes depending on variables, use this to redefine it
    # Could there be a better way?
    # Consider: a line has a list of (object, attribute) pairs, and we call format() using these in draw()
    def set_line(self, index, line):
        if index in range(len(self.lines)):
            self.lines[index] = line

    def draw(self, surf, pos):
        x, y = pos
        for i in range(len(self.lines)):
            surf.blit(self.font.render(self.lines[i], True, self.color), (x, y + self.height * i))

# We'll keep this one really simple at first: the cursor only goes at the end of the current text
# Note to self: Use pygame.key.get_mods() to check for ctrl, so we can enable pasting
class TextInput:
    """A basic text input box"""


class Button:
    """A button widget"""


class Dialog:
    """Emulates a dialog box within the pygame window"""


# Not exactly a priority, but pretty cool!
class ClickableMenu(Panel):
    """A panel which contains a menu, along with invisible buttons on its items"""