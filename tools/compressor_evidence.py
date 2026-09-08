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
from audioeffects.compressor import Compressor

#: `Compressor` has come home to `audioeffects/compressor.py`. This probe
#: names that module so a planted fault is a subclass of the class the
#: traits are about.

#: `_component` reads `VENDOR` off the module a class is *defined* in, and
#: the null-build check (`kit_faults.wire_build`) builds a subclass of the
#: class under test. Without this the subclass refuses to construct, which
#: would be a check that cannot fail.
VENDOR = "PyDevices"

#: The class every render below builds. `using()` swaps it for a subclass -
#: the wire of `kit_faults.null_build_red` - and puts it back.
_SUBJECT = [Compressor]


def subject():
    """The class under test right now."""
    return _SUBJECT[-1]


class using(object):
    """`with using(cls):` - every render inside builds `cls` instead."""

    def __init__(self, cls):
        self.cls = cls

    def __enter__(self):
        _SUBJECT.append(self.cls)
        return self.cls

    def __exit__(self, *exception):
        _SUBJECT.pop()
        return False


import audiofilters

sys.path.insert(0, "tools")

RATE = 48000
CHANNELS = 2
BLOCK = 2048


# -- probes and renders ---------------------------------------------------

def sample(values, rate=RATE, channels=CHANNELS, block=BLOCK,
           loop=False):
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
    adapter.play(raw, loop=loop)
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
    effect = subject().create(source, rate, **options)
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


def _analytic_level(target_db, **options):
    """A first guess at the level that holds `target_db` of GR, from the
    class's own threshold and ratio: above the knee the law is
    `GR = (in - threshold) * (1 - 1/ratio)`. It is only a seed - the FET's
    threshold tilt, the knee and the second stage all move it - but it puts
    the search inside a few dB instead of thirty, which is the difference
    between six renders and twenty-two."""
    source, _ = sample([0.0, 0.0], RATE, CHANNELS)
    effect = build(source, RATE, options.get("patch"),
                   options.get("macros", ()),
                   **{name: value for name, value in options.items()
                      if name not in ("patch", "macros")})
    threshold = effect.macro(1)
    ratio = effect.macro(2)
    effect.deinit()
    slope = 1.0 - 1.0 / max(ratio, 1.0000001)
    if slope <= 1e-6:
        return -12.0
    return min(-0.001, threshold + target_db / slope)


def hold_gr(target_db, hz=200.0, seconds=1.0, low=-60.0, high=0.0,
            rate=RATE, iterations=7, **options):
    """The input level, in dBFS, at which the class settles at `target_db`
    of gain reduction - the level search many rows are stated at.

    Seeded from the analytic level and bracketed +-8 dB around it, so a row
    stated at a gain-reduction depth costs seven renders rather than
    twenty-two. The bracket falls back to the full range if the seed misses.
    """
    seed = _analytic_level(target_db, **options)
    low, high = max(low, seed - 8.0), min(high, seed + 8.0)
    if high - low < 1.0:
        low, high = -60.0, 0.0
    level = seed
    for attempt in range(iterations):
        level = 0.5 * (low + high)
        wet, dry = renders(tone(hz, seconds, 32768.0 * 10 ** (level / 20.0),
                                rate), rate, **options)
        reduction = gr_of(wet, dry) or 0.0
        if abs(reduction - target_db) <= 0.1:
            break
        if attempt == 0 and not (low + 0.1 < level < high - 0.1):
            low, high = -60.0, 0.0
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
    cls = subject()
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
    warm = subject()(quiet_source, sample_rate=rate)
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
        import audioeffects.compressor as module
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

    # Ratio 96 is not a fault: 1000**(96/127) is 33.6:1, whose slope is
    # 0.0298 dB/dB and still inside V4's 0.05 bar. The fault has to put the
    # ratio *below* 20:1, which is where 0.05 dB/dB sits, so it is 50.
    print("CURVE (V4) - Ratio backed off below 20:1")
    levels = list(range(-56, 1, 2))
    for label, knob in (("clean (127)", 127), ("faulted (50)", 50)):
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


# -- the pattern revision's two checks, and this class's own faults -------
#
# `docs/effects-phase2-pattern-revision.md` sections 1.2 and 1.3, and the
# gate audit's G3 ruling on this class: F2's fault was never run, O1's was
# inert, and M5's was "as F5", which is a knob position. All three are
# re-recorded below, each through `kit_faults`.


class _Spy(object):
    """A recording wrapper around a write-only `audiodynamics.Dynamics`.

    The node's Python surface is `set()` and nothing else - `threshold_db`,
    `ratio` and `release_ms` cannot be read back off it (measured: the
    object carries `set`, `play`, `gain_reduction_db` and an opaque
    `_state`). `kit_faults.fault_reachability` wants *the state the fault
    forces, in terms the class's own surface can be asked about*, so this
    records what the class pushes. A copy of `_push_gain_computer`'s
    arithmetic here would move with the class and agree with it by
    construction, which is the both-sides-moved-together trap.
    """

    def __init__(self, node):
        self._node = node
        self.pushed = {}

    def set(self, **options):
        self.pushed.update(options)
        return self._node.set(**options)

    def __getattr__(self, name):
        return getattr(self._node, name)


