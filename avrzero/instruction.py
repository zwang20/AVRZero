from functools import cache, cached_property

from avrzero import BYTE_SIZE, WORD_SIZE
from avrzero.error import AVRSyntaxError


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

    @cached_property
    def name(self):
        return self._tokens[0]

    def match(self, string):
        operand_map = {}
        for token in self._tokens:
            if isinstance(token, Operand):
                num_str = ""
                while string and string[0].isdigit():
                    num_str += string[0]
                    string = string[1:]
                if not num_str:
                    raise AVRSyntaxError(f"expect digits before {string!r}",
                                         obj=self)
                operand_map[token.name] = int(num_str)
            elif token == " ":
                if not string or not string[0].isspace():
                    raise AVRSyntaxError(f"expect space before {string!r}",
                                         obj=self)
                string = string.lstrip()
            else:
                if not string.lower().startswith(token.lower()):
                    raise AVRSyntaxError(f"expect {token!r} before {string!r}",
                                         obj=self)
                string = string[len(token):]

        if string and not string.isspace():
            raise AVRSyntaxError(f"unexpected {string!r} at the end", obj=self)

        return operand_map

    @classmethod
    def parse(cls, string, operands):
        tokens = []
        token = ""
        for char in string:
            if char.isupper():
                token += char
            else:
                if token:
                    tokens.append(token)
                    token = ""
                if char.islower():
                    for operand in operands:
                        if operand.name == char:
                            tokens.append(operand)
                            break
                    else:
                        raise ValueError(
                            f"{char} in syntax, but not in operands"
                        )
                elif char.isspace():
                    tokens.append(" ")
                else:
                    tokens.append(char)

        if token:
            tokens.append(token)

        missing = set(operands) \
                - set(filter(lambda obj: isinstance(obj, Operand), tokens))
        if missing:
            missing_names = ", ".join(map(lambda operand: operand.name,
                                          missing))
            raise ValueError(f"{missing_names} in operands, but not in syntax")

        return cls(tokens)


