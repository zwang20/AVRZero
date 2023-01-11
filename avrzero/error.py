class AVRSyntaxError(Exception):

    def __init__(self, *args, obj=None):
        super().__init__(*args)
        self._obj = obj

    def __str__(self):
        string = super().__str__()
        string += "\n" + "-" * len(string) + "\n"
        string += str(self._obj)

        return string


class AVRMachineError(Exception):
    pass
