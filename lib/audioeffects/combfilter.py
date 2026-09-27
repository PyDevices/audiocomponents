"""`CombFilter` - a delay line short enough to be a pitch, fed back on
itself: the naked resonator every flanger, every Karplus-Strong string and
every reverb tank is built out of.

Rebuilt from scratch for the effects program's Phase 2 against
`workspace docs/effects-internal/dossiers/CombFilter.md`, whose trait table and surface were frozen at
Station A before this file existed. The old `eq.py:CombFilter` is not
consulted except for the seven defects the dossier's section 7 names.

**What it sounds like.** Tune it and the signal grows a set of resonances on
the harmonic series of that note - 220, 440, 660, 880 - so noise turns into a
pitch and a chord turns metallic. Feedback is how hard those resonances
stand: at 0.3 it is a ripple, at 0.7 it is the sound of a comb, at 0.95 a
click rings for seconds on the note you tuned it to. Mix runs from a wire
through dry-plus-comb to the filter on its own. Tone darkens each pass the
way a real resonator's losses do, so the ring goes dull as it dies rather
than staying bright to the end. Glide is the tuning knob's own portamento:
turn Frequency with Glide up and the comb *bends* to the new note.

**Portability tier: audiodsp** (`REQUIRES = ("audioecho", "audiobiquad")`).
`audiodelays.Echo` - the only stock delay - quantises its line to whole
samples and floors it at its own buffer length, so on the library's standard
buffer every frequency from 47 to 880 Hz comes out as the same 46.88 Hz comb
(dossier A2, A12). That is not a tuning error, it is the absence of tuning,
and there is no honest stock fallback: even a 512-byte buffer only reaches
187.5 Hz. On a stock CircuitPython board this module imports cleanly and
construction raises a clear `ImportError`, so the rest of `eq.py` stays
reachable.

**Cost: two nodes.** One `audiobiquad.Biquad` high shelf at a subsonic
corner is the Trim, and it sits **in front**; one `audioecho.FeedbackDelay`
behind it carries the line, the feedback, the blend, the in-loop damping and
the glide. A shelf is the only route to a broadband gain on this palette
(`MixerVoice.level` clamps to 0..1 and `audiomath.Multiply` only attenuates).
Desktop anchor, net of the source pump: 98.8 ns per stereo frame, 0.47 % of
the 20 833 ns one has at 48 kHz. The dossier budgets 2 % of that deadline on
the ESP32-P4 and 7 % on the S3; the board run in the evidence pack settles it.

**Trim is headroom, and it is taken before the gain.** A comb's peak gain is
`1/(1-Feedback)`: +10 dB at 0.7, +22 dB at 0.92, +26 dB at 0.95. Feed a
loud note at the tuned pitch into that and the node's output saturates
(`audiodsp_feedback_delay.c:308-316`). Measured, a 220 Hz sine at -9.5 dBFS
through Feedback 0.92: with the trim **behind** the comb, -9 dB of it leaves
a peak of 12 083 - which is the rail, attenuated, i.e. distortion made quiet;
with the trim **in front**, -18 dB leaves 15 392 and the comb never reaches
the rail at all. So Trim runs to -18 dB rather than the -12 a make-up would
need, and turning it down is how you make room for the resonance.

**One transient this class cannot argue away.** A program change into a comb
whose line is already ringing sums the new dry signal against the old line,
and at Mix 1 that can reach the rail. Measured on the library smoke's own
sequence - six patches, one instance, no reset between them - patches 1, 3
and 4 peak at 32 768; every one of those same patches on a fresh instance
peaks between 8 210 and 18 925 on the same probe. It is what a feedback line
is, not what these patches are. `reset()` empties it.

**Latency: zero samples, at every setting and every rate.** The node writes
`dry*source + wet*loop` in the frame the input arrives, so an impulse comes
out where it went in, at full amplitude. **No option on this class adds
latency**, so there is none to default off and none to name in milliseconds.
The one number worth stating: at Mix 2 there is no dry path at all, and the
first sound then arrives one line-length late - 0.25 ms at 4 kHz, 50 ms at
20 Hz. That is the comb, not latency; it is the delay you asked for by
tuning it.

**The tail reaches exact zero at every Feedback and every tuning.** Up to
audiodsp v0.6.1 it could not above Feedback 0.5: the node's int16 line
rounded the feedback write to nearest, so every `|c| <= 0.5/(1-g)` was a
fixed point of the loop, and at a tuning whose read lands near a whole
sample the tail parked on a few LSB for as long as the graph ran (10 LSB at
1000 Hz / Feedback 0.95), ringing at the nearest whole-sample period
(+17.4 cents at 1760 Hz / Feedback 0.8). audiodsp v0.6.2 (#154) truncates
the fed-back term toward zero exactly where rounding would hand it back
unchanged, so the line empties: from full scale its loudest sample falls by
the geometric law until it is within `floor(0.5/(1-g))` LSB, then by at
least one LSB a lap. Measured at v0.6.2, 48 kHz, Tone off and Trim flat,
after an impulse: 1760 Hz / 0.8 is silent after 928 frames, 1000 Hz / 0.95
after 7 488, and 20 Hz / 0.95, the slowest corner of the surface, after
374 400 (7.8 s), each inside that lap bound times the line (511 413 frames,
10.7 s, at 20 Hz / 0.95). While it rings, it rings at the fractional delay
it was asked for: 1760 Hz / 0.8 at 27.262 frames against the asked 27.273,
0.7 cents, through its tenth repeat, and the first-repeat tap lands within
0.01 cents. `TAIL_SAMPLES` stays `None` for now: a finite bound that depends
on the setting is derivable, but declaring one changes an adopted class's
surface, and that is the Phase 5 gate audit's call, not the pin move's.
This class is a tuned resonator: Frequency is a pitch, and the first-repeat
tap is the note it plays.

**Two traits this class does not have.** The *negative* comb, whose peaks sit
on the odd half-multiples and which sounds hollow rather than pitched, is
**not built**: it composes exactly out of nodes that exist, but only at seven
nodes, three delay lines and a tuning-dependent pre-delay of twice the line,
which is about four times this class's whole cost budget (dossier section 4).
And the textbook peak height holds to 0.2 dB only at and below 2 kHz: above
that the line's fractional tap is itself a one-zero low-pass inside the loop
and the peak sags - measured -0.07 dB at 880 Hz, -0.23 at 1760, -1.02 at
3520, and **exactly 0.00 wherever the sample rate divides by the frequency
into a whole number**, which at 48 kHz includes 1000, 2000, 3000 and 4000 Hz.

`capabilities = ()`: a comb's delay is a *pitch*, not a rhythm - 1/f seconds,
where f is the note you hear - so syncing it to a tempo would be meaningless,
and this class never reads `self._transport()`.
"""

