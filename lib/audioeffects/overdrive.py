"""`Overdrive` - a Tube Screamer-shaped boost: dry plus a clipped shelf.

Rebuilt from scratch at Phase 4 against
`workspace docs/effects-internal/dossiers/Overdrive.md`, traits frozen
2026-09-17 at Station A. The old class in `drive.py` is consulted only for
the defects that dossier section 7 names: no macros, an asymmetric
OVERDRIVE curve, a hidden -3 dB trim, and a 4.5 kHz low-pass after mix.

**What it is.** The note always passes at unity. A high-passed copy is
gained, diode-limited, and added on top, then a movable low-pass. Drive is
never clean (dossier T6): even at the knob's floor a -14 dBFS 1 kHz tone is
already a double-digit THD. Mix 0 is the Tier 1 wire; Drive 0 is still that
12x stage.

**Mix is how much clipped voltage is added, not a crossfade to bypass.**
At Mix 0 the class hands back the source byte for byte - the pedal is out
of circuit, the way a true-bypass footswitch takes it out. One step above
zero the tone stack is in circuit on the dry note as well, so the step off
Mix 0 is a tone change, and that is the pedal switching on rather than a
fade.

**The clip table is a normalised shape, not volts.** `CURVE` fills Q15 to
both rails and `CURVE_VOLTS` is what its full scale stands for; the class
multiplies that into the shaper's `post_gain`. Level and curve are exactly
what they were, and the table keeps all the resolution it has - it used to
reach only 35 % of int16 (audiocomponents#77).

**Portability: audiodsp.** `audioshaper.Waveshaper`, `audiobiquad` for the
100 Hz tone points Q15 cannot carry, `audioroute` for the dry split. It
will not import on a stock CircuitPython board.

**Cost.** Palette sum at patch 0, x4, Mix 1: **1.684 / 2.928 ms -> 32 % /
55 %** of a 5.333 ms stereo block (dossier section 3). It was 1.584 / 2.759
ms until the third fix round added the output pole, which is one more
`audiobiquad` section on the clip branch - 0.100 ms on the P4 and 0.169 on
the S3, from the palette table. **No board has measured the graph with the
pole in it.** Lean patch: none.
The lean position is the constructor option `oversample=2`, which is
cheaper on the S3 and **surrenders T7** - at x2 the wet floor reads
-64.5 dB at the constructor default against a -70 dB bar, and -35.8 dB
at the worst macro corner against -40 dB.

**There is an output capacitor now.** A Tube Screamer is DC-coupled
inside and AC-coupled at the jack; this class had the first half only, so
Symmetry's operating-point offset walked out of the shaper and stood on
the output for ever - **+4461 LSB at shipped patch 6**, into digital
silence, at every rate (audit 3 ruling (n)). `DC_BLOCK_HZ` is a 30 Hz
pole on the clip branch behind the shaper, charged before the first block
and again whenever Symmetry, Mix or Ceiling moves the offset. Silence in
is now silence out at **every shipped patch at 48, 44.1 and 22.05 kHz -
peak 0, not merely zero by the last frame** - and a `program_change` onto
digital silence stays at 0. It costs two things, both measured: the clip
branch carries one more int16 node, which is worth **3.4 dB of alias
floor at the constructor default at 48 kHz** (-81.291 -> -77.939, 1.8 dB
at 44.1, 0.3 dB at 22.05), and a live macro move that changes the offset
re-charges the pole, which costs **one block of input** (5.3 ms at
48 kHz). On a build with no `audiocore.get_buffer` - CircuitPython's
default board build compiles it out - the charge is skipped and the
class's first block after a change is a step of up to 4461 LSB that
decays to zero in 62 ms.

**Latency: zero samples** at every macro setting. The dry tap is a copy.
`oversample` puts group delay on the *clip branch only*: 3.3 samples at
x4, 3.9 at x8, which is **0.069 ms** at 48 kHz x4, **0.081 ms** at 48 kHz
x8 and **0.088 ms** at the 44.1 kHz x8 this class ships. x1 is 0. It is
not on the sixteen-macro surface. Measured integer onset is **0 at every
rate, both channel counts, on all three interpreters**. `tail_samples` is
**4096**, over a worst measured ring of **2692 frames** (48 kHz, patch 6,
a 0 dBFS 1 kHz burst) - the 30 Hz pole is what made it long; it was 512
over a 222-frame ring before. The declaration is **level-free**: the ring
is 2639 to 2692 frames over 100 Hz and 1 kHz bursts at 0 dBFS and shorter
at every quieter input, because what rings is the pole and not the
signal. No delay line.

**The input ceiling is -1 dBFS at the shipped patches and -6 dBFS
anywhere on the surface** (`INPUT_CEILING_DBFS`, `SURFACE_CEILING_DBFS`).
The class adds a clipped shelf to a dry note at unity, so it runs out of
int16 somewhere, and until the third fix round it said nowhere.

**The oversampling factor follows the rate: x8 below 48 kHz, x4 at
48 kHz and above.** Every doubling is worth 11-16 dB of alias floor, and
x8 is where the node stops. 48 kHz keeps x4 because x8 there costs
+0.799 ms a block on the P4 and **+1.408 ms on the S3**, which projects
the S3 to a real-time factor of about 1.00 - the deadline itself. 44.1
and 22.05 kHz pay x8 against blocks 1.09x and 2.18x as long, so it is
free where the deadline is longer. **Every rate under 24 kHz leaves the
internal rate under the 192 kHz floor** and takes x8 because x8 is all
there is: 22.05 kHz runs 176.4 kHz, 16 kHz runs 128 kHz. **No board has
measured 44.1 or 22.05 kHz**, and the 48 kHz board figures are the only
ones this class has.

**Alias floors are stated on the wet branch, with the dry copy muted.**
The dry note is summed on the *circuit* mixer, one stage before the
output, so a mixed reading flatters every floor by **5.6 to 6.6 dB**.
`tools/effect_measurements.mute_dry` reaches the inner mixer; every
number below is that reading (audiocomponents#68, #81).

**Traits that are weaker at the shipped default than at a convenient
setting, named here.** Patch 0 is mid Drive (plateau ~36), Level 100/127,
Tone centre. Headline numbers are those defaults (CPython 48 kHz, 1 kHz
sine unless named):

- T1 at the default, **at -14 dBFS**: 100 Hz THD 1.883 % < 1 kHz
  12.549 %, and that holds at 44.1 (1.873 / 12.245) and 22.05 kHz (1.853
  / 11.080). **It is a claim about a sine at Body 720 Hz.** The
  pair reverses at Drive max (20.3 % vs 16.1 %), at the **bottom of the
  Body travel** - Body 360 crosses at all three rates, by less than 0.1
  percentage points - and on a square wave at the default (58.7 % vs
  20.0 %), whose own harmonics swamp the 100 Hz leg. **It reverses on a
  sawtooth too**, at all three rates and by a wide margin (86.2 % vs
  70.5 % at 48 kHz) - and a saw is closer to a pickup than either. Shipped
  patches **2** (Drive max) and **4** (Body 12) reverse it for the first
  two reasons. Small-signal gains are not SPICE's 23.3 / 38.8 / 37.7 dB;
  the fitted -3 dB pole at Drive max is **854 Hz**, outside 720 +/- 110.
- T2 even lines, **at -14 dBFS**: the trait names h2 **and h4**. At the
  constructor default h2 is -106.608 dB and h4 does not read at all;
  **patch 0 read back is h2 -119.206 dB** - it was -64.5 dB until
  audiocomponents#87 gave a bipolar macro an exact centre at MIDI 64. h3 at Drive max is -16.6 dB, outside
  SPICE -12.6 +/- 2. Shipped patch 6 (Asymmetric) is h2 -25.8 dB with
  **h4 -31.8 dB** beside it - the same character, one more line.
- T3 Delta-peak at the default is 0.160 / 0.174 / 0.109 V at -26 / -14 /
  -6 dBFS, below the 0.30-0.55 V band; at Drive max it is 0.291 / 0.311 /
  0.284 V. **Those are the readings behind the output pole**, which takes
  the clip branch's own offset off the peak; they were 0.297 / 0.326 /
  0.299 at Drive max without it. THD still falls -14 -> -6 dBFS at the default. **Outside that
  stated pair the level law is not monotone**: THD *rises* -20 -> -14
  dBFS at 48 and 44.1 kHz, turns back up at -1 dBFS at 22.05 kHz, and
  rises with level at 100 Hz. No output rail is hit at any of those
  levels, so the turn is the shaper and not the mixer.
- T4 is **disconfirmed**: the tone stack is a moving first-order low-pass,
  not the TS wiper network, and the brightest setting is up at 5 kHz where
  SPICE is 3.5 dB down.
- T5 THD at **-26 dBFS** rises with Drive - 2.346 / 9.631 / 14.630 % at
  Drive MIDI 0 / 64 / 127 - **and that is a claim at Symmetry centred**.
  Off centre the law turns over: at Symmetry MIDI 0, 32, 96 and 127 the
  THD peaks at Drive MIDI 64 and *falls* above it (at Symmetry 0: 8.601 /
  19.875 / 24.900 / 20.291 / 17.660 % over Drive 0 / 32 / 64 / 96 / 127),
  at all three rates. Symmetry is a bias into the shaper, so it decides
  which part of the curve the drive is pushing into, and the trait row
  never said so. End-to-end plateau gain is **not** 10-15 / 90-130 (Drive
  min/max at -72 dBFS is about x4 / x34).
- T6 at Drive *minimum* is 8.305 % THD at -14 dBFS, **under** the 10-40 %
  bar; at the default the class is dirtier (12.549 %).
- T7's bar was **restated on 2026-09-17** under vision section 7.2 and
  narrowed again by the third fix round, which found the redefinition was
  claiming more rates than it had earned. It is now four bars **and a
  rate rule**, all on the wet branch at 1010 Hz, **-6 dBFS unless the row
  says otherwise**:
  **-70 dB at the constructor default** (measured -77.939 / -78.698 /
  -75.565 at 48 / 44.1 / 22.05 kHz), **-50 dB at every shipped patch as
  shipped** (worst patch 3, -56.078 / -71.365 / -54.443), **-40 dB
  anywhere on the macro surface** (worst -47.642 / -61.049 / -46.608, at
  Drive max with Body at the bottom of its travel and Tone open), and
  **-40 dB at that corner at every input level up to full scale** (worst
  -41.956 / -52.157 / **-41.328**, all three at 0 dBFS). A fifth, T7e,
  says what the oversampling is worth: `ALIAS_OVERSAMPLE_COST_DB`.
- **Where the old -60 dB target still stands: 44.1 kHz.** The
  redefinition's first condition is that the old target is unreachable,
  and that is true at two of this class's three rates, not three. At
  **44.1 kHz** the shipped x8 build meets -60 dB on the wet branch
  everywhere - default -78.698, worst shipped patch -71.365, **worst
  surface cell -61.049** - so the old bar is kept there and tested there,
  and the redefinition is not invoked. At **48 kHz** x4 reads -47.642 at
  that corner and x8 would read **-63.870**; the class declines x8 on
  cost (+0.799 ms a block on the P4, +1.408 on the S3, which projects the
  S3 to rt 1.00) and that projection **has no board behind it** - a board
  run at x8 is what would settle it. At **22.05 kHz** x8 reads -46.608
  and x16 does not exist: `AUDIODSP_SHAPER_MAX_OVERSAMPLE` is 8
  (`audiodsp/src/shared/audiodsp_shaper.h:72`), which vision section 6
  routes to a node ask, and it is filed as **audiodsp#104**.
- T7's **3700 Hz** diagnostic at full Drive does **not** hold, and the
  figure the pack published for it was a **mixed** reading. On the wet
  branch, with the dry voice muted and a whole number of periods in the
  transform, it is **-33.898 dB** at 48 kHz on T7's held line (Drive max)
  and **-32.065** at the worst macro corner; mixed, the same cell reads
  -37.804, which is where the old -37.7 came from. **5000 Hz is worse and
  was named nowhere**: -27.750 held and -30.726 at the corner at 48 kHz,
  -35.247 / -37.421 at 44.1 kHz, and **-24.117 / -29.684 at 22.05 kHz**,
  which is the worst inharmonic cell this class has anywhere. The tone
  stack and the high-pass sit in front of the clip, so the class is worse
  than the bare node up there. T7's own bars are 1010 Hz numbers and the
  class does not claim them at 3700 or 5000 Hz.
- **Level is the output stage and Mix does not attenuate the dry.** At
  Mix 1, Level MIDI 0 is silence, not a wire: the one mixer leg carrying
  the whole graph is at zero.
"""

