"""The effects catalogue: what `audioeffects` serves and how `create()`
finds it.

`ALL` is the package's provider names, `create()` builds one of them by
name, and the metadata validator walks every one. These used to sit beside
the registry tests that arbitrated between a class under `rebuilt/` and an
older one; every class has one home now, so only the catalogue's own
promises are left to hold.
"""

import array
import unittest

import audiocore
import audioeffects
from audioeffects import _component
from tools.validate_metadata import MetadataError, validate_effects


def source(channels=2, rate=48000):
    return audiocore.RawSample(
        array.array("h", [4000, -4000] * 2048 * channels),
        sample_rate=rate, channel_count=channels)


class TheCatalogue(unittest.TestCase):

    def test_it_holds_45_names(self):
        self.assertEqual(len(audioeffects.ALL), 45)
        self.assertEqual(len(set(audioeffects.ALL)), 45)

    def test_every_name_is_a_provider_the_package_exports(self):
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                cls = getattr(audioeffects, name)
                self.assertTrue(audioeffects._is_provider(cls))
                self.assertEqual(cls.NAME, name)

    def test_only_components_with_a_name_are_providers(self):
        self.assertTrue(audioeffects._is_provider(audioeffects.Compressor))
        self.assertFalse(audioeffects._is_provider(_component.Component))
        self.assertFalse(audioeffects._is_provider(42))

    def test_create_refuses_a_name_it_does_not_have(self):
        with self.assertRaises(ImportError):
            audioeffects.create("NoSuchEffect", source(), 48000)

    def test_create_builds_the_class_it_exports(self):
        served = audioeffects.create("Limiter", source(), 48000)
        try:
            self.assertIsInstance(served, audioeffects.Limiter)
        finally:
            served.deinit()


class TheMetadataValidatorCoversEveryClass(unittest.TestCase):
    """`validate_effects` used to select on `_core.Effect` alone, so a
    rebuilt class would have been skipped in silence -- and an unvalidated
    class reads exactly like a valid one. It selects on `Component` now that
    `_core` is retired, and checks the count it validated against `ALL`."""

    def test_it_validates_all_45(self):
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
