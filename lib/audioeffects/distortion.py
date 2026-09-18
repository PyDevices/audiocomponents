"""ProCo Rat distortion, with the Boss DS-1 as a second character.

Dossier: `workspace docs/effects-internal/dossiers/Distortion.md`. Evidence:
`workspace docs/effects-internal/evidence/Distortion-evidence.md`.

**What it is.** A hard clip to ground after a gain stage, not a diode pair
in the feedback loop (that is `Overdrive`). Character `filter` is the Rat:
two feedback legs that brighten into the clipper, the op-amp's own bandwidth
folding that rise into a mid hump at high Distortion, then a first-order
Filter that runs backwards (clockwise darker). Character `scoop` is the
DS-1: a 35 dB booster, a second gain stage, the same kind of clipper under
a 7.2 kHz cap, and a passive V-shaped tone. Mix 0 is the wire; Distortion
0 is not -- the Rat is nearly clean there (F4) and the DS-1 never is (SC3).
The DS-1's booster is in the circuit, not on the panel, so `scoop` starts
with Boost at 35 dB; the Rat has no booster and starts at 0.

**Portability tier: audioif** (`REQUIRES = ("audioshaper", "audiobiquad",
"audioroute")`). The clipper is `audioshaper.Waveshaper` with a table
derived from the 1N4148 pair (tools/curves/distortion_curve.py). Tone and
the Rat's legs are `audiobiquad` so a 60 Hz pole still decays to exact
zero; `synthio.Biquad` / `audiofilters.Filter` would not (audioif#77).
`scoop` also carries the DS-1's **output coupling capacitor** at 20 Hz.
It is no longer load-bearing: **Asymmetry is a second table now, not a
bias.** `STOCK_ASYMMETRY * macro` was a 3.5 V offset into diodes that clip
at 0.62 V, which parked the operating point at 0.97 of full scale and
answered a silent input with up to **-6.8 dBFS of DC**; the capacitor held
that back to the biquad's dead band and left the *step* - 0.45 of full
scale, 86 ms, every time the input went from silence to a note (audit 3
(p)4). The DS-1's asymmetric clipping section is one 1N4148 one way and
two in series the other, so Asymmetry blends `_CURVE_DS1_DIODE` into
`_CURVE_DS1_ASYM` and **both answer zero with zero**: silence in is
silence out at every shipped patch, the tail settles inside its
declaration, and a click reads its own latency on all eleven patches
where four of them used to be unmeasurable. It costs 1.8 to 2.3 dB of
level at the four scoop patches, because the asymmetric table's full
scale stands for the *quieter* side's 1.220 V against the pair's 0.622.

**Each character's table is a normalised shape, not volts.** Both fill Q15
to the rails, and `_CURVE_RAT_DIODE_VOLTS` / `_CURVE_DS1_DIODE_VOLTS` are
what their full scale stands for; `_push` multiplies the live one into the
shaper's `post_gain` beside Ceiling. Level and curve are exactly what they
were, and the tables keep all the resolution they have - they used to
reach 66 % and 62 % of int16 (audiocomponents#77).

**Cost, reference patch 0 (filter, Mix 1, Distortion mid, 48 kHz).**
MidSide + Splitter x2 (2-tap) + Biquad x4 + Mixer x2 + Waveshaper x4. The
Rat's gain stage is 1 + a*HP(60 Hz) + b*HP(1539 Hz), normalised by its own
treble gain so the two mixer levels sum to 1; the +1 is voice 0's dry
side, through `Biquad.mix`, and costs no node. Priced sum 1.849 / 3.323 ms
+ glue 0.0 -> **P4 <= 35 %, S3 <= 63 %**, re-derived 2026-09-17 from a
graph three nodes smaller than the 2.245 / 4.128 (43 % / 78 %) one the
board ran. At 22.05 kHz the same graph runs the shaper at x8 and the block
is 11.61 ms, so it is 2.868 / 5.126 ms -> **25 % / 45 %**: fewer node
sums per second than 48 kHz, not more. Constructor `oversample=2` is
26 % / 47 %; it is not a patch.

**Latency.** `latency_samples` is **2 at Mix 1 and 0 at every Mix below
it**. The x4 half-band is the only pure delay in the graph, and 2 is the
click's integer onset at full wet - the same at 48, 44.1 and 22.05 kHz, in
mono and in stereo, on both characters (x1 reports 0, x2 1, x8 2). But the
dry leg is not delayed, so as soon as any dry is in the mix the class's
own onset is the dry one: a click at Mix 126 arrives at sample 0, and
reporting 2 there was true of one point on the axis and wrong at the other
126. The sub-sample click reads 15.2 / 14.3 / 8.7 samples at the three
rates on `filter` and 4.0 / 4.0 / 3.7 on `scoop`; that is the
minimum-phase group delay of the biquads, which `effect_measurements.
click` says is a property of the class and not the latency this reports.
Oversampling is not a macro; it is the construction default, named here
because it is the latency-adding option and it is on. `oversample=1` is 0
samples of half-band delay and misses A1 by 25 dB.

**What the default surrenders.** Patch 0 is Distortion 64, Filter 64, Mix
127, silicon Ceiling.

* F1's 11-18 dB 100 Hz->1 kHz tilt is a *low Distortion* claim, read at
  Distortion 2 % and 10 % with under 0.30 V on the clipper. At the shipped
  Distortion 64 the tilt is **+1.1 dB**, because F2's mid hump is already
  on. The tilt also moves with level - -12.2 dB at Distortion 10 % with
  0.21 V of pre-clip drive, -7.0 dB at 0.53 V - and the row's own 0.30 V
  line is what bounds it.
* F2 is read by Appendix G's equal-drive contour at maximum Distortion:
  the peak is at 800 Hz and 10 kHz is 15.5 dB below it at 48 kHz, 14.2 at
  44.1 kHz. At **22.05 kHz the row cannot be read at all** - 10 kHz is
  above this class's Nyquist margin.
* F5's 5 kHz clause is **false at 22.05 kHz**. The default 1 kHz->5 kHz
  fall is -11.7 dB at 48 and 44.1 kHz and **-13.7 dB** at 22.05 kHz, and
  the closed Filter reads -23.2 dB at 5 kHz against the dossier's
  -20.48 +/-1.5, because `_fo_lp` parks its second pole at
  min(40 kHz, 0.45*rate) and that is 9.9 kHz at 22.05 kHz. The 1 kHz and
  2 kHz clauses hold at all three rates.
* **Volume and Mix stop moving the output above a knee, and the class
  says where it is.** `wet_ceiling()` returns the largest wet level the
  headroom split can deliver at the Ceiling and Asymmetry in force: at the
  shipped Ceiling MIDI 42 it is **1.0 - the whole travel works** - and at
  Ceiling MIDI 108 it is **0.6317, which is Volume MIDI 80**, above which
  84, 96, 112 and 127 all read -6.622 dBFS. That is 43 positions and
  3.6 dB of label travel delivering 0.00 dB at shipped patch 3, and it was
  undisclosed until the third fix round (audit 3 ruling (o)).
  `TestDistortionVolumeAndMixTravel` walks both knobs end to end at three
  Ceilings and holds the class to its own knee.
* **The Filter macro works over its whole travel on `scoop` now.** It read
  the Rat's series resistance and then took `max(fc, CLIP_LP_HZ)`, which
  pinned MIDI 8 to 127 on one section - 120 positions that did nothing -
  and made MIDI 1 to 6 *brighter* than MIDI 0. `FILTER_R0_SCOOP` puts the
  pot's own top on the DS-1's 7230 Hz corner instead, so Filter 0 is the
  stock pedal byte for byte and 10 kHz falls monotonically from +1.26 dB
  to -16.59 dB across the travel.
* **Ceiling stops raising the level before its travel ends.** It is
  output gain, and the clipper's output is held at or below 0.74 of full
  scale (`CLIPPER_CEILING`), so the knob goes quiet at about **MIDI 53 at
  Volume maximum** and **MIDI 78 at the shipped Volume 100**. The top of
  the travel is 2.5 dB below where the saturating build sat and 18 dB
  cleaner, because past that the node clipped its own output at the base
  rate and the alias floor fell to -44 dB.
* **A1 is a -20 dBFS number, and the row says so now.** The bar is
  **-60 dB at 1010 Hz over -22 to -16 dBFS**, graded at both ends and the
  middle: -62.43 / -63.33 / -60.56 at -22, -62.44 / -60.55 / -60.66 at
  -19, -68.37 / -66.97 / -65.06 at -16, at 48 / 44.1 / 22.05 kHz. Outside
  that window it does not hold: **-55.7 / -52.3 / -52.5 at -12 dBFS**, and
  at playing level **-46.5 / -44.7 / -45.0 at -6 dBFS** and -43.8 at -0.9
  (audit 3 ruling (m)). Below the window the reading stops being the
  class's - the pack's instrument reads -58.6 at -24 dBFS and the suite's
  -63.1 at the same cell, which is the int16 floor of a quiet render and
  not a number either of them should be graded on. It is a claim about
  1010 Hz too: at **7010 Hz** the same default reads -42.2 / -34.3 /
  -30.1 at -20 dBFS. **And "it is not aliasing" is a x4 sentence**: the
  ladder at -20 dBFS, 48 kHz is x1 -36.14, x2 -56.44, x4 -61.66, x8
  -62.63, so what the shipped factor buys is 25 dB and what it leaves is
  the quantisation the redefinition names. It holds at the shipped default
  in that window and stays under -50 dB
  anywhere on `filter` with Boost at the 0 the Rat ships with. Raise
  Boost, or switch to `scoop`, whose DS-1 booster is 35 dB in circuit, and
  the floor follows the boost: **-40.4 dB at patch 6** and -39.0 dB at the
  worst scoop cell measured (patch 6 at Ceiling 96, 44.1 kHz) - both about
  3 and 15 dB better than the bias model read, because the asymmetric
  table does not park the clipper against its own rail. Redefined under
  vision 7.2 on 2026-09-17; the dossier's revision carries the old target
  and the measurements that replaced it.
* Scoop traits are not the shipped character.
"""

