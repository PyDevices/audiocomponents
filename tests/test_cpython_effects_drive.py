"""What the drive classes `drive.py` still serves do to a signal today.

The three saturation characters as curves rather than presets.

Retired by the effects program's **phase 4 - drive**. Every assertion here
is written against a surface that phase replaces, so as its classes come
home - each carrying its own invariant and planted-fault tests - the
assertions about them leave this file, and the file goes when the last one
does. `Overdrive`, `Bitcrusher` and `CabinetSim` went on 2026-09-18, to
`test_cpython_effects_overdrive.py`, `..._bitcrusher.py` and
`..._cabinetsim.py`; the knob law, the bit depth and the cabinet's tilt and
headroom are read there, against the classes the package actually serves.
They could not be read here any more: `audioeffects.Overdrive` has been the
rebuild since the board runner adopted it, and the old class's knob and the
old class's `bits` attribute are not on it.

Until `Saturation` comes home the contract-level tests over
`audioeffects.ALL` in `test_cpython_effects_library.py` hold the catalogue,
and these hold its character.

Covers `Saturation`. `Fuzz` and `Exciter` are `drive.py`'s too and have no
character test here; they never had one.
"""

import os
import sys
import unittest

import audioeffects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import (harmonic_db, source, tilt_db,  # noqa: E402
                             tone_gain_db)


class DriveTest(unittest.TestCase):
    def test_the_saturation_characters_are_different_curves(self):
        # The three are not presets over one curve: tube runs the engine's
        # asymmetric OVERDRIVE, which generates even harmonics, and the
        # other two run its odd-symmetric WAVESHAPE, which generates none.
        # A 2nd harmonic is the whole difference between a valve and a
        # tape machine, so measure it rather than trusting the table.
        second = {}
        for character in ("tube", "tape", "console"):
            second[character], third = harmonic_db(
                lambda s, c=character: audioeffects.Saturation(
                    s, amount=1.0, character=c).output)
            self.assertGreater(third, -60.0,
                               "%s generates no harmonics at all" % character)
        self.assertGreater(second["tube"], second["tape"] + 40.0)
        self.assertGreater(second["tube"], second["console"] + 40.0)

    def test_the_saturation_characters_are_level_matched(self):
        # Switching character should change the colour and not the gain,
        # or an arrangement has to be re-balanced to audition one.
        levels = [tone_gain_db(1000.0, lambda s, c=c: audioeffects.Saturation(
            s, amount=1.0, character=c).output)
            for c in ("tube", "tape", "console")]
        self.assertLess(max(levels) - min(levels), 0.75, levels)

    def test_amount_scales_the_whole_character(self):
        # Including the tone shaping. A quarter of the way into tape should
        # be a quarter of its top-end loss, not all of it.
        full, quarter, none = (
            tilt_db(lambda s, a=a: audioeffects.Saturation(
                s, amount=a, character="tape").output)
            for a in (1.0, 0.25, 0.0))
        self.assertLess(full, -2.0)
        self.assertAlmostEqual(quarter, full * 0.25, delta=0.25)
        self.assertAlmostEqual(none, 0.0, delta=0.1)

    def test_tape_darkens_and_console_brightens(self):
        tape = tilt_db(lambda s: audioeffects.Saturation(
            s, amount=1.0, character="tape").output)
        console = tilt_db(lambda s: audioeffects.Saturation(
            s, amount=1.0, character="console").output)
        self.assertLess(tape, -2.0)
        self.assertGreater(console, 0.2)
        # tube shapes nothing: its character is entirely in the harmonics.
        self.assertAlmostEqual(
            tilt_db(lambda s: audioeffects.Saturation(
                s, amount=1.0, character="tube").output), 0.0, delta=0.2)

    def test_tape_has_a_head_bump_and_the_other_two_do_not(self):
        # The low end is the half of the tape character that only became
        # possible once the biquads could describe an 80 Hz shelf at all.
        for character, expected in (("tape", 1.43), ("tube", 0.0),
                                    ("console", 0.0)):
            with self.subTest(character=character):
                self.assertAlmostEqual(
                    tilt_db(lambda s, c=character: audioeffects.Saturation(
                        s, amount=1.0, character=c).output,
                        high=40.0, reference=1000.0),
                    expected, delta=0.2)

    def test_an_unknown_character_is_refused(self):
        with self.assertRaises(ValueError):
            audioeffects.Saturation(source(), character="transistor")


if __name__ == "__main__":
    unittest.main()
