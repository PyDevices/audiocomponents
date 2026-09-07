"""Notch Station A: the runs behind every decision in the dossier's section 8.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/notch_bench.py

CPython, with numpy, because the analysis is (`docs/effects-kit-spec.md`
section 1). Nothing here builds the `Notch` class - Station A runs before
the class exists - so every probe drives the palette nodes directly and the
decisions are made from what the nodes do, not from what a class might.
"""

import math
import os
import sys
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
sys.path.insert(0, ROOT)

import audiobiquad                                          # noqa: E402
import audiofilters                                         # noqa: E402
import numpy as np                                          # noqa: E402
import synthio                                              # noqa: E402
from kit_probes import ArraySource, render                  # noqa: E402

RATE = 48000
CHANNELS = 2


def tone(hz, seconds, rate=RATE, channels=CHANNELS, peak=6000):
    frames = int(rate * seconds)
    data = array("h", bytes(2 * channels * frames))
    for index in range(frames):
        value = int(round(peak * math.sin(2.0 * math.pi * hz * index / rate)))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def burst_then_silence(hz, on_s, total_s, rate=RATE, peak=20000,
                       channels=CHANNELS):
    """The silence is inside the sample: `Filter.c:202-223` memsets the
    output without running the biquads when its source is exhausted, so a
    probe that lets the source end reads exact zero for every build,
    including the dirty ones (the seed's A3)."""
    frames = int(rate * total_s)
    on = int(rate * on_s)
    data = array("h", bytes(2 * channels * frames))
    for index in range(on):
        value = int(round(peak * math.sin(2.0 * math.pi * hz * index / rate)))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data, on


def pull(node, frames, rate=RATE, channels=CHANNELS):
    return render(node, frames, rate=rate,
                  channels=channels).data[:, 0].astype(np.int64)


def rms_db(x, reference):
    a = math.sqrt(float(np.mean(np.square(x.astype(np.float64)))))
    b = math.sqrt(float(np.mean(np.square(reference.astype(np.float64)))))
    if a <= 0.0:
        return -240.0
    return 20.0 * math.log10(a / b)


def gain_db(build, hz, seconds=0.35, rate=RATE, skip=0.15):
    data = tone(hz, seconds, rate)
    frames = int(rate * seconds)
    dry = pull(ArraySource(data, rate=rate, channels=CHANNELS), frames,
               rate=rate)
    node = build(ArraySource(data, rate=rate, channels=CHANNELS))
    wet = pull(node, frames, rate=rate)
    cut = int(rate * skip)
    return rms_db(wet[cut:], dry[cut:])


def biquad(mode, hz, q, rate=RATE, mix=1.0, gain=0.0, channels=CHANNELS):
    return audiobiquad.Biquad(mode=mode, frequency=hz, Q=q, gain_db=gain,
                              mix=mix, sample_rate=rate,
                              channel_count=channels)


def chain(source, nodes):
    upstream = source
    for node in nodes:
        node.play(upstream)
        upstream = node
    return upstream


def closed_form_notch(hz, f0, q, rate=RATE):
    """RBJ's notch, S1, evaluated at the running rate."""
    w0 = 2.0 * math.pi * f0 / rate
    alpha = math.sin(w0) / (2.0 * q)
    cw = math.cos(w0)
    b = (1.0, -2.0 * cw, 1.0)
    a = (1.0 + alpha, -2.0 * cw, 1.0 - alpha)
    z = complex(math.cos(-2.0 * math.pi * hz / rate),
                math.sin(-2.0 * math.pi * hz / rate))
    num = b[0] + b[1] * z + b[2] * z * z
    den = a[0] + a[1] * z + a[2] * z * z
    value = abs(num / den)
    return -240.0 if value <= 0.0 else 20.0 * math.log10(value)


def edges(f0, q):
    """S3/S1: the -3 dB points, difference exactly f0/q."""
    root = math.sqrt(1.0 + 1.0 / (4.0 * q * q))
    return f0 * (root - 1.0 / (2.0 * q)), f0 * (root + 1.0 / (2.0 * q))


# -- D1  the tier: which biquad reaches exact zero --------------------------

