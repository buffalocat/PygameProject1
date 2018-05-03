from tkinter import filedialog, messagebox

import pygame
from enum import IntEnum, Enum

from pygame.rect import Rect

from background import BGCrystal
from game_constants import *
from game_state import GameState
from sokoban_obj import *
from sokoban_str import *

DIR = {K_RIGHT: (1, 0), K_DOWN: (0, 1), K_LEFT: (-1, 0), K_UP: (0, -1)}

ADJ = [(1, 0), (0, 1), (-1, 0), (0, -1)]

class Camera(IntEnum):
    EDITOR = auto()
    FOLLOW_PLAYER = auto()

# Tentative structure of GSSokoban.objmap:
# A 2d array (list of lists) indexed by positions in the room
# Each element of which is a list with an element for each Layer
# The value is the object at that position on that layer, or None

class GSSokoban(GameState):
    def __init__(self, mgr, parent, pick_level=False, testing=False, editing=False):
        super().__init__(mgr, parent)
        self.root.set_bg(BGCrystal(WINDOW_HEIGHT, WINDOW_WIDTH, GOLD))
        self.cam_mode = Camera.FOLLOW_PLAYER
        self.bg = WHITE
        if pick_level:
            filename = None
        else:
            filename = TEMP_MAP_FILE if testing else DEFAULT_MAP_FILE
        if not self.load(filename=filename, editing=editing):
            self.previous_state()

    def update_dynamic(self):
        for obj in self.dynamic:
            obj.update()

    def update_camera(self):
        if self.cam_mode == Camera.FOLLOW_PLAYER:
            px, py = self.player.pos
            if self.w < DISPLAY_WIDTH:
                self.camx = (self.w - DISPLAY_WIDTH) // 2
            else:
                self.camx = min(max(0, px - DISPLAY_CX), self.w - DISPLAY_WIDTH)
            if self.h < DISPLAY_HEIGHT:
                self.camy = (self.h - DISPLAY_HEIGHT) // 2
            else:
                self.camy = min(max(0, py - DISPLAY_CY), self.h - DISPLAY_HEIGHT)

    def draw(self):
        super().draw()
        self.draw_room()

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.type == KEYDOWN:
                if event.key in DIR.keys():
                    self.try_move_player(DIR[event.key])
                    break

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.w and 0 <= pos[1] < self.h

    def create_wall_border(self):
        for y in [-1, self.h]:
            for x in range(self.w):
                self.objmap[(x, y)][Layer.SOLID] = Wall(self.objmap, (x,y))
        for x in [-1, self.w]:
            for y in range(self.h):
                self.objmap[(x, y)][Layer.SOLID] = Wall(self.objmap, (x,y))

    def get_solid(self, pos):
        """Return the solid object at pos, if it exists"""
        if pos in self.objmap:
            return next((obj for obj in self.objmap[pos] if obj.solid), None)
        return None

    # This method shouldn't be necessary if we keep track of the player
    # in a more sophisticated way.  However, as long as there is only
    # one player on the map at a time, this is fine.
    def search_for_player(self):
        """Find the player"""
        for x in range(self.w):
            for y in range(self.h):
                if self.objmap[(x,y)][Layer.PLAYER] is not None:
                    if self.objmap[(x,y)][Layer.PLAYER].is_player:
                        self.player = self.objmap[(x,y)][Layer.PLAYER]
                        return True
        return False

    def try_move_player(self, dpos):
        if self.player is None:
            return False
        x, y = self.player.pos
        dx, dy = dpos
        new_pos = (x+dx, y+dy)
        if self.objmap[new_pos][Layer.PLAYER] is not None:
            return False
        car = self.player.riding
        can_move = True
        if car is not None:
            can_move = self.try_move(dpos, car)
        if can_move:
            self.objmap[self.player.pos][Layer.PLAYER] = None
            self.objmap[new_pos][Layer.PLAYER] = self.player
            self.player.pos = new_pos
        self.update_camera()
        return True

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
                adj = self.objmap[(x+dx, y+dy)][Layer.SOLID]
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
            # Four steps:
            # 1: Remove objects from their old map positions
            # 2: Put them in current positions, update pos
            # 3: Update other data (like groups)
            # 4: Alert all dynamic objects
            for tile in seen:
                for obj in list(tile.group):
                    self.objmap[obj.pos][Layer.SOLID] = None
                    x, y = obj.pos
                    obj.pos = (x+dx, y+dy)
            for tile in seen:
                for obj in list(tile.group):
                    self.objmap[obj.pos][Layer.SOLID] = obj
            for tile in seen:
                for obj in list(tile.group):
                    if obj.sticky:
                        self.update_group(obj)
            self.update_dynamic()
        return can_move

    def update_group(self, obj):
        """Connect to nearby sticky objects"""
        x, y = obj.pos
        for dx, dy in ADJ:
            adj = self.objmap[(x+dx, y+dy)][Layer.SOLID]
            if adj is not None and adj.sticky and obj.color == adj.color and obj.root is not adj.root:
                obj.merge_group(adj)

    @staticmethod
    def real_pos(pos):
        x, y = pos
        return x * MESH + PADDING, y * MESH + PADDING

    def grid_pos(self, x, y):
        return ((x - PADDING) // MESH) + self.camx, ((y - PADDING) // MESH) + self.camy

    def draw_room(self):
        # This will need to be changed significantly
        # once we have a "camera" object
        pygame.draw.rect(self.surf, WHITE, Rect(PADDING, PADDING, MESH * DISPLAY_WIDTH, MESH * DISPLAY_HEIGHT))
        for i in range(DISPLAY_WIDTH):
            for j in range(DISPLAY_HEIGHT):
                pos = (i + self.camx, j + self.camy)
                if self.in_bounds(pos):
                    for obj in self.objmap[pos]:
                        if obj is not None:
                            obj.draw(self.surf, self.real_pos((i, j)))
                else:
                    pygame.draw.rect(self.surf, OUT_OF_BOUNDS_COLOR,
                                     Rect(self.real_pos((i, j)), (MESH, MESH)), 0)
        """for pos in self.objmap:
            if self.in_bounds(pos):
                for obj in self.objmap[pos]:
                    if obj is not None:
                        obj.draw(self.surf, self.real_pos(pos))"""

    def save(self, filename=None):
        if self.player is None:
            if not self.search_for_player():
                messagebox.showinfo("Warning", "The map must have a player object")
                return False
        if filename is None:
            filename = filedialog.asksaveasfilename(initialdir=MAPS_DIR, filetypes=["map .map"])
        if filename is None or filename == "":
            return False
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
                        if obj is not None and str(obj) not in DEPENDENT_OBJS:
                            s = bytes(obj)
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
                # Signals the end of the Placement Data
                file.write(bytes([0]))
                # Write the player's default position
                file.write(bytes(self.player.pos))
                # Begin Structural Data
                for s in self.structures:
                    file.write(bytes(s))
        except IOError:
            print("Failed to write to file")
            return False
        return True

    def load(self, filename=None, start_pos=None, editing=False):
        if filename is None:
            filename = filedialog.askopenfilename(initialdir=MAPS_DIR, filetypes=["map .map"])
        if filename is None:
            return False
        try:
            with open(filename, "r+b") as file:
                # IF NOT BIGMAP
                room_size = file.read(2)
                self.w = int(room_size[0])
                self.h = int(room_size[1])
                self.init_map()
                # This is what we pass to objects and structures as we make them
                map_arg = None if editing else self.objmap
                self.player = None
                self.dynamic = []
                self.structures = []
                x, y = 0, 0
                if not editing:
                    self.create_wall_border()
                # First load in the positional data
                while True:
                    pieces = file.read(1)[0]
                    if pieces == 0:
                        break
                    sizes = [file.read(1)[0] for _ in range(pieces)]
                    attrs = [file.read(n) for n in sizes]
                    obj_type = OBJ_TYPE[attrs[0].decode()]["type"]
                    args = list(map(process_data, attrs[1:]))
                    # IF NOT BIGMAP
                    n = int.from_bytes(file.read(2), byteorder="little")
                    pos_str = file.read(2*n)
                    # IF NOT BIGMAP
                    for i in range(n):
                        pos = tuple(map(int, pos_str[2*i : 2*i + 2]))
                        obj = obj_type(map_arg, pos, *args)
                        self.objmap[pos][obj.layer] = obj
                        if obj.dynamic:
                            self.dynamic.append(obj)
                # Some state behavior is determined by map position
                if not editing:
                    for pos in self.objmap:
                        for obj in self.objmap[pos]:
                            if obj is not None and obj.sticky:
                                self.update_group(obj)
                # Get the default player position
                if start_pos is None:
                    player_pos = tuple(file.read(2))
                    self.player = self.objmap[player_pos][Layer.PLAYER]
                    if self.player is not None:
                        car = self.objmap[self.player.pos][Layer.SOLID]
                        if car is not None and car.rideable:
                            self.player.riding = car
                else:
                    # Later, we should be able to carry player_pos info from previous room
                    pass
                # Load in the structural data of the map
                while True:
                    bytes = int.from_bytes(file.read(2), byteorder="little")
                    if bytes == 0:
                        # Either put in a b"\x00\x00" to signal the end
                        # or just let it reach the end of the file
                        break
                    str = StrType(file.read(1)[0])
                    data = file.read(bytes)
                    self.structures.append(load_str_from_data(map_arg, self.objmap, str, data))
            if not editing:
                for s in self.structures:
                    s.activate()
            self.update_camera()
        except IOError:
            print("Failed to read file")
            return False
        return True

    def init_map(self):
        self.objmap = {(x,y): [None for _ in range(NUM_LAYERS + 1)]
                       for x in range(-1, self.w + 1)
                       for y in range(-1, self.h + 1)}

    def expand_map(self):
        for x in range(-1, self.w + 1):
            for y in range(-1, self.h + 1):
                if (x,y) not in self.objmap:
                    self.objmap[(x,y)] = [None for _ in range(NUM_LAYERS + 1)]

# Turn a bytestring back into data, according to some simple rules
# Note we'll never store the integer 0 (need to be clever, use enums, etc)
def process_data(s):
    if s == b"":
        return False
    elif s == b"\x00":
        return True
    elif len(s) == 3:
        # This is a color
        return tuple(s)
    elif len(s) <= 2:
        # This is an int, possibly an intenum
        return int.from_bytes(s, byteorder="little")
    else:
        # If it's 4 bytes or longer, we'll assume it's a string
        return s.decode()