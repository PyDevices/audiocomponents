"""`TransientShaper`'s own invariant and planted-fault tests (Phase 2).

The class gate asks for these beside the contract-level suite: a fault that
has never been shown to fire is not a check. The full evidence run takes minutes;
this file is the fast subset a suite can carry, and every assertion here has a
faulted counterpart in the same test.

The evidence pack is the record; the numbers there
come from the driver, not from this file.
"""

import math
import os
import re
import sys
from array import array
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (os.path.join(ROOT, "lib"), os.path.join(ROOT, "tools"), HERE,
             os.path.join(HERE, "support")):
    if path not in sys.path:
        sys.path.insert(0, path)

from audioeffects import transientshaper          # noqa: E402
#: The subject is named directly. `TransientShaper` has come home to
#: `audioeffects/transientshaper.py`; `rebuilt.ADOPTED` no longer lists it.
#: These tests still import the home module so a planted-fault subclass is
#: measured against this file, not only `create()`.
import effect_measurements as kit                         # noqa: E402
from support import kit_ceiling                             # noqa: E402
from support import kit_probes as probes                  # noqa: E402

VENDOR = "PyDevices"
RATE = 48000
ATTACK_UP = 127 * (12.0 + 15.0) / 30.0
SUSTAIN_DOWN = 127 * (-12.0 + 24.0) / 48.0


def _node_override(**overrides):
    base = transientshaper.TransientShaper

    class Faulted(base):
        NAME = base.NAME

        def _build(self, **options):
            base._build(self, **options)
            self._node.set(**overrides)
    return Faulted


class NoPeakHold(transientshaper.TransientShaper):
    """The peak-hold defeated where the macro cannot undo it."""

    NAME = transientshaper.TransientShaper.NAME

    def _apply_macro(self, index, position):
        if index == 4:
            self._node.set(slow_hold_ms=0.0)
            return
        transientshaper.TransientShaper._apply_macro(self, index, position)


def render(pcm, frames, cls=None, macros=None, rate=RATE, channels=2):
    source = probes.ArraySource(pcm, rate=rate, block=256,
                                channels=channels)
    effect = (cls or transientshaper.TransientShaper)(source, sample_rate=rate)
    for index, value in (macros or {}).items():
        effect.set_macro(index, value)
    out = probes.render(effect.output, frames, rate=rate, channels=channels,
                        block=256, probe="probe", class_name="TransientShaper")
    effect.deinit()
    return out


def trace(pcm, frames, **options):
    wet = render(pcm, frames, **options)
    result = kit.gaintrace(wet, kit.Render.from_pcm(pcm, wet.rate,
                                                    wet.channels),
                           hop_ms=1.0, floor_db=-60.0)
    return np.array([np.nan if v is None else v
                     for v in result["values"]["trace_gr_db"]], dtype=float)


def decaying(db_per_s, seconds, hz=220.0, rate=RATE, channels=2):
    import math
    from array import array
    count = int(rate * seconds)
    peak = (10 ** (-6.0 / 20.0)) * 32767
    out = array("h", bytes(2 * count * channels))
    for index in range(count):
        moment = index / rate
        envelope = 10.0 ** (-db_per_s * moment / 20.0)
        rise = min(1.0, moment * 1000.0)
        value = int(max(-32768, min(32767, round(
            peak * envelope * rise * math.sin(2 * math.pi * hz * moment)))))
        for channel in range(channels):
            out[index * channels + channel] = value
    return bytes(memoryview(out).cast("B")), count


