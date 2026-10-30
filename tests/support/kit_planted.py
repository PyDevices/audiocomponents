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

import audiocore
import audiomixer
import lifecycle
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


def _leak_band(x):
    """Two LSB more between 3000 and 12000: a level only a mid-level note
    reaches."""
    return x + 2 if 3000 < abs(x) <= 12000 else x


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


class LeakBand(KitPlain):
    """Levels: the wire at Mix 0 is the source except in a band of levels
    (3000 to 12000, which a phrase at -24 dBFS never reaches and one at -12
    does), so the wire holds at one level and not at the next."""
    NAME = "LeakBand"
    CURVE = staticmethod(_leak_band)


class LongTail(KitPlain):
    """Ceiling: the control with a declared tail of 5 s, so its window is
    5 s and not the default 2."""
    NAME = "LongTail"
    TAIL_SAMPLES = 5 * 48000


class EndlessTail(KitPlain):
    """Ceiling: a tail past any window, held to the longest one."""
    NAME = "EndlessTail"
    TAIL_SAMPLES = 100 * 48000


class ClipKit(KitPlain):
    """Ceiling: twice the input, clamped, so a loud input sits on the
    rail."""
    NAME = "ClipKit"
    CURVE = staticmethod(_clip2)


class ClipAtTop(ClipKit):
    """Ceiling: ClipKit saying its Gain at the top clips by design, so
    only a cell with Gain at 127 is excused the rail."""
    NAME = "ClipAtTop"
    CLIPS_AT_TOP = (1,)


class ClipsAlways(ClipKit):
    """Ceiling: ClipKit saying it clips by design everywhere."""
    NAME = "ClipsAlways"
    CLIPS_BY_DESIGN = True


class WrapsAlways(WrapKit):
    """Ceiling: a wrap is never by design, even in a class that clips."""
    NAME = "WrapsAlways"
    CLIPS_BY_DESIGN = True


class DeadStop(KitPlain):
    """Ceiling: Gain's bottom stop is silence, as a level that went NaN on
    a board would be."""
    NAME = "DeadStop"

    def _level(self):
        if self._macros[1] == 0.0:
            return 0.0
        return KitPlain._level(self)


