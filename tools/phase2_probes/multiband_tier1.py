"""The Tier 1 invariant block for `MultibandCompressor`, on any of the three
interpreters.

Every check here is integer work -- a byte compare, a last-non-zero index, an
onset index, a peak, or a read of the live surface -- so the MicroPython and
CircuitPython columns of the evidence pack are runs and not inferences. No
numpy, no f-strings, no `wave`: this file has to import on
`cmods/bin/micropython` and `cmods/bin/circuitpython-effects` as well as on
the venv's CPython.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_tier1.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
        -X heapsize=512M tools/phase2_probes/multiband_tier1.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
        -X heapsize=512M tools/phase2_probes/multiband_tier1.py

The last line is the count of failing invariants; nothing else is a result.
"""

import math
import sys
from array import array

import audiocore
import audioeffects

CLASS = "MultibandCompressor"
RATES = (48000, 44100, 22050)
FAILURES = []


# --- plumbing --------------------------------------------------------------

def pcm_array(data):
    """`array('h')` over little-endian PCM, on every interpreter."""
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


def raw(frames, rate, channels):
    """A `RawSample` over one value per frame, duplicated across channels."""
    values = array("h")
    for value in frames:
        for _ in range(channels):
            values.append(value)
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def pull(node, frames, channels):
    out = array("h")
    want = frames * channels
    while len(out) < want:
        _result, buffer = audiocore.get_buffer(node)
        data = bytes(buffer)
        if not data:
            break
        out.extend(pcm_array(data))
    return out[:want]


def sine(hz, frames, rate, amplitude=9000):
    step = 2.0 * math.pi * hz / rate
    return [int(round(amplitude * math.sin(step * index)))
            for index in range(frames)]


def burst_then_silence(rate, channels, hz=80.0, burst_ms=40.0,
                       silence_seconds=1.0, amplitude=26000, bursts=1):
    """Silence, then a burst, then silence -- twice over, if asked.

    The leading silence is not decoration: emptying a node's pending buffer
    makes it re-read its source and `RawSample` hands its buffer back from
    the beginning, so a probe whose burst sits at frame 0 replays it after
    `reset()` and reads exactly like a delay line that was never cleared.

    `bursts=2` puts a second burst after the silence, which is what the
    "renders again" row needs: the source is never rewound -- the invariant
    forbids touching it -- so the material has to have something left in it.
    """
    lead = int(0.01 * rate)
    burst_frames = int(burst_ms * rate / 1000.0)
    body = sine(hz, burst_frames, rate, amplitude)
    tail = [0] * int(silence_seconds * rate)
    frames = [0] * lead + body + tail
    second = None
    if bursts > 1:
        second = len(frames)
        frames = frames + body + tail
    return (frames, lead, lead + burst_frames, second)


def dc_step(rate, hold_ms=200.0, silence_seconds=3.0, level=20000):
    lead = int(0.01 * rate)
    held = int(hold_ms * rate / 1000.0)
    return ([0] * lead + [level] * held + [0] * int(silence_seconds * rate),
            lead + held)


def build(rate, channels, source, **options):
    return audioeffects.create(CLASS, source, rate, **options)


def report(name, ok, detail):
    print("   %-34s %-5s %s" % (name, "pass" if ok else "FAIL", detail))
    if not ok:
        FAILURES.append("%s: %s" % (name, detail))


def last_non_zero(values):
    for index in range(len(values) - 1, -1, -1):
        if values[index]:
            return index
    return -1


def first_non_zero(values, floor=0):
    for index in range(len(values)):
        if abs(values[index]) > floor:
            return index
    return -1


def peak(values):
    top = 0
    for value in values:
        if value > top:
            top = value
        elif -value > top:
            top = -value
    return top


def rms(values, start=0):
    total = 0.0
    count = 0
    for index in range(start, len(values)):
        total += float(values[index]) * float(values[index])
        count += 1
    return math.sqrt(total / count) if count else 0.0


# --- the invariants --------------------------------------------------------

def check_wire(rate, channels, bands):
    """`Mix` at zero is a real bypass, byte-identical to the source."""
    frames = sine(440.0, int(0.30 * rate), rate, 14000)
    effect = build(rate, channels, raw(frames, rate, channels),
                   bands=bands, mix=0.0)
    out = pull(effect.output, len(frames), channels)
    differ = 0
    worst = 0
    for index in range(len(frames)):
        for channel in range(channels):
            delta = out[index * channels + channel] - frames[index]
            if delta:
                differ += 1
                if abs(delta) > worst:
                    worst = abs(delta)
    effect.deinit()
    report("WIRE mix 0, %d bands" % bands, differ == 0,
           "%d of %d samples differ, worst %d LSB"
           % (differ, len(frames) * channels, worst))


