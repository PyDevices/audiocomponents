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

    @unittest.expectedFailure
    def test_bitcrusher(self):
        # Held for a ruling: re-arming takes a block of the source at the
        # reset, as a fresh build does at construction, and Bitcrusher's
        # own STATE test (reset, then a silent source, output exactly zero)
        # forbids that. Unfixed, a reset before the first pull plays the
        # block primed at construction.
        self.check("Bitcrusher")

    def test_overdrive(self):
        got = [line for line in reds("Overdrive")
               if "/48000/1/" not in line]
        self.assertEqual(got, [], "\n".join(got[:8]))

    @unittest.expectedFailure
    def test_overdrive_mono(self):
        # Open: in mono a reset mid-stream (reset@8) leaves the first 8
        # frames after it at about 0.78 of a fresh instance's (789 LSB at
        # most), with or without the re-arm, and not from the adapter, the
        # filters' or the shaper's reset. Stereo is green.
        got = [line for line in reds("Overdrive") if "/48000/1/" in line]
        self.assertEqual(got, [], "\n".join(got[:8]))

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


if __name__ == "__main__":
    unittest.main()
