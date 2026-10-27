"""A reset part-way through a source buffer keeps the frames the graph took.

A host that hands an effect 100-frame buffers and resets it after twelve
256-frame pulls has had 3,072 frames played and 3,100 taken: the last 28
are the frames that come next. A reset that dropped them ran the output 28
frames ahead of the source for the rest of the stream (audiocomponents#157,
and the reset half of #208). Two things dropped them: the re-arm let go of
the source as if a Mix 0 bypass had read past it, and a mixer voice reading
a Splitter tap directly lost the part of a buffer it held when the reset
stopped it.

The check is the lifecycle matrix's PR property on 100-frame buffers: from
the reset on, the output is byte-identical to a fresh instance at patch 0
fed the source from the frame the reset landed on.
"""

import os
import sys
import unittest
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "lib"))

import audioeffects                                            # noqa: E402
import lifecycle                                               # noqa: E402

RATE = 48000
BLOCK = lifecycle.BLOCK
#: Pulls before the reset: 3,072 frames, which ends 28 frames into the
#: 31st 100-frame source buffer.
BEFORE = 12
AFTER = 40

#: The classes whose reset re-arms the graph and once dropped those frames,
#: and Overdrive, which was fixed first, as the guard on the shared path.
CLASSES = ("Compressor", "Exciter", "Distortion", "Overdrive", "Bitcrusher")


def _rotated(values, channels, frames):
    """`values` starting `frames` in, wrapped: the looped material from
    that frame on."""
    total = len(values) // channels
    at = (frames % total) * channels
    return array("h", values[at:]) + array("h", values[:at])


def _pull_frames(effect, frames, channels):
    out = bytearray()
    lifecycle._pull_to(effect, out, frames * 2 * channels, 2 * channels)
    return bytes(out[:frames * 2 * channels])


def reset_against_fresh(cls, channels, kind="100", patch=None):
    """The first frame where the reset instance and a fresh one differ
    after the reset, or -1."""
    values = lifecycle.material_for("loop", RATE, channels)
    feed = lifecycle.Feed(values, RATE, channels, kind, loop=True)
    effect = cls(feed.port, sample_rate=RATE,
                 **({} if patch is None else {"patch": patch}))
    landed = BEFORE * BLOCK
    fresh_feed = lifecycle.Feed(_rotated(values, channels, landed), RATE,
                                channels, kind, loop=True)
    fresh = cls(fresh_feed.port, sample_rate=RATE, patch=0)
    try:
        _pull_frames(effect, landed, channels)
        effect.reset()
        frames = AFTER * BLOCK
        got = array("h", _pull_frames(effect, frames, channels))
        want = array("h", _pull_frames(fresh, frames, channels))
    finally:
        effect.deinit()
        fresh.deinit()
    for index in range(len(want)):
        if got[index] != want[index]:
            return index // channels
    return -1


class AResetKeepsTheFramesTheGraphTook(unittest.TestCase):

    def test_a_reset_mid_buffer_is_a_fresh_instance_on_time(self):
        for name in CLASSES:
            cls = getattr(audioeffects, name)
            for channels in (2, 1):
                with self.subTest(cls=name, channels=channels):
                    self.assertEqual(
                        reset_against_fresh(cls, channels), -1)

    def test_a_reset_on_a_block_boundary_still_is(self):
        # The control the test above leans on: on 256-frame buffers there
        # is nothing part-taken, and the matrix's PR already holds this.
        for name in CLASSES:
            cls = getattr(audioeffects, name)
            with self.subTest(cls=name):
                self.assertEqual(
                    reset_against_fresh(cls, 2, kind="256"), -1)


if __name__ == "__main__":
    unittest.main()
