"""The lifecycle matrix on audiodsp nodes, before any class is built on them.

`lifecycle.py` judges effect classes. This module wraps each node a phase
stands on in the thinnest class that can carry the matrix: the node alone,
its own controls as the macros, its own `mix` (or the control that is a wire
at one end) as Mix, and two or three settings as patches. Nothing is routed
around and nothing is composed, so a red cell is the node's.

    python tests/support/lifecycle.py NodePitchShift [--quick]
    LIFECYCLE_CLASSES=NodePitchShift python -m unittest tests.test_node_matrix

`clear()` is what `reset()` calls where the node has one (E1), and the
host's `audiocore.reset_buffer` is E2, so the two are both exercised.

Which nodes, and why: Phase 6's classes (PitchShifter, Harmonizer, Octaver,
StereoWidener, Rack, ShimmerHall, AirSpace) and their seed dossiers. The
racks' children are the Phase 2 to 5 classes, so `audioverb.Tank`,
`audioconvolve.Convolver` and `audioecho.FeedbackDelay`'s delay modes are
qualified by `tests/test_lifecycle_matrix.py` running those classes at the
same pin; the routing every class uses (`audioroute.Port`) is under every
class's output already.
"""

import audiodelays
import audiomixer

try:
    import audiobiquad
    import audioecho
    import audiomath
    import audioroute
except ImportError:                                   # pragma: no cover
    audiobiquad = audioecho = audiomath = audioroute = None

from audioeffects import _component

#: `_component` reads VENDOR off the module a class is defined in.
VENDOR = "PyDevices"

BLOCK = 256


def _seconds(e, seconds):
    return int(seconds * e._sample_rate)


class _Node(_component.Component):
    """One node, its controls as macros. A subclass sets `_node_cls`,
    `_make(options)` and `_set(name, value)`."""

    TIER = _component.AUDIODSP
    MACRO_MODES = {}
    #: Seconds; the tail at the running rate is this times the rate.
    _TAIL_S = 0.0
    LATENCY_SAMPLES = 0

    @property
    def tail_samples(self):
        self._check_live()
        return _seconds(self, self._TAIL_S)

    def _values(self):
        return [_component.macro_value(span, self._macros[i])
                for i, span in enumerate(type(self)._MACRO_RANGES)]

    def _register(self, node):
        clear = getattr(node, "clear", None)
        return self._own(node, reset=clear if clear is not None else True)


# -- pitch ----------------------------------------------------------------


class NodePitchShift(_Node):
    """`audiodelays.PitchShift`: the H910's splice shifter (PitchShifter,
    Harmonizer, ShimmerHall's octave)."""
    NAME = "NodePitchShift"
    TIER = _component.STOCK
    REQUIRES = ()
    MACRO_LABELS = ("Mix", "Semitones", "Freeze")
    MACRO_MODES = {0: "UNIPOLAR", 1: "BIPOLAR", 2: "TOGGLE"}
    _MACRO_RANGES = ((0.0, 1.0), (-12.0, 12.0), (0.0, 1.0))
    PATCHES = {0: ("Octave up", (127, 127, 0)),
               1: ("Octave down", (127, 0, 0)),
               2: ("Fifth, half", (64, 96, 0))}
    #: The window plus the overlap, twice, at the node's defaults.
    _TAIL_S = 2 * (1024 + 128) / 22050.0

    def _build(self, mix=1.0, semitones=12.0, freeze=0.0, patch=None):
        self._node = self._register(audiodelays.PitchShift(
            semitones=semitones, mix=mix, window=1024, overlap=128,
            **self._pcm(512)))
        self._node.play(self._source, loop=True)
        self._output = self._node
        self._init_macros((mix, semitones, freeze), patch)

    def _apply_macro(self, index, position):
        mix, semitones, freeze = self._values()
        if index == 0:
            self._node.mix = mix
        elif index == 1:
            self._node.semitones = semitones
        else:
            self._node.freeze = freeze >= 0.5


