"""`CombFilter`'s own invariant and planted-fault tests.

The Tier 2 traits are measured in the evidence pack with the kit; what is
here is the subset a rebuild must not be allowed to regress silently, each
one paired with a fault that turns it red. A checker that has only ever
passed has not been shown to work, so no assertion below stands without its
faulted twin.

There were no old-surface `CombFilter` tests to retire: the class it
replaces declared `MACRO_LABELS = ()` and had no surface for a test to
reach, which is the fourth defect in the dossier's section 7.

The measurements are impulse- and tone-domain and are computed here rather
than taken from the kit, so this file runs in the ordinary suite without a
render on disk. They are the same quantities: a repeat's amplitude-weighted
centroid for the tuning, a single-bin DFT for the steady-state gain, and a
second difference at the block boundaries for the click.
"""

import array
import math
import os
import sys
import unittest

import audiocore

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
import kit_faults as faults                          # noqa: E402
from effects_measure import SAMPLE_RATE                # noqa: E402

from audioeffects import _component                    # noqa: E402
from audioeffects import combfilter            # noqa: E402
#: The subject is named directly. `CombFilter` has come home to
#: `audioeffects/combfilter.py`. These tests still import the home module so
#: a planted-fault subclass is measured against this file, not only
#: `create()`.

#: `_component` reads `VENDOR` off the module a class is *defined* in, not
#: off the one its base came from, so the planted-fault subclasses below
#: need one here or the metadata check refuses them before they can be
#: measured.
VENDOR = "PyDevices"

CHANNELS = 2


# -- the faults -------------------------------------------------------------

class WholeSampleCombFilter(combfilter.CombFilter):
    """T3's fault: tune to the nearest whole sample instead of asking for a
    fractional one. Everything else about the build is untouched, so only
    the tuning may move."""

    NAME = 'CombFilter'

    def _refresh(self):
        combfilter.CombFilter._refresh(self)
        frames = round(self._sample_rate / self._hz(self._value(0)))
        self._comb.set(delay_ms=1000.0 * frames / self._sample_rate)


class SixCentSharpCombFilter(combfilter.CombFilter):
    """T3's second fault: a +6 cent bias on the requested delay, an eighth
    of the 5-cent bar. The whole-sample rounder is green at 110 Hz; this
    one is red everywhere, including there."""

    NAME = 'CombFilter'

    def _refresh(self):
        combfilter.CombFilter._refresh(self)
        frequency = self._hz(self._value(0)) * (2.0 ** (6.0 / 1200.0))
        self._comb.set(delay_ms=1000.0 / frequency)


class SquaredFeedbackCombFilter(combfilter.CombFilter):
    """T2's fault: the loop runs at g squared, so every peak and null is
    the height of a different feedback setting."""

    NAME = 'CombFilter'

    def _refresh(self):
        combfilter.CombFilter._refresh(self)
        self._comb.set(feedback=self._value(1) ** 2)


class NoUnitySnapCombFilter(combfilter.CombFilter):
    """T5's fault: drop the Mix snap, so patch-grid "Mix 1" is 1.0079 and
    the dry leg is 0.9921 instead of unity."""

    NAME = 'CombFilter'

    def _refresh(self):
        combfilter.CombFilter._refresh(self)
        self._comb.set(mix=self._value(2))


class NoGlideCombFilter(combfilter.CombFilter):
    """T6's fault: the read head jumps to a new delay instead of walking to
    it -- the node's behaviour before Ask 2 landed."""

    NAME = 'CombFilter'

    def _refresh(self):
        combfilter.CombFilter._refresh(self)
        self._comb.set(delay_slew=0.0)


class LeakyWireCombFilter(combfilter.CombFilter):
    """The bypass fault: the dry path multiplied by 32767/32768, which is
    inaudible and is not a wire."""

    NAME = 'CombFilter'

    def _build(self, **options):
        combfilter.CombFilter._build(self, **options)
        self._leak = self._own(_LeakyTap(self._output))
        self._output = self._leak


