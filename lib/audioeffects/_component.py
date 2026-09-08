"""The construction shape every rebuilt effect class is built on.

`_core.py` is the pre-contract shape: a module-level `configure()` holds the
sample rate, and `Effect.__new__` sniffs the format off whatever it is handed.
The effects roadmap (§3, "What the contract freezes") frees that, and this
module is the replacement. It lands beside `_core.py` rather than over it:
the families not yet rebuilt keep importing `_core`, untouched, until Phase 6
retires it with the last of them.

What is different here, and why:

* **The format arrives with the source, and the factory confirms it.** There
  is no module state. `create(source, sample_rate, transport=None,
  **options)` is the contract's construction boundary and passes the rate it
  was asked for; a direct call for local code -- `Compressor(source,
  threshold_db=-18)` -- reads the rate and the channel count off the source
  it was handed. Neither path can be told a rate by something that ran
  earlier, which is the failure `configure()` invited.

* **A class enumerates the nodes it builds**, with `self._own(node)`, and
  `reset()` and `deinit()` walk that list. `_core.reset()` touches the output
  node only, so what a chain's reset actually clears depends on which node
  happened to be last. Every node clears something different:
  `audiofilters.Filter` and `Phaser` clear their own delay buffers and
  biquad states (`audioif/src/audiofilters/Filter.c:133-149`);
  `audioecho.FeedbackDelay` empties its whole line
  (`audioecho/FeedbackDelay.c:233-244`, "everything goes");
  `audiodynamics.Dynamics` clears its envelopes and its lookahead but lets
  the sidechain filter's memory and the last reported gain reduction survive
  on purpose (`shared/audioif_dynamics.c:281-295`); and `audiomixer`'s
  voices reset their sources recursively
  (`audiomixer/MixerVoice.c:97`), as does `audiospeed.SpeedChanger`
  (`audiospeed/SpeedChanger.c:109`). One walk over the class's own list is
  the same reset whatever the tail is.

  Two details of the roadmap's wording at that point do not survive contact
  with the files, checked 2026-09-07 and recorded here rather than left to
  be rediscovered. `audiofilters/Filter.c` and `Phaser.c` do **not** reset
  their source inside `reset_buffer` -- not in audioif
  (`src/audiofilters/Filter.c:133-149`) and not in upstream CircuitPython
  (`cmods/circuitpython/shared-module/audiofilters/Filter.c:126-139`). The
  recursion in those files is in `play()` (audioif `:161`, CircuitPython
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
  CircuitPython-ported nodes only. `AUDIOIF` needs at least one audioif-own
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
"""

import math
import sys

import audiocore

#: Portability tiers (roadmap §3). `STOCK` runs on a stock CircuitPython
#: board; `AUDIOIF` needs at least one audioif-own node and says which.
STOCK = "stock"
AUDIOIF = "audioif"

#: The audioif-own modules, as of the Phase 1 palette. A class whose `TIER`
#: is `AUDIOIF` names the ones it needs in `REQUIRES`, and every name must be
#: one of these -- a typo would otherwise buy a tier claim nothing checks.
AUDIOIF_MODULES = (
    "audiobiquad", "audioconvolve", "audiodynamics", "audioecho",
    "audioladder", "audiomath", "audioroute", "audioshaper", "audioverb",
)

#: The three public macro modes, as `audio-components.md` defines them.
MODES = ("UNIPOLAR", "BIPOLAR", "TOGGLE")

MAX_MACROS = 16
MAX_PATCHES = 128

#: How many taps one `audioroute.Splitter` fans out to. The limit lives in
#: the C (`AUDIOIF_SPLITTER_MAX_TAPS`, which raises "taps must be 1..4") and
#: the native modules do not export it, so classes that build parallel
#: branches count against this mirror rather than a literal 4 apiece.
SPLITTER_TAPS = 4

#: The fraction of Nyquist a Hz-valued span may reach. Biquad coefficients
#: lose their shape in the last couple of per cent, and the rate-honesty
#: invariant asks a span to clamp at a lower rate rather than refuse -- so
#: `self._hz()` clamps here instead of raising.
NYQUIST_MARGIN = 0.98


