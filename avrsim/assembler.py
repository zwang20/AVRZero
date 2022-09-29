from avrsim.error import AVRSyntaxError
from avrsim.instruction import InstructionSet


class Assembler:

    def __init__(self, source, instruction_set=InstructionSet.default):
        self._source = source.splitlines()
        self._instruction_set = instruction_set
        self._errors = ()

    @property
    def errors(self):
        return self._errors

    @property
    def instruction_set(self):
        return self._instruction_set

    def assemble(self):
        program = []
        for line_no, line in enumerate(self._source):
            code, delim, comment = line.partition(";")
            tokens = code.split()
            if not tokens:
                continue
            instruction_name, *_ = tokens
            instructions = [*self._instruction_set.by_name(instruction_name)]
            if not instructions:
                self._errors += ((line_no,
                                  f"no instruction named {instruction_name}"),)
            for instruction in instructions:
                try:
                    program.extend(instruction.str_to_opcode(code))
                except AVRSyntaxError as err:
                    self._errors += ((line_no, str(err)),)

        return program
