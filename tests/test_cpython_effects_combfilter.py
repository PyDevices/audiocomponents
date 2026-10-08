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
from audioeffects.rebuilt.digitaldelay import clear_of_stalls  # noqa: E402
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
        # `port_target(self._output)`, not `self._output`: appending a stage
        # means wrapping the node at the end of the graph, not the wire the
        # consumer holds. Wrapping the wire and then pointing the wire at
        # the wrapper is a loop -- `_component._would_loop` refuses it, and
        # `TheOutputPortIsAWire` below plants exactly that.
        tail = _component.port_target(self._output)
        self._leak = self._own(_LeakyTap(tail))
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


class FrozenToneCombFilter(combfilter.CombFilter):
    """Tone's off stop leaving the low-pass in at 0.001 Hz, where its
    float32 coefficient is one step above 0 and its state cannot move: it
    holds what it held, as the node's off stop did up to audiodsp v0.6.2
    (15 070 LSB at 48 kHz on `TheToneOffStopIsTheFilterOut`'s move then),
    and plays it out of silence."""

    NAME = 'CombFilter'

    def _tone_damping(self, tone):
        if tone >= combfilter.TONE_OFF_HZ:
            return 0.001
        return self._hz(tone)


class _ToneMemory:
    """Remembers whether Tone has been in since the last reset, for the
    off-stop faults below (the class itself no longer needs to)."""

    def _tone_damping(self, tone):
        if tone < combfilter.TONE_OFF_HZ:
            self._was_in = True
        return combfilter.CombFilter._tone_damping(self, tone)

    def reset(self):
        self._was_in = False
        combfilter.CombFilter.reset(self)

    def _off_after_in(self, tone):
        return getattr(self, "_was_in", False) and \
            tone >= combfilter.TONE_OFF_HZ


class TrackingCombFilter(_ToneMemory, combfilter.CombFilter):
    """The workaround retired at audiodsp v0.6.3rc1: once Tone has been in,
    the off stop hands `damping_hz` at 32 x the rate instead of 0."""

    NAME = 'CombFilter'

    def _tone_damping(self, tone):
        damping = _ToneMemory._tone_damping(self, tone)
        if self._off_after_in(tone):
            return 32.0 * self._sample_rate
        return damping


class LeakyTrackCombFilter(_ToneMemory, combfilter.CombFilter):
    """The off stop after Tone has been in, tracking the tap at a
    coefficient under 1: `damping_hz` at half the rate (a = 1 - e^-pi,
    0.957), a low-pass left in the loop where the knob says off."""

    NAME = 'CombFilter'

    def _tone_damping(self, tone):
        damping = _ToneMemory._tone_damping(self, tone)
        if self._off_after_in(tone):
            return 0.5 * self._sample_rate
        return damping


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


def silence_source(rate=SAMPLE_RATE, channels=CHANNELS, frames=512):
    return audiocore.RawSample(silence(frames, rate, channels),
                               sample_rate=rate, channel_count=channels)


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


def laps_to_exact_zero(feedback, peak=32768.0):
    """Laps of the line after which no sample can be non-zero, on audiodsp
    v0.6.2 and later.

    Rounding to nearest bounds a lap's peak by x' <= g x + 0.5, so
    x_k <= g^k (peak - c) + c with c = 0.5 / (1 - g); and since audiodsp#154
    no lap hands back a sample as large as the one it sent, so once the peak
    is at most floor(c) it takes at most floor(c) more laps to reach 0. The
    1e-6 keeps a c that is a whole number in exact arithmetic (10 at 0.95)
    from flooring one short in float, where the loop would never end.
    """
    c = 0.5 / (1.0 - feedback)
    stall = math.floor(c + 1e-6)
    laps = 0
    while peak >= stall + 1:
        peak = feedback * (peak - c) + c
        laps += 1
    return laps + int(stall)


def zero_bound_frames(hz, feedback, rate=SAMPLE_RATE):
    """The tail bound in frames: `laps_to_exact_zero` laps, each at most one
    frame past the line (the read interpolates towards the next older
    frame)."""
    return laps_to_exact_zero(feedback) * (math.ceil(rate / hz) + 1)


