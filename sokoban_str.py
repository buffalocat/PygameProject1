from enum import IntEnum, auto

class StrType (IntEnum):
    GROUP = auto()
    SWITCH_LINK = auto()

    def __bytes__(self):
        return bytes([self])

class Structure:
    def __init__(self, map, str):
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
    def destroy(self, str_list, obj):
        pass

    def __str__(self):
        return self.__class__.__name__

class SwitchLink(Structure):
    def __init__(self, map, switch, gates):
        super().__init__(map, StrType.SWITCH_LINK)
        self.switch = switch
        self.gates = gates

    def activate(self):
        for gate in self.gates:
            self.switch.add_gate(gate)

    def get_objs(self):
        return self.gates + [self.switch]

    def destroy(self, str_list, obj):
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

    def destroy(self, str_list, obj):
        pass

    def __bytes__(self):
        data = []
        return self.encode(bytes(data))