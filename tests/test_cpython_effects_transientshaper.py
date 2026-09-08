"""`TransientShaper`'s own invariant and planted-fault tests (Phase 2).

The class gate asks for these beside the contract-level suite: a fault that
has never been shown to fire is not a check. The full evidence run lives in
`workspace docs/effects-internal/probes/phase2_probes/transientshaper_evidence.py` and takes minutes; this
file is the fast subset a suite can carry, and every assertion here has a
faulted counterpart in the same test.

`workspace docs/effects-internal/evidence/TransientShaper-evidence.md` is the record; the numbers there
come from the driver, not from this file.
"""

import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (os.path.join(ROOT, "lib"), os.path.join(ROOT, "tools"), HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

from audioeffects import transientshaper          # noqa: E402
#: The subject is named directly. `TransientShaper` has come home to
#: `audioeffects/transientshaper.py`; `rebuilt.ADOPTED` no longer lists it.
#: These tests still import the home module so a planted-fault subclass is
#: measured against this file, not only `create()`.
import effect_measurements as kit                         # noqa: E402
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
        self.assertEqual(cls.TIER, "audioif")
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
        # Patch 0 is the grid's nearest point to the defaults, not the
        # defaults themselves - the evidence pack's section 6.
        self.assertAlmostEqual(effect.macro(0), 0.118, delta=0.005)
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


if __name__ == "__main__":
    unittest.main()
