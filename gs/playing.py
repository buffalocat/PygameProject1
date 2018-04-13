import pygame
from enum import IntEnum

from game_constants import *
from game_state import GameState
from room import Signal


class GSPlaying(GameState):
    def __init__(self, mgr, parent, room, game):
        super().__init__(mgr, parent)
        self.root.set_color(LIGHT_BROWN)
        self.room = room
        self.room.state = self
        self.game = game(self)
        self.players = [Go.BLACK, Go.WHITE]

    def handle_input(self):
        if self.game.color == self.players[self.room.id]:
            self.game.handle_input()

    def update(self):
        super().update()
        self.room.check_q()

    def draw(self):
        super().draw()
        self.game.draw_board(self.surf)

    def quit(self):
        self.room.state = self.parent

    def send_move(self, move):
        self.room.send_all(Signal.GAME_MOVE, list(move))



class Game:
    def __init__(self, state):
        self.state = state



# The number of spots on a side of the (square) board
BOARD_SIZE = 9
# Half the size of a spot on the board
HALF_MESH = 30
# Radius of a piece
PIECE_SIZE = HALF_MESH - 3
# How thick the board lines are
LINE_WIDTH = 3

ADJ = [(1, 0), (0, 1), (-1, 0), (0, -1)]


class Go(IntEnum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2
    INVALID = 3

class GoGame(Game):
    def __init__(self, state):
        super().__init__(state)
        self.board_init(BOARD_SIZE)
        self.color = Go.BLACK

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                pos = self.mouse_pos(event.pos)
                if pos is not None:
                    if event.button == MB_LEFT:
                        self.try_move(pos)

    def try_move(self, pos):
        self.state.send_move(pos)
        new = self.board[pos]
        if new.color == Go.EMPTY:
            x, y = pos
            # Is this move allowed?
            legal = False
            # Do we have to join any pieces to this piece?
            join = []
            # Do we have to remove a liberty from any adjacent pieces?
            threat = []
            for dx, dy in ADJ:
                cur = self.board[(x+dx, y+dy)].root
                if cur.color == Go.EMPTY:
                    legal = True
                    new.liberties.add(cur.pos)
                elif cur.color == self.color:
                    if len(cur.liberties) > 1:
                        legal = True
                    join.append(cur)
                elif cur.color == self.opp_color():
                    if len(cur.liberties) == 1:
                        legal = True
                    threat.append(cur)
            if legal:
                new.color = self.color
                for piece in join:
                    new.adopt(piece.root)
                for piece in threat:
                    new.threaten(piece.root, self.board)
                self.board[pos] = new
                self.color = self.opp_color()
            else:
                # We may have given this space "liberties" even if it was an illegal move
                new.liberties = set()

    def opp_color(self):
        if self.color == Go.BLACK:
            return Go.WHITE
        else:
            return Go.BLACK

    def board_init(self, size):
        self.board = {}
        # We're not worrying about ko for now
        #self.board_states = []
        #self.board_hashes = []
        for x in range(-1, size + 1):
            for y in range(-1, size + 1):
                if 0 <= x < size and 0 <= y < size:
                    self.board[(x,y)] = Region(Go.EMPTY, (x, y))
                else:
                    self.board[(x,y)] = Region(Go.INVALID, (x, y))

    def board_to_int(self):
        """Compactly represent the board as an int"""
        pass

    def pos(self, x, y):
        """Convert board coordinates to pixels"""
        return (HALF_MESH * (1 + 2*x), HALF_MESH * (1 + 2*y))

    def mouse_pos(self, mpos):
        """Find the board position closest to a pixel position"""
        mx, my = mpos
        x = mx // (2 * HALF_MESH)
        y = my // (2 * HALF_MESH)
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            return (x, y)
        else:
            return None

    def draw_board(self, surf):
        for i in range(BOARD_SIZE):
            pygame.draw.line(surf, BLACK, self.pos(i, 0), self.pos(i, BOARD_SIZE - 1), LINE_WIDTH)
            pygame.draw.line(surf, BLACK, self.pos(0, i), self.pos(BOARD_SIZE - 1, i), LINE_WIDTH)
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                ishi = self.board[(x,y)].color
                if ishi == Go.BLACK:
                    pygame.draw.circle(surf, BLACK, self.pos(x, y), PIECE_SIZE)
                elif ishi == Go.WHITE:
                    pygame.draw.circle(surf, WHITE, self.pos(x, y), PIECE_SIZE)


class Region:
    def __init__(self, color, pos=None):
        self.reset()
        self.color = color
        self.pos = pos

    def reset(self):
        # When reset is used later, "empty" is the default state
        self.color = Go.EMPTY
        # root is an arbitrary "representative" point of the region
        self.root = self
        self.children = {self}
        self.liberties = set()

    def adopt(self, piece):
        piece.liberties -= {self.pos}
        self.children |= piece.children
        self.liberties |= piece.liberties
        for child in piece.children:
            child.root = self

    def threaten(self, piece, board):
        piece.liberties -= {self.pos}
        if not piece.liberties:
            piece.eliminate(board)

    def eliminate(self, board):
        if self.color == Go.BLACK:
            opp = Go.WHITE
        else:
            opp = Go.BLACK
        # We will end up modifying self.children during this loop
        # But we're just setting it to a new set, which doesn't alter the one we're looping over
        for child in self.children:
            child.free_adj(board, opp)
            child.reset()

    def free_adj(self, board, color):
        x, y = self.pos
        for dx, dy in ADJ:
            cur = board[(x + dx, y + dy)].root
            if cur.color == color:
                cur.liberties.add(self.pos)

    def print(self):
        print(f"Has children {list(x.pos for x in self.children)}\n"
              f"Liberties at {list(x for x in self.liberties)}\n\n")