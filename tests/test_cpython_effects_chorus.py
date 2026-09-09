"""`Chorus`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Chorus.md`; Tier 2
rows are T1–T6. Each row here is the measurement and the same measurement
shown red on a fault of the same kind. Exhaustive rates live in the evidence
pack, not in this file.
"""

import math
import os
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                            # noqa: E402
import kit_faults                                           # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import chorus as rebuilt                  # noqa: E402
import kit_probes as probes                                 # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
RATE_I, DEPTH_I, MIX_I, DELAY_I, TONE_I = range(5)


class RegeneratingChorus(rebuilt.Chorus):
    """T1: a decaying train. Feedback is not a macro."""

    NAME = 'Chorus'
    FEEDBACK = 0.3

    def _refresh(self):
        rebuilt.Chorus._refresh(self)
        self._plant_feedback = type(self).FEEDBACK
        self._delay.set(feedback=type(self).FEEDBACK)


class LinearTriangleChorus(rebuilt.Chorus):
    """T2: delay linear in a triangle LFO."""

    NAME = 'Chorus'

    def _refresh(self):
        rebuilt.Chorus._refresh(self)
        self._plant_linear_triangle = True
        depth = self._value(DEPTH_I)
        mean_ms = self._value(DELAY_I)
        tri = array("h", [
            int(round(rebuilt._unit_triangle(i, rebuilt.SHAPE_LEN) * 32767.0))
            for i in range(rebuilt.SHAPE_LEN)])
        self._shape = tri
        self._delay.set(
            delay_ms=mean_ms,
            wow_depth_ms=mean_ms * depth,
            wow_shape=self._shape)


class OpenToneChorus(rebuilt.Chorus):
    """T3: reconstruction filter off. Tone's floor is 1 kHz, not 0."""

    NAME = 'Chorus'

    def _refresh(self):
        rebuilt.Chorus._refresh(self)
        self._plant_open_tone = True
        self._delay.set(damping_hz=0.0)


class HalfMixChorus(rebuilt.Chorus):
    """T4: wet halved after the Mix law."""

    NAME = 'Chorus'

    def _refresh(self):
        rebuilt.Chorus._refresh(self)
        self._plant_half_mix = True
        self._delay.set(mix=self._value(MIX_I) * 0.5)


class DoubleRateChorus(rebuilt.Chorus):
    """T5: Rate law writes 16 Hz at every surface position.

    ×2 at the constructor's 0.8 Hz is 1.6 Hz, still inside T5's 0.3–12 Hz
    bar (gate audit / independent refuter). Sixteen hertz is above 12 at
    the default and at every Rate, so the stated bar goes red where the
    user starts, and no macro or patch restores a Rate-law LFO.
    """

    NAME = 'Chorus'
    PLANTED_HZ = 16.0

    def _refresh(self):
        rebuilt.Chorus._refresh(self)
        self._plant_double_rate = True
        self._planted_wow_hz = type(self).PLANTED_HZ
        self._delay.set(wow_hz=type(self).PLANTED_HZ)


class SineWowChorus(rebuilt.Chorus):
    """T6: additive sine on the delay (`wow_shape=None`)."""

    NAME = 'Chorus'

    def _refresh(self):
        rebuilt.Chorus._refresh(self)
        self._plant_sine_wow = True
        self._delay.set(wow_shape=None)


class WetOnly(rebuilt.Chorus):
    """Measurement helper, not a fault: Mix 2 on the node (wet alone)."""

    NAME = 'Chorus'

    def _refresh(self):
        rebuilt.Chorus._refresh(self)
        self._delay.set(mix=2.0)


class WetOnlyLinear(LinearTriangleChorus):
    NAME = 'Chorus'

    def _refresh(self):
        LinearTriangleChorus._refresh(self)
        self._delay.set(mix=2.0)


class WetOnlySine(SineWowChorus):
    NAME = 'Chorus'

    def _refresh(self):
        SineWowChorus._refresh(self)
        self._delay.set(mix=2.0)


class WetOnlyOpen(OpenToneChorus):
    NAME = 'Chorus'

    def _refresh(self):
        OpenToneChorus._refresh(self)
        self._delay.set(mix=2.0)


def impulse_src(frames, at=32, channels=2, rate=RATE, block=256, level=32000):
    data = array("h", [0] * (frames * channels))
    for ch in range(channels):
        data[at * channels + ch] = level
    return probes.ArraySource(data, rate=rate, channels=channels, block=block)


