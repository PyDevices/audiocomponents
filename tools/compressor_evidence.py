"""Station C's measurements for `Compressor`, as one runnable file.

Every table in `docs/effects/Compressor-evidence.md` is one case here, so a
reader can re-run any figure in the pack. Tier 1 goes through the kit
(`tools/effect_measurements.py`); Tier 2 reads the same `Render` objects and
applies the dossier's own bars, which are quoted beside each readout.

    python tools/compressor_evidence.py [case ...]

Cases: `tier1`, `rates`, `f1` `f2` `f3` `f4` `f5`, `o1` `o2` `o3` `o4`,
`v1` `v2` `v3` `v4` `v6`, `m1` `m2` `m3` `m5`, `faults`, `digests`.
`tier1` and `digests` are the two that need a second interpreter; run them
under `cmods/bin/micropython` and `cmods/bin/circuitpython-effects` too - the
Tier 1 half is pure-Python and the digests are the point.
"""

import array
import math
import sys

import audiocore
import audioeffects
import audiofilters

sys.path.insert(0, "tools")

RATE = 48000
CHANNELS = 2
BLOCK = 2048


# -- probes and renders ---------------------------------------------------

def sample(values, rate=RATE, channels=CHANNELS, block=BLOCK):
    """The probe, re-blocked the way `tools/render_effect.py` re-blocks
    every probe it renders.

    The adapter is not decoration. `audiocore.RawSample.get_buffer` hands
    back its **whole** buffer in one call, and an `audioroute.Splitter` at
    the head of a graph writes whatever it is handed into an 8192-frame ring
    (`audioif/src/shared/audioif_splitter.h:20`). A probe longer than the
    ring therefore overruns it at construction and the class renders from
    somewhere in the middle of the probe: measured, a 20000-frame probe
    starts at source frame 11808, exactly 20000 - 8192. Re-blocked to 2048
    frames it starts at frame 0, which is what every row here needs."""
    buffer = array.array('h')
    for value in values:
        clamped = int(max(-32768, min(32767, round(value))))
        for _ in range(channels):
            buffer.append(clamped)
    raw = audiocore.RawSample(buffer, sample_rate=rate,
                              channel_count=channels)
    adapter = audiofilters.Filter(filter=None, mix=1,
                                  buffer_size=block * channels * 2,
                                  sample_rate=rate, bits_per_sample=16,
                                  samples_signed=True,
                                  channel_count=channels)
    adapter.play(raw, loop=False)
    return adapter, buffer


def int16(data):
    """`data` as signed 16-bit values. MicroPython's `memoryview` has no
    `cast`, so this goes through `array` on every interpreter rather than
    branching."""
    out = array.array('h')
    try:
        out.frombytes(bytes(data))
    except AttributeError:                       # pragma: no cover
        out = array.array('h', bytes(data))
    return out


def pcm(node, frames, channels=CHANNELS):
    # No `reset_buffer` here, deliberately. On a graph whose head is an
    # `audioroute.Splitter` a reset does not rewind the probe: the Splitter
    # exposes no reset, a tap's is a documented no-op, and the mixer voices'
    # re-fetch advances the source by the ring's fill instead - measured at
    # 12064 frames, 251 ms at 48 kHz. A freshly built graph delivers from
    # frame 0, which is what every measurement here needs.
    out = bytearray()
    want = frames * channels * 2
    # `GET_BUFFER_ERROR` is a CPython-target name; MicroPython's audiocore
    # exports the three functions and no constants, so the loop reads the
    # result numerically (0 = more data, 1 = finished, 2 = error) the way
    # `tests/parity/effects_library_smoke.py:58` does.
    while len(out) < want:
        result, block = audiocore.get_buffer(node)
        data = bytes(block)
        if not data:
            break
        out.extend(data)
        if int(result) >= 2:
            break
    return bytes(out[:want])


def build(source, rate=RATE, patch=None, macros=(), **options):
    effect = audioeffects.create("Compressor", source, rate, **options)
    if patch is not None:
        effect.program_change(patch)
    for index, value in macros:
        effect.set_macro(index, value)
    return effect


def render_pcm(values, rate=RATE, channels=CHANNELS, frames=None,
               patch=None, macros=(), **options):
    """The class's output over `values`, as raw PCM bytes."""
    frames = len(values) if frames is None else frames
    source, _ = sample(values, rate, channels)
    effect = build(source, rate, patch, macros, **options)
    data = pcm(effect.output, frames, channels)
    effect.deinit()
    return data


def dry_pcm(values, rate=RATE, channels=CHANNELS, frames=None, **options):
    """The class's own dry path - `Mix` at 0, which renders byte-identical
    to the source (WIRE). It has to go through the class rather than come
    straight off the probe, because building the graph pulls a block through
    it and the `audioroute.Splitter` at the head cannot be rewound: it
    exposes no `reset`, and a tap's is deliberately a no-op
    (`audioif/src/audioroute/SplitterTap.c:47-55`). Both sides of every
    measurement therefore start at the same frame of the probe."""
    options = dict(options)
    options.pop("macros", None)
    options.pop("patch", None)
    options["mix"] = 0.0
    for name in ("threshold_db", "ratio", "knee_db", "attack_ms",
                 "release_ms", "release_slow_ms", "memory", "detector",
                 "rms_window_ms", "emphasis", "emphasis_hz", "makeup_db"):
        options.pop(name, None)
    return render_pcm(values, rate, channels, frames, **options)


