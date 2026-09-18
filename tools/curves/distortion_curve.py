#!/usr/bin/env python3
"""Derive Distortion's waveshaper tables from the Rat and DS-1 clipper circuits.

The tables are the static solution of a silicon pair to ground:

    (Vin - Vo) / R = 2 * IS * sinh(Vo / (N * Vt))

with Nexperia's 1N4148 IS and N (dossier S8), R = 1 kOhm (Rat R6) or
2.2 kOhm (DS-1 R14). Vin is clipped to the op-amp rails (+-3.5 V, dossier
section 8 Q5) before the pair. The result is written into
``lib/audioeffects/distortion.py`` as a bytes literal between marker
comments; the class wraps it in ``array("h", ...)`` and never computes a
float on a board.

Each table is **normalised to its own clipped extreme so it fills int16**,
and the volts its full scale stands for go out beside it as
``_CURVE_<name>_VOLTS`` for the class to carry in the shaper's
``post_gain``. Holding volts directly left the Rat at 66 % of the range and
the DS-1 at 62 %, which threw away resolution for nothing
(audiocomponents#77).

Run again to assert the module already holds what this file generates.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODULE = os.path.join(ROOT, "lib", "audioeffects", "distortion.py")

IS = 4.352e-9
N = 1.906
VT = 25.852e-3
NVT = N * VT
RAIL = 3.5
POINTS = 1024
V_SCALE = 10.0
RAT_R = 1000.0
DS1_R = 2200.0

#: A table that does not reach the rails throws away the only resolution it
#: has, for nothing. Both curves are normalised to their own extreme now,
#: so anything under this on the larger side is a defect and refused
#: (audiocomponents#77).
FILL_FLOOR = 0.95

BEGIN = "# BEGIN CURVE {name}"
END = "# END CURVE {name}"


def diode_pair(vin, resistance):
    vo = 0.0
    for _ in range(80):
        s = math.sinh(vo / NVT)
        c = math.cosh(vo / NVT)
        f = (vin - vo) / resistance - 2.0 * IS * s
        df = -1.0 / resistance - 2.0 * IS * c / NVT
        vo -= f / df
    return vo


#: How many 1N4148s sit in series on the quieter side of the asymmetric
#: clipper. One diode to ground one way and two the other is the DS-1's
#: own asymmetric clipping section - the shipped `Asymmetry` macro used to
#: model it as a **bias into the symmetric table**, which is a 3.5 V offset
#: at the macro's top and parks the operating point at 0.97 of full scale:
#: -6.8 dBFS of DC on the output with a silent input, a coupling capacitor
#: that has to hold it, and a 0.45-of-full-scale step whenever the input
#: goes from silence to a note (audit 3 (p)4, ruling (n)). A real
#: asymmetric clipper answers a silent input with silence; it is the
#: *thresholds* that differ, not the operating point.
ASYM_DIODES = 2


def diode_asym(vin, resistance, count=ASYM_DIODES):
    """One 1N4148 to ground one way, `count` in series the other.

    Same solve as `diode_pair`, with the two antiparallel branches written
    out because they no longer share a magnitude. `diode_asym(0, R)` is
    exactly 0, which is the whole point.
    """
    vo = 0.0
    for _ in range(120):
        forward = math.exp(min(60.0, vo / NVT))
        reverse = math.exp(min(60.0, -vo / (count * NVT)))
        current = IS * (forward - 1.0) - IS * (reverse - 1.0)
        slope = IS * forward / NVT + IS * reverse / (count * NVT)
        f = (vin - vo) / resistance - current
        df = -1.0 / resistance - slope
        step = f / df
        if step > 0.25:
            step = 0.25
        elif step < -0.25:
            step = -0.25
        vo -= step
    return vo


def asym_peak_volts(resistance):
    """The larger of the two clipped extremes - the quieter side's."""
    return max(abs(diode_asym(RAIL, resistance)),
               abs(diode_asym(-RAIL, resistance)))


def asym_curve_volts(resistance):
    return asym_peak_volts(resistance) * 32768.0 / 32767.0


def asym_table(resistance):
    last = float(POINTS - 1)
    peak = asym_peak_volts(resistance)
    values = []
    for index in range(POINTS):
        x = -1.0 + 2.0 * index / last
        vin = max(-RAIL, min(RAIL, x * V_SCALE))
        vo = diode_asym(vin, resistance)
        word = int(round(vo / peak * 32767.0))
        if word > 32767:
            word = 32767
        if word < -32768:
            word = -32768
        values.append(word)
    return values


def peak_volts(resistance):
    """The clipped voltage at the rail, which is the curve's own extreme."""
    return abs(diode_pair(RAIL, resistance))


