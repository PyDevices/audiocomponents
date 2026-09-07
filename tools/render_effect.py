"""Render one audioeffects class over one probe, on any of the three
interpreters, and export the WAV plus the FNV digest the measurement kit
compares.

    render_effect.py <Class> <probe> <outdir> [--rate 48000] [--channels 2]
                     [--block 256] [--macro n=v ...] [--patch n]
                     [--events events.json] [--transport tempo.json]
                     [--selftest]

`docs/effects-kit-spec.md` section 4. Deliberately dual-runtime, in
`tools/render_component.py`'s shape: stdlib-free of numpy, argparse,
pathlib and `wave` on purpose, streaming straight to disk and hashing
incrementally, so one file runs under all three of

    audiocomponents/.venv/bin/python tools/render_effect.py ...
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython ...
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython \
        -X heapsize=256M ...

The heap size is not optional on CircuitPython: its `audiocore.WaveFile`
refuses every stream this file can hand it ("file must be a file opened in
byte mode"), so the probe goes through the RawSample route and the whole
probe is resident. A three-second stereo probe at 48 kHz is 576 KB and the
default heap is smaller than that.

Every render is built through ``audioeffects.create(source, sample_rate,
**options)`` - never the module-level ``configure()``, never a ``patch=``
keyword - and writes two files next to each other: the PCM, and a JSON
sidecar carrying every axis the kit compares on (spec section 1: rate,
channel count, interpreter, and source block size).


The source block size, and why a node sits in front of the effect
-----------------------------------------------------------------
``--block`` is the spec's fourth axis: the number of frames the source
hands back in one ``get_buffer`` call. It is not cosmetic -
`MultibandCompressor` M5 renders **zero non-zero samples** from 16384-,
20000- and 32768-frame sources, because the Splitter's ring is 8192 frames
(`audioif_splitter.c:34-39`).

`audiocore.RawSample.get_buffer()` hands back the whole array in one call
and `audiocore.WaveFile`'s own buffer is capped at 1024 bytes on the native
builds (`audioif/src/audiocore/WaveFile.c`, "buffer length must be 8-1024",
and it halves what it is given), so neither source can be asked for a
stated block size directly, and the two native builds disagree about what
the number they do take even means. So the renderer re-blocks: the probe
feeds a bit-transparent `audiofilters.Filter(filter=None, mix=1)` whose
``buffer_size`` is ``block * channels * 2`` bytes, and *that* is what the
effect pulls from. Measured on all three interpreters, this delivers
exactly `block` frames per call at 256, 8192, 16384, 20000 and 32768 -
M5's whole ladder - and ``--selftest`` renders the probe through the
adapter alone and asserts the bytes come back identical, so the seam is
proved transparent rather than assumed to be.

The adapter is played with ``loop=False``, which gives the source
semantics TAIL and `dc_step` need: the probe is delivered exactly once and
the source then keeps supplying frames of silence, rather than looping or
going away.


What is deliberately not here
-----------------------------
The analysis. Section 1: the render is dual-runtime, the analysis is not.
Every FFT, fit and envelope belongs in `tools/effect_analysis.py` and its
`tools/measure_effect.py` CLI, on the desktop under CPython with numpy.
This file exports numbers only where they cost nothing to carry (frame
count, peak, whether the render is silence) and never analyses.
"""

import json
import sys

import audiocore
import audiofilters
import audioeffects


# --- the digest ------------------------------------------------------------

def checksum(data, value=2166136261):
    """FNV-1a over the bytes.

    Copied unchanged from `audioif/tests/parity/effects_component_probe.py`
    at line 15, which the kit spec names as the digest. `sum(data)` is a sum
    over UNSIGNED BYTES, so it is invariant under any set of byte deltas that
    cancel - a +256-LSB sample error paid for by a single -1-LSB error moves
    it by exactly zero. It is printed alongside so older per-architecture
    records stay comparable, and it is never the comparison.
    """
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


