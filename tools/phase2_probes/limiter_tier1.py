"""`Limiter`'s Tier 1 invariants, on any of the three interpreters.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/limiter_tier1.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
        tools/phase2_probes/limiter_tier1.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
        -X heapsize=256M tools/phase2_probes/limiter_tier1.py

The measurement kit's rule is that the render is dual-runtime and the analysis
is not, and it is the right rule for anything with an FFT in it. These nine
invariants have no FFT: they are byte compares, an onset index, a last-non-zero
index and three reads of the live surface, all of them integer work on int16
frames. Doing them here rather than on rendered WAVs is what lets the MicroPython
and CircuitPython columns of the evidence pack be *runs* rather than
"the same class, so presumably the same answer".

stdlib-free of numpy, argparse and `wave` on purpose - the probes are
generated here in integer arithmetic so all three interpreters see identical
input bytes without a file in between.
"""

import array
import math
import sys

import audiocore
import audiofilters
import audioeffects

RATES = (48000, 44100, 22050)
CEILING, GAIN, LOOKAHEAD, RELEASE, TRUE_PEAK, KNEE = range(6)


# --- probes, generated identically everywhere ------------------------------

def stereo(values):
    out = array.array("h")
    for value in values:
        out.append(value)
        out.append(value)
    return out


def ramp_fs(frames=8192):
    """A repeating full-scale ramp, period 1024. WIRE needs samples above
    half scale in every block: a one-LSB scaling of the dry path is invisible
    below that under round-half-to-even."""
    values = []
    for index in range(frames):
        step = index % 1024
        value = int(step * 65536 / 1024) - 32768
        values.append(32767 if index % 37 == 0 else value)
    return stereo(values)


def burst_then_silence(rate, on_frames, total):
    values = []
    for index in range(total):
        if index < on_frames:
            values.append(int(24000 * math.sin(
                2.0 * math.pi * 1000.0 * index / rate)))
        else:
            values.append(0)
    return stereo(values), on_frames


def click(frames, at=1000, level=16000):
    values = [0] * frames
    values[at] = level
    return stereo(values)


def sine(rate, frames, hz, level):
    return stereo([int(level * math.sin(2.0 * math.pi * hz * index / rate))
                   for index in range(frames)])


def source_of(pcm, rate, channels=2, block=256):
    """The probe as a source that hands back `block` frames a call.

    `audiocore.RawSample` returns its whole buffer in one call and replays it
    from the beginning on `reset_buffer`, and a duck-typed Python source is
    refused outright by the native builds ("does not support
    'protocol_audiosample'"), so the re-blocking goes through the same
    bit-transparent `audiofilters.Filter` the kit's renderer uses. Played
    with `loop=False`, the probe is delivered exactly once and the adapter
    then supplies silence - which is the source semantics TAIL needs.
    """
    sample = audiocore.RawSample(pcm, sample_rate=rate,
                                 channel_count=channels)
    adapter = audiofilters.Filter(filter=None, mix=1,
                                  buffer_size=block * channels * 2,
                                  sample_rate=rate, bits_per_sample=16,
                                  samples_signed=True,
                                  channel_count=channels)
    adapter.play(sample, loop=False)
    return adapter


def int16(data):
    """`data` (any buffer of little-endian int16 frames) as a list of ints.

    `array.frombytes` is CPython's, `array.fromstring` is neither runtime's
    any more, and `memoryview.cast` is not on every build - so this decodes
    the bytes itself. All three interpreters then see the same integers,
    which is the point of running this file on all three.
    """
    raw = bytes(data)
    out = []
    for index in range(0, len(raw) - 1, 2):
        value = raw[index] | (raw[index + 1] << 8)
        out.append(value - 65536 if value >= 32768 else value)
    return out


def pull(node, frames, channels=2):
    """`frames` frames off `node` as a flat list of int16."""
    want = frames * channels
    out = []
    audiocore.reset_buffer(node)
    while len(out) < want:
        _result, data = audiocore.get_buffer(node)
        block = int16(data)
        if not block:
            out.extend([0] * (want - len(out)))
            break
        out.extend(block)
    return out[:want]


def build(rate, pcm, channels=2, **options):
    source = source_of(pcm, rate, channels)
    return audioeffects.create("Limiter", source, rate, **options), source


def db(value, full=32768.0):
    return -200.0 if value <= 0 else 20.0 * math.log10(value / full)


def peak(values):
    top = 0
    for value in values:
        magnitude = -value if value < 0 else value
        if magnitude > top:
            top = magnitude
    return top


def report(name, ok, detail):
    print("   %-34s %-5s %s" % (name, "pass" if ok else "FAIL", detail))
    return ok


# --- the invariants --------------------------------------------------------

