"""`drumkits`: ten machines under one program change.

The promise is narrow and testable. Selecting program N must give you that
machine — not something like it — the sixteen macros must reach the control
their label names on whichever kit is playing, and a hit a kit has no voice
for must be silent rather than substituted. Each of those is checked against
the machines themselves rather than against a stored digest: the standalone
instrument is the oracle, and it is right here in the same library.
"""

import re
import pathlib
import struct
import unittest

import audiocore
import audioinstruments
from audioinstruments import drumkits  # noqa: E402 - CPython test host
from audioinstruments import _gm

SAMPLE_RATE = 48000

#: The mixer holds one buffer, so everything this instrument plays arrives
#: that many frames after the same hit on the machine alone.
LAG_FRAMES = drumkits._MIXER_BYTES // 4

#: Kick, snare, closed hat, open hat, crash - the five every kit answers.
SHARED = (36, 38, 42, 46, 49)

LIB = pathlib.Path(__file__).resolve().parent.parent / "lib" / "audioinstruments"


def frames(node, count):
    """`count` stereo frames of PCM, as bytes."""
    out = b""
    while len(out) < count * 4:
        _result, view = audiocore.get_buffer(node)
        block = bytes(view)
        if not block:
            break
        out += block
    return out[:count * 4]


def peak(pcm):
    if not pcm:
        return 0.0
    values = struct.unpack("<%dh" % (len(pcm) // 2), pcm[:len(pcm) // 2 * 2])
    return max(abs(value) for value in values) / 32768.0


def macro_variable(kit, index):
    """The variable a kit's macro `index` assigns, read from its source."""
    source = (LIB / ("%s.py" % kit)).read_text(encoding="utf-8")
    found = re.search(r"data0 == %d:\s*(\w+)\s*=" % index, source)
    return found.group(1) if found else ""


class DrumKitsTest(unittest.TestCase):
    def test_every_program_plays_the_five_notes_that_travel(self):
        instrument = audioinstruments.create("drumkits", SAMPLE_RATE)
        for index, kit in enumerate(drumkits.KITS):
            instrument.program_change(index)
            self.assertEqual(instrument.kit, kit)
            for note in SHARED:
                instrument.note_on(note, 100)
                level = peak(frames(instrument.output, 4000))
                self.assertGreater(level, 0.001,
                                   "%s is silent on %d" % (kit, note))
                instrument.all_notes_off()
                frames(instrument.output, 12000)

    def test_a_program_is_the_machine_itself(self):
        # Not "sounds like": the same bytes the standalone instrument makes,
        # delayed by the mixer's one buffer.
        for index, kit in enumerate(drumkits.KITS):
            with self.subTest(kit=kit):
                note = audioinstruments.load(kit).NOTE_MAP[0][0]
                alone = audioinstruments.create(kit, SAMPLE_RATE)
                alone.note_on(note, 100)
                expected = frames(alone.output, 6000)

                switcher = audioinstruments.create("drumkits", SAMPLE_RATE)
                switcher.program_change(index)
                switcher.note_on(note, 100)
                played = frames(switcher.output, 6000 + LAG_FRAMES)
                self.assertEqual(expected, played[LAG_FRAMES * 4:])

    def test_a_hit_the_kit_has_no_voice_for_is_silent(self):
        switcher = audioinstruments.create("drumkits", SAMPLE_RATE)
        switcher.program_change(drumkits.KITS.index("tr606"))
        mapped = dict(audioinstruments.load("tr606").NOTE_MAP)
        for note, label in drumkits.NOTE_MAP:
            if note in mapped:
                continue
            switcher.note_on(note, 127)
            self.assertEqual(
                0.0, peak(frames(switcher.output, 2000 + LAG_FRAMES)),
                "the TR-606 answered %s (note %d)" % (label, note))

    def test_every_macro_reaches_the_control_its_kit_maps(self):
        for index, kit in enumerate(drumkits.KITS):
            note = audioinstruments.load(kit).NOTE_MAP[0][0]
            for slot, target in enumerate(drumkits.MACRO_MAP[kit]):
                if target is None:
                    continue
                with self.subTest(kit=kit, macro=drumkits.MACRO_LABELS[slot]):
                    alone = audioinstruments.create(kit, SAMPLE_RATE)
                    alone.set_macro(target, 10)
                    alone.note_on(note, 100)
                    expected = frames(alone.output, 4000)

                    switcher = audioinstruments.create("drumkits", SAMPLE_RATE)
                    switcher.program_change(index)
                    switcher.set_macro(slot, 10)
                    switcher.note_on(note, 100)
                    played = frames(switcher.output, 4000 + LAG_FRAMES)
                    self.assertEqual(expected, played[LAG_FRAMES * 4:])

    def test_no_macro_label_lies_about_what_it_moves(self):
        # The whole reason the macro set is fixed rather than per-kit is that
        # the host cannot be relabelled on a program change. That only buys
        # anything if the labels are true on every kit, so: a slot that says
        # Tune may not drive a level, and one that says Level may not drive a
        # pitch. Both mistakes were in the first draft of MACRO_MAP.
        tuneish = ("tune", "pitch", "_p", "freq")
        for kit in drumkits.KITS:
            for slot, target in enumerate(drumkits.MACRO_MAP[kit]):
                if target is None:
                    continue
                label = drumkits.MACRO_LABELS[slot].lower()
                variable = macro_variable(kit, target).lower()
                self.assertTrue(variable, "%s macro %d is not a simple "
                                          "assignment" % (kit, target))
                moves_pitch = any(word in variable for word in tuneish)
                if "tune" in label:
                    self.assertTrue(moves_pitch, "%s: %s moves %s"
                                    % (kit, label, variable))
                if "level" in label:
                    self.assertFalse(moves_pitch, "%s: %s moves %s"
                                     % (kit, label, variable))

    def test_a_tail_rings_across_a_kit_change(self):
        switcher = audioinstruments.create("drumkits", SAMPLE_RATE)
        switcher.note_on(49, 127)
        frames(switcher.output, 4000)
        before = peak(frames(switcher.output, 2000))
        switcher.program_change(drumkits.KITS.index("tr606"))
        after = peak(frames(switcher.output, 2000))
        self.assertGreater(before, 0.001)
        self.assertGreater(after, before * 0.5,
                           "the outgoing kit's cymbal was cut off")

    def test_the_note_map_is_the_union_of_the_kits(self):
        # The table is written out in the module so every text reader - the
        # plug-in scanner, the project generators - can have it without
        # importing synthio. This is what stops it drifting from the kits.
        union = set()
        for kit in drumkits.KITS:
            union.update(note for note, _label
                         in audioinstruments.load(kit).NOTE_MAP)
        self.assertEqual(sorted(union),
                         [note for note, _label in drumkits.NOTE_MAP])

    def test_every_voice_is_labelled_the_way_general_midi_labels_it(self):
        for note, label in drumkits.NOTE_MAP:
            self.assertEqual(_gm.PERCUSSION[note], label)

    def test_each_patch_is_a_kit_and_carries_that_kit_s_defaults(self):
        for index, kit in enumerate(drumkits.KITS):
            module = audioinstruments.load(kit)
            name, values = drumkits.PATCHES[index]
            self.assertEqual(module.DISPLAY_NAME, name)
            defaults = module.PATCHES[0][1]
            for slot, target in enumerate(drumkits.MACRO_MAP[kit]):
                expected = 64 if target is None else defaults[target]
                self.assertEqual(expected, values[slot],
                                 "%s %s" % (kit, drumkits.MACRO_LABELS[slot]))


if __name__ == "__main__":
    unittest.main()
