"""Independent LowPass refutation harness. Renders through the real class."""
import array, math
import numpy as np
import audiocore, audioeffects


def sine_src(hz, rate, frames, level, channels=2):
    v = array.array("h")
    for n in range(frames):
        s = int(round(level * math.sin(2.0 * math.pi * hz * n / rate)))
        if s > 32767: s = 32767
        if s < -32768: s = -32768
        for _ in range(channels):
            v.append(s)
    return audiocore.RawSample(v, sample_rate=rate, channel_count=channels)


def click_src(rate, frames, level=30000, channels=2):
    v = array.array("h")
    for n in range(frames):
        s = level if n == 16 else 0
        for _ in range(channels):
            v.append(s)
    return audiocore.RawSample(v, sample_rate=rate, channel_count=channels)


def pull(node, frames, channels=2):
    out = array.array("h")
    while len(out) < frames * channels:
        ok, buf = audiocore.get_buffer(node)[0], audiocore.get_buffer(node)[1]
        d = memoryview(bytes(buf)).cast("h")
        if not len(d):
            break
        out.extend(d)
    return np.array(out[:frames * channels], dtype=np.float64).reshape(-1, channels)


def pull1(node, frames, channels=2):
    out = array.array("h")
    while len(out) < frames * channels:
        d = memoryview(bytes(audiocore.get_buffer(node)[1])).cast("h")
        if not len(d):
            break
        out.extend(d)
    a = np.array(out[:frames*channels], dtype=np.float64).reshape(-1, channels)
    return a[:, 0]


def build(rate, **opts):
    audioeffects.configure(rate)
    return opts


def exact_bin_frames(rate, hz, target):
    """frames giving an integer number of cycles nearest `target`."""
    cycles = max(1, int(round(target * hz / rate)))
    return int(round(cycles * rate / hz)), cycles


def dft_mag(x, cycles):
    n = len(x)
    k = cycles
    idx = np.arange(n)
    ref = np.exp(-2j * math.pi * k * idx / n)
    return 2.0 * abs(np.dot(x, ref)) / n


def gain_db(rate, corner, q, slope, probe_hz, level=8000, settle=0.25,
            meas=0.25, mix=1.0, trim=0.0, cls="LowPass"):
    """|H(probe)| in dB through a real render of the class."""
    total_target = int(rate * (settle + meas))
    mframes, cycles = exact_bin_frames(rate, probe_hz, int(rate * meas))
    sframes = int(rate * settle)
    src = sine_src(probe_hz, rate, sframes + mframes + 4096, level)
    audioeffects.configure(rate)
    eff = audioeffects.create(cls, src, rate, frequency=corner, q=q,
                              slope=slope, mix=mix, trim_db=trim)
    y = pull1(eff.output, sframes + mframes)
    dry = sine_src(probe_hz, rate, sframes + mframes + 4096, level)
    d = pull1(dry, sframes + mframes)
    wet = y[sframes:sframes + mframes]
    ref = d[sframes:sframes + mframes]
    mw = dft_mag(wet, cycles)
    md = dft_mag(ref, cycles)
    return 20.0 * math.log10(mw / md), mw, md


def warp(hz, rate):
    return (rate / math.pi) * math.tan(math.pi * hz / rate)


def unwarp(fa, rate):
    return (rate / math.pi) * math.atan(math.pi * fa / rate)
