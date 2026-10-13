"""`ShimmerHall`'s trait and planted-fault tests.

Six traits: T1 the Bloom stagger, T2 the interval, T3 the octaves climbing
one Bloom apart in Rise, T4 Rise's return strength, T5 Damping stopping
the climb, T6 the untouched dry. Each has its measurement, run over the
cells listed with it, and the same measurement shown red on a planted
fault of the same kind. `KIT_PLANTS` hands the plants to the kit, which
shows each one differs from the clean class and that no knob stop or patch
reproduces it.

Every law a measurement checks against is written out here, never taken
from the class.

The material is the card's: a 100 ms tone burst at f0 with 5 ms ramps and
a 2000 LSB peak, after an offset of 0 to 255 frames. A seed set draws f0
(165 to 330 Hz) and the offset from this module's own integer generator,
so every interpreter makes the same bytes. Bands are Goertzel sums over
Hann frames, 1024 frames at 48 kHz and 512 at 22.05 kHz, on the left
channel of a stereo render at 48 kHz and a mono one at 22.05 kHz.

The unit tests run a share of each trait's cells; `figures()` runs every
cell the card names, eight seed sets each, and prints the evidence pack's
numbers. The module is numpy-free and imports on MicroPython and
CircuitPython, where `unittest` is absent: the kit reads `KIT_PLANTS`
there, and running the file with `--figures` prints the figures on
whichever interpreter runs it:

    MICROPYPATH=lib:tests/support micropython \\
        tests/test_cpython_effects_shimmerhall.py --figures T6
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
from audioeffects import rebuilt                            # noqa: E402

VENDOR = "PyDevices"

RATES = (48000, 22050)
BLOCK = 256
SEEDS = tuple(range(8))
(CHARACTER_I, SHIMMER_I, RISE_I, BLOOM_I, INTERVAL_I, DECAY_I, SIZE_I,
 DAMPING_I, MIX_I) = range(9)
INTERVALS = (-12, -5, 7, 12, 24)

ShimmerHall = rebuilt.module_class("ShimmerHall")
_module = sys.modules[ShimmerHall.__module__]


# --------------------------------------------------------------------------
# The card's laws, written out independently of the class


def law_frames(ms, rate):
    """A time in whole frames."""
    return int(math.floor(ms * rate / 1000.0 + 0.5))


def law_bloom(ms):
    """Bloom on its 0-127 grid: 20 to 800 ms, log."""
    step = int(math.log(ms / 20.0) / math.log(40.0) * 127.0 + 0.5)
    return 20.0 * 40.0 ** (step / 127.0)


def law_rise(rise):
    """Rise on its 0-127 grid, 0.9 at the top."""
    return 0.9 * int(rise * 127.0 / 0.9 + 0.5) / 127.0


# --------------------------------------------------------------------------
# Material and rendering: the same bytes on every interpreter


class Lcg:
    def __init__(self, seed):
        self.state = (seed * 2654435761 + 1) & 0x7FFFFFFF

    def next(self):
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state >> 7

    def uniform(self, low, high):
        return low + (high - low) * (self.next() % 1000001) / 1000000.0


def seed_set(seed):
    """(f0, offset) for one seed: f0 uniform in 165..330 Hz, the offset in
    0..255 frames."""
    rng = Lcg(seed)
    return rng.uniform(165.0, 330.0), rng.next() % 256


def rint(x):
    """Round half away from zero."""
    if x >= 0:
        return int(x + 0.5)
    return -int(-x + 0.5)


def burst(rate, channels, f0, offset, frames):
    """The card's burst in `frames` frames: 100 ms at f0, 5 ms ramps, 2000
    LSB peak, after `offset` frames of silence."""
    out = array("h", bytes(2 * frames * channels))
    length = law_frames(100.0, rate)
    ramp = law_frames(5.0, rate)
    w = 2.0 * math.pi * f0 / rate
    for n in range(length):
        g = 1.0
        if n < ramp:
            g = 0.5 - 0.5 * math.cos(math.pi * n / ramp)
        elif n >= length - ramp:
            g = 0.5 - 0.5 * math.cos(math.pi * (length - 1 - n) / ramp)
        v = rint(2000.0 * g * math.sin(w * n))
        for c in range(channels):
            out[(offset + n) * channels + c] = v
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


def left(out, channels):
    """The left channel (the only one, in mono)."""
    if channels == 1:
        return out
    # A loop, not out[0::2]: MicroPython's array takes no slice step.
    return [out[n] for n in range(0, len(out), 2)]


def hann_size(rate):
    return 1024 if rate >= 44100 else 512


_HANN = {}


def hann(size):
    if size not in _HANN:
        _HANN[size] = [0.5 - 0.5 * math.cos(2.0 * math.pi * n / (size - 1))
                       for n in range(size)]
    return _HANN[size]


def goertzel(values, start, size, hz, rate, window):
    """Power at `hz` over values[start:start + size], Hann-windowed."""
    coeff = 2.0 * math.cos(2.0 * math.pi * hz / rate)
    s1 = s2 = 0.0
    for n in range(size):
        x = values[start + n] * window[n]
        s0 = x + coeff * s1 - s2
        s2 = s1
        s1 = s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


def band_track(values, hz, rate, hop):
    """Band power at `hz` per Hann frame, every `hop` frames."""
    size = hann_size(rate)
    window = hann(size)
    track = []
    for start in range(0, len(values) - size + 1, hop):
        track.append(goertzel(values, start, size, hz, rate, window))
    return track


def db(power):
    if power <= 0.0:
        return -400.0
    return 10.0 * math.log(power) / math.log(10.0)


def card_channels(rate):
    """The card's material: stereo at 48 kHz (the left channel read), mono
    at 22.05 kHz."""
    return 2 if rate >= 44100 else 1


def wet(cls, rate, channels, f0, offset, frames, **options):
    """Left channel of a Mix 2 render of the burst."""
    options.setdefault("mix", 2.0)
    return left(render(cls, burst(rate, channels, f0, offset, frames), rate,
                       channels, frames, **options), channels)


# --------------------------------------------------------------------------
# Planted faults


class PinnedStagger(ShimmerHall):
    """T1: Bloom's stagger pinned at 275 ms."""

    def _stagger_frames(self, bloom_ms):
        return law_frames(275.0, self._sample_rate)


