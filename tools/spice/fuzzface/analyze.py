#!/usr/bin/env python3
"""THD of the last 10 ms of each Fuzz Face transient."""
import glob
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def thd(signal, rate, f0=1000.0, harmonics=10):
    window = signal[-int(0.01 * rate):]
    spec = np.abs(np.fft.rfft(window * np.hanning(len(window))))
    bin_hz = rate / float(len(window))
    base = spec[max(1, int(round(f0 / bin_hz)))]
    power = 0.0
    rows = {}
    for n in range(2, harmonics + 1):
        idx = int(round(n * f0 / bin_hz))
        if idx >= len(spec):
            break
        rows["h%d" % n] = 20.0 * math.log10(spec[idx] / base + 1e-18)
        power += spec[idx] ** 2
    return 20.0 * math.log10(math.sqrt(power) / base + 1e-18), rows


def main():
    rate = 1e6  # linearize 1 us
    paths = sorted(glob.glob(os.path.join(HERE, "out", "tran_fuzz*.csv")))
    if not paths:
        print("no CSVs; run ./run.sh")
        return 1
    print("%8s %8s  h2     h3     h4" % ("fuzz", "THD"))
    for path in paths:
        data = np.loadtxt(path, delimiter=",")
        # wrdata: time, v(vol), time, v(in) — or time, v(vol), v(in)
        if data.shape[1] >= 3:
            out = data[:, 1]
        else:
            out = data[:, 1]
        thd_db, harm = thd(out, rate)
        name = os.path.basename(path)
        print("%8s %7.2f  %6.1f %6.1f %6.1f"
              % (name, thd_db, harm.get("h2", 0), harm.get("h3", 0),
                 harm.get("h4", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
