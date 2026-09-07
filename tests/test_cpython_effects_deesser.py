"""`DeEsser`'s own invariant, trait and planted-fault battery.

The class gate (`docs/effects-roadmap.md`, "The class gate") asks for two
things this file carries: the Tier 1 invariants green on CPython at 48 kHz,
44.1 kHz and 22.05 kHz and at `channel_count` 1, and every demonstrated
Tier 2 trait shown **red on a planted fault of the same kind**. The numbers
it prints are what `docs/effects/DeEsser-evidence.md` quotes; run it with
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
import audioeffects                                       # noqa: E402
import effect_measurements as M                           # noqa: E402

PROBES = os.path.join(os.path.dirname(HERE), "tools", "effect_probes")
RATES = (48000, 44100, 22050)


# --------------------------------------------------------------------------
# Rig


def probe(name, rate, channels=2):
    """One of the kit's own probes, as an int16 array."""
    path = os.path.join(PROBES, str(rate), "%dch" % channels, name + ".wav")
    with open(path, "rb") as handle:
        data = handle.read()
    at = 12
    while at < len(data):
        chunk, size = data[at:at + 4], int.from_bytes(data[at + 4:at + 8],
                                                      "little")
        if chunk == b"data":
            return array.array("h", data[at + 8:at + 8 + size])
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
    effect = audioeffects.create("DeEsser", holder, rate, **options)
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
    values = probe(probe_name, rate)
    effect, _holder = build(rate=rate, values=values, **options)
    frames = len(values) // 2
    wet = render(effect.output, frames, rate, probe=probe_name)
    effect.deinit()
    return values, wet, frames


