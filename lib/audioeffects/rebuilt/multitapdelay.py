"""`MultiTapDelay` - one recording read by several heads on a fixed grid.

Rebuilt from scratch for Phase 5 against
`workspace docs/effects-internal/dossiers/MultiTapDelay.md`, whose trait
table was frozen at Station A before this file existed (anchor commit
02e7e0c1467ff43b13ff239325eed54dd84b2dcb, the Station A revision's freeze,
2026-09-28). The old class in `delay.py` is consulted only for the six
defects that dossier's section 7 names; it stays the class the library
serves until the board runner adopts this one.

**What it sounds like.** Your dry signal passes untouched, and a pattern of
echoes follows it: the heads of a multi-head tape echo, each one the same
recording read further along. The heads sit on a grid of whole multiples of
one base time, so head 2 is exactly twice head 1 and head 3 exactly three
times. Time (20-400 ms) is that base, the gap to head 1. Heads (3-8) is how
many heads the grid has, and the pattern repeats once per trip past the
farthest of them. Pattern picks which heads sound, from the twelve
positions of the Roland RE-202's mode selector. Feedback (0-0.95) sends
the pattern round again, each lap quieter; Repeat Tone darkens each lap a
little more than the one before, once per lap, never once per head. Tilt
leans the pattern's levels towards the near heads or the far ones. Mix
(0-2) is the echo level: dry at unity up to 1, the echoes alone at 2, and
Mix 0 is a wire. Sync locks Time to Division of the host's beat.

**The standout:** the Roland RE-201 Space Echo's multi-head modes, with the
Binson Echorec as a second reference. You get the RE-201's three heads and
its one-knob grid as defaults; patch 3 is the Echorec's 74 ms head spacing
on four heads.

**The grid, exactly.** Time is landed on the nearest whole frame,
n1 = floor(t1 fs / 1000 + 0.5), and head k sounds at exactly k n1 frames.
The lap is P = K n1 frames for Heads K, clamped so it fits `max_lap_ms`:
at the default 1600 ms the base stops at 400 / 400 / 320 / 266.67 /
228.56 / 200 ms for 3 ... 8 heads. That clamp is on the audio path only and
`get_macro(0)` keeps the knob's Time, because it moves with Heads and a
Heads move back must give you your Time back. The tap node reads its input
one 256-frame block after the dry has played it (so that nothing you set
before the first pull, or right after `reset()`, lands on audio it has
already written; see `_route`), so it is handed (P + 0.5) frames' worth of
`delay_ms` and head k at (k n1 - 256 + 0.5) / P, and it truncates both:
every head sounds at exactly k n1 against the dry, and a single-precision
board lands on the same frames as a desktop. The lap node interpolates instead, so it is
handed the least single-precision `delay_ms` whose frames, computed the
node's way (`value * rate / 1000.0f`), are at or over P: stepping one
float32 unit at a time from float32(P 1000 / fs), every intermediate
rounded to float32, which is exact on the desktop and the identity on a
board. Where no float32 value lands on P exactly (some laps at 44.1 and
22.05 kHz) the read sits a few thousandths of a frame over P and puts that
fraction of each lap one frame late, inside the lap's own response, never
early.

**Pattern.** Modes 1-11 are S1's head sets, keeping only the heads that
exist on the grid: 1 = {1}, 2 = {2}, 3 = {3}, 4 = {1,2}, 5 = {2,3},
6 = {1,3}, 7 = {1,2,3}, 8 = {1,4}, 9 = {3,4}, 10 = {1,3,4}, 11 = {1,2,4}
(at three heads, modes 8-11 read {1}, {3}, {1,3}, {1,2}). **Mode 12 departs
from S1**: the RE-202's mode 12 puts its heads at "optimized" positions
that Roland does not publish, and this class puts mode 12 on the plain
grid, every head 1 ... K, instead (patch 4 is eight of them). Heads above 4
sound only in mode 12; in modes 1-11 they lengthen the lap without
sounding.

**Where the feedback is tapped is a design decision, not a source.** The
lap is the farthest head on the grid, sounded or not, as if the record
head were fed from head K. So in a mode that does not sound head K the
repeats keep the lap's rhythm, not the heads': mode 1 at three heads
sounds t1, 4 t1, 7 t1 ..., where a machine fed back from the sounding head
would give t1, 2 t1, 3 t1.

**Repeat Tone's out stop is a lighter graph.** With Repeat Tone in circuit
the laps go round an `audioecho.FeedbackDelay` whose in-loop low-pass is the
darkening (its corner pre-warped so it is the -3 dB point of one pass); at
the out stop the class unplugs that node and lets the tap node's own
`decay` make the laps, and nothing darkens. Crossing the out stop while
audio plays changes the graph between blocks by re-pointing a port, which
pulls nothing: the wet does not move against the dry, however many times
you cross between two pulls (a host flipping patches 1 and 0 included),
but the laps in flight are dropped or doubled once (up to half the click's
level at Feedback 0.5).

**Mix 0 hands your source straight through**, the class's output port
pointed at the source itself, so it is byte for byte a wire on every
interpreter. It departs from the dossier's section 6 there, which kept
both lines recording at Mix 0 through the Mixer: CircuitPython's stock
`audiomixer` scales a voice at level 1.0 by 32768 / 32767, so on
CircuitPython that route put every sample at |value| >= 32736 one LSB out
(audiodsp's own Mixer, the one MicroPython and the boards run, passes
unity through). The price is that the lines are not fed while Mix is 0,
and turning Mix up from 0 starts the echoes from empty lines. The same
stock Mixer is on the dry path above Mix 0. At one channel the class hands
the dry's unity as 1 - 2^-15, which every Mixer here passes exactly; at two
the stock Mixer's pan law leaves no level that is exact in both lanes, so
on CircuitPython alone the right lane's dry reads one LSB hot on the
source values within 32 LSB of the rails.

**Moving Time or Heads clicks.** Both nodes jump to the new grid, and in
stereo the tap node's planar line also crosses channels for up to one lap
(the right channel briefly replays what the left one wrote). Nothing about
the grid is claimed while Time or Heads moves with audio playing. A move
made before the first pull, or after `reset()` and before the next pull,
is not a move of that kind: the tap node's line holds only zeros then, so
the first lap lands on the grid in both lanes. That holds however many
times you call `reset()`, or take Mix to 0 and back, between two pulls.

**Portability tier: audiodsp** (`REQUIRES = ("audioecho", "audioroute")`).
The laps are `audioecho.FeedbackDelay` and the dry fan-out is
`audioroute.Splitter`; `audiodelays.MultiTapDelay` and `audiomixer.Mixer`
are stock. On a stock CircuitPython board this module imports cleanly and
construction raises `ImportError`.

**Sample rate: 12 825 Hz and up.** The tap node reads one block behind
the dry, so each head's offset is handed 256 frames short, and the 20 ms
head must land on more than 256 frames for that to place it. Below
12 825 Hz it would not, and the constructor raises `ValueError` rather
than build a class whose Time knob cannot reach its low end.

**Latency: zero samples, at every setting and patch, at every rate the
class accepts**, and after `reset()` from any graph, however many resets
and returns from Mix 0 land between two pulls: the dry stays at +0 and
every head at +k n1 against it. The dry is a Splitter tap into a Mixer
voice, a wire, and nothing looks ahead. The heads are the effect, not latency, and
no option adds any. The output ends in an `audioroute.MidSide` at width 1,
the identity, whose reset forwards nothing: a host that resets the output
(a mixer voice's `play()` does) no longer reaches the Mixer, whose voices
would re-prime from the Splitter and drop the source's first block. That
reset leaves the lines as they are; call `reset()` to empty them.

**Mono.** A one-channel source gets the same effect on its one channel.
There is no Spread: the tap node applies one set of heads to every
channel, so heads cannot be placed across the field.

**RAM at 48 kHz: about 655 KB** at the default `max_lap_ms` 1600: two lines
of 307 392 B (the lap node's is `max_lap_ms` + 1 ms of two int16 lanes
whatever the channel count; the tap node's is the same length times the
channel count, 153 696 B mono), plus the Splitter's ring (about 34 KB), the
Mixer and the small buffers. At 44.1 kHz each line is 282 416 B, at
22.05 kHz 141 208 B. Pass a lower `max_lap_ms` to spend less (800 ms makes
each line 153 792 B, and the base then stops at 800 / K ms). It has a
floor of 540 ms: below that some Heads leave Time dead or its span under
3.33 : 1. A `max_lap_ms` above 1600 or NaN is 1600.

**Cost, a planning estimate; the board measurement is pending hardware.**
Palette rows (MultiTapDelay, which ran four taps; FeedbackDelay +options;
Splitter, two taps; Mixer; MidSide, twice, the input adapter and the tail;
one Python pull of glue) put the full graph at **P4 <= 67 %, S3 <= 88 %**
of a 5.333 ms stereo block, which is over the S3's 80 % line, and the
lean graph (Repeat Tone out) at **P4 <= 59 %, S3 <= 74 %**. **On an S3, stack patch 1, `Three Heads,
Even - lean`, not patch 0**, and only with light classes: the tap node
alone is most of an S3 block. Every Repeat Tone-in setting, the defaults
included, is over the S3's line by this estimate. Eight sounding heads
(patch 4) cost more than any palette row has priced, and so may the long
lines on a PSRAM board.

**Input ceiling.** The heads sit at unity, and the tap node soft-limits at
+-28000 (on the heads' sum, on the line write and on its output), so the
echoes of a hot input are kneed while the dry is not: one head on a
30 000 LSB click reads 28 023. On the kit's `noise_det` at 48 kHz the
output reaches the int16 rail at no patch up to -6 dBFS peak; the wet
passes the knee at -12 dBFS only at patch 4 (eight heads) and patch 1, and
at patch 0 from -9 dBFS.

**Tail.** `tail_samples` is an upper bound, in frames, on how long the
echoes take to reach exact zero once your input stops, recomputed on every
Time, Heads, Feedback or Repeat Tone move. With Repeat Tone in it is
`DigitalDelay`'s bound for the lap node plus one lap for the tap node's
line, and the lap node is handed a Feedback just outside the windows where
its loop low-pass could hold a small value for ever (at most 0.00003 from
the one you set; 0.95 plays as 0.950016). With Repeat Tone out the tap node
truncates every lap toward zero, so the bound is (laps + 1) x P. At patch 0
it is 321 435 frames at 48 kHz (6.7 s).

`capabilities = ("tempo_sync",)`: with Sync on, the class reads
`self._transport()` on every macro move and program change (not per
block), and Time's knob is rewritten to Division x the beat, clamped to its
span. With no host transport, or a tempo that is not a finite positive
number, Time stays where the knob is.
"""

