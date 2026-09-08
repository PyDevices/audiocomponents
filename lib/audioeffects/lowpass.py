"""`LowPass` - the two-pole analog prototype every synth and console
low-pass is a version of, digitised without losing its tail.

Rebuilt from scratch for the effects program's Phase 2 against
`workspace docs/effects-internal/dossiers/LowPass.md`. The old `eq.py:LowPass` is not consulted except
for the seven defects the dossier's section 7 names.

**What it sounds like.** One knob slides the whole curve along the frequency
axis without changing its shape, and one knob decides how loud the corner
itself stands: at Resonance 0.707 the corner is 3 dB down and the curve is
the gentlest roll-off there is, at 2 it is 6 dB up and the filter starts to
whistle where you put it, at 16 it is 24 dB up and a click at the input rings
for seconds. There is no drive, no saturation and no growl anywhere in it -
a low-pass is linear, and the thing that makes a Moog a Moog belongs to
`LadderFilter`. The Slope switch is a console's: 12 dB/oct is the analog
prototype, 24 dB/oct is a second section behind it for when a rumble has to
actually go away.

**Where those two sentences stop being exact.** The Phase 2 gate audit
(2026-09-07) disconfirmed four of the five traits off the point they were
measured at, and the evidence pack's section 1 carries each with its cause.
In a player's terms:

* **The corner gain is the resonance to 0.05 dB everywhere except the bottom
  of the Frequency knob at the top of the Resonance knob, at 24 dB/oct.** At
  f0 20 Hz, Q 16, 24 dB/oct the corner stands **0.44 dB low** (0.09 dB at
  31.5 Hz, inside the bar by 40 Hz). The cause is float32 coefficients at a
  pole that close to z = 1, not the design; the same reading comes off the
  built sections' own coefficients with no audio in the loop. It is a
  quarter-decibel on a peak 24 dB tall - it does not change what the filter
  is for, and it is written here because a trait that says "exactly" has to
  say where.
* **The shape is one curve at every corner from 31.5 Hz up. Below 25 Hz it
  is not**, by 0.079 dB between 20 and 25 Hz against a 0.05 bar - same
  cause, and it gets worse rather than better on a board where `mp_float_t`
  is single.
* **"Rings for Q periods" is a 12 dB/oct statement, below about a sixth of
  the sample rate.** Above 12 kHz at 48 kHz the ring measured in periods of
  f0 stretches (2.75 periods at Q 2, against a 1.60-2.50 band), because the
  decay is set by the warped pole and f0 is not it. At 24 dB/oct the ring is
  **1.36x the Resonance number at Q 2 rising to 1.71x at Q 16** - measured
  2.74 / 6.54 / 13.49 / 27.42 periods at 500 Hz, 48 kHz - so it is longer
  than the knob says at every Q and the knob is not a period count at that
  slope. (The evidence pack's independent record calls this "a uniform
  1.85x"; its own numbers, which reproduce exactly, do not say that, and the
  correction is in the pack.)
* **Rate-honest to 0.1 dB of the closed form everywhere except that same
  corner**: f0 20 Hz, Q 16, 24 dB/oct reads 0.378 dB out at 48 kHz and
  0.293 dB at 44.1 kHz, and 0.008 dB at 22.05 kHz. The failure is
  rate-dependent because the warp is smallest at a low corner.

The one trait that survived an independent refutation is the roll-off:
**-12.03 dB/oct on the warped axis, unity at DC, at every corner and every
rate** - swept over the whole Frequency travel it is within **0.0104 dB** of
its 0.05 dB bar.

**Portability tier: audioif** (`REQUIRES = ("audiobiquad",)`). Both filter
sections and the trim are `audiobiquad.Biquad` - float state, and a tail
that reaches exact zero. The ported `synthio.Biquad` cannot: a `LowPass` at
100 Hz parks on 1 LSB of DC and a 40 Hz one at Q 8 on 4 LSB, and they hold
it for ever (audioif#23, dossier A3 and A14), which is Tier 1's first
invariant failing at exactly the corners this class is for. That is the
dossier's section 8 question 1, settled here for this class.

**Cost.** Three sections, always built - and *all three run whatever their
`mix` is*: `audioif_filter_f32.c:216-241` has no branch on `mix`, so a
section left as a wire costs what a working section costs. Measured on the
boards 2026-09-07: **5.6 % of one stereo block's real-time deadline on the
ESP32-P4 and 9.6 % on the S3**, against a dossier budget of 1.5 % / 5 %.
**Over budget on both, and there is no `" - lean"` patch**: the class has no
macro that removes a section, and measured across every setting its surface
can reach the desktop cost moves less than the same setting moves between
passes (0.013 ms/block against 0.016-0.022;
`workspace docs/effects-internal/probes/phase2_probes/lowpass_cost.py`). It still runs in real time on both
boards with room to spare - the budget was instruction-count arithmetic that
could not see a node graph's per-block Python, and it is the budget that is
being contested, not the class's fitness for use.

**Latency: zero samples, at every setting and every rate.** Every section is
a recursive biquad reading no sample it has not been given. No option on
this class adds a lookahead, a partition or a window, so there is no
latency-adding option to default off and none to name in milliseconds.

`capabilities = ()`: nothing in a low-pass is measured in beats - its two
controls are hertz and a dimensionless Q - and this class never reads
`self._transport()`.

**Mix, and what it means at 24 dB/oct.** Mix is the section-level crossfade
`audiobiquad` already has, set on every section at once. At 0 every section
writes its input sample back unchanged, so the whole class is a byte-exact
wire (measured: a three-section chain at `mix=0` hashes to the source's own
digest). At 1 it is the full cascade. In between, at 12 dB/oct it is exactly
the dry/wet blend it reads as; at 24 dB/oct it is that blend applied to each
of the two sections in turn, which is a smooth walk from wire to cascade but
is not one half of the fourth-order response. The alternative - a splitter
and a mixer around the pair - costs two more nodes and would put an int16
sum on the dry path, so it is not taken; the honest sentence is here
instead.
"""

