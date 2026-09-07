# Effects Dossier — `AnalogDelay` (Boss DM-2; Electro-Harmonix Deluxe Memory Man)

**Class:** `lib/audioeffects/delay.py` — read once, for §7.
**Family / phase:** Time, roadmap Phase 5
**Standout:** both pedals, per vision §4.2 — **confirmed, and split into two
characters** on the one thing that separates them: the DM-2 is one 4096-stage
bucket brigade (S5, S6), the Deluxe Memory Man is **two MN3005s in series**,
8192 stages (S1, read off the drawing). Because a BBD's delay is
`N/(2·f_clk)`, the same delay time puts the two at clocks an octave apart, and
everything downstream of the clock moves with it.
**Grade:** **circuit.** A full schematic with component values was read (S1 —
one page image, read in three tiles), the BBD's own datasheet gives the stage
count and clock range (S2), and the delay law is derived analytically and
cross-checked against two datasheets' published delay ranges to the digit
(Appendix A). The Phase 0 audit re-read S1 independently and confirms the four
load-bearing readings (two MN3005s in series through a 2N5087 follower; the
CD4047 with 240 pF / 5.6 kΩ / 100 kΩ DELAY; NE570 compressor in and expander
out; feedback taken at the expander's output and returned at the compressor's
input), and adds the DM-2's own drawing as **S8**, so both characters now rest
on a schematic rather than one of them on a stage count.
**Portability tier:** needs audioif-own nodes (`audioecho.FeedbackDelay`)
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