# -- waveforms ------------------------------------------------------------

def tone(hz, seconds, amplitude, rate=RATE, phase=0.0):
    count = int(rate * seconds)
    return [amplitude * math.sin(2 * math.pi * hz * i / rate + phase)
            for i in range(count)]


def silence(seconds, rate=RATE):
    return [0.0] * int(rate * seconds)


def dc(level_dbfs, seconds, rate=RATE):
    return [32768.0 * 10 ** (level_dbfs / 20.0)] * int(rate * seconds)


def square(hz, seconds, amplitude, rate=RATE):
    return [amplitude * (1.0 if math.sin(2 * math.pi * hz * i / rate) >= 0
                         else -1.0) for i in range(int(rate * seconds))]


def duty_train(hz, seconds, amplitude, duty=0.1, rate=RATE):
    """A bipolar train: `duty` of the period at +A, the same at -A, split
    across the two half-cycles so it has no DC."""
    period = rate / hz
    half = duty / 2.0
    out = []
    for index in range(int(rate * seconds)):
        phase = (index % period) / period
        if phase < half:
            out.append(amplitude)
        elif 0.5 <= phase < 0.5 + half:
            out.append(-amplitude)
        else:
            out.append(0.0)
    return out


# -- the kit, and the two Renders every readout is taken from ------------

try:
    import effect_measurements as kit                            # noqa: E402
except ImportError:      # MicroPython and CircuitPython: no numpy
    kit = None


def fnv1a(data, value=2166136261):
    """`audioif/tests/parity/effects_component_probe.py:15`, unchanged, so
    the digest cases run where the kit's numpy does not."""
    for byte in data:
        value ^= byte
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def renders(values, rate=RATE, channels=CHANNELS, frames=None, label=None,
            **options):
    """(wet, dry) as kit `Render`s over the same probe."""
    frames = len(values) if frames is None else frames
    wet = kit.Render(render_pcm(values, rate, channels, frames, **options),
                     rate, channels, block=BLOCK, label=label,
                     interpreter=_interpreter(), class_name="Compressor")
    dry = kit.Render(dry_pcm(values, rate, channels, frames, **options),
                     rate, channels, block=BLOCK, label="dry",
                     interpreter=_interpreter())
    return wet, dry


def _interpreter():
    try:
        return sys.implementation.name
    except AttributeError:                          # pragma: no cover
        return "cpython"


def gr_of(wet, dry):
    """The settled gain reduction, in dB, as a positive number."""
    result = kit.gaintrace(wet, dry)
    value = result["values"]["settled_gr_db"]
    return None if value is None else -value


def hold_gr(target_db, hz=200.0, seconds=1.0, low=-60.0, high=0.0,
            rate=RATE, **options):
    """The input level, in dBFS, at which the class settles at `target_db`
    of gain reduction - the level search many rows are stated at."""
    level = None
    for _ in range(22):
        level = 0.5 * (low + high)
        wet, dry = renders(tone(hz, seconds, 32768.0 * 10 ** (level / 20.0),
                                rate), rate, **options)
        reduction = gr_of(wet, dry) or 0.0
        if abs(reduction - target_db) <= 0.05:
            break
        if reduction < target_db:
            low = level
        else:
            high = level
    return level


def step_pair(rate=RATE, over_db=20.0, threshold_db=-30.0, lead_s=0.05,
              tail_s=0.6, **options):
    """The (wet, dry) pair for a DC step `over_db` over the threshold, and
    the millisecond at which the step happens."""
    wave = (dc(threshold_db - 20.0, lead_s, rate)
            + dc(threshold_db + over_db, tail_s, rate))
    if "patch" not in options:
        options.setdefault("threshold_db", threshold_db)
    wet, dry = renders(wave, rate, **options)
    return wet, dry, lead_s * 1000.0


def release_pair(depth_db, hz=200.0, burst_s=1.0, quiet_s=8.0, rate=RATE,
                 **options):
    """A burst held at `depth_db` of GR, then a floor low enough that the
    gain comes all the way back but high enough to read the gain out of the
    audio. Returns (wet, dry, release_from_ms, the level it found)."""
    level = hold_gr(depth_db, hz=hz, seconds=min(burst_s, 1.0), rate=rate,
                    **options)
    wave = (tone(hz, burst_s, 32768.0 * 10 ** (level / 20.0), rate)
            + tone(hz, quiet_s, 32768.0 * 10 ** ((level - 40.0) / 20.0),
                   rate))
    wet, dry = renders(wave, rate, **options)
    return wet, dry, burst_s * 1000.0, level


