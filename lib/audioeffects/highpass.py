"""`HighPass` - the low-cut: a two-pole analog high-pass whose transmission
zero at DC is exact, not nearly.

Rebuilt from scratch for the effects program's Phase 2 against
`workspace docs/effects-internal/dossiers/HighPass.md`. The old `eq.py:HighPass` is not consulted except
for the eight defects the dossier's section 7 names.

**What it sounds like.** One knob decides where the bottom stops, and above
that corner nothing is touched: rumble, handling noise, a subsonic DC offset
and the mud under a vocal go, and the voice does not. The second knob is how
loud the corner itself stands - at Resonance 0.707 it is 3 dB down and the
cut is as gentle as a cut gets, at 2 it is 6 dB up and you can hear where you
put it, at 16 it is 24 dB up and the filter whistles at its own corner. The
Slope switch is a desk's: 12 dB/oct for a low-cut you do not want to notice,
24 dB/oct when the rumble has to actually leave. There is no drive and no
growl anywhere in it - a high-pass is linear.

**Three things the knobs do not do exactly, found by the Phase 2 gate audit
(`docs/effects-phase2-gate-audit.md` section 4.1) and its patch sweep, and
bounded here rather than hidden.**

*The corner gain reads Q down to about 40 Hz, and drifts below that.* Set
Resonance to 8 with the corner at 10 Hz and the steep slope - which is one
knob turn from patch 0's own default corner - and the peak stands
**+17.46 dB where the knob says +18.06**, 0.6 dB shy; at 44.1 kHz with
Resonance 16 it is 2.68 dB shy. The cause is under this class and it is
arithmetic, not a bug in the cut: `audiobiquad` derives its coefficients in
double and stores the five it uses as `float`
(`audioif/src/shared/audioif_filter_f32.h:103`), and a resonant pole pair's
corner gain is set by `1 + a1 + a2`, which at a 10 Hz corner is 1.7e-6 -
smaller than the rounding of `a1 ~ -2` into single precision. Evaluating the
class's own cascade with the coefficients rounded that way predicts every
rendered figure to within 0.005 dB (`workspace docs/effects-internal/probes/phase2_probes/highpass_sweep.py
corner`). **The bound: at f0 with `2*pi*f0/F_s >= 5.2e-3` - 40 Hz at
48 kHz, 18 Hz at 22.05 kHz - the corner reads Q to within 0.05 dB at every Q
and both slopes, measured. Below it the knob is a direction, not a number.**

*And below that same corner it is not quite one curve either.* The shape is
`f0`-independent on the bilinear-warped axis to 0.0125 dB from 31.5 Hz up,
which is what the class is for; at a **10 Hz** corner - patch 0's own - it
is **0.21 dB** off that curve at f0/4, against the same 0.05 dB bar, and the
figure jumps about with tiny changes of Q because the rounding does. One
cause, one bound, three traits: above 40 Hz at 48 kHz the corner gain, the
curve and the rate-honesty all hold; below it the low-cut still cuts and
still removes DC exactly, and the two numbers on the panel stop being exact.
The skirt (12 and 24 dB/oct) and the transmission zero at DC hold at every
setting, including there.

*The corner rings 1.85 times longer at 24 dB/oct than the knob says.* Q is
also a decay time - a released tone at the corner falls to e^-pi of its
level in about Q periods - and it does, at 12 dB/oct. At 24 dB/oct the
resonance rides the steeper Butterworth section alone so that the *gain*
reads the same at both slopes (see `BUTTERWORTH_HIGH` below), and the price
is exactly that ratio: `1.3066 / 0.7071 = 1.848`. Measured 1.91 / 1.86 /
1.85 Q at Resonance 2 / 8 / 16. Musically it is a longer, more obvious
whistle at the same loudness, which is what the steep slope is for.

**The one thing a high-pass does that a low-pass cannot.** The numerator
`(1+cos w0)/2, -(1+cos w0), (1+cos w0)/2` sums to exactly zero at `z = 1`
(RBJ, the dossier's S1), so DC is not attenuated, it is *removed*: a step
settles to exact zero and a held offset decays away. That is the class's
whole musical job, and it is why this class is `audiobiquad` and not
`synthio.Biquad`.

**Portability tier: audioif** (`REQUIRES = ("audiobiquad",)`). Both filter
sections and the trim are `audiobiquad.Biquad` - float state, and a state
word below 1e-20 written as exact zero. The ported `synthio.Biquad` cannot
do the paragraph above: its Q12 integer memory has fixed points, and a
`HighPass` parks on **-71 LSB of DC at a 10 Hz corner, -18 at 20 Hz and -8
at 30 Hz, and holds them for ever** (audioif#23; dossier A3 and A15). A
stock CircuitPython board therefore cannot construct this class. That is the
dossier's section 8 question 1, settled there as D1, and the cost is real:
the old class ran on a stock board and quietly failed the invariant.

**Cost, measured.** Three sections, always built. On the ESP32-P4 this
class costs **5.7 %** of one stereo block's real-time deadline and on the
ESP32-S3 **9.6 %** (2026-09-07, 256-frame stereo blocks at 48 kHz, marginal
over the probe source alone), against dossier budgets of 1.5 % and 5 %:
**over on both**, and it stays parked on that gate item. There is no lean
patch to offer, and the reason is worth knowing before optimising anything
here - `mix` 0 takes a section out of the *sound*, not out of the *work*
(`audioif/src/shared/audioif_filter_f32.c:216-241` computes and stores the
recursion for every sample and only the output line reads `mix`), so patch
0's two wired-out sections cost what live ones cost. What would fit the
budget is a construction option that builds one section instead of three,
at the cost of Slope no longer being a live macro; it is not taken here.
Both boards render this class byte for byte identically.

**Latency: zero samples, at every setting and every rate.** Every section is
a recursive biquad reading no sample it has not been given. No option on
this class adds a lookahead, a partition or a window, so there is no
latency-adding option to default off and none to name in milliseconds.

`capabilities = ()`: nothing in a high-pass is measured in beats - its two
controls are hertz and a dimensionless Q - and this class never reads
`self._transport()`.

**Mix, and what it means at 24 dB/oct.** Mix is the section-level crossfade
`audiobiquad` already has, set on every section in use at once. At 0 every
section writes its input sample back unchanged, so the whole class is a
byte-exact wire. At 1 it is the full cascade, and T1's exact zero at DC is a
statement about *that* setting: between the two the dry path carries DC
through in proportion, because that is what a blend is. At 12 dB/oct the
blend reads exactly as a dry/wet control; at 24 dB/oct it is that blend
applied to each of the two poles in turn, which is a smooth walk from wire
to cascade but is not one half of the fourth-order response. The
alternative - a splitter and a mixer around the pair - costs two more nodes
and would put an int16 sum on the dry path, so it is not taken and this
sentence is here instead.
"""

