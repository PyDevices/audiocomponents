# Effects Dossier — `Distortion` (ProCo Rat; Boss DS-1 as the second character)

**Class:** `lib/audioeffects/drive.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Drive, roadmap Phase 4
**Standout:** ProCo Rat (vision §4.2) — **confirmed**, with the Boss DS-1
carried as a second **character** (vision §10.7: each character gets its own
trait rows). They are not the same circuit: the Rat is one gain stage with the
diodes to ground and a first-order Filter; the DS-1 is a fixed 35 dB transistor
booster into an op-amp stage, diodes to ground under a 7.2 kHz cap, and a
scooped passive tone. Both schematics with values were reached (S1, S2), every
trait below was derived analytically in this run — and re-derived independently
by the Phase 0 licence audit, which reproduced every one of them except F2's dB
levels (Appendix F) — and the DAFx literature models the DS-1 stage by stage
(S5, S6). Nothing argues for a swap.
**Grade:** circuit — schematics with values read for both, and an analytic
derivation of every trait; the ngspice decks are Station A's first job (§8 Q1).
**Portability tier:** **audioif** — `audioroute.Splitter` for the gain-stage
legs and the DS-1 tone crossfade, plus the oversampled waveshaper of §5.
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

**Rat (character `filter`).** 1M / 22 nF at the jack, R3 1K into the op-amp
with C2 1 nF shunting the top ("shunts high freqs to ground and out to mellow
the signal" — S1; with an ideal source that corner is 159 kHz — *derived*,
1/(2π·R3·C2) from S1's own values — and inaudible,
so what it really trims is source impedance). One non-inverting LM308 (the
OP07 in units after about 1996 — S1, "the Texas Instruments OP07DP was a
replacement op-amp used in the new models"; S3 gives the 1996 date and spells
the part "OD07DP") whose inverting input reaches ground
through two parallel legs, R4 47 Ω + C5 2.2 µF (1539 Hz) and R5 560 Ω +
C6 4.7 µF (60 Hz), with the 100K Distortion pot and C4 100 pF as feedback.
Gain is 1 + Zf/Zs: unity at pot zero, up to 1 + 100K/(47‖560) = 2305 (67 dB),
and the two legs make it rise with frequency — 48.2 dB at 100 Hz against
62.1 dB at 1 kHz. That rise is then folded back down by the op-amp's own
bandwidth, which C3 30 pF sets, and the fold is the "mid hump": S1 states the
LM308 gives "no more than 30dB" at 10 kHz. The op-amp output, which hits its
rails long before the pot is up, passes C7 4.7 µF and R6 1K ("limit the amount
of current through the diodes" — S1) into D1/D2, a like pair **to ground**: a
hard, symmetric clip at 0.57–0.66 V. Then the Filter — R7 1.5K plus the 100K
Filter pot in series into C8 3.3 nF to ground, a first-order low-pass running
32 kHz to 475 Hz, wired backwards by convention ("a very dark tone when set
fully clockwise" — S3). A 2N5458 source follower and the 100K Volume pot close
it. **DS-1 (character `scoop`).** A 2SC2240 follower into a common-emitter
booster with 470K / 250 pF feedback and R9 22 Ω in the emitter: "35dB (56 times
bigger)" (S2), a band-pass with poles at 3 Hz and 600 Hz (S5 eq. 15), and it
clips **asymmetrically** — S6 §3.3.3 simulates that stage and reports "one
polarity clips at a lower level than the other", which is where the DS-1's even
harmonics come from. Then a non-inverting op-amp stage (TA7136AP → BA728N →
M5223AL by era, S4) with the 100KB Distortion pot in the feedback under
C7 100 pF, and R13 4.7K + C8 0.47 µF to ground: 0 → 26.5 dB, its input
high-pass moving 72 → 3 Hz as the pot comes up (S2). R14 2.2K into D4/D5 1N4148
to ground with C10 0.01 µF across them — a 7.2 kHz low-pass the conducting
diodes short out. Finally a passive tone: R16 6.8K / C12 0.1 µF (234 Hz) and
C11 0.022 µF / R17 6.8K (1063 Hz) with the 20KB pot strung between their
outputs, giving a scoop near 500–650 Hz — S2 and S4 both say "around 500 Hz"; the
646 Hz upper end is this run's own nodal solve, §3 SC5 and Appendix A. No LFO
in either circuit.

## 2. Sources and license calls

Every source reached in this run, none from memory. **Appendix E** holds what
each one actually said — every quotation and component value; this table
records the contribution and the licence call. The DAFx PDFs were fetched by
`WebFetch`, which cannot render PDF text, and their bytes read with `pypdf`.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. ElectroSmash, "ProCo Rat Analysis" (MAS Effects mirror) | every Rat value and stated figure | "Some Rights Reserved, you are free to copy … (App. S1) | https://electrosmash.mas-effects.com/proco-rat.html | yes |
| S2. ElectroSmash, "Boss DS-1 Distortion Analysis" (same mirror) | every DS-1 value and stated figure | **License unverified … (App. S2) | https://electrosmash.mas-effects.com/boss-ds1-analysis.html | yes |
| S3. Wikipedia, "Pro Co RAT" | op-amp eras, diode types, the reversed Filter … (App. S3) | CC BY-SA 4.0 — footer read this run: "Text is … (App. S3) | https://en.wikipedia.org/wiki/Pro_Co_RAT | yes |
| S4. Wikipedia, "Boss DS-1" | op-amp eras, ±0.7 V clipping, the 500 Hz scoop … (App. S4) | CC BY-SA 4.0 — same footer line, read this run | https://en.wikipedia.org/wiki/Boss_DS-1 | yes |
| S5. Yeh, Abel, Smith, DAFx-07, "Simplified … (App. S5) | the DS-1 stage by stage (eq. 15–19) … (App. S5) | "© 2007 D. T. Yeh. All rights reserved." … (App. S5) | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_distortion.pdf | yes (WebFetch + pypdf) |
| S6. Yeh, Smith, DAFx-08 | the DS-1 common-emitter stage's design values and its … (App. S6) | as S5 (rights line at … (App. S6) | https://ccrma.stanford.edu/~dtyeh/papers/yeh08_dafx_sim.pdf | yes (WebFetch + pypdf) |
| S7. Yeh, Abel, Smith, DAFx-07, "Simulation of the diode limiter …" | the static approximation's error bound and the … (App. S7) | as S5 (rights line at … (App. S7) | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_clipode.pdf | yes (WebFetch + pypdf) |
| S8. Nexperia 1N4148 SPICE model | the ten diode parameters used in every Newton solve … (App. S8) | no license text in the file (re-read in full … (App. S8) | https://assets.nexperia.com/documents/spice-model/1N4148.prm | yes |
| S9. `SharpSoundPlugins` / `Rodent.V2/TFGain.cs` | a value cross-check — agrees on legs and caps … (App. S9) | MIT, chased to the licence file itself and … (App. S9) | https://github.com/ValdemarOrn/SharpSoundPlugins — values read at <https://raw.githubusercontent.com/ValdemarOrn/SharpSoundPlugins/master/Rodent.V2/TFGain.cs> | yes |
| S10. cushychicken, "Simulating the ProCo RAT … in LTSpice" | an independent LTspice study agreeing on 67 dB … (App. S10) | **License unverified … (App. S10) | https://cushychicken.github.io/ltspice-proco-rat/ | yes |
| S11. chrisgilroyrecords, "ProCo 'Ruetz' Rat Mod" | what the mod targets and what it does to the sound | **License unverified … (App. S11) | https://chrisgilroyrecords.wordpress.com/2014/05/31/proco-ruetz-rat-mod/ | yes |
| S12. TI OP07C product page | GBW 0.6 MHz typ and slew rate 0.3 V/µs typ … (App. S12) | manufacturer product page: figures are facts … (App. S12) | https://www.ti.com/product/OP07C | yes |
| S13. The palette, probed under `audiocomponents/.venv/bin/python` | every measured palette number in §4–§5 and Appendices … (App. S13) | MIT (this organization): SPDX line in the … (App. S13) | `audioif/src/shared/audioif_distortion.c` | yes (re-imported by the audit 2026-09-06) |
| S14. archive.org item `boss_DS-1_SERVICE_NOTES` (Boss's own DS-1 … (App. S14) | nothing usable: the item and its OCR text were … (App. S14) | metadata API returns **no `licenseurl` and no … (App. S14) | metadata <https://archive.org/metadata/boss_DS-1_SERVICE_NOTES>; text <https://ia800505.us.archive.org/35/items/boss_DS-1_SERVICE_NOTES/DS-1_SERVICE_NOTES_djvu.txt> | yes (both re-fetched this run: metadata HTTP 200, 7,803 bytes; text HTTP 200, 13,205 bytes) |

**Audit note:** the Phase 0 licence-and-citation audit re-fetched every row
above on 2026-09-06 — every URL, the repository licence files, the archive.org
metadata and the palette — and re-derived §3's numbers independently. Its
corrections, what it reproduced, the one thing it did not (F2), and what it
could not reach are **Appendix F**.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Character **`filter`** (Rat):

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| F1 | **Two-leg pre-clip shaping.** The two feedback legs make the pre-clip gain rise with frequency — ideal-op-amp 48.2 / 62.1 / 66.5 dB at 100 Hz / 1 kHz / 5 kHz at max Distortion (*derived*, reproduced this run) — and the 100 Hz→1 kHz tilt is the legs, not the pot: 13.84 dB at pot 1.00 and 0.50, 13.73 at 0.10 (Appendix A). **It is measured at low Distortion**, because at max Distortion the op-amp's own bandwidth swamps the legs (F2) and drops the measurable tilt to 2.8–7.6 dB; at pot ≤ 0.10 both GBW candidates leave it at 13.1–16.3 dB (Appendix G). | S1 (values, 1539/60 Hz); S9, S10 | high — pure RC … (App. F1) | the 100 Hz→1 kHz tilt outside 11–18 dB at Distortion 10 %, or outside 11–17 dB at Distortion 2 % (bands this dossier's, wide enough for the ideal case and both GBW candidates: 13.73 / 16.27 / 14.57 and 13.13 / 13.65 / 13.29); or a tilt that does not fall as Distortion is raised to maximum | plain swept sine at Distortion 10 … (App. F1) |
| F2 | **The op-amp's bandwidth makes the mid hump.** With a single-pole open loop the max-Distortion response peaks **below 1 kHz** and is ≥ 12 dB down at 10 kHz relative to that peak. Both derivations of the levels agree on that band and disagree on the levels themselves — see the audit note below the table, which is why the row states only the band. | S1 (bandwidth: "Bandwidth and Slew Rate are … (App. F2) | medium — the effect … (App. F2) | a peak above 1.5 kHz — an ideal op-amp with no bandwidth limit peaks at 4.9 kHz and is 0.8 dB down at 10 kHz, which is the fault this row exists to catch — or 10 kHz less than 12 dB below the peak | **the equal-drive contour of … (App. F2) |
| F3 | **Hard symmetric clip to ground.** Output pins at 0.567 V for 1 V of pre-clip drive and 0.660 V for 3.5 V (*derived*, 1K into the pair; reproduced this run); h2 and h4 ≤ −60 dB; at 3.5 V a near-square, THD 32.9 %, h3 −11.2 dB, h5 −17.0 (ideal square −9.54 / −13.98). | S1 ("symmetric distortion"); S3 … (App. F3) | high | h2 **or h4** above −40 dB with matched diodes; output peak outside 0.55–0.60 V at 1 V of drive or 0.64–0.69 V at 3.5 V (the bands this dossier's); the peak rising more than 1.5 dB between them (derived +1.32 dB); h3 at 3.5 V outside −11.2 ± 2 dB, or h5 outside −17.0 ± 3 dB | 1 kHz sine at Distortion pot 10 … (App. F3) |
| F4 | **Clean at minimum.** At pot zero the stage is unity and the diodes idle below about 0.35 V (incremental gain 0.964 at 0.30 V, 0.524 at 0.50): a 0.1 V peak passes at 0.00 % THD, 0.35 V at 0.45 %. This is what separates the Rat from the DS-1 (SC3) and from a Tube Screamer. | S1 ("Gvmin … =1 (0dB)") … (App. F4) | high | THD above 1 % at −20 dBFS, **or outside 0.25–0.8 % at −9.1 dBFS** (0.35 V; derived 0.45 %, the band this dossier's) — the second point is what separates "unity below the knee" from "flat forever" | THD of a 1 kHz sine at −20 dBFS … (App. F4) |
| F5 | **The Filter is first-order and runs backwards.** `1/(2π(1.5K + p·100K)·3.3 nF)`: 32.2 kHz at p = 0, 1820 Hz at 0.25, 936 at 0.5, 475 at 1 — darker clockwise. At p = 1: −7.35 / −12.72 / −20.48 dB at 1 / 2 / 5 kHz, i.e. 6 dB per octave, not 12 (all four corners and the three dB figures reproduced this run). | S1 (formula and span); S3 (direction); S9, S10 | high | the span missing 475 Hz or short of 16 kHz open; more than 9 dB between 2 and 5 kHz at p = 1 (second-order gives ≈15); brightening clockwise; or any quoted dB figure missed by more than 1.5 dB | magnitude response from a swept … (App. F5) |

Character **`scoop`** (DS-1):

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| SC1 | **Two gain stages, the first rising with frequency.** A fixed 35–36 dB booster whose two first-order corners at 3 Hz and 600 Hz put 100 Hz 14.4 dB and 500 Hz 2.5 dB below 1 kHz (*derived*; re-derived this run as 14.35 and 2.53 dB, which come out **only if both corners are high-passes** — the draft's "band-passed" is the opposite tilt and contradicted its own figures, §8 Q9 and Appendix G); then 0 → 26.5 dB whose input corner moves 72 → 3 Hz; about 61.5 dB total at maximum. SC3's 0.96 V at −34 dBFS is the same arithmetic and agrees. | S2; S5 (eq. 15–16) … (App. SC1) | high for the figures … (App. SC1) | total pre-clip gain at max Distortion outside 55–68 dB; the booster's 100 Hz within 8 dB of its 1 kHz, or its 500 Hz more than 5 dB below it; or 100 Hz reading **above** 1 kHz at any setting — the band-pass reading of the same two corners, and the fault this row catches | at Distortion 0 a plain swept … (App. SC1) |
| SC2 | **Hard symmetric clip under a 7.2 kHz cap.** 2.2K into the pair with 0.01 µF across it (1/(2π·2.2K·0.01 µF) = 7.23 kHz, reproduced this run): ceiling 0.532 V (1 V in) to 0.622 V (3.5 V in); below the diode threshold the stage is a first-order low-pass at 7.2 kHz, which the conducting diodes short. | S2; S5 Fig. 8; S4 (±0.7 V); Newton with S8 | high | the small-signal output magnitude matching SC5's tone response **alone** within 1.5 dB at 14 kHz, i.e. no 7.2 kHz pole present at all; the ceiling outside 0.51–0.56 V at 1 V of drive or 0.60–0.65 V at 3.5 V (the bands this dossier's), or rising more than 1.5 dB between them (derived +1.35 dB); h2 or h4 above −40 dB with Asymmetry at 0 | swept sine at −48 dBFS … (App. SC2) |
| SC3 | **Never clean.** The booster alone drives a 20 mV (−34 dBFS) 1 kHz input to about 0.96 V at the clipper, leaving about 18 % THD *with Distortion at minimum* (*derived*; both halves reproduced this run — 0.964 V from SC1's corners, 18.0 % from Appendix A's 2.2 kΩ row at 1 V). | S2; S5 (first-stage distortion "not … (App. SC3) | high | THD below 8 % **or above 30 %** at −34 dBFS with Distortion at minimum — the upper bound is this dossier's, so a build that merely distorts everything cannot pass a trait about how much | THD of a 1 kHz sine at −34 dBFS … (App. SC3) |
| SC4 | **Even harmonics from the asymmetric front end.** The common-emitter stage clips asymmetrically at guitar levels, so `scoop` carries even harmonics `filter` does not: h2 at or above −30 dB re fundamental on a 220 Hz, −20 dBFS input at max Distortion with Asymmetry at stock, **and at least 20 dB above what the same measurement gives with Asymmetry at 0** (F3's matched pair puts that at ≤ −60 dB). | S2 ("Q2 asymmetric clipping gives rise to … (App. SC4) | medium — mechanism … (App. SC4) | h2 below −30 dB at that point, or within 20 dB of the Asymmetry-0 reading. (Separately: if §8 Q1's deck with a 2SC2240 model puts the circuit's own h2 below −40 dB, the row is re-stated at the simulated level or dropped with cause — that is a revision of the claim, not a failure of the build) | harmonic spectrum of a 220 Hz … (App. SC4) |
| SC5 | **The scoop.** At centre the response has a minimum between 500 and 750 Hz sitting 6–10 dB below both the 100 Hz and 5 kHz points (*derived*, full nodal solve into a 100K load: −15.4 dB at 646 Hz against −7.3 and −6.9; an independent solve this run returns −15.41 dB at 645 Hz, 8.08 dB under 100 Hz and 8.51 under 5 kHz). At the bass end 5 kHz is 21.4 dB below 100 Hz (re-solved 21.37); at the treble end 100 Hz is 14.8 dB below 5 kHz (re-solved 14.82). | S2 (its "-20db (500Hz)" against a "-12dB … (App. SC5) | high for shape and … (App. SC5) | a centre notch shallower than 4 dB or outside 400–800 Hz; either extreme with under 12 dB of tilt from 100 Hz to 5 kHz; or any read point more than 2 dB from the composite prediction | magnitude response at Tone −1 / 0 … (App. SC5) |

Shared by both characters:

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| A1 | **Alias floor.** Inharmonic energy in a 1010 Hz sine at max Distortion and −20 dBFS is ≥ 60 dB below the fundamental over 20 Hz–20 kHz. Set 20 dB under S7's static-approximation error so aliasing is never the dominant error of a near-square at 48 kHz. Measured **once per character**, and both must pass; `filter` is the harder of the two, its clipper being a near-square (F3). | S5–S7 (8× is standard) … (App. A1) | medium (the bar is a … (App. A1) | inharmonic energy above −60 dB at that point in **either** character, on **any** target, the P4's single-precision build included | sum of every FFT bin more than … (App. A1) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**`filter`**, following S1 and S5's separated-blocks method:

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**A1 — the oversampled, table-driven waveshaper. Traits: A1; and F3 / SC2 at
h7.**
*The palette instead* runs one fixed curve per mode at the base rate
(`audioif_distortion.c:63-66`), with no anti-aliasing and no way to load a
curve.
*The measurements that show it cannot reach the traits:* (a) on a 1010 Hz sine
the palette's best soft path measures −22.3 dB of inharmonic energy at the
near-square THD of 45 % that F3 demands, against A1's −60 dB — a 38 dB gap,
and −43.5 dB even at 34.5 % THD (Appendix D). (b) Fitted to the Newton diode
curve over ±1 V, `soft_clip` reads h7 at −36.4 dB where the Rat's real clipper
gives −47.9, and −35.1 where the DS-1's gives −58.6: **11.5 and 23.5 dB too
rich**. `tanh` and S5's eq. 19 come far closer (−42.9 and −44.3 for the Rat)
and neither is on the palette; a table carries the Newton curve exactly.
*What is asked:* a table-driven waveshaper in an audioif-own module,
oversampling ×2 / ×4 / ×8 (costed in Phase 1), **minimum-phase IIR**
interpolation and decimation so the node adds no latency, an optional
first-order pre-filter per S7, and curves supplied as data — the Newton tables
of §4, two of them here (booster and clipper).
*Refutation record (Phase 0):* the palette's two saturating curves were fitted
and measured against both clippers — h3 and h5 reachable, h7 and the alias
floor not; the one hard-clip path the palette has wraps to −32768 (§8 Q5) and
is disqualified; the ported node cannot gain an option. **Not refuted.**
Shared with `Overdrive` (its T7), `Fuzz` and `Saturation`.

- **Oversample by composing `audiospeed.SpeedChanger`.** The palette carries a …  *(argument in full: App. R)*
- **Build the curve from `audiomath.Multiply` instead of a table.** `Multiply` …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

`capabilities = ()`; the transport is not read (D10) — neither circuit has a
time-varying element.

Macros — 10 of 16, MIDI 0..127:

| # | Label | Mode | Range and law | Generalizes |
|---|---|---|---|---|
| 0 | Distortion | UNIPOLAR | `filter`: 0 → 67 dB over the feedback pot with an audio law (0 / 47 / 61 / 67 dB at 0 / 10 / 50 / 100 % of the resistance); `scoop`: 0 → 26.5 dB, linear | Distortion (Rat 100K-A; DS-1 100KB) |
| 1 | Filter | UNIPOLAR | first-order low-pass 32 kHz → 475 Hz, **clockwise darker**; active in `filter`, a post-filter in `scoop` (default open) | Filter (Rat 100K) |
| 2 | Tone | BIPOLAR | −1 bass end → +1 treble end of the LP/HP crossfade; active in `scoop`, inert in `filter` | Tone (DS-1 20KB) |
| 3 | Volume | UNIPOLAR | −∞ → 0 dB, audio taper | Volume / Level |
| 4 | Mix | UNIPOLAR | 0 → 1; 0 is the Tier 1 wire | none |
| 5 | Character | TOGGLE | `filter` / `scoop` | none — two standouts |
| 6 | Ceiling | UNIPOLAR | clip threshold 0.5 → 2.0 × silicon (≈0.66 V); the variants S3 names span germanium (lower) to LED (higher) | none; the RAT variants' diode choice |
| 7 | Boost | UNIPOLAR | front booster 0 → 35 dB; `scoop` defaults to 35, `filter` to 0 | none on the Rat; the DS-1's fixed Q2 stage |
| 8 | Asymmetry | UNIPOLAR | the booster curve's bias, 0 = symmetric → 1 = stock DS-1 (SC4's level); `filter` defaults 0 | none; the DS-1's Q2 operating point |
| 9 | Body | UNIPOLAR | the 47 Ω treble leg's series resistance 47 Ω → 10 K: 0 = stock, 1 = the leg effectively removed (S9's Ruetz parameter, S11's mod) — *derived*, it flattens the shaping from 13.9 dB of tilt to 1.3 | none; a documented Rat mod |

Characters: `filter` (default) and `scoop`. Patches:

| # | Name | Char | Dist | Filt | Tone | Vol | Mix | Ceil | Boost | Asym | Body |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Filter Half Mid Gain | filter | 64 | 64 | 64 | 100 | 127 | 64 | 0 | 0 | 0 |
| 1 | Filter Open Low Gain | filter | 24 | 0 | 64 | 110 | 127 | 64 | 0 | 0 | 0 |
| 2 | Filter Closed Full Gain | filter | 127 | 127 | 64 | 84 | 127 | 64 | 0 | 0 | 0 |
| 3 | High Ceiling Full Gain | filter | 127 | 48 | 64 | 72 | 127 | 108 | 0 | 0 | 0 |
| 4 | Low Ceiling Mid Gain | filter | 64 | 56 | 64 | 110 | 127 | 24 | 0 | 0 | 0 |
| 5 | Flat Legs Mid Gain | filter | 72 | 40 | 64 | 100 | 127 | 64 | 0 | 0 | 127 |
| 6 | Scoop Centre Full Boost | scoop | 100 | 0 | 64 | 100 | 127 | 64 | 127 | 96 | 0 |
| 7 | Scoop Bright Mid Gain | scoop | 64 | 0 | 112 | 100 | 127 | 64 | 127 | 96 | 0 |
| 8 | Scoop Bass Low Gain | scoop | 24 | 0 | 16 | 110 | 127 | 64 | 127 | 96 | 0 |
| 9 | Scoop Low Boost Even | scoop | 80 | 0 | 64 | 100 | 127 | 64 | 62 | 127 | 0 |
| 10 | Clean Edge | filter | 0 | 0 | 64 | 127 | 127 | 64 | 0 | 0 | 0 |

Patch 10 exists because F4 says the Rat *can* be nearly clean; there is no such
patch in `scoop`, because SC3 says the DS-1 cannot.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/drive.py` (`grep -n`, 2026-09-06):

