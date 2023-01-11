#!/usr/bin/env bash

source venv/bin/activate
python -m build
python -m pip install --no-deps dist/avrzero-*-py3-none-any.whl
python -m avrzero.gui
