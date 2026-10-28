"""`Compressor`'s own planted-fault checks, in the suite.

The class gate asks each rebuilt class for its invariant and planted-fault
tests. `Compressor`'s measurements live in `tools/compressor_evidence.py`,
because they are minutes of rendering; what belongs *here* is the part that
must not rot silently - the three faults the Phase 2 gate audit sent back,
held to the two rules the pattern revision added:

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
import kit_player                                              # noqa: E402
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

    audiodsp v0.6.1 (#129) made the voice at 1.0 exact, and the pin moved
    there on 2026-09-27 (`AUDIODSP_PIN`). So the unity plant is a control
    now, and the fault the row is shown catching is the kit spec's own:
    the dry voice a hair under unity, 32767/32768.
    """

    def _rendered(self, cls=None, channels=2, frames=8192, dry_level=None):
        values = probes.ramp_fs(frames, channels)
        source = audiocore.RawSample(values, sample_rate=RATE,
                                     channel_count=channels)
        effect = (cls or ev.Compressor).create(source, RATE, mix=0.0)
        try:
            self.assertEqual(effect.latency_samples, 0)
            if dry_level is not None:
                effect._mixer.voice[1].level = dry_level
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

    def test_the_dry_voice_at_unity_is_a_wire_since_audiodsp_v0_6_1(self):
        """audiodsp#95's plant, kept as a control now that it cannot fire.

        The wiring this class shipped with before #95 renders byte-exact on
        the floor the pin names. If this ever goes red, the floor has moved
        back under the suite.
        """
        result = self._rendered(ThroughTheDryVoice)
        self.assertTrue(result["passed"], result["red"])
        self.assertEqual(result["values"]["differing_samples"], 0)

    def test_the_wire_goes_red_on_a_one_lsb_dry_path(self):
        """The fault the WIRE row is shown catching: the dry voice at
        32767/32768, inaudible, and the byte compare must still refuse it.
        It has to put the mixer back in the path to be planted at all,
        because Mix 0 no longer runs through one.
        """
        result = self._rendered(ThroughTheDryVoice,
                                dry_level=32767.0 / 32768.0)
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["max_abs_difference_lsb"], 1)
        self.assertGreater(result["values"]["differing_samples"], 0)

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


# -- the stale blocks (audiocomponents#113) ------------------------------

import os                                                       # noqa: E402
import sys                                                      # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
import stale_blocks as stale                                    # noqa: E402

from audioeffects import compressor                             # noqa: E402


class TheBypassComesBackAsBuilt(unittest.TestCase):
    """Mix up from 0 plays nothing from before (audiocomponents#113; decided
    2026-09-28: "fix the stale blocks"). An instance built wet primes its
    mixer voices with the first block of the source; moved to 0 before it
    played, and back up after the input stopped, that block came out 256
    frames later. `_component.Component._rejoin` clears the graph and the
    voices are primed afresh."""

    CLS = compressor.Compressor
    MIX = 13

    def test_the_block_primed_at_construction_is_not_replayed(self):
        for rate in stale.RATES:
            for channels in (2, 1):
                self.assertEqual(stale.first_blip(
                    self.CLS, self.MIX, rate, channels), 0, (rate, channels))
        for patch in sorted(self.CLS.PATCHES):
            self.assertEqual(stale.first_blip(
                self.CLS, self.MIX, patch=patch), 0, patch)

    def test_mix_back_after_silence_plays_nothing(self):
        for channels in (2, 1):
            self.assertEqual(stale.blip(self.CLS, self.MIX, 127, 0,
                                        channels=channels), (0, 0))

    def test_the_old_rejoin_and_a_clear_without_rearming_are_red(self):
        # Only a block primed at construction was ever stale here, and since
        # `LAZY_BUILD` that block is silence: each plant primes the source's
        # first block as the old build did.
        for fault in (stale.EagerStaleRejoin, stale.EagerClearOnlyRejoin):
            self.assertGreater(stale.first_blip(
                stale.planted(self.CLS, fault), self.MIX), 10000)


