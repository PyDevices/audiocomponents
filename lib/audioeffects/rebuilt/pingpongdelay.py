"""`PingPongDelay` - repeats that alternate between the speakers.

The player's text is the class docstring, and every sentence in it that
makes a claim is tied to a test by the `CLAIMS` table in the class's test
file.
"""

VENDOR = "PyDevices"

from .. import _component
from ..chorus import nominal_damping_hz

# DigitalDelay's arithmetic, reused rather than copied: the same node rounds
# the same way in both classes. Its module moves up one level when it comes
# home, so both homes are tried; the same for SlapbackDelay's `tone_excess`.
try:
    from .digitaldelay import (DIVISION_BEATS, laps_to_zero, nominal_cut_hz,
                               whole_frames)
except ImportError:                     # pragma: no cover - after it lands
    from ..digitaldelay import (DIVISION_BEATS, laps_to_zero,
                                nominal_cut_hz, whole_frames)
try:
    from .slapbackdelay import tone_excess
except ImportError:                     # pragma: no cover - after it lands
    from ..slapbackdelay import tone_excess

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None


#: The Time span, fixed on every instance (dossier section 6): 20-1000 ms,
#: log.
TIME_MIN_MS = 20.0
TIME_MAX_MS = 1000.0

#: The line's headroom over `max_time_ms`: the node clamps a delay at
#: `line_frames - 2` (`audiodsp_feedback_delay.c:148-150`), so a line of
#: exactly `max_time_ms` could not reach it.
LINE_HEADROOM_MS = 1.0

#: The node's own loop ceiling (`audiodsp_feedback_delay.c:157`).
FEEDBACK_MAX = 0.99

#: The Repeat Tone and Repeat Cut spans' corners, Hz. Tone's top stop and
#: Cut's bottom stop are the filters out of circuit.
TONE_MIN_HZ = 800.0
TONE_MAX_HZ = 16000.0
CUT_MIN_HZ = 20.0
CUT_MAX_HZ = 400.0

#: The fixed Time walk, delay-seconds per second: 3/16, exact in float32
#: (dossier section 8.5, `SlapbackDelay`'s section 8 answer 6).
SLEW = 0.1875

#: How close, as a 0..1 knob position, a Time write must come to the
#: constructor's own seeded position to count as a host echoing it back:
#: 1e-6 is 1/7 874 of one MIDI step.
ECHO_TOLERANCE = 1e-6

(TIME_I, FEEDBACK_I, MIX_I, SPREAD_I, SIDE_I, SYNC_I, DIVISION_I, TONE_I,
 CUT_I) = range(9)

#: The constructor defaults NaN falls back to: Time, Feedback, Mix, Spread,
#: Division.
DEFAULT_TIME_MS = 280.0
DEFAULT_FEEDBACK = 0.45
DEFAULT_MIX = 0.3
DEFAULT_SPREAD = 1.0
DEFAULT_DIVISION = 6.0


def _option(value, default):
    """A constructor option as a float; NaN is the option's default."""
    value = float(value)
    if value != value:
        return default
    return value


