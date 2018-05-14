from collections import deque
from tkinter import filedialog, messagebox

from background import BGCrystal, BGSolid
from delta import Delta
from game_state import GameState
from sokoban_obj import *
from sokoban_str import *


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
        self.root.set_bg(BGSolid(LAVENDER))
        self.cam_mode = Camera.FOLLOW_PLAYER
        self.padx = CENTER_PADDINGX
        self.pady = CENTER_PADDINGY
        self.input_key = None
        self.delta = Delta()
        self.deltas = deque(maxlen=MAX_DELTAS)
        self.bg = WHITE
        self.player = None
        if pick_level:
            filename = None
        else:
            filename = TEMP_MAP_FILE if testing else DEFAULT_MAP_FILE
        if not self.load(filename=filename, editing=editing):
            self.previous_state()

    def update_dynamic(self):
        for obj in self.dynamic:
            obj.update()
        for str in self.structures:
            str.update()

    def update_camera(self):
        if self.cam_mode == Camera.FOLLOW_PLAYER:
            px, py = self.player.pos
            if self.w < DISPLAY_WIDTH:
                self.camx = (self.w - DISPLAY_WIDTH) // 2
                self.camxoff = MESH //2 if ((self.w - DISPLAY_WIDTH) % 2) else 0
            else:
                self.camx = min(max(0, px - DISPLAY_CX), self.w - DISPLAY_WIDTH)
                self.camxoff = 0
            if self.h < DISPLAY_HEIGHT:
                self.camy = (self.h - DISPLAY_HEIGHT) // 2
                self.camyoff = MESH //2 if ((self.h - DISPLAY_HEIGHT) % 2) else 0
            else:
                self.camy = min(max(0, py - DISPLAY_CY), self.h - DISPLAY_HEIGHT)
                self.camyoff = 0

    def draw(self):
        super().draw()
        self.draw_room()

    def pre_update(self):
        self.delta = Delta()

    def handle_input(self):
        self.input_key = None
        for event in pygame.event.get(KEYDOWN):
            if event.type == KEYDOWN:
                if event.key in INPUT_KEYS:
                    self.input_key = event.key
                    break

    def update(self):
        input = self.input_key
        # Don't save a Delta at all unless the player Did Something
        if input is not None:
            # Undo (if we have any Deltas left)
            if input == K_z and self.deltas:
                self.delta = self.deltas.pop()
                self.undo_delta()
            # Otherwise, we handle input and put the Delta on the queue
            else:
                moved = False
                if input in DIR:
                    moved = self.try_move_player(DIR[input])
                if moved:
                    self.apply_delta()
                    self.deltas.append(self.delta)
        self.update_camera()

    def apply_delta(self):
        # Move Objects, and set up group merging
        move_objs = []
        for dir in DIR.values():
            dx, dy = dir
            for pos, layer in self.delta.moves[dir]:
                obj = self.objmap[pos][layer]
                self.objmap[pos][layer] = None
                move_objs.append(obj)
                x, y = obj.pos
                obj.pos = (x+dx, y+dy)
        for obj in move_objs:
            self.objmap[obj.pos][obj.layer] = obj
            obj.group.checked = False
        for obj in move_objs:
            if not obj.group.checked:
                obj.group.update_delta()
        # Merge Groups
        for group_set in self.delta.group_merges:
            self.merge_groups(group_set)
        # Update dynamic objects, and have them push their changes on the delta
        self.update_dynamic()

    def undo_delta(self):
        for str, delta in self.delta.structure[::-1]:
            str.undo_delta(delta)
        for obj, delta in self.delta.dynamic[::-1]:
            obj.undo_delta(delta)
        for group_set in self.delta.group_merges[::-1]:
            for group in group_set:
                for obj in group.objs:
                    obj.group = group
        move_objs = []
        for dir in DIR.values():
            dx, dy = dir
            for pos, layer in self.delta.moves[dir]:
                pos = (pos[0] + dx, pos[1] + dy)
                obj = self.objmap[pos][layer]
                self.objmap[pos][layer] = None
                move_objs.append(obj)
                x, y = obj.pos
                obj.pos = (x - dx, y - dy)
        for obj in move_objs:
            self.objmap[obj.pos][obj.layer] = obj

    def merge_groups(self, group_set):
        if len(group_set) > 1:
            new_group = Group(self, set().union(*(group.objs for group in group_set)))
            for obj in new_group.objs:
                obj.group = new_group
            return new_group
        return None

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.w and 0 <= pos[1] < self.h

    def create_wall_border(self):
        for y in [-1, self.h]:
            for x in range(self.w):
                self.objmap[(x, y)][Layer.SOLID] = Wall(self, (x,y))
        for x in [-1, self.w]:
            for y in range(self.h):
                self.objmap[(x, y)][Layer.SOLID] = Wall(self, (x,y))

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
        self.player = None
        return False

    def try_move_player(self, dpos):
        if self.player is None:
            return False
        x, y = self.player.pos
        dx, dy = dpos
        if self.objmap[(x+dx, y+dy)][Layer.PLAYER] is not None:
            return False
        self.delta.add_move(self.player, dpos)
        car = self.player.riding
        can_move = True
        if car is not None:
            can_move = self.try_move(dpos, car)
        if not can_move:
            self.delta.reset_moves()
            return False
        return True

    def try_move(self, dpos, obj):
        # The set of all groups influenced by the motion
        seen = {obj.group}
        to_check = [obj.group]
        can_move = True
        dx, dy = dpos
        while can_move and to_check:
            # Grab the next group to check
            for cur in to_check.pop().objs:
                self.delta.add_move(cur, dpos)
                x, y = cur.pos
                # adj is the tile that cur is trying to move into
                adj = self.objmap[(x+dx, y+dy)][Layer.SOLID]
                # There was nothing there, or we were already considering it
                if adj is None or adj.group in seen:
                    continue
                # It's new, and we can push it
                elif adj.pushable:
                    seen.add(adj.group)
                    to_check.append(adj.group)
                # We're trying to push something we can't push
                else:
                    can_move = False
                    break
        return can_move

    def update_group(self, obj):
        """Connect to nearby sticky objects"""
        x, y = obj.pos
        for dx, dy in ADJ:
            adj = self.objmap[(x+dx, y+dy)][Layer.SOLID]
            if adj is not None and adj.sticky and obj.color == adj.color and obj.root is not adj.root:
                obj.merge_group(adj)

    def real_pos(self, pos, camera=True):
        x, y = pos
        if camera:
            x -= self.camx
            y -= self.camy
        return x * MESH + self.padx, y * MESH + self.pady

    def grid_pos(self, x, y):
        return ((x - self.padx) // MESH) + self.camx, ((y - self.pady) // MESH) + self.camy

    def draw_room(self):
        pygame.draw.rect(self.surf, WHITE, Rect(self.padx, self.pady, MESH * DISPLAY_WIDTH, MESH * DISPLAY_HEIGHT))
        for layer in Layer:
            self.draw_layer(layer)
        self.draw_out_of_bounds()

    def draw_layer(self, layer):
        for i in range(DISPLAY_WIDTH):
            for j in range(DISPLAY_HEIGHT):
                pos = (i + self.camx, j + self.camy)
                if self.in_bounds(pos):
                    obj = self.objmap[pos][layer]
                    if obj is not None:
                        obj.draw(self.surf, self.real_pos(pos))

    def draw_out_of_bounds(self):
        for i in range(DISPLAY_WIDTH):
            for j in range(DISPLAY_HEIGHT):
                pos = (i + self.camx, j + self.camy)
                if not self.in_bounds(pos):
                    pygame.draw.rect(self.surf, OUT_OF_BOUNDS_COLOR,
                                     Rect(self.real_pos(pos), (MESH, MESH)), 0)

    def save(self, filename=None):
        if self.player is None:
            if not self.search_for_player():
                messagebox.showinfo("Warning", "The map must have a player object")
                return False
        if filename is None:
            filename = filedialog.asksaveasfilename(initialdir=MAPS_DIR, filetypes=["map .map"])
        if filename is None or filename == "":
            return False
        if filename.split(".")[-1] not in ["map", "mapx"]:
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
                state_arg = None if editing else self
                self.player = None
                self.dynamic = []
                self.structures = []
                groups_to_check = set()
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
                    args = list(map(unpack_bytes, attrs[1:]))
                    # IF NOT BIGMAP
                    n = int.from_bytes(file.read(2), byteorder="little")
                    pos_str = file.read(2*n)
                    # IF NOT BIGMAP
                    for i in range(n):
                        pos = tuple(map(int, pos_str[2*i : 2*i + 2]))
                        obj = obj_type(state_arg, pos, *args)
                        self.objmap[pos][obj.layer] = obj
                        if obj.dynamic:
                            self.dynamic.append(obj)
                        if obj.sticky and not editing:
                            obj.group.checked = False
                            groups_to_check.add(obj.group)
                # Some state behavior is determined by map position
                if not editing:
                    for group in groups_to_check:
                        if not group.checked:
                            self.merge_groups(group.find_adjacent_groups())
                # Get the default player position
                if start_pos is None:
                    player_pos = tuple(file.read(2))
                    self.player = Player(self, player_pos)
                    self.objmap[player_pos][Layer.PLAYER] = self.player
                    car = self.objmap[self.player.pos][Layer.SOLID]
                    if car is not None and car.rideable:
                        self.player.riding = car
                else:
                    # Later, we should be able to carry player_pos info from previous room
                    pass
                # Load in the structural data of the map
                while True:
                    try:
                        strtype = StrType(file.read(1)[0])
                    except IndexError:
                        break
                    pieces = file.read(1)[0]
                    sizes = [file.read(1)[0] for _ in range(pieces)]
                    attrs = [file.read(n) for n in sizes]
                    self.structures.append(load_str_from_data(self, strtype, attrs))
            if not editing:
                for s in self.structures:
                    s.real_init()
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
def unpack_bytes(s):
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