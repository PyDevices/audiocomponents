"""`Exciter`'s own invariant and planted-fault tests.

Dossier: workspace docs/effects-internal/dossiers/Exciter.md, frozen
2026-09-17. Exhaustive rate coverage lives in the evidence pack; this
file asserts at 48 kHz unless the test is about rate or latency.

Headline numbers are the shipped default: Tune 4 kHz, Harmonics 0.25,
Mix 0.3, Character classic, Output 0 dB.
"""

import math
import os
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import kit_faults                                               # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects.rebuilt import exciter as rebuilt             # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
Exciter = rebuilt.Exciter


def sine(hz, dbfs, frames=48000, rate=RATE, channels=2):
    index = np.arange(frames)
    values = 10.0 ** (dbfs / 20.0) * np.sin(2.0 * math.pi * hz * index / rate)
    quantised = np.clip(np.round(values * 32767.0), -32768, 32767).astype(
        np.int64)
    if channels == 2:
        quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist())


def build(cls=None, rate=RATE, channels=2, frames=48000, probe=None,
          **options):
    cls = cls or Exciter
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, label=None, class_name="Exciter",
                         latency_samples=effect.latency_samples)


def worst_inband(rendered, hz, guard=6, low=20.0, high=20000.0):
    """T7 as its sentence reads: the worst SINGLE inharmonic line in
    20 Hz-20 kHz, re the fundamental, with a skirt cut round every harmonic
    below Nyquist. The kit's `alias_floor_db` sums every non-harmonic bin to
    Nyquist instead, so a fold landing above 20 kHz counts in it and does not
    count in the trait.

    Blackman-Harris, because the worst SINGLE line has no averaging to hide
    a skirt in: when this was written `exact_bin_size` rounded, the
    fundamental sat a fraction of a bin off centre, and its own leakage read
    about -52 dB thirteen bins out - which is not an alias. It no longer
    rounds, and at the tones this class is measured at the length it returns
    is whole periods (`docs/dev/exact-bin-size.md`), but the window stays:
    the fallback length is still a fraction of a sample off, and a trait
    stated as one line is the readout that would show it.
    """
    start = int(rendered.frames * 0.5)
    x = rendered.float[start:, 0]
    size = kit.exact_bin_size(len(x), rendered.rate, hz)
    mags, bin_hz, _, _ = kit.magnitude_spectrum(x, rendered.rate, size=size,
                                                window="blackmanharris")
    mask = np.ones(len(mags), dtype=bool)
    mask[:3] = False
    order = 1
    while hz * order < rendered.rate / 2.0:
        centre = int(round(hz * order / bin_hz))
        mask[max(0, centre - guard):centre + guard + 1] = False
        order += 1
    freqs = np.arange(len(mags)) * bin_hz
    mask &= (freqs >= low) & (freqs <= high)
    centre = int(round(hz / bin_hz))
    base = float(mags[max(0, centre - 2):centre + 3].max())
    selected = mags[mask]
    index = int(np.argmax(selected))
    return (20.0 * math.log10(float(selected[index]) / base),
            float(freqs[mask][index]))


def odd_curve():
    """Odd-symmetric tanh: planted T2 fault of the same kind (no even)."""
    points = 1025
    out = array("h")
    last = points - 1
    for i in range(points):
        x = -1.0 + 2.0 * i / last
        y = math.tanh(2.5 * x)
        out.append(max(-32768, min(32767, int(round(y * 32767.0)))))
    return out


def probe_hz_for(rate, tune):
    """T2's and T7's probe rule: the highest tone at or above the sidechain's
    corner whose h3 still lands below 0.45 × rate, capped at 1.375 × corner
    (5500 Hz at the default). The frozen 8 kHz put h3 at Nyquist and could not
    be measured at any shipped rate (audiocomponents#72)."""
    hz = min(1.375 * tune, 0.45 * rate / 3.0)
    return None if hz < tune else hz


class WetExciter(Exciter):
    """The sidechain alone: the same mixer with the dry voice muted.

    Not the shaper pulled directly. An instrument that points `_output` at a
    node inside the graph never pulls the Mixer, so it sits one mixer block
    earlier in the stream than the class's own output and runs off the end
    of its probe - which is worth 70 dB of measurement floor
    (audiocomponents#78). The Splitter's unread tap is not what costs it;
    the kit refuses the instrument anyway, because its offset is not the
    offset anything it is compared against was measured at. Read off
    `self._shaper` the drift here is −33.5 dB where the same signal through
    the mixer reads −103.6 dB.

    Muting the dry voice keeps every tap pulled and the class's own offset,
    and it is the stricter reading as well: neither Mix nor Output can
    dilute an alias or a harmonic into looking healthy. Every wet-path
    measurement here goes through the mixer.
    """

    NAME = "Exciter"

    def _prime_if_wet(self):
        Exciter._prime_if_wet(self)
        if self._output is self._blend:
            self._blend.voice[0].level = 0.0


class OddClipper(WetExciter):
    """T2: odd-symmetric table at the class's default macros. An odd curve
    makes no even harmonics at all, which is the one thing a one-sided diode
    must do."""

    NAME = "Exciter"

    def _build(self, **options):
        WetExciter._build(self, **options)
        self._shaper.set(curve=odd_curve())
        self._odd = True


class FirstOrderHP(kit_faults._Node):
    """A genuine 6 dB/octave high-pass, for T1's fault."""

    def __init__(self, source, hz, rate, channels):
        kit_faults._Node.__init__(self, source)
        k = math.tan(math.pi * hz / rate)
        self.b0 = 1.0 / (1.0 + k)
        self.a1 = (k - 1.0) / (1.0 + k)
        self.ch = channels
        self.zx = [0.0] * channels
        self.zy = [0.0] * channels

    def _process(self, frames):
        block = frames.reshape(-1, self.ch)
        out = np.empty_like(block)
        for c in range(self.ch):
            x = block[:, c]
            y = np.empty_like(x)
            px, py = self.zx[c], self.zy[c]
            for n in range(len(x)):
                py = self.b0 * (x[n] - px) - self.a1 * py
                px = x[n]
                y[n] = py
            self.zx[c], self.zy[c] = px, py
            out[:, c] = y
        return out.reshape(-1)


class FirstOrder(WetExciter):
    """T1's fault, of the kind App. B asks for: the biquad made a wire and a
    one-pole bilinear high-pass at the same corner put in its place. This
    exercises the filter's ORDER. `NoHighPass` below only exercises its
    presence, which is not what T1 claims (audiocomponents#72)."""

    NAME = "Exciter"

    def _build(self, **options):
        WetExciter._build(self, **options)
        self._hp.mix = 0.0
        self._one = FirstOrderHP(self._hp, self._tune_hz(), self._sample_rate,
                                 self._channel_count)
        self._shaper.play(self._one)

    def _refresh(self):
        WetExciter._refresh(self)
        self._hp.mix = 0.0
        # Re-derive the one-pole from the corner the class is ACTUALLY using
        # on every macro move. Built once in `_build` and left there, the
        # fault's filter and the class's corner were different frequencies
        # away from the constructor's Tune, and two Tune stops (MIDI 64 and
        # 72) landed the reading back inside T1's bar -- a guard a user could
        # dial healthy (audiocomponents#72, second audit ruling (i)).
        one = getattr(self, "_one", None)
        if one is not None:
            k = math.tan(math.pi * self._tune_hz() / self._sample_rate)
            one.b0 = 1.0 / (1.0 + k)
            one.a1 = (k - 1.0) / (1.0 + k)


