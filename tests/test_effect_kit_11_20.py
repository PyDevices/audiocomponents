"""The planted-fault battery for measurements 11-20 of the kit spec.

`docs/effects-kit-spec.md` section 6: a measurement whose planted-fault run
is not committed is not one a class gate may cite, and every fault lands
beside **a control that must pass**, or the battery only proves the checker
always fails.

So every measurement below gets at least two runs of the same code: the
build with nothing wrong with it, which must come back green, and the
build with the spec's own fault in it, which must come back red **on the
readout the spec names** - not merely red somewhere. Several get a third:
the run that shows the fault would *not* have fired on the wrong material,
because "the material cannot reach the mechanism" is the failure this kit
was refuted against.

Two of the ten are the first ten's, and are here because this part of the
brief names them again: CLICK's latency read at both rates, and DIGEST's
byte comparison. Their implementations are part B's `click()` and
`digest()`; what is added here is the planted-fault run for each -
including a real cross-interpreter comparison, CPython against desktop
MicroPython, rendering the same node.

    python -m unittest tests.test_effect_kit_11_20 -v
"""

import math
import os
import subprocess
import sys
import tempfile
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.effect_measurements import (  # noqa: E402
    MeasurementRefused, Render, SilentRenderError, click, cost, decay,
    digest, envelope_record_seconds, envelope_shape, ifreq, null, residual,
    require_identical_channels, roundtrip, stereo, taps, truepeak,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RATE = 48000
MICROPYTHON = os.path.join(ROOT, "..", "cmods", "bin", "micropython")


def make_render(x, rate=RATE, **axes):
    """A `Render` from float samples. Mono is duplicated to stereo, which is
    what every probe in section 3 that is not deliberately decorrelated
    does."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.column_stack([x, x])
    pcm = np.round(np.clip(x, -1.0, 32767.0 / 32768.0)
                   * 32768.0).astype("<i2").tobytes()
    return Render(pcm, rate, x.shape[1], **axes)


# --------------------------------------------------------------------------
# 11 ENVELOPE
# --------------------------------------------------------------------------

class Envelope(unittest.TestCase):
    """Planted fault: replace the shaped LFO with a pure sine at the same
    rate and depth. Rate and depth stay green; duty, slope ratio and the
    rate harmonics go red - the control and the fault in one run."""

    RATE_HZ = 5.0
    SECONDS = 6.0

    def setUp(self):
        self.t = np.arange(int(self.SECONDS * RATE)) / float(RATE)
        self.carrier = np.sin(2 * math.pi * 1000.0 * self.t)

    def shaped(self, attack=0.06, tau=0.18):
        """Fast attack, exponential decay - a tremolo LFO with a shape."""
        phase = (self.t * self.RATE_HZ) % 1.0
        return np.where(phase < attack, phase / attack,
                        np.exp(-(phase - attack) / tau))

    def envelopes(self):
        """The shaped modulator, and the pure sine that is the planted
        fault: same offset, same fitted fundamental amplitude, so the fault
        is genuinely 'at the same rate and depth'."""
        shaped = 0.2 + 0.8 * self.shaped()
        offset = shaped.mean()
        component = 2 * np.mean(shaped * np.exp(
            -2j * math.pi * self.RATE_HZ * self.t))
        sine = offset + abs(component) * np.cos(
            2 * math.pi * self.RATE_HZ * self.t + np.angle(component))
        return shaped, sine

    def test_control_and_planted_fault(self):
        shaped, sine = self.envelopes()
        trait = {"rate_hz": 5.0, "depth_db": 12.14, "duty_pct": 19.0,
                 "slope_ratio": 2.10, "harmonic_db": -4.44}

        control = envelope_shape(make_render(shaped * self.carrier),
                                 expected=trait)
        print("\nENVELOPE control    rate %.4f Hz  depth %.2f dB  duty %.1f%%"
              "  slope %.3f  h2 %.2f dB"
              % (control["values"]["rate_hz"], control["values"]["depth_db"],
                 control["values"]["duty_pct"],
                 control["values"]["slope_ratio"],
                 control["values"]["harmonic_db"][0]))
        self.assertTrue(control["passed"], control["red"])

        faulted = envelope_shape(make_render(sine * self.carrier),
                                 expected=trait)
        print("ENVELOPE pure-sine  rate %.4f Hz  depth %.2f dB  duty %.1f%%"
              "  slope %.3f  h2 %.2f dB"
              % (faulted["values"]["rate_hz"], faulted["values"]["depth_db"],
                 faulted["values"]["duty_pct"],
                 faulted["values"]["slope_ratio"],
                 faulted["values"]["harmonic_db"][0]))
        for line in faulted["red"]:
            print("   RED", line)
        self.assertFalse(faulted["passed"])
        failed = faulted["values"]["failed_readouts"]
        self.assertEqual(sorted(failed),
                         ["duty_pct", "harmonic_db", "slope_ratio"])
        self.assertNotIn("rate_hz", failed)
        self.assertNotIn("depth_db", failed)

    def test_record_length_rule_is_the_measurement(self):
        """A 20 s record at 0.667 Hz passes anything; the rule asks 120 s."""
        self.assertAlmostEqual(envelope_record_seconds(0.667, 0.025), 119.94,
                               places=1)
        rate_hz = 0.667
        seconds = 20.0
        t = np.arange(int(seconds * RATE)) / float(RATE)
        modulated = (0.6 + 0.4 * np.cos(2 * math.pi * rate_hz * t)) \
            * np.sin(2 * math.pi * 1000.0 * t)
        short = envelope_shape(make_render(modulated), rate_hint=rate_hz,
                               rate_tolerance=0.025)
        print("\nENVELOPE 20 s record at 0.667 Hz -> required %.1f s, red %s"
              % (short["values"]["required_seconds"], short["red"]))
        self.assertFalse(short["passed"])
        self.assertIn("record_seconds", short["values"]["failed_readouts"])

        long_enough = envelope_shape(
            make_render(modulated), rate_hint=rate_hz, rate_tolerance=0.15)
        self.assertTrue(long_enough["passed"], long_enough["red"])


# --------------------------------------------------------------------------
# 12 IFREQ
# --------------------------------------------------------------------------

class InstantaneousFrequency(unittest.TestCase):
    """Planted fault: omit the splice-period correction where a granular
    shifter is in the path, and watch a CORRECT build read red. The control
    that must pass beside it is the same uncorrected reading on a path with
    no shifter in it."""

    CARRIER = 440.0
    RATE_HZ = 5.0
    CENTS = 50.0
    SPLICE = 960  # 20 ms grains

    def setUp(self):
        seconds = 2.0
        self.t = np.arange(int(seconds * RATE)) / float(RATE)
        deviation = self.CARRIER * (2 ** (self.CENTS / 1200.0) - 1.0)
        instantaneous = self.CARRIER + deviation * np.cos(
            2 * math.pi * self.RATE_HZ * self.t)
        self.phase = 2 * math.pi * np.cumsum(instantaneous) / RATE
        self.clean = np.sin(self.phase)
        grain = np.arange(len(self.t)) // self.SPLICE
        jump = (math.pi / 3.0) * np.where(grain % 2 == 0, 1.0, -1.0)
        self.spliced = np.sin(self.phase + jump)

    def read(self, signal, **kwargs):
        return ifreq(make_render(signal), self.RATE_HZ,
                     carrier_hz=self.CARRIER, expected_cents=self.CENTS,
                     **kwargs)

    def test_control_no_shifter_uncorrected_stays_green(self):
        control = self.read(self.clean)
        print("\nIFREQ control (no shifter, uncorrected)  dev %.3f cents  "
              "residual %.4f cents" % (control["values"]["deviation_cents"],
                                       control["values"]["residual_rms_cents"]))
        self.assertTrue(control["passed"], control["red"])

    def test_planted_fault_correction_omitted_reddens_a_correct_build(self):
        faulted = self.read(self.spliced)
        print("IFREQ FAULT (shifter, correction omitted)  dev %.3f cents  "
              "residual %.3f cents" % (faulted["values"]["deviation_cents"],
                                       faulted["values"]["residual_rms_cents"]))
        for line in faulted["red"]:
            print("   RED", line)
        self.assertFalse(faulted["passed"])
        self.assertIn("residual_rms_cents",
                      faulted["values"]["failed_readouts"])

        corrected = self.read(self.spliced,
                              splice_period_samples=self.SPLICE)
        print("IFREQ corrected (same build)               dev %.3f cents  "
              "residual %.3f cents"
              % (corrected["values"]["deviation_cents"],
                 corrected["values"]["residual_rms_cents"]))
        self.assertTrue(corrected["passed"], corrected["red"])


# --------------------------------------------------------------------------
# 13 TAPS -- against the live node, not a synthetic stand-in
# --------------------------------------------------------------------------

class Taps(unittest.TestCase):
    """The spec's model planted fault, and the only one in the kit that is
    already measured rather than hypothetical: `audiodelays.Echo` built with
    `freq_shift=False` on `_core.pcm()`'s 2048-byte buffer delivers 21.33 ms
    for every setting below it.

    The flag is the load-bearing detail. With the node's default
    `freq_shift=True` there is no floor, every setting lands within 0.02 ms,
    and a fault planted that way does not fire at all - so the third test
    here is the one that proves this checker CAN fail."""

    BUFFER_BYTES = 2048  # lib/audioeffects/_core.py:pcm()'s default
    FLOOR_MS = 21.333    # two 512-frame stereo blocks at 48 kHz

    def echo_render(self, delay_ms, freq_shift):
        import audiocore
        import audiodelays
        from tests.support.kit_probes import render
        frames = int(0.25 * RATE)
        values = array("h", [0] * (frames * 2))
        values[0] = values[1] = 20000
        source = audiocore.RawSample(values, sample_rate=RATE,
                                     channel_count=2)
        node = audiodelays.Echo(
            max_delay_ms=500, delay_ms=delay_ms, decay=0.7, mix=1.0,
            buffer_size=self.BUFFER_BYTES, sample_rate=RATE,
            bits_per_sample=16, samples_signed=True, channel_count=2,
            freq_shift=freq_shift)
        node.play(source)
        return render(node, frames, rate=RATE, channels=2,
                      block=self.BUFFER_BYTES // 4, probe="impulse",
                      class_name="audiodelays.Echo",
                      label="delay_ms=%s freq_shift=%s"
                      % (delay_ms, freq_shift))

    def test_planted_fault_settings_below_the_buffer_go_red(self):
        print("\nTAPS  audiodelays.Echo(freq_shift=False) at a %d-byte buffer"
              % self.BUFFER_BYTES)
        reds = []
        for delay_ms in (1, 5, 14):
            result = taps(self.echo_render(delay_ms, False),
                          expected_ms=delay_ms, tolerance_ms=0.5)
            print("   set %2d ms -> measured %7.3f ms   %s"
                  % (delay_ms, result["values"]["first_tap_ms"],
                     "RED" if not result["passed"] else "green"))
            self.assertFalse(result["passed"], result["values"])
            self.assertIn("first_tap_ms", result["values"]["failed_readouts"])
            self.assertAlmostEqual(result["values"]["first_tap_ms"],
                                   self.FLOOR_MS, places=2)
            reds.append(result["red"][0])
        print("   " + reds[0])

    def test_control_settings_above_the_buffer_stay_green(self):
        for delay_ms in (30, 40):
            result = taps(self.echo_render(delay_ms, False),
                          expected_ms=delay_ms, tolerance_ms=0.5)
            print("   set %2d ms -> measured %7.3f ms   %s"
                  % (delay_ms, result["values"]["first_tap_ms"],
                     "RED" if not result["passed"] else "green"))
            self.assertTrue(result["passed"], result["red"])

    def test_the_fault_does_not_fire_with_freq_shift_on(self):
        """Plant it with the node's default and the checker cannot fail."""
        print("   with freq_shift=True (the default), no floor:")
        for delay_ms in (1, 5, 14, 30, 40):
            result = taps(self.echo_render(delay_ms, True),
                          expected_ms=delay_ms, tolerance_ms=0.5)
            print("   set %2d ms -> measured %7.3f ms   %s"
                  % (delay_ms, result["values"]["first_tap_ms"],
                     "RED" if not result["passed"] else "green"))
            self.assertTrue(result["passed"], result["red"])
            self.assertLess(abs(result["values"]["error_ms"]), 0.03)


# --------------------------------------------------------------------------
# 14 DECAY
# --------------------------------------------------------------------------

class Decay(unittest.TestCase):
    """Planted fault: apply the darkening once at the input instead of
    inside the loop. Repeat one stays correct and the progression goes flat,
    which is the fault a single-repeat check cannot see."""

    REPEAT_MS = 100.0
    REPEATS = 6
    GAIN = 0.72

    def burst(self, ms=5.0, seed=99):
        state, values = seed, []
        for _ in range(int(RATE * ms / 1000.0)):
            state = (1103515245 * state + 12345) & 0x7fffffff
            values.append((state / 0x3fffffff) - 1.0)
        return np.array(values) * 0.9

    @staticmethod
    def one_pole(x, hz=2500.0):
        alpha = 1.0 - math.exp(-2 * math.pi * hz / RATE)
        out, state = np.empty_like(x), 0.0
        for index, value in enumerate(x):
            state += alpha * (value - state)
            out[index] = state
        return out

    def build(self, in_loop):
        total = int(RATE * (self.REPEAT_MS * (self.REPEATS + 1)) / 1000.0)
        out = np.zeros(total)
        burst = self.burst()
        darkened = self.one_pole(burst)
        for repeat in range(1, self.REPEATS + 1):
            start = int(RATE * self.REPEAT_MS * repeat / 1000.0)
            if in_loop:
                shaped = burst.copy()
                for _ in range(repeat):
                    shaped = self.one_pole(shaped)
            else:
                shaped = darkened
            out[start:start + len(shaped)] += shaped * self.GAIN ** repeat
        return make_render(out)

    def test_control_and_planted_fault(self):
        control = decay(self.build(in_loop=True), darkening_bar_db=-0.5)
        faulted = decay(self.build(in_loop=False), darkening_bar_db=-0.5)
        print("\nDECAY  HF band share per repeat, dB")
        print("   in the loop (control): %s"
              % [round(v, 2) for v in control["values"]["high_band_share_db"]])
        print("   at the input (fault) : %s"
              % [round(v, 2) for v in faulted["values"]["high_band_share_db"]])
        print("   slope: control %.3f dB/repeat, fault %.3f dB/repeat"
              % (control["values"]["darkening_slope_db_per_repeat"],
                 faulted["values"]["darkening_slope_db_per_repeat"]))
        self.assertTrue(control["passed"], control["red"])
        self.assertFalse(faulted["passed"])
        self.assertIn("darkening_slope_db_per_repeat",
                      faulted["values"]["failed_readouts"])
        for line in faulted["red"]:
            print("   RED", line)

    def test_repeat_one_agrees_so_a_single_repeat_check_sees_nothing(self):
        control = decay(self.build(in_loop=True), darkening_bar_db=-0.5)
        faulted = decay(self.build(in_loop=False), darkening_bar_db=-0.5)
        first = (control["values"]["first_repeat_share_db"],
                 faulted["values"]["first_repeat_share_db"])
        print("   repeat one: control %.3f dB, fault %.3f dB (agree to "
              "%.3f dB, against a progression that differs by 3.3 dB per "
              "repeat)" % (first[0], first[1], abs(first[0] - first[1])))
        self.assertAlmostEqual(first[0], first[1], places=1)
        self.assertLess(abs(first[0] - first[1]), 0.05)


# --------------------------------------------------------------------------
# 15 STEREO
# --------------------------------------------------------------------------

class Stereo(unittest.TestCase):
    """Planted fault: the seeds' own - measure down one channel instead of
    across both. A ping-pong that is really two independent delays at half
    rate has exactly the right taps in each channel taken alone."""

    TAP_MS = 60.0
    TAPS = 6

    def click_at(self, out, ms, channel, level):
        index = int(RATE * ms / 1000.0)
        out[index, channel] = level

    def ping_pong(self):
        total = int(RATE * self.TAP_MS * (self.TAPS + 2) / 1000.0)
        out = np.zeros((total, 2))
        for tap in range(1, self.TAPS + 1):
            self.click_at(out, self.TAP_MS * tap, (tap - 1) % 2,
                          0.9 * 0.8 ** tap)
        return make_render(out)

    def two_independent_delays(self):
        """Each channel its own line at twice the delay - per channel this
        is indistinguishable from the ping-pong above."""
        total = int(RATE * self.TAP_MS * (self.TAPS + 2) / 1000.0)
        out = np.zeros((total, 2))
        for tap in range(1, self.TAPS // 2 + 1):
            when = self.TAP_MS * 2 * tap
            self.click_at(out, when, 0, 0.9 * 0.8 ** (2 * tap - 1))
            self.click_at(out, when, 1, 0.9 * 0.8 ** (2 * tap))
        return make_render(out)

    def test_control_ping_pong_alternates(self):
        result = stereo(self.ping_pong(), require_alternation=True)
        print("\nSTEREO control  clusters %s  correlation %.3f"
              % ([c["channels"] for c in result["values"]["arrival_clusters"]],
                 result["values"]["correlation"]))
        self.assertTrue(result["passed"], result["red"])
        self.assertTrue(result["values"]["ping_pong_alternates"])

    def test_planted_fault_two_independent_delays_go_red(self):
        result = stereo(self.two_independent_delays(),
                        require_alternation=True)
        print("STEREO FAULT    clusters %s  correlation %.3f"
              % ([c["channels"] for c in result["values"]["arrival_clusters"]],
                 result["values"]["correlation"]))
        for line in result["red"]:
            print("   RED", line)
        self.assertFalse(result["passed"])
        self.assertIn("ping_pong_alternates",
                      result["values"]["failed_readouts"])

    def test_the_one_channel_read_passes_both(self):
        """Why the fault is worth planting: down one channel the two builds
        are the same measurement."""
        for label, render in (("ping-pong", self.ping_pong()),
                              ("two delays", self.two_independent_delays())):
            result = taps(render, channel=1, expected_ms=2 * self.TAP_MS,
                          tolerance_ms=0.5,
                          expected_spacing_ms=2 * self.TAP_MS)
            print("   down channel R, %-11s first tap %.3f ms, spacing "
                  "%.3f ms -> %s"
                  % (label, result["values"]["first_tap_ms"],
                     result["values"]["repeat_spacing_ms"],
                     "green" if result["passed"] else "RED"))
            self.assertTrue(result["passed"], result["red"])

    def test_a_decorrelated_probe_is_refused(self):
        frames = 4096
        pcm = np.zeros((frames, 2), dtype="<i2")
        pcm[:, 0] = 1000
        pcm[:, 1] = -1000
        with self.assertRaises(MeasurementRefused) as caught:
            require_identical_channels(pcm.tobytes())
        print("   decorrelated probe refused: %s" % caught.exception)


# --------------------------------------------------------------------------
# 16 RESIDUAL
# --------------------------------------------------------------------------

class Residual(unittest.TestCase):
    """Planted fault: truncation replaced by rounding at the same word
    length. The mean goes to zero and fires; the RMS moves from 0.577 to
    0.289 LSB and stays inside any bar a residual RMS would be given, so it
    does not.

    And the probe is load-bearing: on material symmetric about zero,
    truncation toward zero also has a zero mean, so a rounding build and a
    truncating one read identically and the fault does not fire at all."""

    BITS = 8

    def biased_ramp(self, frames=48000):
        """The half-scale-biased ramp: every truncation mode leaves a mean
        on it, and only round-to-nearest does not."""
        return 0.25 + 0.5 * np.arange(frames) / float(frames)

    def sweep(self, frames=48000):
        """Symmetric about zero - the material this measurement must
        refuse."""
        t = np.arange(frames) / float(RATE)
        return 0.5 * np.sin(2 * math.pi * 400.0 * t * (1 + 4 * t))

    @staticmethod
    def truncate_floor(x, bits):
        step = 2.0 ** -(bits - 1)
        return np.floor(x / step) * step

    @staticmethod
    def truncate_toward_zero(x, bits):
        step = 2.0 ** -(bits - 1)
        return np.trunc(x / step) * step

    @staticmethod
    def round_nearest(x, bits):
        step = 2.0 ** -(bits - 1)
        return np.round(x / step) * step

    def test_control_truncation_and_the_planted_rounding_fault(self):
        probe = self.biased_ramp()
        reference = make_render(probe)
        control = residual(make_render(self.truncate_floor(probe, self.BITS)),
                           reference, self.BITS, expect="truncation")
        faulted = residual(make_render(self.round_nearest(probe, self.BITS)),
                           reference, self.BITS, expect="truncation")
        print("\nRESIDUAL on the DC-offset probe (probe mean %.3f FS)"
              % control["values"]["probe_mean_fs"])
        print("   truncation (control): mean %+.4f LSB, RMS %.4f LSB -> %s"
              % (control["values"]["mean_lsb"], control["values"]["rms_lsb"],
                 "green" if control["passed"] else "RED"))
        print("   rounding   (fault)  : mean %+.4f LSB, RMS %.4f LSB -> %s"
              % (faulted["values"]["mean_lsb"], faulted["values"]["rms_lsb"],
                 "green" if faulted["passed"] else "RED"))
        for line in faulted["red"]:
            print("   RED", line)
        self.assertTrue(control["passed"], control["red"])
        self.assertFalse(faulted["passed"])
        self.assertEqual(faulted["values"]["failed_readouts"], ["mean_lsb"])
        self.assertLess(control["values"]["rms_lsb"], 1.0)
        self.assertLess(faulted["values"]["rms_lsb"], 1.0)

    def test_the_dc_offset_probe_is_what_makes_the_fault_fire(self):
        """Truncation toward zero on symmetric material has a zero mean:
        the same fault, on the wrong probe, does not fire."""
        symmetric = self.sweep()
        reading = residual(
            make_render(self.truncate_toward_zero(symmetric, self.BITS)),
            make_render(symmetric), self.BITS, expect="truncation",
            require_dc_probe=False)
        print("   truncate-toward-zero on a SWEEP: mean %+.4f LSB -> the "
              "fault would not fire (%s)"
              % (reading["values"]["mean_lsb"],
                 "green" if reading["passed"] else "RED"))
        self.assertLess(abs(reading["values"]["mean_lsb"]), 0.25)

        biased = self.biased_ramp()
        on_dc = residual(
            make_render(self.truncate_toward_zero(biased, self.BITS)),
            make_render(biased), self.BITS, expect="truncation")
        print("   the same build on the DC-offset probe: mean %+.4f LSB -> "
              "%s" % (on_dc["values"]["mean_lsb"],
                      "green" if on_dc["passed"] else "RED"))
        self.assertTrue(on_dc["passed"], on_dc["red"])

    def test_symmetric_material_is_refused_by_default(self):
        symmetric = self.sweep()
        with self.assertRaises(MeasurementRefused) as caught:
            residual(make_render(self.truncate_floor(symmetric, self.BITS)),
                     make_render(symmetric), self.BITS)
        print("   refused: %s" % caught.exception)


# --------------------------------------------------------------------------
# 17 TRUEPEAK
# --------------------------------------------------------------------------

class TruePeak(unittest.TestCase):
    """Planted fault: read the sample peak instead of the 4x oversampled
    one. The red is against the CEILING in dB TP, not against the other
    setting - the two sample peaks do not collapse to one number."""

    CEILING = -6.0

    def tone_fs4(self, seconds=0.25, sample_peak_dbfs=-6.0):
        """The worst-phase f_s/4 tone `Limiter` L1 requires: sampled at 45
        degrees, every sample lands on +/- A/sqrt(2), so the sample peak
        sits 3.01 dB below the true peak. (Section 3's corpus is
        `tools/effect_probes/`; this is the generator, kept beside the test
        that needs it until that corpus lands.)"""
        count = int(seconds * RATE)
        amplitude = 10.0 ** (sample_peak_dbfs / 20.0) * math.sqrt(2.0)
        return amplitude * np.sin(2 * math.pi * np.arange(count) / 4.0
                                  + math.pi / 4.0)

    def test_planted_fault_sample_peak_certifies_a_ceiling_that_escapes(self):
        render = make_render(self.tone_fs4(sample_peak_dbfs=self.CEILING))
        correct = truepeak(render, ceiling_dbfs=self.CEILING)
        faulted = truepeak(render, ceiling_dbfs=self.CEILING,
                           read="sample_peak")
        print("\nTRUEPEAK  worst-phase f_s/4 tone, ceiling %.2f dBFS"
              % self.CEILING)
        print("   sample peak %.2f dBFS, true peak %.2f dB TP (excess "
              "%.2f dB)" % (correct["values"]["sample_peak_dbfs"],
                            correct["values"]["true_peak_dbtp"],
                            correct["values"]["inter_sample_excess_db"]))
        print("   correct read -> %s" % ("green" if correct["passed"]
                                         else "RED"))
        for line in correct["red"]:
            print("   RED", line)
        print("   faulted read (sample peak) -> %s"
              % ("green" if faulted["passed"] else "RED"))
        self.assertFalse(correct["passed"])
        self.assertIn("true_peak_dbtp", correct["values"]["failed_readouts"])
        self.assertTrue(faulted["passed"],
                        "the faulted read must certify the ceiling as met - "
                        "that is what makes it worth planting")
        self.assertGreater(correct["values"]["over_ceiling_db"], 2.5)

    def test_control_a_true_peak_aware_limiter_passes(self):
        render = make_render(self.tone_fs4(sample_peak_dbfs=self.CEILING
                                           - 3.02))
        result = truepeak(render, ceiling_dbfs=self.CEILING)
        print("   control (true-peak aware): sample peak %.2f dBFS, true "
              "peak %.2f dB TP -> %s"
              % (result["values"]["sample_peak_dbfs"],
                 result["values"]["true_peak_dbtp"],
                 "green" if result["passed"] else "RED"))
        self.assertTrue(result["passed"], result["red"])

    def test_without_the_fs4_tone_the_fault_does_not_fire(self):
        """L1's disconfirmation clause, run: on a 1 kHz tone the two reads
        agree and a limiter with no true-peak detection reads green."""
        t = np.arange(int(0.25 * RATE)) / float(RATE)
        tone = 10.0 ** (self.CEILING / 20.0) * np.sin(2 * math.pi * 1000 * t)
        correct = truepeak(make_render(tone), ceiling_dbfs=self.CEILING)
        faulted = truepeak(make_render(tone), ceiling_dbfs=self.CEILING,
                           read="sample_peak")
        print("   on a 1 kHz tone: sample %.2f dBFS, true %.2f dB TP - both "
              "reads %s"
              % (correct["values"]["sample_peak_dbfs"],
                 correct["values"]["true_peak_dbtp"],
                 "green" if correct["passed"] and faulted["passed"] else
                 "disagree"))
        self.assertTrue(correct["passed"], correct["red"])
        self.assertTrue(faulted["passed"], faulted["red"])
        self.assertLess(correct["values"]["inter_sample_excess_db"], 0.5)


# --------------------------------------------------------------------------
# 18 NULL
# --------------------------------------------------------------------------

class Null(unittest.TestCase):
    """`Octaver` O3's planted fault: null OCT1's modulator, and OCT2 must
    fall below -80 dBFS. Re-wire OCT2 from the dry tap and it does not."""

    FLOOR = -80.0

    def parts(self, frames=24000):
        t = np.arange(frames) / float(RATE)
        dry = 0.5 * np.sin(2 * math.pi * 220.0 * t)
        oct1 = 0.3 * np.sin(2 * math.pi * 110.0 * t)
        return dry, oct1

    def build(self, from_dry_tap):
        """Both renders are of the same build with OCT1's modulator nulled.
        `a` is the full output, `b` is the same output with OCT2 removed -
        so a correct build nulls, and a build whose OCT2 comes off the dry
        tap has OCT2 in `a` and not in `b`."""
        dry, oct1 = self.parts()
        oct2 = dry * 0.7 if from_dry_tap else np.zeros_like(dry)
        return make_render(dry + oct1 + oct2), make_render(dry + oct1)

    def test_control_the_unmodified_build_nulls(self):
        a, b = self.build(from_dry_tap=False)
        result = null(a, b, floor_dbfs=self.FLOOR)
        print("\nNULL control  depth %.1f dBFS against a %.1f floor "
              "(reference %.1f dBFS) -> %s"
              % (result["values"]["null_depth_dbfs"], self.FLOOR,
                 result["values"]["reference_dbfs"],
                 "green" if result["passed"] else "RED"))
        self.assertTrue(result["passed"], result["red"])

    def test_planted_fault_oct2_from_the_dry_tap(self):
        a, b = self.build(from_dry_tap=True)
        result = null(a, b, floor_dbfs=self.FLOOR)
        print("NULL FAULT    depth %.2f dBFS, first offset above the floor "
              "%s" % (result["values"]["null_depth_dbfs"],
                      result["values"]["first_offset_above_floor"]))
        for line in result["red"]:
            print("   RED", line)
        self.assertFalse(result["passed"])
        self.assertIn("null_depth_dbfs", result["values"]["failed_readouts"])

    def test_two_silences_are_refused_not_passed(self):
        silence = make_render(np.zeros(8192))
        with self.assertRaises(MeasurementRefused) as caught:
            null(silence, silence, floor_dbfs=self.FLOOR)
        print("   two silences refused: %s" % caught.exception)


# --------------------------------------------------------------------------
# 19 COST
# --------------------------------------------------------------------------

class Cost(unittest.TestCase):
    """Two planted faults, both of them the same bug wearing different
    clothes: a class that is not working ranks fastest."""

    def working_render(self):
        t = np.arange(24000) / float(RATE)
        return make_render(0.4 * np.sin(2 * math.pi * 440 * t)
                           * (1 + 0.3 * np.sin(2 * math.pi * 3 * t)))

    def test_control_a_working_class_is_ranked(self):
        row = cost("Compressor", self.working_render(), audio_seconds=0.5,
                   wall_seconds=0.25, blocks=94, board="ESP32-P4",
                   settings={"threshold_db": -20, "ratio": 4},
                   gain_reduction_db=8.2, rt_bar=1.5)
        print("\nCOST control  %s on %s: rt %.2f, %.3f ms/block, %.1f dB GR"
              % (row["values"]["subject"], row["values"]["board"],
                 row["values"]["rt_factor"], row["values"]["ms_per_block"],
                 row["values"]["gain_reduction_db"]))
        self.assertTrue(row["passed"], row["red"])
        self.assertEqual(row["values"]["rt_factor"], 2.0)

    def test_planted_fault_a_muted_class_is_refused_not_ranked(self):
        muted = make_render(np.zeros(24000))
        with self.assertRaises(SilentRenderError) as caught:
            cost("Compressor", muted, audio_seconds=0.5, wall_seconds=0.02,
                 blocks=94, board="ESP32-P4", gain_reduction_db=8.2)
        print("COST FAULT (muted class) refused: %s" % caught.exception)
        print("   it would have ranked first: rt 25.0 against the working "
              "class's 2.0")

    def test_planted_fault_an_idling_class_is_refused(self):
        with self.assertRaises(MeasurementRefused) as caught:
            cost("Compressor", self.working_render(), audio_seconds=0.5,
                 wall_seconds=0.05, blocks=94, board="ESP32-P4",
                 settings={"threshold_db": 0.0}, gain_reduction_db=0.2)
        print("COST FAULT (idling below threshold) refused: %s"
              % caught.exception)


# --------------------------------------------------------------------------
# 20 ROUNDTRIP
# --------------------------------------------------------------------------

class RoundTrip(unittest.TestCase):
    """Three guards. The first catches the loopback wire being out; it does
    NOT catch the playback buffer being analysed instead of the capture,
    which is why the other two exist."""

    BLOCK = 256
    LATENCY = 480  # 10 ms at 48 kHz

    def emitted(self, frames=48000):
        out = np.zeros(frames)
        out[1000] = 0.9
        return make_render(out)

    def captured(self, emitted, lag, gain=0.8, noise_db=-60.0, seed=7):
        source = emitted.float[:, 0]
        out = np.zeros(len(source))
        out[lag:] = gain * source[:len(source) - lag]
        state, noise = seed, []
        for _ in range(len(out)):
            state = (1103515245 * state + 12345) & 0x7fffffff
            noise.append((state / 0x3fffffff) - 1.0)
        return make_render(out + 10.0 ** (noise_db / 20.0) * np.array(noise))

    def test_control_a_real_capture(self):
        emitted = self.emitted()
        result = roundtrip(emitted, self.captured(emitted, self.LATENCY),
                           block_frames=self.BLOCK, starvation_count=0,
                           settings={"chunk_ms": 40, "queue_ms": 100})
        print("\nROUNDTRIP control  lag %d samples = %.3f ms, correlation "
              "%.3f, starvation %d"
              % (result["values"]["lag_samples"],
                 result["values"]["round_trip_ms"],
                 result["values"]["correlation_peak"],
                 result["values"]["starvation_count"]))
        self.assertTrue(result["passed"], result["red"])
        self.assertEqual(result["values"]["lag_samples"], self.LATENCY)

    def test_planted_fault_loopback_wire_out(self):
        emitted = self.emitted()
        state, noise = 4242, []
        for _ in range(emitted.frames):
            state = (1103515245 * state + 12345) & 0x7fffffff
            noise.append((state / 0x3fffffff) - 1.0)
        with self.assertRaises(MeasurementRefused) as caught:
            roundtrip(emitted, make_render(0.05 * np.array(noise)),
                      block_frames=self.BLOCK)
        print("ROUNDTRIP FAULT (wire out) refused: %s" % caught.exception)

    def test_planted_fault_the_playback_buffer_analysed(self):
        """The fault guard one walks straight past."""
        emitted = self.emitted()
        same = Render(emitted.pcm, emitted.rate, emitted.channels)
        with self.assertRaises(MeasurementRefused) as caught:
            roundtrip(emitted, same, block_frames=self.BLOCK)
        print("ROUNDTRIP FAULT (playback buffer, byte-identical) refused: %s"
              % caught.exception)

        nearly = make_render(emitted.float[:, 0] * 0.9)
        self.assertNotEqual(nearly.digest, emitted.digest)
        with self.assertRaises(MeasurementRefused) as caught:
            roundtrip(emitted, nearly, block_frames=self.BLOCK)
        print("ROUNDTRIP FAULT (playback buffer, scaled so the digests "
              "differ) refused: %s" % caught.exception)


# --------------------------------------------------------------------------
# 4 CLICK -- the latency read, at 48 kHz AND 44.1 kHz
# --------------------------------------------------------------------------

class Latency(unittest.TestCase):
    """Part B's `click()`, run at both rates with the spec's planted fault:
    report `latency_samples` 256 short and leave the DSP alone.

    The point of the fault is what it does NOT change. The audio is
    byte-identical, so DIGEST is green, WIRE is green, every spectral
    measurement is green - nothing in the kit fires but this."""

    LATENCY = 512
    SHORT_BY = 256

    def pair(self, rate):
        frames = int(0.25 * rate)
        dry, wet = np.zeros(frames), np.zeros(frames)
        dry[1000] = 0.9
        wet[1000 + self.LATENCY] = 0.9
        return (make_render(wet, rate=rate, label="wet"),
                make_render(dry, rate=rate, label="dry"))

    def test_control_and_planted_fault_at_both_rates(self):
        print("\nCLICK  reported latency against measured")
        for rate in (48000, 44100):
            wet, dry = self.pair(rate)
            control = click(wet, dry, self.LATENCY)
            faulted = click(wet, dry, self.LATENCY - self.SHORT_BY)
            print("   %d Hz: measured %s samples (%.3f ms); reported %d -> "
                  "%s; reported %d -> %s"
                  % (rate, control["values"]["measured_latency_samples"],
                     control["values"]["measured_latency_ms"][0],
                     self.LATENCY, "green" if control["passed"] else "RED",
                     self.LATENCY - self.SHORT_BY,
                     "green" if faulted["passed"] else "RED"))
            self.assertTrue(control["passed"], control["red"])
            self.assertFalse(faulted["passed"])
            self.assertAlmostEqual(faulted["values"]["error_samples"],
                                   self.SHORT_BY, places=3)
        print("   " + faulted["red"][0])

    def test_the_audio_is_untouched_so_nothing_else_can_fire(self):
        wet, _ = self.pair(48000)
        other_build = Render(wet.pcm, wet.rate, wet.channels)
        comparison = digest({"reports_correctly": wet,
                             "reports_256_short": other_build})
        print("   the two builds' renders: FNV %08x against %08x -> DIGEST "
              "%s" % (wet.digest, other_build.digest,
                      "green" if comparison["passed"] else "RED"))
        self.assertTrue(comparison["passed"], comparison["red"])


# --------------------------------------------------------------------------
# 6 DIGEST -- the cross-interpreter BYTE comparison
# --------------------------------------------------------------------------

DUAL_RUNTIME_RENDER = '''
"""Stdlib-only, runs under CPython and MicroPython alike (spec section 1:
the render is dual-runtime, the analysis is not). Prints the PCM as hex."""
import binascii
from array import array

import audiocore
import audiodelays

values = array("h")
for frame in range(4096):
    for channel in range(2):
        values.append(((frame * (97 + channel * 18)) % 30001) - 15000)
source = audiocore.RawSample(values, sample_rate=48000, channel_count=2)
node = audiodelays.Echo(max_delay_ms=200, delay_ms=30, decay=0.6, mix=0.5,
                        buffer_size=2048, sample_rate=48000,
                        bits_per_sample=16, samples_signed=True,
                        channel_count=2, freq_shift=False)
node.play(source)
pcm = bytearray()
for _ in range(8):
    result, view = audiocore.get_buffer(node)
    chunk = bytes(view)
    if not chunk:
        break
    pcm += chunk
print(binascii.hexlify(bytes(pcm)).decode())
'''


class Digest(unittest.TestCase):
    """Part B's `digest()`, with the fault the statistic it replaced was
    blind to - and a real cross-interpreter run behind it."""

    def probe(self):
        t = np.arange(4096) / float(RATE)
        return make_render(0.4 * np.sin(2 * math.pi * 300.0 * t))

    def test_control_two_identical_renders_agree(self):
        one = self.probe()
        other = Render(one.pcm, one.rate, one.channels)
        result = digest({"cpython": one, "micropython": other})
        print("\nDIGEST control  FNV %08x both ways -> %s"
              % (one.digest, "green" if result["passed"] else "RED"))
        self.assertTrue(result["passed"], result["red"])

    def test_planted_fault_the_pair_the_byte_sum_cannot_see(self):
        """+256 LSB in one sample paid for by -1 LSB in another, in the same
        block. The unsigned-byte sum moves by exactly zero."""
        one = self.probe()
        data = bytearray(one.pcm)
        high = next(i for i in range(1, 2048, 2) if data[i] < 255)
        low = next(i for i in range(0, 2048, 2) if data[i] >= 1 and i != high)
        data[high] += 1   # +256 LSB on that sample
        data[low] -= 1    # -1 LSB on another, same block
        other = Render(bytes(data), one.rate, one.channels)

        print("DIGEST FAULT    byte sum %d against %d (moves by %d); FNV "
              "%08x against %08x"
              % (one.byte_sum, other.byte_sum,
                 other.byte_sum - one.byte_sum, one.digest, other.digest))
        self.assertEqual(one.byte_sum, other.byte_sum,
                         "the whole point of the fault is that the sum does "
                         "not move")
        self.assertNotEqual(one.digest, other.digest)
        result = digest({"clean": one, "perturbed": other})
        for line in result["red"]:
            print("   RED", line)
        self.assertFalse(result["passed"])

    @unittest.skipUnless(os.path.exists(MICROPYTHON),
                         "cmods/bin/micropython not present")
    def test_cpython_against_desktop_micropython(self):
        """The measurement's own subject: the same node, rendered by two
        interpreters, compared by hashing the bytes."""
        with tempfile.TemporaryDirectory() as directory:
            script = os.path.join(directory, "dual_runtime_render.py")
            with open(script, "w") as handle:
                handle.write(DUAL_RUNTIME_RENDER)
            renders = {}
            for name, binary in (("cpython", sys.executable),
                                 ("micropython", MICROPYTHON)):
                done = subprocess.run([binary, script], capture_output=True,
                                      text=True, cwd=ROOT)
                self.assertEqual(done.returncode, 0, done.stderr)
                pcm = bytes.fromhex(done.stdout.strip())
                renders[name] = Render(pcm, 48000, 2, block=512,
                                       interpreter=name,
                                       class_name="audiodelays.Echo")
        result = digest(renders)
        for name, leg in result["values"]["renders"].items():
            print("   %-12s %5d frames  FNV %s  sum %d"
                  % (name, leg["frames"], leg["fnv1a"], leg["byte_sum"]))
        print("   cross-interpreter -> %s"
              % ("green" if result["passed"] else "RED"))
        for line in result["red"]:
            print("   RED", line)
        self.assertTrue(result["passed"], result["red"])
