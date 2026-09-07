"""`LowPass`'s own invariant and planted-fault tests.

The class's Tier 2 traits are measured in the evidence pack with the kit;
what is here is the subset a rebuild must not be allowed to regress
silently, each one paired with a fault that turns it red. A checker that has
only ever passed has not been shown to work, so no assertion below stands
without its faulted twin.

The two old-surface traits this replaces - the `LowPass` legs of
`test_cpython_effects_dynamics_eq.py`'s `..._above_nyquist_is_refused` (the
class clamps now, and the dossier's section 7 names the raise as the defect)
and of `..._sits_at_its_corner_across_the_whole_band` above 20 kHz (outside
the frozen span) - are retired in the same commit, in that file.

Numpy-free, like `tests/support/effects_measure`: the response readings are
computed from each section's own live `coefficients`, so they measure the
filter the class actually built rather than a re-derivation of RBJ beside it.
"""

import array
import cmath
import math
import os
import sys
import unittest

import audiocore
import audioeffects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import SAMPLE_RATE, source        # noqa: E402

from audioeffects import _component                    # noqa: E402
from audioeffects.rebuilt import lowpass               # noqa: E402

#: `_component` reads `VENDOR` off the module a class is *defined* in, not
#: off the one its base came from, so the planted-fault subclass below needs
#: one here or the metadata check refuses it before it can be measured.
VENDOR = "PyDevices"


def magnitude_db(node, hz, rate=SAMPLE_RATE):
    """|H| of one built section in dB, read off its live coefficients. A
    section at `mix` 0 is a wire and contributes exactly 0 dB."""
    if node.mix == 0.0:
        return 0.0
    b0, b1, b2, a1, a2 = node.coefficients
    z = cmath.exp(-2j * math.pi * hz / rate)
    return 20.0 * math.log10(abs((b0 + b1 * z + b2 * z * z)
                                 / (1.0 + a1 * z + a2 * z * z)))


def response_db(effect, hz, rate=SAMPLE_RATE):
    return sum(magnitude_db(node, hz, rate) for node in effect._nodes)


def warped(hz, rate=SAMPLE_RATE):
    """T2's axis: `f_a = (F_s/pi) * tan(pi f / F_s)`, and its inverse."""
    return (rate / math.pi) * math.tan(math.pi * hz / rate)


def unwarped(f_a, rate=SAMPLE_RATE):
    return (rate / math.pi) * math.atan(math.pi * f_a / rate)


def burst_then_silence(rate=SAMPLE_RATE, burst=9600, seconds=6, channels=2):
    """Tone then zeros **inside one sample**.

    Once a source ends, the node downstream is handed silence by a different
    code path and the state it is holding is never asked for again - which is
    how audioif#23 hid for as long as it did. So the silence is part of the
    sample, and every pull below stays strictly inside it.
    """
    values = array.array("h")
    for frame in range(int(seconds * rate)):
        value = 0
        if frame < burst:
            value = int(32000 * math.sin(2.0 * math.pi * 60.0 * frame / rate))
        for _ in range(channels):
            values.append(value)
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def pull_ints(node, frames, channels=2):
    out = array.array("h")
    while len(out) < frames * channels:
        data = memoryview(bytes(audiocore.get_buffer(node)[1])).cast("h")
        if not len(data):
            break
        out.extend(data)
    return out


class TheSurface(unittest.TestCase):
    def test_the_five_macros_and_six_patches_are_the_frozen_ones(self):
        self.assertEqual(lowpass.LowPass.MACRO_LABELS,
                         ("Frequency", "Resonance", "Slope", "Mix", "Trim"))
        self.assertEqual(len(lowpass.LowPass.PATCHES), 6)
        self.assertEqual(lowpass.LowPass.CAPABILITIES, ())
        self.assertEqual(lowpass.LowPass.LATENCY_SAMPLES, 0)
        self.assertEqual(lowpass.LowPass.TIER, _component.AUDIOIF)
        self.assertEqual(lowpass.LowPass.REQUIRES, ("audiobiquad",))

    def test_every_patch_is_reachable_and_moves_the_filter(self):
        effect = audioeffects.create("LowPass", source(), SAMPLE_RATE)
        seen = set()
        for index in range(len(lowpass.LowPass.PATCHES)):
            effect.program_change(index)
            self.assertEqual(effect.patch_index, index)
            seen.add(round(effect.macro(0), 3))
        # Six patches, six different corners - a patch table whose entries
        # all sounded the same would pass every other test in this file.
        self.assertEqual(len(seen), 6)