class NoHighPass(WetExciter):
    """The filter mixed out: a presence guard, kept as a second fault."""

    NAME = "Exciter"

    def _refresh(self):
        Exciter._refresh(self)
        self._hp.mix = 0.0


class DryHalf(Exciter):
    """T4's guard for "dry is unity at every Mix": dry path not unity.

    The fault is unchanged; the BAR moved 2026-09-17. It used to be an
    absolute 0.05 FS drop in the mixed output's peak, and since Output trims
    the whole class that went healthy at 11 of 17 Output stops, at Mix 0 and
    at three shipped patches, without touching the mechanism
    (audiocomponents#72, second audit ruling (i)). The bar is now the
    clause's own statistic, a ratio with Output divided out.
    """

    NAME = "Exciter"

    def _prime_if_wet(self):
        Exciter._prime_if_wet(self)
        if self._output is self._blend:
            self._blend.voice[0].level *= 0.5


class WetOverDry(Exciter):
    """T4's guard for the headline clause: the wet summed OVER the dry."""

    NAME = "Exciter"

    def _prime_if_wet(self):
        Exciter._prime_if_wet(self)
        if self._output is self._blend:
            self._blend.voice[1].level *= 2.2


def dry_gain(cls, output_db=0.0, **options):
    """The dry leg's gain against what Output asked for.

    The mirror of `kit_probes.wet_render`: it mutes voice 0 and renders the
    class's own mixer, this mutes voice 1 and renders the same mixer. Output
    divides out, so a working class reads 1.000 at every position.
    """
    probe = sine(1000, -12)
    effect = build(cls, probe=probe, output_db=output_db, **options)
    keep = effect._blend.voice[1].level
    effect._blend.voice[1].level = 0.0
    peak = float(np.max(np.abs(render(effect, 48000).float)))
    effect._blend.voice[1].level = keep
    effect.deinit()
    want = 10.0 ** (-12.0 / 20.0) * 10.0 ** (output_db / 20.0)
    return peak / want


def wet_dry_ratio(cls, settled=False, **options):
    """T4's headline statistic through the supported wet-branch instrument."""
    probe = sine(probe_hz_for(RATE, options.get("tune", 4000.0)), -12)
    full = build(cls, probe=probe, **dict(options, mix=0.7))
    dry = build(cls, probe=probe, **dict(options, mix=0.0))
    start = 24000 if settled else 0
    wet = probes.wet_render(full, 48000, allow_tail_frames=8, rate=RATE,
                            channels=2, block=256, class_name="Exciter",
                            latency_samples=full.latency_samples)
    pw = float(np.max(np.abs(wet.float[start:])))
    pd = float(np.max(np.abs(render(dry, 48000).float[start:])))
    full.deinit()
    dry.deinit()
    return 100.0 * pw / pd


def identity_curve():
    """A straight line through the shaper's table: the control audit 4
    asked for.

    The step is exactly 64 LSB over 1025 points, so the ramp is integral
    at every entry and the node's linear interpolation between two of them
    is exact. A build carrying it makes **no h2 at all** — every node in
    front of the shaper and behind it is linear.
    """
    points = len(rebuilt.CURVE)
    last = points - 1
    return array("h", [max(-32768, min(32767,
                                       int(round(-32768.0 + 65535.0 * i
                                                 / last))))
                       for i in range(points)])


IDENTITY_CURVE = identity_curve()


class IdentityCurve(Exciter):
    """The shipped graph with a straight table (audiocomponents#72 item 6).

    Kept in this file rather than in a probe because it is the control a
    harmonic reading is *checked against*: `TheHarmonicReadersControl`
    runs it before believing anything `OddClipper` says.
    """

    NAME = "Exciter"

    def _build(self, **options):
        Exciter._build(self, **options)
        self._shaper.set(curve=IDENTITY_CURVE)

    def _refresh(self):
        Exciter._refresh(self)
        self._shaper.set(curve=IDENTITY_CURVE)


class WireShaper(Exciter):
    """Stricter than the identity curve: the shaper mixed **out**.

    `mix=0` makes the node hand its input straight back, so the wet branch
    is high-pass, wire, coupling pole, mixer — and `pre_gain` / `post_gain`
    are out of the picture as well. That matters, because the identity
    curve is read through the class's own drive split (`pre` 0.094,
    `post` 10.7 at the default), which quantises in Q15 and is the reason
    the identity control's floor sits around −65 dB rather than −100.
    """

    NAME = "Exciter"

    def _build(self, **options):
        Exciter._build(self, **options)
        self._shaper.set(mix=0.0)

    def _refresh(self):
        Exciter._refresh(self)
        self._shaper.set(mix=0.0)


def h2h3(rendered, hz, window="blackmanharris", size=None, span=4,
         settled=0.5):
    """h2 and h3 re the fundamental, windowed, over the whole segment.

    The reader the packs used (`R.h23` in `probes/exciter_refute2.py`)
    calls `kit.spectrum(..., size=None, window=None)`, which asks
    `exact_bin_size` for a rectangular length. T2's probe rule is
    `1.375 × corner` on a LOG macro, so the probe and the rate are usually
    incommensurable and `exact_bin_size` falls back — **floored at 64
    samples**. At 22.05 kHz with a 1102.65 Hz probe over 2205 frames it
    returns 64, whose bins are 344.5 Hz wide, and a ±2-bin peak at the
    fundamental (bin 3.2) and at h2 (bin 6.4) reads the same energy twice.
    That is the whole of the −11 to −21 dB "h2" audit 4 reproduced on a
    curve that makes none.

    A window does not care whether the length is periodic, which is what
    `exact_bin_size`'s own docstring says to reach for when it falls back.
    `window=None` here is the old reader, kept so the plant can ask for it.
    """
    start = int(rendered.frames * settled)
    x = rendered.float[start:, 0]
    if window is None and size is None:
        size = kit.exact_bin_size(len(x), rendered.rate, hz)
        span = 2
    mags, bin_hz, _name, _used = kit.magnitude_spectrum(
        x, rendered.rate, size=size or len(x), window=window)
    nyquist = rendered.rate / 2.0

    def peak(f):
        if f >= nyquist:
            return None
        centre = int(round(f / bin_hz))
        return float(mags[max(0, centre - span):centre + span + 1].max())

    base = peak(hz)
    if not base:
        return None, None
    out = []
    for order in (2, 3):
        value = peak(hz * order)
        out.append(None if value is None
                   else 20.0 * math.log10(value / base + 1e-30))
    return out[0], out[1]


class BaseRateExciter(WetExciter):
    """T7: ×1 at the class's default macros."""

    NAME = "Exciter"

    def _build(self, **options):
        options["oversample"] = 1
        WetExciter._build(self, **options)


class ClassicLocked(Exciter):
    """T5: Dynamics stays a wire while Character reads transient."""

    NAME = "Exciter"

    def _route_character(self, transient):
        Exciter._route_character(self, transient)
        if self._dyn is not None:
            self._dyn.set(attack_gain_db=0.0, sustain_gain_db=0.0)


