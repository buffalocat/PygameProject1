from enum import IntEnum, auto

class StrType (IntEnum):
    GROUP = auto()
    SWITCH_LINK = auto()

    def __bytes__(self):
        return bytes([self])

class Structure:
    def __init__(self, map, str):
        self.virtual = map is None
        self.map = map
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

    def __str__(self):
        return self.__class__.__name__

    def __bytes__(self):
        name = str(self)
        attrs = [name.encode(encoding="utf-8")]
        attrs += [pack_bytes(getattr(self, attrname), typename)
                  for attrname, typename in STR_TYPE[name]["args"]]
        sizes = bytes([len(attrs)] + [len(x) for x in attrs])
        return sizes + b"".join(attrs)


class SwitchLink(Structure):
    def __init__(self, map, switch, gates):
        self.switch = switch
        self.gates = gates
        super().__init__(map, StrType.SWITCH_LINK)

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


# Not actually implemented yet
class Group(Structure):
    def __init__(self, map, objs):
        super().__init__(map, StrType.SWITCH_LINK)
        self.objs = objs

    def get_objs(self):
        return self.objs

    def remove(self, str_list, obj):
        pass

    def __bytes__(self):
        data = []
        return self.encode(bytes(data))


STR_TYPE = {"SwitchLink":
                {"type": SwitchLink,
                 "args": []}}

def load_str_from_data(map_arg, objmap, str, data):
    if str == StrType.SWITCH_LINK:
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
        return SwitchLink(map_arg, switch, gates)
    else:
        return None

def pack_bytes(attr, typename):
    if typename == "color" or typename == "bool":
        return bytes(attr)
    elif typename == "obj":
        return bytes([*attr.pos, attr.layer])
    elif typename[-2:] == "[]":
        return bytes([len(attr)]) + b"".join(pack_bytes(x, typename[-2:]) for x in attr)