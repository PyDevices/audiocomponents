"""A lookahead brickwall limiter: a ceiling the signal does not get past.

Dossier: `docs/effects/Limiter.md`. Evidence:
`docs/effects/Limiter-evidence.md`.

There is no circuit behind this class and no pedal it is named after. What it
models is a *specification* - ITU-R BS.1770-5 Annex 2 for what "the peak did
not exceed the ceiling" means, and Hamalainen's DAFx-02 paper for what a
lookahead limiter has to do to keep that promise. The classic peak limiters
are `Compressor`'s characters; none of them looks ahead and none of them
guarantees a ceiling.

**Two nodes, and the second is the one that makes the promise.**

    source -> shape (DYN_COMPRESS, ratio 1e6)  -> catch (DYN_LIMIT) -> output
              knee, lookahead, true peak, gain    attack 0, no lookahead

A lone lookahead limiter is *worse* than none: the node delays the audio while
its detector releases on the live input, so by the time a peak reaches the
output the gain has been coming back up for the whole lookahead window. That is
the DAFx-02 result, and it is measurable - a 1 ms burst into a -12 dBFS ceiling
comes out at -12.00 dBFS with no lookahead and **-10.55 dBFS with 10 ms of it**
on one node. The second `Dynamics`, at the same ceiling with `attack_ms=0` and
no lookahead of its own, holds -12.00 dBFS at every setting: with a zero
attack the envelope *is* the current sample, `DYN_LIMIT` returns exactly
`-over`, and that gain multiplies that same sample. A sample-exact brickwall by
construction, not an approximation.

**Latency: zero by default.** The Lookahead macro is the only thing in this
class that delays anything, it defaults to **0 ms**, and `latency_samples`
reports what it is set to the moment it moves - `floor(ms x rate / 1000)`, up
to 480 samples (10 ms) at 48 kHz. True Peak adds **no latency at all**: the 4x
reconstruction runs on the detector signal and never reaches the audio path.

**True Peak costs headroom, not time.** With it off, a worst-phase tone at a
quarter of the sample rate leaves a -6 dBFS ceiling **3.01 dB high** in the
reconstructed waveform that a converter will actually produce - the ceiling is
held on the samples and broken between them. With it on the escape is
**0.17 dB**. Turn it on for anything that will be converted or encoded.

**Release is the distortion knob, and it is honest about it.** The gain is
computed per sample with no smoothing of its own, so release time and
smoothing are one control. A 60 Hz sine driven 12 dB into the ceiling measures
**12.0 % THD at the 5 ms end** of the macro and 0.36 % at 300 ms; the default
patch sits at 149 ms and 0.71 %. Fast release on bass material is a fuzz
setting - use it on purpose or stay above about 110 ms.

Stereo is **always channel-linked**: the detector takes the maximum across the
two channels, so the image does not wander when one side is loud. That is not
switchable on this node. A mono source is limited on its one channel, not
summed.
"""

VENDOR = "PyDevices"

from .. import _component

try:
    import audiodynamics
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiodynamics = None


#: `DYN_LIMIT` has no knee term in its gain computer at all
#: (`audioif_dynamics.c:369-370`), so the Knee macro rides a `DYN_COMPRESS`
#: node instead, at a ratio high enough that Knee 0 measures 0.0000 dB/dB of
#: slope above the threshold - a brickwall by measurement, not by mode name.
_BRICKWALL_RATIO = 1.0e6

#: The detector reads `gain_to_db(envelope + 1e-6)` (`audioif_dynamics.c:749`),
#: which puts a full-scale sample a hair over 0 dBFS and pulls it down by one
#: LSB. Everything at or below the ceiling has to pass untouched, so the class
#: hands each node a threshold this much higher. It is 2e-5 of an LSB at full
#: scale: measured, it takes the ramp probe from 28 differing samples to 0 and
#: moves the ceiling by at most 0.0003 dB.
_EPSILON_DB = 0.0002

#: The catch stage recovers in 5 ms whatever the Release macro says. It only
#: ever acts on what the shape stage let past, which is a transient by
#: definition, so a long release here would duck the signal behind every peak
#: the first stage already handled.
_CATCH_RELEASE_MS = 5.0


