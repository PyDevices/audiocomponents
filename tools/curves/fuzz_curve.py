#!/usr/bin/env python3
"""Derive the Fuzz waveshaper tables from the dossier's named values.

Run from the audiocomponents worktree:

    PYTHONPATH=lib python3 tools/curves/fuzz_curve.py

Writes `GERMANIUM_CURVE` and `CASCADE_CURVE` (hex bytes literals wrapping
int16 Q15) between the marker comments in
`lib/audioeffects/rebuilt/fuzz.py`. Run again: exit 0 if the module already
holds what this file generates, exit 1 if it drifted.

Germanium (Fuzz Face Q1). S1: Rc 33 kΩ, collector at rest −1.6 V on a 9 V
supply (1.6 V to saturation, 7.4 V to cutoff). S9 Ebers-Moll for an AC128:
Is 23.75 µA, Nf 1.168, Vt 25.5 mV. Forward-active Ic = Is·exp(Vbe/(Nf·Vt)),
Vc = −9 + Ic·Rc, clamped to [−9, 0]. Rest Vbe is the log that puts Vc at
−1.6 V. The shape is (Vc + 1.6) / 7.4. No term was fitted by ear.

The germanium shape is **normalised to its own extreme** before it is stored,
so the table fills int16 on its larger side, and `GERMANIUM_SCALE` — written
beside the bytes by this file so the two cannot drift — carries the scale
back out in the node's `post_gain`. It used to hold the shape directly, which
peaked at −20713 / +7085 (63 % of the range) and quantised every entry four
decibels more coarsely than it had to for nothing (audiocomponents#77, the
shape audiocomponents#76 proved on Saturation). **The asymmetry is the
circuit's identity and survives exactly**: both halves are divided by the
same number, so −32767 / +11208 holds the same 2.9235 ratio the volts do.

Cascade (Big Muff silicon pair). S5: diodes across the collector–base loop
at ±0.6 V, R9/R15/R17 = 470 kΩ. Static implicit
(Vin − Vo)/R = 2·Is·sinh(Vo/(N·Vt)) with Nexperia's 1N4148 parameters as
facts about the part (Overdrive dossier S6: Is 4.352e-9, N 1.906), Vt
26 mV. Newton, then peak-normalised to Q15. Same curve in both stages.
"""
from __future__ import print_function

import math
import os
import sys

POINTS = 1025
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODULE = os.path.join(ROOT, "lib", "audioeffects", "rebuilt", "fuzz.py")

# S9 AC128 Ebers-Moll (dossier A3).
GE_IS = 23.75e-6
GE_NF = 1.168
GE_VT = 0.0255
GE_RC = 33000.0
GE_VCC = 9.0
GE_VC0 = 1.6
GE_ROOM_CUT = GE_VCC - GE_VC0  # 7.4

# S5 / Nexperia 1N4148 (facts about the part).
SI_IS = 4.352e-9
SI_N = 1.906
SI_VT = 0.026
SI_R = 470000.0

BEGIN_GE = "# --- BEGIN GERMANIUM_CURVE ---"
END_GE = "# --- END GERMANIUM_CURVE ---"
BEGIN_SI = "# --- BEGIN CASCADE_CURVE ---"
END_SI = "# --- END CASCADE_CURVE ---"

# A table that does not reach the rails throws away the only resolution it
# has, for nothing. Each curve is normalised to its own extreme and the scale
# is carried back out in the node's `post_gain`, so this refuses anything
# under 95 % of int16 on the **larger** side — the larger side, because the
# germanium curve is asymmetric by design and squaring it up would be
# throwing the circuit away to satisfy an arithmetic check
# (audiocomponents#77).
FILL_FLOOR = 0.95


def _q15(y):
    return max(-32768, min(32767, int(round(y * 32767.0))))


def fill(words):
    """How much of int16 a table's larger side uses, 0-1."""
    return max(abs(min(words)), abs(max(words))) / 32767.0


def germanium_shape():
    """The collector AC in units of the 7.4 V room, before normalisation.

    Table x = ±1 is the Vbe excursion that takes the collector to cutoff
    (the 7.4 V room). Saturation then lands at x = +1.6/7.4. gm at rest is
    Ic0/(Nf·Vt), so dy/dx at 0 is 1 after dividing the collector AC by 7.4.
    """
    ic0 = GE_ROOM_CUT / GE_RC
    vbe0 = GE_NF * GE_VT * math.log(ic0 / GE_IS)
    gm = ic0 / (GE_NF * GE_VT)
    vbe_full = GE_ROOM_CUT / (GE_RC * gm)  # volts of Vbe to cutoff
    out = []
    last = float(POINTS - 1)
    for i in range(POINTS):
        x = -1.0 + 2.0 * i / last
        vbe = vbe0 + x * vbe_full
        vbe = max(-2.0, min(2.0, vbe))
        ic = GE_IS * math.exp(vbe / (GE_NF * GE_VT))
        vc = -GE_VCC + ic * GE_RC
        if vc > 0.0:
            vc = 0.0
        if vc < -GE_VCC:
            vc = -GE_VCC
        out.append((vc + GE_VC0) / GE_ROOM_CUT)
    return out


