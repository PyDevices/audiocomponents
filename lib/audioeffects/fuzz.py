"""`Fuzz` - a biased germanium pair, with a Big Muff cascade as a second character.

Rebuilt from scratch for Phase 4 against
`workspace docs/effects-internal/dossiers/Fuzz.md`, traits frozen at
Station A on 2026-09-17 before this file existed. The old `drive.py:Fuzz`
was not consulted except for the five defects the dossier's section 7 names;
it was the class the library served until this one was adopted on the boards
on 2026-09-18, and `drive.py` went with the promotion.

**What it sounds like.** `germanium` (default) is a Fuzz Face: Q1 sits off
centre, so small signals clip on one half first and both halves go square
when you hit it. There is no tone stack. `cascade` is a Ram's Head 1973 Big
Muff: two silicon pairs and a mid scoop between 482 Hz and 1206 Hz.

**What the default surrenders.** Mix 1, Fuzz 36 dB, Bias 0, Load 0, Tilt 0.
Tone is inert on germanium. G2's 0.5 dB-per-step THD staircase is not met
here (the last steps are +0.17 / +0.04 / +0.008 dB); h2/h1 still moves.
Cascade C2's 25 dB THD-vs-Sustain bar is not met at −20 dBFS: both ends of
Sustain are already hard-clipped. Gating is the Bias macro's starved end,
not a moving bias - the node cannot follow an envelope.

**On `cascade`, Bias is a gate and not a bias, and what it gates is the
level.** Any position off centre rails both silicon pairs and the output
falls away: C3's three probe tones read **−15.5 dBFS** on average at
centre, **−26.8** at ±0.25, **−43.9** at ±0.5, **−56.2** at ±0.85 and
**−67.8** at ±1, monotone at all three rates. The **scoop survives the
whole travel** (+3.93 … +7.63 dB). Until the fourth fix round this row
said the opposite - "three probe tones come out at the same level, C3's
scoop reads 0.002 dB" - and that reading was the **DC**: with no coupling
capacitor behind the second clipper, three tones sitting on the same
−6 dBFS offset give three identical RMS readings whatever the tone stack
does (audiocomponents#89). Patch 2 "Starved bias, gated" is the only
shipped patch that moves Bias, and that is what it is for; its scoop reads
**2.561 dB** against C3's 3 dB bar, a **0.44 dB** miss where the offset
used to make it 1.9.

**C4 is claimed at Fuzz 18 … 32 dB and is disconfirmed above it, which
includes the `cascade` constructor's own 36 dB.** Inside the span the
notch centre moves 1206 / 762 / 482 Hz over Tone 0.25 / 0.5 / 0.75, a
**1.323 octave** span, at all three rates. At 34 dB and above the clipper
has filled the notch in and the Tone 0.75 curve rises monotonically across
the whole 150-2000 Hz probe grid - there is no interior minimum left to
read. The row used to claim 36 dB; that cell passed on the 300 Hz probe
reading **0.041 dB** under the 150 Hz one, which is not a notch, and the
output pole exposed it by taking 0.2-0.6 dB of sub-31 Hz content out of
the 150 Hz cell. Eight of the nine shipped patches sit at 36 dB or above
and are outside the row; only patch 3 `Cleaned up, load engaged` is
inside it.

**G1's peak clause was restated on 2026-09-17 under vision §7.2**, after the
output coupling went back where the circuit has it (below). At shipped
defaults, 1 kHz −20 dBFS: h2 **−26.92 dBc** and the even series h2+h4+h6+h8
**−21.33 dB** of the fundamental - the two clauses now, both ratios. The old
peak-split clause read **8.221 dB** and every bit of it was the DC offset
nothing was blocking; with the offset gone it is **0.768 dB** and cannot
express the asymmetry at all, because at 36 dB both halves are already at
the rail. Span: input **−46 … −20 dBFS**, and **G1 is level-free across it** -
walked at −46, −33 and −20 dBFS, the hardest point is −20 and it passes
there, which is the model ruling (m) asks every other row to follow. Also
**Fuzz ≤ 36 dB**, **Mix ≥ 0.5**,
**Output Tilt ≥ −3 dB**, Bias centred, any Level above 0, any Load, any
Tone, at all three rates - worst cell in it h2 −29.765, even −24.464. G1
holds at **patches 0, 2, 3 and 8** and misses at **1, 4, 5, 6 and 7** -
every patch at Fuzz 48 dB or above, where both halves square and h2 falls to
−38.91 … −47.46 dBc. That is the product at full fuzz, not a defect, and it
is why the claim is the default's.

**A4's alias floor was redefined on 2026-09-17 under vision §7.2, and
amended the same day** when the replacement turned out to be false at
22.05 kHz, on the Fuzz macro's own grid and at patch 8. The original target
was 20 Hz–20 kHz inharmonic energy ≥ 60 dB below the fundamental at 1010
*and* 3700 Hz at maximum Fuzz; at the shipped ×8 that holds at 1010 Hz only
up to Fuzz 30 dB and at **3700 Hz it fails at every position of the macro**.
What this class claims instead, all on the wet branch: **at 48 and
44.1 kHz**, at the shipped default, the floor is **≥ 50 dB** down at 1010 Hz
and **≥ 35 dB** at 3700 Hz (measured **−55.02 / −38.50** and
**−55.91 / −36.68**); ×8 is **≥ 20 dB** better than ×1 at both (measured
34.79 / 25.41 and 36.79 / 25.32); and **nowhere on the ×8 surface** - every
Fuzz, Bias and Output Tilt position and every shipped patch but the lean one
- does it rise above **35 dB** at 1010 Hz or **28 dB** at 3700 Hz. **The
worst cell is not the one the pack published.** Swept jointly rather than
one macro at a time, the 125-cell Fuzz × Bias × Tilt grid's worst is
**−35.407 dB at 44.1 kHz** (Fuzz 127, Bias centred, Tilt 127) and −36.322
at 48 kHz, against the −38.154 the row carried; at 3700 Hz it is −30.425
(44.1 kHz) against −30.478. **The margin at 1010 Hz is 0.4 dB**, not 3,
and a finer grid reaches −35.431 (audit 3 (p)3). The trait stands and the
number was wrong. Two things it gives up, in the same words as the pack
and the catalogue row: **patch 8 `Fuzz - lean` shapes at ×2 and reads
−30.57 / −19.59**, which is what the S3's block costs; and **at 22.05 kHz
the row is disconfirmed** (−25.09 / −13.47), because a fuzz's own harmonic
series crosses Nyquist at the *output* rate - h11 of 1010 Hz and h3 of
3700 Hz are both above 11.025 kHz - so what folds was never in the
oversampled path to be filtered, and ×8 buys 11.2 dB there against 34.8 at
48 kHz. At Phase 7, listen at full Fuzz on a high note for a thin metallic
ring that does not move with the note.

**Portability tier: audiodsp** (`REQUIRES = ("audioshaper", "audiobiquad",
"audioroute")`). On a stock CircuitPython board this module imports and
construction raises `ImportError`.

**Cost, palette, reference patch 0 (germanium, oversample 8)**, re-derived
2026-09-18 at the rows both boards took that morning:
3×Biquad 0.324/0.612 + Waveshaper ×8 1.933/3.368 + glue 0.0
= **2.257 / 3.980 ms → P4 42 %, S3 75 %** of a 5.333 ms stereo block.
**Patch 8 `Fuzz - lean`** shapes at ×2 through a second shaper the tilt
stage plays instead: 3×Biquad + Waveshaper ×2 0.558/1.017 = **0.882 /
1.629 ms → 17 % / 31 %**. That patch, not the constructor, is the S3's
shipped position.
The boards measured **44.4 % / 76.8 %** at patch 0, **18.5 % / 32.8 %** at
patch 8 and **44.6 % / 77.7 %** at the costliest shipped patch (second pass,
256-frame blocks, 2026-09-18) — **over by 2.1 / 2.2 points**, and the node
census confirms the count, so it is not a miscount.

**Alone on an ESP32-S3 this uses 77 % of a block at its default germanium
patch, 78 % at its costliest; use patch 8 `Fuzz - lean` (33 %) to stack.**

**The cause of the palette miss is not located**, and the shape
of it is the finding: the miss is **0.122 ms on the P4 and 0.116 ms on the
S3**, near enough the same absolute number on two chips that differ by 1.8×
in speed — CPU work does not do that. It is not the shaper's settings
either: the palette row's `pre_gain` 11.77 / `post_gain` 1.0 and this
class's 63.1 / 0.42 measure **0.0718 against 0.0691 ms/block** on desktop
MicroPython at ×8, order-balanced over six runs. `germanium` builds no
`Mixer` and no `Splitter` and hands back a 256-frame block, so the
block-length glue `Saturation` carries is not it either.

The first build of this class summed **2.447 / 4.318** over eight nodes -
three Butterworth high-passes where the pedal has three *first-order*
coupling caps, a 2-tap `Splitter` and a `Mixer` doing a dry/wet blend the
`Waveshaper` has a `mix` parameter for, and a `MidSide` tail whose only job
was to keep a `Mixer` off the end of the chain. Four of those eight are
gone. `cascade` keeps its splitter and a three-voice tone mixer, because its
dry leg has to reach the sum past a tone stack, and since the fourth fix
round it carries a sixth Biquad - the output coupling capacitor
(audiocomponents#89).

**`cascade` ships at `oversample=2`, and it used not to.** At ×8 the boards
read **4.782 / 8.580 ms — 90 % of a P4 block and 161 % of an S3 one, real
time factor 1.00 and 0.56**: it does not run on a T-Embed S3 at 48 kHz. The
docstring said to build it at ×2 and **nothing enforced it**, while
`create()` defaulted to 8 for both characters. `shipped_oversample()` picks
the factor now, ×8 on `germanium` and **×2 on `cascade`**, and a test holds
it. At ×2 the boards read **2.163 / 3.902 ms — 40.6 % / 73.2 %, rt 1.97 /
1.10** against a palette sum of 2×Splitter-2 0.414/0.736 + 6×Biquad
0.648/1.224 + 2×Waveshaper ×2 1.116/2.034 + Mixer 0.050/0.175 = **2.228 /
4.169 ms, 42 % / 78 %**: **inside on both boards**. ×4 is 3.250 / 5.971 ms,
**61 % / 112 %**, so it does not run on the S3 either and is not offered as
a default on any board. What ×2 costs is **2.9 / 5.3 dB of alias floor at
the default and 5.6 / 5.6 dB at maximum Fuzz** — see `CASCADE_OVERSAMPLE`,
which has the whole table. `oversample=` still takes any of 1, 2, 4, 8 for
anyone who wants the ×8 graph on a P4 and knows what it costs.

**What Mix does here, and what it gives up.** On `germanium` the dry/wet
blend is the `Waveshaper`'s own `mix`, so the dry leg is the signal *after*
the pedal's input coupling rather than the bare source: at 0 < Mix < 1 the
dry is down 0.51 dB at 100 Hz and 2.71 dB at 40 Hz. Output Tilt then rides
the blend rather than the wet alone. **Mix 0 is the borrowed source itself**,
not a path through the graph, so the wire invariant is exact by construction.

**Level and Load are the whole output, at every Mix.** They used to ride the
shaper's `post_gain`, which is the wet half of `out = (1-mix)*source +
mix*post_gain*shaped` - so Level 0 mutes only at Mix exactly 1, and at Mix
0.756 it still emitted −35.3 dBFS (audiocomponents#74, second audit). They
are now written as `mix' = 1 - trim*(1-mix)` with `post_gain' =
trim*mix*post_gain/mix'`, which is the same node scaled whole: **Level 0 is
digital silence at every Mix above 0, halving Level is −6.021 dB at every
Mix, and Load 1 is −6.021 dB at every Mix**. Mix 0 is the exception and it
is the wire invariant: at Mix 0 the output *is* the borrowed source, at the
source's own level, and nothing the class has scales it.

**Output Tilt is referenced to its loudest end**, and the number on the
macro is the difference across 1 kHz: at +6 dB the top of the band sits
where Tilt 0 left it and the bottom is 6 dB down. As a plain `HIGH_SHELF`
adding its boost on top, this stage **clipped at +3 dB and above at every
input level** (1035 pinned samples of 9600 at +6 dB, at −20 dBFS in as much
as at 0 dBFS). It clips nowhere **between 100 Hz and 3700 Hz**, which is the span that
sweep covered: the worst peak there is **30 185 of 32 767** (patch 2,
100 Hz, 0 dBFS in). **Below 100 Hz it does reach the rail**: at the
constructor default with Fuzz at maximum a steady 30 Hz sine at 0 dBFS
pins **10 samples of 6 400**, at −1 dBFS 8, and 40 Hz pins 2. The worst
shipped *patch* below 100 Hz is 32 144 (patch 4, 30 Hz, 0 dBFS), a
**0.16 dB** margin. A fuzz at maximum pinning its rail on a 30 Hz sine is
arguably the pedal, so what changes is the claim's span and not the class
(audit 3 (p)5).

**The tail, and where it does not end.** `TAIL_SAMPLES` is **24 576**
(0.512 s at 48 kHz) since the third fix round. 16 384 was a 1 kHz number
and a low note outlives it: after a −6 dBFS burst at **40 Hz** the output
is still not zero at 16 627 frames at the constructor default and **18 750
at patch 5**, and 100 Hz is over it at patches 1, 5 and 7 (audit 3 (p)1).
The declaration covers the worst of 40, 100, 220 and 1000 Hz at those four
settings at all three rates, and it is a −6 dBFS reading - the tail is
shorter at every quieter input. **With Bias off centre it never
reaches digital zero** - a wander of at most 16 LSB (−66.2 dBFS) stays,
because ±1 LSB at the input of a 36 dB gain stage is ±63 LSB at the
steepest part of the curve. Everything above 16 LSB is gone within **9 441**
frames (patch 2, 40 Hz). Patch 2 ships Bias −0.85 and has it.

**The output pole is charged before the first block.** S1's third
capacitor is the output one and its section is behind the shaper, but it
started cold: shipped patch 2 put **21 971 LSB, −3.5 dBFS**, out of
digital silence and took 0.2 s to bleed (audit 3 (p)2, ruling (n)).
`_charge_output` pulls the offset through the pole with the shapers fed
the class's own zero sample - the split is not pulled and no source frame
is consumed - so silence in is silence out at every shipped patch **within
the 16 LSB wander**, and a `program_change` onto silence peaks at 11 LSB
where it peaked at 21 971. It costs one block of input when Bias moves
live on `germanium`; **`cascade` is not re-charged live**, because its wet
leg comes off a `Splitter` and a re-point there would leave one tap a
block ahead of the other.

**`cascade` has its output coupling capacitor now** (audiocomponents#89,
ruling (n), fourth fix round). Without it the low arm of the tone stack is
a `LOW_PASS`, which passes DC, and there is nothing behind the second
clipper to block the clipper's own offset: Bias off centre held
**−16 383 to +16 382 LSB, −6.0 dBFS, on the output for ever**, at eight of
the nine stops of a front-panel macro, at every rate. A Big Muff has that
capacitor between the second clipper and the tone stack and this class now
does too, at 31 Hz - the pedal's own corner, and the one already in front
of that clipper. In the band it costs **1.268 dB at 40 Hz, 0.053 at 100
and 0.000 at 482 Hz and above**. Walked over 108 cells (3 rates × 2 characters × 9 Bias
stops × built-at-the-value and moved-to-it-live), the **settled mean is at
most 7.1 LSB and the peak at most 13**, both on `germanium`; `cascade`'s
worst is 6 LSB of each, inside the 16 LSB residual this class already
states. What it takes with it is C3's Bias clause and C4's Fuzz span,
both restated above; **C1 does not move** (h2 −79.059 → −79.379, peak
growth 0.012 → 0.013 dB).

**Latency.** Mix 1 at oversample 8 is the waveshaper group delay **3.9 samples
(0.083 ms at 48 kHz)**; this class reports **4**. Mix 0 reports **0**.
Oversample 4 reports **3** (3.3 samples, 0.069 ms); oversample 2 and patch 8
report **2** (2.2 samples, 0.046 ms); oversample 1 reports **0**. Named here
because the half-bands are the only lookahead. **`cascade` ships at ×2, so
it reports 2 where `germanium` reports 4** — `LATENCY_SAMPLES` is the class
constant for the shipped `germanium` default and `latency_samples` on the
instance is the one to read.

`capabilities = ()`: nothing reads `self._transport()`.
"""

