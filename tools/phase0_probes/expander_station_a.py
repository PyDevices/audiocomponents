"""Station A bench for the `Expander` rebuild - App. B of `Expander.md`.

Every number in the dossier's App. B is printed by this file and by nothing
else. It drives `audiodynamics.Dynamics` directly, not the class, because its
subject is what the *palette* does: §4's map from a trait to an option, and
the three places a frozen trait statement asks for something the node - or
16-bit audio - cannot give.

    audiocomponents/.venv/bin/python tools/phase0_probes/expander_station_a.py

Kept beside the survey's three refuter probes; not part of the measurement
kit, which measures the class rather than the node.
"""

import array
import math

import audiocore
import audiodynamics

RATE = 48000
CH = 2


def sine(hz, dbfs, seconds=1.0, square=False):
    """A tone at a stated RMS level, identical in both channels."""
    frames = int(RATE * seconds)
    amplitude = 10.0 ** (dbfs / 20.0)
    data = array.array('h', [0] * frames * CH)
    for index in range(frames):
        phase = (index * hz / RATE) % 1.0
        if square:
            value = amplitude * (1.0 if phase < 0.5 else -1.0)
        else:
            value = amplitude * math.sqrt(2.0) * math.sin(2 * math.pi * phase)
        word = int(max(-32768, min(32767, round(value * 32767))))
        data[index * CH] = word
        data[index * CH + 1] = word
    return data


def node(**options):
    return audiodynamics.Dynamics(audiodynamics.DYN_EXPAND, sample_rate=RATE,
                                  channel_count=CH, **options)


def render(source_pcm, frames, mode=audiodynamics.DYN_EXPAND, **options):
    source = audiocore.RawSample(source_pcm, sample_rate=RATE,
                                 channel_count=CH)
    built = audiodynamics.Dynamics(mode, sample_rate=RATE, channel_count=CH,
                                   **options)
    built.play(source)
    out = array.array('h')
    produced = 0
    while produced < frames:
        _, buffer = audiocore.get_buffer(built, False, 0)
        chunk = array.array('h')
        chunk.frombytes(bytes(buffer))
        if not len(chunk):
            break
        out.extend(chunk)
        produced += len(chunk) // CH
    return out


def rms_db(data, start=0.5):
    frames = len(data) // CH
    total = 0.0
    count = 0
    for index in range(int(frames * start), frames):
        value = data[index * CH] / 32768.0
        total += value * value
        count += 1
    if not total:
        return float('-inf')
    return 20 * math.log10(math.sqrt(total / count))


def fit(points):
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    slope = (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
             / sum((x - mx) ** 2 for x in xs))
    residual = max(abs(y - (my + slope * (x - mx))) for x, y in zip(xs, ys))
    return slope, residual


def b1_the_law():
    print("B1  E1, the law - threshold -20 dBFS, RMS detector, depth -90 dB.")
    print("    The span per ratio is bounded by the int16 floor, not by the")
    print("    node: E1's 30 dB clause asks for 30*(ratio-1) dB of output")
    print("    range, which is 210 dB at ratio 8.")
    threshold = -20.0
    for ratio in (1.5, 2.0, 4.0, 8.0):
        span = min(30.0, (80.0 + threshold) / ratio)
        points = []
        for step in range(7):
            level = threshold - 1.0 - step * (span - 1.0) / 6.0
            pcm = sine(1000, level, 0.6)
            out = render(pcm, int(RATE * 0.6), threshold_db=threshold,
                         ratio=ratio, attack_ms=5.0, release_ms=50.0,
                         detector="rms", depth_db=-90.0)
            points.append((rms_db(pcm), rms_db(out)))
        slope, residual = fit(points)
        print("    ratio %-4s span %4.1f dB  slope %.4f (%+.2f%%)  "
              "max residual %.3f dB" % (ratio, span, slope,
                                        100 * (slope - ratio) / ratio,
                                        residual))
    for level in (-15.0, -10.0, -6.0):
        pcm = sine(1000, level, 0.6)
        out = render(pcm, int(RATE * 0.6), threshold_db=threshold, ratio=4.0,
                     attack_ms=5.0, release_ms=50.0, detector="rms",
                     depth_db=-90.0)
        print("    above threshold at %+.0f dBFS: %+0.3f dB"
              % (level, rms_db(out) - rms_db(pcm)))