VENDOR = "PyDevices"

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None                    # `_require_modules` raises for us
try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None

from . import _component


#: The line, in milliseconds. 20 Hz wants 50 ms and the node keeps one frame
#: of headroom below the line's length (`audiodsp_feedback_delay.c:142-150`),
#: so a 50 ms line would tune the bottom of the range to 20.02 Hz. 60 ms is
#: the next round number that clears it; the cost is RAM, 11.5 KB of stereo
#: int16 at 48 kHz, allocated once.
MAX_DELAY_MS = 60.0

#: The top of the Tone travel means *off*, not "a low-pass at 24 kHz". The
#: node's one-pole coefficient at 24 kHz on a 48 kHz graph is 0.957, not 1,
#: so it would still shade the top of every pass; `damping_hz = 0` is the
#: node's own "no filter at all" (`audiodsp_feedback_delay.c:31-38`). A macro
#: at 127/127 maps to exactly this value, so the off position is exact.
TONE_OFF_HZ = 24000.0

#: A trim under this is built as a wire rather than a pass of arithmetic that
#: must come back byte-identical. MIDI 64 is the exact centre of a BIPOLAR
#: span since audiocomponents#87, so the detent itself is 0.000 dB; what this
#: floor still covers is the codes either side of it, which a knob passes
#: through. `LowPass` uses the same floor, for the same reason.
FLAT_DB = 0.2

#: The Mix macro snaps to exactly 1.0 inside this. Same grid, worse
#: consequence: 64/127 of a 0..2 span is 1.0079, which drops the dry leg to
#: 0.9921, and the feedforward comb's null at Feedback 0 stops being total -
#: -42 dB instead of silence. The snap is 1.3 MIDI steps wide and inaudible;
#: the null it protects is a stated trait.
MIX_UNITY_SNAP = 0.02

#: The trim is one high shelf at a subsonic corner, which is a broadband gain
#: everywhere above it. `LowPass` measured this node at that corner flat to
#: 0.010 dB from 50 Hz to 15 kHz at 48/44.1/22.05 kHz and -12..+12 dB; a
#: 10 Hz corner reads 0.95 dB out at 20 Hz, which is why the corner is 5.
TRIM_CORNER_HZ = 5.0
TRIM_Q = 0.7071067811865476