def d1_tail_residual():
    print("\n== D1  held DC after silence, the seed's A3 probe ==")
    print("   0.09 s of 440 Hz at 12 000, then 3.0 s of zeros; 287 of the")
    print("   289 available blocks pulled, so the source never runs out.")
    data, _ = burst_then_silence(440.0, 0.09, 3.09, peak=12000)
    frames = 287 * 256
    rows = []
    for label, f0, q in (("60 Hz  q=8  (mains hum)", 60.0, 8.0),
                         ("50 Hz  q=8", 50.0, 8.0),
                         ("120 Hz q=8  (2f0 of 60)", 120.0, 8.0),
                         ("1 kHz  q=0.707 (default)", 1000.0, 0.707),
                         ("20 Hz  q=32 (span corner)", 20.0, 32.0)):
        ported = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.NOTCH, f0, Q=q),
            mix=1.0, sample_rate=RATE, channel_count=CHANNELS,
            bits_per_sample=16, samples_signed=True, buffer_size=2048)
        ported.play(ArraySource(data))
        stock = pull(ported, frames)
        own = biquad(audiobiquad.NOTCH, f0, q)
        own.play(ArraySource(data))
        f32 = pull(own, frames)
        rows.append((label, int(stock[-1]), int(f32[-1]),
                     int(np.max(np.abs(stock[-4096:]))),
                     int(np.max(np.abs(f32[-4096:])))))
    print("   %-26s %10s %10s %10s %10s"
          % ("setting", "synthio", "audiobiq", "|y| synth", "|y| f32"))
    for row in rows:
        print("   %-26s %10d %10d %10d %10d" % row)


# -- D2  the harmonic section's width law -----------------------------------

def d2_harmonic_width():
    print("\n== D2  the harmonic notch's width: share Q, or scale it? ==")
    print("   -3 dB width in Hz of a notch at 2f0, measured against the")
    print("   fundamental's own width. S3: width = f/Q.")
    for f0, q in ((60.0, 12.0), (50.0, 12.0), (1000.0, 2.0)):
        low, high = edges(f0, q)
        base = high - low
        for law, q2 in (("share Q", q), ("scale Q by 2", 2.0 * q)):
            lo2, hi2 = edges(2.0 * f0, q2)
            measured = []
            for hz in (lo2, hi2):
                got = gain_db(lambda s, h=2.0 * f0, qq=q2:
                              chain(s, [biquad(audiobiquad.NOTCH, h, qq)]),
                              hz)
                measured.append(got)
            print("   f0=%-7.1f Q=%-5.1f  %-13s  width %8.2f Hz "
                  "(fundamental %8.2f)  edges measured %7.3f / %7.3f dB"
                  % (f0, q, law, hi2 - lo2, base, measured[0], measured[1]))


# -- D3  the trim shelf ------------------------------------------------------

def d3_trim_shelf():
    print("\n== D3  the make-up trim: one HIGH_SHELF at 5 Hz ==")
    print("   deviation from the requested gain, dB, at each probe")
    for rate in (48000, 44100, 22050):
        for db in (-12.0, -6.0, 6.0, 12.0):
            worst, where = 0.0, 0.0
            for hz in (20.0, 50.0, 100.0, 1000.0, 5000.0, 10000.0):
                if hz >= rate * 0.45:
                    continue
                got = gain_db(lambda s, d=db, r=rate:
                              chain(s, [biquad(audiobiquad.HIGH_SHELF, 5.0,
                                               0.7071067811865476, rate=r,
                                               gain=d)]),
                              hz, rate=rate)
                if abs(got - db) > abs(worst):
                    worst, where = got - db, hz
            print("   %6d Hz  trim %+6.1f dB   worst deviation %+7.3f dB "
                  "at %8.1f Hz" % (rate, db, worst, where))


# -- D4  the (0, 0.01] snap --------------------------------------------------

def d4_mix_threshold():
    print("\n== D4  is the seed's A9 (0, 0.01] mix snap still needed? ==")
    print("   peak |wet - dry| over a 1 kHz tone at f0, per mix value")
    data = tone(1000.0, 0.25, peak=20000)
    frames = int(RATE * 0.25)
    dry = pull(ArraySource(data), frames)
    for mix in (0.0, 0.005, 0.01, 0.02, 0.5, 1.0):
        own = biquad(audiobiquad.NOTCH, 1000.0, 2.0, mix=mix)
        own.play(ArraySource(data))
        f32 = pull(own, frames)
        ported = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.NOTCH, 1000.0, Q=2.0),
            mix=mix, sample_rate=RATE, channel_count=CHANNELS,
            bits_per_sample=16, samples_signed=True, buffer_size=2048)
        ported.play(ArraySource(data))
        stock = pull(ported, frames)
        print("   mix %-6.3f   audiobiquad %6d      audiofilters %6d"
              % (mix, int(np.max(np.abs(f32 - dry))),
                 int(np.max(np.abs(stock - dry)))))


# -- D5  the frequency span's top -------------------------------------------

