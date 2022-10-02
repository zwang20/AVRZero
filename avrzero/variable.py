class IntVar:

    def __init__(self, value=0, name=None, **kwargs):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
