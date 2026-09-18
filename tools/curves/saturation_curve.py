#!/usr/bin/env python3
"""Derive Saturation waveshaper tables from the dossier's named values.

Run from the audiocomponents worktree:

    PYTHONPATH=lib python3 tools/curves/saturation_curve.py

Writes TUBE_CURVE, TAPE_CURVE, IRON_CURVE (hex bytes, int16 Q15) between
the marker comments in lib/audioeffects/saturation.py. Run again:
exit 0 if the module already holds what this file generates.

Tube: S2 eqs (10)-(12), RSD-1 parameters, in S1's netlist (Rp 100 k, Rk 1.5 k
bypassed, Rg 70 k, Vpp 250 V). Table x = +-1 is +-5 V peak grid. Output is
plate AC / 82.06 V (the cutoff headroom), so +1 is the supply ceiling.
DC solve and unnormalised small-signal gain are printed for TU3.

Tape and iron: Langevin anhysteretic (S3 eq 9), odd, Bias 0. Table x = +-1
is H/a = +-1. Tape bias at 55 kHz is not in the table (its linearising
effect near zero is the Langevin's own slope). No term was fitted by eye.
"""
from __future__ import print_function

import math
import os
import sys

POINTS = 1025
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODULE = os.path.join(ROOT, "lib", "audioeffects", "saturation.py")

# S2 Table 1, RSD-1.
G = 2.242e-3
MU = 103.2
GAMMA = 1.26
C = 3.40
GG = 6.177e-4
XI = 1.314
CG = 9.901
IG0 = 8.025e-8

RP = 100000.0
RK = 1500.0
RG = 70000.0
VPP = 250.0

# Table x=+-1 is this many volts at the grid (TU2's 10 V end).
TUBE_V_FULL = 10.0
# The grid-conduction extreme, so the table fills Q15 exactly: the plate
# sits at 64.071 V for +10 V of grid, 103.868 V below its quiescent
# 167.939, and the cutoff side then lands at 82.061/103.868 = 0.790.
#
# It was 166.7, which used 62 % of the range and threw away 4 dB of the
# only resolution the table has. That mattered where the class runs
# quietly: at 0.05 V of grid the shaper sees two or three steps, the
# second difference of the table there was a single Q15 count, and h3 -
# which is made of the third - was the rounding rather than the triode.
# Patch 0 read a 14.194 dB even-harmonic lead against TU1's 15 dB bar
# (audiocomponents#76). Filling the range costs nothing: same 1025
# points, same 2050 bytes, and `TUBE_MAKEUP` carries the 1/1.6049 back
# so the class's level does not move.
TUBE_SCALE = 103.8684

BEGIN_TUBE = "# --- BEGIN TUBE_CURVE ---"
END_TUBE = "# --- END TUBE_CURVE ---"
BEGIN_TAPE = "# --- BEGIN TAPE_CURVE ---"
END_TAPE = "# --- END TAPE_CURVE ---"
BEGIN_IRON = "# --- BEGIN IRON_CURVE ---"
END_IRON = "# --- END IRON_CURVE ---"


def _q15(y):
    return max(-32768, min(32767, int(round(y * 32767.0))))


def _ik_ig(vgk, vak):
    e1 = vgk + vak / MU
    arg = C * e1
    if arg > 40.0:
        u = e1
    elif arg < -40.0:
        u = 0.0
    else:
        u = math.log(1.0 + math.exp(arg)) / C
    ik = G * (u ** GAMMA) if u > 0.0 else 0.0
    garg = CG * vgk
    if garg > 40.0:
        ug = vgk
    elif garg < -40.0:
        ug = 0.0
    else:
        ug = math.log(1.0 + math.exp(garg)) / CG
    ig = GG * (ug ** XI) + IG0 if ug > 0.0 else IG0
    return ik, ig


def _dc_solve():
    """Damped fixed point. Cathode not bypassed for DC: Vk = Ik * Rk."""
    vk = 1.2
    va = 170.0
    vg = 0.0
    for _ in range(400):
        vgk = vg - vk
        vak = va - vk
        ik, ig = _ik_ig(vgk, vak)
        ia = ik - ig
        vk_n = ik * RK
        va_n = VPP - ia * RP
        vg_n = -ig * RG
        vk = vk + 0.25 * (vk_n - vk)
        va = va + 0.25 * (va_n - va)
        vg = vg + 0.25 * (vg_n - vg)
    vgk = vg - vk
    vak = va - vk
    ik, ig = _ik_ig(vgk, vak)
    ia = ik - ig
    return vk, va, ia, ig, vg