class AlwaysOctave(ShimmerHall):
    """T2: the shifters always handed +12."""

    def _semitones(self):
        return 12


class PinnedLoop(ShimmerHall):
    """T3: Rise's loop pinned at 300 ms."""

    def _loop_frames(self, bloom_ms):
        return ShimmerHall._loop_frames(self, 300.0)


class HeldFeedback(ShimmerHall):
    """T4: the loop's feedback held at 0.6 in Rise."""

    def _loop_feedback(self):
        if self._is_rise():
            return 0.6
        return 0.0


class RiseInBloom(ShimmerHall):
    """T4: Rise handed to the line in Bloom too."""

    def _loop_feedback(self):
        return self._value(RISE_I)


class UndampedLoop(ShimmerHall):
    """T5: the loop's low-pass left out; the hall still gets Damping."""

    def _loop_damping(self):
        return 0.0


class LateDry(ShimmerHall):
    """T6: the dry voice fed through a stagger of its own, as the old class
    had the stagger on the wrong side of the sum."""

    def _dry_source(self):
        rate = self._sample_rate
        line = self._own(_module.audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=self._channel_count,
            max_delay_ms=_module.LINE_MS,
            delay_frames=law_frames(self._value(BLOOM_I), rate),
            feedback=0.0, mix=2.0, damping_hz=0.0, cut_hz=0.0))
        line.play(self._dry_tap)
        return line


#: The kit's plant table. A Rise plant is judged at a Rise patch, a Bloom
#: plant at the Bloom patch its fault shows plainest at.
KIT_PLANTS = {
    "T1": (PinnedStagger, 1),
    "T2": (AlwaysOctave, 2),
    "T3": (PinnedLoop, 3),
    "T4": (HeldFeedback, 4),
    "T4b": RiseInBloom,
    "T5": (UndampedLoop, 4),
    "T6": LateDry,
}


# --------------------------------------------------------------------------
# T1: in Bloom the octave lands Bloom after you play


T1_BLOOMS = (20.0, 200.0, 800.0)


def t1_onset(cls, rate, f0, offset, bloom):
    frames = law_frames(bloom + 400.0, rate) + offset
    s1 = wet(cls, rate, card_channels(rate), f0, offset, frames, bloom_ms=bloom, shimmer=1.0)
    s0 = wet(cls, rate, card_channels(rate), f0, offset, frames, bloom_ms=bloom, shimmer=0.0)
    hz = 2.0 * f0
    size = hann_size(rate)
    window = hann(size)
    for start in range(0, frames - size + 1, 64):
        p1 = goertzel(s1, start, size, hz, rate, window)
        if p1 <= 0.0:
            continue
        p0 = goertzel(s0, start, size, hz, rate, window)
        if p1 > 10.0 * p0:
            return start - offset
    return None


def t1_read(cls, rate, seed):
    """(errors in frames of each onset difference against the Bloom
    difference, the onsets)."""
    f0, offset = seed_set(seed)
    onsets = [t1_onset(cls, rate, f0, offset, b) for b in T1_BLOOMS]
    if None in onsets:
        return None, onsets
    errors = []
    for i in range(len(T1_BLOOMS)):
        for j in range(i + 1, len(T1_BLOOMS)):
            want = law_frames(law_bloom(T1_BLOOMS[j]), rate) \
                - law_frames(law_bloom(T1_BLOOMS[i]), rate)
            errors.append(onsets[j] - onsets[i] - want)
    return errors, onsets


T1_BAR = 2 * BLOCK


# --------------------------------------------------------------------------
# T2: the shifted copy is at the Interval you chose


#: Each Interval's bar in semitones, by character.
T2_BARS = {
    "bloom": {-12: 2.5, -5: 2.5, 7: 2.5, 12: 2.5, 24: 2.5},
    "rise": {-12: 6.0, -5: 2.5, 7: 2.5, 12: 3.5, 24: 6.0},
}


def t2_read(cls, rate, character, interval, seed):
    """The energy-weighted mean shift of d = (Shimmer 1) - (Shimmer 0), in
    semitones, over the 500 ms from Bloom."""
    f0, offset = seed_set(seed)
    bloom = law_bloom(275.0)
    start = law_frames(bloom, rate) + offset
    span = law_frames(500.0, rate)
    frames = start + span
    options = dict(character=character, interval=interval, rise=0.0)
    s1 = wet(cls, rate, card_channels(rate), f0, offset, frames, shimmer=1.0, **options)
    s0 = wet(cls, rate, card_channels(rate), f0, offset, frames, shimmer=0.0, **options)
    d = [s1[n] - s0[n] for n in range(frames)]
    size = 2048 if rate >= 44100 else 1024
    window = hann(size)
    total = weighted = 0.0
    for q in range(-72, 121):
        semis = q * 0.25
        hz = f0 * 2.0 ** (semis / 12.0)
        if hz >= 0.5 * rate:
            continue
        energy = 0.0
        for at in range(start, frames - size + 1, size):
            energy += goertzel(d, at, size, hz, rate, window)
        total += energy
        weighted += energy * semis
    if total <= 0.0:
        return None
    return weighted / total


# --------------------------------------------------------------------------
# T3: in Rise each octave arrives about one Bloom after the one below


def t3_onset(track, base, hop):
    """First frame where `track` is 10 dB over `base` and within 20 dB of
    its own peak."""
    peak = max(track)
    if peak <= 0.0:
        return None
    for k in range(len(track)):
        p = track[k]
        if p > 10.0 * base[k] and p >= peak * 0.01:
            return k * hop
    return None


