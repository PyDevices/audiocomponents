"""`DigitalDelay`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/DigitalDelay.md`
(frozen at anchor 51207b8); its Tier 2 rows are T1-T5. Each row here is the
measurement at a few of the row's cells and the same measurement shown red
on a planted fault of the same kind, at the constructor defaults. Every
fault is shown unreachable from every macro position and shipped patch, and
every row's measurement is shown red on the class built as a wire. The full
spans, the three interpreters and the rates live in the evidence pack, not
in this file.

The rebuild is parked (not in `rebuilt.ADOPTED`), so the class is reached by
`rebuilt.module_class("DigitalDelay")`.
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
import kit_probes as probes                                 # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import rebuilt                            # noqa: E402
from audioeffects.chorus import nominal_damping_hz          # noqa: E402
from audioeffects.rebuilt import digitaldelay as dd         # noqa: E402
from tools import effect_measurements as kit                # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
BLOCK = 256
TIME_I, FEEDBACK_I, MIX_I, GLIDE_I, SYNC_I, DIVISION_I, TONE_I, CUT_I = \
    range(8)

DigitalDelay = rebuilt.module_class("DigitalDelay")


def midi_of_ms(time_ms):
    """Time's MIDI position for `time_ms`, unquantised."""
    return 127.0 * math.log(time_ms / 12.5) / math.log(64.0)


def mapped_frames(position, rate):
    """The dossier's T4 law, written out independently of the class:
    12.5 * 64^position ms, landed on the nearest whole frame."""
    time_ms = 12.5 * 64.0 ** position
    return int(math.floor(time_ms * rate / 1000.0 + 0.5))


# --------------------------------------------------------------------------
# Planted faults, one per Tier 2 row, each of the row's own kind


class DryScaledDelay(DigitalDelay):
    """T1: the dry path coloured - the output scaled by 32767/32768, one
    LSB above -6 dBFS (`kit_faults.OneLsbScale`, WIRE's own fault)."""

    NAME = 'DigitalDelay'

    def _build(self, *arguments, **options):
        DigitalDelay._build(self, *arguments, **options)
        self._plant_dry_scale = True
        self._output = kit_faults.OneLsbScale(self._delay)


class _Stepper:
    """Pulls the owner's node, stepping its delay from Python first: the
    finest a Python-driven Time can move is once per block."""

    def __init__(self, owner):
        self._owner = owner
        node = owner._delay
        self.sample_rate = node.sample_rate
        self.channel_count = node.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        audiocore.reset_buffer(self._owner._delay)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        self._owner._step()
        return audiocore.get_buffer(self._owner._delay,
                                    single_channel_output, audio_channel)


class StaircaseDelay(DigitalDelay):
    """T2: route (b), A8.8 - `delay_ms` stepped from Python once per
    256-frame block with the node's slew off, at the rate the Glide asks
    for. No macro position reaches it: Glide grid 0 is one jump, and every
    other position is the node's own per-frame walk."""

    NAME = 'DigitalDelay'

    def _build(self, *arguments, **options):
        self._current_ms = None
        DigitalDelay._build(self, *arguments, **options)
        self._output = _Stepper(self)

    def _refresh(self):
        DigitalDelay._refresh(self)
        if self._current_ms is None:
            self._current_ms = self._node_ms
        slew = dd.slew_of(self._glide_ms())
        self._step_per_block = slew * BLOCK * 1000.0 / self._sample_rate
        self._delay.set(delay_slew=0.0, delay_ms=self._current_ms)

    def _step(self):
        target = self._node_ms
        step = self._step_per_block
        current = self._current_ms
        if current == target:
            return
        if step <= 0.0 or abs(target - current) <= step:
            current = target
        elif target > current:
            current += step
        else:
            current -= step
        self._current_ms = current
        self._delay.set(delay_ms=current)


class HalfFrameDelay(DigitalDelay):
    """T3: Time handed to the node half a frame off the whole frame, so the
    read interpolator takes the top of the band down on every pass - the
    per-pass loss the whole-frame law designs out."""

    NAME = 'DigitalDelay'

    def _node_time_ms(self, frames):
        return (frames + 0.5) * 1000.0 / self._sample_rate


class LinearMapDelay(DigitalDelay):
    """T4: the Time map linear in the macro instead of log - the same knob
    position means different milliseconds than the stated law."""

    NAME = 'DigitalDelay'

    def _time_map(self, position):
        return 12.5 + 787.5 * position


class OpenTopToneDelay(DigitalDelay):
    """T5: Repeat Tone's top stop pre-warped to a large number instead of
    exactly 0, so the default is not out of circuit."""

    NAME = 'DigitalDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return nominal_damping_hz(self._hz(16000.0), self._sample_rate)
        return DigitalDelay._tone_damping(self, position)