def spied(effect):
    """`effect` with both `Dynamics` nodes recording what is pushed to them,
    every macro re-applied once so the record starts full."""
    effect._fast = _Spy(effect._fast)
    effect._slow = _Spy(effect._slow)
    for index in range(len(type(effect).MACRO_LABELS)):
        effect.set_macro(index, effect.get_macro(index))
    return effect


def spied_build(cls, patch=0):
    """`build(cls)` for `kit_faults.fault_reachability`: a live instance on
    a silent source, its two nodes spied."""
    source, _ = sample([0.0] * 512)
    with using(cls):
        return spied(build(source, patch=patch))


def _module():
    import audioeffects.compressor as module
    return module


def pushed_slow_ratio(effect):
    """The ratio the class pushes to the slow stage, at the instance's own
    settings."""
    return round(float(effect._slow.pushed["ratio"]), 6)


def pushed_slow_ratio_on_optical(effect):
    """The same reading with macro 0 pinned to `optical` - the character O1
    is stated on - and restored afterwards.

    Pinning is the row's own scope, and it is what separates the two
    readings below: unpinned, slow ratio 1.0 is two macro moves away (patch
    1 ships `fet` with Memory 0), so `OPTICAL_MEMORY = 0` looks reachable;
    on the character the row is about, no macro position reaches it, because
    `compressor.py:331-333` never reads macro 6 there."""
    before = effect.get_macro(0)
    try:
        effect.set_macro(0, macro_for(0, 1.0))
        return pushed_slow_ratio(effect)
    finally:
        effect.set_macro(0, before)


def pushed_fet_tilt_db(effect):
    """The threshold tilt the FET ratio law applies at 20:1, in dB: the
    pushed threshold minus the Threshold macro, at F2's own operating point
    - `fet`, ratio 20:1, Threshold -36 dB - pinned inside the reading and
    restored afterwards.

    Threshold is pinned because the check found it reachable without it:
    `compressor.py:305-306` clamps the tilted threshold at 0 dB, so at
    Threshold macro 127 the tilt reads 0.000 dB and the fault's own state is
    two knob turns away. That is a bound on F2, recorded in section 1, not a
    licence to widen the reading."""
    keep = [effect.get_macro(0), effect.get_macro(1), effect.get_macro(2)]
    try:
        effect.set_macro(0, macro_for(0, 0.0))          # FET
        effect.set_macro(1, macro_for(1, -36.0))
        effect.set_macro(2, macro_for(2, 20.0))
        return round(float(effect._fast.pushed["threshold_db"])
                     - float(effect.macro(1)), 6)
    finally:
        for index, position in zip((0, 1, 2), keep):
            effect.set_macro(index, position)


def pushed_tilt_here(effect):
    """The same tilt at whatever character and ratio the instance is at -
    the *unpinned* reading, kept because it is the one that shows the
    reachability check firing."""
    return round(float(effect._fast.pushed["threshold_db"])
                 - float(effect.macro(1)), 6)


def pushed_fast_release_ms(effect):
    """What the class pushes as the fast stage's release, in ms. Nothing is
    pinned: the macro spans 5000 ms down to 20 ms, so a calibration fault
    that pushes less than 20 / RELEASE_MEASURED_PER_SET is out of the
    surface's reach and one that pushes more is not."""
    return round(float(effect._fast.pushed["release_ms"]), 6)


def state_under(constant, value, reading, patch=0):
    """What `reading` reads on a build made with module constant `constant`
    set to `value` - the faulted state, for a fault that is a constant
    rather than a subclass (`kit_faults.fault_reachability` takes the state
    directly for exactly this case)."""
    module = _module()
    keep = getattr(module, constant)
    setattr(module, constant, value)
    try:
        effect = spied_build(Compressor, patch)
        try:
            return reading(effect)
        finally:
            effect.deinit()
    finally:
        setattr(module, constant, keep)


# -- the readings the rows are cited on, as kit-shaped results ------------

def clean_reading(patch, macros, hz, bar, target_gr=10.0, seconds=1.5):
    """THD at a *held* gain reduction - the reading F5, V6 and M5 are
    stated on.

    Composite on purpose. THD under a bar is green on a wire, because a
    wire distorts nothing; the reading only tests the class when the class
    is also holding the gain reduction the row names, so the held reduction
    is half the measurement and the null-build check passes because of it.
    """
    level = hold_gr(target_gr, hz=hz, seconds=seconds, patch=patch,
                    macros=macros)
    wet, dry = renders(tone(hz, seconds, 32768.0 * 10 ** (level / 20.0)),
                       patch=patch, macros=macros)
    held = gr_of(wet, dry) or 0.0
    thd = thd_percent(wet, hz)
    red = []
    if abs(held - target_gr) > 1.0:
        red.append("held %.2f dB of gain reduction against the %.2f dB the "
                   "row is stated at" % (held, target_gr))
    if thd > bar:
        red.append("THD %.4f %% against a bar of %.4f %%" % (thd, bar))
    return {"values": {"thd_percent": round(thd, 4),
                       "gr_db": round(held, 3),
                       "level_dbfs": round(level, 3)},
            "passed": not red, "red": red}


