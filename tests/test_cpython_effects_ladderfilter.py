"""`LadderFilter`'s input ceiling: the kit's plucked phrase is clean on
every patch at -10 dBFS and rails at -3 dBFS on Growl With Drive alone
(audiocomponents#192). The rest of the class is held by the kit and the
lifecycle matrix.

    python -m unittest tests.test_cpython_effects_ladderfilter
"""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "lib"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import kit_levels                                         # noqa: E402
from audioeffects.ladderfilter import LadderFilter        # noqa: E402

#: `_component` reads VENDOR off the module a class is defined in.
VENDOR = "PyDevices"


class TheInputCeiling(unittest.TestCase):

    def test_a_plucked_phrase_is_clean_to_minus_10_dbfs(self):
        self.assertEqual(kit_levels.red_patches(LadderFilter, -10), [])

    def test_at_minus_3_dbfs_growl_with_drive_rails(self):
        self.assertEqual(kit_levels.red_patches(LadderFilter, -3), [4])
        self.assertEqual(LadderFilter.PATCHES[4][0], "Growl With Drive")


if __name__ == "__main__":
    unittest.main()
