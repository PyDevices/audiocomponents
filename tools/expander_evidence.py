"""Station C driver for `Expander` - every number in `Expander-evidence.md`.

    PYTHONPATH=lib .venv/bin/python tools/expander_evidence.py [--rate 48000]

CPython with numpy, over `tools/effect_measurements.py`. The renders are
taken in process from the committed probes in `tools/effect_probes/`, through
the same `audiofilters.Filter` block adapter `tools/render_effect.py` uses, so
a digest printed here is the digest that file prints. The cross-interpreter
leg is `render_effect.py` itself, driven from the shell; this file never
shells out.

**Where the kit does not fit, and what is done instead.** `effect_measurements
.curve()` fits the *compressor* soft-knee law, `out = in + makeup - (1 - 1
/ratio)*f(in)`, which is zero below the threshold and sloped above it. A
downward expander is the other way round, so CURVE's fitted `ratio`,
`threshold_db` and `knee_db` are not this class's and are never cited. What is
used is CURVE's law-agnostic export - the settled in/out point per step - and
E1's own least-squares slope is computed over those points, which is what the
trait statement asks for in the first place.

`gaintrace()`'s *attack* leg has the same shape of assumption: it takes
`nanmin` over the segment as the attack's target, which is a compressor's
attack (gain going down). An expander's attack goes up, so `nanmin` is the
starting value, the span is zero and `attack_t10_90_ms` is always `None`. Its
release leg reads begin -> end and is direction-agnostic, so both steps are
read through that one and E6 is reported in t50/t63/t95 rather than 10-90 %.

Both are gaps in the kit rather than in either class, and both are recorded in
`docs/effects/Expander-evidence.md` section 11 rather than worked around in
silence.
"""

import array
import math
import os
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                          # noqa: E402

import audiocore                                            # noqa: E402
import audiofilters                                         # noqa: E402
import audioeffects                                         # noqa: E402
import effect_measurements as kit                           # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = os.path.join(HERE, "tools", "effect_probes")

#: Macro indexes, from `Expander.MACRO_LABELS`.
THRESHOLD, RATIO, DEPTH, ATTACK, RELEASE = 0, 1, 2, 3, 4
KEY_LOW, KEY_HIGH, KEY_LISTEN, DETECTOR = 5, 6, 7, 8


# -- sources ---------------------------------------------------------------

def probe_pcm(name, rate, channels=2):
    path = os.path.join(PROBES, str(rate), "%dch" % channels, "%s.wav" % name)
    with wave.open(path, "rb") as handle:
        return handle.readframes(handle.getnframes())


def tone(hz, dbfs, seconds, rate, channels=2, square=False):
    """A synthesised tone, for the levels and frequencies the committed set
    does not carry. Stated in RMS dBFS, identical in every channel."""
    frames = int(rate * seconds)
    amplitude = 10.0 ** (dbfs / 20.0)
    data = array.array("h", [0] * frames * channels)
    for index in range(frames):
        phase = (index * hz / rate) % 1.0
        if square:
            value = amplitude * (1.0 if phase < 0.5 else -1.0)
        else:
            value = amplitude * math.sqrt(2.0) * math.sin(2 * math.pi * phase)
        word = int(max(-32768, min(32767, round(value * 32767))))
        for channel in range(channels):
            data[index * channels + channel] = word
    return data.tobytes()


def source_of(pcm, rate, channels, block=2048):
    """The probe behind `render_effect.py`'s block adapter, so a digest here
    is comparable with one from there."""
    raw = audiocore.RawSample(array.array("h", pcm), sample_rate=rate,
                              channel_count=channels)
    adapter = audiofilters.Filter(
        filter=None, mix=1.0, sample_rate=rate, channel_count=channels,
        bits_per_sample=16, samples_signed=True,
        buffer_size=block * channels * 2)
    adapter.play(raw, loop=False)
    return adapter, raw


def build(pcm, rate, channels=2, macros=(), patch=None, block=2048,
          key_pcm=None, options=None):
    adapter, raw = source_of(pcm, rate, channels, block)
    keyword = dict(options or {})
    if key_pcm is not None:
        key_adapter, _ = source_of(key_pcm, rate, channels, block)
        keyword["key"] = key_adapter
    effect = audioeffects.create("Expander", adapter, rate, **keyword)
    if patch is not None:
        effect.program_change(patch)
    for index, value in macros:
        effect.set_macro(index, value)
    return effect, adapter, raw