VENDOR = "PyDevices"

from array import array

try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None
try:
    import audioshaper
except ImportError:
    audioshaper = None
try:
    import audioroute
except ImportError:
    audioroute = None

import audiocore
import audiomixer

from . import _component


# --- BEGIN GERMANIUM_CURVE ---
#: What full scale on `GERMANIUM_CURVE` stands for. The table is
#: normalised to the curve's own extreme so it fills int16
#: (audiocomponents#77) and this carries the scale back out in the
#: shaper's `post_gain`, so the class's level does not move.
GERMANIUM_SCALE = 0.632120559
GERMANIUM_CURVE = bytes.fromhex(
    "018026804c8071809780bc80e28008812d81538179819f81c581eb8112823882" +
    "5e828582ab82d282f9821f8346836d839483bb83e2830a84318458848084a784" +
    "cf84f7841e8546856e859685be85e6850f8637865f868886b086d98602872a87" +
    "53877c87a587ce87f88721884a8874889d88c788f0881a8944896e899889c289" +
    "ec89168a418a6b8a968ac08aeb8a168b408b6b8b968bc18bed8b188c438c6f8c" +
    "9a8cc68cf18c1d8d498d758da18dcd8df98d258e528e7e8eab8ed78e048f318f" +
    "5e8f8b8fb88fe58f12903f906d909a90c890f690239151917f91ad91db910a92" +
    "389266929592c392f292219350937f93ae93dd930c943b946b949a94ca94f994" +
    "299559958995b995e9951a964a967a96ab96db960c973d976e979f97d0970198" +
    "339864989598c798f9982a995c998e99c099f399259a579a8a9abc9aef9a229b" +
    "549b879bba9bee9b219c549c889cbb9cef9c239d579d8b9dbf9df39d279e5b9e" +
    "909ec49ef99e2e9f639f989fcd9f02a037a06da0a2a0d8a00ea143a179a1afa1" +
    "e6a11ca252a289a2bfa2f6a22da363a39aa3d2a309a440a477a4afa4e7a41ea5" +
    "56a58ea5c6a5ffa537a66fa6a8a6e0a619a752a78ba7c4a7fda736a870a8a9a8" +
    "e3a81da957a991a9cba905aa3faa7aaab4aaefaa2aab64ab9fabdbab16ac51ac" +
    "8dacc8ac04ad40ad7cadb8adf4ad30ae6caea9aee6ae22af5faf9cafd9af17b0" +
    "54b091b0cfb00db14ab188b1c6b105b243b281b2c0b2ffb23db37cb3bbb3fbb3" +
    "3ab479b4b9b4f9b438b578b5b8b5f8b539b679b6bab6fab63bb77cb7bdb7feb7" +
    "40b881b8c3b804b946b988b9cab90cba4fba91bad4ba16bb59bb9cbbdfbb23bc" +
    "66bcaabcedbc31bd75bdb9bdfdbd41be86becabe0fbf54bf99bfdebf23c069c0" +
    "aec0f4c03ac17fc1c6c10cc252c299c2dfc226c36dc3b4c3fbc342c48ac4d1c4" +
    "19c561c5a9c5f1c539c682c6cac613c75cc7a5c7eec737c881c8cac814c95ec9" +
    "a8c9f2c93cca87cad1ca1ccb67cbb2cbfdcb48cc94ccdfcc2bcd77cdc3cd0fce" +
    "5ccea8cef5ce42cf8fcfdccf29d076d0c4d012d15fd1add1fcd14ad298d2e7d2" +
    "36d385d3d4d323d472d4c2d412d562d5b2d502d652d6a2d6f3d644d795d7e6d7" +
    "37d889d8dad82cd97ed9d0d922da75dac7da1adb6ddbc0db13dc66dcbadc0edd" +
    "61ddb5dd0ade5edeb2de07df5cdfb1df06e05ce0b1e007e15de1b3e109e25fe2" +
    "b6e20ce363e3bae311e469e4c0e418e570e5c8e520e678e6d1e62ae783e7dce7" +
    "35e88ee8e8e842e99ce9f6e950eaabea05eb60ebbbeb16ec72eccdec29ed85ed" +
    "e1ed3dee9aeef7ee53efb0ef0ef06bf0c8f026f184f1e2f140f29ff2fef25cf3" +
    "bbf31bf47af4daf439f599f5f9f55af6baf61bf77cf7ddf73ef8a0f801f963f9" +
    "c5f927fa8afaecfa4ffbb2fb15fc79fcdcfc40fda4fd08fe6dfed1fe36ff9bff" +
    "00006500cb0031019701fd016302ca0230039703fe036604cd0435059d050506" +
    "6d06d6063f07a80711087a08e4084e09b809220a8c0af70a620bcd0b380ca40c" +
    "0f0d7b0de70d530ec00e2d0f9a0f07107410e2104f11be112c129a1209137813" +
    "e7135614c6143515a51515168616f6166717d8174a18bb182d199f19111a831a" +
    "f61a691bdc1b4f1cc31c361daa1d1f1e931e081f7c1ff21f6720dc205221c821" +
    "3f22b5222c23a3231a24912409258125f9257126ea266327dc275528cf284829" +
    "c2293d2ab72a322bad2bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82bc82b" +
    "c82b"
)
# --- END GERMANIUM_CURVE ---

