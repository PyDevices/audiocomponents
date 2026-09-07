# REFUTER probe (N-TRAN-2 / TransientShaper T4): can a COMPOSED palette graph
# -- a second audiodynamics.Dynamics in DYN_COMPRESS after the DYN_TRANSIENT
# node -- give a sustain-gain trace that HOLDS (T4 clause 1: no sample more
# than 0.25 dB below the running maximum over the first 200 ms) and whose
# shape follows the note's decay rate (clause 2: time-to-90% differing >= 2:1
# between a 10 dB/s and a 40 dB/s decay)?
# Trace read: node.gain_reduction_db per block (the same reporting the seed's
# V-T4 run used on DYN_TRANSIENT).
import math
from array import array
import numpy as np
import audiocore, audiodynamics

SR = 48000
BLK = audiodynamics.FRAMES
DUR = 0.40

def note(rate_db_s, peak=0.7, dur=DUR):
    n = int(SR * dur)
    out = array('h', bytes(2 * n))
    for i in range(n):
        t = i / SR
        a = peak * (10.0 ** (-rate_db_s * t / 20.0))
        out[i] = int(max(-32768, min(32767, round(a * 32767 * math.sin(2 * math.pi * 220 * t)))))
    return out

def trace(rate, peak, thr, ratio=4.0, attack_ms=2.0, release_ms=40.0, ms=200):
    src = audiocore.RawSample(note(rate, peak), sample_rate=SR, channel_count=1)
    d = audiodynamics.Dynamics(audiodynamics.DYN_COMPRESS, sample_rate=SR, channel_count=1)
    d.set(threshold_db=thr, ratio=ratio, attack_ms=attack_ms, release_ms=release_ms,
          knee_db=0.0, makeup_db=0.0)
    d.play(src)
    g, n, need = [], 0, int(SR * ms / 1000)
    while n < need:
        r, buf = audiodynamics.get_buffer(d)
        if r == audiodynamics.GET_BUFFER_ERROR: raise RuntimeError('err')
        n += len(bytes(buf)) // 2
        gr = d.gain_reduction_db
        g.append(gr() if callable(gr) else gr)
    return np.array(g)

def clause1(g):
    run = np.maximum.accumulate(g)
    return float((run - g).max())

def clause2(g):
    lo, hi = g[0], g.max()
    if hi - lo < 1e-9: return None
    idx = int(np.argmax(g >= lo + 0.9 * (hi - lo)))
    return idx * BLK / SR * 1000.0

for label, thr, peak in (("calibrated  thr=-6  peak=0.7", -6.0, 0.7),
                         ("same thr, note 12 dB quieter", -6.0, 0.175)):
    print(label)
    ts = {}
    for rate in (10.0, 40.0):
        g = trace(rate, peak, thr)
        ts[rate] = clause2(g)
        print("  %2.0f dB/s: start %+6.2f  peak %+6.2f  worst drop below running max %.2f dB  t90 %s ms"
              % (rate, g[0], g.max(), clause1(g), ts[rate]))
        print("           trace:", " ".join("%+.2f" % v for v in g))
    if ts[10.0] and ts[40.0]:
        print("  ratio t90(10)/t90(40) = %.2f" % (ts[10.0] / ts[40.0]))
