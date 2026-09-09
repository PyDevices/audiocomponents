"""`Vibrato`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Vibrato.md`; Tier 2
rows are T1–T7. Each row here is the measurement and the same measurement
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
from audioeffects import vibrato as rebuilt                 # noqa: E402
import kit_probes as probes                                 # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
RATE_I, DEPTH_I, RISE_I, ENGAGE_I, DELAY_I, TONE_I, BODY_I, LEVEL_I = range(8)


class DryWetVibrato(rebuilt.Vibrato):
    """T1: mix=1 sums dry+wet. Mix is not a macro."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_mix = 1.0
        self._delay.set(mix=1.0)


class WrongLatencyVibrato(rebuilt.Vibrato):
    """T2: delay_ms moved without updating latency_samples."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_latency = True
        mean_ms = self._value(DELAY_I)
        self._delay.set(delay_ms=mean_ms + 2.0)


class HalfRateVibrato(rebuilt.Vibrato):
    """T3: wow_hz stuck at 1 Hz. Half of the default 5 Hz is still
    inside 1.8–16 Hz; 1 Hz is outside that window at the constructor
    default and at every Rate stop.
    """

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_half_rate = True
        self._delay.set(wow_hz=1.0)


class TriangleVibrato(rebuilt.Vibrato):
    """T4: delay linear in a triangle LFO."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_triangle = True
        tri = array("h", [
            int(round(rebuilt._unit_triangle(i) * 32767.0))
            for i in range(rebuilt.SHAPE_LEN)])
        self._shape = tri
        mean_ms = self._value(DELAY_I)
        m = rebuilt.m_for_cents(mean_ms, self._value(RATE_I),
                                self._value(DEPTH_I))
        self._delay.set(
            delay_ms=mean_ms,
            wow_depth_ms=mean_ms * m,
            wow_shape=self._shape)


def _unit_triangle_local(index, length=256):
    phase = index / float(length)
    if phase < 0.25:
        return 4.0 * phase
    if phase < 0.75:
        return 2.0 - 4.0 * phase
    return 4.0 * phase - 4.0


rebuilt._unit_triangle = _unit_triangle_local


class StepEngageVibrato(rebuilt.Vibrato):
    """T5: depth applied as a step, Rise ignored."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_step = True

    def _on_block(self):
        self._plant_step = True
        self._envelope = 1.0 if self._engaged() else 0.0
        self._write_wow()


class OpenBodyVibrato(rebuilt.Vibrato):
    """T6 low corner: high-pass removed. Body's floor is 20 Hz, not 0."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_open_body = True
        self._delay.set(cut_hz=0.0)


class HalfSampleVibrato(rebuilt.Vibrato):
    """T6 high corner: Delay offset by half a sample after the snap."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_half_sample = True
        mean_ms, _frames = self._mean_delay_ms()
        m = rebuilt.m_for_cents(mean_ms, self._value(RATE_I),
                                self._value(DEPTH_I))
        delay_ms, wow_depth_ms = rebuilt.delay_law(mean_ms, m)
        extra = 500.0 / float(self._sample_rate)
        self._delay.set(delay_ms=delay_ms + extra,
                        wow_depth_ms=wow_depth_ms * self._envelope)


class SineWowVibrato(rebuilt.Vibrato):
    """T7: additive sine on the delay (`wow_shape=None`)."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_sine_wow = True
        self._delay.set(wow_shape=None)


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
    cls = cls or rebuilt.Vibrato
    if source is None:
        source = silence_src(frames, channels=channels, rate=rate)
    return cls(source, sample_rate=rate, **options)


def rms(x):
    x = np.asarray(x, dtype=np.float64)
    return math.sqrt(float(np.mean(x * x))) + 1e-12


def delay_trajectory(cls, rate=RATE, lfo_hz=5.0, seconds=2.5, hop=256, **kw):
    hop = max(int(hop), 256)
    frames = int(rate * seconds)
    data = array("h", [0] * (frames * 2))
    for n in range(0, frames, hop):
        data[n * 2] = 32000
        data[n * 2 + 1] = 32000
    src = probes.ArraySource(data, rate=rate, channels=2, block=256)
    effect = cls(src, sample_rate=rate, rate=lfo_hz, **kw)
    left = pull_left(effect, frames)
    delays = []
    times = []
    for n in range(0, frames - hop, hop):
        window = left[n:n + hop]
        mag = np.abs(window.astype(np.int32)).astype(np.float64)
        mag[:8] = 0
        peak_at = int(np.argmax(mag))
        if mag[peak_at] < 200:
            continue
        lo = max(8, peak_at - 4)
        hi = min(len(mag), peak_at + 5)
        weight = float(np.sum(mag[lo:hi]))
        centre = (float(np.dot(np.arange(lo, hi), mag[lo:hi]))
                  / (weight + 1e-12))
        delays.append(centre)
        times.append(n / float(rate))
    return np.array(times), np.array(delays, dtype=np.float64)