- `drive.py:92` — `MACRO_LABELS = ()`: a distortion with no Distortion knob, no
  Filter and no Volume.
- `drive.py:97-99` — `mode=_DM.CLIP, drive=0.7`: through the kernel's …  *(argument in full: App. R)*
- `drive.py:96` — no tone control of any kind. The Rat's Filter is the control
  the pedal is known for (F5) and the DS-1's scoop is its identity (SC5).
- `drive.py:99` — `pre_gain=6.0` with `post_gain=-6.0` is a fixed operating …  *(argument in full: App. R)*
- `drive.py:86` — the docstring "Hard clipping." is the whole design.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **The ngspice decks** — two, in the TS808's form (`rat`, `ds1`), with a
   2SC2240 model for the booster and an op-amp macro-model whose GBW and slew
   are parameters, so F2's exact peak, SC4's h2 level and the slew question
   each get a second derivation. Station A; where they live is Arthur's.
2. **The 0 dBFS reference** — 1.0 V peak, shared with `Overdrive`.
   Implementation session.
3. **Slew rate**, recorded unmeasured above. Q1's deck at 0.3 V/µs against an
   ideal op-amp on a 1 kHz + 5 kHz two-tone decides whether a trait is added;
   under 1 dB of difference closes the question with that number.
4. **The LM308's real GBW.** F2 is stated to survive both 0.32 MHz (S1's own
   "30dB at 10KHz") and the 1 MHz nominal, but the datasheet was not reached.
   The Phase 0 audit re-tries; failing that Q1's deck records the value as an
   assumption and F2 keeps its wide band.