def t3_read(cls, rate, bloom, seed):
    """(onsets of generations 1.., mean spacing over Bloom - 1)."""
    f0, offset = seed_set(seed)
    frames = law_frames(100.0 + 6 * bloom + 600.0, rate) + offset
    options = dict(character="rise", bloom_ms=bloom, damping_hz=16000.0,
                   decay=4.0, interval=12)
    s0 = wet(cls, rate, card_channels(rate), f0, offset, frames, shimmer=0.0, **options)
    r0 = wet(cls, rate, card_channels(rate), f0, offset, frames, shimmer=1.0, rise=0.0,
             **options)
    r9 = wet(cls, rate, card_channels(rate), f0, offset, frames, shimmer=1.0, rise=0.9,
             **options)
    hop = 256
    onsets = [t3_onset(band_track(r0, 2.0 * f0, rate, hop),
                       band_track(s0, 2.0 * f0, rate, hop), hop)]
    for k in range(2, 6):
        hz = f0 * 2.0 ** k
        if hz >= 0.4 * rate:
            break
        onsets.append(t3_onset(band_track(r9, hz, rate, hop),
                               band_track(r0, hz, rate, hop), hop))
    if None in onsets or len(onsets) < 2:
        return onsets, None
    spacing = (onsets[-1] - onsets[0]) / float(len(onsets) - 1)
    return onsets, spacing / law_frames(law_bloom(bloom), rate) - 1.0


def t3_verdict(onsets, error):
    if error is None:
        return "an onset was not found: %r" % (onsets,)
    for a, b in zip(onsets, onsets[1:]):
        if b <= a:
            return "onsets do not increase: %r" % (onsets,)
    if abs(error) > 0.20:
        return "spacing %.1f %% off Bloom" % (100.0 * error)
    return None


# --------------------------------------------------------------------------
# T4 and T5: how strongly each pass returns, and Damping