class TestExciter(unittest.TestCase):
    def test_mix_zero_is_wire(self):
        probe = sine(1000, -12)
        effect = build(probe=probe, mix=0.0)
        wet = render(effect, 48000)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            48000, rate=RATE, channels=2, block=256)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])

    def test_t2_asymmetry_is_h2_over_h3_at_default(self):
        # The one-sided diode's signature is h2 AT OR ABOVE h3. The frozen
        # "|h2-h3| < 10 dB" bar failed in the direction of MORE asymmetry -
        # at Harmonics 1.0 the gap is 24.6 dB with h2 on top - and its 8 kHz
        # headline probe put h3 at Nyquist. Redefined under vision 7.2
        # (audiocomponents#72). Probe by the rule; measured on the wet path.
        hz = probe_hz_for(RATE, 4000.0)
        for dbfs in (-20, -12, -6):
            spec = kit.spectrum(
                render(build(WetExciter, probe=sine(hz, dbfs)), 48000),
                hz, harmonics=6, size=None)
            h2 = spec["values"]["harmonic_db"]["h2"]
            h3 = spec["values"]["harmonic_db"]["h3"]
            self.assertIsNotNone(h2, dbfs)
            self.assertIsNotNone(h3, dbfs)
            self.assertGreater(h2, h3, "h2 %s h3 %s at %d dBFS"
                               % (h2, h3, dbfs))
            self.assertGreater(h2, -60.0, dbfs)

    def test_t2_fault_odd_curve_kills_h2_at_default(self):
        hz = probe_hz_for(RATE, 4000.0)
        clean = kit.spectrum(
            render(build(WetExciter, probe=sine(hz, -6)), 48000),
            hz, harmonics=6, size=None)["values"]["harmonic_db"]
        dirty = kit.spectrum(
            render(build(OddClipper, probe=sine(hz, -6)), 48000),
            hz, harmonics=6, size=None)["values"]["harmonic_db"]
        self.assertGreater(clean["h2"], clean["h3"])
        self.assertLess(dirty["h2"], dirty["h3"])
        self.assertLess(dirty["h2"], -60.0)

    def test_t2_null_build_red(self):
        hz = probe_hz_for(RATE, 4000.0)

        def measure_with(cls):
            spec = kit.spectrum(render(build(cls, probe=sine(hz, -6)),
                                       48000), hz, harmonics=6, size=None)
            h2 = spec["values"]["harmonic_db"]["h2"]
            h3 = spec["values"]["harmonic_db"]["h3"]
            passed = (h2 is not None and h3 is not None
                      and h2 > h3 and h2 > -60.0)
            return {"passed": passed, "h2": h2, "h3": h3}

        result = kit_faults.null_build_red(WetExciter, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t7_alias_at_default_and_full_drive(self):
        # Measured on the wet branch, worst single in-band line, because on
        # the mixed output Mix and Output dilute the wet and its aliases
        # together while the dry keeps the fundamental - the shape that read
        # healthy at 8 of 92 surface positions (audiocomponents#72).
        hz = probe_hz_for(RATE, 4000.0)
        worst, _ = worst_inband(render(build(WetExciter, probe=sine(hz, -6)),
                                       48000), hz)
        self.assertLess(worst, -60.0)
        full, _ = worst_inband(
            render(build(WetExciter, probe=sine(1010, -6), tune=600.0,
                         harmonics=1.0, mix=0.7), 48000), 1010)
        self.assertLess(full, -60.0)

    def test_t7_fault_oversample_1_at_default(self):
        hz = probe_hz_for(RATE, 4000.0)
        probe = sine(hz, -6)
        clean, _ = worst_inband(render(build(WetExciter, probe=probe), 48000),
                                hz)
        fault, _ = worst_inband(
            render(build(BaseRateExciter, probe=probe), 48000), hz)
        self.assertLess(clean, -60.0)
        self.assertGreater(fault, -60.0)
        self.assertGreater(fault - clean, 40.0)

    def test_t7_fault_is_not_dialled_back_by_output_or_mix(self):
        # The old fault read healthy at Output MIDI 0-40 and at Mix 0/8.
        # Output now trims both voices, and the measurement is the wet branch,
        # so neither macro moves the ratio.
        hz = probe_hz_for(RATE, 4000.0)
        probe = sine(hz, -6)
        for index, positions in ((2, (8, 40, 127)), (4, (0, 24, 40, 127))):
            for pos in positions:
                effect = build(BaseRateExciter, probe=probe)
                effect.set_macro(index, pos)
                worst, _ = worst_inband(render(effect, 48000), hz)
                effect.deinit()
                self.assertGreater(worst, -60.0,
                                   "macro %d = %d read %.3f" % (index, pos,
                                                                worst))

    def test_t7_null_build_red(self):
        hz = probe_hz_for(RATE, 4000.0)
        probe = sine(hz, -6)

        def measure_with(cls):
            # The bar AND the mechanism being active: a wire has no h2 at
            # all, so "no aliases" alone is green on a null build.
            rendered = render(build(cls, probe=probe), 48000)
            h2 = kit.spectrum(rendered, hz, harmonics=6,
                              size=None)["values"]["harmonic_db"]["h2"]
            worst, _ = worst_inband(rendered, hz)
            active = h2 is not None and h2 > -60.0
            return {"passed": bool(active and worst < -60.0),
                    "h2": h2, "worst": worst}

        result = kit_faults.null_build_red(WetExciter, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t1_second_order_at_default_tune(self):
        # Passband reference is 0.45 x rate, written down: the frozen 8 x Tune
        # is above Nyquist for half the frozen Tune grid at every shipped rate.
        def db(hz):
            effect = build(WetExciter, probe=sine(hz, -40), harmonics=0.0,
                           mix=0.7)
            x = render(effect, 48000).float[12000:, 0]
            effect.deinit()
            return 20.0 * math.log10(float(np.sqrt(np.mean(x * x))) + 1e-12)

        passband = db(0.45 * RATE)
        at_tune = db(4000) - passband
        octave = db(2000) - passband
        self.assertAlmostEqual(at_tune, -3.0, delta=1.0)
        self.assertGreater(octave, -13.8)
        self.assertLess(octave, -10.8)

    def test_t1_fault_first_order_at_default(self):
        def octave(cls):
            def db(hz):
                effect = build(cls, probe=sine(hz, -40), harmonics=0.0,
                               mix=0.7)
                x = render(effect, 48000).float[12000:, 0]
                effect.deinit()
                return 20.0 * math.log10(
                    float(np.sqrt(np.mean(x * x))) + 1e-12)

            return db(2000) - db(0.45 * RATE)

        clean = octave(WetExciter)
        first = octave(FirstOrder)
        absent = octave(NoHighPass)
        self.assertLess(clean, -10.8)
        self.assertGreater(clean, -13.8)
        # A genuine one-pole at the same corner: App. F predicts 7.0 dB.
        self.assertGreater(first, -9.0)
        self.assertLess(first, -5.0)
        # And the presence guard, kept as a second fault.
        self.assertGreater(absent, -1.0)

    def test_t1_holds_at_every_rate_because_tune_is_clamped(self):
        # 22.05 kHz read -14.762 at Tune 5000 and -16.170 at Tune 6000 before
        # the rate/7 clamp (audiocomponents#72).
        for rate in (48000, 44100, 22050):
            frames = rate // 2

            def db(hz, tune):
                effect = build(WetExciter, rate=rate, frames=frames,
                               probe=sine(hz, -40, frames=frames, rate=rate),
                               harmonics=0.0, mix=0.7, tune=tune)
                corner = effect._tune_hz()
                x = render(effect, frames, rate=rate).float[frames // 4:, 0]
                effect.deinit()
                return (corner, 20.0 * math.log10(
                    float(np.sqrt(np.mean(x * x))) + 1e-12))

            for tune in (600.0, 6000.0):
                corner, _ = db(0.45 * rate, tune)
                self.assertLessEqual(corner, rate / 7.0 + 1.0)
                passband = db(0.45 * rate, tune)[1]
                octave = db(corner / 2.0, tune)[1] - passband
                self.assertGreater(octave, -13.8, "%d Hz, Tune %g" % (rate,
                                                                      tune))
                self.assertLess(octave, -10.8, "%d Hz, Tune %g" % (rate, tune))

    def test_t1_null_build_red(self):
        def measure_with(cls):
            def db(hz):
                effect = build(cls, probe=sine(hz, -40), harmonics=0.0,
                               mix=0.7)
                # Wire builds output the source: slope is 0 dB.
                x = render(effect, 48000).float[12000:, 0]
                effect.deinit()
                return 20.0 * math.log10(
                    float(np.sqrt(np.mean(x * x))) + 1e-12)

            octave = db(2000) - db(0.45 * RATE)
            passed = -13.8 <= octave <= -10.8
            return {"passed": passed, "octave": octave}

        result = kit_faults.null_build_red(WetExciter, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t4_mix_max_under_dry(self):
        # In-band condition: the tone is at or above the sidechain's corner.
        # A 1 kHz tone at the shipped Tune 4 kHz is two octaves BELOW it and
        # reads 8.35 % - that is the high-pass working, not T4 failing.
        for tune in (600.0, 4000.0, 6000.0):
            hz = 1.375 * tune
            dry = build(probe=sine(hz, -12), tune=tune, harmonics=1.0,
                        mix=0.0)
            wet = build(WetExciter, probe=sine(hz, -12), tune=tune,
                        harmonics=1.0, mix=0.7)
            pd = float(np.max(np.abs(render(dry, 48000).float)))
            pw = float(np.max(np.abs(render(wet, 48000).float)))
            dry.deinit()
            wet.deinit()
            self.assertGreater(pw / pd, 0.20, "Tune %g" % tune)
            self.assertLess(pw / pd, 0.70, "Tune %g" % tune)

    def test_t4_wet_dry_does_not_move_with_output(self):
        # Output +6 dB used to put the wet at 131.4 % of the dry, because it
        # reached `Waveshaper.post_gain` alone (audiocomponents#72).
        ratios = []
        for out_db in (-24.0, -12.0, 0.0):
            dry = build(probe=sine(825, -12), tune=600.0, harmonics=1.0,
                        mix=0.0, output_db=out_db)
            wet = build(WetExciter, probe=sine(825, -12), tune=600.0,
                        harmonics=1.0, mix=0.7, output_db=out_db)
            pd = float(np.max(np.abs(render(dry, 48000).float)))
            pw = float(np.max(np.abs(render(wet, 48000).float)))
            dry.deinit()
            wet.deinit()
            ratios.append(pw / pd)
        for ratio in ratios:
            self.assertGreater(ratio, 0.20)
            self.assertLess(ratio, 0.70)
        self.assertLess(max(ratios) - min(ratios), 0.01)

    def test_output_attenuates_the_whole_effect(self):
        # Before the fix, moving Output over its whole span moved the peak by
        # 0.006 FS, and at Mix 0 it did nothing at all.
        for mix in (0.3, 0.0):
            peaks = {}
            for out_db in (-24.0, -12.0, 0.0):
                effect = build(probe=sine(1000, -12), mix=mix,
                               output_db=out_db)
                peaks[out_db] = float(
                    np.max(np.abs(render(effect, 48000).float)))
                effect.deinit()
            for out_db in (-24.0, -12.0):
                want = peaks[0.0] * 10.0 ** (out_db / 20.0)
                self.assertAlmostEqual(peaks[out_db] / want, 1.0, delta=0.02,
                                       msg="Mix %g, Output %g" % (mix,
                                                                  out_db))

    def test_output_span_has_no_makeup_above_unity(self):
        self.assertEqual(Exciter._MACRO_RANGES[4], (-24.0, 0.0))

    def test_t1_fault_first_order_tracks_the_corner(self):
        # The two Tune stops the pass-2 refuter dialled the old fault healthy
        # at, and the two ends of the macro. The fault re-derives its one-pole
        # from `_tune_hz()` on every macro move, so it reads ~7 dB at all of
        # them instead of drifting back inside T1's 10.8-13.8 dB bar.
        for midi in (0, 64, 72, 127):
            clean = build(WetExciter, probe=probes.silence(512, 2),
                          frames=512)
            clean.set_macro(0, midi)
            corner = clean._tune_hz()
            clean.deinit()
            probe_lo = sine(corner / 2.0, -40)
            probe_ref = sine(0.45 * RATE, -40)

            def octave(cls, midi=midi):
                # Built at the CONSTRUCTOR's Tune and moved with the macro
                # afterwards, which is what a user does and what the old
                # fault could not follow.
                one = build(cls, probe=probe_lo, mix=0.7)
                two = build(cls, probe=probe_ref, mix=0.7)
                one.set_macro(0, midi)
                two.set_macro(0, midi)
                lo = float(np.sqrt(np.mean(
                    render(one, 24000).float[6000:, 0] ** 2)))
                ref = float(np.sqrt(np.mean(
                    render(two, 24000).float[6000:, 0] ** 2)))
                one.deinit()
                two.deinit()
                return 20.0 * math.log10((lo + 1e-12) / (ref + 1e-12))

            self.assertTrue(-13.8 <= octave(WetExciter) <= -10.8,
                            "clean at MIDI %d" % midi)
            self.assertGreater(octave(FirstOrder), -10.8,
                               "fault at MIDI %d" % midi)

    def test_t4_fault_dry_half_fires_at_every_output(self):
        # The old bar was an absolute 0.05 FS peak drop, and Output trims the
        # whole class, so it went healthy at 11 of 17 Output stops. The bar
        # is the clause's own ratio now and Output divides out of it.
        for output_db in (-24.0, -18.0, -12.0, -6.0, 0.0):
            self.assertAlmostEqual(dry_gain(Exciter, output_db=output_db),
                                   1.0, delta=0.05,
                                   msg="clean at Output %g" % output_db)
            self.assertLess(dry_gain(DryHalf, output_db=output_db), 0.6,
                            "fault at Output %g" % output_db)

    def test_t4_fault_wet_over_dry_fires_at_every_output(self):
        for output_db in (-24.0, -12.0, 0.0):
            clean = wet_dry_ratio(Exciter, output_db=output_db)
            fault = wet_dry_ratio(WetOverDry, output_db=output_db)
            self.assertTrue(20.0 <= clean <= 70.0,
                            "clean %g at Output %g" % (clean, output_db))
            self.assertGreater(fault, 70.0,
                               "fault %g at Output %g" % (fault, output_db))

    def test_t4_holds_on_transient_once_the_onset_has_passed(self):
        # `transient` claims T1-T4 as well (dossier S3's Char. column). At
        # the old +12 dB / 50 ms onset the settled half read 72.2-76.0 %,
        # over T4's ceiling. The probe is a steady sine: the only onset in
        # the render is the render's own start, which is the row's named
        # step-edge exception.
        settled = wet_dry_ratio(Exciter, character=1.0, settled=True)
        self.assertTrue(20.0 <= settled <= 70.0, settled)
        for tune in (600.0, 6000.0):
            value = wet_dry_ratio(Exciter, character=1.0, tune=tune,
                                  settled=True)
            self.assertTrue(20.0 <= value <= 70.0,
                            "Tune %g: %g" % (tune, value))

    def test_transient_onset_gain_is_short_and_declared(self):
        self.assertEqual(rebuilt.TRANSIENT_ATTACK_DB, 6.0)
        self.assertEqual(rebuilt.TRANSIENT_SUSTAIN_DB, -12.0)
        self.assertEqual(rebuilt.TRANSIENT_FAST_RELEASE_MS, 8.0)

    def test_t3_h2_rises_with_level(self):
        h2s = []
        for dbfs in (-40, -6):
            spec = kit.spectrum(
                render(build(WetExciter, probe=sine(1000, dbfs),
                             tune=600.0, harmonics=1.0, mix=0.7), 48000),
                1000, harmonics=6, size=4800)
            h2s.append(spec["values"]["harmonic_db"]["h2"])
        self.assertGreater(h2s[1] - h2s[0], 20.0)

    def test_latency_zero_click(self):
        probe = probes.click_stereo(frames=8192, offset=256, channels=2)
        effect = build(probe=probe, frames=8192)
        wet = render(effect, 8192)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            8192, rate=RATE, channels=2, block=256)
        result = kit.click(wet, dry, 0, subsample=False)
        self.assertTrue(result["passed"], result["red"])

    def test_tail_returns_to_zero_at_default(self):
        probe, on = probes.burst_silence(hz=5500.0, on_ms=200.0, total_s=1.0,
                                         dbfs=-6.0, rate=RATE, channels=2)
        effect = build(probe=probe, frames=RATE)
        wet = render(effect, RATE)
        result = kit.tail(wet, burst_end_frame=on,
                          declared_tail_samples=effect.tail_samples)
        self.assertTrue(result["passed"], result["red"])
        self.assertEqual(result["values"]["residual_lsb"], 0)
        # 512 until the third fix round put a 30 Hz coupling pole behind
        # the diode: the worst ring across three rates and eight builds is
        # 3 085 frames now, and `TAIL_SAMPLES` declares 4 096 for it.
        self.assertLessEqual(result["values"]["tail_samples"],
                             rebuilt.Exciter.TAIL_SAMPLES)

    def test_tail_fault_held_dc_at_default(self):
        probe, on = probes.burst_silence(hz=5500.0, on_ms=200.0, total_s=1.0,
                                         dbfs=-6.0, rate=RATE, channels=2)
        effect = build(probe=probe, frames=RATE)
        clean = render(effect, RATE)
        self.assertTrue(kit.tail(clean, burst_end_frame=on)["passed"])
        faulted_pcm = bytearray(clean.pcm)
        faulted_pcm[(RATE - 100) * 4] = 1
        faulted = kit.Render.from_pcm(bytes(faulted_pcm), RATE, 2)
        result = kit.tail(faulted, burst_end_frame=on)
        self.assertFalse(result["passed"], result)

    def test_t3_null_build_red(self):
        def measure_with(cls):
            h2s = []
            for dbfs in (-40, -6):
                spec = kit.spectrum(
                    render(build(cls, probe=sine(1000, dbfs),
                                 tune=600.0, harmonics=1.0, mix=0.7),
                           48000),
                    1000, harmonics=6, size=4800)
                h2s.append(spec["values"]["harmonic_db"]["h2"])
            passed = (h2s[0] is not None and h2s[1] is not None
                      and (h2s[1] - h2s[0]) > 20.0)
            return {"passed": passed, "h2s": h2s}

        result = kit_faults.null_build_red(WetExciter, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t4_null_build_red(self):
        def measure_with(cls):
            def peak(mix):
                effect = build(cls, probe=sine(1000, -12), tune=600.0,
                               harmonics=1.0, mix=mix)
                return float(np.max(np.abs(render(effect, 48000).float)))

            dry = peak(0.0)
            extra = (peak(0.7) - dry) / dry if dry else 0.0
            passed = 0.20 < extra < 0.70
            return {"passed": passed, "extra": extra}

        result = kit_faults.null_build_red(Exciter, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_never_uses_distortion_node(self):
        with open(rebuilt.__file__, encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("audiofilters.Distortion", text)
        self.assertIn("audioshaper.Waveshaper", text)

    def test_capabilities_and_tail_match_what_was_built(self):
        effect = build(probe=probes.silence(256, 2), frames=256)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.tail_samples, 4096)
        self.assertEqual(effect.TIER, "audioif")
        effect.reset()
        effect.deinit()

    def test_t5_classic_default_has_no_onset_emphasis(self):
        # Shipped default is classic: T5 must not hold here.
        frames = 24000
        start = int(0.05 * RATE)
        n = np.arange(frames)
        sig = np.zeros(frames)
        sig[start:] = (10.0 ** (-18 / 20.0)
                       * np.sin(2.0 * math.pi * 5000 * n[start:] / RATE))
        q = np.clip(np.round(sig * 32767), -32768, 32767).astype(np.int64)
        q = np.repeat(q[:, None], 2, axis=1)
        probe = array("h", q.reshape(-1).tolist())
        effect = build(WetExciter, probe=probe, frames=frames, tune=3000.0,
                       harmonics=0.8, mix=0.7, character=0.0)
        x = render(effect, frames).float[:, 0]

        def mag(a, b):
            seg = x[a:b] * np.hanning(b - a)
            spec = np.abs(np.fft.rfft(seg))
            freqs = np.fft.rfftfreq(b - a, 1.0 / RATE)
            h2 = spec[np.argmin(np.abs(freqs - 10000))]
            h3 = spec[np.argmin(np.abs(freqs - 15000))]
            return 20.0 * math.log10(float(h2 + h3) + 1e-18)

        onset = mag(start, start + int(0.05 * RATE))
        steady = mag(frames - int(0.15 * RATE), frames - int(0.05 * RATE))
        self.assertLess(onset - steady, 6.0)

    def test_odd_fault_not_on_the_macro_surface(self):
        out = kit_faults.fault_reachability(
            Exciter, OddClipper,
            lambda effect: bool(getattr(effect, "_odd", False)),
            lambda cls: build(cls, probe=probes.silence(512, 2), frames=512),
            label="Exciter T2 OddClipper")
        self.assertNotEqual(out["target"], out["clean"])

    def test_x1_fault_not_on_the_macro_surface(self):
        out = kit_faults.fault_reachability(
            Exciter, BaseRateExciter,
            lambda effect: int(effect._oversample),
            lambda cls: build(cls, probe=probes.silence(512, 2), frames=512),
            label="Exciter T7 BaseRate")
        self.assertEqual(out["target"], 1)
        self.assertEqual(out["clean"], 4)

    def test_classic_does_not_build_a_dynamics_node(self):
        # `classic` is S1's fixed threshold: nothing between the high-pass and
        # the diode. Leaving Dynamics in the chain at 0 dB cost a palette row
        # (0.394 ms P4 / 0.753 S3) for a wire at the shipped default.
        effect = build(probe=probes.silence(512, 2), frames=512)
        self.assertIsNone(effect._dyn)
        self.assertIs(effect._chain, effect._hp)
        effect.set_macro(3, 127)
        self.assertIsNotNone(effect._dyn)
        self.assertIs(effect._chain, effect._dyn)
        effect.set_macro(3, 0)
        self.assertIs(effect._chain, effect._hp)
        effect.deinit()
        for patch, wants_dynamics in ((0, False), (1, True), (2, False),
                                      (3, False), (4, True), (5, True),
                                      (6, False)):
            one = build(probe=probes.silence(512, 2), frames=512, patch=patch)
            self.assertEqual(one._chain is one._dyn, wants_dynamics,
                             "patch %d" % patch)
            one.deinit()

    def test_oversample_2_is_not_a_lean_position(self):
        # It was documented as one until 2026-09-17, on the strength of the
        # two points the docstring named. Over T7's own grid x2 is red at 19
        # of 60 readings, worst -35.5 dB, and it was red on shipped patch 2
        # at the old drive. This pins the refutation so nobody re-documents
        # it: the class's own default Tune at full Harmonics is enough.
        hz = probe_hz_for(RATE, 6000.0)
        worst, _ = worst_inband(
            render(build(WetExciter, probe=sine(hz, -6), tune=6000.0,
                         harmonics=1.0, mix=0.7, oversample=2), 48000), hz)
        self.assertGreater(worst, -60.0, worst)
        # ...and x4, which ships, holds it at the same point.
        shipped, _ = worst_inband(
            render(build(WetExciter, probe=sine(hz, -6), tune=6000.0,
                         harmonics=1.0, mix=0.7), 48000), hz)
        self.assertLess(shipped, -60.0, shipped)

    def test_harmonics_span_is_fourteen_db(self):
        # +24 dB drove the 1N914 26x past its 0.6 V knee: 1.76 dB more h2 at
        # -6 dBFS and 6.7 dB more fold. The macro's own 0..1 span is
        # unchanged; what it commands is not.
        self.assertEqual(rebuilt.HARMONICS_SPAN_DB, 14.0)
        # And the drive that constant commands, measured: h2 at the top of
        # the Harmonics macro on a -20 dBFS probe reads -21.4 dB at +14 dB of
        # span and -11.6 dB at +24, so this bar cannot survive the span
        # moving by 2 dB in either direction.
        spec = kit.spectrum(
            render(build(WetExciter, probe=sine(5500, -20), tune=4000.0,
                         harmonics=1.0, mix=0.7), 48000),
            5500, harmonics=4, size=kit.exact_bin_size(5500, RATE, 24000))
        h2 = spec["values"]["harmonic_db"]["h2"]
        self.assertTrue(-24.0 < h2 < -19.0, h2)


class TheThirdFixRoundsRows(unittest.TestCase):
    """What audit 3 §4(p) asked this class for: an input ceiling, a DC row
    that reads under material, and a clause `BaseRate` cannot be healthy
    under."""

    def rails_at(self, dbfs, hz, patch=None, frames=9600, **options):
        if patch is not None:
            options["patch"] = patch
        effect = build(probe=sine(hz, dbfs, frames + 2048), frames=frames,
                       **options)
        try:
            wet = render(effect, frames)
        finally:
            effect.deinit()
        values = wet.data[frames // 2:, 0].astype(np.int64)
        return int(np.sum((values >= 32767) | (values <= -32768)))

    def test_nothing_rails_at_the_stated_ceiling(self):
        ceiling = rebuilt.INPUT_CEILING_DBFS
        for hz in (1000.0, 3000.0, 5500.0, 8000.0):
            for patch in sorted(Exciter.PATCHES):
                self.assertEqual(
                    self.rails_at(ceiling, hz, patch=patch), 0,
                    "patch %d rails at the stated ceiling (%s dBFS, "
                    "%.0f Hz)" % (patch, ceiling, hz))
            self.assertEqual(
                self.rails_at(ceiling, hz, harmonics=1.0, mix=1.0), 0,
                "Harmonics max / Mix max rails at %s dBFS, %.0f Hz"
                % (ceiling, hz))

    def test_above_the_ceiling_the_rail_is_reachable(self):
        """Or the number is charity."""
        self.assertGreater(self.rails_at(-2.0, 5500.0, patch=6), 0)
        self.assertGreater(
            self.rails_at(-2.0, 5500.0, harmonics=1.0, mix=1.0), 0)

    def dc_under_material(self, patch=None, dbfs=-6.0, hz=5500.0,
                          frames=9600, **options):
        """The DC a silence test can never see: this class's offset only
        exists while it is making harmonics."""
        if patch is not None:
            options["patch"] = patch
        effect = build(probe=sine(hz, dbfs, frames + 2048), frames=frames,
                       **options)
        try:
            wet = render(effect, frames)
        finally:
            effect.deinit()
        return float(wet.data[frames // 2:, 0].astype(np.int64).mean())

    def test_no_shipped_patch_stands_dc_on_its_own_tone(self):
        for patch in sorted(Exciter.PATCHES):
            mean = self.dc_under_material(patch=patch)
            self.assertLess(
                abs(mean), 16.0,
                "patch %d stands %+.1f LSB of DC on its own in-band tone"
                % (patch, mean))

    def test_the_hot_corner_does_not_either(self):
        mean = self.dc_under_material(dbfs=-6.0, harmonics=1.0, mix=1.0)
        self.assertLess(abs(mean), 16.0, mean)

    def test_the_planted_class_is_the_one_that_does(self):
        """`NoOutputPole` is the class at `80d5a26`: the only high-pass was
        upstream of the diode."""
        for patch in (1, 3, 6):
            mean = self.dc_under_material(patch=patch, cls=NoOutputPole)
            self.assertGreater(
                abs(mean), 100.0,
                "the planted class has to stand DC at patch %d or the rows "
                "above prove nothing (%+.1f)" % (patch, mean))

    def t7_at(self, rate, tune_midi, harm_midi=127, dbfs=-6.0):
        effect = build(probe=sine(1000.0, -6, 2048, rate=rate),
                       frames=2048, rate=rate)
        effect.set_macro(0, tune_midi)
        tune = effect._value(0)
        effect.deinit()
        hz = probe_hz_for(rate, tune)
        if hz is None:
            return None, tune
        frames = rate
        wet = build(WetExciter,
                    probe=sine(hz, dbfs, frames + 2048, rate=rate),
                    frames=frames, rate=rate)
        wet.set_macro(0, tune_midi)
        wet.set_macro(1, harm_midi)
        try:
            worst, _at = worst_inband(render(wet, frames, rate=rate), hz)
        finally:
            wet.deinit()
        return worst, tune

    def test_t7_holds_up_to_the_stated_input_ceiling(self):
        """And not above it. The row is a -6 dBFS reading and the class
        rails at -2, so its level clause ends where the ceiling does."""
        for dbfs in (-6.0, -3.0):
            worst, _tune = self.t7_at(RATE, 127)
            self.assertLess(worst, -60.0, dbfs)
        for dbfs in (-1.0, 0.0):
            worst, _tune = self.t7_at(RATE, 127, dbfs=dbfs)
            self.assertGreater(
                worst, -65.0,
                "above the ceiling T7 is not claimed, and %s dBFS reads "
                "%.3f" % (dbfs, worst))

    def test_t7_is_disconfirmed_at_22k_between_the_grids_points(self):
        """The four places that said "the whole 22.05 kHz column is green
        (worst -64.4 dB)" read the Tune grid's own stops. Walked at every
        eighth stop with Harmonics at maximum, six of twelve are over the
        bar - and a row that is false at half its positions is
        disconfirmed, not restated."""
        red = []
        readable = 0
        for midi in range(0, 128, 8):
            worst, tune = self.t7_at(22050, midi)
            if worst is None:
                continue
            readable += 1
            if worst > -60.0:
                red.append((midi, round(tune), round(worst, 3)))
        self.assertGreaterEqual(readable, 10, readable)
        self.assertGreaterEqual(len(red), 5, (readable, red))
        self.assertLess(min(row[2] for row in red), -35.0, red)

    def test_the_oversampling_is_worth_its_clause_where_tune_is_up(self):
        """T7e: `BaseRate` x1 was healthy at 21 of 276 positions under the
        absolute bar alone, all of them the bottom of the Tune macro. The
        clause says what the factor is worth where the sidechain is high
        enough to fold, and x1's own cost is 0 dB by construction."""
        thin = []
        outside = []
        for midi in range(0, 128, 16):
            effect = build(probe=sine(1000.0, -6, 2048), frames=2048)
            effect.set_macro(0, midi)
            tune = effect._value(0)
            effect.deinit()
            hz = probe_hz_for(RATE, tune)
            if hz is None:
                continue
            probe = sine(hz, -6)
            clean_effect = build(WetExciter, probe=probe)
            clean_effect.set_macro(0, midi)
            clean, _ = worst_inband(render(clean_effect, RATE), hz)
            clean_effect.deinit()
            fault_effect = build(BaseRateExciter, probe=probe)
            fault_effect.set_macro(0, midi)
            fault, _ = worst_inband(render(fault_effect, RATE), hz)
            fault_effect.deinit()
            row = (midi, round(tune, 1), round(clean, 3), round(fault, 3),
                   round(fault - clean, 3))
            if tune >= rebuilt.OVERSAMPLE_CLAUSE_TUNE_HZ:
                if fault - clean < rebuilt.ALIAS_OVERSAMPLE_COST_DB:
                    thin.append(row)
            else:
                outside.append(row)
        self.assertEqual(thin, [], thin)
        for row in outside:
            self.assertLess(
                row[3], -60.0,
                "below the clause's own corner the class is claimed to meet "
                "its absolute bar at x1, and %r does not" % (row,))


class NoOutputPole(Exciter):
    """The class at `80d5a26`: the only high-pass upstream of the diode,
    so the rectified offset walks out on any in-band tone."""

    NAME = 'Exciter'

    def _prime_if_wet(self):
        Exciter._prime_if_wet(self)
        if getattr(self, "_primed", False):
            self._blend.voice[1].play(self._shaper)


class TheTierOneRowsAtEveryShippedPatch(unittest.TestCase):
    """audiocomponents#87.

    `Exciter` declares no BIPOLAR macro (UNIPOLAR x4 plus a TOGGLE), so
    the centre detent has nothing to bite on here and these rows did not
    move. They are taken anyway, because pass 3 found standing DC of -28
    to -41 dBFS on every shipped patch and it was worth ruling out the
    same cause: this class's mean comes from the 1N914 table being a wire
    below zero and a compressor above it with the only high-pass in front
    of it, not from a macro that cannot reach its centre. On digital
    silence there is nothing for that table to rectify, so every patch is
    silent in, silent out and inside the declared tail.
    """

    #: Nothing is red here, and that is the claim.
    RED = {}

    RED_TAIL = {}

    def peaks(self):
        """`{patch: (silence_peak, tail_samples, residual, declared)}`."""
        rows = {}
        for patch in sorted(Exciter.PATCHES):
            effect = build(probe=probes.silence(RATE, 2), patch=patch)
            quiet = render(effect, RATE)
            effect.deinit()
            probe, burst_end = probes.burst_silence(
                hz=5500.0, on_ms=200.0, total_s=1.0, dbfs=-6.0, rate=RATE,
                channels=2)
            effect = build(probe=probe, patch=patch)
            wet = render(effect, len(probe) // 2)
            declared = effect.tail_samples
            effect.deinit()
            result = kit.tail(wet, burst_end_frame=burst_end,
                              declared_tail_samples=declared)
            rows[patch] = (int(np.abs(quiet.data).max()),
                           result["values"]["tail_samples"],
                           result["values"]["residual_lsb"], declared)
        return rows

    def test_silence_in_is_silence_out_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                if patch in self.RED:
                    self.assertGreater(row[0], 0, self.RED[patch])
                    continue
                self.assertEqual(row[0], 0,
                                 "patch %d emits %d LSB into digital "
                                 "silence" % (patch, row[0]))

    def test_the_declared_tail_holds_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            _quiet, tail_samples, residual, declared = row
            with self.subTest(patch=patch, why=self.RED_TAIL.get(patch)):
                if patch in self.RED_TAIL:
                    self.assertGreater(residual, 0, self.RED_TAIL[patch])
                    continue
                self.assertEqual(residual, 0,
                                 "patch %d never returns to zero (%d LSB "
                                 "left)" % (patch, residual))
                self.assertLessEqual(tail_samples or 0, declared,
                                     "patch %d rings %s samples against a "
                                     "declared %s"
                                     % (patch, tail_samples, declared))

    def test_program_change_onto_digital_silence_stays_silent(self):
        """A patch change is a wire message and can arrive between notes."""
        for patch in sorted(Exciter.PATCHES):
            effect = build(probe=probes.silence(RATE, 2), patch=0)
            before = render(effect, RATE // 2)
            effect.program_change(patch)
            after = render(effect, RATE // 2)
            effect.deinit()
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                self.assertEqual(int(np.abs(before.data).max()), 0)
                peak = int(np.abs(after.data).max())
                if patch in self.RED:
                    self.assertGreater(peak, 0, self.RED[patch])
                    continue
                self.assertEqual(peak, 0,
                                 "program_change(%d) on silence emitted %d "
                                 "LSB" % (patch, peak))


class TheHarmonicReadersControl(unittest.TestCase):
    """audiocomponents#72 item 6, the row audit 4 parked this class on.

    Ruling (a) asks whether every planted fault fires at the default and is
    unreachable from the surface, and this pack's macro-surface fault walks
    were read with an instrument the audit had found reporting **h2 that is
    not there** — an identity curve read as −13.283 dB (pass 3) and
    −20.755 dB (audit 4). A reader that fires on nothing makes every fault
    look like it fired, so the walks could not be certified. The audit
    asked for the control a harmonic reader should have had from the start:
    *an identity curve must read no h2.*

    **What the leak actually was.** Not the class, not the curve, and not
    the coupling pole: the **transform length**. Both quoted readings come
    from a probe that read the first 0.1 s of a render, where
    `exact_bin_size(2205, 22050, 1102.65)` returns its 64-sample floor —
    1102.65 Hz at 22.05 kHz needs 147 000 samples to be exactly periodic.
    At 64 samples the bins are 344.5 Hz wide, the fundamental sits at bin
    3.2 and h2 at bin 6.4, and a ±2-bin peak at each reads the same energy
    twice. Read over the settled half, which is where `R.h23` reads, the
    same identity build gives **−92.629 dB** at that cell.

    These rows hold the control at a reduced grid; the full 240-cell walk
    and the four re-run fault walks are `probes/exciter_fix4.py`.
    """

    #: The plant's handles. Together, `WINDOW=None`, `READ_DIVISOR=10` and
    #: `SETTLED=0.0` are exactly `probes/exciter_fix3.py reader`'s
    #: instrument: a rectangular read of the first tenth of a second, which
    #: is where `exact_bin_size` hands back its 64-sample floor.
    WINDOW = "blackmanharris"
    READ_DIVISOR = 2
    SETTLED = 0.5

    #: The build under the control. A plant points it at the shipped class,
    #: which does make h2, so a row that passes whatever it is handed shows
    #: up as one.
    CONTROL = staticmethod(lambda: IdentityCurve)

    #: T2's own axes, thinned: three rates, three Tunes, two probe ratios.
    #: The probe rule is the row's own, so most of these are incommensurable
    #: with their rate - which is the case the reader has to survive.
    CELLS = tuple((rate, tune, ratio)
                  for rate in (48000, 44100, 22050)
                  for tune in (600.0, 1000.0, 4000.0)
                  for ratio in (1.0, 1.375))

    def _h2(self, cls, rate, tune, ratio, dbfs=-6.0, mix=0.7):
        corner = min(tune, rate * Exciter.TUNE_RATE_FRACTION)
        hz = ratio * corner
        if hz * 3.0 >= 0.45 * rate:
            return None, None, hz
        frames = rate // self.READ_DIVISOR
        probe = sine(hz, dbfs, frames + 1024, rate=rate)
        effect = build(cls, rate=rate, frames=frames, probe=probe,
                       tune=tune, harmonics=0.25, mix=mix)
        try:
            wet = probes.wet_render(effect, frames, allow_tail_frames=8,
                                    rate=rate, channels=2, block=256,
                                    class_name="Exciter",
                                    latency_samples=effect.latency_samples)
        finally:
            effect.deinit()
        return h2h3(wet, hz, window=self.WINDOW,
                    settled=self.SETTLED) + (hz,)

    def test_an_identity_curve_reads_no_h2_at_any_cell(self):
        """The control. T2's second clause is "h2 above −60 dB of the
        fundamental", so a floor at or over −60 dB makes that clause
        unfalsifiable at the cell — and there is no such cell."""
        cls = self.CONTROL()
        worst = None
        for rate, tune, ratio in self.CELLS:
            h2, _h3, hz = self._h2(cls, rate, tune, ratio)
            if h2 is None:
                continue
            if worst is None or h2 > worst[0]:
                worst = (h2, rate, tune, hz)
            self.assertLess(
                h2, -60.0,
                "a build that makes no h2 reads %.3f dB of it at %d Hz, "
                "Tune %.0f, probe %.1f Hz" % (h2, rate, tune, hz))
        self.assertIsNotNone(worst)

    def test_the_wire_build_is_quieter_still(self):
        """The identity curve is read through the class's own drive split,
        which quantises in Q15; the shaper mixed out is not. If the two
        ever crossed, the control's floor would be the reader's and not the
        class's."""
        worst_identity = worst_wire = None
        for rate, tune, ratio in self.CELLS[:6]:
            ident = self._h2(IdentityCurve, rate, tune, ratio)[0]
            wire = self._h2(WireShaper, rate, tune, ratio)[0]
            if ident is None or wire is None:
                continue
            worst_identity = max(worst_identity or -999.0, ident)
            worst_wire = max(worst_wire or -999.0, wire)
        self.assertIsNotNone(worst_wire)
        self.assertLess(worst_wire, -60.0, worst_wire)
        self.assertLess(worst_wire, worst_identity + 0.5,
                        (worst_wire, worst_identity))

    def test_the_odd_curve_is_red_where_the_control_is_silent(self):
        """The fault the control exists to license. At the shipped default
        the class makes h2 well over the clause and `OddClipper` — an odd
        table, which makes no even harmonics — does not, while the control
        makes none either. The three readings are what tells a fault that
        fired from a reader that fires on anything."""
        clean = self._h2(Exciter, 48000, 4000.0, 1.375)[0]
        fault = self._h2(OddClipper, 48000, 4000.0, 1.375)[0]
        control = self._h2(IdentityCurve, 48000, 4000.0, 1.375)[0]
        self.assertGreater(clean, -60.0, clean)
        self.assertLess(fault, -60.0, (clean, fault))
        self.assertLess(control, -60.0, (clean, control))
        self.assertGreater(clean - fault, 20.0, (clean, fault))

    def test_the_length_is_what_the_audit_caught(self):
        """The mechanism, as a row. `exact_bin_size` floors at 64 samples,
        and 64 samples at 22.05 kHz cannot separate 1102.65 Hz from its own
        second harmonic. The same segment read with a window says −92 dB.
        """
        rate, hz, frames = 22050, 1102.65, 2205
        self.assertEqual(kit.exact_bin_size(frames, rate, hz), 64)
        probe = sine(hz, -6.0, rate + 1024, rate=rate)
        effect = build(IdentityCurve, rate=rate, frames=rate, probe=probe)
        try:
            rendered = render(effect, rate, rate=rate)
        finally:
            effect.deinit()
        tenth = float(frames) / rendered.frames
        rect = h2h3(rendered, hz, window=None, settled=0.0)[0]
        short = h2h3(rendered, hz, window=None, size=64, settled=0.0)[0]
        windowed = h2h3(rendered, hz, window="blackmanharris",
                        settled=0.0)[0]
        self.assertGreater(short, -30.0, short)
        self.assertLess(windowed, -85.0, windowed)
        self.assertLess(rect, -85.0, rect)
        self.assertGreater(tenth, 0.0)


class TheClassHandsBackThePalettesOwnBlock(unittest.TestCase):
    """256 frames per pull, at either channel count and both characters.

    `Mixer._render_size` is `buffer_size // 2 // 4 * 4` BYTES, so the 1024
    this class shipped rendered **128 stereo frames** and everything behind
    it was pulled twice per 256-frame block — including, on `transient`, an
    `audiodynamics.Dynamics` whose own output block is 256 frames by
    construction (`audioif_dynamics.h:56`). The board's rows show it: adding
    that node cost the class 0.537 ms on the P4 and 1.234 on the S3 where
    the palette prices it 0.495 / 0.985 (audiocomponents#72, fifth round).
    """

    def _frames_per_pull(self, channels, patch):
        import audiocore
        effect = build(channels=channels)
        effect.program_change(patch)
        try:
            lengths = []
            for _ in range(3):
                _result, buffer = audiocore.get_buffer(effect.output)
                lengths.append(len(buffer) // (2 * channels))
            return lengths
        finally:
            effect.deinit()

    def test_every_pull_is_one_palette_block(self):
        for channels in (2, 1):
            for patch in (0, 1):
                lengths = self._frames_per_pull(channels, patch)
                self.assertEqual(lengths, [256, 256, 256],
                                 "%d channel, patch %d: %s"
                                 % (channels, patch, lengths))

    def test_the_shipped_buffer_is_red(self):
        """The plant: the 1024 the class shipped, which reads 128."""
        kept = rebuilt.MIXER_BUFFER_BYTES
        rebuilt.MIXER_BUFFER_BYTES = 512
        try:
            lengths = self._frames_per_pull(2, 0)
        finally:
            rebuilt.MIXER_BUFFER_BYTES = kept
        self.assertEqual(lengths, [128, 128, 128],
                         "the plant did not fire: %s" % (lengths,))

    def test_the_block_length_moves_no_sample(self):
        """A cost change and nothing else, on both characters: the same
        5 kHz render comes back byte for byte at either block length."""
        material = sine(5000.0, -18.0, 24000)
        kept = rebuilt.MIXER_BUFFER_BYTES
        try:
            for patch in (0, 1):
                renders = []
                for size in (512, 1024):
                    rebuilt.MIXER_BUFFER_BYTES = size
                    effect = build(probe=material, frames=24000)
                    effect.program_change(patch)
                    renders.append(render(effect, 24000).pcm)
                    effect.deinit()
                self.assertEqual(renders[0], renders[1],
                                 "patch %d renders differently at 128 and "
                                 "256 frames" % patch)
        finally:
            rebuilt.MIXER_BUFFER_BYTES = kept


if __name__ == "__main__":
    unittest.main()