def static_transport():
    """The transport a component sees when it was given none."""
    return (False, 0.0, 120.0, 4, 4)


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


def macro_of(span, value):
    """`value` as the nearest integer on the 0-127 MIDI grid. Patch authoring
    and the tests that hold patch 0 to the constructor's defaults need this;
    nothing on the audio path calls it."""
    return int(round(macro_position(span, value) * 127))


# --------------------------------------------------------------------------
# Metadata


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
    if tier not in (STOCK, AUDIOIF):
        errors.append("TIER must be _component.STOCK or _component.AUDIOIF")
    requires = getattr(cls, "REQUIRES", ())
    if not isinstance(requires, tuple):
        errors.append("REQUIRES must be a tuple")
        requires = ()
    for module in requires:
        if module not in AUDIOIF_MODULES:
            errors.append("REQUIRES names %r, which is not an audioif-own "
                          "module" % (module,))
    if tier == AUDIOIF and not requires:
        errors.append("the audioif tier must name the modules it needs in "
                      "REQUIRES")
    if tier == STOCK and requires:
        errors.append("the stock tier may not require an audioif-own module")

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

    #: roadmap §3: STOCK or AUDIOIF, with REQUIRES naming the audioif-own
    #: modules an AUDIOIF class needs.
    TIER = STOCK
    REQUIRES = ()

    #: The contract's static reads. `CAPABILITIES` names `"tempo_sync"` if
    #: and only if the class reads `self._transport()`.
    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    #: Knob names, one per macro index; one mode per label; the private
    #: engineering spans behind them; and the patches on the 0-127 grid.
    MACRO_LABELS = ()
    MACRO_MODES = {}
    _MACRO_RANGES = ()
    PATCHES = {}

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

        self._source = source
        self._sample_rate = sample_rate
        self._channel_count = source_channels
        self._transport = static_transport if transport is None else transport
        self._nodes = []
        self._resets = []
        self._deinits = []
        self._output = None
        self._macros = []
        self._patch_index = 0
        self._deinited = False

        self._build(*options, **keywords)

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

    def _pcm(self, buffer_size=2048):
        """The keyword bundle an audioif node wants, at this instance's
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

    def _init_macros(self, values, patch=None):
        """Seed the knobs from `_build`'s own arguments, in the macros' own
        units, and apply a patch over the top if one was asked for. This is
        deliberately the only route into `_apply_macro`, so the constructor
        and a later `set_macro` cannot drift apart."""
        cls = type(self)
        if len(values) != len(cls.MACRO_LABELS):
            raise TypeError("%s seeded %d macros for %d labels"
                            % (cls.NAME, len(values), len(cls.MACRO_LABELS)))
        self._macros = [macro_position(span, value)
                        for span, value in zip(cls._MACRO_RANGES, values)]
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
        self._macros[index] = min(1.0, max(0.0, float(value) / 127.0))
        self._patch_index = None
        self._apply_macro(index, self._macros[index])

    def get_macro(self, index):
        self._check_live()
        self._macro_index(index)
        return self._macros[index] * 127.0

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
        for macro in range(len(patch[1])):
            self._macros[macro] = min(1.0, max(0.0,
                                               float(patch[1][macro]) / 127.0))
            self._apply_macro(macro, self._macros[macro])
        self._patch_index = index

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
        for position in range(len(self._nodes) - 1, -1, -1):
            clear = self._resets[position]
            if clear is False:
                continue
            if clear is True:
                audiocore.reset_buffer(self._nodes[position])
            else:
                clear()
        self.program_change(0)

    def deinit(self):
        """Release every node this class built, tail first. Idempotent, and
        it never deinitialises the borrowed source."""
        if self._deinited:
            return
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


# --------------------------------------------------------------------------
# MIDI-native argument checks, shared by the handlers above.


def _midi_value(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an integer from 0 through 127" % name)
    if not 0 <= value <= 127:
        raise ValueError("%s must be from 0 through 127" % name)
    return value


def _bounded_midi(value):
    return min(127.0, max(0.0, float(value)))


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
