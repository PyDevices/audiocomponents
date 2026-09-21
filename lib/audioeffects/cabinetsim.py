"""`CabinetSim` - a designed guitar-cabinet response, two characters.

Rebuilt from scratch at Phase 4 against
`workspace docs/effects-internal/dossiers/CabinetSim.md`, traits frozen
2026-09-17 at Station A, re-cut 2026-09-17 in the first fix round (T3,
below), disclosures added 2026-09-18 in the second.
The old class in `drive.py` is consulted only for the defects that dossier
§7 names: paying 5.3 ms to convolve a filter, reporting latency 0, a top
that falls forever, a hot low end, one presence bell, and macro ranges
untied to the published curves.

**What it is.** A guitar cabinet is a transfer function: driver, box, and
where the microphone sits. The default is a **synthetic designed cascade**,
not a third-party impulse (Brad, 2026-09-08). Character `4x12 stack` follows
the Vintage 30 on-baffle shape inside a sealed close-miked box; `1x12 combo`
follows a G12M-class driver in an open back - a lower box corner it does not
have, a hotter low mid, and a designed 100-300 Hz cancellation notch. Mix 0
is the Tier 1 wire.

**Portability: audiodsp.** Eight `audiobiquad.Biquad`. Tone at 20-230 Hz is
below the ~300 Hz floor where Q15 `synthio.Biquad` is honest (audiodsp#77),
so this is not stock. The clipper nodes are unused.

**Cost.** Palette sum at patch 0, eight live sections, Mix 1: 0.800 / 1.352 ms
-> **15 % / 26 %** of a 5.333 ms stereo block (dossier §3). No lean patch.
No extra source-pull. The boards measured **17.1 % / 27.7 %** on 2026-09-17:
the palette's `audiobiquad.Biquad` row prices ONE node whose upstream is the
measuring harness, and the eighth node of a serial chain costs more than the
first (0.1138 / 0.1848 ms per section here). That gap is the row, not this
graph - there is no Splitter, no Mixer, no second source and no per-block
Python to find in it.

**Latency: zero samples** at the synthetic default. Constructor `impulse`
defaults off; when a user points the class at an IR they obtained, the
convolver partition is **256 samples / 5.333 ms at 48 kHz**. Named here
because it is the only latency-adding option. Room-scale IRs do not fit
the boards (48000 taps: 18.0 / 31.1 ms). `tail_samples` is **6144 at the synthetic
default** and **6144 + the impulse's own length** when one is loaded: the
class returned the constant whatever `impulse=` held, and an 8 192-tap
impulse measures **8 447** samples of tail while a 48 000-tap room
measures **48 255** - a host that trusted 6 144 truncated the tail it
handed in (audit 3 (p)1, G2). The synthetic figure is
measured burst-to-exact-zero over the whole shipped surface - 1850 samples
at the default, 4421 at shipped patch 1, **5565** at the worst corner
(combo, Low Cut 55, Body +6, a 0 dBFS burst at the bell's own 115 Hz).
The longest ring is the **combo's bell**, not the lowest Low Cut: Low Cut
90 with Body +6 (5493) rings longer than Low Cut 55 with Body 0 (2924).

**Level: this cabinet clips above -13 dBFS, and at the constructor
default above -6 dBFS** - and it has stated no-railed-sample ceilings of
**-14 and -6 dBFS** (`SURFACE_CEILING_DBFS`, `DEFAULT_CEILING_DBFS`). The
-11 and -5 this paragraph used to carry were taken through a
`macro_surface()` that moves **one macro at a time**, so Low Cut 55 with
Body +6 - shipped patch 6's own settings - was never swept: read in
combination, `fix2.analytic_db` at `peak_hz` returns **+13.148 dB** there
against a published +10.91, and the ceiling is -13 dBFS by the pack's own
1 % THD rule and -14 by the first railed sample. The default's own peak is
at **3164 Hz**, a frequency the THD table below never reads. The numbers
were wrong **in the safe direction**, which is what makes them a park: a
user told -11 who plays at -11 clips (audit 3 (p)2 and (p)3). Every one of the eight sections hands the next an
int16 and audiodsp's converter saturates at the rail, and the designed
response is a **boost**: +5.3 dB at the default (its 3.2 kHz break-up
peak) and +10.9 dB at the hottest corner of the surface (combo, Body +6,
118 Hz). There is no output trim and no headroom. Measured at 48 kHz on
exactly periodic windows, THD above 1 %:

* **shipped patch 6** is the worst cell - 150 Hz clips above **-11 dBFS**
  (8.28 % at -9, 27.69 % at -3), 115 Hz above -9;
* **shipped patch 1**, the combo, 115 Hz: **2.01 % at -9 dBFS**, 15.13 %
  at -6, 31.11 % at 0;
* **the constructor default**, 2112 Hz: clips above **-5 dBFS** (4.16 %
  at -3); 150 Hz above -4.

Below that the class is linear and the pack owes no alias row; above it,
one is owed. The non-harmonic floor at 3700 Hz is -90 dB at -20 dBFS and
**-42.0 dB at 0 dBFS** (patch 0, 48 kHz), **-25.7 dB at 0 dBFS** at
22.05 kHz. A 1 kHz guard cannot see any of this, because 1 kHz is the one
frequency the class does not boost.

**Not the same cabinet at 22.05 kHz.** 48 and 44.1 kHz agree within
0.3 dB at every frequency read; 22.05 kHz does not. At the default, re
1 kHz, **5 kHz is +4.34 dB** higher there than at 48 kHz and **7 kHz is
4.37 dB** lower; the worst cell over the seven patches is **4.95 dB**
(patch 3, 8 kHz), and T5a's upper -3 dB point moves **4551 -> 5050 Hz**.
The cause is the bilinear warping of the two top shelves as their corners
approach Nyquist: one design reinterpreted at each rate, not one response.
T2 is not applicable at 22.05 kHz for the same reason.

**The macro surface is the 128 MIDI positions.** `set_macro` snaps a float
position to the nearest integer - see its docstring and
audiocomponents#75.

**Headline traits are the constructor default** - which, since the macro
snap above, *is* patch 0 to the last decibel rather than nearly it. The
four give-ups below join the three above (level, rate, surface); all seven
are in the same words in the pack, the dossier's App. M and N, and the
catalogue row:

* **Every Tier 2 trait is a Mix 1 claim.** Mix is a continuous blend on
  every section at once, so a part-wet cabinet has neither the cliff nor
  the low-end control: **T1 holds down to Mix MIDI 112** and reads 14.6 dB
  at MIDI 96, under its 15 dB bar; **T4 holds down to Mix MIDI 48** and
  reads -8.6 dB at MIDI 32, over its -12. Between those and Mix 0 neither
  is claimed. Mix 0 is the Tier 1 wire.
* **T2 is not claimed above Top 5.6 kHz at every Air, nor above Top
  6.3 kHz at any.** The two shelves separate as Top rises: at the default
  Air the 8-16 kHz fall is 3.8 dB at Top 5.6 kHz, 10.3 at 6.3, **14.0 at
  6.6** and **17.4 at the 7 kHz stop**; at Air -30 it is already 16.2 at
  Top 6.3 kHz. T1 goes with it - **14.6 dB at the 7 kHz stop**, under its
  own bar, which is why T1's span excludes the Top and Air stops. T2 is
  **not applicable at 22.05 kHz**.
* **T3 is not claimed below the default Bite.** At Bite 0 the two break-up
  sections are switched off entirely (`FLAT_DB`), so Bite 0 is not a small
  peak but no peak; shipped patch 2 ships Bite +1 and misses T3's 3 dB bar.
* **T4 is a 40.00 Hz row and the pack read 41.0156 Hz.** The tone snapped
  to the render's own bin grid, which is **1.28 dB** up a six-pole
  rolloff: at an exact 40.00 Hz on a whole-period window the default reads
  **-42.443 / -42.441 / -42.483 dB** at 48 / 44.1 / 22.05 kHz against a
  published -41.16 / -41.96 / -42.01, and shipped patch 6 reads
  **-19.009** against -17.94. The trait stands; the number was the grid's
  (audit 3 (p)5).
* **Three Tier 2 readings go red above the ceiling, and each row takes its
  level span.** T3 at 0 dBFS, T5a's 200 Hz clause at +1.21 dB, and T5b's
  level clause at -6 dBFS with Low Cut 55 and Body +6 - which is shipped
  patch 6's own settings - are all above `SURFACE_CEILING_DBFS`, where
  this class is clipping and no trait is claimed. The seven give-ups named
  none of them (audit 3 (p)4).
* **T5a's 115-230 Hz plateau is disconfirmed** and stays so: the three
  high-pass poles at Low Cut put 115 Hz **4.02 dB** under the low-frequency
  maximum, outside the 3 dB the trait asks for (4.14 at Body -6, 5.12 at
  Body +6). Its 60 Hz clause holds over the whole Body travel and all
  three rates, worst **-20.81 dB** at 22.05 kHz with Body +6; the lower
  -3 dB point lands at **121 Hz**, inside the trait's own 100-130. Its
  **200 Hz-1 kHz clause holds at Body 0 only** - +3.26 dB there, but Body
  -6 is **-1.31** (a rise, not a fall) and Body +6 is **+7.48**, over the
  6 dB the trait allows - and the row is quantified over Body -6 / 0 / +6,
  so that clause is claimed at the headline Body and nowhere else.
* **T5b is a claim about the character**, read at identical macros, not
  about the patch pair.

**Single precision.** Every hertz and decibel the class hands a section is
quantised onto a coarse grid, and every ratio below is an exact binary
fraction, so an ESP32's single-precision Python and a desktop's double
produce the **same float32** (audiocomponents#75). Ungridded, 216 of the
896 reachable macro positions hand the two a different filter. The value
grid alone did not close it - a **float** macro position could still land
where the two precisions straddle a grid tie (`set_macro(3, 76.28125)`
was 2729.0 Hz in double and 2730.0 in single, 2 of 8129 positions on a
1/64-MIDI host grid) - so `set_macro` now snaps the position to the MIDI
integer grid, which is the set the 896-position proof covers.
"""