VENDOR = "PyDevices"

from array import array
import math

import audiocore
import audiomixer

from . import _component

try:
    from audiodsp_util import float32 as _f32
except ImportError:                                  # pragma: no cover
    def _f32(value):
        return value

try:
    import audiobiquad
except ImportError:
    audiobiquad = None
try:
    import audioroute
except ImportError:
    audioroute = None
try:
    import audioshaper
except ImportError:
    audioshaper = None


# S1 component values. 0 dBFS ≡ 1.0 V.
R1 = 4700.0
R6 = 51000.0
P1 = 500000.0
C4 = 51e-12
TONE_LP_HZ = 796.0
UMAX = 3.0
MIN_Q = 0.05
MAX_Q = 60.0

# Patch 0 MIDI 64 / 100 / 127 mapped through the spans below.
DRIVE_DEFAULT = 12.0 * (108.0 / 12.0) ** (64.0 / 127.0)
LEVEL_DEFAULT = 100.0 / 127.0

# BEGIN OVERDRIVE_CURVE
#: Volts at the table's full scale. The table is normalised
#: to its own extreme so it fills int16 (audiocomponents#77)
#: and this carries the scale back out in `post_gain`.
CURVE_VOLTS = 0.347334239
CURVE_BYTES = (
    b"\x01\x80\x0b\x80\x15\x80\x20\x80\x2a\x80\x34\x80\x3e\x80\x48\x80"
    b"\x53\x80\x5d\x80\x67\x80\x72\x80\x7c\x80\x87\x80\x91\x80\x9c\x80"
    b"\xa6\x80\xb1\x80\xbb\x80\xc6\x80\xd0\x80\xdb\x80\xe5\x80\xf0\x80"
    b"\xfb\x80\x05\x81\x10\x81\x1b\x81\x26\x81\x30\x81\x3b\x81\x46\x81"
    b"\x51\x81\x5c\x81\x67\x81\x72\x81\x7d\x81\x88\x81\x93\x81\x9e\x81"
    b"\xa9\x81\xb4\x81\xbf\x81\xca\x81\xd5\x81\xe1\x81\xec\x81\xf7\x81"
    b"\x02\x82\x0e\x82\x19\x82\x24\x82\x30\x82\x3b\x82\x46\x82\x52\x82"
    b"\x5d\x82\x69\x82\x75\x82\x80\x82\x8c\x82\x97\x82\xa3\x82\xaf\x82"
    b"\xba\x82\xc6\x82\xd2\x82\xde\x82\xea\x82\xf5\x82\x01\x83\x0d\x83"
    b"\x19\x83\x25\x83\x31\x83\x3d\x83\x49\x83\x55\x83\x62\x83\x6e\x83"
    b"\x7a\x83\x86\x83\x92\x83\x9f\x83\xab\x83\xb7\x83\xc4\x83\xd0\x83"
    b"\xdd\x83\xe9\x83\xf6\x83\x02\x84\x0f\x84\x1b\x84\x28\x84\x35\x84"
    b"\x41\x84\x4e\x84\x5b\x84\x68\x84\x75\x84\x82\x84\x8e\x84\x9b\x84"
    b"\xa8\x84\xb5\x84\xc3\x84\xd0\x84\xdd\x84\xea\x84\xf7\x84\x04\x85"
    b"\x12\x85\x1f\x85\x2c\x85\x3a\x85\x47\x85\x55\x85\x62\x85\x70\x85"
    b"\x7d\x85\x8b\x85\x99\x85\xa6\x85\xb4\x85\xc2\x85\xd0\x85\xdd\x85"
    b"\xeb\x85\xf9\x85\x07\x86\x15\x86\x23\x86\x31\x86\x40\x86\x4e\x86"
    b"\x5c\x86\x6a\x86\x79\x86\x87\x86\x95\x86\xa4\x86\xb2\x86\xc1\x86"
    b"\xcf\x86\xde\x86\xed\x86\xfb\x86\x0a\x87\x19\x87\x28\x87\x37\x87"
    b"\x46\x87\x55\x87\x64\x87\x73\x87\x82\x87\x91\x87\xa0\x87\xaf\x87"
    b"\xbf\x87\xce\x87\xdd\x87\xed\x87\xfc\x87\x0c\x88\x1c\x88\x2b\x88"
    b"\x3b\x88\x4b\x88\x5b\x88\x6a\x88\x7a\x88\x8a\x88\x9a\x88\xab\x88"
    b"\xbb\x88\xcb\x88\xdb\x88\xeb\x88\xfc\x88\x0c\x89\x1d\x89\x2d\x89"
    b"\x3e\x89\x4e\x89\x5f\x89\x70\x89\x81\x89\x91\x89\xa2\x89\xb3\x89"
    b"\xc4\x89\xd6\x89\xe7\x89\xf8\x89\x09\x8a\x1b\x8a\x2c\x8a\x3e\x8a"
    b"\x4f\x8a\x61\x8a\x72\x8a\x84\x8a\x96\x8a\xa8\x8a\xba\x8a\xcc\x8a"
    b"\xde\x8a\xf0\x8a\x02\x8b\x14\x8b\x27\x8b\x39\x8b\x4c\x8b\x5e\x8b"
    b"\x71\x8b\x84\x8b\x96\x8b\xa9\x8b\xbc\x8b\xcf\x8b\xe2\x8b\xf5\x8b"
    b"\x09\x8c\x1c\x8c\x2f\x8c\x43\x8c\x56\x8c\x6a\x8c\x7d\x8c\x91\x8c"
    b"\xa5\x8c\xb9\x8c\xcd\x8c\xe1\x8c\xf5\x8c\x0a\x8d\x1e\x8d\x32\x8d"
    b"\x47\x8d\x5c\x8d\x70\x8d\x85\x8d\x9a\x8d\xaf\x8d\xc4\x8d\xd9\x8d"
    b"\xee\x8d\x04\x8e\x19\x8e\x2f\x8e\x44\x8e\x5a\x8e\x70\x8e\x86\x8e"
    b"\x9c\x8e\xb2\x8e\xc8\x8e\xde\x8e\xf5\x8e\x0b\x8f\x22\x8f\x39\x8f"
    b"\x4f\x8f\x66\x8f\x7d\x8f\x95\x8f\xac\x8f\xc3\x8f\xdb\x8f\xf2\x8f"
    b"\x0a\x90\x22\x90\x3a\x90\x52\x90\x6a\x90\x82\x90\x9b\x90\xb3\x90"
    b"\xcc\x90\xe5\x90\xfe\x90\x17\x91\x30\x91\x49\x91\x63\x91\x7c\x91"
    b"\x96\x91\xb0\x91\xca\x91\xe4\x91\xfe\x91\x19\x92\x33\x92\x4e\x92"
    b"\x69\x92\x84\x92\x9f\x92\xba\x92\xd6\x92\xf1\x92\x0d\x93\x29\x93"
    b"\x45\x93\x61\x93\x7e\x93\x9a\x93\xb7\x93\xd4\x93\xf1\x93\x0e\x94"
    b"\x2b\x94\x49\x94\x67\x94\x85\x94\xa3\x94\xc1\x94\xe0\x94\xfe\x94"
    b"\x1d\x95\x3c\x95\x5c\x95\x7b\x95\x9b\x95\xbb\x95\xdb\x95\xfb\x95"
    b"\x1b\x96\x3c\x96\x5d\x96\x7e\x96\x9f\x96\xc1\x96\xe3\x96\x05\x97"
    b"\x27\x97\x4a\x97\x6d\x97\x90\x97\xb3\x97\xd6\x97\xfa\x97\x1e\x98"
    b"\x42\x98\x67\x98\x8c\x98\xb1\x98\xd6\x98\xfc\x98\x22\x99\x48\x99"
    b"\x6e\x99\x95\x99\xbc\x99\xe4\x99\x0b\x9a\x33\x9a\x5c\x9a\x84\x9a"
    b"\xad\x9a\xd7\x9a\x01\x9b\x2b\x9b\x55\x9b\x80\x9b\xab\x9b\xd6\x9b"
    b"\x02\x9c\x2e\x9c\x5b\x9c\x88\x9c\xb5\x9c\xe3\x9c\x11\x9d\x40\x9d"
    b"\x6f\x9d\x9f\x9d\xcf\x9d\xff\x9d\x30\x9e\x61\x9e\x93\x9e\xc6\x9e"
    b"\xf8\x9e\x2c\x9f\x60\x9f\x94\x9f\xc9\x9f\xfe\x9f\x34\xa0\x6b\xa0"
    b"\xa2\xa0\xda\xa0\x12\xa1\x4b\xa1\x85\xa1\xbf\xa1\xfa\xa1\x36\xa2"
    b"\x72\xa2\xaf\xa2\xec\xa2\x2b\xa3\x6a\xa3\xaa\xa3\xeb\xa3\x2c\xa4"
    b"\x6e\xa4\xb2\xa4\xf6\xa4\x3b\xa5\x80\xa5\xc7\xa5\x0f\xa6\x57\xa6"
    b"\xa1\xa6\xec\xa6\x37\xa7\x84\xa7\xd2\xa7\x21\xa8\x71\xa8\xc2\xa8"
    b"\x15\xa9\x69\xa9\xbe\xa9\x14\xaa\x6c\xaa\xc5\xaa\x20\xab\x7c\xab"
    b"\xda\xab\x39\xac\x9a\xac\xfc\xac\x61\xad\xc7\xad\x2f\xae\x99\xae"
    b"\x04\xaf\x72\xaf\xe2\xaf\x54\xb0\xc9\xb0\x3f\xb1\xb8\xb1\x34\xb2"
    b"\xb2\xb2\x33\xb3\xb7\xb3\x3d\xb4\xc7\xb4\x53\xb5\xe3\xb5\x76\xb6"
    b"\x0d\xb7\xa7\xb7\x45\xb8\xe7\xb8\x8c\xb9\x36\xba\xe5\xba\x98\xbb"
    b"\x4f\xbc\x0c\xbd\xcd\xbd\x94\xbe\x61\xbf\x33\xc0\x0b\xc1\xe9\xc1"
    b"\xce\xc2\xba\xc3\xac\xc4\xa6\xc5\xa6\xc6\xaf\xc7\xbf\xc8\xd8\xc9"
    b"\xf9\xca\x23\xcc\x55\xcd\x90\xce\xd5\xcf\x22\xd1\x79\xd2\xda\xd3"
    b"\x44\xd5\xb8\xd6\x35\xd8\xbb\xd9\x4b\xdb\xe3\xdc\x85\xde\x2f\xe0"
    b"\xe1\xe1\x9b\xe3\x5d\xe5\x26\xe7\xf5\xe8\xcb\xea\xa6\xec\x87\xee"
    b"\x6c\xf0\x56\xf2\x43\xf4\x33\xf6\x25\xf8\x1a\xfa\x11\xfc\x08\xfe"
    b"\x00\x00\xf8\x01\xef\x03\xe6\x05\xdb\x07\xcd\x09\xbd\x0b\xaa\x0d"
    b"\x94\x0f\x79\x11\x5a\x13\x35\x15\x0b\x17\xda\x18\xa3\x1a\x65\x1c"
    b"\x1f\x1e\xd1\x1f\x7b\x21\x1d\x23\xb5\x24\x45\x26\xcb\x27\x48\x29"
    b"\xbc\x2a\x26\x2c\x87\x2d\xde\x2e\x2b\x30\x70\x31\xab\x32\xdd\x33"
    b"\x07\x35\x28\x36\x41\x37\x51\x38\x5a\x39\x5a\x3a\x54\x3b\x46\x3c"
    b"\x32\x3d\x17\x3e\xf5\x3e\xcd\x3f\x9f\x40\x6c\x41\x33\x42\xf4\x42"
    b"\xb1\x43\x68\x44\x1b\x45\xca\x45\x74\x46\x19\x47\xbb\x47\x59\x48"
    b"\xf3\x48\x8a\x49\x1d\x4a\xad\x4a\x39\x4b\xc3\x4b\x49\x4c\xcd\x4c"
    b"\x4e\x4d\xcc\x4d\x48\x4e\xc1\x4e\x37\x4f\xac\x4f\x1e\x50\x8e\x50"
    b"\xfc\x50\x67\x51\xd1\x51\x39\x52\x9f\x52\x04\x53\x66\x53\xc7\x53"
    b"\x26\x54\x84\x54\xe0\x54\x3b\x55\x94\x55\xec\x55\x42\x56\x97\x56"
    b"\xeb\x56\x3e\x57\x8f\x57\xdf\x57\x2e\x58\x7c\x58\xc9\x58\x14\x59"
    b"\x5f\x59\xa9\x59\xf1\x59\x39\x5a\x80\x5a\xc5\x5a\x0a\x5b\x4e\x5b"
    b"\x92\x5b\xd4\x5b\x15\x5c\x56\x5c\x96\x5c\xd5\x5c\x14\x5d\x51\x5d"
    b"\x8e\x5d\xca\x5d\x06\x5e\x41\x5e\x7b\x5e\xb5\x5e\xee\x5e\x26\x5f"
    b"\x5e\x5f\x95\x5f\xcc\x5f\x02\x60\x37\x60\x6c\x60\xa0\x60\xd4\x60"
    b"\x08\x61\x3a\x61\x6d\x61\x9f\x61\xd0\x61\x01\x62\x31\x62\x61\x62"
    b"\x91\x62\xc0\x62\xef\x62\x1d\x63\x4b\x63\x78\x63\xa5\x63\xd2\x63"
    b"\xfe\x63\x2a\x64\x55\x64\x80\x64\xab\x64\xd5\x64\xff\x64\x29\x65"
    b"\x53\x65\x7c\x65\xa4\x65\xcd\x65\xf5\x65\x1c\x66\x44\x66\x6b\x66"
    b"\x92\x66\xb8\x66\xde\x66\x04\x67\x2a\x67\x4f\x67\x74\x67\x99\x67"
    b"\xbe\x67\xe2\x67\x06\x68\x2a\x68\x4d\x68\x70\x68\x93\x68\xb6\x68"
    b"\xd9\x68\xfb\x68\x1d\x69\x3f\x69\x61\x69\x82\x69\xa3\x69\xc4\x69"
    b"\xe5\x69\x05\x6a\x25\x6a\x45\x6a\x65\x6a\x85\x6a\xa4\x6a\xc4\x6a"
    b"\xe3\x6a\x02\x6b\x20\x6b\x3f\x6b\x5d\x6b\x7b\x6b\x99\x6b\xb7\x6b"
    b"\xd5\x6b\xf2\x6b\x0f\x6c\x2c\x6c\x49\x6c\x66\x6c\x82\x6c\x9f\x6c"
    b"\xbb\x6c\xd7\x6c\xf3\x6c\x0f\x6d\x2a\x6d\x46\x6d\x61\x6d\x7c\x6d"
    b"\x97\x6d\xb2\x6d\xcd\x6d\xe7\x6d\x02\x6e\x1c\x6e\x36\x6e\x50\x6e"
    b"\x6a\x6e\x84\x6e\x9d\x6e\xb7\x6e\xd0\x6e\xe9\x6e\x02\x6f\x1b\x6f"
    b"\x34\x6f\x4d\x6f\x65\x6f\x7e\x6f\x96\x6f\xae\x6f\xc6\x6f\xde\x6f"
    b"\xf6\x6f\x0e\x70\x25\x70\x3d\x70\x54\x70\x6b\x70\x83\x70\x9a\x70"
    b"\xb1\x70\xc7\x70\xde\x70\xf5\x70\x0b\x71\x22\x71\x38\x71\x4e\x71"
    b"\x64\x71\x7a\x71\x90\x71\xa6\x71\xbc\x71\xd1\x71\xe7\x71\xfc\x71"
    b"\x12\x72\x27\x72\x3c\x72\x51\x72\x66\x72\x7b\x72\x90\x72\xa4\x72"
    b"\xb9\x72\xce\x72\xe2\x72\xf6\x72\x0b\x73\x1f\x73\x33\x73\x47\x73"
    b"\x5b\x73\x6f\x73\x83\x73\x96\x73\xaa\x73\xbd\x73\xd1\x73\xe4\x73"
    b"\xf7\x73\x0b\x74\x1e\x74\x31\x74\x44\x74\x57\x74\x6a\x74\x7c\x74"
    b"\x8f\x74\xa2\x74\xb4\x74\xc7\x74\xd9\x74\xec\x74\xfe\x74\x10\x75"
    b"\x22\x75\x34\x75\x46\x75\x58\x75\x6a\x75\x7c\x75\x8e\x75\x9f\x75"
    b"\xb1\x75\xc2\x75\xd4\x75\xe5\x75\xf7\x75\x08\x76\x19\x76\x2a\x76"
    b"\x3c\x76\x4d\x76\x5e\x76\x6f\x76\x7f\x76\x90\x76\xa1\x76\xb2\x76"
    b"\xc2\x76\xd3\x76\xe3\x76\xf4\x76\x04\x77\x15\x77\x25\x77\x35\x77"
    b"\x45\x77\x55\x77\x66\x77\x76\x77\x86\x77\x96\x77\xa5\x77\xb5\x77"
    b"\xc5\x77\xd5\x77\xe4\x77\xf4\x77\x04\x78\x13\x78\x23\x78\x32\x78"
    b"\x41\x78\x51\x78\x60\x78\x6f\x78\x7e\x78\x8d\x78\x9c\x78\xab\x78"
    b"\xba\x78\xc9\x78\xd8\x78\xe7\x78\xf6\x78\x05\x79\x13\x79\x22\x79"
    b"\x31\x79\x3f\x79\x4e\x79\x5c\x79\x6b\x79\x79\x79\x87\x79\x96\x79"
    b"\xa4\x79\xb2\x79\xc0\x79\xcf\x79\xdd\x79\xeb\x79\xf9\x79\x07\x7a"
    b"\x15\x7a\x23\x7a\x30\x7a\x3e\x7a\x4c\x7a\x5a\x7a\x67\x7a\x75\x7a"
    b"\x83\x7a\x90\x7a\x9e\x7a\xab\x7a\xb9\x7a\xc6\x7a\xd4\x7a\xe1\x7a"
    b"\xee\x7a\xfc\x7a\x09\x7b\x16\x7b\x23\x7b\x30\x7b\x3d\x7b\x4b\x7b"
    b"\x58\x7b\x65\x7b\x72\x7b\x7e\x7b\x8b\x7b\x98\x7b\xa5\x7b\xb2\x7b"
    b"\xbf\x7b\xcb\x7b\xd8\x7b\xe5\x7b\xf1\x7b\xfe\x7b\x0a\x7c\x17\x7c"
    b"\x23\x7c\x30\x7c\x3c\x7c\x49\x7c\x55\x7c\x61\x7c\x6e\x7c\x7a\x7c"
    b"\x86\x7c\x92\x7c\x9e\x7c\xab\x7c\xb7\x7c\xc3\x7c\xcf\x7c\xdb\x7c"
    b"\xe7\x7c\xf3\x7c\xff\x7c\x0b\x7d\x16\x7d\x22\x7d\x2e\x7d\x3a\x7d"
    b"\x46\x7d\x51\x7d\x5d\x7d\x69\x7d\x74\x7d\x80\x7d\x8b\x7d\x97\x7d"
    b"\xa3\x7d\xae\x7d\xba\x7d\xc5\x7d\xd0\x7d\xdc\x7d\xe7\x7d\xf2\x7d"
    b"\xfe\x7d\x09\x7e\x14\x7e\x1f\x7e\x2b\x7e\x36\x7e\x41\x7e\x4c\x7e"
    b"\x57\x7e\x62\x7e\x6d\x7e\x78\x7e\x83\x7e\x8e\x7e\x99\x7e\xa4\x7e"
    b"\xaf\x7e\xba\x7e\xc5\x7e\xd0\x7e\xda\x7e\xe5\x7e\xf0\x7e\xfb\x7e"
    b"\x05\x7f\x10\x7f\x1b\x7f\x25\x7f\x30\x7f\x3a\x7f\x45\x7f\x4f\x7f"
    b"\x5a\x7f\x64\x7f\x6f\x7f\x79\x7f\x84\x7f\x8e\x7f\x99\x7f\xa3\x7f"
    b"\xad\x7f\xb8\x7f\xc2\x7f\xcc\x7f\xd6\x7f\xe0\x7f\xeb\x7f\xf5\x7f"
    b"\xff\x7f"
)
# END OVERDRIVE_CURVE