def detector_reading(patch, macros, hz, amplitude=8000.0):
    """V3's composite: |square - sine| and |sine - 10 % duty|, both.

    The first clause alone is 0.000 dB on a wire - a wire reduces neither -
    so it cannot fail; the second is 0.000 dB there too and its band starts
    at 5.99, which is what makes the pair red on a null build.
    """
    read = {}
    for name, wave in (("sine", tone(hz, 1.5, amplitude)),
                       ("square", square(hz, 1.5, amplitude / math.sqrt(2))),
                       ("pulse", duty_train(hz, 1.5, amplitude))):
        wet, dry = renders(wave, patch=patch, macros=list(macros))
        read[name] = gr_of(wet, dry) or 0.0
    square_sine = abs(read["square"] - read["sine"])
    sine_pulse = abs(read["sine"] - read["pulse"])
    red = []
    if square_sine > 0.50:
        red.append("|square - sine| %.3f dB against a bar of 0.50"
                   % square_sine)
    if not 5.99 <= sine_pulse <= 7.99:
        red.append("|sine - pulse| %.3f dB outside 5.99-7.99" % sine_pulse)
    return {"values": {"square_sine_db": round(square_sine, 4),
                       "sine_pulse_db": round(sine_pulse, 4),
                       "sine_db": round(read["sine"], 4)},
            "passed": not red, "red": red}


def ratio_law_reading(patch, macros, ratios=(4.0, 8.0, 12.0, 20.0)):
    """F2's reading: the fitted threshold and knee at four ratios, and
    whether the threshold rises and the knee narrows across them."""
    levels = list(range(-56, 1, 2))
    thresholds, knees = [], []
    for ratio in ratios:
        wet_by, dry_by = static_curve(
            levels, patch=patch,
            macros=list(macros) + [(2, macro_for(2, ratio))])
        values = kit.curve(wet_by, dry_by, detector="rms")["values"]
        thresholds.append(values.get("threshold_db"))
        knees.append(values.get("knee_db"))
    red = []
    if any(value is None for value in thresholds + knees):
        red.append("the curve fit returned no threshold or knee")
    else:
        rises = all(thresholds[i] > thresholds[i - 1]
                    for i in range(1, len(thresholds)))
        narrows = all(knees[i] <= knees[i - 1]
                      for i in range(1, len(knees)))
        span = thresholds[-1] - thresholds[0]
        if not rises or span < 1.0:
            red.append("threshold %s does not rise with ratio (span %.3f dB)"
                       % ([round(v, 2) for v in thresholds], span))
        if not narrows or knees[0] - knees[-1] < 1.0:
            red.append("knee %s does not narrow with ratio"
                       % [round(v, 2) for v in knees])
    return {"values": {"thresholds_db": [None if v is None else round(v, 3)
                                         for v in thresholds],
                       "knees_db": [None if v is None else round(v, 3)
                                    for v in knees],
                       "threshold_span_db": (None if thresholds[0] is None
                                             else round(thresholds[-1]
                                                        - thresholds[0], 3))},
            "passed": not red, "red": red}


def release_shape_reading(patch, macros, depth_db=10.0):
    """O1's reading: t50, t95 and their ratio on the optical two-stage
    release. A wire has no gain trace at all, so the reading is red there."""
    wet, dry, release_ms, level = release_pair(depth_db, burst_s=10.0,
                                               quiet_s=12.0, patch=patch,
                                               macros=list(macros))
    trace = kit.gaintrace(wet, dry, hop_ms=2.0,
                          release_from_ms=release_ms)["values"]
    t50 = trace.get("release_t50_ms")
    t95 = trace.get("release_t95_ms")
    red = []
    if t50 is None or t95 is None or not t50 or not t95:
        red.append("no two-stage release to read (t50 %r, t95 %r)"
                   % (t50, t95))
        ratio = None
    else:
        ratio = t95 / t50
        if not 40.0 <= t50 <= 80.0:
            red.append("t50 %.1f ms outside 40-80" % t50)
        if not 500.0 <= t95 <= 5000.0:
            red.append("t95 %.1f ms outside 500-5000" % t95)
        if ratio < 8.0:
            red.append("t95/t50 %.2f under 8" % ratio)
    return {"values": {"t50_ms": t50, "t95_ms": t95,
                       "t95_over_t50": None if ratio is None
                       else round(ratio, 3),
                       "level_dbfs": round(level, 3)},
            "passed": not red, "red": red}


