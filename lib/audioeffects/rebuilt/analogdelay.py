"""`AnalogDelay` - a bucket-brigade delay whose Time knob is its clock.

The player's text is the class docstring, and every sentence in it that
makes a claim is tied to a test by the `CLAIMS` table in the class's test
file.
"""

VENDOR = "PyDevices"

from array import array
import math

from .. import _component
from ..chorus import nominal_damping_hz

# DigitalDelay's tail and transport arithmetic, reused rather than copied:
# the same node rounds the same way in both classes. Its module moves up
# one level when it comes home, so both homes are tried.
try:
    from .digitaldelay import DIVISION_BEATS, laps_to_zero, whole_frames
except ImportError:                     # pragma: no cover - after it lands
    from ..digitaldelay import DIVISION_BEATS, laps_to_zero, whole_frames

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None


#: The characters and their stage counts (dossier section 6): one MN3005
#: on the DM-2, two in series on the Deluxe Memory Man.
SINGLE_LINE = "single-line"
DOUBLE_LINE = "double-line"
STAGES = {SINGLE_LINE: 4096, DOUBLE_LINE: 8192}

#: sinc(x) is -3 dB at x = 0.4422, so the corner is 0.4422 f_clk =
#: 0.2211 N / T (dossier Appendix A).
CORNER_PER_STAGE_SECOND = 0.2211

#: The Time map, fixed on every instance: 20-600 ms, log, on both
#: characters (the span is ours; dossier section 8.11).
TIME_MIN_MS = 20.0
TIME_MAX_MS = 600.0

#: Modulation's peak delay swing, ms, and Mod Rate's span, Hz.
SWING_MAX_MS = 5.0
RATE_MIN_HZ = 0.05
RATE_MAX_HZ = 8.0

#: The line over `max_time_ms`: the modulation's peak swing, plus one for
#: the node's `length - 2` clamp on the read (`audiodsp_feedback_delay.c`
#: `tap_for`).
LINE_HEADROOM_MS = SWING_MAX_MS + 1.0

#: The node's own loop ceiling (`audiodsp_feedback_delay.c:157`).
FEEDBACK_MAX = 0.99

#: One period of the modulation's triangle, borrowed by the node.
TABLE_POINTS = 256

#: How close a Time write must be to the constructor's seed position to
#: count as a host reading the knob back and writing it again, which keeps
#: the constructor's exact Time on the audio path.
ECHO_TOLERANCE = 1e-9

TIME_I, FEEDBACK_I, MIX_I, MODULATION_I, RATE_I, SPREAD_I, SYNC_I, \
    DIVISION_I = range(8)


def triangle_table(points=TABLE_POINTS):
    """Q15 unit triangle, one period: 0 -> +1 -> 0 -> -1 -> 0."""
    values = array("h", [0] * points)
    for index in range(points):
        phase = index / float(points)
        if phase < 0.25:
            unit = 4.0 * phase
        elif phase < 0.75:
            unit = 2.0 - 4.0 * phase
        else:
            unit = 4.0 * phase - 4.0
        values[index] = int(round(unit * 32767.0))
    return values


def corner_hz(stages, time_ms):
    """The sinc's -3 dB point for `stages` at `time_ms`, before the clamp."""
    return CORNER_PER_STAGE_SECOND * stages * 1000.0 / float(time_ms)


def clock_slew(from_frames, to_frames):
    """The node's `delay_slew` for a clock step from a settled line: the
    walk runs |dT| / T_new delay-seconds per second, so it lasts exactly
    T_new and holds the ratio T_old / T_new (dossier section 6)."""
    return abs(float(to_frames) - float(from_frames)) / float(to_frames)


def walk_floor(frames):
    """The smallest `delay_slew` that still moves a read head sitting at up
    to `frames`: two single-precision steps of `frames`. The node walks
    `delay_current += slew` in single precision, and a slew under half a
    step of the head's position rounds back to where it was, so the head
    would stay put for good (a move under about T / 2048 frames)."""
    mantissa, exponent = math.frexp(float(max(1, frames)))
    del mantissa
    return 2.0 ** (exponent - 23)


def _f32(value):
    """`value` rounded to single precision, the same on every interpreter."""
    return array("f", (value,))[0]


def _f32_up(value):
    """The next single-precision value above a positive single `value`."""
    mantissa, exponent = math.frexp(value)
    del mantissa
    return _f32(value + 2.0 ** (exponent - 24))


def node_frames(value_ms, sample_rate):
    """What the node makes of `delay_ms = value_ms`: the single-precision
    `value * rate / 1000.0f` (`audiodsp_feedback_delay.c:148`)."""
    return _f32(_f32(_f32(value_ms) * sample_rate) / 1000.0)