CURVE = array("h", CURVE_BYTES)

#: The clip stage runs at or above this internal rate where it can. The
#: factor follows the rate rather than being a constant the 48 kHz bench
#: happened to be right about: every doubling is worth 11-16 dB of alias
#: floor, measured (pack section 14, `reach`).
OVERSAMPLE_FLOOR_HZ = 192000.0

#: T7's bars, **restated 2026-09-17** (second fix round) under vision
#: section 7.2. Wet-branch inharmonic energy in a 1010 Hz -6 dBFS sine, dB
#: under the fundamental, read with the dry voice muted. The old target was
#: a single -60 dB everywhere; x8 is all the node has and at 22.05 kHz it
#: reads -46.6 dB at the worst macro corner, while x8 at 48 kHz would put
#: the S3 at a projected real-time factor of 1.00. Dossier section 3a.
ALIAS_DEFAULT_DB = -70.0        #: at the constructor default
ALIAS_PATCH_DB = -50.0          #: at every shipped patch, as shipped
ALIAS_SURFACE_DB = -40.0        #: anywhere on the macro surface

#: T7e, **added by the third fix round**: what the shipped oversampling is
#: worth, in dB of wet alias floor, against the same class run at the base
#: rate - at every surface position where the clip stage is in circuit,
#: which is Drive above its floor **and** Body below the top of its travel.
#: Measured over the pack's 54 positions at three rates: 47 of 52 gradable
#: cells clear this at 48 and 44.1 kHz and all 52 clear it at 22.05 kHz;
#: the worst cell that carries the clause is **+20.520 dB** (`body=360`,
#: 48 kHz). The five cells outside the region are worth 0.81 to 15.32 dB
#: and are named in the class docstring with their numbers.
#:
#: This is the clause that makes `BaseRate` a guard rather than a
#: diagnostic. Under the three absolute bars alone it was healthy at 17 of
#: 54 positions (audit 3 (p)2, ruling (i)) - not because switching the
#: oversampling off removed nothing there, which was the old defence and
#: is false at twelve of them, but because the class has 30 to 40 dB of
#: margin at those settings. Under T7e it is red at every position the
#: clause is claimed over, because its own cost is 0 dB by construction.
ALIAS_OVERSAMPLE_COST_DB = 20.0