class with_constant(object):
    """`with with_constant("OPTICAL_MEMORY", 0.0):` - a fault that is a
    module constant, put back afterwards. The class file is never edited."""

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __enter__(self):
        module = _module()
        self.keep = getattr(module, self.name)
        setattr(module, self.name, self.value)
        return module

    def __exit__(self, *exception):
        setattr(_module(), self.name, self.keep)
        return False


#: The three faults the gate audit sent back, as (constant, value). Each is
#: a *law* of the class, not a position of its surface: `case_checks` shows
#: `kit_faults.fault_reachability` accepting each one and rejecting a
#: reachable near-miss beside it.
REPLANTED = (
    ("F2", "FET_RATIO_REFERENCE", 1e9),
    ("O1", "OPTICAL_MEMORY", 0.0),
    ("M5", "RELEASE_MEASURED_PER_SET", 100.0),
)


def case_replanted():
    """The three faults the gate audit sent back (G3), each shown red on
    the reading its row is cited on, beside the clean control.

    F2's was never run, O1's was inert (`compressor.py:331-333` forces
    `memory = OPTICAL_MEMORY`, so macro 6 is not the stage), and M5's was
    "as F5" - the Release macro at 127, which is a knob a player turns.
    """
    print("F2 (CURVE) - the FET ratio law disabled: "
          "FET_RATIO_REFERENCE = 1e9")
    macros = [(7, macro_for(7, 12.0)), (1, macro_for(1, -36.0))]
    clean = ratio_law_reading(1, macros)
    with with_constant("FET_RATIO_REFERENCE", 1e9):
        faulted = ratio_law_reading(1, macros)
    for label, result in (("clean  ", clean), ("faulted", faulted)):
        print("  %s threshold %s  knee %s -> %s"
              % (label, result["values"]["thresholds_db"],
                 result["values"]["knees_db"],
                 "green" if result["passed"] else "RED"))
    for line in faulted["red"]:
        print("          %s" % line)

    print("O1 (GAINTRACE) - the optical memory removed: "
          "OPTICAL_MEMORY = 0.0")
    clean = release_shape_reading(0, [])
    with with_constant("OPTICAL_MEMORY", 0.0):
        faulted = release_shape_reading(0, [])
    for label, result in (("clean  ", clean), ("faulted", faulted)):
        values = result["values"]
        print("  %s t50 %s ms  t95 %s ms  t95/t50 %s -> %s"
              % (label, _ms(values["t50_ms"]), _ms(values["t95_ms"]),
                 values["t95_over_t50"],
                 "green" if result["passed"] else "RED"))
    for line in faulted["red"]:
        print("          %s" % line)

    print("M5 (SPECTRUM) - the release calibration removed: "
          "RELEASE_MEASURED_PER_SET = 100 (the node is then given a release "
          "126x faster than the knob asks, which no knob position reaches)")
    for label, constant in (("clean  ", None),
                            ("faulted", 100.0)):
        row = []
        for patch in range(8, 14):
            if constant is None:
                result = clean_reading(patch, [], 50.0, 1.0)
            else:
                with with_constant("RELEASE_MEASURED_PER_SET", constant):
                    result = clean_reading(patch, [], 50.0, 1.0)
            row.append("%.4f" % result["values"]["thd_percent"])
        print("  %s TC1-TC6 THD at 10 dB of GR, 50 Hz: %s %%  (bar 1 %%) -> "
              "%s" % (label, " / ".join(row),
                      "green" if constant is None else "RED"))


