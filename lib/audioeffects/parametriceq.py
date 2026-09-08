"""`ParametricEQ` - the Pultec EQP-1A's two low networks and its resonant
top, with three API 550A proportional-Q bells in the middle.

Rebuilt from scratch for the effects program's Phase 2 against
`workspace docs/effects-internal/dossiers/ParametricEQ.md`. The old `eq.py:ParametricEQ` is not
consulted except for the six defects the dossier's section 7 names.

**What it sounds like.** The bottom is a Pultec: boost and attenuate at once
and you do not get silence, you get the record trick - a lift under 60 Hz
with a scoop just above it, because the two networks sit on different
corners. The top is a Pultec too: the HF boost is a *resonant bell* whose
`Bandwidth` control makes it both narrower and louder as it sharpens - up to
9 dB louder at the same boost setting - while the HF attenuator is a
separate shelf on its own frequency selector. The three bells in between are
an API 550A: turn one up and the skirt stays where it is while the curve
narrows, and its cut is the exact mirror of its boost.

**Portability tier: audioif** (`REQUIRES = ("audiobiquad",)`). Every section
is an `audiobiquad.Biquad` - float state, and a tail that reaches exact
zero. The ported `synthio.Biquad` cannot: a 20 Hz low shelf at +10 dB parks
on 32 LSB of DC and holds it for ever (audioif#23, dossier appendix B), and
this class's own useful settings sit right in that band.

**Headroom, and what it costs the traits.** Every section writes int16 and
clips there (`audioif_filter_f32.c:43-51`), so a boost is delivered whole
only while the signal has room for it. Measured at 1 kHz through the middle
bell at +16 dB, RMS of the rendered tone: **+16.00 dB at -20 dBFS, +13.77 dB
at -12 dBFS, +8.37 dB at -6 dBFS**, while the matching -16 dB cut reads
-15.99 dB at every one of them.

Four of the dossier's five traits are bounded by that, and the evidence pack
carries the level each stops at (its section 1d, twelve stops from -40 to
-6 dBFS):

* **T5**, cut is the exact reciprocal of boost - at G = 16 it holds to
  **-16 dBFS** (0.0005 dB) and misses from -15 (0.3734 dB against a 0.1 dB
  bar); at G = 12 it holds to -12 dBFS and first misses at -10 (0.9960); at
  G = 6 it holds at every level run, down to -6.
* **T3**, bandwidth changes peak gain - holds to **-14 dBFS** (+6.43 dB),
  misses from -13 (+5.58 against a 6-12 dB band).
* **T4**, the bells' proportional-Q bandwidth ratio - holds to **-10 dBFS**
  (3.074x), misses at -6 (2.231x against a floor of 3x).
* **T2**, the resonant top - its first two clauses hold at every level; the
  clause that the cut selector does not move the boost's peak has no reading
  at -6 dBFS, because the bell is gone from the full-cut build.
* **T1**, the Pultec low pair, is the one row with no level bound: its three
  figures move by 0.003 dB from -40 to -6 dBFS.

All of it is the clip, not the filter: the coefficients are reciprocal and
proportional at every level, which is what
`tests/test_cpython_effects_parametriceq.py` reads. Drive this EQ from a
signal with headroom for the boost you dial, or trim into it, and the curves
are the ones the traits describe.

**Cost.** Eight sections, always built, and no patch changes that. Measured
2026-09-07 on both boards at construction defaults - where patch 0 is a wire,
so it is a graph idling: **15.2 % of a 256-frame stereo block on the ESP32-P4
and 25.3 % on the ESP32-S3**, inside the dossier's 26 % and 43 %. At patch 3,
where five sections are live, the desktop digest moves off the bare probe's
(`395946e53d4bca94` against `4169efd90ecf44dd`) and the board figure at that
patch is still owed.

**Latency: zero samples, at every setting and every rate.** Every section is
a recursive biquad reading no sample it has not been given, and no option on
this class adds a lookahead, a partition or a window, so there is no
latency-adding option to default off.

`capabilities = ()`: an equaliser has no tempo-dependent behaviour and this
class never reads `self._transport()`.

The macro units are the panel's own. The EQP-1A's four gain pots and its
bandwidth pot are dials marked 0-10, so that is what macros 1, 2, 9, 11 and
13 read; the API 550A's band gains are switch positions marked in dB, so
macros 4, 6 and 8 read dB. `Low Freq`, `Bell n Freq`, `High Freq` and
`Atten Freq` read hertz.
"""

