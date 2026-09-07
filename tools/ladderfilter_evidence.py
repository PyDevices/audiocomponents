"""Every number in `docs/effects/LadderFilter-evidence.md`, from a run.

    audiocomponents/.venv/bin/python tools/ladderfilter_evidence.py <part>

parts: `tier1` `t1` `t2` `t3` `t4` `t5` `faults` `digests` `all`

CPython with numpy, per the kit spec's section 1 rule -- the render is
dual-runtime, the analysis is not. The cross-interpreter legs shell out to
`tools/render_effect.py` under `cmods/bin/micropython` and
`cmods/bin/circuitpython-effects` and analyse the WAVs here.

Every measurement is `tools/effect_measurements.py`'s, called by its own
name, and every one of them is followed by a **planted fault of the same
kind** applied to the same numbers -- the fault battery is `faults`, and a
fault that does not turn its measurement red is reported as such rather than
quietly dropped.
"""

import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (ROOT, os.path.join(ROOT, "lib")):
    if path not in sys.path:
        sys.path.insert(0, path)

import numpy as np                                            # noqa: E402

import audiocore                                              # noqa: E402
import audioeffects                                           # noqa: E402
from tools import effect_measurements as M                    # noqa: E402
from tools import render_effect as R                           # noqa: E402

CLASS = "LadderFilter"
VENV = sys.executable
MP = os.path.join(ROOT, "..", "cmods", "bin", "micropython")
CPY = os.path.join(ROOT, "..", "cmods", "bin", "circuitpython-effects")
OUT = os.environ.get("LADDER_OUT", "/tmp/ladderfilter-evidence")


# --------------------------------------------------------------------------
# In-process rendering: a generated source, through the kit's own block
# adapter, into the class, pulled block by block.
# --------------------------------------------------------------------------

def pcm(frames_iterable, channels):
    import array
    data = array.array("h")
    for frame in frames_iterable:
        for _ in range(channels):
            data.append(frame)
    return data


def tone(hz, seconds, rate, channels=2, dbfs=-14.0, phase=0.0):
    amplitude = 32767.0 * (10.0 ** (dbfs / 20.0))
    count = int(seconds * rate)
    step = 2.0 * math.pi * hz / rate
    return pcm((int(round(amplitude * math.sin(phase + step * n)))
                for n in range(count)), channels)


def impulse(seconds, rate, channels=2, amplitude=32767):
    count = int(seconds * rate)
    return pcm((amplitude if n == 0 else 0 for n in range(count)), channels)


def silence(seconds, rate, channels=2):
    return pcm((0 for _ in range(int(seconds * rate))), channels)


def render(data, rate, channels=2, block=256, options=None, macros=(),
           patch=None, label=None):
    """Build the class around `data` and pull it dry. Returns a Render."""
    source = audiocore.RawSample(data, sample_rate=rate,
                                 channel_count=channels)
    adapter = R.block_adapter(source, rate, channels, block)
    effect = audioeffects.create(CLASS, adapter, rate, **(options or {}))
    if patch is not None:
        effect.program_change(patch)
    for index, value in macros:
        effect.set_macro(index, value)
    audiocore.reset_buffer(effect.output)
    frames = len(data) // channels
    out = bytearray()
    width = 2 * channels
    while len(out) < frames * width:
        _result, buffer = audiocore.get_buffer(effect.output)
        out += bytes(buffer)
    effect.deinit()
    adapter.deinit()
    return M.Render(bytes(out[:frames * width]), rate, channels, block=block,
                    interpreter="cpython %s" % ".".join(
                        str(v) for v in sys.version_info[:3]),
                    label=label, class_name=CLASS,
                    class_version=audioeffects.LadderFilter.VERSION,
                    latency_samples=audioeffects.LadderFilter.LATENCY_SAMPLES)


def scaled(render_object, factor):
    """The same render with every sample scaled - the shape of the WIRE and
    LEVEL faults, applied to the numbers rather than to the C."""
    data = np.round(render_object.data.astype(np.float64) * factor)
    data = np.clip(data, -32768, 32767).astype("<i2")
    return M.Render(data.tobytes(), render_object.rate,
                    render_object.channels, block=render_object.block,
                    interpreter=render_object.interpreter,
                    label=(render_object.label or "") + " [FAULTED]")


def with_even_order(render_object, amount):
    """y + amount*y^2 - an even nonlinearity, T4(b)'s own negation."""
    x = render_object.float
    y = x + amount * x * x
    data = np.clip(np.round(y * 32768.0), -32768, 32767).astype("<i2")
    return M.Render(data.tobytes(), render_object.rate,
                    render_object.channels, block=render_object.block,
                    interpreter=render_object.interpreter,
                    label=(render_object.label or "") + " [FAULTED even]")


def with_dc(render_object, lsb, from_frame):
    data = render_object.data.astype(np.int32).copy()
    data[from_frame:] += int(lsb)
    data = np.clip(data, -32768, 32767).astype("<i2")
    return M.Render(data.tobytes(), render_object.rate,
                    render_object.channels, block=render_object.block,
                    interpreter=render_object.interpreter,
                    label=(render_object.label or "") + " [FAULTED dc]")


def show(name, result):
    mark = "green" if result["passed"] else "RED"
    print("  %-9s %-5s %s" % (name, mark,
                              "; ".join(result["red"]) or "-"))
    return result


# --------------------------------------------------------------------------
# The macro grid, in the class's own units
# --------------------------------------------------------------------------

SPANS = audioeffects.LadderFilter._MACRO_RANGES
CUTOFF, RESONANCE, DRIVE, COMP, POLES, OVERSAMPLE, MIX = range(7)


def at(**settings):
    """Macro moves in engineering units -> (index, 0..127) pairs."""
    order = {"cutoff": CUTOFF, "resonance": RESONANCE, "drive": DRIVE,
             "comp": COMP, "poles": POLES, "oversample": OVERSAMPLE,
             "mix": MIX}
    moves = []
    for name in ("cutoff", "resonance", "drive", "comp", "poles",
                 "oversample", "mix"):
        if name in settings:
            index = order[name]
            moves.append((index, 127.0 * M_position(SPANS[index],
                                                    settings[name])))
    return moves


def M_position(span, value):
    from audioeffects import _component
    return _component.macro_position(span, value)


# --------------------------------------------------------------------------
# Tier 2
# --------------------------------------------------------------------------