def sine_src(hz, frames, channels=2, rate=RATE, block=256, level=8000):
    data = array("h")
    for frame in range(frames):
        value = int(level * math.sin(2.0 * math.pi * hz * frame / rate))
        for _ in range(channels):
            data.append(value)
    return probes.ArraySource(data, rate=rate, channels=channels, block=block)


def silence_src(frames, channels=2, rate=RATE, block=256):
    data = array("h", [0] * (frames * channels))
    return probes.ArraySource(data, rate=rate, channels=channels, block=block)


def pull_left(effect, frames, channels=None):
    channels = channels or effect.channel_count
    out = array("h")
    while len(out) < frames * channels:
        data = memoryview(bytes(audiocore.get_buffer(effect.output)[1]))
        if not data:
            break
        out.extend(data.cast("h"))
    return np.array(out[:frames * channels:channels], dtype=np.int16)


def build(cls=None, rate=RATE, channels=2, frames=48000, source=None,
          **options):
    cls = cls or rebuilt.Chorus
    if source is None:
        source = silence_src(frames, channels=channels, rate=rate)
    return cls(source, sample_rate=rate, **options)


def arrivals(x, threshold=100):
    peaks = []
    i = 0
    n = len(x)
    while i < n:
        if abs(int(x[i])) >= threshold:
            j = i
            best = i
            best_a = abs(int(x[i]))
            while j < n and abs(int(x[j])) >= threshold // 4:
                if abs(int(x[j])) > best_a:
                    best_a = abs(int(x[j]))
                    best = j
                j += 1
            peaks.append((best, best_a))
            i = j
        else:
            i += 1
    return peaks


def inst_hz(x, rate):
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    spec = np.fft.fft(x)
    h = np.zeros(n)
    h[0] = 1.0
    if n % 2 == 0:
        h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[1:(n + 1) // 2] = 2.0
    analytic = np.fft.ifft(spec * h)
    phase = np.unwrap(np.angle(analytic))
    return np.diff(phase) * rate / (2.0 * math.pi)


def half_ratio(hz, rate, lfo_hz, skip_periods=1):
    skip = int(skip_periods * rate / lfo_hz)
    body = hz[skip:]
    period = int(round(rate / lfo_hz))
    half = period // 2
    if half < 32 or len(body) < period:
        return 1.0
    offset = np.abs(body[:period] - 1000.0)
    a = offset[:half]
    b = offset[half:2 * half]
    ratios = []
    for chunk in (a, b):
        lo = float(np.percentile(chunk, 10)) + 1e-9
        hi = float(np.percentile(chunk, 90))
        ratios.append(hi / lo)
    return max(ratios)


def delay_trajectory(cls, rate=RATE, lfo_hz=4.0, seconds=2.0, hop=1024):
    # hop-1024 Nyquist is fs/(2·hop): 23.44 Hz at 48 kHz, 10.77 Hz at
    # 22050. A 16 Hz plant aliases into 0.3–12 at 22050 unless hop ≤ 512.
    hop = max(int(hop), 64)
    frames = int(rate * seconds)
    data = array("h", [0] * (frames * 2))
    for n in range(0, frames, hop):
        data[n * 2] = 32000
        data[n * 2 + 1] = 32000
    src = probes.ArraySource(data, rate=rate, channels=2, block=256)
    effect = cls(src, sample_rate=rate, rate=lfo_hz)
    left = pull_left(effect, frames)
    delays = []
    times = []
    for n in range(0, frames - hop, hop):
        window = left[n:n + hop]
        mag = np.abs(window.astype(np.int32)).astype(np.float64)
        mag[:16] = 0
        peak_at = int(np.argmax(mag))
        if mag[peak_at] < 200:
            continue
        lo = max(16, peak_at - 4)
        hi = min(len(mag), peak_at + 5)
        weight = float(np.sum(mag[lo:hi]))
        centre = float(np.dot(np.arange(lo, hi), mag[lo:hi])) / (weight + 1e-12)
        delays.append(centre)
        times.append(n / float(rate))
    return np.array(times), np.array(delays, dtype=np.float64)


def second_harmonic_db(samples, sample_dt, lfo_hz):
    x = np.asarray(samples, dtype=np.float64) - np.mean(samples)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), sample_dt)
    f1 = np.argmin(np.abs(freqs - lfo_hz))
    f2 = np.argmin(np.abs(freqs - 2.0 * lfo_hz))
    a1 = abs(spec[f1]) + 1e-12
    a2 = abs(spec[f2])
    phase = np.angle(spec[f2]) - 2.0 * np.angle(spec[f1])
    return 20.0 * math.log10(a2 / a1), phase


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = rebuilt.Chorus
        self.assertEqual(cls.MACRO_LABELS,
                         ("Rate", "Depth", "Mix", "Delay", "Tone"))
        self.assertEqual(len(cls.PATCHES), 7)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TIER, _component.AUDIOIF)
        self.assertEqual(cls.REQUIRES, ("audioecho",))
        effect = build()
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(0, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)

    def test_adopted_chorus_is_the_rebuild(self):
        import audioeffects
        self.assertIs(audioeffects.Chorus, rebuilt.Chorus)
        self.assertTrue(issubclass(audioeffects.Chorus,
                                   audioeffects._component.Component))

    def test_patch_0_is_the_constructor_grid(self):
        effect = build()
        grid = rebuilt.Chorus.PATCHES[0][1]
        for index, expected in enumerate(grid):
            self.assertAlmostEqual(effect.get_macro(index), expected, delta=0.6)


