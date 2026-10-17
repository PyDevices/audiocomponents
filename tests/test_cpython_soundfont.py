"""`soundfont` and `soundfont_drums` on the bank `sf2_builder` writes.

The plumbing, without a real bank: how the bank is found, the patch list
and pad map a bank becomes, one voice per region and a stereo layer as two,
the velocity split, release, the exclusive-class choke, Bank Select, voice
stealing, the macros reaching held voices, and Pan: where the energy lands
per channel, a sounding note moving, a stereo pair keeping its spread (on a
sibling bank whose pair is not already at the edges), and Control Change
10 driving it. The General MIDI gate on a real bank is
`test_cpython_soundfont_gm.py`.
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
            self.assertEqual(len(module.MACRO_LABELS), 5)
            self.assertEqual(set(module.MACRO_MODES), set(range(5)))
            self.assertEqual(len(module.PATCHES[0][1]), 5)

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

    # -- pan ------------------------------------------------------------------

    PAN = soundfont.PAN_MACRO

    def _channels(self, inst, seconds=0.1):
        """(left RMS, right RMS) of the next `seconds`."""
        both = sf2_play.render(inst, seconds)
        return sf2_play.rms(both[0::2]), sf2_play.rms(both[1::2])

    def test_pan_is_the_fifth_macro_on_both(self):
        for inst in (self.inst, self.kit):
            self.assertEqual(inst.macro_labels[self.PAN], "Pan")
            self.assertEqual(inst.get_macro(self.PAN), 64)
        self.assertEqual(soundfont.MACRO_MODES[self.PAN], "BIPOLAR")
        self.assertEqual(soundfont_drums.MACRO_MODES[self.PAN], "BIPOLAR")
        self.assertEqual(soundfont.DEFAULT_MACROS[self.PAN], 64)

    def test_pan_puts_the_energy_where_it_says(self):
        # The kit's snare has no pan of its own, so centre is equal.
        kit = self.kit
        kit.note_on(36)
        left, right = self._channels(kit)
        self.assertGreater(left, 0.0005)
        self.assertAlmostEqual(left, right, delta=left * 0.02)
        kit.note_off(36)
        sf2_play.render(kit, 1.0)
        kit.set_macro(self.PAN, 0)
        kit.note_on(36)
        left, right = self._channels(kit)
        self.assertGreater(left, 0.0005)
        self.assertLess(right, left * 0.01)
        kit.note_off(36)
        sf2_play.render(kit, 1.0)
        kit.set_macro(self.PAN, 127)
        kit.note_on(36)
        left, right = self._channels(kit)
        self.assertGreater(right, 0.0005)
        self.assertLess(left, right * 0.01)
        # The macro is an offset on the region's own pan: the piano's zone
        # sits at -0.2, so centre leans left and hard right lands at 0.8.
        player = self.inst._player
        self.inst.note_on(60, 100)
        voice = self.inst.output.voice[player.held[(0, 60)][0]]
        self.assertAlmostEqual(voice.pan, -0.2, places=5)
        self.inst.set_macro(self.PAN, 127)
        self.assertAlmostEqual(voice.pan, 0.8, places=5)
        self.inst.set_macro(self.PAN, 0)
        self.assertEqual(voice.pan, -1.0)      # clamped, not -1.2
        self.inst.set_macro(self.PAN, 64)
        self.assertAlmostEqual(voice.pan, -0.2, places=5)

    def test_a_sounding_note_moves_with_pan(self):
        kit = self.kit
        kit.note_on(46)                        # the open hat rings on
        left, right = self._channels(kit)
        self.assertAlmostEqual(left, right, delta=left * 0.02)
        kit.set_macro(self.PAN, 0)
        sf2_play.render(kit, 0.05)             # past the engine's ramp
        left, right = self._channels(kit)
        self.assertGreater(left, 0.0005)
        self.assertLess(right, left * 0.01)
        kit.set_macro(self.PAN, 127)
        sf2_play.render(kit, 0.05)
        left, right = self._channels(kit)
        self.assertGreater(right, 0.0005)
        self.assertLess(left, right * 0.01)

    def test_a_stereo_pair_keeps_its_spread(self):
        # The tiny bank's pair is already at the edges, so the builder makes
        # a sibling with the pair at -0.5 and +0.5.
        G = sf2_builder.sf2
        b = sf2_builder.Bank("Pair")
        left = b.sample("L", sf2_builder._frames(2, 120), 10, 110, pitch=60,
                        link=1, kind=G.SAMPLE_LEFT)
        right = b.sample("R", sf2_builder._frames(3, 120), 10, 110, pitch=60,
                         link=0, kind=G.SAMPLE_RIGHT)
        pad = b.instrument("Pad", [
            [(G.GEN_PAN, -250), (G.GEN_SAMPLE_MODES, 1),
             (G.GEN_SAMPLE_ID, left)],
            [(G.GEN_PAN, 250), (G.GEN_SAMPLE_MODES, 1),
             (G.GEN_SAMPLE_ID, right)],
        ])
        b.preset("Pad", 0, 0, [[(G.GEN_INSTRUMENT, pad)]])
        path = os.path.join(self.tmp, "pair.sf2")
        b.write(path)
        inst = audioinstruments.create("soundfont", SR, bank=path)
        try:
            player = inst._player
            inst.note_on(60, 100)
            voices = [inst.output.voice[i] for i in player.held[(0, 60)]]
            pans = sorted(v.pan for v in voices)
            self.assertEqual([round(p, 5) for p in pans], [-0.5, 0.5])
            inst.set_macro(self.PAN, 80)       # (80 - 64) / 63 to the right
            pans = sorted(v.pan for v in voices)
            self.assertAlmostEqual(pans[1] - pans[0], 1.0, places=5)
            self.assertAlmostEqual(pans[0], -0.5 + 16 / 63.0, places=5)
            inst.set_macro(self.PAN, 48)       # (48 - 64) / 64 to the left
            pans = sorted(v.pan for v in voices)
            self.assertAlmostEqual(pans[1] - pans[0], 1.0, places=5)
            self.assertAlmostEqual(pans[0], -0.75, places=5)
            inst.set_macro(self.PAN, 0)        # the left voice clamps at -1
            pans = sorted(v.pan for v in voices)
            self.assertEqual(pans, [-1.0, -0.5])
            inst.note_off(60)
            inst.set_macro(self.PAN, 127)      # new notes start there
            inst.note_on(62, 100)
            voices = [inst.output.voice[i] for i in player.held[(0, 62)]]
            self.assertEqual(sorted(v.pan for v in voices), [0.5, 1.0])
        finally:
            inst.deinit()

    def test_cc10_drives_pan(self):
        for inst in (self.inst, self.kit):
            key = 60 if inst is self.inst else 36
            player = inst._player
            inst.note_on(key, 100)
            voice = inst.output.voice[player.held[(0, key)][0]]
            before = voice.pan
            inst.control_change(10, 127)
            self.assertEqual(inst.get_macro(self.PAN), 127)
            self.assertEqual(voice.pan, min(1.0, before + 1.0))
            inst.control_change(10, 0)
            self.assertEqual(inst.get_macro(self.PAN), 0)
            self.assertEqual(voice.pan, -1.0)
            # A program change puts the patch's centre back, as for Volume.
            inst.program_change(0)
            self.assertEqual(inst.get_macro(self.PAN), 64)
            self.assertAlmostEqual(voice.pan, before, places=5)
            # Bank Select still reaches the player past the override.
            if inst is self.inst:
                inst.control_change(0, 1)
                self.assertEqual(player.bank_msb, 1)
                inst.control_change(0, 0)


if __name__ == "__main__":
    unittest.main()