def germanium_scale(shape=None):
    """What full scale on the stored table stands for, in shape units.

    The table holds `y / peak`, and the node reads an entry as
    `entry / 32768` and multiplies the result by `post_gain * 32768`. The
    old table held `round(y * 32767)`, so multiplying the new one's output
    by this number puts the level back exactly where it was.
    """
    shape = germanium_shape() if shape is None else shape
    return max(abs(min(shape)), abs(max(shape)))


def germanium_points():
    """Q15 table, normalised to the curve's own extreme so it fills int16.

    It used to hold the shape directly, peaking at −20713 / +7085 — 63 % of
    the range on the larger side — so every entry carried four more decibels
    of quantisation than it needed to (audiocomponents#77). Both halves are
    divided by the same number, so the off-centre bias that is this
    circuit's identity is untouched.
    """
    shape = germanium_shape()
    peak = germanium_scale(shape)
    out = [_q15(y / peak) for y in shape]
    zero = out[POINTS // 2]
    return [max(-32768, min(32767, v - zero)) for v in out]


def _sinh_clip(vin):
    vo = 0.0
    scale = SI_N * SI_VT
    for _ in range(40):
        arg = vo / scale
        if arg > 20.0:
            arg = 20.0
        elif arg < -20.0:
            arg = -20.0
        sinh = math.sinh(arg)
        cosh = math.cosh(arg)
        f = (vin - vo) / SI_R - 2.0 * SI_IS * sinh
        df = -1.0 / SI_R - 2.0 * SI_IS * cosh / scale
        step = f / df
        vo -= step
        if abs(step) < 1e-12:
            break
    return vo


def cascade_points():
    raw = []
    last = float(POINTS - 1)
    peak = 1e-18
    for i in range(POINTS):
        vin = -1.0 + 2.0 * i / last
        vo = _sinh_clip(vin)
        raw.append(vo)
        if abs(vo) > peak:
            peak = abs(vo)
    scaled = [_q15(v / peak) for v in raw]
    zero = scaled[POINTS // 2]
    return [max(-32768, min(32767, v - zero)) for v in scaled]


def _hex_literal(values, name, preamble=()):
    packed = b"".join(
        bytes((v & 0xFF, (v >> 8) & 0xFF)) for v in values)
    lines = list(preamble)
    lines.append("%s = bytes.fromhex(" % name)
    for offset in range(0, len(packed), 32):
        chunk = packed[offset:offset + 32].hex()
        comma = "" if offset + 32 >= len(packed) else " +"
        lines.append('    "%s"%s' % (chunk, comma))
    lines.append(")")
    return "\n".join(lines), packed


def _replace_block(text, begin, end, body):
    start = text.index(begin)
    stop = text.index(end, start)
    return text[:start] + begin + "\n" + body + "\n" + text[stop:]


def tables():
    ge = germanium_points()
    si = cascade_points()
    preamble = (
        "#: What full scale on `GERMANIUM_CURVE` stands for. The table is",
        "#: normalised to the curve's own extreme so it fills int16",
        "#: (audiocomponents#77) and this carries the scale back out in the",
        "#: shaper's `post_gain`, so the class's level does not move.",
        "GERMANIUM_SCALE = %.9f" % germanium_scale(),
    )
    ge_src, ge_bytes = _hex_literal(ge, "GERMANIUM_CURVE", preamble)
    si_src, si_bytes = _hex_literal(si, "CASCADE_CURVE")
    return ge_src, si_src, ge_bytes, si_bytes, ge, si


def _report(ge, si):
    print("germanium Q15 origin", ge[POINTS // 2],
          "neg peak", min(ge), "pos peak", max(ge),
          "fill %.4f" % fill(ge),
          "asym %.6f" % (abs(min(ge)) / float(max(ge))),
          "scale %.9f" % germanium_scale())
    print("cascade Q15 origin", si[POINTS // 2],
          "neg peak", min(si), "pos peak", max(si),
          "fill %.4f" % fill(si))


def main(argv):
    ge_src, si_src, ge_bytes, si_bytes, ge, si = tables()
    for name, words in (("GERMANIUM_CURVE", ge), ("CASCADE_CURVE", si)):
        used = fill(words)
        if used < FILL_FLOOR:
            sys.stderr.write(
                "fuzz_curve: %s uses %.1f %% of int16 on its larger side "
                "(floor %.0f %%). Normalise it to the curve's own extreme "
                "and carry the scale in post_gain - audiocomponents#77.\n"
                % (name, 100.0 * used, 100.0 * FILL_FLOOR))
            return 3
    if not os.path.isfile(MODULE):
        print("no module yet:", MODULE)
        _report(ge, si)
        return 2
    text = open(MODULE).read()
    rebuilt = _replace_block(text, BEGIN_GE, END_GE, ge_src)
    rebuilt = _replace_block(rebuilt, BEGIN_SI, END_SI, si_src)
    if rebuilt == text:
        print("ok: %s already holds the generated tables (%d + %d bytes)"
              % (MODULE, len(ge_bytes), len(si_bytes)))
        _report(ge, si)
        return 0
    if argv[1:] == ["--check"]:
        print("drift: %s does not match the generator" % MODULE)
        return 1
    open(MODULE, "w").write(rebuilt)
    print("wrote tables into", MODULE)
    _report(ge, si)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
