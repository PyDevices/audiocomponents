"""The refuter's pass over `MultibandCompressor`'s five Tier 2 traits.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_refute.py

Written against the evidence pack of 2026-09-07, not against the class: it
re-runs each demonstrated trait's own measurement at settings, rates, block
sizes and tone positions the evidence did not use, all inside the trait's own
words. `docs/effects/MultibandCompressor-evidence.md`, "Refutation record
(2026-09-07)", is written from this run.
"""

import math
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "tools/phase2_probes")

from array import array                                      # noqa: E402

import effect_measurements as kit                            # noqa: E402
import multiband_traits as T                                 # noqa: E402
from audioeffects.rebuilt.multibandcompressor import (        # noqa: E402
    MultibandCompressor as MB)

VENDOR = "PyDevices"

RATE = 48000
NAMES = ("low", "mid", "high")
LEVEL_DB = 20.0 * math.log10(T.AMPLITUDE / math.sqrt(2.0) / 32768.0)
RATIO = 4.0
THRESHOLD = LEVEL_DB - 12.0 / (1.0 - 1.0 / RATIO)


# --- M1, M2 ----------------------------------------------------------------

def m1_case(label, rate, **opts):
    grid = T.sixth_octave(30.0, min(20000.0, 0.45 * rate))
    settings = dict(T.UNITY)
    settings.update(opts)
    low, high = T.worst(T.sum_curve(MB, rate, grid, **settings))
    bad = max(abs(low), abs(high)) > 0.25
    print("M1 %-40s %-5s max %+.3f min %+.3f  (%d tones to %.0f Hz)"
          % (label, "RED" if bad else "green", high, low, len(grid),
             grid[-1]))
    return bad


def m2_case(label, rate, low_hz, high_hz):
    grid = T.sixth_octave(30.0, min(20000.0, 0.45 * rate))
    settings = dict(T.UNITY)
    settings.update(bands=3, crossover_low_hz=low_hz,
                    crossover_high_hz=high_hz)
    bad = False
    for band, corner, span, reference, name in (
            (1, low_hz, (low_hz * 2, low_hz * 4), 40.0, "low band"),
            (3, high_hz, (high_hz / 4, high_hz / 2),
             min(8000.0, 0.4 * rate), "high band")):
        wet = {}
        dry = {}
        for hz in grid:
            wet[hz] = T.render_tone(MB, hz, rate=rate, solo=band, **settings)
            dry[hz] = T.dry_tone(hz, rate=rate)
        result = kit.response(wet, dry, reference_hz=reference,
                              slope_octave=span)
        points = result["values"]["grid"]
        at_corner = kit._interpolate_log(
            [p["hz"] for p in points], [p["magnitude_db"] for p in points],
            corner) - result["values"]["passband_db"]
        slope = result["values"]["slope_db_per_octave"]
        ok = (abs(at_corner + 6.0) <= 0.5
              and slope is not None and abs(abs(slope) - 24.0) <= 2.0)
        bad = bad or not ok
        print("M2 %-40s %-5s corner %+.2f dB skirt %.1f dB/oct"
              % ("%s%g/%g @%d %s" % (label, low_hz, high_hz, rate, name),
                 "RED" if not ok else "green", at_corner, abs(slope or 0.0)))
    for corner in (low_hz, high_hz):
        wet = {}
        dry = {}
        for hz in (corner / 1.05, corner, corner * 1.05):
            wet[hz] = T.render_tone(MB, hz, rate=rate, **settings)
            dry[hz] = T.dry_tone(hz, rate=rate)
        result = kit.response(wet, dry, reference_hz=corner)
        value = result["values"]["passband_db"]
        ok = abs(value) <= 0.25
        bad = bad or not ok
        print("M2 %-40s %-5s %+.3f dB"
              % ("%ssum at %g Hz @%d" % (label, corner, rate),
                 "RED" if not ok else "green", value))
    return bad


# --- M3 --------------------------------------------------------------------