A bucket brigade is a chain of `N` capacitors handing charge along on a
two-phase clock — a **fixed-length delay line running at its own, movable
sample rate**, so the delay is `N/(2·f_clk)` (S4 eq. 34; confirmed to the digit
by S2's and S3's own published ranges, Appendix A). The knob is therefore a
**clock**, not a length: in the Deluxe Memory Man a CD4047 astable with a
240 pF cap and a 100 kΩ DELAY pot in series with 5.6 kΩ, its complementary
Q/Q̄ outputs clocking both BBDs at half the oscillator rate (S1; S7 for the
half-rate relation). Around it sit the two things a BBD cannot do without.
**Filters**: the chain samples, so it needs an anti-aliasing low-pass in front
and a reconstruction low-pass behind — typically 30 or 36 dB per octave with a
−3 dB point around 3 kHz (S3), a fifth-order low-pass plus a first-order
high-pass on each side in a measured circuit (S4 §4), built in the Memory Man
from cascaded 4558 sections around 2.7 nF and 16 kΩ (S1). **Companding**: an
NE570 compresses into the line and expands after it (S1, both halves of one
chip), because the line's noise sits 75 dB below a 0.9 Vrms signal that already
carries 2.5 % THD (S2). The output stage is a sample-and-hold, so the wet path
carries a `sinc(f/f_clk)` roll-off that **moves with the delay time** (S4 eq.
34/37) — a sliding band limit on top of the fixed one. Feedback is taken
**after** the expander and returned **before** the compressor (S1), so every
pass is a fresh compress-line-expand rather than one shared by all repeats.
The Memory Man's op-amp LFO modulates the **clock**, not the delay
(S1), so the delay follows the reciprocal of the clock law and chorus and
vibrato are two depths on one modulation. (The drawing prints no waveform
label: it shows two 4558 stages, an integrator and a comparator, which is a
triangle-and-square oscillator by topology — an inference, not a stated
fact.)

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Electro-Harmonix *Deluxe Memory Man* schematic (image-only PDF … (App. S1) | the whole signal path with values … (App. S1) | **license unverified … (App. S1) | https://experimentalistsanonymous.com/diy/Schematics/Delay%20Echo%20and%20Samplers/Deluxe%20memory%20man.pdf | yes, read as images — every claim above re-read in the audit. *One correction:* the drawing labels no LFO **waveform**; "triangle" is read from the integrator-plus-comparator topology, not printed, and is marked as inference here and in §1 |
| **S2** MN3005 *4096-Stage Long Delay BBD* product specification … (App. S2) | 4096 stages; clock **10–100 kHz** … (App. S2) | vendor product specification … (App. S2) | https://xvive.com/audio/wp-content/uploads/sites/2/2021/11/Xvive_MN3005_BBD_DATASHEET.pdf | yes, full text — re-downloaded and re-extracted in the audit; every figure in this cell re-checked against the datasheet's own tables |
| **S3** ElectroSmash, *Bucket Brigade Devices: MN3007* … (App. S3) | MN3007 1024 stages, clock 10–100 kHz … (App. S3) | mirror footer: "An unofficial … (App. S3) | https://electrosmash.mas-effects.com/mn3007-bucket-brigade-devices.html | yes — re-fetched in the audit, including the formula image |
| **S4** Holters & Parker, *A Combined Model for a Bucket Brigade Device … (App. S4) | the BBD as a **fixed-length … (App. S4) | **no rights statement printed** anywhere in … (App. S4) | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2018/09/Holters-Parker-2018-A-Combined-Model-for-a-Bucket-Brigade-Device-and-its-Input-and-Output-Filters.pdf | yes, full text — re-downloaded and re-extracted in the audit; eq. 34, the fig. 8 sentence, the "N/2 clock periods" line and the Juno-60 filter orders are all verbatim |
| **S5** Aion FX, *Amethyst Analog Delay* (DM-2 project documentation) | MN3005/MN3101 or MN3205/MN3102 chipset … (App. S5) | "Trademarks and brands are the property of … (App. S5) | https://aionfx.com/project/amethyst-analog-delay/ | yes — re-fetched in the audit; the "around 300ms of delay time when properly calibrated" and compander quotes are verbatim |
| **S6** next.gr, Boss DM-2 schematic page | first version MN3005 + MN3101; later MN3205 + MN3102 … (App. S6) | "© 2025" site footer with Terms of Use / … (App. S6) | https://www.next.gr/boss-dm-2-delay-guitar-pedal-schematic-diagram | yes (text only) — re-fetched in the audit; both IC-version sentences and the 0.8 %/1 % THD comparison are verbatim |
| **S7** TI, CD4047B product page | "The OSCILLATOR output period will be half of the Q … (App. S7) | manufacturer product page carrying no … (App. S7) | https://www.ti.com/product/CD4047B | yes — re-fetched in the audit; the OSCILLATOR/Q sentence is verbatim and the page still carries **no** R·C formula |
| **S8** hobby-hour.com, *Boss DM-2 Delay pedal schematic diagram* … (App. S8) | the DM-2's published specification ("Delay Time: … (App. S8) | **license unverified … (App. S8) | https://www.hobby-hour.com/electronics/s/dm2-delay.php (image: `…/electronics/s/schematics/dm2-delay-schematic.png`) | **yes** — 200 with an ordinary browser user-agent. The earlier "403, not reached" was a user-agent block, not a dead page |

**Looked for, not found:** the CD4047 astable formula, so the DMM's
clock range is **not** claimed anywhere in this dossier (the arithmetic is in
Appendix B, flagged unsourced); and **Raffel & Smith, *Practical Modeling of
Bucket-Brigade Device Circuits*, DAFx-10** — the other standard BBD paper —
which downloaded from both dafx.de and its Hamburg mirror but whose embedded
fonts carry no usable character map, so every digit and most letters extract
scrambled. It is recorded as **not reached**, and the audit re-tested it: it
downloads again (200, 447 850 bytes) and extracts the same scramble
("Procﬁ of the 25 th Intﬁ Conference … uDAFxz21vy Grazy Austria" where the
paper reads "13th Int. Conference … (DAFx-10), Graz, Austria"). Nothing in this
dossier comes from it; Station A should try an HTML rendering or an author's
copy before relying on it.

Copyleft sources are measured or read as
papers, never for code structure (vision §5); nothing here was read for code.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Characters `"single-line"` (`N = 4096`, DM-2) and `"double-line"`
(`N = 8192`, Deluxe Memory Man). They share T1, T2a, T2b, T3, T4 and T5 with
`N` as a parameter; T6 is the row where they must differ, and each character
is measured on its own rows — one passing cannot cover the other.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1** | the Time control is a **clock**: `T = N/(2·f_clk)` with `N` fixed. The falsifiable content is that the arrival time and the band limit are locked by that one law, so with `f_clk` recovered **from the wet magnitude's first null** — never from the −3 dB corner, which the control law itself sets — the product `T_arrival · f_clk` is `N/2` to **±1 %** at every Time setting where the null is in band | S4 eq. 34; S2's own 20.48–204.8 ms over … (App. T1) | high | `T·f_clk` outside `N/2 ±1 %` at any Time setting whose null is in band; or a build in which the null does not move as `1/T` | delay tracking: impulse at Time = … (App. T1) |
| **T2a** | the wet path's high-frequency corner **tracks the delay time**: −3 dB at `0.4422·f_clk = 0.2211·N/T`, so doubling Time halves the corner, within **±10 %**. At Time = 300 ms that is **3019 Hz** single-line and **6038 Hz** double-line (Appendix A) | S4 eq. 34/37, read in full this run … (App. T2a) | high | a corner that does not halve to ±10 % when Time doubles, or that is more than 10 % from `0.2211·N/T` at any setting — a fixed `damping_hz` fails both | swept-sine magnitude of the wet … (App. T2a) |
| **T2b** | that roll-off is a **sinc, not a pole**: `\|H\| = \|sinc(f/f_clk)\|`, −3.92 dB at `f_clk/2` and a **null at `f_clk`** at least **20 dB** deep. Measured as the **ratio of two sweeps an octave apart in Time**, which cancels T5's fixed filter pair exactly and needs no filter estimate: `\|H_T\|/\|H_2T\|` matches `sinc(f/f_clk)/sinc(2f/f_clk)` to **±1 dB** from 100 Hz to `0.45·f_clk` | S4 eq. 34/37 — eq. 37 is explicit that the measurable magnitude is `sinc·\|H_in\|·\|H_out\|`, which is why the raw sweep cannot be fitted against the sinc alone | high | a sweep ratio more than 1 dB from the sinc ratio over that band; or a first null under 20 dB deep, or absent. A one-pole in place of the hold is **5.1 dB** away at 300 ms and has no null at all (Appendix C) | the T2a sweeps at Time = 300 and 600 ms, single-line; take their dB difference, fit against the sinc ratio, report worst dB error over 100 Hz–0.45·f_clk and the depth of the null in the raw 300 ms sweep |
| **T3** | a **change of Time glides in pitch**, on the speed-type law: S4's own account of fig. 8 is that "the effective pitch of the output of the BBD compared to its input depends on the ratio of `f_BBD` between the instant when the signal was sampled by the BBD and when it exits" — so the arithmetic is `TapeDelay` T1a's exactly. A Time step 200 → 100.4 ms holds a constant **+1193 cents for 100.4 ms** and then returns to unity within **±2 cents**, with no sample-level discontinuity anywhere | S4 §4 and fig. 8, quoted verbatim from the paper read this run; the ratio and the duration derived in `TapeDelay.md` Appendix D | high | any Time move producing a sample-to-sample jump larger than the probe tone's own maximum slope; an offset more than 10 cents from +1193; or a hold more than 5 % from 100.4 ms | as `TapeDelay` T1a: 1 kHz wet tone, Time stepped 200 → 100.4 ms at a block boundary; report offset in cents, its duration, and worst `\|x[n]−x[n−1]\|` against `2πf/f_s·A` |
| **T4** | companding **compounds per pass**, because the feedback is taken after the expander and returned before the compressor (S1): with the compander at its shipped setting a 5 ms burst's 10–90 % rise time on repeat 4 differs from repeat 1's by **≥ 1.5×**, against a **±5 %** repeatability floor established by measuring repeat 1 twice | S1 (the feedback tap point … (App. T4) | medium — the topology … (App. T4) | repeat 4's rise time within 10 % of repeat 1's — which is exactly what one compressor/expander pair placed *outside* the loop gives, and is the planted fault for this measurement | envelope trace: 1 kHz tone burst … (App. T4) |
| **T5** | the *fixed* band limit is separate from T2a's sliding one: an anti-alias and a reconstruction low-pass, together at least **30 dB/octave** of ultimate slope measured over the octave above the fixed corner, whose corner **moves by less than ±10 % when Time changes by a factor of four** — so the wet path has two roll-offs, one that follows the knob and one that does not | S3, re-read this run: "typically 30 or 36 dB … (App. T5) | high | an ultimate slope below 30 dB/octave over that octave, or a fixed corner moving more than 10 % across a 4:1 Time change | the T2a sweeps at Time an octave … (App. T5) |
| **T6** | **character difference:** at the same Time, `"double-line"` has twice `"single-line"`'s clock and therefore twice its T2a corner, within **±10 %**; `"single-line"` at 300 ms sits at `f_clk` 6827 Hz and a −3 dB corner near 3.0 kHz, `"double-line"` at 13653 Hz and near 6.0 kHz (Appendix A) | S1 (two MN3005s in series) + S2 (4096 stages) … (App. T6) | high | the two characters producing corners within 10 % of each other at the same Time | T2a's measurement run on both … (App. T6) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node: `audioecho.FeedbackDelay`** (audioif's own → tier **audioif**).
The three things this class needs inside a feedback loop — a band limit, a
level-dependent stage, and a modulated read — are only reachable there. The
per-sample interpolated read (`audioif_feedback_delay.c:226-228`) under the
per-sample magic-circle sine (`:209-213`) carries the Memory Man's clock
modulation; `damping_hz`'s in-loop one-pole (`:231-235`) and `cut_hz`'s
one-pole high-pass (`:236-240`) carry T5's fixed pair, compounding once per
pass exactly as the circuit does; `cross_feed`/`input_pan` (`:249`,
`:126-141`) give Spread.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

All three are additive options on `audioecho.FeedbackDelay`, audioif's own
node (D1). Ranked.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Time | UNIPOLAR | 20–600 ms, log | DM-2 Repeat Rate; DMM Delay |
| 1 | Feedback | UNIPOLAR | 0.00–0.99 | DM-2 Intensity; DMM Feedback |
| 2 | Mix | UNIPOLAR | 0.0–2.0 (`Echo`'s convention) | DM-2 Echo; DMM Blend |
| 3 | Glide | UNIPOLAR | 0–2000 ms, log (0 = instant) | none — the clock's own ramp |
| 4 | Modulation | UNIPOLAR | 0.0–1.0 | DMM Chorus/Vibrato depth (S1: into the clock) |
| 5 | Mod Rate | UNIPOLAR | 0.05–8 Hz, log | DMM LFO |
| 6 | Companding | UNIPOLAR | 0.0–1.0 (0 = bypassed) | the NE570 pair (S1); no panel control |
| 7 | Bandwidth | UNIPOLAR | 1500–8000 Hz, log | T5's fixed filter pair; no panel control |
| 8 | Drive | UNIPOLAR | 0.0–1.0 | level into the line against S2's 0.9 Vrms / 2.5 % THD point |
| 9 | Age | UNIPOLAR | 0.0–1.0 | none — one knob over bandwidth, noise and clock drift |
| 10 | Spread | UNIPOLAR | 0.0–1.0 | none — stereo, under D2; inert at 1 channel |
| 11 | Sync | TOGGLE | off / on | none — reads `transport()` |

**Characters:** `"single-line"` (default, `N = 4096`), `"double-line"`
(`N = 8192`). `N` is not a macro: it is the character, and T6 is what it buys.
**Patches:** 0 *Short Repeats, Bright*; 1 *Long Repeats, Dark*; 2 *Modulated
Repeats*; 3 *Heavy Companding, Even Repeats*; 4 *Failing Clock*; 5 *Dotted
Eighth, Synced*.

## 7. Defects in the current class the rebuild must not repeat

1. **The `Age` knob has no relationship to a bucket brigade.** It maps
   `damping_hz` over 1100–4200 Hz and `cut_hz` over 60–280 Hz on a bare log
   interpolation (`delay.py:225-226`) with no reference to the clock, the
   stage count or the delay time — so the darkening does **not** track the
   Time knob, which is T2a, the trait that most distinguishes a BBD from a
   digital delay.
2. **`Drive` is the node's cubic soft-clip** (`delay.py:219`) standing in for
   a compander. A cubic clip is a static odd-symmetric curve; a compander is
   two envelope followers. They are not approximations of each other.
3. **The modulation rate is a class constant with no knob** — `WOW_HZ = 1.3`
   (`delay.py:204`), where the Memory Man has an LFO with a switch and a depth
   control (S1).
4. **A patch is named after a product** — `PATCHES[2]` is `"Memory Man"`
   (`delay.py:199`). Patch names describe settings.
5. **`Time` steps** — `_apply_macro` writes `delay_ms` straight into the node
   (`delay.py:213`), the discontinuity of §5's N1, on the one delay family
   that physically cannot step.
6. **`latency_samples`/`tail_samples` are base-class defaults** — `delay.py`
   declares neither, so `tail_samples` reports `None` for a class holding a
   0.95-feedback loop (`_core.py:140-141`, `:251-253`).
7. **`capabilities` is empty and the transport is never read** (no
   `CAPABILITIES` in `delay.py`; default `_core.py:139`).

## 8. Open questions

1. **Is the DM-2 character sourced well enough to ship?** This run reached its
   chipset and delay range (S5, S6) but **no readable DM-2 schematic**, so
   `"single-line"` currently rests on a stage count plus the Memory Man's
   topology. *Settles:* Station A — find a readable DM-2 drawing, or restate
   the character honestly as "one 4096-stage line with the Memory Man's
   surrounding circuit".
2. **The BBD's image spectra.** S4 is explicit that the sample-and-hold's
   images and the input's aliasing are part of the sound and "can be
   considered to be desirable". They are **deliberately not fixed as a trait
   here**, and the reason is recorded now rather than discovered later:
   reaching them needs the delay to run at a varying inner clock (S4 §3),
   which replaces `FeedbackDelay`'s core rather than extending it, and S4's own
   remedy for the residual is oversampling, which Tier 3 refuses on latency
   grounds. *Settles:* Phase 0 — confirm the refusal or reopen it as a fourth
   ask.
3. **N3's fate**, and with it whether T4 survives. Phase 0's refutation
   (2026-09-06) removed the second of its two reasons — a Splitter/Mixer branch
   keeps the dry path byte-identical — and left the first standing: one
   compress/expand pair per *repeat* is not one per *pass*, which is what T4
   measures. *Settles:* the node list; if refused, T4 is
   disconfirmed-by-decision.
4. **T1 has no independent handle at short delay times.** `f_clk` is only
   recoverable from the wet magnitude where the sinc's first null is below
   Nyquist — Time ≥ 85.3 ms single-line and ≥ 170.7 ms double-line at 48 kHz,
   ≥ 92.9 / 185.8 ms at 44.1 kHz, ≥ 185.8 / 371.5 ms at 22.05 kHz. Below that
   the only estimate of `f_clk` is the −3 dB corner, which the class's own
   Python control law places, so the check would be measuring the code against
   itself. The seed's rule is therefore that T1 is **recorded unmeasured**
   below those Times rather than passed, and the evidence pack must say so per
   rate. *Settles:* the kit spec — either it accepts the gap, or it adds a
   short-Time handle (an inter-tap arrival difference, or a clock-rate
   sideband) that does not come from the corner.
5. **The DMM's actual clock range.** Not claimed anywhere above: S7 gives the
   Q/oscillator relation but not the R·C formula, so Appendix B's arithmetic
   is flagged unsourced. *Settles:* Station A, from a CD4047 datasheet plus a
   SPICE run of the oscillator, which also settles whether the LFO injection
   makes the modulation depth delay-dependent.

---


## Appendix

### A. The delay law, checked two ways, and the sinc factors

Computed here 2026-09-06. `t_D = N/(2·f_clk)` against each datasheet's own
published range — the check that decides between S4's formula and S3's text:

| part | `N` | clock range (source) | `N/(2·f_clk)` | delay range as published |
|---|---|---|---|---|
| MN3007 (S3) | 1024 | 10–100 kHz | 51.20 – 5.12 ms | 5.12 – 51.2 ms ✔ |
| MN3005 (S2) | 4096 | 10–100 kHz | 204.80 – 20.48 ms | 20.48 – 204.8 ms ✔ |

Both match to the digit, and S4 eq. 34's `N/2` clock periods is the form that
agrees with both. **Audit correction, 2026-09-06:** an earlier draft of this
paragraph said S3's prose gives `N/f_clock` and so contradicts its own delay
range. It does not. S3 states the formula as an image, that image was fetched
and read in the audit
(`electrosmash.mas-effects.com/images/mn3007-bucket-brigade-devices/gif.latex`),
and it reads **`time_delay = N / (2 · f_clock)`**. All three sources agree; the
"the text contradicts the numbers" story was this dossier's own misreading and
is withdrawn.

Sinc factors, from `sinc(x) = sin(πx)/(πx)` with `x = f/f_clk`:
**−1 dB at `0.2615·f_clk`, −3 dB at `0.4422·f_clk`, −3.92 dB at `f_clk/2`,
first null at `f_clk`.** T2a's `0.4422` and T2b's `−3.92 dB` are these.
(`0.4422` is where the loss is exactly −3.000 dB; the half-power point is
`0.442946`, 0.17 % away — immaterial against T2a's ±10 %, recorded so the two
figures never drift apart in later passes. Re-derived in the trait-critic pass,
2026-09-06.)

At Time = 300 ms:

| character | `N` | `f_clk = N/2T` | −3 dB corner | first null |
|---|---|---|---|---|
| single-line | 4096 | 6827 Hz | 3019 Hz | 6827 Hz |
| double-line | 8192 | 13653 Hz | 6038 Hz | 13653 Hz |

T6's "an octave apart at the same Time" is that table.

### B. The Deluxe Memory Man's clock — arithmetic, and why it is not a trait

From S1's drawing: a CD4047 astable with C = 240 pF, R = 5.6 kΩ + a 100 kΩ
DELAY pot, its Q/Q̄ outputs clocking both BBDs at half the oscillator rate
(S7). Applying the commonly quoted `f = 1/(4.4·R·C)` for the 4047's oscillator
gives Q at 4.5–84.6 kHz and therefore `8192/(2·f_clk)` = **48–914 ms**, which
brackets the delay times the Memory Man is known for.

**That formula was not sourced in this run** — S7's page carries the Q/OSC
relation but not the R·C expression — and the drawing also shows the chorus
LFO injecting into the same timing node, which changes the effective R. The
numbers above are therefore recorded here as arithmetic, **excluded from the
trait table**, and left to Station A to source and SPICE.

### C. One-pole against sinc: the measurement behind N2

Fitted here 2026-09-06. The node's damping filter is `y += a·(x−y)` with
`a = 1−exp(−2πf_c/f_s)` (`audioif_feedback_delay.c:31-38`); the target is
`|sinc(f/f_clk)|` (S4 eq. 34). Best `f_c` by worst-case dB error over
100 Hz–min(0.9·f_clk, 16 kHz), at 48 kHz:

| configuration | `f_clk` | best one-pole `f_c` | worst error | at |
|---|---|---|---|---|
| 4096 stages, 300 ms | 6827 Hz | 1286 Hz | **5.1 dB** | 3190 Hz |
| 8192 stages, 300 ms | 13653 Hz | 2406 Hz | **5.5 dB** | 12224 Hz |
| 4096 stages, 60 ms | 34133 Hz | 12062 Hz | 0.5 dB | 9438 Hz |

The filter sits in the feedback loop, so the error is per pass: five repeats
at 300 ms put the one-pole 25 dB away from the sinc. T2b's ±1 dB is not
reachable this way at the delay times this class is for — and is comfortably
reachable at short ones, which is why the lean patch may drop N2 without
dropping the class.

### D. The Deluxe Memory Man values read off S1's drawing

Recorded here so §2's source cell stays short; every value was read from the
scan, none from memory. **Input:** LEVEL preamp on a 4558 (1 MΩ feedback with
22 kΩ + trim, 27 pF), into an active low-pass (1.2 nF, 100 kΩ, 100 kΩ,
200 kΩ, 200 kΩ, 22 nF). **Compressor:** half an NE570 (68 kΩ ×3, 4.7 µF and
1 µF timing). **Anti-alias filter:** 4558 sections around 2.7 nF, 33 kΩ,
33 kΩ, 1 kΩ, 33 nF, with 24 kΩ/16 kΩ/50 kΩ setting the shape, into MN3005 A
pins 13/14 through 2.2 µF + 2.2 µF. **Line:** MN3005 A → 2N5087 emitter
follower (22 kΩ, 820 Ω) → MN3005 B. **Clock:** CD4047, 240 pF and 1 nF timing
caps, 5.6 kΩ + 100 kΩ DELAY, Q/Q̄ (pins 10, 11) to both BBDs' clock pins.
**Output:** 5 kΩ balance trim and a 4558 combiner (100 kΩ, 100 kΩ trim,
680 kΩ, 22 µF, 240 kΩ ×2), then two 4558 low-pass sections (16 kΩ, 16 kΩ,
2.7 nF ×2, 33.2 kΩ, 24.3 kΩ; then 470 Ω, 47 nF, 15 kΩ, 16 kΩ, 2.7 nF ×2,
15 kΩ, 39.1 kΩ), then the other half of the NE570 as expander (11 kΩ, 1 µF,
4.7 µF). **Feedback:** 10 kΩ pot with 47 nF and 0.47 µF/1 kΩ/7.5 kΩ, taken
after the expander. **Output amp:** 4558 with 100 kΩ/240 kΩ and two
shaping networks (120 pF/330 kΩ, 150 pF/180 kΩ). **Blend:** 10 kΩ lin, 150 Ω
to each of DIRECT OUT and ECHO OUT. **Chorus/vibrato LFO:** two 4558 stages
(900 kΩ ×2, 4.7 µF ×2, 1 µF ×2, 120 kΩ, 15 kΩ, 3.3 kΩ) with an LFO switch, a
100 kΩ depth pot, and a 27 kΩ/7.5 kΩ/2.7 kΩ network into the 4047's timing
node. **Supply:** single −15 V (2N6111 regulator, AC 24 V in).

### E. Palette verification (Phase 0, 2026-09-06)

Run in this session on the CPython build (`audiocomponents/.venv/bin/python`)
at 48 kHz; line citations taken with `grep -n`.

**E.1 The one-pole against the sinc, banded three ways.** Best worst-case dB
fit of the node's damping filter (`y += a(x−y)`, `a = 1−exp(−2πf_c/f_s)`,
`audioif_feedback_delay.c:31-38`) to `|sinc(f/f_clk)|`:

| configuration | band | best `f_c` | worst error |
|---|---|---|---|
| 4096 @ 300 ms (`f_clk` 6827 Hz) | 100 Hz–0.9·f_clk (Appendix C's band) | 1239 Hz | **5.38 dB** at 3200 Hz |
| 4096 @ 300 ms | 100 Hz–0.45·f_clk (T2b's own band) | 3110 Hz | **0.22 dB** at 1877 Hz |
| 8192 @ 300 ms (13653 Hz) | 100 Hz–0.9·f_clk | 2343 Hz | **5.63 dB** at 12288 Hz |
| 8192 @ 300 ms | 100 Hz–0.45·f_clk | 6015 Hz | **0.24 dB** at 6144 Hz |
| 4096 @ 60 ms (34133 Hz) | 100 Hz–16 kHz | 12085 Hz | **0.45 dB** at 9416 Hz |

Appendix C reproduces (its 5.1 / 5.5 / 0.5 dB against 5.38 / 5.63 / 0.45 here,
the difference being the `f_c` search grid). **The row that decides T2b is not
in Appendix C**: over the band T2b's own measurement names, the one-pole is
inside ±1 dB, so a build that shipped it would pass the single-sweep form of
the trait while having no sample-and-hold in it at all.

**E.2 T2b's ratio form, which is what the trait actually measures.** Two
sweeps an octave apart in Time, the class's control law
(`damping_hz = 0.4422·f_clk`) at each, ratio in dB against
`sinc(f/f_clk)/sinc(2f/f_clk)` over 100 Hz–0.45·f_clk of the shorter Time:

| N | Times | `f_clk` pair | worst ratio error |
|---|---|---|---|
| 4096 | 300 / 600 ms | 6827 / 3413 Hz | **12.09 dB** at 3072 Hz |
| 8192 | 300 / 600 ms | 13653 / 6827 Hz | **12.09 dB** at 6144 Hz |

Twelve times T2b's ±1 dB. The one-pole is also −7.6 dB at `f_clk` where the
sinc is a null, so T2b's 20 dB-deep-null clause fails on any pole-only build.

**E.3 N2's refutation, run.** Two parameters searched together — the in-loop
low-pass `damping_hz` and the in-loop high-pass `cut_hz` (`y −= lowpass(y)`,
`:236-240`) — against the same target. The high-pass contributes nothing: best
cascade is LP 1258 Hz + HP 140 Hz at **5.43 dB** wide-band, LP 3078 Hz + HP
**0 Hz** at 0.24 dB over T2b's band. A high-pass can only take away lows, and
the sinc is flat at DC. N2 stands.

**E.4 N3's reason (b), withdrawn.** A wet-only branch is buildable on the
palette and keeps the dry byte-identical: an impulse of 30000 LSB returns
**30000** through an `audioroute.Splitter` tap and **30000** through an
`audiomixer.Mixer` voice at level 1.0 (measured). `Splitter` carries four taps
(`audioif_splitter.h:21`). Reason (a) — one compress/expand pair per repeat is
not one per pass — is untouched and is what T4 measures.

**E.5 The step and the mono behaviour** are `TapeDelay.md` Appendix E.1 and
E.4, re-measured in the same run and shared by both classes: 15961 LSB at the
`delay_ms` step against the tone's own 1566, and `cross_feed` 1.0 / `input_pan`
+1.0 removing the wet path entirely at `channel_count` 1.

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

Rate note: **T2b's null clause is band-limited, and the band shrinks with the
sample rate.** The null sits at `f_clk = N/2T`, so it is in band only at the
longer delays: single line at 300 ms puts it at 6.8 kHz and at 600 ms at
3.4 kHz — in band at all three rates — while single line at 60 ms puts it at
34.1 kHz, above Nyquist everywhere. Where the null is out of band, T2b is
checked on the sinc's *shape* over what is left, and the check weakens as the
rate drops: at 60 ms the deviation up to Nyquist is 8.8 dB at 48 kHz but only
1.6 dB at 22.05 kHz on the single line, and 0.4 dB on the double. So T2b is
stated at **48 kHz**, evidenced at 44.1 kHz, and at 22.05 kHz its short-delay
half is recorded as out of band rather than failed. T2a holds at every rate
and every delay.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Electro-Harmonix *Deluxe Memory Man* schematic (image-only PDF — 1 page, 0 text characters, one embedded 1924×598 RGB image, re-extracted and re-read in three tiles at 3× in the audit) | the whole signal path with values — **two MN3005s in series** (A → 22 kΩ → 2N5087 emitter follower with 820 Ω → B), CD4047 clock with 240 pF + 1 nF, 5.6 kΩ and the 100 kΩ DELAY pot, Q/Q̄ (pins 10, 11) to both BBDs, **NE570** compressor before and expander after, multi-section 4558 filters both sides, FEEDBACK 10 kΩ taken from the expander's output node (through 1 kΩ + 0.47 µF) and returned into the compressor's input, an LFO built from two 4558 stages injected into the **clock's timing node**, single −15 V, BLEND 10 kΩ lin to DIRECT OUT and ECHO OUT (full component list: Appendix D) | **license unverified — treated as copyleft.** No rights statement on the drawing; the host's own root page could not be reached to check its terms (mod_security "Not Acceptable" in the audit, though the PDF itself serves 200). Read as a document (vision §5), nothing reproduced | https://experimentalistsanonymous.com/diy/Schematics/Delay%20Echo%20and%20Samplers/Deluxe%20memory%20man.pdf | yes, read as images — every claim above re-read in the audit. *One correction:* the drawing labels no LFO **waveform**; "triangle" is read from the integrator-plus-comparator topology, not printed, and is marked as inference here and in §1 |
| **S2** MN3005 *4096-Stage Long Delay BBD* product specification, rev. 2015-04-A1 (Xvive reissue of the Panasonic part) | 4096 stages; clock **10–100 kHz**; signal delay **20.48–204.8 ms**; S/N 75 dB typ; noise 0.8 mVrms A-wtd at 100 kHz clock; THD **2.5 %** at `f_cp` 40 kHz, 1 kHz, 0.78 Vrms; input swing 0.9 Vrms min at that THD; insertion loss 0 dB typ (±4); V_DD −14…−16 V; two clock inputs CP1/CP2 | vendor product specification; **no license or copyright text anywhere in the file** — only the §8.2 "information … subject to change" disclaimer (checked in the audit) — so **license unverified, treated as copyleft**; the numbers are facts about a part | https://xvive.com/audio/wp-content/uploads/sites/2/2021/11/Xvive_MN3005_BBD_DATASHEET.pdf | yes, full text — re-downloaded and re-extracted in the audit; every figure in this cell re-checked against the datasheet's own tables |
| **S3** ElectroSmash, *Bucket Brigade Devices: MN3007*, read at the MAS Effects archive mirror | MN3007 1024 stages, clock 10–100 kHz, delay 5.12–51.2 ms, S/N 80 dB typ, THD 0.5 % at 0.78 Vrms; MN31xx clock drivers; 570/571 companding; anti-alias/reconstruction filters "typically 30 or 36 dB per octave with a −3 dB point of around 3 kHz"; MN3007 users incl. CE-2, Small Clone, Memory Man. **Audit correction, 2026-09-06: this row previously claimed the article's text states the delay is `N/f_clock` and so contradicts its own delay range. It does not.** The page states its formula as an image (`images/mn3007-bucket-brigade-devices/gif.latex`); that image was fetched and read in the audit and reads **`time_delay = N / (2 · f_clock)`** — in agreement with S4 eq. 34 and with both datasheets. There is no contradiction and no "text versus drawing" trap here | mirror footer: "An unofficial, non-commercial backup … All content and images belong to their original authors/owners" — **license unverified, treated as copyleft**; ElectroSmash's own rights page is unreachable (`electrosmash.com` and `www.electrosmash.com` both fail to resolve from this machine, re-checked in the audit) | https://electrosmash.mas-effects.com/mn3007-bucket-brigade-devices.html | yes — re-fetched in the audit, including the formula image |
| **S4** Holters & Parker, *A Combined Model for a Bucket Brigade Device and its Input and Output Filters*, DAFx-18 | the BBD as a **fixed-length, variable-sample-rate** line; delay = `N/2` clock periods and `sinc(ω/2πf_BBD)` from the output hold (eq. 34); the images and aliasing that hold produces; a **clock-rate step gives a smooth pitch change** where "a simple digital delay-line … would exhibit a discontinuity" (fig. 8); Juno-60 filters "sixth-order filters that can be decomposed into a first-order high-pass filter … and a fifth-order low-pass filter" (§4) | **no rights statement printed** anywhere in the PDF (searched in the audit) — **license unverified, treated as copyleft**: read as a paper, no code taken | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2018/09/Holters-Parker-2018-A-Combined-Model-for-a-Bucket-Brigade-Device-and-its-Input-and-Output-Filters.pdf | yes, full text — re-downloaded and re-extracted in the audit; eq. 34, the fig. 8 sentence, the "N/2 clock periods" line and the Juno-60 filter orders are all verbatim |
| **S5** Aion FX, *Amethyst Analog Delay* (DM-2 project documentation) | MN3005/MN3101 or MN3205/MN3102 chipset; "around 300 ms of delay time when properly calibrated"; the original "uses a compander to significantly improve noise performance" | "Trademarks and brands are the property of their respective owners. Any usage of trademarks on this website is for comparative purposes only, intended under fair use, and is not endorsed by the trademark holders" (verbatim, audit); no project license stated — **license unverified, treated as copyleft** | https://aionfx.com/project/amethyst-analog-delay/ | yes — re-fetched in the audit; the "around 300ms of delay time when properly calibrated" and compander quotes are verbatim |
| **S6** next.gr, Boss DM-2 schematic page | first version MN3005 + MN3101; later MN3205 + MN3102; MN3205 quoted as 0.8 % THD against MN3005's 1 % | "© 2025" site footer with Terms of Use / Disclaimer links (not read) — **license unverified, treated as copyleft**; the schematic image itself did not render to the fetch tool | https://www.next.gr/boss-dm-2-delay-guitar-pedal-schematic-diagram | yes (text only) — re-fetched in the audit; both IC-version sentences and the 0.8 %/1 % THD comparison are verbatim |
| **S7** TI, CD4047B product page | "The OSCILLATOR output period will be half of the Q terminal output in the astable mode" — so Q/Q̄ are the two-phase clocks at half the oscillator rate. **The R·C frequency formula is not on this page and was not sourced in this run** | manufacturer product page carrying no copyright line of its own, only "Content is provided 'as is' by TI and community contributors and does not constitute TI specifications. See terms of use" — **license unverified, treated as copyleft**; the quoted sentence is a fact about a part | https://www.ti.com/product/CD4047B | yes — re-fetched in the audit; the OSCILLATOR/Q sentence is verbatim and the page still carries **no** R·C formula |
| **S8** hobby-hour.com, *Boss DM-2 Delay pedal schematic diagram* — **added by the Phase 0 audit, 2026-09-06** | the DM-2's published specification ("Delay Time: 20ms-300ms", input impedance 470 kΩ, residual noise < −100 dBm IHF-A, 11 mA at DC 9 V) and its IC list (IC1 uPC4558C/JRC4558DD, **IC2 NE570N compandor**, **IC3 MN3005 or MN3205, "4096-stage BBD"**, IC4 MN3101/MN3102, Q5 2SK30ATM-Y); and a **readable 1060×686 schematic** (`schematics/dm2-delay-schematic.png`, read in the audit at 3× in two tiles) showing **one** BBD (IC3, CP1/CP2, OUT1/OUT2), the clock driver IC4 with REPEAT RATE VR6 1 MB, the compander IC2 with its BIAS (VR1 22 kB) and CANCELL (VR2 10 kB) trims, INTENSITY VR4 50 kB and ECHO VR5 50 kB, a multi-pole transistor filter ahead of the line (emitter followers Q3/Q4 with R21–R28 10 kΩ and C17 .0022, C18 .001, C19 .033, C20 .039, C21 330 p) and an op-amp stage after it (½IC1 with R32/R35/R37 47 kΩ, R36 10 kΩ, C28 100 p, C29 .0068). *Read with care:* Q6/Q7 are the cross-coupled bypass flip-flop by the CHECK LED and the NORMAL/EFFECT jacks, **not** a filter — this cell said otherwise in its first draft | **license unverified — treated as copyleft**: no copyright, terms or licence text anywhere on the page (checked in the audit). Read as a document; nothing reproduced | https://www.hobby-hour.com/electronics/s/dm2-delay.php (image: `…/electronics/s/schematics/dm2-delay-schematic.png`) | **yes** — 200 with an ordinary browser user-agent. The earlier "403, not reached" was a user-agent block, not a dead page |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1** | the Time control is a **clock**: `T = N/(2·f_clk)` with `N` fixed. The falsifiable content is that the arrival time and the band limit are locked by that one law, so with `f_clk` recovered **from the wet magnitude's first null** — never from the −3 dB corner, which the control law itself sets — the product `T_arrival · f_clk` is `N/2` to **±1 %** at every Time setting where the null is in band | S4 eq. 34; S2's own 20.48–204.8 ms over 10–100 kHz for `N` = 4096, which reproduces the law to the digit (Appendix A); both re-read this run | high | `T·f_clk` outside `N/2 ±1 %` at any Time setting whose null is in band; or a build in which the null does not move as `1/T` | delay tracking: impulse at Time = 120, 300, 600 ms, arrival to the sample; wet-only swept sine at the same settings; `f_clk` from the null. The null is in band at 48 kHz for Time ≥ 85.3 ms single-line and ≥ 170.7 ms double-line (`T ≥ N/f_s`), and at 44.1 kHz for ≥ 92.9 / 185.8 ms; **at Time = 40 ms there is no independent handle and the row is recorded unmeasured at that setting, never passed** |
| **T2a** | the wet path's high-frequency corner **tracks the delay time**: −3 dB at `0.4422·f_clk = 0.2211·N/T`, so doubling Time halves the corner, within **±10 %**. At Time = 300 ms that is **3019 Hz** single-line and **6038 Hz** double-line (Appendix A) | S4 eq. 34/37, read in full this run; the 0.4422 factor derived (Appendix A) | high | a corner that does not halve to ±10 % when Time doubles, or that is more than 10 % from `0.2211·N/T` at any setting — a fixed `damping_hz` fails both | swept-sine magnitude of the wet path (mix = 2.0, feedback 0) at Time = 60, 150, 300, 600 ms; report the −3 dB point, its ratio to `0.2211·N/T`, and the ratio between consecutive octaves |
| **T4** | companding **compounds per pass**, because the feedback is taken after the expander and returned before the compressor (S1): with the compander at its shipped setting a 5 ms burst's 10–90 % rise time on repeat 4 differs from repeat 1's by **≥ 1.5×**, against a **±5 %** repeatability floor established by measuring repeat 1 twice | S1 (the feedback tap point, read off the drawing); S3 (570/571 as the standard compander, re-read this run) | medium — the topology is read from a drawing, and **S1 was not re-reached in the trait-critic pass**, so the feedback tap point still rests on the audit's read of the scan; the 1.5× is this dossier's threshold, not a measured pedal figure | repeat 4's rise time within 10 % of repeat 1's — which is exactly what one compressor/expander pair placed *outside* the loop gives, and is the planted fault for this measurement | envelope trace: 1 kHz tone burst, 5 ms rise, feedback 0.7; isolate repeats 1–4 by arrival time, report each 10–90 % rise time and the ratio, on both characters |
| **T5** | the *fixed* band limit is separate from T2a's sliding one: an anti-alias and a reconstruction low-pass, together at least **30 dB/octave** of ultimate slope measured over the octave above the fixed corner, whose corner **moves by less than ±10 % when Time changes by a factor of four** — so the wet path has two roll-offs, one that follows the knob and one that does not | S3, re-read this run: "typically 30 or 36 dB per octave with a –3 dB point of around 3 kHz"; S4 §4 verbatim, read this run: "Both the input and output ﬁlters are sixth-order ﬁlters that can be decomposed into a ﬁrst-order high-pass ﬁlter (for adjusting bias voltages) and a ﬁfth-order low-pass ﬁlter" — a 5th-order LP is 30 dB/octave, which reaches S3's figure from a second, independent source | high | an ultimate slope below 30 dB/octave over that octave, or a fixed corner moving more than 10 % across a 4:1 Time change | the T2a sweeps at Time an octave apart with the sinc divided out analytically using `f_clk` from T1's null; report the residual's corner and ultimate slope at each, and the corner's movement |
| **T6** | **character difference:** at the same Time, `"double-line"` has twice `"single-line"`'s clock and therefore twice its T2a corner, within **±10 %**; `"single-line"` at 300 ms sits at `f_clk` 6827 Hz and a −3 dB corner near 3.0 kHz, `"double-line"` at 13653 Hz and near 6.0 kHz (Appendix A) | S1 (two MN3005s in series) + S2 (4096 stages) + T1 | high | the two characters producing corners within 10 % of each other at the same Time | T2a's measurement run on both characters at Time = 300 ms; report the corner ratio |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Audit note on the DM-2 (2026-09-06):** "no DM-2 schematic this run could
read" is **superseded** by S8, reached and read in the audit. §8.1's premise —
that `"single-line"` rests only on a stage count plus the Memory Man's
topology — no longer holds: the DM-2's own drawing shows one 4096-stage BBD, a
compander with its own bias and cancel trims, and a filter section on each
side of the line. No trait row changes; the sourcing gap closes, and §1 and
§8.1 should be re-cut around S8 rather than another drawing being hunted for.

*(from §3)*

Budget as a fraction of one stereo block's deadline: **P4 0.06, S3 0.15** —
proposals against Phase 1's cost table, not measurements. Lean patch **yes**:
`" - lean"` drops the in-loop compander (T4 → disconfirmed, recorded) and the
sample-and-hold (T2b → a delay-tracking one-pole, T2a still held), keeping
T1, T2a, T3, T5, T6. That is the escape valve if the S3 budget is missed.

*(from §3)*

**Latency is zero.** The dry path is the input frame; a BBD delay looks ahead
at nothing. `latency_samples` is **0** at every rate, macro setting and
character, and the class ships **no option that adds latency** — no lookahead,
convolution partition, pitch window or oversampling. **This is a decision, not
a default:** S4 §4 notes that the cleanest way to suppress a BBD model's extra
aliasing is to oversample, and this class declines it precisely because
oversampling's filters cost latency and the stompbox case (vision §9a) has
none to spend. `tail_samples` is recomputed on every `Time`/`Feedback` move as
`T · ln(0.001)/ln(feedback)` frames, clamped to the line at `feedback` 0 and to
a declared ceiling as `feedback → 0.99`.

*(from §4)*

**T2a is a Python control law, not a node feature.** On every `Time` move
Python computes `f_clk = N/(2T)` and sets `damping_hz` to `0.442·f_clk`, so
the corner tracks the knob with no C change at all — the compose-first answer,
and it works. **T2b is where compose-first stops** (§5) — but not for the
reason this seed first gave, and the corrected number is larger. Appendix C's
fit reproduces (5.38 dB at 3200 Hz, best `f_c` 1239 Hz, 4096 stages at 300 ms;
5.63 dB at 12288 Hz for 8192; 0.45 dB at 60 ms), yet **that band is not the
one T2b measures**: over T2b's own single-sweep band, 100 Hz–0.45·f_clk, the
same one-pole is within **0.22 dB** and would pass. What fails is T2b's
*ratio* form and its null. Run over 100 Hz–0.45·f_clk on the 300/600 ms pair
the class's own control law (`damping_hz = 0.4422·f_clk` at each Time) leaves
the two-sweep ratio **12.09 dB** from the sinc ratio at 3072 Hz — twelve times
the ±1 dB bar — and a one-pole has no null at all where the sinc has one
(Appendix E). Nobody should later refuse N2 by quoting the 0.22 dB.

*(from §4)*

`N` is a character constant, so nothing is tabulated on the target. **Mono:**
not stereo by definition; at `channel_count` 1 the node sets `feed_own[0]=1`,
`feed_other[0]=0` (`:62-71`) — and **`Spread` is not inert there, it is
destructive**: with one channel `other` is zero (`:248`) but `sent` still
scales by `1 − cross_feed` (`:203`, `:249`) and `input_pan` still writes
`feed_own[0]` (`:135-141`, read at `:253-254`), so `cross_feed` 1.0 removes
every repeat and `input_pan` +1.0 silences the wet path outright (measured,
`TapeDelay.md` Appendix E.4). The class clamps Spread to zero at one channel
rather than documenting it as harmless.
**`capabilities` (D10): `("tempo_sync",)`** — the class reads `transport()`
and quantises `Time` to a beat division when `Sync` is on.

*(from §5)*

**N1 — delay-time slew with a speed-type mode.** *Unblocks* **T3**. Identical
to `TapeDelay`'s N1 and asked once for both classes: `delay_frames` is written
straight (`audioif_feedback_delay.c:77-84`) and read unsmoothed (`:212`), so a
Time change lands in one sample — **15960 LSB of discontinuity, 10.2× the
probe tone's own maximum slope**, measured on the CPython build
(`TapeDelay.md` Appendix B, re-reproduced in this run). A BBD physically
cannot do that (S4 fig. 8). **The claim that T3 is therefore unreachable is
withdrawn:** `audiodelays.Echo(freq_shift=True)` holds a fixed-length line and
moves the read/write *rate* instead (`Echo.c:116-120`,
`audioif_echo.c:19-28`), which is the speed-type law itself — stepped
200 → 100.4 ms it holds **+1189.8 cents for 100.59 ms** and returns to unity,
click-free (`TapeDelay.md` Appendix E.2). What `Echo` cannot do is hold this
class's other traits: its loop is `buffer[j]*decay + sample` and nothing else
(`audioif_echo.c:23-26`, `:31`), so T2a's tracking corner, T2b's hold and T4's
compander have nowhere to sit, and it is a ported node that never gains them;
its read is nearest-neighbour (`:20`), −30.8 dB of jitter at 150 ms against
`FeedbackDelay`'s −67.8 dB. **The ask stands as the only way to have the pitch
law and the loop in one node**, and `Echo` is the working proof of its `speed`
mode rather than a reason to refuse it.

*(from §5)*

**N2 — a fractional sample-and-hold in the loop (`hold_ratio`).** *Unblocks*
**T2b**. *The palette instead:* one one-pole low-pass — **12.09 dB** from the
sinc on T2b's own two-sweep ratio at 300/600 ms, with no null where the sinc
has one; the widely quoted 5.1 dB is a different band, and over T2b's
single-sweep band the one-pole is within 0.22 dB (§4, Appendix C, Appendix E).
*Shape:*
one option, `hold_ratio = f_s/f_clk`, implemented as a running-sum boxcar of
fractional width over the loop signal — `sinc` exactly, O(1) per sample (one
add, one subtract, one interpolation), no table, no extra memory beyond the
window. Cheapest of the three asks and the one with the largest measured gap.
*Refutation, run in Phase 0 (2026-09-06):* the **cascade** of the node's
existing low-pass and high-pass was fitted to the sinc over both bands, two
parameters searched together — the high-pass buys nothing, the best cascade
puts it at 0–140 Hz and the worst-case error is the low-pass's own
(5.43 dB wide-band, 0.24 dB over T2b's single-sweep band, Appendix E). The
cascade does not reach ±1 dB on the ratio form, and **N2 stands.**

*(from §5)*

**N3 — a compander in the loop (`companding`).** *Unblocks* **T4**. *The
palette instead:* an `audiodynamics.Dynamics` in compress mode before the node
and expand after it. Two reasons that fails, and the second is decisive: (a)
every repeat then gets exactly **one** compress/expand pair regardless of how
many times it has been round, where the circuit gives it one **per pass** —
T4's measurement is built to separate those; (b) **withdrawn** — the dry path
need not pass through the compander at all: `audioroute.Splitter` fans the
source out (up to four taps, `audioif_splitter.h:21`) and `audiomixer.Mixer`
sums the branches, and both are byte-transparent on the dry leg (a 30000-LSB
impulse comes back at 30000 through a Splitter tap and through a Mixer voice at
level 1.0, measured, Appendix E), so a wet-only compander branch keeps Tier 1's
wire test. Reason (a) is decisive on its own, and it is not a matter of
arrangement: nothing can be placed inside `FeedbackDelay`'s loop from Python. *Shape:* two envelope followers and two
gain multiplies per frame per channel, plus a `companding` depth. *If refused:*
T4 is recorded disconfirmed-by-decision, the lean patch becomes the only
patch, and §8.3 carries the reason.
