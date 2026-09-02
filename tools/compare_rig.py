#!/usr/bin/env python3
"""Compare a rig's REAPER bounce against its offline render, per gesture.

    tools/compare_rig.py <rig.RPP> <bounce.wav> <offline.wav>

Same tolerance and metric as micropython-vst3's own reaper/verify_song.py
(bounce-vs-preview, 3.5 dB per-section RMS): exact PCM equality is not
expected (host block size, IPC, pan law and pipeline latency all differ
between "REAPER hosts the plug-in" and "call audioinstruments.create()
directly"), but the two must agree on which gesture is loud, which is
quiet, and that no gesture went silent.

Gesture windows (name, start-of-next-marker) are parsed straight out of the
generated .RPP's own MARKER lines - what Brad actually sees in REAPER -
rather than recomputed from the gesture module, so the printed table never
disagrees with the project (a recomputed level-match boost, for instance,
would print a different number than the one actually baked into the
render it is describing).
"""
import re
import sys
import wave
from pathlib import Path

import numpy as np

TOLERANCE_DB = 3.5

# A window quieter than this in BOTH renders is not agreement, it is absence.
# Without this floor the comparator passes when the plug-in never loaded and
# the offline path also produced nothing: two silences agree perfectly. That
# is the shape of failure that had the reference-material verifier reporting
# 4273 files missing for three runs while the backup was fine - a checker that
# has only ever been shown to PASS has not been shown to work. Planted-fault
# coverage for this file lives in tests/test_rig_comparator.py.
SILENCE_FLOOR_DB = -60.0
MARKER_RE = re.compile(r'^\s*MARKER\s+\d+\s+([0-9.]+)\s+"(.*)"\s+\d')


def load(path):
    # REAPER's render default is 24-bit; the offline path writes 16-bit.
    # Handle both, matching micropython-vst3's own reaper/verify_song.py.
    with wave.open(str(path)) as handle:
        rate = handle.getframerate()
        width = handle.getsampwidth()
        channels = handle.getnchannels()
        raw = handle.readframes(handle.getnframes())
    if width == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif width == 3:
        as_bytes = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        value = (as_bytes[:, 0].astype(np.int32)
                 | (as_bytes[:, 1].astype(np.int32) << 8)
                 | (as_bytes[:, 2].astype(np.int32) << 16))
        value = np.where(value & 0x800000, value - 0x1000000, value)
        data = value.astype(np.float32) / 8388608.0
    elif width == 4:
        data = np.frombuffer(raw, dtype=np.float32)
    else:
        raise SystemExit("unsupported sample width %d in %s" % (width, path))
    return rate, data.reshape(-1, channels)


def rms_db(seg):
    if len(seg) == 0:
        return float("-inf")
    return 20 * np.log10(max(float(np.sqrt((seg ** 2).mean())), 1e-9))


def markers_of(rpp_path):
    out = []
    for line in Path(rpp_path).read_text().splitlines():
        m = MARKER_RE.match(line)
        if m:
            out.append((float(m.group(1)), m.group(2)))
    out.sort()
    return out


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: compare_rig.py <rig.RPP> <bounce.wav> "
                         "<offline.wav>")
    rpp_path, bounce_path, offline_path = sys.argv[1:4]

    markers = markers_of(rpp_path)
    if not markers:
        raise SystemExit("no MARKER lines found in %s" % rpp_path)

    rate_b, bounce = load(bounce_path)
    rate_o, offline = load(offline_path)
    if rate_b != rate_o:
        raise SystemExit("sample rate mismatch: bounce %d, offline %d"
                         % (rate_b, rate_o))
    rate = rate_b
    total = max(len(bounce), len(offline)) / float(rate)

    windows = []
    for i, (start, name) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else total
        windows.append((name, start, end))

    print("%-90s %10s %10s %8s" % ("gesture", "bounce", "offline", "diff"))
    failures = 0
    for name, start, end in windows:
        s0, s1 = int(start * rate), int(end * rate)
        b = rms_db(bounce[s0:min(s1, len(bounce))])
        o = rms_db(offline[s0:min(s1, len(offline))])
        diff = b - o
        silent = b < SILENCE_FLOOR_DB and o < SILENCE_FLOOR_DB
        ok = (not silent) and abs(diff) < TOLERANCE_DB
        failures += 0 if ok else 1
        label = name if len(name) <= 88 else name[:85] + "..."
        note = "" if ok else ("SILENT" if silent else "FAIL")
        print("%-90s %8.1fdB %8.1fdB %+6.1f %s"
              % (label, b, o, diff, note))

    peak_b = float(np.abs(bounce).max())
    peak_o = float(np.abs(offline).max())
    print("\npeak: bounce=%.3f offline=%.3f" % (peak_b, peak_o))

    print()
    if failures:
        print("RIG COMPARE: %d of %d gesture window(s) differ by >= %.1f dB "
              "or are silent in both renders (floor %.0f dB)"
              % (failures, len(windows), TOLERANCE_DB, SILENCE_FLOOR_DB))
        return 1
    print("RIG COMPARE: all %d gesture windows agree within %.1f dB"
          % (len(windows), TOLERANCE_DB))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
