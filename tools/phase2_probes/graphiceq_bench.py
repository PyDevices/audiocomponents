"""GraphicEQ Station A bench: the six probes the dossier's App. S records.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/graphiceq_bench.py

Runs against the palette, not against the class -- these are the measurements
that chose the composition, and they had to exist before there was a class to
measure. `docs/effects/GraphicEQ.md` App. S quotes what this prints.

**The trap this file exists to not fall into again.** The first draft fed an
`audiocore.RawSample` straight into the filter under test. A `RawSample` hands
its buffer back from the beginning when it runs out, so every "burst then
silence" probe was reading the burst *playing again* -- a ten-section chain
read -19321 where it should have read 0, and the reading looked like
instability. Every source here goes through an `audiofilters.Filter(filter=
None, mix=1)` adapter played `loop=False`, which is `tools/render_effect.py`'s
own re-blocking seam: the probe is delivered exactly once and the source then
supplies silence.
"""

import array
import math

import audiobiquad
import audiocore
import audiofilters
import synthio

RATE = 48000
CHANNELS = 2
CENTRES = [31.25 * (2 ** n) for n in range(10)]
SKIRT = 10.0 ** (1.0 / 20.0)
ANCHOR_A = 10.0 ** (12.0 / 40.0)


def fnv1a(data):
    digest = 0x811C9DC5
    for byte in data:
        digest = ((digest ^ byte) * 0x01000193) & 0xFFFFFFFF
    return digest


def band_q(gain_db, anchor=2.0):
    amplitude = 10.0 ** (abs(gain_db) / 40.0)
    numerator = amplitude ** 2 - (SKIRT ** 2) / (amplitude ** 2)
    denominator = ANCHOR_A ** 2 - (SKIRT ** 2) / (ANCHOR_A ** 2)
    if numerator <= 0.0:
        return 0.05
    return min(60.0, max(0.05, anchor * math.sqrt(numerator / denominator)))


def adapter(data, rate=RATE, block=256):
    """The probe, delivered exactly once, then silence."""
    raw = audiocore.RawSample(data, sample_rate=rate,
                              channel_count=CHANNELS)
    node = audiofilters.Filter(filter=None, mix=1.0, sample_rate=rate,
                               channel_count=CHANNELS, bits_per_sample=16,
                               samples_signed=True,
                               buffer_size=block * CHANNELS * 2)
    node.play(raw, loop=False)
    return node


def tone(hz, frames, peak, rate=RATE):
    data = array.array("h", bytes(2 * CHANNELS * frames))
    for index in range(frames):
        value = int(peak * math.sin(2.0 * math.pi * hz * index / rate))
        for channel in range(CHANNELS):
            data[index * CHANNELS + channel] = value
    return data


def noise(frames, peak=8000, seed=12345):
    data = array.array("h", bytes(2 * CHANNELS * frames))
    state = seed
    for index in range(frames):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        value = int(peak * (2.0 * (state / 0x7FFFFFFF) - 1.0))
        for channel in range(CHANNELS):
            data[index * CHANNELS + channel] = value
    return data


def render(node, frames):
    audiocore.reset_buffer(node)
    produced, blob = 0, bytearray()
    while produced < frames:
        result, buffer = audiocore.get_buffer(node, False, 0)
        chunk = bytes(buffer)
        if not chunk:
            break
        blob += chunk
        produced += len(chunk) // (2 * CHANNELS)
        del result
    return bytes(blob)


def f32_chain(source, gains, rate=RATE):
    nodes, previous = [], source
    ceiling = rate * 0.5 * 0.98
    for index, centre in enumerate(CENTRES):
        if gains[index] is None:
            continue
        mode = (audiobiquad.HIGH_SHELF if index == 9
                else audiobiquad.PEAKING_EQ)
        node = audiobiquad.Biquad(mode=mode, frequency=min(centre, ceiling),
                                  Q=band_q(gains[index]),
                                  gain_db=gains[index], sample_rate=rate,
                                  channel_count=CHANNELS)
        node.play(previous)
        nodes.append(node)
        previous = node
    return previous, nodes


def stock_bank(source, gains, blocker=False, rate=RATE):
    sections = [synthio.Biquad(
        synthio.FilterMode.HIGH_SHELF if index == 9
        else synthio.FilterMode.PEAKING_EQ, centre, Q=1.4,
        A=10.0 ** (gains[index] / 40.0))
        for index, centre in enumerate(CENTRES)]
    node = audiofilters.Filter(filter=tuple(sections), mix=1.0,
                               sample_rate=rate, channel_count=CHANNELS,
                               bits_per_sample=16, samples_signed=True,
                               buffer_size=2048)
    node.play(source)
    nodes, out = [node], node
    if blocker:
        high = audiobiquad.Biquad(mode=audiobiquad.HIGH_PASS, frequency=5.0,
                                  Q=0.707, sample_rate=rate,
                                  channel_count=CHANNELS)
        high.play(node)
        nodes.append(high)
        out = high
    return out, nodes


def last_sample(blob):
    values = array.array("h")
    values.frombytes(blob)
    return values[-1] if len(values) else None


