"""`Rack` - a serial chain of effects, as a single effect.

The player's text is the class docstring, and the sentences in it that make
a claim are tied to tests by the `CLAIMS` table in the class's test file.
"""

VENDOR = "PyDevices"

from . import _component


class Rack(_component.Component):
    """A pedalboard cable run: name the effects in order and get a single
    effect back.

    For example:

        rack = Rack.create(source, 48000, chain=(
            ("Fuzz", {}),
            ("DigitalDelay", {"mix": 0.3, "feedback": 0.4}),
            ("ConvolutionReverb", {}),
        ))
        audio_out.play(rack.output)

    `chain` is a tuple of entries, each an effect name, a `(name, options)`
    pair whose options are that effect's constructor keywords, or an effect
    class in place of a name. `("Rack", {"chain": ...})` nests a rack.

    A rack adds no sound of its own: it sounds exactly like the same pedals
    patched by hand, one into the next. Empty, it is a patch cable, and its
    output is your source. A mono source gives a mono rack.

    Order matters as soon as one pedal isn't a plain filter: drive into a
    reverb isn't a reverb into drive.

    `latency_samples` and `tail_samples` are the sums of the pedals' own,
    read live, so they follow a pedal's knobs; the tail is `None` as soon as
    one pedal's is.

    There is no rack Mix, Bypass or Output knob, and patch 0 is its only
    patch. Turn a pedal's own Mix down; `ShimmerHall` and `AirSpace` are
    racks with knobs. The chain is set when the rack is built: to change
    pedals, build a new rack. To turn a pedal's knob, reach it through
    `rack.effects`, a tuple of the pedals in chain order.

    `reset()` clears every pedal and puts each back to the settings the
    rack built it with, undoing knob moves made since. `program_change(0)`
    does the putting back alone, without clearing anything.

    A host's `audiocore.reset_buffer(rack.output)` clears the last pedal
    only, and on an empty rack it rewinds your own source, because the
    output is your source. Call `rack.reset()` instead.

    A tempo-synced pedal follows the song's tempo wherever it sits, nested
    racks included: each pedal gets the rack's transport unless its entry
    names its own, and `transport_changed()` reaches every pedal.
    `capabilities` is the union of the pedals' own, set when the rack is
    built.

    A rack builds nothing of its own, so it costs what its pedals cost.
    Heavy pedals add up quickly on a small board: if the sound breaks up,
    trim the chain. The class itself runs on a stock board; a built rack
    needs whatever modules its pedals need.

    `deinit()` releases every pedal, nested racks included, and never your
    source. If an entry fails to build, or `patch` is refused, the pedals
    already built are released before the error reaches you.
    """

    NAME = 'Rack'
    DISPLAY_NAME = 'Effect Rack'
    CATEGORIES = ('Effect Rack',)
    VERSION = '0.1.0'

    TIER = _component.STOCK

    MACRO_LABELS = ()
    MACRO_MODES = {}
    _MACRO_RANGES = ()
    PATCHES = {0: ("Default", ())}

    def _build(self, chain=(), patch=None):
        built = []
        tail = self._source
        try:
            for entry in chain:
                name, options = _entry(entry)
                child = self._child(name, tail, options)
                built.append(child)
                tail = child.output
            self._effects = tuple(built)
            # What patch 0 and reset() restore: each child's settings as the
            # rack built it (`_record`).
            self._built = tuple(_record(child) for child in built)
            capabilities = []
            for child in built:
                for capability in child.capabilities:
                    if capability not in capabilities:
                        capabilities.append(capability)
            self._capabilities = tuple(capabilities)
            # No port of its own: the rack's output IS the last child's
            # output (its port), and an empty rack's IS the source. Set
            # directly, around the `_output` property, which would wrap it
            # in a new port.
            self._port = tail
            # Last, and inside the release: a `patch` the rack refuses
            # raises here, with every child built.
            self._init_macros((), patch)
        except BaseException:
            # The constructor never returns, so nobody else can release
            # what was built: do it here, tail first, and re-raise.
            for child in reversed(built):
                child.deinit()
            raise

    def _child(self, name, source, options):
        """One chain entry built around `source`, with the rack's transport
        unless the entry names its own."""
        transport = options.pop("transport", self._transport)
        if isinstance(name, str):
            if name == Rack.NAME:
                name = Rack
            else:
                import audioeffects
                return audioeffects.create(name, source, self._sample_rate,
                                           transport=transport, **options)
        return name.create(source, self._sample_rate, transport=transport,
                           **options)

    # -- the reads ------------------------------------------------------

    @property
    def effects(self):
        """The children, in chain order."""
        self._check_live()
        return self._effects

    @property
    def latency_samples(self):
        self._check_live()
        total = 0
        for child in self._effects:
            total += child.latency_samples
        return total

    @property
    def tail_samples(self):
        self._check_live()
        total = 0
        for child in self._effects:
            tail = child.tail_samples
            if tail is None:
                return None
            total += tail
        return total

    @property
    def capabilities(self):
        self._check_live()
        return self._capabilities

    # -- the surface ----------------------------------------------------

    def _apply_positions(self, positions, patch_index):
        """Patch 0: every child back to the settings the rack built it
        with. A nested rack restores inside itself."""
        _component.Component._apply_positions(self, positions, patch_index)
        for child, record in zip(self._effects, self._built):
            _restore(child, record)

    def transport_changed(self):
        self._check_live()
        for child in self._effects:
            child.transport_changed()

    def reset(self):
        """Each child's own reset, tail first, reloading the settings the
        rack built it with in place of its patch 0, so no child passes
        through a patch the rack never gave it: one built at Mix 0 would
        re-arm there and pull a block of the source. A nested rack's reset
        does the same inside itself. The borrowed source is never named."""
        self._check_live()
        for position in range(len(self._effects) - 1, -1, -1):
            child = self._effects[position]
            record = self._built[position]
            if isinstance(child, _component.Component):
                child._reset_to = record
                try:
                    child.reset()
                finally:
                    child._reset_to = None
            else:
                child.reset()
                _restore(child, record)
        self._stranded = False
        self._patch_index = 0

    def deinit(self):
        """Every child's own deinit, tail first. The port is never released
        here: it is the last child's, or, for an empty rack, the source."""
        if self._deinited:
            return
        for child in reversed(self._effects):
            child.deinit()
        self._port = None
        self._deinited = True


def _record(child):
    """What puts `child` back as it stands: its `_record()`, or, for a
    child on another base, its positions and patch index."""
    if isinstance(child, _component.Component):
        return child._record()
    return (list(child._macros), child._patch_index)


def _restore(child, record):
    """Put `child` back to `record`, without clearing anything."""
    if isinstance(child, _component.Component):
        child._restore(record)
    else:
        child._apply_positions(list(record[0]), record[1])


def _entry(entry):
    """(name or class, options dict) for one chain entry."""
    if isinstance(entry, (str, type)):
        return entry, {}
    try:
        name, options = entry
    except (TypeError, ValueError):
        raise ValueError("a chain entry is a NAME, an effect class or a "
                         "(NAME, options) pair, not %r" % (entry,))
    return name, dict(options)