VENDOR = "PyDevices"

try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None                  # `_require_modules` raises for us

from . import _component


#: The fourth-order Butterworth Q pair, which is the same pair for a
#: high-pass as for a low-pass: the LP-to-HP substitution `s <- 1/s` (S4
#: section 2.10) mirrors the response and leaves the pole Qs alone. At
#: 24 dB/oct the first section holds the lower one fixed and the resonance
#: rides the second alone, so `|H(f0)|` is the product
#: `0.5412 * 1.3066 * Q/0.7071 = Q` - the same reading of the Resonance knob
#: at both slopes. Scaling *both* Qs would square it. Measured, both slopes,
#: Q 0.5 to 16: within 0.002 dB of 20*log10(Q) (dossier A15).
BUTTERWORTH_LOW = 0.5411961001461969
BUTTERWORTH_HIGH = 1.3065629648763766

#: The Q at which the pair above is exactly Butterworth, and the resonance
#: the panel's own "flat" position stands for.
FLAT_Q = 0.7071067811865476

#: `audiobiquad`'s own clamp (`AUDIOIF_FILTER_F32_MIN_Q` / `MAX_Q`),
#: mirrored because the module does not export it. Resonance 16 at
#: 24 dB/oct asks for 29.56, which is inside it.
MIN_Q = 0.05
MAX_Q = 60.0

