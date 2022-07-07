def adc(machine, d, r):
    machine.R[d] = machine.R[d] + machine.R[r] + machine.C
    machine.C = 0
    if machine.R[d] > 0xFF:
        machine.R[d] = 0xFF
        machine.C = 1
