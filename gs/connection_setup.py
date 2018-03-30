"""A menu state for setting up a connection with a friend"""
from enum import Enum
from  tkinter import messagebox
import tkinter
from queue import Queue
import threading
import socket

import pygame

from font import FONT_MEDIUM
from game_constants import *
from game_state import GameState, Menu, Panel, TextLines

from random import random  #delete later
from time import sleep  #delete later


class Signal(Enum):
    """Indicators of what kind of data is being passed between threads"""
    ERROR = 0
    INT_IP = 1
    INT_PORT = 2
    EXT_MESSAGE = 3
    CLOSE = 4
    ERROR_PORT = 5


class GSConnectionSetup(GameState):
    def __init__(self, mgr, parent):
        super().__init__(mgr, parent)
        self.bg = RED
        self.menu = ConnectionSetupMenu(self)
        self.room_code = ""
        self.port = 0
        self.connection_q = Queue()
        self.kill_q = Queue()
        self.hosting = False

    def update(self):
        self.menu.update()
        pygame.event.clear()
        self.check_q()

    def draw(self, surf):
        self.surf.fill(self.bg)
        self.menu.draw(self.surf, (10, 10))
        super().draw(surf)

    def quit(self):
        self.kill_thread()


    def show_room_info(self):
        if self.room_code == "":
            self.dialog("Room Info", "The room has not been set up.\n"
                        "Either Host a room or Connect to someone else's.")
        else:
            self.dialog("Room Info", f"Room Code: {self.room_code}\n"
                                     f"Port: {self.port}")

    def check_q(self):
        while not self.connection_q.empty():
            signal, message = self.connection_q.get(block=False)
            if signal == Signal.ERROR_PORT:
                self.hosting = False
                self.dialog("Error", message)
            elif signal == Signal.INT_IP:
                self.room_code = ip_encode(message.decode())
            elif signal == Signal.INT_PORT:
                self.port = message

    def host_room(self):
        """Become the host of a room"""
        if self.hosting:
            self.dialog("Error", "You're already hosting a room.\n"
                        "You can back out to the main menu to stop.")
        else:
            self.hosting = True
            thread = threading.Thread(target=listener_thread,
                                      args=(self.connection_q, self.kill_q))
            thread.start()

    def connect_to_room(self):
        if self.hosting:
            self.dialog("Error", "You're already hosting a room.\n"
                        "You can back out to the main menu to stop.")
        else:
            self.dialog("Error", "This isn't implemented yet lol")

    def kill_thread(self):
        """"Stop the listener from listening and give it the kill signal"""
        if self.hosting:
            # Don't bother unless there's a thread to kill
            self.kill_q.put(Signal.CLOSE)
            dummy = socket.socket()
            dummy.connect((socket.gethostname(), DEFAULT_PORT))
            dummy.send(b"")
            self.hosting = False

    def dialog(self, info, message):
        tkinter.messagebox.showinfo(info, message)


def listener_thread(connection_q, kill_q):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((socket.gethostname(), DEFAULT_PORT))
        ip, port = server.getsockname()
        connection_q.put((Signal.INT_IP, ip.encode()))
        connection_q.put((Signal.INT_PORT, port))
        server.listen(1)
        while True:
            c, address = server.accept()
            message = c.recv(SOCKET_BUFFER_SIZE).decode()
            # There is really no need to check WHAT is on the kill queue
            if not kill_q.empty():
                if kill_q.get(block=False) == Signal.CLOSE:
                    break
            c.close()
            connection_q.put((Signal.EXT_MESSAGE, message))
    except OSError:
        connection_q.put((Signal.ERROR_PORT, "The port is already in use."))
    server.close()

class ConnectionSetupMenu(Menu):
    def __init__(self, parent):
        super().__init__(parent)
        self.add_item("Host Room", "host_room")
        self.add_item("Show Room Status", "show_room_info")
        self.add_item("Connect To Room", "connect_to_room")
        self.add_item("Return to Menu", "mgr.previous_state")
        self.color_def = NAVY_BLUE
        self.color_high = GOLD
        self.height = 40
        self.font = FONT_MEDIUM


# These are some very simple encoding functions, so you don't
# have to send your friends your "raw IP address"
# (It's not meant to be a "security" measure, really)
def ip_to_num(ip):
    ip_parts = map(int, ip.split("."))
    ip_num = 0
    for x in ip_parts:
        ip_num <<= 8
        ip_num += x
    return ip_num

def num_to_ip(n):
    ip_parts = []
    for _ in range(4):
        ip_parts.append(str(n % 256))
        n >>= 8
    return ".".join(ip_parts[::-1])

def num_to_alpha(n):
    chars = []
    while n:
        chars += chr((n % 26) + 65)
        n //= 26
    return "".join(chars)

def alpha_to_num(s):
    n = 0
    for c in s[::-1]:
        n *= 26
        n += ord(c) - 65
    return n

def ip_encode(ip):
    return num_to_alpha(ip_to_num(ip))