#: 50 Hz is on the grid so the passband reference is a real reading and not
#: an extrapolation: at 0.05*f_c the ideal fourth-order response is already
#: -0.043 dB down, and T1's "-3 dB point" is an ABSOLUTE -3.0103 dB, not
#: three below whatever the lowest tone measured. Both readings are exported
#: - the first run of this file reported only the relative one and put the
#: corner 11 Hz high for that reason alone.
T1_GRID = (50.0, 100.0, 200.0, 300.0, 400.0, 435.0, 500.0, 600.0, 800.0,
           1000.0, 1500.0, 2000.0, 3000.0, 4000.0, 6000.0, 8000.0)


def tone_pair(hz, rate, seconds=0.75, dbfs=-20.0, channels=2, **settings):
    data = tone(hz, seconds, rate, channels, dbfs)
    wet = render(data, rate, channels, macros=at(**settings),
                 label="%g Hz wet" % hz)
    dry = render(data, rate, channels,
                 macros=at(mix=0.0), label="%g Hz dry" % hz)
    return wet, dry


def t1(rate=48000, cutoff=1000.0, built_cutoff=None, quiet=False):
    """`cutoff` is the trait's reference - the grid and every bar are stated
    against it. `built_cutoff` is what the class is actually set to, and is
    the same thing unless a fault is being planted."""
    built = cutoff if built_cutoff is None else built_cutoff
    wet, dry = {}, {}
    for hz in T1_GRID:
        if hz > rate * 0.45:
            continue
        w, d = tone_pair(hz, rate, cutoff=built, resonance=0.0, drive=0.0,
                         comp=0.0, poles=4.0, oversample=1.0, mix=1.0)
        wet[hz], dry[hz] = w, d
    result = M.response(wet, dry, reference_hz=0.05 * cutoff,
                        corner_db=-3.0, slope_octave=(4000.0, 8000.0),
                        expected={"slope_db_per_octave": (-25.0, 2.0)})
    level_at_fc = [p["magnitude_db"] for p in result["values"]["grid"]
                   if abs(p["hz"] - cutoff) < 1e-6][0]
    grid_hz = [p["hz"] for p in result["values"]["grid"]]
    grid_db = [p["magnitude_db"] for p in result["values"]["grid"]]
    absolute_corner = M._crossing(grid_hz, grid_db, -3.0103)
    result["values"]["absolute_corner_hz"] = (
        None if absolute_corner is None else round(absolute_corner, 3))
    result["values"]["level_at_cutoff_db"] = round(level_at_fc, 4)
    if abs(level_at_fc + 12.0) > 0.5:
        result["red"].append("level at f_c %+.3f dB (bar -12.0 +- 0.5)"
                             % level_at_fc)
    if absolute_corner is None or abs(absolute_corner - 0.4350 * cutoff) > 20.0:
        result["red"].append("absolute -3.0103 dB point %s against %.1f Hz "
                             "(bar 20)" % (absolute_corner, 0.4350 * cutoff))
    result["passed"] = not result["red"]
    if not quiet:
        print("T1  RESPONSE  %d Hz, cutoff %g Hz, resonance 0" % (rate, cutoff))
        for point in result["values"]["grid"]:
            print("    %8.1f Hz  %+8.3f dB" % (point["hz"],
                                               point["magnitude_db"]))
        print("    level at f_c        %+8.3f dB   (bar -12.0 +- 0.5)"
              % level_at_fc)
        print("    -3 dB corner, absolute  %8.1f Hz   (bar %.1f +- 20)"
              % (result["values"]["absolute_corner_hz"], 0.4350 * cutoff))
        print("    -3 dB corner, re 0.05f_c %7.1f Hz   (exported, not the "
              "trait's number)" % result["values"]["corner_hz"])
        print("    slope 4->8 kHz      %+8.2f dB/octave  (bar -23..-27)"
              % result["values"]["slope_db_per_octave"])
        show("RESPONSE", result)
    return result, level_at_fc


def t2(rate=48000, cutoff=1000.0, ks=(0.0, 1.0, 2.0, 3.0, 4.0), quiet=False):
    """T2 - the level at 0.1*f_c against k, read frequency-selectively."""
    rows = []
    for k in ks:
        wet, dry = {}, {}
        for hz in (0.05 * cutoff, 0.1 * cutoff, 0.2 * cutoff):
            w, d = tone_pair(hz, rate, seconds=1.0, cutoff=cutoff,
                             resonance=k, drive=0.0, comp=0.0, poles=4.0,
                             oversample=1.0, mix=1.0)
            wet[hz], dry[hz] = w, d
        result = M.response(wet, dry, reference_hz=0.1 * cutoff,
                            corner_db=-3.0)
        rows.append((k, result["values"]["passband_db"]))
    expected = {0.0: 0.00, 1.0: -6.02, 2.0: -9.54, 3.0: -12.04, 4.0: -13.98}
    red = []
    for k, value in rows:
        want = expected.get(k)
        if want is not None and abs(value - want) > 0.5:
            red.append("k=%g reads %+.2f dB against %+.2f (bar 0.5)"
                       % (k, value, want))
    if not quiet:
        print("T2  RESPONSE at 0.1*f_c, %d Hz, cutoff %g Hz" % (rate, cutoff))
        for k, value in rows:
            want = expected.get(k)
            print("    k=%-4g  %+8.3f dB   analytic %+7.2f   d %+.3f"
                  % (k, value, want, value - want))
        print("  %-9s %-5s %s" % ("T2", "green" if not red else "RED",
                                  "; ".join(red) or "-"))
    return rows, red


def _dominant_hz(x, rate):
    magnitudes, bin_hz, _window, _length = M.magnitude_spectrum(x, rate)
    index = int(np.argmax(magnitudes[1:])) + 1
    return M._parabola(magnitudes, index) * bin_hz


