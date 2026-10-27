"""`Octaver`'s trait and planted-fault tests.

Six traits, T1 to T6, each with its measurement run over the span listed
with it and the same measurement shown red on a planted fault of the same
kind. `KIT_PLANTS` hands the plants to the kit, which shows each one
differs from the clean class and that no knob stop or patch reproduces it.
`CLAIMS` ties every claim sentence of the docstring to the tests that hold
it.

Every law a measurement checks against is written out here, never taken
from the class: the octave's pitch, the RBJ low-pass, the clock's
attenuation, the material.

The module is numpy-free and imports on MicroPython and CircuitPython,
where `unittest` is absent: the kit reads `KIT_PLANTS` there. Every level is
read with a Hann-windowed Goertzel written out below.
"""

import math
import sys
from array import array

try:
    import unittest
    TestCase = unittest.TestCase
    expected_failure = unittest.expectedFailure
except ImportError:                     # a native interpreter
    unittest = None
    TestCase = object

    def expected_failure(test):
        return test

try:
    import os
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_HERE, "support"))
    sys.path.insert(0, os.path.join(_HERE, "..", "lib"))
except (ImportError, AttributeError, NameError):   # no os.path natively
    pass

import audiomath                                            # noqa: E402
import audioroute                                           # noqa: E402
import kit_common as kc                                     # noqa: E402
import audioeffects                                         # noqa: E402

VENDOR = "PyDevices"

RATES = (48000, 22050)
BLOCK = 256
DIRECT, OCT1, OCT2, TRACKING, TONE1, TONE2, SENS = range(7)

Octaver = audioeffects.Octaver

NOTES = {"E1": 41.2, "A1": 55.0, "E2": 82.41, "A2": 110.0, "D3": 146.8,
         "G3": 196.0, "B3": 246.9, "E3": 164.8, "A3": 220.0, "E4": 329.6,
         "A4": 440.0, "E5": 659.3}

#: Each patch's tracking window (card T2).
WINDOWS = {0: ("E2", "A2", "D3", "G3", "B3", "E4", "A4"),
           3: ("E1", "A1", "E2", "A2", "D3", "G3"),
           4: ("D3", "G3", "B3", "E4", "A4", "E5")}

#: The notes T5 claims clean at each patch: the whole window. Until the
#: dividers clocked on the comparator's ticks, patch 0 stopped at E4: at A4
#: the three draws of seeds 0-39 with the weakest fundamentals had a clock
#: that crossed one rail and not the other, and played the note.
T5_WINDOWS = WINDOWS


# --------------------------------------------------------------------------
# The laws, written out


def midi_of_log(value, low, high):
    """The float MIDI position of `value` on a log span."""
    return 127.0 * math.log(value / low) / math.log(high / low)


def midi_of_lin(value, low, high):
    return 127.0 * (value - low) / (high - low)


def rbj_lowpass_db(f, fc, q, rate):
    """|H(f)| of the RBJ cookbook two-pole low-pass, in dB."""
    w0 = 2.0 * math.pi * fc / rate
    alpha = math.sin(w0) / (2.0 * q)
    cw = math.cos(w0)
    b0 = (1.0 - cw) / 2.0
    b1 = 1.0 - cw
    b2 = b0
    a0 = 1.0 + alpha
    a1 = -2.0 * cw
    a2 = 1.0 - alpha
    w = 2.0 * math.pi * f / rate
    zr, zi = math.cos(w), -math.sin(w)          # z^-1
    z2r, z2i = zr * zr - zi * zi, 2.0 * zr * zi  # z^-2
    nr = b0 + b1 * zr + b2 * z2r
    ni = b1 * zi + b2 * z2i
    dr = a0 + a1 * zr + a2 * z2r
    di = a1 * zi + a2 * z2i
    return 10.0 * math.log10((nr * nr + ni * ni) / (dr * dr + di * di))


def clock_attenuation(f, fc):
    """Two Q 0.5 low-pass sections: four coincident real poles."""
    return (1.0 / (1.0 + (f / fc) ** 2)) ** 2


# --------------------------------------------------------------------------
# Material and measurement


class Rng:
    """A 31-bit LCG: the same uniforms on every interpreter."""

    def __init__(self, seed):
        self.state = (seed * 2654435761 + 12345) & 0x7FFFFFFF

    def uniform(self, low, high):
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return low + (high - low) * (self.state / 2147483648.0)


def _partials(f, n, rate, amps, phases):
    """Sum of sines k*f, by the two-term recurrence, below Nyquist."""
    y = [0.0] * n
    for k in range(1, len(amps) + 1):
        if k * f >= rate / 2.0:
            break
        w = 2.0 * math.pi * k * f / rate
        c = 2.0 * math.cos(w)
        a = amps[k - 1]
        s2 = a * math.sin(phases[k - 1] - w)
        s1 = a * math.sin(phases[k - 1])
        for i in range(n):
            y[i] += s1
            s1, s2 = c * s1 - s2, s1
    return y


def rich(f, n, seed, rate, shift=0.0):
    """Material R: twelve harmonics, U(0.3, 1)/k^U(0.5, 1), the second
    scaled by a further U(1, 2.5), phases U(0, 2 pi) moved `shift` * k,
    normalised to 12000 peak."""
    rng = Rng(seed)
    amps = [rng.uniform(0.3, 1.0) for _ in range(12)]
    exponent = rng.uniform(0.5, 1.0)
    amps = [amps[k] / (k + 1) ** exponent for k in range(12)]
    amps[1] *= rng.uniform(1.0, 2.5)
    phases = [rng.uniform(0.0, 2.0 * math.pi) + shift * (k + 1)
              for k in range(12)]
    y = _partials(f, n, rate, amps, phases)
    peak = max(max(y), -min(y))
    return [12000.0 * v / peak for v in y]


def sine(f, n, rate, amp=16384.0, phase=0.0, start=0):
    y = [0.0] * n
    for i in range(start, n):
        y[i] = amp * math.sin(2.0 * math.pi * f * (i - start) / rate + phase)
    return y


def pcm(left, right=None):
    """Interleaved int16 from one or two float lists."""
    if right is None:
        return array("h", [max(-32768, min(32767, int(round(v))))
                           for v in left])
    out = array("h", bytes(4 * len(left)))
    for i in range(len(left)):
        out[2 * i] = max(-32768, min(32767, int(round(left[i]))))
        out[2 * i + 1] = max(-32768, min(32767, int(round(right[i]))))
    return out


def channel(values, channels, which=0):
    return [values[i] for i in range(which, len(values), channels)]


def render(cls, values, rate, channels, frames=None, options=None,
           patch=None, macros=None):
    """`cls` around `values`, then silence: `frames` frames as int16."""
    if frames is None:
        frames = len(values) // channels
    feed = kc.feed(values, rate, channels)
    e = cls(feed.port, sample_rate=rate, **(options or {}))
    try:
        if patch is not None:
            e.program_change(patch)
        for index, value in (macros or ()):
            e.set_macro(index, value)
        return kc.samples(kc.render(e, frames))
    finally:
        e.deinit()


#: Octave 1 alone, Octave 2 alone: the mixer voice at 1.0 is a wire.
ONLY1 = ((DIRECT, 0), (OCT1, 127), (OCT2, 0))
ONLY2 = ((DIRECT, 0), (OCT1, 0), (OCT2, 127))
OPEN = ((TONE1, 127), (TONE2, 127))

_HANN = {}


def _hann(n):
    if n not in _HANN:
        if len(_HANN) > 16:
            _HANN.clear()
        step = 2.0 * math.pi / (n - 1)
        window = [0.5 - 0.5 * math.cos(step * i) for i in range(n)]
        _HANN[n] = (window, sum(window))
    return _HANN[n]


def level_db(y, f, rate):
    """Hann-windowed Goertzel amplitude of `y` at `f`, in dB re 1."""
    n = len(y)
    window, total = _hann(n)
    c = 2.0 * math.cos(2.0 * math.pi * f / rate)
    s1 = s2 = 0.0
    for i in range(n):
        s1, s2 = y[i] * window[i] + c * s1 - s2, s1
    power = s1 * s1 + s2 * s2 - c * s1 * s2
    amp = math.sqrt(max(power, 0.0)) * 2.0 / total
    return 20.0 * math.log10(amp + 1e-12)


