import math, sys, harness as h

RATE = 48000
RATIOS = (0.125, 0.5, 1.0, 2.0, 4.0, 8.0)
CORNERS = [float(x) for x in sys.argv[1].split(',')]
SLOPE = int(sys.argv[2]) if len(sys.argv) > 2 else 12

curves = {}
for c in CORNERS:
    fa0 = h.warp(c, RATE)
    row = []
    for r in RATIOS:
        p = h.unwarp(fa0 * r, RATE)
        # settle long enough for the corner's own ring and for the probe
        settle = max(0.4, 40.0 / min(p, c))
        meas = max(0.4, 60.0 / p)
        g, mw, md = h.gain_db(RATE, c, 0.7071067811865476, SLOPE, p,
                              level=16000, settle=settle, meas=meas)
        row.append(g)
    curves[c] = row
    print('f0 %8.1f  ' % c + '  '.join('%8.4f' % v for v in row))

ref = curves[CORNERS[0]]
worst = 0.0; where = None
for c in CORNERS[1:]:
    for r, a, b in zip(RATIOS, ref, curves[c]):
        if abs(a - b) > abs(worst):
            worst = a - b; where = (c, r)
print('worst spread vs f0=%.1f: %+.4f dB at %s (bar 0.05)' % (CORNERS[0], worst, where))
