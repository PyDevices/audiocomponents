"""The construction shape every rebuilt effect class is built on.

It replaced `_core.py`, the pre-contract shape, in which a module-level
`configure()` held the sample rate and `Effect.__new__` sniffed the format
off whatever it was handed. The effects roadmap (§3, "What the contract
freezes") freed that; every family was rebuilt on this module, and
`_core.py` was retired in Phase 7.

What is different here, and why:

* **The format arrives with the source, and the factory confirms it.** There
  is no module state. `create(source, sample_rate, transport=None,
  **options)` is the contract's construction boundary and passes the rate it
  was asked for; a direct call for local code -- `Compressor(source,
  threshold_db=-18)` -- reads the rate and the channel count off the source
  it was handed. Neither path can be told a rate by something that ran
  earlier, which is the failure `configure()` invited.

* **A class enumerates the nodes it builds**, with `self._own(node)`, and
  `reset()` and `deinit()` walk that list. `_core.reset()` touched the output
  node only, so what a chain's reset actually clears depends on which node
  happened to be last. Every node clears something different:
  `audiofilters.Filter` and `Phaser` clear their own delay buffers and
  biquad states (`audiodsp/src/audiofilters/Filter.c:133-149`);
  `audioecho.FeedbackDelay` empties its whole line
  (`audioecho/FeedbackDelay.c:233-244`, "everything goes");
  `audiodynamics.Dynamics` clears its envelopes and its lookahead but lets
  the sidechain filter's memory and the last reported gain reduction survive
  on purpose (`shared/audiodsp_dynamics.c:281-295`); and `audiomixer`'s
  voices reset their sources recursively
  (`audiomixer/MixerVoice.c:97`), as does `audiospeed.SpeedChanger`
  (`audiospeed/SpeedChanger.c:109`). One walk over the class's own list is
  the same reset whatever the tail is.

  Two details of the roadmap's wording at that point do not survive contact
  with the files, checked 2026-09-07 and recorded here rather than left to
  be rediscovered. `audiofilters/Filter.c` and `Phaser.c` do **not** reset
  their source inside `reset_buffer` -- not in audiodsp
  (`src/audiofilters/Filter.c:133-149`) and not in upstream CircuitPython
  (`circuitpython/shared-module/audiofilters/Filter.c:126-139`). The
  recursion in those files is in `play()` (audiodsp `:161`, CircuitPython
  `:151`) and in the loop-restart path (CircuitPython `:190`); the nodes
  whose `reset_buffer` really does recurse are `audiomixer`'s and
  `audiospeed`'s. None of that changes the design -- the enumerated walk is
  what makes a reset the same whatever the tail is, either way -- but it
  changes which node an evidence pack may blame.

  A second thing worth carrying: emptying a node's pending buffer makes it
  re-read its source, and `audiocore.RawSample` hands its buffer back from
  the beginning. A probe whose burst sits at frame 0 therefore replays it
  after `reset()` and reads exactly like a delay line that was never
  cleared. `tests/test_component_foundation.py` leads its probe with
  silence for that reason.

* **The borrowed source is never reset and never deinitialised.**
  `_own()` refuses to take the source, and neither walk ever names it. A node
  that recurses upstream of its own accord is that node's behaviour, and the
  class gate's STATE measurement is where a class proves the source still
  renders afterwards.

* **The metadata shape is enforced at construction**, once per class, so a
  malformed macro or patch table is a build failure rather than a wrong
  sound. `tools/validate_metadata.py` remains the fuller, CPython-side check
  (it also holds a class to declaring its fields explicitly); this is the
  part that must hold on a board.

* **Every class states a portability tier.** `STOCK` is built from
  CircuitPython-ported nodes only. `AUDIODSP` needs at least one audiodsp-own
  node and says which in `REQUIRES`; the module does the guarded import so it
  stays importable on a stock board, and construction raises a clear
  `ImportError`. The construction-time check imports the module for itself
  rather than reading the module-level `None`, so it is honest even when the
  module was imported before it was blocked -- which is exactly what
  `tests/test_portability_tier.py` does.

The shape a rebuilt class takes:

    from . import _component

    VENDOR = "PyDevices"

    class Thing(_component.Component):
        NAME = 'Thing'
        TIER = _component.STOCK
        MACRO_LABELS = ("Drive",)
        MACRO_MODES = {0: "UNIPOLAR"}
        _MACRO_RANGES = ((0.0, 1.0),)
        PATCHES = {0: ("Default", (64,))}

        def _build(self, drive=0.5, patch=None):
            node = audiofilters.Distortion(**self._pcm())
            node.play(self._source)
            self._own(node)
            self._output = node
            self._init_macros((drive,), patch)

        def _apply_macro(self, index, position):
            ...

`_build` replaces `__init__`: the base does the format, the tier and the
metadata first, then hands the constructor's own options straight through, so
no class author can forget to call up.

A setting you derive here is not the setting a board derives
------------------------------------------------------------

`mp_float_t` is **single precision on an ESP32 and double on every
desktop**. So a corner computed from a macro, a shelf gain computed from a
level, a `frequency * ratio` - anything a class works out in Python and
hands to a node - reaches the node as a different number on a board than on
a desktop, before a single sample is rendered. Measured on `Overdrive`
(audiocomponents#75), read back as float32 bits, board against desktop:

    _hp.frequency      4434fc30 / 4434fc2f    723.940430 / 723.940369 Hz
    _c4.frequency      46a44afe / 46a44afd    21029.4961 / 21029.4941 Hz
    _shelf.gain_db     3b4e6980 / 3b4e69a0    0.00314959884 / 0.00314960629
    its a2 coefficient 3f2e8697 / 3f2e8698    0.681741178 / 0.681741238

One ULP of float32 on three of those and 32 on the shelf gain. `audiobiquad`
gives bit-identical coefficients from identical settings on all four legs,
so this is the class's own arithmetic and not the node's.

**This is accepted and deliberately not fixed** (2026-09-22): a board
and a desktop are allowed to differ by a last-bit coefficient, and no class
is to be rewritten around it. What it means for you:

- Do not write a gate that requires a board and a desktop to render the
  same bytes out of a class that derives a setting in Python. They cannot,
  and the gate would be measuring the width of a float.
- A literal does not rescue you unless it is exactly representable in
  float32. `11.7709228` written as a literal is `413c55b4` on a board and
  `413c55b3` on a desktop, because each parses it at its own width
  (audiocomponents#90). `11.75` is the same on both.
- Where you want the legs to agree, hand the node a number every format
  holds - a power of two, a short binary fraction, or a value from a table
  of literals chosen that way - and say in the class why that number and
  not the obvious one.
"""

import math
import sys

import audiocore

#: `audioroute.Port` -- the pass-through node every Component ends in, so the
#: object a consumer takes from `.output` is the same object for the life of
#: the component. `None` where audiodsp is not installed: on a stock
#: CircuitPython board there is no `audioroute` and no C pump either, and a
#: class there behaves exactly as it did before the port existed. See
#: `_OutputPort` below for what that costs and where.
try:
    from audioroute import Port as PORT
except (ImportError, AttributeError):        # pragma: no cover - stock board
    PORT = None


def _get_output(effect):
    return getattr(effect, "_port", None)


#: How far `_would_loop` looks before giving up. It never gets this far on a
#: board: the first node it asks has no `__dict__`, so the walk stops at one.
_LOOP_BUDGET = 32