VENDOR = "PyDevices"

import math

try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None                  # `_require_modules` raises for us

from . import _component


#: A section whose gain is under this is built as a wire: `mix = 0` makes
#: the kernel write `to_s16(x0)`, which is the input sample unchanged
#: (`audioif/src/shared/audioif_filter_f32.c:239`). Two reasons for the
#: number. A quarter of a decibel is inaudible and a section still costs a
#: pass. And a BIPOLAR macro has no exact centre on the 0-127 grid - 64/127
#: puts a +/-16 dB bell at 0.126 dB and a +/-12 dB output at 0.094 dB - so
#: without a floor a "flat" patch would not be a wire.
FLAT_DB = 0.2

#: The proportional-Q law of the dossier's appendix A. Holding a bell's
#: response at a fixed absolute level `L` (the skirt) across boost settings
#: means holding the dimensionless detuning `u` constant, which gives
#:
#:     Q(G) = sqrt( (A^2 - L^2/A^2) / (u0^2 (L^2 - 1)) ),  A = 10^(G/40)
#:
#: with `u0` fixed by one anchor. The skirt is 1 dB and the anchor is
#: Q(12 dB) = 2 - dossier section 8, question 2, settled by measurement: at
#: a 0.1 dB skirt the +1 dB crossing moves 18.0 % across +2/+6/+12 dB and
#: T4's own 5 % bar is missed, at 0.5 dB it moves 11.6 %, and at 1 dB it
#: does not move at all (0.000 %) while the mid-gain bandwidth still falls
#: 3.38x, against T4's floor of 3x.
SKIRT_DB = 1.0
ANCHOR_DB = 12.0
ANCHOR_Q = 2.0

#: Constant Q, the other half of macro 14. One octave, by the octave-to-Q
#: closed form the dossier's appendix A checks against Bohn (S3 section 4.1):
#: `Q = sqrt(2^N)/(2^N - 1)`, which is 1.4142 at N = 1.
CONSTANT_Q = 1.4142135623730951

#: `audiobiquad`'s own clamp (`AUDIOIF_FILTER_F32_MIN_Q`/`MAX_Q`), mirrored
#: because the module does not export it.
MIN_Q = 0.05
MAX_Q = 60.0

#: Both low sections are 0.707 shelves; what separates them is the corner.
#: The cut sits a fixed ratio above the boost, which is the mechanism T1
#: rests on - S9's drawing shows it as two capacitor banks (C12-C17 for cut,
#: C18-C23 for boost) on one ganged selector. 5.0 is the seed's own working
#: point, measured in the dossier's appendix G(i).
SHELF_Q = 0.707
CUT_RATIO = 5.0

#: The make-up amplifier. No node on the palette gives gain above unity -
#: `MixerVoice.level` clamps to 0..1 silently and `audiomath.Multiply` can
#: only attenuate - so the output trim is a high shelf at a subsonic corner.
#: Measured on this node: +12.00 dB from 100 Hz to 10 kHz at 48, 44.1 and
#: 22.05 kHz, and +11.89 dB at 20 Hz.
OUTPUT_CORNER_HZ = 5.0

#: The EQP-1A's HF attenuator selector, from the panel: three positions.
#: S8's drawing carries exactly these three and no others.
ATTEN_STEPS = (5000.0, 10000.0, 20000.0)

