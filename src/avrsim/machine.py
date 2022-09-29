from avrsim.register import Register, PointerRegister, StatusRegister


class Machine:

    def __init__(self, RAMEND=0xFFFF, flash_size=0x10000,
                 instruction_set=InstructionSet.default):
        # === Data Memory ===
        self.RAMEND = RAMEND
        self.registers = [Register(addr) for addr in range(RAMEND + 1)]

        # general purpose registers
        self.R = self.general_registers = self.registers[0x00:0x20]
        self.X = PointerRegister(self.registers[27:25:-1])
        self.Y = PointerRegister(self.registers[29:27:-1])
        self.Z = PointerRegister(self.registers[31:29:-1])

        # I/O registers
        self.IOR = self.io_registers = self.registers[0x20:0x60]
        self.SP = PointerRegister(self.registers[0x5E:0x5C:-1])
        self.SREG = StatusRegister.from_(self.registers[0x5F])

        # extended I/O registers
        self.EIOR = self.ext_io_registers = self.registers[0x0060:0x0100]

        # === Program Memory ===
        self.flash_size = flash_size
        self.flash = [0x00] * flash_size

        self.PC = PointerRegister((Register(), Register()))

        # === Instruction Set ===
        self.instruction_set = instruction_set

        # === Reset ===
        self.reset()

    def __repr__(self):
        return "\n".join((
            f"Machine(RAMEND={self.RAMEND},",
            f"        flash_size={self.flash_size},"
            f"        instruction_set={self.instruction_set!r})"))

    def __str__(self):
        lines = ["=" * 80]
        lines.extend(map(str, self.R))
        lines.append(f"{self.SREG} SREG")
        lines.append(f"{self.X} X")
        lines.append(f"{self.Y} Y")
        lines.append(f"{self.Z} Z")
        lines.append("=" * 80)
        return "\n".join(lines)

    def reset(self):
        self.SP.val = self.RAMEND
        self.PC.val = 0

    def load_program(self, program):
        self.flash = [0] * len(self.flash)
        program = program[:len(self.flash)]
        self.flash[:len(program)] = program