def _would_loop(port, node):
    """Whether pointing `port` at `node` would make the port its own source.

    `self._output = Wrap(self._output)` -- appending one more stage to the
    end of the graph -- was a legal construction before the port and is a
    loop after it: the wrapper takes the WIRE as its source, and the wire is
    then pointed at the wrapper. Nothing catches it downstream. A pull walks
    the two of them until the interpreter runs out of stack, which on
    CPython is a `RecursionError` out of the render and on a board is the
    pump thread wedged with no exception anyone can see.

    So it is refused here, on the interpreter thread, where raising is free.
    A class that means to append a stage wraps `port_target(self._output)` --
    the node at the end of the graph -- and not `self._output` itself, and
    that is what the API contract says.

    The walk reads `__dict__`, so it sees the CPython twins in full and
    finds nothing on a native build, where a node holds its source in C.
    That is the same honest degradation the measurement kit's graph walks
    have, and it costs a board one failed attribute lookup per re-point.
    """
    pending = [node]
    seen = 0
    while pending and seen < _LOOP_BUDGET:
        current = pending.pop()
        if current is port:
            return True
        seen += 1
        try:
            held = current.__dict__
        except AttributeError:           # a native node keeps no __dict__
            continue
        for value in held.values():
            if hasattr(value, "_get_buffer"):
                pending.append(value)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if hasattr(item, "_get_buffer"):
                        pending.append(item)
    return False


def _set_output(effect, node):
    if node is None:
        effect._port = None
        return
    port = getattr(effect, "_port", None)
    if port is None:
        # No `audioroute`: the port is the node, which is exactly what
        # `_output` has always been.
        effect._port = node if PORT is None else PORT(node)
        return
    if PORT is None:
        effect._port = node
        return
    if _would_loop(port, node):
        raise ValueError(
            "%s's new output is built on its own output port, so playing it "
            "would make the port its own source and a pull would never "
            "return. To append a node to the end of the graph, wrap "
            "port_target(self._output) -- the node the port is playing -- "
            "rather than self._output, which is the wire."
            % type(effect).__name__)
    port.play(node)


#: `self._output = node` is a re-point, not a new identity.
#:
#: The defect this fixes is a pattern, not a class: about twenty classes in
#: the palette do `self._output = self._source` when Mix reaches 0 and
#: `self._output = self._mixer` when it leaves, `Distortion._rebuild` points
#: `_output` at a brand new mixer when Character crosses 0.5, and
#: `Phaser._install_cascade` swaps the cascade node that IS its output on
#: every Stages move. Everything downstream took `.output` ONCE -- a rack
#: when it built its chain, a user at `mixer.voice[0].play(fx.output)`, a C
#: pump when it adopted the tail -- so none of them ever heard about it.
#:
#: So it is fixed centrally, here, rather than in forty files: the first
#: assignment builds a `Port` around the node and every assignment after that
#: re-points that same port. A class author writes what they always wrote.
#:
#: `None` clears it, which is what `__init__` and `deinit` do. Releasing the
#: port itself is `deinit`'s job and not this setter's, because the order
#: matters there and a plain attribute store is no place to say so.
#:
#: The pre-contract `_core.Effect` base carried this same object until it
#: was retired, so its classes had the fix too.
output_port = property(_get_output, _set_output)


def port_target(output):
    """What a component's output actually plays.

    A `Port`'s identity never changes, so "what is the consumer holding" and
    "which node is really at the end of the graph" have different answers for
    the first time. Callers that mean the second one ask here: a reset that
    must not reach through to the borrowed source, a deinit that must release
    the node rather than the wire.
    """
    if PORT is not None and isinstance(output, PORT):
        return output.source
    return output


#: Portability tiers (roadmap §3). `STOCK` runs on a stock CircuitPython
#: board; `AUDIODSP` needs at least one audiodsp-own node and says which.
STOCK = "stock"
AUDIODSP = "audiodsp"

#: The audiodsp-own modules, as of the Phase 1 palette. A class whose `TIER`
#: is `AUDIODSP` names the ones it needs in `REQUIRES`, and every name must be
#: one of these -- a typo would otherwise buy a tier claim nothing checks.
AUDIODSP_MODULES = (
    "audiobiquad", "audioconvolve", "audiodynamics", "audioecho",
    "audioladder", "audiomath", "audioroute", "audioshaper", "audioverb",
)

#: The three public macro modes, as `docs/reference/metadata.md` defines them.
MODES = ("UNIPOLAR", "BIPOLAR", "TOGGLE")

MAX_MACROS = 16
MAX_PATCHES = 128

#: How many taps one `audioroute.Splitter` fans out to. The limit lives in
#: the C (`AUDIODSP_SPLITTER_MAX_TAPS`, which raises "taps must be 1..4") and
#: the native modules do not export it, so classes that build parallel
#: branches count against this mirror rather than a literal 4 apiece.
SPLITTER_TAPS = 4

#: The fraction of Nyquist a Hz-valued span may reach. Biquad coefficients
#: lose their shape in the last couple of per cent, and the rate-honesty
#: invariant asks a span to clamp at a lower rate rather than refuse -- so
#: `self._hz()` clamps here instead of raising.
NYQUIST_MARGIN = 0.98


#: `Component._followed_bpm` before `transport_changed()` has read a tempo.
_UNREAD = object()


def static_transport():
    """The transport a component sees when it was given none."""
    return (False, 0.0, 120.0, 4, 4)


#: The tempo and the quarter notes in a bar a synced class follows until a
#: transport it can read says otherwise: `static_transport`'s 120 bpm, 4/4.
GOOD_BEAT = (120.0, 4.0)

#: The largest numerator or denominator of a time signature `synced_beat`
#: follows. A bar of 128/1 is 512 quarter notes; past it a synced sweep
#: would stand still.
METER_LIMIT = 128.0


