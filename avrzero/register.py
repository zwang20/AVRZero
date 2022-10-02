from random import randint
from tkinter import _get_default_root

from avrzero import BYTE_SIZE, WORD_SIZE

if _get_default_root is not None:
    from tkinter import IntVar
else:
    from avrzero.variable import IntVar
del _get_default_root


class Register:

    N_BITS = BYTE_SIZE

    def __init__(self, name=None, addr=None, val=None, win=None):
        self._name = name
        self._addr = addr
        if val is None:
            val = randint(0, (1 << self.N_BITS) - 1)
        self._val = IntVar(master=win, value=val, name=name)

    def __repr__(self):
        if self.addr is None:
            return f"Register(val={self.val:0{self.N_BITS}b})"
        else:
            return f"Register({self.addr_str}, {self.val:0{self.N_BITS}b})"

    def __str__(self):
        return f"{self.addr_str} -> {self.val:0{self.N_BITS}b}"

    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return self.addr_str

    @property
    def addr(self):
        return self._addr

    @property
    def addr_str(self):
        if self.addr is None:
            return "0x????"
        else:
            return f"0x{self.addr:04X}"

    @property
    def val(self):
        return self._val.get()

    @val.setter
    def val(self, val):
        self._val.set(val % (1 << self.N_BITS))

    def __getitem__(self, idx):
        return (self.val & (1 << idx)) >> idx

    def __setitem__(self, idx, bit):
        bit = 1 if bit else 0
        self.val &= ~(1 << idx)
        self.val |= bit << idx

    def __format__(self, format_spec):
        return self.val.__format__(format_spec)

    def trace_add(self, mode, callback):
        self._val.trace_add(mode, callback)


class PointerRegister(Register):

    N_BITS = WORD_SIZE

    def __init__(self, name=None, pair=None):
        pair = tuple(pair)
        self._name = name
        self._addr = (r.addr for r in pair)
        self._pair = pair

    def __repr__(self):
        r1, r2 = self._pair
        return f"PointerRegister([{r1!r}, {r2!r}])"

    @property
    def addr(self):
        return self._addr

    @property
    def addr_str(self):
        r1, r2 = self._pair
        return f"{r1.addr_str}:{r2.addr_str}"

    @property
    def val(self):
        r1, r2 = self._pair
        return r1.val << r2.N_BITS | r2.val

    @val.setter
    def val(self, val):
        r1, r2 = self._pair
        r1.val = val >> r2.N_BITS
        r2.val = val & ((1 << r2.N_BITS) - 1)

    def trace_add(self, mode, callback):
        r1, r2 = self._pair
        r1._val.trace_add(mode, callback)
        r2._val.trace_add(mode, callback)


class StatusRegister(Register):

    BIT_NAMES = (("C", "Carry flag"),
                 ("Z", "Zero flag"),
                 ("N", "Negative flag"),
                 ("O", "Overflow flag"),
                 ("S", "Sign flag"),
                 ("H", "Half-carry flag"),
                 ("T", "Bit copy"),
                 ("I", "Interrupt flag"))

    @classmethod
    def from_(cls ,reg):
        reg._name = "status register"
        reg.__class__ = cls
        return reg


for i, (abbr, name) in enumerate(StatusRegister.BIT_NAMES):
    prop = property(lambda r, n=i: r.__getitem__(n),
                    lambda r, b, n=i: r.__setitem__(n, b))
    name = name.lower().translate({" ": "_", "-": "_"})
    setattr(StatusRegister, abbr, prop)
    setattr(StatusRegister, name, prop)
