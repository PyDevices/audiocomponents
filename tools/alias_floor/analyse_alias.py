"""Read the rendered segments and report the alias floor with the kit.

    audiocomponents/.venv/bin/python tools/alias_floor/analyse_alias.py [work_dir]

`work_dir` holds what `make_material.py` wrote plus one directory per leg:

    alias_out_COM4/out_48000.raw      alias_out_COM4/out_44100.raw
    alias_out_COM49/...               alias_out_desktop/...

Two readings of the same spectrum, both by the drive dossiers' own rule -
Overdrive T7: "sum of every FFT bin more than two bins from a harmonic of
1010 Hz and from DC, against the fundamental's bin; 4800 samples at 48 kHz,
no window (101 exact periods, so every harmonic lands on a bin)":

  * `alias_floor_20k_db` - that sum restricted to 20 Hz - 20 kHz, which is
    the band all four bars name (Overdrive T7, Distortion A1, Fuzz A4,
    Saturation A4). **This is the number the -60 dB bar is graded on.**
  * `alias_floor_db` - `effect_measurements.spectrum`'s own reading, the same
    rule with no band limit, i.e. out to Nyquist. It is reported beside the
    first because the two part company at 48 kHz where the last decimation
    stage's transition band (20-28 kHz, by design) lets a fold land between
    20 kHz and Nyquist.

and the loudest single non-harmonic line, so a floor set by one image is
distinguishable from one set by a carpet.
"""

import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np                                          # noqa: E402
from effect_measurements import Render, spectrum            # noqa: E402

RATES = ((48000, 4800), (44100, 4410))
FREQS = (1010, 3700)
FACTORS = (1, 2, 4, 8)
BAR = -60.0
LEGS = (("P4", "alias_out_COM4"), ("S3", "alias_out_COM49"),
        ("desktop", "alias_out_desktop"))


def inharmonic(x, rate, size, f0, low_hz=None, high_hz=None):
    """Inharmonic energy against the fundamental's bin, over a band.

    Returns (summed dB, loudest single line dB, that line's Hz).
    """
    seg = np.asarray(x[:size], dtype=np.float64)
    spec = np.abs(np.fft.rfft(seg))
    bin_hz = rate / float(size)
    mask = np.ones(len(spec), dtype=bool)
    mask[:3] = False
    order = 1
    while f0 * order < rate / 2.0:
        centre = int(round(f0 * order / bin_hz))
        mask[max(0, centre - 2):centre + 3] = False
        order += 1
    freqs = np.arange(len(spec)) * bin_hz
    if low_hz is not None:
        mask &= freqs >= low_hz
    if high_hz is not None:
        mask &= freqs <= high_hz
    centre = int(round(f0 / bin_hz))
    base = spec[max(0, centre - 2):centre + 3].max()
    total = math.sqrt(float((spec[mask] ** 2).sum()))
    picked = np.where(mask, spec, 0.0)
    index = int(np.argmax(picked))
    return (20.0 * math.log10(max(total, 1e-12) / base),
            20.0 * math.log10(max(float(picked[index]), 1e-12) / base),
            float(index * bin_hz))


def main(work):
    rows = []
    for label, directory in LEGS:
        for rate, frames in RATES:
            path = os.path.join(work, directory, "out_%d.raw" % rate)
            if not os.path.exists(path):
                print("missing:", path)
                continue
            blob = open(path, "rb").read()
            segment_bytes = frames * 2
            expect = segment_bytes * len(FREQS) * len(FACTORS)
            if len(blob) != expect:
                raise SystemExit("SIZE MISMATCH %s: %d bytes, expected %d"
                                 % (path, len(blob), expect))
            index = 0
            for hz in FREQS:
                for factor in FACTORS:
                    pcm = blob[index * segment_bytes:
                               (index + 1) * segment_bytes]
                    index += 1
                    render = Render(pcm, rate, 1, label="%s %d %d x%d"
                                    % (label, rate, hz, factor))
                    result = spectrum(render, float(hz), harmonics=10,
                                      settled_ratio=0.0, size=frames,
                                      bars={"alias_floor_db": BAR})
                    full_db, peak_db, peak_hz = inharmonic(
                        render.float[:, 0], rate, frames, float(hz))
                    band_db, band_peak_db, band_peak_hz = inharmonic(
                        render.float[:, 0], rate, frames, float(hz),
                        low_hz=20.0, high_hz=20000.0)
                    rows.append({
                        "board": label,
                        "sample_rate": rate,
                        "tone_hz": hz,
                        "oversample": factor,
                        "alias_floor_20k_db": round(band_db, 3),
                        "alias_floor_db": result["values"]["alias_floor_db"],
                        "peak_alias_20k_db": round(band_peak_db, 3),
                        "peak_alias_20k_hz": round(band_peak_hz, 1),
                        "peak_alias_db": round(peak_db, 3),
                        "peak_alias_hz": round(peak_hz, 1),
                        "fundamental_dbfs":
                            result["values"]["fundamental_dbfs"],
                        "thd_db": result["values"]["thd_db"],
                        "transform_length": result["values"]["transform_length"],
                        "bin_hz": result["values"]["bin_hz"],
                        "window": result["values"]["window"],
                        "meets_60db_bar": band_db <= BAR,
                        "meets_60db_bar_full_band":
                            result["values"]["alias_floor_db"] <= BAR,
                        "pcm_sha256_16": hashlib.sha256(pcm).hexdigest()[:16],
                    })

    out = os.path.join(work, "alias_rows.json")
    json.dump(rows, open(out, "w"), indent=2)
    print("%-8s %6s %5s %4s %11s %11s %11s %10s %s"
          % ("leg", "rate", "tone", "os", "20Hz-20k", "full band",
             "peak line", "at Hz", "meets -60"))
    for row in rows:
        print("%-8s %6d %5d  x%-2d %11.2f %11.2f %11.2f %10.1f %s"
              % (row["board"], row["sample_rate"], row["tone_hz"],
                 row["oversample"], row["alias_floor_20k_db"],
                 row["alias_floor_db"], row["peak_alias_db"],
                 row["peak_alias_hz"], "yes" if row["meets_60db_bar"] else "NO"))
    print("\nwrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "work"))