class _LeakyTap(audiocore._AudioSample if hasattr(audiocore, "_AudioSample")
                else object):
    """One LSB off the top of every sample. Not an effect -- a fault."""

    def __init__(self, source):
        self._source = source
        self.sample_rate = source.sample_rate
        self.channel_count = source.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True
        self.single_buffer = False
        self.max_buffer_length = 512 * 2 * source.channel_count
        self._deinited = False

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        audiocore.reset_buffer(self._source)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        result, data = audiocore.get_buffer(self._source, False, 0)
        values = array.array("h")
        values.extend(memoryview(bytes(data)).cast("h"))
        for index in range(len(values)):
            values[index] = int(values[index] * 32767 // 32768)
        return result, values

    def deinit(self):
        self._deinited = True


class TwoSampleShortCombFilter(combfilter.CombFilter):
    """TAIL-pitch fault: the line is two whole samples shorter than the
    nearest sample to F_s/f. The parked ring then sits well outside the
    half-sample cents bound the class states."""

    NAME = 'CombFilter'

    def _refresh(self):
        combfilter.CombFilter._refresh(self)
        frames = round(self._sample_rate / self._hz(self._value(0))) - 2
        self._comb.set(delay_ms=1000.0 * frames / self._sample_rate)


class UnresetCombFilter(combfilter.CombFilter):
    """The state fault the vision names for this family: a delay line left
    full after `reset()`."""

    NAME = 'CombFilter'

    def _build(self, **options):
        combfilter.CombFilter._build(self, **options)
        self._resets[self._nodes.index(self._comb)] = False


class ShortLatencyCombFilter(combfilter.CombFilter):
    """The CLICK fault: report 256 samples of latency the DSP does not
    have. The audio is untouched, so only the reported number may move."""

    NAME = 'CombFilter'
    LATENCY_SAMPLES = 256


# -- helpers ----------------------------------------------------------------

def silence(frames, rate=SAMPLE_RATE, channels=CHANNELS):
    return array.array("h", bytes(2 * channels * frames))


def impulse_at(frame, frames, rate=SAMPLE_RATE, channels=CHANNELS,
               level=20000):
    values = silence(frames, rate, channels)
    for channel in range(channels):
        values[frame * channels + channel] = level
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def tone(hz, frames, rate=SAMPLE_RATE, channels=CHANNELS, level=2000):
    values = array.array("h")
    for frame in range(frames):
        value = int(level * math.sin(2.0 * math.pi * hz * frame / rate))
        for _ in range(channels):
            values.append(value)
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def pull(node, frames, channels=CHANNELS):
    out = array.array("h")
    while len(out) < frames * channels:
        data = memoryview(bytes(audiocore.get_buffer(node)[1])).cast("h")
        if not len(data):
            break
        out.extend(data)
    return out[:frames * channels]


def left(values, channels=CHANNELS):
    return values[0::channels]


def centroid(values, around, span=3):
    """The amplitude-weighted centre of a repeat, to sub-sample resolution.
    Linear interpolation preserves a pulse's first moment, so this reads the
    delay the node was actually asked for, fraction and all."""
    low = max(0, int(around) - span)
    high = min(len(values), int(around) + span + 1)
    weight = sum(abs(values[i]) for i in range(low, high))
    if not weight:
        return 0.0
    return sum(i * abs(values[i]) for i in range(low, high)) / weight


def cents(measured, ideal):
    return 1200.0 * math.log(ideal / measured, 2.0) if measured else 1e9


def bin_db(values, hz, rate=SAMPLE_RATE, skip=0):
    """One DFT bin, in dB relative to full scale of the probe's own units."""
    real = imaginary = 0.0
    count = len(values) - skip
    for index in range(skip, len(values)):
        angle = 2.0 * math.pi * hz * index / rate
        real += values[index] * math.cos(angle)
        imaginary += values[index] * math.sin(angle)
    return 20.0 * math.log10(2.0 * math.hypot(real, imaginary) / count
                             + 1e-12)


def wet_gain_db(cls, hz, probe_hz, feedback, rate=SAMPLE_RATE):
    """Steady-state gain at `probe_hz` through the comb tuned to `hz`, wet
    only, against the same tone through the class at Mix 0.

    Two things the reading needs and a shorter render will not give. The
    probe is scaled so that even the peak stays inside int16 -- at Feedback
    0.95 the comb has +26 dB, and a probe that clips reads about a decibel
    low, which looks exactly like a filter that is wrong. And the render is
    long enough for the loop to settle: the envelope decays by `g` per pass
    of `F_s/hz` frames, so reaching -60 dB takes `-6.91/ln(g)` passes, which
    at 0.95 is 135 of them.
    """
    level = int(20000 * (1.0 - feedback) * 0.8) or 1
    passes = int(-6.91 / math.log(feedback)) + 2 if feedback else 4
    settle = int(passes * rate / hz) + rate // 4
    frames = settle + rate // 2
    made = cls(tone(probe_hz, frames + 4096, rate, level=level),
               frequency=hz, feedback=feedback, mix=2.0, glide=0.0,
               sample_rate=rate)
    dry = cls(tone(probe_hz, frames + 4096, rate, level=level),
              frequency=hz, feedback=feedback, mix=0.0, glide=0.0,
              sample_rate=rate)
    return (bin_db(left(pull(made.output, frames)), probe_hz, rate,
                   skip=settle)
            - bin_db(left(pull(dry.output, frames)), probe_hz, rate,
                     skip=settle))


def click_excess_db(cls, rate=SAMPLE_RATE, block=512, seconds=1.0):
    """T6's estimator: the worst second difference *at* a block boundary,
    minus the 99.9th percentile of the ones off the boundaries in the same
    render. A discontinuity in the read pointer shows up here; the running
    waveform's own curvature is what is subtracted off."""
    frames = int(rate * seconds)
    effect = cls(tone(440.0, frames + 8192, rate, level=8000),
                 frequency=100.0, feedback=0.7, mix=1.0, sample_rate=rate)
    out = array.array("h")
    steps = frames // block
    for step in range(steps):
        position = step / max(1, steps - 1)
        effect.set_macro(0, _component.macro_of(
            cls._MACRO_RANGES[0], 100.0 * (10.0 ** position)))
        data = memoryview(bytes(audiocore.get_buffer(effect.output)[1]))
        out.extend(data.cast("h"))
    y = left(out)
    start = rate // 4
    on = off = []
    on, off = [], []
    for index in range(start, len(y) - 2):
        value = abs(y[index + 2] - 2 * y[index + 1] + y[index])
        (on if (index + 2) % block == 0 else off).append(value)
    off.sort()
    floor = off[int(0.999 * (len(off) - 1))]
    return 20.0 * math.log10((max(on) + 1e-9) / (floor + 1e-9))


# -- the tests --------------------------------------------------------------

class TheSurface(unittest.TestCase):
    def test_the_six_macros_and_six_patches_are_the_frozen_ones(self):
        cls = combfilter.CombFilter
        self.assertEqual(cls.MACRO_LABELS,
                         ("Frequency", "Feedback", "Mix", "Tone", "Trim",
                          "Glide"))
        self.assertEqual(len(cls.PATCHES), 6)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertIsNone(cls.TAIL_SAMPLES)
        self.assertEqual(cls.TIER, _component.AUDIOIF)
        self.assertEqual(cls.REQUIRES, ("audioecho", "audiobiquad"))

    def test_every_patch_is_reachable_and_moves_the_comb(self):
        effect = combfilter.CombFilter.create(tone(220.0, 4096),
                                     SAMPLE_RATE)
        tuned = set()
        for index in range(len(combfilter.CombFilter.PATCHES)):
            effect.program_change(index)
            self.assertEqual(effect.patch_index, index)
            tuned.add(round(effect.macro(0), 3))
        self.assertEqual(len(tuned), 6)

    def test_patch_zero_is_the_constructors_defaults_on_the_grid(self):
        # On the grid, not in the units: a BIPOLAR macro has no exact centre
        # on 0-127, so patch 0's Trim is 64 and reads +0.14 dB. The class
        # treats anything under 0.2 dB as a wire, which is what makes that
        # honest -- the check is that the patch is `macro_of()` of the
        # constructor's own default.
        cls = combfilter.CombFilter
        effect = combfilter.CombFilter.create(tone(220.0, 4096),
                                     SAMPLE_RATE)
        defaults = [effect.macro(index) for index in range(6)]
        self.assertEqual(
            cls.PATCHES[0][1],
            tuple(_component.macro_of(cls._MACRO_RANGES[index], value)
                  for index, value in enumerate(defaults)))


class TheCombTunesFractionally(unittest.TestCase):
    """T3, and the fault that rounds it onto the sample grid."""

    PROBES = (55.0, 110.0, 440.0, 880.0, 1760.0, 3520.0)

    def measure(self, cls, hz, rate=SAMPLE_RATE):
        ideal = rate / hz
        effect = cls(impulse_at(0, 8192, rate), frequency=hz, feedback=0.0,
                     mix=2.0, glide=0.0, sample_rate=rate)
        y = left(pull(effect.output, int(ideal) + 64))
        return cents(centroid(y, ideal), ideal)

    def test_every_request_lands_within_five_cents(self):
        for hz in self.PROBES:
            with self.subTest(hz=hz):
                self.assertLess(abs(self.measure(combfilter.CombFilter, hz)),
                                5.0)

    def test_rounding_onto_the_sample_grid_is_red(self):
        # The discriminating probes: below a few hundred hertz the grid is
        # finer than five cents and a rounder is indistinguishable.
        worst = max(abs(self.measure(WholeSampleCombFilter, hz))
                    for hz in (880.0, 1760.0, 3520.0))
        self.assertGreater(worst, 5.0)
        # ... and the same fault at 110 Hz is *not* caught, which is why the
        # trait names where it has teeth.
        self.assertLess(abs(self.measure(WholeSampleCombFilter, 110.0)), 5.0)

    def test_a_six_cent_bias_is_red_even_at_110_hz(self):
        # The refuter's fault: an eighth of the bar, and it fires where
        # the rounder cannot.
        error = self.measure(SixCentSharpCombFilter, 110.0)
        self.assertGreater(abs(error), 5.0)
        # This file's cents() is 1200*log(ideal/measured); a shorter line
        # reads +6. The auditor's -6.000 is the same bias with the opposite
        # sign convention.
        self.assertAlmostEqual(abs(error), 6.0, delta=0.05)


class TheFeedbackKnobIsThePeakHeight(unittest.TestCase):
    """T2 below 2 kHz, where the dossier freezes the 0.2 dB tolerance."""

    def test_the_peak_and_null_follow_the_closed_form(self):
        for feedback in (0.3, 0.5, 0.8, 0.95):
            with self.subTest(feedback=feedback):
                peak = wet_gain_db(combfilter.CombFilter, 200.0, 200.0,
                                   feedback)
                null = wet_gain_db(combfilter.CombFilter, 200.0, 300.0,
                                   feedback)
                self.assertAlmostEqual(
                    peak, 20.0 * math.log10(1.0 / (1.0 - feedback)),
                    delta=0.2)
                self.assertAlmostEqual(
                    null, 20.0 * math.log10(1.0 / (1.0 + feedback)),
                    delta=0.2)

    def test_a_squared_feedback_is_red(self):
        peak = wet_gain_db(SquaredFeedbackCombFilter, 200.0, 200.0, 0.8)
        self.assertGreater(abs(peak - 20.0 * math.log10(1.0 / 0.2)), 0.2)


class ZeroFeedbackIsTheFeedforwardComb(unittest.TestCase):
    """T5, and the fault the Mix snap exists to prevent."""

    #: The comb is tuned to 1 kHz, so the peaks are at 1, 2, 3 kHz and the
    #: nulls at 500 Hz, 1500, 2500. Each is probed at its own frequency: a
    #: null is a property of the transfer function, and a 1 kHz tone carries
    #: nothing at 500 Hz for it to cancel.
    TUNED_HZ = 1000.0

    def render(self, cls, probe_hz, mix_macro=64):
        # Mix is set from the 0-127 grid on purpose: that is where the snap
        # earns its place. A constructor asked for 1.0 gets 1.0 either way.
        effect = cls(tone(probe_hz, 28096), frequency=self.TUNED_HZ,
                     feedback=0.0, glide=0.0)
        effect.set_macro(2, mix_macro)
        return left(pull(effect.output, 24000))

    def test_the_null_is_total_and_the_peak_is_six_decibels(self):
        cls = combfilter.CombFilter
        for null_hz in (500.0, 1500.0, 2500.0):
            with self.subTest(hz=null_hz):
                self.assertLess(
                    bin_db(self.render(cls, null_hz), null_hz, skip=12000),
                    -60.0)
        for peak_hz in (1000.0, 2000.0):
            with self.subTest(hz=peak_hz):
                wet = bin_db(self.render(cls, peak_hz), peak_hz, skip=12000)
                dry = bin_db(self.render(cls, peak_hz, mix_macro=0), peak_hz,
                             skip=12000)
                self.assertAlmostEqual(wet - dry, 6.02, delta=0.1)

    def test_without_the_mix_snap_the_null_fills_in(self):
        y = self.render(NoUnitySnapCombFilter, 500.0)
        self.assertGreater(bin_db(y, 500.0, skip=12000), -60.0)


class TheTuningKnobIsClickFree(unittest.TestCase):
    """T6, and the fault of the jump the slew replaced."""

    def test_the_boundary_is_not_findable(self):
        self.assertLess(click_excess_db(combfilter.CombFilter), 1.0)

    def test_a_jumped_read_head_is_red(self):
        self.assertGreater(click_excess_db(NoGlideCombFilter), 1.0)

    def test_but_the_kit_rejects_this_fault_as_a_position_of_the_surface(
            self):
        """The gate audit's ruling on T6, committed as a test.

        `docs/effects-phase2-gate-audit.md` section 4.1: `NoGlideCombFilter`
        forces `delay_slew = 0`, and macro 5 `Glide` spans 0...1 with grid
        position 0 sitting exactly there - so the "fault" and the clean
        class at Glide 0 are the same build, and both read the same
        +8.28 dB. The two tests above therefore demonstrate that Glide at or
        above about 0.01 is click-free, which is not what the dossier froze;
        T6 stands as **unmeasured** until a fault the surface cannot dial is
        written.

        This asserts the kit's own check now catches it
        (`kit_faults.fault_reachability`, pattern revision section 1.3).
        """
        def build(cls):
            values = array.array("h", [0] * (2048 * CHANNELS))
            return cls.create(audiocore.RawSample(
                values, sample_rate=SAMPLE_RATE,
                channel_count=CHANNELS), SAMPLE_RATE)

        with self.assertRaises(faults.FaultReachable) as caught:
            faults.fault_reachability(combfilter.CombFilter, 0.0,
                                      lambda effect: effect.macro(5), build)
        self.assertIn("macro 5 'Glide' at grid position 0",
                      str(caught.exception))


class TheBypassIsAWire(unittest.TestCase):
    def probe(self):
        values = array.array("h")
        for frame in range(4096):
            for channel in range(CHANNELS):
                values.append(((frame * (61 + channel * 17)) % 401) - 200)
        return values

    def render(self, cls, **options):
        values = self.probe()
        effect = cls(audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                                         channel_count=CHANNELS), **options)
        return pull(effect.output, 4096)

    def test_mix_zero_is_byte_identical_to_the_source(self):
        self.assertEqual(list(self.render(combfilter.CombFilter, mix=0.0,
                                          feedback=0.9)),
                         list(self.probe()))

    def test_mix_zero_with_a_trim_asked_for_is_still_a_wire(self):
        self.assertEqual(list(self.render(combfilter.CombFilter, mix=0.0,
                                          trim_db=-12.0)),
                         list(self.probe()))

    def test_one_lsb_off_the_dry_path_is_red(self):
        self.assertNotEqual(list(self.render(LeakyWireCombFilter, mix=0.0)),
                            list(self.probe()))


