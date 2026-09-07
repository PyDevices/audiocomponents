"""`Limiter`'s Tier 2 traits, each with the planted fault that turns it red.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/limiter_traits.py

CPython with numpy, through the measurement kit
(`tools/effect_measurements.py`). The class is built through
`create(source, sample_rate, **options)` every time - never the module-level
`configure()`, never a `patch=` keyword.

Every row prints a number and its bar. The faults are the cheap kind the kit
spec asks for: a subclass with the catch stage removed, the kit's own faulted
true-peak read, a macro at the wrong end, and a latency report 256 samples
short. `tests/test_cpython_effects_limiter.py` asserts what this file
measures; this file is where the numbers for the evidence pack come from.
"""

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
sys.path.insert(0, ROOT)

import audioeffects                                             # noqa: E402
import kit_probes as probes                                     # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
CEILING, GAIN, LOOKAHEAD, RELEASE, TRUE_PEAK, KNEE = range(6)


class NoCatchStage(audioeffects.Limiter):
    """L2 and L3's planted fault: the second `Dynamics` taken out, which is
    the one-node limiter the dossier's section 4 measured."""

    NAME = 'Limiter'

    def _build(self, **options):
        audioeffects.Limiter._build(self, **options)
        self._output = self._shape


def interleave(mono, channels=2):
    from array import array
    values = np.clip(np.round(np.asarray(mono) * 32768.0),
                     -32768, 32767).astype(np.int64)
    if channels == 2:
        values = np.repeat(values[:, None], 2, axis=1)
    return array("h", values.reshape(-1).tolist())


def burst(frames=48000, start=4800, length=48, level=1.0):
    values = np.zeros(frames)
    values[start:start + length] = level
    return interleave(values)


def impulse(frames=48000, at=4800, level=1.0):
    values = np.zeros(frames)
    values[at] = level
    return interleave(values)


def worst_phase_fs4(frames=48000, sample_peak_db=-0.5):
    index = np.arange(frames)
    amplitude = 10.0 ** (sample_peak_db / 20.0) / math.cos(math.pi / 4.0)
    return interleave(amplitude
                      * np.cos(2.0 * math.pi * index / 4.0 + math.pi / 4.0))


def sine(hz, frames=48000, dbfs=-0.1, rate=RATE):
    index = np.arange(frames)
    return interleave(10.0 ** (dbfs / 20.0)
                      * np.sin(2.0 * math.pi * hz * index / rate))


def build(probe, rate=RATE, cls=None, **options):
    source = probes.ArraySource(probe, rate=rate, block=256)
    return (cls or audioeffects.Limiter).create(source, rate, **options)


def render(effect, frames, rate=RATE, probe=None):
    return probes.render(effect.output, frames, rate=rate, block=256,
                         probe=probe, class_name="Limiter",
                         latency_samples=effect.latency_samples)


def thd_percent(values, rate, fundamental, harmonics=10):
    spectrum = np.abs(np.fft.rfft(np.asarray(values, dtype=np.float64)))
    width = rate / float(len(values))

    def magnitude(hz):
        centre = int(round(hz / width))
        return float(spectrum[max(0, centre - 1):centre + 2].max())

    upper = math.sqrt(sum(magnitude(fundamental * order) ** 2
                          for order in range(2, harmonics + 1)))
    return 100.0 * upper / magnitude(fundamental)