class T1OneVoice(unittest.TestCase):
    def _wet_peak_and_tail(self, cls):
        src = impulse_src(RATE * 2, at=32)
        effect = build(cls, frames=RATE * 2, source=src)
        left = pull_left(effect, RATE * 2)
        peaks = arrivals(left, threshold=400)
        self.assertGreaterEqual(len(peaks), 2, peaks[:6])
        dry, wet = peaks[0], peaks[1]
        after = left[wet[0] + 64:]
        limit = 10.0 ** (-48.0 / 20.0) * wet[1]
        later = int(np.max(np.abs(after.astype(np.int32)))) if len(after) else 0
        return dry, wet, later, limit, peaks

    def test_one_wet_arrival_at_defaults(self):
        dry, wet, later, limit, peaks = self._wet_peak_and_tail(rebuilt.Chorus)
        self.assertEqual(dry[0], 32)
        self.assertGreater(wet[0] - dry[0], 100)
        self.assertLess(later, limit)
        self.assertEqual(len([p for p in peaks if p[1] >= 400]), 2)

    def test_feedback_plants_a_train(self):
        dry, wet, later, limit, peaks = self._wet_peak_and_tail(
            RegeneratingChorus)
        self.assertGreater(len(peaks), 2, peaks[:8])
        self.assertGreater(later, limit)


class T2Reciprocal(unittest.TestCase):
    def _ratio(self, cls, lfo_hz=4.0):
        frames = int(RATE * 2.5)
        src = sine_src(1000.0, frames, level=6000)
        effect = cls(src, sample_rate=RATE, rate=lfo_hz)
        left = pull_left(effect, frames)
        hz = inst_hz(left.astype(np.float64), RATE)
        return half_ratio(hz, RATE, lfo_hz)

    def test_offset_ramps_inside_a_half(self):
        ratio = self._ratio(WetOnly)
        self.assertGreater(ratio, 1.25 * 0.8)
        self.assertLess(abs(ratio - 4.31) / 4.31, 0.60)
        self.assertGreater(ratio, 1.56)

    def test_linear_triangle_collapses_the_ratio(self):
        clean = self._ratio(WetOnly)
        faulted = self._ratio(WetOnlyLinear)
        self.assertLess(abs(faulted - 1.0), 0.35)
        self.assertGreater(abs(clean - 1.0), abs(faulted - 1.0))