def b2_the_detector():
    print("B2  E2, the detector - threshold -20 dBFS, ratio 2, attack 5 ms,")
    print("    release 150 ms; sine and square at equal RMS -35 dBFS.")
    for detector in ("peak", "rms"):
        gains = []
        for square in (False, True):
            pcm = sine(1000, -35.0, 1.0, square=square)
            out = render(pcm, RATE, threshold_db=-20.0, ratio=2.0,
                         attack_ms=5.0, release_ms=150.0, detector=detector)
            gains.append(rms_db(out))
        print("    detector=%-4s sine %.2f  square %.2f  gap %.2f dB"
              % (detector, gains[0], gains[1], abs(gains[0] - gains[1])))


def b3_the_key_band():
    print("B3  E3, the key band - 500-2000 Hz, threshold -40 dBFS, ratio 4,")
    print("    depth -60 dB (so the floor is -60), RMS detector.")
    for poles in (1, 2):
        for hz in (250.0, 1000.0, 4000.0):
            row = []
            for level in (-60.0, -40.0, -20.0, 0.0):
                pcm = sine(hz, level, 1.0)
                source = audiocore.RawSample(pcm, sample_rate=RATE,
                                             channel_count=CH)
                built = node(threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                             attack_ms=5.0, release_ms=50.0, detector="rms",
                             sidechain_hz=500.0, sidechain_lp_hz=2000.0,
                             sidechain_poles=poles)
                built.play(source)
                for _ in range(180):
                    audiocore.get_buffer(built, False, 0)
                row.append((level, built.gain_reduction_db()))
            print("    poles=%d  %6.0f Hz  " % (poles, hz)
                  + "  ".join("%+.0f dBFS/%.1f dB" % pair for pair in row))
    print("    rejection, poles=2, a -20 dBFS tone per frequency:")
    for hz in (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0):
        pcm = sine(hz, -20.0, 1.0)
        source = audiocore.RawSample(pcm, sample_rate=RATE, channel_count=CH)
        built = node(threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                     attack_ms=5.0, release_ms=50.0, detector="rms",
                     sidechain_hz=500.0, sidechain_lp_hz=2000.0,
                     sidechain_poles=2)
        built.play(source)
        for _ in range(180):
            audiocore.get_buffer(built, False, 0)
        reduction = built.gain_reduction_db()
        implied = -40.0 + reduction / 3.0 if reduction < 0 else 0.0
        print("      %6.0f Hz  gain %8.2f dB  implied detector %8.2f dBFS"
              % (hz, reduction, implied))


def b4_the_depth():
    print("B4  E4, depth - input -6 dBFS, threshold 30 dB above it (+24 dB),")
    print("    ratio 8, RMS detector; the settled attenuation against the")
    print("    setting.")
    pcm = sine(1000, -6.0, 0.6)
    dry = rms_db(pcm)
    for depth in (0.0, -20.0, -40.0, -60.0, -80.0):
        out = render(pcm, int(RATE * 0.6), threshold_db=24.0, ratio=8.0,
                     attack_ms=5.0, release_ms=50.0, detector="rms",
                     depth_db=depth)
        got = rms_db(out) - dry
        print("    depth %+6.1f dB -> %8.2f dB  (error %+.2f)"
              % (depth, got, got - depth))