def case_checks():
    """The pattern revision's two checks, run on this class's own readings
    and its own faults - and shown firing, on a reachable near-miss and on
    an inert one, so neither is a check that only ever agrees."""
    sys.path.insert(0, "tests/support")
    import kit_faults as faults

    print("NULL-BUILD RED (revision 1.2) - each reading, on the class built "
          "as a wire")
    checks = (
        ("F5/V6 - THD at a held 10 dB of GR",
         lambda cls: _with(cls, clean_reading, 1, [(4, 0)], 50.0, 0.5)),
        ("V3 - |square-sine| and |sine-pulse|",
         lambda cls: _with(cls, detector_reading, 3,
                           [(2, 127), (7, 0), (1, macro_for(1, -30.0))],
                           200.0)),
        ("O1 - the two-stage release",
         lambda cls: _with(cls, release_shape_reading, 0, [])),
    )
    for label, measure in checks:
        try:
            result = faults.null_build_red(Compressor, measure, label=label)
        except (faults.NullBuildGreen, faults.ControlRed) as exc:
            print("  %-38s FAILED: %s" % (label, exc))
            continue
        print("  %-38s wire RED (%s); class green"
              % (label, "; ".join(result["null"]["red"])[:96]))

    print("FAULT-REACHABILITY (revision 1.3) - each replanted fault, and a "
          "near-miss beside it")
    o1_target = state_under("OPTICAL_MEMORY", 0.0,
                            pushed_slow_ratio_on_optical)
    checked = faults.fault_reachability(
        Compressor, o1_target, pushed_slow_ratio_on_optical, spied_build,
        label="O1 - OPTICAL_MEMORY = 0")
    print("  O1  fault reads slow ratio %s on `optical` against the clean "
          "%s; %d macro positions and patches walked, none reaches it"
          % (checked["target"], checked["clean"], checked["checked"]))
    try:
        faults.fault_reachability(
            Compressor, state_under("OPTICAL_MEMORY", 0.0,
                                    pushed_slow_ratio),
            pushed_slow_ratio, spied_build,
            label="O1 - the same fault, read off whatever character is set")
    except faults.FaultReachable as exc:
        print("  O1  the check fires on the near-miss: %s" % exc)

    f2_target = state_under("FET_RATIO_REFERENCE", 1e9, pushed_fet_tilt_db)
    checked = faults.fault_reachability(
        Compressor, f2_target, pushed_fet_tilt_db, spied_build,
        label="F2 - FET_RATIO_REFERENCE = 1e9")
    print("  F2  fault reads a %s dB tilt at `fet` 20:1 against the clean "
          "%s dB; %d positions walked, none reaches it"
          % (checked["target"], checked["clean"], checked["checked"]))
    try:
        faults.fault_reachability(
            Compressor, state_under("FET_RATIO_REFERENCE", 1e9,
                                    pushed_tilt_here),
            pushed_tilt_here, spied_build,
            label="F2 - the same fault, read at whatever ratio is set")
    except (faults.FaultInert, faults.FaultReachable) as exc:
        print("  F2  the check fires on the near-miss: %s" % exc)

    m5_target = state_under("RELEASE_MEASURED_PER_SET", 100.0,
                            pushed_fast_release_ms)
    checked = faults.fault_reachability(
        Compressor, m5_target, pushed_fast_release_ms, spied_build,
        label="M5 - RELEASE_MEASURED_PER_SET = 100")
    print("  M5  fault pushes %s ms of release against the clean %s ms; "
          "%d positions walked, the surface's own floor is 20/0.795 = "
          "25.157 ms" % (checked["target"], checked["clean"],
                         checked["checked"]))
    instance = spied_build(Compressor)
    try:
        instance.program_change(1)
        near = pushed_fast_release_ms(instance)
    finally:
        instance.deinit()
    try:
        faults.fault_reachability(
            Compressor, near, pushed_fast_release_ms, spied_build,
            label="M5 - a 'fault' that only pushes what patch 1 asks")
    except faults.FaultReachable as exc:
        print("  M5  the check fires on the near-miss: %s" % exc)


def _with(cls, reading, *arguments):
    with using(cls):
        return reading(*arguments)


# -- the sweep driver: the span each row quantifies over -------------------

def _run_sweep(patch, spans, measure_at, figure, bar, name,
               worst="max"):
    """`kit.macro_sweep` on a fresh instance at `patch`, printed one line per
    cell and one for the worst."""
    source, _ = sample([0.0] * 512)
    instance = build(source, patch=patch)
    try:
        result = kit.macro_sweep(instance, spans, measure_at, figure=figure,
                                 worst=worst, bar=bar, name=name)
    finally:
        instance.deinit()
    values = result["values"]
    for cell in values["cells"]:
        print("    %-34s %10.4f%s"
              % (", ".join("%s %.4g" % (label, unit)
                           for label, unit in sorted(cell["units"].items())),
                 cell["figure"], "   (a stop)" if cell["at_a_stop"] else ""))
    print("  worst %.4f at %s, bar %.4f -> %s"
          % (values["worst"],
             ", ".join("%s %.4g" % (label, unit)
                       for label, unit in sorted(values["at_units"].items())),
             bar, "green" if result["passed"] else "RED"))
    return result


