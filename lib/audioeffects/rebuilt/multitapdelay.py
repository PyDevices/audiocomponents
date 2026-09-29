"""`MultiTapDelay` - one recording read by several heads on a fixed grid.

The player's text is the class docstring, and every sentence in it that
makes a claim is tied to a test by the `CLAIMS` table in the class's test
file. How it works, and why, is in the class's dossier in the workspace
repo (`docs/effects-internal/dossiers/MultiTapDelay.md`), and in the
docstrings of `_route`, `_wire` and `_resync` below.
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
    from .digitaldelay import laps_to_zero, whole_frames
except ImportError:                     # pragma: no cover - after it lands
    from ..digitaldelay import laps_to_zero, whole_frames

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
    (`audiodsp_feedback_delay.c:148` at v0.6.3rc1)."""
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
    (`audiodsp_multitap.c:32` at v0.6.3rc1), which truncates toward zero, so a peak x
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
    """A multi-head echo: one recording read by several heads on a grid.

    The heads of a multi-head tape echo, after the Roland Space Echo's
    multi-head modes: your dry signal passes untouched, and a pattern of
    echoes follows it.

    **The controls.**
    Time is the gap to head 1, landed on a whole frame, and head k sounds at
    exactly k times that gap.
    Heads is how many heads the grid has, and the pattern repeats once per
    trip past the farthest of them.
    Pattern picks which heads sound, from the twelve positions of the Roland
    RE-202's mode selector.
    Its last position sounds every head on the grid, not the RE-202's
    unpublished positions.
    The lap is the farthest head on the grid, sounded or not, so heads past
    the ones a position sounds lengthen the lap without sounding.
    Feedback sends the pattern round again, each lap quieter.
    Repeat Tone darkens each lap a little more than the one before, once per
    lap, never once per head.
    Tilt leans the pattern's levels towards the near heads or the far ones.
    Up to Mix 1 the dry passes at unity, and at Mix 2 the echoes play alone.
    On CircuitPython alone, a stereo dry's right lane reads one LSB hot on
    source values within 32 LSB of the rails.
    Mix 0 is a wire.
    Sync locks Time to Division of the host's beat, clamped to Time's span.
    With no host tempo, Time stays on the knob.
    Time runs from 20 to 400 ms, Heads from 3 to 8, Feedback from 0 to 0.95
    and Mix from 0 to 2.
    `max_lap_ms` (1600 by default, 540 at least) caps the lap: where a grid
    would pass it, Time comes down to fit.
    A click comes out on the frame it went in: there is no latency.
    A one-channel source gets the same effect on its one channel.
    The sample rate must be at least 12 825 Hz: below it the constructor
    raises `ValueError`.

    **Reset, Mix at zero and the tail.**
    The lines are not fed while Mix is 0, so a return from Mix 0 starts both
    lines empty.
    `reset()` empties both lines and returns to patch 0.
    Neither a reset nor a trip to Mix 0 drops a frame of your source or
    plays one twice, whatever size of buffer it hands out.
    `tail_samples` is an upper bound on how long the echoes take to reach
    exact zero once your input stops.
    The tail rings on while your source hands back nothing.

    **Limits shared by the family.**
    A control that jumps makes the output step: move it in small steps from
    the host if you need it smooth.
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
        # bare `audiocore.RawSample` hands back its whole array at once. It
        # is also what Mix 0 hands out (`_route`), so the source is read
        # through it, and only through it, at every Mix: whatever part of a
        # source buffer it holds plays next, whichever way the output goes.
        adapter = audioroute.MidSide(width=1.0, sample_rate=rate,
                                     channel_count=channels)
        adapter.play(self._source)
        # A MidSide with no source hands out one block of zeros per pull and
        # never finishes: what the tap node primes from, and what the
        # Splitter reads while the graph is wired and while `_resync` swaps
        # tap 1's pending block for zeros (`_route`).
        self._hush = audioroute.MidSide(width=1.0, sample_rate=rate,
                                        channel_count=channels)
        # The Splitter reads the adapter through a port, so `_wire` and
        # `_resync` can point it at `_hush` without touching the adapter:
        # a MidSide's `play()` drops the frames it holds, and the unread
        # rest of a long source buffer has to stay where it is.
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
        # What Mix 0 hands out (`_bypass`): the input adapter behind one
        # more width-1 MidSide, byte for byte, whose reset forwards nothing,
        # so a host resetting the output at Mix 0 leaves the adapter's
        # unread frames where they are, as the tail does above Mix 0. The
        # adapter hands it whole 256-frame blocks, so it never holds any.
        self._through = audioroute.MidSide(width=1.0, sample_rate=rate,
                                           channel_count=channels)
        self._through.play(adapter)

        self._adapter = adapter
        self._split = split
        self._dry = dry
        self._tap1 = tap1

        # The Mixer and the Splitter's side are not reset: a Mixer voice
        # resets its source recursively, which would reach the borrowed
        # source. The tap node's reset empties its line through
        # `audiocore.reset_buffer`; the lap node's `clear` empties its line
        # and loop filters. The feed port is not reset either: it would
        # forward the reset to whatever it points at. Nor is the input
        # adapter: what it holds is the source's own audio, not yet heard,
        # and a reset that dropped it would put every later frame early (a
        # source in 512-frame buffers, 256 frames) or play a bare
        # `RawSample` again from its first frame (`DeEsser` owns its
        # adapter the same way).
        self._own(self._through)
        self._own(self._tail)
        self._own(self._mixer, reset=False)
        self._own(self._tapnode)
        self._own(self._feed, reset=False)
        self._own(self._fd, reset=self._fd.clear)
        self._own(dry, reset=False)
        self._own(tap1, reset=False)
        self._own(split, reset=False)
        self._own(self._in, reset=False)
        self._own(adapter, reset=False)
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
        # The Feedback is handed as set. Up to audiodsp v0.6.2 the lap
        # node's loop low-pass could hold a small value for ever a hair
        # either side of 1 - 0.5 / k, and this class stepped the Feedback
        # clear of those windows; since v0.6.3rc1 the node lands a damping
        # state that has stopped moving (audiodsp#157), and `laps_to_zero`
        # counts that landing's one extra lap.
        loop = feedback
        decay = feedback if lean else 0.0

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

        Mix 0 hands the input adapter out through the port (`_bypass`, by
        way of `_through`), a width-1 MidSide that passes the source byte
        for byte, so it is a
        wire on every interpreter: CircuitPython's stock `audiomixer`
        scales a voice at level 1.0 by 32768 / 32767, which puts every
        sample at |value| >= 32736 one LSB out (audiodsp's own Mixer passes
        unity through). The source is read through the adapter at every
        Mix, so whatever part of a buffer it holds plays next either way.
        Nothing is pulled through the graph while the port is on the
        adapter, so nothing here may prime from it then: a `play()` would
        take a block away from the port. `_route_around` marks the graph
        stranded, and the return clears it through `_rejoin` (the base's
        stale-block helper) before `_resync`; the adapter is not reset by
        either, since it is registered without one.

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

        **Every wiring is quiet** where `audiocore.get_buffer` exists
        (`_wire`): the Splitter reads `_hush` while the voices prime, and
        one pull of the Mixer hands the primed zeros out, so the graph is
        left as it is between two pulls mid-stream and nothing is taken
        from the source. Up to re-audit fix round 1 a wiring outside
        `reset()` primed the dry voice with the source's first block, and
        a `_resync` before the first pull then dropped that block's heads
        (tap 1 held it, not yet heard) and, in mono on a native build,
        refilled the tap's own buffer the voice was pointing into, so the
        dry's first 256 samples played as zeros. Inside `reset()` the
        wiring is quiet on every build, because a reset must take nothing
        from the source.

        Where `get_buffer` is left out, a wiring outside `reset()` primes
        the source's first block into the dry voice, and nothing here can
        pull it out. The first pull plays it on time. A Mix-0 route before
        that pull hands out the adapter, which has already given that block
        away, so the run plays the source one block early without it; the
        voice keeps the block, and plays it at the return (or the reset)
        with tap 1's copy going into the lines, since `_resync` cannot swap
        it, so its heads follow it. A wiring inside `reset()` opens the
        output with the one silent block it primed, and a reset or a return
        from Mix 0 lets tap 1's pending block into the lines, its heads
        late by any Mix-0 run between. The module docstring says all of
        this in a host's terms.
        """
        if not self._ready:
            return
        if self._macros[MIX_I] <= 0.0:
            self._route_around(self._bypass())
            self._at_source = True
            return
        if not self._wired:
            self._wire(self._quiet_wiring())
            self._wired = True
        elif self._at_source or self._resetting:
            # The base's stale-block helper clears what `_route_around`
            # left (both lines and the tail); `_resync` clears the lines
            # again, which changes nothing, and swaps tap 1's block.
            self._rejoin()
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

    def _bypass(self):
        """What Mix 0 hands out: the input adapter, a width-1 MidSide that
        passes the source byte for byte in the palette's blocks, behind
        `_through`, which keeps a host's reset off it. Pointing the output
        at the source itself would skip whatever part of a source buffer
        the adapter holds (a source in 512-frame buffers jumps 256 frames
        ahead) and hand a bare `RawSample` out again from its first
        frame."""
        return self._through

    def _quiet_wiring(self):
        """Whether `_wire` primes the voices from `_hush`: wherever
        `audiocore.get_buffer` can hand the primed zeros out, and always
        inside `reset()`, which must take nothing from the source."""
        return self._resetting or \
            getattr(audiocore, "get_buffer", None) is not None

    def _wire(self, quiet=False):
        """Play every node once, the first time Mix is above 0 (`_route`).

        `quiet`: the Splitter reads `_hush` while the voices prime, so the
        dry voice primes zeros and tap 1's pending block is zeros, and one
        pull of the Mixer hands those zeros out. Nothing is taken from the
        source, and the graph is left as it is between two pulls
        mid-stream: no voice holds a block, the dry tap is caught up, and
        tap 1 is one block behind it. A voice that still held its primed
        block would point into a mono `SplitterTap`'s own buffer, which
        `_resync` refills, and tap 1 would hold audio whose dry had not
        played yet, which `_resync` drops."""
        pull = getattr(audiocore, "get_buffer", None)
        self._fd.play(self._tap1)
        self._feed.play(self._hush)
        self._tapnode.play(self._feed, loop=False)
        if quiet:
            self._in.play(self._hush)
        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._mixer.voice[0].play(self._dry, loop=False)
        self._mixer.voice[1].play(self._tapnode, loop=False)
        self._feed.play(self._target(self._lean))
        self._plugged = self._lean
        if quiet:
            self._in.play(self._adapter)
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
        source is taken and the tap node stays one block behind the dry.
        A quiet wiring (`_wire`) leaves tap 1 holding zeros and no voice
        holding a block, so right after construction this is that state
        too: the dry tap's pull refills no buffer a voice still points
        into, and what tap 1 drops was never audio."""
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
        return int(laps * (lap + 1 + memory) + lap)
