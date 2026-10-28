"""The rebuilt `Rack`: a serial chain of effects as one effect.

One test per trait of the class card (T1-T6), each shown red on the card's
planted faults, and the `CLAIMS` table that ties every claim in the class
docstring to a test. Numpy-free: the planted classes and the trait checks
import on MicroPython and CircuitPython too, and T5 runs on all three
interpreters (`python tests/test_cpython_effects_rack.py` natively, from the
repository root with `MICROPYPATH=lib:tests/support`).

Most traits run on the card's probe chain K, which has a nested rack, a
delay line mid-chain, latency in three children and one tempo-synced
child. Every K check first asserts four leaves and a nonzero latency, so a
rack that builds nothing fails rather than passes. Expected sums and node
lists come from the same leaves built by hand, never from `rack.effects`.
"""

import os
import sys

try:
    import unittest
    TestCase = unittest.TestCase
except ImportError:                          # a native interpreter
    unittest = None
    TestCase = object

try:
    from array import array
except ImportError:                          # pragma: no cover
    array = None

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")
elif sys.implementation.name == "cpython":
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_HERE, "support"))
    sys.path.insert(0, os.path.dirname(_HERE))       # for `tools`

import audiocore
import audioeffects
from audioeffects import _component

VENDOR = "PyDevices"

Rack = audioeffects.Rack

CPYTHON = sys.implementation.name == "cpython"
RATES = (48000, 22050)
CHANNELS = (2, 1)
SEEDS = (1, 2, 3, 4, 5, 6, 7, 8)
BLOCK = 256

K = (("Fuzz", {}),
     ("Rack", {"chain": (("DigitalDelay", {"mix": 0.3, "feedback": 0.4}),
                         ("Vibrato", {}))}),
     ("ConvolutionReverb", {}))

#: K's leaves, in order, and the macros the card moves.
FUZZ, DELAY, VIBRATO, REVERB = range(4)
FUZZ_FUZZ = 0
FUZZ_MIX = 5
DELAY_FEEDBACK = 1
VIBRATO_DELAY = 4


def impulse():
    """2000 frames, int16 mono, clicks at 0, 700 and 1500."""
    ir = array("h", bytes(4000))
    ir[0] = 16384
    ir[700] = 8192
    ir[1500] = 4096
    return ir


#: A child built at a setting off the 0-127 grid (Reverb's Size 1.0), which
#: patch 0 must put back exactly, not on the grid.
OFF_GRID = (("Reverb", {"character": "chamber", "size": 1.0}),
            ("DigitalDelay", {"mix": 0.3}))


def c2():
    return (("CabinetSim", {}), ("ConvolutionReverb", {"impulse": impulse()}))


# --------------------------------------------------------------------------
# Material and rendering (the same protocol as kit_probes, numpy-free)


class Source:
    """int16 frames, BLOCK of them per `get_buffer`, counting rewinds."""

    def __init__(self, data, rate, channels):
        self.sample_rate = rate
        self.channel_count = channels
        self.bits_per_sample = 16
        self.samples_signed = True
        self._pcm = bytes(data)
        self._stride = BLOCK * channels * 2
        self._position = 0
        self.rewinds = 0

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self.rewinds += 1
        self._position = 0

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        chunk = self._pcm[self._position:self._position + self._stride]
        self._position += len(chunk)
        return (1 if self._position < len(self._pcm) else 0), chunk


class Switchable:
    """The rack's borrowed source, with a different source behind it.
    `swap` rewinds the new inner source itself, so `rewinds` counts only
    what the rack asked of the source it holds."""

    def __init__(self, inner):
        self.inner = inner
        self.sample_rate = inner.sample_rate
        self.channel_count = inner.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True
        self.rewinds = 0

    def swap(self, source):
        self.inner = source

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self.rewinds += 1
        self.inner._reset_buffer(single_channel_output, audio_channel)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        return self.inner._get_buffer(single_channel_output, audio_channel)


def noise_det(frames, seed, channels, dbfs=-12.0):
    """kit_probes.noise_det, the same bytes on every interpreter."""
    amplitude = 10 ** (dbfs / 20.0) * 32767.0
    state = seed
    out = array("h", bytes(2 * frames * channels))
    for i in range(frames):
        state = (1103515245 * state + 12345) & 0x7fffffff
        value = int(round(amplitude * ((state / 0x3fffffff) - 1.0)))
        for ch in range(channels):
            out[i * channels + ch] = value
    return out


def material(seed, channels, frames=48000):
    """4096 frames of silence, 8192 of noise at -12 dBFS, then silence."""
    out = array("h", bytes(2 * frames * channels))
    burst = noise_det(8192, seed, channels)
    start = 4096 * channels
    for i in range(min(len(burst), len(out) - start)):
        out[start + i] = burst[i]
    return out


def clicks(frames, channels, at, level=16384):
    out = array("h", bytes(2 * frames * channels))
    for frame in at:
        for ch in range(channels):
            out[frame * channels + ch] = level
    return out


def pull(node, frames, channels):
    """`frames` frames of `node` as bytes, padded with silence when it runs
    dry."""
    want = frames * channels * 2
    out = bytearray()
    while len(out) < want:
        data = bytes(audiocore.get_buffer(node)[1])
        if not data:
            out.extend(bytes(want - len(out)))
            break
        out.extend(data)
    return bytes(out[:want])


def fnv(data):
    """FNV-1a, 32 bits."""
    h = 0x811c9dc5
    for byte in data:
        h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
    return h


