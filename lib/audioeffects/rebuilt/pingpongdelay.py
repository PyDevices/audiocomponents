"""`PingPongDelay` - repeats that alternate between the speakers.

Rebuilt from scratch for Phase 5 against
`workspace docs/effects-internal/dossiers/PingPongDelay.md`, whose trait
table was frozen at Station A before this file existed (anchor commit
eb466725d4422619d8e941c043f77512c1e5237b, the Station A critique's
re-freeze, 2026-09-28). The old class in `delay.py` is consulted only for
the seven defects that dossier's section 7 names; it stays the class the
library serves until the board runner adopts this one.

**What it sounds like.** Your dry signal passes untouched on both sides.
The first repeat comes back Time later on one side only, the side First
Side names; the next comes back Time after that on the other side, a
Feedback's worth quieter, and they keep bouncing, one side and then the
other, all the way down. Each side on its own repeats every two Times.
Time (20-1000 ms) is the spacing between one repeat and the next. Feedback
(0-0.99) is how many bounces you hear. Mix (0-2) is the wet/dry balance:
dry at unity up to 1, the repeats alone at 2, and Mix 0 is a wire while the
line keeps recording. Spread moves the whole thing between two plain
delays, one per side with the same repeats on both (0), and the full
bounce (1). Sync locks Time to Division of the host's beat. Repeat Tone
and Repeat Cut put a low-pass and a high-pass inside the loop, so each
bounce is a little darker or thinner than the last; both default out.

**No standout.** A ping-pong is a routing of two delay lines, not a
circuit, and no product defines it (dossier section 2). The traits are the
textbook property of the topology, stated so a measurement can fail them.

**Portability tier: audiodsp** (`REQUIRES = ("audioecho",)`). The
cross-feed exists only on `audioecho.FeedbackDelay`; nothing a stock
CircuitPython board carries crosses one channel's repeats into the other's
line. On a stock board this module imports cleanly and construction raises
`ImportError`.

**Latency: zero samples, at every setting and every rate.** Nothing looks
ahead. The dry path is a wire on both channels until the first repeat
arrives, and the repeats are the effect, not latency. No option adds any.

**Mono.** A one-channel source gets the mono sum of the stereo behaviour:
an ordinary feedback delay at the same Time, Feedback and Mix, repeats at
T, 2T, 3T ... at gains 1, f, f^2 .... Spread and First Side do nothing on
a one-channel instance, because there is no second line to cross into:
the class hands the node `cross_feed` 0 and `input_pan` 0 there whatever
they say. (Handing it the stereo settings would silence the loop after one
half-level repeat, which is what the old class did.) On a stereo source
identical in both channels, with Mix at 2, the two channels summed are
that mono delay's output exactly, sample for sample, as long as no two
repeats overlap one another: on sustained material that overlaps its own
repeats each side rounds its own write where the mono delay rounds the sum
once, and the two part by a few LSB. That holds with Repeat Tone never in
since the last `reset()`; once it has been in, its out stop moves the
Feedback a hair (below), and at Feedback 0.99 the first eight repeats part
from a delay at the knob's Feedback in 5 samples by up to 5 LSB. With a
loop filter in, the material
must also end at least 512 frames before Time at 48 kHz, because each
side's filter meets that side's next repeat two Times later where the mono
delay's meets the very next one: a noise burst ending one frame before
Time parts them in 295 samples by 1 LSB (Repeat Tone 800 Hz) and in 680 by
up to 2 LSB (Repeat Cut 400 Hz).

**Spread's law.** Spread s hands the node `cross_feed` s and `input_pan`
-s (First Side left) or +s (right). On a click identical in both channels,
repeat n reads f^(n-1) [(1 - s/2) + (s/2)(1 - 2s)^(n-1)] of the click on
the First Side channel and f^(n-1) [(1 - s/2) - (s/2)(1 - 2s)^(n-1)] on
the other. At Spread 0 the two channels are identical; at Spread 1 each
repeat is on one side only and the other side is exact zero. At the Times
the node lands off the frame (below) the law misses by up to 289 LSB on a
20 000 click at Feedback 0.99 (44.1 kHz, MIDI 95; 145 LSB at 22.05 kHz).

**What the loop hears.** At Spread 1 the loop is fed the average of the
two input channels, (L + R) / 2, into one line, so what the two channels
share bounces and what differs between them never repeats. A source whose
right channel is the left one upside down puts nothing in the loop: the
defaults pass it through untouched and Mix 2 is silence. The dry path is
always each channel's own signal, never swapped or summed.

**Input ceiling.** The dry path sits at unity and the repeats add to it,
so a hot input can put the output on the int16 rail, and there is no input
gain to turn down. Measured on the kit's `noise_det` at 48 kHz over 20 s,
the defaults are clean up to -3 dBFS peak (at -2 they rail 2331 samples)
and every shipped patch up to -3.1 dBFS. Patch 4 (Spread 0, where each
side repeats every Time rather than every two) rails first: 76 samples at
-3 dBFS, and 167 902 on a 997 Hz sine there; patch 3 rails 4. On any
material, with Repeat Cut out and Mix below 1, an input peaking at or
below one LSB under (1 - Mix) of full scale, floor(32767 (1 - Mix)) - 1,
cannot reach the rail at any Time, Feedback or Spread, because the lines
hold int16 and so the repeats never exceed Mix x full scale: -3.1 dBFS at
the default Mix 0.3 and at every patch. At exactly (1 - Mix) of full scale
the sum can round onto 32767, the rail value, though nothing is clipped.
Repeat Cut's high-pass overshoots a square wave's edges, so with it in
leave more room: a 40 Hz square wave at -3.1 dBFS rails with Cut at 40 or
400 Hz, and is clean from -4 dBFS.

**RAM.** The line is `max_time_ms + 1` ms of two int16 lanes whatever the
channel count: 192 192 B at 48 kHz for the default 1000 ms (176 576 B at
44.1 kHz, 88 288 B at 22.05 kHz), plus about 1.2 KB of node. The extra
millisecond is what lets Time reach 1000 ms exactly. Pass a lower
`max_time_ms` to spend less (300 ms costs 57 792 B, 500 ms 96 192 B);
Time then stops at that ceiling and `get_macro(0)` shows where it stopped.

**Cost.** One `audioecho.FeedbackDelay` with `delay_slew` on; no mixer.
Palette row FeedbackDelay +options (the nearest not-cheaper row; there is
no row for the slew alone), glue 0: **P4 <= 9 %, S3 <= 15 %** of a
5.333 ms stereo block. The board measurement is pending hardware.

**Turning Time while it plays** walks the repeats to the new time at a
fixed 0.1875 delay-seconds per second instead of clicking, so every repeat
already in the loop bends in pitch while it moves: +297.5 cents while Time
falls and -359.5 cents while it rises (1200 log2(1 +- 0.1875)). 280 ->
200 ms takes 427 ms, the full range 5.23 s. There is no Glide knob; a
ping-pong's time is set to a subdivision, not played. While Time walks,
the line is read between samples, and the two-tap read costs the top of
the band sqrt(1 - 2 frac (1 - frac)(1 - cos 2 pi f / fs)) per pass. Every
static Time is handed to the node as the nearest whole frame at the
running rate, floor(ms fs / 1000 + 0.5); the knob's milliseconds and
`get_macro(0)` stay as you set them. At 48 kHz the node lands every one of
the 128 knob positions exactly on that frame, where the read is lossless,
so the repeats of a Time you have stopped turning do not darken.

At 44.1 and 22.05 kHz it does not always. The node turns the milliseconds
back into frames in float32, and for some Times no float32 value lands on
the whole frame, so the read sits one float32 step off it: at most 1/512
of a frame at 44.1 kHz and 1/1024 at 22.05 kHz. That is 25 of the 128
knob positions at 44.1 kHz (MIDI 2, 3, 4, 19, 20, 24, 25, 28, 38, 43, 47,
48, 50, 63, 65, 67, 69, 70, 83, 92, 93, 95, 107, 108, 114) and 20 at
22.05 kHz (MIDI 2, 4, 19, 28, 38, 47, 63, 65, 67, 69, 70, 83, 88, 92, 93,
95, 108, 110, 112, 114). No patch's own Time is among them, nor the
default 280 ms; a Time Sync takes from a host's tempo can be. At those
Times each pass puts up to 0.2 % of the repeat on the frame beside it
(a 20 000 click's first repeat reads 19 961 and 39 at MIDI 95, 44.1 kHz),
and the repeats darken slowly: at Feedback 0.99 the 60th repeat of a
10 kHz tone is 0.86 dB quieter than the Feedback alone makes it at
44.1 kHz, 0.98 dB at 22.05 kHz, and a 1 kHz tone 0.01-0.02 dB. The class
cannot hand the node a number that lands there; a node change is asked
for.

**Repeat Tone** is the corner the loop low-pass achieves (800-16 000 Hz,
the top stop out). It is inside the loop, so repeat n has passed it n
times: on one side, each repeat is two passes darker than the last one
there. With Repeat Tone in, a repeat's peak also lands late by the
filter's group delay, more each pass. At a low rate the knob's corners
clamp below Nyquist: at 22.05 kHz positions 111-126 all sit on the
10 804.5 Hz clamp and do the same thing.

**The filters' out stops, after a filter has been in.** The node leaves a
loop filter's state frozen while the filter is out, and a frozen filter
plays what it held when it comes back in, out of silence. So once Repeat
Tone has been in since the last `reset()` (a constructor `tone_hz` or a
patch counts), its out stop keeps the low-pass running at a coefficient of
exactly 1, which follows the repeats. The Feedback is still handed clear
of the stall window described under Tail, which at some Feedbacks moves it
by up to 2.6 x 10^-5 (0.99 plays as 0.989976102; 0.85 does not move), so
the repeats die a hair sooner than with the filter truly out. On 2 s of
0 dBFS noise that is 0 LSB at Feedback 0.85, 1-5 LSB at 0.5, 0.75, 0.9 and
0.95, and 6 LSB at 0.99; a full-scale click at 0.99 followed through its
whole tail differs by up to 32 LSB, around its 70th repeat. Repeat Cut
cannot do that (a high-pass at coefficient 1
mutes the loop), so once Repeat Cut has been in since the last `reset()`
its bottom stop stays in circuit at the 20 Hz corner, the knob's own
bottom, until the next `reset()`. That costs the low end of the repeats
something a true out would not, and `tail_samples` is `None` while it
lasts. A `reset()` brings both exact outs back.

Each pass through a loop filter also takes something off a repeat's peak,
so with either filter in the late repeats of a quiet bounce fade faster
than Feedback alone says: at Feedback 0.52 (MIDI 67) with Repeat Cut at
400 Hz the 8th repeat of a 20 000 click is 143 LSB at 48 kHz.

**Tail.** `tail_samples` is an upper bound on how long the output takes to
reach exact zero after your input stops, and it is long: the loop rounds
its way down from full scale, 14 laps at the default Feedback (188 174
frames, 3.9 s, at 48 kHz) and 685 at 0.99 (11.4 minutes at Time 1000 ms).
The cross-feed moves repeats between the sides without changing the loop
gain, so the figure is the same at every Spread. With Repeat Tone in the
node's loop low-pass can hold a small value for ever at a Feedback a hair
either side of 1 - 0.5 / k, so there the class hands the node a Feedback
just outside that window (under 3 x 10^-5 away, far inside one step of the
knob, which still reads what you set). With Repeat Cut in circuit
`tail_samples` is `None`: no bound is derived there.

`capabilities = ("tempo_sync",)`: with Sync on, the class reads
`self._transport()` on every macro move and program change (not per
block). With no host transport, or a host whose tempo is not a finite
positive number, Time stays where the knob is. A Division past the
1000 ms ceiling (or `max_time_ms`) clamps there, and `get_macro(0)` shows
it.

A constructor value stays on the audio path unrounded by the knob's grid;
Time is then handed as a whole frame. A value outside a knob's span clamps
to the nearer stop, a `tone_hz` or `cut_hz` of 0 or less is that filter
out, and NaN takes that option's default. A `max_time_ms` above 1000 or
NaN is 1000.
"""

