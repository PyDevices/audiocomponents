"""`HighPass`'s own invariant and planted-fault tests.

The class's Tier 2 traits are measured in the evidence pack with the kit;
what is here is the subset a rebuild must not be allowed to regress
silently, each one paired with a fault that turns it red. A checker that has
only ever passed has not been shown to work, so no assertion below stands
without its faulted twin.

The one old-surface trait this replaces - the `HighPass` leg of
`test_cpython_effects_dynamics_eq.py`'s
`..._sits_at_its_corner_across_the_whole_band` at 22 kHz, outside the frozen
span - is retired in the same commit, in that file. `CornerTest` below walks
the whole of the span that replaced it.

Numpy-free, like `tests/support/effects_measure`: the response readings are
computed from each section's own live `coefficients`, so they measure the
filter the class actually built rather than a re-derivation of RBJ beside
it. The two readings that cannot be taken that way - the DC residual and the
tail - render audio.
"""

import array
import cmath
import math
import os
import sys
import unittest

import audiocore
import audiofilters
import synthio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import SAMPLE_RATE, source        # noqa: E402

from audioeffects import _component                    # noqa: E402
from audioeffects import highpass              # noqa: E402

#: The subject is named directly. `HighPass` has come home to
#: `audioeffects/highpass.py`; `rebuilt.ADOPTED` no longer lists it. These
#: tests still import the home module so a planted-fault subclass is
#: measured against this file, not only `create()`.

#: `_component` reads `VENDOR` off the module a class is *defined* in, not
#: off the one its base came from, so a planted-fault subclass here needs one
#: or the metadata check refuses it before it can be measured.
VENDOR = "PyDevices"

FLAT_Q = highpass.FLAT_Q


# -- reading the filter the class built ------------------------------------

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


def dc_gain(effect):
    """|H(z=1)| of the whole cascade, linear. A high-pass's whole job is
    that this is zero; `response_db` would take the log of it."""
    gain = 1.0
    for node in effect._nodes:
        if node.mix == 0.0:
            continue
        b0, b1, b2, a1, a2 = node.coefficients
        gain *= abs((b0 + b1 + b2) / (1.0 + a1 + a2))
    return gain


def warped(hz, rate=SAMPLE_RATE):
    """T4's axis: `f_a = (F_s/pi) * tan(pi f / F_s)`, and its inverse."""
    return (rate / math.pi) * math.tan(math.pi * hz / rate)


def unwarped(f_a, rate=SAMPLE_RATE):
    return (rate / math.pi) * math.atan(math.pi * f_a / rate)


# -- rendering -------------------------------------------------------------

def tone_then_silence(hz=440.0, rate=SAMPLE_RATE, tone=0.09, seconds=3.0,
                      level=12000, channels=2):
    """The dossier's A3 probe: a burst, then digital silence *inside the
    source*, so a pull can never run off the end of it."""
    values = array.array("h")
    tone_frames = int(tone * rate)
    for frame in range(tone_frames):
        value = int(round(level * math.sin(2.0 * math.pi * hz * frame
                                           / rate)))
        for _ in range(channels):
            values.append(value)
    values.extend(array.array("h", bytes(2 * int(seconds * rate) * channels)))
    return values


def pull_ints(node, frames, channels=2):
    """Exactly `frames` frames, never one more. A pull past the end of the
    source measures the source's padding rather than the node, which is how
    the held-DC defect stayed hidden for as long as it did (dossier A3)."""
    want = frames * channels
    out = array.array("h")
    while len(out) < want:
        data = memoryview(bytes(audiocore.get_buffer(node)[1])).cast("h")
        if not len(data):
            break
        out.extend(data)
    return out[:want]


def raw(values, rate=SAMPLE_RATE, channels=2):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


# -- the surface -----------------------------------------------------------