# --------------------------------------------------------------------------
# Planted faults for the Tier 1 checks the review round added


class SixtyDbTailDelay(DigitalDelay):
    """The first build's tail: the -60 dB lap count plus one lap, which a
    -6 dBFS burst outlives on its way down to exact zero."""

    NAME = 'DigitalDelay'

    @property
    def tail_samples(self):
        frames = self._frames
        if self._feedback <= 0.0:
            return int(frames)
        laps = 1.0 + 3.0 * math.log(10.0) / -math.log(self._feedback)
        return int(math.ceil(frames * laps))


class TargetOnlyTailDelay(DigitalDelay):
    """The tail from the target Time alone, while the read head is still
    walking down from the old one."""

    NAME = 'DigitalDelay'

    def _refresh(self):
        DigitalDelay._refresh(self)
        self._reach = self._frames


class PerMacroPatchDelay(DigitalDelay):
    """A patch applied one macro at a time with a refresh after each, so
    Time is read against the outgoing patch's Sync."""

    NAME = 'DigitalDelay'
    program_change = _component.Component.program_change


# --------------------------------------------------------------------------
# Sources and pulls


def array_src(values, channels=2, rate=RATE):
    data = array("h")
    for value in values:
        for _ in range(channels):
            data.append(int(value))
    return probes.ArraySource(data, rate=rate, channels=channels, block=BLOCK)


def silence_src(frames, channels=2, rate=RATE):
    return probes.ArraySource(array("h", [0] * (frames * channels)),
                              rate=rate, channels=channels, block=BLOCK)


def sine_values(hz, frames, rate, level):
    return [int(round(level * math.sin(2.0 * math.pi * hz * n / rate)))
            for n in range(frames)]


