from enum import IntEnum, auto

class StrType (IntEnum):
    GROUP = auto()
    SWITCH_LINK = auto()

    def __bytes__(self):
        return bytes([self])

class Structure:
    def __init__(self, str):
        self.str = str

    def activate(self):
        """Build the structure in the map"""
        pass

    def get_objs(self):
        pass

    def encode(self, data):
        return len(data).to_bytes(2, byteorder="little") + bytes(self.str) + data

class SwitchLink(Structure):
    def __init__(self, switch, gates):
        super().__init__(StrType.SWITCH_LINK)
        self.switch = switch
        self.gates = gates

    def activate(self):
        for gate in self.gates:
            self.switch.add_gate(gate)

    def get_objs(self):
        return self.gates + [self.switch]

    def __bytes__(self):
        # IF NOT BIGMAP
        data = [*self.switch.pos, self.switch.layer]
        for gate in self.gates:
            data.extend(gate.pos)
            data.append(gate.layer)
        return self.encode(bytes(data))