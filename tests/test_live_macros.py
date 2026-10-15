"""Turning a continuous macro changes the notes that are already sounding.

A player holding a chord and sweeping Cutoff expects to hear the sweep, the
way a hardware knob reaches every voice at once (audiocomponents#166). Each
case here holds a note, moves one macro to an extreme while it sounds, and
asserts the held note comes out differently at 0 than at 127.

``LIVE`` lists, per instrument, the macros that reach a held note. Macros not
listed take effect on the next note: envelope times, glide, voice modes,
waveform and table choices, pitch, and anything baked into a wavetable when
the note starts. Drum machines are not listed at all: their hits are short,
and every macro reaches the next hit.
"""

import hashlib
import unittest

import audiocore
import audioinstruments

SAMPLE_RATE = 48000

#: instrument -> macro indices that a held note follows.
LIVE = {
    "minimoog": (0, 1, 2, 3, 7, 15),
}


def held(name, index, value):
    """Hash of a held note's output after macro ``index`` moves to ``value``.

    The macro starts mid-range so that a layer it would gate off at zero is
    sounding when the note starts."""
    instrument = audioinstruments.create(name, SAMPLE_RATE, channel_count=1)
    instrument.set_macro(index, 64)
    instrument.note_on(57, 110)
    for _ in range(20):
        audiocore.get_buffer(instrument.output)
    instrument.set_macro(index, value)
    digest = hashlib.sha256()
    for _ in range(40):
        digest.update(bytes(audiocore.get_buffer(instrument.output)[1]))
    return digest.hexdigest()


class LiveMacroTest(unittest.TestCase):
    def test_every_listed_instrument_is_melodic(self):
        for name in LIVE:
            self.assertIn(name, audioinstruments.MELODIC)

    def test_held_notes_follow_live_macros(self):
        for name, indices in LIVE.items():
            labels = audioinstruments.load(name).MACRO_LABELS
            for index in indices:
                with self.subTest(instrument=name, macro=labels[index]):
                    self.assertNotEqual(
                        held(name, index, 0), held(name, index, 127),
                        "%s: turning %s does not reach a held note"
                        % (name, labels[index]))


if __name__ == "__main__":
    unittest.main()
