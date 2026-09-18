"""The kit's two graph guards, each with its planted fault and its control.

audiocomponents#78 read 70 dB of measurement floor off a wet-branch
instrument that pointed `_output` at a node inside the graph, and blamed the
`Splitter` tap the instrument left unpulled. The tap is innocent - the first
test here is the proof - and the floor came from somewhere else: an
instrument taken off an inner node sits one mixer block EARLIER in the
stream than the class's own output, so it runs off the end of its probe and
reads the class's decay into silence.

So there are two guards and two faults:

    require_whole_graph   a pull path that reads one tap of a Splitter and
                          not another is refused. Fault: `_output` on an
                          inner node. Controls: the class's own output, and
                          the class at Mix 0 where the whole split is
                          routed round and NO tap is read - which is a
                          bypass, not this defect.

    require_live          a render whose tail is silence outlived its probe
                          and is refused. Fault: a probe exactly as long as
                          the render. Control: a probe 256 frames longer.

`Exciter` is the subject because it is the class the issue was found on. The
numbers here are at audioif `3388df4`.
"""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                                # noqa: E402
import audioroute                                               # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects.exciter import Exciter                       # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"
RATE = 48000


class WetOffTheShaper(Exciter):
    """The instrument the build pack and the refutation probe both used:
    `_output` on a node inside the graph, so the Mixer - and with it the dry
    tap - is never pulled."""

    NAME = "Exciter"

    def _prime_if_wet(self):
        Exciter._prime_if_wet(self)
        self._output = self._shaper


def sine(hz, dbfs, frames, rate=RATE, channels=2):
    idx = np.arange(frames)
    v = 10.0 ** (dbfs / 20.0) * np.sin(2.0 * math.pi * hz * idx / rate)
    q = np.clip(np.round(v * 32767.0), -32768, 32767).astype(np.int16)
    return np.repeat(q[:, None], channels, axis=1).reshape(-1).tobytes()


def build(cls, probe, rate=RATE, channels=2, block=256, **options):
    source = probes.ArraySource(probe, rate=rate, channels=channels,
                                block=block)
    return cls.create(source, rate, **options)


class UnreadTapIsHarmlessTest(unittest.TestCase):
    """audiocomponents#78's premise, tested rather than assumed.

    The issue says an unread tap drags the ring and costs the read tap its
    stream. At audioif `3388df4` - which carries audioif#87, the oversized
    block fix - it does not, and the guard below exists for a different
    reason.
    """

    def _ramp(self, frames, channels=2):
        values = np.arange(frames, dtype=np.int64) % 30000
        return np.repeat(values[:, None], channels,
                         axis=1).astype(np.int16).reshape(-1).tobytes()

    def _pull_one_tap(self, block, frames=40000, taps=2, read=1):
        source = probes.ArraySource(self._ramp(frames), rate=RATE, block=block)
        splitter = audioroute.Splitter(source, taps=taps)
        tap = splitter.tap(read)
        pcm = bytearray()
        while len(pcm) < frames * 4:
            _, data = audiocore.get_buffer(tap)
            chunk = bytes(data)
            if not chunk:
                break
            pcm += chunk
        splitter.deinit()
        got = np.frombuffer(bytes(pcm[:frames * 4]), dtype="<i2")[::2]
        return got

    def test_a_tap_nobody_reads_does_not_seam_the_tap_somebody_does(self):
        # A counting ramp: a chunk the ring dropped is a step that is not 1.
        # Every source block size from one sixteenth of the ring to nearly
        # five rings.
        for block in (256, 1024, 8192, 9600, 16384, 40000):
            got = self._pull_one_tap(block)
            steps = np.diff(got.astype(np.int64)) % 30000
            self.assertEqual(int((steps != 1).sum()), 0,
                             "block %d seamed the read tap" % block)

    def test_draining_the_other_tap_changes_no_byte_of_the_wet_read(self):
        # The same claim on the real graph: the wet branch read off the
        # shaper, once with the dry tap read by nobody and once with it
        # drained in lockstep.
        probe = sine(1010.0, -6.0, 24000)
        renders = []
        for drain in (False, True):
            effect = build(WetOffTheShaper, probe, tune=600.0, harmonics=1.0,
                           mix=0.7)
            want, pcm = 24000 * 4, bytearray()
            while len(pcm) < want:
                _, data = audiocore.get_buffer(effect.output)
                chunk = bytes(data)
                if drain:
                    audiocore.get_buffer(effect._dry)
                if not chunk:
                    break
                pcm += chunk
            renders.append(bytes(pcm[:want]))
            effect.deinit()
        self.assertEqual(kit.fnv1a(renders[0]), kit.fnv1a(renders[1]))