# --- event kinds, adopted from audioif/lib/audiorender/events.py -----------

# Spec section 8 leaves the event format open and says Phase 1 either adopts
# `events.py:27`'s serialisable tuple form or says why not. It is adopted:
# an event is (sample_position, kind, data, value), values normalised 0.0-1.0
# for macros, and ORDER breaks a tie at one position. NOTE_ON/NOTE_OFF are
# rejected rather than ignored - an effect has no notes, and a timeline that
# thinks it does is a mistake worth failing on.
MACRO = 6
PROGRAM = 9
ORDER = {MACRO: 0, PROGRAM: 1}


def deliver(effect, event):
    """Play one event on an effect, in `audiorender.events.deliver`'s shape.

    Values are normalised here and MIDI on the effect's side, so this is
    where the scale changes - a multiply, not a quantization.
    """
    _, kind, data, value = event
    if kind == MACRO:
        effect.set_macro(data, value * 127.0)
    elif kind == PROGRAM:
        effect.program_change(data)
    else:
        raise ValueError("event kind %r is not one an effect can take; "
                         "MACRO is %d and PROGRAM is %d" % (kind, MACRO,
                                                            PROGRAM))


# --- the transport stub, modelled on audiorender/tempo.py:12 ---------------

class Transport:
    """What `--transport` gives a class that reads one.

    An effect's transport is the callable `_core.static_transport` stands in
    for: it returns ``(playing, position_seconds, bpm, numerator,
    denominator)``. `audiorender/tempo.py:12`'s `TempoMap` is the model for
    the map itself - a list of ``(beat, bpm)`` or ``(beat, bpm, num, den)``
    rows, piecewise constant from that beat until the next - and the walk
    below is that class's arithmetic, kept here because `audiorender` is
    desktop-only and this file has to run on a board.

    Without one, `Rack` R7 and STATE's `tempo_sync` clause have nothing to
    read, which is why the flag exists.
    """

    def __init__(self, rows=((0.0, 120.0, 4, 4),), playing=True,
                 start_seconds=0.0, sample_rate=48000):
        self.rows = [tuple(row) for row in rows]
        self.playing = bool(playing)
        self.start_seconds = float(start_seconds)
        self.sample_rate = int(sample_rate)
        self.position_samples = 0

    def advance(self, frames):
        self.position_samples += int(frames)

    def _beat_at_seconds(self, seconds):
        elapsed = 0.0
        for index, row in enumerate(self.rows):
            start, bpm = row[0], row[1]
            end = (self.rows[index + 1][0]
                   if index + 1 < len(self.rows) else None)
            span = None if end is None else (end - start) * 60.0 / bpm
            if span is None or seconds <= elapsed + span:
                return start + (seconds - elapsed) * bpm / 60.0
            elapsed += span
        return self.rows[-1][0]

    def _row_at_beat(self, beat):
        current = self.rows[0]
        for row in self.rows:
            if beat >= row[0]:
                current = row
        return current

    def __call__(self):
        seconds = self.start_seconds + (self.position_samples
                                        / float(self.sample_rate))
        row = self._row_at_beat(self._beat_at_seconds(seconds))
        numerator = row[2] if len(row) > 2 else 4
        denominator = row[3] if len(row) > 3 else 4
        return (self.playing, seconds, float(row[1]), int(numerator),
                int(denominator))

    def describe(self):
        return {"rows": [list(row) for row in self.rows],
                "playing": self.playing,
                "start_seconds": self.start_seconds}


# --- WAV, without the `wave` module ---------------------------------------

def wav_header(data_len, sample_rate, channels):
    """Straight from `tools/render_component.py:29`."""
    byte_rate = sample_rate * channels * 2
    return (b"RIFF" + (36 + data_len).to_bytes(4, "little")
            + b"WAVEfmt " + (16).to_bytes(4, "little")
            + (1).to_bytes(2, "little") + channels.to_bytes(2, "little")
            + sample_rate.to_bytes(4, "little") + byte_rate.to_bytes(4, "little")
            + (channels * 2).to_bytes(2, "little") + (16).to_bytes(2, "little")
            + b"data" + data_len.to_bytes(4, "little"))


