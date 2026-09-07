"""`Limiter`'s own invariant and planted-fault tests.

The dossier is `docs/effects/Limiter.md`; its Tier 2 rows are L1..L7 and each
one has a test here under its own number. The class gate asks for two things
of every trait, and this file carries both: the measurement, and the *same*
measurement shown red on a fault of the same kind. A green measurement with no
demonstrated red is a measurement that has never been shown able to fail.

The faults are the cheap kind - a subclass, a macro at the wrong end, or the
kit's own faulted read - never a change to a library file.
"""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiodynamics                                            # noqa: E402
import audioeffects                                             # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects.rebuilt import limiter as rebuilt             # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

#: `_component` reads VENDOR off the module a class is defined in, and
#: `NoCatchStage` below is a subclass of a rebuilt class. Without this the
#: planted fault would refuse to construct - a fault that cannot fail.
VENDOR = "PyDevices"

RATE = 48000

CEILING, GAIN, LOOKAHEAD, RELEASE, TRUE_PEAK, KNEE = range(6)


def macro_of(index, value):
    """`value` in the macro's own units, as its 0-127 position."""
    from audioeffects import _component
    return _component.macro_of(
        audioeffects.Limiter._MACRO_RANGES[index], value)


class NoCatchStage(audioeffects.Limiter):
    """L2 and L3's planted fault: the second `Dynamics` removed.

    This is the one-node limiter the dossier's section 4 measured and the
    seed's N-L1 was written about. It is a *whole* fault rather than a
    perturbation because the trait's subject is the composition: the claim is
    that lookahead never creates overshoot, and the thing that makes that true
    is the catch stage. Take it out and the class is the S2 pathology.
    """

    NAME = 'Limiter'

    def _build(self, **options):
        audioeffects.Limiter._build(self, **options)
        self._output = self._shape


def build(cls=None, rate=RATE, channels=2, frames=48000, probe=None,
          **options):
    cls = cls or audioeffects.Limiter
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2, label=None):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, label=label, class_name="Limiter",
                         latency_samples=effect.latency_samples)


def interleave(mono, channels=2):
    from array import array
    quantised = np.clip(np.round(np.asarray(mono) * 32768.0),
                        -32768, 32767).astype(np.int64)
    if channels == 2:
        quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist())


def burst(frames=48000, start=4800, length=48, level=1.0, channels=2):
    values = np.zeros(frames)
    values[start:start + length] = level
    return interleave(values, channels)


def impulse(frames=48000, at=4800, level=1.0, channels=2):
    values = np.zeros(frames)
    values[at] = level
    return interleave(values, channels)


def worst_phase_fs4(frames=48000, sample_peak_db=-0.5, channels=2):
    """S1's own worst case: a tone at exactly f_s/4, phased so every sample
    sits at 1/sqrt(2) of a peak that lands between two of them. `tone_fs4` in
    the kit's probe set is the same shape."""
    index = np.arange(frames)
    amplitude = 10.0 ** (sample_peak_db / 20.0) / math.cos(math.pi / 4.0)
    return interleave(
        amplitude * np.cos(2.0 * math.pi * index / 4.0 + math.pi / 4.0),
        channels)


def sine(hz, frames=48000, dbfs=-0.1, rate=RATE, channels=2):
    index = np.arange(frames)
    return interleave(10.0 ** (dbfs / 20.0)
                      * np.sin(2.0 * math.pi * hz * index / rate), channels)


def peak_dbfs(render_result, skip=0):
    return kit.peak_db(render_result.float[skip:, 0])


def thd_percent(values, rate, fundamental, harmonics=10):
    spectrum = np.abs(np.fft.rfft(np.asarray(values, dtype=np.float64)))
    width = rate / float(len(values))

    def magnitude(hz):
        centre = int(round(hz / width))
        return float(spectrum[max(0, centre - 1):centre + 2].max())

    upper = math.sqrt(sum(magnitude(fundamental * order) ** 2
                          for order in range(2, harmonics + 1)))
    return 100.0 * upper / magnitude(fundamental)


# --------------------------------------------------------------------------
# Tier 2


