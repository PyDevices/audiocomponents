"""The five Tier 2 traits of `MultibandCompressor`, each beside the planted
fault of its own kind.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_traits.py

Desktop only: the analysis is numpy and the kit
(`tools/effect_measurements.py`), which is CPython by design - the render is
dual-runtime, the analysis is not (`docs/effects-kit-spec.md` section 1).
The Tier 1 block, which is integer work, runs on all three interpreters in
`multiband_tier1.py`.

Every fault below is a subclass that cuts one seam of the real class, so the
faulted build is the class minus one decision and not a different program.
"""

import math
import sys

sys.path.insert(0, "tools")

import audiocore                                             # noqa: E402
import audiofilters                                          # noqa: E402
import audiobiquad                                           # noqa: E402
import effect_measurements as kit                            # noqa: E402

from array import array                                      # noqa: E402
from audioeffects.rebuilt.multibandcompressor import (        # noqa: E402
    MultibandCompressor)

VENDOR = "PyDevices"

RATE = 48000
CHANNELS = 2
AMPLITUDE = 8000
SECONDS = 0.35
FAILURES = []


# --- the faults ------------------------------------------------------------

class NoRatioClamp(MultibandCompressor):
    """M1's fault: the eight-to-one crossover clamp removed.

    The trait is stated *against* that clamp, so the fault of the same kind
    is a build that accepts the setting the clamp exists to refuse. The
    surface enforces the rule twice - the 8:1 push-up in `_apply_crossovers`
    and the 800 Hz floor on Crossover High's own span - so both come out
    here, or the fault cannot reach 2:1 at all and reads as if the clamp
    were doing nothing.
    """

    _MACRO_RANGES = (MultibandCompressor._MACRO_RANGES[:1]
                     + ((200.0, 8000.0, "log"),)
                     + MultibandCompressor._MACRO_RANGES[2:])

    def _apply_crossovers(self):
        self._low_hz = self._hz(self.macro(0))
        if self._bands == 2:
            self._high_hz = self._low_hz
            self._tune(0, (self._low_hz, self._low_hz))
            self._tune(1, (self._low_hz, self._low_hz))
            return
        self._high_hz = self._hz(self.macro(1))
        self._tune(0, (self._low_hz, self._low_hz))
        self._tune(1, (self._low_hz, self._low_hz,
                       self._high_hz, self._high_hz))
        self._tune(2, (self._high_hz, self._high_hz))


class LinkwitzRiley2(MultibandCompressor):
    """M2's fault: one Butterworth section a side instead of two.

    LR2, which RaneNote 160 says needs one output inverted. Nothing here
    inverts anything, so the corner should read -3 dB with a 12 dB/octave
    skirt and the sum should null there.
    """

    def _band_modes(self, band):
        full = MultibandCompressor._band_modes(self, band)
        if len(full) == 2:
            return full[:1]
        return (audiobiquad.HIGH_PASS, audiobiquad.LOW_PASS)


class SharedDetector(MultibandCompressor):
    """M3's fault: one threshold and ratio, on every band's detector.

    The gain computer shared across the split - a full-band compressor
    wearing a crossover - which is exactly the loss of isolation M3
    measures. Both of M3's clauses fire, on different rows: driving the low
    band pulls the other two down with it, and driving the mid or the high
    band does nothing at all.
    """

    def _apply_macro(self, index, position):
        if 2 <= index <= 7:
            for detector in self._detectors:
                detector.set(threshold_db=self.macro(2), ratio=self.macro(5))
        else:
            MultibandCompressor._apply_macro(self, index, position)


class LookaheadLatency(MultibandCompressor):
    """M4's fault: 128 samples of real delay, still reported as zero.

    `audiodynamics` has a lookahead this class deliberately does not expose;
    turning it on is the shortest way to make the class late without
    changing anything else.
    """

    LOOKAHEAD_SAMPLES = 128

    def _apply_macro(self, index, position):
        """The lookahead goes on with the last macro, not after `_build`.

        It has to land before the Mixer's voices take their first chunk, or
        the fault cannot reach the first 256 frames of the render and an
        impulse at frame 64 reads as undelayed on a build that is 128
        samples late. Re-playing the voices afterwards is not the same
        thing: that re-pulls the chain and costs the fault half its own
        delay (measured, 64 samples where 128 were asked for).
        """
        MultibandCompressor._apply_macro(self, index, position)
        if index == len(self.MACRO_LABELS) - 1:
            for detector in self._detectors:
                detector.set(lookahead_ms=((self.LOOKAHEAD_SAMPLES + 0.5)
                                           * 1000.0 / self._sample_rate))