#: Full-scale spans behind the panel dials.
LOW_BOOST_MAX_DB = 16.0
LOW_ATTEN_MAX_DB = 20.0
HIGH_BOOST_MAX_DB = 18.0
HIGH_ATTEN_MAX_DB = 20.0

#: Broad and sharp, the two ends of the Bandwidth pot.
BW_Q_BROAD = 0.5
BW_Q_SHARP = 2.5


def _u0_squared():
    """`u0^2` from the anchor, rather than a number copied out of the
    dossier. Q(ANCHOR_DB) comes back as ANCHOR_Q by construction."""
    skirt = 10.0 ** (SKIRT_DB / 10.0)
    anchor = 10.0 ** (ANCHOR_DB / 20.0)
    return ((anchor - skirt / anchor)
            / (ANCHOR_Q * ANCHOR_Q * (skirt - 1.0)))


_U0_SQUARED = _u0_squared()


def proportional_q(gain_db):
    """The bell Q the proportional law gives for `gain_db`.

    Reads the **magnitude** of the gain, never its sign. A law that read the
    signed gain would give a cut a different width from the matching boost
    and break T5's reciprocal at the skirts while the peak still looked
    right - the dossier names that as T5's way of failing.
    """
    magnitude = abs(gain_db)
    if magnitude <= SKIRT_DB:
        # Inside the skirt the law has no root: the bell is not taller than
        # the level it is being held to. Such a section is a wire anyway.
        return MIN_Q
    skirt = 10.0 ** (SKIRT_DB / 10.0)
    squared = 10.0 ** (magnitude / 20.0)
    value = math.sqrt((squared - skirt / squared)
                      / (_U0_SQUARED * (skirt - 1.0)))
    return min(MAX_Q, max(MIN_Q, value))


def _nearest(value, steps):
    """The panel position `value` lands on. A selector, not a sweep."""
    best = steps[0]
    for step in steps:
        if abs(math.log(step / value)) < abs(math.log(best / value)):
            best = step
    return best


