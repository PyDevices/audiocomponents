"""`RingMod`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/RingMod.md`.
Exhaustive rates live in the evidence pack, not in this file.
"""

import math
import os
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                            # noqa: E402
import kit_faults                                           # noqa: E402
from audioeffects import ringmod as rebuilt                 # noqa: E402
from audioeffects.ringmod import BAL, FREQ, PBAL              # noqa: E402
import kit_probes as probes                                 # noqa: E402

VENDOR = "PyDevices"

RATE = 48000


class ChopperOnMultiplier(rebuilt.RingMod):
    NAME = "RingMod"
    FORCE_CHOPPER = True


class SineOnSwitching(rebuilt.RingMod):
    NAME = "RingMod"
    FORCE_SINE = True


class FlatCarrier(rebuilt.RingMod):
    NAME = "RingMod"
    BYPASS_CARRIER_LOW = True


class HardChopper(rebuilt.RingMod):
    NAME = "RingMod"
    HARD_CHOPPER = True


class MakeupOnChopper(rebuilt.RingMod):
    NAME = "RingMod"
    FORCE_MAKEUP = True


class ZeroMod(rebuilt.RingMod):
    NAME = "RingMod"
    ZERO_MOD = True


def sine_src(hz, frames, channels=2, rate=RATE, peak=16384):
    data = array("h")
    for frame in range(frames):
        value = int(peak * math.sin(2.0 * math.pi * hz * frame / rate))
        for _ in range(channels):
            data.append(value)
    return probes.ArraySource(data, rate=rate, channels=channels, block=256)


def pull(effect, frames):
    channels = effect.channel_count
    out = array("h")
    while len(out) < frames * channels:
        data = memoryview(bytes(audiocore.get_buffer(effect.output)[1]))
        if not data:
            break
        out.extend(data.cast("h"))
    return np.array(out[:frames * channels], dtype=np.int16).reshape(
        -1, channels)


def db_at(y, hz, rate=RATE):
    spec = np.abs(np.fft.rfft(y.astype(np.float64)))
    index = int(round(hz * len(y) / rate))
    peak = spec.max()
    return 20.0 * math.log10(spec[index] / (peak + 1e-18) + 1e-18)


def sideband_pair(cls, program_hz, carrier_hz, frames=48000, **opts):
    src = sine_src(program_hz, frames, peak=16384)
    effect = cls(src, sample_rate=RATE, frequency=carrier_hz, depth=1.0,
                 mix=1.0, **opts)
    y = pull(effect, frames)[:, 0]
    return y


class RingModInvariants(unittest.TestCase):

    def test_mix_zero_is_a_wire(self):
        frames = 4096
        src = sine_src(1000, frames, peak=12000)
        effect = rebuilt.RingMod(src, sample_rate=RATE, mix=0.0)
        y = pull(effect, frames)[:, 0]
        ideal = np.array([
            int(12000 * math.sin(2.0 * math.pi * 1000 * i / RATE))
            for i in range(frames)])
        self.assertEqual(int(np.max(np.abs(y - ideal))), 0)

    def test_depth_zero_is_a_wire(self):
        frames = 4096
        src = sine_src(1000, frames, peak=12000)
        effect = rebuilt.RingMod(src, sample_rate=RATE, depth=0.0)
        y = pull(effect, frames)[:, 0]
        ideal = np.array([
            int(12000 * math.sin(2.0 * math.pi * 1000 * i / RATE))
            for i in range(frames)])
        self.assertEqual(int(np.max(np.abs(y - ideal))), 0)

    def test_latency_and_tail_are_zero(self):
        src = sine_src(440, 256)
        effect = rebuilt.RingMod(src, sample_rate=RATE)
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.tail_samples, 0)
        self.assertEqual(effect.capabilities, ())

    def test_click_delay_is_zero(self):
        frames = 2048
        data = array("h", [0] * (frames * 2))
        data[0] = 20000
        data[1] = 20000
        src = probes.ArraySource(data, rate=RATE, channels=2, block=256)
        effect = rebuilt.RingMod(src, sample_rate=RATE, mix=0.0)
        y = pull(effect, frames)[:, 0]
        self.assertEqual(int(np.argmax(np.abs(y))), 0)
        self.assertEqual(int(y[0]), 20000)

    def test_frequency_clamps_below_nyquist_fraction(self):
        src = sine_src(440, 256, rate=22050)
        effect = rebuilt.RingMod(src, sample_rate=22050, frequency=8000.0)
        self.assertLessEqual(effect._value(FREQ), 22050 * 0.45 + 1e-6)

    def test_mono_constructs(self):
        src = sine_src(440, 512, channels=1)
        effect = rebuilt.RingMod(src, sample_rate=RATE)
        y = pull(effect, 512)
        self.assertEqual(y.shape[1], 1)
        self.assertTrue(int(np.max(np.abs(y))) > 0)

    def test_silence_in_silence_out(self):
        frames = 2048
        src = probes.ArraySource(
            array("h", [0] * (frames * 2)), rate=RATE, channels=2, block=256)
        effect = rebuilt.RingMod(src, sample_rate=RATE)
        y = pull(effect, frames)
        self.assertEqual(int(np.max(np.abs(y))), 0)