class L1TruePeak(unittest.TestCase):
    """The ceiling is a true-peak promise: no more than 0.5 dB TP over."""

    def _reading(self, true_peak, rate=RATE):
        effect = build(probe=worst_phase_fs4(rate), rate=rate,
                       ceiling_db=-6.0, release_ms=60.0, true_peak=true_peak)
        result = render(effect, rate, rate=rate, label="tone_fs4")
        trimmed = kit.Render.from_pcm(
            result.pcm[400 * 4:], rate, 2, probe="tone_fs4",
            interpreter="cpython", block=256)
        effect.deinit()
        return kit.truepeak(trimmed, ceiling_dbfs=-6.0, tolerance_db=0.5)

    def test_true_peak_on_holds_the_ceiling_at_both_rates(self):
        for rate in (48000, 44100):
            with self.subTest(rate=rate):
                result = self._reading(True, rate)
                self.assertTrue(result["passed"], result["red"])
                self.assertLessEqual(result["values"]["over_ceiling_db"], 0.5)

    def test_with_it_off_three_decibels_escape(self):
        # Not a failure of the class: it is what a sample-peak ceiling means,
        # and S1's own figure for f_s/4 is 3 dB. It is here so the trait's
        # subject is visible as a difference and not only as a bound.
        result = self._reading(False)
        self.assertFalse(result["passed"])
        self.assertGreater(result["values"]["over_ceiling_db"], 2.5)

    def test_the_faulted_read_certifies_what_the_correct_one_fails(self):
        # The kit's own fault: judge the ceiling on the sample peak. With
        # true peak off the output sits exactly on -6.00 dBFS, so the faulted
        # read calls the ceiling met while 3 dB escapes between the samples.
        effect = build(probe=worst_phase_fs4(), ceiling_db=-6.0,
                       release_ms=60.0, true_peak=False)
        result = render(effect, RATE, label="tone_fs4")
        trimmed = kit.Render.from_pcm(result.pcm[400 * 4:], RATE, 2,
                                      probe="tone_fs4",
                                      interpreter="cpython", block=256)
        effect.deinit()
        correct = kit.truepeak(trimmed, ceiling_dbfs=-6.0, tolerance_db=0.5)
        faulted = kit.truepeak(trimmed, ceiling_dbfs=-6.0, tolerance_db=0.5,
                               read="sample_peak")
        self.assertFalse(correct["passed"], "the correct read must go red")
        self.assertTrue(faulted["passed"], "the faulted read must certify it")


class L2LookaheadNeverOvershoots(unittest.TestCase):
    """Sweeping Lookahead 0 -> maximum, the sample peak stays under the
    ceiling and does not grow with lookahead."""

    CEILING_DB = -12.0

    def _sweep(self, cls, probe_factory):
        peaks = []
        for lookahead in range(0, 11):
            effect = build(cls, probe=probe_factory(),
                           ceiling_db=self.CEILING_DB, release_ms=60.0,
                           lookahead_ms=float(lookahead))
            peaks.append(peak_dbfs(render(effect, 48000)))
            effect.deinit()
        return peaks

    def test_the_peak_stays_under_the_ceiling_and_does_not_grow(self):
        peaks = self._sweep(audioeffects.Limiter, burst)
        for lookahead, value in enumerate(peaks):
            with self.subTest(lookahead_ms=lookahead):
                self.assertLessEqual(value - self.CEILING_DB, 0.1)
        self.assertLessEqual(max(peaks) - peaks[0], 0.1)

    def test_without_the_catch_stage_it_goes_red_both_ways(self):
        peaks = self._sweep(NoCatchStage, burst)
        self.assertGreater(peaks[-1] - self.CEILING_DB, 0.1)
        self.assertGreater(peaks[-1] - peaks[0], 0.1)
        self.assertGreater(peaks[5], peaks[1],
                           "the fault must also show the rising trend, not "
                           "only a bound broken at one end")


