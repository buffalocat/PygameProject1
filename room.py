import random
import socket
import threading
import tkinter.messagebox
from enum import IntEnum
from queue import Queue

from game_constants import *

# Requirements:
# each Signal is an int between 0 and 255
# and is to be sent as the first byte of any message
# messages below a certain index are designated as "internal"
# "external" messages are relayed to all clients

INTERNAL = 8

class Signal(IntEnum):
    """Indicators of what kind of data is being passed between threads"""
    ERROR = 0
    INT_IP = 1
    INT_PORT = 2
    EXT_MESSAGE = 3
    CLOSE = 4
    ERROR_PORT = 5

class Room:
    def __init__(self):
        self.hosting = False
        self.room_code = ""
        self.port = 0
        self.players = []
        # A list of (IP address, port) pairs we need to communicate with
        # If we're a guest, this just contains the host IP
        self.clients = []
        # This queue receives all requests
        self.connection_q = Queue()
        # This queue is how we kill our listener thread
        self.kill_q = Queue()

    def add_player(self, player):
        self.players.append(player)
        if player.ip is not None and player.ip not in self.clients:
            self.clients.append(player.ip)

    def send(self, message):
        for address, port in self.clients:
            s = socket.socket()
            s.connect(())

    def listen(self):
        thread = threading.Thread(target=listener_thread,
                                  args=(self.connection_q, self.kill_q))
        thread.start()

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
        port = DEFAULT_PORT
        success = False
        while not success and port < MAX_PORT:
            try:
                server.bind((socket.gethostname(), port))
                success = True
            except OSError:
                port += 1
                success = False
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
        connection_q.put((Signal.ERROR_PORT, "Failed to find an available port."))
    server.close()


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


# Let's add in some noise, essentially a "session password"
# It also reverses the bits! But remove_noise unreverses them!
def add_noise(a):
    b = 0
    while a:
        b <<= 1
        if random.random() > 0.5:
            b += 1
        b <<= 1
        b += a & 1
        a >>= 1
    return b


def remove_noise(b):
    a = 0
    while b:
        a <<= 1
        a += b & 1
        b >>= 2
    return a


def ip_encode(ip):
    return num_to_alpha(add_noise(ip_to_num(ip)))


def ip_decode(s):
    return num_to_ip(remove_noise(alpha_to_num(s)))