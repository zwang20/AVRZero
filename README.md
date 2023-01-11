# AVR Zero

[![PyPI](https://img.shields.io/pypi/v/avrzero?&style=flat-square)][PyPI]

A simple AVR instruction set IDE and simulator for educational purposes.

> **Warning**
>
> This is in no way an accurate representation of the AVR instruction set and
> the AVR assembly. Programs that work in this simulator are not guaranteed to
> work on an actual AVR chip.

![Screenshot](image/screenshot.png)

## Starting Guide

The project is available on PyPI, simply install it with `pip`.

```sh
python -m pip install avrzero
```

Then, you can run the graphics user interface with

```sh
python -m avrzero.gui
```

Or you can run the command line tools with

```sh
python -m avrzero
```

## Install from Source

First, you need to clone the GitHub repository.

Then, install dependencies

```sh
pip install tk
pip install build
```

At the project root, run

```sh
python -m build
```

The artifacts will be in the `dist` directory. Install with

```sh
python -m pip install --no-deps dist/avrzero-*-py3-none-any.whl
```

[PyPI]: https://pypi.org/project/avrzero/
