from enum import IntEnum, auto
from game_constants import RED

# It's rather important that this order is not changed...
# On the other hand, because so many structures can appear in a map
# I'd rather not write out the name in bytes every time
class StrType (IntEnum):
    DOOR = auto()
    SWITCH_LINK = auto()
    GROUP = auto()

    def __bytes__(self):
        return bytes([self])

class Structure:
    def __init__(self, state, strtype):
        self.state = state
        self.strtype = strtype

    def activate(self):
        """Build the structure in the map"""
        pass

    def get_objs(self):
        pass

    def encode(self, data):
        return len(data).to_bytes(2, byteorder="little") + bytes(self.strtype) + data

    # We need the room's list of structures, in case we have to
    # remove self from it, or add new ones during destruction
    def remove(self, str_list, obj):
        pass

    def update(self):
        pass

    def __str__(self):
        return self.__class__.__name__

    def __bytes__(self):
        attrs = [pack_bytes(getattr(self, attrname), typename)
                 for attrname, typename in STR_TYPE[self.strtype]["args"]]
        sizes = [self.strtype, len(attrs)] + [len(x) for x in attrs]
        return bytes(sizes) + b"".join(attrs)


class SwitchLink(Structure):
    def __init__(self, state, switches, gates, all, persistent):
        self.switches = switches
        self.gates = gates
        self.all = all
        self.persistent = persistent
        self.active = [False for _ in switches]
        self.n = len(switches)
        self.signal = False
        super().__init__(state, StrType.SWITCH_LINK)

    def activate(self):
        for switch in self.switches:
            switch.add_link(self)

    def set_signal(self, switch, signal):
        i = self.switches.index(switch)
        self.active[i] = signal

    def update(self):
        signal_before = self.signal
        if self.all:
            if all(self.active):
                self.signal = True
            elif not self.persistent:
                self.signal = False
        else:
            if any(self.active):
                self.signal = True
            elif not self.persistent:
                self.signal = False
        if self.signal != signal_before:
            self.state.delta.add_structure(self, signal_before)
            self.send_signal()

    def undo_delta(self, delta):
        """delta = bool signal"""
        self.signal = delta
        self.send_signal()

    def send_signal(self):
        for gate in self.gates:
            gate.set_signal(self.signal)

    def get_objs(self):
        return self.gates + self.switches

    def remove(self, str_list, obj):
        if obj is self.switches:
            i = self.switches.index(obj)
            del self.active[i]
            self.switches.remove(obj)
            self.n -= 1
        elif obj in self.gates:
            self.gates.remove(obj)
        if self.n == 0 or len(self.gates) == 0:
            str_list.remove(self)


# Doors are simple: one-way paths that the PLA YER can go through
class Door(Structure):
    def __init__(self, map, state, pos, dest_file, dest_pos):
        self.state = state
        self.pos = pos
        self.dest_file = dest_file
        self.dest_pos = dest_pos
        super().__init__(map, StrType.DOOR)

    def update(self):
        if self.state.player.pos in self.pos:
            self.state.try_room_change(self.dest_file, self.dest_pos)


STR_TYPE = {StrType.SWITCH_LINK:
                {"type": SwitchLink,
                 "args": [("switches", "obj[]"), ("gates", "obj[]"), ("all", "bool"), ("persistent", "bool")]}}


def load_str_from_data(state, strtype, attrs):
    arg_types = STR_TYPE[strtype]["args"]
    args = [unpack_bytes(attrs[i], state.objmap, arg_types[i][1]) for i in range(len(attrs))]
    return STR_TYPE[strtype]["type"](state, *args)


DATA_SIZE = {"bool": 1,
             "color": 3,
             "obj": 3}


def unpack_bytes(data, map, typename):
    if typename == "bool":
        return bool(data[0])
    elif typename == "color":
        return tuple(data)
    elif typename == "obj":
        return map[(data[0], data[1])][data[2]]
    elif typename[-2:] == "[]":
        element_type = typename[:-2]
        size = DATA_SIZE[element_type]
        return [unpack_bytes(data[size*i + 1 : size*(i+1) + 1], map, element_type) for i in range(data[0])]
    elif typename == "string":
        return data[1:].decode()


def pack_bytes(attr, typename):
    if typename == "bool":
        return bytes([int(attr)])
    elif typename == "color":
        return bytes(attr)
    elif typename == "obj":
        return bytes([*attr.pos, attr.layer])
    if typename[-2:] == "[]":
        return bytes([len(attr)]) + b"".join(pack_bytes(x, typename[:-2]) for x in attr)
    elif typename == "string":
        return bytes([len(attr)]) + attr.encode(encoding="utf-8")