def _u16(data, offset):
    return data[offset] | (data[offset + 1] << 8)


def _u32(data, offset):
    return (data[offset] | (data[offset + 1] << 8)
            | (data[offset + 2] << 16) | (data[offset + 3] << 24))


def wav_info(path):
    """(sample_rate, channels, bits, data_offset, data_length) of a PCM WAV.

    A twelve-line RIFF walk rather than `wave`, which MicroPython does not
    have. Anything that is not 16-bit PCM is refused here rather than
    misread downstream.
    """
    handle = open(path, "rb")
    try:
        header = handle.read(12)
        if header[0:4] != b"RIFF" or header[8:12] != b"WAVE":
            raise ValueError("%s is not a RIFF/WAVE file" % path)
        rate = channels = bits = None
        offset = 12
        while True:
            handle.seek(offset)
            chunk = handle.read(8)
            if len(chunk) < 8:
                raise ValueError("%s has no data chunk" % path)
            name = chunk[0:4]
            length = _u32(chunk, 4)
            if name == b"fmt ":
                body = handle.read(min(length, 16))
                if _u16(body, 0) != 1:
                    raise ValueError("%s is not uncompressed PCM" % path)
                channels = _u16(body, 2)
                rate = _u32(body, 4)
                bits = _u16(body, 14)
            elif name == b"data":
                if bits != 16:
                    raise ValueError("%s is %s-bit; the kit's probes are 16"
                                     % (path, bits))
                return rate, channels, bits, offset + 8, length
            offset += 8 + length + (length & 1)
    finally:
        handle.close()


def wav_pcm_digest(path, chunk=8192):
    """FNV-1a of a WAV's PCM bytes, header excluded, without loading it."""
    rate, channels, bits, start, length = wav_info(path)
    handle = open(path, "rb")
    try:
        handle.seek(start)
        value = 2166136261
        remaining = length
        while remaining > 0:
            data = handle.read(min(chunk, remaining))
            if not data:
                break
            value = checksum(data, value)
            remaining -= len(data)
        return value
    finally:
        handle.close()


# --- the probe source ------------------------------------------------------

