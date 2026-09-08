"""`Notch` - the two-pole band-stop: everything except one band, tuned.

Rebuilt from scratch for the effects program's Phase 2 against
`workspace docs/effects-internal/dossiers/Notch.md`. The old `eq.py:Notch` is not consulted except for
the seven defects the dossier's section 7 names.

**What it sounds like.** One knob says where, one says how wide, and what
comes out is the input with a slice taken out of it and nothing else
touched - a whistle, a feedback tone or a mains hum goes and the rest of the
mix does not move, because a notch is exactly unity at DC and at Nyquist by
construction. Width is a bandwidth, not a depth: at Q 0.7 the notch is
wider than the note it sits on and reads as a scoop; at Q 30 it is a few
hertz across and you hear the tone leave without hearing the music change.
Harmonics adds a second notch an octave up, half as wide in hertz, because
mains hum is a series and one notch at 50 or 60 Hz leaves the buzz. Depth is
a blend, not a filter control - at 0 the class is a wire.

**Portability tier: audioif** (`REQUIRES = ("audiobiquad",)`). All three
sections are `audiobiquad.Biquad`: float state, and a tail that reaches
exact zero. The ported `synthio.Biquad` cannot - the mains-hum setting
`Notch(60 Hz, q=8)` parks on 2 LSB of DC and `Notch(20 Hz, q=32)` on 18, and
they hold it for ever (audioif#23, dossier A3 and A16), which is Tier 1's
first invariant failing at exactly the settings this class is for.

**What that costs, said here because a caller has to know it.** A `float`
coefficient set cannot put the notch's zeros exactly on the unit circle:
`b0` and `b1` are rounded independently, so the rejection at the centre is
`|2*b0*cos(w0) + b1| * (1+alpha) / (2*alpha*sin(w0))` rather than nothing at
all. Measured (dossier A16, 48 kHz): under one LSB - a true null - from
500 Hz up at Q <= 12, **-35.65 dB at 60 Hz Q 12**, and **-11.21 dB at
20 Hz Q 32**. So this class is a clean utility notch across the musical range and
a 35 dB hum *reducer* at the bottom, not a hum eliminator. The dossier's T1
is recorded disconfirmed below about 250 Hz for that reason, and its section
5 carries the one node ask that would recover 17-36 dB of it. The ported
kernel is deeper there and cannot hold the Tier 1 invariant; that trade is
dossier section 8, D1 and D2.

**And one more measured edge.** T2 asks for unity within 0.1 dB at 0.48*Fs
at every setting. It holds everywhere except the top of the Frequency span
at the bottom of the Width span, where the notch's *own band* reaches that
far: at 16 kHz and Q 0.5 the band is 32 kHz wide and 0.48*Fs reads
-0.21 dB. That is the probe sitting inside the band, not the filter
leaking, and it is why Frequency clamps at 0.4*Fs rather than at Nyquist.

**Cost.** Three sections, always built, two of them wires at patch 0 - and
a wire costs what a notch costs, because the kernel runs each recursion
before it blends and there is no branch on `mix`
(`audioif/src/shared/audioif_filter_f32.c:216-241`). So Harmonics buys back
no CPU: the class costs three sections at every setting. The dossier budgets
1.5 % of one stereo block's real-time deadline on the ESP32-P4 and 5 % on
the S3 with one notch and 2.5 % / 9 % with two, and since the two are the
same figure it is the higher pair that governs; the board run in the
evidence pack is what settles it.

**Latency: zero samples, at every setting and every rate.** Every section is
a recursive biquad reading no sample it has not been given. No option on
this class adds a lookahead, a partition or a window, so there is no
latency-adding option to default off and none to name in milliseconds.

`capabilities = ()`: nothing in a notch is measured in beats - its controls
are hertz and a dimensionless Q - and this class never reads
`self._transport()`.
"""

VENDOR = "PyDevices"

try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None                  # `_require_modules` raises for us

from . import _component