def harmonic_db(samples, sample_dt, lfo_hz, order):
    x = np.asarray(samples, dtype=np.float64) - np.mean(samples)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), sample_dt)
    f1 = np.argmin(np.abs(freqs - lfo_hz))
    fk = np.argmin(np.abs(freqs - order * lfo_hz))
    a1 = abs(spec[f1]) + 1e-12
    ak = abs(spec[fk])
    phase = np.angle(spec[fk]) - order * np.angle(spec[f1])
    return 20.0 * math.log10(ak / a1), phase


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


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = rebuilt.Vibrato
        self.assertEqual(cls.MACRO_LABELS,
                         ("Rate", "Depth", "Rise", "Engage", "Delay", "Tone",
                          "Body", "Level"))
        self.assertEqual(len(cls.PATCHES), 7)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.TIER, _component.AUDIOIF)
        self.assertEqual(cls.REQUIRES, ("audioecho",))
        effect = build()
        self.assertEqual(effect.latency_samples, 192)
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(0, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)

    def test_adopted_vibrato_is_the_rebuild(self):
        import audioeffects
        self.assertIs(audioeffects.Vibrato, rebuilt.Vibrato)
        self.assertTrue(issubclass(audioeffects.Vibrato,
                                   audioeffects._component.Component))

    def test_patch_0_is_the_constructor_grid(self):
        effect = build()
        grid = rebuilt.Vibrato.PATCHES[0][1]
        for index, expected in enumerate(grid):
            self.assertAlmostEqual(effect.get_macro(index), expected, delta=0.6)

    def test_default_output_is_the_delay_not_the_mixer(self):
        effect = build()
        self.assertIsNot(effect.output, effect._mixer)
        effect.set_macro(LEVEL_I, 127)
        self.assertIs(effect.output, effect._mixer)
        effect.set_macro(LEVEL_I, rebuilt.Vibrato.PATCHES[0][1][LEVEL_I])
        self.assertIsNot(effect.output, effect._mixer)