class TheLatencyIsZero(unittest.TestCase):
    """The impulse comes out in the frame it went in, at both rates."""

    def arrival(self, cls, rate):
        effect = cls(impulse_at(64, 4096, rate), frequency=440.0,
                     feedback=0.7, mix=1.0, glide=0.0, sample_rate=rate)
        y = left(pull(effect.output, 1024))
        for index in range(len(y)):
            if y[index]:
                return index
        return -1

    def test_the_measured_delay_matches_the_reported_zero(self):
        for rate in (48000, 44100):
            with self.subTest(rate=rate):
                effect = combfilter.CombFilter(impulse_at(64, 512, rate),
                                               sample_rate=rate)
                self.assertEqual(effect.latency_samples, 0)
                self.assertEqual(self.arrival(combfilter.CombFilter, rate)
                                 - 64, 0)

    def test_a_class_that_reports_256_short_is_red(self):
        effect = ShortLatencyCombFilter(impulse_at(64, 512, 48000))
        self.assertNotEqual(
            effect.latency_samples,
            self.arrival(ShortLatencyCombFilter, 48000) - 64)


class ResetEmptiesTheLine(unittest.TestCase):
    """The Tier 1 state invariant, and this family's own planted fault."""

    #: The burst sits after the frames this test reads back, on purpose.
    #: Emptying a node's pending buffer makes it re-read its source, and
    #: `audiocore.RawSample` hands its buffer back from the beginning
    #: (`_component`'s own note): a probe whose burst is early replays it
    #: after `reset()` and reads exactly like a line that was never cleared.
    BURST_FROM = 12000
    BURST_TO = 22000

    def residue(self, cls):
        values = array.array("h")
        for frame in range(48000):
            value = 0
            if self.BURST_FROM <= frame < self.BURST_TO:
                value = int(20000 * math.sin(2.0 * math.pi * 440.0 * frame
                                             / SAMPLE_RATE))
            for _ in range(CHANNELS):
                values.append(value)
        source = audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                                     channel_count=CHANNELS)
        effect = cls(source, frequency=440.0, feedback=0.9, mix=2.0,
                     glide=0.0)
        pull(effect.output, 32000)
        effect.reset()
        return max(abs(v) for v in pull(effect.output, 8192)), effect, source

    def test_reset_leaves_the_line_silent_and_the_source_rendering(self):
        residue, _effect, source = self.residue(combfilter.CombFilter)
        self.assertEqual(residue, 0)
        # The borrowed source is untouched: it still carries its burst, so
        # reading on past this point finds it. Where the cursor sits after a
        # reset is the source's business, not the class's, so the read is
        # long enough to reach the burst from either end.
        self.assertGreater(max(abs(v) for v in pull(source, 48000)), 0)

    def test_a_line_left_full_is_red(self):
        residue, _effect, _source = self.residue(UnresetCombFilter)
        self.assertGreater(residue, 0)

    def test_deinit_releases_the_nodes_and_leaves_the_source(self):
        source = tone(220.0, 8192)
        effect = combfilter.CombFilter(source)
        nodes = list(effect._nodes)
        effect.deinit()
        for node in nodes:
            self.assertTrue(getattr(node, "_deinited", True))
        self.assertGreater(max(abs(v) for v in pull(source, 2048)), 0)