def _between(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def _side(value):
    """`first_side` -> 0.0 (left) or 1.0 (right)."""
    if isinstance(value, str):
        word = value.lower()
        if word == "left":
            return 0.0
        if word == "right":
            return 1.0
        raise ValueError("first_side must be 'left' or 'right', not %r"
                         % (value,))
    return 1.0 if float(value) >= 0.5 else 0.0


class PingPongDelay(_component.Component):
    """Two delay lines crossed into each other: the repeats bounce between the
    speakers.

    Your dry signal passes untouched on both sides, and the repeats come
    back one side and then the other, all the way down.

    **The controls.** The first repeat comes back Time later on the side
    First Side names, the next Time after that on the other side, and they
    keep bouncing, each a Feedback's worth quieter than the last. Time runs
    from 20 to 1000 ms and Feedback from 0 to 0.99. Mix is the echo level:
    the dry stays at unity up to Mix 1, Mix 2 is the repeats alone, and at
    Mix 0 the output is the input. Spread moves between two plain delays
    with the same repeats on both sides, at 0, and the full bounce, at 1. At
    Spread 1 each repeat is on one side only, and the other side is exact
    zero. With Sync on, Time is Division of the host's beat, up to 1000 ms;
    with no host tempo, Time stays where the knob is. The class reads the
    host's transport only while Sync is on, and then only when a control
    moves or a patch loads, never while it plays. Repeat Tone is a low-pass
    and Repeat Cut a high-pass inside the loop, so each bounce is a little
    darker or thinner than the last. Repeat Tone's top stop and Repeat Cut's
    bottom stop take them out, and a filter taken out is out. At 22.05 kHz
    the top positions of Repeat Tone sit on one clamp below Nyquist and
    sound the same. Turning Time walks the repeats to the new Time, bending
    their pitch, instead of clicking.

    **Stereo and mono.** At Spread 1 the loop hears the average of the two
    input channels, so what differs between them never repeats. The dry is
    always each channel's own signal, never swapped or summed. A one-channel
    source gets an ordinary feedback delay at the same Time, Feedback and
    Mix, and Spread and First Side do nothing there.

    **Where it stops.** At 48 kHz every Time position lands on the nearest
    whole frame. At 44.1 and 22.05 kHz the node lands some positions a
    fraction of a frame off, and a sliver of each repeat falls on the frame
    beside it. The dry sits at unity and the repeats add to it, so a hot
    input can reach the int16 rail. With Repeat Cut out and Mix below 1, an
    input that peaks at or below floor(32767 (1 - Mix)) - 1 cannot reach the
    rail, at any Time, Feedback or Spread. Repeat Cut's high-pass
    overshoots, so with it in leave more room.

    **Limits shared by the family.** A control that jumps makes the output
    step: move it in small steps from the host if you need it smooth. When
    your source ends, the tail rings out as it would on silence.

    **Latency, tail, portability.** A click comes out on the frame it went
    in: there is no latency. `tail_samples` is an upper bound on how many
    frames the output takes to reach exact zero, counted from when your
    input stops or from when you read it if that is later, for the settings
    as they stand when you read it. With Repeat Cut in circuit
    `tail_samples` is `None`: the class gives no bound there. Pass a lower
    `max_time_ms` for a shorter line: Time then stops at that ceiling, and
    `get_macro(0)` shows where it stopped. A constructor value outside a
    knob's span clamps to the nearer stop, a `tone_hz` or `cut_hz` of 0 or
    less is that filter out, and NaN takes the option's default. `reset()`
    empties the line and returns to patch 0. The class needs audiodsp's
    `audioecho`, and on a board without it construction raises
    `ImportError`.
    """

    NAME = 'PingPongDelay'
    DISPLAY_NAME = 'Ping-Pong Delay'
    CATEGORIES = ('Delay',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho",)

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Time", "Feedback", "Mix", "Spread", "First Side",
                    "Sync", "Division", "Repeat Tone", "Repeat Cut")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "TOGGLE",
        5: "TOGGLE",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
        8: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (TIME_MIN_MS, TIME_MAX_MS, "log"),  # 0  Time, ms
        (0.0, FEEDBACK_MAX),                # 1  Feedback
        (0.0, 2.0),                         # 2  Mix; dry at unity to 1
        (0.0, 1.0),                         # 3  Spread
        (0.0, 1.0),                         # 4  First Side: left, right
        (0.0, 1.0),                         # 5  Sync
        (0.0, 15.0),                        # 6  Division index
        (TONE_MIN_HZ, TONE_MAX_HZ, "log"),  # 7  Repeat Tone, Hz; top = out
        (CUT_MIN_HZ, CUT_MAX_HZ, "log"),    # 8  Repeat Cut, Hz; bottom = out
    )

    #: `_component.macro_of` of the dossier's section 6 settings; patch 0 is
    #: the constructor's defaults on the grid.
    PATCHES = {
        0: ("Wide Bounce", (86, 58, 19, 127, 0, 0, 51, 127, 0)),
        1: ("Eighth Note Bounce", (86, 64, 19, 127, 0, 127, 51, 127, 0)),
        2: ("Quarter Note Bounce", (86, 51, 19, 127, 0, 127, 76, 127, 0)),
        3: ("Narrow Bounce", (86, 58, 19, 64, 0, 0, 51, 127, 0)),
        4: ("Two Delays", (86, 58, 19, 0, 0, 0, 51, 127, 0)),
        5: ("Dark Bounce", (99, 83, 19, 127, 0, 0, 51, 48, 0)),
        6: ("Right First", (86, 58, 19, 127, 127, 0, 51, 127, 0)),
    }

    def _build(self, time_ms=DEFAULT_TIME_MS, feedback=DEFAULT_FEEDBACK,
               mix=DEFAULT_MIX, spread=DEFAULT_SPREAD, first_side="left",
               sync=False, division=DEFAULT_DIVISION, tone_hz=TONE_MAX_HZ,
               cut_hz=CUT_MIN_HZ, max_time_ms=TIME_MAX_MS, patch=None):
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
        #: at. The walk starts from wherever the head is and the class cannot
        #: see how far it has got, so after a falling move this keeps the old
        #: Time until a reset lands the head.
        self._reach = 1
        #: True while the node has been built or cleared and not yet told a
        #: second Time: it snaps onto the configured delay on its first pull.
        self._fresh = True
        #: True while several macros are applied at once (the constructor,
        #: `program_change`); the node is refreshed once, after the last.
        self._deferred = False
        self._feedback = 0.0
        self._damping = 0.0
        self._cut = 0.0
        self._node_ms = 0.0
        #: The constructor's Time, exactly, until macro 0 moves. Seeding a
        #: log knob and reading it back is not exact, and a few ulps under a
        #: half frame lands one frame short.
        self._time_exact = None
        self._time_seed = -1.0
        self._seeding = True
        # A log knob cannot seed 0 or a negative, so those clamp to the
        # nearer stop here; 0 or less is how the node spells a filter out.
        time_ms = _between(_option(time_ms, DEFAULT_TIME_MS),
                           TIME_MIN_MS, max_time_ms)
        tone_hz = _option(tone_hz, TONE_MAX_HZ)
        if not tone_hz > 0.0:
            tone_hz = TONE_MAX_HZ
        tone_hz = _between(tone_hz, TONE_MIN_HZ, TONE_MAX_HZ)
        cut_hz = _option(cut_hz, CUT_MIN_HZ)
        if not cut_hz > 0.0:
            cut_hz = CUT_MIN_HZ
        cut_hz = _between(cut_hz, CUT_MIN_HZ, CUT_MAX_HZ)
        values = (time_ms,
                  _between(_option(feedback, DEFAULT_FEEDBACK),
                           0.0, FEEDBACK_MAX),
                  _between(_option(mix, DEFAULT_MIX), 0.0, 2.0),
                  _between(_option(spread, DEFAULT_SPREAD), 0.0, 1.0),
                  _side(first_side),
                  1.0 if sync else 0.0,
                  _between(_option(division, DEFAULT_DIVISION), 0.0, 15.0),
                  tone_hz,
                  cut_hz)
        self._delay = audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=max_time_ms + LINE_HEADROOM_MS,
            delay_ms=time_ms,
            feedback=0.0,
            mix=0.0,
            damping_hz=0.0,
            cut_hz=0.0,
            cross_feed=0.0,
            input_pan=0.0,
            delay_slew=0.0)
        # `clear()` empties both lanes and the loop filters and re-primes the
        # read head (`audiodsp_feedback_delay.c:295-303`, `:286-288`), so a
        # reset is silent and snaps onto patch 0's Time.
        self._own(self._delay, reset=self._clear)
        self._delay.play(self._source)
        self._output = self._delay
        self._time_exact = time_ms
        self._deferred = True
        try:
            self._init_macros(values)
        finally:
            self._deferred = False
            self._seeding = False
        self._time_seed = self._macros[TIME_I]
        self._refresh()
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

    def _clamp_ms(self, time_ms):
        time_ms = float(time_ms)
        if time_ms > self._max_time_ms:
            return self._max_time_ms
        if time_ms < TIME_MIN_MS:
            return TIME_MIN_MS
        return time_ms

    def _node_time_ms(self, frames):
        """What the node is handed for a whole-frame Time."""
        return frames * 1000.0 / self._sample_rate

    def _tone_damping(self, position):
        """Macro 7's position -> the node's `damping_hz`: the corner the
        loop low-pass achieves, clamped below Nyquist and pre-warped. The
        top stop is exactly 0 (out of circuit) and is never pre-warped."""
        if position >= 1.0:
            return 0.0
        corner = _component.macro_value(self._MACRO_RANGES[TONE_I], position)
        return nominal_damping_hz(self._hz(corner), self._sample_rate)

    def _cut_hz(self, position):
        """Macro 8's position -> the node's `cut_hz`: the corner the loop
        high-pass achieves, clamped and pre-warped. The bottom stop is
        exactly 0 (out of circuit)."""
        if position <= 0.0:
            return 0.0
        corner = _component.macro_value(self._MACRO_RANGES[CUT_I], position)
        return nominal_cut_hz(self._hz(corner), self._sample_rate)

    def _cross_and_pan(self):
        """(cross_feed, input_pan) for Spread and First Side. A one-channel
        node has no second lane: anything but (0, 0) there silences its loop
        (dossier section 7.1), so Spread and First Side are inert."""
        if self._channel_count == 1:
            return 0.0, 0.0
        spread = _between(self._value(SPREAD_I), 0.0, 1.0)
        if self._macros[SIDE_I] >= 0.5:
            return spread, spread
        return spread, -spread

    def _synced_ms(self):
        """Division x the host's beat, or `None` with no host transport
        (the static one), where Time stays where the knob is."""
        transport = self._transport
        if transport is _component.static_transport:
            return None
        state = transport() if callable(transport) else transport
        # A host whose tempo is not a finite positive number (0, None, a
        # negative, NaN or infinity) leaves Time on the knob, as the static
        # transport does. `not bpm > 0` catches NaN, and `bpm * 0` is NaN
        # for infinity.
        bpm = float(state[2] or 0.0)
        if not bpm > 0.0 or bpm * 0.0 != 0.0:
            return None
        index = int(round(self._value(DIVISION_I)))
        index = min(len(DIVISION_BEATS) - 1, max(0, index))
        return DIVISION_BEATS[index] * 60000.0 / bpm

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        if index == TIME_I and not self._seeding and not (
                self._time_exact is not None
                and abs(position - self._time_seed) <= ECHO_TOLERANCE):
            # A host that reads Time back and writes the same position
            # (`set_macro(0, get_macro(0))`) keeps the constructor's exact
            # Time; any other position drops it.
            self._time_exact = None
        if not self._deferred:
            self._refresh()

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index` whole, then refresh the node once. A refresh
        per macro would read Time against the outgoing patch's Sync."""
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

    def _time_ms(self):
        """The Time the audio path plays, before it is landed: Division x
        the beat with Sync on and a host tempo, else the constructor's exact
        Time until macro 0 moves, else the knob. Clamped at `max_time_ms`,
        and the knob moved to show the clamp."""
        span = self._MACRO_RANGES[TIME_I]
        synced = None
        if self._macros[SYNC_I] >= 0.5:
            synced = self._synced_ms()
        if synced is not None:
            self._time_exact = None
            time_ms = self._clamp_ms(synced)
            self._macros[TIME_I] = _component.macro_position(span, time_ms)
            return time_ms
        if self._time_exact is not None:
            return self._time_exact
        time_ms = _component.macro_value(span, self._macros[TIME_I])
        clamped = self._clamp_ms(time_ms)
        if clamped != time_ms:
            self._macros[TIME_I] = _component.macro_position(span, clamped)
        return clamped

    def _refresh(self):
        rate = self._sample_rate
        self._frames = max(1, whole_frames(self._time_ms(), rate))
        self._node_ms = self._node_time_ms(self._frames)
        if self._fresh or self._frames > self._reach:
            self._reach = self._frames
        # Both out stops are exactly 0, and the Feedback is handed as set.
        # Since audiodsp v0.6.3rc1 the node keeps an out low-pass's state on
        # the tap and an out high-pass's at zero (#158, #159), and lands a
        # low-pass that has stopped moving (#157).
        damping = self._tone_damping(self._macros[TONE_I])
        cut = self._cut_hz(self._macros[CUT_I])
        feedback = _between(self._value(FEEDBACK_I), 0.0, FEEDBACK_MAX)
        self._feedback = feedback
        self._damping = damping
        self._cut = cut
        cross, pan = self._cross_and_pan()
        self._delay.set(
            delay_slew=SLEW,
            delay_ms=self._node_ms,
            feedback=feedback,
            mix=_between(self._value(MIX_I), 0.0, 2.0),
            damping_hz=damping,
            cut_hz=cut,
            cross_feed=cross,
            input_pan=pan)

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound, or `None` with Repeat Cut in circuit.

        `laps_to_zero(f, excess)` laps, each at most one frame longer than
        the longest delay the read head may be at (the read interpolates
        towards the next older frame), plus the Tone low-pass's memory.
        While a walk falls, that is the Time it is walking from, until a
        reset lands the head. The cross-feed hands each lane a convex mix
        of the two lanes' loop values (`audiodsp_feedback_delay.c:581-589`),
        so the per-lap argument holds at every Spread."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        if self._cut > 0.0:
            return None
        memory, excess = tone_excess(self._damping, self._sample_rate)
        laps = laps_to_zero(self._feedback, excess)
        return int(laps * (self._reach + 1 + memory))