def wire(rate):
    """Ceiling at the top of its span, Gain at 0: the defeated setting."""
    pcm = ramp_fs(8192)
    effect, _source = build(rate, pcm, ceiling_db=0.0, gain_db=0.0)
    out = pull(effect.output, 8192)
    effect.deinit()
    differ = sum(1 for index in range(len(out)) if out[index] != pcm[index])
    return report("WIRE ceiling 0 dB, gain 0", differ == 0,
                  "%d of %d samples differ" % (differ, len(out)))


def tail(rate):
    ok = True
    for lookahead in (0.0, 10.0):
        pcm, on = burst_then_silence(rate, rate // 5, rate)
        effect, _source = build(rate, pcm, ceiling_db=-6.0,
                                lookahead_ms=lookahead)
        declared = effect.tail_samples
        out = pull(effect.output, rate)
        effect.deinit()
        last = -1
        for index in range(on * 2, len(out)):
            if out[index]:
                last = index
        measured = 0 if last < 0 else (last // 2) - on + 1
        residual = peak(out[-(rate // 10) * 2:])
        ok = report("TAIL lookahead %4.1f ms" % lookahead,
                    measured <= declared and residual == 0,
                    "tail %d samples (declared %d), residual %d LSB"
                    % (measured, declared, residual)) and ok
    return ok


def level(rate):
    ok = True
    for ceiling in (0.0, -6.0, -24.0):
        pcm = sine(rate, rate // 4, 1000.0,
                   int(32767 * 10.0 ** ((ceiling - 6.0) / 20.0)))
        effect, _source = build(rate, pcm, ceiling_db=ceiling)
        out = pull(effect.output, rate // 4)
        effect.deinit()
        worst = 0
        for index in range(512 * 2, len(out)):
            delta = out[index] - pcm[index]
            if delta < 0:
                delta = -delta
            if delta > worst:
                worst = delta
        ok = report("LEVEL ceiling %+6.1f dB" % ceiling, worst == 0,
                    "worst deviation from the source %d LSB" % worst) and ok
    return ok


def gain_is_honest(rate):
    ok = True
    for gain in (0.0, 6.0, 12.0, 24.0):
        pcm = sine(rate, rate // 4, 1000.0, int(32767 * 10.0 ** (-40.0 / 20.0)))
        effect, _source = build(rate, pcm, ceiling_db=0.0, gain_db=gain)
        out = pull(effect.output, rate // 4)
        effect.deinit()
        measured = db(peak(out[1024:])) - db(peak(pcm))
        ok = report("GAIN %4.1f dB into the ceiling" % gain,
                    abs(measured - gain) < 0.1,
                    "measured %+.3f dB" % measured) and ok
    return ok


def click_latency(rate):
    ok = True
    for asked in (0.0, 1.5, 10.0):
        pcm = click(rate // 8)
        effect, _source = build(rate, pcm, ceiling_db=0.0,
                                lookahead_ms=asked)
        reported = effect.latency_samples
        out = pull(effect.output, rate // 8)
        effect.deinit()
        at = 0
        top = 0
        for index in range(0, len(out), 2):
            magnitude = out[index] if out[index] > 0 else -out[index]
            if magnitude > top:
                top, at = magnitude, index // 2
        measured = at - 1000
        expected = int(asked * rate / 1000.0)
        ok = report("CLICK lookahead %4.1f ms" % asked,
                    measured == reported == expected,
                    "reported %d, measured %d, floor(ms*fs/1000) %d"
                    % (reported, measured, expected)) and ok
    return ok


def state(rate):
    pcm, on = burst_then_silence(rate, rate // 5, rate)
    source = source_of(pcm, rate)
    effect = audioeffects.create("Limiter", source, rate, ceiling_db=-6.0,
                                 lookahead_ms=10.0)
    span = (on // 256) * 256
    pull(effect.output, span)
    primed = peak(pull(effect.output, 256))
    effect.reset()
    # reset() restores patch 0, which puts the lookahead back to zero (the
    # contract, audio-component-api.md:201-202). Re-arm it, so what is read
    # next is the ring itself and not the live input.
    effect.set_macro(LOOKAHEAD, 127)
    after = peak(pull(effect.output, 256))
    ok = report("STATE reset clears the ring", primed > 0 and after == 0,
                "primed %d LSB, after reset %d LSB" % (primed, after))
    nodes = list(effect._nodes)
    ok = report("STATE the source is not owned", source not in nodes,
                "%d nodes owned" % len(nodes)) and ok

    effect.deinit()
    effect.deinit()                                   # idempotent
    closed = False
    try:
        effect.output
    except RuntimeError:
        closed = True
    ok = report("STATE deinit closes the surface", closed,
                "output raises after deinit, and deinit twice is safe") and ok

    # The borrowed source is never deinitialised, so it must still render.
    # It has to be read where it still has audio in it: the source above has
    # been pulled past the burst by the reset check, and reading *that* would
    # report zero on a healthy build - a check that cannot fail. So this leg
    # gets its own source and its own probe, a continuous tone, and the read
    # is after the class over it has been deinited.
    tone = sine(rate, rate // 4, 1000.0, 20000)
    borrowed = source_of(tone, rate)
    passing = audioeffects.create("Limiter", borrowed, rate, ceiling_db=-6.0)
    pull(passing.output, 512)
    passing.deinit()
    still = peak(pull(borrowed, 512))
    ok = report("STATE the source still renders", still > 0,
                "%d LSB off the borrowed source after the class over it was "
                "deinited" % still) and ok

    releasable = [node for node in nodes if hasattr(node, "deinit")]
    if not releasable:
        print("   %-34s %-5s %s"
              % ("STATE the nodes refuse work", "n/a",
                 "audiodynamics.Dynamics has no deinit() on this build - "
                 "_component's walk finds nothing to call, so there is "
                 "nothing to observe. See the evidence pack, section 11"))
        return ok
    refused = 0
    for node in releasable:
        try:
            node.set(threshold_db=-1.0)
        except Exception:
            refused += 1
    return report("STATE the nodes refuse work", refused == len(releasable),
                  "%d of %d refused after deinit"
                  % (refused, len(releasable))) and ok


def capabilities(rate):
    calls = []

    def transport():
        calls.append(1)
        return (False, 0.0, 120.0, 4, 4)

    pcm = sine(rate, rate // 8, 440.0, 12000)
    source = source_of(pcm, rate)
    effect = audioeffects.create("Limiter", source, rate,
                                 transport=transport)
    pull(effect.output, rate // 8)
    ok = report("CAPS () and no transport read",
                effect.capabilities == () and not calls,
                "capabilities %r, transport called %d times"
                % (effect.capabilities, len(calls)))
    effect.deinit()
    return ok


def mono(rate):
    values = [0] * (rate // 4)
    for index in range(4800, 4848):
        values[index] = 32767
    pcm = array.array("h", values)
    effect, _source = build(rate, pcm, channels=1, ceiling_db=-12.0,
                            lookahead_ms=5.0)
    out = pull(effect.output, rate // 4, channels=1)
    channels = effect.channel_count
    effect.deinit()
    over = db(peak(out)) + 12.0
    return report("MONO channel_count 1",
                  channels == 1 and over <= 0.1,
                  "channel_count %d, peak %+.3f dB over the ceiling"
                  % (channels, over))


def rate_honest(rate):
    effect, _source = build(rate, sine(rate, 2048, 440.0, 8000),
                            lookahead_ms=10.0)
    reported = effect.latency_samples
    effect.deinit()
    return report("RATE lookahead 10 ms clamps",
                  reported == int(10.0 * rate / 1000.0),
                  "%d samples at %d Hz" % (reported, rate))


def allocation(rate):
    """Pulling `output` allocates nothing - measured against a control.

    Two things had to be kept out of this number. Decoding the frames into a
    Python list, which every other check here does, allocates hundreds of
    kilobytes by itself. And `audiocore.get_buffer` allocates its own
    `(result, buffer)` per call whatever is behind it - 1088 bytes a pull on
    the MicroPython build, measured on a bare source with no class in the
    path at all. So the reading is a *difference*: the same 200 pulls through
    the class and through its source alone, and the class's own allocation is
    what is left over.
    """
    try:
        import gc
        gc.mem_alloc
    except (ImportError, AttributeError):
        print("   %-34s %-5s %s" % ("ALLOC pulling output", "n/a",
                                    "gc.mem_alloc() is a MicroPython read; "
                                    "CPython's leg is tracemalloc, in the "
                                    "kit's STATE"))
        return True

    def across(node, pulls=200):
        audiocore.reset_buffer(node)
        loudest = 0
        for _ in range(20):
            _result, data = audiocore.get_buffer(node)
            block = int16(data)
            if block:
                top = peak(block)
                if top > loudest:
                    loudest = top
        gc.collect()
        before = gc.mem_alloc()
        for _ in range(pulls):
            audiocore.get_buffer(node)
        return gc.mem_alloc() - before, loudest

    pcm = sine(rate, rate, 1000.0, 20000)
    control, _quiet = across(source_of(pcm, rate))
    effect, _source = build(rate, pcm, ceiling_db=-12.0)
    measured, loudest = across(effect.output)
    effect.deinit()
    return report("ALLOC 200 blocks of output",
                  measured == control and loudest > 0,
                  "%d bytes through the class, %d through the bare source "
                  "(%+d), render peak %d LSB"
                  % (measured, control, measured - control, loudest))


def main():
    print("Limiter Tier 1 invariants - %s" % sys.implementation.name)
    print("=" * 72)
    failures = 0
    for rate in RATES:
        print()
        print("%d Hz" % rate)
        for check in (wire, tail, level, gain_is_honest, click_latency,
                      state, capabilities, mono, rate_honest, allocation):
            if not check(rate):
                failures += 1
    print()
    print("%d failing invariant%s" % (failures, "" if failures == 1 else "s"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
