"""`TapeDelay`'s own invariant and planted-fault tests.

The dossier's Tier 2
rows are T1a, T1b, T2, T3, T4 (demonstrated) and T5 (disconfirmed by
design). Each demonstrated row here is the measurement at a few of the
cells its *Quantified over* column names, the same measurement red on a
planted fault of the same kind, the fault shown unreachable from every macro
position and shipped patch at three rates by what the node is handed (fix
round 1: the first walk read a marker only the fault set, and could not
fail), and the measurement red on the class built as a wire. The exhaustive grids (every Glide grid position,
every Spacing and Time position, three rates for every cell) live in the
evidence pack, not in this file.

Re-audit fix round 2 (2026-09-28) added Tier 1's cross-feed stall: the five
stall cells and the kit's TAIL over Spread's whole travel. The trial of the
second process (2026-09-28, audiodsp v0.6.3rc3) hands Spread as set, since
the node cures the stall itself (audiodsp#173), and drops the
`RawSpreadTape` plant: it was the class as it now is, and at rc3 it ends.
`CLAIMS` ties every sentence of the module docstring to the test that
asserts it, and `BOARD_COST` holds the board figures the Cost paragraph
quotes.
"""

import math
import os
import re
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                            # noqa: E402
import lifecycle                                            # noqa: E402
import kit_faults                                           # noqa: E402
import kit_probes as probes                                 # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import rebuilt                            # noqa: E402
from audioeffects.rebuilt import tapedelay as tape          # noqa: E402
from audioeffects.rebuilt.digitaldelay import (             # noqa: E402
    clear_of_stalls)
from tools import effect_measurements as kit                # noqa: E402

VENDOR = "PyDevices"

TapeDelay = tape.TapeDelay

RATE = 48000
BLOCK = 256
TONE = 997.0
(TIME_I, FEEDBACK_I, MIX_I, GLIDE_I, WOW_I, FLUTTER_I, RECORD_I, SPACING_I,
 SPREAD_I, SYNC_I, DIVISION_I) = range(11)

#: Every Tier 2 row's Held fixed: wet only, no feedback, no wobble, no
#: squash, no spread (the rows name these; Time and Spacing vary per cell).
HELD = dict(mix=2.0, feedback=0.0, wow_cents=0.0, flutter_cents=0.0,
            record_level=0.0, spread=0.0)


# -- planted faults -------------------------------------------------------

class DoubleWalkTape(TapeDelay):
    """T1a: the varispeed walk at twice the tape equation's rate. The Glide
    law pins at 0.99 and the doubled rates here are 1.40-1.98, and no
    character hands varispeed anything but the tape equation."""

    NAME = 'TapeDelay'

    def _walk_rate(self, from_ms, to_ms):
        rate = TapeDelay._walk_rate(self, from_ms, to_ms)
        if self._character == tape.VARISPEED:
            return 2.0 * rate
        return rate


class GlideScaledVarispeed(TapeDelay):
    """Section 8.9: the varispeed walk multiplied by 6 000 / Glide, which
    would make Glide live on the character that must ignore it."""

    NAME = 'TapeDelay'

    def _walk_rate(self, from_ms, to_ms):
        rate = TapeDelay._walk_rate(self, from_ms, to_ms)
        if self._character == tape.VARISPEED:
            glide = self._glide_ms()
            if glide > 0.0:
                return rate * 6000.0 / glide
        return rate


class WalkAtZeroTape(TapeDelay):
    """Station B's step fault, Glide 0 handed slew 0.98 instead of the
    jump. Fix round 1: no longer a planted fault. The clean class built with
    `glide_ms=1180/0.98` (1 204.08 ms) hands the node the same 0.98 and
    renders the same bytes, so the state is a constructor value; it is kept
    as the control that shows the constructor walk can call a fault
    reachable."""

    NAME = 'TapeDelay'

    def _walk_rate(self, from_ms, to_ms):
        rate = TapeDelay._walk_rate(self, from_ms, to_ms)
        if self._character == tape.SLIDING_HEAD and rate <= 0.0:
            return 0.98
        return rate


class FastWalkAtZeroTape(TapeDelay):
    """T1b's step (fix round 1): Glide 0 handed slew 8 instead of the jump,
    so the read head walks between the two Times (598 frames for
    200 -> 100.4 ms at 48 kHz) where the class jumps. Sliding-head never
    hands more than the 0.99 pin, from the knob or the constructor."""

    NAME = 'TapeDelay'

    def _walk_rate(self, from_ms, to_ms):
        rate = TapeDelay._walk_rate(self, from_ms, to_ms)
        if self._character == tape.SLIDING_HEAD and rate <= 0.0:
            return 8.0
        return rate


class LoopShiftTape(TapeDelay):
    """T1b's gesture, varispeed: a loop pitch shift of 0.12 semitone, which
    the class never sets, so every pass round the loop is transposed."""

    NAME = 'TapeDelay'

    def _refresh(self):
        TapeDelay._refresh(self)
        self._delay.set(loop_semitones=0.12)


class DoubleCornerTape(TapeDelay):
    """T2: the loss corner at twice eq. (13)'s -3 dB point."""

    NAME = 'TapeDelay'

    def _corner_hz(self, time_ms, spacing_um):
        return 2.0 * TapeDelay._corner_hz(self, time_ms, spacing_um)


class PostLossTape(TapeDelay):
    """T2's n-pass clause: the loss taken out of the loop and put once on
    the wet output, through a second node one frame long, so every repeat
    carries one pass of loss instead of n."""

    NAME = 'TapeDelay'

    def _build(self, *arguments, **keywords):
        self._post = None
        TapeDelay._build(self, *arguments, **keywords)
        import audioecho
        self._post = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, max_delay_ms=1.0,
            delay_ms=1000.0 / self._sample_rate, feedback=0.0, mix=2.0,
            damping_hz=self._damping))
        self._post.play(self._delay)
        self._output = self._post
        self._refresh()

    def _refresh(self):
        TapeDelay._refresh(self)
        self._delay.set(damping_hz=0.0)
        if getattr(self, "_post", None) is not None:
            self._post.set(damping_hz=self._damping)


class SquareLawTape(TapeDelay):
    """T3, varispeed: the corner following the speed squared."""

    NAME = 'TapeDelay'

    def _corner_hz(self, time_ms, spacing_um):
        corner = TapeDelay._corner_hz(self, time_ms, spacing_um)
        if self._character == tape.VARISPEED:
            corner *= (tape.speed(tape.VARISPEED, time_ms)
                       / tape.speed(tape.VARISPEED, 350.0))
        return corner


class HalfFollowTape(TapeDelay):
    """T3, sliding-head: the corner following the square root of the
    varispeed speed, so the fixed transport's loss moves with Time."""

    NAME = 'TapeDelay'

    def _corner_hz(self, time_ms, spacing_um):
        corner = TapeDelay._corner_hz(self, time_ms, spacing_um)
        if self._character == tape.SLIDING_HEAD:
            corner *= math.sqrt(tape.speed(tape.VARISPEED, time_ms)
                                / tape.speed(tape.VARISPEED, 350.0))
        return corner


class FlutterOnWowLineTape(TapeDelay):
    """T4's two-line clause: the flutter component written at the wow
    line's harmonic (72) instead of its own (512), so the table carries one
    line in 0.2-12 Hz. No position reaches it: the clean table always puts
    Flutter at harmonic 512, and at Flutter 0 the wow line carries only the
    wow, with the drift at its fixed 0.25 ms per cent of Wow beside it."""

    NAME = 'TapeDelay'

    def _write_table(self, wow_cents, flutter_cents, out):
        return tape.wow_table(wow_cents, flutter_cents, out,
                              flutter_harmonic=tape.WOW_HARMONIC)


class NoFlutterLineTape(TapeDelay):
    """The first round's two-line fault, kept only to show the table walk
    can fail: the flutter line deleted while Flutter is up is the table the
    clean class writes at Flutter grid 0 (the reviewer's 0 differing
    samples), a macro position in disguise (pattern revision section 1.3).
    It is not a planted fault of any row."""

    NAME = 'TapeDelay'

    def _write_table(self, wow_cents, flutter_cents, out):
        return tape.wow_table(wow_cents, 0.0, out)


class Harmonic504Tape(TapeDelay):
    """T4's ratio clause: the flutter line at harmonic 504, exactly 7 x 72."""

    NAME = 'TapeDelay'

    def _write_table(self, wow_cents, flutter_cents, out):
        return tape.wow_table(wow_cents, flutter_cents, out,
                              flutter_harmonic=504)


class NoDriftTape(TapeDelay):
    """T4's slow-band clause: the table with the slow component zeroed,
    which the detector must read red-free."""

    NAME = 'TapeDelay'

    def _write_table(self, wow_cents, flutter_cents, out):
        return tape.wow_table(wow_cents, flutter_cents, out, drift=False)


class DialableTape(TapeDelay):
    """The reviewer's control for the walk itself: Spacing forced to 20 um,
    which Spacing MIDI 127 and patch 5 both play. Not a fault of any row;
    the damping reading must call it reachable."""

    NAME = 'TapeDelay'

    def _corner_hz(self, time_ms, spacing_um):
        return TapeDelay._corner_hz(self, time_ms, tape.SPACING_MAX_UM)


class _Stepper:
    """Pulls the owner's node, letting the owner move its delay from Python
    first: the finest a Python-driven Time can move is once per block
    (DigitalDelay's `_Stepper`)."""

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


class StaircaseTape(TapeDelay):
    """T1b's no-step clause: `delay_ms` stepped from Python once per
    256-frame block with the node's slew off, at the rate the character
    asks for. No position reaches it: Glide grid 0 is one jump, and every
    other position is the node's own per-frame walk, handed once per
    move."""

    NAME = 'TapeDelay'

    def _build(self, *arguments, **keywords):
        self._current_ms = None
        self._step_per_block = 0.0
        TapeDelay._build(self, *arguments, **keywords)
        self._output = _Stepper(self)

    def _refresh(self):
        TapeDelay._refresh(self)
        if self._current_ms is None or self._fresh:
            self._current_ms = self._node_ms
        self._step_per_block = self._slew * BLOCK * 1000.0 / self._sample_rate
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


class PerBlockSlidingTape(TapeDelay):
    """T1b's sliding-head repeats clause: the moves handed the tape
    equation's T(t) once per block (a motor, not a head), a per-block hook
    the class does not have. The speed in each block is L / T, T the Time
    last asked and L the Time the instance was built at; T at the block's
    end is the span back over which the tape ran L. With it the repeats
    after a gesture telescope back to the source, as a varispeed's do."""

    NAME = 'TapeDelay'

    def _build(self, *arguments, **keywords):
        self._speeds = None
        TapeDelay._build(self, *arguments, **keywords)
        self._length = float(self._frames)
        self._speeds = []
        self._current = float(self._frames)
        self._output = _Stepper(self)

    def _refresh(self):
        TapeDelay._refresh(self)
        if self._speeds is not None:
            self._delay.set(delay_slew=0.0,
                            delay_ms=self._current * 1000.0
                            / self._sample_rate)

    def _step(self):
        self._speeds.append(self._length / self._frames)
        remaining = self._length
        span = 0.0
        for speed in reversed(self._speeds):
            if speed * BLOCK >= remaining:
                span += remaining / speed
                remaining = 0.0
                break
            span += BLOCK
            remaining -= speed * BLOCK
        if remaining > 0.0:
            span += remaining / self._speeds[0]
        if span != self._current:
            slew = max(abs(span - self._current) / BLOCK, 1e-9)
            self._current = span
            self._delay.set(delay_slew=slew,
                            delay_ms=span * 1000.0 / self._sample_rate)


class SteppedTape(TapeDelay):
    """The workaround retired at audiodsp v0.6.3rc1: the Feedback handed to
    the node at the nearer edge of the loss low-pass's stall window
    (`clear_of_stalls`), a Feedback nobody set."""

    NAME = 'TapeDelay'

    def _refresh(self):
        TapeDelay._refresh(self)
        excess = tape.tone_excess(self._damping, self._sample_rate)[1]
        stepped = clear_of_stalls(self._feedback, excess)
        if stepped != self._feedback:
            self._feedback = stepped
            self._delay.set(feedback=stepped)


class NoneAtZeroTape(TapeDelay):
    """The class before audiodsp v0.6.3rc1: a Wow and Flutter of 0 hands the
    node no table, so the node ramps the old depth out (#160) on its own
    sine instead of the table's shape, a jump in the read offset."""

    NAME = 'TapeDelay'

    def _refresh(self):
        TapeDelay._refresh(self)
        if self._wow_ms == 0.0 and self._table is not None:
            self._table = None
            self._delay.set(wow_shape=None)


class LeanDriveOnTape(TapeDelay):
    """The lean patch with the drive left on: patch 8 plays patch 0's
    Record Level, so it names the saving and makes none (the cost
    ruling, 2026-09-28)."""

    NAME = 'TapeDelay'
    PATCHES = dict(TapeDelay.PATCHES)
    PATCHES[8] = ("Tape Delay - lean", TapeDelay.PATCHES[0][1])


class LeanMovesMoreTape(TapeDelay):
    """A lean patch that also moves Spacing: the drive is off, but it is no
    longer patch 0 with the drive off."""

    NAME = 'TapeDelay'
    PATCHES = dict(TapeDelay.PATCHES)
    PATCHES[8] = ("Tape Delay - lean",
                  (89, 58, 22, 89, 32, 32, 0, 60, 0, 0, 51))


class LeanResetTape(TapeDelay):
    """Not the contract: a reset that restores the lean patch instead of
    patch 0, so the drive stays off. The docstring says reset() brings it
    back; this is the build that sentence would be false on."""

    NAME = 'TapeDelay'

    def reset(self):
        TapeDelay.reset(self)
        self.program_change(8)


class DriveOffTape(TapeDelay):
    """Not a fault: the cost study's variant D, `loop_drive` handed 0 after
    every refresh (`DriveOff`). Built at
    `max_time_ms=800` it is variant K, the configuration the boards
    measured."""

    NAME = 'TapeDelay'

    def _refresh(self):
        TapeDelay._refresh(self)
        self._delay.set(loop_drive=0.0)


class JumpWowTape(TapeDelay):
    """A Wow or Flutter move that moves the read head by the whole change in
    depth at once, as the node did at the wobble's crest up to v0.6.2 (it
    added depth x table with no ramp)."""

    NAME = 'TapeDelay'

    def _refresh(self):
        old = self._wow_ms
        TapeDelay._refresh(self)
        if not self._seeding and not self._deferred and self._wow_ms != old:
            self._delay.set(delay_slew=0.0,
                            delay_ms=self._node_ms + self._wow_ms - old)


# -- sources and renders --------------------------------------------------

def src_of(x, channels=2, rate=RATE):
    """A float signal (frames,) as an int16 ArraySource, the same on every
    channel."""
    x = np.clip(np.round(np.asarray(x, dtype=float)), -32768, 32767)
    x = np.repeat(x.astype(np.int16)[:, None], channels, axis=1)
    return probes.ArraySource(array("h", x.reshape(-1).tobytes()),
                              rate=rate, channels=channels, block=BLOCK)


def sine(hz, amp, frames, rate=RATE):
    return amp * np.sin(2.0 * math.pi * hz * np.arange(frames) / rate)


def render(effect, frames, events=None):
    """Pull `frames` frames from the effect; `events` maps a frame to a
    callable applied to the effect before the block that starts there
    (the render pulls whole blocks). Returns (frames, channels) float."""
    channels = effect.channel_count
    events = sorted((events or {}).items())
    out = []
    done = 0
    while done < frames:
        while events and events[0][0] <= done:
            events.pop(0)[1](effect)
        data = bytes(audiocore.get_buffer(effect.output)[1])
        if not data:
            break
        block = np.frombuffer(data, dtype=np.int16).reshape(-1, channels)
        out.append(block)
        done += block.shape[0]
    y = np.concatenate(out)[:frames].astype(float)
    if y.shape[0] < frames:
        y = np.vstack([y, np.zeros((frames - y.shape[0], channels))])
    return y


def time_midi(ms):
    """Time as a float MIDI value, so `set_macro` lands on `ms`."""
    return _component.macro_position(TapeDelay._MACRO_RANGES[TIME_I],
                                     ms) * 127.0


def set_time(ms):
    return lambda effect: effect.set_macro(TIME_I, time_midi(ms))


def frames_of(ms, rate=RATE):
    return int(math.floor(ms * rate / 1000.0 + 0.5))


def cents(ratio):
    return 1200.0 * math.log2(ratio)


# -- estimators -----------------------------------------------------------

def _fit(seg, rate, hz):
    n = np.arange(len(seg))
    a = np.stack([np.cos(2 * np.pi * hz * n / rate),
                  np.sin(2 * np.pi * hz * n / rate), np.ones(len(seg))], 1)
    coef, *_ = np.linalg.lstsq(a, seg, rcond=None)
    r = seg - a @ coef
    return float(r @ r), coef


def peak_hz(x, rate, pad=16):
    x = np.asarray(x, dtype=float)
    x = (x - x.mean()) * np.hanning(len(x))
    n = len(x) * pad
    s = np.abs(np.fft.rfft(x, n))
    i = int(np.argmax(s[1:])) + 1
    a, b, c = (math.log(s[i - 1] + 1e-30), math.log(s[i] + 1e-30),
               math.log(s[i + 1] + 1e-30))
    denom = a - 2 * b + c
    p = 0.5 * (a - c) / denom if denom != 0.0 else 0.0
    return (i + p) * rate / n