5. **The op-amp's rail swing** (±3.5 V assumed in this run's clipper tables;
   S9 assumes ±4 V) moves nothing in F3 — the diodes clip at 0.66 V either way
   — but sets where `scoop`'s stages square off before them. Same deck.
   Related: the palette's one hard-clip path wraps to −32768
   (`audioif_distortion.c:45`, `:64`; `audiofilters/Distortion.c:272`), a
   ported-node defect measured in `Overdrive.md` Appendix F; the rebuild never
   uses that path.
6. **DS-1 revision values.** S2 and S5 disagree on C8 (0.47 µF vs 1 µF) and C7
   (100 pF vs 250 pF), consistent with the three op-amp eras S4 lists, and the
   service notes' text (S13) was not reachable to settle it. SC1 uses S2's
   values, self-consistent with its 72 Hz corner, and the disconfirmation bands
   are wide enough for either.
7. **The Rat's gain pot: 100K or 150K.** S1 and S10 say 100K; S9's MIT emulator
   uses 150K. F1 and F5 are stated from 100K, and the difference moves the top
   of the Distortion law by 3.5 dB, inside F1's band. Phase 0 audit, or Q1.
8. **Characters versus classes** (vision §10.7). This seed keeps the DS-1 as a
   character with its own rows; if Station C shows the two trait sets cannot
   both pass on one node graph, the answer is two graphs behind one `Character`
   toggle, never a merged trait set. Implementation session.
9. **What S5 eq. 15 actually calls the booster's shape.** SC1's own figures
   (100 Hz 14.4 dB and 500 Hz 2.5 dB below 1 kHz) are reproduced only by two
   first-order **high-pass** corners at 3 Hz and 600 Hz; read as a band-pass
   *passing* 3–600 Hz the same corners put 100 Hz 5.6 dB **above** 1 kHz, the
   opposite tilt. The figures are kept and the wording corrected, but S5 was
   not re-read in the trait-critic pass, so which the paper itself states is
   open: Station A re-reads eq. 15 with §8 Q1's deck and either confirms the
   wording or moves the figures. Until then a rebuild is measured against the
   figures, not the word.


## Appendix

### A. The analytic derivations, in full

**Diode pair to ground** (Newton on `(Vin − Vo)/R = 2·IS·sinh(Vo/(N·Vt))`,
S8's IS 4.352e-9 and N 1.906, Vt 25.852 mV):

| Vin | Rat, R6 = 1K: Vout / incremental gain | DS-1, R14 = 2.2K: Vout / gain |
|---|---|---|
| 0.30 V | 0.2982 V / 0.964 | 0.2961 V / 0.927 |
| 0.50 V | 0.4552 V / 0.524 | 0.4349 V / 0.431 |
| 1.00 V | 0.5670 V / 0.102 | 0.5320 V / 0.095 |
| 2.00 V | 0.6240 V / 0.035 | 0.5865 V / 0.034 |
| 3.50 V | 0.6597 V / 0.017 | 0.6215 V / 0.017 |
| 9.00 V | 0.7125 V / 0.006 | 0.6739 V / 0.006 |

Harmonics of a 1 kHz sine through those stages (ideal square: h3 −9.54,
h5 −13.98 dB):

| stage | pre-clip peak | out peak | THD | h3 | h5 | h7 |
|---|---|---|---|---|---|---|
| Rat 1K | 0.10 V | 0.1000 V | 0.00 % | −88.2 | −114.7 | −147.4 |
| Rat 1K | 0.35 V | 0.3452 V | 0.45 % | −47.3 | −57.9 | −73.7 |
| Rat 1K | 1.00 V | 0.5670 V | 16.87 % | −15.6 | −30.5 | −47.9 |
| Rat 1K | 3.50 V | 0.6597 V | 32.88 % | −11.2 | −17.0 | −21.5 |
| DS-1 2.2K | 1.00 V | 0.5320 V | 18.02 % | −15.1 | −28.2 | −58.7 |
| DS-1 2.2K | 3.50 V | 0.6215 V | 32.98 % | −11.2 | −17.0 | −21.3 |

**Rat gain stage**, `1 + Zf/Zs` with both legs, 100K ‖ 100 pF feedback, dB:

| pot | model | 100 Hz | 500 Hz | 1 kHz | 2 kHz | 5 kHz | 10 kHz |
|---|---|---|---|---|---|---|---|
| 1.00 | ideal | 48.25 | 57.50 | 62.09 | 65.20 | 66.46 | 65.72 |
| 0.50 | ideal | 42.24 | 51.48 | 56.08 | 59.24 | 60.75 | 60.74 |
| 0.10 | ideal | 28.41 | 37.55 | 42.14 | 45.31 | 46.90 | 47.18 |
| 1.00 | GBW 0.32 MHz | 47.85 | 51.91 | 48.62 | 43.42 | 35.86 | 29.97 |
| 1.00 | GBW 1.0 MHz | 48.12 | 55.62 | 55.70 | 52.04 | 45.23 | 39.60 |

Peak at pot 1.0: 66.47 dB at 4925 Hz ideal; 52.10 dB at 411 Hz at 0.32 MHz;
56.25 dB at 717 Hz at 1 MHz. The 0.32 MHz row reproduces S1's own "no more than
30dB" at 10 kHz to 0.03 dB, which is why F2 uses it as the low bound. The Ruetz
setting (R4 47 Ω → 10 K) flattens the stage to 44.22 / 45.52 / 45.15 dB at
100 Hz / 1 kHz / 5 kHz — 1.3 dB of tilt instead of 13.9, matching S11's "lowers
the over all gain … adds a great rich bottom end".

**Rat Filter**, `1/(2π(1.5K + p·100K)·3.3 nF)`:

| p | fc | 1 kHz | 2 kHz | 5 kHz |
|---|---|---|---|---|
| 0.00 | 32152 Hz | −0.00 | −0.02 | −0.10 |
| 0.25 | 1820 Hz | −1.15 | −3.44 | −9.32 |
| 0.50 | 936 Hz | −3.30 | −7.45 | −14.70 |
| 1.00 | 475 Hz | −7.35 | −12.72 | −20.48 |

**DS-1 booster**, `H(s) = s²/((s+2π·3)(s+2π·600))` (S5 eq. 15), dB re 1 kHz:
50 Hz −20.29, 100 Hz −14.35, 200 Hz −8.67, 500 Hz −2.54, 1 kHz 0.00,
2 kHz +0.96, 5 kHz +1.27.

**DS-1 tone**, full nodal solve of C11 0.022 µF / R17 6.8K (high-pass node),
R16 6.8K / C12 0.1 µF (low-pass node), the 20K pot strung between them with the
wiper as output into a 100K load. t = 0 is the bass end:

| t | 100 Hz | 250 Hz | 500 Hz | 1 kHz | 2 kHz | 5 kHz |
|---|---|---|---|---|---|---|
| 0.00 | −2.85 | −4.56 | −7.73 | −12.09 | −16.95 | −24.23 |
| 0.25 | −4.90 | −6.96 | −11.02 | −15.67 | −14.64 | −12.83 |
| 0.50 | −7.32 | −9.84 | −14.49 | −13.14 | −8.86 | −6.89 |
| 0.75 | −10.47 | −13.50 | −15.30 | −9.10 | −5.05 | −3.24 |
| 1.00 | −15.23 | −17.20 | −12.18 | −5.84 | −2.15 | −0.41 |

Centre: minimum −15.41 dB at 646 Hz, 8.08 dB below the shallower of the two
ends — S2's own "-20db (500Hz)" against a "-12dB overall" reference is an 8 dB
depth, so the solve agrees on depth and puts the frequency 146 Hz higher.
**Note for whoever re-derives this:** summing the two sections' *magnitudes*
instead of their phasors gives a notch only 1.5 dB deep at 499 Hz. The complex
solve is the right one; the magnitude sum is wrong and looks plausible.

### B. Palette curve shapes against the Newton diode curve

Each palette curve fitted for amplitude and scale by least squares over
±1.0 V of pre-clip drive, then a 1 kHz sine at 1.0 V peak put through it:

| stage | curve | fit rms | THD (ref) | h3 (ref) | h5 (ref) | h7 (ref) |
|---|---|---|---|---|---|---|
| Rat 1K | `soft_clip` | 0.0171 V | 15.04 (16.87) | −16.83 (−15.61) | −28.06 (−30.54) | −36.37 (−47.91) |
| Rat 1K | `WAVESHAPE` 0.9 | 0.0230 V | 15.97 | −16.51 | −26.06 | −33.03 |
| Rat 1K | tanh (not on the palette) | 0.0092 V | 16.10 | −16.06 | −29.61 | −42.91 |
| Rat 1K | S5 eq. 19, n = 2.5 (not on the palette) | 0.0084 V | 16.06 | −16.08 | −29.54 | −44.29 |
| DS-1 2.2K | `soft_clip` | 0.0151 V | 16.37 (18.02) | −16.13 (−15.11) | −26.97 (−28.15) | −35.10 (−58.65) |
| DS-1 2.2K | S5 eq. 19, n = 2.5 | 0.0066 V | 17.49 | −15.39 | −27.91 | −41.13 |

### C. First-order sections from a low-Q biquad

`synthio.Biquad` takes mode / frequency / Q / A only
(`audioif/src/synthio/Biquad.c:37-61`), so a first-order section is two real
poles with the second parked at 40 kHz: for a 1 kHz pole, f0 = 6324.6 Hz,
Q = 0.1543. Measured through `audiofilters.Filter` on the audioif CPython
build against a true first-order 1 kHz pole (dB): 100 Hz −0.04 (−0.04),
250 −0.23 (−0.26), 500 −0.87 (−0.97), 1000 −2.77 (−3.01), 2000 −6.63 (−6.99),
4000 −12.05 (−12.30), 8000 −18.64 (−18.13), 12000 −23.71 (−21.61). Good to
0.51 dB through 8 kHz; the parked pole shows above 10 kHz, which is why F5's
stated points stop at 5 kHz.

### D. The alias floor the palette actually reaches

1010 Hz sine at −6 dBFS through the palette's `soft_clip` path, no post-gain
compensation, 4800 samples (101 exact periods), inharmonic energy summed over
every non-harmonic bin: +12 dB pre-gain → THD 14.84 %, −64.8 dB; +18 → 24.68 %,
−54.5; +24 → 34.51 %, −43.5; +28 → 39.20 %, −36.5; +40 → 44.97 %, −22.3.
Re-measured by the palette verifier on 2026-09-06: every `soft_clip` row above
came back identical. The other two saturating paths are **corrected** — the
draft named the wrong drive position: `WAVESHAPE` reads −31.0 dB at 36.2 % THD
at **drive 0.95** (at drive 0.90 it is −38.1 dB at 30.7 %), and `OVERDRIVE`
−31.8 dB at 42.1 % at +28 dB of pre-gain (−28.9 dB at 43.3 % at +30 dB). F3 asks for a near-square (32.9 % at 3.5 V of drive, rising toward
38 % at 10 V), where the palette is 20–38 dB above A1's bar.

### E. What each source said, verbatim

**S1, ElectroSmash "ProCo Rat Analysis".** Values: R1/R2 1M, R3 1K, C1 22 nF,
C2 1 nF, U1 LM308, C3 30 pF, RDISTORTION 100K-A, R4 47 Ω, R5 560 Ω, C5 2.2 µF,
C6 4.7 µF, C7 4.7 µF, **C4 100 pF** (the feedback cap §1 names — added by the
licence audit 2026-09-06, which found it in the BOM but not in this list),
R6 1K, D1/D2 1N914, RTONE 100K-A, R7 1.5K, C8 3.3 nF, Q1 2N5458, R8 1M,
RVOLUME 100K-A. Every one of these was re-read in the fetched page's own parts
list this run. Gain: "Gvmin=1+0/(47//560)=1 (0dB)" and
"Gvmax=1+100K/(47//560)=2305 (67dB)". Legs: "fc2 = 1/(2π·47·2.2uF)=1539 Hz",
"fc3 = 1/(2π·560·4.7uF)=60 Hz". Clipping: "silicon diodes D1 and D2 do
hard-clipping on the pre-amplified signal creating symmetric distortion".
Filter: "fc=1/(2π·(RTONE + R7)·C8)", "fcmin=475Hz", "fcmax=32KHz". Op-amp:
"The LM308 is 0.3V/us around 40 times slower"; "the Slew rate taken from the
datasheet image is 300000 V/s"; "At 10KHz, for instance, the max. voltage gain
will be no more than 30dB"; "frequencies below 500Hz will be amplified without
problems, but higher frequencies will have less and less amplification";
"Bandwidth and Slew Rate are proportional to 1/Ccompensation … The typical and
suggested value by the datasheet is 30pF (same as used in the Rat design)";
"Part of the signature sound of a Rat is essentially the op-amp collapsing
under pressure". Other: "The 1nF cap C2 shunts high freqs to ground and out to
mellow the signal"; "The resistor R6 will limit the amount of current through
the diodes". Rights: "Some Rights Reserved, you are free to copy, share, remix
and use all material. Trademarks, brand names and logos are the property of
their respective owners." — verified verbatim on this page by the audit
2026-09-06.

**S2, ElectroSmash "Boss DS-1 Distortion Analysis".** Q1/Q2/Q3 2SC2240;
C1 47 n, R1 1K, R2 470K, R3 10K; C2 0.47 µ, C3 47 n, C4 250 p, R4/R5 100K,
R7 470K, R8 10K, R9 22 Ω; U1 NJM3404A (or M5223AL, BA728N), C5 68 n, C7 100 p,
C8 0.47 µ, C10 0.01 µ, R10 100K, R13 4.7K, R14 2.2K, VR1 100KB, D4/D5 1N4148;
C11 0.022 µ, C12 0.1 µ, R16/R17 6.8K, VR3 20KB. Quotes: "35dB (56 times
bigger)"; "Q2 asymmetric clipping gives rise to even-order harmonics";
"1 + (100K/4.7K) = 22.3 (26.5dB)" maximum and "1 (0dB)" minimum; "fc max =
72Hz" to "fc min = 3Hz"; "fc=7.2KHz" for R14 and C10; tone "fc=234Hz" and
"fc=1063Hz", a "frequency scoop/notch around 500Hz", "overall -12dB (4 times)
loss" with "-20db (500Hz)".

