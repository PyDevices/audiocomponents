"""The Tier 1 rows of `HighPass`'s evidence pack, on any of the three
interpreters.

    PYTHONPATH=lib .venv/bin/python  tools/phase2_probes/highpass_tier1_portable.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython  <this>
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \\
        -X heapsize=256M  <this>

`tools/phase2_probes/highpass_evidence.py` measures the same invariants with
the kit, under CPython with numpy. This file exists because three of those
rows are *class behaviour*, not audio: `reset()`, `deinit()` and
`capabilities` are not settled by two interpreters rendering identical bytes,
so claiming them for MicroPython and CircuitPython off the digest table would
be claiming something the digests do not say. Numpy-free, argparse-free and
`wave`-free, in `tools/render_effect.py`'s shape, so one file runs on all
three.

Every row prints `pass` or `FAIL` with its number. Exit status is the number
of failures.
"""

import math
import sys
from array import array

import audiocore
import audioeffects

RATES = (48000, 44100, 22050)


def interpreter():
    version = getattr(sys, "implementation", None)
    name = getattr(version, "name", "cpython")
    if name == "cpython":
        return "cpython"
    if "circuitpython" in str(getattr(sys, "version", "")).lower():
        return "circuitpython"
    return name


def silence(frames, channels):
    return array("h", bytes(2 * frames * channels))


def ramp(frames, channels):
    out = array("h", bytes(2 * frames * channels))
    for frame in range(frames):
        value = (frame * 64) % 65536 - 32768
        for channel in range(channels):
            out[frame * channels + channel] = value
    return out


def dc_then_nothing(frames, channels, held, level=16000):
    out = array("h", bytes(2 * frames * channels))
    for frame in range(held):
        for channel in range(channels):
            out[frame * channels + channel] = level
    return out


def source(values, rate, channels):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def samples(data):
    """`array('h')` over little-endian PCM, on every interpreter.
    MicroPython has no `memoryview.cast`; CircuitPython and CPython do.
    `tools/render_effect.py:268` carries the same helper for the same
    reason."""
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


def take(node, frames, channels):
    """Exactly `frames` frames, never one more: a pull past the end of the
    source measures the source's padding, not the class."""
    want = frames * channels
    out = array("h")
    while len(out) < want:
        data = bytes(audiocore.get_buffer(node)[1])
        if not len(data):
            break
        out.extend(samples(data))
    return out[:want]


def peak(values):
    loudest = 0
    for value in values:
        if value < 0:
            value = -value
        if value > loudest:
            loudest = value
    return loudest


def row(name, ok, detail):
    print("  %-26s %-5s %s" % (name, "pass" if ok else "FAIL", detail))
    return 0 if ok else 1


