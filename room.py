"""A room where players gather to play a game"""

# Online multiplayer doesn't work yet, but the
# rough idea is there.  For now, I'll just remove
# the option from the main menu and leave this as is.

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


class Signal(IntEnum):
    """Indicators of what kind of data is being passed between threads"""
    ERROR = 1
    ROOM_CODE = 2

    QUIT = 4

    KILL_LISTENER = 7

    NEW_CLIENT = 14
    NEW_PLAYER = 16
    TELL_ID = 18
    DISCONNECT = 20

    START_GAME = 32
    GAME_MOVE = 36

STR_SIGNALS = [Signal.ERROR,
               Signal.ROOM_CODE,
               Signal.KILL_LISTENER,
               Signal.NEW_PLAYER,
               Signal.NEW_CLIENT]

INT_SIGNALS = [Signal.TELL_ID,
               Signal.QUIT,
               Signal.START_GAME]

LIST_SIGNALS = [Signal.GAME_MOVE]


class GameID(IntEnum):
    """ID numbers for game types.  Must fit in one byte"""
    GO = 1


class Room:
    def __init__(self, state):
        self.state = state
        self.hosting = False
        self.listener_alive = False
        self.room_code = ""
        self.port = 0
        # id initializes to an invalid value
        # and must be set upon room creation/joining
        self.id = 255
        # the list of players is currently not very useful
        self.players = []
        # A list of (IP address, port) pairs we need to communicate with
        # If we're a guest, this just contains the host IP
        self.clients = []
        # This queue receives all requests
        self.connection_q = Queue()
        # This queue is how we kill our listener thread
        self.kill_q = Queue()

    # For now, player is just a string
    def add_player(self, player):
        self.players.append(player)

    def send_all(self, signal, message):
        """Relay a message to all clients"""
        total_message = self.join_message(signal, message)
        for x in self.clients:
            if x is not None:
                try:
                    s = socket.socket()
                    s.connect(x)
                    s.send(total_message)
                except ConnectionError:
                    self.dialog("Error", "Friend has disconnected.")

    def send(self, player_id, signal, message):
        total_message = self.join_message(signal, message)
        try:
            s = socket.socket()
            s.connect(self.clients[player_id])
            s.send(total_message)
        except ConnectionError:
            self.dialog("Error", "Friend has disconnected.")

    # This can surely be improved, but it'll work for now...
    def join_message(self, signal, message):
        if signal in STR_SIGNALS:
            return bytes([signal]) + message.encode()
        elif signal in INT_SIGNALS:
            return bytes([signal, message])
        elif signal in LIST_SIGNALS:
            # In this case, message is a list of ints as bytes
            return bytes([signal] + message)
        else:
            self.dialog("Error", "Not sure what to do with Signal (not categorized)")
            return b""

    def listen(self):
        self.listener = threading.Thread(target=listener_thread,
                                         args=(self.connection_q, self.kill_q))
        self.listener_alive = True
        self.listener.start()

    def host(self):
        """Begin hosting a new room"""
        self.hosting = True
        self.add_player("host")
        self.clients.append(None)
        self.id = 0
        self.listen()

    def connect(self, code):
        """Connect to an existing room"""
        self.room_code = code
        ip, port = room_decode(code)
        print(ip, port)
        self.clients.append((ip, port))
        self.listen()

    # Pretty much everything important goes in this method
    def check_q(self):
        if not self.connection_q.empty():
            signal, message = self.connection_q.get(block=False)
            if signal == Signal.ERROR:
                self.hosting = False
                self.dialog("Error", message)
            elif signal == Signal.ROOM_CODE:
                _, port = room_decode(message)
                self.port = port
                if self.hosting:
                    self.room_code = message
                else:
                    self.send_all(Signal.NEW_CLIENT, message)
            elif signal == Signal.NEW_CLIENT:
                ip, port = room_decode(message)
                self.clients.append((ip, port))
                for player in self.players:
                    self.send(-1, Signal.NEW_PLAYER, player)
                self.send(-1, Signal.TELL_ID, len(self.players))
                self.add_player("guest" + str(len(self.players)))
                self.send_all(Signal.NEW_PLAYER, self.players[-1])
            elif signal == Signal.NEW_PLAYER:
                self.add_player(message)
            elif signal == Signal.TELL_ID:
                self.id = int.from_bytes(message, byteorder="little")
            elif signal == Signal.QUIT:
                self.state.previous_state()
            elif signal == Signal.START_GAME:
                self.state.start_game()
            elif signal == Signal.GAME_MOVE:
                self.state.game.try_move(tuple(message))


    def start_signal(self):
        self.send_all(Signal.START_GAME, GameID.GO)

    def kill_thread(self):
        """"Stop the listener from listening and give it the kill signal"""
        if self.listener_alive:
            # Don't bother unless there's a thread to kill
            self.send_all(Signal.QUIT, self.id)
            self.kill_q.put(Signal.KILL_LISTENER)
            dummy = socket.socket()
            dummy.connect((socket.gethostname(), self.port))
            dummy.send(b"")
            self.hosting = False

    def dialog(self, info, message):
        tkinter.messagebox.showinfo(info, message)


def listener_thread(connection_q, kill_q):
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        port = DEFAULT_PORT
        success = False
        host = socket.gethostname()
        while not success and port < MAX_PORT:
            try:
                server.bind((host, port))
                success = True
            except OSError:
                port += 1
                success = False
        address = socket.getaddrinfo(host, port, socket.AF_INET6)
        ip = address[0][4][0]
        room_code = room_encode(ip, port)
        connection_q.put((Signal.ROOM_CODE, room_code))
        server.listen(5)
        while True:
            c, address = server.accept()
            total_message = c.recv(SOCKET_BUFFER_SIZE)
            # There is really no need to check WHAT is on the kill queue
            if not kill_q.empty():
                if kill_q.get(block=False) == Signal.KILL_LISTENER:
                    break
            c.close()
            signal, message = Signal(total_message[0]), total_message[1:]
            if signal in STR_SIGNALS:
                connection_q.put((Signal(signal), message.decode()))
            else:
                connection_q.put((Signal(signal), message))
    except OSError:
        connection_q.put((Signal.ERROR, "Failed to find an available port."))
    server.close()


# These are some very simple encoding functions, so you don't
# have to send your friends your "raw IP address"
# (It's not meant to be a "security" measure, really)
def ipv4_to_num(ip):
    ip_parts = map(int, ip.split("."))
    ip_num = 0
    for x in ip_parts:
        ip_num <<= 8
        ip_num += x
    return ip_num

def num_to_ipv4(n):
    ip_parts = []
    for _ in range(4):
        ip_parts.append(str(n % 256))
        n >>= 8
    return ".".join(ip_parts[::-1])

def ipv6_to_num(ip):
    ip_parts = ip.split(":")
    print(ip, ip_parts)
    ip_num = 0
    for x in ip_parts:
        ip_num <<= 16
        ip_num += int("0x" + x, 16)
    return ip_num

def num_to_ipv6(n):
    ip_parts = []
    for _ in range(4):
        ip_parts.append(hex(n % (1 << 16))[2:])
        n >>= 16
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


def room_encode(ip, port):
    # dummy version
    return ip + "_" + str(port)
    #return num_to_alpha(add_noise(ipv6_to_num(ip))) + num_to_alpha(port)


def room_decode(s):
    # dummy version
    first, second = s.split("_")
    return first, int(second)
    #first, second = s[:-3], s[-3:]
    #return num_to_ipv6(remove_noise(alpha_to_num(first))), alpha_to_num(second)