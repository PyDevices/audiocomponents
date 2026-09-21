"""`Compressor`'s own planted-fault checks, in the suite.

The class gate asks each rebuilt class for its invariant and planted-fault
tests. `Compressor`'s measurements live in `tools/compressor_evidence.py`,
because they are minutes of rendering; what belongs *here* is the part that
must not rot silently - the three faults the Phase 2 gate audit sent back,
held to the two rules the pattern revision added
(`docs/effects-phase2-pattern-revision.md` sections 1.2 and 1.3):

* a planted fault must be one the class's own macro grid and shipped
  patches cannot dial, and must not be inert;
* a measurement must go red on the class built as a wire, or it cannot
  fail.

Each check is run a second time against a fault that *should* be refused, so
the battery proves it can fire rather than only that it agrees. The audit's
G3 ruling for this class is what these stand against: F2's fault was never
run, O1's was inert (`compressor.py:331-333` forces `memory =
OPTICAL_MEMORY`), and M5's was the Release macro at 127, which is a knob a
player turns.
"""

import os
import sys
import unittest
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "lib"))

import audiocore                                               # noqa: E402
import kit_faults as faults                                    # noqa: E402
import kit_probes as probes                                    # noqa: E402
import compressor_evidence as ev                               # noqa: E402
from tools import effect_measurements as kit                   # noqa: E402

#: `_component` reads VENDOR off the module a class is *defined* in, and the
#: planted fault below is defined here. Without it the fault would refuse to
#: construct, which is a fault that cannot fail.
VENDOR = "PyDevices"

RATE = 48000
MIX = 13


class ThroughTheDryVoice(ev.Compressor):
    """The wiring this class shipped with before audiodsp#95: Mix 0 routed
    through the mixer's dry voice at level 1.0 instead of handing back the
    borrowed source. Nothing else moves - the levels are the same numbers -
    so the only difference in the render is the mixer's own `level / 32767`
    multiply.
    """

    NAME = 'Compressor'

    def _refresh_output(self):
        if not self._ready:
            return
        if not self._primed:
            self._prime()
        self._output = self._mixer


class MixZeroIsAWireTest(unittest.TestCase):
    """WIRE, on the only probe that can see the fault it is about.

    This class had no byte-compare row at all, and audiodsp#95 is why one is
    needed: a mixer voice at level 1.0 is not unity - upstream's Q15 level
    is `1.0 * 32768` and the kernel divides by 32767 - so the dry voice at
    unity came out one LSB high at every sample from 32736 up. Three of
    16384 on a full-scale ramp, all in the right channel, because a stereo
    voice at pan 0 gets 32767 on the left and 32768 on the right. Nothing
    peaking below -6.02 dBFS reaches the mechanism.
    """

    def _rendered(self, cls=None, channels=2, frames=8192):
        values = probes.ramp_fs(frames, channels)
        source = audiocore.RawSample(values, sample_rate=RATE,
                                     channel_count=channels)
        effect = (cls or ev.Compressor).create(source, RATE, mix=0.0)
        try:
            self.assertEqual(effect.latency_samples, 0)
            wet = probes.render(effect.output, frames, rate=RATE,
                                channels=channels, block=256)
        finally:
            effect.deinit()
        dry = kit.Render(bytes(memoryview(values).cast("B")), RATE, channels)
        return kit.wire(wet, dry, latency_samples=0)

    def test_mix_zero_is_a_wire_at_both_channel_counts(self):
        for channels in (1, 2):
            with self.subTest(channels=channels):
                result = self._rendered(channels=channels)
                self.assertTrue(result["passed"], result["red"])
                self.assertEqual(result["values"]["differing_samples"], 0)

    def test_the_dry_voice_at_unity_is_the_fault_the_wire_catches(self):
        result = self._rendered(ThroughTheDryVoice)
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["max_abs_difference_lsb"], 1)

    def test_the_head_of_the_render_is_not_a_hole(self):
        """The second defect the ramp found: this class opened no level
        gates at all, so a voice waiting for a zero crossing that a ramp
        never offers held its level at 0 - 128 frames of silence at the top
        of every render, at every Mix setting including 1. `_prime` opens
        them on one block of silence now.
        """
        values = probes.ramp_fs(8192)
        source = audiocore.RawSample(values, sample_rate=RATE,
                                     channel_count=2)
        effect = ev.Compressor.create(source, RATE, mix=1.0)
        try:
            wet = probes.render(effect.output, 8192, rate=RATE, channels=2,
                                block=256)
        finally:
            effect.deinit()
        head = array("h")
        head.frombytes(wet.pcm[:512])
        self.assertNotEqual(int(head[0]), 0)
        self.assertEqual([index for index in range(len(head))
                          if head[index] == 0], [])