def l1_true_peak():
    print("L1  the ceiling is a true-peak promise (bar: +0.50 dB TP)")
    print("    rate    True Peak   sample peak   true peak   over ceiling")
    for rate in (48000, 44100):
        for flag in (True, False):
            effect = build(worst_phase_fs4(rate), rate=rate,
                           ceiling_db=-6.0, release_ms=60.0, true_peak=flag)
            result = render(effect, rate, rate=rate, probe="tone_fs4")
            effect.deinit()
            trimmed = kit.Render.from_pcm(result.pcm[400 * 4:], rate, 2,
                                          probe="tone_fs4", block=256,
                                          interpreter="cpython")
            reading = kit.truepeak(trimmed, ceiling_dbfs=-6.0,
                                   tolerance_db=0.5)
            values = reading["values"]
            print("    %5d   %-9s  %8.2f dBFS  %8.2f dBTP  %+6.2f dB  %s"
                  % (rate, "on" if flag else "off",
                     values["sample_peak_dbfs"], values["true_peak_dbtp"],
                     values["over_ceiling_db"],
                     "green" if reading["passed"] else "RED"))
    print("    planted fault: the kit's faulted read judges the ceiling on")
    print("    the sample peak instead of the reconstructed one.")
    effect = build(worst_phase_fs4(), ceiling_db=-6.0, release_ms=60.0,
                   true_peak=False)
    result = render(effect, RATE, probe="tone_fs4")
    effect.deinit()
    trimmed = kit.Render.from_pcm(result.pcm[400 * 4:], RATE, 2,
                                  probe="tone_fs4", block=256,
                                  interpreter="cpython")
    for read in ("true_peak", "sample_peak"):
        reading = kit.truepeak(trimmed, ceiling_dbfs=-6.0, tolerance_db=0.5,
                               read=read)
        print("      read=%-12s judged %8.2f -> %s   %s"
              % (read, reading["values"]["judged_dbfs"],
                 "green" if reading["passed"] else "RED",
                 "; ".join(reading["red"])))
    print()


def l2_l3_overshoot():
    print("L2/L3  lookahead never creates overshoot (bar: +0.10 dB, and no")
    print("       rise with lookahead). Ceiling -12 dBFS, release 60 ms.")
    for label, factory, settings in (
            ("L2  1 ms burst", burst, [float(n) for n in range(11)]),
            ("L3  1-sample impulse", impulse, [0.5, 1.0, 2.0, 5.0, 10.0])):
        print("    %s" % label)
        print("      lookahead    the class    fault: no catch stage")
        for lookahead in settings:
            row = []
            for cls in (audioeffects.Limiter, NoCatchStage):
                effect = build(factory(), cls=cls, ceiling_db=-12.0,
                               release_ms=60.0, lookahead_ms=lookahead)
                row.append(kit.peak_db(render(effect, 48000).float[:, 0]))
                effect.deinit()
            print("      %6.2f ms   %+7.3f dB   %+7.3f dB   %s / %s"
                  % (lookahead, row[0] + 12.0, row[1] + 12.0,
                     "green" if row[0] + 12.0 <= 0.1 else "RED",
                     "green" if row[1] + 12.0 <= 0.1 else "RED"))
    print()


def l4_latency():
    print("L4  reported latency equals floor(lookahead_ms * fs / 1000)")
    print("    rate     asked      floor()   reported   click   verdict")
    for rate in (48000, 44100, 22050):
        for asked in (0.0, 0.5, 1.5, 3.0, 7.3, 10.0):
            probe = probes.click_stereo(16384, offset=256)
            dry = probes.render(probes.ArraySource(probe, rate=rate,
                                                   block=256),
                                16384, rate=rate, block=256,
                                probe="click_stereo", class_name="source")
            effect = build(probe, rate=rate, ceiling_db=0.0,
                           lookahead_ms=asked)
            wet = render(effect, 16384, rate=rate, probe="click_stereo")
            reading = kit.click(wet, dry, effect.latency_samples)
            measured = reading["values"]["measured_latency_samples"]
            print("    %5d  %6.2f ms  %8d  %9d  %6s  %s"
                  % (rate, asked, int(asked * rate / 1000.0),
                     effect.latency_samples,
                     ",".join("%g" % value for value in set(measured)),
                     "green" if reading["passed"] else "RED"))
            effect.deinit()
    print("    planted fault: report 256 samples short, DSP untouched.")
    probe = probes.click_stereo(16384, offset=256)
    dry = probes.render(probes.ArraySource(probe, rate=RATE, block=256),
                        16384, rate=RATE, block=256, probe="click_stereo",
                        class_name="source")
    digests = []
    for short in (0, 256):
        effect = build(probe, ceiling_db=0.0, lookahead_ms=10.0)
        wet = render(effect, 16384, probe="click_stereo")
        digests.append("%08x" % wet.digest)
        reading = kit.click(wet, dry, effect.latency_samples - short)
        print("      reported %3d short -> %s   %s"
              % (short, "green" if reading["passed"] else "RED",
                 "; ".join(reading["red"])))
        effect.deinit()
    print("      audio digests %s and %s - %s"
          % (digests[0], digests[1],
             "identical, so only the report moved"
             if digests[0] == digests[1] else "DIFFERENT, which is wrong"))
    print()


