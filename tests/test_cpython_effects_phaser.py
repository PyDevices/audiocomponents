"""`Phaser`'s own invariant and planted-fault tests.

The dossier's
Tier 2 rows are P1..P10. Exhaustive rate coverage lives in the evidence
pack. This file stays at 48 kHz except where a test is about rate
handling.

The old `modulation.Phaser` had `MACRO_LABELS = ()` and no surface test
to retire.
"""

import array
import math
import os
import re
import sys
import unittest

import audiocore
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from audioeffects import _component                            # noqa: E402
from audioeffects import phaser as phaser_module               # noqa: E402
from tools import effect_measurements as kit                   # noqa: E402
import kit_ceiling                                          # noqa: E402
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


#: Drive's curve as the class shipped it before audiocomponents#77: the
#: cubic straight into Q15, peaking at 2/3 of the range.
OLD_CUBIC_CURVE = array.array("h")
for _index in range(phaser_module.CURVE_POINTS):
    _x = -1.0 + 2.0 * _index / float(phaser_module.CURVE_POINTS - 1)
    OLD_CUBIC_CURVE.append(max(-32768, min(32767,
                                           int(round((_x - _x ** 3 / 3.0)
                                                     * 32767.0)))))


class OldDriveTable(Phaser):
    """The control for the normalisation: the 66.7 % table and `post_gain`
    back at 1.0, which is the arithmetic this class shipped.

    `set(curve=...)` and not `node.curve = ...`: `Waveshaper` has no `curve`
    property, so the assignment would bind a stray Python attribute, leave
    the loaded table alone, and read as a 3.5 dB level move that is the
    normalisation rather than the class.
    """

    NAME = 'Phaser'

    def _build(self, *arguments, **keywords):
        Phaser._build(self, *arguments, **keywords)
        self._shaper.set(curve=OLD_CUBIC_CURVE, post_gain=1.0)


class NoPostGain(Phaser):
    """The fault the normalisation could have introduced: the filled table
    with the scale not carried back out."""

    NAME = 'Phaser'

    def _build(self, *arguments, **keywords):
        Phaser._build(self, *arguments, **keywords)
        self._shaper.set(post_gain=1.0)


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
        effect._guard.play(quiet)
        after = pcm(effect.output, 256)
        self.assertEqual(max(abs(int(v)) for v in memoryview(after).cast("h")),
                         0)
        self.assertEqual(len(effect._nodes), 3)
        leftover = ramp(256)
        effect.deinit()
        still = pcm(leftover, 256)
        self.assertGreater(max(abs(int(v)) for v in memoryview(still).cast("h")),
                           0)


class ReplaysTheSource(Phaser):
    """F4's fault: every Feedback, Mix, Stages or Drive move, and a reset,
    plays the borrowed source into the head of the graph again, which drops
    what the head had taken of it."""

    NAME = 'Phaser'

    def _refresh_drive(self):
        Phaser._refresh_drive(self)
        self._guard.play(self._source)


class TestPhaserKeepsItsPlace(unittest.TestCase):
    """A move that keeps the route, a move that changes it, and a reset
    play nothing from the source again: at Mix 0 the output stays the
    source, byte for byte, on a whole RawSample (which a re-play rewinds to
    its start) and on a stream of 100-frame buffers (where it drops part of
    one)."""

    MOVES = ((FEEDBACK_I, None), (MIX_I, 0.0), (DRIVE_I, 0.0),
             (STAGES_I, None), (DRIVE_I, None), ("reset", None))

    def _wire(self, cls, source, frames):
        effect = cls.create(source, RATE)
        effect.set_macro(MIX_I, 0.0)
        out = bytearray()

        def pull(blocks):
            for _ in range(blocks):
                out.extend(bytes(audiocore.get_buffer(effect.output)[1]))

        for index, (macro, value) in enumerate(self.MOVES):
            pull(1 + index % 2)
            if macro == "reset":
                effect.reset()
                effect.set_macro(MIX_I, 0.0)
            else:
                effect.set_macro(macro, effect.get_macro(macro)
                                 if value is None else value)
        while len(out) < 4 * frames:
            chunk = bytes(audiocore.get_buffer(effect.output)[1])
            if not chunk:
                break
            out += chunk
        effect.deinit()
        del out[4 * frames:]
        return bytes(out)

    def _check(self, make):
        frames = 3072
        expect = bytes(make(frames)[1])
        got = self._wire(Phaser, make(frames)[0], frames)
        self.assertEqual(got, expect[:len(got)])
        self.assertEqual(len(got), len(expect))
        planted = self._wire(ReplaysTheSource, make(frames)[0], frames)
        self.assertNotEqual(planted, expect[:len(planted)])

    def test_a_whole_raw_sample_is_not_rewound(self):
        def make(frames):
            values = array.array("h", [((i * 37) % 2001) - 1000
                                       for i in range(2 * frames)])
            return (audiocore.RawSample(values, sample_rate=RATE,
                                        channel_count=2), values)
        self._check(make)

    def test_a_stream_of_short_buffers_drops_nothing(self):
        import kit_probes

        def make(frames):
            values = array.array("h", [((i * 37) % 2001) - 1000
                                       for i in range(2 * frames)])
            return (kit_probes.ArraySource(values, rate=RATE, channels=2,
                                       block=100), values)
        self._check(make)