def t3(rate=48000, cutoff=1000.0, top_position=127.0, quiet=False):
    """T3 - one impulse, three seconds of silence, at the top of Resonance
    travel and at 90 % of it.

    The two positions are read differently because the trait states them
    differently, and reading both the same way is what the first run of this
    function got wrong. At the top of travel the subject is a tone that is
    still there, so the reading is one settled window against a later
    settled window (0.9-1.0 s against 2.9-3.0 s). At 90 % the subject is an
    absence, so the reading is the last second against the render's own
    peak - which is the impulse response, and is gone inside a few
    milliseconds. Comparing two windows that are both on the noise floor
    reports "0.0 dB of decay" and is not a measurement.
    """
    data = impulse(3.0, rate, 2, 32767)
    rows = []
    for label, position in (("top of travel", top_position),
                            ("90 % of travel", 0.9 * top_position)):
        out = render(data, rate, 2,
                     macros=at(cutoff=cutoff, drive=0.0, comp=0.0,
                               poles=4.0, oversample=1.0, mix=1.0)
                     + [(RESONANCE, position)],
                     label="impulse @ %s" % label)
        left = out.float[:, 0]
        peak_db = M.db(float(np.abs(left).max()))
        early_db = M.db(float(np.abs(left[int(0.9 * rate):
                                          int(1.0 * rate)]).max()))
        late_db = M.db(float(np.abs(left[int(2.9 * rate):
                                         int(3.0 * rate)]).max()))
        last_second_db = M.db(float(np.abs(left[int(2.0 * rate):]).max()))
        segment = left[int(1.0 * rate):int(3.0 * rate)]
        hz = (_dominant_hz(segment, rate)
              if float(np.abs(segment).max()) > 1e-6 else None)
        rows.append({"label": label, "position": position,
                     "peak_db": peak_db, "early_db": early_db,
                     "late_db": late_db, "decay_db": late_db - early_db,
                     "last_second_db": last_second_db,
                     "below_peak_db": last_second_db - peak_db, "hz": hz})
    red = []
    top, ninety = rows[0], rows[1]
    if top["hz"] is None:
        red.append("nothing sustains at the top of travel")
    elif abs(top["hz"] - cutoff) / cutoff > 0.03:
        red.append("top of travel oscillates at %.1f Hz against a %g Hz "
                   "cutoff (%.2f %% out, bar 3 %%)"
                   % (top["hz"], cutoff,
                      abs(top["hz"] - cutoff) / cutoff * 100))
    if top["decay_db"] < -3.0:
        red.append("top of travel decays %.2f dB over 2 s (bar 3 dB)"
                   % -top["decay_db"])
    if ninety["below_peak_db"] > -40.0:
        red.append("90 %% of travel is only %.1f dB below its own peak in "
                   "the last second (bar 40)" % -ninety["below_peak_db"])
    if not quiet:
        print("T3  impulse then 3 s of silence, %d Hz, cutoff %g Hz"
              % (rate, cutoff))
        for row in rows:
            print("    %-16s macro %5.1f  render peak %+8.2f dBFS  "
                  "0.9-1.0 s %+8.2f  2.9-3.0 s %+8.2f  decay %+7.2f dB  "
                  "last second %+8.2f (%+7.2f dB re peak)  tone %s"
                  % (row["label"], row["position"], row["peak_db"],
                     row["early_db"], row["late_db"], row["decay_db"],
                     row["last_second_db"], row["below_peak_db"],
                     "-" if row["hz"] is None else "%.2f Hz" % row["hz"]))
        print("  %-9s %-5s %s" % ("T3", "green" if not red else "RED",
                                  "; ".join(red) or "-"))
    return rows, red


def t4(rate=48000, cutoff=1000.0, quiet=False):
    """T4 - bounded, odd, and in the loop."""
    print("T4  the nonlinearity, %d Hz, cutoff %g Hz" % (rate, cutoff))
    red = []

    # (a) and (b) at self-oscillation: an impulse then 3 s of silence, read
    #     over the last two seconds.
    data = impulse(3.0, rate, 2, 32767)
    out = render(data, rate, 2,
                 macros=at(cutoff=cutoff, drive=0.0, comp=0.0, poles=4.0,
                           oversample=1.0, mix=1.0) + [(RESONANCE, 127.0)],
                 label="self-oscillation")
    left = out.float[:, 0]
    tone_hz = _dominant_hz(left[int(1.0 * rate):], rate)
    window = int(0.25 * rate)
    envelope = [M.db(float(np.abs(left[s:s + window]).max()))
                for s in range(int(1.0 * rate), int(3.0 * rate) - window,
                               window)]
    drift = max(envelope) - min(envelope)
    settled = M.Render(
        out.data[int(1.0 * rate):].tobytes(), rate, 2,
        block=out.block, interpreter=out.interpreter, label="settled")
    # Blackman-Harris, not the kit's default exact-bin rectangular window,
    # and the difference is the whole of T4(b). The fundamental here is the
    # FILTER'S OWN frequency - 999.82 Hz, which nobody chose - so
    # exact_bin_size() cannot land it on a bin, and a rectangular window's
    # leakage skirt from a full-scale fundamental reads -74.5 dB at h2.
    # Measured both ways in this run: rectangular h2 -74.49 dB, hann
    # -134.53, blackman-harris -131.11, with h3 within 0.3 dB of each other
    # at -65.9 / -63.1 / -63.4. The -74 dB was leakage, and it is the number
    # that made T4(b)'s "20 dB below h3" clause fail on a correct build.
    spec = M.spectrum(settled, tone_hz, harmonics=8,
                      window="blackmanharris")
    spec_rect = M.spectrum(settled, tone_hz, harmonics=8)
    thd_percent = 100.0 * 10.0 ** (spec["values"]["thd_db"] / 20.0)
    harmonics = spec["values"]["harmonic_db"]
    evens = [harmonics[k] for k in ("h2", "h4", "h6", "h8")
             if harmonics.get(k) is not None]
    h3 = harmonics.get("h3")
    print("    (a) tone %.2f Hz   peak drift %.3f dB over 2 s (bar 1.0)   "
          "THD %.3f %% (bar 15)" % (tone_hz, drift, thd_percent))
    print("    (b) h2 %s dB  h3 %s dB  h4 %s  h5 %s  h6 %s  h7 %s   "
          "[blackman-harris]"
          % (harmonics.get("h2"), h3, harmonics.get("h4"),
             harmonics.get("h5"), harmonics.get("h6"), harmonics.get("h7")))
    print("    (b) the same read with the kit's default exact-bin "
          "rectangular window: h2 %s  h3 %s  -- leakage, see the comment"
          % (spec_rect["values"]["harmonic_db"].get("h2"),
             spec_rect["values"]["harmonic_db"].get("h3")))
    if drift > 1.0:
        red.append("(a) peak drifts %.2f dB over 2 s (bar 1.0)" % drift)
    if thd_percent > 15.0:
        red.append("(a) THD %.2f %% (bar 15)" % thd_percent)
    for name, value in zip(("h2", "h4", "h6", "h8"), evens):
        if value > -40.0:
            red.append("(b) %s at %.1f dB re h1 (bar -40)" % (name, value))
        if h3 is not None and value > h3 - 20.0:
            red.append("(b) %s is %.1f dB below h3 (bar 20)"
                       % (name, h3 - value))

    # (c) a held 1 kHz tone on the resonant peak at k = 3.9, four drives.
    held = tone(cutoff, 1.5, rate, 2, -20.0)
    ladder = []
    for drive_db in (0.0, 8.0, 16.0, 24.0):
        out = render(held, rate, 2,
                     macros=at(cutoff=cutoff, resonance=3.9, drive=drive_db,
                               comp=0.0, poles=4.0, oversample=1.0, mix=1.0),
                     label="drive %+g dB" % drive_db)
        settled = M.Render(out.data[int(0.5 * rate):].tobytes(), rate, 2,
                           block=out.block, interpreter=out.interpreter,
                           label="drive %+g dB settled" % drive_db)
        spec = M.spectrum(settled, cutoff, harmonics=8,
                          window="blackmanharris")
        value = spec["values"]["harmonic_db"]["h3"]
        evens_here = [spec["values"]["harmonic_db"][k]
                      for k in ("h2", "h4", "h6", "h8")
                      if spec["values"]["harmonic_db"].get(k) is not None]
        ladder.append((drive_db, value, max(evens_here)))
        print("    (c) drive %+5.1f dB   h3 %+8.2f dB re h1   worst even "
              "%+8.2f dB" % (drive_db, value, max(evens_here)))
        if max(evens_here) > -40.0:
            red.append("(b) at drive %+g dB the worst even harmonic is "
                       "%.1f dB re h1 (bar -40)" % (drive_db,
                                                    max(evens_here)))
    values = [row[1] for row in ladder]
    monotonic = all(values[i] < values[i + 1] for i in range(len(values) - 1))
    span = values[-1] - values[0]
    print("    (c) monotonic %s   end to end %+.2f dB (bar 10)"
          % (monotonic, span))
    if not monotonic:
        red.append("(c) h3 is not monotonic across Drive: %s"
                   % [round(v, 2) for v in values])
    if span < 10.0:
        red.append("(c) h3 moves %.2f dB end to end (bar 10)" % span)
    print("  %-9s %-5s %s" % ("T4", "green" if not red else "RED",
                              "; ".join(red) or "-"))
    return {"tone_hz": tone_hz, "drift_db": drift, "thd_percent": thd_percent,
            "harmonics": harmonics, "ladder": ladder}, red


