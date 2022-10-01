import math


class Formatter:

    all = []

    def __init__(self, name, format_spec, base):
        self._name = name
        self._format_spec = format_spec
        self._base = base
        self.all.append(self)

    @property
    def name(self):
        return self._name

    def format_spec(self, n_bits):
        width = math.ceil(n_bits / math.log(self._base, 2))
        return self._format_spec.format(width)

    @property
    def base(self):
        return self._base

    @classmethod
    def by_name(cls, name):
        for formatter in cls.all:
            if formatter.name == name:
                return formatter
        return cls.all[0]


bin_formatter = Formatter("binary", "{{:0{}b}}", 2)
oct_formatter = Formatter("octal", "{{:0{}o}}", 8)
dec_formatter = Formatter("decimal", "{{:0{}d}}", 10)
hex_formatter = Formatter("hexadecimal", "{{:0{}x}}", 16)
