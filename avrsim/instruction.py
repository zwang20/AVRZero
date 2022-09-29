from functools import cache, cached_property

from avrsim.error import AVRSyntaxError


BYTE_SIZE = 8


class Syntax:

    def __init__(self, tokens):
        self._tokens = tokens

    def __str__(self):
        string = ""
        for token in self._tokens:
            if isinstance(token, str):
                string += token
            else:
                string += token.name

        return string

    def match(self, string):
        operand_map = {}
        for token in self._tokens:
            if isinstance(token, Operand):
                num_str = ""
                while string and string[0].isdigit():
                    num_str += string[0]
                    string = string[1:]
                if not num_str:
                    raise AVRSyntaxError("expect digits")
                operand_map[token.name] = int(num_str)
            elif token == " ":
                if not string or not string[0].isspace():
                    return AVRSyntaxError("expect space")
                string = string.lstrip()
            else:
                if not string.lower().startswith(token.lower()):
                    return AVRSyntaxError(f"expect {token}")
                string = string[len(token):]

        return operand_map

    @classmethod
    def parse(cls, string, operands):
        tokens = []
        token = ""
        for char in string:
            if char.isupper():
                token += char
            elif char.islower() or char.isspace() or char == ",":
                if token:
                    tokens.append(token)
                    token = ""
                if char.islower():
                    for operand in operands:
                        if operand.name == char:
                            tokens.append(operand)
                if char.isspace():
                    tokens.append(" ")
                elif char == ",":
                    tokens.append(",")
            else:
                raise ValueError("invalid character in syntax")

        return cls(tokens)


class Operand:

    def __init__(self, name, choices):
        if not isinstance(name, str):
            raise TypeError("invalid type for name, expect str")
        if isinstance(choices, range):
            if choices.step != 1:
                raise ValueError("invalid step for choices, expect 1")
        elif isinstance(choices, set):
            if not all(isinstance(choice, int) for choice in choices):
                raise TypeError("invalid type for an item in choices, "
                                "expect int")
        else:
            raise TypeError("invalid type for choices, expect set of int")
        self._name = name
        self._choices = choices

    @property
    def name(self):
        return self._name

    @property
    def choices(self):
        return tuple(*self._choices)

    def __str__(self):
        name = self._name
        choices = self._choices
        if isinstance(choices, range):
            return f"{choices.start} <= {name} < {choices.stop}"
        elif isinstance(choices, set):
            return f"{name} ∈ {set}"

    def check(self, value):
        return value in self._choices