class TheSurface(unittest.TestCase):
    def test_the_five_macros_and_six_patches_are_the_frozen_ones(self):
        cls = highpass.HighPass
        self.assertIs(cls, highpass.HighPass)
        self.assertEqual(cls.MACRO_LABELS,
                         ("Frequency", "Resonance", "Slope", "Mix", "Trim"))
        self.assertEqual(len(cls.PATCHES), 6)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TIER, _component.AUDIOIF)
        self.assertEqual(cls.REQUIRES, ("audiobiquad",))

    def test_patch_zero_is_the_constructors_own_defaults(self):
        # Within one step of the 0-127 grid: Q 0.7071 lands on 13/127.
        built = highpass.HighPass(source())
        seeded = list(built._macros)
        built.program_change(0)
        for index, (was, now) in enumerate(zip(seeded, built._macros)):
            self.assertAlmostEqual(was, now, delta=1.0 / 127.0,
                                   msg="macro %d" % index)

    def test_every_patch_is_reachable_and_moves_the_filter(self):
        built = highpass.HighPass(source())
        seen = set()
        for index in range(len(highpass.HighPass.PATCHES)):
            built.program_change(index)
            self.assertEqual(built.patch_index, index)
            seen.add(round(built.macro(0), 3))
        self.assertEqual(len(seen), len(highpass.HighPass.PATCHES))


# -- T1: the transmission zero at DC --------------------------------------

class TheZeroAtDCIsExact(unittest.TestCase):
    """The one thing a high-pass does that a low-pass cannot."""

    def rendered_residual(self, node_factory, blocks=287, frame_block=512):
        values = tone_then_silence()
        node = node_factory()
        node.play(raw(values))
        data = pull_ints(node, blocks * frame_block)
        tail = data[-frame_block * 2:]
        return max(abs(value) for value in tail)

    def test_the_settled_output_is_bit_exactly_zero(self):
        for hz, q, slope in ((10.0, FLAT_Q, 12), (20.0, FLAT_Q, 12),
                             (30.0, 16.0, 24), (100.0, FLAT_Q, 12)):
            with self.subTest(hz=hz, q=q, slope=slope):
                built = highpass.HighPass(source(), frequency=hz, q=q,
                                              slope=slope)
                self.assertEqual(
                    self.rendered_residual(lambda b=built: b.output), 0)

    def test_the_ported_biquad_the_class_replaced_is_red(self):
        # The planted fault of the same kind: the node the dossier's D1
        # moved off. Same probe, same 287 blocks, same corners - and it
        # parks on a residual and holds it.
        residuals = {}
        for hz in (10.0, 20.0, 30.0):
            def ported(f=hz):
                node = audiofilters.Filter(
                    filter=synthio.Biquad(synthio.FilterMode.HIGH_PASS, f,
                                          Q=FLAT_Q),
                    mix=1.0, sample_rate=SAMPLE_RATE, channel_count=2,
                    bits_per_sample=16, samples_signed=True,
                    buffer_size=2048)
                return node
            residuals[hz] = self.rendered_residual(ported)
        self.assertGreaterEqual(residuals[10.0], 8, residuals)
        self.assertGreater(residuals[10.0], residuals[30.0])
        for hz, held in residuals.items():
            self.assertGreater(held, 0, "%g Hz should be red: %r"
                               % (hz, residuals))

    def test_the_probe_run_past_its_source_is_the_measurements_own_fault(self):
        # `audiofilters/Filter.c` memsets its output when the source is
        # exhausted, without running the biquads at all, so the *same*
        # ported node reads exact zero if the probe runs long. That is why
        # `pull_ints` counts frames.
        def ported():
            return audiofilters.Filter(
                filter=synthio.Biquad(synthio.FilterMode.HIGH_PASS, 10.0,
                                      Q=FLAT_Q),
                mix=1.0, sample_rate=SAMPLE_RATE, channel_count=2,
                bits_per_sample=16, samples_signed=True, buffer_size=2048)
        self.assertGreater(self.rendered_residual(ported), 0)
        self.assertEqual(self.rendered_residual(ported, blocks=340), 0)

    def test_the_cascades_gain_at_dc_is_zero_at_every_setting(self):
        for hz in (10.0, 30.0, 300.0, 2000.0, 20000.0):
            for slope in (12, 24):
                with self.subTest(hz=hz, slope=slope):
                    built = highpass.HighPass(source(), frequency=hz,
                                                  slope=slope, trim_db=6.0)
                    self.assertLess(dc_gain(built), 1e-12)

    def test_a_low_shelf_where_the_trim_is_would_be_red(self):
        # The trim must not have gain at DC: a LOW_SHELF at the same corner
        # would put one there, and the cascade's DC gain would stop being
        # zero if the trim ran ahead of the poles. Both halves shown.
        built = highpass.HighPass(source(), frequency=30.0, trim_db=6.0)
        self.assertLess(dc_gain(built), 1e-12)
        shelf = built._trim
        shelf.mode = 5                       # audiobiquad.LOW_SHELF
        b0, b1, b2, a1, a2 = shelf.coefficients
        self.assertGreater(abs((b0 + b1 + b2) / (1.0 + a1 + a2)), 1.5)