class CondKit(KitPlain):
    """The control for the ceiling's mid-stop, combined and low-note
    cells: three macros (Mix, Level, Tone), no setting of which wraps. Its
    plants swap in a wrapping table, at unity, at one setting only."""
    NAME = "CondKit"
    MACRO_LABELS = ("Mix", "Level", "Tone")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (0.25, 1.0), (0.0, 1.0))
    PATCHES = {0: ("Default", (127, 64, 64)), 1: ("Soft", (127, 32, 64))}
    _TABLES = {}

    def _build(self, mix=1.0, level=0.25 + 0.75 * 64 / 127, tone=64 / 127,
               patch=None):
        import audioshaper
        self._shaper = self._own(audioshaper.Waveshaper(
            curve=self._table(_same), oversample=1,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._arm()
        self._macros = [0.0, 0.0, 0.0]
        self._init_macros((mix, level, tone), patch)

    def _table(self, fn):
        if fn not in CondKit._TABLES:
            CondKit._TABLES[fn] = _curve(fn)
        return CondKit._TABLES[fn]

    def _at(self, index, midi):
        return abs(self._macros[index] - midi / 127.0) < 1e-6

    def _bad(self):
        return False

    def _apply_macro(self, index, position):
        if self._bad():
            self._shaper.set(curve=self._table(_wrap2), post_gain=1.0)
        else:
            mix = self.macro(0)
            self._shaper.set(curve=self._table(_same),
                             post_gain=1.0 - mix + mix * self.macro(1))


class MidWrap(CondKit):
    """Ceiling: wraps with Level at 64 alone, a position between the
    stops."""
    NAME = "MidWrap"
    PATCHES = {0: ("Default", (127, 96, 64)), 1: ("Soft", (127, 32, 64))}

    def __init__(self, source, *a, **kw):
        kw.setdefault("level", 0.25 + 0.75 * 96 / 127)
        CondKit.__init__(self, source, *a, **kw)

    def _bad(self):
        return self._at(1, 64)


class ComboWrap(CondKit):
    """Ceiling: wraps only with Mix and Level at 127 and Tone at 0
    together, the combination a docstring calls the worst."""
    NAME = "ComboWrap"

    def _bad(self):
        return self._at(0, 127) and self._at(1, 127) and self._at(2, 0)


class PatchComboRail(CondKit):
    """Ceiling: sits on the rail only on patch 1, with Mix and Level at 127
    and Tone at 0 together: the combination ComboWrap is bad on, but at a
    patch the default-patch cells never reach. A rail, because the combined
    cells on a patch run on the squares, which a wrap does not show on."""
    NAME = "PatchComboRail"
    _born = None

    def program_change(self, index, *args, **kw):
        # Any macro move forgets the patch index, so the plant keeps the
        # patch it was last given.
        self._born = index
        return CondKit.program_change(self, index, *args, **kw)

    def _bad(self):
        return (self._born == 1 and self._at(0, 127)
                and self._at(1, 127) and self._at(2, 0))

    def _apply_macro(self, index, position):
        if self._bad():
            self._shaper.set(curve=self._table(_clip2), post_gain=1.0)
        else:
            CondKit._apply_macro(self, index, position)


class AllWrap(CondKit):
    """Ceiling: wraps only with every macro at 127 together."""
    NAME = "AllWrap"

    def _bad(self):
        return self._at(0, 127) and self._at(1, 127) and self._at(2, 127)


class _LowNote:
    """A Python-level node (CPython only): half the input, until the input
    has sat past 0.885 of full scale for 250 frames on one side after
    crossing from the other; from there it ramps up by 128 a frame and
    wraps round int16, as a sum that overflowed on a long half-cycle
    would."""

    def __init__(self, inner):
        self.inner = inner
        self.sample_rate = inner.sample_rate
        self.channel_count = inner.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True
        self._clear()

    def _clear(self):
        ch = self.channel_count
        self.run = [0] * ch
        self.side = [0] * ch
        self.flipped = [False] * ch

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self._clear()
        audiocore.reset_buffer(self.inner)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        more, data = audiocore.get_buffer(self.inner)
        x = array("h", bytes(data))
        ch = self.channel_count
        for i in range(len(x)):
            c = i % ch
            v = x[i]
            side = 1 if v >= 29000 else (-1 if v <= -29000 else 0)
            if side and side == self.side[c]:
                self.run[c] += 1
            elif side:
                if self.side[c]:
                    self.flipped[c] = True
                self.side[c] = side
                self.run[c] = 1
            else:
                self.run[c] = 0
            y = v // 2
            if self.flipped[c] and self.run[c] > 250:
                y += side * 128 * (self.run[c] - 250)
                y = (y + 32768) % 65536 - 32768
            x[i] = y
        return more, memoryview(bytes(x))


class LowWrap(KitPlain):
    """Ceiling: wraps on a square below about 60 Hz at 48 kHz, and on no
    material the 100 Hz square, the 50 Hz sine, the clicks or the DC step
    reach (CPython only: its output is a Python-level node)."""
    NAME = "LowWrap"

    def _arm(self):
        self._shaper.play(self._source)
        self._output = _LowNote(self._shaper)


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


class NanRaises(KitPlain):
    """Args: a NaN macro value is refused with ValueError, moving nothing;
    the contract clamps it to the bottom stop instead."""
    NAME = "NanRaises"

    def set_macro(self, index, value, *args, **kw):
        if value != value:
            raise ValueError("planted: NaN refused")
        KitPlain.set_macro(self, index, value, *args, **kw)


class NanTop(KitPlain):
    """Args: a NaN macro value lands on the top stop, read back and played
    there; the contract puts it on the bottom stop."""
    NAME = "NanTop"

    def set_macro(self, index, value, *args, **kw):
        if value != value:
            value = 127
        KitPlain.set_macro(self, index, value, *args, **kw)


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

    def __init__(self, source, *options, **keywords):
        # The base class drops a NaN option before `_build` runs, so the
        # fault has to be planted where the NaN still shows.
        gain = keywords.get("gain", 1.0)
        self._nan = gain != gain
        KitPlain.__init__(self, source, *options, **keywords)

    def _level(self):
        if self._nan:
            return 0.6
        return KitPlain._level(self)


class ClearsFirst(KitPlain):
    """Args: program_change zeroes the cached level before it validates,
    so a refused call leaves the next render quiet."""
    NAME = "ClearsFirst"

    def program_change(self, index, *args, **kw):
        self._shaper.set(post_gain=0.0)
        KitPlain.program_change(self, index, *args, **kw)


class ClearsMacro(KitPlain):
    """Args: a refused set_macro has already dropped the patch, and a
    refused program_change has already moved a macro."""
    NAME = "ClearsMacro"

    def set_macro(self, index, value, *args, **kw):
        self._patch_index = None
        KitPlain.set_macro(self, index, value, *args, **kw)

    def program_change(self, index, *args, **kw):
        self._macros[1] = 0.5
        KitPlain.program_change(self, index, *args, **kw)


# -- a board build with no audiocore.get_buffer -----------------------------


class FlushKit(lifecycle.Routed):
    """The control for nogb: Routed, with a voice of its own, primed at
    construction and flushed by pulling its mixer once. Where
    `audiocore.get_buffer` is absent it plays that voice again instead, so
    nothing it renders depends on which it did."""
    NAME = "FlushKit"

    def _build(self, mix=1.0, gain=1.0, patch=None):
        ch = self._channel_count
        self._quiet = self._own(audiomixer.Mixer(
            voice_count=1, **self._pcm(lifecycle.BLOCK * ch * 2)), reset=False)
        self._zeros = lifecycle._raw(array("h", bytes(2 * 8 * ch)),
                                     self._sample_rate, ch)
        self._quiet.voice[0].play(self._zeros, loop=True)
        pull = getattr(audiocore, "get_buffer", None)
        if pull is not None:
            pull(self._quiet)
        else:
            self._quiet.voice[0].play(self._zeros, loop=True)
        lifecycle.Routed._build(self, mix, gain, patch)


class FlushOnly(lifecycle.Routed):
    """Nogb: the voices are primed whenever the graph is armed (at
    construction, after a reset, when Mix comes back) and flushed only by
    pulling the mixer; with no `get_buffer` the primed block stays in the
    voice and plays later, out of step."""
    NAME = "FlushOnly"

    def _arm(self):
        lifecycle.Routed._arm(self)
        pull = getattr(audiocore, "get_buffer", None)
        if pull is not None:
            pull(self._mixer)


class DoubleReset(FlushKit):
    """Nogb: with no `get_buffer`, a second reset in a row plays the voices
    again, which drops the block they held and takes the source's next one:
    a block of the render is gone."""
    NAME = "DoubleReset"
    _fresh = False

    def reset(self):
        again = self._fresh
        FlushKit.reset(self)
        self._fresh = True
        if again and getattr(audiocore, "get_buffer", None) is None:
            lifecycle.Routed._arm(self)

    def set_macro(self, *args, **kw):
        self._fresh = False
        FlushKit.set_macro(self, *args, **kw)


class FlushKit3(FlushKit):
    """The control for nogb's every-patch cells: FlushKit with a patch
    between the first and the last."""
    NAME = "FlushKit3"
    PATCHES = {0: ("Unity", (127, 127)), 1: ("Mid", (127, 112)),
               2: ("Soft", (127, 96))}


class MidPatchReset(FlushKit3):
    """Nogb: at the middle patch only, with no `get_buffer`, a reset plays
    the voices again, which drops the block they held: a fault neither the
    defaults nor the last patch reach."""
    NAME = "MidPatchReset"

    def reset(self):
        mid = self._patch_index == 1
        FlushKit3.reset(self)
        if mid and getattr(audiocore, "get_buffer", None) is None:
            lifecycle.Routed._arm(self)


class PatchPulls(FlushKit3):
    """Nogb: at the middle patch only, the build pulls its quiet mixer
    with `audiocore.get_buffer` unconditionally, so where that is compiled
    out it raises AttributeError there and nowhere else (Distortion's
    patches 6 to 9 did this)."""
    NAME = "PatchPulls"

    def _build(self, mix=1.0, gain=1.0, patch=None):
        FlushKit3._build(self, mix, gain, patch)
        if patch == 1:
            audiocore.get_buffer(self._quiet)

    def program_change(self, index, *args, **kw):
        FlushKit3.program_change(self, index, *args, **kw)
        if index == 1:
            audiocore.get_buffer(self._quiet)


class NativeFlush(FlushKit):
    """Nogb: FlushOnly's fault on MicroPython and CircuitPython only (a
    path a class takes off CPython, as Vibrato's native graph and
    Saturation's CircuitPython reset do): a check that runs on CPython
    alone reads it as clean."""
    NAME = "NativeFlush"

    def _arm(self):
        FlushKit._arm(self)
        if sys.implementation.name == "cpython":
            return
        pull = getattr(audiocore, "get_buffer", None)
        if pull is not None:
            pull(self._mixer)


# -- reset equals fresh -------------------------------------------------------


class FreshKit(EchoTail):
    """The control for the fresh check: EchoTail with a second patch; a
    reset clears the repeat line and lands on patch 0, which is where the
    constructor's defaults sit."""
    NAME = "FreshKit"


class OffGrid(FreshKit):
    """A control for the fresh check: the constructor's Gain default is a
    hair under patch 0's 127, which a declared default may be. Its reset is
    clean, so it is never red; `boot` reports the difference."""
    NAME = "OffGrid"

    def _build(self, mix=1.0, gain=0.999, patch=None):
        FreshKit._build(self, mix, gain, patch)


class PatchLeak(FreshKit):
    """Fresh: from patch 1 only, reset() keeps the repeat line, so the
    20 ms it held plays after the reset; from the defaults and patch 0 the
    reset is clean."""
    NAME = "PatchLeak"

    def reset(self):
        if self._patch_index != 1:
            FreshKit.reset(self)
            return
        self._check_live()
        self._clear_nodes(keep=(self._delay,))
        self._stranded = False
        self.program_change(0)


class MoveLeak(FreshKit):
    """Fresh: the reset itself is clean, but the first macro move after it
    lands a hair off where the same move on a fresh instance lands, as a
    state the reset left behind and only a move wakes would."""
    NAME = "MoveLeak"
    _after_reset = False

    def reset(self):
        FreshKit.reset(self)
        self._after_reset = True

    def _apply_macro(self, index, position):
        level = self._level()
        if self._after_reset and not self._constructing \
                and self._patch_index is None:
            level = level * 0.99
            self._after_reset = False
        self._shaper.set(post_gain=level)


PLANTS = {}
for _cls in (KitPlain, Silent, LeakBand, WrapKit, WrapKitQuiet, ClipKit, DeadStop,
             ClipAtTop, ClipsAlways, WrapsAlways,
             CondKit, MidWrap, ComboWrap, AllWrap, LowWrap, ImplKit, EchoTail, ShortTail, EventTail, NoneSilent, NoneDC,
             ReadbackOff, StopRaises, NanLevel, PatchStale, CtorNan,
             ClearsFirst, ClearsMacro, FlushKit, FlushOnly, DoubleReset,
             FlushKit3, MidPatchReset, PatchPulls, NativeFlush, FreshKit,
             OffGrid, PatchLeak, MoveLeak):
    PLANTS[_cls.NAME] = _cls

# The refused-values contract's plants (7d), registered on their own.
for _cls in (NanRaises, NanTop):
    PLANTS[_cls.NAME] = _cls
