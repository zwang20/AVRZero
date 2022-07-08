from register import Register, PointerRegister, StatusRegister


class Machine:

    def __init__(self, RAMEND=0xFFFF):
        self.RAMEND = RAMEND
        self.registers = [Register(addr) for addr in range(RAMEND)]

        self.PC = PointerRegister((Register(None), Register(None)))

        # general purpose registers
        self.R = self.general_registers = self.registers[0x00:0x20]
        self.X = PointerRegister(self.registers[27:25:-1])
        self.Y = PointerRegister(self.registers[29:27:-1])
        self.Z = PointerRegister(self.registers[31:29:-1])

        # I/O registers
        self.IOR = self.io_registers = self.registers[0x20:0x60]
        self.SP = PointerRegister(self.registers[0x5E:0x5C:-1])
        self.SREG = StatusRegister.from_(self.registers[0x5F])

        # Extended I/O registers
        self.ext_io = self.registers[0x0060:0x0100]

    def __str__(self):
        lines = []
        lines.append("=" * 80)
        lines.extend(map(str, self.R))
        lines.append(f"{self.SREG} SREG")
        lines.append("=" * 80)
        return "\n".join(lines)