VENDOR = "PyDevices"

from .. import _component
from ..chorus import nominal_damping_hz

# DigitalDelay's arithmetic, reused rather than copied: the same node rounds
# the same way in both classes. Its module moves up one level when it comes
# home, so both homes are tried; the same for SlapbackDelay's `tone_excess`.
try:
    from .digitaldelay import (DIVISION_BEATS, clear_of_stalls, laps_to_zero,
                               nominal_cut_hz, whole_frames)
except ImportError:                     # pragma: no cover - after it lands
    from ..digitaldelay import (DIVISION_BEATS, clear_of_stalls,
                                laps_to_zero, nominal_cut_hz, whole_frames)
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

#: Repeat Tone out after it has been in: `damping_hz` at 32 x the rate,
#: where 1 - expf(-2 pi 32) is exactly 1.0f (`one_pole_coefficient`,
#: `audiodsp_feedback_delay.c:33-40`), so the loop low-pass's state follows
#: the tap instead of freezing (dossier section 8.11, `SlapbackDelay`'s
#: answer).
TONE_TRACK_PER_RATE = 32.0

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
    """Two delay lines crossed into each other: the repeats alternate
    between the speakers, one side and then the other. audiodsp tier; zero
    latency.

    **What the default surrenders:** both loop filters are out, so the
    bounce does not darken on its own; Time walks rather than jumps, and a
    walk bends the repeats' pitch while it moves; at full Spread what
    differs between the two input channels never repeats; on a mono source
    Spread and First Side do nothing; and there is no input gain, so an
    input above -3 dBFS peak can reach the rail.
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
        #: True once a loop filter has been handed an in-circuit corner
        #: since the node was built or cleared. From then on its state is
        #: live, and its out stop is not 0 (dossier section 8.11).
        self._tone_used = False
        self._cut_used = False
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
        # read head (`audiodsp_feedback_delay.c:291-299`, `:286-288`), so a
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
        self._tone_used = False
        self._cut_used = False

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
        damping = self._tone_damping(self._macros[TONE_I])
        if damping > 0.0:
            self._tone_used = True
        elif self._tone_used:
            # The node updates its loop low-pass only while the coefficient
            # is above 0 (`audiodsp_feedback_delay.c:493`), so handing 0
            # after Tone has been in would freeze whatever the filter held.
            # A coefficient of exactly 1 keeps the state on the tap instead.
            damping = TONE_TRACK_PER_RATE * rate
        cut = self._cut_hz(self._macros[CUT_I])
        if cut > 0.0:
            self._cut_used = True
        elif self._cut_used:
            # The same freeze for the high-pass (`:498`), which outputs
            # value - state and so would mute the loop at coefficient 1:
            # once Cut has been in, its bottom stop is the 20 Hz corner.
            cut = nominal_cut_hz(self._hz(CUT_MIN_HZ), rate)
        feedback = _between(self._value(FEEDBACK_I), 0.0, FEEDBACK_MAX)
        if damping > 0.0 and feedback > 0.0:
            # With Tone in, the node can hold a small value for ever at a
            # Feedback a hair either side of 1 - 0.5 / k; the node is handed
            # the nearer edge of that window.
            feedback = self._loop_feedback(feedback,
                                           tone_excess(damping, rate)[1])
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

    def _loop_feedback(self, feedback, excess):
        """The Feedback handed to the node with Repeat Tone in circuit."""
        return clear_of_stalls(feedback, excess)

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound, or `None` with Repeat Cut in circuit.

        `laps_to_zero(f, excess)` laps, each at most one frame longer than
        the longest delay the read head may be at (the read interpolates
        towards the next older frame), plus the Tone low-pass's memory.
        While a walk falls, that is the Time it is walking from, until a
        reset lands the head. The cross-feed hands each lane a convex mix
        of the two lanes' loop values (`audiodsp_feedback_delay.c:520-529`),
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
        if laps is None:                    # pragma: no cover - stepped clear
            return None
        return int(laps * (self._reach + 1 + memory))