class TheTailIsBoundedRatherThanZero(unittest.TestCase):
    """The one Tier 1 invariant this class does not always meet, held to
    both ends of what it does. `to_s16` rounds, so every |c| <= 0.5/(1-g) is
    a fixed point of the loop -- but whether the loop can sit on one is
    decided by the *fractional part* of `sample_rate / Frequency`, not by the
    feedback alone. 440 Hz is 109.09 frames: the read is nearly exact and a
    lone LSB survives its round trip. 438.3 Hz is 109.51: the interpolator
    averages it with a zero neighbour and rounds it away. Both are asserted,
    because the first alone would read as "this class never settles" and the
    second alone as "it always does"."""

    #: 48 000 / 440 = 109.09 frames -- 0.09 of a sample off the grid.
    PARKS_HZ = 440.0
    #: 48 000 / 438.3 = 109.51 frames -- half a sample off it.
    DRAINS_HZ = 438.3

    def residue(self, feedback, seconds=4, tuned=None):
        values = array.array("h")
        for frame in range(SAMPLE_RATE * seconds):
            value = 0
            if 2048 <= frame < 6848:
                value = int(20000 * math.sin(2.0 * math.pi * 440.0 * frame
                                             / SAMPLE_RATE))
            for _ in range(CHANNELS):
                values.append(value)
        effect = combfilter.CombFilter(
            audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                                channel_count=CHANNELS),
            frequency=self.PARKS_HZ if tuned is None else tuned,
            feedback=feedback, mix=2.0, glide=0.0)
        y = pull(effect.output, SAMPLE_RATE * seconds)
        return max(abs(v) for v in y[-SAMPLE_RATE:])

    def test_below_half_the_line_reaches_exact_zero(self):
        self.assertEqual(self.residue(0.45), 0)

    def test_a_whole_sample_tuning_parks_inside_the_closed_form_bound(self):
        for feedback in (0.7, 0.8, 0.9):
            with self.subTest(feedback=feedback):
                bound = math.floor(0.5 / (1.0 - feedback))
                measured = self.residue(feedback)
                self.assertGreater(measured, 0)
                self.assertLessEqual(measured, bound)

    def test_a_half_sample_tuning_still_reaches_exact_zero(self):
        # The other end, and the reason the docstring's number is a bound
        # rather than a typical value.
        for feedback in (0.7, 0.9):
            with self.subTest(feedback=feedback):
                self.assertEqual(self.residue(feedback,
                                              tuned=self.DRAINS_HZ), 0)


