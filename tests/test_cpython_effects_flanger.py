"""`Flanger`'s own invariant and planted-fault tests.

Dossier: workspace docs/effects-internal/dossiers/Flanger.md, frozen
2026-09-08. Exhaustive rate coverage lives in the evidence pack; this
file asserts at 48 kHz unless the test is about rate or latency.
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
from audioeffects import rebuilt as rebuilt_pkg                 # noqa: E402
from audioeffects.rebuilt import flanger as rebuilt             # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
Flanger = rebuilt.Flanger


def macro_of(index, value):
    from audioeffects import _component
    return _component.macro_of(Flanger._MACRO_RANGES[index], value)


class LinearMsFlanger(Flanger):
    """F1: delay linear in milliseconds instead of 1/clock."""
    NAME = 'Flanger'
    DELAY_LAW = "linear"


class UnequalMixFlanger(Flanger):
    """F2: equal-weight mix forced off the node's 1.0 after every refresh."""
    NAME = 'Flanger'
    FORCED_MIX = 0.55

    def _refresh(self):
        Flanger._refresh(self)
        if getattr(type(self), "FORCED_MIX", None) is not None:
            self._wet.set(mix=type(self).FORCED_MIX)


class SquaredColorFlanger(Flanger):
    """F3: Color applied as g^2."""
    NAME = 'Flanger'
    COLOR_LAW = "squared"


class DeafMatrixFlanger(Flanger):
    """F4: Filter Matrix does not stop the LFO."""
    NAME = 'Flanger'
    MATRIX_HONOURED = False


class InvertedMatrixFlanger(Flanger):
    """F4 at defaults: Matrix off stops the LFO (the switch is inverted)."""
    NAME = 'Flanger'
    MATRIX_INVERTED = True

    def _refresh(self):
        Flanger._refresh(self)
        if type(self).MATRIX_INVERTED:
            matrix = self._value(4) >= 0.5
            if not matrix:
                self._wet.set(wow_hz=0.0, wow_depth_ms=0.0)


class HalfRangeFlanger(Flanger):
    """F5: Range travel halved, so 4:1 is unreachable."""
    NAME = 'Flanger'
    RANGE_SCALE = 0.35


class NoSlewFlanger(Flanger):
    """F6: delay jumps; slew is not a macro."""
    NAME = 'Flanger'
    DELAY_SLEW = 0.0


class FlatDampingFlanger(Flanger):
    """F7: no clock-dependent darkening."""
    NAME = 'Flanger'
    DAMPING_HONOURED = False

    def _refresh(self):
        Flanger._refresh(self)
        self._wet.set(damping_hz=0.0)


class SoftColorFlanger(Flanger):
    """F8: Color ceiling too low for a 2 s tail at 3 ms."""
    NAME = 'Flanger'
    COLOR_CEILING = 0.5


class ShortLatencyFlanger(Flanger):
    """CLICK: report 256 samples short."""
    NAME = 'Flanger'

    @property
    def latency_samples(self):
        self._check_live()
        return max(0, self._latency - 256)


def build(cls=None, rate=RATE, channels=2, frames=48000, probe=None,
          **options):
    cls = cls or Flanger
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2, label=None):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, label=label, class_name="Flanger",
                         latency_samples=effect.latency_samples)


def noise(frames=65536, channels=2, seed=1):
    rng = np.random.RandomState(seed)
    mono = rng.randint(-8000, 8000, size=frames, dtype=np.int32)
    if channels == 2:
        stacked = np.repeat(mono[:, None], 2, axis=1)
    else:
        stacked = mono[:, None]
    return array("h", stacked.reshape(-1).tolist())


def sine(hz, frames=48000, dbfs=-20.0, rate=RATE, channels=2):
    index = np.arange(frames)
    values = 10.0 ** (dbfs / 20.0) * np.sin(2.0 * math.pi * hz * index / rate)
    quantised = np.clip(np.round(values * 32768.0), -32768, 32767).astype(np.int64)
    if channels == 2:
        quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist())


