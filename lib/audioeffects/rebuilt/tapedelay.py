"""`TapeDelay` - a tape echo with two transports: the Roland RE-201's motor
and the Maestro EP-3's sliding head.

Your dry signal passes untouched, and the repeats follow it off a loop of
tape, each one a little darker than the last.

**Controls.** Time is the delay, from 20 to 1200 ms, and Feedback is how
much of each repeat goes round again, up to 0.99. Mix is the echo return:
the dry stays at unity up to Mix 1, Mix 2 is the repeats alone, and at Mix 0
the output is the input. Spacing is how far the worn head sits off the tape:
more spacing, darker repeats. Wow and Flutter are the transport's slow and
fast wobble. Record Level drives the tape harder, a soft squash on every
pass. Spread feeds each channel's repeats into the other, and does nothing
on a mono source. With Sync on, Time is Division of the host's beat; with no
host tempo, Time stays where the knob is.

**Two characters.** `character="varispeed"`, the default, is the RE-201:
Time moves the motor, so a Time move bends the pitch of everything on the
tape instead of clicking, then settles. Glide does nothing on this
character. `character="sliding-head"` is the EP-3: Time slides a head, so the pitch
bends only while the head moves, at the rate Glide sets, and the tape runs
at one speed, so the darkening does not follow Time. Glide 0 is an instant
slide, and its price is a click.

**Where the pitch bend stops.** A Time move made while the last one is still
bending takes its rate from the last Time you set, not from where the tape
has got to, so it does not telescope as a real motor would. A long rising
move, or a rising slide at the fastest Glides, can read more than 10 cents
off the ideal bend, because the node walks its read head in single
precision.

**The tape.** The wobble is periodic, not random. A Wow or Flutter move that
changes only how deep the wobble is glides in, and one that changes their
balance steps, so set the balance before you play. The darkening follows
the tape's loss law only up to a band top that rises with the tape's speed.
Record Level has no memory: tape hysteresis is not modelled. The RE-201's
Bass and Treble are not here.

**Limits shared by the family.** A control that jumps makes the output step:
move it in small steps from the host if you need it smooth. When your source
ends, the tail rings out as it would on silence.

**Latency, tail, portability.** Latency is zero samples: nothing looks ahead.
`tail_samples` is an upper bound on how long the output takes to reach exact
zero once your input stops, at every Feedback and Spread, stereo and mono.
Pass a lower `max_time_ms` for a shorter line: Time then stops at that
ceiling, and `get_macro(0)` shows where it stopped. The class needs
audiodsp's `audioecho`, and on a board without it construction raises
`ImportError`. `character` must be `"varispeed"` or `"sliding-head"`.

**Cost.** Measured at v0.6.2 at the default and every patch, the full class
costs 0.551-0.608 ms a block on the P4 and 1.056-1.093 ms on the S3, over the
budgets of 0.480 ms and 0.800 ms. Measured at v0.6.2, patch 8 on a class
built with `max_time_ms=800` costs 0.445-0.455 ms on the P4 and 0.781-0.797
ms on the S3, inside both budgets.
`reset()` returns to patch 0, so a host that wants the lean patch sets it
again after a reset.
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


CHARACTERS = ("varispeed", "sliding-head")
VARISPEED, SLIDING_HEAD = CHARACTERS

#: The Time map, fixed on every instance (dossier section 6): 20-1 200 ms.
TIME_MIN_MS = 20.0
TIME_MAX_MS = 1200.0

#: Glide is the time a full-range Time move takes on sliding-head; the
#: node's `delay_slew` is FULL_RANGE_MS / glide_ms (dossier section 6).
FULL_RANGE_MS = TIME_MAX_MS - TIME_MIN_MS

#: The Glide knob's span, log, with grid 0 the jump.
GLIDE_MIN_MS = 1200.0
GLIDE_MAX_MS = 12000.0

#: At slew 1 a rising Time stands the read head still. A constructor Glide
#: under 1 191.9 ms is pinned here; no grid position gets there (grid 1 is
#: 1 222.0 ms, slew 0.966).
SLEW_PIN = 0.99

#: The Glide knob's position for a constructor Glide faster than grid 1:
#: grid 1 itself, never grid 0, the jump (DigitalDelay's `GLIDE_FLOOR`).
GLIDE_FLOOR = 1.0 / 127.0

#: The node's own loop ceiling (`audiodsp_feedback_delay.c:157`).
FEEDBACK_MAX = 0.99

#: The line's headroom over `max_time_ms`: one frame for the node's
#: `line_frames - 2` clamp (`audiodsp_feedback_delay.c:148-150`) plus the
#: wow table's largest excursion, 3.096 ms at the Wow and Flutter stops,
#: rounded up (dossier Tier 3).
LINE_HEADROOM_MS = 5.0

#: S3 eq. (13)'s play gap and tape thickness, metres (dossier section 6).
GAP_M = 5e-6
THICK_M = 35e-6

#: The Spacing knob, micrometres, log.
SPACING_MIN_UM = 2.0
SPACING_MAX_UM = 20.0

#: The speed law (dossier section 6). Varispeed: 40 cm/s at Time 180 ms and
#: below, 12 cm/s at 600 ms and above, 40 x 180 / T between (fixed heads:
#: T is inversely v). Sliding-head: the Echoplex's roughly 8 ips.
V_FAST = 0.40
V_SLOW = 0.12
T_FAST_MS = 180.0
T_SLOW_MS = 600.0
V_SLIDING = 0.2032

#: The wow table: one period of TABLE_POINTS Q15 points at WOW_HZ, holding
#: the wow line at harmonic WOW_HARMONIC, the flutter line at
#: FLUTTER_HARMONIC and the drift at harmonics 1-9, amplitude 1/k, at
#: DRIFT_PHASES (dossier section 6).
#: TABLE_POINTS is not a cost lever. The node reads any length the same way,
#: and a shorter table silently kills the flutter: at 1 024 points harmonic
#: 512 sits on the table's Nyquist, at 256 it folds onto DC, and the Flutter
#: knob then writes the same table as Flutter 0 while T4 still reads two
#: lines, an interpolation image of the wow line (the 2026-09-28 cost study).
WOW_HZ = 0.01
TABLE_POINTS = 4096
WOW_HARMONIC = 72
FLUTTER_HARMONIC = 512
WOW_LINE_HZ = 0.72
FLUTTER_LINE_HZ = 5.12
DRIFT_PHASES = (0.37, 2.91, 5.02, 1.18, 4.40, 3.33, 0.84, 5.71, 2.26)
#: The drift's peak excursion, ms per cent of Wow.
DRIFT_PER_WOW_CENT_MS = 0.25
WOW_MAX_CENTS = 8.0
FLUTTER_MAX_CENTS = 4.0

(TIME_I, FEEDBACK_I, MIX_I, GLIDE_I, WOW_I, FLUTTER_I, RECORD_I, SPACING_I,
 SPREAD_I, SYNC_I, DIVISION_I) = range(11)

#: How close, as a 0..1 knob position, a Time write must come to the
#: constructor's own seeded position to count as a host echoing it back.
ECHO_TOLERANCE = 1e-6

#: The constructor defaults, which NaN falls back to.
DEFAULTS = (350.0, 0.45, 0.35, 6000.0, 2.0, 1.0, 0.2, 5.0, 0.0, 0.0, 6.0)


# -- the loss law -------------------------------------------------------------

def eq13_gain(k, spacing_m):
    """S3 eq. (13), one pass, as a linear gain at wavenumber `k` (rad/m):
    spacing e^(-k d), thickness (1 - e^(-k delta)) / (k delta) and gap
    |sinc(k g / 2)|, at `GAP_M` and `THICK_M`."""
    spacing = math.exp(-k * spacing_m)
    kd = k * THICK_M
    thickness = (1.0 - math.exp(-kd)) / kd
    half = k * GAP_M / 2.0
    gap = abs(math.sin(half) / half)
    return spacing * thickness * gap


def k3_of(spacing_m):
    """The wavenumber at which eq. (13) is at half power (-3.01 dB), by
    bisection in log k: 15 967 rad/m (393.5 um) at 5 um."""
    lo, hi = 1.0, 1e7
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        gain = eq13_gain(mid, spacing_m)
        if gain * gain > 0.5:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def speed(character, time_ms):
    """Tape speed, m/s, for a character at a Time (dossier section 6)."""
    if character == SLIDING_HEAD:
        return V_SLIDING
    t = float(time_ms)
    if t < T_FAST_MS:
        t = T_FAST_MS
    if t > T_SLOW_MS:
        t = T_SLOW_MS
    return V_FAST * T_FAST_MS / t


def tone_excess(damping_hz, sample_rate):
    """(frames, relative excess) for the loop low-pass at `damping_hz`
    (already pre-warped): after `frames` frames whatever its state held
    weighs under 2^-17 of it, and its single-precision state can rest up to
    2^-24 / a above the line's peak, a being the coefficient.
    `DigitalDelay`'s `_tone_excess`, as a function of the handed value."""
    if damping_hz <= 0.0:
        return 0, 0.0
    per_frame = 2.0 * math.pi * damping_hz / sample_rate
    coefficient = 1.0 - math.exp(-per_frame)
    frames = int(math.ceil(32.0 * math.log(2.0) / per_frame))
    return frames, 2.0 ** -17 + 2.0 ** -24 / coefficient