def d5_span_top():
    print("\n== D5  the Frequency span's top, and what 2f0 does at it ==")
    for rate in (48000, 44100, 22050):
        print("   %6d Hz: 0.4*Fs = %8.1f Hz, _hz() ceiling 0.49*Fs = "
              "%8.1f Hz" % (rate, rate * 0.4, rate * 0.49))
    print("   unity outside the band, notch f0=1 kHz Q=0.707, at 0.48*Fs:")
    for rate in (48000, 44100, 22050):
        hz = rate * 0.48
        got = gain_db(lambda s, r=rate:
                      chain(s, [biquad(audiobiquad.NOTCH, 1000.0, 0.707,
                                       rate=r)]), hz, rate=rate)
        print("      %6d Hz  probe %8.1f Hz  %+7.3f dB  (closed form "
              "%+7.3f)" % (rate, hz, got,
                           closed_form_notch(hz, 1000.0, 0.707, rate)))


# -- D6  the tail ceiling ----------------------------------------------------

def d6_tail_ceiling():
    print("\n== D6  tail to exact zero: the worst corner of the span ==")
    print("   full-scale burst, then silence inside the source; the frame")
    print("   after which every later sample is exactly zero")
    seconds = 40.0
    data, on = burst_then_silence(60.0, 0.2, seconds, peak=32767)
    frames = int(RATE * seconds)
    for label, sections in (
            ("20 Hz  Q 32, one section", ((20.0, 32.0),)),
            ("20 Hz  Q 32 + 40 Hz Q 60", ((20.0, 32.0), (40.0, 60.0))),
            ("50 Hz  Q 12 + 100 Hz Q 24", ((50.0, 12.0), (100.0, 24.0))),
            ("1 kHz  Q 0.707 (patch 0)", ((1000.0, 0.707),))):
        nodes = [biquad(audiobiquad.NOTCH, hz, q) for hz, q in sections]
        nodes.append(biquad(audiobiquad.HIGH_SHELF, 5.0, 0.7071067811865476,
                            mix=0.0))
        node = chain(ArraySource(data), nodes)
        out = pull(node, frames)
        nonzero = np.nonzero(out)[0]
        last = int(nonzero[-1]) if len(nonzero) else -1
        print("   %-28s last non-zero frame %8d, %8d after the source "
              "went silent (%6.2f s)"
              % (label, last, last - on, (last - on) / float(RATE)))


# -- D7  the closed form, so the trait table is checked before code ----------

def d7_closed_form():
    print("\n== D7  T1/T2/T3 against S1's closed form, palette vs formula ==")
    for f0, q in ((1000.0, 2.0), (60.0, 12.0), (8000.0, 30.0)):
        low, high = edges(f0, q)
        for label, hz in (("f0 exactly", f0),
                          ("f0 * 1.0005", f0 * 1.0005),
                          ("lower -3 dB", low),
                          ("upper -3 dB", high),
                          ("0.48 * Fs", RATE * 0.48),
                          ("DC-ish 10 Hz", 10.0)):
            got = gain_db(lambda s, h=f0, qq=q:
                          chain(s, [biquad(audiobiquad.NOTCH, h, qq)]), hz)
            ideal = closed_form_notch(hz, f0, q)
            print("   f0=%-7.1f Q=%-5.1f %-13s probe %9.2f Hz  "
                  "measured %9.3f dB  ideal %9.3f dB  dev %+7.3f"
                  % (f0, q, label, hz, got, ideal,
                     got - ideal if ideal > -200 else 0.0))




# -- D8  the tail with the trim in circuit, and T2 at the span's corners ----

def d8_tail_with_trim():
    print("\n== D8  tail to exact zero with the trim section active ==")
    seconds = 40.0
    data, on = burst_then_silence(60.0, 0.2, seconds, peak=32767)
    frames = int(RATE * seconds)
    for label, sections, trim in (
            ("20 Hz Q32 + 40 Hz Q60, trim +12", ((20.0, 32.0), (40.0, 60.0)),
             12.0),
            ("20 Hz Q32 + 40 Hz Q60, trim -12", ((20.0, 32.0), (40.0, 60.0)),
             -12.0),
            ("trim +12 alone (5 Hz shelf)", (), 12.0)):
        nodes = [biquad(audiobiquad.NOTCH, hz, q) for hz, q in sections]
        nodes.append(biquad(audiobiquad.HIGH_SHELF, 5.0,
                            0.7071067811865476, mix=1.0, gain=trim))
        node = chain(ArraySource(data), nodes)
        out = pull(node, frames)
        nonzero = np.nonzero(out)[0]
        last = int(nonzero[-1]) if len(nonzero) else -1
        print("   %-34s last non-zero frame %8d, %8d after silence "
              "(%6.2f s)" % (label, last, last - on,
                             (last - on) / float(RATE)))