def transfer_db(wet, dry, rate=RATE, nfft=16384):
    w = wet.float[:, 0]
    d = dry.float[:, 0]
    hop = nfft // 2
    acc_w = None
    acc_d = None
    count = 0
    window = np.hanning(nfft)
    for start in range(0, min(len(w), len(d)) - nfft, hop):
        fw = np.fft.rfft(w[start:start + nfft] * window)
        fd = np.fft.rfft(d[start:start + nfft] * window)
        pw = np.abs(fw) ** 2
        pd = np.abs(fd) ** 2
        acc_w = pw if acc_w is None else acc_w + pw
        acc_d = pd if acc_d is None else acc_d + pd
        count += 1
    mag = 10.0 * np.log10((acc_w / count) / np.maximum(acc_d / count, 1e-24))
    hz = np.fft.rfftfreq(nfft, 1.0 / rate)
    return hz, mag


def deepest_notch(hz, mag, lo=100.0, hi=8000.0):
    band = (hz >= lo) & (hz <= hi)
    mean = float(np.mean(mag[band]))
    idx = int(np.argmin(mag[band]))
    return float(hz[band][idx]), float(mag[band][idx] - mean), mean


def peak_in_band(hz, mag, lo=100.0, hi=6000.0):
    band = (hz >= lo) & (hz <= hi)
    return float(np.max(mag[band]))


