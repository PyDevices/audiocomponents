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

Fix round 1 (2026-09-27, after gate audit round 1): T2's pitch is read by a
local least-squares fit against the dossier's own law (787.5 / glide_ms,
written out here, never the class's `slew_of`), with a planted wrong Glide
law; T1 has a dry fault that shows below -6 dBFS; T5's compounding clause
has a measurement and an out-of-loop fault, and its out-stop fault is one
no position dials at any rate; every fault's reachability walk runs at
48, 44.1 and 22.05 kHz with a reading of what the node is handed (or what
the output does) at the position walked. The input ceiling, the Glide
round trip, a 0 bpm host and Repeat Tone's clamp at 22.05 kHz each have a
test beside a planted fault.

Fix round 2 (2026-09-27, after gate audit round 2): the input ceiling is
rendered over 20 s at -3.1 dBFS and shown red at the old -3.0; the Glide
readback survives a 7-bit round trip through `_component.macro_of`, beside
the round-2 seeding; a NaN or infinite tempo leaves Time on the knob,
beside the round-2 guard; T5's Tone-compounding fault `PostToneDelay` is
here and in the reachability walks; and T2's part of the knob the row no
longer claims (rising, strictly between Glide grid 1 and 2) is tested by a
float32 model of the node's walk and by rendered fractional positions.
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


class DryGainDelay(DigitalDelay):
    """T1 at every level the row names: the output +0.1 dB
    (`kit_faults.HiddenGain`, LEVEL's own fault). `OneLsbScale` is the
    identity below 16 384 LSB, so on the -20 and -40 dBFS materials only
    this one can go red."""

    NAME = 'DigitalDelay'

    def _build(self, *arguments, **options):
        DigitalDelay._build(self, *arguments, **options)
        self._output = kit_faults.HiddenGain(self._delay, 0.1)


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


class HalfGlideMsDelay(DigitalDelay):
    """T2: the Glide law wrong - the knob's milliseconds halved, so the node
    walks at twice the dossier's 787.5 / glide_ms. A measurement that took
    its law from the class's own `slew_of` could not see it."""

    NAME = 'DigitalDelay'

    def _glide_ms(self):
        return 0.5 * DigitalDelay._glide_ms(self)


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
    """Superseded at fix round 1, kept so the round-1 probes still import:
    Repeat Tone's top stop pre-warped from the clamped 16 kHz. At 22.05 kHz
    that is 6 183.7, exactly what Tone positions 111-126 hand the node, so
    the surface dials it there. `RawTopToneDelay` replaces it."""

    NAME = 'DigitalDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return nominal_damping_hz(self._hz(16000.0), self._sample_rate)
        return DigitalDelay._tone_damping(self, position)


class RawTopToneDelay(DigitalDelay):
    """T5's out stop: Repeat Tone's top stop hands the node the span's top
    corner, clamped below Nyquist, as a raw `damping_hz` (16 000 / 16 000 /
    10 804.5 at 48 / 44.1 / 22.05 kHz) instead of exactly 0. Every in-circuit
    position hands a pre-warped value, which is lower at every rate, so no
    position reaches it."""

    NAME = 'DigitalDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return self._hz(16000.0)
        return DigitalDelay._tone_damping(self, position)


class CornerShiftDelay(DigitalDelay):
    """T5's corner clauses: both filters pre-warped for a corner 15 % above
    the label. Both filters are out at the defaults, so it is inert there by
    design; it is read at the corner cells."""

    NAME = 'DigitalDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return 0.0
        corner = 1.15 * _component.macro_value(self._MACRO_RANGES[TONE_I],
                                               position)
        return nominal_damping_hz(self._hz(corner), self._sample_rate)

    def _cut_hz(self, position):
        if position <= 0.0:
            return 0.0
        corner = 1.15 * _component.macro_value(self._MACRO_RANGES[CUT_I],
                                               position)
        return dd.nominal_cut_hz(self._hz(corner), self._sample_rate)


class PostCutDelay(DigitalDelay):
    """T5's compounding clause: Repeat Cut moved out of the loop onto the
    output - the same one-pole, the same pre-warp, applied once. One pass
    is identical to the class; the repeats do not compound."""

    NAME = 'DigitalDelay'

    def _build(self, *arguments, **options):
        self._post = 0.0
        self._hp = [0.0, 0.0]
        DigitalDelay._build(self, *arguments, **options)
        self._output = _PostHighPass(self)

    def _cut_hz(self, position):
        self._post = DigitalDelay._cut_hz(self, position)
        return 0.0


class _PostHighPass:
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
        owner = self._owner
        result, data = audiocore.get_buffer(owner._delay)
        raw = bytes(data)
        if not raw or owner._post <= 0.0:
            return result, memoryview(raw)
        a = 1.0 - math.exp(-2.0 * math.pi * owner._post / owner._sample_rate)
        v = np.frombuffer(raw, dtype="<i2").astype(np.float64)
        channels = self.channel_count
        out = np.empty_like(v)
        for c in range(channels):
            state = owner._hp[c]
            column = v[c::channels]
            filtered = np.empty_like(column)
            for i in range(len(column)):
                state += a * (column[i] - state)
                filtered[i] = column[i] - state
            owner._hp[c] = state
            out[c::channels] = filtered
        out = np.clip(np.where(out >= 0, np.trunc(out + 0.5),
                               np.trunc(out - 0.5)), -32768, 32767)
        return result, memoryview(out.astype("<i2").tobytes())


