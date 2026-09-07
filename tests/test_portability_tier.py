"""The portability tier, tested where it can be tested.

Roadmap section 3 gives every class one of two tiers:

**stock** -- built from CircuitPython-ported nodes only, so it runs on a
stock CircuitPython board. **audioif** -- needs at least one audioif-own
node (`audioecho`, `audiodynamics`, `audiomath`, `audioroute`,
`audioconvolve`, or one of the modules D1 added), so it runs on
MicroPython, CPython and the patched CircuitPython build, and on a stock
board imports cleanly and raises a clear `ImportError` at construction while
the other classes in its module stay importable.

**No stock CircuitPython interpreter exists in this workspace** --
`cmods/bin/circuitpython` is the patched oracle and
`cmods/bin/circuitpython-effects` is the patched effects build -- so the
roadmap names this substitute: a CPython test that blocks the audioif-own
modules in `sys.modules`, then holds every stock-tier class to building and
rendering and every audioif-tier class to its documented `ImportError`.

What that substitute does **not** prove is in this file's own "what is not
done" line, and in every evidence pack that cites it: blocking a module in
`sys.modules` is not a board without the module. A stock CircuitPython
`audiofilters` is a different C build from audioif's, and only a stock board
can show a stock-tier class actually rendering on one.

The battery runs over the classes that declare a tier today and grows on its
own as classes are rebuilt: it walks `audioeffects.ALL` for the rebuilt
half of the library and `rebuilt.known()` for everything under `rebuilt/`.
`test_the_battery_holds_a_subject_in_each_tier` is what keeps it from
passing by having nothing to hold.
"""

import array
import sys
import unittest

import audiocore
import audioeffects
from audioeffects import _component
from audioeffects import rebuilt

#: `_component` reads VENDOR off the defining module, and the planted-fault
#: class below is defined here.
VENDOR = "PyDevices"


def source(channels=2, rate=48000):
    return audiocore.RawSample(
        array.array("h", [4000, -4000] * 2048 * channels),
        sample_rate=rate, channel_count=channels)


def subjects():
    """Every class that declares a portability tier today.

    The shipped catalogue first, so a rebuilt class is covered the moment it
    replaces one of the 46; then everything under `rebuilt/`, which picks up
    the fixtures and any class not yet adopted into `__all__`.
    """
    found = {}
    for name in audioeffects.ALL:
        for exported in audioeffects.__all__:
            candidate = getattr(audioeffects, exported, None)
            if (isinstance(candidate, type)
                    and issubclass(candidate, _component.Component)
                    and getattr(candidate, "NAME", None) == name):
                found[name] = candidate
    for name in rebuilt.known():
        found.setdefault(name, rebuilt.load(name))
    return found


class BlockedModules:
    """The audioif-own modules, made unimportable for the duration.

    `None` in `sys.modules` is the interpreter's own "blocked" marker: a
    later `import` of that name raises `ImportError` rather than finding the
    module that is still loaded. That is what makes this test independent of
    import order -- a class module whose guarded import already succeeded is
    held to its tier just the same, because `_component._require_modules()`
    imports the module for itself at construction rather than reading the
    `None` the guard left behind.
    """

    def __enter__(self):
        self.saved = {}
        for name in _component.AUDIOIF_MODULES:
            self.saved[name] = sys.modules.get(name)
            sys.modules[name] = None
        return self

    def __exit__(self, *error):
        for name, module in self.saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        return False


class PortabilityTierTests(unittest.TestCase):
    def setUp(self):
        self.subjects = subjects()

    def tiers(self, tier):
        return {name: cls for name, cls in self.subjects.items()
                if cls.TIER == tier}

    def test_the_battery_holds_a_subject_in_each_tier(self):
        # Without this, a battery over an empty catalogue passes, and
        # "absence reads as agreement" is exactly how a tier check stops
        # checking. It fails loudly when the last subject in a tier goes.
        self.assertTrue(self.tiers(_component.STOCK),
                        "no stock-tier class to hold")
        self.assertTrue(self.tiers(_component.AUDIOIF),
                        "no audioif-tier class to hold")

    def test_every_class_declares_one_of_the_two_tiers(self):
        for name, cls in self.subjects.items():
            with self.subTest(name=name):
                self.assertIn(cls.TIER, (_component.STOCK,
                                         _component.AUDIOIF))
                if cls.TIER == _component.AUDIOIF:
                    self.assertTrue(cls.REQUIRES)
                    for module in cls.REQUIRES:
                        self.assertIn(module, _component.AUDIOIF_MODULES)
                else:
                    self.assertEqual(cls.REQUIRES, ())

    def test_stock_tier_classes_build_and_render_with_audioif_blocked(self):
        with BlockedModules():
            for name, cls in self.tiers(_component.STOCK).items():
                with self.subTest(name=name):
                    effect = cls.create(source(), 48000)
                    try:
                        result, data = audiocore.get_buffer(effect.output)
                        self.assertTrue(len(data) > 0)
                        self.assertEqual(len(data) %
                                         (2 * effect.channel_count), 0)
                    finally:
                        effect.deinit()

    def test_audioif_tier_classes_raise_a_clear_import_error(self):
        with BlockedModules():
            for name, cls in self.tiers(_component.AUDIOIF).items():
                with self.subTest(name=name):
                    with self.assertRaises(ImportError) as caught:
                        cls.create(source(), 48000)
                    message = str(caught.exception)
                    self.assertIn(cls.NAME, message)
                    self.assertIn(cls.REQUIRES[0], message)
                    self.assertIn("stock CircuitPython board", message)

    def test_control_the_same_audioif_classes_build_when_nothing_is_blocked(
            self):
        # The control beside the battery. Without it, a class that cannot be
        # built at all would read as a passing tier check.
        for name, cls in self.tiers(_component.AUDIOIF).items():
            with self.subTest(name=name):
                effect = cls.create(source(), 48000)
                try:
                    result, data = audiocore.get_buffer(effect.output)
                    self.assertTrue(len(data) > 0)
                finally:
                    effect.deinit()

    def test_planted_fault_a_stock_class_that_reaches_for_audioif(self):
        # A class mis-declared as stock while building on an audioif-own
        # node: the block must turn it red rather than let the tier claim
        # stand. This is the shape a wrong dossier line would take.
        class MislabelledStock(_component.Component):
            NAME = 'MislabelledStock'
            TIER = _component.STOCK
            REQUIRES = ()
            MACRO_LABELS = ()
            MACRO_MODES = {}
            _MACRO_RANGES = ()
            PATCHES = {0: ("Default", ())}

            def _build(self):
                import audioecho
                node = self._own(audioecho.FeedbackDelay(
                    sample_rate=self._sample_rate,
                    channel_count=self._channel_count,
                    max_delay_ms=50.0))
                node.play(self._source)
                self._output = node

        effect = MislabelledStock.create(source(), 48000)
        effect.deinit()                      # green with nothing blocked
        with BlockedModules():
            with self.assertRaises(ImportError):
                MislabelledStock.create(source(), 48000)

    def test_blocking_is_undone(self):
        with BlockedModules():
            pass
        import audioecho
        self.assertIsNotNone(audioecho)


if __name__ == "__main__":
    unittest.main()
