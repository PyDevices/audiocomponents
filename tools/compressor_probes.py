"""Station A's palette probes for `Compressor`, as one runnable file.

Every table in the dossier's Appendix J is one case here. They are probes of
the *node*, not of the class: they ran before the class existed, to settle
what `audiodynamics` can and cannot do before the trait table was frozen.
Station C's measurements live in `Compressor-evidence.md` and go through the
kit (`tools/effect_measurements.py`); these do not.

    python tools/compressor_probes.py [case ...]

with no argument it runs every case. Cases: `options`, `wire`, `sidechain`,
`feedback`, `detector`, `program_attack`, `both`.
"""

import array
import math
import sys

import audiocore
import audiodynamics

RATE = 48000


# -- the plumbing ---------------------------------------------------------

def raw(samples, rate=RATE, channels=2):
    """A stereo `RawSample` over `samples`, the same value in both channels."""
    buffer = array.array('h')
    for value in samples:
        clamped = int(max(-32768, min(32767, value)))
        for _ in range(channels):
            buffer.append(clamped)
    return audiocore.RawSample(buffer, sample_rate=rate,
                               channel_count=channels), buffer


def pull(node, frames, channels=2):
    """`frames` frames out of `node`, as an int16 array."""
    out = array.array('h')
    while len(out) < frames * channels:
        result, block = audiocore.get_buffer(node)
        data = bytes(block)
        if not data:
            break
        out.extend(memoryview(data).cast('h'))
        if result == audiocore.GET_BUFFER_ERROR:
            break
    return out[:frames * channels]


def dyn(**options):
    return audiodynamics.Dynamics(audiodynamics.DYN_COMPRESS,
                                  sample_rate=RATE, channel_count=2, **options)


def gain_trace(out, source, channels=2):
    """Gain in dB per frame, output over input; `None` where the input is 0."""
    trace = []
    for index in range(0, len(out), channels):
        drive = source[index]
        if drive == 0:
            trace.append(None)
        else:
            wet = out[index]
            trace.append(20 * math.log10(abs(wet) / abs(drive))
                         if wet else -200.0)
    return trace


def step_trace(attack_ms, ratio, feedback, threshold_db, release_ms=200.0,
               over_db=20.0, lead_s=0.05, tail_s=0.6, **extra):
    """The GR trace after a DC step `over_db` over `threshold_db`."""
    lead = int(RATE * lead_s)
    tail = int(RATE * tail_s)
    quiet = 32768 * 10 ** ((threshold_db - 20.0) / 20.0)
    loud = 32768 * 10 ** ((threshold_db + over_db) / 20.0)
    wave = [quiet] * lead + [loud] * tail
    source, _ = raw(wave)
    node = dyn(threshold_db=threshold_db, ratio=ratio, knee_db=0.0,
               attack_ms=attack_ms, release_ms=release_ms,
               feedback_detector=feedback, **extra)
    node.play(source)
    out = pull(node, lead + tail)
    trace = gain_trace(out, [v for v in wave for _ in (0, 1)])
    return [value for value in trace[lead + 1:] if value is not None]


def _fraction_ms(segment, fraction):
    final = min(segment[-int(RATE * 0.05):])
    base = segment[0]
    target = base + fraction * (final - base)
    for index, value in enumerate(segment):
        if value <= target:
            return index / float(RATE) * 1000.0
    return None


def _absolute_ms(segment, gain_reduction_db):
    for index, value in enumerate(segment):
        if value <= -gain_reduction_db:
            return index / float(RATE) * 1000.0
    return None


# -- the cases ------------------------------------------------------------

def case_options():
    """J.1 - what `set()` accepts on the pin."""
    node = dyn()
    accepted, refused = [], []
    names = ("threshold_db", "ratio", "knee_db", "makeup_db", "attack_ms",
             "release_ms", "sidechain_hz", "lookahead_ms", "true_peak",
             "detector", "rms_ms", "feedback_detector", "sidechain_lp_hz",
             "sidechain_poles", "key_listen", "depth_db", "hold_ms",
             "hysteresis_db", "relative_threshold", "program_attack",
             "transient_dual", "slow_hold_ms",
             "rms_window_ms", "release_stage2_ms")
    for name in names:
        value = "rms" if name == "detector" else 1.0
        try:
            node.set(**{name: value})
            accepted.append(name)
        except TypeError:
            refused.append(name)
    print("accepted (%d of the %d asked for): %s"
          % (len(accepted), len(names), ", ".join(accepted)))
    print("refused: %s" % ", ".join(refused))