VENDOR = "PyDevices"

from array import array
import math
import struct

from .. import _component
from ..chorus import nominal_damping_hz

# DigitalDelay's tail arithmetic, reused rather than copied: the lap node
# is the same node and rounds the same way. Its module moves up one level
# when it comes home, so both homes are tried.
try:
    from .digitaldelay import clear_of_stalls, laps_to_zero, whole_frames
except ImportError:                     # pragma: no cover - after it lands
    from ..digitaldelay import clear_of_stalls, laps_to_zero, whole_frames

import audiocore

try:
    import audiodelays
    import audiomixer
except ImportError:                     # pragma: no cover - a bare build
    audiodelays = None
    audiomixer = None

try:
    import audioecho
    import audioroute
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None
    audioroute = None


#: Section 6's spans, fixed on every instance.
TIME_MIN_MS = 20.0
TIME_MAX_MS = 400.0
HEADS_MIN = 3
HEADS_MAX = 8
FEEDBACK_MAX = 0.95
TONE_MIN_HZ = 800.0
TONE_MAX_HZ = 16000.0

#: Tilt's span in dB from head 1 to head K at |Tilt| = 1 (ours).
TILT_DB = 12.0

#: `max_lap_ms`: 400 ms x four heads by default, and never under 540 ms,
#: where every Heads keeps Time alive and its span at 3.33 : 1 or more.
MAX_LAP_MS = 1600.0
MIN_LAP_MS = 540.0

