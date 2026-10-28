"""`Vibrato`'s own invariant and planted-fault tests.

The dossier's Tier 2
rows are T1–T7. Each row here is the measurement and the same measurement
shown red on a fault of the same kind. Exhaustive rates live in the evidence
pack, not in this file.
"""

import math
import os
import re
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

    def _rise_ramp_ms(self):
        return 0.0


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
                        wow_depth_ms=wow_depth_ms if self._engaged() else 0.0)


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
        self.assertEqual(cls.TIER, _component.AUDIODSP)
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
        # Asked of the port this test could not fail - a port is never the
        # mixer, so both `assertIsNot`s would pass on any build at all. It
        # asks what the port is PLAYING.
        effect = build()
        playing = _component.port_target
        self.assertIsNot(playing(effect.output), effect._mixer)
        effect.set_macro(LEVEL_I, 0)
        self.assertIs(playing(effect.output), effect._mixer)
        effect.set_macro(LEVEL_I, rebuilt.Vibrato.PATCHES[0][1][LEVEL_I])
        self.assertIsNot(playing(effect.output), effect._mixer)


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


#: What the wet path's two poles add to a landing: they carry the ramp's
#: difference in their state for a little after the depth has arrived.
RING_S = 0.03


def engage_landing(cls, rise, engage=None):
    """Seconds from an Engage move to the frame from which the moved
    instance renders exactly what one built engaged renders: the end of the
    envelope, plus the few ms the Tone and Body poles take to forget the
    difference (RING_S). `engage(effect)` makes the move (`set_macro` by
    default)."""
    lead = int(RATE * 0.2)
    frames = lead + int(RATE * (rise / rebuilt.RISE_10_90 + 0.3))
    # The tone outlasts the render, so neither instance runs out of input.
    tone = frames + RATE
    moved = cls(sine_src(1000.0, tone, level=8234), sample_rate=RATE,
                engage=False, rise=rise, depth=30.0)
    held = cls(sine_src(1000.0, tone, level=8234), sample_rate=RATE,
               engage=True, rise=rise, depth=30.0)
    a = list(pull_left(moved, lead))
    b = list(pull_left(held, lead))
    if engage is None:
        moved.set_macro(ENGAGE_I, 127)
    else:
        engage(moved)
    a.extend(pull_left(moved, frames - lead))
    b.extend(pull_left(held, frames - lead))
    differ = [i for i in range(lead, min(len(a), len(b))) if a[i] != b[i]]
    landing = (differ[-1] + 1 - lead) / float(RATE) if differ else 0.0
    return landing, np.array(a[lead:], dtype=np.float64)


class T5Ramp(unittest.TestCase):
    """Engage ramps the depth in a straight line whose 10-90 % is Rise, so
    the whole ramp is Rise / 0.8, and lands exactly on the engaged depth."""

    def test_one_fifty_ms_rise_at_defaults(self):
        landing, left = engage_landing(rebuilt.Vibrato, 0.15)
        whole = 0.15 / rebuilt.RISE_10_90
        self.assertGreater(landing, whole * 0.9)
        self.assertLess(landing, whole + RING_S)
        # No zipper: the level moves smoothly through the ramp and after.
        hop = int(RATE * 0.01)
        dbs = []
        for i in range(0, len(left) - hop, hop):
            dbs.append(20.0 * math.log10(rms(left[i:i + hop])))
        steps = np.abs(np.diff(np.array(dbs)))
        self.assertLess(float(np.max(steps)), 0.5)

    def test_a_long_rise_lands_on_time(self):
        landing, _left = engage_landing(rebuilt.Vibrato, 1.0)
        self.assertGreater(landing, 1.25 * 0.9)
        self.assertLess(landing, 1.25 + RING_S)

    def test_step_engage_is_faster_than_the_rise(self):
        clean, _ = engage_landing(rebuilt.Vibrato, 0.15)
        faulted, _ = engage_landing(StepEngageVibrato, 0.15)
        self.assertGreater(clean, 0.15)
        self.assertLess(faulted, 0.1)


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