#: `audiobiquad`'s own clamp (`AUDIOIF_FILTER_F32_MIN_Q` / `MAX_Q`,
#: `audioif/src/shared/audioif_filter_f32.c:21-22`), mirrored because the
#: module does not export it. It bites on the harmonic notch: Width 32
#: doubles to 64 and lands on 60, so the harmonic is 6.7 % wider in hertz
#: than the fundamental there. Stated rather than hidden - dossier D3.
MIN_Q = 0.05
MAX_Q = 60.0

#: The harmonic notch sits at this multiple of the centre, and its Q is
#: multiplied by the same number so that its width *in hertz* matches the
#: fundamental's: width is f/Q (S3), so f -> 2f at Q -> 2Q is the same
#: number of hertz. Mains harmonics are exact multiples, so the narrow one
#: is what a hum eliminator wants (dossier A16, D3: 5.00 Hz against 10.00).
HARMONIC = 2.0

#: The highest centre this class will tune to, as a fraction of the rate.
#: Not `_hz()`'s 0.49: T2 reads unity at 0.48*Fs, and a notch centred above
#: this has its own band over that probe. Clamps, never refuses - the
#: rate-honesty invariant (vision section 3).
CENTRE_CEILING = 0.4

#: The trim is one high shelf at a subsonic corner, which is a broadband
#: gain everywhere above it: no node on the palette gives gain above unity
#: (`MixerVoice.level` clamps to 0..1, `audiomath.Multiply` only
#: attenuates), and there is no route from Python to a biquad's `b`
#: coefficients. Measured on this node at 48 000 / 44 100 / 22 050 Hz and
#: -12/-6/+6/+12 dB: worst deviation from the requested gain 0.105 dB, at
#: 20 Hz, and 0.021 dB or better from 50 Hz up (dossier A16).
TRIM_CORNER_HZ = 5.0
TRIM_Q = 0.7071067811865476

#: A trim under this is built as a wire rather than a pass of arithmetic
#: that must come back byte-identical. A BIPOLAR macro has no exact centre
#: on the 0-127 grid - 64/127 puts a +/-12 dB trim at 0.094 dB - so without
#: a floor a patch whose trim reads "0" would not be one.
FLAT_DB = 0.2