class L3ShortPeaksAreCaught(unittest.TestCase):
    """A single-sample impulse is caught at every non-zero lookahead."""

    CEILING_DB = -12.0

    def _peaks(self, cls):
        peaks = {}
        for lookahead in (0.5, 1.0, 2.0, 5.0, 10.0):
            effect = build(cls, probe=impulse(), ceiling_db=self.CEILING_DB,
                           release_ms=60.0, lookahead_ms=lookahead)
            peaks[lookahead] = peak_dbfs(render(effect, 48000))
            effect.deinit()
        return peaks

    def test_every_non_zero_setting(self):
        for lookahead, value in self._peaks(audioeffects.Limiter).items():
            with self.subTest(lookahead_ms=lookahead):
                self.assertLessEqual(value - self.CEILING_DB, 0.1)

    def test_without_the_catch_stage_every_setting_is_red(self):
        peaks = self._peaks(NoCatchStage)
        for lookahead, value in peaks.items():
            with self.subTest(lookahead_ms=lookahead):
                self.assertGreater(value - self.CEILING_DB, 0.0)
        self.assertGreater(peaks[10.0] - self.CEILING_DB, 0.1)


class L4LatencyIsTheLookahead(unittest.TestCase):
    """`latency_samples == floor(lookahead_ms * fs / 1000)`, and the click
    agrees to the sample."""

    def test_reported_matches_the_arithmetic_at_three_rates(self):
        for rate in (48000, 44100, 22050):
            for asked in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 7.3, 10.0):
                with self.subTest(rate=rate, lookahead_ms=asked):
                    effect = build(rate=rate, frames=1024,
                                   lookahead_ms=asked)
                    self.assertEqual(effect.latency_samples,
                                     int(asked * rate / 1000.0))
                    effect.deinit()

    def test_every_patch_reports_what_its_macro_says(self):
        for index in sorted(audioeffects.Limiter.PATCHES):
            for rate in (48000, 44100, 22050):
                with self.subTest(patch=index, rate=rate):
                    effect = build(rate=rate, frames=1024, patch=index)
                    self.assertEqual(
                        effect.latency_samples,
                        int(effect.macro(LOOKAHEAD) * rate / 1000.0))
                    effect.deinit()

    def test_the_click_agrees_with_the_report_to_the_sample(self):
        for rate in (48000, 44100):
            for asked in (0.0, 1.5, 10.0):
                with self.subTest(rate=rate, lookahead_ms=asked):
                    probe = probes.click_stereo(16384, offset=256)
                    dry = probes.render(
                        probes.ArraySource(probe, rate=rate, block=256),
                        16384, rate=rate, block=256, probe="click_stereo",
                        class_name="source")
                    effect = build(probe=probe, rate=rate,
                                   ceiling_db=0.0, lookahead_ms=asked)
                    wet = render(effect, 16384, rate=rate)
                    result = kit.click(wet, dry, effect.latency_samples)
                    effect.deinit()
                    self.assertTrue(result["passed"], result["red"])

    def test_a_report_256_samples_short_is_red(self):
        # The kit's CLICK fault, on this class. The DSP is untouched, so the
        # two renders are byte-identical and only the report moves.
        probe = probes.click_stereo(16384, offset=256)
        dry = probes.render(probes.ArraySource(probe, rate=RATE, block=256),
                            16384, rate=RATE, block=256,
                            probe="click_stereo", class_name="source")
        digests = []
        for short in (0, 256):
            effect = build(probe=probe, ceiling_db=0.0, lookahead_ms=10.0)
            wet = render(effect, 16384)
            digests.append(wet.digest)
            result = kit.click(wet, dry, effect.latency_samples - short)
            effect.deinit()
            self.assertEqual(result["passed"], short == 0, result["red"])
        self.assertEqual(digests[0], digests[1])


class L5ZeroByDefault(unittest.TestCase):
    def test_constructed_with_no_options(self):
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                effect = build(rate=rate, frames=1024)
                self.assertEqual(effect.latency_samples, 0)
                self.assertEqual(effect.tail_samples, 0)
                self.assertEqual(effect.macro(LOOKAHEAD), 0.0)
                self.assertLess(effect.macro(TRUE_PEAK), 0.5)
                self.assertEqual(effect.patch_index, 0)
                effect.deinit()

    def test_patch_zero_is_the_same_place(self):
        effect = build(frames=1024, lookahead_ms=8.0, true_peak=True)
        self.assertGreater(effect.latency_samples, 0)
        effect.program_change(0)
        self.assertEqual(effect.latency_samples, 0)
        self.assertLess(effect.macro(TRUE_PEAK), 0.5)
        effect.deinit()