def pull(effect, frames, channels=None, on_block=None):
    """Interleaved int16 of `frames` frames; `on_block(frame)` runs before
    each block is pulled."""
    channels = channels or effect.channel_count
    out = array("h")
    while len(out) < frames * channels:
        if on_block is not None:
            on_block(len(out) // channels)
        data = bytes(audiocore.get_buffer(effect.output)[1])
        if not data:
            out.extend([0] * (frames * channels - len(out)))
            break
        out.extend(memoryview(data).cast("h"))
    return np.array(out[:frames * channels], dtype=np.int16)


def left(interleaved, channels):
    return interleaved[0::channels].astype(np.float64)


def inst_hz(x, rate):
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    spec = np.fft.fft(x)
    h = np.zeros(n)
    h[0] = 1.0
    if n % 2 == 0:
        h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[1:(n + 1) // 2] = 2.0
    phase = np.unwrap(np.angle(np.fft.ifft(spec * h)))
    return np.diff(phase) * rate / (2.0 * math.pi)


def cents(ratio):
    return 1200.0 * math.log(ratio) / math.log(2.0)


# --------------------------------------------------------------------------
# The measurements, each returning {"passed": ...}


def t1_measure(cls, rate=RATE, channels=2, **options):
    """WIRE over the first T - 1 frames on the full-scale ramp, and the
    first repeat arriving in the 64 frames after, where Mix is above 0."""
    options.setdefault("glide_ms", 4000.0)
    effect_probe = cls(silence_src(64, channels, rate), sample_rate=rate,
                       **options)
    frames_t = effect_probe._frames
    mix = effect_probe.macro(MIX_I)
    effect_probe.deinit()
    total = max(8192, frames_t + 512)
    ramp = probes.ramp_fs(frames=total, channels=channels)
    source = probes.ArraySource(ramp, rate=rate, channels=channels,
                                block=BLOCK)
    effect = cls(source, sample_rate=rate, **options)
    out = pull(effect, total, channels)
    src = np.array(ramp, dtype=np.int16)
    window = (frames_t - 1) * channels
    differing = int(np.count_nonzero(out[:window] != src[:window]))
    after = slice(frames_t * channels, (frames_t + 64) * channels)
    arrived = int(np.count_nonzero(out[after] != src[after]))
    passed = differing == 0 and (mix <= 0.0 or arrived > 0)
    return {"passed": passed, "differing": differing, "arrived": arrived,
            "frames": frames_t}


def t2_render(cls, rate, glide_ms, start_ms, target_ms, move_at=20480):
    slew = dd.slew_of(glide_ms)
    nominal = 0
    if target_ms is not None and slew > 0.0:
        nominal = int(abs(target_ms - start_ms) / slew * rate / 1000.0)
    frames = move_at + nominal + int(0.3 * rate)
    source = array_src(sine_values(997.0, frames, rate, 12000), 2, rate)
    effect = cls(source, sample_rate=rate, time_ms=start_ms, feedback=0.0,
                 mix=2.0, glide_ms=glide_ms)

    def move(frame):
        if target_ms is not None and frame == move_at:
            effect.set_macro(TIME_I, midi_of_ms(target_ms))

    out = left(pull(effect, frames, 2, on_block=move), 2)
    return out, nominal


def t2_measure(cls, rate=RATE, glide_ms=3937.5, start_ms=200.0,
               target_ms=150.0, move_at=20480):
    """The wet pitch against w_s (1 - dD) during the walk, the residual
    50-250 ms after it, and the no-step clause in three windows: the walk
    (less a 128-frame margin, inside which the node's float32 walk ends;
    A8.1 reads it ending up to 105 frames early) against the signed bar
    |1 - dD| x the unramped maximum, the margin against the looser of the
    two legitimate slopes, and the frames after against the unramped
    maximum, each with 5 % for phase sampling."""
    slew = dd.slew_of(glide_ms)
    y, nominal = t2_render(cls, rate, glide_ms, start_ms, target_ms, move_at)
    base, _ = t2_render(cls, rate, glide_ms, start_ms, None, move_at)
    d_base = float(np.abs(np.diff(base[move_at:])).max())
    falling = target_ms < start_ms
    ratio = (1.0 + slew) if falling else (1.0 - slew)
    end = move_at + nominal
    walk = float(np.abs(np.diff(y[move_at - 1:end - 128 + 1])).max())
    gap = float(np.abs(np.diff(y[end - 128:end + 64 + 1])).max())
    after = float(np.abs(np.diff(y[end + 64:end + 64 + 2000])).max())
    hz = inst_hz(y, rate)
    during = float(np.median(hz[move_at + 400:end - 400]))
    residual = float(np.median(hz[end + int(0.05 * rate):
                                  end + int(0.25 * rate)]))
    pitch_error = cents(during / (997.0 * ratio))
    residual_error = cents(residual / 997.0)
    passed = (abs(pitch_error) <= 10.0 and abs(residual_error) <= 1.0
              and walk <= 1.05 * ratio * d_base
              and gap <= 1.05 * max(ratio, 1.0) * d_base
              and after <= 1.05 * d_base)
    return {"passed": passed, "pitch_cents": pitch_error,
            "residual_cents": residual_error, "walk": walk, "gap": gap,
            "after": after, "unramped": d_base,
            "bar": 1.05 * ratio * d_base}


def t3_burst(rate):
    n = int(rate * 50.0 / 1000.0)
    rng = np.random.RandomState(12345)
    return np.round(rng.uniform(-1.0, 1.0, n) * 8192).astype(np.int16)


def t3_shares(segment, rate):
    spec = np.abs(np.fft.rfft(segment)) ** 2
    freqs = np.fft.rfftfreq(len(segment), 1.0 / rate)
    total = spec[freqs >= 20.0].sum()
    bands = ((100.0, 1000.0), (1000.0, 4000.0), (4000.0, rate / 2.0))
    if total <= 0.0:
        return None
    return [spec[(freqs >= lo) & (freqs < hi)].sum() / total
            for lo, hi in bands]


def t3_measure(cls, rate=RATE, tone_hz=16000.0, **options):
    """Burst then silence at Feedback 0.8, Mix 2: each repeat's band shares
    against repeat 1's, through repeat 8. Returns the worst deviation per
    band and repeat 8's 4 kHz-Nyquist share against repeat 1's."""
    options.setdefault("time_ms", 350.0)
    burst = t3_burst(rate)
    probe = cls(silence_src(64, 2, rate), sample_rate=rate, **options)
    frames_t = probe._frames
    probe.deinit()
    total = 9 * frames_t + len(burst) + rate // 10
    values = np.zeros(total, dtype=np.int16)
    values[:len(burst)] = burst
    effect = cls(array_src(values.tolist(), 2, rate), sample_rate=rate,
                 feedback=0.8, mix=2.0, tone_hz=tone_hz, cut_hz=20.0,
                 glide_ms=4000.0, **options)
    y = left(pull(effect, total, 2), 2)
    rows = []
    for k in range(1, 9):
        segment = y[k * frames_t:k * frames_t + len(burst)]
        if float(np.sqrt(np.mean(segment ** 2))) < 1.0:
            return {"passed": False, "why": "repeat %d is silent" % k}
        shares = t3_shares(segment, rate)
        if shares is None or min(shares) <= 0.0:
            return {"passed": False, "why": "repeat %d has no band" % k}
        rows.append(shares)
    worst = [max(abs(10.0 * math.log10(row[i] / rows[0][i])) for row in rows)
             for i in range(3)]
    high8 = 10.0 * math.log10(rows[7][2] / rows[0][2])
    return {"passed": max(worst) <= 1.0, "worst": worst, "high8": high8,
            "frames": frames_t}


def t4_delay(cls, rate=RATE, transport=None, midi=None, division=None,
             sync=None, **options):
    """The wet click's landing in frames: one full-scale sample at frame
    1000, Mix 2, Feedback 0, Glide 0 (an instant knob)."""
    at = 1000
    frames = at + int(0.81 * rate) + 512
    values = [0] * frames
    values[at] = 32767
    source = array_src(values, 2, rate)
    if transport is None:
        effect = cls(source, sample_rate=rate, feedback=0.0, mix=2.0,
                     glide_ms=0.0, **options)
    else:
        effect = cls.create(source, rate, transport=transport, feedback=0.0,
                            mix=2.0, glide_ms=0.0, **options)
    if sync is not None:
        effect.set_macro(SYNC_I, sync)
    if division is not None:
        effect.set_macro(DIVISION_I, division)
    if midi is not None:
        effect.set_macro(TIME_I, midi)
    y = np.abs(left(pull(effect, frames, 2), 2))
    peak = int(np.argmax(y))
    lo, hi = max(0, peak - 2), min(len(y), peak + 3)
    centroid = float(np.dot(np.arange(lo, hi), y[lo:hi]) / y[lo:hi].sum())
    return centroid - at, effect.get_macro(TIME_I)


def t4_measure(cls, rate=RATE, positions=None):
    """Delay tracking against the stated law's whole frame, within one
    sample; with no positions, at the constructor's own 350 ms."""
    if positions is None:
        measured, _ = t4_delay(cls, rate, time_ms=350.0)
        expected = int(math.floor(350.0 * rate / 1000.0 + 0.5))
        errors = [abs(measured - expected)]
    else:
        errors = []
        for k in positions:
            measured, _ = t4_delay(cls, rate, midi=127.0 * k / 16.0)
            errors.append(abs(measured - mapped_frames(k / 16.0, rate)))
    return {"passed": max(errors) <= 1.0, "worst": max(errors)}


def t5_gain_db(cls, hz, rate=RATE, window_s=0.25, **options):
    """One pass, wet only, Time 350.0 ms: the tone's magnitude against the
    class's own filters-out render at the same Time and rate."""
    frames_t = int(math.floor(350.0 * rate / 1000.0 + 0.5))
    total = frames_t + int(window_s * rate) + int(0.05 * rate)
    values = sine_values(hz, total, rate, 8192)

    def magnitude(**opts):
        effect = cls(array_src(values, 2, rate), sample_rate=rate,
                     time_ms=350.0, feedback=0.0, mix=2.0, glide_ms=4000.0,
                     **opts)
        y = left(pull(effect, total, 2), 2)
        n = int(window_s * rate)
        segment = y[-n:]
        t = np.arange(n) / float(rate)
        return abs(np.sum(segment * np.exp(-2j * math.pi * hz * t))) * 2.0 / n

    wet = magnitude(**options)
    ref = magnitude()
    return 20.0 * math.log10(max(wet, 1e-9) / max(ref, 1e-9))


def t5_out_identical(cls, rate=RATE, channels=2):
    """The class at both filter stops (its defaults) against a node given
    neither filter option, on deterministic noise: byte for byte."""
    frames = 8192
    noise = probes.noise_det(frames=frames, channels=channels)
    effect = cls(probes.ArraySource(noise, rate=rate, channels=channels,
                                    block=BLOCK),
                 sample_rate=rate, time_ms=12.5, feedback=0.6, mix=2.0)
    out = pull(effect, frames, channels)
    reference = dd.audioecho.FeedbackDelay(
        sample_rate=rate, channel_count=channels, max_delay_ms=801.0,
        delay_ms=12.5, feedback=0.6, mix=2.0)
    reference.play(probes.ArraySource(noise, rate=rate, channels=channels,
                                      block=BLOCK))
    ref = array("h")
    while len(ref) < frames * channels:
        data = bytes(audiocore.get_buffer(reference)[1])
        if not data:
            break
        ref.extend(memoryview(data).cast("h"))
    ref = np.array(ref[:frames * channels], dtype=np.int16)
    return int(np.count_nonzero(out != ref))


def t5_measure(cls, rate=RATE):
    """Repeat Tone 7 kHz: -3 dB inside 6.3-7.7 kHz, no more than 3 dB down
    at 5 kHz, more than 3 dB down at 10 kHz; Repeat Cut 40 Hz: -3 dB inside
    36-44 Hz; both out-of-circuit stops byte-identical to filters-out."""
    tone = {hz: t5_gain_db(cls, hz, rate, tone_hz=7000.0)
            for hz in (5000, 6300, 7700, 10000)}
    cut = {hz: t5_gain_db(cls, hz, rate, cut_hz=40.0) for hz in (36, 44)}
    differing = t5_out_identical(cls, rate)
    passed = (tone[6300] > -3.0 > tone[7700] and tone[5000] >= -3.0
              and tone[10000] < -3.0 and cut[36] < -3.0 < cut[44]
              and differing == 0)
    return {"passed": passed, "tone": tone, "cut": cut,
            "differing": differing}


# --------------------------------------------------------------------------
# The surface


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = DigitalDelay
        self.assertEqual(cls.MACRO_LABELS,
                         ("Time", "Feedback", "Mix", "Glide", "Sync",
                          "Division", "Repeat Tone", "Repeat Cut"))
        self.assertEqual(len(cls.PATCHES), 6)
        self.assertEqual(cls.CAPABILITIES, ("tempo_sync",))
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TIER, _component.AUDIODSP)
        self.assertEqual(cls.REQUIRES, ("audioecho",))
        effect = cls(silence_src(512), sample_rate=RATE)
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.capabilities, ("tempo_sync",))
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(0, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)

    def test_parked_not_served(self):
        import audioeffects
        self.assertNotIn("DigitalDelay", rebuilt.ADOPTED)
        self.assertIn("DigitalDelay", rebuilt.parked())
        self.assertIsNot(audioeffects.DigitalDelay, DigitalDelay)

    def test_patch_0_is_the_constructor_grid(self):
        effect = DigitalDelay(silence_src(512), sample_rate=RATE)
        grid = DigitalDelay.PATCHES[0][1]
        for index, expected in enumerate(grid):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_tail_samples_follows_time_and_feedback(self):
        # laps_to_zero(f) laps of (the head's longest delay + 1) frames.
        self.assertEqual(dd.laps_to_zero(0.0), 1)
        self.assertEqual(dd.laps_to_zero(0.35), 12)
        self.assertEqual(dd.laps_to_zero(64 / 127.0 * 0.99), 24)
        self.assertIsNone(dd.laps_to_zero(0.5))
        effect = DigitalDelay(silence_src(512), sample_rate=RATE)
        self.assertEqual(effect.tail_samples, 12 * 16801)
        effect.program_change(0)
        self.assertEqual(effect.tail_samples, 12 * 16936)
        effect.set_macro(FEEDBACK_I, 0)
        self.assertEqual(effect.tail_samples, 16936)
        # A falling move walks from the old Time, so the old Time stays the
        # bound until a jump lands the head.
        effect.set_macro(TIME_I, 0)
        self.assertEqual(effect.tail_samples, 16936)
        effect.set_macro(GLIDE_I, 0)
        self.assertEqual(effect.tail_samples, 601)
        effect.set_macro(FEEDBACK_I, 64)
        self.assertEqual(effect.tail_samples, 24 * 601)
        effect.set_macro(TONE_I, 100)
        self.assertEqual(effect.tail_samples, 25 * 601)
        effect.set_macro(FEEDBACK_I, 65)
        self.assertIsNone(effect.tail_samples)
        effect.set_macro(FEEDBACK_I, 0)
        effect.set_macro(CUT_I, 1)
        self.assertIsNone(effect.tail_samples)
        effect.reset()
        self.assertEqual(effect.tail_samples, 12 * 16936)

    def test_glide_law(self):
        self.assertEqual(dd.slew_of(0.0), 0.0)
        self.assertAlmostEqual(dd.slew_of(3937.5), 0.2)
        self.assertAlmostEqual(dd.slew_of(4000.0), 0.196875)
        self.assertEqual(dd.slew_of(500.0), 0.99)
        effect = DigitalDelay(silence_src(512), sample_rate=RATE,
                              glide_ms=800.0)
        self.assertAlmostEqual(dd.slew_of(effect._glide_ms()), 0.984375)
        effect.set_macro(GLIDE_I, 1)
        self.assertAlmostEqual(dd.slew_of(effect._glide_ms()), 0.96669,
                               places=5)
        effect.set_macro(GLIDE_I, 0)
        self.assertEqual(effect._glide_ms(), 0.0)
        effect.set_macro(GLIDE_I, 127)
        self.assertAlmostEqual(effect._glide_ms(), 8000.0)

    def test_filter_stops_are_exactly_zero(self):
        effect = DigitalDelay(silence_src(512), sample_rate=RATE)
        self.assertEqual(effect._tone_damping(1.0), 0.0)
        self.assertEqual(effect._cut_hz(0.0), 0.0)
        self.assertAlmostEqual(dd.nominal_cut_hz(40.0, 48000), 39.7916,
                               places=3)
        self.assertAlmostEqual(dd.nominal_cut_hz(400.0, 44100), 378.3309,
                               places=3)


