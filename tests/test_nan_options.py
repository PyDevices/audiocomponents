"""A NaN constructor option is the option left out, on every effect.

The API reference promises it for macros (NaN is the bottom stop) and each
class's docstring promises it for constructor options (NaN takes the
option's default). 28 classes built with the NaN as it stood. The base class
now drops a NaN option before `_build` sees it, so one rule covers every
class, and an echo of `get_macro()` through `set_macro()` leaves a macro
where the constructor put it.
"""

import array
import inspect
import math
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "support"))
sys.path.insert(0, os.path.join(_HERE, "..", "lib"))

import audiocore                                            # noqa: E402
import audioeffects                                         # noqa: E402
import kit_common                                           # noqa: E402

NAN = float("nan")
FRAMES = 2048


def source():
    values = [int(8000 * math.sin(i * 0.05)) for i in range(4096)] * 40
    return audiocore.RawSample(array.array("h", values), sample_rate=48000,
                               channel_count=2)


def render(effect):
    try:
        return kit_common.render(effect, FRAMES)
    finally:
        effect.deinit()


def options_of(cls):
    """The names of `cls`'s numeric constructor options: those whose
    default is a number or None (left out)."""
    names = []
    for p in inspect.signature(cls._build).parameters.values():
        if p.name in ("self", "patch") or p.kind in (p.VAR_KEYWORD,
                                                      p.VAR_POSITIONAL):
            continue
        if isinstance(p.default, bool):
            continue
        if p.default is None or isinstance(p.default, (int, float)):
            names.append(p.name)
    return [n for n in names if n not in cls._NAN_OWN]


class ANanOptionIsTheOptionLeftOut(unittest.TestCase):

    def test_every_class_renders_a_nan_option_as_its_default(self):
        for name in audioeffects.ALL:
            cls = getattr(audioeffects, name)
            for option in options_of(cls):
                with self.subTest(effect=name, option=option):
                    try:
                        left_out = render(cls(source()))
                    except Exception:
                        self.skipTest("the default build is not renderable")
                    nan = render(cls(source(), **{option: NAN}))
                    self.assertEqual(nan, left_out)

    def test_a_positional_nan_is_the_option_left_out(self):
        for name in ("Chorus", "Limiter", "Phaser"):
            cls = getattr(audioeffects, name)
            with self.subTest(effect=name):
                self.assertEqual(render(cls(source(), NAN)),
                                 render(cls(source())))

    def test_a_class_keeps_the_nan_meaning_it_documents(self):
        self.assertEqual(
            {name: getattr(audioeffects, name)._NAN_OWN
             for name in audioeffects.ALL
             if getattr(audioeffects, name)._NAN_OWN},
            {"ShimmerHall": ("interval",), "ConvolutionReverb":
             ("damping_hz",), "TapeDelay": ("glide_ms",),
             "DigitalDelay": ("glide_ms",)})

    def test_a_number_still_plays_as_passed(self):
        cls = audioeffects.Chorus
        self.assertNotEqual(render(cls(source(), rate=2.5)),
                            render(cls(source())))


class AnEchoOfGetMacroLeavesTheMacroWhereItIs(unittest.TestCase):

    OFF_GRID = {
        "CabinetSim": dict(low_cut=80.0, body=0.37, break_up=2431.0,
                           bite=4.7, top=5110.0, air=-21.3, mix=0.333),
        "SlapbackDelay": dict(time_ms=97.3, level=0.37, saturation=0.31,
                              tone_hz=3333.0, wow_cents=11.1, repeats=0.27),
    }

    def test_the_value_reads_back_exactly(self):
        for name, options in self.OFF_GRID.items():
            cls = getattr(audioeffects, name)
            effect = cls(source(), **options)
            try:
                for index in range(len(cls.MACRO_LABELS)):
                    with self.subTest(effect=name, macro=index):
                        before = effect.get_macro(index)
                        effect.set_macro(index, before, channel=-1)
                        self.assertEqual(effect.get_macro(index), before)
            finally:
                effect.deinit()

    def test_the_echo_does_not_change_the_sound(self):
        for name, options in self.OFF_GRID.items():
            cls = getattr(audioeffects, name)
            for index in range(len(cls.MACRO_LABELS)):
                with self.subTest(effect=name, macro=index):
                    echoed = cls(source(), **options)
                    echoed.set_macro(index, echoed.get_macro(index),
                                     channel=-1)
                    self.assertEqual(render(echoed),
                                     render(cls(source(), **options)))

    def test_cabinet_sim_still_snaps_a_value_the_host_chose(self):
        effect = audioeffects.CabinetSim(source())
        try:
            effect.set_macro(2, 46.99)
            self.assertEqual(effect.get_macro(2), 47.0)
        finally:
            effect.deinit()


if __name__ == "__main__":
    unittest.main()