class Operand:

    def __init__(self, name, choices):
        if not isinstance(name, str):
            raise TypeError("invalid type for name, expect str")
        if len(name) != 1:
            raise ValueError("invalid length for name, expect 1")
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

    @cached_property
    def choices(self):
        return sorted(tuple(self._choices))

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

    def __init__(self, opcode_str, operands):
        if not isinstance(opcode_str, str):
            raise TypeError("invalid type for operand str, expect str")
        if len(opcode_str) % BYTE_SIZE:
            raise ValueError("invalid length for operand str, "
                             f"expect multiple of {BYTE_SIZE}")
        self._str = opcode_str
        self._operands = operands

    def __str__(self):
        return self._str

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
        for operand in self._operands:
            key = operand.name
            val = operand.choices.index(operand_map[key])
            mapped |= self.map_int(val, self.mask_char(key))

        codes = []
        for _ in range(self.n_bits // WORD_SIZE):
            codes.insert(0, mapped & ((1 << WORD_SIZE) - 1))
            mapped >>= WORD_SIZE
        return codes

    def get_operand_map(self, codes):
        mapped = 0
        for _ in range(self.n_bits // WORD_SIZE):
            mapped <<= WORD_SIZE
            mapped |= codes.pop(0)

        operand_map = {}
        for operand in self._operands:
            key = operand.name
            idx = self.get_int(mapped, self.mask_char(key))
            operand_map[key] = operand.choices[idx]

        return operand_map

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

    @staticmethod
    def get_int(mapped, mask):
        bit_len = mask.bit_length() - 1
        integer = 0
        weight = 0
        while bit_len >= 0:
            if mask & (1 << bit_len):
                integer <<= 1
                if mapped & (1 << bit_len):
                    integer |= 1
            bit_len -= 1

        return integer

    @classmethod
    def parse(cls, opcode_str, operands):
        opcode = cls(opcode_str, operands)
        operand_names = set(operand.name for operand in operands)
        opcode_names = set(opcode._str) - {"0", "1"}
        missing_names = opcode_names - operand_names
        if missing_names:
            raise ValueError(f"{missing_names} in opcode, but not in operands")
        missing_names = operand_names - opcode_names
        if missing_names:
            raise ValueError(f"{missing_names} in operands, but not in opcode")
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
        return self.syntax.name

    def str_to_opcode(self, string):
        operand_map = self._syntax.match(string)
        for operand in self._operands:
            if not operand.check(operand_map[operand.name]):
                raise AVRSyntaxError(
                    f"operand {operand.name} has invalid value", obj=self)

        return self._opcode.map_operands(operand_map)

    @classmethod
    def make(cls, syntax, operands, opcode, belong_to=None):
        seen_operand_names = []
        for operand in operands:
            if operand.name in seen_operand_names:
                raise ValueError("duplicate operand names")
            else:
                seen_operand_names.append(operand.name)

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
                yield instruction

    def by_opcode(self, codes):
        opcode = 0
        for code in codes:
            opcode <<= WORD_SIZE
            opcode |= code
        for instruction in self._instructions:
            if (instruction.opcode.fixed_mask & opcode ==
                    instruction.opcode.fixed):
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
    R = SREG = machine.SREG

    val = Rd.val + Rr.val + SREG.C
    SREG.H = Rd[3] and Rr[3] or Rr[3] and not R[3] and not R[3] and Rd[3]
    SREG.V = Rd[7] and Rr[7] and not R[7] or not Rd[7] and not Rr[7] and R[7]
    SREG.S = SREG.N != SREG.V
    SREG.N = R[7]
    SREG.Z = not R
    SREG.C = Rd[7] and Rr[7] or Rr[7] and not R[7] or not R[7] and Rd[7]
    Rd.val = val

    machine.PC.val += 1

@Instruction.make(
    syntax="ADD Rd, Rr",
    operands=(Operand("d", range(0, 32)),
              Operand("r", range(0, 32))),
    opcode="0000" "11rd" "dddd" "rrrr"
)
def add(machine, d, r):
    Rd, Rr = machine.R[d], machine.R[r]
    R = SREG = machine.SREG

    val = Rd.val + Rr.val
    SREG.H = Rd[3] and Rr[3] or Rr[3] and not R[3] and not R[3] and Rd[3]
    SREG.V = Rd[7] and Rr[7] and not R[7] or not Rd[7] and not Rr[7] and R[7]
    SREG.S = SREG.N != SREG.V
    SREG.N = R[7]
    SREG.Z = not R
    SREG.C = Rd[7] and Rr[7] or Rr[7] and not R[7] or not R[7] and Rd[7]
    Rd.val = val

    machine.PC.val += 1

@Instruction.make(
    syntax="BCLR s",
    operands=(Operand("s", range(0, 8)),),
    opcode="1001" "0100" "1sss" "1000"
)
def bclr(machine, s):
    machine.SREG[s] = 0
    machine.PC.val += 1

@Instruction.make(
    syntax="CALL k",
    operands=(Operand("k", range(0, 64_000)),),
    opcode="1001" "010k" "kkkk" "111k"
    "kkkk" "kkkk" "kkkk" "kkkk"
)
def call(machine, k):
    machine.push_stack(machine.PC.val + 2, 2)
    machine.PC.val = k

@Instruction.make(
    syntax="LD Rd, X",
    operands=(Operand("d", range(0, 32)),),
    opcode="1001" "000d" "dddd" "1100"
)
def ld(machine, d):
    machine.R[d].val = machine.R[machine.X.val].val

@Instruction.make(
    syntax="LD Rd, X+",
    operands=(Operand("d", range(0, 32)),),
    opcode="1001" "000d" "dddd" "1101"
)
def ld_post_inc(machine, d):
    machine.R[d].val = machine.R[machine.X.val].val
    machine.X.val += 1

@Instruction.make(
    syntax="LD Rd, -X",
    operands=(Operand("d", range(0, 32)),),
    opcode="1001" "000d" "dddd" "1110"
)
def ld_pre_dec(machine, d):
    machine.X.val -= 1
    machine.R[d].val = machine.R[machine.X.val].val

@Instruction.make(
    syntax="LDI Rd, k",
    operands=(Operand("d", range(16, 32)),
              Operand("k", range(0, 256))),
    opcode="1110" "kkkk" "dddd" "kkkk"
)
def ldi(machine, d, k):
    machine.R[d].val = k
    machine.PC.val += 1

@Instruction.make(
    syntax="NOP",
    operands=(),
    opcode="0000" "0000" "0000" "0000"
)
def nop(machine):
    machine.PC.val += 1

@Instruction.make(
    syntax="POP Rd",
    operands=(Operand("d", range(0, 32)),),
    opcode="1001" "000d" "dddd" "1111"
)
def pop(machine, d):
    machine.R[d].val = machine.pop_stack()
    machine.PC.val += 1

@Instruction.make(
    syntax="PUSH Rd",
    operands=(Operand("d", range(0, 32)),),
    opcode="1001" "001d" "dddd" "1111"
)
def push(machine, d):
    machine.push_stack(machine.R[d].val)
    machine.PC.val += 1

@Instruction.make(
    syntax="RET",
    operands=(),
    opcode="1001" "0101" "0000" "1000"
)
def ret(machine):
    machine.PC.val = machine.pop_stack(2)
