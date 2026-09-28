"""`AnalogDelay` - a bucket-brigade delay whose Time knob is its clock.

Rebuilt from scratch for Phase 5 against
`workspace docs/effects-internal/dossiers/AnalogDelay.md`, whose trait
table was frozen at Station A before this file existed (anchor commit
cc61011, 2026-09-28, the Station A critique revision). The old class in
`delay.py` is consulted only for the seven defects that dossier's section 7
names; it stays the class the library serves until the auditor adopts this
one.

**What it sounds like.** Your dry signal passes untouched, and repeats
follow it that get darker the longer you set Time, because in a bucket
brigade the Time knob is a clock: the line has a fixed number of stages,
so a longer delay is a slower clock and a lower band limit. Two characters
pick the stage count: `"single-line"` (the default) is one 4096-stage line,
the Boss DM-2; `"double-line"` is two in series, 8192 stages, the
Electro-Harmonix Deluxe Memory Man, which at the same Time runs its clock
an octave higher and so keeps its repeats an octave brighter. Time is
20-600 ms on both, Feedback 0-0.99, and Mix 0-2 (dry at unity up to 1, wet
alone at 2; Mix 0 is a wire while the line keeps recording). Turn Time
while it plays and the repeats bend in pitch the way a clock step bends
them, and settle (a turn through many positions takes seconds; see
"Turning Time" below). Modulation (0-5 ms) and Mod Rate (0.05-8 Hz) wobble the
delay on a triangle, the Memory Man's chorus and vibrato: a blend with
Modulation up is a chorus, the wet alone (Mix 2, patch 4) a vibrato.
Spread feeds each side's repeats into the other. Sync locks Time to
Division of the host's beat.

**The standouts:** the Boss DM-2 and the Deluxe Memory Man, as the two
characters. The band limit is the one thing that separates them, so it is
the one thing the character changes.

**Portability tier: audiodsp** (`REQUIRES = ("audioecho",)`): one
`audioecho.FeedbackDelay`, audiodsp's own node. On a stock CircuitPython
board this module imports cleanly and construction raises `ImportError`.

**Latency: zero samples, at every setting, patch, character and rate.**
Nothing looks ahead. The delay is the wet path, not latency on the dry
path, and no option adds any. That is a decision: oversampling is the
clean way to keep a bucket-brigade model free of aliasing, and its filters
cost latency a stompbox has none to spend.

**Mono.** A one-channel source gets the identical effect on its one
channel with Spread held at 0. At one channel the node's cross-feed sends
the repeat nowhere (Feedback 0.7 with cross-feed 1.0 leaves the dry, the
first repeat and nothing after it), so the class hands the node 0 there
whatever the knob says. The class never passes `input_pan`, which in mono
would overwrite the node's mono feed.

**RAM.** The line is `max_time_ms + 6` ms of two int16 lanes whatever the
channel count: 116 352 B at 48 kHz for the default 600 ms (106 896 B at
44.1 kHz, 53 448 B at 22.05 kHz), plus 512 B for the triangle table and
about 1.2 KB of node. The six milliseconds are the modulation's 5 ms peak
swing and one for the read's clamp. Pass a lower `max_time_ms` to spend
less; Time then stops at that ceiling and `get_macro(0)` shows where.

**Cost.** One `audioecho.FeedbackDelay` with `delay_slew` on, the loop
low-pass in and a borrowed 256-point table; no mixer, the same graph for
both characters and every patch. Palette row FeedbackDelay +options (the
nearest not-cheaper row), glue 0: **P4 <= 9 %, S3 <= 15 %** of a 5.333 ms
stereo block. The board measurement is pending hardware.

**The band limit.** The repeats' high-frequency corner is the sinc's -3 dB
point at the line's clock, 0.2211 N / T: 3019 Hz at 300 ms single-line,
6038 Hz double-line, halving each time Time doubles. It is the node's one
loop low-pass, pre-warped so its -3 dB point is that corner, so each pass
through the loop darkens the repeat once more, as the circuit's filters
do. Where the law passes 0.98 of Nyquist (below 38.5 ms single-line and
77.0 ms double-line at 48 kHz; 41.9 / 83.8 ms at 44.1 kHz; 83.8 /
167.6 ms at 22.05 kHz) the corner holds at that clamp, so there a shorter
Time no longer brightens the repeats.

**What the class surrenders, said plainly.** Three things both pedals do
are not here. There is no sample-and-hold, so the repeats roll off on one
pole where a bucket brigade rolls off on a sinc with a null at its clock
(12.1 dB off the sinc's shape between 300 and 600 ms, and -7.7 dB, not a
null, at the clock). There is no compander, so the repeats do not pump
and a burst's rise time does not change from repeat to repeat. And there
is no fixed anti-alias and reconstruction pair: both pedals bound their
wet path near 3 kHz at every Time, so at short Times this class's repeats
are brighter than either pedal's. The line's image spectra and its clock
noise are not modelled either. None of those has a node in audiodsp v0.6.3rc1
that can sit inside the loop.

**Time.** Every Time is landed on the nearest whole frame at the running
rate, and the node is handed a delay whose read's whole part is that frame
on every interpreter: the node turns milliseconds into frames in single
precision, and at 44.1 and 22.05 kHz one frame count in about seven has
no single-precision value that lands on it exactly, so the class hands the
next value up. The read then trails the frame by at most 0.00195 frames at
44.1 kHz (0.00098 at 22.05; none at 48), never early.

**A Time move glides in pitch on the clock's own law.** A move from
`T_old` to `T_new` walks the read head at |T_new - T_old| / T_new, so it
holds the pitch ratio T_old / T_new for exactly T_new and then returns to
unity, without a click: 200 -> 100.4 ms bends the repeats +1193 cents for
100.4 ms, 100 -> 300 ms -1902 cents for 300 ms. The node walks the head in
single precision, and a rate under half a step of the head's position
would round back to where it was and leave the head short for good, so
the rate never goes below two single-precision steps of the furthest the
head may sit (1/512 of a frame per frame from 8 192 to 16 384 frames,
1/256 above). That only touches moves of under 0.4 % of T: they land in
less than T_new, bent by at most 7 cents (300 -> 300.1 ms, 5 frames at
48 kHz, lands in 0.053 s).

**Turning Time takes seconds to settle.** The walk's rate is taken from
the Time last handed to the node, not from where the head is, because the
class cannot see the head. A knob turned through several positions sends
several moves, and once the head falls behind, the last move's small rate
carries it the rest of the way. At 48 kHz, 7-bit positions one block
apart: MIDI 101 -> 111 (299 -> 391 ms, 10 moves) still differs from the
same move made as one jump 3.4 s after the last move, where the jump has
landed in 0.39 s; MIDI 64 -> 101 (111 -> 299 ms, 37 moves) 6.9 s. A
14-bit controller's fine steps are slower still: 300 -> 400 ms in 1386
moves takes 20 s, walking at the floor. The pitch claim covers none of
this, only a move from rest. It is claimed for moves of up to 3 : 1 and inputs
from -28.7 to -0.2 dBFS; quieter, int16 rounding decides the reading
(13 cents off at -48.7 dBFS). The claim is about the walk itself: under
feedback, each later repeat re-reads a line that was written while the
head was moving, so the repeats do not telescope the way a clock step in
a real bucket brigade makes them, and nothing here claims they do.

**Modulation.** The swing is a fixed number of milliseconds whatever the
Time, so a Time move never steps the read offset and equal Modulation
bends equally at every Time (+-20.7 cents at patch 3's 3 ms and 1 Hz,
+257 / -302 at the stops). The shape is a plain triangle, the clock law's
first order; it differs from the exact reciprocal by up to S / T of the
swing (1.7 % at 300 ms and full depth, 25 % at 20 ms). A Modulation move
glides: since audiodsp v0.6.3rc1 the node ramps a new swing in over 20 ms
(audiodsp#160), where up to v0.6.2 it jumped the read by the change in
depth times where the triangle stood (142 frames for 5 -> 2 ms at the
triangle's peak, 48 kHz). While the swing travels the extra pitch is the
change over 20 ms times where the triangle stands: 5 -> 2 ms at a peak
bends the repeats by 15 % for those 20 ms, +242 cents at one peak and
-281 at the other. A move made while the last one's 20 ms is still
running starts a new 20 ms from wherever the swing has got to, so the
swing travels at (target - where it stands) / 20 ms, which a knob turned
through several positions a block apart can make a little faster than
any one move's own |change| / 20 ms. So the read moves at most that
distance over 20 ms plus the triangle's own 4 x Mod Rate x swing of a
frame per frame faster or slower than the tone. With the wet alone and
Feedback 0, no step in the output is then larger than the input's own
largest step times 1 plus that: on a 997 Hz tone at 12 000 LSB, Time
300 ms, five moves between 0 and 5 ms at Mod Rate 1 and 8 Hz and eight
points of the triangle, at 48, 44.1 and 22.05 kHz, the largest step in
the 40 ms after a move is at most 0.943 of that (1 -> 1.5 ms at 1 Hz,
48 kHz: 1 522 LSB against 1 615, where v0.6.2's node read 7 133). With
the dry in or the repeats recirculating, the output's own step already
passes that bar before any move (1.9 x at Mix 1, 1.3 x at Feedback 0.5),
so the sentence says nothing there. Mod Rate moves keep the triangle's
phase and do not step.

**Input ceiling.** The dry path sits at unity and the repeats add to it,
so a hot input can put the output on the int16 rail; there is no input
gain to turn down. The loop's low-pass, cross-feed and interpolated read
are each a convex mix, so no repeat exceeds full scale and the wet adds at
most Mix x full scale: below Mix 1, an input peaking at or below
floor(32767 (1 - Mix)) - 1 cannot reach the rail at any Time, Feedback,
Modulation or Spread (-4.4 dBFS at the default Mix 0.4).

**Tail.** `tail_samples` is an upper bound on how long the repeats take to
reach exact zero after your input stops: DigitalDelay's lap count at the
Feedback the node is handed, each lap the longest delay the head may be at
plus the swing, one frame for the interpolated read and the low-pass's
memory. 187 954 frames (3.9 s) at the defaults; 26.5 s at patch 5, the
longest. The loop low-pass is always in, and at a Feedback a hair either
side of 1 - 0.5 / k it can come to rest a hair above k LSB and hand it
back. Up to audiodsp v0.6.2 it did so for ever, and the class handed the
node the nearer edge of that window instead. Since v0.6.3rc1 the node sets
a stalled low-pass onto its input (audiodsp#157), the Feedback you set is
the one the node plays, and the bound counts one more lap there. In
stereo the cross-feed could do the same thing: the node's sum of the two
sides, in single precision, can come out a step above both, and with
Spread at 39 / 127 or any other value off a short binary grid and a
Feedback a float32 step or two under 1 - 0.5 / k that handed k LSB back for
ever. So Spread reaches the node on a grid of 4096ths, within 1/8192 of
the knob, where that sum is exact on every interpreter for any side
under 4096 LSB (above that a step is far too small to hold a repeat);
0 and 1 are untouched. The bound then holds at every Feedback and Spread
the constructor or a macro can hand, stereo and mono. After a falling
Time move the bound keeps the Time the head walked from until a reset,
because the class cannot see how far the walk has got.

`capabilities = ("tempo_sync",)`: with Sync on, the class reads
`self._transport()` on every macro move and program change (not per block).
With no host transport, or a host whose tempo is not a finite positive
number, Time stays where the knob is. A synced Time change walks at the
clock's law like any other.

Constructor values stay on the audio path unquantised by the grid, and a
constructor Time plays exactly as given (not through the knob's map, whose
round trip can move a Time that sits on a half frame to the frame below)
until Time is moved; a host that reads the knob back and writes the same
position keeps it. A constructor Time of 0 or less is 20 ms, a Mod Rate of 0 or less 0.05 Hz,
a `max_time_ms` above 600 or NaN 600 ms. `character` is `"single-line"`
or `"double-line"`; anything else raises `ValueError`.
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

#: Spread's grid as the node is handed it: whole 4096ths, so the loop's
#: cross-feed sum is exact for the small lanes a tail ends on.
SPREAD_GRID = 4096

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


def spread_on_grid(spread):
    """`spread` on the 1/4096 grid the node is handed (dossier section 8,
    R13). The node sends `own * (1 - s) + other * s` round the loop in
    single precision; with s = 39 / 127 or any other value off a short
    binary grid those two products can add up to one step above both
    lanes, and at a Feedback a hair under 1 - 0.5 / k that hands a landed
    k LSB back for ever. On the grid both products of a lane under 4096
    LSB are exact, so the sum lies between the lanes on every interpreter,
    whether or not a board fuses the multiply-add. The grid moves Spread
    by at most 1/8192."""
    return math.floor(spread * SPREAD_GRID + 0.5) / SPREAD_GRID


def _between(value, low, high):
    value = float(value)
    if not value >= low:
        return low
    if value > high:
        return high
    return value


class AnalogDelay(_component.Component):
    """A bucket-brigade delay: the Time knob is the line's clock, so the
    repeats darken as Time grows and a Time move bends their pitch.
    audiodsp tier; zero latency.

    **What the default surrenders:** no sample-and-hold (a one-pole
    roll-off, not the sinc, and no null at the clock), no compander, no
    fixed ~3 kHz pair, so short Times are brighter than either pedal.
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
        # low-pass that has stopped moving (#157), so the low-pass holds no
        # Feedback's small value for ever and nothing is stepped clear
        # here. The cross-feed's own stall is closed below, by Spread's
        # grid.
        self._feedback = _between(self._value(FEEDBACK_I), 0.0, FEEDBACK_MAX)

        self._swing_ms = _between(self._value(MODULATION_I), 0.0,
                                  SWING_MAX_MS)
        # At one channel the node's cross-feed sends the repeat nowhere.
        # At two, Spread goes on the 1/4096 grid, where the loop's sum of
        # the two sides cannot land above both and hand a value back.
        if self._channel_count == 1:
            self._spread = 0.0
        else:
            self._spread = spread_on_grid(
                _between(self._value(SPREAD_I), 0.0, 1.0))
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
        low-pass's memory. Finite at every setting the class reaches, and
        with Spread on its grid it holds at every Spread in stereo."""
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