def case_wire():
    """J.2 - `ratio=1` is byte-identical to the source, once and twice."""
    frames = 4096
    wave = [20000 * math.sin(2 * math.pi * 440 * i / RATE)
            for i in range(frames)]
    reference = array.array('h', [int(v) for v in wave for _ in (0, 1)])
    settings = dict(threshold_db=-60.0, ratio=1.0, knee_db=0.0,
                    attack_ms=1.0, release_ms=100.0, makeup_db=0.0)

    source, _ = raw(wave)
    one = dyn(**settings)
    one.play(source)
    out = pull(one, frames)
    print("(a)  ratio=1, threshold -60, makeup 0: byte-identical to source ->",
          bytes(out) == bytes(reference[:len(out)]))
    print("     differing samples:",
          sum(1 for i in range(len(out)) if out[i] != reference[i]))

    source, _ = raw(wave)
    first, second = dyn(**settings), dyn(**settings)
    first.play(source)
    second.play(first)
    out = pull(second, frames)
    print("(a2) two in series at ratio=1:         byte-identical ->",
          bytes(out) == bytes(reference[:len(out)]))


def case_sidechain():
    """J.2 - the side-chain memory is not observable after `reset()`."""
    warm_frames = int(RATE * 0.3)
    read_frames = int(RATE * 0.05)
    high = [12000 * math.sin(2 * math.pi * 10000 * i / RATE)
            for i in range(warm_frames)]
    low = [12000 * math.sin(2 * math.pi * 100 * i / RATE)
           for i in range(read_frames)]
    settings = dict(threshold_db=-30.0, ratio=8.0, knee_db=0.0,
                    attack_ms=5.0, release_ms=100.0, sidechain_hz=1000.0)

    def render(warm, do_reset):
        node = dyn(**settings)
        if warm:
            burst, _ = raw(high)
            node.play(burst)
            pull(node, warm_frames)
            if do_reset:
                audiocore.reset_buffer(node)
        tone, _ = raw(low)
        node.play(tone)
        return bytes(pull(node, read_frames)), node

    cold, _ = render(False, False)
    reset_run, node = render(True, True)
    no_reset, _ = render(True, False)
    print("warm + reset() + play  == cold :", reset_run == cold,
          " (%d differing bytes of %d)"
          % (sum(1 for i in range(len(cold)) if cold[i] != reset_run[i]),
             len(cold)))
    print("warm +          play   == cold :", no_reset == cold,
          " (reset() is what clears it)")

    meter = dyn(**settings)
    burst, _ = raw(high)
    meter.play(burst)
    pull(meter, warm_frames)
    print("gain_reduction_db before reset  %.3f" % meter.gain_reduction_db())
    audiocore.reset_buffer(meter)
    print("gain_reduction_db after  reset  %.3f  (the C keeps it on purpose)"
          % meter.gain_reduction_db())


def case_feedback():
    """J.3 - the ordering both ways, and the 2:1 cap."""
    print("matched on settings: 10-90 %% of each build's own span")
    print("  ratio  attack     ff 10-90    fb 10-90   fb>ff?")
    slower = total = 0
    for ratio in (4.0, 8.0, 12.0, 20.0):
        for attack in (0.02, 0.05, 0.2, 0.8, 5.0, 20.0):
            forward = step_trace(attack, ratio, False, -30.0)
            back = step_trace(attack, ratio, True, -30.0)
            one = _fraction_ms(forward, 0.9) - _fraction_ms(forward, 0.1)
            two = _fraction_ms(back, 0.9) - _fraction_ms(back, 0.1)
            total += 1
            good = two > one
            slower += good
            print("  %5.0f  %6.2f ms  %8.4f ms %8.4f ms   %-3s (GR ff %6.2f "
                  "fb %6.2f)" % (ratio, attack, one, two,
                                 "yes" if good else "NO",
                                 min(forward[-2400:]), min(back[-2400:])))
    print("  strictly slower on %d of %d settings\n" % (slower, total))

    print("the 2:1 cap: measured against 20*(1 - 1/(2 - 1/R))")
    for ratio in (4.0, 8.0, 12.0, 20.0):
        back = step_trace(0.2, ratio, True, -30.0)
        predicted = 20.0 * (1.0 - 1.0 / (2.0 - 1.0 / ratio))
        print("  R=%-3.0f measured %6.3f dB   predicted %6.3f dB"
              % (ratio, -min(back[-2400:]), predicted))
    print()

    print("time to a FIXED absolute 6 dB of GR, same threshold and ratio")
    slower = total = 0
    for ratio in (4.0, 8.0, 12.0, 20.0):
        for attack in (0.05, 0.2, 0.8, 5.0, 20.0, 50.0):
            one = _absolute_ms(step_trace(attack, ratio, False, -30.0), 6.0)
            two = _absolute_ms(step_trace(attack, ratio, True, -30.0), 6.0)
            total += 1
            good = one is not None and two is not None and two > one
            slower += good
            print("  %5.0f %6.2f ms  %8.4f  %8.4f    %s"
                  % (ratio, attack, -1 if one is None else one,
                     -1 if two is None else two, "yes" if good else "tie/NO"))
    print("  fb slower on %d of %d (the rest are ties at 0.0 ms, below the "
          "two-sample floor)" % (slower, total))


