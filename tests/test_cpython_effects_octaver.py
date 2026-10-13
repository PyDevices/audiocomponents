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
except ImportError:                     # a native interpreter
    unittest = None
    TestCase = object

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
from audioeffects import rebuilt                            # noqa: E402

VENDOR = "PyDevices"

RATES = (48000, 22050)
BLOCK = 256
DIRECT, OCT1, OCT2, TRACKING, TONE1, TONE2, SENS = range(7)

Octaver = rebuilt.module_class("Octaver")

NOTES = {"E1": 41.2, "A1": 55.0, "E2": 82.41, "A2": 110.0, "D3": 146.8,
         "G3": 196.0, "B3": 246.9, "E3": 164.8, "A3": 220.0, "E4": 329.6,
         "A4": 440.0, "E5": 659.3}

#: Each patch's tracking window (card T2 and T5).
WINDOWS = {0: ("E2", "A2", "D3", "G3", "B3", "E4", "A4"),
           3: ("E1", "A1", "E2", "A2", "D3", "G3"),
           4: ("D3", "G3", "B3", "E4", "A4", "E5")}


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


def t4_split(cls, rate, channels, name, tones_open):
    f = NOTES[name]
    n = rate
    s = sine(f, n, rate)
    values = pcm(s, s if channels == 2 else None)
    y = render(cls, values, rate, channels,
               macros=ONLY2 + (OPEN if tones_open else ()))
    y = tail_part(channel(y, channels))
    return level_db(y, f / 4.0, rate) - level_db(y, 0.75 * f, rate)


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

    def _signal_leg(self, tap):
        node = Octaver._signal_leg(self, tap)
        fan = self._own(audioroute.Splitter(node, taps=2), reset=False)
        self._fan = fan
        return fan.tap(0)

    def _second(self, tap):
        return self._own(audiomath.SubOctave(
            self._fan.tap(1), order=2, mix=1.0,
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


class DoubleTone(Octaver):
    """T6: Tone 1 at twice the hertz its knob shows."""

    def _tone1_hz(self):
        return self._hz(2.0 * Octaver._tone1_hz(self))


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
    "T5": ClockWire,
    "T6": DoubleTone,
}


# --------------------------------------------------------------------------
# The trait tests (CPython: unittest)

#: T5's one stereo draw that drops out at the top of patch 0's window
#: (seed 7, at both rates): its mid's fundamental sits under Sensitivity
#: once the clock filter has taken 55 dB off it.
T5_STEREO_DROPOUT = (0, "A4", 7)


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
                for f in (82.41, 110.0, 196.0):
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
    """(a) On R decaying 40 dB at E2 and A2, Octave 1's f/2 tracks the
    note's f within 1 dB, median at least -20 dB. (b) Once the clock is
    3 dB under Sensitivity, Octave 1 is 60 dB under the input."""

    ENVELOPE_NOTES = ("E2", "A2")

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


class T5Range(TestCase):
    """8/8 draws of R divide cleanly (f/2 20 dB over its neighbours) at
    every note of each patch's window."""

    def _window(self, rate, channels):
        for patch in (0, 3, 4):
            for name in WINDOWS[patch]:
                clean, low = t5_clean(Octaver, rate, channels, patch, name)
                if (channels == 2 and (patch, name)
                        == T5_STEREO_DROPOUT[:2]):
                    self.assertEqual(clean, 7, (patch, name, rate, low))
                    continue
                self.assertEqual(clean, 8, (rate, channels, patch, name,
                                            low))

    def test_the_windows_mono(self):
        for rate in RATES:
            self._window(rate, 1)

    def test_the_windows_stereo(self):
        for rate in RATES:
            self._window(rate, 2)

    def test_a_stereo_note_can_drop_out_at_the_top(self):
        patch, name, seed = T5_STEREO_DROPOUT
        f = NOTES[name]
        for rate in RATES:
            n = rate // 2
            left = rich(f, n, seed, rate)
            right = rich(f, n, seed, rate, shift=0.3)
            stereo = render(Octaver, pcm(left, right), rate, 2, patch=patch,
                            macros=ONLY1)
            mono = render(Octaver, pcm(left), rate, 1, patch=patch,
                          macros=ONLY1)
            self.assertLess(
                t5_margin(tail_part(channel(stereo, 2)), f, rate), 20.0)
            self.assertGreaterEqual(t5_margin(tail_part(mono), f, rate),
                                    20.0)

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


class TheSurface(TestCase):
    """The controls, the wire, latency, tail, reset and tempo."""

    def _fresh(self, rate=48000, channels=1, **options):
        feed = kc.feed(array("h", bytes(4 * channels)), rate, channels)
        return Octaver(feed.port, sample_rate=rate, **options)

    def test_the_spans(self):
        e = self._fresh()
        self.assertEqual(e.MACRO_LABELS, ("Direct", "Octave 1", "Octave 2",
                                          "Tracking", "Tone 1", "Tone 2",
                                          "Sensitivity"))
        ends = ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (40.0, 400.0),
                (100.0, 2000.0), (40.0, 800.0), (-90.0, -40.0))
        for i, (low, high) in enumerate(ends):
            e.set_macro(i, 0)
            self.assertAlmostEqual(e.macro(i), low, places=9)
            e.set_macro(i, 127)
            self.assertAlmostEqual(e.macro(i), high, places=9)
        e.deinit()

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
        the ceiling found worst and at every patch."""
        import kit_ceiling
        rate = 48000
        amp = 3277
        worst = 0.0
        configs = [(None, k) for k in ((OCT1, 127), (OCT2, 127),
                                       (TONE1, 0))]
        configs += [(p, None) for p in sorted(Octaver.PATCHES)]
        for which in ("square", "sine"):
            values = kit_ceiling.material(which, rate, 1, amp)
            for patch, knob in configs:
                y = render(Octaver, values, rate, 1, patch=patch,
                           macros=(knob,) if knob else ())
                worst = max(worst, max(abs(v) for v in y) / float(amp))
        self.assertTrue(2.6 <= worst <= 2.8, worst)
        self.assertLessEqual(worst * 10.0 ** (
            Octaver.INPUT_CEILING_DBFS / 20.0), 1.0)


CLAIMS = (
    ("An octave down that is your own note: like the Boss OC-2, it turns "
     "every other cycle of what you play upside down, so the octave keeps "
     "your attack, your decay and your tone.",
     ("T1Divider.test_the_pitch_is_half_the_note",
      "T1Divider.test_the_onset_is_within_2_ms",
      "T2Multiplication.test_mono_every_window",
      "T3Dynamics.test_the_octave_follows_the_decay")),
    ("Direct, Octave 1 and Octave 2 are the three levels, each from 0 to 1.",
     "TheSurface.test_the_spans"),
    ("Tracking, from 40 to 400 Hz, moves the range of notes the divider "
     "follows.",
     ("TheSurface.test_the_spans", "T5Range.test_the_windows_mono")),
    ("Tone 1 (100 to 2000 Hz) and Tone 2 (40 to 800 Hz) are two-pole "
     "low-passes at the hertz they show, on the first and second octave.",
     ("TheSurface.test_the_spans",
      "T6Tone.test_tone_1_is_a_two_pole_low_pass",
      "T6Tone.test_tone_2_is_a_two_pole_low_pass")),
    ("Sensitivity, from -90 to -40 dBFS, is how quiet a note can get before "
     "the octaves stop.",
     ("TheSurface.test_the_spans",
      "T3Dynamics.test_silent_below_sensitivity")),
    ("Constructor values land on the nearest of each knob's 128 steps.",
     ("TheSurface.test_constructor_values_land_on_the_grid",
      "TheSurface.test_a_fresh_instance_reads_patch_0")),
    ("The octave is exactly half your note and sounds within 2 ms of it.",
     ("T1Divider.test_the_pitch_is_half_the_note",
      "T1Divider.test_the_onset_is_within_2_ms")),
    ("Octave 2 is Octave 1 divided again: two octaves down, not a fourth "
     "below the note.",
     "T4SecondOctave.test_two_octaves_down"),
    ("On low notes, to A2, the octave follows your note's decay within "
     "1 dB: it has no envelope of its own.",
     "T3Dynamics.test_the_octave_follows_the_decay"),
    ("Below Sensitivity the octaves are silent, with no ghost and no hum.",
     "T3Dynamics.test_silent_below_sensitivity"),
    ("With the Tones open the octave carries a fifth above it 4.4 dB "
     "quieter, as the pedal's multiplication does, wherever Tracking is "
     "set.",
     "T2Multiplication.test_mono_every_window"),
    ("Turning Tone 1 down thins that fifth more on high notes than on low "
     "ones.",
     "T6Tone.test_tone_1_is_a_two_pole_low_pass"),
    ("At patch 0, on a mono source, every note from low E (E2) to A4 "
     "divides cleanly, even with a strong second harmonic.",
     "T5Range.test_the_windows_mono"),
    ("The Bass patch covers E1 to G3, and High on the neck covers D3 to E5.",
     ("T5Range.test_the_windows_mono", "T5Range.test_the_windows_stereo")),
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
    ("A stereo source is clocked on its mid: with the right channel 45 "
     "degrees ahead of the left, the fifth sits 3.2 dB under the octave "
     "instead of 4.4, on both channels.",
     ("T2Multiplication.test_stereo_45_degrees",
      "T2Multiplication.test_in_phase_stereo_reads_as_mono")),
    ("So near the top of the range a stereo note whose channels cancel "
     "each other's fundamental can drop out: one stereo A4 in eight did, "
     "at patch 0.",
     ("T5Range.test_a_stereo_note_can_drop_out_at_the_top",
      "T5Range.test_the_windows_stereo")),
    ("The output can peak at 2.8 times the input (a square wave, with "
     "Octave 2 at full), so keep the input under -9 dBFS.",
     "TheSurface.test_the_peak_gain"),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "DECLARED:Octaver,E4-,P5"),
    ("With both octaves at 0 and Direct at 1 the output is the input, byte "
     "for byte.",
     "TheSurface.test_the_wire_is_the_input"),
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