class RingModTraits(unittest.TestCase):

    def test_m1_multiplier_sidebands(self):
        y = sideband_pair(rebuilt.RingMod, 500, 1500)
        self.assertLess(abs(db_at(y, 1000) - db_at(y, 2000)), 0.5)
        for hz in (500, 1500, 4000, 5000, 7000, 8000):
            self.assertLessEqual(db_at(y, hz), -60.0)

    def test_m1_fault_hard_chopper_at_defaults(self):
        src = sine_src(500, 48000, peak=16384)
        effect = HardChopper(src, sample_rate=RATE)
        y = pull(effect, 48000)[:, 0]
        # Constructor Frequency is 220 Hz; 3·f₂+f₁ = 1160 Hz is a switching
        # product the multiplier must not emit. FORCE_CHOPPER is Shape 1 on
        # Character, which the grid can dial; HARD_CHOPPER is not.
        self.assertGreater(db_at(y, 1160), -40.0)

    def test_m1_holds_at_program_change_0(self):
        """Patch 0 used to snap Balance to 64/127 = 0.007874 and lift
        residuals to −36 dB. MIDI 64 is now the bipolar null."""
        src = sine_src(500, 32768, peak=16384)
        patched = rebuilt.RingMod(src, sample_rate=RATE)
        patched.program_change(0)
        self.assertLess(abs(patched._value(BAL)), 1e-9)
        self.assertLess(abs(patched._value(PBAL)), 1e-9)
        # M1's material is 500×1500; patch 0 Frequency is ~228 Hz, not
        # that row. Balance midi 64 must stay a null on the frozen pair.
        src = sine_src(500, 32768, peak=16384)
        effect = rebuilt.RingMod(src, sample_rate=RATE, frequency=1500.0)
        effect.set_macro(BAL, 64)
        effect.set_macro(PBAL, 64)
        self.assertLess(abs(effect._value(BAL)), 1e-9)
        y = pull(effect, 32768)[:, 0]
        win = np.hanning(len(y))
        spec = np.abs(np.fft.rfft(y.astype(np.float64) * win))
        peak = spec.max()

        def bin_db(hz):
            index = int(round(hz * len(y) / RATE))
            return 20.0 * math.log10(spec[index] / (peak + 1e-18) + 1e-18)

        self.assertLess(abs(bin_db(1000) - bin_db(2000)), 0.5)
        for hz in (500, 1500, 4000, 5000, 7000, 8000):
            self.assertLessEqual(bin_db(hz), -60.0)

    def test_m2_is_the_q15_product_at_half_scale(self):
        """M2 stays disconfirmed. The Q15 product is −3.01 dB; synthio's
        voice sum (A1/P12) takes another 6 dB."""
        y = sideband_pair(rebuilt.RingMod, 500, 1500)
        program = 16384.0 / math.sqrt(2.0)
        rms = float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))
        err = 20.0 * math.log10(rms / program)
        self.assertLess(abs(err + 9.03), 0.2)

    def test_m4_carrier_low(self):
        def energy(carrier):
            y = sideband_pair(rebuilt.RingMod, 500, carrier)
            spec = np.abs(np.fft.rfft(y.astype(np.float64)))
            total = 0.0
            for hz in (abs(carrier - 500), carrier + 500):
                total += spec[int(round(hz * len(y) / RATE))]
            return total
        ratio_db = 20.0 * math.log10(energy(2) / energy(200))
        self.assertLess(abs(ratio_db + 8.6), 1.5)

    def test_m4_same_kind_plant_inert_at_constructor_frequency(self):
        """M4 DISCONFIRMED as a G3 row: Carrier-Low bypass cannot fire
        at Frequency=220. carrier_gain(220, 5) is 0.99974; the plant
        reads 0.0022 dB at 48000 / 44100 / 22050."""
        def energy(cls, carrier, rate):
            src = sine_src(500, rate, rate=rate, peak=16384)
            effect = cls(src, sample_rate=rate, frequency=carrier,
                         depth=1.0, mix=1.0)
            y = pull(effect, rate)[:, 0]
            spec = np.abs(np.fft.rfft(y.astype(np.float64)))
            total = 0.0
            for hz in (abs(carrier - 500), carrier + 500):
                total += spec[int(round(hz * len(y) / rate))]
            return total

        self.assertAlmostEqual(rebuilt.carrier_gain(220.0, 5.0), 0.99974, 5)
        for rate in (48000, 44100, 22050):
            clean = energy(rebuilt.RingMod, 220.0, rate)
            flat = energy(FlatCarrier, 220.0, rate)
            delta_db = 20.0 * math.log10((flat + 1e-18) / (clean + 1e-18))
            self.assertLess(abs(delta_db - 0.0022), 0.001)

    def test_m4_fault_flat_carrier(self):
        def energy(cls, carrier):
            y = sideband_pair(cls, 500, carrier)
            spec = np.abs(np.fft.rfft(y.astype(np.float64)))
            total = 0.0
            for hz in (abs(carrier - 500), carrier + 500):
                total += spec[int(round(hz * len(y) / RATE))]
            return total
        ratio_db = 20.0 * math.log10(
            energy(FlatCarrier, 2) / energy(FlatCarrier, 200))
        self.assertLess(abs(ratio_db), 1.0)

    def test_w1_switching_odd_orders_are_not_a_demonstrated_row(self):
        """Character 1 Shape 1 still makes the Bode chopper products.
        That is not a G3 demonstrated row: the plant is inert at create()."""
        src = sine_src(500, 48000, peak=16384)
        effect = rebuilt.RingMod(
            src, sample_rate=RATE, frequency=1500, depth=1.0, mix=1.0,
            shape=1.0, character=1.0)
        y = pull(effect, 48000)[:, 0]
        self.assertLess(abs(db_at(y, 4000) + 9.5), 3.0)
        self.assertLess(abs(db_at(y, 5000) + 9.5), 3.0)
        self.assertLess(abs(db_at(y, 7000) + 14.0), 3.0)
        self.assertLess(abs(db_at(y, 8000) + 14.0), 3.0)
        self.assertLess(db_at(y, 2500), -40.0)
        self.assertLess(db_at(y, 3500), -40.0)

    def test_w1_fails_at_constructor_default(self):
        """W1 is disconfirmed at Character 0: 3·f₂+f₁ is the Q15 floor."""
        src = sine_src(500, 48000, peak=16384)
        effect = rebuilt.RingMod(src, sample_rate=RATE)
        y = pull(effect, 48000)[:, 0]
        # Constructor Frequency 220 Hz; 3·220+500 = 1160.
        odd3 = db_at(y, 1160)
        self.assertLess(odd3, -60.0)
        self.assertGreater(abs(odd3 + 9.5), 3.0)

    def test_carrier_waveform_is_one_short_period(self):
        src = sine_src(440, 256)
        effect = rebuilt.RingMod(src, sample_rate=RATE, frequency=0.1)
        self.assertEqual(effect._carrier_frames, rebuilt.TABLE_FRAMES)
        effect.set_macro(FREQ, 0)
        self.assertEqual(effect._carrier_frames, rebuilt.TABLE_FRAMES)
        defaulted = rebuilt.RingMod(src, sample_rate=RATE)
        self.assertEqual(defaulted._carrier_frames, rebuilt.TABLE_FRAMES)
        self.assertIsNotNone(defaulted._synth)

    def test_w4_q15_cannot_hold_unity_rms(self):
        """W4 is disconfirmed: peak-normalizing the Gibbs square to fit
        Q15 drops RMS outside 0.5 dB. Restoring it clips and fails W2."""
        src = sine_src(500, 48000, peak=16384)
        effect = rebuilt.RingMod(
            src, sample_rate=RATE, frequency=1500, depth=1.0, mix=1.0,
            shape=1.0, character=1.0)
        y = pull(effect, 48000)[:, 0]
        program = 16384.0 / math.sqrt(2.0)
        rms = float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))
        err = 20.0 * math.log10(rms / program)
        self.assertGreater(abs(err), 0.5)
        self.assertLess(abs(err), 9.0)

    def test_m3_translated_band(self):
        frames = RATE
        tones = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
        data = array("h")
        for frame in range(frames):
            acc = 0.0
            for hz in tones:
                acc += math.sin(2.0 * math.pi * hz * frame / RATE)
            value = int(8000.0 * acc / len(tones))
            data.extend((value, value))
        src = probes.ArraySource(data, rate=RATE, channels=2, block=256)
        effect = rebuilt.RingMod(
            src, sample_rate=RATE, frequency=900.0, depth=1.0, mix=1.0)
        y = pull(effect, frames)[:, 0].astype(np.float64)
        win = np.hanning(len(y))
        spec = np.abs(np.fft.rfft(y * win))
        freqs = np.fft.rfftfreq(len(y), 1.0 / RATE)
        peak = spec.max()
        outside = (freqs < 780) | (freqs > 1020)
        out_db = 20.0 * math.log10(spec[outside].max() / (peak + 1e-18) + 1e-18)
        self.assertLess(out_db, -40.0)

    def test_w2_sieve_holds_when_frequency_is_the_note(self):
        """The looping table detuned the odd·odd set. `Note.frequency`
        does not. This is the row's bar, not a G3 demonstration: the
        default is Character 0, and W1 stays disconfirmed there."""
        src = sine_src(523, 48000, peak=16000)
        effect = rebuilt.RingMod(
            src, sample_rate=RATE, frequency=1481, depth=1.0, mix=1.0,
            shape=1.0, character=1.0)
        y = pull(effect, 48000)[:, 0].astype(np.float64)
        spec = np.abs(np.fft.rfft(y))
        mag_db = 20.0 * np.log10(
            spec / (len(y) * 32768.0 / 2.0) + 1e-18)
        f1, f2, fs = 523.0, 1481.0, float(RATE)
        allowed = set()
        m = 1
        while m * f2 < fs / 2:
            k = 1
            while k * f1 + m * f2 < fs:
                for sign_k in (-1, 1):
                    for sign_m in (-1, 1):
                        allowed.add(abs(sign_k * k * f1 + sign_m * m * f2))
                k += 2
            m += 2
        off = 0
        for index, value in enumerate(mag_db):
            if value <= -60.0:
                continue
            hz = index * fs / len(y)
            if min(abs(hz - a) for a in allowed) > 2.0:
                off += 1
        self.assertEqual(off, 0)

    def test_w2_fault_hard_chopper(self):
        src = sine_src(523, 48000, peak=16000)
        effect = HardChopper(
            src, sample_rate=RATE, frequency=1481, depth=1.0, mix=1.0,
            shape=1.0, character=1.0)
        y = pull(effect, 48000)[:, 0].astype(np.float64)
        spec = np.abs(np.fft.rfft(y))
        mag_db = 20.0 * np.log10(
            spec / (len(y) * 32768.0 / 2.0) + 1e-18)
        f1, f2, fs = 523.0, 1481.0, float(RATE)
        allowed = set()
        m = 1
        while m * f2 < fs / 2:
            k = 1
            while k * f1 + m * f2 < fs:
                for sign_k in (-1, 1):
                    for sign_m in (-1, 1):
                        allowed.add(abs(sign_k * k * f1 + sign_m * m * f2))
                k += 2
            m += 2
        off = 0
        for index, value in enumerate(mag_db):
            if value <= -60.0:
                continue
            hz = index * fs / len(y)
            if min(abs(hz - a) for a in allowed) > 2.0:
                off += 1
        self.assertGreater(off, 50)


