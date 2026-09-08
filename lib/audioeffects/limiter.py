"""A lookahead brickwall limiter: a ceiling the signal does not get past.

Dossier: `workspace docs/effects-internal/dossiers/Limiter.md`. Evidence:
`workspace docs/effects-internal/evidence/Limiter-evidence.md`.

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

**True Peak costs real time, and it costs lookahead.** The palette prices
each `Dynamics` with `true_peak=2` at the +options row: **1.611 ms / 3.461 ms**
marginal on the P4 / S3. This class lights it on *both* stages, so the
toggle is **3.222 ms / 6.922 ms** (61 % / 130 % of a 5.333 ms block) - the
S3 cannot hold that graph (measured 6.550 ms/block, rt 0.81 at the old Loud
setting). Leave it off unless you have a P4 and need the inter-sample
ceiling. With True Peak off (the default), a worst-phase tone at a quarter
of the sample rate leaves a -6 dBFS ceiling **3.01 dB high** in the
reconstructed waveform at 48000, 44100 and 22050 Hz - the ceiling is held
on the samples and broken between them. With it on, and **any** lookahead
at all, the worst of the 65 committed probes at 48 kHz and 44.1 kHz, at
Lookahead 0.25, 1.5 and 10 ms, is **+0.22 dB** over the ceiling against a
0.50 dB bar, with no probe red. With True Peak on and Lookahead at **0**
it is a sample ceiling and nothing more: a full-scale ramp escapes by
**+2.22 dB TP** and a DC step by +1.12. That is not a bug that can be fixed - the detector
names an inter-sample peak five and a half samples after it happened, so
catching one costs delay. The last twelve samples of the Lookahead macro go
to the catch stage for exactly this, which is why turning True Peak on adds
no latency of its own. Every shipped patch that turns it on also asks for
lookahead, and those patches (*Catch The Peaks*, *Delivery Ceiling*,
*Loud (True Peak)*) are **P4 only**. Turn it on for anything that will be
converted or encoded, and give it a millisecond.

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

from . import _component

try:
    import audiodynamics
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiodynamics = None


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

#: How much of L3's +0.1 dB bar the true-peak reserve may spend, and the
#: arithmetic that spends no more. Once the catch stage has a delay in front
#: of it (`TRUE_PEAK_RESERVE_SAMPLES`), its detector sees a peak `reserve`
#: samples before the audio carrying it arrives, and a one-pole release sags
#: `20/ln(10) x reserve / release` dB in between - measured, 0.344 dB at a
#: 0.25 ms reserve against a 5 ms release, which is over L3's bar. So the
#: catch stage's release is stretched to keep that sag under this figure
#: whenever the reserve is in use, and left at `_CATCH_RELEASE_MS` when it is
#: not. The measured sag comes out at 0.79 of what the formula predicts, so
#: the number below is the conservative side of the node's own law.
_CATCH_SAG_DB = 0.05
_DB_PER_TIME_CONSTANT = 8.685889638065035


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

    **True Peak costs real time.** Each stage it lights is a `Dynamics`
    +options row on the palette (1.611 / 3.461 ms); both stages together
    are 61 % / 130 % of a block and **miss the S3 deadline** (rt 0.81).
    With True Peak off (the default), a worst-phase tone at a quarter of
    the sample rate leaves a -6 dBFS ceiling **3.01 dB high** in the
    reconstructed waveform at 48000, 44100 and 22050 Hz. On, with any
    lookahead at all, the worst of the 65 committed probes at both rates
    is **+0.22 dB** over, and none is red. With True Peak on and
    **Lookahead 0** it is a sample ceiling only - `ramp_fs` escapes by
    **+2.22 dB TP**, `dc_step` by +1.12 - because an inter-sample
    peak cannot be caught with no delay to catch it in. The last twelve
    samples of the Lookahead macro are the catch stage's, so True Peak still
    adds no latency of its own; every shipped patch that turns it on asks
    for lookahead too, and those patches are P4 only.
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
        2: ("Loud", (125, 64, 0, 72, 0, 0)),
        3: ("Soft Ceiling", (116, 0, 0, 78, 0, 95)),
        4: ("Delivery Ceiling", (122, 0, 25, 72, 127, 0)),
        5: ("Loud (True Peak)", (125, 64, 38, 38, 127, 0)),
    }

    #: `DYN_LIMIT` has no knee term in its gain computer at all
    #: (`audioif_dynamics.c:369-370`), so the Knee macro rides a
    #: `DYN_COMPRESS` node instead, at a ratio high enough that Knee 0
    #: measures 0.0000 dB/dB of slope above the threshold - a brickwall by
    #: measurement, not by mode name. It is a class attribute and not a
    #: module constant so that L6's fault of the same kind - a limiting law
    #: with a *finite* ratio - can be planted as a subclass and shown to be
    #: a state no macro and no patch of this class can reach.
    BRICKWALL_RATIO = 1.0e6

    #: The 4x true-peak level. `True` still means the node's older half-band
    #: estimate, which is why this is a number here and not a flag.
    TRUE_PEAK_OVERSAMPLED = 2

    #: The true-peak reserve, in samples, and why it is a sample count and
    #: not a millisecond figure. The node's 4x detector reads a **12-tap**
    #: polyphase window (`AUDIOIF_DYNAMICS_TP_TAPS`,
    #: `audioif_dynamics.h:51`; `oversampled_peak`,
    #: `audioif_dynamics.c:349-357`), so the inter-sample peak it names at
    #: sample *n* happened about five and a half samples earlier. A gain
    #: computed from that number can only be applied to audio at least that
    #: far behind the detector - with no delay in the catch stage the peak
    #: has already left the node, which is why a true-peak ceiling with
    #: **no** lookahead is a sample-peak ceiling however the toggle is set
    #: (measured: +2.22 dB TP on `ramp_fs`, evidence L1). Twelve samples is
    #: one whole window, and it is taken **out of** the Lookahead macro
    #: rather than added to it, so `latency_samples` is still exactly what
    #: the macro asks for. Planting `0` here is L1's fault of the same kind.
    TRUE_PEAK_RESERVE_SAMPLES = 12

    def _build(self, ceiling_db=-1.0, gain_db=0.0, lookahead_ms=0.0,
               release_ms=150.0, true_peak=False, knee_db=0.0, patch=None):
        """`lookahead_ms` is the only latency this class has and it defaults
        to **0 ms**; at its maximum it is 10 ms (480 samples at 48 kHz), and
        `latency_samples` reports it the moment it moves. `true_peak` adds no
        latency. `release_ms` below about 110 ms is a distortion setting on
        low material - see the class docstring."""
        self._latency = 0
        self._true_peak = bool(true_peak)
        self._shape = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            ratio=type(self).BRICKWALL_RATIO, attack_ms=0.0))
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
            self._true_peak = level != 0
            self._shape.set(true_peak=level)
            self._catch.set(true_peak=level)
            # The toggle moves the reserve, so the split has to be redone -
            # a patch applies macro 2 before macro 4, and every shipped patch
            # that turns True Peak on also asks for lookahead.
            self._apply_lookahead(self._macros[2])
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
        """Set the delay in whole samples, split between the two stages, and
        report exactly the total.

        The node truncates in single precision -
        `lookahead_frames = (uint32_t)(ms * fs / 1000.0f)`,
        `audioif_dynamics.c:126-127` - so asking for the millisecond value
        directly and then computing the sample count in double precision
        disagrees with the node about once in twenty-five at 44.1 kHz.
        Asking for the *midpoint* of the truncation bin instead puts the
        request as far from both edges as it can be, and single-precision
        rounding cannot carry it into a neighbour: measured, 22 disagreements
        become 0 over the same 489 cases.

        **The split, and why the catch stage gets the last twelve samples.**
        With True Peak on, the catch stage is the node that has to hold the
        *reconstructed* ceiling, and it cannot do that with nothing in front
        of it: its detector names an inter-sample peak about five and a half
        samples after the fact. So the last `TRUE_PEAK_RESERVE_SAMPLES` of
        whatever the Lookahead macro asks for are moved from the shape stage
        to the catch stage. The two delays sum to the macro's own number, so
        `latency_samples` does not move; measured, this takes `ramp_fs` at
        Lookahead 10 ms from +0.98 dB TP over a -6 dBFS ceiling to +0.16,
        and `dc_step` from +1.08 to +0.09. The catch stage's release is
        stretched with the reserve - see `_CATCH_SAG_DB` - because a delay in
        front of a releasing detector is a peak that arrives after the gain
        has started coming back: at the 5 ms release it costs +0.344 dB of
        L3's +0.100 bar on an impulse, and at the stretched release +0.043.
        """
        rate = self._sample_rate
        samples = int(_component.macro_value(self._MACRO_RANGES[2], position)
                      * rate / 1000.0)
        self._latency = samples
        reserve = (min(samples, type(self).TRUE_PEAK_RESERVE_SAMPLES)
                   if self._true_peak else 0)
        shape = samples - reserve
        self._shape.set(lookahead_ms=(0.0 if shape == 0
                                      else (shape + 0.5) * 1000.0 / rate))
        release_ms = _CATCH_RELEASE_MS
        if reserve:
            reserve_ms = reserve * 1000.0 / rate
            release_ms = max(release_ms, _DB_PER_TIME_CONSTANT * reserve_ms
                             / _CATCH_SAG_DB)
        self._catch.set(lookahead_ms=(0.0 if reserve == 0
                                      else (reserve + 0.5) * 1000.0 / rate),
                        release_ms=release_ms)