def _pcm_array(data):
    """`array('h')` over little-endian PCM, on every interpreter.

    MicroPython has no `memoryview.cast`; CircuitPython and CPython do.
    """
    from array import array
    values = array("h")
    try:
        values.extend(memoryview(data).cast("h"))
        return values
    except AttributeError:
        pass
    import struct
    step = 4096
    for offset in range(0, len(data), step * 2):
        piece = data[offset:offset + step * 2]
        values.extend(struct.unpack("<%dh" % (len(piece) // 2), piece))
    return values


def probe_source(path, rate, channels, force=None):
    """The probe as an audiocore sample, plus the name of the route taken.

    `WaveFile` is preferred: it streams, so a board is not asked to hold a
    fourteen-second probe in RAM. The desktop CircuitPython build refuses
    every stream this file can open it ("file must be a file opened in byte
    mode"), so there is a `RawSample` fallback, and the route taken is
    recorded in the export - a cross-interpreter digest that differs must
    never be readable as a class difference when it was a source one. The
    two routes were measured to produce identical bytes; `--selftest`
    re-checks that on whatever interpreter is running.
    """
    file_rate, file_channels, _bits, start, length = wav_info(path)
    if file_rate != rate:
        raise ValueError("probe %s is %d Hz, --rate says %d"
                         % (path, file_rate, rate))
    if file_channels != channels:
        raise ValueError("probe %s is %d-channel, --channels says %d"
                         % (path, file_channels, channels))
    if force != "RawSample":
        handle = open(path, "rb")
        try:
            sample = audiocore.WaveFile(handle)
            return sample, handle, "WaveFile", length // (channels * 2)
        except (TypeError, ValueError, OSError):
            handle.close()
            if force == "WaveFile":
                return None, None, "WaveFile", length // (channels * 2)
    handle = open(path, "rb")
    try:
        handle.seek(start)
        data = handle.read(length)
    finally:
        handle.close()
    sample = audiocore.RawSample(_pcm_array(data), sample_rate=rate,
                                 channel_count=channels)
    return sample, None, "RawSample", length // (channels * 2)


def block_adapter(source, rate, channels, block):
    """A bit-transparent node that re-blocks `source` to `block` frames.

    See the module docstring. The delivered block size is asserted by the
    caller against what was asked for, because a node that quietly halved it
    would move every digest in the kit and look like a class change.
    """
    adapter = audiofilters.Filter(filter=None, mix=1,
                                  buffer_size=block * channels * 2,
                                  sample_rate=rate, bits_per_sample=16,
                                  samples_signed=True,
                                  channel_count=channels)
    adapter.play(source, loop=False)
    return adapter


# --- construction ----------------------------------------------------------

#: Arguments a class cannot be built without, or that would make a probe run
#: absurd. Same table and same reasons as
#: `tests/parity/effects_library_smoke.py`: ConvolutionReverb's default
#: second of stereo impulse is 1.5 MB.
#: `GraphicEQ`'s entry is gone with its rebuild: the old class had no
#: default curve, the rebuilt one is flat by default and flat is a
#: wire, and handing it a curve here made patch 0 stop matching the
#: constructor's own defaults.
EXTRA_ARGUMENTS = {
    "ConvolutionReverb": {"seconds": 0.25},
}


def class_version():
    """The library version this render came from, for the export."""
    for candidate in ("VERSION", "../VERSION", "../../VERSION"):
        try:
            handle = open(candidate, "r")
        except OSError:
            continue
        try:
            return handle.read().strip()
        finally:
            handle.close()
    return "unknown"


def interpreter():
    name = sys.implementation.name
    version = ".".join(str(part) for part in sys.implementation.version[:3])
    return "%s %s" % (name, version)


# --- the render ------------------------------------------------------------

def render(effect, path, rate, channels, frames, events=(), transport=None):
    """Pull blocks until `frames` frames are written, delivering events on
    block boundaries.

    Streams straight to `path` and hashes incrementally, exactly as
    `render_component.render()` does - a whole render held in RAM is a
    MemoryError on MicroPython. The last block is clipped so the file is
    `frames` frames long and not a block more, because WIRE is a byte
    compare and a byte compare cannot tolerate a ragged tail.

    Returns (digest, byte_sum, nonzero_bytes, frames_written, blocks).
    """
    pending = sorted(events, key=lambda event: (event[0], ORDER[event[1]]))
    handle = open(path, "wb")
    handle.write(b"\x00" * 44)          # rewritten once the size is known
    digest = 2166136261
    byte_sum = 0
    nonzero = 0
    written = 0
    blocks = 0
    frame_bytes = channels * 2
    try:
        while written < frames:
            position = written
            while pending and pending[0][0] <= position:
                deliver(effect, pending.pop(0))
            result, buffer = audiocore.get_buffer(effect.output)
            data = bytes(buffer)
            if not data:
                break
            available = len(data) // frame_bytes
            if written + available > frames:
                data = data[:(frames - written) * frame_bytes]
                available = len(data) // frame_bytes
            handle.write(data)
            digest = checksum(data, digest)
            for byte in data:
                byte_sum += byte
                if byte:
                    nonzero += 1
            written += available
            blocks += 1
            if transport is not None:
                transport.advance(available)
        handle.seek(0)
        handle.write(wav_header(written * frame_bytes, rate, channels))
    finally:
        handle.close()
    return digest, byte_sum, nonzero, written, blocks


# --- probe resolution ------------------------------------------------------

PROBE_DIR = "tools/effect_probes"


def _manifest_paths():
    here = sys.argv[0]
    cut = here.rfind("/")
    root = here[:cut] if cut > 0 else "."
    return (PROBE_DIR + "/probes.json",
            root + "/effect_probes/probes.json",
            root + "/../" + PROBE_DIR + "/probes.json")


def load_manifest():
    for candidate in _manifest_paths():
        try:
            handle = open(candidate, "r")
        except OSError:
            continue
        try:
            manifest = json.load(handle)
        finally:
            handle.close()
        cut = candidate.rfind("/")
        return manifest, candidate[:cut] if cut > 0 else "."
    return None, None


def resolve_probe(name, rate, channels):
    """(path, expected digest or None, probe entry or None).

    A probe named in `probes.json` is checked against the digest the
    manifest records for it, so a stale probe cannot be mistaken for a
    fresh one - spec section 3's whole reason for the manifest. A bare
    path is allowed and says so in the export.
    """
    if name.endswith(".wav"):
        return name, None, None
    manifest, directory = load_manifest()
    if manifest is None:
        raise SystemExit("no probes.json found; run "
                         "tools/effect_probes/make_probes.py, or give "
                         "render_effect.py a path to a .wav")
    probe = manifest["probes"].get(name)
    if probe is None:
        raise SystemExit("probes.json has no probe %r (it has %d)"
                         % (name, len(manifest["probes"])))
    key = "%d/%d" % (rate, channels)
    entry = probe["files"].get(key)
    if entry is None:
        raise SystemExit("probe %r has no %s Hz %d-channel file; it has %s"
                         % (name, rate, channels,
                            ", ".join(sorted(probe["files"]))))
    return directory + "/" + entry["path"], entry["fnv1a"], entry


# --- self test -------------------------------------------------------------

def selftest(probe_path, rate, channels, block):
    """Prove the two seams this file adds are transparent, on whichever
    interpreter is running.

    Not in the spec's CLI line: added because section 6 holds every checker
    in the kit to a planted fault, and the block adapter is a checker's
    plumbing. It asserts (a) the adapter delivers exactly `block` frames,
    (b) the probe survives the adapter byte-identically, and (c) the
    WaveFile and RawSample routes agree. A run that cannot say those three
    things has not shown the renderer to be a wire.
    """
    _rate, _channels, _bits, start, length = wav_info(probe_path)
    handle = open(probe_path, "rb")
    try:
        handle.seek(start)
        expected = handle.read(length)
    finally:
        handle.close()
    frames = length // (channels * 2)

    results = {}
    for forced in ("WaveFile", "RawSample"):
        source, holder, route, _frames = probe_source(probe_path, rate,
                                                      channels, forced)
        if source is None:
            results[forced] = None
            continue
        adapter = block_adapter(source, rate, channels, block)
        audiocore.reset_buffer(adapter)
        got = b""
        delivered = None
        while len(got) < len(expected):
            _result, buffer = audiocore.get_buffer(adapter)
            data = bytes(buffer)
            if not data:
                break
            if delivered is None:
                delivered = len(data) // (channels * 2)
            got += data
        adapter.deinit()
        if holder is not None:
            holder.close()
        results[forced] = (delivered, got[:len(expected)] == expected)

    print("selftest %s  %d Hz  %d ch  block %d  (%d frames)"
          % (probe_path.rsplit("/", 1)[-1], rate, channels, block, frames))
    failures = 0
    seen = [route for route, value in results.items() if value is not None]
    for route in ("WaveFile", "RawSample"):
        value = results[route]
        if value is None:
            print("  %-10s route unavailable on %s" % (route, interpreter()))
            continue
        delivered, identical = value
        ok = (delivered == block) and identical
        failures += 0 if ok else 1
        print("  %-10s delivered %s frames/call (asked %d), probe survives "
              "byte-identical: %s  %s"
              % (route, delivered, block, identical, "" if ok else "FAIL"))
    if not seen:
        print("  no source route worked at all")
        return 1
    if failures:
        print("SELFTEST: FAILED")
        return 1
    print("SELFTEST: the adapter is a wire at block %d" % block)
    return 0


# --- CLI -------------------------------------------------------------------

USAGE = ("render_effect.py <Class> <probe> <outdir> [--rate 48000] "
         "[--channels 2]\n"
         "                 [--block 256] [--macro n=v ...] [--patch n]\n"
         "                 [--events events.json] [--transport tempo.json]\n"
         "                 [--selftest]")


def parse_args(argv):
    options = {"rate": 48000, "channels": 2, "block": 256, "macros": [],
               "patch": None, "events": None, "transport": None,
               "selftest": False}
    positional = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--rate":
            options["rate"] = int(argv[index + 1]); index += 2
        elif token == "--channels":
            options["channels"] = int(argv[index + 1]); index += 2
        elif token == "--block":
            options["block"] = int(argv[index + 1]); index += 2
        elif token == "--patch":
            options["patch"] = int(argv[index + 1]); index += 2
        elif token == "--events":
            options["events"] = argv[index + 1]; index += 2
        elif token == "--transport":
            options["transport"] = argv[index + 1]; index += 2
        elif token == "--selftest":
            options["selftest"] = True; index += 1
        elif token == "--macro":
            name, _, value = argv[index + 1].partition("=")
            options["macros"].append((int(name), float(value))); index += 2
        elif token.startswith("--"):
            raise SystemExit("unknown option %r\n%s" % (token, USAGE))
        else:
            positional.append(token); index += 1
    if len(positional) != 3:
        raise SystemExit(USAGE)
    options["cls"], options["probe"], options["outdir"] = positional
    return options


def _tag(path):
    """A filename-safe tag for an events or transport file."""
    name = path.rsplit("/", 1)[-1]
    if name.endswith(".json"):
        name = name[:-5]
    return "".join(character if (character.isalpha() or character.isdigit())
                   else "-" for character in name)


def load_events(path):
    handle = open(path, "r")
    try:
        document = json.load(handle)
    finally:
        handle.close()
    events = document["events"] if isinstance(document, dict) else document
    events = [tuple(event) for event in events]
    for event in events:
        if event[1] not in ORDER:
            raise SystemExit("%s carries event kind %r; an effect takes "
                             "MACRO (%d) and PROGRAM (%d) only, and a "
                             "timeline that thinks it has notes is a "
                             "mistake worth failing on"
                             % (path, event[1], MACRO, PROGRAM))
    return events


def load_transport(path, rate):
    handle = open(path, "r")
    try:
        document = json.load(handle)
    finally:
        handle.close()
    rows = document.get("rows")
    if rows is None:
        rows = [[0.0, document.get("bpm", 120.0),
                 document.get("numerator", 4),
                 document.get("denominator", 4)]]
    return Transport(rows=rows, playing=document.get("playing", True),
                     start_seconds=document.get("start_seconds", 0.0),
                     sample_rate=rate)


def main(argv):
    options = parse_args(argv)
    rate = options["rate"]
    channels = options["channels"]
    block = options["block"]

    path, expected, entry = resolve_probe(options["probe"], rate, channels)
    digest_of_probe = wav_pcm_digest(path)
    if expected is not None and digest_of_probe != int(expected, 16):
        raise SystemExit("probe %s does not match probes.json "
                         "(file %08x, manifest %s) - it is stale; "
                         "regenerate with tools/effect_probes/make_probes.py"
                         % (path, digest_of_probe, expected))

    if options["selftest"]:
        return selftest(path, rate, channels, block)

    try:
        import os
        os.mkdir(options["outdir"])
    except OSError:
        pass

    source, holder, route, probe_frames = probe_source(path, rate, channels)
    adapter = block_adapter(source, rate, channels, block)
    audiocore.reset_buffer(adapter)
    _result, first = audiocore.get_buffer(adapter)
    delivered = len(bytes(first)) // (channels * 2)
    if delivered != block:
        raise SystemExit("the block adapter delivered %d frames per call, "
                         "not the %d asked for; every digest in this run "
                         "would be incomparable" % (delivered, block))
    adapter.deinit()
    if holder is not None:
        holder.close()

    # Rebuilt, because the block check above consumed the first block.
    source, holder, route, probe_frames = probe_source(path, rate, channels)
    adapter = block_adapter(source, rate, channels, block)

    transport = (load_transport(options["transport"], rate)
                 if options["transport"] else None)
    arguments = dict(EXTRA_ARGUMENTS.get(options["cls"], {}))
    effect = audioeffects.create(options["cls"], adapter, rate,
                                 transport=transport, **arguments)

    # A patch replaces every macro, so on the command line it is applied
    # first and the --macro flags override it. That is the opposite of
    # `audiorender.events.ORDER`, which is right for a timeline (a program
    # change at a position replaces the block of macro values sent with it)
    # and wrong for a flag the operator typed to override the patch. Events
    # from --events keep ORDER exactly.
    if options["patch"] is not None:
        effect.program_change(options["patch"])
    for index, value in options["macros"]:
        effect.set_macro(index, value)

    events = load_events(options["events"]) if options["events"] else []
    frames = probe_frames + effect.latency_samples
    stem = "%s__%s__%d__%dch__blk%d" % (options["cls"], options["probe"],
                                        rate, channels, block)
    if options["patch"] is not None:
        stem += "__p%d" % options["patch"]
    for index, value in options["macros"]:
        stem += "__m%d-%g" % (index, value)
    # A timeline and a transport change the render, so they have to change
    # its name: two different renders sharing one filename is the stale
    # artifact the spec's section 6 says is worse than no render at all.
    if options["events"]:
        stem += "__ev%s" % _tag(options["events"])
    if options["transport"]:
        stem += "__tp%s" % _tag(options["transport"])
    wav_path = "%s/%s.wav" % (options["outdir"], stem)

    audiocore.reset_buffer(effect.output)
    digest, byte_sum, nonzero, written, blocks = render(
        effect, wav_path, rate, channels, frames, events, transport)

    export = {
        "class": options["cls"],
        "class_version": class_version(),
        "interpreter": interpreter(),
        "probe": options["probe"],
        "probe_path": path,
        "probe_digest": "%08x" % digest_of_probe,
        "probe_verified": expected is not None,
        "probe_frames": probe_frames,
        "source_route": route,
        "sample_rate": rate,
        "channel_count": channels,
        "block_frames": block,
        "block_delivered": delivered,
        "effect_block_frames": None,
        "macros": [[index, value] for index, value in options["macros"]],
        "patch": options["patch"],
        "events": options["events"],
        "event_count": len(events),
        "transport": transport.describe() if transport else None,
        "latency_samples": effect.latency_samples,
        "tail_samples": effect.tail_samples,
        "capabilities": list(effect.capabilities),
        "frames": written,
        "blocks": blocks,
        "digest_fnv1a": "%08x" % digest,
        "byte_sum": byte_sum,
        "nonzero_bytes": nonzero,
        "silent": nonzero == 0,
        "wav": wav_path,
    }
    export["effect_block_frames"] = (written // blocks) if blocks else None
    json_path = "%s/%s.json" % (options["outdir"], stem)
    handle = open(json_path, "w")
    try:
        json.dump(export, handle)
    finally:
        handle.close()

    effect.deinit()
    adapter.deinit()
    if holder is not None:
        holder.close()

    print("%s %s %d Hz %dch block %d -> %d frames  fnv %08x  sum %d  %s"
          % (options["cls"], options["probe"], rate, channels, block,
             written, digest, byte_sum,
             "SILENT" if export["silent"] else "audio"))
    print("  %s" % wav_path)
    print("  %s" % json_path)
    return 1 if export["silent"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