def settled_change(values, wet, frames, hz, rate):
    """A band's change in dB, measured over a window in the settled middle
    of the render rather than across the attack."""
    count = min(4800, frames // 4)
    first = frames // 2
    return (band_db(wet.data.reshape(-1).tolist(), hz, rate, 2, first, count)
            - band_db(values, hz, rate, 2, first, count))


# --------------------------------------------------------------------------


class Tier1(unittest.TestCase):
    """The standard invariant block, on CPython, at three rates."""

    def test_wire_at_range_zero_is_byte_identical(self):
        """WIRE. Range 0 in broadband mode is the class's `mix` at zero,
        and the dossier's section 8.2 is why it is exact: broadband mode
        carries no audio split, so there is nothing to sum."""
        for rate in RATES:
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
        find, comes through at unity."""
        for rate in RATES:
            values = tone(200, 12000, 24000, rate)
            effect, _holder = build(rate=rate, values=values)
            wet = render(effect.output, 24000, rate)
            dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
            result = M.level(wet, dry, tolerance_db=0.05, skip_frames=2048)
            effect.deinit()
            print("\n  LEVEL %5d Hz: %s" % (rate, result["values"]))
            self.assertEqual(result["red"], [], "%d Hz" % rate)

    def test_tail_reaches_exact_zero(self):
        """TAIL. Burst then silence: the crossover's state has to reach
        exact zero, which is what `audiobiquad` exists for."""
        for rate in RATES:
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
        span, where the Butterworth pair rings longest."""
        for rate in RATES:
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

    def test_latency_is_zero_at_48k_and_44k1(self):
        """CLICK. The reported `latency_samples` against the measured
        click delay, at the two rates the gate names."""
        for rate in (48000, 44100):
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
        """
        rate = 48000
        values = probe("noise_det", rate)
        effect, holder = build(rate=rate, values=values)
        quiet = source(silence(len(values) // 2), rate)
        nodes = [("node%d" % index, node)
                 for index, node in enumerate(effect._nodes)
                 if hasattr(node, "_get_buffer")]
        # Read before `M.state` runs: its last act is `deinit()`, after
        # which every property on the live surface raises.
        self.assertEqual(effect.capabilities, ())
        result = M.state(
            effect,
            pull=lambda blocks: render(effect.output, blocks * 256, rate),
            swap=lambda new: effect._adapter.play(new),
            probe_source=holder, silent_source=quiet, blocks=32,
            nodes=nodes)
        print("\n  STATE: %s" % result["values"])
        self.assertEqual(result["red"], [])

    def test_mono_gets_the_same_processing(self):
        """The invariants also hold at `channel_count` 1, and the dossier's
        section 4 says a mono source gets identical processing."""
        rate = 48000
        values = probe("ramp_fs", rate, channels=1)
        effect, _holder = build(rate=rate, channels=1, values=values,
                                range_db=0.0)
        frames = len(values)
        wet = render(effect.output, frames, rate, channels=1)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 1)
        result = M.wire(wet, dry, latency_samples=0)
        print("\n  MONO WIRE: %s" % result["values"])
        self.assertEqual(result["red"], [])
        self.assertEqual(effect.channel_count, 1)
        effect.deinit()

    def test_frequency_clamps_below_nyquist_rather_than_refusing(self):
        """Rate honesty. The Frequency span tops at 8 kHz, which is below
        Nyquist at every rate the gate names, so it never clamps - and the
        clamp is still shown to exist, by asking for more than the rate
        has."""
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
        """D6. A sine and a square of equal RMS get the same reduction.

        `square_1k_*_rms` is the kit's matched-RMS pair for `sine_1k_*`.
        The split goes below both so the whole tone is in the detector's
        band, which is what the trait is about.
        """
        rate = 48000
        readings = {}
        for name in ("sine_1k_-6", "square_1k_-6_rms"):
            values, wet, frames = deess(rate, name, frequency=800.0,
                                        range_db=20.0, sensitivity_db=6.0)
            readings[name] = settled_change(values, wet, frames, 1000, rate)
        gap = abs(readings["sine_1k_-6"] - readings["square_1k_-6_rms"])
        print("\n  D6 48000 Hz: sine %.3f square(rms) %.3f gap %.3f dB"
              % (readings["sine_1k_-6"], readings["square_1k_-6_rms"], gap))
        self.assertLess(gap, 0.5)

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
            values = tone(200, 12000, 24000, rate)
            effect, _holder = build(rate=rate, values=values, range_db=20.0,
                                    sensitivity_db=sensitivity)
            wet = render(effect.output, 24000, rate)
            resting[sensitivity] = settled_change(values, wet, 24000, 200,
                                                  rate)
            effect.deinit()
        print("\n  D7 48000 Hz: %s | resting gain on the low tone %s"
              % ({k: round(v, 3) for k, v in reached.items()},
                 {k: round(v, 4) for k, v in resting.items()}))
        self.assertLess(abs(resting[30.0]), 0.1)

    def test_d2_tracking_half_and_d8_flat_sum(self):
        """D2's tracking clause and D8's flat sum, together, because both
        read the same render: HF-only mode at Range 0 is the crossover's
        own sum, and the corner has to move with the Frequency macro.

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
                values = tone(hz, 12000, 24000, rate)
                effect, _holder = build(rate=rate, values=values,
                                        frequency=corner, range_db=0.0,
                                        hf_only=True)
                wet = render(effect.output, 24000, rate)
                summed.append((hz, settled_change(values, wet, 24000, hz,
                                                  rate)))
                effect.deinit()
            print("\n  D8 corner %6.0f Hz: %s"
                  % (corner, [(int(h), round(d, 3)) for h, d in summed]))
            for _hz, deviation in summed:
                self.assertLess(abs(deviation), 0.25)

        # D2's tracking clause: the high half's -3 dB point moves with the
        # macro. Measured on the high band alone, which is what the Listen
        # path exposes and what the detector follows.
        corners = []
        for corner in (800.0, 2500.0, 8000.0):
            hz = corner
            values = tone(hz, 12000, 24000, rate)
            effect, _holder = build(rate=rate, values=values,
                                    frequency=corner, range_db=20.0,
                                    sensitivity_db=0.0, hf_only=True)
            # Range 20 with Sensitivity 0 never ducks, so the high voice is
            # attenuated by 1 - alpha and the low voice is at unity: the
            # ratio between them is the crossover's own split at `hz`.
            wet = render(effect.output, 24000, rate)
            corners.append((corner, settled_change(values, wet, 24000, hz,
                                                   rate)))
            effect.deinit()
        print("\n  D2 tracking: %s"
              % [(int(c), round(d, 3)) for c, d in corners])
        for _corner, deviation in corners:
            # At its own corner an LR4 pair is -6 dB a side, so the blended
            # sum sits between the two levels at every setting - the point
            # is that it is the *same* number at all three, i.e. the corner
            # moved with the macro.
            self.assertLess(abs(deviation - corners[0][1]), 0.5)

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
        """D4, disconfirmed on purpose, and measured rather than asserted.

        The trait asks for a straight line in dB at 925 dB/sec.
        `audiodynamics` releases with a one-pole in linear gain, which is a
        curve in dB at every coefficient. This test holds the class to what
        it *is*, so the day N-DEESS-2 lands it fails and someone re-reads
        the trait.
        """
        rate = 48000
        values = sibilant_burst(rate, low_hz=1000.0, seconds=2.0,
                                burst=(0.5, 1.0))
        effect, _holder = build(rate=rate, values=values, range_db=12.0,
                                sensitivity_db=36.0, release_ms=3.0)
        frames = len(values) // 2
        wet = render(effect.output, frames, rate)
        dry = M.Render.from_pcm(values.tobytes()[:len(wet.pcm)], rate, 2)
        trace = M.gaintrace(wet, dry, hop_ms=1.0, release_from_ms=1000.0)
        effect.deinit()
        rows = trace["values"]
        marks = [(t, g) for t, g in zip(rows["trace_ms"], rows["trace_gr_db"])
                 if g is not None and 1000.0 <= t <= 1060.0]
        stamps = [t for t, _g in marks]
        series = [g for _t, g in marks]
        begin, end = series[0], series[-1]
        # A straight line in dB from `begin` to `end` over the same span;
        # the deviation from it is what says the recovery curves.
        span = stamps[-1] - stamps[0]
        straight = [begin + (end - begin) * (t - stamps[0]) / span
                    for t in stamps]
        deviation = max(abs(a - b) for a, b in zip(series, straight))
        t63 = rows.get("release_t63_ms")
        rate_db_s = (None if t63 in (None, 0)
                     else abs(end - begin) * 0.63 / (t63 / 1000.0))
        print("\n  D4 48000 Hz: from %.2f dB to %.2f dB, t63 %s ms, "
              "mean rate %s dB/sec, worst deviation from a straight dB line "
              "%.2f dB (the 902 asks for ~0)"
              % (begin, end, t63, None if rate_db_s is None
                 else round(rate_db_s, 1), deviation))
        self.assertGreater(deviation, 0.5)

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
        values = probe("noise_det", rate)
        effect, holder = build(rate=rate, values=values)
        quiet = source(silence(len(values) // 2), rate)
        # The fault: the reset walk without the ring flush, which is what
        # the class did before `_reset_chain` existed.
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
        effect2, holder2 = build(rate=rate, values=probe("noise_det", rate))
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
            values = probe("sibilant_" + level_tag, rate)
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
        values = probe("sibilant_-6", rate)
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

    def test_d6_goes_red_on_a_peak_detector(self):
        """D6's fault of the same kind: `detector="peak"`, which is what
        the node does without the option D6 asked Phase 1 for."""
        rate = 48000
        readings = {}
        for name in ("sine_1k_-6", "square_1k_-6_rms"):
            values = probe(name, rate)
            effect, _holder = build(rate=rate, values=values,
                                    frequency=800.0, range_db=20.0,
                                    sensitivity_db=6.0)
            effect._duck.set(detector="peak")
            frames = len(values) // 2
            wet = render(effect.output, frames, rate)
            readings[name] = settled_change(values, wet, frames, 1000, rate)
            effect.deinit()
        gap = abs(readings["sine_1k_-6"] - readings["square_1k_-6_rms"])
        print("\n  D6 fault (peak detector): sine %.3f square %.3f gap %.3f"
              % (readings["sine_1k_-6"], readings["square_1k_-6_rms"], gap))
        self.assertGreater(gap, 0.5)

    def test_d7_goes_red_when_the_range_blend_is_removed(self):
        """D7's fault: the wet path at unity with no dry beside it, which
        is a de-esser with no maximum - the third defect section 7 names."""
        rate = 48000
        values = probe("sibilant_-6", rate)
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
        values = tone(corner, 12000, 24000, rate)
        effect, _holder = build(rate=rate, values=values, frequency=corner,
                                range_db=0.0, hf_only=True)
        clean = render(effect.output, 24000, rate)
        self.assertLess(abs(settled_change(values, clean, 24000, corner,
                                           rate)), 0.25,
                        "the control failed")
        effect.deinit()

        effect2, _holder2 = build(rate=rate, values=tone(corner, 12000,
                                                        24000, rate),
                                  frequency=corner, range_db=0.0,
                                  hf_only=True)
        # The fault: the second section of each half pushed far out of the
        # way, leaving one 12 dB/octave section a side.
        effect2._lows[1].frequency = rate * 0.45
        effect2._highs[1].frequency = 20.0
        faulted = render(effect2.output, 24000, rate)
        deviation = settled_change(values, faulted, 24000, corner, rate)
        effect2.deinit()
        print("\n  D8 fault (one section a side): %+.3f dB at the corner"
              % deviation)
        self.assertGreater(abs(deviation), 0.25)


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
