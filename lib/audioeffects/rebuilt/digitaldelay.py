"""`DigitalDelay` - a clean interpolated line with the Boss DD-2's control law.

Rebuilt from scratch for Phase 5 against
`workspace docs/effects-internal/dossiers/DigitalDelay.md`, whose trait
table was frozen at Station A before this file existed (anchor commit
51207b8, 2026-09-27). The old class in `delay.py` is consulted only for the
seven defects that dossier's section 7 names; it stays the class the
library serves until the auditor adopts this one.

**What it sounds like.** Your dry signal passes untouched, and one clean
repeat follows it, fed back for more. Time (12.5-800 ms) is the DD-2's
D.TIME and its three MODE ranges folded into one knob. Feedback (0-0.99)
is F.BACK, Mix (0-2) is E.LEVEL: dry at unity up to 1, wet alone at 2, and
Mix 0 is a wire while the line keeps recording. Turn Time while it plays
and the repeats bend in pitch and settle, the way the pedal's single master
clock resamples its memory, instead of clicking. Glide sets how fast that
happens: the time a full-range Time move takes, 800 ms to 8 s. Repeat Tone
and Repeat Cut put the pedal's 7 kHz and 40 Hz corners into the loop as
knobs, so each repeat gets a little darker or thinner than the last. Sync
locks Time to Division of the host's beat.

**The standout:** the Boss DD-2 Digital Delay (1983), light touch. You get
its control law and its dry/wet discipline as defaults, and its converter
colour as two knobs that default off. Patch 5 is the pedal's own corners.

**Portability tier: audiodsp** (`REQUIRES = ("audioecho",)`). The stock
`audiodelays.Echo` limits its only output at +-28000, so its Mix 0 is not
a wire, and its one continuous-time mode lands 350 ms 33 samples late. On
a stock CircuitPython board this module imports cleanly and construction
raises `ImportError`.

**Latency: zero samples, at every setting and every rate.** Nothing looks
ahead. The delay is the wet path, not latency on the dry path, and no
option adds any.

**Mono.** A one-channel source gets the identical effect on its one
channel. The class never passes `input_pan`, which in mono would overwrite
the node's mono feed and halve the repeats.

**RAM.** The line is `max_time_ms + 1` ms of two int16 lanes whatever the
channel count: 153 792 B at 48 kHz for the default 800 ms (141 296 B at
44.1 kHz, 70 648 B at 22.05 kHz), plus about 1.2 KB of node. Pass a lower
`max_time_ms` to spend less (300 ms costs 57 792 B); Time then stops at
that ceiling and `get_macro(0)` shows where it stopped.

**Cost.** One `audioecho.FeedbackDelay` with `delay_slew` on; no mixer.
Palette row FeedbackDelay +options (the nearest not-cheaper row; there is
no row for the slew alone), glue 0: **P4 <= 9 %, S3 <= 15 %** of a
5.333 ms stereo block. The board measurement is pending hardware.

**What the default surrenders.** It is a clean line, so it does not darken
on its own: the DD-2's 7 kHz band limit and its compander are not in the
default sound (patch 5 and the Tone and Cut knobs put the corners back; the
compander is not modelled at all). Freeze (the pedal's HOLD) is not here:
the node's loop tops out at 0.99, so a held phrase would fade 0.087 dB a
lap, and a HOLD that fades is worse than none. **Glide 0 is an instant
knob, and its price is a click**: a 200 -> 150 ms jump steps 7712 LSB into
a tone whose own steepest step is 1565. At the default Glide (4 s for the
full range) a falling Time bends the repeats 311 cents up and a rising one
380 cents down while it moves, and a 200 -> 150 ms move takes 254 ms. At the
knob's fastest glide (grid 1, 814.6 ms) a falling move reads +1171 cents and
a rising one nearly stalls the read head.

While Time moves, the line is read between samples, and the two-tap read
costs the top of the band sqrt(1 - 2 frac (1 - frac)(1 - cos 2 pi f / fs))
per pass: 5.1 dB at 15 kHz at a half frame, 48 kHz. Every static Time is
landed on the nearest whole frame at the running rate, where the read is
lossless, so the repeats of a Time you have stopped turning do not darken.
Above Mix 1 the dry falls as 2 - Mix, by `audiodelays.Echo`'s convention.

`capabilities = ("tempo_sync",)`: with Sync on, the class reads
`self._transport()` on every macro move and program change (not per block).
With no host transport, Time stays where the knob is.
"""

