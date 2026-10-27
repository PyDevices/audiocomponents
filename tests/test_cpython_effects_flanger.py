"""`Flanger`'s trait and planted-fault tests.

Six traits, T1 to T6 (the card's), each with its measurement run over the
span listed with it and the same measurement shown red on a planted fault
of the same kind. `KIT_PLANTS` hands the plants to the kit, which shows
each one differs from the clean class and that no knob stop or patch
reproduces it. `CLAIMS` ties every claim sentence of the docstring to the
tests that hold it.

Every law a measurement checks against is written out here, never taken
from the class: the comb's sum in integers, the two Color laws, the ring's
trips, the triangle, the tempo's period.

The module is numpy-free and imports on MicroPython and CircuitPython,
where `unittest` is absent: the kit reads `KIT_PLANTS` there, and
`native_report()` prints each trait's figures for the three interpreters to
be compared (`python tests/test_cpython_effects_flanger.py --report`).
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
from audioeffects import flanger as flanger_module          # noqa: E402

VENDOR = "PyDevices"

Flanger = flanger_module.Flanger

RATES = (48000, 22050)
BLOCK = 256
RATE, RANGE, MANUAL, COLOR, MIX, POLARITY, SYNC, DIVISION = range(8)
SEEDS = range(8)


# --------------------------------------------------------------------------
# Material


class Rng:
    """A 31-bit LCG, the same on every interpreter."""

    def __init__(self, seed):
        self.state = (seed * 2654435761 + 12345) & 0x7FFFFFFF

    def next(self):
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state

    def randint(self, low, high):
        return low + self.next() % (high - low + 1)

    def unit(self):
        return self.next() / 2147483648.0


def noise(seed, frames, peak, channels=1):
    """Interleaved seeded noise, each channel its own draw."""
    rng = Rng(seed)
    return array("h", [rng.randint(-peak, peak)
                       for _ in range(frames * channels)])


def sine(f, rate, frames, amp, phase=0.0):
    return array("h", [int(round(amp * math.sin(
        2.0 * math.pi * f * n / rate + phase))) for n in range(frames)])


def clicks(rate, frames, offset, spacing, amp=16384):
    x = array("h", bytes(2 * frames))
    for c in range(offset, frames - spacing, spacing):
        x[c] = amp
    return x, list(range(offset, frames - spacing, spacing))


def render(cls, values, rate, channels=1, frames=None, options=None,
           macros=None, transport=None, actions=None):
    """`cls` around `values`, then silence: `frames` frames, interleaved."""
    if frames is None:
        frames = len(values) // channels
    feed = kc.feed(values, rate, channels)
    keywords = dict(options or {})
    if transport is not None:
        keywords["transport"] = transport
    e = cls(feed.port, sample_rate=rate, **keywords)
    try:
        for index, value in (macros or ()):
            e.set_macro(index, value)
        return kc.samples(kc.render(e, frames, actions))
    finally:
        e.deinit()


def channel(values, channels, which=0):
    return [values[i] for i in range(which, len(values), channels)]


def held(tau, rate, color=0.0, mix=1.0, polarity="positive"):
    """Options for a comb held still at `tau` frames: Range 0."""
    return {"depth": 0.0, "manual_ms": tau * 1000.0 / rate, "color": color,
            "mix": mix, "polarity": polarity}


# --------------------------------------------------------------------------
# The laws, written out


def trunc_mul(d, m):
    """trunc(d * m / 32768), toward zero, in integers."""
    return (d * m) >> 15 if d >= 0 else -((-d * m) >> 15)


def comb_law(x, tau, mix, sign=1):
    """x[n] + sign * trunc(x[n - tau] * int(mix * 32767) / 32768); the dry
    alone at Mix 0.01 and below."""
    m = int(mix * 32767)
    out = []
    for n in range(len(x)):
        if mix <= 0.01:
            out.append(x[n])
            continue
        d = x[n - tau] if n >= tau else 0
        out.append(x[n] + sign * trunc_mul(d, m))
    return out


def q15(color):
    return int(color * 32767) / 32767.0


def color_laws(g, negative=False):
    """(gain at k/tau, gain at (2k + 1)/(2 tau)) of the comb at Mix 1."""
    plus = (2.0 - g) / (1.0 - g)
    minus = g / (1.0 + g)
    return (minus, plus) if negative else (plus, minus)


def db(v):
    return 20.0 * math.log10(max(v, 1e-12))


def amp_at(y, f, rate, start):
    """Least-squares amplitude of `f` over y[start:]."""
    s = c = 0.0
    for i in range(start, len(y)):
        w = 2.0 * math.pi * f * i / rate
        s += y[i] * math.sin(w)
        c += y[i] * math.cos(w)
    return 2.0 * math.sqrt(s * s + c * c) / (len(y) - start)


def trips_60(g):
    return 60.0 / (-20.0 * math.log10(g))


def trips_silence(g):
    return 90.3 / (-20.0 * math.log10(g)) + 1.0


def card_tail(color, top_ms, rate):
    """The card's section 5 bound, written out."""
    g = int(color * 32767) / 32767.0
    d = min(int(rate // 100), int(math.ceil(top_ms * rate / 1000.0)))
    if g <= 0.0:
        return d + 3
    return (int(math.ceil(90.31 / (-20.0 * math.log10(g)))) + 2) * (d + 1) + 2


def triangle_ms(n, lfo, rate, manual, depth, clamp=True):
    """The delay the node reads at output frame n, in frames: from the
    floor, the phase advanced once a frame from 0, the top clamped to the
    line (`clamp`)."""
    inc = int(min(lfo / rate, 0.5) * 4294967296.0)
    ph = ((n + 1) * inc) & 0xFFFFFFFF
    tri = ph >> 15
    if tri > 65535:
        tri = 131071 - tri
    line = int(rate // 100)
    top = manual + depth * (10.0 - manual)
    top_f = top * rate / 1000.0
    if clamp:
        top_f = min(top_f, line)
    lo_f = manual * rate / 1000.0
    return lo_f + (top_f - lo_f) * tri / 65536.0


def tempo_rate(bpm, quarters, bars):
    """One sweep per `bars` bars of `quarters` quarter notes."""
    return bpm / (60.0 * quarters * bars)


# --------------------------------------------------------------------------
# The measurements


def t1_worst(cls, rate, tau, mix, channels, seed, sign=1, polarity=None):
    """The largest |out - law| over every channel, and how many samples
    differ at all."""
    frames = 3000
    x = noise(seed, frames, 14000, channels)
    options = held(tau, rate, mix=mix,
                   polarity=polarity or ("negative" if sign < 0
                                         else "positive"))
    y = render(cls, x, rate, channels, frames, options)
    worst = differ = 0
    for ch in range(channels):
        law = comb_law(channel(x, channels, ch), tau, mix, sign)
        got = channel(y, channels, ch)
        for n in range(frames):
            e = abs(got[n] - law[n])
            if e:
                differ += 1
                worst = max(worst, e)
    return worst, differ


def t1_notch_db(cls, rate, tau, k, phase, channels=1):
    """A sine of 8000 on the k-th notch at Mix 1, Color 0: output level
    against input, dB."""
    f = (2 * k + 1) * rate / (2.0 * tau)
    frames = int(rate * 0.2)
    x = sine(f, rate, frames, 8000, phase)
    if channels == 2:
        stereo = array("h", bytes(4 * frames))
        for n in range(frames):
            stereo[2 * n] = stereo[2 * n + 1] = x[n]
        x = stereo
    y = render(cls, x, rate, channels, frames, held(tau, rate))
    return max(db(amp_at(channel(y, channels, ch), f, rate, frames // 2)
                  / 8000.0) for ch in range(channels))


def comb_pair_db(cls, rate, color, negative, phase, tau=None):
    """(level at k/tau, at (2k + 1)/(2 tau)), k = 1, against the input, dB:
    a sine of 1000, the second half of 0.6 s."""
    tau = tau or (144 if rate == 48000 else 66)
    frames = int(rate * 0.6)
    out = []
    for f in (rate / float(tau), rate / (2.0 * tau)):
        x = sine(f, rate, frames, 1000, phase)
        y = render(cls, x, rate, 1, frames,
                   held(tau, rate, color=color,
                        polarity="negative" if negative else "positive"))
        out.append(db(amp_at(y, f, rate, frames // 2) / 1000.0))
    return out


def ring_reading(cls, rate, manual_ms, color, seed, depth=0.0, lfo=None):
    """(the -60 dB time as a fraction of its law, the last non-zero
    sample as a fraction of the silence law, the last non-zero sample in
    frames after the burst, `tail_samples` read after it)."""
    burst = int(0.05 * rate)
    x = noise(seed, burst, 16000)
    options = {"depth": depth, "manual_ms": manual_ms, "color": color,
               "mix": 1.0}
    if lfo is not None:
        options["rate"] = lfo
    feed = kc.feed(x, rate, 1)
    e = cls(feed.port, sample_rate=rate, **options)
    try:
        top = manual_ms + depth * (10.0 - manual_ms)
        long = max(e.tail_samples, card_tail(color, top, rate))
        # One render: a pull hands whole blocks, so two renders would drop
        # the frames of the burst's last block past the burst.
        y = kc.samples(kc.render(e, burst + long + 4 * BLOCK))
        tail = e.tail_samples
    finally:
        e.deinit()
    win, hop = int(0.01 * rate), int(0.001 * rate)
    sq = [0]
    for v in y:
        sq.append(sq[-1] + v * v)

    def rms(a, b):
        return math.sqrt((sq[b] - sq[a]) / float(b - a))
    ref = rms(burst - win, burst)
    t60 = None
    pos = burst
    while pos + win <= len(y):
        if rms(pos, pos + win) <= ref * 1e-3:
            t60 = (pos - burst) / float(rate)
            break
        pos += hop
    last = 0
    for i in range(len(y) - 1, -1, -1):
        if y[i]:
            last = i
            break
    g = q15(color)
    top = manual_ms + depth * (10.0 - manual_ms)
    top_frames = min(rate // 100, top * rate / 1000.0)
    law60 = trips_60(g) * manual_ms / 1000.0
    law_sil = trips_silence(g) * top_frames
    return (None if t60 is None else t60 / law60,
            (last - burst) / law_sil, last - burst, tail)


def end_then_replay(cls, reset):
    """The source ends after a burst at 3 ms and full Color; then, with or
    without a reset, the node is played again on silence. Non-zero
    samples in what comes out."""
    rate = 48000
    x = noise(0, 2400, 16000)
    feed = kc.feed(x, rate, 1)
    e = cls(feed.port, sample_rate=rate, depth=0.0, manual_ms=3.0,
            color=0.95)
    try:
        kc.render(e, 2560)
        feed.point(feed.empty)
        ended = kc.samples(kc.render(e, 4096))
        if reset:
            e.reset()
        feed.point(feed.sil)
        # A host plays the node again: the only way back in after an end.
        e._node.play(feed.port)
        again = kc.samples(kc.render(e, 4864))
    finally:
        e.deinit()
    return sum(1 for v in ended if v), sum(1 for v in again if v)


def sweep_readings(cls, rate, lfo, depth, manual, seed, frames=None,
                   options=None, transport=None, actions=None):
    """[(output frame, delay in frames)] from a click every 12 ms, Color 0,
    Mix 1: each click's echo as a centroid of its frames."""
    spacing = int(0.012 * rate)
    offset = Rng(seed).randint(0, spacing - 1)
    if frames is None:
        frames = int(rate / lfo) + spacing
    x, at = clicks(rate, frames, offset, spacing)
    opts = {"rate": lfo, "depth": depth, "manual_ms": manual, "color": 0.0,
            "mix": 1.0}
    opts.update(options or {})
    y = render(cls, x, rate, 1, frames, opts, transport=transport,
               actions=actions)
    out = []
    for c in at:
        tot = mom = 0.0
        for i in range(c + 1, min(len(y), c + spacing)):
            if y[i]:
                tot += y[i]
                mom += (i - c) * y[i]
        if tot:
            d = mom / tot
            out.append((c + int(d), d))
    return out


def sweep_worst(readings, lfo, rate, manual, depth):
    return max(abs(d - triangle_ms(n, lfo, rate, manual, depth))
               for n, d in readings)


def fit_rate(readings, rate, manual, depth, guess, start_phase=0,
             start_frame=-1):
    """The sweep rate whose triangle fits the readings best, by a golden
    search within 2 % of `guess`; the phase runs from `start_phase` at
    `start_frame`."""
    lo_f = manual * rate / 1000.0
    top = manual + depth * (10.0 - manual)
    top_f = min(top * rate / 1000.0, int(rate // 100))

    def err(lfo):
        inc = lfo / rate * 4294967296.0
        total = 0.0
        for n, d in readings:
            ph = (start_phase + (n - start_frame) * inc) % 4294967296.0
            tri = ph / 32768.0
            if tri > 65536.0:
                tri = 131072.0 - tri
            exp = lo_f + (top_f - lo_f) * tri / 65536.0
            total += (d - exp) ** 2
        return total
    a, b = guess * 0.98, guess * 1.02
    r = (math.sqrt(5.0) - 1.0) / 2.0
    c, d = b - r * (b - a), a + r * (b - a)
    fc, fd = err(c), err(d)
    for _ in range(60):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - r * (b - a)
            fc = err(c)
        else:
            a, c, fc = c, d, fd
            d = a + r * (b - a)
            fd = err(d)
    return (a + b) / 2.0


class Transport:
    """A host transport whose tempo and time signature a test moves, in
    the API's order: (playing, seconds, bpm, numerator, denominator)."""

    def __init__(self, bpm, numerator, denominator=4):
        self.bpm = bpm
        self.numerator = numerator
        self.denominator = denominator

    def __call__(self):
        return (True, 0.0, self.bpm, self.numerator, self.denominator)


def synced_period_error(cls, rate, bpm, numerator, bars, seed,
                        denominator=4):
    """The fitted sweep's period against Division bars of
    numerator x 4 / denominator quarter notes at the tempo, as a
    fraction."""
    transport = Transport(bpm, numerator, denominator)
    want = tempo_rate(bpm, numerator * 4.0 / denominator, bars)
    manual, depth = 1.0, 0.6
    readings = sweep_readings(
        cls, rate, want, depth, manual, seed,
        frames=int(rate / want * 1.05) + int(0.012 * rate),
        options={"rate": 0.25, "sync": True, "division": bars},
        transport=transport)
    got = fit_rate(readings, rate, manual, depth, want)
    return abs(got / want - 1.0)


def tempo_change_error(cls, rate, seed):
    """120 -> 150 bpm in 4/4 at one bar, `transport_changed()` between two
    pulls: the next full period against 150 bpm, the phase carried."""
    transport = Transport(120.0, 4)
    first = tempo_rate(120.0, 4, 1.0)
    second = tempo_rate(150.0, 4, 1.0)
    manual, depth = 1.0, 0.6
    change = 120                        # the pull before which it lands
    boundary = change * BLOCK

    def move(e):
        transport.bpm = 150.0
        e.transport_changed()
    frames = boundary + int(rate / second * 1.05) + int(0.012 * rate)
    readings = sweep_readings(
        cls, rate, first, depth, manual, seed, frames=frames,
        options={"rate": 0.25, "sync": True, "division": 1.0},
        transport=transport, actions={change: move})
    inc1 = int(min(first / rate, 0.5) * 4294967296.0)
    phase = (boundary * inc1) & 0xFFFFFFFF
    after = [(n, d) for n, d in readings if n >= boundary + 300]
    got = fit_rate(after, rate, manual, depth, second, start_phase=phase,
                   start_frame=boundary - 1)
    return abs(got / second - 1.0)


def meter_change_error(cls, rate, seed):
    """4/4 to 3/4 at 120 bpm, one bar, `transport_changed()` between two
    pulls: the next full period against the new bar."""
    transport = Transport(120.0, 4)
    first = tempo_rate(120.0, 4, 1.0)
    second = tempo_rate(120.0, 3, 1.0)
    manual, depth = 1.0, 0.6
    change = 120
    boundary = change * BLOCK

    def move(e):
        transport.numerator = 3
        e.transport_changed()
    frames = boundary + int(rate / second * 1.05) + int(0.012 * rate)
    # A host calls `transport_changed()` once a block: the first call has
    # read 120 bpm in 4/4 long before the meter moves.
    readings = sweep_readings(
        cls, rate, first, depth, manual, seed, frames=frames,
        options={"rate": 0.25, "sync": True, "division": 1.0},
        transport=transport,
        actions={1: lambda e: e.transport_changed(), change: move})
    inc1 = int(min(first / rate, 0.5) * 4294967296.0)
    phase = (boundary * inc1) & 0xFFFFFFFF
    after = [(n, d) for n, d in readings if n >= boundary + 300]
    got = fit_rate(after, rate, manual, depth, second, start_phase=phase,
                   start_frame=boundary - 1)
    return abs(got / second - 1.0)


def knob_pair_db(cls, rate, macros, patch=None):
    """The comb's level against the input, dB, at its first peak k/tau
    (a dip once Polarity is minus), Range 0, with the polarity set by
    `macros` or `patch` after construction."""
    feed = kc.feed(array("h", [0, 0]), rate, 1)
    e = cls(feed.port, sample_rate=rate, **held(144, rate, color=0.5))
    if patch is not None:
        e.program_change(patch)
        e.set_macro(RANGE, 0)
    for index, value in macros:
        e.set_macro(index, value)
    delay = e.macro(MANUAL) * rate / 1000.0
    e.deinit()
    frames = int(rate * 0.6)
    f = rate / delay
    x = sine(f, rate, frames, 1000)
    feed = kc.feed(x, rate, 1)
    e = cls(feed.port, sample_rate=rate, **held(144, rate, color=0.5))
    try:
        if patch is not None:
            e.program_change(patch)
            e.set_macro(RANGE, 0)
        for index, value in macros:
            e.set_macro(index, value)
        y = kc.samples(kc.render(e, frames))
        color = e.macro(COLOR)
    finally:
        e.deinit()
    return db(amp_at(y, f, rate, frames // 2) / 1000.0), color


# --------------------------------------------------------------------------
# The planted faults


class HalfMix(Flanger):
    """T1: Mix sent to the node halved (the old class's law)."""
    NAME = 'Flanger'

    def _refresh(self):
        Flanger._refresh(self)
        self._node.mix = self._value(MIX) * 0.5


class SquaredColor(Flanger):
    """T2: Color squared on the way to the node."""
    NAME = 'Flanger'

    def _refresh(self):
        Flanger._refresh(self)
        color = self._value(COLOR) ** 2
        self._node.feedback = -color if self._negative() else color


class SixtyTail(Flanger):
    """T3: `tail_samples` from the 60 dB law instead of silence."""
    NAME = 'Flanger'

    @property
    def tail_samples(self):
        self._check_live()
        g = q15(self._value(COLOR))
        d = min(self._sample_rate // 100, int(math.ceil(
            self._top_ms() * self._sample_rate / 1000.0)))
        if g <= 0.0:
            return d + 3
        return int(math.ceil(trips_60(g))) * (d + 1)


class KeepLine(Flanger):
    """T3: a `reset()` that leaves the node's line alone."""
    NAME = 'Flanger'

    def reset(self):
        self._check_live()
        self.program_change(0)


class SquaredRange(Flanger):
    """T4: Range squared on the way to the node."""
    NAME = 'Flanger'

    def _refresh(self):
        Flanger._refresh(self)
        self._node.depth = self._value(RANGE) ** 2


class FourBeatBar(Flanger):
    """T5: the bar taken as four beats whatever the meter."""
    NAME = 'Flanger'

    def _rate_hz(self):
        if self._macros[SYNC] < 0.5:
            return Flanger._rate_hz(self)
        state = self._transport()
        bars = flanger_module._choice(flanger_module.DIVISION_BARS,
                                      self._macros[DIVISION])
        return max(1.0, float(state[2])) / (60.0 * 4.0 * bars)


class MeterDeaf(Flanger):
    """T5: `transport_changed()` follows the tempo and not the meter."""
    NAME = 'Flanger'

    def transport_changed(self):
        from audioeffects import _component
        _component.Component.transport_changed(self)


class FrozenPolarity(Flanger):
    """T6: Polarity read from the constructor, so the knob does nothing."""
    NAME = 'Flanger'

    def _build(self, polarity="positive", **options):
        self._frozen = polarity == "negative"
        Flanger._build(self, polarity=polarity, **options)

    def _negative(self):
        return self._frozen


class FrozenSync(Flanger):
    """T5: Sync read from the constructor, so the knob does nothing."""
    NAME = 'Flanger'

    def _build(self, sync=False, **options):
        self._frozen = bool(sync)
        Flanger._build(self, sync=sync, **options)

    def _rate_hz(self):
        if not self._frozen:
            return self._value(RATE)
        return Flanger._rate_hz(self)


class KeptNothing(Flanger):
    """A restore that leaves the exact constructor values out."""
    NAME = 'Flanger'
    _KEPT = ()


class InvertOnly(Flanger):
    """T6: `invert` set with the feedback left positive."""
    NAME = 'Flanger'

    def _refresh(self):
        Flanger._refresh(self)
        self._node.feedback = self._value(COLOR)


class FeedbackOnly(Flanger):
    """T6: feedback -Color with `invert` left off."""
    NAME = 'Flanger'

    def _refresh(self):
        Flanger._refresh(self)
        self._node.invert = False


#: A 3/4 host, for the plant whose fault only a meter other than 4 shows.
WALTZ = Transport(90.0, 3)

KIT_PLANTS = {
    "T1": HalfMix,
    "T2": SquaredColor,
    "T3": SixtyTail,
    "T4": SquaredRange,
    "T5": (FourBeatBar, 5, {"options": {"transport": WALTZ}}),
    "T6-invert": (InvertOnly, 3),
    "T6-feedback": (FeedbackOnly, 3),
}


# --------------------------------------------------------------------------
# The trait tests (CPython: unittest)


#: Manual at 0.25, 1 and 5 ms, the knob's floor, a middle and its top:
#: whole frames at 48 kHz, and at 22.05 kHz 11, 44 and 110 frames (0.499,
#: 1.995 and 4.989 ms), none of them whole milliseconds. The card's 220
#: frames (9.977 ms) is past Manual's top, so it is read where the sweep
#: reaches it (T4).
T1_TAUS = {48000: (12, 48, 240), 22050: (11, 44, 110)}


class T1Comb(TestCase):
    """The copy is your signal exactly Manual late, added at Mix."""

    def test_the_comb_is_the_sum_in_integers(self):
        for rate in RATES:
            for tau in T1_TAUS[rate]:
                for mix in (0.0, 0.5, 1.0):
                    for channels in (1, 2):
                        for seed in SEEDS:
                            worst, _ = t1_worst(Flanger, rate, tau, mix,
                                                channels, seed)
                            self.assertLessEqual(
                                worst, 1, (rate, tau, mix, channels, seed))

    def test_mix_0_is_the_input_byte_for_byte(self):
        for rate in RATES:
            for channels in (1, 2):
                x = noise(3, 4096, 30000, channels)
                y = render(Flanger, x, rate, channels, options={"mix": 0.0})
                self.assertEqual(list(y), list(x))
                # Mix brought to 0 from its knob: the wire again.
                y = render(Flanger, x, rate, channels, macros=((MIX, 0),))
                self.assertEqual(list(y), list(x))

    def test_a_notch_is_40_db_down(self):
        for rate in RATES:
            for tau in T1_TAUS[rate]:
                for k in range(3):
                    if (2 * k + 1) * rate / (2.0 * tau) >= 8000.0:
                        continue
                    for channels in (1, 2):
                        for seed in SEEDS:
                            level = t1_notch_db(Flanger, rate, tau, k,
                                                2.0 * math.pi * seed / 8.0,
                                                channels)
                            self.assertLessEqual(level, -40.0,
                                                 (rate, tau, k, seed))

    def test_the_plant_is_red(self):
        worst, _ = t1_worst(HalfMix, 48000, 48, 1.0, 1, 0)
        self.assertGreater(worst, 2)
        worst, _ = t1_worst(HalfMix, 48000, 48, 0.0, 1, 0)
        self.assertEqual(worst, 0)


class T2Color(TestCase):
    """Color raises the peaks and fills the notches, on the two laws."""

    def test_the_two_laws(self):
        for rate in RATES:
            for color in (0.0, 0.5, 0.8, 0.95):
                plus, minus = color_laws(q15(color))
                for seed in SEEDS:
                    peak, notch = comb_pair_db(Flanger, rate, color, False,
                                               2.0 * math.pi * seed / 8.0)
                    self.assertLessEqual(abs(peak - db(plus)), 0.25,
                                         (rate, color, seed, peak))
                    if color > 0.0:
                        self.assertLessEqual(abs(notch - db(minus)), 0.25,
                                             (rate, color, seed, notch))
                    else:
                        self.assertLessEqual(notch, -40.0)

    def test_full_color_and_color_0(self):
        """+26.4 dB and -6.2 dB at full Color; +6 dB on a peak at Color 0."""
        plus, minus = color_laws(q15(0.95))
        self.assertAlmostEqual(db(plus), 26.4, delta=0.06)
        self.assertAlmostEqual(db(minus), -6.2, delta=0.06)
        self.assertAlmostEqual(db(color_laws(0.0)[0]), 6.02, places=2)
        peak, notch = comb_pair_db(Flanger, 48000, 0.95, False, 0.0)
        self.assertLessEqual(abs(peak - 26.4), 0.3)
        self.assertLessEqual(abs(notch + 6.2), 0.3)

    def test_the_plant_is_red(self):
        for color in (0.5, 0.95):
            plus, _ = color_laws(q15(color))
            peak, _ = comb_pair_db(SquaredColor, 48000, color, False, 0.0)
            self.assertGreater(abs(peak - db(plus)), 1.0)


#: The card's 8 ms is past Manual's top; 5 ms is the longest held comb.
T3_MANUALS = (1.0, 3.0, 5.0)


class T3Ring(TestCase):
    """Color sets how long the comb rings while the source plays silence."""

    def test_the_ring_follows_its_laws(self):
        for rate in RATES:
            for manual in T3_MANUALS:
                for color in (0.5, 0.8, 0.95):
                    for seed in SEEDS:
                        t60, silence, last, tail = ring_reading(
                            Flanger, rate, manual, color, seed)
                        key = (rate, manual, color, seed)
                        self.assertIsNotNone(t60, key)
                        self.assertTrue(0.5 <= t60 <= 1.1, (key, t60))
                        self.assertLessEqual(silence, 1.0, (key, silence))
                        self.assertLessEqual(last, tail, key)

    def test_the_swept_ring_is_inside_the_tail(self):
        for rate in RATES:
            for manual in (1.0, 5.0):
                for color in (0.5, 0.95):
                    for seed in SEEDS:
                        _, _, last, tail = ring_reading(
                            Flanger, rate, manual, color, seed, depth=1.0,
                            lfo=4.0)
                        self.assertLessEqual(last, tail,
                                             (rate, manual, color, seed))

    def test_the_longest_rings(self):
        """At most about 0.4 s at 3 ms and 0.7 s at 5 ms, full Color."""
        g = q15(0.95)
        self.assertAlmostEqual(trips_60(g) * 0.003, 0.404, places=3)
        self.assertAlmostEqual(trips_60(g) * 0.005, 0.673, places=3)
        for manual, law in ((3.0, 0.404), (5.0, 0.673)):
            for rate in RATES:
                worst = max(ring_reading(Flanger, rate, manual, 0.95,
                                         seed)[0] for seed in SEEDS)
                self.assertLessEqual(worst * law, 1.1 * law)

    def test_the_source_ends_and_reset_clears_the_line(self):
        ended, again = end_then_replay(Flanger, reset=True)
        self.assertEqual(ended, 0)
        self.assertEqual(again, 0)
        # Without the reset the frozen ring comes back: the case is live.
        ended, again = end_then_replay(Flanger, reset=False)
        self.assertEqual(ended, 0)
        self.assertGreater(again, 4000)

    def test_the_plants_are_red(self):
        reds = 0
        for seed in SEEDS:
            _, _, last, tail = ring_reading(SixtyTail, 48000, 3.0, 0.95,
                                            seed)
            reds += last > tail
        self.assertEqual(reds, len(SEEDS))
        # The plant's reset loads patch 0 over the frozen ring, which then
        # plays at patch 0's Color; the clean class plays nothing.
        self.assertGreater(end_then_replay(KeepLine, reset=True)[1], 500)


T4_CELLS = ((1.0, 1.0, 0.5), (8.0, 0.5, 2.0), (0.25, 0.25, 1.0))


class T4Sweep(TestCase):
    """The sweep is a triangle in milliseconds from Manual to its top."""

    def test_the_triangle(self):
        for rate in RATES:
            for lfo, depth, manual in T4_CELLS:
                for seed in SEEDS:
                    readings = sweep_readings(Flanger, rate, lfo, depth,
                                              manual, seed)
                    worst = sweep_worst(readings, lfo, rate, manual, depth)
                    self.assertLessEqual(worst, 0.15,
                                         (rate, lfo, depth, manual, seed))

    def test_the_top_at_22050_is_half_a_frame_under_10_ms(self):
        self.assertAlmostEqual(220 * 1000.0 / 22050, 9.977, places=3)
        readings = sweep_readings(Flanger, 22050, 1.0, 1.0, 0.5, 0)
        self.assertLessEqual(sweep_worst(readings, 1.0, 22050, 0.5, 1.0),
                             0.15)
        # A top at 10 ms itself, 220.5 frames, misses the readings near it.
        self.assertGreater(max(
            abs(d - triangle_ms(n, 1.0, 22050, 0.5, 1.0, clamp=False))
            for n, d in readings), 0.3)

    def test_the_sweep_starts_at_manual_and_again_after_a_reset(self):
        rate = 48000
        first = sweep_readings(Flanger, rate, 1.0, 1.0, 2.0, 0)
        self.assertLessEqual(abs(first[0][1] - triangle_ms(
            first[0][0], 1.0, rate, 2.0, 1.0)), 0.15)
        self.assertLess(first[0][1], 2.0 * 48 + 8)
        # A reset half-way through: the sweep reads from Manual again.
        spacing = int(0.012 * rate)
        x, at = clicks(rate, rate, 7, spacing)
        feed = kc.feed(x, rate, 1)
        e = Flanger(feed.port, sample_rate=rate, rate=1.0, depth=1.0,
                    manual_ms=2.0, color=0.0, mix=1.0)
        try:
            kc.render(e, 24576)
            e.reset()
            # Patch 0 now; hold its sweep to the card's triangle from 0.
            y = kc.samples(kc.render(e, rate - 24576))
            manual = e.macro(MANUAL)
            depth = e.macro(RANGE)
            lfo = e.macro(RATE)
            color = e.macro(COLOR)
        finally:
            e.deinit()
        self.assertGreater(color, 0.0)
        # Color is patch 0's now, so read the first click after the reset
        # only: its echo arrives before any feedback does.
        c = next(c for c in at if c >= 24576) - 24576
        seg = [(i, y[i]) for i in range(c + 1, c + spacing) if y[i]]
        lead = [(i, v) for i, v in seg if i - c < manual * 48 + 4]
        d = sum((i - c) * v for i, v in lead) / sum(v for _, v in lead)
        self.assertLessEqual(abs(d - triangle_ms(c + int(d), lfo, rate,
                                                 manual, depth)), 0.15)

    def test_both_channels_sweep_together(self):
        rate = 48000
        mono = noise(5, 9600, 12000)
        x = array("h", bytes(4 * len(mono)))
        for n in range(len(mono)):
            x[2 * n] = x[2 * n + 1] = mono[n]
        y = render(Flanger, x, rate, 2, options={"rate": 4.0, "depth": 1.0})
        self.assertEqual(channel(y, 2, 0), channel(y, 2, 1))
        self.assertNotEqual(channel(y, 2, 0), list(mono))

    def test_the_plant_is_red(self):
        readings = sweep_readings(SquaredRange, 48000, 8.0, 0.5, 2.0, 0)
        self.assertGreater(sweep_worst(readings, 8.0, 48000, 2.0, 0.5), 50)


class T5Sync(TestCase):
    """With Sync on, one sweep lasts Division bars at the host's tempo."""

    def test_the_period(self):
        for rate in RATES:
            for bpm, beats in ((120.0, 4), (90.0, 3)):
                for bars in (1.0, 0.25):
                    for seed in SEEDS:
                        err = synced_period_error(Flanger, rate, bpm, beats,
                                                  bars, seed)
                        self.assertLessEqual(err, 0.005,
                                             (rate, bpm, beats, bars, seed))

    def test_a_tempo_change(self):
        for rate in RATES:
            for seed in SEEDS:
                self.assertLessEqual(tempo_change_error(Flanger, rate, seed),
                                     0.005, (rate, seed))

    def test_the_bar_is_the_time_signature(self):
        # 3/4 is three quarter notes, 6/8 three, 7/8 three and a half; the
        # class once read the denominator alone as the beats in a bar.
        for numerator, denominator in ((3, 4), (6, 8), (7, 8)):
            for rate in RATES:
                err = synced_period_error(Flanger, rate, 120.0, numerator,
                                          1.0, 0, denominator)
                self.assertLessEqual(err, 0.005,
                                     (numerator, denominator, rate))

    def test_a_meter_change(self):
        for rate in RATES:
            for seed in SEEDS:
                self.assertLessEqual(meter_change_error(Flanger, rate, seed),
                                     0.005, (rate, seed))
        self.assertGreater(meter_change_error(MeterDeaf, 48000, 0), 0.005)

    def test_the_sync_knob(self):
        """Sync turned on from its knob, and from patch 5."""
        transport = Transport(90.0, 3)
        want = tempo_rate(90.0, 3, 1.0)
        for cls, red in ((Flanger, False), (FrozenSync, True)):
            readings = sweep_readings(
                cls, 48000, want, 0.6, 1.0, 0,
                frames=int(48000 / want * 1.05) + 576,
                options={"rate": 0.25}, transport=transport,
                actions={0: lambda e: e.set_macro(SYNC, 127)})
            err = abs(fit_rate(readings, 48000, 1.0, 0.6, want) / want - 1)
            self.assertEqual(err > 0.005, red, cls)
            feed = kc.feed(array("h", [0, 0]), 48000, 1)
            e = cls(feed.port, sample_rate=48000, transport=transport)
            e.program_change(5)
            self.assertEqual(abs(e._node.rate - want) > 1e-9, red, cls)
            e.deinit()

    def test_rate_is_ignored_and_20_hz_is_the_stop(self):
        transport = Transport(700.0, 4)
        self.assertGreater(tempo_rate(700.0, 4, 0.125), 20.0)
        readings = sweep_readings(
            Flanger, 48000, 20.0, 0.1, 1.0, 0, frames=24000,
            options={"rate": 3.0, "sync": True, "division": 0.125},
            transport=transport)
        self.assertLessEqual(abs(fit_rate(readings, 48000, 1.0, 0.1, 20.0)
                                 / 20.0 - 1.0), 0.005)

    def test_the_plant_is_red(self):
        err = synced_period_error(FourBeatBar, 48000, 90.0, 3, 1.0, 0)
        self.assertGreater(err, 0.005)
        self.assertLessEqual(
            synced_period_error(FourBeatBar, 48000, 120.0, 4, 1.0, 0), 0.005)


class T6Polarity(TestCase):
    """Polarity minus turns the comb over."""

    def test_the_comb_turns_over(self):
        for rate in RATES:
            for color in (0.0, 0.5, 0.95):
                low, high = color_laws(q15(color), negative=True)
                for seed in SEEDS:
                    at_k, at_half = comb_pair_db(Flanger, rate, color, True,
                                                 2.0 * math.pi * seed / 8.0)
                    self.assertLessEqual(abs(at_half - db(high)), 0.25)
                    if color > 0.0:
                        self.assertLessEqual(abs(at_k - db(low)), 0.25,
                                             (rate, color, seed, at_k))
                    else:
                        self.assertLessEqual(at_k, -40.0)

    def test_the_polarity_knob_and_patch_3(self):
        low, _ = color_laws(q15(0.5), negative=True)
        for cls, red in ((Flanger, False), (FrozenPolarity, True)):
            at_k, _ = knob_pair_db(cls, 48000, ((POLARITY, 127),))
            self.assertEqual(abs(at_k - db(low)) > 0.25, red, (cls, at_k))
            # Patch 3, "Negative jet", held still: its first peak is a dip.
            at_k, color = knob_pair_db(cls, 48000, (), patch=3)
            low3, _ = color_laws(q15(color), negative=True)
            self.assertEqual(abs(at_k - db(low3)) > 1.0, red, (cls, at_k))

    def test_color_0_subtracts_the_copy(self):
        for rate in RATES:
            for tau in T1_TAUS[rate]:
                for seed in SEEDS[:2]:
                    worst, _ = t1_worst(Flanger, rate, tau, 1.0, 1, seed,
                                        sign=-1)
                    self.assertLessEqual(worst, 1)

    def test_the_plants_are_red(self):
        for plant in (InvertOnly, FeedbackOnly):
            for color in (0.5, 0.95):
                low, _ = color_laws(q15(color), negative=True)
                at_k, _ = comb_pair_db(plant, 48000, color, True, 0.0)
                self.assertGreater(abs(at_k - db(low)), 1.0, plant)
        worst, _ = t1_worst(InvertOnly, 48000, 48, 1.0, 1, 0, sign=-1)
        self.assertEqual(worst, 0)          # Color 0: the byte check
        worst, _ = t1_worst(FeedbackOnly, 48000, 48, 1.0, 1, 0, sign=-1)
        self.assertGreater(worst, 2)


class TheAdoption(TestCase):
    def test_create_serves_this_class_from_its_own_module(self):
        import audiocore
        import audioeffects
        self.assertIs(audioeffects.Flanger, Flanger)
        self.assertEqual(Flanger.__module__, "audioeffects.flanger")
        served = audioeffects.create(
            "Flanger",
            audiocore.RawSample(array("h", [0, 0] * 64), sample_rate=48000,
                                channel_count=2),
            48000)
        self.assertIsInstance(served, Flanger)
        served.deinit()

    def test_both_old_flangers_are_gone(self):
        for name in ("audioeffects.modulation",
                     "audioeffects.rebuilt.flanger"):
            with self.assertRaises(ImportError):
                __import__(name)

    def test_the_tier_is_stock(self):
        from audioeffects import _component
        self.assertEqual(Flanger.TIER, _component.STOCK)
        self.assertEqual(Flanger.REQUIRES, ())


class TheSurface(TestCase):
    """The controls, the wire, latency, tail, reset and tempo."""

    def _fresh(self, sample_rate=48000, channels=1, **options):
        feed = kc.feed(array("h", bytes(4 * channels)), sample_rate,
                       channels)
        return Flanger(feed.port, sample_rate=sample_rate, **options)

    def test_range_0_holds_the_comb_at_manual(self):
        readings = sweep_readings(Flanger, 48000, 4.0, 0.0, 2.0, 0,
                                  frames=24000)
        for _, d in readings:
            self.assertAlmostEqual(d, 96.0, delta=0.01)

    def test_polarity_and_sync(self):
        e = self._fresh(polarity="negative", sync=True)
        self.assertEqual(e.get_macro(POLARITY), 127.0)
        self.assertEqual(e.get_macro(SYNC), 127.0)
        self.assertTrue(e._node.invert)
        self.assertLess(e._node.feedback, 0.0)
        e.deinit()
        with self.assertRaises(ValueError):
            self._fresh(polarity="minus")

    def test_rate_is_ignored_while_sync_is_on(self):
        e = self._fresh(sync=True)
        before = e._node.rate
        e.set_macro(RATE, 127)
        self.assertEqual(e._node.rate, before)
        self.assertAlmostEqual(before, tempo_rate(120.0, 4, 1.0))
        e.deinit()

    def test_a_fresh_instance_is_patch_0(self):
        e = self._fresh()
        self.assertEqual(e.patch_index, 0)
        self.assertEqual(tuple(e.get_macro(i) for i in range(8)),
                         tuple(float(v) for v in Flanger.PATCHES[0][1]))
        e.deinit()

    def test_constructor_values_play_exactly_until_their_knob_moves(self):
        e = self._fresh(rate=0.3, depth=0.33, manual_ms=1.7, color=0.41,
                        mix=0.77)
        node = e._node
        self.assertEqual((node.rate, node.depth, node.min_delay_ms,
                          node.feedback, node.mix),
                         (0.3, 0.33, 1.7, 0.41, 0.77))
        # A host echoing the knob back moves nothing.
        for i in range(5):
            e.set_macro(i, e.get_macro(i))
        self.assertEqual((node.rate, node.depth, node.min_delay_ms,
                          node.feedback, node.mix),
                         (0.3, 0.33, 1.7, 0.41, 0.77))
        e.set_macro(COLOR, e.get_macro(COLOR) + 1)
        self.assertNotEqual(node.feedback, 0.41)
        self.assertEqual(node.mix, 0.77)
        e.program_change(4)
        self.assertNotEqual(node.mix, 0.77)
        e.deinit()

    def test_a_restore_puts_the_exact_values_back(self):
        exact = (0.3, 0.33, 1.7, 0.41, 0.77)
        for cls, red in ((Flanger, False), (KeptNothing, True)):
            e = self._fresh(rate=0.3, depth=0.33, manual_ms=1.7, color=0.41,
                            mix=0.77)
            e.__class__ = cls
            record = e._record()
            e.program_change(2)
            e._reset_to = record
            e.reset()
            e._reset_to = None
            node = e._node
            got = (node.rate, node.depth, node.min_delay_ms, node.feedback,
                   node.mix)
            self.assertEqual(got != exact, red, (cls, got))
            e.deinit()

    def test_mix_s_first_step_is_a_wire_and_its_second_36_db_down(self):
        rate = 48000
        x = noise(9, 9600, 12000)
        options = held(48, rate)
        y = render(Flanger, x, rate, 1, options=options, macros=((MIX, 1),))
        self.assertEqual(list(y), list(x))
        y = render(Flanger, x, rate, 1, options=options, macros=((MIX, 2),))
        wet = [y[n] - x[n] for n in range(48, len(x))]
        level = db(math.sqrt(sum(v * v for v in wet) / len(wet))
                   / math.sqrt(sum(v * v for v in x[:-48]) / (len(x) - 48)))
        self.assertAlmostEqual(level, db(2.0 / 127.0), delta=0.2)
        self.assertAlmostEqual(level, -36.0, delta=0.5)

    def test_the_linear_range(self):
        """About -28 dBFS at full Color, -7.5 dBFS at Color 0, on a peak;
        the knee above."""
        rate, tau = 48000, 144
        f = rate / float(tau)
        for color, linear, hot in ((0.95, -28.0, -24.0), (0.0, -7.5, -3.0)):
            law = db(color_laws(q15(color))[0])
            got = []
            for level in (linear, hot):
                amp = int(32767 * 10.0 ** (level / 20.0))
                x = sine(f, rate, 28800, amp)
                y = render(Flanger, x, rate, 1,
                           options=held(tau, rate, color=color))
                got.append(db(amp_at(y, f, rate, 14400) / amp))
            self.assertLessEqual(abs(got[0] - law), 0.1, (color, got))
            self.assertLess(got[1], law - 0.5, (color, got))

    def test_no_wrap_at_the_input_ceiling(self):
        """The kit's ceiling check at -6 dBFS, mono, both rates: no wrap,
        no rail, no silence at any patch or knob stop."""
        import kit_ceiling
        self.assertEqual(Flanger.INPUT_CEILING_DBFS, -6.0)
        lines = []
        red = kit_ceiling.run(Flanger, emit=lines.append, channels=(1,))
        self.assertEqual(red, 0, [l for l in lines if "RED" in l][:3])

    def test_no_latency(self):
        self.assertEqual(Flanger.LATENCY_SAMPLES, 0)
        e = self._fresh()
        self.assertEqual(e.latency_samples, 0)
        e.deinit()

    def test_the_tail_is_the_card_s_bound(self):
        self.assertEqual(card_tail(0.95, 10.0, 48000), 98607)
        self.assertEqual(Flanger.TAIL_SAMPLES, 98607)
        self.assertEqual(card_tail(0.95, 5.5, 48000), 54327)
        for rate in RATES:
            for options in ({}, {"color": 0.0}, {"color": 0.95, "depth": 1.0},
                            {"color": 0.5, "depth": 0.0, "manual_ms": 3.0}):
                e = self._fresh(sample_rate=rate, **options)
                top = e.macro(MANUAL) + e.macro(RANGE) * (10.0 -
                                                          e.macro(MANUAL))
                self.assertEqual(e.tail_samples,
                                 card_tail(e.macro(COLOR), top, rate))
                self.assertLessEqual(e.tail_samples, Flanger.TAIL_SAMPLES)
                e.deinit()

    def test_reset_returns_to_patch_0(self):
        e = self._fresh()
        e.set_macro(COLOR, 0)
        e.program_change(3)
        e.reset()
        self.assertEqual(e.patch_index, 0)
        self.assertEqual(tuple(e.get_macro(i) for i in range(8)),
                         tuple(float(v) for v in Flanger.PATCHES[0][1]))
        e.deinit()

    def test_the_circuitpython_hang_is_a_stated_skip(self):
        import lifecycle
        self.assertIn(("Flanger", "E8-", "circuitpython"), lifecycle.SKIP)


# --------------------------------------------------------------------------
# The figures, on any interpreter


def native_report(emit=print):
    """One line per trait reading, the same on every interpreter whose node
    renders the same bytes (a reduced grid: the unit tests run the whole
    one on CPython)."""
    impl = sys.implementation.name
    for rate in RATES:
        for tau in T1_TAUS[rate]:
            for mix in (0.5, 1.0):
                worst = 0
                for seed in (0, 1):
                    worst = max(worst, t1_worst(Flanger, rate, tau, mix, 1,
                                                seed)[0])
                emit("%s|T1|%d|%d|%.1f|%d" % (impl, rate, tau, mix, worst))
        for color in (0.0, 0.95):
            for negative in (False, True):
                a, b = comb_pair_db(Flanger, rate, color, negative, 0.0)
                emit("%s|T2T6|%d|%.2f|%d|%.3f|%.3f"
                     % (impl, rate, color, negative, a, b))
        t60, sil, last, tail = ring_reading(Flanger, rate, 3.0, 0.95, 0)
        emit("%s|T3|%d|%.3f|%.3f|%d|%d" % (impl, rate, t60, sil, last, tail))
        readings = sweep_readings(Flanger, rate, 8.0, 0.5, 2.0, 0)
        emit("%s|T4|%d|%.4f" % (impl, rate, sweep_worst(readings, 8.0, rate,
                                                        2.0, 0.5)))
        emit("%s|T5|%d|%.5f" % (impl, rate, synced_period_error(
            Flanger, rate, 90.0, 3, 1.0, 0)))
    emit("%s|T3-end|%d|%d" % ((impl,) + end_then_replay(Flanger, True)))
    emit("DONE")


#: Each claim sentence of the docstring, word for word, and its tests.
CLAIMS = (
    ("Manual is the sweep's floor, and Range is how far it climbs "
     "from there towards 10 ms: at Range 0 the comb holds still at "
     "Manual.",
     ("T4Sweep.test_the_triangle",
      "TheSurface.test_range_0_holds_the_comb_at_manual")),
    ("Color feeds the copy back into the line and raises the comb's "
     "peaks into a ring.",
     ("T2Color.test_the_two_laws", "T3Ring.test_the_ring_follows_its_laws")),
    ("Mix is the copy's level against a dry that never moves: 1 is "
     "equal weight and the deepest notches, 0 is a wire.",
     ("T1Comb.test_the_comb_is_the_sum_in_integers",
      "T1Comb.test_a_notch_is_40_db_down",
      "T1Comb.test_mix_0_is_the_input_byte_for_byte")),
    ("With Sync on, one sweep lasts Division bars at the host's "
     "tempo and meter, and Rate is ignored.",
     ("T5Sync.test_the_period", "T5Sync.test_a_tempo_change",
      "TheSurface.test_rate_is_ignored_while_sync_is_on",
      "T5Sync.test_a_meter_change", "T5Sync.test_the_sync_knob")),
    ("Polarity minus turns the comb over and puts a notch at DC.",
     ("T6Polarity.test_the_comb_turns_over",
      "T6Polarity.test_the_polarity_knob_and_patch_3",
      "T6Polarity.test_color_0_subtracts_the_copy")),
    ("Constructor values play exactly until their knob first moves or a "
     "patch loads.",
     ("TheSurface.test_constructor_values_play_exactly_until_their_knob_"
      "moves", "TheSurface.test_a_restore_puts_the_exact_values_back")),
    ("The copy is your signal exactly Manual late, added at Mix.",
     "T1Comb.test_the_comb_is_the_sum_in_integers"),
    ("At Color 0 and Mix 1 a tone on a notch comes out at least 40 dB "
     "down.",
     "T1Comb.test_a_notch_is_40_db_down"),
    ("Color raises the peaks by up to 26.4 dB over the input and fills the "
     "notches to 6 dB under it.",
     ("T2Color.test_the_two_laws", "T2Color.test_full_color_and_color_0")),
    ("The sweep is a triangle in milliseconds that starts at Manual and "
     "reaches its top once a sweep.",
     ("T4Sweep.test_the_triangle",
      "T4Sweep.test_the_sweep_starts_at_manual_and_again_after_a_reset")),
    ("The ring lasts about 0.4 s to -60 dB at 3 ms and full Color, and "
     "about 0.7 s at 5 ms; it grows as Range sweeps the delay longer, and "
     "it never oscillates on its own.",
     ("T3Ring.test_the_longest_rings",
      "T3Ring.test_the_ring_follows_its_laws",
      "T3Ring.test_the_swept_ring_is_inside_the_tail")),
    ("It is linear only to about -28 dBFS on a resonant frequency at full "
     "Color, and -7.5 dBFS at Color 0: above that the output is squashed "
     "and gritty, not louder.",
     "TheSurface.test_the_linear_range"),
    ("Turning Mix up makes the output louder, by 6 dB on a comb peak "
     "at Mix 1: there is no wet-only setting.",
     ("T2Color.test_full_color_and_color_0",)),
    ("There is no tone control, no through-zero and no stereo spread: both "
     "channels sweep together.",
     "T4Sweep.test_both_channels_sweep_together"),
    ("Sync sets the sweep's period, not its phase: the sweep starts at "
     "Manual when the class is built or reset, not on a bar line, and a "
     "synced sweep faster than 20 Hz runs at 20 Hz.",
     ("T4Sweep.test_the_sweep_starts_at_manual_and_again_after_a_reset",
      "T5Sync.test_rate_is_ignored_and_20_hz_is_the_stop")),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "DECLARED:Flanger,E4-,P5"),
    ("At 22.05 kHz the sweep's top is 9.977 ms, half a frame under 10 ms.",
     "T4Sweep.test_the_top_at_22050_is_half_a_frame_under_10_ms"),
    ("Mix's first step above 0 is still a wire; the copy comes in at the "
     "second step, about 36 dB down.",
     "TheSurface.test_mix_s_first_step_is_a_wire_and_its_second_36_db_down"),
    ("Keep the input under -6 dBFS.",
     "TheSurface.test_no_wrap_at_the_input_ceiling"),
    ("At Mix 0 the output is the input, byte for byte.",
     "T1Comb.test_mix_0_is_the_input_byte_for_byte"),
    ("There is no latency.", "TheSurface.test_no_latency"),
    ("`tail_samples` is the longest the ring can last at the controls in "
     "force, while the source keeps playing, silence included.",
     ("TheSurface.test_the_tail_is_the_card_s_bound",
      "T3Ring.test_the_ring_follows_its_laws",
      "T3Ring.test_the_swept_ring_is_inside_the_tail")),
    ("If the source ends, the output stops dead; `reset()` clears what the "
     "line held and returns to patch 0.",
     ("T3Ring.test_the_source_ends_and_reset_clears_the_line",
      "TheSurface.test_reset_returns_to_patch_0")),
    ("On a CircuitPython board, stop the flanger from the host if your "
     "source can run dry: CircuitPython's own flanger waits on a source "
     "that comes back empty. Firmware built with micropython-pydevices' "
     "build_mp.py carries the fix and returns.",
     "TheSurface.test_the_circuitpython_hang_is_a_stated_skip"),
)


if __name__ == "__main__":
    if "--report" in sys.argv:
        native_report()
    elif unittest is not None:
        unittest.main()