def _plate_for_grid(vg, vk):
    """Solve the load line for a held grid. Bisection, not a fixed point:
    Ia rises with Va, so VPP - Ia*RP - Va falls monotonically and the
    bracket [Vk, VPP] always contains the plate."""
    lo = vk
    hi = VPP
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        ik, ig = _ik_ig(vg - vk, mid - vk)
        if VPP - (ik - ig) * RP - mid > 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _plate_at(vin, vk, va0):
    """Ck bypassed: Vk held. Grid stopper Rg loads Ig. Returns plate volts.

    Both unknowns are bisected. The damped fixed point this replaced
    (2026-09-17) diverged the moment the grid conducted: Ig rises as
    exp(9.901*Vgk), so above Vgk = 0 each pass overshot further than the
    last and the table it wrote above +1.3 V of grid drive was noise, not
    a triode - the plate came back -128.8 V at +5 V in and +201.9 V at
    +10 V, where it must sit between the cathode and the supply. Ig rises
    with Vg, so vin - Ig*RG - Vg falls monotonically and the grid sits in
    [min(vin, Vk) - 5, vin] - grid-leak clamping, the real circuit's own
    reason the grid cannot follow a large positive swing.
    """
    lo = min(vin, vk) - 5.0
    hi = vin
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        va = _plate_for_grid(mid, vk)
        _, ig = _ik_ig(mid - vk, va - vk)
        if vin - ig * RG - mid > 0.0:
            lo = mid
        else:
            hi = mid
    return _plate_for_grid(0.5 * (lo + hi), vk)


def tube_points():
    vk, va0, ia, ig, vg = _dc_solve()
    # Small-signal gain: 1 mV either side, unnormalised.
    plus = _plate_at(0.001, vk, va0)
    minus = _plate_at(-0.001, vk, va0)
    gain = (plus - minus) / 0.002
    last = float(POINTS - 1)
    q15 = []
    for i in range(POINTS):
        x = -1.0 + 2.0 * i / last
        vin = x * TUBE_V_FULL
        va = _plate_at(vin, vk, va0)
        y = (va - va0) / TUBE_SCALE
        q15.append(_q15(y))
    zero = q15[POINTS // 2]
    # **The stage is inverting and the table is not, since the third fix
    # round.** A triode inverts, and a table that carries the inversion
    # puts the wet leg 180 degrees out of phase with the dry one - which
    # makes `Mix` a notch instead of a blend: correlation -47.2, and the
    # rendered level walks -18.57 dB at Mix 0.75 and back to -8.06 at Mix
    # 1 (audit 3 (p)2). Every unit this models has an even number of gain
    # stages for exactly that reason, so the sign goes here and no
    # harmonic magnitude moves with it.
    q15 = [max(-32768, min(32767, zero - v)) for v in q15]
    meta = {
        "vk": vk, "va": va0, "ia": ia, "ig": ig, "vg": vg,
        "gain": gain, "gain_db": 20.0 * math.log10(abs(gain)),
    }
    return q15, meta


def _langevin(x):
    if abs(x) < 1e-8:
        return x / 3.0
    return math.cosh(x) / math.sinh(x) - 1.0 / x


def tape_points():
    """Odd Langevin. x=+-1 -> H/a = +-1."""
    last = float(POINTS - 1)
    peak = abs(_langevin(1.0))
    out = []
    for i in range(POINTS):
        x = -1.0 + 2.0 * i / last
        out.append(_q15(_langevin(x) / peak))
    zero = out[POINTS // 2]
    return [max(-32768, min(32767, v - zero)) for v in out]


def iron_points():
    """Same anhysteretic as tape: iron's difference is the flux filter."""
    return tape_points()


def _hex_literal(values, name):
    packed = b"".join(
        bytes((v & 0xFF, (v >> 8) & 0xFF)) for v in values)
    lines = []
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
    tube, meta = tube_points()
    tape = tape_points()
    iron = iron_points()
    tube_src, tube_b = _hex_literal(tube, "TUBE_CURVE")
    tape_src, tape_b = _hex_literal(tape, "TAPE_CURVE")
    iron_src, iron_b = _hex_literal(iron, "IRON_CURVE")
    return (tube_src, tape_src, iron_src, tube_b, tape_b, iron_b,
            tube, tape, iron, meta)


def main(argv):
    (tube_src, tape_src, iron_src, tube_b, tape_b, iron_b,
     tube, tape, iron, meta) = tables()
    print("DC solve: Vk=%.3f V Ia=%.3f mA plate=%.2f V Ig=%.1f nA"
          % (meta["vk"], meta["ia"] * 1e3, meta["va"], meta["ig"] * 1e9))
    print("small-signal gain = %.2fx = %.2f dB (inverting=%s)"
          % (meta["gain"], meta["gain_db"], meta["gain"] < 0.0))
    print("tube Q15 origin", tube[POINTS // 2],
          "neg peak", min(tube), "pos peak", max(tube))
    print("tape Q15 origin", tape[POINTS // 2],
          "neg peak", min(tape), "pos peak", max(tape))
    if not os.path.isfile(MODULE):
        print("no module yet:", MODULE)
        return 2
    text = open(MODULE).read()
    rebuilt = _replace_block(text, BEGIN_TUBE, END_TUBE, tube_src)
    rebuilt = _replace_block(rebuilt, BEGIN_TAPE, END_TAPE, tape_src)
    rebuilt = _replace_block(rebuilt, BEGIN_IRON, END_IRON, iron_src)
    if rebuilt == text:
        print("ok: %s already holds the generated tables (%d + %d + %d bytes)"
              % (MODULE, len(tube_b), len(tape_b), len(iron_b)))
        return 0
    if argv[1:] == ["--check"]:
        print("drift: %s does not match the generator" % MODULE)
        return 1
    open(MODULE, "w").write(rebuilt)
    print("wrote tables into", MODULE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