VENDOR = "PyDevices"

try:
    import audiobiquad
except ImportError:
    audiobiquad = None

from . import _component


MIN_Q = 0.05
MAX_Q = 60.0
HP_Q = 0.7071067811865476

#: Quantisation grids (audiocomponents#75). Steps are integers or negative
#: powers of two; the spread between a single- and a double-precision
#: `macro_value` is at worst 5.7e-4, three orders of magnitude inside the
#: coarsest of them, so both round to the same grid point.
HZ_GRID_LOW = 0.5           # Low Cut, 55-140 Hz
HZ_GRID = 1.0               # Break-up and Top
DB_GRID = 0.015625          # 1/64 dB
MIX_GRID = 0.015625         # 1/64

#: `4x12 stack`: the sealed close-miked bump S3 measures with its -3 dB
#: points at 115 and 232 Hz. Broad, because T5a reads 115 Hz.
STACK_BODY_HZ = 150.0
STACK_BODY_Q = 0.9
STACK_BODY_BIAS = 5.0
#: `1x12 combo`: the G12M's hotter low end (S2 is -2.6 dB at 100 Hz where
#: S1 is -6.4). Lower and narrower, so the character shows at 100 Hz and
#: not at 1 kHz.
COMBO_BODY_HZ = 115.0
COMBO_BODY_Q = 1.5
COMBO_BODY_BIAS = 8.0
#: The open back's cancellation notch, above the combo's bump so the notch
#: has a shoulder on both sides inside 100-300 Hz at every Low Cut.
NOTCH_HZ = 245.0
NOTCH_Q = 3.0
NOTCH_DB = -9.0
#: Break-up. Exact binary fractions: `gridded_hz * ratio` is exact in
#: single and double precision alike.
PEAK_A_RATIO = 0.8125       # 13/16
PEAK_B_RATIO = 1.21875      # 39/32
PEAK_A_Q = 7.0
PEAK_B_Q = 4.8125
#: The cliff: one broad shelf for T2's floor, one steep for T1's fall.
SHELF1_RATIO = 1.3125       # 21/16
SHELF1_Q = 0.5625
SHELF2_RATIO = 1.15625      # 37/32
SHELF2_Q = 3.0
SHELF2_GAIN_FRAC = 0.46875  # 15/32
FLAT_DB = 0.2
#: T3's band, re-cut in the fix round: the two maxima travel with Break-up,
#: which is the macro whose whole job is to move them.
T3_BAND_LO = 0.70
T3_BAND_HI = 1.40

