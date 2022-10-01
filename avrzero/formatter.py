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

    @property
    def format_spec(self):
        return self._format_spec

    @property
    def base(self):
        return self._base

    @classmethod
    def by_name(cls, name):
        for formatter in cls.all:
            if formatter.name == name:
                return formatter
        return cls.all[0]


bin_formatter = Formatter("binary", "{:016b}", 2)
oct_formatter = Formatter("octal", "{:06o}", 8)
dec_formatter = Formatter("decimal", "{:05d}", 10)
hex_formatter = Formatter("hexadecimal", "{:04x}", 16)