# --------------------------------------------------------------------------
# Tier 2 rows


class T1DryIsAWire(unittest.TestCase):
    def test_defaults_stereo_and_mono(self):
        for channels in (2, 1):
            result = t1_measure(DigitalDelay, channels=channels)
            self.assertTrue(result["passed"], (channels, result))
            self.assertEqual(result["frames"], 16800)

    def test_the_hardest_cells(self):
        for rate in (48000, 22050):
            for mix in (0.9921, 1.0):
                result = t1_measure(DigitalDelay, rate=rate, time_ms=12.5,
                                    feedback=0.99, mix=mix, tone_hz=800.0,
                                    cut_hz=400.0)
                self.assertTrue(result["passed"], (rate, mix, result))

    def test_a_coloured_dry_is_red(self):
        result = t1_measure(DryScaledDelay)
        self.assertFalse(result["passed"])
        self.assertGreater(result["differing"], 0)


class T2TimeResamples(unittest.TestCase):
    def test_the_row_cell_falls_on_the_law(self):
        result = t2_measure(DigitalDelay)
        self.assertTrue(result["passed"], result)
        self.assertLess(abs(result["pitch_cents"]), 10.0)

    def test_a_rising_move_at_the_default_glide(self):
        result = t2_measure(DigitalDelay, glide_ms=4000.0, start_ms=150.0,
                            target_ms=200.0)
        self.assertTrue(result["passed"], result)

    def test_the_block_staircase_is_red(self):
        result = t2_measure(StaircaseDelay, glide_ms=4000.0)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["walk"], result["bar"])


