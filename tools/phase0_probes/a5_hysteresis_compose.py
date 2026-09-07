# REFUTER probe (A5 / Saturation TP3): does a COMPOSED palette graph -- one
# static table on a parallel branch, one linear memory element on the other,
# summed -- produce a loop whose normalised area grows monotonically with
# drive, against a control that is the same path with the memory branch off?
#
# Front section (common to engaged and control): audiofilters.Filter HPF 30 Hz
#   -- the "first-order section" whose own phase gives the control non-zero
#   area at 20 Hz, exactly as TP3 requires of its Hysteresis 0 control.
# Engaged: Mixer[ Distortion(static table, fixed pre_gain) , FeedbackDelay
#   (feedback .9, loop_drive 0 = LINEAR memory: the seed's own element) ]
# Control: Mixer[ Distortion(...) , silent ]
import math
import numpy as np
import audiocore, audiofilters, audiomixer, audioecho, synthio
from array import array

SR = 48000
F0 = 20.0
P = int(SR / F0)          # one period, 2400 frames
BUF = 512
FS = 32767

def q15(v): return int(max(-32768, min(32767, round(v * FS))))

def tri(n, A):
    # 20 Hz triangle, one period table
    out = []
    for i in range(n):
        p = (i / n + 0.25) % 1.0
        v = 4 * p - 1 if p < 0.5 else 3 - 4 * p
        out.append(q15(A * v))
    return array('h', out)

def render(node, frames):
    out, n = [], 0
    while n < frames:
        r, buf = audiocore.get_buffer(node)
        a = np.frombuffer(bytes(buf), dtype='<i2')
        out.append(a); n += len(a)
        if r == audiocore.GET_BUFFER_ERROR: raise RuntimeError('err')
    return np.concatenate(out)[:frames].astype(np.float64)

def shoelace_norm(x, y):
    # closed polygon area of the (x,y) trajectory over one period,
    # normalised by the two peaks -> measures loop SHAPE, not gain
    a = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    return a / (np.abs(x).max() * np.abs(y).max() + 1e-30)

def hpf(src):
    f = audiofilters.Filter(filter=synthio.Biquad(synthio.FilterMode.HIGH_PASS,
                                                  frequency=30, Q=0.707),
                            sample_rate=SR, channel_count=1, buffer_size=BUF)
    f.play(src, loop=True)
    return f

def graph(A, memory=True, table=True, pre_gain=12.0):
    tab = tri(P, A)
    s1 = audiocore.RawSample(tab, sample_rate=SR, channel_count=1)
    s2 = audiocore.RawSample(tab, sample_rate=SR, channel_count=1)
    b1 = hpf(s1)
    d = audiofilters.Distortion(drive=1.0, pre_gain=pre_gain if table else 0.0,
                                post_gain=0, mode=audiofilters.DistortionMode.CLIP,
                                soft_clip=False, mix=1 if table else 0,
                                sample_rate=SR, channel_count=1, buffer_size=BUF)
    d.play(b1)
    mx = audiomixer.Mixer(voice_count=2, channel_count=1, sample_rate=SR,
                          buffer_size=BUF)
    mx.voice[0].play(d); mx.voice[0].level = 0.5
    if memory:
        b2 = hpf(s2)
        fd = audioecho.FeedbackDelay(sample_rate=SR, max_delay_ms=60.0,
                                     channel_count=1, delay_ms=1.0,
                                     feedback=0.9, mix=2.0, loop_drive=0.0)
        fd.play(b2)
        mx.voice[1].play(fd); mx.voice[1].level = 0.5
    return mx, tab

def measure(A, memory, table, pre_gain=12.0):
    mx, tab = graph(A, memory, table, pre_gain)
    y = render(mx, 8 * P)[5 * P:6 * P]
    x = np.frombuffer(bytes(tab), dtype='<i2').astype(np.float64)
    return shoelace_norm(x, y), np.abs(y).max() / FS

# --- controls the run must pass -------------------------------------------
x = np.frombuffer(bytes(tri(P, 0.5)), dtype='<i2').astype(np.float64)
print("control wire (x vs x)        :", shoelace_norm(x, x))
print("planted one-sample lag       :", shoelace_norm(x, np.roll(x, 1)))
print("planted 20-sample lag        :", shoelace_norm(x, np.roll(x, 20)))

print()
print(f"{'in dBFS':>8} {'engaged':>12} {'control':>12} {'excess dB':>10} {'peak_e':>7} {'peak_c':>7}")
for dbfs in (-18, -12, -6):
    A = 10 ** (dbfs / 20)
    ae, pe = measure(A, memory=True, table=True)
    ac, pc = measure(A, memory=False, table=True)
    print(f"{dbfs:8} {ae:12.4e} {ac:12.4e} "
          f"{10*math.log10((ae+1e-30)/(ac+1e-30))*2:10.2f} {pe:7.3f} {pc:7.3f}")

print("\nlinear reference (no table: pre_gain 0, mix 0) -- must be FLAT:")
for dbfs in (-18, -12, -6):
    A = 10 ** (dbfs / 20)
    ae, pe = measure(A, memory=True, table=False)
    ac, pc = measure(A, memory=False, table=False)
    print(f"{dbfs:8} {ae:12.4e} {ac:12.4e} "
          f"{10*math.log10((ae+1e-30)/(ac+1e-30))*2:10.2f} {pe:7.3f} {pc:7.3f}")
