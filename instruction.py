from register import Register


def adc(machine, d, r):
    Rd, Rr = machine.R[d], machine.R[r]
    SREG = machine.SREG

    R = Register(val=Rd.val + Rr.val + SREG.C)
    SREG.H = Rd[3] and Rr[3] or Rr[3] and not R[3] and not R[3] and Rd[3]
    SREG.V = Rd[7] and Rr[7] and not R[7] or not Rd[7] and not Rr[7] and R[7]
    SREG.S = SREG.N ^ SREG.V
    SREG.N = R[7]
    SREG.Z = not R
    SREG.C = Rd[7] and Rr[7] or Rr[7] and not R[7] or not R[7] and Rd[7]
    Rd.val = R.val