class Limiter(_component.Component):
    """Brickwall limiting against a ceiling, with optional lookahead and
    true-peak detection. `audioif` tier: it needs `audiodynamics`.

    Two `audiodynamics.Dynamics` in series - a shaping stage that carries the
    Knee, the Lookahead and the true-peak detector, and a catch stage that is
    the reason lookahead never overshoots. A lone lookahead limiter is worse
    than none: measured, a 1 ms burst into a -12 dBFS ceiling comes out at
    -12.00 dBFS with no lookahead and -10.55 dBFS with 10 ms of it, because
    the node delays the audio while its detector releases on the live input.
    With the catch stage the same burst reads -12.00 dBFS at every setting.

    **Latency is 0 by default.** Lookahead is the only thing here that delays
    anything; it spans **0 ms to 10 ms** (up to **480 samples** at 48 kHz) and
    `latency_samples` reports `floor(ms x rate / 1000)` the moment the macro
    moves. True Peak adds no latency at all - the 4x reconstruction runs on
    the detector signal and never reaches the audio.

    **Release is the distortion knob and this docstring says so.** The gain is
    computed per sample with no smoothing of its own, so release time and
    smoothing are one control. A 60 Hz sine driven 12 dB into the ceiling
    measures **12.0 % THD at the 5 ms end** of the Release macro, 3.1 % at
    30 ms and 0.36 % at 300 ms; the default patch sits at 149 ms and 0.71 %.
    The 1 % line falls between 100 ms (1.05 %) and 149 ms. Fast release on low
    material is a fuzz setting - reach for it on purpose, or stay above about
    110 ms.

    **True Peak costs headroom, not time.** Off, a worst-phase tone at a
    quarter of the sample rate leaves a -6 dBFS ceiling 3.01 dB high in the
    waveform a converter will actually reconstruct. On, the escape is 0.17 dB.
    """

    NAME = 'Limiter'
    DISPLAY_NAME = 'Limiter'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiodynamics",)

    #: A ceiling has no tempo. The class never reads `self._transport()`.
    CAPABILITIES = ()

    #: Both are per instance, not per class: the lookahead is a macro. The
    #: class attributes are the default patch's values, and the properties
    #: below report what this instance is actually set to.
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Ceiling", "Gain", "Lookahead", "Release", "True Peak",
                    "Knee")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "TOGGLE",
        5: "UNIPOLAR",
    }
    #: True Peak is a switch worn as a knob: at or above the middle it is on.
    #: On means `true_peak=2`, the 4x polyphase detector. The node's
    #: `true_peak=1` half-band estimate is deliberately not reachable from
    #: here - it leaves 1.07 dB above the ceiling where the trait allows 0.5.
    _MACRO_RANGES = ((-24.0, 0.0), (0.0, 24.0), (0.0, 10.0),
                     (5.0, 2000.0, "log"), (0.0, 1.0), (0.0, 12.0))
    PATCHES = {
        0: ("Safety Ceiling", (122, 0, 0, 72, 0, 0)),
        1: ("Catch The Peaks", (122, 0, 19, 53, 127, 0)),
        2: ("Loud", (125, 64, 38, 38, 127, 0)),
        3: ("Soft Ceiling", (116, 0, 0, 78, 0, 95)),
        4: ("Delivery Ceiling", (122, 0, 25, 72, 127, 0)),
    }

    #: The 4x true-peak level. `True` still means the node's older half-band
    #: estimate, which is why this is a number here and not a flag.
    TRUE_PEAK_OVERSAMPLED = 2

    def _build(self, ceiling_db=-1.0, gain_db=0.0, lookahead_ms=0.0,
               release_ms=150.0, true_peak=False, knee_db=0.0, patch=None):
        """`lookahead_ms` is the only latency this class has and it defaults
        to **0 ms**; at its maximum it is 10 ms (480 samples at 48 kHz), and
        `latency_samples` reports it the moment it moves. `true_peak` adds no
        latency. `release_ms` below about 110 ms is a distortion setting on
        low material - see the class docstring."""
        self._latency = 0
        self._shape = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            ratio=_BRICKWALL_RATIO, attack_ms=0.0))
        self._shape.play(self._source)
        self._catch = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_LIMIT,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            attack_ms=0.0, release_ms=_CATCH_RELEASE_MS))
        self._catch.play(self._shape)
        self._output = self._catch
        self._init_macros((ceiling_db, gain_db, lookahead_ms, release_ms,
                           1.0 if true_peak else 0.0, knee_db), patch)

    # -- the live surface ---------------------------------------------

    @property
    def latency_samples(self):
        """The lookahead, in samples: 0 unless the Lookahead macro has been
        moved off zero."""
        self._check_live()
        return self._latency

    @property
    def tail_samples(self):
        """The same number. The only thing this class holds after its input
        goes silent is whatever is still in the lookahead delay; there is no
        reverberant or feedback state anywhere in it."""
        self._check_live()
        return self._latency

    # -- macros --------------------------------------------------------

    def _apply_macro(self, index, position):
        if index == 0 or index == 1:
            self._apply_ceiling()
        elif index == 2:
            self._apply_lookahead(position)
        elif index == 3:
            self._shape.set(release_ms=self.macro(3))
        elif index == 4:
            level = (self.TRUE_PEAK_OVERSAMPLED if position >= 0.5 else 0)
            self._shape.set(true_peak=level)
            self._catch.set(true_peak=level)
        else:
            self._shape.set(knee_db=self.macro(5))

    def _apply_ceiling(self):
        """Ceiling and Gain are one setting on the nodes.

        `makeup_db` is applied *after* the gain computer
        (`audioif_dynamics.c:679`), so it cannot be the drive-into-the-ceiling
        knob on its own - it would push the output back through the ceiling.
        Dropping the threshold by the same number of dB compensates exactly:
        below the threshold the output is `L + G`, above it the output is
        `(ceiling - G) + G`, which is the ceiling. That is gain-then-limit,
        with no node to pay for it.
        """
        ceiling_db = self.macro(0)
        gain_db = self.macro(1)
        self._shape.set(threshold_db=ceiling_db - gain_db + _EPSILON_DB,
                        makeup_db=gain_db)
        self._catch.set(threshold_db=ceiling_db + _EPSILON_DB)

    def _apply_lookahead(self, position):
        """Set the delay in whole samples and report exactly that many.

        The node truncates in single precision -
        `lookahead_frames = (uint32_t)(ms * fs / 1000.0f)`,
        `audioif_dynamics.c:126-127` - so asking for the millisecond value
        directly and then computing the sample count in double precision
        disagrees with the node about once in twenty-five at 44.1 kHz.
        Asking for the *midpoint* of the truncation bin instead puts the
        request as far from both edges as it can be, and single-precision
        rounding cannot carry it into a neighbour: measured, 22 disagreements
        become 0 over the same 489 cases.
        """
        rate = self._sample_rate
        samples = int(_component.macro_value(self._MACRO_RANGES[2], position)
                      * rate / 1000.0)
        self._latency = samples
        self._shape.set(lookahead_ms=(0.0 if samples == 0
                                      else (samples + 0.5) * 1000.0 / rate))
