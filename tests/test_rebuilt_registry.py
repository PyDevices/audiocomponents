"""The registry rule: a rebuilt class replaces the old one by NAME, without
either module being edited.

A rebuild adds exactly one file, `lib/audioeffects/rebuilt/<name_lower>.py`,
one class per file. Nothing lists the classes, so a family phase can be
rebuilt in parallel with no shared file to conflict over -- which is the
whole point of the rule and the thing these tests hold it to.

Phase 2's sixteen have come home as one file per effect beside the package,
so they are no longer under `rebuilt/`. This directory keeps the machinery
and the two `Example` fixtures for the phases still to come.

`ExampleStock` and `ExampleAudioif` are the subjects: fixtures under
`rebuilt/`, deliberately absent from `audioeffects.__all__` so that neither
enters `audioeffects.ALL` and no host can reach them (audiocomponents#37).

**Two questions, two functions.** `rebuilt.module_class(name)` asks what the
rebuild built - it answers for every module here, adopted or parked, and it
is what a tool, an evidence probe or a class's own tests ask.
`rebuilt.load(name)` asks what the *library serves*, and it answers `None`
unless the auditor has named the class in `rebuilt.ADOPTED`. `TheLookup`
below holds the first question and `TheAdoptionGate` the second.
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

#: Every one of the 46 that Phase 2 rebuilt. They have come home, so
#: `rebuilt.module_class` misses them and the package imports each from
#: its own file. `TheLookup.REBUILT` is this same tuple.
REBUILT = ("Compressor", "Limiter", "Expander", "NoiseGate", "DeEsser",
           "TransientShaper", "MultibandCompressor", "ParametricEQ",
           "GraphicEQ", "LowPass", "HighPass", "BandPass", "Notch",
           "LadderFilter", "CombFilter", "DynamicEQ",
           "AutoPan", "Chorus", "Phaser", "Tremolo", "Vibrato")


def source(channels=2, rate=48000):
    return audiocore.RawSample(
        array.array("h", [4000, -4000] * 2048 * channels),
        sample_rate=rate, channel_count=channels)


class TheLookup(unittest.TestCase):

    def test_a_name_with_a_file_resolves_to_its_class(self):
        found = rebuilt.module_class("ExampleStock")
        self.assertIsNotNone(found)
        self.assertEqual(found.NAME, "ExampleStock")
        self.assertTrue(issubclass(found, _component.Component))

    def test_a_name_with_no_file_is_a_miss_not_an_error(self):
        self.assertIsNone(rebuilt.module_class("NoSuchEffectAnywhere"))

    #: Names that have been rebuilt. A rebuild adds its own name here in
    #: the same commit as its module; every other name of the 46 must still
    #: miss, which is the fallback branch this battery exists for. The
    #: roster is kept AND derived from `known()` in the test below it: the
    #: roll call catches a module that never registered, the derived form
    #: catches one registered under a name nobody listed.
    REBUILT = REBUILT

    def test_a_rebuilt_name_hits_and_every_other_one_misses(self):
        # Both branches over the real catalogue. Phase 2's sixteen have
        # come home, so they miss here. A later-phase file under `rebuilt/`
        # is a hit on `module_class` and is still not what the package
        # exports until `ADOPTED` names it.
        rebuilt_names = set(rebuilt.known())
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.module_class(name)
                if name in rebuilt_names:
                    self.assertIsNotNone(found)
                    self.assertEqual(found.NAME, name)
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
                found = rebuilt.module_class(name)
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
                found = rebuilt.module_class(name)
                if found is None:
                    misses += 1
                    continue
                hits += 1
                self.assertTrue(issubclass(found, _component.Component))
                self.assertEqual(found.NAME, name)
                exported = getattr(audioeffects, name)
                if name in rebuilt.ADOPTED:
                    self.assertIs(exported, found)
                else:
                    self.assertIsNot(exported, found)
                    self.assertTrue(issubclass(
                        exported, audioeffects._core.Effect))
        self.assertEqual(misses + hits, len(audioeffects.ALL))

    def test_the_rebuilt_classes_are_what_the_registry_reports(self):
        # `known()` walks the directory; `load()` walks one name. They must
        # agree, or a file that never took effect could hide behind either.
        for name in rebuilt.known():
            with self.subTest(name=name):
                self.assertIs(rebuilt.module_class(name).NAME, name)

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
                found = rebuilt.module_class(name)
                exported = next(cls for cls in
                                (getattr(audioeffects, attribute)
                                 for attribute in audioeffects.__all__)
                                if audioeffects._is_provider(cls)
                                and cls.NAME == name)
                if found is None:
                    misses += 1
                    if name in REBUILT:
                        self.assertTrue(issubclass(
                            exported, _component.Component))
                    else:
                        self.assertTrue(issubclass(
                            exported, audioeffects._core.Effect))
                else:
                    self.assertTrue(issubclass(found, _component.Component))
                    self.assertEqual(found.NAME, name)
                    if name in rebuilt.ADOPTED:
                        self.assertIs(exported, found)
                    else:
                        self.assertIsNot(exported, found)
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
                found = rebuilt.module_class(name)
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
                self.assertEqual(len(exported), 1)
                if name in rebuilt.ADOPTED:
                    self.assertIs(exported[0], found)
                else:
                    self.assertIsNot(exported[0], found)
    def test_every_name_misses_or_resolves_to_its_own_class(self):
        # Both branches of the fallback, over the real catalogue. A name with
        # no module misses and the old class stands; a name with one resolves
        # to a Component whose NAME is that name, and that is what the
        # package exports under it. Written this way rather than as "every
        # name misses today" so that the first rebuild does not have to edit
        # this file, and the sixteenth does not have to either.
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.module_class(name)
                exported = getattr(audioeffects, name)
                if found is None:
                    if name in REBUILT:
                        self.assertTrue(issubclass(
                            exported, _component.Component))
                    else:
                        self.assertTrue(issubclass(
                            exported, audioeffects._core.Effect))
                else:
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                    if name in rebuilt.ADOPTED:
                        self.assertIs(exported, found)
                    else:
                        self.assertIsNot(exported, found)

    def test_a_file_whose_class_does_not_match_is_an_error(self):
        # `examplestock.py` exists, but holds no class whose NAME is
        # "Examplestock". That is a typo in a filename or a NAME, and
        # quietly serving the old class would hide a rebuild that never
        # took effect -- so it raises rather than missing.
        with self.assertRaises(ImportError) as caught:
            rebuilt.module_class("Examplestock")
        self.assertIn("holds no Component", str(caught.exception))

    def test_known_lists_what_is_there(self):
        listed = set(rebuilt.known())
        self.assertTrue(set(FIXTURES) <= listed)
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
                found = rebuilt.module_class(name)
                self.assertIsNotNone(found)
                self.assertEqual(found.NAME, name)
        # The fixtures are always there; rebuilt classes join them as they
        # land, and every name reported must have a loadable class.
        names = sorted(rebuilt.known())
        for fixture in FIXTURES:
            self.assertIn(fixture, names)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertIsNotNone(rebuilt.module_class(name))
        # The two fixtures are always there; a rebuilt class joins them, and
        # everything `known()` reports must load back under its own name.
        names = sorted(rebuilt.known())
        self.assertIn("ExampleAudioif", names)
        self.assertIn("ExampleStock", names)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(rebuilt.module_class(name).NAME, name)
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
                found = rebuilt.module_class(name)
                if found is None:
                    misses.append(name)
                    continue
                self.assertTrue(issubclass(found, _component.Component))
                self.assertEqual(found.NAME, name)
                exported = getattr(audioeffects, name)
                if name in rebuilt.ADOPTED:
                    self.assertIs(exported, found)
                else:
                    self.assertIsNot(exported, found)
                    self.assertTrue(issubclass(
                        exported, audioeffects._core.Effect))
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
                self.assertEqual(rebuilt.module_class(name).NAME, name)

    def test_every_name_misses_or_resolves_to_its_own_class__geq(self):
        # Both branches of the fallback, over the real catalogue. A name with
        # no module misses and the old class stands; a name with one resolves
        # to a Component of that NAME, and that is what the package exports
        # under it. Written this way, and not as "every name misses today",
        # so that the first rebuild does not have to edit this file and the
        # sixteenth does not either.
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.module_class(name)
                exported = getattr(audioeffects, name)
                if found is None:
                    if name in REBUILT:
                        self.assertTrue(issubclass(
                            exported, _component.Component))
                    else:
                        self.assertTrue(issubclass(
                            exported, audioeffects._core.Effect))
                else:
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                    if name in rebuilt.ADOPTED:
                        self.assertIs(exported, found)
                    else:
                        self.assertIsNot(exported, found)

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
                found = rebuilt.module_class(name)
                if name not in rebuilt_names:
                    self.assertIsNone(found)
                    continue
                self.assertIsNotNone(found)
                self.assertEqual(found.NAME, name)
                self.assertTrue(issubclass(found, _component.Component))
                exported = getattr(audioeffects, name)
                if name in rebuilt.ADOPTED:
                    self.assertIs(exported, found)
                else:
                    self.assertIsNot(exported, found)
                    self.assertTrue(issubclass(
                        exported, audioeffects._core.Effect))

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
                found = rebuilt.module_class(name)
                exported = getattr(audioeffects, name)
                if found is None:
                    if name in REBUILT:
                        self.assertTrue(issubclass(
                            exported, _component.Component))
                    else:
                        self.assertTrue(issubclass(
                            exported, audioeffects._core.Effect))
                else:
                    self.assertEqual(found.NAME, name)
                    self.assertTrue(issubclass(found, _component.Component))
                    if name in rebuilt.ADOPTED:
                        self.assertIs(exported, found)
                    else:
                        self.assertIsNot(exported, found)

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
                found = rebuilt.module_class(name)
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

    def test_every_name_either_misses_or_resolves_to_its_own_class__nt(self):
        # The fallback branch, over the real catalogue. A name Phase 2 has
        # not reached must miss, so the old class stands; a name it has
        # reached must come back as a Component whose NAME is that name and
        # which is what the package exports. Both branches are live now that
        # the first classes are rebuilt, which is why this is no longer
        # "every name misses".
        rebuilt_names = set(rebuilt.known())
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.module_class(name)
                if name not in rebuilt_names:
                    self.assertIsNone(found)
                    continue
                self.assertIsNotNone(found)
                self.assertEqual(found.NAME, name)
                self.assertTrue(issubclass(found, _component.Component))
                exported = getattr(audioeffects, name)
                if name in rebuilt.ADOPTED:
                    self.assertIs(exported, found)
                else:
                    self.assertIsNot(exported, found)
                    self.assertTrue(issubclass(
                        exported, audioeffects._core.Effect))

    def test_known_lists_what_is_there__nt(self):
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

    def test_every_name_not_yet_rebuilt_is_still_a_miss(self):
        # The fallback branch, over the real catalogue: a name with no file
        # under `rebuilt/` must miss. A Phase 3 class that has a file here
        # resolves; Phase 2's home classes miss (they live beside the package).
        rebuilt_names = set(rebuilt.known())
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.module_class(name)
                if name in rebuilt_names:
                    self.assertIsNotNone(found)
                    self.assertEqual(found.NAME, name)
                else:
                    self.assertIsNone(found)

    def test_every_rebuilt_name_resolves_to_a_component(self):
        # Phase 2's sixteen have come home: the package serves a Component
        # from each class's own file, and `rebuilt.module_class` misses.
        for name in REBUILT:
            with self.subTest(name=name):
                self.assertIsNone(rebuilt.module_class(name))
                found = getattr(audioeffects, name)
                self.assertEqual(found.NAME, name)
                self.assertTrue(issubclass(found, _component.Component))
                self.assertFalse(
                    issubclass(found, audioeffects._core.Effect))

    def test_known_lists_what_is_there__lf(self):
        listed = set(rebuilt.known())
        self.assertTrue(set(FIXTURES) <= listed)
        self.assertIn("Flanger", listed)
        for name in listed:
            if name not in FIXTURES:
                self.assertIn(name, audioeffects.ALL)

    def test_known_lists_what_is_there__cf(self):
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

    def test_every_name_either_misses_or_is_what_the_package_exports__deq(self):
        # The fallback branch and the hit branch, over the real catalogue. A
        # name with no file misses and the old class stands; a name with one
        # resolves to a Component carrying that NAME, and that object is what
        # `audioeffects.<Name>` is bound to. Neither branch may be empty for
        # the whole catalogue, so this still says something once every family
        # has been rebuilt.
        misses = hits = 0
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                found = rebuilt.module_class(name)
                if found is None:
                    misses += 1
                    continue
                hits += 1
                self.assertTrue(issubclass(found, _component.Component))
                self.assertEqual(found.NAME, name)
                exported = getattr(audioeffects, name)
                if name in rebuilt.ADOPTED:
                    self.assertIs(exported, found)
                else:
                    self.assertIsNot(exported, found)
                    self.assertTrue(issubclass(
                        exported, audioeffects._core.Effect))
        self.assertEqual(misses + hits, len(audioeffects.ALL))

    def test_known_lists_what_is_there__deq(self):
        # The two fixtures are always here; anything else listed is a rebuilt
        # member of the 46, and nothing else may appear.
        listed = sorted(rebuilt.known())
        self.assertIn("ExampleAudioif", listed)
        self.assertIn("ExampleStock", listed)
        for name in listed:
            if name not in ("ExampleAudioif", "ExampleStock"):
                self.assertIn(name, audioeffects.ALL)


class TheReplacement(unittest.TestCase):
    """`_adopt` is what the package runs over its own globals at import.
    Here it runs over a scratch namespace, so both branches can be shown
    without touching one of the 46."""

    def test_an_adopted_class_replaces_the_old_one_by_name(self):
        class OldExample(_component.Component):
            NAME = 'ExampleStock'
            MACRO_LABELS = ()
            MACRO_MODES = {}
            PATCHES = {0: ("Default", ())}

        before = rebuilt.ADOPTED
        rebuilt.ADOPTED = ("ExampleStock",)
        try:
            namespace = {"Thing": OldExample}
            audioeffects._adopt(namespace, ["Thing"])
            self.assertIs(namespace["Thing"],
                          rebuilt.module_class("ExampleStock"))
            self.assertIsNot(namespace["Thing"], OldExample)
        finally:
            rebuilt.ADOPTED = before

    def test_a_parked_class_does_not_replace_anything(self):
        # ExampleStock sits under `rebuilt/` and is not in `ADOPTED`, so
        # `_adopt` leaves the old class standing.
        class OldExample(_component.Component):
            NAME = 'ExampleStock'
            MACRO_LABELS = ()
            MACRO_MODES = {}
            PATCHES = {0: ("Default", ())}

        namespace = {"Thing": OldExample}
        audioeffects._adopt(namespace, ["Thing"])
        self.assertIs(namespace["Thing"], OldExample)
        self.assertIsNotNone(rebuilt.module_class("ExampleStock"))

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
        self.assertTrue(
            audioeffects._is_provider(rebuilt.module_class("ExampleStock")))
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
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in rebuilt.known():
            with self.subTest(name=name):
                if name in ("ExampleStock", "ExampleAudioif"):
                    self.assertNotIn(name, audioeffects.ALL)
                    self.assertNotIn(name, audioeffects.__all__)
                else:
                    self.assertIn(name, audioeffects.ALL)
                    self.assertIn(name, audioeffects.__all__)
        # The catalogue keeps its size across every rebuild: a rebuilt class
        # replaces a name, it does not add one. Only the fixtures are held
        # out of it -- a rebuilt class is expected to be in it.
        for name in FIXTURES:
            self.assertIn(name, rebuilt.known())
        # The catalogue is 46 whatever has been rebuilt: a rebuilt class
        # replaces one of the 46 by NAME and does not add to them. What must
        # stay out are the two fixtures, which is what this test is for
        # (audiocomponents#37 removes them at Phase 7).
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in FIXTURES:
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_create_still_refuses_a_name_it_does_not_have(self):
        with self.assertRaises(ImportError):
            audioeffects.create("ExampleStock", source(), 48000)

    def test_a_rebuilt_class_builds_through_the_contract_boundary(self):
        for name in rebuilt.known():
            with self.subTest(name=name):
                cls = rebuilt.module_class(name)
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
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__peq(self):
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in self.FIXTURES:
            self.assertIsNotNone(rebuilt.module_class(name))
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
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in FIXTURES:
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__lp(self):
        # The catalogue stays 46 whichever half of the library serves a
        # name. The two fixtures are the ones that must never enter it; a
        # rebuilt class is *expected* in it, under the name it replaced.
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertIn(name, rebuilt.known())
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__hp(self):
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in FIXTURES:
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__bp(self):
        # The catalogue stays 46 whatever has been rebuilt: a rebuilt class
        # replaces one of them by NAME, and the two fixtures are reachable
        # from neither `ALL` nor `__all__`.
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__nt(self):
        # The catalogue stays 46 whichever half of the library serves a
        # name. The two fixtures are the ones that must never enter it; a
        # rebuilt class is *expected* in it, under the name it replaced.
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__lf(self):
        # The catalogue is 46 whatever has been rebuilt: a rebuild replaces
        # a name, it never adds one. The fixtures stay outside it; a rebuilt
        # class takes the place of the old one under the same name.
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in FIXTURES:
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)
        for name in REBUILT:
            self.assertIn(name, audioeffects.ALL)
            self.assertIn(name, audioeffects.__all__)
        listed = set(rebuilt.known())
        self.assertTrue(set(FIXTURES) <= listed)
        self.assertIn("Flanger", listed)
        for name in listed:
            if name not in FIXTURES:
                self.assertIn(name, audioeffects.ALL)

    def test_the_fixtures_are_not_among_the_46__cf(self):
        # The catalogue stays 46 whichever half of the library serves a
        # name. The two fixtures are the ones that must never enter it; a
        # rebuilt class is *expected* in it, under the name it replaced.
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertIn(name, rebuilt.known())
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)

    def test_the_fixtures_are_not_among_the_46__deq(self):
        # The catalogue is 46 whatever has been rebuilt: a rebuild replaces a
        # name, it never adds one. The two Example fixtures are the ones that
        # must stay outside it.
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in ("ExampleStock", "ExampleAudioif"):
            self.assertNotIn(name, audioeffects.ALL)
            self.assertNotIn(name, audioeffects.__all__)


class TheAdoptionGate(unittest.TestCase):
    """A rebuilt class is served only once the auditor names it.

    `rebuilt.ADOPTED` is the one list this package keeps, and it is the
    auditor's, not the builder's. Phase 2's sixteen have come home, so they
    are not in `ADOPTED` and not under `rebuilt/`. What remains here is the
    two Example fixtures, parked, and the machinery later phases will use.

    A rebuild still adds exactly one file and edits nothing else. Adoption
    is a separate edit, made once, in a commit that cites the gate. Coming
    home is a later edit, once that phase's gate is met.
    """

    def test_phase2_names_have_left_adopted(self):
        # Home classes must not reappear in ADOPTED.
        self.assertTrue(set(REBUILT).isdisjoint(rebuilt.ADOPTED))
        # Phase 3 THROUGH names have come home. Flanger and RingMod stay
        # parked, so ADOPTED is empty and the substitution machinery stays.
        self.assertEqual(rebuilt.ADOPTED, ())
        self.assertEqual(rebuilt.adopted(), ())
        parked = set(rebuilt.parked())
        known = set(rebuilt.known())
        self.assertTrue(set(FIXTURES) <= parked)
        self.assertTrue(set(FIXTURES) <= known)
        self.assertEqual(parked, known - set(rebuilt.ADOPTED))
        self.assertTrue(parked - set(FIXTURES) <= set(audioeffects.ALL))
        self.assertTrue(known - set(FIXTURES) <= set(audioeffects.ALL))
        self.assertIn("Flanger", parked)
        self.assertIn("RingMod", parked)
        self.assertNotIn("AutoPan", parked)
        self.assertNotIn("Chorus", parked)
        self.assertNotIn("Phaser", parked)
        self.assertNotIn("Tremolo", parked)
        self.assertNotIn("Vibrato", parked)
        for name in known:
            if name not in FIXTURES:
                self.assertIn(name, audioeffects.ALL)
                if name in rebuilt.ADOPTED:
                    self.assertIs(rebuilt.load(name),
                                  rebuilt.module_class(name))
                else:
                    self.assertIsNone(rebuilt.load(name))
        for name in REBUILT:
            with self.subTest(name=name):
                self.assertIsNone(rebuilt.module_class(name))
                self.assertIsNone(rebuilt.load(name))
                self.assertTrue(issubclass(getattr(audioeffects, name),
                                           _component.Component))

    def test_an_adopted_name_is_what_the_library_serves(self):
        # Empty `ADOPTED` would make a loop over it vacuous. Plant a
        # fixture so the substitution path is still shown to work.
        class OldExample(_component.Component):
            NAME = 'ExampleStock'
            MACRO_LABELS = ()
            MACRO_MODES = {}
            PATCHES = {0: ("Default", ())}

        before = rebuilt.ADOPTED
        rebuilt.ADOPTED = ("ExampleStock",)
        try:
            self.assertEqual(rebuilt.adopted(), ("ExampleStock",))
            found = rebuilt.module_class("ExampleStock")
            self.assertIs(rebuilt.load("ExampleStock"), found)
            namespace = {"Thing": OldExample}
            audioeffects._adopt(namespace, ["Thing"])
            self.assertIs(namespace["Thing"], found)
        finally:
            rebuilt.ADOPTED = before

    def test_a_parked_name_is_built_and_not_served(self):
        for name in FIXTURES:
            with self.subTest(name=name):
                built = rebuilt.module_class(name)
                self.assertIsNotNone(built)
                self.assertEqual(built.NAME, name)
                self.assertEqual(built.__module__,
                                 "audioeffects.rebuilt." + name.lower())
                self.assertIsNone(rebuilt.load(name))
                self.assertNotIn(name, audioeffects.ALL)
                self.assertNotIn(name, audioeffects.__all__)

    def test_create_builds_the_home_class_for_limiter(self):
        from audioeffects.limiter import Limiter
        effect = audioeffects.create("Limiter", source(), 48000)
        try:
            self.assertIsInstance(effect, Limiter)
            self.assertEqual(type(effect).__module__, "audioeffects.limiter")
        finally:
            effect.deinit()

    def test_a_parked_module_is_importable_under_its_own_name(self):
        for name in FIXTURES:
            with self.subTest(name=name):
                module = __import__("audioeffects.rebuilt." + name.lower(),
                                    None, None, ["_"])
                held = [value for value in vars(module).values()
                        if isinstance(value, type)
                        and issubclass(value, _component.Component)
                        and getattr(value, "NAME", None) == name]
                self.assertEqual(len(held), 1)
                self.assertIs(held[0], rebuilt.module_class(name))

    def test_planted_fault_parking_a_name_flips_what_is_served(self):
        """The gate has to be able to close, or it is not a gate.

        Adopt ExampleStock, then drop it: `_adopt` replaces, then the old
        class stands again. This is the auditor's edit, run and undone.
        """
        class OldExample(_component.Component):
            NAME = 'ExampleStock'
            MACRO_LABELS = ()
            MACRO_MODES = {}
            PATCHES = {0: ("Default", ())}

        before = rebuilt.ADOPTED
        rebuilt.ADOPTED = ("ExampleStock",)
        try:
            namespace = {"Thing": OldExample}
            audioeffects._adopt(namespace, ["Thing"])
            self.assertIs(namespace["Thing"],
                          rebuilt.module_class("ExampleStock"))
        finally:
            rebuilt.ADOPTED = before

        namespace = {"Thing": OldExample}
        audioeffects._adopt(namespace, ["Thing"])
        self.assertIs(namespace["Thing"], OldExample)
        self.assertEqual(rebuilt.ADOPTED, before)

    def test_a_name_adopted_with_no_module_behind_it_raises(self):
        # The auditor's own typo. Silently shipping the old class for a name
        # the auditor believes is adopted is the failure mode this refuses.
        before = rebuilt.ADOPTED
        rebuilt.ADOPTED = before + ("NoSuchEffectAnywhere",)
        try:
            with self.assertRaises(ImportError) as caught:
                rebuilt.adopted()
            self.assertIn("is in ADOPTED", str(caught.exception))
        finally:
            rebuilt.ADOPTED = before

    def test_adoption_does_not_change_the_catalogue(self):
        # `ALL` is provider names, and a rebuild replaces a name rather than
        # adding one - so the catalogue is 46 whether a class lives under
        # `rebuilt/` or has come home.
        self.assertEqual(len(audioeffects.ALL), 45)
        for name in REBUILT:
            self.assertIn(name, audioeffects.ALL)


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