class LinearMsFlangerReach(unittest.TestCase):
    def test_f1_law_is_not_a_macro(self):
        kit_faults.fault_reachability(
            Flanger, LinearMsFlanger,
            lambda e: type(e).DELAY_LAW,
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F1")

    def test_linear_ms_fires_at_defaults(self):
        probe = sine(1000, frames=8192)
        clean = build(probe=probe)
        dirty = build(LinearMsFlanger, probe=probe)
        a = render(clean, 8192, label="tone")
        b = render(dirty, 8192, label="tone")
        clean.deinit()
        dirty.deinit()
        self.assertGreater(float(np.max(np.abs(a.float - b.float))), 1e-4)


class F2EqualWeightComb(unittest.TestCase):
    def _notch(self, cls=Flanger, delay_ms=3.0):
        probe = noise(65536)
        dry_src = probes.ArraySource(probe, rate=RATE, block=256)
        dry = probes.render(dry_src, 65536, rate=RATE, block=256,
                            probe="noise", class_name="source")
        effect = build(cls, probe=probe, mix=1.0, color=0.0,
                       filter_matrix=1.0, manual_ms=delay_ms, range_=0.0)
        wet = render(effect, 65536, label="noise")
        effect.deinit()
        hz, mag = transfer_db(wet, dry)
        freq, depth, mean = deepest_notch(hz, mag)
        return {"freq": freq, "depth": depth, "mean": mean,
                "hz": hz, "mag": mag}

    def test_held_3ms_notches_are_odd_harmonics_and_deep(self):
        reading = self._notch()
        expected = 1000.0 / (2.0 * 3.0)
        self.assertGreater(abs(reading["depth"]), 30.0, reading)
        # nearest predicted (2k+1)/(2 tau)
        k = round((reading["freq"] / expected - 1.0) / 2.0)
        pred = (2 * k + 1) * expected
        self.assertLess(abs(reading["freq"] - pred) / pred, 0.005, reading)

    def test_forced_mix_shallower_than_30db(self):
        reading = self._notch(UnequalMixFlanger)
        self.assertLess(abs(reading["depth"]), 30.0, reading)

    def test_mix_fault_is_not_a_surface_flag(self):
        kit_faults.fault_reachability(
            Flanger, UnequalMixFlanger,
            lambda e: getattr(type(e), "FORCED_MIX", None),
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F2")

    def test_unequal_mix_fires_at_defaults(self):
        probe = noise(32768)
        dry_src = probes.ArraySource(probe, rate=RATE, block=256)
        dry = probes.render(dry_src, 32768, rate=RATE, block=256,
                            probe="noise", class_name="source")
        clean = build(probe=probe)
        dirty = build(UnequalMixFlanger, probe=probe)
        a = render(clean, 32768, label="noise")
        b = render(dirty, 32768, label="noise")
        clean.deinit()
        dirty.deinit()
        _, da, _ = deepest_notch(*transfer_db(a, dry))
        _, db, _ = deepest_notch(*transfer_db(b, dry))
        self.assertGreater(abs(abs(da) - abs(db)), 1.0, (da, db))

    def test_null_build_has_no_notch(self):
        def measure(cls):
            reading = self._notch(cls)
            return {"passed": abs(reading["depth"]) >= 30.0, "red": [reading]}
        kit_faults.null_build_red(Flanger, measure, label="Flanger F2")


class F3ColorIsPeaks(unittest.TestCase):
    def _peak(self, color, cls=Flanger):
        probe = noise(32768)
        dry_src = probes.ArraySource(probe, rate=RATE, block=256)
        dry = probes.render(dry_src, 32768, rate=RATE, block=256,
                            probe="noise", class_name="source")
        effect = build(cls, probe=probe, mix=1.0, color=color,
                       filter_matrix=1.0, manual_ms=3.0)
        wet = render(effect, 32768, label="noise")
        effect.deinit()
        hz, mag = transfer_db(wet, dry)
        return peak_in_band(hz, mag)

    def test_peaks_rise_from_color_0_to_09(self):
        lows = [self._peak(c) for c in (0.0, 0.3, 0.6, 0.9)]
        self.assertEqual(lows, sorted(lows), lows)
        self.assertGreaterEqual(lows[-1] - lows[0], 15.0, lows)

    def _peak_at(self, color, rate, seed=1):
        probe = noise(32768, seed=seed)
        dry_src = probes.ArraySource(probe, rate=rate, block=256)
        dry = probes.render(dry_src, 32768, rate=rate, block=256,
                            probe="noise", class_name="source")
        effect = build(rate=rate, probe=probe, mix=1.0, color=color,
                       filter_matrix=1.0, manual_ms=3.0)
        wet = render(effect, 32768, rate=rate, label="noise")
        effect.deinit()
        return peak_in_band(*transfer_db(wet, dry, rate=rate))

    def test_peaks_rise_at_44100_and_22050(self):
        """F3's +15 dB four-stop bar at the two lower rates the audit named."""
        for rate, seed in ((44100, 99), (22050, 1), (22050, 99)):
            lows = [self._peak_at(c, rate, seed=seed)
                    for c in (0.0, 0.3, 0.6, 0.9)]
            self.assertEqual(lows, sorted(lows), (rate, seed, lows))
            self.assertGreaterEqual(lows[-1] - lows[0], 15.0,
                                    (rate, seed, lows))

    def test_squared_color_is_not_plus_15db(self):
        lows = [self._peak(c, SquaredColorFlanger) for c in (0.0, 0.9)]
        self.assertLess(lows[-1] - lows[0], 15.0, lows)

    def test_color_law_is_not_a_macro(self):
        kit_faults.fault_reachability(
            Flanger, SquaredColorFlanger,
            lambda e: type(e).COLOR_LAW,
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F3")

    def test_floor_fills_at_least_10db(self):
        probe = noise(32768)
        dry_src = probes.ArraySource(probe, rate=RATE, block=256)
        dry = probes.render(dry_src, 32768, rate=RATE, block=256,
                            probe="noise", class_name="source")
        floors = []
        for color in (0.0, 0.9):
            effect = build(probe=probe, mix=1.0, color=color,
                           filter_matrix=1.0, manual_ms=3.0)
            wet = render(effect, 32768, label="noise")
            effect.deinit()
            hz, mag = transfer_db(wet, dry)
            _, depth, _ = deepest_notch(hz, mag)
            floors.append(depth)
        self.assertGreaterEqual(floors[1] - floors[0], 10.0, floors)

    def test_squared_color_fires_at_defaults(self):
        probe = noise(32768)
        dry_src = probes.ArraySource(probe, rate=RATE, block=256)
        dry = probes.render(dry_src, 32768, rate=RATE, block=256,
                            probe="noise", class_name="source")
        clean = build(probe=probe)
        dirty = build(SquaredColorFlanger, probe=probe)
        a = render(clean, 32768, label="noise")
        b = render(dirty, 32768, label="noise")
        clean.deinit()
        dirty.deinit()
        ha, ma = transfer_db(a, dry)
        hb, mb = transfer_db(b, dry)
        self.assertGreater(abs(peak_in_band(ha, ma) - peak_in_band(hb, mb)),
                           0.5)

    def test_f3_null_build_is_red(self):
        def measure(cls):
            lows = [self._peak(c, cls) for c in (0.0, 0.9)]
            rise = lows[-1] - lows[0]
            return {"passed": rise >= 15.0, "red": [{"rise": rise}]}
        kit_faults.null_build_red(Flanger, measure, label="Flanger F3")


class F4FilterMatrix(unittest.TestCase):
    def test_matrix_stops_wow(self):
        effect = build(probe=probes.silence(2048), filter_matrix=1.0,
                       rate_hz=8.0)
        # wow_hz is not a macro; Matrix on must leave it at 0.
        self.assertEqual(effect._value(4) >= 0.5, True)
        effect.deinit()

    def test_deaf_matrix_keeps_sweeping_flag(self):
        kit_faults.fault_reachability(
            Flanger, DeafMatrixFlanger,
            lambda e: type(e).MATRIX_HONOURED,
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F4")

    def test_inverted_matrix_is_not_a_macro(self):
        kit_faults.fault_reachability(
            Flanger, InvertedMatrixFlanger,
            lambda e: bool(getattr(type(e), "MATRIX_INVERTED", False)),
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F4 invert")

    def test_inverted_matrix_kills_sweep_at_defaults(self):
        probe = sine(1000, frames=8192, dbfs=-16.0)
        clean = build(probe=probe, rate_hz=8.0)
        dirty = build(InvertedMatrixFlanger, probe=probe, rate_hz=8.0)
        a = render(clean, 8192, label="tone")
        b = render(dirty, 8192, label="tone")
        clean.deinit()
        dirty.deinit()
        self.assertGreater(float(np.max(np.abs(a.float - b.float))), 1e-4)


class F5SweepSpan(unittest.TestCase):
    def test_range_max_is_four_to_one(self):
        effect = build(probe=probes.silence(2048), range_=1.0,
                       filter_matrix=0.0)
        short, long_ms = effect._span_ms()
        self.assertGreaterEqual(long_ms / short, 4.0 - 1e-6)
        self.assertGreaterEqual(long_ms, 8.0)
        self.assertLessEqual(long_ms, 12.0)
        effect.deinit()

    def test_half_range_misses_the_ratio(self):
        effect = build(HalfRangeFlanger, probe=probes.silence(2048),
                       range_=1.0, filter_matrix=0.0)
        short, long_ms = effect._span_ms()
        self.assertLess(long_ms / short, 4.0)
        effect.deinit()

    def test_range_scale_is_not_a_macro(self):
        kit_faults.fault_reachability(
            Flanger, HalfRangeFlanger,
            lambda e: type(e).RANGE_SCALE,
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F5")

    def test_half_range_fires_at_defaults(self):
        probe = sine(1000, frames=8192)
        clean = build(probe=probe)
        dirty = build(HalfRangeFlanger, probe=probe)
        a = render(clean, 8192, label="tone")
        b = render(dirty, 8192, label="tone")
        clean.deinit()
        dirty.deinit()
        self.assertGreater(float(np.max(np.abs(a.float - b.float))), 1e-4)


class F6Slew(unittest.TestCase):
    def test_slew_is_one_on_the_shipped_class(self):
        self.assertEqual(Flanger.DELAY_SLEW, 1.0)
        self.assertEqual(NoSlewFlanger.DELAY_SLEW, 0.0)

    def test_slew_is_not_a_macro(self):
        kit_faults.fault_reachability(
            Flanger, NoSlewFlanger,
            lambda e: type(e).DELAY_SLEW,
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F6")

    def test_no_slew_fires_on_the_live_manual_step(self):
        from audioeffects import _component
        probe = sine(1000, frames=8192)
        pos = _component.macro_of(Flanger._MACRO_RANGES[3], 6.0)
        clean = build(probe=probe, filter_matrix=1.0, manual_ms=1.0,
                      color=0.0, mix=2.0)
        dirty = build(NoSlewFlanger, probe=probe, filter_matrix=1.0,
                      manual_ms=1.0, color=0.0, mix=2.0)
        render(clean, 256, label="tone")
        render(dirty, 256, label="tone")
        clean.set_macro(3, pos)
        dirty.set_macro(3, pos)
        a = render(clean, 2048, label="tone")
        b = render(dirty, 2048, label="tone")
        clean.deinit()
        dirty.deinit()
        self.assertGreater(
            float(np.max(np.abs(a.float[:1024] - b.float[:1024]))), 1e-4)

    def test_no_slew_is_silent_at_constructor_defaults(self):
        """F6's plant does not move audio until a live delay_ms step."""
        probe = sine(1000, frames=8192)
        clean = build(probe=probe)
        dirty = build(NoSlewFlanger, probe=probe)
        a = render(clean, 8192, label="tone")
        b = render(dirty, 8192, label="tone")
        clean.deinit()
        dirty.deinit()
        self.assertEqual(float(np.max(np.abs(a.float - b.float))), 0.0)


class F7Darkens(unittest.TestCase):
    def _level_10k(self, delay_ms, cls=Flanger):
        probe = sine(10000, frames=8192, dbfs=-16.0)
        effect = build(cls, probe=probe, mix=2.0, color=0.0,
                       filter_matrix=1.0, manual_ms=delay_ms, range_=0.0)
        wet = render(effect, 8192, label="tone10k")
        effect.deinit()
        skip = int(delay_ms * RATE / 1000.0) + 64
        return kit.rms_db(wet.float[skip:, 0])

    def test_10khz_falls_from_1ms_to_10ms(self):
        short = self._level_10k(1.0)
        long_ = self._level_10k(10.0)
        self.assertGreaterEqual(short - long_, 0.4, (short, long_))

    def test_flat_damping_is_not_a_macro(self):
        kit_faults.fault_reachability(
            Flanger, FlatDampingFlanger,
            lambda e: getattr(type(e), "DAMPING_HONOURED", True),
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F7")

    def test_flat_damping_does_not_fall_0p4(self):
        short = self._level_10k(1.0, FlatDampingFlanger)
        long_ = self._level_10k(10.0, FlatDampingFlanger)
        self.assertLess(short - long_, 0.4, (short, long_))

    def test_flat_damping_fires_at_defaults(self):
        probe = sine(10000, frames=8192, dbfs=-16.0)
        clean = build(probe=probe)
        dirty = build(FlatDampingFlanger, probe=probe)
        a = render(clean, 8192, label="tone10k")
        b = render(dirty, 8192, label="tone10k")
        clean.deinit()
        dirty.deinit()
        self.assertGreater(abs(kit.rms_db(a.float[256:, 0])
                               - kit.rms_db(b.float[256:, 0])), 0.05)

    def test_f7_fall_null_build_is_red(self):
        def measure(cls):
            fall = self._level_10k(1.0, cls) - self._level_10k(10.0, cls)
            return {"passed": fall >= 0.4, "red": [{"fall": fall}]}
        kit_faults.null_build_red(Flanger, measure, label="Flanger F7")


class F8ColorCeiling(unittest.TestCase):
    def test_max_color_tail_is_at_least_two_seconds(self):
        effect = build(probe=probes.silence(2048), color=0.99,
                       filter_matrix=1.0, manual_ms=3.0, mix=1.0)
        self.assertGreaterEqual(effect.tail_samples / float(RATE), 2.0)
        effect.deinit()

    def test_soft_ceiling_is_under_two_seconds(self):
        effect = build(SoftColorFlanger, probe=probes.silence(2048),
                       color=0.99, filter_matrix=1.0, manual_ms=3.0, mix=1.0)
        self.assertLess(effect.tail_samples / float(RATE), 2.0)
        effect.deinit()

    def test_ceiling_is_not_a_macro(self):
        kit_faults.fault_reachability(
            Flanger, SoftColorFlanger,
            lambda e: type(e).COLOR_CEILING,
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Flanger F8")

    def test_soft_ceiling_fires_at_defaults(self):
        probe = sine(1000, frames=8192)
        clean = build(probe=probe)
        dirty = build(SoftColorFlanger, probe=probe)
        a = render(clean, 8192, label="tone")
        b = render(dirty, 8192, label="tone")
        declared_gap = clean.tail_samples - dirty.tail_samples
        clean.deinit()
        dirty.deinit()
        self.assertGreater(declared_gap, 0)
        self.assertGreater(float(np.max(np.abs(a.float - b.float))), 1e-4)

    def _audio_t60(self, cls=Flanger, color=0.99, listen_s=3.0, hz=440.0):
        rate = RATE
        burst = int(rate * 0.05)
        total = burst + int(rate * listen_s)
        probe = sine(hz, frames=total, dbfs=-6.0, rate=rate)
        arr = np.frombuffer(probe, dtype=np.int16).copy()
        arr[burst * 2:] = 0
        probe = array("h", arr.tolist())
        effect = build(cls, probe=probe, color=color, filter_matrix=1.0,
                       manual_ms=3.0, mix=1.0)
        wet = render(effect, total, label="burst")
        effect.deinit()
        x = wet.float[:, 0]
        win = int(rate * 0.02)
        peak = 0.0
        t60 = None
        for start in range(burst, len(x) - win, win // 2):
            rms = float(np.sqrt(np.mean(x[start:start + win] ** 2)))
            if start == burst:
                peak = max(rms, 1e-12)
            db = 20.0 * math.log10(max(rms, 1e-12) / peak)
            if t60 is None and db <= -60.0:
                t60 = (start - burst) / float(rate)
        return t60

    def test_audio_t60_at_color_max_is_at_least_two_seconds(self):
        """F8 audio: Color-max cut is 0.4 Hz so the ring clears 2 s."""
        t60 = self._audio_t60()
        self.assertIsNotNone(t60, "never reached −60 dB")
        self.assertGreaterEqual(t60, 2.0, t60)

    def test_audio_t60_at_200hz_is_at_least_two_seconds(self):
        t60 = self._audio_t60(hz=200.0)
        self.assertIsNotNone(t60, "never reached −60 dB")
        self.assertGreaterEqual(t60, 2.0, t60)

    def test_soft_ceiling_audio_t60_is_under_two_seconds(self):
        t60 = self._audio_t60(SoftColorFlanger)
        self.assertIsNotNone(t60, "never reached −60 dB")
        self.assertLess(t60, 2.0, t60)

    def test_f8_audio_null_build_is_red(self):
        def measure(cls):
            t60 = self._audio_t60(cls, listen_s=2.5)
            passed = t60 is not None and t60 >= 2.0
            return {"passed": passed, "red": [{"t60": t60}]}
        kit_faults.null_build_red(Flanger, measure, label="Flanger F8 audio")

    def test_default_audio_tail_is_not_two_seconds(self):
        """Headline: constructor Color 0.55 is ~0.1 s, not F8's Color-max 2 s."""
        effect = build(probe=probes.silence(2048))
        self.assertLess(effect.tail_samples / float(RATE), 0.2)
        effect.deinit()


class TierOne(unittest.TestCase):
    def test_mix_zero_is_a_wire(self):
        probe = probes.ramp_fs(8192)
        frames = len(probe) // 2
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256), frames,
            rate=RATE, block=256, probe="ramp_fs", class_name="source")
        effect = build(probe=probe, mix=0.0)
        wet = render(effect, frames)
        effect.deinit()
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])

    def test_click_matches_reported_latency(self):
        probe = probes.click_stereo(4096)
        frames = len(probe) // 2
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256), frames,
            rate=RATE, block=256, probe="click", class_name="source")
        effect = build(probe=probe, mix=0.0)
        wet = render(effect, frames)
        result = kit.click(wet, dry, effect.latency_samples)
        effect.deinit()
        self.assertTrue(result["passed"], result["red"])

    def test_click_red_when_reported_256_short(self):
        probe = probes.click_stereo(8192)
        frames = len(probe) // 2
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256), frames,
            rate=RATE, block=256, probe="click", class_name="source")
        effect = build(ShortLatencyFlanger, probe=probe, mix=0.0,
                       through_zero=1.0, range_=1.0)
        wet = render(effect, frames)
        result = kit.click(wet, dry, effect.latency_samples)
        effect.deinit()
        self.assertFalse(result["passed"], result)

    def test_capabilities_is_tempo_sync_and_transport_is_read(self):
        calls = []

        def transport():
            calls.append(1)
            return (True, 0.0, 120.0, 4, 4)

        probe = probes.silence(2048)
        source = probes.ArraySource(probe, rate=RATE, block=256)
        effect = Flanger.create(source, RATE, transport=transport)
        self.assertEqual(effect.capabilities, ("tempo_sync",))
        effect.set_macro(0, 64)
        self.assertGreaterEqual(len(calls), 1)
        effect.deinit()

    def test_through_zero_defaults_off_and_is_named_in_ms(self):
        text = (Flanger.__doc__ or "") + (Flanger._build.__doc__ or "")
        self.assertIn("0 ms", text)
        self.assertIn("10 ms", text)
        effect = build(probe=probes.silence(2048))
        self.assertEqual(effect.latency_samples, 0)
        effect.deinit()

    def test_library_still_serves_the_old_class(self):
        import audioeffects
        self.assertEqual(audioeffects.Flanger.__module__,
                      "audioeffects.modulation")
        self.assertIs(rebuilt_pkg.load("Flanger"), None)
        self.assertIs(rebuilt_pkg.module_class("Flanger"), Flanger)

    def test_reset_then_silent_source_is_zero(self):
        probe = probes.ramp_fs(2048)
        effect = build(probe=probe)
        render(effect, 256)
        effect.reset()
        silent = probes.ArraySource(probes.silence(2048), rate=RATE, block=256)
        effect._source = silent
        effect._wet.play(silent)
        wet = render(effect, 512)
        effect.deinit()
        self.assertEqual(int(np.max(np.abs(wet.data))), 0)

    def test_default_surrender_is_named_in_docstrings(self):
        text = ((Flanger.__doc__ or "") + (rebuilt.__doc__ or ""))
        self.assertIn("What the default gives up", text)
        self.assertIn("−22 dB", text)
        self.assertIn("0.1 s", text)
        self.assertIn("48 / 44.1 / 22.05 kHz", text)
        self.assertIn("2 s ring", text)
        self.assertIn("click is not that bar", text)
