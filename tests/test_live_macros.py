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
    "andromeda": (0, 1, 2, 3, 4, 5, 6, 7),
    "arp2600": (0, 1, 2, 3, 4),
    "b3": (0, 1, 2, 3, 4, 5, 7, 9),
    "clavinet": (0, 1, 3, 4, 5),
    "cp70": (0, 1, 2, 7),
    "cs80": (0, 1, 2, 3, 6, 15),
    "cz101": (0, 1, 4, 5, 6),
    "d50": (0, 1, 2, 4, 5),
    "dx7": (0, 1, 3, 8, 10, 12, 14),
    "emulator2": (0, 1, 2, 7, 8, 9),
    "fairlight": (0, 2, 8),
    "farfisa": (0, 1, 2, 3, 4, 5, 7, 8),
    "fs1r": (0, 4, 5),
    "jp8000": (0, 1, 2, 4, 5, 14),
    "juno106": (0, 1, 2, 3, 4, 6, 7, 9, 10),
    "jupiter8": (0, 1, 2, 3, 4, 6, 14),
    "k2600": (0, 1, 2, 3, 4, 5, 6, 7, 12, 13, 14),
    "karplus": (0, 3),
    "mellotron": (0, 1, 2, 3, 6),
    "microwave": (0, 1, 2, 3, 4, 5),
    "minimoog": (0, 1, 2, 3, 7, 15),
    "ms20": (0, 1, 2, 3, 4, 6, 12),
    "ms2000": (0, 2, 3, 4, 5, 6),
    "music_easel": (0, 1, 2, 3),
    "nord_lead": (0, 1, 2, 5, 6, 7),
    "obxa": (0, 2, 3, 4),
    "odyssey": (0, 1, 2, 4, 5, 12),
    "pianet": (0, 2, 4, 5),
    "polysix": (0, 1, 2, 3, 4, 5),
    "ppg_wave": (0, 1, 2, 3, 4),
    "prophet5": (0, 1, 2, 3, 14, 15),
    "prophet_vs": (0, 1, 2, 3, 4, 5, 6),
    "rhodes": (0, 1, 2, 5, 6),
    "sh101": (0, 2, 3, 4, 5),
    "solina": (0, 1, 2, 3, 4),
    "taurus": (0, 3, 4, 5),
    "tb303": (0, 2, 3, 4, 6, 7),
    "virus": (0, 2, 3, 4, 5, 6),
    "vl1": (0, 1, 2, 3, 4),
    "vox_continental": (0, 1, 2, 3, 4, 5, 6, 7),
    "vp330": (0, 1, 2, 3, 6, 7, 8, 9, 10),
    "wasp": (0, 2, 3, 4),
    "wurlitzer": (0, 1, 2),
}

#: (instrument, macro) -> (other macro, value) to set before the note. An LFO
#: rate is only heard while its depth is up, and a modulation LFO whose depth
#: is zero when the note starts is never built at all.
GATES = {
    ("clavinet", 4): (3, 100),      # Wah Rate needs Wah Depth
    ("cz101", 5): (6, 100),         # Vibrato Rate needs Vibrato Depth
    ("dx7", 14): (12, 100),         # Vibrato Rate needs Vibrato Depth
    ("emulator2", 7): (8, 100),     # Vibrato Rate needs Vibrato Depth
    ("farfisa", 7): (8, 100),       # Vibrato Rate needs Vibrato Depth
    ("k2600", 13): (12, 100),       # Mod Rate needs Mod Wheel
    ("k2600", 14): (12, 100),       # Mod Depth needs Mod Wheel
    ("pianet", 4): (5, 100),        # Vibrato Rate needs Vibrato Depth
    ("prophet5", 14): (15, 100),    # LFO Rate needs LFO Depth
    ("vl1", 3): (4, 100),           # Growl Rate needs Growl Depth
    ("vox_continental", 5): (6, 100),   # Vibrato Rate needs Vibrato Depth
    ("vp330", 7): (8, 100),         # Vibrato Rate needs Vibrato Depth
}

#: Macros on a transient that has died away by the time the other cases move
#: their knob; these move at once.
EARLY = (("b3", 7), ("cp70", 1), ("d50", 1))   # Key Click, Hammer, Transient


def held(name, index, value):
    """Hash of a held note's output after macro ``index`` moves to ``value``.

    The macro starts mid-range so that a layer it would gate off at zero is
    sounding when the note starts."""
    instrument = audioinstruments.create(name, SAMPLE_RATE, channel_count=1)
    gate = GATES.get((name, index))
    if gate is not None:
        instrument.set_macro(*gate)
    instrument.set_macro(index, 64)
    instrument.note_on(57, 110)
    for _ in range(0 if (name, index) in EARLY else 20):
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
