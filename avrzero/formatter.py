import math


class Formatter:

    NON_PRINTING = "[?]"
    all = []

    def __init__(self, name, format_spec, base=None, converter=None):
        self._name = name
        self._format_spec = format_spec
        self._base = base
        self._converter = converter
        self.all.append(self)

    @property
    def name(self):
        return self._name

    def format(self, value, /, n_bits):
        if self._base is not None:
            width = math.ceil(n_bits / math.log(self._base, 2))
            string = self._format_spec.format(value, width)
        else:
            string = self._format_spec.format(value)
        if string.isprintable():
            return string
        else:
            return self.NON_PRINTING

    @property
    def converter(self):
        if self._converter is None:
            return lambda s: int(s, self._base)
        return self._converter

    @classmethod
    def by_name(cls, name):
        for formatter in cls.all:
            if formatter.name == name:
                return formatter
        return cls.all[0]


bin_formatter = Formatter("binary", "{:0{}b}", 2)
oct_formatter = Formatter("octal", "{:0{}o}", 8)
dec_formatter = Formatter("decimal", "{:0{}d}", 10)
hex_formatter = Formatter("hexadecimal", "{:0{}x}", 16)
chr_formatter = Formatter("character", "{:c}", converter=ord)