class WholeGraphTest(unittest.TestCase):
    """`require_whole_graph` - the fault, and two controls."""

    def test_the_guard_fires_on_a_wet_branch_taken_off_an_inner_node(self):
        probe = sine(1010.0, -6.0, 8000)
        effect = build(WetOffTheShaper, probe, mix=0.7)
        self.addCleanup(effect.deinit)
        with self.assertRaises(kit.StarvedTapError) as caught:
            probes.render(effect, 8000, rate=RATE)
        message = str(caught.exception)
        self.assertIn("tap 0 unread", message)
        self.assertIn("taps read: 1", message)
        self.assertIn("mute_dry", message)

    def test_the_walk_does_not_miss_an_edge_it_has_no_name_for(self):
        # The day this guard landed it read `Bitcrusher`'s wet branch as
        # unread and turned thirteen of its tests red, because the walk knew
        # `_source` and `_sample` and `audiospeed.SpeedChanger` calls its
        # source `source`. A node type names its source whatever it likes,
        # so the walk takes every node-like attribute rather than a list of
        # names. `Bitcrusher` is the case: a Splitter, a hold in front of
        # the shaper, and a dry voice muted to zero. The hold was a
        # SpeedChanger pair until audioif e3b95e7; it is an
        # `audioshaper.SampleHold` now (audioif#97), which also calls its
        # source `source` and is just as nameless to the walk.
        from audioeffects.bitcrusher import Bitcrusher
        probe = sine(1000.0, -12.0, 8000)
        effect = build(Bitcrusher, probe)
        self.addCleanup(effect.deinit)
        names = dict((name, node)
                     for name, node in kit.enumerate_nodes(effect))
        self.assertTrue(any(type(node).__name__ == "SampleHold"
                            for node in names.values()),
                        sorted(names))
        self.assertEqual(kit.unread_taps(effect.output, effect), [])
        probes.render(effect, 8000, rate=RATE)

    def test_the_guard_needs_no_help_from_the_caller(self):
        # Every probe written before #78 renders a bare node. The Splitter
        # is found from the pull path, so those are checked too.
        probe = sine(1010.0, -6.0, 8000)
        effect = build(WetOffTheShaper, probe, mix=0.7)
        self.addCleanup(effect.deinit)
        self.assertEqual(kit.unread_taps(effect.output), [("a Splitter", 0, (1,))])
        with self.assertRaises(kit.StarvedTapError):
            probes.render(effect.output, 8000, rate=RATE)

    def test_the_guard_is_quiet_on_the_class_s_own_output(self):
        # The control that must pass: the same class, the same probe, read
        # the way the class is meant to be read.
        probe = sine(1010.0, -6.0, 8000)
        effect = build(Exciter, probe, mix=0.7)
        self.addCleanup(effect.deinit)
        rendered = probes.render(effect, 8000, rate=RATE)
        self.assertEqual(kit.unread_taps(effect.output, effect), [])
        kit.require_signal(rendered)

    def test_a_split_nobody_reads_at_all_is_a_bypass_and_not_this_defect(self):
        # The second control, and the one that keeps the guard from being a
        # tripwire: at Mix 0 the class routes round the whole split and its
        # output is the borrowed source. No tap is read, the split is even,
        # and a WIRE render must not be refused.
        probe = sine(1010.0, -6.0, 8000)
        effect = build(Exciter, probe, mix=0.0)
        self.addCleanup(effect.deinit)
        self.assertIs(effect.output, effect._source)
        self.assertEqual(kit.unread_taps(effect.output, effect), [])
        probes.render(effect, 8000, rate=RATE)

    def test_the_render_can_be_asked_for_the_defect_on_purpose(self):
        probe = sine(1010.0, -6.0, 8000)
        effect = build(WetOffTheShaper, probe, mix=0.7)
        self.addCleanup(effect.deinit)
        rendered = probes.render(effect.output, 8000, rate=RATE,
                                 effect=effect, allow_starved_taps=True)
        kit.require_signal(rendered)