#: The input ceiling, stated because the class **adds** a clipped shelf to
#: a dry note at unity and so has to run out of headroom somewhere (audit 3
#: ruling (o)). Sine into the output's int16, 100 Hz to 2 kHz:
#:
#: * **-1 dBFS** at every shipped patch. Patch 7 `Edge Boost` is the one
#:   that reaches the rail at all, 4 samples of 9600 at 0 dBFS / 400 Hz.
#: * **-6 dBFS** anywhere on the macro surface. Drive max with Level max
#:   and Tone open rails at -3 dBFS (570 of 9600 at 700 Hz).
#:
#: The 30 Hz output pole bought most of this: before it, patch 7 railed at
#: **-3 dBFS** at 700 Hz and 1 kHz, because Symmetry's offset rode on the
#: peaks. The standing offset is now blocked and only the signal itself
#: reaches the rail.
INPUT_CEILING_DBFS = -1.0
SURFACE_CEILING_DBFS = -6.0


def shipped_oversample(sample_rate):
    """The factor this rate ships with: x4 at 48 kHz and up, x8 below it.

    Never below x4, because x2's own node floor at 1010 Hz is -56.4 dB and
    fails T7 before the class is in it; never above x8, because the node
    stops there and because the cost is real - x8 at 48 kHz is +0.799 ms
    on the P4 and +1.408 ms on the S3 per block, which is the whole of why
    the budget's rate keeps x4.

    So the rule is exactly: **x8 at every rate below 48 kHz, x4 at 48 kHz
    and above.** The 192 kHz floor is reached at 48 kHz and above only.
    **Every rate under 24 kHz leaves the internal rate under that floor**
    and takes x8 anyway because x8 is all there is: 22.05 kHz runs
    176.4 kHz internally, and 16 kHz - outside this program's three rates,
    but reachable - runs 128 kHz and reads **-50.451 dB** at Drive max on
    the wet branch, **-41.732 dB** at the worst macro corner. (The -56.9 dB
    the second fix round quoted here was a *mixed* reading, with the dry
    note diluting the floor by about 6 dB.) The ceiling is the node's:
    `AUDIODSP_SHAPER_MAX_OVERSAMPLE` is 8, and audiodsp#104 is the ask.
    The floor is a target, not a guarantee, and the class's bars are
    `ALIAS_DEFAULT_DB` / `ALIAS_PATCH_DB` / `ALIAS_SURFACE_DB` /
    `ALIAS_OVERSAMPLE_COST_DB`.
    """
    factor = 4
    while factor < 8 and float(sample_rate) * factor < OVERSAMPLE_FLOOR_HZ:
        factor *= 2
    return factor