def curve_volts(resistance):
    """Volts the node reads at the table's full scale.

    The table is normalised to 32767 so both rails land exactly on it and
    the curve stays symmetric - an asymmetric table would write even
    harmonics the diode pair does not have - while `Waveshaper` divides its
    entries by 32768. The ratio lives here, not in the class, so the two
    cannot drift.
    """
    return peak_volts(resistance) * 32768.0 / 32767.0


def table(resistance):
    last = float(POINTS - 1)
    peak = peak_volts(resistance)
    values = []
    for index in range(POINTS):
        x = -1.0 + 2.0 * index / last
        vin = max(-RAIL, min(RAIL, x * V_SCALE))
        vo = diode_pair(vin, resistance)
        word = int(round(vo / peak * 32767.0))
        if word > 32767:
            word = 32767
        if word < -32768:
            word = -32768
        values.append(word)
    return values


def fill(values):
    """How much of int16 the table's larger side uses, 0-1."""
    return max(abs(min(values)), abs(max(values))) / 32767.0


def as_bytes_literal(values):
    raw = b"".join(int(v).to_bytes(2, "little", signed=True) for v in values)
    hexed = raw.hex()
    lines = []
    for start in range(0, len(hexed), 64):
        chunk = hexed[start:start + 64]
        lines.append("    '" + chunk + "'")
    return "bytes.fromhex(\n" + "\n".join(lines) + "\n)"


def replace_block(text, name, literal, volts):
    begin = BEGIN.format(name=name)
    end = END.format(name=name)
    start = text.find(begin)
    stop = text.find(end)
    if start < 0 or stop < 0 or stop <= start:
        raise SystemExit("markers missing for %s" % name)
    stop += len(end)
    body = (
        begin + "\n"
        + "#: Volts at this table's full scale. The table is normalised to\n"
        + "#: its own extreme so it fills int16 (audiocomponents#77) and the\n"
        + "#: class carries the scale back out in `post_gain`.\n"
        + "_CURVE_%s_VOLTS = %.9f\n" % (name, volts)
        + "_CURVE_%s = " % name
        + literal + "\n"
        + end
    )
    return text[:start] + body + text[stop:]


def extract_block(text, name):
    begin = BEGIN.format(name=name)
    end = END.format(name=name)
    start = text.find(begin)
    stop = text.find(end)
    return text[start:stop + len(end)]


def main(argv):
    check = "--check" in argv or not os.environ.get("DISTORTION_CURVE_WRITE")
    # Default: write if the module exists and --check was not given.
    write = "--write" in argv
    if write:
        check = False
    if not write and "--check" not in argv:
        write = True
        check = False

    rat_words = table(RAT_R)
    ds1_words = table(DS1_R)
    ds1_asym_words = asym_table(DS1_R)
    for name, words in (("RAT_DIODE", rat_words), ("DS1_DIODE", ds1_words),
                        ("DS1_ASYM", ds1_asym_words)):
        used = fill(words)
        if used < FILL_FLOOR:
            raise SystemExit(
                "distortion_curve.py: %s uses %.1f %% of int16 on its larger "
                "side (floor %.0f %%). Normalise it to the curve's own "
                "extreme and carry the scale in post_gain - "
                "audiocomponents#77." % (name, 100.0 * used,
                                         100.0 * FILL_FLOOR))
    rat = as_bytes_literal(rat_words)
    ds1 = as_bytes_literal(ds1_words)
    ds1_asym = as_bytes_literal(ds1_asym_words)
    with open(MODULE, "r", encoding="utf-8") as handle:
        text = handle.read()
    wanted = replace_block(
        replace_block(
            replace_block(text, "RAT_DIODE", rat, curve_volts(RAT_R)),
            "DS1_DIODE", ds1, curve_volts(DS1_R)),
        "DS1_ASYM", ds1_asym, asym_curve_volts(DS1_R))
    if check:
        if wanted != text:
            raise SystemExit("distortion.py curves are stale; run with --write")
        print("distortion_curve.py: module already holds RAT_DIODE, "
              "DS1_DIODE and DS1_ASYM")
        print("points=%d V_scale=%.1f rail=%.1f R_rat=%.0f R_ds1=%.0f"
              % (POINTS, V_SCALE, RAIL, RAT_R, DS1_R))
        print("fill rat=%.2f %% ds1=%.2f %% (floor %.0f %%); "
              "full scale rat=%.6f V ds1=%.6f V"
              % (100.0 * fill(rat_words), 100.0 * fill(ds1_words),
                 100.0 * FILL_FLOOR, curve_volts(RAT_R), curve_volts(DS1_R)))
        return 0
    if wanted == text:
        print("distortion_curve.py: already current")
        return 0
    with open(MODULE, "w", encoding="utf-8") as handle:
        handle.write(wanted)
    print("distortion_curve.py: wrote RAT_DIODE, DS1_DIODE and DS1_ASYM "
          "into %s" % MODULE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