#: The block every node renders, in frames.
BLOCK = 256

#: How far the tap node's own timeline runs behind the dry, in frames, and
#: so how much shorter than k n1 each head's offset is handed (`_route`).
#: Every offset k n1 - LAG must be at least one frame: an offset of 0 reads
#: the line a whole lap back, and a negative one is a position the node
#: refuses. The shortest head is Time's 20 ms, and the lap clamp never
#: lands n1 below it, so that holds exactly where 20 ms lands on more than
#: LAG frames: at MIN_SAMPLE_RATE and above (257 frames at 12 825 Hz, 441
#: at 22.05 kHz). The class refuses a lower rate at construction.
LAG = BLOCK

#: The lowest sample rate the class accepts: the least whole rate at which
#: Time's 20 ms lands on more than LAG frames, floor(20 fs / 1000 + 0.5).
MIN_SAMPLE_RATE = 12825

#: S1's `Head Combinations for Each Mode`, modes 1-11. Mode 12 is every
#: head on the plain grid (section 8.3), so it is not in the table.
HEAD_SETS = ((1,), (2,), (3,), (1, 2), (2, 3), (1, 3), (1, 2, 3), (1, 4),
             (3, 4), (1, 3, 4), (1, 2, 4))

#: Division's sixteen note values, in quarter-note beats, rising: 1/32,
#: 1/16T, 1/32., 1/16, 1/8T, 1/16., 1/8, 1/4T, 1/8., 1/4, 1/2T, 1/4., 1/2,
#: 1/1T, 1/2., 1/1 (`DigitalDelay`'s).
DIVISION_BEATS = (0.125, 1.0 / 6.0, 0.1875, 0.25, 1.0 / 3.0, 0.375, 0.5,
                  2.0 / 3.0, 0.75, 1.0, 4.0 / 3.0, 1.5, 2.0, 8.0 / 3.0, 3.0,
                  4.0)

#: The tap node truncates every sample it sends round toward zero; the
#: tail bound reckons with a decay this much larger, relatively, so a
#: board's single-precision arithmetic can only lengthen it.
DECAY_MARGIN = 2.0 ** -16

(TIME_I, PATTERN_I, HEADS_I, FEEDBACK_I, MIX_I, TILT_I, TONE_I, SYNC_I,
 DIVISION_I) = range(9)