def pull(node, frames, rate, channels, **axes):
    out = bytearray()
    got = 0
    while got < frames:
        _, buffer = audiocore.get_buffer(node, False, 0)
        chunk = bytes(buffer)
        if not chunk:
            break
        out.extend(chunk)
        got += len(chunk) // (2 * channels)
    return kit.Render.from_pcm(bytes(out[:frames * 2 * channels]), rate,
                               channels, interpreter="cpython", **axes)


def render(pcm, rate, *, channels=2, macros=(), patch=None, frames=None,
           block=2048, key_pcm=None, label=None, options=None):
    effect, adapter, raw = build(pcm, rate, channels, macros, patch, block,
                                 key_pcm, options)
    total = frames or (len(pcm) // (2 * channels))
    audiocore.reset_buffer(effect.output)
    out = pull(effect.output, total, rate, channels, label=label)
    effect.deinit()
    adapter.deinit()
    return out


def dry(pcm, rate, channels=2, label=None):
    return kit.Render.from_pcm(pcm, rate, channels, interpreter="cpython",
                               label=label)


# -- the macro positions the traits are stated at --------------------------

def at(**settings):
    """0-127 positions for a set of engineering values."""
    from audioeffects.rebuilt.expander import Expander
    from audioeffects import _component
    order = {"threshold_db": THRESHOLD, "ratio": RATIO, "depth_db": DEPTH,
             "attack_ms": ATTACK, "release_ms": RELEASE,
             "key_low_hz": KEY_LOW, "key_high_hz": KEY_HIGH,
             "key_listen": KEY_LISTEN, "detector": DETECTOR}
    out = []
    for name, value in settings.items():
        index = order[name]
        out.append((index, _component.macro_position(
            Expander._MACRO_RANGES[index], value) * 127.0))
    return sorted(out)


def report(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def verdict(result):
    return "green" if result["passed"] else "RED %s" % "; ".join(result["red"])


# --------------------------------------------------------------------------
# Tier 2 - the circuit traits
# --------------------------------------------------------------------------

def e1_law(rate, fault=None):
    """E1 - the ratio law. CURVE's points, E1's own least-squares slope.

    The span per ratio is bounded by the int16 output floor, not by the node
    (dossier App. B1): at ratio 8 the trait's 30 dB clause would need 210 dB
    of output range. The span actually driven is printed with every row.
    """
    report("E1  the law - threshold -20 dBFS, RMS detector, depth -90 dB"
           "%s" % (" [FAULT: %s]" % fault if fault else ""))
    threshold = -20.0
    rows = []
    for ratio in (1.5, 2.0, 4.0, 8.0):
        span = min(30.0, (75.0 + threshold) / ratio)
        wet, dryer = {}, {}
        for step in range(7):
            level = threshold - 1.0 - step * (span - 1.0) / 6.0
            pcm = tone(1000.0, level, 0.6, rate)
            settings = dict(threshold_db=threshold,
                            ratio=ratio * (fault or 1.0), depth_db=-90.0,
                            attack_ms=5.0, release_ms=50.0, detector=1.0,
                            key_low_hz=25.0, key_high_hz=35000.0)
            wet[level] = render(pcm, rate, macros=at(**settings),
                                label="e1 %g @ %g" % (ratio, level))
            dryer[level] = dry(pcm, rate, label="e1 dry %g" % level)
        try:
            result = kit.curve(wet, dryer, detector="rms")
        except kit.SilentRenderError as refusal:
            print("  ratio %-4s span %4.1f dB  -> RED, refused: %s"
                  % (ratio, span, refusal))
            rows.append((ratio, span, None, None, None, ["refused"]))
            continue
        points = [(p["in_db"], p["out_db"])
                  for p in result["values"]["points"]]
        xs = np.array([p[0] for p in points])
        ys = np.array([p[1] for p in points])
        slope = float(np.polyfit(xs, ys, 1)[0])
        fitted = np.polyval(np.polyfit(xs, ys, 1), xs)
        residual = float(np.abs(ys - fitted).max())
        error = 100.0 * (slope - ratio) / ratio
        red = []
        if abs(error) > 5.0:
            red.append("slope %.4f is %+.2f%% off the set ratio" %
                       (slope, error))
        if residual > 0.5:
            red.append("worst point %.3f dB off the fitted line" % residual)
        if fault and ratio * fault > 8.0:
            # The Ratio macro's span stops at 8.0, so a fault that multiplies
            # it cannot be expressed at the top of the span: the faulted run
            # is the clean one there. Said, rather than counted as a pass.
            red = ["not expressible: %g x %g is past the Ratio span's own "
                   "8.0 ceiling, so this row is the clean run"
                   % (ratio, fault)]
        rows.append((ratio, span, slope, error, residual, red))
        print("  ratio %-4s span %4.1f dB  slope %.4f (%+.2f%%)  "
              "worst residual %.3f dB  -> %s"
              % (ratio, span, slope, error, residual,
                 "green" if not red else "RED " + "; ".join(red)))
    above = []
    for level in (-15.0, -10.0, -6.0):
        pcm = tone(1000.0, level, 0.6, rate)
        settings = dict(threshold_db=threshold, ratio=4.0 * (fault or 1.0),
                        depth_db=-90.0, attack_ms=5.0, release_ms=50.0,
                        detector=1.0, key_low_hz=25.0, key_high_hz=35000.0)
        wet = render(pcm, rate, macros=at(**settings))
        gain = kit.rms_db(wet.float[wet.frames // 2:, 0]) - \
            kit.rms_db(dry(pcm, rate).float[wet.frames // 2:, 0])
        above.append(gain)
    del above[len(above):]
    print("  above threshold: %s dB (bar +/-0.05)"
          % ", ".join("%+.3f" % g for g in above))
    passed = (not any(row[5] for row in rows)
              and all(abs(g) <= 0.05 for g in above))
    print("  E1 -> %s" % ("green" if passed else "RED"))
    return passed


def e2_detector(rate, fault=False):
    """E2 - the detector. Sine against square at equal RMS, 15 dB below."""
    report("E2  the detector - sine and square at equal RMS -35 dBFS, "
           "threshold -20 dBFS, ratio 2%s"
           % (" [FAULT: detector forced to peak]" if fault else ""))
    settings = dict(threshold_db=-20.0, ratio=2.0, depth_db=-80.0,
                    attack_ms=5.0, release_ms=150.0,
                    detector=0.0 if fault else 1.0,
                    key_low_hz=25.0, key_high_hz=35000.0)
    gains = []
    for square in (False, True):
        pcm = tone(1000.0, -35.0, 1.0, rate, square=square)
        wet = render(pcm, rate, macros=at(**settings))
        half = wet.frames // 2
        gains.append(kit.rms_db(wet.float[half:, 0])
                     - kit.rms_db(dry(pcm, rate).float[half:, 0]))
    gap = abs(gains[0] - gains[1])
    print("  sine %+.2f dB   square %+.2f dB   gap %.2f dB (bar 0.50)"
          % (gains[0], gains[1], gap))
    print("  E2 -> %s" % ("green" if gap <= 0.5 else "RED"))
    return gap <= 0.5


def e3_key_band(rate):
    """E3 - the key band, as the trait states it: an out-of-band tone swept
    to 0 dBFS must leave the gain at its floor."""
    report("E3  the key band - 500-2000 Hz, threshold -40 dBFS, ratio 4, "
           "depth -60 dB")
    settings = dict(threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                    attack_ms=5.0, release_ms=50.0, detector=1.0,
                    key_low_hz=500.0, key_high_hz=2000.0)
    worst = 0.0
    for hz in (250.0, 4000.0):
        row = []
        for level in (-60.0, -40.0, -20.0, -6.0, 0.0):
            pcm = tone(hz, level, 1.0, rate)
            wet = render(pcm, rate, macros=at(**settings))
            half = wet.frames // 2
            out_db = kit.rms_db(wet.float[half:, 0])
            gain = out_db - kit.rms_db(dry(pcm, rate).float[half:, 0])
            if out_db < -85.0:
                # The output is under one LSB: it is at the floor, and the
                # dB reading is the quantiser's, not the class's.
                row.append((level, -60.0))
                continue
            row.append((level, gain))
            worst = max(worst, abs(gain - (-60.0)))
        print("  %6.0f Hz (an octave outside): %s"
              % (hz, "  ".join("%+.0f dBFS/%+.1f dB" % p for p in row)))
    print("  worst departure from the -60 dB floor: %.1f dB (bar 1.0)" % worst)
    print("  E3 -> %s" % ("green" if worst <= 1.0 else "RED, disconfirmed"))
    return worst <= 1.0


def e4_depth(rate, fault=False):
    """E4 - depth, through the class's own surface.

    The trait states its operating point as "the input 30 dB below threshold
    at -6 dBFS", which puts the threshold at +24 dBFS - outside the Threshold
    macro's -80..0 dB span, and outside the DS201's own (-54 dB to infinity,
    S1). The same overshoot is driven inside the surface instead: threshold at
    0 dBFS, input 30 dB below it. That caps what a 16-bit output can show, so
    the -60 dB row is reported for what it is rather than passed off: at a
    -30 dBFS input a -60 dB floor is -90 dBFS, under one LSB. The node-level
    numbers for -60 and -80 are the dossier's B4.
    """
    report("E4  depth - threshold 0 dBFS, input 30 dB below it at -30 dBFS, "
           "ratio 8%s" % (" [FAULT: depth pinned at 0 dB]" if fault else ""))
    quiet = tone(1000.0, -30.0, 0.6, rate)
    reference = dry(quiet, rate)
    worst = 0.0
    measurable = []
    for depth in (0.0, -20.0, -40.0, -60.0):
        settings = dict(threshold_db=0.0, ratio=8.0,
                        depth_db=0.0 if fault else depth, attack_ms=5.0,
                        release_ms=50.0, detector=1.0, key_low_hz=25.0,
                        key_high_hz=35000.0)
        wet = render(quiet, rate, macros=at(**settings))
        half = wet.frames // 2
        got = kit.rms_db(wet.float[half:, 0]) \
            - kit.rms_db(reference.float[half:, 0])
        settled = kit.rms_db(wet.float[half:, 0])
        floored = settled < -85.0 or not np.isfinite(got)
        note = "  <- at/under the int16 floor, not a reading of the class" \
            if floored else ""
        if not floored:
            worst = max(worst, abs(got - depth))
            measurable.append(depth)
        print("  depth %+6.1f dB -> %8.2f dB   error %+.2f (bar 0.50)%s"
              % (depth, got, got - depth, note))
    print("  measurable rows: %s; worst error %.2f dB"
          % (", ".join("%+.0f" % d for d in measurable), worst))
    print("  the -80 dB span clause and the -60 dB row are the node's, at a")
    print("  threshold above this class's span: dossier B4, -60.15 and "
          "-81.68 dB")
    passed = worst <= 0.5 and len(measurable) >= 3
    print("  E4 -> %s" % ("green on the rows a 16-bit path can show"
                          if passed else "RED"))
    return passed


def e5_one_shot(rate):
    """E5 - the one-shot. A 1 ms burst under a 200 ms attack."""
    report("E5  the one-shot - a 1 ms full-scale burst then silence, under a "
           "200 ms attack")
    frames = int(rate * 0.5)
    data = array.array("h", [0] * frames * 2)
    for index in range(int(rate * 0.001)):
        word = int(32767 * math.sin(2 * math.pi * 1000 * index / rate))
        data[index * 2] = word
        data[index * 2 + 1] = word
    pcm = data.tobytes()
    settings = dict(threshold_db=-40.0, ratio=8.0, depth_db=-80.0,
                    attack_ms=200.0, release_ms=200.0, detector=1.0,
                    key_low_hz=25.0, key_high_hz=35000.0)
    effect, adapter, _ = build(pcm, rate, macros=at(**settings))
    trace = []
    for _ in range(60):
        audiocore.get_buffer(effect.output, False, 0)
        trace.append(effect.gain_reduction_db())
    effect.deinit()
    adapter.deinit()
    print("  gain per block, first eight: %s"
          % " ".join("%.1f" % value for value in trace[:8]))
    print("  the class has no Hold macro to turn on; hold_ms is inert in "
          "DYN_EXPAND (dossier App. B5)")
    print("  E5 -> disconfirmed on the palette, not measured green or red "
          "here")
    return None


def e6_times(rate):
    """E6 - the times, read with the kit's GAINTRACE."""
    report("E6  the times - a 20 dB step, threshold -20 dBFS, ratio 2, "
           "depth -20 dB")
    for label, settings, low, high in (
            ("attack ", (1.0, 10.0, 100.0, 1000.0), -30.0, -10.0),
            ("release", (10.0, 100.0, 1000.0, 4000.0), -10.0, -30.0)):
        for setting in settings:
            hold_ms = max(600.0, setting * 6)
            first = tone(1000.0, low, 0.3, rate)
            second = tone(1000.0, high, hold_ms / 1000.0, rate)
            pcm = first + second
            macros = at(threshold_db=-20.0, ratio=2.0, depth_db=-20.0,
                        detector=1.0, key_low_hz=25.0, key_high_hz=35000.0,
                        **{("attack_ms" if label.strip() == "attack"
                            else "release_ms"): setting,
                           ("release_ms" if label.strip() == "attack"
                            else "attack_ms"): (10.0 if label.strip()
                                                == "attack" else 1.0)})
            wet = render(pcm, rate, macros=macros)
            # GAINTRACE's *attack* leg takes nanmin as the target, which is
            # a compressor's attack (gain going down). An expander's attack
            # goes up, so nanmin is the starting value and the span is zero.
            # Its release leg reads begin -> end and is direction-agnostic,
            # so both steps are read through that one.
            result = kit.gaintrace(wet, dry(pcm, rate), hop_ms=0.5,
                                   release_from_ms=300.0)
            values = result["values"]
            t50 = values.get("release_t50_ms")
            t63 = values.get("release_t63_ms")
            t95 = values.get("release_t95_ms")
            print("  %s %8.2f ms  t50 %9s  t63 %9s  t95 %9s ms   "
                  "t63/set %5s   (%s -> %s dB)"
                  % (label, setting,
                     "n/a" if t50 is None else "%.2f" % t50,
                     "n/a" if t63 is None else "%.2f" % t63,
                     "n/a" if t95 is None else "%.2f" % t95,
                     "n/a" if not t63 else "%.2f" % (t63 / setting),
                     values.get("release_from_gr_db"),
                     values.get("release_to_gr_db")))
    print("  E6 -> disconfirmed as stated: the settings are one-pole time")
    print("        constants, so a 10-90 %% time is not the same number")
    return None


# --------------------------------------------------------------------------
# Tier 1 - the invariants
# --------------------------------------------------------------------------

WIRE_MACROS = ("ratio 1.0", "depth 0 dB")


def wire_settings(which, faulted=False):
    base = dict(threshold_db=-20.0, attack_ms=5.0, release_ms=50.0,
                detector=1.0, key_low_hz=25.0, key_high_hz=35000.0)
    if which == "ratio 1.0":
        base.update(ratio=1.0, depth_db=-80.0)
    else:
        base.update(ratio=8.0, depth_db=0.0)
    if faulted:
        base["ratio"] = base["ratio"] * 1.0001 + 0.02
    return base


def tier1(rate, channels=2):
    report("Tier 1 invariants at %d Hz, %d channel(s), cpython"
           % (rate, channels))
    results = {}

    # WIRE - both wire states, byte compared against the source.
    pcm = probe_pcm("ramp_fs", rate, channels)
    for which in WIRE_MACROS:
        wet = render(pcm, rate, channels=channels,
                     macros=at(**wire_settings(which)))
        result = kit.wire(wet, dry(pcm, rate, channels), latency_samples=0)
        results["WIRE " + which] = result
        print("  WIRE  %-11s %s" % (which, verdict(result)))

    # LEVEL - unity through the wire state.
    wet = render(pcm, rate, channels=channels,
                 macros=at(**wire_settings("ratio 1.0")))
    result = kit.level(wet, dry(pcm, rate, channels))
    results["LEVEL"] = result
    print("  LEVEL rms %s dB -> %s"
          % (result["values"]["rms_db"], verdict(result)))

    # TAIL - burst then silence, at the class's declared state.
    burst = probe_pcm("burst_silence", rate, channels)
    settings = dict(threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                    attack_ms=5.0, release_ms=2000.0, detector=1.0,
                    key_low_hz=25.0, key_high_hz=35000.0)
    wet = render(burst, rate, channels=channels, macros=at(**settings))
    burst_end = int(rate * 0.2)
    result = kit.tail(wet, burst_end_frame=burst_end,
                      declared_tail_samples=0)
    results["TAIL"] = result
    print("  TAIL  tail %s samples, residual %s LSB -> %s"
          % (result["values"]["tail_samples"],
             result["values"]["residual_lsb"], verdict(result)))
    listen = render(burst, rate, channels=channels,
                    macros=at(key_listen=1.0, **settings))
    listen_result = kit.tail(listen, burst_end_frame=burst_end)
    print("  TAIL  Key Listen on (the diagnostic, off in every patch): "
          "tail %s samples, residual %s LSB"
          % (listen_result["values"]["tail_samples"],
             listen_result["values"]["residual_lsb"]))

    # CLICK - reported latency against the measured onset.
    click_pcm = probe_pcm("click_stereo", rate, channels)
    wet = render(click_pcm, rate, channels=channels, macros=at(**settings))
    result = kit.click(wet, dry(click_pcm, rate, channels), 0)
    results["CLICK"] = result
    print("  CLICK measured %s samples against a reported 0 -> %s"
          % (result["values"].get("measured_latency_samples"),
             verdict(result)))

    # RESPONSE - rate honesty: the Key High span clamps rather than refusing.
    from audioeffects.rebuilt.expander import Expander
    effect, adapter, _ = build(pcm, rate, channels,
                               macros=at(key_high_hz=35000.0))
    reported = effect.macro(KEY_HIGH)
    applied = effect._hz(reported)
    effect.deinit()
    adapter.deinit()
    print("  RATE  Key High at the top of its span reports %.0f Hz and "
          "applies %.0f Hz (Nyquist %.0f) -> %s"
          % (reported, applied, rate / 2,
             "green" if applied < rate / 2 else "RED"))
    del Expander
    return results


def state(rate, channels=2):
    report("STATE at %d Hz, %d channel(s), cpython" % (rate, channels))
    settings = dict(threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                    attack_ms=5.0, release_ms=200.0, detector=1.0,
                    key_low_hz=25.0, key_high_hz=35000.0)
    probe = probe_pcm("burst_silence", rate, channels)
    effect, adapter, raw = build(probe, rate, channels, macros=at(**settings))

    def pull_blocks(blocks):
        out = bytearray()
        for _ in range(blocks):
            _, buffer = audiocore.get_buffer(effect.output, False, 0)
            out.extend(bytes(buffer))
        return kit.Render.from_pcm(bytes(out), rate, channels,
                                   interpreter="cpython")

    def swap(which):
        # A marker rather than a node: `audiofilters.Filter(loop=False)` is
        # spent once its probe has been delivered, so handing the *same*
        # object back would test whether an exhausted source resumes, which
        # is not the invariant. A fresh adapter over the same bytes is.
        data = probe if which == "probe" else bytes(len(probe))
        effect._node.play(source_of(data, rate, channels, 2048)[0])

    result = kit.state(effect, pull=pull_blocks, swap=swap,
                       probe_source="probe", silent_source="silent",
                       blocks=64, nodes=[("Dynamics", effect._node)])
    values = result["values"]
    print("  reset residual %s LSB; resumed %s; %s bytes over %s pulls; "
          "capabilities %s"
          % (values["reset_residual_lsb"], values["resumed"],
             values["alloc_growth_bytes"], values["alloc_pulls"],
             values["capabilities"]))
    print("  nodes enumerated: %s" % values["nodes"])
    print("  STATE -> %s" % verdict(result))
    print("  note: audiodynamics.Dynamics has no deinit/__enter__/__exit__ at")
    print("        all (upstream-diff.md:711-714), so the deinit leg is the")
    print("        class's own contract, checked below rather than by STATE.")
    return result


def deinit_contract(rate):
    report("deinit(), by the component contract rather than by STATE")
    settings = dict(threshold_db=-40.0, ratio=4.0, depth_db=-60.0)
    probe = probe_pcm("burst_silence", rate, 2)
    effect, adapter, raw = build(probe, rate, 2, macros=at(**settings))
    node = effect._node
    for _ in range(4):
        audiocore.get_buffer(effect.output, False, 0)
    effect.deinit()
    owned_cleared = effect._nodes == [] and effect._output is None
    try:
        effect.output
        source_still_reachable = False
    except RuntimeError:
        source_still_reachable = True
    _, buffer = audiocore.get_buffer(adapter, False, 0)
    source_renders = any(bytes(buffer))
    effect.deinit()                      # idempotent
    del node, raw
    print("  owned list cleared: %s; output refuses after deinit: %s; "
          "borrowed source still renders: %s; deinit twice: no error"
          % (owned_cleared, source_still_reachable, source_renders))
    passed = owned_cleared and source_still_reachable and source_renders
    print("  deinit -> %s" % ("green" if passed else "RED"))
    return passed


# --------------------------------------------------------------------------
# Planted faults - one of the same kind for every readout cited green
# --------------------------------------------------------------------------

def faults(rate):
    report("Planted faults - each readout shown red, with the clean control "
           "beside it")

    print("\n  WIRE: the wire state nudged off unity (ratio 1.0 -> 1.0201)")
    pcm = probe_pcm("ramp_fs", rate, 2)
    clean = render(pcm, rate, macros=at(**wire_settings("ratio 1.0")))
    dirty = render(pcm, rate,
                   macros=at(**wire_settings("ratio 1.0", faulted=True)))
    source = dry(pcm, rate)
    print("    clean   -> %s" % verdict(kit.wire(clean, source)))
    print("    faulted -> %s" % verdict(kit.wire(dirty, source)))

    print("\n  TAIL: +1 LSB of DC written into the settled state")
    burst = probe_pcm("burst_silence", rate, 2)
    settings = dict(threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                    attack_ms=5.0, release_ms=2000.0, detector=1.0,
                    key_low_hz=25.0, key_high_hz=35000.0)
    wet = render(burst, rate, macros=at(**settings))
    end = int(rate * 0.2)
    print("    clean   -> %s"
          % verdict(kit.tail(wet, burst_end_frame=end,
                             declared_tail_samples=0)))
    faulted = np.array(wet.data, dtype=np.int16)
    faulted[end + 1000:, :] += 1
    injected = kit.Render.from_pcm(faulted.tobytes(), rate, 2,
                                   interpreter="cpython")
    print("    faulted -> %s"
          % verdict(kit.tail(injected, burst_end_frame=end,
                             declared_tail_samples=0)))

    print("\n  CLICK: latency_samples reported 256 short, the DSP untouched")
    click_pcm = probe_pcm("click_stereo", rate, 2)
    wet = render(click_pcm, rate, macros=at(**settings))
    source = dry(click_pcm, rate, 2)
    print("    clean   -> %s" % verdict(kit.click(wet, source, 0)))
    print("    faulted -> %s" % verdict(kit.click(wet, source, 256)))
    print("    the audio digest is the same render both ways: %08x"
          % wet.digest)

    print("\n  E1: the ratio driven 30 %% high")
    e1_law(rate, fault=1.3)

    print("\n  E2: the Detector toggle forced to peak")
    e2_detector(rate, fault=True)

    print("\n  E4: Depth pinned at 0 dB")
    e4_depth(rate, fault=True)

    print("\n  STATE deinit leg: a node the class does not own, declared "
          "owned")
    probe = probe_pcm("burst_silence", rate, 2)
    effect, adapter, _ = build(probe, rate, 2, macros=at(**settings))

    def pull_blocks(blocks):
        out = bytearray()
        for _ in range(blocks):
            _, buffer = audiocore.get_buffer(effect.output, False, 0)
            out.extend(bytes(buffer))
        return kit.Render.from_pcm(bytes(out), rate, 2,
                                   interpreter="cpython")

    def swap(which):
        data = probe if which == "probe" else bytes(len(probe))
        effect._node.play(source_of(data, rate, 2, 2048)[0])
    planted = audiofilters.Filter(filter=None, mix=1.0, sample_rate=rate,
                                  channel_count=2, bits_per_sample=16,
                                  samples_signed=True, buffer_size=2048)
    result = kit.state(effect, pull=pull_blocks, swap=swap,
                       probe_source="probe", silent_source="silent",
                       blocks=16,
                       nodes=[("Dynamics", effect._node),
                              ("planted", planted)])
    print("    faulted -> %s" % verdict(result))
    print("    (the clean run above declares the one node the class builds "
          "and is green)")

    print("\n  Not planted, and why: the reset leg's own fault is 'a delay")
    print("  line left full'. This class's audio path is a per-sample")
    print("  multiply with no sample memory, so there is no line to fill -")
    print("  silence in is zero out whatever the envelope holds. That fault")
    print("  is planted where it bites, on the foundation's two-arm reset")
    print("  walk (tests/test_component_foundation.py).")


def what_reset_clears(rate):
    """What `reset()` clears and what the node deliberately keeps.

    `audiodynamics.Dynamics.reset_buffer` drops the detector envelopes and
    keeps the side-chain filter memory and the last reported gain reduction
    (`audioif/docs/upstream-diff.md:704-706`), so the class's reset walk
    inherits exactly that. Read at the boundary rather than inferred: the
    reported gain reduction immediately after `reset()`, against a fresh
    instance's, and the first block after it.
    """
    report("What reset() clears, and what it deliberately keeps")
    settings = dict(threshold_db=-40.0, ratio=4.0, depth_db=-60.0,
                    attack_ms=5.0, release_ms=2000.0, detector=1.0,
                    key_low_hz=500.0, key_high_hz=2000.0)
    quiet = tone(1000.0, -55.0, 0.4, rate)
    loud = tone(1000.0, -6.0, 0.4, rate)

    fresh, _, _ = build(loud, rate, macros=at(**settings))
    print("  a fresh instance reports %+.2f dB before its first block"
          % fresh.gain_reduction_db())
    fresh.deinit()

    primed, adapter, _ = build(quiet, rate, macros=at(**settings))
    for _ in range(60):
        audiocore.get_buffer(primed.output, False, 0)
    before = primed.gain_reduction_db()
    primed.reset()
    after = primed.gain_reduction_db()
    primed._node.play(source_of(loud, rate, 2, 2048)[0])
    for macro, value in at(**settings):
        primed.set_macro(macro, value)
    for _ in range(120):
        audiocore.get_buffer(primed.output, False, 0)
    settled = primed.gain_reduction_db()
    primed.deinit()
    adapter.deinit()
    print("  primed on a quiet -55 dBFS tone it reports %+.2f dB; "
          "immediately" % before)
    print("  after reset() it still reports %+.2f dB - the last reported"
          % after)
    print("  gain reduction is one of the two things the node keeps on")
    print("  purpose. Driven on from a loud -6 dBFS tone it settles at")
    print("  %+.2f dB, so the detector envelopes really were dropped."
          % settled)
    print("  Neither is a defect: it is the node's documented reset")
    print("  (upstream-diff.md:704-706), and the class's walk inherits it.")


# --------------------------------------------------------------------------
# Digests
# --------------------------------------------------------------------------

def digests(rate):
    report("Digests, cpython, in process - the same block adapter "
           "render_effect.py uses")
    settings = at(threshold_db=-36.0, ratio=1.5, depth_db=-20.0,
                  attack_ms=5.0, release_ms=200.0, detector=1.0,
                  key_low_hz=25.0, key_high_hz=35000.0)
    for probe in ("chord", "noise_det", "sweep_log"):
        pcm = probe_pcm(probe, rate, 2)
        wet = render(pcm, rate, macros=settings, block=2048,
                     label=probe)
        print("  %-10s %5d Hz  block 2048  fnv %08x  sum %d  frames %d"
              % (probe, rate, wet.digest, wet.byte_sum, wet.frames))


def main(argv):
    rate = 48000
    if "--rate" in argv:
        rate = int(argv[argv.index("--rate") + 1])
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    steps = [("e1", lambda: e1_law(rate)), ("e2", lambda: e2_detector(rate)),
             ("e3", lambda: e3_key_band(rate)), ("e4", lambda: e4_depth(rate)),
             ("e5", lambda: e5_one_shot(rate)), ("e6", lambda: e6_times(rate)),
             ("tier1", lambda: tier1(rate)),
             ("tier1mono", lambda: tier1(rate, 1)),
             ("state", lambda: state(rate)),
             ("deinit", lambda: deinit_contract(rate)),
             ("reset", lambda: what_reset_clears(rate)),
             ("faults", lambda: faults(rate)),
             ("digests", lambda: digests(rate))]
    print("Expander evidence, %d Hz, cpython %s"
          % (rate, sys.version.split()[0]))
    for name, step in steps:
        if only and name != only:
            continue
        step()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
