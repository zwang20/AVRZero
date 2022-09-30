import argparse
from pprint import pprint

from avrzero.assembler import Assembler
from avrzero.machine import Machine


parser = argparse.ArgumentParser(
    description="a simple AVR instruction set simulator"
)
parser.add_argument("file")
args = parser.parse_args()

with open(args.file, "r") as asm_file:
    asm_source = file.read()

assembler = Assembler(asm_source)
machine = Machine()

print(assembler.assemble())