**S3, Wikipedia "Pro Co RAT"** (CC BY-SA 4.0): "As with the RAT2, the
TurboRAT's LM308 op-amp was changed to the OD07DP in 1996"; "two 1N4148 silicon
diodes to produce the bulk of the RAT's distortion"; "The Filter control's
sweep works in reverse compared to other distortion pedals: it produces a very
dark tone when set fully clockwise"; the TurboRAT "removed the silicon diodes
and replaced them with 5mm red status indicator LEDs"; the You Dirty RAT
"switched to germanium diodes … a more saturated and compressed version".

**S4, Wikipedia "Boss DS-1"** (CC BY-SA 4.0): "built around the Toshiba
TA7136AP pre-amplifier"; 1994 "the Rohm BA728N"; 2000-present "Mitsubishi
M5223AL op-amp"; "silicon 1N4148 clipping diodes organized in a hard clipping
arrangement, clipping any signal above 0.7v and below -0.7v"; the tone is a
"fixed cutoff low-pass filter and a fixed cuttoff high-pass filter", creating
"a notch, or scoop, around 500 Hz when the potentiometer is in the center
position"; "The seesaw nature of the tone control leads to a -12 dB volume
loss".

**S5, Yeh/Abel/Smith DAFx-07.** §3.2: "This stage shows 36 dB of bandpass gain
… two zeros at DC, one pole at 3 Hz, one pole at 600 Hz, and another at 72 kHz,
which is ignored"; eq. 15. §3.3: eq. 16 with "Rt = D·100kΩ, Rb =
(1−D)100kΩ+4.7kΩ, Cz = 1µF, and Cc = 250pF"; "The op amp provides the main
nonlinearity of the Distortion effect. To first order, the op amp hard clips
the signal at Vdd/2 … It is also typically asymmetrical in behavior, leading to
significant even-order harmonics where otherwise only odd-order harmonics are
expected." §3.4: Fig. 8 is "2.2k / 0.01u / N914"; eq. 18 is the clipper ODE;
"the DC transfer curve is computed by setting dVo/dt = 0 … and tabulating the
function Vo = f(Vi) by Newton iteration"; eq. 19 `x/(1+|x|^n)^(1/n)` "well
approximates hyperbolic tangent when n = 2.5". §3.5: "The high pass corner
frequency is fhpf = 1.16 kHz and the low pass corner frequency is flpf =
320 Hz"; the tone circuit's intent is "a V-shaped equalization". §5: the test
signal is "a 220 Hz sine signal with amplitude of 100 mV"; "The measured spectra
exhibit a strong even-order nonlinearity that is not modeled in the digital
implementation."

**S6, Yeh/Smith DAFx-08.** §3.3: "Figure 9 shows the common-emitter
amplification stage from the Boss DS-1 … The design values for this circuit are
Ri = 100kΩ, Rc = 10kΩ, Rl = 100kΩ, Rf = 470kΩ, Re = 22Ω, Ci = 0.047µF, Cf =
250pF, and Co = 0.47µF." §3.3.3: "The BJT amplifier was simulated at a sampling
rate of 8× the audio rate 48000 Hz … Note the asymmetry of the duty cycle of
the output given a sine wave input. This is due to the asymmetry in the
nonlinearity: one polarity clips at a lower level than the other. This injects
an offset at DC … A slowly shifting bias would affect the distortion of
subsequent nonlinear stages."

**S7, Yeh/Abel/Smith DAFx-07 (clipode).** "The approximation shows noticeably
larger error than the numerical solvers, but it is typically less than -40 dB";
"It is found that using a first-order low-pass filter before the nonlinearity
with a cutoff frequency determined by the R and C of the diode limiter reduces
aliasing while maintaining accurate output."