class T3NoDarkening(unittest.TestCase):
    def test_the_constructor_time_at_48k_and_22k(self):
        for rate, frames in ((48000, 16800), (22050, 7718)):
            result = t3_measure(DigitalDelay, rate=rate)
            self.assertTrue(result["passed"], (rate, result))
            self.assertEqual(result["frames"], frames)

    def test_the_control_darkens(self):
        result = t3_measure(DigitalDelay, tone_hz=3000.0)
        self.assertLessEqual(result["high8"], -20.0, result)

    def test_a_half_frame_read_is_red(self):
        result = t3_measure(HalfFrameDelay)
        self.assertFalse(result["passed"], result)


class T4TimeLaw(unittest.TestCase):
    def test_the_map_at_the_stops_and_between(self):
        result = t4_measure(DigitalDelay, positions=(0, 4, 8, 12, 16))
        self.assertTrue(result["passed"], result)
        result = t4_measure(DigitalDelay, rate=22050, positions=(0, 16))
        self.assertTrue(result["passed"], result)

    def test_a_lowered_ceiling_clamps_visibly(self):
        measured, reported = t4_delay(DigitalDelay, midi=127.0,
                                      max_time_ms=300.0)
        self.assertLessEqual(abs(measured - 14400), 1.0)
        self.assertAlmostEqual(reported, 97.048, places=3)
        measured, reported = t4_delay(DigitalDelay, midi=64.0,
                                      max_time_ms=300.0)
        self.assertLessEqual(abs(measured - mapped_frames(64 / 127.0, RATE)),
                             1.0)
        self.assertAlmostEqual(reported, 64.0, places=6)

    def test_sync_quantises_time_into_the_map(self):
        def transport():
            return (True, 0.0, 120.0, 4, 4)
        for division, frames, reported in ((0, 3000, None),
                                           (51, 12000, None),
                                           (127, 38400, 127.0)):
            measured, got = t4_delay(DigitalDelay, transport=transport,
                                     sync=127, division=division)
            self.assertLessEqual(abs(measured - frames), 1.0, division)
            if reported is not None:
                self.assertAlmostEqual(got, reported, places=6)

    def test_no_host_leaves_time_on_the_knob(self):
        measured, _ = t4_delay(DigitalDelay, sync=127, division=0,
                               time_ms=350.0)
        self.assertLessEqual(abs(measured - 16800), 1.0)

    def test_a_linear_map_is_red(self):
        self.assertTrue(t4_measure(DigitalDelay)["passed"])
        self.assertFalse(t4_measure(LinearMapDelay)["passed"])