class T3DarkWet(unittest.TestCase):
    def _ratio_at(self, cls, hz, frames=RATE):
        wet = cls(sine_src(hz, frames, level=8000),
                  sample_rate=RATE, delay_ms=8.0, depth=0.0)
        dry = rebuilt.Chorus(sine_src(hz, frames, level=8000),
                             sample_rate=RATE, mix=0.0, delay_ms=8.0,
                             depth=0.0)
        w = pull_left(wet, frames)[RATE // 4:]
        d = pull_left(dry, frames)[RATE // 4:]
        return 20.0 * math.log10(
            (float(np.sqrt(np.mean(w.astype(float) ** 2))) + 1e-12)
            / (float(np.sqrt(np.mean(d.astype(float) ** 2))) + 1e-12))

    def test_ten_khz_is_at_least_ten_db_down(self):
        low = self._ratio_at(WetOnly, 200.0)
        high = self._ratio_at(WetOnly, 10000.0)
        self.assertLess(high - low, -10.0)

    def test_open_tone_is_not_that_dark(self):
        low = self._ratio_at(WetOnlyOpen, 200.0)
        high = self._ratio_at(WetOnlyOpen, 10000.0)
        self.assertGreater(high - low, -6.0)


class T4NearEqual(unittest.TestCase):
    def _energy_ratio(self, cls):
        src = impulse_src(RATE, at=32)
        effect = cls(src, sample_rate=RATE, depth=0.0)
        left = pull_left(effect, RATE)
        peaks = arrivals(left, threshold=200)
        dry, wet = peaks[0], peaks[1]
        dry_e = float(np.sum(np.abs(
            left[max(0, dry[0] - 2):dry[0] + 8].astype(np.int32))))
        wet_e = float(np.sum(np.abs(
            left[wet[0] - 2:wet[0] + 16].astype(np.int32))))
        return wet_e / dry_e

    def test_vintage_mix_near_0_815(self):
        ratio = self._energy_ratio(rebuilt.Chorus)
        self.assertGreater(ratio, 0.61)
        self.assertLess(ratio, 1.09)
        self.assertAlmostEqual(ratio, 0.815, delta=0.12)

    def test_half_mix_misses_the_bar(self):
        ratio = self._energy_ratio(HalfMixChorus)
        self.assertLess(ratio, 0.61)


class T5RateSpan(unittest.TestCase):
    def _lfo_hz(self, cls, rate_hz, sample_rate=RATE, hop=1024):
        seconds = max(2.0, 4.0 / rate_hz)
        times, delay = delay_trajectory(
            cls, rate=sample_rate, lfo_hz=rate_hz, seconds=seconds, hop=hop)
        self.assertGreater(len(delay), 8)
        y = delay - np.mean(delay)
        spec = np.fft.rfft(y)
        dt = times[1] - times[0] if len(times) > 1 else hop / float(sample_rate)
        freqs = np.fft.rfftfreq(len(y), dt)
        spec_abs = np.abs(spec)
        peak = int(np.argmax(spec_abs[1:])) + 1
        return float(freqs[peak])

    def test_rate_stops_span_more_than_ten_to_one(self):
        slow = self._lfo_hz(WetOnly, 0.5)
        fast = self._lfo_hz(WetOnly, 10.0)
        self.assertGreater(slow, 0.25)
        self.assertLess(slow, 0.9)
        self.assertGreater(fast, 6.0)
        self.assertLess(fast, 12.0)
        self.assertGreater(fast / slow, 10.0)

    def test_planted_rate_trips_the_stated_bar_at_defaults(self):
        clean = self._lfo_hz(WetOnly, 0.8)
        faulted = self._lfo_hz(DoubleRateChorus, 0.8)
        self.assertGreater(clean, 0.3)
        self.assertLess(clean, 12.0)
        self.assertGreater(faulted, 12.0)
        self.assertLess(faulted, 20.0)

    def test_planted_rate_trips_the_stated_bar_at_22050(self):
        # hop-1024 Nyquist at 22050 is 10.77 Hz; 16 Hz aliases to ~5.43
        # (inside 0.3–12). hop-512 Nyquist is 21.53 Hz.
        clean = self._lfo_hz(WetOnly, 0.8, sample_rate=22050, hop=512)
        faulted = self._lfo_hz(DoubleRateChorus, 0.8, sample_rate=22050,
                               hop=512)
        self.assertGreater(clean, 0.3)
        self.assertLess(clean, 12.0)
        self.assertGreater(faulted, 12.0)
        self.assertLess(faulted, 20.0)


class T6ClockLaw(unittest.TestCase):
    def _h2(self, cls, lfo_hz=4.0):
        times, delay = delay_trajectory(cls, lfo_hz=lfo_hz, seconds=2.5,
                                        hop=1024)
        dt = times[1] - times[0]
        db, phase = second_harmonic_db(delay, dt, lfo_hz)
        return db, phase

    def test_second_harmonic_near_m_over_two(self):
        db, phase = self._h2(WetOnly)
        self.assertGreater(db, -22.0)
        self.assertLess(db, -8.0)

    def test_sine_wow_drops_the_second_harmonic(self):
        clean, _ = self._h2(WetOnly)
        faulted, _ = self._h2(WetOnlySine)
        self.assertLess(faulted, -20.0)
        self.assertLess(faulted, clean - 6.0)


class Tier1Fast(unittest.TestCase):
    def test_mix_zero_is_a_wire(self):
        frames = 4096
        data = array("h")
        for i in range(frames):
            v = int(8000 * math.sin(2 * math.pi * 440 * i / RATE))
            data.extend((v, v))
        src = probes.ArraySource(data, rate=RATE, channels=2, block=256)
        effect = rebuilt.Chorus(src, sample_rate=RATE, mix=0.0, depth=0.0)
        left = pull_left(effect, frames)
        orig = np.array(data[0::2], dtype=np.int16)
        self.assertTrue(np.array_equal(left, orig[:len(left)]))

    def test_silence_stays_silence(self):
        effect = build(frames=RATE)
        left = pull_left(effect, RATE)
        self.assertEqual(int(np.max(np.abs(left.astype(np.int32)))), 0)

    def test_deinit_leaves_the_source(self):
        frames = 512
        src = sine_src(440.0, frames)
        effect = rebuilt.Chorus(src, sample_rate=RATE)
        pull_left(effect, 64)
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(src)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)

    def test_click_delay_is_zero(self):
        effect = rebuilt.Chorus(
            impulse_src(2048, at=10), sample_rate=RATE, mix=0.0, depth=0.0)
        left = pull_left(effect, 2048)
        peak = int(np.argmax(np.abs(left.astype(np.int32))))
        self.assertEqual(peak, 10)
        self.assertEqual(effect.latency_samples, 0)


class FaultsAreUnreachable(unittest.TestCase):
    def _reach(self, faulted, reading):
        return kit_faults.fault_reachability(
            rebuilt.Chorus, faulted, reading,
            lambda cls: cls(silence_src(512), sample_rate=RATE))

    def test_t1_fault_is_not_a_macro_or_patch(self):
        result = self._reach(
            RegeneratingChorus,
            lambda effect: getattr(effect, "_plant_feedback", 0.0))
        self.assertAlmostEqual(result["target"], 0.3)
        self.assertEqual(result["checked"], 92)

    def test_t2_through_t6_faults_are_not_on_the_surface(self):
        for faulted, reading, expected in (
                (LinearTriangleChorus,
                 lambda e: getattr(e, "_plant_linear_triangle", False), True),
                (OpenToneChorus,
                 lambda e: getattr(e, "_plant_open_tone", False), True),
                (HalfMixChorus,
                 lambda e: getattr(e, "_plant_half_mix", False), True),
                (DoubleRateChorus,
                 lambda e: getattr(e, "_planted_wow_hz", 0.0), 16.0),
                (SineWowChorus,
                 lambda e: getattr(e, "_plant_sine_wow", False), True)):
            result = self._reach(faulted, reading)
            self.assertEqual(result["target"], expected)
            self.assertEqual(result["checked"], 92)


class NullBuildRed(unittest.TestCase):
    """Demonstrated rows must go red on the class built as a wire."""

    def test_t1_t4_t5_t6_null_build_is_red(self):
        def t1(cls):
            try:
                dry, wet, later, limit, peaks = T1OneVoice()._wet_peak_and_tail(
                    cls)
            except AssertionError:
                return {"passed": False}
            n = len([p for p in peaks if p[1] >= 400])
            return {"passed": n == 2 and later < limit}

        def t4(cls):
            try:
                ratio = T4NearEqual()._energy_ratio(cls)
            except (AssertionError, IndexError, ValueError):
                return {"passed": False}
            return {"passed": 0.61 < ratio < 1.09}

        def t5(cls):
            times, delay = delay_trajectory(cls, lfo_hz=0.8, seconds=5.0,
                                            hop=1024)
            if len(delay) < 8 or float(np.std(delay)) < 0.5:
                return {"passed": False}
            hz = T5RateSpan()._lfo_hz(cls, 0.8)
            return {"passed": 0.3 <= hz <= 12.0}

        def t6(cls):
            times, delay = delay_trajectory(cls, lfo_hz=4.0, seconds=2.5,
                                            hop=1024)
            if len(delay) < 8 or float(np.std(delay)) < 0.5:
                return {"passed": False}
            dt = times[1] - times[0]
            db, _phase = second_harmonic_db(delay, dt, 4.0)
            return {"passed": abs(db - (-14.9)) <= 6.0}

        for name, measure in (("T1", t1), ("T4", t4), ("T5", t5), ("T6", t6)):
            result = kit_faults.null_build_red(
                rebuilt.Chorus, measure, label="Chorus %s" % name)
            self.assertFalse(result["null"]["passed"], name)
            self.assertTrue(result["control"]["passed"], name)