def f32(value):
    """`value` rounded to single precision: exact emulation on a desktop,
    the identity on a board, whose float already is one."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _f32_step(value, up):
    """The next single-precision value above (or below) a positive one."""
    bits = struct.unpack("<I", struct.pack("<f", value))[0]
    bits += 1 if up else -1
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def lap_node_frames(value_ms, sample_rate):
    """The lap node's own arithmetic for a `delay_ms` it is handed,
    `value * rate / 1000.0f` in single precision
    (`audiodsp_feedback_delay.c:148` at v0.6.2)."""
    return f32(f32(f32(value_ms) * f32(sample_rate)) / f32(1000.0))


def lap_node_ms(lap, sample_rate):
    """The `delay_ms` the lap node is handed for a lap of `lap` frames: the
    least single-precision value whose frames, the node's way, are at or
    over `lap`. From float32(lap 1000 / fs), step up one float32 unit while
    the frames are under; if the start is already over, step down while
    the next value down is still at or over."""
    value = f32(lap * 1000.0 / sample_rate)
    frames = lap_node_frames(value, sample_rate)
    while frames < lap:
        value = _f32_step(value, True)
        frames = lap_node_frames(value, sample_rate)
    while frames > lap:
        lower = _f32_step(value, False)
        if lap_node_frames(lower, sample_rate) < lap:
            break
        value = lower
        frames = lap_node_frames(value, sample_rate)
    return value


def head_set(mode, heads, table=HEAD_SETS):
    """Pattern mode 1-12 on a grid of `heads` heads -> the heads that
    sound, rising. Mode 12 is every head 1 ... K."""
    if mode >= 12:
        return tuple(range(1, heads + 1))
    return tuple(k for k in table[mode - 1] if k <= heads)


def head_levels(selected, heads, tilt):
    """Tilt's law: a straight line in dB across the grid, `TILT_DB` x Tilt
    from head 1 to head K, far heads louder for Tilt > 0, with the loudest
    sounding head at exactly 1.0."""
    db = [TILT_DB * tilt * (k - 1) / (heads - 1) for k in selected]
    top = max(db)
    return tuple(1.0 if value == top else 10.0 ** ((value - top) / 20.0)
                 for value in db)


def landed(time_ms, heads, sample_rate, max_lap_ms):
    """(n1, P) in frames: the base on the nearest whole frame, clamped so
    the lap P = K n1 fits `max_lap_ms`."""
    n1 = max(1, whole_frames(time_ms, sample_rate))
    cap = int(math.floor(max_lap_ms * sample_rate / 1000.0)) // heads
    if n1 > cap:
        n1 = cap
    return n1, heads * n1


def trunc_laps(decay):
    """Laps of the tap node's own loop to exact zero from full scale. Once
    the input stops it writes `(int32_t)(delayed * decay)`
    (`audiodsp_multitap.c:32`), which truncates toward zero, so a peak x
    goes to floor(x d) < x and the count is finite at every decay."""
    decay = min(max(float(decay), 0.0), 1.0) * (1.0 + DECAY_MARGIN)
    laps = 0
    peak = 32768
    while peak > 0:
        laps += 1
        image = int(math.floor(decay * peak))
        if image >= peak:
            image = peak - 1
        peak = image
    return laps


def tone_excess(damping_hz, sample_rate):
    """`DigitalDelay._tone_excess` for a pre-warped `damping_hz`: (memory
    frames, relative excess) of the lap node's loop low-pass, (0, 0.0)
    with it out."""
    if damping_hz <= 0.0:
        return 0, 0.0
    per_frame = 2.0 * math.pi * damping_hz / sample_rate
    coefficient = 1.0 - math.exp(-per_frame)
    frames = int(math.ceil(32.0 * math.log(2.0) / per_frame))
    return frames, 2.0 ** -17 + 2.0 ** -24 / coefficient


def _number(value, default):
    """`value` as a float, or `default` for NaN or something that is not a
    number."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return float(default)
    if value != value:
        return float(default)
    return value