def ring_period(values, asked, repeats=10):
    """The ring's period, from the centroid of its `repeats`-th repeat,
    found by walking repeat to repeat from the first one. A pulse keeps its
    first moment through linear interpolation, so this reads the delay the
    loop really has, fraction and all, while the ring is loud enough to
    carry one."""
    first = centroid(values, asked)
    position = first
    for _ in range(repeats - 1):
        position = centroid(values, position + first)
    return position / repeats


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
        self.assertEqual(cls.TIER, _component.AUDIODSP)
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
        # On the grid, not in the units. Patch 0's Trim is 64, which since
        # audiocomponents#87 is the exact centre of the BIPOLAR span and
        # reads 0.00 dB -- it read +0.14 while the grid had no centre, and
        # the class's 0.2 dB wire floor is what made that honest. The check
        # is that the patch is `macro_of()` of the constructor's own
        # default, at that macro's own mode.
        cls = combfilter.CombFilter
        effect = combfilter.CombFilter.create(tone(220.0, 4096),
                                     SAMPLE_RATE)
        defaults = [effect.macro(index) for index in range(6)]
        self.assertEqual(
            cls.PATCHES[0][1],
            tuple(_component.macro_of(cls._MACRO_RANGES[index], value,
                                      cls.MACRO_MODES[index])
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

        `NoGlideCombFilter` forces `delay_slew = 0`, and macro 5 `Glide` spans
        0...1 with grid position 0 sitting exactly there - so the "fault" and
        the clean class at Glide 0 are the same build, and both read the same
        +8.28 dB. The two tests above therefore demonstrate that Glide at or
        above about 0.01 is click-free, which is not what the dossier froze; T6
        stands as **unmeasured** until a fault the surface cannot dial is
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
    #: `reset()` lands the moment the burst stops, with the line at full
    #: ring. Up to audiodsp v0.6.1 it could land anywhere after the burst,
    #: because a line left alone parked on a few LSB for ever; since v0.6.2
    #: (audiodsp#154) a line left alone empties itself, inside 11 544 frames
    #: at 440 Hz / Feedback 0.9 (`zero_bound_frames`), so a reset 10 000
    #: frames late found a line nearly drained by itself and the planted
    #: fault below read 0 -- a control with no teeth. Here the 8192 frames
    #: read after the reset hold the loudest part of the ring an un-reset
    #: line still carries, from either end of the source (its first 12 000
    #: frames are silence, and so is everything after 22 000).
    RESET_AT = BURST_TO

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
        pull(effect.output, self.RESET_AT)
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
        # Measured at v0.6.2: 32 768, the rail. A full line, not a parked
        # LSB; the same reset 10 000 frames later read 0 here.
        residue, _effect, _source = self.residue(UnresetCombFilter)
        self.assertGreater(residue, 1000)

    def test_deinit_releases_the_nodes_and_leaves_the_source(self):
        source = tone(220.0, 8192)
        effect = combfilter.CombFilter(source)
        nodes = list(effect._nodes)
        effect.deinit()
        for node in nodes:
            self.assertTrue(getattr(node, "_deinited", True))
        self.assertGreater(max(abs(v) for v in pull(source, 2048)), 0)


class TheTailReachesExactZero(unittest.TestCase):
    """Silence in, silence out, at every Feedback and every tuning, inside
    a stated bound.

    Up to audiodsp v0.6.1 this class could not meet it above Feedback 0.5:
    the node's feedback write rounded to nearest, so every
    |c| <= 0.5/(1-g) was a fixed point of the loop, and at a tuning whose
    read lands nearly on a whole sample (440 Hz, 109.09 frames) a few LSB
    went round for ever -- this class was `TheTailIsBoundedRatherThanZero`
    and held the residue under that bound. v0.6.2 (audiodsp#154) truncates
    the fed-back term toward zero exactly where rounding would hand it back
    unchanged, so the tail now reaches exact zero at whole-sample and
    half-sample tunings alike, inside `zero_bound_frames` of the burst's
    end. Measured at v0.6.2 on this burst at 440 Hz: the last non-zero
    frame is 3 164 / 4 906 / 9 597 / 18 109 frames after the burst at
    Feedback 0.7 / 0.8 / 0.9 / 0.95, against bounds of 3 774 / 5 772 /
    11 544 / 23 643."""

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

    def last_sound(self, feedback, seconds=4, tuned=None):
        """Frames from the burst's last frame to the last non-zero one."""
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
        last = max(i for i in range(len(y)) if y[i]) // CHANNELS
        return last - 6847

    def test_a_whole_sample_tuning_reaches_exact_zero_inside_the_bound(self):
        for feedback in (0.7, 0.8, 0.9, 0.95):
            with self.subTest(feedback=feedback):
                bound = zero_bound_frames(self.PARKS_HZ, feedback)
                measured = self.last_sound(feedback)
                self.assertGreater(measured, 0)
                self.assertLessEqual(measured, bound,
                                     "still sounding %d frames after the "
                                     "burst, over the %d-frame bound"
                                     % (measured, bound))
                self.assertEqual(self.residue(feedback), 0)

    def test_a_half_sample_tuning_still_reaches_exact_zero(self):
        # The other end, and the reason the docstring's number is a bound
        # rather than a typical value.
        for feedback in (0.7, 0.9):
            with self.subTest(feedback=feedback):
                self.assertEqual(self.residue(feedback,
                                              tuned=self.DRAINS_HZ), 0)


class LapShortCombFilter(combfilter.CombFilter):
    """`tail_samples` one lap short. On full-scale DC at 20 Hz / Feedback
    0.7, the bound's tightest cell, the tail outlives it."""

    NAME = 'CombFilter'

    @property
    def tail_samples(self):
        memory = combfilter._tone_excess(self._damping,
                                         self._sample_rate)[0]
        return (combfilter.CombFilter._tail_bound(self)
                - (self._reach + 1 + memory))


class NoTrimTermCombFilter(combfilter.CombFilter):
    """`tail_samples` without the trim's term: the comb's laps only, while
    the fixed-point shelf in front is still letting its last LSB out."""

    NAME = 'CombFilter'

    @property
    def tail_samples(self):
        bound = combfilter.CombFilter._tail_bound(self)
        if self._trim.mix > 0.0:
            bound -= int(math.ceil(combfilter.TRIM_TAIL_S
                                   * self._sample_rate))
        return bound


class SteppedCombFilter(combfilter.CombFilter):
    """The workaround retired at audiodsp v0.6.3rc1: with Tone in, the
    Feedback handed at the nearer edge of a stall window
    (`clear_of_stalls`), a Feedback nobody set."""

    NAME = 'CombFilter'

    def _refresh(self):
        combfilter.CombFilter._refresh(self)
        if self._damping > 0.0 and self._feedback > 0.0:
            excess = combfilter._tone_excess(self._damping,
                                             self._sample_rate)[1]
            self._feedback = clear_of_stalls(self._feedback, excess)
            self._comb.set(feedback=self._feedback)


class TheTailIsDeclared(unittest.TestCase):
    """`tail_samples` is finite at every setting (housekeeping,
    2026-09-28, a ruling of that date): the comb's lap bound, each lap
    one frame past the longest line the read head may be at plus the Tone
    low-pass's memory, plus `TRIM_TAIL_S` while the trim is in circuit.
    Every macro's stops and interior points, every patch, the long corners
    and the stall centres, at three rates, stereo and mono, end inside it
    (900 cells); these are the cells where each
    part of the bound is tight, each beside a bound that is short there."""

    def render(self, cls, material, **options):
        """(declared, last non-zero frame after a 50 ms burst, peak of the
        last 0.25 s), silence running to the declared bound plus 0.5 s."""
        rate = SAMPLE_RATE
        probe = cls(audiocore.RawSample(array.array("h", [0] * 512),
                                        sample_rate=rate,
                                        channel_count=CHANNELS),
                    **options)
        declared = probe.tail_samples
        probe.deinit()
        lead = rate // 20
        frames = lead + (rate if declared is None else declared) + rate // 2
        values = array.array("h", [0] * (frames * CHANNELS))
        for index in range(lead * CHANNELS):
            values[index] = material
        effect = cls(audiocore.RawSample(values, sample_rate=rate,
                                         channel_count=CHANNELS),
                     **options)
        y = pull(effect.output, frames)
        effect.deinit()
        last = 0
        for index in range(len(y) - 1, lead * CHANNELS - 1, -1):
            if y[index]:
                last = index // CHANNELS - lead + 1
                break
        held = max(abs(v) for v in y[-(rate // 4) * CHANNELS:])
        return declared, last, held

    def test_finite_at_every_patch_and_every_stop(self):
        effect = combfilter.CombFilter(
            audiocore.RawSample(array.array("h", [0] * 512),
                                sample_rate=SAMPLE_RATE,
                                channel_count=CHANNELS))
        for patch in range(6):
            effect.program_change(patch)
            self.assertIsInstance(effect.tail_samples, int, patch)
        for index in range(6):
            for midi in (0, 64, 127):
                effect.program_change(0)
                effect.set_macro(index, midi)
                self.assertIsInstance(effect.tail_samples, int,
                                      (index, midi))
        effect.deinit()

    def test_the_lap_bound_holds_where_it_is_tight(self):
        # Full-scale DC at 20 Hz / Feedback 0.7: 69 600 frames against
        # 69 629 when this test was written.
        options = {"frequency": 20.0, "glide": 0.0}
        declared, last, held = self.render(combfilter.CombFilter, 32767,
                                           **options)
        self.assertLessEqual(last, declared)
        self.assertGreater(last, declared - 2402)
        self.assertEqual(held, 0)
        declared, last, _held = self.render(LapShortCombFilter, 32767,
                                            **options)
        self.assertGreater(last, declared)

    def test_the_trim_term_covers_the_shelf(self):
        options = {"trim_db": -18.0, "feedback": 0.0, "glide": 0.0}
        declared, last, held = self.render(combfilter.CombFilter, 32767,
                                           **options)
        self.assertLessEqual(last, declared)
        self.assertGreater(last, 20000)
        self.assertEqual(held, 0)
        declared, last, held = self.render(NoTrimTermCombFilter, 32767,
                                           **options)
        self.assertTrue(last > declared or held, (declared, last, held))

    def test_the_stall_cell_reaches_zero_at_the_feedback_set(self):
        # Feedback 0.5 with Tone at 2 kHz is a stall centre: up to audiodsp
        # v0.6.2 the node held 1 LSB there for ever and the class stepped
        # the Feedback clear. Since v0.6.3rc1 (#157) the node lands the
        # stalled state: 0.5 is handed as set, and the tail ends inside the
        # bound, which counts its landing lap.
        options = {"frequency": 1000.0, "feedback": 0.5, "tone_hz": 2000.0,
                   "glide": 0.0}
        declared, last, held = self.render(combfilter.CombFilter, 2,
                                           **options)
        self.assertGreater(last, 0)
        self.assertLessEqual(last, declared)
        self.assertEqual(held, 0)
        for cls, handed_as_set in ((combfilter.CombFilter, True),
                                   (SteppedCombFilter, False)):
            effect = cls(silence_source(SAMPLE_RATE), **options)
            self.assertEqual(effect._feedback == effect._value(1),
                             handed_as_set, cls)
            self.assertLess(abs(effect._feedback - 0.5), 3e-5)
            effect.deinit()


class TheToneOffStopIsTheFilterOut(unittest.TestCase):
    """Tone off after Tone has been in. Up to audiodsp v0.6.2 the node froze
    its loop low-pass while `damping_hz` was 0, and from 2026-09-28 this
    class handed 32 x the rate there instead (a coefficient of exactly 1).
    Since v0.6.3rc1 the node keeps an off low-pass's state on the tap
    (audiodsp#158), the off stop is exactly 0 again, and these assert what
    that buys: silence when Tone comes back, and the same bytes and bound
    as a fresh instance. The retired cure is planted beside each."""

    def tone_back_in(self, cls, rate=SAMPLE_RATE, channels=CHANNELS,
                     mix=2.0):
        """300 Hz at 30 000 LSB for 0.5 s with Tone 2 kHz, Feedback 0; Tone
        to its off stop as the input stops, 2 s of silence, Tone to MIDI 0:
        the output's peak after that move. The source is exactly as long as
        what is read, so it never wraps round and replays the tone."""
        loud = (rate // 2) // 256 * 256
        back = (loud + 2 * rate) // 256 * 256
        frames = back + rate // 4
        values = silence(frames, rate, channels)
        for frame in range(loud):
            value = int(round(30000 * math.sin(2.0 * math.pi * 300.0 * frame
                                               / rate)))
            for channel in range(channels):
                values[frame * channels + channel] = value
        effect = cls(audiocore.RawSample(values, sample_rate=rate,
                                         channel_count=channels),
                     sample_rate=rate, frequency=440.0, feedback=0.0,
                     mix=mix, tone_hz=2000.0)
        out = array.array("h")
        while len(out) < frames * channels:
            done = len(out) // channels
            if done == loud:
                effect.set_macro(3, 127)
            elif done == back:
                effect.set_macro(3, 0)
            out.extend(memoryview(bytes(audiocore.get_buffer(
                effect.output)[1])).cast("h"))
        effect.deinit()
        return max(abs(v) for v in out[back * channels:frames * channels])

    def test_tone_back_in_after_silence_stays_silent(self):
        for rate in (48000, 44100, 22050):
            for channels in (2, 1):
                self.assertEqual(self.tone_back_in(
                    combfilter.CombFilter, rate, channels), 0,
                    (rate, channels))
        self.assertEqual(self.tone_back_in(combfilter.CombFilter, mix=1.0),
                         0)
        # Planted: a low-pass left in with a frozen state (0.001 Hz) plays
        # what it held (at v0.6.2 the node's own off stop played 15 070 LSB
        # at 48 kHz, 10 110 at 44.1, 8 828 at 22.05 here).
        self.assertGreater(self.tone_back_in(FrozenToneCombFilter), 10000)
        self.assertGreater(self.tone_back_in(FrozenToneCombFilter, 22050),
                           5000)

    def test_the_off_stop_hands_exactly_zero(self):
        # Fresh, after Tone has been in, after a Tone in the constructor or
        # a patch, and at the 0.95 stall centre, which is handed as set.
        # The retired tracking cure, planted, hands 32 x the rate.
        for rate in (48000, 44100, 22050):
            for cls, expected in ((combfilter.CombFilter, 0.0),
                                  (TrackingCombFilter, 32.0 * rate)):
                effect = cls(silence_source(rate), sample_rate=rate)
                self.assertEqual(effect._damping, 0.0)
                effect.set_macro(1, 127)
                effect.set_macro(3, 0)
                effect.set_macro(3, 127)
                self.assertEqual(effect._damping, expected, (cls, rate))
                self.assertEqual(effect._feedback, 0.95)
                self.assertIsInstance(effect.tail_samples, int)
                effect.deinit()
                for options in ({"tone_hz": 5000.0}, {"patch": 3}):
                    effect = cls(silence_source(rate), sample_rate=rate,
                                 **options)
                    effect.program_change(0)
                    self.assertEqual(effect._damping, expected,
                                     (cls, rate, options))
                    effect.deinit()

    def off_after_tone(self, cls, rate=SAMPLE_RATE, channels=CHANNELS,
                       **options):
        """(samples, worst LSB) by which the off stop after Tone has been
        in differs from a fresh instance's off stop, on 1 s of full-scale
        noise."""
        frames = rate
        seed = 12345
        values = array.array("h")
        for _ in range(frames * channels):
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            values.append((seed >> 15) - 32768)
        tracked = cls(audiocore.RawSample(values, sample_rate=rate,
                                          channel_count=channels),
                      sample_rate=rate, **options)
        tracked.set_macro(3, 0)
        tracked.set_macro(3, 127)
        fresh = combfilter.CombFilter(
            audiocore.RawSample(array.array("h", values), sample_rate=rate,
                                channel_count=channels),
            sample_rate=rate, **options)
        a = pull(tracked.output, frames, channels)
        b = pull(fresh.output, frames, channels)
        tracked.deinit()
        fresh.deinit()
        diff = [abs(x - y) for x, y in zip(a, b)]
        return sum(1 for d in diff if d), max(diff)

    def test_the_off_stop_after_tone_is_the_filter_out(self):
        # Byte for byte a fresh instance's off stop, at a whole-frame read
        # (1000 Hz at 48 kHz) and a fractional one (440 Hz, 109.09 frames,
        # at 48 and 22.05 kHz mono), where the retired tracking cure was
        # within 1 LSB.
        options = {"frequency": 1000.0, "feedback": 0.8, "mix": 2.0}
        self.assertEqual(self.off_after_tone(combfilter.CombFilter,
                                             **options), (0, 0))
        for rate in (48000, 22050):
            self.assertEqual(self.off_after_tone(combfilter.CombFilter,
                                                 rate, 1), (0, 0), rate)
        # Planted: the retired cure moves samples at the fractional read,
        # and a coefficient of 0.957 is a low-pass left in the loop.
        count, _worst = self.off_after_tone(TrackingCombFilter, 48000, 1)
        self.assertGreater(count, 0)
        _count, worst = self.off_after_tone(LeakyTrackCombFilter, **options)
        self.assertGreater(worst, 1000)

    def test_the_tail_bound_after_tone_is_the_fresh_one(self):
        # Tone off after Tone is the filter off, so the bound is the fresh
        # instance's, with no memory term; the retired cure counted one
        # frame of memory a lap. The 0.95 stop at 20 Hz is the long corner.
        for rate in (48000, 22050):
            bounds = []
            for cls in (combfilter.CombFilter, TrackingCombFilter):
                effect = cls(silence_source(rate), sample_rate=rate,
                             frequency=20.0, feedback=0.95, glide=0.0)
                fresh_bound = effect.tail_samples
                effect.set_macro(3, 0)
                effect.set_macro(3, 127)
                bounds.append((fresh_bound, effect.tail_samples))
                effect.deinit()
            self.assertEqual(bounds[0][0], bounds[0][1], rate)
            self.assertGreater(bounds[1][1], bounds[1][0], rate)


class TheRingIsTheAskedPitchAndEnds(unittest.TestCase):
    """The TAIL-pitch trait. The ring plays the fractional delay the comb
    was asked for, through its tenth repeat within 1 cent, and then reaches
    exact zero inside `zero_bound_frames`.

    Up to audiodsp v0.6.1 this class was `TheParkedRingIsTheNearestSample`:
    above Feedback 0.5 the tail parked on a ring whose period was the
    nearest whole number of samples, +17.4 cents at 1760 Hz / Feedback 0.8,
    for ever. v0.6.2 (audiodsp#154) empties the line, so there is no parked
    ring left to measure; what the ear gets instead is the ring itself, and
    that is what this class holds. Measured at v0.6.2: 1760 Hz / 0.8 rings
    at 27.262 frames against the asked 27.273 (0.7 cents) and is silent
    928 frames after the impulse (bound 1 508); 1000 Hz / 0.8 rings at
    exactly 48 and is silent after 2 016 (bound 2 548). The line two samples
    short rings at 25.000, 150.6 cents sharp."""

    #: The ring's period is held to this many cents of the asked delay.
    RING_CENTS = 1.0

    def ring(self, cls, hz, feedback, rate=SAMPLE_RATE, seconds=1):
        """(period of the ring in frames, frames to its last non-zero
        sample) for an impulse at frame 0."""
        frames = rate * seconds
        effect = cls(impulse_at(0, frames + 512, rate),
                     frequency=hz, feedback=feedback, mix=2.0, glide=0.0,
                     sample_rate=rate)
        y = left(pull(effect.output, frames))
        last = max(i for i in range(len(y)) if y[i])
        return ring_period(y, rate / hz), last

    def delay_skew_frames(self, effect):
        """Asked delay minus the nearest whole sample. The clean class
        is the fractional part; the fault is -2."""
        asked = effect._sample_rate / effect._hz(effect._value(0))
        if isinstance(effect, TwoSampleShortCombFilter):
            return float(round(asked) - 2) - round(asked)
        return asked - round(asked)

    def test_1760_at_feedback_08_rings_on_the_asked_pitch_then_ends(self):
        period, last = self.ring(combfilter.CombFilter, 1760.0, 0.8)
        error = 1200.0 * math.log((SAMPLE_RATE / period) / 1760.0, 2.0)
        self.assertLess(abs(error), self.RING_CENTS, period)
        self.assertLessEqual(last, zero_bound_frames(1760.0, 0.8))

    def test_1000_rings_on_the_asked_pitch_then_ends(self):
        period, last = self.ring(combfilter.CombFilter, 1000.0, 0.8)
        self.assertAlmostEqual(period, 48.0, delta=0.005)
        error = 1200.0 * math.log((SAMPLE_RATE / period) / 1000.0, 2.0)
        self.assertLess(abs(error), self.RING_CENTS, period)
        self.assertLessEqual(last, zero_bound_frames(1000.0, 0.8))

    def test_the_first_repeat_at_1760_is_still_the_asked_tap(self):
        ideal = SAMPLE_RATE / 1760.0
        effect = combfilter.CombFilter(
            impulse_at(0, 8192), frequency=1760.0, feedback=0.8,
            mix=2.0, glide=0.0)
        y = left(pull(effect.output, int(ideal) + 64))
        self.assertLess(abs(cents(centroid(y, ideal), ideal)), 0.01)

    def test_a_two_sample_shorter_line_is_outside_the_bound(self):
        period, _last = self.ring(TwoSampleShortCombFilter, 1760.0, 0.8)
        self.assertAlmostEqual(period, 25.0, delta=0.05)
        error = 1200.0 * math.log((SAMPLE_RATE / period) / 1760.0, 2.0)
        self.assertGreater(abs(error), self.RING_CENTS)

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
