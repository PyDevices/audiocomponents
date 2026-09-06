#!/usr/bin/env python3
"""analyze.py -- read the CSVs run.sh left in out/ and print the numbers.

numpy only.  Run with a python that has numpy, e.g.
  /home/brad/gh/pydevices/micropython-vst3/.venv/bin/python analyze.py

Prints:
  1. drive stage, AC at drive max: the high-pass corner from the simulated
     response beside the analytic 1/(2*pi*R4*C3) from the source's values
     (also the 51 pF low-pass corner and the plateau gain, same treatment);
  2. drive stage, each transient: THD and harmonics 2..5 relative to the
     fundamental, plus the input/output peaks and the monotonicity check
     the brief asks for (THD must rise with drive at a fixed input level);
  3. tone stage: gain in dB at 100 Hz, 1 kHz, 5 kHz at tone 0 / 0.5 / 1,
     beside an independent analytic solve of the same network with an
     ideal op-amp.
"""
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# --- component values, as read from source S1 (README) -----------------------
R4, C3 = 4.7e3, 47e-9        # inverting-input RC to ground
R6, P1 = 51e3, 500e3         # series feedback resistor, Distortion pot (max)
C4 = 51e-12                  # feedback capacitor
R5, C2 = 10e3, 1e-6          # (+) input bias resistor, input coupling cap
R7, C5, R9 = 1e3, 220e-9, 10e3           # tone stage low-pass node
R8, C6, R11, P2 = 220.0, 220e-9, 1e3, 20e3  # wiper RC, feedback R, Tone pot

POS = ["0", "0.5", "1"]
AMP = ["0.05", "0.2", "0.5"]
TONE = ["0", "0.5", "1"]
F0 = 1000.0        # transient test tone
DT = 1e-6          # linearize step (tran 1u ...)
T_WINDOW = (20e-3, 30e-3)   # analysis window: last 10 periods of 30 ms
N_HARM_THD = 20    # THD sums harmonics 2..20 (2 kHz .. 20 kHz)


def load(name):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        sys.exit(f"analyze.py: missing {path} -- run ./run.sh first")
    return np.loadtxt(path, delimiter=",", skiprows=1)


def read_opamp_params():
    """aol and gbw of the behavioural op-amp, read from models.lib."""
    text = open(os.path.join(HERE, "models.lib")).read()
    m = re.search(r"^\.param\s+aol=([0-9.eE+-]+)\s+gbw=([0-9.eE+-]+)", text, re.M)
    if not m:
        sys.exit("analyze.py: could not read '.param aol=... gbw=...' from models.lib")
    return float(m.group(1)), float(m.group(2))


def fc(r, c):
    return 1.0 / (2.0 * math.pi * r * c)


def interp_db(f, gdb, f_at):
    return float(np.interp(math.log10(f_at), np.log10(f), gdb))