T5_GRID = (800.0, 850.0, 875.0, 900.0, 925.0, 950.0, 975.0, 1000.0, 1050.0)


def t5(rate=48000, cutoff=1000.0, quiet=False):
    """T5 - character follows input level, at k = 3.

    The **resonant peak is not at the cutoff** and this measurement reads it
    where it is: at k = 3 the poles put it near 0.93*f_c, and the first run
    of this function read the transfer at f_c instead and reported a smaller
    move than the filter has. So: a grid across the peak, one tone at a
    time, with the peak taken as the grid's maximum.

    Every level carries two controls it would otherwise be read without.
    The **output peak in LSB**, so a reading taken on a clipped render is
    visible rather than inferred - at k = 3 the peak sits +3.5 dB over the
    input and 0 dBFS in is the last level that does not clip. And the
    **wire's own THD at the same level through the same analysis**, so a
    distortion figure that is really the 16-bit render's quantization floor
    cannot be attributed to the filter. Both exist because the first run of
    this function reported 0.93 % THD at -60 dBFS in, which is the floor.
    """
    rows = []
    for dbfs in (-60.0, -40.0, -26.0, -20.0, -14.0, -10.0, -6.0, -3.0, 0.0):
        wet, dry = {}, {}
        for hz in T5_GRID:
            w, d = tone_pair(hz, rate, seconds=1.0, dbfs=dbfs, cutoff=cutoff,
                             resonance=3.0, drive=0.0, comp=0.0, poles=4.0,
                             oversample=1.0, mix=1.0)
            wet[hz], dry[hz] = w, d
        curve = M.response(wet, dry, reference_hz=T5_GRID[0])
        points = [(p["hz"], p["magnitude_db"])
                  for p in curve["values"]["grid"]]
        peak_hz, peak_db = max(points, key=lambda point: point[1])
        loudest = max(int(np.abs(wet[hz].data).max()) for hz in T5_GRID)
        settled = M.Render(wet[peak_hz].data[int(0.5 * rate):].tobytes(),
                           rate, 2)
        wire_settled = M.Render(
            dry[peak_hz].data[int(0.5 * rate):].tobytes(), rate, 2)
        spec = M.spectrum(settled, peak_hz, harmonics=8,
                          window="blackmanharris")
        wire_spec = M.spectrum(wire_settled, peak_hz, harmonics=8,
                               window="blackmanharris")
        rows.append({
            "in_dbfs": dbfs, "peak_hz": peak_hz, "peak_db": peak_db,
            "out_lsb": loudest, "clipped": loudest >= 32760,
            "thd_percent": 100.0 * 10.0 ** (spec["values"]["thd_db"] / 20.0),
            "wire_thd_percent":
                100.0 * 10.0 ** (wire_spec["values"]["thd_db"] / 20.0),
            "h3_db": spec["values"]["harmonic_db"]["h3"]})
    by_level = {row["in_dbfs"]: row for row in rows}
    move = by_level[0.0]["peak_db"] - by_level[-20.0]["peak_db"]
    ladder = [by_level[level]["thd_percent"]
              for level in (-26.0, -20.0, -14.0, -10.0, -6.0, -3.0, 0.0)]
    red = []
    if abs(move) < 3.0:
        red.append("the peak moves %.2f dB across the 20 dB rise from "
                   "-20 to 0 dBFS in (bar 3)" % abs(move))
    if not all(ladder[i] < ladder[i + 1] for i in range(len(ladder) - 1)):
        red.append("THD is not monotonic from -26 to 0 dBFS in: %s"
                   % [round(v, 4) for v in ladder])
    if by_level[-40.0]["thd_percent"] >= 0.5:
        red.append("THD %.4f %% at -40 dBFS in (bar 0.5)"
                   % by_level[-40.0]["thd_percent"])
    if any(row["clipped"] for row in rows):
        red.append("a reading was taken on a clipped render")
    if not quiet:
        print("T5  input level, %d Hz, cutoff %g Hz, k = 3, peak read over "
              "%g-%g Hz" % (rate, cutoff, T5_GRID[0], T5_GRID[-1]))
        for row in rows:
            print("    in %+6.1f dBFS  peak %+7.3f dB @ %6.1f Hz  out %6d "
                  "LSB %-8s THD %8.4f %%  wire THD %8.4f %%  h3 %+8.2f dB"
                  % (row["in_dbfs"], row["peak_db"], row["peak_hz"],
                     row["out_lsb"], "CLIPPED" if row["clipped"] else "",
                     row["thd_percent"], row["wire_thd_percent"],
                     row["h3_db"]))
        print("    peak height moves %+.3f dB across the 20 dB rise "
              "(-20 -> 0 dBFS in): it goes %s as the level rises. The SIGN "
              "is the dossier's Q4, unsourced before this run. (bar 3 dB)"
              % (move, "DOWN" if move < 0 else "UP"))
        print("  %-9s %-5s %s" % ("T5", "green" if not red else "RED",
                                  "; ".join(red) or "-"))
    return rows, red