def case_sweeps():
    """Every row that was measured at a point, re-measured over the span it
    quantifies over (`kit.macro_sweep`), worst cell reported.

    The spans are the evidence table's *Quantified over* column: F5 and V6
    quantify over the Release macro's whole travel, V3 over the RMS Window
    macro's, O1 over the Threshold macro's. The probe tone is *held fixed*
    per row and named, because it is not a macro and the sweep cannot walk
    it.
    """
    for patch, hz, bar, label in ((1, 50.0, 0.5, "F5 patch 1 Fast Peak Catch"),
                                  (5, 50.0, 0.5, "F5 patch 5 Let The Stick "
                                                 "Through"),
                                  (1, 1000.0, 0.5, "F5 patch 1, 1 kHz"),
                                  (3, 1000.0, 0.2, "V6 patch 3 Bus Glue"),
                                  (3, 50.0, 0.2, "V6 patch 3, 50 Hz")):
        print("%s - THD %% at 10 dB of GR over Release 0-127, %g Hz held"
              % (label, hz))
        _sweep(patch, [kit.MacroSpan(4, 0, 127, midpoints=3)],
               lambda settings, patch=patch, hz=hz, bar=bar:
               clean_reading(patch, list(settings.items()), hz, bar),
               "thd_percent", bar, "SWEEP(clean)")

    print("V3 patch 3 Bus Glue - |square - sine| dB over RMS Window 0-127, "
          "50 Hz held")
    base = [(2, 127), (7, 0), (1, macro_for(1, -30.0))]
    _run_sweep(3, [kit.MacroSpan(9, 0, 127, midpoints=3)],
           lambda settings: detector_reading(
               3, base + list(settings.items()), 50.0),
           "square_sine_db", 0.50, "SWEEP(V3)")

    print("V3 patch 3 - the same reading against probe frequency, which is "
          "not a macro: the 0.50 dB bar's floor")
    for hz in (40.0, 50.0, 63.0, 80.0, 100.0, 200.0, 400.0):
        result = detector_reading(3, base, hz)
        print("    %6.1f Hz   |sq-sn| %6.3f dB   |sn-pl| %6.3f dB   %s"
              % (hz, result["values"]["square_sine_db"],
                 result["values"]["sine_pulse_db"],
                 "green" if result["passed"] else "RED"))

    print("O1 patch 0 Level Ride - how far t95/t50 falls short of 8 over "
          "Threshold -44.9..-19.8 dB. The span stops at macro 85 because "
          "above it 10 dB of gain reduction is not reachable at 0 dBFS, and "
          "at macro 32 because below it the probe's own post-burst floor "
          "(40 dB under a level the search puts at -49.5 dBFS) is one LSB "
          "and there is no trace to read. Both stops are the measurement's, "
          "not the class's.")
    _run_sweep(0, [kit.MacroSpan(1, 32, 85, midpoints=1)],
           lambda settings: release_shape_reading(0, list(settings.items())),
           lambda result: max(0.0, 8.0 - (result["values"]["t95_over_t50"]
                                          or 0.0)),
           0.0, "SWEEP(O1)")


def case_patches():
    """The patch sweep, first, as the revised template asks: every shipped
    patch read back off the instance, and the reading F5, V6 and M5 are all
    stated on run at those settings.

    A shipped patch is a setting the class's author chose and published, so
    a trait the class misses there is not a corner case - it is the product.
    """
    source, _ = sample([0.0] * 512)
    instance = build(source)
    print("  patch  name                    character  thr dB  ratio   "
          "atk ms   rel ms   THD @50 Hz  THD @1 kHz")
    try:
        for patch in sorted(type(instance).PATCHES):
            instance.program_change(patch)
            name = type(instance).PATCHES[patch][0]
            character = ("fet", "optical", "vca",
                         "varimu")[int(round(instance.macro(0)))]
            low = clean_reading(patch, [], 50.0, 0.5)
            high = clean_reading(patch, [], 1000.0, 0.5)
            print("  %5d  %-22s  %-9s %6.1f %6.1f %8.3f %8.1f   %8.4f %% "
                  "%8.4f %%"
                  % (patch, name, character, instance.macro(1),
                     instance.macro(2), instance.macro(3), instance.macro(4),
                     low["values"]["thd_percent"],
                     high["values"]["thd_percent"]))
    finally:
        instance.deinit()
    print("  bars: F5 and M5 0.5 %% and 1 %%; V6 0.2 %%. Each cell holds "
          "10 dB of gain reduction, found by the level search.")


# -- Tier 1's two open rows, on every interpreter -------------------------

def _alloc_mode():
    import gc
    return "gc" if hasattr(gc, "mem_alloc") else "tracemalloc"


def _alloc_now(mode):
    import gc
    if mode == "gc":
        gc.collect()
        return gc.mem_alloc()
    import tracemalloc
    gc.collect()
    return tracemalloc.get_traced_memory()[0]


def _alloc_over(node, pulls, mode):
    """Bytes the heap grew over `pulls` single-block pulls, each dropped,
    and how many of them carried audio. `effect_measurements.state()`'s
    method without its numpy: a class that allocates nothing because
    nothing was pulled is flat too, so the heard count travels with it."""
    for _ in range(2):                       # warm, and dropped
        audiocore.get_buffer(node)
    before = _alloc_now(mode)
    heard = 0
    for _ in range(pulls):
        _result, block = audiocore.get_buffer(node)
        for offset in range(0, min(len(block), 32)):
            if block[offset]:
                heard += 1
                break
    return _alloc_now(mode) - before, heard


