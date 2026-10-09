"""`SlapbackDelay` - one tape repeat after the dry, in mono: the Sun Studio slap.

The player's text is the class docstring, and every sentence in it that
makes a claim is tied to a test by the `CLAIMS` table in the class's test
file.
"""

VENDOR = "PyDevices"

import math

from .. import _component
from ..chorus import nominal_damping_hz

# DigitalDelay's tail arithmetic, reused rather than copied: the same node
# rounds the same way in both classes. Its module moves up one level when
# it comes home, so both homes are tried.
try:
    from .digitaldelay import laps_to_zero, whole_frames
except ImportError:                     # pragma: no cover - after it lands
    from ..digitaldelay import laps_to_zero, whole_frames

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None


#: The Time span, fixed on every instance (dossier section 6): 40-250 ms, log.
TIME_MIN_MS = 40.0
TIME_MAX_MS = 250.0

#: The line: Time's top plus 1 ms. The node clamps a delay at
#: `line_frames - 2` (`audiodsp_feedback_delay.c:148-150`), and the read
#: reaches 250 ms plus the wow's 22.1 frames at 3.5 cents; 251 ms clears
#: that at every rate (dossier Tier 3, A8.6).
LINE_MS = TIME_MAX_MS + 1.0

#: The Tone span's corners; the top stop is exactly `damping_hz = 0`.
TONE_MIN_HZ = 2000.0
TONE_MAX_HZ = 20000.0

#: The wow's fixed rate and the Wow knob's ceiling, in cents peak.
WOW_HZ = 0.7
WOW_MAX_CENTS = 3.5

#: The Repeats knob's top, handed to the node's `feedback`.
REPEATS_MAX = 0.6

#: The fixed Time walk, delay-seconds per second: 3/16, exact in float32,
#: so every step of the walk is exact at 48 kHz (dossier section 8.6).
SLEW = 0.1875

#: How close, as a 0..1 knob position, a Time write must come to the
#: constructor's own seeded position to count as a host echoing it back:
#: 1e-6 is 1/7 874 of one MIDI step, and holds a single-precision board's
#: round trip through the 0-127 scale.
ECHO_TOLERANCE = 1e-6

TIME_I, LEVEL_I, SATURATION_I, TONE_I, WOW_I, REPEATS_I = range(6)

#: The constructor defaults, which NaN falls back to.
DEFAULTS = (135.0, 0.35, 0.15, TONE_MAX_HZ, 1.0, 0.0)


def wow_depth_ms(cents):
    """The Wow knob's cents -> the node's `wow_depth_ms` at 0.7 Hz.

    A delay swinging D sin(2 pi f t) ms moves pitch by a peak ratio of
    1 + 2 pi f D / 1000, so the rising side reaches `cents` at
    D = (2^(cents/1200) - 1) / (2 pi 0.7) x 1000 (dossier A4): 1.0 cent is
    0.1314 ms, 3.5 cents 0.4601 ms. Clamped to 0..3.5 cents."""
    cents = float(cents)
    if not cents > 0.0:
        return 0.0
    if cents > WOW_MAX_CENTS:
        cents = WOW_MAX_CENTS
    return ((2.0 ** (cents / 1200.0) - 1.0) / (2.0 * math.pi * WOW_HZ)
            * 1000.0)


def tone_excess(damping_hz, sample_rate):
    """(frames, relative excess) for a loop low-pass at `damping_hz` (already
    pre-warped): after `frames` frames whatever its state held weighs under
    2^-17 of it, and its single-precision state can rest up to
    2^-24 / a above the line's peak, a being the coefficient. `DigitalDelay`'s
    `_tone_excess`, as a function of the handed value. (0, 0.0) with Tone
    out."""
    if damping_hz <= 0.0:
        return 0, 0.0
    per_frame = 2.0 * math.pi * damping_hz / sample_rate
    coefficient = 1.0 - math.exp(-per_frame)
    frames = int(math.ceil(32.0 * math.log(2.0) / per_frame))
    return frames, 2.0 ** -17 + 2.0 ** -24 / coefficient


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