# --- BEGIN CASCADE_CURVE ---
CASCADE_CURVE = bytes.fromhex(
    "01800f801e802c803b80498058806780758084809380a280b080bf80ce80dd80" +
    "ec80fb800a81198128813781468156816581748184819381a281b281c181d181" +
    "e081f08100820f821f822f823f824f825f826f827f828f829f82af82bf82cf82" +
    "df82f0820083108321833183428352836383748384839583a683b783c883d883" +
    "e983fa830c841d842e843f8450846284738484849684a784b984cb84dc84ee84" +
    "0085128523853585478559856b857e859085a285b485c785d985ec85fe851186" +
    "2386368649865c866e8681869486a786ba86ce86e186f48608871b872e874287" +
    "568769877d879187a587b887cc87e087f58709881d88318846885a886f888388" +
    "9888ac88c188d688eb88008915892a893f8955896a897f899589ab89c089d689" +
    "ec89028a188a2e8a448a5a8a708a878a9d8ab38aca8ae18af88a0e8b258b3c8b" +
    "538b6b8b828b998bb18bc88be08bf78b0f8c278c3f8c578c6f8c888ca08cb88c" +
    "d18cea8c028d1b8d348d4d8d668d7f8d998db28dcc8de58dff8d198e338e4d8e" +
    "678e818e9c8eb68ed18eec8e068f218f3c8f588f738f8e8faa8fc58fe18ffd8f" +
    "1990359051906e908a90a790c490e190fe901b913891559173919191ae91cc91" +
    "ea9109922792469264928392a292c192e09200931f933f935f937f939f93bf93" +
    "e09300942194429463948594a694c894ea940c952e95509573959595b895db95" +
    "fe952296469669968d96b296d696fb961f9744976a978f97b597db9701982798" +
    "4d9874989b98c298e9981199399961998999b299db99049a2d9a569a809aaa9a" +
    "d59aff9a2a9b559b809bac9bd89b049c309c5d9c8a9cb79ce59c139d419d709d" +
    "9e9dcd9dfd9d2d9e5d9e8d9ebe9eef9e209f529f849fb69fe99f1ca050a083a0" +
    "b8a0eca021a157a18ca1c2a1f9a130a267a29fa2d7a210a349a382a3bca3f6a3" +
    "31a46ca4a8a4e4a421a55ea59ba5daa518a657a697a6d7a618a759a79aa7dda7" +
    "1fa863a8a7a8eba830a976a9bca903aa4baa93aadbaa25ab6fabb9ab05ac51ac" +
    "9dacebac39ad88add7ad27ae78aecaae1caf70afc4af18b06eb0c4b01cb174b1" +
    "ccb126b281b2dcb238b396b3f4b353b4b3b413b575b5d8b53cb6a0b606b76db7" +
    "d4b73db8a7b812b97db9eab958bac7ba37bba9bb1bbc8fbc03bd79bdf0bd68be" +
    "e1be5cbfd7bf54c0d2c052c1d2c154c2d7c25bc3e0c367c4efc478c502c68ec6" +
    "1bc7a9c739c8cac85cc9efc984ca1acbb1cb49cce3cc7ecd1aceb7ce56cff6cf" +
    "97d039d1ddd182d228d3cfd377d420d5cbd577d623d7d1d780d830d9e1d994da" +
    "47dbfbdbb0dc66dd1dded5de8edf48e002e1bee17ae237e3f5e3b4e473e533e6" +
    "f4e6b6e778e83be9fee9c2ea87eb4cec12edd8ed9eee65ef2df0f5f0bdf186f2" +
    "4ff319f4e2f4acf577f641f70cf8d7f8a2f96efa39fb05fcd1fc9cfd68fe34ff" +
    "0000cc00980164022f03fb03c70492055e062907f407bf088909540a1e0be70b" +
    "b10c7a0d430e0b0fd30f9b1062112812ee12b41379143e150216c51688174a18" +
    "0c19cd198d1a4c1b0b1cc91c861d421efe1eb81f72202b21e3219a2250230524" +
    "b9246c251f26d02680272f28dd288929352ae02a892b312cd82c7e2d232ec72e" +
    "692f0a30aa304931e63182321d33b7334f34e6347c351136a4363637c7375738" +
    "e5387239fe39883a113b993b203ca53c293dac3d2e3eae3e2e3fac3f2940a440" +
    "1f41984110428742fd427143e5435744c9443945a84516468346ee465947c347" +
    "2c489348fa486049c449284a8b4aed4a4d4bad4b0c4c6a4cc84c244d7f4dda4d" +
    "344e8c4ee44e3c4f924fe84f3c509050e45036518851d95129527852c7521553" +
    "6353af53fb5347549154db5425556d55b555fd5544568a56d056155759579d57" +
    "e15723586658a758e85829596959a959e859265a655aa25adf5a1c5b585b945b" +
    "cf5b0a5c445c7e5cb75cf05c295d615d995dd05d075e3e5e745ea95edf5e145f" +
    "485f7d5fb05fe45f17604a607c60ae60e060116142617361a361d36103623362" +
    "62629062bf62ed621b6349637663a363d063fc63286454648064ab64d6640165" +
    "2b6556658065aa65d365fc6525664e6677669f66c766ef6617673e6765678c67" +
    "b367d967ff6725684b6871689668bc68e16805692a694e6973699769ba69de69" +
    "026a256a486a6b6a8d6ab06ad26af46a166b386b5a6b7b6b9d6bbe6bdf6b006c" +
    "206c416c616c816ca16cc16ce16c006d206d3f6d5e6d7d6d9c6dba6dd96df76d" +
    "166e346e526e6f6e8d6eab6ec86ee56e026f1f6f3c6f596f766f926faf6fcb6f" +
    "e76f03701f703b70567072708d70a870c470df70fa7014712f714a7164717f71" +
    "9971b371cd71e77101721b7234724e72677281729a72b372cc72e572fe721673" +
    "2f734873607378739173a973c173d973f1730974207438744f7467747e749574" +
    "ad74c474db74f27408751f7536754d75637579759075a675bc75d275e875fe75" +
    "14762a76407655766b7681769676ab76c176d676eb76007715772a773f775477" +
    "68777d779177a677ba77cf77e377f7770b782078347848785b786f7883789778" +
    "aa78be78d278e578f8780c791f793279467959796c797f799279a479b779ca79" +
    "dd79ef79027a147a277a397a4c7a5e7a707a827a957aa77ab97acb7add7aee7a" +
    "007b127b247b357b477b597b6a7b7c7b8d7b9e7bb07bc17bd27be37bf47b067c" +
    "177c287c387c497c5a7c6b7c7c7c8c7c9d7cae7cbe7ccf7cdf7cf07c007d107d" +
    "217d317d417d517d617d717d817d917da17db17dc17dd17de17df17d007e107e" +
    "207e2f7e3f7e4e7e5e7e6d7e7c7e8c7e9b7eaa7eba7ec97ed87ee77ef67e057f" +
    "147f237f327f417f507f5e7f6d7f7c7f8b7f997fa87fb77fc57fd47fe27ff17f" +
    "ff7f"
)
# --- END CASCADE_CURVE ---