# -- T2: the corner gain is the resonance ---------------------------------

class CornerTest(unittest.TestCase):
    """|H(f0)| = Q, at both slopes, over the whole frozen span and at three
    rates. This is what replaces the retired 22 kHz row."""

    def corner_db(self, hz, q, slope, rate=SAMPLE_RATE):
        built = highpass.HighPass(source(rate=rate), frequency=hz, q=q,
                                      slope=slope, sample_rate=rate)
        return response_db(built, built.macro(0), rate)

    def test_the_corner_gain_reads_q_at_both_slopes(self):
        for q in (0.5, FLAT_Q, 1.0, 2.0, 4.0, 8.0, 16.0):
            for slope in (12, 24):
                with self.subTest(q=q, slope=slope):
                    self.assertAlmostEqual(
                        self.corner_db(1000.0, q, slope),
                        20.0 * math.log10(q), delta=0.05)

    def test_the_corner_sits_at_minus_three_across_the_whole_span(self):
        for hz in (10.0, 50.0, 100.0, 200.0, 400.0, 1000.0, 4000.0,
                   12000.0, 18000.0, 20000.0):
            for slope in (12, 24):
                with self.subTest(hz=hz, slope=slope):
                    self.assertAlmostEqual(self.corner_db(hz, FLAT_Q, slope),
                                           -3.01, delta=0.05)

    def test_the_corner_gain_is_q_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            for slope in (12, 24):
                with self.subTest(rate=rate, slope=slope):
                    self.assertAlmostEqual(
                        self.corner_db(1000.0, 4.0, slope, rate),
                        20.0 * math.log10(4.0), delta=0.05)

    def test_scaling_both_butterworth_qs_is_red(self):
        # The fault of the same kind: put the resonance on both sections of
        # the steep pair and the knob squares. Resonance 2 would stand
        # +12 dB up instead of +6.
        built = highpass.HighPass(source(), frequency=1000.0, q=2.0,
                                      slope=24)
        self.assertAlmostEqual(response_db(built, built.macro(0)), 6.02,
                               delta=0.05)
        built._pole_one.Q = highpass.BUTTERWORTH_LOW * 2.0 / FLAT_Q
        self.assertGreater(response_db(built, built.macro(0)), 11.0)


# -- T3: the skirt --------------------------------------------------------

class TheSkirtIsTwelveDecibelsAnOctave(unittest.TestCase):
    def skirt(self, hz, slope):
        built = highpass.HighPass(source(), frequency=hz, slope=slope)
        corner = built.macro(0)
        low = response_db(built, corner / 8.0)
        high = response_db(built, corner / 4.0)
        return high, high - low

    def test_twelve_and_twenty_four_decibels_an_octave(self):
        for hz in (20.0, 160.0, 640.0, 1280.0, 3200.0):
            with self.subTest(hz=hz):
                quarter, per_octave = self.skirt(hz, 12)
                self.assertAlmostEqual(quarter, -24.10, delta=0.30)
                self.assertAlmostEqual(per_octave, 12.03, delta=0.30)
                quarter, per_octave = self.skirt(hz, 24)
                self.assertAlmostEqual(quarter, -48.20, delta=0.60)
                self.assertAlmostEqual(per_octave, 24.06, delta=0.60)

    def test_the_second_section_left_as_a_wire_is_red(self):
        # The fault of the same kind: a Slope switch that does not switch.
        built = highpass.HighPass(source(), frequency=640.0, slope=24)
        corner = built.macro(0)
        self.assertAlmostEqual(response_db(built, corner / 4.0), -48.20,
                               delta=0.60)
        built._pole_two.mix = 0.0
        self.assertGreater(response_db(built, corner / 4.0), -30.0)

    def test_nyquist_passes_at_unity(self):
        for hz in (20.0, 1000.0, 20000.0):
            for slope in (12, 24):
                with self.subTest(hz=hz, slope=slope):
                    built = highpass.HighPass(source(), frequency=hz,
                                                  slope=slope)
                    self.assertAlmostEqual(
                        response_db(built, SAMPLE_RATE * 0.48), 0.0,
                        delta=0.10)


