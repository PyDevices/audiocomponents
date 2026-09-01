#!/usr/bin/env python3
"""Measure one-shot drum hits for the accuracy program's dossiers and gates.

    measure_hits.py <dir-of-wavs> [--json out.json]

Per file: duration, peak dBFS, decay time constant tau (least-squares fit of
log-envelope over the post-peak region), T60 extrapolated from tau, dominant
frequency early (first 50 ms after peak) and late (100-300 ms), and spectral
centroid -- enough to state and later verify envelope/pitch acceptance
criteria. Aggregates min/median/max per statistic over the directory.

Station A uses the aggregates to ground a dossier's criteria; Station C
re-runs the same script so the numbers in the evidence pack are computed by
the same code that proposed them. stdlib + numpy only.
"""
import argparse, json, math, sys, wave
from pathlib import Path
import numpy as np


def load_wav(path):
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
        width = w.getsampwidth()
        ch = w.getnchannels()
    if width == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        x = ((b[:, 0].astype(np.int32)) | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        x = (x - (x >> 23 << 24)).astype(np.float64) / (1 << 23)
    elif width == 4:
        x = np.frombuffer(raw, dtype="<i4").astype(np.float64) / (1 << 31)
    else:
        raise ValueError("unsupported sample width %d" % width)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return sr, x


def envelope(x, sr, win_ms=5.0):
    win = max(1, int(sr * win_ms / 1000.0))
    pad = (-len(x)) % win
    seg = np.pad(np.abs(x), (0, pad)).reshape(-1, win)
    return np.sqrt((seg ** 2).mean(axis=1)), win


def dominant_freq(x, sr, start, stop):
    seg = x[start:stop]
    if len(seg) < 64:
        return None
    seg = seg * np.hanning(len(seg))
    spec = np.abs(np.fft.rfft(seg, n=max(4096, len(seg))))
    freqs = np.fft.rfftfreq(max(4096, len(seg)), 1.0 / sr)
    lo = np.searchsorted(freqs, 20.0)
    if lo >= len(spec):
        return None
    return float(freqs[lo + int(np.argmax(spec[lo:]))])


def centroid(x, sr):
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
    s = spec.sum()
    return float((freqs * spec).sum() / s) if s > 0 else None


def measure(path):
    sr, x = load_wav(path)
    if not len(x):
        return None
    peak = float(np.max(np.abs(x)))
    if peak == 0:
        return None
    env, win = envelope(x, sr)
    pk = int(np.argmax(env))
    # Fit log-envelope from peak down to -50 dB or the end, whichever first.
    floor = env[pk] * 10 ** (-50 / 20.0)
    tail = env[pk:]
    below = np.nonzero(tail <= floor)[0]
    stop = int(below[0]) if len(below) else len(tail)
    seg = tail[:max(stop, 3)]
    t = np.arange(len(seg)) * win / sr
    ln = np.log(np.maximum(seg, 1e-9))
    slope, _ = np.polyfit(t, ln, 1)
    tau = float(-1.0 / slope) if slope < 0 else None            # seconds to 1/e
    t60 = float(tau * math.log(1000.0)) if tau else None        # -60 dB time
    pk_smp = pk * win
    f_early = dominant_freq(x, sr, pk_smp, pk_smp + int(0.05 * sr))
    f_late = dominant_freq(x, sr, pk_smp + int(0.10 * sr), pk_smp + int(0.30 * sr))
    return {
        "file": path.name, "sr": sr,
        "duration_s": round(len(x) / sr, 4),
        "peak_dbfs": round(20 * math.log10(peak), 2),
        "tau_s": round(tau, 4) if tau else None,
        "t60_s": round(t60, 4) if t60 else None,
        "f_early_hz": round(f_early, 1) if f_early else None,
        "f_late_hz": round(f_late, 1) if f_late else None,
        "centroid_hz": round(centroid(x, sr), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json")
    args = ap.parse_args()
    root = Path(args.root)
    rows = []
    for p in sorted(root.rglob("*.wav")):
        if "__MACOSX" in str(p):
            continue
        try:
            row = measure(p)
        except Exception as e:
            print("skip %s: %s" % (p.name, e), file=sys.stderr)
            continue
        if row:
            row["group"] = p.parent.name
            rows.append(row)
    groups = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r)
    summary = {}
    for g, rs in sorted(groups.items()):
        stats = {}
        for key in ("duration_s", "tau_s", "t60_s", "f_early_hz", "f_late_hz", "centroid_hz"):
            vals = [r[key] for r in rs if r[key] is not None]
            if vals:
                stats[key] = {"min": min(vals), "median": float(np.median(vals)), "max": max(vals), "n": len(vals)}
        summary[g] = stats
        print("%-28s n=%-3d  tau %s  f_early %s  centroid %s" % (
            g, len(rs),
            ("%.3f/%.3f/%.3f" % (stats["tau_s"]["min"], stats["tau_s"]["median"], stats["tau_s"]["max"])) if "tau_s" in stats else "-",
            ("%.0f/%.0f/%.0f" % (stats["f_early_hz"]["min"], stats["f_early_hz"]["median"], stats["f_early_hz"]["max"])) if "f_early_hz" in stats else "-",
            ("%.0f/%.0f/%.0f" % (stats["centroid_hz"]["min"], stats["centroid_hz"]["median"], stats["centroid_hz"]["max"])) if "centroid_hz" in stats else "-"))
    if args.json:
        json.dump({"files": rows, "summary": summary}, open(args.json, "w"), indent=1)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