class _PostLowPass(_PostHighPass):
    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        owner = self._owner
        result, data = audiocore.get_buffer(owner._delay)
        raw = bytes(data)
        if not raw or owner._post_lp <= 0.0:
            return result, memoryview(raw)
        a = 1.0 - math.exp(-2.0 * math.pi * owner._post_lp
                           / owner._sample_rate)
        v = np.frombuffer(raw, dtype="<i2").astype(np.float64)
        channels = self.channel_count
        out = np.empty_like(v)
        for c in range(channels):
            state = owner._lp[c]
            column = v[c::channels]
            filtered = np.empty_like(column)
            for i in range(len(column)):
                state += a * (column[i] - state)
                filtered[i] = state
            owner._lp[c] = state
            out[c::channels] = filtered
        out = np.clip(np.where(out >= 0, np.trunc(out + 0.5),
                               np.trunc(out - 0.5)), -32768, 32767)
        return result, memoryview(out.astype("<i2").tobytes())


class ZeroBpmDelay(DigitalDelay):
    """The round-1 reading of a host's tempo: 0 bpm read as 120 bpm, so a
    host that reports no tempo drags Time to 120 bpm's value."""

    NAME = 'DigitalDelay'

    def _synced_ms(self):
        transport, state = self._transport_state()
        if transport is _component.static_transport:
            return None
        bpm = float(state[2]) if state[2] else 120.0
        index = int(round(self._value(DIVISION_I)))
        index = min(len(dd.DIVISION_BEATS) - 1, max(0, index))
        return dd.DIVISION_BEATS[index] * 60000.0 / bpm


class JumpSeedGlideDelay(DigitalDelay):
    """The round-1 Glide seeding: a constructor Glide at or under 800 ms
    seeded at position 0, which the surface defines as the jump."""

    NAME = 'DigitalDelay'

    def _build(self, *arguments, **options):
        DigitalDelay._build(self, *arguments, **options)
        if self._macros[GLIDE_I] <= dd.GLIDE_FLOOR:
            self._macros[GLIDE_I] = 0.0


class NearZeroSeedGlideDelay(DigitalDelay):
    """The round-2 Glide seeding: a constructor Glide at or under 800 ms
    seeded at position 1e-9, just above the jump. A float host keeps it;
    it reads back as MIDI 1.27e-7, which any 7-bit path stores as 0."""

    NAME = 'DigitalDelay'

    def _build(self, *arguments, **options):
        DigitalDelay._build(self, *arguments, **options)
        if (self._glide_exact is not None and self._glide_exact > 0.0
                and self._glide_exact <= 800.0):
            self._macros[GLIDE_I] = 1e-9


class NanBpmDelay(DigitalDelay):
    """The round-2 tempo guard, `bpm <= 0.0`, which a NaN passes and an
    infinite tempo passes too: both drag Time to the bottom of the knob."""

    NAME = 'DigitalDelay'

    def _synced_ms(self):
        transport, state = self._transport_state()
        if transport is _component.static_transport:
            return None
        bpm = float(state[2] or 0.0)
        if bpm <= 0.0:
            return None
        index = int(round(self._value(DIVISION_I)))
        index = min(len(dd.DIVISION_BEATS) - 1, max(0, index))
        return dd.DIVISION_BEATS[index] * 60000.0 / bpm


class PostToneDelay(DigitalDelay):
    """T5's compounding clause, Tone half: Repeat Tone's one-pole low-pass
    moved out of the loop onto the output - the same pre-warped
    coefficient, applied once. One pass is identical to the class; the
    repeats do not compound, so T3's control stops darkening. (The
    re-refuter's fault, `digitaldelay_rerefute1_t5.py`, moved here at fix
    round 2.)"""

    NAME = 'DigitalDelay'

    def _build(self, *arguments, **options):
        self._post_lp = 0.0
        self._lp = [0.0, 0.0]
        DigitalDelay._build(self, *arguments, **options)
        self._output = _PostLowPass(self)

    def _tone_damping(self, position):
        self._post_lp = DigitalDelay._tone_damping(self, position)
        return 0.0


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


def laps_to_exact_zero(feedback, peak=32768.0):
    """Laps of the line after which no sample can be non-zero, on audiodsp
    v0.6.2 and later, at any Feedback below the node's 1.0.

    Rounding to nearest still bounds a lap's peak by x' <= f x + 0.5, so
    x_k <= f^k (peak - c) + c with c = 0.5 / (1 - f); and since audiodsp#154
    no lap can hand back a sample as large as the one it sent, so once the
    peak is at most floor(c) it takes at most floor(c) more laps to reach 0.
    The 1e-6 keeps a c that is a whole number in exact arithmetic (10 at
    0.95) from flooring one short in float, where the loop would never end.
    """
    c = 0.5 / (1.0 - feedback)
    stall = math.floor(c + 1e-6)
    laps = 0
    while peak >= stall + 1:
        peak = feedback * (peak - c) + c
        laps += 1
    return laps + int(stall)


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


def t1_quiet(cls, dbfs, rate=RATE, channels=2, **options):
    """WIRE over the first T - 1 frames on `noise_det` at `dbfs` peak: the
    row's quieter levels, where `OneLsbScale` cannot show."""
    options.setdefault("glide_ms", 4000.0)
    effect_probe = cls(silence_src(64, channels, rate), sample_rate=rate,
                       **options)
    frames_t = effect_probe._frames
    effect_probe.deinit()
    total = frames_t + 256
    data = probes.noise_det(frames=total, dbfs=dbfs, channels=channels)
    effect = cls(probes.ArraySource(data, rate=rate, channels=channels,
                                    block=BLOCK), sample_rate=rate, **options)
    out = pull(effect, total, channels)
    src = np.array(data, dtype=np.int16)
    window = (frames_t - 1) * channels
    differing = int(np.count_nonzero(out[:window] != src[:window]))
    return {"passed": differing == 0, "differing": differing,
            "peak": int(np.abs(src).max())}


def dossier_slew(glide_ms):
    """The dossier's section 6 Glide law, written out here and never taken
    from the class: 787.5 ms over `glide_ms`, pinned at 0.99, 0 the jump."""
    glide_ms = float(glide_ms)
    if glide_ms <= 0.0:
        return 0.0
    return min(0.99, 787.5 / glide_ms)