def case_alloc():
    """Tier 1's *no-allocation* row, which every earlier run left
    `unmeasured` because `effect_measurements.state()` needs numpy.

    Same method, no numpy: 200 single-block pulls, each dropped, after a
    warm-up, read with `tracemalloc` on CPython and `gc.mem_alloc()` on the
    two native builds. The bare probe is pulled the same way beside it,
    because what the harness allocates per pull is not this class's - the
    marginal is the row. Bar: the kit's own 8192 bytes.
    """
    mode = _alloc_mode()
    if mode == "tracemalloc":
        import tracemalloc
        tracemalloc.start()
    print("  reading by %s, 200 single-block pulls each, bar 8192 bytes"
          % mode)
    print("   rate    ch    class B   bare B   marginal B   blocks heard   ")
    for rate in (48000, 44100, 22050):
        for channels in (2, 1):
            probe = tone(220.0, 0.25, 9000.0, rate)
            source, _ = sample(probe, rate, channels, loop=True)
            effect = build(source, rate)
            grown, heard = _alloc_over(effect.output, 200, mode)
            effect.deinit()
            bare_source, _ = sample(probe, rate, channels, loop=True)
            bare, _ = _alloc_over(bare_source, 200, mode)
            marginal = grown - bare
            print("  %6d %5d %10d %8d %12d %8d/200   %s"
                  % (rate, channels, grown, bare, marginal, heard,
                     "pass" if (marginal <= 8192 and heard) else "FAIL"))
    if mode == "tracemalloc":
        import tracemalloc
        tracemalloc.stop()


def case_deinit():
    """Tier 1's `deinit()` row, on every interpreter.

    The row read `n/a` on the two native builds because the probe read
    `node._deinited`, which is the CPython shim's attribute and nothing
    else's. What is measurable everywhere is the *call*: the walk at
    `effect._deinits` is instrumented here, so a node the class forgot
    shows up as a missing call rather than as a missing attribute. The
    memory the release gives back is read beside it where the interpreter
    can report it.

    Use-after-deinit is deliberately not probed here: on both native builds
    a deinitialised `audiomixer.Mixer` renders on and then dumps core.
    `tools/compressor_deinit_use.py` is that probe, one node per process.
    """
    mode = _alloc_mode()
    source, _ = sample(tone(220.0, 0.25, 9000.0), loop=True)
    effect = build(source)
    pcm(effect.output, 4096)
    nodes = list(effect._nodes)
    names = [type(node).__name__ for node in nodes]
    owned = [effect._deinits[index] is not False
             for index in range(len(nodes))]
    received = []
    for index in range(len(nodes)):
        release = effect._deinits[index]
        if release is False:
            continue
        if release is True:
            release = getattr(nodes[index], "deinit", None)

        def record(index=index, release=release):
            received.append(index)
            if release is not None:
                release()
        effect._deinits[index] = record
    before = _alloc_now(mode)
    effect.deinit()
    freed = before - _alloc_now(mode)
    print("  node                 owned for deinit   received the call   "
          "_deinited")
    for index, name in enumerate(names):
        flag = getattr(nodes[index], "_deinited", None)
        print("  %d %-18s %-18s %-19s %s"
              % (index, name, "yes" if owned[index] else "no (no deinit)",
                 "yes" if index in received else "no",
                 "n/a" if flag is None else flag))
    print("  %d of %d nodes owned, %d of %d calls received"
          % (sum(owned), len(nodes), len(received), sum(owned)))
    print("  heap released by deinit(): %d bytes (%s)" % (freed, mode))
    still = True
    try:
        effect.output
        still = False
    except Exception as exception:
        message = "%s" % (exception,)
    print("  the class after deinit(): %s"
          % (("output refused - %s" % message) if still
             else "output still answers - FAIL"))


def case_workpatch():
    """The gain reduction each digest in section 3 was taken at.

    Section 3's digests are a check on the class's audio only if the class
    was working when they were taken. This is the same probes and the same
    patches, with the settled gain reduction beside each digest, computed
    without numpy so the two native builds report it too. A cell at 0.0 dB
    is the bare probe with a graph around it, which is what the board leg
    has to avoid measuring.
    """
    print("  probe        rate   patch   fnv1a      wet dBFS   dry dBFS   "
          "GR dB")
    for name, wave_of in (("chord", _chord), ("noise_det", _noise),
                          ("sweep_log", _sweep)):
        for rate in (48000, 44100):
            for patch in (0, 3, 13):
                wave = wave_of(rate)
                wet = render_pcm(wave, rate, CHANNELS, patch=patch)
                dry = dry_pcm(wave, rate, CHANNELS)
                wet_db = _rms_dbfs(wet)
                dry_db = _rms_dbfs(dry)
                print("  %-11s %6d %5d   %08x %9.3f %10.3f %7.3f"
                      % (name, rate, patch, fnv1a(wet), wet_db, dry_db,
                         dry_db - wet_db))


def _rms_dbfs(data, channels=CHANNELS, channel=0):
    """RMS in dBFS over one channel, in pure Python, so the two native
    builds can read a gain reduction without numpy."""
    view = int16(data)
    total, count = 0.0, 0
    for index in range(channel, len(view), channels):
        value = view[index] / 32768.0
        total += value * value
        count += 1
    if not count or total <= 0.0:
        return -999.0
    return 10.0 * math.log10(total / count)


