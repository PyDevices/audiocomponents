"""`Phaser`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Phaser.md`; its
Tier 2 rows are P1..P10. Exhaustive rate coverage lives in the evidence
pack. This file stays at 48 kHz except where a test is about rate
handling.

The old `modulation.Phaser` had `MACRO_LABELS = ()` and no surface test
to retire.
"""

import array
import math
import os
import sys
import unittest

import audiocore
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))

from audioeffects import _component                            # noqa: E402
from audioeffects import phaser as phaser_module               # noqa: E402
from tools import effect_measurements as kit                   # noqa: E402
import kit_faults as faults                                    # noqa: E402

VENDOR = "PyDevices"

Phaser = phaser_module.Phaser
RATE = 48000

RATE_I, DEPTH_I, CENTRE_I, FEEDBACK_I, MIX_I, STAGES_I, SHAPE_I, DRIVE_I, \
    SYNC_I, DIV_I = range(10)


def silence(frames=4096, channels=2, rate=RATE):
    return audiocore.RawSample(array.array("h", bytes(2 * channels * frames)),
                               sample_rate=rate, channel_count=channels)


def ramp(frames=4096, channels=2, rate=RATE):
    values = array.array("h")
    denom = max(1, frames - 1)
    for index in range(frames):
        value = max(-32768, min(32767,
                                int(round(-32768 + 65535.0 * index / denom))))
        for _ in range(channels):
            values.append(value)
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def burst_then_silence(hz, on_frames, frames, rate=RATE, channels=2,
                       peak=20000):
    values = array.array("h", bytes(2 * channels * frames))
    for index in range(on_frames):
        value = int(round(peak * math.sin(2.0 * math.pi * hz * index / rate)))
        for channel in range(channels):
            values[index * channels + channel] = value
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def pcm(node, frames, channels=2):
    want = frames * channels * 2
    out = bytearray()
    while len(out) < want:
        chunk = bytes(audiocore.get_buffer(node)[1])
        if not chunk:
            break
        out += chunk
    return bytes(out[:want])


def built(source=None, rate=RATE, cls=None, **options):
    return (cls or Phaser).create(source or silence(rate=rate), rate,
                                  **options)


class MixOneCascade(Phaser):
    """P4's fault of the same kind: Mix forced to 1 (bare cascade, no
    null) while the Mix knob still reads the default 0.5."""

    NAME = 'Phaser'

    def _refresh_mix_feedback(self):
        self._cascade.feedback = self._value(3)
        self._cascade.mix = 1.0


class SixStagesAlways(Phaser):
    """P1's fault: six stages at the default Stages 4."""

    NAME = 'Phaser'

    def _install_cascade(self, stages):
        Phaser._install_cascade(self, 6)


class NoDriveLaw(Phaser):
    """P7's fault: Drive is ignored; the shaper stays a wire.

    `_refresh_drive` is the one to defeat: Mix and Feedback both call it,
    so intercepting only macro 7 lets those knobs put the cubic back.
    """

    NAME = 'Phaser'
    _drive_forced = 0.0

    def _refresh_drive(self):
        self._shaper.set(mix=0.0, pre_gain=1.0)
        self._drive_forced = 0.0


class FeedbackStuck(Phaser):
    """P5/P8's fault: Feedback knob moves, the node stays at 0."""

    NAME = 'Phaser'

    def _refresh_mix_feedback(self):
        self._cascade.feedback = 0.0
        self._cascade.mix = self._value(4)
        self._refresh_drive()


class ShortLatency(Phaser):
    NAME = 'Phaser'
    LATENCY_SAMPLES = 256
    NAME = 'Phaser'
    LATENCY_SAMPLES = 256