class TheParkedRingIsTheNearestSample(unittest.TestCase):
    """The TAIL-pitch bound. Above Feedback 0.5 the parked ring's period
    is the nearest whole number of samples to F_s/Frequency, not the
    fractional delay the comb was asked for: +17.4 cents at 1760 Hz /
    Feedback 0.8 (27 samples at 48 kHz) and at most a half-sample —
    about 70 cents — near 4 kHz. The first-repeat tap still lands
    within 0.01 cents. Below Feedback 0.5, and at half-sample tunings,
    the tail reaches exact zero."""

    #: Half a sample at 4 kHz / 48 kHz is 70.67 cents; the bound the
    #: class states is "about 70 cents".
    HALF_SAMPLE_CENTS = 70.0

    def parked_period(self, cls, hz, feedback, rate=SAMPLE_RATE, seconds=4):
        frames = rate * seconds
        effect = cls(impulse_at(0, frames + 512, rate),
                     frequency=hz, feedback=feedback, mix=2.0, glide=0.0,
                     sample_rate=rate)
        y = left(pull(effect.output, frames))
        edges = [i for i in range(1, len(y) - 2048, 1)
                 if y[i - 1] == 0 and y[i] != 0 and i >= frames - rate]
        if len(edges) < 4:
            edges = [i for i in range(max(1, frames - rate), len(y))
                     if y[i - 1] == 0 and y[i] != 0]
        self.assertGreater(len(edges), 3, "tail did not oscillate")
        gaps = [edges[i] - edges[i - 1] for i in range(1, len(edges))]
        return sum(gaps) / len(gaps)

    def delay_skew_frames(self, effect):
        """Asked delay minus the nearest whole sample. The clean class
        is the fractional part; the fault is -2."""
        asked = effect._sample_rate / effect._hz(effect._value(0))
        if isinstance(effect, TwoSampleShortCombFilter):
            return float(round(asked) - 2) - round(asked)
        return asked - round(asked)

    def test_1760_at_feedback_08_parks_27_samples_17_cents_sharp(self):
        period = self.parked_period(combfilter.CombFilter, 1760.0, 0.8)
        self.assertAlmostEqual(period, 27.0, delta=0.05)
        error = 1200.0 * math.log((SAMPLE_RATE / period) / 1760.0, 2.0)
        self.assertAlmostEqual(error, 17.4, delta=0.2)
        self.assertLess(abs(error), self.HALF_SAMPLE_CENTS)

    def test_1000_parks_on_the_asked_pitch(self):
        period = self.parked_period(combfilter.CombFilter, 1000.0, 0.8)
        self.assertAlmostEqual(period, 48.0, delta=0.05)
        error = 1200.0 * math.log((SAMPLE_RATE / period) / 1000.0, 2.0)
        self.assertAlmostEqual(error, 0.0, delta=0.2)

    def test_the_first_repeat_at_1760_is_still_the_asked_tap(self):
        ideal = SAMPLE_RATE / 1760.0
        effect = combfilter.CombFilter(
            impulse_at(0, 8192), frequency=1760.0, feedback=0.8,
            mix=2.0, glide=0.0)
        y = left(pull(effect.output, int(ideal) + 64))
        self.assertLess(abs(cents(centroid(y, ideal), ideal)), 0.01)

    def test_a_two_sample_shorter_line_is_outside_the_bound(self):
        period = self.parked_period(TwoSampleShortCombFilter, 1760.0, 0.8)
        self.assertAlmostEqual(period, 25.0, delta=0.05)
        error = 1200.0 * math.log((SAMPLE_RATE / period) / 1760.0, 2.0)
        self.assertGreater(abs(error), self.HALF_SAMPLE_CENTS)

    def test_the_surface_cannot_dial_the_two_sample_short(self):
        def build(cls):
            return cls.create(impulse_at(0, 2048), SAMPLE_RATE)

        faults.fault_reachability(
            combfilter.CombFilter, TwoSampleShortCombFilter,
            self.delay_skew_frames, build, tolerance=0.25)


