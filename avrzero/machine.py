from avrzero import BYTE_SIZE
from avrzero.error import AVRMachineError
from avrzero.instruction import InstructionSet
from avrzero.register import Register, PointerRegister, StatusRegister
from avrzero.variable import IntVar


class Machine:

    def __init__(self, RAMEND=0xFFFF, flash_size=0x10000,
                 instruction_set=InstructionSet.default, win=None):
        # === Data Memory ===
        self.RAMEND = RAMEND
        self.memory = []
        for addr in range(32):
            self.memory.append(Register(name=f"R{addr}", addr=addr, win=win))
        for addr in range(32, RAMEND + 1):
            self.memory.append(Register(addr=addr, win=win))

        # general purpose registers
        self.R = self.general_registers = self.memory[0x00:0x20]
        self.X = PointerRegister("X", self.memory[27:25:-1])
        self.Y = PointerRegister("Y", self.memory[29:27:-1])
        self.Z = PointerRegister("Z", self.memory[31:29:-1])

        # I/O registers
        self.IOR = self.io_registers = self.memory[0x20:0x60]
        self.SP = PointerRegister("stack pointer", self.memory[0x5E:0x5C:-1])
        self.SREG = StatusRegister.from_(self.memory[0x5F])

        # extended I/O registers
        self.EIOR = self.ext_io_registers = self.memory[0x0060:0x0100]

        # === Program Memory ===
        self.flash_size = flash_size
        self.flash = [IntVar(win, 0x0000) for _ in range(self.flash_size)]

        self.PC = PointerRegister("program counter", (Register(), Register()))

        # === Instruction Set ===
        self.instruction_set = instruction_set

        # === Reset ===
        self.reset()

    def __repr__(self):
        return "\n".join((
            f"Machine(RAMEND={self.RAMEND},",
            f"        flash_size={self.flash_size},",
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

    def _push_stack(self, val):
        self.SP.val -= 1
        self.memory[self.SP.val].val = val

    def _pop_stack(self):
        val = self.memory[self.SP.val].val
        self.SP.val += 1
        return val

    def push_stack(self, val, n_byte=1):
        for _ in range(n_byte):
            self._push_stack(val & ((1 << BYTE_SIZE) - 1))
            val >>= BYTE_SIZE

    def pop_stack(self, n_byte=1):
        val = 0
        for _ in range(n_byte):
            val <<= BYTE_SIZE
            val |= self._pop_stack()

        return val

    def reset(self):
        self.SP.val = self.RAMEND
        self.PC.val = 0x0000

    def load_program(self, program):
        program = program[:self.flash_size]
        for i in range(len(program)):
            self.flash[i].set(program[i])
        for i in range(len(program), self.flash_size):
            self.flash[i].set(0)

    def step(self):
        opcode = [*map(IntVar.get, self.flash[self.PC.val:self.PC.val + 1])]
        instruction = self.instruction_set.by_opcode(opcode)
        if instruction is None:
            opcode = [*map(IntVar.get, self.flash[self.PC.val:self.PC.val + 2])]
            instruction = self.instruction_set.by_opcode(opcode)
        if instruction is None:
            return
        operand_map = instruction.opcode.get_operand_map(opcode)
        instruction.action(self, **operand_map)