class RingModFaultsUnreachable(unittest.TestCase):

    def _reach(self, faulted, reading):
        return kit_faults.fault_reachability(
            rebuilt.RingMod, faulted, reading,
            lambda cls: cls(sine_src(440, 256, peak=8000), sample_rate=RATE))

    def test_faults_not_on_the_macro_grid(self):
        cases = (
            (ChopperOnMultiplier,
             lambda e: getattr(e, "_plant_chopper", False), True),
            (SineOnSwitching,
             lambda e: getattr(e, "_plant_sine", False), True),
            (FlatCarrier,
             lambda e: getattr(e, "_plant_flat_carrier", False), True),
            (HardChopper,
             lambda e: getattr(e, "_plant_hard_chopper", False), True),
            (MakeupOnChopper,
             lambda e: getattr(e, "_plant_makeup", False), True),
            (ZeroMod,
             lambda e: getattr(e, "_plant_zero_mod", False), True),
        )
        for faulted, reading, expected in cases:
            result = self._reach(faulted, reading)
            self.assertEqual(result["target"], expected)
            self.assertEqual(result["checked"], 12 * 17 + 9)


def _m1_frozen(cls):
    """M1 as frozen: 500×1500 Depth 1 Mix 1, 32768 Hann."""
    src = sine_src(500, 32768, peak=16384)
    effect = cls(src, sample_rate=RATE, frequency=1500.0, depth=1.0, mix=1.0)
    y = pull(effect, 32768)[:, 0]
    win = np.hanning(len(y))
    spec = np.abs(np.fft.rfft(y.astype(np.float64) * win))
    peak = spec.max() + 1e-18

    def bin_db(hz):
        index = int(round(hz * len(y) / RATE))
        return 20.0 * math.log10(spec[index] / peak + 1e-18)

    pair_ok = abs(bin_db(1000) - bin_db(2000)) < 0.5
    resid_ok = all(
        bin_db(hz) <= -60.0
        for hz in (500, 1500, 4000, 5000, 7000, 8000))
    return {"passed": pair_ok and resid_ok,
            "detail": (bin_db(1000), bin_db(2000), bin_db(500))}