class NoGuard(MultibandCompressor):
    """M5's fault: the Splitter fed straight off the source.

    This is the shipped class's topology (`dynamics.py:239`) and the defect
    the dossier's section 7 leads with.
    """

    def _build_input(self):
        self._guard = None
        return self._source


# --- rendering -------------------------------------------------------------

def tone(hz, rate, channels, seconds=SECONDS, amplitude=AMPLITUDE):
    frames = int(seconds * rate)
    step = 2.0 * math.pi * hz / rate
    values = array("h")
    for index in range(frames):
        value = int(round(amplitude * math.sin(step * index)))
        for _ in range(channels):
            values.append(value)
    return values


def raw(values, rate, channels):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def block_adapter(source, rate, channels, block):
    adapter = audiofilters.Filter(filter=None, mix=1,
                                  buffer_size=block * channels * 2,
                                  sample_rate=rate, bits_per_sample=16,
                                  samples_signed=True,
                                  channel_count=channels)
    adapter.play(source, loop=False)
    return adapter


def render(effect, frames, channels):
    out = bytearray()
    want = frames * channels * 2
    while len(out) < want:
        _result, buffer = audiocore.get_buffer(effect.output)
        data = bytes(buffer)
        if not data:
            break
        out.extend(data)
    return bytes(out[:want])


def build(cls, values, rate=RATE, channels=CHANNELS, block=None, **options):
    source = raw(values, rate, channels)
    if block is not None:
        source = block_adapter(source, rate, channels, block)
    return cls(source, sample_rate=rate, **options)


