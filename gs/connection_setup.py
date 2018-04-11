"""A menu state for setting up a connection with a friend"""
from  tkinter import messagebox
import tkinter

from font import FONT_MEDIUM
from game_constants import *
from game_state import GameState
from gs.playing import GSPlaying, Game
from room import Room
from widget import Panel, Menu, TextLines


class GSConnectionSetup(GameState):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.root.set_color(RED)
        self.root.add(ConnectionSetupMenu(self, (10, 10)))
        self.room = Room()

    def update(self):
        super().update()
        self.room.check_q()

    def quit(self):
        self.room.kill_thread()

    def show_room_info(self):
        if self.room.room_code == "":
            self.dialog("Room Info", "The room has not been set up.\n"
                        "Either Host a room or Connect to someone else's.")
        else:
            self.dialog("Room Info", f"Room Code: {self.room.room_code}\n"
                                     f"Port: {self.room.port}")

    def copy_room_code(self):
        if self.room.room_code == "":
            self.dialog("Error", "Please host or connect to a room first")
        else:
            self.mgr.root.clipboard_clear()
            self.mgr.root.clipboard_append(self.room.room_code)

    def play_go(self):
        GSPlaying(self.mgr, self, self.room, Game())

    def host_room(self):
        """Become the host of a room"""
        if self.room.hosting:
            self.dialog("Error", "You're already hosting a room.\n"
                        "You can back out to the main menu to stop.")
        else:
            self.room.hosting = True
            self.room.listen()

    def connect_to_room(self):
        if self.room.hosting:
            self.dialog("Error", "You're already hosting a room.\n"
                        "You can back out to the main menu to stop.")
        else:
            self.dialog("Error", "This isn't implemented yet lol")

    def dialog(self, info, message):
        tkinter.messagebox.showinfo(info, message)

class ConnectionSetupMenu(Menu):
    def __init__(self, parent, pos):
        super().__init__(parent, pos)
        self.add_item("Host Room", "host_room")
        self.add_item("Show Room Status", "show_room_info")
        self.add_item("Copy Room Code to Clipboard", "copy_room_code")
        self.add_item("Connect To Room (Paste from Clipboard)", "connect_to_room")
        self.add_item("Begin Game (Go)", "play_go")
        self.add_item("Return to Menu", "previous_state")
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 40
        self.font = FONT_MEDIUM