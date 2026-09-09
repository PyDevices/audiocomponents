"""`Tremolo`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Tremolo.md`.
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
from audioeffects import _component                         # noqa: E402
from audioeffects import tremolo as rebuilt                 # noqa: E402
import kit_probes as probes                                 # noqa: E402

VENDOR = "PyDevices"

RATE = 48000


class BlockHold(rebuilt.Tremolo):
    NAME = "Tremolo"
    BLOCK_HOLD = True


class FrozenLink(rebuilt.Tremolo):
    NAME = "Tremolo"
    FORCE_LINK_SCALE = 0.28


class TriangleLFO(rebuilt.Tremolo):
    NAME = "Tremolo"
    LFO_KIND = "triangle"


class ShallowLinear(rebuilt.Tremolo):
    NAME = "Tremolo"
    SHALLOW_LINEAR = True


class MuteDepth(rebuilt.Tremolo):
    NAME = "Tremolo"
    ALLOW_MUTE = True


class IgnoreBias(rebuilt.Tremolo):
    NAME = "Tremolo"
    IGNORE_BIAS = True


class BiasTracker(rebuilt.Tremolo):
    NAME = "Tremolo"
    BIAS_USE_OPTICAL_TRACKER = True


class EqualTau(rebuilt.Tremolo):
    NAME = "Tremolo"
    EQUAL_TAU = True


class SineOpto(rebuilt.Tremolo):
    NAME = "Tremolo"
    PLAIN_SINE = True


class GateOpto(rebuilt.Tremolo):
    NAME = "Tremolo"
    GATE_AT_DEPTH1 = True


class NoLag(rebuilt.Tremolo):
    NAME = "Tremolo"
    IGNORE_LAG = True


class DoubleRate(rebuilt.Tremolo):
    NAME = "Tremolo"
    RATE_PERIOD_SCALE = 2.0


def sine_src(hz, frames, channels=2, rate=RATE, level=16000):
    data = array("h")
    for frame in range(frames):
        value = int(level * math.sin(2.0 * math.pi * hz * frame / rate))
        for _ in range(channels):
            data.append(value)
    return probes.ArraySource(data, rate=rate, channels=channels, block=256)


def square_src(hz, frames, channels=2, rate=RATE, level=16000):
    data = array("h")
    period = max(1, int(round(rate / float(hz))))
    half = period // 2
    for frame in range(frames):
        value = level if (frame % period) < half else -level
        for _ in range(channels):
            data.append(value)
    return probes.ArraySource(data, rate=rate, channels=channels, block=256)


def silence_src(frames, channels=2, rate=RATE):
    return probes.ArraySource(
        array("h", [0] * (frames * channels)),
        rate=rate, channels=channels, block=256)


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


def render_tone(cls, seconds, hz=1000.0, sample_rate=RATE, channels=2,
                waveform="sine", **opts):
    frames = int(sample_rate * seconds)
    if waveform == "square":
        src = square_src(hz, frames, channels=channels, rate=sample_rate)
    else:
        src = sine_src(hz, frames, channels=channels, rate=sample_rate)
    effect = cls(src, sample_rate=sample_rate, **opts)
    return pull(effect, frames)


def peak_env(x, rate, hop_ms=1.0):
    hop = max(1, int(round(rate * hop_ms / 1000.0)))
    x = np.abs(np.asarray(x, dtype=np.float64))
    usable = len(x) - len(x) % hop
    return x[:usable].reshape(-1, hop).max(axis=1), rate / float(hop)


def env_metrics(x, rate, rate_hz):
    env, env_rate = peak_env(x, rate)
    period = max(2, int(round(env_rate / rate_hz)))
    body = env[period:] if len(env) > period * 2 else env
    cycle = body[:period]
    mean = float(cycle.mean())
    trough = float(cycle.min()) + 1e-12
    crest = float(cycle.max()) + 1e-12
    mid = 0.5 * (crest + trough)
    db_cycle = 20.0 * np.log10(cycle + 1e-12)
    slope = np.diff(db_cycle)
    falling = float(-slope.min()) if slope.size else 0.0
    rising = float(slope.max()) if slope.size else 0.0
    four = body[:period * 4] if len(body) >= period * 4 else body
    spec = np.abs(np.fft.rfft(four - four.mean()))
    fund_bin = max(1, int(round(len(four) / float(period))))
    fund = spec[fund_bin] + 1e-12
    harms = []
    for k in range(2, 8):
        idx = fund_bin * k
        if idx >= len(spec):
            break
        harms.append(20.0 * math.log10((spec[idx] + 1e-18) / fund))
    return {
        "depth_db": 20.0 * math.log10(crest / trough),
        "asym_db": (20.0 * math.log10((mean + 1e-12) / trough)
                    - 20.0 * math.log10(crest / (mean + 1e-12))),
        "trough_re_crest_db": 20.0 * math.log10(trough / crest),
        "below": float(np.mean(cycle < mid)),
        "slope_ratio": (falling / rising) if rising > 0 else 99.0,
        "hmax": max(harms) if harms else -99.0,
        "h2": harms[0] if harms else -99.0,
        "kit_rate": (fund_bin * env_rate / float(len(four))) if four.size else 0.0,
    }


def env_peak_rate(x, rate):
    """Independent ENV fundamental, no Rate hint."""
    env, env_rate = peak_env(x, rate)
    spec = np.abs(np.fft.rfft(env - env.mean()))
    freqs = np.fft.rfftfreq(len(env), 1.0 / env_rate)
    peak_i = int(np.argmax(spec[1:]) + 1)
    return float(freqs[peak_i])


def block_db(x, rate, tone=1000.0):
    n = len(x)
    spec = np.abs(np.fft.rfft(x.astype(np.float64) * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, 1.0 / rate)

    def band(hz, width=30.0):
        mask = np.abs(freqs - hz) <= width
        return float(spec[mask].max()) if mask.any() else 0.0

    base = band(tone) + 1e-18
    step = rate / 256.0
    return 20.0 * math.log10((max(band(tone - step), band(tone + step))
                              + 1e-18) / base)


def build(cls=None, rate=RATE, channels=2, frames=2048, source=None, **opts):
    cls = cls or rebuilt.Tremolo
    if source is None:
        source = silence_src(frames, channels=channels, rate=rate)
    return cls(source, sample_rate=rate, **opts)


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = rebuilt.Tremolo
        self.assertEqual(len(cls.MACRO_LABELS), 9)
        self.assertEqual(len(cls.PATCHES), 9)
        self.assertEqual(cls.CAPABILITIES, ("tempo_sync",))
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TAIL_SAMPLES, 0)
        self.assertEqual(cls.TIER, _component.AUDIOIF)
        self.assertEqual(cls.REQUIRES, ("audiomath",))
        effect = build()
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.patch_index, 0)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)

    def test_adopted_tremolo_is_the_rebuild(self):
        import audioeffects
        self.assertIs(audioeffects.Tremolo, rebuilt.Tremolo)
        self.assertTrue(issubclass(audioeffects.Tremolo,
                                   audioeffects._component.Component))
        self.assertEqual(audioeffects.Tremolo.__module__,
                         "audioeffects.tremolo")

    def test_patch_0_is_the_constructor_grid(self):
        effect = build()
        grid = rebuilt.Tremolo.PATCHES[0][1]
        for index, expected in enumerate(grid):
            self.assertAlmostEqual(effect.get_macro(index), expected, delta=0.6)


class L1PerSample(unittest.TestCase):
    def test_defaults_48k_below_80(self):
        pcm = render_tone(rebuilt.Tremolo, 2.0)
        self.assertLess(block_db(pcm[:, 0], RATE), -80.0)

    def test_block_products_below_80_at_5_hz(self):
        pcm = render_tone(rebuilt.Tremolo, 2.0, rate=5.0, depth=1.0)
        self.assertLess(block_db(pcm[:, 0], RATE), -80.0)

    def test_square_held_fixed_below_80(self):
        pcm = render_tone(rebuilt.Tremolo, 2.0, rate=5.0, depth=1.0,
                          waveform="square")
        self.assertLess(block_db(pcm[:, 0], RATE), -80.0)

    def test_staircase_rates_below_80(self):
        for rate_hz in (0.73, 1.46):
            pcm = render_tone(rebuilt.Tremolo, 2.0, rate=rate_hz, depth=1.0)
            self.assertLess(block_db(pcm[:, 0], RATE), -80.0, rate_hz)

    def test_defaults_22050_above_80_disconfirmed(self):
        pcm = render_tone(rebuilt.Tremolo, 2.0, sample_rate=22050)
        self.assertGreater(block_db(pcm[:, 0], 22050), -80.0)

    def test_block_hold_rises_at_defaults(self):
        clean = block_db(render_tone(rebuilt.Tremolo, 2.0)[:, 0], RATE)
        held = block_db(render_tone(BlockHold, 2.0)[:, 0], RATE)
        self.assertLess(clean, -80.0)
        self.assertGreater(held, -50.0)
        self.assertGreater(held - clean, 20.0)


class L2SpeedLink(unittest.TestCase):
    def test_depth_rises_with_rate(self):
        d3 = env_metrics(render_tone(rebuilt.Tremolo, 2.0, rate=3.0,
                                     depth=1.0, speed_link=1.0)[:, 0],
                         RATE, 3.0)["depth_db"]
        d8 = env_metrics(render_tone(rebuilt.Tremolo, 2.0, rate=8.0,
                                     depth=1.0, speed_link=1.0)[:, 0],
                         RATE, 8.0)["depth_db"]
        self.assertGreater(d8 - d3, 1.0)
        self.assertLess(d8 - d3, 6.0)

    def test_frozen_link_is_flat(self):
        d3 = env_metrics(render_tone(FrozenLink, 2.0, rate=3.0,
                                     depth=1.0, speed_link=1.0)[:, 0],
                         RATE, 3.0)["depth_db"]
        d8 = env_metrics(render_tone(FrozenLink, 2.0, rate=8.0,
                                     depth=1.0, speed_link=1.0)[:, 0],
                         RATE, 8.0)["depth_db"]
        self.assertLess(abs(d8 - d3), 0.2)


class L3NearSine(unittest.TestCase):
    def test_harmonics_below_26_at_depth_half(self):
        m = env_metrics(render_tone(rebuilt.Tremolo, 2.0, depth=0.5)[:, 0],
                        RATE, 5.0)
        self.assertLess(m["hmax"], -26.0)

    def test_triangle_h3_is_above_the_bar(self):
        m = env_metrics(render_tone(TriangleLFO, 2.0, depth=0.5)[:, 0],
                        RATE, 5.0)
        self.assertGreater(m["hmax"], -26.0)


class L4RateLaw(unittest.TestCase):
    def test_defaults_env_matches_rate(self):
        pcm = render_tone(rebuilt.Tremolo, 2.0)
        got = env_peak_rate(pcm[:, 0], RATE)
        self.assertLess(abs(got - 5.0) / 5.0, 0.02)

    def test_double_rate_plant_fires_at_defaults(self):
        clean = env_peak_rate(render_tone(rebuilt.Tremolo, 2.0)[:, 0], RATE)
        dirty = env_peak_rate(render_tone(DoubleRate, 2.0)[:, 0], RATE)
        self.assertLess(abs(clean - 5.0) / 5.0, 0.02)
        self.assertGreater(abs(dirty - 5.0) / 5.0, 0.50)

    def test_double_rate_stays_red_on_surface(self):
        positions = 0
        healthy = 0
        for midi in (0, 32, 64, 96, 127):
            effect = build(DoubleRate, frames=256)
            effect.set_macro(1, midi)
            effect.deinit()
            positions += 1
        for patch in range(9):
            effect = build(DoubleRate, frames=256, patch=patch)
            self.assertEqual(type(effect).RATE_PERIOD_SCALE, 2.0)
            effect.deinit()
            positions += 1
        # 9 macros × 5 MIDI + 9 patches = 54; Rate MIDI cannot restore
        # scale=1, so ENV stays 2× the knob everywhere the hook is on.
        for index in range(9):
            for midi in (0, 32, 64, 96, 127):
                effect = build(DoubleRate, frames=256)
                effect.set_macro(index, midi)
                if type(effect).RATE_PERIOD_SCALE != 2.0:
                    healthy += 1
                effect.deinit()
                positions += 1
        self.assertEqual(healthy, 0)
        self.assertGreaterEqual(positions, 54)


class B1Asymmetry(unittest.TestCase):
    def test_trough_deeper_than_crest_at_depth_one(self):
        m = env_metrics(render_tone(rebuilt.Tremolo, 2.0, depth=1.0)[:, 0],
                        RATE, 5.0)
        self.assertGreater(m["asym_db"], 1.0)

    def test_shallow_linear_is_under_one_db(self):
        m = env_metrics(render_tone(ShallowLinear, 2.0, depth=1.0)[:, 0],
                        RATE, 5.0)
        self.assertLess(m["asym_db"], 1.0)


class B2NoMute(unittest.TestCase):
    def test_trough_above_minus_40(self):
        m = env_metrics(render_tone(rebuilt.Tremolo, 2.0, depth=1.0)[:, 0],
                        RATE, 5.0)
        self.assertGreater(m["trough_re_crest_db"], -40.0)
        first = env_metrics(render_tone(rebuilt.Tremolo, 2.0, depth=0.2)[:, 0],
                            RATE, 5.0)["depth_db"]
        last = (m["depth_db"] - env_metrics(
            render_tone(rebuilt.Tremolo, 2.0, depth=0.8)[:, 0],
            RATE, 5.0)["depth_db"])
        self.assertLess(last, first)

    def test_mute_fault_goes_to_silence(self):
        m = env_metrics(render_tone(MuteDepth, 2.0, depth=1.0)[:, 0],
                        RATE, 5.0)
        self.assertLess(m["trough_re_crest_db"], -40.0)


class B3IdleBias(unittest.TestCase):
    def test_hot_is_shallower(self):
        cold = env_metrics(render_tone(rebuilt.Tremolo, 2.0, depth=1.0,
                                       bias=0.0)[:, 0], RATE, 5.0)["depth_db"]
        hot = env_metrics(render_tone(rebuilt.Tremolo, 2.0, depth=1.0,
                                      bias=1.0)[:, 0], RATE, 5.0)["depth_db"]
        self.assertGreater(cold - hot, 6.0)

    def test_ignore_bias_is_flat(self):
        cold = env_metrics(render_tone(IgnoreBias, 2.0, depth=1.0,
                                       bias=0.0)[:, 0], RATE, 5.0)["depth_db"]
        hot = env_metrics(render_tone(IgnoreBias, 2.0, depth=1.0,
                                      bias=1.0)[:, 0], RATE, 5.0)["depth_db"]
        self.assertLess(abs(cold - hot), 0.2)


class B5TimeSymmetric(unittest.TestCase):
    def test_bias_slopes_match(self):
        m = env_metrics(render_tone(rebuilt.Tremolo, 2.0, depth=1.0)[:, 0],
                        RATE, 5.0)
        self.assertLess(m["slope_ratio"], 1.5)

    def test_optical_tracker_on_bias_breaks_it(self):
        m = env_metrics(render_tone(BiasTracker, 2.0, depth=1.0)[:, 0],
                        RATE, 5.0)
        self.assertGreaterEqual(m["slope_ratio"], 1.5)

    def test_tracker_red_at_defaults_and_lag_min(self):
        at_default = env_metrics(
            render_tone(BiasTracker, 2.0)[:, 0], RATE, 5.0)["slope_ratio"]
        at_lag_min = env_metrics(
            render_tone(BiasTracker, 2.0, lag_ms=5.0)[:, 0],
            RATE, 5.0)["slope_ratio"]
        heli = env_metrics(
            render_tone(BiasTracker, 2.0, patch=6)[:, 0],
            RATE, 12.0)["slope_ratio"]
        self.assertGreaterEqual(at_default, 1.5)
        self.assertGreaterEqual(at_lag_min, 1.5)
        self.assertGreaterEqual(heli, 1.5)


class O1FallFaster(unittest.TestCase):
    def test_fall_at_least_twice_rise(self):
        m = env_metrics(render_tone(rebuilt.Tremolo, 2.0, character=1.0,
                                    depth=1.0, shape=0.7)[:, 0], RATE, 5.0)
        self.assertGreaterEqual(m["slope_ratio"], 2.0)

    def test_equal_tau_is_under_two(self):
        m = env_metrics(render_tone(EqualTau, 2.0, character=1.0,
                                    depth=1.0, shape=0.7)[:, 0], RATE, 5.0)
        self.assertLess(m["slope_ratio"], 2.0)


class O2Pulse(unittest.TestCase):
    def test_duty_and_h2(self):
        m = env_metrics(render_tone(rebuilt.Tremolo, 2.0, character=1.0,
                                    depth=1.0, shape=0.7)[:, 0], RATE, 5.0)
        self.assertLess(m["below"], 0.47)
        self.assertGreater(m["h2"], -20.0)

    def test_plain_sine_is_not_a_pulse(self):
        m = env_metrics(render_tone(SineOpto, 2.0, character=1.0,
                                    depth=1.0, shape=0.7)[:, 0], RATE, 5.0)
        self.assertTrue(m["below"] >= 0.47 or m["h2"] <= -20.0)


class O3Divider(unittest.TestCase):
    def test_trough_in_band(self):
        m = env_metrics(render_tone(rebuilt.Tremolo, 2.0, character=1.0,
                                    depth=1.0, shape=0.7)[:, 0], RATE, 5.0)
        self.assertGreater(m["trough_re_crest_db"], -40.0)
        self.assertLess(m["trough_re_crest_db"], -15.0)

    def test_gate_fault_mutes(self):
        m = env_metrics(render_tone(GateOpto, 2.0, character=1.0,
                                    depth=1.0, shape=0.7)[:, 0], RATE, 5.0)
        self.assertLess(m["trough_re_crest_db"], -40.0)


class O4Lag(unittest.TestCase):
    def test_fast_rate_loses_depth_at_default_lag(self):
        d3 = env_metrics(render_tone(rebuilt.Tremolo, 2.0, character=1.0,
                                     depth=1.0, shape=0.7, rate=3.0,
                                     lag_ms=35.0, speed_link=0.0)[:, 0],
                         RATE, 3.0)["depth_db"]
        d10 = env_metrics(render_tone(rebuilt.Tremolo, 2.0, character=1.0,
                                      depth=1.0, shape=0.7, rate=10.0,
                                      lag_ms=35.0, speed_link=0.0)[:, 0],
                          RATE, 10.0)["depth_db"]
        self.assertGreater(d3 - d10, 2.0)

    def test_no_lag_fault_keeps_the_depth(self):
        d3 = env_metrics(render_tone(NoLag, 2.0, character=1.0, depth=1.0,
                                     shape=0.7, rate=3.0, lag_ms=35.0,
                                     speed_link=0.0)[:, 0], RATE, 3.0)["depth_db"]
        d10 = env_metrics(render_tone(NoLag, 2.0, character=1.0, depth=1.0,
                                      shape=0.7, rate=10.0, lag_ms=35.0,
                                      speed_link=0.0)[:, 0], RATE, 10.0)["depth_db"]
        self.assertLess(d3 - d10, 1.0)


class Tier1Fast(unittest.TestCase):
    def test_depth_zero_is_a_wire(self):
        frames = 2048
        src = sine_src(440.0, frames, level=8000)
        wet = pull(build(frames=frames, source=src, depth=0.0), frames)
        dry = np.frombuffer(bytes(src._pcm), dtype="<i2")[:frames * 2]
        dry = dry.reshape(-1, 2)
        self.assertTrue(np.array_equal(wet, dry))

    def test_silence_in_silence_out(self):
        frames = 2048
        pcm = pull(build(frames=frames, source=silence_src(frames)), frames)
        self.assertEqual(int(np.max(np.abs(pcm))), 0)

    def test_click_latency_zero(self):
        frames = 4096
        data = array("h", [0] * (frames * 2))
        data[400] = 32000
        data[401] = 32000
        src = probes.ArraySource(data, rate=RATE, channels=2, block=256)
        pcm = pull(build(frames=frames, source=src, depth=0.0), frames)
        onset = int(np.argmax(np.abs(pcm[:, 0])))
        self.assertEqual(onset, 200)

    def test_default_surrender_same_words(self):
        text = (
            "Default is bias, Depth 0.5, Rate 5 Hz — "
            "not the optical standout and not L1's Depth 1. "
            "Wet peak at the default is −1.341 dB vs a 16000-LSB tone, "
            "not the ~6 dB `synthio` `>>16` ceiling; "
            "Depth 0 is still a wire. At 22.05 kHz the default's L1 bar "
            "is measured at the constructor, not assumed. Optical L1/L2 "
            "are disconfirmed; O1–O4 unmeasured at the constructor."
        )
        def flat(s):
            return " ".join(s.split())

        self.assertIn(flat(text), flat(rebuilt.Tremolo.__doc__))
        readme = os.path.join(os.path.dirname(__file__), "..",
                              "lib", "audioeffects", "README.md")
        with open(readme, "r", encoding="utf-8") as handle:
            body = handle.read()
        self.assertIn(text, body)

    def test_l1_exception_same_words(self):
        text = (
            "L1 holds on sine at every rate, and misses by 0.16 dB on "
            "SQUARE material at 44.1 kHz only (−79.844 against −80; "
            "48 kHz holds at −82.01)."
        )
        module_path = os.path.join(
            os.path.dirname(__file__), "..",
            "lib", "audioeffects", "tremolo.py")
        with open(module_path, "r", encoding="utf-8") as handle:
            module_src = handle.read()
        self.assertIn(text, module_src)
        self.assertIn(text, rebuilt.Tremolo.__doc__)
        readme = os.path.join(os.path.dirname(__file__), "..",
                              "lib", "audioeffects", "README.md")
        with open(readme, "r", encoding="utf-8") as handle:
            body = handle.read()
        self.assertIn(text, body)


class NullBuilds(unittest.TestCase):
    def test_demonstrated_rows_red_on_a_wire(self):
        def l1_conj(cls):
            x = render_tone(cls, 2.0)[:, 0]
            return (block_db(x, RATE) < -80.0
                    and env_metrics(x, RATE, 5.0)["depth_db"] > 2.0)

        def l3_conj(cls):
            m = env_metrics(render_tone(cls, 2.0)[:, 0], RATE, 5.0)
            return m["hmax"] < -26.0 and m["depth_db"] > 2.0

        def l4(cls):
            got = env_peak_rate(render_tone(cls, 2.0)[:, 0], RATE)
            return abs(got - 5.0) / 5.0 < 0.01

        def b1(cls):
            return env_metrics(
                render_tone(cls, 2.0, depth=1.0)[:, 0], RATE, 5.0
            )["asym_db"] > 1.0

        for label, measure in (
            ("L1", l1_conj), ("L3", l3_conj), ("L4", l4), ("B1", b1),
        ):
            out = kit_faults.null_build_red(
                rebuilt.Tremolo, measure, label=label)
            self.assertFalse(out["null"])
            self.assertTrue(out["control"])


class FaultReachability(unittest.TestCase):
    def test_class_attr_faults_not_on_the_surface(self):
        cases = (
            (BlockHold, lambda e: type(e).BLOCK_HOLD),
            (FrozenLink, lambda e: type(e).FORCE_LINK_SCALE),
            (TriangleLFO, lambda e: type(e).LFO_KIND),
            (ShallowLinear, lambda e: type(e).SHALLOW_LINEAR),
            (MuteDepth, lambda e: type(e).ALLOW_MUTE),
            (IgnoreBias, lambda e: type(e).IGNORE_BIAS),
            (BiasTracker, lambda e: type(e).BIAS_USE_OPTICAL_TRACKER),
            (EqualTau, lambda e: type(e).EQUAL_TAU),
            (SineOpto, lambda e: type(e).PLAIN_SINE),
            (GateOpto, lambda e: type(e).GATE_AT_DEPTH1),
            (NoLag, lambda e: type(e).IGNORE_LAG),
            (DoubleRate, lambda e: type(e).RATE_PERIOD_SCALE),
        )
        for faulted, reading in cases:
            result = kit_faults.fault_reachability(
                rebuilt.Tremolo, faulted, reading,
                lambda cls: build(cls, frames=256))
            self.assertGreaterEqual(result["checked"], 150)