def band_peak(values, hz, rate):
    """The peak band power at `hz` over the render, hop of half a frame."""
    return max(band_track(values, hz, rate, hann_size(rate) // 2))


def t45_render(cls, rate, f0, offset, character, rise, damping):
    frames = law_frames(100.0 + 200.0 * 6 + 400.0, rate) + offset
    return wet(cls, rate, card_channels(rate), f0, offset, frames, character=character,
               shimmer=1.0, rise=rise, damping_hz=damping, bloom_ms=200.0,
               interval=12)


def t4_cells(full=False):
    cells = []
    for rate in RATES:
        sets = [seed_set(s) for s in (SEEDS if full else SEEDS[:2])]
        if full:
            sets += [(165.0, seed_set(0)[1]), (330.0, seed_set(1)[1])]
        cells += [(rate, f0, offset) for f0, offset in sets]
    return cells


def t4_read(cls, rate, f0, offset):
    """(Rise: generation 3's gain from Rise 0.3 to 0.9 relative to
    generation 1, in dB; Bloom: whether 0.3 and 0.9 render the same; Bloom
    2 f0 peak against Rise 0.9's, in dB)."""
    levels = []
    renders = {}
    for rise in (0.3, 0.9):
        r = t45_render(cls, rate, f0, offset, "rise", rise, 16000.0)
        renders[rise] = r
        levels.append(db(band_peak(r, 8.0 * f0, rate))
                      - db(band_peak(r, 2.0 * f0, rate)))
    gain = levels[1] - levels[0]
    b3 = t45_render(cls, rate, f0, offset, "bloom", 0.3, 16000.0)
    b9 = t45_render(cls, rate, f0, offset, "bloom", 0.9, 16000.0)
    alive = db(band_peak(b9, 2.0 * f0, rate)) \
        - db(band_peak(renders[0.9], 2.0 * f0, rate))
    return gain, list(b3) == list(b9), alive


def t5_read(cls, rate, f0, offset):
    """Generation 4 relative to generation 1 at Damping 16 kHz less the
    same at 800 Hz, in dB."""
    rel = []
    for damping in (800.0, 16000.0):
        r = t45_render(cls, rate, f0, offset, "rise", 0.9, damping)
        rel.append(db(band_peak(r, 16.0 * f0, rate))
                   - db(band_peak(r, 2.0 * f0, rate)))
    return rel[1] - rel[0]


def t5_cells(full=False):
    cells = []
    for rate in RATES:
        for f0 in (165.0, 330.0):
            for seed in (SEEDS if full else SEEDS[:1]):
                cells.append((rate, f0, seed_set(seed)[1]))
    return cells


# --------------------------------------------------------------------------
# T6: the dry never carries the shimmer


def t6_material(rate, channels, seed):
    """0.5 s of uniform noise at -18 dBFS RMS, then 1 s of silence."""
    amp = rint(32768.0 * 10.0 ** (-18.0 / 20.0) * math.sqrt(3.0))
    rng = Lcg(100 + seed)
    frames = law_frames(500.0, rate)
    out = array("h", bytes(2 * (frames + rate) * channels))
    for i in range(frames * channels):
        out[i] = rng.next() % (2 * amp + 1) - amp
    return out


def patch_options(cls, patch, **over):
    """Constructor options that build patch `patch`'s settings, with
    `over` on top: Mix set at construction opens the voices' level gates
    at that Mix, where a move after it waits for a zero crossing."""
    names = ("character", "shimmer", "rise", "bloom_ms", "interval",
             "decay", "size", "damping_hz", "mix")
    steps = cls.PATCHES[patch][1]
    options = {}
    for index, name in enumerate(names):
        position = _component.position_of_midi("UNIPOLAR", steps[index])
        if index == CHARACTER_I:
            options[name] = "rise" if position >= 0.5 else "bloom"
        elif index == INTERVAL_I:
            options[name] = INTERVALS[min(4, int(5.0 * position))]
        else:
            options[name] = _component.macro_value(
                cls._MACRO_RANGES[index], position)
    options.update(over)
    return options


def t6_read(cls, rate, channels, patch, seed):
    """(the largest |(Mix 1) - (Mix 2) - source|, the largest |output|)."""
    values = t6_material(rate, channels, seed)
    frames = len(values) // channels
    outs = []
    for mix in (1.0, 2.0):
        feed = kc.feed(values, rate, channels)
        e = cls(feed.port, **patch_options(cls, patch, mix=mix))
        try:
            outs.append(kc.samples(kc.render(e, frames)))
        finally:
            e.deinit()
    worst = loud = 0
    for i in range(len(values)):
        worst = max(worst, abs(outs[0][i] - outs[1][i] - values[i]))
        loud = max(loud, abs(outs[0][i]), abs(outs[1][i]))
    return worst, loud


T6_PATCHES = (0, 4)


# --------------------------------------------------------------------------
# Running without `audiocore.get_buffer`


def without_get_buffer(build, moves, frames=4096, seed=3, rate=48000,
                       channels=2, hide=True):
    """Render with `audiocore.get_buffer` hidden from the class, as on a
    CircuitPython board build, while it builds and while it moves; with
    `hide` false, the same render with it in place."""
    import types
    real = _module.audiocore
    fake = types.ModuleType("audiocore")
    for name in dir(real):
        if name != "get_buffer" or not hide:
            setattr(fake, name, getattr(real, name))

    def hidden(action):
        def run(e):
            _module.audiocore = _component.audiocore = fake
            try:
                action(e)
            finally:
                _module.audiocore = _component.audiocore = real
        return run

    rng = Lcg(seed)
    values = array("h", [rng.next() % 40001 - 20000
                         for _ in range(frames * channels)])
    feed = kc.feed(values, rate, channels)
    _module.audiocore = _component.audiocore = fake
    try:
        e = build(feed.port)
    finally:
        _module.audiocore = _component.audiocore = real
    try:
        out = kc.samples(kc.render(
            e, frames, dict((k, hidden(f)) for k, f in moves.items())))
    finally:
        e.deinit()
    return values, out


GET_BUFFER_CASES = (
    ("built at the defaults", ShimmerHall, {}),
    ("built in Rise", lambda src: ShimmerHall(src, character="rise"), {}),
    ("reset before the first pull", ShimmerHall, {0: lambda e: e.reset()}),
    ("reset twice before the first pull", ShimmerHall,
     {0: lambda e: (e.reset(), e.reset())}),
    ("built at Mix 0, then patch 0", lambda src: ShimmerHall(src, mix=0.0),
     {3: lambda e: e.program_change(0)}),
    ("built at Mix 0, reset", lambda src: ShimmerHall(src, mix=0.0),
     {3: lambda e: e.reset()}),
    ("Mix 0 before the first block, back", ShimmerHall,
     {0: lambda e: e.set_macro(MIX_I, 0), 4: lambda e: e.set_macro(MIX_I, 32)}),
    ("Mix 0 after playing, reset twice", ShimmerHall,
     {2: lambda e: e.set_macro(MIX_I, 0), 6: lambda e: (e.reset(), e.reset())}),
    ("a Character move and a reset in one block", ShimmerHall,
     {2: lambda e: (e.program_change(4), e.reset())}),
)


# --------------------------------------------------------------------------
# The tests


def _port(rate=48000, channels=2):
    return kc.feed(array("h", bytes(4 * channels)), rate, channels).port


class TheSurface(TestCase):
    def test_macros_patches_tier_latency(self):
        self.assertEqual(ShimmerHall.MACRO_LABELS,
                         ("Character", "Shimmer", "Rise", "Bloom",
                          "Interval", "Decay", "Size", "Damping", "Mix"))
        self.assertEqual(ShimmerHall.MACRO_MODES[0], "TOGGLE")
        self.assertEqual(ShimmerHall.TIER, _component.AUDIODSP)
        self.assertEqual(ShimmerHall.REQUIRES,
                         ("audioroute", "audioecho", "audioverb"))
        self.assertEqual(ShimmerHall.CAPABILITIES, ())
        self.assertEqual(ShimmerHall.LATENCY_SAMPLES, 0)
        self.assertEqual([ShimmerHall.PATCHES[i][0] for i in range(6)],
                         ["Octave Bloom", "Short Stagger", "Fifth Halo",
                          "Slow Rise", "Rise Damped", "Falling Octaves"])

    def test_the_spans(self):
        e = ShimmerHall(_port())
        try:
            ends = []
            for index in range(1, 9):
                if index == INTERVAL_I:
                    continue
                row = []
                for midi in (0, 127):
                    e.set_macro(index, midi)
                    row.append(round(e.macro(index), 9))
                ends.append(row)
            self.assertEqual(ends, [[0.0, 1.0], [0.0, 0.9], [20.0, 800.0],
                                    [0.3, 10.0], [0.5, 1.5],
                                    [500.0, 16000.0], [0.0, 2.0]])
        finally:
            e.deinit()

    def test_interval_has_five_zones(self):
        e = ShimmerHall(_port())
        try:
            for midi, semis in zip((0, 32, 64, 96, 127), INTERVALS):
                e.set_macro(INTERVAL_I, midi)
                self.assertEqual(e.macro(INTERVAL_I), float(semis))
            heard = set()
            for midi in range(128):
                e.set_macro(INTERVAL_I, midi)
                heard.add(e.macro(INTERVAL_I))
            self.assertEqual(heard, set(float(i) for i in INTERVALS))
        finally:
            e.deinit()

    def test_the_constructor(self):
        for bad in (0, 5, 13, 12.5, True, float("nan")):
            with self.assertRaises(ValueError):
                ShimmerHall(_port(), interval=bad)
        with self.assertRaises(ValueError):
            ShimmerHall(_port(), character="plate")
        e = ShimmerHall(_port(), bloom_ms=5000.0, rise=2.0, decay=-1.0,
                        shimmer=float("nan"), character="rise", interval=-5)
        try:
            self.assertEqual(e.get_macro(BLOOM_I), 127.0)
            self.assertEqual(e.get_macro(RISE_I), 127.0)
            self.assertEqual(e.get_macro(DECAY_I), 0.0)
            self.assertEqual(e.get_macro(SHIMMER_I), 89.0)
            self.assertEqual(e.get_macro(CHARACTER_I), 127.0)
            self.assertEqual(e.macro(INTERVAL_I), -5.0)
        finally:
            e.deinit()

    def test_patches_are_the_card_settings_on_the_grid(self):
        card = {
            0: ("bloom", 0.7, 0.6, 275, 12, 4.0, 1.0, 6000, 0.5),
            1: ("bloom", 0.6, 0.6, 60, 12, 2.5, 0.8, 8000, 0.4),
            2: ("bloom", 0.8, 0.6, 400, 7, 6.0, 1.2, 5000, 0.6),
            3: ("rise", 0.7, 0.6, 400, 12, 6.0, 1.2, 8000, 0.6),
            4: ("rise", 0.8, 0.8, 250, 12, 4.0, 1.0, 2000, 0.5),
            5: ("rise", 0.7, 0.6, 300, -12, 5.0, 1.0, 4000, 0.5),
        }
        zones = dict(zip(INTERVALS, (0, 32, 64, 96, 127)))
        for index, row in card.items():
            want = [0 if row[0] == "bloom" else 127]
            for i in range(1, 9):
                if i == INTERVAL_I:
                    want.append(zones[row[i]])
                else:
                    want.append(_component.macro_of(
                        ShimmerHall._MACRO_RANGES[i], row[i]))
            self.assertEqual(ShimmerHall.PATCHES[index][1], tuple(want),
                             index)

    def test_a_fresh_instance_reads_patch_0(self):
        e = ShimmerHall(_port())
        try:
            self.assertEqual(tuple(e.get_macro(i) for i in range(9)),
                             ShimmerHall.PATCHES[0][1])
            self.assertEqual(e.patch_index, 0)
            values = [e.macro(i) for i in range(9)]
            want = [0.0, 0.7008, 0.6024, 273.1, 12.0, 4.0206, 1.00394,
                    5990.5, 0.5039]
            for got, card in zip(values, want):
                self.assertAlmostEqual(got, card, delta=abs(card) * 1e-4)
        finally:
            e.deinit()

    def test_patches_play_the_same_whatever_the_constructor_said(self):
        # No constructor value is kept beside the grid, so a patch is the
        # same on every instance.
        values = burst(48000, 2, 247.0, 31, 9600)
        for patch in sorted(ShimmerHall.PATCHES):
            renders = []
            # Mix stays at the default: a level a patch moves waits for
            # the voice's next zero crossing, so the burst's first
            # half-cycle would play at the constructor's Mix.
            for options in ({}, dict(shimmer=0.37, rise=0.71, bloom_ms=33.3,
                                     interval=-5, decay=7.7, size=0.61,
                                     damping_hz=777.0, character="rise")):
                feed = kc.feed(values, 48000, 2)
                e = ShimmerHall(feed.port, **options)
                e.program_change(patch)
                try:
                    renders.append(kc.render(e, 9600))
                finally:
                    e.deinit()
            self.assertEqual(renders[0], renders[1], patch)

    def test_the_hall_is_its_own_patch_0(self):
        hall_cls = ShimmerHall._Hall
        self.assertEqual(sorted(hall_cls.PATCHES), [0])
        concert = None
        for name, row in ShimmerHall._Hall.__bases__[0].PATCHES.values():
            if name == "Concert Hall":
                concert = row
        want = (127, 94, 64, 0, concert[4], 91, concert[6], concert[7],
                concert[8], concert[9], concert[10], concert[11], 127)
        self.assertEqual(hall_cls.PATCHES[0][1], want)
        h = hall_cls(_port())
        try:
            for i in range(13):
                self.assertAlmostEqual(h.get_macro(i), want[i], places=6)
        finally:
            h.deinit()

    def test_only_one_provider(self):
        self.assertEqual(list(rebuilt.known()).count("ShimmerHall"), 1)
        self.assertNotIn("_Hall", rebuilt.known())

    def test_mix_0_is_the_input(self):
        values = t6_material(48000, 2, 1)
        for character in ("bloom", "rise"):
            out = render(ShimmerHall, values, 48000, 2, 24000, mix=0.0,
                         character=character)
            self.assertEqual(list(out), list(values[:48000]))

    def test_no_latency(self):
        values = array("h", bytes(2 * 2 * 4096))
        values[2000] = values[2001] = 12000
        out = render(ShimmerHall, values, 48000, 2, 4096, mix=1.0)
        self.assertEqual(out[2000], 12000)
        self.assertEqual(list(out[:2000]), [0] * 2000)

    def test_a_mono_source_gets_a_mono_rack(self):
        e = ShimmerHall(_port(48000, 1))
        try:
            self.assertEqual(e.channel_count, 1)
            self.assertEqual(e.output.channel_count, 1)
        finally:
            e.deinit()

    def test_tail_samples(self):
        # The output reaches exact zero inside the bound, at every patch.
        for rate in RATES:
            for patch in sorted(ShimmerHall.PATCHES):
                values = burst(rate, 1, 247.0, 0, law_frames(150.0, rate))
                feed = kc.feed(values, rate, 1)
                e = ShimmerHall(feed.port, patch=patch)
                try:
                    tail = e.tail_samples
                    stream = kc.Stream(e)
                    end = len(values) + tail + 2 * BLOCK
                    while stream.frames < end:
                        stream.step()
                    self.assertLessEqual(stream.last,
                                         len(values) + tail + BLOCK,
                                         (rate, patch))
                finally:
                    e.deinit()

    def test_tail_is_zero_at_mix_0(self):
        e = ShimmerHall(_port(), mix=0.0)
        try:
            self.assertEqual(e.tail_samples, 0)
        finally:
            e.deinit()

    def test_reset_empties_the_graph_and_returns_to_patch_0(self):
        values = burst(48000, 2, 247.0, 0, 48000)
        clean = render(ShimmerHall, values[2 * 9728:], 48000, 2, 24000)

        def moves(e):
            e.program_change(5)
        feed = kc.feed(values, 48000, 2)
        e = ShimmerHall(feed.port, patch=3)
        try:
            kc.render(e, 9728, {10: moves})
            e.reset()
            self.assertEqual(e.patch_index, 0)
            self.assertEqual(tuple(e.get_macro(i) for i in range(9)),
                             ShimmerHall.PATCHES[0][1])
            out = kc.samples(kc.render(e, 24000))
        finally:
            e.deinit()
        self.assertEqual(list(out), list(clean))

    def test_a_character_move_recuts_the_wet_chain(self):
        # After a Character move, the wet path renders as a fresh
        # instance's in that character, and the dry carries on.
        values = t6_material(48000, 2, 2)
        for start, end in (("bloom", 3), ("rise", 0)):
            fresh_wet = render(ShimmerHall, values[2 * 9728:], 48000, 2,
                               19200, patch=end)
            feed = kc.feed(values, 48000, 2)
            e = ShimmerHall(feed.port, character=start)
            try:
                kc.render(e, 9728)
                e.program_change(end)
                out = kc.samples(kc.render(e, 19200))
            finally:
                e.deinit()
            self.assertEqual(list(out), list(fresh_wet), start)

    def test_the_hall_follows_decay_size_and_damping(self):
        e = ShimmerHall(_port())
        try:
            hall = e._hall
            for ours, theirs in ((DECAY_I, 1), (SIZE_I, 2), (DAMPING_I, 5)):
                for midi in (0, 37, 127):
                    e.set_macro(ours, midi)
                    self.assertAlmostEqual(hall.macro(theirs), e.macro(ours),
                                           delta=abs(e.macro(ours)) * 1e-12)
            self.assertEqual(hall.macro(0), 4.0)
            self.assertEqual(hall.macro(12), 2.0)
        finally:
            e.deinit()

    def test_a_size_move_empties_the_hall(self):
        for character in ("bloom", "rise"):
            values = burst(48000, 1, 247.0, 0, 48000)
            feed = kc.feed(values, 48000, 1)
            e = ShimmerHall(feed.port, character=character, rise=0.0,
                            mix=2.0)
            try:
                kc.render(e, 256 * 188)
                ringing = kc.samples(kc.render(e, 1024))
                e.set_macro(SIZE_I, 0)
                after = kc.samples(kc.render(e, 8192))
            finally:
                e.deinit()
            self.assertGreater(max(abs(x) for x in ringing), 20, character)
            self.assertEqual(max(abs(x) for x in after), 0, character)

    def test_the_input_ceiling(self):
        # Every level at the top, a steady 100 Hz square: clean at -24
        # dBFS, on the rail at -12.
        import kit_ceiling
        self.assertEqual(ShimmerHall.INPUT_CEILING_DBFS, -24.0)
        full = dict(shimmer=1.0, mix=1.0, decay=10.0, size=1.5,
                    damping_hz=16000.0, bloom_ms=20.0, interval=12)
        for options in (dict(full, character="bloom"),
                        dict(full, character="rise", rise=0.9)):
            verdict, _digest = kit_ceiling.measure(
                ShimmerHall, 48000, 2, "square", None, None, options)
            self.assertEqual(verdict, "ok", options)
        stated = ShimmerHall.INPUT_CEILING_DBFS
        try:
            ShimmerHall.INPUT_CEILING_DBFS = -12.0
            verdict, _digest = kit_ceiling.measure(
                ShimmerHall, 48000, 2, "square", None, None,
                dict(full, character="bloom"))
        finally:
            ShimmerHall.INPUT_CEILING_DBFS = stated
        self.assertIn("rail", verdict)

    def test_a_refused_call_keeps_the_constructors_values(self):
        # The kit's `opt` cells cannot build this class (its nudge moves
        # `interval` off the five), so they run here with every other
        # numeric option moved: a refused call changes nothing.
        import kit_args
        options = dict(shimmer=0.37, rise=0.71, bloom_ms=33.3, decay=7.7,
                       size=0.61, damping_hz=777.0, mix=1.37)
        real = kit_args._nudged
        kit_args._nudged = lambda cls: [options]
        try:
            for label, _call, _noop in kit_args.refusals(ShimmerHall):
                verdict = kit_args.refused_cell(ShimmerHall, label, "opt")
                if isinstance(verdict, tuple):
                    verdict = verdict[0]
                self.assertTrue(verdict.startswith("ok"), (label, verdict))
        finally:
            kit_args._nudged = real

    def test_the_tempo_is_never_read(self):
        def transport():
            raise AssertionError("read the transport")
        feed = kc.feed(array("h", bytes(16)), 48000, 2)
        e = ShimmerHall(feed.port, transport=transport)
        try:
            for i in range(9):
                e.set_macro(i, 127)
            e.transport_changed()
        finally:
            e.deinit()

    def test_without_get_buffer_plays_what_it_plays_with_it(self):
        for name, build, moves in GET_BUFFER_CASES:
            _values, out = without_get_buffer(build, moves)
            _values, want = without_get_buffer(build, moves, hide=False)
            self.assertEqual(list(out), list(want), name)


class T1TheStagger(TestCase):
    def test_the_octave_lands_bloom_after_you_play(self):
        for rate in RATES:
            for seed in SEEDS[:2]:
                errors, onsets = t1_read(ShimmerHall, rate, seed)
                self.assertIsNotNone(errors, (rate, seed, onsets))
                for error in errors:
                    self.assertLessEqual(abs(error), T1_BAR,
                                         (rate, seed, onsets))

    def test_pinned_stagger_is_red(self):
        errors, onsets = t1_read(PinnedStagger, 48000, 0)
        self.assertGreater(max(abs(x) for x in errors), T1_BAR, onsets)


class T2TheInterval(TestCase):
    def test_the_shift_is_the_interval(self):
        for character in ("bloom", "rise"):
            for interval in INTERVALS:
                rate = 48000 if interval > 0 else 22050
                mean = t2_read(ShimmerHall, rate, character, interval, 1)
                self.assertLessEqual(abs(mean - interval),
                                     T2_BARS[character][interval],
                                     (character, interval, mean))

    def test_always_octave_is_red(self):
        for character in ("bloom", "rise"):
            for interval in (-12, -5, 7, 24):
                mean = t2_read(AlwaysOctave, 48000, character, interval, 1)
                self.assertGreater(abs(mean - interval),
                                   T2_BARS[character][interval],
                                   (character, interval, mean))


class T3TheClimb(TestCase):
    def test_each_octave_arrives_one_bloom_later(self):
        for rate, bloom, seed in ((48000, 200.0, 0), (22050, 400.0, 1)):
            onsets, error = t3_read(ShimmerHall, rate, bloom, seed)
            self.assertIsNone(t3_verdict(onsets, error),
                              (rate, bloom, seed))

    def test_pinned_loop_is_red(self):
        for bloom in (200.0, 400.0):
            onsets, error = t3_read(PinnedLoop, 48000, bloom, 0)
            self.assertIsNotNone(t3_verdict(onsets, error), (bloom, onsets))


class T4TheReturn(TestCase):
    def test_rise_sets_how_strongly_each_pass_returns(self):
        for rate, f0, offset in t4_cells():
            gain, same, alive = t4_read(ShimmerHall, rate, f0, offset)
            self.assertLessEqual(abs(gain - 19.0), 3.0, (rate, f0, gain))
            self.assertTrue(same, (rate, f0))
            self.assertGreater(alive, -20.0, (rate, f0, alive))

    def test_held_feedback_is_red(self):
        gain, _same, _alive = t4_read(HeldFeedback, 48000, 247.0, 13)
        self.assertGreater(abs(gain - 19.0), 3.0, gain)

    def test_rise_in_bloom_is_red(self):
        _gain, same, _alive = t4_read(RiseInBloom, 48000, 247.0, 13)
        self.assertFalse(same)


class T5TheDamping(TestCase):
    def test_damping_stops_the_climb(self):
        for rate, f0, offset in t5_cells():
            drop = t5_read(ShimmerHall, rate, f0, offset)
            self.assertGreaterEqual(drop, 12.0, (rate, f0, drop))

    def test_undamped_loop_is_red(self):
        for f0 in (165.0, 330.0):
            drop = t5_read(UndampedLoop, 48000, f0, 13)
            self.assertLess(drop, 12.0, (f0, drop))


class T6TheDry(TestCase):
    def test_the_dry_never_carries_the_shimmer(self):
        for rate in RATES:
            for channels in (2, 1):
                for patch in T6_PATCHES:
                    worst, loud = t6_read(ShimmerHall, rate, channels, patch,
                                          rate % 7 + patch)
                    self.assertEqual(worst, 0, (rate, channels, patch))
                    self.assertLess(loud, 32767, (rate, channels, patch))

    def test_late_dry_is_red(self):
        worst, _loud = t6_read(LateDry, 48000, 2, 0, 1)
        self.assertGreater(worst, 1000)


#: Every claim sentence of the class docstring and the test that holds it.
CLAIMS = (
    ("`ShimmerHall` - a hall that rings an octave above what you play.",
     ("test_a_fresh_instance_reads_patch_0",
      "test_the_shift_is_the_interval")),
    ("In Bloom the shifted copy goes into the hall once, Bloom after you "
     "play, and the whole hall waits for it.",
     ("test_the_octave_lands_bloom_after_you_play",
      "test_pinned_stagger_is_red", "test_rise_sets_how_strongly_each_pass_"
      "returns", "test_rise_in_bloom_is_red")),
    ("In Rise the shifter sits in a feedback loop: the hall starts at once, "
     "and each pass comes back shifted again, so the tail climbs while "
     "Damping darkens every pass until it fades.",
     ("test_each_octave_arrives_one_bloom_later", "test_pinned_loop_is_red",
      "test_damping_stops_the_climb", "test_undamped_loop_is_red")),
    ("Shimmer (0 to 1) is how loud the shifted copy goes into the hall.",
     ("test_the_spans", "test_the_shift_is_the_interval")),
    ("Bloom (20 to 800 ms) is the wait in Bloom and the time between passes "
     "in Rise.",
     ("test_the_spans", "test_the_octave_lands_bloom_after_you_play",
      "test_each_octave_arrives_one_bloom_later")),
    ("Rise (0 to 0.9) is how strongly each pass returns, in Rise only.",
     ("test_the_spans", "test_rise_sets_how_strongly_each_pass_returns",
      "test_held_feedback_is_red", "test_rise_in_bloom_is_red")),
    ("Interval picks one of five shifts: -12, -5, +7, +12 or +24 semitones.",
     ("test_interval_has_five_zones", "test_the_shift_is_the_interval",
      "test_always_octave_is_red")),
    ("Decay (0.3 to 10 s), Size (0.5 to 1.5) and Damping (500 Hz to 16 kHz) "
     "set the hall, and Damping also darkens each pass of the loop.",
     ("test_the_spans", "test_the_hall_follows_decay_size_and_damping",
      "test_damping_stops_the_climb", "test_undamped_loop_is_red")),
    ("Mix (0 to 2) is `audiodelays.Echo`'s: your dry signal at unity up to "
     "1, the hall alone at 2.",
     ("test_the_spans", "test_the_dry_never_carries_the_shimmer")),
    ("In Bloom, move Bloom and the shifted copy moves by the same time, "
     "within 512 frames.",
     ("test_the_octave_lands_bloom_after_you_play",
      "test_pinned_stagger_is_red")),
    ("Its energy centres within 2.5 semitones of the Interval.",
     ("test_the_shift_is_the_interval", "test_always_octave_is_red")),
    ("In Rise the loop's short window spreads the first pass wider: within "
     "2.5 semitones at -5 and +7, 3.5 at +12 and 6 at -12 and +24.",
     ("test_the_shift_is_the_interval", "test_always_octave_is_red")),
    ("In Rise at +12 each octave arrives one Bloom after the one below, "
     "within 20 %.",
     ("test_each_octave_arrives_one_bloom_later", "test_pinned_loop_is_red")),
    ("Moving Rise from 0.3 to 0.9 brings the third pass back 16 to 22 dB "
     "stronger against the first, and in Bloom Rise changes nothing.",
     ("test_rise_sets_how_strongly_each_pass_returns",
      "test_held_feedback_is_red", "test_rise_in_bloom_is_red")),
    ("With Damping at 800 Hz the fourth pass is at least 12 dB weaker "
     "against the first than at 16 kHz.",
     ("test_damping_stops_the_climb", "test_undamped_loop_is_red")),
    ("Up to Mix 1 your dry signal passes untouched, sample for sample: the "
     "shimmer is only ever in the hall.",
     ("test_the_dry_never_carries_the_shimmer", "test_late_dry_is_red")),
    ("At Mix 0 the output is your input, byte for byte.",
     "test_mix_0_is_the_input"),
    ("Latency is zero.", "test_no_latency"),
    ("Keep your input at or under -24 dBFS: with Decay, Size, Shimmer and "
     "Rise at the top, a steady loud input fills the hall to the rail.",
     "test_the_input_ceiling"),
    ("`tail_samples` bounds how long the output takes to reach exact zero "
     "once your input stops.",
     ("test_tail_samples", "test_tail_is_zero_at_mix_0")),
    ("`reset()` empties the hall, the line and the shifter, and restores "
     "patch 0.", "test_reset_empties_the_graph_and_returns_to_patch_0"),
    ("Moving Character or Size empties the hall: the tail drops and the dry "
     "carries on.",
     ("test_a_character_move_recuts_the_wet_chain",
      "test_a_size_move_empties_the_hall")),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "DECLARED:ShimmerHall,E6-,P5"),
    ("Interval is a fixed shift in semitones, with no key awareness.",
     "test_interval_has_five_zones"),
    ("A value outside a macro's span clamps to the nearer stop, and NaN "
     "takes the default; an `interval` other than the five raises "
     "`ValueError`.", "test_the_constructor"),
)


# --------------------------------------------------------------------------
# The figures on whichever interpreter runs this file


def figures(which=("T1", "T2", "T3", "T4", "T5", "T6", "L")):
    """Print each trait's numbers over every cell the card names, eight
    seed sets each: the evidence pack's rows."""
    name = sys.implementation.name
    if "T1" in which:
        for rate in RATES:
            worst = 0
            spread = []
            for seed in SEEDS:
                errors, onsets = t1_read(ShimmerHall, rate, seed)
                if errors is None:
                    print("%s|T1|%d|seed %d|no onset %r" % (name, rate, seed,
                                                           onsets))
                    continue
                spread += errors
                worst = max(worst, max(abs(x) for x in errors))
            print("%s|T1|%d|errors %d..%d frames|worst %d|bar %d" % (
                name, rate, min(spread), max(spread), worst, T1_BAR))
        errors, _onsets = t1_read(PinnedStagger, 48000, 0)
        print("%s|T1|plant 48000|errors %r" % (name, errors))
    if "T2" in which:
        for character in ("bloom", "rise"):
            for interval in INTERVALS:
                got = []
                for rate in RATES:
                    for seed in SEEDS:
                        got.append(t2_read(ShimmerHall, rate, character,
                                           interval, seed) - interval)
                print("%s|T2|%s|%+d|error %.2f..%.2f st|bar %.1f" % (
                    name, character, interval, min(got), max(got),
                    T2_BARS[character][interval]))
            plant = [t2_read(AlwaysOctave, 48000, character, i, 1) - i
                     for i in (-12, -5, 7, 24)]
            print("%s|T2|%s|plant errors %s" % (
                name, character, " ".join("%.1f" % x for x in plant)))
    if "T3" in which:
        for bloom in (200.0, 400.0):
            errors = []
            fails = 0
            for rate in RATES:
                for seed in SEEDS:
                    onsets, error = t3_read(ShimmerHall, rate, bloom, seed)
                    bad = t3_verdict(onsets, error)
                    if bad:
                        fails += 1
                        print("%s|T3|RED|%d|%g|%d|%s" % (name, rate, bloom,
                                                         seed, bad))
                    if error is not None:
                        errors.append(100.0 * error)
            plant = t3_read(PinnedLoop, 48000, bloom, 0)[1]
            print("%s|T3|Bloom %g|runs 16|red %d|spacing %.1f..%.1f %%|"
                  "plant %.1f %%" % (name, bloom, fails, min(errors),
                                     max(errors), 100.0 * plant))
    if "T4" in which:
        gains = []
        alive = []
        same = True
        for rate, f0, offset in t4_cells(True):
            g, s, a = t4_read(ShimmerHall, rate, f0, offset)
            gains.append(g)
            alive.append(a)
            same = same and s
        held = t4_read(HeldFeedback, 48000, 247.0, 13)[0]
        bloom = t4_read(RiseInBloom, 48000, 247.0, 13)[1]
        print("%s|T4|runs %d|gain %.1f..%.1f dB|Bloom identical %r|Bloom "
              "2f0 against Rise 0.9 %.1f..%.1f dB|plant held %.1f dB|plant "
              "Rise in Bloom identical %r" % (
                  name, len(gains), min(gains), max(gains), same,
                  min(alive), max(alive), held, bloom))
    if "T5" in which:
        for f0 in (165.0, 330.0):
            drops = [t5_read(ShimmerHall, rate, f, offset)
                     for rate, f, offset in t5_cells(True) if f == f0]
            plant = t5_read(UndampedLoop, 48000, f0, 13)
            print("%s|T5|f0 %g|runs %d|drop %.1f..%.1f dB|plant %.1f dB" % (
                name, f0, len(drops), min(drops), max(drops), plant))
    if "T6" in which:
        worst = loud = runs = 0
        for rate in RATES:
            for channels in (2, 1):
                for patch in T6_PATCHES:
                    for seed in SEEDS:
                        w, lo = t6_read(ShimmerHall, rate, channels, patch,
                                        seed)
                        worst = max(worst, w)
                        loud = max(loud, lo)
                        runs += 1
        plant = t6_read(LateDry, 48000, 2, 0, 1)[0]
        print("%s|T6|runs %d|worst %d LSB|loudest %d|plant %d LSB" % (
            name, runs, worst, loud, plant))
    if "L" in which:
        for rate in (48000, 44100):
            for channels in (2, 1):
                values = array("h", bytes(2 * channels * 4096))
                for c in range(channels):
                    values[1000 * channels + c] = 12000
                out = render(ShimmerHall, values, rate, channels, 4096,
                             mix=1.0)
                first = None
                for n in range(4096):
                    if out[n * channels]:
                        first = n
                        break
                e = ShimmerHall(kc.feed(values, rate, channels).port)
                stated = e.latency_samples
                e.deinit()
                print("%s|L|%d|%d|latency_samples %d|click at +%d" % (
                    name, rate, channels, stated, first - 1000))


if __name__ == "__main__":
    if unittest is not None and "--figures" not in sys.argv:
        unittest.main()
    else:
        # By name, not as __main__: a plant reads VENDOR from the module
        # that defines it, and natively __main__ is not one it can find.
        import test_cpython_effects_shimmerhall as module
        picked = [a for a in sys.argv[1:] if a[:1] in ("T", "L")]
        module.figures(tuple(picked)
                       or ("T1", "T2", "T3", "T4", "T5", "T6", "L"))