class NodeGranularPitchShift(_Node):
    """`audiodelays.GranularPitchShift`: the alternative shifter a
    PitchShifter card may choose."""
    NAME = "NodeGranularPitchShift"
    TIER = _component.STOCK
    REQUIRES = ()
    MACRO_LABELS = ("Mix", "Semitones", "Spread")
    MACRO_MODES = {0: "UNIPOLAR", 1: "BIPOLAR", 2: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (-12.0, 12.0), (0.0, 1.0))
    PATCHES = {0: ("Octave up", (127, 127, 0)),
               1: ("Octave down, spread", (127, 0, 96)),
               2: ("Fifth, half", (64, 96, 0))}
    _TAIL_S = 4 * 1024 / 22050.0

    def _build(self, mix=1.0, semitones=12.0, spread=0.0, patch=None):
        self._node = self._register(audiodelays.GranularPitchShift(
            semitones=semitones, mix=mix, grain_size=1024, density=2,
            spread=spread, **self._pcm(512)))
        self._node.play(self._source, loop=True)
        self._output = self._node
        self._init_macros((mix, semitones, spread), patch)

    def _apply_macro(self, index, position):
        mix, semitones, spread = self._values()
        if index == 0:
            self._node.mix = mix
        elif index == 1:
            self._node.semitones = semitones
        else:
            self._node.spread = spread


class NodeShimmerLoop(_Node):
    """`audioecho.FeedbackDelay` with a pitch shift in its loop
    (`loop_semitones`, ShimmerHall's Rise). Mix runs to 2.0, wet alone."""
    NAME = "NodeShimmerLoop"
    REQUIRES = ("audioecho",)
    MACRO_LABELS = ("Mix", "Feedback", "Semitones", "Time")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "BIPOLAR",
                   3: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 2.0), (0.0, 0.7), (-12.0, 12.0),
                     (10.0, 100.0))
    PATCHES = {0: ("Rise", (64, 64, 127, 64)),
               1: ("Fall, wet", (127, 96, 0, 32)),
               2: ("Fifth", (64, 32, 96, 127))}
    #: 0.7 ** n * 32768 < 1 at n = 30 repeats of the longest time, plus
    #: the loop shifter's window.
    _TAIL_S = 30 * 0.1 + 0.1

    def _build(self, mix=1.0, feedback=0.35, semitones=12.0, time_ms=55.0,
               patch=None):
        self._node = self._register(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, max_delay_ms=120.0,
            delay_ms=time_ms, feedback=feedback, mix=mix,
            loop_semitones=semitones))
        self._node.play(self._source)
        self._output = self._node
        self._init_macros((mix, feedback, semitones, time_ms), patch)

    def _apply_macro(self, index, position):
        mix, feedback, semitones, time_ms = self._values()
        name = ("mix", "feedback", "loop_semitones", "delay_ms")[index]
        self._node.set(**{name: (mix, feedback, semitones, time_ms)[index]})