def probe_i():
    print("(i) tail after in-sample silence -- 200 Hz burst, 3 s of zeros")
    data = tone(200.0, int(RATE * 0.1), 20000)
    frames = int(RATE * 3.1)
    cases = (("all ten at +6", [6.0] * 10),
             ("31.25 Hz at +6", [6.0] + [0.0] * 9),
             ("all flat", [0.0] * 10))
    for label, build in (("audiobiquad chain", f32_chain),
                         ("stock Filter", stock_bank),
                         ("stock + f32 HP 5 Hz",
                          lambda s, g: stock_bank(s, g, blocker=True))):
        for name, gains in cases:
            out, nodes = build(adapter(data), list(gains))
            print("    %-20s %-16s last sample %d"
                  % (label, name, last_sample(render(out, frames))))
            for node in nodes:
                node.deinit()


def probe_ii():
    print("(ii) ring-down, all ten at +12 dB, 40 Hz burst then silence")
    for rate in (48000, 44100, 22050):
        burst = int(rate * 0.25)
        out, nodes = f32_chain(adapter(tone(40.0, burst, 24000, rate), rate),
                               [12.0] * 10, rate)
        blob = render(out, rate * 4)
        values = array.array("h")
        values.frombytes(blob)
        last = max((i for i in range(len(values)) if values[i]), default=-1)
        tail = last // CHANNELS - burst
        print("    %5d Hz: tail %6d frames (%.1f ms)"
              % (rate, tail, 1000.0 * tail / rate))
        for node in nodes:
            node.deinit()


def probe_iii():
    print("(iii) the f32 high-pass against a held DC")
    # The DC runs a second longer than the render on purpose. Reading the
    # last sample of a render that ends exactly where the DC ends catches
    # the *trailing* edge -- the adapter has begun handing out silence and
    # the high-pass is responding to that step, not to the DC. The first
    # draft of this probe did exactly that and read -7 / -6 / -4 where the
    # answer is zero.
    frames = RATE * 3
    data = array.array("h", bytes(2 * CHANNELS * (frames + RATE)))
    for index in range((frames + RATE) * CHANNELS):
        data[index] = 7
    for hz in (1.0, 5.0, 20.0):
        node = audiobiquad.Biquad(mode=audiobiquad.HIGH_PASS, frequency=hz,
                                  Q=0.707, sample_rate=RATE,
                                  channel_count=CHANNELS)
        node.play(adapter(data))
        print("    %5.1f Hz high-pass on a held +7 LSB: last sample %d"
              % (hz, last_sample(render(node, frames))))
        node.deinit()


def probe_iv():
    print("(iv) is a flat section a wire? one PEAKING_EQ, gain_db 0, mix 1")
    frames = 24000
    data = noise(frames)
    dry = array.array("h")
    dry.frombytes(render(adapter(data), frames))
    for centre in CENTRES:
        node = audiobiquad.Biquad(mode=audiobiquad.PEAKING_EQ,
                                  frequency=centre, Q=1.4, gain_db=0.0,
                                  sample_rate=RATE, channel_count=CHANNELS)
        node.play(adapter(data))
        wet = array.array("h")
        wet.frombytes(render(node, frames))
        span = min(len(dry), len(wet))
        bad = [i for i in range(span) if dry[i] != wet[i]]
        print("    %8.2f Hz: %6d differing, first at %-6s worst %d"
              % (centre, len(bad), bad[0] if bad else "-",
                 max((abs(dry[i] - wet[i]) for i in bad), default=0)))
        node.deinit()
    node = audiobiquad.Biquad(mode=audiobiquad.PEAKING_EQ, frequency=31.25,
                              Q=1.4, gain_db=0.0, mix=0.0, sample_rate=RATE,
                              channel_count=CHANNELS)
    node.play(adapter(data))
    wet = render(node, frames)
    print("    31.25 Hz at mix=0: dry %08x wet %08x  %s"
          % (fnv1a(dry.tobytes()), fnv1a(wet),
             "IDENTICAL" if wet == dry.tobytes() else "DIFFER"))
    node.deinit()


def probe_v():
    print("(v) the Q law against ParametricEQ.md Appendix A, anchor 2.0")
    print("    " + "  ".join("%2.0f dB: %.3f" % (g, band_q(g))
                             for g in (1, 2, 3, 6, 9, 12)))


def probe_vi():
    print("(vi) a subsonic HIGH_SHELF as a broadband gain, gain_db +12")
    frames = 24000
    for corner in (2.0, 5.0, 10.0, 20.0):
        row = []
        for hz in (30.0, 100.0, 1000.0, 10000.0):
            data = tone(hz, frames, 4000)
            dry = render(adapter(data), frames)
            node = audiobiquad.Biquad(mode=audiobiquad.HIGH_SHELF,
                                      frequency=corner, Q=0.707,
                                      gain_db=12.0, sample_rate=RATE,
                                      channel_count=CHANNELS)
            node.play(adapter(data))
            wet = render(node, frames)
            node.deinit()
            row.append("%6.0f Hz %+6.2f" % (hz, _rms_db(wet) - _rms_db(dry)))
        print("    corner %5.1f Hz -> %s" % (corner, "  ".join(row)))


def _rms_db(blob, skip=4800):
    values = array.array("h")
    values.frombytes(blob)
    tail = values[skip * CHANNELS::CHANNELS]
    if not len(tail):
        return -999.0
    power = sum(float(v) * v for v in tail) / len(tail)
    return 10.0 * math.log10(power) if power > 0 else -999.0


if __name__ == "__main__":
    for probe in (probe_i, probe_ii, probe_iii, probe_iv, probe_v, probe_vi):
        probe()
        print()
