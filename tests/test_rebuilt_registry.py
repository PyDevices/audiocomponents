"""The registry rule: a rebuilt class replaces the old one by NAME, without
either module being edited.

A rebuild adds exactly one file, `lib/audioeffects/rebuilt/<name_lower>.py`,
one class per file. Nothing lists the classes, so sixteen of them can be
rebuilt in parallel with no shared file to conflict over -- which is the
whole point of the rule and the thing these tests hold it to.

`ExampleStock` and `ExampleAudioif` are the subjects: fixtures under
`rebuilt/`, deliberately absent from `audioeffects.__all__` so that neither
enters `audioeffects.ALL` and no host can reach them (audiocomponents#37).
"""

import array
import unittest

import audiocore
import audioeffects
from audioeffects import _component
from audioeffects import rebuilt
from tools.validate_metadata import MetadataError, validate_effects


def source(channels=2, rate=48000):
    return audiocore.RawSample(
        array.array("h", [4000, -4000] * 2048 * channels),
        sample_rate=rate, channel_count=channels)


class TheLookup(unittest.TestCase):
    def test_a_name_with_a_file_resolves_to_its_class(self):
        found = rebuilt.load("ExampleStock")
        self.assertIsNotNone(found)
        self.assertEqual(found.NAME, "ExampleStock")
        self.assertTrue(issubclass(found, _component.Component))

    def test_a_name_with_no_file_is_a_miss_not_an_error(self):
        self.assertIsNone(rebuilt.load("NoSuchEffectAnywhere"))

    def test_every_one_of_the_46_is_a_miss_today(self):
        # The fallback branch, over the real catalogue: nothing in Phase 2's
        # families has been rebuilt yet, so every name must miss and every
        # old class must still be the one the package exports.
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                self.assertIsNone(rebuilt.load(name))

    def test_a_file_whose_class_does_not_match_is_an_error(self):
        # `examplestock.py` exists, but holds no class whose NAME is
        # "Examplestock". That is a typo in a filename or a NAME, and
        # quietly serving the old class would hide a rebuild that never
        # took effect -- so it raises rather than missing.
        with self.assertRaises(ImportError) as caught:
            rebuilt.load("Examplestock")
        self.assertIn("holds no Component", str(caught.exception))

    def test_known_lists_what_is_there(self):
        self.assertEqual(sorted(rebuilt.known()),
                         ["ExampleAudioif", "ExampleStock"])


class TheReplacement(unittest.TestCase):
    """`_adopt` is what the package runs over its own globals at import.
    Here it runs over a scratch namespace, so both branches can be shown
    without touching one of the 46."""

    def test_a_rebuilt_class_replaces_the_old_one_by_name(self):
        class OldExampleStock(_component.Component):
            NAME = 'ExampleStock'
            MACRO_LABELS = ()
            MACRO_MODES = {}
            PATCHES = {0: ("Default", ())}

        namespace = {"Thing": OldExampleStock}
        audioeffects._adopt(namespace, ["Thing"])
        self.assertIs(namespace["Thing"], rebuilt.load("ExampleStock"))
        self.assertIsNot(namespace["Thing"], OldExampleStock)

    def test_the_old_class_stands_when_there_is_no_file(self):
        class OldUnrebuilt(_component.Component):
            NAME = 'UnrebuiltForThisTest'
            MACRO_LABELS = ()
            MACRO_MODES = {}
            PATCHES = {0: ("Default", ())}

        namespace = {"Thing": OldUnrebuilt}
        audioeffects._adopt(namespace, ["Thing"])
        self.assertIs(namespace["Thing"], OldUnrebuilt)

    def test_a_non_provider_in_the_namespace_is_left_alone(self):
        namespace = {"configure": audioeffects.configure}
        audioeffects._adopt(namespace, ["configure"])
        self.assertIs(namespace["configure"], audioeffects.configure)

    def test_both_bases_count_as_providers(self):
        # `_core.Effect` for the families not rebuilt yet, `Component` for
        # the ones that are; neither base itself is a provider.
        self.assertTrue(audioeffects._is_provider(audioeffects.Compressor))
        self.assertTrue(audioeffects._is_provider(rebuilt.load("ExampleStock")))
        self.assertFalse(audioeffects._is_provider(audioeffects._core.Effect))
        self.assertFalse(audioeffects._is_provider(_component.Component))
        self.assertFalse(audioeffects._is_provider(42))


class TheCatalogueIsUnchanged(unittest.TestCase):
    def test_the_fixtures_are_not_among_the_46(self):
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in rebuilt.known():
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_create_still_refuses_a_name_it_does_not_have(self):
        with self.assertRaises(ImportError):
            audioeffects.create("ExampleStock", source(), 48000)

    def test_a_rebuilt_class_builds_through_the_contract_boundary(self):
        for name in rebuilt.known():
            with self.subTest(name=name):
                cls = rebuilt.load(name)
                effect = cls.create(source(), 48000)
                try:
                    self.assertEqual(effect.sample_rate, 48000)
                    self.assertEqual(effect.channel_count, 2)
                    self.assertEqual(effect.patch_index, 0)
                    result, data = audiocore.get_buffer(effect.output)
                    self.assertTrue(len(data) > 0)
                    self.assertEqual(len(data) % (2 * effect.channel_count), 0)
                finally:
                    effect.deinit()


class TheMetadataValidatorCoversBothBases(unittest.TestCase):
    """`validate_effects` used to select on `_core.Effect` alone, so a
    rebuilt class would have been skipped in silence -- and an unvalidated
    class reads exactly like a valid one. It now selects on both bases and
    checks the count it validated against `ALL`."""

    def test_it_validates_all_46(self):
        self.assertEqual(len(validate_effects(audioeffects)),
                         len(audioeffects.ALL))

    def test_planted_fault_a_class_the_walk_never_reaches(self):
        class OneShort:
            """audioeffects with one name missing from `__all__` -- what a
            base the validator has not been taught about looks like."""

            ALL = audioeffects.ALL
            __all__ = [name for name in audioeffects.__all__
                       if name != "Compressor"]

            def __getattr__(self, name):
                return getattr(audioeffects, name)

        with self.assertRaises(MetadataError) as caught:
            validate_effects(OneShort())
        self.assertIn("were skipped", str(caught.exception))
        self.assertIn("Compressor", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
