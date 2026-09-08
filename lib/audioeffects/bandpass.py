"""`BandPass` - the two-pole resonant band-pass, rebuilt on `audiobiquad`.

The middle output of every state-variable filter ever built: a wah pedal, a
telephone, and the mid leg of a multiband crossover are all this one circuit.
Two knobs and no nonlinearity - a **centre frequency** and a **width** - in
RBJ's *constant 0 dB peak gain* form, whose numerator `(alpha, 0, -alpha)`
has zeros at both `z = 1` and `z = -1`. So it is exactly zero at DC and at
Nyquist, and its peak is 0 dB **at every width**: narrowing the band changes
what gets through, never how loud it is. That is the property that makes the
width knob musical rather than a gain staircase.

**Portability tier: audioif** (`REQUIRES = ("audiobiquad",)`), and the reason
is a defect, not a preference. On the ported `synthio.Biquad` the recursion
keeps its output memory in Q12 sample units with no dither and no leak, so it
lands on states that reproduce themselves: `BandPass(80 Hz, q=4)` there holds
-1 LSB of DC for ever after the music stops (audioif#23; the dossier's A3).
`audiobiquad.Biquad` is the float-state answer Phase 1 landed for exactly
that, and on it every setting this class offers settles to bit-exact zero
(the dossier's A14). A stock CircuitPython board does not have the module and
this class says so on construction rather than sounding different there.

**Cost**, in a musician's terms: two float biquad sections and no tables, no
lookahead and no buffers - the cheapest thing in the effects library after a
gain stage. Both sections are always built, so the cost is the same whichever
way `Slope` sits, and it is the same at every patch: 91.2 ns per stereo frame
at patch 0 and 95.5 at patch 1 on the desktop, against 20 833 ns of real time.
**Measured on both boards** 2026-09-07: 3.8 % of one 256-frame stereo block at
48 kHz on the ESP32-P4 and 6.2 % on the ESP32-S3, against the dossier's budget
of P4 <= 4 % and S3 <= 13 %. Inside both. There is no `" - lean"` patch and
none is owed: no reachable setting costs less than patch 0 does.

**Latency: zero, at every rate and every setting.** No option this class
offers adds any - there is nothing here that looks ahead, so no option needs
a millisecond figure in this docstring.

Two things about the surface that the algebra, not the taste, decided:

* **`Mix` rides on both sections.** `mix = 0` is a byte-exact wire in both
  slope settings, which is what Tier 1 asks of it. With `Slope` off the blend
  is the plain linear dry/wet `(1-m)*x + m*H(x)`. With `Slope` on it is that
  mixed section run twice, `((1-m)I + mH)^2 x`, and **not** a linear blend
  between the dry signal and the two-section output: per-section crossfades
  cannot cancel their own cross terms, and no arrangement of this palette's
  nodes gets a linear one without a splitter and a mixer.
* **`Slope` on divides the working Q by 1.5538** - it multiplies by
  `sqrt(sqrt(2) - 1)` - so that two cascaded sections keep the -3 dB width
  the `Width` knob asks for. Without it the cascade's width would be 41 % of
  the number on the panel.

**Five of the dossier's rows are disconfirmed, and they are two different
things.** One belongs to this build and bounds what the class promises; four
belong to RBJ's prototype, which this class tracks to nine thousandths of a
decibel wherever it was checked.

**The build's one - the 0 dB peak is not held at a low centre with a narrow
width.** T1 says the gain at f0 is 0.00 dB +- 0.05 at every width. Measured
2026-09-07 over the whole `Frequency` x `Width` grid at four probe levels, it
holds **at every width for f0 >= 100 Hz, and at every centre for Q <= 2**, and
it does not hold in eleven of fifty-six cells below that - all of them f0
<= 63 Hz with Q >= 4, worst **-0.50 dB at f0 20 Hz with Q 32**, which is the
`Frequency` knob's bottom stop against the `Width` knob's top. Two knob turns
from patch 5 `Sub Window`. What it sounds like: a sub-bass resonance up to
half a decibel quieter than the same knob setting an octave higher, and the
error changes sign with the signal level (+0.09 dB at -3 dBFS, -0.48 at -12,
+0.44 at -20), so it is not a trim anyone can dial out.

The cause is not this class and not the prototype. RBJ's closed form at that
cell is `+0.00000 dB`, and `audiobiquad`'s own five coefficients, read off the
node and run through a `float64` recursion, give `-0.003 dB`. Run through the
kernel's `float32` one they give `-0.480`, which is the class to a ten
thousandth of a decibel. `audioif_filter_f32.c:220-238` is a direct-form I
biquad with float state, and at `w0 = 0.0026 rad` its two feedback
coefficients cancel to seven parts in a million, so the increment single
precision has to carry is 2e-5 of the numbers being differenced. Filed as
audioif#64 with the fix (a transposed direct form II costs nothing at run
time); this class is parked on it as audiocomponents#39. The measurement, the
map and the four-way decomposition are
`workspace docs/effects-internal/probes/phase2_probes/bandpass_lowcorner.py`.

**The prototype's four**, each measured against RBJ's closed form at the
running rate and each tracking it to <= 0.009 dB, so none of them is a defect
of this build - what fails is the tolerance the dossier wrote around a warped
axis:

* **T4's `|H(f0/100)| = -37.0 +- 0.1 dB` clause, above about 2.5 kHz.**
  Measured `-36.994` at f0 500 Hz, `-37.001` at 1 kHz, `-37.037` at 2 kHz,
  then `-37.279` at 4.8 kHz, `-37.837` at 8 kHz and `-41.350` at 16 kHz,
  against a closed form of `-36.991 / -37.001 / -37.038 / -37.281 / -37.837
  / -41.359`.
* **T2's `-3 dB` edges, above about 2 kHz.** At f0 4 kHz - patch 3 `Presence
  Window` sits at 4 072 Hz - the predicted edges read `-3.209 / -3.222` at
  Q 16 and `-3.130 / -3.803` at Q 0.5, against a `-3.0 +- 0.15` bar; the
  closed form reads the same four numbers.
* **T4's low skirt, at Q >= 8.** `+6.435 dB/oct` at f0 500 Hz Q 8 against a
  `+(5.7...6.3)` band - and `+6.435` from the closed form. Patch 4 `Narrow
  Probe` is Q 23.8, so it is a shipped setting, not a corner.
* **T4's high skirt, at Q >= 8.** `-6.586 dB/oct` at f0 500 Hz Q 8 inside the
  clause's own `f0 <= 600 Hz` condition; closed form `-6.585`.

Read together they say one thing: the +-6 dB/oct and -3 dB clauses are Q 0.707
statements below about 2 kHz, and the dossier did not write the conditions
down. The same warp is the defect the trait-critic pass fixed for T4's high
skirt and left standing in the rest.

**One thing to know before automating it.** The biquad's coefficients step
at the block boundary - they are deliberately not interpolated, because
sliding between two high-Q sections can pass through an unstable pair
(`audioif/docs/upstream-diff.md:1953`). So a *hard jump* in `Frequency` or
`Width` - a program change from a high centre to a low one, say - rings the
energy stored at the old centre out through the new filter, and that is
audible as a click: measured 11 964 peak from a 2 637 peak steady state on a
1 421 Hz -> 203 Hz jump, against 9 442 for the same jump on the stock palette,
so it is the shape of the circuit and not of this rebuild. Automate the knob
in steps and it is a sweep; jump it and it is a click.

`capabilities = ()`: nothing in a band-pass is measured in beats, and the
class never reads `self._transport()`.

Dossier: `workspace docs/effects-internal/dossiers/BandPass.md`, traits frozen 2026-09-07.
Evidence:  `workspace docs/effects-internal/evidence/BandPass-evidence.md`.
"""

