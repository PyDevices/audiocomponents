"""`SlapbackDelay`'s own invariant and planted-fault tests.

The dossier, frozen at the Station A critique's re-freeze, has Tier 2
rows T1-T5. Each row here is the measurement at a few of the row's
cells and the same measurement shown red on a planted fault of the same
kind, at the constructor defaults (or, for a clause the defaults do not
reach, at the row's own cell, said where it is). Every fault is shown
unreachable from every macro position and shipped patch, and every row's
measurement is shown red on the class built as a wire. The full spans, the
three interpreters and the rates live in the evidence pack, not in this
file.

Every law a measurement checks against is written out here from the
dossier, never taken from the class: the whole-frame landing, the Wow map,
the Time span.

The class is reached by `rebuilt.module_class("SlapbackDelay")`, which is also what
`audioeffects.SlapbackDelay` serves since its adoption on 2026-09-28.

The pin's move to audiodsp v0.6.3rc1 (2026-09-28) took out the tracking
Tone stop and the stall-window stepping: Tone out hands exactly 0 and is
byte-identical to no filter (planted: the retired tracking stop), Repeats
0.5 with Tone in reaches zero as set (planted: the retired stepping), and a
Wow move no longer steps (planted: the read head moved by the whole change
at once). Two surface tests pin the Times the node lands off the whole
frame at 44.1 and 22.05 kHz.
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
import audiomixer                                           # noqa: E402
import audioroute                                           # noqa: E402
import kit_faults                                          # noqa: E402
import kit_probes as probes                                 # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import rebuilt                            # noqa: E402
from audioeffects.chorus import nominal_damping_hz          # noqa: E402
from audioeffects.rebuilt import slapbackdelay as sd        # noqa: E402
from audioeffects.rebuilt.digitaldelay import (             # noqa: E402
    clear_of_stalls as dd_clear_of_stalls)
from tools.effect_measurements import instantaneous_hz      # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
BLOCK = 256
RATES = (48000, 44100, 22050)
TIME_I, LEVEL_I, SATURATION_I, TONE_I, WOW_I, REPEATS_I = range(6)

SlapbackDelay = rebuilt.module_class("SlapbackDelay")


# --------------------------------------------------------------------------
# The dossier's laws, written out independently of the class


def law_frames(time_ms, rate):
    """Section 6: the nearest whole frame, floor(ms fs / 1000 + 0.5)."""
    return int(math.floor(time_ms * rate / 1000.0 + 0.5))


def law_time_ms(midi):
    """Section 6: Time is 40-250 ms, log, on the 0-127 grid."""
    return 40.0 * 6.25 ** (midi / 127.0)


def law_wow_ms(cents):
    """A4: the rising side of a 0.7 Hz wow reaches `cents` at this depth."""
    cents = min(max(cents, 0.0), 3.5)
    return (2.0 ** (cents / 1200.0) - 1.0) / (2.0 * math.pi * 0.7) * 1000.0


def law_wow_frames(cents, rate):
    return int(math.ceil(law_wow_ms(cents) * rate / 1000.0))


#: Section 6's patch table, in engineering units, which `macro_of` puts on
#: the grid: (Time ms, Level, Saturation, Tone Hz, Wow cents, Repeats).
DOSSIER_PATCHES = (
    ("Single Slap", (135.0, 0.35, 0.15, 20000.0, 1.0, 0.0)),
    ("Short Slap", (85.0, 0.35, 0.15, 20000.0, 1.0, 0.0)),
    ("Doubling", (40.0, 0.5, 0.15, 20000.0, 2.0, 0.0)),
    ("Hot Return", (135.0, 0.35, 0.7, 20000.0, 1.0, 0.0)),
    ("Two Repeats", (135.0, 0.35, 0.15, 20000.0, 1.0, 0.35)),
    ("Dark Slap", (135.0, 0.35, 0.15, 5000.0, 1.0, 0.0)),
)
DOSSIER_SPANS = ((40.0, 250.0, "log"), (0.0, 2.0), (0.0, 1.0),
                 (2000.0, 20000.0, "log"), (0.0, 3.5), (0.0, 0.6))


# --------------------------------------------------------------------------
# Planted faults, one or more per Tier 2 row, each of the row's own kind


class Frames441Slapback(SlapbackDelay):
    """Time landed with 44.1 kHz frames at every rate. **Off the surface at
    22.05 kHz only** (fix round 1): there it lands 5 954 frames, past Time's
    250 ms top, and the node clamps it at the line (250.9 ms). At 48 kHz
    the same 5 954 frames are what the clean class plays at `time_ms`
    124.041667 (the gate audit's dial: 0 samples differ), and at 44.1 kHz
    it is the right count. So it is T2's 22.05 kHz fault and nothing
    else; `ShortHalfFrameSlapback` is the delay fault at every rate."""

    NAME = 'SlapbackDelay'

    def _node_time_ms(self, frames):
        del frames
        return law_frames(self._time_ms(), 44100) * 1000.0 / self._sample_rate


class ShortHalfFrameSlapback(SlapbackDelay):
    """T1's delay clause and T2 (fix round 1): Time landed 8 % short and
    half a frame over, `floor(0.92 T) + 0.5` frames. The clean class lands
    every Time on a whole frame, so no Time position or constructor value
    hands the node a fraction; at the defaults the repeat comes 124.2 ms
    after the dry at every rate."""

    NAME = 'SlapbackDelay'

    def _node_time_ms(self, frames):
        return ((int(0.92 * frames) + 0.5) * 1000.0 / self._sample_rate)


class FloorSlapback(SlapbackDelay):
    """**Retired at fix round 1.** A floor on the loop gain, Repeats 0
    handing the node 0.05. The clean class renders the same bytes at
    Repeats 0.05 (`set_macro(5, 10.5833)`), so it is a surface state, not
    a fault; `TheRetiredFaultsAreDialable` keeps that as a test."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if self._feedback <= 0.0:
            self._delay.set(feedback=0.05)


#: The second node's mix: at Level 0.35 the 2T copy is 0.35 x 0.0614 of the
#: click against a first repeat of 0.35 + 0.0614, about -26 dB.
SECOND_MIX = 0.0614


class HalfFrameSlapback(SlapbackDelay):
    """The whole-frame landing's surface test: Time handed half a frame
    over the whole frame, so the repeat splits across two frames."""

    NAME = 'SlapbackDelay'

    def _node_time_ms(self, frames):
        return (frames + 0.5) * 1000.0 / self._sample_rate


class SecondRepeatSlapback(SlapbackDelay):
    """T1's no-second-repeat clause (fix round 1): a second node after the
    first, at the same whole-frame Time, dry at unity and 0.0614 wet. It
    puts a copy of the first repeat at 2T, about 26 dB down, and nothing at
    3T or 4T. Every Repeats setting above 0 puts energy at 3T as well, so
    no surface state renders a lone 2T repeat."""

    NAME = 'SlapbackDelay'

    def _build(self, **options):
        self._second = None
        SlapbackDelay._build(self, **options)
        second = audioecho_node(self._sample_rate, self._channel_count)
        second.play(self._delay)
        self._own(second, reset=second.clear)
        self._second = second
        self._output = second
        self._refresh()

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if getattr(self, "_second", None) is not None:
            self._second.set(delay_slew=sd.SLEW, delay_ms=self._node_ms,
                             feedback=0.0, mix=SECOND_MIX, loop_drive=0.0,
                             damping_hz=0.0, cut_hz=0.0, wow_hz=sd.WOW_HZ,
                             wow_depth_ms=0.0)


#: The split build's crossover and its offset, as a fraction of T.
SPLIT_HZ = 4000.0
SPLIT_SHIFT = 0.004


class SplitSlapback(SlapbackDelay):
    """T2's agreement clause (Station A's split build, run on the class at
    fix round 1): the source split in two, one node reading 0.4 % early
    through the loop low-pass at 4 kHz with the dry, and a second, wet only,
    reading 0.4 % late through the loop high-pass at the same coefficient.
    The low-pass and high-pass sum to the identity, so each band's comb is
    a clean 1/T', and the two bands' spacings differ by 0.8 %. The late
    node reads on a whole frame (Wow 0): with the class's wow on it too,
    the split reads -0.03 % between the fits at 22.05 kHz at click 100,
    green, and -0.75 to -0.84 % at other wow phases. The class builds one
    node, so no surface state hands two delays."""

    NAME = 'SlapbackDelay'

    def _build(self, **options):
        self._high = None
        SlapbackDelay._build(self, **options)
        rate, channels = self._sample_rate, self._channel_count
        split = audioroute.Splitter(self._source, taps=2)
        low_in, high_in = split.tap(0), split.tap(1)
        self._delay.play(low_in)
        high = audioecho_node(rate, channels)
        high.play(high_in)
        mixer = audiomixer.Mixer(voice_count=2, **self._pcm(1024))
        mixer.voice[0].play(self._delay, loop=True)
        mixer.voice[1].play(high, loop=True)
        mixer.voice[0].level = 1.0
        self._own(mixer, reset=False)
        self._own(high, reset=high.clear)
        self._own(low_in, reset=False)
        self._own(high_in, reset=False)
        self._own(split, reset=False)
        self._high, self._mixer = high, mixer
        self._output = mixer
        self._refresh()

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if getattr(self, "_high", None) is None:
            return
        rate = self._sample_rate
        shift = int(round(SPLIT_SHIFT * self._frames))
        corner = nominal_damping_hz(self._hz(SPLIT_HZ), rate)
        self._delay.set(delay_ms=(self._frames - shift) * 1000.0 / rate,
                        damping_hz=corner)
        self._high.set(delay_slew=sd.SLEW,
                       delay_ms=(self._frames + shift) * 1000.0 / rate,
                       feedback=0.0, mix=2.0,
                       loop_drive=self._value(SATURATION_I), damping_hz=0.0,
                       cut_hz=corner, wow_hz=sd.WOW_HZ, wow_depth_ms=0.0)
        self._mixer.voice[1].level = min(self._value(LEVEL_I), 1.0)


def audioecho_node(rate, channels):
    """A bare node on the class's line, for the faults that add one."""
    return sd.audioecho.FeedbackDelay(
        sample_rate=rate, channel_count=channels, max_delay_ms=sd.LINE_MS,
        delay_ms=135.0, feedback=0.0, mix=0.0, damping_hz=0.0, cut_hz=0.0,
        delay_slew=0.0)


class PannedSlapback(SlapbackDelay):
    """T3: the node handed `input_pan` -0.2, so the repeat leans left."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        self._delay.set(input_pan=-0.2)


class OpenTopSlapback(SlapbackDelay):
    """**Retired as T4's walked fault at fix round 1.** The top stop hands
    the node the pre-warped 20 kHz (13 095.11 Hz at 48 kHz) instead of
    exactly 0. No macro position reaches it at 48 and 44.1 kHz, but the
    constructor's `tone_hz=19999.999` renders it byte for byte at three
    rates, and at 22.05 kHz grid 94-126 hand the same 6 183.68. It stays
    as a red on the out clause; `RawTopSlapback` is the walked fault."""

    NAME = 'SlapbackDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return nominal_damping_hz(self._hz(20000.0), self._sample_rate)
        return SlapbackDelay._tone_damping(self, position)


class RawTopSlapback(SlapbackDelay):
    """T4's out clause (fix round 1): the top stop hands the node a raw
    `damping_hz` of 20 000, not 0. Every in-circuit position and
    constructor value hands a pre-warped corner, at most 13 095.11 /
    12 266.31 / 6 183.68 Hz at 48 / 44.1 / 22.05 kHz, so nothing on the
    surface hands 20 000 or renders its coefficient."""

    NAME = 'SlapbackDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return 20000.0
        return SlapbackDelay._tone_damping(self, position)


class RawToneSlapback(SlapbackDelay):
    """T4's corner clauses: Tone handed raw, not pre-warped. Silent at the
    defaults (Tone out hands 0 either way). Read at the 15 kHz cell, where
    the one-pole then has no half-power point below Nyquist. On the shipped
    patches it stays inside the bar at 48 and 44.1 kHz (patch 5's raw
    5 042 Hz lands +3.87 / +4.63 % off), and at 22.05 kHz patch 5 reads
    +24.92 %, red: the corners have a fault red at a shipped patch there
    (`test_a_raw_tone_is_red_at_patch_5_at_22k`)."""

    NAME = 'SlapbackDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return 0.0
        corner = _component.macro_value(self._MACRO_RANGES[TONE_I], position)
        return self._hz(corner)


class NoTwoPiSlapback(SlapbackDelay):
    """T5: the depth map without its 2 pi, a 6.3x deeper wobble."""

    NAME = 'SlapbackDelay'

    def _wow_depth_ms(self, cents):
        return sd.wow_depth_ms(cents) * 2.0 * math.pi


class NoWowTailSlapback(SlapbackDelay):
    """Tier 1's tail: the bound without the wow's depth, which the repeat
    of a burst outlives by the frames the wow moves it late."""

    NAME = 'SlapbackDelay'

    @property
    def tail_samples(self):
        memory, excess = sd.tone_excess(self._damping, self._sample_rate)
        laps = sd.laps_to_zero(self._feedback, excess)
        return int(laps * (self._reach + 1 + memory))


class SteppedSlapback(SlapbackDelay):
    """The workaround retired at audiodsp v0.6.3rc1: with Tone in, Repeats
    handed to the node at the nearer edge of the stall window at 0.5
    (`clear_of_stalls`), a Feedback nobody set."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if self._damping > 0.0 and self._feedback > 0.0:
            excess = sd.tone_excess(self._damping, self._sample_rate)[1]
            self._feedback = dd_clear_of_stalls(self._feedback, excess)
            self._delay.set(feedback=self._feedback)


class FrozenToneSlapback(SlapbackDelay):
    """Tier 1's silence clause after a Tone move: the out stop leaves the
    low-pass in at 0.001 Hz, where its float32 coefficient is one step
    above 0 and its state cannot move, so it holds what it held, as the
    node's out stop did up to v0.6.2 (the review's stale-state defect),
    and plays it out of silence."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if self._macros[TONE_I] >= 1.0:
            self._delay.set(damping_hz=0.001)


class TrackingSlapback(SlapbackDelay):
    """The workaround retired at audiodsp v0.6.3rc1: once Tone has been in,
    the out stop hands `damping_hz` at 32 x the rate instead of 0."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if self._damping > 0.0:
            self._was_in = True
        elif getattr(self, "_was_in", False):
            self._delay.set(damping_hz=32.0 * self._sample_rate)

    def _clear(self):
        SlapbackDelay._clear(self)
        self._was_in = False


class JumpWowSlapback(SlapbackDelay):
    """Tier 1's click-free Wow: a Wow move that moves the read head by the
    whole change in depth at once, as the node did at the wow's crest up to
    v0.6.2 (it added depth x wow with no ramp)."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        old = self._wow_ms
        SlapbackDelay._refresh(self)
        if not self._seeding and not self._deferred and self._wow_ms != old:
            self._delay.set(delay_slew=0.0,
                            delay_ms=self._node_ms + self._wow_ms - old)


class TargetOnlyTailSlapback(SlapbackDelay):
    """Tier 1's tail after a falling move: the bound from the target Time
    alone, while the read head is still walking down from the old one."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        self._reach = self._frames


class EchoForgetsTimeSlapback(SlapbackDelay):
    """Time's readback (fix round 1): any Time move drops the constructor's
    exact Time, as the class did before, so a host echoing `get_macro(0)`
    back moves the 44.1 kHz default from 5 954 frames to 5 953."""

    NAME = 'SlapbackDelay'

    def _apply_macro(self, index, position):
        if index == TIME_I and not self._seeding:
            self._time_exact = None
        if not self._deferred:
            self._refresh()


class JumpTimeSlapback(SlapbackDelay):
    """A Time move that jumps: the node's walk turned off, so the read head
    lands on the new Time at once (trial, 2026-09-29)."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        self._delay.set(delay_slew=0.0)


# --------------------------------------------------------------------------
# Sources and pulls


def to_source(values, channels=2, rate=RATE):
    """A mono sequence, copied to every channel."""
    x = np.clip(np.round(np.asarray(values, dtype=np.float64)),
                -32768, 32767).astype(np.int16)
    data = array("h", np.repeat(x[:, None], channels, axis=1)
                 .reshape(-1).tobytes())
    return probes.ArraySource(data, rate=rate, channels=channels,
                              block=BLOCK), data


def silence_src(frames, channels=2, rate=RATE):
    return probes.ArraySource(array("h", [0] * (frames * channels)),
                              rate=rate, channels=channels, block=BLOCK)


def pull(effect, frames, channels=None, on_block=None):
    """(frames, channels) int16; `on_block(frame)` runs before each block."""
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
    return np.array(out[:frames * channels],
                    dtype=np.int16).reshape(-1, channels)


def render(cls, values, rate=RATE, channels=2, macros=None, **options):
    """`values` through `cls` built with `options`, then `macros`
    ({index: MIDI}) set, so a macro can be held over a patch."""
    source, _ = to_source(values, channels, rate)
    effect = cls(source, sample_rate=rate, **options)
    for index in sorted(macros or {}):
        effect.set_macro(index, macros[index])
    return pull(effect, len(values), channels)


def cell_time_and_wow(options):
    """The cell's Time and Wow by the dossier's laws: a constructor value
    as given, a patch at its grid values."""
    if "patch" in options:
        midi = SlapbackDelay.PATCHES[options["patch"]][1]
        return law_time_ms(midi[TIME_I]), 3.5 * midi[WOW_I] / 127.0
    return options.get("time_ms", 135.0), options.get("wow_cents", 1.0)


# --------------------------------------------------------------------------
# T1: one repeat, and no second one


def t1_read(cls, rate=RATE, channels=2, click_lsb=32767, **options):
    """The click response at frame 0: energy in the windows
    +-k (ceil(wow) + 2) frames around kT (+64 with Tone in), k = 1..4, and
    the delay in ms by the centroid around the first non-zero sample after
    the click, wherever it lands."""
    time_ms, wow = cell_time_and_wow(options)
    T = law_frames(time_ms, rate)
    w = law_wow_frames(wow, rate)
    tone_in = options.get("tone_hz", 20000.0) < 20000.0
    tail = 64 if tone_in else 0
    n = int(4.6 * T) + 200
    x = np.zeros(n)
    x[0] = click_lsb
    y = render(cls, x, rate, channels, **options)[:, 0]
    energies = []
    for k in (1, 2, 3, 4):
        lo = max(0, k * T - k * (w + 2))
        hi = k * T + k * (w + 2) + tail + 1
        energies.append(float((y[lo:hi].astype(float) ** 2).sum()))
    nonzero = np.nonzero(y[1:])[0]
    if not len(nonzero):
        return energies, float("nan")
    lo = int(nonzero[0]) + 1
    seg = np.abs(y[lo:lo + 2 * (w + 2) + tail + 1].astype(float))
    centroid = lo + float((np.arange(len(seg)) * seg).sum() / seg.sum())
    return energies, centroid * 1000.0 / rate


def t1_measure(cls, rate=RATE, channels=2, click_lsb=32767, delay_bar=True,
               **options):
    """Repeats 0: a first repeat, exact zero in the 2T-4T windows, and (at
    the defaults) the delay in 130-140 ms."""
    energies, delay_ms = t1_read(cls, rate, channels, click_lsb, **options)
    red = []
    if energies[0] <= 0.0:
        red.append("no first repeat")
    if any(e > 0.0 for e in energies[1:]):
        red.append("a 2T-4T window is not exact zero")
    if delay_bar and not 130.0 <= delay_ms <= 140.0:
        red.append("delay %.3f ms" % delay_ms)
    second = (10.0 * math.log10(energies[1] / energies[0])
              if energies[0] > 0.0 and energies[1] > 0.0 else None)
    return {"passed": not red, "red": red, "delay_ms": delay_ms,
            "second_db": second}


def t1_control(cls, rate=RATE, **options):
    """At Repeats above 0 the 2T window carries more than -20 dB re the
    first."""
    energies, _ = t1_read(cls, rate, **options)
    if energies[0] <= 0.0 or energies[1] <= 0.0:
        return {"passed": False, "second_db": None}
    second = 10.0 * math.log10(energies[1] / energies[0])
    return {"passed": second > -20.0, "second_db": second}


# --------------------------------------------------------------------------
# T2: the comb's teeth are 1/T


PAD_S = 20.0


#: The first tooth: the first local maximum of the autocorrelation at or
#: above this fraction of its tallest (fix round 1).
FIRST_TOOTH = 0.5


def comb_guess(mag, bin_hz, minimum_hz=1.0):
    """The spacing's first guess: an autocorrelation along frequency, by
    FFT, 1 Hz floor, taking its **first** tooth. It takes no law.

    Fix round 1: the tallest tooth is not always the first. Where 1/T
    falls near half a bin of the 20 s pad, the first tooth is sampled off
    its top and the second outranks it (Time grid 117, 120 and 124 at 48
    and 44.1 kHz), and the notches were then numbered two to a gap. Every
    tooth of a comb's autocorrelation stands at nearly the same height, so
    the first local maximum at or above half the tallest is the first
    tooth."""
    m = mag - mag.mean()
    size = 1 << int(math.ceil(math.log(2 * len(m), 2)))
    spec = np.fft.rfft(m, n=size)
    corr = np.fft.irfft(spec * np.conj(spec), n=size)[:len(m)]
    low = max(1, int(minimum_hz / bin_hz))
    c = corr[low:]
    tall = FIRST_TOOTH * float(c.max())
    tops = np.nonzero((c[1:-1] > c[:-2]) & (c[1:-1] >= c[2:])
                      & (c[1:-1] >= tall))[0]
    peak = low + (int(tops[0]) + 1 if len(tops) else int(np.argmax(c)))
    y0, y1, y2 = corr[peak - 1], corr[peak], corr[peak + 1]
    den = y0 - 2 * y1 + y2
    off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
    return (peak + off) * bin_hz


def old_comb_guess(mag, bin_hz, minimum_hz=1.0):
    """The guess before fix round 1, kept as a planted fault: the
    autocorrelation's tallest tooth, which is sometimes the second."""
    m = mag - mag.mean()
    size = 1 << int(math.ceil(math.log(2 * len(m), 2)))
    spec = np.fft.rfft(m, n=size)
    corr = np.fft.irfft(spec * np.conj(spec), n=size)[:len(m)]
    low = max(1, int(minimum_hz / bin_hz))
    peak = low + int(np.argmax(corr[low:]))
    y0, y1, y2 = corr[peak - 1], corr[peak], corr[peak + 1]
    den = y0 - 2 * y1 + y2
    off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
    return (peak + off) * bin_hz


def notch_spacing(mag, bin_hz, lo, hi, guess):
    """Notches as local minima (parabolic sub-bin), numbered by consecutive
    gaps, spacing by least squares. (nan, count) under three notches."""
    a, b = int(lo / bin_hz), int(hi / bin_hz)
    half = max(2, int(0.4 * guess / bin_hz))
    freqs = []
    k = a + half
    while k < b - half:
        seg = mag[k - half:k + half + 1]
        j = int(np.argmin(seg))
        if j == half and seg.max() - seg.min() > 1e-9 * max(seg.max(), 1):
            y0, y1, y2 = mag[k - 1], mag[k], mag[k + 1]
            den = y0 - 2 * y1 + y2
            off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
            freqs.append((k + off) * bin_hz)
            k += half
        else:
            k += 1
    if len(freqs) < 3:
        return float("nan"), len(freqs)
    freqs = np.array(freqs)
    index = np.concatenate([[0.0], np.cumsum(np.round(np.diff(freqs)
                                                      / guess))])
    return float(np.polyfit(index, freqs, 1)[0]), len(freqs)


def t2_measure(cls, rate=RATE, click_lsb=32767, click_at=100, **options):
    """The click response at Level 0.35, zero-padded to 20 s: the notch
    spacing over 200 Hz-2 kHz and 8-10 kHz, each within 0.5 % of 1/T and
    within 0.5 % of each other."""
    time_ms, _ = cell_time_and_wow(options)
    T = law_frames(time_ms, rate)
    law = rate / float(T)
    n = click_at + T + 400
    x = np.zeros(n)
    x[click_at] = click_lsb
    y = render(cls, x, rate, 2, **options)[:, 0].astype(float)
    size = int(PAD_S * rate)
    mag = np.abs(np.fft.rfft(y, n=size))
    bin_hz = rate / float(size)
    return t2_read(mag, bin_hz, law)


def t2_read(mag, bin_hz, law):
    """The fits on a magnitude spectrum. A fit that raises (a `LinAlgError`
    from `polyfit`) reads red and is reported, never skipped."""
    guess = comb_guess(mag, bin_hz)
    try:
        low, low_n = notch_spacing(mag, bin_hz, 200.0, 2000.0, guess)
        high, high_n = notch_spacing(mag, bin_hz, 8000.0, 10000.0, guess)
    except Exception as exc:        # noqa: BLE001 - a crash is a red cell
        nan = float("nan")
        return {"passed": False, "deviations": (nan, nan, nan),
                "notches": (0, 0), "guess": guess,
                "crash": type(exc).__name__}
    deviations = (100.0 * (low - law) / law, 100.0 * (high - law) / law,
                  100.0 * (high - low) / low)
    passed = all(abs(d) <= 0.5 for d in deviations)   # NaN reads red
    return {"passed": passed, "deviations": deviations,
            "notches": (low_n, high_n), "guess": guess, "crash": None}


# --------------------------------------------------------------------------
# T3: mono, the dry's position, and present


def t3_measure(cls, rate=RATE, **options):
    """On the channel-identical full-scale ramp: max |L - R| is 0 LSB, the
    one-channel render is the stereo render's left channel sample for
    sample, and at Level 2 the output is exact zero before T - (ceil(wow)
    + 2) frames and carries the probe's energy, shifted by T, within
    4 dB."""
    time_ms, wow = cell_time_and_wow(options)
    T = law_frames(time_ms, rate)
    w = law_wow_frames(wow, rate) + 2
    frames = T + 4096
    ramp = probes.ramp_fs(frames=frames, channels=1)
    stereo = render(cls, ramp, rate, 2, **options)
    mono = render(cls, ramp, rate, 1, **options)[:, 0]
    lr = int(np.abs(stereo[:, 0].astype(np.int32)
                    - stereo[:, 1].astype(np.int32)).max())
    mono_diff = int(np.count_nonzero(mono != stereo[:, 0]))
    wet = render(cls, ramp, rate, 2, macros={LEVEL_I: 127}, **options)
    head = int(np.count_nonzero(wet[:T - w]))
    y = wet[T - w:, 0].astype(float)
    s = np.array(ramp, dtype=np.float64)[:frames - T + w]
    energy_db = 10.0 * math.log10(max((y ** 2).sum(), 1e-12)
                                  / (s ** 2).sum())
    wet_lr = int(np.abs(wet[:, 0].astype(np.int32)
                        - wet[:, 1].astype(np.int32)).max())
    passed = (lr == 0 and wet_lr == 0 and mono_diff == 0 and head == 0
              and abs(energy_db) <= 4.0)
    return {"passed": passed, "lr": max(lr, wet_lr), "mono_diff": mono_diff,
            "head": head, "energy_db": energy_db}


#: T3's presence on steady tones, as measured (re-audit fix round 1,
#: dossier revision). No band is claimed: two sentences that claimed one
#: were each disconfirmed (fix rounds 1 and 2). The 4 dB bar is the frozen
#: row's, on `ramp_fs` and `sweep_log`. On a steady tone the repeat's level
#: depends on the frequency (the wow's fractional read, section 8.3, takes
#: the top of the band down) and on the level (Saturation's cubic takes a
#: full-scale tone down), and this table is what the class reads: Level 2,
#: `presence_db`, a 2 s tone, head 0 in every cell. Keys are (cell,
#: options, dBFS, fraction of the rate); values are dB at 48 / 44.1 /
#: 22.05 kHz. Any reading more than PRESENCE_PIN_DB from its entry is red,
#: so the words cannot drift from the class either way.
PRESENCE_TABLE = (
    ("defaults", {}, -20.0, 1.0 / 3.0, (-2.90, -3.29, -3.01)),
    ("Saturation 1", {"saturation": 1.0}, -20.0, 1.0 / 3.0,
     (-2.91, -3.30, -3.02)),
    ("patch 3", {"patch": 3}, -20.0, 1.0 / 3.0, (-2.81, -3.37, -3.11)),
    ("defaults", {}, 0.0, 1.0 / 3.0, (-3.09, -3.47, -3.20)),
    ("Saturation 1", {"saturation": 1.0}, 0.0, 1.0 / 3.0,
     (-4.29, -4.57, -4.35)),
    ("patch 3", {"patch": 3}, 0.0, 1.0 / 3.0, (-3.78, -4.24, -4.01)),
    ("Saturation 1", {"saturation": 1.0}, 0.0, 0.30, (-3.87, -4.08, -3.92)),
    ("Saturation 1", {"saturation": 1.0}, -3.0, 1.0 / 3.0,
     (-3.57, -3.92, -3.66)),
)
PRESENCE_PIN_DB = 0.02


def dbfs_amp(dbfs):
    return 32767.0 * 10.0 ** (dbfs / 20.0)


def presence_db(cls, values, rate=RATE, **options):
    """Level 2: (non-zero frames before T - (ceil(wow) + 2), the energy
    after that against the source's over the same number of frames)."""
    time_ms, wow = cell_time_and_wow(options)
    T = law_frames(time_ms, rate)
    w = law_wow_frames(wow, rate) + 2
    y = render(cls, values, rate, 2, macros={LEVEL_I: 127},
               **options)[:, 0].astype(float)
    wet = y[T - w:]
    s = np.asarray(values, dtype=np.float64)[:len(wet)]
    return (int(np.count_nonzero(y[:T - w])),
            10.0 * math.log10(max((wet ** 2).sum(), 1e-12)
                              / (s ** 2).sum()))


def tone(hz, rate, seconds=2.0, amp=3277):
    n = int(seconds * rate)
    return np.round(amp * np.sin(2.0 * math.pi * hz * np.arange(n) / rate))


# --------------------------------------------------------------------------
# T4: Tone's number is the corner it achieves, and out is out


#: T4's out clause material since fix round 1: 0 dBFS `noise_det`, 4 s. The
#: full-scale ramp reads 0 differing in every Tone-out state, so it could
#: not see the 1 LSB the coefficient-1 stop leaves on a fractional tap.
OUT_SECONDS = 4.0


def node_pull(rate, channels, data, **options):
    """`data` through a bare node on the class's 251 ms line."""
    node = sd.audioecho.FeedbackDelay(sample_rate=rate,
                                      channel_count=channels,
                                      max_delay_ms=251.0, **options)
    node.play(probes.ArraySource(data, rate=rate, channels=channels,
                                 block=BLOCK))
    out = array("h")
    while len(out) < len(data):
        chunk = bytes(audiocore.get_buffer(node)[1])
        if not chunk:
            break
        out.extend(memoryview(chunk).cast("h"))
    return np.array(out[:len(data)], dtype=np.int16)


def t4_out_differing(cls, rate=RATE, channels=2, seconds=OUT_SECONDS):
    """The class at its defaults (Tone out) against a node given no
    `damping_hz`, at the dossier's settings for the defaults, on 0 dBFS
    `noise_det`: the samples that differ."""
    frames = int(seconds * rate)
    data = probes.noise_det(frames=frames, dbfs=0.0, channels=channels)
    effect = cls(probes.ArraySource(data, rate=rate, channels=channels,
                                    block=BLOCK), sample_rate=rate)
    out = pull(effect, frames, channels).reshape(-1)
    ref = node_pull(rate, channels, data,
                    delay_ms=law_frames(135.0, rate) * 1000.0 / rate,
                    feedback=0.0, mix=0.35, loop_drive=0.15, wow_hz=0.7,
                    wow_depth_ms=law_wow_ms(1.0), delay_slew=0.1875)
    return int(np.count_nonzero(out != ref))


def t4_out_history(cls, rate=RATE, channels=2, seconds=OUT_SECONDS,
                   steps=(), **ctor):
    """The restated out clause: build with `ctor`, apply `steps` (patch
    indices, or (macro, MIDI) pairs) before the first pull, and compare
    with a node given every option the class handed except `damping_hz`,
    on 0 dBFS `noise_det`. (differing, max |difference|, handed
    `damping_hz`)."""
    frames = int(seconds * rate)
    data = probes.noise_det(frames=frames, dbfs=0.0, channels=channels)
    with NodeSpy():
        effect = cls(probes.ArraySource(data, rate=rate, channels=channels,
                                        block=BLOCK), sample_rate=rate,
                     **ctor)
        for step in steps:
            if isinstance(step, tuple):
                effect.set_macro(*step)
            else:
                effect.program_change(step)
        handed = dict(effect._delay._handed)
    out = pull(effect, frames, channels).reshape(-1)
    damping = handed.pop("damping_hz")
    ref = node_pull(rate, channels, data, **handed)
    d = np.abs(out.astype(np.int32) - ref.astype(np.int32))
    return int(np.count_nonzero(d)), int(d.max()), damping


def t4_ratio(cls, tone_hz, rate=RATE):
    """(freqs, dB): the click response at 8 192 LSB with Tone at `tone_hz`
    over the same class's Tone-out response, one pass, wet only,
    Saturation 0, Wow 0, Time 135 ms, a 65 536-point FFT."""
    T = law_frames(135.0, rate)
    size = 65536
    n = T + size
    x = np.zeros(n)
    x[0] = 8192
    common = {"time_ms": 135.0, "level": 2.0, "saturation": 0.0,
              "wow_cents": 0.0, "repeats": 0.0}
    y_in = render(cls, x, rate, 2, tone_hz=tone_hz, **common)[:, 0]
    y_out = render(cls, x, rate, 2, tone_hz=20000.0, **common)[:, 0]
    a = np.abs(np.fft.rfft(y_in[T - 32:T - 32 + size].astype(float)))
    b = np.abs(np.fft.rfft(y_out[T - 32:T - 32 + size].astype(float)))
    freqs = np.fft.rfftfreq(size, 1.0 / rate)
    return freqs, 20.0 * np.log10(np.maximum(a, 1e-12) / np.maximum(b, 1e-12))


def half_power_hz(freqs, db):
    """The first -3.01 dB crossing, interpolated; `None` below Nyquist
    never."""
    below = np.nonzero(db[1:] < -3.0103)[0]
    if not len(below):
        return None
    i = int(below[0]) + 1
    f0, f1, d0, d1 = freqs[i - 1], freqs[i], db[i - 1], db[i]
    return float(f0 + (f1 - f0) * (-3.0103 - d0) / (d1 - d0))


def t4_corner(cls, tone_hz, label, rate=RATE, passband=False):
    """The half-power point within +-10 % of the cell's `label`; with
    `passband`, 30 Hz within 0.05 dB, 1 kHz within 0.1 dB and nothing more
    than 3.1 dB down in 30 Hz-15 kHz."""
    freqs, db = t4_ratio(cls, tone_hz, rate)
    corner = half_power_hz(freqs, db)
    passed = corner is not None and abs(corner / label - 1.0) <= 0.10
    values = {"corner": corner}
    if passband:
        at = lambda hz: float(db[int(np.argmin(np.abs(freqs - hz)))])  # noqa: E731
        band = (freqs >= 30.0) & (freqs <= 15000.0)
        values.update(at30=at(30.0), at1k=at(1000.0),
                      worst=float(db[band].min()))
        passed = (passed and abs(values["at30"]) <= 0.05
                  and abs(values["at1k"]) <= 0.1 and values["worst"] >= -3.1)
    values["passed"] = passed
    return values


def t4_measure(cls, rate=RATE):
    """The out stop byte-identical to no `damping_hz`, and the 15 kHz and
    2 kHz corners."""
    differing = t4_out_differing(cls, rate)
    top = t4_corner(cls, 15000.0, 15000.0, rate, passband=True)
    bottom = t4_corner(cls, 2000.0, 2000.0, rate)
    return {"passed": differing == 0 and top["passed"] and bottom["passed"],
            "differing": differing, "top": top, "bottom": bottom}


# --------------------------------------------------------------------------
# T5: Wow's cents are real cents


def t5_cents(cls, rate=RATE, amp=12000, saturation=0.15, **options):
    """The repeat's pitch deviation at the 0.7 Hz wow rate, rising side, in
    cents: 440 Hz, Level 2, Repeats 0, Tone out, Time 135 ms, 2 s from the
    first repeat; the kit's `instantaneous_hz`, 5 % trimmed at each end,
    least squares on a constant plus a cosine and a sine at 0.7 Hz."""
    T = law_frames(135.0, rate)
    n = T + 2 * rate
    x = amp * np.sin(2.0 * math.pi * 440.0 * np.arange(n) / rate)
    options.setdefault("time_ms", 135.0)
    y = render(cls, x, rate, 2, macros={LEVEL_I: 127}, repeats=0.0,
               saturation=saturation, **options)[:, 0].astype(float)
    f = instantaneous_hz(y[T + 64:], rate)
    edge = int(0.05 * len(f))
    f = f[edge:len(f) - edge]
    t = (np.arange(len(f)) + edge) / float(rate)
    angle = 2.0 * math.pi * 0.7 * t
    design = np.vstack([np.ones(len(f)), np.cos(angle), np.sin(angle)]).T
    coef = np.linalg.lstsq(design, f, rcond=None)[0]
    return 1200.0 * math.log(1.0 + math.hypot(coef[1], coef[2]) / coef[0],
                             2.0)


def t5_measure(cls, rate=RATE):
    """1.0 +- 0.25 cents at the default, 3.5 +- 0.5 at the top, under 0.05
    at zero."""
    default = t5_cents(cls, rate)
    top = t5_cents(cls, rate, wow_cents=3.5)
    zero = t5_cents(cls, rate, wow_cents=0.0)
    passed = (abs(default - 1.0) <= 0.25 and abs(top - 3.5) <= 0.5
              and zero < 0.05)
    return {"passed": passed, "default": default, "top": top, "zero": zero}


# --------------------------------------------------------------------------
# Tier 1 helpers


def tail_measure(cls, rate=RATE, burst_ms=50.0, burst_lsb=32767,
                 **options):
    """A full-scale DC burst, then silence: the frames from the burst's end
    to the output's last non-zero frame, against the declared
    `tail_samples`."""
    probe = cls(silence_src(64, 2, rate), sample_rate=rate, **options)
    declared = probe.tail_samples
    probe.deinit()
    burst = int(burst_ms * rate / 1000.0)
    n = burst + declared + rate // 2
    x = np.zeros(n)
    x[:burst] = burst_lsb
    y = render(cls, x, rate, 2, **options)[:, 0]
    nonzero = np.nonzero(y[burst:])[0]
    last = int(nonzero[-1]) + 1 if len(nonzero) else 0
    return {"passed": 0 < last <= declared, "declared": declared,
            "last": last, "held": int(np.abs(y[-rate // 4:]).max())}


def railed_samples(cls, dbfs, seconds=4.0, rate=RATE, **options):
    """`noise_det` at `dbfs` peak, 48 kHz stereo: output samples on the
    int16 rail that are not on it in the source."""
    frames = int(seconds * rate)
    data = probes.noise_det(frames=frames, dbfs=dbfs, channels=2)
    effect = cls(probes.ArraySource(data, rate=rate, channels=2,
                                    block=BLOCK), sample_rate=rate, **options)
    out = pull(effect, frames, 2).reshape(-1).astype(np.int64)
    src = np.array(data, dtype=np.int64)
    rail = (out >= 32767) | (out <= -32768)
    return int(np.count_nonzero(rail & ~((src >= 32767) | (src <= -32768))))


# --------------------------------------------------------------------------
# Reachability: what the node is handed at the position walked


class NodeSpy:
    """While active, every `audioecho.FeedbackDelay.set` call records its
    options on the node as `_handed` (the latest value of each)."""

    def __enter__(self):
        node_class = sd.audioecho.FeedbackDelay
        original = node_class.set
        self._restore = (node_class, original)

        def watched(node, **options):
            if not hasattr(node, "_handed"):
                node._handed = {}
            node._handed.update(options)
            return original(node, **options)

        node_class.set = watched
        return self

    def __exit__(self, *exc):
        node_class, original = self._restore
        node_class.set = original
        return False


# Every reading below is a value the node was handed, and nothing else: no
# knob position, no label, no law (fix round 1; the gate audit found
# `read_landing_error` 0 by construction and `read_floor` carrying the
# label "Repeats at 0").


def delay_nodes(effect):
    return [node for node in effect._nodes
            if isinstance(node, sd.audioecho.FeedbackDelay)]


def read_fraction(effect):
    """How far the handed delay sits from a whole frame at the running
    rate, to 1e-6 of a frame."""
    rate = effect._sample_rate
    frames = float(effect._delay._handed["delay_ms"]) * rate / 1000.0
    return round(abs(frames - math.floor(frames + 0.5)), 6)


def read_delays(effect):
    """The handed delay of every node the class owns, in frames to 1e-3:
    one entry on the clean class at every position."""
    rate = effect._sample_rate
    return tuple(sorted(round(float(node._handed["delay_ms"]) * rate
                              / 1000.0, 3) for node in delay_nodes(effect)))


def read_frames(effect):
    """The handed delay in frames, to 1e-3."""
    return round(float(effect._delay._handed["delay_ms"])
                 * effect._sample_rate / 1000.0, 3)


def read_feedback(effect):
    return round(float(effect._delay._handed["feedback"]), 4)


def read_pan(effect):
    return float(effect._delay._handed.get("input_pan", 0.0))


def read_damping(effect):
    return round(float(effect._delay._handed["damping_hz"]), 2)


def read_wow_depth(effect):
    return round(float(effect._delay._handed["wow_depth_ms"]), 5)


#: The fine grid every walk also runs on (fix round 1): quarter steps,
#: 509 positions per macro.
FINE = tuple(i / 4.0 for i in range(509))

#: (name, fault, reading, constructor options for both builds). Every walk
#: runs at 48, 44.1 and 22.05 kHz, on the kit's grid and on `FINE`.
REACH_WALKS = (
    ("ShortHalfFrameSlapback", ShortHalfFrameSlapback, read_fraction, {}),
    ("SecondRepeatSlapback", SecondRepeatSlapback, read_delays, {}),
    ("SplitSlapback", SplitSlapback, read_delays, {}),
    ("PannedSlapback", PannedSlapback, read_pan, {}),
    ("RawTopSlapback", RawTopSlapback, read_damping, {}),
    ("RawToneSlapback", RawToneSlapback, read_damping,
     {"tone_hz": 15000.0}),
    ("NoTwoPiSlapback", NoTwoPiSlapback, read_wow_depth, {}),
)


def reach(faulted, reading, rate, ctor, grid=None):
    def build(cls):
        return cls(silence_src(512, 2, rate), sample_rate=rate, **ctor)

    with NodeSpy():
        return kit_faults.fault_reachability(SlapbackDelay, faulted, reading,
                                             build, grid=grid)


# --------------------------------------------------------------------------
# The surface


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = SlapbackDelay
        self.assertEqual(cls.MACRO_LABELS,
                         ("Time", "Level", "Saturation", "Tone", "Wow",
                          "Repeats"))
        self.assertEqual(len(cls.PATCHES), 6)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TIER, _component.AUDIODSP)
        self.assertEqual(cls.REQUIRES, ("audioecho",))
        effect = cls(silence_src(512), sample_rate=RATE)
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(0, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)

    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-09-28, so `create()` serves this one. It was the
        reverse assertion while the class was parked; revert
        `rebuilt.ADOPTED` and this goes red."""
        import audioeffects
        self.assertIn("SlapbackDelay", rebuilt.ADOPTED)
        self.assertNotIn("SlapbackDelay", rebuilt.parked())
        self.assertIs(audioeffects.SlapbackDelay, SlapbackDelay)
        served = audioeffects.create("SlapbackDelay", silence_src(64), RATE)
        self.assertIsInstance(served, SlapbackDelay)
        served.deinit()

    def test_patches_are_the_dossier_settings_on_the_grid(self):
        for index, (name, values) in enumerate(DOSSIER_PATCHES):
            label, midi = SlapbackDelay.PATCHES[index]
            self.assertEqual(label, name)
            self.assertEqual(midi, tuple(_component.macro_of(span, value)
                                         for span, value in
                                         zip(DOSSIER_SPANS, values)))

    def test_patch_0_is_the_constructor_grid(self):
        effect = SlapbackDelay(silence_src(512), sample_rate=RATE)
        grid = SlapbackDelay.PATCHES[0][1]
        for index, expected in enumerate(grid):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_time_lands_on_a_whole_frame(self):
        # 135 ms is 6 480 / 5 954 / 2 977 frames (5 953.5 at 44.1 kHz lands
        # up); the stops 1 920 / 1 764 / 882 and 12 000 / 11 025 / 5 513.
        for rate, frames in ((48000, (6480, 1920, 12000)),
                             (44100, (5954, 1764, 11025)),
                             (22050, (2977, 882, 5513))):
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            got = [effect._frames]
            for midi in (0, 127):
                effect.set_macro(TIME_I, midi)
                got.append(effect._frames)
            self.assertEqual(tuple(got), frames, rate)
            for midi in range(128):
                effect.set_macro(TIME_I, midi)
                self.assertEqual(effect._frames,
                                 law_frames(law_time_ms(midi), rate))
                self.assertEqual(effect._node_ms,
                                 effect._frames * 1000.0 / rate)

    def test_where_the_node_lands_the_handed_frame(self):
        # The node turns the handed ms back into frames in float32
        # (`audiodsp_feedback_delay.c:148`). At 48 kHz every Time position
        # lands exactly; at 44.1 and 22.05 kHz these land one float32 step
        # off, which the class cannot avoid (the node ask is drafted).
        # Goes red when the node lands every whole frame.
        off_frame = {
            48000: [],
            44100: [4, 8, 9, 10, 11, 38, 39, 40, 41, 49, 50, 53, 55, 60, 83,
                    86, 91, 93, 96, 99, 102],
            22050: [8, 10, 34, 38, 39, 40, 41, 45, 53, 60, 81, 83, 86, 91,
                    93, 96, 97, 98, 99, 102],
        }
        f32 = np.float32
        for rate, worst in ((48000, 0.0), (44100, 2.0 ** -11),
                            (22050, 2.0 ** -12)):
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            missed = []
            for midi in range(128):
                effect.set_macro(TIME_I, midi)
                ms = f32(effect._node_ms)
                frames = float((ms * f32(rate)) / f32(1000.0))
                if frames != effect._frames:
                    self.assertLessEqual(abs(frames - effect._frames), worst,
                                         (rate, midi))
                    missed.append(midi)
            self.assertEqual(missed, off_frame[rate], rate)

    def test_an_off_frame_time_leaks_into_the_next_frame(self):
        # MIDI 60 at 44.1 kHz is 4 193 frames, landed 1/2048 of a frame
        # late: a 20 000 click's repeat (Wow 0, Level 2) reads 19 618 and
        # 10 in the frame after; at 48 kHz the same position reads 19 627 alone
        # (the default Saturation's loss). At 22.05 kHz it reads 5 in the
        # frame before and 19 623. A half frame, planted, leaks.
        def window(cls, rate):
            probe = cls(silence_src(64, 2, rate), sample_rate=rate)
            probe.set_macro(TIME_I, 60)
            frames = probe._frames
            values = np.zeros(frames + 64)
            values[0] = 20000
            y = render(cls, values, rate, macros={TIME_I: 60}, level=2.0,
                       wow_cents=0.0)[:, 0]
            return [int(v) for v in y[frames - 1:frames + 2]]

        self.assertEqual(window(SlapbackDelay, 44100), [0, 19618, 10])
        self.assertEqual(window(SlapbackDelay, 22050), [5, 19623, 0])
        self.assertEqual(window(SlapbackDelay, 48000), [0, 19627, 0])
        self.assertNotEqual(window(HalfFrameSlapback, 48000),
                            [0, 19627, 0])

    def test_a_host_echoing_time_keeps_the_frame(self):
        # Fix round 1: set_macro(0, get_macro(0)) on the constructor's
        # 135.0 ms keeps 5 954 frames at 44.1 kHz; the old behaviour,
        # planted, drops to 5 953. Any other position still moves it.
        for rate, frames in ((48000, 6480), (44100, 5954), (22050, 2977)):
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            effect.set_macro(TIME_I, effect.get_macro(TIME_I))
            self.assertEqual(effect._frames, frames, rate)
            effect.set_macro(TIME_I, effect.get_macro(TIME_I))
            self.assertEqual(effect._frames, frames, rate)
        old = EchoForgetsTimeSlapback(silence_src(64, 2, 44100),
                                      sample_rate=44100)
        old.set_macro(TIME_I, old.get_macro(TIME_I))
        self.assertEqual(old._frames, 5953)
        effect = SlapbackDelay(silence_src(64, 2, 44100), sample_rate=44100)
        effect.set_macro(TIME_I, effect.get_macro(TIME_I) + 0.01)
        self.assertIsNone(effect._time_exact)
        effect = SlapbackDelay(silence_src(64, 2, 44100), sample_rate=44100)
        effect.program_change(0)
        self.assertEqual(effect._frames, law_frames(law_time_ms(84), 44100))

    def test_the_wow_map_and_its_ceiling(self):
        self.assertAlmostEqual(sd.wow_depth_ms(1.0), 0.13137, places=5)
        self.assertAlmostEqual(sd.wow_depth_ms(3.5), 0.46012, places=5)
        self.assertEqual(sd.wow_depth_ms(0.0), 0.0)
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               wow_cents=10.0)
        self.assertAlmostEqual(effect._wow_ms, law_wow_ms(3.5), places=12)
        for midi in range(128):
            effect.set_macro(WOW_I, midi)
            self.assertAlmostEqual(effect._wow_ms,
                                   law_wow_ms(3.5 * midi / 127.0), places=12)

    def test_tone_stops_and_the_22k_clamp(self):
        for rate in RATES:
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            dampings = [effect._tone_damping(m / 127.0) for m in range(128)]
            self.assertEqual(dampings[127], 0.0)
            if rate == 22050:
                self.assertLess(dampings[93], dampings[94])
                self.assertEqual(len(set(dampings[94:127])), 1)
                self.assertAlmostEqual(dampings[94], 6183.68, places=2)
            else:
                self.assertTrue(all(b > a for a, b in
                                    zip(dampings[:126], dampings[1:127])))
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               tone_hz=15000.0)
        self.assertAlmostEqual(effect._damping, 11566.93, places=2)

    def test_tail_samples_follows_time_tone_wow_and_repeats(self):
        # laps x (reach + ceil(wow) + 1 + memory); one lap at Repeats 0.
        for rate, declared in ((48000, 6488), (44100, 5961), (22050, 2981)):
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            self.assertEqual(effect.tail_samples, declared, rate)
            self.assertEqual(declared, law_frames(135.0, rate)
                             + law_wow_frames(1.0, rate) + 1)
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE)
        self.assertEqual(sd.laps_to_zero(0.35), 11)
        self.assertEqual(sd.laps_to_zero(0.6), 21)
        effect.set_macro(REPEATS_I, 127)
        self.assertEqual(effect.tail_samples, 21 * 6488)
        # A falling move walks from the old Time, so the old Time stays in
        # the bound; a reset lands the head on patch 0.
        effect.set_macro(TIME_I, 0)
        self.assertEqual(effect.tail_samples, 21 * 6488)
        effect.set_macro(TIME_I, 127)
        self.assertEqual(effect.tail_samples, 21 * (12000 + 7 + 1))
        effect.reset()
        self.assertEqual(effect.tail_samples,
                         law_frames(law_time_ms(84), RATE)
                         + law_wow_frames(3.5 * 36 / 127.0, RATE) + 1)
        # Tone in at Repeats 0.5, a stall centre: since audiodsp v0.6.3rc1
        # the node is handed 0.5 itself, and the bound takes its landing
        # lap there (111 758 frames; 105 184 with the retired stepping).
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               tone_hz=2000.0, repeats=0.5)
        self.assertEqual(effect._feedback, 0.5)
        self.assertAlmostEqual(effect.get_macro(REPEATS_I), 127 * 0.5 / 0.6)
        self.assertEqual(effect.tail_samples, 111758)

    def test_constructor_clamps_and_nan(self):
        nan = float("nan")
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               time_ms=nan, level=nan, saturation=nan,
                               tone_hz=nan, wow_cents=nan, repeats=nan)
        self.assertEqual([effect.macro(i) for i in (1, 2, 5)],
                         [0.35, 0.15, 0.0])
        self.assertEqual(effect._frames, 6480)
        self.assertEqual(effect._damping, 0.0)
        self.assertAlmostEqual(effect._wow_ms, law_wow_ms(1.0))
        for options, frames in (({"time_ms": 0.0, "tone_hz": 0.0}, 1920),
                                ({"time_ms": -5.0, "tone_hz": -1.0}, 1920),
                                ({"time_ms": 900.0, "tone_hz": 1e6}, 12000)):
            effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                                   **options)
            self.assertEqual(effect._frames, frames, options)
            self.assertEqual(effect._damping, 0.0, options)
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               tone_hz=100.0, repeats=2.0, level=5.0)
        self.assertEqual(effect.get_macro(TONE_I), 0.0)
        self.assertEqual(effect.get_macro(REPEATS_I), 127.0)
        self.assertEqual(effect.get_macro(LEVEL_I), 127.0)


# --------------------------------------------------------------------------
# Tier 2 rows


class T1OneRepeat(unittest.TestCase):
    def test_defaults_three_rates_stereo_and_mono(self):
        for rate in RATES:
            for channels in (2, 1):
                result = t1_measure(SlapbackDelay, rate, channels)
                self.assertTrue(result["passed"], (rate, channels, result))
        result = t1_measure(SlapbackDelay, RATE, 2, click_lsb=328)
        self.assertTrue(result["passed"], result)
        result = t1_measure(SlapbackDelay, RATE, patch=0)
        self.assertTrue(result["passed"], result)

    def test_no_second_repeat_at_the_stops_and_patches(self):
        for options in ({"time_ms": 40.0}, {"time_ms": 250.0},
                        {"saturation": 1.0}, {"tone_hz": 2000.0},
                        {"wow_cents": 3.5}, {"wow_cents": 0.0},
                        {"level": 2.0}, {"patch": 1}, {"patch": 2},
                        {"patch": 3}, {"patch": 5}):
            result = t1_measure(SlapbackDelay, RATE, delay_bar=False,
                                **options)
            self.assertTrue(result["passed"], (options, result))

    def test_the_control_moves(self):
        for options in ({"repeats": 0.35}, {"patch": 4}, {"repeats": 0.6}):
            result = t1_control(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))

    def test_a_short_fractional_landing_is_red(self):
        # Fix round 1: floor(0.92 T) + 0.5 frames, off the whole-frame
        # surface, red on the delay bar at every rate.
        for rate in RATES:
            result = t1_measure(ShortHalfFrameSlapback, rate)
            self.assertFalse(result["passed"], rate)
            self.assertIn("delay", " ".join(result["red"]))
            self.assertLess(result["delay_ms"], 130.0)

    def test_a_lone_second_repeat_is_red(self):
        # Fix round 1: a second node puts the first repeat again at 2T,
        # about 26 dB down, under the control's -20 dB, and nothing at 3T.
        for rate in RATES:
            energies, _ = t1_read(SecondRepeatSlapback, rate)
            self.assertEqual(energies[2], 0.0, rate)
            self.assertEqual(energies[3], 0.0, rate)
            result = t1_measure(SecondRepeatSlapback, rate)
            self.assertFalse(result["passed"], rate)
            self.assertEqual(result["red"],
                             ["a 2T-4T window is not exact zero"])
            self.assertLess(result["second_db"], -20.0)
            self.assertGreater(result["second_db"], -30.0)

    def test_the_level_span(self):
        # (m): the clauses hold down to a 3 LSB click (-80.8 dBFS).
        for rate in RATES:
            result = t1_measure(SlapbackDelay, rate, click_lsb=3)
            self.assertTrue(result["passed"], (rate, result))


class T2Comb(unittest.TestCase):
    def test_the_defaults_and_the_stops(self):
        for rate in RATES:
            result = t2_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        for options in ({"time_ms": 40.0, "wow_cents": 0.0},
                        {"time_ms": 250.0, "wow_cents": 0.0},
                        {"time_ms": 137.0, "wow_cents": 0.0}, {"patch": 0}):
            result = t2_measure(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))
        result = t2_measure(SlapbackDelay, RATE, click_lsb=3277)
        self.assertTrue(result["passed"], result)

    def test_the_second_tooth_cells(self):
        # Fix round 1: the gate audit's red cells, Wow 0, where 1/T falls
        # near half a bin of the pad and the tallest tooth is the second.
        for rate in (48000, 44100):
            for midi in (117, 120, 124):
                result = t2_measure(SlapbackDelay, rate,
                                    time_ms=law_time_ms(midi),
                                    wow_cents=0.0)
                self.assertTrue(result["passed"], (rate, midi, result))

    def test_the_old_first_guess_is_red_there(self):
        # The old guess, the autocorrelation's argmax, planted: at grid 124
        # (48 kHz, Wow 0) it takes 2/T and the low fit reads +47 %.
        rate = 48000
        T = law_frames(law_time_ms(124), rate)
        x = np.zeros(100 + T + 400)
        x[100] = 32767
        y = render(SlapbackDelay, x, rate, 2, time_ms=law_time_ms(124),
                   wow_cents=0.0)[:, 0].astype(float)
        size = int(PAD_S * rate)
        mag = np.abs(np.fft.rfft(y, n=size))
        bin_hz = rate / float(size)
        law = rate / float(T)
        old = old_comb_guess(mag, bin_hz)
        self.assertAlmostEqual(old / law, 2.0, delta=0.01)
        low, _ = notch_spacing(mag, bin_hz, 200.0, 2000.0, old)
        self.assertGreater(abs(low / law - 1.0), 0.005)
        new = comb_guess(mag, bin_hz)
        self.assertAlmostEqual(new / law, 1.0, delta=0.01)

    def test_a_short_fractional_landing_is_red(self):
        for rate in RATES:
            result = t2_measure(ShortHalfFrameSlapback, rate)
            self.assertFalse(result["passed"], rate)
            self.assertGreater(result["deviations"][0], 8.0)

    def test_frames_at_44k_are_red_at_22k(self):
        result = t2_measure(Frames441Slapback, 22050)
        self.assertFalse(result["passed"], result)

    def test_the_split_build_is_red_on_agreement_alone(self):
        # Station A's split, on the class: each fit inside 0.5 %, the two
        # fits more than 0.5 % apart.
        for rate in RATES:
            low, high, between = t2_measure(SplitSlapback,
                                            rate)["deviations"]
            self.assertLessEqual(abs(low), 0.5, rate)
            self.assertLessEqual(abs(high), 0.5, rate)
            self.assertGreater(abs(between), 0.5, rate)


class T3Mono(unittest.TestCase):
    def test_the_defaults_the_corner_and_the_patches(self):
        for rate in RATES:
            result = t3_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        for options in ({"repeats": 0.6, "saturation": 1.0,
                         "tone_hz": 2000.0, "wow_cents": 3.5},
                        {"patch": 2}, {"patch": 4}, {"patch": 5},
                        {"time_ms": 40.0}, {"time_ms": 250.0}):
            result = t3_measure(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))

    def test_a_panned_repeat_is_red(self):
        result = t3_measure(PannedSlapback, RATE)
        self.assertFalse(result["passed"])
        self.assertGreater(result["lr"], 0)

    def test_presence_on_tones_reads_the_measured_table(self):
        # Re-audit fix round 1: the dossier reports this table instead of
        # a band. Each cell must read within PRESENCE_PIN_DB of its entry.
        for label, options, dbfs, fraction, table in PRESENCE_TABLE:
            for rate, want in zip(RATES, table):
                head, energy = presence_db(
                    SlapbackDelay, tone(fraction * rate, rate,
                                        amp=dbfs_amp(dbfs)),
                    rate, **options)
                cell = (label, dbfs, fraction, rate, round(energy, 3))
                self.assertEqual(head, 0, cell)
                self.assertLessEqual(abs(energy - want), PRESENCE_PIN_DB,
                                     cell)

    def test_a_full_scale_tone_at_saturation_1_reads_past_4_db(self):
        # Round 3 disconfirmed "with Tone out and Repeats 0, the 4 dB bar
        # holds on material below a third of the running rate" here: Tone
        # out, Repeats 0, Saturation 1, a 0 dBFS tone at fs/3, at every
        # rate. If this comes back inside 4 dB, a band sentence could be
        # written again, and it would have to be measured first.
        for rate in RATES:
            head, energy = presence_db(
                SlapbackDelay, tone(rate / 3.0, rate, amp=dbfs_amp(0.0)),
                rate, saturation=1.0)
            self.assertEqual(head, 0, rate)
            self.assertLess(energy, -4.0, (rate, energy))

    def test_tone_in_and_repeats_take_a_tone_past_4_db(self):
        # Fix round 2: Tone at its 2 kHz stop takes a 3 kHz tone more than
        # 4 dB down, and Repeats at its 0.6 stop stacks a 1 kHz tone more
        # than 4 dB up, at every rate (-20 dBFS). The low-pass and the
        # repeats doing their jobs, not a defect.
        for rate in RATES:
            head, energy = presence_db(SlapbackDelay, tone(3000.0, rate),
                                       rate, tone_hz=2000.0)
            self.assertEqual(head, 0, rate)
            self.assertLess(energy, -4.0, (rate, energy))
            head, energy = presence_db(SlapbackDelay, tone(1000.0, rate),
                                       rate, repeats=0.6)
            self.assertEqual(head, 0, rate)
            self.assertGreater(energy, 4.0, (rate, energy))

    def test_presence_at_nyquist_is_the_disclosed_wow_loss(self):
        # At Nyquist the defaults read outside 4 dB, and at Wow 0 inside
        # 0.5 dB: the loss is the wow's fractional read, not the class
        # dropping the repeat. If this moves, the dossier's words move too.
        for rate in RATES:
            alt = probes.alt_fs(frames=rate, channels=1)
            _, energy = presence_db(SlapbackDelay, alt, rate)
            self.assertLess(energy, -4.0, rate)
            _, still = presence_db(SlapbackDelay, alt, rate, wow_cents=0.0)
            self.assertLess(abs(still), 0.5, rate)


class T4Tone(unittest.TestCase):
    def test_out_and_the_corners_at_48k_and_44k(self):
        for rate in (48000, 44100):
            result = t4_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))

    def test_the_grid_cells(self):
        for rate in (48000, 44100):
            for midi in (51, 111, 126):
                label = 2000.0 * 10.0 ** (midi / 127.0)
                result = t4_corner(SlapbackDelay, label, label, rate)
                self.assertTrue(result["passed"], (rate, midi, result))

    def test_the_22k_cells(self):
        self.assertEqual(t4_out_differing(SlapbackDelay, 22050), 0)
        for label in (2000.0, 2000.0 * 10.0 ** (51 / 127.0)):
            result = t4_corner(SlapbackDelay, label, label, 22050)
            self.assertTrue(result["passed"], (label, result))

    def test_an_open_top_stop_is_red_at_the_defaults(self):
        for rate in RATES:
            self.assertGreater(t4_out_differing(RawTopSlapback, rate), 0)
            self.assertGreater(t4_out_differing(OpenTopSlapback, rate), 0)
        for rate in (48000, 44100):
            self.assertFalse(t4_measure(RawTopSlapback, rate)["passed"])
            self.assertFalse(t4_measure(OpenTopSlapback, rate)["passed"])

    def test_out_after_tone_has_been_in_is_the_filter_out(self):
        # Since audiodsp v0.6.3rc1 the node keeps an out low-pass on the
        # tap (#158), so the out stop hands exactly 0 whatever came before
        # (the constructor and a patch count as Tone in) and the output is
        # byte-identical to the node given no `damping_hz`: with Wow on,
        # and at Wow 0 on a Time whose float32 landing leaves a fraction
        # (44.1 kHz grid 8, 1 980 frames asked) as on one it lands whole
        # (grid 84). The tracking cure this replaced moved samples by 1 LSB
        # on those cells; planted, it is red on every one.
        for rate in RATES:
            for channels in (2, 1):
                for ctor in ({"tone_hz": 5000.0}, {"patch": 5}):
                    differing, peak, damping = t4_out_history(
                        SlapbackDelay, rate, channels, steps=(0,), **ctor)
                    self.assertEqual((differing, peak, damping),
                                     (0, 0, 0.0), (rate, channels, ctor))
                    differing, _peak, damping = t4_out_history(
                        TrackingSlapback, rate, channels, steps=(0,),
                        **ctor)
                    self.assertEqual(damping, 32.0 * rate)
                    self.assertGreater(differing, 0, (rate, channels, ctor))
        for channels in (2, 1):
            for midi in (8, 84):
                steps = (0, (WOW_I, 0), (TIME_I, midi))
                differing, peak, _ = t4_out_history(
                    SlapbackDelay, 44100, channels, steps=steps,
                    tone_hz=5000.0)
                self.assertEqual((differing, peak), (0, 0), (channels, midi))
            differing, _peak, _ = t4_out_history(
                TrackingSlapback, 44100, channels,
                steps=(0, (WOW_I, 0), (TIME_I, 8)), tone_hz=5000.0)
            self.assertGreater(differing, 0, channels)

    def test_out_on_a_fresh_history_is_byte_identical(self):
        for rate in RATES:
            for channels in (2, 1):
                self.assertEqual(t4_out_differing(SlapbackDelay, rate,
                                                  channels), 0)
                differing, _, damping = t4_out_history(
                    SlapbackDelay, rate, channels, steps=(0,))
                self.assertEqual((differing, damping), (0, 0.0))
                # A Tone-in constructor with a patch 0 on top never put
                # Tone in on the node after the constructor finished, but
                # the constructor counts: this one is the 1 LSB case.
                differing, peak, damping = t4_out_history(
                    SlapbackDelay, rate, channels, tone_hz=5000.0, patch=0)
                self.assertLessEqual(peak, 1)

    def test_the_bound_goes_red(self):
        # The restated clause's own planted faults: an open top after
        # Tone has been in is far outside 1 LSB.
        for rate in RATES:
            for cls in (RawTopSlapback, OpenTopSlapback):
                _, peak, _ = t4_out_history(cls, rate, 2, steps=(0,),
                                            patch=5)
                self.assertGreater(peak, 1, (rate, cls.__name__))

    def test_a_raw_tone_is_red_at_the_15k_cell(self):
        for rate in (48000, 44100):
            result = t4_corner(RawToneSlapback, 15000.0, 15000.0, rate,
                               passband=True)
            self.assertFalse(result["passed"])
            self.assertIsNone(result["corner"])

    def test_a_raw_tone_is_red_at_patch_5_at_22k(self):
        label = 2000.0 * 10.0 ** (51 / 127.0)
        result = t4_corner(RawToneSlapback, label, label, 22050)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["corner"] / label - 1.0, 0.2)


class T5Wow(unittest.TestCase):
    def test_zero_default_and_top(self):
        for rate in RATES:
            result = t5_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        for saturation in (0.0, 0.15):
            self.assertLess(abs(t5_cents(SlapbackDelay, RATE, amp=328,
                                         saturation=saturation) - 1.0), 0.25)
        cents = t5_cents(SlapbackDelay, RATE, patch=0)
        self.assertLess(abs(cents - 1.0), 0.25)

    def test_the_level_span(self):
        # (m): the clauses hold on a 10 LSB sine (-70.3 dBFS).
        for rate in RATES:
            zero = t5_cents(SlapbackDelay, rate, amp=10, wow_cents=0.0)
            default = t5_cents(SlapbackDelay, rate, amp=10)
            top = t5_cents(SlapbackDelay, rate, amp=10, wow_cents=3.5)
            self.assertLess(zero, 0.05, rate)
            self.assertLess(abs(default - 1.0), 0.25, rate)
            self.assertLess(abs(top - 3.5), 0.5, rate)

    def test_the_ceiling(self):
        cents = t5_cents(SlapbackDelay, RATE, wow_cents=10.0)
        self.assertLess(cents, 4.0)
        self.assertLess(abs(cents - 3.5), 0.5)

    def test_a_map_without_its_two_pi_is_red(self):
        result = t5_measure(NoTwoPiSlapback, RATE)
        self.assertFalse(result["passed"])
        self.assertGreater(result["default"], 5.0)


# --------------------------------------------------------------------------
# Tier 1, the fast half


class Tier1Fast(unittest.TestCase):
    def test_level_zero_is_a_wire_on_the_full_scale_ramp(self):
        corner = {"repeats": 0.6, "saturation": 1.0, "tone_hz": 2000.0,
                  "wow_cents": 3.5, "level": 0.0}
        for rate in RATES:
            for channels in (2, 1):
                for time_ms in (40.0, 250.0):
                    frames = law_frames(time_ms, rate) * 3
                    ramp = probes.ramp_fs(frames=frames, channels=channels)
                    effect = SlapbackDelay(
                        probes.ArraySource(ramp, rate=rate,
                                           channels=channels, block=BLOCK),
                        sample_rate=rate, time_ms=time_ms, **corner)
                    out = pull(effect, frames, channels).reshape(-1)
                    self.assertTrue(np.array_equal(
                        out, np.array(ramp, dtype=np.int16)),
                        (rate, channels, time_ms))

    def test_the_dry_is_unity_until_the_repeat(self):
        # Level 1.0 and grid 63 (0.992): the first T - 24 frames are the
        # source, byte for byte, with the wow at its top.
        for level in (0.0, 0.35, 0.7, 1.0, 2.0 * 63 / 127.0):
            T = law_frames(40.0, RATE)
            ramp = probes.ramp_fs(frames=T * 2, channels=2)
            effect = SlapbackDelay(
                probes.ArraySource(ramp, rate=RATE, channels=2, block=BLOCK),
                sample_rate=RATE, time_ms=40.0, level=level, wow_cents=3.5,
                repeats=0.6, saturation=1.0)
            out = pull(effect, T * 2, 2).reshape(-1)
            window = (T - 24) * 2
            self.assertTrue(np.array_equal(
                out[:window], np.array(ramp, dtype=np.int16)[:window]))

    def test_silence_stays_silence(self):
        effect = SlapbackDelay(silence_src(RATE), sample_rate=RATE,
                               repeats=0.6, level=2.0, tone_hz=2000.0,
                               saturation=1.0, wow_cents=3.5)
        self.assertEqual(int(np.abs(pull(effect, RATE)).max()), 0)

    def test_the_tail_reaches_exact_zero_inside_tail_samples(self):
        for rate in RATES:
            for level in (0.35, 2.0):
                result = tail_measure(SlapbackDelay, rate, level=level)
                self.assertTrue(result["passed"], (rate, level, result))
        for options in ({"repeats": 0.35, "level": 2.0},
                        {"repeats": 0.6, "level": 2.0},
                        {"repeats": 0.6, "level": 2.0, "saturation": 1.0,
                         "tone_hz": 2000.0, "wow_cents": 3.5},
                        {"time_ms": 250.0, "wow_cents": 3.5,
                         "repeats": 0.6, "level": 2.0}):
            result = tail_measure(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))

    def test_a_tail_without_the_wow_is_red(self):
        result = tail_measure(NoWowTailSlapback, RATE, level=2.0)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["last"], result["declared"])

    def _stall(self, cls):
        """Repeats 0.5, Tone 2 kHz, Level 2, Saturation 0: a 2 LSB DC for
        1 s, then 3 s of silence."""
        values = np.zeros(4 * RATE)
        values[:RATE] = 2.0
        source, _ = to_source(values)
        effect = cls(source, sample_rate=RATE, repeats=0.5, tone_hz=2000.0,
                     level=2.0, saturation=0.0)
        declared = effect.tail_samples
        y = pull(effect, len(values))[:, 0]
        nonzero = np.nonzero(y[RATE:])[0]
        last = int(nonzero[-1]) + 1 if len(nonzero) else 0
        return declared, last, int(np.abs(y[-RATE // 4:]).max())

    def test_the_stall_cell_reaches_zero_at_the_repeats_set(self):
        # Repeats 0.5 with Tone in is a stall centre: up to audiodsp v0.6.2
        # the node held 1 LSB there for ever and the class moved Repeats
        # clear of it. Since v0.6.3rc1 (#157) the node lands the stalled
        # state, so 0.5 is handed as set and the tail ends inside the bound.
        declared, last, held = self._stall(SlapbackDelay)
        self.assertEqual(held, 0)
        self.assertGreater(last, 0)
        self.assertLessEqual(last, declared)
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               repeats=0.5, tone_hz=2000.0)
        self.assertEqual(effect._feedback, 0.5)
        # Planted: the retired stepping hands a Repeats nobody set.
        stepped = SteppedSlapback(silence_src(64), sample_rate=RATE,
                                  repeats=0.5, tone_hz=2000.0)
        self.assertNotEqual(stepped._feedback, 0.5)
        self.assertLess(abs(stepped._feedback - 0.5), 2.5e-5)

    def _tone_back_in(self, cls, rate=RATE, channels=2, level=2.0):
        """300 Hz at 30 000 LSB for 0.5 s with Tone 2 kHz, Tone out, 2 s of
        silence, then Tone to MIDI 0: the output's peak after that move."""
        loud = (rate // 2) // BLOCK * BLOCK
        back = (loud + 2 * rate) // BLOCK * BLOCK
        values = np.zeros(back + rate // 4)
        values[:loud] = 30000 * np.sin(2 * math.pi * 300.0
                                       * np.arange(loud) / rate)
        source, _ = to_source(values, channels, rate)
        effect = cls(source, sample_rate=rate, tone_hz=2000.0, level=level)

        def move(frame):
            if frame == loud:
                effect.set_macro(TONE_I, 127)
            elif frame == back:
                effect.set_macro(TONE_I, 0)

        y = pull(effect, len(values), channels, on_block=move)
        return int(np.abs(y[back:]).max())

    def test_tone_back_in_after_silence_stays_silent(self):
        for rate in RATES:
            for channels in (2, 1):
                self.assertEqual(self._tone_back_in(SlapbackDelay, rate,
                                                    channels), 0,
                                 (rate, channels))
        self.assertEqual(self._tone_back_in(SlapbackDelay, level=0.35), 0)
        # Planted: a low-pass left in with a frozen state (0.001 Hz) plays
        # what it held back out of silence.
        self.assertGreater(self._tone_back_in(FrozenToneSlapback), 20000)
        self.assertGreater(self._tone_back_in(FrozenToneSlapback,
                                              level=0.35), 5000)

    def test_tone_out_hands_exactly_zero(self):
        # After Tone has been in, after a patch with Tone in, and fresh.
        # The retired tracking cure, planted, hands 32 x the rate.
        with NodeSpy():
            for rate in RATES:
                for cls, expected in ((SlapbackDelay, 0.0),
                                      (TrackingSlapback, 32.0 * rate)):
                    effect = cls(silence_src(64, 2, rate), sample_rate=rate)
                    self.assertEqual(effect._delay._handed["damping_hz"],
                                     0.0)
                    effect.set_macro(TONE_I, 0)
                    effect.set_macro(TONE_I, 127)
                    self.assertEqual(effect._delay._handed["damping_hz"],
                                     expected, (cls, rate))
                    effect = cls(silence_src(64, 2, rate), sample_rate=rate,
                                 patch=5)
                    effect.program_change(0)
                    self.assertEqual(effect._delay._handed["damping_hz"],
                                     expected, (cls, rate))

    def _wow_move(self, cls, start, target):
        """(the tone's own largest step before the move, the largest step
        over the 2 000 frames from the move) for a Wow move at frame
        15 616 on 997 Hz at 12 000 LSB, Level 2, 48 kHz."""
        at = 15616
        values = 12000 * np.sin(2 * math.pi * 997.0 * np.arange(RATE) / RATE)
        source, _ = to_source(values)
        effect = cls(source, sample_rate=RATE, level=2.0)
        effect.set_macro(WOW_I, start)

        def move(frame):
            if frame == at:
                effect.set_macro(WOW_I, target)

        y = pull(effect, RATE, on_block=move)[:, 0].astype(int)
        steady = int(np.abs(np.diff(y[at - 3000:at - 1])).max())
        return steady, int(np.abs(np.diff(y[at - 1:at + 2000])).max())

    def test_a_wow_move_does_not_step(self):
        # Since audiodsp v0.6.3rc1 the node ramps a new depth in over 20 ms
        # (#160): no step larger than the tone's own (1 565 LSB) after a
        # move 36 -> 73 or 0 -> 127, where v0.6.2 stepped 7 684 and 23 037.
        for start, target in ((36, 73), (0, 127)):
            steady, worst = self._wow_move(SlapbackDelay, start, target)
            self.assertLessEqual(worst, steady, (start, target))
            # Planted: the read head moved by the whole change at once.
            steady, worst = self._wow_move(JumpWowSlapback, start, target)
            self.assertGreater(worst, 4 * steady, (start, target))

    def _walk_tail(self, cls):
        """250 ms of 997 Hz, then Time 250 -> 40 ms on the tone's last
        block, Repeats 0, Level 2."""
        tone = int(0.25 * RATE) // BLOCK * BLOCK
        values = np.zeros(tone + RATE)
        values[:tone] = 12000 * np.sin(2 * math.pi * 997.0
                                       * np.arange(tone) / RATE)
        source, _ = to_source(values)
        effect = cls(source, sample_rate=RATE, time_ms=250.0, level=2.0)
        seen = {}

        def move(frame):
            if frame == tone:
                effect.set_macro(TIME_I, 0)
                seen["declared"] = effect.tail_samples

        y = pull(effect, len(values), on_block=move)[:, 0]
        last = int(np.nonzero(y[tone:])[0][-1]) + 1
        return seen["declared"], last

    def test_a_falling_walk_keeps_the_old_time_in_the_tail(self):
        declared, last = self._walk_tail(SlapbackDelay)
        self.assertGreater(last, 4000)
        self.assertLessEqual(last, declared)
        declared, last = self._walk_tail(TargetOnlyTailSlapback)
        self.assertGreater(last, declared)

    def test_reset_empties_the_line(self):
        values = np.zeros(RATE)
        values[256:2304] = 12000 * np.sin(2 * math.pi * 997.0
                                          * np.arange(2048) / RATE)
        source, _ = to_source(values)
        effect = SlapbackDelay(source, sample_rate=RATE, repeats=0.6,
                               level=2.0)
        pull(effect, 2304)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(int(np.abs(pull(effect, RATE // 2)).max()), 0)

    def test_deinit_leaves_the_source(self):
        source, _ = to_source(8000 * np.sin(2 * math.pi * 440.0
                                            * np.arange(1024) / RATE))
        effect = SlapbackDelay(source, sample_rate=RATE)
        pull(effect, 256)
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(source)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)

    def test_click_delay_is_zero(self):
        for rate in (48000, 44100):
            values = np.zeros(2048)
            values[10] = 30000
            y = render(SlapbackDelay, values, rate)[:, 0]
            self.assertEqual(int(np.argmax(np.abs(y))), 10)
            self.assertEqual(int(y[10]), 30000)

    def test_the_transport_is_never_read(self):
        reads = []

        def transport():
            reads.append(1)
            return (True, 0.0, 120.0, 4, 4)
        effect = SlapbackDelay.create(silence_src(512), RATE,
                                      transport=transport)
        for index in range(6):
            effect.set_macro(index, 127)
        effect.program_change(4)
        effect.reset()
        pull(effect, 256)
        self.assertEqual(reads, [])


class InputCeiling(unittest.TestCase):
    """The docstring's ceiling on `noise_det`, 48 kHz stereo, 4 s: the
    defaults clean at -2.5 dBFS peak and not at -2.4, patch 2 (Doubling,
    the first shipped patch to rail) clean at -3.4 and not at -3.3."""

    def test_the_stated_ceiling_is_clean_and_just_over_is_not(self):
        for options, ceiling, over in (({}, -2.5, -2.4),
                                       ({"patch": 2}, -3.4, -3.3)):
            self.assertEqual(railed_samples(SlapbackDelay, ceiling,
                                            **options), 0, options)
            self.assertGreater(railed_samples(SlapbackDelay, over,
                                              **options), 0, options)


# --------------------------------------------------------------------------
# The docstring's claims, each tied to the test that asserts it (the trial
# of the second process, 2026-09-29)

#: (sentence, word for word as the class docstring has it, and the test
#: that asserts it). Every sentence in the docstring that makes a claim is
#: here; one that could not be tied to a test was struck.
CLAIMS = (
    ("By default the repeat comes 135 ms after the dry, once.",
     "test_defaults_three_rates_stereo_and_mono"),
    ("Time runs from 40 to 250 ms, Level from 0 to 2, Saturation from 0 to "
     "1, Tone from 2 kHz to out at its top stop, Wow from 0 to 3.5 cents "
     "and Repeats from 0 to 0.6.", "test_the_knob_spans"),
    ("Level 0 is a wire.", "test_level_zero_is_a_wire_on_the_full_scale_ramp"),
    ("Up to Level 1 the dry passes untouched until the repeat arrives, "
     "however hard Saturation drives the repeat.",
     "test_the_dry_is_unity_until_the_repeat"),
    ("A hot input can reach the rail, since the repeat adds to a dry at "
     "unity.", "test_the_stated_ceiling_is_clean_and_just_over_is_not"),
    ("At Repeats 0 there is one repeat and no second.",
     "test_no_second_repeat_at_the_stops_and_patches"),
    ("Repeats above 0 sends the repeat round for more.",
     "test_the_control_moves"),
    ("Wow swings the repeat's pitch by the cents the knob reads, at a slow "
     "fixed rate.", "test_zero_default_and_top"),
    ("The default Wow takes the repeat's very top more than 4 dB down at "
     "Nyquist, where Wow 0 leaves it within half a dB.",
     "test_presence_at_nyquist_is_the_disclosed_wow_loss"),
    ("At 22.05 kHz the last Tone positions below the top stop clamp below "
     "Nyquist and all do the same thing.",
     "test_tone_stops_and_the_22k_clamp"),
    ("Every Time position lands on the nearest whole frame at 48 kHz.",
     "test_where_the_node_lands_the_handed_frame"),
    ("At 44.1 and 22.05 kHz the node lands some positions a fraction of a "
     "frame off, and a sliver of the repeat falls on the frame beside it.",
     "test_an_off_frame_time_leaks_into_the_next_frame"),
    ("A host that writes back `get_macro(0)` keeps the constructor's exact "
     "Time.", "test_a_host_echoing_time_keeps_the_frame"),
    ("Turning Time walks the repeat to the new Time, bending its pitch, "
     "instead of clicking.", "test_a_time_move_walks"),
    ("A Wow move glides instead of stepping.", "test_a_wow_move_does_not_step"),
    ("A source the same in both channels comes out the same in both "
     "channels, and a one-channel source gets the stereo render's left "
     "channel.", "test_the_defaults_the_corner_and_the_patches"),
    ("A click comes out on the frame it went in: there is no latency.",
     "test_click_delay_is_zero"),
    ("`tail_samples` is an upper bound on how many frames the output takes "
     "to reach exact zero, counted from when your input stops or from when "
     "you read it if that is later, for the settings as they stand when you "
     "read it.", "test_tail_samples_holds_for_the_settings_as_they_stand"),
    ("`reset()` empties the line and returns to patch 0.",
     "test_reset_empties_the_line"),
    ("The class never reads the host's tempo.",
     "test_the_transport_is_never_read"),
    ("A constructor value outside a knob's span clamps to the nearer stop, a "
     "`tone_hz` of 0 or less is Tone out, and NaN takes the option's "
     "default.", "test_constructor_clamps_and_nan"),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "test_a_jumping_control_steps_the_output"),
    ("The tail rings only while the source keeps feeding: feed silence to "
     "let it ring out.", "test_a_tail_cut_short_carries_on"),
    ("A tail cut short by a source that stopped carries on when the source "
     "comes back.", "test_a_tail_cut_short_carries_on"),
)


def _flat(text):
    return " ".join(text.split())


def _cell(event, patch, channels=1, rate=RATE, cls=None):
    """One lifecycle matrix cell on the class, as measured, with the class's
    DECLARED rows lifted so the raw verdict shows."""
    import lifecycle
    cls = cls or SlapbackDelay
    ev = [e for e in lifecycle.events(cls, patch) if e.name == event][0]
    saved = dict(lifecycle.DECLARED)
    for key in list(lifecycle.DECLARED):
        if key[0] == "SlapbackDelay":
            del lifecycle.DECLARED[key]
    controls = {}
    try:
        return lifecycle.run_cell(cls, ev, rate, channels, patch, {},
                                  controls)
    finally:
        lifecycle.DECLARED.clear()
        lifecycle.DECLARED.update(saved)
        for ctl in controls.values():
            ctl.close()


class NoWowSlapback(SlapbackDelay):
    """The class with Wow at 0 in the constructor and every patch: the
    control for the reset cells' declared P4 rows."""

    NAME = 'SlapbackDelay'
    PATCHES = dict((index, (name, values[:WOW_I] + (0,)
                            + values[WOW_I + 1:]))
                   for index, (name, values) in SlapbackDelay.PATCHES.items())

    def _build(self, *args, **options):
        options.setdefault("wow_cents", 0.0)
        SlapbackDelay._build(self, *args, **options)


def _time_move(cls, target=52):
    """(the tone's own largest step before the move, the largest step over
    the 2 000 frames from it, zero crossings in 1 024 frames before and
    after) for Time 135 ms -> `target` at frame 15 616 on 997 Hz at 12 000
    LSB, Level 2 (the repeat alone), Wow 0, 48 kHz."""
    at = 15616
    values = 12000 * np.sin(2 * math.pi * 997.0 * np.arange(RATE) / RATE)
    source, _ = to_source(values)
    effect = cls(source, sample_rate=RATE, level=2.0, wow_cents=0.0)

    def move(frame):
        if frame == at:
            effect.set_macro(TIME_I, target)

    y = pull(effect, RATE, on_block=move)[:, 0].astype(int)
    steady = int(np.abs(np.diff(y[at - 3000:at - 1])).max())
    worst = int(np.abs(np.diff(y[at - 1:at + 2000])).max())

    def crossings(seg):
        return int(np.count_nonzero(np.diff(np.sign(seg)) != 0))
    return (steady, worst, crossings(y[at - 1024:at]),
            crossings(y[at + 256:at + 1280]))


def _midtail(ctor, moves, at=2048, rate=RATE):
    """A full-scale DC burst of 50 ms at Level 2, then silence; `moves` made
    `at` frames into the silence. (`tail_samples` read as the input stops,
    `tail_samples` read just after the moves, frames from the moves to the
    output's last non-zero frame)."""
    burst = int(0.05 * rate) // BLOCK * BLOCK
    move = burst + at
    frames = move + 30 * rate
    values = np.zeros(frames)
    values[:burst] = 32767
    source, _ = to_source(values, 2, rate)
    effect = SlapbackDelay(source, sample_rate=rate, level=2.0, **ctor)
    seen = {}

    def on_block(frame):
        if frame == burst:
            seen["before"] = effect.tail_samples
        if frame == move:
            for index, value in moves:
                effect.set_macro(index, value)
            seen["after"] = effect.tail_samples

    y = pull(effect, frames, on_block=on_block)[:, 0]
    nonzero = np.nonzero(y[move:])[0]
    last = int(nonzero[-1]) + 1 if len(nonzero) else 0
    return seen["before"], seen["after"], last


class TheClaims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        doc = _flat(SlapbackDelay.__doc__)
        tests = set()
        for value in globals().values():
            if isinstance(value, type) and issubclass(value,
                                                      unittest.TestCase):
                tests.update(n for n in dir(value) if n.startswith("test_"))
        rest = doc
        for sentence, test in CLAIMS:
            self.assertIn(sentence, doc, sentence)
            self.assertIn(test, tests, sentence)
            rest = rest.replace(sentence, " ")
        self.assertIn("**Limits shared by the family.**", doc)
        numbers = [w for w in rest.split() if any(c.isdigit() for c in w)]
        self.assertEqual(numbers, [])

    def test_the_knob_spans(self):
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE)
        for index, low, high in ((TIME_I, 40.0, 250.0), (LEVEL_I, 0.0, 2.0),
                                 (SATURATION_I, 0.0, 1.0),
                                 (WOW_I, 0.0, 3.5), (REPEATS_I, 0.0, 0.6)):
            effect.set_macro(index, 0)
            self.assertAlmostEqual(effect._value(index), low, places=9)
            effect.set_macro(index, 127)
            self.assertAlmostEqual(effect._value(index), high, places=9)
        effect.set_macro(TONE_I, 0)
        self.assertAlmostEqual(effect._value(TONE_I), 2000.0, places=6)
        self.assertEqual(effect._damping,
                         nominal_damping_hz(2000.0, RATE))
        effect.set_macro(TONE_I, 127)
        self.assertEqual(effect._damping, 0.0)

    def test_a_time_move_walks(self):
        # 135 -> 85 ms (grid 52) on the repeat alone: the pitch bends up
        # (more crossings after the move), and no step is larger than the
        # bent tone's own (+297.5 cents, x 1.19). Planted: the walk turned
        # off, so the head jumps 50 ms and the output clicks.
        steady, worst, before, after = _time_move(SlapbackDelay)
        self.assertLessEqual(worst, 1.25 * steady)
        self.assertGreater(after, before)
        steady, worst, _, _ = _time_move(JumpTimeSlapback)
        self.assertGreater(worst, 2 * steady)

    def test_tail_samples_holds_for_the_settings_as_they_stand(self):
        # Re-audit 1 found the tail sentence named no clock. Each row moves
        # a setting 2 048 frames into the silence (1 024 on a 40 ms Time,
        # whose repeat is over by then) and reads `tail_samples` after it:
        # the output is exact zero within that many frames of the move.
        rows = (({}, [(REPEATS_I, 127)], 2048),
                ({"repeats": 0.6}, [(REPEATS_I, 0)], 2048),
                ({"time_ms": 250.0}, [(TIME_I, 0)], 2048),
                ({"time_ms": 40.0}, [(TIME_I, 127)], 1024),
                ({"wow_cents": 0.0}, [(WOW_I, 127)], 2048),
                ({"wow_cents": 3.5, "repeats": 0.6}, [(WOW_I, 0)], 2048),
                ({"time_ms": 40.0, "wow_cents": 3.5}, [(WOW_I, 0)], 1024),
                ({"repeats": 0.5}, [(TONE_I, 0)], 2048),
                ({"tone_hz": 2000.0, "repeats": 0.6}, [(TONE_I, 127)], 2048))
        for ctor, moves, at in rows:
            before, after, last = _midtail(ctor, moves, at)
            self.assertGreater(last, 0, (ctor, moves))
            self.assertLessEqual(last, after, (ctor, moves, before, after))
        # The value read before a Repeats move up does not hold after it.
        before, after, last = _midtail({}, [(REPEATS_I, 127)])
        self.assertGreater(last, before)

    def test_the_reset_cells_differ_from_an_unreset_control_with_wow(self):
        # The matrix's E1 and E2 cells go red on P4 at every patch, each
        # with Wow above 0; with Wow 0 in the constructor and every patch
        # the same cells are ok. A reset restarts the wobble where a fresh
        # instance's starts (test_a_reset_restarts_the_wobble), and the
        # matrix's control never stopped, so its wobble is further along.
        # The class declares the cells.
        for event in ("E1-reset@block", "E1-reset@part", "E2-reset_buffer"):
            for patch in (None, 2):
                res = _cell(event, patch)
                self.assertTrue(res["P4"].startswith("RED"), (event, res))
                res = _cell(event, patch, cls=NoWowSlapback)
                self.assertEqual(res["P4"], "ok", (event, res))

    def test_a_reset_restarts_the_wobble(self):
        # Backs the DECLARED reason for E1/E2 P4: after reset() or the
        # host's reset_buffer, patch 0 with Wow at its top, the output is
        # sample for sample a fresh instance's fed the same material from
        # that frame, while an instance that ran on without the reset
        # differs in nearly every sample.
        at = 40 * BLOCK
        for rate in (48000, 22050):
            for channels in (2, 1):
                noise = np.random.default_rng(7).uniform(
                    -12000, 12000, at + rate // 2)
                for how in ("reset", "reset_buffer"):
                    source, _ = to_source(noise, channels, rate)
                    a = SlapbackDelay(source, sample_rate=rate, patch=0)
                    a.set_macro(WOW_I, 127)
                    pull(a, at)
                    if how == "reset":
                        a.reset()
                    else:
                        audiocore.reset_buffer(a.output)
                    a.set_macro(WOW_I, 127)
                    got = pull(a, rate // 2)
                    source, _ = to_source(noise[at:], channels, rate)
                    b = SlapbackDelay(source, sample_rate=rate, patch=0)
                    b.set_macro(WOW_I, 127)
                    want = pull(b, rate // 2)
                    key = (rate, channels, how)
                    self.assertEqual(int(np.count_nonzero(got != want)), 0,
                                     key)
                source, _ = to_source(noise, channels, rate)
                c = SlapbackDelay(source, sample_rate=rate, patch=0)
                c.set_macro(WOW_I, 127)
                ran_on = pull(c, at + rate // 2)[at:]
                differ = int(np.count_nonzero(ran_on[-1000:]
                                              != want[-1000:]))
                self.assertGreater(differ, 0.99 * 1000 * channels,
                                   (rate, channels))

    def test_a_jumping_control_steps_the_output(self):
        # The matrix's E5 cell at patch 2 (Level to 0 and back) steps past
        # its bar; the class declares it (audiocomponents#117).
        res = _cell("E5-mix0", 2)
        self.assertTrue(res["P5"].startswith("RED"), res)
        self.assertEqual(res["P1"], "ok", res)

    def test_a_tail_cut_short_carries_on(self):
        # The matrix's E8-dry cell at patch 2: the source hands back an
        # empty buffer once, and when it comes back the tail it cut short
        # plays out of the silence (audiodsp#180).
        res = _cell("E8-dry", 2)
        self.assertTrue(res["P3"].startswith("RED(peak"), res)
        self.assertEqual(res["P2"], "ok", res)


# --------------------------------------------------------------------------
# The two checks every planted fault and every row is held to


class FaultsAreUnreachable(unittest.TestCase):
    """Every fault's reachability walk, reading only what the node is
    handed, at 48, 44.1 and 22.05 kHz, on the kit's grid (17 positions per
    macro) and on the fine grid (509), plus the six patches."""

    CHECKED = 6 * 17 + 6
    CHECKED_FINE = 6 * len(FINE) + 6

    def test_every_fault_is_off_the_surface(self):
        for name, faulted, reading, ctor in REACH_WALKS:
            for rate in RATES:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, ctor)
                    self.assertEqual(result["checked"], self.CHECKED)

    def test_every_fault_is_off_the_fine_grid(self):
        for name, faulted, reading, ctor in REACH_WALKS:
            for rate in RATES:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, ctor, grid=FINE)
                    self.assertEqual(result["checked"], self.CHECKED_FINE)

    def test_frames_at_44k_are_off_the_surface_at_22k_only(self):
        reach(Frames441Slapback, read_frames, 22050, {})
        reach(Frames441Slapback, read_frames, 22050, {}, grid=FINE)
        # At 44.1 kHz the 44.1 kHz landing is the right one: inert.
        with self.assertRaises(kit_faults.FaultInert):
            reach(Frames441Slapback, read_frames, 44100, {})

    def test_the_rates_left_out_are_left_out_for_their_stated_reason(self):
        # At 22.05 kHz grid 94-126 hand the old open top's clamp too.
        with self.assertRaises(kit_faults.FaultReachable):
            reach(OpenTopSlapback, read_damping, 22050, {})
        # The raw Tone is silent at the defaults, where Tone is out.
        with self.assertRaises(kit_faults.FaultInert):
            reach(RawToneSlapback, read_damping, RATE, {})


class TheRetiredFaultsAreDialable(unittest.TestCase):
    """The gate audit's dial, kept: the faults fix round 1 retired render
    what a clean surface state renders, byte for byte."""

    def _noise(self, rate, seconds=1.0):
        frames = int(seconds * rate)
        return np.frombuffer(probes.noise_det(frames=frames, dbfs=-6.0,
                                              channels=1),
                             dtype=np.int16)[:frames].astype(float)

    def test_the_floor_is_repeats_0_05(self):
        for rate in RATES:
            x = self._noise(rate)
            a = render(FloorSlapback, x, rate)
            b = render(SlapbackDelay, x, rate, repeats=0.05)
            c = render(SlapbackDelay, x, rate,
                       macros={REPEATS_I: 127 * 0.05 / 0.6})
            self.assertEqual(int(np.count_nonzero(a != b)), 0, rate)
            self.assertEqual(int(np.count_nonzero(a != c)), 0, rate)

    def test_frames_at_44k_are_a_time_at_48k(self):
        x = self._noise(48000)
        a = render(Frames441Slapback, x, 48000)
        b = render(SlapbackDelay, x, 48000, time_ms=5954 * 1000.0 / 48000)
        self.assertEqual(int(np.count_nonzero(a != b)), 0)

    def test_the_open_top_is_a_constructor_tone(self):
        for rate in RATES:
            x = self._noise(rate)
            a = render(OpenTopSlapback, x, rate)
            b = render(SlapbackDelay, x, rate, tone_hz=19999.999)
            self.assertEqual(int(np.count_nonzero(a != b)), 0, rate)


class NullBuildRed(unittest.TestCase):
    """Every demonstrated row goes red on the class built as a wire, beside
    a control on the real class that must pass."""

    def test_every_row_is_red_on_a_wire(self):
        for name, measure in (("T1", t1_measure), ("T2", t2_measure),
                              ("T3", t3_measure), ("T4", t4_measure),
                              ("T5", t5_measure)):
            with self.subTest(row=name):
                result = kit_faults.null_build_red(
                    SlapbackDelay, measure, label="SlapbackDelay %s" % name)
                self.assertFalse(result["null"]["passed"], name)
                self.assertTrue(result["control"]["passed"], name)


if __name__ == "__main__":
    unittest.main()
