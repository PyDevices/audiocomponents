import math, cmath, harness as h

FLAT = 0.7071067811865476

def rbj_lp_db(f0, q, hz, rate):
    w0 = 2*math.pi*f0/rate
    al = math.sin(w0)/(2*q)
    c = math.cos(w0)
    b0 = (1-c)/2; b1 = 1-c; b2 = b0
    a0 = 1+al; a1 = -2*c; a2 = 1-al
    b0, b1, b2, a1, a2 = b0/a0, b1/a0, b2/a0, a1/a0, a2/a0
    z = cmath.exp(-2j*math.pi*hz/rate)
    return 20*math.log10(abs((b0+b1*z+b2*z*z)/(1+a1*z+a2*z*z)))

for rate in (48000, 44100, 22050):
    top = 0.45*rate
    for f0, q in ((1000.0, FLAT), (1000.0, 4.0), (100.0, FLAT), (5000.0, FLAT)):
        if f0 > 0.4*rate:
            continue
        worst = 0.0; where = None
        for frac in (0.005, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.45):
            p = frac*rate
            want = rbj_lp_db(f0, q, p, rate)
            settle = max(0.4, 40.0/min(p, f0))
            meas = max(0.4, 60.0/p)
            got, _, _ = h.gain_db(rate, f0, q, 12, p, level=int(min(30000, 26000/q)),
                                  settle=settle, meas=meas)
            d = got-want
            if abs(d) > abs(worst):
                worst = d; where = (p, got, want)
        print('rate %5d f0 %7.1f Q %5.3f  worst %+.4f dB at %.0f Hz (got %+.3f want %+.3f) bar 0.1'
              % (rate, f0, q, worst, where[0], where[1], where[2]))