# -- T4: one curve on the warped axis -------------------------------------

class TheShapeIsOneCurve(unittest.TestCase):
    RATIOS = (0.125, 0.5, 1.0, 2.0, 8.0)

    def curve(self, hz):
        built = highpass.HighPass(source(), frequency=hz)
        corner = built.macro(0)
        return [response_db(built, unwarped(warped(corner) * ratio))
                for ratio in self.RATIOS]

    def test_the_warped_curve_is_the_same_at_every_corner(self):
        reference = self.curve(31.5)
        for hz in (125.0, 500.0, 1000.0, 2000.0, 4000.0, 16000.0):
            with self.subTest(hz=hz):
                for want, got in zip(reference, self.curve(hz)):
                    self.assertAlmostEqual(want, got, delta=0.05)

    def test_a_corner_moved_fifteen_percent_deforms_it(self):
        # The fault of the same kind: a class whose built corner is not the
        # corner it was asked for. The curve read against the *asked-for*
        # corner is then a different curve.
        reference = self.curve(1000.0)
        built = highpass.HighPass(source(), frequency=1000.0)
        for node in (built._pole_one,):
            node.frequency = 1150.0
        moved = [response_db(built, unwarped(warped(1000.0) * ratio))
                 for ratio in self.RATIOS]
        self.assertGreater(max(abs(a - b) for a, b in zip(reference, moved)),
                           0.5)


# -- Tier 1: the wire, the rate, the trim, the tail -----------------------

class TheBypassIsAWire(unittest.TestCase):
    def rendered(self, effect, frames=4096):
        return bytes(pull_ints(effect.output, frames))

    def test_mix_zero_is_byte_identical_to_the_source(self):
        values = source()
        wet = highpass.HighPass(values, frequency=300.0, mix=0.0)
        dry = pull_ints(source(), 4096)
        self.assertEqual(self.rendered(wet), bytes(dry))

    def test_mix_zero_with_a_trim_asked_for_is_still_a_wire(self):
        wet = highpass.HighPass(source(), frequency=300.0, mix=0.0,
                                    trim_db=9.0, slope=24)
        self.assertEqual(self.rendered(wet), bytes(pull_ints(source(), 4096)))

    def test_a_trace_of_the_wet_path_on_a_bypass_is_red(self):
        # The fault of the same kind: a bypass that is not quite a bypass.
        # 1/256 of the cascade leaking into the blend moves the render by
        # single LSBs and nothing else - the smallest fault of this kind the
        # int16 output can carry, and the check must still see it.
        wet = highpass.HighPass(source(), frequency=300.0, mix=0.0)
        wet._pole_one.mix = 1.0 / 256.0
        self.assertNotEqual(self.rendered(wet),
                            bytes(pull_ints(source(), 4096)))


class TheClassIsRateHonest(unittest.TestCase):
    def test_a_corner_above_nyquist_clamps_rather_than_raising(self):
        # The dossier's section 7 names `set_frequency`'s raise as a defect:
        # the rate-honesty invariant asks a Hz span to clamp at the running
        # rate rather than refuse.
        built = highpass.HighPass(source(), frequency=SAMPLE_RATE * 0.75)
        self.assertLess(built._pole_one.frequency, SAMPLE_RATE * 0.5)
        self.assertGreater(max(abs(v) for v in pull_ints(built.output, 2048)),
                           0)

    def test_the_span_top_clamps_at_a_low_rate(self):
        built = highpass.HighPass(source(rate=22050), frequency=20000.0,
                                      sample_rate=22050)
        self.assertAlmostEqual(built._pole_one.frequency, 22050 * 0.49,
                               delta=1.0)