def b5_the_one_shot():
    print("B5  E5, the one-shot - a 1 ms full-scale burst then silence, under")
    print("    a 200 ms attack. Gain read once per 256-frame block.")
    frames = int(RATE * 0.5)
    pcm = array.array('h', [0] * frames * CH)
    for index in range(int(RATE * 0.001)):
        word = int(32767 * math.sin(2 * math.pi * 1000 * index / RATE))
        pcm[index * CH] = word
        pcm[index * CH + 1] = word
    for mode, label in ((audiodynamics.DYN_EXPAND, "EXPAND"),
                        (audiodynamics.DYN_GATE, "GATE  ")):
        for hold in (None, 20.0):
            options = dict(threshold_db=-40.0, attack_ms=200.0,
                           release_ms=200.0, depth_db=-80.0)
            if mode == audiodynamics.DYN_EXPAND:
                options["ratio"] = 8.0
                options["detector"] = "rms"
            if hold is not None:
                options["hold_ms"] = hold
            source = audiocore.RawSample(pcm, sample_rate=RATE,
                                         channel_count=CH)
            built = audiodynamics.Dynamics(mode, sample_rate=RATE,
                                           channel_count=CH, **options)
            built.play(source)
            trace = []
            for _ in range(60):
                audiocore.get_buffer(built, False, 0)
                trace.append(built.gain_reduction_db())
            print("    %s %-11s best gain %7.2f dB   first six blocks %s"
                  % (label, "hold_ms=%s" % hold, max(trace),
                     " ".join("%.1f" % value for value in trace[:6])))


def _step(low_db, high_db, ms_low, ms_high):
    n_low = int(RATE * ms_low / 1000.0)
    n_high = int(RATE * ms_high / 1000.0)
    data = array.array('h', [0] * (n_low + n_high) * CH)
    for index in range(n_low + n_high):
        amplitude = 10.0 ** ((low_db if index < n_low else high_db) / 20.0)
        value = amplitude * math.sqrt(2.0) * math.sin(
            2 * math.pi * index * 1000.0 / RATE)
        word = int(max(-32768, min(32767, round(value * 32767))))
        data[index * CH] = word
        data[index * CH + 1] = word
    return data, n_low


def _gain_trace(pcm, out, frames):
    """Gain in dB read at the 1 kHz sine's own peaks - period 48 frames at
    48 kHz, peaks at index % 48 in (12, 36) - so the ratio is never taken
    near a zero crossing."""
    trace = []
    for index in range(frames):
        if index % 48 not in (12, 36):
            continue
        source = pcm[index * CH]
        if abs(source) < 8:
            continue
        gain = out[index * CH] / source
        if gain > 0:
            trace.append((index / RATE * 1000.0, 20 * math.log10(gain)))
    return trace


def _marks(trace, step_ms, begin_db, end_db):
    span = end_db - begin_db
    found = {}
    for fraction in (0.1, 0.632, 0.9):
        for when, gain in trace:
            if when < step_ms:
                continue
            if (gain - begin_db) / span >= fraction:
                found[fraction] = when - step_ms
                break
    return found


