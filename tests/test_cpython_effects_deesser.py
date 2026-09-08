"""`DeEsser`'s own invariant, trait and planted-fault battery.

The class gate (`docs/effects-roadmap.md`, "The class gate") asks for two
things this file carries: the Tier 1 invariants green on CPython at 48 kHz
and at `channel_count` 1, and every demonstrated Tier 2 trait shown **red
on a planted fault of the same kind**. Three-rate, three-interpreter
coverage is the evidence pack's, not this suite's
(`workspace docs/effects-internal/evidence/DeEsser-evidence.md`); run with
`-v` and the readouts appear beside each test.

Structure, so a reader can find one thing:

* `Tier1` - WIRE, LEVEL, TAIL, CLICK, STATE, rate honesty, mono.
* `Tier2` - D1 and D3 through D8, each with the dossier's own criterion.
* `PlantedFaults` - each measurement above driven by a deliberately broken
  build, and required to go red. A checker that has only ever passed has not
  been shown to work.

The analysis is `tools/effect_measurements.py`, which is numpy and CPython;
the MicroPython and CircuitPython legs render through
`tools/render_effect.py` and are analysed here, which is the kit spec's
split (section 1, "the render is dual-runtime; the analysis is not").
"""

import array
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))

import audiocore                                          # noqa: E402
from audioeffects import deesser                  # noqa: E402
#: The subject is named directly. `DeEsser` has come home to
#: `audioeffects/deesser.py`; `rebuilt.ADOPTED` no longer lists it. These
#: tests still import the home module so a planted-fault subclass is
#: measured against this file, not only `create()`. The G2 cell it was
#: parked on - 22.05 kHz never rendered on either native build - is closed
#: (`DeEsser-evidence.md` section 2); G6 is not, and the fixer pass measured
#: why no `" - lean"` patch can close it (section 4).
import effect_measurements as M                           # noqa: E402
from audioeffects import _component                        # noqa: E402
sys.path.insert(0, os.path.join(HERE, "support"))
import kit_faults as F                                     # noqa: E402

#: `_component` reads `VENDOR` off the module a class is *defined* in, and
#: the two faults below are subclasses of a rebuilt class. Without this the
#: metadata check refuses them before they can be measured - a fault that
#: cannot be built is a fault that cannot fail.
VENDOR = "PyDevices"

PROBES = os.path.join(os.path.dirname(HERE), "tools", "effect_probes")
#: Unit tests render at one rate. 44.1 kHz and 22.05 kHz stay in the
#: evidence pack (`tools/compressor_evidence.py`-style probes, all three
#: interpreters). The Nyquist clamp test is the exception and keeps `RATES`.
RATE = 48000
RATES = (48000, 44100, 22050)
#: `settled_change` reads 4800 frames from the midpoint. 16384 frames is
#: 341 ms at 48 kHz: past the attack (a few ms) and long enough for that
#: window. Not used for a tail, a release, or a settling-time row.
SETTLED_FRAMES = 16384
#: STATE pulls 32 blocks three times, 2 warm blocks, then 200 single-block
#: alloc pulls. The source must outlast that or the alloc leg is silence.
STATE_FRAMES = 32 * 256 * 3 + 2 * 256 + 200 * 256 + 256

#: The Frequency-macro fault. The corner is forced to 500 Hz - **below the
#: macro's own 800 Hz floor**, which is what makes it a fault and not a
#: setting: `fault_reachability` walks the 0-127 grid and every shipped
#: patch and cannot dial it (`FrozenCrossover` in `KitChecks`).
FROZEN_CORNER_HZ = 500.0

#: The two patches that ship in HF-only mode. D1's level independence is
#: recorded disconfirmed at both: the crossover is in the audio path there,
#: and the low band it leaves alone carries no reduction, so the balance the
#: detector reads moves with the programme level in a way broadband mode's
#: single stream does not. Measured in `PatchSweep`.
DEESS_HF_ONLY_PATCHES = (3, 4)

#: The Release-macro fault, as a multiplier on what the class pushes into
#: the node. 250 puts every position of the 1-200 ms span past 200 ms, so
#: no Release setting reaches the state the fault forces.
SLOW_RELEASE_SCALE = 250.0


# --------------------------------------------------------------------------
# Rig


def probe(name, rate, channels=2, frames=None):
    """One of the kit's own probes, as an int16 array.

    `frames` takes a prefix. The kit probes hold one balance for their
    whole length, so a settled spectral reading on the first third is the
    same measurement as on the whole file; a tail or a release still
    loads the file through.
    """
    path = os.path.join(PROBES, str(rate), "%dch" % channels, name + ".wav")
    with open(path, "rb") as handle:
        data = handle.read()
    at = 12
    while at < len(data):
        chunk, size = data[at:at + 4], int.from_bytes(data[at + 4:at + 8],
                                                      "little")
        if chunk == b"data":
            values = array.array("h", data[at + 8:at + 8 + size])
            if frames is not None:
                values = values[:frames * channels]
            return values
        at += 8 + size + (size & 1)
    raise ValueError("no data chunk in %s" % path)


def tone(hz, amplitude, frames, rate, channels=2):
    values = array.array("h")
    for frame in range(frames):
        sample = int(round(amplitude * math.sin(2 * math.pi * hz * frame
                                                / rate)))
        for _ in range(channels):
            values.append(sample)
    return values


def silence(frames, channels=2):
    return array.array("h", bytes(frames * 2 * channels))


def source(values, rate, channels=2):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def render(node, frames, rate, channels=2, **axes):
    """Pull `frames` frames and wrap them as a kit `Render`."""
    got = bytearray()
    want = frames * 2 * channels
    while len(got) < want:
        _result, data = audiocore.get_buffer(node, False, 0)
        block = bytes(data)
        if not block:
            break
        got += block
    return M.Render.from_pcm(bytes(got[:want]), rate, channels,
                             interpreter="cpython", **axes)


def build(rate=48000, channels=2, values=None, frames=None, **options):
    """A DeEsser over `values`, through the contract's own boundary."""
    if values is None:
        values = tone(1000, 12000, frames or 8192, rate, channels)
    holder = source(values, rate, channels)
    effect = deesser.DeEsser.create(holder, rate, **options)
    return effect, holder


def band_db(values, hz, rate, channels, first, count, channel=0):
    """One frequency's magnitude in dBFS, by a direct DFT bin.

    A bin rather than an FFT because the probe tones are not on an FFT
    grid at every rate, and a windowed FFT would blur the 200 Hz and 6 kHz
    components of the sibilant probe into each other's skirts.
    """
    angular = 2.0 * math.pi * hz / rate
    real = imaginary = 0.0
    for step in range(count):
        sample = values[(first + step) * channels + channel]
        real += sample * math.cos(angular * step)
        imaginary -= sample * math.sin(angular * step)
    magnitude = 2.0 * math.hypot(real, imaginary) / count
    return 20.0 * math.log10(max(magnitude, 1e-9) / 32768.0)


def sibilant_burst(rate, low_hz=200.0, high_hz=6000.0, seconds=1.5,
                   burst=(0.5, 1.0), low_lsb=11000, high_lsb=2750,
                   channels=2):
    """A steady low tone with a high-frequency burst laid over part of it.

    The kit's `sibilant_*` probes hold one balance for their whole length,
    which is what D1 and D7 need and exactly what D4 and D5 cannot use: a
    gain trace needs the *edges*, and it needs signal still present after
    the sibilant stops or there is nothing to read the recovery from. This
    is that probe - the low tone runs throughout, the high tone switches on
    at `burst[0]` and off at `burst[1]`.
    """
    frames = int(seconds * rate)
    first, last = int(burst[0] * rate), int(burst[1] * rate)
    values = array.array("h")
    for frame in range(frames):
        sample = low_lsb * math.sin(2 * math.pi * low_hz * frame / rate)
        if first <= frame < last:
            sample += high_lsb * math.sin(2 * math.pi * high_hz * frame
                                          / rate)
        word = max(-32768, min(32767, int(round(sample))))
        for _ in range(channels):
            values.append(word)
    return values


def fraction_ms(trace, times, begin, end, fraction):
    """When the trace has covered `fraction` of the way from `begin` to
    `end`. The kit's own `_fraction_ms`, reached through a public name so
    this file does not read a private."""
    return M._fraction_ms(trace, times, begin, end, fraction)


def deess(rate, probe_name, seconds=None, **options):
    """Render one sibilant probe through the class and hand back both
    halves, so a trait can compare them band by band."""
    values = probe(probe_name, rate, frames=SETTLED_FRAMES)
    effect, _holder = build(rate=rate, values=values, **options)
    frames = len(values) // 2
    wet = render(effect.output, frames, rate, probe=probe_name)
    effect.deinit()
    return values, wet, frames