def render_tone(cls, hz, rate=RATE, channels=CHANNELS, solo=None,
                seconds=SECONDS, **options):
    """One steady tone through a fresh instance, as a kit `Render`.

    A fresh instance per tone, because a crossover that carried the previous
    tone's ring-down into this one would be measuring two things.  `solo`
    reaches past the macro surface to the Mixer's voice levels: there is no
    solo control on this class, and muting a band is what M2 and M3 need.
    """
    values = tone(hz, rate, channels, seconds)
    effect = build(cls, values, rate, channels, **options)
    if solo is not None:
        for voice in range(effect.bands + 1):
            effect._mixer.voice[voice].level = 1.0 if voice == solo else 0.0
    pcm = render(effect, len(values) // channels, channels)
    effect.deinit()
    return kit.Render(pcm, rate, channels, label="%g Hz" % hz,
                      class_name=cls.__name__, interpreter="cpython")


def dry_tone(hz, rate=RATE, channels=CHANNELS, seconds=SECONDS):
    values = tone(hz, rate, channels, seconds)
    return kit.Render(bytes(memoryview(values).cast("B")), rate, channels,
                      label="dry %g Hz" % hz, interpreter="cpython")


def sixth_octave(low, high):
    grid = []
    hz = float(low)
    while hz <= high * 1.0001:
        grid.append(round(hz, 3))
        hz *= 2.0 ** (1.0 / 6.0)
    return grid


UNITY = {"low_ratio": 1.0, "mid_ratio": 1.0, "high_ratio": 1.0,
         "low_gain_db": 0.0, "mid_gain_db": 0.0, "high_gain_db": 0.0,
         "mix": 1.0}


def sum_curve(cls, rate, grid, **options):
    wet = {}
    dry = {}
    for hz in grid:
        wet[hz] = render_tone(cls, hz, rate=rate, **options)
        dry[hz] = dry_tone(hz, rate=rate)
    return kit.response(wet, dry, reference_hz=grid[0])


def worst(result):
    values = [point["magnitude_db"] for point in result["values"]["grid"]]
    return min(values), max(values)


def verdict(label, ok, detail):
    print("    %-46s %-5s %s" % (label, "green" if ok else "RED", detail))
    if not ok:
        FAILURES.append(label)
    return ok


def expect_red(label, ok, detail):
    print("    %-46s %-5s %s" % (label, "RED" if not ok else "green", detail))
    if ok:
        FAILURES.append("the planted fault %s did not fire" % label)


# --- M1 --------------------------------------------------------------------

def m1(rate):
    print()
    print("M1  unity sum: flat within +-0.25 dB, 30 Hz to min(20k, 0.45 fs)")
    top = min(20000.0, 0.45 * rate)
    grid = sixth_octave(30.0, top)
    print("    %d tones, %g..%g Hz, %d Hz" % (len(grid), grid[0], grid[-1],
                                              rate))
    cases = (
        ("3 bands, 40/8000 (widest)",
         dict(bands=3, crossover_low_hz=40.0, crossover_high_hz=8000.0)),
        ("3 bands, 200/2000",
         dict(bands=3, crossover_low_hz=200.0, crossover_high_hz=2000.0)),
        ("3 bands, 800/800 -> clamped to 800/6400",
         dict(bands=3, crossover_low_hz=800.0, crossover_high_hz=800.0)),
        ("2 bands, 200", dict(bands=2, crossover_low_hz=200.0)),
        ("2 bands, 800", dict(bands=2, crossover_low_hz=800.0)),
        ("2 bands, 40", dict(bands=2, crossover_low_hz=40.0)),
    )
    for label, options in cases:
        settings = dict(UNITY)
        settings.update(options)
        result = sum_curve(MultibandCompressor, rate, grid, **settings)
        low, high = worst(result)
        verdict(label, max(abs(low), abs(high)) <= 0.25,
                "max %+.3f  min %+.3f dB" % (high, low))

    print("    planted fault: the ratio clamp removed, so 200/400 (2:1) is")
    print("    a legal setting - the trait is stated against that clamp.")
    print("    The 8:1 row is the CONTROL: the same faulted build at a legal")
    print("    ratio must be green, or the fault is just a broken class.")
    for ratio, label, expect in ((2.0, "2:1", False), (4.0, "4:1", False),
                                 (8.0, "8:1 (control)", True)):
        settings = dict(UNITY)
        settings.update(bands=3, crossover_low_hz=200.0,
                        crossover_high_hz=200.0 * ratio)
        result = sum_curve(NoRatioClamp, rate, grid, **settings)
        low, high = worst(result)
        ok = max(abs(low), abs(high)) <= 0.25
        line = "max %+.3f  min %+.3f dB" % (high, low)
        name = "NoRatioClamp at %s (200/%d Hz)" % (label, 200 * ratio)
        if expect:
            verdict(name, ok, line)
        else:
            expect_red(name, ok, line)


# --- M2 --------------------------------------------------------------------

def m2(rate):
    print()
    print("M2  each crossover is -6 dB at its corner with a 24 dB/octave")
    print("    skirt, and the two halves are in phase there")
    grid = sixth_octave(30.0, min(20000.0, 0.45 * rate))
    settings = dict(UNITY)
    settings.update(bands=3, crossover_low_hz=200.0,
                    crossover_high_hz=2000.0)

    for cls, name in ((MultibandCompressor, "LR4, the class"),
                      (LinkwitzRiley2, "LR2, the planted fault")):
        print("    %s" % name)
        for band, corner, span, direction in (
                (1, 200.0, (400.0, 800.0), "low band, above"),
                (3, 2000.0, (500.0, 1000.0), "high band, below")):
            wet = {}
            dry = {}
            for hz in grid:
                wet[hz] = render_tone(cls, hz, rate=rate, solo=band,
                                      **settings)
                dry[hz] = dry_tone(hz, rate=rate)
            reference = 40.0 if band == 1 else 8000.0
            result = kit.response(wet, dry, reference_hz=reference,
                                  slope_octave=span)
            at_corner = kit._interpolate_log(
                [p["hz"] for p in result["values"]["grid"]],
                [p["magnitude_db"] for p in result["values"]["grid"]],
                corner) - result["values"]["passband_db"]
            slope = result["values"]["slope_db_per_octave"]
            ok = (abs(at_corner + 6.0) <= 0.5
                  and slope is not None and abs(abs(slope) - 24.0) <= 2.0)
            line = ("%s: corner %+.2f dB, skirt %.1f dB/octave"
                    % (direction, at_corner, abs(slope or 0.0)))
            if cls is MultibandCompressor:
                verdict("  %s" % direction, ok, line)
            else:
                expect_red("  %s" % direction, ok, line)

        print("      the sum at each corner (in phase, no null):")
        for corner in (200.0, 2000.0):
            wet = {}
            dry = {}
            for hz in (corner / 1.05, corner, corner * 1.05):
                wet[hz] = render_tone(cls, hz, rate=rate, **settings)
                dry[hz] = dry_tone(hz, rate=rate)
            result = kit.response(wet, dry, reference_hz=corner)
            at_corner = result["values"]["passband_db"]
            ok = abs(at_corner) <= 0.25
            if cls is MultibandCompressor:
                verdict("  sum at %g Hz" % corner, ok,
                        "%+.3f dB" % at_corner)
            else:
                expect_red("  sum at %g Hz" % corner, ok,
                           "%+.3f dB" % at_corner)


# --- M3 --------------------------------------------------------------------

#: Where each band is measured: inside its own passband, no closer than an
#: octave to either of its corners. Closer in, the band's own LR4 skirt has
#: taken it below unity, and a fixed threshold then buys less reduction than
#: it does in the middle - 0.53 dB down one octave inside a corner is 0.40 dB
#: less reduction at ratio 4. That is arithmetic, and it is inside M3's tilt
#: bar; it is stated here rather than hidden by a narrower window.
BAND_TONES = {
    0: (30.0, 45.0, 63.0, 80.0, 100.0),
    1: (400.0, 566.0, 700.0, 900.0, 1000.0),
    2: (4000.0, 5600.0, 8000.0, 11300.0, 16000.0),
}


def m3(rate):
    print()
    print("M3  band isolation: 12 dB on one band, +-0.5 dB on the others")
    print("    Read per band, SOLOED, not off the sum. On the sum a")
    print("    neighbour's LR4 skirt fills in what the driven band gave up:")
    print("    measured, the low band 12 dB down reads -10.4 dB at 100 Hz in")
    print("    the summed output, because the mid band is only 24.6 dB down")
    print("    there. That is the crossover's arithmetic, not the class's")
    print("    isolation, and a per-band read is what M3's words describe.")
    base = dict(UNITY)
    base.update(bands=3, crossover_low_hz=200.0, crossover_high_hz=2000.0)

    level_db = 20.0 * math.log10(AMPLITUDE / math.sqrt(2.0) / 32768.0)
    ratio = 4.0
    threshold = level_db - 12.0 / (1.0 - 1.0 / ratio)
    print("    the probe tone sits at %.2f dBFS RMS; threshold %.2f dB at "
          "ratio %g asks for 12 dB" % (level_db, threshold, ratio))

    idle = {}
    for band, tones in BAND_TONES.items():
        for hz in tones:
            idle[(band, hz)] = render_tone(MultibandCompressor, hz,
                                           rate=rate, solo=band + 1, **base)

    names = ("low", "mid", "high")
    for cls, label in ((MultibandCompressor, "the class"),
                       (SharedDetector,
                        "the planted fault: one threshold and ratio on "
                        "every detector")):
        print("    %s" % label)
        for driven in (0, 1, 2):
            options = dict(base)
            options[names[driven] + "_threshold_db"] = threshold
            options[names[driven] + "_ratio"] = ratio
            deltas = {}
            for band, tones in BAND_TONES.items():
                for hz in tones:
                    wet = render_tone(cls, hz, rate=rate, solo=band + 1,
                                      **options)
                    reference = idle[(band, hz)]
                    a = kit.tone_bin(wet.float[wet.frames // 2:, 0], rate, hz)
                    b = kit.tone_bin(
                        reference.float[reference.frames // 2:, 0], rate, hz)
                    deltas[(band, hz)] = (kit.db(abs(a) / abs(b))
                                          if abs(b) else 0.0)
            inside = [deltas[(driven, hz)] for hz in BAND_TONES[driven]]
            others = [deltas[(band, hz)] for band in BAND_TONES
                      if band != driven for hz in BAND_TONES[band]]
            reduction = sum(inside) / len(inside)
            tilt = max(inside) - min(inside)
            leak = max(abs(value) for value in others)
            print("      %-4s driven, per tone: %s"
                  % (names[driven],
                     "  ".join("%.0f:%+.2f" % (hz, deltas[(driven, hz)])
                               for hz in BAND_TONES[driven])))
            depth_ok = abs(reduction + 12.0) <= 0.5
            even_ok = tilt <= 0.5
            leak_ok = leak <= 0.5
            line = ("mean %+.2f dB, tilt %.2f dB, worst other band %+.2f dB"
                    % (reduction, tilt, leak))
            if cls is MultibandCompressor:
                verdict("  %s: depth" % names[driven], depth_ok, line)
                verdict("  %s: evenness" % names[driven], even_ok,
                        "tilt %.2f dB across %g..%g Hz"
                        % (tilt, BAND_TONES[driven][0],
                           BAND_TONES[driven][-1]))
                verdict("  %s: isolation" % names[driven], leak_ok,
                        "worst other band %+.2f dB" % leak)
            else:
                expect_red("  %s (fault)" % names[driven],
                           depth_ok and even_ok and leak_ok, line)
    _m3_causes(rate, base, threshold, ratio)


def _m3_causes(rate, base, threshold, ratio):
    """Where the low band's tilt comes from, measured rather than argued.

    Two effects, and they pull the same way. The band's own LR4 skirt is
    0.53 dB down an octave inside its corner, and a fixed threshold buys
    (1 - 1/ratio) x 0.53 = 0.40 dB less reduction there. Below about 50 Hz
    the RMS detector's 10 ms window is shorter than one period of the tone,
    so its envelope ripples and the gain follows it - lengthening the window
    to 30 ms is the control that isolates that half.
    """
    print("    where the low band's tilt comes from:")
    driven = dict(base)
    driven.update(low_threshold_db=threshold, low_ratio=ratio)
    for window in (None, 30.0):
        row = []
        for hz in BAND_TONES[0]:
            wet = _low_band(hz, rate, driven, window)
            reference = _low_band(hz, rate, base, window)
            a = kit.tone_bin(wet.float[wet.frames // 2:, 0], rate, hz)
            b = kit.tone_bin(reference.float[reference.frames // 2:, 0],
                             rate, hz)
            row.append((hz, kit.db(abs(a) / abs(b)) if abs(b) else 0.0))
        print("      rms_ms %-6s %s   tilt %.2f dB"
              % ("(default 10)" if window is None else window,
                 "  ".join("%.0f:%+.2f" % entry for entry in row),
                 max(v for _hz, v in row) - min(v for _hz, v in row)))


def _low_band(hz, rate, settings, window):
    values = tone(hz, rate, CHANNELS)
    effect = build(MultibandCompressor, values, rate, CHANNELS, **settings)
    if window is not None:
        effect._detectors[0].set(rms_ms=window)
        effect._mixer.play(effect._detectors[0], voice=1, loop=True)
    for voice in range(effect.bands + 1):
        effect._mixer.voice[voice].level = 1.0 if voice == 1 else 0.0
    pcm = render(effect, len(values) // CHANNELS, CHANNELS)
    effect.deinit()
    return kit.Render(pcm, rate, CHANNELS, interpreter="cpython")


# --- M4 --------------------------------------------------------------------

def m4(rates):
    print()
    print("M4  zero latency: the impulse leaves in the frame it entered")
    for rate in rates:
        for label, options in (
                ("3 bands, 200/2000",
                 dict(bands=3, crossover_low_hz=200.0,
                      crossover_high_hz=2000.0)),
                ("3 bands, 40/8000",
                 dict(bands=3, crossover_low_hz=40.0,
                      crossover_high_hz=8000.0)),
                ("2 bands, 200", dict(bands=2, crossover_low_hz=200.0))):
            for cls, expect in ((MultibandCompressor, True),
                                (LookaheadLatency, False)):
                values = array("h")
                for index in range(64 + 1 + int(0.2 * rate)):
                    value = 24000 if index == 64 else 0
                    for _ in range(CHANNELS):
                        values.append(value)
                effect = build(cls, values, rate, CHANNELS, mix=1.0,
                               **options)
                pcm = render(effect, len(values) // CHANNELS, CHANNELS)
                reported = effect.latency_samples
                effect.deinit()
                wet = kit.Render(pcm, rate, CHANNELS, interpreter="cpython")
                dry = kit.Render(bytes(memoryview(values).cast("B")), rate,
                                 CHANNELS, interpreter="cpython")
                result = kit.click(wet, dry, reported, subsample=False,
                                   tolerance_samples=0.0)
                line = ("%d Hz %s: reported %d, measured %s"
                        % (rate, label, reported,
                           result["values"]["measured_latency_samples"]))
                if expect:
                    verdict("  %d Hz %s" % (rate, label), result["passed"],
                            line)
                else:
                    expect_red("  fault: %d samples of lookahead, still "
                               "reported 0" % cls.LOOKAHEAD_SAMPLES,
                               result["passed"], line)


# --- M5 --------------------------------------------------------------------

def m5(rate):
    print()
    print("M5  the sum survives its source: identical bytes at every block")
    grid = (256, 8192, 16384, 20000, 32768)
    values = tone(220.0, rate, CHANNELS, seconds=0.75, amplitude=20000)
    frames = len(values) // CHANNELS
    for cls, expect in ((MultibandCompressor, True), (NoGuard, False)):
        digests = []
        for block in grid:
            effect = build(cls, values, rate, CHANNELS, block=block,
                           bands=3, mix=1.0)
            pcm = render(effect, min(frames, 8192), CHANNELS)
            effect.deinit()
            render_object = kit.Render(pcm, rate, CHANNELS, block=block,
                                       interpreter="cpython")
            digests.append((block, "%08x" % render_object.digest,
                            0 if render_object.is_silent else 1))
        identical = len(set(entry[1] for entry in digests)) == 1
        alive = all(entry[2] for entry in digests)
        line = "  ".join("%d:%s%s" % (block, digest,
                                      "" if live else " SILENT")
                         for block, digest, live in digests)
        if expect:
            verdict("  the class", identical and alive, line)
        else:
            expect_red("  fault: the guard removed", identical and alive,
                       line)

    # the burst-then-silence material the dossier's A-M5 used, which is what
    # turns the drop from a time shift into an erasure
    print("    the same ladder on burst-then-silence material (A-M5):")
    burst = array("h")
    body = tone(440.0, rate, CHANNELS, seconds=0.04, amplitude=24000)
    burst.extend(body)
    for _ in range(int(0.6 * rate)):
        for _ in range(CHANNELS):
            burst.append(0)
    for cls, expect in ((MultibandCompressor, True), (NoGuard, False)):
        counts = []
        for block in grid:
            effect = build(cls, burst, rate, CHANNELS, block=block, bands=3,
                           mix=1.0)
            pcm = render(effect, len(burst) // CHANNELS, CHANNELS)
            effect.deinit()
            render_object = kit.Render(pcm, rate, CHANNELS, block=block)
            counts.append((block,
                           int((render_object.data != 0).sum())))
        alive = all(count for _block, count in counts)
        line = "  ".join("%d:%d" % entry for entry in counts)
        if expect:
            verdict("  the class, burst material", alive, line)
        else:
            expect_red("  fault: the guard removed, burst material", alive,
                       line)


def main():
    print("MultibandCompressor Tier 2 traits, CPython, audioif at the pin")
    print("=" * 72)
    m1(RATE)
    m2(RATE)
    m3(RATE)
    m4((48000, 44100))
    m5(RATE)
    print()
    print("=" * 72)
    for line in FAILURES:
        print("FAILED  %s" % line)
    print("%d failing rows" % len(FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
