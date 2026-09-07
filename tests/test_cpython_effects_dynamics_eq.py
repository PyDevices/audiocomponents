"""What the dynamics and EQ classes do to a signal today.

Where a bell lands, what a corner costs, whether lookahead catches the
transient and whether the compressor compresses - measured, not
rendered. Several of these pin engine fixes at the library level as
well, and those live on in the node's own tests, not here.

Retired by the effects program's **phase 2 - dynamics and EQ**. Every
assertion here is written against a surface that phase replaces, so when
its classes have been rebuilt - each carrying its own invariant and
planted-fault tests - this module is deleted whole and nothing else in the
suite moves. Until then the contract-level tests over `audioeffects.ALL` in
`test_cpython_effects_library.py` hold the catalogue, and these hold the
character.

Covers `ParametricEQ`, `GraphicEQ`, `LowPass`, `HighPass`, `Compressor`,
`MultibandCompressor` and `Limiter`.
"""

import math
import os
import sys
import unittest
from array import array

import audiocore
import audioeffects
import audiofilters
import synthio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import (SAMPLE_RATE, peak, source,  # noqa: E402
                             tone_gain_db)


class DynamicsAndEQTest(unittest.TestCase):
    def test_a_bell_lands_where_it_was_asked_for(self):
        # Pins both engine fixes at the library level. A peaking bell is
        # only usable once PEAKING_EQ computes b2 with the RBJ sign, and it
        # only lands on its own center once a stereo Filter stops sharing
        # one biquad state between the channels - with that sharing the
        # recursion advances twice per frame and every filter sits an
        # octave high. Measured, not merely rendered.
        for hz, expected in ((1000.0, 6.0), (250.0, 6.0)):
            at_center = tone_gain_db(
                hz, lambda s: audioeffects.ParametricEQ(
                    s, bands=[(hz, expected, 2.0)]).output)
            self.assertAlmostEqual(at_center, expected, delta=0.4,
                                   msg="bell at %g Hz" % hz)
            # Two octaves up the bell is over; a shared state would put the
            # boost here instead.
            away = tone_gain_db(
                hz * 4.0, lambda s: audioeffects.ParametricEQ(
                    s, bands=[(hz, expected, 2.0)]).output)
            self.assertLess(abs(away), 0.5, "bell at %g Hz leaks" % hz)

    def test_a_cut_and_a_boost_cost_the_same(self):
        # The old ParametricEQ synthesized boosts from Splitter branches and
        # capped them at three; cuts were notch sections. Now both are one
        # biquad in one cascade, so ten boosts build as readily as ten cuts.
        boosts = audioeffects.GraphicEQ(source(), gains_db=(6.0,) * 10)
        self.assertEqual(len(boosts.biquads), 10)
        self.assertFalse(hasattr(boosts, "splitter"))
        self.assertGreater(peak(boosts.output, 8), 0.001)

    def test_an_eq_with_nothing_to_do_is_a_wire(self):
        src = source()
        flat = audioeffects.GraphicEQ(src, gains_db=(0.0,) * 10)
        self.assertEqual(flat.biquads, [])
        self.assertIs(flat.output, src)

    def test_a_filter_above_nyquist_is_refused(self):
        # Silently folded coefficients used to be unreachable because every
        # frequency was halved on the way in.
        with self.assertRaises(ValueError):
            audioeffects.LowPass(source(), frequency=SAMPLE_RATE * 0.75)

    def test_a_filter_sits_at_its_corner_across_the_whole_band(self):
        # Nothing pinned this, which is how the biquads got away with being
        # unusable at both ends of the band for as long as they were. Q 0.707
        # is -3.01 dB at the corner by definition, so the assertion needs no
        # reference implementation to compare against.
        for hz in (50.0, 100.0, 200.0, 400.0, 1000.0, 4000.0, 12000.0,
                   18000.0, 22000.0):
            for name in ("LowPass", "HighPass"):
                with self.subTest(filter=name, hz=hz):
                    at_corner = tone_gain_db(
                        hz, lambda s, n=name, f=hz:
                        getattr(audioeffects, n)(s, frequency=f).output)
                    self.assertAlmostEqual(at_corner, -3.01, delta=0.25)

    def test_a_low_filter_passes_what_it_should_and_stops_what_it_should(self):
        # The failure this replaces was silent and total: coefficients in Q15
        # quantize to nonsense below a few hundred hertz, and a LowPass at
        # 100 Hz returned silence while a HighPass at 30 Hz returned about
        # 21 dB of noise. See docs/upstream-diff.md.
        passband = tone_gain_db(
            25.0, lambda s: audioeffects.LowPass(s, frequency=100.0).output)
        self.assertAlmostEqual(passband, 0.0, delta=0.25)
        stopband = tone_gain_db(
            800.0, lambda s: audioeffects.LowPass(s, frequency=100.0).output)
        self.assertLess(stopband, -30.0)
        for hz in (30.0, 60.0):
            with self.subTest(hz=hz):
                passband = tone_gain_db(
                    hz * 8.0,
                    lambda s, f=hz: audioeffects.HighPass(s, frequency=f).output)
                self.assertAlmostEqual(passband, 0.0, delta=0.25)

    def test_a_low_shelf_lifts_its_shelf_and_not_the_whole_band(self):
        # An 80 Hz LOW_SHELF asked for +1.5 dB used to lift everything below
        # it by +13.4 - the coefficients had nowhere near enough resolution to
        # describe a gentle shelf that low.
        def shelf(source_sample):
            node = audiofilters.Filter(
                filter=synthio.Biquad(
                    synthio.FilterMode.LOW_SHELF, 80.0, Q=0.707,
                    A=audioeffects._core.db_to_amplitude(1.5)),
                **audioeffects._core.pcm())
            node.play(source_sample)
            return node

        self.assertAlmostEqual(tone_gain_db(20.0, shelf), 1.5, delta=0.25)
        self.assertAlmostEqual(tone_gain_db(2000.0, shelf), 0.0, delta=0.25)

    def test_every_graphic_eq_band_lands_on_its_own_iso_centre(self):
        # The bottom three were the visible casualty of the Q15 floor: a +6 dB
        # request read +12.14, +6.96 and +3.07 dB at 31.5, 63 and 125 Hz.
        for index, band in enumerate(audioeffects.eq.ISO_BANDS):
            gains = [0.0] * len(audioeffects.eq.ISO_BANDS)
            gains[index] = 6.0
            with self.subTest(band=band):
                self.assertAlmostEqual(
                    tone_gain_db(band, lambda s, g=gains:
                                 audioeffects.GraphicEQ(s, g).output),
                    6.0, delta=0.25)

    def test_the_multiband_bands_add_back_up_to_a_wire(self):
        # Below every threshold none of the three compressors is doing
        # anything, so what comes out is purely the crossover sum.
        def idle(source_sample):
            return audioeffects.MultibandCompressor(
                source_sample, thresholds_db=(6.0, 6.0, 6.0)).output

        for hz in (40.0, 100.0, 200.0, 1000.0, 2000.0, 8000.0):
            with self.subTest(hz=hz):
                self.assertAlmostEqual(tone_gain_db(hz, idle), 0.0, delta=0.4)

    def test_the_compressor_actually_compresses(self):
        # Not just "it renders". The comparison is against a Compressor whose
        # threshold sits above the signal, so both sides are the same node
        # pulling the same blocks and only the gain computer differs.
        idle = audioeffects.Compressor(source(), threshold_db=6.0, ratio=12.0)
        working = audioeffects.Compressor(source(), threshold_db=-36.0,
                                          ratio=12.0, character="fet")
        self.assertLess(peak(working.output, 8, skip=4),
                        peak(idle.output, 8, skip=4) * 0.75)

    def test_lookahead_stops_a_limiter_overshooting_the_transient(self):
        # Without it the gain only starts coming down once the peak has
        # already been through, so the first cycle of every transient goes
        # over the ceiling. With it the detector is ahead of the audio.
        def peak_over(lookahead_ms):
            values = array("h")
            for frame in range(24000):
                loud = 1200 <= frame < 6000
                value = 32000 if loud and frame % 2 else (
                    -32000 if loud else 0)
                values.append(value)
                values.append(value)
            source = audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                                         channel_count=2)
            limiter = audioeffects.Limiter(source, ceiling_db=-12.0,
                                           release_ms=60.0,
                                           lookahead_ms=lookahead_ms)
            return peak(limiter.output, 60)

        ceiling = 10.0 ** (-12.0 / 20.0)
        self.assertGreater(peak_over(0.0), ceiling * 1.5)
        self.assertLess(peak_over(5.0), ceiling * 1.2)

    def test_true_peak_sees_the_level_between_the_samples(self):
        # A quarter-rate sine offset by 45 degrees puts every sample at
        # -3 dBFS and every actual peak, halfway between two of them, at 0.
        # A sample-peak detector cannot see that at all.
        def reduction(true_peak):
            values = array("h")
            for frame in range(12000):
                value = int(32767.0 * math.sin(
                    math.pi * frame / 2.0 + math.pi / 4.0))
                values.append(value)
                values.append(value)
            source = audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                                         channel_count=2)
            limiter = audioeffects.Limiter(source, ceiling_db=-2.0,
                                           true_peak=true_peak)
            for _ in range(20):
                audiocore.get_buffer(limiter.output)
            return limiter.node.gain_reduction_db()

        self.assertEqual(reduction(False), 0.0)
        self.assertLess(reduction(True), -0.3)

    def test_the_new_dynamics_options_are_off_by_default(self):
        # Everything built before this phase has to render exactly as it did,
        # which is why both are opt-in rather than sensible defaults.
        plain = audioeffects.Limiter(source())
        self.assertEqual(plain.macro(2), 0.0)
        self.assertLess(plain.macro(3), 0.5)


if __name__ == "__main__":
    unittest.main()