def tail_part(y):
    """The render with its first quarter discarded."""
    return y[len(y) // 4:]


def rising_pitch(y, rate):
    """Frequency from rising zero crossings."""
    count = 0
    first = last = None
    for i in range(1, len(y)):
        if y[i - 1] <= 0 < y[i]:
            if first is None:
                first = i
            last = i
            count += 1
    return (count - 1) * rate / (last - first)


def cents(ratio):
    return 1200.0 * math.log(ratio) / math.log(2.0)


# --------------------------------------------------------------------------
# The measurements


def t1_pitch(cls, rate, channels, f):
    n = int(1.5 * rate)
    s = sine(f, n, rate)
    values = pcm(s, s if channels == 2 else None)
    y = render(cls, values, rate, channels, macros=ONLY1)
    return cents(rising_pitch(channel(y, channels)[rate // 2:], rate)
                 / (f / 2.0))


def t1_onset_ms(cls, rate, channels, f, start=480):
    n = rate // 2
    s = sine(f, n, rate, start=start)
    values = pcm(s, s if channels == 2 else None)
    y = channel(render(cls, values, rate, channels, macros=ONLY1), channels)
    for i in range(n):
        if abs(y[i]) >= 8:
            return 1000.0 * (i - start) / rate
    return None


def balance(y, f, rate):
    """level(f/2) - level(3f/2)."""
    return level_db(y, f / 2.0, rate) - level_db(y, 1.5 * f, rate)


def t2_mono(cls, rate, patch):
    """{note: balance} over the patch's window, Tones open."""
    out = {}
    for name in WINDOWS[patch]:
        f = NOTES[name]
        if 1.5 * f > 0.45 * rate:
            continue
        n = int(1.5 * rate)
        y = render(cls, pcm(sine(f, n, rate)), rate, 1, patch=patch,
                   macros=ONLY1 + OPEN)
        out[name] = balance(tail_part(y), f, rate)
    return out


def t2_stereo(cls, rate, degrees):
    """{note: (left, right)} at patch 0, R leading L by `degrees`."""
    out = {}
    for name in WINDOWS[0]:
        f = NOTES[name]
        n = int(1.5 * rate)
        values = pcm(sine(f, n, rate),
                     sine(f, n, rate, phase=math.radians(degrees)))
        y = render(cls, values, rate, 2, macros=ONLY1 + OPEN)
        out[name] = (balance(tail_part(channel(y, 2, 0)), f, rate),
                     balance(tail_part(channel(y, 2, 1)), f, rate))
    return out


def windows_db(y, f, rate, width, count):
    return [level_db(y[i * width:(i + 1) * width], f, rate)
            for i in range(count)]


def t3_envelope(cls, rate, name, seed):
    """(spread, median) of Octave 1's f/2 against the input's f, per 8/f
    window, while the note is above -36 dBFS, after the first two."""
    f = NOTES[name]
    n = 2 * rate
    r = rich(f, n, seed, rate)
    x = [32767.0 * 10.0 ** ((-6.0 - 40.0 * i / n) / 20.0) * r[i] / 12000.0
         for i in range(n)]
    values = pcm(x)
    y = render(cls, values, rate, 1, macros=ONLY1 + ((SENS, 0),))
    width = int(round(8.0 * rate / f))
    count = int(1.5 * rate) // width
    xin = [float(v) for v in values]
    diffs = [a - b for a, b in zip(windows_db(y, f / 2.0, rate, width, count),
                                   windows_db(xin, f, rate, width, count))]
    diffs = sorted(diffs[2:])
    return diffs[-1] - diffs[0], diffs[len(diffs) // 2]


def t3_sensitivity(cls, rate, name, sens=-50.0):
    """The worst Octave 1 power (DC included) against the input's, in dB,
    over the 8/f windows that start with the clock 3 dB under
    Sensitivity."""
    f = NOTES[name]
    probe = cls(kc.feed(array("h", bytes(4)), rate, 1).port,
                sample_rate=rate)
    fc = probe.macro(TRACKING)
    probe.deinit()
    n = 3 * rate
    a0 = 10.0 ** ((sens + 20.0) / 20.0) * 32768.0 / clock_attenuation(f, fc)
    amp = [a0 * 10.0 ** (-60.0 * i / n / 20.0) for i in range(n)]
    x = [amp[i] * math.sin(2.0 * math.pi * f * i / rate) for i in range(n)]
    values = pcm(x)
    y = render(cls, values, rate, 1,
               macros=ONLY1 + ((SENS, midi_of_lin(sens, -90.0, -40.0)),))
    width = int(round(8.0 * rate / f))
    worst = -999.0
    for k in range(n // width):
        lo = k * width
        clock = amp[lo] * clock_attenuation(f, fc) / 32768.0
        if 20.0 * math.log10(clock) > sens - 3.0:
            continue
        out = sum(v * v for v in y[lo:lo + width]) / width
        inp = sum(float(v) * v for v in values[lo:lo + width]) / width
        rel = 10.0 * math.log10(out + 1e-30) - 10.0 * math.log10(inp)
        worst = max(worst, rel)
    return worst


def rbj_lowpass(x, fc, q, rate):
    """The RBJ cookbook two-pole low-pass run over `x`, in float."""
    w0 = 2.0 * math.pi * fc / rate
    alpha = math.sin(w0) / (2.0 * q)
    cw = math.cos(w0)
    a0 = 1.0 + alpha
    b0 = (1.0 - cw) / 2.0 / a0
    b1 = (1.0 - cw) / a0
    a1 = -2.0 * cw / a0
    a2 = (1.0 - alpha) / a0
    y = [0.0] * len(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        v = b0 * x[i] + b1 * x1 + b0 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, x[i], y1, v
        y[i] = v
    return y


#: The decaying notes the one-sided clock showed on: (patch, note, seed).
#: At 0a69a2f each played its dry note 3 to 17 dB under the input for 54 to
#: 194 ms at its end, with Octave 1 alone and no dry.
ONE_SIDED = ((0, "E2", 3), (0, "G3", 1), (3, "D3", 7), (3, "A1", 7),
             (2, "D3", 2))


def t3_one_sided(cls, rate, patch, name, seed):
    """Octave 1 alone on R decaying 80 dB over 4 s from -6 dBFS peak, at
    `patch`, per 8/f window after the first two: (the worst of the output's
    f over the input's f, in dB, over the windows the octave plays all the
    way through; the same over the windows it stops in; the worst output
    power against the input's over the windows whose clock peaks 3 dB under
    Sensitivity, or None where there is none). The clock is the two Q 0.5
    low-passes at the Tracking the patch shows, run over the input.

    The window the octave stops in is read apart: an octave that ends
    within a few cycles spreads its f/2 over the bins beside it, f among
    them, however cleanly it divides."""
    f = NOTES[name]
    probe = cls(kc.feed(array("h", bytes(4)), rate, 1).port,
                sample_rate=rate)
    probe.program_change(patch)
    fc = probe.macro(TRACKING)
    sens = probe.macro(SENS)
    probe.deinit()
    n = 4 * rate
    r = rich(f, n, seed, rate)
    values = pcm([16384.0 / 12000.0 * r[i] * 10.0 ** (-4.0 * i / n)
                  for i in range(n)])
    xin = [float(v) for v in values]
    clock = rbj_lowpass(rbj_lowpass(xin, fc, 0.5, rate), fc, 0.5, rate)
    y = render(cls, values, rate, 1, patch=patch, macros=ONLY1)
    width = int(round(8.0 * rate / f))
    period = int(rate / f) + 1
    worst = [-999.0, -999.0]
    worst_quiet = None
    edge = 32768.0 * 10.0 ** ((sens - 3.0) / 20.0)
    for k in range(2, n // width):
        lo, hi = k * width, (k + 1) * width
        part = y[lo:hi]
        if any(part):
            through = any(part[-period:])
            worst[not through] = max(worst[not through],
                                     level_db(part, f, rate)
                                     - level_db(xin[lo:hi], f, rate))
        if max(abs(v) for v in clock[lo:hi]) < edge:
            out = sum(float(v) * v for v in part) / width
            inp = sum(v * v for v in xin[lo:hi]) / width
            rel = 10.0 * math.log10(out + 1e-30) - 10.0 * math.log10(inp)
            worst_quiet = rel if worst_quiet is None else max(worst_quiet,
                                                              rel)
    return worst[0], worst[1], worst_quiet


def t3_steady_one_sided(cls, rate):
    """Octave 1 alone on R (seed 7) at D3, -26 dBFS peak, at the Bass
    patch, whose clock sits at Sensitivity: the output's f over the
    input's f, in dB, after the first quarter."""
    f = NOTES["D3"]
    n = rate // 2
    gain = 32768.0 * 10.0 ** (-26.0 / 20.0) / 12000.0
    values = pcm([v * gain for v in rich(f, n, 7, rate)])
    y = tail_part(render(cls, values, rate, 1, patch=3, macros=ONLY1))
    return (level_db(y, f, rate)
            - level_db(tail_part([float(v) for v in values]), f, rate))


def t4_split(cls, rate, channels, name, tones_open):
    f = NOTES[name]
    n = rate
    s = sine(f, n, rate)
    values = pcm(s, s if channels == 2 else None)
    y = render(cls, values, rate, channels,
               macros=ONLY2 + (OPEN if tones_open else ()))
    y = tail_part(channel(y, channels))
    return level_db(y, f / 4.0, rate) - level_db(y, 0.75 * f, rate)


def t4_decay(cls, rate, name, tones_open, sens=0):
    """Octave 2's f/4 over the larger of its f/2 and its 3f/4, per 16/f
    window, on a sine decaying -6 to -86 dBFS over 4 s at the Sensitivity
    step `sens`, over every window that ends before Octave 1's last sound
    (after the first two). Under f/2 it is passing Octave 1 on; under 3f/4
    it has turned into a fourth below the note."""
    f = NOTES[name]
    n = 4 * rate
    x = [16384.0 * 10.0 ** (-80.0 * i / n / 20.0)
         * math.sin(2.0 * math.pi * f * i / rate) for i in range(n)]
    values = pcm(x)
    tones = OPEN if tones_open else ()
    knob = ((SENS, sens),)
    oct1 = render(cls, values, rate, 1, macros=ONLY1 + tones + knob)
    oct2 = render(cls, values, rate, 1, macros=ONLY2 + tones + knob)
    last = max(i for i in range(len(oct1)) if oct1[i])
    width = int(round(16.0 * rate / f))
    splits = []
    for k in range(2, last // width):
        part = oct2[k * width:(k + 1) * width]
        under = level_db(part, f / 4.0, rate)
        splits.append(under - max(level_db(part, f / 2.0, rate),
                                  level_db(part, 0.75 * f, rate)))
    return splits


def t5_margin(y, f, rate):
    """Octave 1's f/2 over the strongest of f/4, 3f/4, f and 2f."""
    main = level_db(y, f / 2.0, rate)
    stray = max(level_db(y, q, rate) for q in (f / 4.0, 0.75 * f, f,
                                                2.0 * f))
    return main - stray


def t5_clean(cls, rate, channels, patch, name, seeds=8):
    """How many of `seeds` R notes divide cleanly (>= 20 dB), and the
    smallest margin."""
    f = NOTES[name]
    n = rate // 2
    clean = 0
    low = 999.0
    for seed in range(seeds):
        left = rich(f, n, seed, rate)
        right = rich(f, n, seed, rate, shift=0.3) if channels == 2 else None
        y = render(cls, pcm(left, right), rate, channels, patch=patch,
                   macros=ONLY1)
        margin = t5_margin(tail_part(channel(y, channels)), f, rate)
        clean += margin >= 20.0
        low = min(low, margin)
    return clean, low


def t6_change(cls, rate, f, tone_hz, index=TONE1, low=100.0, high=2000.0,
              split=2.0):
    """The change in the octave's balance between Tone at `tone_hz` and at
    its top stop, with the prediction from the hertz the knob shows. For
    Tone 1 the balance is f/2 against 3f/2 of Octave 1; for Tone 2,
    f/4 against 3f/4 of Octave 2 (`split` 4)."""
    n = rate
    values = pcm(sine(f, n, rate))
    only = ONLY1 if index == TONE1 else ONLY2
    lo, hi = f / split, 3.0 * f / split
    readings = []
    shown = []
    for midi in (midi_of_log(tone_hz, low, high), 127):
        feed = kc.feed(values, rate, 1)
        e = cls(feed.port, sample_rate=rate)
        for i, v in only + OPEN + ((index, midi),):
            e.set_macro(i, v)
        shown.append(e.macro(index))
        y = tail_part(kc.samples(kc.render(e, n)))
        e.deinit()
        readings.append(level_db(y, lo, rate) - level_db(y, hi, rate))
    measured = readings[0] - readings[1]
    predicted = ((rbj_lowpass_db(lo, shown[0], 0.7071, rate)
                  - rbj_lowpass_db(hi, shown[0], 0.7071, rate))
                 - (rbj_lowpass_db(lo, shown[1], 0.7071, rate)
                    - rbj_lowpass_db(hi, shown[1], 0.7071, rate)))
    return measured, predicted


# --------------------------------------------------------------------------
# T7: real material, at three levels


#: A note is judged where its clock stands this far over (tracking) or under
#: (silence) the Sensitivity set, by the same estimate T3 uses: the note's
#: own line, through the two clock filters. Within 10 dB of Sensitivity the
#: octave is still rising to its level (G3 at 22.05 kHz reads -4.9 dB at
#: +10.7), so tracking is judged from 12.
T7_TRACK_MARGIN_DB = 12.0
T7_SILENT_MARGIN_DB = 6.0
#: Octave 1's f/2 against the note's f, within this many dB, where it plays
#: (the measured spread is 0 to -1.3 dB, and -4.9 at G3 at 22.05 kHz).
T7_TRACK_DB = 6.0
#: Octave 1's level against the note's, at least this far under it, where
#: the clock is under Sensitivity.
T7_SILENT_DB = -40.0
T7_SENSITIVITIES = (-70.0, -60.0, -50.0)


def without_offset(values, rate):
    """The phrase with each note's mean taken out: `kit_common.pluck`
    rings round a small offset (1 to 2 % of the note's peak in the last half
    of its slot), which the string's loop never loses."""
    note = kc.PHRASE_NOTE_MS * rate // 1000
    out = array("h", values)
    for k in range(len(kc.PHRASE_NOTES)):
        lo = k * note
        hi = min(len(out), lo + note)
        if hi <= lo:
            continue
        mean = sum(out[lo:hi]) / (hi - lo)
        for i in range(lo, hi):
            out[i] = int(round(out[i] - mean))
    return out


def t7_read(cls, rate, level, sens, bright=False, offset=True):
    """The plucked phrase (`kit_common.phrase`) at `level` dBFS through
    Octave 1 alone with Sensitivity `sens`: for each note, read over the last
    half of its slot, [(note Hz, the clock's margin over Sensitivity in dB,
    Octave 1's f/2 against the note's f in dB, Octave 1's level against the
    input's in dB)]. The margin is the note's own line through the clock
    filters, as in T3."""
    probe = cls(kc.feed(array("h", bytes(4)), rate, 1).port,
                sample_rate=rate)
    fc = probe.macro(TRACKING)
    probe.deinit()
    values = kc.phrase(rate, 1, level, bright=bright)
    if not offset:
        values = without_offset(values, rate)
    y = render(cls, values, rate, 1,
               macros=ONLY1 + ((SENS, midi_of_lin(sens, -90.0, -40.0)),))
    note = kc.PHRASE_NOTE_MS * rate // 1000
    out = []
    for k in range(len(kc.PHRASE_NOTES)):
        f = kc.PHRASE_NOTES[k]
        # The string sounds at rate / (period + 0.5): the loop's average
        # lengthens it by half a sample.
        hz = rate / (rate // f + 0.5)
        lo = k * note + note // 2
        hi = k * note + note - rate // 50
        heard = [float(v) for v in values[lo:hi]]
        got = list(y[lo:hi])
        line = level_db(heard, hz, rate)
        clock = 20.0 * math.log10(10.0 ** (line / 20.0)
                                  * clock_attenuation(hz, fc) / 32768.0)
        rms_in = math.sqrt(sum(v * v for v in heard) / len(heard))
        rms_out = math.sqrt(sum(v * v for v in got) / len(got))
        out.append((f, clock - sens, level_db(got, hz / 2.0, rate) - line,
                    20.0 * math.log10((rms_out + 1e-9) / rms_in)))
    return out


def t7_verdict(cells, notes):
    """The first fault among `notes` (indexes into the phrase), or None: a
    note whose clock is over Sensitivity by the margin must have its octave,
    and one under it by the margin must be silent."""
    for k in notes:
        f, margin, octave, level = cells[k]
        if margin >= T7_TRACK_MARGIN_DB and abs(octave) > T7_TRACK_DB:
            return "%d Hz, clock %.1f dB over Sensitivity: f/2 %.1f dB" \
                   " against the note" % (f, margin, octave)
        if margin <= -T7_SILENT_MARGIN_DB and level > T7_SILENT_DB:
            return "%d Hz, clock %.1f dB under Sensitivity: %.1f dB against" \
                   " the input, not silent" % (f, margin, level)
    return None


# --------------------------------------------------------------------------
# The planted faults


class PitchShiftOctave(Octaver):
    """T1: a splice shifter an octave down in place of the multiply."""

    def _octave(self, signal, square):
        import audiodelays
        shifter = self._own(audiodelays.PitchShift(
            semitones=-12.0, mix=1.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        shifter.play(signal)
        return shifter


class HeldAllPass(Octaver):
    """T2: the all-pass held at 90 Hz while Tracking moves."""

    def _set_tracking(self, hz):
        Octaver._set_tracking(self, hz)
        if self._allpass is not None:
            self._allpass.frequency = 90.0


class NoAllPass(Octaver):
    """T2: the signal multiplied as it comes, the switch off its
    crossings."""

    def _signal_leg(self, tap):
        return tap


class NoMidSide(Octaver):
    """T2 stereo: each channel clocked on itself, one divider's polarity
    across both."""

    def _mid(self, tap):
        return tap


class SquareToTone(Octaver):
    """T2: the comparator's square fed straight to Tone 1, no multiply."""

    def _octave(self, signal, square):
        return square


class Compressed(Octaver):
    """T3 (a): a compressor after the multiply, an envelope of its own."""

    def _octave(self, signal, square):
        import audiodynamics
        product = Octaver._octave(self, signal, square)
        comp = self._own(audiodynamics.Dynamics(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, threshold_db=-30.0,
            ratio=4.0, attack_ms=1.0, release_ms=100.0))
        comp.play(product)
        return comp


class WireOctave(Octaver):
    """T3 (a): the signal itself in place of the octave."""

    def _octave(self, signal, square):
        return signal


class OneBinCurve(Octaver):
    """T3 (b): the comparator as a one-point step, which the shaper's
    interpolation turns into a gain stage."""

    def _curve(self):
        half = 2048
        return array("h", [-32767] * half + [0] + [32767] * half)

    def _pre_gain(self, sensitivity_db):
        return (2.0 / 4096.0) / 10.0 ** (sensitivity_db / 20.0)


class FourthBelow(Octaver):
    """T4: Octave 2 as `SubOctave(order=2)` on the all-passed dry."""

    def _second(self, signal, tick):
        self._spare = tick
        return self._own(audiomath.SubOctave(
            signal, order=2, mix=1.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count))


class ToneClocked(Octaver):
    """T4: Octave 2 as a divider on Octave 1's output after Tone 1,
    counting down to Sensitivity, as the class was first built (then
    through Tone 1 again, which the clean graph has there): on a
    decaying note it also counts the near-zero junctions where the
    multiplication's humps meet, and turns into a fourth below."""

    def _second(self, signal, tick):
        self._spare = (signal, tick)
        fan = self._own(audioroute.Splitter(self._tone1, taps=2),
                        reset=False)
        self._octave1 = fan.tap(0)
        return self._own(audiomath.SubOctave(
            fan.tap(1), order=1, mix=1.0, threshold=10.0 ** (-80.0 / 20.0),
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))


class ClockWire(Octaver):
    """T5: both clock filters taken out of the clock leg."""

    def _clock_leg(self, tap):
        square = Octaver._clock_leg(self, tap)
        self._comparator.play(self._mid_node)
        return square

    def _mid(self, tap):
        self._mid_node = Octaver._mid(self, tap)
        return self._mid_node


class NoMean(Octaver):
    """T7: the comparator's zero left where it was, on the clock's own
    waveform, with no slow mean taken out of the clock."""

    def _centre(self, clock):
        return clock


class DoubleTone(Octaver):
    """T6: Tone 1 at twice the hertz its knob shows."""

    def _tone1_hz(self):
        return self._hz(2.0 * Octaver._tone1_hz(self))


class DryVoice(Octaver):
    """Not a plant: the octave voices held at 0 on the mixer's path, so a
    test can follow the dry through the wire and back byte for byte."""

    def _levels(self):
        voices = self._mixer.voice
        voices[0].level = 1.0
        voices[1].level = 0.0
        voices[2].level = 0.0


KIT_PLANTS = {
    "T1": PitchShiftOctave,
    "T2-held": (HeldAllPass, 3),
    "T2-none": NoAllPass,
    "T2-mid": NoMidSide,
    "T2-square": SquareToTone,
    "T3-comp": Compressed,
    "T3-wire": WireOctave,
    "T3-bin": OneBinCurve,
    "T4": (FourthBelow, 1),
    "T4-tone1": (ToneClocked, 1),
    "T5": ClockWire,
    "T6": DoubleTone,
}


# --------------------------------------------------------------------------
# The trait tests (CPython: unittest)

def _within(value, target, tolerance):
    return abs(value - target) <= tolerance


class T1Divider(TestCase):
    """The octave is exactly f/2 and sounds within 2 ms of the note."""

    NOTES_HZ = (82.41, 110.0, 111.0, 196.0)

    def test_the_pitch_is_half_the_note(self):
        for rate in RATES:
            for channels in (1, 2):
                for f in self.NOTES_HZ:
                    off = t1_pitch(Octaver, rate, channels, f)
                    self.assertLessEqual(abs(off), 1.0,
                                         (rate, channels, f, off))

    def test_the_onset_is_within_2_ms(self):
        for rate in RATES:
            for channels in (1, 2):
                for f in self.NOTES_HZ:
                    onset = t1_onset_ms(Octaver, rate, channels, f)
                    self.assertIsNotNone(onset)
                    self.assertLessEqual(onset, 2.0, (rate, channels, f))

    def test_a_pitch_shifter_is_red(self):
        rate = 48000
        offs = [t1_pitch(PitchShiftOctave, rate, 1, f)
                for f in self.NOTES_HZ]
        onsets = [t1_onset_ms(PitchShiftOctave, rate, 1, f)
                  for f in (82.41, 110.0, 196.0)]
        self.assertTrue(any(abs(c) > 1.0 for c in offs), offs)
        self.assertTrue(all(o > 2.0 for o in onsets), onsets)


class T2Multiplication(TestCase):
    """Tones open: f/2 over 3f/2 is 4.44 +- 0.3 dB over each patch's
    window, at its Tracking; 3.2 +- 0.3 dB on both channels of a stereo
    source with R 45 degrees ahead."""

    def test_mono_every_window(self):
        for rate in RATES:
            for patch in (0, 3, 4):
                for name, value in t2_mono(Octaver, rate, patch).items():
                    self.assertTrue(_within(value, 4.44, 0.3),
                                    (rate, patch, name, value))

    def test_stereo_45_degrees(self):
        for rate in RATES:
            for name, pair in t2_stereo(Octaver, rate, 45).items():
                for value in pair:
                    self.assertTrue(_within(value, 3.2, 0.3),
                                    (rate, name, pair))

    def test_in_phase_stereo_reads_as_mono(self):
        rate = 48000
        mono = t2_mono(Octaver, rate, 0)
        for name, pair in t2_stereo(Octaver, rate, 0).items():
            self.assertAlmostEqual(pair[0], mono[name], delta=0.01)
            self.assertAlmostEqual(pair[1], mono[name], delta=0.01)

    def _red(self, cls, patch):
        values = t2_mono(cls, 48000, patch)
        return [v for v in values.values() if not _within(v, 4.44, 0.3)]

    def test_an_all_pass_held_at_90_hz_is_red(self):
        self.assertTrue(self._red(HeldAllPass, 3))
        self.assertTrue(self._red(HeldAllPass, 4))

    def test_no_all_pass_is_red(self):
        self.assertTrue(self._red(NoAllPass, 0))

    def test_the_square_straight_to_tone_1_is_red(self):
        self.assertTrue(self._red(SquareToTone, 0))

    def test_no_mid_side_is_red(self):
        values = t2_stereo(NoMidSide, 48000, 45)
        self.assertTrue(any(not _within(pair[1], 3.2, 0.3)
                            for pair in values.values()), values)


class T3Dynamics(TestCase):
    """(a) On R decaying 40 dB at A2, Octave 1's f/2 tracks the note's f
    within 1 dB, median at least -20 dB. (b) Once the clock is 3 dB under
    Sensitivity, Octave 1 is 60 dB under the input."""

    #: A note is claimed where its worst draw clears the 1 dB bar by more
    #: than the spread between draws. D3's worst draws cross the bar; E2's
    #: worst of 32 (0.86 dB) clears it by 0.14 against draws from 0.06 to
    #: 0.86, so neither is claimed. A2's worst of 32 is 0.29.
    ENVELOPE_NOTES = ("A2",)

    def test_the_octave_follows_the_decay(self):
        for rate in RATES:
            for name in self.ENVELOPE_NOTES:
                for seed in range(8):
                    spread, median = t3_envelope(Octaver, rate, name, seed)
                    self.assertLessEqual(spread, 1.0, (rate, name, seed))
                    self.assertGreaterEqual(median, -20.0,
                                            (rate, name, seed))

    def test_silent_below_sensitivity(self):
        for rate in RATES:
            for name in ("E2", "D3"):
                self.assertLessEqual(t3_sensitivity(Octaver, rate, name),
                                     -60.0, (rate, name))

    def test_no_dry_note_as_the_clock_fades(self):
        """(c) A clock whose peaks are unequal crosses one rail before the
        other. Octave 1 alone never passes the dry note: on decaying notes
        its f stays 30 dB under the input's in every window it plays
        through and 20 dB in the window it stops in, and it is 60 dB under
        the input once the clock peaks 3 dB under Sensitivity; on a steady
        note whose clock sits at Sensitivity, 40 dB.

        At 0a69a2f the divider clocked on the rails alone and these read
        -3 to -13 dB: the dry note. What is left at the edge is the
        quiet side's peaks crossing its rail on some cycles and not on
        others, which a clock 3 or 4 LSB high does near -80 dBFS (worst
        -34.2 dB, patch 0 E2)."""
        for rate in RATES:
            for patch, name, seed in ONE_SIDED:
                worst_f, stop_f, quiet = t3_one_sided(Octaver, rate, patch,
                                                      name, seed)
                self.assertLessEqual(worst_f, -30.0,
                                     (rate, patch, name, seed))
                self.assertLessEqual(stop_f, -20.0,
                                     (rate, patch, name, seed))
                self.assertIsNotNone(quiet)
                self.assertLessEqual(quiet, -60.0, (rate, patch, name, seed))
            self.assertLessEqual(t3_steady_one_sided(Octaver, rate), -40.0,
                                 rate)

    def test_a_quiet_high_note_stops_first(self):
        """(d) Sensitivity reads the clock, after Tracking's low-pass: a
        sine at -60 dBFS at patch 0 has its clock 9.4 dB over Sensitivity
        at E2 (10.6 dB under the note) and 26.3 dB under it at E4 (46.3 dB
        under the note), by `clock_attenuation`."""
        amp = 32768.0 * 10.0 ** (-60.0 / 20.0)
        for rate in RATES:
            for name, plays in (("E2", True), ("E4", False)):
                f = NOTES[name]
                db = 20.0 * math.log10(clock_attenuation(f, 90.0))
                self.assertEqual(-60.0 + db > -80.0 + 3.0, plays)
                y = render(Octaver, pcm(sine(f, rate, rate, amp=amp)), rate,
                           1, macros=ONLY1)
                self.assertEqual(any(tail_part(y)), plays, (rate, name))

    def test_a_compressor_is_red(self):
        spread, _ = t3_envelope(Compressed, 48000, "E2", 0)
        self.assertGreater(spread, 1.0)

    def test_a_wire_for_the_octave_is_red(self):
        _, median = t3_envelope(WireOctave, 48000, "E2", 0)
        self.assertLess(median, -20.0)

    def test_a_one_point_comparator_is_red(self):
        self.assertGreater(t3_sensitivity(OneBinCurve, 48000, "E2"), -60.0)


class T4SecondOctave(TestCase):
    """Octave 2's f/4 over 3f/4: +6 dB with the Tones open, +9 at patch 0."""

    NAMES = ("E2", "A2", "D3", "G3", "B3")

    def test_two_octaves_down(self):
        for rate in RATES:
            for channels in (1, 2):
                for name in self.NAMES:
                    self.assertGreaterEqual(
                        t4_split(Octaver, rate, channels, name, True), 6.0)
                    self.assertGreaterEqual(
                        t4_split(Octaver, rate, channels, name, False), 9.0)

    def test_a_fourth_below_is_red(self):
        self.assertLess(t4_split(FourthBelow, 48000, 1, "E2", True), 6.0)

    def test_two_octaves_down_as_the_note_dies(self):
        """A decaying sine: f/4 stays 6 dB over f/2 and over 3f/4 until
        Octave 1 stops, at Sensitivity -90 and -65 dBFS."""
        for rate in RATES:
            for name in self.NAMES:
                for tones_open in (True, False):
                    for sens in (0, 64):
                        splits = t4_decay(Octaver, rate, name, tones_open,
                                          sens)
                        self.assertGreater(len(splits), 4)
                        self.assertGreaterEqual(
                            min(splits), 6.0,
                            (rate, name, tones_open, sens, splits))

    def test_a_divider_on_tone_1_is_red(self):
        splits = t4_decay(ToneClocked, 48000, "B3", True, 64)
        self.assertLess(min(splits), 6.0, splits)


class T5Range(TestCase):
    """8/8 draws of R, at its 12000 peak (-8.7 dBFS), divide cleanly (f/2
    20 dB over its neighbours) at every note of each patch's window."""

    def _window(self, rate, channels):
        for patch in (0, 3, 4):
            for name in T5_WINDOWS[patch]:
                clean, low = t5_clean(Octaver, rate, channels, patch, name)
                self.assertEqual(clean, 8, (rate, channels, patch, name,
                                            low))

    def test_the_windows_mono(self):
        for rate in RATES:
            self._window(rate, 1)

    def test_the_windows_stereo(self):
        for rate in RATES:
            self._window(rate, 2)

    def test_outside_the_window(self):
        rate = 48000
        clean, _ = t5_clean(Octaver, rate, 1, 0, "E1")
        self.assertLess(clean, 8)
        f = NOTES["E5"]
        for seed in range(8):
            y = render(Octaver, pcm(rich(f, rate // 2, seed, rate)), rate,
                       1, patch=0, macros=ONLY1)
            # The attack's step clocks it for a moment; then silence.
            self.assertFalse(any(tail_part(y)), seed)

    def test_wires_for_the_clock_filters_are_red(self):
        for rate in RATES:
            counts = [t5_clean(ClockWire, rate, 1, 0, name)[0]
                      for name in WINDOWS[0]]
            self.assertLess(min(counts), 8, counts)


class T6Tone(TestCase):
    """The change in Octave 1's f/2 over 3f/2 between Tone 1 at 324 Hz and
    at 2000 Hz is the RBJ two-pole's, within 0.25 dB."""

    NOTES_HZ = (164.8, 220.0, 329.6)

    def test_tone_1_is_a_two_pole_low_pass(self):
        for rate in RATES:
            changes = []
            for f in self.NOTES_HZ:
                measured, predicted = t6_change(Octaver, rate, f, 324.0)
                self.assertAlmostEqual(measured, predicted, delta=0.25)
                changes.append(measured)
            self.assertLess(changes[0], changes[1])
            self.assertLess(changes[1], changes[2])

    def test_tone_2_is_a_two_pole_low_pass(self):
        for rate in RATES:
            for f in (110.0, 146.8, 196.0):
                measured, predicted = t6_change(
                    Octaver, rate, f, 70.3, index=TONE2, low=40.0,
                    high=800.0, split=4.0)
                self.assertAlmostEqual(measured, predicted, delta=0.25)

    def test_tone_1_at_twice_its_hertz_is_red(self):
        misses = [abs(m - p) for m, p in
                  (t6_change(DoubleTone, 48000, f, 324.0)
                   for f in self.NOTES_HZ)]
        self.assertGreater(max(misses), 0.25, misses)


#: The phrase's notes inside the tracking window of patch 0 that divide:
#: A2, E2, D3 and G3.
T7_HELD = (0, 1, 2, 3)
#: B3 and E4, the top of the window.
T7_TOP = (4, 5)


class T7RealMaterial(TestCase):
    """T1 to T5 were measured on sines and partial sums at one level. This
    plays a plucked phrase (six strings, one at a time, noisy at the attack
    and decaying through every level under their peak) at -24, -12 and
    -3 dBFS, with Sensitivity at -70, -60 and -50, and holds each note whose
    clock stands over Sensitivity by 12 dB to its octave and each one under
    it by 6 dB to silence."""

    def test_the_lower_notes_divide_and_fall_silent_at_every_level(self):
        for rate in RATES:
            for level in kc.LEVELS_DBFS:
                for sens in T7_SENSITIVITIES:
                    cells = t7_read(Octaver, rate, level, sens)
                    self.assertIsNone(t7_verdict(cells, T7_HELD),
                                      (rate, level, sens))

    def test_a_wire_for_the_octave_is_red_on_real_material(self):
        cells = t7_read(WireOctave, 48000, -12, -70.0)
        self.assertIsNotNone(t7_verdict(cells, T7_HELD))

    def test_a_one_point_comparator_is_red_on_real_material(self):
        cells = t7_read(OneBinCurve, 48000, -24, -50.0)
        self.assertIsNotNone(t7_verdict(cells, T7_HELD))

    def test_the_top_of_the_window_divides_without_an_offset(self):
        """audiocomponents#190: the phrase with each note's mean taken out
        (`without_offset`) has B3 and E4 divide at every level and every
        Sensitivity that puts the clock 12 dB over it, as the card claims
        from E2 to A4."""
        for rate in RATES:
            for level in kc.LEVELS_DBFS:
                for sens in T7_SENSITIVITIES:
                    cells = t7_read(Octaver, rate, level, sens, offset=False)
                    self.assertIsNone(t7_verdict(cells, T7_TOP),
                                      (rate, level, sens))

    def test_the_phrase_s_own_offset_leaves_its_top_notes_dividing(self):
        """The same phrase as `kit_common.pluck` makes it, with the offset
        its loop keeps (1 to 2 % of a note's peak in the last half of its
        slot): B3 and E4 divide at every level and every Sensitivity that
        puts the clock 12 dB over it, as they do without it. Until the
        comparator's zero followed the clock's mean they played the note
        itself here (audiocomponents#190)."""
        for rate in RATES:
            for level in kc.LEVELS_DBFS:
                for sens in T7_SENSITIVITIES:
                    cells = t7_read(Octaver, rate, level, sens)
                    self.assertIsNone(t7_verdict(cells, T7_TOP),
                                      (rate, level, sens))

    def test_without_the_mean_the_phrase_s_offset_stops_its_top_notes(self):
        """The planted fault: the clock handed to the comparator as it
        comes. B3 and E4 play the note itself, and the octave is gone, at
        -3 dBFS with the clock well over Sensitivity."""
        cells = t7_read(NoMean, 48000, -3, -70.0)
        for k in T7_TOP:
            f, margin, octave, level = cells[k]
            self.assertGreaterEqual(margin, T7_TRACK_MARGIN_DB, f)
            self.assertLess(octave, -T7_TRACK_DB, f)
            self.assertGreater(level, -10.0, f)
        self.assertIsNotNone(t7_verdict(cells, T7_TOP))

    def _offset_read(self, cls, name, fraction, rate=48000):
        """Octave 1's f/2 against the note's f, in dB, for a sine at the
        card's -8.7 dBFS with a direct offset of `fraction` of its peak."""
        n = rate // 2
        f = NOTES[name]
        x = [12000.0 * math.sin(2.0 * math.pi * f * i / rate)
             + 12000.0 * fraction for i in range(n)]
        values = pcm(x)
        y = tail_part(render(cls, values, rate, 1, macros=ONLY1))
        heard = [float(v) for v in values[len(values) // 4:]]
        return level_db(y, f / 2.0, rate) - level_db(heard, f, rate)

    def test_an_offset_does_not_end_the_range_from_the_top(self):
        """A sine at the card's -8.7 dBFS with a direct offset of 3 %, 10 %
        and 30 % of its peak: B3, E4 and A4 divide at each, at both rates.
        Before the comparator's zero followed the clock's mean, 3 % stopped
        B3, 1 % stopped E4 and 0.3 % stopped A4."""
        for rate in RATES:
            for name in ("B3", "E4", "A4"):
                for fraction in (0.03, 0.1, 0.3):
                    read = self._offset_read(Octaver, name, fraction, rate)
                    self.assertGreater(read, -T7_TRACK_DB,
                                       (rate, name, fraction))

    def test_without_the_mean_an_offset_ends_the_range_from_the_top(self):
        """The planted fault again, on sines: B3 divides with 1 % of its
        peak and stops at 3 %, E4 divides at 0.3 % and stops at 1 %, A4
        divides at 0.1 % and stops at 0.3 %."""
        for name, holds, stops in (("B3", 0.01, 0.03), ("E4", 0.003, 0.01),
                                   ("A4", 0.001, 0.003)):
            read = {fraction: self._offset_read(NoMean, name, fraction)
                    for fraction in (holds, stops)}
            self.assertGreater(read[holds], -T7_TRACK_DB, (name, read))
            self.assertLess(read[stops], -40.0, (name, read))


class TheAdoption(TestCase):
    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-10-13, so `create()` serves this one. Serve another class under the name and this goes red."""
        import audiocore
        import audioeffects
        from array import array
        self.assertIs(audioeffects.Octaver, Octaver)
        served = audioeffects.create(
            "Octaver",
            audiocore.RawSample(array("h", [0, 0] * 64), sample_rate=48000,
                                channel_count=2),
            48000)
        self.assertIsInstance(served, Octaver)
        served.deinit()


class TheSurface(TestCase):
    """The controls, the wire, latency, tail, reset and tempo."""

    def _fresh(self, rate=48000, channels=1, **options):
        feed = kc.feed(array("h", bytes(4 * channels)), rate, channels)
        return Octaver(feed.port, sample_rate=rate, **options)

    def test_constructor_values_land_on_the_grid(self):
        e = self._fresh(tracking_hz=100.0, tone1_hz=500.0, octave1=0.33,
                        sensitivity_db=-61.0)
        for i, value in ((TRACKING, midi_of_log(100.0, 40.0, 400.0)),
                         (TONE1, midi_of_log(500.0, 100.0, 2000.0)),
                         (OCT1, 0.33 * 127.0),
                         (SENS, midi_of_lin(-61.0, -90.0, -40.0))):
            self.assertEqual(e.get_macro(i), float(int(round(value))))
        e.deinit()

    def test_a_fresh_instance_reads_patch_0(self):
        e = self._fresh()
        self.assertEqual(tuple(e.get_macro(i) for i in range(7)),
                         tuple(float(v) for v in Octaver.PATCHES[0][1]))
        e.deinit()

    def test_sensitivity_dead_stretch(self):
        """A note decaying 100 dB passes the clock through every level."""
        for rate in RATES:
            n = rate
            x = [16384.0 * 10.0 ** (-100.0 * i / n / 20.0)
                 * math.sin(2.0 * math.pi * 82.41 * i / rate)
                 for i in range(n)]
            values = pcm(x)
            ref = render(Octaver, values, rate, 1,
                         macros=ONLY1 + ((SENS, 0),))
            for midi in (7, 14):
                self.assertEqual(render(Octaver, values, rate, 1,
                                        macros=ONLY1 + ((SENS, midi),)),
                                 ref)
            self.assertNotEqual(render(Octaver, values, rate, 1,
                                       macros=ONLY1 + ((SENS, 15),)), ref)
            self.assertAlmostEqual(-90.0 + 50.0 * 14 / 127.0, -84.49,
                                   places=2)

    def _material(self, rate, channels):
        n = BLOCK * (rate // 2 // BLOCK)
        left = rich(110.0, n, 3, rate)
        right = rich(110.0, n, 4, rate) if channels == 2 else None
        return pcm(left, right)

    def test_the_wire_is_the_input(self):
        for rate in RATES:
            for channels in (1, 2):
                values = self._material(rate, channels)
                n = len(values) // channels
                y = render(Octaver, values, rate, channels,
                           options={"octave1": 0.0})
                self.assertEqual(y, kc.samples(bytes(values)))
                # An octave up and back: the wire again, byte for byte.
                feed = kc.feed(values, rate, channels)
                e = Octaver(feed.port, sample_rate=rate, octave1=0.0)
                first = kc.render(e, BLOCK * 8)
                e.set_macro(OCT1, 89)
                middle = kc.render(e, BLOCK * 8)
                e.set_macro(OCT1, 0)
                last = kc.render(e, n - BLOCK * 16)
                e.deinit()
                fsize = 2 * channels
                raw = bytes(values)
                self.assertEqual(first, raw[:BLOCK * 8 * fsize])
                self.assertNotEqual(middle,
                                    raw[BLOCK * 8 * fsize:BLOCK * 16 * fsize])
                self.assertEqual(last, raw[BLOCK * 16 * fsize:])

    def test_the_wire_keeps_every_frame(self):
        """Into the wire and back on a source whose buffers are not the
        class's 256 frames, from the first pull or mid-stream: every
        source frame comes out once, on time. The octave voices are held at
        0 (`DryVoice`), so the output is the source throughout."""
        import lifecycle
        rate = 48000
        for channels in (1, 2):
            values = self._material(rate, channels)
            raw = bytes(values)
            for kind in ("100", "256", "300", "1000", "raw"):
                for steps in (("p20", 0, "p10", 89, "p30"),
                              (0, "p10", 89, "p10")):
                    out = self._dry_run(lifecycle, values, rate, channels,
                                        kind, steps)
                    self.assertEqual(out, raw[:len(out)],
                                     (channels, kind, steps))

    #: Moves into the wire and back, resets, before the first pull and in
    #: one gap between two pulls: "pN" pulls N blocks, a number sets
    #: Octave 1 (0 is the wire).
    SKIPS = (
        (0, "p10"),
        (0, "reset", 0, "p10"),
        ("reset", "p10"),
        ("p4", 0, "p4", 89, 0, 89, 0, "p6"),
        (0, "p4", 89, 0, 89, 0, 89, 0, "p6"),
        ("p4", 0, "p4", "reset", 0, "p6"),
        (0, "p4", 89, 0, "p4", 89, 0, "p4", 89, "p4", 0, "p6"),
        ("p4", "reset", "reset", "p6"),
    )

    def test_the_wire_never_skips(self):
        """Every move in `SKIPS`, with `audiocore.get_buffer` and without
        it (as on a CircuitPython board build): the output is the source,
        every frame once and in order."""
        import lifecycle
        rate = 48000
        for channels in (2, 1):
            values = self._material(rate, channels)
            raw = bytes(values)
            for hide in (False, True):
                for steps in self.SKIPS:
                    out = self._dry_run(lifecycle, values, rate, channels,
                                        "256", steps, hide)
                    self.assertEqual(out, raw[:len(out)],
                                     (channels, hide, steps))

    def _dry_run(self, lifecycle, values, rate, channels, kind, steps,
                 hide=False):
        import types
        from audioeffects import _component
        module = sys.modules[Octaver.__module__]
        real = module.audiocore
        fake = types.ModuleType("audiocore")
        for name in dir(real):
            if name != "get_buffer" or not hide:
                setattr(fake, name, getattr(real, name))
        feed = lifecycle.Feed(values, rate, channels, kind, loop=False)
        out = b""
        module.audiocore = _component.audiocore = fake
        try:
            e = DryVoice(feed.port, sample_rate=rate)
            for step in steps:
                if step == "reset":
                    e.reset()
                elif isinstance(step, str):
                    out += kc.render(e, BLOCK * int(step[1:]))
                else:
                    e.set_macro(OCT1, step)
            e.deinit()
        finally:
            module.audiocore = _component.audiocore = real
        return out

    def test_no_latency(self):
        for rate in (48000, 44100, 22050):
            values = array("h", bytes(2 * 4096))
            values[1000] = 12000
            e = self._fresh(rate=rate)
            self.assertEqual(e.latency_samples, 0)
            e.deinit()
            y = render(Octaver, values, rate, 1)
            first = [i for i in range(len(y)) if y[i]][0]
            self.assertEqual(first, 1000)
            self.assertEqual(y[1000], 12000)

    def test_the_tail_is_bounded(self):
        slow = ((OCT2, 127), (TRACKING, 0), (TONE1, 0), (TONE2, 0))
        for rate in RATES:
            for macros in ((), slow):
                for name in ("E2", "A2"):
                    feed = kc.feed(pcm(rich(NOTES[name], rate // 2, 1,
                                            rate)), rate, 1)
                    e = Octaver(feed.port, sample_rate=rate)
                    for i, v in macros:
                        e.set_macro(i, v)
                    tail = e.tail_samples
                    y = kc.samples(kc.render(e, rate // 2 + tail + 4096))
                    e.deinit()
                    last = max(i for i in range(len(y)) if y[i])
                    self.assertGreater(last, rate // 2 - BLOCK)
                    self.assertLessEqual(last, rate // 2 + tail + BLOCK,
                                         (rate, macros, name, tail))

    def test_reset_renders_as_fresh(self):
        rate = 48000
        values = self._material(rate, 1)
        n = len(values)
        gap = array("h", bytes(2 * BLOCK * 128))
        # The macros come back to patch 0.
        e = TheSurface._fresh(self)
        e.program_change(1)
        e.set_macro(TRACKING, 100)
        e.reset()
        self.assertEqual(e.patch_index, 0)
        self.assertEqual(tuple(e.get_macro(i) for i in range(7)),
                         tuple(float(v) for v in Octaver.PATCHES[0][1]))
        e.deinit()
        # The dividers and filters come back clear: after a note, a pause
        # and a reset, the next note renders as on a fresh instance. (A
        # reset that moves a level takes it at the next zero crossing, as
        # every level move on the mixer does.)
        feed = kc.feed(values + gap + values, rate, 1)
        e = Octaver(feed.port, sample_rate=rate)
        kc.render(e, n + len(gap))
        e.reset()
        after = kc.samples(kc.render(e, n))
        e.deinit()
        self.assertEqual(after, render(Octaver, values, rate, 1))

    def _values_of(self, patch):
        """The constructor keywords that build `patch`'s knobs."""
        from audioeffects import _component
        names = ("direct", "octave1", "octave2", "tracking_hz", "tone1_hz",
                 "tone2_hz", "sensitivity_db")
        grid = Octaver.PATCHES[patch][1]
        return {names[i]: _component.macro_value(
            Octaver._MACRO_RANGES[i],
            _component.position_of_midi("UNIPOLAR", grid[i]))
            for i in range(7)}

    def test_a_patch_builds_as_its_values(self):
        # `patch=` lands every knob before the voices are armed: the
        # all-pass glides a Tracking move over one block, so a patch
        # loaded after arming walked its first block from patch 0's 90 Hz.
        for rate in RATES:
            values = self._material(rate, 1)
            for patch in sorted(Octaver.PATCHES):
                with self.subTest(rate=rate, patch=patch):
                    self.assertEqual(
                        render(Octaver, values, rate, 1,
                               options={"patch": patch}),
                        render(Octaver, values, rate, 1,
                               options=self._values_of(patch)))

    def test_the_lean_patch_is_both_octaves_2_db_louder(self):
        # Patch 6 is patch 1 with Direct at 1, so the mixer passes the dry
        # through with no multiply, and the octaves raised to keep patch
        # 1's balance. Turned down by patch 1's Direct level it renders
        # patch 1, to the octave levels' rounding on the 128-step grid.
        name, grid = Octaver.PATCHES[6]
        self.assertEqual(name, "Both octaves - lean")
        self.assertEqual(Octaver.PATCHES[1][0], "Both octaves")
        one = Octaver.PATCHES[1][1]
        self.assertEqual(grid[DIRECT], 127)
        self.assertEqual(grid[OCT1], grid[OCT2])
        self.assertEqual(grid[TRACKING:], one[TRACKING:])
        down = one[DIRECT] / 127.0
        self.assertAlmostEqual(20.0 * math.log10(down), -1.90, places=2)
        self.assertLess(abs(grid[OCT1] * down - one[OCT1]), 0.2)
        for rate in RATES:
            for channels in (1, 2):
                with self.subTest(rate=rate, channels=channels):
                    values = self._material(rate, channels)
                    both = render(Octaver, values, rate, channels,
                                  options={"patch": 1})
                    lean = render(Octaver, values, rate, channels,
                                  options={"patch": 6})
                    peak = max(abs(v) for v in both)
                    self.assertGreater(peak, 1000)
                    self.assertLess(max(lean), 32767)
                    self.assertGreater(min(lean), -32768)
                    worst = max(abs(lean[i] * down - both[i])
                                for i in range(len(both)))
                    self.assertLessEqual(worst, 0.003 * peak + 3.0)

    def test_a_patch_before_the_first_pull_renders_as_fresh(self):
        # Arming plays only silence, so the all-pass has heard nothing yet:
        # a Tracking move before the first pull lands at once, not walked
        # over the first block from where the arming left it. (Patches 1,
        # 2 and 5 move Direct, which the mixer takes half a block late.)
        for rate in RATES:
            values = self._material(rate, 1)
            for patch in (0, 3, 4):
                with self.subTest(rate=rate, patch=patch):
                    self.assertEqual(
                        render(Octaver, values, rate, 1, patch=patch),
                        render(Octaver, values, rate, 1,
                               options={"patch": patch}))

    def test_a_return_from_the_wire_renders_as_fresh(self):
        # Octave 1 to 0 is the wire at patches 0, 3 and 4; the way back
        # renders what a fresh instance built at the patch renders.
        for rate in RATES:
            values = self._material(rate, 1)
            n = len(values)
            gap = array("h", bytes(2 * BLOCK * 16))
            for patch in (0, 3, 4):
                with self.subTest(rate=rate, patch=patch):
                    feed = kc.feed(values + gap + values, rate, 1)
                    e = Octaver(feed.port, sample_rate=rate, patch=patch)
                    kc.render(e, n)
                    e.set_macro(OCT1, 0)
                    kc.render(e, len(gap))
                    e.set_macro(OCT1, Octaver.PATCHES[patch][1][OCT1])
                    after = kc.samples(kc.render(e, n))
                    e.deinit()
                    self.assertEqual(after, render(
                        Octaver, values, rate, 1, options={"patch": patch}))

    def test_never_reads_the_tempo(self):
        calls = []

        def transport():
            calls.append(1)
            return (True, 0.0, 99.0, 4, 4)
        feed = kc.feed(self._material(48000, 1), 48000, 1)
        e = Octaver.create(feed.port, 48000, transport=transport)
        self.assertEqual(e.capabilities, ())
        kc.render(e, 4096)
        e.transport_changed()
        for i in range(7):
            e.set_macro(i, 100)
        e.program_change(2)
        kc.render(e, 4096)
        e.deinit()
        self.assertEqual(calls, [])

    def test_one_note_at_a_time(self):
        rate = 48000

        def intermodulation(freqs):
            n = 2 * rate
            x = [sum(5000.0 * math.sin(2.0 * math.pi * f * i / rate + j)
                     for j, f in enumerate(freqs)) for i in range(n)]
            y = render(Octaver, pcm(x), rate, 1, macros=ONLY1)[rate // 2:]
            total = sum(float(v) * v for v in y) / len(y)
            lines = set()
            for f in freqs:
                for k in range(1, 40, 2):
                    if k * f / 2.0 < rate / 2.0:
                        lines.add(k * f / 2.0)
            wanted = 0.0
            for q in lines:
                amp = 10.0 ** (level_db(y, q, rate) / 20.0)
                wanted += amp * amp / 2.0
            return 1.0 - wanted / total
        self.assertLess(intermodulation((110.0,)), 0.01)
        chord = intermodulation((110.0, 164.81))
        self.assertTrue(0.35 <= chord <= 0.47, chord)

    def test_the_peak_gain(self):
        """The kit's square and sine at its own amplitude, at the settings
        the ceiling found worst, all three levels at full with the Tones at
        both stops, and at every patch; and a square on every semitone from
        E1 to A2 with all three levels at full, the Tones open and Tracking
        at both stops, at both rates. The worst is a square near E2 with
        Tracking at 40 Hz: 5.03 times its peak."""
        import kit_ceiling
        amp = 3277
        worst = 0.0
        full = ((DIRECT, 127), (OCT1, 127), (OCT2, 127))
        configs = [(None, (k,)) for k in ((OCT1, 127), (OCT2, 127),
                                          (TONE1, 0))]
        configs += [(None, full + ((TONE1, t), (TONE2, t)))
                    for t in (0, 127)]
        configs += [(p, ()) for p in sorted(Octaver.PATCHES)]
        for which in ("square", "sine"):
            values = kit_ceiling.material(which, 48000, 1, amp)
            for patch, knobs in configs:
                y = render(Octaver, values, 48000, 1, patch=patch,
                           macros=knobs)
                worst = max(worst, max(abs(v) for v in y) / float(amp))
        for rate in RATES:
            for semitone in range(18):
                period = rate / (41.2034 * 2.0 ** (semitone / 12.0))
                values = pcm([amp if (i / period) % 1.0 < 0.5 else -amp
                              for i in range(rate)])
                for stop in (0, 127):
                    y = render(Octaver, values, rate, 1,
                               macros=full + OPEN + ((TRACKING, stop),))
                    worst = max(worst, max(abs(v) for v in y) / float(amp))
        self.assertTrue(4.95 <= worst <= 5.1, worst)
        self.assertLessEqual(worst * 10.0 ** (
            Octaver.INPUT_CEILING_DBFS / 20.0), 0.9)


CLAIMS = (
    ("An octave down that is your own note: like the Boss OC-2, it turns "
     "every other cycle of what you play upside down, so the octave keeps "
     "your attack, your decay and your tone.",
     ("T1Divider.test_the_pitch_is_half_the_note",
      "T1Divider.test_the_onset_is_within_2_ms",
      "T2Multiplication.test_mono_every_window",
      "T3Dynamics.test_the_octave_follows_the_decay")),
    ("Tracking moves the range of notes the divider follows.",
     ("T5Range.test_the_windows_mono",)),
    ("Tone 1 and Tone 2 are two-pole low-passes at the hertz they "
     "show, on the first and second octave.",
     ("T6Tone.test_tone_1_is_a_two_pole_low_pass",
      "T6Tone.test_tone_2_is_a_two_pole_low_pass")),
    ("Sensitivity is the level your note must keep after Tracking's "
     "low-pass for the octaves to play, not the level you play at.",
     ("T3Dynamics.test_silent_below_sensitivity",)),
    ("The higher the note, the more that low-pass takes, so a quiet high "
     "note stops before a quiet low one: at patch 0 a sine at -60 dBFS "
     "still has its octave on E2 and none on E4.",
     "T3Dynamics.test_a_quiet_high_note_stops_first"),
    ("Constructor values land on the nearest of each knob's 128 "
     "steps. The Effect controls page lists what the knobs span.",
     ("TheSurface.test_constructor_values_land_on_the_grid",
      "TheSurface.test_a_fresh_instance_reads_patch_0")),
    ("The octave is exactly half your note and sounds within 2 ms of it.",
     ("T1Divider.test_the_pitch_is_half_the_note",
      "T1Divider.test_the_onset_is_within_2_ms")),
    ("Octave 2 is Octave 1 divided again: two octaves down, not a fourth "
     "below the note, until Octave 1 itself stops.",
     ("T4SecondOctave.test_two_octaves_down",
      "T4SecondOctave.test_two_octaves_down_as_the_note_dies")),
    ("On an A2 the octave follows your note's decay within 1 dB: it has "
     "no envelope of its own.",
     "T3Dynamics.test_the_octave_follows_the_decay"),
    ("Below Sensitivity the octaves are silent, with no ghost and no hum, "
     "and as a note fades into it the octave never turns into the note "
     "itself.",
     ("T3Dynamics.test_silent_below_sensitivity",
      "T3Dynamics.test_no_dry_note_as_the_clock_fades")),
    ("With the Tones open the octave carries a fifth above it 4.4 dB "
     "quieter, as the pedal's multiplication does, wherever Tracking is "
     "set.",
     "T2Multiplication.test_mono_every_window"),
    ("Turning Tone 1 down thins that fifth more on high notes than on low "
     "ones.",
     "T6Tone.test_tone_1_is_a_two_pole_low_pass"),
    ("Played at -8.7 dBFS peak, every note at patch 0 from low E (E2) to A4 "
     "divides cleanly, even with a strong second harmonic.",
     ("T5Range.test_the_windows_mono", "T5Range.test_the_windows_stereo")),
    ("Played at -8.7 dBFS peak, the Bass patch covers E1 to G3, and High on "
     "the neck covers D3 to E5; played quieter, each range ends lower.",
     ("T5Range.test_the_windows_mono", "T5Range.test_the_windows_stereo",
      "T3Dynamics.test_a_quiet_high_note_stops_first")),
    ("Below the range a low note's second harmonic clocks the divider and "
     "it skips; above it the clock is low-passed under Sensitivity and the "
     "octave goes silent.",
     "T5Range.test_outside_the_window"),
    ("Between -90 and -84.5 dBFS Sensitivity changes nothing: that whole "
     "stretch is one step of the clock.",
     "TheSurface.test_sensitivity_dead_stretch"),
    ("It plays one note at a time: on a power chord (A2 and E3) about two "
     "fifths of the octave is intermodulation.",
     "TheSurface.test_one_note_at_a_time"),
    ("A direct offset in the input, as a plucked string rings round, does "
     "not take the top of the range from you: the divider turns over on the "
     "clock's own centre, not on zero.",
     ("T7RealMaterial.test_the_phrase_s_own_offset_leaves_its_top_notes_"
      "dividing",
      "T7RealMaterial.test_an_offset_does_not_end_the_range_from_the_top",
      "T7RealMaterial.test_without_the_mean_the_phrase_s_offset_stops_its_"
      "top_notes",
      "T7RealMaterial.test_without_the_mean_an_offset_ends_the_range_from_"
      "the_top")),
    ("A stereo source is clocked on its mid: with the right channel 45 "
     "degrees ahead of the left, the fifth sits 3.2 dB under the octave "
     "instead of 4.4, on both channels.",
     ("T2Multiplication.test_stereo_45_degrees",
      "T2Multiplication.test_in_phase_stereo_reads_as_mono")),
    ("The output can peak at about 5 times the input (a low square, all "
     "three levels at full with the Tones open), so keep the input under "
     "-15 dBFS.",
     "TheSurface.test_the_peak_gain"),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "DECLARED:Octaver,E4-,P5"),
    ("On an ESP32-S3, Both octaves can't keep up and the sound breaks up; "
     "play Both octaves - lean instead.",
     "TheSurface.test_the_lean_patch_is_both_octaves_2_db_louder"),
    ("It has the same balance of your note and the two octaves, 2 dB "
     "louder: turn the level after it down 2 dB and you hear Both octaves.",
     "TheSurface.test_the_lean_patch_is_both_octaves_2_db_louder"),
    ("With both octaves at 0 and Direct at 1 the output is the input, byte "
     "for byte, however the host's buffers are cut.",
     ("TheSurface.test_the_wire_is_the_input",
      "TheSurface.test_the_wire_keeps_every_frame",
      "TheSurface.test_the_wire_never_skips")),
    ("There is no latency.", "TheSurface.test_no_latency"),
    ("`tail_samples` covers the all-pass and the two Tone filters ringing "
     "down.",
     "TheSurface.test_the_tail_is_bounded"),
    ("`reset()` clears the filters and the dividers and returns to patch "
     "0.",
     "TheSurface.test_reset_renders_as_fresh"),
    ("The class never reads the host's tempo.",
     "TheSurface.test_never_reads_the_tempo"),
)


if __name__ == "__main__" and unittest is not None:
    unittest.main()