class NodeSubOctave(_Node):
    """`audiomath.SubOctave`: the OC-2's flip-flop divider (Octaver)."""
    NAME = "NodeSubOctave"
    REQUIRES = ("audiomath",)
    MACRO_LABELS = ("Mix", "Order", "Threshold")
    MACRO_MODES = {0: "UNIPOLAR", 1: "TOGGLE", 2: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (1.0, 2.0), (0.001, 0.1, "log"))
    PATCHES = {0: ("One octave", (127, 0, 64)),
               1: ("Two octaves", (127, 127, 64)),
               2: ("Half, high threshold", (64, 0, 120))}
    _TAIL_S = 0.05

    def _build(self, mix=1.0, order=1.0, threshold=0.01, patch=None):
        self._node = self._register(audiomath.SubOctave(
            order=int(order), mix=mix, threshold=threshold,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._node.play(self._source)
        self._output = self._node
        self._init_macros((mix, order, threshold), patch)

    def _apply_macro(self, index, position):
        mix, order, threshold = self._values()
        if index == 0:
            self._node.set(mix=mix)
        elif index == 1:
            self._node.set(order=2 if order >= 1.5 else 1)
        else:
            self._node.set(threshold=threshold)


class NodeSquare(_Node):
    """`audiomath.Multiply` fed two taps of one `audioroute.Splitter`: the
    frequency doubler the Octaver dossier names, and the Splitter under it.
    Mix is the Multiply's own."""
    NAME = "NodeSquare"
    REQUIRES = ("audiomath", "audioroute")
    MACRO_LABELS = ("Mix",)
    MACRO_MODES = {0: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0),)
    PATCHES = {0: ("Square", (127,)), 1: ("Half", (64,))}
    _TAIL_S = 0.0

    def _build(self, mix=1.0, patch=None):
        split = audioroute.Splitter(self._source, taps=2)
        self._split = self._own(split, reset=False)
        self._node = self._register(audiomath.Multiply(
            split.tap(0), split.tap(1), mix=mix,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._output = self._node
        self._init_macros((mix,), patch)

    def _apply_macro(self, index, position):
        self._node.set(mix=self._values()[0])


# -- stereo and routing ---------------------------------------------------


class NodeMidSide(_Node):
    """`audioroute.MidSide`: StereoWidener's matrix. Width 1 is a wire, so
    Mix carries the width from 1 (Mix 0) to the Target macro (Mix 1)."""
    NAME = "NodeMidSide"
    REQUIRES = ("audioroute",)
    MACRO_LABELS = ("Mix", "Target")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (0.0, 2.0))
    PATCHES = {0: ("Wide", (127, 127)), 1: ("Mono", (127, 0)),
               2: ("Narrow, half", (64, 32))}
    _TAIL_S = 0.0

    def _build(self, mix=1.0, target=2.0, patch=None):
        self._node = self._register(audioroute.MidSide(
            width=1.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._node.play(self._source)
        self._output = self._node
        self._init_macros((mix, target), patch)

    def _apply_macro(self, index, position):
        mix, target = self._values()
        self._node.set(width=1.0 + mix * (target - 1.0))


class NodeSplitMix(_Node):
    """`audioroute.Splitter` into `audiomixer.Mixer`, the house fan-out
    (every parallel class, Harmonizer's stack, the racks' dry). Mix moves
    the second tap's voice up and the first's down; at Mix 0 the first tap
    plays at unity, which the Rack dossier found byte-identical (A6.3)."""
    NAME = "NodeSplitMix"
    REQUIRES = ("audioroute",)
    MACRO_LABELS = ("Mix", "Level")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (0.0, 1.0))
    PATCHES = {0: ("Even", (64, 127)), 1: ("Second only", (127, 127)),
               2: ("Quiet", (127, 32))}
    _TAIL_S = 0.0

    def _build(self, mix=0.5, level=1.0, patch=None):
        split = audioroute.Splitter(self._source, taps=2)
        self._split = self._own(split, reset=False)
        self._mixer = self._register(audiomixer.Mixer(
            voice_count=2, **self._pcm(BLOCK * self._channel_count * 2)))
        self._mixer.voice[0].play(split.tap(0), loop=True)
        self._mixer.voice[1].play(split.tap(1), loop=True)
        self._output = self._mixer
        self._init_macros((mix, level), patch)

    def _apply_macro(self, index, position):
        mix, level = self._values()
        self._mixer.voice[0].level = 1.0 - mix
        self._mixer.voice[1].level = mix * level


class NodeBiquad(_Node):
    """`audiobiquad.Biquad`, low-pass: the Octaver's tracking and tone
    filters, AirSpace's top cut."""
    NAME = "NodeBiquad"
    REQUIRES = ("audiobiquad",)
    MACRO_LABELS = ("Mix", "Frequency", "Q")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (60.0, 8000.0, "log"), (0.5, 4.0))
    PATCHES = {0: ("Dark", (127, 32, 10)), 1: ("Resonant", (127, 64, 127)),
               2: ("Half, bright", (64, 120, 10))}
    _TAIL_S = 0.5

    def _build(self, mix=1.0, frequency=500.0, Q=0.7071, patch=None):
        self._node = self._register(audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=frequency, Q=Q, mix=mix,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._node.play(self._source)
        self._output = self._node
        self._init_macros((mix, frequency, Q), patch)

    def _apply_macro(self, index, position):
        mix, frequency, q = self._values()
        if index == 0:
            self._node.mix = mix
        elif index == 1:
            self._node.frequency = self._hz(frequency)
        else:
            self._node.Q = q


class NodeEcho(_Node):
    """`audiodelays.Echo`: Reverb's predelay and the Haas line a
    StereoWidener card may choose."""
    NAME = "NodeEcho"
    TIER = _component.STOCK
    REQUIRES = ()
    MACRO_LABELS = ("Mix", "Time", "Decay")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (5.0, 100.0), (0.0, 0.5))
    PATCHES = {0: ("Haas", (127, 5, 0)), 1: ("Slap", (64, 127, 64)),
               2: ("Short repeats", (96, 40, 127))}
    #: 0.5 ** n * 32768 < 1 at n = 16 repeats of the longest time.
    _TAIL_S = 16 * 0.1 + 0.1

    def _build(self, mix=1.0, time_ms=10.0, decay=0.0, patch=None):
        self._node = self._register(audiodelays.Echo(
            max_delay_ms=120, delay_ms=time_ms, decay=decay, mix=mix,
            freq_shift=False, **self._pcm(512)))
        self._node.play(self._source, loop=True)
        self._output = self._node
        self._init_macros((mix, time_ms, decay), patch)

    def _apply_macro(self, index, position):
        mix, time_ms, decay = self._values()
        if index == 0:
            self._node.mix = mix
        elif index == 1:
            self._node.delay_ms = time_ms
        else:
            self._node.decay = decay


class NodeMultiTapDelay(_Node):
    """`audiodelays.MultiTapDelay`: the heads of the class of the same
    name, whose line and write heads a reset must leave as a fresh node
    has them."""
    NAME = "NodeMultiTapDelay"
    TIER = _component.STOCK
    REQUIRES = ()
    MACRO_LABELS = ("Mix", "Time", "Decay")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (20.0, 300.0), (0.0, 0.5))
    PATCHES = {0: ("Two heads", (64, 64, 0)), 1: ("Short", (127, 10, 64)),
               2: ("Long repeats", (96, 127, 127))}
    #: 0.5 ** n * 32768 < 1 at n = 16 repeats of the longest time; the
    #: node rounds each repeat, so it is given 24.
    _TAIL_S = 24 * 0.3 + 0.3

    def _build(self, mix=0.5, time_ms=150.0, decay=0.0, patch=None):
        self._node = self._register(audiodelays.MultiTapDelay(
            max_delay_ms=320, delay_ms=time_ms, decay=decay, mix=mix,
            taps=((1.0, 1.0), (0.5, 0.7)), **self._pcm(512)))
        self._node.play(self._source, loop=True)
        self._output = self._node
        self._init_macros((mix, time_ms, decay), patch)

    def _apply_macro(self, index, position):
        mix, time_ms, decay = self._values()
        if index == 0:
            self._node.mix = mix
        elif index == 1:
            self._node.delay_ms = time_ms
        else:
            self._node.decay = decay


class NodeFlanger(_Node):
    """`audiodelays.Flanger`: CircuitPython's flanger node, which Phase 7's
    `Flanger` is rebuilt on. Mix is a wire at 0."""
    NAME = "NodeFlanger"
    TIER = _component.STOCK
    REQUIRES = ()
    MACRO_LABELS = ("Mix", "Rate", "Depth", "Feedback")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "BIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (0.0, 5.0), (0.0, 1.0), (-0.9, 0.9))
    PATCHES = {0: ("Jet", (127, 13, 127, 115)),
               1: ("Slow sweep", (64, 3, 96, 80)),
               2: ("Negative", (96, 26, 64, 13))}
    #: 0.9 ** n * 32768 < 1 at n = 99 repeats of the 10 ms line, plus one
    #: sweep's worth of line.
    _TAIL_S = 99 * 0.010 + 0.02

    def _build(self, mix=0.5, rate=0.5, depth=0.5, feedback=0.5,
               patch=None):
        self._node = self._register(audiodelays.Flanger(
            max_delay_ms=10, min_delay_ms=1.0, rate=rate, depth=depth,
            feedback=feedback, mix=mix, **self._pcm(512)))
        self._node.play(self._source, loop=True)
        self._output = self._node
        self._init_macros((mix, rate, depth, feedback), patch)

    def _apply_macro(self, index, position):
        name = ("mix", "rate", "depth", "feedback")[index]
        setattr(self._node, name, self._values()[index])


class NodeComparator(_Node):
    """`audioshaper.Waveshaper` with a step curve: the Octaver's comparator
    ahead of its divider."""
    NAME = "NodeComparator"
    REQUIRES = ("audioshaper",)
    MACRO_LABELS = ("Mix", "Drive")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (1.0, 8.0))
    PATCHES = {0: ("Square", (127, 0)), 1: ("Driven, half", (64, 127))}
    _TAIL_S = 0.01

    def _build(self, mix=1.0, drive=1.0, patch=None):
        from array import array
        import audioshaper
        half = 128
        curve = array("h", [-16000] * half + [0] + [16000] * half)
        self._node = self._register(audioshaper.Waveshaper(
            sample_rate=self._sample_rate, curve=curve, oversample=1,
            channel_count=self._channel_count, mix=mix, pre_gain=drive))
        self._node.play(self._source)
        self._output = self._node
        self._init_macros((mix, drive), patch)

    def _apply_macro(self, index, position):
        mix, drive = self._values()
        if index == 0:
            self._node.set(mix=mix)
        else:
            self._node.set(pre_gain=drive)