VENDOR = "PyDevices"

import math

import audiobiquad

from . import _component


class BandPass(_component.Component):
    """A resonant band-pass: 0 dB at the centre at every width above 100 Hz,
    exact zeros at DC and Nyquist, +-6 dB/octave skirts (+-12 with `Slope`
    on). Below 100 Hz at Q >= 4 the peak loses up to half a decibel - the
    kernel's float32 recursion, audioif#64, module docstring."""

    NAME = 'BandPass'
    DISPLAY_NAME = 'Band Pass'
    CATEGORIES = ('Filter',)
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0

    #: The surface's worst case **at the design rate**: Q 32 at 20 Hz with
    #: two sections at 48 kHz, `ceil(6 * Q * F_s / f0)` = 460 800 samples,
    #: 9.6 s. A class constant cannot be a ceiling for a resonator whose ring
    #: time scales with the sample rate, so `tail_samples` below reports the
    #: build instead; this is the design-rate figure a reader of the class
    #: gets, not a bound over every rate.
    TAIL_SAMPLES = 460800

    MACRO_LABELS = ("Frequency", "Width", "Slope", "Mix")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "TOGGLE", 3: "UNIPOLAR"}
    _MACRO_RANGES = ((20.0, 16000.0, "log"), (0.5, 32.0, "log"),
                     (0.0, 1.0), (0.0, 1.0))
    PATCHES = {
        0: ("Wide Mid", (74, 11, 0, 127)),
        1: ("Telephone", (81, 27, 127, 127)),
        2: ("Snare Crack", (44, 42, 0, 127)),
        3: ("Presence Window", (101, 34, 0, 127)),
        4: ("Narrow Probe", (74, 118, 0, 127)),
        5: ("Sub Window", (21, 55, 127, 127)),
    }

    #: What every section is built as, beyond the three things the knobs
    #: move. A class constant with one job: T1 is a claim about *this*
    #: numerator - RBJ's constant 0 dB peak-gain `(alpha, 0, -alpha)` - and a
    #: planted fault that puts a different numerator behind the same surface
    #: has to reach the class's own build to test it. The gate audit's T1
    #: ruling is that the old fault built a bare `audiobiquad.Biquad`
    #: outside the class, so its red never passed through `BandPass` at all.
    _SECTION = {"mode": audiobiquad.BAND_PASS}

    #: `sqrt(sqrt(2) - 1)`. Two cascaded band-passes reach -3 dB where one
    #: reaches -1.505 dB, so the working Q must come down by this factor for
    #: the cascade's width to stay `f0 / Q`. The dossier's A14 measures it:
    #: at 1 kHz, Q 2 the wanted width is 500.0 Hz, `Q * k` gives 497.4 Hz,
    #: and `Q / k` - the seed's wording - gives 206.1 Hz.
    _CASCADE_Q = 0.6435942529055827

    #: Ring time to half an int16 LSB, in time constants of `Q*F_s/(pi*f0)`
    #: samples: 3.53 for one section, about 5.1 for the cascade's double
    #: pole. Rounded up, and used by `tail_samples`.
    _RING_ONE = 4.0
    _RING_TWO = 6.0

    def _build(self, frequency=1000.0, q=0.707, sections=1, mix=1.0,
               patch=None):
        """Build the two sections. `sections` is 1 or 2 and seeds the `Slope`
        toggle; the second section is always built, because a TOGGLE macro
        has to be able to turn it on later, and it is a byte-exact wire while
        it is off."""
        # Hz-valued spans clamp at the running rate rather than refusing
        # (vision section 3, rate-honesty). `_hz` keeps the section off
        # Nyquist; 0.4 * F_s is the dossier's own ceiling, which keeps the
        # bilinear compression out of T4's high skirt.
        self._ceiling = min(16000.0, 0.4 * self._sample_rate)
        self._sections = []
        upstream = self._source
        for _ in range(2):
            node = audiobiquad.Biquad(
                frequency=self._centre(frequency), Q=float(q), mix=0.0,
                sample_rate=self._sample_rate,
                channel_count=self._channel_count, **self._SECTION)
            node.play(upstream)
            self._own(node)
            self._sections.append(node)
            upstream = node
        self._output = self._sections[-1]
        self._init_macros(
            (frequency, q, 1.0 if int(sections) >= 2 else 0.0, mix), patch)

    # -- the knobs ----------------------------------------------------

    def _centre(self, hz):
        return self._hz(min(self._ceiling, float(hz)))

    def _steep(self):
        return self._macros[2] >= 0.5

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _push_frequency(self):
        hz = self._centre(self._value(0))
        for section in self._sections:
            section.frequency = hz

    def _push_q(self):
        q = self._value(1)
        if self._steep():
            q *= self._CASCADE_Q
        for section in self._sections:
            section.Q = q

    def _push_mix(self):
        mix = self._value(3)
        self._sections[0].mix = mix
        self._sections[1].mix = mix if self._steep() else 0.0

    def _apply_macro(self, index, position):
        del position
        if index == 0:
            self._push_frequency()
        elif index == 1:
            self._push_q()
        elif index == 2:
            # The toggle moves two things at once: the second section stops
            # being a wire, and both sections' Q comes down so the width the
            # panel asks for survives the cascade.
            self._push_q()
            self._push_mix()
        else:
            self._push_mix()

    # -- what the build reports ---------------------------------------

    @property
    def centre_hz(self):
        """The centre frequency in force, after the rate's own clamp."""
        self._check_live()
        return self._centre(self._value(0))

    @property
    def bandwidth_hz(self):
        """`Width` as the -3 dB bandwidth it stands for, `f0 / Q`. The knob
        stores Q, because Q is what the node takes and what the dossier's T2
        is stated in; this is the number a panel shows."""
        self._check_live()
        return self.centre_hz / self._value(1)

    @property
    def sections(self):
        """1 or 2 - how many band-pass sections are in the path."""
        self._check_live()
        return 2 if self._steep() else 1

    @property
    def tail_samples(self):
        """The ring time of *this* build, not a class constant.

        A band-pass is a resonator: its tail is `Q * F_s / (pi * f0)` samples
        of time constant, and the output reaches half an int16 LSB after
        about 3.5 of them (5.1 for the cascade's double pole). A host told
        the surface's worst case at every setting would allocate 9.6 s for a
        filter nobody asked for.
        """
        self._check_live()
        ring = self._RING_TWO if self._steep() else self._RING_ONE
        return int(math.ceil(ring * self._value(1) * self._sample_rate
                             / self.centre_hz))
