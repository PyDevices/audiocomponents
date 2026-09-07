"""What the pitch and stereo classes do to a signal today.

The octaver's reach either way, and its refusal to build shifters it
was not asked for - a Splitter fans out to four taps and no more.

Retired by the effects program's **phase 6 - pitch, stereo, racks**. Every
assertion here is written against a surface that phase replaces, so when
its classes have been rebuilt - each carrying its own invariant and
planted-fault tests - this module is deleted whole and nothing else in the
suite moves. Until then the contract-level tests over `audioeffects.ALL` in
`test_cpython_effects_library.py` hold the catalogue, and these hold the
character.

Covers `Octaver`.
"""

import os
import sys
import unittest

import audioeffects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import peak, source  # noqa: E402


class PitchTest(unittest.TestCase):
    def test_an_octaver_reaches_two_octaves_either_way(self):
        deep = audioeffects.Octaver(source(), down=0.4, down2=0.4)
        self.assertEqual(deep.down2.semitones, -24.0)
        self.assertIsNone(deep.up)
        self.assertGreater(peak(deep.output, 12), 0.001)
        high = audioeffects.Octaver(source(), down=0.0, up=0.4, up2=0.4)
        self.assertEqual(high.up2.semitones, 24.0)
        self.assertIsNone(high.down)

    def test_an_octaver_builds_only_the_octaves_it_was_asked_for(self):
        # A Splitter fans out to four taps, so the dry signal plus three
        # octaves is the ceiling - and the default, one octave down, should
        # cost one shifter rather than four.
        one = audioeffects.Octaver(source())
        self.assertEqual(len(one.mixer.voice), 2)
        with self.assertRaises(ValueError):
            audioeffects.Octaver(source(), down=0.3, down2=0.3, up=0.3,
                                 up2=0.3)


if __name__ == "__main__":
    unittest.main()
