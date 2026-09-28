"""`AnalogDelay`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/AnalogDelay.md`
(frozen at anchor cc61011, the Station A critique revision, with the
post-build revision of 2026-09-28 in its section 8: T3's inside no-step bar
carries the loop low-pass's memory, the walk is read where the head lands,
the binade pieces have a resolvable minimum, and T7's arrival clause is
claimed across Mix's interior material by material). Four of its
Tier 2 rows can be demonstrated, T2a, T3, T6 and T7, and each is here as
the measurement at a few of the row's cells beside the same measurement
shown red on the row's planted fault at the constructor defaults. Every
fault is shown unreachable from every macro position and shipped patch at
48, 44.1 and 22.05 kHz, and every row's measurement is shown red on the
class built as a wire. T1 is unmeasured and T2b, T4 and T5 are disconfirmed
by decision; `RecordedRows` holds the numbers their verdicts rest on, so a
build that gained a hold or a fixed pair would show up here first. The
full spans, the stereo renders the rows name, the three interpreters and
the M5 table live in the evidence pack, not in this file.

The rebuild is parked (not in `rebuilt.ADOPTED`), so the class is reached by
`rebuilt.module_class("AnalogDelay")`.

The dossier's laws are written out here independently of the class: the
corner is 0.2211 N / T, the Time map 20 * 30^position ms, the whole frame
floor(ms fs / 1000 + 0.5), and a Time move's walk rate |dT| / T_new.
"""

import math
import os
import sys
import unittest
import wave
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
from audioeffects.rebuilt import analogdelay as ad          # noqa: E402
from tools import effect_measurements as kit                # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
RATES = (48000, 44100, 22050)
BLOCK = 256
TIME_I, FEEDBACK_I, MIX_I, MODULATION_I, RATE_I, SPREAD_I, SYNC_I, \
    DIVISION_I = range(8)
SINGLE, DOUBLE = "single-line", "double-line"
STAGES = {SINGLE: 4096, DOUBLE: 8192}

AnalogDelay = rebuilt.module_class("AnalogDelay")

PROBE_DIR = os.path.join(os.path.dirname(__file__), "..", "tools",
                         "effect_probes")


# --------------------------------------------------------------------------
# The dossier's laws, written out independently of the class


def law_corner(character, time_ms):
    """0.2211 N / T, T the knob's milliseconds (dossier T2a)."""
    return 0.2211 * STAGES[character] / (time_ms / 1000.0)


def whole(time_ms, rate):
    """The nearest whole frame at the running rate (dossier section 6)."""
    return int(math.floor(time_ms * rate / 1000.0 + 0.5))


def grid_ms(midi):
    """Time's map: 20-600 ms, log, at MIDI position `midi`."""
    return 20.0 * 30.0 ** (midi / 127.0)


def midi_of_ms(time_ms):
    """Time's MIDI position for `time_ms`, unquantised."""
    return 127.0 * math.log(time_ms / 20.0) / math.log(30.0)


def clamp_hz(hz, rate):
    return min(max(hz, 1.0), rate * 0.5 * 0.98)


def first_claimed(character, rate):
    """The first Time grid position where the corner law is under the
    clamp (dossier T2a, Quantified over)."""
    for midi in range(128):
        if law_corner(character, grid_ms(midi)) < rate * 0.5 * 0.98:
            return midi
    return None


def cents(ratio):
    return 1200.0 * math.log(ratio) / math.log(2.0)


# --------------------------------------------------------------------------
# Planted faults, one or more per demonstrated row, each of the row's kind


class CornerN6144(AnalogDelay):
    """T2a: the corner law run on N = 6144 on both characters. N is the
    character, not a macro, so no position or patch reaches it."""

    NAME = 'AnalogDelay'

    def _corner_for(self, time_ms):
        return ad.corner_hz(6144, time_ms)


class DoubleLineN6144(AnalogDelay):
    """T6: double-line's corner law run on N = 6144, single-line's
    untouched."""

    NAME = 'AnalogDelay'

    def _corner_for(self, time_ms):
        if self._character == DOUBLE:
            return ad.corner_hz(6144, time_ms)
        return AnalogDelay._corner_for(self, time_ms)


class JumpAnalogDelay(AnalogDelay):
    """T3: the move as one jump (slew 0), which has no walk at all."""

    NAME = 'AnalogDelay'

    def _walk_rate(self, from_frames, to_frames):
        return 0.0


class ConstantGlideWalk(AnalogDelay):
    """T3: DigitalDelay's constant walk at its Glide 800 ms (slew 787.5 /
    800) in place of the clock's law."""

    NAME = 'AnalogDelay'

    def _walk_rate(self, from_frames, to_frames):
        return 787.5 / 800.0


class UnflooredWalk(AnalogDelay):
    """Section 6: the clock's law with no floor. A slew under half a
    single-precision step of the head's position rounds away in the node's
    walk, so a small move never lands."""

    NAME = 'AnalogDelay'

    def _walk_rate(self, from_frames, to_frames):
        return ad.clock_slew(from_frames, to_frames)


class _ReadStep(kit_faults._Node):
    """A node in the path that, from frame `step_at` on, plays its source
    `frames` frames late: the read stepping back that far, once, and
    staying there."""

    def __init__(self, source, frames):
        kit_faults._Node.__init__(self, source)
        self.frames = int(frames)
        self.pulled = 0
        self.step_at = None
        self._history = np.zeros(self.frames * self.channel_count)

    def _process(self, block):
        channels = self.channel_count
        count = len(block) // channels
        joined = np.concatenate([self._history, block])
        late = joined[:len(block)]
        self._history = joined[len(block):]
        out = block.copy()
        if self.step_at is not None:
            start = max(0, self.step_at - self.pulled)
            if start < count:
                out[start * channels:] = late[start * channels:]
        self.pulled += count
        return out