class JumpingVibrato(rebuilt.Vibrato):
    """The moves as they were: the mean line lands at once and Depth 0
    writes a silent clock law."""

    NAME = 'Vibrato'

    def _refresh(self):
        rebuilt.Vibrato._refresh(self)
        self._plant_jump = True
        m = rebuilt.m_for_cents(self._mean_delay_ms()[0], self._value(RATE_I),
                                self._value(DEPTH_I))
        self._shape = rebuilt.clock_shape(m)
        self._delay.set(delay_slew=0.0, wow_shape=self._shape)


class MovesGlide(unittest.TestCase):
    """A Rate, Depth or Delay move glides the read head, so the output
    steps no more than the music does (the lifecycle matrix's P5): a
    triangle whose own largest step is 100 LSB, moved part-way through."""

    MOVES = ((DEPTH_I, 0), (DEPTH_I, 127), (RATE_I, 0), (RATE_I, 127),
             (DELAY_I, 0), (DELAY_I, 127))

    def _step(self, cls, macro, value):
        import lifecycle
        tri = lifecycle.triangle(8192, 2, RATE)
        outs = []
        for moved in (False, True):
            effect = cls.create(probes.ArraySource(tri, rate=RATE,
                                                   channels=2), RATE)
            out = bytearray()
            for block in range(24):
                if moved and block == 12:
                    effect.set_macro(macro, value)
                out += bytes(audiocore.get_buffer(effect.output)[1])
            effect.deinit()
            outs.append(array("h", bytes(out)))
        lo, hi = 12 * 256, 13 * 256
        control = lifecycle._max_step(outs[0], 2, lo, hi)
        return lifecycle._max_step(outs[1], 2, lo, hi), control

    def test_each_move_is_smooth(self):
        for macro, value in self.MOVES:
            got, control = self._step(rebuilt.Vibrato, macro, value)
            self.assertLessEqual(got, 1.5 * max(100, control),
                                 (macro, value, got, control))

    def test_jumping_moves_step(self):
        steps = [self._step(JumpingVibrato, macro, value)
                 for macro, value in self.MOVES]
        self.assertTrue(any(got > 1.5 * max(100, control)
                            for got, control in steps), steps)


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
        def engage(effect):
            # Do not set_macro: that re-routes a wire_build back onto the
            # delay. Flip the Engage cell and write the depth it asks for.
            effect._macros[ENGAGE_I] = 1.0
            effect._write_wow()

        def measure(cls):
            landing, _left = engage_landing(cls, 0.15, engage)
            whole = 0.15 / rebuilt.RISE_10_90
            return _Flag(whole * 0.9 < landing < whole + RING_S, landing)

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


class OldTail(rebuilt.Vibrato):
    """The bound before audiocomponents#114: the longest delay plus 64
    frames, leaving out the ring of the wet path's two filters."""

    NAME = 'Vibrato'

    @property
    def tail_samples(self):
        self._check_live()
        rate = self._sample_rate
        body = self._hz(self._value(6))
        damping = rebuilt.nominal_damping_hz(self._hz(self._value(5)), rate)
        return (rebuilt.Vibrato.tail_samples.fget(self)
                - rebuilt.one_pole_ring(damping, rate)
                - rebuilt.one_pole_ring(body, rate))


class TheResetRestartsTheLfo(unittest.TestCase):
    """Lifecycle E1 P4 compares a reset instance with one that never met
    the reset. A reset is a fresh instance exactly (PR), LFO phase
    included, so the sweep that follows is a fresh one's and never meets
    the uninterrupted control's again: P4 is declared at E1, and PR holds
    the reset itself."""

    def test_e1_is_declared_and_the_reset_is_fresh(self):
        import lifecycle
        lines = []
        lifecycle.run_class(rebuilt.Vibrato, rates=(RATE,), channels=(2,),
                            patches=[None], only=["E1"], emit=lines.append)
        cells = [line for line in lines if "|E1-" in line]
        self.assertEqual(len(cells), 2, lines)
        for line in cells:
            self.assertNotIn("RED", line)
            self.assertIn("P4:decl", line)
        self.assertIn("PR:ok", cells[0])