def reduction_at(probe_name, macros, hz=6000, rate=48000, cls=None,
                 post=None, **options):
    """One probe's settled band change, with the macros driven onto the
    instance rather than handed to the constructor.

    Driving the macros is the discipline the pattern revision's section 3
    asks for and the thing D2's fault needs: a setting reached through
    `create(...)` never passes through `_apply_macro`, so a fault planted
    there would not be in the path.
    """
    values = probe(probe_name, rate, frames=SETTLED_FRAMES)
    holder = source(values, rate, 2)
    effect = (cls or deesser.DeEsser).create(holder, rate, **options)
    for index, position in macros.items():
        effect.set_macro(index, position)
    if post is not None:
        post(effect)
    frames = len(values) // 2
    wet = render(effect.output, frames, rate)
    got = settled_change(values, wet, frames, hz, rate)
    effect.deinit()
    return got


def settled_change(values, wet, frames, hz, rate):
    """A band's change in dB, measured over a window in the settled middle
    of the render rather than across the attack."""
    count = min(4800, frames // 4)
    first = frames // 2
    return (band_db(wet.data.reshape(-1).tolist(), hz, rate, 2, first, count)
            - band_db(values, hz, rate, 2, first, count))


# --------------------------------------------------------------------------
# The two faults that live in the class rather than in a live instance


class FrozenCrossover(deesser.DeEsser):
    """D2's fault: the Frequency macro moves, the filters do not.

    Both corners - the audio pair and the detector's side chain - are forced
    to `FROZEN_CORNER_HZ` after every macro move, so `macro(0)` reports what
    the player asked for and the class does something else. This is the
    fault the refutation pass found D2's old test could not see, because
    that test read HF-only mode's *sum*, which is flat at every corner.
    """

    def _apply_macro(self, index, position):
        deesser.DeEsser._apply_macro(self, index, position)
        if index == 0:
            corner = self._hz(FROZEN_CORNER_HZ)
            for node in self._lows:
                node.frequency = corner
            for node in self._highs:
                node.frequency = corner
            self._duck.set(sidechain_hz=corner * deesser._DETECTOR_CORNER)


class SlowRelease(deesser.DeEsser):
    """D4's fault: the Release macro pushed into the node scaled by
    `SLOW_RELEASE_SCALE` - a units bug, ms read as something else.

    It is a fault and not a setting because the smallest value it can force
    (1 ms x 250) is past the top of the macro's own 1-200 ms span, so no
    Release position reaches it.
    """

    def _apply_macro(self, index, position):
        deesser.DeEsser._apply_macro(self, index, position)
        if index == 4:
            value = _component.macro_value(self._MACRO_RANGES[4], position)
            self._duck.set(release_ms=value * SLOW_RELEASE_SCALE)


# --------------------------------------------------------------------------
# The two measurements the gate audit sent back, each rebuilt so it can fail


def listen_band_db(cls, corner_position, hz, rate=48000):
    """One point of the detector's own band, through the Listen path.

    Listen puts the detector's side chain on the output at unity, which is
    the only place on this class's public surface where a single filtered
    band is audible on its own: HF-only mode *sums* the two halves, and a
    Linkwitz-Riley pair sums flat at every corner, which is why the old D2
    reading could not fail.

    The corner is reached with `set_macro`, never with the constructor, so
    a fault in `_apply_macro` is in the path.
    """
    values = tone(hz, 12000, SETTLED_FRAMES, rate)
    holder = source(values, rate, 2)
    effect = cls.create(holder, rate, listen=True, sensitivity_db=0.0,
                        range_db=20.0)
    effect.set_macro(0, corner_position)
    wet = render(effect.output, SETTLED_FRAMES, rate)
    got = settled_change(values, wet, SETTLED_FRAMES, hz, rate)
    effect.deinit()
    return got


def extracted_corner_hz(cls, corner_position, rate=48000):
    """The detector band's -3 dB corner, from two points of its own shape.

    `sidechain_poles=2` is a cascade of two one-poles, magnitude
    `w^2 / (w^2 + wc^2)`, so a reading at `f1` and one at `f2` fix `wc`
    without knowing the path's broadband gain - and the gain is exactly what
    the old reading could not separate from the corner. With
    `r = |H(f1)| / |H(f2)|`,

        wc^2 = f1^2 f2^2 (1 - r) / (r f2^2 - f1^2)

    and the -3 dB point is `1.5538 * wc`, which is where
    `_DETECTOR_CORNER` puts the commanded Frequency.

    Returns `(commanded_hz, extracted_hz, error_percent)`. On a build that
    does not filter at all (`r = 1`, a wire) the extraction returns 0 Hz,
    which is -100 % and red - that is the null-build check passing.
    """
    holder = source(tone(200, 100, 512, rate), rate, 2)
    reader = cls.create(holder, rate)
    reader.set_macro(0, corner_position)
    commanded = reader.macro(0)
    reader.deinit()
    f1, f2 = commanded / 2.0, commanded * 2.0
    ratio = 10.0 ** ((listen_band_db(cls, corner_position, f1, rate)
                      - listen_band_db(cls, corner_position, f2, rate))
                     / 20.0)
    denominator = ratio * f2 * f2 - f1 * f1
    if denominator <= 0.0:
        extracted = float("inf")
    else:
        squared = (f1 * f1 * f2 * f2) * (1.0 - ratio) / denominator
        extracted = math.sqrt(squared) * 1.5537739740300374 if squared > 0 \
            else 0.0
    return commanded, extracted, 100.0 * (extracted - commanded) / commanded


def _mute_the_gain_cell(effect):
    """The output mixer's wet voice at zero: the dry blend on its own, with
    no detector and no gain cell in the sum. What is left is
    `(1 - alpha) * x` through the same two int16 mixer voices the class
    uses, which is the floor any reduction it reports is measured against.
    """
    effect._out.voice[3].level = 0.0


def _corner_cell(cls, position, rate):
    """One cell of D2's sweep, in the kit's result shape."""
    commanded, extracted, error = extracted_corner_hz(cls, position, rate)
    return {"values": {"commanded_hz": commanded, "extracted_hz": extracted,
                       "error_percent": error}}


def release_rate_db_s(cls, hop_ms=2.5, seconds=3.0, rate=48000,
                      release_from_ms=1000.0):
    """The release, as the dB/sec the 902's spec sheet states it in.

    Returns a kit-shaped result so `null_build_red` can read it: `passed`
    is False when the recovery never completes inside the render, which is
    what a wire and a 875 ms release both do.
    """
    values = sibilant_burst(rate, low_hz=200.0, seconds=seconds,
                            burst=(0.5, 1.0))
    holder = source(values, rate, 2)
    effect = cls.create(holder, rate, range_db=12.0, sensitivity_db=30.0)
    frames = len(values) // 2
    wet = render(effect.output, frames, rate)
    dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
    trace = M.gaintrace(wet, dry, hop_ms=hop_ms,
                        release_from_ms=release_from_ms)
    effect.deinit()
    rows = trace["values"]
    t95 = rows["release_t95_ms"]
    values_out = {"rate_db_s": None, "covered_db": None, "depth_db": None,
                  "window_ms": None, "straightness_db": None,
                  "hop_ms": hop_ms}
    if t95 is None:
        return {"name": "D4", "values": values_out, "passed": False,
                "red": ["no release completed inside the render"]}
    marks = [(t, g) for t, g in zip(rows["trace_ms"], rows["trace_gr_db"])
             if g is not None and release_from_ms <= t <= release_from_ms + t95]
    stamps = [t for t, _g in marks]
    series = [g for _t, g in marks]
    span = stamps[-1] - stamps[0]
    if span <= 0.0:
        return {"name": "D4", "values": values_out, "passed": False,
                "red": ["the release window is shorter than one hop"]}
    straight = [series[0] + (series[-1] - series[0]) * (t - stamps[0]) / span
                for t in stamps]
    covered = abs(series[-1] - series[0])
    values_out.update({"rate_db_s": covered / (span / 1000.0),
                       "covered_db": covered, "depth_db": abs(series[0]),
                       "window_ms": span,
                       "straightness_db": max(abs(a - b) for a, b
                                              in zip(series, straight))})
    off = abs(values_out["rate_db_s"] - 925.0) / 925.0
    values_out["percent_off_925"] = 100.0 * off
    return {"name": "D4", "values": values_out, "passed": off <= 0.10,
            "red": ([] if off <= 0.10 else
                    ["%.0f dB/sec is %.1f %% off the 902's 925"
                     % (values_out["rate_db_s"], 100.0 * off)])}


# --------------------------------------------------------------------------


class Tier1(unittest.TestCase):
    """The standard invariant block, on CPython, at 48 kHz.

    44.1 kHz and 22.05 kHz are in the evidence pack, not duplicated here.
    """

    def test_wire_at_range_zero_is_byte_identical(self):
        """WIRE. Range 0 in broadband mode is the class's `mix` at zero,
        and the dossier's section 8.2 is why it is exact: broadband mode
        carries no audio split, so there is nothing to sum.

        One rate: identity is not a rate-handling claim. `ramp_fs` is
        already 0.5 s, which is the length the kit built to expose a
        1-LSB dry-path fault.
        """
        rate = RATE
        values = probe("ramp_fs", rate)
        effect, _holder = build(rate=rate, values=values, range_db=0.0)
        frames = len(values) // 2
        wet = render(effect.output, frames, rate)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
        result = M.wire(wet, dry, latency_samples=0)
        effect.deinit()
        print("\n  WIRE %5d Hz: %s" % (rate, result["values"]))
        self.assertEqual(result["red"], [], "%d Hz" % rate)

    def test_level_is_honest_with_no_sibilance(self):
        """LEVEL. A tone below the split, with nothing for the detector to
        find, comes through at unity.

        16384 frames with a 2048-frame skip is 0.3 s of settled tone; LEVEL
        is an RMS, not a tail.
        """
        rate = RATE
        values = tone(200, 12000, SETTLED_FRAMES, rate)
        effect, _holder = build(rate=rate, values=values)
        wet = render(effect.output, SETTLED_FRAMES, rate)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
        result = M.level(wet, dry, tolerance_db=0.05, skip_frames=2048)
        effect.deinit()
        print("\n  LEVEL %5d Hz: %s" % (rate, result["values"]))
        self.assertEqual(result["red"], [], "%d Hz" % rate)

    def test_tail_reaches_exact_zero(self):
        """TAIL. Burst then silence: the crossover's state has to reach
        exact zero, which is what `audiobiquad` exists for.

        Full `burst_silence` (3.2 s): this row *is* the tail.
        """
        rate = RATE
        values = probe("burst_silence", rate)
        effect, _holder = build(rate=rate, values=values)
        frames = len(values) // 2
        wet = render(effect.output, frames, rate)
        burst_end = int(0.2 * rate)
        result = M.tail(wet, burst_end_frame=burst_end,
                        declared_tail_samples=effect.tail_samples)
        effect.deinit()
        print("\n  TAIL %5d Hz: %s" % (rate, result["values"]))
        self.assertEqual(result["red"], [], "%d Hz" % rate)

    def test_tail_in_hf_only_mode_is_the_crossover(self):
        """TAIL again, on the path that actually has one: broadband never
        puts the audio through a filter, so the declared `tail_samples` has
        to be read against HF-only mode at the bottom of the Frequency
        span, where the Butterworth pair rings longest.

        Three corners at one rate; the length is the tail probe. Three-rate
        coverage of this row is in the evidence pack.
        """
        rate = RATE
        for corner in (800.0, 2500.0, 8000.0):
            values = probe("burst_silence", rate)
            effect, _holder = build(rate=rate, values=values,
                                    hf_only=True, frequency=corner)
            frames = len(values) // 2
            wet = render(effect.output, frames, rate)
            result = M.tail(wet, burst_end_frame=int(0.2 * rate),
                            declared_tail_samples=effect.tail_samples)
            effect.deinit()
            print("\n  TAIL hf-only %5d Hz corner %6.0f: %s"
                  % (rate, corner, result["values"]))
            self.assertEqual(result["red"], [])

    def test_latency_is_zero_at_every_rate(self):
        """CLICK. The reported `latency_samples` against the measured
        click delay.

        One rate: latency 0 is not a coefficient-per-rate claim. 8192
        frames is 171 ms, longer than a block and long enough to place an
        impulse; the 3 s kit impulse is leftover length, not the
        measurement. 22.05 kHz stays in the evidence pack (G2).
        """
        rate = RATE
        values = probe("impulse", rate)
        effect, _holder = build(rate=rate, values=values, range_db=0.0)
        frames = min(len(values) // 2, 8192)
        wet = render(effect.output, frames, rate)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
        result = M.click(wet, dry, effect.latency_samples)
        effect.deinit()
        print("\n  CLICK %5d Hz: %s" % (rate, result["values"]))
        self.assertEqual(result["red"], [], "%d Hz" % rate)

    def test_reset_and_deinit_and_capabilities(self):
        """STATE. The reset walk, the deinit walk, `capabilities`, and the
        no-allocation rule.

        `nodes` is passed explicitly. `M.enumerate_nodes` reads an effect's
        *public* attributes, and every node this class owns is private, so
        left to itself the deinit leg would hold an empty list and pass
        vacuously - the shape of failure this workspace calls
        absence-reading-as-agreement. The list handed over is the class's
        own `_nodes`, minus the three `audioroute.Splitter`s, which have no
        `deinit` on any target and so can never be shown deinitialised.

        One rate, both channel counts. The source is `STATE_FRAMES` of
        `noise_det`, which is what the pulls consume; the 4 s file was
        leftover from G2's three-rate row, not from the measurement.
        """
        rate = RATE
        for channels in (2, 1):
            values = probe("noise_det", rate, channels=channels,
                           frames=STATE_FRAMES)
            effect, holder = build(rate=rate, channels=channels,
                                   values=values)
            frames = (len(values) // channels)
            quiet = source(silence(frames, channels), rate,
                           channels=channels)
            nodes = [("node%d" % index, node)
                     for index, node in enumerate(effect._nodes)
                     if hasattr(node, "_get_buffer")]
            # Read before `M.state` runs: its last act is `deinit()`,
            # after which every property on the live surface raises.
            self.assertEqual(effect.capabilities, ())
            result = M.state(
                effect,
                pull=lambda blocks, r=rate, c=channels: render(
                    effect.output, blocks * 256, r, channels=c),
                swap=lambda new: effect._adapter.play(new),
                probe_source=holder, silent_source=quiet, blocks=32,
                nodes=nodes)
            print("\n  STATE %5d Hz %dch: %s"
                  % (rate, channels, result["values"]))
            self.assertEqual(result["red"], [],
                             "%d Hz %dch" % (rate, channels))

    def test_mono_gets_the_same_processing(self):
        """The invariants also hold at `channel_count` 1, and the dossier's
        section 4 says a mono source gets identical processing.

        One rate; `ramp_fs` is already the short identity probe.
        """
        rate = RATE
        values = probe("ramp_fs", rate, channels=1)
        effect, _holder = build(rate=rate, channels=1, values=values,
                                range_db=0.0)
        frames = len(values)
        wet = render(effect.output, frames, rate, channels=1)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 1)
        result = M.wire(wet, dry, latency_samples=0)
        print("\n  MONO WIRE %5d Hz: %s" % (rate, result["values"]))
        self.assertEqual(result["red"], [], "%d Hz" % rate)
        self.assertEqual(effect.channel_count, 1)
        effect.deinit()

    def test_frequency_clamps_below_nyquist_rather_than_refusing(self):
        """Rate honesty. The Frequency span tops at 8 kHz, which is below
        Nyquist at every rate the gate names, so it never clamps - and the
        clamp is still shown to exist, by asking for more than the rate
        has.

        This row *is* about rate handling (`_hz` warps the ceiling per
        rate), so it keeps the three-rate loop.
        """
        for rate in RATES:
            effect, _holder = build(rate=rate)
            effect.set_macro(0, 127)
            self.assertLessEqual(effect.macro(0), 8000.0 + 1e-6)
            self.assertAlmostEqual(effect._hz(1e9),
                                   rate * 0.5 * 0.98, places=6)
            print("\n  RATE %5d Hz: top of span %.1f Hz, ceiling %.1f Hz"
                  % (rate, effect.macro(0), rate * 0.5 * 0.98))
            effect.deinit()

    def test_patch_index_follows_the_contract(self):
        effect, _holder = build()
        self.assertEqual(effect.patch_index, 0)
        effect.program_change(4)
        self.assertEqual(effect.patch_index, 4)
        effect.set_macro(1, 100)
        self.assertIsNone(effect.patch_index)
        effect.deinit()


class Tier2(unittest.TestCase):
    """The dossier's circuit traits, each against its own criterion."""

    def test_d1_level_independence(self):
        """D1. One spectral balance at four absolute levels; the settled
        reductions must agree within 1 dB."""
        rate = 48000
        readings = {}
        for level_tag in ("-6", "-20", "-40", "-55"):
            values, wet, frames = deess(rate, "sibilant_" + level_tag,
                                        range_db=20.0, sensitivity_db=34.0)
            readings[level_tag] = settled_change(values, wet, frames, 6000,
                                                 rate)
        spread = max(readings.values()) - min(readings.values())
        print("\n  D1 48000 Hz: %s spread %.3f dB"
              % ({k: round(v, 3) for k, v in readings.items()}, spread))
        self.assertLess(spread, 1.0)
        for tag, value in readings.items():
            self.assertLess(value, -5.0,
                            "the reduction collapsed at %s dBFS" % tag)

    def test_d1_over_the_sensitivity_span(self):
        """D1, swept over the control the gate audit found it depends on.

        The row above measures the spread at Sensitivity 34 and it is
        green there. The refutation pass showed the reading is a property
        of that setting; this sweeps the macro's whole travel and asserts
        both halves of the honest verdict.

        **Disconfirmed** over the span - the worst cell must exceed the
        1 dB bar, and a green sweep here would mean the trait had quietly
        started holding and this test's verdict was stale. **Bounded** at
        every Sensitivity the six shipped patches use, which is where a
        player meets it.
        """
        rate = 48000

        loud = {}

        def cell(settings):
            got = [reduction_at("sibilant_" + tag, settings, range_db=20.0,
                                rate=rate)
                   for tag in ("-6", "-20", "-40", "-55")]
            # The same four renders answer two questions, so they are read
            # twice rather than run twice: the whole -6..-55 span, which is
            # what the dossier's D1 quantifies over, and the -6..-40 part of
            # it, which is where the bound in the verdict sits.
            loud[settings[2]] = max(got[:3]) - min(got[:3])
            return {"values": {"spread_db": max(got) - min(got),
                               "deepest_db": min(got)}}

        subject = build(rate=rate, range_db=20.0)[0]
        try:
            swept = M.macro_sweep(
                subject, [M.MacroSpan("Sensitivity", 0, 127, midpoints=15)],
                cell, figure="spread_db", bar=1.0, unit="dB", name="D1")
        finally:
            subject.deinit()
        print("\n  D1 over the Sensitivity span: worst %.3f dB at %s "
              "(bar 1.0); cells %s"
              % (swept["values"]["worst"], swept["values"]["at_units"],
                 [(round(cell_["units"]["Sensitivity"], 1),
                   round(cell_["figure"], 3))
                  for cell_ in swept["values"]["cells"]]))
        self.assertNotEqual(swept["red"], [],
                            "D1 is recorded disconfirmed over this span")

        # And the bound the verdict carries: drop the -55 dBFS probe and the
        # spread collapses at every Sensitivity. The trait holds from -6 to
        # -40 dBFS; what fails is the bottom probe, whose own dry blend
        # already spreads 0.643-1.253 dB with the gain cell muted (D7).
        worst_loud = max(loud.values())
        print("  D1 over -6..-40 dBFS alone: worst %.3f dB at Sensitivity "
              "%.1f dB" % (worst_loud,
                           max(loud, key=lambda k: loud[k]) / 127.0 * 48.0))
        self.assertLess(worst_loud, 0.5)

        at_patches = {}
        for position in sorted({patch[1][2]
                                for patch in deesser.DeEsser.PATCHES.values()}):
            got = [reduction_at("sibilant_" + tag, {2: position},
                                range_db=20.0, rate=rate)
                   for tag in ("-6", "-20", "-40", "-55")]
            at_patches[position] = max(got) - min(got)
        print("  D1 at the shipped patches' Sensitivity: %s"
              % {k: round(v, 3) for k, v in at_patches.items()})
        for position, spread in at_patches.items():
            self.assertLess(spread, 1.0,
                            "macro 2 = %d is a shipped patch's own setting"
                            % position)

    def test_d3_the_twelve_db_clause_is_unreachable(self):
        """D3's third clause, which the evidence table dropped and the gate
        audit put back: "either band's reduction more than 0.5 dB from the
        commanded 12 dB" is a disconfirming condition of the frozen trait.

        Swept over Sensitivity, because that is the only control that can
        drive the reduction towards the commanded Range. It saturates: the
        best any reachable setting reaches is asserted below to be *outside*
        the 0.5 dB bar. Cause: the Range blend is an asymptote
        (`-20*log10(1 - alpha)` is approached, never met), the same
        N-DEESS-6 that bounds D7.
        """
        rate = 48000

        def cell(settings):
            got = reduction_at("sibilant_-6", settings, range_db=12.0,
                               rate=rate)
            return {"values": {"miss_db": abs(got + 12.0), "reduction": got}}

        subject = build(rate=rate, range_db=12.0)[0]
        try:
            swept = M.macro_sweep(
                subject, [M.MacroSpan("Sensitivity", 0, 127, midpoints=7)],
                cell, figure="miss_db", worst="min", bar=0.5, unit="dB",
                name="D3")
        finally:
            subject.deinit()
        best = min(cell_["figure"] for cell_ in swept["values"]["cells"])
        print("\n  D3 12 dB clause: best %.3f dB from the commanded 12 "
              "(bar 0.5); cells %s"
              % (best, [(round(cell_["units"]["Sensitivity"], 1),
                         round(cell_["figure"], 3))
                        for cell_ in swept["values"]["cells"]]))
        self.assertGreater(best, 0.5,
                           "the 12 dB clause is recorded unreachable")

    def test_d3_the_two_modes(self):
        """D3. Broadband moves both bands together; HF-only leaves the low
        band alone."""
        rate = 48000
        out = {}
        for hf_only in (False, True):
            values, wet, frames = deess(rate, "sibilant_-6", range_db=12.0,
                                        sensitivity_db=34.0, hf_only=hf_only)
            out[hf_only] = (settled_change(values, wet, frames, 6000, rate),
                            settled_change(values, wet, frames, 200, rate))
        print("\n  D3 48000 Hz: broadband high %.3f low %.3f | "
              "hf-only high %.3f low %.3f"
              % (out[False][0], out[False][1], out[True][0], out[True][1]))
        self.assertLess(abs(out[False][0] - out[False][1]), 0.5)
        self.assertLess(abs(out[True][1]), 0.25)
        self.assertLess(out[True][0], -5.0)

    def test_d6_rms_detection(self):
        """D6, and why its own criterion is not measurable on this class.

        The trait asks for a sine and a square of equal RMS to get the same
        reduction within 0.5 dB. They do - **and so do they with
        `detector="peak"`**, 0.41 dB against 0.46 dB, so that reading tells
        an RMS detector from a rectifier not at all and a green result on it
        would be absence reading as agreement.

        The cause is worth the paragraph. With `relative_threshold` on, the
        gain computer subtracts a full-band reference that is a **rectified
        peak follower whatever `detector` says** - `fabsf(sense)`,
        `audioif_dynamics.c:594-600` - so `detector="rms"` governs only the
        band level. A matched-RMS sine and square therefore cannot come out
        equal: their peaks differ by 3 dB and the reference is a peak.

        What *is* measurable, and what this test asserts, is that the option
        is doing something: a 10 %-duty train against a sine of the same RMS
        separates by 4.96 dB on the RMS detector and 3.54 dB on the peak
        one, a 1.42 dB difference from the option alone. Node ask
        N-DEESS-8.
        """
        rate = 48000
        readings = {}
        for detector in ("rms", "peak"):
            row = {}
            for name in ("sine_1k_-14", "train10_1k_-14_rms"):
                values = probe(name, rate)
                effect, _holder = build(rate=rate, values=values,
                                        frequency=800.0, range_db=20.0,
                                        sensitivity_db=2.0)
                if detector == "peak":
                    effect._duck.set(detector="peak")
                frames = len(values) // 2
                wet = render(effect.output, frames, rate)
                row[name] = settled_change(values, wet, frames, 1000, rate)
                effect.deinit()
            readings[detector] = round(abs(row["sine_1k_-14"]
                                           - row["train10_1k_-14_rms"]), 3)
        # And the dossier's own pair, recorded because it is what D6 says -
        # together with the number that shows it cannot be cited.
        stated = {}
        for detector in ("rms", "peak"):
            row = {}
            for name in ("sine_1k_-6", "square_1k_-6_rms"):
                values = probe(name, rate)
                effect, _holder = build(rate=rate, values=values,
                                        frequency=800.0, range_db=20.0,
                                        sensitivity_db=6.0)
                if detector == "peak":
                    effect._duck.set(detector="peak")
                frames = len(values) // 2
                wet = render(effect.output, frames, rate)
                row[name] = settled_change(values, wet, frames, 1000, rate)
                effect.deinit()
            stated[detector] = round(abs(row["sine_1k_-6"]
                                         - row["square_1k_-6_rms"]), 3)
        print("\n  D6 48000 Hz: crest separation rms %.3f dB vs peak %.3f dB "
              "(the option is active, %.3f dB of it); the dossier's own "
              "sine/square pair reads rms %.3f dB against peak %.3f dB, "
              "which cannot tell them apart"
              % (readings["rms"], readings["peak"],
                 readings["rms"] - readings["peak"],
                 stated["rms"], stated["peak"]))
        self.assertGreater(readings["rms"] - readings["peak"], 1.0)
        # The disconfirmation, held so it stays visible: the stated pair does
        # not discriminate, and this fails the day the reference follower
        # becomes switchable.
        self.assertLess(abs(stated["rms"] - stated["peak"]), 0.5)

    def test_d7_range_bounds_and_never_exceeds(self):
        """D7. The reduction never passes the Range setting, and unity
        holds with no sibilant present.

        The dossier's own reading (section 8.1): this build's Range is an
        asymptote, so the measured reduction is *below* the setting and the
        distance is recorded rather than asserted away.
        """
        rate = 48000
        reached = {}
        for range_db in (5.0, 10.0, 20.0):
            values, wet, frames = deess(rate, "sibilant_-6",
                                        range_db=range_db,
                                        sensitivity_db=44.0)
            reached[range_db] = settled_change(values, wet, frames, 6000,
                                               rate)
            self.assertGreater(reached[range_db], -range_db - 0.05,
                               "Range %g dB was exceeded" % range_db)
        # The resting clause, at the Sensitivity a patch actually uses.
        # Read the print: at the 44 dB the Range clause above needed, a bare
        # 200 Hz tone *is* ducked, because a band sitting 21 dB under the
        # programme is inside a 44 dB allowance. That is the control doing
        # its job, not a defect, and both numbers are recorded.
        resting = {}
        for sensitivity in (30.0, 44.0):
            values = tone(200, 12000, SETTLED_FRAMES, rate)
            effect, _holder = build(rate=rate, values=values, range_db=20.0,
                                    sensitivity_db=sensitivity)
            wet = render(effect.output, SETTLED_FRAMES, rate)
            resting[sensitivity] = settled_change(values, wet, SETTLED_FRAMES,
                                                  200, rate)
            effect.deinit()
        print("\n  D7 48000 Hz: %s | resting gain on the low tone %s"
              % ({k: round(v, 3) for k, v in reached.items()},
                 {k: round(v, 4) for k, v in resting.items()}))
        self.assertLess(abs(resting[30.0]), 0.1)

        # The ceiling, on the probe the refutation pass said breaks it, and
        # the control that says what broke it. `sibilant_-55` at Sensitivity
        # 44 reads past `-Range` at all three settings. Muting the gain
        # cell's own voice leaves the dry blend alone - no detector, no
        # gain computer, just `(1 - alpha) * x` through the same mixer - and
        # *that* reads further past the ceiling than the class does. So the
        # excess is the 16-bit truncation of a dry voice at -75 dBFS, and
        # the bound the palette can actually build is the floor below, not
        # `-Range`. This is the question the refutation record left open.
        sensitivity = 127.0 * _component.macro_position((0.0, 48.0), 44.0)
        for range_db in (5.0, 10.0, 20.0):
            position = 127.0 * _component.macro_position((0.0, 20.0),
                                                         range_db)
            macros = {1: position, 2: sensitivity}
            floor = reduction_at("sibilant_-55", macros, rate=rate,
                                 post=_mute_the_gain_cell)
            got = reduction_at("sibilant_-55", macros, rate=rate)
            print("  D7 floor  Range %4.1f: class %.4f dB, dry blend alone "
                  "%.4f dB (ideal %.1f)" % (range_db, got, floor, -range_db))
            self.assertGreaterEqual(got, floor - 0.01,
                                    "Range %g dB was passed by more than "
                                    "the blend's own quantisation floor"
                                    % range_db)

    def test_d8_flat_sum(self):
        """D8's flat sum: HF-only mode at Range 0 is the crossover's own
        recombination, and it has to be flat inside 0.25 dB.

        D2's tracking clause used to be read off this same render and is
        not any more - see `test_d2_corner_tracks_over_the_frequency_span`.
        A Linkwitz-Riley pair sums flat at *every* corner, so a reading
        taken on the sum is green whatever the corner is doing, which is
        what the refutation pass found and the gate audit ruled
        (`unmeasured`, "the measurement cannot fail").

        D2's *order* clause is not tested here: the dossier records it
        disconfirmed (section 8.3), and a test asserting a claim the class
        does not make would be theatre.
        """
        rate = 48000
        for corner in (800.0, 2500.0, 8000.0):
            summed = []
            for hz in (corner / 4.0, corner, corner * 2.0):
                if hz >= rate * 0.45:
                    continue
                values = tone(hz, 12000, SETTLED_FRAMES, rate)
                effect, _holder = build(rate=rate, values=values,
                                        frequency=corner, range_db=0.0,
                                        hf_only=True)
                wet = render(effect.output, SETTLED_FRAMES, rate)
                summed.append((hz, settled_change(values, wet, SETTLED_FRAMES,
                                                  hz, rate)))
                effect.deinit()
            print("\n  D8 corner %6.0f Hz: %s"
                  % (corner, [(int(h), round(d, 3)) for h, d in summed]))
            for _hz, deviation in summed:
                self.assertLess(abs(deviation), 0.25)

    def test_d2_corner_tracks_over_the_frequency_span(self):
        """D2's tracking clause, rebuilt so it can fail, and swept.

        The reading is `extracted_corner_hz`: a *frequency* solved out of
        the detector band's own shape, compared with the frequency the
        Frequency macro was asked for. The bar is the dossier's 5 %.

        It is run with `M.macro_sweep` over the macro's whole travel rather
        than at three hand-picked corners, because a trait quantified over
        a span and measured at a point is the defect the pattern revision's
        section 1.1 names - and the span is where this one weakens: the
        error is 0.01 % at the bottom and grows towards the top, where the
        one-pole's own discrete shape starts to show against fs.

        The audio pair's corner is not directly observable through this
        class's surface - HF-only mode sums the two halves and broadband
        never splits the audio - so what is measured here is the detector
        half. The audio half's corner is shown to move by the TAIL ladder
        in `test_tail_in_hf_only_mode_is_the_crossover`: 170 / 51 / 14
        samples at 800 / 2500 / 8000 Hz, which is 1/f to three figures.
        """
        rate = 48000
        subject = build(rate=rate)[0]
        try:
            result = M.macro_sweep(
                subject, [M.MacroSpan("Frequency", 0, 127, midpoints=3)],
                lambda settings: _corner_cell(deesser.DeEsser,
                                             settings[0], rate),
                figure="error_percent", bar=5.0, unit="%", name="D2")
        finally:
            subject.deinit()
        print("\n  D2 tracking sweep: worst %.2f %% at %s (bar 5 %%); "
              "cells %s"
              % (result["values"]["worst"], result["values"]["at_units"],
                 [(round(cell["units"]["Frequency"]), round(cell["figure"], 2))
                  for cell in result["values"]["cells"]]))
        self.assertEqual(result["red"], [])

    def test_d5_attack_shortens_with_the_overshoot(self):
        """D5, on the axis the option actually reads.

        `program_attack` scales the attack coefficient by the root of
        `level / db_to_gain(threshold_db)` - an **absolute** overshoot -
        while `relative_threshold` has moved the gain computer to a
        relative one. So the axis that moves the attack here is programme
        level at a fixed spectral balance, and the three runs below hold the
        balance and raise the level 10 dB at a time. The depths staying
        together across that span is D1 measured a second way; the times
        shortening is D5.

        The dossier asks for a ratio of about 3.3 and this build does not
        reach it: that half of D5 is disconfirmed in the evidence pack,
        with the composition failure above as its cause and N-DEESS-7 as
        the ask. What is demonstrated is the direction - a fixed attack
        coefficient cannot produce it at all.
        """
        rate = 48000
        readings = {}
        for scale, tag in ((0.1, "+0 dB"), (0.3162, "+10 dB"),
                           (1.0, "+20 dB")):
            values = sibilant_burst(rate, low_hz=1000.0, seconds=1.0,
                                    burst=(0.5, 1.0),
                                    low_lsb=int(28000 * scale),
                                    high_lsb=int(7000 * scale))
            effect, _holder = build(rate=rate, values=values, range_db=6.0,
                                    sensitivity_db=23.5)
            frames = len(values) // 2
            wet = render(effect.output, frames, rate)
            dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
            trace = M.gaintrace(wet, dry, hop_ms=0.1, attack_from_ms=500.0)
            effect.deinit()
            rows = trace["values"]
            marks = [(t, g) for t, g in zip(rows["trace_ms"],
                                            rows["trace_gr_db"])
                     if g is not None and t >= 500.0]
            depth = rows["attack_gr_depth_db"]
            readings[tag] = (round(depth, 3),
                             fraction_ms([g for _t, g in marks],
                                         [t for t, _g in marks],
                                         marks[0][1], depth, 0.63))
        print("\n  D5 48000 Hz: (depth dB, t63 ms) %s" % readings)
        depths = [value[0] for value in readings.values()]
        self.assertLess(max(depths) - min(depths), 1.0)
        self.assertLess(readings["+20 dB"][1], readings["+0 dB"][1])

    def test_d4_release_is_an_exponential_not_a_dB_ramp(self):
        """D4, disconfirmed on shape and measured on rate.

        The trait asks for a straight line in dB at 925 dB/sec.
        `audiodynamics` releases with a one-pole in linear gain, which is a
        curve in dB at every coefficient - so the *rate* can be tuned to the
        902's and the *shape* cannot. Both halves are read here, and the
        test holds the class to the shape it has, so the day N-DEESS-2 lands
        this fails and someone re-reads the trait.

        The carrier is 200 Hz and the hop is 2.5 ms, which is exactly half
        a period of it: the RMS of a sine over any half period is the same
        number whatever the phase, so the trace reads the gain and not the
        carrier's own waveform. At a 1 kHz carrier and a 0.1 ms hop the same
        measurement read 23.5 ms for a recovery that takes 8, which is the
        method's error and not the class's.
        """
        rate = 48000
        values = sibilant_burst(rate, low_hz=200.0, seconds=2.0,
                                burst=(0.5, 1.0))
        effect, _holder = build(rate=rate, values=values, range_db=12.0,
                                sensitivity_db=30.0, release_ms=3.5)
        frames = len(values) // 2
        wet = render(effect.output, frames, rate)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
        trace = M.gaintrace(wet, dry, hop_ms=2.5, release_from_ms=1000.0)
        effect.deinit()
        rows = trace["values"]
        t95 = rows["release_t95_ms"]
        self.assertIsNotNone(t95)
        marks = [(t, g) for t, g in zip(rows["trace_ms"], rows["trace_gr_db"])
                 if g is not None and 1000.0 <= t <= 1000.0 + t95]
        stamps = [t for t, _g in marks]
        series = [g for _t, g in marks]
        begin, end_db = series[0], series[-1]
        span = stamps[-1] - stamps[0]
        straight = [begin + (end_db - begin) * (t - stamps[0]) / span
                    for t in stamps]
        deviation = max(abs(a - b) for a, b in zip(series, straight))
        covered = abs(end_db - begin)
        rate_db_s = covered / (span / 1000.0)
        print("\n  D4 48000 Hz: %.2f dB of an %.2f dB recovery in %.2f ms = "
              "%.0f dB/sec, against the 902's 925 (%.1f%% away); worst "
              "departure from a straight dB line %.2f dB"
              % (covered, abs(begin), span, rate_db_s,
                 100.0 * abs(rate_db_s - 925.0) / 925.0, deviation))
        self.assertGreater(deviation, 0.3)

    def test_d4_release_rate_is_asserted_and_bounded(self):
        """D4's *rate* half, asserted rather than printed, and swept.

        The gate audit ruled this row `unmeasured`: the old test asserted
        only the shape (`deviation > 0.3`) and printed the dB/sec, so it was
        green at 602, 322 and 132 dB/sec. It is asserted here against the
        902's 925 +/- 10 %, at the Release the class ships and at the three
        hops the refutation pass used - because an exponential has no
        dB/sec and the figure is an average over whatever window is read.

        And then swept, which is the honest half: the Release macro is a
        control the player turns, and over its own 1-200 ms travel the rate
        runs from four figures down to two. So the row is *demonstrated at
        the shipped Release and bounded by it*, not demonstrated of the
        class. The sweep's assertion is that bound: the worst cell must be
        outside the bar, because a green sweep here would mean the Release
        macro does nothing.
        """
        rate = 48000
        readings = {}
        for hop in (1.25, 2.5, 5.0):
            result = release_rate_db_s(deesser.DeEsser, hop_ms=hop,
                                       rate=rate)
            readings[hop] = result["values"]
            self.assertEqual(result["red"], [], "hop %g ms" % hop)
        print("\n  D4 rate at the shipped Release (3.5 ms): %s"
              % {hop: (round(v["rate_db_s"]), round(v["percent_off_925"], 1))
                 for hop, v in readings.items()})

        subject = build(rate=rate)[0]
        try:
            swept = M.macro_sweep(
                subject, [M.MacroSpan("Release", 0, 127, midpoints=5)],
                lambda settings: _release_cell(settings, rate),
                figure="percent_off_925", worst="max", bar=10.0, unit="%",
                name="D4")
        finally:
            subject.deinit()
        print("  D4 rate over the Release span: worst %.1f %% off at %s; "
              "cells %s"
              % (swept["values"]["worst"], swept["values"]["at_units"],
                 [(round(cell["units"]["Release"], 2),
                   round(cell["figure"], 1))
                  for cell in swept["values"]["cells"]]))
        self.assertNotEqual(swept["red"], [],
                            "the Release macro moved the rate by nothing")


def _release_cell(settings, rate):
    """One cell of D4's Release sweep. A cell whose recovery does not
    finish inside the render is 100 % off, not a hole: the slowest Release
    is the point of the span the trait is weakest at."""
    holder = source(tone(200, 100, 512, rate), rate, 2)
    reader = deesser.DeEsser.create(holder, rate)
    reader.set_macro(4, settings[4])
    release_ms = reader.macro(4)
    reader.deinit()

    class _AtPosition(deesser.DeEsser):
        def _build(self, *arguments, **keywords):
            keywords["release_ms"] = release_ms
            deesser.DeEsser._build(self, *arguments, **keywords)

    result = release_rate_db_s(_AtPosition, rate=rate)
    if result["values"]["rate_db_s"] is None:
        return {"values": {"percent_off_925": 100.0}}
    return {"values": {"percent_off_925": result["values"]["percent_off_925"],
                       "rate_db_s": result["values"]["rate_db_s"]}}


class PlantedFaults(unittest.TestCase):
    """Each measurement above, driven by a broken build, must go red.

    The faults are planted in a *live instance* rather than in the module,
    so the clean control and the faulted run are the same code path and the
    only difference is the fault.
    """

    def test_wire_goes_red_on_a_one_lsb_dry_path(self):
        rate = 48000
        values = probe("ramp_fs", rate)
        effect, _holder = build(rate=rate, values=values, range_db=0.0)
        frames = len(values) // 2
        clean = render(effect.output, frames, rate)
        dry = M.Render.from_pcm(values.tobytes()[:len(clean.pcm)], rate, 2)
        self.assertEqual(M.wire(clean, dry)["red"], [], "the control failed")
        # The fault: the dry voice a hair under unity - the 32767/32768 the
        # kit spec names, which `ramp_fs` was built to expose.
        effect2, _holder2 = build(rate=rate, values=probe("ramp_fs", rate),
                                  range_db=0.0)
        effect2._out.voice[0].level = 32767.0 / 32768.0
        faulted = render(effect2.output, frames, rate)
        result = M.wire(faulted, dry)
        print("\n  WIRE fault: %s" % result["values"])
        self.assertNotEqual(result["red"], [])
        effect.deinit()
        effect2.deinit()

    def test_tail_goes_red_on_a_held_dc_state(self):
        rate = 48000
        values = probe("burst_silence", rate)
        burst_end = int(0.2 * rate)
        effect, _holder = build(rate=rate, values=values)
        frames = len(values) // 2
        clean = render(effect.output, frames, rate)
        self.assertEqual(M.tail(clean, burst_end_frame=burst_end)["red"], [],
                         "the control failed")
        # The fault: one LSB of DC held in the settled state, which is the
        # audioif#23 class of defect this invariant exists for.
        faulted_pcm = bytearray(clean.pcm)
        offset = (frames - 100) * 4
        faulted_pcm[offset] = 1
        faulted = M.Render.from_pcm(bytes(faulted_pcm), rate, 2)
        result = M.tail(faulted, burst_end_frame=burst_end)
        print("\n  TAIL fault: %s" % result["values"])
        self.assertNotEqual(result["red"], [])
        effect.deinit()

    def test_click_goes_red_when_latency_is_misreported(self):
        rate = 48000
        values = probe("impulse", rate)
        effect, _holder = build(rate=rate, values=values, range_db=0.0)
        frames = 8192
        wet = render(effect.output, frames, rate)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
        self.assertEqual(M.click(wet, dry, 0)["red"], [],
                         "the control failed")
        result = M.click(wet, dry, 256)
        print("\n  CLICK fault (256 short): %s" % result["values"])
        self.assertNotEqual(result["red"], [])
        effect.deinit()

    def test_state_goes_red_when_a_ring_is_left_full(self):
        """The reset fault of the same kind the dossier's V7-7 measured:
        skip the ring flush and the class replays what the rings hold."""
        rate = 48000
        values = probe("noise_det", rate, frames=STATE_FRAMES)
        effect, holder = build(rate=rate, values=values)
        quiet = source(silence(len(values) // 2), rate)
        # The fault: the reset walk without the ring flush, which is what
        # the class did before `_reset_chain` existed. 32-block pulls fill
        # the rings; the 4 s file was leftover length.
        render(effect.output, 32 * 256, rate)
        for node in (effect._duck, effect._pre, effect._out):
            audiocore.reset_buffer(node)
        effect._adapter.play(quiet)
        after = render(effect.output, 32 * 256, rate)
        residual = int(abs(after.data).max())
        print("\n  STATE fault (no ring flush): residual %d LSB" % residual)
        self.assertGreater(residual, 0)
        effect.deinit()

        # The control, on the class's own reset, has to be zero.
        effect2, holder2 = build(rate=rate,
                                 values=probe("noise_det", rate,
                                              frames=STATE_FRAMES))
        quiet2 = source(silence(len(values) // 2), rate)
        render(effect2.output, 32 * 256, rate)
        effect2.reset()
        effect2._adapter.play(quiet2)
        clean = render(effect2.output, 32 * 256, rate)
        print("  STATE control (class reset): residual %d LSB"
              % int(abs(clean.data).max()))
        self.assertEqual(int(abs(clean.data).max()), 0)
        effect2.deinit()
        del holder, holder2

    def test_d1_goes_red_on_an_absolute_threshold(self):
        """D1's fault of the same kind: turn `relative_threshold` off and
        the class becomes the primitive de-esser the dossier's section 7
        names, whose reduction collapses with level."""
        rate = 48000
        readings = {}
        for level_tag in ("-6", "-20", "-40"):
            values = probe("sibilant_" + level_tag, rate,
                           frames=SETTLED_FRAMES)
            effect, _holder = build(rate=rate, values=values, range_db=20.0,
                                    sensitivity_db=34.0)
            effect._duck.set(relative_threshold=0.0)
            frames = len(values) // 2
            wet = render(effect.output, frames, rate)
            readings[level_tag] = settled_change(values, wet, frames, 6000,
                                                 rate)
            effect.deinit()
        spread = max(readings.values()) - min(readings.values())
        print("\n  D1 fault (absolute threshold): %s spread %.3f dB"
              % ({k: round(v, 3) for k, v in readings.items()}, spread))
        self.assertGreater(spread, 1.0)

    def test_d3_goes_red_when_hf_only_ducks_the_low_band(self):
        """D3's fault: route the low band through the gain cell in HF-only
        mode, which is broadband mode wearing HF-only's label."""
        rate = 48000
        values = probe("sibilant_-6", rate, frames=SETTLED_FRAMES)
        effect, _holder = build(rate=rate, values=values, range_db=12.0,
                                sensitivity_db=34.0, hf_only=True)
        effect._pre.voice[0].level = 1.0     # the raw stream back into the cell
        effect._out.voice[1].level = 0.0     # and the untouched low half out
        frames = len(values) // 2
        wet = render(effect.output, frames, rate)
        low = settled_change(values, wet, frames, 200, rate)
        effect.deinit()
        print("\n  D3 fault (HF-only ducking the lows): low band %+.3f dB"
              % low)
        self.assertGreater(abs(low), 0.25)

    def test_d7_goes_red_when_the_range_blend_is_removed(self):
        """D7's fault: the wet path at unity with no dry beside it, which
        is a de-esser with no maximum - the third defect section 7 names."""
        rate = 48000
        values = probe("sibilant_-6", rate, frames=SETTLED_FRAMES)
        effect, _holder = build(rate=rate, values=values, range_db=5.0,
                                sensitivity_db=44.0)
        effect._out.voice[0].level = 0.0
        effect._out.voice[3].level = 1.0
        frames = len(values) // 2
        wet = render(effect.output, frames, rate)
        reached = settled_change(values, wet, frames, 6000, rate)
        effect.deinit()
        print("\n  D7 fault (no Range blend): reduction %.3f dB against a "
              "5 dB Range" % reached)
        self.assertLess(reached, -5.05)

    def test_d8_goes_red_on_a_single_section_crossover(self):
        """D8's fault of the same kind: one Butterworth section a side
        instead of two, which nulls at the crossing (dossier A-D1)."""
        rate = 48000
        corner = 2500.0
        values = tone(corner, 12000, SETTLED_FRAMES, rate)
        effect, _holder = build(rate=rate, values=values, frequency=corner,
                                range_db=0.0, hf_only=True)
        clean = render(effect.output, SETTLED_FRAMES, rate)
        self.assertLess(abs(settled_change(values, clean, SETTLED_FRAMES,
                                           corner, rate)), 0.25,
                        "the control failed")
        effect.deinit()

        effect2, _holder2 = build(rate=rate, values=tone(corner, 12000,
                                                        SETTLED_FRAMES, rate),
                                  frequency=corner, range_db=0.0,
                                  hf_only=True)
        # The fault: the second section of each half pushed far out of the
        # way, leaving one 12 dB/octave section a side.
        effect2._lows[1].frequency = rate * 0.45
        effect2._highs[1].frequency = 20.0
        faulted = render(effect2.output, SETTLED_FRAMES, rate)
        deviation = settled_change(values, faulted, SETTLED_FRAMES, corner,
                                   rate)
        effect2.deinit()
        print("\n  D8 fault (one section a side): %+.3f dB at the corner"
              % deviation)
        self.assertGreater(abs(deviation), 0.25)

    def test_d2_goes_red_when_the_crossover_does_not_follow(self):
        """D2's fault of the same kind, and the one the old reading could
        not see: the Frequency macro moves and the filters stay put."""
        rate = 48000
        for position in (0, 64, 127):
            clean = extracted_corner_hz(deesser.DeEsser, position, rate)
            faulted = extracted_corner_hz(FrozenCrossover, position, rate)
            print("\n  D2 fault at macro 0 = %3d: commanded %.0f Hz, clean "
                  "%.0f (%+.2f %%), frozen %.0f (%+.2f %%)"
                  % (position, clean[0], clean[1], clean[2],
                     faulted[1], faulted[2]))
            self.assertLess(abs(clean[2]), 5.0, "the control failed")
            self.assertGreater(abs(faulted[2]), 5.0)

    def test_d4_goes_red_when_the_release_is_pushed_in_wrong(self):
        """D4's fault of the same kind: the Release the class pushes into
        the node scaled by 250, a units bug no Release position can dial."""
        rate = 48000
        clean = release_rate_db_s(deesser.DeEsser, rate=rate)
        self.assertEqual(clean["red"], [], "the control failed")
        faulted = release_rate_db_s(SlowRelease, rate=rate)
        print("\n  D4 fault (release x%g): clean %.0f dB/sec -> faulted %s"
              % (SLOW_RELEASE_SCALE, clean["values"]["rate_db_s"],
                 ("no release completed inside the render"
                  if faulted["values"]["rate_db_s"] is None
                  else "%.0f dB/sec (%.1f %% off)"
                       % (faulted["values"]["rate_db_s"],
                          faulted["values"]["percent_off_925"]))))
        self.assertNotEqual(faulted["red"], [])


class PatchSweep(unittest.TestCase):
    """Every Tier 2 row that can be read at a *setting*, read at all six
    shipped patches.

    The revised evidence template puts this before any chosen operating
    point: "a shipped patch is a setting the class's author chose, published
    and expects a player to use, so a trait the class misses there is not a
    corner case - it is the product." Phase 2's gate audit broke this class
    at the Sensitivity its own Range row uses, which is why the table is
    here rather than in prose.

    D5 and D6 are not in it: both need bespoke probe material (a levelled
    sibilant burst, a matched-RMS pair) rather than a setting, and both are
    read at their own operating points in their own tests.
    """

    def _patches(self):
        effect = build()[0]
        try:
            rows = []
            for index in sorted(deesser.DeEsser.PATCHES):
                effect.program_change(index)
                rows.append((index, deesser.DeEsser.PATCHES[index][0],
                             [effect.get_macro(macro)
                              for macro in range(7)],
                             [effect.macro(macro) for macro in range(7)]))
        finally:
            effect.deinit()
        return rows

    def test_every_row_at_every_shipped_patch(self):
        rate = 48000
        table = {}
        print("\n  patch settings, read back off the instance:")
        for index, name, positions, units in self._patches():
            print("    %d %-18s %s" % (index, name,
                                       [round(value, 2) for value in units]))

        print("  D1 spread / D3 mode split / D4 rate / D7 excess / D2 error,"
              " at each patch:")
        for index, name, positions, units in self._patches():
            macros = dict(enumerate(positions))
            got = [reduction_at("sibilant_" + tag, macros, rate=rate)
                   for tag in ("-6", "-20", "-40", "-55")]
            d1 = max(got) - min(got)
            low = reduction_at("sibilant_-6", macros, hz=200, rate=rate)
            d2 = extracted_corner_hz(deesser.DeEsser, positions[0], rate)[2]
            release_position = positions[4]

            class _AtPatch(deesser.DeEsser):
                def _build(self, *arguments, **keywords):
                    keywords["release_ms"] = units[4]
                    deesser.DeEsser._build(self, *arguments, **keywords)

            d4 = release_rate_db_s(_AtPatch, rate=rate)
            ceiling = -units[1]
            print("    %d %-18s D1 %.3f dB | high %+.3f low %+.3f dB "
                  "(Mode %s) | D4 %s dB/sec at Release %.2f ms | D7 "
                  "reached %+.3f against %.1f | D2 %+.2f %%"
                  % (index, name, d1, got[0], low,
                     "HF" if units[3] >= 0.5 else "broadband",
                     ("none" if d4["values"]["rate_db_s"] is None
                      else "%.0f" % d4["values"]["rate_db_s"]),
                     units[4], got[0], ceiling, d2))
            table[index] = (d1, got[0], ceiling, d2)
            del release_position

        # What the table is held to, and it is not "all green". D1 is
        # recorded disconfirmed above Sensitivity 34 dB and it misses at the
        # two HF-only patches, which is the disconfirmation meeting a
        # setting the class's own author published - the template's "not a
        # corner case, it is the product". The rows below are the verdict
        # this pack carries, so a change in either direction fails here.
        broadband = [index for index in table
                     if index not in DEESS_HF_ONLY_PATCHES]
        for index in broadband:
            self.assertLess(table[index][0], 1.0,
                            "D1 at broadband patch %d" % index)
        for index in DEESS_HF_ONLY_PATCHES:
            self.assertGreater(table[index][0], 1.0,
                               "D1 is recorded disconfirmed at HF-only "
                               "patch %d" % index)
            macros = dict(enumerate(deesser.DeEsser.PATCHES[index][1]))
            loud = [reduction_at("sibilant_" + tag, macros, rate=rate)
                    for tag in ("-6", "-20", "-40")]
            print("    patch %d over -6..-40 dBFS alone: %s spread %.3f dB"
                  % (index, [round(value, 3) for value in loud],
                     max(loud) - min(loud)))
            self.assertLess(max(loud) - min(loud), 0.5,
                            "the -55 dBFS probe is the whole of it")
        for index, (_d1, reached, ceiling, error) in table.items():
            self.assertGreater(reached, ceiling - 0.05,
                               "D7 at patch %d" % index)
            self.assertLess(abs(error), 5.0, "D2 at patch %d" % index)


class KitChecks(unittest.TestCase):
    """The two checks the Phase 2 pattern revision added, run on this
    class's own measurements: a measurement that is green on a build that
    does nothing has not measured anything (section 1.2), and a fault the
    class's own surface can dial is a disconfirmation waiting to be written
    down rather than a fault (section 1.3).
    """

    def test_the_d2_reading_is_red_on_a_null_build(self):
        """`DeEsser` rebuilt as a wire - the constructor runs, every macro
        answers, `output` is the source - must not read a corner."""
        rate = 48000
        checked = F.null_build_red(
            deesser.DeEsser,
            lambda cls: {"passed": abs(extracted_corner_hz(cls, 64,
                                                           rate)[2]) < 5.0},
            label="DeEsser D2")
        print("\n  D2 null build: wire %s, control %s"
              % (checked["null"], checked["control"]))
        self.assertFalse(checked["null"]["passed"])

    def test_the_d4_reading_is_red_on_a_null_build(self):
        """A wire has no gain to release, so the rate reading must refuse
        rather than return a number."""
        rate = 48000
        checked = F.null_build_red(
            deesser.DeEsser,
            lambda cls: release_rate_db_s(cls, rate=rate),
            label="DeEsser D4")
        print("\n  D4 null build: %s" % checked["null"]["red"])
        self.assertFalse(checked["null"]["passed"])

    def test_the_frozen_crossover_fault_is_out_of_the_surface_s_reach(self):
        """`FrozenCrossover` forces 500 Hz; the Frequency macro's own floor
        is 800 Hz, so no position and no shipped patch reaches it."""
        got = F.fault_reachability(
            deesser.DeEsser, FROZEN_CORNER_HZ,
            lambda effect: round(effect.macro(0), 1),
            lambda cls: cls.create(source(tone(200, 100, 512, 48000), 48000,
                                          2), 48000),
            tolerance=0.05, label="DeEsser FrozenCrossover")
        print("\n  D2 fault reachability: clean %.1f Hz, fault %.1f Hz, "
              "%d positions walked" % (got["clean"], got["target"],
                                       got["checked"]))

    def test_the_slow_release_fault_is_out_of_the_surface_s_reach(self):
        """`SlowRelease` forces at least 250 ms; the Release macro's own
        span tops at 200 ms."""
        got = F.fault_reachability(
            deesser.DeEsser,
            1.0 * SLOW_RELEASE_SCALE,
            lambda effect: round(effect.macro(4), 3),
            lambda cls: cls.create(source(tone(200, 100, 512, 48000), 48000,
                                          2), 48000),
            tolerance=0.001, label="DeEsser SlowRelease")
        print("\n  D4 fault reachability: clean %.3f ms, the cheapest state "
              "the fault can force %.1f ms, %d positions walked"
              % (got["clean"], got["target"], got["checked"]))

    def test_the_shipped_faults_are_out_of_the_surface_s_reach(self):
        """The faults that were already in the pack, put through the same
        check. Each is named by the state it forces, because each is a
        write to a node the class's surface does not expose.

        The `hf_only` fault of D3 is the exception and it is *not* listed:
        routing the low band into the gain cell is not a state any macro
        holds, it is different wiring, so there is nothing for the
        reachability walk to compare against.
        """
        rate = 48000

        def builder(cls):
            return cls.create(source(tone(200, 100, 512, rate), rate, 2),
                              rate)

        # WIRE's fault is the dry voice at 32767/32768; the Range macro
        # sets that voice's level to `1 - alpha`, and `alpha` is 0 only at
        # Range 0, where the level is exactly 1.0.
        got = F.fault_reachability(
            deesser.DeEsser, 32767.0 / 32768.0,
            lambda effect: effect._out.voice[0].level,
            builder, tolerance=0.0, label="DeEsser WIRE fault")
        print("\n  WIRE fault reachability: clean %.6f, fault %.6f, %d "
              "positions walked"
              % (got["clean"], got["target"], got["checked"]))

        # D7's fault removes the dry blend: the wet voice at 1.0 with the
        # dry at 0.0, **with Listen off**. The Listen half of the reading is
        # not decoration - this check is what found that macro 6 dials
        # exactly those two levels, so the fault as the pack first stated it
        # was a setting a player can reach. Listen is a monitor path and
        # puts the detector's band on the output at unity by design, so
        # D7's bound is a claim about the processing modes and the fault
        # has to be planted inside them. Range 20 is the closest the Range
        # macro itself comes, and that is alpha = 0.9.
        got = F.fault_reachability(
            deesser.DeEsser, [False, 0.0, 1.0],
            lambda effect: [bool(effect.macro(6) >= 0.5),
                            effect._out.voice[0].level,
                            effect._out.voice[3].level],
            builder, tolerance=1e-9, label="DeEsser D7 fault")
        print("  D7 fault reachability: clean %s, fault %s, %d positions "
              "walked" % ([got["clean"][0]] + [round(v, 4)
                                               for v in got["clean"][1:]],
                          got["target"], got["checked"]))

        # D8's fault pushes the second section of each half out of the way.
        # The Frequency macro moves all four corners together over
        # 800-8000 Hz and cannot separate them.
        got = F.fault_reachability(
            deesser.DeEsser, [rate * 0.45, 20.0],
            lambda effect: [effect._lows[1].frequency,
                            effect._highs[1].frequency],
            builder, tolerance=1e-6, label="DeEsser D8 fault")
        print("  D8 fault reachability: clean %s, fault %s, %d positions "
              "walked" % ([round(v, 1) for v in got["clean"]],
                          got["target"], got["checked"]))


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