def lsq_hz(seg, rate):
    """Least-squares sine with a DC term: the search starts at the
    segment's own spectral peak and takes no law (the Station A critique's
    estimator)."""
    seg = np.asarray(seg, dtype=float)
    if len(seg) < 16 or not np.any(seg):
        return float("nan")
    f0 = peak_hz(seg, rate)
    span = 1.5 * rate / len(seg)
    a, b = max(1.0, f0 - span), f0 + span
    g = (math.sqrt(5) - 1) / 2
    x1, x2 = b - g * (b - a), a + g * (b - a)
    e1, e2 = _fit(seg, rate, x1)[0], _fit(seg, rate, x2)[0]
    for _ in range(50):
        if e1 < e2:
            b, x2, e2 = x2, x1, e1
            x1 = b - g * (b - a)
            e1 = _fit(seg, rate, x1)[0]
        else:
            a, x1, e1 = x1, x2, e2
            x2 = a + g * (b - a)
            e2 = _fit(seg, rate, x2)[0]
    return 0.5 * (a + b)


def analytic(x):
    x = np.asarray(x, dtype=float)
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


def ifreq(x, rate):
    return np.diff(np.unwrap(np.angle(analytic(x)))) * rate / (2 * math.pi)


# -- T1: one Time move ----------------------------------------------------