class CompressorFaultsTest(unittest.TestCase):
    """The three replanted faults, and both checks shown firing."""

    def test_the_optical_memory_fault_is_not_a_knob_position(self):
        """O1's fault, `OPTICAL_MEMORY = 0`, on the character O1 is stated
        on. Nothing on the surface reaches it there, because `_push_slow`
        never reads macro 6 on `optical`."""
        target = ev.state_under("OPTICAL_MEMORY", 0.0,
                                ev.pushed_slow_ratio_on_optical)
        checked = faults.fault_reachability(
            ev.Compressor, target, ev.pushed_slow_ratio_on_optical,
            ev.spied_build, label="O1 - OPTICAL_MEMORY = 0")
        self.assertEqual(1.0, checked["target"])
        self.assertNotEqual(checked["clean"], checked["target"])
        self.assertGreater(checked["checked"], 200)

    def test_the_same_fault_off_the_character_is_refused(self):
        """And the check fires: read off whatever character is set, slow
        ratio 1.0 is shipped patch 1's own state."""
        target = ev.state_under("OPTICAL_MEMORY", 0.0, ev.pushed_slow_ratio)
        with self.assertRaises(faults.FaultReachable):
            faults.fault_reachability(
                ev.Compressor, target, ev.pushed_slow_ratio, ev.spied_build,
                label="O1 - read off whatever character is set")

    def test_the_fet_ratio_fault_is_not_a_knob_position(self):
        """F2's fault, `FET_RATIO_REFERENCE = 1e9`, at the row's own
        operating point."""
        target = ev.state_under("FET_RATIO_REFERENCE", 1e9,
                                ev.pushed_fet_tilt_db)
        checked = faults.fault_reachability(
            ev.Compressor, target, ev.pushed_fet_tilt_db, ev.spied_build,
            label="F2 - FET_RATIO_REFERENCE = 1e9")
        self.assertEqual(0.0, checked["target"])
        self.assertAlmostEqual(4.182916, checked["clean"], places=4)

    def test_the_fet_ratio_fault_read_at_any_ratio_is_refused(self):
        """And the check fires the other way: at patch 0's own ratio the
        clean class applies no tilt either, so the fault is inert."""
        target = ev.state_under("FET_RATIO_REFERENCE", 1e9,
                                ev.pushed_tilt_here)
        with self.assertRaises(faults.FaultInert):
            faults.fault_reachability(
                ev.Compressor, target, ev.pushed_tilt_here, ev.spied_build,
                label="F2 - read at whatever ratio is set")

    def test_the_release_calibration_fault_is_out_of_the_knobs_reach(self):
        """M5's fault, `RELEASE_MEASURED_PER_SET = 100`. The Release macro
        stops at 20 ms, which the class divides by 0.795, so 25.157 ms is
        the fastest release any position can ask for."""
        target = ev.state_under("RELEASE_MEASURED_PER_SET", 100.0,
                                ev.pushed_fast_release_ms)
        checked = faults.fault_reachability(
            ev.Compressor, target, ev.pushed_fast_release_ms, ev.spied_build,
            label="M5 - RELEASE_MEASURED_PER_SET = 100")
        self.assertLess(checked["target"], 25.157)
        self.assertAlmostEqual(75.471698, checked["clean"], places=4)

    def test_a_calibration_a_shipped_patch_already_asks_for_is_refused(self):
        """And the check fires: a "fault" that only pushes what patch 1
        pushes is patch 1."""
        instance = ev.spied_build(ev.Compressor)
        try:
            instance.program_change(1)
            near = ev.pushed_fast_release_ms(instance)
        finally:
            instance.deinit()
        with self.assertRaises(faults.FaultReachable):
            faults.fault_reachability(
                ev.Compressor, near, ev.pushed_fast_release_ms,
                ev.spied_build, label="M5 - what patch 1 asks")

    def test_the_detector_reading_is_red_on_a_wire(self):
        """V3's reading is composite for a reason: `|square - sine|` alone
        is 0.000 dB on a build that reduces nothing, so it cannot fail. The
        pair - with `|sine - pulse|` in 5.99-7.99 - is red on the wire and
        green on the class."""
        base = [(2, 127), (7, 0), (1, ev.macro_for(1, -30.0))]

        def measure(cls):
            with ev.using(cls):
                return ev.detector_reading(3, base, 200.0)

        result = faults.null_build_red(ev.Compressor, measure,
                                       label="V3 - the detector pair")
        self.assertTrue(result["control"]["passed"])
        self.assertFalse(result["null"]["passed"])


if __name__ == "__main__":
    unittest.main()
