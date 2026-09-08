"""`Limiter`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Limiter.md`; its Tier 2 rows are L1..L7 and each
one has a test here under its own number. The class gate asks for two things
of every trait, and this file carries both: the measurement, and the *same*
measurement shown red on a fault of the same kind. A green measurement with no
demonstrated red is a measurement that has never been shown able to fail.

The faults are the cheap kind - a subclass, a macro at the wrong end, or the
kit's own faulted read - never a change to a library file.
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

import audiodynamics                                            # noqa: E402
import kit_faults                                               # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects import limiter as rebuilt             # noqa: E402

#: The subject is named directly. `Limiter` has come home to
#: `audioeffects/limiter.py`. These tests still import the home module so a
#: planted subclass is a subclass of the class the traits are about, not
#: whichever class `create("Limiter", ...)` happens to serve.
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
        rebuilt.Limiter._MACRO_RANGES[index], value)


class NoCatchStage(rebuilt.Limiter):
    """L2 and L3's planted fault: the second `Dynamics` removed.

    This is the one-node limiter the dossier's section 4 measured and the
    seed's N-L1 was written about. It is a *whole* fault rather than a
    perturbation because the trait's subject is the composition: the claim is
    that lookahead never creates overshoot, and the thing that makes that true
    is the catch stage. Take it out and the class is the S2 pathology.

    Silent at Lookahead 0: `_build` already gives the shape stage
    `attack_ms=0.0` and `BRICKWALL_RATIO`, so with no delay that stage
    applies its brickwall gain to the same sample its detector sees and
    the catch stage has nothing left to catch. It still guards L2/L3
    from 2 ms of lookahead upward.
    """

    NAME = 'Limiter'

    def _build(self, **options):
        rebuilt.Limiter._build(self, **options)
        self._output = self._shape


class SlowAttack(rebuilt.Limiter):
    """New L1's planted fault at Lookahead 0: both stages get a 10 ms
    attack, so the envelope is no longer the current sample and the
    peak leaves before the gain arrives.

    That is the mechanism `_build` writes as `attack_ms=0.0` on both
    `Dynamics` nodes - the same construction the module docstring names
    as a sample-exact brickwall. Attack is not a macro; no shipped
    patch writes it.
    """

    NAME = 'Limiter'
    ATTACK_MS = 10.0

    def _build(self, **options):
        rebuilt.Limiter._build(self, **options)
        self._shape.set(attack_ms=type(self).ATTACK_MS)
        self._catch.set(attack_ms=type(self).ATTACK_MS)


class NoTruePeakReserve(rebuilt.Limiter):
    """L1's planted fault, and the class as it shipped into the gate audit:
    the catch stage gets none of the Lookahead, so its true-peak detector
    names an inter-sample peak that has already left the node."""

    NAME = 'Limiter'
    TRUE_PEAK_RESERVE_SAMPLES = 0


class FiniteRatio(rebuilt.Limiter):
    """L6's fault of the same kind: a limiting law with a finite ratio.

    **Both** stages, because either one alone still flattens the curve - the
    refutation pass's finding, and the reason a fault on the shape stage's
    ratio alone read green all the way down to ratio 1.0.
    """

    NAME = 'Limiter'
    BRICKWALL_RATIO = 4.0

    def _build(self, ceiling_db=-1.0, gain_db=0.0, lookahead_ms=0.0,
               release_ms=150.0, true_peak=False, knee_db=0.0, patch=None):
        ratio = type(self).BRICKWALL_RATIO
        self._latency = 0
        self._true_peak = bool(true_peak)
        self._shape = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS, sample_rate=self._sample_rate,
            channel_count=self._channel_count, ratio=ratio, attack_ms=0.0))
        self._shape.play(self._source)
        self._catch = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS, sample_rate=self._sample_rate,
            channel_count=self._channel_count, ratio=ratio, attack_ms=0.0,
            release_ms=5.0))
        self._catch.play(self._shape)
        self._output = self._catch
        self._init_macros((ceiling_db, gain_db, lookahead_ms, release_ms,
                           1.0 if true_peak else 0.0, knee_db), patch)


class SoftKneeAlways(rebuilt.Limiter):
    """L6's second fault: the shape stage is handed a 12 dB knee whatever the
    Knee macro says, so the hard-knee clause can go red without moving a
    knob - a knob position is a disconfirmation, not a fault."""

    NAME = 'Limiter'
    FORCED_KNEE_DB = 12.0

    def _apply_macro(self, index, position):
        rebuilt.Limiter._apply_macro(self, index, position)
        if index == KNEE:
            self._shape.set(knee_db=type(self).FORCED_KNEE_DB)


class UndocumentedTrade(rebuilt.Limiter):
    """L7's second clause, given a fault: the sentence that names the
    distortion trade taken out of the docstring."""

    NAME = 'Limiter'
    __doc__ = "Brickwall limiting against a ceiling. audioif tier."


#: What L7's second clause asks the docstring to say, as patterns a run can
#: check. A docstring that stops naming the trade, or names a number the
#: class no longer measures, turns `trade_named` red.
TRADE_PATTERNS = (
    ("fast end", r"([0-9]+\.[0-9]) % THD at the ([0-9]+(?:\.[0-9]+)?) ms "
                 r"end"),
    ("default patch", r"default patch sits at ([0-9]+) ms and "
                      r"([0-9]+\.[0-9]+) %"),
)


def trade_named(cls, measure):
    """L7's second disconfirming clause, re-measured rather than read.

    `measure(release_ms=...)` renders the class and returns THD per cent.
    """
    text = cls.__doc__ or ""
    red = []
    for label, pattern in TRADE_PATTERNS:
        match = re.search(pattern, text)
        if match is None:
            red.append("the docstring does not name the %s" % label)
            continue
        if label == "fast end":
            claimed, ms = (float(group) for group in match.groups())
            floor_ms = rebuilt.Limiter._MACRO_RANGES[RELEASE][0]
            if abs(ms - floor_ms) > 0.01:
                red.append("the docstring calls the fast end %g ms; the "
                           "macro's floor is %g ms" % (ms, floor_ms))
        else:
            ms, claimed = (float(group) for group in match.groups())
        measured = measure(release_ms=ms)
        if abs(claimed - measured) > 0.5:
            red.append("the docstring claims %.2f %% at %g ms; measured "
                       "%.3f %%" % (claimed, ms, measured))
    return {"passed": not red, "red": red}


def build(cls=None, rate=RATE, channels=2, frames=48000, probe=None,
          **options):
    cls = cls or rebuilt.Limiter
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


class L1SamplePeak(unittest.TestCase):
    """New L1: the sample-peak brickwall, including at Lookahead 0."""

    CEILING_DB = -12.0
    RATES = (48000, 44100, 22050)

    def _over(self, cls, rate, lookahead_ms=0.0, probe_factory=burst,
              **options):
        frames = rate
        effect = build(cls, probe=probe_factory(frames=frames), rate=rate,
                       ceiling_db=self.CEILING_DB, release_ms=60.0,
                       lookahead_ms=lookahead_ms, **options)
        over = peak_dbfs(render(effect, frames, rate=rate)) - self.CEILING_DB
        effect.deinit()
        return over

    def test_the_clean_class_holds_the_ceiling_at_three_rates(self):
        for rate in self.RATES:
            for lookahead in (0.0, 2.0, 10.0):
                for factory in (burst, impulse):
                    with self.subTest(rate=rate, lookahead=lookahead,
                                      probe=factory.__name__):
                        over = self._over(rebuilt.Limiter, rate,
                                          lookahead_ms=lookahead,
                                          probe_factory=factory)
                        self.assertLessEqual(over, 0.1, "%+.3f dB" % over)

    def test_the_default_patch_holds_the_ceiling(self):
        for rate in self.RATES:
            with self.subTest(rate=rate):
                frames = rate
                effect = build(probe=burst(frames=frames), rate=rate,
                               ceiling_db=self.CEILING_DB)
                over = (peak_dbfs(render(effect, frames, rate=rate))
                        - self.CEILING_DB)
                self.assertEqual(effect.macro(LOOKAHEAD), 0.0)
                self.assertLess(effect.macro(TRUE_PEAK), 0.5)
                effect.deinit()
                self.assertLessEqual(over, 0.1, "%+.3f dB" % over)

    def test_slow_attack_goes_red_wherever_l1_is_claimed(self):
        for rate in self.RATES:
            for lookahead in (0.0, 2.0, 10.0):
                for factory in (burst, impulse):
                    with self.subTest(rate=rate, lookahead=lookahead,
                                      probe=factory.__name__):
                        over = self._over(SlowAttack, rate,
                                          lookahead_ms=lookahead,
                                          probe_factory=factory)
                        self.assertGreater(over, 0.1, "%+.3f dB" % over)

    def test_no_catch_stage_is_silent_at_lookahead_zero(self):
        over = self._over(NoCatchStage, 48000, lookahead_ms=0.0)
        self.assertLessEqual(over, 0.1, "%+.3f dB" % over)

    def test_no_catch_stage_still_guards_long_lookahead(self):
        over = self._over(NoCatchStage, 48000, lookahead_ms=10.0)
        self.assertGreater(over, 0.1, "%+.3f dB" % over)

    def test_the_fault_is_not_a_position_of_the_surface(self):
        out = kit_faults.fault_reachability(
            rebuilt.Limiter, SlowAttack,
            lambda effect: float(getattr(type(effect), "ATTACK_MS", 0.0)),
            lambda cls: build(cls, probe=probes.silence(2048)),
            label="Limiter new L1 SlowAttack")
        self.assertEqual(out["target"], 10.0)
        self.assertEqual(out["clean"], 0.0)
        self.assertEqual(out["checked"], 108)

    def test_no_surface_position_restores_the_sample_ceiling(self):
        # Rebuild at every kit grid cell and every shipped patch. A
        # 0 dBFS burst against Ceiling 127 (0 dBFS) never enters the
        # limiter - material cannot reach the mechanism - so that one
        # cell is not a restore. Every other cell, and all six patches,
        # stays red.
        positions = tuple(range(0, 128, 8)) + (127,)
        labels = rebuilt.Limiter.MACRO_LABELS
        healthy = []
        checked = 0
        for index, label in enumerate(labels):
            for position in positions:
                effect = build(SlowAttack, probe=burst(),
                               ceiling_db=self.CEILING_DB)
                effect.set_macro(index, position)
                ceiling = effect.macro(CEILING)
                over = peak_dbfs(render(effect, 48000)) - ceiling
                effect.deinit()
                checked += 1
                if over <= 0.1:
                    healthy.append((label, position, over, ceiling))
        for index in sorted(rebuilt.Limiter.PATCHES):
            effect = build(SlowAttack, probe=burst(), patch=index)
            ceiling = effect.macro(CEILING)
            over = peak_dbfs(render(effect, 48000)) - ceiling
            effect.deinit()
            checked += 1
            if over <= 0.1:
                healthy.append(("patch", index, over, ceiling))
        self.assertEqual(checked, 108)
        unrestorable = [(label, pos, over, ceil)
                        for label, pos, over, ceil in healthy
                        if not (label == "Ceiling" and ceil >= -0.05)]
        self.assertEqual(unrestorable, [],
                         "SlowAttack read healthy where the burst was "
                         "into the ceiling: %s" % (unrestorable,))
        self.assertEqual(len(healthy), 1)
        self.assertEqual(healthy[0][0], "Ceiling")


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
        peaks = self._sweep(rebuilt.Limiter, burst)
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
        for lookahead, value in self._peaks(rebuilt.Limiter).items():
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
        for index in sorted(rebuilt.Limiter.PATCHES):
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

    def _fit(self, cls=None, knee_db=0.0, step_db=0.25, low=-32.0,
             high=-16.0, frames=8000):
        """L6's reading, rewritten by the fix round.

        The old one was two numbers that could not fail: a polyfit slope that
        read -0.00000 dB/dB on a build with **no compression at all**, because
        it was measuring the catch stage's clip and not the shape stage's
        ratio; and a bending-band width that returned 0.000 dB from a single
        point and 7.900 dB on a finer grid (gate audit section 3, G3, and the
        refutation record). This is one reading - the kit's CURVE fit of the
        whole law, with its residual - judged on **both** clauses at once, and
        judging them together is what lets it go red on a wire.
        """
        renders = {}
        for level_db in np.arange(low, high + step_db / 2.0, step_db):
            effect = build(cls, probe=sine(1000.0, frames,
                                           dbfs=float(level_db)),
                           ceiling_db=self.CEILING_DB, release_ms=150.0,
                           knee_db=knee_db)
            renders[float(level_db)] = render(effect, frames)
            effect.deinit()
        return kit.curve(renders, detector="peak")["values"]

    @staticmethod
    def _judge(values, knee_db=0.0):
        red = []
        if values["ratio"] is not None and values["ratio"] < 100.0:
            red.append("ratio %.4f" % values["ratio"])
        if knee_db == 0.0 and values["knee_db"] > 0.5:
            red.append("knee %.3f dB" % values["knee_db"])
        return red

    def test_the_law_is_a_brickwall_with_no_knee_at_knee_zero(self):
        values = self._fit()
        self.assertEqual([], self._judge(values), values)
        self.assertLess(values["fit_residual_db"], 0.05)

    def test_the_reading_goes_red_on_the_class_built_as_a_wire(self):
        # The null-build check the pattern revision asks for (section 1.2).
        # A wire fits ratio 1.0, which is what the old slope-only reading
        # could not see.
        wire = kit_faults.wire_build(rebuilt.Limiter)
        self.assertNotEqual([], self._judge(self._fit(cls=wire)))

    def test_a_finite_ratio_in_both_stages_is_red(self):
        self.assertNotEqual([], self._judge(self._fit(cls=FiniteRatio)))

    def test_a_knee_forced_open_is_red_with_the_macro_at_zero(self):
        self.assertNotEqual([], self._judge(self._fit(cls=SoftKneeAlways)))

    def test_neither_fault_is_a_position_of_the_surface(self):
        for cls, reading in (
                (FiniteRatio, lambda e: type(e).BRICKWALL_RATIO),
                (SoftKneeAlways,
                 lambda e: getattr(type(e), "FORCED_KNEE_DB", None))):
            with self.subTest(fault=cls.__name__):
                kit_faults.fault_reachability(
                    rebuilt.Limiter, cls, reading,
                    lambda subject: build(subject, probe=probes.silence(2048)),
                    label="Limiter L6")

    def test_the_knee_figure_is_not_a_property_of_the_grid(self):
        # The refutation's finding: the old width moved 0.000 -> 7.900 dB
        # between a 0.25 dB grid and a 0.05 dB one.
        coarse = self._fit(step_db=0.25)
        fine = self._fit(step_db=0.05)
        self.assertLessEqual(abs(coarse["knee_db"] - fine["knee_db"]), 0.5,
                             "%r vs %r" % (coarse, fine))

    def test_the_knee_tracks_its_macro(self):
        soft = self._fit(knee_db=12.0, step_db=0.5)
        self.assertGreater(soft["knee_db"], 4.0)


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
        """L7's second disconfirming clause, as a check that can fail.

        The gate audit's G3 cell for this class: the clause was true on
        inspection and had **no automated check and no planted fault**. This
        one re-measures what the docstring claims, so a docstring that stops
        naming the trade - or names a number the class no longer produces -
        turns it red.
        """
        reading = trade_named(rebuilt.Limiter, self._thd)
        self.assertTrue(reading["passed"], reading["red"])

    def test_a_docstring_without_the_trade_is_red(self):
        reading = trade_named(UndocumentedTrade, self._thd)
        self.assertFalse(reading["passed"])

    def test_the_docstring_check_goes_red_on_a_wire(self):
        kit_faults.null_build_red(
            rebuilt.Limiter, lambda cls: trade_named(cls, self._thd),
            label="Limiter L7 docstring")

    def test_no_macro_position_changes_the_docstring(self):
        kit_faults.fault_reachability(
            rebuilt.Limiter, UndocumentedTrade,
            lambda effect: type(effect).__doc__,
            lambda cls: build(cls, probe=probes.silence(2048)),
            label="Limiter L7 docstring")

    def test_the_docstring_names_the_lookahead_in_milliseconds(self):
        # The gate's wording: every latency-adding option defaults off or to
        # its shortest and is named in the docstring, in milliseconds.
        text = (rebuilt.Limiter.__doc__ or "") + (
            rebuilt.Limiter._build.__doc__ or "")
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
        effect = rebuilt.Limiter.create(source, RATE, ceiling_db=-6.0,
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
        effect = rebuilt.Limiter.create(source, RATE,
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
        self.assertEqual(rebuilt.Limiter.TIER, _component.AUDIOIF)
        self.assertEqual(rebuilt.Limiter.REQUIRES, ("audiodynamics",))

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


# --------------------------------------------------------------------------
# The fix round: L1's answer to the gate audit, and what it must not cost


class TheTruePeakReserve(unittest.TestCase):
    """L1 after the fix round (gate audit §4.1, audiocomponents#38).

    The catch stage is handed the last `TRUE_PEAK_RESERVE_SAMPLES` of
    whatever the Lookahead macro asks for, because the node's 4x detector
    names an inter-sample peak about five and a half samples after it
    happened and a gain computed from it needs audio behind it to act on.
    These tests hold the three things that reserve must not cost: the
    reported latency, L2 and L3's sample ceiling, and the default state.
    """

    CEILING_DB = -6.0

    def _committed(self, name, rate=RATE):
        import wave
        path = os.path.join(os.path.dirname(__file__), "..", "tools",
                            "effect_probes", str(rate), "2ch", name + ".wav")
        with wave.open(path, "rb") as handle:
            frames = handle.getnframes()
            return array("h", handle.readframes(frames)), frames

    def _over(self, name, cls=None, rate=RATE, **options):
        """The committed probe through the class, read against the ceiling
        over the **aligned** window: the source carries the class's own
        latency in trailing silence and the leading latency is trimmed, so
        the harness's own cut to silence is not read as an overshoot."""
        pcm, frames = self._committed(name, rate)
        padded = array("h", pcm)
        padded.extend([0] * 8192)
        effect = build(cls, probe=padded, rate=rate,
                       ceiling_db=self.CEILING_DB, release_ms=60.0,
                       true_peak=True, **options)
        latency = effect.latency_samples
        result = render(effect, frames + latency, rate=rate, label=name)
        effect.deinit()
        window = kit.Render.from_pcm(result.pcm[latency * 4:], rate, 2,
                                     probe=name, block=256,
                                     interpreter="cpython")
        return kit.truepeak(window, ceiling_dbfs=self.CEILING_DB,
                            tolerance_db=0.5)

    def test_the_promise_holds_at_every_non_zero_lookahead(self):
        for rate in (48000, 44100):
            for lookahead in (0.25, 1.496, 10.0):
                for name in ("ramp_fs", "dc_step", "tone_fs4",
                             "square_1k_-6_peak"):
                    with self.subTest(rate=rate, lookahead=lookahead,
                                      probe=name):
                        reading = self._over(name, rate=rate,
                                             lookahead_ms=lookahead)
                        self.assertTrue(reading["passed"], reading["red"])

    def test_at_lookahead_zero_it_is_a_sample_ceiling_and_says_so(self):
        # The bound, asserted as a bound. An inter-sample peak cannot be
        # caught with no delay to catch it in, so this is the shape of the
        # class and not a defect waiting for a fix - and the docstring and
        # the catalogue row say so.
        reading = self._over("ramp_fs", lookahead_ms=0.0)
        self.assertFalse(reading["passed"])
        self.assertGreater(reading["values"]["over_ceiling_db"], 2.0)
        self.assertIn("Lookahead 0", rebuilt.Limiter.__doc__)

    def test_without_the_reserve_the_ceiling_breaks_at_ten_milliseconds(self):
        # The planted fault of the same kind, at a setting the clean class
        # passes: the class reads +0.16 dB TP over and the fault +0.98.
        clean = self._over("ramp_fs", lookahead_ms=10.0)
        faulted = self._over("ramp_fs", cls=NoTruePeakReserve,
                             lookahead_ms=10.0)
        self.assertTrue(clean["passed"], clean["red"])
        self.assertFalse(faulted["passed"])

    def test_the_fault_is_not_a_position_of_the_surface(self):
        kit_faults.fault_reachability(
            rebuilt.Limiter, NoTruePeakReserve,
            lambda effect: type(effect).TRUE_PEAK_RESERVE_SAMPLES,
            lambda cls: build(cls, probe=probes.silence(2048),
                              true_peak=True, lookahead_ms=1.5),
            label="Limiter L1")

    def test_the_reading_goes_red_on_the_class_built_as_a_wire(self):
        kit_faults.null_build_red(
            rebuilt.Limiter,
            lambda cls: self._over("ramp_fs", cls=cls, lookahead_ms=1.5),
            label="Limiter L1")

    def test_the_reserve_does_not_move_the_reported_latency(self):
        # L4 is the trait the reserve could most easily have cost: the two
        # delays sum to the macro's own number, at every rate and setting.
        for rate in (48000, 44100, 22050):
            for asked in (0.0, 0.5, 1.5, 3.0, 7.3, 10.0):
                with self.subTest(rate=rate, lookahead=asked):
                    wanted = int(asked * rate / 1000.0)
                    for true_peak in (False, True):
                        effect = build(rate=rate, frames=1024,
                                       lookahead_ms=asked,
                                       true_peak=true_peak)
                        self.assertEqual(effect.latency_samples, wanted)
                        effect.deinit()

    def test_the_reserve_does_not_cost_l3(self):
        # A delay in front of a releasing detector is a peak that arrives
        # after the gain has begun coming back. The catch stage's release is
        # stretched with the reserve for exactly this; at the unstretched
        # 5 ms it costs +0.344 dB of L3's +0.100 bar.
        for lookahead in (0.5, 1.0, 2.0, 5.0, 10.0):
            with self.subTest(lookahead=lookahead):
                effect = build(probe=impulse(), ceiling_db=-12.0,
                               release_ms=60.0, lookahead_ms=lookahead,
                               true_peak=True)
                over = peak_dbfs(render(effect, 48000)) + 12.0
                effect.deinit()
                self.assertLessEqual(over, 0.1, "%+.3f dB over" % over)

    def test_true_peak_off_is_byte_for_byte_what_it_always_was(self):
        # The reserve is only taken when True Peak is on, so nothing on the
        # default path moved: this render is the fault's render exactly.
        digests = []
        for cls in (rebuilt.Limiter, NoTruePeakReserve):
            effect = build(cls, probe=burst(), ceiling_db=-12.0,
                           release_ms=60.0, lookahead_ms=5.0, true_peak=False)
            digests.append(render(effect, 48000).digest)
            effect.deinit()
        self.assertEqual(digests[0], digests[1])


if __name__ == "__main__":
    unittest.main()