class Opcode:

    def __init__(self, opcode_str):
        if not isinstance(opcode_str, str):
            raise TypeError("invalid type for operand str, expect str")
        if len(opcode_str) % BYTE_SIZE:
            raise ValueError("invalid length for operand str, "
                             f"expect multiple of {BYTE_SIZE}")
        self._str = opcode_str

    def __str__(self):
        return self._str

    @cached_property
    def operand_names(self):
        return set(self._str) - {"0", "1"}

    @cached_property
    def n_bits(self):
        return len(self._str)

    @cached_property
    def fixed_mask(self):
        return self.binary_mask(self._str, "01")

    @cached_property
    def fixed(self):
        return self.binary_mask(self._str, "1")

    @cache
    def mask_char(self, char):
        return self.binary_mask(self._str, char)

    def map_operands(self, operand_map):
        mapped = self.fixed
        for key, val in operand_map.items():
            mapped |= self.map_int(val, self.mask_char(key))

        codes = []
        for _ in range(self.n_bits // BYTE_SIZE):
            codes.insert(0, mapped & ((1 << BYTE_SIZE) - 1))
            mapped >>= BYTE_SIZE
        return codes

    @staticmethod
    def binary_mask(code, select):
        mask = 0
        for i, bit in enumerate(code[::-1]):
            if bit in select:
                mask |= 1 << i

        return mask

    @staticmethod
    def map_int(integer, mask):
        mapped = 0
        weight = 0
        while mask:
            if mask % 2:
                mapped |= (integer % 2) << weight
                integer //= 2
            mask //= 2
            weight += 1

        return mapped

    @classmethod
    def parse(cls, opcode_str, operands):
        opcode = cls(opcode_str)
        return opcode


class Instruction:

    def __init__(self, action, syntax, operands, opcode):
        if not callable(action):
            raise TypeError("invalid type for action, expect callable")
        if not isinstance(syntax, Syntax):
            raise TypeError("invalid type for syntax, expect Syntax")
        if not isinstance(operands, tuple):
            raise TypeError("invalid type for operands, expect tuple")
        if not all(isinstance(operand, Operand) for operand in operands):
            raise TypeError("invalid type for an item of operands, "
                            "expect Operand")
        if not isinstance(opcode, Opcode):
            raise TypeError("invalid type for opcode, expect Opcode")

        self._action = action
        self._syntax = syntax
        self._operands = operands
        self._opcode = opcode

    def __str__(self):
        return "\n".join((
            "Instruction " + self.name,
            f"\tSyntax: {self.syntax}",
            f"\tOperands: {', '.join(map(str, self._operands))}",
            f"\tOpcode: {self.opcode}"))

    @property
    def action(self):
        return self._action

    @property
    def syntax(self):
        return self._syntax

    @property
    def operands(self):
        return self._operands

    @property
    def opcode(self):
        return self._opcode

    @cached_property
    def name(self):
        return self._action.__qualname__

    def str_to_opcode(self, string):
        operand_map = self._syntax.match(string)
        for operand in self._operands:
            if not operand.check(operand_map[operand.name]):
                raise AVRSyntaxError("invalid operand")

        return self._opcode.map_operands(operand_map)

    @classmethod
    def make(cls, syntax, operands, opcode, belong_to=None):
        def decorator(action):
            instruction = cls(action,
                              Syntax.parse(syntax, operands),
                              operands,
                              Opcode.parse(opcode, operands))
            if belong_to is None:
                InstructionSet.default.add(instruction)
            else:
                belong_to.add(instruction)

            return instruction

        return decorator


class InstructionSet:

    default = None

    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError("invalid type for name, expect str")
        self._name = name
        self._instructions = ()

    def __str__(self):
        string = "Instruction Set " + self._name + "\n"
        string += "\tInstructions: " + ", ".join(
            instruction.name for instruction in self._instructions)
        return string

    def add(self, instruction):
        self._instructions = self._instructions + (instruction,)

    def by_name(self, name):
        for instruction in self._instructions:
            if instruction.name.casefold() == name.casefold():
                return instruction

    def by_opcode(self, codes):
        opcode = 0
        for code in codes:
            opcode <<= BYTE_SIZE
            opcode |= code
        for instruction in self._instructions:
            if instruction.opcode.fixed_mask & opcode == \
                    instruction.opcode.fixed:
                return instruction


InstructionSet.default = InstructionSet("default")


@Instruction.make(
    syntax="ADC Rd, Rr",
    operands=(Operand("d", range(0, 32)),
              Operand("r", range(0, 32))),
    opcode="0001" "11rd" "dddd" "rrrr"
)
def adc(machine, d, r):
    Rd, Rr = machine.R[d], machine.R[r]
    SREG = machine.SREG

    val = Rd.val + Rr.val + SREG.C
    SREG.H = Rd[3] and Rr[3] or Rr[3] and not R[3] and not R[3] and Rd[3]
    SREG.V = Rd[7] and Rr[7] and not R[7] or not Rd[7] and not Rr[7] and R[7]
    SREG.S = SREG.N ^ SREG.V
    SREG.N = R[7]
    SREG.Z = not R
    SREG.C = Rd[7] and Rr[7] or Rr[7] and not R[7] or not R[7] and Rd[7]
    Rd.val = val


@Instruction.make(
    syntax="BCLR s",
    operands=(Operand("s", range(0, 8)),),
    opcode="1001" "0100" "1sss" "1000"
)
def bclr(machine, s):
    machine.SREG[s] = 0

@Instruction.make(
    syntax="CALL k",
    operands=(Operand("k", range(0, 64_000)),),
    opcode="1001" "010k" "kkkk" "111k"
    "kkkk" "kkkk" "kkkk" "kkkk"
)
def call(machine, k):
    # machine.push(PC + 2)
    machine.SP.val = machine.SP.val - 2