def glide_of_grid(grid):
    """The Glide knob's label at a grid position: log 800-8000 ms, grid 0
    the jump (dossier section 6)."""
    if grid <= 0:
        return 0.0
    return 800.0 * 10.0 ** (grid / 127.0)


def ls_hz(segment, rate):
    """The frequency whose sine, with a phase and a DC term, fits `segment`
    best in least squares. It reads only the samples it is given - the
    analytic signal's FFT reads the whole render, which is what failed on
    the near-stall rising cells - and it takes no law: the search starts
    at the segment's own spectral peak, walks in 10-cent steps until the
    minimum is inside the bracket, then narrows to 1 cent and a golden
    section."""
    seg = np.asarray(segment, dtype=np.float64)
    n = len(seg)
    t = np.arange(n) / float(rate)
    ones = np.ones(n)

    def residual(cents_off, base):
        f = base * 2.0 ** (cents_off / 1200.0)
        w = 2.0 * math.pi * f * t
        basis = np.stack([np.sin(w), np.cos(w), ones], axis=1)
        coef = np.linalg.lstsq(basis, seg, rcond=None)[0]
        return float(np.sum((seg - basis.dot(coef)) ** 2))

    pad = 1 << int(math.ceil(math.log(max(16 * n, 1 << 16), 2)))
    spec = np.abs(np.fft.rfft((seg - seg.mean()) * np.hanning(n), pad))
    spec[0] = 0.0
    base = max(float(np.argmax(spec)) * rate / pad, 5.0)
    centre = 0.0
    for _ in range(40):
        offsets = centre + np.arange(-300.0, 301.0, 10.0)
        errors = [residual(c, base) for c in offsets]
        k = int(np.argmin(errors))
        centre = float(offsets[k])
        if 0 < k < len(offsets) - 1:
            break
    offsets = centre + np.arange(-10.0, 10.5, 1.0)
    centre = float(offsets[int(np.argmin([residual(c, base)
                                          for c in offsets]))])
    lo, hi = centre - 1.0, centre + 1.0
    g = (math.sqrt(5.0) - 1.0) / 2.0
    a, b = hi - g * (hi - lo), lo + g * (hi - lo)
    fa, fb = residual(a, base), residual(b, base)
    for _ in range(30):
        if fa < fb:
            hi, b, fb = b, a, fa
            a = hi - g * (hi - lo)
            fa = residual(a, base)
        else:
            lo, a, fa = a, b, fb
            b = lo + g * (hi - lo)
            fb = residual(b, base)
    return base * 2.0 ** ((lo + hi) / 2400.0)


def t2_render(cls, rate, values, start_ms, target_ms, glide_ms, glide_grid,
              move_at, frames):
    source = array_src(values, 2, rate)
    effect = cls(source, sample_rate=rate, time_ms=start_ms, feedback=0.0,
                 mix=2.0, glide_ms=glide_ms)
    if glide_grid is not None:
        effect.set_macro(GLIDE_I, glide_grid)

    def move(frame):
        if target_ms is not None and frame == move_at:
            effect.set_macro(TIME_I, midi_of_ms(target_ms))

    return left(pull(effect, frames, 2, on_block=move), 2)