# --- 1. drive stage AC ----------------------------------------------------------
def drive_ac():
    d = load("drive_ac_posmax.csv")
    f, gdb = d[:, 0], d[:, 1]
    k = int(np.argmax(gdb))
    f_peak, g_peak = f[k], gdb[k]

    # naive: -3 dB below the peak on the low side (biased low, because the
    # 51 pF pole is only 8x above the high-pass pole; reported for honesty)
    lo = slice(0, k + 1)
    f_naive = float(10 ** np.interp(g_peak - 3.0, gdb[lo], np.log10(f[lo])))

    # fit: the stage's small-signal model with three free parameters,
    #   G_ideal(f) = 1 + A * (jf/fh)/(1+jf/fh) / (1+jf/fl)      (ideal op-amp)
    #   G(f)       = Hin * G_ideal / (1 + G_ideal/Aol(f))        (real loop)
    # where Hin is the C2/R5 input coupling high-pass at its analytic corner
    # and Aol(f) = aol/(1 + jf/(gbw/aol)) is the single-pole op-amp exactly
    # as models.lib defines it (aol, gbw read from that file).  With Aol
    # left out (the "ideal op-amp fit" line below) the fitter absorbs the
    # 4558's 0.1 dB of loop-gain droop around 1 kHz as a ~3 % corner shift;
    # with it in, the fit reproduces the R4*C3 corner.  Neither fit is told
    # the analytic corner.
    aol, gbw = read_opamp_params()
    fin = fc(R5, C2)
    sel = (f >= 20) & (f <= 20000)
    fs, gs = f[sel], gdb[sel]
    hin = (1j * fs / fin) / (1 + 1j * fs / fin)
    aol_f = aol / (1 + 1j * fs / (gbw / aol))

    def fit(with_opamp):
        def err(A, fh, fl):
            # A: (na,1,1), fh: (1,nh,1), fl: (1,1,nl); fs broadcast on a 4th axis
            s = 1j * fs[None, None, None, :]
            g = 1 + A[..., None] * (s / fh[..., None]) / (1 + s / fh[..., None]) / (1 + s / fl[..., None])
            if with_opamp:
                g = g / (1 + g / aol_f)
            g = hin * g
            return np.sum((20 * np.log10(np.abs(g)) - gs) ** 2, axis=-1)

        ra = [math.log10(30), math.log10(300)]
        rh = [math.log10(200), math.log10(3000)]
        rl = [math.log10(1500), math.log10(30000)]
        for _ in range(5):
            As = np.logspace(*ra, 25)[:, None, None]
            fhs = np.logspace(*rh, 41)[None, :, None]
            fls = np.logspace(*rl, 41)[None, None, :]
            e = err(As, fhs, fls)
            ia, ih, il = np.unravel_index(np.argmin(e), e.shape)
            A, fh, fl = float(As[ia, 0, 0]), float(fhs[0, ih, 0]), float(fls[0, 0, il])
            for v, rng in ((A, ra), (fh, rh), (fl, rl)):       # shrink around the winner
                span = (rng[1] - rng[0]) / 4
                rng[0], rng[1] = math.log10(v) - span / 2, math.log10(v) + span / 2
        return A, fh, fl, math.sqrt(float(np.min(e)) / len(fs))

    A, fh, fl, rms = fit(True)
    A0, fh0, fl0, rms0 = fit(False)

    fh_an = fc(R4, C3)
    fl_an = fc(R6 + P1, C4)
    A_an = (R6 + P1) / R4
    # two zero-biased 1N4148s sit across the feedback network; the Nexperia
    # model gives each a small-signal resistance N*Vt/IS at 0 V, which the
    # AC analysis sees in parallel with R6+P1 (a real, minor effect)
    rd = 1.906 * 0.025865 / 4.352e-9
    rf_eff = 1 / (1 / (R6 + P1) + 2 / rd)
    A_d = rf_eff / R4
    fl_d = fc(rf_eff, C4)

    print("1. Drive stage, small-signal AC at drive max (pos = 1)")
    print(f"   peak gain                 {g_peak:6.1f} dB at {f_peak:7.0f} Hz")
    print(f"   gain at 100 Hz / 1 kHz / 5 kHz   {interp_db(f, gdb, 100):5.1f} / "
          f"{interp_db(f, gdb, 1000):5.1f} / {interp_db(f, gdb, 5000):5.1f} dB")
    print(f"   high-pass corner (fit)    {fh:7.1f} Hz   analytic 1/(2 pi R4 C3)        "
          f"= {fh_an:7.1f} Hz   dev {100 * (fh / fh_an - 1):+5.1f} %")
    print(f"   low-pass corner  (fit)    {fl:7.0f} Hz   analytic 1/(2 pi (R6+P1) C4)   "
          f"= {fl_an:7.0f} Hz   dev {100 * (fl / fl_an - 1):+5.1f} %"
          f"   (with the diodes' {rd / 1e6:.1f} MOhm each in parallel: {fl_d:.0f} Hz, dev {100 * (fl / fl_d - 1):+5.1f} %)")
    print(f"   plateau gain 1+A (fit)    {1 + A:7.1f}      analytic 1+(R6+P1)/R4        "
          f"= {1 + A_an:7.1f}      dev {100 * ((1 + A) / (1 + A_an) - 1):+5.1f} %"
          f"   (with the diodes: {1 + A_d:.1f}, dev {100 * ((1 + A) / (1 + A_d) - 1):+5.1f} %)")
    print(f"   fit residual              {rms:.3f} dB rms over {len(fs)} points, 20 Hz .. 20 kHz;"
          f" op-amp aol = {aol:.0e}, gbw = {gbw / 1e6:.0f} MHz from models.lib")
    print(f"   ideal-op-amp fit          {fh0:7.1f} Hz corner (dev {100 * (fh0 / fh_an - 1):+5.1f} %), "
          f"{fl0:.0f} Hz low-pass, gain {1 + A0:.1f}, residual {rms0:.3f} dB rms"
          f"   -- the 4558's finite GBW read as a corner shift")
    print(f"   naive -3 dB below peak    {f_naive:7.1f} Hz   (biased low by the 51 pF pole 8x above; not the corner)")
    return fh, fh_an


# --- 2. drive stage transients ---------------------------------------------------
def harmonics(name):
    d = load(name)
    t, vout, vin = d[:, 0], d[:, 1], d[:, 2]
    sel = (t >= T_WINDOW[0] - DT / 2) & (t < T_WINDOW[1] - DT / 2)
    x = vout[sel] - vout[sel].mean()
    xi = vin[sel] - vin[sel].mean()
    n = len(x)
    df = 1.0 / (n * DT)
    k = int(round(F0 / df))
    assert abs(k * df - F0) < 1e-6, "window is not an integer number of periods"
    X = np.abs(np.fft.rfft(x)) * 2.0 / n
    h = np.array([X[k * m] for m in range(1, N_HARM_THD + 1)])
    thd = math.sqrt(float(np.sum(h[1:] ** 2))) / h[0]
    return dict(thd=thd, h=h, in_pk=float(np.max(np.abs(xi))),
                out_pk=float(np.max(x)), out_min=float(np.min(x)), n=n)


