import math, cmath
def rbj_lp_db(f0, q, hz, rate):
    w0 = 2*math.pi*f0/rate
    al = math.sin(w0)/(2*q)
    c = math.cos(w0)
    b0 = (1-c)/2; b1 = 1-c; b2 = b0
    a0 = 1+al; a1 = -2*c; a2 = 1-al
    b0, b1, b2, a1, a2 = b0/a0, b1/a0, b2/a0, a1/a0, a2/a0
    z = cmath.exp(-2j*math.pi*hz/rate)
    return 20*math.log10(abs((b0+b1*z+b2*z*z)/(1+a1*z+a2*z*z)))