class MidWalkReadStep(AnalogDelay):
    """T3's no-step clause: halfway through a Time move's walk the read
    steps 8 frames late, once, and walks on from there. Nothing the surface
    reaches puts a step in the walk: every Time move is one constant-rate
    walk (section 6)."""

    NAME = 'AnalogDelay'
    STEP_FRAMES = 8

    def _build(self, *arguments, **options):
        AnalogDelay._build(self, *arguments, **options)
        self._step = _ReadStep(self._delay, self.STEP_FRAMES)
        self._output = self._step

    def _refresh(self):
        before, fresh = self._frames, self._fresh
        AnalogDelay._refresh(self)
        step = getattr(self, "_step", None)
        if (step is not None and not fresh and self._frames != before
                and self._slew > 0.0):
            walk = abs(self._frames - before) / self._slew
            step.step_at = step.pulled + int(walk // 2)


class DryGainDelay(AnalogDelay):
    """T7: the output +0.1 dB (`kit_faults.HiddenGain`), a dry above
    unity, which nothing reaches: the node's dry is exactly 1 below Mix 1."""

    NAME = 'AnalogDelay'

    def _build(self, *arguments, **options):
        AnalogDelay._build(self, *arguments, **options)
        self._output = kit_faults.HiddenGain(self._delay, 0.1)


class PlainHandOff(AnalogDelay):
    """Section 6's hand-off: `k * 1000 / fs` as DigitalDelay hands it,
    which the node's single-precision arithmetic lands a frame short at
    some counts (patch 0's Time at 44.1 kHz)."""

    NAME = 'AnalogDelay'

    def _node_time_ms(self, frames):
        return frames * 1000.0 / self._sample_rate


class SpreadInMono(AnalogDelay):
    """Section 4: Spread passed to the node at one channel."""

    NAME = 'AnalogDelay'

    def _refresh(self):
        AnalogDelay._refresh(self)
        spread = self._value(SPREAD_I)
        self._spread = spread
        self._delay.set(cross_feed=spread)


class TargetOnlyTail(AnalogDelay):
    """Tail: sized on the target Time only, forgetting that a falling walk
    starts from the old one."""

    NAME = 'AnalogDelay'

    def _refresh(self):
        AnalogDelay._refresh(self)
        self._reach = self._frames


class NoSwingTail(AnalogDelay):
    """Tail: the modulation's swing left out of the reach."""

    NAME = 'AnalogDelay'

    def _tail_bound(self):
        memory, excess = ad.tone_excess(self._damping, self._sample_rate)
        laps = ad.laps_to_zero(self._feedback, excess)
        return int(laps * (self._reach + 1 + memory))


class HalfTail(AnalogDelay):
    """Tail: half the bound."""

    NAME = 'AnalogDelay'

    def _tail_bound(self):
        return AnalogDelay._tail_bound(self) // 2


class RawFeedback(AnalogDelay):
    """Tail: the Feedback handed as set, inside a stall window."""

    NAME = 'AnalogDelay'

    def _refresh(self):
        AnalogDelay._refresh(self)
        feedback = min(0.99, self._value(FEEDBACK_I))
        self._feedback = feedback
        self._delay.set(feedback=feedback)


class PerMacroPatch(AnalogDelay):
    """A patch applied one macro at a time, refreshing after each."""

    NAME = 'AnalogDelay'

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        _component.Component.program_change(self, index, channel, note_id,
                                            sample_position)


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


def sine_values(hz, frames, rate, level, phase=0.0):
    n = np.arange(frames)
    return np.round(level * np.sin(2.0 * math.pi * hz * n / rate
                                   + phase)).astype(np.int64).tolist()


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


def material(name, rate, channels):
    path = os.path.join(PROBE_DIR, str(rate), "%dch" % channels,
                        name + ".wav")
    handle = wave.open(path)
    try:
        data = handle.readframes(handle.getnframes())
    finally:
        handle.close()
    return array("h", data)


def analytic(x):
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
    return np.fft.ifft(spec * h)


def inst_hz(x, rate):
    phase = np.unwrap(np.angle(analytic(x)))
    return np.diff(phase) * rate / (2.0 * math.pi)


# --------------------------------------------------------------------------
# T2a / T6: the first repeat's -3 dB corner


def first_repeat(cls, rate, character, time_ms=None, midi=None,
                 amp=32767, frames=8192, **options):
    """Mix 2, Feedback 0, one impulse of `amp` at frame 0; the first
    repeat's samples from its whole-frame arrival, scaled to a unit
    impulse. Time from the constructor (`time_ms`) or the grid (`midi`)."""
    if midi is not None:
        time_ms = grid_ms(midi)
    arrival = whole(time_ms, rate)
    total = arrival + frames
    values = [0] * total
    values[0] = amp
    effect = cls(array_src(values, 1, rate), sample_rate=rate,
                 character=character, feedback=0.0, mix=2.0,
                 time_ms=time_ms, **options)
    if midi is not None:
        effect.set_macro(TIME_I, midi)
    out = left(pull(effect, total, 1), 1)
    effect.deinit()
    return out[arrival:] / float(amp)


def magnitude_db(h, rate, hz):
    k = np.arange(len(h))
    value = abs(np.dot(h, np.exp(-2j * math.pi * hz / rate * k)))
    return 20.0 * math.log10(max(value, 1e-15))


def crossing_hz(h, rate, level_db=-3.0103, low=10.0):
    """The first frequency where |H| falls through `level_db`, by
    bisection on the exact DTFT, or `None` where it never does below
    0.999 x Nyquist (a wire's empty first repeat, or no corner)."""
    high = rate * 0.5 * 0.999
    if not np.any(h):
        return None
    if magnitude_db(h, rate, high) > level_db:
        return None
    if magnitude_db(h, rate, low) < level_db:
        return None
    for _ in range(50):
        middle = math.sqrt(low * high)
        if magnitude_db(h, rate, middle) > level_db:
            low = middle
        else:
            high = middle
    return math.sqrt(low * high)


def corner_ratio(cls, rate, character, time_ms=None, midi=None, amp=32767):
    """The measured corner over `0.2211 N / T`, or `None`."""
    h = first_repeat(cls, rate, character, time_ms=time_ms, midi=midi,
                     amp=amp)
    hz = crossing_hz(h, rate)
    if hz is None:
        return None
    knob = grid_ms(midi) if midi is not None else time_ms
    return hz / law_corner(character, knob)


def t2a_measure(cls, rate=RATE):
    """T2a at the named cells, both characters: every ratio within 10 %,
    and the octave ratios 1.8-2.2 between claimed cells."""
    ratios = {}
    for character in (SINGLE, DOUBLE):
        for time_ms in (75.0, 150.0, 300.0, 600.0):
            if law_corner(character, time_ms) >= rate * 0.5 * 0.98:
                continue
            ratios[(character, time_ms)] = corner_ratio(
                cls, rate, character, time_ms=time_ms)
    passed = all(r is not None and abs(r - 1.0) <= 0.10
                 for r in ratios.values())
    octaves = []
    if passed:
        for (character, time_ms), ratio in ratios.items():
            longer = (character, 2.0 * time_ms)
            if longer in ratios:
                hz_short = ratio * law_corner(character, time_ms)
                hz_long = ratios[longer] * law_corner(character, 2 * time_ms)
                octaves.append(hz_short / hz_long)
        passed = all(1.8 <= o <= 2.2 for o in octaves)
    return {"passed": passed, "ratios": ratios, "octaves": octaves}


def t6_measure(cls, rate=RATE, times=(150.0, 300.0, 600.0)):
    """T6: double-line's corner over single-line's at the same Time,
    1.8-2.2 at every cell where double-line's target is under the clamp."""
    ratios = {}
    for time_ms in times:
        if law_corner(DOUBLE, time_ms) >= rate * 0.5 * 0.98:
            continue
        single = first_repeat(cls, rate, SINGLE, time_ms=time_ms)
        double = first_repeat(cls, rate, DOUBLE, time_ms=time_ms)
        hz_single = crossing_hz(single, rate)
        hz_double = crossing_hz(double, rate)
        ratios[time_ms] = (None if hz_single is None or hz_double is None
                           else hz_double / hz_single)
    passed = bool(ratios) and all(
        r is not None and 1.8 <= r <= 2.2 for r in ratios.values())
    return {"passed": passed, "ratios": ratios}


# --------------------------------------------------------------------------
# T3: a Time move glides on the clock's law


MOVE_AT = 40960        # a block boundary 853 ms in: the line is full


def default_move_at(rate):
    """The block boundary T3 moves on at `rate`: MOVE_AT's 853 ms, floored
    to a block."""
    return MOVE_AT * rate // 48000 // BLOCK * BLOCK


def t3_render(cls, rate, character, t_old, t_new, values, channels=1,
              move_at=None, handed=None):
    """Render `values` at Mix 2, Feedback 0, Time `t_old`, moving Time to
    `t_new` through `set_macro(0, ...)` on the block at `move_at` (a block
    boundary; MOVE_AT's by default). With a dict `handed`, the node's
    options as handed by that move are copied into it."""
    effect = cls(array_src(values, channels, rate), sample_rate=rate,
                 character=character, time_ms=t_old, feedback=0.0, mix=2.0)
    target = midi_of_ms(t_new)
    if move_at is None:
        move_at = default_move_at(rate)

    def move(frame):
        if frame == move_at:
            if handed is None:
                effect.set_macro(TIME_I, target)
            else:
                with NodeSpy():
                    effect.set_macro(TIME_I, target)
                handed.update(getattr(effect._delay, "_handed", {}))

    out = left(pull(effect, len(values), channels, on_block=move), channels)
    effect.deinit()
    return out, move_at


def t3_static(cls, rate, character, time_ms, values, channels=1):
    effect = cls(array_src(values, channels, rate), sample_rate=rate,
                 character=character, time_ms=time_ms, feedback=0.0, mix=2.0)
    out = left(pull(effect, len(values), channels), channels)
    effect.deinit()
    return out


def open_loop(cls):
    """Measurement helper, not a fault: `cls` with the loop low-pass taken
    out after every refresh, so a ramp render reads the read head's delay
    with no filter lag on it. The walk does not depend on the filter."""
    def _refresh(self):
        cls._refresh(self)
        self._delay.set(damping_hz=0.0)
    return type("OpenLoop" + cls.__name__, (cls,), {"_refresh": _refresh})


def read_position(cls, rate, character, t_old, t_new, frames):
    """The read head's delay, frame by frame, off a slope-1 ramp render
    through `open_loop(cls)`: `n - ramp(n) - out(n)`. Superseded for T3 by
    `head_trace` (dossier section 8, revision 2026-09-28); kept so the
    Station C and refutation probes still run as they were written."""
    k_old = whole(t_old, rate)
    move_at = default_move_at(rate)
    origin = move_at - k_old - 2000
    n = np.arange(frames)
    ramp = ((n - origin) % 65536) - 32768
    out, move_at = t3_render(open_loop(cls), rate, character, t_old, t_new,
                             ramp.tolist())
    return (n - origin - 32768) - out, move_at


def walk_end(delay, move_at, k_new):
    """The first frame after the move at which the read position, and the
    frame after it, sit within 2 frames of `k_new` (the Station A probe's
    rule), or the end of the render if it never does. Superseded for T3 by
    `landing` (revision 2026-09-28): it reads a walk 2 / slew frames early,
    which is 10-21 % of a one-grid-step move from the 20 ms stop."""
    near = np.abs(delay[move_at:] - k_new) <= 2.0
    both = np.nonzero(near[:-1] & near[1:])[0]
    if both.size == 0:
        return len(delay)
    return move_at + int(both[0])


def binade_pieces(delay, move_at, end, law):
    """Each piece of the walk between powers of two of the read position,
    at least 1000 frames long, as (pitch ratio off a least-squares slope,
    frames). Superseded for T3 by `walk_pieces` (revision 2026-09-28): it
    found no piece on 60 -> 20 and 40 -> 20 ms at 48 and 22.05 kHz, and T3
    then passed with nothing read; kept so the refutation probes still
    run as they were written."""
    span = delay[move_at:end]
    powers = np.floor(np.log2(np.maximum(span, 1.0)))
    pieces = []
    start = 0
    for index in range(1, len(span) + 1):
        if index == len(span) or powers[index] != powers[start]:
            a, b = start + 16, index - 16
            if b - a >= 1000:
                x = np.arange(a, b, dtype=np.float64)
                slope = np.polyfit(x, span[a:b], 1)[0]
                pieces.append((1.0 - slope, b - a))
            start = index
    return pieces


def ramp_slope(k_old, k_new):
    """The steepest power-of-two ramp slope, up to 64 LSB per frame, whose
    period still holds the longer delay twice over with room for the walk:
    the head then reads to 1 / slope frame."""
    kmax = max(k_old, k_new)
    slope = 1
    while slope < 64 and 65536 // (2 * slope) > 1.25 * kmax + 64:
        slope *= 2
    return slope


def head_trace(cls, rate, character, t_old, t_new, frames, move_at=None,
               channels=1):
    """The read head's delay off one steep ramp render through
    `open_loop(cls)`: (delay per frame to 1 / slope frame, the frames whose
    read straddles the ramp's wrap marked False, slope, move frame)."""
    k_old, k_new = whole(t_old, rate), whole(t_new, rate)
    slope = ramp_slope(k_old, k_new)
    n = np.arange(frames)
    ramp = ((n * slope) % 65536) - 32768
    out, move_at = t3_render(open_loop(cls), rate, character, t_old, t_new,
                             ramp.tolist(), channels, move_at=move_at)
    period = 65536.0 / slope
    delay = np.mod(n - (out + 32768.0) / slope, period)
    bad = np.abs(np.diff(out, prepend=out[0])) > 4 * slope
    for k in (1, 2):
        bad[:-k] |= bad[k:].copy()
        bad[k:] |= bad[:-k].copy()
    return delay, ~bad, slope, move_at


def landing(delay, valid, slope, move_at, k_new):
    """The frame after the last one, from the move on, at which the head
    is more than one ramp step (1 / slope frame) off `k_new`: where the
    walk lands, at the ramp's resolution. The end of the render if the
    head is still off there."""
    off = (np.abs(delay[move_at:] - k_new) > 1.0 / slope) & valid[move_at:]
    idx = np.nonzero(off)[0]
    if idx.size == 0:
        return move_at
    last = move_at + int(idx[-1]) + 1
    return len(delay) if last >= len(delay) - 3 else last


def min_piece(slope, k_old, k_new):
    """The shortest piece whose rate the ramp resolves to 1 cent: one ramp
    step of position (1 / slope frame) over the piece moves its rate by at
    most (2^(1/1200) - 1) of the law's pitch ratio k_old / k_new."""
    ratio = float(k_old) / k_new
    return int(math.ceil(1.0 / (slope * ratio * (2.0 ** (1.0 / 1200.0)
                                                 - 1.0))))


def walk_pieces(delay, valid, slope, move_at, end, k_old, k_new):
    """The walk cut where the head crosses each power of two between the
    two Times (the node walks the head in single precision, so each binade
    plays at its own rate), each piece's pitch ratio 1 - dD/dn by least
    squares over its valid frames, as (ratio, frames). A piece shorter than
    `min_piece` is left out; if none is left, the whole walk is one piece,
    and if that is short too, the list is empty and the clause is red."""
    shortest = min_piece(slope, k_old, k_new)
    lo_k, hi_k = sorted((k_old, k_new))
    edges = [2 ** e for e in range(1, 20) if lo_k < 2 ** e < hi_k]
    cuts = [move_at]
    for edge in sorted(edges, reverse=k_new < k_old):
        seg = delay[move_at:end]
        hit = (seg >= edge) if k_new > k_old else (seg < edge)
        idx = np.nonzero(hit & valid[move_at:end])[0]
        if idx.size:
            cuts.append(move_at + int(idx[0]))
    cuts.append(end)

    def fit(a, b):
        m = np.arange(a + 2, b - 2)
        m = m[valid[m]]
        if len(m) < shortest:
            return None
        return (1.0 - np.polyfit(m.astype(float), delay[m], 1)[0], len(m))

    pieces = [p for p in (fit(a, b) for a, b in zip(cuts, cuts[1:]))
              if p is not None]
    if not pieces:
        whole_walk = fit(move_at, end)
        if whole_walk is not None:
            pieces = [whole_walk]
    return pieces


def memory_bars(bar, pre_bar, damping_hz, rate, frames):
    """T3's inside no-step bar, frame by frame from the move (dossier
    section 8, revision 2026-09-28): the shifted tone's own largest first
    difference, plus what the loop low-pass can still carry of the pre-move
    tone's slope `k` frames on, `pre_bar * (1 - a)^(k + 1)`, with `a` the
    one-pole's coefficient `1 - exp(-2 pi damping_hz / fs)` for the
    `damping_hz` the move handed the node. The one-pole's first difference
    obeys d(k) = (1 - a) d(k - 1) + a x'(k), so this is its memory, not a
    fitted allowance."""
    if damping_hz > 0.0:
        keep = math.exp(-2.0 * math.pi * damping_hz / rate)
    else:
        keep = 0.0
    k = np.arange(frames, dtype=np.float64)
    return bar + pre_bar * keep ** (k + 1.0)


def inside_clause(diff, move_at, walk, bar, pre_bar, damping_hz, rate):
    """T3's inside no-step statistic, revised 2026-09-28: the largest
    first difference over the walk as read, each frame against its
    `memory_bars` bar, as (largest ratio, its frame from the move, the
    settle, the largest first difference in the same window with no
    memory term, which is the frozen statistic's numerator). The walk's
    frames are the move's to the landing's; the last
    difference, into the landed frame, is the head's last partial step,
    where the pitch goes back to unity as the law says, and is the after
    clause's. The window runs at least `settle` frames, the frames until
    the low-pass's memory of the pre-move slope is under 5 % of the bar,
    so a move with no walk (the jump) is still read."""
    keep = (math.exp(-2.0 * math.pi * damping_hz / rate)
            if damping_hz > 0.0 else 0.0)
    settle = 1
    if keep > 0.0 and pre_bar > 0.05 * bar:
        settle = max(1, int(math.ceil(
            math.log(0.05 * bar / pre_bar) / math.log(keep))))
    span = min(max(walk - 1, settle, 1), len(diff) - move_at)
    window = diff[move_at:move_at + span]
    ratios = window / memory_bars(bar, pre_bar, damping_hz, rate, span)
    worst = int(np.argmax(ratios))
    return float(ratios[worst]), worst, settle, float(np.max(window))


def t3_measure(cls, rate=RATE, character=SINGLE, t_old=200.0, t_new=100.4,
               level=12000, channels=1, phase=0.0, move_at=None):
    """T3's clauses on one move: the pitch over the whole walk and on each
    binade piece within 10 cents of 1200 log2(T_old / T_new), the walk
    within 5 % of T_new (read where the head lands, off a steep ramp), the
    residual 50-250 ms after it within 1 cent, and the two no-step
    statistics within 5 % of their bars (the inside one against
    `memory_bars`). `inside_from_move` over `inside_bar` is the frozen
    statistic (the largest first difference from the move frame against
    the shifted tone's bar, no memory term) over the same window, kept
    beside the revision."""
    k_old, k_new = whole(t_old, rate), whole(t_new, rate)
    law = cents(float(k_old) / k_new)
    if move_at is None:
        move_at = default_move_at(rate)
    frames = move_at + int(1.25 * k_new) + 400 + int(0.3 * rate) + 4096
    delay, valid, slope, _ = head_trace(cls, rate, character, t_old, t_new,
                                        frames, move_at, channels)
    end = landing(delay, valid, slope, move_at, k_new)
    walk = end - move_at
    walk_ok = abs(walk - k_new) <= 0.05 * k_new

    handed = {}
    tone = sine_values(997.0, frames, rate, level, phase)
    out, _ = t3_render(cls, rate, character, t_old, t_new, tone, channels,
                       move_at=move_at, handed=handed)
    diff = np.abs(np.diff(out))

    shifted = 997.0 * k_old / k_new
    ref = t3_static(cls, rate, character, t_new,
                    sine_values(shifted, k_new + 8192, rate, level), channels)
    inside_bar = float(np.max(np.abs(np.diff(ref[k_new + 2048:]))))
    ref = t3_static(cls, rate, character, t_old,
                    sine_values(997.0, k_old + 8192, rate, level), channels)
    pre_bar = float(np.max(np.abs(np.diff(ref[k_old + 2048:]))))
    ref = t3_static(cls, rate, character, t_new,
                    sine_values(997.0, k_new + 8192, rate, level), channels)
    later_bar = float(np.max(np.abs(np.diff(ref[k_new + 2048:]))))

    damping = float(handed.get("damping_hz", 0.0))
    inside_ratio, worst, settle, inside_from_move = inside_clause(
        diff, move_at, walk, inside_bar, pre_bar, damping, rate)
    inside_ok = inside_ratio <= 1.05

    result = {"walk": walk, "k_new": k_new, "law": law, "slope": slope,
              "inside_ratio": inside_ratio, "inside_at": worst,
              "inside_ok": inside_ok, "inside_from_move": inside_from_move,
              "inside_bar": inside_bar, "pre_bar": pre_bar,
              "damping_hz": damping, "settle": settle,
              "later_bar": later_bar, "walk_ok": walk_ok}
    if walk < 64 or end + int(0.25 * rate) + 1 > frames:
        # No walk at all, or one that never lands on T_new inside the
        # render: the walk clause is red and the pitch has nothing to read.
        result.update(passed=False, whole=None, pieces=[], residual=None,
                      later=None)
        return result
    hz = inst_hz(out, rate)
    margin = min(400, walk // 10)
    whole_cents = cents(float(np.median(hz[move_at + margin:end - margin]))
                        / 997.0)
    pieces = [cents(ratio) for ratio, _ in
              walk_pieces(delay, valid, slope, move_at, end, k_old, k_new)]
    after = hz[end + int(0.05 * rate):end + int(0.25 * rate)]
    residual = cents(float(np.median(after)) / 997.0)
    later = float(np.max(diff[end + 64:end + 4064]))

    result.update(whole=whole_cents, pieces=pieces, residual=residual,
                  later=later)
    result["passed"] = (
        walk_ok
        and abs(whole_cents - law) <= 10.0
        and len(pieces) > 0
        and all(abs(p - law) <= 10.0 for p in pieces)
        and abs(residual) <= 1.0
        and inside_ok
        and later <= 1.05 * later_bar)
    return result


# --------------------------------------------------------------------------
# T7: the dry path is a wire until the first repeat, and the repeat is there


def t7_measure(cls, rate=RATE, channels=2, name="ramp_fs", **options):
    """WIRE over the first T - S - 1 frames of the kit's material, and,
    where Mix is above 0 and the material outlasts it, the output not the
    source somewhere in [T - S - 1, T + S + 64)."""
    probe_effect = cls(silence_src(64, channels, rate), sample_rate=rate,
                       **options)
    frames_t = probe_effect._frames
    swing = int(math.ceil(probe_effect._swing_ms * rate / 1000.0))
    mix = probe_effect.macro(MIX_I)
    probe_effect.deinit()
    data = material(name, rate, channels)
    total = len(data) // channels
    effect = cls(probes.ArraySource(data, rate=rate, channels=channels,
                                    block=BLOCK), sample_rate=rate, **options)
    out = pull(effect, total, channels)
    effect.deinit()
    src = np.array(data, dtype=np.int16)
    window = max(0, frames_t - swing - 1) * channels
    differing = int(np.count_nonzero(out[:window] != src[:window]))
    arrival_end = (frames_t + swing + 64) * channels
    applies = mix > 0.0 and arrival_end <= len(src)
    arrived = None
    if applies:
        arrived = int(np.count_nonzero(out[window:arrival_end]
                                       != src[window:arrival_end]))
    passed = differing == 0 and (not applies or arrived > 0)
    return {"passed": passed, "differing": differing, "arrived": arrived,
            "frames": frames_t, "swing": swing}


# --------------------------------------------------------------------------
# Tail


def kit_tail(cls, seconds, rate=RATE, **options):
    data, on = probes.burst_silence(total_s=seconds, rate=rate)
    effect = cls(probes.ArraySource(data, rate=rate, channels=2,
                                    block=BLOCK), sample_rate=rate, **options)
    declared = effect.tail_samples
    render = probes.render(effect, int(seconds * rate), rate=rate,
                           channels=2)
    result = kit.tail(render, burst_end_frame=on,
                      declared_tail_samples=declared,
                      settle_frames=effect._frames)
    effect.deinit()
    return declared, result["values"], result["red"]


def fullscale_tail(cls, rate=RATE, channels=1, **options):
    """A full-scale DC fill for two laps, then silence: the last non-zero
    frame after the input stops against `tail_samples`."""
    probe_effect = cls(silence_src(64, channels, rate), sample_rate=rate,
                       **options)
    declared = probe_effect.tail_samples
    frames_t = probe_effect._frames
    probe_effect.deinit()
    fill = (2 * frames_t + BLOCK) // BLOCK * BLOCK
    total = fill + declared + 2 * BLOCK
    values = [32767] * fill + [0] * (total - fill)
    effect = cls(array_src(values, channels, rate), sample_rate=rate,
                 **options)
    out = pull(effect, total, channels)
    after = out[fill * channels:]
    nonzero = np.nonzero(after)[0]
    last = 0 if nonzero.size == 0 else int(nonzero[-1]) // channels + 1
    return {"passed": last <= declared, "declared": declared, "last": last}


# --------------------------------------------------------------------------
# Reachability: what the node is handed, or what the output does, at the
# position walked. The twin's `FeedbackDelay.set` is watched while a walk
# runs, so a reading sees the options the class actually handed over.


class NodeSpy:
    """While active, every `audioecho.FeedbackDelay.set` call records its
    options on the node: `_handed` (the latest value of each option) and
    `_writes` (each call's options, in order)."""

    def __enter__(self):
        node_class = ad.audioecho.FeedbackDelay
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


def copy_of(effect, source):
    """A fresh instance of the same class and character on `source`, at
    `effect`'s macro positions."""
    other = type(effect)(source, sample_rate=effect._sample_rate,
                         character=effect._character)
    for index in range(len(type(effect).MACRO_LABELS)):
        other.set_macro(index, effect.get_macro(index))
    return other


def read_corner_law(effect):
    """The `damping_hz` handed to the node against the pre-warp of the
    dossier's corner law at the knob's milliseconds, clamped, for this
    instance's character."""
    rate = effect._sample_rate
    knob = effect.macro(TIME_I)
    law = nominal_damping_hz(clamp_hz(law_corner(effect._character, knob),
                                      rate), rate)
    return round(effect._delay._handed["damping_hz"] / law, 4)


def read_walk_law(effect):
    """On a copy at these positions, one Time move of 32 grid steps after
    a block has been pulled: the `delay_slew` handed against the dossier's
    |dT| / T_new of the two whole frames."""
    rate = effect._sample_rate
    other = copy_of(effect, silence_src(4 * BLOCK, 2, rate))
    pull(other, BLOCK, 2)
    before = other._frames
    now = other.get_macro(TIME_I)
    other.set_macro(TIME_I, now + 32.0 if now < 64 else now - 32.0)
    after = other._frames
    slew = other._delay._handed["delay_slew"]
    other.deinit()
    law = abs(after - before) / float(after)
    return round(slew / law, 4)


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


def read_landing(effect):
    """Whether the node's own single-precision arithmetic lands the handed
    delay at or above its whole frame."""
    ms = np.float32(effect._delay._handed["delay_ms"])
    frames = float(ms * np.float32(effect._sample_rate) / np.float32(1000.0))
    return frames >= effect._frames


def read_step(effect):
    """On an open-loop copy at these positions, read with Mix 2, Feedback 0
    and Modulation 0, one Time move of 32 grid steps once the line has
    filled, off a slope-1 ramp: whether the read head jumps, in any one
    frame of the walk, by more than the walk's own rate rounded up plus
    one frame."""
    rate = effect._sample_rate
    now = effect.get_macro(TIME_I)
    new = now + 32.0 if now < 64 else now - 32.0
    k_old = effect._frames
    k_new = whole(grid_ms(new), rate)
    fill = (k_old + 2 * BLOCK) // BLOCK * BLOCK
    frames = fill + int(1.3 * k_new) + 2 * BLOCK
    n = np.arange(frames)
    ramp = (n % 65536) - 32768
    other = open_loop(type(effect))(array_src(ramp.tolist(), 1, rate),
                                    sample_rate=rate,
                                    character=effect._character)
    for index in range(len(type(effect).MACRO_LABELS)):
        other.set_macro(index, effect.get_macro(index))
    other.set_macro(MIX_I, 127)
    other.set_macro(FEEDBACK_I, 0)
    other.set_macro(MODULATION_I, 0)

    def move(frame):
        if frame == fill:
            other.set_macro(TIME_I, new)

    out = left(pull(other, frames, 1, on_block=move), 1)
    slew = other._slew
    other.deinit()
    delay = np.mod(n - (out + 32768.0), 65536.0)
    # A read that straddles the ramp's wrap is not a jump of the head.
    bad = np.abs(np.diff(out, prepend=out[0])) > 64.0
    for k in (1, 2):
        bad[:-k] |= bad[k:].copy()
        bad[k:] |= bad[:-k].copy()
    good = ~bad
    jumps = np.abs(np.diff(delay[fill:]))[good[fill + 1:]]
    return bool(np.max(jumps) > math.ceil(slew) + 1.0)


#: (name, fault, reading, constructor options for both builds).
REACH_WALKS = (
    ("CornerN6144", CornerN6144, read_corner_law, {}),
    ("CornerN6144 double", CornerN6144, read_corner_law,
     {"character": DOUBLE}),
    ("DoubleLineN6144", DoubleLineN6144, read_corner_law,
     {"character": DOUBLE}),
    ("JumpAnalogDelay", JumpAnalogDelay, read_walk_law, {}),
    ("ConstantGlideWalk", ConstantGlideWalk, read_walk_law, {}),
    ("DryGainDelay", DryGainDelay, read_dry_gain, {}),
    ("MidWalkReadStep", MidWalkReadStep, read_step, {}),
)


def reach(faulted, reading, rate, ctor):
    """`kit_faults.fault_reachability` at `rate`, the node watched."""
    def build(cls):
        return cls(silence_src(512, 2, rate), sample_rate=rate, **ctor)

    with NodeSpy():
        return kit_faults.fault_reachability(AnalogDelay, faulted, reading,
                                             build)


# --------------------------------------------------------------------------
# The surface


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = AnalogDelay
        self.assertEqual(cls.MACRO_LABELS,
                         ("Time", "Feedback", "Mix", "Modulation", "Mod Rate",
                          "Spread", "Sync", "Division"))
        self.assertEqual(cls.MACRO_MODES[SYNC_I], "TOGGLE")
        self.assertEqual(len(cls.PATCHES), 7)
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
        self.assertNotIn("AnalogDelay", rebuilt.ADOPTED)
        self.assertIn("AnalogDelay", rebuilt.parked())
        self.assertIsNot(audioeffects.AnalogDelay, AnalogDelay)

    def test_patches_are_the_dossier_settings_on_the_grid(self):
        # Section 6's table, settings in the macros' own units, through
        # `_component.macro_of`; patch 0 is the constructor's defaults.
        spans = AnalogDelay._MACRO_RANGES
        settings = {
            0: (300.0, 0.40, 0.40, 0.0, 0.8, 0.0, 0.0, 6.0),
            1: (60.0, 0.30, 0.50, 0.0, 0.8, 0.0, 0.0, 6.0),
            2: (550.0, 0.55, 0.40, 0.0, 0.8, 0.0, 0.0, 6.0),
            3: (350.0, 0.45, 0.45, 3.0, 1.0, 0.0, 0.0, 6.0),
            4: (40.0, 0.0, 2.0, 2.0, 5.0, 0.0, 0.0, 6.0),
            5: (450.0, 0.85, 0.35, 1.0, 0.4, 0.5, 0.0, 6.0),
            6: (300.0, 0.45, 0.40, 0.0, 0.8, 0.0, 1.0, 8.0),
        }
        names = ("Single Line Repeats", "Short Bright Repeats",
                 "Long Dark Repeats", "Modulated Repeats", "Wet Vibrato",
                 "High Feedback Wash", "Dotted Eighth, Synced")
        for index, values in settings.items():
            grid = tuple(_component.macro_of(span, value)
                         for span, value in zip(spans, values))
            self.assertEqual(AnalogDelay.PATCHES[index],
                             (names[index], grid), index)
        effect = AnalogDelay(silence_src(512), sample_rate=RATE)
        for index, expected in enumerate(AnalogDelay.PATCHES[0][1]):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_characters(self):
        for character, stages in ((SINGLE, 4096), (DOUBLE, 8192)):
            effect = AnalogDelay(silence_src(64), sample_rate=RATE,
                                 character=character)
            self.assertEqual(effect._stages, stages)
        with self.assertRaises(ValueError):
            AnalogDelay(silence_src(64), sample_rate=RATE,
                        character="triple-line")

    def test_the_corner_law_as_handed(self):
        # Section 6: damping_hz 2 980.2 / 2 973.3 / 2 847.8 at 300 ms
        # single-line, the pre-warped 3 018.8 Hz corner.
        for rate, damping in ((48000, 2980.2), (44100, 2973.3),
                              (22050, 2847.8)):
            effect = AnalogDelay(silence_src(64, 2, rate), sample_rate=rate)
            self.assertAlmostEqual(effect._damping, damping, places=1)
            self.assertAlmostEqual(effect._corner, 3018.8, delta=0.1)
        effect = AnalogDelay(silence_src(64), sample_rate=RATE,
                             character=DOUBLE)
        self.assertAlmostEqual(effect._corner, 6037.5, places=1)
        # Under the clamp point the corner holds at 0.98 x Nyquist.
        effect.set_macro(TIME_I, 0)
        self.assertEqual(effect._corner, 23520.0)

    def test_tail_samples_as_each_patch_plays(self):
        # Tier 3 and App. F4: laps x (reach + swing + 1 + memory), each
        # patch sized as its MIDI tuple plays, at 48 kHz, single-line.
        expected = {None: 187954, 0: 172956, 1: 28940, 2: 480276,
                    3: 238966, 4: 2037, 5: 1273515, 6: 201782}
        for patch, frames in expected.items():
            effect = AnalogDelay(silence_src(64), sample_rate=RATE,
                                 patch=patch)
            self.assertEqual(effect.tail_samples, frames, patch)
        # Patch 6 with a host at 120 bpm: 375 ms, 18 000 frames.
        effect = AnalogDelay.create(silence_src(64), RATE,
                                    transport=lambda: (True, 0.0, 120.0,
                                                       4, 4), patch=6)
        self.assertEqual(effect._frames, 18000)
        self.assertEqual(effect.tail_samples, 253008)

    def test_the_tail_is_finite_everywhere_the_knobs_go(self):
        for character in (SINGLE, DOUBLE):
            for rate in RATES:
                effect = AnalogDelay(silence_src(64, 2, rate),
                                     sample_rate=rate, character=character)
                for time_midi in (0, 25, 64, 101, 127):
                    effect.set_macro(TIME_I, time_midi)
                    for fb_midi in range(128):
                        effect.set_macro(FEEDBACK_I, fb_midi)
                        self.assertIsNotNone(effect.tail_samples,
                                             (character, rate, time_midi,
                                              fb_midi))
                        self.assertLess(abs(effect._feedback
                                            - 0.99 * fb_midi / 127.0), 3e-5)

    def test_constructor_edges(self):
        effect = AnalogDelay(silence_src(64), sample_rate=RATE, time_ms=0.0,
                             mod_rate_hz=0.0, max_time_ms=float("nan"))
        self.assertEqual(effect._frames, 960)
        self.assertAlmostEqual(effect.macro(RATE_I), 0.05)
        self.assertEqual(effect._max_time_ms, 600.0)
        effect = AnalogDelay(silence_src(64), sample_rate=RATE,
                             max_time_ms=100.0, time_ms=300.0)
        self.assertEqual(effect._frames, 4800)
        self.assertAlmostEqual(effect.macro(TIME_I), 100.0)
        effect.set_macro(TIME_I, 127)
        self.assertEqual(effect._frames, 4800)
        self.assertAlmostEqual(effect.get_macro(TIME_I), midi_of_ms(100.0))


# --------------------------------------------------------------------------
# Section 6: Time lands on its whole frame on every interpreter


class TimeHandOff(unittest.TestCase):
    def test_every_frame_count_lands_whole(self):
        # Every count from 20 to 606 ms at the three rates: the node's
        # single-precision arithmetic (modelled with numpy's float32,
        # independently of the class's `array('f')`) lands the handed
        # value at or above the count, at most 0.00195 frames above it.
        for rate in RATES:
            worst = 0.0
            stepped = 0
            fs = np.float32(rate)
            for k in range(whole(20.0, rate), whole(606.0, rate) + 1):
                value = ad.hand_off_ms(k, rate)
                got = float(np.float32(np.float32(value) * fs)
                            / np.float32(1000.0))
                self.assertGreaterEqual(got, k, (rate, k))
                worst = max(worst, got - k)
                plain = np.float32(k * 1000.0 / rate)
                stepped += float(np.float32(plain * fs)
                                 / np.float32(1000.0)) < k
            self.assertLessEqual(worst, 0.00196, rate)
            # App. F5: none at 48 kHz, 1 899 at 44.1, 953 at 22.05.
            self.assertEqual(stepped, {48000: 0, 44100: 1899,
                                       22050: 953}[rate])

    def _impulse(self, cls, rate, time_ms):
        k = whole(time_ms, rate)
        values = [0] * (k + 512)
        values[0] = 32767
        effect = cls(array_src(values, 1, rate), sample_rate=rate,
                     time_ms=time_ms, feedback=0.0, mix=2.0)
        effect.set_macro(TIME_I, midi_of_ms(time_ms))
        out = left(pull(effect, k + 512, 1), 1)
        return k, out

    def test_patch_0_time_arrives_on_its_frame(self):
        # Patch 0's grid Time at 44.1 kHz is k = 13 188, a count the plain
        # hand-off lands short: nothing may arrive before k.
        rate = 44100
        time_ms = grid_ms(101)
        k, out = self._impulse(AnalogDelay, rate, time_ms)
        self.assertEqual(k, 13188)
        self.assertEqual(int(np.count_nonzero(out[1:k])), 0)
        self.assertGreater(abs(out[k]), 10000)
        k, out = self._impulse(PlainHandOff, rate, time_ms)
        self.assertNotEqual(int(np.count_nonzero(out[1:k])), 0)

    def test_the_plain_hand_off_is_off_the_surface(self):
        for rate in (44100, 22050):
            with NodeSpy():
                result = kit_faults.fault_reachability(
                    AnalogDelay, False, read_landing,
                    lambda cls: cls(silence_src(64, 2, rate),
                                    sample_rate=rate))
            self.assertEqual(result["clean"], True)


# --------------------------------------------------------------------------
# Tier 2 rows


class T2aCornerTracksTime(unittest.TestCase):
    def test_the_named_cells_and_octaves(self):
        for rate in RATES:
            result = t2a_measure(AnalogDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
            for ratio in result["ratios"].values():
                self.assertLess(abs(ratio - 1.0), 0.01, (rate, result))

    def test_the_grid_at_both_levels(self):
        # Every claimed grid position at 48 kHz on both characters through
        # the kit's sweep, stops first, at 0 dBFS; at -40 dBFS from one
        # position higher, and every eighth.
        for character in (SINGLE, DOUBLE):
            first = first_claimed(character, RATE)
            self.assertEqual(first, {SINGLE: 25, DOUBLE: 51}[character])
            for amp, low, midpoints in (
                    (32767, first, 127 - first - 1),
                    (328, first + 1, (127 - first - 1) // 8)):
                def measure_at(settings, amp=amp, character=character):
                    ratio = corner_ratio(AnalogDelay, RATE, character,
                                         midi=settings[TIME_I], amp=amp)
                    return {"values": {"error": 1.0 if ratio is None
                                       else ratio - 1.0}}
                result = kit.macro_sweep(
                    lambda: AnalogDelay(silence_src(64), sample_rate=RATE,
                                        character=character),
                    [kit.MacroSpan(TIME_I, low, 127, midpoints=midpoints)],
                    measure_at, figure="error", bar=0.10)
                self.assertEqual(result["red"], [],
                                 (character, amp, result["values"]["worst"],
                                  result["values"]["at_units"]))

    def test_the_other_rates_on_the_grid(self):
        for rate in (44100, 22050):
            for character in (SINGLE, DOUBLE):
                first = first_claimed(character, rate)
                for midi in list(range(first, 128, 6)) + [127]:
                    ratio = corner_ratio(AnalogDelay, rate, character,
                                         midi=midi)
                    self.assertIsNotNone(ratio, (rate, character, midi))
                    self.assertLess(abs(ratio - 1.0), 0.10,
                                    (rate, character, midi, ratio))

    def test_n6144_is_red(self):
        for rate in RATES:
            self.assertFalse(t2a_measure(CornerN6144, rate)["passed"], rate)
        ratio = corner_ratio(CornerN6144, RATE, SINGLE, time_ms=300.0)
        self.assertAlmostEqual(ratio, 1.5, delta=0.01)
        ratio = corner_ratio(CornerN6144, RATE, DOUBLE, time_ms=300.0)
        self.assertAlmostEqual(ratio, 0.75, delta=0.01)


class T6CharactersAnOctaveApart(unittest.TestCase):
    def test_the_named_cells(self):
        for rate in RATES:
            result = t6_measure(AnalogDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        # 150 ms at 22.05 kHz: double-line's target is above the clamp, so
        # the cell is not claimed, and the ratio shows why.
        single = crossing_hz(first_repeat(AnalogDelay, 22050, SINGLE,
                                          time_ms=150.0), 22050)
        double = crossing_hz(first_repeat(AnalogDelay, 22050, DOUBLE,
                                          time_ms=150.0), 22050)
        self.assertLess(double / single, 1.8)
        self.assertAlmostEqual(double / single, 1.7927, delta=0.001)

    def test_double_lines_grid_and_the_patches(self):
        for midi in list(range(51, 128, 4)) + [127, 101, 124, 107, 116]:
            single = crossing_hz(first_repeat(AnalogDelay, RATE, SINGLE,
                                              midi=midi), RATE)
            double = crossing_hz(first_repeat(AnalogDelay, RATE, DOUBLE,
                                              midi=midi), RATE)
            self.assertTrue(1.8 <= double / single <= 2.2, (midi,))

    def test_n6144_on_double_line_is_red(self):
        for rate in RATES:
            result = t6_measure(DoubleLineN6144, rate, times=(300.0,))
            self.assertFalse(result["passed"], rate)
            self.assertAlmostEqual(result["ratios"][300.0], 1.5, delta=0.01)


class T3TimeGlidesOnTheClock(unittest.TestCase):
    def test_the_row_cell(self):
        # 200 -> 100.4 ms: +1193.2 cents for 4 819 frames at 48 kHz.
        for character in (SINGLE, DOUBLE):
            result = t3_measure(AnalogDelay, RATE, character)
            self.assertTrue(result["passed"], (character, result))
            self.assertAlmostEqual(result["law"], 1193.2, delta=0.05)

    def test_moves_both_ways_at_three_rates(self):
        for rate, t_old, t_new, level in (
                (48000, 100.4, 200.0, 12000),
                (48000, 300.0, 100.0, 1200),
                (44100, 100.0, 300.0, 32000),
                (44100, 200.0, 600.0, 12000),
                (22050, 600.0, 200.0, 3800),
                (22050, 20.0, 60.0, 12000),
                (48000, 40.0, 20.0, 12000)):
            result = t3_measure(AnalogDelay, rate, SINGLE, t_old, t_new,
                                level)
            self.assertTrue(result["passed"],
                            (rate, t_old, t_new, level, result))

    def test_the_long_moves_are_read_per_binade(self):
        # 200 -> 600 ms crosses 16 384 frames at 48 kHz; its upper binade
        # plays its own rate, within 10 cents of the law (App. F5: +3.38).
        result = t3_measure(AnalogDelay, RATE, SINGLE, 200.0, 600.0)
        self.assertEqual(len(result["pieces"]), 2, result)
        self.assertTrue(result["passed"], result)

    def test_the_jump_is_red(self):
        # The walk clause reds a jump at every boundary: there is no walk.
        # The inside clause sees the step itself at 15 of these 16; at the
        # other the jump lands on nearly the same sample value (0.964 of
        # its bar), which no first-difference statistic can see.
        base = default_move_at(RATE)
        seen = 0
        for j in range(16):
            result = t3_measure(JumpAnalogDelay, RATE, SINGLE, 20.0, 60.0,
                                move_at=base + BLOCK * j)
            self.assertFalse(result["passed"], (j, result))
            self.assertLess(result["walk"], 64, j)
            seen += 0 if result["inside_ok"] else 1
        self.assertGreaterEqual(seen, 15)

    def test_the_constant_glide_is_red(self):
        for rate in RATES:
            result = t3_measure(ConstantGlideWalk, rate, SINGLE, 300.0, 100.0)
            self.assertFalse(result["passed"], (rate, result))
            self.assertGreater(result["walk"], 1.5 * result["k_new"])
            self.assertLess(result["whole"] - result["law"], -600.0)
            self.assertTrue(all(p - result["law"] < -600.0
                                for p in result["pieces"]), result)


class T3NoStepRevision(unittest.TestCase):
    """Dossier section 8, revision 2026-09-28: the inside no-step bar
    carries the loop low-pass's memory of the pre-move slope, derived from
    the handed `damping_hz`; the walk is read where the head lands; the
    binade pieces have a minimum the ramp resolves, and a walk with none
    left is read whole."""

    def test_the_one_pole_memory_is_not_a_step(self):
        # 20 -> 60 ms moved ten blocks later than the pack's boundary: the
        # frozen statistic reads 551 against a 522 bar (1.0556) at the
        # walk's first frame; the revised bar there is 522 + 1562 (1 - a).
        move_at = default_move_at(RATE) + 10 * BLOCK
        for character in (SINGLE, DOUBLE):
            result = t3_measure(AnalogDelay, RATE, character, 20.0, 60.0,
                                move_at=move_at)
            self.assertGreater(result["inside_from_move"],
                               1.05 * result["inside_bar"], character)
            self.assertTrue(result["inside_ok"], (character, result))
            self.assertTrue(result["passed"], (character, result))
            result = t3_measure(open_loop(AnalogDelay), RATE, character,
                                20.0, 60.0, move_at=move_at)
            self.assertLessEqual(result["inside_from_move"],
                                 1.05 * result["inside_bar"], character)

    def test_the_memory_is_the_handed_coefficient(self):
        bars = memory_bars(522.0, 1562.0, 11606.7651, RATE, 3)
        keep = math.exp(-2.0 * math.pi * 11606.7651 / RATE)
        self.assertAlmostEqual(bars[0], 522.0 + 1562.0 * keep)
        self.assertAlmostEqual(bars[2], 522.0 + 1562.0 * keep ** 3)
        self.assertEqual(list(memory_bars(522.0, 1562.0, 0.0, RATE, 2)),
                         [522.0, 522.0])

    def test_a_mid_walk_read_step_is_red(self):
        result = t3_measure(MidWalkReadStep, RATE, SINGLE)
        self.assertFalse(result["inside_ok"], result)
        self.assertLess(abs(result["inside_at"] - result["k_new"] // 2), 4,
                        result)
        self.assertFalse(result["passed"])

    def test_one_grid_step_from_the_stop_lands(self):
        # The frozen walk_end read this 9.6 / 10.5 / 21.0 % short.
        for rate in RATES:
            k_new = whole(grid_ms(1), rate)
            move_at = default_move_at(rate)
            frames = move_at + 2 * k_new + 4096
            delay, valid, slope, _ = head_trace(AnalogDelay, rate, SINGLE,
                                                20.0, grid_ms(1), frames)
            walk = landing(delay, valid, slope, move_at, k_new) - move_at
            self.assertLess(abs(walk - k_new), 0.02 * k_new, (rate, walk))
            old, _ = read_position(AnalogDelay, rate, SINGLE, 20.0,
                                   grid_ms(1), frames)
            walk = walk_end(old, move_at, k_new) - move_at
            self.assertGreater(abs(walk - k_new), 0.05 * k_new, (rate, walk))

    def test_every_named_move_reads_a_piece(self):
        # The frozen binade_pieces found none on 60 -> 20 and 40 -> 20 ms
        # at 48 and 22.05 kHz, or on 20 -> 60 ms at 22.05 kHz.
        for rate in (48000, 22050):
            for t_old, t_new in ((60.0, 20.0), (40.0, 20.0), (20.0, 60.0),
                                 (20.0, 40.0)):
                result = t3_measure(AnalogDelay, rate, SINGLE, t_old, t_new)
                self.assertGreater(len(result["pieces"]), 0,
                                   (rate, t_old, t_new))
                self.assertTrue(result["passed"], (rate, t_old, t_new))

    def test_a_sliver_under_the_minimum_is_not_read(self):
        # 3 : 1 from 8 182 frames crosses 8 192 in a 16-frame sliver the
        # frozen reading put at -31.77 cents; the ramp cannot resolve it.
        k_old = 8182
        result = t3_measure(AnalogDelay, RATE, SINGLE, k_old * 1000.0 / RATE,
                            3 * k_old * 1000.0 / RATE)
        self.assertEqual(len(result["pieces"]), 2, result)
        self.assertTrue(result["passed"], result)
        self.assertGreater(min_piece(1, k_old, 3 * k_old), 16)

    def test_no_piece_is_red(self):
        # A walk too short for any piece to resolve reads no piece, which
        # is red rather than a pass with nothing read.
        delay = np.full(100, 960.0)
        pieces = walk_pieces(delay, np.ones(100, bool), 1, 0, 50, 2880, 960)
        self.assertEqual(pieces, [])


def noise_src(frames, rate, seed=5):
    rng = np.random.RandomState(seed)
    values = np.round(rng.uniform(-1.0, 1.0, frames) * 8000.0)
    return probes.ArraySource(array("h", values.astype(np.int16).tobytes()),
                              rate=rate, channels=1, block=BLOCK)


def small_move_lands(cls, rate, t_old, t_new):
    """(differing samples, walk floor handed) over the last 0.5 s of 3 s
    after one move from rest `t_old -> t_new` through `set_macro`, against
    the class built at `t_new`: 0 means the head reached the new frame."""
    fill = int(rate / BLOCK) + 1
    settled = int(3.0 * rate)
    outs = []
    for time_ms in (t_old, t_new):
        effect = cls(noise_src(fill * BLOCK + settled + BLOCK, rate),
                     sample_rate=rate, time_ms=time_ms, mix=2.0,
                     feedback=0.0)
        pull(effect, fill * BLOCK)
        if time_ms == t_old:
            effect.set_macro(TIME_I, midi_of_ms(t_new))
        outs.append(pull(effect, settled))
    last = int(0.5 * rate)
    return int(np.count_nonzero(outs[0][-last:] != outs[1][-last:]))


class SmallTimeMovesLand(unittest.TestCase):
    """Section 6: every Time lands on its whole frame, a move of a few
    frames included. The node walks in single precision, so the class
    floors the walk rate at two single-precision steps of the furthest the
    head may sit (written out here: 2^(e - 23) for a head under 2^e
    frames)."""

    MOVES = ((300.0, 300.1), (300.0, 299.9), (600.0, 599.5),
             (300.0, 300.02))

    def test_moves_under_eight_frames_land(self):
        for rate in (48000, 44100):
            for t_old, t_new in self.MOVES:
                moved = whole(t_new, rate) - whole(t_old, rate)
                self.assertLess(abs(moved), 25)
                with self.subTest(rate=rate, move=(t_old, t_new)):
                    self.assertEqual(
                        small_move_lands(AnalogDelay, rate, t_old, t_new), 0)

    def test_the_floor_as_handed(self):
        with NodeSpy():
            effect = AnalogDelay(silence_src(4 * BLOCK), sample_rate=RATE)
            effect.set_macro(TIME_I, midi_of_ms(300.1))   # +5 frames
            self.assertEqual(effect._delay._handed["delay_slew"], 2.0 ** -9)
            effect = AnalogDelay(silence_src(4 * BLOCK), sample_rate=RATE,
                                 time_ms=600.0)
            effect.set_macro(TIME_I, midi_of_ms(599.5))   # -24 frames
            self.assertEqual(effect._delay._handed["delay_slew"], 2.0 ** -8)
            effect = AnalogDelay(silence_src(4 * BLOCK), sample_rate=RATE)
            effect.set_macro(TIME_I, midi_of_ms(100.0))   # the law, 2.0
            self.assertAlmostEqual(effect._delay._handed["delay_slew"], 2.0)

    def test_the_unfloored_law_leaves_the_head_short(self):
        for rate in (48000, 44100):
            for t_old, t_new in self.MOVES[:3]:
                with self.subTest(rate=rate, move=(t_old, t_new)):
                    self.assertGreater(
                        small_move_lands(UnflooredWalk, rate, t_old, t_new),
                        1000)


class T7DryIsAWire(unittest.TestCase):
    def test_defaults_on_three_materials(self):
        for name in ("ramp_fs", "tones_step", "sweep_log"):
            for channels in (2, 1):
                result = t7_measure(AnalogDelay, RATE, channels, name)
                self.assertTrue(result["passed"], (name, channels, result))
                self.assertEqual(result["frames"], 14400)

    def test_the_stops_and_the_corner(self):
        cells = (
            {"time_ms": 20.0}, {"time_ms": 600.0}, {"feedback": 0.99},
            {"mix": 0.0}, {"mix": 63 * 2.0 / 127.0}, {"mix": 1.0},
            {"modulation_ms": 5.0}, {"mod_rate_hz": 0.05},
            {"mod_rate_hz": 8.0}, {"spread": 1.0},
            {"time_ms": 20.0, "feedback": 0.99, "mix": 1.0,
             "modulation_ms": 5.0, "mod_rate_hz": 8.0, "spread": 1.0})
        for options in cells:
            for character in (SINGLE, DOUBLE):
                result = t7_measure(AnalogDelay, RATE, 2, "ramp_fs",
                                    character=character, **options)
                self.assertTrue(result["passed"], (options, character,
                                                   result))
        corner = cells[-1]
        for rate in RATES:
            for channels in (2, 1):
                result = t7_measure(AnalogDelay, rate, channels, "sweep_log",
                                    **corner)
                self.assertTrue(result["passed"], (rate, channels, result))
                self.assertEqual(result["frames"], whole(20.0, rate))
                self.assertIsNotNone(result["arrived"])

    def test_the_patches_with_mix_up_to_one(self):
        for patch in (0, 1, 2, 3, 5, 6):
            result = t7_measure(AnalogDelay, RATE, 2, "tones_step",
                                patch=patch)
            self.assertTrue(result["passed"], (patch, result))

    def test_the_mix_interior(self):
        # Dossier section 8, revision 2026-09-28: arrival is claimed on
        # ramp_fs and tones_step at every Mix above 0, and on sweep_log from
        # grid 17 at 48 kHz, where the wet's ~2 LSB times Mix first clears
        # the node's round to nearest. The null build reds at grid 1.
        for name, grids in (("ramp_fs", (1, 2, 8, 16, 17, 40, 63)),
                            ("tones_step", (1, 2, 8, 16, 17, 40, 63)),
                            ("sweep_log", (17, 24, 40, 63))):
            for grid in grids:
                result = t7_measure(AnalogDelay, RATE, 2, name,
                                    mix=2.0 * grid / 127.0)
                self.assertTrue(result["passed"], (name, grid, result))
        result = t7_measure(AnalogDelay, RATE, 2, "sweep_log",
                            mix=2.0 * 16 / 127.0)
        self.assertEqual(result["arrived"], 0)       # the unclaimed edge
        wire = kit_faults.wire_build(AnalogDelay)
        result = t7_measure(wire, RATE, 2, "ramp_fs", mix=2.0 / 127.0)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["differing"], 0)

    def test_a_dry_above_unity_is_red_at_every_level(self):
        for name in ("ramp_fs", "tones_step", "sweep_log"):
            result = t7_measure(DryGainDelay, RATE, 2, name)
            self.assertFalse(result["passed"], name)
            self.assertGreater(result["differing"], 1000, name)


# --------------------------------------------------------------------------
# The rows recorded unmeasured or disconfirmed by decision


class RecordedRows(unittest.TestCase):
    def test_no_null_at_the_clock(self):
        # T1 and T2b: with no sample-and-hold the first repeat has no null
        # at f_clk = N / 2T (App. F1: -7.67 / -7.07 dB at 300 ms), so there
        # is nothing to read f_clk from. A null 20 dB deep would mean the
        # class gained a hold it was not built with.
        for character, f_clk in ((SINGLE, 4096 / 0.6), (DOUBLE, 8192 / 0.6)):
            h = first_repeat(AnalogDelay, RATE, character, time_ms=300.0)
            self.assertGreater(magnitude_db(h, RATE, f_clk), -20.0)

    def test_the_only_corner_moves_with_time(self):
        # T5: the class's one corner moves 75 % across 150 -> 600 ms and its
        # slope over the octave above it is a one-pole's (App. F1: 3.3-3.95
        # dB/octave), against a fixed pair's 30 dB/octave.
        low = crossing_hz(first_repeat(AnalogDelay, RATE, SINGLE,
                                       time_ms=600.0), RATE)
        high = crossing_hz(first_repeat(AnalogDelay, RATE, SINGLE,
                                        time_ms=150.0), RATE)
        self.assertGreater(1.0 - low / high, 0.7)
        h = first_repeat(AnalogDelay, RATE, SINGLE, time_ms=300.0)
        corner = crossing_hz(h, RATE)
        slope = magnitude_db(h, RATE, corner) - magnitude_db(
            h, RATE, 2.0 * corner)
        self.assertLess(slope, 6.0)


# --------------------------------------------------------------------------
# Tier 1, the fast half


class Tier1Fast(unittest.TestCase):
    def test_mix_zero_is_a_wire_on_the_full_scale_ramp(self):
        for rate in RATES:
            for channels in (2, 1):
                for character in (SINGLE, DOUBLE):
                    ramp = probes.ramp_fs(frames=rate, channels=channels)
                    source = probes.ArraySource(ramp, rate=rate,
                                                channels=channels,
                                                block=BLOCK)
                    effect = AnalogDelay(source, sample_rate=rate, mix=0.0,
                                         time_ms=20.0, feedback=0.99,
                                         modulation_ms=5.0, mod_rate_hz=8.0,
                                         spread=1.0, character=character)
                    out = pull(effect, rate, channels)
                    self.assertTrue(np.array_equal(
                        out, np.array(ramp, dtype=np.int16)),
                        (rate, channels, character))

    def test_silence_stays_silence(self):
        for patch in range(7):
            effect = AnalogDelay(silence_src(RATE // 2), sample_rate=RATE,
                                 patch=patch)
            self.assertEqual(int(np.max(np.abs(pull(effect, RATE // 2)))), 0)

    def test_the_tail_reaches_exact_zero_inside_tail_samples(self):
        for options, seconds in (({}, 4.5), ({"patch": 1}, 1.5),
                                 ({"patch": 3}, 5.5), ({"patch": 4}, 0.5),
                                 ({"character": DOUBLE}, 4.5)):
            declared, values, red = kit_tail(AnalogDelay, seconds, **options)
            self.assertEqual(red, [], (options, values))
            self.assertLessEqual(values["tail_samples"], declared)
        declared, values, red = kit_tail(HalfTail, 4.5)
        self.assertNotEqual(red, [], values)

    def test_full_scale_meets_the_bound(self):
        # Full scale round the loop at the patches whose Feedback sits on a
        # stall window's side and at 0.99, mono, 48 kHz, short Times.
        for options in ({"time_ms": 20.0, "feedback": 0.5},
                        {"time_ms": 20.0, "feedback": 0.9},
                        {"time_ms": 20.0, "feedback": 0.99},
                        {"time_ms": 40.0, "feedback": 0.7,
                         "modulation_ms": 5.0, "mod_rate_hz": 8.0}):
            result = fullscale_tail(AnalogDelay, **options)
            self.assertTrue(result["passed"], (options, result))
            self.assertGreater(result["last"], 0)

    def test_a_raw_feedback_in_a_stall_window_never_ends(self):
        # Feedback 0.5 at 600 ms, where the low-pass is slow enough to rest
        # a hair above 1 LSB: handed raw, 1 LSB goes round for ever on a
        # 2 LSB DC; stepped clear of the window, it ends inside the bound.
        probe = AnalogDelay(silence_src(64), sample_rate=RATE, time_ms=600.0,
                            feedback=0.5, mix=2.0)
        declared = probe.tail_samples
        fill = 4 * 28800 // BLOCK * BLOCK
        values = [2] * fill + [0] * (declared + RATE)
        for cls, ends in ((AnalogDelay, True), (RawFeedback, False)):
            effect = cls(array_src(values, 1), sample_rate=RATE,
                         time_ms=600.0, feedback=0.5, mix=2.0)
            out = pull(effect, len(values), 1)
            self.assertEqual(int(np.max(np.abs(out[-RATE:]))) == 0, ends,
                             cls.__name__)

    def _walk_tail(self, cls):
        """600 ms of 997 Hz, Feedback 0, Mix 2; as the tone stops, Time
        600 -> 20 ms (slew 29), and one block later, with the head still
        near 600 ms, 20 -> 21 ms, whose rate (|dT| / T_new, 0.048) is taken
        from the Time last handed and not from where the head is. The walk
        then crawls down from near 600 ms for most of a second."""
        tone = int(0.6 * RATE) // BLOCK * BLOCK + BLOCK
        values = sine_values(997.0, tone, RATE, 12000) + [0] * (2 * RATE)
        effect = cls(array_src(values), sample_rate=RATE, time_ms=600.0,
                     feedback=0.0, mix=2.0)
        seen = {}

        def move(frame):
            if frame == tone:
                effect.set_macro(TIME_I, 0)
            elif frame == tone + BLOCK:
                effect.set_macro(TIME_I, midi_of_ms(21.0))
                seen["declared"] = effect.tail_samples

        out = pull(effect, len(values), on_block=move)
        after = out[(tone + BLOCK) * 2:]
        last = int(np.nonzero(after)[0][-1]) // 2 + 1
        return seen["declared"], last

    def test_a_falling_walk_keeps_the_old_time_in_the_tail(self):
        declared, last = self._walk_tail(AnalogDelay)
        self.assertGreater(last, 20000)
        self.assertLessEqual(last, declared)
        declared, last = self._walk_tail(TargetOnlyTail)
        self.assertGreater(last, declared)

    def test_the_swing_is_in_the_tail(self):
        # Feedback 0 at 20 ms with a 5 ms swing: the repeat can sit up to
        # 240 frames late, and the bound says so.
        options = {"time_ms": 20.0, "feedback": 0.0, "modulation_ms": 5.0,
                   "mod_rate_hz": 8.0, "mix": 2.0}
        effect = AnalogDelay(silence_src(64), sample_rate=RATE, **options)
        self.assertEqual(effect.tail_samples, 960 + 240 + 1 +
                         ad.tone_excess(effect._damping, RATE)[0])
        faulted = NoSwingTail(silence_src(64), sample_rate=RATE, **options)
        self.assertLess(faulted.tail_samples, effect.tail_samples)
        # A burst ending while the triangle holds the read late is heard
        # after the faulted bound.
        worst = 0
        for start in range(0, 6000, 750):
            values = [0] * start + sine_values(997.0, 2048, RATE, 12000)
            values += [0] * 4096
            effect = AnalogDelay(array_src(values, 1), sample_rate=RATE,
                                 **options)
            out = pull(effect, len(values), 1)
            nonzero = np.nonzero(out[start + 2048:])[0]
            if nonzero.size:
                worst = max(worst, int(nonzero[-1]) + 1)
        self.assertLessEqual(worst, AnalogDelay(
            silence_src(64), sample_rate=RATE, **options).tail_samples)
        self.assertGreater(worst, faulted.tail_samples)

    def test_mono_holds_spread_at_zero(self):
        # Section 4: at one channel the node's cross-feed sends the repeat
        # nowhere; the class holds it at 0, and the repeats go on.
        def repeats(cls):
            values = [0] * (3 * 4800 + 512)
            values[0] = 12000
            effect = cls(array_src(values, 1), sample_rate=RATE,
                         time_ms=100.0, feedback=0.7, mix=2.0, spread=1.0)
            out = left(pull(effect, len(values), 1), 1)
            return [float(np.max(np.abs(out[k * 4800:k * 4800 + 256])))
                    for k in (1, 2, 3)]
        clean = repeats(AnalogDelay)
        self.assertTrue(all(r > 1000 for r in clean), clean)
        faulted = repeats(SpreadInMono)
        self.assertEqual(faulted[1:], [0.0, 0.0])

    def test_modulation_is_the_table_and_a_time_move_leaves_it(self):
        with NodeSpy():
            effect = AnalogDelay(silence_src(4 * BLOCK), sample_rate=RATE,
                                 modulation_ms=5.0, mod_rate_hz=1.0)
            self.assertEqual(effect._delay._handed["wow_depth_ms"], 5.0)
            self.assertAlmostEqual(effect._delay._handed["wow_hz"], 1.0)
            pull(effect, BLOCK)
            effect.set_macro(TIME_I, 64)
            self.assertEqual(effect._delay._handed["wow_depth_ms"], 5.0)
            self.assertNotIn("wow_shape", effect._delay._writes[-1])
        table = ad.triangle_table()
        self.assertEqual((table[0], table[64], table[128], table[192]),
                         (0, 32767, 0, -32767))

    def test_the_swing_reads_as_a_triangle(self):
        # App. F4: 300 ms, 5 ms at 1 Hz reads +-240 frames off a ramp.
        rate = RATE
        start = 20000
        origin = start - 15200
        frames = start + rate + 100
        n = np.arange(frames)
        ramp = ((n - origin) % 65536) - 32768
        effect = AnalogDelay(array_src(ramp.tolist(), 1, rate),
                             sample_rate=rate, mix=2.0, feedback=0.0,
                             modulation_ms=5.0, mod_rate_hz=1.0)
        out = left(pull(effect, frames, 1), 1)
        delay = (ramp - out)[start:start + rate]
        swing = np.max(delay) - np.min(delay)
        self.assertAlmostEqual(swing / 2.0, 240.0, delta=3.0)

    def test_reset_empties_the_line(self):
        values = [0] * 256 + sine_values(997.0, 2048, RATE, 12000)
        values += [0] * RATE
        effect = AnalogDelay(array_src(values), sample_rate=RATE,
                             time_ms=100.0, feedback=0.9, mix=2.0)
        pull(effect, 2304)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(int(np.max(np.abs(pull(effect, RATE // 2)))), 0)

    def test_deinit_leaves_the_source(self):
        source = array_src(sine_values(440.0, 1024, RATE, 8000))
        effect = AnalogDelay(source, sample_rate=RATE)
        pull(effect, 256)
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(source)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)

    def test_click_delay_is_zero(self):
        for rate in (48000, 44100):
            values = [0] * 2048
            values[10] = 30000
            effect = AnalogDelay(array_src(values, 2, rate), sample_rate=rate)
            out = left(pull(effect, 2048), 2)
            self.assertEqual(int(np.argmax(np.abs(out))), 10)
            self.assertEqual(out[10], 30000)
            self.assertEqual(effect.latency_samples, 0)

    def test_the_input_ceiling(self):
        # Below Mix 1 an input peaking at floor(32767 (1 - Mix)) - 1 cannot
        # reach the rail: a square at that peak, Feedback 0.99, 20 ms.
        mix = 0.4
        peak = int(math.floor(32767 * (1.0 - mix))) - 1
        values = ([peak] * 24 + [-peak - 1] * 24) * 2000
        effect = AnalogDelay(array_src(values), sample_rate=RATE, mix=mix,
                             time_ms=20.0, feedback=0.99)
        out = pull(effect, len(values))
        self.assertLess(int(np.max(out)), 32767)
        self.assertGreater(int(np.min(out)), -32768)
        self.assertGreater(int(np.max(out)), peak + 5000)


class SyncAndTransport(unittest.TestCase):
    def _synced(self, bpm, patch=6):
        def transport():
            return (True, 0.0, bpm, 4, 4)
        return AnalogDelay.create(silence_src(64), RATE, transport=transport,
                                  patch=patch)

    def test_a_host_sets_time_from_division(self):
        effect = self._synced(120.0)
        self.assertEqual(effect._frames, 18000)
        effect.set_macro(DIVISION_I, 127)        # 1/1 = 2000 ms, clamps
        self.assertEqual(effect._frames, 28800)
        self.assertAlmostEqual(effect.get_macro(TIME_I), 127.0)

    def test_no_host_or_a_bad_tempo_leaves_time_on_the_knob(self):
        effect = AnalogDelay(silence_src(64), sample_rate=RATE, patch=6)
        self.assertEqual(effect._frames, whole(grid_ms(101), RATE))
        for bpm in (0.0, -1.0, float("nan"), float("inf"), None):
            effect = self._synced(bpm)
            self.assertEqual(effect._frames, whole(grid_ms(101), RATE), bpm)

    def test_the_transport_is_read_only_with_sync_on(self):
        reads = []

        def transport():
            reads.append(1)
            return (True, 0.0, 120.0, 4, 4)
        effect = AnalogDelay.create(silence_src(512), RATE,
                                    transport=transport)
        self.assertEqual(reads, [])
        effect.set_macro(SYNC_I, 127)
        self.assertGreater(len(reads), 0)

    def test_a_patch_moves_time_once(self):
        # program_change refreshes once, so a patch change from a synced
        # patch to an unsynced one lands the new patch's own Time and walks
        # to it at the clock's law from the synced Time.
        for cls, frames in ((AnalogDelay, whole(grid_ms(41), RATE)),
                            (PerMacroPatch, 18000)):
            effect = cls.create(silence_src(64), RATE,
                                transport=lambda: (True, 0.0, 120.0, 4, 4),
                                patch=6)
            effect.program_change(1)
            self.assertEqual(effect._frames, frames, cls)
        with NodeSpy():
            effect = self._synced(120.0)
            mark = len(effect._delay._writes)
            effect.program_change(1)
            writes = effect._delay._writes[mark:]
            self.assertEqual(len(writes), 1)
            k = whole(grid_ms(41), RATE)
            self.assertAlmostEqual(writes[0]["delay_slew"],
                                   abs(k - 18000) / float(k))
            effect = PerMacroPatch.create(
                silence_src(64), RATE,
                transport=lambda: (True, 0.0, 120.0, 4, 4), patch=6)
            mark = len(effect._delay._writes)
            effect.program_change(1)
            self.assertEqual(len(effect._delay._writes[mark:]), 8)

    def test_another_macro_leaves_a_walk_at_its_rate(self):
        with NodeSpy():
            effect = AnalogDelay(silence_src(8 * BLOCK), sample_rate=RATE)
            pull(effect, BLOCK)
            effect.set_macro(TIME_I, midi_of_ms(100.0))
            slew = effect._delay._handed["delay_slew"]
            self.assertAlmostEqual(slew, 2.0)
            effect.set_macro(FEEDBACK_I, 90)
            self.assertEqual(effect._delay._handed["delay_slew"], slew)


# --------------------------------------------------------------------------
# The two checks every planted fault and every row is held to


class FaultsAreUnreachable(unittest.TestCase):
    """Every fault's reachability walk, at 48, 44.1 and 22.05 kHz, reading
    what the node is handed (or what the output does) at each position."""

    CHECKED = 8 * 17 + 7

    def test_every_fault_is_off_the_surface_at_three_rates(self):
        for rate in RATES:
            for name, faulted, reading, ctor in REACH_WALKS:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, ctor)
                    self.assertEqual(result["checked"], self.CHECKED)
                    self.assertNotEqual(result["target"], result["clean"])


class NullBuildRed(unittest.TestCase):
    """Every demonstrated row goes red on the class built as a wire, beside
    a control on the real class that must pass."""

    def test_every_row_is_red_on_a_wire(self):
        for name, measure in (
                ("T2a", t2a_measure),
                ("T3", t3_measure),
                ("T6", t6_measure),
                ("T7", t7_measure)):
            with self.subTest(row=name):
                result = kit_faults.null_build_red(
                    AnalogDelay, measure, label="AnalogDelay %s" % name)
                self.assertFalse(result["null"]["passed"], name)
                self.assertTrue(result["control"]["passed"], name)


if __name__ == "__main__":
    unittest.main()
