# REFUTER probe: Tremolo B4 by BIAS composition (additive), not drive modulation.
# chain: Mixer(source200Hz, biasLFO) -> Distortion(static curve) -> Filter(HPF) -> Multiply(env)
import math
import numpy as np
import audiocore, audiofilters, audiomath, audiomixer, synthio
from array import array

SR = 48000
T = SR // 4          # 4 Hz LFO period = 12000 frames
FS = 32767

def q15(x):
    return int(max(-32768, min(32767, round(x * FS))))

def render(node, frames):
    out = []
    n = 0
    while n < frames:
        r, buf = audiocore.get_buffer(node)
        a = np.frombuffer(bytes(buf), dtype='<i2')
        out.append(a); n += len(a)
        if r == audiocore.GET_BUFFER_ERROR: raise RuntimeError('err')
    return np.concatenate(out)[:frames].astype(np.float64)

def h_ratio(seg, f0):
    w = np.hanning(len(seg))
    sp = np.abs(np.fft.rfft(seg * w))
    fr = np.fft.rfftfreq(len(seg), 1.0 / SR)
    def peak(f):
        i = np.argmin(np.abs(fr - f))
        lo, hi = max(0, i - 2), min(len(sp), i + 3)
        return sp[lo:hi].max()
    return 20 * math.log10(peak(3 * f0) / peak(f0) + 1e-30)

def run(mode, drive, A, B, pre_gain=0.0, soft=False):
    src_tab = array('h', [q15(A * math.sin(2 * math.pi * i / 240)) for i in range(240)])
    lfo = [0.5 * (1 - math.cos(2 * math.pi * i / T)) for i in range(T)]   # 0 at trough
    bias_tab = array('h', [q15(B * (1 - l)) for l in lfo])
    env_tab = array('h', [q15(l) for l in lfo])
    src = audiocore.RawSample(src_tab, sample_rate=SR, channel_count=1)
    bias = audiocore.RawSample(bias_tab, sample_rate=SR, channel_count=1)
    env = audiocore.RawSample(env_tab, sample_rate=SR, channel_count=1)
    mx = audiomixer.Mixer(voice_count=2, channel_count=1, sample_rate=SR, buffer_size=1024)
    mx.voice[0].play(src, loop=True); mx.voice[0].level = 1.0
    mx.voice[1].play(bias, loop=True); mx.voice[1].level = 1.0
    dist = audiofilters.Distortion(drive=drive, pre_gain=pre_gain, post_gain=0, mode=mode,
                                   soft_clip=soft, mix=1, sample_rate=SR, channel_count=1,
                                   buffer_size=1024)
    dist.play(mx)
    hp = audiofilters.Filter(filter=synthio.Biquad(synthio.FilterMode.HIGH_PASS,
                                                  frequency=30, Q=0.707),
                             sample_rate=SR, channel_count=1, buffer_size=1024)
    hp.play(dist)
    mul = audiomath.Multiply(source=hp, modulator=env, sample_rate=SR, channel_count=1)
    y = render(mul, 3 * T)
    seg = y[2 * T:3 * T]                       # settled period
    hop = SR // 1000
    rms = np.array([np.sqrt((seg[i:i + hop] ** 2).mean()) for i in range(0, T - hop, hop)])
    imin, imax = int(np.argmin(rms)) * hop, int(np.argmax(rms)) * hop
    tenth = T // 10
    def win(c):
        s = max(0, min(T - tenth, c - tenth // 2))
        return seg[s:s + tenth]
    h_lo, h_hi = h_ratio(win(imin), 200.0), h_ratio(win(imax), 200.0)
    crest = 20 * math.log10(np.abs(y).max() / FS + 1e-30)
    return h_lo, h_hi, h_lo - h_hi, crest

print(f"{'mode':10} {'drv':>4} {'A':>4} {'B':>4} {'h3@min':>8} {'h3@max':>8} {'diff':>7} {'crest':>7}")
M = audiofilters.DistortionMode
for mode, name in ((M.WAVESHAPE, 'WAVESHAPE'), (M.CLIP, 'CLIP')):
    for drive in (0.3, 0.6, 0.9):
        for A, B in ((0.45, 0.45), (0.35, 0.6), (0.30, 0.68), (0.5, 0.45)):
            lo, hi, d, c = run(mode, drive, A, B)
            print(f"{name:10} {drive:4} {A:4} {B:4} {lo:8.1f} {hi:8.1f} {d:7.2f} {c:7.1f}")
# depth 0 control: no bias motion, no envelope motion
lo, hi, d, c = run(M.WAVESHAPE, 0.6, 0.45, 0.0)
print(f"DEPTH0-ish (B=0, env still moves): diff {d:.2f} dB crest {c:.1f}")