class NodeAllPass(_Node):
    """`audiobiquad.AllPass`, two stages: the Octaver's signal-path phase
    match."""
    NAME = "NodeAllPass"
    REQUIRES = ("audiobiquad",)
    MACRO_LABELS = ("Mix", "Frequency")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (60.0, 4000.0, "log"))
    PATCHES = {0: ("Low", (127, 30)), 1: ("High, half", (64, 110))}
    _TAIL_S = 0.1

    def _build(self, mix=1.0, frequency=300.0, patch=None):
        self._node = self._register(audiobiquad.AllPass(
            stages=2, frequency=frequency, mix=mix,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._node.play(self._source)
        self._output = self._node
        self._init_macros((mix, frequency), patch)

    def _apply_macro(self, index, position):
        mix, frequency = self._values()
        if index == 0:
            self._node.mix = mix
        else:
            self._node.frequency = self._hz(frequency)


NODES = {}
for _cls in (NodePitchShift, NodeGranularPitchShift, NodeShimmerLoop,
             NodeSubOctave, NodeSquare, NodeMidSide, NodeSplitMix,
             NodeBiquad, NodeEcho, NodeMultiTapDelay, NodeFlanger,
             NodeComparator,
             NodeAllPass):
    NODES[_cls.NAME] = _cls


#: Red cells a node has by design, one row per (adapter NAME, event name
#: prefix, property): reason. Merged into lifecycle.DECLARED on import.
DECLARED = {
    ("NodeSubOctave", "E1-", "P4"):
        "a reset restarts the divider at the pass-through polarity; a node"
        " that counted an odd number of edges plays the same octave inverted",
    ("NodeSubOctave", "E2-", "P4"):
        "as E1: the host reset restarts the divider's count",
    ("NodeBiquad", "E2-", "P4"):
        "a float32 recursion on looping input can settle one ulp off a"
        " never-reset one and flip one LSB now and then for good",
    ("NodeBiquad", "E6-", "P4"):
        "as E2: one ulp of filter state after a move and back",
    ("NodeShimmerLoop", "E1-", "P4"):
        "clear() restarts the loop shifter's crossfade phase, so the node is"
        " never in phase with one that was never cleared",
    ("NodeShimmerLoop", "E2-", "P4"):
        "as E1: the host reset restarts the loop shifter's phase",
    ("NodeShimmerLoop", "E4-", "P4"):
        "a Semitones move runs the free-running shifter phase at another rate",
    ("NodeShimmerLoop", "E6-", "P4"):
        "a patch with other semitones moves the free-running shifter phase",
    ("NodeShimmerLoop", "E11-", "P4"):
        "moves of Semitones before a pull move the shifter phase",
    ("NodeEcho", "E4-m0", "P3"):
        "upstream's Echo holds its line still at mix 0 and plays it when mix"
        " comes back; a class routes around and rejoins clean",
    ("NodeEcho", "E5-", "P3"):
        "as E4: the line held at mix 0 plays when mix comes back",
    ("NodeEcho", "E9-", "P3"):
        "as E4, at every source buffer size",
    ("NodePitchShift", "E2-", "P4"):
        "reset_buffer restarts the splice phase, so the node matches a fresh"
        " one, not the uninterrupted control",
    ("NodePitchShift", "E1-", "P4"):
        "as E2: a reset starts the splice again, and the splice's move"
        " depends on what played, so the node matches a fresh one, not the"
        " uninterrupted control",
    ("NodePitchShift", "E4-m2=127", "P4"):
        "a freeze set while a splice crossfades finishes that splice's move"
        " first, so the frozen loop reads from where the control's does not",
    ("NodePitchShift", "E4-m1", "P4"):
        "a Semitones move runs the read position at another rate, so the"
        " splice phase lands elsewhere; putting it back would click",
    ("NodePitchShift", "E6-", "P4"):
        "as E4: a patch with other semitones moves the splice phase",
    ("NodePitchShift", "E11-", "P4"):
        "as E4: moves before a pull move the splice phase",
    ("NodeFlanger", "E1-", "P4"):
        "a reset starts the sweep's LFO again from the top, so the node"
        " matches a fresh one, not the uninterrupted control",
    ("NodeFlanger", "E2-", "P4"):
        "as E1: the host reset starts the sweep again",
    ("NodeFlanger", "E4-m1=", "P4"):
        "a Rate move runs the free-running sweep at another rate, so its"
        " phase lands elsewhere; putting it back would jump the sweep",
    ("NodeFlanger", "E6-", "P4"):
        "as E4: a patch with another Rate moves the sweep's phase",
    ("NodeFlanger", "E11-", "P4"):
        "as E4: Rate moves before a pull move the sweep's phase",
    ("NodeGranularPitchShift", "E1-", "P4"):
        "a reset restarts the grain clock, so grains never line up with the"
        " uninterrupted control again",
    ("NodeGranularPitchShift", "E2-", "P4"):
        "as E1: the host reset restarts the grain clock",
    ("NodeGranularPitchShift", "E6-", "P4"):
        "a Spread move to 0 draws no jitter, so the random sequence falls"
        " behind the control's",
}

#: Ruled N1 (2026-10-13): a control that jumps steps the output in every
#: node (no in-node ramp yet; audiocomponents docs/how-it-works/control-smoothing.md),
#: so P5 is declared for every node adapter.
import lifecycle  # noqa: E402

for _name in NODES:
    for _event in lifecycle.CONTROL_EVENTS:
        DECLARED[(_name, _event, "P5")] = (
            "a control that jumps steps the output; the in-node 20 ms ramp"
            " is planned, not built (docs/how-it-works/control-smoothing.md)")

lifecycle.DECLARED.update(DECLARED)