def hand_off_ms(frames, sample_rate):
    """The `delay_ms` the class hands the node for whole frame `frames`:
    `frames * 1000 / fs` in single precision, stepped up one single step
    where the node's own arithmetic would land below `frames`, so the
    read's whole part is `frames` (dossier section 6, the hand-off)."""
    value = _f32(frames * 1000.0 / sample_rate)
    if node_frames(value, sample_rate) < frames:
        value = _f32_up(value)
    return value


def tone_excess(damping_hz, sample_rate):
    """(frames, relative excess) for the loop low-pass, by DigitalDelay's
    `_tone_excess` arithmetic: after `frames` frames whatever the state
    held weighs under 2^-17 LSB, and the single-precision state can rest
    up to 2^-24 / a of the peak above it, a being the coefficient."""
    if damping_hz <= 0.0:
        return 0, 0.0
    per_frame = 2.0 * math.pi * damping_hz / sample_rate
    coefficient = 1.0 - math.exp(-per_frame)
    frames = int(math.ceil(32.0 * math.log(2.0) / per_frame))
    return frames, 2.0 ** -17 + 2.0 ** -24 / coefficient


def _between(value, low, high):
    value = float(value)
    if not value >= low:
        return low
    if value > high:
        return high
    return value


class AnalogDelay(_component.Component):
    """A bucket-brigade delay whose Time knob is the line's clock.

    A bucket brigade has a fixed number of stages, so a longer delay is a
    slower clock and a lower band limit: the repeats get darker as you turn
    Time up, and your dry signal passes untouched.

    **The controls.** Time sets the delay and with it the clock. Feedback
    sends each repeat round again. Mix blends the repeats in. Modulation
    and Mod Rate wobble the delay, a chorus in a blend and a vibrato with
    the repeats alone. Spread feeds each side's repeats into the other.
    Sync locks Time to Division of the host's beat, clamped to Time's span.
    Time runs from 20 to 600 ms, Feedback from 0 to 0.99 and Mix from 0 to 2.
    Up to Mix 1 the dry passes untouched until the first repeat arrives.
    Mix 0 is a wire.
    A click comes out on the frame it went in: there is no latency.
    A one-channel source gets the same effect with Spread held at 0.

    **Two characters.** `"single-line"` (the default) is one 4096-stage
    line, the Boss DM-2; `"double-line"` is two in series, the Deluxe Memory
    Man. Any other `character` raises `ValueError`.
    The repeats' high-frequency corner is 0.2211 N / T for N stages and a
    Time of T seconds, so it halves each time Time doubles.
    Where the law passes 0.98 of Nyquist the corner holds there, so a
    shorter Time no longer brightens the repeats.

    **Time.** Every Time lands on a whole frame at every rate.
    A small Time move still lands.
    Turning Time through several positions a block apart takes seconds to
    settle, where one jump to the same place lands within the new Time.

    **Modulation.** The delay swings on a triangle by a fixed number of
    milliseconds, whatever the Time.
    A Time move leaves the swing as it is.
    A Modulation move glides over 20 ms.

    **Level and tail.** Below Mix 1, an input peaking at or below
    floor(32767 (1 - Mix)) - 1 does not reach the rail.
    `tail_samples` is an upper bound on how long the repeats take to reach
    exact zero after your input stops.
    `reset()` empties the line and returns to patch 0.
    With no host tempo, Time stays on the knob.

    **What it leaves out.** There is no sample-and-hold, so the repeats
    have no null at the clock.
    There is no fixed anti-alias pair: the repeats' one corner is the one
    that moves with Time.

    **Limits shared by the family.**
    A control that jumps makes the output step: move it in small steps from
    the host if you need it smooth.
    The tail rings only while the source keeps feeding: feed silence to let
    it ring out. A tail cut short by a source that stopped carries on when
    the source comes back.
    """

    NAME = 'AnalogDelay'
    DISPLAY_NAME = 'Analog Delay'
    CATEGORIES = ('Delay',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho",)

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Time", "Feedback", "Mix", "Modulation", "Mod Rate",
                    "Spread", "Sync", "Division")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "TOGGLE",
        7: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (TIME_MIN_MS, TIME_MAX_MS, "log"),  # 0  Time, ms
        (0.0, FEEDBACK_MAX),                # 1  Feedback
        (0.0, 2.0),                         # 2  Mix; dry at unity to 1
        (0.0, SWING_MAX_MS),                # 3  Modulation, peak swing ms
        (RATE_MIN_HZ, RATE_MAX_HZ, "log"),  # 4  Mod Rate, Hz
        (0.0, 1.0),                         # 5  Spread (cross-feed)
        (0.0, 1.0),                         # 6  Sync
        (0.0, 15.0),                        # 7  Division index
    )

    #: `_component.macro_of` of the dossier's section 6 settings; patch 0 is
    #: the constructor's defaults on the grid.
    PATCHES = {
        0: ("Single Line Repeats", (101, 51, 25, 0, 69, 0, 0, 51)),
        1: ("Short Bright Repeats", (41, 38, 32, 0, 69, 0, 0, 51)),
        2: ("Long Dark Repeats", (124, 71, 25, 0, 69, 0, 0, 51)),
        3: ("Modulated Repeats", (107, 58, 29, 76, 75, 0, 0, 51)),
        4: ("Wet Vibrato", (26, 0, 127, 51, 115, 0, 0, 51)),
        5: ("High Feedback Wash", (116, 109, 22, 25, 52, 64, 0, 51)),
        6: ("Dotted Eighth, Synced", (101, 58, 25, 0, 69, 0, 127, 68)),
    }

    def _build(self, time_ms=300.0, feedback=0.4, mix=0.4, modulation_ms=0.0,
               mod_rate_hz=0.8, spread=0.0, sync=False, division=6,
               character=SINGLE_LINE, max_time_ms=TIME_MAX_MS, patch=None):
        if character not in STAGES:
            raise ValueError("character must be %r or %r, not %r"
                             % (SINGLE_LINE, DOUBLE_LINE, character))
        self._character = character
        self._stages = STAGES[character]
        max_time_ms = float(max_time_ms)
        # `not <=` catches NaN, which would otherwise pass both clamps and
        # size the line from nothing.
        if not max_time_ms <= TIME_MAX_MS:
            max_time_ms = TIME_MAX_MS
        if max_time_ms < TIME_MIN_MS:
            max_time_ms = TIME_MIN_MS
        self._max_time_ms = max_time_ms
        #: The whole-frame Time last handed to the node, and what was handed.
        self._frames = 1
        self._node_ms = 0.0
        #: The longest whole-frame delay the read head may still sit at. A
        #: walk starts from wherever the head is and the class cannot see how
        #: far it has got, so after a falling move this keeps the old Time
        #: until a reset lands the head.
        self._reach = 1
        #: The walk rate of the last Time move; a move of another macro
        #: leaves the walk in progress at its rate.
        self._slew = 0.0
        #: True while the node has been built or cleared and has not yet
        #: been told a second Time: it snaps onto the delay on its first pull.
        self._fresh = True
        #: True inside `program_change`, which applies the macros one at a
        #: time; the node is refreshed once, after the last.
        self._deferred = False
        self._feedback = 0.0
        self._damping = 0.0
        self._corner = 0.0
        self._swing_ms = 0.0
        self._spread = 0.0
        time_ms = float(time_ms)
        if not time_ms > 0.0:
            time_ms = TIME_MIN_MS
        #: The constructor's Time, exactly, until Time is moved: the log
        #: map's round trip can move a value by a last bit, which is enough
        #: to land a Time that sits on a half frame (150 ms at 22.05 kHz,
        #: 3307.5 frames) on the frame below.
        self._time_exact = time_ms
        self._time_seed = 0.0
        self._seeding = True
        mod_rate_hz = float(mod_rate_hz)
        if not mod_rate_hz > 0.0:
            mod_rate_hz = RATE_MIN_HZ
        #: Written once; a Modulation move changes the depth, not the table.
        self._table = triangle_table()
        self._delay = audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=max_time_ms + LINE_HEADROOM_MS,
            delay_ms=self._clamp_ms(time_ms),
            feedback=0.0,
            mix=0.0,
            damping_hz=0.0,
            cut_hz=0.0,
            wow_hz=0.0,
            wow_depth_ms=0.0,
            wow_shape=self._table,
            delay_slew=0.0)
        # `clear()` empties the line and the loop filter and re-primes the
        # read head, so a reset is silent and snaps onto patch 0's Time.
        self._own(self._delay, reset=self._clear)
        self._delay.play(self._source)
        self._output = self._delay
        self._deferred = True
        try:
            self._init_macros((time_ms, feedback, mix, modulation_ms,
                               mod_rate_hz, spread, 1.0 if sync else 0.0,
                               float(division)))
        finally:
            self._deferred = False
            self._seeding = False
        self._refresh()
        # Read after the refresh, which re-seats a Time above `max_time_ms`.
        self._time_seed = self._macros[TIME_I]
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
        return _between(time_ms, TIME_MIN_MS, self._max_time_ms)

    def _corner_for(self, time_ms):
        """The corner law for this character at `time_ms`, before the clamp.
        A hook, so a planted fault can run it on another stage count."""
        return corner_hz(self._stages, time_ms)

    def _node_time_ms(self, frames):
        """What the node is handed for whole frame `frames`."""
        return hand_off_ms(frames, self._sample_rate)

    def _walk_rate(self, from_frames, to_frames):
        """The node's `delay_slew` for a Time move: the clock's law, floored
        at two single-precision steps of the furthest the head may sit, so
        a move too small for the law's rate still lands."""
        return max(clock_slew(from_frames, to_frames),
                   walk_floor(max(from_frames, to_frames, self._reach)))

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
        # transport does. `not bpm > 0` catches NaN, and `bpm * 0` is NaN
        # for infinity.
        bpm = float(state[2] or 0.0)
        if not bpm > 0.0 or bpm * 0.0 != 0.0:
            return None
        index = int(round(self._value(DIVISION_I)))
        index = min(len(DIVISION_BEATS) - 1, max(0, index))
        return DIVISION_BEATS[index] * 60000.0 / bpm

    # -- applying ------------------------------------------------------

    def _time_ms(self):
        """The Time the audio path plays, before it is clamped and landed."""
        if self._time_exact is not None:
            return self._time_exact
        return self._value(TIME_I)

    def _apply_macro(self, index, position):
        if index == TIME_I and not self._seeding and not (
                self._time_exact is not None
                and abs(position - self._time_seed) <= ECHO_TOLERANCE):
            # A host that reads Time back and writes the same position keeps
            # the constructor's exact Time; any other move drops it.
            self._time_exact = None
        if not self._deferred:
            self._refresh()

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index` whole, then refresh once, so Time is read
        against the new patch's Sync and moves (and walks) once."""
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
        # The cleared node snapped onto patch 0's Time.
        self._fresh = False

    def _refresh(self):
        fs = self._sample_rate
        span = self._MACRO_RANGES[TIME_I]
        if self._macros[SYNC_I] >= 0.5:
            synced = self._synced_ms()
            if synced is not None:
                # Division quantises Time into the same map, and the clamp
                # shows through get_macro(0) the same way.
                self._time_exact = None
                self._macros[TIME_I] = _component.macro_position(
                    span, self._clamp_ms(synced))
        time_ms = self._time_ms()
        clamped = self._clamp_ms(time_ms)
        if clamped != time_ms:
            if self._time_exact is not None:
                self._time_exact = clamped
            self._macros[TIME_I] = _component.macro_position(span, clamped)
        frames = max(1, whole_frames(clamped, fs))
        if self._fresh:
            # A fresh node snaps onto the delay on its first pull; there is
            # no walk to set a rate for.
            self._slew = 0.0
            self._reach = frames
        elif frames != self._frames:
            # A clock step: the walk's rate from the Time last handed.
            self._slew = self._walk_rate(self._frames, frames)
            if frames > self._reach:
                self._reach = frames
        self._frames = frames
        self._node_ms = self._node_time_ms(frames)

        # The corner law on the knob's milliseconds, clamped below Nyquist
        # and pre-warped so the one-pole's -3 dB point is the corner.
        self._corner = self._hz(self._corner_for(clamped))
        self._damping = nominal_damping_hz(self._corner, fs)

        # Handed as set: since audiodsp v0.6.3rc1 the node lands a loop
        # low-pass that has stopped moving (#157), and since v0.6.3rc3 a
        # stereo cross-feed sum too (#170), so nothing is stepped clear.
        self._feedback = _between(self._value(FEEDBACK_I), 0.0, FEEDBACK_MAX)

        self._swing_ms = _between(self._value(MODULATION_I), 0.0,
                                  SWING_MAX_MS)
        # At one channel the node's cross-feed sends the repeat nowhere.
        if self._channel_count == 1:
            self._spread = 0.0
        else:
            self._spread = _between(self._value(SPREAD_I), 0.0, 1.0)
        self._delay.set(
            delay_slew=self._slew,
            delay_ms=self._node_ms,
            feedback=self._feedback,
            mix=_between(self._value(MIX_I), 0.0, 2.0),
            damping_hz=self._damping,
            cut_hz=0.0,
            cross_feed=self._spread,
            wow_hz=_between(self._value(RATE_I), RATE_MIN_HZ, RATE_MAX_HZ),
            wow_depth_ms=self._swing_ms)

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound: `laps_to_zero(f, excess)` laps of the longest delay
        the read head may be at, plus the modulation's peak swing in frames
        rounded up, plus one frame for the interpolated read, plus the loop
        low-pass's memory. Finite at every setting the class reaches."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        memory, excess = tone_excess(self._damping, self._sample_rate)
        laps = laps_to_zero(self._feedback, excess)
        swing = int(math.ceil(self._swing_ms * self._sample_rate / 1000.0))
        return int(laps * (self._reach + swing + 1 + memory))
