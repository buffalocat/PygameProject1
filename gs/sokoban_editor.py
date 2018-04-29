import tkinter as tk

from gs.sokoban import GSSokoban
from sokoban_obj import *
from font import FONT_MEDIUM
from sokoban_obj import Player, Layer
from widget import TextLines

class GSSokobanEditor(GSSokoban):
    def __init__(self, mgr, parent):
        self.editor = tk.Frame(mgr.root)
        self.init_editor_frame()
        super().__init__(mgr, parent, testing=False)
        self.create_mode = Wall
        self.create_args = []
        self.set_sample()
        self.create_text()

    def init_editor_frame(self):
        self.editor.pack(side=tk.RIGHT)
        main_menu = tk.Frame(self.editor)
        main_menu.pack(anchor=tk.N)
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

        def object_type_callback(*args):
            self.create_mode = OBJ_TYPE[self.object_type.get()]["type"]
            self.current_object_settings.pack_forget()
            self.current_object_settings, self.create_args = self.object_settings_dict[self.object_type.get()]
            self.current_object_settings.pack()
            self.set_sample()

        object_chooser = tk.Frame(self.editor)
        object_chooser.pack(side=tk.TOP)
        self.object_type_list = list(OBJ_TYPE.keys())
        self.object_type = tk.StringVar(object_chooser)
        self.object_type.set(self.object_type_list[0])
        self.object_type.trace("w", object_type_callback)
        object_type_menu = tk.OptionMenu(object_chooser, self.object_type, *self.object_type_list)
        object_type_menu.pack(side=tk.TOP)

        object_settings = tk.Frame(self.editor)
        object_settings.pack(side=tk.TOP)
        self.object_settings_dict = {}
        for obj_name in OBJ_TYPE:
            current = tk.Frame(object_settings)
            self.object_settings_dict[obj_name] = (current, [])
            for name, type in OBJ_TYPE[obj_name]["args"]:
                var = None
                widget = None
                if type == "bool":
                    var = tk.IntVar()
                    widget = tk.Checkbutton(current, text=name, variable=var)
                elif type == "color":
                    var = ColorVar()
                    color_list = list(OBJ_COLORS.keys())
                    var.var.set(color_list[0])
                    widget = tk.OptionMenu(current, var.var, *color_list)
                var.trace("w", self.set_sample)
                self.object_settings_dict[obj_name][1].append(var)
                widget.pack(side=tk.TOP)

        self.current_object_settings = self.object_settings_dict[self.object_type.get()][0]
        self.current_object_settings.pack()

    def draw(self):
        super().draw()
        self.draw_room()
        # Show what item we can create
        self.sample.draw(self.surf, (PADDING, ROOM_HEIGHT*MESH + PADDING * 3 // 2))
        self.text.draw(self.surf, (2 * PADDING + MESH, ROOM_HEIGHT*MESH + PADDING * 3 // 2))

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.key in OBJ_HOTKEYS:
                if OBJ_HOTKEYS[event.key] < len(self.object_type_list):
                    self.object_type.set(self.object_type_list[OBJ_HOTKEYS[event.key]])
        for event in pygame.event.get(MOUSEBUTTONDOWN):
            pos = self.grid_pos(*pygame.mouse.get_pos())
            if self.in_bounds(pos):
                if event.button == MB_LEFT:
                    self.create(pos)
                elif event.button == MB_RIGHT:
                    self.destroy(pos)

    def clear(self):
        self.load(filename=DEFAULT_MAP_FILE)

    def create(self, pos):
        obj = self.create_mode(pos, *(x.get() for x in self.create_args))
        self.objmap[pos][obj.layer] = obj
        if obj.is_player:
            self.player = obj
        return True

    def destroy(self, pos):
        for i in range(NUM_LAYERS + 1):
            obj = self.objmap[pos][i]
            self.objmap[pos][i] = None
            if obj is not None:
                if obj.is_player:
                    self.player = None
                if obj.sticky:
                    group = obj.root.group - {obj}
                    # Ensure everyone has a clean slate before rebuilding
                    for child in group:
                        child.root = child
                        child.group = frozenset([child])
                    for child in group:
                        self.update_group(child)

    def set_sample(self, *args):
        # An "object" at a fake position, not recorded on the grid
        self.sample = self.create_mode(None, *(x.get() for x in self.create_args))

    def create_text(self):
        self.text = TextLines()
        self.text.color = BLACK
        self.text.font = FONT_MEDIUM
        self.text.height = 40
        self.text.add_line("Press S to Save and L to Load")
        self.text.add_line("Left/Right click to Create/Destroy")
        self.text.add_line("Press Esc to exit the editor")

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

    def reinit(self):
        self.editor.pack(side=tk.RIGHT)

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


OBJ_HOTKEYS = {K_z: 0,
               K_x: 1,
               K_c: 2,
               K_v: 3}