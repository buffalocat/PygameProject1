import tkinter as tk

from gs.sokoban import *
from font import FONT_MEDIUM
from sokoban_obj import Player, Layer
from widget import TextLines

class GSSokobanEditor(GSSokoban):
    def __init__(self, mgr, parent):
        self.editor = tk.Frame(mgr.root)
        self.init_editor_frame()
        super().__init__(mgr, parent, testing=False)
        self.create_mode = Wall
        self.set_sample()
        self.create_text()

    def init_editor_frame(self):
        self.editor.pack(side=tk.RIGHT)
        main_menu = tk.Frame(self.editor)
        main_menu.pack()
        load_b = tk.Button(main_menu, text="Load", command=self.load)
        save_b = tk.Button(main_menu, text="Save", command=self.save)
        play_b = tk.Button(main_menu, text="Play", command=self.play)
        quit_b = tk.Button(main_menu, text="Quit", command=self.previous_state)
        load_b.pack(side=tk.LEFT)
        save_b.pack(side=tk.LEFT)
        play_b.pack(side=tk.LEFT)
        quit_b.pack(side=tk.LEFT)


    def draw(self):
        super().draw()
        self.draw_room()
        # Show what item we can create
        self.sample.draw(self.surf, (PADDING, ROOM_HEIGHT*MESH + PADDING * 3 // 2))
        self.text.draw(self.surf, (2 * PADDING + MESH, ROOM_HEIGHT*MESH + PADDING * 3 // 2))

    def handle_input(self):
        for event in pygame.event.get(MOUSEBUTTONDOWN):
            pos = self.grid_pos(*pygame.mouse.get_pos())
            if self.in_bounds(pos):
                if event.button == MB_LEFT:
                    self.create(pos)
                elif event.button == MB_RIGHT:
                    self.destroy(pos)

    def create(self, pos):
        obj = self.create_mode(pos)
        self.objmap[pos][obj.layer] = obj
        if obj.sticky:
            self.update_group(obj)
        return True

    def destroy(self, pos):
        for i in range(NUM_LAYERS + 1):
            obj = self.objmap[pos][i]
            self.objmap[pos][i] = None
            if obj is not None and obj.sticky:
                group = obj.root.group - {obj}
                # Ensure everyone has a clean slate before rebuilding
                for child in group:
                    child.root = child
                    child.group = frozenset([child])
                for child in group:
                    self.update_group(child)
            del obj

    def set_sample(self):
        # An "object" at a fake position, not recorded on the grid
        self.sample = self.create_mode(None)

    def create_text(self):
        self.text = TextLines()
        self.text.color = BLACK
        self.text.font = FONT_MEDIUM
        self.text.height = 40
        self.text.add_line("Press S to Save and L to Load")
        self.text.add_line("ZXCVB change block type")
        self.text.add_line("Left/Right click to Create/Destroy")

    def destroy_editor(self):
        widgets = [self.editor]
        for w in widgets:
            widgets.extend(w.winfo_children())
        for w in widgets:
            w.destroy()

    def play(self):
        self.editor.pack_forget()
        self.save(TEMP_MAP_FILE)
        GSSokoban(self.mgr, self, testing=True)

    def reinit(self):
        self.editor.pack(side=tk.RIGHT)

    def quit(self):
        super().quit()
        self.destroy_editor()