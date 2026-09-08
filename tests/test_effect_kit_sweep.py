"""The sweep driver's battery: a measurement run over the span its trait
quantifies over, not at a point inside it.

`docs/effects-phase2-pattern-revision.md` section 1.1 is what this file
holds `tools/effect_measurements.py:macro_sweep` to. Twenty-eight of the
forty-five clauses an independent refutation pass broke across sixteen
classes broke the same way: the row quantified over a span, the pack
measured one setting inside it, and the setting was chosen after the trait
was frozen.

Every test here carries **both halves**, in the shape
`test_effect_kit.py` uses for the planted faults:

* the deliberately wrong input - the single chosen point, the span narrowed
  away from its stops - which reads **green**; and
* the same measurement swept over the whole span, which reads **red** and
  names the cell it broke at, in the class's own macro units.

A driver that always went red would prove nothing, so the flat-trait control
is asserted as hard as the break.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audioeffects                                             # noqa: E402
import kit_probes as probes                                     # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

RATE = 48000
BAR_DB = 0.5


def gate(source=None, **options):
    """A live `NoiseGate`. The sweep drives it and reads its macros back;
    the units in every cell below are the ones the panel shows."""
    source = source or probes.ArraySource(probes.sine(1000.0, 0.2, -60.0),
                                          rate=RATE)
    return audioeffects.NoiseGate.create(source, RATE, **options)


def deviation_from_attack(effect):
    """A stand-in trait with the shape Phase 2 kept finding: flat where the
    packs measured, and out of tolerance at the macro's own end position.

    `DynamicEQ`'s composite law is this exactly - inside 1 dB at attack
    2 ms, 4.269 dB at the macro's 100 ms end (pattern revision section 1.1).
    The number here is a function of what the class reports for the knob, so
    the sweep has to move the class to find it.
    """
    attack_ms = effect.macro(1)
    return 0.02 + 0.9 * (attack_ms / 1000.0)


class TheSweepRunsTheSpanNotAPoint(unittest.TestCase):

    def setUp(self):
        self.effect = gate()
        self.addCleanup(self.effect.deinit)
        self.seen = []

    def measure_at(self, settings):
        del settings                    # the figure is read off the class
        value = deviation_from_attack(self.effect)
        self.seen.append(round(self.effect.macro(1), 3))
        return {"measurement": "STANDIN", "unit": "dB",
                "values": {"deviation_db": value}, "axes": {},
                "criteria": {"bar_db": BAR_DB},
                "red": [] if abs(value) <= BAR_DB else ["deviation_db"],
                "passed": abs(value) <= BAR_DB}

    def test_the_chosen_point_reads_green(self):
        # The deliberately wrong input: one setting inside the span, chosen
        # after the trait was frozen. This is what the packs did.
        self.effect.set_macro(1, 64)
        result = self.measure_at({1: 64})
        self.assertTrue(result["passed"])
        self.assertLess(result["values"]["deviation_db"], BAR_DB)

    def test_the_same_measurement_swept_over_the_span_is_red(self):
        result = kit.macro_sweep(self.effect, [kit.MacroSpan(1)],
                                 self.measure_at, figure="deviation_db",
                                 bar=BAR_DB, unit="dB")
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["at"], {1: 127.0})
        self.assertTrue(result["values"]["at_a_stop"])
        self.assertGreater(result["values"]["worst"], BAR_DB)
        # And the point it broke at is reported in the class's own units,
        # read back off the instance: Attack's top is 1000 ms.
        self.assertAlmostEqual(result["values"]["at_units"]["Attack"],
                               1000.0, places=3)
        self.assertIn("Attack", result["red"][0])

    def test_the_stops_are_run_first_and_the_midpoint_after(self):
        kit.macro_sweep(self.effect, [kit.MacroSpan(1)], self.measure_at,
                        figure="deviation_db")
        self.assertEqual(len(self.seen), 3)
        self.assertAlmostEqual(self.seen[0], 0.01, places=3)     # low stop
        self.assertAlmostEqual(self.seen[1], 1000.0, places=1)   # high stop
        self.assertLess(self.seen[2], 1000.0)                    # midpoint

    def test_a_span_narrowed_away_from_its_stops_reads_green(self):
        # The second wrong input, and the one a sweep can still get wrong:
        # sweeping a stretch of the knob that does not include the end the
        # trait breaks at. It reads green, which is why `at_a_stop` and the
        # span's own end values travel with every result.
        result = kit.macro_sweep(self.effect, [kit.MacroSpan(1, 60, 68)],
                                 self.measure_at, figure="deviation_db",
                                 bar=BAR_DB)
        self.assertTrue(result["passed"])
        self.assertEqual(result["values"]["spans"][0]["midi"], [60.0, 68.0])
        self.assertLess(result["values"]["spans"][0]["units"][1], 1000.0)

    def test_the_control_a_flat_trait_stays_green_over_the_whole_span(self):
        # The battery's control. A driver that reddened everything would
        # prove nothing about the class.
        flat = lambda settings: {"values": {"deviation_db": 0.01},  # noqa: E731
                                 "measurement": "STANDIN"}
        result = kit.macro_sweep(self.effect, [kit.MacroSpan(1)], flat,
                                 figure="deviation_db", bar=BAR_DB)
        self.assertTrue(result["passed"])
        self.assertEqual(result["values"]["spread"], 0.0)

    def test_two_spans_sweep_the_corners_of_both(self):
        result = kit.macro_sweep(
            self.effect, [kit.MacroSpan(1), kit.MacroSpan("Release")],
            self.measure_at, figure="deviation_db", bar=BAR_DB)
        self.assertEqual(result["values"]["points"], 9)
        # The figure moves with Attack alone, so the worst cell is the first
        # one at Attack's top stop - Release is swept and reported, and the
        # cell says where it stood.
        self.assertEqual(result["values"]["at"][1], 127.0)
        self.assertIn(3, result["values"]["at"])
        self.assertIn("Release", result["values"]["at_units"])
        self.assertEqual([span["label"] for span in
                          result["values"]["spans"]], ["Attack", "Release"])

    def test_the_instance_is_left_where_it_was_found(self):
        before = self.effect.get_macro(1)
        kit.macro_sweep(self.effect, [kit.MacroSpan(1)], self.measure_at,
                        figure="deviation_db")
        self.assertEqual(self.effect.get_macro(1), before)


class TheSweepRefusesWhatIsNotASpan(unittest.TestCase):
    """The refusals. Each returns a plausible number if it is allowed
    through, which is why each raises instead."""

    def setUp(self):
        self.effect = gate()
        self.addCleanup(self.effect.deinit)

    def test_a_span_of_one_point_is_refused(self):
        with self.assertRaises(kit.MeasurementRefused) as caught:
            kit.macro_sweep(self.effect, [kit.MacroSpan(1, 64, 64)],
                            lambda settings: 0.0)
        self.assertIn("that is a point, not a span",
                      str(caught.exception).replace("\n", " "))
        self.assertIn("Attack", str(caught.exception))

    def test_no_span_at_all_is_refused(self):
        with self.assertRaises(kit.MeasurementRefused):
            kit.macro_sweep(self.effect, [], lambda settings: 0.0)

    def test_a_grid_past_the_ceiling_is_refused(self):
        spans = [kit.MacroSpan(index, midpoints=3) for index in range(4)]
        with self.assertRaises(kit.MeasurementRefused) as caught:
            kit.macro_sweep(self.effect, spans, lambda settings: 0.0,
                            max_cells=64)
        self.assertIn("cell ceiling", str(caught.exception).replace(
            "-cell ceiling", " cell ceiling"))

    def test_a_result_with_several_readouts_needs_the_figure_named(self):
        with self.assertRaises(kit.MeasurementRefused):
            kit.macro_sweep(self.effect, [kit.MacroSpan(1)],
                            lambda settings: {"values": {"a": 1.0,
                                                         "b": 2.0}})

    def test_a_macro_the_class_does_not_have_is_an_error(self):
        with self.assertRaises(ValueError):
            kit.macro_sweep(self.effect, [kit.MacroSpan("Wetness")],
                            lambda settings: 0.0)


class TheSweepCarriesARealMeasurement(unittest.TestCase):
    """The driver takes any kit measurement. Here it is LEVEL over a real
    class: `NoiseGate`'s Range knob, on a -20 dBFS tone with Threshold at
    the top of its travel, so the gate is shut and Range is what the level
    reads.

    The span stops at Range 96 rather than 127 on purpose, and the test
    below says why: at the knob's own top the wet render is -80 dB down on a
    -20 dBFS tone, which is silence in int16, and the kit refuses to measure
    a silent render at all."""

    def setUp(self):
        self.pcm = probes.sine(1000.0, 0.5, -20.0, rate=RATE)
        self.dry = probes.render(probes.ArraySource(self.pcm, rate=RATE),
                                 12000, rate=RATE, label="dry")

    def measure_at(self, settings):
        effect = gate(probes.ArraySource(self.pcm, rate=RATE))
        try:
            effect.set_macro(0, 127)        # Threshold 0 dBFS: gate shut
            for index, value in settings.items():
                effect.set_macro(index, value)
            wet = probes.render(effect.output, 12000, rate=RATE, label="wet")
        finally:
            effect.deinit()
        return kit.level(wet, self.dry, tolerance_db=BAR_DB, skip_frames=4800)

    def test_the_wire_end_of_the_knob_reads_green(self):
        # Range 0 is 0 dB of attenuation - the gate shut is a wire - so the
        # chosen point a pack might report is inside LEVEL's bar.
        self.assertTrue(self.measure_at({4: 0})["passed"])

    def test_swept_over_the_knob_level_goes_red_at_the_far_stop(self):
        subject = gate()
        self.addCleanup(subject.deinit)
        result = kit.macro_sweep(
            subject, [kit.MacroSpan(4, 0, 96)], self.measure_at,
            figure=lambda outcome: max(outcome["values"]["rms_db"], key=abs),
            bar=BAR_DB, unit="dB", name="LEVEL over Range")
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["at"], {4: 96.0})
        self.assertTrue(result["values"]["at_a_stop"])
        self.assertAlmostEqual(result["values"]["at_units"]["Range"],
                               -60.472, places=2)
        self.assertLess(result["values"]["worst"], -BAR_DB)
        self.assertEqual(result["values"]["measurement"], "LEVEL")

    def test_the_silence_rule_still_refuses_the_knobs_own_top(self):
        # Not a sweep failure - the kit's own silence rule, reached through
        # the sweep. -80 dB on a -20 dBFS tone is nothing left in int16, and
        # a measurement that read that as a beautiful figure is exactly what
        # `require_signal` exists to stop.
        subject = gate()
        self.addCleanup(subject.deinit)
        with self.assertRaises(kit.SilentRenderError):
            kit.macro_sweep(
                subject, [kit.MacroSpan(4)], self.measure_at,
                figure=lambda outcome: max(outcome["values"]["rms_db"],
                                           key=abs))


if __name__ == "__main__":
    unittest.main()