# -- the glide laws -----------------------------------------------------------

def slew_of(glide_ms):
    """Sliding-head's `delay_slew` for a Glide: 0 (the jump) at Glide 0,
    otherwise 1 180 ms over `glide_ms`, pinned at 0.99."""
    glide_ms = float(glide_ms)
    if not glide_ms > 0.0:
        return 0.0
    slew = FULL_RANGE_MS / glide_ms
    if slew > SLEW_PIN:
        slew = SLEW_PIN
    return slew


def varispeed_slew(from_ms, to_ms):
    """The tape equation for a speed step from a settled transport:
    dT/dt = 1 - T_old / T_new, so the walk runs |dT| / T_new
    delay-seconds per second and lasts exactly T_new (S4 eq. 3)."""
    return abs(float(to_ms) - float(from_ms)) / float(to_ms)


# -- the wow table ------------------------------------------------------------

_SINE = None
_DRIFT = None


def _shapes():
    """(one period of sine, the unit drift) at `TABLE_POINTS`, float32,
    computed once and shared by every instance. The drift is harmonics 1-9
    at amplitude 1/k and `DRIFT_PHASES`, scaled to a peak of 1."""
    global _SINE, _DRIFT
    if _SINE is None:
        points = TABLE_POINTS
        mask = points - 1
        quarter = points // 4
        sine = array("f", [0.0] * points)
        for n in range(points):
            sine[n] = math.sin(2.0 * math.pi * n / points)
        weights = [(k, math.cos(p) / k, math.sin(p) / k)
                   for k, p in zip(range(1, 10), DRIFT_PHASES)]
        drift = array("f", [0.0] * points)
        peak = 0.0
        for n in range(points):
            total = 0.0
            for k, c, s in weights:
                i = k * n
                total += (sine[i & mask] * c + sine[(i + quarter) & mask] * s)
            drift[n] = total
            if abs(total) > peak:
                peak = abs(total)
        for n in range(points):
            drift[n] = drift[n] / peak
        _DRIFT = drift
        _SINE = sine
    return _SINE, _DRIFT


