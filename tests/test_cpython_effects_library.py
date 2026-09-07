"""The contract every class in `audioeffects.ALL` is held to.

Exports and metadata, the factory and the rate it owns, building and
rendering, chaining into each other and out of an instrument, and the patch
surface - what docs/audio-component-api.md states about the catalogue as a
whole rather than about any one effect. Nothing here names an effect for its
character, so a family phase can rebuild its classes from scratch without
touching this file: what a rebuild must not break is written here, once,
over the catalogue.

The per-class trait tests that used to sit beside these were written against
the surfaces the effects program replaces. They live in one module per
family phase now - `test_cpython_effects_dynamics_eq.py` (phase 2),
`..._modulation.py` (3), `..._drive.py` (4), `..._time.py` (5),
`..._pitch.py` and `..._racks.py` (6) - and a phase retires its own by
deleting its module, touching nothing else. `test_cpython_convolve_node.py`
holds the audioconvolve node checks, which belong to the palette.

This is also the first offline coverage the library ever had: half of it is
built on Dynamics and Splitter, which used to exist only inside a VST
plug-in's engine, so the only way to run those classes was to load the
plug-in in a host. Now they are ordinary audioif nodes and the whole
catalogue renders here.
"""

import os
import sys
import unittest

import audioeffects
import audioinstruments
from tools.validate_metadata import validate_effects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import SAMPLE_RATE, build, peak, source  # noqa: E402

#: Every name the package exports as an effect. `ALL` is the catalogue the
#: contract freezes - the provider names, computed by the package itself -
#: so these tests read it rather than deriving the set from `dir()` again.
CLASSES = audioeffects.ALL

#: The classes that carry a patch surface. Optional, and most do not yet -
#: see audioeffects._core.Effect.
PATCHABLE = tuple(name for name in CLASSES
                  if getattr(audioeffects, name).MACRO_LABELS)


class EffectsLibraryTest(unittest.TestCase):
    def test_every_public_effect_implements_the_factory_contract(self):
        validate_effects(audioeffects)
        for name in CLASSES:
            cls = getattr(audioeffects, name)
            self.assertTrue(callable(getattr(cls, "create", None)), name)
            effect = build(name)
            self.assertIsNotNone(effect.output, name)

    def test_factory_owns_the_sample_rate(self):
        original = audioeffects.sample_rate()
        try:
            effect = audioeffects.create("LowPass", source(rate=22050),
                                         22050)
            self.assertEqual(effect.output.sample_rate, 22050)
        finally:
            audioeffects.configure(original)

    def test_the_catalogue_is_all_there(self):
        self.assertEqual(len(CLASSES), 46, CLASSES)

    def test_every_effect_builds_and_renders(self):
        for name in CLASSES:
            effect = build(name)
            self.assertIsNotNone(effect.output, name)
            level = peak(effect.output, 8)
            self.assertGreater(level, 0.001, "%s renders silence" % name)

    def test_effects_chain_into_each_other(self):
        # The `.output` of one is the `source` of the next; that is the whole
        # composition rule, and the three here cover all three node kinds
        # (a plain effect, one built on a Splitter, one built on Dynamics).
        drive = audioeffects.Exciter(source(), frequency=2500.0, amount=0.4)
        comp = audioeffects.Compressor(drive.output, threshold_db=-30.0,
                                       ratio=6.0, character="optical")
        verb = audioeffects.Reverb(comp.output, preset="hall", mix=0.35)
        self.assertGreater(peak(verb.output, 12), 0.001)

    def test_an_instrument_feeds_an_effect(self):
        instrument = audioinstruments.create("tr909", SAMPLE_RATE)
        for note, _ in audioinstruments.load("tr909").NOTE_MAP[:4]:
            instrument.note_on(note)
        chain = audioeffects.TapeDelay(instrument.output, time_ms=220.0,
                                       feedback=0.4, mix=0.4)
        self.assertGreater(peak(chain.output, 12), 0.001)

    def test_configure_sets_the_rate_the_nodes_are_built_at(self):
        try:
            audioeffects.configure(22050)
            self.assertEqual(audioeffects.sample_rate(), 22050)
            slow = audioeffects.LowPass(source(rate=22050))
            self.assertEqual(slow.output.sample_rate, 22050)
        finally:
            audioeffects.configure(SAMPLE_RATE)
        self.assertEqual(audioeffects.LowPass(source()).output.sample_rate,
                         SAMPLE_RATE)

    def test_patch_zero_is_the_constructor_defaults(self):
        # Patch 0 is defined as the defaults rendered onto the 7-bit grid, so
        # this catches a default that moves without its patch following it.
        for name in PATCHABLE:
            effect = build(name)
            expected = tuple(
                int(round(position * 127)) for position in effect._macros)
            self.assertEqual(getattr(audioeffects, name).PATCHES[0][1],
                             expected, name)

    def test_every_patch_names_a_value_for_every_macro(self):
        for name in PATCHABLE:
            cls = getattr(audioeffects, name)
            for index, (patch_name, values) in sorted(cls.PATCHES.items()):
                self.assertEqual(len(values), len(cls.MACRO_LABELS),
                                 "%s patch %d" % (name, index))
                self.assertTrue(patch_name, "%s patch %d" % (name, index))
                for value in values:
                    self.assertIsInstance(value, int)
                    self.assertTrue(0 <= value <= 127,
                                    "%s patch %d" % (name, index))

    def test_every_patch_builds_and_renders(self):
        for name in PATCHABLE:
            for index in sorted(getattr(audioeffects, name).PATCHES):
                effect = build(name, patch=index)
                self.assertGreater(peak(effect.output, 8), 0.001,
                                   "%s patch %d renders silence"
                                   % (name, index))

    def test_a_macro_moves_the_thing_it_names(self):
        effect = build(PATCHABLE[0])
        for index, span in enumerate(effect._MACRO_RANGES):
            effect.set_macro(index, 127)
            self.assertAlmostEqual(effect.macro(index), span[1], delta=1e-6)
            effect.set_macro(index, 0)
            self.assertAlmostEqual(effect.macro(index), span[0], delta=1e-6)

    def test_a_macro_index_the_class_does_not_have_is_refused(self):
        # Loud, unlike an unknown program change: a host addressing a knob
        # that is not there is an application bug, not a wire message.
        effect = build(PATCHABLE[0])
        with self.assertRaises(IndexError):
            effect.set_macro(len(effect.MACRO_LABELS), 64)

    def test_a_program_change_to_a_patch_that_is_not_there_is_ignored(self):
        effect = build(PATCHABLE[0])
        before = list(effect._macros)
        effect.program_change(99)
        self.assertEqual(effect._macros, before)

    def test_a_class_without_macros_declares_an_empty_macro_surface(self):
        plain = audioeffects.Reverb(source())
        self.assertEqual(plain.MACRO_LABELS, ())
        self.assertEqual(plain.MACRO_MODES, {})
        self.assertEqual(plain.PATCHES, {0: ("Default", ())})
        with self.assertRaises(IndexError):
            plain.set_macro(0, 64)


if __name__ == "__main__":
    unittest.main()
