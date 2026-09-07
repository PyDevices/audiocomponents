"""Station A bench for `HighPass` -- the runs the dossier's decisions rest on.

Every number in `docs/effects/HighPass.md` section 8 and appendix A15 comes
from this file. It measures *nodes*, not the class: at Station A the class
does not exist yet, and the point of the bench is to choose the nodes it
will be built from.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/highpass_bench.py <run>

Runs: `dc` (the held-DC comparison the tier decision rests on), `corner`
(|H(f0)| = Q, both slopes), `span` (the closed form at three rates, 10 Hz to
20 kHz), `skirt` (+12 and +24 dB/oct), `trim` (the make-up shelf), `tail`
(burst to exact zero), `latency` (a click through the cascade), `grid` (the
0-127 log grid's step size). `all` runs every one.

CPython only, with numpy: this is analysis, not a render (kit spec section
1).
"""

import math
import sys
from array import array

import numpy as np

import audiocore
import audiobiquad
import audiofilters
import synthio

RATE = 48000
FLAT_Q = 1.0 / math.sqrt(2.0)
BUTTERWORTH_LOW = 0.5411961001461969
BUTTERWORTH_HIGH = 1.3065629648763766


# -- sources and rendering -------------------------------------------------

def raw(values, rate=RATE, channels=2):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def sine_array(hz, frames, level, rate=RATE, channels=2):
    out = array("h", bytes(2 * frames * channels))
    for frame in range(frames):
        value = int(round(level * math.sin(2.0 * math.pi * hz * frame / rate)))
        for channel in range(channels):
            out[frame * channels + channel] = value
    return out


def take(node, frames, channels=2):
    """Exactly `frames` frames off `node`, never one more.

    A probe that pulls past the end of its source measures the source's
    padding, not the node -- which is how the held-DC defect stayed hidden
    (dossier A3).
    """
    want = frames * channels
    chunks = []
    have = 0
    while have < want:
        data = bytes(audiocore.get_buffer(node)[1])
        if not data:
            break
        chunks.append(data)
        have += len(data) // 2
    return np.frombuffer(b"".join(chunks), dtype="<i2")[:want]


def pull(node, blocks, block=2048):
    """At least `blocks * block` frames off `node`, as one interleaved int16
    array. Nodes hand back what their own buffer holds -- `audiobiquad`'s is
    256 frames, `audiofilters.Filter`'s is what it was built with -- so this
    counts frames rather than calls."""
    want = blocks * block * 2
    chunks = []
    have = 0
    while have < want:
        data = bytes(audiocore.get_buffer(node)[1])
        if not data:
            break
        chunks.append(data)
        have += len(data) // 2
    return np.frombuffer(b"".join(chunks), dtype="<i2")


# -- the two candidate sections --------------------------------------------

def float_hp(frequency, q, rate=RATE, channels=2, mix=1.0):
    return audiobiquad.Biquad(mode=audiobiquad.HIGH_PASS,
                              frequency=frequency, Q=q, mix=mix,
                              sample_rate=rate, channel_count=channels)


def ported_hp(frequency, q, rate=RATE, channels=2, mix=1.0):
    node = audiofilters.Filter(
        filter=synthio.Biquad(synthio.FilterMode.HIGH_PASS, frequency, Q=q),
        mix=mix, sample_rate=rate, channel_count=channels,
        bits_per_sample=16, samples_signed=True, buffer_size=2048)
    return node


def chain(nodes, source):
    upstream = source
    for node in nodes:
        node.play(upstream)
        upstream = node
    return upstream


# -- closed form (RBJ, S1) -------------------------------------------------

def rbj_highpass(f0, q, rate):
    w0 = 2.0 * math.pi * f0 / rate
    alpha = math.sin(w0) / (2.0 * q)
    cos = math.cos(w0)
    b0 = (1.0 + cos) / 2.0
    b1 = -(1.0 + cos)
    b2 = (1.0 + cos) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cos
    a2 = 1.0 - alpha
    return (b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)


def rbj_db(f0, q, rate, probe):
    b0, b1, b2, a1, a2 = rbj_highpass(f0, q, rate)
    z = np.exp(-2j * math.pi * probe / rate)
    h = (b0 + b1 * z + b2 * z * z) / (1.0 + a1 * z + a2 * z * z)
    return 20.0 * math.log10(abs(h))