class SlapbackDelay(_component.Component):
    """One tape repeat after the dry, in the same place: the Sun Studio slap.

    Your dry signal passes untouched, and one copy of it comes back a moment
    later, a little quieter: the two-machine tape echo on Sam Phillips' Sun
    sides.
    By default the repeat comes 135 ms after the dry, once.

    **The controls.** Time is the gap between the dry and the repeat. Level
    is the console's return. Saturation is how hard the return drove the
    record amplifier. Tone is the tape path's top end. Wow is the
    transport's slow wobble. Repeats sends the slap round again.
    Time runs from 40 to 250 ms, Level from 0 to 2, Saturation from 0 to 1,
    Tone from 2 kHz to out at its top stop, Wow from 0 to 3.5 cents and
    Repeats from 0 to 0.6.
    Level 0 is a wire.
    Up to Level 1 the dry passes untouched until the repeat arrives, however
    hard Saturation drives the repeat.
    A hot input can reach the rail, since the repeat adds to a dry at unity.
    At Repeats 0 there is one repeat and no second.
    Repeats above 0 sends the repeat round for more.
    Wow swings the repeat's pitch by the cents the knob reads, at a slow
    fixed rate.
    The default Wow takes the repeat's very top more than 4 dB down at
    Nyquist, where Wow 0 leaves it within half a dB.
    At 22.05 kHz the last Tone positions below the top stop clamp below
    Nyquist and all do the same thing.

    **Time.** Every Time position lands on the nearest whole frame at
    48 kHz.
    At 44.1 and 22.05 kHz the node lands some positions a fraction of a
    frame off, and a sliver of the repeat falls on the frame beside it.
    A host that writes back `get_macro(0)` keeps the constructor's exact
    Time.
    Turning Time walks the repeat to the new Time, bending its pitch,
    instead of clicking.
    A Wow move glides instead of stepping.

    **Mono, latency, tail.** A source the same in both channels comes out
    the same in both channels, and a one-channel source gets the stereo
    render's left channel.
    A click comes out on the frame it went in: there is no latency.
    `tail_samples` is an upper bound on how many frames the output takes to
    reach exact zero, counted from when your input stops or from when you
    read it if that is later, for the settings as they stand when you read
    it.
    `reset()` empties the line and returns to patch 0.
    The class never reads the host's tempo.
    A constructor value outside a knob's span clamps to the nearer stop, a
    `tone_hz` of 0 or less is Tone out, and NaN takes the option's default.

    **Limits shared by the family.**
    A control that jumps makes the output step: move it in small steps from
    the host if you need it smooth.
    When your source ends, the tail rings out as it would on silence.
    """

    NAME = 'SlapbackDelay'
    DISPLAY_NAME = 'Slapback Delay'
    CATEGORIES = ('Delay',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Time", "Level", "Saturation", "Tone", "Wow", "Repeats")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (TIME_MIN_MS, TIME_MAX_MS, "log"),  # 0  Time, ms
        (0.0, 2.0),                         # 1  Level; dry at unity to 1
        (0.0, 1.0),                         # 2  Saturation, loop_drive
        (TONE_MIN_HZ, TONE_MAX_HZ, "log"),  # 3  Tone, Hz; top = out
        (0.0, WOW_MAX_CENTS),               # 4  Wow, cents peak at 0.7 Hz
        (0.0, REPEATS_MAX),                 # 5  Repeats, feedback
    )

    #: `_component.macro_of` of the dossier's section 6 settings; patch 0 is
    #: the constructor's defaults on the grid.
    PATCHES = {
        0: ("Single Slap", (84, 22, 19, 127, 36, 0)),
        1: ("Short Slap", (52, 22, 19, 127, 36, 0)),
        2: ("Doubling", (0, 32, 19, 127, 73, 0)),
        3: ("Hot Return", (84, 22, 89, 127, 36, 0)),
        4: ("Two Repeats", (84, 22, 19, 127, 36, 74)),
        5: ("Dark Slap", (84, 22, 19, 51, 36, 0)),
    }

    def _build(self, time_ms=135.0, level=0.35, saturation=0.15,
               tone_hz=TONE_MAX_HZ, wow_cents=1.0, repeats=0.0, patch=None):
        self._frames = 1
        #: The longest delay, in whole frames, the read head may still sit
        #: at. The walk starts from wherever the head is and the class cannot
        #: see how far it has got, so after a falling move this keeps the old
        #: Time until a reset lands the head (dossier section 8.7).
        self._reach = 1
        #: True while the node has been built or cleared and not yet told a
        #: second Time: it snaps onto the configured delay on its first pull.
        self._fresh = True
        #: True while several macros are applied at once (the constructor,
        #: `program_change`); the node is refreshed once, after the last.
        self._deferred = False
        self._feedback = 0.0
        self._damping = 0.0
        self._wow_ms = 0.0
        self._node_ms = 0.0
        #: The constructor's Time, exactly, until macro 0 moves. Seeding a
        #: log knob and reading it back is not exact: 135.0 ms comes back a
        #: few ulps under, which at 44.1 kHz (5 953.5 frames) lands on 5 953
        #: instead of the 5 954 the whole-frame law gives 135.0.
        self._time_exact = None
        #: The knob position the constructor's Time seeded, which a host's
        #: echo of `get_macro(0)` comes back to within `ECHO_TOLERANCE`.
        self._time_seed = -1.0
        self._seeding = True
        # A log knob cannot seed 0 or a negative, so those clamp to the
        # nearer stop here; 0 or less is how the node spells Tone out.
        time_ms = _between(_option(time_ms, DEFAULTS[TIME_I]),
                           TIME_MIN_MS, TIME_MAX_MS)
        tone_hz = _option(tone_hz, DEFAULTS[TONE_I])
        if not tone_hz > 0.0:
            tone_hz = TONE_MAX_HZ
        tone_hz = _between(tone_hz, TONE_MIN_HZ, TONE_MAX_HZ)
        values = (time_ms,
                  _option(level, DEFAULTS[LEVEL_I]),
                  _option(saturation, DEFAULTS[SATURATION_I]),
                  tone_hz,
                  _option(wow_cents, DEFAULTS[WOW_I]),
                  _option(repeats, DEFAULTS[REPEATS_I]))
        self._delay = audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=LINE_MS,
            delay_ms=time_ms,
            feedback=0.0,
            mix=0.0,
            damping_hz=0.0,
            cut_hz=0.0,
            delay_slew=0.0)
        # `clear()` empties the line and the loop filters and re-primes the
        # read head (`audiodsp_feedback_delay.c:291-299`), so a reset is
        # silent and snaps onto patch 0's Time.
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

    def _node_time_ms(self, frames):
        """What the node is handed for a whole-frame Time."""
        return frames * 1000.0 / self._sample_rate

    def _tone_damping(self, position):
        """Macro 3's position -> the node's `damping_hz`: the corner the
        loop low-pass achieves, clamped below Nyquist and pre-warped. The
        top stop is exactly 0 (out of circuit) and is never pre-warped."""
        if position >= 1.0:
            return 0.0
        corner = _component.macro_value(self._MACRO_RANGES[TONE_I], position)
        return nominal_damping_hz(self._hz(corner), self._sample_rate)

    def _wow_depth_ms(self, cents):
        return wow_depth_ms(cents)

    # -- applying ------------------------------------------------------

    def _time_ms(self):
        """The Time the audio path plays, before it is landed."""
        if self._time_exact is not None:
            return self._time_exact
        return self._value(TIME_I)

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
        """Apply patch `index` whole, then refresh the node once."""
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
        self._frames = max(1, whole_frames(self._time_ms(),
                                           self._sample_rate))
        self._node_ms = self._node_time_ms(self._frames)
        if self._fresh or self._frames > self._reach:
            self._reach = self._frames
        # Tone out is exactly 0, and Repeats is handed as set: since
        # audiodsp v0.6.3rc1 the node keeps an out low-pass on the signal
        # (#158) and lands a stalled one (#157).
        damping = self._tone_damping(self._macros[TONE_I])
        feedback = _between(self._value(REPEATS_I), 0.0, REPEATS_MAX)
        self._feedback = feedback
        self._damping = damping
        self._wow_ms = self._wow_depth_ms(self._value(WOW_I))
        self._delay.set(
            delay_slew=SLEW,
            delay_ms=self._node_ms,
            feedback=feedback,
            mix=_between(self._value(LEVEL_I), 0.0, 2.0),
            loop_drive=_between(self._value(SATURATION_I), 0.0, 1.0),
            damping_hz=damping,
            cut_hz=0.0,
            wow_hz=WOW_HZ,
            wow_depth_ms=self._wow_ms)

    @property
    def tail_samples(self):
        """What this bound promises is in the class docstring; how it is
        built is in the dossier."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        memory, excess = tone_excess(self._damping, self._sample_rate)
        laps = laps_to_zero(self._feedback, excess)
        wow =int(math.ceil(self._wow_ms * self._sample_rate / 1000.0))
        return int(laps * (self._reach + wow + 1 + memory))