def cents_to_depth_ms(cents, line_hz):
    """A delay D sin(2 pi f t) ms moves pitch by a peak ratio of
    1 + 2 pi f D / 1000, so `cents` peak is
    D = (2^(cents/1200) - 1) / (2 pi f) x 1000: 8 cents of the 0.72 Hz line
    is 1.024 ms, 4 cents of the 5.12 Hz line 0.072 ms."""
    cents = float(cents)
    if not cents > 0.0:
        return 0.0
    return ((2.0 ** (cents / 1200.0) - 1.0) / (2.0 * math.pi * line_hz)
            * 1000.0)


def wow_table(wow_cents, flutter_cents, out, flutter_harmonic=FLUTTER_HARMONIC,
              drift=True):
    """Write the wow table for (Wow, Flutter) into `out`, an int16 array of
    `TABLE_POINTS`, and return its peak excursion in ms, which is the
    node's `wow_depth_ms`; 0.0 (and `out` untouched) with nothing to write.

    The wow line's peak is `cents_to_depth_ms(wow, 0.72 Hz)`, the flutter
    line's `cents_to_depth_ms(flutter, 5.12 Hz)` and the drift's 0.25 ms per
    cent of Wow; the table is their sum normalised to its own peak."""
    w = cents_to_depth_ms(wow_cents, WOW_LINE_HZ)
    f = cents_to_depth_ms(flutter_cents, FLUTTER_LINE_HZ)
    d = DRIFT_PER_WOW_CENT_MS * float(wow_cents) if drift else 0.0
    if not d > 0.0:
        d = 0.0
    if w <= 0.0 and f <= 0.0 and d <= 0.0:
        return 0.0
    sine, walk = _shapes()
    mask = TABLE_POINTS - 1
    peak = 0.0
    for n in range(TABLE_POINTS):
        x = (w * sine[(WOW_HARMONIC * n) & mask]
             + f * sine[(flutter_harmonic * n) & mask] + d * walk[n])
        if abs(x) > peak:
            peak = abs(x)
    scale = 32767.0 / peak
    for n in range(TABLE_POINTS):
        x = (w * sine[(WOW_HARMONIC * n) & mask]
             + f * sine[(flutter_harmonic * n) & mask] + d * walk[n])
        out[n] = int(math.floor(x * scale + 0.5))
    return peak


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