#: The output capacitor, third fix round. A TS is DC-coupled inside and
#: AC-coupled at the jack; the class had the first half only, so Symmetry's
#: operating-point offset walked straight out of the shaper and stood on the
#: output for ever - **+4461 LSB at shipped patch 6** into digital silence
#: (audit 3 ruling (n)). This pole sits after the shaper, on the clip branch
#: only, so the dry note is still a byte-exact copy. 30 Hz because the clip
#: branch is already high-passed at Body (360 Hz at its lowest), so the pole
#: takes nothing a player hears, and because it has to settle: at 20 Hz the
#: offset was still nonzero at frame 16383, at 30 Hz it is exactly zero from
#: frame 2965.
DC_BLOCK_HZ = 30.0
DC_BLOCK_Q = 0.5

#: How many blocks `_settle_dc` will pull before it gives up. The pole needs
#: about 3000 frames at 48 kHz; 64 blocks is 16384 frames, five times that.
DC_SETTLE_BLOCKS = 64

#: The length of the zero sample the charge is pulled through, in frames.
#: One block, because the shaper's `play()` has no `loop` and the charge
#: re-plays it per pull; 2 KB of stereo int16 that only the charge holds.
DC_QUIET_FRAMES = 512


def _one_pole(freq, park):
    freq = max(1.0, float(freq))
    park = max(freq * 1.01, float(park))
    f0 = math.sqrt(freq * park)
    q = f0 / (freq + park)
    return f0, min(MAX_Q, max(MIN_Q, q))


