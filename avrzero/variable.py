from tkinter import _get_default_root


if _get_default_root is not None:
    from tkinter import IntVar
else:
    class IntVar:

        def __init__(self, value=0, name=None, **kwargs):
            self._value = value

        def get(self):
            return self._value

        def set(self, value):
            self._value = value

del _get_default_root