# -- Tier 3: what a patch can and cannot buy ------------------------------

#: The configurations `case_cost` times, as (label, patch, macros). The lean
#: candidates are the cheapest states the *surface* can reach: the peak
#: detector instead of the true-RMS one, the side-chain filter off, and the
#: slow stage at `ratio=1`. None of them removes a node, because a patch
#: cannot: the graph is fixed at construction.
COST_CONFIGURATIONS = (
    ("patch 0 Level Ride (the board run's state)", 0, ()),
    ("patch 3 Bus Glue (RMS detector, working)", 3, ()),
    ("patch 3 + peak detector", 3, ((8, 0),)),
    ("patch 3 + peak detector, emphasis off, memory 0", 3,
     ((8, 0), (10, 0), (6, 0))),
    ("patch 1 Fast Peak Catch (peak detector)", 1, ()),
    ("patch 13 Vari-Mu TC6 (the deepest of the three digest patches)", 13,
     ()),
    ("patch 3 at Mix 0 (the graph with the class defeated)", 3, ((13, 0),)),
)


def _cost_builder(patch, macros):
    def build_it(probe):
        import measure_effect_cost as cost
        effect = subject().create(probe.output, cost.SAMPLE_RATE)
        if patch is not None:
            effect.program_change(patch)
        for index, value in macros:
            effect.set_macro(index, value)
        return effect.output, (), (effect,)
    return build_it


def _cost_render(patch, macros, blocks=128):
    """The runner's own probe through the class at those settings, and the
    same probe raw, so a gain reduction can be read off the pair."""
    import measure_effect_cost as cost
    probe = cost.Probe()
    effect = subject().create(probe.output, cost.SAMPLE_RATE)
    if patch is not None:
        effect.program_change(patch)
    for index, value in macros:
        effect.set_macro(index, value)
    wet = pcm(effect.output, blocks * cost.BLOCK_FRAMES, cost.CHANNELS)
    meter = effect.gain_reduction_db
    effect.deinit()
    bare = cost.Probe()
    dry = pcm(bare.output, blocks * cost.BLOCK_FRAMES, cost.CHANNELS)
    return wet, dry, meter


def case_cost():
    """Tier 3, desktop: what the leanest patch the surface can reach costs
    against the full one, on `tools/measure_effect_cost.py`'s own probe,
    builder and timing loop, so a board run of the same target compares.

    A desktop ms/block is not a board's. What this settles is the *ratio*
    between two configurations of one class, and whether a `" - lean"`
    patch could close a budget the board run missed by 2.6x on the P4.
    """
    import measure_effect_cost as cost
    keep = cost.MIN_WALL_S
    cost.MIN_WALL_S = 4.0
    print("  %d Hz, %d ch, %d-frame blocks; %.3f ms/block is real time; "
          "%.1f s of timing per run"
          % (cost.SAMPLE_RATE, cost.CHANNELS, cost.BLOCK_FRAMES,
             cost.BLOCK_SECONDS * 1000.0, cost.MIN_WALL_S))
    print("  the control is re-run *beside* each configuration, three times "
          "each, best of three: a desktop's ms/block drifts by more between "
          "the first row and the last than the rows differ by.")
    cost.prime(_cost_builder(0, ()))
    print("")
    print("  %-46s %8s %8s %9s %8s %7s %7s %s"
          % ("configuration", "ms/blk", "control", "marginal", "vs full",
             "meter", "level", "digest"))
    full = None
    try:
        for label, patch, macros in COST_CONFIGURATIONS:
            targets, controls = [], []
            for _ in range(3):
                controls.append(cost.run(cost._source, False)["ms_per_block"])
                targets.append(cost.run(_cost_builder(patch, macros), True))
            best = min(run["ms_per_block"] for run in targets)
            spread = max(run["ms_per_block"] for run in targets) - best
            control = min(controls)
            marginal = best - control
            if full is None:
                full = marginal
            wet, dry, meter = _cost_render(patch, macros)
            level = _rms_dbfs(dry) - _rms_dbfs(wet)
            print("  %-46s %8.4f %8.4f %9.4f %7.1f%% %7.2f %7.2f %s"
                  % (label, best, control, marginal,
                     100.0 * marginal / full, meter, level,
                     targets[0]["digest"]))
            print("      (best of three; target spread %.4f ms, control "
                  "spread %.4f)"
                  % (spread, max(controls) - control))
    finally:
        cost.MIN_WALL_S = keep
    print("  `meter` is the class's own `gain_reduction_db` on the last "
          "block, both stages summed; `level` is dry RMS minus wet RMS over "
          "128 blocks, which carries the Makeup macro as well. A row whose "
          "digest is the source's `4169efd90ecf44dd` is a wire, whatever "
          "its ms/block says.")


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