def m3_run(label, base, band_tones, soloed):
    print("--- %s  (%s)" % (label, "soloed, as the evidence reads it"
                            if soloed else "SUMMED output, no solo"))
    for driven in sorted(band_tones):
        options = dict(base)
        options[NAMES[driven] + "_threshold_db"] = THRESHOLD
        options[NAMES[driven] + "_ratio"] = RATIO
        for band in sorted(band_tones):
            row = []
            for hz in band_tones[band]:
                solo = (band + 1) if soloed else None
                wet = T.render_tone(MB, hz, rate=RATE, solo=solo, **options)
                idle = T.render_tone(MB, hz, rate=RATE, solo=solo, **base)
                a = kit.tone_bin(wet.float[wet.frames // 2:, 0], RATE, hz)
                b = kit.tone_bin(idle.float[idle.frames // 2:, 0], RATE, hz)
                row.append((hz, kit.db(abs(a) / abs(b)) if abs(b) else 0.0))
            values = [v for _hz, v in row]
            if band == driven:
                mean = sum(values) / len(values)
                tilt = max(values) - min(values)
                extra = ("mean %+.2f tilt %.2f  depth %s tilt %s"
                         % (mean, tilt,
                            "green" if abs(mean + 12.0) <= 0.5 else "RED",
                            "green" if tilt <= 0.5 else "RED"))
            else:
                worst = max(abs(v) for v in values)
                extra = ("worst %+.2f  isolation %s"
                         % (worst, "green" if worst <= 0.5 else "RED"))
            print("  %-4s driven, %-4s band: %s | %s"
                  % (NAMES[driven], NAMES[band],
                     " ".join("%.0f:%+.2f" % entry for entry in row), extra))


def m3_skirt(base):
    """Is the shortfall the band's own skirt, or something unexplained?"""
    driven = dict(base)
    driven.update(mid_threshold_db=THRESHOLD, mid_ratio=RATIO)
    print("--- the mid band's shortfall against what its own skirt predicts")
    print("    A = idle magnitude re the band's peak; B = the reduction;")
    print("    C = -12 + (1 - 1/ratio) x |A|, section 1a's cause 1")
    rows = []
    for hz in (200.0, 240.0, 283.0, 340.0, 400.0, 566.0, 700.0, 1000.0,
               1414.0, 1700.0, 2000.0):
        idle = T.render_tone(MB, hz, rate=RATE, solo=2, **base)
        wet = T.render_tone(MB, hz, rate=RATE, solo=2, **driven)
        a = kit.db(abs(kit.tone_bin(idle.float[idle.frames // 2:, 0],
                                    RATE, hz)))
        b = kit.db(abs(kit.tone_bin(wet.float[wet.frames // 2:, 0], RATE, hz)))
        rows.append((hz, a, b - a))
    peak = max(a for _hz, a, _d in rows)
    for hz, a, d in rows:
        skirt = a - peak
        predicted = -12.0 + (1.0 - 1.0 / RATIO) * (-skirt)
        print("    %6.0f Hz  A %+6.2f  B %+7.2f  C %+7.2f  B-C %+5.2f"
              % (hz, skirt, d, predicted, d - predicted))
    inside = [d for hz, _a, d in rows if 283.0 <= hz <= 1414.0]
    print("    283..1414 Hz, all within 1.75 dB of the band's own peak:"
          " mean %+.2f  tilt %.2f"
          % (sum(inside) / len(inside), max(inside) - min(inside)))


def m3_bytes(base):
    options = dict(base)
    options.update(low_threshold_db=THRESHOLD, low_ratio=RATIO)
    wet = T.render_tone(MB, 700.0, rate=RATE, solo=2, **options)
    idle = T.render_tone(MB, 700.0, rate=RATE, solo=2, **base)
    print("--- the soloed idle read, at the byte level: mid band at 700 Hz,")
    print("    low band driven to 12 dB. identical bytes: %s (%08x vs %08x)"
          % (wet.data.tobytes() == idle.data.tobytes(), wet.digest,
             idle.digest))


# --- M4, M5 ----------------------------------------------------------------

def m4_case(label, rate, **opts):
    values = array("h")
    for index in range(64 + 1 + int(0.2 * rate)):
        value = 24000 if index == 64 else 0
        for _ in range(T.CHANNELS):
            values.append(value)
    effect = T.build(MB, values, rate, T.CHANNELS, **opts)
    pcm = T.render(effect, len(values) // T.CHANNELS, T.CHANNELS)
    reported = effect.latency_samples
    effect.deinit()
    result = kit.click(kit.Render(pcm, rate, T.CHANNELS,
                                  interpreter="cpython"),
                       kit.Render(bytes(memoryview(values).cast("B")), rate,
                                  T.CHANNELS, interpreter="cpython"),
                       reported, subsample=False, tolerance_samples=0.0)
    print("M4 %-52s %-5s reported %d measured %s"
          % (label, "green" if result["passed"] else "RED", reported,
             result["values"]["measured_latency_samples"]))
    return 0 if result["passed"] else 1


def m5_case(label, cls, blocks, values, **opts):
    digests = []
    frames = len(values) // T.CHANNELS
    for block in blocks:
        effect = T.build(cls, values, RATE, T.CHANNELS, block=block, **opts)
        pcm = T.render(effect, frames, T.CHANNELS)
        effect.deinit()
        render = kit.Render(pcm, RATE, T.CHANNELS, block=block,
                            interpreter="cpython")
        digests.append((block, "%08x" % render.digest,
                        int((render.data != 0).sum())))
    ok = (len(set(entry[1] for entry in digests)) == 1
          and all(entry[2] for entry in digests))
    print("M5 %-40s %-5s %s" % (label, "green" if ok else "RED",
                                "  ".join("%d:%s/%d" % entry
                                          for entry in digests)))
    return 0 if ok else 1


def main():
    print("MultibandCompressor - the refuter's pass, CPython, pin 2f6cbc3")
    print("=" * 72)
    print("--- M1: three bands at other exactly-8:1 pairs, 48 kHz")
    for low in (40.0, 100.0, 400.0, 800.0):
        m1_case("3b %g/%g (8:1)" % (low, low * 8), 48000, bands=3,
                crossover_low_hz=low, crossover_high_hz=low * 8)
    print("--- M1: two bands across the whole macro span, 48 kHz")
    for low in (60.0, 120.0, 300.0, 500.0, 650.0):
        m1_case("2b %g" % low, 48000, bands=2, crossover_low_hz=low)
    print("--- M1: the evidence's own settings at 44.1 and 22.05 kHz")
    for rate in (44100, 22050):
        m1_case("3b 200/2000", rate, bands=3, crossover_low_hz=200.0,
                crossover_high_hz=2000.0)
        m1_case("3b 800/6400", rate, bands=3, crossover_low_hz=800.0,
                crossover_high_hz=6400.0)
        m1_case("2b 200", rate, bands=2, crossover_low_hz=200.0)
    print("--- M1: quiet material, amplitude 800 not 8000")
    T.AMPLITUDE = 800
    m1_case("3b 200/2000 at -32 dBFS", 48000, bands=3,
            crossover_low_hz=200.0, crossover_high_hz=2000.0)
    T.AMPLITUDE = 8000
    print("--- M2: 200/2000 at the other two rates, and another pair")
    m2_case("", 44100, 200.0, 2000.0)
    m2_case("", 22050, 200.0, 2000.0)
    m2_case("", 48000, 100.0, 4000.0)

    base = dict(T.UNITY)
    base.update(bands=3, crossover_low_hz=200.0, crossover_high_hz=2000.0)
    tones = {0: (30.0, 63.0, 100.0, 141.0),
             1: (283.0, 400.0, 700.0, 1000.0, 1414.0),
             2: (2828.0, 4000.0, 8000.0, 16000.0)}
    m3_run("M3 on the summed output, 200/2000", base, tones, False)
    m3_run("M3 soloed, the same tones", base, tones, True)
    wide = dict(T.UNITY)
    wide.update(bands=3, crossover_low_hz=40.0, crossover_high_hz=8000.0)
    m3_run("M3 mid band at 40/8000", wide,
           {1: (80.0, 200.0, 500.0, 1200.0, 4000.0)}, True)
    m3_skirt(base)
    m3_bytes(base)

    print("--- M4: settings, rates and patches the evidence did not try")
    m4_case("22050 Hz 3 bands 200/2000", 22050, mix=1.0, bands=3,
            crossover_low_hz=200.0, crossover_high_hz=2000.0)
    m4_case("22050 Hz 2 bands 200", 22050, mix=1.0, bands=2,
            crossover_low_hz=200.0)
    m4_case("48000 Hz 3 bands 800/6400 (closest legal)", 48000, mix=1.0,
            bands=3, crossover_low_hz=800.0, crossover_high_hz=800.0)
    m4_case("48000 Hz 2 bands 800", 48000, mix=1.0, bands=2,
            crossover_low_hz=800.0)
    m4_case("48000 Hz mix 0.5", 48000, mix=0.5)
    m4_case("48000 Hz mix 0.0 (bypass)", 48000, mix=0.0)
    m4_case("48000 Hz attack 0.1 ms, release 5 ms, ratio 20", 48000, mix=1.0,
            attack_ms=0.1, release_ms=5.0, low_ratio=20.0, mid_ratio=20.0,
            high_ratio=20.0, low_threshold_db=-60.0, mid_threshold_db=-60.0,
            high_threshold_db=-60.0)
    for patch in range(5):
        m4_case("48000 Hz patch %d" % patch, 48000, patch=patch)

    print("--- M5: seven blocks, the whole render, and burst digests")
    blocks = (256, 8193, 12000, 16384, 32768, 65536, 100000)
    tone = T.tone(220.0, RATE, T.CHANNELS, seconds=0.75, amplitude=20000)
    m5_case("tone, 7 blocks, all 36000 frames", MB, blocks, tone, bands=3,
            mix=1.0)
    m5_case("tone, 7 blocks, 2 bands", MB, blocks, tone, bands=2, mix=1.0)
    m5_case("tone, the NoGuard fault, all frames", T.NoGuard, blocks, tone,
            bands=3, mix=1.0)
    burst = array("h")
    burst.extend(T.tone(440.0, RATE, T.CHANNELS, seconds=0.04,
                        amplitude=24000))
    for _ in range(int(0.6 * RATE)):
        for _ in range(T.CHANNELS):
            burst.append(0)
    m5_case("burst, 7 blocks, digest not just a count", MB, blocks, burst,
            bands=3, mix=1.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