def samples(data):
    values = array("h")
    try:
        values.frombytes(bytes(data))
        return values
    except AttributeError:                       # MicroPython's array
        pass
    import struct
    values.extend(struct.unpack("<%dh" % (len(data) // 2), bytes(data)))
    return values


def silent(data):
    return not any(data)


# --------------------------------------------------------------------------
# The same leaves, by hand


def hand(source, rate, chain, transport=None):
    """(leaves, output): each leaf built around the previous output, a
    nested rack's entries inline."""
    leaves = []
    out = source
    for entry in chain:
        if isinstance(entry, str):
            name, options = entry, {}
        else:
            name, options = entry
        if name == "Rack":
            inner, out = hand(out, rate, options.get("chain", ()), transport)
            leaves.extend(inner)
            continue
        leaf = audioeffects.create(name, out, rate, transport=transport,
                                   **dict(options))
        leaves.append(leaf)
        out = leaf.output
    return leaves, out


def leaves(rack):
    """The leaf effects of a rack, nested racks walked in order."""
    found = []
    for child in rack.effects:
        if isinstance(child, Rack):
            found.extend(leaves(child))
        else:
            found.append(child)
    return found


def release(effects):
    for effect in reversed(effects):
        effect.deinit()


def live_reads(leaf):
    """{macro index: get_macro} over the indices this leaf has live."""
    reads = {}
    for index in range(len(type(leaf).MACRO_LABELS)):
        try:
            reads[index] = leaf.get_macro(index)
        except IndexError:
            pass
    return reads


def state_of(leaf):
    return (list(leaf._macros), leaf.patch_index, live_reads(leaf))


def is_released(node):
    """Released on this interpreter: the CPython twins mark `_deinited`; a
    native node raises on a guarded getter."""
    if getattr(node, "_deinited", False):
        return True
    try:
        node.channel_count
    except Exception:                                # noqa: BLE001
        return True
    return False


#: What `nodes_of` left out because it has no `deinit` on this interpreter
#: (Vibrato's ramp tap and splitter output, Python objects on CPython): named
#: in the evidence, not claimed.
NO_DEINIT = set()

#: How many nodes T5's last clean run found through the rack.
COUNTED = []


def nodes_of(leaf):
    """The nodes a leaf built that can be released: on CPython the kit's
    enumeration (its register and anything outside it), natively the
    register."""
    if CPYTHON:
        from tools.effect_measurements import enumerate_nodes
        found = enumerate_nodes(leaf)
    else:
        found = [("_nodes[%d]" % i, node)
                 for i, node in enumerate(leaf._nodes)]
    nodes = []
    for name, node in found:
        if hasattr(node, "deinit"):
            nodes.append(node)
        else:
            NO_DEINIT.add("%s.%s" % (type(leaf).NAME, name))
    return nodes


# --------------------------------------------------------------------------
# The planted faults


class MixerRack(Rack):
    """T1: an empty rack wraps its source in a one-voice unity Mixer."""

    def _build(self, chain=(), patch=None):
        Rack._build(self, chain, patch)
        if not self._effects:
            import audiomixer
            mixer = audiomixer.Mixer(voice_count=1, **self._pcm(BLOCK))
            mixer.voice[0].level = 1.0
            mixer.voice[0].play(self._source, loop=False)
            self._own(mixer)
            self._port = mixer


class PortFreeingRack(Rack):
    """T1: deinit is Component's, which releases the port first."""

    def deinit(self):
        _component.Component.deinit(self)


class ReversedRack(Rack):
    """T2: the entries built in reverse order."""

    def _build(self, chain=(), patch=None):
        Rack._build(self, tuple(reversed(tuple(chain))), patch)


class BareNestedRack(Rack):
    """T2: a nested rack's entries built without their options."""

    def _child(self, name, source, options):
        if name == "Rack":
            options = dict(options)
            options["chain"] = tuple(
                entry if isinstance(entry, str) else entry[0]
                for entry in options.get("chain", ()))
        return Rack._child(self, name, source, options)


class CachedLatencyRack(Rack):
    """T3: latency summed once, at construction; the tail stays live."""

    def _build(self, chain=(), patch=None):
        Rack._build(self, chain, patch)
        self._cached = Rack.latency_samples.fget(self)

    @property
    def latency_samples(self):
        self._check_live()
        return self._cached


class CachedTailRack(Rack):
    """T3: tail summed once, at construction."""

    def _build(self, chain=(), patch=None):
        Rack._build(self, chain, patch)
        self._cached = Rack.tail_samples.fget(self)

    @property
    def tail_samples(self):
        self._check_live()
        return self._cached


class SkipNoneRack(Rack):
    """T3: a child whose tail is None is skipped instead of making the
    rack's None."""

    @property
    def tail_samples(self):
        self._check_live()
        total = 0
        for child in self._effects:
            tail = child.tail_samples
            if tail is not None:
                total += tail
        return total


class ZeroLatencyRack(Rack):
    """T3: reports no latency (the old class did, when no child declared
    any)."""

    @property
    def latency_samples(self):
        self._check_live()
        return 0


class LastOutputResetRack(Rack):
    """T4: reset clears only the last child's output (the old class's
    shape), then patch 0."""

    def reset(self):
        self._check_live()
        if self._effects:
            audiocore.reset_buffer(
                _component.port_target(self._effects[-1].output))
        _component.Component.reset(self)


class ChildResetOnlyRack(Rack):
    """T4: each child's own reset and nothing after it."""

    def reset(self):
        self._check_live()
        for child in reversed(self._effects):
            child.reset()


class PublicRestoreRack(Rack):
    """T4: patch 0, and the put-back after each child's own reset, restore
    through the public `set_macro`."""

    def _apply_positions(self, positions, patch_index):
        _component.Component._apply_positions(self, positions, patch_index)
        for child, record in zip(self._effects, self._built):
            macros = record[0]
            for macro in range(len(macros)):
                child.set_macro(macro, _component.midi_of_position(
                    child._mode(macro), macros[macro]))

    def reset(self):
        self._check_live()
        for child in reversed(self._effects):
            child.reset()
        _component.Component.reset(self)


class SkipNestedRack(Rack):
    """T4: patch 0 leaves nested racks' children alone."""

    def _apply_positions(self, positions, patch_index):
        _component.Component._apply_positions(self, positions, patch_index)
        for child, record in zip(self._effects, self._built):
            if not isinstance(child, Rack):
                child._apply_positions(list(record[0]), record[1])


class NoRestoreRack(Rack):
    """T4: `program_change(0)` applies nothing."""

    def _apply_positions(self, positions, patch_index):
        _component.Component._apply_positions(self, positions, patch_index)


class LastOnlyDeinitRack(Rack):
    """T5: deinit releases the last child only."""

    def deinit(self):
        if self._deinited:
            return
        if self._effects:
            self._effects[-1].deinit()
        self._port = None
        self._deinited = True


class OutputNodeDeinitRack(Rack):
    """T5: deinit releases each child's output node, not the child (the old
    class's shape)."""

    def deinit(self):
        if self._deinited:
            return
        for child in reversed(self._effects):
            node = _component.port_target(child.output)
            if node is not child._source and hasattr(node, "deinit"):
                node.deinit()
        self._port = None
        self._deinited = True


class LeakyBuildRack(Rack):
    """T5: a build that raises part-way releases nothing."""

    def _build(self, chain=(), patch=None):
        built = []
        tail = self._source
        for entry in chain:
            name, options = (entry, {}) if isinstance(entry, (str, type)) \
                else (entry[0], dict(entry[1]))
            child = self._child(name, tail, options)
            built.append(child)
            tail = child.output
        self._effects = tuple(built)
        self._built = ()
        self._capabilities = ()
        self._port = tail
        self._init_macros((), patch)


class NoTransportRack(Rack):
    """T6: children built without the rack's transport."""

    def _child(self, name, source, options):
        options.pop("transport", None)
        if isinstance(name, str):
            if name == Rack.NAME:
                return NoTransportRack.create(source, self._sample_rate,
                                              **options)
            return audioeffects.create(name, source, self._sample_rate,
                                       **options)
        return name.create(source, self._sample_rate, **options)


class DeafRack(Rack):
    """T6: `transport_changed` does nothing."""

    def transport_changed(self):
        self._check_live()


class ClassCapabilitiesRack(Rack):
    """T6: capabilities are the class's `()`."""

    @property
    def capabilities(self):
        self._check_live()
        return type(self).CAPABILITIES


class PutBackRack(Rack):
    """T4: each child's own reset, which loads its patch 0, then the
    positions and patch index the rack built it with put back over the top
    (the class's first shape)."""

    def reset(self):
        self._check_live()
        for child in reversed(self._effects):
            child.reset()
        for child, record in zip(self._effects, self._built):
            child._apply_positions(list(record[0]), record[1])
        self._patch_index = 0


class PrimingRack(Rack):
    """T4 at Mix 0: a reset that takes a block from each pedal before the
    host pulls, which is what an eager re-arm does (the pedals' own re-arm
    is lazy since Phase 7; `PutBackRack` was red here only through the
    eager one, and is green at Mix 0 now)."""

    def reset(self):
        Rack.reset(self)
        for child in self._effects:
            pull(child.output, BLOCK, self._channel_count)


class PositionsOnlyRack(Rack):
    """T4: the restore puts back positions and patch index alone, not the
    exact constructor values a child keeps beside them."""

    def _build(self, chain=(), patch=None):
        Rack._build(self, chain, patch)
        self._built = tuple((record[0], record[1], ())
                            for record in self._built)


class LeakyPatchRack(Rack):
    """T5: a refused `patch=` raises with the built pedals unreleased (the
    class's first shape: the patch is applied outside the release)."""

    def _build(self, chain=(), patch=None):
        Rack._build(self, chain)
        self._init_macros((), patch)


def _recording_lowpass():
    base = audioeffects.LowPass

    class RecordingLowPass(base):
        """A LowPass that records each instance it builds."""

        built = []

        def _build(self, *args, **kwargs):
            base._build(self, *args, **kwargs)
            # The register, kept: deinit empties the instance's own.
            RecordingLowPass.built.append(list(self._nodes))

    return RecordingLowPass


#: The kit's plant-validity table: one planted fault per trait. The traits'
#: faults live in reset, deinit, identity and the host transport, which a
#: render at the kit's options does not reach; those rows are declared in
#: the kit (kit_common.DECLARED) and shown red here by the trait tests.
KIT_PLANTS = {
    "T1": MixerRack,
    "T2": ReversedRack,
    "T3": ZeroLatencyRack,
    "T4": ChildResetOnlyRack,
    "T5": LastOnlyDeinitRack,
    "T6": ClassCapabilitiesRack,
}


# --------------------------------------------------------------------------
# The traits, as checks that return what was wrong (empty is a pass)


def t1(cls, rate, channels):
    """With nothing in it, a rack is a patch cable."""
    wrong = []
    for build in ("direct", "create"):
        src = Source(material(1, channels, 4096), rate, channels)
        rack = cls(src) if build == "direct" else cls.create(src, rate)
        if rack.output is not src:
            wrong.append("%s: output is not the source" % build)
        if rack.latency_samples != 0 or rack.tail_samples != 0:
            wrong.append("%s: latency %r tail %r" % (
                build, rack.latency_samples, rack.tail_samples))
        if rack.capabilities != ():
            wrong.append("%s: capabilities %r" % (build, rack.capabilities))
        rack.reset()
        if src.rewinds:
            wrong.append("%s: reset rewound the source %d times"
                         % (build, src.rewinds))
        rack.deinit()
    try:
        from audioroute import Port
    except ImportError:                              # pragma: no cover
        return wrong
    data = material(2, channels, 8192)
    port = Port(Source(data, rate, channels))
    rack = cls(port)
    rack.deinit()
    try:
        got = pull(port, 8192, channels)
    except Exception as exc:                         # noqa: BLE001
        got = "raised %s" % type(exc).__name__
    want = pull(Port(Source(data, rate, channels)), 8192, channels)
    if got != want:
        wrong.append("the Port source does not render after deinit (%s)"
                     % (got if isinstance(got, str) else "bytes differ"))
    return wrong


def t2(cls, rate, channels, seeds, chain=K):
    """A rack sounds exactly like the same effects patched by hand."""
    wrong = []
    for seed in seeds:
        data = material(seed, channels)
        rack = cls.create(Source(data, rate, channels), rate, chain=chain)
        made, out = hand(Source(data, rate, channels), rate, chain)
        try:
            if len(leaves(rack)) != 4 or rack.latency_samples == 0:
                wrong.append("seed %d: built %d leaves, latency %d" % (
                    seed, len(leaves(rack)), rack.latency_samples))
            ours = fnv(pull(rack.output, 48000, channels))
            theirs = fnv(pull(out, 48000, channels))
            if ours != theirs:
                wrong.append("seed %d: %08x != %08x by hand"
                             % (seed, ours, theirs))
        finally:
            rack.deinit()
            release(made)
    return wrong


def _sums(made):
    latency = 0
    tail = 0
    for leaf in made:
        latency += leaf.latency_samples
        t = leaf.tail_samples
        tail = None if (tail is None or t is None) else tail + t
    return latency, tail


def t3(cls, rate, channels):
    """The rack reports the delay and ring-out of the whole board."""
    wrong = []
    seen = []
    src = Source(material(1, channels, 4096), rate, channels)
    rack = cls.create(src, rate, chain=K)
    made, _ = hand(Source(material(1, channels, 4096), rate, channels),
                   rate, K)
    ours = leaves(rack)
    as_built = [leaf._record() for leaf in made]
    try:
        if len(ours) != 4 or rack.latency_samples == 0:
            return ["built %d leaves, latency %d" % (
                len(ours), rack.latency_samples)], seen

        def read(when):
            want = _sums(made)
            got = (rack.latency_samples, rack.tail_samples)
            seen.append(got)
            if got != want:
                wrong.append("%s: rack %r, by hand %r" % (when, got, want))
            if rack.capabilities != ("tempo_sync",):
                wrong.append("%s: capabilities %r" % (when,
                                                      rack.capabilities))

        read("built")
        for leaf, macro in ((FUZZ, FUZZ_MIX), (VIBRATO, VIBRATO_DELAY),
                            (DELAY, DELAY_FEEDBACK)):
            back = made[leaf].get_macro(macro)
            for value in (0, 127, back):
                ours[leaf].set_macro(macro, value)
                made[leaf].set_macro(macro, value)
                read("leaf %d macro %d at %r" % (leaf, macro, value))
        # The same reset by hand: each leaf's own, tail first, reloading
        # the settings it was built with in place of its patch 0.
        rack.reset()
        for position in range(len(made) - 1, -1, -1):
            made[position]._reset_to = as_built[position]
            made[position].reset()
            made[position]._reset_to = None
        read("reset")
        if len(set(s[0] for s in seen)) < 3 or \
                len(set(s[1] for s in seen)) < 2:
            wrong.append("the moves did not move the reads: %r" % (seen,))
    finally:
        rack.deinit()
        release(made)
    rack = cls.create(Source(material(1, channels, 4096), rate, channels),
                      rate, chain=(("LowPass", {}),
                                   ("LadderFilter", {"resonance": 4.2})))
    try:
        if rack.tail_samples is not None:
            wrong.append("LowPass into a self-oscillating LadderFilter "
                         "reports tail %r"
                         % rack.tail_samples)
    finally:
        rack.deinit()
    return wrong, seen


def _moves(rack):
    found = leaves(rack)
    found[DELAY].set_macro(DELAY_FEEDBACK, 127)
    found[FUZZ].set_macro(FUZZ_FUZZ, 0)


def t4(cls, rate, channels, seeds, chains=("K", "C2")):
    """Reset clears the whole board and puts every pedal back where the
    rack set it."""
    wrong = []
    for which in chains:
        chain = {"K": K, "C2": c2(), "R": OFF_GRID}[which]
        for seed in seeds:
            key = "%s seed %d" % (which, seed)
            fresh_src = Switchable(Source(material(seed, channels), rate,
                                          channels))
            fresh = Rack.create(fresh_src, rate, chain=chain)
            want = fnv(pull(fresh.output, 48000, channels))
            fresh.deinit()

            src = Switchable(Source(material(seed + 1, channels), rate,
                                    channels))
            try:
                rack = cls.create(src, rate, chain=chain)
            except Exception as exc:                 # noqa: BLE001
                wrong.append("%s: build raised %r" % (key, exc))
                continue
            try:
                found = leaves(rack)
                if which == "K" and (len(found) != 4
                                     or rack.latency_samples == 0):
                    wrong.append("%s: built %d leaves" % (key, len(found)))
                    continue
                built = [state_of(leaf) for leaf in found]
                if which == "K":
                    _moves(rack)
                if silent(pull(rack.output, 24000, channels)):
                    wrong.append("%s: the first render is silent" % key)
                try:
                    rack.reset()
                except Exception as exc:             # noqa: BLE001
                    wrong.append("%s: reset raised %r" % (key, exc))
                    continue
                for index, leaf in enumerate(found):
                    if state_of(leaf) != built[index]:
                        wrong.append("%s: leaf %d reads %r, built %r" % (
                            key, index, state_of(leaf), built[index]))
                if src.rewinds:
                    wrong.append("%s: reset rewound the source %d times"
                                 % (key, src.rewinds))
                src.swap(Source(material(seed, channels), rate, channels))
                got = fnv(pull(rack.output, 48000, channels))
                if got != want:
                    wrong.append("%s: after reset %08x, fresh %08x"
                                 % (key, got, want))
            finally:
                rack.deinit()
        if which != "K":
            continue
        # program_change(0) alone: macros back, nothing cleared.
        src = Switchable(Source(material(1, channels), rate, channels))
        rack = cls.create(src, rate, chain=chain)
        try:
            found = leaves(rack)
            built = [state_of(leaf) for leaf in found]
            _moves(rack)
            pull(rack.output, 24000, channels)
            rack.program_change(0)
            for index, leaf in enumerate(found):
                if state_of(leaf) != built[index]:
                    wrong.append("program_change(0): leaf %d reads %r, built "
                                 "%r" % (index, state_of(leaf), built[index]))
            if src.rewinds:
                wrong.append("program_change(0) rewound the source")
        finally:
            rack.deinit()
    return wrong


def t5(cls):
    """Switching the rack off releases every part of every pedal in it."""
    wrong = []
    rate, channels = 48000, 2
    # A native node takes only a native source: the lifecycle matrix's
    # Feed, a Port around a re-blocked RawSample, on every interpreter.
    import lifecycle

    def feed():
        return lifecycle.Feed(data, rate, channels, "256", loop=False).port

    data = material(1, channels, 8192)
    src = feed()
    rack = cls.create(src, rate, chain=K)
    made, _ = hand(feed(), rate, K)
    try:
        found = leaves(rack)
        if len(found) != 4:
            return ["built %d leaves" % len(found)]
        nodes = []
        for leaf in found:
            nodes.extend(nodes_of(leaf))
        expected = 0
        for leaf in made:
            expected += len(nodes_of(leaf))
        COUNTED[:] = [len(nodes)]
        if len(nodes) != expected or not nodes:
            wrong.append("found %d nodes through the rack, %d by hand"
                         % (len(nodes), expected))
        pull(rack.output, 4096, channels)
        children = list(rack.effects) + found
        rack.deinit()
        alive = [i for i, node in enumerate(nodes) if not is_released(node)]
        if alive:
            wrong.append("%d of %d nodes still live: %r" % (
                len(alive), len(nodes),
                [type(nodes[i]).__name__ for i in alive]))
        try:
            if silent(pull(src, 4096, channels)):
                wrong.append("the source renders silence after deinit")
        except Exception as exc:                     # noqa: BLE001
            wrong.append("the source raises after deinit: %r" % exc)
        for child in children + [rack]:
            try:
                child.latency_samples
            except RuntimeError:
                continue
            except Exception as exc:                 # noqa: BLE001
                wrong.append("%s raised %s, not the contract's RuntimeError"
                             % (type(child).__name__, type(exc).__name__))
                continue
            wrong.append("%s still answers after deinit"
                         % type(child).__name__)
        try:
            rack.deinit()
        except Exception as exc:                     # noqa: BLE001
            wrong.append("a second deinit raised %r" % exc)
    finally:
        release(made)
    recording = _recording_lowpass()
    try:
        cls(feed(), chain=(recording, "NoSuchEffect"))
        wrong.append("a chain naming NoSuchEffect built")
    except ImportError:
        pass
    if len(recording.built) != 1:
        wrong.append("RecordingLowPass built %d times"
                     % len(recording.built))
    else:
        built = recording.built[0]
        live = [n for n in built if not is_released(n)]
        if not built or live:
            wrong.append("the half-built LowPass keeps %d of %d nodes live"
                         % (len(live), len(built)))
    return wrong


class Host:
    """A host transport: playing, at `bpm`."""

    def __init__(self, bpm):
        self.bpm = bpm

    def __call__(self):
        return (True, 0.0, float(self.bpm), 4, 4)


def _echo(values, channels, click, lo, hi):
    """Frames from `click` to the loudest sample in [click+lo, click+hi)."""
    best = -1
    where = None
    for frame in range(click + lo, click + hi):
        v = abs(values[frame * channels])
        if v > best:
            best, where = v, frame
    return where - click


def t6(cls, rate, channels=2):
    """A tempo-synced pedal in the rack follows the song's tempo."""
    wrong = []
    first = 16000 if rate == 48000 else 7350
    second = 9600 if rate == 48000 else 4410
    click1 = 4096
    change = ((click1 + first + 2048) // BLOCK + 1) * BLOCK
    click2 = change + (3 * rate) // 2
    frames = click2 + 2 * second
    host = Host(90)
    src = Source(clicks(frames, channels, (click1, click2)), rate, channels)
    rack = cls.create(src, rate, transport=host, chain=(("Rack", {
        "chain": (("DigitalDelay", {"sync": True, "division": 6,
                                    "feedback": 0.0, "mix": 1.0,
                                    "glide_ms": 800.0}),)}),))
    try:
        if rack.capabilities != ("tempo_sync",):
            wrong.append("capabilities %r" % (rack.capabilities,))
        head = pull(rack.output, change, channels)
        host.bpm = 150
        rack.transport_changed()
        rest = pull(rack.output, frames - change, channels)
        values = samples(head + rest)
        got1 = _echo(values, channels, click1, 64, 2 * first)
        got2 = _echo(values, channels, click2, 64, 2 * second)
        if abs(got1 - first) > 2:
            wrong.append("90 BPM: echo at %d, want %d" % (got1, first))
        if abs(got2 - second) > 2:
            wrong.append("150 BPM: echo at %d, want %d" % (got2, second))
    finally:
        rack.deinit()
    return wrong


#: Pedals that, built at Mix 0, re-arm their voices when their own reset
#: loads patch 0 (Mix on), which pulls a block of the source.
MIX0 = ("Compressor", "Saturation", "Bitcrusher", "DynamicEQ", "Exciter",
        "Overdrive")

#: Pedals that keep an exact constructor value beside its knob, each built
#: off the grid, with the knobs moved before the reset and Time after it.
EXACT = (("DigitalDelay", {"time_ms": 300.0, "glide_ms": 10.0, "mix": 1.0,
                           "feedback": 0.0}),
         ("TapeDelay", {"time_ms": 97.3, "glide_ms": 10.0, "mix": 1.0,
                        "feedback": 0.0}),
         ("AnalogDelay", {"time_ms": 97.3, "mix": 1.0, "feedback": 0.0}),
         ("SlapbackDelay", {"time_ms": 97.3}),
         ("PingPongDelay", {"time_ms": 97.3, "mix": 1.0, "feedback": 0.0}))


#: The exact constructor values those pedals keep.
KEPT = ("_time_exact", "_glide_exact")


def _feed(values, rate, channels):
    """A native-safe source: the lifecycle matrix's Feed, whose port can be
    pointed at fresh material without the rack seeing a rewind."""
    import lifecycle
    return lifecycle.Feed(values, rate, channels, "256", loop=False)


def _against_fresh(cls, rate, channels, chain, values, run, before=None):
    """[] if a `cls` rack fed `values` from just before a mid-stream reset
    renders what a freshly built `Rack` does under `run(rack)`; else what
    differed.
    `before(rack)` moves knobs ahead of the reset."""
    feed = _feed(values, rate, channels)
    fresh = Rack.create(feed.port, rate, chain=chain)
    try:
        want = run(fresh)
    finally:
        fresh.deinit()
    other = array("h", values)
    for i in range(len(other)):
        other[i] = -other[i] // 2
    feed = _feed(other, rate, channels)
    rack = cls.create(feed.port, rate, chain=chain)
    try:
        if before is not None:
            before(rack)
        pull(rack.output, 3000, channels)
        # The new material goes in ahead of the reset, so a block the reset
        # pulls is missing from what plays after it.
        feed.point(_feed(values, rate, channels).mat)
        rack.reset()
        got = run(rack)
    finally:
        rack.deinit()
    if got == want:
        return []
    a, b = samples(got), samples(want)
    first = 0
    while a[first] == b[first]:
        first += 1
    return ["after reset %08x, fresh %08x, first difference at frame %d"
            % (fnv(got), fnv(want), first // channels)]


def t4_mix0(cls, rate, channels, names=MIX0):
    """A pedal built at Mix 0 comes back from the rack's reset as built: on
    time, and through a later Mix move back up."""
    wrong = []
    values = noise_det(16384, 5, channels)
    for name in names:
        mix = list(getattr(audioeffects, name).MACRO_LABELS).index("Mix")

        def run(rack):
            head = pull(rack.output, 4096, channels)
            rack.effects[0].set_macro(mix, 100)
            return head + pull(rack.output, 8192, channels)

        for line in _against_fresh(cls, rate, channels,
                                   ((name, {"mix": 0.0}),), values, run):
            wrong.append("%s at Mix 0: %s" % (name, line))
    return wrong


def t4_exact(cls, rate, channels, cases=EXACT):
    """A pedal's exact constructor values come back from the rack's reset:
    a host's read-back of Time and a Time move after it play what the
    freshly built rack's do."""
    wrong = []
    frames = 36000
    values = clicks(frames, channels, range(512, frames, 4800))
    for name, options in cases:
        labels = list(getattr(audioeffects, name).MACRO_LABELS)

        def before(rack):
            pedal = rack.effects[0]
            pedal.set_macro(0, 90)
            if "Glide" in labels:
                pedal.set_macro(labels.index("Glide"), 30)

        def run(rack):
            pedal = rack.effects[0]
            # A host that reads Time back and writes it keeps the exact one.
            pedal.set_macro(0, pedal.get_macro(0))
            head = pull(rack.output, 12000, channels)
            pedal.set_macro(0, 60)
            return head + pull(rack.output, frames - 12000, channels)

        for line in _against_fresh(cls, rate, channels,
                                   ((name, dict(options)),), values, run,
                                   before):
            wrong.append("%s %r: %s" % (name, options, line))
        # The values themselves, which a render at these settings may not
        # reach (an exact Time a whole frame away from its knob's).
        fresh = Rack.create(_feed(values, rate, channels).port, rate,
                            chain=((name, dict(options)),))
        rack = cls.create(_feed(values, rate, channels).port, rate,
                          chain=((name, dict(options)),))
        try:
            before(rack)
            rack.reset()
            for kept in KEPT:
                want = getattr(fresh.effects[0], kept, None)
                got = getattr(rack.effects[0], kept, None)
                if got != want:
                    wrong.append("%s: %s reads %r after reset, %r as built"
                                 % (name, kept, got, want))
        finally:
            rack.deinit()
            fresh.deinit()
    return wrong


def t4_widener(cls, rate, channels):
    """A StereoWidener built at Delay 20 ms comes back from the rack's reset
    as built: it plays the 20 ms, reads 20.0 back, and renders what the
    freshly built rack does, after its Delay was moved before the reset."""
    wrong = []
    frames = 12000
    values = clicks(frames, channels, range(512, frames, 2400))
    widener = audioeffects.StereoWidener
    chain = ((widener, {"delay_ms": 20.0}),)

    def before(rack):
        rack.effects[0].set_macro(1, 100)

    def run(rack):
        return pull(rack.output, frames - 512, channels)

    for line in _against_fresh(cls, rate, channels, chain, values, run,
                               before):
        wrong.append("StereoWidener: %s" % line)
    rack = cls.create(_feed(values, rate, channels).port, rate, chain=chain)
    try:
        before(rack)
        rack.reset()
        got = rack.effects[0].macro(1)
        if got != 20.0:
            wrong.append("StereoWidener: Delay reads %r after reset, 20.0 "
                         "as built" % (got,))
        if rack.effects[0]._delay_exact != 20.0:
            wrong.append("StereoWidener: _delay_exact is %r after reset"
                         % (rack.effects[0]._delay_exact,))
    finally:
        rack.deinit()
    return wrong


def t4_pitchshifter(cls, rate, channels):
    """A PitchShifter in a rack comes back from the rack's reset as built
    and re-armed: after its knobs were moved it renders what the freshly
    built rack does, whether it was built playing or at Mix 0, and a Mix
    move after the reset keeps the repeats."""
    wrong = []
    frames = 14000
    # A held level under the clicks, so the signal never crosses zero: a
    # level a re-arm leaves unplayed waits for a crossing it does not get.
    values = clicks(frames, channels, range(512, frames, 2400))
    for i in range(len(values)):
        values[i] += 6000
    shifter = audioeffects.PitchShifter
    cases = (
        ("defaults", {}, ((0, 40), (1, 100), (2, 90), (3, 50), (4, 90)),
         ()),
        ("off the defaults", {"pitch": -5.0, "fine": 20.0, "mix": 1.5,
                              "delay_ms": 30.0, "feedback": 0.4,
                              "window_ms": 20.0},
         ((0, 100), (4, 0), (2, 20)), ()),
        ("built at Mix 0", {"mix": 0.0, "pitch": 4.0},
         ((2, 100), (4, 80)), ()),
        ("Mix 0 after the reset", {"mix": 1.0, "feedback": 0.5},
         ((0, 20), (2, 40)), ((2, 0), (2, 100))),
    )
    for label, options, moves, after in cases:
        chain = ((shifter, options),)

        def before(rack, moves=moves):
            for index, value in moves:
                rack.effects[0].set_macro(index, value)

        def run(rack, after=after):
            out = pull(rack.output, 4000, channels)
            for index, value in after:
                rack.effects[0].set_macro(index, value)
                out += pull(rack.output, 3000, channels)
            return out

        for line in _against_fresh(cls, rate, channels, chain, values, run,
                                   before):
            wrong.append("PitchShifter, %s: %s" % (label, line))
    return wrong


def t4_airspace(cls, rate, channels):
    """An AirSpace built at Time 112.0813 ms (an exact value on a default's
    step) comes back from the rack's reset as built: it reads the same
    macros, and renders what the freshly built rack does, after its knobs
    were moved before the reset."""
    wrong = []
    frames = 12000
    values = clicks(frames, channels, range(512, frames, 2400))
    airspace = audioeffects.AirSpace
    chain = ((airspace, {"time_ms": 112.0813}),)

    def before(rack):
        rack.effects[0].set_macro(0, 100)
        rack.effects[0].set_macro(4, 30.5)
        rack.effects[0].set_macro(10, 64)

    def run(rack):
        return pull(rack.output, frames - 512, channels)

    for line in _against_fresh(cls, rate, channels, chain, values, run,
                               before):
        wrong.append("AirSpace: %s" % line)
    fresh = cls.create(_feed(values, rate, channels).port, rate, chain=chain)
    rack = cls.create(_feed(values, rate, channels).port, rate, chain=chain)
    try:
        want = [fresh.effects[0].macro(i) for i in range(11)]
        before(rack)
        rack.reset()
        got = [rack.effects[0].macro(i) for i in range(11)]
        if got != want:
            wrong.append("AirSpace: macros read %r after reset, %r as built"
                         % (got, want))
        if want[0] != 112.0813:
            wrong.append("AirSpace: Time reads %r as built, 112.0813"
                         % (want[0],))
        record = rack._built[0]
        flags = rack.effects[0]._snap
        if flags is record[2][0]:
            wrong.append("AirSpace: the rack's record shares its flags")
    finally:
        fresh.deinit()
        rack.deinit()
    return wrong


def t5_patch(cls):
    """A `patch=` the rack refuses releases every pedal it had built."""
    wrong = []
    data = material(1, 2, 4096)
    for patch in (-1, "x", True):
        recording = _recording_lowpass()
        try:
            cls(_feed(data, 48000, 2).port,
                chain=(recording, ("Rack", {"chain": (recording,)})),
                patch=patch)
            wrong.append("patch=%r built" % (patch,))
            continue
        except ValueError:
            pass
        if len(recording.built) != 2:
            wrong.append("patch=%r: %d pedals built" % (
                patch, len(recording.built)))
            continue
        for built in recording.built:
            live = [n for n in built if not is_released(n)]
            if not built or live:
                wrong.append("patch=%r: a LowPass keeps %d of %d nodes live"
                             % (patch, len(live), len(built)))
    return wrong


# --------------------------------------------------------------------------
# The tests



def _native_binaries():
    """{family: path or None}: LIFECYCLE_MICROPYTHON /
    LIFECYCLE_CIRCUITPYTHON, or the workspace's `bin/`."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bindir = None
    here = root
    for _up in range(5):
        here = os.path.dirname(here)
        if os.path.isfile(os.path.join(here, "bin", "micropython")):
            bindir = os.path.join(here, "bin")
            break
    found = {}
    for family in ("micropython", "circuitpython"):
        path = os.environ.get("LIFECYCLE_" + family.upper())
        if path is None and bindir is not None:
            path = os.path.join(bindir, family)
        found[family] = path if path and os.path.isfile(path) else None
    return found, root

class TheAdoption(TestCase):
    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-10-13, so `create()` serves this one. Serve another class under the name and this goes red."""
        import audiocore
        import audioeffects
        from array import array
        self.assertIs(audioeffects.Rack, Rack)
        served = audioeffects.create(
            "Rack",
            audiocore.RawSample(array("h", [0, 0] * 64), sample_rate=48000,
                                channel_count=2),
            48000)
        self.assertIsInstance(served, Rack)
        served.deinit()


class TestEmptyRack(TestCase):
    """T1. With nothing in it, a rack is a patch cable."""

    def test_an_empty_rack_is_a_patch_cable(self):
        for rate in RATES:
            for channels in CHANNELS:
                self.assertEqual(t1(Rack, rate, channels), [],
                                 (rate, channels))

    def test_t1_faults_are_red(self):
        for plant in (MixerRack, PortFreeingRack):
            self.assertNotEqual(t1(plant, 48000, 2), [], plant.__name__)

class TestByHand(TestCase):
    """T2. A rack sounds exactly like the same effects patched by
    hand."""

    def test_a_rack_sounds_like_its_pedals_by_hand(self):
        for rate in RATES:
            for channels in CHANNELS:
                self.assertEqual(t2(Rack, rate, channels, SEEDS), [],
                                 (rate, channels))

    def test_t2_faults_are_red(self):
        # Reversed: drive after the reverb is a different sound.
        for plant in (ReversedRack, BareNestedRack):
            wrong = t2(plant, 48000, 2, (1,))
            self.assertTrue(any("by hand" in w for w in wrong),
                            (plant.__name__, wrong))

    def test_a_mono_source_gives_a_mono_rack(self):
        src = Source(material(1, 1, 4096), 48000, 1)
        rack = Rack.create(src, 48000, chain=K)
        try:
            self.assertEqual(rack.channel_count, 1)
            self.assertEqual(rack.output.channel_count, 1)
            for leaf in leaves(rack):
                self.assertEqual(leaf.channel_count, 1)
        finally:
            rack.deinit()

    def test_effects_is_the_chain_in_order(self):
        rack = Rack.create(Source(material(1, 2, 4096), 48000, 2), 48000,
                           chain=K)
        try:
            self.assertIsInstance(rack.effects, tuple)
            self.assertEqual([type(c).NAME for c in rack.effects],
                             ["Fuzz", "Rack", "ConvolutionReverb"])
            self.assertEqual([type(c).NAME for c in leaves(rack)],
                             ["Fuzz", "DigitalDelay", "Vibrato",
                              "ConvolutionReverb"])
            self.assertIs(rack.effects[1].effects[0]._source,
                          rack.effects[0].output)
            self.assertIs(rack.output, rack.effects[-1].output)
        finally:
            rack.deinit()

    def test_the_rack_builds_no_node(self):
        rack = Rack.create(Source(material(1, 2, 4096), 48000, 2), 48000,
                           chain=K)
        try:
            self.assertEqual(rack._nodes, [])
            self.assertIs(rack.output, rack.effects[-1].output)
        finally:
            rack.deinit()

    def test_the_example_plays(self):
        src = Source(material(1, 2), 48000, 2)
        rack = Rack.create(src, 48000, chain=(
            ("Fuzz", {}),
            ("DigitalDelay", {"mix": 0.3, "feedback": 0.4}),
            ("ConvolutionReverb", {}),
        ))
        try:
            self.assertEqual(len(rack.effects), 3)
            self.assertFalse(silent(pull(rack.output, 24000, 2)))
        finally:
            rack.deinit()

    def test_chain_entries_keep_their_meaning(self):
        src = Source(material(1, 2, 4096), 48000, 2)
        rack = Rack(src, chain=("LowPass", ("HighPass", {}),
                                audioeffects.LowPass))
        try:
            self.assertEqual([type(c).NAME for c in rack.effects],
                             ["LowPass", "HighPass", "LowPass"])
        finally:
            rack.deinit()
        with self.assertRaises(ValueError):
            Rack(src, chain=(42,))
        with self.assertRaises(ImportError):
            Rack(src, chain=("NoSuchEffect",))

class TestReads(TestCase):
    """T3. The rack reports the delay and ring-out of the whole board,
    as it stands right now."""

    def test_latency_and_tail_are_the_live_sums(self):
        for rate in RATES:
            for channels in CHANNELS:
                wrong, seen = t3(Rack, rate, channels)
                self.assertEqual(wrong, [], (rate, channels))

    def test_t3_faults_are_red(self):
        for plant in (CachedLatencyRack, CachedTailRack, SkipNoneRack,
                      ZeroLatencyRack):
            wrong, _ = t3(plant, 48000, 2)
            self.assertNotEqual(wrong, [], plant.__name__)

class TestReset(TestCase):
    """T4. Reset clears the whole board and puts every pedal back where
    the rack set it."""

    def test_reset_puts_every_pedal_back(self):
        for rate in RATES:
            for channels in CHANNELS:
                self.assertEqual(t4(Rack, rate, channels, SEEDS), [],
                                 (rate, channels))

    def test_t4_faults_are_red(self):
        for plant in (LastOutputResetRack, ChildResetOnlyRack,
                      PublicRestoreRack, SkipNestedRack, NoRestoreRack):
            self.assertNotEqual(t4(plant, 48000, 2, (1,)), [],
                                plant.__name__)
        # The public surface cannot restore C2: a measured
        # ConvolutionReverb refuses every macro but Mix.
        wrong = t4(PublicRestoreRack, 48000, 2, (1,), chains=("C2",))
        self.assertTrue(any("raised" in w for w in wrong), wrong)

    def test_an_off_grid_child_comes_back_as_built(self):
        for rate in RATES:
            self.assertEqual(t4(Rack, rate, 2, (1, 2), chains=("R",)),
                             [], rate)

    def test_a_mix0_pedal_comes_back_as_built(self):
        for rate, channels in ((48000, 2), (22050, 1)):
            self.assertEqual(t4_mix0(Rack, rate, channels), [],
                             (rate, channels))

    def test_exact_constructor_values_come_back(self):
        for rate, channels in ((48000, 2), (22050, 1)):
            self.assertEqual(t4_exact(Rack, rate, channels), [],
                             (rate, channels))

    def test_a_stereo_widener_comes_back_with_its_exact_delay(self):
        self.assertEqual(t4_widener(Rack, 48000, 2), [])

    def test_a_pitch_shifter_comes_back_re_armed_and_as_built(self):
        self.assertEqual(t4_pitchshifter(Rack, 48000, 2), [])

    def test_an_airspace_comes_back_with_its_exact_time(self):
        self.assertEqual(t4_airspace(Rack, 48000, 2), [])
        self.assertEqual(t4_airspace(Rack, 22050, 1), [])

    def test_reset_as_built_faults_are_red(self):
        self.assertNotEqual(t4_mix0(PrimingRack, 48000, 2), [])
        for plant in (PutBackRack, PositionsOnlyRack):
            self.assertNotEqual(t4_exact(plant, 48000, 2), [],
                                plant.__name__)

    def test_reset_as_built_micropython(self):
        _native(self, "micropython", "T4")

    def test_reset_as_built_circuitpython(self):
        _native(self, "circuitpython", "T4")

    def test_a_host_reset_clears_the_last_pedal_only(self):
        # A delay into a filter: the host's reset_buffer on the output
        # clears the filter and leaves the delay's repeats playing.
        chain = (("DigitalDelay", {"mix": 1.0, "feedback": 0.6}),
                 ("LowPass", {}))
        rate, channels = 48000, 2
        data = material(1, channels, 96000)
        for host in (True, False):
            rack = Rack.create(Source(data, rate, channels), rate,
                               chain=chain)
            try:
                pull(rack.output, 16384, channels)
                if host:
                    audiocore.reset_buffer(rack.output)
                else:
                    rack.reset()
                after = pull(rack.output, 24000, channels)
                self.assertEqual(silent(after), not host, host)
            finally:
                rack.deinit()
        # On an empty rack the host's reset is a rewind of the source.
        src = Source(data, rate, channels)
        rack = Rack.create(src, rate)
        audiocore.reset_buffer(rack.output)
        self.assertEqual(src.rewinds, 1)
        rack.deinit()

class TestDeinit(TestCase):
    """T5. Switching the rack off releases every part of every pedal in
    it, including a rack that failed half-built."""

    def test_deinit_releases_every_pedal(self):
        self.assertEqual(t5(Rack), [])

    def test_t5_faults_are_red(self):
        for plant in (LastOnlyDeinitRack, OutputNodeDeinitRack,
                      LeakyBuildRack):
            self.assertNotEqual(t5(plant), [], plant.__name__)

    def test_a_refused_patch_releases_every_pedal(self):
        self.assertEqual(t5_patch(Rack), [])
        self.assertNotEqual(t5_patch(LeakyPatchRack), [])

    def test_deinit_releases_every_pedal_micropython(self):
        _native(self, "micropython", "T5")

    def test_deinit_releases_every_pedal_circuitpython(self):
        _native(self, "circuitpython", "T5")

class TestTempo(TestCase):
    """T6. A tempo-synced pedal in the rack follows the song's tempo,
    wherever it sits."""

    def test_a_synced_pedal_follows_the_tempo(self):
        for rate in RATES:
            self.assertEqual(t6(Rack, rate), [], rate)

    def test_k_capabilities_are_the_union(self):
        rack = Rack.create(Source(material(1, 2, 4096), 48000, 2), 48000,
                           chain=K)
        try:
            self.assertEqual(rack.capabilities, ("tempo_sync",))
        finally:
            rack.deinit()
        rack = Rack.create(Source(material(1, 2, 4096), 48000, 2), 48000,
                           chain=("LowPass",))
        try:
            self.assertEqual(rack.capabilities, ())
        finally:
            rack.deinit()

    def test_an_entry_keeps_its_own_transport(self):
        own = Host(150)
        rack = Rack.create(Source(material(1, 2, 4096), 48000, 2), 48000,
                           transport=Host(90),
                           chain=(("DigitalDelay", {"transport": own}),
                                  "DigitalDelay"))
        try:
            self.assertIs(rack.effects[0].transport, own)
            self.assertIs(rack.effects[1].transport, rack.transport)
        finally:
            rack.deinit()

    def test_t6_faults_are_red(self):
        for plant in (NoTransportRack, DeafRack, ClassCapabilitiesRack):
            self.assertNotEqual(t6(plant, 48000), [], plant.__name__)

class TestSurface(TestCase):
    """The surface is the chain: no macros, patch 0 alone."""

    def test_the_surface_is_the_chain(self):
        self.assertEqual(Rack.MACRO_LABELS, ())
        self.assertEqual(Rack.MACRO_MODES, {})
        self.assertEqual(Rack.PATCHES, {0: ("Default", ())})
        rack = Rack.create(Source(material(1, 2, 4096), 48000, 2), 48000,
                           chain=K)
        try:
            rack.program_change(1)
            self.assertEqual(rack.patch_index, 0)
            with self.assertRaises(IndexError):
                rack.set_macro(0, 64)
        finally:
            rack.deinit()

    def test_the_class_is_stock_tier(self):
        self.assertEqual(Rack.TIER, _component.STOCK)
        self.assertEqual(Rack.REQUIRES, ())


#: The planted faults the native half of T5 holds red.
NATIVE_PLANTS = (LastOnlyDeinitRack, OutputNodeDeinitRack, LeakyBuildRack)


def _native_lines(part):
    """What `_native_main(part)` prints when every check holds."""
    if part == "T5":
        return (["T5|Rack|ok"]
                + ["T5|%s|red" % plant.__name__ for plant in NATIVE_PLANTS]
                + ["T5|patch|Rack|ok", "T5|patch|LeakyPatchRack|red",
                   "DONE"])
    return ["T4|mix0|Rack|ok", "T4|mix0|PrimingRack|red",
            "T4|exact|Rack|ok", "T4|exact|PutBackRack|red",
            "T4|exact|PositionsOnlyRack|red", "DONE"]


def _native(case, family, part):
    """Run `_native_main(part)` on a native interpreter and hold its lines
    to `_native_lines(part)`."""
    import subprocess
    import tempfile
    binaries, root = _native_binaries()
    binary = binaries[family]
    if binary is None:
        case.skipTest("no %s binary: set LIFECYCLE_%s"
                      % (family, family.upper()))
    with tempfile.TemporaryDirectory() as scratch:
        env = dict(os.environ, MICROPYPATH="lib:tests/support",
                   GCOV_PREFIX=scratch)
        done = subprocess.run(
            [binary, "-X", "heapsize=256M",
             "tests/test_cpython_effects_rack.py", part],
            capture_output=True, text=True, cwd=root, env=env)
    lines = [line for line in done.stdout.splitlines()
             if not line.startswith("T5|nodes|")]
    case.assertEqual(lines, _native_lines(part),
                     done.stdout[-2000:] + done.stderr[-2000:])


#: Every claim sentence of the class docstring, word for word, and the
#: tests that hold it.
CLAIMS = (
    ("For example: rack = Rack.create(source, 48000, chain=( (\"Fuzz\", {}), "
     "(\"DigitalDelay\", {\"mix\": 0.3, \"feedback\": 0.4}), "
     "(\"ConvolutionReverb\", {}), )) audio_out.play(rack.output) `chain` is "
     "a tuple of entries, each an effect name, a `(name, options)` pair whose "
     "options are that effect's constructor keywords, or an effect class in "
     "place of a name.",
     ("test_the_example_plays", "test_chain_entries_keep_their_meaning")),
    ("A rack adds no sound of its own: it sounds exactly like the same "
     "pedals patched by hand, one into the next.",
     ("test_a_rack_sounds_like_its_pedals_by_hand",
      "test_the_rack_builds_no_node")),
    ("Empty, it is a patch cable, and its output is your source.",
     "test_an_empty_rack_is_a_patch_cable"),
    ("A mono source gives a mono rack.",
     ("test_a_mono_source_gives_a_mono_rack",
      "test_a_rack_sounds_like_its_pedals_by_hand")),
    ("Order matters as soon as one pedal isn't a plain filter: drive into a "
     "reverb isn't a reverb into drive.", "test_t2_faults_are_red"),
    ("`latency_samples` and `tail_samples` are the sums of the pedals' own, "
     "read live, so they follow a pedal's knobs; the tail is `None` as soon "
     "as one pedal's is.", "test_latency_and_tail_are_the_live_sums"),
    ("There is no rack Mix, Bypass or Output knob, and patch 0 is its only "
     "patch.", "test_the_surface_is_the_chain"),
    ("To turn a pedal's knob, reach it through `rack.effects`, a tuple of "
     "the pedals in chain order.", "test_effects_is_the_chain_in_order"),
    ("`reset()` clears every pedal and puts each back to the settings the "
     "rack built it with, undoing knob moves made since.",
     ("test_reset_puts_every_pedal_back",
      "test_a_mix0_pedal_comes_back_as_built",
      "test_exact_constructor_values_come_back")),
    ("`program_change(0)` does the putting back alone, without clearing "
     "anything.", "test_reset_puts_every_pedal_back"),
    ("A host's `audiocore.reset_buffer(rack.output)` clears the last pedal "
     "only, and on an empty rack it rewinds your own source, because the "
     "output is your source.", "test_a_host_reset_clears_the_last_pedal_only"),
    ("A tempo-synced pedal follows the song's tempo wherever it sits, nested "
     "racks included: each pedal gets the rack's transport unless its entry "
     "names its own, and `transport_changed()` reaches every pedal.",
     ("test_a_synced_pedal_follows_the_tempo",
      "test_an_entry_keeps_its_own_transport")),
    ("`capabilities` is the union of the pedals' own, set when the rack is "
     "built.", ("test_k_capabilities_are_the_union",
                "test_a_synced_pedal_follows_the_tempo")),
    ("A rack builds nothing of its own, so it costs what its pedals cost.",
     "test_the_rack_builds_no_node"),
    ("The class itself runs on a stock board; a built rack needs whatever "
     "modules its pedals need.", "test_the_class_is_stock_tier"),
    ("`deinit()` releases every pedal, nested racks included, and never "
     "your source.", ("test_deinit_releases_every_pedal",
                      "test_an_empty_rack_is_a_patch_cable")),
    ("If an entry fails to build, or `patch` is refused, the pedals already "
     "built are released before the error reaches you.",
     ("test_deinit_releases_every_pedal",
      "test_a_refused_patch_releases_every_pedal")),
)


def _native_main(part="T5"):
    """T5 (or T4's reset-as-built checks) on this interpreter by itself:
    the clean class, then each plant, which must be red."""
    if part == "T4":
        for label, check, plants in (
                ("mix0", t4_mix0, (PrimingRack,)),
                ("exact", t4_exact, (PutBackRack, PositionsOnlyRack))):
            wrong = check(Rack, 48000, 2)
            print("T4|%s|Rack|%s" % (label, "ok" if not wrong
                                     else "RED(%s)" % wrong))
            for plant in plants:
                print("T4|%s|%s|%s" % (label, plant.__name__,
                                       "red" if check(plant, 48000, 2)
                                       else "GREEN"))
        print("DONE")
        return
    wrong = t5(Rack)
    print("T5|Rack|%s" % ("ok" if not wrong else "RED(%s)" % wrong))
    print("T5|nodes|%r|no deinit|%s" % (COUNTED, sorted(NO_DEINIT)))
    for plant in NATIVE_PLANTS:
        print("T5|%s|%s" % (plant.__name__, "red" if t5(plant) else "GREEN"))
    wrong = t5_patch(Rack)
    print("T5|patch|Rack|%s" % ("ok" if not wrong else "RED(%s)" % wrong))
    print("T5|patch|LeakyPatchRack|%s" % (
        "red" if t5_patch(LeakyPatchRack) else "GREEN"))
    print("DONE")


if __name__ == "__main__":
    if unittest is None:
        # Run as the module, not `__main__`: `_component` reads VENDOR off
        # the module a planted class is defined in.
        sys.path.insert(0, "tests")
        import test_cpython_effects_rack
        test_cpython_effects_rack._native_main(
            sys.argv[1] if len(sys.argv) > 1 else "T5")
    else:
        unittest.main()