class SurfaceTests(unittest.TestCase):
    """The metadata the contract freezes, and the two zeros."""

    def test_the_surface_is_the_dossier_s(self):
        cls = transientshaper.TransientShaper
        self.assertEqual(cls.__module__, "audioeffects.transientshaper")
        self.assertEqual(cls.MACRO_LABELS,
                         ("Attack", "Sustain", "Output", "Attack Speed",
                          "Sustain Hold"))
        self.assertEqual(len(cls.PATCHES), 7)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TAIL_SAMPLES, 0)
        self.assertEqual(cls.TIER, "audiodsp")
        self.assertEqual(cls.REQUIRES, ("audiodynamics",))

    def test_the_class_reads_no_transport(self):
        """`capabilities` is () if and only if the transport is never read,
        so the claim is checked against the source, not only the tuple."""
        source = os.path.join(ROOT, "lib", "audioeffects",
                              "transientshaper.py")
        with open(source) as handle:
            code = [line for line in handle
                    if not line.lstrip().startswith("#")]
        self.assertNotIn("self._transport(", "".join(code))

    def test_patch_0_is_the_constructor_s_defaults_on_the_grid(self):
        effect = transientshaper.TransientShaper(
            probes.ArraySource(probes.silence(1024), rate=RATE, block=256),
            sample_rate=RATE)
        self.assertEqual(effect.patch_index, 0)
        self.assertAlmostEqual(effect.macro(0), 0.0, delta=0.0)
        effect.set_macro(0, 127)
        self.assertIsNone(effect.patch_index)
        effect.program_change(0)
        self.assertEqual(effect.patch_index, 0)
        # Patch 0 is the grid's nearest point to the defaults, and for a
        # BIPOLAR macro the nearest point is now the defaults themselves:
        # MIDI 64 is the centre detent (audiocomponents#87), so Attack comes
        # back at exactly 0 dB rather than the +0.118 the evidence pack's
        # section 6 recorded when 64 meant 64/127 of the span.
        self.assertEqual(effect.macro(0), 0.0)
        effect.deinit()


class InvariantTests(unittest.TestCase):
    """Tier 1, with the fault beside the control."""

    def test_the_defaults_are_a_wire_and_a_hidden_gain_is_not(self):
        pcm = probes.ramp_fs(frames=4096).tobytes()
        clean = render(pcm, 4096)
        control = kit.wire(clean, kit.Render.from_pcm(pcm, RATE, 2))
        self.assertTrue(control["passed"], control["red"])
        self.assertEqual(control["values"]["differing_samples"], 0)

        faulted = render(pcm, 4096, cls=_node_override(makeup_db=0.002))
        result = kit.wire(faulted, kit.Render.from_pcm(pcm, RATE, 2))
        self.assertFalse(result["passed"])
        self.assertGreater(result["values"]["differing_samples"], 0)

    def test_the_tail_is_exactly_zero(self):
        pcm, end = probes.burst_silence(hz=1000.0, on_ms=100.0, total_s=0.5)
        pcm = pcm.tobytes()
        frames = int(RATE * 0.5)
        wet = render(pcm, frames, macros={0: ATTACK_UP, 1: SUSTAIN_DOWN})
        result = kit.tail(wet, burst_end_frame=end, declared_tail_samples=0)
        self.assertTrue(result["passed"], result["red"])
        self.assertIsNone(result["values"]["tail_samples"])
        self.assertEqual(result["values"]["residual_lsb"], 0)