class TheFiltersRingIsInTheTail(unittest.TestCase):
    """Body's high-pass and Tone's low-pass ring after the line has emptied,
    longest at Body's 20 Hz stop (audiocomponents#114): the output reaches
    exact zero inside the bound at every Body stop, and a bound without the
    filters is red at the low ones."""

    def test_the_ring_ends_inside_the_bound(self):
        import tail_ring
        for rate in (48000, 22050):
            for channels in (2, 1):
                for body in (0, 64, 127):
                    for tone in (0, 127):
                        got, bound = tail_ring.ring(
                            "Vibrato", rate, channels,
                            start=((6, body), (5, tone)))
                        self.assertLessEqual(
                            got, bound, (rate, channels, body, tone))

    def test_a_bound_without_the_filters_is_red(self):
        import tail_ring
        for rate in (48000, 22050):
            got, bound = tail_ring.ring("Vibrato", rate, 2,
                                        start=((6, 0),), cls=OldTail)
            self.assertGreater(got, bound, rate)


class TheGraphPullsWithoutGetBuffer(unittest.TestCase):
    """Vibrato's own re-blocking sources pull the graph the way the
    twin's nodes do, not through the script-facing `audiocore.get_buffer`
    that CircuitPython's board builds compile out: with it hidden, every
    patch renders the bytes it renders with it, through a reset."""

    def test_every_patch_renders_the_same(self):
        import kit_nogb
        scenarios = dict(kit_nogb.SCENARIOS)
        for patch in [None] + sorted(rebuilt.Vibrato.PATCHES):
            for label in ("reset-once", "reset-first"):
                with self.subTest(patch=patch, scenario=label):
                    self.assertEqual(kit_nogb._bytes_cell(
                        rebuilt.Vibrato, {}, RATE, 2, patch,
                        scenarios[label]), "ok")