class TheClassIsRateHonest(unittest.TestCase):
    def test_the_tuning_holds_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                ideal = rate / 880.0
                effect = combfilter.CombFilter(
                    impulse_at(0, 8192, rate), frequency=880.0, feedback=0.0,
                    mix=2.0, glide=0.0, sample_rate=rate)
                y = left(pull(effect.output, int(ideal) + 64))
                self.assertLess(abs(cents(centroid(y, ideal), ideal)), 5.0)

    def test_a_tone_corner_above_nyquist_clamps_rather_than_raising(self):
        effect = combfilter.CombFilter(tone(440.0, 4096, 22050),
                                       tone_hz=18000.0, sample_rate=22050)
        self.assertLessEqual(effect._comb._state and 1, 1)   # built at all
        self.assertGreater(max(abs(v) for v in
                               pull(effect.output, 2048)), 0)


class MonoIsTheSameComb(unittest.TestCase):
    def test_a_mono_source_gets_the_same_tuning(self):
        ideal = SAMPLE_RATE / 880.0
        values = array.array("h", bytes(2 * 8192))
        values[0] = 20000
        effect = combfilter.CombFilter(
            audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                                channel_count=1),
            frequency=880.0, feedback=0.0, mix=2.0, glide=0.0)
        self.assertEqual(effect.channel_count, 1)
        y = pull(effect.output, int(ideal) + 64, channels=1)
        self.assertLess(abs(cents(centroid(y, ideal), ideal)), 5.0)


if __name__ == "__main__":                              # pragma: no cover
    unittest.main()
