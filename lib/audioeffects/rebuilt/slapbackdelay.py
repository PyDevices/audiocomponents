"""`SlapbackDelay` - one tape repeat at 135 ms, in mono, the Sun Studio slap.

Rebuilt from scratch for Phase 5 against
`workspace docs/effects-internal/dossiers/SlapbackDelay.md`, whose trait
table was frozen at Station A before this file existed (anchor commit
7a5a4cbd8a734ea3df6ae8b8b04e32e763a15b5a, the Station A critique's
re-freeze, 2026-09-27). The old class in `delay.py` is consulted only for
the seven defects that dossier's section 7 names. This class was adopted
on 2026-09-28, and `audioeffects.SlapbackDelay` serves it.

**What it sounds like.** Your dry signal passes untouched, and one copy of
it comes back 135 ms later, from the same place, a little quieter: the
two-machine tape echo on the 1955 Sun sides, which Halmrast measured at
134-137 ms, one repeat, mono. Time (40-250 ms) is the head spacing over the
tape speed. Level (0-2) is the console return: dry at unity up to 1, the
repeat alone at 2, and Level 0 is a wire while the line keeps recording.
Saturation is how hard the return drove the record amplifier; it colours
the repeat and never the dry. Tone is the tape path's top end, out of
circuit by default. Wow is the transport's slow wobble, in cents at a fixed
0.7 Hz. Repeats sends the slap back round for a second and third; the Sun
rig had no feedback path, so it defaults to 0.

**The standout:** Sam Phillips' two-Ampex-350 slapback at Sun Studio, as
measured on *Baby Let's Play House* and *Tryin' to Get to You*. You get its
time, its single repeat and its mono placement as defaults, and its tape
colours as knobs.

**Portability tier: audiodsp** (`REQUIRES = ("audioecho",)`). The stock
`audiodelays.Echo` limits its only output at +-28000, so its Mix 0 is not
a wire. On a stock CircuitPython board this module imports cleanly and
construction raises `ImportError`.

**Latency: zero samples, at every setting and every rate.** Nothing looks
ahead. The 135 ms is the repeat, not latency on the dry path, and no option
adds any.

**Mono.** The repeat sits exactly where the dry sits: on a source identical
in both channels the output is identical in both channels, at every knob
position. A one-channel source gets the identical effect on its one channel,
sample for sample the left channel of a stereo render. The class never
passes `input_pan`, and it has no width, spread or pan knob, and never will.

**RAM.** A fixed line of 251 ms (Time's top plus 1 ms) of two int16 lanes
whatever the channel count: 48 192 B at 48 kHz, 44 276 B at 44.1 kHz,
22 136 B at 22.05 kHz, plus about 1.2 KB of node. No option sizes it.

**Cost.** One `audioecho.FeedbackDelay` with `delay_slew`, wow and
`loop_drive` on; no mixer. Palette row FeedbackDelay +options (the nearest
not-cheaper row; no row prices `loop_drive`), glue 0: **P4 <= 9 %,
S3 <= 15 %** of a 5.333 ms stereo block. Measured on both boards on
2026-09-28 at every shipped patch, with the tool's control in the same
conditions as the palette row: the P4 at most 0.396 ms, 7.4 % (rt 5.82 or
better); the S3 0.781-0.783 ms, 14.6-14.7 %, at the default and patches
0-4, and 0.813 ms, 15.2 %, at patch 5, the one patch with Tone in
circuit (rt 3.08 or better). Brad passed patch 5 against the 15 % bar on
2026-09-28; alone on an S3 the class leaves about 85 % of the block for
everything else. All seven patch digests are identical on both boards and
differ from the desktop's, because the Wow depth is worked out in Python
in a board's single precision (`wow_depth_ms` 2.1 x 10^-5 to
6.8 x 10^-5 ms high, under 0.0001 cent; patch 4's Feedback also one
float32 step off).

**What the default surrenders.** The default is Tone out, so the repeat is
as bright as the dry: an Ampex 350 at 15 ips rolls off at 15 kHz and at
7.5 ips lower still, and the Tone knob (patch 5, Dark Slap) is how you get
there. Wow is on at 1 cent, and wow moves the read head between samples, so
the repeat's top end breathes: at 48 kHz a 15 kHz tone in the repeat swings
between -0.03 and -5.11 dB (mean -2.61 dB) about 25 times a second; at
44.1 kHz between -0.02 and -6.38 dB (mean -3.35 dB). With Wow at 0 every
static Time is handed to the node as the nearest whole frame at the
running rate, so the default 135 ms is 6 480 frames at 48 kHz and 5 954
frames (135.011 ms) at 44.1 kHz, not the 5 953.5 that would cost the
repeat 6.35 dB at 15 kHz for as long as it played. At 48 kHz the node
lands every one of the 128 Time positions exactly on that frame, and the
repeat loses nothing.

At 44.1 and 22.05 kHz it does not always. The node turns the milliseconds
back into frames in float32, and for some Times no float32 value lands on
the whole frame, so the read sits one float32 step off it. Among the 128
Time positions that is 21 at 44.1 kHz (MIDI 4, 8, 9, 10, 11, 38, 39, 40,
41, 49, 50, 53, 55, 60, 83, 86, 91, 93, 96, 99, 102) and 20 at 22.05 kHz
(MIDI 8, 10, 34, 38, 39, 40, 41, 45, 53, 60, 81, 83, 86, 91, 93, 96, 97,
98, 99, 102), at most 1/2048 of a frame off at 44.1 kHz and 1/4096 at
22.05 kHz. Of the 9 262 whole frames a constructor `time_ms` reaches
from 40 to 250 ms, 1 159 land off at 44.1 kHz, and 579 of 4 632 at
22.05 kHz, up to 1/1024 and 1/2048 of a frame. None do at 48 kHz, nor the
default 135 ms or any shipped patch's Time at any rate. There the repeat
puts a sliver on the frame beside it: a 20 000 click's repeat reads
19 618 and 10 at MIDI 60, 44.1 kHz (19 623 and 5 at 22.05 kHz), against
19 627 on the frame (the default Saturation's own loss). The class cannot
hand the node a number that lands there; a node change is asked for.

**Saturation** is the node's cubic soft clip on the repeat, applied again on
each pass when Repeats is up. On the repeat of a -6 dBFS tone the default
0.15 adds a third harmonic at -50.0 dB re the fundamental and takes the
fundamental down 0.08 dB; 1.0 puts the third at -33.1 dB and the
fundamental at -0.56 dB. There is no second harmonic.

**Turning Time while it plays** walks the repeat to the new time at a fixed
0.1875 delay-seconds per second, instead of clicking: the repeat bends
+297.5 cents while Time falls and -359.5 cents while it rises, and
135 -> 85 ms takes 267 ms. There is no Glide knob; a slap's time is set,
not played.

**Turning Wow while it plays glides.** Since audiodsp v0.6.3rc1 the node
ramps a new wow depth in over 20 ms (audiodsp#160), so the repeat bends
for those 20 ms instead of jumping. On a 997 Hz tone at 12 000 LSB,
Level 2, 48 kHz, a Wow move from grid 36 to 73 or from 0 to 127 steps the
output by no more than the tone's own largest step, 1 564 LSB, anywhere
in the 2 000 frames after it (up to v0.6.2 the same moves stepped 7 684
and 23 037). While the depth travels, the extra pitch is the change over
20 ms times where the 0.7 Hz cycle is: 0 to 127 is 0.46 ms, up to 2.3 %
at the cycle's crest for those 20 ms. A patch change that moves Wow is a
click only as far as its Level jump makes it: patch 0 to patch 2
(Doubling), tried on every block boundary of that tone, steps up to 3 416
LSB against patch 0's own 2 106 at 48 kHz (3 569 against 2 292 at
44.1 kHz; 5 503 and 5 680 at v0.6.2), and 3 414 with Wow held at patch 0's,
so what is left is the Level moving at once, not the Wow.

**Tone out is out, after Tone has been in too.** Bring Tone back in after
the repeat has died away and nothing plays: 0 LSB at 48, 44.1 and
22.05 kHz, stereo and mono, after a 300 Hz tone at 30 000 LSB with Tone at
2 kHz. The out stop hands the node exactly 0, and since audiodsp v0.6.3rc1
the node keeps an out low-pass's state on the signal (audiodsp#158), so
Tone out after Tone in renders the same bytes as a fresh instance's Tone
out. Up to v0.6.2 the node froze that state and played it back; this class
cured it with a tracking out stop, 1 LSB off the filter truly out in
places, and the cure came out when the node was fixed.

**A host that echoes Time back** (`set_macro(0, get_macro(0))`) keeps the
constructor's exact Time: the 44.1 kHz default stays on 5 954 frames.
Any other Time position lands the knob's own value, and that includes a
restore: save `get_macro(0)`, move Time, write the saved value back, and
the 44.1 kHz default comes back on 5 953 frames, one short.

**Tone at a low rate.** The knob's corners clamp below Nyquist at the
running rate. At 22.05 kHz grid positions 94-126 all sit on the 10 804.5 Hz
clamp and do the same thing, and position 127 takes the filter out. At 44.1
and 48 kHz every position moves.

**Input ceiling.** The dry path sits at unity and the repeat adds to it,
and there is no input gain to turn down. Measured on the kit's `noise_det`
at 48 kHz over 4 s, the defaults put no sample on the rail from -2.5 dBFS
peak down (at -2.4 they rail 14 samples), and the shipped patches from
-3.4 dBFS (patch 2, Doubling, the first to rail) down.

**Tail.** `tail_samples` is an upper bound on how long the output takes to
reach exact zero after your input stops: one lap of the line at Repeats 0
(6 488 frames at the defaults, 48 kHz), 11 laps at 0.35, 21 at the 0.6
stop. With Tone in circuit, at a Repeats a hair either side of 0.5 (which
the span reaches), the loop low-pass can rest a hair above 1 LSB and hand
it back; up to audiodsp v0.6.2 it did so for ever and the class moved
Repeats clear of it. Since v0.6.3rc1 the node sets a stalled low-pass onto
its input (audiodsp#157), Repeats is handed as set, the bound counts one
more lap there, and the tail reaches exact zero inside it.

`capabilities = ()`: a slapback's time is a fixed distance over a fixed
tape speed, with no musical relationship to a tempo, so the class never
reads `self._transport()`.

A constructor value stays on the audio path unrounded by the knob's grid;
Time is then landed on a whole frame. A value outside a knob's span clamps
to the nearer stop (a Wow above 3.5 cents plays 3.5), a `tone_hz` of 0 or
less is Tone out, and NaN takes that option's default.
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
    """One tape repeat, 135 ms after the dry and in the same place: the Sun
    Studio slap. audiodsp tier; zero latency.

    **What the default surrenders:** Tone is out, so the repeat is brighter
    than an Ampex 350's 15 kHz top; the 1-cent wow makes the repeat's top
    end breathe (a 15 kHz tone swings to -5.11 dB at 48 kHz, -6.38 dB at
    44.1); and the Time knob walks rather than jumps.
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
        """Frames until the output is exactly zero once the input stops, as
        an upper bound: `laps_to_zero(f, excess)` laps of the longest delay
        the read head may be at, plus the wow's depth in frames rounded up,
        plus one frame for the interpolated read, plus the Tone low-pass's
        memory. One lap at Repeats 0. Finite at every setting the class
        reaches."""
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