class Notch(_component.Component):
    """A tuned band-stop with a bandwidth knob, an octave-up harmonic notch
    and a make-up trim. Three `audiobiquad` sections; audioif tier; zero
    latency."""

    NAME = 'Notch'
    DISPLAY_NAME = 'Notch'
    CATEGORIES = ('Filter', 'EQ')
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0

    #: Measured, not assumed: the longest burst-to-exact-zero this class
    #: reaches anywhere in its own span - 20 Hz at Width 32 with the
    #: harmonic notch on and the trim at +12 dB, struck with a full-scale
    #: burst - is 140 405 samples after the source goes silent, at 48 kHz.
    #: Lower rates are shorter in frames (a tail is a time, and 48 kHz has
    #: the most frames in it), so this is a ceiling at every rate. Declared
    #: at the next multiple of 2048. Patch 0's own tail is 88 samples.
    TAIL_SAMPLES = 143360

    MACRO_LABELS = ("Frequency", "Width", "Harmonics", "Depth", "Trim")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "TOGGLE",
                   3: "UNIPOLAR", 4: "BIPOLAR"}
    _MACRO_RANGES = (
        (20.0, 16000.0, "log"),         # 0  Frequency, Hz
        (0.5, 32.0, "log"),             # 1  Width, as Q; bandwidth is f0/Q
        (0.0, 1.0),                     # 2  Harmonics, 0 = one notch
        (0.0, 1.0),                     # 3  Depth, 0 is a wire
        (-12.0, 12.0),                  # 4  Trim, dB
    )
    #: Named for settings, never for products, and every value is
    #: `macro_of()` of the setting in the comment beside it. A 7-bit step on
    #: a 20 Hz - 16 kHz log span is 5.4 %, so the settings below are what
    #: the grid stands for and not what was asked for.
    PATCHES = {
        0: ("Wide Notch", (74, 11, 0, 127, 64)),        # 983 Hz, Q 0.72
        1: ("Hum 50", (17, 97, 127, 127, 64)),          # 48.9 Hz, Q 12.0, 2
        2: ("Hum 60", (21, 97, 127, 127, 64)),          # 60.4 Hz, Q 12.0, 2
        3: ("Feedback Tamer", (92, 118, 0, 127, 64)),   # 2535 Hz, Q 23.8
        4: ("Mud Scoop", (51, 27, 0, 76, 64)),          # 293 Hz, Q 1.21,
                                                        # depth 0.60
        5: ("Whistle Kill", (114, 125, 0, 127, 64)),    # 8072 Hz, Q 30.0
    }

    # -- construction --------------------------------------------------

    def _build(self, frequency=1000.0, q=0.7071067811865476, harmonics=1,
               depth=1.0, trim_db=0.0, patch=None):
        """Three sections, in chain order: the fundamental notch, the
        harmonic notch, then the trim.

        The trim closes the chain because it is the *output* make-up and
        each section writes int16 and clips there
        (`audioif/src/shared/audioif_filter_f32.c:43-51`); a boost applied
        before the notch would clip material the notch is about to remove.

        The harmonic section is built at every setting and left as a wire
        when Harmonics is off - a node cannot be added to a running graph,
        and Harmonics is a live macro. It is also left as a wire when 2*f0
        would land above the centre ceiling, which is what a rate-honest
        harmonic notch does at 22.05 kHz rather than folding.

        `harmonics` is a count, 1 or 2; `depth` and `q` are in the units of
        their macros and `frequency` and `trim_db` in theirs. Nothing here
        adds latency.
        """
        rate = self._sample_rate
        channels = self._channel_count

        def section(mode):
            node = audiobiquad.Biquad(mode=mode, frequency=1000.0,
                                      Q=TRIM_Q, gain_db=0.0, mix=0.0,
                                      sample_rate=rate,
                                      channel_count=channels)
            return self._own(node, reset=True, deinit=True)

        self._fundamental = section(audiobiquad.NOTCH)
        self._harmonic = section(audiobiquad.NOTCH)
        self._trim = section(audiobiquad.HIGH_SHELF)

        upstream = self._source
        for node in self._nodes:
            node.play(upstream)
            upstream = node
        self._output = upstream

        self._init_macros(
            (frequency, q, 0.0 if int(harmonics) <= 1 else 1.0, depth,
             trim_db),
            patch)

    # -- the control laws ----------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _centre(self, hz):
        """A centre frequency, clamped into the band a notch can hold.

        `_hz()` clamps at 0.49*Fs, which is where a biquad stops being a
        biquad; this clamps lower, at 0.4*Fs, which is where a notch stops
        leaving 0.48*Fs alone. Clamps rather than raising, which is the
        rate-honesty invariant and the fourth defect section 7 names.
        """
        return min(self._hz(hz), self._sample_rate * CENTRE_CEILING)

    def _refresh(self):
        """Push all five knobs at once.

        One routine rather than five, because every setting here depends on
        at least one other: the harmonic section's frequency and Q are the
        fundamental's doubled, whether it is in circuit depends on
        Harmonics *and* on whether 2*f0 fits under the ceiling, and every
        section's `mix` depends on Depth.
        """
        asked = self._value(0)
        centre = self._centre(asked)
        width = min(MAX_Q, max(MIN_Q, self._value(1)))
        depth = self._value(3)
        trim_db = self._value(4)
        stacked = self._macros[2] >= 0.5

        self._fundamental.frequency = centre
        self._fundamental.Q = width
        self._fundamental.mix = depth

        harmonic = HARMONIC * centre
        reachable = harmonic <= self._sample_rate * CENTRE_CEILING
        self._harmonic.frequency = self._centre(harmonic)
        self._harmonic.Q = min(MAX_Q, max(MIN_Q, HARMONIC * width))
        self._harmonic.mix = depth if (stacked and reachable) else 0.0

        self._trim.frequency = self._hz(TRIM_CORNER_HZ)
        self._trim.Q = TRIM_Q
        self._trim.gain_db = trim_db
        # The trim is the notch's make-up, so it goes with the notch: at
        # Depth 0 the class is a wire, trim included, which is what Tier 1's
        # bypass invariant asks of it.
        self._trim.mix = 1.0 if (depth > 0.0 and abs(trim_db) >= FLAT_DB) \
            else 0.0

    def _apply_macro(self, index, position):
        del index, position
        self._refresh()