# --------------------------------------------------------------------------
# Tier 1, in process, on CPython
# --------------------------------------------------------------------------

def probe_pcm(name, rate, channels):
    path = os.path.join(HERE, "effect_probes", "%d" % rate,
                        "%dch" % channels, "%s.wav" % name)
    file_rate, file_channels, _bits, start, length = R.wav_info(path)
    assert file_rate == rate and file_channels == channels, path
    handle = open(path, "rb")
    try:
        handle.seek(start)
        data = handle.read(length)
    finally:
        handle.close()
    return R._pcm_array(data), path


#: The class's unity setting: the filter as far out of the way as its own
#: panel puts it. `_hz()` clamps the cutoff to 0.49*f_s, so this is 18 kHz
#: at 48 and 44.1 kHz and 10.8 kHz at 22.05.
UNITY = dict(cutoff=18000.0, resonance=0.0, drive=0.0, comp=0.0, poles=4.0,
             oversample=1.0, mix=1.0)


def tier1(rate=48000, channels=2, block=2048):
    print("TIER 1  %d Hz  %d ch  block %d  (cpython)" % (rate, channels,
                                                         block))
    results = {}
    cls = audioeffects.LadderFilter

    ramp, _ = probe_pcm("ramp_fs", rate, channels)
    source = M.Render(ramp.tobytes(), rate, channels, label="ramp_fs source")
    wired = render(ramp, rate, channels, block, macros=at(mix=0.0),
                   label="ramp_fs @ mix 0")
    results["WIRE"] = show("WIRE", M.wire(wired, source,
                                          latency_samples=cls.LATENCY_SAMPLES))

    burst, _ = probe_pcm("burst_silence", rate, channels)
    burst_end = int(0.2 * rate)
    tailed = render(burst, rate, channels, block, patch=0,
                    label="burst_silence @ patch 0")
    results["TAIL"] = show("TAIL", M.tail(tailed, burst_end_frame=burst_end,
                                          residual_tolerance_lsb=0))

    # LEVEL on a 100 Hz tone, not on the broadband `noise_det`, and the
    # difference is not a convenience. This class is a LOW-PASS: four poles
    # at 18 kHz take 4.77 dB of RMS off white noise at 48 kHz (measured, on
    # `noise_det`, in the first run of this file), which is the filter doing
    # its job and not hidden gain. LEVEL's subject is "unity through the
    # path", so it is read where the class claims unity - in the passband,
    # at 0.006*f_c, where the ideal fourth-order magnitude is 5e-7 dB down.
    # The broadband figure is exported beside it rather than dropped.
    tone_pcm, _ = probe_pcm("sine_100_-14", rate, channels)
    wet = render(tone_pcm, rate, channels, block, macros=at(**UNITY),
                 label="sine_100 @ unity")
    dry = render(tone_pcm, rate, channels, block, macros=at(mix=0.0),
                 label="sine_100 @ mix 0")
    results["LEVEL"] = show("LEVEL", M.level(wet, dry, tolerance_db=0.05,
                                             skip_frames=int(0.1 * rate)))
    noise, _ = probe_pcm("noise_det", rate, channels)
    noise_wet = render(noise, rate, channels, block, macros=at(**UNITY),
                       label="noise_det @ unity")
    noise_dry = render(noise, rate, channels, block, macros=at(mix=0.0),
                       label="noise_det @ mix 0")
    broadband = M.level(noise_wet, noise_dry, tolerance_db=99.0)
    print("    LEVEL, broadband control on noise_det: %s dB RMS - the "
          "four-pole roll-off, exported so it is not mistaken for gain"
          % broadband["values"]["rms_db"])
    results["LEVEL_broadband"] = broadband

    click_pcm, _ = probe_pcm("click_stereo", rate, channels)
    click_wet = render(click_pcm, rate, channels, block, patch=0,
                       label="click_stereo @ patch 0")
    click_dry = render(click_pcm, rate, channels, block, macros=at(mix=0.0),
                       label="click_stereo @ mix 0")
    # The INTEGER reading is the one `latency_samples` declares, and this
    # row is judged on it. `effect_measurements.click`'s own docstring is
    # the authority: a minimum-phase filter's group delay "is a real
    # property of the class and *not* the processing latency
    # `latency_samples` declares", and "a class whose latency is a pure
    # delay reads the same both ways". This one does not read the same both
    # ways, which is the evidence that what it has is group delay and not
    # latency. The sub-sample figure is exported as that group delay.
    results["CLICK"] = show("CLICK", M.click(click_wet, click_dry,
                                             cls.LATENCY_SAMPLES,
                                             tolerance_samples=1.0,
                                             subsample=False))
    fine = M.click(click_wet, click_dry, cls.LATENCY_SAMPLES,
                   tolerance_samples=1.0)
    print("    CLICK, sub-sample: %s samples (%s ms) - the class's group "
          "delay at patch 0, not its latency"
          % (fine["values"]["measured_latency_samples"],
             fine["values"]["measured_latency_ms"]))
    results["CLICK_subsample"] = fine
    for name, position in (("Oversample off", 0.0), ("Oversample 2x", 127.0)):
        wet_option = render(click_pcm, rate, channels, block, patch=0,
                            macros=[(OVERSAMPLE, position)])
        integer = M.click(wet_option, click_dry, cls.LATENCY_SAMPLES,
                          tolerance_samples=1.0, subsample=False)
        fine_option = M.click(wet_option, click_dry, cls.LATENCY_SAMPLES,
                              tolerance_samples=1.0)
        print("    CLICK, %-14s integer %s  sub-sample %s  -> %s"
              % (name, integer["values"]["measured_latency_samples"],
                 fine_option["values"]["measured_latency_samples"],
                 "green" if integer["passed"] else "RED"))
        results["CLICK_" + name] = integer

    results["STATE"] = show("STATE", state_leg(rate, channels, block))
    print("    reported latency %d samples, tail %s"
          % (cls.LATENCY_SAMPLES, cls.TAIL_SAMPLES))
    return results