#: The three coupling caps S1 names, in Hz. Each is **one** real pole in the
#: circuit, and a biquad holds two, so the germanium input section is two
#: nodes rather than the three Butterworth sections this class first shipped
#: - which were sixth order where the pedal is third, and cost a node for it.
HP_HZ = (14.0, 7.9, 31.0)

#: The pair (7.9, 14) and the pair (31, PARK) as `HIGH_PASS` biquads. Two
#: real poles at f1 and f2 under a double zero at DC are exactly two cascaded
#: first-order high-passes: f0 = sqrt(f1 f2), Q = f0 / (f1 + f2). Literals,
#: not `math.sqrt` at import: a filter setting derived in Python float
#: differs between a board and a desktop (audiocomponents#75), and a literal
#: parses the same on both.
#:
#: `HP_PARK_HZ` is the spare pole of the output section. It goes **below** the
#: band, not above it: a high-pass's second zero already sits at DC, so a
#: parked pole above the corner would tilt the whole band at 6 dB/octave.
#:
#: **Where below the band matters, because this section is what carries the
#: clipper's offset out.** With zero in, the germanium curve still puts a
#: constant at the shaper's output, and this section is the only thing that
#: removes it. A step into a double-zero pair of poles `a < b` leaves a slow
#: term of amplitude `a/(b-a)` decaying at `1/a`: parked at 1 Hz that is
#: 3.3 % of the offset decaying over 159 ms, and the output was still moving
#: **0.80 s** after a burst stopped. At 5 Hz it is 19 % decaying over 32 ms -
#: louder at once, gone sooner - and it costs **0.068 dB at 40 Hz** and
#: 0.011 dB at 100 Hz, where the first-order 31 Hz pole above it already
#: costs 2.04 dB and 0.44 dB.
HP_PARK_HZ = 5.0
#: How many blocks `_charge_output` will pull before it gives up, and how
#: long the zero sample it pulls through is. The germanium output pole is
#: 12.45 Hz, so its charge is about 0.15 s: 32 blocks of 512 frames is
#: 16384, which covers it at every rate. The shaper's native `play()` takes
#: no `loop`, so the sample is a block long and is re-played each pull.
CHARGE_BLOCKS = 32
CHARGE_FRAMES = 512

