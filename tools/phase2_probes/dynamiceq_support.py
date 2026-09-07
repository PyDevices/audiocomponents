"""Shared rig for the `DynamicEQ` probes: build, render, read.

Dual-runtime on purpose - CPython, `cmods/bin/micropython` and
`cmods/bin/circuitpython-effects` all run this file - so it holds no numpy
and no f-strings, and every analysis it does is arithmetic a board could do.
The measurements that need numpy live in `tools/effect_measurements.py` and
read WAVs; these probes read arrays.

Run any probe with the library on the path:

    PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \\
        tools/phase2_probes/dynamiceq_traits.py
"""

import array
import math
import struct

import audiocore

import audioeffects

RATE = 48000
CHANNELS = 2
FULL_SCALE = 32767.0


def build(rate=RATE, channels=CHANNELS, frames=0, data=None, **options):
    """A `DynamicEQ` around a `RawSample` of `data`, through `create()`."""
    if data is None:
        data = array.array('h', bytes(2 * channels * frames))
    source = audiocore.RawSample(data, sample_rate=rate,
                                 channel_count=channels)
    effect = audioeffects.create('DynamicEQ', source, rate, **options)
    return effect, source


def sine(hz, amplitude, frames, rate=RATE, channels=CHANNELS, phase=0.0):
    data = array.array('h', bytes(2 * channels * frames))
    step = 2.0 * math.pi * hz / rate
    for index in range(frames):
        value = int(round(amplitude * math.sin(step * index + phase)))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def burst(hz, amplitude, on_frames, total_frames, lead=0,
          rate=RATE, channels=CHANNELS):
    """`lead` frames of silence, `on_frames` of tone, then silence.

    The lead is not decoration: `audiocore.RawSample` hands its buffer back
    from the beginning, so a burst at frame 0 replays after a `reset()` and
    reads exactly like a node that was never cleared.
    """
    data = array.array('h', bytes(2 * channels * total_frames))
    step = 2.0 * math.pi * hz / rate
    for index in range(on_frames):
        value = int(round(amplitude * math.sin(step * index)))
        for channel in range(channels):
            data[(lead + index) * channels + channel] = value
    return data


def dc(amplitude, on_frames, total_frames, lead=0, channels=CHANNELS):
    data = array.array('h', bytes(2 * channels * total_frames))
    for index in range(on_frames):
        for channel in range(channels):
            data[(lead + index) * channels + channel] = int(amplitude)
    return data


def samples(raw):
    """Signed 16-bit little-endian bytes -> an `array('h')`.

    `array.frombytes` is CPython's and `memoryview.cast` is not on
    MicroPython, so `struct.unpack` is the one route all three interpreters
    have. It is slower and it is the only thing here that is.
    """
    return array.array('h', struct.unpack('<%dh' % (len(raw) // 2), raw))


def impulse_at(amplitude, at, total_frames, channels=CHANNELS):
    data = array.array('h', bytes(2 * channels * total_frames))
    for channel in range(channels):
        data[at * channels + channel] = int(amplitude)
    return data


def render(node_or_effect, frames, channels=CHANNELS):
    """Pull `frames` frames off an effect's output, or off a bare node."""
    out = array.array('h')
    node = getattr(node_or_effect, 'output', node_or_effect)
    while len(out) // channels < frames:
        result, buffer = audiocore.get_buffer(node)
        raw = bytes(buffer)
        if not raw:
            break
        out.extend(samples(raw))
    return out[:frames * channels]


def rms(data, skip=0, channels=CHANNELS, channel=0):
    """RMS of one channel from frame `skip` on.

    Walked with a range rather than a strided slice: MicroPython and
    CircuitPython both raise `NotImplementedError: only slices with step=1`,
    so a strided slice is a measurement that runs on one interpreter of the
    three.
    """
    total = 0.0
    count = 0
    for index in range(skip * channels + channel, len(data), channels):
        value = float(data[index])
        total += value * value
        count += 1
    return math.sqrt(total / count) if count else 0.0


def peak(data, skip=0, channels=CHANNELS):
    highest = 0
    for index in range(skip * channels, len(data)):
        value = data[index]
        if value < 0:
            value = -value
        if value > highest:
            highest = value
    return highest


def gain_db(wet, dry):
    if wet <= 0.0 or dry <= 0.0:
        return float('-inf')
    return 20.0 * math.log10(wet / dry)


def dbfs(amplitude):
    return 20.0 * math.log10(amplitude / FULL_SCALE)


def amp(level_db):
    return int(round(FULL_SCALE * (10.0 ** (level_db / 20.0))))


def fnv1a(data):
    """`audioif/tests/parity/effects_component_probe.py:15`, unchanged."""
    value = 2166136261
    for byte in data:
        value ^= byte
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def compressor_law(over_db, ratio, knee_db=6.0):
    """`audioif/src/shared/audioif_dynamics.c:392-403`, in Python."""
    half = knee_db * 0.5
    slope = 1.0 - 1.0 / ratio
    if over_db <= -half:
        return 0.0
    if over_db < half and knee_db > 0.0:
        x = over_db + half
        return -slope * x * x / (2.0 * knee_db)
    return -slope * over_db


def biquad_response(mode, hz, centre, q, rate=RATE):
    """|H(f)| in dB for the two RBJ sections this class splits with.

    S1's coefficients, evaluated in Python. `mode` is 'notch' or 'band'.
    """
    w0 = 2.0 * math.pi * centre / rate
    alpha = math.sin(w0) / (2.0 * q)
    cos0 = math.cos(w0)
    a = (1.0 + alpha, -2.0 * cos0, 1.0 - alpha)
    if mode == 'notch':
        b = (1.0, -2.0 * cos0, 1.0)
    else:
        b = (alpha, 0.0, -alpha)
    w = 2.0 * math.pi * hz / rate
    return _polar(b, a, w)


def _polar(b, a, w):
    br = b[0] + b[1] * math.cos(-w) + b[2] * math.cos(-2 * w)
    bi = b[1] * math.sin(-w) + b[2] * math.sin(-2 * w)
    ar = a[0] + a[1] * math.cos(-w) + a[2] * math.cos(-2 * w)
    ai = a[1] * math.sin(-w) + a[2] * math.sin(-2 * w)
    num = math.sqrt(br * br + bi * bi)
    den = math.sqrt(ar * ar + ai * ai)
    if den == 0.0:
        return float('inf')
    return 20.0 * math.log10(num / den) if num > 0 else float('-inf')