def start_of(from_ms, rate):
    return max(20480, (frames_of(from_ms, rate) + 9600) // BLOCK * BLOCK)


def steady_slope(hz, time_ms, character, rate=RATE, amp=12000.0,
                 spacing_um=5.0):
    """The largest first difference a steady tone at `hz` makes through the
    class at `time_ms`, unramped: a tone's own slope through the corner in
    force."""
    frames = frames_of(time_ms, rate) + int(0.3 * rate)
    effect = TapeDelay(src_of(sine(hz, amp, frames, rate), 1, rate),
                       time_ms=time_ms, character=character,
                       spacing_um=spacing_um, **HELD)
    y = render(effect, frames)[:, 0]
    return float(np.max(np.abs(np.diff(y[frames_of(time_ms, rate) + 2000:]))))


def move(cls, a, b, rate=RATE, character=tape.VARISPEED, amp=12000.0,
         channels=1, after_ms=400.0, **options):
    """A 997 Hz tone through one Time move a -> b issued on a block
    boundary once the wet tone is established. Returns the left channel,
    the move's frame and the effect."""
    opts = dict(HELD)
    opts.update(options)
    start = start_of(a, rate)
    frames = start + int(abs(frames_of(b, rate) - frames_of(a, rate)) * 3
                         + rate * after_ms / 1000.0) + 2 * rate
    effect = cls(src_of(sine(TONE, amp, frames, rate), channels, rate),
                 time_ms=a, character=character, **opts)
    y = render(effect, frames, {start: set_time(b)})[:, 0]
    return y, start, effect


def t1a_cell(cls, a, b, rate=RATE, amp=12000.0):
    """T1a's clauses on one move: the pitch over the walk against
    1200 log2(T_old / T_new), the hold against T_new, the residual
    50-250 ms after, and the walk's first differences against the shifted
    tone's own slope."""
    y, start, effect = move(cls, a, b, rate, amp=amp)
    ta, tb = frames_of(a, rate), frames_of(b, rate)
    law_c = cents(ta / float(tb))
    law_hz = TONE * ta / float(tb)
    walk = tb                        # the tape equation: the move lasts T_new
    trim = min(400, walk // 10)
    got = lsq_hz(y[start + trim:start + walk - trim], rate)
    err = cents(got / law_hz) if got == got else float("inf")
    # The hold: from where the pitch passes half way (in cents) to the law
    # on the way in to where it passes back on the way out. The smoothing
    # and the low-pass's settle spread both edges alike, so they cancel.
    fi = ifreq(y[start - 2000:start + 3 * walk], rate)
    k = max(1, int(0.001 * rate))
    fi = np.convolve(fi, np.ones(k) / k, mode="same")[k:-k]
    shift = 1200.0 * np.log2(np.maximum(fi, 1e-9) / TONE)
    past = np.nonzero(shift * math.copysign(1.0, law_c) > abs(law_c) / 2)[0]
    hold = int(past[-1] - past[0] + 1) if len(past) else 0
    after = y[start + walk + int(0.05 * rate):start + walk + int(0.25 * rate)]
    res = lsq_hz(after, rate)
    residual = cents(res / TONE) if res == res else float("inf")
    tau = rate / (2 * math.pi * effect._damping)
    settle = int(math.ceil(5 * tau))
    body = y[start + settle:start + walk - 64]
    bar = 1.05 * steady_slope(law_hz, b, tape.VARISPEED, rate, amp)
    step = float(np.max(np.abs(np.diff(body)))) / bar if len(body) > 2 \
        else 0.0
    red = (abs(err) > 10.0 or abs(hold - walk) > 0.05 * walk
           or abs(residual) > 1.0 or step > 1.0)
    return dict(passed=not red, err=err, law=law_c, hold=hold, walk=walk,
                residual=residual, step=step)


class TheSurface(unittest.TestCase):
    def test_macros_characters_tier_latency(self):
        self.assertEqual(TapeDelay.MACRO_LABELS, (
            "Time", "Feedback", "Mix", "Glide", "Wow", "Flutter",
            "Record Level", "Spacing", "Spread", "Sync", "Division"))
        self.assertEqual(TapeDelay.MACRO_MODES[SYNC_I], "TOGGLE")
        self.assertEqual(len(TapeDelay.PATCHES), 9)
        self.assertEqual(TapeDelay.CAPABILITIES, ("tempo_sync",))
        self.assertEqual(TapeDelay.LATENCY_SAMPLES, 0)
        self.assertEqual(TapeDelay.TIER, _component.AUDIODSP)
        self.assertEqual(TapeDelay.REQUIRES, ("audioecho",))
        self.assertEqual(tape.CHARACTERS, ("varispeed", "sliding-head"))
        for character in tape.CHARACTERS:
            effect = TapeDelay(src_of(np.zeros(512)), character=character)
            self.assertEqual(effect.latency_samples, 0)
            self.assertEqual(effect.patch_index, 0)
        with self.assertRaises(ValueError):
            TapeDelay(src_of(np.zeros(512)), character="reel")

    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-09-29, so `create()` serves this one. It was the
        reverse assertion while the class was parked; revert
        `rebuilt.ADOPTED` and this goes red."""
        import audioeffects
        self.assertIs(rebuilt.module_class("TapeDelay"), TapeDelay)
        self.assertIn("TapeDelay", rebuilt.ADOPTED)
        self.assertNotIn("TapeDelay", rebuilt.parked())
        self.assertIs(rebuilt.load("TapeDelay"), TapeDelay)
        self.assertIs(audioeffects.TapeDelay, TapeDelay)
        served = audioeffects.create("TapeDelay", src_of(np.zeros(64)), RATE)
        self.assertIsInstance(served, TapeDelay)
        served.deinit()

    def test_patches_are_the_dossier_settings_on_the_grid(self):
        # Section 6's table: Time, Fdbk, Mix, Glide, Wow, Flutter, Rec,
        # Spacing, Spread, Sync, Div (as an index).
        settings = (
            (350.0, 0.45, 0.35, 6000.0, 2.0, 1.0, 0.2, 5.0, 0.0, 0.0, 6.0),
            (800.0, 0.55, 0.35, 12000.0, 2.0, 1.0, 0.2, 5.0, 0.0, 0.0, 6.0),
            (90.0, 0.15, 0.50, 6000.0, 1.0, 0.5, 0.2, 5.0, 0.0, 0.0, 6.0),
            (450.0, 0.55, 0.35, 6000.0, 6.0, 2.0, 0.2, 15.0, 0.0, 0.0, 6.0),
            (400.0, 0.90, 0.40, 6000.0, 2.0, 1.0, 0.6, 5.0, 0.0, 0.0, 6.0),
            (350.0, 0.45, 0.35, 6000.0, 4.0, 3.0, 0.5, 20.0, 0.0, 0.0, 6.0),
            (350.0, 0.45, 0.35, 6000.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 6.0),
            (350.0, 0.45, 0.35, 6000.0, 2.0, 1.0, 0.2, 5.0, 0.0, 1.0, 8.0),
            (350.0, 0.45, 0.35, 6000.0, 2.0, 1.0, 0.0, 5.0, 0.0, 0.0, 6.0),
        )
        for index, values in enumerate(settings):
            want = tuple(
                _component.macro_of(span, value, TapeDelay.MACRO_MODES[i])
                for i, (span, value) in enumerate(
                    zip(TapeDelay._MACRO_RANGES, values)))
            self.assertEqual(TapeDelay.PATCHES[index][1], want, index)

    def test_patch_0_is_the_constructor_grid(self):
        effect = TapeDelay(src_of(np.zeros(512)))
        for index, expected in enumerate(TapeDelay.PATCHES[0][1]):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_time_lands_on_a_whole_frame(self):
        for rate, frames in ((48000, 16800), (44100, 15435), (22050, 7718)):
            effect = TapeDelay(src_of(np.zeros(512), rate=rate))
            self.assertEqual(effect._frames, frames)
            self.assertEqual(effect._node_ms, frames * 1000.0 / rate)
            # A host echoing Time back keeps the constructor's exact Time.
            effect.set_macro(TIME_I, effect.get_macro(TIME_I))
            self.assertEqual(effect._frames, frames)

    def test_the_loss_corner(self):
        # Eq. (13)'s half-power wavelength: 393.5 um at 5, 336.7 at 2 and
        # 671.4 at 20 (dossier section 6).
        for spacing, wavelength in ((5.0, 393.5), (2.0, 336.7),
                                    (20.0, 671.4)):
            k3 = tape.k3_of(spacing * 1e-6)
            self.assertAlmostEqual(2 * math.pi / k3 * 1e6, wavelength,
                                   delta=0.05)
        # 22.05 kHz: 521.85 and 515.49 Hz (the dossier rounds the first to
        # 521.9).
        for rate, varispeed, sliding in ((48000, 522.6, 516.2),
                                         (22050, 521.85, 515.49)):
            got = [TapeDelay(src_of(np.zeros(512), rate=rate),
                             character=c)._damping
                   for c in tape.CHARACTERS]
            self.assertAlmostEqual(got[0], varispeed, delta=0.05)
            self.assertAlmostEqual(got[1], sliding, delta=0.05)
        # The speed law: 40 cm/s to 180 ms, 12 cm/s from 600 ms.
        self.assertEqual(tape.speed(tape.VARISPEED, 60.0), 0.40)
        self.assertEqual(tape.speed(tape.VARISPEED, 1200.0), 0.12)
        self.assertAlmostEqual(tape.speed(tape.VARISPEED, 350.0), 0.20571,
                               places=5)
        self.assertEqual(tape.speed(tape.SLIDING_HEAD, 60.0), 0.2032)

    def test_the_wow_table(self):
        effect = TapeDelay(src_of(np.zeros(512)))
        self.assertAlmostEqual(effect._wow_ms, 0.758, delta=0.001)
        table = effect._table
        self.assertEqual(len(table), 4096)
        self.assertEqual(max(abs(v) for v in table), 32767)
        first = table
        effect.set_macro(WOW_I, 127)
        # A move writes the table the node is not reading.
        self.assertIsNot(effect._table, first)
        effect.set_macro(FLUTTER_I, 127)
        self.assertIs(effect._table, first)
        # The stops: 1.024 + 0.072 + 2.000 ms of components, 3.034 ms peak.
        self.assertAlmostEqual(effect._wow_ms, 3.034, delta=0.001)
        self.assertAlmostEqual(tape.cents_to_depth_ms(8.0, 0.72), 1.024,
                               delta=0.0005)
        self.assertAlmostEqual(tape.cents_to_depth_ms(4.0, 5.12), 0.072,
                               delta=0.0005)
        # Down to 0 on a playing node the last table stays handed, so the
        # depth the node ramps out over 20 ms (audiodsp#160) leaves on its
        # own shape; at depth 0 the table moves nothing.
        effect.set_macro(WOW_I, 0)
        effect.set_macro(FLUTTER_I, 0)
        self.assertEqual(effect._wow_ms, 0.0)
        self.assertIsNotNone(effect._table)
        # Planted: the class before v0.6.3rc1 dropped it.
        dropped = NoneAtZeroTape(src_of(np.zeros(512)))
        dropped.set_macro(WOW_I, 0)
        dropped.set_macro(FLUTTER_I, 0)
        self.assertIsNone(dropped._table)
        # A fresh node snaps onto its depth, so a constructor or patch at 0
        # hands no table at all.
        for effect in (TapeDelay(src_of(np.zeros(512)), wow_cents=0.0,
                                 flutter_cents=0.0),
                       TapeDelay(src_of(np.zeros(512)), patch=6)):
            self.assertIsNone(effect._table)
            self.assertEqual(effect._wow_ms, 0.0)

    def test_the_table_holds_its_three_components(self):
        out = array("h", [0] * 4096)
        depth = tape.wow_table(8.0, 4.0, out)
        spec = np.abs(np.fft.rfft(np.array(out, dtype=float))) \
            * depth / 32767.0 * 2.0 / 4096.0
        self.assertAlmostEqual(spec[72], 1.024, delta=0.002)
        self.assertAlmostEqual(spec[512], 0.072, delta=0.002)
        drift = spec[1:10] * np.arange(1, 10)
        self.assertLess(float(np.ptp(drift)), 0.002)
        self.assertGreater(float(np.sum(spec[1:10])), 0.5)
        others = np.delete(spec[1:], [k - 1 for k in
                                      list(range(1, 10)) + [72, 512]])
        self.assertLess(float(np.max(others)), 0.0005)

    def test_tail_samples_at_each_patch_played_from_rest(self):
        # Dossier Tier 3 and App. F7', varispeed, 48 kHz. Patch 7 at the
        # static transport keeps its knob Time (patch 0's). At a 120 bpm host
        # it plays 1/8. = 0.75 beat = 375 ms: App. F7' sized it at 187.5 ms,
        # which is 1/16. at 120 bpm, so its 128 982 frames is not the bound
        # this patch needs; the class's is 257 418.
        want = (241990, 692550, 27336, 407322, 1671015, 245728, 240800,
                241990, 241990)
        for index, frames in enumerate(want):
            effect = TapeDelay(src_of(np.zeros(512)), patch=index)
            self.assertEqual(effect.tail_samples, frames, index)
        effect = TapeDelay.create(src_of(np.zeros(512)), RATE,
                                  transport=lambda: (True, 0.0, 120.0, 4, 4),
                                  patch=7)
        self.assertAlmostEqual(effect._time_played, 375.0, places=6)
        memory, excess = tape.tone_excess(effect._damping, RATE)
        laps = tape.laps_to_zero(effect._feedback, excess)
        self.assertEqual(effect.tail_samples,
                         laps * (18000 + 37 + 1 + memory))
        self.assertEqual(effect.tail_samples, 257418)
        effect = TapeDelay(src_of(np.zeros(512)))
        self.assertEqual(effect.tail_samples, 240282)

    def test_the_glide_law_and_its_floor(self):
        effect = TapeDelay(src_of(np.zeros(512)), character="sliding-head")
        self.assertAlmostEqual(effect._slew, 1180.0 / 6000.0, places=12)
        effect.set_macro(GLIDE_I, 1)
        self.assertAlmostEqual(effect._slew, 0.965666, places=5)
        effect.set_macro(GLIDE_I, 127)
        self.assertAlmostEqual(effect._slew, 1180.0 / 12000.0, places=12)
        effect.set_macro(GLIDE_I, 0)
        self.assertEqual(effect._slew, 0.0)
        # A constructor Glide faster than grid 1 keeps its walk (the 0.99
        # pin) and seeds the knob at grid 1, never grid 0, the jump.
        fast = TapeDelay(src_of(np.zeros(512)), character="sliding-head",
                         glide_ms=1000.0)
        self.assertEqual(fast._slew, 0.99)
        self.assertAlmostEqual(fast.get_macro(GLIDE_I), 1.0, places=9)
        fast.set_macro(GLIDE_I, round(fast.get_macro(GLIDE_I)))
        self.assertGreater(fast._slew, 0.0)
        for jump in (0.0, -5.0, float("nan")):
            self.assertEqual(TapeDelay(src_of(np.zeros(512)),
                                       character="sliding-head",
                                       glide_ms=jump)._slew, 0.0)

    def test_constructor_clamps_and_nan(self):
        effect = TapeDelay(src_of(np.zeros(512)), time_ms=0.0, spacing_um=0.0,
                           max_time_ms=float("nan"), feedback=float("nan"))
        self.assertEqual(effect._frames, frames_of(20.0))
        self.assertAlmostEqual(effect.macro(SPACING_I), 2.0, places=9)
        self.assertEqual(effect._max_time_ms, 1200.0)
        self.assertAlmostEqual(effect.macro(FEEDBACK_I), 0.45, places=9)
        low = TapeDelay(src_of(np.zeros(512)), time_ms=900.0,
                        max_time_ms=300.0)
        self.assertEqual(low._frames, frames_of(300.0))
        self.assertAlmostEqual(low.macro(TIME_I), 300.0, places=6)
        low.set_macro(TIME_I, 127)
        self.assertAlmostEqual(low.macro(TIME_I), 300.0, places=6)

    def test_spread_is_held_at_zero_in_mono(self):
        mono = TapeDelay(src_of(np.zeros(512), channels=1), spread=1.0)
        self.assertEqual(mono._spread, 0.0)
        stereo = TapeDelay(src_of(np.zeros(512)), spread=1.0)
        self.assertEqual(stereo._spread, 1.0)


LEAN = 8


def lean_surface(cls):
    """(the lean patch's name, the positions where it differs from patch 0
    as {index: (patch 0, lean)})."""
    name, lean = cls.PATCHES[LEAN]
    full = cls.PATCHES[0][1]
    return name, {i: (a, b) for i, (a, b) in enumerate(zip(full, lean))
                  if a != b}


def lean_handed(cls, **ctor):
    """What the node is handed at the lean patch and at patch 0, as
    {option: (patch 0, lean)} for every option that differs; a table is
    compared point by point."""
    def state(patch):
        effect = cls(src_of(np.zeros(512)), patch=patch, **ctor)
        handed = dict(effect._delay._handed)
        effect.deinit()
        if handed.get("wow_shape") is not None:
            handed["wow_shape"] = tuple(handed["wow_shape"])
        return handed
    with NodeSpy():
        full, lean = state(0), state(LEAN)
    return {k: (full.get(k), lean.get(k)) for k in set(full) | set(lean)
            if full.get(k) != lean.get(k)}


def lean_render(cls, patch=LEAN, **ctor):
    """A 997 Hz tone at -1 dBFS for 300 ms, then silence, through `patch`,
    one second at 48 kHz stereo: loud enough that the drive shows on every
    repeat."""
    x = np.zeros(RATE)
    x[:int(0.3 * RATE)] = sine(TONE, 29205.0, int(0.3 * RATE))
    return render(cls(src_of(x), patch=patch, **ctor), RATE)


class LeanPatch(unittest.TestCase):
    """The cost ruling of 2026-09-28: keep the class and add a lean
    patch. Patch 8 `Tape Delay - lean` is patch 0 with Record Level 0, and
    with `max_time_ms=800` it is the cost study's variant K, which met the
    P4 and S3 bars in every run."""

    def test_the_lean_patch_is_patch_0_with_the_drive_off(self):
        name, moved = lean_surface(TapeDelay)
        self.assertEqual(name, "Tape Delay - lean")
        self.assertTrue(name.endswith(" - lean"))
        self.assertEqual(moved, {RECORD_I: (25, 0)})
        # What the node is handed: the drive off, and nothing else moved.
        handed = lean_handed(TapeDelay)
        self.assertEqual(set(handed), {"loop_drive"})
        self.assertGreater(handed["loop_drive"][0], 0.19)
        self.assertEqual(handed["loop_drive"][1], 0.0)
        self.assertEqual(lean_handed(TapeDelay, max_time_ms=800.0),
                         lean_handed(TapeDelay))
        # Planted: the drive left on, and a lean patch that moves more.
        self.assertEqual(lean_handed(LeanDriveOnTape), {})
        self.assertNotEqual(lean_surface(LeanDriveOnTape)[1],
                            {RECORD_I: (25, 0)})
        self.assertIn("damping_hz", lean_handed(LeanMovesMoreTape))
        self.assertNotEqual(lean_surface(LeanMovesMoreTape)[1],
                            {RECORD_I: (25, 0)})

    def test_the_lean_build_renders_what_the_boards_measured(self):
        lean = lean_render(TapeDelay, max_time_ms=800.0)
        self.assertGreater(float(np.max(np.abs(lean[int(0.4 * RATE):]))),
                           1000.0)
        # Variant K at patch 0 is the cell the boards timed; patch 8 at the
        # 800 ms line renders it byte for byte, and so does patch 8 on the
        # full line (the shorter line moves no byte at this Time).
        k = lean_render(DriveOffTape, 0, max_time_ms=800.0)
        self.assertEqual(lean.tobytes(), k.tobytes())
        self.assertEqual(lean.tobytes(), lean_render(TapeDelay).tobytes())
        # The drive is what the lean patch drops: patch 0 differs.
        self.assertNotEqual(lean.tobytes(),
                            lean_render(TapeDelay, 0).tobytes())
        # Planted: the drive left on renders patch 0, not variant K.
        on = lean_render(LeanDriveOnTape, max_time_ms=800.0)
        self.assertNotEqual(on.tobytes(), k.tobytes())
        # The 800 ms build stops Time there, where get_macro(0) shows it.
        effect = TapeDelay(src_of(np.zeros(512)), patch=LEAN,
                           max_time_ms=800.0)
        effect.set_macro(TIME_I, 127)
        self.assertAlmostEqual(effect.macro(TIME_I), 800.0, places=6)
        self.assertEqual(effect._frames, frames_of(800.0))

    def _drive_across_reset(self, cls):
        """(Record Level MIDI and the drive handed) on the lean patch at the
        800 ms build, after `reset()`, and after `program_change(8)`."""
        readings = []
        with NodeSpy():
            effect = cls(src_of(np.zeros(512)), patch=LEAN,
                         max_time_ms=800.0)
            for step in (None, effect.reset,
                         lambda: effect.program_change(LEAN)):
                if step is not None:
                    step()
                readings.append((effect.get_macro(RECORD_I),
                                 round(effect._delay._handed["loop_drive"],
                                       5)))
            effect.deinit()
        return readings

    def test_reset_brings_the_drive_back(self):
        # Re-audit fix round 2, the docstring's restated sentence: reset()
        # restores patch 0 (the component contract), so the drive and its
        # cost come back and a board calls program_change(8) after it.
        self.assertEqual(self._drive_across_reset(TapeDelay),
                         [(0.0, 0.0), (25.0, 0.19685), (0.0, 0.0)])
        # Planted: a reset that restored the lean patch would make the
        # sentence false; the reading sees it.
        self.assertEqual(self._drive_across_reset(LeanResetTape)[1],
                         (0.0, 0.0))


class T1aVarispeed(unittest.TestCase):
    def test_the_named_moves(self):
        for rate, a, b in ((48000, 200.0, 100.4), (48000, 180.0, 600.0),
                           (48000, 40.0, 20.0), (22050, 200.0, 100.4),
                           (44100, 600.0, 180.0)):
            got = t1a_cell(TapeDelay, a, b, rate)
            self.assertTrue(got["passed"], (rate, a, b, got))
        got = t1a_cell(TapeDelay, 200.0, 100.4)
        self.assertAlmostEqual(got["law"], 1193.2, delta=0.05)
        self.assertLess(abs(got["err"]), 1.0)

    def test_the_level_span(self):
        for amp in (380.0, 32000.0):
            got = t1a_cell(TapeDelay, 200.0, 100.4, 48000, amp)
            self.assertTrue(got["passed"], (amp, got))

    def test_a_doubled_walk_is_red(self):
        for rate, a, b in ((48000, 200.0, 100.4), (22050, 180.0, 600.0)):
            got = t1a_cell(DoubleWalkTape, a, b, rate)
            self.assertFalse(got["passed"], got)
            self.assertGreater(abs(got["err"]), 400.0)

    def test_the_top_binade_per_piece(self):
        # Fix round 1 (dossier T1a, revised under vision 7.2): a rising
        # move from rest whose walk passes 32 768 frames is claimed to a
        # ratio of 2.95 : 1. The node rounds each step of its float32 walk
        # to the read head's ulp (2^-8 frames up there), and past that
        # ratio the top piece can read over 10 c. The claimed edge cell is
        # the float32 model's worst claimed move (408.90 -> 1 196.31 ms,
        # ratio 2.926, model -9.92 c); 333 -> 1 100 ms (ratio 3.30) is the
        # span refuter's excluded cell, red on its top piece.
        for a, b, red in ((19627 / 48.0, 57423 / 48.0, False),
                          (333.0, 1100.0, True)):
            law = TONE * frames_of(a) / float(frames_of(b))
            got = walk_cell(TapeDelay, a, b, RATE, tape.VARISPEED, law)
            self.assertEqual(got["unread"], 0, got)
            self.assertEqual(got["passed"], not red, (a, b, got))
        self.assertAlmostEqual(got["worst"], -11.16, delta=0.05)


class GlideIsInertOnVarispeed(unittest.TestCase):
    """Section 8.9: one varispeed Time move at Glide grid 1, grid 127 and
    the constructor's 6 000 ms renders byte-identical, and the fault that
    scales the walk by 6 000 / Glide does not."""

    def _renders(self, cls):
        out = []
        for glide in (None, 1, 127):
            opts = dict(HELD)
            frames = 20480 + 3 * RATE // 4
            effect = cls(src_of(sine(TONE, 12000.0, frames), 2),
                         time_ms=200.0, **opts)
            if glide is not None:
                effect.set_macro(GLIDE_I, glide)
            out.append(render(effect, frames,
                              {20480: set_time(100.4)}).tobytes())
        return out

    def test_three_glides_one_render(self):
        a, b, c = self._renders(TapeDelay)
        self.assertEqual(a, b)
        self.assertEqual(a, c)

    def test_a_glide_scaled_walk_is_red(self):
        a, b, c = self._renders(GlideScaledVarispeed)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)


#: How far either side of the nominal walk end the edge window reaches: the
#: float32 walk lands -65 to +16 frames off it (dossier App. F1').
WALK_SLACK = 128


def ramp_walk_end(cls, a, b, rate, character, start, **options):
    """Where the read head stops, read off a render of the same move with
    a slope-1/k ramp in place of the tone (DigitalDelay's `walk_end_ramp`):
    the wet output is the ramp delayed, so D[n] = n - k (y[n] + 30 000) is
    the delay in frames to within k, plus the loss low-pass's constant lag.
    The walk ends at the last frame whose D is more than 2k + 2 frames off
    the settled D of the render's last 0.2 s."""
    opts = dict(HELD)
    opts.update(options)
    slew = abs(frames_of(b, rate) - frames_of(a, rate))
    frames = start + int(slew * 12) + rate // 2
    k = max(1, -(-frames // 60000))
    ramp = np.arange(frames) // k - 30000.0
    effect = cls(src_of(ramp, 1, rate), time_ms=a, character=character,
                 **opts)
    y = render(effect, frames, {start: set_time(b)})[:, 0]
    d = np.arange(frames) - k * (y + 30000.0)
    settled = float(np.median(d[-rate // 5:]))
    off = np.nonzero(np.abs(d[start:] - settled) > 2 * k + 2)[0]
    return start + (int(off[-1]) + 1 if len(off) else 0)


def no_step(y, start, end, a, b, law_hz, rate, amp, character, damping):
    """T1b's no-step clause, T1a's three windows: inside the walk, the
    shifted tone's own slope at T_new through the corner in force; in the
    first five time constants after either end, DigitalDelay's signed law
    max(1, ratio) x the unfiltered unramped maximum; before and after, the
    997 Hz tone's own slope at each Time. Each bar plus 5 %. Returns each
    window's largest first difference over its bar, in that order. The
    before window's bar is the same tone's own render, so it reads
    1 / 1.05 exactly on a clean class; the four after it are the clause."""
    settle = int(math.ceil(5 * rate / (2 * math.pi * damping)))
    raw = 2.0 * math.pi * TONE / rate * amp
    signed = max(1.0, law_hz / TONE) * raw
    windows = (
        (start - 4000, start, steady_slope(TONE, a, character, rate, amp)),
        (start, start + settle, signed),
        (start + settle, end - WALK_SLACK,
         steady_slope(law_hz, b, character, rate, amp)),
        (end - WALK_SLACK, end + settle + WALK_SLACK, signed),
        (end + settle + WALK_SLACK, end + settle + WALK_SLACK + rate // 5,
         steady_slope(TONE, b, character, rate, amp)))
    out = []
    for lo, hi, bar in windows:
        got = float(np.max(np.abs(np.diff(y[lo:hi])))) if hi - lo > 2 \
            else 0.0
        out.append(got / (1.05 * bar))
    return out


def glide_cell(cls, grid, a, b, rate=RATE, amp=12000.0):
    """One of T1b's Glide-grid cells, sliding-head: each binade piece's
    pitch against 1 - dT/dt written from the Glide asked (never the class's
    slew function), the residual 50-250 ms after, and the no-step clause."""
    law = 1180.0 / _component.macro_value(TapeDelay._MACRO_RANGES[GLIDE_I],
                                          grid / 127.0)
    start = start_of(a, rate)
    frames = start + 3 * rate
    effect = cls(src_of(sine(TONE, amp, frames, rate), 1, rate), time_ms=a,
                 character=tape.SLIDING_HEAD, **HELD)
    effect.set_macro(GLIDE_I, grid)
    y = render(effect, frames, {start: set_time(b)})[:, 0]
    fa, fb = frames_of(a, rate), frames_of(b, rate)
    walk = int(abs(fb - fa) / law)
    want = TONE * (1.0 + law if b < a else 1.0 - law)
    pieces = []
    edges = [start]
    power = 1 << int(math.log2(max(fa, fb)))
    if min(fa, fb) < power < max(fa, fb):
        edges.append(start + int(abs(power - fa) / law))
    edges.append(start + walk)
    for lo, hi in zip(edges[:-1], edges[1:]):
        trim = min(400, (hi - lo) // 10)
        got = lsq_hz(y[lo + trim:hi - trim], rate)
        pieces.append(cents(got / want) if got == got else float("inf"))
    after = lsq_hz(y[start + walk + int(0.05 * rate):
                     start + walk + int(0.25 * rate)], rate)
    residual = cents(after / TONE) if after == after else float("inf")
    end = ramp_walk_end(TapeDelay, a, b, rate, tape.SLIDING_HEAD, start,
                        glide_ms=_component.macro_value(
                            TapeDelay._MACRO_RANGES[GLIDE_I], grid / 127.0))
    windows = no_step(y, start, end, a, b, want, rate, amp,
                      tape.SLIDING_HEAD, effect._damping)
    step = max(windows)
    red = (max(abs(p) for p in pieces) > 10.0 or abs(residual) > 1.0
           or step > 1.0)
    return dict(passed=not red, pieces=pieces, residual=residual, step=step,
                windows=windows, walk=walk, end=end - start)


def ramp_cell(cls, rate=RATE, amp=12000.0):
    """T1b's ramp: sliding-head, Glide 2 950 ms (slew 0.4), 200 -> 400 ms.
    The walk is 24 000 frames; the pitch -884.4 cents while it walks. The
    pitch, the residual and the no-step clause."""
    y, start, effect = move(cls, 200.0, 400.0, rate, tape.SLIDING_HEAD, amp,
                            glide_ms=2950.0)
    law_slew = 1180.0 / 2950.0
    walk = int(round((frames_of(400.0, rate) - frames_of(200.0, rate))
                     / law_slew))
    trim = min(400, walk // 10)
    law = TONE * (1.0 - law_slew)
    got = lsq_hz(y[start + trim:start + walk - trim], rate)
    err = cents(got / law) if got == got else float("inf")
    after = lsq_hz(y[start + walk + int(0.05 * rate):
                     start + walk + int(0.25 * rate)], rate)
    residual = cents(after / TONE) if after == after else float("inf")
    end = ramp_walk_end(TapeDelay, 200.0, 400.0, rate, tape.SLIDING_HEAD,
                        start, glide_ms=2950.0)
    windows = no_step(y, start, end, 200.0, 400.0, law, rate, amp,
                      tape.SLIDING_HEAD, effect._damping)
    step = max(windows)
    return dict(passed=abs(err) <= 10.0 and abs(residual) <= 1.0
                and step <= 1.0, err=err, residual=residual, step=step,
                windows=windows,
                law=cents(law / TONE), end=end - start, walk=walk)


#: Fix round 1: a binade piece counts only when its two readings - the
#: read head's slope off the ramp render and the least-squares sine on the
#: tone - both exist and agree within PIECE_AGREE cents. The span refuter
#: read -215.6 c off the ramp slope alone on a 45-frame piece (grid 1,
#: 41.7 -> 55.7 ms), where no sine fits; such a piece is reported unread.
PIECE_AGREE = 1.0

#: The sine is fitted on at most this many frames from the middle of a
#: piece: the pitch is constant inside a binade, and a long piece costs
#: time and says nothing more.
PIECE_FIT_MAX = 24000


def binade_pieces(y, d, ok, start, end, fa, fb, law_hz, rate):
    """The walk start..end cut where the read head crosses a power of two
    (inside a binade the node rounds each step to the head's float32 ulp,
    so each binade plays its own rate), each piece read two ways in cents
    off `law_hz`. Returns [(frames, ramp cents, sine cents, read)], `read`
    True when both readings exist and agree within PIECE_AGREE."""
    edges = [start]
    lo_f, hi_f = min(fa, fb), max(fa, fb)
    p = 1
    while p <= hi_f:
        if lo_f < p < hi_f:
            seg = d[start:end]
            idx = np.nonzero(((seg - p) * np.sign(fb - fa) >= 0)
                             & ok[start:end])[0]
            if len(idx):
                edges.append(start + int(idx[0]))
        p <<= 1
    edges.append(end)
    edges = sorted(set(edges))
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        n = hi - lo
        ramp_c = float("nan")
        if n > 8:
            idx = np.arange(lo + 2, hi - 2)
            idx = idx[ok[idx]]
            if len(idx) > 4:
                slope = np.polyfit(idx.astype(float),
                                   d[idx].astype(float), 1)[0]
                if 1.0 - slope > 0.0:
                    ramp_c = cents((1.0 - slope) * TONE / law_hz)
        trim = min(400, n // 10)
        a, b = lo + trim, hi - trim
        if b - a > PIECE_FIT_MAX:
            mid = (a + b) // 2
            a, b = mid - PIECE_FIT_MAX // 2, mid + PIECE_FIT_MAX // 2
        sine_c = float("nan")
        if b - a >= max(64, rate / law_hz):
            got = lsq_hz(y[a:b], rate)
            if got == got:
                sine_c = cents(got / law_hz)
        read = (ramp_c == ramp_c and sine_c == sine_c
                and abs(ramp_c - sine_c) <= PIECE_AGREE)
        out.append((n, ramp_c, sine_c, read))
    return out


def walk_cell(cls, a, b, rate, character, law_hz, amp=12000.0, setup=None,
              after_ms=300.0, **options):
    """One Time move a -> b read per binade piece with the guard above:
    the tone render and the ramp render of the same move, the walk's end
    off the read position. `law_hz` is the pitch the law says the walk
    plays. Returns dict(pieces, worst (over read pieces), unread (pieces
    not read), read_frames, walk, passed (no read piece over 10 c))."""
    fa, fb = frames_of(a, rate), frames_of(b, rate)
    start = start_of(a, rate)
    rate_of_walk = abs(1.0 - law_hz / TONE)
    walk_est = int(abs(fb - fa) / rate_of_walk) if rate_of_walk > 0 else 0
    frames = start + int(1.1 * walk_est) + int(after_ms * rate / 1000.0)
    opts = dict(HELD)
    opts.update(options)
    effect = cls(src_of(sine(TONE, amp, frames, rate), 1, rate), time_ms=a,
                 character=character, **opts)
    if setup is not None:
        setup(effect)
    y = render(effect, frames, {start: set_time(b)})[:, 0]
    effect.deinit()
    d, ok = read_position(cls, a, b, rate, character, start, frames, setup,
                          **options)
    walking = np.nonzero((d[start:] != fb) & ok[start:])[0]
    end = start + (int(walking[-1]) + 1 if len(walking) else 0)
    pieces = binade_pieces(y, d, ok, start, end, fa, fb, law_hz, rate)
    read = [p for p in pieces if p[3]]
    worst = max((max(p[1], p[2], key=abs) for p in read), key=abs,
                default=float("nan"))
    return dict(pieces=pieces, worst=worst,
                unread=sum(1 for p in pieces if not p[3]),
                read_frames=sum(p[0] for p in read), walk=end - start,
                passed=bool(read) and abs(worst) <= 10.0)


def glide_law_hz(glide_ms, a, b):
    """Sliding-head's pitch while the head walks a -> b at Glide
    `glide_ms`, from the Glide asked (1 180 ms / Glide), never from the
    class's slew function."""
    law = FULL_RANGE_LAW / glide_ms
    return TONE * (1.0 + law if b < a else 1.0 - law)


#: 1 180 ms, sliding-head's full-range Time move, written from the numbers.
FULL_RANGE_LAW = 1200.0 - 20.0


def glide_ms_of(grid):
    return _component.macro_value(TapeDelay._MACRO_RANGES[GLIDE_I],
                                  grid / 127.0)


_READ_HEADS = {}


def read_head(cls):
    """`cls` with its loop low-pass handed 0 after every refresh: an
    instrument for reading where the read head is, never a subject. The
    walk is the node's `delay_slew` (`audiodsp_feedback_delay.c:492`,
    `:497` at v0.6.3rc1) and never sees the filter, which filters what was read, so the
    positions are the class's (Station C's `read_head_class`)."""
    if cls not in _READ_HEADS:
        def _refresh(self):
            cls._refresh(self)
            self._delay.set(damping_hz=0.0)
        _READ_HEADS[cls] = type("ReadHead" + cls.__name__, (cls,),
                                {"_refresh": _refresh})
    return _READ_HEADS[cls]


def read_position(cls, a, b, rate, character, start, frames, setup=None,
                  **options):
    """The read position D[n], in frames, off a render of the move a -> b
    issued at `start`, with a wrapping 1-LSB-per-frame ramp as the source
    (the wet sample is n - D[n], so D is exact on a whole frame and the
    interpolated position rounded between them), on `read_head(cls)`.
    `ok` is False next to the ramp's wrap and before the line has filled.
    `setup(effect)` runs after construction (a Glide grid position).
    Returns (D, ok)."""
    opts = dict(HELD)
    opts.update(options)
    n = np.arange(frames)
    x = (n % 65536) - 32768.0
    effect = read_head(cls)(src_of(x, 1, rate), time_ms=a,
                            character=character, **opts)
    if setup is not None:
        setup(effect)
    y = render(effect, frames, {start: set_time(b)})[:, 0]
    d = (n - (y.astype(np.int64) + 32768)) % 65536
    wrap = np.abs(np.diff(y)) > 30000
    ok = np.ones(frames, bool)
    ok[1:] &= ~wrap
    ok[:-1] &= ~wrap
    ok[:start // 2] = False
    return d, ok


def step_cell(cls, rate=RATE, amp=12000.0, start=None):
    """T1b's step (fix round 1): sliding-head at Glide 0, 200 -> 100.4 ms.
    The read position off a ramp render sits on T_old's whole frame before
    the move and on T_new's after it, and no frame reads a position between
    the two: the node jumps, where any walk, however fast, reads the
    positions between. The pitch 2-50 ms after the move is within 10 cents
    of the tone. `start` is the frame the move is issued on (a block
    boundary; the default is the other T1 cells' frame).

    The round-0 clause (a jump on the read recovered through the inverted
    loss low-pass of at least 5x the unfiltered tone's slope) is struck: it
    reads the tone's two phases across the jump, so it moves with the frame
    the move lands on (x1.00-x13.03 over 16 block boundaries at 48 kHz)."""
    fa, fb = frames_of(200.0, rate), frames_of(100.4, rate)
    if start is None:
        start = start_of(200.0, rate)
    frames = start + rate // 2
    opts = dict(HELD)
    effect = cls(src_of(sine(TONE, amp, frames, rate), 1, rate),
                 time_ms=200.0, character=tape.SLIDING_HEAD, glide_ms=0.0,
                 **opts)
    y = render(effect, frames, {start: set_time(100.4)})[:, 0]
    got = lsq_hz(y[start + int(0.002 * rate):start + int(0.05 * rate)], rate)
    offset = cents(got / TONE) if got == got else float("inf")
    # The struck round-0 figure, reported and never graded, so the earlier
    # probes that print it still run.
    coef = 1.0 - math.exp(-2.0 * math.pi * effect._damping / rate)
    recovered = y[:-1] + np.diff(y) / coef
    ratio = float(np.max(np.abs(np.diff(recovered))[start - 3:start + 3])) \
        / (2.0 * math.pi * TONE / rate * amp)
    d, ok = read_position(cls, 200.0, 100.4, rate, tape.SLIDING_HEAD, start,
                          frames, glide_ms=0.0)
    lo = start - 2000
    window = np.arange(lo, frames)
    window = window[ok[lo:frames]]
    pos = d[window]
    between = int(np.sum((pos != fa) & (pos != fb)))
    before = bool(np.all(d[lo:start][ok[lo:start]] == fa))
    tail = start + rate // 10
    after = bool(np.all(d[tail:frames][ok[tail:frames]] == fb))
    landed = window[pos == fb]
    first = int(landed[0]) - start if len(landed) else None
    return dict(passed=before and after and between == 0
                and abs(offset) <= 10.0, between=between, before=before,
                after=after, offset=offset, landed=first, fa=fa, fb=fb,
                ratio=ratio)


G_START = 9472
T0, T1 = 200.0, 300.0


def burst(frames, peak, rate=RATE, at=0.100):
    x = np.zeros(frames)
    n = int(0.040 * rate)
    t = np.arange(n)
    s0 = int(at * rate)
    x[s0:s0 + n] = peak * np.sin(np.pi * t / n) ** 2 * np.sin(
        2 * np.pi * 1000.0 * t / rate)
    return x


def find_repeats(y, count=4, rate=RATE):
    env = np.abs(analytic(y))
    k = int(0.005 * rate)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    i = int(0.19 * rate)
    thr = 0.01 * env[i:].max()
    peaks = []
    while i < len(env) and len(peaks) < count:
        if env[i] > thr:
            m = i + int(np.argmax(env[i:i + int(0.03 * rate)]))
            lo = m
            while lo > 0 and env[lo] > env[m] * 0.5:
                lo -= 1
            hi = m
            while hi < len(env) - 1 and env[hi] > env[m] * 0.5:
                hi += 1
            peaks.append(((lo + hi) // 2) - int(0.010 * rate))
            i = hi + int(0.1 * rate)
        else:
            i += 1
    return peaks


def gesture(cls, character, peak=12000.0, moves=True):
    """The 200 -> 300 -> 200 ms gesture at Feedback 0.7 with a 40 ms burst
    at 100-140 ms, stereo, 48 kHz. Varispeed: two moves from rest, the
    return 400 ms after the first. Sliding-head: two walks at slew 0.5
    (Glide 2 360 ms), 200 ms apart. Returns each repeat's pitch in cents
    against 1 kHz."""
    frames = int(2.2 * RATE)
    opts = dict(HELD)
    opts.update(feedback=0.7)
    effect = cls(src_of(burst(frames, peak), 2), time_ms=T0,
                 character=character, glide_ms=2360.0, **opts)
    events = {}
    if moves:
        if character == tape.VARISPEED:
            second = (G_START + int(0.4 * RATE)) // BLOCK * BLOCK
        else:
            second = G_START + int(0.2 * RATE) // BLOCK * BLOCK
        events = {G_START: set_time(T1), second: set_time(T0)}
    y = render(effect, frames, events)[:, 0]
    out = []
    for a in find_repeats(y):
        seg = y[a:a + int(0.02 * RATE)]
        out.append(cents(peak_hz(seg, RATE, pad=8) / 1000.0))
    return out


def gesture_verdict(cls):
    """T1b's feedback clauses: every sliding-head repeat 1-4 more than 100
    cents off the source; every varispeed repeat 2-4 within 5 cents of the
    same repeat with no gesture; and the two characters not the same."""
    control = gesture(TapeDelay, tape.VARISPEED, moves=False)
    vari = gesture(cls, tape.VARISPEED)
    slide = gesture(cls, tape.SLIDING_HEAD)
    ok_slide = len(slide) == 4 and all(abs(c) > 100.0 for c in slide)
    ok_vari = (len(vari) == 4 and len(control) == 4
               and all(abs(v - c) <= 5.0
                       for v, c in zip(vari[1:], control[1:])))
    return dict(passed=ok_slide and ok_vari, vari=vari, slide=slide,
                control=control)


class T1bSlidingHead(unittest.TestCase):
    def test_the_ramp(self):
        got = ramp_cell(TapeDelay)
        self.assertTrue(got["passed"], got)
        self.assertAlmostEqual(got["law"], -884.4, delta=0.05)

    def test_the_ramp_at_other_levels_and_rates(self):
        for rate, amp in ((48000, 120.0), (48000, 32000.0), (22050, 12000.0)):
            got = ramp_cell(TapeDelay, rate, amp)
            self.assertTrue(got["passed"], (rate, amp, got))

    def test_glide_grid_cells_both_ways(self):
        # Each side of the power of two the walk crosses (8 192 frames at
        # 48 kHz, 4 096 at 22.05) is read on its own, and the no-step
        # clause holds over T1a's three windows.
        for rate, grid in ((48000, 4), (48000, 89), (48000, 127),
                           (22050, 89)):
            for a, b in ((200.0, 150.0), (150.0, 200.0)):
                got = glide_cell(TapeDelay, grid, a, b, rate)
                self.assertTrue(got["passed"], (rate, grid, a, b, got))

    def test_a_staircase_is_red_on_the_no_step_clause(self):
        # Station A's cell (App. F8): grid 89, 200 -> 150 ms, 48 kHz.
        got = glide_cell(StaircaseTape, 89, 200.0, 150.0)
        self.assertFalse(got["passed"], got)
        self.assertGreater(got["step"], 1.0, got)
        clean = glide_cell(TapeDelay, 89, 200.0, 150.0)
        self.assertLess(clean["step"], 1.0, clean)

    def test_a_staircase_is_red_on_the_ramp(self):
        got = ramp_cell(StaircaseTape)
        self.assertFalse(got["passed"], got)
        self.assertGreater(got["step"], 1.0, got)

    def test_the_glide_binades(self):
        # Fix round 1 (dossier T1b, revised under vision 7.2): a rising move
        # is claimed from grid 4 while the head stays under 16 384 frames,
        # from grid 10 past 16 384 and from grid 22 past 32 768 (48 kHz:
        # 341.3 and 682.7 ms). The claimed edge grids read green inside
        # their binades; grid 1 at the default Time's 350 -> 450 ms, no
        # longer claimed, reads +40.98 c; falling moves are claimed at
        # every grid, grid 1 included.
        cells = ((4, 200.0, 330.0, False), (10, 400.0, 650.0, False),
                 (22, 750.0, 1150.0, False), (1, 350.0, 450.0, True),
                 (1, 650.0, 400.0, False))
        for grid, a, b, red in cells:
            got = walk_cell(TapeDelay, a, b, RATE, tape.SLIDING_HEAD,
                            glide_law_hz(glide_ms_of(grid), a, b),
                            setup=lambda e, g=grid: e.set_macro(GLIDE_I, g))
            self.assertEqual(got["unread"], 0, (grid, a, b, got))
            self.assertEqual(got["passed"], not red, (grid, a, b, got))
            if red:
                self.assertAlmostEqual(got["worst"], 40.98, delta=0.05)

    def test_a_short_piece_is_not_read(self):
        # Fix round 1: a piece whose two readings do not both exist and
        # agree within 1 c is reported unread, not green or red. The span
        # refuter's cell, grid 1, 41.75 -> 55.66 ms (Time MIDI 31.75 and
        # 0.75 of it), cuts a 45-frame piece and a 646-frame one; the
        # shifted tone (34 Hz) has no period in either, so neither is read
        # (Station C's ramp-slope-only reader put -215.6 c on the first).
        grid = 1
        b = _component.macro_value(TapeDelay._MACRO_RANGES[TIME_I], 0.25)
        a = 0.75 * b
        got = walk_cell(TapeDelay, a, b, RATE, tape.SLIDING_HEAD,
                        glide_law_hz(glide_ms_of(grid), a, b),
                        setup=lambda e: e.set_macro(GLIDE_I, grid))
        self.assertEqual(got["unread"], len(got["pieces"]), got)
        self.assertFalse(got["passed"], got)
        self.assertLess(min(p[0] for p in got["pieces"]), 64, got)

    def test_the_step_at_glide_0(self):
        # Fix round 1: the read position jumps between two frames, at three
        # rates and on four block boundaries each; no pitch offset after.
        for rate in (48000, 44100, 22050):
            base = start_of(200.0, rate)
            for k in (0, 2, 5, 13):
                got = step_cell(TapeDelay, rate, start=base + k * BLOCK)
                self.assertTrue(got["passed"], (rate, k, got))
                self.assertEqual(got["landed"], 0, (rate, k, got))

    def test_a_fast_walk_at_glide_0_is_red(self):
        for rate in (48000, 22050):
            got = step_cell(FastWalkAtZeroTape, rate)
            self.assertFalse(got["passed"], got)
            self.assertGreater(got["between"], 200, got)

    def test_the_gesture(self):
        got = gesture_verdict(TapeDelay)
        self.assertTrue(got["passed"], got)
        self.assertLess(abs(got["vari"][0] + 701.4), 2.0, got)

    def test_a_loop_shift_is_red_on_the_gesture(self):
        got = gesture_verdict(LoopShiftTape)
        self.assertFalse(got["passed"], got)

    def test_a_per_block_tape_equation_is_red_on_the_sliding_head(self):
        # The sliding-head's moves driven along the tape equation once per
        # block telescope: its repeats come back to the source, so the
        # sliding-head clause (every repeat 1-4 over 100 cents off) fails.
        slide = gesture(PerBlockSlidingTape, tape.SLIDING_HEAD)
        self.assertEqual(len(slide), 4, slide)
        self.assertTrue(any(abs(c) <= 100.0 for c in slide), slide)
        # Measured at 48 kHz: -701.5, -3.7, -5.2, -7.4 cents.
        self.assertLess(max(abs(c) for c in slide[1:]), 10.0, slide)
        self.assertFalse(gesture_verdict(PerBlockSlidingTape)["passed"])


# -- T2, T3: the loss law -------------------------------------------------

def eq13_db(f, v, spacing_m):
    k = 2.0 * np.pi * np.asarray(f, dtype=float) / v
    spacing = np.exp(-k * spacing_m)
    thick = (1.0 - np.exp(-k * tape.THICK_M)) / (k * tape.THICK_M)
    half = k * tape.GAP_M / 2.0
    gap = np.abs(np.sin(half) / half)
    return 20.0 * np.log10(spacing * thick * gap)


def lambda_top_um(spacing_um, tol=1.75):
    """The shortest wavelength down to which a one-pole with eq. (13)'s
    -3 dB point stays within `tol` dB of eq. (13) (dossier App. F3)."""
    d = spacing_um * 1e-6
    kc = tape.k3_of(d)
    ks = np.geomspace(kc / 30.0, kc * 100.0, 20000)
    onepole = -10.0 * np.log10(1.0 + (ks / kc) ** 2)
    err = np.abs(onepole - eq13_db(ks / (2 * math.pi), 1.0, d))
    bad = np.where(err > tol)[0]
    kmax = ks[bad[0] - 1] if len(bad) else ks[-1]
    return 2 * math.pi / kmax * 1e6


def one_pass(cls, time_ms, spacing_um, character=tape.VARISPEED, rate=RATE,
             amp=32767.0):
    """The one-pass response of an impulse through the class: 4 096 frames
    from the whole-frame Time, scaled to the impulse."""
    t = frames_of(time_ms, rate)
    frames = t + 4096 + 512
    x = np.zeros(frames)
    x[0] = amp
    opts = dict(HELD)
    effect = cls(src_of(x, 2, rate), time_ms=time_ms, spacing_um=spacing_um,
                 character=character, **opts)
    y = render(effect, frames)[:, 0]
    return y[t:t + 4096] / amp


def response_db(seg, rate, freqs):
    n = np.arange(len(seg))
    freqs = np.asarray(freqs, dtype=float)
    basis = np.exp(-2j * np.pi * np.outer(freqs, n) / rate)
    mag = np.abs(basis @ seg)
    return 20.0 * np.log10(np.maximum(mag, 1e-30))


def t2_one_pass(cls, time_ms, spacing_um, character, rate=RATE,
                amp=32767.0):
    v = tape.speed(character, time_ms)
    top = min(v / (lambda_top_um(spacing_um) * 1e-6), rate / 8.0)
    f = np.geomspace(100.0, top, 200)
    got = response_db(one_pass(cls, time_ms, spacing_um, character, rate,
                               amp), rate, f)
    err = got - eq13_db(f, v, spacing_um * 1e-6)
    worst = float(np.max(np.abs(err)))
    return dict(passed=worst <= 2.0, worst=worst, top=top,
                at=float(f[int(np.argmax(np.abs(err)))]))


def tone_db_off_eq13(time_ms, spacing_um, character, hz, rate=RATE,
                     amp=30000.0):
    """One pass on a steady tone at `hz`: the least-squares amplitude of
    the wet tone once the loop low-pass has settled, over the input's, in
    dB, less eq. (13) there (the material refuter's `tone_level_db`)."""
    t = frames_of(time_ms, rate)
    frames = t + int(0.3 * rate)
    effect = TapeDelay(src_of(sine(hz, amp, frames, rate), 2, rate),
                       time_ms=time_ms, spacing_um=spacing_um,
                       character=character, **HELD)
    y = render(effect, frames)[:, 0]
    seg = y[t + 2000:t + 2000 + int(0.2 * rate)]
    n = np.arange(len(seg))
    a = np.stack([np.cos(2 * np.pi * hz * n / rate),
                  np.sin(2 * np.pi * hz * n / rate), np.ones(len(seg))], 1)
    coef, *_ = np.linalg.lstsq(a, seg, rcond=None)
    level = 20 * math.log10(math.hypot(coef[0], coef[1]) / amp)
    v = tape.speed(character, time_ms)
    return level - float(eq13_db([hz], v, spacing_um * 1e-6)[0])


def t2_npass(cls, time_ms=350.0, spacing_um=5.0, character=tape.VARISPEED,
             rate=RATE):
    """Bursts at the band top through the loop at Feedback 0.7: the loss
    of each repeat above 4 LSB against n x the first's."""
    v = tape.speed(character, time_ms)
    top = min(v / (lambda_top_um(spacing_um) * 1e-6), rate / 8.0)
    t = frames_of(time_ms, rate)
    n_b = int(0.060 * rate)
    frames = t * 6 + int(0.2 * rate)
    x = np.zeros(frames)
    tt = np.arange(n_b)
    x[:n_b] = 30000 * np.sin(np.pi * tt / n_b) ** 2 * np.sin(
        2 * np.pi * top * tt / rate)
    opts = dict(HELD)
    opts.update(feedback=0.7)
    effect = cls(src_of(x, 2, rate), time_ms=time_ms, spacing_um=spacing_um,
                 character=character, **opts)
    y = render(effect, frames)[:, 0]
    basis = np.stack([np.cos(2 * np.pi * top * tt / rate),
                      np.sin(2 * np.pi * top * tt / rate)], 1)

    def amp_of(seg):
        coef, *_ = np.linalg.lstsq(basis, seg, rcond=None)
        return math.hypot(*coef)
    ref = amp_of(x[:n_b])
    g = 20 * math.log10(effect._feedback)
    losses = []
    for k in range(1, 5):
        seg = y[k * t:k * t + n_b]
        a = amp_of(seg)
        if a < 4.0 or float(np.max(np.abs(seg))) < 4.0:
            break
        losses.append(20 * math.log10(a / ref) - (k - 1) * g)
    worst = max(abs(loss - (k + 1) * losses[0])
                for k, loss in enumerate(losses)) if losses else float("inf")
    return dict(passed=len(losses) >= 2 and worst <= 2.0, worst=worst,
                per_pass=[loss / (k + 1) for k, loss in enumerate(losses)],
                top=top)


class T2LossLaw(unittest.TestCase):
    def test_the_band_tops(self):
        self.assertAlmostEqual(lambda_top_um(5.0), 41.4, delta=0.1)
        self.assertAlmostEqual(lambda_top_um(2.0), 122.2, delta=0.1)
        self.assertAlmostEqual(lambda_top_um(20.0), 105.3, delta=0.1)

    def test_one_pass_at_the_named_cells(self):
        for rate, character, time_ms, spacing in (
                (48000, tape.VARISPEED, 350.0, 5.0),
                (48000, tape.VARISPEED, 600.0, 20.0),
                (48000, tape.VARISPEED, 60.0, 2.0),
                (48000, tape.SLIDING_HEAD, 350.0, 5.0),
                (48000, tape.VARISPEED, 350.0, 3.772),
                (44100, tape.VARISPEED, 320.0, 5.0),
                (22050, tape.VARISPEED, 600.0, 5.0),
                (22050, tape.SLIDING_HEAD, 350.0, 20.0)):
            got = t2_one_pass(TapeDelay, time_ms, spacing, character, rate)
            self.assertTrue(got["passed"],
                            (rate, character, time_ms, spacing, got))

    def test_below_0_dbfs_the_impulse_reads_high_not_the_class(self):
        # Fix round 1 (dossier T2, revised under vision 7.2): the one-pass
        # clause is stated at 0 dBFS. At -20 dBFS the impulse's int16-
        # rounded tail carries this cell's reading over the bar (2.052 dB,
        # sliding-head 350 ms, Spacing MIDI 39, 48 kHz), while a steady tone
        # at the frequency it reads worst sits inside at both levels, so the
        # -20 dBFS impulse is no longer a claim of the row.
        spacing = _component.macro_value(
            TapeDelay._MACRO_RANGES[SPACING_I], 39 / 127.0)
        low = t2_one_pass(TapeDelay, 350.0, spacing, tape.SLIDING_HEAD,
                          amp=3277.0)
        full = t2_one_pass(TapeDelay, 350.0, spacing, tape.SLIDING_HEAD)
        self.assertGreater(low["worst"], 2.0, low)
        self.assertTrue(full["passed"], full)
        for amp in (3277.0, 30000.0):
            off = tone_db_off_eq13(350.0, spacing, tape.SLIDING_HEAD,
                                   low["at"], amp=amp)
            self.assertLess(abs(off), 2.0, (amp, off))

    def test_a_doubled_corner_is_red(self):
        for rate in (48000, 22050):
            got = t2_one_pass(DoubleCornerTape, 350.0, 5.0, tape.VARISPEED,
                              rate)
            self.assertFalse(got["passed"], (rate, got))
            self.assertGreater(got["worst"], 4.0)

    def test_n_passes(self):
        for character, time_ms in ((tape.VARISPEED, 350.0),
                                   (tape.VARISPEED, 600.0),
                                   (tape.SLIDING_HEAD, 350.0)):
            got = t2_npass(TapeDelay, time_ms, character=character)
            self.assertTrue(got["passed"], (character, time_ms, got))

    def test_the_loss_outside_the_loop_is_red(self):
        got = t2_npass(PostLossTape)
        self.assertFalse(got["passed"], got)
        self.assertGreater(got["worst"], 10.0)


def corner_and_10k(seg, rate):
    """The first crossing 3.01 dB under the one-pass response's own DC
    level, interpolated in log frequency on a 20 000-point grid, and its
    level at 10 kHz (against unity).

    Fix round 1: the crossing was read against unity. As the impulse falls
    its int16-rounded tail loses DC, which moved the corner ratio with level
    (+0.734 % at -20 dBFS against unity, +0.125 % against the response's
    DC; Spacing MIDI 51, 48 kHz). A response with no DC has no corner."""
    dc = float(np.sum(seg))
    level_10k = float(response_db(seg, rate, [10000.0])[0])
    if not dc > 0.0:
        return float("nan"), level_10k
    ref = 20.0 * math.log10(dc) - 3.0103
    f = np.geomspace(20.0, min(20000.0, 0.49 * rate), 20000)
    db = response_db(seg, rate, f)
    below = np.nonzero(db <= ref)[0]
    if not len(below) or below[0] == 0:
        return float("nan"), level_10k
    i = below[0]
    a, b = db[i - 1], db[i]
    frac = (a - ref) / (a - b)
    corner = math.exp(math.log(f[i - 1]) + frac
                      * (math.log(f[i]) - math.log(f[i - 1])))
    return corner, level_10k


def t3_cell(cls, spacing_um=5.0, rate=RATE, amp=32767.0):
    out = {}
    for character in tape.CHARACTERS:
        c1, l1 = corner_and_10k(one_pass(cls, 180.0, spacing_um, character,
                                         rate, amp), rate)
        c2, l2 = corner_and_10k(one_pass(cls, 600.0, spacing_um, character,
                                         rate, amp), rate)
        out[character] = (c1 / c2, l1 - l2)
    ratio_v, span_v = out[tape.VARISPEED]
    ratio_s, span_s = out[tape.SLIDING_HEAD]
    ok_v = abs(ratio_v / (10.0 / 3.0) - 1.0) <= 0.01 and span_v >= 9.0
    ok_s = abs(ratio_s - 1.0) <= 0.01 and abs(span_s) <= 1.0
    return dict(passed=ok_v and ok_s, varispeed=out[tape.VARISPEED],
                sliding=out[tape.SLIDING_HEAD])


class T3LossFollowsSpeed(unittest.TestCase):
    def test_the_span_at_the_named_cells(self):
        for rate, midi in ((48000, 51), (48000, 0), (48000, 127),
                           (44100, 64), (22050, 51)):
            spacing = _component.macro_value(
                TapeDelay._MACRO_RANGES[SPACING_I], midi / 127.0)
            got = t3_cell(TapeDelay, spacing, rate)
            self.assertTrue(got["passed"], (rate, midi, got))

    def test_at_minus_20_dbfs(self):
        got = t3_cell(TapeDelay, 5.0, RATE, 3277.0)
        self.assertTrue(got["passed"], got)

    def test_a_square_law_and_a_half_follow_are_red(self):
        for rate in (48000, 22050):
            got = t3_cell(SquareLawTape, 5.0, rate)
            self.assertFalse(got["passed"], got)
            self.assertGreater(got["varispeed"][0], 10.0)
            got = t3_cell(HalfFollowTape, 5.0, rate)
            self.assertFalse(got["passed"], got)
            self.assertGreater(got["sliding"][0], 1.5)


# -- T4: the fluctuation --------------------------------------------------

def bh4(n):
    a = (0.35875, 0.48829, 0.14128, 0.01168)
    k = np.arange(n) / (n - 1)
    return (a[0] - a[1] * np.cos(2 * np.pi * k) + a[2] * np.cos(4 * np.pi * k)
            - a[3] * np.cos(6 * np.pi * k))


def delay_trace(cls, rate=RATE, wow=2.0, flutter=1.0, amp=12000.0,
                seconds=60.0, time_ms=350.0, tone=TONE):
    """The delay recovered from a steady tone's analytic phase (997 Hz, the
    row's) over `seconds`, averaged to 200 Hz, mean removed; one
    channel."""
    frames = int(seconds * rate) + int(time_ms / 1000 * rate) + rate
    opts = dict(HELD)
    opts.update(wow_cents=wow, flutter_cents=flutter)
    effect = cls(src_of(sine(tone, amp, frames, rate), 1, rate),
                 time_ms=time_ms, **opts)
    y = render(effect, frames)[:, 0]
    start = int(time_ms / 1000 * rate) + rate // 2
    y = y[start:start + int(seconds * rate)]
    ph = np.unwrap(np.angle(analytic(y)))
    t = (np.arange(len(y)) + start) / float(rate)
    trace = t - ph / (2 * np.pi * tone)
    step = int(round(rate / 200.0))
    m = len(trace) // step
    trace = trace[:m * step].reshape(m, step).mean(axis=1) * 1000.0
    return trace - trace.mean(), rate / float(step)


def _fit_line(trace, t, f0):
    """The least-squares sinusoid near `f0`: (frequency, the fit, its
    amplitude in the trace's units)."""
    best = None
    for f in np.linspace(f0 - 0.005, f0 + 0.005, 101):
        a = np.stack([np.sin(2 * np.pi * f * t), np.cos(2 * np.pi * f * t)],
                     axis=1)
        coef, *_ = np.linalg.lstsq(a, trace, rcond=None)
        fit = a @ coef
        err = float(np.sum((trace - fit) ** 2))
        if best is None or err < best[0]:
            best = (err, f, fit, math.hypot(*coef))
    return best[1], best[2], best[3]


#: Fix round 1: every T4 clause also needs what it reads to be there in
#: absolute terms, each line's fitted amplitude and the slow band's at least
#: this many ms of delay. The weakest claimed line, Flutter grid 1
#: (0.0315 c), is 5.66e-4 ms peak by the wow law; the class built as a wire
#: has a whole delay trace of 3e-7 ms rms. Read in dB over its own floor
#: alone, the detector could not tell the two apart.
T4_FLOOR_MS = 1e-5


def t4_verdict(trace, rate):
    """T4's clauses: two lines in 0.2-12 Hz each >= 40 dB over the median
    floor between them, their ratio not within 1 % of p/q (p, q <= 8), and
    the 0.017-0.1 Hz band of the residual after both lines are fitted out
    >= 40 dB over that residual's floor. Fix round 1: each clause also
    needs its lines, or its band, at least T4_FLOOR_MS in amplitude; the
    ratio clause reads two lines, so it needs both there."""
    n = len(trace)
    w = bh4(n)
    f = np.fft.rfftfreq(n, 1.0 / rate)
    df = f[1]
    sdb = 10 * np.log10(np.abs(np.fft.rfft(trace * w)) ** 2 + 1e-300)
    lo = np.searchsorted(f, 0.2)
    hi = np.searchsorted(f, 12.0)
    lines = []
    for i in np.argsort(sdb[lo:hi])[::-1] + lo:
        if all(abs(f[i] - f[j]) > 0.3 for j in lines):
            lines.append(i)
        if len(lines) == 2:
            break
    lines.sort()
    a, b = lines
    between = sdb[a + 8:b - 8]
    if len(between) < 8:
        return dict(passed=False, why="lines adjacent", two_lines=False,
                    ratio_ok=False, drift_ok=False)
    floor = float(np.median(between))

    def parabolic(i):
        p, q, r = sdb[i - 1], sdb[i], sdb[i + 1]
        return (i + 0.5 * (p - r) / (p - 2 * q + r)) * df
    t = np.arange(n) / rate
    f1, fit1, a1 = _fit_line(trace, t, parabolic(a))
    f2, fit2, a2 = _fit_line(trace - fit1, t, parabolic(b))
    r = trace - fit1 - fit2
    r = r - np.sum(r * w) / np.sum(w)
    spec = np.abs(np.fft.rfft(r * w))
    rdb = 10 * np.log10(spec ** 2 + 1e-300)
    rfloor = float(np.median(rdb[a + 8:b - 8]))
    ratio = f2 / f1
    near = min(abs(ratio - p / float(q)) / (p / float(q))
               for p in range(1, 9) for q in range(1, 9))
    top = np.searchsorted(f, 0.1)
    drift = float(rdb[1:top].max()) - rfloor
    # The band's largest bin as a sinusoid's amplitude (the window's
    # coherent gain is its sum).
    slow_ms = 2.0 * float(spec[1:top].max()) / float(np.sum(w))
    d1, d2 = sdb[a] - floor, sdb[b] - floor
    there = a1 >= T4_FLOOR_MS and a2 >= T4_FLOOR_MS
    two = d1 >= 40.0 and d2 >= 40.0 and there
    ratio_ok = near > 0.01 and there
    drift_ok = drift >= 40.0 and slow_ms >= T4_FLOOR_MS
    return dict(passed=two and ratio_ok and drift_ok,
                two_lines=two, ratio_ok=ratio_ok, drift_ok=drift_ok,
                f1=f1, f2=f2, d1=d1, d2=d2, a1=a1, a2=a2, slow_ms=slow_ms,
                ratio=ratio, drift=drift)


class T4Fluctuation(unittest.TestCase):
    def test_the_default_at_48k(self):
        got = t4_verdict(*delay_trace(TapeDelay))
        self.assertTrue(got["passed"], got)
        self.assertAlmostEqual(got["f1"], 0.7194, delta=0.001)
        self.assertAlmostEqual(got["f2"], 5.1155, delta=0.001)

    def test_the_stops_and_the_default_at_22k(self):
        got = t4_verdict(*delay_trace(TapeDelay, wow=8.0, flutter=4.0,
                                      seconds=60.0))
        self.assertTrue(got["passed"], got)
        got = t4_verdict(*delay_trace(TapeDelay, rate=22050))
        self.assertTrue(got["passed"], got)

    def test_the_planted_tables_are_each_red_on_their_clause(self):
        for rate in (48000, 22050):
            got = t4_verdict(*delay_trace(FlutterOnWowLineTape, rate=rate))
            self.assertFalse(got["passed"], (rate, got))
            self.assertFalse(got.get("two_lines", False), (rate, got))
        got = t4_verdict(*delay_trace(Harmonic504Tape))
        self.assertFalse(got["passed"], got)
        self.assertFalse(got["ratio_ok"], got)
        self.assertTrue(got["drift_ok"], got)
        got = t4_verdict(*delay_trace(NoDriftTape))
        self.assertFalse(got["passed"], got)
        self.assertFalse(got["drift_ok"], got)
        self.assertTrue(got["two_lines"], got)

    def test_the_weakest_claimed_lines_clear_the_absolute_floor(self):
        # Fix round 1: Wow grid 1 x Flutter grid 1 at the row's lower level,
        # where the flutter line is 5.66e-4 ms by the wow law.
        got = t4_verdict(*delay_trace(TapeDelay, wow=8.0 / 127,
                                      flutter=4.0 / 127, amp=1200.0))
        self.assertTrue(got["passed"], got)
        self.assertGreater(min(got["a1"], got["a2"], got["slow_ms"]),
                           10 * T4_FLOOR_MS, got)

    def test_the_wire_is_red_on_every_clause(self):
        # Fix round 1: the class built as a wire, at the probe tones where
        # the round-0 detector read it green on every clause (996 Hz) or on
        # all but the ratio (997 Hz, 1 000 Hz). The absolute clause is what
        # turns each red; the pack runs 990-1 004 Hz at three rates.
        wire = kit_faults.wire_build(TapeDelay)
        for tone in (996.0, 997.0, 1000.0):
            got = t4_verdict(*delay_trace(wire, tone=tone))
            self.assertFalse(got["two_lines"], (tone, got))
            self.assertFalse(got["ratio_ok"], (tone, got))
            self.assertFalse(got["drift_ok"], (tone, got))

    def test_flutter_under_grid_1_is_red_and_not_claimed(self):
        # Fix round 1: Flutter above 0 and under grid 1 (0.0315 c) is added
        # to Not claimed; at 0.005 c (Wow 8 c) the flutter line reads under
        # 40 dB over its floor.
        got = t4_verdict(*delay_trace(TapeDelay, wow=8.0, flutter=0.005))
        self.assertFalse(got["two_lines"], got)

    def test_wow_under_grid_1_is_red_and_not_claimed(self):
        # Fix round 2: Wow above 0 and under grid 1 (0.063 c) is added to
        # Not claimed, as Flutter's was. At 1.2e-4 c (Flutter 1 c, 48 kHz)
        # the slow band still reads well over 40 dB above its own floor but
        # carries under T4_FLOOR_MS of delay (8.21e-6 ms), so the absolute
        # clause is what fails it: the exclusion is needed, and grid 1
        # (test_the_weakest_claimed_lines_clear_the_absolute_floor) is not
        # in it.
        got = t4_verdict(*delay_trace(TapeDelay, wow=1.2e-4, flutter=1.0))
        self.assertFalse(got["passed"], got)
        self.assertFalse(got["drift_ok"], got)
        self.assertGreaterEqual(got["drift"], 40.0, got)
        self.assertLess(got["slow_ms"], T4_FLOOR_MS, got)
        self.assertTrue(got["two_lines"], got)
        self.assertTrue(got["ratio_ok"], got)


# -- T5: disconfirmed by design -------------------------------------------

def loop_area(source_of, record_level, rate=RATE):
    """Output against input over one period of a 5 Hz triangle at
    29 205 LSB peak, one pass, Time 350 ms, the loss low-pass in: the
    enclosed area by the shoelace formula (Saturation TP3's shape)."""
    per = rate // 5
    periods = 8
    t = frames_of(350.0, rate)
    frames = t + per * periods
    ph = (np.arange(frames) % per) / float(per)
    tri = 29205.0 * (4 * np.abs(ph - 0.5) - 1)
    opts = dict(HELD)
    opts.update(record_level=record_level)
    effect = TapeDelay(source_of(tri), time_ms=350.0, **opts)
    y = render(effect, frames)[:, 0]
    a = t + per * (periods - 2)
    x, z = tri[a - t:a - t + per], y[a:a + per]
    return 0.5 * abs(float(np.dot(x, np.roll(z, -1))
                           - np.dot(z, np.roll(x, -1))))


class T5NoMemory(unittest.TestCase):
    """T5 is recorded disconfirmed by design: the loop's only record
    nonlinearity is a static cubic, so Record Level 1's loop is no larger
    than the Record Level 0 control's. These tests pin that, and show the
    measurement can pass on a build with memory."""

    def test_record_level_draws_no_hysteresis_loop(self):
        control = loop_area(lambda x: src_of(x, 1), 0.0)
        half = loop_area(lambda x: src_of(x, 1), 0.5)
        full = loop_area(lambda x: src_of(x, 1), 1.0)
        self.assertLess(10 * math.log10(full / control), 6.0)
        self.assertLess(10 * math.log10(full / control), 0.0)
        self.assertLess(full, half)

    def test_the_measurement_passes_a_build_with_memory(self):
        import audioshaper
        xs = np.linspace(-1, 1, 1025)
        curve = array("h", np.round(xs * 32767).astype(np.int16).tobytes())

        def shaped(h):
            def source_of(x):
                ws = audioshaper.Waveshaper(sample_rate=RATE, channel_count=1,
                                            curve=curve, hysteresis=h,
                                            hysteresis_width=0.02)
                ws.play(src_of(x, 1))
                return ws
            return source_of
        control = loop_area(shaped(0.0), 0.0)
        memory = loop_area(shaped(1.0), 0.0)
        self.assertGreater(10 * math.log10(memory / control), 6.0)


# -- Tier 1 ---------------------------------------------------------------

class Tier1Fast(unittest.TestCase):
    def test_mix_zero_is_a_wire_on_the_full_scale_ramp(self):
        for channels in (2, 1):
            data = probes.ramp_fs(frames=48000, channels=channels)
            src = probes.ArraySource(data, rate=RATE, channels=channels)
            effect = TapeDelay(src, mix=0.0, time_ms=20.0)
            out = render(effect, 48000)
            want = np.frombuffer(data.tobytes(), dtype=np.int16).reshape(
                -1, channels)
            self.assertEqual(int(np.sum(out != want)), 0, channels)

    def test_the_dry_is_unity_until_the_repeat(self):
        x = sine(440.0, 12000.0, 4096)
        effect = TapeDelay(src_of(x), mix=1.0)
        out = render(effect, 4096)[:, 0]
        self.assertTrue(np.array_equal(out, np.round(x)))

    def test_the_control_spans(self):
        # Time runs 20 to 1 200 ms and Feedback stops at 0.99, handed so.
        effect = TapeDelay(src_of(np.zeros(512)))
        effect.set_macro(TIME_I, 0)
        self.assertAlmostEqual(effect.macro(TIME_I), 20.0, places=9)
        self.assertEqual(effect._frames, frames_of(20.0))
        effect.set_macro(TIME_I, 127)
        self.assertAlmostEqual(effect.macro(TIME_I), 1200.0, places=9)
        self.assertEqual(effect._frames, frames_of(1200.0))
        effect.set_macro(FEEDBACK_I, 0)
        self.assertEqual(effect._feedback, 0.0)
        effect.set_macro(FEEDBACK_I, 127)
        self.assertEqual(effect._feedback, 0.99)

    def test_mix_2_is_the_repeats_alone(self):
        # A click at Mix 2: nothing until the repeat, 100 ms later.
        x = np.zeros(8192)
        x[10] = 30000
        out = render(TapeDelay(src_of(x), mix=2.0, time_ms=100.0,
                               feedback=0.0), 8192)[:, 0]
        self.assertEqual(float(np.max(np.abs(out[:4800]))), 0.0)
        self.assertGreater(float(np.max(np.abs(out[4800:5200]))), 1000.0)

    def test_construction_needs_audioecho(self):
        saved = sys.modules.get("audioecho", False)
        sys.modules["audioecho"] = None
        try:
            with self.assertRaises(ImportError):
                TapeDelay(src_of(np.zeros(512)))
        finally:
            if saved is False:
                del sys.modules["audioecho"]
            else:
                sys.modules["audioecho"] = saved
        TapeDelay(src_of(np.zeros(512))).deinit()

    def _tail_across_a_stop(self, stop, loud=False):
        """A 50 ms burst into Time 100 ms, Feedback 0.5, Mix 2, then
        silence; after 24 pulls the source hands empty buffers for `stop`
        pulls, then silence again (with `loud`, the burst on a loop).
        Returns (the bytes handed while it was stopped, the 40 blocks
        pulled after it)."""
        burst = array("h", np.repeat(
            np.round(sine(TONE, 12000.0, 2400)).astype(np.int16), 2)
            .tobytes())
        feed = lifecycle.Feed(burst, RATE, 2, "256", False)
        effect = TapeDelay(feed.port, sample_rate=RATE, time_ms=100.0,
                           feedback=0.5, mix=2.0)
        for _ in range(24):
            audiocore.get_buffer(effect.output)
        feed.point(feed.empty)
        stopped = bytearray()
        for _ in range(stop):
            stopped.extend(bytes(audiocore.get_buffer(effect.output)[1]))
        feed.point(lifecycle._adapter(burst, RATE, 2, 256, True)
                   if loud else feed.sil)
        after = bytearray()
        while len(after) < 40 * BLOCK * 4:
            after.extend(bytes(audiocore.get_buffer(effect.output)[1]))
        effect.deinit()
        return bytes(stopped), bytes(after[:40 * BLOCK * 4])

    def test_the_tail_rings_out_when_the_source_ends(self):
        # Restated at audiodsp eb2d20d (audiocomponents#127). Up to v0.6.3
        # the node advanced only on frames its source handed it, so a
        # source that ran dry froze the tail and a source that came back
        # played over it, and this test pinned that. That was the node's
        # defect (audiodsp#180), fixed in audiodsp#213: a node lets go of a
        # source that has ended and renders the frames it was not handed
        # from silence. So across the end the tail is, byte for byte, the
        # tail fed silence all along, and a loud source pointed behind the
        # same port afterwards is not heard.
        stopped, after = self._tail_across_a_stop(30, loud=True)
        self.assertGreater(max(abs(v) for v in array("h", stopped)), 1000)
        fed = self._tail_across_a_stop(0)[1]
        self.assertEqual((stopped + after)[:len(fed)], fed)

    def test_silence_stays_silence(self):
        for character in tape.CHARACTERS:
            for patch in range(len(TapeDelay.PATCHES)):
                effect = TapeDelay(src_of(np.zeros(RATE)),
                                   character=character, patch=patch)
                self.assertEqual(float(np.max(np.abs(render(effect, RATE)))),
                                 0.0, (character, patch))

    def test_the_tail_reaches_exact_zero_inside_tail_samples(self):
        for patch, channels in ((0, 2), (2, 1), (5, 2)):
            effect = TapeDelay(src_of(np.zeros(512), channels=channels),
                               patch=patch)
            bound = effect.tail_samples
            n = 4800
            x = 0.9 * 32767.0 * (np.random.RandomState(7).rand(n) * 2 - 1)
            frames = n + bound + 4096
            effect = TapeDelay(src_of(np.concatenate(
                [x, np.zeros(frames - n)]), channels), patch=patch)
            out = render(effect, frames)
            nz = np.nonzero(np.any(out != 0, axis=1))[0]
            last = int(nz[-1]) if len(nz) else 0
            self.assertLess(last - n, bound, (patch, last - n, bound))

    def test_reset_empties_the_line(self):
        x = np.concatenate([sine(1000.0, 20000.0, 4800),
                            np.zeros(RATE)])
        effect = TapeDelay(src_of(x), mix=2.0, time_ms=100.0)
        render(effect, 5120)
        effect.reset()
        out = render(effect, 4800 * 3)
        self.assertEqual(float(np.max(np.abs(out))), 0.0)

    def test_deinit_leaves_the_source(self):
        src = src_of(sine(440.0, 8000.0, 2048))
        effect = TapeDelay(src)
        render(effect, 256)
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(src)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)

    def test_click_delay_is_zero(self):
        for rate in (48000, 44100):
            x = np.zeros(2048)
            x[10] = 30000
            effect = TapeDelay(src_of(x, rate=rate), mix=1.0)
            out = render(effect, 2048)[:, 0]
            self.assertEqual(int(np.argmax(np.abs(out))), 10)
            self.assertEqual(effect.latency_samples, 0)

    def test_spread_does_not_silence_mono(self):
        x = np.zeros(RATE)
        x[32] = 12000
        outs = []
        for spread in (0.0, 37.0 / 127.0, 1.0):
            effect = TapeDelay(src_of(x, 1), time_ms=100.0, feedback=0.7,
                               mix=1.0, spread=spread)
            outs.append(render(effect, RATE).tobytes())
        self.assertEqual(outs[0], outs[1])
        self.assertEqual(outs[0], outs[2])

    def test_the_transport_is_read_only_with_sync_on(self):
        reads = []

        def transport():
            reads.append(1)
            return (True, 0.0, 100.0, 4, 4)
        effect = TapeDelay.create(src_of(np.zeros(512)), RATE,
                                  transport=transport)
        effect.set_macro(FEEDBACK_I, 64)
        self.assertEqual(reads, [])
        effect.set_macro(SYNC_I, 127)
        self.assertGreater(len(reads), 0)
        # 1/8 of 100 bpm is 300 ms.
        self.assertAlmostEqual(effect._time_played, 300.0, places=6)
        effect.set_macro(DIVISION_I, 127)
        self.assertAlmostEqual(effect._time_played, 1200.0, places=6)

    def test_a_host_without_a_tempo_leaves_time_on_the_knob(self):
        for bpm in (0.0, -10.0, float("nan"), float("inf"), None):
            effect = TapeDelay.create(
                src_of(np.zeros(512)), RATE,
                transport=lambda _b=bpm: (True, 0.0, _b, 4, 4), sync=True)
            self.assertAlmostEqual(effect._time_played, 350.0, places=9)
        static = TapeDelay(src_of(np.zeros(512)), sync=True)
        self.assertAlmostEqual(static._time_played, 350.0, places=9)

    def test_a_synced_move_is_a_varispeed_move(self):
        tempo = [120.0]
        effect = TapeDelay.create(
            src_of(np.zeros(512)), RATE,
            transport=lambda: (True, 0.0, tempo[0], 4, 4), sync=True)
        self.assertAlmostEqual(effect._time_played, 250.0, places=6)
        tempo[0] = 60.0
        effect.set_macro(FEEDBACK_I, 50)
        self.assertAlmostEqual(effect._time_played, 500.0, places=6)
        self.assertAlmostEqual(effect._slew, 250.0 / 500.0, places=9)

    def test_a_move_inside_a_walk_takes_its_rate_from_the_last_time(self):
        effect = TapeDelay(src_of(np.zeros(RATE)), time_ms=200.0)
        render(effect, 512)
        effect.set_macro(TIME_I, time_midi(300.0))
        self.assertAlmostEqual(effect._slew, 100.0 / 300.0, places=9)
        effect.set_macro(FEEDBACK_I, 10)
        self.assertAlmostEqual(effect._slew, 100.0 / 300.0, places=9)
        effect.set_macro(TIME_I, time_midi(200.0))
        self.assertAlmostEqual(effect._slew, 100.0 / 200.0, places=9)
        # The falling move keeps the old Time in the tail's reach.
        self.assertEqual(effect._reach, frames_of(300.0))

    def test_the_feedback_is_handed_as_set(self):
        # Up to audiodsp v0.6.2 the always-in loss low-pass could hold a
        # small value for ever a hair either side of 1 - 0.5 / k, and the
        # class stepped the Feedback clear (the 0.99 stop played as about
        # 0.98998). Since v0.6.3rc1 the node lands a stalled low-pass
        # (#157): every position is handed as set and the bound is finite,
        # 686 laps at the stop (683 stepped).
        for rate in (48000, 44100, 22050):
            effect = TapeDelay(src_of(np.zeros(512), rate=rate))
            for midi in range(128):
                effect.set_macro(FEEDBACK_I, midi)
                self.assertEqual(effect._feedback,
                                 min(0.99, effect._value(FEEDBACK_I)),
                                 (rate, midi))
                self.assertIsNotNone(effect.tail_samples, (rate, midi))
            excess = tape.tone_excess(effect._damping, rate)[1]
            self.assertEqual(effect._feedback, 0.99)
            self.assertEqual(tape.laps_to_zero(effect._feedback, excess),
                             686)
            # Planted: the retired stepping hands a Feedback nobody set.
            stepped = SteppedTape(src_of(np.zeros(512), rate=rate))
            stepped.set_macro(FEEDBACK_I, 127)
            self.assertNotEqual(stepped._feedback, 0.99, rate)
            self.assertLess(abs(stepped._feedback - 0.99), 3e-5)
            self.assertEqual(tape.laps_to_zero(stepped._feedback, excess),
                             683)

    def _stall(self, cls, rate=RATE, channels=2):
        """The stall cell: Feedback 0.5 (k = 1), Mix 2, Time 100 ms, no
        wobble or squash, a 2 LSB DC for 1 s, then 3 s of silence. Returns
        (the Feedback handed, tail_samples, frames from the input's end to
        the last non-zero sample, whether the last frame is non-zero)."""
        frames = 4 * rate
        x = np.zeros(frames)
        x[:rate] = 2.0
        effect = cls(src_of(x, channels, rate), feedback=0.5, mix=2.0,
                     record_level=0.0, time_ms=100.0, wow_cents=0.0,
                     flutter_cents=0.0)
        declared = effect.tail_samples
        out = render(effect, frames)
        nz = np.nonzero(np.any(out != 0, axis=1))[0]
        last = int(nz[-1]) if len(nz) else -1
        return effect._feedback, declared, last - rate + 1, last == frames - 1

    def test_the_stall_cell_reaches_zero_at_the_feedback_set(self):
        # Up to audiodsp v0.6.2 the node held this cell for ever with the
        # Feedback handed raw, and the class stepped it clear. Since
        # v0.6.3rc1 (#157) 0.5 is handed as set and the tail ends inside
        # the bound (the Station C Tier 1 cell).
        for rate in (48000, 44100, 22050):
            for channels in (2, 1):
                feedback, declared, tail, held = self._stall(
                    TapeDelay, rate, channels)
                self.assertEqual(feedback, 0.5, (rate, channels))
                self.assertFalse(held, (rate, channels))
                self.assertGreater(tail, 0, (rate, channels))
                self.assertLessEqual(tail, declared, (rate, channels))
        # Planted: the retired stepping hands a Feedback nobody set.
        stepped = SteppedTape(src_of(np.zeros(512)), feedback=0.5)
        self.assertNotEqual(stepped._feedback, 0.5)
        self.assertLess(abs(stepped._feedback - 0.5), 3e-5)

    #: Re-audit round 1's cross-feed stall cells, (label, k, the Feedback
    #: the node is handed as float32, Spread): "knob" cells set Spread's
    #: MIDI position and a fractional Feedback position by `set_macro`,
    #: "ctor" cells pass both to the constructor. The first three are the
    #: re-refuter's portable cells (k = 9, 11, 50), the fourth a constructor
    #: Spread off every grid, and the fifth one of the 13 cells whose
    #: hand-back survives every order a compiler may sum the cross-feed in
    #: (separate roundings and both fused multiply-adds), so the plant holds
    #: there on a board too.
    CROSS_FEED_CELLS = (
        ("knob", 9, 0.9444443583488464, 1),
        ("knob", 11, 0.9545453786849976, 3),
        ("knob", 50, 0.9899999499320984, 2),
        ("ctor", 50, 0.9899998903274536, 0.1726040393114090),
        ("knob", 15, 0.9666665792465210, 37),
    )

    @staticmethod
    def feedback_position(target):
        """A fractional Feedback knob position whose value reaches the node
        as exactly `target` in float32 (0..0.99, linear)."""
        want = np.float32(target)
        m = float(want) * 127.0 / 0.99
        for step in range(-400, 401):
            cand = m + step * 1e-9
            if np.float32(0.99 * (cand / 127.0)) == want:
                return cand
        raise ValueError("no Feedback position reaches %r" % target)

    def _cross_feed_stall(self, cls, cell, rate=RATE, channels=2):
        """Time 20 ms, Mix 2, Record Level 0, patch 8's wobble (Wow 2 c,
        Flutter 1 c), the cell's Feedback and Spread: a DC of 2k + 2 LSB for
        four laps, then silence for `tail_samples` (read after the knobs
        move) plus a lap plus 4 096 frames. Returns (tail_samples, frames
        from the input's end to the last non-zero frame, |the last frame|,
        the Feedback handed)."""
        route, k, feedback, spread = cell
        ctor = dict(time_ms=20.0, mix=2.0, record_level=0.0, wow_cents=2.0,
                    flutter_cents=1.0)
        if route == "ctor":
            ctor.update(feedback=feedback, spread=spread)

        def build(src):
            effect = cls(src, **ctor)
            if route == "knob":
                effect.set_macro(FEEDBACK_I, self.feedback_position(feedback))
                effect.set_macro(SPREAD_I, spread)
            return effect
        probe = build(src_of(np.zeros(512), channels, rate))
        declared = probe.tail_samples
        lap = probe._frames
        handed = probe._feedback
        probe.deinit()
        lead = 4 * lap
        frames = lead + declared + lap + 4096
        x = np.zeros(frames)
        x[:lead] = 2 * k + 2
        out = render(build(src_of(x, channels, rate)), frames)
        nz = np.nonzero(np.any(out[lead:] != 0, axis=1))[0]
        tail = int(nz[-1]) + 1 if len(nz) else 0
        return declared, tail, int(np.max(np.abs(out[-1]))), handed

    def test_the_cross_feed_stall_cells_reach_zero(self):
        # Re-audit round 1's Tier 1 failure: up to audiodsp v0.6.3rc2 these
        # cells held k LSB on both lanes for ever with Spread handed as set,
        # and the class put Spread on a 1/4096 grid. Since v0.6.3rc3 the node
        # ends a cross-fed tail itself (#173): Spread is handed as set and
        # each cell ends inside the bound, in stereo and (Spread held at 0)
        # in mono. The trial dropped the RawSpreadTape plant: it was the
        # class as it now is, and at rc3 it ends too.
        for cell in self.CROSS_FEED_CELLS:
            route, k, feedback, spread = cell
            for channels in (2, 1):
                declared, tail, final, handed = self._cross_feed_stall(
                    TapeDelay, cell, channels=channels)
                self.assertEqual(np.float32(handed), np.float32(feedback),
                                 cell)
                self.assertEqual(final, 0, (cell, channels))
                self.assertGreater(tail, 0, (cell, channels))
                self.assertLessEqual(tail, declared, (cell, channels))

    def test_spread_is_handed_as_set(self):
        # At two channels Spread reaches the node as the knob sets it, the
        # constructor's too; at one it is held at 0. The 1/4096 grid the
        # class used up to v0.6.3rc2 is gone.
        for rate in (48000, 44100, 22050):
            effect = TapeDelay(src_of(np.zeros(512), 2, rate))
            with NodeSpy():
                for midi in [m / 4.0 for m in range(4 * 127 + 1)]:
                    effect.set_macro(SPREAD_I, midi)
                    knob = min(1.0, max(0.0, effect._value(SPREAD_I)))
                    self.assertEqual(effect._delay._handed["cross_feed"],
                                     knob, midi)
                    self.assertEqual(effect._spread, knob, midi)
            typed = TapeDelay(src_of(np.zeros(512), 2, rate),
                              spread=0.1726040393114090)
            self.assertEqual(typed._spread, 0.1726040393114090)
            mono = TapeDelay(src_of(np.zeros(512), 1, rate),
                             spread=37.0 / 127.0)
            self.assertEqual(mono._spread, 0.0)

    def _depth_move(self, cls, start, target, points=8):
        """(the tone's own largest step before the move, the largest step in
        the 2 000 frames after it) over `points` moves a quarter of the
        0.72 Hz wow line apart, on 997 Hz at 12 000 LSB, mono, wet only,
        Time 350 ms, 48 kHz."""
        first = (16800 + 9600) // BLOCK * BLOCK
        steadies, worsts = [], []
        for k in range(points):
            at = first + k * 65 * BLOCK
            events = {at: lambda e: [e.set_macro(i, v)
                                     for i, v in target.items()]}
            effect = cls(src_of(sine(TONE, 12000.0, at + 2400), 1),
                         mix=2.0, feedback=0.0, record_level=0.0,
                         spread=0.0)
            for index, value in start.items():
                effect.set_macro(index, value)
            y = render(effect, at + 2000 + BLOCK, events)[:, 0]
            steadies.append(float(np.abs(np.diff(y[at - 3000:at - 1])).max()))
            worsts.append(float(np.abs(np.diff(y[at - 1:at + 2000])).max()))
        return max(steadies), max(worsts)

    def test_a_depth_move_does_not_step(self):
        # Since audiodsp v0.6.3rc1 the node ramps a new depth in over 20 ms
        # (#160). While it travels the read offset may move |change| / 20 ms
        # of a frame per frame on top of the wobble, so the tone may slope up
        # to its own largest step times 1 + |change| / 20 ms, and no more.
        # Wow at Flutter 0 keeps the table's shape; a knob down to 0 keeps
        # the last table while the depth ramps out.
        # The planted faults are read where they show: through the loss
        # low-pass a read-head jump is plain only at some phases of the
        # tone (on Wow 32 -> 127 the eight moves read 791 against 809).
        wow_up = ({WOW_I: 32, FLUTTER_I: 0}, {WOW_I: 127}, 2.257, ())
        wow_out = ({WOW_I: 127, FLUTTER_I: 0}, {WOW_I: 0}, 3.017,
                   (NoneAtZeroTape,))
        flutter_out = ({WOW_I: 0, FLUTTER_I: 127}, {FLUTTER_I: 0}, 0.072,
                       (NoneAtZeroTape, JumpWowTape))
        for start, target, change, faults in (wow_up, wow_out, flutter_out):
            steady, worst = self._depth_move(TapeDelay, start, target)
            self.assertLessEqual(worst, steady * (1.0 + change / 20.0),
                                 (start, target))
            # Planted: no table at 0, so the depth ramps out on the node's
            # sine; and the read head moved by the whole change at once.
            for cls in faults:
                steady, worst = self._depth_move(cls, start, target)
                self.assertGreater(worst, steady * (1.0 + change / 20.0),
                                   (cls.__name__, start, target))

    def test_a_balance_move_steps_as_the_docstring_says(self):
        # A move that changes the balance of Wow and Flutter changes the
        # table's shape, which the node swaps at once: the docstring's 803
        # against the tone's 728, and 1 117 through a flutter-only table.
        self.assertEqual(self._depth_move(TapeDelay,
                                          {WOW_I: 32, FLUTTER_I: 0},
                                          {FLUTTER_I: 127}), (728.0, 803.0))
        self.assertEqual(self._depth_move(TapeDelay,
                                          {WOW_I: 32, FLUTTER_I: 32},
                                          {WOW_I: 0, FLUTTER_I: 0}),
                         (728.0, 1117.0))


def spread_tail_sweep(cls, feedback, rate=RATE):
    """The kit's TAIL through `macro_sweep` over Spread's 128 grid
    positions, stereo, Time 20 ms, Mix 2, Record Level 0, no wobble, at
    `feedback` (the constructor's, reaching the node as its float32): each
    cell a 0.5 FS DC held 0.5 s (`kit_probes.dc_step`), then silence for
    `tail_samples` plus a lap plus 4 096 frames. A cell's figure is its tail
    over `tail_samples`, infinite when the line never empties. Returns
    (the sweep's result, the MIDI positions whose figure is over 1)."""
    ctor = dict(feedback=feedback, mix=2.0, time_ms=20.0, record_level=0.0,
                wow_cents=0.0, flutter_cents=0.0)
    subject = cls(src_of(np.zeros(512), 2, rate), **ctor)
    step, held = probes.dc_step(level=0.5, hold_s=0.5, total_s=0.5,
                                rate=rate, channels=2)
    lead = np.frombuffer(step.tobytes(), dtype=np.int16).reshape(-1, 2)[:, 0]

    def measure(settings):
        declared = subject.tail_samples
        frames = held + declared + subject._frames + 4096
        x = np.zeros(frames)
        x[:len(lead)] = lead
        effect = cls(src_of(x, 2, rate), **ctor)
        effect.set_macro(SPREAD_I, settings[SPREAD_I])
        out = render(effect, frames).astype(np.int16)
        effect.deinit()
        got = kit.tail(kit.Render(out.tobytes(), rate, 2),
                       burst_end_frame=held, declared_tail_samples=declared,
                       settle_frames=4096)["values"]
        if not got["returns_to_zero"]:
            return float("inf")
        return got["tail_samples"] / float(declared)

    result = kit.macro_sweep(
        subject, [kit.MacroSpan(SPREAD_I, 0, 127, midpoints=126)], measure,
        worst="max", bar=1.0, name="TAIL/SPREAD")
    red = sorted(c["settings"][SPREAD_I] for c in result["values"]["cells"]
                 if not c["figure"] <= 1.0)
    subject.deinit()
    return result, red


class CrossFeedTailSweep(unittest.TestCase):
    """Tier 1 TAIL over Spread's whole travel at the re-refuter's two
    Feedbacks (re-audit round 1): the class is green at all 128 positions.
    Up to audiodsp v0.6.3rc2 Spread handed as set was red at MIDI 1 and 5
    (0.9444443583) and 2 and 39 (0.9899999499); at rc3 the node ends those
    tails itself (#173)."""

    def test_the_tail_ends_at_every_spread(self):
        for feedback in (0.9444443583488464, 0.9899999499320984):
            result, red = spread_tail_sweep(TapeDelay, feedback)
            self.assertEqual(result["values"]["points"], 128)
            self.assertEqual(red, [], feedback)
            self.assertFalse(result["red"], feedback)
            self.assertLess(result["values"]["worst"], 1.0, feedback)


class InputCeiling(unittest.TestCase):
    """The docstring's ceiling on the kit's `noise_det`, 20 s at 48 kHz:
    clean at -1.1 dBFS at the defaults (stereo and mono) and at -2.0 dBFS
    at every patch; the defaults rail 0.1 dB above."""

    def _rails(self, dbfs, channels=2, patch=None, character="varispeed"):
        frames = 20 * RATE
        data = probes.noise_det(frames=frames, dbfs=dbfs, channels=channels)
        src = probes.ArraySource(data, rate=RATE, channels=channels)
        effect = TapeDelay(src, patch=patch, character=character)
        out = render(effect, frames)
        return int(np.sum((out >= 32767) | (out <= -32768)))

    def test_the_stated_ceiling_is_clean_and_just_over_is_not(self):
        for channels, over in ((2, 14), (1, 7)):
            self.assertEqual(self._rails(-1.1, channels), 0, channels)
            self.assertEqual(self._rails(-1.0, channels), over, channels)
        for character in tape.CHARACTERS:
            for patch in range(len(TapeDelay.PATCHES)):
                self.assertEqual(self._rails(-2.0, 2, patch, character), 0,
                                 (character, patch))
        self.assertGreater(self._rails(-1.8, 2, 2), 0)
        self.assertGreater(self._rails(-1.7, 2, 4, "sliding-head"), 0)


# -- reachability: what the node is handed --------------------------------
#
# Fix round 1: the first walk read a marker attribute only the faulted
# subclass set, so it could not fail (the reviewer's `DialableTape` passed
# it). Every reading below is a value the class handed its node, or a law
# over handed values at the position walked, and nothing else.

class NodeSpy:
    """While active, every `audioecho.FeedbackDelay.set` call records its
    options on the node: `_handed` (the latest value of each option) and
    `_writes` (each call's options, in order)."""

    def __enter__(self):
        node_class = tape.audioecho.FeedbackDelay
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


def copy_of(effect):
    """A fresh instance of the same class and character at `effect`'s macro
    positions, on silence at its rate. Fix round 1: it also carries the
    constructor values the knobs cannot hold - an exact Glide off the grid
    (under grid 1 down to the 0.99 pin, or the jump), an exact Time and the
    line's `max_time_ms` - so a reading taken on the copy sees what the
    node is handed; the round-0 copy dropped them."""
    ctor = {"character": effect._character,
            "max_time_ms": effect._max_time_ms}
    if effect._glide_exact is not None:
        ctor["glide_ms"] = effect._glide_exact
    if effect._time_exact is not None:
        ctor["time_ms"] = effect._time_exact
    other = type(effect)(src_of(np.zeros(4096), 2, effect._sample_rate),
                         **ctor)
    for index in range(len(type(effect).MACRO_LABELS)):
        if index == GLIDE_I and effect._glide_exact is not None:
            continue
        if index == TIME_I and effect._time_exact is not None:
            continue
        other.set_macro(index, effect.get_macro(index))
    return other


def nudge_time(effect):
    """Move Time 32 grid steps, toward the middle of the knob."""
    now = effect.get_macro(TIME_I)
    effect.set_macro(TIME_I, now + 32.0 if now < 64.0 else now - 32.0)


def pull(effect, blocks):
    for _ in range(blocks):
        audiocore.get_buffer(effect.output)


def read_damping(effect):
    """The `damping_hz` handed to the loop now."""
    return round(float(effect._delay._handed["damping_hz"]), 2)


def k3_law(spacing_m):
    """Eq. (13)'s half-power wavenumber, by bisection on this file's own
    `eq13_db` (not the class's `k3_of`)."""
    lo, hi = 1.0, 1e7
    for _ in range(100):
        mid = math.sqrt(lo * hi)
        if float(eq13_db(mid / (2 * math.pi), 1.0, spacing_m)) > -3.0103:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def speed_law(character, time_ms):
    """Dossier section 6's speed law, written here from the numbers."""
    if character == tape.SLIDING_HEAD:
        return 0.2032
    return 0.40 * 180.0 / min(600.0, max(180.0, time_ms))


def read_corner_against_law(effect):
    """The handed `damping_hz` over the pre-warped eq. (13) corner at the
    Time and Spacing the knobs' labels say and the character's speed."""
    time_ms = min(effect._max_time_ms, effect.macro(TIME_I))
    spacing = effect.macro(SPACING_I)
    fc = speed_law(effect._character, time_ms) * k3_law(spacing * 1e-6) \
        / (2 * math.pi)
    law = tape.nominal_damping_hz(fc, effect._sample_rate)
    return round(effect._delay._handed["damping_hz"] / law, 3)


def read_speed_law(effect):
    """How the handed corner follows Time at these positions: on a copy,
    the `damping_hz` handed at Time 180 ms over the one at 600 ms (3.333 on
    varispeed, 1 on sliding-head)."""
    other = copy_of(effect)
    other.set_macro(TIME_I, time_midi(180.0))
    fast = other._delay._handed["damping_hz"]
    other.set_macro(TIME_I, time_midi(600.0))
    slow = other._delay._handed["damping_hz"]
    other.deinit()
    return round(fast / slow, 3)


def read_loss_placement(effect):
    """(the `damping_hz` handed to the loop, the one handed to a node after
    it)."""
    post = getattr(effect, "_post", None)
    after = post._handed["damping_hz"] if post is not None else 0.0
    return (round(float(effect._delay._handed["damping_hz"]), 2),
            round(float(after), 2))


def read_loop_shift(effect):
    """The `loop_semitones` handed to the node (never, on the clean
    class)."""
    return round(float(effect._delay._handed.get("loop_semitones", 0.0)), 4)


def read_table(effect):
    """(the handed `wow_depth_ms`, the handed table's points)."""
    handed = effect._delay._handed
    shape = handed["wow_shape"]
    return (round(float(handed["wow_depth_ms"]), 9),
            tuple(shape) if shape is not None else None)


def read_walk(effect):
    """(the `delay_slew` handed for one Time move, the law's) on a copy at
    these positions: varispeed's law is |dT| / T_new from the two handed
    `delay_ms`; sliding-head's is 1 180 ms over the Glide the knob's label
    says, pinned at 0.99, and 0 at grid 0."""
    other = copy_of(effect)
    before = other._delay._handed["delay_ms"]
    nudge_time(other)
    after = other._delay._handed["delay_ms"]
    handed = other._delay._handed["delay_slew"]
    if other._character == tape.VARISPEED:
        law = abs(after - before) / after
    elif other._macros[GLIDE_I] <= 0.0:
        law = 0.0
    else:
        law = min(0.99, 1180.0 / other.macro(GLIDE_I))
    other.deinit()
    return (round(float(handed), 6), round(float(law), 6))


def read_handed_slew(effect):
    """The `delay_slew` handed for one Time move, on a copy at these
    positions and constructor values: the node's walk alone, whatever the
    knob's label says. It is what T1b's step fault changes, and a
    constructor Glide reaches every slew up to the 0.99 pin."""
    other = copy_of(effect)
    nudge_time(other)
    handed = other._delay._handed["delay_slew"]
    other.deinit()
    return round(float(handed), 9)


def read_python_steps(effect):
    """How many times `delay_ms` is handed while eight blocks are pulled
    after one Time move, on a copy at these positions: the class hands it
    once, on the move; a Python-driven Time hands it every block."""
    other = copy_of(effect)
    pull(other, 1)
    mark = len(other._delay._writes)
    nudge_time(other)
    pull(other, 8)
    writes = sum(1 for w in other._delay._writes[mark:] if "delay_ms" in w)
    other.deinit()
    return writes


#: (name, fault, reading, constructor options for both builds). A fault
#: whose law is live only away from the defaults is built where it is live
#: (DigitalDelay's corner-cell precedent): `GlideScaledVarispeed` is the
#: clean class at Glide 6 000 ms, so it is built at grid 1's 1 222 ms;
#: `FastWalkAtZeroTape` differs only at Glide 0. Fix round 1: T1b's step
#: fault is `FastWalkAtZeroTape`, read by the handed slew alone;
#: `WalkAtZeroTape` was a constructor value (1 204.08 ms).
SLIDE = {"character": tape.SLIDING_HEAD}
REACH_WALKS = (
    ("DoubleWalkTape", DoubleWalkTape, read_walk, {}),
    ("GlideScaledVarispeed", GlideScaledVarispeed, read_walk,
     {"glide_ms": 1222.0}),
    ("FastWalkAtZeroTape", FastWalkAtZeroTape, read_handed_slew,
     dict(SLIDE, glide_ms=0.0)),
    ("StaircaseTape", StaircaseTape, read_python_steps, SLIDE),
    ("LoopShiftTape", LoopShiftTape, read_loop_shift, {}),
    ("PerBlockSlidingTape", PerBlockSlidingTape, read_python_steps, SLIDE),
    ("DoubleCornerTape varispeed", DoubleCornerTape,
     read_corner_against_law, {}),
    ("DoubleCornerTape sliding-head", DoubleCornerTape,
     read_corner_against_law, SLIDE),
    ("PostLossTape", PostLossTape, read_loss_placement, {}),
    ("SquareLawTape", SquareLawTape, read_speed_law, {}),
    ("HalfFollowTape", HalfFollowTape, read_speed_law, SLIDE),
    ("FlutterOnWowLineTape", FlutterOnWowLineTape, read_table, {}),
    ("Harmonic504Tape", Harmonic504Tape, read_table, {}),
    ("NoDriftTape", NoDriftTape, read_table, {}),
)


def reach(faulted, reading, rate, ctor):
    """`kit_faults.fault_reachability` at `rate`, the node watched."""
    def build(cls):
        return cls(src_of(np.zeros(512), 2, rate), **ctor)

    with NodeSpy():
        return kit_faults.fault_reachability(TapeDelay, faulted, reading,
                                             build)


#: Fix round 1: the constructor values the reachability walk visits beside
#: the macro grid and the patches - the ones a knob cannot hold. Glide: the
#: jump, under the 0.99 pin, the pin's edge (1 191.9 ms), between the pin
#: and grid 1 (1 204.08 ms is slew 0.98 exactly), grid 1 itself, the
#: defaults and past the 12 s top. Time: 0 (20 ms), off-grid values, past
#: the top. The line: a lowered `max_time_ms`.
CTOR_VALUES = (
    ("glide_ms", (0.0, 500.0, 1000.0, 1191.9, 1195.0, 1200.0,
                  1180.0 / 0.98, 1210.0, 1221.0, 1221.96, 1250.0, 2950.0,
                  6000.0, 12000.0, 30000.0)),
    ("time_ms", (0.0, 20.0, 100.4, 351.0, 1199.9, 5000.0)),
    ("max_time_ms", (300.0, 1200.0)),
)


def _same(a, b, tolerance):
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(_same(x, y, tolerance)
                                        for x, y in zip(a, b))
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= tolerance


def reach_ctor(faulted, reading, rate, ctor, tolerance=1e-9):
    """The fault's reading against the clean class built at every value in
    CTOR_VALUES, one option at a time on top of `ctor`, the node watched.
    Raises `kit_faults.FaultReachable` on a match; returns the number of
    constructions checked."""
    checked = 0
    with NodeSpy():
        subject = faulted(src_of(np.zeros(512), 2, rate), **ctor)
        target = reading(subject)
        subject.deinit()
        for name, values in CTOR_VALUES:
            for value in values:
                opts = dict(ctor)
                opts[name] = value
                clean = TapeDelay(src_of(np.zeros(512), 2, rate), **opts)
                got = reading(clean)
                clean.deinit()
                checked += 1
                if _same(got, target, tolerance):
                    raise kit_faults.FaultReachable(
                        "%s: the clean class built with %s=%r reads %r, the "
                        "state the fault forces" % (
                            faulted.__name__, name, value, got))
    return checked


class FaultsAreUnreachable(unittest.TestCase):
    """Every planted fault's reachability walk, at 48, 44.1 and 22.05 kHz,
    reading what the node is handed at each position (11 macros x 17
    positions + 9 patches); and two builds the walk must call reachable, so
    the readings are shown able to fail."""

    CHECKED = 11 * 17 + 9

    def test_every_fault_is_off_the_surface_at_three_rates(self):
        for rate in (48000, 44100, 22050):
            for name, faulted, reading, ctor in REACH_WALKS:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, ctor)
                    self.assertEqual(result["checked"], self.CHECKED)

    def test_every_fault_is_off_the_constructor_values(self):
        # Fix round 1: the walk also visits the constructor values a knob
        # cannot hold (CTOR_VALUES, 23 constructions per fault).
        for rate in (48000, 44100, 22050):
            for name, faulted, reading, ctor in REACH_WALKS:
                with self.subTest(fault=name, rate=rate):
                    self.assertEqual(
                        reach_ctor(faulted, reading, rate, ctor),
                        sum(len(v) for _, v in CTOR_VALUES))

    def test_a_constructor_value_fault_is_called_reachable(self):
        # Station B's step fault, slew 0.98 at Glide 0, is the clean class
        # built at glide_ms 1 204.08: the constructor walk must say so,
        # and the macro walk alone cannot.
        ctor = dict(SLIDE, glide_ms=0.0)
        with self.assertRaises(kit_faults.FaultReachable):
            reach_ctor(WalkAtZeroTape, read_handed_slew, RATE, ctor)
        self.assertEqual(reach(WalkAtZeroTape, read_handed_slew, RATE,
                               ctor)["checked"], self.CHECKED)

    def test_a_dialable_fault_is_called_reachable(self):
        # Spacing forced to 20 um: Spacing MIDI 127 plays it.
        with self.assertRaises(kit_faults.FaultReachable):
            reach(DialableTape, read_damping, RATE, {})
        # The first round's two-line fault is the table Flutter 0 writes.
        with self.assertRaises(kit_faults.FaultReachable):
            reach(NoFlutterLineTape, read_table, RATE, {})
        # Read by the handed corner alone, the T3 faults are the clean
        # class at 350 ms; that is why they are read by the corner's law
        # over Time.
        for faulted, character in ((SquareLawTape, tape.VARISPEED),
                                   (HalfFollowTape, tape.SLIDING_HEAD)):
            with self.assertRaises(kit_faults.FaultInert):
                reach(faulted, read_damping, RATE, {"character": character})

    def test_the_varispeed_walk_is_the_tape_equation_everywhere(self):
        effect = TapeDelay(src_of(np.zeros(RATE)))
        render(effect, 512)
        last = effect._node_ms
        for midi in list(range(0, 128, 8)) + [127]:
            effect.set_macro(TIME_I, midi)
            if effect._node_ms != last:
                self.assertAlmostEqual(
                    effect._slew, abs(effect._node_ms - last)
                    / effect._node_ms, places=12)
            last = effect._node_ms
        for index in range(11):
            if index == TIME_I:
                continue
            for midi in (0, 64, 127):
                effect.set_macro(index, midi)
                self.assertLess(effect._slew, 60.0)


class NullBuildRed(unittest.TestCase):
    """Every demonstrated row goes red on the class built as a wire."""

    def test_every_demonstrated_row_is_red_on_a_wire(self):
        rows = (
            ("T1a", lambda cls: t1a_cell(cls, 200.0, 100.4)),
            ("T1b ramp", lambda cls: ramp_cell(cls)),
            ("T2", lambda cls: t2_one_pass(cls, 350.0, 5.0, tape.VARISPEED)),
            ("T3", lambda cls: t3_cell(cls)),
            ("T4", lambda cls: t4_verdict(*delay_trace(cls, seconds=60.0))),
            # Fix round 1: the step's read-position clause and the
            # per-piece reader.
            ("T1b step", lambda cls: step_cell(cls)),
            ("T1a per piece", lambda cls: walk_cell(
                cls, 600.0, 1200.0, RATE, tape.VARISPEED, TONE * 0.5)),
            ("T1b per piece", lambda cls: walk_cell(
                cls, 400.0, 650.0, RATE, tape.SLIDING_HEAD,
                glide_law_hz(glide_ms_of(10), 400.0, 650.0),
                setup=lambda e: e.set_macro(GLIDE_I, 10))),
        )
        for name, measure in rows:
            result = kit_faults.null_build_red(TapeDelay, measure,
                                               label="TapeDelay %s" % name)
            self.assertFalse(result["null"]["passed"], name)
            self.assertTrue(result["control"]["passed"], name)
            if name == "T4":
                # Fix round 1: red on every clause, not on the ratio alone.
                null = result["null"]
                self.assertFalse(null["two_lines"] or null["ratio_ok"]
                                 or null["drift_ok"], null)


# -- the docstring's claims -----------------------------------------------

#: The board figures the docstring's Cost quotes, in ms per 256-frame stereo
#: block (budget: palette row FeedbackDelay +options with no glue). Measured
#: at audiodsp v0.6.2 (the full class at the default and every patch; patch
#: 8 at `max_time_ms=800`, three runs); re-measured once at the final release.
BOARD_COST = {
    "measured_at": "v0.6.2",
    "budget": {"P4": 0.480, "S3": 0.800},
    "full": {"P4": (0.551, 0.608), "S3": (1.056, 1.093)},
    "lean": {"P4": (0.445, 0.455), "S3": (0.781, 0.797)},
}

#: Every claim the module docstring makes, word for word, and the tests that
#: assert it ("Class.test_name", in this file).
CLAIMS = (
    ("Time is the delay, from 20 to 1200 ms, and Feedback is how much of "
     "each repeat goes round again, up to 0.99.",
     ("Tier1Fast.test_the_control_spans",)),
    ("Mix is the echo return: the dry stays at unity up to Mix 1, Mix 2 is "
     "the repeats alone, and at Mix 0 the output is the input.",
     ("Tier1Fast.test_the_dry_is_unity_until_the_repeat",
      "Tier1Fast.test_mix_2_is_the_repeats_alone",
      "Tier1Fast.test_mix_zero_is_a_wire_on_the_full_scale_ramp")),
    ("Spread feeds each channel's repeats into the other, and does nothing "
     "on a mono source.",
     ("Tier1Fast.test_spread_does_not_silence_mono",
      "Tier1Fast.test_spread_is_handed_as_set")),
    ("With Sync on, Time is Division of the host's beat; with no host "
     "tempo, Time stays where the knob is.",
     ("Tier1Fast.test_the_transport_is_read_only_with_sync_on",
      "Tier1Fast.test_a_host_without_a_tempo_leaves_time_on_the_knob")),
    ("`character=\"varispeed\"`, the default, is the RE-201: Time moves the "
     "motor, so a Time move bends the pitch of everything on the tape "
     "instead of clicking, then settles.",
     ("T1aVarispeed.test_the_named_moves",)),
    ("Glide does nothing on this character.",
     ("GlideIsInertOnVarispeed.test_three_glides_one_render",)),
    ("`character=\"sliding-head\"` is the EP-3: Time slides a head, so the "
     "pitch bends only while the head moves, at the rate Glide sets, and "
     "the tape runs at one speed, so the darkening does not follow Time.",
     ("T1bSlidingHead.test_the_ramp", "TheSurface.test_the_loss_corner")),
    ("Glide 0 is an instant slide, and its price is a click.",
     ("T1bSlidingHead.test_the_step_at_glide_0",)),
    ("A Time move made while the last one is still bending takes its rate "
     "from the last Time you set, not from where the tape has got to, so it "
     "does not telescope as a real motor would.",
     ("Tier1Fast.test_a_move_inside_a_walk_takes_its_rate_from_the_last_time",)),
    ("A long rising move, or a rising slide at the fastest Glides, can read "
     "more than 10 cents off the ideal bend, because the node walks its "
     "read head in single precision.",
     ("T1aVarispeed.test_the_top_binade_per_piece",
      "T1bSlidingHead.test_the_glide_binades")),
    ("The wobble is periodic, not random.",
     ("TheSurface.test_the_table_holds_its_three_components",)),
    ("A Wow or Flutter move that changes only how deep the wobble is glides "
     "in, and one that changes their balance steps, so set the balance "
     "before you play.",
     ("Tier1Fast.test_a_depth_move_does_not_step",
      "Tier1Fast.test_a_balance_move_steps_as_the_docstring_says")),
    ("The darkening follows the tape's loss law only up to a band top that "
     "rises with the tape's speed.",
     ("T2LossLaw.test_one_pass_at_the_named_cells",)),
    ("Record Level has no memory: tape hysteresis is not modelled.",
     ("T5NoMemory.test_record_level_draws_no_hysteresis_loop",)),
    ("The RE-201's Bass and Treble are not here.",
     ("TheSurface.test_macros_characters_tier_latency",)),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     ("Tier1Fast.test_a_balance_move_steps_as_the_docstring_says",)),
    ("When your source ends, the tail rings out as it would on silence.",
     ("Tier1Fast.test_the_tail_rings_out_when_the_source_ends",)),
    ("Latency is zero samples: nothing looks ahead.",
     ("Tier1Fast.test_click_delay_is_zero",)),
    ("`tail_samples` is an upper bound on how long the output takes to "
     "reach exact zero once your input stops, at every Feedback and Spread, "
     "stereo and mono.",
     ("Tier1Fast.test_the_tail_reaches_exact_zero_inside_tail_samples",
      "Tier1Fast.test_the_cross_feed_stall_cells_reach_zero",
      "CrossFeedTailSweep.test_the_tail_ends_at_every_spread")),
    ("Pass a lower `max_time_ms` for a shorter line: Time then stops at "
     "that ceiling, and `get_macro(0)` shows where it stopped.",
     ("LeanPatch.test_the_lean_build_renders_what_the_boards_measured",)),
    ("The class needs audiodsp's `audioecho`, and on a board without it "
     "construction raises `ImportError`.",
     ("Tier1Fast.test_construction_needs_audioecho",)),
    ("`character` must be `\"varispeed\"` or `\"sliding-head\"`.",
     ("TheSurface.test_macros_characters_tier_latency",)),
    ("Measured at v0.6.2 at the default and every patch, the full class "
     "costs 0.551-0.608 ms a block on the P4 and 1.056-1.093 ms on the S3, "
     "over the budgets of 0.480 ms and 0.800 ms.",
     ("Claims.test_the_board_figures_are_the_table",)),
    ("Measured at v0.6.2, patch 8 on a class built with `max_time_ms=800` "
     "costs 0.445-0.455 ms on the P4 and 0.781-0.797 ms on the S3, inside "
     "both budgets.",
     ("Claims.test_the_board_figures_are_the_table",
      "LeanPatch.test_the_lean_build_renders_what_the_boards_measured")),
    ("`reset()` returns to patch 0, so a host that wants the lean patch "
     "sets it again after a reset.",
     ("LeanPatch.test_reset_brings_the_drive_back",)),
)

#: Model names that carry digits and are not figures.
NAMES = ("RE-201", "EP-3")

FAMILY_HEADING = "**Limits shared by the family.**"


def _flat(text):
    return " ".join(text.split())


def claim_problems(doc, claims=CLAIMS):
    """What is wrong between a docstring and `claims`: a sentence missing, a
    named test that does not exist, a digit outside every claim."""
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
    for name in NAMES:
        rest = rest.replace(name, " ")
    for match in re.finditer(r"\S*\d\S*", rest):
        problems.append("figure outside a claim: %s" % match.group())
    return problems


class Claims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        self.assertEqual(claim_problems(tape.__doc__), [])
        self.assertEqual(claim_problems(TapeDelay.__doc__, ()), [])
        self.assertIn(FAMILY_HEADING, _flat(tape.__doc__))
        # The checker can fail: a figure outside a claim, a claim the
        # docstring does not carry, a test that does not exist.
        self.assertTrue(claim_problems(tape.__doc__ + " It reads 12 ms."))
        self.assertTrue(claim_problems(tape.__doc__.replace(
            "nothing looks ahead", "nothing looks back")))
        self.assertTrue(claim_problems(tape.__doc__, CLAIMS + (
            ("The wobble is periodic, not random.",
             ("Tier1Fast.test_nothing_here",)),)))

    def test_the_board_figures_are_the_table(self):
        cost = BOARD_COST
        doc = _flat(tape.__doc__)

        def span(pair):
            return "%.3f-%.3f ms" % pair
        full = ("Measured at %s at the default and every patch, the full "
                "class costs %s a block on the P4 and %s on the S3, over "
                "the budgets of %.3f ms and %.3f ms." % (
                    cost["measured_at"], span(cost["full"]["P4"]),
                    span(cost["full"]["S3"]), cost["budget"]["P4"],
                    cost["budget"]["S3"]))
        lean = ("Measured at %s, patch 8 on a class built with "
                "`max_time_ms=800` costs %s on the P4 and %s on the S3, "
                "inside both budgets." % (
                    cost["measured_at"], span(cost["lean"]["P4"]),
                    span(cost["lean"]["S3"])))
        self.assertIn(full, doc)
        self.assertIn(lean, doc)
        # "over" and "inside" are what the table says.
        for board in ("P4", "S3"):
            self.assertGreater(cost["full"][board][0], cost["budget"][board])
            self.assertLess(cost["lean"][board][1], cost["budget"][board])
        self.assertEqual(TapeDelay.PATCHES[8][0], "Tape Delay - lean")


if __name__ == "__main__":
    unittest.main()