class L6BrickwallAndKnee(unittest.TestCase):
    """Infinite ratio above the ceiling, and no knee at Knee zero."""

    CEILING_DB = -24.0

    def _curve(self, knee_db, levels, frames=12000):
        outputs = []
        for level_db in levels:
            effect = build(probe=sine(1000.0, frames, dbfs=float(level_db)),
                           ceiling_db=self.CEILING_DB, release_ms=150.0,
                           knee_db=knee_db)
            outputs.append(peak_dbfs(render(effect, frames),
                                     skip=frames // 2))
            effect.deinit()
        return np.array(levels), np.array(outputs)

    def test_the_slope_above_the_ceiling_is_flat_over_24_db(self):
        # 24 dB of input above the ceiling, which is why the ceiling for this
        # row is -24 dBFS: int16 has no headroom above 0 dBFS to put it in.
        levels = list(np.linspace(-24.0, -0.2, 25))
        levels, outputs = self._curve(0.0, levels)
        slope = np.polyfit(levels, outputs, 1)[0]
        self.assertLessEqual(abs(slope), 0.02, "slope %.4f dB/dB" % slope)
        self.assertLessEqual(float(outputs.max()) - self.CEILING_DB, 0.05)

    def test_the_knee_is_hard_at_zero_and_soft_at_maximum(self):
        # Knee width as the dossier defines it: the input span over which the
        # curve's local slope leaves 0.95 dB/dB and reaches the asymptote.
        # The grid is 0.25 dB, so a width of 0.5 dB is three points wide and
        # the bar can actually be failed.
        grid = list(np.arange(-32.0, -15.75, 0.25))

        def width(knee_db):
            levels, outputs = self._curve(knee_db, grid, frames=8000)
            slopes = np.gradient(outputs, levels)
            bending = levels[(slopes < 0.95) & (slopes > 0.05)]
            return 0.0 if not bending.size else float(bending.max()
                                                      - bending.min())

        hard = width(0.0)
        soft = width(12.0)
        self.assertLessEqual(hard, 0.5, "knee width %.3f dB at Knee 0" % hard)
        self.assertGreater(soft, 4.0,
                           "Knee at maximum must actually be a knee (%.3f dB)"
                           " or the hard-knee half of this row passes on a "
                           "macro that does nothing" % soft)


class L7SmoothingIsADocumentedTrade(unittest.TestCase):
    """THD at the default patch, and the fast-release setting named as a
    distortion setting in the docstring."""

    def _thd(self, release_ms=None, rate=RATE):
        options = {"ceiling_db": -12.0}
        if release_ms is not None:
            options["release_ms"] = release_ms
        effect = build(probe=sine(60.0, rate, dbfs=-0.1, rate=rate),
                       rate=rate, **options)
        result = render(effect, rate, rate=rate)
        effect.deinit()
        half = rate // 2
        return thd_percent(result.float[half:, 0], rate, 60.0)

    def test_the_default_patch_is_under_one_percent(self):
        for rate in (48000, 44100):
            with self.subTest(rate=rate):
                self.assertLess(self._thd(rate=rate), 1.0)

    def test_the_fastest_release_is_red_at_the_same_bar(self):
        self.assertGreater(self._thd(release_ms=5.0), 1.0)

    def test_the_docstring_names_the_trade(self):
        text = (audioeffects.Limiter.__doc__ or "")
        self.assertIn("THD", text)
        self.assertIn("distortion", text)

    def test_the_docstring_names_the_lookahead_in_milliseconds(self):
        # The gate's wording: every latency-adding option defaults off or to
        # its shortest and is named in the docstring, in milliseconds.
        text = (audioeffects.Limiter.__doc__ or "") + (
            audioeffects.Limiter._build.__doc__ or "")
        self.assertIn("0 ms", text)
        self.assertIn("10 ms", text)
        self.assertIn("480 samples", text)


# --------------------------------------------------------------------------
# Tier 1


class TierOne(unittest.TestCase):
    def test_the_ceiling_at_zero_is_a_wire(self):
        # This class has no mix, depth or drive control; its defeated setting
        # is the Ceiling at the top of its span with no gain. On the ramp,
        # which carries samples above half scale in every block, the compare
        # is byte for byte.
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                probe = probes.ramp_fs(8192)
                frames = len(probe) // 2
                dry = probes.render(
                    probes.ArraySource(probe, rate=rate, block=256), frames,
                    rate=rate, block=256, probe="ramp_fs",
                    class_name="source")
                effect = build(probe=probe, rate=rate, ceiling_db=0.0)
                wet = render(effect, frames, rate=rate)
                effect.deinit()
                result = kit.wire(wet, dry, latency_samples=0)
                self.assertTrue(result["passed"], result["red"])

    def test_without_the_epsilon_correction_the_wire_is_red(self):
        # The planted fault for the row above, and the reason the correction
        # exists: the node reads `envelope + 1e-6` before the log, so a
        # full-scale sample looks a hair over 0 dBFS and comes back an LSB
        # down. Nothing about the class changes but that constant.
        probe = probes.ramp_fs(8192)
        frames = len(probe) // 2
        dry = probes.render(probes.ArraySource(probe, rate=RATE, block=256),
                            frames, rate=RATE, block=256, probe="ramp_fs",
                            class_name="source")
        original = rebuilt._EPSILON_DB
        try:
            rebuilt._EPSILON_DB = 0.0
            effect = build(probe=probe, ceiling_db=0.0)
            wet = render(effect, frames)
            effect.deinit()
        finally:
            rebuilt._EPSILON_DB = original
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertFalse(result["passed"],
                         "the correction has to be shown to be load-bearing")

    def test_silence_in_silence_out_and_the_tail_reaches_zero(self):
        for lookahead in (0.0, 10.0):
            with self.subTest(lookahead_ms=lookahead):
                probe, burst_end = probes.burst_silence(
                    hz=1000.0, on_ms=200.0, total_s=1.0)
                effect = build(probe=probe, ceiling_db=-6.0,
                               lookahead_ms=lookahead)
                result = render(effect, 48000)
                declared = effect.tail_samples
                effect.deinit()
                measured = kit.tail(result, burst_end_frame=burst_end,
                                    declared_tail_samples=declared)
                self.assertTrue(measured["passed"], measured["red"])
                self.assertEqual(measured["values"]["residual_lsb"], 0)

    def test_level_honest_through_the_dry_path(self):
        # Below the ceiling nothing is touched, at any Ceiling setting.
        for ceiling_db in (0.0, -6.0, -24.0):
            with self.subTest(ceiling_db=ceiling_db):
                probe = probes.sine(1000.0, 0.5, ceiling_db - 6.0)
                frames = len(probe) // 2
                dry = probes.render(
                    probes.ArraySource(probe, rate=RATE, block=256), frames,
                    rate=RATE, block=256, probe="sine", class_name="source")
                effect = build(probe=probe, ceiling_db=ceiling_db)
                wet = render(effect, frames)
                effect.deinit()
                result = kit.level(wet, dry, tolerance_db=0.05,
                                   skip_frames=512)
                self.assertTrue(result["passed"], result["red"])

    def test_the_gain_macro_is_the_gain_it_says(self):
        # `makeup_db` alone would land after the gain computer; the class
        # drops the threshold by the same number of dB so the pair is
        # gain-then-limit. Below the ceiling that has to read as exactly the
        # gain asked for.
        for gain_db in (0.0, 6.0, 12.0, 24.0):
            with self.subTest(gain_db=gain_db):
                probe = probes.sine(1000.0, 0.5, -40.0)
                frames = len(probe) // 2
                effect = build(probe=probe, ceiling_db=0.0, gain_db=gain_db)
                wet = render(effect, frames)
                effect.deinit()
                self.assertAlmostEqual(peak_dbfs(wet, skip=512),
                                       -40.0 + gain_db, delta=0.1)

    def test_reset_clears_both_nodes_and_leaves_the_source_alone(self):
        # The lookahead ring is the only state either node holds that a probe
        # can see, so the test fills it and then reads it back. The burst ends
        # at `burst_end`; rendering exactly that far leaves the last 480
        # samples of it inside the delay, and the next pull is those samples
        # against a source that is now supplying silence.
        probe, burst_end = probes.burst_silence(hz=1000.0, on_ms=200.0,
                                                total_s=1.0)
        source = probes.ArraySource(probe, rate=RATE, block=256)
        effect = audioeffects.Limiter.create(source, RATE, ceiling_db=-6.0,
                                             lookahead_ms=10.0)
        self.assertNotIn(source, effect._nodes)
        render(effect, burst_end - burst_end % 256)
        primed = int(np.abs(np.frombuffer(render(effect, 256).pcm,
                                          dtype="<i2")).sum())
        effect.reset()
        # reset() restores patch 0, which puts the lookahead back to zero
        # (the contract: audio-component-api.md:201-202). Re-arm it, so what
        # is read next is the ring itself and not the live input.
        effect.set_macro(LOOKAHEAD, macro_of(LOOKAHEAD, 10.0))
        after = int(np.abs(np.frombuffer(render(effect, 256).pcm,
                                         dtype="<i2")).sum())
        self.assertGreater(primed, 0)
        self.assertEqual(after, 0)
        effect.program_change(0)
        self.assertEqual(effect.patch_index, 0)
        effect.deinit()

    def test_deinit_releases_both_nodes_and_is_idempotent(self):
        effect = build(frames=2048)
        nodes = list(effect._nodes)
        self.assertEqual(len(nodes), 2)
        effect.deinit()
        effect.deinit()
        for node in nodes:
            with self.assertRaises(Exception):
                node.set(threshold_db=-1.0)

    def test_capabilities_is_empty_and_the_transport_is_never_read(self):
        calls = []

        def transport():
            calls.append(1)
            return (False, 0.0, 120.0, 4, 4)

        source = probes.ArraySource(probes.silence(48000), rate=RATE,
                                    block=256)
        effect = audioeffects.Limiter.create(source, RATE,
                                             transport=transport)
        render(effect, 24000)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(calls, [])
        effect.deinit()

    def test_mono(self):
        effect = build(channels=1, probe=burst(48000, channels=1),
                       ceiling_db=-12.0, lookahead_ms=5.0)
        self.assertEqual(effect.channel_count, 1)
        result = render(effect, 48000, channels=1)
        effect.deinit()
        self.assertLessEqual(kit.peak_db(result.float[:, 0]) + 12.0, 0.1)

    def test_the_lookahead_clamps_rather_than_refusing_at_a_low_rate(self):
        effect = build(rate=22050, frames=1024, lookahead_ms=10.0)
        self.assertEqual(effect.latency_samples, 220)
        effect.deinit()


class TheSurface(unittest.TestCase):
    def test_the_tier_is_declared_and_the_module_is_named(self):
        from audioeffects import _component
        self.assertEqual(audioeffects.Limiter.TIER, _component.AUDIOIF)
        self.assertEqual(audioeffects.Limiter.REQUIRES, ("audiodynamics",))

    def test_true_peak_on_selects_the_four_times_detector(self):
        # Not the node's older half-band estimate, which does not reach L1.
        effect = build(frames=1024, true_peak=True)
        self.assertEqual(rebuilt.Limiter.TRUE_PEAK_OVERSAMPLED, 2)
        self.assertGreaterEqual(effect.macro(TRUE_PEAK), 0.5)
        effect.deinit()

    def test_the_nodes_are_the_two_the_dossier_names(self):
        effect = build(frames=1024)
        shape, catch = effect._nodes
        self.assertIsInstance(shape, audiodynamics.Dynamics)
        self.assertIsInstance(catch, audiodynamics.Dynamics)
        effect.deinit()

    def test_patch_index_follows_the_contract(self):
        effect = build(frames=1024)
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(CEILING, 100)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)
        effect.deinit()


if __name__ == "__main__":
    unittest.main()
