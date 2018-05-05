from enum import IntEnum, auto

# It's rather important that this order is not changed...
# On the other hand, because so many structures can appear in a map
# I'd rather not write out the name in bytes every time
class StrType (IntEnum):
    GROUP = auto()
    SINGLE_SWITCH_LINK = auto()
    DOOR = auto()
    MULTI_SWITCH_LINK = auto()

    def __bytes__(self):
        return bytes([self])

class Structure:
    def __init__(self, state, str):
        self.state = state
        self.str = str

    def activate(self):
        """Build the structure in the map"""
        pass

    def get_objs(self):
        pass

    def encode(self, data):
        return len(data).to_bytes(2, byteorder="little") + bytes(self.str) + data

    # We need the room's list of structures, in case we have to
    # remove self from it, or add new ones during destruction
    def remove(self, str_list, obj):
        pass

    def update(self):
        pass

    def __str__(self):
        return self.__class__.__name__

    def __bytes__(self):
        name = str(self)
        attrs = [name.encode(encoding="utf-8")]
        attrs += [pack_bytes(getattr(self, attrname), typename)
                  for attrname, typename in STR_TYPE[name]["args"]]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)


class SingleSwitchLink(Structure):
    def __init__(self, map, switch, gates):
        self.switch = switch
        self.gates = gates
        super().__init__(map, StrType.SINGLE_SWITCH_LINK)

    def activate(self):
        for gate in self.gates:
            self.switch.add_link(gate)

    def get_objs(self):
        return self.gates + [self.switch]

    def remove(self, str_list, obj):
        if obj is self.switch:
            str_list.remove(self)
        elif obj in self.gates:
            self.gates.remove(obj)

    def __bytes__(self):
        # IF NOT BIGMAP
        data = [*self.switch.pos, self.switch.layer]
        for gate in self.gates:
            data.extend(gate.pos)
            data.append(gate.layer)
        return self.encode(bytes(data))

class MultiSwitchLink(Structure):
    def __init__(self, map, switches, gates, all, persistent):
        self.switches = switches
        self.active = [False for _ in switches]
        self.n = len(switches)
        self.all = all
        self.persistent = persistent
        self.signal = False
        self.gates = gates
        super().__init__(map, StrType.MULTI_SWITCH_LINK)

    def activate(self):
        for switch in self.switches:
            switch.add_link(self)

    def set_signal(self, switch, signal):
        i = self.switches.index(switch)
        self.active[i] = signal

    def update(self):
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
        self.send_signal()

    def send_signal(self):
        for gate in self.gates:
            gate.set_signal(self, self.signal)

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

    def __bytes__(self):
        # IF NOT BIGMAP
        data = [int(self.all), len(self.switches), int(self.persistent)]
        for switch in self.switches:
            data.extend(switch.pos)
            data.append(switch.layer)
        for gate in self.gates:
            data.extend(gate.pos)
            data.append(gate.layer)
        return self.encode(bytes(data))

# Doors are simple: one-way paths that the PLAYER can go through
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


STR_TYPE = {"SwitchLink":
                {"type": SingleSwitchLink,
                 "args": []}}

def load_str_from_data(map_arg, objmap, str, data):
    if str == StrType.SINGLE_SWITCH_LINK:
        switch = None
        gates = []
        # IF NOT BIGMAP
        for i in range(len(data) // 3):
            pos = tuple(data[3 * i:3 * i + 2])
            layer = data[3 * i + 2]
            if i == 0:
                switch = objmap[pos][layer]
            else:
                gates.append(objmap[pos][layer])
        return SingleSwitchLink(map_arg, switch, gates)
    elif str == StrType.MULTI_SWITCH_LINK:
        all = bool(data[0])
        persistent = bool(data[2])
        switches = []
        gates = []
        n_switches = data[1]
        # IF NOT BIGMAP
        for i in range(1, len(data) // 3):
            pos = tuple(data[3 * i:3 * i + 2])
            layer = data[3 * i + 2]
            if i <= n_switches:
                switches.append(objmap[pos][layer])
            else:
                gates.append(objmap[pos][layer])
        return MultiSwitchLink(map_arg, switches, gates, all, persistent)
    else:
        return None

def pack_bytes(attr, typename):
    if typename == "bool":
        return bytes(int(attr))
    elif typename == "color":
        return bytes(attr)
    elif typename == "obj":
        return bytes([*attr.pos, attr.layer])
    elif typename[-2:] == "[]":
        return bytes([len(attr)]) + b"".join(pack_bytes(x, typename[-2:]) for x in attr)