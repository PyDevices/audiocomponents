"""The kit's planted faults: tiny components that each break one thing a
kit check measures, beside the controls that break nothing.

`tests/test_kit.py` holds every plant red on its cell and its control
green on the same cell. Each is an `audioshaper.Waveshaper` (a table and a
level) around the borrowed source, with an `audioecho.FeedbackDelay` after
it for the tail plants, so they render fast on every interpreter.
"""

import sys

try:
    from array import array
except ImportError:                                   # pragma: no cover
    array = None

from audioeffects import _component

#: `_component` reads VENDOR off the module a class is defined in.
VENDOR = "PyDevices"


def _curve(fn):
    """A Q15 Waveshaper table of 4097 points over the int16 input."""
    table = array("h", bytes(2 * 4097))
    for i in range(4097):
        table[i] = max(-32768, min(32767, fn((i - 2048) * 16)))
    return table


def _same(x):
    return x


def _wrap2(x):
    y = 2 * x
    while y > 32767:
        y -= 65536
    while y < -32768:
        y += 65536
    return y


def _clip2(x):
    return 2 * x


def _dc9(x):
    return x + 9


def _nothing(x):
    return 0


class KitPlain(_component.Component):
    """The control: the source through a straight table at a level of
    1 - Mix + Mix x Gain, Gain from 0.25 to 1, so no knob position is
    silent and none goes past unity."""
    NAME = "KitPlain"
    TIER = _component.AUDIODSP
    REQUIRES = ("audioroute", "audioshaper")
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0
    MACRO_LABELS = ("Mix", "Gain")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (0.25, 1.0))
    PATCHES = {0: ("Unity", (127, 127)), 1: ("Soft", (127, 96))}
    CURVE = staticmethod(_same)

    def _build(self, mix=1.0, gain=1.0, patch=None):
        import audioshaper
        self._shaper = self._own(audioshaper.Waveshaper(
            curve=_curve(type(self).CURVE), oversample=1,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._arm()
        self._macros = [0.0, 0.0]
        self._init_macros((mix, gain), patch)

    def _arm(self):
        self._shaper.play(self._source)
        self._output = self._shaper

    def _level(self):
        mix = self.macro(0)
        return 1.0 - mix + mix * self.macro(1)

    def _apply_macro(self, index, position):
        self._shaper.set(post_gain=self._level())


class Silent(KitPlain):
    """A class that does nothing at all: every check must tell it from a
    pass."""
    NAME = "Silent"
    CURVE = staticmethod(_nothing)


# -- the input ceiling -------------------------------------------------------


class WrapKit(KitPlain):
    """Ceiling: twice the input, wrapped round int16 as a missing clamp
    would."""
    NAME = "WrapKit"
    CURVE = staticmethod(_wrap2)


class WrapKitQuiet(WrapKit):
    """The same class stating a level it is clean at: 7 dB down, where
    twice the input stays inside int16."""
    NAME = "WrapKitQuiet"
    INPUT_CEILING_DBFS = -7


class ClipKit(KitPlain):
    """Ceiling: twice the input, clamped, so a loud input sits on the
    rail."""
    NAME = "ClipKit"
    CURVE = staticmethod(_clip2)


class DeadStop(KitPlain):
    """Ceiling: Gain's bottom stop is silence, as a level that went NaN on
    a board would be."""
    NAME = "DeadStop"

    def _level(self):
        if self._macros[1] == 0.0:
            return 0.0
        return KitPlain._level(self)


class ImplKit(KitPlain):
    """P6: the level is a hair different off CPython, so every render
    check prints other bytes natively."""
    NAME = "ImplKit"

    def _level(self):
        level = KitPlain._level(self)
        if sys.implementation.name != "cpython":
            level = level * 0.99
        return level


# -- the tail ---------------------------------------------------------------


class EchoTail(KitPlain):
    """One repeat 20 ms after the input, nothing dry, and a tail that says
    so (2048 frames covers 20 ms at 48 and 22.05 kHz)."""
    NAME = "EchoTail"
    TAIL_SAMPLES = 2048
    REQUIRES = ("audioroute", "audioshaper", "audioecho")

    def _build(self, mix=1.0, gain=1.0, patch=None):
        import audioecho
        self._delay = self._own(audioecho.FeedbackDelay(
            max_delay_ms=50, delay_ms=20, feedback=0.0, mix=1.0,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        KitPlain._build(self, mix, gain, patch)

    def _arm(self):
        self._shaper.play(self._source)
        self._delay.play(self._shaper)
        self._output = self._delay


class ShortTail(EchoTail):
    """Tail: `tail_samples` 0 under a 20 ms repeat."""
    NAME = "ShortTail"
    TAIL_SAMPLES = 0


class EventTail(EchoTail):
    """Tail: right at construction, 0 after any control move, though the
    repeat never changes."""
    NAME = "EventTail"

    @property
    def tail_samples(self):
        self._check_live()
        return 0 if getattr(self, "_moved", False) else 2048

    def set_macro(self, index, value, *args, **kw):
        EchoTail.set_macro(self, index, value, *args, **kw)
        self._moved = True

    def program_change(self, index, *args, **kw):
        EchoTail.program_change(self, index, *args, **kw)
        if not self._constructing:
            self._moved = True


class NoneSilent(EchoTail):
    """Tail: reports no bound, and falls silent 20 ms after the input."""
    NAME = "NoneSilent"
    TAIL_SAMPLES = None


class NoneDC(KitPlain):
    """Tail: reports no bound, and never falls silent (a DC of 9)."""
    NAME = "NoneDC"
    TAIL_SAMPLES = None
    CURVE = staticmethod(_dc9)


# -- plant validity ------------------------------------------------------------


class Inert(KitPlain):
    """Plants: a plant that changes nothing."""


class KnobReach(KitPlain):
    """Plants: Gain stuck at its bottom stop, which the knob reaches."""

    def _level(self):
        mix = self.macro(0)
        return 1.0 - mix + mix * 0.25


class DCOffset(KitPlain):
    """Plants: a DC of 9 under the output, which no knob reaches."""
    CURVE = staticmethod(_dc9)


class SoftOnly(KitPlain):
    """Plants: a fault only patch 1 shows (its Gain read a step low)."""

    def _level(self):
        if self._patch_index == 1:
            mix = self.macro(0)
            return 1.0 - mix + mix * (0.25 + 0.75 * 95.0 / 127.0)
        return KitPlain._level(self)

    def program_change(self, index, *args, **kw):
        KitPlain.program_change(self, index, *args, **kw)
        self._apply_macro(1, self._macros[1])


#: KitPlain's plants, the way a class's test module declares them: a
#: label to a plant, or to (plant, the patch it is judged at).
KIT_PLANTS = {"inert": Inert, "knob": KnobReach, "valid": DCOffset,
              "soft": (SoftOnly, 1), "soft-at-d": SoftOnly}


# -- readback and arguments ---------------------------------------------------


class ReadbackOff(KitPlain):
    """Args: get_macro reads half a step under where the knob is."""
    NAME = "ReadbackOff"

    def get_macro(self, index):
        return KitPlain.get_macro(self, index) - 0.5


class StopRaises(KitPlain):
    """Args: the top stop is refused."""
    NAME = "StopRaises"

    def set_macro(self, index, value, *args, **kw):
        if value == 127:
            raise ValueError("planted: 127 refused")
        KitPlain.set_macro(self, index, value, *args, **kw)


class NanLevel(KitPlain):
    """Args: a NaN macro reads back 0 but plays a level of 0.5."""
    NAME = "NanLevel"

    def set_macro(self, index, value, *args, **kw):
        KitPlain.set_macro(self, index, value, *args, **kw)
        if value != value:
            self._shaper.set(post_gain=0.5)


class PatchStale(KitPlain):
    """Args: a patch change applies only the first macro."""
    NAME = "PatchStale"

    def program_change(self, index, *args, **kw):
        patch = type(self).PATCHES.get(index)
        if patch is None:
            return
        self._macros[0] = _component.position_of_midi("UNIPOLAR",
                                                      patch[1][0])
        self._apply_macro(0, self._macros[0])
        self._patch_index = index


class CtorNan(KitPlain):
    """Args: a NaN Gain builds a level of 0.6, neither the default nor
    the bottom stop."""
    NAME = "CtorNan"

    def _build(self, mix=1.0, gain=1.0, patch=None):
        self._nan = gain != gain
        KitPlain._build(self, mix, gain, patch)

    def _level(self):
        if self._nan:
            return 0.6
        return KitPlain._level(self)


PLANTS = {}
for _cls in (KitPlain, Silent, WrapKit, WrapKitQuiet, ClipKit, DeadStop,
             ImplKit, EchoTail, ShortTail, EventTail, NoneSilent, NoneDC,
             ReadbackOff, StopRaises, NanLevel, PatchStale, CtorNan):
    PLANTS[_cls.NAME] = _cls
