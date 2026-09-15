import pathlib
import unittest
from types import SimpleNamespace

import audioinstruments

from support import note_table
from tools.validate_metadata import MetadataError, validate_component


def component(**fields):
    defaults = {
        "NAME": "example",
        "MACRO_LABELS": (),
        "MACRO_MODES": {},
        "PATCHES": {0: ("Default", ())},
    }
    defaults.update(fields)
    return SimpleNamespace(**defaults)


class MetadataContractTest(unittest.TestCase):
    def test_macroless_component_is_valid_when_empty_fields_are_explicit(self):
        self.assertFalse(validate_component(component(), kind="instrument"))

    def test_missing_required_field_is_invalid_even_when_the_value_is_empty(self):
        owner = component()
        del owner.MACRO_MODES
        with self.assertRaises(MetadataError):
            validate_component(owner, kind="instrument")

    def test_modes_are_complete_and_toggle_patches_are_discrete(self):
        owner = component(
            MACRO_LABELS=("Power", "Drive"),
            MACRO_MODES={0: "TOGGLE", 1: "UNIPOLAR"},
            PATCHES={0: ("Default", (64, 64))},
        )
        with self.assertRaises(MetadataError):
            validate_component(owner, kind="instrument")

    def test_malformed_patch_values_report_metadata_error(self):
        owner = component(PATCHES={0: ("Default", (128,))},
                           MACRO_LABELS=("Level",),
                           MACRO_MODES={0: "UNIPOLAR"})
        with self.assertRaises(MetadataError):
            validate_component(owner, kind="instrument")

    def test_percussion_is_defined_by_a_valid_note_map(self):
        melodic = component()
        self.assertFalse(validate_component(melodic, kind="instrument"))

        percussion = component(NOTE_MAP=((36, "Bass Drum"),))
        self.assertTrue(validate_component(percussion, kind="instrument"))

    def test_note_map_is_not_valid_on_an_effect(self):
        with self.assertRaises(MetadataError):
            validate_component(
                component(NOTE_MAP=((36, "Bass Drum"),)), kind="effect")

    def test_public_engineering_ranges_are_rejected(self):
        with self.assertRaises(MetadataError):
            validate_component(component(MACRO_RANGES=()), kind="effect")


if __name__ == "__main__":
    unittest.main()


class DrumNoteTableTest(unittest.TestCase):
    """The README's kit/hit table has to stay the modules' own answer.

    It is the page someone reads to decide whether their pattern will play on
    a given kit, and a hand-kept grid of 25 notes across ten machines is the
    kind of thing that is true the day it is written and wrong a month later.
    """

    README = (pathlib.Path(__file__).resolve().parent.parent
              / "lib" / "audioinstruments" / "README.md")

    def test_the_readme_table_is_what_the_note_maps_say(self):
        self.assertIn(note_table.render(),
                      self.README.read_text(encoding="utf-8"))

    def test_the_readme_voice_and_macro_counts_are_current(self):
        text = self.README.read_text(encoding="utf-8")
        for name, _heading in note_table.KITS:
            module = audioinstruments.load(name)
            self.assertIn(
                "**`%s`**" % name, text, "%s is missing from the README" % name)
            line = next(l for l in text.splitlines()
                        if l.startswith("- **`%s`**" % name))
            self.assertIn("%d voices" % len(module.NOTE_MAP), line)
            self.assertIn("%d macros" % len(module.MACRO_LABELS), line)

    def test_every_kit_answers_the_five_that_make_a_pattern_portable(self):
        # The README promises this outright, so it is a test and not a note.
        for name, _heading in note_table.KITS:
            mapped = dict(audioinstruments.load(name).NOTE_MAP)
            for note in (36, 38, 42, 46, 49):
                self.assertIn(note, mapped,
                              "%s does not answer %d" % (name, note))