class TheCornerIsTheResonance(unittest.TestCase):
    """T1, at both slopes, and the fault that moves it."""

    QS = (0.5, 0.7071067811865476, 1.0, 2.0, 4.0, 8.0, 16.0)

    def corner_gain(self, slope, q, hz=1000.0):
        effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                     frequency=hz, q=q, slope=slope)
        return response_db(effect, hz)

    def test_the_corner_gain_reads_q_at_both_slopes(self):
        for slope in (12, 24):
            for q in self.QS:
                with self.subTest(slope=slope, q=q):
                    self.assertAlmostEqual(self.corner_gain(slope, q),
                                           20.0 * math.log10(q), delta=0.05)

    def test_scaling_both_butterworth_qs_is_red(self):
        """The fault of the same kind: the design decision A15 records.

        Scaling *both* section Qs by the resonance - the reading of section 4
        this class rejected - squares the corner gain. It must go red on T1's
        own bar at 24 dB/oct while 12 dB/oct, which has one section, stays
        green. A fault that turned both red would not be telling them apart.
        """
        for q in (2.0, 4.0, 8.0):
            with self.subTest(q=q):
                effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                             frequency=1000.0, q=q, slope=24)
                scale = q / lowpass.FLAT_Q
                effect._pole_one.Q = lowpass.BUTTERWORTH_LOW * scale
                faulted = response_db(effect, 1000.0)
                self.assertGreater(abs(faulted - 20.0 * math.log10(q)), 0.05)
                # ... and it lands where the squared law says it does.
                self.assertAlmostEqual(faulted, 40.0 * math.log10(q) + 3.01,
                                       delta=0.1)


class TheShapeIsOneCurve(unittest.TestCase):
    """T2 on the warped axis, and the fault that deforms it."""

    RATIOS = (0.125, 0.5, 1.0, 2.0, 4.0, 8.0)
    CORNERS = (31.5, 125.0, 500.0, 1000.0, 2000.0, 4000.0)

    def curve(self, effect, corner):
        base = warped(corner)
        return [response_db(effect, unwarped(base * ratio))
                for ratio in self.RATIOS]

    def test_the_warped_curve_is_the_same_at_every_corner(self):
        reference = None
        for corner in self.CORNERS:
            effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                         frequency=corner)
            values = self.curve(effect, corner)
            if reference is None:
                reference = values
                continue
            for ratio, one, other in zip(self.RATIOS, reference, values):
                with self.subTest(corner=corner, ratio=ratio):
                    self.assertAlmostEqual(one, other, delta=0.05)

    def test_a_corner_moved_fifteen_percent_deforms_it(self):
        """RESPONSE's own fault, applied to T2's readout: one section retuned
        while the other is not is a curve that is no longer one curve."""
        effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                     frequency=1000.0, slope=24)
        clean = self.curve(effect, 1000.0)
        effect._pole_two.frequency = 1150.0
        faulted = self.curve(effect, 1000.0)
        worst = max(abs(one - other) for one, other in zip(clean, faulted))
        self.assertGreater(worst, 0.05)


class TheSlopeIsTwelveDecibelsAnOctave(unittest.TestCase):
    """T3 on the warped axis, at both slopes."""

    def fitted(self, effect, corner):
        base = warped(corner)
        four = response_db(effect, unwarped(base * 4.0))
        eight = response_db(effect, unwarped(base * 8.0))
        return four, eight - four

    def test_twelve_and_twenty_four_decibels_an_octave(self):
        for corner in (31.5, 125.0, 500.0, 2000.0):
            with self.subTest(corner=corner):
                gentle = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                             frequency=corner)
                four, slope = self.fitted(gentle, corner)
                self.assertAlmostEqual(four, -24.10, delta=0.05)
                self.assertAlmostEqual(slope, -12.03, delta=0.05)

                steep = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                            frequency=corner, slope=24)
                four, slope = self.fitted(steep, corner)
                self.assertAlmostEqual(four, -48.19, delta=0.10)
                self.assertAlmostEqual(slope, -24.06, delta=0.10)

    def test_the_second_section_left_as_a_wire_is_red(self):
        """The fault of the same kind: Slope says 24 dB/oct and only one
        section is in the path. The corner gain stays green - both sections
        would have to move for that - so this fires on part of the readout,
        which is what separates it from a tripwire."""
        effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                     frequency=125.0, slope=24)
        corner_before = response_db(effect, 125.0)
        effect._pole_two.mix = 0.0
        four, slope = self.fitted(effect, 125.0)
        self.assertGreater(abs(slope - (-24.06)), 0.10)
        # One section left, so it rolls off at twelve rather than
        # twenty-four. Not exactly -12.03: the section left standing carries
        # the Butterworth 0.5412 rather than 0.707, which is a shallower
        # approach to the asymptote.
        self.assertAlmostEqual(slope, -11.75, delta=0.10)
        self.assertNotAlmostEqual(response_db(effect, 125.0), corner_before,
                                 delta=0.05)