#: `cascade`'s output coupling capacitor, **in the graph since the fourth
#: fix round** (audiocomponents#89). A Big Muff has one between the second
#: clipper and the tone stack; this class had none at all, and the low arm
#: of the tone stack is a LOW_PASS, which passes DC. With Bias off centre
#: the class stood **-16 383 to +16 382 LSB (-6.0 dBFS) on the output for
#: ever**, at eight of the nine stops of the Bias macro, at every rate.
#: 31 Hz is the pedal's own corner and the one already in front of the
#: second clipper. Measured against the class without it, on the wet
#: branch at Tone 0.5: **1.268 dB at 40 Hz, 0.295 at 60, 0.053 at 100,
#: 0.006 at 200 and 0.000 at 482 Hz and above** - the same shape `hp_mid`
#: already imposes one stage earlier.
CASCADE_OUT_HP_HZ = 31.0

HP_A_HZ = 10.516653          # sqrt(7.9 * 14)
HP_A_Q = 0.480212            # 10.516653 / 21.9
HP_B_HZ = 12.4498996         # sqrt(31 * 5)
HP_B_Q = 0.34583054          # 12.4498996 / 36.0

TILT_HZ = 1000.0
TONE_LP_HZ = 482.0
TONE_HP_HZ = 1206.0
BUTTER_Q = 0.7071067811865475
CHARACTERS = ("germanium", "cascade")
OVERSAMPLES = (1, 2, 4, 8)

#: Patch 8, `Fuzz - lean`. The factor is fixed at construction - the node
#: cannot retune its half-bands live - so the lean position is a **second
#: shaper** at `LEAN_OVERSAMPLE`, built beside the shipped one and played by
#: the tilt stage when this patch is selected. Only the routed shaper is ever
#: pulled; the other one costs its 5696 B of RAM and no time at all.
LEAN_PATCH = 8
LEAN_OVERSAMPLE = 2

#: The factor each character ships at, and the reason it is not one number.
#:
#: `germanium` is one clipper: ×8 prices at 2.257 / 3.980 ms and the boards
#: measured 2.379 / 4.096 — **rt 1.81 on the P4 and 1.05 on the S3**, which
#: clears. `cascade` is two clippers behind a tone stack, and at ×8 the same
#: boards read **4.782 / 8.580 ms — 90 % of a P4 block and 161 % of an S3
#: one, rt 1.00 and 0.56** (audiocomponents#74). It does not run. The
#: docstring said so before this round and nothing enforced it: `oversample`
#: is a constructor option a user reaches, `create()` defaulted to 8 for
#: both characters, and a default that cannot make the deadline on a board
#: this library ships for is not a default.
#:
#: **×2, and it costs floor — said out loud.** Cascade's alias floor,
#: 48 kHz, −6 dBFS, wet branch, A4's own rule, measured for the first time
#: this round (`probes/fuzz_fix5.py`), at 1010 / 3700 Hz:
#:
#:     Fuzz default  ×1 −18.315/−13.407  ×2 −27.372/−21.343
#:                   ×4 −30.123/−24.946  ×8 −30.232/−26.595
#:     Fuzz maximum  ×1 −17.537/−13.283  ×2 −24.237/−20.397
#:                   ×4 −28.491/−23.897  ×8 −29.847/−25.982
#:
#: So ×2 gives up **2.9 / 5.3 dB at the default and 5.6 / 5.6 dB at maximum
#: Fuzz** against ×8. ×4 would give almost all of it back (within 0.1 / 1.6
#: at the default, 1.4 / 2.1 at maximum) and **it does not run either**:
#: 3.250 / 5.971 ms by the palette, **61 % of a P4 block and 112 % of an S3
#: one**. ×2 is the only factor that makes the deadline on both boards.
#:
#: Oversampling buys cascade much less than it buys germanium in the first
#: place — ×8 over ×1 is **12.3 / 12.7 dB** here against germanium's
#: 20.9 / 18.7 — because the second clipper folds harmonics the first one
#: already put above the *output* Nyquist, which no internal rate reaches.
#: **Cascade is outside A4's span at every factor** (A4 is a germanium row:
#: nothing in its sweep passes `character=`, and at ×8 cascade reads −29.8 /
#: −26.0 against A4's surface bars of 35 / 28 dB). That is disclosed here,
#: in the class docstring, in the catalogue row and in the pack, in the same
#: words.
GERMANIUM_OVERSAMPLE = 8
CASCADE_OVERSAMPLE = 2

#: The tone mixer's buffer, per channel. `Mixer._render_size` is
#: `buffer_size // 2 // 4 * 4` BYTES, so the 1024 `cascade` shipped rendered
#: **128 stereo frames** and the tilt stage behind it pulled the three-voice
#: mixer, both tone arms and the dry tap **twice** per 256-frame block —
#: the palette's block, and the unit every audiodsp node works in.
#: `1024 * channel_count` is one pull per block at either channel count,
#: which is what `Distortion` already does (`_pcm_mixer`).
MIXER_BUFFER_BYTES = 1024


def shipped_oversample(character):
    """The factor this character ships at: ×8 on `germanium`, ×2 on
    `cascade`. Chosen on cascade's own alias floor — see
    `CASCADE_OVERSAMPLE`, which has the numbers — and not on the maximum
    the node offers."""
    if character == "cascade":
        return CASCADE_OVERSAMPLE
    return GERMANIUM_OVERSAMPLE