class Overdrive(_component.Component):
    """Dry plus a diode-limited high-pass; Tube Screamer structure."""

    NAME = 'Overdrive'
    DISPLAY_NAME = 'Overdrive'
    CATEGORIES = ('Distortion',)
    VERSION = '0.0.2'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioshaper", "audiobiquad", "audioroute")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 4096

    #: T7's bars, so a test or a probe reads them from one place.
    ALIAS_DEFAULT_DB = ALIAS_DEFAULT_DB
    ALIAS_PATCH_DB = ALIAS_PATCH_DB
    ALIAS_SURFACE_DB = ALIAS_SURFACE_DB
    ALIAS_OVERSAMPLE_COST_DB = ALIAS_OVERSAMPLE_COST_DB
    INPUT_CEILING_DBFS = INPUT_CEILING_DBFS
    SURFACE_CEILING_DBFS = SURFACE_CEILING_DBFS

    MACRO_LABELS = ("Drive", "Tone", "Level", "Mix", "Body", "Ceiling",
                    "Symmetry")
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
        4: "UNIPOLAR", 5: "UNIPOLAR", 6: "BIPOLAR",
    }
    _MACRO_RANGES = (
        (12.0, 108.0, "log"),
        (0.0, 1.0),
        (0.0, 1.0),
        (0.0, 1.0),
        (360.0, 1440.0, "log"),
        (0.5, 1.0),
        (-1.0, 1.0),
    )
    PATCHES = {
        0: ("Mid Drive Flat", (64, 64, 100, 127, 64, 127, 64)),
        1: ("Low Drive Bright", (16, 110, 100, 127, 64, 127, 64)),
        2: ("Full Drive Dark", (127, 20, 90, 127, 64, 127, 64)),
        3: ("Full Drive Bright", (127, 118, 84, 127, 64, 127, 64)),
        4: ("Thick Body Mid Drive", (72, 60, 100, 127, 12, 127, 64)),
        5: ("Tight Body High Drive", (100, 80, 96, 127, 118, 127, 64)),
        6: ("Asymmetric Mid Drive", (64, 64, 100, 127, 64, 127, 108)),
        7: ("Edge Boost", (0, 96, 127, 127, 64, 127, 64)),
    }

    def _build(self, drive=DRIVE_DEFAULT, tone=64.0 / 127.0,
               level=LEVEL_DEFAULT, mix=1.0, body=720.0, ceiling=1.0,
               symmetry=0.0, oversample=None, patch=None):
        rate = self._sample_rate
        channels = self._channel_count
        if oversample is None:
            factor = shipped_oversample(rate)
        else:
            factor = int(oversample)
            if factor not in (1, 2, 4, 8):
                raise ValueError("oversample must be 1, 2, 4 or 8")
        self._oversample = factor

        # The input adapter is not decoration. `audioroute.Splitter` wants
        # a source that hands back the palette's own blocks, and a plain
        # `audiocore.RawSample` - which is what an app feeds an effect -
        # hands back its whole array in one `get_buffer`. `MidSide` at
        # width 1.0 is the cheapest node that re-blocks it, and without it
        # the class renders silence from a bare RawSample while passing
        # every test whose probe chunks itself.
        adapter = audioroute.MidSide(width=1.0, sample_rate=rate,
                                     channel_count=channels)
        self._silence = audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels)
        # A second zero sample, because a sample plays in one place at a
        # time and `open_level_gates` takes `_silence` for the voices at
        # the very moment `_settle_dc` needs one for the shaper. It is a
        # block long rather than two frames long because the shaper's
        # native `play()` takes **no `loop` argument** - two frames would
        # run out inside the first pull on MicroPython and CircuitPython,
        # where the CPython twin's `loop=True` is not even accepted.
        self._quiet = audiocore.RawSample(
            array("h", bytes(2 * DC_QUIET_FRAMES * channels)),
            sample_rate=rate, channel_count=channels)
        adapter.play(self._source)
        split = audioroute.Splitter(adapter, taps=2)
        dry = split.tap(0)
        tap1 = split.tap(1)

        self._hp = audiobiquad.Biquad(
            mode=audiobiquad.HIGH_PASS, frequency=720.0, Q=0.15,
            sample_rate=rate, channel_count=channels)
        self._c4 = audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=6000.0, Q=0.15,
            sample_rate=rate, channel_count=channels)
        self._shaper = audioshaper.Waveshaper(
            sample_rate=rate, channel_count=channels, curve=CURVE,
            oversample=factor, mix=1.0, pre_gain=1.0, post_gain=1.0,
            bias=0.0, hysteresis=0.0)
        # The output capacitor. It is after the shaper and before the
        # circuit sum, so the dry copy never sees it.
        self._dc = audiobiquad.Biquad(
            mode=audiobiquad.HIGH_PASS, frequency=DC_BLOCK_HZ,
            Q=DC_BLOCK_Q, sample_rate=rate, channel_count=channels)
        # The clip branch is wired to the split *after* the offset has been
        # settled, below: a `play()` takes a block from whatever it is
        # handed, so re-pointing the shaper at `_c4` once the offset is
        # charged costs the caller nothing, while doing it the other way
        # round throws a block of the source away
        # (`AConstructorPatchCostsTheSourceNothing`).
        self._hp.play(tap1)
        self._c4.play(self._hp)
        self._shaper.play(self._c4)
        self._dc.play(self._shaper)

        circuit = audiomixer.Mixer(voice_count=2, **self._pcm())
        self._lp = audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=TONE_LP_HZ, Q=0.15,
            sample_rate=rate, channel_count=channels)
        # The Level stage. One voice, so it is the palette's own Mixer row
        # rather than a second summing point the budget cannot price - and
        # the node is built with one, which is what the comment used to
        # claim while asking for two.
        out = audiomixer.Mixer(voice_count=1, **self._pcm())

        self._lp.play(circuit)

        self._adapter = adapter
        self._split = split
        self._dry = dry
        self._tap1 = tap1
        self._circuit = circuit
        self._out = out

        self._own(out, reset=False)
        self._own(self._lp)
        self._own(circuit, reset=False)
        self._own(self._dc)
        self._own(self._shaper)
        self._own(self._c4)
        self._own(self._hp)
        self._own(dry, reset=False)
        self._own(tap1, reset=False)
        self._own(split, reset=False)
        self._own(adapter)
        self._own(self._silence, reset=False)
        self._own(self._quiet, reset=False)

        self._output = out
        self._primed = False
        self._ready = False
        self._dc_charged = False
        self._dc_key = None
        self._post_gain = 1.0
        self._clip_bias = 0.0
        self._init_macros(
            (drive, tone, level, mix, body, ceiling, symmetry), patch)

        # Arming a mixer voice resets the node it is given AND takes a
        # block from it, so the pole cannot be charged before this and
        # cannot be re-armed after it. The clip branch is therefore muted
        # at the shaper for the arming - the block the voice keeps is a
        # zero one - and charged once nothing will touch it again.
        if self._clip_bias:
            self._shaper.set(post_gain=0.0)
        _component.open_level_gates(
            circuit, [circuit.voice[0], circuit.voice[1]], self._silence)
        _component.open_level_gates(out, [out.voice[0]], self._silence)
        self._ready = True
        self._prime_if_wet()
        if self._clip_bias:
            self._shaper.set(post_gain=self._post_gain)
        self._settle_dc()

    def _shaper_dc(self):
        """What the shaper puts out with nothing at its input, in LSB.

        The table is read at `bias`, so the offset is `CURVE` interpolated
        at that point times the shaper's `post_gain` - no measurement, no
        extra node, and `test_the_computed_offset_is_the_one_the_shaper_
        emits` holds the arithmetic to the node itself.
        """
        span = len(CURVE) - 1
        where = (self._clip_bias + 1.0) * 0.5 * span
        index = int(where)
        if index >= span:
            return CURVE[span] * self._post_gain
        rise = where - index
        return (CURVE[index] * (1.0 - rise)
                + CURVE[index + 1] * rise) * self._post_gain

    def _settle_dc(self):
        """Charge the output capacitor before the first real block.

        The pole removes the standing offset but it cannot remove the step
        that starts it: a cold blocker hands its first block straight
        through, which is 4461 LSB of thump at shipped patch 6 and then
        62 ms of decay. So the pole is fed the offset on its own - a
        two-frame sample holding `_shaper_dc()`, looped - and pulled until
        a whole block comes back zero, about twelve blocks at 48 kHz.

        **Nothing upstream is touched**: not the source, not the split,
        not the shaper. That is the whole reason it is done this way
        rather than by running the circuit on silence, which is the same
        idea and costs the caller a block of input and one side of the
        split (`AConstructorPatchCostsTheSourceNothing`, `StarvedTapError`).

        It costs nothing at Symmetry 0, where there is no offset to
        settle. On a build with no `audiocore.get_buffer` - CircuitPython's
        default board build compiles it out - this does nothing and the
        thump is back; the class docstring says so.
        """
        pull = getattr(audiocore, "get_buffer", None)
        if pull is None:
            return False
        if not (self._clip_bias or self._dc_charged):
            return False
        self._dc_charged = bool(self._clip_bias)
        try:
            for index in range(DC_SETTLE_BLOCKS):
                # Re-played every pull: `_quiet` is one block long and the
                # node has no loop. The re-play resets the shaper's
                # oversampler, which costs a few samples of ramp at the
                # top of each block and nothing at all to the charge.
                self._shaper.play(self._quiet)
                _state, data = pull(self._dc)
                if not data:
                    break
                # The first block back is the one the pole was holding
                # before it was handed the offset, so it says nothing
                # about the new one. Reading it as the answer is how this
                # charged nothing at all for an afternoon.
                if index and not any(array("h", bytes(data))):
                    break
        finally:
            self._shaper.play(self._c4)
        return True

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _park(self):
        return self._sample_rate * 0.5 * _component.NYQUIST_MARGIN

    def _apply_macro(self, index, position):
        del position
        self._refresh()

    def _refresh(self):
        plateau = self._value(0)
        tone = self._value(1)
        mix = self._value(3)
        body = self._hz(self._value(4))
        ceiling = self._value(5)
        symmetry = self._value(6)
        park = self._park()

        r2 = max(1.0, (plateau - 1.0) * R1)
        pre = (r2 / R1) / UMAX
        # Mix rides the clipped voltage, not a crossfade: the dry note is
        # already in the circuit sum at unity, so scaling the clip here is
        # the whole of "how much overdrive" and costs no node. `CURVE_VOLTS`
        # is the third term because the table holds a normalised shape
        # rather than volts (audiocomponents#77); it is a constant, so the
        # clip branch's level is exactly what it was.
        self._post_gain = _f32(ceiling * mix * CURVE_VOLTS)
        self._clip_bias = _f32(0.12 * symmetry)
        self._shaper.set(pre_gain=_f32(pre), post_gain=self._post_gain,
                         bias=self._clip_bias, mix=1.0)

        self._hp.frequency = body
        self._hp.Q = 0.25
        self._hp.mix = 1.0

        c4_hz = 1.0 / (2.0 * math.pi * r2 * C4)
        if c4_hz >= park * 0.95:
            self._c4.mix = 0.0
        else:
            f0, q = _one_pole(self._hz(c4_hz), park)
            self._c4.frequency = f0
            self._c4.Q = q
            self._c4.mix = 1.0

        fc = 480.0 * (18.0 ** tone)
        f0, q = _one_pole(self._hz(fc), park)
        self._lp.frequency = f0
        self._lp.Q = q
        self._lp.mix = 1.0
        self._prime_if_wet()
        # The offset the pole has to hold off is `curve(bias) * post_gain`,
        # so Mix and Ceiling move it as well as Symmetry. Re-settle when
        # any of the three changes and there is - or was - an offset:
        # otherwise a `program_change` onto silence is a thump.
        key = (self._clip_bias, mix, ceiling)
        if key != self._dc_key:
            self._dc_key = key
            if getattr(self, "_ready", False):
                self._settle_dc()

    def _prime_if_wet(self):
        mix = self._value(3)
        level = self._value(2)
        if mix <= 0.0:
            self._output = self._source
            return
        if not getattr(self, "_ready", False):
            self._output = self._out
            return
        if not self._primed:
            self._circuit.voice[0].play(self._dry)
            self._circuit.voice[1].play(self._dc)
            self._out.voice[0].play(self._lp)
            self._primed = True
        self._output = self._out
        self._circuit.voice[0].level = 1.0
        self._circuit.voice[1].level = 1.0
        self._out.voice[0].level = level
