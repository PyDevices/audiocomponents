"""A reset comes back as a fresh instance at patch 0, for the classes the
kit's fresh check found red when it was built (Phase 7, step 7d).

Each class runs the fresh check's quick grid (`tests/support/kit_fresh.py`,
KIT.md): a reset before the first pull and mid-stream, from the defaults
and every patch, and each macro moved after it, against a fresh instance
built at patch 0. Every cell must be green.

    python -m unittest tests.test_reset_is_fresh
"""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "lib"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import kit_common as kc                                   # noqa: E402
import kit_fresh                                          # noqa: E402

VENDOR = "PyDevices"


def reds(name):
    lines = []
    kit_fresh.run(kc.resolve(name), emit=lines.append, quick=True)
    return [line for line in lines if "V:RED" in line]


class AResetIsAFreshInstance(unittest.TestCase):

    def check(self, name):
        got = reds(name)
        self.assertEqual(got, [], "\n".join(got[:8]))

    # The output mixer kept the block each voice had primed through the
    # chain the reset then cleared (`Component._reset_rearmed`).
    def test_exciter(self):
        self.check("Exciter")

    def test_compressor(self):
        self.check("Compressor")

    def test_bitcrusher(self):
        self.check("Bitcrusher")

    def test_overdrive(self):
        got = reds("Overdrive")
        self.assertEqual(got, [], "\n".join(got[:8]))

    def test_overdrive_mono(self):
        # audiocomponents#142's mono half: a fresh build's construction-
        # primed first block rendered its first 8 frames about 1.28x a
        # running instance's. Since Overdrive builds lazily (Phase 7) the
        # fresh build primes silence and a reset matches it, cell by cell.
        for patch in kc.patches(kc.resolve("Overdrive")):
            self.assertEqual(kit_fresh.reset_cell(
                kc.resolve("Overdrive"), 48000, 1, patch, {},
                kit_fresh.RESET_AT), "ok", patch)

    def test_distortion(self):
        self.check("Distortion")

    # The LFO, a note on a synthio.Synthesizer the walk does not reach,
    # played on through a reset (a fresh synthesizer now).
    def test_tremolo(self):
        self.check("Tremolo")

    def test_autopan(self):
        self.check("AutoPan")

    def test_ringmod(self):
        self.check("RingMod")

    def test_phaser(self):
        self.check("Phaser")

    # Stale state: a flat section's settings, a mixer re-played at the
    # outgoing patch's levels.
    def test_parametriceq(self):
        self.check("ParametricEQ")

    def test_dynamiceq(self):
        self.check("DynamicEQ")

    def test_multibandcompressor(self):
        self.check("MultibandCompressor")


class AResetTakesNothingFromTheSource(unittest.TestCase):
    """The arming is lazy (`Component._reset_rearmed`): a voice primes a
    block of silence, so the next block the source hands out after a reset
    is the one it would have handed without it."""

    NAMES = ("Bitcrusher", "Exciter", "Compressor", "Distortion",
             "Overdrive", "DynamicEQ", "MultibandCompressor")

    def test_the_source_stands_where_it_stood(self):
        import audiocore
        for name in self.NAMES:
            cls = kc.resolve(name)
            for patch in kc.patches(cls):
                for ch in (2, 1):
                    values = kit_fresh._material(48000, ch)
                    where = []
                    for reset in (False, True):
                        feed = kit_fresh._feed(values, 48000, ch)
                        e = kc.build(cls, feed.port, 48000, patch)
                        for _ in range(8):
                            kc.pull(e)
                        if reset:
                            e.reset()
                        where.append(bytes(
                            audiocore.get_buffer(feed.mat)[1]))
                        e.deinit()
                    self.assertEqual(where[0], where[1], (name, patch, ch))


if __name__ == "__main__":
    unittest.main()
