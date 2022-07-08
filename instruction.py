def adc(machine, d, r):
    machine.R[d].val = machine.R[d].val + machine.R[r].val + machine.SREG.C
    machine.SREG.C = 0
    if machine.R[d].val > 0xFF:
        machine.R[d].val = 0xFF
        machine.SREG.C = 1
