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


#: The two fixtures under `rebuilt/`, which are never among the 46. Every
#: other name `rebuilt.known()` reports is a class this program has actually
#: rebuilt, and the assertions below are written against the **rule** rather
#: than against the day the foundation landed -- the first rebuilt class
#: (`NoiseGate`, Phase 2) turned three of them red as written.
#: The two fixtures under `rebuilt/`, which are not among the 46 and are
#: removed at Phase 7 (audiocomponents#37). Everything else `known()` returns
#: is a real rebuilt class, and these tests must not care how many there are:
#: sixteen of them arrive in parallel, and a test that lists them by hand is
#: the shared file the registry rule exists to avoid.
FIXTURES = ("ExampleAudioif", "ExampleStock")


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

    #: Names that have been rebuilt. A rebuild adds its own name here in
    #: the same commit as its module; every other name of the 46 must still
    #: miss, which is the fallback branch this battery exists for. The
    #: roster is kept AND derived from `known()` in the test below it: the
    #: roll call catches a module that never registered, the derived form
    #: catches one registered under a name nobody listed.
    REBUILT = ("Compressor", "Limiter", "Expander", "NoiseGate", "DeEsser",
               "TransientShaper", "MultibandCompressor", "ParametricEQ",
               "GraphicEQ", "LowPass", "HighPass", "BandPass")

    def test_a_rebuilt_name_hits_and_every_other_one_misses(self):
        # Both branches over the real catalogue. When this file was written
        # `REBUILT` was empty and every name missed; Phase 2 fills it one
        # class at a time, and a name that is not in it must still resolve
        # to `None` so the old class in the family module stands.
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                if name in self.REBUILT:
                    self.assertIsNotNone(found)
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                else:
                    self.assertIsNone(found)

    def test_each_of_the_46_resolves_by_whether_it_has_a_file(self):
        # The fallback branch, over the real catalogue. It used to read
        # "every one of the 46 is a miss today", which was true only until
        # the first class was rebuilt and would have had to be edited by
        # each of the sixteen in turn -- a shared file to conflict over, in
        # the one test file whose subject is that there is no shared file.
        # The invariant that does not expire: a name with a module under
        # `rebuilt/` resolves to a Component carrying that NAME, and a name
        # without one misses, so the old class stands.
        rebuilt_names = set(rebuilt.known())
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                if name in rebuilt_names:
                    self.assertIsNotNone(found)
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                else:
                    self.assertIsNone(found)

    def test_every_name_either_misses_or_is_what_the_package_exports(self):
        # The fallback branch and the hit branch, over the real catalogue. A
        # name with no file misses, and the old class stands; a name with one
        # resolves to a Component that carries that NAME, and that is the
        # object `audioeffects.<Name>` is bound to. Neither branch is allowed
        # to be empty for the whole catalogue, so this test still says
        # something once every family has been rebuilt.
        misses = hits = 0
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                if found is None:
                    misses += 1
                    continue
                hits += 1
                self.assertTrue(issubclass(found, _component.Component))
                self.assertEqual(found.NAME, name)
                self.assertIs(getattr(audioeffects, name), found)
        self.assertEqual(misses + hits, len(audioeffects.ALL))

    def test_the_rebuilt_classes_are_what_the_registry_reports(self):
        # `known()` walks the directory; `load()` walks one name. They must
        # agree, or a file that never took effect could hide behind either.
        for name in rebuilt.known():
            with self.subTest(name=name):
                self.assertIs(rebuilt.load(name).NAME, name)

    def test_each_of_the_46_either_misses_or_resolves_to_its_own_class(self):
        # Both branches, over the real catalogue, in a form that does not
        # have to be edited again as the families are rebuilt one file at a
        # time: a name with no file misses and the old class stands; a name
        # with a file resolves to a Component carrying that same NAME, and
        # that is the object the package exports.
        #
        # (This test read `assertIsNone` for every one of the 46 while no
        # class had been rebuilt. The first rebuild turned it red, which is
        # a count going stale rather than the rule being broken -- so the
        # rule is what it holds now. Rewritten by the `Expander` rebuild,
        # 2026-09-07.)
        misses = 0
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                exported = next(cls for cls in
                                (getattr(audioeffects, attribute)
                                 for attribute in audioeffects.__all__)
                                if audioeffects._is_provider(cls)
                                and cls.NAME == name)
                if found is None:
                    misses += 1
                    self.assertTrue(issubclass(exported,
                                               audioeffects._core.Effect))
                else:
                    self.assertTrue(issubclass(found, _component.Component))
                    self.assertEqual(found.NAME, name)
                    self.assertIs(exported, found)
        # Until Phase 6 retires `_core`, the miss branch above is reached by
        # real names and not only by `NoSuchEffectAnywhere`.
        self.assertGreater(misses, 0)

    def test_every_one_of_the_46_either_misses_or_resolves_to_its_own_name(
            self):
        # Both branches, over the real catalogue. A name with no file must
        # miss, so the old class stands; a name with one must resolve to a
        # Component carrying that same NAME, and that class must be the one
        # the package exports. Asserting "everything misses" instead would
        # be an assertion about the calendar, and would have to be deleted
        # by whichever rebuild landed first.
        rebuilt_names = set(rebuilt.known())
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                if name not in rebuilt_names:
                    self.assertIsNone(found)
                    continue
                self.assertIsNotNone(found)
                self.assertEqual(found.NAME, name)
                self.assertTrue(issubclass(found, _component.Component))
                exported = [getattr(audioeffects, attribute)
                            for attribute in audioeffects.__all__
                            if getattr(getattr(audioeffects, attribute, None),
                                       "NAME", None) == name]
                self.assertEqual(exported, [found])
    def test_every_name_misses_or_resolves_to_its_own_class(self):
        # Both branches of the fallback, over the real catalogue. A name with
        # no module misses and the old class stands; a name with one resolves
        # to a Component whose NAME is that name, and that is what the
        # package exports under it. Written this way rather than as "every
        # name misses today" so that the first rebuild does not have to edit
        # this file, and the sixteenth does not have to either.
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                exported = getattr(audioeffects, name)
                if found is None:
                    self.assertTrue(issubclass(exported,
                                               audioeffects._core.Effect))
                else:
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                    self.assertIs(exported, found)

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
                         sorted(["ExampleAudioif", "ExampleStock"]
                                + list(self.REBUILT)))
        # The two fixtures are always there; anything else in the list is a
        # rebuilt member of the 46, and nothing else may appear.
        listed = sorted(rebuilt.known())
        self.assertIn("ExampleAudioif", listed)
        self.assertIn("ExampleStock", listed)
        for name in listed:
            if name not in ("ExampleAudioif", "ExampleStock"):
                self.assertIn(name, audioeffects.ALL)
        # The two fixtures are always there; the rest of the list grows by
        # one file per rebuilt class, so what is held is the property and
        # not the roll call.
        names = rebuilt.known()
        self.assertEqual(len(names), len(set(names)))
        for fixture in ("ExampleAudioif", "ExampleStock"):
            self.assertIn(fixture, names)
        for name in names:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                self.assertIsNotNone(found)
                self.assertEqual(found.NAME, name)
        # The fixtures are always there; rebuilt classes join them as they
        # land, and every name reported must have a loadable class.
        names = sorted(rebuilt.known())
        for fixture in FIXTURES:
            self.assertIn(fixture, names)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertIsNotNone(rebuilt.load(name))
        # The two fixtures are always there; a rebuilt class joins them, and
        # everything `known()` reports must load back under its own name.
        names = sorted(rebuilt.known())
        self.assertIn("ExampleAudioif", names)
        self.assertIn("ExampleStock", names)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(rebuilt.load(name).NAME, name)
        known = rebuilt.known()
        self.assertEqual(len(set(known)), len(known))
        for name in FIXTURES:
            self.assertIn(name, known)
        # Anything else there is a rebuilt member of the catalogue, never a
        # stray module.
        for name in known:
            if name not in FIXTURES:
                self.assertIn(name, audioeffects.ALL)

    def test_known_lists_what_is_there__mbc(self):
        # The two fixtures are always there; anything else in the list is a
        # rebuilt member of the 46, and nothing else may appear.
        listed = sorted(rebuilt.known())
        self.assertIn("ExampleAudioif", listed)
        self.assertIn("ExampleStock", listed)
        for name in listed:
            if name not in ("ExampleAudioif", "ExampleStock"):
                self.assertIn(name, audioeffects.ALL)

    def test_each_of_the_46_either_misses_or_resolves_to_its_own_name(self):
        # Written as "every one of the 46 is a miss today" when nothing had
        # been rebuilt; generalized on 2026-09-07, in the commit that rebuilt
        # the first of them, so it keeps holding what it was for. A name
        # either misses -- the old class stands, which is the fallback branch
        # -- or resolves to a `Component` carrying that same NAME. What it
        # may never do is resolve to something else.
        misses = []
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                if found is None:
                    misses.append(name)
                    continue
                self.assertTrue(issubclass(found, _component.Component))
                self.assertEqual(found.NAME, name)
                self.assertIs(getattr(audioeffects, name), found)
        # And the fallback branch is still exercised by the real catalogue,
        # not only by the fixtures. When the last of the 46 is rebuilt this
        # assertion is the one that has to go, deliberately (Phase 6).
        self.assertTrue(misses, "no name in ALL misses any more; the "
                                "fallback branch is now untested here")

    def test_known_lists_what_is_there__peq(self):
        # The two fixtures are always there; rebuilt classes join them as
        # each family phase lands one, so this is a subset check plus the
        # honesty check that everything listed actually resolves.
        listed = sorted(rebuilt.known())
        self.assertIn("ExampleAudioif", listed)
        self.assertIn("ExampleStock", listed)
        for name in listed:
            with self.subTest(name=name):
                self.assertEqual(rebuilt.load(name).NAME, name)

    def test_every_name_misses_or_resolves_to_its_own_class__geq(self):
        # Both branches of the fallback, over the real catalogue. A name with
        # no module misses and the old class stands; a name with one resolves
        # to a Component of that NAME, and that is what the package exports
        # under it. Written this way, and not as "every name misses today",
        # so that the first rebuild does not have to edit this file and the
        # sixteenth does not either.
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                exported = getattr(audioeffects, name)
                if found is None:
                    self.assertTrue(issubclass(exported,
                                               audioeffects._core.Effect))
                else:
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                    self.assertIs(exported, found)

    def test_known_lists_what_is_there__geq(self):
        known = rebuilt.known()
        self.assertEqual(len(set(known)), len(known))
        for name in FIXTURES:
            self.assertIn(name, known)
        # Anything else there is a rebuilt member of the catalogue, never a
        # stray module.
        for name in known:
            if name not in FIXTURES:
                self.assertIn(name, audioeffects.ALL)

    def test_every_name_either_misses_or_resolves_to_its_own_class(self):
        # The fallback branch, over the real catalogue. A name Phase 2 has
        # not reached must miss, so the old class stands; a name it has
        # reached must come back as a Component whose NAME is that name and
        # which is what the package exports. Both branches are live now
        # that the first classes are rebuilt, which is why this is no
        # longer "every name misses".
        rebuilt_names = set(rebuilt.known())
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                if name not in rebuilt_names:
                    self.assertIsNone(found)
                    continue
                self.assertIsNotNone(found)
                self.assertEqual(found.NAME, name)
                self.assertTrue(issubclass(found, _component.Component))
                self.assertIs(getattr(audioeffects, name), found)

    def test_known_lists_what_is_there__lp(self):
        # The two fixtures are always here; a rebuilt class joins them, and
        # `known()` must list every module in the directory rather than a
        # list this file keeps. So the assertion is set equality against
        # what the directory actually holds.
        import os
        here = os.path.dirname(rebuilt.__file__)
        modules = set(entry[:-3] for entry in os.listdir(here)
                      if entry.endswith(".py") and not entry.startswith("_"))
        self.assertEqual(set(name.lower() for name in rebuilt.known()),
                         modules)
        self.assertIn("ExampleStock", rebuilt.known())
        self.assertIn("ExampleAudioif", rebuilt.known())

    def test_every_name_misses_or_resolves_to_its_own_class__hp(self):
        # Both branches of the fallback, over the real catalogue. A name with
        # no module misses and the old class stands; a name with one resolves
        # to a Component of that NAME, and that is what the package exports
        # under it. Written this way, and not as "every name misses today",
        # so that the first rebuild does not have to edit this file and the
        # sixteenth does not either.
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                exported = getattr(audioeffects, name)
                if found is None:
                    self.assertTrue(issubclass(exported,
                                               audioeffects._core.Effect))
                else:
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                    self.assertIs(exported, found)

    def test_known_lists_what_is_there__hp(self):
        known = rebuilt.known()
        self.assertEqual(len(set(known)), len(known))
        for name in FIXTURES:
            self.assertIn(name, known)
        # Anything else there is a rebuilt member of the catalogue, never a
        # stray module.
        for name in known:
            if name not in FIXTURES:
                self.assertIn(name, audioeffects.ALL)

    def test_a_name_resolves_only_when_its_file_is_there(self):
        # The fallback branch, over the real catalogue. A name with a module
        # under `rebuilt/` resolves to the class in it; every other name
        # misses, and the old class in the family module stands.
        rebuilt_names = set(rebuilt.known())
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.load(name)
                if name in rebuilt_names:
                    self.assertIsNotNone(found)
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                    self.assertEqual(found.__module__,
                                     "audioeffects.rebuilt." + name.lower())
                else:
                    self.assertIsNone(found)

    def test_known_lists_what_is_there__bp(self):
        known = sorted(rebuilt.known())
        # The two fixtures are always there; everything else `known()`
        # reports is one of the 46, never a stray module.
        self.assertIn("ExampleAudioif", known)
        self.assertIn("ExampleStock", known)
        self.assertEqual(len(known), len(set(known)))
        for name in known:
            if name not in ("ExampleAudioif", "ExampleStock"):
                self.assertIn(name, audioeffects.ALL)


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
    #: The same two names as the module-level `FIXTURES`, on the class
    #: because the `ParametricEQ` rebuild's tests read them from
    #: `self`.
    FIXTURES = ("ExampleStock", "ExampleAudioif")


    def test_the_fixtures_are_not_among_the_46(self):
        # The catalogue is 46 whichever half of the library serves a name,
        # and whatever has been rebuilt: a rebuild replaces a name, it never
        # adds one. A rebuilt class is *supposed* to appear in both
        # `known()` and `ALL`; the two Example fixtures are the ones that
        # must stay outside it.
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in rebuilt.known():
            with self.subTest(name=name):
                if name in TheLookup.REBUILT:
                    self.assertIn(name, audioeffects.ALL)
                    self.assertIn(name, audioeffects.__all__)
                elif name not in ("ExampleStock", "ExampleAudioif"):
                    self.assertNotIn(name, audioeffects.ALL)
                    self.assertNotIn(name, audioeffects.__all__)
        # The catalogue keeps its size across every rebuild: a rebuilt class
        # replaces a name, it does not add one. Only the fixtures are held
        # out of it -- a rebuilt class is expected to be in it.
        for name in FIXTURES:
            self.assertIn(name, rebuilt.known())
        # The catalogue is 46 whatever has been rebuilt: a rebuilt class
        # replaces one of the 46 by NAME and does not add to them. What must
        # stay out are the two fixtures, which is what this test is for
        # (audiocomponents#37 removes them at Phase 7).
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in FIXTURES:
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

    def test_the_fixtures_are_not_among_the_46__mbc(self):
        # The catalogue is 46 whatever has been rebuilt: a rebuild replaces a
        # name, it never adds one. The two Example fixtures are the ones that
        # must stay outside it.
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__peq(self):
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in self.FIXTURES:
            self.assertIsNotNone(rebuilt.load(name))
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)
        # The catalogue does not grow when a class is rebuilt: everything
        # else under `rebuilt/` must already be one of the 46.
        for name in rebuilt.known():
            if name in self.FIXTURES:
                continue
            self.assertIn(name, audioeffects.ALL)
            self.assertIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__geq(self):
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in FIXTURES:
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__lp(self):
        # The catalogue stays 46 whichever half of the library serves a
        # name. The two fixtures are the ones that must never enter it; a
        # rebuilt class is *expected* in it, under the name it replaced.
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertIn(name, rebuilt.known())
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__hp(self):
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in FIXTURES:
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__bp(self):
        # The catalogue stays 46 whatever has been rebuilt: a rebuilt class
        # replaces one of them by NAME, and the two fixtures are reachable
        # from neither `ALL` nor `__all__`.
        self.assertEqual(len(audioeffects.ALL), 46)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)


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
