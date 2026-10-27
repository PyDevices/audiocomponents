"""`PitchShifter`'s trait and planted-fault tests.

Four traits: T1 the interval, T2 the splice's arrivals, T3 the repeats
shifted again, T4 the untouched dry. Each has its measurement, run over the
cells listed with it, and the same measurement shown red on a planted fault
of the same kind. `KIT_PLANTS` hands the plants to the kit, which shows
each one differs from the clean class and that no knob stop or patch
reproduces it.

Every law a measurement checks against is written out here, never taken
from the class: the ratio grid, the window and crossfade in frames, the
Delay and Feedback grids.

The unit tests run a share of each trait's cells; `figures()` runs every
cell the card names, eight seed sets each, and prints the evidence pack's
numbers. The module is numpy-free and imports on MicroPython and
CircuitPython, where `unittest` is absent: the kit reads `KIT_PLANTS`
there, and running the file with `--figures` prints the figures on
whichever interpreter runs it:

    MICROPYPATH=lib:tests/support micropython \\
        tests/test_cpython_effects_pitchshifter.py --figures T1
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

import kit_common as kc                                     # noqa: E402
from audioeffects import _component                         # noqa: E402
import audioeffects                                         # noqa: E402

VENDOR = "PyDevices"

RATES = (48000, 22050)
CHANNELS = (2, 1)
WINDOWS = (15.0, 30.0, 60.0)
BLOCK = 256
SEEDS = tuple(range(1, 9))
PITCH_I, FINE_I, MIX_I, DELAY_I, FEEDBACK_I = range(5)

PitchShifter = audioeffects.PitchShifter


# --------------------------------------------------------------------------
# The card's laws, written out independently of the class


def law_window(window_ms, rate):
    """The shifter's window in whole frames."""
    window_ms = min(60.0, max(15.0, window_ms))
    return int(math.floor(window_ms * rate / 1000.0 + 0.5))


def law_overlap(rate):
    """The crossfade: 4/3 ms in whole frames, 64 at 48 kHz."""
    return int(math.floor(rate * 4.0 / 3000.0 + 0.5))


def law_delay_ms(ms):
    """Delay on its 0-127 grid, 112.5 ms at the top."""
    return 112.5 * int(ms * 127.0 / 112.5 + 0.5) / 127.0


def law_frames(ms, rate):
    """The line's delay in whole frames, at least one."""
    return max(1, int(math.floor(law_delay_ms(ms) * rate / 1000.0 + 0.5)))


def law_feedback(feedback):
    """Feedback on its 0-127 grid, 0.95 at the top."""
    return 0.95 * int(feedback * 127.0 / 0.95 + 0.5) / 127.0


def law_step(pitch, fine=0.0):
    """The node's read rate nearest the interval, in 256ths."""
    return int(math.floor(2.0 ** ((pitch + fine / 100.0) / 12.0) * 256 + 0.5))


def law_ratio(pitch, fine=0.0):
    return law_step(pitch, fine) / 256.0


def wanted(pitch, fine=0.0):
    return 2.0 ** ((pitch + fine / 100.0) / 12.0)


# --------------------------------------------------------------------------
# Material and rendering: integer arithmetic, the same on every interpreter


class Lcg:
    def __init__(self, seed):
        self.state = (seed * 2654435761 + 1) & 0x7FFFFFFF

    def next(self):
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state >> 7

    def uniform(self, low, high):
        return low + (high - low) * (self.next() % 1000001) / 1000000.0


def rint(x):
    """Round half away from zero."""
    if x >= 0:
        return int(x + 0.5)
    return -int(-x + 0.5)


def sine(frames, hz, rate, amp, channels, phase=0.0, start=0):
    out = array("h", bytes(2 * (start + frames) * channels))
    w = 2.0 * math.pi * hz / rate
    for n in range(frames):
        v = rint(amp * math.sin(w * n + phase))
        for c in range(channels):
            out[(start + n) * channels + c] = v
    return out


def render(cls, values, rate, channels, frames, moves=None, **options):
    """`frames` frames of a fresh instance fed `values` in 256-frame blocks
    and then silence; `moves` maps a pull index to a callable."""
    feed = kc.feed(values, rate, channels)
    e = cls(feed.port, **options)
    try:
        return kc.samples(kc.render(e, frames, moves))
    finally:
        e.deinit()