**S9, `Rodent.V2/TFGain.cs`** (MIT per the repository README, "All code in this
repository is licensed under the MIT License"): `double R1 = 560;`,
`double R2 = 47 + 10000 * Parameters[P_RUETZ];`, `double C1 = 4.7e-6;`,
`double C2 = 2.2e-6;`, `double C3 = 100e-12;`, `double Gain = 150e3 *
Parameters[P_GAIN];`. Read for value comparison only; nothing ported.

**S10, cushychicken.** "Gain = 1 + Rgain/(560 || 47) = ~2300 [V/V] = ~67[dB]";
"D2/D3 serve to clip the signal down to a more modest +/-0.65[V]"; "R15 and C11
set a limit of the RC filter of the tone stage at about 32kHz … until bottoming
out at 475Hz"; "At higher gain, the opamp can't switch any faster, which limits
the response of higher frequencies as the gain increases"; "Increasing this to
300pF creates a softer transition to the opamp railing out, which yields an
overall softer clip - fewer higher harmonics."

**S11, chrisgilroyrecords.** The mod targets "the 47ohm resistor in the
circuit"; it "lowers the over all gain so the distortion is less aggressive,
think more of an overdrive", "alters part of the frequency response adding a
great rich bottom end" and gives "a smoother top end". No replacement
resistance range is stated on that page.

**S12, TI OP07C product page.** Slew rate "0.3 V/µs" typical; gain bandwidth
product "0.6 MHz" typical.

**S14 (renumbered from S13 by the audit 2026-09-06, because S13 in §2 is the
palette), archive.org item `boss_DS-1_SERVICE_NOTES`.** Metadata API
`https://archive.org/metadata/boss_DS-1_SERVICE_NOTES`, re-read this run (HTTP 200,
7,803 bytes; the `metadata` object's field list contains no `licenseurl`, no
`rights` and no `possible-copyright-status`): title "Boss: DS 1 SERVICE NOTES",
added 2016-01-25, DjVuTXT and image PDF derivatives present,
**no `licenseurl` and no rights field** — license unverified, treated as
copyleft. The OCR text **was** reached this run, at
`https://ia800505.us.archive.org/35/items/boss_DS-1_SERVICE_NOTES/DS-1_SERVICE_NOTES_djvu.txt`
(HTTP 200, 13,205 bytes); the earlier 404 came from requesting the item
identifier as the filename. Its first lines read "Dec. 1994", "This notes
includes the contents of the DS-1 First Edition and makes it obsolate", and it
names the "DS-1A" and "DS-1" revisions and, in OCR exactly as it stands,
"Q1-@3 2SC2240GA or 28C3378GR" (the licence audit 2026-09-06 replaced a
cleaned-up "Q1-Q3 … 2SC3378GR" with the literal text, since the point of the
row is that the OCR is degraded) —
but the schematic and parts list are OCR'd from a scan and are not legible as
values (the 250 pF feedback cap appears as "2e0p", C8 only as "0.47/50"). So it
is reached, and it still does not settle §8 Q6.

### F. The Phase 0 licence-and-citation audit (2026-09-06)

Every source in §2 was re-reached **by the audit itself** in this run; nothing
below rests on an earlier run's claim, and nothing is cited that this run did
not fetch.

**What was re-reached, and how.** Both ElectroSmash mirror pages by `curl`
(HTTP 200; 21,360 and 34,094 bytes), their text extracted and grepped locally —
which is how the rights-line finding is a checked fact: **the Rat page carries
ElectroSmash's "Some Rights Reserved" line in its article body and the DS-1 and
Tube Screamer pages carry no rights line at all**, only the mirror's footer.
Every S1 and S2 quotation in Appendix E was located in that text, including
both parts lists (which match Appendix E component for component, and supplied
the C4 100 pF the list had been missing) and the LaTeX-rendered formulas the
seed quotes in plain form (`G_{v max}=1+\frac{100K}{47//560}=2305 \: (67dB)`,
`f_{c min}= 475Hz`, `f_{c max}= 32KHz`). Both Wikipedia articles (HTTP 200;
footer read: "Text is available under the Creative Commons
Attribution-ShareAlike 4.0 License") and every S3 and S4 quotation. All three
DAFx PDFs downloaded from `ccrma.stanford.edu` (HTTP 200; 347,276 / 442,111 /
198,922 bytes), re-extracted with `pypdf` and **every S5, S6 and S7 quotation
located in the extracted text** — eq. 15's "36 dB of bandpass gain … one pole
at 3 Hz, one pole at 600 Hz, and another at 72 kHz", eq. 16's "Rt = D 100k,
Rb = (1 D)100k + 4.7k, Cz = 1 F, Cc = 250 pF", the op-amp hard-clip and
asymmetry sentence, Fig. 8's "2.2k 0.01u N914", eq. 19's "n = 2.5", §3.5's
"fhpf = 1.16 kHz … flpf = 320 Hz" and "V-shaped equalization", §5's 220 Hz /
100 mV test signal, and DAFx-08 §3.3's design values and §3.3.3's "one polarity
clips at a lower level than the other". The author's index page carries the
rights line; a grep of all three extracted PDFs finds no rights or copyright
text in the papers themselves. The Nexperia `.prm` read in full through
`WebFetch` (plain `curl` gets HTTP 403) and Nexperia's Terms of Use.
`SharpSoundPlugins`: `license.txt` (HTTP 200, 1,085 bytes, MIT, "Copyright (c)
2013 Valdemar Erlingsson"), `readme.md` and `Rodent.V2/TFGain.cs`, whose six
constants match Appendix E exactly. `cushychicken` and `chrisgilroyrecords` by
`curl`, every quotation confirmed — including S10's slew-rate sentence, which
is what F2's mechanism note turns on. TI's OP07C page (0.6 MHz GBW typ,
0.3 V/µs slew typ, and no occurrence of "LM308" or "replacement"). The
archive.org item: metadata JSON re-read (no `licenseurl`, no `rights` field)
and the OCR text re-fetched (HTTP 200, 13,205 bytes). Every `grep -n` line
number cited in §2–§5 and §7 was re-checked against the tree and holds.

**What was re-derived independently, and what it showed.** The audit recomputed
the derived numbers of §3 from the sourced component values, in complex
arithmetic, without looking at the seed's method:

- **Reproduced exactly.** F1's 48.2 / 62.1 / 66.5 dB at 100 Hz / 1 kHz / 5 kHz;
  F5's 32.2 kHz / 1820 / 936 / 475 Hz span and its −7.35 / −12.72 / −20.48 dB
  at Filter closed; F3's 0.567 V and 0.660 V and SC2's 0.532 V and 0.622 V from
  the Newton solve with S8's IS and N; F4's incremental gains 0.964 at 0.30 V
  and 0.524 at 0.50 V; SC1's 14.4 dB and 2.5 dB from S5's eq. 15 poles; **and
  SC5's full nodal solve — −15.4 dB at 645 Hz against −7.3 dB at 100 Hz and
  −6.9 dB at 5 kHz, 21.4 dB of tilt at the bass end and 14.8 dB at the treble
  end** — which is the number the earlier draft got wrong by summing
  magnitudes, so the correction Appendix A records is itself now confirmed by a
  second, independent solve.
- **Not reproduced: F2's levels.** Detailed in the audit note under the
  `filter` trait table. The trait as stated (peak below 1 kHz, ≥ 12 dB down at
  10 kHz) holds under both derivations; the parenthetical dB levels do not
  agree, and §8 Q1's deck settles them.
- Appendix D's alias floor and the palette curve fits of Appendix B were **not**
  recomputed; they carry no Tier 2 trait of this class (A1's bar is stated as
  the dossier's own) and they are this dossier's arithmetic, not a source.

**What was corrected in this run.**

1. **S2's licence call is now "license unverified — treated as copyleft"**, and
   the assertion that S1's line "is taken to cover this article too" is gone. A
   line read on one article of an unofficial mirror licenses that article, not
   the site.
2. **S1's cell now says what was actually read and what it does not say**: the
   line is on this page verbatim, it names no licence, and it reaches us
   through a repackager whose own footer disclaims ownership.
3. **S10 and S11 are downgraded to "license unverified — treated as
   copyleft."** S10's only rights text is a bare "© … Wherein The Chicken"
   footer; S11's page carries none at all. Neither was ever more than a
   document read for facts, but "no licence stated" and "unverified, treated as
   copyleft" are different claims, and the second is the honest one.
4. **S3, S4, S5, S6, S7, S8, S9, S12 and S13's cells now name the evidence**
   for their calls — the Wikipedia footer line, the grep that found no rights
   text inside the PDFs, the MIT `license.txt` chased past the README's label,
   the Nexperia terms sentence about personal non-commercial use, the SPDX line
   and `audioif/LICENSE` for the palette.
5. **Appendix E's S1 block gains C4 100 pF**, the value §1 uses for the Rat's
   feedback cap, which was in the source's BOM but missing from the list.
6. **Appendix E's S14 block now quotes the OCR literally** ("Q1-@3 2SC2240GA or
   28C3378GR") instead of a cleaned-up reading, since the row exists to show
   the OCR is unusable.
7. **§2's "attempted and failed" paragraph is rewritten to this run's own
   attempts.** The LM308 datasheet was re-tried from five hosts, including the
   LT/Analog PDF that S10 itself links, and reached from none; the
   `circuits-diy.com` claim was dropped because its URL was never recorded and
   this run could not reach it.
8. **The Rat-model search was re-run.** It confirms no white-box circuit model
   in the literature, and adds one fact worth having: recent black-box
   virtual-analog work does use a ProCo Rat as a training target, which is a
   proxy oracle under vision §4's fourth tier, not a model.

**What could not be reached.** The LM308 datasheet (five hosts, above); its
gain-bandwidth stays unsourced, and F2 keeps its wide band. ElectroSmash's
origin rights page — `electrosmash.com` does not resolve from this machine.
GEOFEX and `web.archive.org` were not attempted, per
`agent-knowledge/instrument-sources.md`, and are cited nowhere.

**Not touched:** §§4–8, which this audit may not edit. Three items there need a
later hand: §8 Q4's "the Phase 0 audit re-tries" is done, with the negative
result recorded in §2; §8 Q6's "the service notes' text (S13) was not
reachable" is superseded — the text is reachable, its id is S14, and the reason
Q6 stays open is OCR quality; and §8 Q1's deck now has one more job, settling
F2's levels between two derivations that disagree.

### G. The trait-critic pass (2026-09-06)

Independent pass over the Tier 2 table alone: is every row falsifiable as
stated, does each name a source, a confidence, a disconfirmation condition and
a measurement someone could actually run, and does each character carry at
least three of its own? Sources were **not** re-fetched here (Appendix F's
licence audit did that); what this pass did was re-derive every *derived*
number from the component values in §1, in code written from scratch, and then
ask of each measurement column: *could a person run this and get the number the
row claims?* **Rows after the pass: 11 — F1–F5, SC1–SC5, A1. None removed,
none added.**

**Everything re-derived reproduced.** The diode-pair Newton solve (both
1 kΩ and 2.2 kΩ, all six voltages and all four harmonic rows of Appendix A),
the Rat gain stage's three ideal-op-amp rows to 0.01 dB, F5's four Filter
corners and its three dB figures, SC2's 7.23 kHz, SC3's 0.964 V, and SC5's
whole nodal solve (centre minimum −15.41 dB at 645 Hz, 8.08 dB under the
100 Hz point and 8.51 under the 5 kHz one; bass end 21.37 dB of tilt, treble
end 14.82) — every one inside the last digit the seed prints. F2's
GBW-limited levels reproduced the **licence audit's** figures and not the
seed's, which is now recorded in the audit note under the table.

**The structural defect: five rows named a measurement nobody could run.**
F1, F2, SC1, SC2 and SC5 asked for a "pre-clip transfer" or a "small-signal
sweep". Unlike the Tube Screamer next door, where the dry signal passes at
unity and the pre-clip shelf is visible at the output, both of these circuits
put their diodes **to ground after all the gain**: at max Distortion the Rat's
own numbers give 2113× at 5 kHz, so even a −77 dBFS input arrives at the
clipper above its knee, and in 16-bit probe material −77 dBFS is two LSB. The
rows would have been marked "could not be measured" at Station C, or — worse —
measured at a convenient level and reported as a number that means nothing.
Two fixes, both using only figures already in this dossier:

- **An equal-drive contour** replaces the linear sweep wherever the gain is
  high (F1, F2, and SC1 at max Distortion). At each frequency the input level
  is bisected until the *output* peak reaches 0.298 V, which Appendix A's own
  row puts at 0.300 V of pre-clip drive (incremental diode gain 0.964); the
  pre-clip gain is then 20·log₁₀(0.300 / input peak). It reads the shaping at
  full 16-bit resolution, needs no access to an internal node, and is
  self-checking: run at two target voltages a factor of two apart it must give
  the same curve.
- **A stated level where a plain sweep still works** (F4, F5, SC2, SC5, and
  SC1 at Distortion 0). −48 dBFS through `scoop`'s fixed 35 dB booster puts
  0.22 V on the clipper, where Appendix A's incremental gain is 0.98;
  −20 dBFS through `filter` at Distortion 0 is F4's own 0.00 % THD point.

The same arithmetic gave F3 and SC2 their drive levels. F3 asked for "−20 and
−6 dBFS at max Distortion", which is 127 V and 500 V of pre-clip drive — not
the 1 V and 3.5 V the row is about; it now sets its level from F1's *measured*
1 kHz gain at pot 10 % (indicatively −42.2 and −31.3 dBFS), and SC2 the same
way from SC1's (indicatively −33.7 and −22.8 dBFS at Distortion 0). Both take
the level from the measurement rather than a table, because F2's bandwidth
moves the gain at that setting by up to 2.6 dB.

**F1 and F2 contradicted each other, and F1 would have failed a correct
build.** F1 stated *ideal-op-amp* gains and then disconfirmed itself on "100 Hz
within 8 dB of 1 kHz **at max Distortion**" — the one setting where F2 says the
op-amp's bandwidth dominates. Re-derived here at pot 1.00, the measurable
100 Hz→1 kHz tilt is **2.84 dB** at 0.32 MHz GBW and **7.58 dB** at 1 MHz,
against the ideal 13.84. Both are inside the old disconfirmation band: a
rebuild that implemented F2 exactly as this dossier asks would have been
reported as failing F1. The two rows are about different halves of the same
response and were being read at the same point.

The fix keeps both claims and separates where each is read. F1 moves to
Distortion ≤ 10 %, where the loop gain is high enough that the legs show
through — tilt 13.73 (ideal) / 16.27 (0.32 MHz) / 14.57 (1 MHz) at pot 0.10,
and 13.13 / 13.65 / 13.29 at pot 0.02, so an 11–18 dB band at the first and
11–17 at the second holds for every candidate — and it gains a second, cheap
clause that ties it to F2 rather than fighting it: *the tilt must fall as
Distortion is raised to maximum*. F2 keeps max Distortion and the equal-drive
contour, and its own disconfirmation (a peak above 1.5 kHz) is what catches a
build that left the bandwidth low-pass out, since the ideal network peaks at
4.9 kHz.

**SC1's prose contradicted SC1's numbers.** "A band-pass with poles at 3 and
600 Hz" reads as a passband from 3 to 600 Hz, which would put 100 Hz *above*
1 kHz. The row's own derived figures — 100 Hz 14.4 dB and 500 Hz 2.5 dB below
1 kHz — are returned only by two first-order **high-pass** corners at those
frequencies (re-derived here: 14.35 and 2.53 dB), and SC3's independent
0.96 V-at-−34 dBFS arithmetic agrees with that reading. The figures stand, the
wording is corrected, and because this pass did not re-read S5, §8 Q9 records
the open half: which of the two S5 eq. 15 itself states. Left as it was, a
rebuild could have implemented the words, built the opposite tilt, and passed
nothing while looking as if it matched.

**The other rewrites.** F3, F4, SC3 and A1 had one-sided disconfirmations —
"h2 above −40 dB", "THD below 8 %", "THD above 1 %" — that a build failing in
the other direction would sail through; each now carries the second bound, and
F3 and F4 gained a second operating point so the row tests the pair of numbers
it quotes rather than one. F3's h4 and h5 were claimed and never tested; they
are in the disconfirmation now. **SC4** was the sharpest case: its
disconfirmation was a condition on a *future SPICE run*, not on the build, so
no measurement of the rebuild could ever have failed it. It now states the
claim as a contrast — h2 at or above −30 dB at stock Asymmetry **and** at
least 20 dB above the same reading at Asymmetry 0 — which makes the
Asymmetry-0 reading a control that must pass, so the row cannot be met by a
build that is merely dirty everywhere; the SPICE condition stays, relabelled
as what it is, a revision of the claim rather than a failure of the build.
**A1** said "shared by both characters" without saying it is measured in each;
it does now, and both must pass.

**Not touched:** §§1–2 and 4–8 apart from adding Q9, and the Tier 1 and Tier 3
blocks, which were checked and not edited — Tier 1 is byte-identical to the
template's standard block, and Tier 3 carries both boards (P4 0.10, S3 0.25),
the zero-latency statement and "options that add latency: none".

**One thing this pass did not fix, for whoever owns §6.** The Distortion macro
law there reads "0 / 47 / 61 / 67 dB at 0 / 10 / 50 / 100 % of the
resistance", which are peak gains across frequency (Appendix A's 5 kHz column:
46.90 / 60.75 / 66.46), while F1 and F3 are stated at 1 kHz (42.14 / 56.08 /
62.09). Both are right about different things and the seed never says which a
knob position means. A dossier-wide convention — one frequency, named once —
would stop the implementation session guessing.

### App. I — Tier 1 invariants, the standard block

Verbatim from vision §3, moved out of §3 under the length rule. It is the
same block in every seed; a class-specific note on it is kept with it here.

- [ ] Silence in gives silence out; a decaying tail reaches exact zero — no
      held DC (the audioif#23 class of defect).
- [ ] `mix` at zero, or drive at zero, is a wire (byte-identical to source).
- [ ] Level-honest: unity through the dry path, no hidden gain.
- [ ] Reported `latency_samples` / `tail_samples` match what is measured —
      latency by a click against the dry path at 48 kHz and 44.1 kHz, tail
      by the burst-then-silence probe.
- [ ] `reset()` leaves every node the class built silent and stateless and
      the borrowed source untouched (planted faults: a delay line left full;
      an upstream instrument reset through a Filter- or Phaser-tailed chain).
- [ ] `deinit()` deinitialises every node the class built and leaves the
      source rendering (planted fault: an intermediate node left live).
- [ ] `capabilities` names exactly the optional behaviours the class honours
      (`"tempo_sync"` declared if and only if the transport is read).
- [ ] Pulling `output` allocates nothing.
- [ ] CPython and desktop MicroPython render identical bytes on the probe
      material, or the cause is recorded here; the P4 and S3 digests match
      the desktop's or carry a recorded cause (float width is the expected
      one, never the class).
- [ ] Rate-honest: designed and stated at 48 kHz; every invariant also holds
      at 44.1 kHz and 22.05 kHz; Hz-valued spans and options clamp below
      Nyquist at the running rate, never refuse; any Tier 2 trait that cannot
      hold at a lower rate is named here with why.
- [ ] Every invariant also holds at `channel_count` 1; a stereo-by-definition
      class states in §4 what a mono source gets (a wire, or the mono sum of
      its stereo behaviour), and the kit measures that statement.

**The wire is `mix` = 0.** In `filter`, Distortion at minimum passes a 100 mV
signal at unity with THD under 0.01 % (F4) but is not byte-identical — the
diode pair bends anything much above 0.35 V. In `scoop` Distortion at minimum
is never a wire at all: the fixed booster clips first (SC3). Both docstrings
say so. **At 22.05 kHz** F5's Filter clamps its open end below Nyquist (a
32 kHz corner cannot exist there) and A1 is stated over 20 Hz–11 kHz; every
other trait holds.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. ElectroSmash, "ProCo Rat Analysis" (MAS Effects mirror) | every Rat value and stated figure | "Some Rights Reserved, you are free to copy, share, remix and use all material." — **re-read verbatim on this page** by the licence audit 2026-09-06, and found on none of the other ElectroSmash pages this program has fetched. Two qualifications: it names **no licence**, and it reaches us through an unofficial mirror whose own footer disclaims ownership (the origin does not resolve here). A document read for topology and values; nothing reproduced | https://electrosmash.mas-effects.com/proco-rat.html | yes |
| S2. ElectroSmash, "Boss DS-1 Distortion Analysis" (same mirror) | every DS-1 value and stated figure | **License unverified — treated as copyleft.** Re-checked 2026-09-06: **no rights line on this page** — only the mirror's footer. S1's line is in the *Rat* article and is not here; the draft's "taken to cover this article too" was an assertion and is gone. Read for topology and values | https://electrosmash.mas-effects.com/boss-ds1-analysis.html | yes |
| S3. Wikipedia, "Pro Co RAT" | op-amp eras, diode types, the reversed Filter, the variants | CC BY-SA 4.0 — footer read this run: "Text is available under the Creative Commons Attribution-ShareAlike 4.0 License" | https://en.wikipedia.org/wiki/Pro_Co_RAT | yes |
| S4. Wikipedia, "Boss DS-1" | op-amp eras, ±0.7 V clipping, the 500 Hz scoop, the −12 dB loss | CC BY-SA 4.0 — same footer line, read this run | https://en.wikipedia.org/wiki/Boss_DS-1 | yes |
| S5. Yeh, Abel, Smith, DAFx-07, "Simplified, physically-informed models …" | the DS-1 stage by stage (eq. 15–19), the Newton-tabulated curve, the tone corners, the 220 Hz/100 mV test signal | "© 2007 D. T. Yeh. All rights reserved.", re-read this run on the author's index page <https://ccrma.stanford.edu/~dtyeh/papers/pubs.html>; the PDFs carry no rights text (grepped this run). **Not permissive**; a paper, math portable, no code copied | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_distortion.pdf | yes (WebFetch + pypdf) |
| S6. Yeh, Smith, DAFx-08 | the DS-1 common-emitter stage's design values and its *simulated* clipping asymmetry | as S5 (rights line at <https://ccrma.stanford.edu/~dtyeh/papers/pubs.html>; no rights text in the PDF — grepped this run) | https://ccrma.stanford.edu/~dtyeh/papers/yeh08_dafx_sim.pdf | yes (WebFetch + pypdf) |
| S7. Yeh, Abel, Smith, DAFx-07, "Simulation of the diode limiter …" | the static approximation's error bound and the anti-alias pre-filter | as S5 (rights line at <https://ccrma.stanford.edu/~dtyeh/papers/pubs.html>; no rights text in the PDF — grepped this run) | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_clipode.pdf | yes (WebFetch + pypdf) |
| S8. Nexperia 1N4148 SPICE model | the ten diode parameters used in every Newton solve here | no license text in the file (re-read in full this run; `curl` gets HTTP 403, `WebFetch` reaches it). Nexperia's Terms of Use (<https://www.nexperia.com/about/terms-and-policies/terms-of-use>, re-read this run) reserve all rights and permit reproduction "for personal non-commercial use only" — **not permissive**; the parameter values are facts about a part | https://assets.nexperia.com/documents/spice-model/1N4148.prm | yes |
| S9. `SharpSoundPlugins` / `Rodent.V2/TFGain.cs` | a value cross-check — agrees on legs and caps, uses a **150 kΩ** gain pot where S1 draws 100K; the Ruetz mod as a 47 Ω → 10 kΩ parameter | MIT, chased to the licence file itself and re-chased this run: `license.txt` is the MIT text, "Copyright (c) 2013 Valdemar Erlingsson" (<https://raw.githubusercontent.com/ValdemarOrn/SharpSoundPlugins/master/license.txt>), which the README's label agrees with. Permissive, readable; **nothing ported**, values compared only | https://github.com/ValdemarOrn/SharpSoundPlugins — values read at <https://raw.githubusercontent.com/ValdemarOrn/SharpSoundPlugins/master/Rodent.V2/TFGain.cs> | yes |
| S10. cushychicken, "Simulating the ProCo RAT … in LTSpice" | an independent LTspice study agreeing on 67 dB, ±0.65 V, 475 Hz–32 kHz and the op-amp speed limit | **License unverified — treated as copyleft.** The page's only rights text is its footer, read this run: "© <year> Wherein The Chicken" (the year is filled in by script). No licence is granted anywhere on it and the site has no terms page. Read as a document; nothing reproduced | https://cushychicken.github.io/ltspice-proco-rat/ | yes |
| S11. chrisgilroyrecords, "ProCo 'Ruetz' Rat Mod" | what the mod targets and what it does to the sound | **License unverified — treated as copyleft.** Re-checked this run: no licence, rights or copyright line anywhere in the page or its footer. Read as a document | https://chrisgilroyrecords.wordpress.com/2014/05/31/proco-ruetz-rat-mod/ | yes |
| S12. TI OP07C product page | GBW 0.6 MHz typ and slew rate 0.3 V/µs typ, from the page's own parameter table. *It does **not** say the part replaced the LM308 — that is S1's and S3's claim; re-confirmed this run, the strings "LM308" and "replacement" appear nowhere on it* | manufacturer product page: figures are facts, no licence granted — read-only | https://www.ti.com/product/OP07C | yes |
| S13. The palette, probed under `audiocomponents/.venv/bin/python` | every measured palette number in §4–§5 and Appendices B–D | MIT (this organization): SPDX line in the file, `audioif/LICENSE` | `audioif/src/shared/audioif_distortion.c` | yes (re-imported by the audit 2026-09-06) |
| S14. archive.org item `boss_DS-1_SERVICE_NOTES` (Boss's own DS-1 service notes, Dec. 1994) | nothing usable: the item and its OCR text were reached, but the OCR of the schematic and parts list is too degraded to read values from (C4's 250p OCRs as "2e0p"; no legible C7/C8 designators) | metadata API returns **no `licenseurl` and no rights field** — license unverified, treated as copyleft; read-only in any case | metadata <https://archive.org/metadata/boss_DS-1_SERVICE_NOTES>; text <https://ia800505.us.archive.org/35/items/boss_DS-1_SERVICE_NOTES/DS-1_SERVICE_NOTES_djvu.txt> | yes (both re-fetched this run: metadata HTTP 200, 7,803 bytes; text HTTP 200, 13,205 bytes) |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| F1 | **Two-leg pre-clip shaping.** The two feedback legs make the pre-clip gain rise with frequency — ideal-op-amp 48.2 / 62.1 / 66.5 dB at 100 Hz / 1 kHz / 5 kHz at max Distortion (*derived*, reproduced this run) — and the 100 Hz→1 kHz tilt is the legs, not the pot: 13.84 dB at pot 1.00 and 0.50, 13.73 at 0.10 (Appendix A). **It is measured at low Distortion**, because at max Distortion the op-amp's own bandwidth swamps the legs (F2) and drops the measurable tilt to 2.8–7.6 dB; at pot ≤ 0.10 both GBW candidates leave it at 13.1–16.3 dB (Appendix G). | S1 (values, 1539/60 Hz); S9, S10 | high — pure RC arithmetic | the 100 Hz→1 kHz tilt outside 11–18 dB at Distortion 10 %, or outside 11–17 dB at Distortion 2 % (bands this dossier's, wide enough for the ideal case and both GBW candidates: 13.73 / 16.27 / 14.57 and 13.13 / 13.65 / 13.29); or a tilt that does not fall as Distortion is raised to maximum | plain swept sine at Distortion 10 % and 2 %, at a level whose pre-clip peak stays under 0.30 V at every frequency (Appendix A's incremental gain 0.964): −57.4 and −43.5 dBFS, set by the 5 kHz gains 46.9 and 33.1 dB. Read 100 / 500 / 1000 / 2000 / 5000 Hz; Filter 0, Volume unity, Mix 1 |
| F2 | **The op-amp's bandwidth makes the mid hump.** With a single-pole open loop the max-Distortion response peaks **below 1 kHz** and is ≥ 12 dB down at 10 kHz relative to that peak. Both derivations of the levels agree on that band and disagree on the levels themselves — see the audit note below the table, which is why the row states only the band. | S1 (bandwidth: "Bandwidth and Slew Rate are proportional to 1/Ccompensation", and the 30 dB at 10 kHz figure); S10 — *S10 attributes the same high-gain HF rolloff to the **slew rate**, "That's the limitation imposed by the LM308's output slew rate", not to the bandwidth, so it corroborates the effect and not this trait's named mechanism (re-read on the page this run)*; S12 as successor cross-check | medium — the effect is sourced twice but by two different named mechanisms, the exact GBW is unsourced (§8 Q4), and the derived levels did not reproduce (note below) | a peak above 1.5 kHz — an ideal op-amp with no bandwidth limit peaks at 4.9 kHz and is 0.8 dB down at 10 kHz, which is the fault this row exists to catch — or 10 kHz less than 12 dB below the peak | **the equal-drive contour of Appendix G**, run at ⅓-octave steps from 100 Hz to 15 kHz at max Distortion — a plain sweep cannot be used here, nothing survives the clipper at 67 dB: at each frequency bisect the input until the output peak reaches 0.298 V, which Appendix A puts at 0.300 V of pre-clip drive, and take the gain as 20·log₁₀(0.300 / input peak), corrected for the Filter's 32.2 kHz response. Filter 0, Volume unity |
| F3 | **Hard symmetric clip to ground.** Output pins at 0.567 V for 1 V of pre-clip drive and 0.660 V for 3.5 V (*derived*, 1K into the pair; reproduced this run); h2 and h4 ≤ −60 dB; at 3.5 V a near-square, THD 32.9 %, h3 −11.2 dB, h5 −17.0 (ideal square −9.54 / −13.98). | S1 ("symmetric distortion"); S3; S10 ("+/-0.65V"); Newton with S8 | high | h2 **or h4** above −40 dB with matched diodes; output peak outside 0.55–0.60 V at 1 V of drive or 0.64–0.69 V at 3.5 V (the bands this dossier's); the peak rising more than 1.5 dB between them (derived +1.32 dB); h3 at 3.5 V outside −11.2 ± 2 dB, or h5 outside −17.0 ± 3 dB | 1 kHz sine at Distortion pot 10 %, with the input level **set from F1's own measured 1 kHz gain at that setting** so the pre-clip drive is 1.00 V and then 3.50 V — indicatively −42.2 and −31.3 dBFS at the ideal 42.14 dB, but the op-amp's bandwidth moves that by up to 2.6 dB, so the level comes from the measurement and not from the table (Appendix G); output peak at both, harmonic spectrum at the second. Filter 0, Volume unity |
| F4 | **Clean at minimum.** At pot zero the stage is unity and the diodes idle below about 0.35 V (incremental gain 0.964 at 0.30 V, 0.524 at 0.50): a 0.1 V peak passes at 0.00 % THD, 0.35 V at 0.45 %. This is what separates the Rat from the DS-1 (SC3) and from a Tube Screamer. | S1 ("Gvmin … =1 (0dB)"); Newton with S8 (reproduced this run) | high | THD above 1 % at −20 dBFS, **or outside 0.25–0.8 % at −9.1 dBFS** (0.35 V; derived 0.45 %, the band this dossier's) — the second point is what separates "unity below the knee" from "flat forever" | THD of a 1 kHz sine at −20 dBFS and at −9.1 dBFS, Distortion 0, Filter 0, Volume unity |
| F5 | **The Filter is first-order and runs backwards.** `1/(2π(1.5K + p·100K)·3.3 nF)`: 32.2 kHz at p = 0, 1820 Hz at 0.25, 936 at 0.5, 475 at 1 — darker clockwise. At p = 1: −7.35 / −12.72 / −20.48 dB at 1 / 2 / 5 kHz, i.e. 6 dB per octave, not 12 (all four corners and the three dB figures reproduced this run). | S1 (formula and span); S3 (direction); S9, S10 | high | the span missing 475 Hz or short of 16 kHz open; more than 9 dB between 2 and 5 kHz at p = 1 (second-order gives ≈15); brightening clockwise; or any quoted dB figure missed by more than 1.5 dB | magnitude response from a swept sine at Filter 0 / 0.5 / 1, at 1, 2, 5 kHz, **at Distortion minimum and −20 dBFS**, where F4 puts THD at 0.00 % so the reading is the Filter alone |
| SC1 | **Two gain stages, the first rising with frequency.** A fixed 35–36 dB booster whose two first-order corners at 3 Hz and 600 Hz put 100 Hz 14.4 dB and 500 Hz 2.5 dB below 1 kHz (*derived*; re-derived this run as 14.35 and 2.53 dB, which come out **only if both corners are high-passes** — the draft's "band-passed" is the opposite tilt and contradicted its own figures, §8 Q9 and Appendix G); then 0 → 26.5 dB whose input corner moves 72 → 3 Hz; about 61.5 dB total at maximum. SC3's 0.96 V at −34 dBFS is the same arithmetic and agrees. | S2; S5 (eq. 15–16) — the *shape* above is stated from the figures, which this run reproduced; S5's own wording was not re-read in this pass | high for the figures; medium for the naming, pending §8 Q9 | total pre-clip gain at max Distortion outside 55–68 dB; the booster's 100 Hz within 8 dB of its 1 kHz, or its 500 Hz more than 5 dB below it; or 100 Hz reading **above** 1 kHz at any setting — the band-pass reading of the same two corners, and the fault this row catches | at Distortion 0 a plain swept sine at −48 dBFS (35 dB puts 0.22 V on the clipper, incremental gain 0.98); at Distortion max, Appendix G's equal-drive contour. Read at 100 / 500 / 1000 Hz, Tone centre, SC5's response and SC2's pole divided out |
| SC2 | **Hard symmetric clip under a 7.2 kHz cap.** 2.2K into the pair with 0.01 µF across it (1/(2π·2.2K·0.01 µF) = 7.23 kHz, reproduced this run): ceiling 0.532 V (1 V in) to 0.622 V (3.5 V in); below the diode threshold the stage is a first-order low-pass at 7.2 kHz, which the conducting diodes short. | S2; S5 Fig. 8; S4 (±0.7 V); Newton with S8 | high | the small-signal output magnitude matching SC5's tone response **alone** within 1.5 dB at 14 kHz, i.e. no 7.2 kHz pole present at all; the ceiling outside 0.51–0.56 V at 1 V of drive or 0.60–0.65 V at 3.5 V (the bands this dossier's), or rising more than 1.5 dB between them (derived +1.35 dB); h2 or h4 above −40 dB with Asymmetry at 0 | swept sine at −48 dBFS, Distortion 0, Tone centre, compared point by point against the prediction (SC5's tone network × a first-order 7.23 kHz pole), 1.5 dB from 200 Hz to 16 kHz; output peak on a 1 kHz sine at Distortion 0, the level set from SC1's measured 1 kHz gain so the pre-clip drive is 1.00 V and 3.50 V (indicatively −33.7 and −22.8 dBFS at the derived 33.7 dB); harmonic spectrum at max Distortion, Asymmetry 0 |
| SC3 | **Never clean.** The booster alone drives a 20 mV (−34 dBFS) 1 kHz input to about 0.96 V at the clipper, leaving about 18 % THD *with Distortion at minimum* (*derived*; both halves reproduced this run — 0.964 V from SC1's corners, 18.0 % from Appendix A's 2.2 kΩ row at 1 V). | S2; S5 (first-stage distortion "not negligible") | high | THD below 8 % **or above 30 %** at −34 dBFS with Distortion at minimum — the upper bound is this dossier's, so a build that merely distorts everything cannot pass a trait about how much | THD of a 1 kHz sine at −34 dBFS, Distortion 0, Tone centre, Asymmetry 0 |
| SC4 | **Even harmonics from the asymmetric front end.** The common-emitter stage clips asymmetrically at guitar levels, so `scoop` carries even harmonics `filter` does not: h2 at or above −30 dB re fundamental on a 220 Hz, −20 dBFS input at max Distortion with Asymmetry at stock, **and at least 20 dB above what the same measurement gives with Asymmetry at 0** (F3's matched pair puts that at ≤ −60 dB). | S2 ("Q2 asymmetric clipping gives rise to even-order harmonics"); S6 §3.3.3 (simulated: "one polarity clips at a lower level than the other") | medium — mechanism sourced twice; the −30 dB level is proposed pending §8 Q1's deck | h2 below −30 dB at that point, or within 20 dB of the Asymmetry-0 reading. (Separately: if §8 Q1's deck with a 2SC2240 model puts the circuit's own h2 below −40 dB, the row is re-stated at the simulated level or dropped with cause — that is a revision of the claim, not a failure of the build) | harmonic spectrum of a 220 Hz sine at −20 dBFS, max Distortion, **at Asymmetry stock and at Asymmetry 0** — the second reading is the control that must pass, so the row cannot be met by a build that is simply dirty everywhere |
| SC5 | **The scoop.** At centre the response has a minimum between 500 and 750 Hz sitting 6–10 dB below both the 100 Hz and 5 kHz points (*derived*, full nodal solve into a 100K load: −15.4 dB at 646 Hz against −7.3 and −6.9; an independent solve this run returns −15.41 dB at 645 Hz, 8.08 dB under 100 Hz and 8.51 under 5 kHz). At the bass end 5 kHz is 21.4 dB below 100 Hz (re-solved 21.37); at the treble end 100 Hz is 14.8 dB below 5 kHz (re-solved 14.82). | S2 (its "-20db (500Hz)" against a "-12dB overall" reference is an 8 dB depth, which the solve reproduces at 8.1); S4; S5 §3.5 | high for shape and depth; medium for the exact frequency (S2 and S5 differ by loading) | a centre notch shallower than 4 dB or outside 400–800 Hz; either extreme with under 12 dB of tilt from 100 Hz to 5 kHz; or any read point more than 2 dB from the composite prediction | magnitude response at Tone −1 / 0 / +1, read at 100 / 500 / 646 / 1000 / 5000 Hz, **swept at −48 dBFS with Distortion at minimum** so the clipper is linear; the prediction is the tone network above **times SC2's 7.23 kHz pole**, which puts the 5 kHz points 1.7 dB under the figures quoted |
| A1 | **Alias floor.** Inharmonic energy in a 1010 Hz sine at max Distortion and −20 dBFS is ≥ 60 dB below the fundamental over 20 Hz–20 kHz. Set 20 dB under S7's static-approximation error so aliasing is never the dominant error of a near-square at 48 kHz. Measured **once per character**, and both must pass; `filter` is the harder of the two, its clipper being a near-square (F3). | S5–S7 (8× is standard); the bar is this dossier's | medium (the bar is a design choice) | inharmonic energy above −60 dB at that point in **either** character, on **any** target, the P4's single-precision build included | sum of every FFT bin more than two bins from a harmonic of 1010 Hz and from DC, against the fundamental's bin; 4800 samples at 48 kHz, no window (101 exact periods, so every harmonic lands on a bin) |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**The DS-1 service notes are reachable** (a correction to the draft, which
recorded a 404): the item's file is named `DS-1_SERVICE_NOTES_djvu.txt`, not
`boss_DS-1_SERVICE_NOTES_djvu.txt` — identifier and filename differ. It is
source **S14** above, re-fetched by this run. It still does not settle §8 Q6,
but for a different reason than the draft's: the OCR of the parts list is
illegible, not unreachable. Detail in Appendix F.

*(from §2)*

**Attempted and not reached — the LM308 datasheet.** §8 Q4 asks the Phase 0
audit to re-try it; it did, on 2026-09-06, from five hosts, and reached none:
`ti.com/lit/ds/symlink/lm108-n.pdf` 404, `ti.com/product/LM308` 404,
`alldatasheet.com` 403, and the LT/Analog `lt0108.pdf` that S10 itself links
(`curl` HTTP/2 stream error; `WebFetch` 60 s timeout). A web search returns an
800 kHz unity-gain figure in snippet text; a snippet is not a source anyone
read, so it is **not** cited here or in F2. **The LM308's gain-bandwidth stays
unsourced**, and F2 is stated across both candidate values. (The draft's
`circuits-diy.com` claim is dropped: its URL was never recorded and this run
could not reach it.) **ElectroSmash's own rights page** was re-tried at
`www.electrosmash.com/rights` and `electrosmash.com/rights`; neither host
resolves here. **Not attempted, and therefore not cited:** GEOFEX and
`web.archive.org`, both recorded in `agent-knowledge/instrument-sources.md` as
unreachable from this machine. **Looked for and not found:** a published
circuit model of the Rat — re-searched this run over DAFx/AES/CCRMA; what
exists is black-box virtual-analog work that uses a Rat as a *training target*,
not a derivation of its circuit, so the Rat's references stay hobbyist (S1,
S10) and open-source (S9). **No copyleft source was ported or read for
structure**; S9, the one code source, is MIT and its values were compared, not
copied.

*(from §3)*

Voltages are the circuits'; the rebuild works in normalized units under the
mapping **0 dBFS ≡ 1.0 V peak at the input jack** (shared with `Overdrive`,
§8 Q2), so 20 / 100 / 500 mV read −34 / −20 / −6 dBFS. Numbers marked
*derived* come from this run's analytic solution of the stated network with an
ideal op-amp; the clippers from a Newton solution of
`(Vin − Vo)/R = 2·IS·sinh(Vo/(N·Vt))` with S8's IS and N. Appendix A carries
the tables. Character trait ids are prefixed so they never collide with the
source ids: **F** for `filter`, **SC** for `scoop`.

*(from §3)*

**Audit note on F2's numbers (2026-09-06).** The seed derived 52.1 dB at 411 Hz
(22.1 dB down at 10 kHz) at 0.32 MHz GBW and 56.3 dB at 717 Hz (16.6 dB down)
at 1 MHz. The licence audit re-derived the same circuit independently, in
complex arithmetic, and got **62.1 dB at 448 Hz (32.0 dB down)** and **64.6 dB
at 798 Hz (24.8 dB down)** — the loop crosses over with 32°/41° of phase
margin, so it peaks *above* the ideal curve, not under it. Both derivations
agree on 30.0 dB at 10 kHz (S1's own figure), on a peak below 1 kHz and on more
than 12 dB of drop, **so the trait as stated survives and only the levels are
in doubt**; they are recorded as *not reproduced* rather than corrected in
place, and §8 Q1's deck settles them. The ideal-op-amp half reproduced exactly
(peak 66.5 dB at 4932 Hz, 0.8 dB down at 10 kHz). Method, and the
magnitudes-versus-phasors reading of the gap, are in Appendix F.
*Trait-critic pass, 2026-09-06:* a **third** independent derivation of the same
network, written from the values in §1 alone, returns 62.13 dB at 448 Hz
(32.1 dB down at 10 kHz) at 0.32 MHz and 64.75 dB at 797 Hz (24.9 dB down) at
1 MHz, and 66.47 dB at 4933 Hz (0.75 dB down) ideal — i.e. it reproduces the
audit's figures, not the seed's, and its 0.32 MHz reading at 10 kHz is
30.04 dB against S1's own "no more than 30dB". Two of three derivations now
agree; the levels stay recorded as *not reproduced* until §8 Q1's deck, and the
row's band is unaffected.

*(from §3)*

**Recorded as unmeasured, not a trait: the LM308's slew rate.** S1's own
5.3 kHz figure assumes a 9 V peak a 9 V single supply cannot deliver; for the
diode-limited ±0.66 V output an edge at 0.3 V/µs takes 4.4 µs, under one sample
at 48 kHz. Whether it audibly changes which zero crossings the diodes see in a
two-tone signal is what §8 Q3's deck decides; the *bandwidth* half of the same
capacitor is F2 and is measurable.

*(from §3)*

**Trait-critic pass, 2026-09-06.** Rows after the pass: **11 — F1–F5
(`filter`), SC1–SC5 (`scoop`), A1 (both)**; none removed, none added, none
newly unmeasured, and each character keeps five of its own. Every *derived*
figure reproduced under an independent re-derivation. Two defects were
structural: five rows asked for a "pre-clip transfer" through a circuit whose
point is that nothing reaches the output unclipped, and SC1's prose named a
shape its own numbers contradict. Appendix G carries both.

*(from §3)*

Budget as a fraction of one stereo block's deadline (256 frames at 48 kHz =
5.33 ms, `audioif_multiply.h:24`): **ESP32-P4 0.10, ESP32-S3 0.25** — above
`Overdrive` because both characters carry two shaped gain legs and a
block-updated bandwidth low-pass, and `scoop` adds a second nonlinearity (the
booster) ahead of the clipper. Lean patch expected: **yes** on the S3, the
oversampling factor being the knob. RAM: two waveshaper tables (booster,
clipper) plus five biquad states.

*(from §3)*

**Latency (vision §9a): algorithmic latency zero — 0 samples, 0.00 ms at
48 kHz.** Neither circuit looks ahead; every block is a filter, a memoryless
curve or a mixer sum. The only thing that could add latency is §5's waveshaper
anti-aliasing, so the ask requires minimum-phase IIR interpolation and
decimation; a linear-phase FIR decimator would add its group delay and is
refused. **Options that add latency: none.** `tail_samples` = 0. Reported
`latency_samples` = 0, verified by the click measurement at the class gate.

*(from §4)*

```
source ─ Splitter(3) ─ tap0 ×1 ─────────────────────────────┐
                     ├ tap1 ─ HP(60 Hz)   ─ ×Rf/560 ────────┤ Mixer
                     └ tap2 ─ HP(1539 Hz) ─ ×Rf/47  ────────┘
   → LP(GBW/G, block-rate) → rail clip → diode curve → Filter LP → Volume
```

*(from §4)*

`1 + Zf/Zs = 1 + (Rf/560)·HP60 + (Rf/47)·HP1539` exactly — each leg is a
first-order high-pass times a constant — so the shaping is a three-way sum
through `audioroute.Splitter` (`upstream-diff.md:661`; four taps,
`audioif_splitter.h:21`) and `audiomixer.Mixer`, and the op-amp's bandwidth is
a first-order low-pass at `GBW/G` whose coefficient Python updates on a
Distortion move (F2). **`scoop`:** HP(3 Hz) → band-pass (poles 3/600 Hz) × 56 →
an *asymmetric* curve (SC4) → HP(72→3 Hz, block-rate) × (1..22.3) → rail clip →
LP(7.2 kHz) → diode curve → Splitter(2) → [LP 234 Hz, HP 1063 Hz] → Mixer with
complementary levels (Tone) → Level. A mono source gets exactly these graphs;
neither character is stereo by definition.

*(from §4)*

Measured on the palette this run (S13; Appendices B–D): its fixed curves fit
the Newton diode curve to 0.015–0.017 V rms over ±1 V and land within 1.2 dB at
h3 and 2.5 dB at h5, so **F1, F2, F4, F5, SC1, SC3 and SC5** are reachable by
composition — the shaping is exact sums of first-order sections, and a
two-real-pole biquad with its second pole parked at 40 kHz tracks a first-order
response within 0.51 dB to 8 kHz, which is what F5 and SC5 measure.
The Tier 1 wire is `mix` **exactly 0**, not `mix ≤ 0.01`: the `mix <= 0.01`
copy branch is the MicroPython / CircuitPython binding's alone
(`audiofilters/Distortion.c:244-251`) and the CPython build does not run that
binding — its shim calls the shared kernel (`src/cpython/audiofilters.py:163` →
`audioif_distortion.c:47`), which has no such branch. Measured this run on the
same graph: at `mix = 0.005` and `mix = 0.01` MicroPython
(`cmods/bin/micropython`) returns the source bytes unchanged while CPython
mixes, 306 counts of difference at `mix = 0.01` on a 20000-count sine; both
agree at `mix = 0` and both differ at `mix = 0.02`. The bottom 1 % of a `Mix`
macro is therefore a Tier 1 cross-runtime divergence of the **ported node**,
and the rebuild reaches the wire by not building the branch, never by leaning
on the ≤ 0.01 shortcut. The `OVERDRIVE` curve is fixed but genuinely
asymmetric — re-measured on the bare node this run at 1010 Hz, −20 dBFS,
`soft_clip` off and no post-gain: **h2 −37.1 dB against h3 −44.4 at unity,
h2 −26.9 against h3 −37.4 at +12 dB of pre-gain**, the even harmonic 7–10 dB
*above* the odd one. (The draft's −37.7/−37.0 and −27.4/−33.6 are the *old
class's whole chain* — `OVERDRIVE` with `soft_clip` on and the `_push`
post-gain, reproduced here as −37.5/−38.6 and −27.3/−34.5 — not the palette
curve on its own; §7's numbers are that chain and stay as they are.) So the
curve is a usable stand-in for SC4's mechanism, and a stronger one than the
draft claimed, though its amount is not a knob. What the palette does **not**
reach is A1, the knee's high-order detail in F3 and SC2, and — new from the
palette verifier — the **3 Hz corner** `scoop` asks of a `synthio.Biquad`: §5.

*(from §4)*

**audioif#23 lands on this class, and hard.** Burst-then-silence through
`audiofilters.Filter`, measured this run at 48 kHz, Q = 0.707: HIGH_PASS at **3 Hz holds
−789 counts of DC for ever** (2.4 % of full scale, −32 dBFS), 10 Hz holds 71,
30 Hz 8, 60 Hz 2, 72 Hz 1, and everything at 234 Hz and above settles to exact
zero. The `filter` graph is nearly clean — its 1539 Hz leg reaches 0, its 60 Hz
leg 2 counts — but `scoop` as drawn puts a 3 Hz pole in the booster's band-pass
*and* sweeps its input high-pass 72 → 3 Hz, so it fails Tier 1's "a decaying
tail reaches exact zero" by three orders of magnitude, and a −32 dBFS DC step
sitting in front of a hard clipper biases SC4's asymmetry as well. Two answers,
in compose-first order: (i) **do not build the 3 Hz section at all** — it is a
DC blocker in a circuit that has a bias rail, and a digital graph has none; over
20 Hz–20 kHz it is within 0.10 dB of a wire (0.10 dB at 20 Hz, 0.016 at 50 Hz,
0.004 at 100 Hz — SC1's own figures start at 100 Hz), so SC1 loses nothing by starting
the booster's band-pass at its 600 Hz pole alone and letting the *input*
high-pass stop at its 72 Hz end. (ii) If Station A shows the sweep must reach
below ~100 Hz to make SC1's tilt, it needs the DC-clean biquad — §5 A2.

*(from §4)*

Python computes the two leg gains and the bandwidth corner per Distortion
position, the Newton tables for the diode stage of both characters and the
booster's asymmetric curve, and the Filter and Tone coefficients — all on
CPython, shipped as data, never rebuilt on a board. C runs per sample: splitter
copies, three to five biquads, one or two table lookups at the oversampled rate
with the decimation, mixer sums.

*(from §5)*

*Palette-verifier refutation pass, 2026-09-06.* Measurement (b) was re-derived
independently from the Newton solve and the least-squares fit and came back the
same to 0.2 dB (`soft_clip` h7 −36.4 for the Rat's clipper and −35.1 for the
DS-1's, against the clippers' own −47.9 and −58.6; `tanh` −42.7 against the
draft's −42.9, a fit-grid difference); measurement
(a)'s Appendix D rows re-measured identical. The `CLIP` wrap was re-measured
too: 10 of 480 samples at −32768 with +20 dB of pre-gain, 230 of 480 at +40 dB.
Two compose-first routes were then tried and **both refuted**:

*(from §5)*

- **Oversample by composing `audiospeed.SpeedChanger`.** The palette carries a
  rate changer, so ×4 could be `SpeedChanger(rate=0.25)` → `Distortion` →
  `SpeedChanger(rate=4.0)`. Measured on the same 1010 Hz / −6 dBFS probe whose
  base-rate `soft_clip` floor is −50.9 dB, the composed chain reads **−6.9 dB**,
  44 dB *worse*: `SpeedChanger` is a zero-order hold with no interpolation and
  no decimation filter (`src/cpython/audiospeed.py:56-66`), so the upsample adds
  hold images and the downsample folds them back. It is a CircuitPython port
  (`src/audiospeed/SpeedChanger.c:1`) and may never gain an interpolator.

*(from §5)*

- **Build the curve from `audiomath.Multiply` instead of a table.** `Multiply`
  takes two arbitrary streams (`src/cpython/audiomath.py:29-31`), so a
  `Splitter` feeding both inputs is x² and a chain of them is an odd polynomial
  — which would pass an alias test on a single tone, since an order-N polynomial
  makes no harmonic above N·f. It fails on the clipper's own shape: a polynomial
  does not saturate, and F3 and SC2 are stated on a *near-square* knee at
  3.5–10 V of drive. Fitted to h3 = −12.6 dB / h5 = −18.4 dB at one level,
  `f(u) = u − 1.4504·u³ + 0.8348·u⁵` runs to 53.3 % THD and an output peak
  8204× its input two decades up, where both clippers hold their output inside
  0.66 V (Appendix A). No composition of `Multiply` reaches a limiter.

*(from §5)*

**A2 — a DC-clean biquad in an audioif-own module (the vision §6 / Gate 0
candidate), if `scoop` keeps a corner below ~100 Hz. Traits: Tier 1 (no held
DC); SC1.**
*The palette instead* runs `synthio.Biquad`'s int32 fixed-point state, which
sticks at low W0 (audioif#23). *The measurement:* §4's table — 3 Hz holds −789
counts for ever, 10 Hz 71, 30 Hz 8, 60 Hz 2, 72 Hz 1, ≥234 Hz exact zero.
*Refutation record (Phase 0, palette verifier):* **partly refuted, and the
refutation is the preferred answer.** The 3 Hz pole is a DC blocker with no job
in a digital graph and drops out at a cost of 0.10 dB at 20 Hz and 0.004 dB at
100 Hz (§4 (i)); with it gone the class's lowest corner is the input high-pass's 72 Hz
end, where the residue is 1 count. One count is still not exact zero, so this
class does not *close* audioif#23 — it **inherits whatever Gate 0 decides for
the EQ family and the Phaser** (roadmap Phase 0) and asks for no separate node.
An ask survives only if Station A shows SC1's tilt needs the sweep below about
100 Hz. Not shared: `Overdrive` measured clean at every corner it uses.

*(from §5)*

No ask for the pre-clip shaping (the three-way `Splitter` + `Mixer` sum is
exact), for the op-amp bandwidth (a block-updated biquad), for first-order
sections (0.51 dB to 8 kHz), or for the booster's asymmetry (a second table on
the same node). The `Splitter` + `Mixer` sum was re-verified this run: with
`taps=3`, tap 0 through `audiomixer.Mixer` at level 1.0 is byte-identical to
the source and keeps a click on its original frame — unity and zero latency on
the unshaped leg, which is what Tier 3's `latency_samples` = 0 rests on.

*(from §7)*

- `drive.py:97-99` — `mode=_DM.CLIP, drive=0.7`: through the kernel's
  `drive = 1.0001 − drive` (`audioif_distortion.c:57`) and `pow(fabs(value),
  drive)` (`:17`) that is a **power-law expander with exponent 0.3, not a
  clipper**. Measured on the shipped settings: a −60 dBFS input leaves at
  −22.2 dBFS, and THD is 24.5 / 25.4 / 25.4 / 25.4 % at −60 / −40 / −20 /
  −6 dBFS. There is no linear region at all — F4 is impossible — and the noise
  floor rises by 37.8 dB.

*(from §7)*

- `drive.py:99` — `pre_gain=6.0` with `post_gain=-6.0` is a fixed operating
  point: nothing about how hard the curve is driven is reachable from outside,
  and the compensation hides it.