class MuteDryTest(unittest.TestCase):
    """`mute_dry` - the supported wet-branch instrument."""

    def test_muting_the_dry_voice_leaves_no_tap_unread(self):
        probe = sine(1010.0, -6.0, 8000)
        effect = build(Exciter, probe, mix=0.7)
        self.addCleanup(effect.deinit)
        muted = kit.mute_dry(effect)
        # `(mixer, index, level_before)` since the reach moved in from the
        # tests-side wrapper (audiocomponents#81).
        self.assertEqual([index for _, index, _ in muted], [0])
        self.assertEqual([mixer for mixer, _, _ in muted], [effect._blend])
        self.assertEqual(effect._blend.voice[0].level, 0.0)
        self.assertEqual(kit.unread_taps(effect.output, effect), [])

    def test_the_wet_branch_is_not_the_mixed_output(self):
        # A wet instrument that reads the same as the mixed output is not a
        # wet instrument.
        probe = sine(1010.0, -6.0, 12000)
        mixed = probes.render(build(Exciter, probe, mix=0.3), 12000, rate=RATE)
        effect = build(Exciter, probe, mix=0.3)
        self.addCleanup(effect.deinit)
        wet = probes.wet_render(effect, 12000, rate=RATE)
        self.assertNotEqual(mixed.digest, wet.digest)
        kit.require_signal(wet)

    def test_it_refuses_a_class_with_no_dry_voice_to_mute(self):
        probe = sine(1010.0, -6.0, 8000)
        effect = build(WetOffTheShaper, probe, mix=0.7)
        self.addCleanup(effect.deinit)
        with self.assertRaises(kit.MeasurementRefused):
            kit.mute_dry(effect)


class LiveRenderTest(unittest.TestCase):
    """`require_live` - the guard that catches what #78 actually measured."""

    def _wet(self, probe_frames, render_frames):
        probe = sine(1010.0, -6.0, probe_frames)
        effect = build(WetOffTheShaper, probe, tune=600.0, harmonics=1.0,
                       mix=0.7)
        self.addCleanup(effect.deinit)
        return probes.render(effect.output, render_frames, rate=RATE,
                             effect=effect, allow_starved_taps=True)

    def test_the_guard_fires_on_a_render_that_outlived_its_probe(self):
        rendered = self._wet(24000, 24000)
        self.assertGreater(kit.silent_tail_frames(rendered), 0)
        with self.assertRaises(kit.ExhaustedProbeError) as caught:
            kit.require_live(rendered)
        self.assertIn("outlived its probe", str(caught.exception))

    def test_the_guard_is_quiet_when_the_probe_outlives_the_render(self):
        # The control: 256 frames of headroom, and nothing else changed.
        rendered = self._wet(24000 + 256, 24000)
        self.assertEqual(kit.silent_tail_frames(rendered), 0)
        kit.require_live(rendered)

    def test_that_is_where_the_seventy_dB_came_from(self):
        # The issue's own reading, both ways. Nothing about the Splitter is
        # different between these two numbers: one probe is 256 frames
        # longer than the other.
        #
        # The window is taken from the END of the settled region, because
        # the defect is at the end: the exhausted render's last 88 frames
        # are silence, and a transform that stops short of them reads a
        # clean tone. This used to be accidental - `exact_bin_size` rounded
        # 252 periods to 11976 samples and overshot into the silence by 24
        # of them. It now returns whole periods (9600 here), which stops 400 frames
        # early, so the window says where it wants to sit rather than
        # relying on a rounding error to put it there.
        floors = []
        for margin in (0, 256):
            rendered = self._wet(24000 + margin, 24000)
            x = rendered.float[12000:, 0]
            size = kit.exact_bin_size(len(x), RATE, 1010.0)
            mags, bin_hz, _, _ = kit.magnitude_spectrum(x[len(x) - size:],
                                                        RATE, size=size)
            centre = int(round(1010.0 / bin_hz))
            base = float(mags[centre - 2:centre + 3].max())
            floors.append(20.0 * math.log10(float(mags[1:7].max()) / base))
        exhausted, live = floors
        self.assertGreater(exhausted, -40.0)      # -31.6 dB; the issue's
                                                  # own reading was -33.5
        self.assertLess(live, -100.0)             # -111.5 dB with headroom
        self.assertGreater(exhausted - live, 60.0)


if __name__ == "__main__":
    unittest.main()