class T1NoDry(unittest.TestCase):
    def _ptp(self, cls, depth=0.0):
        levels = []
        for hz in (200.0, 250.0, 300.0, 500.0, 750.0, 1000.0, 1500.0, 2000.0):
            src = sine_src(hz, RATE, level=6000)
            effect = cls(src, sample_rate=RATE, depth=depth)
            y = pull_left(effect, RATE)[RATE // 8:]
            levels.append(20.0 * math.log10(rms(y)))
        return max(levels) - min(levels)

    def test_no_comb_at_default_depths(self):
        for depth in (0.0, 30.0, 60.0):
            ptp = self._ptp(rebuilt.Vibrato, depth)
            self.assertLess(ptp, 1.0, "depth %s ptp %s" % (depth, ptp))

    def test_mix_one_plants_a_comb(self):
        clean = self._ptp(rebuilt.Vibrato, 0.0)
        faulted = self._ptp(DryWetVibrato, 0.0)
        self.assertGreater(faulted, 1.0)
        self.assertGreater(faulted, clean + 1.0)

    def _impulse_peaks(self, cls):
        src = impulse_src(4096, at=32)
        effect = cls(src, sample_rate=RATE, depth=0.0)
        left = pull_left(effect, 4096)
        mag = np.abs(left.astype(np.int32))
        peaks = []
        index = 0
        while index < len(mag):
            if mag[index] > 1000:
                peaks.append(index)
                index += 8
            else:
                index += 1
        lat = effect.latency_samples
        delayed = any(abs(peak - (32 + lat)) <= 2 for peak in peaks)
        dry = any(abs(peak - 32) <= 2 for peak in peaks)
        return peaks, delayed, dry, lat

    def test_default_is_one_delayed_peak(self):
        peaks, delayed, dry, lat = self._impulse_peaks(rebuilt.Vibrato)
        self.assertEqual(lat, 192)
        self.assertTrue(delayed)
        self.assertFalse(dry)
        self.assertEqual(len(peaks), 1)

    def test_dry_wet_has_two_peaks(self):
        peaks, delayed, dry, _lat = self._impulse_peaks(DryWetVibrato)
        self.assertTrue(delayed)
        self.assertTrue(dry)
        self.assertGreaterEqual(len(peaks), 2)


class T2MeanDelay(unittest.TestCase):
    def _arrival(self, cls, rate):
        src = impulse_src(4096, at=200, rate=rate)
        effect = cls(src, sample_rate=rate, depth=0.0)
        left = pull_left(effect, 4096)
        peak = int(np.argmax(np.abs(left.astype(np.int32))))
        return peak - 200, effect.latency_samples

    def test_reported_matches_click_at_48k(self):
        measured, reported = self._arrival(rebuilt.Vibrato, RATE)
        self.assertEqual(reported, 192)
        self.assertLessEqual(abs(measured - reported), 1)

    def test_wrong_latency_misses(self):
        measured, reported = self._arrival(WrongLatencyVibrato, RATE)
        self.assertEqual(reported, 192)
        self.assertGreater(abs(measured - reported), 1)


class T3RateSpan(unittest.TestCase):
    def _lfo_hz(self, cls, rate_hz):
        seconds = max(3.0, 6.0 / rate_hz)
        times, delay = delay_trajectory(cls, lfo_hz=rate_hz, seconds=seconds,
                                        hop=512)
        self.assertGreater(len(delay), 8)
        y = delay - np.mean(delay)
        spec = np.fft.rfft(y)
        dt = times[1] - times[0]
        freqs = np.fft.rfftfreq(len(y), dt)
        peak = int(np.argmax(np.abs(spec)[1:])) + 1
        return float(freqs[peak])

    def test_rate_stops_span_at_least_six_to_one(self):
        slow = self._lfo_hz(rebuilt.Vibrato, 2.0)
        fast = self._lfo_hz(rebuilt.Vibrato, 15.0)
        self.assertGreater(slow, 1.8)
        self.assertLess(slow, 2.3)
        self.assertGreater(fast, 13.0)
        self.assertLess(fast, 16.0)
        self.assertGreater(fast / slow, 6.0)

    def test_half_rate_moves_the_fundamental(self):
        clean = self._lfo_hz(rebuilt.Vibrato, 5.0)
        faulted = self._lfo_hz(HalfRateVibrato, 5.0)
        self.assertGreater(clean, 1.8)
        self.assertLess(clean, 16.0)
        self.assertTrue(faulted < 1.8 or faulted > 16.0, faulted)


class T4SmoothLfo(unittest.TestCase):
    def _h3(self, cls):
        times, delay = delay_trajectory(cls, lfo_hz=5.0, seconds=2.5, hop=256)
        dt = times[1] - times[0]
        db, _ = harmonic_db(delay, dt, 5.0, 3)
        return db

    def test_third_harmonic_at_published_defaults(self):
        db = self._h3(rebuilt.Vibrato)
        self.assertLess(db, -25.0)

    def test_triangle_raises_the_third(self):
        clean = self._h3(rebuilt.Vibrato)
        faulted = self._h3(TriangleVibrato)
        self.assertGreater(faulted, -22.0)
        self.assertGreater(faulted, clean + 6.0)


class T5Ramp(unittest.TestCase):
    def _env_times(self, cls, rise=0.15):
        frames = int(RATE * 1.2)
        src = sine_src(1000.0, frames, level=8234)
        effect = cls(src, sample_rate=RATE, engage=False, rise=rise,
                     depth=30.0)
        pull_left(effect, int(RATE * 0.2))
        effect.set_macro(ENGAGE_I, 127)
        dt = 128.0 / RATE
        stamps = []
        elapsed = 0.0
        while elapsed < rise * 2.5 + 0.1:
            audiocore.get_buffer(effect.output)
            stamps.append((elapsed, float(effect._envelope)))
            elapsed += dt
            if stamps[-1][1] >= 0.999:
                break
        return stamps, effect

    def _ten_ninety(self, stamps):
        peak = max(v for _, v in stamps) + 1e-12
        t10 = next(t for t, v in stamps if v >= 0.1 * peak)
        t90 = next(t for t, v in stamps if v >= 0.9 * peak)
        return t90 - t10

    def test_one_fifty_ms_rise_at_defaults(self):
        stamps, effect = self._env_times(rebuilt.Vibrato, 0.15)
        seconds = self._ten_ninety(stamps)
        self.assertGreater(seconds, 0.15 * 0.8)
        self.assertLess(seconds, 0.15 * 1.2)
        left = pull_left(effect, int(RATE * 0.3)).astype(np.float64)
        hop = int(RATE * 0.01)
        dbs = []
        for i in range(0, len(left) - hop, hop):
            dbs.append(20.0 * math.log10(rms(left[i:i + hop])))
        steps = np.abs(np.diff(np.array(dbs)))
        self.assertLess(float(np.max(steps)), 0.5)

    def test_step_engage_is_faster_than_the_rise(self):
        clean, _ = self._env_times(rebuilt.Vibrato, 0.15)
        faulted, _ = self._env_times(StepEngageVibrato, 0.15)
        self.assertGreater(self._ten_ninety(clean), 0.10)
        self.assertLess(self._ten_ninety(faulted), 0.02)


class T6Band(unittest.TestCase):
    def _db_vs_1k(self, cls, hz):
        src = sine_src(hz, RATE, level=8000)
        effect = cls(src, sample_rate=RATE, depth=0.0)
        y = pull_left(effect, RATE)[RATE // 4:]
        ref_src = sine_src(1000.0, RATE, level=8000)
        ref = cls(ref_src, sample_rate=RATE, depth=0.0)
        r = pull_left(ref, RATE)[RATE // 4:]
        return 20.0 * math.log10(rms(y) / rms(r))

    def test_corners_at_48k_whole_sample_delay(self):
        low = self._db_vs_1k(rebuilt.Vibrato, 40.0)
        high = self._db_vs_1k(rebuilt.Vibrato, 17000.0)
        self.assertAlmostEqual(low, -3.0, delta=1.5)
        self.assertAlmostEqual(high, -3.0, delta=1.5)

    def test_open_body_loses_the_low_corner(self):
        clean = self._db_vs_1k(rebuilt.Vibrato, 40.0)
        faulted = self._db_vs_1k(OpenBodyVibrato, 40.0)
        self.assertLess(clean, -1.5)
        self.assertGreater(faulted, -1.0)

    def test_program_change_zero_keeps_the_high_corner(self):
        src = sine_src(17000.0, RATE, level=8000)
        effect = rebuilt.Vibrato(src, sample_rate=RATE)
        effect.program_change(0)
        effect.set_macro(DEPTH_I, 0)
        y = pull_left(effect, RATE)[RATE // 4:]
        ref_src = sine_src(1000.0, RATE, level=8000)
        ref = rebuilt.Vibrato(ref_src, sample_rate=RATE)
        ref.program_change(0)
        ref.set_macro(DEPTH_I, 0)
        r = pull_left(ref, RATE)[RATE // 4:]
        db = 20.0 * math.log10(rms(y) / rms(r))
        self.assertEqual(effect.latency_samples, 192)
        self.assertAlmostEqual(db, -3.0, delta=1.5)

    def test_half_sample_loses_the_high_corner(self):
        clean = self._db_vs_1k(rebuilt.Vibrato, 17000.0)
        faulted = self._db_vs_1k(HalfSampleVibrato, 17000.0)
        self.assertGreater(clean, -4.5)
        self.assertLess(faulted, clean - 3.0)


class T7ClockLaw(unittest.TestCase):
    def _h2(self, cls, lfo_hz=5.0):
        times, delay = delay_trajectory(cls, lfo_hz=lfo_hz, seconds=2.5,
                                        hop=256)
        dt = times[1] - times[0]
        return harmonic_db(delay, dt, lfo_hz, 2)

    def test_second_harmonic_near_m_over_two(self):
        db, _phase = self._h2(rebuilt.Vibrato)
        # m ≈ 0.134 at constructor defaults → m/2 = −23.5 dB. The seed's
        # "quadrature" invariant is φ2−2φ1; the closed form 1/(1+m sin)
        # itself has that relative phase at 0 (wrapped), not ±π/2 — T7 is
        # the magnitude against m/2.
        self.assertGreater(db, -29.5)
        self.assertLess(db, -17.5)

    def test_sine_wow_drops_the_second_harmonic(self):
        clean, _ = self._h2(rebuilt.Vibrato)
        faulted, _ = self._h2(SineWowVibrato)
        self.assertLess(faulted, -30.0)
        self.assertLess(faulted, clean - 6.0)


class Tier1Fast(unittest.TestCase):
    def test_depth_zero_is_a_pure_delay(self):
        frames = 4096
        src = impulse_src(frames, at=10)
        effect = rebuilt.Vibrato(src, sample_rate=RATE, depth=0.0)
        left = pull_left(effect, frames)
        peak = int(np.argmax(np.abs(left.astype(np.int32))))
        self.assertEqual(peak, 10 + effect.latency_samples)
        self.assertEqual(effect.latency_samples, 192)

    def test_silence_stays_silence(self):
        effect = build(frames=RATE)
        left = pull_left(effect, RATE)
        self.assertEqual(int(np.max(np.abs(left.astype(np.int32)))), 0)


class FaultsAreUnreachable(unittest.TestCase):
    def _reach(self, faulted, reading):
        return kit_faults.fault_reachability(
            rebuilt.Vibrato, faulted, reading,
            lambda cls: cls(silence_src(512), sample_rate=RATE))

    def test_all_faults_are_not_a_macro_or_patch(self):
        for faulted, reading, expected in (
                (DryWetVibrato,
                 lambda e: getattr(e, "_plant_mix", 0.0), 1.0),
                (WrongLatencyVibrato,
                 lambda e: getattr(e, "_plant_latency", False), True),
                (HalfRateVibrato,
                 lambda e: getattr(e, "_plant_half_rate", False), True),
                (TriangleVibrato,
                 lambda e: getattr(e, "_plant_triangle", False), True),
                (StepEngageVibrato,
                 lambda e: getattr(e, "_plant_step", False), True),
                (OpenBodyVibrato,
                 lambda e: getattr(e, "_plant_open_body", False), True),
                (HalfSampleVibrato,
                 lambda e: getattr(e, "_plant_half_sample", False), True),
                (SineWowVibrato,
                 lambda e: getattr(e, "_plant_sine_wow", False), True)):
            result = self._reach(faulted, reading)
            self.assertEqual(result["target"], expected)
            self.assertEqual(result["checked"], 143)


class _Flag:
    def __init__(self, passed, detail=None):
        self.passed = bool(passed)
        self.detail = detail

    def __bool__(self):
        return self.passed


class NullBuildsAtDefault(unittest.TestCase):
    """kit_faults.null_build_red at constructor defaults. A wire-green
    measurement is unmeasured, never demonstrated.
    """

    def test_t1_delayed_peak_is_red_on_a_wire(self):
        def measure(cls):
            src = impulse_src(4096, at=32)
            effect = cls(src, sample_rate=RATE, depth=0.0)
            left = pull_left(effect, 4096)
            mag = np.abs(left.astype(np.int32))
            peaks = [i for i in range(len(mag)) if mag[i] > 1000]
            clustered = []
            for peak in peaks:
                if not clustered or peak - clustered[-1] > 8:
                    clustered.append(peak)
            lat = effect.latency_samples
            delayed = any(abs(peak - (32 + lat)) <= 2 for peak in clustered)
            dry = any(abs(peak - 32) <= 2 for peak in clustered)
            return _Flag(delayed and (not dry) and len(clustered) == 1,
                         (clustered, lat))

        result = kit_faults.null_build_red(rebuilt.Vibrato, measure,
                                           label="T1")
        self.assertFalse(bool(result["null"]))
        self.assertTrue(bool(result["control"]))

    def test_t2_click_is_red_on_a_wire(self):
        def measure(cls):
            src = impulse_src(4096, at=200)
            effect = cls(src, sample_rate=RATE, depth=0.0)
            left = pull_left(effect, 4096)
            peak = int(np.argmax(np.abs(left.astype(np.int32))))
            return _Flag(abs((peak - 200) - effect.latency_samples) <= 1)

        result = kit_faults.null_build_red(rebuilt.Vibrato, measure,
                                           label="T2")
        self.assertFalse(bool(result["null"]))
        self.assertTrue(bool(result["control"]))

    def test_t3_rate_is_red_on_a_wire(self):
        def measure(cls):
            times, delay = delay_trajectory(cls, lfo_hz=5.0, seconds=2.5,
                                            hop=512)
            if len(delay) < 8:
                return _Flag(False, "short")
            y = delay - np.mean(delay)
            if float(np.max(np.abs(y))) < 0.25:
                return _Flag(False, "flat")
            spec = np.fft.rfft(y)
            dt = times[1] - times[0]
            freqs = np.fft.rfftfreq(len(y), dt)
            peak = int(np.argmax(np.abs(spec)[1:])) + 1
            hz = float(freqs[peak])
            return _Flag(1.8 < hz < 16.0, hz)

        result = kit_faults.null_build_red(rebuilt.Vibrato, measure,
                                           label="T3")
        self.assertFalse(bool(result["null"]))
        self.assertTrue(bool(result["control"]))

    def test_t4_h3_is_red_on_a_wire(self):
        def measure(cls):
            times, delay = delay_trajectory(cls, lfo_hz=5.0, seconds=2.5,
                                            hop=256)
            if len(delay) < 8 or float(np.max(np.abs(
                    delay - np.mean(delay)))) < 0.25:
                return _Flag(False, "flat")
            dt = times[1] - times[0]
            db, _ = harmonic_db(delay, dt, 5.0, 3)
            return _Flag(db < -25.0, db)

        result = kit_faults.null_build_red(rebuilt.Vibrato, measure,
                                           label="T4")
        self.assertFalse(bool(result["null"]))
        self.assertTrue(bool(result["control"]))

    def test_t6_body_is_red_on_a_wire(self):
        def measure(cls):
            src = sine_src(40.0, RATE, level=8000)
            effect = cls(src, sample_rate=RATE, depth=0.0)
            y = pull_left(effect, RATE)[RATE // 4:]
            ref_src = sine_src(1000.0, RATE, level=8000)
            ref = cls(ref_src, sample_rate=RATE, depth=0.0)
            r = pull_left(ref, RATE)[RATE // 4:]
            db = 20.0 * math.log10(rms(y) / rms(r))
            return _Flag(db < -1.5, db)

        result = kit_faults.null_build_red(rebuilt.Vibrato, measure,
                                           label="T6")
        self.assertFalse(bool(result["null"]))
        self.assertTrue(bool(result["control"]))

    def test_t5_audio_rise_is_red_on_a_wire(self):
        def measure(cls):
            frames = int(RATE * 0.8)
            src = sine_src(1000.0, frames, level=8234)
            effect = cls(src, sample_rate=RATE, engage=False, rise=0.15,
                         depth=30.0)
            pull_left(effect, int(RATE * 0.05))
            # Do not set_macro: that re-routes a wire_build back onto the
            # delay. Flip the Engage cell the envelope already reads.
            effect._macros[ENGAGE_I] = 1.0
            dt = 128.0 / RATE
            stamps = []
            elapsed = 0.0
            chunks = []
            while elapsed < 0.4:
                data = pull_left(effect, 128)
                chunks.append(data)
                stamps.append((elapsed, float(effect._envelope)))
                elapsed += dt
                if stamps[-1][1] >= 0.999:
                    break
            if not stamps:
                return _Flag(False, "no stamps")
            peak = max(v for _, v in stamps) + 1e-12
            crossed = [t for t, v in stamps if v >= 0.1 * peak]
            crossed90 = [t for t, v in stamps if v >= 0.9 * peak]
            if not crossed or not crossed90:
                return _Flag(False, (peak, len(stamps)))
            t10, t90 = crossed[0], crossed90[0]
            return _Flag(0.12 < (t90 - t10) < 0.18, t90 - t10)

        result = kit_faults.null_build_red(rebuilt.Vibrato, measure,
                                           label="T5")
        self.assertFalse(bool(result["null"]))
        self.assertTrue(bool(result["control"]))

    def test_t7_h2_is_red_on_a_wire(self):
        def measure(cls):
            times, delay = delay_trajectory(cls, lfo_hz=5.0, seconds=2.5,
                                            hop=256)
            if len(delay) < 8 or float(np.max(np.abs(
                    delay - np.mean(delay)))) < 0.25:
                return _Flag(False, "flat")
            dt = times[1] - times[0]
            db, _ = harmonic_db(delay, dt, 5.0, 2)
            return _Flag(-29.5 < db < -17.5, db)

        result = kit_faults.null_build_red(rebuilt.Vibrato, measure,
                                           label="T7")
        self.assertFalse(bool(result["null"]))
        self.assertTrue(bool(result["control"]))