class TheTrimIsFlat(unittest.TestCase):
    def trim_error(self, db, hz, rate=SAMPLE_RATE):
        built = highpass.HighPass(source(rate=rate), frequency=10.0,
                                      trim_db=db, sample_rate=rate)
        return magnitude_db(built._trim, hz, rate) - db

    def test_the_trim_is_the_gain_it_says_across_the_band(self):
        for rate in (48000, 44100, 22050):
            for db in (-12.0, -6.0, 6.0, 12.0):
                for hz in (50.0, 1000.0, 9000.0):
                    with self.subTest(rate=rate, db=db, hz=hz):
                        self.assertAlmostEqual(self.trim_error(db, hz, rate),
                                               0.0, delta=0.05)

    def test_a_trim_corner_at_the_span_floor_is_red(self):
        # The fault of the same kind: a shelf whose corner is not under the
        # band it is meant to be flat across. Moved to 50 Hz it is 3 dB out
        # at 50 and the class's own lowest corners sit inside its skirt.
        built = highpass.HighPass(source(), frequency=10.0, trim_db=12.0)
        self.assertAlmostEqual(magnitude_db(built._trim, 50.0), 12.0,
                               delta=0.05)
        built._trim.frequency = 50.0
        self.assertLess(magnitude_db(built._trim, 50.0), 11.0)

    def test_a_trim_under_the_floor_is_a_wire(self):
        built = highpass.HighPass(source(), frequency=300.0)
        built.program_change(0)
        self.assertEqual(built._trim.mix, 0.0)


class TheDeclaredTailIsTheMeasuredOne(unittest.TestCase):
    def measured_tail(self, effect, burst=2048, seconds=8.0):
        """Frames from the source going silent to the last non-zero output
        sample. The burst is led with silence because `RawSample` hands its
        buffer back from the beginning, so a burst at frame 0 replays."""
        lead = 2048
        values = array.array("h", bytes(2 * lead * 2))
        for frame in range(burst):
            value = int(round(32000 * math.sin(2.0 * math.pi * 200.0 * frame
                                               / SAMPLE_RATE)))
            values.append(value)
            values.append(value)
        values.extend(array.array("h",
                                  bytes(2 * int(seconds * SAMPLE_RATE) * 2)))
        upstream = raw(values)
        for child in effect._nodes:
            child.play(upstream)
            upstream = child
        frames = lead + burst + int(seconds * SAMPLE_RATE)
        data = pull_ints(effect.output, frames)
        last = 0
        for index in range(len(data) - 1, -1, -1):
            if data[index]:
                last = index // 2
                break
        return max(0, last - (lead + burst))

    def driven_tail(self, effect, f0, drive=None, settle=None):
        """The tail after the resonance has been *driven*, not struck.

        The blind spot the Phase 2 gate audit found: `measured_tail` above
        hits the filter with 2 048 frames of a 200 Hz tone, and a Q-29.6
        pole at 10 Hz never gets near its steady state in 43 ms. This drives
        the corner at full scale until the ring has stopped climbing, then
        releases it, which is where `TAIL_SAMPLES` has to be a ceiling.
        """
        lead = 2048
        drive = drive or int(SAMPLE_RATE * 6.0)
        settle = settle or int(SAMPLE_RATE * 16.0)
        values = array.array("h", bytes(2 * lead * 2))
        for frame in range(drive):
            value = int(round(32767 * math.sin(2.0 * math.pi * f0 * frame
                                               / SAMPLE_RATE)))
            values.append(value)
            values.append(value)
        values.extend(array.array("h", bytes(2 * settle * 2)))
        upstream = raw(values)
        for child in effect._nodes:
            child.play(upstream)
            upstream = child
        data = pull_ints(effect.output, lead + drive + settle)
        last = 0
        for index in range(len(data) - 1, -1, -1):
            if data[index]:
                last = index // 2
                break
        return max(0, last - (lead + drive))

    def test_a_measured_tail_fits_inside_the_declaration(self):
        built = highpass.HighPass(source(), frequency=30.0, q=16.0,
                                      slope=24, trim_db=12.0)
        measured = self.measured_tail(built)
        self.assertGreater(measured, 0)
        self.assertLess(measured, highpass.HighPass.TAIL_SAMPLES)

    def test_the_declaration_covers_the_worst_settings_the_surface_reaches(
            self):
        # Gate audit section 4.1: the declaration was taken from a burst and
        # a driven corner is far longer. 10 Hz / Resonance 16 / 24 dB/oct /
        # +12 dB is the worst cell of
        # `workspace docs/effects-internal/probes/phase2_probes/highpass_sweep.py tail`, 54 cells, and it is
        # at every span's own stop - Frequency 0 is patch 0's own corner.
        built = highpass.HighPass(source(), frequency=10.0, q=16.0,
                                      slope=24, trim_db=12.0)
        measured = self.driven_tail(built, 10.0)
        self.assertGreater(measured, 600000)
        self.assertLess(measured, highpass.HighPass.TAIL_SAMPLES)

    def test_the_declaration_the_pack_shipped_is_red_on_that_run(self):
        # The fault of the same kind, and the one that was really shipped:
        # 305 152 was measured from a 200 ms burst, and this is the same
        # class with that number back in place.
        class BurstDeclaredTail(highpass.HighPass):
            TAIL_SAMPLES = 305152

        built = BurstDeclaredTail(source(), frequency=10.0, q=16.0,
                                  slope=24, trim_db=12.0)
        self.assertGreater(self.driven_tail(built, 10.0), built.tail_samples)

    def test_the_tail_is_longer_at_a_lower_corner(self):
        low = highpass.HighPass(source(), frequency=20.0, q=16.0,
                                    slope=24)
        high = highpass.HighPass(source(), frequency=1000.0, q=16.0,
                                     slope=24)
        self.assertGreater(self.measured_tail(low),
                           self.measured_tail(high))

    def test_a_declaration_short_of_the_measurement_is_red(self):
        # The fault of the same kind: a class that under-declares its tail.
        class ShortTail(highpass.HighPass):
            TAIL_SAMPLES = 1024
        built = ShortTail(source(), frequency=20.0, q=16.0, slope=24)
        self.assertGreater(self.measured_tail(built), built.tail_samples)


