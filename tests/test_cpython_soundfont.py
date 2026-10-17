"""`soundfont` and `soundfont_drums` on the bank `sf2_builder` writes.

The plumbing, without a real bank: how the bank is found, the patch list
and pad map a bank becomes, one voice per region and a stereo layer as two,
the velocity split, release, the exclusive-class choke, Bank Select, voice
stealing, and the macros reaching held voices. The General MIDI gate on a
real bank is `test_cpython_soundfont_gm.py`.
"""

import os
import pathlib
import shutil
import sys
import tempfile
import unittest

import audioinstruments
import audioinstruments.soundfont as soundfont
import audioinstruments.soundfont_drums as soundfont_drums

SUPPORT = pathlib.Path(__file__).resolve().parent / "support"
if str(SUPPORT) not in sys.path:
    sys.path.insert(0, str(SUPPORT))

import sf2_builder  # noqa: E402
import sf2_play  # noqa: E402

SR = 48000


class SoundFontInstrumentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="sf2inst")
        cls.path = os.path.join(cls.tmp, "tiny.sf2")
        sf2_builder.tiny_bank().write(cls.path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.inst = audioinstruments.create("soundfont", SR, bank=self.path)
        self.kit = audioinstruments.create("soundfont_drums", SR,
                                           bank=self.path)

    def tearDown(self):
        self.inst.deinit()
        self.kit.deinit()

    # -- finding the bank ---------------------------------------------------

    def test_bank_is_found_in_order(self):
        home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(home, "soundfonts"))
        shutil.copy(self.path, os.path.join(home, "soundfonts", "b.sf2"))
        shutil.copy(self.path, os.path.join(home, "soundfonts", "a.sf2"))
        saved = {k: os.environ.pop(k, None)
                 for k in ("SOUNDFONT", "HOME", "USERPROFILE")}
        try:
            os.environ["HOME"] = home
            self.assertEqual(soundfont.find_bank("/x/y.sf2"), "/x/y.sf2")
            self.assertEqual(soundfont.find_bank(),
                             home + "/soundfonts/a.sf2")
            os.environ["SOUNDFONT"] = "/from/env.sf2"
            self.assertEqual(soundfont.find_bank(), "/from/env.sf2")
            self.assertEqual(soundfont.find_bank("/x/y.sf2"), "/x/y.sf2")
            del os.environ["SOUNDFONT"]
            os.environ["HOME"] = os.path.join(self.tmp, "nowhere")
            with self.assertRaises(OSError) as caught:
                soundfont.find_bank()
            message = str(caught.exception)
            for place in ("bank=", "SOUNDFONT", "soundfonts"):
                self.assertIn(place, message)
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_an_open_bank_is_shared_by_path(self):
        self.assertIs(self.inst._player.bank, self.kit._player.bank)
        other = audioinstruments.create("soundfont", SR,
                                        bank=self.inst.bank)
        try:
            self.assertIs(other.bank, self.inst.bank)
        finally:
            other.deinit()

    # -- what the bank becomes -----------------------------------------------

    def test_patches_and_pads_come_from_the_bank(self):
        self.assertEqual([p[0] for p in self.inst.patches.values()],
                         ["Piano", "Pad"])
        self.assertEqual(self.inst.patches[0][1], soundfont.DEFAULT_MACROS)
        self.assertEqual([p[0] for p in self.kit.patches.values()],
                         ["Standard Kit"])
        self.assertEqual(self.inst.preset, (0, 0))
        self.assertEqual(self.kit.preset, (128, 0))
        self.assertEqual(self.kit.preset_name, "Standard Kit")
        notes = [n for n, _ in soundfont_drums.NOTE_MAP]
        self.assertEqual(notes, list(range(35, 82)))
        self.assertIn("NOTE_MAP", vars(soundfont_drums))
        self.assertNotIn("NOTE_MAP", vars(soundfont))
        self.assertEqual(self.kit.note_map, soundfont_drums.NOTE_MAP)
        self.assertIsNone(self.inst.note_map)
        for module in (soundfont, soundfont_drums):
            self.assertEqual(len(module.MACRO_LABELS), 4)
            self.assertEqual(set(module.MACRO_MODES), set(range(4)))
            self.assertEqual(len(module.PATCHES[0][1]), 4)

    def test_both_are_live_instruments(self):
        for inst in (self.inst, self.kit):
            self.assertEqual(inst.sample_rate, SR)
            self.assertEqual(inst.channel_count, 2)
            self.assertFalse(inst.schedulable)
            self.assertEqual(inst.patch_index, 0)

    # -- notes ---------------------------------------------------------------

    def test_a_note_is_one_voice_per_region(self):
        player = self.inst._player
        self.inst.note_on(60, 100)          # the piano alone above vel 63
        self.assertEqual(len(player.held[(0, 60)]), 1)
        self.inst.note_on(64, 40)           # piano plus the stereo pad pair
        self.assertEqual(len(player.held[(0, 64)]), 3)
        voices = self.inst.output.voice
        pans = sorted(round(voices[i].pan, 2) for i in player.held[(0, 64)])
        self.assertEqual(pans, [-0.8, -0.2, 1.0])
        self.assertGreater(sf2_play.peak(sf2_play.render(self.inst, 0.05)),
                           0.0005)
        self.inst.note_off(60)
        self.inst.note_off(64)
        self.assertEqual(player.held, {})
        self.assertIsNotNone(sf2_play.silent_after(self.inst, 2.0, 1e-4))
        self.assertFalse(self.inst.output.playing)

    def test_velocity_picks_the_zone(self):
        player = self.kit._player
        self.kit.note_on(38, 60)
        soft = player.slots[player.held[(0, 38)][0]][4]
        self.kit.note_off(38)
        self.kit.note_on(38, 100)
        loud = player.slots[player.held[(0, 38)][0]][4]
        # The soft zone carries 100 cB of attenuation, scaled by 0.4.
        self.assertAlmostEqual(
            soft / (60 / 127.0) ** 2,
            (loud / (100 / 127.0) ** 2) * 10 ** (-100 * 0.4 / 200.0),
            places=6)

    def test_a_key_the_kit_lacks_is_silent(self):
        self.kit.note_on(70, 100)
        self.assertEqual(self.kit._player.held, {})
        self.assertEqual(sf2_play.peak(sf2_play.render(self.kit, 0.02)), 0.0)

    def test_closed_hat_chokes_the_open_one(self):
        player = self.kit._player
        self.kit.note_on(46, 100)
        open_slot = player.held[(0, 46)][0]
        self.assertEqual(player.slots[open_slot][3], 1)
        self.kit.note_on(42, 100)
        self.assertNotIn((0, 46), player.held)
        self.assertIn((0, 42), player.held)
        self.assertNotEqual(player.slots[open_slot], None)
        self.assertEqual(player.slots[open_slot][0], (0, 42))

    def test_program_change_and_bank_select(self):
        self.inst.program_change(1)
        self.assertEqual(self.inst.preset, (0, 1))
        self.assertEqual(self.inst.preset_name, "Pad")
        self.assertEqual(self.inst.patch_index, 1)
        # Bank 5 does not exist: back to the melodic bank.
        self.inst.control_change(0, 5)
        self.inst.program_change(0)
        self.assertEqual(self.inst.preset, (0, 0))
        # MSB 1, LSB 0 is bank 128, which does.
        self.inst.control_change(0, 1)
        self.inst.control_change(32, 0)
        self.inst.program_change(0)
        self.assertEqual(self.inst.preset, (128, 0))
        self.inst.note_on(36, 100)
        self.assertEqual(len(self.inst._player.held[(0, 36)]), 1)
        self.inst.reset()
        self.assertEqual(self.inst.preset, (0, 0))
        self.assertEqual(self.inst._player.held, {})

    def test_voice_stealing_takes_the_oldest(self):
        self.inst.program_change(1)       # two voices a note
        player = self.inst._player
        for key in range(40, 60):         # 40 voices asked of 32
            self.inst.note_on(key, 100)
        self.assertEqual(sorted(k for _, k in player.held),
                         list(range(44, 60)))
        self.assertTrue(all(slot is not None for slot in player.slots))
        # A releasing voice goes before a held one.
        self.inst.note_off(50)
        self.inst.note_on(60, 100)
        self.assertEqual(sorted(k for _, k in player.held),
                         [k for k in range(44, 61) if k != 50])

    def test_macros_reach_held_voices(self):
        player = self.inst._player
        self.inst.note_on(60, 100)
        slot = player.held[(0, 60)][0]
        voice = self.inst.output.voice[slot]
        ratio = player.slots[slot][5]
        self.assertAlmostEqual(voice.pitch, ratio, places=5)
        self.inst.set_macro(3, 127)
        self.assertAlmostEqual(voice.pitch,
                               ratio * 2 ** ((63 / 127.0) * 2 / 12.0),
                               places=5)
        self.inst.set_macro(3, 64)
        self.assertAlmostEqual(voice.pitch, ratio, places=5)
        self.inst.pitch_bend(16383)
        self.assertAlmostEqual(voice.pitch, ratio * 2 ** (2 / 12.0),
                               places=4)
        level = player.slots[slot][4]
        self.assertAlmostEqual(voice.level, level * 100 / 127.0, places=5)
        self.inst.set_macro(0, 0)
        self.assertEqual(voice.level, 0.0)
        self.inst.set_macro(1, 127)
        self.assertAlmostEqual(player.attack_scale, 4.0, places=1)
        self.inst.set_macro(2, 0)
        self.assertAlmostEqual(player.release_scale, 0.25, places=2)


if __name__ == "__main__":
    unittest.main()