class TapeDelay(_component.Component):
    """A tape echo with the RE-201's motor or the EP-3's sliding head.
    The module docstring is the player's manual."""

    NAME = 'TapeDelay'
    DISPLAY_NAME = 'Tape Delay'
    CATEGORIES = ('Delay',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho",)

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Time", "Feedback", "Mix", "Glide", "Wow", "Flutter",
                    "Record Level", "Spacing", "Spread", "Sync", "Division")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
        8: "UNIPOLAR",
        9: "TOGGLE",
        10: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (TIME_MIN_MS, TIME_MAX_MS, "log"),      # 0  Time, ms
        (0.0, FEEDBACK_MAX),                    # 1  Feedback
        (0.0, 2.0),                             # 2  Mix; dry at unity to 1
        (GLIDE_MIN_MS, GLIDE_MAX_MS, "log"),    # 3  Glide, ms; grid 0 = jump
        (0.0, WOW_MAX_CENTS),                   # 4  Wow, cents at 0.72 Hz
        (0.0, FLUTTER_MAX_CENTS),               # 5  Flutter, cents at 5.12 Hz
        (0.0, 1.0),                             # 6  Record Level, loop_drive
        (SPACING_MIN_UM, SPACING_MAX_UM, "log"),  # 7  Spacing, um
        (0.0, 1.0),                             # 8  Spread, cross_feed
        (0.0, 1.0),                             # 9  Sync
        (0.0, 15.0),                            # 10 Division index
    )

    #: `_component.macro_of` of the dossier's section 6 settings; patch 0 is
    #: the constructor's defaults on the grid. Patch 8 is patch 0 with Record
    #: Level at 0, the board's lean patch (with `max_time_ms=800`; the module
    #: docstring's Cost).
    PATCHES = {
        0: ("Warm Repeats", (89, 58, 22, 89, 32, 32, 25, 51, 0, 0, 51)),
        1: ("Long Repeats, Slow Glide",
            (114, 71, 22, 127, 32, 32, 25, 51, 0, 0, 51)),
        2: ("Short Slap", (47, 19, 32, 89, 16, 16, 25, 51, 0, 0, 51)),
        3: ("Dark Repeats, Heavy Wow",
            (97, 71, 22, 89, 95, 64, 25, 111, 0, 0, 51)),
        4: ("High Intensity", (93, 115, 25, 89, 32, 32, 76, 51, 0, 0, 51)),
        5: ("Worn Heads", (89, 58, 22, 89, 64, 95, 64, 127, 0, 0, 51)),
        6: ("Clean Transport", (89, 58, 22, 89, 0, 0, 0, 0, 0, 0, 51)),
        7: ("Dotted Eighth, Synced",
            (89, 58, 22, 89, 32, 32, 25, 51, 0, 127, 68)),
        8: ("Tape Delay - lean", (89, 58, 22, 89, 32, 32, 0, 51, 0, 0, 51)),
    }

    def _build(self, time_ms=350.0, feedback=0.45, mix=0.35, glide_ms=6000.0,
               wow_cents=2.0, flutter_cents=1.0, record_level=0.2,
               spacing_um=5.0, spread=0.0, sync=False, division=6,
               character=VARISPEED, max_time_ms=TIME_MAX_MS, patch=None):
        if character not in CHARACTERS:
            raise ValueError(
                "character must be 'varispeed' or 'sliding-head'")
        self._character = character
        max_time_ms = float(max_time_ms)
        # `not <=` catches NaN, which would otherwise pass both clamps and
        # size the line from nothing.
        if not max_time_ms <= TIME_MAX_MS:
            max_time_ms = TIME_MAX_MS
        if max_time_ms < TIME_MIN_MS:
            max_time_ms = TIME_MIN_MS
        self._max_time_ms = max_time_ms
        #: The whole-frame Time last handed to the node, and in ms.
        self._frames = 0
        self._node_ms = 0.0
        #: The Time the loss corner is read at: the clamped Time before it
        #: is landed on a frame.
        self._time_played = 0.0
        #: The longest delay, in whole frames, the read head may still sit
        #: at. A walk starts from wherever the head is and the class cannot
        #: see how far it has got, so after a falling move this keeps the old
        #: Time until a jump or a reset lands the head.
        self._reach = 1
        #: True while the node has been built or cleared and not yet told a
        #: second Time: it snaps onto the configured delay on its first pull.
        self._fresh = True
        #: True while several macros are applied at once (the constructor,
        #: `program_change`); the node is refreshed once, after the last.
        self._deferred = False
        self._slew = 0.0
        self._feedback = 0.0
        self._damping = 0.0
        self._corner = 0.0
        self._spread = 0.0
        self._wow_ms = 0.0
        #: (Wow, Flutter) the current table was written for.
        self._wow_key = None
        #: Two tables: the node borrows one while a move writes the other.
        self._tables = (array("h", [0] * TABLE_POINTS),
                        array("h", [0] * TABLE_POINTS))
        self._table_index = 1
        self._table = None
        #: k3 for the Spacing last asked, keyed by the Spacing in metres.
        self._k3_key = None
        self._k3 = 0.0

        # A log knob cannot seed 0 or a negative; those clamp to the bottom.
        time_ms = _option(time_ms, DEFAULTS[TIME_I])
        if not time_ms > 0.0:
            time_ms = TIME_MIN_MS
        time_ms = _between(time_ms, TIME_MIN_MS, TIME_MAX_MS)
        spacing_um = _option(spacing_um, DEFAULTS[SPACING_I])
        if not spacing_um > 0.0:
            spacing_um = SPACING_MIN_UM
        #: A constructor Glide stays on the audio path until macro 3 moves:
        #: the span starts at 1 200 ms, so a faster Glide (down to the 0.99
        #: pin) or an exact 0 has no knob position. A slower one is clamped
        #: to the span's top, 12 s. 0, a negative and NaN are the jump.
        glide_ms = float(glide_ms)
        if glide_ms > GLIDE_MAX_MS:
            glide_ms = GLIDE_MAX_MS
        if not glide_ms > 0.0:
            glide_ms = 0.0
        self._glide_exact = glide_ms
        #: The constructor's Time, exactly, until macro 0 moves. Seeding a
        #: log knob and reading it back is not exact: 350.0 ms comes back a
        #: few ulps under, which at 22.05 kHz (7 717.5 frames) would land on
        #: 7 717 instead of the 7 718 the whole-frame law gives 350.0.
        self._time_exact = time_ms
        self._time_seed = -1.0
        self._seeding = True
        values = (time_ms,
                  _option(feedback, DEFAULTS[FEEDBACK_I]),
                  _option(mix, DEFAULTS[MIX_I]),
                  max(GLIDE_MIN_MS, glide_ms),
                  _option(wow_cents, DEFAULTS[WOW_I]),
                  _option(flutter_cents, DEFAULTS[FLUTTER_I]),
                  _option(record_level, DEFAULTS[RECORD_I]),
                  spacing_um,
                  _option(spread, DEFAULTS[SPREAD_I]),
                  1.0 if sync else 0.0,
                  _option(division, DEFAULTS[DIVISION_I]))
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
        # read head, so a reset is silent and snaps onto the current Time.
        self._own(self._delay, reset=self._clear)
        self._delay.play(self._source)
        self._output = self._delay
        self._deferred = True
        try:
            self._init_macros(values)
        finally:
            self._deferred = False
            self._seeding = False
        # The knob is seeded where the constructor's Glide is, or at grid 1
        # for a faster one; `_glide_exact` carries the real value, so a
        # get_macro / set_macro round trip keeps it gliding.
        if self._glide_exact > 0.0 and self._macros[GLIDE_I] < GLIDE_FLOOR:
            self._macros[GLIDE_I] = GLIDE_FLOOR
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
        time_ms = float(time_ms)
        if time_ms > self._max_time_ms:
            return self._max_time_ms
        if time_ms < TIME_MIN_MS:
            return TIME_MIN_MS
        return time_ms

    def _time_ms(self):
        """The Time the audio path plays, before it is clamped and landed."""
        if self._time_exact is not None:
            return self._time_exact
        return self._value(TIME_I)

    def _glide_ms(self):
        if self._glide_exact is not None:
            return self._glide_exact
        if self._macros[GLIDE_I] <= 0.0:
            return 0.0
        return self._value(GLIDE_I)

    def _walk_rate(self, from_ms, to_ms):
        """The node's `delay_slew` for a Time move: the tape equation on
        varispeed, the Glide law on sliding-head."""
        if self._character == VARISPEED:
            return varispeed_slew(from_ms, to_ms)
        return slew_of(self._glide_ms())

    def _corner_hz(self, time_ms, spacing_um):
        """The loop low-pass's -3 dB corner, before the clamp and the
        pre-warp: eq. (13)'s half-power point, v k3(d) / 2 pi."""
        spacing_m = spacing_um * 1e-6
        if spacing_m != self._k3_key:
            self._k3 = k3_of(spacing_m)
            self._k3_key = spacing_m
        return speed(self._character, time_ms) * self._k3 / (2.0 * math.pi)

    def _write_table(self, wow_cents, flutter_cents, out):
        """Hook for the table law; returns the depth in ms."""
        return wow_table(wow_cents, flutter_cents, out)

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
        # negative, NaN or infinity) leaves Time on the knob. `not bpm > 0`
        # catches NaN, and `bpm * 0` is NaN for infinity.
        bpm = float(state[2] or 0.0)
        if not bpm > 0.0 or bpm * 0.0 != 0.0:
            return None
        index = int(round(self._value(DIVISION_I)))
        index = min(len(DIVISION_BEATS) - 1, max(0, index))
        return DIVISION_BEATS[index] * 60000.0 / bpm

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        if not self._seeding:
            if index == GLIDE_I:
                self._glide_exact = None
            elif index == TIME_I and not (
                    self._time_exact is not None
                    and abs(position - self._time_seed) <= ECHO_TOLERANCE):
                # A host that reads Time back and writes the same position
                # keeps the constructor's exact Time; any other drops it.
                self._time_exact = None
        if not self._deferred:
            self._refresh()

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index` whole, then refresh the node once, so Time
        is read against the new patch's Sync and moves once."""
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
        # The cleared node snaps onto the current Time on its next pull.
        self._reach = max(1, self._frames)
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
        node_ms = frames * 1000.0 / fs
        if self._character == VARISPEED:
            # The motor's law sets each move's rate from the Time it leaves;
            # with no move the walk in progress keeps its rate.
            if frames != self._frames and not self._fresh:
                self._slew = self._walk_rate(self._node_ms, node_ms)
        else:
            self._slew = self._walk_rate(self._node_ms, node_ms)
        if self._fresh or self._slew <= 0.0:
            # A fresh node snaps onto the target, and with the slew off the
            # read head jumps there on the next frame.
            self._reach = frames
        elif frames > self._reach:
            self._reach = frames
        self._frames = frames
        self._node_ms = node_ms
        self._time_played = clamped

        spacing = _between(self._value(SPACING_I), SPACING_MIN_UM,
                           SPACING_MAX_UM)
        self._corner = self._corner_hz(clamped, spacing)
        self._damping = nominal_damping_hz(self._hz(self._corner), fs)
        # Handed as set: since audiodsp v0.6.3rc1 the node lands a loop
        # low-pass that has stopped moving (#157), so no Feedback holds a
        # small value for ever and nothing is stepped clear here.
        self._feedback = _between(self._value(FEEDBACK_I), 0.0, FEEDBACK_MAX)

        wow = _between(self._value(WOW_I), 0.0, WOW_MAX_CENTS)
        flutter = _between(self._value(FLUTTER_I), 0.0, FLUTTER_MAX_CENTS)
        key = (wow, flutter)
        if key != self._wow_key:
            # Write the table the node is not reading, then hand it over.
            spare = 1 - self._table_index
            depth = self._write_table(wow, flutter, self._tables[spare])
            if depth > 0.0:
                self._table_index = spare
                self._table = self._tables[spare]
            elif self._fresh:
                self._table = None
            # Otherwise a playing node keeps the table it has: the node ramps
            # the old depth out over 20 ms (audiodsp#160), and without a
            # table it would ramp it out on its own sine instead, a jump in
            # the read offset. At depth 0 the table moves nothing.
            self._wow_ms = depth
            self._wow_key = key

        # At one channel the node's cross-feed sends the repeat nowhere.
        # At two, Spread is handed as set: since audiodsp v0.6.3rc3 a
        # cross-fed tail reaches exact zero however the node rounds the
        # cross-feed sum (audiodsp#173), so the 1/4096 grid is gone.
        if self._channel_count == 1:
            self._spread = 0.0
        else:
            self._spread = _between(self._value(SPREAD_I), 0.0, 1.0)
        self._delay.set(
            delay_slew=self._slew,
            delay_ms=node_ms,
            feedback=self._feedback,
            mix=_between(self._value(MIX_I), 0.0, 2.0),
            loop_drive=_between(self._value(RECORD_I), 0.0, 1.0),
            damping_hz=self._damping,
            cut_hz=0.0,
            cross_feed=self._spread,
            wow_hz=WOW_HZ,
            wow_depth_ms=self._wow_ms,
            wow_shape=self._table)

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound: `laps_to_zero(f, excess)` laps of the longest delay
        the read head may be at, plus the wow table's peak excursion in
        frames rounded up, plus one frame for the interpolated read, plus
        the loop low-pass's memory. Finite at every setting the class
        reaches, stereo and mono, at every Spread."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        memory, excess = tone_excess(self._damping, self._sample_rate)
        laps = laps_to_zero(self._feedback, excess)
        wow = int(math.ceil(self._wow_ms * self._sample_rate / 1000.0))
        return int(laps * (self._reach + wow + 1 + memory))
