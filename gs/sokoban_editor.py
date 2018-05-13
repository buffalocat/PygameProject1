import tkinter as tk
from tkinter import messagebox

from gs.sokoban import Camera, GSSokoban
from sokoban_obj import *
from sokoban_str import *
from font import FONT_MEDIUM, FONT_SMALL
from sokoban_obj import Layer
from widget import TextLines

DEFAULT_LAYER = Layer.SOLID

class SelectMode(IntEnum):
    NONE = auto()
    STANDARD = auto()
    SINGLE = auto()
    STRUCTURE = auto()

# SELECTION CONSTANTS
SELECT_COLOR = {SelectMode.STANDARD: HOT_PINK,
                SelectMode.SINGLE: BRIGHT_ORANGE,
                SelectMode.STRUCTURE: NEON_GREEN}

SELECT_THICKNESS = 3

MAP_JUMP_DISTANCE = 10

# GUI CONSTANTS
PADX = 5
PADY = 5

VERBOSE = True

class GSSokobanEditor(GSSokoban):
    def __init__(self, mgr, parent):
        self.editor = tk.Frame(mgr.root)
        super().__init__(mgr, parent, testing=False, editing=True)
        self.cam_mode = Camera.EDITOR
        self.init_attrs()
        self.init_editor_frame()
        self.init_selection()
        self.reinit()
        self.create_text()

    def init_attrs(self):
        """Initialize attributes of the editor"""
        self.camx = 0
        self.camy = 0
        self.padx = EDIT_PADDING
        self.pady = EDIT_PADDING
        self.edit_layer = None
        self.create_args = None
        self.visible = {layer: None for layer in Layer}

    def init_selection(self):
        self.select_mode.set(SelectMode.NONE)
        self.selected = []
        self.cur_object = None
        # Note: we have to be careful not to accidentally modify this!
        # But it's also convenient to not do a deep copy
        # This is the list of structures which contain all objects in selected
        self.structure_select = self.structures
        # This is the currently selected structure
        self.cur_structure = None

    def reinit(self):
        """Initialization which occurs whenever a map is loaded"""
        self.editor.pack(side=tk.RIGHT, anchor=tk.N, padx=20, pady=20)
        # Make sure part of the room is in view
        self.move_camera((0,0))


    def init_editor_frame(self):
        # Use this to initialize frame variables
        dummy_frame = tk.Frame()
        # MAIN MENU BLOCK
        main_menu = tk.Frame(self.editor, padx=PADX, pady=PADY)
        main_menu.pack()
        load_b = tk.Button(main_menu, text="Load", command=self.load_reinit)
        save_b = tk.Button(main_menu, text="Save", command=self.save)
        clear_b = tk.Button(main_menu, text="Clear", command=self.clear)
        play_b = tk.Button(main_menu, text="Play", command=self.play)
        quit_b = tk.Button(main_menu, text="Quit", command=self.ask_previous_state)
        load_b.grid()
        save_b.grid(row=0, column=1)
        clear_b.grid(row=0, column=2)
        play_b.grid(row=0, column=3)
        quit_b.grid(row=0, column=4)

        def room_width_callback(*args):
            try:
                self.w = min(int(self.room_width_var.get()), 255)
                self.update_camera()
                self.expand_map()
            except ValueError:
                pass

        def room_height_callback(*args):
            try:
                self.h = min(int(self.room_height_var.get()), 255)
                self.update_camera()
                self.expand_map()
            except ValueError:
                pass

        room_size = tk.Frame(self.editor, padx=PADX, pady=PADY)
        room_size.pack(side=tk.TOP, fill=tk.X)
        self.room_width_var = tk.StringVar()
        self.room_width_var.trace("w", room_width_callback)
        self.room_height_var = tk.StringVar()
        self.room_height_var.trace("w", room_height_callback)
        room_width_label = tk.Label(room_size, text="Width")
        room_height_label = tk.Label(room_size, text="Height")
        room_width = tk.Entry(room_size, textvariable=self.room_width_var)
        room_height = tk.Entry(room_size, textvariable=self.room_height_var)
        room_width_label.grid()
        room_width.grid(row=0, column=1)
        room_height_label.grid()
        room_height.grid(row=1, column=1)

        # SET UP PACK STRUCTURE UNDER THE MENU
        two_cols = tk.Frame(self.editor)
        two_cols.pack(side=tk.TOP)
        left_col = tk.Frame(two_cols)
        left_col.grid(sticky=tk.N)
        right_col = tk.Frame(two_cols)
        right_col.grid(row=0, column=1, sticky=tk.N)

        # LAYER SELECT AND OBJECT SELECT BLOCK
        def edit_layer_callback(*args):
            self.current_object_type_menu.pack_forget()
            self.edit_layer = Layer(self.edit_layer_var.get())
            self.current_object_type_menu = self.object_type_menu_dict[self.edit_layer]
            self.current_object_type_menu.pack()
            self.create_mode_var.set(OBJ_BY_LAYER[self.edit_layer][0])

        def object_type_callback(*args):
            self.current_object_settings.pack_forget()
            self.create_mode = OBJ_TYPE[self.create_mode_var.get()]["type"]
            self.current_object_settings, self.create_args = self.object_settings_dict[self.create_mode_var.get()]
            self.current_object_settings.pack()
            self.set_sample()

        layer_select = tk.LabelFrame(left_col, text="Layer Select", padx=PADX, pady=PADY)
        layer_select.pack(fill=tk.X)
        self.edit_layer_var = tk.IntVar()
        self.edit_layer_var.trace("w", edit_layer_callback)

        object_select = tk.LabelFrame(left_col, text="Object Select", padx=PADX, pady=PADY)
        object_select.pack(side=tk.TOP, fill=tk.X)
        # The purpose of this frame is to ensure the menu appears above the options
        object_type_menu_frame = tk.Frame(object_select)
        object_type_menu_frame.pack()
        self.create_mode_var = tk.StringVar(object_select)
        self.create_mode_var.trace("w", object_type_callback)
        self.object_type_menu_dict = {}

        tk.Label(layer_select, text="Layer").grid(row=0, column=0)
        tk.Label(layer_select, text="Edit").grid(row=0, column=1)
        tk.Label(layer_select, text="Visible").grid(row=0, column=2)


        row = 0
        for layer in Layer:
            row += 1
            tk.Label(layer_select, text=layer.name).grid(row=row, column=0)
            tk.Radiobutton(layer_select, variable=self.edit_layer_var, value=int(layer)).grid(row=row, column=1)
            var = BoolVar()
            var.set(True)
            tk.Checkbutton(layer_select, variable=var.var).grid(row=row, column=2)
            self.visible[layer] = var
            self.object_type_menu_dict[layer] = tk.OptionMenu(object_type_menu_frame, self.create_mode_var,
                                                              *(x for x in OBJ_BY_LAYER[layer]))

        object_settings = tk.Frame(object_select, padx=PADX, pady=PADY)
        object_settings.pack(side=tk.TOP, fill=tk.X)
        self.object_settings_dict = {}
        for obj_name in OBJ_TYPE:
            if obj_name not in DEPENDENT_OBJS:
                current = tk.Frame(object_settings)
                self.object_settings_dict[obj_name] = (current, [])
                for name, type in OBJ_TYPE[obj_name]["args"]:
                    var, widget = self.make_variable_widget(current, name, type, obj_name)
                    var.trace("w", self.set_sample)
                    self.object_settings_dict[obj_name][1].append(var)
                    widget.pack(side=tk.TOP)

        # Initialize the Layer and Object select
        self.current_object_settings = dummy_frame
        self.current_object_type_menu = dummy_frame

        self.edit_layer_var.set(int(DEFAULT_LAYER))

        # OBJ SELECTION
        def on_select_object(event):
            cur = event.widget.curselection()
            if cur:
                self.select_mode.set(SelectMode.SINGLE)
                self.cur_object = self.selected[cur[0]]

        select_frame = tk.LabelFrame(right_col, text="Selection", padx=PADX, pady=PADY)
        select_frame.pack(side=tk.TOP, fill=tk.X)
        select_scrollbar = tk.Scrollbar(select_frame, orient=tk.VERTICAL)
        self.select_list = tk.Listbox(select_frame, selectmode=tk.SINGLE,
                                      yscrollcommand=select_scrollbar.set)
        self.select_list.bind("<<ListboxSelect>>", on_select_object)
        select_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        select_scrollbar.config(command=self.select_list.yview)
        self.select_list.pack()

        # STRUCTURE SELECTION
        def on_select_structure(event):
            cur = event.widget.curselection()
            if cur:
                self.select_mode.set(SelectMode.STRUCTURE)
                self.cur_structure = self.structure_select[cur[0]]

        structure_select_frame = tk.LabelFrame(right_col, text="Structure Select", padx=PADX, pady=PADY)
        structure_select_frame.pack(side=tk.TOP, fill=tk.X)
        structure_select_scrollbar = tk.Scrollbar(structure_select_frame, orient=tk.VERTICAL)
        self.structure_select_list = tk.Listbox(structure_select_frame, selectmode=tk.SINGLE,
                                                yscrollcommand=structure_select_scrollbar.set)
        self.structure_select_list.bind("<<ListboxSelect>>", on_select_structure)
        structure_select_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        structure_select_scrollbar.config(command=self.select_list.yview)
        self.structure_select_list.pack()

        # EDIT SELECTION
        def change_select_mode_callback(*args):
            self.current_edit_selection.pack_forget()
            self.current_edit_selection = edit_selection_dict[self.select_mode.get()]
            self.current_edit_selection.pack()

        edit_selection = tk.Frame(left_col)
        edit_selection.pack(side=tk.TOP, fill=tk.X)
        edit_selection_nothing = tk.Frame(edit_selection)

        # CREATE STRUCTURE
        create_structure = tk.LabelFrame(edit_selection, text="Create Structure", padx=PADX, pady=PADY)

        link_switch_b = tk.Button(create_structure, text="Link Switch", command=self.link_switch)
        link_switch_b.pack()

        self.link_switch_persistent, link_switch_persistent_box = self.make_variable_widget(create_structure, "Persistent", "bool")
        link_switch_persistent_box.pack()

        create_group_b = tk.Button(create_structure, text="Create Group", command=self.create_group)
        # This doesn't exist yet
        #create_group_b.pack()

        # EDIT OBJECT
        edit_object = tk.LabelFrame(edit_selection, text="Edit Object", padx=PADX, pady=PADY)
        #delete_object_b = tk.Button(edit_object, text="Delete Object")
        #delete_object_b.pack()

        # EDIT STRUCTURE
        edit_structure = tk.LabelFrame(edit_selection, text="Edit Structure", padx=PADX, pady=PADY)
        delete_structure = tk.Button(edit_structure, text="Delete Structure", command=self.delete_selected_structure)
        delete_structure.pack()

        # Finish putting together the EDIT SELECTION frame
        edit_selection_dict = {SelectMode.NONE: edit_selection_nothing,
                                    SelectMode.STANDARD: create_structure,
                                    SelectMode.SINGLE: edit_object,
                                    SelectMode.STRUCTURE: edit_structure}
        self.current_edit_selection = edit_selection_nothing
        self.select_mode = SelectModeVar()
        self.select_mode.trace("w", change_select_mode_callback)

        # Nothing actually points to the dummy frame anymore: destroy it
        dummy_frame.destroy()

    def delete_selected_structure(self):
        if self.cur_structure is not None:
            self.structures.remove(self.cur_structure)
            self.cur_structure = None
            self.reset_selection()

    def make_variable_widget(self, frame, name, type, obj_name=None):
        var = None
        widget = None
        if type == "bool":
            var = BoolVar()
            var.set(False)
            widget = tk.Checkbutton(frame, text=name, variable=var.var)
        elif type == "color":
            var = ColorVar()
            color_list = OBJ_TYPE[obj_name]["color"] if obj_name in OBJ_TYPE and "color" in OBJ_TYPE[obj_name] else None
            if not color_list: color_list = [color.name for color in ColorEnum]
            var.set(color_list[0])
            widget = tk.OptionMenu(frame, var.var, *color_list)
        return var, widget

    def draw(self):
        super().draw()
        self.sample.draw(self.surf, (self.padx, DISPLAY_HEIGHT * MESH + self.pady * 3 // 2))
        self.text.draw(self.surf, (2 * self.padx + MESH, DISPLAY_HEIGHT * MESH + self.pady * 3 // 2))
        self.draw_selection()

    def draw_selection(self):
        mode = self.select_mode.get()
        if mode != SelectMode.NONE:
            selection = []
            if mode == SelectMode.STANDARD:
                selection = self.selected
            elif mode == SelectMode.SINGLE:
                selection = [self.cur_object]
            elif mode == SelectMode.STRUCTURE:
                selection = self.cur_structure.get_objs()
            color = SELECT_COLOR[mode]
            for obj in selection:
                x, y = self.real_pos(obj.pos)
                if obj.layer == Layer.SOLID:
                    pygame.draw.rect(self.surf, color, Rect(x, y, MESH, MESH), SELECT_THICKNESS)
                elif obj.layer == Layer.FLOOR:
                    pygame.draw.rect(self.surf, color, Rect(x+MESH//6, y+MESH//6, 2*MESH//3 + 1, 2*MESH//3 + 1), SELECT_THICKNESS)
                elif obj.layer == Layer.PLAYER:
                    pygame.draw.circle(self.surf, color, (x+MESH//2, y+MESH//2), MESH//3, SELECT_THICKNESS)

    def draw_room(self):
        pygame.draw.rect(self.surf, WHITE, Rect(self.padx, self.pady, MESH * DISPLAY_WIDTH, MESH * DISPLAY_HEIGHT))
        for layer in Layer:
            if self.visible[layer].get():
                self.draw_layer(layer)
        self.draw_out_of_bounds()

    def move_camera(self, dir, distance=1):
        dx, dy = dir[0] * distance, dir[1] * distance
        self.camx = min(max(-DISPLAY_WIDTH+1, self.camx + dx), self.w-1)
        self.camy = min(max(-DISPLAY_HEIGHT+1, self.camy + dy), self.h-1)

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.key in DIR.keys():
                distance = MAP_JUMP_DISTANCE if pygame.key.get_mods() & KMOD_SHIFT else 1
                self.move_camera(DIR[event.key], distance)
            if event.key in LAYER_HOTKEYS:
                self.edit_layer_var.set(LAYER_HOTKEYS[event.key])
            if event.key in OBJ_HOTKEYS:
                self.create_mode_var.set(OBJ_BY_LAYER[self.edit_layer][OBJ_HOTKEYS[event.key]
                                                                       % len(OBJ_BY_LAYER[self.edit_layer])])
        for event in pygame.event.get(MOUSEBUTTONDOWN):
            x, y = pygame.mouse.get_pos()
            if self.in_editor(x, y):
                pos = self.grid_pos(x, y)
                if self.in_bounds(pos):
                    if event.button == MB_RIGHT:
                        self.handle_right_click(pos)
                    if event.button == MB_LEFT:
                        self.handle_left_click(pos)
        for event in pygame.event.get(MOUSEMOTION):
            x, y = pygame.mouse.get_pos()
            if self.in_editor(x, y):
                pos = self.grid_pos(x, y)
                if self.in_bounds(pos):
                    if pygame.mouse.get_pressed()[MB_RIGHT - 1]:
                        self.handle_right_click(pos)
                    if pygame.mouse.get_pressed()[MB_LEFT-1]:
                        self.handle_left_click(pos)

    def in_editor(self, x, y):
        return EDITOR_RECT.collidepoint(x, y)

    def handle_left_click(self, pos):
        if pygame.key.get_mods() & KMOD_CTRL:
            obj = self.objmap[pos][self.edit_layer]
            if obj is not None:
                self.add_to_selection(obj)
        else:
            if not self.selected:
                self.create(pos)
            self.reset_selection()

    def handle_right_click(self, pos):
        if pygame.key.get_mods() & KMOD_CTRL:
            obj = self.objmap[pos][self.edit_layer]
            if obj is not None:
                self.remove_from_selection(obj)
        else:
            if not self.selected:
                self.destroy(pos)
            self.reset_selection()

    def add_to_selection(self, obj):
        self.select_mode.set(SelectMode.STANDARD)
        if obj not in self.selected:
            # Here we know the list is only getting smaller
            self.structure_select = [s for s in self.structure_select if obj in s.get_objs()]
            self.reset_structure_select_list()
            self.selected.append(obj)
            self.select_list.insert(tk.END, obj.display_str())

    def remove_from_selection(self, obj):
        if obj in self.selected:
            i = self.selected.index(obj)
            self.selected.remove(obj)
            self.select_list.delete(i)
            # The list could get larger
            self.structure_select = [s for s in self.structures
                                     if all(x in s.get_objs() for x in self.selected)]
            self.reset_structure_select_list()
        if self.selected:
            self.select_mode.set(SelectMode.STANDARD)
        else:
            self.select_mode.set(SelectMode.NONE)

    def reset_selection(self):
        self.select_mode.set(SelectMode.NONE)
        self.selected = []
        self.structure_select = self.structures
        self.select_list.delete(0, tk.END)
        self.reset_structure_select_list()

    def reset_structure_select_list(self):
        self.structure_select_list.delete(0, tk.END)
        self.structure_select_list.insert(0, *[str.name() for str in self.structure_select])

    def load_reinit(self):
        """Load a map and reinitialize the editor"""
        if self.load(editing=True):
            self.init_selection()
            self.reinit()

    def clear(self):
        if messagebox.askokcancel("Clear", "Clear the current map?"):
            self.load(filename=DEFAULT_MAP_FILE, editing=True)

    def ask_previous_state(self):
        if messagebox.askokcancel("Quit", "Quit the Editor?"):
            self.previous_state()

    def create(self, pos):
        if self.objmap[pos][self.edit_layer] is None:
            obj = self.create_mode(None, pos, *(x.get() for x in self.create_args))
            self.objmap[pos][obj.layer] = obj
            if obj.is_player:
                self.player = obj
            return True
        return False

    def destroy(self, pos):
        obj = self.objmap[pos][self.edit_layer]
        if obj is not None:
            self.remove_from_selection(obj)
            # Remove the object from any structures it's in
            for s in self.structures:
                if obj in s.get_objs():
                    s.remove(self.structures, obj)
            self.objmap[pos][self.edit_layer] = None
            if obj.is_player:
                self.search_for_player()
            return True
        return False

    def edit(self, pos):
        pass

    def link_switch(self):
        switches = []
        gates = []
        for obj in self.selected:
            if obj.is_switch:
                switches.append(obj)
            elif obj.is_switchable:
                gates.append(obj)
            else:
                return False
        self.structures.append(SwitchLink(None, switches, gates, self.link_switch_persistent.get()))
        self.reset_selection()
        return True

    def create_group(self):
        pass

    def update(self):
        pass

    def set_sample(self, *args):
        # An "object" at a fake position, not recorded on the grid
        self.sample = self.create_mode(None, None, *(x.get() for x in self.create_args))

    def create_text(self):
        self.text = TextLines()
        self.text.color = BLACK
        self.text.font = FONT_SMALL
        self.text.height = 20
        self.text.add_line("Left/Right click to Create/Destroy (only on current layer)")
        self.text.add_line("Hold ctrl while clicking to Select/Deselect")
        self.text.add_line("Use arrow keys to move; hold shift to move faster")
        self.text.add_line("QWE change layers quickly; 1-9 cycle through objects")
        self.text.add_line("In-game Controls: Arrow keys to move, Z to undo")

    def destroy_editor(self):
        widgets = [self.editor]
        for w in widgets:
            widgets.extend(w.winfo_children())
        for w in widgets:
            w.destroy()

    def play(self):
        if self.save(TEMP_MAP_FILE):
            self.editor.pack_forget()
            GSSokoban(self.mgr, self, testing=True)

    def quit(self):
        super().quit()
        self.destroy_editor()

# Wrappers of tk.Var classes to make things behave conveniently
class ColorVar:
    def __init__(self):
        self.var = tk.StringVar()

    def get(self):
        return ColorEnum[self.var.get()]

    def set(self, value):
        self.var.set(value)

    def trace(self, mode, callback):
        return self.var.trace(mode, callback)


class BoolVar:
    def __init__(self):
        self.var = tk.IntVar()

    def get(self):
        return True if self.var.get() else False

    def set(self, value):
        self.var.set(value)

    def trace(self, mode, callback):
        return self.var.trace(mode, callback)


class SelectModeVar:
    def __init__(self):
        self.var = tk.IntVar()

    def get(self):
        return SelectMode(self.var.get())

    def set(self, value):
        self.var.set(int(value))

    def trace(self, mode, callback):
        return self.var.trace(mode, callback)


LAYER_HOTKEYS = {K_q: 1,
                 K_w: 2,
                 K_e: 3}

OBJ_HOTKEYS = {K_1: 0,
               K_2: 1,
               K_3: 2,
               K_4: 3,
               K_5: 4,
               K_6: 5,
               K_7: 6,
               K_8: 7,
               K_9: 8}