class TheClaims(unittest.TestCase):
    """The class docstring's figures that the rows above do not reach."""

    def _gain_db(self, **options):
        effect = rebuilt.Vibrato(sine_src(1000.0, RATE, level=8000),
                                 sample_rate=RATE, depth=0.0, **options)
        out = pull_left(effect, RATE)[RATE // 4:]
        return 20.0 * math.log10(rms(out) / (8000 / math.sqrt(2.0)))

    def test_depth_holds_its_cents_across_rate_and_delay(self):
        for delay_ms in (1.0, 4.0, 12.0):
            for rate_hz in (2.0, 5.0, 15.0):
                m = rebuilt.m_for_cents(delay_ms, rate_hz, 60.0)
                self.assertAlmostEqual(
                    rebuilt.peak_cents(delay_ms, rate_hz, m), 60.0, delta=0.5)
        for rate_hz in (2.0, 15.0):
            effect = rebuilt.Vibrato(sine_src(1000.0, RATE * 2, level=8000),
                                     sample_rate=RATE, rate=rate_hz,
                                     depth=30.0, rise=0.15)
            out = pull_left(effect, RATE * 2)[RATE // 2:]
            cents = 1200.0 * np.log2(inst_hz(out, RATE)[2000:-2000] / 1000.0)
            self.assertAlmostEqual(float(np.percentile(cents, 99.5)), 30.0,
                                   delta=3.0)

    def test_level_cuts_up_to_12_db_and_tops_out_at_unity(self):
        self.assertAlmostEqual(self._gain_db(level_db=-12.0), -12.0,
                               delta=0.2)
        self.assertAlmostEqual(self._gain_db(level_db=0.0), 0.0, delta=0.2)
        # audiocomponents#216: the whole knob is audible, so its top is 0 dB.
        effect = build()
        effect.set_macro(LEVEL_I, 127)
        self.assertAlmostEqual(effect._value(7), 0.0, places=6)
        effect.set_macro(LEVEL_I, 0)
        self.assertAlmostEqual(effect._value(7), -12.0, places=6)

    def test_latency_at_44_1_khz(self):
        effect = rebuilt.Vibrato(silence_src(256, rate=44100),
                                 sample_rate=44100)
        self.assertEqual(effect.latency_samples, 176)

    def test_construction_needs_audioecho(self):
        saved = sys.modules["audioecho"]
        sys.modules["audioecho"] = None
        try:
            with self.assertRaises(ImportError):
                build(frames=256)
        finally:
            sys.modules["audioecho"] = saved


CLAIMS = (
    ("A vibrato after the Boss VB-2: your signal comes out only through a "
     "short bucket-brigade line whose clock a sine sweeps, so the pitch "
     "wobbles and none of the dry is left to comb against it.",
     ("T1NoDry.test_default_is_one_delayed_peak",
      "T7ClockLaw.test_second_harmonic_near_m_over_two")),
    ("Depth is the peak pitch swing, and stays that size wherever "
     "Rate and Delay sit.",
     ("TheClaims.test_depth_holds_its_cents_across_rate_and_delay",)),
    ("Engage turns the vibrato on and off without switching the "
     "audio: Rise is how long the depth takes to go from 10 % to 90 "
     "% of the way, in a straight line.",
     ("T5Ramp.test_one_fifty_ms_rise_at_defaults",
      "T5Ramp.test_a_long_rise_lands_on_time")),
    ("Any other knob that moves the depth glides there over 20 ms "
     "rather than stepping.",
     ("MovesGlide.test_each_move_is_smooth",)),
    ("Tone is the wet voice's low-pass, and Body its high-pass; at "
     "the defaults the band is 3 dB down at 40 Hz and at 17 kHz.",
     ("T6Band.test_corners_at_48k_whole_sample_delay",)),
    ("Level cuts the output by up to 12 dB; at the top of its travel the "
     "output is at the input's level.",
     ("TheClaims.test_level_cuts_up_to_12_db_and_tops_out_at_unity",)),
    ("With no dry path there is no comb: from 200 Hz to 2 kHz the level "
     "stays within 1 dB at any Depth up to 60 cents.",
     ("T1NoDry.test_no_comb_at_default_depths",)),
    ("At the default patch the sweep is a smooth sine, its third harmonic "
     "more than 25 dB down.",
     ("T4SmoothLfo.test_third_harmonic_at_published_defaults",)),
    ("Latency is the Delay, snapped to a whole sample: 4 ms by default, "
     "which is 192 samples at 48 kHz and 176 at 44.1 kHz.",
     ("T2MeanDelay.test_reported_matches_click_at_48k",
      "TheClaims.test_latency_at_44_1_khz")),
    ("Nothing looks ahead.",
     ("Tier1Fast.test_depth_zero_is_a_pure_delay",)),
)


def _flat(text):
    return " ".join(text.split())


def claim_problems(doc, claims=CLAIMS):
    """What is wrong between a docstring and `claims`: a sentence missing, a
    named test that does not exist, a figure outside every claim."""
    doc = _flat(doc)
    problems = []
    rest = doc
    for sentence, tests in claims:
        if sentence not in doc:
            problems.append("missing: %s" % sentence)
        rest = rest.replace(sentence, " ")
        for name in tests:
            owner, _, test = name.partition(".")
            if not hasattr(globals().get(owner), test):
                problems.append("no test %s" % name)
    for match in re.finditer(r"\S*\d\S*", rest):
        problems.append("figure outside a claim: %s" % match.group())
    return problems


class Claims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        doc = rebuilt.__doc__ + " " + rebuilt.Vibrato.__doc__
        self.assertEqual(claim_problems(doc), [])
        # The checker can fail: a figure outside a claim, a claim the
        # docstring does not carry, a test that does not exist.
        self.assertTrue(claim_problems(doc + " It reads 12 ms."))
        self.assertTrue(claim_problems(doc.replace("within 1 dB",
                                                   "within 3 dB")))
        self.assertTrue(claim_problems(
            doc, CLAIMS + (("Latency", ("TheClaims.test_nothing_here",)),)))


#: Not here, because they show only when a knob moves, on a reset or a
#: rejoin, or not at all on a fresh build: `StepEngageVibrato`,
#: `JumpingVibrato`; they change only a reported tail or latency: `OldTail`.
KIT_PLANTS = {
    "DryWetVibrato": DryWetVibrato,
    "WrongLatencyVibrato": WrongLatencyVibrato,
    "HalfRateVibrato": HalfRateVibrato,
    "TriangleVibrato": TriangleVibrato,
    "OpenBodyVibrato": OpenBodyVibrato,
    "HalfSampleVibrato": HalfSampleVibrato,
    "SineWowVibrato": SineWowVibrato,
}