VENDOR = "PyDevices"

try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None                  # `_require_modules` raises for us

from . import _component


#: The fourth-order Butterworth Q pair. At 24 dB/oct the first section holds
#: the lower one fixed and the resonance rides the second alone, so that
#: `|H(f0)|` is the product `0.5412 * 1.3066 * Q/0.7071 = Q` - the same
#: reading of the Resonance knob at both slopes. Scaling *both* Qs would
#: square it (Resonance 2 would stand +15 dB up rather than +6) and T1 would
#: hold at one slope and not the other. Measured, both slopes, Q 0.5 to 16:
#: within 0.001 dB of 20*log10(Q) **at f0 1 kHz**. Swept over the whole
#: Frequency travel by the gate audit it holds to 0.011 dB at 12 dB/oct and
#: leaves the bar at 24 dB/oct only at f0 20-31.5 Hz with Q 16 (worst
#: -0.2717 dB, `workspace docs/effects-internal/probes/phase2_probes/lowpass_patch_sweep.py sweep`).
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
#: coefficients, so the shelf is how a low-pass gets its make-up. Measured
#: on this node at 48 000 / 44 100 / 22 050 Hz and -12/-6/+6/+12 dB: flat to
#: 0.010 dB from 50 Hz to 15 kHz, 0.100 dB worst at 20 Hz. A 10 Hz corner
#: reads 0.95 dB out at 20 Hz, which is why the corner is 5.
TRIM_CORNER_HZ = 5.0
TRIM_Q = 0.7071067811865476

#: A trim under this is built as a wire rather than a pass of arithmetic
#: that must come back byte-identical. A BIPOLAR macro has no exact centre
#: on the 0-127 grid - 64/127 puts a +/-12 dB trim at 0.094 dB - so without
#: a floor a patch whose trim reads "0" would not be one.
FLAT_DB = 0.2


class LowPass(_component.Component):
    """A two-pole low-pass with a resonant corner, a 12/24 dB/oct slope
    switch and a make-up trim. Three `audiobiquad` sections; audioif tier;
    zero latency."""

    NAME = 'LowPass'
    DISPLAY_NAME = 'Low Pass'
    CATEGORIES = ('Filter', 'EQ')
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0

    #: Measured, not assumed: the longest burst-to-exact-zero this class
    #: reaches anywhere in its own span - 20 Hz at Resonance 16 and
    #: 24 dB/oct, struck with a full-scale burst - is 203 731 samples after
    #: the source goes silent, at 48 kHz. Lower rates are shorter in frames
    #: (a tail is a time, and 48 kHz has the most frames in it), so this is
    #: a ceiling at every rate. Declared at the next multiple of 2048.
    TAIL_SAMPLES = 204800

    MACRO_LABELS = ("Frequency", "Resonance", "Slope", "Mix", "Trim")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "TOGGLE",
                   3: "UNIPOLAR", 4: "BIPOLAR"}
    _MACRO_RANGES = (
        (20.0, 20000.0, "log"),         # 0  Frequency, Hz
        (0.5, 16.0, "log"),             # 1  Resonance, Q
        (0.0, 1.0),                     # 2  Slope, 0 = 12 dB/oct, 1 = 24
        (0.0, 1.0),                     # 3  Mix, 0 is a wire
        (-12.0, 12.0),                  # 4  Trim, dB
    )
    #: Named for settings, never for products, and every value is
    #: `macro_of()` of the setting in the comment beside it.
    PATCHES = {
        0: ("Open", (127, 13, 0, 127, 64)),        # 20000 Hz, Q 0.71, 12 dB
        1: ("Soft Roll", (105, 13, 0, 127, 64)),   # 6044 Hz, Q 0.71, 12 dB
        2: ("Steep Cut", (92, 13, 127, 127, 64)),  # 2980 Hz, Q 0.71, 24 dB
        3: ("Resonant Peak", (75, 91, 0, 127, 32)),   # 1182 Hz, Q 5.99,
                                                      # 12 dB, -5.95 dB
        4: ("Squelch", (59, 116, 127, 127, 16)),      # 495 Hz, Q 11.85,
                                                      # 24 dB, -8.98 dB
        5: ("Sub Only", (33, 13, 127, 127, 64)),   # 120 Hz, Q 0.71, 24 dB
    }

    # -- construction --------------------------------------------------

    def _build(self, frequency=20000.0, q=FLAT_Q, slope=12, mix=1.0,
               trim_db=0.0, patch=None):
        """Three sections, in chain order: the two filter poles, then the
        trim.

        The trim closes the chain rather than opening it because each
        section writes int16 and clips there
        (`audioif/src/shared/audioif_filter_f32.c:43-51`): a resonant corner
        at Resonance 16 stands 24 dB above the passband, and the trim is
        there to bring that back down, so it has to sit after the peak it is
        trimming.

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

        self._pole_one = section(audiobiquad.LOW_PASS)
        self._pole_two = section(audiobiquad.LOW_PASS)
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