VENDOR = "PyDevices"

from array import array
import math

from . import _component

try:
    import audioshaper
except ImportError:
    audioshaper = None

try:
    import audiobiquad
except ImportError:
    audiobiquad = None

try:
    import audioroute
except ImportError:
    audioroute = None

import audiocore
import audiomixer

try:
    from audioif_util import float32 as _f32
except ImportError:                                  # pragma: no cover
    def _f32(value):
        return value


# BEGIN CURVE RAT_DIODE
#: Volts at this table's full scale. The table is normalised to
#: its own extreme so it fills int16 (audiocomponents#77) and the
#: class carries the scale back out in `post_gain`.
_CURVE_RAT_DIODE_VOLTS = 0.659737631
_CURVE_RAT_DIODE = bytes.fromhex(
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '01800180018001800180018001800180018001800180018001800a801a802b80'
    '3c804d805e806f8081809280a480b680c880da80ec80fe801081238136814881'
    '5b816e8182819581a981bc81d081e481f8810d82218236824b82608275828a82'
    'a082b682cc82e282f8820f8325833c8354836b8382839a83b283cb83e383fc83'
    '15842e84488462847c849684b184cb84e78402851e853a85568573859085ae85'
    'cb85e98508862786468665868586a686c786e8860a872c874e8772879587b987'
    'de87038829884f8876889d88c588ee88178942896c899889c489f1891f8a4d8a'
    '7d8aad8adf8a118b448b798bae8be58b1c8c558c8f8ccb8c088d468d868dc88d'
    '0b8e508e968edf8e2a8f778fc68f18906c90c3901d917a91da913e92a5921193'
    '8193f6936f94ef947495009693962e97d1977e983699fa99ca9aaa9b9a9c9d9d'
    'b69ee79f34a1a1a232a4eca5d4a7efa940acc9ae8bb183b4abb7fbba6dbef8c1'
    '96c542c9f8ccb5d076d43ad801dcc9df91e35be725ebf0eebaf285f650fa1bfe'
    'e501b0057b09460d1011db14a5186f1c3720ff23c6278a2b4b2f0833be366a3a'
    '083e9341054555487d4b754e3751c05311562c58145ace5b5f5dcc5e19604a61'
    '63626663566436650666ca6682672f68d2686d69006a8c6a116b916b0a6c7f6c'
    'ef6c5b6dc26d266e866ee36e3d6f946fe86f3a708970d67021716a71b071f571'
    '38727a72ba72f87235737173ab73e4731b7452748774bc74ef74217553758375'
    'b375e1750f763c7668769476be76e97612773b7763778a77b177d777fd772278'
    '47786b788e78b278d478f678187939795a797b799b79ba79d979f879177a357a'
    '527a707a8d7aaa7ac67ae27afe7a197b357b4f7b6a7b847b9e7bb87bd27beb7b'
    '047c1d7c357c4e7c667c7e7c957cac7cc47cdb7cf17c087d1e7d347d4a7d607d'
    '767d8b7da07db57dca7ddf7df37d087e1c7e307e447e577e6b7e7e7e927ea57e'
    'b87eca7edd7ef07e027f147f267f387f4a7f5c7f6e7f7f7f917fa27fb37fc47f'
    'd57fe67ff67fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
)
# END CURVE RAT_DIODE
# BEGIN CURVE DS1_DIODE
#: Volts at this table's full scale. The table is normalised to
#: its own extreme so it fills int16 (audiocomponents#77) and the
#: class carries the scale back out in `post_gain`.
_CURVE_DS1_DIODE_VOLTS = 0.621544239
_CURVE_DS1_DIODE = bytes.fromhex(
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '01800180018001800180018001800180018001800180018001800a801c802d80'
    '3f8051806380758087809980ac80be80d180e480f7800a811d81308144815881'
    '6b817f819481a881bc81d181e681fa81108225823a82508266827c829282a882'
    'bf82d582ec8203831b8332834a8362837a839283ab83c483dd83f6830f842984'
    '43845e8478849384ae84c984e58401851d853a85578574859185af85cd85ec85'
    '0b862a86498669868a86aa86cc86ed860f873287548778879b87c087e4870a88'
    '308856887d88a488cc88f5881e89488973899e89ca89f689248a528a818ab18a'
    'e18a138b458b798bad8be28b198c508c898cc38cfe8c3b8d788db88df88d3b8e'
    '7e8ec48e0b8f548fa08fed8f3c908e90e29039919291ee914e92b19217938193'
    'ef936194d8945495d5955c96ea967e971b98bf986d99259ae89ab89b959c839d'
    '829e969fc0a004a266a3e9a494a669a870aaacac23afd5b1c3b4eab744bbc9be'
    '72c235c60ccaf2cde2d1dad5d6d9d6ddd8e1dbe5e0e9e5edeaf1f0f5f7f9fdfd'
    '03020906100a160e1b122016251a281e2a222a26262a1e2e0e32f435cb398e3d'
    '3741bc4416483d4b2b4edd505453905597576c59175b9a5cfc5d405f6a607e61'
    '7d626b6348641865db6593664167e56782681669a4692b6aac6a286b9f6b116c'
    '7f6ce96c4f6db26d126e6e6ec76e1e6f726fc46f13706070ac70f5703c718271'
    'c571087248728872c57202733d737773b073e7731e7453748774bb74ed741f75'
    '4f757f75ae75dc750a76367662768d76b876e2760b7734775c778377aa77d077'
    'f6771c78407865788878ac78ce78f17813793479567976799779b779d679f579'
    '147a337a517a6f7a8c7aa97ac67ae37aff7a1b7b377b527b6d7b887ba27bbd7b'
    'd77bf17b0a7c237c3c7c557c6e7c867c9e7cb67cce7ce57cfd7c147d2b7d417d'
    '587d6e7d847d9a7db07dc67ddb7df07d067e1a7e2f7e447e587e6c7e817e957e'
    'a87ebc7ed07ee37ef67e097f1c7f2f7f427f547f677f797f8b7f9d7faf7fc17f'
    'd37fe47ff67fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
    'ff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7fff7f'
)
# END CURVE DS1_DIODE
# BEGIN CURVE DS1_ASYM
#: Volts at this table's full scale. The table is normalised to
#: its own extreme so it fills int16 (audiocomponents#77) and the
#: class carries the scale back out in `post_gain`.
_CURVE_DS1_ASYM_VOLTS = 1.220114412
_CURVE_DS1_ASYM = bytes.fromhex(
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '0180018001800180018001800180018001800180018001800180018001800180'
    '01800180018001800180018001800180018001800180018001800c8022803880'
    '4f8065807c809380aa80c180d880f0800881208138815181698182819b81b581'
    'ce81e88102821c82378252826d828882a482c082dc82f882158332834f836d83'
    '8b83a983c883e78306842684468466848784a884c984eb840e85308554857785'
    '9b85c085e5850b86318657867e86a686ce86f78620874a877487a087cb87f887'
    '258853888288b188e188128944897789aa89df89148a4b8a828abb8af58a2f8b'
    '6b8ba88be78b278c688caa8cef8c348d7b8dc48d0f8e5c8eaa8efb8e4d8fa28f'
    'fa8f5390b0900f917191d5913e92a99218938b9302947d94fc9481950a969996'
    '2e97c9976b981399c4997c9a3d9b079cda9cb99da29e979f99a0a7a1c4a2eea3'
    '28a570a6c8a72fa9a6aa2cacc0ad62af11b1ccb292b462b63bb81cba03bcf1bd'
    'e4bfdbc1d6c3d3c5d4c7d7c9dbcbe1cde8cff0d1fad303d60ed819da24dc2fde'
    '3be047e254e460e66ce879ea86ec92ee9ff0acf2b9f4c6f6d3f8e0faedfcfafe'
    '0601130320052d073909460b520d5d0f6811711379157e1780197c1b711d5c1f'
    '38210423b9245426d2273229732a962b9e2c8e2d672e2c2fe12f86301e31aa31'
    '2c32a53216338033e33341349934ed343d358835d035153657369636d3360d37'
    '45377b37af37e137123841386f389b38c638ef3818393f3965398b39af39d239'
    'f539173a383a583a773a963ab43ad23aef3a0b3b273b423b5d3b773b903baa3b'
    'c23bdb3bf33b0a3c213c383c4e3c643c7a3c8f3ca43cb93cce3ce23cf53c093d'
    '1c3d2f3d423d543d673d793d8a3d9c3dad3dbe3dcf3de03df03d013e113e213e'
    '303e403e4f3e5e3e6d3e7c3e8b3e9a3ea83eb63ec43ed23ee03eee3efb3e093f'
    '163f233f303f3d3f4a3f563f633f6f3f7c3f883f943fa03fac3fb73fc33fcf3f'
    'da3fe53ff13ffc3f074012401d40284032403d40484052405d40674071407b40'
    '85408f409940a340ad40b740c040ca40d440dd40e640f040f94002410b411441'
    '1d4126412f413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
    '3441344134413441344134413441344134413441344134413441344134413441'
)
# END CURVE DS1_ASYM
V_SCALE = 10.0
GBW_HZ = 320000.0
R_GAIN = 100000.0
R_BODY_STOCK = 47.0
R_BODY_RUETZ = 10000.0
R_LEG_BASS = 560.0
FILTER_R0 = 1500.0
FILTER_POT = 100000.0
FILTER_C = 3.3e-9
#: The series resistance that puts the Filter pot's own top exactly on the
#: DS-1's post-clip corner. On `scoop` the class used to read the Rat's
#: `FILTER_R0` and then take `max(fc, CLIP_LP_HZ)`, which pinned **MIDI 8
#: to 127 on one section** - 120 positions that did nothing - and made MIDI
#: 1 to 6 *brighter* than MIDI 0, +5.68 dB at MIDI 1 (audit 3 (p)3). With
#: this the corner starts at `CLIP_LP_HZ` at MIDI 0 and falls monotonically
#: to 452 Hz at MIDI 127, so Filter 0 is byte-for-byte the stock DS-1 and
#: every position above it moves.
FILTER_R0_SCOOP = 1.0 / (2.0 * math.pi * 7230.0 * FILTER_C)
BOOSTER_HZ = 600.0
TONE_LP_HZ = 234.0
TONE_HP_HZ = 1063.0
CLIP_LP_HZ = 7230.0
OPAMP_HP_HZ = 72.0
#: The DS-1's output coupling capacitor, which the first build left out.
#: `Waveshaper.bias` is Asymmetry, and a biased table has a non-zero output
#: at zero input: the shipped scoop patches put **-6.8 to -25.1 dBFS of DC**
#: on the output with a silent source (patch 8 +0.456 of full scale), which
#: is headroom gone and a thump on engage. 0.047 uF into the 100 k volume
#: pot is about 34 Hz; 20 Hz is the quieter end of that and costs 0.17 dB at
#: 100 Hz, where SC1 and SC5 are read.
OUT_HP_HZ = 20.0
PARK_HZ = 40000.0
PARK_LO_HZ = 5.0