class CombFilter(_component.Component):
    """A tuned feedback comb: one delay line of 1/f seconds fed back on
    itself, with an in-loop tone control, a make-up trim and a glide on the
    tuning knob. Two nodes; audiodsp tier; zero latency."""

    NAME = 'CombFilter'
    DISPLAY_NAME = 'Comb Filter'
    CATEGORIES = ('Filter',)
    VERSION = '0.0.2'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho", "audiobiquad")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0

    #: Declared unbounded, conservatively. Since audiodsp v0.6.2 (#154) the
    #: tail reaches exact zero at every setting, inside
    #: `laps * (ceil(F_s/Frequency) + 1)` frames (the module docstring has
    #: the lap law and the numbers); up to v0.6.1 it could park for ever
    #: above Feedback 0.5. Declaring the finite bound is the gate audit's
    #: change to make.
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Frequency", "Feedback", "Mix", "Tone", "Trim", "Glide")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "BIPOLAR", 5: "UNIPOLAR"}
    _MACRO_RANGES = (
        (20.0, 4000.0, "log"),      # 0  Frequency, Hz (line 50 ms..0.25 ms)
        (0.0, 0.95),                # 1  Feedback, g; the node clamps at 0.99
        (0.0, 2.0),                 # 2  Mix; 0 wire, 1 dry+wet, 2 wet only
        (500.0, 24000.0, "log"),    # 3  Tone, in-loop low-pass; top is off
        (-18.0, 18.0),              # 4  Trim, dB (input)
        (0.0, 1.0),                 # 5  Glide, delay-seconds per second
    )
    #: Named for settings, never for products; every value is `macro_of()` of
    #: the setting in the comment beside it.
    PATCHES = {
        0: ("Metallic", (74, 94, 64, 127, 64, 6)),        # 440 Hz, 0.7,
                                                          # Mix 1, tone off
        1: ("Ringing Pitch", (57, 123, 64, 127, 53, 6)),  # 220 Hz, 0.92,
                                                          # Mix 1, -3 dB
        2: ("Soft Ripple", (41, 40, 32, 127, 64, 6)),     # 110 Hz, 0.3,
                                                          # Mix 0.5
        3: ("Dark Resonator", (48, 114, 64, 45, 42, 6)),  # 150 Hz, 0.85,
                                                          # tone 2 kHz, -6 dB
        4: ("Single Slap", (24, 0, 64, 127, 64, 6)),      # 55 Hz, 0.0, Mix 1
        5: ("Filter Only", (94, 107, 127, 127, 64, 6)),   # 1 kHz, 0.8, Mix 2
    }

    # -- construction --------------------------------------------------

    def _build(self, frequency=440.0, feedback=0.7, mix=1.0,
               tone_hz=TONE_OFF_HZ, trim_db=0.0, glide=0.05, patch=None):
        """Two nodes, in chain order: the trim, then the comb.

        The trim **opens** the chain, which is the one place this class
        parts company with `LowPass`. A comb is linear, so `trim . comb` and
        `comb . trim` are the same filter on paper -- but not in int16: the
        comb node writes its output through `to_s16`, which saturates
        (`audiodsp_feedback_delay.c:308-316`), and a peak of `1/(1-g)` is
        +21.9 dB at Feedback 0.92. Measured on the library's own smoke probe
        (11 000 LSB, -9.5 dBFS), the trim behind the comb left patches 1 and
        3 pinned at the rail, 32 768; the same trims in front of it clear the
        rail with room to spare. Headroom has to be taken before the gain,
        not after.

        `frequency` is in hertz and every other option is in the units of its
        macro. Nothing here adds latency.
        """
        self._trim = self._own(audiobiquad.Biquad(
            mode=audiobiquad.HIGH_SHELF,
            frequency=self._hz(TRIM_CORNER_HZ), Q=TRIM_Q, gain_db=0.0,
            mix=0.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._comb = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=MAX_DELAY_MS,
            delay_ms=1000.0 / self._hz(frequency),
            feedback=0.0, mix=0.0))

        upstream = self._source
        for node in self._nodes:
            node.play(upstream)
            upstream = node
        self._output = upstream

        self._init_macros(
            (frequency, feedback, mix, tone_hz, trim_db, glide), patch)

    # -- the control laws ----------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _refresh(self):
        """Push all six knobs at once.

        One routine rather than six, because the trim's own `mix` depends on
        the Mix knob as well as on the trim: at Mix 0 this class is a wire,
        trim included, which is what Tier 1's bypass invariant asks of it.
        """
        frequency = self._hz(self._value(0))
        blend = self._value(2)
        if abs(blend - 1.0) <= MIX_UNITY_SNAP:
            blend = 1.0
        tone = self._value(3)
        trim_db = self._value(4)

        self._comb.set(
            delay_ms=1000.0 / frequency,
            feedback=self._value(1),
            mix=blend,
            damping_hz=0.0 if tone >= TONE_OFF_HZ else self._hz(tone),
            delay_slew=self._value(5))

        self._trim.gain_db = trim_db
        self._trim.mix = (1.0 if blend > 0.0 and abs(trim_db) >= FLAT_DB
                          else 0.0)

    def _apply_macro(self, index, position):
        del index, position
        self._refresh()
