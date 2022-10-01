# Machine and Registers

## Register

There are three types of registers: (normal) register, pointer register and
status register.

A register stores one byte (8 bits).

- Get and set its value with `val`, it handles overflow (simply truncates).
- Get and set its bits with Python indexing operator. For example, to get the
  third low bit of `register`, type `register[2]`. The getter returns either `0`
  or `1`. The setter sets bits to `0` and `1` according to the given truth
  value.

A pointer register is one word (16 bits) long.  Note that pointer register does
not store the value directly, but rather a pair of registers. This way, its
value updates as underlying register value changes and vice versa.

- Everything available to register.

A status register simply has more flag attributes making it easier to set
corresponding bits.

- Everything available to register.
- The following attributes can be referenced by short or long name:

Short name | Long name
---------- | -----------------
`C`        | `carry_flag`
`Z`        | `zero_flag`
`N`        | `negative_flag`
`O`        | `overflow_flag`
`S`        | `sign_flag`
`H`        | `half_carry_flag`
`T`        | `bit_copy`
`I`        | `interrupt_flag`

## Machine

We use a typical AVR instruction set machine layout. The machine has two main
parts: `memory` and `flash`.

**`memory`**

The memory of a machine is a collection of `Register` objects. It represents the
RAM of a physical machine. Some alias attributes are created for the ease of
writing instructions:

- `R` or `general_registers` for a list slice of all general purpose registers
  R0:R31;
- `X`, `Y`, and `Z` for special pointer registers that corresponds to R27:R26,
  R29:R28, and R31:R30 respectively.
- `IOR` or `io_registers` for a list slice of I/O registers 0x20:0x60;
- `SP` for stack pointer register 0x5E:0x5D;
- `SREG` for status register 0x5F;
- `EIOR` or `ext_io_registers` for a list slice of extended I/O registers
  0x60:0x100.
- The program counter `PC` is a special register not on the memory.

Consult the [Register](#Register) section for more information on how to use a
register. For the list slices, use Python index operator `[]` as you normally
would.

_Do not forget to add `.val` when getting and setting machine register values._

**`flash`**

The flash of a machine stores a program. A program is represented by a
collection of `int` objects.

- To load a program, use `load_program`.

# Make Your Own Instruction

Below is an example of the implementation of AVR instruction in this project.
You can find all implemented instructions in `instruction.py`.

```
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
```

The `@Instrction.make` decorator takes in three arguments as you can see in the
example above and an optional keyword argument:

**`syntax`**

The syntax of an instruction should be a Python `str` that consists of:
- All uppercase letters are fixed characters that must appear in the code;
- A single lowercase letter is taken a placeholder for an operand;
- Space are taken as a placeholder for one or more spaces;
- All other characters (such as comma) are fixed characters.

**`operands`**

The operands of an instruction and their constraints should be a Python `tuple`
of `Operand` objects.

Operand initializer takes in two arguments: `name` and `choices`. The `choices`
are the values that an operand can take. It should be a Python `range` or `set`.
Note that `range` object can only have `step=1` which is the default. If you
need other sequences (such as `range(0, 8, 2)`), use a `set` instead (like so
`{0, 2, 4, 6}`).

**`opcode`**

The opcode of an instruction should be a Python `str` that is either one word
(16) or two words long. For readability, we separate the string by length of
four as in the example.

**`belong_to`** Optional

The instruction set that an instruction should belong to should be an
`InstructionSet` object. By default, this argument takes on the value of
`InstructionSet.default` which is the default instruction set used by other
modules in the package.

Consult [Machine and Registers](#Machine-and-Registers) section for how to write
the statements inside the function.