#: The measured integer-onset click delay per oversampling factor, which
#: is what `latency_samples` reports at full wet. `audioshaper.
#: GROUP_DELAY_SAMPLES` is the half-band's group delay (0 / 2.2 / 3.3 /
#: 3.9); the onset of a symmetric response arrives before its centroid, so
#: these are the numbers a click actually reads.
CLICK_DELAY_SAMPLES = {1: 0, 2: 1, 4: 2, 8: 2}

#: The internal rate the clipper wants. Below it the decimator's fold is
#: what A1 reads instead of the class; above it nothing improves and the
#: node costs twice. 48 kHz and 44.1 kHz reach it at x4; 22.05 kHz does not,
#: and x8 there buys 5.1 dB at 1010 Hz and 11.1 dB at 3700 Hz for less of
#: the block than x4 costs at 48 kHz, because the block is twice as long.
OVERSAMPLE_FLOOR_HZ = 176400.0


def shipped_oversample(sample_rate):
    """The factor this rate ships with: x4 at 48 and 44.1 kHz, x8 at 22.05.

    Never below x4 - x2 misses A1 at every rate - and never above x8,
    because the node stops there and because above `OVERSAMPLE_FLOOR_HZ`
    the floor is no longer the fold. At 48 kHz x8 moves maximum-Distortion
    1010 Hz from -58.51 to -58.93 dB and 3700 Hz from -48.11 to -48.12 for
    +0.784 / +1.408 ms, which is why it is not taken there.
    """
    factor = 4
    while factor < 8 and float(sample_rate) * factor < OVERSAMPLE_FLOOR_HZ:
        factor *= 2
    return factor