def check(rate, channels):
    print("\n== %d Hz, %d channel(s) ==" % (rate, channels))
    failures = 0
    frames = 8192

    # WIRE - mix 0, with a trim and the steep slope asked for, is the source.
    values = ramp(frames, channels)
    effect = audioeffects.create("HighPass", source(values, rate, channels),
                                 rate, frequency=300.0, mix=0.0,
                                 trim_db=9.0, slope=24)
    rendered = take(effect.output, frames, channels)
    reference = take(source(values, rate, channels), frames, channels)
    differing = sum(1 for a, b in zip(rendered, reference) if a != b)
    failures += row("WIRE mix 0", differing == 0,
                    "%d of %d samples differ" % (differing, len(reference)))

    # TAIL - a held DC offset removed inside the source, settling to exact
    # zero. This is the class's T1.
    held = rate // 2
    total = rate * 2
    values = dc_then_nothing(total, channels, held)
    effect = audioeffects.create("HighPass", source(values, rate, channels),
                                 rate, frequency=30.0)
    rendered = take(effect.output, total, channels)
    settled = rendered[-(rate // 4) * channels:]
    failures += row("TAIL exact zero", peak(settled) == 0,
                    "%d LSB in the last %d frames" % (peak(settled),
                                                      rate // 4))

    # LEVEL - a 1 kHz tone through a 10 Hz corner comes back at unity.
    seconds = 0.25
    count = int(rate * seconds)
    values = array("h", bytes(2 * count * channels))
    for frame in range(count):
        value = int(8000 * math.sin(2.0 * math.pi * 1000.0 * frame / rate))
        for channel in range(channels):
            values[frame * channels + channel] = value
    effect = audioeffects.create("HighPass", source(values, rate, channels),
                                 rate, frequency=10.0)
    wet = take(effect.output, count, channels)
    skip = count // 4 * channels
    wet_energy = sum(v * v for v in wet[skip:])
    dry_energy = sum(v * v for v in values[skip:])
    ratio_db = 10.0 * math.log10(float(wet_energy) / float(dry_energy))
    failures += row("LEVEL unity", abs(ratio_db) <= 0.05,
                    "wet:dry %+.4f dB" % ratio_db)

    # CLICK - reported latency against the measured onset.
    values = silence(frames, channels)
    for channel in range(channels):
        values[50 * channels + channel] = 20000
    effect = audioeffects.create("HighPass", source(values, rate, channels),
                                 rate, frequency=300.0)
    rendered = take(effect.output, frames, channels)
    first = None
    for index in range(0, len(rendered), channels):
        if rendered[index]:
            first = index // channels
            break
    failures += row("CLICK latency 0",
                    first == 50 and effect.latency_samples == 0,
                    "reported %d, first output frame %s (input at 50)"
                    % (effect.latency_samples, first))

    # STATE - reset, the borrowed source, deinit, capabilities. The probe
    # is led with silence: `RawSample` hands its buffer back from the
    # beginning, so a burst at frame 0 replays after `reset()` and reads
    # exactly like a section that was never cleared.
    total = rate
    values = array("h", bytes(2 * 4096 * channels))
    for frame in range(4096):
        value = int(28000 * math.sin(2.0 * math.pi * 200.0 * frame / rate))
        for channel in range(channels):
            values.append(value)
    values.extend(array("h", bytes(2 * (total - 8192) * channels)))
    borrowed = source(values, rate, channels)
    effect = audioeffects.create("HighPass", borrowed, rate, frequency=20.0,
                                 q=16.0, slope=24)
    take(effect.output, 8192, channels)
    primed = peak(take(effect.output, 2048, channels))
    effect.reset()
    after = peak(take(effect.output, 2048, channels))
    failures += row("STATE reset", primed > 0 and after == 0,
                    "primed %d LSB, after reset %d LSB (the source replays "
                    "its silent lead)" % (primed, after))
    take(effect.output, 4096, channels)
    resumed = peak(take(effect.output, 4096, channels))
    failures += row("STATE source untouched", resumed > 0,
                    "%d LSB once the source reaches its burst again"
                    % resumed)
    nodes = list(effect._nodes)
    effect.deinit()
    effect.deinit()
    live = [node for node in nodes if not getattr(node, "_deinited", True)]
    failures += row("STATE deinit", not live and len(nodes) == 3,
                    "%d nodes enumerated, %d live afterwards"
                    % (len(nodes), len(live)))

    effect = audioeffects.create("HighPass", source(ramp(2048, channels),
                                                    rate, channels), rate)
    failures += row("STATE capabilities", effect.capabilities == (),
                    "%r; the class never reads self._transport()"
                    % (effect.capabilities,))

    # RATE - the span's top clamps below Nyquist instead of refusing.
    effect = audioeffects.create("HighPass", source(ramp(2048, channels),
                                                    rate, channels), rate,
                                 frequency=20000.0)
    built = effect._pole_one.frequency
    ceiling = min(20000.0, rate * 0.49)
    failures += row("RATE clamp", abs(built - ceiling) < 1.0,
                    "20 kHz asked for -> built at %.1f Hz (ceiling %.1f)"
                    % (built, ceiling))
    return failures


def main():
    print("HighPass Tier 1, portable rows -- interpreter: %s"
          % interpreter())
    failures = 0
    for rate in RATES:
        failures += check(rate, 2)
    failures += check(48000, 1)
    print("\n%d failures" % failures)
    return failures


if __name__ == "__main__":
    sys.exit(main())