VENDOR = "PyDevices"

import math

from .. import _component
from ..chorus import nominal_damping_hz

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None


#: The Time map, fixed on every instance (dossier T4): 12.5-800 ms, log.
TIME_MIN_MS = 12.5
TIME_MAX_MS = 800.0

#: Glide is the time a full-range Time move takes; the node's `delay_slew`
#: (delay-seconds per second) is FULL_RANGE_MS / glide_ms (dossier section 6).
FULL_RANGE_MS = TIME_MAX_MS - TIME_MIN_MS

#: At slew 1 a rising Time stands the read head still, and past it the line
#: plays backwards. A constructor Glide under 795.45 ms is pinned here; no
#: grid position gets there (grid 1 is slew 0.967).
SLEW_PIN = 0.99

#: The node's own loop ceiling (`audiodsp_feedback_delay.c:157`).
FEEDBACK_MAX = 0.99

#: The line's headroom over `max_time_ms`: the node clamps a delay at
#: `line_frames - 2`, so a line of exactly `max_time_ms` could not reach it.
LINE_HEADROOM_MS = 1.0

#: Division's sixteen note values, in quarter-note beats, rising: 1/32,
#: 1/16T, 1/32., 1/16, 1/8T, 1/16., 1/8, 1/4T, 1/8., 1/4, 1/2T, 1/4., 1/2,
#: 1/1T, 1/2., 1/1.
DIVISION_BEATS = (0.125, 1.0 / 6.0, 0.1875, 0.25, 1.0 / 3.0, 0.375, 0.5,
                  2.0 / 3.0, 0.75, 1.0, 4.0 / 3.0, 1.5, 2.0, 8.0 / 3.0, 3.0,
                  4.0)

TIME_I, FEEDBACK_I, MIX_I, GLIDE_I, SYNC_I, DIVISION_I, TONE_I, CUT_I = \
    range(8)


def nominal_cut_hz(corner_hz, sample_rate):
    """`cut_hz` whose one-pole high-pass -3 dB is `corner_hz` at
    `sample_rate`. 0 stays 0, which is the filter out of circuit.

    The node's high-pass is `y -= lp(y)` with the low-pass coefficient
    a = 1 - exp(-2 pi hz / fs) (`audiodsp_feedback_delay.c:33-40`,
    `:462-466`), so with b = 1 - a it is H = b (1 - z^-1) / (1 - b z^-1).
    |H|^2 = 1/2 gives b^2 (3 - 4 cos w) + 2 b cos w - 1 = 0; the root in
    (0, 1) is the pole, and `cut_hz = -fs ln b / 2 pi`.
    """
    fs = float(sample_rate)
    fc = float(corner_hz)
    if fc <= 0.0:
        return 0.0
    c = math.cos(2.0 * math.pi * fc / fs)
    qa = 3.0 - 4.0 * c
    qb = 2.0 * c
    if abs(qa) < 1e-12:
        roots = (1.0 / qb,) if qb != 0.0 else ()
    else:
        disc = qb * qb + 4.0 * qa
        if disc < 0.0:
            disc = 0.0
        root = math.sqrt(disc)
        roots = ((-qb + root) / (2.0 * qa), (-qb - root) / (2.0 * qa))
    pole = None
    for candidate in roots:
        if 0.0 < candidate < 1.0:
            pole = candidate
    if pole is None:
        return fc
    return -fs * math.log(pole) / (2.0 * math.pi)


def slew_of(glide_ms):
    """The node's `delay_slew` for a Glide: 0 (the jump) at Glide 0,
    otherwise 787.5 ms over `glide_ms`, pinned at 0.99."""
    glide_ms = float(glide_ms)
    if glide_ms <= 0.0:
        return 0.0
    slew = FULL_RANGE_MS / glide_ms
    if slew > SLEW_PIN:
        slew = SLEW_PIN
    return slew


