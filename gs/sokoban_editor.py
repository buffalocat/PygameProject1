from gs.sokoban import *
from font import FONT_MEDIUM
from widget import TextLines

class GSSokobanEditor(GSSokoban):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.create_mode = Wall
        self.set_sample()
        self.create_text()

    def draw(self):
        super().draw()
        self.draw_room()
        # Show what item we can create
        self.sample.draw(self.surf, (PADDING, ROOM_HEIGHT*MESH + PADDING * 3 // 2))
        self.text.draw(self.surf, (2 * PADDING + MESH, ROOM_HEIGHT*MESH + PADDING * 3 // 2))

    def handle_input(self):
        for event in pygame.event.get(KEYDOWN):
            if event.type == KEYDOWN:
                if event.key in DIR.keys():
                    if self.try_move(DIR[event.key], self.player):
                        break
                elif event.key in CREATE.keys():
                    self.create_mode = CREATE[event.key]
                    self.set_sample()
                elif event.key == K_s:
                    self.save()
                elif event.key == K_l:
                    self.load()
        for event in pygame.event.get(MOUSEBUTTONDOWN):
            pos = self.grid_pos(*pygame.mouse.get_pos())
            if self.in_bounds(pos):
                if event.button == MB_LEFT:
                    if self.create_mode == Player:
                        self.move_player(pos)
                    elif pos != self.player.pos:
                        self.create(pos)
                elif event.button == MB_RIGHT:
                    if pos != self.player.pos:
                        self.destroy(pos)

    def create(self, pos):
        obj = self.create_mode(pos)
        if obj.solid and self.get_solid(pos) is not None:
            return False
        self.put_obj(obj, pos)
        if obj.sticky:
            self.update_group(obj)
        return True

    def destroy(self, pos):
        obj = self.get_solid(pos)
        self.objmap[pos] = []
        # Reevaluate stickiness relations now that obj is "gone"
        if obj is not None and obj.sticky:
            group = obj.root.group - {obj}
            # Ensure everyone has a clean slate before rebuilding
            for child in group:
                child.root = child
                child.group = frozenset([child])
            for child in group:
                self.update_group(child)

    def set_sample(self):
        # An "object" at a fake position, not recorded on the grid
        self.sample = self.create_mode((-1, -1))

    def create_text(self):
        self.text = TextLines()
        self.text.color = BLACK
        self.text.font = FONT_MEDIUM
        self.text.height = 40
        self.text.add_line("Press S to Save and L to Load")
        self.text.add_line("ZXCVB change block type")
        self.text.add_line("Left/Right click to Create/Destroy")