def drive_tran():
    print()
    print("2. Drive stage, 1 kHz transient: THD and harmonics 2..5 re fundamental")
    print(f"   (window {T_WINDOW[0] * 1e3:.0f}..{T_WINDOW[1] * 1e3:.0f} ms = 10 periods, "
          f"THD over harmonics 2..{N_HARM_THD})")
    print("   pos   in pk    out pk    h1 gain   THD      h2       h3       h4       h5")
    print("         (mV)     (V)       (dB)      (%)      (dB)     (dB)     (dB)     (dB)")
    table = {}
    for a in AMP:
        for p in POS:
            r = harmonics(f"drive_tran_pos{p}_amp{a}.csv")
            table[(p, a)] = r
            hdb = 20 * np.log10(r["h"] / r["h"][0])
            print(f"   {p:>3}   {r['in_pk'] * 1e3:5.0f}    {r['out_pk']:5.3f}     "
                  f"{20 * math.log10(r['h'][0] / r['in_pk']):5.1f}     {100 * r['thd']:5.1f}    "
                  f"{hdb[1]:6.1f}   {hdb[2]:6.1f}   {hdb[3]:6.1f}   {hdb[4]:6.1f}")
        print()
    ok = True
    for a in AMP:
        seq = [table[(p, a)]["thd"] for p in POS]
        mono = all(seq[i] < seq[i + 1] for i in range(len(seq) - 1))
        ok &= mono
        print(f"   THD vs drive at {float(a) * 1e3:3.0f} mV: "
              + " < ".join(f"{100 * s:.1f}%" for s in seq)
              + ("   rises monotonically: OK" if mono else "   NOT monotonic: FAIL"))
    return ok, table


# --- 3. tone stage ----------------------------------------------------------------
def tone_analytic(tone, f):
    """Ideal-op-amp nodal solve of the tone network (README, ts808_tone.cir).

    Nodes: p = (+) input, w = pot wiper, n = (-) input (= p, ideal op-amp).
    """
    w = 2 * math.pi * f
    rpa = P2 * tone + 1.0
    rpb = P2 * (1 - tone) + 1.0
    ya, yb = 1 / rpa, 1 / rpb
    yw = 1 / (R8 + 1 / (1j * w * C6))
    y5, y9, y7 = 1j * w * C5, 1 / R9, 1 / R7
    # KCL at w with Vn = Vp:  Vw = Vp (ya+yb)/(ya+yb+yw)
    kw = (ya + yb) / (ya + yb + yw)
    # KCL at p:  Vp (y7+y5+y9+ya) - Vw ya = Vin y7
    vp = y7 / (y7 + y5 + y9 + ya - kw * ya)
    vw = kw * vp
    # KCL at n:  (Vout - Vn)/R11 = (Vn - Vw) yb
    vout = vp + R11 * yb * (vp - vw)
    return 20 * math.log10(abs(vout))


def tone():
    print()
    print("3. Tone stage, small-signal gain at op-amp pin 7 (Level at max), dB")
    print("   tone     100 Hz    1 kHz    5 kHz   |  analytic, ideal op-amp:  100 Hz    1 kHz    5 kHz"
          "   |  after C7/R12/P3 (lv): 100 Hz  1 kHz  5 kHz")
    for tstr in TONE:
        d = load(f"tone_ac_tone{tstr}.csv")
        f, g, glv = d[:, 0], d[:, 1], d[:, 3]
        sim = [interp_db(f, g, x) for x in (100, 1000, 5000)]
        lv = [interp_db(f, glv, x) for x in (100, 1000, 5000)]
        an = [tone_analytic(float(tstr), x) for x in (100, 1000, 5000)]
        print(f"   {tstr:>4}   {sim[0]:7.2f}  {sim[1]:7.2f}  {sim[2]:7.2f}   |"
              f"                          {an[0]:7.2f}  {an[1]:7.2f}  {an[2]:7.2f}"
              f"   |                        {lv[0]:6.2f} {lv[1]:6.2f} {lv[2]:6.2f}")
    print(f"   (analytic low-pass node: 1/(2 pi (R7||R9) C5) = {fc(R7 * R9 / (R7 + R9), C5):.0f} Hz;"
          f" ElectroSmash's 1/(2 pi R7 C5) = {fc(R7, C5):.1f} Hz ignores R9;"
          f" treble shelf zero 1/(2 pi R8 C6) = {fc(R8, C6):.0f} Hz, max boost 1+R11/R8 = "
          f"{20 * math.log10(1 + R11 / R8):.1f} dB)")


def main():
    fh, fh_an = drive_ac()
    ok, _ = drive_tran()
    tone()
    print()
    dev = abs(fh / fh_an - 1)
    print(f"Sanity: high-pass corner within a few percent of analytic: "
          f"{'OK' if dev < 0.05 else 'FAIL'} ({100 * dev:.1f} %);  "
          f"THD monotonic in drive at every input level: {'OK' if ok else 'FAIL'}")
    return 0 if (ok and dev < 0.05) else 1


if __name__ == "__main__":
    sys.exit(main())
