from random import randint


class Machine:

    flag_chr = "CZNVSHTI"

    def __init__(self):
        self.registers = [0x00 for _ in range(32)]
        self.flags = 0x11
        self.stack = []

    def __str__(self):
        s = "=" * 80 + "\n"
        n_col = 16
        for i in range(0, 32, n_col):
            s += " ".join(map(lambda n: f"R{n:02d}",
                              range(i, i + n_col))) + "\n"
            s += " ".join(map(lambda n: f" {n:02x}",
                              self.registers[i: i + n_col])) + "\n"
        s += self.flag_chr[::-1] + "\n"
        s += f"{self.flags:08b}" + "\n"
        s += "=" * 80
        return s

    def get_flag_bit(self, n):
        print(n)
        return self.flags & (1 << n)

    def set_flag_bit(self, n, b):
        print(n,b)
        self.flags &= ~(1 << n)
        self.flags |= b << n

    @property
    def R(self):
        return self.registers

    @property
    def X(self):
        return self.registers[27:25:-1]

    @property
    def Y(self):
        return self.registers[29:27:-1]

    @property
    def Z(self):
        return self.registers[31:29:-1]


for i, c in enumerate(Machine.flag_chr):
    setattr(Machine, c, property(
        lambda m, n=i: m.get_flag_bit(n),
        lambda m, b, n=i: m.set_flag_bit(n, b)
    ))

