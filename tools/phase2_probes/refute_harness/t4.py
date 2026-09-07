import math, sys, numpy as np, harness as h
import audioeffects
sys.path.insert(0, '/home/brad/gh/pydevices/audiocomponents/tools')
import effect_measurements as em

def periods(rate, f0, q, slope=12, level=30000):
    audioeffects.configure(rate)
    frames = int(rate * max(1.0, 8.0 * q / f0))
    src = h.click_src(rate, frames + 8192, level=level)
    e = audioeffects.create('LowPass', src, rate, frequency=f0, q=q,
                            slope=slope, mix=1.0, trim_db=0.0)
    y = h.pull1(e.output, frames)
    env = np.abs(em.analytic(y))
    pk = int(np.argmax(env))
    target = env[pk] * math.exp(-math.pi)
    below = np.nonzero(env[pk:] <= target)[0]
    if not len(below):
        return None, env[pk]
    n = pk + below[0]
    return (n - pk) / rate * f0, env[pk]

for rate in (48000, 44100, 22050):
    for f0 in (100.0, 500.0, 2000.0):
        row = []
        for q in (2.0, 4.0, 8.0, 16.0):
            p, peak = periods(rate, f0, q)
            lo, hi = 0.8 * q, 1.25 * q
            flag = '' if (p is not None and lo <= p <= hi) else '  <-- OUT'
            row.append('Q%-4g %6.2f (%.2f-%.2f)%s' % (q, p if p else -1, lo, hi, flag))
        print('rate %5d f0 %7.1f  ' % (rate, f0) + ' | '.join(row))
