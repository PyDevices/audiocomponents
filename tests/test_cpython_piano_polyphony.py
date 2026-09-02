"""Holding a chord on a piano must not silence keys (audiocomponents#18).

`synthio.Synthesizer.press` refuses at capacity rather than stealing, so past
a certain key a held chord simply stopped sounding new notes - not quieter,
not stolen, absent. These tests hold chords the way the bug report does and
assert two things the five pianos now guarantee:

* every key produces sound, however deep into the chord it falls; and
* the number of keys sounding at once never drops below what the engine can
  physically carry.

The keys are stacked fourths so no key's fundamental sits on another key's
harmonic, and the check reads the engine's own note state rather than a
spectrum: these wavetables run to thirty-nine harmonics, which makes a
fundamental peak an unreliable witness.
"""

import unittest

import audiocore
import audioinstruments
from audioinstruments import _support

SAMPLE_RATE = 48000
PIANOS = ("rhodes", "wurlitzer", "pianet", "clavinet", "cp70")
KEYS = (48, 53, 58, 63, 68, 73, 78, 83, 88, 93)

# A ten-key chord is inside every one of these instruments' modelled key
# counts - twelve for cp70, sixteen for the rest - so nothing here is
# testing MAX_VOICES.


def sounding_keys(instrument):
    """The distinct MIDI keys the engine is actually sounding right now."""
    import math
    synth = instrument.synth
    keys = set()
    for note in synth.pressed:
        _state, level = synth.note_info(note)
        try:
            amplitude = float(note.amplitude)
        except (TypeError, ValueError):
            amplitude = 1.0
        if level > 0.001 and amplitude > 0.0005:
            keys.add(int(round(69 + 12 * math.log(note.frequency / 440.0)
                               / math.log(2.0))))
    return keys


def play_chord(name, gap_blocks, hold_blocks):
    """Press every key of KEYS in turn, holding all of them, and return the
    instrument with the chord still down."""
    instrument = audioinstruments.create(name, sample_rate=SAMPLE_RATE,
                                         channel_count=2)
    for pitch in KEYS:
        instrument.note_on(pitch, 100)
        for _ in range(gap_blocks):
            audiocore.get_buffer(instrument.output)
    for _ in range(hold_blocks):
        audiocore.get_buffer(instrument.output)
    return instrument


class PianoPolyphonyTest(unittest.TestCase):
    def test_every_key_of_a_rolled_chord_sounds(self):
        # A chord rolled on at roughly 0.15 s a key, all ten held to the end.
        for name in PIANOS:
            instrument = play_chord(name, 28, 20)
            self.assertEqual(sounding_keys(instrument), set(KEYS),
                             "%s: keys went missing from a held chord" % name)
            instrument.deinit()

    def test_every_key_of_a_block_chord_sounds(self):
        # The harder case: ten keys inside one block, so nothing the engine
        # was already playing has had a chance to finish and free a channel.
        for name in PIANOS:
            instrument = play_chord(name, 0, 40)
            self.assertEqual(sounding_keys(instrument), set(KEYS),
                             "%s: keys went missing from a block chord" % name)
            instrument.deinit()

    def test_a_note_on_is_never_left_entirely_silent(self):
        # Deep into a chord the engine may have no room for every layer of a
        # key, and dropping one is correct. Dropping all of them is the bug.
        for name in PIANOS:
            placed = []
            original = _support.press_voice

            def watching(synth, voices, retired, notes, _original=original):
                got = _original(synth, voices, retired, notes)
                placed.append(len(got))
                return got

            _support.press_voice = watching
            try:
                instrument = play_chord(name, 0, 4)
            finally:
                _support.press_voice = original
            instrument.deinit()
            self.assertEqual(len(placed), len(KEYS), name)
            self.assertNotIn(0, placed,
                             "%s: a key was refused outright" % name)

    def test_cp70_survives_a_chorus_move_under_a_held_chord(self):
        # cp70's notes-per-key is macro-dependent - three with Chorus up, two
        # with it down - so a voice pressed before the move and one pressed
        # after disagree about their own size. The listening guide's own
        # gesture 1 asks for exactly this move, and a fix that counts keys
        # rather than asking the engine drops the keys pressed after it.
        for before, after in ((127, 0), (0, 127)):
            instrument = audioinstruments.create("cp70",
                                                 sample_rate=SAMPLE_RATE,
                                                 channel_count=2)
            instrument.set_macro(5, before)
            for pitch in KEYS[:5]:
                instrument.note_on(pitch, 100)
                for _ in range(28):
                    audiocore.get_buffer(instrument.output)
            instrument.set_macro(5, after)
            for pitch in KEYS[5:]:
                instrument.note_on(pitch, 100)
                for _ in range(28):
                    audiocore.get_buffer(instrument.output)
            self.assertEqual(sounding_keys(instrument), set(KEYS),
                             "cp70: keys lost across a Chorus %d -> %d move"
                             % (before, after))
            instrument.deinit()

    def test_reclaiming_never_tracks_one_note_in_two_places(self):
        # A note handed to a new key must leave the voice or the pool it came
        # from. Tracked twice, it would be released twice and two keys would
        # believe they own one channel.
        for name in PIANOS:
            instrument = audioinstruments.create(name,
                                                 sample_rate=SAMPLE_RATE,
                                                 channel_count=2)
            seen = {}
            original = _support.press_voice

            def watching(synth, voices, retired, notes, _original=original):
                got = _original(synth, voices, retired, notes)
                seen.clear()
                for key in voices:
                    for note in voices[key][0]:
                        self.assertNotIn(id(note), seen, name)
                        seen[id(note)] = key
                for note in retired:
                    self.assertNotIn(id(note), seen, name)
                    seen[id(note)] = "retired"
                return got

            _support.press_voice = watching
            try:
                for round_ in range(4):
                    for pitch in KEYS:
                        instrument.note_on(pitch, 100)
                        audiocore.get_buffer(instrument.output)
                    for pitch in KEYS[:5]:
                        instrument.note_off(pitch)
                    audiocore.get_buffer(instrument.output)
            finally:
                _support.press_voice = original
            instrument.deinit()

    def test_the_reclaim_pool_stays_bounded(self):
        # It holds note objects, so an unbounded one is a slow leak on a
        # microcontroller.
        retired = []
        for index in range(_support.RETIRED_LIMIT * 3):
            _support.retire(retired, (index,))
            self.assertLessEqual(len(retired), _support.RETIRED_LIMIT)
        # Oldest out first: what is left is the most recent window.
        self.assertEqual(retired[-1], _support.RETIRED_LIMIT * 3 - 1)


if __name__ == "__main__":
    unittest.main()
