"""Print DS-1 clipper peaks/THD from out/."""
import csv
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def load(name):
    path = os.path.join(OUT, name)
    with open(path, newline="") as handle:
        rows = list(csv.reader(handle))
    return np.array([[float(c) for c in row] for row in rows[1:]])


def thd(y, rate, f0=1000.0):
    spec = np.abs(np.fft.rfft(y))
    bin_hz = rate / float(len(y))
    def peak(hz):
        centre = int(round(hz / bin_hz))
        return float(spec[max(0, centre - 2):centre + 3].max())
    base = peak(f0)
    harm = [peak(f0 * n) for n in range(2, 11)]
    return 100.0 * math.sqrt(sum(h * h for h in harm)) / base, [
        20.0 * math.log10(max(h, 1e-18) / base) for h in harm]


def main():
    print("DS-1 clipper transients (last 10 ms, 1 kHz):")
    for amp in ("0.35", "1.0", "3.5"):
        data = load("clip_tran_amp%s.csv" % amp)
        t = data[:, 0]
        vo = data[:, 1]
        mask = t >= 0.010
        y = vo[mask]
        dt = float(np.median(np.diff(t[mask])))
        rate = 1.0 / dt
        peak = float(np.max(np.abs(y)))
        pct, harms = thd(y - np.mean(y), rate)
        print("  amp %s V: peak %.4f V  THD %.2f %%  h3 %.1f  h5 %.1f"
              % (amp, peak, pct, harms[1], harms[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