def b6_the_times():
    print("B6  E6, the times - a 20 dB level step, threshold -20 dBFS,")
    print("    ratio 2, depth -20 dB, RMS detector. attack_ms and release_ms")
    print("    are one-pole time constants, so 10-90 %% of the gain-in-dB")
    print("    trace is a function of the step size too.")
    for label, settings, low, high, other in (
            ("attack ", (0.01, 1.0, 10.0, 100.0, 1000.0), -30.0, -10.0,
             "release_ms"),
            ("release", (2.0, 10.0, 100.0, 1000.0, 4000.0), -10.0, -30.0,
             "attack_ms")):
        for setting in settings:
            hold = max(600.0, setting * 6)
            pcm, n_low = _step(low, high, 300.0, hold)
            frames = len(pcm) // CH
            options = {"threshold_db": -20.0, "ratio": 2.0,
                       "depth_db": -20.0, "detector": "rms",
                       other: 1.0 if other == "attack_ms" else 10.0}
            options["attack_ms" if label.strip() == "attack"
                    else "release_ms"] = setting
            out = render(pcm, frames, **options)
            trace = _gain_trace(pcm, out, min(frames, len(out) // CH))
            step_ms = n_low / RATE * 1000.0
            before = [g for t, g in trace if t < step_ms]
            after = [g for t, g in trace if t > step_ms + hold * 0.8]
            if not before or not after:
                print("    %s %8.2f ms  no trace" % (label, setting))
                continue
            found = _marks(trace, step_ms, before[-1], after[-1])
            t63 = found.get(0.632)
            width = (None if 0.1 not in found or 0.9 not in found
                     else found[0.9] - found[0.1])
            print("    %s %8.2f ms  t63 %9s ms  10-90 %9s ms  "
                  "10-90/set %5s   (%.1f -> %.1f dB)"
                  % (label, setting,
                     "n/a" if t63 is None else "%.3f" % t63,
                     "n/a" if width is None else "%.3f" % width,
                     "n/a" if not width else "%.2f" % (width / setting),
                     before[-1], after[-1]))


    print("    the fastest attack, with the RMS window taken out of it:")
    for detector in ("rms", "peak"):
        pcm, n_low = _step(-30.0, -10.0, 300.0, 600.0)
        frames = len(pcm) // CH
        out = render(pcm, frames, threshold_db=-20.0, ratio=2.0,
                     depth_db=-20.0, detector=detector, attack_ms=0.01,
                     release_ms=10.0)
        trace = _gain_trace(pcm, out, min(frames, len(out) // CH))
        step_ms = n_low / RATE * 1000.0
        before = [g for t, g in trace if t < step_ms]
        after = [g for t, g in trace if t > step_ms + 480.0]
        found = _marks(trace, step_ms, before[-1], after[-1])
        print("      attack_ms=0.01, detector=%-4s  t63 %.3f ms "
              "(%.1f samples at 48 kHz)"
              % (detector, found[0.632], found[0.632] * RATE / 1000.0))


def b7_latency_and_wire():
    print("B7  latency, the wire states and the tail.")
    frames = 4096
    pcm = array.array('h', [0] * frames * CH)
    pcm[128 * CH] = 32767
    pcm[128 * CH + 1] = 32767
    out = render(pcm, frames, threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                 attack_ms=5.0, release_ms=50.0, detector="rms",
                 sidechain_hz=25.0, sidechain_lp_hz=23520.0,
                 sidechain_poles=2)
    arrival = next((i for i in range(frames) if out[i * CH]), None)
    print("    impulse in at frame 128, out at frame %s" % arrival)
    ramp = array.array('h', [0] * 2048 * CH)
    for index in range(2048):
        word = ((index * 64) % 65536) - 32768
        ramp[index * CH] = word
        ramp[index * CH + 1] = word
    for label, options in (
            ("ratio 1.0", dict(ratio=1.0, depth_db=-80.0)),
            ("depth 0 dB", dict(ratio=8.0, depth_db=0.0))):
        out = render(ramp, 2048, threshold_db=0.0, attack_ms=5.0,
                     release_ms=50.0, detector="rms", sidechain_hz=25.0,
                     sidechain_lp_hz=23520.0, sidechain_poles=2, **options)
        same = all(out[i] == ramp[i] for i in range(2048 * CH))
        worst = max(abs(out[i] - ramp[i]) for i in range(2048 * CH))
        print("    %-11s byte-identical to the source: %-5s (worst %d LSB)"
              % (label, same, worst))
    burst = array.array('h', [0] * 24000 * CH)
    for index in range(9600):
        word = int(16000 * math.sin(2 * math.pi * 220 * index / RATE))
        burst[index * CH] = word
        burst[index * CH + 1] = word
    for listen in (0.0, 1.0):
        out = render(burst, 24000, threshold_db=-40.0, ratio=4.0,
                     depth_db=-60.0, attack_ms=5.0, release_ms=2000.0,
                     detector="rms", sidechain_hz=25.0,
                     sidechain_lp_hz=23520.0, sidechain_poles=2,
                     key_listen=listen)
        after = [i for i in range(9600, min(24000, len(out) // CH))
                 if out[i * CH]]
        last = (after[-1] - 9600) if after else -1
        print("    key_listen=%d: last non-zero frame after the burst ends: "
              "%d" % (int(listen), last))


if __name__ == "__main__":
    for probe in (b1_the_law, b2_the_detector, b3_the_key_band, b4_the_depth,
                  b5_the_one_shot, b6_the_times, b7_latency_and_wire):
        probe()
        print()