class TheTailReachesExactZero(unittest.TestCase):
    """Tier 1's first invariant - the one the tier moved for."""

    def residual(self, cls_or_name, **options):
        sample = burst_then_silence()
        effect = (cls_or_name.create(sample, SAMPLE_RATE, **options)
                  if not isinstance(cls_or_name, str)
                  else audioeffects.create(cls_or_name, sample, SAMPLE_RATE,
                                           **options))
        values = pull_ints(effect.output, SAMPLE_RATE * 5)
        settle = values[-len(values) // 10:]
        return max(abs(value) for value in settle)

    def test_the_rebuilt_class_settles_on_exact_zero(self):
        for hz, q in ((100.0, 0.7071067811865476), (40.0, 8.0)):
            with self.subTest(hz=hz, q=q):
                self.assertEqual(self.residual("LowPass", frequency=hz, q=q),
                                 0)

    def test_the_ported_biquad_the_class_replaced_is_red(self):
        """The planted fault is the node this class does not use.

        `audioif#23`'s own two configurations, built on `synthio.Biquad`
        through `audiofilters.Filter` - the palette the old class was on -
        park on a non-zero word and hold it. Same probe, same pulls, same
        settle window as the green run above, so the difference is the node.
        """
        import audiofilters
        import synthio
        residuals = []
        for hz, q in ((100.0, 0.7071067811865476), (40.0, 8.0)):
            sample = burst_then_silence()
            node = audiofilters.Filter(
                filter=synthio.Biquad(synthio.FilterMode.LOW_PASS, hz, Q=q),
                mix=1.0, sample_rate=SAMPLE_RATE, channel_count=2,
                bits_per_sample=16, samples_signed=True, buffer_size=2048)
            node.play(sample)
            values = pull_ints(node, SAMPLE_RATE * 5)
            settle = values[-len(values) // 10:]
            residuals.append(max(abs(value) for value in settle))
        self.assertGreater(max(residuals), 0)


class TheBypassIsAWire(unittest.TestCase):
    def dry_and_wet(self, **options):
        probe = source()
        dry = pull_ints(probe, 4096)
        probe = source()
        effect = audioeffects.create("LowPass", probe, SAMPLE_RATE, **options)
        return dry, pull_ints(effect.output, 4096)

    def test_mix_zero_is_byte_identical_to_the_source(self):
        dry, wet = self.dry_and_wet(mix=0.0)
        self.assertEqual(bytes(dry), bytes(wet))

    def test_mix_zero_with_a_trim_asked_for_is_still_a_wire(self):
        # The trim is the filter's make-up, so it goes with the filter. A
        # class that let the trim through at Mix 0 would fail WIRE on
        # material a wire test would otherwise pass.
        dry, wet = self.dry_and_wet(mix=0.0, trim_db=6.0)
        self.assertEqual(bytes(dry), bytes(wet))

    def test_one_lsb_on_the_dry_path_is_red(self):
        """The fault of the same kind, so the comparison above is shown to
        be able to fail: one LSB moved in the bypassed render."""
        dry, wet = self.dry_and_wet(mix=0.0)
        faulted = array.array("h", wet)
        faulted[17] = faulted[17] + (1 if faulted[17] < 32767 else -1)
        self.assertNotEqual(bytes(dry), bytes(faulted))


class TheClassIsRateHonest(unittest.TestCase):
    def test_a_corner_above_nyquist_clamps_rather_than_raising(self):
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                effect = audioeffects.create(
                    "LowPass", source(rate=rate), rate, frequency=rate * 0.9)
                built = effect._pole_one.frequency
                self.assertLessEqual(built, rate * 0.5)
                self.assertGreater(built, rate * 0.4)

    def test_the_corner_gain_is_q_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                effect = audioeffects.create("LowPass", source(rate=rate),
                                             rate, frequency=1000.0)
                self.assertAlmostEqual(response_db(effect, 1000.0, rate),
                                       -3.01, delta=0.05)


class TheTrimIsFlat(unittest.TestCase):
    def test_the_trim_is_the_gain_it_says_across_the_band(self):
        for want in (-12.0, -6.0, 6.0, 12.0):
            for hz in (50.0, 200.0, 1000.0, 5000.0, 15000.0):
                with self.subTest(want=want, hz=hz):
                    effect = audioeffects.create("LowPass", source(),
                                                 SAMPLE_RATE, trim_db=want)
                    self.assertAlmostEqual(magnitude_db(effect._trim, hz),
                                           want, delta=0.02)

    def test_a_ten_hertz_corner_is_red_at_the_bottom(self):
        """The fault of the same kind, and it is the alternative A15
        rejected: the same shelf an octave up is out by nearly a decibel at
        20 Hz while staying green everywhere above 50."""
        effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                     trim_db=12.0)
        effect._trim.frequency = 10.0
        self.assertGreater(abs(magnitude_db(effect._trim, 20.0) - 12.0), 0.5)
        self.assertAlmostEqual(magnitude_db(effect._trim, 200.0), 12.0,
                               delta=0.05)

    def test_a_trim_under_the_floor_is_a_wire(self):
        effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                     trim_db=0.1)
        self.assertEqual(effect._trim.mix, 0.0)
        effect = audioeffects.create("LowPass", source(), SAMPLE_RATE,
                                     trim_db=0.3)
        self.assertEqual(effect._trim.mix, 1.0)


