"""HighPass Station C: every number in `docs/effects/HighPass-evidence.md`.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/highpass_evidence.py

CPython only, with numpy, because the analysis is
(`docs/effects-kit-spec.md` section 1: the render is dual-runtime, the
analysis is not). The other two interpreters are reached through
`tools/render_effect.py`, whose digests the pack's section 3 carries -- and
byte-identical renders are what lets a Tier 1 row measured here stand for
all three.

Every Tier 2 trait is followed by a planted fault **of the same kind**: not
a different bug that happens to be red, but the specific thing the trait
denies. The clean run beside it is the control, because a battery with no
control only proves the checker always fails.
"""

import math
import os
import sys
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
sys.path.insert(0, ROOT)

import audiocore                                            # noqa: E402
import audioeffects                                         # noqa: E402
import audiofilters                                         # noqa: E402
import numpy as np                                          # noqa: E402
import synthio                                              # noqa: E402
from audioeffects.rebuilt import highpass                    # noqa: E402
import kit_probes as probes                                  # noqa: E402
from kit_probes import ArraySource, SwitchableSource, render  # noqa: E402
from tools import effect_measurements as kit                 # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
CHANNELS = 2
FLAT_Q = highpass.FLAT_Q
RATES = (48000, 44100, 22050)


def build(data, rate=RATE, channels=CHANNELS, block=256, **options):
    source = ArraySource(data, rate=rate, channels=channels, block=block)
    return source, audioeffects.create("HighPass", source, rate, **options)


def take(effect, frames, rate=RATE, channels=CHANNELS, block=256, label=None):
    return render(effect.output, frames, rate=rate, channels=channels,
                  block=block, label=label, class_name="HighPass",
                  class_version=highpass.HighPass.VERSION,
                  latency_samples=effect.latency_samples)


def dry(data, frames, rate=RATE, channels=CHANNELS, block=256):
    return render(ArraySource(data, rate=rate, channels=channels,
                              block=block),
                  frames, rate=rate, channels=channels, block=block,
                  label="dry")


def line(name, result):
    print("  %-9s %-7s %s" % (name, "green" if result["passed"] else "RED",
                              "; ".join(result["red"]) or ""))
    return result


def tone_gain_db(hz, rate=RATE, channels=CHANNELS, seconds=0.5, dbfs=-14.0,
                 report_peak=False, **options):
    """Steady-state gain at `hz`, read off the exact tone bin of the second
    half of the render. The first half is the settle: a resonant corner
    rings for Q periods, and reading a filter that has not finished ringing
    reads the ring."""
    data = probes.sine(hz, seconds, dbfs, rate=rate, channels=channels)
    frames = int(rate * seconds)
    _, effect = build(data, rate=rate, channels=channels, **options)
    wet = take(effect, frames, rate=rate, channels=channels)
    reference = dry(data, frames, rate=rate, channels=channels)
    start = frames // 2
    w = kit.tone_bin(wet.float[start:, 0], rate, hz)
    d = kit.tone_bin(reference.float[start:, 0], rate, hz)
    gain = 20.0 * math.log10(abs(w) / abs(d))
    if report_peak:
        return gain, int(np.abs(wet.data[start:]).max())
    return gain


def settled_seconds(f0, q, floor=1.0):
    """Long enough that the corner has stopped ringing before the window
    opens: the window is the second half, and a Q-period ring at f0 needs
    about 4 Q periods to be gone."""
    return max(floor, 2.0 * (4.0 * q / f0) + 0.25)


def rbj_db(f0, q, rate, probe):
    """S1's closed form for a HIGH_PASS at the running rate."""
    w0 = 2.0 * math.pi * f0 / rate
    alpha = math.sin(w0) / (2.0 * q)
    cos = math.cos(w0)
    b0, b1, b2 = (1.0 + cos) / 2.0, -(1.0 + cos), (1.0 + cos) / 2.0
    a0, a1, a2 = 1.0 + alpha, -2.0 * cos, 1.0 - alpha
    z = np.exp(-2j * math.pi * probe / rate)
    h = ((b0 + b1 * z + b2 * z * z) / (a0 + a1 * z + a2 * z * z))
    return 20.0 * math.log10(abs(h))


def warped(hz, rate):
    return (rate / math.pi) * math.tan(math.pi * hz / rate)


