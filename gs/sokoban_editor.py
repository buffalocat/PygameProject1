import tkinter as tk

from enum import Enum, auto

from gs.sokoban import GSSokoban
from sokoban_obj import *
from sokoban_str import *
from font import FONT_MEDIUM
from sokoban_obj import Layer
from widget import TextLines

DEFAULT_LAYER = Layer.SOLID

VERBOSE = True

class GSSokobanEditor(GSSokoban):
    def __init__(self, mgr, parent):
        self.editor = tk.Frame(mgr.root)
        self.selected = set()
        self.init_attrs()
        self.init_editor_frame()
        super().__init__(mgr, parent, testing=False)
        self.create_text()

    def reinit(self):
        self.editor.pack(side=tk.RIGHT, anchor=tk.N, padx=20, pady=20)

    def init_attrs(self):
        """Initialize attributes so we know they exist"""
        self.edit_layer = None
        self.create_args = None

    def init_editor_frame(self):
        self.reinit()

        # MAIN MENU BLOCK
        main_menu = tk.Frame(self.editor)
        main_menu.pack()
        load_b = tk.Button(main_menu, text="Load", command=self.load)
        save_b = tk.Button(main_menu, text="Save", command=self.save)
        clear_b = tk.Button(main_menu, text="Clear", command=self.clear)
        play_b = tk.Button(main_menu, text="Play", command=self.play)
        quit_b = tk.Button(main_menu, text="Quit", command=self.previous_state)
        load_b.grid()
        save_b.grid(row=0, column=1)
        clear_b.grid(row=0, column=2)
        play_b.grid()
        quit_b.grid(row=1, column=1)

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

        layer_select = tk.Frame(self.editor)
        layer_select.pack()
        self.edit_layer_var = tk.IntVar()
        self.edit_layer_var.trace("w", edit_layer_callback)

        object_chooser = tk.Frame(self.editor)
        object_chooser.pack(side=tk.TOP)
        self.create_mode_var = tk.StringVar(object_chooser)
        self.create_mode_var.trace("w", object_type_callback)
        self.layer_button_dict = {}
        self.object_type_menu_dict = {}

        for layer in Layer:
            current = tk.Radiobutton(layer_select, text=layer.name, variable=self.edit_layer_var, value=int(layer))
            self.layer_button_dict[layer] = current
            self.object_type_menu_dict[layer] = tk.OptionMenu(object_chooser, self.create_mode_var, *OBJ_BY_LAYER[layer])
            current.pack()

        object_settings = tk.Frame(self.editor)
        object_settings.pack(side=tk.TOP)
        self.object_settings_dict = {}
        for obj_name in OBJ_TYPE:
            current = tk.Frame(object_settings)
            self.object_settings_dict[obj_name] = (current, [])
            for name, type in OBJ_TYPE[obj_name]["args"]:
                var, widget = self.make_variable_widget(current, name, type)
                var.trace("w", self.set_sample)
                self.object_settings_dict[obj_name][1].append(var)
                widget.pack(side=tk.TOP)

        # Initialize the Layer and Object select
        dummy_frame = tk.Frame()
        self.current_object_settings = dummy_frame
        self.current_object_type_menu = dummy_frame

        self.edit_layer_var.set(int(DEFAULT_LAYER))
        # Those variables no longer point to the dummy frame
        dummy_frame.destroy()

        # STRUCTURES BLOCK
        group_operations = tk.Frame(self.editor)
        group_operations.pack(side=tk.TOP)

        link_switch_b = tk.Button(group_operations, text="Link Switch", command=self.link_switch)
        link_switch_b.pack()

        create_group_b = tk.Button(group_operations, text="Create Group", command=self.create_group)
        create_group_b.pack()

    def make_variable_widget(self, frame, name, type):
        var = None
        widget = None
        if type == "bool":
            var = BoolVar()
            var.var.set(0)
            widget = tk.Checkbutton(frame, text=name, variable=var.var)
        elif type == "color":
            var = ColorVar()
            color_list = list(OBJ_COLORS.keys())
            var.var.set(color_list[0])
            widget = tk.OptionMenu(frame, var.var, *color_list)
        return var, widget

    def draw(self):
        super().draw()
        self.sample.draw(self.surf, (PADDING, ROOM_HEIGHT*MESH + PADDING * 3 // 2))
        self.text.draw(self.surf, (2 * PADDING + MESH, ROOM_HEIGHT*MESH + PADDING * 3 // 2))

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.key in LAYER_HOTKEYS:
                self.edit_layer_var.set(LAYER_HOTKEYS[event.key])
            if event.key in OBJ_HOTKEYS:
                self.create_mode_var.set(OBJ_BY_LAYER[self.edit_layer][OBJ_HOTKEYS[event.key]
                                                                       % len(OBJ_BY_LAYER[self.edit_layer])])
        for event in pygame.event.get(MOUSEBUTTONDOWN):
            pos = self.grid_pos(*pygame.mouse.get_pos())
            if self.in_bounds(pos):
                if event.button == MB_LEFT:
                    self.handle_left_click(pos)
                elif event.button == MB_RIGHT:
                    self.handle_right_click(pos)
        for event in pygame.event.get(MOUSEMOTION):
            pos = self.grid_pos(*pygame.mouse.get_pos())
            if self.in_bounds(pos):
                if pygame.mouse.get_pressed()[MB_LEFT-1]:
                    self.handle_left_click(pos)
                elif pygame.mouse.get_pressed()[MB_RIGHT-1]:
                    self.handle_right_click(pos)

    def handle_left_click(self, pos):
        if pygame.key.get_mods() & KMOD_CTRL:
            obj = self.objmap[pos][self.edit_layer]
            if obj is not None:
                self.selected.add(obj)
                if VERBOSE:
                    print(f"Selected {obj}")
        else:
            if self.selected:
                self.selected = set()
            else:
                self.create(pos)

    def handle_right_click(self, pos):
        if pygame.key.get_mods() & KMOD_CTRL:
            self.selected.discard(self.objmap[pos][self.edit_layer])
        else:
            if self.selected:
                self.selected = set()
            else:
                self.destroy(pos)

    def clear(self):
        self.load(filename=DEFAULT_MAP_FILE)

    def create(self, pos):
        obj = self.create_mode(self.objmap, pos, *(x.get() for x in self.create_args))
        self.objmap[pos][obj.layer] = obj
        if obj.is_player:
            self.player = obj
        return True

    def destroy(self, pos):
        obj = self.objmap[pos][self.edit_layer]
        # Destroying an object also destroys any structures it's in
        for x in self.structures:
            if obj in x.get_objs():
                self.structures.remove(x)
        self.objmap[pos][self.edit_layer] = None

    def edit(self, pos):
        pass

    def link_switch(self):
        switch = None
        connections = []
        for obj in self.selected:
            if obj.is_switch:
                if switch is not None:
                    return False
                switch = obj
            elif obj.is_switchable:
                connections.append(obj)
            else:
                return False
        if switch is None or len(connections) == 0:
            return False
        self.structures.append(SwitchLink(switch, connections))
        if VERBOSE:
            print(f"Made a switch with {switch} and {connections}")
        return True

    def create_group(self):
        pass

    def set_sample(self, *args):
        # An "object" at a fake position, not recorded on the grid
        self.sample = self.create_mode(None, None, *(x.get() for x in self.create_args))

    def create_text(self):
        self.text = TextLines()
        self.text.color = BLACK
        self.text.font = FONT_MEDIUM
        self.text.height = 40
        self.text.add_line("Left/Right click to Create/Destroy")

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

# A wrapper of tk.StringVar to make it behave how I want
class ColorVar:
    def __init__(self):
        self.var = tk.StringVar()

    def get(self):
        return OBJ_COLORS[self.var.get()]

    def trace(self, mode, callback):
        return self.var.trace(mode, callback)

class BoolVar:
    def __init__(self):
        self.var = tk.IntVar()

    def get(self):
        return True if self.var.get() else False

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