#: The trim is one high shelf at a subsonic corner, which is a broadband
#: gain everywhere above it: no node on the palette gives gain above unity
#: (`MixerVoice.level` clamps to 0..1, `audiomath.Multiply` only
#: attenuates), and there is no route from Python to a biquad's `b`
#: coefficients, so the shelf is how a high-pass gets its make-up. Measured
#: on this node at 48 000 / 44 100 / 22 050 Hz and -12/-6/+6/+12 dB: flat to
#: 0.0152 dB from 50 Hz to 15 kHz (dossier A15).
#:
#: The corner is 5 Hz and not lower for the same reason it is not higher:
#: it has to sit under the class's own lowest corner (10 Hz) so that the
#: shelf is flat across everything the filter passes, and a shelf's skirt
#: is not infinitely steep.
TRIM_CORNER_HZ = 5.0
TRIM_Q = 0.7071067811865476

#: A trim under this is built as a wire rather than a pass of arithmetic
#: that must come back byte-identical. A BIPOLAR macro has no exact centre
#: on the 0-127 grid - 64/127 puts a +/-12 dB trim at 0.094 dB - so without
#: a floor a patch whose trim reads "0" would not be one.
FLAT_DB = 0.2


class HighPass(_component.Component):
    """A two-pole high-pass with a resonant corner, a 12/24 dB/oct slope
    switch and a make-up trim. Three `audiobiquad` sections; audioif tier;
    zero latency; DC removed exactly rather than nearly."""

    NAME = 'HighPass'
    DISPLAY_NAME = 'High Pass'
    CATEGORIES = ('Filter', 'EQ')
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0

    #: Measured, not assumed - and re-measured after the Phase 2 gate audit
    #: found the first measurement's excitation too weak to be a ceiling
    #: (`docs/effects-phase2-gate-audit.md` section 4.1). The tail of a
    #: high-pass is its resonant pole ringing down, so the longest one comes
    #: from the state that pole is driven to, not from the loudest strike:
    #: a full-scale tone **at** the corner, held until the ring has stopped
    #: climbing, then released. At the worst settings the surface reaches -
    #: 10 Hz, Resonance 16, 24 dB/oct (which puts Q 29.56 on the second
    #: section) and +12 dB of trim - that measures **627 267 samples** at
    #: 48 kHz, against the 303 727 a 200 ms burst produced. Swept over
    #: Frequency x Resonance x Slope x Trim, 54 cells, worst cell at every
    #: span's own stop: `workspace docs/effects-internal/probes/phase2_probes/highpass_sweep.py tail`.
    #: Lower rates are shorter in frames (a tail is a time, and 48 kHz has
    #: the most frames in it: 625 665 / 561 319 / 287 882 at 48 / 44.1 /
    #: 22.05 kHz), so this is a ceiling at every rate. Declared at the next
    #: multiple of 2048 above the measurement plus one period of the 10 Hz
    #: corner (4 800 samples), which is the allowance for where in the cycle
    #: the drive stops.
    TAIL_SAMPLES = 632832

    MACRO_LABELS = ("Frequency", "Resonance", "Slope", "Mix", "Trim")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "TOGGLE",
                   3: "UNIPOLAR", 4: "BIPOLAR"}
    _MACRO_RANGES = (
        (10.0, 20000.0, "log"),         # 0  Frequency, Hz
        (0.5, 16.0, "log"),             # 1  Resonance, Q
        (0.0, 1.0),                     # 2  Slope, 0 = 12 dB/oct, 1 = 24
        (0.0, 1.0),                     # 3  Mix, 0 is a wire
        (-12.0, 12.0),                  # 4  Trim, dB
    )
    #: Named for settings, never for products, and every value is
    #: `macro_of()` of the setting in the comment beside it.
    PATCHES = {
        0: ("Flat", (0, 13, 0, 127, 64)),            # 10 Hz, Q 0.71, 12 dB
        1: ("Rumble Cut", (18, 13, 127, 127, 64)),   # 29.4 Hz, Q 0.71, 24
        2: ("Stage Low-Cut", (35, 13, 0, 127, 64)),  # 81.2 Hz, Q 0.71, 12
        3: ("Thin It Out", (57, 13, 0, 127, 64)),    # 303 Hz, Q 0.71, 12
        4: ("Radio", (71, 40, 127, 127, 48)),        # 701 Hz, Q 1.49, 24,
                                                     # -2.93 dB
        5: ("Whistle", (89, 110, 0, 127, 16)),       # 2057 Hz, Q 10.06,
                                                     # 12 dB, -8.98 dB
    }

    # -- construction --------------------------------------------------

    def _build(self, frequency=10.0, q=FLAT_Q, slope=12, mix=1.0,
               trim_db=0.0, patch=None):
        """Three sections, in chain order: the two filter poles, then the
        trim.

        The trim closes the chain rather than opening it because each
        section writes int16 and clips there
        (`audioif/src/shared/audioif_filter_f32.c:43-51`): a resonant corner
        at Resonance 16 stands 24 dB above the passband, and the trim is
        there to bring that back down, so it has to sit after the peak it is
        trimming. It also has to sit after the poles for T1: a shelf ahead
        of them would put a DC gain of one in front of the transmission
        zero, which is harmless, but a shelf behind them cannot reintroduce
        what the zero removed.

        The second section is built at every setting and left as a wire when
        the slope is 12 dB/oct - a node cannot be added to a running graph,
        and Slope is a live macro.

        `slope` is in dB per octave, 12 or 24; every other option is in the
        units of its macro. Nothing here adds latency.
        """
        rate = self._sample_rate
        channels = self._channel_count

        def section(mode):
            node = audiobiquad.Biquad(mode=mode, frequency=1000.0, Q=FLAT_Q,
                                      gain_db=0.0, mix=0.0,
                                      sample_rate=rate,
                                      channel_count=channels)
            return self._own(node, reset=True, deinit=True)

        self._pole_one = section(audiobiquad.HIGH_PASS)
        self._pole_two = section(audiobiquad.HIGH_PASS)
        self._trim = section(audiobiquad.HIGH_SHELF)

        upstream = self._source
        for node in self._nodes:
            node.play(upstream)
            upstream = node
        self._output = upstream

        self._init_macros(
            (frequency, q, 0.0 if int(slope) <= 12 else 1.0, mix, trim_db),
            patch)

    # -- the control laws ----------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    @property
    def _steep(self):
        return self._macros[2] >= 0.5

    def _refresh(self):
        """Push all five knobs at once.

        One routine rather than five, because every setting here depends on
        at least one other: the section Qs depend on the slope, and every
        section's `mix` depends on Mix and on whether that section is in use
        at this slope and this trim.
        """
        corner = self._hz(self._value(0))
        resonance = self._value(1)
        blend = self._value(3)
        trim_db = self._value(4)
        steep = self._steep

        if steep:
            q_one = BUTTERWORTH_LOW
            q_two = BUTTERWORTH_HIGH * resonance / FLAT_Q
        else:
            q_one = resonance
            q_two = FLAT_Q

        self._pole_one.frequency = corner
        self._pole_one.Q = min(MAX_Q, max(MIN_Q, q_one))
        self._pole_one.mix = blend

        self._pole_two.frequency = corner
        self._pole_two.Q = min(MAX_Q, max(MIN_Q, q_two))
        self._pole_two.mix = blend if steep else 0.0

        self._trim.frequency = self._hz(TRIM_CORNER_HZ)
        self._trim.Q = TRIM_Q
        self._trim.gain_db = trim_db
        # The trim is the filter's make-up, so it goes with the filter: at
        # Mix 0 the class is a wire, trim included, which is what Tier 1's
        # bypass invariant asks of it.
        self._trim.mix = 1.0 if (blend > 0.0 and abs(trim_db) >= FLAT_DB) \
            else 0.0

    def _apply_macro(self, index, position):
        del index, position
        self._refresh()