# -- the lean route after a macro move (audiocomponents#208) -------------

import lifecycle                                                # noqa: E402


def _render(effect, feed_blocks, channels):
    out = bytearray()
    lifecycle._pull_to(effect, out, feed_blocks * 256 * 2 * channels,
                       2 * channels)
    return bytes(out)


class TheLeanRouteFollowsTheMacros(unittest.TestCase):
    """Patch 14 `Compressor - lean` drops the slow stage from the pull
    chain, which is exact only while that stage is a wire (Memory 0, not
    `optical`). A macro move unsets the patch index, and the class used to
    stay on the lean route regardless: Makeup went to the slow stage, out of
    the path, and a Character or Memory that gave the slow stage work was
    never heard. Patch 14 and back to the defaults by macros stayed about
    9,000 LSB off an untouched copy for as long as it played."""

    CLS = compressor.Compressor

    def _pair(self, channels, build_a, build_b, blocks=64):
        values = lifecycle.material_for("loop", RATE, channels)
        feeds = [lifecycle.Feed(values, RATE, channels, "256", loop=True)
                 for _ in range(2)]
        a = build_a(feeds[0].port)
        b = build_b(feeds[1].port)
        try:
            return (_render(a, blocks, channels),
                    _render(b, blocks, channels))
        finally:
            a.deinit()
            b.deinit()

    def test_macros_back_to_patch_0_leave_the_lean_route(self):
        steps = self.CLS.PATCHES[0][1]

        def moved(port):
            effect = self.CLS(port, sample_rate=RATE, patch=14)
            for index, value in enumerate(steps):
                effect.set_macro(index, value)
            return effect

        for channels in (2, 1):
            with self.subTest(channels=channels):
                got, want = self._pair(channels, moved, lambda port: self.CLS(
                    port, sample_rate=RATE, patch=0))
                self.assertEqual(got, want)

    def test_makeup_moved_on_the_lean_route_is_heard(self):
        # Patch 1 has patch 14's settings on the full route, where the slow
        # stage at Memory 0 is a wire. Makeup applied by the other stage
        # rounds differently, 2 LSB apart unmoved and 7 at Makeup 100; a
        # Makeup that never reached the path is thousands.
        def lean(port):
            effect = self.CLS(port, sample_rate=RATE, patch=14)
            effect.set_macro(12, 100)
            return effect

        def full(port):
            effect = self.CLS(port, sample_rate=RATE, patch=1)
            effect.set_macro(12, 100)
            return effect

        got, want = self._pair(2, lean, full)
        got = array("h", got)
        want = array("h", want)
        self.assertLessEqual(
            max(abs(x - y) for x, y in zip(got, want)), 16)

    def test_patch_14_and_back_mid_stream_settles(self):
        # The lifecycle matrix's E6 cell at the defaults: the move lands
        # before pull 12 and the macros go back 2 pulls later. The detector
        # re-attacks, and then the two meet exactly.
        values = lifecycle.material_for("loop", RATE, 2)
        feeds = [lifecycle.Feed(values, RATE, 2, "256", loop=True)
                 for _ in range(2)]
        effect = self.CLS(feeds[0].port, sample_rate=RATE)
        control = self.CLS(feeds[1].port, sample_rate=RATE)
        ctx = lifecycle.Ctx(effect, None)
        out = bytearray()
        cout = bytearray()
        try:
            for k in range(400):
                if k == 12:
                    effect.program_change(14)
                if k == 14:
                    lifecycle.restore(effect, ctx)
                lifecycle._pull_to(effect, out, (k + 1) * 1024, 4)
                lifecycle._pull_to(control, cout, (k + 1) * 1024, 4)
        finally:
            effect.deinit()
            control.deinit()
        tail = 200 * 1024
        self.assertEqual(bytes(out[tail:400 * 1024]),
                         bytes(cout[tail:400 * 1024]))


