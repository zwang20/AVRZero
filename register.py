from random import randint


class Register:

    N_BITS = 8

    def __init__(self, addr, val=None):
        self.addr = addr
        if val is None:
            val = randint(0, (1 << self.N_BITS) - 1)
        self._val = val

    def __str__(self):
        return f"0x{self.addr:04X} : {self.val:0{self.N_BITS}b}"

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, val):
        self._val = val % ((1 << self.N_BITS) - 1)

    def get_bit(self, n):
        return self.val & (1 << n)

    def set_bit(self, n, b):
        self.val &= ~(1 << n)
        self.val |= b << n


class PointerRegister(Register):

    N_BITS = Register.N_BITS * 2

    def __init__(self, pair=None):
        self.addr = (r.addr for r in pair)
        self._pair = pair
    
    @property
    def val(self):
        r1, r2 = self.pair
        return r1 << r2.N_BITS | r2

    @val.setter
    def val(self, val):
        r1, r2 = self.pair
        r1.val = val >> r2.N_BITS
        r2.val = val & ((1 << r2.N_BITS) - 1)


class FlagRegister(Register):

    BIT_NAMES = ["Carry flag", "Zero flag", "Negative flag", "Overflow flag",
                 "Sign flag", "Half-carry flag", "Bit copy", "Interrupt flag"]

    def __init__(self, reg):
        self.reg = reg

    def __str__(self):
        return str(self.reg)

    @property
    def val(self):
        return self.reg.val

    @val.setter
    def val(self, val):
        self.reg.val = val


for i, name in enumerate(FlagRegister.BIT_NAMES):
    char_name = name[0]
    setattr(FlagRegister, char_name, property(
        lambda r, n=i: r.get_bit(n),
        lambda r, b, n=i: r.set_bit(n, b)
    ))