# Patch 0 engineering values (constructor defaults).
CHAR_STACK = 0.0
LOW_CUT_DEFAULT = 90.0
BODY_DEFAULT = 0.0
BREAK_DEFAULT = 2600.0
BITE_DEFAULT = 5.0
TOP_DEFAULT = 5200.0
AIR_DEFAULT = -22.0
MIX_DEFAULT = 1.0


def _grid(value, step):
    """`value` on a `step` grid, identically in single and double precision.

    Rounding half away from zero, on a step coarse enough that the two
    precisions never straddle a tie - proved over every reachable macro
    position by `test_settings_survive_single_precision`.
    """
    if value >= 0.0:
        return int(value / step + 0.5) * step
    return -(int(-value / step + 0.5) * step)


class CabinetSim(_component.Component):
    """A designed 4x12 / 1x12 cabinet. Eight `audiobiquad` sections;
    audiodsp tier; zero latency unless a user impulse is loaded.

    **This cabinet clips above -11 dBFS, and at the constructor default
    above -5 dBFS**: the response is a boost (+10.9 dB at the hottest
    corner, +5.3 dB at the default) on a path where every section hands
    the next an int16. Feed it lower, or expect the rail. **It is not the
    same cabinet at 22.05 kHz** - 5 kHz sits 4.34 dB higher re 1 kHz there
    than at 48 kHz, worst cell 4.95 dB. The macro surface is the 128 MIDI
    positions; a float snaps. Every Tier 2 trait is a Mix 1 claim; T5a's
    115-230 Hz plateau is disconfirmed; T2 is not claimed above Top
    6.3 kHz."""

    NAME = 'CabinetSim'
    DISPLAY_NAME = 'Cabinet Sim'
    CATEGORIES = ('Distortion',)
    VERSION = '0.3.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audiobiquad",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    #: Measured over the whole shipped surface, not at three settings: a
    #: burst then silence, counted to the last non-zero sample. The longest
    #: ring is **not** the lowest Low Cut - it is the combo's own bell, +8
    #: dB of bias plus up to +6 of Body at 115 Hz Q 1.5, which rings longer
    #: than three high-pass poles do. At 48 kHz, a 0 dBFS burst: **5565**
    #: samples at the worst corner (combo, Low Cut 55, Body +6, burst at
    #: the bell's own 115 Hz), 5493 at the default Low Cut with Body +6,
    #: 4421 at shipped patch 1, 2924 at Low Cut 55 with Body 0, and 1850 at
    #: the constructor default. Lower rates are shorter in frames (5079 at
    #: 44.1 kHz, 2557 at 22.05). **6144** is that worst case with 10 %
    #: margin, and the test holds the declaration in both directions.
    TAIL_SAMPLES = 6144

    #: The level above which the class's own resonances reach the rail, at
    #: the **worst combined** macro cell and at the constructor default.
    #: The pack published -11 and -5, taken through a `macro_surface()`
    #: that moves one macro at a time and therefore never swept Low Cut 55
    #: with Body +6 - shipped patch 6's own settings (audit 3 (p)2 and
    #: (p)3). Read in combination: `fix2.analytic_db` at `peak_hz` returns
    #: **+13.148 dB** at combo with Low Cut 55 and Body +6 against a
    #: published +10.91, the ceiling there is **-13 dBFS**, and the
    #: default's own peak is at **3164 Hz** - a frequency the pack's THD
    #: table never read - where the ceiling is **-6 dBFS**.
    #:
    #: The numbers were wrong in the safe direction, which is why they are
    #: a park and not a footnote: a user told -11 who plays at -11 clips.
    #:
    #: **These two are the no-railed-sample levels**, which is what a user
    #: needs; the pack's `clip_ceiling` reads the highest level under 1 %
    #: THD and says -13 and -6 at the same cells, because a handful of
    #: railed samples in 4 096 is not 1 % of THD yet. At the worst
    #: combined cell the first railed sample is at -13 dBFS (153 of 4 096
    #: at 115 Hz) and -14 is clean at 60, 115, 150 and 3164 Hz; the
    #: default is clean at -6 and above, its own peak being at 3164 Hz.
    SURFACE_CEILING_DBFS = -14.0
    DEFAULT_CEILING_DBFS = -6.0

    MACRO_LABELS = (
        "Character", "Low Cut", "Body", "Break-up", "Bite", "Top", "Air",
        "Mix",
    )
    MACRO_MODES = {
        0: "TOGGLE",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (0.0, 1.0),                 # 0 Character: <0.5 stack, >=0.5 combo
        (55.0, 140.0, "log"),       # 1 Low Cut, Hz
        (-6.0, 6.0),                # 2 Body, dB
        (1800.0, 3600.0, "log"),    # 3 Break-up, Hz
        (0.0, 8.0),                 # 4 Bite, dB
        (4500.0, 7000.0, "log"),    # 5 Top, Hz
        (-30.0, -12.0),             # 6 Air, dB
        (0.0, 1.0),                 # 7 Mix
    )
    #: The grid each macro's engineering value is quantised onto, or None
    #: where the value is a toggle read against 0.5.
    _MACRO_GRIDS = (None, HZ_GRID_LOW, DB_GRID, HZ_GRID, DB_GRID, HZ_GRID,
                    DB_GRID, MIX_GRID)
    PATCHES = {
        0: ("Sealed Four By Twelve", (
            0,
            _component.macro_of((55.0, 140.0, "log"), 90.0),
            _component.macro_of((-6.0, 6.0), 0.0),
            _component.macro_of((1800.0, 3600.0, "log"), 2600.0),
            _component.macro_of((0.0, 8.0), 5.0),
            _component.macro_of((4500.0, 7000.0, "log"), 5200.0),
            _component.macro_of((-30.0, -12.0), -22.0),
            127,
        )),
        1: ("Open-Backed Twelve", (
            127,
            _component.macro_of((55.0, 140.0, "log"), 70.0),
            _component.macro_of((-6.0, 6.0), 3.0),
            _component.macro_of((1800.0, 3600.0, "log"), 2900.0),
            _component.macro_of((0.0, 8.0), 5.0),
            _component.macro_of((4500.0, 7000.0, "log"), 5400.0),
            _component.macro_of((-30.0, -12.0), -20.0),
            127,
        )),
        2: ("Off-Axis Close Mic", (
            0,
            _component.macro_of((55.0, 140.0, "log"), 90.0),
            _component.macro_of((-6.0, 6.0), 0.0),
            _component.macro_of((1800.0, 3600.0, "log"), 2600.0),
            _component.macro_of((0.0, 8.0), 1.0),
            _component.macro_of((4500.0, 7000.0, "log"), 4700.0),
            _component.macro_of((-30.0, -12.0), -22.0),
            127,
        )),
        3: ("Cone Centre", (
            0,
            _component.macro_of((55.0, 140.0, "log"), 90.0),
            _component.macro_of((-6.0, 6.0), 0.0),
            _component.macro_of((1800.0, 3600.0, "log"), 2600.0),
            _component.macro_of((0.0, 8.0), 7.0),
            _component.macro_of((4500.0, 7000.0, "log"), 6000.0),
            _component.macro_of((-30.0, -12.0), -22.0),
            127,
        )),
        4: ("Dark Practice Box", (
            0,
            _component.macro_of((55.0, 140.0, "log"), 120.0),
            _component.macro_of((-6.0, 6.0), 0.0),
            _component.macro_of((1800.0, 3600.0, "log"), 2600.0),
            _component.macro_of((0.0, 8.0), 5.0),
            _component.macro_of((4500.0, 7000.0, "log"), 4500.0),
            _component.macro_of((-30.0, -12.0), -30.0),
            127,
        )),
        5: ("Bright Small Box", (
            0,
            _component.macro_of((55.0, 140.0, "log"), 140.0),
            _component.macro_of((-6.0, 6.0), 0.0),
            _component.macro_of((1800.0, 3600.0, "log"), 2600.0),
            _component.macro_of((0.0, 8.0), 6.0),
            _component.macro_of((4500.0, 7000.0, "log"), 5200.0),
            _component.macro_of((-30.0, -12.0), -12.0),
            127,
        )),
        6: ("Bass-Heavy Room", (
            0,
            _component.macro_of((55.0, 140.0, "log"), 55.0),
            _component.macro_of((-6.0, 6.0), 6.0),
            _component.macro_of((1800.0, 3600.0, "log"), 2600.0),
            _component.macro_of((0.0, 8.0), 5.0),
            _component.macro_of((4500.0, 7000.0, "log"), 5200.0),
            _component.macro_of((-30.0, -12.0), -22.0),
            127,
        )),
    }

    def _build(self, character=CHAR_STACK, low_cut=LOW_CUT_DEFAULT,
               body=BODY_DEFAULT, break_up=BREAK_DEFAULT,
               bite=BITE_DEFAULT, top=TOP_DEFAULT, air=AIR_DEFAULT,
               mix=MIX_DEFAULT, impulse=None, patch=None):
        """Eight sections, or one convolver when `impulse` is set.

        Nothing on the sixteen-macro surface adds latency. `impulse` is a
        user IR (int16 frames); default None is the synthetic cascade.
        """
        self._impulse = impulse
        self._convolver = None
        # How many frames the user impulse holds, so `tail_samples` can
        # say what a host has to keep pulling for.
        self._impulse_frames = 0 if impulse is None else len(impulse)
        rate = self._sample_rate
        channels = self._channel_count

        if impulse is not None:
            try:
                import audioconvolve
            except ImportError:
                raise ImportError(
                    "CabinetSim(impulse=...) needs audioconvolve, which a "
                    "stock CircuitPython board does not have")
            node = audioconvolve.Convolver(
                impulse=impulse, impulse_channels=1,
                sample_rate=rate, channel_count=channels,
                mix=1.0)
            self._own(node)
            node.play(self._source)
            self._convolver = node
            self._output = node
            self._hp_a = self._hp_b = self._hp_or_notch = None
            self._body = self._peak_a = self._peak_b = None
            self._shelf_a = self._shelf_b = None
        else:
            def section(mode):
                node = audiobiquad.Biquad(
                    mode=mode, frequency=1000.0, Q=HP_Q, gain_db=0.0,
                    mix=0.0, sample_rate=rate, channel_count=channels)
                return self._own(node)

            self._hp_a = section(audiobiquad.HIGH_PASS)
            self._hp_b = section(audiobiquad.HIGH_PASS)
            self._hp_or_notch = section(audiobiquad.HIGH_PASS)
            self._body = section(audiobiquad.PEAKING_EQ)
            self._peak_a = section(audiobiquad.PEAKING_EQ)
            self._peak_b = section(audiobiquad.PEAKING_EQ)
            self._shelf_a = section(audiobiquad.HIGH_SHELF)
            self._shelf_b = section(audiobiquad.HIGH_SHELF)

            upstream = self._source
            for node in self._nodes:
                node.play(upstream)
                upstream = node
            self._output = upstream

        self._init_macros(
            (character, low_cut, body, break_up, bite, top, air, mix),
            patch)

    def _value(self, index):
        """A macro's engineering value, on its grid (audiocomponents#75).

        The **position** is snapped to the 0-127 MIDI grid first. Gridding
        the value alone is not enough: a host that sends a float position
        can land where the double and the single computation straddle a
        grid tie, and `set_macro(3, 76.28125)` was 2729.0 Hz in double and
        2730.0 in single - two different renders. The 128 positions per
        macro are the set the class proves, so they are the set it plays.
        """
        position = int(self._macros[index] * 127.0 + 0.5) / 127.0
        raw = _component.macro_value(self._MACRO_RANGES[index], position)
        step = self._MACRO_GRIDS[index]
        if step is None:
            return raw
        return _grid(raw, step)

    @property
    def _combo(self):
        return self._macros[0] >= 0.5

    def _push(self, node, mode, hz, q, gain_db, mix):
        if node is None:
            return
        if mix <= 0.0:
            node.mix = 0.0
            return
        shaped = mode in (audiobiquad.PEAKING_EQ, audiobiquad.LOW_SHELF,
                          audiobiquad.HIGH_SHELF, audiobiquad.NOTCH)
        if shaped and abs(gain_db) < FLAT_DB:
            node.mix = 0.0
            return
        node.mode = mode
        node.frequency = self._hz(hz)
        node.Q = min(MAX_Q, max(MIN_Q, q))
        node.gain_db = gain_db
        node.mix = mix

    def _refresh(self):
        blend = self._value(7)
        if self._convolver is not None:
            if blend <= 0.0:
                self._output = self._source
            else:
                self._convolver.set(mix=blend)
                self._output = self._convolver
            return

        if blend <= 0.0:
            for node in self._nodes:
                node.mix = 0.0
            return

        combo = self._combo
        low_cut = self._value(1)
        body_db = self._value(2)
        breakup = self._value(3)
        bite = self._value(4)
        top = self._value(5)
        air = self._value(6)

        self._push(self._hp_a, audiobiquad.HIGH_PASS, low_cut, HP_Q, 0.0,
                   blend)
        self._push(self._hp_b, audiobiquad.HIGH_PASS, low_cut, HP_Q, 0.0,
                   blend)
        if combo:
            self._push(self._hp_or_notch, audiobiquad.PEAKING_EQ, NOTCH_HZ,
                       NOTCH_Q, NOTCH_DB, blend)
            self._push(self._body, audiobiquad.PEAKING_EQ, COMBO_BODY_HZ,
                       COMBO_BODY_Q, body_db + COMBO_BODY_BIAS, blend)
        else:
            self._push(self._hp_or_notch, audiobiquad.HIGH_PASS, low_cut,
                       HP_Q, 0.0, blend)
            self._push(self._body, audiobiquad.PEAKING_EQ, STACK_BODY_HZ,
                       STACK_BODY_Q, body_db + STACK_BODY_BIAS, blend)
        self._push(self._peak_a, audiobiquad.PEAKING_EQ,
                   breakup * PEAK_A_RATIO, PEAK_A_Q, bite, blend)
        self._push(self._peak_b, audiobiquad.PEAKING_EQ,
                   breakup * PEAK_B_RATIO, PEAK_B_Q, bite, blend)
        self._push(self._shelf_a, audiobiquad.HIGH_SHELF,
                   top * SHELF1_RATIO, SHELF1_Q, air, blend)
        self._push(self._shelf_b, audiobiquad.HIGH_SHELF,
                   top * SHELF2_RATIO, SHELF2_Q, air * SHELF2_GAIN_FRAC,
                   blend)

    def set_macro(self, index, value, channel=0, note_id=-1,
                  sample_position=0):
        """Set macro `index` from the 0-127 MIDI scale.

        **This surface is the 128 integer positions**, and a float snaps to
        the nearest before anything else happens. The base class accepts
        floats "so a host with finer resolution need not quantize"; on this
        class a finer position is not safe to honour, because only those
        128 per macro are proved to hand a board's single precision and a
        desktop's double the same filter (audiocomponents#75). The snap is
        done here, on the MIDI number the host passed, where `+ 0.5` is
        exact in both precisions - snapping later, from the stored 0..1
        position, would put the tie back at every half-step.
        `get_macro` reads back the snapped number, not the one sent.
        """
        try:
            value = float(value)
        except (TypeError, ValueError):
            pass
        else:
            value = float(int(value + 0.5)) if value >= 0.0 else 0.0
        return _component.Component.set_macro(self, index, value,
                                              channel=channel,
                                              note_id=note_id,
                                              sample_position=sample_position)

    def _apply_macro(self, index, position):
        del index, position
        self._refresh()

    @property
    def latency_samples(self):
        self._check_live()
        if self._convolver is None or self._value(7) <= 0.0:
            return 0
        return int(self._convolver.latency)

    @property
    def tail_samples(self):
        """The synthetic sections' ring, **or the user impulse's length**.

        `TAIL_SAMPLES` is the eight-section number and the class returned
        it whatever `impulse=` held: an 8 192-tap impulse measures **8 447**
        samples of tail and a 48 000-tap room measures **48 255**, and a
        host that trusts 6 144 truncates the tail it was handed (audit 3
        (p)1, G2). The convolver's own ring is the impulse plus what the
        sections behind it add, so the declaration is the impulse's length
        plus the synthetic figure - which is what those two measurements
        say, to 255 and 255 samples.
        """
        self._check_live()
        declared = type(self).TAIL_SAMPLES
        if self._convolver is None or self._value(7) <= 0.0:
            return declared
        taps = getattr(self, "_impulse_frames", 0)
        return declared + int(taps)