def whole_frames(time_ms, sample_rate):
    """The nearest whole frame at the running rate (dossier section 6)."""
    return int(math.floor(float(time_ms) * sample_rate / 1000.0 + 0.5))


class DigitalDelay(_component.Component):
    """A clean digital delay with the DD-2's control law: the dry path is a
    wire, and turning Time pitch-bends the repeats instead of clicking.
    audiodsp tier; zero latency.

    **What the default surrenders:** no band limit and no compander in the
    default sound (patch 5 and the Tone and Cut knobs are the corners), no
    HOLD, and Glide 0's instant knob clicks. At the default Glide a falling
    Time bends the repeats +311 cents while it moves, a rising one -380.
    """

    NAME = 'DigitalDelay'
    DISPLAY_NAME = 'Digital Delay'
    CATEGORIES = ('Delay',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho",)

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Time", "Feedback", "Mix", "Glide", "Sync", "Division",
                    "Repeat Tone", "Repeat Cut")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "TOGGLE",
        5: "UNIPOLAR",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (TIME_MIN_MS, TIME_MAX_MS, "log"),  # 0  Time, ms
        (0.0, FEEDBACK_MAX),                # 1  Feedback
        (0.0, 2.0),                         # 2  Mix; dry at unity to 1
        (800.0, 8000.0, "log"),             # 3  Glide, ms; grid 0 = jump
        (0.0, 1.0),                         # 4  Sync
        (0.0, 15.0),                        # 5  Division index
        (800.0, 16000.0, "log"),            # 6  Repeat Tone, Hz; top = out
        (20.0, 400.0, "log"),               # 7  Repeat Cut, Hz; bottom = out
    )

    #: `_component.macro_of` of the dossier's section 6 settings; patch 0 is
    #: the constructor's defaults on the grid.
    PATCHES = {
        0: ("Clean Repeats", (102, 45, 19, 89, 0, 51, 127, 0)),
        1: ("Eighth Notes", (102, 51, 19, 89, 127, 51, 127, 0)),
        2: ("Dotted Eighths", (102, 58, 19, 89, 127, 68, 127, 0)),
        3: ("Short Doubling", (45, 0, 32, 89, 0, 51, 127, 0)),
        4: ("Long Ambient", (125, 90, 16, 89, 0, 51, 127, 0)),
        5: ("Band Limited Repeats", (102, 77, 19, 89, 0, 51, 92, 29)),
    }

    def _build(self, time_ms=350.0, feedback=0.35, mix=0.3, glide_ms=4000.0,
               sync=False, division=6, tone_hz=16000.0, cut_hz=20.0,
               max_time_ms=TIME_MAX_MS, patch=None):
        max_time_ms = float(max_time_ms)
        if max_time_ms > TIME_MAX_MS:
            max_time_ms = TIME_MAX_MS
        if max_time_ms < TIME_MIN_MS:
            max_time_ms = TIME_MIN_MS
        self._max_time_ms = max_time_ms
        self._frames = 1
        self._feedback = 0.0
        self._node_ms = 0.0
        #: A constructor Glide stays on the audio path until macro 3 moves:
        #: the Glide span starts at 800 ms, so a faster constructor Glide
        #: (down to the 0.99 pin) or an exact 0 has no knob position.
        self._glide_exact = float(glide_ms)
        self._seeding = True
        self._delay = audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=max_time_ms + LINE_HEADROOM_MS,
            delay_ms=self._clamp_ms(time_ms),
            feedback=0.0,
            mix=0.0,
            damping_hz=0.0,
            cut_hz=0.0,
            delay_slew=0.0)
        # `clear()` empties the line and the loop filters and re-primes the
        # read head, so a reset is silent and snaps onto patch 0's Time.
        self._own(self._delay, reset=self._delay.clear)
        self._delay.play(self._source)
        self._output = self._delay
        # The knob is seeded at its bottom (800 ms) for a faster or zero
        # constructor Glide; `_glide_exact` carries the real value.
        self._init_macros((time_ms, feedback, mix, max(800.0, glide_ms),
                           1.0 if sync else 0.0, float(division), tone_hz,
                           cut_hz))
        self._seeding = False
        if patch is not None:
            self.program_change(patch)

    # -- the maps ------------------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _time_map(self, position):
        """Macro 0's position -> milliseconds; the same on every instance."""
        return _component.macro_value(self._MACRO_RANGES[TIME_I], position)

    def _clamp_ms(self, time_ms):
        time_ms = float(time_ms)
        if time_ms > self._max_time_ms:
            return self._max_time_ms
        if time_ms < TIME_MIN_MS:
            return TIME_MIN_MS
        return time_ms

    def _glide_ms(self):
        if self._glide_exact is not None:
            return self._glide_exact
        if self._macros[GLIDE_I] <= 0.0:
            return 0.0
        return self._value(GLIDE_I)

    def _tone_damping(self, position):
        """Macro 6's position -> the node's `damping_hz`. The top stop is
        exactly 0 (out of circuit) and is never pre-warped."""
        if position >= 1.0:
            return 0.0
        corner = _component.macro_value(self._MACRO_RANGES[TONE_I], position)
        return nominal_damping_hz(self._hz(corner), self._sample_rate)

    def _cut_hz(self, position):
        """Macro 7's position -> the node's `cut_hz`. The bottom stop is
        exactly 0 (out of circuit)."""
        if position <= 0.0:
            return 0.0
        corner = _component.macro_value(self._MACRO_RANGES[CUT_I], position)
        return nominal_cut_hz(self._hz(corner), self._sample_rate)

    def _transport_state(self):
        transport = self._transport
        state = transport() if callable(transport) else transport
        return transport, state

    def _synced_ms(self):
        """Division x the host's beat, or `None` with no host transport
        (the static one), where Time stays where the knob is."""
        transport, state = self._transport_state()
        if transport is _component.static_transport:
            return None
        bpm = float(state[2]) if state[2] else 120.0
        if bpm <= 0.0:
            return None
        index = int(round(self._value(DIVISION_I)))
        index = min(len(DIVISION_BEATS) - 1, max(0, index))
        return DIVISION_BEATS[index] * 60000.0 / bpm

    def _node_time_ms(self, frames):
        """What the node is handed for a whole-frame Time."""
        return frames * 1000.0 / self._sample_rate

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        del position
        if index == GLIDE_I and not self._seeding:
            self._glide_exact = None
        self._refresh()

    def _refresh(self):
        span = self._MACRO_RANGES[TIME_I]
        if self._macros[SYNC_I] >= 0.5:
            synced = self._synced_ms()
            if synced is not None:
                # Division quantises Time into the same map, and the clamp
                # shows through get_macro(0) the same way (dossier T4).
                self._macros[TIME_I] = _component.macro_position(
                    span, self._clamp_ms(synced))
        time_ms = self._time_map(self._macros[TIME_I])
        clamped = self._clamp_ms(time_ms)
        if clamped != time_ms:
            self._macros[TIME_I] = _component.macro_position(span, clamped)
        self._frames = max(1, whole_frames(clamped, self._sample_rate))
        self._node_ms = self._node_time_ms(self._frames)
        feedback = self._value(FEEDBACK_I)
        if feedback > FEEDBACK_MAX:
            feedback = FEEDBACK_MAX
        if feedback < 0.0:
            feedback = 0.0
        self._feedback = feedback
        self._delay.set(
            delay_slew=slew_of(self._glide_ms()),
            delay_ms=self._node_ms,
            feedback=feedback,
            mix=self._value(MIX_I),
            damping_hz=self._tone_damping(self._macros[TONE_I]),
            cut_hz=self._cut_hz(self._macros[CUT_I]))

    @property
    def tail_samples(self):
        """The -60 dB lap count plus one lap, from the Time in whole frames
        and the Feedback: `ceil(T (1 + 3 / -log10 f))`, and `T` at f = 0. A
        loop filter only shortens the tail, so this is an upper bound."""
        self._check_live()
        frames = self._frames
        feedback = self._feedback
        if feedback <= 0.0:
            return int(frames)
        laps = 1.0 + 3.0 * math.log(10.0) / -math.log(feedback)
        return int(math.ceil(frames * laps))