_RANGES = (
    (18.0, 54.0),          # 0 Fuzz, dB of pre_gain
    (0.0, 1.0),            # 1 Level
    (0.0, 1.0),            # 2 Tone
    (-1.0, 1.0),           # 3 Bias
    (0.0, 1.0),            # 4 Load
    (0.0, 1.0),            # 5 Mix
    (-6.0, 6.0),           # 6 Output Tilt, dB
)


#: Each macro's public mode, in index order, written out beside `_RANGES`
#: because `macro_of` needs it: a BIPOLAR macro's MIDI law has a centre
#: detent at 64 and a UNIPOLAR one does not (audiocomponents#87), so a patch
#: authored without the mode lands beside its engineering value. It is the
#: same list as `MACRO_MODES` below, which stays written out as a literal
#: for the hosts that read it out of the source; the shared contract test
#: holds the two in step.
_MODES = ("UNIPOLAR", "UNIPOLAR", "UNIPOLAR", "BIPOLAR",
          "UNIPOLAR", "UNIPOLAR", "BIPOLAR")


def _patch(*engineering):
    return tuple(_component.macro_of(span, value, mode)
                 for span, mode, value in zip(_RANGES, _MODES, engineering))


# audiodsp CPython binding documents these; the native MP/CP modules do not
# export the dict. Same numbers as audioshaper.GROUP_DELAY_SAMPLES.
_GROUP_DELAY_SAMPLES = {1: 0.0, 2: 2.2, 4: 3.3, 8: 3.9}


def _q15_array(blob):
    """int16 Q15 table. CPython has `array.frombytes`; MicroPython 1.29 does not."""
    out = array("h")
    frombytes = getattr(out, "frombytes", None)
    if frombytes is not None:
        frombytes(blob)
        return out
    for index in range(0, len(blob), 2):
        value = blob[index] | (blob[index + 1] << 8)
        if value >= 32768:
            value -= 65536
        out.append(value)
    return out


def _group_delay_samples(oversample):
    delay = _GROUP_DELAY_SAMPLES[int(oversample)]
    return int(round(delay))