class TraitTests(unittest.TestCase):
    """The three traits whose planted faults are cheap enough to carry."""

    def test_t2_both_sections_act_at_once_and_the_selector_cannot(self):
        pcm, count = decaying(20.0, 0.5)
        for cls, want in ((None, True),
                          (_node_override(transient_dual=False), False)):
            attack = trace(pcm, count, cls=cls, macros={0: ATTACK_UP})
            sustain = trace(pcm, count, cls=cls, macros={1: SUSTAIN_DOWN})
            length = min(len(attack), len(sustain))
            live = ~(np.isnan(attack[:length]) | np.isnan(sustain[:length]))
            overlap = int((live & (attack[:length] > 0.5)
                           & (sustain[:length] < -0.5)).sum())
            self.assertEqual(overlap > 0, want,
                             "overlapping hops: %d" % overlap)

    def test_t4_the_sustain_envelope_holds_and_a_follower_does_not(self):
        depths = {}
        for tag, cls in (("hold", None), ("follower", NoPeakHold)):
            pcm, count = decaying(10.0, 0.5)
            values = trace(pcm, count, cls=cls, macros={1: SUSTAIN_DOWN})
            live = ~np.isnan(values)
            depths[tag] = float((-values[live]).max())
        # The peak-hold opens the differential further on the same note.
        self.assertGreater(depths["hold"], depths["follower"] + 1.0)

    def test_t5_the_rms_detector_settles_where_the_peak_detector_does_not(
            self):
        import math
        from array import array
        count = int(RATE * 0.30)
        peak = (10 ** (-6.0 / 20.0)) * 32767
        out = array("h", bytes(2 * count * 2))
        for index in range(count):
            value = int(round(peak * math.sin(
                2 * math.pi * 1000.0 * index / RATE)))
            out[index * 2] = out[index * 2 + 1] = value
        pcm = bytes(memoryview(out).cast("B"))
        steady = {}
        for tag, cls in (("rms", None),
                         ("peak", _node_override(detector=0.0))):
            values = trace(pcm, count, cls=cls, macros={0: ATTACK_UP})
            steady[tag] = float(values[int(0.150 * 1000)])
        self.assertLess(steady["rms"], 0.5)
        self.assertGreater(steady["peak"], 1.5)




def attack(db):
    return 127 * (db + 15.0) / 30.0


def sustain(db):
    return 127 * (db + 24.0) / 48.0


def output(db):
    return 127 * (db + 22.0) / 28.0


def tone(dbfs, seconds=0.3, hz=1000.0):
    """A held sine at `dbfs`, both channels, from the first frame."""
    count = int(RATE * seconds)
    peak = 10 ** (dbfs / 20.0) * 32767
    out = array("h", bytes(4 * count))
    for index in range(count):
        out[2 * index] = out[2 * index + 1] = int(round(
            peak * math.sin(2 * math.pi * hz * index / RATE)))
    return bytes(memoryview(out).cast("B")), count


class TheClaims(unittest.TestCase):
    """The class docstring's figures that the tests above do not reach."""

    def test_attack_reaches_its_ends_on_a_hit(self):
        pcm, count = tone(-20.0)
        for db in (15.0, -15.0):
            values = trace(pcm, count, macros={0: attack(db)})
            reached = np.nanmax(values) if db > 0 else np.nanmin(values)
            self.assertAlmostEqual(reached, db, delta=0.25)

    def test_quiet_hits_are_shaped_as_hard_as_loud_ones(self):
        macros = {0: attack(12.0), 1: sustain(-12.0)}
        traces = {}
        for dbfs in (-20.0, -30.0, -40.0):
            pcm, count = tone(dbfs)
            traces[dbfs] = trace(pcm, count, macros=dict(macros))
        for dbfs in (-30.0, -40.0):
            spread = np.nanmax(np.abs(traces[dbfs] - traces[-20.0]))
            self.assertLess(spread, 0.5, dbfs)

    def test_output_reaches_plus_six(self):
        pcm, count = tone(-20.0)
        values = trace(pcm, count, macros={2: output(6.0)})
        self.assertAlmostEqual(float(np.nanmedian(values)), 6.0, delta=0.1)

    def test_the_held_note_is_still_lifted_at_100_ms(self):
        pcm, count = tone(-6.0)
        values = trace(pcm, count, macros={0: ATTACK_UP})
        self.assertGreater(float(values[100]), 0.5)
        self.assertLess(float(values[150]), 0.5)

    def test_sustain_runs_out_on_a_slow_decay(self):
        pcm, count = decaying(3.0, 12.0)
        slow = float(np.nanmin(trace(pcm, count, macros={1: sustain(-24.0)})))
        self.assertAlmostEqual(slow, -16.0, delta=1.0)
        pcm, count = decaying(10.0, 3.0)
        fast = float(np.nanmin(trace(pcm, count, macros={1: sustain(-24.0)})))
        self.assertLess(fast, -23.5)

    def test_latency_is_zero(self):
        self.assertEqual(transientshaper.TransientShaper.LATENCY_SAMPLES, 0)
        pcm, count = tone(-20.0, seconds=0.05)
        effect = transientshaper.TransientShaper(
            probes.ArraySource(pcm, rate=RATE, block=256, channels=2),
            sample_rate=RATE)
        self.assertEqual(effect.latency_samples, 0)
        effect.deinit()

    def test_construction_needs_audiodynamics(self):
        cls = transientshaper.TransientShaper
        self.assertEqual(cls.REQUIRES, ("audiodynamics",))
        saved = sys.modules["audiodynamics"]
        sys.modules["audiodynamics"] = None
        try:
            pcm, count = tone(-20.0, seconds=0.01)
            with self.assertRaises(ImportError):
                cls(probes.ArraySource(pcm, rate=RATE, block=256,
                                       channels=2), sample_rate=RATE)
        finally:
            sys.modules["audiodynamics"] = saved


