from random import randint


class Register:

    N_BITS = 8
    MAX_VAL = 1 << N_BITS

    def __init__(self, addr, val=None):
        self.addr = addr
        if val is None:
            val = randint(0, (1 << self.N_BITS) - 1)
        self._val = val

    def __str__(self):
        if self.addr is None:
            addr_str = "????"
        else:
            addr_str = f"{self.addr:04X}"
        return f"0x{addr_str} : {self.val:0{self.N_BITS}b}"

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, val):
        self._val = val % ((1 << self.N_BITS) - 1)

    def __getitem__(self, idx):
        return self.val & (1 << idx)

    def __setitem__(self, idx, bit):
        bit = 1 if bit else 0
        self.val &= ~(1 << idx)
        self.val |= bit << idx


class PointerRegister(Register):

    N_BITS = Register.N_BITS * 2

    def __init__(self, pair=None):
        self.addr = (r.addr for r in pair)
        self._pair = pair

    def __str__(self):
        r1, r2 = self._pair
        return f"0x{r1.addr:04X}:0x{r2.addr:04X} : {self.val:0{self.N_BITS}b}"

    @property
    def val(self):
        r1, r2 = self._pair
        return r1.val << r2.N_BITS | r2.val

    @val.setter
    def val(self, val):
        r1, r2 = self._pair
        r1.val = val >> r2.N_BITS
        r2.val = val & ((1 << r2.N_BITS) - 1)


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
        reg.__class__ = cls
        return reg


for i, (abbr, name) in enumerate(StatusRegister.BIT_NAMES):
    prop = property(
        lambda r, n=i: r.__getitem__(n),
        lambda r, b, n=i: r.__setitem__(n, b)
        )
    name = name.lower().translate({" ": "_", "-": "_"})
    setattr(StatusRegister, abbr, prop)
    setattr(StatusRegister, name, prop)