def case_detector():
    """J.4 - V3's two figures, peak against RMS."""
    hz, amplitude = 200.0, 8000.0
    frames = int(RATE * 1.5)

    def sine(count):
        return [amplitude * math.sin(2 * math.pi * hz * i / RATE)
                for i in range(count)]

    def square(count):
        return [amplitude / math.sqrt(2)
                * (1 if math.sin(2 * math.pi * hz * i / RATE) >= 0 else -1)
                for i in range(count)]

    def pulse(count):
        period = RATE / hz
        shape = []
        for index in range(count):
            phase = (index % period) / period
            shape.append(amplitude if phase < 0.05
                         else (-amplitude if 0.5 <= phase < 0.55 else 0.0))
        return shape

    def steady(wave, options):
        source, _ = raw(wave(frames))
        node = dyn(threshold_db=-30.0, ratio=1000.0, knee_db=0.0,
                   attack_ms=0.5, release_ms=50.0, **options)
        node.play(source)
        pull(node, frames)
        return node.gain_reduction_db()

    print("  detector          sine      square    |sq-sn|     10%-duty"
          "   sine-pulse")
    for label, options in (("peak (default)", {}),
                           ("rms  10 ms", {"detector": "rms"}),
                           ("rms   3 ms", {"detector": "rms", "rms_ms": 3.0}),
                           ("rms  30 ms",
                            {"detector": "rms", "rms_ms": 30.0})):
        one, two = steady(sine, options), steady(square, options)
        three = steady(pulse, options)
        print("  %-14s %8.3f  %8.3f    %7.3f     %8.3f      %7.3f"
              % (label, one, two, abs(two - one), three, abs(one - three)))
    print("  V3 asks                                <= 0.50"
          "                  6.99 +- 1")


def _attack_points(attack_ms, program, detector, rms_ms):
    """Time to 99 % of the full overshoot on 10 / 20 / 30 dB steps."""
    points = []
    for over in (10.0, 20.0, 30.0):
        extra = dict(program_attack=program)
        if detector:
            extra["detector"] = detector
            extra["rms_ms"] = rms_ms
        segment = step_trace(attack_ms, 1000.0, False, -40.0,
                             release_ms=200.0, over_db=over, tail_s=0.5,
                             **extra)
        points.append(_fraction_ms(segment, 0.99))
    return points


def case_program_attack():
    """J.4 - V2 on the peak detector."""
    print("  time to 99 %% of the full overshoot, 10 / 20 / 30 dB over")
    for program in (False, True):
        for attack in (5.0, 12.0, 20.0, 40.0):
            row = _attack_points(attack, program, None, 10.0)
            if None in row:
                continue
            print("  prog=%-5s det=peak atk=%5.1f ms -> %7.3f %7.3f %7.3f"
                  "   t30/t10 %.3f" % (program, attack, row[0], row[1],
                                       row[2], row[2] / row[0]))
    print("  V2 asks (15/5/3 ms +-30%): 10.5-19.5  3.5-6.5  2.1-3.9,"
          "  t30/t10 <= 0.333")


def case_both():
    """J.4 - no RMS window and attack pair holds V2 and V3 at once."""
    print(" rms_ms  atk    t10      t20      t30   | V3a(<=0.5)"
          " V3b(5.99-7.99) | both")
    met = 0
    for rms_ms in (1.0, 2.0, 3.0, 5.0, 8.0, 10.0):
        for attack in (0.5, 1.0, 2.0, 3.0, 5.0, 8.0):
            row = _attack_points(attack, True, "rms", rms_ms)
            if None in row:
                continue
            v2 = (10.5 <= row[0] <= 19.5 and 3.5 <= row[1] <= 6.5
                  and 2.1 <= row[2] <= 3.9 and row[2] <= row[0] / 3.0)
            print(" %5.1f %5.1f %7.3f %8.3f %8.3f  |"
                  % (rms_ms, attack, row[0], row[1], row[2]),
                  "V2" if v2 else "  ")
            met += v2
    print(" settings meeting V2 while the RMS detector is engaged: %d" % met)


CASES = {
    "options": case_options,
    "wire": case_wire,
    "sidechain": case_sidechain,
    "feedback": case_feedback,
    "detector": case_detector,
    "program_attack": case_program_attack,
    "both": case_both,
}


def main(argv):
    wanted = argv[1:] or list(CASES)
    for name in wanted:
        if name not in CASES:
            raise SystemExit("no such case %r; have %s"
                             % (name, ", ".join(sorted(CASES))))
        print("=== %s ===" % name)
        CASES[name]()
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