DIST, FILT, TONE, VOL, MIX, CHAR, CEIL, BOOST, ASYM, BODY = range(10)


def _fo_lp(frequency, rate):
    """Parked-pole first-order low-pass as an RBJ section (dossier App. C)."""
    park = min(PARK_HZ, 0.45 * rate)
    corner = max(float(frequency), 1.0)
    f0 = math.sqrt(corner * park)
    q = f0 / (corner + park)
    return f0, q


def _fo_hp(frequency, rate):
    """Parked-pole first-order high-pass: `_fo_lp` read the other way up.

    The second pole parks *below* the band at `PARK_LO_HZ` instead of above
    it, so the section falls 6 dB/oct from `frequency` down and the park is
    a fixed literal rather than a fraction of the rate. Unlike `_fo_lp`,
    this one is the same section at 22.05 kHz as at 48 kHz.
    """
    corner = max(float(frequency), 1.0)
    f0 = math.sqrt(corner * PARK_LO_HZ)
    q = f0 / (corner + PARK_LO_HZ)
    return f0, q


class Distortion(_component.Component):
    """Hard clipping after a shaped gain stage. `audioif` tier.

    Character `filter` (default) follows the ProCo Rat; `scoop` follows the
    Boss DS-1. Mix 0 is the wire. Distortion 0 is clean only in `filter`.
    """

    NAME = 'Distortion'
    DISPLAY_NAME = 'Distortion'
    CATEGORIES = ('Drive',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioshaper", "audiobiquad", "audioroute")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 2
    TAIL_SAMPLES = 48000

    MACRO_LABELS = (
        "Distortion", "Filter", "Tone", "Volume", "Mix",
        "Character", "Ceiling", "Boost", "Asymmetry", "Body",
    )
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "BIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "TOGGLE",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
        8: "UNIPOLAR",
        9: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (0.0, 1.0),
        (0.0, 1.0),
        (-1.0, 1.0),
        (0.0, 1.0),
        (0.0, 1.0),
        (0.0, 1.0),
        (0.5, 2.0),
        (0.0, 35.0),
        (0.0, 1.0),
        (0.0, 1.0),
    )
    PATCHES = {
        0: ("Filter Half Mid Gain", (64, 64, 64, 100, 127, 0, 42, 0, 0, 0)),
        1: ("Filter Open Low Gain", (24, 0, 64, 110, 127, 0, 42, 0, 0, 0)),
        2: ("Filter Closed Full Gain", (127, 127, 64, 84, 127, 0, 42, 0, 0, 0)),
        3: ("High Ceiling Full Gain", (127, 48, 64, 72, 127, 0, 108, 0, 0, 0)),
        4: ("Low Ceiling Mid Gain", (64, 56, 64, 110, 127, 0, 24, 0, 0, 0)),
        5: ("Flat Legs Mid Gain", (72, 40, 64, 100, 127, 0, 42, 0, 0, 127)),
        6: ("Scoop Centre Full Boost", (100, 0, 64, 100, 127, 127, 42, 127, 96, 0)),
        7: ("Scoop Bright Mid Gain", (64, 0, 112, 100, 127, 127, 42, 127, 96, 0)),
        8: ("Scoop Bass Low Gain", (24, 0, 16, 110, 127, 127, 42, 127, 96, 0)),
        9: ("Scoop Low Boost Even", (80, 0, 64, 100, 127, 127, 42, 62, 127, 0)),
        10: ("Clean Edge", (0, 0, 64, 127, 127, 0, 42, 0, 0, 0)),
    }

    OVERSAMPLE = 4
    #: **Removed at the third fix round.** Asymmetry used to be
    #: `Waveshaper.bias`, `STOCK_ASYMMETRY * macro`, which is a **3.5 V
    #: offset** into a table whose diodes clip at 0.62 V: it parked the
    #: operating point at 0.97 of full scale, so a silent input came out at
    #: -6.8 dBFS of DC, the coupling capacitor had to hold that, and the
    #: step from silence to a note was 0.45 of full scale and took 86 ms to
    #: bleed (audit 3 (p)4 and ruling (n)). The DS-1's asymmetric clipping
    #: section is one diode one way and two in series the other - the
    #: *thresholds* differ, not the operating point - so Asymmetry now
    #: blends `_CURVE_DS1_DIODE` into `_CURVE_DS1_ASYM`, both of which
    #: answer a silent input with exactly zero.
    ASYM_BLEND_STEPS = 256

    #: The largest share of full scale the clipper's output may be asked
    #: for. Above it `audioshaper.Waveshaper` saturates its own output on
    #: the decimator's ring - see `_headroom`, and the knee measured on the
    #: bare node: clean to 0.74, -47.9 dB at 0.80, -34.0 dB at 1.00.
    CLIPPER_CEILING = 0.74

    def _build(self, distortion=0.5, filt=0.5, tone=0.0, volume=100.0 / 127.0,
               mix=1.0, character=0.0, ceiling=None, boost=None, asymmetry=0.0,
               body=0.0, patch=None, oversample=None):
        # The DS-1's 35 dB booster is in the circuit, not on the panel, so
        # `scoop` starts with it up: `create(character=1.0)` is a DS-1 and
        # not a DS-1 with its first stage missing. Every shipped scoop patch
        # already has Boost at or near maximum. `filter` (the Rat) has no
        # booster at all and starts at 0.
        if boost is None:
            boost = 35.0 if character >= 0.5 else 0.0
        if ceiling is None:
            ceiling = 1.0
        if oversample is None:
            self._oversample = (shipped_oversample(self._sample_rate)
                                if self.OVERSAMPLE == 4 else self.OVERSAMPLE)
        else:
            self._oversample = int(oversample)
        if self._oversample not in (1, 2, 4, 8):
            raise ValueError("oversample must be 1, 2, 4 or 8")
        # The half-band is the only pure delay in the graph: every other
        # node is minimum phase, so what those add is group delay, which
        # `effect_measurements.click` says in as many words is "a real
        # property of the class and *not* the processing latency
        # latency_samples declares". So the click row reads the integer
        # onset, and CLICK_DELAY_SAMPLES is what that reading is - measured,
        # not derived, and the same at 48 kHz, 44.1 kHz and 22.05 kHz, in
        # mono and in stereo, on both characters.
        self._wet_latency = CLICK_DELAY_SAMPLES[self._oversample]
        self._latency = self._wet_latency
        self._scoop = False
        self._rat_curve = array("h", _CURVE_RAT_DIODE)
        self._ds1_curve = array("h", _CURVE_DS1_DIODE)
        self._ds1_asym = array("h", _CURVE_DS1_ASYM)
        # The table the shaper actually reads on `scoop`: the two DS-1
        # tables blended at Asymmetry. It is written in place, never
        # reallocated, and only when the macro moves.
        self._blend = array("h", bytes(2 * len(self._ds1_curve)))
        self._blend_at = None
        n = 256 * self._channel_count
        self._silence = self._own(
            audiocore.RawSample(
                array("h", bytes(2 * n)),
                sample_rate=self._sample_rate,
                channel_count=self._channel_count),
            reset=False)
        self._wiring = []
        self._install_graph(character >= 0.5)
        self._init_macros(
            (distortion, filt, tone, volume, mix, character, ceiling, boost,
             asymmetry, body),
            patch)
        self._connect()

    @property
    def latency_samples(self):
        self._check_live()
        return self._latency

    def _pcm_mixer(self, voices):
        # `Mixer._render_size` is `buffer_size // 2 // 4 * 4` BYTES, so the
        # stock 1024 renders 128 stereo frames and every mixer in the chain
        # is pulled twice per 256-frame block - the palette's block, and the
        # unit every audioif node works in. 1024 * channel_count makes one
        # pull one block at either channel count.
        return dict(
            voice_count=voices,
            buffer_size=1024 * self._channel_count,
            channel_count=self._channel_count,
            bits_per_sample=16,
            samples_signed=True,
            sample_rate=self._sample_rate)

    def _lp(self, frequency):
        f0, q = _fo_lp(self._hz(frequency), self._sample_rate)
        node = audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=f0, Q=q, mix=1.0,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count)
        return self._own(node)

    def _hp(self, frequency):
        f0, q = _fo_hp(self._hz(frequency), self._sample_rate)
        node = audiobiquad.Biquad(
            mode=audiobiquad.HIGH_PASS, frequency=f0, Q=q, mix=1.0,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count)
        return self._own(node)

    def _wire(self, voice, source):
        """Remember what a mixer voice will play. Nothing is attached until
        `_connect`, because `Mixer.play` pulls a chunk there and then: a
        voice wired before the macros are pushed hands the first block of
        real audio through a mixer whose levels are still the construction
        zeros, and the class loses its first block. That is what made the
        old click reading depend on where in the render the click sat -
        5.3 samples inside the first block, 15.0 after it."""
        self._wiring.append((voice, source))

    def _connect(self):
        """Open every level gate at the pushed levels, then wire the graph."""
        self._charge_output_cap()
        for mixer in self._mixers:
            _component.open_level_gates(
                mixer, list(mixer.voice), self._silence)
        for voice, source in self._wiring:
            voice.play(source)

    def _charge_output_cap(self):
        """Settle `_out_hp` on the bias before the first block is asked for.

        A biased table answers silence with a constant, so the coupling
        capacitor starts with the whole offset across it and passes a step
        the size of the offset - at shipped patch 8, **0.456 of full
        scale**, decaying over about 30 ms. A pedal does that when its
        battery goes in. This class does not have to: the shaper is pointed
        at its own silence buffer and the chain downstream of it is pulled
        until the pole has settled, which happens before anything reads the
        Splitter, so no tap is starved and the real source is not touched.
        """
        if self._out_hp is None or not self._macros:
            return
        # Ten time constants of the pole, in whole blocks. The silence
        # buffer is one block long, so it is re-played each time round.
        blocks = int(10.0 * self._sample_rate
                     / (2.0 * math.pi * OUT_HP_HZ * 256.0)) + 1
        for _ in range(blocks):
            self._shaper.play(self._silence)
            if not audiocore.get_buffer(self._out_hp)[1]:
                break
        self._shaper.play(self._booster)

    def _mixer_node(self, voices=2):
        node = self._own(
            audiomixer.Mixer(**self._pcm_mixer(voices)), reset=False)
        self._mixers.append(node)
        return node

    def _install_graph(self, scoop):
        self._scoop = bool(scoop)
        self._wiring = []
        self._mixers = []
        adapter = self._own(audioroute.MidSide(
            width=1.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count), reset=False)
        adapter.play(self._source)
        mix_split = self._own(
            audioroute.Splitter(adapter, taps=2), reset=False)
        self._dry_tap = self._own(mix_split.tap(0), reset=False)
        wet_in = self._own(mix_split.tap(1), reset=False)

        if not scoop:
            legs = self._own(audioroute.Splitter(wet_in, taps=2), reset=False)
            # 1 + a*HP(60) + b*HP(1539), normalised by the DC-to-treble gain
            # so the mixer levels sum to exactly 1 and nothing clips on the
            # way to the clipper. The follower's unity path is voice 0's own
            # dry side: `Biquad.mix` crossfades it against the high-pass, so
            # the +1 costs no node (see `_push_filter`).
            self._leg_bass = self._hp(60.0)
            self._leg_treble = self._hp(1539.0)
            self._leg_bass.play(legs.tap(0))
            self._leg_treble.play(legs.tap(1))
            self._leg_mix = self._mixer_node(2)
            self._leg_mix.voice[0].level = 1.0
            self._leg_mix.voice[1].level = 0.0
            self._wire(self._leg_mix.voice[0], self._leg_bass)
            self._wire(self._leg_mix.voice[1], self._leg_treble)
            self._gain = self._leg_mix
            self._gbw = self._lp(1000.0)
            self._gbw.play(self._gain)
            shaper_src = self._gbw
            curve = self._rat_curve
            self._curve_volts = _CURVE_RAT_DIODE_VOLTS
            self._clip_lp = None
            self._booster = None
        else:
            self._booster = self._hp(BOOSTER_HZ)
            self._booster.play(wet_in)
            shaper_src = self._booster
            self._blend_at = None
            self._curve_volts = self._blend_curve(0.0)[0]
            curve = self._blend
            self._gain = None
            self._gbw = None
            self._leg_mix = None
            self._leg_bass = None
            self._leg_treble = None
        if not scoop:
            self._out_hp = None

        self._shaper = self._own(audioshaper.Waveshaper(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            curve=curve,
            oversample=self._oversample,
            pre_gain=1.0,
            post_gain=1.0,
            mix=1.0,
            bias=0.0))
        self._shaper.play(shaper_src)

        # A Mixer must never be the source of another Mixer's voice.
        # `MixerVoice.play` calls `reset_buffer` on what it is handed, and a
        # Mixer's reset rewinds every one of ITS voices and re-pulls them -
        # a second chunk through the Splitter that the dry tap never takes,
        # so the wet branch runs 256 frames ahead of the dry for the whole
        # render. That is why the DS-1 tone stack is summed in the output
        # mixer's own voices instead of in a stage of its own: the scoop
        # graph is three voices, the Rat's two.
        if scoop:
            self._clip_lp = self._lp(CLIP_LP_HZ)
            self._clip_lp.play(self._shaper)
            # The output coupling capacitor. Asymmetry is the shaper's
            # `bias`, and a biased table answers a silent input with a
            # constant, so without this the four shipped scoop patches sit
            # at -6.8 to -25.1 dBFS of DC. `filter` never biases the table
            # and does not carry the node.
            self._out_hp = self._hp(OUT_HP_HZ)
            self._out_hp.play(self._clip_lp)
            tone_split = self._own(
                audioroute.Splitter(self._out_hp, taps=2), reset=False)
            self._tone_lp = self._lp(TONE_LP_HZ)
            self._tone_hp = self._hp(TONE_HP_HZ)
            self._tone_lp.play(tone_split.tap(0))
            self._tone_hp.play(tone_split.tap(1))
            self._filt = None
            self._mixer = self._mixer_node(3)
            self._tone_lo = self._mixer.voice[0]
            self._tone_hi = self._mixer.voice[1]
            self._wet = self._tone_lo
            self._dry = self._mixer.voice[2]
            self._wire(self._tone_lo, self._tone_lp)
            self._wire(self._tone_hi, self._tone_hp)
        else:
            self._filt = self._lp(32152.0)
            self._filt.play(self._shaper)
            self._tone_lp = None
            self._tone_hp = None
            self._mixer = self._mixer_node(2)
            self._tone_lo = None
            self._tone_hi = None
            self._wet = self._mixer.voice[0]
            self._dry = self._mixer.voice[1]
            self._wire(self._wet, self._filt)
        self._wire(self._dry, self._dry_tap)
        self._output = self._mixer

    def _apply_macro(self, index, position):
        if index == CHAR:
            scoop = position >= 0.5
            if scoop != self._scoop:
                self._rebuild(scoop)
            self._push()
            return
        self._push()

    def _rebuild(self, scoop):
        for node in reversed(self._nodes):
            release = getattr(node, "deinit", None)
            if release is not None:
                release()
        self._nodes = []
        self._resets = []
        self._deinits = []
        n = 256 * self._channel_count
        self._silence = self._own(
            audiocore.RawSample(
                array("h", bytes(2 * n)),
                sample_rate=self._sample_rate,
                channel_count=self._channel_count),
            reset=False)
        self._install_graph(scoop)
        self._push()
        if self._constructing:
            # `_build` connects once itself, after `_init_macros` has
            # returned. Connecting here as well would prime the graph
            # twice, and `_connect` primes by playing each mixer voice -
            # which pulls a block of the borrowed source and then throws
            # it away when `_build` primes the same voices again. A
            # constructor `patch=` that crosses the Character boundary
            # (the four scoop patches, 6 to 9) lost the first 5.3 ms of
            # the material exactly that way: a click at frame 1024 came
            # out at 774 rather than 1028 (audiocomponents#82).
            return
        self._connect()

    def _push(self):
        if not self._macros:
            return
        mix = self.macro(MIX)
        volume = self.macro(VOL)
        if mix <= 0.0:
            self._latency = 0
            self._output = self._source
            return
        # The dry leg is not delayed and the wet leg is, so the class's own
        # onset is the DRY one at every Mix that lets any dry through: a
        # click at Mix 64 arrives at sample 0, not at sample 2. Reporting
        # the wet leg's 2 there was true of one point on the axis and false
        # of the other 126.
        self._latency = self._wet_latency if mix >= 1.0 else 0
        self._output = self._mixer
        self._dry.level = 1.0 - mix
        ceiling = self.macro(CEIL)
        if self._scoop:
            # Asymmetry is a table now, not a bias, so the volts its full
            # scale stands for move with it and the headroom split has to
            # see the blended figure.
            self._curve_volts, changed = self._blend_curve(self.macro(ASYM))
            if changed:
                self._shaper.set(curve=self._blend)
        # The tables hold a normalised shape rather than volts
        # (audiocomponents#77), so the character's own full-scale voltage
        # is the second term. It is a constant per character, so Ceiling
        # still scales exactly what it scaled.
        post, level = self._headroom(_f32(ceiling * self._curve_volts),
                                     _f32(mix * volume))
        self._shaper.set(post_gain=_f32(post))
        if self._scoop:
            self._push_scoop(level)
        else:
            self._wet.level = level
            self._push_filter()

    def wet_ceiling(self):
        """The largest wet level this class can deliver at the Ceiling and
        Asymmetry in force, 0-1 - and therefore where `Volume` and `Mix`
        stop moving the output.

        `Ceiling` scales the diode drop and the clipper's own output is
        held at or below `CLIPPER_CEILING` of full scale, so above this
        point the split in `_headroom` has nowhere left to put the level:
        `post_gain` is already at the ceiling and a mixer voice cannot go
        past 1.0. **Volume and Mix are live below it and inoperative above
        it** - `Volume` MIDI 84 to 127 is one number at shipped patch 3,
        which is 43 positions and 3.6 dB of label travel delivering 0.00 dB
        (audit 3 (p)2, ruling (o)).

        At the shipped Ceiling (MIDI 42) and Asymmetry 0 this is **1.0** -
        the whole travel works - and it falls as either knob rises: the
        knee is what `test_volume_is_monotone_below_the_knee` walks.
        """
        volts = self.macro(CEIL) * self._curve_volts
        if volts <= self.CLIPPER_CEILING:
            return 1.0
        return self.CLIPPER_CEILING / volts

    @classmethod
    def _headroom(cls, clipper_volts, wet_level):
        """Split the wet level between `post_gain` and the mixer voice so
        the clipper's own output stays under `CLIPPER_CEILING`.

        Ceiling scales the diode drop, and at 2.0x the clipper asks the
        node for 1.32 of full scale. The node cannot give it: its
        decimator rings a third past the rails on a square edge, so the
        Waveshaper saturates its own output at the BASE rate, which is
        hard clipping downstream of the half-band and the one kind of
        alias no oversampling factor can reach. The level was not there to
        be had either - measured on the bare node at 48 kHz, x4, a
        fully-clipped 1010 Hz tone reads -58.42 dB of inharmonic energy at
        `post_gain` 0.74, -47.92 at 0.80 and -34.03 at 1.00, while the
        output peak grows 0.4 dB over the same span.

        So the volume that was going to be applied on the mixer voice is
        moved in front of the node instead, which is where a pedal's
        volume pot sits, and only as much of it as the headroom needs: a
        setting that was not over the ceiling keeps exactly the split it
        had and its bytes do not move. Where even the whole wet level is
        not enough - Ceiling past MIDI 53 with Volume and Mix at maximum,
        MIDI 78 at the shipped Volume - `post_gain` stops at the ceiling
        and the level stops with it, 2.5 dB below where the saturating
        build sat and 18 dB cleaner.
        """
        move = 1.0
        if clipper_volts > cls.CLIPPER_CEILING:
            move = min(wet_level, cls.CLIPPER_CEILING / clipper_volts)
        post = clipper_volts * move
        level = wet_level if move <= 0.0 else wet_level / move
        return post, min(level, 1.0)

    def _push_filter(self):
        pot = self.macro(DIST)
        body = self.macro(BODY)
        r4 = R_BODY_STOCK + body * (R_BODY_RUETZ - R_BODY_STOCK)
        rf = pot * R_GAIN
        a = rf / R_LEG_BASS
        b = rf / r4
        total = 1.0 + a + b
        # voice 0 carries 1 + a*HP(60): level (1+a)/total with the biquad
        # crossfaded at a/(1+a), so its dry side is the follower. voice 1 is
        # b*HP(1539) at b/total. The two levels sum to 1 exactly, which is
        # where the 6 dB of clipper headroom over the old dry-minus-lowpass
        # pair comes from.
        self._leg_bass.mix = a / (1.0 + a)
        self._leg_treble.mix = 1.0
        self._leg_mix.voice[0].level = (1.0 + a) / total
        self._leg_mix.voice[1].level = b / total
        boost = _component.db_to_gain(self.macro(BOOST))
        self._shaper.set(
            pre_gain=total * boost / V_SCALE,
            bias=0.0,
            mix=1.0)
        gbw_hz = GBW_HZ / max(total, 1.0)
        f0, q = _fo_lp(self._hz(gbw_hz), self._sample_rate)
        self._gbw.frequency = f0
        self._gbw.Q = q
        p = self.macro(FILT)
        fc = 1.0 / (2.0 * math.pi * (FILTER_R0 + p * FILTER_POT) * FILTER_C)
        f0, q = _fo_lp(self._hz(fc), self._sample_rate)
        self._filt.frequency = f0
        self._filt.Q = q

    def _blend_curve(self, asymmetry):
        """Mix the two DS-1 tables at `asymmetry`, in place, in integers.

        Each table is normalised to its own extreme, so a straight lerp of
        the two would not be a lerp of *volts*: the asymmetric one's full
        scale is 1.220 V against the pair's 0.622. The weights below are
        each table's share of the blended volts, in Q8, so what comes out
        is the voltage curve the blend asks for and `_blend_volts` is what
        its full scale stands for. Returns that.

        Only called when Asymmetry moves - a knob move, not a block - and
        it writes into an array the build already owns.
        """
        low = _CURVE_DS1_DIODE_VOLTS
        high = _CURVE_DS1_ASYM_VOLTS
        # Single precision, because this reaches `post_gain` through
        # `_headroom` and a board computes it in float32 where a desktop
        # computes it in double (audiocomponents#75).
        volts = _f32(low + (high - low) * asymmetry)
        if self._blend_at == asymmetry:
            return volts, False
        steps = self.ASYM_BLEND_STEPS
        w_high = int(round(steps * asymmetry * high / volts))
        w_low = int(round(steps * (1.0 - asymmetry) * low / volts))
        table = self._blend
        pair = self._ds1_curve
        asym = self._ds1_asym
        for index in range(len(table)):
            value = (pair[index] * w_low + asym[index] * w_high) // steps
            if value > 32767:
                value = 32767
            elif value < -32768:
                value = -32768
            table[index] = value
        self._blend_at = asymmetry
        return volts, True

    def _push_scoop(self, wet_level):
        pot = self.macro(DIST)
        dist_gain = 1.0 + pot * (100000.0 / 4700.0)
        boost = _component.db_to_gain(self.macro(BOOST))
        self._shaper.set(
            pre_gain=dist_gain * boost / V_SCALE,
            bias=0.0,
            mix=1.0)
        tone = 0.5 * (self.macro(TONE) + 1.0)
        self._tone_lo.level = (1.0 - tone) * wet_level
        self._tone_hi.level = tone * wet_level
        # The DS-1's post-clip cap is the top of this pot's travel, not a
        # floor under it: `max(fc, CLIP_LP_HZ)` left 120 of 128 positions
        # on one section and ran the first six backwards.
        p = self.macro(FILT)
        fc = 1.0 / (2.0 * math.pi
                    * (FILTER_R0_SCOOP + p * FILTER_POT) * FILTER_C)
        f0, q = _fo_lp(self._hz(fc), self._sample_rate)
        self._clip_lp.frequency = f0
        self._clip_lp.Q = q