class TheDeclaredTailIsTheMeasuredOne(unittest.TestCase):
    """`TAIL_SAMPLES` is a ceiling over the whole span, measured at the
    worst setting the macros offer. Here it is held to the tail at a setting
    cheap enough to render inside a unit test, with the fault that would
    make the declaration a wrong number rather than a spare one."""

    def tail_after(self, frames, **options):
        sample = burst_then_silence(burst=9600, seconds=2)
        effect = audioeffects.create("LowPass", sample, SAMPLE_RATE,
                                     **options)
        values = pull_ints(effect.output, frames)
        last = 0
        for index in range(len(values)):
            if values[index]:
                last = index // 2
        return max(0, last - 9600)

    def test_a_measured_tail_fits_inside_the_declaration(self):
        measured = self.tail_after(SAMPLE_RATE * 2, frequency=100.0, q=16.0)
        self.assertGreater(measured, 0)
        self.assertLessEqual(measured, lowpass.LowPass.TAIL_SAMPLES)

    def test_a_declaration_short_of_the_measurement_is_red(self):
        """The planted fault, TAIL's own shape: the DSP untouched and the
        declared number wrong. A subclass that declares a 1024-sample tail
        renders byte-identical audio and must still fail the comparison the
        test above passes, or that comparison is a tripwire."""

        class ShortTailLowPass(lowpass.LowPass):
            TAIL_SAMPLES = 1024

        sample = burst_then_silence(burst=9600, seconds=2)
        clean = audioeffects.create("LowPass", sample, SAMPLE_RATE,
                                    frequency=100.0, q=16.0)
        clean_pcm = bytes(pull_ints(clean.output, SAMPLE_RATE * 2))

        sample = burst_then_silence(burst=9600, seconds=2)
        faulted = ShortTailLowPass.create(sample, SAMPLE_RATE,
                                          frequency=100.0, q=16.0)
        faulted_pcm = bytes(pull_ints(faulted.output, SAMPLE_RATE * 2))

        # The audio is the same; only the declaration moved.
        self.assertEqual(clean_pcm, faulted_pcm)
        measured = self.tail_after(SAMPLE_RATE * 2, frequency=100.0, q=16.0)
        self.assertLessEqual(measured, clean.tail_samples)
        self.assertGreater(measured, faulted.tail_samples)

    def test_the_tail_is_longer_at_a_lower_corner(self):
        wide = self.tail_after(SAMPLE_RATE * 2, frequency=1000.0)
        deep = self.tail_after(SAMPLE_RATE * 2, frequency=100.0, q=16.0)
        self.assertGreater(deep, wide * 10)


if __name__ == "__main__":
    unittest.main()
