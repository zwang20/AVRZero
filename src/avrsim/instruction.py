from avrsim.register import Register


class Instruction:

    def __init__(self, action, syntax, limits, opcode):
        self.action = action
        self.syntax = syntax
        self.limits = limits
        self.opcode = opcode

    @classmethod
    def make(cls, syntax, limits, opcode, belong_to=None):
        def decorator(action):
            instruciton = cls(action, syntax, limits, opcode)
            if belong_to is None:
                InstructionSet.default.instructions.append(instruciton)
            else:
                belong_to.instructions.append(instruction)

        return decorator


class InstructionSet:

    default = None

    def __init__(self):
        self.instructions = []


# default instruction set
InstructionSet.default = InstructionSet()


@Instruction.make(
    syntax="ADC Rd, Rr",
    limits={"d": range(0, 32), "r": range(0, 32)},
    opcode="0001 11rd dddd rrrr"
)
def adc(machine, d, r):
    Rd, Rr = machine.R[d], machine.R[r]
    SREG = machine.SREG

    R = Register(val=Rd.val + Rr.val + SREG.C)
    SREG.H = Rd[3] and Rr[3] or Rr[3] and not R[3] and not R[3] and Rd[3]
    SREG.V = Rd[7] and Rr[7] and not R[7] or not Rd[7] and not Rr[7] and R[7]
    SREG.S = SREG.N ^ SREG.V
    SREG.N = R[7]
    SREG.Z = not R
    SREG.C = Rd[7] and Rr[7] or Rr[7] and not R[7] or not R[7] and Rd[7]
    Rd.val = R.val