class _Holder:
    """The pull/swap seam STATE wants, over one live class instance."""

    def __init__(self, rate, channels, block, options=None):
        self.rate, self.channels, self.block = rate, channels, block
        self.width = 2 * channels
        self.adapter = R.block_adapter(
            audiocore.RawSample(silence(0.1, rate, channels),
                                sample_rate=rate, channel_count=channels),
            rate, channels, block)
        self.effect = audioeffects.create(CLASS, self.adapter, rate,
                                          **(options or {}))

    def swap(self, source):
        self.adapter.play(source, loop=False)
        audiocore.reset_buffer(self.adapter)

    def pull(self, blocks):
        out = bytearray()
        for _ in range(blocks):
            _result, buffer = audiocore.get_buffer(self.effect.output)
            out += bytes(buffer)
        return M.Render(bytes(out), self.rate, self.channels,
                        block=self.block, label="pull")


def state_leg(rate, channels, block, break_reset=False):
    noise, _ = probe_pcm("noise_det", rate, channels)
    holder = _Holder(rate, channels, block)
    if break_reset:
        holder.effect.reset = lambda: None
    probe_source = audiocore.RawSample(noise, sample_rate=rate,
                                       channel_count=channels)
    quiet = audiocore.RawSample(silence(2.0, rate, channels),
                                sample_rate=rate, channel_count=channels)
    holder.swap(probe_source)
    holder.effect.program_change(4)     # Growl With Drive: a charged loop
    return M.state(holder.effect, pull=holder.pull, swap=holder.swap,
                   probe_source=probe_source, silent_source=quiet,
                   blocks=32, alloc_pulls=120)


# --------------------------------------------------------------------------
# Cross-interpreter digests, through the kit's own renderer
# --------------------------------------------------------------------------

#: `-X heapsize=256M` is not optional on CircuitPython and
#: `render_effect.py`'s own docstring says why: its `audiocore.WaveFile`
#: refuses the streams this kit hands it, so the whole probe goes through
#: RawSample and is resident. A 3 s stereo 48 kHz probe is 576 KB and the
#: default heap is smaller than that - the failure is a MemoryError at
#: `render_effect.py:319`, not a wrong digest.
INTERPRETERS = (("cpython", [VENV]),
                ("micropython", [MP]),
                ("circuitpython-effects", [CPY, "-X", "heapsize=256M"]))