def _m3_skirts(cls, carrier=900.0):
    frames = 8192
    tones = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
    data = array("h")
    for frame in range(frames):
        acc = 0.0
        for hz in tones:
            acc += math.sin(2.0 * math.pi * hz * frame / RATE)
        value = int(8000.0 * acc / len(tones))
        data.extend((value, value))
    src = probes.ArraySource(data, rate=RATE, channels=2, block=256)
    effect = cls(src, sample_rate=RATE, frequency=carrier, depth=1.0, mix=1.0)
    y = pull(effect, frames)[:, 0].astype(np.float64)
    win = np.hanning(len(y))
    spec = np.abs(np.fft.rfft(y * win))
    freqs = np.fft.rfftfreq(len(y), 1.0 / RATE)
    peak = spec.max() + 1e-18
    lo, hi = carrier - 120.0, carrier + 120.0
    outside = (freqs < lo) | (freqs > hi)
    out_db = 20.0 * math.log10(spec[outside].max() / peak + 1e-18)
    return {"passed": out_db < -40.0, "detail": out_db}


def _m4_ratio(cls):
    def energy(carrier):
        y = sideband_pair(cls, 500, carrier)
        spec = np.abs(np.fft.rfft(y.astype(np.float64)))
        total = 0.0
        for hz in (abs(carrier - 500), carrier + 500):
            total += spec[int(round(hz * len(y) / RATE))]
        return total
    e2, e200 = energy(2), energy(200)
    ratio_db = 20.0 * math.log10(e2 / (e200 + 1e-18) + 1e-18)
    # A wire 500 Hz tone has a sidelobe ratio near −8 dB by accident.
    # The 200 Hz render's peak must sit on a sideband, not the program.
    y200 = sideband_pair(cls, 500, 200)
    spec = np.abs(np.fft.rfft(y200.astype(np.float64)))
    peak_hz = spec.argmax() * RATE / float(len(y200))
    peak_ok = min(abs(peak_hz - 300.0), abs(peak_hz - 700.0)) < 4.0
    return {"passed": abs(ratio_db + 8.6) < 1.5 and peak_ok,
            "detail": (ratio_db, peak_hz)}


class RingModNullBuild(unittest.TestCase):

    def test_m1_null_build_red_at_defaults(self):
        got = kit_faults.null_build_red(
            rebuilt.RingMod, _m1_frozen, label="RingMod M1")
        self.assertFalse(got["null"]["passed"])
        self.assertTrue(got["control"]["passed"])

    def test_m3_null_build_red(self):
        got = kit_faults.null_build_red(
            rebuilt.RingMod, _m3_skirts, label="RingMod M3")
        self.assertFalse(got["null"]["passed"])
        self.assertTrue(got["control"]["passed"])

    def test_m4_null_build_red(self):
        got = kit_faults.null_build_red(
            rebuilt.RingMod, _m4_ratio, label="RingMod M4")
        self.assertFalse(got["null"]["passed"])
        self.assertTrue(got["control"]["passed"])


if __name__ == "__main__":
    unittest.main()