import kit_ceiling                                               # noqa: E402


class TheCeiling(unittest.TestCase):
    def test_clean_at_the_stated_input_level(self):
        # square is where it rails first: p3 at -3 dBFS.
        self.assertEqual(
            kit_ceiling.stated_level_reds(compressor.Compressor, "square"), [])
        self.assertTrue(kit_ceiling.stated_level_reds(
            compressor.Compressor, "square", db=-3, keys=("p3",)))


def _burst_then_silence(rate=RATE, frames=4096):
    """A loud burst into exact zeros, interleaved stereo."""
    values = array("h", bytes(2 * 2 * frames))
    for frame in range(frames // 2):
        value = 20000 if (frame // 24) % 2 else -20000
        values[2 * frame] = values[2 * frame + 1] = value
    return values


class ThePlayersText(unittest.TestCase):
    def silent_frames_that_sound(self, patch, shift=0):
        """Samples where the input is zero and the output is not; `shift`
        reads the input that many frames ahead, the planted fault."""
        values = _burst_then_silence()
        effect = compressor.Compressor.create(
            audiocore.RawSample(values, sample_rate=RATE, channel_count=2),
            RATE, patch=patch)
        try:
            out = array("h")
            while len(out) < len(values):
                data = audiocore.get_buffer(effect.output)[1]
                data = memoryview(bytes(data)).cast("h")
                if not len(data):
                    break
                out.extend(data)
        finally:
            effect.deinit()
        bad = 0
        for i in range(min(len(values), len(out)) - 2 * shift):
            if values[i + 2 * shift] == 0 and out[i] != 0:
                bad += 1
        return bad

    def test_silence_in_is_silence_out_on_the_same_sample(self):
        for patch in sorted(compressor.Compressor.PATCHES):
            with self.subTest(patch=patch):
                self.assertEqual(self.silent_frames_that_sound(patch), 0)
        # Read the input a frame ahead and the burst's last frame sounds
        # against a zero.
        self.assertGreater(self.silent_frames_that_sound(0, shift=1), 0)

    def test_latency_is_zero_on_every_patch(self):
        self.assertEqual(kit_player.latency_problems(
            compressor.Compressor, RATE), [])
        self.assertTrue(kit_player.latency_problems(
            compressor.Compressor, RATE, delayed=True))

    def test_construction_needs_audiodynamics_and_audioroute(self):
        self.assertEqual(compressor.Compressor.REQUIRES,
                         ("audiodynamics", "audioroute"))
        self.assertEqual(kit_player.missing_module_problems(
            compressor.Compressor, RATE), [])

    def test_every_claim_is_in_the_docstring_and_tested(self):
        kit_player.check_claims(
            self, compressor.__doc__ + " " + compressor.Compressor.__doc__,
            CLAIMS, globals(), "Mix at 0 is your dry signal.")


CLAIMS = (
    ("`Compressor` - compressor characters on a shared palette.",
     ("TheLeanRouteFollowsTheMacros.test_macros_back_to_patch_0_leave_the_"
      "lean_route",)),
    ("Mix at 0 is your dry signal.",
     ("MixZeroIsAWireTest.test_mix_zero_is_a_wire_at_both_channel_counts",
      "MixZeroIsAWireTest.test_the_wire_goes_red_on_a_one_lsb_dry_path")),
    ("**Timing.** Latency is zero at every setting.",
     ("ThePlayersText.test_latency_is_zero_on_every_patch",)),
    ("The gain multiplies the audio, so silence in is silence out on the "
     "same sample.",
     ("ThePlayersText.test_silence_in_is_silence_out_on_the_same_sample",)),
    ("**Levels.** Keep the input under -6 dBFS and the defaults and "
     "patches stay off the rails.",
     ("TheCeiling.test_clean_at_the_stated_input_level",)),
)


if __name__ == "__main__":
    unittest.main()
