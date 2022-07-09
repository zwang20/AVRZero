from register import Register


def adc(machine, d, r):
    machine.R[d].val = machine.R[d].val + machine.R[r].val + machine.SREG.C
    machine.SREG.C = 0
    if not 0 <= machine.R[d].val < Register.MAX_VAL:
        machine.R[d].val %= Register.MAX_VAL
        machine.SREG.C = 1