def d9_span_corners():
    print("\n== D9  T2's unity at 0.48*Fs, at the top of the Frequency span ==")
    print("   closed form only (S1), so the span can be frozen before code")
    for rate in (48000, 44100, 22050):
        top = min(16000.0, rate * 0.4)
        for q in (0.5, 0.707, 2.0, 8.0, 32.0):
            probe = rate * 0.48
            print("   %6d Hz  f0=%8.1f Q=%-5.1f  at 0.48*Fs %9.1f Hz -> "
                  "%+8.4f dB   at 10 Hz -> %+8.4f dB"
                  % (rate, top, q, probe,
                     closed_form_notch(probe, top, q, rate),
                     closed_form_notch(10.0, top, q, rate)))


def d10_settled_on_centre():
    print("\n== D10  T1 on-centre, with the transient actually settled ==")
    print("   commensurate probes; 4.0 s of tone, the last 0.5 s read")
    for f0, q in ((60.0, 12.0), (50.0, 12.0), (1000.0, 2.0), (1000.0, 32.0),
                  (1000.0, 0.5), (8000.0, 30.0)):
        seconds = 4.0
        data = tone(f0, seconds, peak=6000)
        frames = int(RATE * seconds)
        node = chain(ArraySource(data), [biquad(audiobiquad.NOTCH, f0, q)])
        out = pull(node, frames)
        settled = out[-int(RATE * 0.5):]
        print("   f0=%-8.1f Q=%-5.1f  samples/cycle %8.2f   peak |y| in the "
              "last 0.5 s: %6d" % (f0, q, RATE / f0,
                                   int(np.max(np.abs(settled)))))


# -- D11  the on-centre floor law, both kernels, against the coefficients ---

def _response(node, f0, rate=RATE):
    """H(f0), complex, from the node's own float coefficients - the shipped
    values, not the algebra. `audiobiquad.Biquad.coefficients` reads the
    block slots without advancing them."""
    b0, b1, b2, a1, a2 = node.coefficients
    w = 2.0 * math.pi * f0 / rate
    z = complex(math.cos(-w), math.sin(-w))
    return (b0 + b1 * z + b2 * z * z) / (1.0 + a1 * z + a2 * z * z)


def _predicted(node, f0, rate=RATE):
    return abs(_response(node, f0, rate))


def _ported_notch(f0, q, rate=RATE, channels=CHANNELS):
    return audiofilters.Filter(
        filter=synthio.Biquad(synthio.FilterMode.NOTCH, f0, Q=q), mix=1.0,
        sample_rate=rate, channel_count=channels, bits_per_sample=16,
        samples_signed=True, buffer_size=2048)


def d11_on_centre_floor(level=6000):
    print("\n== D11  the on-centre floor, both kernels vs the coefficients ==")
    print("   commensurate probes, level %d, 48 kHz, peak |y| over the last"
          % level)
    print("   1.0 s of a 6.0 s render; -75.56 dB is one LSB, the floor")
    print("%-8s %-6s %10s %10s %10s %10s %12s" % (
        "f0", "Q", "own peak", "own dB", "stock pk", "stock dB", "predicted"))
    for f0 in (20.0, 50.0, 60.0, 120.0, 250.0, 500.0, 1000.0, 4000.0,
               8000.0):
        for q in (0.707, 2.0, 12.0, 32.0):
            seconds = 6.0
            data = tone(f0, seconds, peak=level)
            frames = int(RATE * seconds)
            own = biquad(audiobiquad.NOTCH, f0, q)
            own.play(ArraySource(data))
            a = pull(own, frames)[-RATE:]
            ported = _ported_notch(f0, q)
            ported.play(ArraySource(data))
            b = pull(ported, frames)[-RATE:]
            pa, pb = int(np.max(np.abs(a))), int(np.max(np.abs(b)))
            pred = _predicted(biquad(audiobiquad.NOTCH, f0, q), f0)
            print("%-8.1f %-6.3f %10d %10s %10d %10s %12s" % (
                f0, q, pa,
                "%.2f" % (20 * math.log10(pa / level)) if pa else "-inf", pb,
                "%.2f" % (20 * math.log10(pb / level)) if pb else "-inf",
                "%.2f" % (20 * math.log10(pred)) if pred > 0 else "-inf"))