class ResetAndDeinitWalkEveryNode(unittest.TestCase):
    def primed_source(self, lead=4096, burst=4096, silence=48000):
        """Silence, a full-scale burst, then silence. The lead matters:
        `RawSample` hands its buffer back from the beginning, so a probe
        whose burst sits at frame 0 replays it after `reset()` and reads
        exactly like a section that was never cleared."""
        values = array.array("h", bytes(2 * lead * 2))
        for frame in range(burst):
            value = int(round(30000 * math.sin(2.0 * math.pi * 200.0 * frame
                                               / SAMPLE_RATE)))
            values.append(value)
            values.append(value)
        values.extend(array.array("h", bytes(2 * silence * 2)))
        return raw(values)

    def test_reset_clears_all_three_sections(self):
        built = highpass.HighPass(self.primed_source(), frequency=20.0,
                                      q=16.0, slope=24, trim_db=6.0)
        pull_ints(built.output, 8192)
        primed = max(abs(v) for v in pull_ints(built.output, 2048))
        self.assertGreater(primed, 0)
        built.reset()
        # The source replays its silent lead, so a cleared cascade can only
        # write zeros; anything left in a section would come out here.
        self.assertEqual(max(abs(v) for v in pull_ints(built.output, 2048)),
                         0)
        self.assertEqual(len(built._nodes), 3)

    def test_a_section_left_uncleared_is_red(self):
        # The fault of the same kind: `reset()` reaching the output node
        # only, which is what `_core.reset()` did (dossier section 7).
        built = highpass.HighPass(self.primed_source(), frequency=20.0,
                                      q=16.0, slope=24, trim_db=6.0)
        pull_ints(built.output, 8192)
        audiocore.reset_buffer(built._trim)      # the tail alone
        built.program_change(0)
        self.assertGreater(max(abs(v) for v in pull_ints(built.output, 2048)),
                           0)

    def test_reset_leaves_the_borrowed_source_rendering(self):
        borrowed = self.primed_source()
        built = highpass.HighPass(borrowed, frequency=20.0, q=16.0,
                                      slope=24)
        pull_ints(built.output, 8192)
        built.reset()
        pull_ints(built.output, 4096)            # past the silent lead
        self.assertGreater(max(abs(v) for v in pull_ints(built.output, 4096)),
                           0)

    def test_deinit_releases_every_node_and_is_idempotent(self):
        built = highpass.HighPass(source(), frequency=300.0)
        nodes = list(built._nodes)
        built.deinit()
        built.deinit()
        for node in nodes:
            self.assertTrue(node._deinited)
        with self.assertRaises(RuntimeError):
            built.output


if __name__ == "__main__":
    unittest.main()