def render_out(binary, probe, rate, channels, block, macros=(), patch=None):
    outdir = os.path.join(OUT, os.path.basename(binary[0]))
    os.makedirs(outdir, exist_ok=True)
    argv = list(binary) + [os.path.join(HERE, "render_effect.py"), CLASS,
                           probe, outdir, "--rate", str(rate), "--channels",
                           str(channels), "--block", str(block)]
    if patch is not None:
        argv += ["--patch", str(patch)]
    for index, value in macros:
        argv += ["--macro", "%d=%g" % (index, value)]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.path.join(ROOT, "lib")
    environment["MICROPYPATH"] = "%s:%s" % (
        os.path.join(ROOT, "lib"),
        os.path.join(ROOT, "..", "cmods", "micropython", "lib"))
    done = subprocess.run(argv, cwd=ROOT, env=environment,
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit("%s: %s\n%s" % (argv[0], done.stdout, done.stderr))
    line = done.stdout.strip().split("\n")[0]
    return line.split("fnv ")[1].split()[0]


def digests():
    print("DIGEST  cross-interpreter, through tools/render_effect.py")
    rows = []
    plan = [("chord", 48000, 2, 2048, (), 0),
            ("noise_det", 48000, 2, 2048, (), 0),
            ("sweep_log", 48000, 2, 2048, (), 0),
            ("chord", 44100, 2, 2048, (), 0),
            ("chord", 22050, 2, 2048, (), 0),
            ("chord", 48000, 1, 2048, (), 0),
            ("impulse", 48000, 2, 2048, (), 2),
            ("noise_det", 48000, 2, 256, (), 4)]
    for probe, rate, channels, block, macros, patch in plan:
        values = []
        for name, binary in INTERPRETERS:
            values.append(render_out(binary, probe, rate, channels, block,
                                     macros, patch))
        agree = len(set(values)) == 1
        rows.append((probe, rate, channels, block, patch, values, agree))
        print("    %-10s %5d Hz %dch blk%-5d p%d  %s  %s"
              % (probe, rate, channels, block, patch, "  ".join(values),
                 "identical" if agree else "DIFFER"))
    return rows


# --------------------------------------------------------------------------
# Tier 1 on the other two interpreters: rendered there, analysed here
# --------------------------------------------------------------------------

#: The unity setting on the 0-127 grid, for the command line. macro 5 is
#: Oversample and 127 is 2x, which is the default and what every Tier 2
#: reading here was taken at.
UNITY_MIDI = ((0, 127), (1, 0), (2, 0), (3, 0), (4, 127), (5, 127), (6, 127))
DRY_MIDI = ((6, 0),)


def _wav(binary, probe, rate, channels, block, macros=(), patch=None):
    render_out(binary, probe, rate, channels, block, macros, patch)
    outdir = os.path.join(OUT, os.path.basename(binary[0]))
    stem = "%s__%s__%d__%dch__blk%d" % (CLASS, probe, rate, channels, block)
    if patch is not None:
        stem += "__p%d" % patch
    for index, value in macros:
        stem += "__m%d-%g" % (index, value)
    return os.path.join(outdir, stem + ".wav")


def tier1_other(rate=48000, channels=2, block=2048):
    """WIRE, TAIL, LEVEL and CLICK rendered on each interpreter through the
    kit's own renderer and analysed here, which is the spec's split. STATE
    is not here: it drives the class rather than reading a render, so it has
    its own dual-runtime file, `tools/ladderfilter_state_probe.py`."""
    cls = audioeffects.LadderFilter
    print("TIER 1  %d Hz  %d ch  block %d  (rendered per interpreter)"
          % (rate, channels, block))
    ramp, ramp_path = probe_pcm("ramp_fs", rate, channels)
    source = M.Render(ramp.tobytes(), rate, channels, label="ramp_fs")
    burst_end = int(0.2 * rate)
    for name, binary in INTERPRETERS:
        axes = dict(rate=rate, channels=channels, block=block,
                    interpreter=name)
        wired = M.Render.from_wav(
            _wav(binary, "ramp_fs", rate, channels, block, DRY_MIDI), **axes)
        tailed = M.Render.from_wav(
            _wav(binary, "burst_silence", rate, channels, block, (), 0),
            **axes)
        wet = M.Render.from_wav(
            _wav(binary, "sine_100_-14", rate, channels, block, UNITY_MIDI),
            **axes)
        dry = M.Render.from_wav(
            _wav(binary, "sine_100_-14", rate, channels, block, DRY_MIDI),
            **axes)
        click_wet = M.Render.from_wav(
            _wav(binary, "click_stereo", rate, channels, block, (), 0),
            **axes)
        click_dry = M.Render.from_wav(
            _wav(binary, "click_stereo", rate, channels, block, DRY_MIDI),
            **axes)
        rows = [
            ("WIRE", M.wire(wired, source,
                            latency_samples=cls.LATENCY_SAMPLES)),
            ("TAIL", M.tail(tailed, burst_end_frame=burst_end)),
            ("LEVEL", M.level(wet, dry, skip_frames=int(0.1 * rate))),
            ("CLICK", M.click(click_wet, click_dry, cls.LATENCY_SAMPLES,
                              subsample=False)),
        ]
        print("  %-22s %s   digests wire %08x tail %08x level %08x "
              "click %08x"
              % (name,
                 "  ".join("%s %s" % (n, "green" if r["passed"] else "RED")
                           for n, r in rows),
                 wired.digest, tailed.digest, wet.digest, click_wet.digest))
        for label, result in rows:
            if not result["passed"]:
                print("      RED %s: %s" % (label, "; ".join(result["red"])))


# --------------------------------------------------------------------------
# Rate honesty, and the source block-size ladder
# --------------------------------------------------------------------------

def misc():
    print("RATE HONESTY  the Cutoff span clamps, never refuses")
    from audioeffects import _component
    for rate in (48000, 44100, 22050):
        effect = audioeffects.create(
            CLASS,
            audiocore.RawSample(silence(0.1, rate, 2), sample_rate=rate,
                                channel_count=2), rate)
        effect.set_macro(CUTOFF, 127)
        panel = effect.macro(CUTOFF)
        ceiling = rate * 0.5 * _component.NYQUIST_MARGIN
        applied = min(panel, ceiling)
        print("    %5d Hz  macro 0 at 127 -> panel %8.1f Hz, applied %8.1f "
              "Hz (0.49*f_s = %8.1f), no exception"
              % (rate, panel, applied, rate * 0.49))
        effect.set_macro(CUTOFF, 0)
        print("           macro 0 at 0   -> panel %8.1f Hz, applied %8.1f Hz"
              % (effect.macro(CUTOFF), max(effect.macro(CUTOFF), 1.0)))
        effect.deinit()

    print("BLOCK LADDER  the source block size, byte for byte")
    values = []
    for block in (256, 2048, 8192, 16384, 20000, 32768):
        digest = render_out([VENV], "chord", 48000, 2, block, (), 0)
        values.append((block, digest))
        print("    block %-6d %s" % (block, digest))
    agree = len({digest for _block, digest in values}) == 1
    print("    identical across the ladder: %s" % agree)


# --------------------------------------------------------------------------
# The class's own planted faults
# --------------------------------------------------------------------------

def faults(rate=48000, channels=2, block=2048):
    print("PLANTED FAULTS  %d Hz %d ch" % (rate, channels))
    cls = audioeffects.LadderFilter

    ramp, _ = probe_pcm("ramp_fs", rate, channels)
    source = M.Render(ramp.tobytes(), rate, channels, label="ramp_fs")
    wired = render(ramp, rate, channels, block, macros=at(mix=0.0))
    print("  WIRE      clean")
    show("WIRE", M.wire(wired, source, latency_samples=0))
    print("  WIRE      fault: the dry path x 32767/32768")
    show("WIRE", M.wire(scaled(wired, 32767.0 / 32768.0), source,
                        latency_samples=0))

    burst, _ = probe_pcm("burst_silence", rate, channels)
    tailed = render(burst, rate, channels, block, patch=0)
    burst_end = int(0.2 * rate)
    print("  TAIL      clean")
    show("TAIL", M.tail(tailed, burst_end_frame=burst_end))
    print("  TAIL      fault: +1 LSB of DC held in the settled state")
    show("TAIL", M.tail(with_dc(tailed, 1, int(1.0 * rate)),
                        burst_end_frame=burst_end))

    tone_pcm, _ = probe_pcm("sine_100_-14", rate, channels)
    wet = render(tone_pcm, rate, channels, block, macros=at(**UNITY))
    dry = render(tone_pcm, rate, channels, block, macros=at(mix=0.0))
    skip = int(0.1 * rate)
    print("  LEVEL     clean")
    show("LEVEL", M.level(wet, dry, skip_frames=skip))
    print("  LEVEL     fault: 0.5 dB of hidden gain on the wet path")
    show("LEVEL", M.level(scaled(wet, 10.0 ** (0.5 / 20.0)), dry,
                          skip_frames=skip))

    click_pcm, _ = probe_pcm("click_stereo", rate, channels)
    click_wet = render(click_pcm, rate, channels, block, patch=0)
    click_dry = render(click_pcm, rate, channels, block, macros=at(mix=0.0))
    print("  CLICK     clean (the integer reading, which is what "
          "latency_samples declares)")
    show("CLICK", M.click(click_wet, click_dry, cls.LATENCY_SAMPLES,
                          subsample=False))
    print("  CLICK     fault: latency_samples reported 256 short, the DSP "
          "untouched (digest %08x both ways)" % click_wet.digest)
    show("CLICK", M.click(click_wet, click_dry, 256, subsample=False))

    print("  STATE     clean")
    show("STATE", state_leg(rate, channels, block))
    print("  STATE     fault: reset() made a no-op, the loop left charged")
    show("STATE", state_leg(rate, channels, block, break_reset=True))

    print("  T1        clean")
    clean_result, clean_level = t1(rate=rate, cutoff=1000.0, quiet=True)
    print("    level at f_c %+.3f dB, absolute -3 dB %.1f Hz, slope %.2f "
          "dB/octave -> %s"
          % (clean_level, clean_result["values"]["absolute_corner_hz"],
             clean_result["values"]["slope_db_per_octave"],
             "green" if clean_result["passed"] else "RED"))
    print("  T1        fault: the class built at 1150 Hz - the corner moved "
          "15 % - with the trait's grid and bars still stated at 1 kHz")
    result, level_at_fc = t1(rate=rate, cutoff=1000.0, built_cutoff=1150.0,
                             quiet=True)
    corner = result["values"]["absolute_corner_hz"]
    slope = result["values"]["slope_db_per_octave"]
    red = []
    if abs(level_at_fc + 12.0) > 0.5:
        red.append("level at 1000 Hz reads %+.2f dB (bar -12.0 +- 0.5)"
                   % level_at_fc)
    if abs(corner - 435.0) > 20.0:
        red.append("-3 dB corner %.1f Hz (bar 435 +- 20)" % corner)
    if not (-27.0 <= slope <= -23.0):
        red.append("slope %.2f dB/octave (bar -23..-27)" % slope)
    print("    level at 1000 Hz %+.2f dB, corner %.1f Hz, slope %.2f  -> %s"
          % (level_at_fc, corner, slope, "RED" if red else "green"))
    for line in red:
        print("      RED %s" % line)

    print("  T2        fault: Passband Comp at 1, which is the droop's own "
          "negation")
    rows = []
    for k in (0.0, 1.0, 2.0, 3.0, 4.0):
        wet_by, dry_by = {}, {}
        for hz in (50.0, 100.0, 200.0):
            w, d = tone_pair(hz, rate, seconds=1.0, cutoff=1000.0,
                             resonance=k, drive=0.0, comp=1.0, poles=4.0,
                             oversample=1.0, mix=1.0)
            wet_by[hz], dry_by[hz] = w, d
        value = M.response(wet_by, dry_by,
                           reference_hz=100.0)["values"]["passband_db"]
        rows.append((k, value))
    want = {0.0: 0.00, 1.0: -6.02, 2.0: -9.54, 3.0: -12.04, 4.0: -13.98}
    red = ["k=%g reads %+.2f against %+.2f" % (k, v, want[k])
           for k, v in rows if abs(v - want[k]) > 0.5]
    print("    " + "  ".join("k=%g %+.2f" % row for row in rows)
          + "  -> %s" % ("RED" if red else "green"))
    for line in red:
        print("      RED %s" % line)

    print("  T3        clean")
    t3(rate=rate)
    print("  T3        fault: the Resonance travel capped at k = 3.9 - the "
          "old class's defect 3, a filter that cannot oscillate. The same "
          "measurement, with the top of travel at macro 118.")
    t3(rate=rate, top_position=117.93)

    print("  T4(b)     fault: an even nonlinearity, y + 0.05*y^2, on the "
          "self-oscillation render")
    osc = render(impulse(3.0, rate, 2, 32767), rate, 2,
                 macros=at(cutoff=1000.0, drive=0.0, comp=0.0, poles=4.0,
                           oversample=1.0, mix=1.0) + [(RESONANCE, 127.0)])
    settled = M.Render(osc.data[int(1.0 * rate):].tobytes(), rate, 2)
    tone_hz = _dominant_hz(osc.float[int(1.0 * rate):, 0], rate)
    for label, subject in (("clean", settled),
                           ("faulted", with_even_order(settled, 0.05))):
        spec = M.spectrum(subject, tone_hz, harmonics=8,
                          window="blackmanharris")
        h = spec["values"]["harmonic_db"]
        worst = max(v for k, v in h.items()
                    if k in ("h2", "h4", "h6", "h8") and v is not None)
        print("    %-8s worst even harmonic %+8.2f dB re h1 -> %s"
              % (label, worst, "RED" if worst > -40.0 else "green"))

    print("  T4(c)/T5  fault: the Drive knob frozen at 0 dB while the "
          "measurement believes it moved")
    values = []
    for _drive_db in (0.0, 8.0, 16.0, 24.0):
        out = render(tone(1000.0, 1.5, rate, 2, -20.0), rate, 2,
                     macros=at(cutoff=1000.0, resonance=3.9, drive=0.0,
                               comp=0.0, poles=4.0, oversample=1.0, mix=1.0))
        settled = M.Render(out.data[int(0.5 * rate):].tobytes(), rate, 2)
        values.append(M.spectrum(
            settled, 1000.0, harmonics=8,
            window="blackmanharris")["values"]["harmonic_db"]["h3"])
    span = values[-1] - values[0]
    print("    h3 %s   end to end %+.2f dB -> %s"
          % ([round(v, 2) for v in values], span,
             "RED" if span < 10.0 else "green"))


# --------------------------------------------------------------------------

def main(argv):
    part = argv[0] if argv else "all"
    if part in ("tier1", "all"):
        for rate in (48000, 44100, 22050):
            tier1(rate, 2)
        tier1(48000, 1)
    if part in ("t1", "all"):
        t1(48000)
        t1(44100)
    if part in ("t2", "all"):
        t2(48000)
        t2(44100)
    if part in ("t3", "all"):
        t3(48000)
        t3(44100)
    if part in ("t4", "all"):
        t4(48000)
    if part in ("t5", "all"):
        t5(48000)
    if part in ("tier1_other", "all"):
        for rate in (48000, 44100, 22050):
            tier1_other(rate, 2)
        tier1_other(48000, 1)
    if part in ("faults", "all"):
        faults()
    if part in ("digests", "all"):
        digests()
    if part in ("misc", "all"):
        misc()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