class TestPhaserCurveFillsTheRange(unittest.TestCase):
    """The drive table reaches the rails, and the generator will not emit
    one that does not ([audiocomponents#77]).

    `CUBIC_CURVE` used to hold `y = x - x**3/3` straight in Q15, and that
    curve peaks at 2/3 by construction, so the table used **66.7 %** of
    int16 and threw away half a bit of the only resolution a lookup table
    has. It is normalised to its own extreme now and `CURVE_SCALE` carries
    the 2/3 back out in the shaper's `post_gain`, so the level does not
    move.
    """

    def _generator(self):
        from tools.curves import phaser_curve
        return phaser_curve

    def _quiet_check(self, gen):
        """`--check` with its report swallowed; returns the exit code."""
        import io
        import contextlib
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink), \
                contextlib.redirect_stderr(sink):
            return gen.main(["--check"])

    def test_shipped_table_reaches_both_rails(self):
        self.assertEqual((min(phaser_module.CUBIC_CURVE),
                          max(phaser_module.CUBIC_CURVE)),
                         (-32767, 32767))

    def _held_level(self, cls=None, dbfs=-14.0, frames=24000):
        """Output RMS and peak of a held Phaser over a 1 kHz tone.

        Held, because a swept notch is not a stationary level: the reading
        would be about where the LFO happened to be.
        """
        values = array.array("h")
        amplitude = (10.0 ** (dbfs / 20.0)) * 32767.0
        for index in range(frames):
            sample = int(round(amplitude * math.sin(2.0 * math.pi * 1000.0
                                                    * index / RATE)))
            values.append(max(-32768, min(32767, sample)))
            values.append(max(-32768, min(32767, sample)))
        source = audiocore.RawSample(values, sample_rate=RATE,
                                     channel_count=2)
        effect = (cls or Phaser).create(source, RATE, rate=0.0, depth=0.0)
        try:
            data = np.frombuffer(pcm(effect.output, frames),
                                 dtype=np.int16).astype(np.float64)
        finally:
            effect.deinit()
        settled = data[4800 * 2:]
        return (20.0 * math.log10(math.sqrt(float(np.mean(settled ** 2)))
                                  / 32767.0),
                float(np.max(np.abs(settled))))

    def test_carrying_the_scale_in_post_gain_does_not_move_the_level(self):
        """The whole point of the normalisation: finer table, same sound.

        The control is the class with the **pre-fix** table and `post_gain`
        back at 1.0, which is the arithmetic the class shipped. It has to
        land on the same level, and the fault below shows the row can fail:
        the normalised table with `post_gain` left at 1.0 is 3.5 dB loud.
        """
        for dbfs in (-26.0, -14.0, -6.0):
            with self.subTest(dbfs=dbfs):
                before = self._held_level(OldDriveTable, dbfs)
                after = self._held_level(Phaser, dbfs)
                self.assertLess(abs(after[0] - before[0]), 0.01,
                                "RMS %.6f against %.6f" % (after[0],
                                                           before[0]))
                self.assertEqual(after[1], before[1])

    def test_without_the_post_gain_the_level_moves(self):
        """The planted fault, and it is the mistake this change could have
        made: normalise the table and forget to carry the scale out."""
        before = self._held_level(OldDriveTable)
        loud = self._held_level(NoPostGain)
        self.assertGreater(loud[0] - before[0], 1.0)

    def test_module_holds_what_the_generator_writes(self):
        self.assertEqual(self._quiet_check(self._generator()), 0)

    def test_generator_refuses_a_table_that_leaves_the_range_empty(self):
        """Planted: the pre-fix normalisation, the cubic straight into
        Q15."""
        gen = self._generator()
        keep = gen.curve_scale
        try:
            gen.curve_scale = lambda: 1.0
            self.assertLess(gen.fill(gen.table_words()), 0.95)
            self.assertNotEqual(self._quiet_check(gen), 0)
        finally:
            gen.curve_scale = keep
        self.assertEqual(self._quiet_check(gen), 0)

    def test_the_table_is_odd_so_it_writes_no_even_harmonics(self):
        """An asymmetric table would put even harmonics into a stage that
        has none. The grid is symmetric and the curve is odd, so every pair
        has to cancel exactly."""
        points = list(phaser_module.CUBIC_CURVE)
        for index in range(len(points) // 2):
            self.assertEqual(points[index], -points[len(points) - 1 - index])


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


class Meter:
    """A host transport whose tempo and time signature a test moves, in
    the API's order: (playing, seconds, bpm, numerator, denominator)."""

    def __init__(self, bpm=120.0, numerator=4, denominator=4):
        self.bpm = bpm
        self.numerator = numerator
        self.denominator = denominator

    def __call__(self):
        return (True, 0.0, self.bpm, self.numerator, self.denominator)


class MeterDeaf(Phaser):
    """The base's `transport_changed()`: it follows the tempo alone, so a
    meter change at one tempo keeps the old rate."""

    def transport_changed(self):
        _component.Component.transport_changed(self)


def synced(cls=Phaser, meter=None):
    """A Phaser with Sync on under `meter`, having read it once."""
    meter = meter or Meter()
    effect = built(cls=cls, transport=meter)
    effect.set_macro(SYNC_I, 127)
    effect.transport_changed()
    return effect, meter


def bar_rate(effect, bpm, quarters):
    """The sweep's rate for Division at `quarters` quarter notes a bar."""
    bars = phaser_module._choice(phaser_module.DIVISION_BARS,
                                 effect._macros[DIV_I])
    return bpm / (60.0 * quarters * bars)


class TestPhaserFollowsTheMeter(unittest.TestCase):
    """With Sync on the sweep lasts Division bars, and a bar is the host's
    time signature: numerator x 4 / denominator quarter notes at its
    tempo (the transport's fourth and fifth fields)."""

    def test_the_bar_is_the_time_signature(self):
        for numerator, denominator, quarters in (
                (4, 4, 4.0), (3, 4, 3.0), (6, 8, 3.0), (7, 8, 3.5),
                (2, 2, 4.0), (5, 4, 5.0)):
            with self.subTest(meter="%d/%d" % (numerator, denominator)):
                effect, _ = synced(meter=Meter(120.0, numerator,
                                               denominator))
                self.assertAlmostEqual(effect._lfo.rate,
                                       bar_rate(effect, 120.0, quarters),
                                       places=9)

    def test_a_meter_change_is_followed(self):
        # 4/4 to 3/4 at one tempo, `transport_changed()` after it: the rate
        # is the one a fresh instance built in 3/4 has.
        for cls, follows in ((Phaser, True), (MeterDeaf, False)):
            with self.subTest(cls=cls.__name__):
                effect, meter = synced(cls)
                before = effect._lfo.rate
                meter.numerator = 3
                effect.transport_changed()
                fresh, _ = synced(meter=Meter(120.0, 3, 4))
                if follows:
                    self.assertEqual(effect._lfo.rate, fresh._lfo.rate)
                    self.assertNotEqual(effect._lfo.rate, before)
                else:
                    self.assertEqual(effect._lfo.rate, before)

    def test_a_held_meter_reads_once_and_moves_nothing(self):
        effect, meter = synced()
        rate = effect._lfo.rate
        for _ in range(4):
            effect.transport_changed()
        self.assertEqual(effect._lfo.rate, rate)

    def test_a_nan_meter_is_unchanged_as_a_nan_tempo_is(self):
        # The base's rule for a tempo: a NaN read twice is no change.
        effect, meter = synced(meter=Meter(120.0, float("nan"), 4))
        calls = []
        orig = effect._apply_macro

        def counting(index, position):
            calls.append(index)
            orig(index, position)
        effect._apply_macro = counting
        effect.transport_changed()
        self.assertEqual(calls, [])
        self.assertAlmostEqual(effect._lfo.rate, bar_rate(effect, 120.0, 4.0),
                               places=9)


class TheClaims(unittest.TestCase):

    def test_the_constructor_drive_and_mix(self):
        effect = built()
        self.assertAlmostEqual(effect.macro(DRIVE_I), 0.3, delta=0.01)
        self.assertAlmostEqual(effect.macro(MIX_I), 0.5, delta=0.01)
        lean = Phaser.PATCHES[8]
        self.assertEqual(lean[0], "Phaser - lean")
        self.assertEqual(lean[1][:DRIVE_I], Phaser.PATCHES[0][1][:DRIVE_I])
        self.assertEqual(lean[1][DRIVE_I], 0)
        self.assertEqual(lean[1][DRIVE_I + 1:],
                         Phaser.PATCHES[0][1][DRIVE_I + 1:])

    def test_the_reported_tail_is_the_worst_case(self):
        self.assertEqual(Phaser.TAIL_SAMPLES, 552960)

    def test_construction_needs_audiobiquad_and_audioshaper(self):
        self.assertEqual(Phaser.REQUIRES, ("audiobiquad", "audioshaper"))
        for name in Phaser.REQUIRES:
            with self.subTest(module=name):
                saved = sys.modules[name]
                sys.modules[name] = None
                try:
                    with self.assertRaises(ImportError):
                        Phaser.create(silence(), RATE)
                finally:
                    sys.modules[name] = saved


class TheCeiling(unittest.TestCase):
    def test_clean_at_the_stated_input_level(self):
        # sq147 is where it rails first: p1 at -6 dBFS.
        self.assertEqual(
            kit_ceiling.stated_level_reds(Phaser, "sq147"), [])
        self.assertTrue(kit_ceiling.stated_level_reds(
            Phaser, "sq147", db=-6, keys=("p1",)))


CLAIMS = (
    ("Keep the input under -9 dBFS and the defaults and patches stay "
     "off the rails.",
     ("TheCeiling.test_clean_at_the_stated_input_level",)),
    ("`Phaser` - four first-order all-pass stages swept the way a Phase 90 "
     "is.",
     ("TestPhaserTraits.test_p1_two_notches_at_defaults_six_stages_is_"
      "three",)),
    ("The player's text is the class docstring; the `CLAIMS` table in the "
     "class's test file ties its claim sentences to tests.",
     ("Claims.test_every_claim_is_in_the_docstring_and_tested",)),
    ("A phaser after the Phase 90: notches swept up and down your signal on "
     "a triangle.",
     ("TestPhaserTraits.test_p1_two_notches_at_defaults_six_stages_is_"
      "three",
      "TestPhaserTraits.test_default_lfo_is_builtin_not_a_table")),
    ("Rate is the sweep's speed, and at 0 the notches hold still.",
     ("TestPhaserTraits.test_p1_two_notches_at_defaults_six_stages_is_three",)),
    ("Stages sets how many all-pass stages there are, and each pair "
     "makes a notch: four stages make two, the second about two and "
     "a half octaves above the first.",
     ("TestPhaserTraits.test_p1_two_notches_at_defaults_six_stages_is_three",)),
    ("Mix at 0 is your dry signal, and at 0.5, the default, the notches go "
     "deeper than 40 dB.",
     ("TestPhaserInvariants.test_mix_zero_is_a_wire",
      "TheClaims.test_the_constructor_drive_and_mix",
      "TestPhaserTraits.test_p4_null_at_defaults_mix_one_is_shallow",
      "TestPhaserTraits.test_mix_one_fault_fires_at_default_macros")),
    ("Feedback lifts a hump between the notches.",
     ("TestPhaserTraits.test_p5_feedback_raises_peak_stuck_is_flat",)),
    ("Drive softens the signal on its way into the stages, so it "
     "grows harmonics as your level rises.",
     ("TestPhaserTraits.test_p7_harmonics_grow_fault_is_flat",
      "TestPhaserTraits.test_p7_harmonics_at_constructor_drive_fault_is_flat")),
    ("Drive is 0.3 when you construct the class, and there the Feedback "
     "hump stays under 5 dB.",
     ("TheClaims.test_the_constructor_drive_and_mix",
      "TestPhaserTraits.test_p5_misses_at_constructor_drive")),
    ("Turn Drive to 0 and Feedback lifts it more than 5 dB.",
     ("TestPhaserTraits.test_p5_feedback_raises_peak_stuck_is_flat",)),
    ("The Phaser - lean patch is the default with Drive at 0.",
     ("TheClaims.test_the_constructor_drive_and_mix",)),
    ("With Sync on, the sweep locks to the host: Division picks the "
     "length of a sweep in bars, a bar is read from the host's time "
     "signature, and a change of tempo or meter is followed.",
     ("TestPhaserInvariants.test_capabilities_declare_tempo_sync_and_read_transport",
      "TestPhaserFollowsTheMeter.test_the_bar_is_the_time_signature",
      "TestPhaserFollowsTheMeter.test_a_meter_change_is_followed")),
    ("Latency is zero at every setting.",
     ("TestPhaserInvariants.test_latency_is_zero_and_click_agrees",)),
    ("Silence in is silence out once the notches ring down, which at "
     "musical settings is quick; the class reports the worst case, 552960 "
     "samples, for stages at their sharpest.",
     ("TestPhaserInvariants.test_silence_tail_reaches_zero",
      "TheClaims.test_the_reported_tail_is_the_worst_case")),
    ("The class needs audiodsp's `audiobiquad` and `audioshaper`, and on a "
     "board without them construction raises `ImportError`.",
     ("TheClaims.test_construction_needs_audiobiquad_and_audioshaper",)),
)


def _flat(text):
    return " ".join(text.split())


def claim_problems(doc, claims=CLAIMS):
    """What is wrong between a docstring and `claims`: a sentence missing, a
    named test that does not exist, a figure outside every claim."""
    doc = _flat(doc)
    problems = []
    rest = doc
    for sentence, tests in claims:
        if sentence not in doc:
            problems.append("missing: %s" % sentence)
        rest = rest.replace(sentence, " ")
        for name in tests:
            owner, _, test = name.partition(".")
            if not hasattr(globals().get(owner), test):
                problems.append("no test %s" % name)
    for match in re.finditer(r"\S*\d\S*", rest):
        problems.append("figure outside a claim: %s" % match.group())
    return problems


class Claims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        doc = phaser_module.__doc__ + " " + Phaser.__doc__
        self.assertEqual(claim_problems(doc), [])
        # The checker can fail: a figure outside a claim, a claim the
        # docstring does not carry, a test that does not exist.
        self.assertTrue(claim_problems(doc + " It reads 12 ms."))
        self.assertTrue(claim_problems(doc.replace("deeper than",
                                                   "shallower than")))
        self.assertTrue(claim_problems(
            doc, CLAIMS + (("Latency", ("TheClaims.test_nothing_here",)),)))


#: Not here, because they show only when a knob moves, on a reset or a
#: rejoin, or not at all on a fresh build: `MeterDeaf`; they change only a
#: reported tail or latency: `ShortLatency`; they render what a knob or a
#: patch renders, so the kit cannot tell them from a setting:
#: `MixOneCascade`, `NoDriveLaw`, `FeedbackStuck`.
KIT_PLANTS = {
    "SixStagesAlways": SixStagesAlways,
    "OldDriveTable": OldDriveTable,
    "NoPostGain": NoPostGain,
    "ReplaysTheSource": ReplaysTheSource,
}