def d12_floor_is_not_a_transient(level=6000):
    print("\n== D12  the floor is steady state, not an unfinished tail ==")
    for f0, q, seconds in ((60.0, 12.0, 16.0), (50.0, 12.0, 16.0),
                           (60.0, 32.0, 30.0), (20.0, 32.0, 40.0)):
        data = tone(f0, seconds, peak=level)
        node = chain(ArraySource(data), [biquad(audiobiquad.NOTCH, f0, q)])
        out = pull(node, int(RATE * seconds))
        marks = []
        for at in (1.0, 2.0, 4.0, 8.0, seconds - 0.5):
            begin = int(RATE * at)
            end = begin + int(RATE * 0.5)
            if end <= len(out):
                marks.append("%4.1fs:%5d"
                             % (at, int(np.max(np.abs(out[begin:end])))))
        print("   f0=%-7.1f Q=%-5.1f  %s" % (f0, q, "  ".join(marks)))


def d13_the_node_ask(level=6000):
    print("\n== D13  the node ask: |1 - H_BP(f0)| against |H_NOTCH(f0)| ==")
    for f0, q in ((20.0, 32.0), (60.0, 12.0), (60.0, 32.0), (1000.0, 2.0)):
        band = biquad(audiobiquad.BAND_PASS, f0, q)
        b0, _, b2, _, _ = band.coefficients
        # The complex residual, not |1 - |H||: the ask is about subtracting
        # the band-pass from the signal, so its phase error counts too.
        gap = abs(1.0 - _response(band, f0))
        deep = _predicted(biquad(audiobiquad.NOTCH, f0, q), f0)
        print("   f0=%-7.1f Q=%-5.1f  |1 - H_BP(f0)| = %.3e (%7.2f dB)   "
              "|H_NOTCH(f0)| = %.3e (%7.2f dB)   b2 == -b0: %s"
              % (f0, q, gap, 20 * math.log10(gap) if gap else -999.0,
                 deep, 20 * math.log10(deep) if deep else -999.0, b2 == -b0))
    print("   control - the ported kernel is really notching, not idle:")
    for f0, q in ((60.0, 12.0), (20.0, 32.0)):
        for probe in (f0, f0 * 10.0, 1000.0):
            seconds = 3.0
            data = tone(probe, seconds, peak=level)
            frames = int(RATE * seconds)
            ported = _ported_notch(f0, q)
            ported.play(ArraySource(data))
            wet = pull(ported, frames)[-RATE:]
            dry = pull(ArraySource(data), frames)[-RATE:]
            print("      notch f0=%-7.1f Q=%-5.1f probe %8.1f Hz -> %8.2f dB"
                  % (f0, q, probe, rms_db(wet, dry)))


# -- D14  T2's unity at the top of the span, closed form --------------------

def d14_span_against_t2():
    print("\n== D14  where T2's 0.1 dB unity at 0.48*Fs actually holds ==")
    for rate in (48000, 44100, 22050):
        probe = rate * 0.48
        for q in (0.5, 0.707):
            low, high = 0.05 * rate, 0.48 * rate
            for _ in range(80):
                middle = 0.5 * (low + high)
                if abs(closed_form_notch(probe, middle, q, rate)) <= 0.1:
                    low = middle
                else:
                    high = middle
            print("   %6d Hz  Q=%-6.3f  f0_max = %9.1f Hz = %.4f * Fs"
                  % (rate, q, low, low / rate))
    print("   and what a fixed ceiling gives at 0.48*Fs, Q 0.5:")
    for fraction in (0.28, 0.30, 0.33, 0.40):
        row = []
        for rate in (48000, 22050):
            row.append("%6d Hz: %+7.4f dB (f0 %8.1f)"
                       % (rate, closed_form_notch(rate * 0.48,
                                                  rate * fraction, 0.5, rate),
                          rate * fraction))
        print("      %.2f*Fs   %s" % (fraction, "  |  ".join(row)))
    print("   DC (10 Hz) at the same corners, Q 0.5:")
    for fraction in (0.28, 0.33, 0.40):
        for rate in (48000, 22050):
            print("      %.2f*Fs %6d Hz -> %+9.5f dB"
                  % (fraction, rate,
                     closed_form_notch(10.0, rate * fraction, 0.5, rate)))


if __name__ == "__main__":
    d1_tail_residual()
    d2_harmonic_width()
    d3_trim_shelf()
    d4_mix_threshold()
    d5_span_top()
    d6_tail_ceiling()
    d7_closed_form()
    d8_tail_with_trim()
    d9_span_corners()
    d10_settled_on_centre()
    d11_on_centre_floor()
    d12_floor_is_not_a_transient()
    d13_the_node_ask()
    d14_span_against_t2()