class TestPhaserInvariants(unittest.TestCase):

    def test_mix_zero_is_a_wire(self):
        wet_src, dry_src = ramp(), ramp()
        effect = built(wet_src)
        effect.set_macro(MIX_I, 0)
        wet = kit.Render.from_pcm(pcm(effect.output, 4096), RATE, 2)
        dry = kit.Render.from_pcm(pcm(dry_src, 4096), RATE, 2)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertFalse(result["red"], result)

        wet_src, dry_src = ramp(), ramp()
        effect = MixOneCascade.create(wet_src, RATE)
        wet = kit.Render.from_pcm(pcm(effect.output, 4096), RATE, 2)
        dry = kit.Render.from_pcm(pcm(dry_src, 4096), RATE, 2)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["red"], "default Mix 0.5 with mix=1 is not a wire")

    def test_silence_tail_reaches_zero(self):
        source = burst_then_silence(1000, 4800, 24000)
        effect = built(source)
        data = pcm(effect.output, 24000)
        tail = memoryview(data).cast("h")[-8000:]
        self.assertEqual(max(abs(int(v)) for v in tail), 0)

    def test_latency_is_zero_and_click_agrees(self):
        values = array.array("h", bytes(2 * 2 * 8192))
        values[200] = 32000
        values[201] = 32000
        src_a = audiocore.RawSample(array.array("h", values), sample_rate=RATE,
                                    channel_count=2)
        src_b = audiocore.RawSample(array.array("h", values), sample_rate=RATE,
                                    channel_count=2)
        effect = built(src_a)
        self.assertEqual(effect.latency_samples, 0)
        wet = kit.Render.from_pcm(pcm(effect.output, 8192), RATE, 2)
        dry = kit.Render.from_pcm(pcm(src_b, 8192), RATE, 2)
        result = kit.click(wet, dry, 0)
        self.assertFalse(result["red"], result)
        src_a = audiocore.RawSample(array.array("h", values), sample_rate=RATE,
                                    channel_count=2)
        src_b = audiocore.RawSample(array.array("h", values), sample_rate=RATE,
                                    channel_count=2)
        lied = ShortLatency.create(src_a, RATE)
        wet = kit.Render.from_pcm(pcm(lied.output, 8192), RATE, 2)
        dry = kit.Render.from_pcm(pcm(src_b, 8192), RATE, 2)
        result = kit.click(wet, dry, lied.latency_samples)
        self.assertTrue(result["red"])

    def test_capabilities_declare_tempo_sync_and_read_transport(self):
        seen = []

        def transport():
            seen.append(1)
            return (True, 0.0, 120.0, 4, 4)

        effect = Phaser.create(silence(), RATE, transport=transport)
        self.assertEqual(effect.capabilities, ("tempo_sync",))
        effect.set_macro(SYNC_I, 127)
        self.assertTrue(seen)

    def test_patch_zero_round_trips(self):
        effect = built()
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(FEEDBACK_I, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(0)
        self.assertEqual(effect.patch_index, 0)
        self.assertLess(effect.macro(FEEDBACK_I), 0.05)

    def test_adopted_phaser_is_the_rebuild(self):
        from audioeffects import Phaser as Served
        self.assertIs(Served, Phaser)
        self.assertEqual(Served.__module__, "audioeffects.phaser")
        self.assertTrue(issubclass(Phaser, _component.Component))

    def test_rate_honest_construction(self):
        for rate in (44100, 22050):
            effect = built(silence(rate=rate), rate=rate)
            effect.set_macro(CENTRE_I, 127)
            self.assertLessEqual(effect._held_hz,
                                 rate * 0.5 * _component.NYQUIST_MARGIN)
            _low, high = effect._fb_span()
            self.assertLessEqual(high, rate * 0.5 * _component.NYQUIST_MARGIN)

    def test_reset_then_silence_and_deinit_leaves_source(self):
        src = ramp(512)
        effect = built(src)
        primed = pcm(effect.output, 128)
        primed_peak = max(abs(int(v)) for v in memoryview(primed).cast("h"))
        self.assertGreater(primed_peak, 0)
        effect.reset()
        quiet = silence(512)
        effect._source = quiet
        effect._shaper.play(quiet)
        after = pcm(effect.output, 256)
        self.assertEqual(max(abs(int(v)) for v in memoryview(after).cast("h")),
                         0)
        self.assertEqual(len(effect._nodes), 2)
        leftover = ramp(256)
        effect.deinit()
        still = pcm(leftover, 256)
        self.assertGreater(max(abs(int(v)) for v in memoryview(still).cast("h")),
                           0)


class TestPhaserTraits(unittest.TestCase):

    def _held_noise(self, cls=Phaser, seed=1, frames=65536):
        rng = np.random.RandomState(seed)
        noise = rng.randint(-8000, 8001, size=frames * 2, dtype=np.int16)
        buf = array.array("h", noise.tobytes())
        source = audiocore.RawSample(buf, sample_rate=RATE, channel_count=2)
        dry_src = audiocore.RawSample(array.array("h", buf), sample_rate=RATE,
                                      channel_count=2)
        effect = cls.create(source, RATE)
        effect.set_macro(RATE_I, 0)
        effect.set_macro(DEPTH_I, 0)
        effect.set_macro(DRIVE_I, 0)
        data = pcm(effect.output, frames)
        dry = pcm(dry_src, frames)
        return source, effect, data, dry

    def test_p1_two_notches_at_defaults_six_stages_is_three(self):
        _source, _effect, data, dry = self._held_noise()
        notches = _notches_h(data, dry)
        self.assertEqual(len(notches), 2, notches)
        cents = 1200.0 * math.log2(notches[1] / notches[0])
        self.assertLess(abs(cents - 3052.0), 80.0, (notches, cents))
        _s, _e, data6, dry6 = self._held_noise(SixStagesAlways, seed=1)
        notches6 = _notches_h(data6, dry6)
        self.assertGreaterEqual(len(notches6), 3, notches6)

    def test_p4_null_at_defaults_mix_one_is_shallow(self):
        _s, _e, data, dry = self._held_noise(seed=2)
        self.assertLess(_notch_floor_h(data, dry), -40.0)
        _s, _e, broken, dry_b = self._held_noise(MixOneCascade, seed=2)
        self.assertGreater(_notch_floor_h(broken, dry_b), -20.0)

    def test_p7_harmonics_grow_fault_is_flat(self):
        def thd(level, cls):
            frames = 24000
            peak = int(round(32767 * (10.0 ** (level / 20.0))))
            values = array.array("h")
            for index in range(frames):
                sample = int(round(peak * math.sin(
                    2.0 * math.pi * 1000.0 * index / RATE)))
                values.append(sample)
                values.append(sample)
            source = audiocore.RawSample(values, sample_rate=RATE,
                                         channel_count=2)
            effect = cls.create(source, RATE)
            effect.set_macro(RATE_I, 0)
            effect.set_macro(DEPTH_I, 0)
            effect.set_macro(DRIVE_I, _component.macro_of(
                Phaser._MACRO_RANGES[DRIVE_I], 0.5))
            x = np.frombuffer(pcm(effect.output, frames),
                              dtype=np.int16)[0::2].astype(np.float64)
            spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
            n = len(x)
            h1 = spec[int(round(1000.0 * n / RATE))]
            h2 = spec[int(round(2000.0 * n / RATE))]
            h3 = spec[int(round(3000.0 * n / RATE))]
            return 20.0 * math.log10((h2 + h3) / max(h1, 1e-12))

        clean_hi, clean_lo = thd(-6, Phaser), thd(-40, Phaser)
        self.assertGreater(clean_hi - clean_lo, 3.0, (clean_lo, clean_hi))
        # Linear cascade at the same Drive knob: h3 at -6 dBFS stays in the
        # noise, more than 20 dB quieter than the cubic. Level-flatness of
        # a dB THD ratio is not the check — at −40 dBFS the ratio is a
        # noise floor.
        self.assertLess(thd(-6, NoDriveLaw), clean_hi - 20.0)

    def test_p7_harmonics_at_constructor_drive_fault_is_flat(self):
        """P7 at the shipped Drive 0.3, not only at the dossier's Drive 0.5."""

        def thd(level, cls):
            frames = 24000
            peak = int(round(32767 * (10.0 ** (level / 20.0))))
            values = array.array("h")
            for index in range(frames):
                sample = int(round(peak * math.sin(
                    2.0 * math.pi * 1000.0 * index / RATE)))
                values.append(sample)
                values.append(sample)
            source = audiocore.RawSample(values, sample_rate=RATE,
                                         channel_count=2)
            effect = cls.create(source, RATE)
            effect.set_macro(RATE_I, 0)
            effect.set_macro(DEPTH_I, 0)
            x = np.frombuffer(pcm(effect.output, frames),
                              dtype=np.int16)[0::2].astype(np.float64)
            spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
            n = len(x)
            h1 = spec[int(round(1000.0 * n / RATE))]
            h2 = spec[int(round(2000.0 * n / RATE))]
            h3 = spec[int(round(3000.0 * n / RATE))]
            return 20.0 * math.log10((h2 + h3) / max(h1, 1e-12))

        rise = thd(-6, Phaser) - thd(-40, Phaser)
        self.assertGreater(rise, 10.0, rise)
        self.assertLess(thd(-6, NoDriveLaw) - thd(-40, NoDriveLaw), 0.0)

        def measure(cls):
            return {"passed": (thd(-6, cls) - thd(-40, cls)) >= 10.0}

        checked = faults.null_build_red(Phaser, measure, label="P7")
        self.assertFalse(checked["null"]["passed"])
        self.assertTrue(checked["control"]["passed"])

    def test_default_lfo_is_builtin_not_a_table(self):
        effect = built()
        self.assertFalse(effect._lfo_custom)
        wave = getattr(effect._lfo, "waveform", None)
        self.assertTrue(wave is None or (hasattr(wave, "__len__")
                                         and len(wave) <= 4))
        effect.program_change(8)
        self.assertEqual(effect.patch_index, 8)
        self.assertLessEqual(effect._value(DRIVE_I), 0.0)

    def test_p5_misses_at_constructor_drive(self):
        """Headline: P5 at Drive 0.3, the constructor default."""

        def peak(drive, fb):
            rng = np.random.RandomState(3)
            noise = rng.randint(-8000, 8001, size=65536 * 2, dtype=np.int16)
            buf = array.array("h", noise.tobytes())
            source = audiocore.RawSample(buf, sample_rate=RATE,
                                        channel_count=2)
            dry_src = audiocore.RawSample(array.array("h", buf),
                                          sample_rate=RATE,
                                          channel_count=2)
            effect = Phaser.create(source, RATE)
            effect.set_macro(RATE_I, 0)
            effect.set_macro(DEPTH_I, 0)
            effect.set_macro(DRIVE_I, _component.macro_of(
                Phaser._MACRO_RANGES[DRIVE_I], drive))
            effect.set_macro(FEEDBACK_I, _component.macro_of(
                Phaser._MACRO_RANGES[FEEDBACK_I], fb))
            wet = np.frombuffer(pcm(effect.output, 65536),
                                dtype=np.int16)[0::2].astype(np.float64)
            dry = np.frombuffer(pcm(dry_src, 65536),
                                dtype=np.int16)[0::2].astype(np.float64)
            n = len(wet)
            win = np.hanning(n)
            mag = (np.abs(np.fft.rfft(wet * win))
                   / np.maximum(np.abs(np.fft.rfft(dry * win)), 1.0))
            hz = np.fft.rfftfreq(n, 1.0 / RATE)
            band = (hz >= 600.0) & (hz <= 1800.0)
            db = 20.0 * np.log10(np.maximum(mag[band], 1e-12))
            return float(np.max(db))

        default_rise = peak(0.3, 0.7) - peak(0.3, 0.0)
        self.assertLess(default_rise, 5.0, default_rise)

        def stuck_peak(fb):
            rng = np.random.RandomState(3)
            noise = rng.randint(-8000, 8001, size=32768 * 2, dtype=np.int16)
            buf = array.array("h", noise.tobytes())
            source = audiocore.RawSample(buf, sample_rate=RATE,
                                        channel_count=2)
            dry_src = audiocore.RawSample(array.array("h", buf),
                                          sample_rate=RATE,
                                          channel_count=2)
            effect = FeedbackStuck.create(source, RATE)
            effect.set_macro(RATE_I, 0)
            effect.set_macro(DEPTH_I, 0)
            effect.set_macro(FEEDBACK_I, _component.macro_of(
                Phaser._MACRO_RANGES[FEEDBACK_I], fb))
            wet = np.frombuffer(pcm(effect.output, 32768),
                                dtype=np.int16)[0::2].astype(np.float64)
            dry = np.frombuffer(pcm(dry_src, 32768),
                                dtype=np.int16)[0::2].astype(np.float64)
            n = len(wet)
            win = np.hanning(n)
            mag = (np.abs(np.fft.rfft(wet * win))
                   / np.maximum(np.abs(np.fft.rfft(dry * win)), 1.0))
            hz = np.fft.rfftfreq(n, 1.0 / RATE)
            band = (hz >= 600.0) & (hz <= 1800.0)
            db = 20.0 * np.log10(np.maximum(mag[band], 1e-12))
            return float(np.max(db))

        self.assertLess(abs(stuck_peak(0.7) - stuck_peak(0.0)), 1.0)

    def test_p5_feedback_raises_peak_stuck_is_flat(self):
        def peak(cls, fb):
            rng = np.random.RandomState(3)
            noise = rng.randint(-8000, 8001, size=65536 * 2, dtype=np.int16)
            buf = array.array("h", noise.tobytes())
            source = audiocore.RawSample(buf, sample_rate=RATE,
                                        channel_count=2)
            dry_src = audiocore.RawSample(array.array("h", buf),
                                          sample_rate=RATE,
                                          channel_count=2)
            effect = cls.create(source, RATE)
            effect.set_macro(RATE_I, 0)
            effect.set_macro(DEPTH_I, 0)
            effect.set_macro(DRIVE_I, 0)
            effect.set_macro(FEEDBACK_I, _component.macro_of(
                Phaser._MACRO_RANGES[FEEDBACK_I], fb))
            wet = np.frombuffer(pcm(effect.output, 65536),
                                dtype=np.int16)[0::2].astype(np.float64)
            dry = np.frombuffer(pcm(dry_src, 65536),
                                dtype=np.int16)[0::2].astype(np.float64)
            n = len(wet)
            win = np.hanning(n)
            mag = (np.abs(np.fft.rfft(wet * win))
                   / np.maximum(np.abs(np.fft.rfft(dry * win)), 1.0))
            hz = np.fft.rfftfreq(n, 1.0 / RATE)
            band = (hz >= 600.0) & (hz <= 1800.0)
            db = 20.0 * np.log10(np.maximum(mag[band], 1e-12))
            return float(np.max(db))

        rise = peak(Phaser, 0.7) - peak(Phaser, 0.0)
        self.assertGreater(rise, 5.0, rise)
        stuck = peak(FeedbackStuck, 0.7) - peak(FeedbackStuck, 0.0)
        self.assertLess(stuck, 1.0, stuck)

    def test_mix_one_fault_fires_at_default_macros(self):
        clean = built()
        faulted = MixOneCascade.create(silence(), RATE)
        self.assertAlmostEqual(clean.macro(MIX_I), 0.5, delta=0.03)
        self.assertAlmostEqual(faulted.macro(MIX_I), 0.5, delta=0.03)
        self.assertGreater(abs(faulted._cascade.mix - 0.5), 0.4)

        def _build(cls):
            return cls.create(silence(), RATE)

        mix_out = faults.fault_reachability(
            Phaser, MixOneCascade,
            lambda e: (round(e._cascade.mix, 3), round(e.macro(MIX_I), 3)),
            _build, grid=(0, 32, 64, 96, 127), label="MixOneCascade")
        self.assertEqual(mix_out["target"], (1.0, 0.5))
        self.assertEqual(mix_out["checked"], 59)

        six_out = faults.fault_reachability(
            Phaser, SixStagesAlways,
            lambda e: (int(e._cascade.stages), round(e.macro(STAGES_I), 3)),
            _build, grid=(0, 32, 64, 96, 127), label="SixStagesAlways")
        self.assertEqual(six_out["target"], (6, 0.0))

        drive_out = faults.fault_reachability(
            Phaser, NoDriveLaw,
            lambda e: (round(getattr(e, "_drive_forced", e._value(DRIVE_I)), 3),
                       round(e.macro(DRIVE_I), 3)),
            _build, grid=(0, 32, 64, 96, 127), label="NoDriveLaw")
        self.assertEqual(drive_out["target"][0], 0.0)
        self.assertAlmostEqual(drive_out["target"][1], 0.3, delta=0.02)

        stuck = FeedbackStuck.create(silence(), RATE)
        stuck.set_macro(FEEDBACK_I, 64)
        target = (round(stuck._cascade.feedback, 3), round(stuck.macro(FEEDBACK_I), 3))
        self.assertEqual(target[0], 0.0)
        self.assertGreater(target[1], 0.4)
        fb_out = faults.fault_reachability(
            Phaser, target,
            lambda e: (round(e._cascade.feedback, 3), round(e.macro(FEEDBACK_I), 3)),
            _build, grid=(0, 32, 64, 96, 127), label="FeedbackStuck")
        self.assertEqual(fb_out["checked"], 59)

        checked = healthy = 0
        for index in range(10):
            for position in (0, 32, 64, 96, 127):
                rng = np.random.RandomState(2)
                noise = rng.randint(-8000, 8001, size=32768 * 2, dtype=np.int16)
                buf = array.array("h", noise.tobytes())
                source = audiocore.RawSample(buf, sample_rate=RATE,
                                            channel_count=2)
                dry_src = audiocore.RawSample(array.array("h", buf),
                                              sample_rate=RATE,
                                              channel_count=2)
                effect = MixOneCascade.create(source, RATE)
                effect.set_macro(RATE_I, 0)
                effect.set_macro(DEPTH_I, 0)
                effect.set_macro(DRIVE_I, 0)
                effect.set_macro(index, position)
                fl = _notch_floor_h(pcm(effect.output, 32768),
                                    pcm(dry_src, 32768))
                checked += 1
                if fl < -40.0:
                    healthy += 1
        for patch in Phaser.PATCHES:
            rng = np.random.RandomState(2)
            noise = rng.randint(-8000, 8001, size=32768 * 2, dtype=np.int16)
            buf = array.array("h", noise.tobytes())
            source = audiocore.RawSample(buf, sample_rate=RATE,
                                        channel_count=2)
            dry_src = audiocore.RawSample(array.array("h", buf),
                                          sample_rate=RATE,
                                          channel_count=2)
            effect = MixOneCascade.create(source, RATE)
            effect.program_change(patch)
            effect.set_macro(RATE_I, 0)
            effect.set_macro(DEPTH_I, 0)
            effect.set_macro(DRIVE_I, 0)
            fl = _notch_floor_h(pcm(effect.output, 32768),
                                pcm(dry_src, 32768))
            checked += 1
            if fl < -40.0:
                healthy += 1
        self.assertEqual(checked, 59)
        self.assertEqual(healthy, 0)


def _notches_h(wet_bytes, dry_bytes, floor_db=-12.0):
    wet = np.frombuffer(wet_bytes, dtype=np.int16)[0::2].astype(np.float64)
    dry = np.frombuffer(dry_bytes, dtype=np.int16)[0::2].astype(np.float64)
    n = min(len(wet), len(dry))
    win = np.hanning(n)
    num = np.abs(np.fft.rfft(wet[:n] * win))
    den = np.abs(np.fft.rfft(dry[:n] * win))
    hz = np.fft.rfftfreq(n, 1.0 / RATE)
    band = (hz >= 80.0) & (hz <= 8000.0)
    mag = num[band] / np.maximum(den[band], 1.0)
    freqs = hz[band]
    db = 20.0 * np.log10(np.maximum(mag, 1e-12))
    found = []
    for i in range(2, len(db) - 2):
        if db[i] < floor_db and db[i] <= db[i - 1] and db[i] <= db[i + 1]:
            if not found or freqs[i] > found[-1] * 1.8:
                found.append(float(freqs[i]))
    return found


def _notch_floor_h(wet_bytes, dry_bytes):
    wet = np.frombuffer(wet_bytes, dtype=np.int16)[0::2].astype(np.float64)
    dry = np.frombuffer(dry_bytes, dtype=np.int16)[0::2].astype(np.float64)
    n = min(len(wet), len(dry))
    win = np.hanning(n)
    num = np.abs(np.fft.rfft(wet[:n] * win))
    den = np.abs(np.fft.rfft(dry[:n] * win))
    hz = np.fft.rfftfreq(n, 1.0 / RATE)
    band = (hz >= 100.0) & (hz <= 8000.0)
    mag = num[band] / np.maximum(den[band], 1.0)
    mean = float(np.mean(mag))
    return 20.0 * math.log10(float(np.min(mag)) / max(mean, 1e-12))