def unwarped(f_a, rate):
    return (rate / math.pi) * math.atan(math.pi * f_a / rate)


# --------------------------------------------------------------------------
# Tier 1
# --------------------------------------------------------------------------

def tier_one(rate, channels):
    print("\n== Tier 1, %d Hz, %d channel(s) ==" % (rate, channels))
    results = {}

    # WIRE - mix 0 is byte-identical to the source.
    data = probes.ramp_fs(frames=8192, channels=channels)
    _, effect = build(data, rate=rate, channels=channels, frequency=300.0,
                      mix=0.0, trim_db=9.0, slope=24)
    wet = take(effect, 8192, rate=rate, channels=channels)
    results["WIRE"] = line("WIRE", kit.wire(
        wet, dry(data, 8192, rate=rate, channels=channels),
        latency_samples=effect.latency_samples))

    # TAIL - burst then silence, and the dc_step leg that is T1.
    burst, end = probes.burst_silence(total_s=3.0, rate=rate,
                                      channels=channels)
    frames = int(rate * 3.0)
    _, effect = build(burst, rate=rate, channels=channels, frequency=30.0)
    burst_render = take(effect, frames, rate=rate, channels=channels)
    step, removed = probes.dc_step(hold_s=0.5, total_s=3.0, rate=rate,
                                   channels=channels)
    _, effect = build(step, rate=rate, channels=channels, frequency=30.0)
    step_render = take(effect, frames, rate=rate, channels=channels)
    results["TAIL"] = line("TAIL", kit.tail(
        burst_render, burst_end_frame=end,
        declared_tail_samples=highpass.HighPass.TAIL_SAMPLES,
        dc_render=step_render, dc_removed_frame=removed))

    # LEVEL - a 1 kHz tone through a 10 Hz corner is the dry path.
    seconds = 0.5
    tone = probes.sine(1000.0, seconds, -14.0, rate=rate, channels=channels)
    count = int(rate * seconds)
    _, effect = build(tone, rate=rate, channels=channels, frequency=10.0)
    results["LEVEL"] = line("LEVEL", kit.level(
        take(effect, count, rate=rate, channels=channels),
        dry(tone, count, rate=rate, channels=channels),
        skip_frames=count // 4))

    # CLICK - the integer onset, which is what latency_samples declares; a
    # minimum-phase filter's group delay is a property of the class, not its
    # processing latency (kit CLICK docstring).
    click = probes.click_stereo(frames=8192, offset=256, channels=channels)
    _, effect = build(click, rate=rate, channels=channels, frequency=300.0)
    results["CLICK"] = line("CLICK", kit.click(
        take(effect, 8192, rate=rate, channels=channels),
        dry(click, 8192, rate=rate, channels=channels),
        effect.latency_samples, subsample=False))

    # STATE - reset, deinit, capabilities, allocation.
    noise = probes.noise_det(frames=8192 * 8, channels=channels)
    inner = ArraySource(noise, rate=rate, channels=channels)
    holder = SwitchableSource(inner)
    silent = ArraySource(probes.silence(8192 * 8, channels=channels),
                         rate=rate, channels=channels)
    effect = audioeffects.create("HighPass", holder, rate, frequency=30.0,
                                 q=8.0, slope=24)

    def pull(blocks):
        return render(effect.output, blocks * 256, rate=rate,
                      channels=channels, block=256)

    results["STATE"] = line("STATE", kit.state(
        effect, pull=pull, swap=holder.swap, probe_source=inner,
        silent_source=silent, blocks=32))

    # RESPONSE - the corner is where it was asked for, at this rate; and
    # rate honesty: a Hz span above the rate's ceiling clamps rather than
    # refusing, and the filter still filters there.
    corner = 1000.0
    grid = [corner * ratio for ratio in (0.25, 0.5, 0.71, 0.84, 1.0, 1.19,
                                         1.41, 2.0, 4.0)]
    wet_by_hz, dry_by_hz = {}, {}
    for hz in grid:
        seconds = 0.25
        tone = probes.sine(hz, seconds, -6.0, rate=rate, channels=channels)
        count = int(rate * seconds)
        _, effect = build(tone, rate=rate, channels=channels,
                          frequency=corner)
        wet_by_hz[hz] = take(effect, count, rate=rate, channels=channels)
        dry_by_hz[hz] = dry(tone, count, rate=rate, channels=channels)
    results["RESPONSE"] = line("RESPONSE", kit.response(
        wet_by_hz, dry_by_hz, reference_hz=grid[-1],
        expected={"corner_hz": (corner, 3.0),
                  "passband_db": (0.0, 0.10)}))

    # The clamp itself: 20 kHz asked for at every rate.
    ceiling = min(20000.0, rate * 0.49)
    _, effect = build(probes.silence(256, channels=channels), rate=rate,
                      channels=channels, frequency=20000.0)
    built = effect._pole_one.frequency
    at_corner = tone_gain_db(built, rate=rate, channels=channels, dbfs=-6.0,
                             frequency=20000.0)
    clamped = abs(built - ceiling) < 1.0 and abs(at_corner + 3.01) < 0.10
    print("  %-9s %-7s 20 kHz asked for at %d Hz -> built at %.1f Hz "
          "(ceiling %.1f), which reads %+.3f dB at its own corner"
          % ("CLAMP", "green" if clamped else "RED", rate, built, ceiling,
             at_corner))
    results["CLAMP"] = {"passed": clamped, "red": [],
                        "values": {"built_hz": built, "ceiling_hz": ceiling,
                                   "corner_db": at_corner}}
    return results


def tier_one_faults():
    print("\n== Tier 1 planted faults, 48 kHz ==")
    data = probes.ramp_fs(frames=8192)
    control_source = dry(data, 8192)

    # WIRE: 1/256 of the cascade leaking into a bypass.
    _, effect = build(data, frequency=300.0, mix=0.0)
    clean = kit.wire(take(effect, 8192), control_source)
    _, effect = build(data, frequency=300.0, mix=0.0)
    effect._pole_one.mix = 1.0 / 256.0
    faulted = kit.wire(take(effect, 8192), control_source)
    print("  WIRE   clean %s / faulted %s  (%s)"
          % ("green" if clean["passed"] else "RED",
             "RED" if not faulted["passed"] else "green",
             faulted["red"][0] if faulted["red"] else "-"))

    # TAIL: the ported biquad this class moved off, same probe.
    step, removed = probes.dc_step(hold_s=0.5, total_s=3.0)
    frames = 48000 * 3
    _, effect = build(step, frequency=10.0)
    clean = kit.tail(take(effect, frames), burst_end_frame=removed,
                     dc_render=take(*(lambda: (build(step,
                                                     frequency=10.0)[1],
                                               frames))()),
                     dc_removed_frame=removed)
    ported = audiofilters.Filter(
        filter=synthio.Biquad(synthio.FilterMode.HIGH_PASS, 10.0, Q=FLAT_Q),
        mix=1.0, sample_rate=RATE, channel_count=CHANNELS,
        bits_per_sample=16, samples_signed=True, buffer_size=2048)
    ported.play(ArraySource(step, block=256))
    faulted_render = render(ported, frames, rate=RATE, channels=CHANNELS,
                            block=256)
    faulted = kit.tail(faulted_render, burst_end_frame=removed,
                       dc_render=faulted_render, dc_removed_frame=removed)
    print("  TAIL   clean %s / faulted %s  (%s)"
          % ("green" if clean["passed"] else "RED",
             "RED" if not faulted["passed"] else "green",
             faulted["red"][0] if faulted["red"] else "-"))

    # CLICK: latency_samples reported 256 short, the DSP untouched.
    click = probes.click_stereo(frames=8192, offset=256)
    control = dry(click, 8192)
    _, effect = build(click, frequency=300.0)
    wet = take(effect, 8192)
    clean = kit.click(wet, control, 0, subsample=False)
    faulted = kit.click(wet, control, 256, subsample=False)
    print("  CLICK  clean %s / faulted %s  (%s); audio digest unchanged "
          "%08x -> %08x"
          % ("green" if clean["passed"] else "RED",
             "RED" if not faulted["passed"] else "green",
             faulted["red"][0] if faulted["red"] else "-",
             wet.digest, wet.digest))

    # STATE: a section left uncleared by reset().
    noise = probes.noise_det(frames=8192 * 8)
    inner = ArraySource(noise, rate=RATE, channels=CHANNELS)
    holder = SwitchableSource(inner)
    silent = ArraySource(probes.silence(8192 * 8), rate=RATE,
                         channels=CHANNELS)
    effect = audioeffects.create("HighPass", holder, RATE, frequency=20.0,
                                 q=16.0, slope=24)
    original = type(effect).reset

    def only_the_tail(self):
        audiocore.reset_buffer(self._trim)
        self.program_change(0)

    def pull(blocks):
        return render(effect.output, blocks * 256, rate=RATE,
                      channels=CHANNELS, block=256)

    type(effect).reset = only_the_tail
    try:
        faulted = kit.state(effect, pull=pull, swap=holder.swap,
                            probe_source=inner, silent_source=silent,
                            blocks=32)
    finally:
        type(effect).reset = original
    print("  STATE  faulted %s  (%s)"
          % ("RED" if not faulted["passed"] else "green",
             faulted["red"][0] if faulted["red"] else "-"))


# --------------------------------------------------------------------------
# Tier 2
# --------------------------------------------------------------------------

def trait_t1():
    print("\n== T1  exact zero at DC ==")
    step, removed = probes.dc_step(hold_s=0.5, total_s=3.0)
    frames = 48000 * 3
    for hz, slope in ((10.0, 12), (10.0, 24), (30.0, 12), (100.0, 24),
                      (2000.0, 12)):
        _, effect = build(step, frequency=hz, slope=slope)
        rendered = take(effect, frames)
        result = kit.tail(rendered, burst_end_frame=removed,
                          dc_render=rendered, dc_removed_frame=removed)
        print("  f0=%-8g slope=%-3d %-6s residual %d LSB, dc after removal "
              "%.3f LSB, tail %s samples"
              % (hz, slope, "green" if result["passed"] else "RED",
                 result["values"]["residual_lsb"],
                 result["values"]["dc_after_removed_lsb"],
                 result["values"]["tail_samples"]))


def trait_t2():
    print("\n== T2  |H(f0)| = Q, both slopes ==")
    print("  %-8s %-10s %10s %10s" % ("Q", "20logQ", "12 dB/oct",
                                      "24 dB/oct"))
    for q in (0.5, FLAT_Q, 1.0, 2.0, 4.0, 8.0):
        want = 20.0 * math.log10(q)
        dbfs = -14.0 - max(0.0, want)
        row = []
        for slope in (12, 24):
            row.append(tone_gain_db(1000.0, dbfs=dbfs, frequency=1000.0,
                                    q=q, slope=slope))
        flag = "green" if max(abs(v - want) for v in row) <= 0.05 else "RED"
        print("  %-8g %-10.3f %10.3f %10.3f  %s"
              % (q, want, row[0], row[1], flag))

    print("  planted fault - the resonance on both Butterworth sections:")
    data = probes.sine(1000.0, 0.5, -20.0)
    _, effect = build(data, frequency=1000.0, q=2.0, slope=24)
    effect._pole_one.Q = highpass.BUTTERWORTH_LOW * 2.0 / FLAT_Q
    wet = take(effect, 24000)
    reference = dry(data, 24000)
    got = 20.0 * math.log10(
        abs(kit.tone_bin(wet.float[12000:, 0], RATE, 1000.0))
        / abs(kit.tone_bin(reference.float[12000:, 0], RATE, 1000.0)))
    print("    Q 2 at 24 dB/oct reads %+.3f dB against 20log10(2) = +6.021 "
          "-> %s" % (got, "RED" if abs(got - 6.021) > 0.05 else "green"))


def trait_t3():
    print("\n== T3  the skirt, both slopes, and unity at Nyquist ==")
    print("  %-8s %-6s %10s %12s %12s"
          % ("f0", "slope", "|H(f0/4)|", "dB/oct", "23 kHz"))
    for f0 in (20.0, 160.0, 640.0, 1280.0, 3200.0):
        for slope in (12, 24):
            eighth = tone_gain_db(f0 / 8.0, dbfs=-6.0, frequency=f0,
                                  slope=slope, seconds=1.0)
            quarter = tone_gain_db(f0 / 4.0, dbfs=-6.0, frequency=f0,
                                   slope=slope, seconds=1.0)
            top = tone_gain_db(23000.0, dbfs=-14.0, frequency=f0,
                               slope=slope)
            want, tol = ((-24.10, 0.30) if slope == 12 else (-48.20, 0.60))
            flag = ("green" if abs(quarter - want) <= tol
                    and abs(top) <= 0.10 else "RED")
            print("  %-8g %-6d %10.3f %12.3f %12.3f  %s"
                  % (f0, slope, quarter, quarter - eighth, top, flag))
    print("  planted fault - the second pole left as a wire at 24 dB/oct:")
    data = probes.sine(160.0, 1.0, -6.0)
    _, effect = build(data, frequency=640.0, slope=24)
    effect._pole_two.mix = 0.0
    wet, reference = take(effect, 48000), dry(data, 48000)
    got = 20.0 * math.log10(
        abs(kit.tone_bin(wet.float[24000:, 0], RATE, 160.0))
        / abs(kit.tone_bin(reference.float[24000:, 0], RATE, 160.0)))
    print("    reads %.3f dB where the trait says -48.20 +/- 0.60 -> %s"
          % (got, "RED" if abs(got + 48.20) > 0.60 else "green"))


def trait_t4():
    print("\n== T4  one curve on the warped axis ==")
    ratios = (0.125, 0.5, 1.0, 2.0, 4.0)
    reference = None
    for f0 in (31.5, 125.0, 500.0, 1000.0, 2000.0, 4000.0):
        curve = []
        for ratio in ratios:
            probe = unwarped(warped(f0, RATE) * ratio, RATE)
            curve.append(tone_gain_db(probe, dbfs=-6.0, frequency=f0,
                                      seconds=1.0))
        if reference is None:
            reference = curve
            spread = 0.0
        else:
            spread = max(abs(a - b) for a, b in zip(reference, curve))
        print("  f0=%-8g %s  worst |dev| from the 31.5 Hz curve %.4f dB"
              % (f0, "green" if spread <= 0.05 else "RED", spread))
    print("  planted fault - the built corner 15 % off the asked-for one:")
    curve = []
    for ratio in ratios:
        probe = unwarped(warped(1000.0, RATE) * ratio, RATE)
        data = probes.sine(probe, 1.0, -6.0)
        _, effect = build(data, frequency=1000.0)
        effect._pole_one.frequency = 1150.0
        wet, ref = take(effect, 48000), dry(data, 48000)
        curve.append(20.0 * math.log10(
            abs(kit.tone_bin(wet.float[24000:, 0], RATE, probe))
            / abs(kit.tone_bin(ref.float[24000:, 0], RATE, probe))))
    spread = max(abs(a - b) for a, b in zip(reference, curve))
    print("    worst |dev| %.4f dB against a 0.05 dB bar -> %s"
          % (spread, "RED" if spread > 0.05 else "green"))


def _burst_source(f0, level, on_frames, total_frames):
    """A tone burst at `f0`, then silence, inside one source."""
    data = array("h", bytes(2 * CHANNELS * total_frames))
    for frame in range(on_frames):
        value = int(round(level * math.sin(2.0 * math.pi * f0 * frame
                                           / RATE)))
        for channel in range(CHANNELS):
            data[frame * CHANNELS + channel] = value
    return data


def ring_periods(f0, q, slope=12, tweak=None):
    """T5: how many periods of f0 the ring takes to fall to e^-pi (-27.3 dB)
    of the amplitude it had when the drive stopped.

    **A click is the wrong stimulus for a high-pass, and this is the run
    that says so.** A high-pass passes the click itself: the impulse
    response's first sample is the click arriving unfiltered, and it is
    20-30 dB above the ring behind it, so an envelope peak taken over the
    whole response is the strike and e^-pi of it is reached in a tenth of a
    period at every Q. Measured that way, Q 2 and Q 16 both read 0.01 Q. The
    dossier's T5 measurement cell says "impulse", and for this class that
    cell is wrong; a tone burst at f0, released, excites the same resonance
    and leaves nothing but its decay to read.

    The drive level is scaled by Q so the steady state stays inside full
    scale: at Q 16 the corner stands 24 dB up, and a burst at -6 dBFS would
    clip and flatten the very envelope this measures.
    """
    on_frames = int(RATE * 0.5)
    total_frames = int(RATE * 2.0)
    level = 20000.0 / max(1.0, q)
    _, effect = build(_burst_source(f0, level, on_frames, total_frames),
                      frequency=f0, q=q, slope=slope)
    if tweak is not None:
        tweak(effect)
    data = take(effect, total_frames).float[:, 0]
    envelope = np.abs(kit.analytic(data))
    # From the release, and never into the last fifth: `analytic()` is an
    # FFT Hilbert transform and the burst at the front of the buffer wraps
    # round to lift the envelope at the back.
    ring = envelope[on_frames:int(total_frames * 0.8)]
    if not ring.size:
        return None
    target = float(ring[0]) * math.exp(-math.pi)
    above = np.nonzero(ring >= target)[0]
    if not above.size:
        return None
    return float(above[-1]) / (RATE / f0)


def trait_t5():
    print("\n== T5  Q is the ringing (decay time is Q periods) ==")
    print("     tone burst at f0, released; periods to e^-pi of the")
    print("     amplitude at release. See ring_periods() for why not a click.")
    for q in (2.0, 4.0, 8.0, 16.0):
        periods = ring_periods(200.0, q)
        ratio = None if periods is None else periods / q
        flag = ("unmeasured" if ratio is None
                else "green" if 0.8 <= ratio <= 1.25 else "RED")
        print("  Q=%-5g  e^-pi reached after %6.2f periods = %.2f Q  %s"
              % (q, periods if periods else float("nan"),
                 ratio if ratio else float("nan"), flag))
    print("  planted fault - the built Q a quarter of the asked-for one:")

    def quarter(effect):
        effect._pole_one.Q = 2.0

    periods = ring_periods(200.0, 8.0, tweak=quarter)
    ratio = periods / 8.0 if periods else None
    print("    e^-pi after %.2f periods = %.2f Q -> %s"
          % (periods if periods else float("nan"),
             ratio if ratio else float("nan"),
             "RED" if ratio is None or not 0.8 <= ratio <= 1.25 else "green"))


def trait_t6():
    print("\n== T6  rate-honest against the closed form at the running "
          "rate ==")
    worst = 0.0
    for rate in RATES:
        for f0 in (10.0, 30.0, 100.0, 1000.0, 8000.0):
            if f0 > rate * 0.45:
                continue
            for ratio in (0.25, 1.0, 4.0):
                probe = f0 * ratio
                if probe > rate * 0.45 or probe < 5.0:
                    continue
                got = tone_gain_db(probe, rate=rate, dbfs=-6.0,
                                   frequency=f0, seconds=1.0)
                want = rbj_db(f0, FLAT_Q, rate, probe)
                worst = max(worst, abs(got - want))
    print("  worst |rendered - closed form| over every rate/f0/probe: "
          "%.4f dB (bar 0.10) -> %s"
          % (worst, "green" if worst <= 0.10 else "RED"))
    print("  planted fault - coefficients built for 48 kHz while 44.1 kHz "
          "runs:")
    rate, f0, probe = 44100, 100.0, 25.0
    data = probes.sine(probe, 1.0, -6.0)
    source = ArraySource(data, rate=rate, channels=CHANNELS)
    effect = audioeffects.create("HighPass", source, rate, frequency=f0)
    effect._pole_one.frequency = f0 * 48000.0 / rate
    wet = take(effect, rate, rate=rate)
    ref = dry(data, rate, rate=rate)
    got = 20.0 * math.log10(
        abs(kit.tone_bin(wet.float[rate // 2:, 0], rate, probe))
        / abs(kit.tone_bin(ref.float[rate // 2:, 0], rate, probe)))
    want = rbj_db(f0, FLAT_Q, rate, probe)
    print("    %.3f dB against a closed form of %.3f -> %s"
          % (got, want, "RED" if abs(got - want) > 0.10 else "green"))


def latency():
    print("\n== Latency: reported against measured ==")
    for rate in (48000, 44100):
        click = probes.click_stereo(frames=8192, offset=256)
        _, effect = build(click, rate=rate, frequency=300.0)
        wet = take(effect, 8192, rate=rate)
        reference = dry(click, 8192, rate=rate)
        integer = kit.click(wet, reference, effect.latency_samples,
                            subsample=False)
        fine = kit.click(wet, reference, effect.latency_samples,
                         subsample=True, tolerance_samples=4.0)
        print("  %d Hz  reported %d  measured (integer) %s  (sub-sample) %s"
              " -> %s"
              % (rate, effect.latency_samples,
                 integer["values"]["measured_latency_samples"],
                 fine["values"]["measured_latency_samples"],
                 "green" if integer["passed"] else "RED"))


def refutation():
    """The refutation pass: the strongest case against each demonstrated
    trait, and the run that answers it."""
    print("\n== Refutation pass ==")

    print("  T2  \"|H(f0)| = Q was only checked at f0 = 1 kHz; the corner")
    print("      gain could be right there and wrong elsewhere.\"")
    print("      Re-read with the settle scaled to the ring: a Q-16 corner")
    print("      at 30 Hz rings for half a second, and a one-second render")
    print("      read from its midpoint reads the ring, not the corner")
    print("      (it did: +23.933 dB against +24.082, 0.149 dB out).")
    for f0 in (30.0, 300.0, 15000.0):
        for q in (0.5, 4.0, 16.0):
            want = 20.0 * math.log10(q)
            seconds = settled_seconds(f0, q)
            got = tone_gain_db(f0, dbfs=-14.0 - max(0.0, want),
                               frequency=f0, q=q, seconds=seconds)
            print("      f0=%-8g Q=%-5g  %+8.3f dB against %+8.3f  (%.2f s)"
                  "  %s"
                  % (f0, q, got, want, seconds,
                     "green" if abs(got - want) <= 0.05 else "RED"))

    print("  T3  \"the slope is fitted over one octave, f0/8 to f0/4; two")
    print("      points can fit any line.\"  Fitted over three octaves,")
    print("      f0/32 to f0/4, five points -- and the fit is bounded by")
    print("      the 16-bit floor, not by the filter: at 24 dB/oct, f0/32")
    print("      is 120 dB down, which at any input level inside full")
    print("      scale renders as zero. Points under 20 LSB are dropped")
    print("      and the count is printed.")
    for f0 in (640.0, 3200.0):
        for slope in (12, 24):
            xs, ys, dropped = [], [], 0
            for ratio in (1 / 32.0, 1 / 16.0, 1 / 8.0, 1 / 5.66, 1 / 4.0):
                probe = f0 * ratio
                gain, level = tone_gain_db(probe, dbfs=-2.0, frequency=f0,
                                           slope=slope, seconds=1.0,
                                           report_peak=True)
                if level < 20:
                    dropped += 1
                    continue
                xs.append(math.log(probe, 2.0))
                ys.append(gain)
            want = 12.0 if slope == 12 else 24.0
            if len(xs) < 3:
                print("      f0=%-8g slope=%-3d unmeasurable: %d of 5 points"
                      " under 20 LSB" % (f0, slope, dropped))
                continue
            fitted = float(np.polyfit(np.array(xs), np.array(ys), 1)[0])
            print("      f0=%-8g slope=%-3d fitted %.3f dB/oct over %d "
                  "points (%d dropped under 20 LSB)  %s"
                  % (f0, slope, fitted, len(xs), dropped,
                     "green" if abs(fitted - want) <= 0.6 else "RED"))

    print("  T1  \"exact zero could be a mute rather than a filter: a class")
    print("      that wrote silence would pass this.\"")
    step, removed = probes.dc_step(hold_s=0.5, total_s=3.0)
    frames = 48000 * 3
    _, effect = build(step, frequency=10.0)
    rendered = take(effect, frames)
    result = kit.tail(rendered, burst_end_frame=removed, dc_render=rendered,
                      dc_removed_frame=removed)
    passband = tone_gain_db(1000.0, frequency=10.0)
    print("      the same render has %s samples of tail before the zero, "
          "and 1 kHz through the same corner reads %+.4f dB"
          % (result["values"]["tail_samples"], passband))

    print("  T6  \"three rates agreeing could mean the class ignores the")
    print("      rate rather than honouring it.\"  The fault run above")
    print("      moves the reading 3.0 dB, so the measurement can tell the")
    print("      difference; and the closed form it is differenced against")
    print("      is evaluated at each rate separately.")


def main():
    print("HighPass Station C, audioif 0.2.0 at 2f6cbc3, "
          "class version %s" % highpass.HighPass.VERSION)
    for rate in RATES:
        tier_one(rate, 2)
    tier_one(48000, 1)
    tier_one_faults()
    trait_t1()
    trait_t2()
    trait_t3()
    trait_t4()
    trait_t5()
    trait_t6()
    latency()
    refutation()
    return 0


if __name__ == "__main__":
    sys.exit(main())
