"""`DigitalDelay` - a clean interpolated line with the Boss DD-2's control law.

Rebuilt from scratch for Phase 5 against
`workspace docs/effects-internal/dossiers/DigitalDelay.md`, whose trait
table was frozen at Station A before this file existed (anchor commit
51207b8, 2026-09-27). The old class in `delay.py` is consulted only for the
seven defects that dossier's section 7 names. This class was adopted on
2026-09-28, and `audioeffects.DigitalDelay` serves it.

**What it sounds like.** Your dry signal passes untouched, and one clean
repeat follows it, fed back for more. Time (12.5-800 ms) is the DD-2's
D.TIME and its three MODE ranges folded into one knob. Feedback (0-0.99)
is F.BACK, Mix (0-2) is E.LEVEL: dry at unity up to 1, wet alone at 2, and
Mix 0 is a wire while the line keeps recording. Turn Time while it plays
and the repeats bend in pitch and settle, the way the pedal's single master
clock resamples its memory, instead of clicking. Glide sets how fast that
happens: the time a full-range Time move takes, 800 ms to 8 s. Repeat Tone
and Repeat Cut put the pedal's 7 kHz and 40 Hz corners into the loop as
knobs, so each repeat gets a little darker or thinner than the last. Sync
locks Time to Division of the host's beat.

**The standout:** the Boss DD-2 Digital Delay (1983), light touch. You get
its control law and its dry/wet discipline as defaults, and its converter
colour as two knobs that default off. Patch 5 is the pedal's own corners.

**Portability tier: audiodsp** (`REQUIRES = ("audioecho",)`). The stock
`audiodelays.Echo` limits its only output at +-28000, so its Mix 0 is not
a wire, and its one continuous-time mode lands 350 ms 33 samples late. On
a stock CircuitPython board this module imports cleanly and construction
raises `ImportError`.

**Latency: zero samples, at every setting and every rate.** Nothing looks
ahead. The delay is the wet path, not latency on the dry path, and no
option adds any.

**Mono.** A one-channel source gets the identical effect on its one
channel. The class never passes `input_pan`, which in mono would overwrite
the node's mono feed and halve the repeats.

**RAM.** The line is `max_time_ms + 1` ms of two int16 lanes whatever the
channel count: 153 792 B at 48 kHz for the default 800 ms (141 296 B at
44.1 kHz, 70 648 B at 22.05 kHz), plus about 1.2 KB of node. Pass a lower
`max_time_ms` to spend less (300 ms costs 57 792 B); Time then stops at
that ceiling and `get_macro(0)` shows where it stopped.

**Cost.** One `audioecho.FeedbackDelay` with `delay_slew` on; no mixer.
Palette row FeedbackDelay +options (the nearest not-cheaper row; there is
no row for the slew alone), glue 0: **P4 <= 9 %, S3 <= 15 %** of a
5.333 ms stereo block. Measured on both boards on 2026-09-27 at every
shipped patch: the P4 at most 0.372 ms, 7.0 % (patch 5, rt 5.49); the S3
at most 0.631 ms as the tool reads it, and about 0.78 ms, 14.6 %, at
patch 5 once the tool's control is measured in the same conditions as the
palette row (the dearest patch, the one with both loop filters in; rt
3.11). Alone on an S3 it leaves about 85 % of the block for everything
else. Six of the seven patch digests are identical on both boards and the
desktop; patch 5's is identical on both boards and differs from the
desktop's because `nominal_cut_hz` and `nominal_damping_hz` are worked out
in Python, in a board's single precision: `cut_hz` lands 0.035 % high
(39.44766 Hz against 39.43366) and `damping_hz` one float32 step off.

**What the default surrenders.** It is a clean line, so it does not darken
on its own: the DD-2's 7 kHz band limit and its compander are not in the
default sound (patch 5 and the Tone and Cut knobs put the corners back; the
compander is not modelled at all). Freeze (the pedal's HOLD) is not here:
the node's loop tops out at 0.99, so a held phrase would fade 0.087 dB a
lap, and a HOLD that fades is worse than none. **Glide 0 is an instant
knob, and its price is a click**: a 200 -> 150 ms jump steps 7712 LSB into
a tone whose own steepest step is 1565. At the default Glide (4 s for the
full range) a falling Time bends the repeats 311 cents up and a rising one
380 cents down while it moves, and a 200 -> 150 ms move takes 254 ms. At the
knob's fastest glide (grid 1, 814.6 ms) a falling move reads +1171 cents and
a rising one nearly stalls the read head.

While Time moves, the line is read between samples, and the two-tap read
costs the top of the band sqrt(1 - 2 frac (1 - frac)(1 - cos 2 pi f / fs))
per pass: 5.1 dB at 15 kHz at a half frame, 48 kHz. Every static Time is
landed on the nearest whole frame at the running rate, where the read is
lossless, so the repeats of a Time you have stopped turning do not darken.
Above Mix 1 the dry falls as 2 - Mix, by `audiodelays.Echo`'s convention.

**Repeat Tone at a low rate.** The knob's corners clamp below Nyquist at
the running rate, so where the rate is too low for the top of the span the
top of the knob goes flat. At 22.05 kHz positions 111-126 (labelled
10 970-15 627 Hz) all sit on the 10 804.5 Hz clamp and do the same thing,
and position 127 takes the filter out. At 44.1 and 48 kHz every position
moves.

**Repeat Tone out, after it has been in.** The node leaves a loop filter
frozen while it is out, and a frozen low-pass would play what it held,
out of silence, when Tone came back in (26 443 LSB at Mix 2, 48 kHz,
before this was fixed on 2026-09-28). So once Tone has been in circuit
since the last `reset()`, the out stop keeps the low-pass running at a
coefficient of exactly 1, which follows the repeat sample for sample, and
Tone back in after silence is silent. Against the filter truly out that is
exact at a whole-frame read and 1 LSB where the read is fractional (while
Time glides, and where the node's single-precision delay misses the whole
frame, as `time_ms=136.054` at 44.1 kHz does). At a Feedback inside one of
Repeat Tone's stall windows (0.5, 0.75, 0.9 and on up to the 0.99 stop)
the out stop also hands the Feedback that Tone in hands, moved clear by
at most 0.00003, and the repeats differ from the filter truly out by a few
LSB: 51 at most in the runs at the 0.99 stop (8 s of -18 dBFS noise, Time
12.5 ms). The defaults, and anything since a reset that has not put Tone
in, hand the node exactly no filter; a `reset()` makes the out stop exact
again.

**Repeat Cut back in, after it has been out.** Repeat Cut has the same
node defect and no such cure: its high-pass subtracts its state, so no
corner keeps that state live without cutting. Take Cut out while the
repeats play and bring it back in after they have died away, and the
frozen state plays out of silence: 20 858 LSB at its peak over 428
samples at Mix 2, 48 kHz stereo, after a 300 Hz tone at 30 000 LSB with
Cut at 400 Hz (18 699 at 44.1 kHz, 16 352 at 22.05). A `reset()` clears
it. The fix is the node's (audiodsp's loop filters keeping their state
live while out), due after Phase 5.

A constructor `glide_ms` faster than the knob's fastest walk (under
814.6 ms, down to the 0.99 pin) stays on the audio path, and the knob
reads back at grid 1, the fastest walk it has, never at grid 0, the jump:
handing `get_macro(3)` back to `set_macro(3, ...)`, even rounded to a
7-bit MIDI value, keeps the glide (at grid 1's slew, 0.967). One slower
than the knob's 8 s plays 8 s, and the knob reads 8 s; a Glide of 0,
a negative or NaN is the jump. A constructor Time of 0 is 12.5 ms, and
a Repeat Tone or Repeat Cut of 0 is that filter out of circuit, as it is
on the node. A `max_time_ms` above 800 or NaN is 800 ms.

**Where the pitch claim stops.** The node walks the read head in single
precision, so the rate it plays is the Glide's rate rounded to the float
step of the delay, and that step doubles each time the delay passes a
power of two: a move across one plays two rates, one on each side. Near
a stall that rounding is worth several cents. The claim is stated for a
rising 150 -> 200 ms move, read on each side of the power of two it
crosses: at the Glide knob's fastest positions, strictly between grid 1
and grid 4 (814.6-860.2 ms), the part of that move past the power of
two can read up to 25.3 cents off the glide law at 48 and 44.1 kHz and
12.7 at 22.05 kHz (just above grid 3 it is 12.5 cents over the last
26 ms of the walk), so that part of the knob is not claimed on a rising
move. Grid 1 itself and everything from grid 4 up are, and the margin
at the edge is thin: grid 4 reads 9.7 cents and the worst position above
it, grid 4.05, 9.9 cents, against a 10-cent bar. Nor is a constructor
Glide under 860.2 ms claimed on a rising move, except 800 ms (slew
63/64, which single precision holds exactly): at the 0.99 pin a rising
Time can read 41 cents off. A longer rising move reaches delays where
the float step is coarser, and at a fast Glide it is not claimed:
350 -> 500 ms at grid 3 reads +15.8 cents at 48 and 44.1 kHz, 400 ->
800 ms at grid 3 reads -34.4 cents past 32 768 frames at 44.1 kHz, and
at grid 5 +10.7 at 48 kHz. At the default Glide every move the dossier
names is inside 10 cents on each side of every power of two it crosses
(worst 3.4 cents, the full-range move's last stretch).
The pitch and no-step claims are measured on inputs from -8.7 to
-0.2 dBFS. Quieter, int16 rounding decides the reading: a near-stall
rising glide is a few LSB of signal, and even a falling move at
-48.7 dBFS can step 0.4 % past its bar.

**Input ceiling.** The dry path sits at unity and the repeats add to it, so
a hot input can put the output on the int16 rail; there is no input gain
to turn down. Measured on the kit's `noise_det` at 48 kHz over 20 s, the
defaults are clean up to -3.1 dBFS peak and the shipped patches up to
-4 dBFS (patch 3, Mix 0.5, rails first). At -3.0 dBFS the defaults put a
few samples on the rail over 4 s and more. On any material, with Repeat
Cut out and Mix below 1, an input peaking at or below one LSB under
(1 - Mix) of full scale, floor(32767 (1 - Mix)) - 1, cannot reach the
rail at any Time or Feedback, because the line holds int16 and so the
repeats never exceed Mix x full scale: -3.1 dBFS at the default Mix 0.3,
-6.1 dBFS at patch 3. At exactly (1 - Mix) of full scale the sum can round
onto 32767, the rail value, though nothing is clipped. High Feedback does
not keep building past that: at Feedback 0.99 the line saturates, and the
defaults' noise_det ceiling is still -3.1 dBFS over 20 s (at -3.0 it
rails 2284 samples). Repeat Cut's high-pass can overshoot a peak, so with
it in circuit leave more room: patch 5 (Cut at 40 Hz) is clean on
noise_det at -4 dBFS, but a 40 Hz square wave there puts 54752 samples on
the rail over 20 s, and it is clean from -6 dBFS down.

**Tail.** `tail_samples` is an upper bound on how long the repeats take to
reach exact zero after your input stops, and it is long: the loop has to
round its way down from full scale, 11 laps at the default Feedback and
685 at 0.99 (nine minutes at Time 800 ms). Since audiodsp v0.6.2 the node
steps a repeat toward zero wherever rounding would hand it back
unchanged, so with both filters out the bound holds at every Feedback.
With Repeat Tone in circuit each lap is a little longer, and the node
has a second floor of its own: wherever 0.5 / (1 - Feedback) is within a
hair of a whole number k (0.5, 0.75, 0.83, 0.875, 0.9 and on up to the
knob's top, 0.99), its loop low-pass can come to rest a hair above k LSB
and send it round for ever (a 2 LSB DC at Feedback 0.5, Tone 800 Hz,
used to leave 1 LSB going round; at 0.9, 5 LSB). So with Repeat Tone in
the class hands the node a Feedback just outside each of those windows,
at the nearer edge, at most 0.00003 from the one you set (0.99 plays as
about 0.98998 and 0.5 as 0.49999), far inside one step of the knob,
which still reads what you set. The tail then reaches exact zero there too, inside
a finite `tail_samples`. With Repeat Cut in circuit `tail_samples` is
`None`: no bound is derived there.

`capabilities = ("tempo_sync",)`: with Sync on, the class reads
`self._transport()` on every macro move and program change (not per block).
With no host transport, or a host whose tempo is not a finite positive
number (0, negative, NaN, infinite or missing), Time stays where the knob
is.
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
#: the knob's 7-bit step (0.0078).
STALL_CLEARANCE = 2.0 ** -20

#: `stall_window` widens each window by this much, relatively, either side,
#: so a Feedback on an edge that `laps_to_zero`'s own rounding puts inside
#: (a constructor value that comes back through the macro 10^-17 away) is
#: moved too. Four times under `STALL_CLEARANCE`, so a moved value is
#: never itself on the widened edge.
STALL_FUZZ = 2.0 ** -22

#: Repeat Tone out after it has been in: `damping_hz` at 32 x the rate,
#: where 1 - expf(-2 pi 32) is exactly 1.0f (`one_pole_coefficient`,
#: `audiodsp_feedback_delay.c:33-40`), so the loop low-pass's state follows
#: the tap sample for sample instead of freezing on what it held
#: (`:493-497`). `SlapbackDelay`'s constant, for the same node defect. It
#: can differ from the filter truly out by 1 LSB only where the read is
#: fractional: while Time glides, and wherever the node's float32
#: `delay_ms * rate / 1000` misses the whole frame the class asked for.
TONE_TRACK_PER_RATE = 32.0

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
    input stops, or `None` where a lap could hand a sample back unchanged.

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
    gone: where that write is still x, the peak can stay there for ever.
    The node does that (1 LSB at Feedback 0.5, 5 at 0.9, Tone 800 Hz, on
    a DC input), so the count is `None` wherever the reckoning allows it.
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
                return None
        peak = image
    return laps


def stall_window(feedback, excess):
    """The Repeat Tone stall window `feedback` sits in, as (low, high), or
    `None` outside every window.

    `laps_to_zero(f, excess)` is `None` exactly when some whole peak x it
    reaches is handed back: the rounding branch taken,
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
    so `get_macro(1)` still names the setting that plays."""
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
    audiodsp tier; zero latency.

    **What the default surrenders:** no band limit and no compander in the
    default sound (patch 5 and the Tone and Cut knobs are the corners), no
    HOLD, and Glide 0's instant knob clicks. At the default Glide a falling
    Time bends the repeats +311 cents while it moves, a rising one -380.
    """

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
        #: True once Repeat Tone has been handed an in-circuit corner since
        #: the node was built or cleared. From then on the loop low-pass's
        #: state is live, and the out stop hands `TONE_TRACK_PER_RATE` x the
        #: rate, not 0.
        self._tone_used = False
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
        self._tone_used = False

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
        damping = self._tone_damping(self._macros[TONE_I])
        if damping > 0.0:
            self._tone_used = True
        elif self._tone_used:
            # The node updates its loop low-pass only while the coefficient
            # is above 0 (`audiodsp_feedback_delay.c:493-497`), so handing 0
            # after Repeat Tone has been in would freeze whatever the filter
            # held, and a later Tone move would play it out of silence. A
            # coefficient of exactly 1 keeps the state on the tap instead.
            damping = TONE_TRACK_PER_RATE * self._sample_rate
        self._damping = damping
        if damping > 0.0:
            # With Repeat Tone in, the node can hold a small value for ever
            # at Feedback values a hair either side of 1 - 0.5 / k; the node
            # is handed the nearer edge of that window instead.
            feedback = self._loop_feedback(feedback)
        self._feedback = feedback
        self._delay.set(
            delay_slew=slew,
            delay_ms=self._node_ms,
            feedback=feedback,
            mix=self._value(MIX_I),
            damping_hz=damping,
            cut_hz=self._cut_hz(self._macros[CUT_I]))

    def _loop_feedback(self, feedback):
        """The Feedback handed to the node with Repeat Tone in circuit:
        `clear_of_stalls` at this Tone's excess."""
        return clear_of_stalls(feedback, self._tone_excess()[1])

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

        Finite at every Feedback with both filters out. With Repeat Tone
        in, each lap is `memory` frames longer, the time the low-pass takes
        to forget the lap before, and the count is `None` near the Feedback
        values where the node can hold a small value for ever
        (`laps_to_zero`). `None` with Repeat Cut in circuit, whose
        high-pass can more than double a peak in one pass, so the per-lap
        argument does not hold; the node measures that case rather than
        bounding it, and this class has no bound for it either.
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
        if laps is None:
            return None
        return int(laps * (self._reach + 1 + memory))

    def _tone_excess(self):
        """(frames, relative excess) for Repeat Tone's low-pass. After
        `frames` frames whatever the state held before, full scale at
        most, weighs under 2^-17 LSB, which is under 2^-17 of any non-zero
        peak; and the single-precision state can rest up to 2^-24 / a of
        the peak above it, a being the coefficient, because a step
        a (v - y) under half an ulp rounds away. Read from the `damping_hz`
        the node was handed, so the out stop after Tone has been in (the
        low-pass tracking the tap at a coefficient of 1) counts one frame
        of memory. (0, 0.0) with the filter truly out."""
        damping = self._damping
        if damping <= 0.0:
            return 0, 0.0
        per_frame = 2.0 * math.pi * damping / self._sample_rate
        coefficient = 1.0 - math.exp(-per_frame)
        frames = int(math.ceil(32.0 * math.log(2.0) / per_frame))
        return frames, 2.0 ** -17 + 2.0 ** -24 / coefficient