def first_nonzero(out, channels, lo, hi):
    """The first frame in [lo, hi) with a non-zero sample, or None."""
    for n in range(lo, min(hi, len(out) // channels)):
        for c in range(channels):
            if out[n * channels + c]:
                return n
    return None


# --------------------------------------------------------------------------
# Planted faults


class LinearRatio(PitchShifter):
    """T1: the speed is linear in the interval between the stops,
    1 + n/12 up and 1 + n/24 down, equal at 0 and +-12."""

    def _ratio(self, semitones):
        if semitones >= 0.0:
            return 1.0 + semitones / 12.0
        return 1.0 + semitones / 24.0


class WindowAt48k(PitchShifter):
    """T2: the window turned into frames at 48 kHz whatever the rate."""

    def _window_frames(self, window_ms):
        return int(math.floor(window_ms * 48.0 + 0.5))


class FlatLoop(PitchShifter):
    """T3: the loop's splicer is never engaged, so every repeat is the
    first pass's interval again."""

    def _loop_semitones(self, step):
        return 0.0


class DryThroughShifter(PitchShifter):
    """T4: the dry is the shifter's own, through its `mix` and its knee,
    instead of the Splitter's tap."""

    def _levels(self):
        mix = self._mix()
        self._shift.mix = min(1.0, mix) * 0.5
        voices = self._mixer.voice
        voices[0].level = 0.0
        voices[1].level = 1.0


#: The kit's plant table. T2's plant shows only off 48 kHz; T3's only
#: where Feedback is up, at the first patch that has it.
KIT_PLANTS = {
    "T1": LinearRatio,
    "T2": (WindowAt48k, None, {"rate": 22050}),
    "T3": (FlatLoop, 4),
    "T4": DryThroughShifter,
}


# --------------------------------------------------------------------------
# T1: the interval


T1_PITCHES = (-12, -11, -7, -5, -1, 0, 1, 5, 7, 12)
T1_CELLS = tuple((p, 0.0) for p in T1_PITCHES) + ((0, -50.0), (0, 50.0))


def t1_read(cls, rate, channels, window_ms, pitch, fine):
    """The measured speed over the wanted one, and the crossings counted.

    A sine whose period divides the window, so a splice jumps whole
    periods; 0.6 s at Mix 2, Delay 0, Feedback 0, at -12 dBFS; upward zero
    crossings, interpolated, from 0.1 s."""
    window = law_window(window_ms, rate)
    k = max(1, int(200.0 * window / rate + 0.5))
    hz = k * float(rate) / window
    amp = rint(32767 * 10.0 ** (-12.0 / 20.0))
    frames = int(0.6 * rate)
    values = sine(frames, hz, rate, amp, channels)
    out = render(cls, values, rate, channels, frames, pitch=pitch,
                 fine=fine, mix=2.0, window_ms=window_ms)
    crossings = []
    for n in range(int(0.1 * rate), frames - 1):
        a = out[n * channels]
        b = out[(n + 1) * channels]
        if a < 0 <= b:
            crossings.append(n + float(-a) / (b - a))
    if len(crossings) < 10:
        return None, len(crossings)
    measured = (len(crossings) - 1) * rate / (crossings[-1] - crossings[0])
    return measured / hz / wanted(pitch, fine), len(crossings)


def t1_cells(full=False):
    """(rate, channels, window, pitch, fine). The unit test runs every
    interval at every rate, channel count and window: 144 short renders."""
    for rate in RATES:
        for channels in CHANNELS:
            for window in WINDOWS:
                for pitch, fine in T1_CELLS:
                    yield rate, channels, window, pitch, fine


# --------------------------------------------------------------------------
# T2: the splice's arrivals


T2_PITCHES = ((-12, 0.0), (-5, 0.0), (0, 0.0), (7, 0.0), (12, 0.0),
              (0, 50.0))
T2_DELAYS = (0.0, 60.0, 100.0)


def t2_read(cls, rate, channels, window_ms, pitch, fine, delay_ms, seed,
            clicks=200):
    """Each click's arrival, frames after the line's delay, or None for a
    click that never arrived.

    Single full-scale clicks at random spacings of 1.05 to 1.5 x (W + O),
    Mix 2, Feedback 0. An arrival is the first non-zero output frame in
    [click + D, next click + D)."""
    window = law_window(window_ms, rate)
    overlap = law_overlap(rate)
    span = window + overlap
    delay = law_frames(delay_ms, rate)
    rng = Lcg(seed * 7919 + rate + channels)
    at = []
    n = BLOCK
    for _ in range(clicks):
        at.append(n)
        n += int(rng.uniform(1.05, 1.5) * span)
    end = n
    frames = end + delay + 2 * span
    values = array("h", bytes(2 * frames * channels))
    for c in at:
        for ch in range(channels):
            values[c * channels + ch] = 32767
    out = render(cls, values, rate, channels, frames, pitch=pitch, fine=fine,
                 mix=2.0, delay_ms=delay_ms, window_ms=window_ms)
    arrivals = []
    for i, c in enumerate(at):
        nxt = at[i + 1] if i + 1 < len(at) else end
        hit = first_nonzero(out, channels, c + delay, nxt + delay)
        arrivals.append(None if hit is None else hit - c - delay)
    return arrivals


def t2_verdict(arrivals, rate, window_ms, pitch, fine):
    """The card's bars on one seed set: a list of what failed, empty when
    it holds, and the numbers."""
    window = law_window(window_ms, rate)
    overlap = law_overlap(rate)
    got = [a for a in arrivals if a is not None]
    fails = []
    if law_step(pitch, fine) == 256:
        if len(got) != len(arrivals) or any(a != overlap for a in got):
            fails.append("unity: not every click exactly D + O late")
        return fails, {"arrived": len(got) / float(len(arrivals))}
    ratio = law_ratio(pitch, fine)
    figures = {"arrived": len(got) / float(len(arrivals))}
    if not got:
        return ["no click arrived"], figures
    late = max(got)
    early = min(got)
    figures["max"] = late / (window / max(ratio, 1.0))
    figures["min"] = early / float(window)
    figures["past"] = late - (window + overlap)
    if figures["arrived"] < 0.3:
        fails.append("arrived %.2f < 0.3" % figures["arrived"])
    if late > window + overlap:
        fails.append("an arrival %d past W + O %d" % (late, window + overlap))
    if late < 0.85 * window / max(ratio, 1.0):
        fails.append("max %.3f of W / max(r, 1)" % figures["max"])
    if early > 0.2 * window:
        fails.append("min %.3f of W" % figures["min"])
    return fails, figures


def t2_cells(full=False):
    """(rate, channels, window, (pitch, fine), delay, seeds). Every interval
    and Delay at 48 kHz stereo and the default window; every rate, channel
    count and window at each interval, Delay rotating. The unit test runs
    two seed sets a cell and eight at the worst cells the card names; the
    figures run eight everywhere."""
    seen = set()
    for interval in T2_PITCHES:
        for delay in T2_DELAYS:
            key = (48000, 2, 30.0, interval, delay)
            seen.add(key)
            yield key + ((SEEDS if full else SEEDS[:2]),)
    turn = 0
    for rate in RATES:
        for channels in CHANNELS:
            for window in WINDOWS:
                for interval in T2_PITCHES:
                    delay = T2_DELAYS[turn % 3]
                    turn += 1
                    key = (rate, channels, window, interval, delay)
                    if key in seen:
                        continue
                    seen.add(key)
                    worst = (interval == (12, 0.0) and rate == 48000
                             and window == 60.0)
                    seeds = SEEDS if (full or worst) else SEEDS[:1]
                    yield key + (seeds,)


# --------------------------------------------------------------------------
# T3: the repeats, shifted again


T3_PITCHES = (-7, -5, 5, 7, 12)
T3_FEEDBACKS = (0.3, 0.6, 0.9)
T3_DELAY_MS = 100.0
CENTS_STEP = 10.0


def hann_burst(frames, hz, rate, amp, phase):
    out = []
    w = 2.0 * math.pi * hz / rate
    for n in range(frames):
        g = 0.5 - 0.5 * math.cos(2.0 * math.pi * n / (frames - 1))
        out.append(rint(amp * g * math.sin(w * n + phase)))
    return out


def goertzel_power(values, hz, rate):
    coeff = 2.0 * math.cos(2.0 * math.pi * hz / rate)
    s1 = s2 = 0.0
    for x in values:
        s0 = x + coeff * s1 - s2
        s2 = s1
        s1 = s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


def strongest(values, low, high, rate):
    """The frequency in [low, high], 10-cent steps, with the most power."""
    if low > high:
        low, high = high, low
    steps = int(1200.0 * math.log(high / low) / math.log(2.0) / CENTS_STEP)
    best = None
    best_hz = low
    for i in range(steps + 1):
        hz = low * 2.0 ** (i * CENTS_STEP / 1200.0)
        p = goertzel_power(values, hz, rate)
        if best is None or p > best:
            best = p
            best_hz = hz
    return best_hz


def t3_read(cls, rate, channels, window_ms, pitch, feedback, seed):
    """Per pass k = 1, 2, 3: (error in cents from f r^k, energy over one
    repeat period round its centre).

    A 40 ms Hann sine burst at -8 dBFS, f in 300-600 Hz and a random phase
    per seed; Mix 2, Delay 100 ms. Pass k's 40 ms gate (Hann-weighted) is
    centred at the burst's centre + D + (W + O)/2 + (k - 1)(D + (W + O)/2)."""
    rng = Lcg(seed * 104729 + rate + channels + pitch)
    hz = rng.uniform(300.0, 600.0)
    phase = rng.uniform(0.0, 2.0 * math.pi)
    window = law_window(window_ms, rate)
    overlap = law_overlap(rate)
    delay = law_frames(T3_DELAY_MS, rate)
    period = delay + (window + overlap) / 2.0
    gate = int(0.04 * rate)
    start = BLOCK
    burst = hann_burst(gate, hz, rate, rint(32767 * 10.0 ** (-8.0 / 20.0)),
                       phase)
    centre = start + gate / 2.0
    frames = int(centre + 3.5 * period + gate) + BLOCK
    values = array("h", bytes(2 * frames * channels))
    for n, v in enumerate(burst):
        for c in range(channels):
            values[(start + n) * channels + c] = v
    out = render(cls, values, rate, channels, frames, pitch=pitch, mix=2.0,
                 delay_ms=T3_DELAY_MS, feedback=feedback,
                 window_ms=window_ms)
    ratio = law_ratio(pitch)
    taper = [0.5 - 0.5 * math.cos(2.0 * math.pi * n / (gate - 1))
             for n in range(gate)]
    passes = []
    for k in (1, 2, 3):
        mid = centre + period * k
        lo = int(mid - gate / 2.0)
        piece = [out[(lo + n) * channels] * taper[n] for n in range(gate)]
        peak = strongest(piece, hz * ratio ** (k - 1), hz * ratio ** (k + 1),
                         rate)
        error = 1200.0 * math.log(peak / (hz * ratio ** k)) / math.log(2.0)
        energy = 0.0
        for n in range(int(mid - period / 2.0), int(mid + period / 2.0)):
            for c in range(channels):
                v = out[n * channels + c]
                energy += v * v
        passes.append((error, energy))
    return passes


def t3_verdict(passes, pitch, feedback, window_ms):
    """The card's bars: each pass nearest r^k, within half the interval;
    and pass k's energy at least Feedback^(2(k-1)) of pass 1's, less
    15 dB (pass 2 only at the 60 ms window)."""
    fails = []
    bar = abs(pitch) * 50.0
    played = law_feedback(feedback)
    first = passes[0][1]
    levels = []
    for k, (error, energy) in enumerate(passes, 1):
        if abs(error) >= bar:
            fails.append("pass %d %.0f cents off" % (k, error))
        if k == 1:
            continue
        if first <= 0.0:
            fails.append("pass 1 silent")
            continue
        db = 10.0 * math.log(max(energy, 1e-30) / first) / math.log(10.0)
        want = 20.0 * (k - 1) * math.log(played) / math.log(10.0)
        levels.append(db - want)
        if k == 3 and window_ms >= 60.0:
            continue
        if db < want - 15.0:
            fails.append("pass %d %.1f dB below Feedback^%d" % (
                k, db - want, k - 1))
    return fails, levels


def t3_cells(full=False):
    """(rate, channels, window, pitch, feedback, seeds). Every interval and
    Feedback at 48 kHz stereo and the default window; every rate, channel
    count and window at each interval, Feedback rotating. Two seed sets a
    cell in the unit test, eight in the figures."""
    seen = set()
    for pitch in T3_PITCHES:
        for feedback in T3_FEEDBACKS:
            key = (48000, 2, 30.0, pitch, feedback)
            seen.add(key)
            yield key + ((SEEDS if full else SEEDS[:2]),)
    turn = 0
    for rate in RATES:
        for channels in CHANNELS:
            for window in WINDOWS:
                for pitch in T3_PITCHES:
                    feedback = T3_FEEDBACKS[turn % 3]
                    turn += 1
                    key = (rate, channels, window, pitch, feedback)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield key + ((SEEDS if full else SEEDS[:1]),)


# --------------------------------------------------------------------------
# T4: the dry, untouched


T4_MIXES = (0.25, 0.5, 1.0)


def t4_material(frames, channels, seed):
    """A full-scale ramp interleaved, frame by frame, with full-scale
    noise, each channel its own noise."""
    rng = Lcg(seed)
    out = array("h", bytes(2 * frames * channels))
    for n in range(frames):
        for c in range(channels):
            if n % 2 == 0:
                v = -32768 + (n * 65535) // (frames - 1)
            else:
                v = rng.next() % 65536 - 32768
            out[n * channels + c] = v
    return out


def t4_read(cls, rate, channels, window_ms, mix, pitch, delay_ms, feedback,
            seed, frames=8192):
    """The worst |out_m - x - m out_2| over every sample where
    |x + m out_2| <= 32767, from fresh instances at Mix m and at Mix 2."""
    values = t4_material(frames, channels, seed)
    common = dict(pitch=pitch, delay_ms=delay_ms, feedback=feedback,
                  window_ms=window_ms)
    out_m = render(cls, values, rate, channels, frames, mix=mix, **common)
    out_2 = render(PitchShifter, values, rate, channels, frames, mix=2.0,
                   **common)
    worst = 0
    for i in range(frames * channels):
        x = values[i]
        wet = mix * out_2[i]
        if abs(x + wet) > 32767:
            continue
        d = abs(out_m[i] - x - wet)
        if d > worst:
            worst = d
    return worst


def t4_cells(full=False):
    """(rate, channels, window, mix, pitch, delay, feedback, seeds)."""
    for mix in T4_MIXES:
        for pitch in (-5, 7):
            for delay in (0.0, 60.0):
                for feedback in (0.0, 0.6):
                    yield (48000, 2, 30.0, mix, pitch, delay, feedback,
                           SEEDS if full else SEEDS[:2])
    for rate in RATES:
        for channels in CHANNELS:
            for window in WINDOWS:
                if (rate, channels, window) == (48000, 2, 30.0):
                    continue
                yield (rate, channels, window, 1.0, 7, 60.0, 0.6,
                       SEEDS if full else SEEDS[:1])


# --------------------------------------------------------------------------
# Running without `audiocore.get_buffer`


def without_get_buffer(build, moves, frames=4096, seed=3, rate=48000,
                       channels=2, hide=True):
    """Render with `audiocore.get_buffer` hidden from the class, as on a
    CircuitPython board build, while it builds and while it moves; with
    `hide` false, the same render with it in place."""
    import types
    from audioeffects import pitchshifter as module
    real = module.audiocore
    fake = types.ModuleType("audiocore")
    for name in dir(real):
        if name != "get_buffer" or not hide:
            setattr(fake, name, getattr(real, name))

    def hidden(action):
        def run(e):
            module.audiocore = _component.audiocore = fake
            try:
                action(e)
            finally:
                module.audiocore = _component.audiocore = real
        return run

    rng = Lcg(seed)
    values = array("h", [rng.next() % 40001 - 20000
                         for _ in range(frames * channels)])
    feed = kc.feed(values, rate, channels)
    module.audiocore = _component.audiocore = fake
    try:
        e = build(feed.port)
    finally:
        module.audiocore = _component.audiocore = real
    try:
        out = kc.samples(kc.render(
            e, frames, dict((k, hidden(f)) for k, f in moves.items())))
    finally:
        e.deinit()
    return values, out


GET_BUFFER_CASES = (
    ("built at the defaults", PitchShifter, {}),
    ("reset before the first pull", PitchShifter, {0: lambda e: e.reset()}),
    ("reset twice before the first pull", PitchShifter,
     {0: lambda e: (e.reset(), e.reset())}),
    ("built at Mix 0, then patch 0", lambda src: PitchShifter(src, mix=0.0),
     {3: lambda e: e.program_change(0)}),
    ("built at Mix 0, reset", lambda src: PitchShifter(src, mix=0.0),
     {3: lambda e: e.reset()}),
    ("Mix 0 before the first block, back", PitchShifter,
     {0: lambda e: e.set_macro(MIX_I, 0), 4: lambda e: e.set_macro(MIX_I, 64)}),
    ("Mix 0 after playing, reset twice", PitchShifter,
     {2: lambda e: e.set_macro(MIX_I, 0), 6: lambda e: (e.reset(), e.reset())}),
    ("a patch change and a reset in one block", PitchShifter,
     {2: lambda e: (e.program_change(4), e.reset())}),
)


# --------------------------------------------------------------------------
# The tests


class TheAdoption(TestCase):
    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-10-13, so `create()` serves this one. Serve another class under the name and this goes red."""
        import audiocore
        import audioeffects
        from array import array
        self.assertIs(audioeffects.PitchShifter, PitchShifter)
        served = audioeffects.create(
            "PitchShifter",
            audiocore.RawSample(array("h", [0, 0] * 64), sample_rate=48000,
                                channel_count=2),
            48000)
        self.assertIsInstance(served, PitchShifter)
        served.deinit()


class TheSurface(TestCase):
    def test_macros_patches_tier_latency(self):
        self.assertEqual(PitchShifter.MACRO_LABELS,
                         ("Pitch", "Fine", "Mix", "Delay", "Feedback"))
        self.assertEqual(PitchShifter.MACRO_MODES,
                         {0: "BIPOLAR", 1: "BIPOLAR", 2: "BIPOLAR",
                          3: "UNIPOLAR", 4: "UNIPOLAR"})
        self.assertEqual(PitchShifter.TIER, _component.AUDIODSP)
        self.assertEqual(PitchShifter.CAPABILITIES, ())
        self.assertEqual(PitchShifter.LATENCY_SAMPLES, 0)

    def test_pitch_plays_whole_semitones(self):
        e = PitchShifter(kc.feed(array("h", bytes(16)), 48000, 2).port)
        try:
            reached = set()
            for midi in range(128):
                e.set_macro(PITCH_I, midi)
                value = e.macro(PITCH_I)
                self.assertEqual(value, float(int(value)))
                position = _component.position_of_midi("BIPOLAR", midi)
                exact = -12.0 + 24.0 * position
                self.assertEqual(value, float(rint(exact)), midi)
                reached.add(int(value))
            self.assertEqual(reached, set(range(-12, 13)))
        finally:
            e.deinit()

    def test_fine_steps_are_the_ratio_grid(self):
        # Consecutive Fine positions land on consecutive 256ths, or the
        # same one: about 7 cents a step near unity, 13.5 near -12.
        self.assertAlmostEqual(1200.0 * math.log(257.0 / 256) / math.log(2),
                               6.75, places=2)
        self.assertAlmostEqual(1200.0 * math.log(129.0 / 128) / math.log(2),
                               13.47, places=2)
        for pitch, low, high in ((0, 249, 264), (-12, 124, 132)):
            e = PitchShifter(kc.feed(array("h", bytes(16)), 48000, 2).port,
                             pitch=pitch)
            try:
                steps = []
                for midi in range(128):
                    e.set_macro(FINE_I, midi)
                    steps.append(e._step)
                    self.assertEqual(
                        e._step, law_step(pitch, e.macro(FINE_I)), midi)
                for a, b in zip(steps, steps[1:]):
                    self.assertIn(b - a, (0, 1))
                self.assertEqual((steps[0], steps[-1]), (low, high))
            finally:
                e.deinit()

    def test_patches_are_the_card_settings_on_the_grid(self):
        card = {
            0: (7, 0, 1, 0, 0), 1: (12, 0, 1, 0, 0), 2: (-12, 0, 1, 0, 0),
            3: (0, 9, 1, 15, 0), 4: (7, 0, 1, 90, 0.55),
            5: (-5, 0, 1, 100, 0.55), 6: (7, 0, 2, 0, 0)}
        for index, values in card.items():
            want = tuple(
                _component.macro_of(PitchShifter._MACRO_RANGES[i], values[i],
                                    PitchShifter.MACRO_MODES[i])
                for i in range(5))
            self.assertEqual(PitchShifter.PATCHES[index][1], want, index)

    def test_a_fresh_instance_reads_patch_0(self):
        e = PitchShifter(kc.feed(array("h", bytes(16)), 48000, 2).port)
        try:
            self.assertEqual(tuple(e.get_macro(i) for i in range(5)),
                             PitchShifter.PATCHES[0][1])
            self.assertEqual(e.patch_index, 0)
        finally:
            e.deinit()

    def test_patches_play_the_same_whatever_the_constructor_said(self):
        # No constructor value is kept beside the grid, so a patch is the
        # same on every instance.
        values = sine(4096, 330.0, 48000, 9000, 2)
        for patch in sorted(PitchShifter.PATCHES):
            renders = []
            for options in ({}, dict(pitch=-3.4, fine=17.3, mix=0.37,
                                     delay_ms=13.3, feedback=0.71)):
                renders.append(render(PitchShifter, values, 48000, 2, 8192,
                                      patch=patch, **options))
            self.assertEqual(renders[0], renders[1], patch)

    def test_window_ms_is_set_at_construction(self):
        for rate in (48000, 44100, 22050):
            for asked, played in ((30.0, 30.0), (15.0, 15.0), (60.0, 60.0),
                                  (5.0, 15.0), (90.0, 60.0),
                                  (float("nan"), 30.0)):
                e = PitchShifter(kc.feed(array("h", bytes(16)), rate, 2).port,
                                 window_ms=asked)
                try:
                    self.assertEqual(e._window, law_window(played, rate))
                    self.assertEqual(e._overlap, law_overlap(rate))
                finally:
                    e.deinit()
        self.assertEqual(law_overlap(48000), 64)

    def test_mix_0_is_the_input(self):
        for channels in CHANNELS:
            rng = Lcg(5)
            values = array("h", [rng.next() % 65536 - 32768
                                 for _ in range(4096 * channels)])
            out = render(PitchShifter, values, 48000, channels, 4096,
                         mix=0.0)
            self.assertEqual(out, values)
            moves = {4: lambda e: e.set_macro(MIX_I, 0)}
            out = render(PitchShifter, values, 48000, channels, 4096,
                         moves=moves)
            self.assertEqual(out[4 * BLOCK * channels:],
                             values[4 * BLOCK * channels:])

    def test_mix_2_is_the_shifted_voice_alone(self):
        # At unity the shifted voice is the input D + O frames late, and
        # nothing else plays: no dry.
        for rate in RATES:
            for delay_ms in (0.0, 60.0, 112.5):
                late = law_frames(delay_ms, rate) + law_overlap(rate)
                rng = Lcg(9)
                frames = 8192
                values = array("h", [rng.next() % 50001 - 25000
                                     for _ in range(frames * 2)])
                out = render(PitchShifter, values, rate, 2, frames + late,
                             pitch=0.0, mix=2.0, delay_ms=delay_ms)
                self.assertEqual(out[:late * 2], array("h", bytes(4 * late)))
                self.assertEqual(out[late * 2:], values, (rate, delay_ms))

    def test_a_hot_input_reaches_the_rail_at_mix_1(self):
        values = sine(8192, 220.0, 48000, 32767, 2)
        out = render(PitchShifter, values, 48000, 2, 8192, pitch=0.0)
        self.assertEqual(max(out), 32767)
        self.assertEqual(min(out), -32768)

    def test_feedback_near_its_top_stacks_level_far_past_the_input(self):
        # A noise burst peaking at -10.3 dBFS (10000 of 32768), through
        # Feedback 127 with Delay 0 and Mix 2: at unison the repeats pile up
        # on each other and the shifted voice alone reaches the rail; at an
        # octave and a fourth or a fifth either way it comes within 6 dB of
        # it. Restated 2026-10-14 for audiodsp#245's splice fix, measured
        # at v0.6.6rc4: an octave up no longer reaches the rail (24 054 at
        # 48 kHz stereo, 21 738 at 22.05 kHz mono), and the lowest stack is
        # a fourth up at 22.05 kHz mono, 16 930 (-5.7 dBFS), where the bar
        # was 4 dB (20 675).
        close = 32768 * 10 ** (-6 / 20.0)
        for rate, channels in ((48000, 2), (22050, 1)):
            burst = rate // 10
            values = array("h", bytes(2 * burst * channels))
            state = 12345
            for i in range(burst * channels):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                values[i] = (state >> 8) % 20001 - 10000
            self.assertTrue(9900 < max(max(values), -min(values)) <= 10000)
            frames = 3 * rate
            padded = values + array("h", bytes(2 * (frames - burst)
                                               * channels))
            for pitch in (-12, -7, -5, 0, 5, 7, 12):
                out = render(PitchShifter, padded, rate, channels, frames,
                             pitch=float(pitch), mix=2.0, delay_ms=0.0,
                             feedback=0.95)
                peak = max(max(out), -min(out))
                where = (rate, channels, pitch, peak)
                if pitch == 0:
                    self.assertTrue(max(out) == 32767 or min(out) == -32768,
                                    where)
                else:
                    self.assertGreaterEqual(peak, close, where)

    def test_a_mono_source_is_one_channel_of_a_stereo_one(self):
        for rate in RATES:
            for options in ({}, dict(patch=4), dict(patch=5, window_ms=15.0),
                            dict(pitch=-12, mix=1.5, window_ms=60.0)):
                rng = Lcg(11)
                mono = array("h", [rng.next() % 40001 - 20000
                                   for _ in range(8192)])
                stereo = array("h", bytes(4 * 8192))
                for n in range(8192):
                    stereo[2 * n] = stereo[2 * n + 1] = mono[n]
                a = render(PitchShifter, mono, rate, 1, 16384, **options)
                b = render(PitchShifter, stereo, rate, 2, 16384, **options)
                # A Mixer voice at a level below 1 rounds a stereo frame
                # and a mono one a last bit apart.
                worst = max(abs(x - y) for x, y in zip(a, b[::2]))
                self.assertLessEqual(worst, 1, (rate, options))
                self.assertGreater(max(a), 1000)

    def test_no_latency(self):
        values = array("h", bytes(4 * 2048))
        values[2 * 700] = values[2 * 700 + 1] = 12000
        for patch in sorted(PitchShifter.PATCHES):
            out = render(PitchShifter, values, 48000, 2, 2048, patch=patch)
            if patch == 6:
                # The shifted voice alone has no dry to arrive on time.
                continue
            self.assertEqual(out[2 * 700], 12000, patch)
            self.assertEqual(out[2 * 699], 0, patch)
        e = PitchShifter(kc.feed(values, 48000, 2).port)
        try:
            self.assertEqual(e.latency_samples, 0)
        finally:
            e.deinit()

    def test_tail_samples(self):
        # The bound holds where the output is longest: every patch, and
        # Feedback at the top with Delay and the window at theirs.
        cases = [dict(patch=p) for p in sorted(PitchShifter.PATCHES)]
        cases.append(dict(feedback=0.95, delay_ms=112.5, window_ms=60.0,
                          pitch=12))
        cases.append(dict(feedback=0.95, delay_ms=112.5, window_ms=60.0,
                          pitch=-12))
        cases.append(dict(feedback=0.95, pitch=0, fine=0.0))
        for rate in RATES:
            for options in cases:
                rng = Lcg(13)
                frames = 4096
                values = array("h", [rng.next() % 65536 - 32768
                                     for _ in range(frames * 2)])
                feed = kc.feed(values, rate, 2)
                e = PitchShifter(feed.port, **options)
                try:
                    tail = e.tail_samples
                    stream = kc.Stream(e)
                    stream.to(frames + tail + 2 * BLOCK)
                    last = stream.last
                    self.assertLessEqual(last, frames + tail,
                                         (rate, options, tail))
                    self.assertGreater(last, frames, (rate, options))
                finally:
                    e.deinit()

    def test_tail_is_zero_at_mix_0(self):
        e = PitchShifter(kc.feed(array("h", bytes(16)), 48000, 2).port,
                         mix=0.0)
        try:
            self.assertEqual(e.tail_samples, 0)
        finally:
            e.deinit()

    def test_reset_empties_the_graph_and_returns_to_patch_0(self):
        # After a reset the class renders what a fresh instance renders
        # from that point of the source on.
        for rate in RATES:
            for channels in CHANNELS:
                rng = Lcg(17)
                frames = 16384
                values = array("h", [rng.next() % 40001 - 20000
                                     for _ in range(frames * channels)])
                at = 12 * BLOCK
                # Patch 6 moves a Mixer level (the dry goes to nothing), so
                # its voice must not wait for a zero crossing to come back.
                for patch in (5, 6):
                    feed = kc.feed(values, rate, channels)
                    e = PitchShifter(feed.port, patch=patch)
                    try:
                        kc.render(e, at)
                        e.reset()
                        self.assertEqual(e.patch_index, 0)
                        self.assertEqual(
                            tuple(e.get_macro(i) for i in range(5)),
                            PitchShifter.PATCHES[0][1])
                        after = kc.samples(kc.render(e, frames - at))
                    finally:
                        e.deinit()
                    fresh = render(PitchShifter, values[at * channels:],
                                   rate, channels, frames - at)
                    self.assertEqual(after, fresh, (rate, channels, patch))

    def test_the_tempo_is_never_read(self):
        reads = []

        def transport():
            reads.append(1)
            return (True, 0.0, 120.0, 4, 4)

        e = PitchShifter.create(kc.feed(array("h", bytes(16)), 48000, 2).port,
                                48000, transport=transport)
        try:
            for i in range(5):
                for v in (0, 64, 127):
                    e.set_macro(i, v)
                    e.transport_changed()
            for patch in PitchShifter.PATCHES:
                e.program_change(patch)
            e.reset()
            self.assertEqual(e.capabilities, ())
        finally:
            e.deinit()
        self.assertEqual(reads, [])

    def test_without_get_buffer_plays_what_it_plays_with_it(self):
        for channels in CHANNELS:
            for what, build, moves in GET_BUFFER_CASES:
                _, plain = without_get_buffer(build, moves, channels=channels,
                                              hide=False)
                _, hidden = without_get_buffer(build, moves,
                                               channels=channels)
                self.assertEqual(plain, hidden, (what, channels))


def played(values, rate, channels, blocks, moves, **options):
    """`blocks` pulls of an instance built with `options` and fed `values`,
    `moves` mapping a pull index to a callable."""
    e = PitchShifter(kc.feed(values, rate, channels).port, **options)
    try:
        return kc.samples(kc.render(e, blocks * BLOCK, moves))
    finally:
        e.deinit()


class TheRestart(TestCase):
    """What an instance plays after a control stranded its graph, or after
    a reset, against what a fresh instance plays from that point on."""

    def test_a_control_touched_at_mix_0_leaves_the_graph_playing(self):
        # Built at Mix 0, a control touched there strands the graph; the
        # first Mix move that wires it must not leave that mark behind, or
        # the next ordinary Mix move empties the shifter mid-playback.
        for rate, channels in ((48000, 2), (22050, 1)):
            rng = Lcg(23)
            values = array("h", [rng.next() % 40001 - 20000
                                 for _ in range(60 * BLOCK * channels)])

            def touch(e):
                position = e.get_macro(DELAY_I)
                e.set_macro(DELAY_I, 30)
                e.set_macro(DELAY_I, position)
            moves = {2: lambda e: e.set_macro(MIX_I, 64),
                     30: lambda e: e.set_macro(MIX_I, 80)}
            plain = played(values, rate, channels, 60, moves, mix=0.0,
                           feedback=0.5, delay_ms=20.0)
            e = PitchShifter(kc.feed(values, rate, channels).port, mix=0.0,
                             feedback=0.5, delay_ms=20.0)
            try:
                touch(e)
                touched = kc.samples(kc.render(e, 60 * BLOCK, moves))
            finally:
                e.deinit()
            self.assertEqual(touched, plain, (rate, channels))

    def test_a_return_from_mix_0_is_a_fresh_instance_at_that_mix(self):
        # The voices' new levels hold from the first frame: a dry that
        # waited for its next zero crossing would play at unity on a DC
        # input, where a fresh Mix 2 instance plays nothing yet.
        for rate, channels in ((48000, 2), (22050, 1)):
            rng = Lcg(29)
            noisy = array("h", [rng.next() % 40001 - 20000
                                for _ in range(40 * BLOCK * channels)])
            dc = array("h", [6000] * (40 * BLOCK * channels))
            for name, values in (("noise", noisy), ("dc", dc)):
                moves = {12: lambda e: e.set_macro(MIX_I, 0),
                         18: lambda e: e.set_macro(MIX_I, 127)}
                got = played(values, rate, channels, 40, moves)
                fresh = render(PitchShifter, values[18 * BLOCK * channels:],
                               rate, channels, 22 * BLOCK, mix=2.0)
                self.assertEqual(got[18 * BLOCK * channels:], fresh,
                                 (rate, channels, name))

    def test_a_level_set_before_the_first_pull_plays_from_the_first_frame(
            self):
        # A patch or a Mix move before anything has been pulled: the voices
        # start at the new level, not a block at the old one, byte for byte
        # what an instance built at that setting plays. A DC input shows a
        # dry that waited for a zero crossing; the 40 Hz sine one that
        # crossed late.
        for rate, channels in ((48000, 2), (22050, 1)):
            frames = 40 * BLOCK
            dc = array("h", [6000] * (frames * channels))
            slow = sine(frames, 40.0, rate, 12000, channels, phase=0.3)
            for name, values in (("dc", dc), ("40 Hz", slow)):
                for patch in range(len(PitchShifter.PATCHES)):
                    got = played(values, rate, channels, 40,
                                 {0: lambda e, p=patch: e.program_change(p)})
                    fresh = render(PitchShifter, values, rate, channels,
                                   frames, patch=patch)
                    self.assertEqual(got, fresh, (rate, channels, name,
                                                  "patch", patch))
                for midi in (0, 1, 32, 63, 64, 65, 96, 126, 127):
                    mix = _component.macro_value(
                        (0.0, 2.0), _component.position_of_midi(
                            "BIPOLAR", midi))
                    got = played(values, rate, channels, 40,
                                 {0: lambda e, m=midi: e.set_macro(MIX_I, m)})
                    fresh = render(PitchShifter, values, rate, channels,
                                   frames, mix=mix)
                    self.assertEqual(got, fresh, (rate, channels, name,
                                                  "mix", midi))
                got = played(values, rate, channels, 40,
                             {0: lambda e: (e.reset(), e.program_change(6))})
                fresh = render(PitchShifter, values, rate, channels, frames,
                               patch=6)
                self.assertEqual(got, fresh, (rate, channels, name,
                                              "reset, patch 6"))

    def test_mix_0_and_a_patch_together_is_a_fresh_instance_at_that_patch(
            self):
        for rate, channels in ((48000, 2), (22050, 1)):
            rng = Lcg(31)
            values = array("h", [rng.next() % 40001 - 20000
                                 for _ in range(40 * BLOCK * channels)])

            def both(e):
                e.set_macro(MIX_I, 0)
                e.program_change(6)
            got = played(values, rate, channels, 40, {12: both})
            fresh = render(PitchShifter, values[12 * BLOCK * channels:],
                           rate, channels, 28 * BLOCK, patch=6)
            self.assertEqual(got[12 * BLOCK * channels:], fresh,
                             (rate, channels))

    def test_a_mix_sweep_after_a_reset_does_not_empty_the_repeats(self):
        # A host that took the output once and keeps the node: a reset does
        # not hand the re-arm window back, so Mix moves that change a level
        # while it plays are ordinary moves and the repeats carry on.
        for rate, channels in ((48000, 2), (22050, 1)):
            rng = Lcg(41)
            blocks = 20
            values = array("h", bytes(2 * blocks * BLOCK * channels))
            for n in range(6 * BLOCK * channels):
                values[n] = rng.next() % 40001 - 20000
            sweep = (70, 76, 82, 88, 94, 100, 106, 112, 118, 124)
            energies = []
            rearms = []
            for with_reset in (True, False):
                e = PitchShifter(kc.feed(values, rate, channels).port)
                try:
                    count = [0]
                    rearm = e._rearm

                    def wrapped(count=count, rearm=rearm):
                        count[0] += 1
                        rearm()
                    node = e.output
                    out = []
                    for k in range(blocks):
                        if k == 3:
                            if with_reset:
                                e.reset()
                            e.set_macro(FEEDBACK_I, 120)
                            e.set_macro(DELAY_I, 20)
                        if k == 5:
                            e._rearm = wrapped
                        if k >= 7:
                            e.set_macro(MIX_I, sweep[k - 7] if k < 17 else 64)
                        out.append(bytes(kc.audiocore.get_buffer(node)[1]))
                    rearms.append(count[0])
                    energies.append(sum(
                        sum(x * x for x in memoryview(b).cast("h"))
                        for b in out[8:17]))
                finally:
                    e.deinit()
            self.assertEqual(rearms, [0, 0], (rate, channels))
            self.assertGreater(energies[0], 0.25 * energies[1],
                               (rate, channels, energies))

    def test_a_patch_right_after_a_reset_plays_the_old_level_at_first(self):
        # The limit the docstring discloses beside the early output read:
        # a reset does not hand the first-block window back, so a patch
        # loaded right after one plays its first block (256 frames) at the
        # old level and nothing after it.
        for rate, channels in ((48000, 2), (22050, 1)):
            blocks = 30
            dc = array("h", [6000] * (blocks * BLOCK * channels))
            later = dc[12 * BLOCK * channels:]
            got = played(dc, rate, channels, blocks,
                         {12: lambda e: (e.reset(), e.program_change(6))})
            fresh = render(PitchShifter, later, rate, channels,
                           (blocks - 12) * BLOCK, patch=6)
            got = got[12 * BLOCK * channels:]
            differ = [n for n in range(len(fresh) // (2 * channels))
                      if got[n * channels:(n + 1) * channels]
                      != fresh[n * channels:(n + 1) * channels]]
            self.assertTrue(differ, (rate, channels))
            self.assertLess(max(differ), BLOCK, (rate, channels))

    def test_a_patch_right_after_a_return_from_mix_0_plays_the_old_level(
            self):
        # The return from Mix 0 re-arms the graph at the Mix it comes back
        # to (test_a_return_from_mix_0_is_a_fresh_instance_at_that_mix); a
        # patch loaded after it, once the output has been taken, is an
        # ordinary move and plays its first block at the old level.
        for rate, channels in ((48000, 2), (22050, 1)):
            blocks = 30
            dc = array("h", [6000] * (blocks * BLOCK * channels))

            def back(e):
                e.set_macro(MIX_I, 64)
                e.program_change(6)
            got = played(dc, rate, channels, blocks,
                         {10: lambda e: e.set_macro(MIX_I, 0), 18: back})
            fresh = render(PitchShifter, dc[18 * BLOCK * channels:], rate,
                           channels, (blocks - 18) * BLOCK, patch=6)
            got = got[18 * BLOCK * channels:]
            differ = [n for n in range(len(fresh) // (2 * channels))
                      if got[n * channels:(n + 1) * channels]
                      != fresh[n * channels:(n + 1) * channels]]
            self.assertTrue(differ, (rate, channels))
            self.assertLess(max(differ), BLOCK, (rate, channels))

    def test_only_a_move_that_changes_a_voice_level_re_arms(self):
        # Before the output is first taken, Pitch, Fine, Delay, Feedback and
        # a patch that leaves both Mixer levels where they are do not re-arm
        # the graph (a re-arm primes the shifter again); a move that changes
        # a level does, once, and the same level again does not.
        def counted(e):
            count = [0]
            rearm = e._rearm

            def wrapped():
                count[0] += 1
                rearm()
            e._rearm = wrapped
            return count

        def mix_of(midi):
            return _component.macro_value(
                (0.0, 2.0), _component.position_of_midi("BIPOLAR", midi))
        for rate, channels in ((48000, 2), (22050, 1)):
            rng = Lcg(37)
            frames = 24 * BLOCK
            values = array("h", [rng.next() % 40001 - 20000
                                 for _ in range(frames * channels)])
            neutral = (
                ("pitch", lambda e: e.set_macro(PITCH_I, 127),
                 {"pitch": 12.0}),
                ("delay", lambda e: e.set_macro(DELAY_I, 64),
                 {"delay_ms": 112.5 * 64 / 127}),
                ("mix at unity", lambda e: e.set_macro(MIX_I, 64), {}),
                ("patch 4", lambda e: e.program_change(4), {"patch": 4}),
                ("patch 4 macro by macro",
                 lambda e: [e.set_macro(i, m) for i, m in
                            enumerate(PitchShifter.PATCHES[4][1])],
                 {"patch": 4}),
                ("patch 3 and back", lambda e: (e.program_change(3),
                                                e.program_change(0)), {}),
            )
            for name, move, options in neutral:
                e = PitchShifter(kc.feed(values, rate, channels).port)
                try:
                    count = counted(e)
                    move(e)
                    got = kc.samples(kc.render(e, frames))
                finally:
                    e.deinit()
                self.assertEqual(count[0], 0, (rate, channels, name))
                fresh = render(PitchShifter, values, rate, channels,
                               frames, **options)
                self.assertEqual(got, fresh, (rate, channels, name))
            for index, midi in ((FINE_I, 3), (FEEDBACK_I, 90)):
                e = PitchShifter(kc.feed(values, rate, channels).port)
                try:
                    count = counted(e)
                    e.set_macro(index, midi)
                finally:
                    e.deinit()
                self.assertEqual(count[0], 0, (rate, channels, index))
            changing = (
                ("mix 127", lambda e: e.set_macro(MIX_I, 127),
                 {"mix": 2.0}),
                ("mix 32", lambda e: e.set_macro(MIX_I, 32),
                 {"mix": mix_of(32)}),
                ("patch 6", lambda e: e.program_change(6), {"patch": 6}),
            )
            for name, move, options in changing:
                e = PitchShifter(kc.feed(values, rate, channels).port)
                try:
                    count = counted(e)
                    move(e)
                    first = count[0]
                    move(e)
                    got = kc.samples(kc.render(e, frames))
                finally:
                    e.deinit()
                self.assertEqual((first, count[0]), (1, 1),
                                 (rate, channels, name))
                fresh = render(PitchShifter, values, rate, channels, frames,
                               **options)
                self.assertEqual(got, fresh, (rate, channels, name))
            # Once the output has been taken, no move re-arms.
            e = PitchShifter(kc.feed(values, rate, channels).port)
            try:
                count = counted(e)
                e.output
                e.program_change(6)
                e.set_macro(MIX_I, 127)
            finally:
                e.deinit()
            self.assertEqual(count[0], 0, (rate, channels, "taken"))

    def test_an_output_taken_before_a_patch_plays_the_old_level_at_first(
            self):
        # The limit the docstring discloses: a host that takes the output
        # before it loads a patch hears the first block (256 frames) at the
        # old level, and nothing after it. The class cannot see a pull, so
        # it has stopped re-arming once the output has been taken.
        for rate, channels in ((48000, 2), (22050, 1)):
            frames = 40 * BLOCK
            dc = array("h", [6000] * (frames * channels))
            slow = sine(frames, 40.0, rate, 12000, channels, phase=0.3)
            for name, values in (("dc", dc), ("40 Hz", slow)):
                e = PitchShifter(kc.feed(values, rate, channels).port)
                try:
                    e.output
                    e.program_change(6)
                    got = kc.samples(kc.render(e, frames))
                finally:
                    e.deinit()
                fresh = render(PitchShifter, values, rate, channels, frames,
                               patch=6)
                differ = [n for n in range(frames)
                          if got[n * channels:(n + 1) * channels]
                          != fresh[n * channels:(n + 1) * channels]]
                self.assertTrue(differ, (rate, channels, name))
                self.assertLess(max(differ), BLOCK, (rate, channels, name))

    def test_the_voice_at_unity_after_a_pitch_move_sits_where_the_splice_left_it(
            self):
        # From a fresh start (test_mix_2_is_the_shifted_voice_alone) or a
        # reset the unity voice is O frames late. After Pitch has moved
        # away and back it is wherever the splice left it, up to W + O.
        for rate, channels in ((48000, 2), (22050, 1)):
            window = law_window(30.0, rate)
            overlap = law_overlap(rate)
            frames = 40 * BLOCK
            at = 30 * BLOCK
            seen = []
            for away, back in ((5, 8), (3, 4), (5, 9), (2, 11)):
                values = array("h", bytes(2 * frames * channels))
                for c in range(channels):
                    values[at * channels + c] = 20000
                moves = {away: lambda e: e.set_macro(PITCH_I, 101),
                         back: lambda e: e.set_macro(PITCH_I, 64)}
                out = played(values, rate, channels, 40, moves, pitch=0.0,
                             mix=2.0)
                first = first_nonzero(out, channels, at, frames)
                self.assertIsNotNone(first)
                seen.append(first - at)
            for late in seen:
                self.assertTrue(0 <= late <= window + overlap, (rate, late))
            self.assertTrue(any(late != overlap for late in seen), seen)


class T1TheInterval(TestCase):
    def test_pitch_moves_by_the_semitones_it_reads(self):
        for rate, channels, window, pitch, fine in t1_cells():
            ratio, count = t1_read(PitchShifter, rate, channels, window,
                                   pitch, fine)
            cell = (rate, channels, window, pitch, fine)
            self.assertIsNotNone(ratio, (cell, count))
            self.assertLess(abs(ratio - 1.0), 0.005, cell)

    def test_linear_ratio_is_red(self):
        for pitch in (7, -5):
            ratio, _ = t1_read(LinearRatio, 48000, 2, 30.0, pitch, 0.0)
            self.assertGreater(abs(ratio - 1.0), 0.04, pitch)


class T2TheSplice(TestCase):
    def test_arrivals_drift_between_at_once_and_one_window_late(self):
        for rate, channels, window, (pitch, fine), delay, seeds in \
                t2_cells():
            for seed in seeds:
                arrivals = t2_read(PitchShifter, rate, channels, window,
                                   pitch, fine, delay, seed)
                fails, _ = t2_verdict(arrivals, rate, window, pitch, fine)
                self.assertEqual(fails, [], (rate, channels, window, pitch,
                                             fine, delay, seed))

    def test_window_at_48k_is_red(self):
        arrivals = t2_read(WindowAt48k, 22050, 2, 30.0, 7, 0.0, 0.0, 1)
        fails, _ = t2_verdict(arrivals, 22050, 30.0, 7, 0.0)
        self.assertTrue(any("past W + O" in f for f in fails), fails)


class T3TheRepeats(TestCase):
    def test_each_repeat_is_shifted_again(self):
        for rate, channels, window, pitch, feedback, seeds in t3_cells():
            for seed in seeds:
                passes = t3_read(PitchShifter, rate, channels, window,
                                 pitch, feedback, seed)
                fails, _ = t3_verdict(passes, pitch, feedback, window)
                self.assertEqual(fails, [], (rate, channels, window, pitch,
                                             feedback, seed))

    def test_flat_loop_is_red(self):
        passes = t3_read(FlatLoop, 48000, 2, 30.0, 7, 0.6, 1)
        fails, _ = t3_verdict(passes, 7, 0.6, 30.0)
        self.assertTrue(any(f.startswith("pass 2") for f in fails), fails)
        self.assertGreater(abs(passes[1][0]), 600.0)


class T4TheDry(TestCase):
    def test_the_dry_is_untouched(self):
        for rate, channels, window, mix, pitch, delay, feedback, seeds in \
                t4_cells():
            for seed in seeds:
                worst = t4_read(PitchShifter, rate, channels, window, mix,
                                pitch, delay, feedback, seed)
                self.assertLessEqual(worst, 2, (rate, channels, window, mix,
                                                pitch, delay, feedback, seed))

    def test_dry_through_shifter_is_red(self):
        worst = t4_read(DryThroughShifter, 48000, 2, 30.0, 1.0, 7, 0.0, 0.0,
                        1)
        self.assertGreater(worst, 1000)


#: Every claim sentence of the class docstring and the test that holds it.
CLAIMS = (
    ("Pitch is the interval in whole semitones.",
     ("test_pitch_plays_whole_semitones",)),
    ("The shifter reads in steps of 1/256 of the speed, so Fine moves in "
     "steps of about 7 cents near unity and 13.5 near the octave down, and "
     "the interval is within 0.5 % of the one Pitch and Fine name.",
     ("test_fine_steps_are_the_ratio_grid",
      "test_pitch_moves_by_the_semitones_it_reads",
      "test_linear_ratio_is_red")),
    ("Mix keeps your dry signal at unity up to its centre, 1, with "
     "the shifted voice coming up to unity beside it; at 2 you hear "
     "the shifted voice alone, and at 0 the output is your input.",
     ("test_the_dry_is_untouched", "test_mix_2_is_the_shifted_voice_alone",
      "test_mix_0_is_the_input")),
    ("Feedback sends the shifted voice round again, and every repeat "
     "is shifted once more: at a fifth up the repeats climb a fifth, "
     "then a ninth, then a thirteenth.",
     ("test_each_repeat_is_shifted_again", "test_flat_loop_is_red")),
    ("Off unity, each note comes back anywhere from straight away to one "
     "window and 1.3 ms late, plus Delay, the delay sweeping and jumping at "
     "every splice.",
     ("test_arrivals_drift_between_at_once_and_one_window_late",
      "test_window_at_48k_is_red")),
    ("At unity it sits still, 1.3 ms late, from a fresh start, a reset or a "
     "return from Mix 0; after a Pitch move it sits wherever the splice "
     "left it, up to one window and 1.3 ms late.",
     ("test_mix_2_is_the_shifted_voice_alone",
      "test_reset_empties_the_graph_and_returns_to_patch_0",
      "test_a_return_from_mix_0_is_a_fresh_instance_at_that_mix",
      "test_the_voice_at_unity_after_a_pitch_move_sits_where_the_splice_"
      "left_it")),
    ("On CircuitPython's own pitch shifter a reset or a return from Mix 0 "
     "does not restart the splice, so there it sits wherever the splice "
     "was.",
     ("DECLARED:PitchShifter,E10-reset,P4,circuitpython",
      "DECLARED:PitchShifter,E10-mix0,P4,circuitpython")),
    ("The window is 30 ms unless you pass `window_ms`, 15 to 60, when you "
     "build it: a longer window splices less often and arrives later.",
     ("test_window_ms_is_set_at_construction",
      "test_arrivals_drift_between_at_once_and_one_window_late")),
    ("Up to Mix 1 your dry signal passes untouched, sample for sample, with "
     "the shifted voice added on top, so a hot input can reach the rail.",
     ("test_the_dry_is_untouched", "test_dry_through_shifter_is_red",
      "test_a_hot_input_reaches_the_rail_at_mix_1")),
    ("Feedback stacks level too, far past the input: at Feedback 127, Delay "
     "0 and Mix 2 a noise burst peaking at -10.3 dBFS reaches the rail at "
     "unison, and comes within 6 dB of it at an octave or a fourth or fifth "
     "either way.",
     "test_feedback_near_its_top_stacks_level_far_past_the_input"),
    ("If your host takes the output before it loads a patch or moves Mix, "
     "or loads a patch right after a reset, the first 256 frames, 5 ms at "
     "48 kHz, play at the old level.",
     ("test_an_output_taken_before_a_patch_plays_the_old_level_at_first",
      "test_a_patch_right_after_a_reset_plays_the_old_level_at_first",
      "test_a_patch_right_after_a_return_from_mix_0_plays_the_old_level",
      "test_a_mix_sweep_after_a_reset_does_not_empty_the_repeats")),
    ("A one-channel source gets a one-channel shifter with the same window.",
     "test_a_mono_source_is_one_channel_of_a_stereo_one"),
    ("Latency is zero samples: the dry is never delayed.",
     ("test_no_latency", "test_the_dry_is_untouched")),
    ("`tail_samples` is an upper bound on how long the output takes to "
     "reach exact zero once your input stops, at every Feedback.",
     ("test_tail_samples", "test_tail_is_zero_at_mix_0")),
    ("`reset()` empties the shifter and both delay lines and returns to "
     "patch 0.",
     "test_reset_empties_the_graph_and_returns_to_patch_0"),
    ("The class never reads the host's tempo.",
     "test_the_tempo_is_never_read"),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "DECLARED:PitchShifter,E4-m2=,P5"),
)


# --------------------------------------------------------------------------
# The figures on whichever interpreter runs this file


def figures(which=("T1", "T2", "T3", "T4", "L")):
    """Print each trait's numbers over every cell the card names, eight
    seed sets each: the evidence pack's rows."""
    name = sys.implementation.name
    if "T1" in which:
        worst = 0.0
        fewest = None
        for rate, channels, window, pitch, fine in t1_cells(True):
            ratio, count = t1_read(PitchShifter, rate, channels, window,
                                   pitch, fine)
            worst = max(worst, abs(ratio - 1.0) if ratio else 1.0)
            fewest = count if fewest is None else min(fewest, count)
        plant = [t1_read(LinearRatio, 48000, 2, 30.0, p, 0.0)[0] - 1.0
                 for p in (7, -5)]
        print("%s|T1|cells 144|worst %.4f %%|fewest crossings %d|plant +7 "
              "%.2f %% -5 %.2f %%" % (name, 100 * worst, fewest,
                                      100 * plant[0], 100 * plant[1]))
    if "T2" in which:
        cells = fails = 0
        lo_arrived = 1.0
        lo_max = 9.0
        hi_min = 0.0
        past = None
        for rate, channels, window, (pitch, fine), delay, seeds in \
                t2_cells(True):
            for seed in seeds:
                arrivals = t2_read(PitchShifter, rate, channels, window,
                                   pitch, fine, delay, seed)
                bad, got = t2_verdict(arrivals, rate, window, pitch, fine)
                cells += 1
                fails += 1 if bad else 0
                if bad:
                    print("%s|T2|RED|%r|%r" % (name, (rate, channels, window,
                                                      pitch, fine, delay,
                                                      seed), bad))
                if "max" in got:
                    lo_arrived = min(lo_arrived, got["arrived"])
                    lo_max = min(lo_max, got["max"])
                    hi_min = max(hi_min, got["min"])
                    past = got["past"] if past is None else max(past,
                                                                got["past"])
        plant = t2_verdict(t2_read(WindowAt48k, 22050, 2, 30.0, 7, 0.0, 0.0,
                                   1), 22050, 30.0, 7, 0.0)[1]
        print("%s|T2|renders %d|red %d|fewest arrived %.3f|max a / (W/max(r,"
              "1)) lowest %.3f|min a / W highest %.3f|latest past W+O %d|"
              "plant past W+O %d" % (name, cells, fails, lo_arrived, lo_max,
                                     hi_min, past, plant["past"]))
    if "T3" in which:
        cells = fails = 0
        worst_cents = 0.0
        worst_db = 99.0
        cents_at = db_at = None
        for rate, channels, window, pitch, feedback, seeds in t3_cells(True):
            for seed in seeds:
                passes = t3_read(PitchShifter, rate, channels, window, pitch,
                                 feedback, seed)
                bad, levels = t3_verdict(passes, pitch, feedback, window)
                cells += 1
                fails += 1 if bad else 0
                if bad:
                    print("%s|T3|RED|%r|%r" % (name, (rate, channels, window,
                                                      pitch, feedback, seed),
                                               bad))
                cell = (rate, channels, window, pitch, feedback, seed)
                for error, _ in passes:
                    if abs(error) / (abs(pitch) * 100.0) > worst_cents:
                        worst_cents = abs(error) / (abs(pitch) * 100.0)
                        cents_at = cell
                for k, level in enumerate(levels, 2):
                    if k == 3 and window >= 60.0:
                        continue
                    if level < worst_db:
                        worst_db = level
                        db_at = cell + (k,)
        plant = t3_read(FlatLoop, 48000, 2, 30.0, 7, 0.6, 1)
        print("%s|T3|renders %d|red %d|worst error %.1f %% of the interval "
              "at %r|worst level %.1f dB from Feedback^(k-1) at %r|plant "
              "pass 2 %.0f cents, pass 3 %.0f" % (
                  name, cells, fails, 100 * worst_cents, cents_at, worst_db,
                  db_at, plant[1][0], plant[2][0]))
    if "L" in which:
        for rate in (48000, 44100):
            for channels in CHANNELS:
                values = array("h", bytes(2 * channels * 4096))
                for c in range(channels):
                    values[1000 * channels + c] = 12000
                dry = render(PitchShifter, values, rate, channels, 4096,
                             pitch=0.0)
                wet = render(PitchShifter, values, rate, channels, 4096,
                             pitch=0.0, mix=2.0)
                e = PitchShifter(kc.feed(values, rate, channels).port)
                stated = e.latency_samples
                e.deinit()
                print("%s|L|%d|%d|latency_samples %d|dry click at +%d|"
                      "shifted voice at unity, Mix 2, at +%d (D + O = %d)"
                      % (name, rate, channels, stated,
                         first_nonzero(dry, channels, 0, 4096) - 1000,
                         first_nonzero(wet, channels, 0, 4096) - 1000,
                         law_frames(0.0, rate) + law_overlap(rate)))
    if "T4" in which:
        cells = 0
        worst = 0
        for rate, channels, window, mix, pitch, delay, feedback, seeds in \
                t4_cells(True):
            for seed in seeds:
                worst = max(worst, t4_read(PitchShifter, rate, channels,
                                           window, mix, pitch, delay,
                                           feedback, seed))
                cells += 1
        plant = t4_read(DryThroughShifter, 48000, 2, 30.0, 1.0, 7, 0.0, 0.0,
                        1)
        print("%s|T4|renders %d|worst %d LSB|plant %d LSB" % (
            name, cells, worst, plant))


if __name__ == "__main__":
    if unittest is not None and "--figures" not in sys.argv:
        unittest.main()
    else:
        # By name, not as __main__: a plant reads VENDOR from the module
        # that defines it, and natively __main__ is not one it can find.
        import test_cpython_effects_pitchshifter as module
        picked = [a for a in sys.argv[1:] if a[:1] in ("T", "L")]
        module.figures(tuple(picked) or ("T1", "T2", "T3", "T4", "L"))
