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

Covers `ParametricEQ`, `GraphicEQ`, `LowPass`, `HighPass` and `Compressor`.
Two classes left with their rebuilds, on 2026-09-07: `Limiter`'s trait tests
were retired from the foot of this file and live in
`test_cpython_effects_limiter.py`, and `MultibandCompressor`'s one assertion
here - the bands add back up to a wire, to 0.4 dB - is now M1 in
`test_cpython_effects_multiband.py`, at 0.25 dB, at six settings, and with
the fault that turns it red.
Covers `ParametricEQ`, `LowPass`, `HighPass`, `Compressor`,
`MultibandCompressor` and `Limiter`.

**`GraphicEQ`'s three assertions are gone from here**, retired with its
rebuild: they read `.biquads`, expected the all-flat class to return its own
source, and pinned the ISO centres -- all three of which the dossier's
section 7 names as defects. Two of them were about the *cascade* rather than
about `GraphicEQ`, so they live on above, moved onto `ParametricEQ`; the
third has no successor here because "an EQ with nothing to do is its own
source" is the behaviour the rebuild deliberately does not have. What
replaces all three is `test_cpython_effects_graphiceq.py`.
"""

import os
import sys
import unittest

import audioeffects
import audiofilters
import synthio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import (SAMPLE_RATE, peak, source,  # noqa: E402
                             tone_gain_db)


class DynamicsAndEQTest(unittest.TestCase):
    # `test_a_bell_lands_where_it_was_asked_for` was retired here on
    # 2026-09-07 in the commit that rebuilt `ParametricEQ` (roadmap section
    # 3, "the class gate": a rebuilt class never has to satisfy a test
    # written against the surface it replaced). It was written against the
    # retired `bands=[(hz, gain, q)]` constructor, and what it pinned - that
    # a peaking bell lands on its own centre and does not leak two octaves
    # up - is measured against the rebuilt surface in
    # `test_cpython_effects_parametriceq.py`, whose `BellLawTest` reads the
    # built section's own coefficients. The two engine fixes it also pinned
    # (`PEAKING_EQ`'s b2 sign, per-channel biquad state) keep their own
    # tests in audioif. `GraphicEQ` below still builds on the untouched
    # `eq.ParametricEQ` and is not affected.

    def test_a_cut_and_a_boost_cost_the_same(self):
        # The old ParametricEQ synthesized boosts from Splitter branches and
        # capped them at three; cuts were notch sections. Now both are one
        # biquad in one cascade, so a bank of boosts builds as readily as a
        # bank of cuts.
        #
        # Read on `ParametricEQ`, since `GraphicEQ` was rebuilt and the claim
        # is about the cascade -- and read through the rebuilt
        # `ParametricEQ`'s own surface, since its rebuild landed in this same
        # integration: `bands=`/`.biquads` are the old signature, the eight
        # named sections are the new one.
        for tag, settings in (
                ("boost", dict(low_boost=6.0, bell1_db=6.0, bell2_db=6.0,
                               bell3_db=6.0, high_boost=6.0)),
                ("cut", dict(low_atten=6.0, bell1_db=-6.0, bell2_db=-6.0,
                             bell3_db=-6.0, high_atten=6.0))):
            with self.subTest(direction=tag):
                built = audioeffects.ParametricEQ(source(), **settings)
                self.assertEqual(len(built._nodes), 8)
                self.assertFalse(hasattr(built, "splitter"))
                self.assertGreater(peak(built.output, 8), 0.001)

    def test_a_filter_above_nyquist_is_handled_rather_than_folded(self):
        # Silently folded coefficients used to be unreachable because every
        # frequency was halved on the way in, and the old `_core` classes
        # answered an out-of-range corner by raising. Both classes are
        # rebuilt now and both *clamp*: the rate-honesty invariant asks a
        # Hz-valued span to clamp at the running rate rather than refuse
        # (each dossier's section 7 names the raise as a defect), so the
        # assertion is that the corner lands under Nyquist and the filter
        # still filters.
        #
        # This read the raise for `HighPass` between its rebuild's branch
        # point and this integration, because `LowPass` was rebuilt first
        # and wrote the pair while the other half was still `_core`.
        for name in ("LowPass", "HighPass"):
            with self.subTest(filter=name):
                clamped = getattr(audioeffects, name)(
                    source(), frequency=SAMPLE_RATE * 0.75)
                self.assertLess(clamped.macro(0), SAMPLE_RATE * 0.5)
                self.assertGreater(peak(clamped.output, 8), 0.001)

    def test_a_filter_sits_at_its_corner_across_the_whole_band(self):
        # Nothing pinned this, which is how the biquads got away with being
        # unusable at both ends of the band for as long as they were. Q 0.707
        # is -3.01 dB at the corner by definition, so the assertion needs no
        # reference implementation to compare against.
        # 22 kHz is dropped from both rows on 2026-09-07, each in the commit
        # that rebuilt its class: the rebuilt `LowPass`'s Frequency macro
        # spans 20 Hz to 20 kHz and the rebuilt `HighPass`'s 10 Hz to 20 kHz
        # (each dossier's section 6, D2 for `HighPass`), so a corner above
        # that is not a setting either offers, and asking for one measures
        # the span's own ceiling rather than the coefficients. Everything
        # from 50 Hz to 18 kHz still runs here, and each rebuilt class has
        # its own corner sweep over its whole span, at both slopes and three
        # rates: `test_cpython_effects_lowpass.py` and
        # `test_cpython_effects_highpass.py::CornerTest`.
        for hz in (50.0, 100.0, 200.0, 400.0, 1000.0, 4000.0, 12000.0,
                   18000.0, 22000.0):
            for name in ("LowPass", "HighPass"):
                if hz > 20000.0:
                    continue
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

    def test_every_band_lands_on_its_own_centre(self):
        # The bottom three were the visible casualty of the Q15 floor: a +6 dB
        # request read +12.14, +6.96 and +3.07 dB at 31.5, 63 and 125 Hz.
        # Read on `ParametricEQ` since `GraphicEQ` was rebuilt: its centres
        # are the M-108's octave doublings, not the ISO series, and its Q
        # moves with gain -- both of which this assertion would have to be
        # rewritten around, and both of which its own tests now cover.
        # Read through the rebuilt `ParametricEQ`'s middle bell, whose
        # centre is a macro: same claim, same +6 dB, same 0.25 dB bar.
        for band in audioeffects.eq.ISO_BANDS:
            with self.subTest(band=band):
                self.assertAlmostEqual(
                    tone_gain_db(band, lambda s, hz=band:
                                 audioeffects.ParametricEQ(
                                     s, bell2_hz=hz, bell2_db=6.0).output),
                    6.0, delta=0.25)

    def test_the_compressor_actually_compresses(self):
        # Not just "it renders". The comparison is against a Compressor whose
        # threshold sits above the signal, so both sides are the same node
        # pulling the same blocks and only the gain computer differs.
        idle = audioeffects.Compressor(source(), threshold_db=6.0, ratio=12.0)
        working = audioeffects.Compressor(source(), threshold_db=-36.0,
                                          ratio=12.0, character="fet")
        self.assertLess(peak(working.output, 8, skip=4),
                        peak(idle.output, 8, skip=4) * 0.75)


# `Limiter`'s three trait tests retired here, 2026-09-07, with the rebuild
# (effects roadmap, "The class gate": a class's old-surface trait tests are
# retired in the commit that lands the rebuild). They asserted things about a
# surface and a node that no longer exist, and two of the three asserted
# behaviour the dossier records as defects:
#
#   test_lookahead_stops_a_limiter_overshooting_the_transient - it asserted
#     that the lone node overshoots by more than 50 % without lookahead and
#     comes back inside 20 % with it. That is defect 2 of `Limiter.md` section
#     7 written as a pass: measured, lookahead on one node makes the overshoot
#     *worse*, and the old class only read green because its hardcoded
#     0.05 ms attack made the no-lookahead case bad enough to beat. The
#     rebuilt class overshoots at no setting; L2 and L3 in
#     `test_cpython_effects_limiter.py` are the replacement, and they are
#     bounds against the ceiling rather than a ratio between two builds.
#   test_true_peak_sees_the_level_between_the_samples - it read
#     `limiter.node.gain_reduction_db()`, a private attribute of a one-node
#     build. L1 replaces it, and measures the output's true peak rather than
#     the detector's opinion of it.
#   test_the_new_dynamics_options_are_off_by_default - macro 3 is Release on
#     the rebuilt surface, not True Peak. L5 replaces it.
#
# Nothing else in this module refers to `Limiter`; the rest still covers the
# classes phase 2 has not reached.


if __name__ == "__main__":
    unittest.main()