def _field(state, index):
    """`state[index]` as a finite float, or None for a field that is missing
    or is not a finite number."""
    try:
        value = float(state[index])
    except (TypeError, ValueError, OverflowError, IndexError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def synced_beat(state, last=GOOD_BEAT):
    """(bpm, quarter notes in one bar) read off a host transport tuple
    `(playing, position, bpm, numerator, denominator)`: numerator x 4 /
    denominator quarters, so 4/4 is 4, 3/4 is 3 and 6/8 is 3.

    What a host gets wrong keeps the last good reading, `last`, rather than
    raising or standing the sweep still: a tempo that is missing, None, NaN,
    infinite, or 0 or below keeps `last`'s tempo, and a signature with a
    field missing, or a numerator or denominator that is not a number from
    1 to `METER_LIMIT`, keeps `last`'s bar. A tempo below 1 bpm is 1."""
    bpm, quarters = last
    tempo = _field(state, 2)
    if tempo is not None and tempo > 0.0:
        bpm = max(1.0, tempo)
    numerator = _field(state, 3)
    denominator = _field(state, 4)
    if numerator is not None and denominator is not None \
            and 1.0 <= numerator <= METER_LIMIT \
            and 1.0 <= denominator <= METER_LIMIT:
        quarters = numerator * 4.0 / denominator
    return bpm, quarters


def biquad_ring(node):
    """Frames an `audiobiquad.Biquad` rings for after its input stops, from
    any state, as an upper bound, read off the coefficients in force.

    With no input the output is a sum of the two poles' powers, p1**n and
    p2**n. Its amplitude is at most a small constant times the state over
    |p1 - p2| (which is 2 r sin(w) for a resonator), and the state is at
    most a few times full scale whatever filter built it, including the
    one in force before a control moved (audiocomponents#114: a large
    move down rang 10 to 30 % past bounds that left both of those out). So
    the output is under half an LSB after ln(65536 * 40 / |p1 - p2|)
    time constants of the larger pole. A cascade's bound is the sum of its
    sections'.
    """
    a1, a2 = node.coefficients[3], node.coefficients[4]
    disc = a1 * a1 - 4.0 * a2
    if disc < 0.0:
        radius = math.sqrt(a2)
        gap = math.sqrt(-disc)
    else:
        root = math.sqrt(disc)
        radius = max(abs(-a1 + root), abs(-a1 - root)) / 2.0
        gap = root
    if radius <= 0.0:
        return 2
    if radius >= 1.0:
        return None
    if gap < 1e-9:
        gap = 1e-9
    return int(math.ceil((_RING_LN + math.log(1.0 / gap))
                         / -math.log(radius))) + 2


def cascade_ring(nodes):
    """`biquad_ring` summed over a cascade, or None if any section has a
    pole on or outside the unit circle."""
    total = 0
    for node in nodes:
        ring = biquad_ring(node)
        if ring is None:
            return None
        total += ring
    return total


#: ln(65536 * 40): full scale to half an LSB, with the state's headroom.
_RING_LN = math.log(65536.0 * 40.0)


def db_to_gain(db):
    return 10.0 ** (db / 20.0)


def db_to_amplitude(db):
    """Biquad peaking/shelf A parameter."""
    return 10.0 ** (db / 40.0)


def logmap(value, lo, hi):
    """0..1 -> lo..hi, logarithmic; the natural mapping for frequencies."""
    return lo * ((hi / lo) ** value)


def macro_value(span, position):
    """A macro's 0..1 position -> the value it stands for. ``span`` is
    ``(low, high)``, or ``(low, high, "log")`` for the ones that should sweep
    by ratio rather than by difference - anything in hertz or seconds."""
    low, high = span[0], span[1]
    if len(span) > 2:
        return logmap(position, low, high)
    return low + (high - low) * position


def macro_position(span, value):
    """The inverse of `macro_value`, unquantized. Used to seed a knob from a
    constructor argument, so the exact number a caller asked for stays on the
    audio path rather than being rounded onto the 7-bit grid first."""
    low, high = span[0], span[1]
    if len(span) > 2:
        position = math.log(value / low) / math.log(high / low)
    else:
        position = (value - low) / (high - low)
    return min(1.0, max(0.0, position))


def clamped_midi(value):
    """`value` on the 0-127 MIDI scale as a float, clamped to it: NaN is 0,
    and an int too large for a float (10**400) is the stop on its side."""
    try:
        value = float(value)
    except OverflowError:
        return 127.0 if value > 0 else 0.0
    return min(127.0, max(0.0, value))


def position_of_midi(mode, midi):
    """The 0-127 MIDI grid -> a macro's 0..1 position, by the macro's mode.

    UNIPOLAR and TOGGLE are the plain linear law: 0 is one end, 127 the
    other. **BIPOLAR gets a centre detent.** The grid has an even number of
    steps and therefore no middle -- 64/127 is 0.50394 -- so the plain law
    cannot express the centre of a span at all, and a bipolar macro's centre
    is the setting that means "none of this". `Overdrive`'s Symmetry at MIDI
    64 was +0.007874 rather than 0, which is a bias the shaper turns into DC
    that never decays, so every shipped patch held +56 to +85 LSB forever and
    `TAIL_SAMPLES` was false at all of them; `Fuzz`'s patch 0 banged 329 LSB
    out of digital silence for the same reason (audiocomponents#87).

    So for BIPOLAR the two halves get their own slopes and meet at 64:

        m >= 64:  0.5 + (m - 64) / 126      64 -> 0.5, 127 -> 1.0
        m <  64:  0.5 - (64 - m) / 128      64 -> 0.5,   0 -> 0.0

    `macro_value` stays linear over the span, so a symmetric span reads
    exactly 0.0 at MIDI 64 and the ends still reach both limits. The law is
    continuous at 64 and takes floats, so a host with finer resolution than
    7 bits still lands where its knob says.
    """
    midi = clamped_midi(midi)
    if mode != "BIPOLAR":
        return midi / 127.0
    if midi >= 64.0:
        return 0.5 + (midi - 64.0) / 126.0
    return 0.5 - (64.0 - midi) / 128.0


def midi_of_position(mode, position):
    """The inverse of `position_of_midi`, unquantized. What `get_macro`
    reports and what patch authoring rounds onto the grid."""
    position = min(1.0, max(0.0, float(position)))
    if mode != "BIPOLAR":
        return position * 127.0
    if position >= 0.5:
        return 64.0 + (position - 0.5) * 126.0
    return 64.0 - (0.5 - position) * 128.0


def macro_of(span, value, mode="UNIPOLAR"):
    """`value` as the nearest integer on the 0-127 MIDI grid. Patch authoring
    and the tests that hold patch 0 to the constructor's defaults need this;
    nothing on the audio path calls it.

    `mode` is the macro's own `MACRO_MODES` entry, because BIPOLAR uses a
    different MIDI law -- pass it or a bipolar patch lands beside its value
    rather than on it."""
    return int(round(midi_of_position(mode, macro_position(span, value))))


#: Frames in one block of `_lazy_silence` (an `audioroute.MidSide` with no
#: source hands out this many per pull).
_SILENCE_FRAMES = 256


def _drain(pull, mixer):
    """Pull `mixer` until each voice on the lazy silence has handed up the
    whole silent block it primed and holds nothing: a mixer that pulls
    fewer frames than the block (128 at two channels on some classes) left
    the rest to play first, and the output started half a block late."""
    total = 0
    for _ in range(64):
        state, data = pull(mixer)
        frames = len(data) // (2 * mixer.channel_count) if data else 0
        if not frames:
            return
        total += frames
        if total % _SILENCE_FRAMES == 0:
            return


def release(node):
    """Let go of a node no graph points at any more (None is fine): its
    `release_all()` where it has one, then its `deinit()`."""
    if node is None:
        return
    for name in ("release_all", "deinit"):
        call = getattr(node, name, None)
        if call is not None:
            call()


# --------------------------------------------------------------------------
# Level gates


def open_level_gates(node, voices, silence):
    """Render one block of silence through `node` so every voice starts at
    its level instead of at zero. Returns whether it could.

    Since CircuitPython 10.3.0 a mixer voice or a synthio note does not take
    a level, amplitude or pan change until its signal is at zero or changes
    sign, and a fresh one starts at level 0 (audiodsp 4ec5718). So a class's
    first block is gated: silent for material that does not cross zero in
    it - a gain table, a ramp, an impulse at frame 0 - and then the level
    steps in at the block boundary, which is a click. A zero sample opens
    the gate at once, so each voice in `voices` plays `silence` (a looped
    all-zero sample the node accepts) for one pull; the caller then hands
    the voices their real sources. Set the levels first: a level moved
    after this waits for a zero crossing, as it should.

    `silence` must hold **at least two frames**. A one-frame mono sample is
    two bytes, less than the packed word the native mixer consumes per
    loop, and `get_buffer` never returns on MicroPython or CircuitPython
    (audiodsp#85); the CPython twin returns, so the hang only shows on a
    board or a native desktop build. Two Phase 4 classes lost their mono
    renders to it. `bytes(2 * 2 * channels)` is the shape the classes here
    use.

    `audiocore.get_buffer` is compiled out of CircuitPython's default board
    builds (CIRCUITPY_AUDIOCORE_DEBUG), so there this does nothing and the
    first block keeps upstream's behaviour.
    """
    pull = getattr(audiocore, "get_buffer", None)
    if pull is None:
        return False
    for voice in voices:
        voice.play(silence, loop=True)
    pull(node)
    return True


def let_go_of_source(head, source, consumers=()):
    """Drop the source frames `head` has taken and not handed on, without
    reading or resetting `source`. Returns whether it could.

    For the node at the head of a graph a bypass stopped pulling, called
    as the graph rejoins. While Mix is 0 the host reads the source itself,
    so whatever the head still held from before is old audio: played on
    the way back it is up to 20 ms of what was sounding when the bypass
    began, and the stream runs late by as much. A host reset does not drop
    those frames, by design (the source was not reset), so the reset walk
    `_rejoin` runs leaves them.

    A Splitter holds them in its ring, and `Splitter.clear()` lets them go
    (audiodsp 0.6.6rc7); before that node there is no way to, and this
    returns False. A node with `play()` (a Biquad, a MidSide) drops what it
    held when it is handed its source again, and reads nothing from it.

    `consumers` are `(node, tap)` pairs, each a node reading one of the
    Splitter's taps, handed its tap again so it drops what it held too. A
    tap hands out at most 256 frames, and less at the end of a source
    buffer, so the first node behind it carries part of a chunk across
    blocks: old audio as well, once the ring is cleared. Nodes further
    down read whole blocks and hold nothing over.
    """
    if hasattr(head, "tap"):
        clear = getattr(head, "clear", None)
        if clear is None:
            return False
        clear()
        for node, tap in consumers:
            node.play(tap)
        return True
    head.play(source)
    return True


# --------------------------------------------------------------------------
# Metadata


def _is_nan(value):
    return isinstance(value, float) and value != value


def _without_nan(cls, options, keywords):
    """The constructor's options with every NaN taken out, so `_build` sees
    that option as left out and uses its default, as each class's
    documentation says. One rule here covers every class; none has to clean
    its own arguments.

    A class that gives NaN a meaning of its own for an option (NaN Glide is
    the jump, NaN damping is out of circuit, NaN interval is refused) names
    it in `_NAN_OWN`, and that option reaches `_build` as passed.

    A NaN passed by position is dropped by name where the interpreter can
    name `_build`'s arguments (CPython); on one that cannot, only the
    keyword form is cleaned."""
    own = cls._NAN_OWN
    if any(_is_nan(value) for value in options):
        code = getattr(cls._build, "__code__", None)
        if code is not None and len(options) <= code.co_argcount - 1:
            names = code.co_varnames[1:1 + len(options)]
            keywords = dict(zip(names, options), **keywords)
            options = ()
    return options, {name: value for name, value in keywords.items()
                     if name in own or not _is_nan(value)}


class MetadataError(ValueError):
    """A class's macro or patch tables do not have the frozen shape."""


#: Classes whose metadata has been checked. A set rather than a class
#: attribute because a class attribute is inherited, and a subclass would
#: then be waved through on its parent's check.
_CHECKED = set()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _whole(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _check_metadata(cls):
    """Hold `cls` to the metadata shape roadmap §3 freezes. Runs once per
    class, at the first construction."""
    if cls in _CHECKED:
        return
    errors = []
    name = getattr(cls, "NAME", None)
    if not _text(name):
        errors.append("NAME must be a non-empty string")

    tier = getattr(cls, "TIER", None)
    if tier not in (STOCK, AUDIODSP):
        errors.append("TIER must be _component.STOCK or _component.AUDIODSP")
    requires = getattr(cls, "REQUIRES", ())
    if not isinstance(requires, tuple):
        errors.append("REQUIRES must be a tuple")
        requires = ()
    for module in requires:
        if module not in AUDIODSP_MODULES:
            errors.append("REQUIRES names %r, which is not an audiodsp-own "
                          "module" % (module,))
    if tier == AUDIODSP and not requires:
        errors.append("the audiodsp tier must name the modules it needs in "
                      "REQUIRES")
    if tier == STOCK and requires:
        errors.append("the stock tier may not require an audiodsp-own module")

    labels = getattr(cls, "MACRO_LABELS", None)
    if not isinstance(labels, tuple):
        errors.append("MACRO_LABELS must be a tuple")
        labels = ()
    elif len(labels) > MAX_MACROS:
        errors.append("MACRO_LABELS may hold at most %d entries" % MAX_MACROS)
    elif not all(_text(label) for label in labels):
        errors.append("MACRO_LABELS entries must be non-empty strings")
    elif len(set(labels)) != len(labels):
        errors.append("MACRO_LABELS entries must be unique")

    modes = getattr(cls, "MACRO_MODES", None)
    if not isinstance(modes, dict):
        errors.append("MACRO_MODES must be an index-keyed dict")
        modes = {}
    elif not all(_whole(index) for index in modes):
        errors.append("MACRO_MODES keys must be macro indexes")
    else:
        if sorted(modes) != list(range(len(labels))):
            errors.append("MACRO_MODES needs exactly one entry per label, "
                          "keyed 0..%d" % (len(labels) - 1))
        for index in modes:
            if modes[index] not in MODES:
                errors.append("MACRO_MODES[%r] must be one of %r"
                              % (index, MODES))

    spans = getattr(cls, "_MACRO_RANGES", ())
    if not isinstance(spans, tuple) or len(spans) != len(labels):
        errors.append("_MACRO_RANGES needs one span per macro label")

    errors.extend(_check_patches(cls, labels, modes))

    module = sys.modules.get(getattr(cls, "__module__", None))
    if module is None:
        errors.append("cannot reach the defining module to read VENDOR")
    elif not _text(getattr(module, "VENDOR", None)):
        errors.append("VENDOR must be a non-empty string at module level")

    if errors:
        raise MetadataError("%s: %s" % (name or cls, "; ".join(errors)))
    _CHECKED.add(cls)


def _check_patches(cls, labels, modes):
    patches = getattr(cls, "PATCHES", None)
    if not isinstance(patches, dict):
        return ["PATCHES must be an index-keyed dict"]
    if not patches:
        return ["PATCHES must hold at least patch 0"]
    errors = []
    indexes = list(patches)
    if not all(_whole(index) for index in indexes):
        return ["PATCHES indexes must be integers"]
    if len(indexes) > MAX_PATCHES:
        errors.append("PATCHES may hold at most %d entries" % MAX_PATCHES)
    if sorted(indexes) != list(range(len(indexes))):
        errors.append("PATCHES indexes must be contiguous from 0")
    names = []
    for index in sorted(indexes):
        patch = patches[index]
        if not isinstance(patch, tuple) or len(patch) != 2:
            errors.append("PATCHES[%d] must be (name, values)" % index)
            continue
        label, values = patch
        if not _text(label):
            errors.append("PATCHES[%d] name must be a non-empty string"
                          % index)
        else:
            names.append(label)
        if not isinstance(values, tuple) or len(values) != len(labels):
            errors.append("PATCHES[%d] needs one value per macro" % index)
            continue
        for macro, value in enumerate(values):
            if not _whole(value) or not 0 <= value <= 127:
                errors.append("PATCHES[%d] values must be MIDI integers "
                              "0..127" % index)
                break
            if modes.get(macro) == "TOGGLE" and value not in (0, 127):
                errors.append("PATCHES[%d] TOGGLE values must be 0 or 127"
                              % index)
                break
    if len(set(names)) != len(names):
        errors.append("patch names must be unique")
    return errors


def _require_modules(cls):
    """The portability tier's construction-time half.

    The import is attempted here rather than read off the module-level
    guard, so blocking a module after the class module was imported still
    raises -- see `tests/test_portability_tier.py`.
    """
    for module in getattr(cls, "REQUIRES", ()):
        try:
            __import__(module)
        except ImportError:
            raise ImportError(
                "%s needs the %s module, which a stock CircuitPython board "
                "does not have" % (getattr(cls, "NAME", cls.__name__),
                                   module))


# --------------------------------------------------------------------------
# The component


class Component:
    """Base for a rebuilt effect: subclasses implement `_build`.

    The live surface below is the contract's, frozen by roadmap §3. A
    subclass supplies `NAME`, `TIER`, the macro and patch tables, `_build`
    and -- if it has macros -- `_apply_macro`.
    """

    #: The stable provider name `audioeffects.create()` discovers.
    NAME = None

    #: roadmap §3: STOCK or AUDIODSP, with REQUIRES naming the audiodsp-own
    #: modules an AUDIODSP class needs.
    TIER = STOCK
    REQUIRES = ()

    #: The contract's static reads. `CAPABILITIES` names `"tempo_sync"` if
    #: and only if the class reads `self._transport()`.
    CAPABILITIES = ()

    #: The index of a tempo-synced class's Sync switch, or None. While that
    #: macro is on, `transport_changed()` reads the host's tempo, and when
    #: it has moved applies the switch again, which re-reads the transport
    #: the way moving the switch to where it already is would.
    _SYNC_MACRO = None
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    #: Knob names, one per macro index; one mode per label; the private
    #: engineering spans behind them; and the patches on the 0-127 grid.
    MACRO_LABELS = ()
    MACRO_MODES = {}
    _MACRO_RANGES = ()
    PATCHES = {}

    #: Constructor options for which NaN means something the class defines
    #: (see `_without_nan`); every other NaN option is left out.
    _NAN_OWN = ()

    #: Every `self._output = node` in every subclass re-points one stable
    #: port. See `output_port` at the top of this module.
    _output = output_port

    def __init__(self, source, *options, **keywords):
        sample_rate = keywords.pop("sample_rate", None)
        transport = keywords.pop("transport", None)
        cls = type(self)
        _check_metadata(cls)
        _require_modules(cls)

        source_rate = getattr(source, "sample_rate", None)
        source_channels = getattr(source, "channel_count", None)
        if source_rate is None or source_channels is None:
            raise TypeError("an effect source must expose sample_rate and "
                            "channel_count")
        source_rate = int(source_rate)
        source_channels = int(source_channels)
        if sample_rate is None:
            sample_rate = source_rate
        else:
            sample_rate = int(sample_rate)
            if sample_rate != source_rate:
                raise ValueError(
                    "%s was asked for %d Hz around a %d Hz source; an effect "
                    "does not resample" % (cls.NAME, sample_rate, source_rate))
        if source_channels not in (1, 2):
            raise ValueError("an effect source must be 1 or 2 channels, not "
                             "%d" % source_channels)

        options, keywords = _without_nan(cls, options, keywords)

        self._source = source
        self._sample_rate = sample_rate
        self._channel_count = source_channels
        self._transport = static_transport if transport is None else transport
        #: The tempo `transport_changed()` last acted on; `_UNREAD` until
        #: it first reads one.
        self._followed_bpm = _UNREAD
        self._nodes = []
        self._resets = []
        self._deinits = []
        self._port = None
        self._output = None
        self._macros = []
        self._patch_index = 0
        self._deinited = False
        #: Whether a control has routed the output around the graph since the
        #: graph last played. See `_route_around` and `_rejoin`.
        self._stranded = False
        #: True only while `_build` is running.
        #:
        #: `_init_macros` applies a constructor `patch=` from inside
        #: `_build`, so `_apply_macro` can be handed a graph `_build` has
        #: not finished priming yet. A class that rewires or re-primes from
        #: a macro then primes twice, and a priming `play()` on a mixer
        #: voice pulls a block of the borrowed source there and then: the
        #: first pull's block is dropped when the second one replaces it,
        #: and the class's output starts 5.3 ms into the material.
        #: `Distortion` did that at every scoop patch, where the Character
        #: macro crosses 0.5 and the graph is rebuilt (audiocomponents#82).
        #: `Saturation` and `Overdrive` each grew a private flag for the
        #: same hazard; this is the one every class can read.
        self._constructing = True
        #: True while a class seeds its knobs from its constructor's
        #: arguments (the class sets it in `_build`) or `_restore` puts them
        #: back: a class that keeps an exact constructor value beside a knob
        #: (`_KEPT`) keeps it through a knob applied while this is set.
        self._seeding = False

        # A `LAZY_BUILD` class's constructor arms lazily, as a reset does
        # (`_play_voice`): a voice primes a block of silence, not the
        # source's first block, so a Mix 0 set before the first pull hands
        # out the source from frame 0 rather than from frame 256. The
        # silence is handed up by `get_buffer`, or where it is compiled out
        # by `_pull_node`.
        pull = getattr(audiocore, "get_buffer", None)
        self._lazy_pending = []
        self._arming_lazily = bool(cls.LAZY_BUILD and PORT is not None)
        try:
            self._build(*options, **keywords)
        finally:
            self._constructing = False
            self._arming_lazily = False
        self._hand_up_lazy(pull)

        if self._output is None:
            raise TypeError("%s._build() set no output" % cls.NAME)
        if len(self._macros) != len(cls.MACRO_LABELS):
            raise TypeError("%s._build() must call _init_macros() with one "
                            "value per macro" % cls.NAME)
        output_rate = int(getattr(self._output, "sample_rate", sample_rate))
        output_channels = int(getattr(self._output, "channel_count",
                                      source_channels))
        if output_rate != sample_rate:
            raise ValueError("%s built a %d Hz output around a %d Hz source"
                             % (cls.NAME, output_rate, sample_rate))
        if output_channels != source_channels:
            raise ValueError("%s built a %d channel output around a %d "
                             "channel source" % (cls.NAME, output_channels,
                                                 source_channels))

    @classmethod
    def create(cls, source, sample_rate, transport=None, **options):
        """The contract's construction boundary: the host names the rate it
        believes the graph runs at, and a mismatch with `source` is an
        error rather than a silent resample."""
        if not _whole(sample_rate) or sample_rate < 1:
            raise ValueError("sample_rate must be a positive integer")
        return cls(source, sample_rate=sample_rate, transport=transport,
                   **options)

    # -- what a subclass implements -----------------------------------

    def _build(self, **options):
        raise NotImplementedError("%s must implement _build()"
                                  % type(self).NAME)

    def _apply_macro(self, index, position):
        """Push macro `index`, at its 0..1 `position`, into the nodes. Read
        `self._macros[other]` for a setting that depends on two knobs."""
        raise NotImplementedError("%s declares macros but does not apply them"
                                  % type(self).NAME)

    # -- what a subclass builds with ----------------------------------

    def _own(self, node, reset=True, deinit=True):
        """Register a node this class built, and return it.

        Everything registered here is what `reset()` and `deinit()` walk, in
        reverse of the order it was registered -- tail first. `reset` and
        `deinit` may each be `False`, for a node that must be left alone, or
        a callable taking no arguments, for a node with its own clear (a
        child component's `reset`, `FeedbackDelay.clear`).
        """
        if node is self._source:
            raise ValueError("%s tried to own its borrowed source"
                             % type(self).NAME)
        if node is None:
            raise ValueError("%s owned nothing" % type(self).NAME)
        self._nodes.append(node)
        self._resets.append(reset)
        self._deinits.append(deinit)
        return node

    def _clear_nodes(self, keep=(), only=None):
        """Clear the nodes this class registered, tail first, the way
        `reset()` does, and leave the macros and the patch alone.

        Each node is cleared by what it was registered with: `reset=True` is
        `audiocore.reset_buffer`, a callable is called, `False` is skipped.
        `keep` names nodes to leave untouched (a node the bypass itself
        reads, which is still live). `only`, when given, limits the walk to
        those nodes - a sub-branch that a control takes out and puts back.
        """
        for position in range(len(self._nodes) - 1, -1, -1):
            node = self._nodes[position]
            if only is not None and not _named(node, only):
                continue
            if _named(node, keep):
                continue
            clear = self._resets[position]
            if clear is False:
                continue
            if clear is True:
                audiocore.reset_buffer(node)
            else:
                clear()

    def _route_around(self, bypass):
        """Point the output at `bypass` - the borrowed source, or the node
        a bypass hands back - and remember that the graph behind it has
        stopped being pulled.

        The stale-block defect (audiocomponents#113): a graph nobody pulls
        keeps whatever it held when the control moved - its filters' and
        shapers' memory, a lookahead line, the block a mixer voice had
        queued. Bring the control back after a pause and that plays out of
        silence: a 5 ms fragment of whatever was sounding when the knob went
        down. `_rejoin` is the other half. During `_build` nothing has
        played yet, so nothing is stranded.
        """
        if not self._constructing:
            self._stranded = True
        self._output = bypass

    def _rejoin(self, keep=()):
        """The graph `_route_around` left is about to be pulled again.

        If it was routed around since it last played, every node it
        registered is cleared (`_clear_nodes`, `keep` passed through) and
        this returns True: the caller then arms it the way its constructor
        does - the level gates, the voices, a coupling capacitor charged on
        the bias - so the graph comes back as it was built rather than as it
        was left. Clearing is the state silence would have decayed to for
        every node whose silence answer is zero; a node that answers silence
        with a constant (a biased shaper's coupling pole) is exactly what
        the constructor's charge settles, which is why re-arming is the
        caller's half. Returns False, and touches nothing, otherwise.
        """
        if not self._stranded:
            return False
        self._stranded = False
        self._clear_nodes(keep)
        return True

    #: Whether the source frames the graph's head took before it last
    #: stopped being pulled are ones the host has since read past. True
    #: everywhere but inside `_reset_rearmed` of a graph that was playing
    #: when the reset came: there they are the frames that come next.
    _source_read_past = True

    def _let_go_of_source(self, head, source, consumers=()):
        """`let_go_of_source`, when the frames `head` holds are old audio.

        Coming back off a Mix 0 bypass they are: the host read the source
        itself meanwhile. A reset of a graph that was playing is the other
        case. Nothing has read past them, and dropping them ran the class
        ahead of its source for good: the part of a 100-frame source buffer
        the head had taken, 28 frames after twelve 256-frame pulls
        (audiocomponents#157). Returns whether it let go."""
        if not self._source_read_past:
            return False
        return let_go_of_source(head, source, consumers)

    def _pcm(self, buffer_size=2048):
        """The keyword bundle an audiodsp node wants, at this instance's
        format. There is no module state behind it."""
        return {
            "sample_rate": self._sample_rate,
            "channel_count": self._channel_count,
            "bits_per_sample": 16,
            "samples_signed": True,
            "buffer_size": buffer_size,
        }

    def _hz(self, frequency):
        """A Hz-valued setting, clamped into the running rate's usable band.

        Rate-honesty (vision §3) asks a span to clamp at a lower rate rather
        than refuse: a 12 kHz shelf on a 22.05 kHz graph becomes the highest
        shelf that rate has, not a `ValueError` in the middle of a piece.
        Above Nyquist a biquad's coefficients fold over and the filter is
        noise rather than a filter, silently, so nothing may pass unclamped.
        """
        frequency = float(frequency)
        ceiling = self._sample_rate * 0.5 * NYQUIST_MARGIN
        if frequency > ceiling:
            return ceiling
        if frequency < 1.0:
            return 1.0
        return frequency

    def _init_macros(self, values, patch=None, defaults=None):
        """Seed the knobs from `_build`'s own arguments, in the macros' own
        units, and apply a patch over the top if one was asked for. This is
        deliberately the only route into `_apply_macro`, so the constructor
        and a later `set_macro` cannot drift apart.

        `defaults`, when given, holds one flag per value: True where the
        caller did not choose it (the argument was left out). That value is
        seeded on patch 0's step for its macro rather than at the value
        itself, so a fresh instance is patch 0 exactly, as the contract
        says, and a reset lands where a fresh instance starts. A value the
        caller passed is seeded where it is."""
        cls = type(self)
        if len(values) != len(cls.MACRO_LABELS):
            raise TypeError("%s seeded %d macros for %d labels"
                            % (cls.NAME, len(values), len(cls.MACRO_LABELS)))
        self._macros = [macro_position(span, value)
                        for span, value in zip(cls._MACRO_RANGES, values)]
        if defaults is not None:
            steps = cls.PATCHES[0][1]
            for index in range(len(values)):
                if defaults[index]:
                    self._macros[index] = position_of_midi(
                        self._mode(index), steps[index])
        for index in range(len(self._macros)):
            self._apply_macro(index, self._macros[index])
        self._patch_index = 0
        if patch is not None:
            self.program_change(patch)

    def macro(self, index):
        """What macro `index` currently stands for, in its own units."""
        self._check_live()
        return macro_value(type(self)._MACRO_RANGES[index],
                           self._macros[index])

    def _mode(self, index):
        """Macro `index`'s public mode. Every crossing between the 0-127 grid
        and a 0..1 position goes through this and `position_of_midi`, so the
        constructor, `set_macro`, `program_change` and `get_macro` cannot
        disagree about where a bipolar macro's centre is."""
        return type(self).MACRO_MODES.get(index, "UNIPOLAR")

    # -- the live surface ---------------------------------------------

    def _check_live(self):
        if self._deinited:
            raise RuntimeError("effect has been deinitialized")

    @property
    def output(self):
        self._check_live()
        return self._output

    @property
    def sample_rate(self):
        self._check_live()
        return self._sample_rate

    @property
    def channel_count(self):
        self._check_live()
        return self._channel_count

    @property
    def latency_samples(self):
        self._check_live()
        value = type(self).LATENCY_SAMPLES
        if not _whole(value) or value < 0:
            raise ValueError("latency_samples must be a non-negative integer")
        return value

    @property
    def tail_samples(self):
        self._check_live()
        value = type(self).TAIL_SAMPLES
        if value is None:
            return None
        if not _whole(value) or value < 0:
            raise ValueError("tail_samples must be a non-negative integer "
                             "or None")
        return value

    @property
    def capabilities(self):
        self._check_live()
        value = type(self).CAPABILITIES
        if not isinstance(value, tuple):
            raise ValueError("capabilities must be a tuple")
        for capability in value:
            if not isinstance(capability, str) or any(
                    ord(character) >= 128 for character in capability):
                raise ValueError("capabilities must be ASCII strings")
        return value

    @property
    def patch_index(self):
        self._check_live()
        return self._patch_index

    @property
    def transport(self):
        self._check_live()
        return self._transport

    def set_macro(self, index, value, channel=0, note_id=-1,
                  sample_position=0):
        """Set macro `index` from the 0-127 MIDI scale. Floats are accepted
        so a host with finer resolution need not quantize."""
        del channel, note_id
        _sample_position(sample_position)
        self._check_live()
        self._macro_index(index)
        self._macros[index] = position_of_midi(self._mode(index), value)
        self._patch_index = None
        self._lazily(self._apply_macro, index, self._macros[index])

    def get_macro(self, index):
        self._check_live()
        self._macro_index(index)
        return midi_of_position(self._mode(index), self._macros[index])

    def _macro_index(self, index):
        if isinstance(index, bool) or not isinstance(index, int):
            raise IndexError("macro index must be an integer")
        labels = type(self).MACRO_LABELS
        if not 0 <= index < len(labels):
            raise IndexError("%s has %d macros; no index %d"
                             % (type(self).NAME, len(labels), index))
        return index

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index`. An index this class does not have is ignored,
        as it is on an instrument: a program change is a wire message, and
        the wire carries indices nobody has to have implemented."""
        del channel, note_id
        _sample_position(sample_position)
        self._check_live()
        if isinstance(index, bool) or not isinstance(index, int):
            raise ValueError("program index must be a non-negative integer")
        if index < 0:
            raise ValueError("program index must be non-negative")
        patch = type(self).PATCHES.get(index)
        if patch is None:
            return
        self._lazily(self._apply_positions,
                     [position_of_midi(self._mode(macro), value)
                      for macro, value in enumerate(patch[1])],
                     index)

    def _apply_positions(self, positions, patch_index):
        """Set the macros to `positions` (0..1, one per macro from index 0),
        apply each, and record `patch_index`.

        This is the body of `program_change`, and the one path a patch and a
        restore share: a rack puts a child back as it built it by handing
        this the positions and patch index it recorded, which the public
        `set_macro` cannot do for a class whose grid is coarser than its
        positions or whose macros are not all live. A class that does work
        once per patch (a refresh, a re-route) does it here, not in
        `program_change`, so both paths get it.
        """
        for macro in range(len(positions)):
            self._macros[macro] = positions[macro]
            self._apply_macro(macro, positions[macro])
        self._patch_index = patch_index

    #: Attributes beyond the macros and the patch index that a class's
    #: constructor leaves and a put-back must restore with them: an exact
    #: constructor value kept beside its knob (`_glide_exact`). A class that
    #: keeps one names it here; `_record` and `_restore` carry it.
    _KEPT = ()

    #: What `reset()` reloads in place of patch 0: `None`, or a `_record()`
    #: a parent hands in for the length of one reset, so a child it built
    #: comes back as built in one step, never passing through patch 0.
    _reset_to = None

    def _record(self):
        """This instance's settings as they stand, for `_restore`: the
        positions, the patch index and the `_KEPT` values."""
        return (list(self._macros), self._patch_index,
                tuple(getattr(self, name) for name in type(self)._KEPT))

    def _restore(self, record):
        """Put back what `_record` returned, through `_apply_positions`.

        The kept values go back first and the positions are applied with
        `_seeding` set, the flag a class's constructor holds while it seeds
        the knobs: a class that drops an exact value when its knob moves
        keeps it while seeding, so the values and the knobs land together.
        """
        positions, patch_index, kept = record
        for name, value in zip(type(self)._KEPT, kept):
            setattr(self, name, value)
        self._seeding = True
        try:
            self._lazily(self._apply_positions, list(positions), patch_index)
        finally:
            self._seeding = False

    def pitch_bend(self, value, channel=0, sample_position=0):
        self._check_live()
        _pitch_bend(value)
        _channel(channel)
        _sample_position(sample_position)

    def control_change(self, controller, value, channel=0,
                       sample_position=0):
        self._check_live()
        _midi_value(controller, "controller")
        _bounded_midi(value)
        _channel(channel)
        _sample_position(sample_position)

    def channel_pressure(self, value, channel=0, sample_position=0):
        self._check_live()
        _bounded_midi(value)
        _channel(channel)
        _sample_position(sample_position)

    def transport_changed(self):
        """Tell the component the host's transport may have changed.

        A tempo-synced component with Sync on reads the transport, and when
        the tempo differs from the one it last followed, sets itself to it:
        a synced Time or Rate follows the song without a control moving. A
        host may call this once a block: with Sync off it reads nothing, and
        with the tempo unchanged it reads the transport and returns. A
        component that does not sync to tempo does nothing.
        """
        self._check_live()
        index = type(self)._SYNC_MACRO
        if index is None or self._macros[index] < 0.5:
            return
        transport = self._transport
        state = transport() if callable(transport) else transport
        bpm = state[2]
        last = self._followed_bpm
        if last is not _UNREAD and (bpm == last or (bpm != bpm and
                                                    last != last)):
            return
        self._followed_bpm = bpm
        self._apply_macro(index, self._macros[index])

    def _synced_beat(self):
        """`synced_beat` of the transport as it reads now, against the last
        good reading this instance took (`GOOD_BEAT` before the first),
        which it then keeps."""
        transport = self._transport
        state = transport() if callable(transport) else transport
        beat = synced_beat(state, getattr(self, "_good_beat", GOOD_BEAT))
        self._good_beat = beat
        return beat

    def poly_pressure(self, pitch, value, channel=0, note_id=-1,
                      sample_position=0):
        self._check_live()
        _midi_value(pitch, "pitch")
        _bounded_midi(value)
        _channel(channel)
        _note_id(note_id)
        _sample_position(sample_position)

    def reset(self):
        """Clear every node this class built, tail first, and restore patch
        0. The borrowed source is never named here."""
        self._check_live()
        self._clear_nodes()
        # Everything is clear now, so nothing is stranded: patch 0 coming
        # back off a bypass is the reset's own re-arm, not a second clear.
        self._stranded = False
        if self._reset_to is None:
            self.program_change(0)
        else:
            # A parent's reset: straight back to the settings it built this
            # with. Loading patch 0 on the way could re-arm a graph those
            # settings route around, and pull the source to do it. Those
            # settings may route around the graph, but it has not played
            # since it was cleared, so it is no more stranded than a graph
            # `_build` routes around.
            self._restore(self._reset_to)
            self._stranded = False

    #: Set inside `_reset_rearmed`, and inside the constructor for a class
    #: with `LAZY_BUILD`: `_play_voice` hands a voice a stand-in.
    _arming_lazily = False
    #: Whether the constructor arms the voices the way a reset does: on
    #: silence, so building takes nothing from the source. A class that
    #: primes at construction and then routes around its graph at Mix 0
    #: wants it; without it a Mix 0 set before the first pull hands out a
    #: source that has already given its first block to a voice.
    LAZY_BUILD = False

    def _play_voice(self, voice, source, loop=False):
        """`voice.play(source)`, except while `_reset_rearmed` (or a
        `LAZY_BUILD` constructor) arms the graph: then the voice is played
        on a Port standing on silence, so priming it takes nothing from the
        source, and the Port is pointed
        at `source` once the voice has given its silent block up. The next
        pull then fetches from `source` itself, which is what a fresh
        build's voice does after the block it primed has played."""
        if not self._arming_lazily or PORT is None:
            getattr(self, "_lazy_on", {}).pop(id(voice), None)
            voice.play(source, loop=loop)
            return
        ports = getattr(self, "_lazy_ports", None)
        if ports is None:
            ports = self._lazy_ports = {}
        port = ports.get(id(voice))
        # A graph built again since (Distortion's Character) released the
        # Port with the voice it stood in for; and a new voice may have the
        # old one's id.
        if port is not None and not _named(port, self._nodes):
            port = None
        if port is None:
            port = self._own(PORT(source), reset=False)
            ports[id(voice)] = port
        port.play(self._lazy_silence())
        voice.play(port, loop=loop)
        self._lazy_pending.append((voice, port, source))
        on = getattr(self, "_lazy_on", None)
        if on is None:
            on = self._lazy_on = {}
        on[id(voice)] = port

    def _lazily(self, call, *args):
        """`call(*args)` with the voices it arms armed lazily, for a
        `LAZY_BUILD` class, and the silence they primed handed up after.

        A control re-arms as a build does: a rejoin off Mix 0, a patch that
        builds the graph again, a reset a class does itself. Each primes
        its voices, and a voice primed off the source takes a block the
        bypass then never hands out when Mix 0 follows before a pull. So
        here, as in the constructor, they prime silence and are pointed at
        their sources once it is handed up. Inside a build or a reset that
        already arms lazily, it is the plain call."""
        if (self._arming_lazily or self._constructing or PORT is None
                or not type(self).LAZY_BUILD):
            return call(*args)
        self._arming_lazily = True
        try:
            call(*args)
        finally:
            self._arming_lazily = False
            self._hand_up_lazy(getattr(audiocore, "get_buffer", None))

    def _repoint_voice(self, voice, source):
        """Hand a voice that is playing a new source without priming it:
        the Port it stands on is pointed at `source`, and the next pull
        fetches from it. `source` is not reset: a stage the graph has been
        pulling all along carries on, where a reset jumped its state. A
        voice that is not on a Port is played (`_play_voice`). A route
        change re-primed one voice and left the other where it was: the
        two then ran a block apart for good, and the bypass that followed
        handed out a source a block short."""
        for at in range(len(self._lazy_pending)):
            if self._lazy_pending[at][0] is voice:
                port = self._lazy_pending[at][1]
                self._lazy_pending[at] = (voice, port, source)
                return
        port = getattr(self, "_lazy_on", {}).get(id(voice))
        if port is None or not _named(port, self._nodes):
            self._play_voice(voice, source)
            return
        port.play(source)

    def _lazy_silence(self):
        """A source that hands one block of zeros per pull and never ends:
        a width-1 `audioroute.MidSide` with nothing to play (MultiTapDelay's
        `_hush`). A two-frame sample would end, and a voice that saw it end
        would stop."""
        silence = getattr(self, "_lazy_zero", None)
        # Only while this graph still owns it: a graph built again since (a
        # patch across Distortion's Character) released it with the rest,
        # and a second reset that reached for it raised "deinitialized".
        if silence is not None and not _named(silence, self._nodes):
            silence = None
        if silence is None:
            import audioroute
            silence = self._own(audioroute.MidSide(
                width=1.0, sample_rate=self._sample_rate,
                channel_count=self._channel_count), reset=False)
            self._lazy_zero = silence
        return silence

    def _pull_node(self, node):
        """Pull one block of `node` through the graph from the control
        side, and return what `audiocore.get_buffer` returns, or None where
        the build has none (CircuitPython's default board builds compile it
        out). There a scratch one-voice Mixer primes from a width-1
        `audioroute.MidSide` standing on `node`: the voice's `play()` resets
        the MidSide, which forwards nothing upstream, and takes one block,
        so `node` is pulled once (for blocks of 256 frames or more) and its
        state moves exactly as a `get_buffer` would move it. The block
        itself can't be read back, and the voice is stopped again, so a
        later pull of the scratch Mixer reaches nothing. Returns False
        where neither way exists (no `audioroute`)."""
        pull = getattr(audiocore, "get_buffer", None)
        if pull is not None:
            return pull(node)
        if PORT is None:
            return False
        scratch = getattr(self, "_puller", None)
        if scratch is not None and not _named(scratch[0], self._nodes):
            scratch = None
        if scratch is not None and node is scratch[0]:
            return None
        if scratch is None:
            import audiomixer
            import audioroute
            mixer = self._own(audiomixer.Mixer(
                voice_count=1, **self._pcm(512 * self._channel_count)),
                reset=False)
            shim = self._own(audioroute.MidSide(
                width=1.0, sample_rate=self._sample_rate,
                channel_count=self._channel_count), reset=False)
            scratch = self._puller = (mixer, shim)
        mixer, shim = scratch
        shim.play(node)
        mixer.voice[0].play(shim)
        mixer.voice[0].stop()
        return None

    def _reset_rearmed(self, rearm, primed=(), building=False):
        """`reset()` for a class whose mixer voices each hold a block they
        primed ahead, and which arms them once, the way `_build` does.

        The base walk clears the nodes behind a voice but not the block the
        voice already took through them, so the first block after a reset
        was the old chain's and the next one a cleared chain's: a step of a
        few to a few hundred LSB where a fresh instance has none. Here every
        voice of every mixer this class owns is stopped, the `primed` flags
        are dropped, patch 0 goes in with the graph unarmed (`_ready` off,
        so no macro primes a voice part-way through the patch), and then
        `rearm()` arms the graph as coming back from a bypass does: the
        class's own refresh, called with the graph marked stranded so its
        `_rejoin` branch runs. With `building`, the patch goes in with
        `_constructing` set, for a class that builds part of its graph again
        on a macro and must not connect it part-way through the patch.

        **The arming is lazy: a reset takes nothing from the source.** Each
        voice the class plays through `_play_voice` primes a block of
        silence instead; each mixer is pulled once, which hands those up;
        and then the voices' stand-ins are pointed at their real sources,
        so the next pull fetches as a fresh build's next pull does. Where
        `audiocore.get_buffer` is compiled out, `_pull_node` hands the
        silence up, so a board resets as a desktop does. Saturation keeps its
        own `reset()`.
        """
        self._check_live()
        # The frames the graph's head has taken are old audio only if a
        # bypass left the graph un-pulled before the reset
        # (`_let_go_of_source`).
        read_past = self._stranded
        self._clear_nodes()
        for node in self._nodes:
            voices = getattr(node, "voice", None)
            if voices is None:
                continue
            for voice in voices:
                voice.stop()
        for name in primed:
            setattr(self, name, False)
        ready = getattr(self, "_ready", None)
        self._ready = False
        self._stranded = False
        # `building`: the patch goes in as a constructor's `patch=` does,
        # for a class that builds part of its graph again on a macro.
        self._constructing = bool(building)
        try:
            if self._reset_to is None:
                self.program_change(0)
            else:
                self._restore(self._reset_to)
        finally:
            self._ready = ready
            self._constructing = False
        # Stranded, so the refresh's `_rejoin` arms the graph (and clears
        # it again, which changes nothing). A patch 0 at Mix 0 routes
        # around instead; the Mix move off 0 arms it then.
        self._stranded = True
        self._lazy_pending = []
        # Lazily wherever the primed silence can be handed up before the
        # next pull: by `get_buffer`, or where it is compiled out by
        # `_pull_node` (a snapshot of the nodes, since `_pull_node` may own
        # its scratch mixer).
        pull = getattr(audiocore, "get_buffer", None)
        self._arming_lazily = PORT is not None
        self._source_read_past = read_past
        try:
            rearm()
        finally:
            self._arming_lazily = False
            self._source_read_past = True
        # Settings that route around the graph leave it as `_build` leaves
        # a graph it routes around: cleared and not played since, so not
        # stranded. A later Mix move then arms it as a fresh instance's
        # does, rather than clearing it again through `_rejoin`.
        self._stranded = False
        pending = self._lazy_pending
        self._lazy_pending = []
        if pending:
            # The graph as it stands now: a patch that builds part of it
            # again has new mixers.
            for node in list(self._nodes):
                if getattr(node, "voice", None) is None:
                    continue
                if pull is not None:
                    _drain(pull, node)
                else:
                    self._pull_node(node)
            for _voice, port, source in pending:
                port.play(source)

    def _hand_up_lazy(self, pull):
        """The constructor's half of the lazy arming: pull each mixer
        once, so the voices `_play_voice` armed on silence hand that
        silence up, then point their stand-ins at the real sources, so the
        first pull fetches as an eagerly primed build's would. `pull` is
        `get_buffer`, or None where it is compiled out and `_pull_node` does
        it."""
        pending = self._lazy_pending
        self._lazy_pending = []
        if not pending:
            return
        # The graph as it stands now (a snapshot: `_pull_node` may own its
        # scratch mixer): a patch that builds part of it again has new
        # mixers, and released the old voices' stand-ins. Only a mixer with
        # a voice on the silence: mid-stream, pulling one that plays its
        # real sources would take a block of them.
        for node in list(self._nodes):
            voices = getattr(node, "voice", None)
            if voices is None:
                continue
            if not any(voice is armed for armed, _p, _s in pending
                       for voice in voices):
                continue
            if pull is not None:
                _drain(pull, node)
            else:
                self._pull_node(node)
        for _voice, port, source in pending:
            if _named(port, self._nodes):
                port.play(source)

    def deinit(self):
        """Release every node this class built, tail first. Idempotent, and
        it never deinitialises the borrowed source."""
        if self._deinited:
            return
        # THE PORT GOES FIRST. A pump is holding it, and the walk below is
        # about to free buffers the pump would otherwise still be reading:
        # releasing the wire stops the pull at the wire, with a published
        # reason, instead of inside a Mixer whose voice buffers have gone.
        # Where `audioroute` is absent the port IS the tail node and the walk
        # releases it, exactly as before.
        port = self._port
        if PORT is not None and isinstance(port, PORT):
            port.deinit()
        for position in range(len(self._nodes) - 1, -1, -1):
            release = self._deinits[position]
            if release is False:
                continue
            if release is True:
                release = getattr(self._nodes[position], "deinit", None)
            if release is not None:
                release()
        self._nodes = []
        self._resets = []
        self._deinits = []
        self._output = None
        self._deinited = True


def _named(node, nodes):
    """Whether `node` is one of `nodes`, by identity. A node may define
    `__eq__`, and a walk over the graph means this object, not an equal
    one."""
    for other in nodes:
        if other is node:
            return True
    return False


# --------------------------------------------------------------------------
# MIDI-native argument checks, shared by the handlers above.


def _midi_value(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an integer from 0 through 127" % name)
    if not 0 <= value <= 127:
        raise ValueError("%s must be from 0 through 127" % name)
    return value


def _bounded_midi(value):
    return clamped_midi(value)


def _pitch_bend(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("pitch bend must be an integer from 0 through 16383")
    if not 0 <= value <= 16383:
        raise ValueError("pitch bend must be from 0 through 16383")
    return value


def _channel(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("channel must be an integer from 0 through 15")
    if not 0 <= value <= 15:
        raise ValueError("channel must be from 0 through 15")
    return value


def _note_id(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("note_id must be -1 or a non-negative integer")
    if value < -1:
        raise ValueError("note_id must be -1 or non-negative")
    return value


def _sample_position(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("sample_position must be a non-negative integer")
    if value < 0:
        raise ValueError("sample_position must be non-negative")
    return value