class T5BandLimit(unittest.TestCase):
    def test_the_corners_at_48k(self):
        result = t5_measure(DigitalDelay)
        self.assertTrue(result["passed"], result)

    def test_the_in_circuit_stops(self):
        self.assertAlmostEqual(
            t5_gain_db(DigitalDelay, 800, tone_hz=800.0), -3.01, delta=0.2)
        self.assertAlmostEqual(
            t5_gain_db(DigitalDelay, 400, cut_hz=400.0), -3.01, delta=0.2)

    def test_an_open_top_stop_is_red(self):
        self.assertGreater(t5_out_identical(OpenTopToneDelay), 0)
        self.assertFalse(t5_measure(OpenTopToneDelay)["passed"])


# --------------------------------------------------------------------------
# Tier 1, the fast half


class Tier1Fast(unittest.TestCase):
    def test_mix_zero_is_a_wire_on_the_full_scale_ramp(self):
        for rate in (48000, 44100, 22050):
            for channels in (2, 1):
                ramp = probes.ramp_fs(frames=8192, channels=channels)
                source = probes.ArraySource(ramp, rate=rate,
                                            channels=channels, block=BLOCK)
                effect = DigitalDelay(source, sample_rate=rate, mix=0.0,
                                      time_ms=12.5, feedback=0.99)
                out = pull(effect, 8192, channels)
                self.assertTrue(np.array_equal(
                    out, np.array(ramp, dtype=np.int16)), (rate, channels))

    def test_silence_stays_silence(self):
        effect = DigitalDelay(silence_src(RATE), sample_rate=RATE,
                              feedback=0.99, mix=2.0, tone_hz=800.0,
                              cut_hz=400.0)
        self.assertEqual(int(np.max(np.abs(pull(effect, RATE)))), 0)

    def _kit_tail(self, cls, seconds, **options):
        data, on = probes.burst_silence(total_s=seconds, rate=RATE)
        effect = cls(probes.ArraySource(data, rate=RATE, channels=2,
                                        block=BLOCK),
                     sample_rate=RATE, **options)
        declared = effect.tail_samples
        render = probes.render(effect, int(seconds * RATE), rate=RATE,
                               channels=2)
        result = kit.tail(render, burst_end_frame=on,
                          declared_tail_samples=declared,
                          settle_frames=effect._frames)
        return declared, result["values"], result["red"]

    def test_the_tail_reaches_exact_zero_inside_tail_samples(self):
        # The kit's TAIL on its own -6 dBFS burst, at the defaults and at
        # the Sync-on patch with the highest Feedback under 0.5.
        for options, seconds in (({}, 5.0), ({"patch": 2}, 6.0)):
            declared, values, red = self._kit_tail(DigitalDelay, seconds,
                                                   **options)
            self.assertEqual(red, [], (options, values))
            self.assertLessEqual(values["tail_samples"], declared)
        declared, values, red = self._kit_tail(SixtyDbTailDelay, 5.0)
        self.assertNotEqual(red, [], values)
        self.assertGreater(values["tail_samples"], declared)

    def test_the_floor_bug_is_reported_as_unbounded(self):
        # audiodsp v0.6.1 rounds the feedback write half away from zero, so
        # from Feedback 0.5 a 1 LSB repeat writes itself back forever. The
        # class says None there. When the node is fixed the residual below
        # goes to 0, and tail_samples can come back for the top half.
        values = [0] * 256 + sine_values(997.0, 2048, RATE, 12000)
        values += [0] * (3 * RATE)
        effect = DigitalDelay(array_src(values), sample_rate=RATE,
                              time_ms=12.5, feedback=0.5, mix=2.0)
        self.assertIsNone(effect.tail_samples)
        out = pull(effect, len(values))
        self.assertGreater(int(np.max(np.abs(out[-600 * 2:]))), 0)
        effect.set_macro(FEEDBACK_I, 64)
        self.assertIsNotNone(effect.tail_samples)

    def _walk_tail(self, cls):
        """800 ms of 997 Hz, then Time 800 -> 12.5 ms at the default Glide
        on the tone's last block, Feedback 0, Mix 2."""
        tone = int(0.8 * RATE) // BLOCK * BLOCK
        values = sine_values(997.0, tone, RATE, 12000) + [0] * RATE
        effect = cls(array_src(values), sample_rate=RATE, time_ms=800.0,
                     feedback=0.0, mix=2.0)
        seen = {}

        def move(frame):
            if frame == tone:
                effect.set_macro(TIME_I, 0)
                seen["declared"] = effect.tail_samples

        out = pull(effect, len(values), on_block=move)
        after = out[tone * 2:]
        last = int(np.nonzero(after)[0][-1]) // 2 + 1
        return seen["declared"], last

    def test_a_falling_walk_keeps_the_old_time_in_the_tail(self):
        declared, last = self._walk_tail(DigitalDelay)
        self.assertGreater(last, 30000)
        self.assertLessEqual(last, declared)
        declared, last = self._walk_tail(TargetOnlyTailDelay)
        self.assertGreater(last, declared)

    def _patch_times(self, cls):
        def transport():
            return (True, 0.0, 120.0, 4, 4)
        effect = cls.create(silence_src(512), RATE, transport=transport)
        seen = []
        effect.program_change(1)
        effect.program_change(0)
        seen.append((effect._frames, round(effect.get_macro(TIME_I), 3)))
        effect.program_change(1)
        effect.program_change(4)
        seen.append((effect._frames, round(effect.get_macro(TIME_I), 3)))
        effect.program_change(2)
        effect.reset()
        seen.append((effect._frames, round(effect.get_macro(TIME_I), 3),
                     effect.patch_index))
        return seen

    def test_a_sync_off_patch_loads_its_own_time(self):
        # 120 bpm: patch 1's synced Time is 12000 frames (1/8), patch 2's
        # 18000 (1/8 dotted).
        self.assertEqual(self._patch_times(DigitalDelay),
                         [(16935, 102.0), (35966, 125.0),
                          (16935, 102.0, 0)])
        faulted = self._patch_times(PerMacroPatchDelay)
        self.assertEqual([row[0] for row in faulted], [12000, 12000, 18000])

    def test_reset_empties_the_line(self):
        values = [0] * 256 + sine_values(997.0, 2048, RATE, 12000)
        values += [0] * RATE
        effect = DigitalDelay(array_src(values), sample_rate=RATE,
                              time_ms=100.0, feedback=0.9, mix=2.0)
        pull(effect, 2304)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(int(np.max(np.abs(pull(effect, RATE // 2)))), 0)

    def test_deinit_leaves_the_source(self):
        source = array_src(sine_values(440.0, 1024, RATE, 8000))
        effect = DigitalDelay(source, sample_rate=RATE)
        pull(effect, 256)
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(source)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)

    def test_click_delay_is_zero(self):
        values = [0] * 2048
        values[10] = 30000
        effect = DigitalDelay(array_src(values), sample_rate=RATE)
        out = left(pull(effect, 2048), 2)
        self.assertEqual(int(np.argmax(np.abs(out))), 10)
        self.assertEqual(effect.latency_samples, 0)

    def test_the_transport_is_read_only_with_sync_on(self):
        reads = []

        def transport():
            reads.append(1)
            return (True, 0.0, 120.0, 4, 4)
        effect = DigitalDelay.create(silence_src(512), RATE,
                                     transport=transport)
        self.assertEqual(reads, [])
        effect.set_macro(SYNC_I, 127)
        self.assertGreater(len(reads), 0)


# --------------------------------------------------------------------------
# The two checks every planted fault and every row is held to


class FaultsAreUnreachable(unittest.TestCase):
    CHECKED = 8 * 17 + 6

    def _reach(self, faulted, reading):
        return kit_faults.fault_reachability(
            DigitalDelay, faulted, reading,
            lambda cls: cls(silence_src(512), sample_rate=RATE))

    def test_every_fault_is_off_the_surface(self):
        for faulted, reading, expected in (
                (DryScaledDelay,
                 lambda e: getattr(e, "_plant_dry_scale", False), True),
                (StaircaseDelay,
                 lambda e: round(getattr(e, "_step_per_block", 0.0), 6),
                 round(0.196875 * BLOCK * 1000.0 / RATE, 6)),
                (HalfFrameDelay,
                 lambda e: round(abs(e._node_ms * e._sample_rate / 1000.0
                                     - round(e._node_ms * e._sample_rate
                                             / 1000.0)), 6), 0.5),
                (LinearMapDelay, lambda e: round(e._time_map(0.5), 6),
                 406.25),
                (OpenTopToneDelay, lambda e: round(e._tone_damping(1.0), 3),
                 round(nominal_damping_hz(16000.0, RATE), 3))):
            with self.subTest(fault=faulted.__name__):
                result = self._reach(faulted, reading)
                self.assertEqual(result["target"], expected)
                self.assertEqual(result["checked"], self.CHECKED)


class NullBuildRed(unittest.TestCase):
    """Every demonstrated row goes red on the class built as a wire, beside
    a control on the real class that must pass."""

    def test_every_row_is_red_on_a_wire(self):
        for name, measure in (
                ("T1", t1_measure),
                ("T2", t2_measure),
                ("T3", t3_measure),
                ("T4", lambda cls: t4_measure(cls, positions=(0, 8, 16))),
                ("T5", t5_measure)):
            with self.subTest(row=name):
                result = kit_faults.null_build_red(
                    DigitalDelay, measure, label="DigitalDelay %s" % name)
                self.assertFalse(result["null"]["passed"], name)
                self.assertTrue(result["control"]["passed"], name)


if __name__ == "__main__":
    unittest.main()