def check_tail(rate, channels, bands, crossover_low_hz):
    """Silence in, silence out; the decay reaches exact zero."""
    frames, _lead, end, _second = burst_then_silence(rate, channels)
    effect = build(rate, channels, raw(frames, rate, channels), bands=bands,
                   crossover_low_hz=crossover_low_hz, mix=1.0)
    declared = effect.tail_samples
    out = pull(effect.output, len(frames), channels)
    after = out[end * channels:]
    last = last_non_zero(after)
    tail_frames = -1 if last < 0 else (last // channels) + 1
    residual = peak(after[-(rate // 2) * channels:])
    effect.deinit()
    ok = (last >= 0) and residual == 0 and tail_frames <= declared
    report("TAIL crossover %5.0f Hz" % crossover_low_hz, ok,
           "tail %d samples (declared %d), residual %d LSB"
           % (tail_frames, declared, residual))


def check_dc(rate, channels, bands):
    """The audioif#23 shape: a DC step, removed, must settle on exact zero."""
    frames, removed = dc_step(rate)
    effect = build(rate, channels, raw(frames, rate, channels), bands=bands,
                   crossover_low_hz=40.0, mix=1.0)
    out = pull(effect.output, len(frames), channels)
    settled = out[-(rate // 2) * channels:]
    residual = peak(settled)
    effect.deinit()
    report("TAIL dc_step, crossover 40 Hz", residual == 0,
           "%d LSB held in the last half second after the step was removed"
           % residual)


def check_level(rate, channels, bands):
    """Unity through the summed path: every band at ratio 1, gain 0."""
    frames = sine(1000.0, int(0.35 * rate), rate, 9000)
    effect = build(rate, channels, raw(frames, rate, channels), bands=bands,
                   low_ratio=1.0, mid_ratio=1.0, high_ratio=1.0, mix=1.0)
    out = pull(effect.output, len(frames), channels)
    effect.deinit()
    start = int(0.20 * rate) * channels
    reference = rms([value for value in frames
                     for _ in range(channels)], start)
    measured = rms(out, start)
    decibels = (20.0 * math.log10(measured / reference)
                if reference and measured else -99.0)
    report("LEVEL 1 kHz, %d bands at unity" % bands, abs(decibels) <= 0.25,
           "%+.3f dB against the source" % decibels)


def check_click(rate, channels, bands):
    """Zero latency: the impulse leaves in the frame it entered."""
    position = 64
    frames = [0] * position + [24000] + [0] * int(0.20 * rate)
    wet = build(rate, channels, raw(frames, rate, channels), bands=bands,
                mix=1.0)
    reported = wet.latency_samples
    out = pull(wet.output, len(frames), channels)
    wet.deinit()
    onset = first_non_zero(out, 0)
    measured = (onset // channels) - position if onset >= 0 else -1
    report("CLICK impulse at frame %d" % position,
           measured == reported == 0,
           "reported %d, measured %d" % (reported, measured))


def check_state(rate, channels, bands):
    """`reset()`, `deinit()`, ownership, and the borrowed source."""
    frames, _lead, end, second = burst_then_silence(
        rate, channels, silence_seconds=0.15, bursts=2)
    source = raw(frames, rate, channels)
    effect = build(rate, channels, source, bands=bands, mix=1.0)
    primed = peak(pull(effect.output, end + 64, channels))
    effect.reset()
    after = peak(pull(effect.output, 512, channels))
    report("STATE reset clears every node", primed > 0 and after == 0,
           "primed %d LSB, after reset %d LSB" % (primed, after))

    #: A reset that leaves the class silent for ever passes the row above.
    #: `audiomixer.Mixer.reset_buffer` **stops** its voices on the ported
    #: CircuitPython node and rewinds them on audioif's, and a stopped voice
    #: never plays again, so "after reset 0 LSB" is exactly what a permanent
    #: silence looks like. The class re-plays its voices in its own reset for
    #: that reason; this is the row that would catch it if it stopped. The
    #: source is never rewound here -- the invariant forbids touching it --
    #: so the material carries a second burst instead.
    revived = peak(pull(effect.output, second + 4096, channels))
    report("STATE it renders again after reset", revived > 0,
           "%d LSB on the probe's second burst after reset()" % revived)

    owned = effect._nodes
    report("STATE the source is not owned",
           all(node is not source for node in owned),
           "%d nodes owned, none of them the source" % len(owned))

    effect.deinit()
    closed = False
    try:
        effect.output
    except RuntimeError:
        closed = True
    twice = True
    try:
        effect.deinit()
    except Exception as error:            # noqa: BLE001 - the point is that
        twice = False                     # nothing is raised
        print("      second deinit raised %r" % (error,))
    report("STATE deinit closes the surface", closed and twice,
           "output raises after deinit, and deinit twice is safe")

    audiocore.reset_buffer(source)
    still = peak(pull(source, 4096, channels))
    report("STATE the source still renders", still > 0,
           "%d LSB off the borrowed source after the class over it was "
           "deinited" % still)


def check_caps(rate, channels, bands):
    calls = []

    def transport():
        calls.append(1)
        return (False, 0.0, 120.0, 4, 4)

    source = raw(sine(440.0, 8192, rate, 12000), rate, channels)
    effect = audioeffects.create(CLASS, source, rate, transport=transport,
                                 bands=bands)
    pull(effect.output, 4096, channels)
    capabilities = effect.capabilities
    effect.deinit()
    report("CAPS () and no transport read",
           capabilities == () and not calls,
           "capabilities %r, transport called %d times"
           % (capabilities, len(calls)))


def check_rate(rate, channels, bands):
    """Rate honesty: a corner above the usable band clamps, never refuses."""
    source = raw(sine(440.0, 4096, rate, 12000), rate, channels)
    effect = build(rate, channels, source, bands=bands)
    effect.set_macro(0, 127)
    effect.set_macro(1, 127)
    low = effect.crossover_low_hz
    high = effect.crossover_high_hz
    ceiling = rate * 0.5 * 0.98
    ok = low <= ceiling + 1e-6
    if bands == 3:
        ok = ok and high <= ceiling + 1e-6 and high >= low * 8.0 - 1e-6
    effect.deinit()
    report("RATE both corners at maximum", ok,
           "low %.1f Hz, high %s, Nyquist margin %.1f Hz"
           % (low, "n/a" if high is None else "%.1f Hz" % high, ceiling))


def check_alloc(rate, channels, bands):
    """Pulling `output` allocates nothing, against a bare-source control."""
    try:
        import gc
    except ImportError:
        report("ALLOC pulling output", True, "no gc module on this build")
        return
    if not hasattr(gc, "mem_alloc"):
        report("ALLOC pulling output", True,
               "n/a  gc.mem_alloc() is a MicroPython read; CPython's leg "
               "is tracemalloc, in the kit's STATE")
        return
    #: The control is a `Filter` with no filter at the Mixer's own block
    #: size, not the bare source: `audiocore.get_buffer` allocates its own
    #: (result, buffer) pair per call, so the comparison has to be against a
    #: node that is pulled the same number of times. A `RawSample` hands back
    #: its whole array in one call and would make the class look free.
    import audiofilters
    frames = sine(440.0, 200 * 256, rate, 12000)
    effect = build(rate, channels, raw(frames, rate, channels), bands=bands,
                   mix=1.0)
    pull(effect.output, 4096, channels)
    gc.collect()
    before = gc.mem_alloc()
    rendered = pull(effect.output, 200 * 128, channels)
    through_class = gc.mem_alloc() - before
    effect.deinit()

    control = audiofilters.Filter(filter=None, mix=1,
                                  buffer_size=128 * channels * 2,
                                  sample_rate=rate, channel_count=channels,
                                  bits_per_sample=16, samples_signed=True)
    control.play(raw(frames, rate, channels), loop=False)
    pull(control, 4096, channels)
    gc.collect()
    before = gc.mem_alloc()
    pull(control, 200 * 128, channels)
    through_control = gc.mem_alloc() - before
    report("ALLOC pulling output", through_class - through_control <= 0,
           "%d against a one-node control's %d, %+d bytes, on a render whose "
           "peak is %d LSB"
           % (through_class, through_control,
              through_class - through_control, peak(rendered)))


# --- the run ---------------------------------------------------------------

def main():
    name = sys.implementation.name
    print("%s Tier 1 invariants - %s" % (CLASS, name))
    print("=" * 72)
    for rate in RATES:
        for channels in (2, 1):
            print()
            print("%d Hz, %d channel%s"
                  % (rate, channels, "" if channels == 1 else "s"))
            for bands in (3, 2):
                check_wire(rate, channels, bands)
            check_level(rate, channels, 3)
            check_level(rate, channels, 2)
            check_tail(rate, channels, 3, 200.0)
            check_tail(rate, channels, 3, 40.0)
            check_dc(rate, channels, 3)
            check_click(rate, channels, 3)
            check_click(rate, channels, 2)
            check_state(rate, channels, 3)
            check_caps(rate, channels, 3)
            check_rate(rate, channels, 3)
            check_rate(rate, channels, 2)
            check_alloc(rate, channels, 3)
    print()
    print("=" * 72)
    for line in FAILURES:
        print("FAILED  %s" % line)
    print("%d failing invariants" % len(FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