class TheCeiling(unittest.TestCase):
    def test_clean_at_the_stated_input_level(self):
        # square is where it rails first: p1 at -9 dBFS.
        cls = transientshaper.TransientShaper
        self.assertEqual(kit_ceiling.stated_level_reds(cls, "square"), [])
        self.assertTrue(kit_ceiling.stated_level_reds(
            cls, "square", db=-9, keys=("p1",)))


CLAIMS = (
    ("Keep the input under -12 dBFS and the defaults and patches stay "
     "off the rails.",
     ("TheCeiling.test_clean_at_the_stated_input_level",)),
    ("There is no threshold and no ratio: the gain follows the difference "
     "between two envelopes of your own signal, so between -20 and -40 dBFS "
     "a quiet hit is shaped as hard as a loud one, to within 0.5 dB.",
     ("TheClaims.test_quiet_hits_are_shaped_as_hard_as_loud_ones",)),
    ("Attack moves the first few milliseconds of every hit.",
     ("TheClaims.test_attack_reaches_its_ends_on_a_hit",)),
    ("Sustain moves what rings after it, and the two act at once: a "
     "snare can get more stick and less room from one instance.",
     ("TraitTests.test_t2_both_sections_act_at_once_and_the_selector_cannot",)),
    ("Sustain Hold is how long the ring section holds at the peak "
     "before it lets go; held, it digs deeper into the ring than a "
     "plain follower does.",
     ("TraitTests.test_t4_the_sustain_envelope_holds_and_a_follower_does_not",)),
    ("A held note at Attack +12 is still lifted by more than 0.5 dB 100 ms "
     "after the hit, and back within 0.5 dB by 150 ms, since the detector "
     "reads the note's RMS rather than its peaks.",
     ("TheClaims.test_the_held_note_is_still_lifted_at_100_ms",
      "TraitTests.test_t5_the_rms_detector_settles_where_the_peak_detector_"
      "does_not")),
    ("On a slow decay Sustain runs out before its end: on a note fading at "
     "3 dB a second, Sustain -24 reaches about -16 dB.",
     ("TheClaims.test_sustain_runs_out_on_a_slow_decay",)),
    ("Latency is zero at every setting, and so is the tail: silence in is "
     "silence out in the same frame.",
     ("TheClaims.test_latency_is_zero",
      "InvariantTests.test_the_tail_is_exactly_zero")),
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
        doc = (transientshaper.__doc__ + " "
               + transientshaper.TransientShaper.__doc__)
        self.assertEqual(claim_problems(doc), [])
        # The checker can fail: a figure outside a claim, a claim the
        # docstring does not carry, a test that does not exist.
        self.assertTrue(claim_problems(doc + " It reads 12 ms."))
        self.assertTrue(claim_problems(doc.replace("as hard as",
                                                   "harder than")))
        self.assertTrue(claim_problems(
            doc, CLAIMS + (("Latency", ("TheClaims.test_nothing_here",)),)))


KIT_PLANTS = {
    "NoPeakHold": (NoPeakHold, 6),
}


if __name__ == "__main__":
    unittest.main()