class MultiTapDelay(_component.Component):
    """A multi-head echo: several heads on a grid of whole multiples of one
    base time, S1's twelve head sets, laps that darken once per lap.
    audiodsp tier; zero latency.

    **What the default surrenders:** mode 12 is the plain grid, not the
    RE-202's unpublished "optimized" heads; the feedback is taken from the
    farthest head on the grid by decision; Time and Heads click when they
    move; and on an ESP32-S3 every Repeat Tone-in setting, the defaults
    included, is over the 80 % cost line by the palette estimate, so the
    S3 build is patch 1 (Repeat Tone out).
    """

    NAME = 'MultiTapDelay'
    DISPLAY_NAME = 'Multi-Tap Delay'
    CATEGORIES = ('Delay',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho", "audioroute")

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Time", "Pattern", "Heads", "Feedback", "Mix", "Tilt",
                    "Repeat Tone", "Sync", "Division")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "BIPOLAR",
        6: "UNIPOLAR",
        7: "TOGGLE",
        8: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (TIME_MIN_MS, TIME_MAX_MS, "log"),  # 0  Time, the base head t1, ms
        (0.0, 11.0),                        # 1  Pattern index -> mode 1-12
        (float(HEADS_MIN), float(HEADS_MAX)),  # 2  Heads K
        (0.0, FEEDBACK_MAX),                # 3  Feedback, the lap level
        (0.0, 2.0),                         # 4  Mix; dry at unity to 1
        (-1.0, 1.0),                        # 5  Tilt
        (TONE_MIN_HZ, TONE_MAX_HZ, "log"),  # 6  Repeat Tone, Hz; top = out
        (0.0, 1.0),                         # 7  Sync
        (0.0, 15.0),                        # 8  Division index
    )

    #: `_component.macro_of` of the dossier's section 6 settings; patch 0
    #: is the constructor's defaults on the grid.
    PATCHES = {
        0: ("Three Heads, Even", (85, 69, 0, 60, 22, 64, 68, 0, 25)),
        1: ("Three Heads, Even - lean", (85, 69, 0, 60, 22, 64, 127, 0, 25)),
        2: ("Two Heads, Near Loudest", (93, 35, 25, 67, 22, 32, 68, 0, 25)),
        3: ("Four Heads, Far Loudest", (55, 127, 25, 67, 22, 96, 78, 0, 25)),
        4: ("Eight Heads, Dense", (29, 127, 127, 74, 19, 64, 56, 0, 25)),
        5: ("One Head, Long Repeats", (76, 23, 0, 94, 22, 64, 48, 0, 25)),
        6: ("Triplet Grid, Synced", (85, 69, 0, 60, 22, 64, 68, 127, 34)),
    }

    #: The head-set table a Pattern position reads (S1's, modes 1-11).
    _SETS = HEAD_SETS

    def _build(self, time_ms=150.0, pattern=7, heads=3, feedback=0.45,
               mix=0.35, tilt=0.0, tone_hz=4000.0, sync=False, division=3,
               max_lap_ms=MAX_LAP_MS, patch=None):
        rate = self._sample_rate
        channels = self._channel_count
        self._check_rate(rate)
        max_lap_ms = _number(max_lap_ms, MAX_LAP_MS)
        if max_lap_ms > MAX_LAP_MS:
            max_lap_ms = MAX_LAP_MS
        if max_lap_ms < MIN_LAP_MS:
            max_lap_ms = MIN_LAP_MS
        self._max_lap_ms = max_lap_ms

        # Constructor values in the macros' own units. A value outside a
        # span clamps to the nearer stop (`macro_position` does that), NaN
        # takes the default, and a Time of 0 or less is the bottom of its
        # span, which a log knob cannot seed. Repeat Tone at 0 or less is
        # its out stop, as it is on the node.
        time_ms = _number(time_ms, 150.0)
        if not time_ms > 0.0:
            time_ms = TIME_MIN_MS
        tone_hz = _number(tone_hz, 4000.0)
        if not tone_hz > 0.0:
            tone_hz = TONE_MAX_HZ
        pattern = int(math.floor(_number(pattern, 7) + 0.5))
        pattern = min(12, max(1, pattern))
        heads = int(math.floor(_number(heads, HEADS_MIN) + 0.5))
        heads = min(HEADS_MAX, max(HEADS_MIN, heads))

        #: What the nodes were last handed, so a move writes only what it
        #: changes (a `delay_ms` write re-bases the tap node's line).
        self._tap_ms = None
        self._taps = None
        self._n1 = 1
        self._lap = HEADS_MIN
        self._heads = heads
        self._selected = ()
        self._levels = ()
        self._lap_ms = 0.0
        self._feedback = 0.0
        self._lap_mix = 0.0
        self._decay = 0.0
        self._damping = 0.0
        self._lean = False
        #: Which node the tap node is playing: None until the graph is
        #: wired, then True (the Splitter's tap, the lean graph) or False
        #: (the lap node).
        self._plugged = None
        #: True once the Mixer's voices and the tap node have been played,
        #: which happens the first time Mix is above 0.
        self._wired = False
        #: True while Mix 0 has the output port on the borrowed source.
        self._at_source = False
        self._deferred = False
        #: True inside `reset()`, where a `play()` must not reach the
        #: borrowed source (`_route`).
        self._resetting = False

        # The input adapter re-blocks whatever the app hands the class into
        # the palette's own blocks, which `audioroute.Splitter` needs: a
        # bare `audiocore.RawSample` hands back its whole array at once.
        adapter = audioroute.MidSide(width=1.0, sample_rate=rate,
                                     channel_count=channels)
        adapter.play(self._source)
        # A MidSide with no source hands out one block of zeros per pull and
        # never finishes: what the tap node primes from, what the input
        # adapter reads while a reset wires the graph, and what the Splitter
        # reads while `_resync` swaps tap 1's pending block for zeros
        # (`_route`).
        self._hush = audioroute.MidSide(width=1.0, sample_rate=rate,
                                        channel_count=channels)
        # The Splitter reads the adapter through a port, so `_resync` can
        # point it at `_hush` for two pulls without touching the adapter
        # (whose unread rest of a long source buffer stays where it is).
        self._in = audioroute.Port(adapter)
        split = audioroute.Splitter(self._in, taps=2)
        dry = split.tap(0)
        tap1 = split.tap(1)
        self._silence = audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels)
        # The tap node always plays this port; the graph's two shapes are
        # the port pointed at the lap node or at the Splitter's tap, and a
        # re-point is one store that pulls nothing.
        self._feed = audioroute.Port(self._hush)

        # The laps: the lap node recirculates at P with the darkening in
        # its loop. Its `mix` is the Feedback, so its output is the dry plus
        # Feedback x the loop: lap 1 at unity, lap n at Feedback^(n - 1).
        self._fd = audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=channels,
            max_delay_ms=max_lap_ms + 1.0,
            delay_ms=max_lap_ms * 0.5, feedback=0.0, mix=0.0,
            damping_hz=0.0, cut_hz=0.0, delay_slew=0.0)
        # The heads: wet only (`mix` 1.0 in its 0..1 convention, doubled to
        # 2 in the node), 256 frames a pull.
        self._tapnode = audiodelays.MultiTapDelay(
            max_delay_ms=int(math.ceil(max_lap_ms)) + 1,
            delay_ms=max_lap_ms * 0.5, decay=0.0, mix=1.0,
            taps=((1.0, 1.0),), buffer_size=BLOCK * channels * 2,
            sample_rate=rate, bits_per_sample=16, samples_signed=True,
            channel_count=channels)
        self._mixer = audiomixer.Mixer(
            voice_count=2, buffer_size=BLOCK * channels * 4,
            channel_count=channels, bits_per_sample=16, samples_signed=True,
            sample_rate=rate)
        # The tail: a MidSide at width 1 is the identity, byte for byte, and
        # its reset forwards nothing upstream. A host that resets the
        # output (a mixer voice's `play()` does) would otherwise reach the
        # Mixer, whose voices re-prime from the Splitter's taps and throw
        # away the source's block they already hold (`_route`).
        self._tail = audioroute.MidSide(width=1.0, sample_rate=rate,
                                        channel_count=channels)
        self._tail.play(self._mixer)

        self._adapter = adapter
        self._split = split
        self._dry = dry
        self._tap1 = tap1

        # The Mixer and the Splitter's side are not reset: a Mixer voice
        # resets its source recursively, which would reach the borrowed
        # source. The tap node's reset empties its line through
        # `audiocore.reset_buffer`; the lap node's `clear` empties its line
        # and loop filters. The feed port is not reset either: it would
        # forward the reset to whatever it points at.
        self._own(self._tail)
        self._own(self._mixer, reset=False)
        self._own(self._tapnode)
        self._own(self._feed, reset=False)
        self._own(self._fd, reset=self._fd.clear)
        self._own(dry, reset=False)
        self._own(tap1, reset=False)
        self._own(split, reset=False)
        self._own(self._in, reset=False)
        self._own(adapter)
        self._own(self._hush, reset=False)
        self._own(self._silence, reset=False)
        self._output = self._tail

        self._ready = False
        self._init_macros((time_ms, float(pattern - 1), float(heads),
                           feedback, mix, tilt, tone_hz,
                           1.0 if sync else 0.0, _number(division, 3)),
                          patch)

        self._ready = True
        self._route()

    def _check_rate(self, rate):
        """Refuse, before anything is built, a rate at which the shortest
        head would be handed an offset of 0 or less (`LAG`)."""
        if whole_frames(TIME_MIN_MS, rate) <= LAG:
            raise ValueError(
                "MultiTapDelay needs a sample rate of at least %d Hz (got "
                "%d): below it the 20 ms head is %d frames or fewer, which "
                "the tap node's one-block lag cannot place"
                % (MIN_SAMPLE_RATE, rate, LAG))

    # -- the maps ------------------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _pattern_mode(self):
        """Pattern's position -> mode 1-12: index floor(11 p + 0.5)."""
        index = int(math.floor(11.0 * self._macros[PATTERN_I] + 0.5))
        return min(12, max(1, index + 1))

    def _heads_count(self):
        """Heads' position -> K = floor(3 + 5 p + 0.5), 3-8."""
        count = int(math.floor(HEADS_MIN + (HEADS_MAX - HEADS_MIN)
                               * self._macros[HEADS_I] + 0.5))
        return min(HEADS_MAX, max(HEADS_MIN, count))

    def _head_set(self, mode, heads=None):
        return head_set(mode, self._heads_count() if heads is None
                        else heads, type(self)._SETS)

    def _tone_damping(self):
        """Repeat Tone -> the lap node's `damping_hz`, pre-warped so one
        pass is -3 dB at the knob's corner after the Nyquist clamp. The
        top stop is exactly 0: out of circuit, the lean graph."""
        if self._macros[TONE_I] >= 1.0:
            return 0.0
        return nominal_damping_hz(self._hz(self._value(TONE_I)),
                                  self._sample_rate)

    def _synced_ms(self):
        """Division x the host's beat, or `None` with no host transport
        (the static one) or a tempo that is not a finite positive number,
        where Time stays on the knob."""
        transport = self._transport
        if transport is _component.static_transport:
            return None
        state = transport() if callable(transport) else transport
        try:
            bpm = float(state[2] or 0.0)
        except (TypeError, ValueError, IndexError):
            return None
        if not bpm > 0.0 or bpm * 0.0 != 0.0:
            return None
        index = int(round(self._value(DIVISION_I)))
        index = min(len(DIVISION_BEATS) - 1, max(0, index))
        return DIVISION_BEATS[index] * 60000.0 / bpm

    def _tap_node_ms(self, lap):
        """The tap node's `delay_ms` for a lap of `lap` frames: half a
        frame over, so its truncation lands on `lap` in either float
        width."""
        return (lap + 0.5) * 1000.0 / self._sample_rate

    def _tap_positions(self, selected, n1, lap):
        """Head k at (k n1 - LAG + 0.5) / P, so the node's truncation of
        the offset lands on k n1 - LAG: the tap node reads its input one
        block after the dry has played it (`_route`), so each head sounds
        at exactly k n1 against the dry."""
        return tuple((k * n1 - LAG + 0.5) / lap for k in selected)

    def _lap_node_ms(self, lap):
        return lap_node_ms(lap, self._sample_rate)

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        del index, position
        if not self._deferred:
            self._refresh()

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index` whole, then refresh once, so Time is never
        read against the outgoing patch's Sync and the graph re-plugs at
        most once."""
        self._deferred = True
        try:
            _component.Component.program_change(
                self, index, channel, note_id, sample_position)
        finally:
            self._deferred = False
        if type(self).PATCHES.get(index) is not None:
            self._refresh()

    def _refresh(self):
        rate = self._sample_rate
        if self._macros[SYNC_I] >= 0.5:
            synced = self._synced_ms()
            if synced is not None:
                synced = min(TIME_MAX_MS, max(TIME_MIN_MS, synced))
                self._macros[TIME_I] = _component.macro_position(
                    self._MACRO_RANGES[TIME_I], synced)
        heads = self._heads_count()
        n1, lap = landed(self._value(TIME_I), heads, rate, self._max_lap_ms)
        selected = self._head_set(self._pattern_mode(), heads)
        levels = head_levels(selected, heads, self._value(TILT_I))
        taps = tuple(zip(self._tap_positions(selected, n1, lap), levels))

        feedback = self._value(FEEDBACK_I)
        feedback = min(FEEDBACK_MAX, max(0.0, feedback))
        lean = self._macros[TONE_I] >= 1.0
        damping = self._tone_damping()
        if lean:
            loop = feedback
            decay = feedback
        else:
            # With Repeat Tone in, the lap node can hold a small value for
            # ever at Feedback values a hair either side of 1 - 0.5 / k; it
            # is handed the nearer edge of that window instead.
            loop = clear_of_stalls(feedback,
                                   tone_excess(damping, rate)[1])
            decay = 0.0

        tap_ms = self._tap_node_ms(lap)
        lap_ms = self._lap_node_ms(lap)
        if tap_ms != self._tap_ms:
            self._tapnode.delay_ms = tap_ms
            self._tap_ms = tap_ms
        if taps != self._taps:
            self._tapnode.taps = taps
            self._taps = taps
        self._tapnode.decay = decay
        self._fd.set(delay_ms=lap_ms, feedback=loop, mix=loop,
                     damping_hz=damping, cut_hz=0.0, delay_slew=0.0)
        #: The lap node's `mix`, which is its Feedback (dossier section 4).
        self._lap_mix = loop
        mix = self._value(MIX_I)
        self._mixer.voice[0].level = self._dry_level(mix)
        self._mixer.voice[1].level = min(1.0, mix)

        self._n1 = n1
        self._lap = lap
        self._heads = heads
        self._selected = selected
        self._levels = levels
        self._lap_ms = lap_ms
        self._feedback = loop
        self._decay = decay
        self._damping = damping
        self._lean = lean
        self._route()

    def _dry_level(self, mix):
        """The dry voice's level, min(1, 2 - Mix). At one channel unity is
        handed as 1 - 2^-15, which every Mixer this class meets passes
        through exactly: CircuitPython's stock `audiomixer` turns a level
        of 1.0 into 32768 / 32767 and puts the samples nearest the rails
        one LSB hot, while 32767 / 32767 is 1. Two channels cannot do that
        (the stock Mixer's pan law hands the left lane 32767 x level >> 15,
        so 1 - 2^-15 is one LSB cold there), so they keep 1.0, and on
        CircuitPython alone their right lane is the hot one."""
        level = min(1.0, 2.0 - mix)
        if level >= 1.0 and self._channel_count == 1:
            return 1.0 - 2.0 ** -15
        return level

    def _route(self):
        """Where the output port points, and what the tap node reads.

        Mix 0 hands the borrowed source straight back through the port, so
        it is a wire on every interpreter: CircuitPython's stock
        `audiomixer` scales a voice at level 1.0 by 32768 / 32767, which
        puts every sample at |value| >= 32736 one LSB out (audiodsp's own
        Mixer passes unity through). Nothing is pulled through the graph
        while the port is on the source, so nothing here may prime a node
        then: a `play()` would take a block of the source away from the
        port.

        **The tap node runs one block behind the dry.** A Mixer voice's
        `play()` primes one block from its source, and the voices hand
        that block out on the first pull, so whatever the tap node renders
        at wiring is rendered with the settings of that moment. If that
        were the source's first block, a Time or Heads move before the
        first pull would re-base the tap node's planar line under it, and
        in stereo the right lane would lose its first block's heads. So
        the tap node primes a block of zeros instead (it plays `_feed`,
        pointed at `_hush`), renders those zeros for the wet voice's
        prime, and only then is the port pointed at the lap node or the
        Splitter's tap, which pulls nothing. The source's first block
        reaches the tap node's line on the second pull, with whatever the
        settings are by then; every head is handed LAG frames short
        (`_tap_positions`), so it still sounds at exactly k n1 against the
        dry, and the Splitter's tap 1 always holds the one block the tap
        node has not reached yet.

        Crossing Repeat Tone's out stop re-points the port (and empties
        the lap node going in), which pulls nothing, so any number of
        crossings between two pulls leaves the wet where it was against the
        dry. Coming back from Mix 0, and in `reset()`, `_resync` empties
        both lines and swaps that one pending block on tap 1 for a block of
        zeros (the Splitter reads `_hush` for one pull of each tap), so no
        audio from before either reaches the lines, nothing is taken from
        the source, and a second or third `_resync` before the next pull
        leaves exactly what the first did.

        A reset that has to wire the graph (a class never wired at Mix 0)
        must not pull the source either: the input adapter plays `_hush`
        while the voices prime, so the dry's primed block and tap 1's
        pending block are zeros, and one pull of the Mixer then hands the
        dry's zeros out, so the next pull reads the source's next block on
        time. That pull needs `audiocore.get_buffer`; where a build leaves
        it out, the output after such a reset opens with that one silent
        block, and a reset or a return from Mix 0 lets tap 1's pending block
        into the lines.
        """
        if not self._ready:
            return
        if self._macros[MIX_I] <= 0.0:
            self._output = self._source
            self._at_source = True
            return
        if not self._wired:
            self._wire(self._resetting)
            self._wired = True
        elif self._at_source or self._resetting:
            self._resync()
        elif self._lean != self._plugged:
            self._plug(self._lean)
        self._at_source = False
        self._output = self._tail

    def reset(self):
        """Empty both lines and restore patch 0, without pulling the
        borrowed source (`_route`)."""
        self._check_live()
        self._resetting = True
        try:
            _component.Component.reset(self)
        finally:
            self._resetting = False

    def _target(self, lean):
        """What the feed port points at: the Splitter's tap (the lean
        graph, the tap node's own `decay` making the laps) or the lap
        node."""
        return self._tap1 if lean else self._fd

    def _wire(self, quiet=False):
        """Play every node once, the first time Mix is above 0 (`_route`).
        `quiet` inside `reset()`: nothing is taken from the source."""
        pull = getattr(audiocore, "get_buffer", None)
        self._fd.play(self._tap1)
        self._feed.play(self._hush)
        self._tapnode.play(self._feed, loop=False)
        if quiet:
            self._adapter.play(self._hush)
        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._mixer.voice[0].play(self._dry, loop=False)
        self._mixer.voice[1].play(self._tapnode, loop=False)
        self._feed.play(self._target(self._lean))
        self._plugged = self._lean
        if quiet:
            self._adapter.play(self._source)
            if pull is not None:
                pull(self._mixer)

    def _resync(self):
        """Empty both lines and swap the block tap 1 holds for the tap node
        for a block of zeros, the same however many times it runs between
        two pulls (`_route`).

        With the Splitter reading `_hush`, one pull of tap 1 then one of the
        dry tap always leaves tap 0 caught up and tap 1 one block of zeros
        behind it. From the usual state (tap 1 holding the source's last
        block, tap 0 caught up) the first pull drops that block and the
        second writes the zeros. From the state this leaves, a second call
        reads those zeros back and writes them again, so nothing of the
        source is taken and the tap node stays one block behind the dry."""
        pull = getattr(audiocore, "get_buffer", None)
        self._fd.clear()
        audiocore.reset_buffer(self._tapnode)
        if pull is not None:
            self._in.play(self._hush)
            try:
                pull(self._tap1)
                pull(self._dry)
            finally:
                self._in.play(self._adapter)
        self._feed.play(self._target(self._lean))
        self._plugged = self._lean

    def _plug(self, lean):
        """Point the feed port at the Splitter's tap or at the lap node,
        emptying the lap node going in. A store: nothing is pulled, so the
        dry is never disturbed and the wet does not move against it."""
        if not lean:
            self._fd.clear()
        self._feed.play(self._target(lean))
        self._plugged = lean

    # -- the contract's reads ------------------------------------------

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops,
        as an upper bound.

        Repeat Tone in: `laps_to_zero(f', excess) x (P + 1 + memory) + P`,
        `DigitalDelay`'s bound for the lap node at the Feedback it is
        handed, plus one lap for the tap node's line to be read out.
        Repeat Tone out: `(trunc_laps(f) + 1) x P`, the tap node's own
        truncating loop. Finite at every setting.
        """
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        lap = self._lap
        if self._macros[MIX_I] <= 0.0:
            return 0
        if self._lean:
            return int((trunc_laps(self._decay) + 1) * lap)
        memory, excess = tone_excess(self._damping, self._sample_rate)
        laps = laps_to_zero(self._feedback, excess)
        if laps is None:                # pragma: no cover - cleared above
            return None
        return int(laps * (lap + 1 + memory) + lap)