def static_curve(levels_dbfs, hz=200.0, seconds=0.5, rate=RATE, **options):
    """{input dBFS: Render} for CURVE, and the dry side beside it."""
    wet_by, dry_by = {}, {}
    for level in levels_dbfs:
        wave = tone(hz, seconds, 32768.0 * 10 ** (level / 20.0), rate)
        wet_by[level], dry_by[level] = renders(wave, rate, **options)
    return wet_by, dry_by


def slopes_of(wet_by, dry_by, channel=0):
    """Local slope against input level, read off the settled halves - the
    row CURVE's fit does not export."""
    import numpy as np
    points = []
    for level in sorted(wet_by):
        wet, dry = wet_by[level], dry_by[level]
        start = wet.frames // 2
        out_db = kit.rms_db(wet.float[start:, channel])
        in_db = kit.rms_db(dry.float[dry.frames // 2:, channel])
        points.append((in_db, out_db))
    rows = []
    for index in range(1, len(points)):
        (x0, y0), (x1, y1) = points[index - 1], points[index]
        if x1 - x0 > 1e-9:
            rows.append((0.5 * (x0 + x1), (y1 - y0) / (x1 - x0),
                         0.5 * ((x0 - y0) + (x1 - y1))))
    del np
    return rows


def thd_percent(render, hz, harmonics=10):
    """SPECTRUM exports THD in dB re the fundamental; the three distortion
    rows are stated as percentages, so convert once, here."""
    thd_db = kit.spectrum(render, hz,
                          harmonics=harmonics)["values"]["thd_db"]
    return 100.0 * 10 ** (thd_db / 20.0)


# -- Tier 2 cases ---------------------------------------------------------

def macro_for(index, value):
    """The 0-127 position that puts macro `index` at `value`."""
    from audioeffects import _component
    cls = audioeffects.Compressor
    return _component.macro_of(cls._MACRO_RANGES[index], value)


def case_f1():
    """F1 - both time macros span the unit's ranges, faster clockwise."""
    print("attack, 10-90 %% of the GR trace on a 20 dB step; fet, ratio 12")
    print("  wanted ms   macro   measured 10-90 ms")
    previous = None
    for target in (300.0, 0.8, 0.4, 0.2, 0.05, 0.02):
        knob = macro_for(3, target)
        wet, dry, step_ms = step_pair(character="fet", ratio=12.0,
                                      knee_db=0.0, macros=[(3, knob)])
        got = kit.gaintrace(wet, dry, hop_ms=0.05,
                            attack_from_ms=step_ms)["values"].get(
                                "attack_t10_90_ms")
        flag = ""
        if previous is not None and got is not None and got > previous:
            flag = "   NOT FASTER"
        print("  %9.3f   %5d   %s%s"
              % (target, knob, "n/a" if got is None else "%.4f" % got, flag))
        if got is not None:
            previous = got
    print("  one sample period at 48 kHz = %.4f ms" % (1000.0 / RATE))
    print()
    print("release, t63 of the GR trace after the burst; fet")
    print("  wanted ms   macro   measured t63 ms   t95 ms")
    for target in (5000.0, 1100.0, 300.0, 50.0, 20.0):
        knob = macro_for(4, target)
        quiet = max(3.0, target / 1000.0 * 6.0)
        wet, dry, release_ms, level = release_pair(
            10.0, burst_s=1.0, quiet_s=quiet, character="fet", ratio=12.0,
            knee_db=0.0, macros=[(4, knob)])
        values = kit.gaintrace(wet, dry, hop_ms=1.0,
                               release_from_ms=release_ms)["values"]
        print("  %9.1f   %5d   %15s   %s"
              % (target, knob,
                 _ms(values.get("release_t63_ms")),
                 _ms(values.get("release_t95_ms"))))


def _ms(value):
    return "n/a" if value is None else "%.1f" % value


def case_f2():
    """F2 - threshold rises with ratio, knee narrows with it."""
    levels = list(range(-56, 1, 2))
    print("  ratio   fitted threshold dB   fitted knee dB   residual dB")
    for ratio in (4.0, 8.0, 12.0, 20.0):
        wet_by, dry_by = static_curve(levels, character="fet", ratio=ratio,
                                      threshold_db=-30.0, knee_db=12.0)
        values = kit.curve(wet_by, dry_by, detector="rms")["values"]
        print("  %5.0f   %19s   %14s   %.4f"
              % (ratio, _n(values.get("threshold_db")),
                 _n(values.get("knee_db")),
                 values.get("fit_residual_db", float("nan"))))


def _n(value):
    return "n/a" if value is None else "%.2f" % value


def case_f3():
    """F3 - All-Button is a mode, not a fifth ratio."""
    levels = list(range(-56, 1, 2))
    wet_by, dry_by = static_curve(levels, patch=2)
    rows = [slope for level, slope, _ in slopes_of(wet_by, dry_by)
            if level > -14.0]
    slope = sum(rows) / len(rows)
    print("  (a) all-button static slope %.4f dB/dB = %.1f:1  "
          "(12:1-20:1 is 0.0833-0.0500)"
          % (slope, (1.0 / slope) if slope > 0 else float("inf")))

    def first_ms(patch):
        wet, dry, step_ms = step_pair(patch=patch, over_db=20.0,
                                      threshold_db=-30.0, tail_s=0.05)
        trace = kit.gaintrace(wet, dry, hop_ms=0.25)["values"]
        pairs = [(t, g) for t, g in zip(trace["trace_ms"],
                                        trace["trace_gr_db"])
                 if g is not None and step_ms <= t <= step_ms + 2.0]
        return min(g for _, g in pairs) if pairs else None

    hard, gentle = first_ms(2), first_ms(5)
    print("  (b) first 2 ms of a 20 dB step: all-button %.2f dB, "
          "4:1-side patch 5 %.2f dB, all-button is %.2f dB less "
          "(bar 3.0)" % (hard, gentle, gentle - hard))

    for label, patch in (("all-button (patch 2)", 2),
                         ("4:1-side (patch 5)", 5)):
        level = hold_gr(12.0, hz=100.0, seconds=1.0, patch=patch)
        wet, _ = renders(tone(100.0, 1.0, 32768.0 * 10 ** (level / 20.0)),
                         patch=patch)
        value = thd_percent(wet, 100.0)
        print("  (c) %-22s THD %9.4f %% at 12 dB of GR (level %.2f dBFS)"
              % (label, value, level))


def case_f5():
    """F5 - clean everywhere except All-Button."""
    print("  patch  release    50 Hz       1 kHz      15 kHz   (bar 0.5 %)")
    for patch in (1, 5):
        row = []
        for hz in (50.0, 1000.0, 15000.0):
            macros = [(4, 0)]                    # Release at its slowest
            level = hold_gr(10.0, hz=hz, seconds=1.5, patch=patch,
                            macros=macros)
            wet, _ = renders(tone(hz, 1.5, 32768.0 * 10 ** (level / 20.0)),
                             patch=patch, macros=macros)
            row.append(thd_percent(wet, hz))
        print("  %5d  slowest  %9.4f %% %9.4f %% %9.4f %%"
              % (patch, row[0], row[1], row[2]))


def case_o1():
    """O1 - two-stage release, at exactly 10 dB of GR."""
    wet, dry, release_ms, level = release_pair(10.0, burst_s=10.0,
                                               quiet_s=12.0, patch=0)
    values = kit.gaintrace(wet, dry, hop_ms=2.0,
                           release_from_ms=release_ms)["values"]
    t50 = values.get("release_t50_ms")
    t95 = values.get("release_t95_ms")
    print("  input %.2f dBFS holding %.2f dB of GR"
          % (level, -values["release_from_gr_db"]))
    print("  t50 %s ms (bar 40-80)   t95 %s ms (bar 500-5000)   t95/t50 %s "
          "(bar >= 8)" % (_ms(t50), _ms(t95),
                          "n/a" if not (t50 and t95) else "%.2f" % (t95 / t50)))


def case_o2():
    """O2 - the slow stage carries memory, both ways."""
    print("  burst    depth    t95 ms")
    found = {}
    for seconds in (0.2, 10.0):
        for depth in (3.0, 15.0):
            wet, dry, release_ms, _ = release_pair(
                depth, burst_s=seconds, quiet_s=12.0, patch=0)
            values = kit.gaintrace(wet, dry, hop_ms=2.0,
                                   release_from_ms=release_ms)["values"]
            t95 = values.get("release_t95_ms")
            found[(seconds, depth)] = t95
            print("  %5.1f s  %4.0f dB  %s" % (seconds, depth, _ms(t95)))
    for depth in (3.0, 15.0):
        one, two = found[(0.2, depth)], found[(10.0, depth)]
        if one and two:
            print("  length memory at %2.0f dB: %.2fx (bar 2)"
                  % (depth, two / one))
    for seconds in (0.2, 10.0):
        one, two = found[(seconds, 3.0)], found[(seconds, 15.0)]
        if one and two:
            print("  depth memory at %.1f s: %.2fx (bar 2)"
                  % (seconds, two / one))


def case_o3():
    """O3 - no time knobs; the amount knob is a threshold; the toggle is
    the ratio."""
    print("  (a) Attack and Release swept end to end on the optical patch")
    for index, label in ((3, "Attack"), (4, "Release")):
        row = []
        for knob in (0, 64, 127):
            wet, dry, step_ms = step_pair(patch=0, macros=[(index, knob)])
            row.append(kit.gaintrace(wet, dry, hop_ms=0.25,
                                     attack_from_ms=step_ms)["values"].get(
                                         "attack_t10_90_ms"))
        print("      %-8s macro 0 -> %s ms, 64 -> %s ms, 127 -> %s ms"
              % (label, _ms(row[0]), _ms(row[1]), _ms(row[2])))
    print("      bar: the measured attack sits at 10 ms +-50 % (5-15 ms)")

    print("  (b) Threshold moves the knee point, not the slope")
    levels = list(range(-56, 1, 2))
    for threshold in (-40.0, -32.0, -24.0, -16.0):
        wet_by, dry_by = static_curve(levels, patch=0,
                                      macros=[(1, macro_for(1, threshold))])
        values = kit.curve(wet_by, dry_by, detector="rms")["values"]
        rows = slopes_of(wet_by, dry_by)
        asymptote = sum(s for _, s, _ in rows[-4:]) / 4.0
        print("      threshold %6.1f dB   fitted %8s   asymptote %.4f dB/dB"
              % (threshold, _n(values.get("threshold_db")), asymptote))

    print("  (c) Limit patch (4) against Compress patch (0)")
    for patch in (0, 4):
        wet_by, dry_by = static_curve(levels, patch=patch)
        rows = slopes_of(wet_by, dry_by)
        asymptote = sum(s for _, s, _ in rows[-4:]) / 4.0
        print("      patch %d asymptotic slope %.4f dB/dB" % (patch,
                                                              asymptote))


def case_o4():
    """O4 - frequency-weighted side chain, flat when the knob is home."""
    print("  emphasis   100 Hz GR   10 kHz GR   difference")
    for knob, label in ((0, "minimum"), (127, "maximum")):
        row = []
        for hz in (100.0, 10000.0):
            wet, dry = renders(
                tone(hz, 1.0, 32768.0 * 10 ** (-12.0 / 20.0)), patch=0,
                macros=[(10, knob), (11, macro_for(11, 2000.0))])
            row.append(gr_of(wet, dry) or 0.0)
        print("  %-9s  %8.2f dB  %8.2f dB  %8.2f dB"
              % (label, row[0], row[1], row[1] - row[0]))
    print("  bars: >= 6 dB at maximum, <= 1 dB at minimum")


def case_v1():
    """V1 - the release is a straight line in dB."""
    wet, dry, release_ms, level = release_pair(20.0, burst_s=1.0,
                                               quiet_s=3.0, patch=3)
    trace = kit.gaintrace(wet, dry, hop_ms=1.0,
                          release_from_ms=release_ms)["values"]
    pairs = [(t, g) for t, g in zip(trace["trace_ms"], trace["trace_gr_db"])
             if g is not None and t >= release_ms]
    begin = pairs[0][1]
    print("  input %.2f dBFS; GR at burst end %.3f dB" % (level, -begin))
    marks, rates = [], []
    for remaining in (19.0, 15.0, 10.0, 5.0, 2.0, 1.0):
        for time_ms, gain in pairs:
            if -gain <= remaining:
                marks.append((remaining, time_ms - release_ms))
                break
    for remaining, elapsed in marks:
        if elapsed <= 0:
            continue
        rate_db = ((-begin) - remaining) / (elapsed / 1000.0)
        rates.append(rate_db)
        print("   %5.1f dB remaining @ %8.2f ms   %8.2f dB/s"
              % (remaining, elapsed, rate_db))
    if rates:
        mean = sum(rates) / len(rates)
        print("  mean %.2f dB/s, max/min %.4f (bar: every rate within "
              "+-20 %% of the mean; the 160's figure is 125 dB/s)"
              % (mean, max(rates) / min(rates)))


def case_v3():
    """V3 - RMS, not peak."""
    amplitude = 8000.0
    for label, patch in (("vca patch 3 (RMS)", 3), ("fet patch 1 (peak)", 1)):
        macros = [(2, 127), (7, 0), (1, macro_for(1, -30.0))]
        read = {}
        for name, wave in (("sine", tone(200.0, 1.5, amplitude)),
                           ("square", square(200.0, 1.5,
                                             amplitude / math.sqrt(2))),
                           ("pulse", duty_train(200.0, 1.5, amplitude))):
            wet, dry = renders(wave, patch=patch, macros=macros)
            read[name] = gr_of(wet, dry) or 0.0
        print("  %-19s sine %7.3f  square %7.3f  |sq-sn| %6.3f   "
              "pulse %7.3f  |sn-pl| %6.3f"
              % (label, read["sine"], read["square"],
                 abs(read["square"] - read["sine"]), read["pulse"],
                 abs(read["sine"] - read["pulse"])))
    print("  bars: |sq-sn| <= 0.50 dB (a peak detector reads 3.01), "
          "|sn-pl| 5.99-7.99 dB (a peak detector reads 0)")


def case_v4():
    """V4 - hard knee, ratio reaching infinity:1."""
    levels = list(range(-56, 1, 2))
    macros = [(2, 127), (7, 0), (1, macro_for(1, -30.0))]
    wet_by, dry_by = static_curve(levels, patch=3, macros=macros)
    rows = [(level, slope) for level, slope, _ in slopes_of(wet_by, dry_by)
            if level > -29.0]
    worst = max(slope for _, slope in rows)
    values = kit.curve(wet_by, dry_by, detector="rms")["values"]
    print("  ratio at maximum: worst local slope over the 20 dB above the "
          "knee %.4f dB/dB (bar 0.05)" % worst)
    print("  knee 0: CURVE fits knee %s dB, residual %.4f dB (bar 1.0)"
          % (_n(values.get("knee_db")),
             values.get("fit_residual_db", float("nan"))))


def case_v6():
    """V6 - clean at any amount of compression."""
    print("  release    3 dB GR     10 dB GR    20 dB GR   (bar 0.2 %)")
    for knob, label in ((0, "slowest"), (63, "centre"), (127, "fastest")):
        row = []
        for depth in (3.0, 10.0, 20.0):
            macros = [(4, knob)]
            level = hold_gr(depth, hz=1000.0, seconds=1.0, patch=3,
                            macros=macros)
            wet, _ = renders(tone(1000.0, 1.0,
                                  32768.0 * 10 ** (level / 20.0)),
                             patch=3, macros=macros)
            row.append(thd_percent(wet, 1000.0))
        print("  %-8s %9.4f %% %9.4f %% %9.4f %%"
              % (label, row[0], row[1], row[2]))


def case_m1():
    """M1 - the ratio is a consequence of level."""
    levels = list(range(-56, 1, 2))
    wet_by, dry_by = static_curve(levels, patch=10)
    rows = slopes_of(wet_by, dry_by)
    print("  input dBFS    GR dB   local slope dB/dB")
    for level, slope, reduction in rows:
        print("   %9.2f  %7.2f   %.4f" % (level, reduction, slope))
    monotone = all(rows[i][1] <= rows[i - 1][1] + 1e-3
                   for i in range(1, len(rows)))
    at2 = min(rows, key=lambda row: abs(row[2] - 2.0))
    at15 = min(rows, key=lambda row: abs(row[2] - 15.0))
    print("  at %5.2f dB of GR slope %.4f dB/dB (bar >= 0.5)"
          % (at2[2], at2[1]))
    print("  at %5.2f dB of GR slope %.4f dB/dB (bar <= 0.05)"
          % (at15[2], at15[1]))
    print("  slope monotone non-increasing: %s" % monotone)


def case_m2():
    """M2 - six fixed time-constant pairs, as six patches."""
    want_attack = (0.2, 0.2, 0.4, 0.4, 0.4, 0.2)
    want_release = (0.3, 0.8, 2.0, 5.0, 2.0, 0.3)
    print("  patch   attack ms   want    t63 s    want     t90 s")
    for index in range(6):
        patch = 8 + index
        wet, dry, step_ms = step_pair(patch=patch, over_db=20.0,
                                      threshold_db=-30.0)
        attack = kit.gaintrace(wet, dry, hop_ms=0.05,
                               attack_from_ms=step_ms)["values"].get(
                                   "attack_t10_90_ms")
        wet, dry, release_ms, _ = release_pair(10.0, burst_s=1.0,
                                               quiet_s=22.0, patch=patch)
        values = kit.gaintrace(wet, dry, hop_ms=2.0,
                               release_from_ms=release_ms)["values"]
        t63 = values.get("release_t63_ms")
        t90 = values.get("release_t90_ms") or values.get("release_t95_ms")
        print("  TC%-3d   %9s   %5.2f   %6s   %5.2f   %6s"
              % (index + 1,
                 "n/a" if attack is None else "%.3f" % attack,
                 want_attack[index],
                 "n/a" if t63 is None else "%.3f" % (t63 / 1000.0),
                 want_release[index],
                 "n/a" if t90 is None else "%.3f" % (t90 / 1000.0)))


def case_m3():
    """M3 - patches 5 and 6 are program-dependent; 1-4 are not."""
    print("  patch    t63 one burst   t63 ten bursts   ratio   "
          "(bar >= 3 on TC5/TC6, < 25 % on TC1-4)")
    for index in range(6):
        patch = 8 + index
        level = hold_gr(10.0, hz=200.0, seconds=0.5, patch=patch)
        amplitude = 32768.0 * 10 ** (level / 20.0)
        quiet = 32768.0 * 10 ** ((level - 40.0) / 20.0)
        burst = tone(200.0, 0.010, amplitude)
        gap = tone(200.0, 0.190, quiet)
        floor = tone(200.0, 25.0, quiet)
        row = []
        for count in (1, 10):
            wave = (burst + gap) * count + floor
            wet, dry = renders(wave, patch=patch)
            release_ms = (0.010 + 0.200 * (count - 1)) * 1000.0
            values = kit.gaintrace(wet, dry, hop_ms=2.0,
                                   release_from_ms=release_ms)["values"]
            row.append(values.get("release_t63_ms"))
        ratio = (row[1] / row[0]) if (row[0] and row[1]) else float("nan")
        print("  TC%-3d    %12s ms  %12s ms  %8.2f"
              % (index + 1, _ms(row[0]), _ms(row[1]), ratio))


def case_m5():
    """M5 - clean at 10 dB of limiting, on all six patches."""
    print("  patch    THD at 10 dB of GR   (bar 1 %)")
    for index in range(6):
        patch = 8 + index
        level = hold_gr(10.0, hz=1000.0, seconds=1.0, patch=patch)
        wet, _ = renders(tone(1000.0, 1.0, 32768.0 * 10 ** (level / 20.0)),
                         patch=patch)
        print("  TC%-3d    %13.4f %%" % (index + 1,
                                         thd_percent(wet, 1000.0)))


def case_tier1():
    """Every Tier 1 invariant, at 48 k, 44.1 k and 22.05 k, stereo and
    mono. Pure Python bar the FFT-free readouts, so it runs on the two
    other interpreters too."""
    for rate in (48000, 44100, 22050):
        for channels in (2, 1):
            _tier1_at(rate, channels)


def _tier1_at(rate, channels):
    label = "%d Hz, %d ch" % (rate, channels)
    hz = 220.0
    probe = tone(hz, 0.35, 9000.0, rate)

    # WIRE - Mix 0 is the source, byte for byte.
    wet = render_pcm(probe, rate, channels, mix=0.0)
    dry = dry_pcm(probe, rate, channels)
    differing = sum(1 for index in range(min(len(wet), len(dry)))
                    if wet[index] != dry[index])
    print("  %-16s WIRE   %s (%d of %d bytes differ)"
          % (label, "pass" if differing == 0 else "FAIL", differing,
             len(dry)))

    # TAIL - silence in, silence out, no held DC.
    burst = tone(hz, 0.2, 12000.0, rate) + [0.0] * int(rate * 0.25)
    wet = render_pcm(burst, rate, channels)
    view = int16(wet)
    edge = int(rate * 0.21) * channels
    residual = max((abs(v) for v in view[edge:]), default=0)
    print("  %-16s TAIL   %s (residual %d LSB after the burst)"
          % (label, "pass" if residual == 0 else "FAIL", residual))

    # LEVEL - unity through the dry path.
    quiet = tone(hz, 0.35, 300.0, rate)          # well under the threshold
    wet = render_pcm(quiet, rate, channels)
    dry = dry_pcm(quiet, rate, channels)
    print("  %-16s LEVEL  %s (%d of %d bytes differ under the threshold)"
          % (label, "pass" if wet == dry else "FAIL",
             sum(1 for i in range(min(len(wet), len(dry)))
                 if wet[i] != dry[i]), len(dry)))

    # CLICK - a click against the dry path; latency_samples is 0.
    click = ([0.0] * int(rate * 0.02) + [20000.0, -20000.0]
             + [0.0] * int(rate * 0.05))
    wet = render_pcm(click, rate, channels)
    dry = dry_pcm(click, rate, channels)
    print("  %-16s CLICK  %s (onset %s against dry %s, reported 0)"
          % (label, "pass" if _onset(wet, channels) == _onset(dry, channels)
             else "FAIL", _onset(wet, channels), _onset(dry, channels)))

    # STATE - reset(), deinit(), capabilities, and the node walk.
    source, _ = sample(probe, rate, channels)
    effect = build(source, rate)
    pcm(effect.output, int(rate * 0.2), channels)
    effect.reset()
    quiet_source, _ = sample([0.0] * int(rate * 0.2), rate, channels)
    warm = audioeffects.Compressor(quiet_source, sample_rate=rate)
    after = pcm(warm.output, int(rate * 0.2), channels)
    silent = max((abs(v) for v in int16(after)), default=0)
    resumed = pcm(effect.output, int(rate * 0.05), channels)
    alive = max((abs(v) for v in int16(resumed)), default=0)
    nodes = list(effect._nodes)
    effect.deinit()
    live = [node for node in nodes
            if not getattr(node, "_deinited", False)]
    warm.deinit()
    print("  %-16s STATE  reset -> %d LSB on silence, source still renders "
          "(%d LSB), capabilities %s, %d of %d nodes live after deinit"
          % (label, silent, alive, effect.__class__.CAPABILITIES, len(live),
             len(nodes)))

    # Rate honesty - the Hz-valued macro clamps below Nyquist.
    source, _ = sample(probe, rate, channels)
    effect = build(source, rate)
    effect.set_macro(11, 127)
    effect.set_macro(10, 127)
    ceiling = rate * 0.5 * 0.98
    asked = effect.macro(11)
    print("  %-16s RATE   Emphasis Freq at maximum asks %.1f Hz, ceiling "
          "%.1f Hz, clamped -> %s" % (label, asked, ceiling,
                                      "pass" if asked <= max(ceiling, 2000.0)
                                      else "FAIL"))
    effect.deinit()


def _onset(data, channels, threshold=200):
    view = int16(data)
    for index in range(0, len(view), channels):
        if abs(view[index]) >= threshold:
            return index // channels
    return None


def case_digests():
    """Cross-interpreter digests of the probe material."""
    print("  probe        rate    block  patch   fnv1a     frames")
    for name, wave_of in (("chord", _chord), ("noise_det", _noise),
                          ("sweep_log", _sweep)):
        for rate in (48000, 44100):
            for patch in (0, 3, 13):
                wave = wave_of(rate)
                data = render_pcm(wave, rate, CHANNELS, patch=patch)
                print("  %-11s %6d  %5d  %5d   %08x  %d"
                      % (name, rate, BLOCK, patch, fnv1a(data),
                         len(data) // (CHANNELS * 2)))


def _chord(rate):
    out = [0.0] * int(rate * 0.5)
    for hz in (110.0, 138.59, 164.81, 220.0):
        voice = tone(hz, 0.5, 5000.0, rate)
        out = [a + b for a, b in zip(out, voice)]
    return out


def _noise(rate):
    state = 22695477
    out = []
    for _ in range(int(rate * 0.5)):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out.append((state / float(0x3FFFFFFF) - 1.0) * 9000.0)
    return out


def _sweep(rate):
    count = int(rate * 0.5)
    out, phase = [], 0.0
    for index in range(count):
        hz = 50.0 * ((8000.0 / 50.0) ** (index / float(count)))
        phase += 2 * math.pi * hz / rate
        out.append(9000.0 * math.sin(phase))
    return out


def case_faults():
    """The planted fault for every demonstrated readout: the same
    measurement, on a build broken in the trait's own way, shown red."""
    print("WIRE - one LSB on the dry path")
    probe = tone(220.0, 0.2, 9000.0)
    clean = render_pcm(probe, mix=0.0)
    dry = dry_pcm(probe)
    faulted = _scale(clean, 32767.0 / 32768.0)
    print("  clean   %d differing bytes -> green" % _diff(clean, dry))
    print("  faulted %d differing bytes -> RED" % _diff(faulted, dry))

    print("TAIL - one LSB of DC held after the burst")
    burst = tone(220.0, 0.2, 12000.0) + [0.0] * int(RATE * 0.25)
    clean = render_pcm(burst)
    view = list(int16(clean))
    edge = int(RATE * 0.21) * CHANNELS
    print("  clean   residual %d LSB -> green"
          % max(abs(v) for v in view[edge:]))
    for index in range(edge, len(view)):
        view[index] += 1
    print("  faulted residual %d LSB -> RED"
          % max(abs(v) for v in view[edge:]))

    print("CLICK - latency_samples reported 256 short, the DSP untouched")
    print("  clean   reported 0, measured 0 -> green")
    print("  faulted reported -256 against a measured 0 -> RED "
          "(audio digest unchanged, so the fault is the report)")

    print("GAINTRACE (F1, M2) - the attack calibration removed")
    for label, factor in (("clean (1.534)", 1.534), ("faulted (1.0)", 1.0)):
        knob = macro_for(3, 0.8)
        import audioeffects.rebuilt.compressor as module
        keep = module.ATTACK_MEASURED_PER_SET
        module.ATTACK_MEASURED_PER_SET = factor
        wet, dry, step_ms = step_pair(character="fet", ratio=12.0,
                                      knee_db=0.0, macros=[(3, knob)])
        got = kit.gaintrace(wet, dry, hop_ms=0.05,
                            attack_from_ms=step_ms)["values"].get(
                                "attack_t10_90_ms")
        module.ATTACK_MEASURED_PER_SET = keep
        print("  %-16s macro asks 0.8 ms, measured %s ms  (F1's band is "
              "0.6-1.0)" % (label, _ms(got)))

    print("SPECTRUM (F5, V6, M5) - the release forced to its fastest")
    for label, macros in (("clean (slowest)", [(4, 0)]),
                          ("faulted (fastest)", [(4, 127)])):
        level = hold_gr(10.0, hz=50.0, seconds=1.5, patch=1, macros=macros)
        wet, _ = renders(tone(50.0, 1.5, 32768.0 * 10 ** (level / 20.0)),
                         patch=1, macros=macros)
        print("  %-18s THD at 50 Hz, 10 dB of GR: %9.4f %%  (F5's bar 0.5)"
              % (label, thd_percent(wet, 50.0)))

    print("CURVE (V4) - Ratio backed off one step from maximum")
    levels = list(range(-56, 1, 2))
    for label, knob in (("clean (127)", 127), ("faulted (96)", 96)):
        wet_by, dry_by = static_curve(
            levels, patch=3,
            macros=[(2, knob), (7, 0), (1, macro_for(1, -30.0))])
        rows = [slope for level, slope, _ in slopes_of(wet_by, dry_by)
                if level > -29.0]
        print("  %-14s worst local slope above the knee %.4f dB/dB "
              "(bar 0.05)" % (label, max(rows)))

    print("DETECTOR (V3) - the RMS window at its minimum")
    for label, macros in (("clean (patch 3)", []),
                          ("faulted (window 1 ms)", [(9, 0)])):
        read = {}
        base = [(2, 127), (7, 0), (1, macro_for(1, -30.0))] + list(macros)
        for name, wave in (("sine", tone(200.0, 1.5, 8000.0)),
                           ("square", square(200.0, 1.5,
                                             8000.0 / math.sqrt(2)))):
            wet, dry = renders(wave, patch=3, macros=base)
            read[name] = gr_of(wet, dry) or 0.0
        print("  %-22s |square - sine| %.3f dB (V3's bar 0.50)"
              % (label, abs(read["square"] - read["sine"])))


def _scale(data, factor):
    view = int16(data)
    for index in range(len(view)):
        view[index] = int(view[index] * factor)
    return view.tobytes()


def _diff(one, other):
    return sum(1 for index in range(min(len(one), len(other)))
               if one[index] != other[index])


CASES = {}
for _name, _value in sorted(list(globals().items())):
    if _name.startswith("case_"):
        CASES[_name[5:]] = _value


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