# -- tone measurement ------------------------------------------------------

def tone_db(build, probe_hz, level, rate=RATE, cycles=None, settle_blocks=8):
    """Gain at `probe_hz`, read off the exact FFT bin of an integer number
    of cycles, so quantization noise elsewhere in the spectrum cannot bias
    it."""
    block = 2048
    if cycles is None:
        cycles = max(16, int(round(probe_hz * 0.25)))
    frames = int(round(cycles * rate / probe_hz))
    total = frames + settle_blocks * block + block
    values = sine_array(probe_hz, total, level, rate)
    node = build(raw(values, rate))
    data = pull(node, (total + block - 1) // block, block)
    left = data[0::2].astype(np.float64)
    skip = settle_blocks * block
    segment = left[skip:skip + frames]
    reference = np.asarray(values, dtype=np.float64)[0::2][skip:skip + frames]
    bin_index = cycles
    wet = np.fft.rfft(segment)[bin_index]
    dry = np.fft.rfft(reference)[bin_index]
    return 20.0 * math.log10(abs(wet) / abs(dry))


# -- runs ------------------------------------------------------------------

def run_dc():
    """A3's probe, on both candidate sections.

    0.09 s of tone then 3.0 s of digital silence, and **every pull strictly
    inside the source**: when a `Filter`'s source is exhausted
    (`audiofilters/Filter.c:202-223`) it memsets its output to zero without
    running the biquads at all, so a probe that runs two blocks long reads
    exact zero from a filter that is still holding DC. That correction is
    this measurement's planted fault -- `--overrun` runs it long on purpose
    and the residual disappears.
    """
    overrun = "--overrun" in sys.argv
    print("== held DC after silence: ported synthio.Biquad vs audiobiquad ==")
    print("   0.09 s of 440 Hz at 12000, then 3.0 s of zeros; 287 of the 289")
    print("   available 512-frame blocks pulled%s"
          % (" -- OVERRUN, 320 blocks, the planted fault" if overrun else ""))
    tone_frames = int(0.09 * RATE)
    silence_frames = int(3.0 * RATE)
    values = sine_array(440.0, tone_frames, 12000)
    values.extend(array("h", bytes(2 * silence_frames * 2)))
    frame_block = 512
    blocks = 320 if overrun else 287
    frames = blocks * frame_block
    print("%-28s %10s %10s %12s" % ("setting", "ported", "float",
                                    "float zero@"))
    for f0, q in ((10.0, FLAT_Q), (20.0, FLAT_Q), (30.0, FLAT_Q),
                  (60.0, FLAT_Q), (100.0, FLAT_Q), (300.0, FLAT_Q),
                  (1000.0, FLAT_Q), (2000.0, FLAT_Q), (20000.0, FLAT_Q),
                  (30.0, 4.0), (30.0, 16.0), (100.0, 16.0)):
        row = []
        for build in (ported_hp, float_hp):
            node = build(f0, q)
            node.play(raw(array("h", values)))
            data = take(node, frames)
            row.append(int(np.max(np.abs(data[-frame_block * 2:]))))
        node = float_hp(f0, q)
        node.play(raw(array("h", values)))
        data = take(node, frames)
        left = data[0::2]
        nonzero = np.nonzero(left)[0]
        zero_at = (str(int(nonzero[-1]) // frame_block + 1) if len(nonzero)
                   else "0")
        print("f0=%-8g Q=%-8g%12d %10d %12s"
              % (f0, q, row[0], row[1], zero_at))


def run_corner():
    """|H(f0)| = Q, at both slopes, on audiobiquad."""
    print("== |H(f0)| against 20*log10(Q), audiobiquad, 48 kHz ==")
    print("%-8s %-10s %12s %12s %12s" % ("Q", "20logQ", "12 dB/oct",
                                         "24 dB/oct", "worst dev"))
    for q in (0.5, FLAT_Q, 1.0, 2.0, 4.0, 8.0, 16.0):
        want = 20.0 * math.log10(q)
        level = int(min(12000, 20000 / max(1.0, q)))
        f0 = 1000.0
        one = tone_db(lambda s, f=f0, qq=q: chain([float_hp(f, qq)], s),
                      f0, level)

        def steep(s, f=f0, qq=q):
            return chain([float_hp(f, BUTTERWORTH_LOW),
                          float_hp(f, BUTTERWORTH_HIGH * qq / FLAT_Q)], s)

        two = tone_db(steep, f0, level)
        print("%-8g %-10.3f %12.3f %12.3f %12.3f"
              % (q, want, one, two, max(abs(one - want), abs(two - want))))


def run_span():
    """The rendered response against S1's closed form at the running rate."""
    print("== rendered vs closed form, audiobiquad, three rates ==")
    print("%-8s %-8s %-10s %10s %10s %10s"
          % ("rate", "f0", "probe", "measured", "closed", "dev"))
    worst = 0.0
    for rate in (48000, 44100, 22050):
        for f0 in (10.0, 20.0, 30.0, 100.0, 1000.0, 8000.0, 20000.0):
            if f0 > rate * 0.45:
                continue
            for ratio in (0.25, 1.0, 4.0):
                probe = f0 * ratio
                if probe > rate * 0.45 or probe < 5.0:
                    continue
                level = 20000
                got = tone_db(
                    lambda s, f=f0, r=rate: chain([float_hp(f, FLAT_Q, r)], s),
                    probe, level, rate=rate)
                want = rbj_db(f0, FLAT_Q, rate, probe)
                worst = max(worst, abs(got - want))
                print("%-8d %-8g %-10g %10.3f %10.3f %10.3f"
                      % (rate, f0, probe, got, want, got - want))
    print("worst deviation %.4f dB" % worst)


def run_skirt():
    """+12 dB/oct at one section, +24 at two."""
    print("== skirt below f0, audiobiquad, 48 kHz, Q 0.707 ==")
    print("%-8s %-10s %12s %12s %12s"
          % ("f0", "slope", "|H(f0/4)|", "fit dB/oct", "at Nyq*0.96"))
    for f0 in (20.0, 160.0, 640.0, 1280.0, 3200.0):
        for name, nodes in (
                ("12", lambda f=f0: [float_hp(f, FLAT_Q)]),
                ("24", lambda f=f0: [float_hp(f, BUTTERWORTH_LOW),
                                     float_hp(f, BUTTERWORTH_HIGH)])):
            points = []
            for ratio in (0.125, 0.177, 0.25):
                probe = f0 * ratio
                got = tone_db(lambda s, n=nodes: chain(n(), s), probe, 24000)
                points.append((math.log(probe, 2.0), got))
            xs = np.array([p[0] for p in points])
            ys = np.array([p[1] for p in points])
            slope = np.polyfit(xs, ys, 1)[0]
            quarter = [y for x, y in points][-1]
            top = tone_db(lambda s, n=nodes: chain(n(), s), 23000.0, 24000)
            print("%-8g %-10s %12.3f %12.3f %12.3f"
                  % (f0, name, quarter, slope, top))


def run_trim():
    """One HIGH_SHELF at 5 Hz as the class's make-up gain."""
    print("== trim: audiobiquad HIGH_SHELF at 5 Hz, flatness 50 Hz-15 kHz ==")
    print("%-8s %-8s %10s %10s %10s"
          % ("rate", "dB", "50 Hz", "1 kHz", "15 kHz"))
    for rate in (48000, 44100, 22050):
        for db in (-12.0, -6.0, 6.0, 12.0):
            row = []
            for probe in (50.0, 1000.0, 15000.0):
                if probe > rate * 0.45:
                    row.append(float("nan"))
                    continue
                level = int(20000 / max(1.0, 10.0 ** (db / 20.0)))
                got = tone_db(
                    lambda s, d=db, r=rate: chain([
                        audiobiquad.Biquad(mode=audiobiquad.HIGH_SHELF,
                                           frequency=5.0, Q=FLAT_Q,
                                           gain_db=d, sample_rate=r,
                                           channel_count=2)], s),
                    probe, level, rate=rate)
                row.append(got - db)
            print("%-8d %-8g %10.4f %10.4f %10.4f"
                  % (rate, db, row[0], row[1], row[2]))


def run_tail():
    """Burst then silence: the block at which the output is exactly zero."""
    print("== tail to exact zero, audiobiquad, 48 kHz ==")
    print("   full-scale burst, then silence; first all-zero block and the")
    print("   sample index of the last non-zero frame")
    block = 2048
    lead = block
    burst = 2048
    silence = 48000 * 12
    print("%-40s %10s %14s" % ("setting", "zero block", "tail samples"))
    worst = 0
    for f0, q, slope, trim in ((10.0, 16.0, 24, 12.0), (10.0, 16.0, 24, 0.0),
                               (10.0, 16.0, 12, 12.0),
                               (20.0, 16.0, 24, 12.0),
                               (30.0, 16.0, 24, 12.0),
                               (100.0, 16.0, 24, 12.0),
                               (1000.0, 16.0, 24, 12.0),
                               (10.0, FLAT_Q, 12, 0.0),
                               (20000.0, 0.5, 12, 0.0)):
        values = array("h", bytes(2 * lead * 2))
        values.extend(sine_array(f0 if f0 > 40 else 200.0, burst, 32000))
        values.extend(array("h", bytes(2 * silence * 2)))
        if slope == 12:
            nodes = [float_hp(f0, q)]
        else:
            nodes = [float_hp(f0, BUTTERWORTH_LOW),
                     float_hp(f0, BUTTERWORTH_HIGH * q / FLAT_Q)]
        nodes.append(audiobiquad.Biquad(mode=audiobiquad.HIGH_SHELF,
                                        frequency=5.0, Q=FLAT_Q,
                                        gain_db=trim,
                                        mix=1.0 if trim else 0.0,
                                        sample_rate=RATE, channel_count=2))
        chain(nodes, raw(values))
        data = pull(nodes[-1], (lead + burst + silence) // block, block)
        nonzero = np.nonzero(data)[0]
        end = int(nonzero[-1]) // 2 if len(nonzero) else 0
        after = end - (lead + burst)
        worst = max(worst, after)
        zero_block = end // block + 1
        print("f0=%-7g Q=%-6g slope=%-3d trim=%-5g%10d %14d"
              % (f0, q, slope, trim, zero_block, after))
    print("worst tail after the source goes silent: %d samples "
          "(%.3f s at 48 kHz)" % (worst, worst / 48000.0))


def run_latency():
    """A click in, a click out: the cascade reads no sample it has not been
    given."""
    print("== latency: click at frame 50, 48 kHz and 44.1 kHz ==")
    for rate in (48000, 44100):
        for slope, nodes in (
                (12, lambda r=rate: [float_hp(100.0, FLAT_Q, r)]),
                (24, lambda r=rate: [float_hp(100.0, BUTTERWORTH_LOW, r),
                                     float_hp(100.0, BUTTERWORTH_HIGH, r),
                                     audiobiquad.Biquad(
                                         mode=audiobiquad.HIGH_SHELF,
                                         frequency=5.0, Q=FLAT_Q,
                                         gain_db=6.0, sample_rate=r,
                                         channel_count=2)])):
            values = array("h", bytes(2 * 4096 * 2))
            values[50 * 2] = 20000
            values[50 * 2 + 1] = 20000
            built = nodes()
            chain(built, raw(values, rate))
            data = pull(built[-1], 2)
            left = data[0::2]
            first = int(np.nonzero(left)[0][0])
            print("rate %d slope %2d dB/oct: first non-zero output frame %d "
                  "(input at 50), peak %d"
                  % (rate, slope, first, int(np.max(np.abs(left)))))


def run_grid():
    """What one step of the 0-127 macro grid is worth on the two candidate
    Frequency spans."""
    print("== the Frequency macro's log grid ==")
    for lo, hi in ((10.0, 2000.0), (10.0, 20000.0), (20.0, 20000.0)):
        octaves = math.log(hi / lo, 2.0)
        cents = 1200.0 * octaves / 127.0
        below = 127.0 * math.log(200.0 / lo, 2.0) / octaves
        print("%6g Hz .. %6g Hz: %.2f octaves, %.1f cents per step, "
              "%.0f of 127 steps below 200 Hz"
              % (lo, hi, octaves, cents, below))


RUNS = {
    "dc": run_dc, "corner": run_corner, "span": run_span, "skirt": run_skirt,
    "trim": run_trim, "tail": run_tail, "latency": run_latency,
    "grid": run_grid,
}


def main(argv):
    names = [name for name in argv[1:] if not name.startswith("--")] or \
        ["all"]
    if names == ["all"]:
        names = list(RUNS)
    for name in names:
        RUNS[name]()
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