def l5_defaults():
    print("L5  zero by default")
    for rate in (48000, 44100, 22050):
        effect = build(probes.silence(2048), rate=rate)
        print("    %5d Hz  latency %d, tail %s, Lookahead %.3f ms, "
              "True Peak %.2f, patch %s"
              % (rate, effect.latency_samples, effect.tail_samples,
                 effect.macro(LOOKAHEAD), effect.macro(TRUE_PEAK),
                 effect.patch_index))
        effect.deinit()
    print("    planted fault: patch 2 ('Loud'), which turns both on.")
    effect = build(probes.silence(2048), patch=2)
    print("      patch 2 -> latency %d samples, True Peak %.2f  RED against "
          "L5's bar, as it should be"
          % (effect.latency_samples, effect.macro(TRUE_PEAK)))
    effect.deinit()
    print()


def l6_curve():
    print("L6  infinite ratio, hard knee. Ceiling -24 dBFS, so a full 24 dB")
    print("    of input above it fits under 0 dBFS in int16.")

    def curve(knee_db, levels, frames=12000):
        outputs = []
        for level_db in levels:
            effect = build(sine(1000.0, frames, dbfs=float(level_db)),
                           ceiling_db=-24.0, release_ms=150.0,
                           knee_db=knee_db)
            outputs.append(kit.peak_db(
                render(effect, frames).float[frames // 2:, 0]))
            effect.deinit()
        return np.array(levels), np.array(outputs)

    levels, outputs = curve(0.0, list(np.linspace(-24.0, -0.2, 25)))
    slope = float(np.polyfit(levels, outputs, 1)[0])
    print("    slope above the ceiling over 24 dB: %+.5f dB/dB (bar 0.02)  %s"
          % (slope, "green" if abs(slope) <= 0.02 else "RED"))
    print("    highest output over the whole span: %+.4f dBFS"
          % float(outputs.max()))

    grid = list(np.arange(-32.0, -15.75, 0.25))

    def width(knee_db):
        levels, outputs = curve(knee_db, grid, frames=8000)
        slopes = np.gradient(outputs, levels)
        bending = levels[(slopes < 0.95) & (slopes > 0.05)]
        return 0.0 if not bending.size else float(bending.max()
                                                  - bending.min())

    hard, soft = width(0.0), width(12.0)
    print("    knee width at Knee 0:  %.3f dB (bar 0.50)  %s"
          % (hard, "green" if hard <= 0.5 else "RED"))
    print("    planted fault: the same measurement at Knee 12 -> %.3f dB  %s"
          % (soft, "RED" if soft > 0.5 else "green"))
    print()


def l7_thd():
    print("L7  smoothing is a documented trade (bar: 1 % at the default")
    print("    patch). 60 Hz sine at 0 dBFS into a -12 dBFS ceiling.")

    def thd(release_ms=None, rate=RATE):
        options = {"ceiling_db": -12.0}
        if release_ms is not None:
            options["release_ms"] = release_ms
        effect = build(sine(60.0, rate, dbfs=-0.1, rate=rate), rate=rate,
                       **options)
        result = render(effect, rate, rate=rate)
        effect.deinit()
        return thd_percent(result.float[rate // 2:, 0], rate, 60.0)

    for rate in (48000, 44100):
        value = thd(rate=rate)
        print("    %5d Hz, the default patch's 149 ms release: %.3f %%  %s"
              % (rate, value, "green" if value < 1.0 else "RED"))
    print("    planted fault: the Release macro at its fastest, 5 ms.")
    for release in (5.0, 30.0, 100.0, 149.0, 300.0):
        value = thd(release_ms=release)
        print("      release %6.1f ms -> %7.3f %%   %s"
              % (release, value, "RED" if value > 1.0 else "green"))
    print("    The docstring names the 5 ms end as a distortion setting; "
          "that number is recorded, not bounded.")
    print()


def main():
    print("Limiter Tier 2 traits, CPython, audioif at the pin")
    print("=" * 72)
    print()
    l1_true_peak()
    l2_l3_overshoot()
    l4_latency()
    l5_defaults()
    l6_curve()
    l7_thd()


if __name__ == "__main__":
    main()
