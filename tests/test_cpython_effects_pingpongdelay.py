"""`PingPongDelay`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/PingPongDelay.md`
(frozen at anchor eb46672, the Station A critique's re-freeze); its Tier 2
rows are T1-T5. Each row here is the measurement at a few of the row's
cells and the same measurement shown red on a planted fault of the same
kind, at the constructor defaults (or, for a clause the defaults do not
reach, at the row's own cell, said where it is). Every fault is shown
unreachable from every macro position and shipped patch, and every row's
measurement is shown red on the class built as a wire. The full spans, the
three interpreters and the rates live in the evidence pack, not in this
file.

Every law a measurement checks against is written out here from the
dossier, never taken from the class: the whole-frame landing, the Time
span, the Spread law, the reference mono delay.

The rebuild is parked (not in `rebuilt.ADOPTED`), so the class is reached by
`rebuilt.module_class("PingPongDelay")`.
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
import kit_faults                                          # noqa: E402
import kit_probes as probes                                 # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import rebuilt                            # noqa: E402
from audioeffects.chorus import nominal_damping_hz          # noqa: E402
from audioeffects.rebuilt import pingpongdelay as pp        # noqa: E402
from audioeffects.rebuilt.digitaldelay import (             # noqa: E402
    clear_of_stalls)
from tools.effect_measurements import instantaneous_hz      # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
BLOCK = 256
RATES = (48000, 44100, 22050)
(TIME_I, FEEDBACK_I, MIX_I, SPREAD_I, SIDE_I, SYNC_I, DIVISION_I, TONE_I,
 CUT_I) = range(9)

PingPongDelay = rebuilt.module_class("PingPongDelay")

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.join(HERE, "..", "tools", "effect_probes")


# --------------------------------------------------------------------------
# The dossier's laws, written out independently of the class


def law_frames(time_ms, rate):
    """Section 6: the nearest whole frame, floor(ms fs / 1000 + 0.5)."""
    return int(math.floor(time_ms * rate / 1000.0 + 0.5))


def law_time_ms(midi):
    """Section 6: Time is 20-1000 ms, log, on the 0-127 grid."""
    return 20.0 * 50.0 ** (midi / 127.0)


def law_feedback(midi):
    return 0.99 * midi / 127.0


def law_spread(n, s, f, first):
    """T4: repeat n's level, as a fraction of the click, on the First Side
    channel (`first` True) or the other."""
    sign = 1.0 if first else -1.0
    return f ** (n - 1) * ((1.0 - s / 2.0)
                           + sign * (s / 2.0) * (1.0 - 2.0 * s) ** (n - 1))


#: Division's sixteen values in quarter-note beats (DigitalDelay's list).
LAW_DIVISION_BEATS = (0.125, 1.0 / 6.0, 0.1875, 0.25, 1.0 / 3.0, 0.375, 0.5,
                      2.0 / 3.0, 0.75, 1.0, 4.0 / 3.0, 1.5, 2.0, 8.0 / 3.0,
                      3.0, 4.0)

#: Section 6's patch table, in engineering units: (Time ms, Feedback, Mix,
#: Spread, First Side, Sync, Division index, Tone Hz, Cut Hz).
DOSSIER_PATCHES = (
    ("Wide Bounce", (280.0, 0.45, 0.3, 1.0, 0, 0, 6, 16000.0, 20.0)),
    ("Eighth Note Bounce", (280.0, 0.5, 0.3, 1.0, 0, 1, 6, 16000.0, 20.0)),
    ("Quarter Note Bounce", (280.0, 0.4, 0.3, 1.0, 0, 1, 9, 16000.0, 20.0)),
    ("Narrow Bounce", (280.0, 0.45, 0.3, 0.5, 0, 0, 6, 16000.0, 20.0)),
    ("Two Delays", (280.0, 0.45, 0.3, 0.0, 0, 0, 6, 16000.0, 20.0)),
    ("Dark Bounce", (420.0, 0.65, 0.3, 1.0, 0, 0, 6, 2500.0, 20.0)),
    ("Right First", (280.0, 0.45, 0.3, 1.0, 1, 0, 6, 16000.0, 20.0)),
)
DOSSIER_SPANS = ((20.0, 1000.0, "log"), (0.0, 0.99), (0.0, 2.0), (0.0, 1.0),
                 (0.0, 1.0), (0.0, 1.0), (0.0, 15.0),
                 (800.0, 16000.0, "log"), (20.0, 400.0, "log"))
DOSSIER_MODES = ("UNIPOLAR", "UNIPOLAR", "UNIPOLAR", "UNIPOLAR", "TOGGLE",
                 "TOGGLE", "UNIPOLAR", "UNIPOLAR", "UNIPOLAR")

#: The presence floor T1 and T2 share (dossier section 3).
FLOOR = 200


# --------------------------------------------------------------------------
# Planted faults, one or more per Tier 2 row, each of the row's own kind


class LossyCrossPingPong(PingPongDelay):
    """T1's exclusion bar: `cross_feed` 0.99 with `input_pan` -1 at Spread
    1. The clean class hands (s, -s), so no position reaches (0.99, -1),
    and even `spread=0.99` hands (0.99, -0.99). The wrong channel reads
    about -23 dB."""

    NAME = 'PingPongDelay'

    def _cross_and_pan(self):
        cross, pan = PingPongDelay._cross_and_pan(self)
        return cross * 0.99, pan


class LateReadPingPong(PingPongDelay):
    """T1's peak clause: the delay handed one frame late, T + 1 frames.
    Repeat n peaks n frames late."""

    NAME = 'PingPongDelay'

    def _node_time_ms(self, frames):
        return (frames + 1) * 1000.0 / self._sample_rate


class ScaledFeedbackPingPong(PingPongDelay):
    """T2: Feedback handed as 0.98 f, about 2 % against the 1 % bar."""

    NAME = 'PingPongDelay'

    def _refresh(self):
        PingPongDelay._refresh(self)
        self._delay.set(feedback=self._feedback * 0.98)


class MonoStereoSettingsPingPong(PingPongDelay):
    """T3, the seeds' own (section 7.1): the one-channel build left at the
    stereo settings, `cross_feed` s and `input_pan` -s. At Spread 1 the
    loop is silenced after one half-level repeat."""

    NAME = 'PingPongDelay'

    def _cross_and_pan(self):
        spread = self._value(SPREAD_I)
        return spread, -spread


class PanlessPingPong(PingPongDelay):
    """T4: `input_pan` left at 0, the cross-feed alone (section 7.3)."""

    NAME = 'PingPongDelay'

    def _cross_and_pan(self):
        cross, pan = PingPongDelay._cross_and_pan(self)
        return cross, 0.0


class DryGainPingPong(PingPongDelay):
    """T5: the output +0.1 dB (`kit_faults.HiddenGain`), `DigitalDelay`'s
    `DryGainDelay`."""

    NAME = 'PingPongDelay'

    def _build(self, *arguments, **options):
        PingPongDelay._build(self, *arguments, **options)
        self._output = kit_faults.HiddenGain(self._delay, 0.1)


class _Steer(kit_faults._Node):
    """Between the source and the node: `mode` "avg" hands both channels
    (L + R) / 2, "swap" hands them exchanged. On a channel-identical source
    both are the identity, byte for byte, which is why T5's kit materials
    cannot see them (fix round 1; the material refuter's faults)."""

    def __init__(self, source, mode):
        kit_faults._Node.__init__(self, source)
        self.mode = mode

    def _process(self, frames):
        if self.channel_count != 2:
            return frames
        x = frames.reshape(-1, 2)
        if self.mode == "avg":
            m = (x[:, 0] + x[:, 1]) / 2.0
            return np.repeat(m[:, None], 2, axis=1).reshape(-1)
        return x[:, ::-1].reshape(-1)


class MonoInPingPong(PingPongDelay):
    """T5's "never spread": the node fed (L + R) / 2 on both channels. At
    Spread 1 the loop hears the average anyway, so only the dry changes."""

    NAME = 'PingPongDelay'

    def _build(self, *arguments, **options):
        PingPongDelay._build(self, *arguments, **options)
        self._steer = _Steer(self._source, "avg")
        self._delay.play(self._steer)


class SwapInPingPong(PingPongDelay):
    """T5's "never spread": the node fed the source with its channels
    exchanged, so the dry comes out on the wrong side."""

    NAME = 'PingPongDelay'

    def _build(self, *arguments, **options):
        PingPongDelay._build(self, *arguments, **options)
        self._steer = _Steer(self._source, "swap")
        self._delay.play(self._steer)


class NoSlewPingPong(PingPongDelay):
    """Section 8.5's walk: the slew off, so a Time move jumps. Red on the
    pitch clause, and on the step bar on a rising move only."""

    NAME = 'PingPongDelay'

    def _refresh(self):
        PingPongDelay._refresh(self)
        self._delay.set(delay_slew=0.0)


class FrozenFilterPingPong(PingPongDelay):
    """Section 8.11's defect, restated at audiodsp v0.6.3rc1: once a loop
    filter has been in, its out stop leaves it in at 0.001 Hz, where its
    float32 coefficient is one step above 0 and its state cannot move, so
    it holds what it held, as the node's out stop did up to v0.6.2, and
    plays it back when the filter comes back in."""

    NAME = 'PingPongDelay'

    def _refresh(self):
        PingPongDelay._refresh(self)
        if self._damping > 0.0:
            self._tone_was_in = True
        elif getattr(self, "_tone_was_in", False):
            self._delay.set(damping_hz=0.001)
        if self._cut > 0.0:
            self._cut_was_in = True
        elif getattr(self, "_cut_was_in", False):
            self._delay.set(cut_hz=0.001)

    def _clear(self):
        PingPongDelay._clear(self)
        self._tone_was_in = self._cut_was_in = False


class SteppedPingPong(PingPongDelay):
    """The workaround retired at audiodsp v0.6.3rc1: with Repeat Tone in,
    the Feedback handed at the nearer edge of the stall window
    (`clear_of_stalls`), a Feedback nobody set."""

    NAME = 'PingPongDelay'

    def _refresh(self):
        PingPongDelay._refresh(self)
        self._step()

    def _step(self):
        if self._damping > 0.0 and self._feedback > 0.0:
            excess = pp.tone_excess(self._damping, self._sample_rate)[1]
            stepped = clear_of_stalls(self._feedback, excess)
            if stepped != self._feedback:
                self._feedback = stepped
                self._delay.set(feedback=stepped)


class TrackingPingPong(SteppedPingPong):
    """The class before audiodsp v0.6.3rc1: once Repeat Tone has been in,
    its out stop hands `damping_hz` at 32 x the rate (the low-pass tracking
    the tap), and the Feedback is stepped clear as with Tone in."""

    NAME = 'PingPongDelay'

    def _refresh(self):
        PingPongDelay._refresh(self)
        if self._damping > 0.0:
            self._tone_was_in = True
        elif getattr(self, "_tone_was_in", False):
            self._damping = 32.0 * self._sample_rate
            self._delay.set(damping_hz=self._damping)
        self._step()

    def _clear(self):
        PingPongDelay._clear(self)
        self._tone_was_in = False


class HeldCutPingPong(PingPongDelay):
    """The class before audiodsp v0.6.3rc1: once Repeat Cut has been in,
    its bottom stop stays in circuit at the 20 Hz corner, and
    `tail_samples` is `None` while it lasts."""

    NAME = 'PingPongDelay'

    def _refresh(self):
        PingPongDelay._refresh(self)
        if self._cut > 0.0:
            self._cut_was_in = True
        elif getattr(self, "_cut_was_in", False):
            self._cut = pp.nominal_cut_hz(self._hz(pp.CUT_MIN_HZ),
                                          self._sample_rate)
            self._delay.set(cut_hz=self._cut)

    def _clear(self):
        PingPongDelay._clear(self)
        self._cut_was_in = False


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


def click(frames, level=20000):
    x = np.zeros(frames)
    x[0] = level
    return x


def burst(rate, ms=50.0, peak=8192):
    """T3's 50 ms deterministic noise burst: numpy `RandomState(12345)`,
    uniform, peak 8 192 LSB (-12 dBFS)."""
    n = int(round(ms * rate / 1000.0))
    return np.random.RandomState(12345).uniform(-peak, peak, n)


def material(name, rate, channels):
    """A kit probe as it ships, (frames, channels) int16."""
    path = os.path.join(PROBES, str(rate), "%dch" % channels, name + ".wav")
    with wave.open(path, "rb") as handle:
        data = handle.readframes(handle.getnframes())
    return np.frombuffer(data, dtype=np.int16).reshape(-1, channels)


def render_pcm(cls, pcm, rate, macros=None, **options):
    channels = pcm.shape[1]
    source = probes.ArraySource(array("h", pcm.reshape(-1).tobytes()),
                                rate=rate, channels=channels, block=BLOCK)
    effect = cls(source, sample_rate=rate, **options)
    for index in sorted(macros or {}):
        effect.set_macro(index, macros[index])
    return pull(effect, pcm.shape[0], channels)


def cell_frames(options, macros=None, rate=RATE):
    """The cell's whole-frame T by the dossier's law: a constructor Time
    as given, a patch or a Time macro at its grid value."""
    macros = macros or {}
    if TIME_I in macros:
        return law_frames(law_time_ms(macros[TIME_I]), rate)
    if "patch" in options:
        midi = PingPongDelay.PATCHES[options["patch"]][1]
        return law_frames(law_time_ms(midi[TIME_I]), rate)
    return law_frames(options.get("time_ms", 280.0), rate)


def cell_feedback(options, macros=None):
    macros = macros or {}
    if FEEDBACK_I in macros:
        return law_feedback(macros[FEEDBACK_I])
    if "patch" in options:
        return law_feedback(PingPongDelay.PATCHES[options["patch"]][1][1])
    return options.get("feedback", 0.45)


# --------------------------------------------------------------------------
# T1: repeats alternate


def windows(y, T, rate, repeats=8):
    """(own channel, opposite channel, own peak, peak offset) per repeat,
    in +-1 ms windows at n T, First Side left: odd n on channel 0."""
    half = int(math.floor(rate / 1000.0))
    rows = []
    for n in range(1, repeats + 1):
        at = n * T
        lo, hi = max(0, at - half), min(len(y), at + half + 1)
        own = 0 if n % 2 else 1
        seg = y[lo:hi].astype(np.int32)
        if len(seg) == 0:
            rows.append((own, 0, 0, None))
            continue
        peak_at = int(np.argmax(np.abs(seg[:, own])))
        rows.append((own, int(np.count_nonzero(seg[:, 1 - own])),
                     int(np.abs(seg[:, own]).max()), lo + peak_at - at))
    return rows


def t1_measure(cls, rate=RATE, macros=None, peak_clause=True, **options):
    """T1 at one cell: the click (20 000 LSB, both channels) at Mix 2 and
    Spread 1; per repeat 1-8 the opposite channel exact zero in its +-1 ms
    window, its own peak at least 200 LSB, and (with Repeat Tone out) the
    peak on n T; and the First Side right render the left one swapped."""
    options = dict(options)
    options.setdefault("mix", 2.0)
    options.setdefault("spread", 1.0)
    T = cell_frames(options, macros, rate)
    frames = 9 * T + int(0.02 * rate)
    x = click(frames)
    left = render(cls, x, rate, 2, macros=macros, first_side="left",
                  **options)
    right = render(cls, x, rate, 2, macros=macros, first_side="right",
                   **options)
    rows = windows(left, T, rate)
    leaks = sum(row[1] for row in rows)
    weak = [n + 1 for n, row in enumerate(rows) if row[2] < FLOOR]
    late = [n + 1 for n, row in enumerate(rows)
            if row[3] is None or row[3] != 0]
    swapped = int(np.count_nonzero(right != left[:, ::-1]))
    passed = (leaks == 0 and not weak and swapped == 0
              and (not peak_clause or not late))
    return {"passed": passed, "leaks": leaks, "weak": weak, "late": late,
            "swapped": swapped, "peaks": [row[2] for row in rows],
            "offsets": [row[3] for row in rows], "T": T}


def t1_default(cls):
    return t1_measure(cls, feedback=0.6)


# --------------------------------------------------------------------------
# T2: one decay ratio across the alternation


def t2_measure(cls, rate=RATE, fit=True, **options):
    """Peaks of repeats 1-8 in time order across both channels; each
    successive ratio within 1 % of f, and (from Feedback MIDI 28) the two
    channels' fitted decays per 2T within 1 % of each other. Only peaks of
    at least 200 LSB enter; fewer than three, or fewer than two on a
    channel for the fit, reads red."""
    options = dict(options)
    options.setdefault("mix", 2.0)
    options.setdefault("spread", 1.0)
    f = cell_feedback(options)
    T = cell_frames(options, None, rate)
    frames = 9 * T + int(0.02 * rate)
    y = render(cls, click(frames), rate, 2, **options)
    rows = windows(y, T, rate)
    peaks = [row[2] for row in rows]
    kept = [p for p in peaks if p >= FLOOR]
    # Peaks in time order stop at the first one under the floor.
    run = []
    for p in peaks:
        if p < FLOOR:
            break
        run.append(p)
    ratios = [run[k + 1] / float(run[k]) for k in range(len(run) - 1)]
    worst = max([abs(r / f - 1.0) for r in ratios] or [float("inf")])
    ok_ratio = len(run) >= 3 and worst <= 0.01
    agree = None
    ok_fit = True
    if fit:
        decays = []
        for own in (0, 1):
            n = [k + 1 for k, row in enumerate(rows)
                 if row[0] == own and row[2] >= FLOOR]
            if len(n) < 2:
                decays.append(None)
                continue
            logs = [math.log(rows[k - 1][2]) for k in n]
            slope = np.polyfit(n, logs, 1)[0]
            decays.append(math.exp(2.0 * slope))
        if None in decays:
            ok_fit = False
        else:
            agree = abs(decays[0] / decays[1] - 1.0)
            ok_fit = agree <= 0.01
    one_channel = [rows[k][2] for k in range(0, 8, 2) if rows[k][2] >= FLOOR]
    down = (one_channel[1] / float(one_channel[0])
            if len(one_channel) >= 2 else None)
    return {"passed": ok_ratio and ok_fit, "worst": worst, "agree": agree,
            "kept": len(kept), "peaks": peaks, "down_one_channel": down}


def t2_default(cls):
    return t2_measure(cls)


# --------------------------------------------------------------------------
# T3: the mono sum is an ordinary delay, exactly


def reference(x, rate, T, f, damping=0.0, cut=0.0):
    """A plain one-channel `FeedbackDelay(cross_feed=0, input_pan=0)` at
    whole-frame T and f, Mix 2."""
    node = pp.audioecho.FeedbackDelay(
        sample_rate=rate, channel_count=1, max_delay_ms=1001.0,
        delay_ms=T * 1000.0 / rate, feedback=f, mix=2.0,
        damping_hz=damping, cut_hz=cut, cross_feed=0.0, input_pan=0.0)
    source, _ = to_source(x, 1, rate)
    node.play(source)
    out = array("h")
    while len(out) < len(x):
        out.extend(memoryview(bytes(audiocore.get_buffer(node)[1]))
                   .cast("h"))
    node.deinit()
    return np.array(out[:len(x)], dtype=np.int32)


def t3_measure(cls, rate=RATE, what="click", damping=0.0, cut=0.0,
               **options):
    """The class's stereo render summed in int32, the class's mono render
    and the plain reference, compared sample for sample at Mix 2 (at
    Spread 0 the sum is twice the reference)."""
    options = dict(options)
    macros = None
    if "patch" in options:
        # The patch's own Mix is 0.2992: Mix is held at 2 over it.
        macros = {MIX_I: 127}
    else:
        options.setdefault("mix", 2.0)
    options.setdefault("spread", 1.0)
    T = cell_frames(options, None, rate)
    f = cell_feedback(options)
    frames = 9 * T + int(0.1 * rate)
    x = np.zeros(frames)
    if what == "click":
        x[0] = 20000
    elif what == "quiet":
        x[0] = 328
    else:
        b = np.round(burst(rate))
        x[:len(b)] = b
    stereo = render(cls, x, rate, 2, macros=macros,
                    **options).astype(np.int32)
    total = stereo[:, 0] + stereo[:, 1]
    mono = render(cls, x, rate, 1, macros=macros,
                  **options)[:, 0].astype(np.int32)
    ref = reference(x, rate, T, f, damping, cut)
    scale = 2 if options["spread"] == 0.0 else 1
    sum_diff = int(np.count_nonzero(total != scale * ref))
    mono_diff = int(np.count_nonzero(mono != ref))
    repeats_ref = int(np.count_nonzero(ref[1:]))
    repeats_mono = int(np.count_nonzero(mono[1:]))
    passed = sum_diff == 0 and mono_diff == 0 and repeats_mono >= repeats_ref
    return {"passed": passed, "sum_diff": sum_diff, "mono_diff": mono_diff,
            "repeats": (repeats_mono, repeats_ref)}


def t3_default(cls):
    return t3_measure(cls, feedback=0.6)


# --------------------------------------------------------------------------
# T4: Spread's law


def t4_measure(cls, rate=RATE, spreads=None, time_ms=280.0, feedback=0.6,
               level=20000, swap=False):
    """On the channel-identical click at Mix 2: every repeat 1-8 on both
    channels within 4 LSB of the law (values under 4 LSB recorded, not
    claimed), L - R exact zero at Spread 0, the wrong-multiple windows exact
    zero at Spread 1, and (`swap`) the First Side right render the left one
    swapped."""
    spreads = [k / 10.0 for k in range(11)] if spreads is None else spreads
    T = law_frames(time_ms, rate)
    frames = 9 * T + int(0.02 * rate)
    x = click(frames, level)
    worst = 0.0
    red = []
    for s in spreads:
        left = render(cls, x, rate, 2, time_ms=time_ms, feedback=feedback,
                      mix=2.0, spread=s, first_side="left")
        for n in range(1, 9):
            for channel, first in ((0, True), (1, False)):
                law = level * law_spread(n, s, feedback, first)
                got = float(left[n * T, channel])
                if abs(law) < 4.0 and law != 0.0:
                    continue
                if law == 0.0 and got != 0.0:
                    red.append(("zero", s, n, channel, got))
                error = abs(got - law)
                worst = max(worst, error)
                if error > 4.0:
                    red.append(("law", s, n, channel, got, law))
        if s == 0.0:
            lr = int(np.count_nonzero(left[:, 0] != left[:, 1]))
            if lr:
                red.append(("L-R", s, lr))
        if s == 1.0:
            leaks = sum(row[1] for row in windows(left, T, rate))
            if leaks:
                red.append(("wrong multiple", s, leaks))
        if swap:
            right = render(cls, x, rate, 2, time_ms=time_ms,
                           feedback=feedback, mix=2.0, spread=s,
                           first_side="right")
            differ = int(np.count_nonzero(right != left[:, ::-1]))
            if differ:
                red.append(("swap", s, differ))
    return {"passed": not red, "worst": worst, "red": red}


def t4_default(cls):
    return t4_measure(cls, spreads=(0.0, 0.5, 1.0))


# --------------------------------------------------------------------------
# T5: the dry path is a wire until the first repeat


T5_MATERIALS = ("ramp_fs", "tones_step", "sweep_log")


def lr_material(rate):
    """Fix round 1: channel-different stereo, independent L and R noise
    (`RandomState(7)`, uniform, peak 16 000 LSB = -6.2 dBFS), 2 T at
    280 ms long. Every kit probe is channel-identical, and on those a dry
    that is mono-summed or swapped is byte-identical to the source."""
    n = 2 * law_frames(280.0, rate)
    rs = np.random.RandomState(7)
    left = rs.uniform(-16000, 16000, n)
    right = rs.uniform(-16000, 16000, n)
    return np.round(np.stack([left, right], axis=1)).astype(np.int16)


def antiphase_material(rate):
    """R = -L: `lr_material`'s left channel against its own negative."""
    left = lr_material(rate)[:, 0]
    return np.stack([left, -left], axis=1)


def read_dry_crosstalk(effect):
    """How much of the right input reaches the left output before the first
    repeat, at this instance's macro positions: two copies on 256 frames,
    (L = ramp, R = 0) and (L = ramp, R = -ramp), and the count of left
    output samples that differ. 0 for a dry that is each channel's own
    signal, at every Mix: the first repeat is never inside 256 frames
    (the material refuter's reading)."""
    rate = effect._sample_rate
    n = 256
    ramp = np.linspace(-30000, 30000, n)
    outs = []
    for right in (np.zeros(n), -ramp):
        pcm = np.stack([ramp, right], axis=1).round().astype(np.int16)
        other = type(effect)(probes.ArraySource(
            array("h", pcm.reshape(-1).tobytes()), rate=rate, channels=2,
            block=BLOCK), sample_rate=rate)
        for index in range(len(type(effect).MACRO_LABELS)):
            other.set_macro(index, effect.get_macro(index))
        outs.append(pull(other, n, 2))
        other.deinit()
    return int(np.count_nonzero(outs[0][:, 0] != outs[1][:, 0]))


def t5_measure(cls, rate=RATE, channels=2, materials=T5_MATERIALS,
               macros=None, pcm=None, **options):
    """WIRE over the first T - 1 frames on each material, and, where Mix is
    above 0, the output not the source somewhere in the T frames from
    frame T. `pcm`, when given, is the one material, as (frames,
    channels) int16."""
    T = cell_frames(options, macros, rate)
    probe = cls(silence_src(64, channels, rate), sample_rate=rate,
                **options)
    for index in sorted(macros or {}):
        probe.set_macro(index, macros[index])
    mix = probe.macro(MIX_I)
    probe.deinit()
    differing = 0
    absent = []
    given = pcm
    for name in (("given",) if given is not None else materials):
        pcm = given if given is not None else material(name, rate, channels)
        end = min(len(pcm), 2 * T)
        y = render_pcm(cls, pcm[:end], rate, macros=macros, **options)
        differing += int(np.count_nonzero(y[:T - 1] != pcm[:T - 1]))
        if mix > 0.0 and len(pcm) > T:
            if not np.count_nonzero(y[T:end] != pcm[T:end]):
                absent.append(name)
    return {"passed": differing == 0 and not absent,
            "differing": differing, "absent": absent, "T": T}


def t5_default(cls):
    return t5_measure(cls, materials=("tones_step",))


def t5_lr_default(cls):
    return t5_measure(cls, pcm=lr_material(RATE))


# --------------------------------------------------------------------------
# The walk (section 8.5), measured as the dossier's A6.6 did


def walk_cents(cls, rate=RATE, start_ms=280.0, target_ms=200.0):
    """997 Hz at 12 000 LSB, Mix 2, Feedback 0; Time moved on a block
    boundary at least 8 192 frames after the start Time's wet begins; the
    pitch over the walk by the kit's `instantaneous_hz`, median over the
    walk less 400 frames each end. (cents, walk frames)."""
    T0 = law_frames(start_ms, rate)
    move = ((T0 + 8192) // BLOCK + 1) * BLOCK
    walk = int(round(abs(target_ms - start_ms) / 1000.0 / pp.SLEW * rate))
    frames = move + walk + rate // 2
    x = 12000 * np.sin(2.0 * math.pi * 997.0 * np.arange(frames) / rate)
    source, _ = to_source(x, 2, rate)
    effect = cls(source, sample_rate=rate, time_ms=start_ms, feedback=0.0,
                 mix=2.0)
    target_midi = 127.0 * math.log(target_ms / 20.0) / math.log(50.0)

    def on_block(frame):
        if frame == move:
            effect.set_macro(TIME_I, target_midi)

    y = pull(effect, frames, 2, on_block)[:, 0].astype(float)
    hz = instantaneous_hz(y, rate)
    segment = hz[move + 400:move + walk - 400]
    return 1200.0 * math.log(float(np.median(segment)) / 997.0, 2.0), walk


def law_cents(start_ms, target_ms):
    ratio = 1.0 + pp.SLEW if target_ms < start_ms else 1.0 - pp.SLEW
    return 1200.0 * math.log(ratio, 2.0)


# --------------------------------------------------------------------------
# Reachability: what the node is handed at the position walked


class NodeSpy:
    """While active, every `audioecho.FeedbackDelay.set` call records its
    options on the node as `_handed` (the latest value of each)."""

    def __enter__(self):
        node_class = pp.audioecho.FeedbackDelay
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


def handed(effect, name):
    return effect._delay._handed[name]


def read_cross_pan(effect):
    return (round(float(handed(effect, "cross_feed")), 6),
            round(float(handed(effect, "input_pan")), 6))


def read_frames(effect):
    return round(float(handed(effect, "delay_ms")) * effect._sample_rate
                 / 1000.0, 3)


def read_feedback(effect):
    return round(float(handed(effect, "feedback")), 4)


def read_slew(effect):
    return float(handed(effect, "delay_slew"))


def read_dry_gain(effect):
    """The dry path's gain before the first repeat: a copy at these
    positions on a 256-frame full-scale ramp, least-squares out / in."""
    ramp = probes.ramp_fs(frames=256, channels=effect.channel_count)
    other = type(effect)(probes.ArraySource(
        ramp, rate=effect._sample_rate, channels=effect.channel_count,
        block=BLOCK), sample_rate=effect._sample_rate)
    for index in range(len(type(effect).MACRO_LABELS)):
        other.set_macro(index, effect.get_macro(index))
    out = pull(other, 256).reshape(-1).astype(np.float64)
    src = np.array(ramp, dtype=np.float64)
    other.deinit()
    return round(float(np.dot(out, src) / np.dot(src, src)), 5)


#: The fine grid every handed-value walk also runs on: quarter steps, 509
#: positions per macro.
FINE = tuple(i / 4.0 for i in range(509))

#: (name, fault, reading, channels). Every walk runs at 48, 44.1 and
#: 22.05 kHz on the kit's grid, and the handed-value walks on `FINE` too.
REACH_WALKS = (
    ("LossyCrossPingPong", LossyCrossPingPong, read_cross_pan, 2),
    ("LateReadPingPong", LateReadPingPong, read_frames, 2),
    ("ScaledFeedbackPingPong", ScaledFeedbackPingPong, read_feedback, 2),
    ("MonoStereoSettingsPingPong", MonoStereoSettingsPingPong,
     read_cross_pan, 1),
    ("PanlessPingPong", PanlessPingPong, read_cross_pan, 2),
    ("NoSlewPingPong", NoSlewPingPong, read_slew, 2),
)


def reach(faulted, reading, rate, channels=2, grid=None):
    def build(cls):
        return cls(silence_src(512, channels, rate), sample_rate=rate)

    with NodeSpy():
        return kit_faults.fault_reachability(PingPongDelay, faulted, reading,
                                             build, grid=grid)


def spied(cls=None, **options):
    rate = options.pop("rate", RATE)
    channels = options.pop("channels", 2)
    with NodeSpy():
        effect = (cls or PingPongDelay)(silence_src(512, channels, rate),
                                        sample_rate=rate, **options)
    return effect


# --------------------------------------------------------------------------
# The surface


class TheSurface(unittest.TestCase):
    """Every node `set` in these tests is recorded, so a macro moved after
    construction reads back what the node was handed."""

    def setUp(self):
        self._spy = NodeSpy().__enter__()

    def tearDown(self):
        self._spy.__exit__(None, None, None)

    def test_macros_patches_tier_latency(self):
        cls = PingPongDelay
        self.assertEqual(cls.MACRO_LABELS,
                         ("Time", "Feedback", "Mix", "Spread", "First Side",
                          "Sync", "Division", "Repeat Tone", "Repeat Cut"))
        self.assertEqual(tuple(cls.MACRO_MODES[i] for i in range(9)),
                         DOSSIER_MODES)
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
        self.assertNotIn("PingPongDelay", rebuilt.ADOPTED)
        self.assertIn("PingPongDelay", rebuilt.parked())
        self.assertIsNot(audioeffects.PingPongDelay, PingPongDelay)

    def test_patches_are_the_dossier_settings_on_the_grid(self):
        for index, (name, values) in enumerate(DOSSIER_PATCHES):
            label, midi = PingPongDelay.PATCHES[index]
            self.assertEqual(label, name)
            self.assertEqual(midi, tuple(
                _component.macro_of(span, value, mode)
                for span, value, mode in zip(DOSSIER_SPANS, values,
                                             DOSSIER_MODES)))

    def test_patch_0_is_the_constructor_grid(self):
        effect = PingPongDelay(silence_src(512), sample_rate=RATE)
        for index, expected in enumerate(PingPongDelay.PATCHES[0][1]):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_what_patch_0_hands_the_node(self):
        # Tier 3's reference patch on the grid: 13 575 frames, 0.4521,
        # 0.2992, the full cross, both filters out.
        effect = spied(patch=0)
        self.assertEqual(read_frames(effect), 13575.0)
        self.assertEqual(read_feedback(effect), 0.4521)
        self.assertAlmostEqual(handed(effect, "mix"), 0.2992, places=4)
        self.assertEqual(read_cross_pan(effect), (1.0, -1.0))
        self.assertEqual(handed(effect, "damping_hz"), 0.0)
        self.assertEqual(handed(effect, "cut_hz"), 0.0)
        self.assertEqual(handed(effect, "delay_slew"), 0.1875)

    def test_time_lands_on_a_whole_frame(self):
        for rate in RATES:
            effect = spied(rate=rate)
            self.assertEqual(read_frames(effect), law_frames(280.0, rate))
            for midi in [127.0 * k / 16.0 for k in range(17)]:
                effect.set_macro(TIME_I, midi)
                self.assertEqual(read_frames(effect),
                                 law_frames(law_time_ms(midi), rate),
                                 (rate, midi))
        # The stops at 48 kHz: 960 and 48 000 frames.
        effect = spied()
        effect.set_macro(TIME_I, 0)
        self.assertEqual(read_frames(effect), 960.0)
        effect.set_macro(TIME_I, 127)
        self.assertEqual(read_frames(effect), 48000.0)

    def test_where_the_node_lands_the_handed_frame(self):
        # Section 6, restated at Station B fix round 1: the node turns the
        # handed ms back into frames in float32
        # (`audiodsp_feedback_delay.c:148`). At 48 kHz every grid position
        # lands exactly; at 44.1 and 22.05 kHz these land one float32 step
        # off, which the class cannot avoid (the node ask is drafted).
        off_frame = {
            48000: [],
            44100: [2, 3, 4, 19, 20, 24, 25, 28, 38, 43, 47, 48, 50, 63, 65,
                    67, 69, 70, 83, 92, 93, 95, 107, 108, 114],
            22050: [2, 4, 19, 28, 38, 47, 63, 65, 67, 69, 70, 83, 88, 92, 93,
                    95, 108, 110, 112, 114],
        }
        f32 = np.float32
        for rate in RATES:
            effect = spied(rate=rate)
            missed = []
            for midi in range(128):
                effect.set_macro(TIME_I, midi)
                ms = f32(handed(effect, "delay_ms"))
                frames = (ms * f32(rate)) / f32(1000.0)
                law = law_frames(law_time_ms(midi), rate)
                self.assertEqual(read_frames(effect), law, (rate, midi))
                if float(frames) != law:
                    self.assertLessEqual(abs(float(frames) - law),
                                         2.0 ** -9, (rate, midi))
                    missed.append(midi)
            self.assertEqual(missed, off_frame[rate], rate)

    def test_an_off_frame_time_leaks_into_the_next_frame(self):
        # The reviewer's cell: MIDI 95 at 44.1 kHz is 16 457 frames, and a
        # 20 000 click's repeat reads 39 one frame early; at 48 kHz the same
        # position is exact.
        for rate, window in ((44100, [0, 39, 19961, 0]),
                             (48000, [0, 0, 20000, 0])):
            frames = law_frames(law_time_ms(95), rate)
            y = render(PingPongDelay, click(frames + 64), rate=rate,
                       macros={TIME_I: 95}, mix=2.0, feedback=0.0)
            total = y.astype(np.int32).sum(axis=1)
            self.assertEqual([int(v) for v in total[frames - 2:frames + 2]],
                             window, rate)

    def test_a_host_echoing_time_keeps_the_frame(self):
        # 135 ms at 44.1 kHz is 5 953.5 frames, which the law lands up.
        effect = spied(rate=44100, time_ms=135.0)
        self.assertEqual(read_frames(effect), 5954.0)
        effect.set_macro(TIME_I, effect.get_macro(TIME_I))
        self.assertEqual(read_frames(effect), 5954.0)

    def test_a_lowered_ceiling_clamps_visibly(self):
        effect = spied(max_time_ms=300.0)
        for midi in (100, 110, 127):
            effect.set_macro(TIME_I, midi)
            self.assertEqual(read_frames(effect), 14400.0)
            self.assertAlmostEqual(effect.get_macro(TIME_I), 87.91,
                                   delta=0.005)
        self.assertEqual(spied(max_time_ms=float("nan"))._max_time_ms,
                         1000.0)
        self.assertEqual(spied(max_time_ms=5000.0)._max_time_ms, 1000.0)

    def test_sync_quantises_time_and_clamps(self):
        def at_120():
            return (True, 0.0, 120.0, 4, 4)

        expected = {0: 3000, 6: 12000, 9: 24000, 12: 48000, 15: 48000}
        for index, frames in expected.items():
            with NodeSpy():
                effect = PingPongDelay(silence_src(512), sample_rate=RATE,
                                       transport=at_120, sync=True,
                                       division=index)
            self.assertEqual(read_frames(effect), float(frames), index)
        self.assertAlmostEqual(effect.get_macro(TIME_I), 127.0, places=6)
        # The static transport, and hosts whose tempo is not finite and
        # positive, leave Time on the knob.
        for transport in (None, lambda: (True, 0.0, 0.0, 4, 4),
                          lambda: (True, 0.0, float("nan"), 4, 4),
                          lambda: (True, 0.0, float("inf"), 4, 4)):
            with NodeSpy():
                effect = PingPongDelay(silence_src(512), sample_rate=RATE,
                                       transport=transport, sync=True)
            self.assertEqual(read_frames(effect), 13440.0)

    def test_sync_patches_follow_the_beat(self):
        def at_120():
            return (True, 0.0, 120.0, 4, 4)

        with NodeSpy():
            effect = PingPongDelay(silence_src(512), sample_rate=RATE,
                                   transport=at_120)
            effect.program_change(1)
            self.assertEqual(read_frames(effect), 12000.0)
            effect.program_change(2)
            self.assertEqual(read_frames(effect), 24000.0)
            effect.program_change(0)
            self.assertEqual(read_frames(effect), 13575.0)

    def test_spread_and_first_side_hand_the_pair(self):
        effect = spied()
        for k in range(11):
            effect.set_macro(SPREAD_I, 12.7 * k)
            s = handed(effect, "cross_feed")
            self.assertAlmostEqual(s, k / 10.0, places=12)
            self.assertEqual(handed(effect, "input_pan"), -s)
            effect.set_macro(SIDE_I, 127)
            self.assertEqual(handed(effect, "input_pan"), s)
            effect.set_macro(SIDE_I, 0)
        # Mono: inert, (0, 0) at every position and patch.
        mono = spied(channels=1)
        for index in (SPREAD_I, SIDE_I):
            for midi in (0, 64, 127):
                mono.set_macro(index, midi)
                self.assertEqual(read_cross_pan(mono), (0.0, 0.0))
        for patch in PingPongDelay.PATCHES:
            mono.program_change(patch)
            self.assertEqual(read_cross_pan(mono), (0.0, 0.0))

    def test_the_filter_stops(self):
        for rate in RATES:
            effect = spied(rate=rate)
            self.assertEqual(handed(effect, "damping_hz"), 0.0)
            self.assertEqual(handed(effect, "cut_hz"), 0.0)
            effect.set_macro(TONE_I, 126)
            corner = 800.0 * 20.0 ** (126 / 127.0)
            corner = min(corner, rate * 0.5 * 0.98)
            self.assertAlmostEqual(handed(effect, "damping_hz"),
                                   nominal_damping_hz(corner, rate),
                                   places=6)
            # Out after in is out: since audiodsp v0.6.3rc1 the node keeps
            # an out filter's state live (#158, #159), so both out stops
            # hand exactly 0 whatever came before, and the bound is finite.
            effect.set_macro(TONE_I, 127)
            self.assertEqual(handed(effect, "damping_hz"), 0.0)
            effect.set_macro(CUT_I, 1)
            self.assertGreater(handed(effect, "cut_hz"), 0.0)
            self.assertIsNone(effect.tail_samples)
            effect.set_macro(CUT_I, 0)
            self.assertEqual(handed(effect, "cut_hz"), 0.0)
            self.assertIsNotNone(effect.tail_samples)
            # Planted: the retired cures (Tone tracking at 32 x the rate,
            # Cut held in at the 20 Hz corner with no bound).
            for cls, name, want in (
                    (TrackingPingPong, "damping_hz", 32.0 * rate),
                    (HeldCutPingPong, "cut_hz",
                     pp.nominal_cut_hz(20.0, rate))):
                old = spied(cls, rate=rate)
                old.set_macro(TONE_I, 126)
                old.set_macro(TONE_I, 127)
                old.set_macro(CUT_I, 1)
                old.set_macro(CUT_I, 0)
                self.assertAlmostEqual(handed(old, name), want, places=9)

    def test_a_constructor_filter_out_again_is_out(self):
        # A constructor or patch filter, then a patch without it: both out
        # stops hand exactly 0 since audiodsp v0.6.3rc1 (up to v0.6.2 they
        # counted as having been in and handed the tracking stop and the
        # 20 Hz corner). Planted: the retired cures.
        for ctor in ({"tone_hz": 5000.0, "cut_hz": 100.0}, {"patch": 5}):
            effect = spied(**ctor)
            effect.program_change(0)
            self.assertEqual(handed(effect, "damping_hz"), 0.0, ctor)
            self.assertEqual(handed(effect, "cut_hz"), 0.0, ctor)
            old = spied(TrackingPingPong, **ctor)
            old.program_change(0)
            self.assertEqual(handed(old, "damping_hz"), 32.0 * RATE, ctor)
        old = spied(HeldCutPingPong, cut_hz=100.0)
        old.program_change(0)
        self.assertAlmostEqual(handed(old, "cut_hz"),
                               pp.nominal_cut_hz(20.0, RATE), places=9)

    def test_repeat_tone_clamps_at_22k(self):
        effect = spied(rate=22050)
        values = set()
        for midi in range(111, 127):
            effect.set_macro(TONE_I, midi)
            values.add(handed(effect, "damping_hz"))
        self.assertEqual(len(values), 1)
        effect.set_macro(TONE_I, 110)
        self.assertNotIn(handed(effect, "damping_hz"), values)

    def test_the_walk_bends_by_the_law_and_the_jump_does_not(self):
        for start, target in ((280.0, 200.0), (200.0, 280.0)):
            law = law_cents(start, target)
            got, walk = walk_cents(PingPongDelay, RATE, start, target)
            self.assertAlmostEqual(got, law, delta=1.5, msg=(start, target))
            self.assertEqual(walk, 20480)       # 427 ms at 48 kHz
            jumped, _ = walk_cents(NoSlewPingPong, RATE, start, target)
            self.assertLess(abs(jumped), 1.0, (start, target))

    def test_tail_samples_follows_time_feedback_and_tone(self):
        self.assertEqual(spied().tail_samples, 14 * 13441)
        self.assertEqual(spied(patch=0).tail_samples, 190064)
        self.assertEqual(spied(patch=5).tail_samples, 487944)
        self.assertEqual(spied(time_ms=1000.0, feedback=0.99).tail_samples,
                         685 * 48001)
        for patch in (3, 4, 6):
            self.assertEqual(spied(patch=patch).tail_samples, 190064)
        self.assertIsNone(spied(cut_hz=40.0).tail_samples)
        # Cut in, then out: since audiodsp v0.6.3rc1 the out stop is out
        # (the node holds an out high-pass at zero, #159), so the bound is
        # the one Cut never in has. Planted: the retired held 20 Hz corner.
        effect = spied(cut_hz=40.0)
        effect.set_macro(CUT_I, 0)
        self.assertEqual(handed(effect, "cut_hz"), 0.0)
        self.assertEqual(effect.tail_samples, 14 * 13441)
        held = HeldCutPingPong(silence_src(64), sample_rate=RATE,
                               cut_hz=40.0)
        held.set_macro(CUT_I, 0)
        self.assertIsNone(held.tail_samples)

    def test_the_feedback_is_handed_as_set(self):
        # Up to audiodsp v0.6.2 the class stepped the Feedback clear of the
        # loop low-pass's stall windows with Repeat Tone in (0.99 played as
        # 0.989976102). Since v0.6.3rc1 the node lands a stalled low-pass
        # (#157): with Tone in or out every Feedback position is handed as
        # set, and the bound is finite. Planted: the retired stepping.
        for rate in RATES:
            for tone in (0.0, 800.0, 16000.0):
                effect = spied(rate=rate, tone_hz=tone)
                for midi in range(128):
                    effect.set_macro(FEEDBACK_I, midi)
                    want = min(0.99, effect._value(FEEDBACK_I))
                    self.assertEqual(effect._feedback, want,
                                     (rate, tone, midi))
                    self.assertEqual(handed(effect, "feedback"), want)
                    self.assertIsNotNone(effect.tail_samples)
            stepped = SteppedPingPong(silence_src(64, rate=rate),
                                      sample_rate=rate, tone_hz=800.0,
                                      feedback=0.99)
            self.assertNotEqual(stepped._feedback, 0.99, rate)
            self.assertLess(abs(stepped._feedback - 0.99), 3e-5)

    def test_constructor_clamps_and_nan(self):
        nan = float("nan")
        effect = spied(time_ms=nan, feedback=nan, mix=nan, spread=nan,
                       division=nan, tone_hz=nan, cut_hz=nan)
        self.assertEqual(read_frames(effect), 13440.0)
        self.assertEqual(read_feedback(effect), 0.45)
        self.assertAlmostEqual(handed(effect, "mix"), 0.3)
        self.assertEqual(read_cross_pan(effect), (1.0, -1.0))
        self.assertEqual(handed(effect, "damping_hz"), 0.0)
        self.assertEqual(handed(effect, "cut_hz"), 0.0)
        effect = spied(time_ms=0.0, feedback=2.0, mix=-1.0, spread=3.0,
                       tone_hz=0.0, cut_hz=-5.0)
        self.assertEqual(read_frames(effect), 960.0)
        self.assertEqual(read_feedback(effect), 0.99)
        self.assertEqual(handed(effect, "mix"), 0.0)
        self.assertEqual(read_cross_pan(effect), (1.0, -1.0))
        self.assertEqual(handed(effect, "damping_hz"), 0.0)
        self.assertEqual(handed(effect, "cut_hz"), 0.0)
        self.assertEqual(read_frames(spied(time_ms=5000.0)), 48000.0)
        self.assertEqual(read_cross_pan(spied(first_side="Right")),
                         (1.0, 1.0))
        with self.assertRaises(ValueError):
            spied(first_side="middle")


# --------------------------------------------------------------------------
# The Tier 2 rows


class T1RepeatsAlternate(unittest.TestCase):
    def test_the_three_feedbacks_at_three_rates(self):
        for rate in RATES:
            for f in (0.6, 0.85, 0.99):
                result = t1_measure(PingPongDelay, rate, feedback=f)
                self.assertTrue(result["passed"], (rate, f, result))

    def test_the_time_stops_and_the_patch_cells(self):
        for options, macros in (({"time_ms": 20.0}, None),
                                ({"time_ms": 1000.0}, None),
                                ({}, {TIME_I: 63.5}),
                                ({}, {TIME_I: 86}),
                                ({}, {TIME_I: 99})):
            result = t1_measure(PingPongDelay, feedback=0.85,
                                macros=macros, **options)
            self.assertTrue(result["passed"], (options, macros, result))

    def test_the_lowest_claimed_feedback(self):
        for rate in RATES:
            result = t1_measure(PingPongDelay, rate, time_ms=20.0,
                                macros={FEEDBACK_I: 67})
            self.assertTrue(result["passed"], (rate, result))
            self.assertGreaterEqual(min(result["peaks"]), FLOOR)

    def test_repeat_cut_from_60_ms(self):
        for rate in RATES:
            for midi in (1, 32, 127):
                result = t1_measure(PingPongDelay, rate, time_ms=60.0,
                                    feedback=0.99, macros={CUT_I: midi})
                self.assertTrue(result["passed"], (rate, midi, result))

    def test_repeat_tone_in_keeps_the_exclusion_not_the_peak(self):
        result = t1_measure(PingPongDelay, feedback=0.6,
                            macros={TONE_I: 0}, peak_clause=False)
        self.assertEqual(result["leaks"], 0)
        self.assertEqual(result["swapped"], 0)
        # Named in advance: presence past repeat 3 and the peak position.
        self.assertEqual(result["weak"][0], 4)
        self.assertTrue(result["late"])

    def test_presence_is_not_claimed_with_a_loop_filter_in(self):
        # Fix round 1 (audit item 4): presence is claimed with both loop
        # filters out. At the Feedback floor with Cut at its 400 Hz stop a
        # repeat falls under 200 LSB, and the exclusion, the peak and the
        # swap still hold on the same render.
        weak = {48000: [8], 44100: [8], 22050: [7, 8]}
        for rate in RATES:
            result = t1_measure(PingPongDelay, rate, time_ms=280.0,
                                macros={FEEDBACK_I: 67, CUT_I: 127})
            self.assertEqual(result["weak"], weak[rate], rate)
            self.assertEqual(result["leaks"], 0, rate)
            self.assertEqual(result["late"], [], rate)
            self.assertEqual(result["swapped"], 0, rate)
            # Tone near its top loses repeat 8 at f 0.6.
            result = t1_measure(PingPongDelay, rate, feedback=0.6,
                                macros={TONE_I: 126}, peak_clause=False)
            self.assertEqual(result["weak"], [8], rate)
            self.assertEqual(result["leaks"], 0, rate)
            self.assertEqual(result["swapped"], 0, rate)

    def test_a_lossy_cross_is_red(self):
        for rate in RATES:
            result = t1_measure(LossyCrossPingPong, rate, feedback=0.6)
            self.assertFalse(result["passed"], rate)
            self.assertGreater(result["leaks"], 0)

    def test_a_late_read_is_red_on_the_peak(self):
        for rate in RATES:
            result = t1_measure(LateReadPingPong, rate, feedback=0.6)
            self.assertFalse(result["passed"], rate)
            self.assertEqual(result["leaks"], 0)
            self.assertEqual(result["offsets"][:4], [1, 2, 3, 4])


class T2OneDecayRatio(unittest.TestCase):
    def test_the_constructor_feedbacks_at_the_named_times(self):
        for rate in RATES:
            for f in (0.6, 0.85):
                for time_ms in (20.0, 280.0):
                    result = t2_measure(PingPongDelay, rate, feedback=f,
                                        time_ms=time_ms)
                    self.assertTrue(result["passed"],
                                    (rate, f, time_ms, result))

    def test_the_feedback_span_ends(self):
        for midi, fit in ((13, False), (28, True), (60, True), (127, True)):
            result = t2_measure(PingPongDelay, fit=fit,
                                feedback=law_feedback(midi))
            self.assertTrue(result["passed"], (midi, result))
        # Below MIDI 28 the other channel has one peak: the fit reads red.
        self.assertFalse(t2_measure(PingPongDelay,
                                    feedback=law_feedback(27))["passed"])

    def test_reading_down_one_channel_returns_f_squared(self):
        # The seeds' fault is the measurement's own: why the ratio is taken
        # across both channels.
        for f in (0.6, 0.85):
            result = t2_measure(PingPongDelay, feedback=f)
            self.assertAlmostEqual(result["down_one_channel"], f * f,
                                   delta=0.001)

    def test_a_scaled_feedback_is_red(self):
        for rate in RATES:
            for f in (0.6, 0.85):
                result = t2_measure(ScaledFeedbackPingPong, rate, feedback=f)
                self.assertFalse(result["passed"], (rate, f))
                self.assertGreater(result["worst"], 0.019)


class T3MonoSum(unittest.TestCase):
    def test_the_named_pairs_at_three_rates(self):
        for rate in RATES:
            for options in ({"feedback": 0.45}, {"feedback": 0.6},
                            {"feedback": 0.99},
                            {"time_ms": 20.0, "feedback": 0.85},
                            {"patch": 0}):
                result = t3_measure(PingPongDelay, rate, **options)
                self.assertTrue(result["passed"], (rate, options, result))

    def test_the_quiet_click_the_burst_and_first_side_right(self):
        for what in ("quiet", "burst"):
            result = t3_measure(PingPongDelay, what=what, feedback=0.85)
            self.assertTrue(result["passed"], (what, result))
        result = t3_measure(PingPongDelay, feedback=0.6, first_side="right")
        self.assertTrue(result["passed"], result)

    def test_spread_0_is_twice_the_reference(self):
        result = t3_measure(PingPongDelay, feedback=0.6, spread=0.0)
        self.assertTrue(result["passed"], result)

    def test_the_loop_filters_read_exact(self):
        damping = nominal_damping_hz(800.0, RATE)
        result = t3_measure(PingPongDelay, feedback=0.6, tone_hz=800.0,
                            damping=damping)
        self.assertTrue(result["passed"], result)
        cut = pp.nominal_cut_hz(400.0, RATE)
        result = t3_measure(PingPongDelay, feedback=0.6, cut_hz=400.0,
                            cut=cut)
        self.assertTrue(result["passed"], result)

    def _gap(self, k, peak, opts, damping=0.0, cut=0.0, macros=None):
        """The row's burst lengthened to end `k` frames before T (280 ms,
        f 0.6, 48 kHz), `macros` set after construction: (sum differing,
        max LSB, first differing frame, mono differing)."""
        T = law_frames(280.0, RATE)
        frames = 9 * T + int(0.1 * RATE)
        n = T - k
        x = np.zeros(frames)
        x[:n] = np.round(np.random.RandomState(12345)
                         .uniform(-peak, peak, n))
        stereo = render(PingPongDelay, x, RATE, 2, macros=macros,
                        time_ms=280.0, feedback=0.6, mix=2.0,
                        **opts).astype(np.int32)
        total = stereo[:, 0] + stereo[:, 1]
        mono = render(PingPongDelay, x, RATE, 1, macros=macros,
                      time_ms=280.0, feedback=0.6, mix=2.0,
                      **opts)[:, 0].astype(np.int32)
        ref = reference(x, RATE, T, 0.6, damping, cut)
        where = np.flatnonzero(total != ref)
        return (len(where), int(np.abs(total - ref).max()),
                int(where[0]) if len(where) else None,
                int(np.count_nonzero(mono != ref)))

    def test_the_filter_cells_need_material_ending_512_frames_before_t(self):
        # Fix round 1 (audit item 5): each lane's loop filter meets its
        # own lane's next repeat 2 T later, the reference's the very next,
        # so a burst ending close to T parts them. The filter cells are
        # claimed on material ending at least 512 frames before T.
        damping = nominal_damping_hz(800.0, RATE)
        self.assertEqual(self._gap(1, 8192, {"tone_hz": 800.0}, damping),
                         (295, 1, 2 * law_frames(280.0, RATE), 0))
        self.assertEqual(self._gap(1, 8192, {}), (0, 0, None, 0))
        cut = pp.nominal_cut_hz(400.0, RATE)
        for peak in (8192, 32767):
            self.assertEqual(self._gap(512, peak, {"cut_hz": 400.0},
                                       cut=cut)[0], 0, peak)
        # At 0 dBFS 256 frames is not enough for Cut 400 Hz.
        self.assertEqual(self._gap(256, 32767, {"cut_hz": 400.0},
                                   cut=cut)[0], 16)

    def test_the_gap_grows_as_repeat_cut_goes_down(self):
        # Fix round 2 (audit round 2, item 4): 512 frames is the three
        # named cells' gap, not any loop filter's. At Cut MIDI 1 (the knob
        # at 20 x 20^(1/127) Hz) and 0 dBFS a burst ending 4 096 frames
        # before T still differs in 511 samples, and 8 192 is exact; the
        # mono build is exact at both. The old "512 frames" is red there.
        cut = pp.nominal_cut_hz(20.0 * 20.0 ** (1.0 / 127.0), RATE)
        macros = {CUT_I: 1}
        at_512 = self._gap(512, 32767, {}, cut=cut, macros=macros)
        self.assertGreater(at_512[0], 0)
        self.assertEqual(at_512[3], 0)
        at_4096 = self._gap(4096, 32767, {}, cut=cut, macros=macros)
        self.assertEqual((at_4096[0], at_4096[3]), (511, 0))
        at_8192 = self._gap(8192, 32767, {}, cut=cut, macros=macros)
        self.assertEqual((at_8192[0], at_8192[3]), (0, 0))

    def _tone_in_then_out(self, cls, rate):
        """(samples differing, largest difference) between the channels'
        sum with Tone 5 kHz in then out and the mono reference at
        Feedback 0.99, on a click, Time 280 ms, Mix 2."""
        T = law_frames(280.0, rate)
        frames = 9 * T + int(0.1 * rate)
        x = click(frames)
        src, _ = to_source(x, 2, rate)
        effect = cls(src, sample_rate=rate, time_ms=280.0, feedback=0.99,
                     mix=2.0, tone_hz=5000.0)
        effect.set_macro(TONE_I, 127)
        stereo = pull(effect, frames).astype(np.int32)
        total = stereo[:, 0] + stereo[:, 1]
        ref = reference(x, rate, T, 0.99)
        return (int(np.count_nonzero(total != ref)),
                int(np.abs(total - ref).max()))

    def test_tone_in_then_out_is_inside_the_row(self):
        # Fix round 1 put this cell outside the row: the out stop after
        # Tone had been in handed a Feedback stepped clear of the stall
        # window (0.99 -> 0.989976102), 5 samples up to 5 LSB off. Since
        # audiodsp v0.6.3rc1 Tone out is out whatever came before, and the
        # cell reads exact at three rates. Planted: the retired tracking
        # stop with its stepping.
        for rate in RATES:
            self.assertEqual(self._tone_in_then_out(PingPongDelay, rate),
                             (0, 0), rate)
            self.assertEqual(self._tone_in_then_out(TrackingPingPong, rate),
                             (5, 5), rate)

    def test_the_mono_stereo_settings_are_red(self):
        for rate in RATES:
            result = t3_measure(MonoStereoSettingsPingPong, rate,
                                feedback=0.6)
            self.assertFalse(result["passed"], rate)
            self.assertEqual(result["sum_diff"], 0)
            self.assertLess(result["repeats"][0], result["repeats"][1])


class T4SpreadLaw(unittest.TestCase):
    def test_the_eleven_positions(self):
        for rate in RATES:
            for f in (0.3, 0.99):
                result = t4_measure(PingPongDelay, rate, feedback=f)
                self.assertTrue(result["passed"], (rate, f, result["red"]))
                self.assertLessEqual(result["worst"], 1.5)

    def test_the_short_time_and_the_quiet_click(self):
        result = t4_measure(PingPongDelay, time_ms=20.0, feedback=0.85)
        self.assertTrue(result["passed"], result["red"])
        result = t4_measure(PingPongDelay, level=328)
        self.assertTrue(result["passed"], result["red"])

    def test_first_side_right_is_the_swap_at_every_position(self):
        result = t4_measure(PingPongDelay, swap=True)
        self.assertTrue(result["passed"], result["red"])

    def test_the_law_misses_off_the_frame(self):
        # Fix round 1 (audit item 3): at the Times the node lands one
        # float32 step off the frame the two-tap read leaks each pass into
        # the frame beside it, and the law is not claimed there. MIDI 95
        # misses at 44.1 and 22.05 kHz; MIDI 86 and 127 hold.
        miss = {44100: 289.0, 22050: 145.0}
        for rate in (44100, 22050):
            result = t4_measure(PingPongDelay, rate, spreads=(1.0,),
                                time_ms=law_time_ms(95), feedback=0.99)
            self.assertFalse(result["passed"], rate)
            self.assertGreater(result["worst"], miss[rate], rate)
            for midi in (86, 127):
                result = t4_measure(PingPongDelay, rate, spreads=(1.0,),
                                    time_ms=law_time_ms(midi),
                                    feedback=0.99)
                self.assertTrue(result["passed"], (rate, midi))

    def test_a_constructor_time_off_the_frame_is_outside_the_law(self):
        # Fix round 2 (audit round 2, item 1): T4's exclusion is a
        # condition, any Time the node lands off the frame, not a list of
        # knob positions. A constructor or Sync Time reaches every whole
        # frame; at 44.1 kHz 750.0227 ms (n 33 076) is the worst band,
        # 1/256 of a frame off, where the old docstring said at most 1/512.
        rate = 44100
        f32 = np.float32
        for n, miss, readback, worst in ((33076, 2.0 ** -8, [19922, 78],
                                          575.31),
                                         (33077, 0.0, [20000, 0], 0.69)):
            time_ms = n * 1000.0 / rate
            effect = spied(rate=rate, time_ms=time_ms)
            self.assertEqual(read_frames(effect), float(n))
            ms = f32(handed(effect, "delay_ms"))
            landed = float((ms * f32(rate)) / f32(1000.0))
            self.assertEqual(abs(landed - n), miss, n)
            y = render(PingPongDelay, click(n + 8), rate=rate,
                       time_ms=time_ms, mix=2.0, feedback=0.0, spread=0.0)
            self.assertEqual([int(v) for v in y[n:n + 2, 0]], readback, n)
            result = t4_measure(PingPongDelay, rate, spreads=(0.0, 0.5, 1.0),
                                time_ms=time_ms, feedback=0.99)
            self.assertAlmostEqual(result["worst"], worst, 2)
            self.assertEqual(result["passed"], miss == 0.0, n)
        # The old bound, 1/512 of a frame, is red on n 33 076.
        effect = spied(rate=rate, time_ms=33076 * 1000.0 / rate)
        ms = f32(handed(effect, "delay_ms"))
        self.assertGreater(abs(float((ms * f32(rate)) / f32(1000.0))
                               - 33076), 2.0 ** -9)

    def test_the_panless_spread_is_red(self):
        for rate in RATES:
            result = t4_measure(PanlessPingPong, rate, spreads=(0.5, 1.0))
            self.assertFalse(result["passed"], rate)
            self.assertGreaterEqual(result["worst"], 19999.0)


class T5DryPath(unittest.TestCase):
    def test_the_defaults_stereo_and_mono(self):
        for rate in RATES:
            for channels in (2, 1):
                result = t5_measure(PingPongDelay, rate, channels)
                self.assertTrue(result["passed"], (rate, channels, result))

    def test_the_named_cells(self):
        cells = (
            ({"mix": 0.2}, None),
            ({"mix": 0.2, "spread": 0.5}, None),
            ({"mix": 0.2, "first_side": "right"}, None),
            ({"feedback": 0.99, "tone_hz": 800.0, "cut_hz": 400.0,
              "mix": 1.0}, None),
            ({"time_ms": 20.0}, None),
            ({}, {MIX_I: 63}),
        )
        for options, macros in cells:
            result = t5_measure(PingPongDelay, macros=macros, **options)
            self.assertTrue(result["passed"], (options, macros, result))
        for patch in PingPongDelay.PATCHES:
            result = t5_measure(PingPongDelay, patch=patch,
                                materials=("tones_step",))
            self.assertTrue(result["passed"], (patch, result))

    def test_mix_0_is_a_wire_without_presence(self):
        result = t5_measure(PingPongDelay, mix=0.0)
        self.assertTrue(result["passed"], result)

    def test_a_dry_gain_is_red(self):
        for rate in RATES:
            for channels in (2, 1):
                for options in ({}, {"mix": 0.2}):
                    result = t5_measure(DryGainPingPong, rate, channels,
                                        **options)
                    self.assertFalse(result["passed"],
                                     (rate, channels, options))
                    self.assertGreater(result["differing"], 0)

    def test_never_spread_on_independent_channels(self):
        # Fix round 1 (audit item 6): the kit's materials are
        # channel-identical, so a dry that is mono-summed or swapped reads
        # green on them. On independent L and R the window still reads 0,
        # and both faults read red.
        for rate in RATES:
            pcm = lr_material(rate)
            for options in ({}, {"mix": 0.2}, {"spread": 0.5},
                            {"first_side": "right"}):
                result = t5_measure(PingPongDelay, rate, pcm=pcm, **options)
                self.assertTrue(result["passed"], (rate, options, result))
            for cls in (MonoInPingPong, SwapInPingPong):
                for options in ({}, {"mix": 0.2}):
                    self.assertTrue(t5_measure(cls, rate, **options)
                                    ["passed"], (rate, cls, options))
                    result = t5_measure(cls, rate, pcm=pcm, **options)
                    self.assertFalse(result["passed"], (rate, cls, options))
                    self.assertGreater(result["differing"], 0)

    def test_an_antiphase_source_does_not_repeat_at_spread_1(self):
        # Disclosed, not a row: at Spread 1 the loop hears (L + R) / 2
        # (`input_pan` hard over), so R = -L puts nothing in the loop. The
        # defaults are a byte wire on it and Mix 2 is silence; at Spread
        # 0.5 it repeats.
        for rate in RATES:
            T = law_frames(280.0, rate)
            anti = antiphase_material(rate)
            y = render_pcm(PingPongDelay, anti, rate)
            self.assertEqual(int(np.count_nonzero(y != anti)), 0, rate)
            y = render_pcm(PingPongDelay, anti, rate, mix=2.0)
            self.assertEqual(int(np.count_nonzero(y[T:])), 0, rate)
            y = render_pcm(PingPongDelay, anti, rate, spread=0.5)
            self.assertGreater(int(np.count_nonzero(y[T:] != anti[T:])), 0,
                               rate)
            # Fix round 2 (audit round 2, item 5): where the source
            # saturates R cannot be -L (L is -32 768), so the full-scale
            # ramp leaves 1 LSB at Mix 2, not the silence the old sentence
            # said: the exact-zero assertion above is red on it.
            left = material("ramp_fs", rate, 1)[:, 0].astype(np.int32)
            sat = np.stack([left, np.clip(-left, -32768, 32767)],
                           axis=1).astype(np.int16)
            self.assertGreater(int(np.count_nonzero(left == -32768)), 0)
            y = render_pcm(PingPongDelay, sat, rate)
            self.assertEqual(int(np.count_nonzero(y != sat)), 0, rate)
            y = render_pcm(PingPongDelay, sat, rate, mix=2.0)
            self.assertEqual(int(np.abs(y[T:].astype(np.int32)).max()), 1,
                             rate)
            self.assertGreater(int(np.count_nonzero(y[T:])), 0, rate)


# --------------------------------------------------------------------------
# Tier 1


class Tier1Fast(unittest.TestCase):
    def test_mix_zero_is_a_wire_on_the_full_scale_ramp(self):
        for rate in RATES:
            for channels in (2, 1):
                ramp = probes.ramp_fs(frames=4 * 13440, channels=channels)
                src = np.array(ramp, dtype=np.int16).reshape(-1, channels)
                for options in ({"mix": 0.0},
                                {"mix": 0.0, "feedback": 0.99,
                                 "time_ms": 20.0, "tone_hz": 800.0}):
                    y = render_pcm(PingPongDelay, src, rate, **options)
                    self.assertEqual(int(np.count_nonzero(y != src)), 0,
                                     (rate, channels, options))

    def test_silence_stays_silence(self):
        for rate in RATES:
            y = render(PingPongDelay, np.zeros(rate), rate,
                       feedback=0.99, tone_hz=800.0, cut_hz=400.0)
            self.assertEqual(int(np.count_nonzero(y)), 0)

    def _round_trip(self, cls, index, first, back, rate, channels=2):
        """300 Hz at 30 000 LSB for 0.5 s with the filter in, the filter
        out as the input stops, 2 s of silence, the filter back in; the
        largest sample after the return (Wide Bounce's Time, Feedback 0,
        Mix 2)."""
        on = rate // 2
        frames = on + 2 * rate + rate // 2
        x = np.zeros(frames)
        x[:on] = 30000 * np.sin(2.0 * math.pi * 300.0 * np.arange(on)
                                / rate)
        source, _ = to_source(x, channels, rate)
        effect = cls(source, sample_rate=rate, feedback=0.0, mix=2.0)
        effect.set_macro(index, first)
        rest = (on // BLOCK + 1) * BLOCK
        back_at = rest + 2 * rate // BLOCK * BLOCK

        def on_block(frame):
            if frame == rest:
                effect.set_macro(index, 127 if index == TONE_I else 0)
            elif frame == back_at:
                effect.set_macro(index, back)

        y = pull(effect, frames, channels, on_block)
        return int(np.abs(y[back_at:].astype(np.int32)).max())

    def test_a_filter_back_in_after_silence_stays_silent(self):
        tone_2k = 127.0 * math.log(2000.0 / 800.0) / math.log(20.0)
        for rate in RATES:
            for channels in (2, 1):
                self.assertEqual(self._round_trip(
                    PingPongDelay, TONE_I, tone_2k, 0, rate, channels), 0)
                self.assertEqual(self._round_trip(
                    PingPongDelay, CUT_I, 127, 1, rate, channels), 0)
        # Planted: a filter whose state cannot move (left in at 0.001 Hz,
        # as the node's out stop behaved up to v0.6.2) plays it back.
        self.assertGreater(self._round_trip(
            FrozenFilterPingPong, TONE_I, tone_2k, 0, RATE), 10000)
        self.assertGreater(self._round_trip(
            FrozenFilterPingPong, CUT_I, 127, 1, RATE), 15000)

    def _tone_out_after_in(self, x, rate, cls=PingPongDelay, **options):
        """Largest |difference| between Tone out after Tone 2 kHz was in
        (on `cls`) and Tone never in, on `x`, Mix 2."""
        frames = len(x)
        source, _ = to_source(x, 2, rate)
        touched = cls(source, sample_rate=rate, mix=2.0, tone_hz=2000.0,
                      **options)
        touched.set_macro(TONE_I, 127)
        clean, _ = to_source(x, 2, rate)
        plain = PingPongDelay(clean, sample_rate=rate, mix=2.0, **options)
        a = pull(touched, frames).astype(np.int32)
        b = pull(plain, frames).astype(np.int32)
        return int(np.abs(a - b).max())

    def test_tone_out_after_tone_in_is_the_filter_out(self):
        # Up to audiodsp v0.6.2 the out stop after Tone had been in kept
        # the low-pass tracking the tap and the Feedback stepped clear of
        # the stall windows: 0 at 0.85, up to 6 LSB at 0.99 on 2 s of
        # 0 dBFS noise, and at Time 20 ms up to 19 LSB during the noise and
        # 37 through the tail. Since v0.6.3rc1 (#158, #157) it hands 0, and
        # every one of those cells renders the same bytes as Tone never in.
        # Planted: the retired tracking stop with its stepping (35 LSB
        # through the 20 ms tail on the fixed node; 37 on v0.6.2's).
        for rate in RATES:
            frames = 2 * rate
            x = np.frombuffer(probes.noise_det(frames=frames, dbfs=0.0,
                                               channels=1),
                              dtype=np.int16)[:frames].astype(float)
            for feedback in (0.85, 0.99):
                self.assertEqual(self._tone_out_after_in(
                    x, rate, feedback=feedback), 0, (rate, feedback))
            self.assertGreater(self._tone_out_after_in(
                x, rate, cls=TrackingPingPong, feedback=0.99), 1, rate)
        n = 2 * RATE
        probe = PingPongDelay(silence_src(64), sample_rate=RATE,
                              time_ms=20.0, feedback=0.99)
        frames = n + probe.tail_samples + law_frames(20.0, RATE)
        probe.deinit()
        x = np.zeros(frames)
        x[:n] = np.frombuffer(probes.noise_det(frames=n, dbfs=0.0,
                                               channels=1),
                              dtype=np.int16)[:n]
        for cls, worst in ((PingPongDelay, 0), (TrackingPingPong, 35)):
            source, _ = to_source(x, 2, RATE)
            touched = cls(source, sample_rate=RATE, mix=2.0, time_ms=20.0,
                          feedback=0.99, tone_hz=2000.0)
            touched.set_macro(TONE_I, 127)
            clean, _ = to_source(x, 2, RATE)
            plain = PingPongDelay(clean, sample_rate=RATE, mix=2.0,
                                  time_ms=20.0, feedback=0.99)
            d = np.abs(pull(touched, frames).astype(np.int32)
                       - pull(plain, frames).astype(np.int32)).max()
            self.assertEqual(int(d), worst, cls.__name__)

    def test_cut_out_after_cut_in_is_the_filter_out(self):
        # Up to audiodsp v0.6.2 Cut's bottom stop stayed in at 20 Hz once
        # Cut had been in. Since v0.6.3rc1 (#159) it hands 0, and 2 s of
        # 0 dBFS noise at Feedback 0.99 renders the same bytes as Cut never
        # in, at three rates. Planted: the retired held corner.
        for rate in RATES:
            frames = 2 * rate
            x = np.frombuffer(probes.noise_det(frames=frames, dbfs=0.0,
                                               channels=1),
                              dtype=np.int16)[:frames].astype(float)
            for cls, differs in ((PingPongDelay, False),
                                 (HeldCutPingPong, True)):
                source, _ = to_source(x, 2, rate)
                touched = cls(source, sample_rate=rate, mix=2.0,
                              feedback=0.99, cut_hz=400.0)
                touched.set_macro(CUT_I, 0)
                clean, _ = to_source(x, 2, rate)
                plain = PingPongDelay(clean, sample_rate=rate, mix=2.0,
                                      feedback=0.99)
                d = int(np.abs(pull(touched, frames).astype(np.int32)
                               - pull(plain, frames).astype(np.int32)).max())
                self.assertEqual(d > 0, differs, (rate, cls.__name__, d))

    def test_the_stall_cell_reaches_zero_at_the_feedback_set(self):
        # Feedback 0.5 with Repeat Tone 800 Hz in is a stall centre (k = 1):
        # up to audiodsp v0.6.2 the node could hold 1 LSB there for ever and
        # the class stepped the Feedback clear. Since v0.6.3rc1 (#157) 0.5
        # is handed as set, and a 2 LSB DC for 1 s ends inside the bound.
        for rate in RATES:
            frames = 4 * rate
            x = np.zeros(frames)
            x[:rate] = 2.0
            source, _ = to_source(x, 2, rate)
            effect = PingPongDelay(source, sample_rate=rate, feedback=0.5,
                                   mix=2.0, time_ms=100.0, tone_hz=800.0)
            self.assertEqual(effect._feedback, 0.5)
            declared = effect.tail_samples
            y = pull(effect, frames)
            nonzero = np.flatnonzero(y.any(axis=1))
            self.assertGreater(len(nonzero), 0, rate)
            last = int(nonzero[-1])
            self.assertLess(last, frames - 1, rate)
            self.assertLessEqual(last - rate + 1, declared, rate)
        stepped = SteppedPingPong(silence_src(64), sample_rate=RATE,
                                  feedback=0.5, tone_hz=800.0)
        self.assertNotEqual(stepped._feedback, 0.5)
        self.assertLess(abs(stepped._feedback - 0.5), 3e-5)

    def _in_then_out(self, cls, which, rate):
        """(samples differing, largest difference) from the fresh noise on:
        1 s of 0 dBFS noise with Tone 2 kHz or Cut 400 Hz really in, the
        filter out as the noise stops, silence past `tail_samples`, then
        1 s of fresh noise, against an instance whose filter was never in.
        Time 20 ms, Feedback 0.5 (a stall window centre), Mix 2."""
        loud = rate // BLOCK * BLOCK
        bound = PingPongDelay(silence_src(64, rate=rate), sample_rate=rate,
                              time_ms=20.0, feedback=0.5).tail_samples
        fresh = (loud + bound + rate // 4) // BLOCK * BLOCK
        frames = fresh + rate + bound + rate // 4
        x = np.zeros(frames)
        x[:loud] = np.random.RandomState(12345).uniform(-32767, 32767, loud)
        x[fresh:fresh + rate] = np.random.RandomState(777).uniform(
            -32767, 32767, rate)
        ctor = {"time_ms": 20.0, "feedback": 0.5, "mix": 2.0}
        filt = {"tone_hz": 2000.0} if which == TONE_I else {"cut_hz": 400.0}
        source, _ = to_source(x, 2, rate)
        touched = cls(source, sample_rate=rate, **dict(ctor, **filt))

        def move(frame):
            if frame == loud:
                touched.set_macro(which, 127 if which == TONE_I else 0)

        a = pull(touched, frames, 2, move).astype(np.int32)
        clean, _ = to_source(x, 2, rate)
        b = pull(PingPongDelay(clean, sample_rate=rate, **ctor),
                 frames).astype(np.int32)
        d = np.abs(a[fresh:] - b[fresh:])
        return int(np.count_nonzero(d)), int(d.max())

    def test_a_filter_really_in_then_out_is_out(self):
        # The out-stop tests above hand the out stop before any audio.
        # Here the filter plays 1 s of noise first: once those repeats have
        # died, the instance renders the same bytes as one whose filter was
        # never in, at three rates. Planted: the retired cures, the Tone
        # stop tracking with the Feedback stepped, and Cut held at 20 Hz.
        for rate in RATES:
            for which in (TONE_I, CUT_I):
                self.assertEqual(self._in_then_out(PingPongDelay, which,
                                                   rate), (0, 0),
                                 (rate, which))
            self.assertGreater(self._in_then_out(TrackingPingPong, TONE_I,
                                                 rate)[0], 0, rate)
            self.assertGreater(self._in_then_out(HeldCutPingPong, CUT_I,
                                                 rate)[0], 0, rate)

    def test_the_tail_after_cut_in_then_out_is_inside_the_bound(self):
        # Since audiodsp v0.6.3rc1 the bound is finite once Cut is out,
        # whatever came before. Full-scale noise with Cut in (400 Hz and
        # MIDI 1), Cut out as it stops: the tail ends inside the bound read
        # after the move. Planted: the retired held Cut (no bound) and the
        # bound one lap short.

        class OneLapShort(PingPongDelay):
            NAME = 'PingPongDelay'

            def _tail_bound(self):
                laps = pp.laps_to_zero(self._feedback, 0.0)
                return int((laps - 1) * (self._reach + 1))

        def cell(cls, cut_midi, feedback, spread):
            loud = RATE // 2 // BLOCK * BLOCK
            bound = PingPongDelay(silence_src(64), sample_rate=RATE,
                                  time_ms=20.0, feedback=feedback,
                                  spread=spread).tail_samples
            frames = loud + bound + RATE // 4
            x = np.zeros(frames)
            x[:loud] = np.random.RandomState(4242).uniform(-32767, 32767,
                                                           loud)
            source, _ = to_source(x, 2)
            effect = cls(source, sample_rate=RATE, time_ms=20.0,
                         feedback=feedback, spread=spread, mix=2.0)
            effect.set_macro(CUT_I, cut_midi)
            seen = {}

            def move(frame):
                if frame == loud:
                    effect.set_macro(CUT_I, 0)
                    seen["declared"] = effect.tail_samples

            y = pull(effect, frames, 2, move)
            last = int(np.flatnonzero(y.any(axis=1))[-1]) - loud + 1
            return seen["declared"], last

        for cut_midi in (127, 1):
            for feedback in (0.45, 0.85):
                for spread in (1.0, 0.0):
                    declared, tail = cell(PingPongDelay, cut_midi, feedback,
                                          spread)
                    self.assertIsNotNone(declared)
                    self.assertLessEqual(tail, declared,
                                         (cut_midi, feedback, spread))
                    self.assertGreater(tail, declared // 2)
        self.assertIsNone(cell(HeldCutPingPong, 127, 0.45, 1.0)[0])
        declared, tail = cell(OneLapShort, 127, 0.45, 1.0)
        self.assertGreater(tail, declared)

    def test_the_tail_reaches_exact_zero_inside_tail_samples(self):
        on = 200 * RATE // 1000
        for options in ({}, {"patch": 0}, {"patch": 4}, {"patch": 5},
                        {"patch": 6}):
            probe = PingPongDelay(silence_src(64), sample_rate=RATE,
                                  **options)
            bound = probe.tail_samples
            probe.deinit()
            frames = on + bound + 1024
            x = np.zeros(frames)
            x[:on] = 16384 * np.sin(2.0 * math.pi * 1000.0
                                    * np.arange(on) / RATE)
            y = render(PingPongDelay, x, **options)
            nonzero = np.flatnonzero(y.any(axis=1))
            last = int(nonzero[-1]) - on + 1 if len(nonzero) else 0
            self.assertLessEqual(last, bound, options)
            self.assertGreater(last, bound // 2, options)

    def test_a_full_scale_fill_at_every_spread(self):
        T = law_frames(20.0, RATE)
        fill = 4 * T
        for f in (0.45, 0.85):
            for spread in (1.0, 0.5, 0.0):
                for mix in (0.3, 2.0):
                    probe = PingPongDelay(silence_src(64), sample_rate=RATE,
                                          time_ms=20.0, feedback=f,
                                          spread=spread, mix=mix)
                    bound = probe.tail_samples
                    probe.deinit()
                    x = np.zeros(fill + bound + 1024)
                    x[:fill] = 32767
                    y = render(PingPongDelay, x, time_ms=20.0, feedback=f,
                               spread=spread, mix=mix)
                    last = int(np.flatnonzero(y.any(axis=1))[-1]) - fill + 1
                    self.assertLessEqual(last, bound, (f, spread, mix))

    def test_a_falling_walk_keeps_the_old_time_in_the_tail(self):
        effect = PingPongDelay(silence_src(512), sample_rate=RATE,
                               time_ms=1000.0)
        long_tail = effect.tail_samples
        effect.set_macro(TIME_I, 0)
        self.assertEqual(effect.tail_samples, long_tail)
        effect.reset()
        self.assertEqual(effect.tail_samples, 190064)

    def test_reset_silences_a_full_line(self):
        # A line full of repeats, reset, then silence in: silence out.
        frames = RATE
        x = np.concatenate([16384 * np.sin(2.0 * math.pi * 440.0
                                           * np.arange(frames) / RATE),
                            np.zeros(3 * frames)])
        source, _ = to_source(x, 2)
        effect = PingPongDelay(source, sample_rate=RATE, feedback=0.85)
        stop = (frames // BLOCK + 1) * BLOCK
        seen = []

        def on_block(frame):
            if frame == stop:
                effect.reset()
                seen.append(frame)

        y = pull(effect, 4 * frames, 2, on_block)
        self.assertEqual(seen, [stop])
        self.assertEqual(int(np.count_nonzero(y[stop:])), 0)

    def test_deinit_leaves_the_source(self):
        source, _ = to_source(8000 * np.sin(2 * math.pi * 440.0
                                            * np.arange(1024) / RATE))
        effect = PingPongDelay(source, sample_rate=RATE)
        pull(effect, 256)
        effect.deinit()
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(source)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)
        with self.assertRaises(RuntimeError):
            effect.tail_samples

    def test_click_delay_is_zero(self):
        for rate in (48000, 44100):
            y = render(PingPongDelay, click(2048), rate)
            self.assertEqual(int(np.argmax(np.abs(y[:, 0]))), 0)
            self.assertEqual(int(y[0, 0]), 20000)

    def test_the_transport_is_read_only_with_sync_on(self):
        calls = []

        def host():
            calls.append(1)
            return (True, 0.0, 120.0, 4, 4)

        effect = PingPongDelay(silence_src(512), sample_rate=RATE,
                               transport=host)
        self.assertEqual(calls, [])
        pull(effect, 4 * BLOCK)
        self.assertEqual(calls, [])
        effect.set_macro(SYNC_I, 127)
        self.assertEqual(len(calls), 1)
        pull(effect, 4 * BLOCK)
        self.assertEqual(len(calls), 1)


def railed_samples(cls, dbfs, seconds, values=None, **options):
    """Output samples on the int16 rail that the source did not put there:
    the kit's `noise_det` at `dbfs` peak (or `values`), 48 kHz stereo."""
    frames = int(seconds * RATE)
    if values is None:
        values = np.frombuffer(probes.noise_det(frames=frames, dbfs=dbfs,
                                                channels=1),
                               dtype=np.int16)[:frames].astype(float)
    x = np.round(values).astype(np.int32)
    y = render(cls, values, RATE, 2, **options).astype(np.int32)
    source = ((x >= 32767) | (x <= -32768))[:, None]
    out = (y >= 32767) | (y <= -32768)
    return int(np.count_nonzero(out & ~source))


class InputCeiling(unittest.TestCase):
    """Fix round 1 (audit-3 ruling (o)): the docstring's ceiling on
    `noise_det`, 48 kHz stereo, over 20 s. The defaults are clean at
    -3 dBFS peak and patch 4 (Spread 0, the first shipped patch to rail)
    at -3.1; each is red 1 dB over."""

    SECONDS = 20.0

    def test_the_stated_ceiling_is_clean_and_1_db_over_is_not(self):
        for options, ceiling in (({}, -3.0), ({"patch": 4}, -3.1)):
            self.assertEqual(railed_samples(PingPongDelay, ceiling,
                                            self.SECONDS, **options), 0,
                             options)
            self.assertGreater(railed_samples(PingPongDelay, ceiling + 1.0,
                                              self.SECONDS, **options), 0,
                               options)

    def test_the_any_material_bound(self):
        # With Repeat Cut out, a DC one LSB under floor(32767 (1 - Mix))
        # never reaches the rail at Feedback 0.99, at any Spread; at
        # floor(32767 (1 - Mix)) itself the sum can round onto 32767.
        for mix in (0.5, 0.3):
            edge = int(math.floor(32767 * (1.0 - mix)))
            for spread in (1.0, 0.0):
                for level, reaches in ((edge - 1, False),
                                       (edge, mix == 0.5)):
                    y = render(PingPongDelay, [level] * (RATE // 2), RATE, 2,
                               time_ms=12.5, feedback=0.99, mix=mix,
                               spread=spread)
                    self.assertEqual(bool(np.any(y >= 32767)), reaches,
                                     (mix, spread, level))

    def test_repeat_cut_needs_more_room(self):
        # The loop high-pass overshoots a square's edges: at the defaults'
        # Mix a 40 Hz square wave rails at -3.1 dBFS with Cut in, and not
        # with Cut out.
        t = np.arange(int(4 * RATE)) / RATE
        wave_ = np.sign(np.sin(2.0 * math.pi * 40.0 * t + 1e-9))
        loud = 32767.0 * 10.0 ** (-3.1 / 20.0) * wave_
        for cut_hz in (40.0, 400.0):
            self.assertGreater(railed_samples(PingPongDelay, None, 4.0,
                                              values=loud, cut_hz=cut_hz), 0,
                               cut_hz)
        self.assertEqual(railed_samples(PingPongDelay, None, 4.0,
                                        values=loud), 0)

    def test_the_cut_in_ceiling(self):
        # Fix round 2 (audit round 2, item 2): "clean from -4 dBFS" was the
        # 40 Hz square at the defaults only. The worst cell tried, a 5 Hz
        # square with Cut at 40 Hz at Feedback 0.99, is clean at the stated
        # -5.5 dBFS and rails 1 dB over; at -4 dBFS it rails, so the old
        # sentence is red on it. Under the arithmetic bound,
        # floor(32767 - 65535 Mix) - 1 = 13 105 LSB at Mix 0.3, it and the
        # defaults' 5 Hz square at Cut MIDI 1 are clean.
        t = np.arange(int(4 * RATE)) / RATE
        wave_ = np.sign(np.sin(2.0 * math.pi * 5.0 * t + 1e-9))

        def railed(dbfs=None, peak=None, macros=None, **options):
            level = peak if peak is not None else 32767.0 * 10.0 ** (
                dbfs / 20.0)
            values = level * wave_
            x = np.round(values).astype(np.int32)
            y = render(PingPongDelay, values, RATE, 2, macros=macros,
                       **options).astype(np.int32)
            source = ((x >= 32767) | (x <= -32768))[:, None]
            return int(np.count_nonzero(((y >= 32767) | (y <= -32768))
                                        & ~source))

        corner = {"cut_hz": 40.0, "feedback": 0.99}
        self.assertEqual(railed(-5.5, **corner), 0)
        self.assertGreater(railed(-4.5, **corner), 0)
        self.assertGreater(railed(-4.0, **corner), 0)
        edge = int(math.floor(32767 - 65535 * 0.3)) - 1
        self.assertEqual(edge, 13105)
        self.assertEqual(railed(peak=edge, **corner), 0)
        self.assertEqual(railed(peak=edge, macros={CUT_I: 1}), 0)
        self.assertGreater(railed(-4.0, macros={CUT_I: 1}), 0)
        self.assertEqual(railed(-4.5, macros={CUT_I: 1}), 0)


# --------------------------------------------------------------------------
# The gate's two checks on every fault


class FaultsAreUnreachable(unittest.TestCase):
    """Every fault's reachability walk, reading only what the node is
    handed (or, for the dry gain, a copy's dry path), at 48, 44.1 and
    22.05 kHz on the kit's grid (17 positions per macro) plus the seven
    patches, and the handed-value walks on the fine grid (509) too."""

    CHECKED = 9 * 17 + 7
    CHECKED_FINE = 9 * len(FINE) + 7

    def test_every_fault_is_off_the_surface(self):
        for name, faulted, reading, channels in REACH_WALKS:
            for rate in RATES:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, channels)
                    self.assertEqual(result["checked"], self.CHECKED)

    def test_every_fault_is_off_the_fine_grid(self):
        for name, faulted, reading, channels in REACH_WALKS:
            for rate in RATES:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, channels,
                                   grid=FINE)
                    self.assertEqual(result["checked"], self.CHECKED_FINE)

    def test_the_dry_gain_is_off_the_surface(self):
        for rate in RATES:
            for channels in (2, 1):
                result = reach(DryGainPingPong, read_dry_gain, rate,
                               channels)
                self.assertEqual(result["checked"], self.CHECKED)

    def test_the_spread_dry_is_off_the_surface(self):
        # Fix round 1: T5's "never spread" faults, read as the right input
        # reaching the left output before the first repeat.
        for cls in (MonoInPingPong, SwapInPingPong):
            for rate in RATES:
                with self.subTest(fault=cls.__name__, rate=rate):
                    result = reach(cls, read_dry_crosstalk, rate)
                    self.assertEqual(result["checked"], self.CHECKED)
                    self.assertEqual(result["clean"], 0)


class NullBuildRed(unittest.TestCase):
    """Every demonstrated row goes red on the class built as a wire, beside
    a control on the real class that must pass."""

    def test_every_row_is_red_on_a_wire(self):
        for name, measure in (("T1", t1_default), ("T2", t2_default),
                              ("T3", t3_default), ("T4", t4_default),
                              ("T5", t5_default),
                              ("T5 independent L/R", t5_lr_default)):
            with self.subTest(row=name):
                result = kit_faults.null_build_red(
                    PingPongDelay, measure, label="PingPongDelay %s" % name)
                self.assertFalse(result["null"]["passed"], name)
                self.assertTrue(result["control"]["passed"], name)



# --------------------------------------------------------------------------
# The trial of the second process: the tests the docstring's claims and the
# re-audit's restatements needed that the rows above did not already give


class HeldFloorPingPong(PingPongDelay):
    """The pre-v0.6.3rc3 cross-feed stall (audiodsp#170), planted on the
    output: once a channel has read `held` LSB it never reads less, so the
    tail sits on a DC of `held` for ever."""

    NAME = 'PingPongDelay'
    held = 1

    def _build(self, *arguments, **options):
        PingPongDelay._build(self, *arguments, **options)
        self._output = _HoldFloor(self._delay, type(self).held)


class _HoldFloor(kit_faults._Node):
    def __init__(self, source, held):
        kit_faults._Node.__init__(self, source)
        self.held = held
        self._sign = [0] * source.channel_count

    def _process(self, frames):
        ch = self.channel_count
        x = frames.reshape(-1, ch).copy()
        for c in range(ch):
            col = x[:, c]
            if not self._sign[c]:
                hit = np.flatnonzero(np.abs(col) == self.held)
                if len(hit):
                    self._sign[c] = 1 if col[hit[0]] > 0 else -1
                    tail = col[hit[0]:]
                    low = np.abs(tail) < self.held
                    tail[low] = self._sign[c] * self.held
                continue
            low = np.abs(col) < self.held
            col[low] = self._sign[c] * self.held
        return x.reshape(-1)


def _midtail(ctor, moves, at=2048, rate=RATE):
    """A full-scale DC burst of 50 ms in both channels at Mix 2, then
    silence; `moves` made `at` frames into the silence. Returns
    (`tail_samples` read as the input stops, `tail_samples` read just after
    the moves, frames from the moves to the output's last non-zero frame).
    The render runs to the larger of the two bounds plus a second."""
    burst = int(0.05 * rate) // BLOCK * BLOCK
    move = burst + at
    options = dict(ctor, mix=2.0)
    probe = PingPongDelay(silence_src(64, rate=rate), sample_rate=rate,
                          **options)
    for index, value in moves:
        probe.set_macro(index, value)
    longest = max(probe.tail_samples, 13454) + rate
    probe.deinit()
    frames = move + longest + BLOCK
    values = np.zeros(frames)
    values[:burst] = 32767
    source, _ = to_source(values, 2, rate)
    effect = PingPongDelay(source, sample_rate=rate, **options)
    seen = {}

    def on_block(frame):
        if frame == burst:
            seen["before"] = effect.tail_samples
        if frame == move:
            for index, value in moves:
                effect.set_macro(index, value)
            seen["after"] = effect.tail_samples

    y = pull(effect, frames, 2, on_block)
    effect.deinit()
    nonzero = np.flatnonzero(y[move:].any(axis=1))
    last = int(nonzero[-1]) + 1 if len(nonzero) else 0
    return seen["before"], seen["after"], last


class TrialClaims(unittest.TestCase):
    def test_the_knob_spans(self):
        effect = PingPongDelay(silence_src(64), sample_rate=RATE)
        for index, low, high in ((TIME_I, 20.0, 1000.0),
                                 (FEEDBACK_I, 0.0, 0.99),
                                 (MIX_I, 0.0, 2.0), (SPREAD_I, 0.0, 1.0)):
            effect.set_macro(index, 0)
            self.assertAlmostEqual(effect._value(index), low, places=9)
            effect.set_macro(index, 127)
            self.assertAlmostEqual(effect._value(index), high, places=9)
        effect.set_macro(FEEDBACK_I, 127)
        self.assertEqual(effect._feedback, 0.99)
        effect.set_macro(FEEDBACK_I, 0)
        self.assertEqual(effect._feedback, 0.0)

    def test_mix_2_is_the_repeats_alone(self):
        # A click at Mix 2: nothing until the repeat, Time later.
        T = law_frames(100.0, RATE)
        y = render(PingPongDelay, click(2 * T), mix=2.0, time_ms=100.0,
                   feedback=0.0)
        self.assertEqual(int(np.count_nonzero(y[:T])), 0)
        self.assertEqual(int(y[T, 0]), 20000)

    HZ = 997.0
    LEVEL = 8000.0

    def _bar(self):
        """1.5 x the tone's own largest step."""
        t = np.arange(4096) / RATE
        x = np.round(self.LEVEL * np.sin(2.0 * math.pi * self.HZ * t))
        return 1.5 * float(np.max(np.abs(np.diff(x))))

    def _mix_moves(self, steps):
        """The tone at Time 987 frames (the repeat half a cycle off the
        dry), Feedback 0, Mix from MIDI 0 to 127 in `steps` equal moves, one
        a block from frame 20 480; the largest step in the output from
        there."""
        frames = 20480 + (steps + 8) * BLOCK
        t = np.arange(frames) / RATE
        values = self.LEVEL * np.sin(2.0 * math.pi * self.HZ * t)
        source, _ = to_source(values)
        effect = PingPongDelay(source, sample_rate=RATE,
                               time_ms=987 * 1000.0 / RATE, feedback=0.0,
                               mix=0.0)

        def move(frame):
            k = (frame - 20480) // BLOCK + 1
            if frame >= 20480 and k <= steps:
                effect.set_macro(MIX_I, 127.0 * k / steps)

        y = pull(effect, frames, 2, move)[:, 0].astype(np.int32)
        effect.deinit()
        return float(np.max(np.abs(np.diff(y[20479:]))))

    def test_a_jump_steps_and_small_steps_do_not(self):
        # The family limit (audiocomponents#117), the matrix's E4-m2=127
        # P5 cells: Mix 0 -> 2 in one move steps the output; the same move
        # in 127 steps from the host, one a block, stays under the bar.
        self.assertGreater(self._mix_moves(1), 4.0 * self._bar())
        self.assertLess(self._mix_moves(127), self._bar())

    def _tail_across_a_stop(self, stop):
        """A 50 ms tone burst into Time 100 ms, Feedback 0.5, Mix 2, then
        silence; after 24 pulls the source hands empty buffers for `stop`
        pulls, then silence again. Returns (the bytes handed while it was
        stopped, the 40 blocks pulled after it came back)."""
        import lifecycle
        tone = np.round(self.LEVEL * np.sin(
            2.0 * math.pi * self.HZ * np.arange(2400) / RATE)).astype(int)
        burst = array("h")
        for v in tone:
            burst.extend((int(v), int(v)))
        feed = lifecycle.Feed(burst, RATE, 2, "256", False)
        effect = PingPongDelay(feed.port, sample_rate=RATE, time_ms=100.0,
                               feedback=0.5, mix=2.0)
        for _ in range(24):
            audiocore.get_buffer(effect.output)
        feed.point(feed.empty)
        stopped = bytearray()
        for _ in range(stop):
            stopped.extend(bytes(audiocore.get_buffer(effect.output)[1]))
        feed.point(feed.sil)
        after = bytearray()
        while len(after) < 40 * BLOCK * 4:
            after.extend(bytes(audiocore.get_buffer(effect.output)[1]))
        effect.deinit()
        return bytes(stopped), bytes(after[:40 * BLOCK * 4])

    def test_the_tail_waits_for_the_source(self):
        # The family limit (audiodsp#180): a source that hands empty
        # buffers stops the tail; when it feeds again the tail carries on
        # where it was, as if the stop had not happened.
        stopped, after = self._tail_across_a_stop(30)
        self.assertEqual(stopped.strip(b"\x00"), b"")
        self.assertGreater(max(abs(v) for v in array("h", after)), 1000)
        self.assertEqual(after, self._tail_across_a_stop(0)[1])

    def test_tail_samples_holds_for_the_settings_as_they_stand(self):
        # Re-audit 1's first restatement: the bound counts from when it is
        # read, for the settings as they stand. Each row moves a setting
        # 2 048 frames into the silence and reads `tail_samples` after it:
        # the output is exact zero within that many frames of the move.
        rows = (({"time_ms": 20.0}, [(FEEDBACK_I, 127)]),
                ({"time_ms": 20.0, "feedback": 0.99}, [(FEEDBACK_I, 0)]),
                ({"time_ms": 20.0, "feedback": 0.99}, [(FEEDBACK_I, 64)]),
                ({"time_ms": 20.0, "feedback": 0.85}, [(TIME_I, 30)]),
                ({"time_ms": 60.0, "feedback": 0.85}, [(TIME_I, 0)]),
                ({"time_ms": 20.0, "feedback": 0.85}, [(TONE_I, 0)]),
                ({"time_ms": 20.0, "feedback": 0.85, "tone_hz": 800.0},
                 [(TONE_I, 127)]),
                ({"time_ms": 20.0, "feedback": 0.85}, [(SPREAD_I, 39)]),
                ({"time_ms": 20.0, "feedback": 0.85, "cut_hz": 400.0},
                 [(CUT_I, 0)]))
        for ctor, moves in rows:
            before, after, last = _midtail(ctor, moves)
            self.assertGreater(last, 0, (ctor, moves))
            self.assertIsNotNone(after, (ctor, moves))
            self.assertLessEqual(last, after, (ctor, moves, before, after))
        # The value read before a Feedback move up does not hold after it.
        before, after, last = _midtail({"time_ms": 20.0},
                                       [(FEEDBACK_I, 127)])
        self.assertGreater(last, before)
        self.assertGreater(after, before)

    #: (typed feedback, Spread, k): where the pre-rc3 node's float32
    #: cross-feed sum handed k back on both lanes for ever (audiodsp#170).
    #: The first is the re-audit's typed cell; the rest are the cells the
    #: fixer's probe (`trial/PingPongDelay/stall_probe.py` in the workspace)
    #: finds held under every order of the sum, one per Feedback. No
    #: Feedback knob position is among them.
    CROSS_FEED_CELLS = ((0.9899999, 39.0 / 127.0, 50),
                        (0.9899999, 2.0 / 127.0, 50),
                        (0.9666666, 37.0 / 127.0, 15),
                        (0.9827586, 38.0 / 127.0, 29),
                        (0.9833333, 43.0 / 127.0, 30),
                        (0.9838709, 42.0 / 127.0, 31))

    def _cross_feed_tail(self, cls, feedback, spread, k):
        """Stereo, 48 kHz, Time 20 ms, Mix 2: a DC of 2k + 2 LSB in both
        channels for four laps, then silence to `tail_samples` plus a lap.
        Returns (declared, the last non-zero frame after the fill, the
        largest |sample| past `tail_samples`)."""
        options = {"time_ms": 20.0, "feedback": feedback, "mix": 2.0,
                   "spread": spread}
        probe = PingPongDelay(silence_src(64), sample_rate=RATE, **options)
        declared = probe.tail_samples
        probe.deinit()
        fill = 4 * 960 // BLOCK * BLOCK + BLOCK
        values = [2 * k + 2] * fill + [0] * (declared + 960 + BLOCK)
        source, _ = to_source(values)
        cls.held = k
        effect = cls(source, sample_rate=RATE, **options)
        out = pull(effect, len(values), 2).astype(np.int64)
        effect.deinit()
        after = out[fill:]
        nonzero = np.flatnonzero(after.any(axis=1))
        last = 0 if nonzero.size == 0 else int(nonzero[-1]) + 1
        return declared, last, int(np.max(np.abs(after[declared:])))

    def test_the_cross_feed_stall_cells_reach_zero(self):
        # Re-audit 1's third item: this class hands Spread as `cross_feed`,
        # and up to audiodsp v0.6.3rc2 these typed cells held k LSB on both
        # lanes for ever. At v0.6.3rc3 the node ends them (#170): the tail
        # is exact zero inside `tail_samples`. Planted: a tail that holds a
        # DC of k once it gets there, red at every cell.
        for feedback, spread, k in self.CROSS_FEED_CELLS:
            key = (feedback, spread)
            effect = PingPongDelay(silence_src(64), sample_rate=RATE,
                                   feedback=feedback, spread=spread)
            self.assertEqual(float(np.float32(effect._feedback)),
                             float(np.float32(feedback)), key)
            effect.deinit()
            declared, last, past = self._cross_feed_tail(
                PingPongDelay, feedback, spread, k)
            self.assertGreater(last, 0, key)
            self.assertLessEqual(last, declared, key)
            self.assertEqual(past, 0, key)
            declared, last, past = self._cross_feed_tail(
                HeldFloorPingPong, feedback, spread, k)
            self.assertGreater(last, declared, key)
            self.assertEqual(past, k, key)

    def test_reset_returns_to_patch_0(self):
        effect = PingPongDelay(silence_src(512), sample_rate=RATE, patch=5)
        effect.set_macro(SPREAD_I, 10)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        for index, midi in enumerate(PingPongDelay.PATCHES[0][1]):
            self.assertAlmostEqual(effect.get_macro(index), midi, delta=0.6)

    def test_construction_needs_audioecho(self):
        saved = sys.modules.get("audioecho", False)
        saved_attr = pp.audioecho
        sys.modules["audioecho"] = None
        pp.audioecho = None
        try:
            with self.assertRaises(ImportError):
                PingPongDelay(silence_src(512), sample_rate=RATE)
        finally:
            pp.audioecho = saved_attr
            if saved is False:
                del sys.modules["audioecho"]
            else:
                sys.modules["audioecho"] = saved


# --------------------------------------------------------------------------
# The docstring's claims

#: Every claim the class docstring makes, word for word, and the tests that
#: assert it ("Class.test_name", in this file).
CLAIMS = (
    ("Two delay lines crossed into each other: the repeats bounce between "
     "the speakers.",
     ("T1RepeatsAlternate.test_the_three_feedbacks_at_three_rates",)),
    ("Your dry signal passes untouched on both sides, and the repeats come "
     "back one side and then the other, all the way down.",
     ("T5DryPath.test_the_defaults_stereo_and_mono",
      "T1RepeatsAlternate.test_the_three_feedbacks_at_three_rates")),
    ("The first repeat comes back Time later on the side First Side names, "
     "the next Time after that on the other side, and they keep bouncing, "
     "each a Feedback's worth quieter than the last.",
     ("T1RepeatsAlternate.test_the_three_feedbacks_at_three_rates",
      "T1RepeatsAlternate.test_the_time_stops_and_the_patch_cells",
      "T2OneDecayRatio.test_the_constructor_feedbacks_at_the_named_times",
      "T4SpreadLaw.test_first_side_right_is_the_swap_at_every_position")),
    ("Time runs from 20 to 1000 ms and Feedback from 0 to 0.99.",
     ("TrialClaims.test_the_knob_spans",
      "TheSurface.test_time_lands_on_a_whole_frame")),
    ("Mix is the echo level: the dry stays at unity up to Mix 1, Mix 2 is "
     "the repeats alone, and at Mix 0 the output is the input.",
     ("T5DryPath.test_the_named_cells",
      "TrialClaims.test_mix_2_is_the_repeats_alone",
      "Tier1Fast.test_mix_zero_is_a_wire_on_the_full_scale_ramp")),
    ("Spread moves between two plain delays with the same repeats on both "
     "sides, at 0, and the full bounce, at 1.",
     ("T4SpreadLaw.test_the_eleven_positions",
      "T3MonoSum.test_spread_0_is_twice_the_reference")),
    ("At Spread 1 each repeat is on one side only, and the other side is "
     "exact zero.",
     ("T1RepeatsAlternate.test_the_three_feedbacks_at_three_rates",)),
    ("With Sync on, Time is Division of the host's beat, up to 1000 ms; "
     "with no host tempo, Time stays where the knob is.",
     ("TheSurface.test_sync_quantises_time_and_clamps",)),
    ("The class reads the host's transport only while Sync is on, and then "
     "only when a control moves or a patch loads, never while it plays.",
     ("Tier1Fast.test_the_transport_is_read_only_with_sync_on",
      "TheSurface.test_sync_patches_follow_the_beat")),
    ("Repeat Tone is a low-pass and Repeat Cut a high-pass inside the "
     "loop, so each bounce is a little darker or thinner than the last.",
     ("T3MonoSum.test_the_loop_filters_read_exact",)),
    ("Repeat Tone's top stop and Repeat Cut's bottom stop take them out, "
     "and a filter taken out is out.",
     ("TheSurface.test_the_filter_stops",
      "Tier1Fast.test_a_filter_really_in_then_out_is_out")),
    ("At 22.05 kHz the top positions of Repeat Tone sit on one clamp below "
     "Nyquist and sound the same.",
     ("TheSurface.test_repeat_tone_clamps_at_22k",)),
    ("Turning Time walks the repeats to the new Time, bending their pitch, "
     "instead of clicking.",
     ("TheSurface.test_the_walk_bends_by_the_law_and_the_jump_does_not",)),
    ("At Spread 1 the loop hears the average of the two input channels, so "
     "what differs between them never repeats.",
     ("T5DryPath.test_an_antiphase_source_does_not_repeat_at_spread_1",)),
    ("The dry is always each channel's own signal, never swapped or "
     "summed.",
     ("T5DryPath.test_never_spread_on_independent_channels",)),
    ("A one-channel source gets an ordinary feedback delay at the same "
     "Time, Feedback and Mix, and Spread and First Side do nothing there.",
     ("T3MonoSum.test_the_named_pairs_at_three_rates",
      "TheSurface.test_spread_and_first_side_hand_the_pair")),
    ("At 48 kHz every Time position lands on the nearest whole frame.",
     ("TheSurface.test_where_the_node_lands_the_handed_frame",)),
    ("At 44.1 and 22.05 kHz the node lands some positions a fraction of a "
     "frame off, and a sliver of each repeat falls on the frame beside it.",
     ("TheSurface.test_where_the_node_lands_the_handed_frame",
      "TheSurface.test_an_off_frame_time_leaks_into_the_next_frame")),
    ("The dry sits at unity and the repeats add to it, so a hot input can "
     "reach the int16 rail.",
     ("InputCeiling.test_the_stated_ceiling_is_clean_and_1_db_over_is_not",)),
    ("With Repeat Cut out and Mix below 1, an input that peaks at or below "
     "floor(32767 (1 - Mix)) - 1 cannot reach the rail, at any Time, "
     "Feedback or Spread.",
     ("InputCeiling.test_the_any_material_bound",)),
    ("Repeat Cut's high-pass overshoots, so with it in leave more room.",
     ("InputCeiling.test_repeat_cut_needs_more_room",
      "InputCeiling.test_the_cut_in_ceiling")),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     ("TrialClaims.test_a_jump_steps_and_small_steps_do_not",)),
    ("The tail rings only while the source keeps feeding: feed silence to "
     "let it ring out.",
     ("TrialClaims.test_the_tail_waits_for_the_source",)),
    ("A tail cut short by a source that stopped carries on when the source "
     "comes back.",
     ("TrialClaims.test_the_tail_waits_for_the_source",)),
    ("A click comes out on the frame it went in: there is no latency.",
     ("Tier1Fast.test_click_delay_is_zero",
      "TheSurface.test_macros_patches_tier_latency")),
    ("`tail_samples` is an upper bound on how many frames the output takes "
     "to reach exact zero, counted from when your input stops or from when "
     "you read it if that is later, for the settings as they stand when "
     "you read it.",
     ("TrialClaims.test_tail_samples_holds_for_the_settings_as_they_stand",
      "TrialClaims.test_the_cross_feed_stall_cells_reach_zero",
      "Tier1Fast.test_the_tail_reaches_exact_zero_inside_tail_samples",
      "Tier1Fast.test_a_full_scale_fill_at_every_spread",
      "Tier1Fast.test_the_stall_cell_reaches_zero_at_the_feedback_set",
      "Tier1Fast.test_the_tail_after_cut_in_then_out_is_inside_the_bound",
      "Tier1Fast.test_a_falling_walk_keeps_the_old_time_in_the_tail")),
    ("With Repeat Cut in circuit `tail_samples` is `None`: the class gives "
     "no bound there.",
     ("TheSurface.test_tail_samples_follows_time_feedback_and_tone",
      "TheSurface.test_the_filter_stops")),
    ("Pass a lower `max_time_ms` for a shorter line: Time then stops at "
     "that ceiling, and `get_macro(0)` shows where it stopped.",
     ("TheSurface.test_a_lowered_ceiling_clamps_visibly",)),
    ("A constructor value outside a knob's span clamps to the nearer stop, "
     "a `tone_hz` or `cut_hz` of 0 or less is that filter out, and NaN "
     "takes the option's default.",
     ("TheSurface.test_constructor_clamps_and_nan",)),
    ("`reset()` empties the line and returns to patch 0.",
     ("Tier1Fast.test_reset_silences_a_full_line",
      "TrialClaims.test_reset_returns_to_patch_0")),
    ("The class needs audiodsp's `audioecho`, and on a board without it "
     "construction raises `ImportError`.",
     ("TrialClaims.test_construction_needs_audioecho",)),
)

FAMILY_HEADING = "**Limits shared by the family.**"


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
    for word in rest.split():
        if any(c.isdigit() for c in word):
            problems.append("figure outside a claim: %s" % word)
    return problems


class Claims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        self.assertEqual(claim_problems(PingPongDelay.__doc__), [])
        self.assertEqual(claim_problems(pp.__doc__, ()), [])
        self.assertIn(FAMILY_HEADING, _flat(PingPongDelay.__doc__))
        # The checker can fail: a figure outside a claim, a claim the
        # docstring does not carry, a test that does not exist.
        self.assertTrue(claim_problems(PingPongDelay.__doc__
                                       + " It reads 12 ms."))
        self.assertTrue(claim_problems(_flat(PingPongDelay.__doc__).replace(
            "there is no latency", "there is little latency")))
        self.assertTrue(claim_problems(PingPongDelay.__doc__, CLAIMS + (
            ("A click comes out on the frame it went in: there is no "
             "latency.", ("Tier1Fast.test_nothing_here",)),)))


if __name__ == "__main__":
    unittest.main()