class ParametricEQ(_component.Component):
    """Pultec EQP-1A shelves and a resonant top, API 550A proportional-Q
    bells in between. Eight `audiobiquad` sections; audioif tier; zero
    latency."""

    NAME = 'ParametricEQ'
    DISPLAY_NAME = 'Parametric EQ'
    CATEGORIES = ('EQ',)
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    #: Measured, not assumed: the longest burst-to-exact-zero this class
    #: reaches anywhere in its own span - a 20 Hz bell at +16 dB, whose Q the
    #: proportional law puts at 2.58 - at 48 kHz, 785 ms. Lower rates are
    #: shorter in frames (32832 at 44.1 kHz, 18240 at 22.05 kHz), so this is a
    #: ceiling at every rate. Patch 0 is a wire and its tail is zero.
    TAIL_SAMPLES = 37696

    MACRO_LABELS = (
        "Low Freq", "Low Boost", "Low Atten",
        "Bell 1 Freq", "Bell 1 Gain",
        "Bell 2 Freq", "Bell 2 Gain",
        "Bell 3 Freq", "Bell 3 Gain",
        "Bandwidth", "High Freq", "High Boost",
        "Atten Freq", "High Atten", "Q Law", "Output",
    )
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
        3: "UNIPOLAR", 4: "BIPOLAR",
        5: "UNIPOLAR", 6: "BIPOLAR",
        7: "UNIPOLAR", 8: "BIPOLAR",
        9: "UNIPOLAR", 10: "UNIPOLAR", 11: "UNIPOLAR",
        12: "UNIPOLAR", 13: "UNIPOLAR", 14: "TOGGLE", 15: "BIPOLAR",
    }
    _MACRO_RANGES = (
        (20.0, 200.0, "log"),               # 0  Low Freq, Hz
        (0.0, 10.0),                        # 1  Low Boost, panel dial
        (0.0, 10.0),                        # 2  Low Atten, panel dial
        (20.0, 20000.0, "log"),             # 3  Bell 1 Freq, Hz
        (-16.0, 16.0),                      # 4  Bell 1 Gain, dB
        (20.0, 20000.0, "log"),             # 5  Bell 2 Freq, Hz
        (-16.0, 16.0),                      # 6  Bell 2 Gain, dB
        (20.0, 20000.0, "log"),             # 7  Bell 3 Freq, Hz
        (-16.0, 16.0),                      # 8  Bell 3 Gain, dB
        (0.0, 10.0),                        # 9  Bandwidth, 0 broad 10 sharp
        (3000.0, 16000.0, "log"),           # 10 High Freq, Hz
        (0.0, 10.0),                        # 11 High Boost, panel dial
        (5000.0, 20000.0, "log"),           # 12 Atten Freq, Hz (stepped)
        (0.0, 10.0),                        # 13 High Atten, panel dial
        (0.0, 1.0),                         # 14 Q Law, 0 prop / 1 constant
        (-12.0, 12.0),                      # 15 Output, dB
    )
    PATCHES = {
        0: ("Flat",
            (61, 0, 0, 46, 64, 72, 64, 97, 64, 64, 91, 0, 64, 0, 0, 64)),
        1: ("Low Lift And Clear",
            (61, 32, 32, 46, 64, 72, 64, 97, 64, 64, 91, 0, 64, 0, 0, 64)),
        2: ("Air Above Ten",
            (61, 0, 0, 46, 64, 72, 64, 97, 64, 64, 91, 76, 64, 0, 0, 64)),
        3: ("Broad Warm Tilt",
            (61, 51, 0, 46, 64, 72, 64, 97, 64, 0, 91, 38, 64, 38, 0, 64)),
        4: ("Sharp Presence Bell",
            (61, 0, 0, 46, 64, 92, 95, 97, 64, 127, 91, 0, 64, 0, 0, 64)),
        5: ("Rumble Trim And Top Trim",
            (38, 0, 64, 46, 64, 72, 64, 97, 64, 64, 91, 0, 64, 64, 0, 64)),
        6: ("Wide Gentle Smile",
            (61, 38, 0, 46, 64, 68, 48, 97, 64, 25, 91, 51, 64, 0, 0, 64)),
    }

    # -- construction --------------------------------------------------

    def _build(self, low_hz=60.0, low_boost=0.0, low_atten=0.0,
               bell1_hz=250.0, bell1_db=0.0,
               bell2_hz=1000.0, bell2_db=0.0,
               bell3_hz=4000.0, bell3_db=0.0,
               bandwidth=5.0, high_hz=10000.0, high_boost=0.0,
               atten_hz=10000.0, high_atten=0.0,
               q_law=0.0, output_db=0.0, patch=None):
        """Eight sections, in chain order, cutting sections first.

        The two attenuators lead, the three bells sit in the middle and the
        two boosts and the output trim close, because the chain is not
        linear: each section writes int16 and clips there
        (`audioif_filter_f32.c:43-51`), so a boost ahead of a cut spends
        headroom the cut then throws away. The class states the headroom it
        needs rather than hiding it: at full low boost a full-scale source
        clips in section 5, exactly as it would in the make-up amplifier of
        the passive unit.

        Every option is in the units of the macro it seeds, and nothing here
        adds latency.
        """
        rate = self._sample_rate
        channels = self._channel_count

        def section(mode):
            node = audiobiquad.Biquad(mode=mode, frequency=1000.0, Q=SHELF_Q,
                                      gain_db=0.0, mix=0.0,
                                      sample_rate=rate,
                                      channel_count=channels)
            return self._own(node, reset=True, deinit=True)

        self._low_atten = section(audiobiquad.LOW_SHELF)
        self._high_atten = section(audiobiquad.HIGH_SHELF)
        self._bells = [section(audiobiquad.PEAKING_EQ) for _ in range(3)]
        self._low_boost = section(audiobiquad.LOW_SHELF)
        self._high_boost = section(audiobiquad.PEAKING_EQ)
        self._output_trim = section(audiobiquad.HIGH_SHELF)

        upstream = self._source
        for node in self._nodes:
            node.play(upstream)
            upstream = node
        self._output = upstream

        self._init_macros(
            (low_hz, low_boost, low_atten,
             bell1_hz, bell1_db, bell2_hz, bell2_db, bell3_hz, bell3_db,
             bandwidth, high_hz, high_boost, atten_hz, high_atten,
             q_law, output_db), patch)

    # -- the control laws ----------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _set(self, node, hz, q, gain_db):
        """Push one section, and make a flat one a wire rather than a pass
        of arithmetic that must come back byte-identical."""
        if abs(gain_db) < FLAT_DB:
            node.mix = 0.0
            return
        node.frequency = self._hz(hz)
        node.Q = min(MAX_Q, max(MIN_Q, q))
        node.gain_db = gain_db
        node.mix = 1.0

    def _bell_q(self, gain_db):
        if self._macros[14] >= 0.5:
            return CONSTANT_Q
        return proportional_q(gain_db)

    def _refresh_low(self):
        """The two low networks. The boost dial is a square-law taper and
        the attenuator's is linear, which is what makes dial 2.5 on both
        reproduce the reissue's measured `+3 dB bass shelf with a -2 dB
        mid-band cut` (S2) instead of cancelling: +8.0 dB against -5.0 dB.
        Both tapers are ours. What is sourced is that the two pots cannot
        share a law - S9 marks the bass boost 10 k Log against the bass cut
        at 100 k Log - not these two exponents.
        """
        corner = self._value(0)
        boost = LOW_BOOST_MAX_DB * math.sqrt(self._value(1) / 10.0)
        atten = LOW_ATTEN_MAX_DB * (self._value(2) / 10.0)
        self._set(self._low_boost, corner, SHELF_Q, boost)
        self._set(self._low_atten, corner * CUT_RATIO, SHELF_Q, -atten)

    def _refresh_bell(self, which):
        hz = self._value(3 + 2 * which)
        gain = self._value(4 + 2 * which)
        self._set(self._bells[which], hz, self._bell_q(gain), gain)

    def _refresh_high_boost(self):
        """The EQP-1A's resonant top. `Bandwidth` sets this section's Q
        *and* its peak gain: sharp is 0.5 broad's width and, at full boost,
        9 dB louder - the figure S2 measured on the reissue. It reaches this
        section and no other; S8's drawing puts the `HI BOOST Q` 2K2A pot
        inside the resonant network itself, where it cannot touch the bells.
        """
        sharpness = self._value(9) / 10.0
        gain = (HIGH_BOOST_MAX_DB * (self._value(11) / 10.0)
                * (0.5 + 0.5 * sharpness))
        q = BW_Q_BROAD * ((BW_Q_SHARP / BW_Q_BROAD) ** sharpness)
        self._set(self._high_boost, self._value(10), q, gain)

    def _refresh_high_atten(self):
        atten = HIGH_ATTEN_MAX_DB * (self._value(13) / 10.0)
        self._set(self._high_atten, _nearest(self._value(12), ATTEN_STEPS),
                  SHELF_Q, -atten)

    def _refresh_output(self):
        self._set(self._output_trim, OUTPUT_CORNER_HZ, SHELF_Q,
                  self._value(15))

    def _apply_macro(self, index, position):
        if index in (0, 1, 2):
            self._refresh_low()
        elif index in (3, 4):
            self._refresh_bell(0)
        elif index in (5, 6):
            self._refresh_bell(1)
        elif index in (7, 8):
            self._refresh_bell(2)
        elif index == 9:
            self._refresh_high_boost()
        elif index in (10, 11):
            self._refresh_high_boost()
        elif index in (12, 13):
            self._refresh_high_atten()
        elif index == 14:
            for which in range(3):
                self._refresh_bell(which)
        else:
            self._refresh_output()