def t2_measure(cls, rate=RATE, glide_ms=3937.5, start_ms=200.0,
               target_ms=150.0, move_at=20480, glide_grid=None, level=12000):
    """T2's three clauses at one cell, against the dossier's own law.

    The law is w_s (1 - dD) with dD = 787.5 / (the Glide asked) - the
    constructor's `glide_ms`, or the knob's label at `glide_grid` - never
    the class's own `slew_of`. The walk's end is read off a ramp render of
    the same move (the node's float32 walk ends early, A8.1). Pitch: the
    least-squares frequency of the walk less a margin of min(400, walk/10)
    frames at each end; residual: the same fit 50-250 ms after the walk.
    No-step: the largest first difference in the walk against
    1.05 |1 - dD| x the unramped maximum, a gap past the ramp's end against
    the looser legitimate slope, and 2000 frames after against the unramped
    maximum. `body` is the walk's largest step outside its last block, so
    a staircase's one remainder jump at the end is reported apart."""
    asked = glide_ms if glide_grid is None else glide_of_grid(glide_grid)
    slew = dossier_slew(asked)
    falling = target_ms < start_ms
    ratio = (1.0 + slew) if falling else (1.0 - slew)
    nominal = (int(abs(target_ms - start_ms) / slew * rate / 1000.0)
               if slew > 0.0 else 0)
    frames = move_at + nominal + int(0.35 * rate) + 4096
    sine = sine_values(997.0, frames, rate, level)
    y = t2_render(cls, rate, sine, start_ms, target_ms, glide_ms, glide_grid,
                  move_at, frames)
    base = t2_render(cls, rate, sine, start_ms, None, glide_ms, glide_grid,
                     move_at, frames)
    d_base = float(np.abs(np.diff(base[move_at:])).max())
    k = max(1, -(-frames // 60000))
    ramp = [i // k - 30000 for i in range(frames)]
    r = t2_render(cls, rate, ramp, start_ms, target_ms, glide_ms, glide_grid,
                  move_at, frames)
    delay = np.arange(frames) - k * (r + 30000.0)
    target_frames = int(math.floor(target_ms * rate / 1000.0 + 0.5))
    short = np.where(np.abs(delay[move_at:] - target_frames) > 2 * k + 2)[0]
    end = move_at + (int(short.max()) + 1 if len(short) else 0)
    walked = end - move_at
    result = {"slew": slew, "ratio": ratio, "unramped": d_base,
              "walk_frames": walked, "nominal": nominal, "law": "dossier",
              "bar": 1.05 * ratio * d_base}
    if slew <= 0.0 or walked < 64 or end + 4096 > len(y):
        step = float(np.abs(np.diff(y[move_at - 1:move_at + 256])).max())
        result.update({"passed": False, "walk": step, "gap": step,
                       "after": step, "body": step, "end": None,
                       "bar_gap": result["bar"], "bar_after": result["bar"],
                       "pitch_cents": None, "residual_cents": None,
                       "why": "no walk read off the ramp"})
        return result
    a = move_at + walked // 10
    b = end - walked // 10
    result["slew_measured"] = (
        abs(float(np.polyfit(np.arange(a, b), delay[a:b], 1)[0]))
        if b - a > 10 else float("nan"))
    slack = 2 * k + 2
    margin = int(math.ceil((slack + (slack - 2) // 2) / slew)) + 2
    walk = float(np.abs(np.diff(y[move_at - 1:end + 1])).max())
    body = float(np.abs(np.diff(y[move_at - 1:max(move_at, end - BLOCK)
                                  + 1])).max())
    end_jump = float(np.abs(np.diff(y[max(move_at, end - BLOCK) - 1:
                                      end + 1])).max())
    gap = float(np.abs(np.diff(y[end:end + margin + 1])).max())
    after = float(np.abs(np.diff(y[end + margin:end + margin + 2000])).max())
    edge = min(400, walked // 10)
    window = walked - 2 * edge
    pitch = cents(ls_hz(y[move_at + edge:end - edge], rate)
                  / (997.0 * ratio))
    settled = end + margin
    residual = cents(ls_hz(y[settled + int(0.05 * rate):
                             settled + int(0.25 * rate)], rate) / 997.0)
    bar_gap = 1.05 * max(ratio, 1.0) * d_base
    bar_after = 1.05 * d_base
    passed = (abs(pitch) <= 10.0 and abs(residual) <= 1.0
              and walk <= result["bar"] and gap <= bar_gap
              and after <= bar_after)
    result.update({"passed": passed, "pitch_cents": pitch,
                   "residual_cents": residual, "walk": walk, "body": body,
                   "end": end_jump, "gap": gap, "after": after,
                   "bar_gap": bar_gap, "bar_after": bar_after,
                   "window": window})
    return result


def f32_walk_cents(rate, grids, start_ms=150.0, target_ms=200.0):
    """A float32 model of the node's slew walk (`current += slew`,
    `audiodsp_feedback_delay.c:408` / `:413` at v0.6.1), from `start_ms` to
    `target_ms` in whole frames, at the dossier's law for each Glide grid
    position in `grids`. Returns, per position, the cents the walk plays
    off the law, read over the walk's middle 80 % (gate audit round 2's
    model, `digitaldelay_audit2_f32scan.py`)."""
    grids = np.asarray(grids, dtype=np.float64)
    a = dd.whole_frames(start_ms, rate)
    b = dd.whole_frames(target_ms, rate)
    law = np.array([dossier_slew(glide_of_grid(g)) for g in grids])
    step = law.astype(np.float32)
    rising = b > a
    tgt = np.float32(b)
    start = np.full(len(grids), a, np.float32)

    def advance(c):
        if rising:
            return np.minimum((c + step).astype(np.float32), tgt)
        return np.maximum((c - step).astype(np.float32), tgt)

    n = np.zeros(len(grids), np.int64)
    c = start.copy()
    done = np.zeros(len(grids), bool)
    k = 0
    while not done.all():
        k += 1
        c = np.where(done, c, advance(c))
        newly = (~done) & (c == tgt)
        n[newly] = k
        done |= newly
    ia, ib = n // 10, n - n // 10
    c = start.copy()
    pa = np.zeros(len(grids))
    pb = np.zeros(len(grids))
    for k in range(1, int(n.max()) + 1):
        c = advance(c)
        pa[ia == k] = c[ia == k]
        pb[ib == k] = c[ib == k]
    eff = np.abs(pb - pa) / (ib - ia)
    ratio = (1.0 - eff) / (1.0 - law) if rising else (1.0 + eff) / (1.0 + law)
    return 1200.0 * np.log2(ratio)


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
    node_ms = effect._node_ms
    out = pull(effect, frames, channels)
    # The reference takes the class's whole-frame Time (12.5 ms is 551.25
    # frames at 44.1 kHz; the class lands it on 551, dossier section 6).
    reference = dd.audioecho.FeedbackDelay(
        sample_rate=rate, channel_count=channels, max_delay_ms=801.0,
        delay_ms=node_ms, feedback=0.6, mix=2.0)
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


def t5_compound(cls, rate=RATE, level=8192, settings=None, **options):
    """T5's compounding clause: the T3 burst at Feedback 0.8, Mix 2, Time
    350.0 ms; repeat 8's share of each band against repeat 1's, in dB, for
    20-100 Hz (the Cut clause's band), 100 Hz-1 kHz, 1-4 kHz and
    4 kHz-Nyquist."""
    n = int(rate * 50.0 / 1000.0)
    burst = np.round(np.random.RandomState(12345).uniform(-1.0, 1.0, n)
                     * level).astype(np.int16)
    opts = {"time_ms": 350.0, "feedback": 0.8, "mix": 2.0,
            "glide_ms": 4000.0}
    opts.update(options)
    frames_t = dd.whole_frames(350.0, rate)
    total = 9 * frames_t + n + rate // 10
    values = np.zeros(total, dtype=np.int16)
    values[:n] = burst
    effect = cls(array_src(values.tolist(), 2, rate), sample_rate=rate,
                 **opts)
    for index in sorted(settings or {}):
        effect.set_macro(index, settings[index])
    y = left(pull(effect, total, 2), 2)
    bands = ((20.0, 100.0), (100.0, 1000.0), (1000.0, 4000.0),
             (4000.0, rate / 2.0 + 1.0))

    def shares(segment):
        spec = np.abs(np.fft.rfft(segment)) ** 2
        freqs = np.fft.rfftfreq(len(segment), 1.0 / rate)
        total_energy = spec[freqs >= 20.0].sum()
        return [spec[(freqs >= lo) & (freqs < hi)].sum() / total_energy
                for lo, hi in bands]

    first = shares(y[frames_t:frames_t + n])
    eighth = shares(y[8 * frames_t:8 * frames_t + n])
    return {"last": [10.0 * math.log10(e / f) for e, f in zip(eighth, first)]}


def railed_samples(cls, dbfs, seconds=1.0, rate=RATE, **options):
    """The input ceiling's measurement: `noise_det` at `dbfs` peak, 48 kHz
    stereo; output samples on the int16 rail that are not on it in the
    source."""
    frames = int(seconds * rate)
    data = probes.noise_det(frames=frames, dbfs=dbfs, channels=2)
    effect = cls(probes.ArraySource(data, rate=rate, channels=2, block=BLOCK),
                 sample_rate=rate, **options)
    out = pull(effect, frames, 2).astype(np.int64)
    src = np.array(data, dtype=np.int64)
    rail = (out >= 32767) | (out <= -32768)
    return int(np.count_nonzero(rail & ~((src >= 32767) | (src <= -32768))))


# --------------------------------------------------------------------------
# Reachability: what the node is handed, or what the output does, at the
# position walked. The twin's `FeedbackDelay.set` is watched while a walk
# runs, so a reading sees the options the class actually handed over.


class NodeSpy:
    """While active, every `audioecho.FeedbackDelay.set` call records its
    options on the node: `_handed` (the latest value of each option) and
    `_writes` (each call's options, in order)."""

    def __enter__(self):
        node_class = dd.audioecho.FeedbackDelay
        original = node_class.set
        self._restore = (node_class, original)

        def watched(node, **options):
            if not hasattr(node, "_handed"):
                node._handed = {}
                node._writes = []
            node._handed.update(options)
            node._writes.append(dict(options))
            return original(node, **options)

        node_class.set = watched
        return self

    def __exit__(self, *exc):
        node_class, original = self._restore
        node_class.set = original
        return False


def copy_of(effect, source, **ctor):
    """A fresh instance of the same class on `source`, at `effect`'s macro
    positions."""
    other = type(effect)(source, sample_rate=effect._sample_rate, **ctor)
    for index in range(len(type(effect).MACRO_LABELS)):
        other.set_macro(index, effect.get_macro(index))
    return other


def read_dry_gain(effect):
    """The dry path's gain before the first repeat: a copy at these
    positions on a 256-frame full-scale ramp, least-squares out / in."""
    ramp = probes.ramp_fs(frames=256, channels=2)
    other = copy_of(effect, probes.ArraySource(
        ramp, rate=effect._sample_rate, channels=2, block=BLOCK))
    out = pull(other, 256, 2).astype(np.float64)
    src = np.array(ramp, dtype=np.float64)
    other.deinit()
    return round(float(np.dot(out, src) / np.dot(src, src)), 5)


def read_python_steps(effect):
    """How many times the node's `delay_ms` is written while eight blocks
    are pulled after one Time move, on a copy at these positions: the class
    writes it once, on the move; a Python-stepped Time writes it every
    block."""
    rate = effect._sample_rate
    other = copy_of(effect, silence_src(16 * BLOCK, 2, rate))
    pull(other, BLOCK, 2)
    time_now = other.get_macro(TIME_I)
    mark = len(other._delay._writes)
    other.set_macro(TIME_I, time_now + 32.0 if time_now < 64 else
                    time_now - 32.0)
    pull(other, 8 * BLOCK, 2)
    writes = sum(1 for w in other._delay._writes[mark:] if "delay_ms" in w)
    other.deinit()
    return writes


def read_landing_fraction(effect):
    """The handed delay's distance from a whole frame, landed the node's way
    (float32 `value * rate / 1000`, `audiodsp_feedback_delay.c:148`)."""
    ms = np.float32(effect._delay._handed["delay_ms"])
    frames = float(ms * np.float32(effect._sample_rate) / np.float32(1000.0))
    return round(abs(frames - round(frames)), 2)


def read_map_error(effect):
    """The handed delay's whole frames against the dossier's T4 law at the
    knob's own position."""
    rate = effect._sample_rate
    frames = int(math.floor(effect._delay._handed["delay_ms"] * rate / 1000.0
                            + 0.5))
    return frames - mapped_frames(effect._macros[TIME_I], rate)


def read_damping(effect):
    """The `damping_hz` handed to the node now."""
    return round(float(effect._delay._handed["damping_hz"]), 1)


def read_corner_ratios(effect):
    """Each filter's handed coefficient against the pre-warp of its label
    at the knob's position (1.0 at an out stop and wherever they agree)."""
    rate = effect._sample_rate
    handed = effect._delay._handed
    position = effect._macros[TONE_I]
    if position >= 1.0:
        tone = 1.0 if handed["damping_hz"] == 0.0 else 0.0
    else:
        label = 800.0 * 20.0 ** position
        tone = handed["damping_hz"] / nominal_damping_hz(effect._hz(label),
                                                         rate)
    position = effect._macros[CUT_I]
    if position <= 0.0:
        cut = 1.0 if handed["cut_hz"] == 0.0 else 0.0
    else:
        label = 20.0 * 20.0 ** position
        cut = handed["cut_hz"] / dd.nominal_cut_hz(effect._hz(label), rate)
    return (round(tone, 3), round(cut, 3))


def read_cut_placement(effect):
    """(the `cut_hz` handed to the loop, the high-pass applied outside it)."""
    return (round(float(effect._delay._handed["cut_hz"]), 3),
            round(float(getattr(effect, "_post", 0.0)), 3))


def read_tone_placement(effect):
    """(the `damping_hz` handed to the loop, the low-pass applied outside
    it)."""
    return (round(float(effect._delay._handed["damping_hz"]), 3),
            round(float(getattr(effect, "_post_lp", 0.0)), 3))


def read_slew_against_label(effect):
    """The `delay_slew` handed to the node against the dossier's law at the
    Glide the knob's label says (the constructor's exact value while the
    knob has not moved)."""
    handed = effect._delay._handed["delay_slew"]
    if effect._glide_exact is not None:
        asked = effect._glide_exact
    else:
        asked = glide_of_grid(127.0 * effect._macros[GLIDE_I])
    law = dossier_slew(asked)
    if law == 0.0:
        return 1.0 if handed == 0.0 else 0.0
    return round(handed / law, 4)


#: (name, fault, reading, constructor options for both builds). The corner
#: and compounding faults are built at their corner cells (Tone 7 kHz, Cut
#: 40 Hz), because both filters are out at the defaults.
REACH_WALKS = (
    ("DryScaledDelay", DryScaledDelay, read_dry_gain, {}),
    ("DryGainDelay", DryGainDelay, read_dry_gain, {}),
    ("StaircaseDelay", StaircaseDelay, read_python_steps, {}),
    ("HalfGlideMsDelay", HalfGlideMsDelay, read_slew_against_label, {}),
    ("HalfFrameDelay", HalfFrameDelay, read_landing_fraction, {}),
    ("LinearMapDelay", LinearMapDelay, read_map_error, {}),
    ("RawTopToneDelay", RawTopToneDelay, read_damping, {}),
    ("CornerShiftDelay", CornerShiftDelay, read_corner_ratios,
     {"tone_hz": 7000.0, "cut_hz": 40.0}),
    ("PostCutDelay", PostCutDelay, read_cut_placement, {"cut_hz": 40.0}),
    ("PostToneDelay", PostToneDelay, read_tone_placement,
     {"tone_hz": 7000.0}),
)


def reach(faulted, reading, rate, ctor):
    """`kit_faults.fault_reachability` at `rate`, the node watched."""
    def build(cls):
        return cls(silence_src(512, 2, rate), sample_rate=rate, **ctor)

    with NodeSpy():
        return kit_faults.fault_reachability(DigitalDelay, faulted, reading,
                                             build)


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
        result = t1_measure(DryGainDelay)
        self.assertFalse(result["passed"])

    def test_the_quieter_levels_have_a_fault_leg(self):
        # -20 and -40 dBFS: the clean class is a wire, OneLsbScale cannot
        # show there (it is the identity below 16 384 LSB), and the +0.1 dB
        # fault does.
        for dbfs in (-20.0, -40.0):
            self.assertTrue(t1_quiet(DigitalDelay, dbfs)["passed"], dbfs)
            self.assertEqual(t1_quiet(DryScaledDelay, dbfs)["differing"], 0)
            self.assertGreater(t1_quiet(DryGainDelay, dbfs)["differing"], 0)


class T2TimeResamples(unittest.TestCase):
    def test_the_row_cell_falls_on_the_law(self):
        result = t2_measure(DigitalDelay)
        self.assertTrue(result["passed"], result)
        self.assertLess(abs(result["pitch_cents"]), 10.0)

    def test_a_rising_move_at_the_default_glide(self):
        result = t2_measure(DigitalDelay, glide_ms=4000.0, start_ms=150.0,
                            target_ms=200.0)
        self.assertTrue(result["passed"], result)

    def test_a_near_stall_rising_cell(self):
        # Glide grid 2, 150 -> 200 ms: the law's ratio is 0.051 (a 50 Hz
        # tone, 1.7 cycles in the window). The analytic-signal median read
        # -15.00 c here; the least-squares fit reads the node.
        result = t2_measure(DigitalDelay, glide_grid=2, start_ms=150.0,
                            target_ms=200.0)
        self.assertTrue(result["passed"], result)

    def test_the_constructor_800_ms_cell(self):
        result = t2_measure(DigitalDelay, glide_ms=800.0)
        self.assertTrue(result["passed"], result)

    def test_a_wrong_glide_law_is_red(self):
        result = t2_measure(HalfGlideMsDelay)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["pitch_cents"], 200.0)

    def test_the_block_staircase_is_red(self):
        result = t2_measure(StaircaseDelay, glide_ms=4000.0)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["body"], result["bar"])

    def test_the_unclaimed_band_is_where_the_float32_walk_says(self):
        # Fix round 2 (dossier section 8.11): the rising move is not claimed
        # strictly between Glide grid 1 and grid 2. The float32 model of the
        # node's walk, over the whole knob in steps of 0.01, puts every
        # position more than 10 c off the law inside that band at every
        # rate, and does find some there at 48 kHz (so the scan can fail).
        grids = np.arange(100, 12701) / 100.0
        for rate in (48000, 44100, 22050):
            off = grids[np.abs(f32_walk_cents(rate, grids)) > 10.0]
            self.assertTrue(np.all((off > 1.0) & (off < 2.0)),
                            (rate, off[(off <= 1.0) | (off >= 2.0)]))
            if rate == 48000:
                self.assertGreater(len(off), 0)
        falling = f32_walk_cents(48000, grids, 200.0, 150.0)
        self.assertLess(float(np.abs(falling).max()), 10.0)

    def test_inside_the_band_is_red_and_outside_it_holds(self):
        # Grid 1.245 is the model's worst position at 48 kHz: rendered, it
        # reads about -15 c. Fractional positions outside the band pass.
        inside = t2_measure(DigitalDelay, glide_grid=1.245, start_ms=150.0,
                            target_ms=200.0)
        self.assertLess(inside["pitch_cents"], -10.0, inside)
        for rate, grid in ((48000, 2.05), (48000, 3.55), (44100, 1.95),
                           (22050, 1.245)):
            result = t2_measure(DigitalDelay, rate=rate, glide_grid=grid,
                                start_ms=150.0, target_ms=200.0)
            self.assertTrue(result["passed"], (rate, grid, result))


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
        for rate in (48000, 44100, 22050):
            self.assertEqual(t5_out_identical(DigitalDelay, rate), 0, rate)
            self.assertGreater(t5_out_identical(RawTopToneDelay, rate), 0,
                               rate)
        self.assertFalse(t5_measure(RawTopToneDelay)["passed"])

    def test_the_corners_shifted_are_red(self):
        # 15 % high puts the 7 kHz corner at 8 050 Hz, so 7 700 Hz is still
        # less than 3 dB down, and the 40 Hz corner at 46 Hz.
        result = t5_measure(CornerShiftDelay)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["tone"][7700], -3.0)

    def test_the_cut_compounds_in_the_loop(self):
        # Repeat Cut at its 400 Hz stop, Feedback 0.8: repeat 8's 20-100 Hz
        # share at least 6 dB under repeat 1's (the fix round's bar, dated
        # in the dossier); moved out of the loop it does not compound.
        for rate in (48000, 22050):
            clean = t5_compound(DigitalDelay, rate, settings={CUT_I: 127})
            self.assertLessEqual(clean["last"][0], -6.0, (rate, clean))
            post = t5_compound(PostCutDelay, rate, settings={CUT_I: 127})
            self.assertGreater(post["last"][0], -1.0, (rate, post))

    def test_the_tone_compounds_in_the_loop(self):
        # T3's control is the Tone half of the compounding clause: Repeat
        # Tone 3 kHz takes repeat 8's 4 kHz-Nyquist share at least 20 dB
        # under repeat 1's. Moved out of the loop it does not compound.
        for rate in (48000, 44100, 22050):
            clean = t3_measure(DigitalDelay, rate=rate, tone_hz=3000.0)
            self.assertLessEqual(clean["high8"], -20.0, (rate, clean))
            post = t3_measure(PostToneDelay, rate=rate, tone_hz=3000.0)
            self.assertGreater(post["high8"], -1.0, (rate, post))


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

    def test_the_floor_is_gone_at_feedback_half(self):
        # Up to audiodsp v0.6.1 the node rounded the feedback write to
        # nearest, so from Feedback 0.5 a 1 LSB repeat wrote itself back
        # forever: on this material 1 LSB was still going round after three
        # seconds. v0.6.2 (audiodsp#154) truncates the fed-back term toward
        # zero exactly where rounding would hand it back unchanged, so the
        # largest sample on the line falls by at least 1 LSB a lap and, from
        # full scale, by the geometric bound until then
        # (`laps_to_exact_zero`). The tail therefore ends inside that many
        # laps of at most one frame past the 600-frame Time (measured at
        # v0.6.2: silent 8 748 frames after the input, bound 9 616). The class
        # still says None here: its declaration is DigitalDelay's re-audit
        # to change, not this pin move's.
        values = [0] * 256 + sine_values(997.0, 2048, RATE, 12000)
        input_end = len(values)
        values += [0] * (3 * RATE)
        effect = DigitalDelay(array_src(values), sample_rate=RATE,
                              time_ms=12.5, feedback=0.5, mix=2.0)
        self.assertIsNone(effect.tail_samples)
        out = pull(effect, len(values))
        bound = laps_to_exact_zero(0.5) * (600 + 1)
        nonzero = np.nonzero(out)[0]
        self.assertGreater(len(nonzero), 0)
        last = int(nonzero[-1]) // 2
        self.assertLessEqual(last - input_end, bound,
                             "the tail ran %d frames past the input, "
                             "over the %d-frame bound"
                             % (last - input_end, bound))
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
# Fix round 1: the audit's (o) items and the 0 bpm host


class InputCeiling(unittest.TestCase):
    """The docstring's ceiling on `noise_det`, 48 kHz stereo, over 20 s:
    the defaults clean at -3.1 dBFS peak, patch 3 (the first shipped patch
    to rail) at -4. Fix round 2: 1 s could not see the defaults rail at the
    old -3.0 dBFS (4 samples over 20 s, the first at frame 169 739), so the
    render is 20 s and -3.0 is the red leg."""

    SECONDS = 20.0

    def test_the_stated_ceiling_is_clean_and_just_over_is_not(self):
        for options, ceiling, over in (({}, -3.1, -3.0),
                                       ({"patch": 3}, -4.0, -3.0)):
            self.assertEqual(railed_samples(DigitalDelay, ceiling,
                                            self.SECONDS, **options), 0,
                             options)
            self.assertGreater(railed_samples(DigitalDelay, over,
                                              self.SECONDS, **options), 0,
                               options)

    def test_the_any_material_bound(self):
        # A DC one LSB under floor(32767 (1 - Mix)) never reaches the rail
        # at Feedback 0.99; at floor(32767 (1 - Mix)) itself the sum rounds
        # onto 32767 (the docstring says so: nothing clips).
        for mix in (0.5, 0.3):
            edge = int(math.floor(32767 * (1.0 - mix)))
            for level, railed in ((edge - 1, False), (edge, mix == 0.5)):
                values = [level] * (RATE // 2)
                effect = DigitalDelay(array_src(values), sample_rate=RATE,
                                      time_ms=12.5, feedback=0.99, mix=mix)
                out = pull(effect, len(values))
                self.assertEqual(bool(np.any(out >= 32767)), railed,
                                 (mix, level))


class GlideRoundTrip(unittest.TestCase):
    def _round_trip(self, cls, glide_ms):
        effect = cls(silence_src(512), sample_rate=RATE, glide_ms=glide_ms)
        before = dd.slew_of(effect._glide_ms())
        effect.set_macro(GLIDE_I, effect.get_macro(GLIDE_I))
        return before, dd.slew_of(effect._glide_ms())

    def test_get_macro_hands_back_the_glide(self):
        # A constructor Glide faster than grid 1 reads back as grid 1, so a
        # float trip lands the knob's fastest walk (0.966689; from 500 ms's
        # pinned 0.99 that is -2.36 %, the most the knob can hold).
        for glide_ms in (500.0, 800.0, 4000.0):
            before, after = self._round_trip(DigitalDelay, glide_ms)
            self.assertGreater(before, 0.0)
            self.assertLessEqual(abs(after / before - 1.0), 0.025, glide_ms)
        effect = DigitalDelay(silence_src(512), sample_rate=RATE,
                              glide_ms=0.0)
        self.assertEqual(effect.get_macro(GLIDE_I), 0.0)

    def test_the_jump_seed_is_red(self):
        before, after = self._round_trip(JumpSeedGlideDelay, 800.0)
        self.assertGreater(before, 0.9)
        self.assertEqual(after, 0.0)

    def _seven_bit_trip(self, cls, glide_ms):
        """The Glide knob stored as a 7-bit value, the way a patch author
        or a MIDI host stores it (`_component.macro_of` of `macro(3)`), and
        handed back."""
        effect = cls(silence_src(512), sample_rate=RATE, glide_ms=glide_ms)
        before = dd.slew_of(effect._glide_ms())
        midi = _component.macro_of(cls._MACRO_RANGES[GLIDE_I],
                                   effect.macro(GLIDE_I))
        effect.set_macro(GLIDE_I, midi)
        return before, midi, dd.slew_of(effect._glide_ms())

    def test_a_seven_bit_trip_keeps_the_glide(self):
        grid_1 = dossier_slew(glide_of_grid(1))
        for glide_ms in (500.0, 800.0, 810.0, 4000.0):
            before, midi, after = self._seven_bit_trip(DigitalDelay,
                                                       glide_ms)
            self.assertGreater(after, 0.0, glide_ms)
            if before > grid_1:
                # Faster than the grid can hold: grid 1, the fastest walk.
                self.assertEqual(midi, 1, glide_ms)
                self.assertAlmostEqual(after, 0.966689, places=6)
            else:
                self.assertLessEqual(abs(after / before - 1.0), 0.02,
                                     glide_ms)
        for glide_ms in (500.0, 800.0):
            _, midi, after = self._seven_bit_trip(NearZeroSeedGlideDelay,
                                                  glide_ms)
            self.assertEqual((midi, after), (0, 0.0), glide_ms)


class ZeroBpmHost(unittest.TestCase):
    def test_a_tempo_that_is_not_finite_leaves_time_on_the_knob(self):
        # Fix round 2: NaN and infinity passed the round-2 guard
        # (`bpm <= 0.0`) and landed Time at 12.5 ms (600 frames).
        for bpm in (float("nan"), float("inf"), float("-inf")):
            def transport(_bpm=bpm):
                return (True, 0.0, _bpm, 4, 4)
            measured, _ = t4_delay(DigitalDelay, transport=transport,
                                   sync=127, division=51, time_ms=350.0)
            self.assertLessEqual(abs(measured - 16800), 1.0, bpm)
            measured, _ = t4_delay(NanBpmDelay, transport=transport,
                                   sync=127, division=51, time_ms=350.0)
            if bpm > 0.0 or bpm != bpm:
                self.assertLessEqual(abs(measured - 600), 1.0, bpm)

    def test_no_tempo_leaves_time_on_the_knob(self):
        for bpm in (0.0, None):
            def transport(_bpm=bpm):
                return (True, 0.0, _bpm, 4, 4)
            measured, _ = t4_delay(DigitalDelay, transport=transport,
                                   sync=127, division=51, time_ms=350.0)
            self.assertLessEqual(abs(measured - 16800), 1.0, bpm)
            measured, _ = t4_delay(ZeroBpmDelay, transport=transport,
                                   sync=127, division=51, time_ms=350.0)
            self.assertLessEqual(abs(measured - 12000), 1.0, bpm)


class RepeatToneKnee(unittest.TestCase):
    """Repeat Tone's clamp: at 22.05 kHz positions 111-126 sit on the
    10 804.5 Hz ceiling and 127 is out; at 44.1 and 48 kHz every position
    moves."""

    def _dampings(self, rate):
        effect = DigitalDelay(silence_src(64, 2, rate), sample_rate=rate)
        return [effect._tone_damping(p / 127.0) for p in range(128)]

    def test_the_knee(self):
        values = self._dampings(22050)
        self.assertLess(values[110], values[111])
        self.assertEqual(len(set(values[111:127])), 1)
        self.assertEqual(values[127], 0.0)
        for rate in (48000, 44100):
            values = self._dampings(rate)
            self.assertTrue(all(b > a for a, b in zip(values[:126],
                                                      values[1:127])), rate)
            self.assertEqual(values[127], 0.0)


# --------------------------------------------------------------------------
# The two checks every planted fault and every row is held to


class FaultsAreUnreachable(unittest.TestCase):
    """Every fault's reachability walk, at 48, 44.1 and 22.05 kHz, reading
    what the node is handed (or what the output does) at each position."""

    CHECKED = 8 * 17 + 6

    def test_every_fault_is_off_the_surface_at_three_rates(self):
        for rate in (48000, 44100, 22050):
            for name, faulted, reading, ctor in REACH_WALKS:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, ctor)
                    self.assertEqual(result["checked"], self.CHECKED)

    def test_the_old_out_stop_fault_is_dialled_at_22k(self):
        with self.assertRaises(kit_faults.FaultReachable):
            reach(OpenTopToneDelay, read_damping, 22050, {})


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
