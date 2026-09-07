"""What the drive classes do to a signal today.

The three saturation characters as curves rather than presets, the
overdrive knob buying harmonics and not volume, the bit depth, and the
cabinet's tilt and headroom.

Retired by the effects program's **phase 4 - drive**. Every assertion here
is written against a surface that phase replaces, so when its classes have
been rebuilt - each carrying its own invariant and planted-fault tests -
this module is deleted whole and nothing else in the suite moves. Until
then the contract-level tests over `audioeffects.ALL` in
`test_cpython_effects_library.py` hold the catalogue, and these hold the
character.

Covers `Saturation`, `Overdrive`, `Bitcrusher` and `CabinetSim`.
"""

import os
import sys
import unittest

import audioeffects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import (harmonic_db, peak, source, tilt_db,  # noqa: E402
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

    def test_the_overdrive_knob_actually_drives(self):
        # OVERDRIVE mode ignores the engine node's own `drive` argument -
        # its curve is a fixed shape - so passing the knob straight through
        # left it inert. It is pre-gain into the curve now, with the level
        # put back after, so turning it up buys harmonics and not volume.
        harmonics = []
        for drive in (0.1, 0.4, 0.9):
            second, third = harmonic_db(
                lambda s, d=drive: audioeffects.Overdrive(
                    s, drive=d, mix=1.0).output)
            harmonics.append(second)
        self.assertEqual(harmonics, sorted(harmonics), harmonics)
        self.assertGreater(harmonics[-1], harmonics[0] + 6.0, harmonics)
        levels = [tone_gain_db(1000.0, lambda s, d=d: audioeffects.Overdrive(
            s, drive=d, mix=1.0).output) for d in (0.1, 0.4, 0.9)]
        self.assertLess(max(levels) - min(levels), 2.0, levels)

    def test_a_bitcrusher_can_be_asked_for_a_bit_depth(self):
        for bits in (4, 8, 12):
            self.assertEqual(audioeffects.Bitcrusher(source(),
                                                     bits=bits).bits, bits)
        # Fewer bits is a coarser quantizer, so a louder error against the
        # signal it came from - which is what "crushed" means.
        eight = peak(audioeffects.Bitcrusher(source(), bits=8).output, 8)
        four = peak(audioeffects.Bitcrusher(source(), bits=4).output, 8)
        self.assertNotAlmostEqual(eight, four, places=3)
        with self.assertRaises(ValueError):
            audioeffects.Bitcrusher(source(), bits=20)

    def test_a_cabinet_rolls_the_top_off_and_keeps_the_body(self):
        cabinet = lambda s: audioeffects.CabinetSim(s, patch=1).output
        body = tone_gain_db(100.0, cabinet)
        middle = tone_gain_db(1000.0, cabinet)
        top = tone_gain_db(10000.0, cabinet)
        # The bump is real, and the roll-off above the cone's limit is steep.
        self.assertGreater(body, middle + 2.0)
        self.assertLess(top, middle - 20.0)

    def test_a_cabinet_does_not_amplify(self):
        # It is normalized by what it does to a signal, not by its tallest
        # tap: three filter sections with two peaking boosts have a peak gain
        # of several, and a cabinet that multiplies by several clips.
        for index in sorted(audioeffects.CabinetSim.PATCHES):
            cabinet = audioeffects.CabinetSim(source(), patch=index)
            self.assertLess(peak(cabinet.output, 8, skip=2), 0.95, index)


if __name__ == "__main__":
    unittest.main()
