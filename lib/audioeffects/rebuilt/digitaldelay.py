"""`DigitalDelay` - a clean digital delay with the Boss DD-2's control law.

Your dry signal passes untouched, and one clean repeat follows it, fed back
for more.

**Controls.** Time is the delay, from 12.5 to 800 ms, and Feedback is how
much of each repeat goes round again, up to 0.99. Mix is the echo level: the
dry stays at unity up to Mix 1, Mix 2 is the repeats alone, and at Mix 0 the
output is the input. Turn Time while it plays and the repeats bend in pitch
and settle, instead of clicking. Glide is how long a full-range Time move
takes, from 800 ms to 8 s. Glide 0 is an instant knob, and its price is a
click. Repeat Tone is a low-pass and Repeat Cut a high-pass inside the loop,
so each repeat is a little darker or thinner than the last. Repeat Tone's
top stop and Repeat Cut's bottom stop take them out. With Sync on, Time is
Division of the host's beat, up to 800 ms; with no host tempo, Time stays
where the knob is. The class reads the tempo only when a control moves or a
patch loads, so after a tempo change Time keeps the old beat until you move
a control.

**The pedal.** Patch 5 puts the DD-2's 7 kHz and 40 Hz corners in the
loop. The DD-2's compander and its HOLD are not here.

**Where it stops.** At 48 kHz the repeats of a Time you have stopped
turning do not darken. At 44.1 and 22.05 kHz a few Times land a hair off
the whole frame, and at those each repeat spills a little onto the frame
beside it. A rising Time move at the fastest Glides can read more than 10
cents off the ideal bend, because the node walks its read head in single
precision. At 22.05 kHz the top positions of Repeat Tone sit on one clamp
below Nyquist and sound the same. The dry sits at unity and the repeats add
to it, so a hot input can reach the int16 rail. With Repeat Cut out and Mix
below 1, an input that peaks at or below floor(32767 (1 - Mix)) - 1 cannot
reach the rail, at any Time or Feedback.

**Limits shared by the family.** A control that jumps makes the output step:
move it in small steps from the host if you need it smooth. The tail rings
only while the source keeps feeding: feed silence to let it ring out. A tail
cut short by a source that stopped carries on when the source comes back.

**Latency, tail, portability.** Latency is zero samples: nothing looks
ahead. `tail_samples` is an upper bound on how long the output takes to
reach exact zero once your input stops, at every Feedback, with Repeat Tone
in or out. With Repeat Cut in circuit, as at patch 5, `tail_samples` is
`None`: the class gives no bound there. Pass a lower `max_time_ms` for a
shorter line: Time then stops at that ceiling, and `get_macro(0)` shows
where it stopped. A constructor Time of 0 is the bottom of its span, and a
Repeat Tone or Repeat Cut of 0 is that filter out. `reset()` empties the
line and returns to patch 0. The class reads the host's transport only
while Sync is on. The class needs audiodsp's `audioecho`, and on a board
without it construction raises `ImportError`.
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

#: The Glide knob's span, log, with grid 0 the jump. A constructor Glide
#: slower than the top is clamped to it, the way Time clamps at
#: `max_time_ms`, so `get_macro(3)` always names the Glide that plays.
GLIDE_MIN_MS = 800.0
GLIDE_MAX_MS = 8000.0

#: At slew 1 a rising Time stands the read head still, and past it the line
#: plays backwards. A constructor Glide under 795.45 ms is pinned here; no
#: grid position gets there (grid 1 is slew 0.967).
SLEW_PIN = 0.99

#: The Glide knob's position for a constructor Glide faster than grid 1:
#: grid 1 itself (814.6 ms, slew 0.967), the knob's fastest walk. Grid 0 is
#: the jump, and a position just above it reads back as a MIDI value that
#: rounds to 0 on any 7-bit path (fix round 2).
GLIDE_FLOOR = 1.0 / 127.0

#: The node's own loop ceiling (`audiodsp_feedback_delay.c:157`).
FEEDBACK_MAX = 0.99

#: The line's headroom over `max_time_ms`: the node clamps a delay at
#: `line_frames - 2`, so a line of exactly `max_time_ms` could not reach it.
LINE_HEADROOM_MS = 1.0

#: The largest magnitude one line sample can hold (int16).
LINE_PEAK = 32768

#: `laps_to_zero` reckons with a Feedback this much larger, relatively, so
#: the node's single-precision feedback and product, and a board's
#: single-precision Python, can only make the bound longer, never shorter.
FEEDBACK_MARGIN = 2.0 ** -16

#: How far outside a Repeat Tone stall window `clear_of_stalls` puts the
#: Feedback it hands the node, relative to the window's edge: many times a
#: single-precision float's step (2^-24), so a board's arithmetic lands on
#: the same side, and far under the window's own width (2-4 x 10^-5) and
#: the knob's 7-bit step (0.0078). This class stopped stepping at audiodsp
#: v0.6.3rc1, whose node lands a stalled damping state (audiodsp#157).
STALL_CLEARANCE = 2.0 ** -20

#: `stall_window` widens each window by this much, relatively, either side,
#: so a Feedback on an edge that `laps_to_zero`'s own rounding puts inside
#: (a constructor value that comes back through the macro 10^-17 away) is
#: moved too. Four times under `STALL_CLEARANCE`, so a moved value is
#: never itself on the widened edge.
STALL_FUZZ = 2.0 ** -22

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
    `:498-501` at v0.6.2), so with b = 1 - a it is
    H = b (1 - z^-1) / (1 - b z^-1).
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


def laps_to_zero(feedback, excess=0.0):
    """How many laps of the line can still hold a non-zero sample once the
    input stops. Finite at every Feedback since audiodsp v0.6.3rc1.

    Once the input stops, the node writes `to_s16(recirculated(s, f))` for
    each value s it sends round (`audiodsp_feedback_delay.c:529`). Since
    audiodsp v0.6.2 (#154) `recirculated` (`:344`) rounds f s to nearest
    where |s| - |f s| > 0.5 and truncates it toward zero otherwise.

    With Repeat Tone out (`excess` 0) s is a line sample, or a mix of two
    at a fractional read, so |s| <= x, the line's peak, and the node
    guarantees |write| < |s|: a lap maps x to at most
    min(x - 1, floor(f x + 0.5)). Both halves only grow with x, so the peak
    of one lap bounds every sample of the next, and iterating from full
    scale counts the laps to exact zero. That is finite at every Feedback;
    0.99 takes 685 laps.

    With Repeat Tone in, s is the loop low-pass's state, which can sit
    above the line's peak by up to `excess` times it (`DigitalDelay`'s
    `_tone_excess`). Then a lap maps x to the node's write at
    s = x (1 + excess), whichever branch it takes, and the guarantee is
    gone: where that write is still x, the peak is handed back. Up to
    audiodsp v0.6.2 it stayed there for ever (1 LSB at Feedback 0.5, 5 at
    0.9, Tone 800 Hz, on a DC input), and this count was `None` there.
    From v0.6.3rc1 (audiodsp#157) the node sets a damping state that has
    stopped moving onto its input, once a block, at or below 64 LSB, which
    covers every such x (at most 50, at the node's 0.99). So the peak is
    counted one more lap there and then leaves as with the filter out,
    min(x - 1, floor(f x + 0.5)). The extra lap is measured, not derived
    (the landing waits for a block's end, and a host picks the block):
    at every window centre k = 1 ... 50, Repeat Tone grid 0, 64 and 126,
    on a 2 LSB DC and on full scale, in blocks of 64 to 4 096 frames at
    Time 12.5 ms, each tail ends inside the count with the extra lap left
    out, 239 frames or more short of it.
    """
    feedback = float(feedback)
    if feedback < 0.0:
        feedback = 0.0
    if feedback > FEEDBACK_MAX:
        feedback = FEEDBACK_MAX
    up = feedback * (1.0 + FEEDBACK_MARGIN)
    low = feedback * (1.0 - FEEDBACK_MARGIN)
    laps = 0
    peak = LINE_PEAK
    while peak > 0:
        laps += 1
        if excess <= 0.0:
            image = int(math.floor(up * peak + 0.5))
            if image >= peak:
                image = peak - 1
        else:
            sent = peak * (1.0 + excess)
            if sent * (1.0 - low) > 0.5:
                image = int(math.floor(up * sent + 0.5))
            else:
                image = int(math.floor(up * sent))
            if image >= peak:
                # The node's landing (audiodsp#157): one more lap, then the
                # peak leaves as it does with the filter out.
                laps += 1
                image = int(math.floor(up * peak + 0.5))
                if image >= peak:
                    image = peak - 1
        peak = image
    return laps


# `stall_window` and `clear_of_stalls` are no longer called by this class
# (the node lands a stalled damping state since audiodsp v0.6.3rc1, #157).
# Only planted faults use them: the faults in this class's test file and in
# other classes' test files (SlapbackDelay, PingPongDelay, CombFilter,
# TapeDelay, MultiTapDelay) that hand the node the old stepped Feedback.
def stall_window(feedback, excess):
    """The Repeat Tone stall window `feedback` sits in, as (low, high), or
    `None` outside every window.

    `laps_to_zero(f, excess)` takes its extra landing lap exactly when
    some whole peak x it reaches is handed back: the rounding branch taken,
    x (1 + excess)(1 - f (1 - m)) > 0.5, and the image not below x,
    f (1 + m) x (1 + excess) + 0.5 >= x, m being `FEEDBACK_MARGIN`. For
    each x that is one window, [(1 - 0.5 / x) / ((1 + m)(1 + excess)),
    (1 - 0.5 / (x (1 + excess))) / (1 - m)), 2-4 x 10^-5 wide around
    1 - 0.5 / x; x = 1 ... 50 are the ones under the node's 0.99. Each is
    returned widened by `STALL_FUZZ` either side. With Repeat Tone out
    (`excess` 0) no lap hands a value back, and there is no window."""
    if excess <= 0.0 or feedback <= 0.0:
        return None
    grow = (1.0 + FEEDBACK_MARGIN) * (1.0 + excess)
    centre = int(math.floor(0.5 / (1.0 - feedback) + 0.5)) if feedback < 1.0 \
        else 50
    for x in (centre - 1, centre, centre + 1):
        if x < 1:
            continue
        low = (1.0 - 0.5 / x) / grow * (1.0 - STALL_FUZZ)
        high = ((1.0 - 0.5 / (x * (1.0 + excess))) / (1.0 - FEEDBACK_MARGIN)
                * (1.0 + STALL_FUZZ))
        if low <= feedback < high:
            return low, high
    return None


def clear_of_stalls(feedback, excess):
    """`feedback` moved to the nearer edge of the Repeat Tone stall window
    it sits in (`stall_window`), just outside it, or unchanged outside
    every window. The top window's upper edge is above the node's 0.99, so
    there it always moves down. Every move is under 3 x 10^-5 of Feedback
    (2.6 x 10^-5 at the 0.99 stop), far inside one step of the 7-bit knob,
    so `get_macro(1)` still names the setting that plays.

    Not called by this class since audiodsp v0.6.3rc1 (the node lands a
    stalled damping state, audiodsp#157); only planted faults use it."""
    window = stall_window(feedback, excess)
    if window is None:
        return feedback
    low, high = window
    below = low * (1.0 - STALL_CLEARANCE)
    above = high * (1.0 + STALL_CLEARANCE)
    if above > FEEDBACK_MAX or feedback - below <= above - feedback:
        return below
    return above


class DigitalDelay(_component.Component):
    """A clean digital delay with the DD-2's control law: the dry path is a
    wire, and turning Time pitch-bends the repeats instead of clicking.
    audiodsp tier; zero latency. The module docstring has the rest."""

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
        (GLIDE_MIN_MS, GLIDE_MAX_MS, "log"),  # 3  Glide, ms; grid 0 = jump
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
        # `not <=` catches NaN, which would otherwise pass both clamps and
        # size the line from nothing.
        if not max_time_ms <= TIME_MAX_MS:
            max_time_ms = TIME_MAX_MS
        if max_time_ms < TIME_MIN_MS:
            max_time_ms = TIME_MIN_MS
        self._max_time_ms = max_time_ms
        self._frames = 1
        #: The longest delay, in whole frames, the read head may still sit
        #: at. A Glide walk starts from wherever the head is and the class
        #: cannot see how far it has got, so after a falling move this keeps
        #: the old Time until a jump (Glide 0) or a clear lands the head.
        self._reach = 1
        #: True while the node has been built or cleared and not yet told a
        #: second Time: it snaps onto the configured delay on its first pull.
        self._fresh = True
        #: True inside `program_change`, which applies the macros one at a
        #: time; the node is refreshed once, after the last.
        self._deferred = False
        self._feedback = 0.0
        self._damping = 0.0
        self._node_ms = 0.0
        # 0 (or less) is how the node spells a filter out of circuit, so
        # Repeat Tone and Repeat Cut at 0 are their out stops; Time at 0
        # is the bottom of its span. Each is a value a log knob cannot seed.
        time_ms = float(time_ms)
        if not time_ms > 0.0:
            time_ms = TIME_MIN_MS
        tone_hz = float(tone_hz)
        if not tone_hz > 0.0:
            tone_hz = self._MACRO_RANGES[TONE_I][1]
        cut_hz = float(cut_hz)
        if not cut_hz > 0.0:
            cut_hz = self._MACRO_RANGES[CUT_I][0]
        #: A constructor Glide stays on the audio path until macro 3 moves:
        #: the Glide span starts at 800 ms, so a faster constructor Glide
        #: (down to the 0.99 pin) or an exact 0 has no knob position. A
        #: slower one is clamped to the span's top, 8 s.
        glide_ms = float(glide_ms)
        if glide_ms > GLIDE_MAX_MS:
            glide_ms = GLIDE_MAX_MS
        if not glide_ms > 0.0:
            # 0, a negative and NaN are the jump; a NaN slew would neither
            # walk nor jump, and the Time knob would do nothing.
            glide_ms = 0.0
        self._glide_exact = glide_ms
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
        self._own(self._delay, reset=self._clear)
        self._delay.play(self._source)
        self._output = self._delay
        # The knob is seeded where the constructor's Glide is, or at grid 1
        # for a faster one; `_glide_exact` carries the real value. Position
        # 0 is the jump, so a Glide that is not 0 is never seeded below grid
        # 1, and a get_macro / set_macro round trip keeps it gliding even
        # when a host rounds it to a MIDI value.
        self._init_macros((time_ms, feedback, mix,
                           max(GLIDE_MIN_MS, glide_ms),
                           1.0 if sync else 0.0, float(division), tone_hz,
                           cut_hz))
        if self._glide_exact > 0.0 and self._macros[GLIDE_I] < GLIDE_FLOOR:
            self._macros[GLIDE_I] = GLIDE_FLOOR
        self._seeding = False
        if patch is not None:
            self.program_change(patch)
        self._fresh = False

    def _clear(self):
        self._delay.clear()
        self._fresh = True

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
        # A host whose tempo is not a finite positive number (0, None, a
        # negative, NaN or infinity) leaves Time on the knob, as the static
        # transport does; it is never read as 120 bpm. `not bpm > 0` catches
        # NaN, and `bpm * 0` is NaN for infinity.
        bpm = float(state[2] or 0.0)
        if not bpm > 0.0 or bpm * 0.0 != 0.0:
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
        if not self._deferred:
            self._refresh()

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index` whole, then refresh once. The base applies
        the macros in index order, so a refresh per macro would read Time
        against the outgoing patch's Sync and, with a host transport, keep
        its synced Time instead of the new patch's own."""
        self._deferred = True
        try:
            _component.Component.program_change(
                self, index, channel, note_id, sample_position)
        finally:
            self._deferred = False
        if type(self).PATCHES.get(index) is not None:
            self._refresh()

    def reset(self):
        _component.Component.reset(self)
        self._fresh = False

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
        slew = slew_of(self._glide_ms())
        if self._fresh or slew <= 0.0:
            # A fresh node snaps onto the target, and with the slew off the
            # read head jumps there on the next frame.
            self._reach = self._frames
        elif self._frames > self._reach:
            self._reach = self._frames
        feedback = self._value(FEEDBACK_I)
        if feedback > FEEDBACK_MAX:
            feedback = FEEDBACK_MAX
        if feedback < 0.0:
            feedback = 0.0
        # Both out stops are exactly 0. Since audiodsp v0.6.3rc1 the node
        # keeps an out filter's state live (#158, #159), and lands a damping
        # state that has stopped moving (#157), so nothing is moved here.
        damping = self._tone_damping(self._macros[TONE_I])
        self._damping = damping
        self._feedback = feedback
        self._delay.set(
            delay_slew=slew,
            delay_ms=self._node_ms,
            feedback=feedback,
            mix=self._value(MIX_I),
            damping_hz=damping,
            cut_hz=self._cut_hz(self._macros[CUT_I]))

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound, or `None` where no bound is derived.

        `laps_to_zero(f)` laps, each at most one frame longer than the
        longest delay the read head may be at (the read interpolates
        towards the next older frame). While a Glide walk falls, that is
        the Time it is walking from, not the target, and it stays so until
        a Glide-0 move or a reset lands the head, because the class cannot
        see how far the walk has got.

        Finite at every Feedback with Repeat Cut out. With Repeat Tone in,
        each lap is `memory` frames longer, the time the low-pass takes to
        forget the lap before, and near the Feedback values where the node
        once held a small value for ever the count takes one more lap
        (`laps_to_zero`). `None` with Repeat Cut in circuit: this class
        derives no bound there.
        """
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget` and whose `super()` hands back the property itself."""
        if self._macros[CUT_I] > 0.0:
            return None
        memory, excess = self._tone_excess()
        laps = laps_to_zero(self._feedback, excess)
        return int(laps * (self._reach + 1 + memory))

    def _tone_excess(self):
        """(frames, relative excess) for Repeat Tone's low-pass. After
        `frames` frames whatever the state held before, full scale at
        most, weighs under 2^-17 LSB, which is under 2^-17 of any non-zero
        peak; and the single-precision state can rest up to 2^-24 / a of
        the peak above it, a being the coefficient, because a step
        a (v - y) under half an ulp rounds away. Read from the `damping_hz`
        the node was handed. (0, 0.0) with the filter out."""
        damping = self._damping
        if damping <= 0.0:
            return 0, 0.0
        per_frame = 2.0 * math.pi * damping / self._sample_rate
        coefficient = 1.0 - math.exp(-per_frame)
        frames = int(math.ceil(32.0 * math.log(2.0) / per_frame))
        return frames, 2.0 ** -17 + 2.0 ** -24 / coefficient