class Fuzz(_component.Component):
    """Fuzz Face germanium, or a Ram's Head 1973 Big Muff as `cascade`."""

    NAME = 'Fuzz'
    DISPLAY_NAME = 'Fuzz'
    CATEGORIES = ('Distortion',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioshaper", "audiobiquad", "audioroute")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 4
    #: Measured, not inherited, and **re-measured at 40 Hz by the third
    #: fix round**: 16 384 was a 1 kHz number and a low note outlives it -
    #: 16 627 frames at the constructor default, **18 750 at patch 5**, and
    #: 100 Hz is over it at patches 1, 5 and 7 (audit 3 (p)1). This covers
    #: the worst of 40, 100, 220 and 1000 Hz at the default and at patches
    #: 1, 5 and 7, at all three rates, after a -6 dBFS burst. What it does
    #: **not** cover is said in the docstring: with Bias off centre the
    #: class never reaches digital zero, and that wander is bounded at
    #: 16 LSB.
    TAIL_SAMPLES = 24576

    MACRO_LABELS = ("Fuzz", "Level", "Tone", "Bias", "Load", "Mix",
                    "Output Tilt")
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "BIPOLAR",
        4: "UNIPOLAR", 5: "UNIPOLAR", 6: "BIPOLAR",
    }
    _MACRO_RANGES = _RANGES
    PATCHES = {
        0: ("Bias centred, fuzz half",
            _patch(36.0, 1.0, 0.5, 0.0, 0.0, 1.0, 0.0)),
        1: ("Full fuzz, volume back",
            _patch(54.0, 0.4, 0.5, 0.0, 0.0, 1.0, 0.0)),
        2: ("Starved bias, gated",
            _patch(42.0, 1.0, 0.5, -0.85, 0.0, 1.0, 0.0)),
        3: ("Cleaned up, load engaged",
            _patch(24.0, 1.0, 0.5, 0.0, 1.0, 1.0, 0.0)),
        4: ("Cascade scoop centred",
            _patch(48.0, 1.0, 0.5, 0.0, 0.0, 1.0, 0.0)),
        5: ("Cascade sustain maximum",
            _patch(54.0, 0.8, 0.5, 0.0, 0.0, 1.0, 0.0)),
        6: ("Cascade treble end",
            _patch(48.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0)),
        7: ("Full fuzz, mix back",
            _patch(54.0, 1.0, 0.5, 0.0, 0.0, 0.35, 0.0)),
        LEAN_PATCH: ("Fuzz - lean",
                     _patch(36.0, 1.0, 0.5, 0.0, 0.0, 1.0, 0.0)),
    }

    def _build(self, fuzz_db=36.0, level=1.0, tone=0.5, bias=0.0,
               load=0.0, mix=1.0, tilt_db=0.0, character="germanium",
               oversample=None, patch=None):
        rate = self._sample_rate
        channels = self._channel_count
        if character not in CHARACTERS:
            raise ValueError("character must be 'germanium' or 'cascade'")
        if oversample is None:
            oversample = shipped_oversample(character)
        oversample = int(oversample)
        if oversample not in OVERSAMPLES:
            raise ValueError("oversample must be 1, 2, 4 or 8")
        self._character = character
        self._oversample = oversample
        self._quiet = self._own(audiocore.RawSample(
            array("h", bytes(2 * CHARGE_FRAMES * channels)),
            sample_rate=rate, channel_count=channels), reset=False)
        self._charged_bias = None
        self._charge_tap = None
        #: `[(shaper, its real source)]` - what `_charge_output` re-points
        #: at the zero sample and puts back. On `cascade` only the first
        #: clipper is on this list: the second takes `hp_mid`, and handing
        #: it `hp_in` instead wires the two stages in parallel.
        self._charge_wiring = []
        self._lean_oversample = min(oversample, LEAN_OVERSAMPLE)
        self._wet_delay = _group_delay_samples(oversample)
        self._latency = self._wet_delay if mix > 0.0 else 0
        self._routed_lean = False
        self._ready = False

        # The class keeps a reference to the table it loaded. `Waveshaper`
        # takes a curve and never gives it back, so without this the only
        # way to ask which table a built instance is playing is to render it
        # - and a gate check that cannot ask ends up reading a literal keyed
        # on the class's type instead, which is what audiocomponents#74's
        # second audit found. No macro moves it.
        curve_h = _q15_array(
            GERMANIUM_CURVE if character == "germanium" else CASCADE_CURVE)
        self._curve = curve_h
        self._hps = []
        self._lean = None
        self._split = None
        self._dry = None
        self._silence = None
        self._cascade_out_hp = None
        self._tone_split = None
        self._tone_lp = None
        self._tone_hp = None
        self._tone_mix = None

        if character == "germanium":
            # Three coupling caps, three real poles, **two** biquads - and
            # the third cap is the **output** one, so its section goes after
            # the shaper, where S1 puts it (dossier line 147:
            # `HP14 - HP7.9 - Waveshaper(Ge) - HP31 - Tilt`). Each section is
            # `HIGH_PASS` at a geometric-mean corner with two real poles
            # under it, which is exactly what cascading first-order sections
            # does. The class first shipped three Butterworth sections here,
            # sixth order against the pedal's third, and paid a node for the
            # difference; the fix round then folded all three poles in front
            # of the shaper, which left **nothing blocking the clipper's own
            # offset** (audiocomponents#74, second audit).
            hp_a = self._own(audiobiquad.Biquad(
                mode=audiobiquad.HIGH_PASS, frequency=self._hz(HP_A_HZ),
                Q=HP_A_Q, sample_rate=rate, channel_count=channels))
            hp_a.play(self._source)
            hp_b = self._own(audiobiquad.Biquad(
                mode=audiobiquad.HIGH_PASS, frequency=self._hz(HP_B_HZ),
                Q=HP_B_Q, sample_rate=rate, channel_count=channels))
            self._hps = [hp_a, hp_b]

            # `GERMANIUM_SCALE` is a constant factor of `post_gain`: the
            # table holds a shape normalised to its own extreme so it fills
            # int16 (audiocomponents#77), and this puts the collector volts
            # back. Level, Load and Mix ride the node's own `post_gain` and
            # `mix`, so the whole dry/wet blend costs no node at all.
            shaper = self._own(audioshaper.Waveshaper(
                sample_rate=rate, channel_count=channels,
                curve=curve_h, oversample=oversample,
                pre_gain=1.0, post_gain=GERMANIUM_SCALE, mix=1.0, bias=0.0))
            # Wired to `_quiet` until `_charge_output` has run: a `play()`
            # takes a block from what it is handed, so pointing the shaper
            # at `hp_a` once the pole is charged costs the caller nothing,
            # and doing it the other way round throws a block of the source
            # away (`AConstructorPatchCostsTheSourceNothing`).
            shaper.play(self._quiet)
            self._charge_wiring.append((shaper, hp_a))
            self._shapers = [shaper]
            if self._lean_oversample < oversample:
                self._lean = self._own(audioshaper.Waveshaper(
                    sample_rate=rate, channel_count=channels,
                    curve=curve_h, oversample=self._lean_oversample,
                    pre_gain=1.0, post_gain=GERMANIUM_SCALE, mix=1.0,
                    bias=0.0))
                self._lean.play(self._quiet)
                self._charge_wiring.append((self._lean, hp_a))
                self._shapers.append(self._lean)
            hp_b.play(shaper)
            self._charge_tap = hp_b
            head = hp_b
        else:
            # `cascade` keeps its input splitter, because its dry leg has to
            # reach the sum *past* a tone stack the wet legs go through.
            self._split = self._own(
                audioroute.Splitter(source=self._source, taps=2), reset=False)
            self._dry = self._own(self._split.tap(0), reset=False)
            wet_in = self._own(self._split.tap(1), reset=False)
            hp_in = self._own(audiobiquad.Biquad(
                mode=audiobiquad.HIGH_PASS, frequency=self._hz(14.0),
                Q=BUTTER_Q, sample_rate=rate, channel_count=channels))
            hp_in.play(wet_in)
            self._hps.append(hp_in)
            shaper1 = self._own(audioshaper.Waveshaper(
                sample_rate=rate, channel_count=channels,
                curve=curve_h, oversample=oversample,
                pre_gain=1.0, post_gain=1.0, mix=1.0, bias=0.0))
            shaper1.play(self._quiet)
            self._charge_wiring.append((shaper1, hp_in))
            hp_mid = self._own(audiobiquad.Biquad(
                mode=audiobiquad.HIGH_PASS, frequency=self._hz(31.0),
                Q=BUTTER_Q, sample_rate=rate, channel_count=channels))
            hp_mid.play(shaper1)
            self._hps.append(hp_mid)
            shaper2 = self._own(audioshaper.Waveshaper(
                sample_rate=rate, channel_count=channels,
                curve=curve_h, oversample=oversample,
                pre_gain=1.0, post_gain=1.0, mix=1.0, bias=0.0))
            shaper2.play(hp_mid)
            self._shapers = [shaper1, shaper2]
            # **The output coupling capacitor**, fourth fix round
            # (audiocomponents#89). A Big Muff has one between Q4's
            # collector and the tone stack; this class had none at all
            # behind the second clipper, and the low arm of the tone stack
            # is a LOW_PASS, which passes DC. Without it a Bias off centre
            # stood **-16 383 to +16 382 LSB (-6.0 dBFS) on the output for
            # ever**, at eight of nine stops of a front-panel macro, at
            # every rate. 31 Hz is the pedal's own corner and the one
            # already in front of the second clipper. It costs one Biquad
            # on `cascade` and **0.011 dB at 100 Hz**; what it takes with
            # it is C3's and C4's Bias clauses, restated below and in the
            # pack.
            self._cascade_out_hp = self._own(audiobiquad.Biquad(
                mode=audiobiquad.HIGH_PASS,
                frequency=self._hz(CASCADE_OUT_HP_HZ),
                Q=BUTTER_Q, sample_rate=rate, channel_count=channels))
            self._cascade_out_hp.play(shaper2)
            self._hps.append(self._cascade_out_hp)
            self._charge_tap = self._cascade_out_hp
            self._tone_split = self._own(
                audioroute.Splitter(source=self._cascade_out_hp, taps=2),
                reset=False)
            tap_lp = self._own(self._tone_split.tap(0), reset=False)
            tap_hp = self._own(self._tone_split.tap(1), reset=False)
            self._tone_lp = self._own(audiobiquad.Biquad(
                mode=audiobiquad.LOW_PASS, frequency=self._hz(TONE_LP_HZ),
                Q=BUTTER_Q, sample_rate=rate, channel_count=channels))
            self._tone_lp.play(tap_lp)
            self._tone_hp = self._own(audiobiquad.Biquad(
                mode=audiobiquad.HIGH_PASS, frequency=self._hz(TONE_HP_HZ),
                Q=BUTTER_Q, sample_rate=rate, channel_count=channels))
            self._tone_hp.play(tap_hp)
            # Three voices, one summing point: the two tone arms and the dry
            # leg. The separate Mix mixer and the `MidSide` tail behind it
            # are gone - the tilt stage is the last node either way, so the
            # tail's only reason ("never end on a Mixer") went with them.
            self._tone_mix = self._own(
                audiomixer.Mixer(voice_count=3,
                                 **self._pcm(MIXER_BUFFER_BYTES * channels)),
                reset=self._reset_mixers)
            self._silence = self._own(audiocore.RawSample(
                array("h", [0] * (2 * channels)),
                sample_rate=rate, channel_count=channels), reset=False)
            head = self._tone_mix

        self._tilt = self._own(audiobiquad.Biquad(
            mode=audiobiquad.HIGH_SHELF, frequency=self._hz(TILT_HZ),
            Q=BUTTER_Q, gain_db=0.0, sample_rate=rate,
            channel_count=channels))
        self._tilt.play(head)
        self._output = self._tilt

        # Macros write every mixer level before any voice takes a source,
        # then the gates open at those levels (audiocomponents#66).
        self._init_macros((fuzz_db, level, tone, bias, load, mix, tilt_db),
                          patch)
        self._charge_output()
        for node, source in self._charge_wiring:
            node.play(source)
        if self._tone_mix is not None:
            _component.open_level_gates(
                self._tone_mix,
                [self._tone_mix.voice[0], self._tone_mix.voice[1],
                 self._tone_mix.voice[2]],
                self._silence)
            self._tone_mix.voice[0].play(self._tone_lp)
            self._tone_mix.voice[1].play(self._tone_hp)
            self._tone_mix.voice[2].play(self._dry)
        self._ready = True
        self._route()
        self._refresh()

    def _charge_output(self, rewire=False):
        """Settle the output pole on the offset before the first block.

        Bias is an offset into an asymmetric curve, so the shaper answers a
        silent input with a constant: shipped patch 2 (Bias -0.844) put
        **21 971 LSB, -3.5 dBFS**, out of digital silence and took 0.2 s to
        bleed through the output pole (audit 3 (p)2, ruling (n)). The pole
        was there; it started cold. This pulls the offset through it with
        the shapers fed the class's own zero sample - **the split is not
        pulled and no source frame is consumed** - and stops as soon as a
        whole block comes back zero.

        At a build the shapers are left on that zero sample and `_build`
        points them at the real chain afterwards, once, which is the
        `play()` the caller was always paying for. A **live** Bias move
        re-charges with `rewire=True` - a `program_change` onto silence
        banged 21 971 LSB without it.

        **`cascade` is re-charged live too, since the fourth fix round, and
        it costs nothing.** The third round left it out on the grounds that
        re-pointing `shaper1` would leave one tap of the input `Splitter` a
        block ahead of the other for the rest of the render. Measured, it
        does not: the charge pulls the **output pole**, and above it only
        `shaper1` is re-pointed, onto `self._quiet` - `hp_in` is never
        pulled, so neither tap of the input split moves. A 1 kHz burst
        behind a live Bias move arrives at the same output frame with the
        move as without it (`probes/fuzz_fix4.py align`), and a block
        pulled off `self._dry` to "rebalance" is what puts the dry leg 256
        frames **early**, which is how this was measured in the first
        place.

        On a build with no `audiocore.get_buffer` - CircuitPython's default
        board build compiles it out - this does nothing and the bang is
        back.
        """
        pull = getattr(audiocore, "get_buffer", None)
        if pull is None or self._charge_tap is None:
            return False
        self._charged_bias = self._value(3)
        for index in range(CHARGE_BLOCKS):
            for node, _source in self._charge_wiring:
                node.play(self._quiet)
            _state, data = pull(self._charge_tap)
            if not data:
                break
            # The first block back is what the pole was holding before the
            # shapers were re-pointed, so it says nothing about this offset.
            if index and not any(array("h", bytes(data))):
                break
        if rewire:
            for node, source in self._charge_wiring:
                node.play(source)
        return True

    def _reset_mixers(self):
        audiocore.reset_buffer(self._tone_mix)
        self._tone_mix.voice[0].play(self._tone_lp)
        self._tone_mix.voice[1].play(self._tone_hp)
        self._tone_mix.voice[2].play(self._dry)

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _apply_macro(self, index, position):
        del index, position
        self._refresh()

    def _refresh(self):
        """Every macro, pushed at once.

        On `germanium` there is no summing node to push to: the shaper's own
        `mix` is the dry/wet blend and its `post_gain` carries Level and
        Load, so Mix, Level, Load, Fuzz and Bias are five numbers written to
        one node. On `cascade` the same five land on the two shapers and the
        three voices of the tone mixer.
        """
        fuzz_gain = _component.db_to_gain(self._value(0))
        tone = self._value(2)
        bias = self._value(3)
        mix = self._value(5)
        # **Output Tilt is referenced to its loudest end.** The macro's
        # number is the difference across 1 kHz, and the boost half of it is
        # taken out of the whole output rather than added on top: at +6 dB
        # the top of the band sits where Tilt 0 left it and the bottom is
        # 6 dB down. A one-sided `HIGH_SHELF` added it to an output that
        # already peaks at 0.79 FS, and the stage **clipped at +3 dB and
        # above at every input level** - 1035 pinned samples of 9600 at
        # +6 dB, at -20 dBFS in as much as at 0 dBFS (audiocomponents#74,
        # this round; the shape the second audit parked `CabinetSim` for).
        # This is the same tone control, it costs no node, and the peak can
        # no longer exceed the one Tilt 0 has.
        tilt_db = self._value(6)
        self._tilt.gain_db = tilt_db
        trim = (self._value(1) * (1.0 - 0.5 * self._value(4))
                * _component.db_to_gain(-max(tilt_db, 0.0)))
        if self._tone_mix is None:
            # The node's own law is
            # `out = (1-mix)*source + mix*post_gain*shaped`
            # (`audiodsp/src/shared/audiodsp_shaper.c:253`), so a trim written
            # to `post_gain` alone scales the wet half and **leaves the dry
            # half at full level** - Level 0 went on emitting at every Mix
            # below 1 (audiocomponents#74, second audit). The Volume pot is
            # after the blend in S1, so the whole output carries it. One
            # substitution puts it there and still costs no node:
            #   mix'       = 1 - trim*(1-mix)
            #   post_gain' = trim*mix*post_gain / mix'
            # gives `out = trim*[(1-mix)*source + mix*post_gain*shaped]`
            # exactly. At the shipped default (trim 1, Mix 1) it is the
            # identity, and at trim 0 it is mix' 1 with post_gain 0: silence.
            wet_mix = 1.0 - trim * (1.0 - mix)
            post = ((trim * mix * GERMANIUM_SCALE / wet_mix)
                    if wet_mix > 0.0 else 0.0)
            for shaper in self._shapers:
                shaper.set(pre_gain=fuzz_gain, bias=bias, mix=wet_mix,
                           post_gain=post)
            if self._ready and bias != self._charged_bias:
                self._charge_output(rewire=True)
        else:
            # cascade: Sustain is the level into the first clipper only, and
            # the dry voice carries Level and Load with the wet ones.
            self._shapers[0].set(pre_gain=fuzz_gain, bias=bias)
            self._shapers[1].set(bias=bias)
            wet = mix * trim
            self._tone_mix.voice[0].level = wet * (1.0 - tone)
            self._tone_mix.voice[1].level = wet * tone
            self._tone_mix.voice[2].level = trim * (1.0 - mix)
            if self._ready and bias != self._charged_bias:
                self._charge_output(rewire=True)
        self._refresh_output()

    def _refresh_output(self):
        """Mix 0 is the borrowed source itself, not a path through the graph.

        Nothing rounds on the way, so the wire invariant is exact by
        construction rather than by luck - which is what the `MidSide` tail
        stopped being when the pin moved to audiodsp `3388df4` (seven samples
        of 16384 off by one LSB).
        """
        if not self._ready:
            return
        if self._value(5) <= 0.0:
            self._output = self._source
            self._latency = 0
        else:
            self._output = self._tilt
            self._latency = self._wet_delay

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        _component.Component.program_change(self, index, channel, note_id,
                                            sample_position)
        self._route()
        self._refresh_output()

    def _route(self):
        """Patch 8 `Fuzz - lean` is the only pull chain that shapes at ×2
        instead of the constructor's factor. Nothing else in the graph moves,
        and the factor it drops is the one number the S3's budget turns on.
        """
        if self._lean is None:
            return
        lean = self._patch_index == LEAN_PATCH
        if lean == self._routed_lean:
            return
        self._hps[1].play(self._lean if lean else self._shapers[0])
        self._routed_lean = lean
        self._wet_delay = _group_delay_samples(
            self._lean_oversample if lean else self._oversample)

    @property
    def latency_samples(self):
        self._check_live()
        return int(self._latency)
