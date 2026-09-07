# Effects Dossier — `Fuzz` (Dallas Arbiter Fuzz Face, germanium; Big Muff Pi as a second character)

**Class:** `lib/audioeffects/drive.py` — read once, for §7.
**Family / phase:** Drive, roadmap Phase 4
**Standout:** Fuzz Face (germanium), vision §4.2 — **confirmed**. `Overdrive`
clips inside an op-amp's feedback loop and `Distortion` clips to ground after
a gain stage; both bias near mid-rail. This circuit's identity is its
*off-centre* bias, its 5–8 kΩ input impedance and its complete absence of
tone shaping (S1, S4). The Big Muff Pi rides as a second **character**
(vision §10.7 — own trait rows). No swap argued.
**Grade:** circuit — schematics with values reached for both (S1, S5, S6);
traits derived analytically from the sourced bias points and corners (A1). No
SPICE deck is claimed here, but **two germanium device models were reached**,
neither of them by the first pass: S1's own article ends with two AC128 PSpice
`.MODEL` cards (β=85 and β=120), on the same page as its "Some Rights
Reserved" line — no named licence instrument, so §2 reads it as a document and
cites the parameter values as facts about the part; and **S9**, added by the
second audit pass, extracts Ebers-Moll *and* Gummel-Poon parameters for a real
AC128 from its own bench measurements. §8 Q1's premise — "no permissively
licensed AC128 model reached" — no longer holds, twice over; the knee can be
solved rather than held as a parameter. §8 is Arthur's to update.
**Portability tier:** needs audioif-own nodes (the §5 waveshaper;
`audioroute.Splitter` + `audiomixer.Mixer` for `cascade`'s tone crossfade)
**Status:** seed (Phase 0), 2026-09-06. Levels use the drive family's
convention (`Overdrive` §8): **0 dBFS ≡ 1.0 V peak at the jack**.

## 1. The circuit, in one paragraph

**`germanium` (Fuzz Face).** Two PNP germanium common-emitter stages,
DC-coupled collector to base, inside one shunt-series feedback loop — 100 kΩ
from Q2's emitter to Q1's base, setting bias and gain together (S1, S2).
Three capacitors and no others (2.2 µF in, 20 µF on the emitter network,
0.01 µF out into the 500 kΩ Volume pot) put the only three corners at 14, 7.9
and 31 Hz; there is no tone control, and S1's summary is that the circuit
"just removes some bass and keeps all the highs". The nonlinearity is the
transistors running out of room, and the room is unequal: S1's text gives Q1's
collector as sitting "around -1.6V" on a 9 V supply, against a mid-rail of
−4.5 V, so "the input stage will first hit soft saturation on the negative
semi-cycle", giving "soft asymmetric distortion to small signals and clipping
harder in both semi-cycles on big input signals". S8 reaches the same
conclusion independently — "the Fuzz Face has asymetrical clipping designed
into it" — from a bias of "about half a volt", which is S1's *target*, not the
−1.6 V S1 reports (A1). The 1 kΩ Fuzz pot is Q2's emitter
degeneration; opening it bypasses that resistor through the 20 µF and shunts
the *AC* feedback to ground (S1), raising gain while the DC bias — set
through paths the capacitor does not touch — stays put. Input impedance is
5.2–8.4 kΩ and moves with that pot (S1), low enough to load a pickup: S1 says
put the pedal first in the chain, S4 that the germanium version cleans up on
the guitar volume. Device selection is part of the circuit (S3). Values: A3.

**`cascade` (Big Muff Pi).** A booster, then two clipping stages in series on
the booster's own topology — about 23 dB then 25 dB (S5), each with a silicon
pair across the collector–base feedback loop conducting at ±0.6 V, each
band-limited at the bottom by a series input decoupling cap and at the top by
a Miller cap across the loop that rolls off "around 1KHz" (S5's own words; its
overview section says 1.2 kHz) — then a passive tone stack and a 13 dB output
stage. The 100 kΩ Sustain pot sits *before* the clippers and
sets the level into them (S5): it buys distortion, not volume. The tone stack
is five parts, a low-pass arm (482 Hz) and a high-pass arm (1206 Hz) blended
by a 100 kΩ linear pot (arm values S6, for the 1973 Ram's Head; pot value
S5's BOM); their interference leaves a notch S5 measures ~6.5 dB deep at
1 kHz with the pot centred. S6 states the mechanism — "the tone potentiometer
mixes the two filters" — and gives no statement either way about whether the
notch *centre* moves with the knob; the claim that the centre stays put is
neither sourced nor derived, and is carried as the *unmeasured* row **C4**.
Note the arms are era-dependent, and the two sources
describe two different units: S5 analyses an "American Version 3 … released in
1976-1977" whose BOM carries 22 kΩ and 39 kΩ with the same 10 nF and 4 nF —
S6's *Ram's Head '75* row exactly, 408 / 1809 Hz on S6's own pairing — not the
two 33 kΩ of the '73 row these arm values come from (audit record).

## 2. Sources and license calls

Every row below was **re-fetched and re-read in full by the Phase 0 licence
and citation audit on 2026-09-06** (raw HTML/PDF, not a fetch-tool summary);
the "Reached" column records that pass, and the corrections it forced are
reported to Phase 0's audit report (`effects-survey-audit.md`, not yet
written). Detail on what each gave is in A3.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 ElectroSmash, "Fuzz Face Analysis" (MAS Effects mirror) | topology, values, bias points, corners, Zin/Zout … (App. S1) | ElectroSmash's own footer … (App. S1) | https://electrosmash.mas-effects.com/fuzz-face.html | yes — audit run 2026-09-06, HTTP 200 |
| S2 Coda Effects, "Sunface / Fuzzface circuit analysis" | confirms the 100 kΩ feedback path and the 2.2 µF input … (App. S2) | **All rights reserved** … (App. S2) | https://www.coda-effects.com/p/circuit-analysis-fuzz-face.html | yes — audit run 2026-09-06, HTTP 200 (article body is in the page's `post-body` div; a naive tag-strip returns only chrome) |
| S3 Small Bear, "5F" Fuzz Face FAQ | hFE 70–85 / 120–140 (and 90–120 / 150–190 as the … (App. S3) | The article page carries no rights line … (App. S3) | https://diy.smallbearelec.com/HowTos/FuzzFaceFAQ/FFFAQ.htm | yes — audit run 2026-09-06, HTTP 200 |
| S4 Wikipedia, "Fuzz Face" | germanium→silicon history … (App. S4) | CC BY-SA 4.0, stated on the page ("Text is … (App. S4) | https://en.wikipedia.org/wiki/Fuzz_Face | yes — audit run 2026-09-06, HTTP 200 |
| S5 ElectroSmash, "Big Muff Pi Analysis" (same mirror) | four stages (19.6 / 23 / 25 / 13 dB) … (App. S5) | **Not "as S1".** This page carries **no … (App. S5) | https://electrosmash.mas-effects.com/big-muff-pi-analysis.html | yes — audit run 2026-09-06, HTTP 200 |
| S6 Coda Effects, "Big Muff tonestack" | the two arms as an era table (Triangle 22k/22k … (App. S6) | **All rights reserved** … (App. S6) | https://www.coda-effects.com/p/big-muff-tonestack-dealing-with-mids.html | yes — audit run 2026-09-06, HTTP 200 |
| S7 Yeh, *Automated Physical Modeling of Nonlinear Audio Circuits For … (App. S7) | Ebers-Moll eqs (10)–(12) … (App. S7) | "Copyright (c) 2010 IEEE. Personal use of … (App. S7) | https://ccrma.stanford.edu/~dtyeh/papers/yeh12_taslp.pdf | yes — audit run 2026-09-06, HTTP 200, 10 pages extracted |
| **S8** R. G. Keen, "The Technology of the Fuzz Face", GEOFEX … (App. S8) | the voltage-feedback topology … (App. S8) | "Copyright 1998 R.G. Keen All Rights … (App. S8) | http://www.geofex.com/article_folders/fuzzface/fftech.htm | yes — audit run 2026-09-06, HTTP 200, 24.5 kB; re-fetched by the second audit pass, HTTP 200, 24 549 bytes |
| **S9** B. Holmes, M. Holters & M. van Walstijn … (App. S9) | the Dallas Arbiter Fuzz-Face as one of its two case … (App. S9) | **No licence statement in the PDF … (App. S9) | https://dafx.de/paper-archive/2017/papers/DAFx17_paper_28.pdf (the DAFx-17 host serves the identical bytes at `www.dafx17.eca.ed.ac.uk/papers/DAFx17_paper_28.pdf`) | yes — second audit pass 2026-09-06, HTTP 200, 728 338 bytes, 8 pages extracted |

**Still looked for, not found.** No hardware capture sought — none is on the
bench (vision §2.3).

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

*Derived* = arithmetic on sourced values, shown in A1. Character
**`germanium`** (Fuzz Face):

*Trait-critic pass, 2026-09-06:* nine rows, eight graded and one (**C4**)
marked *unmeasured*. The record is under the Appendix.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| G1 | **Off-centre bias → asymmetric clipping.** Q1's collector sits "around -1.6V" on a −9 V supply (S1, re-read this run), leaving 1.6 V of room one way and 7.4 V the other — 4.63:1, **13.3 dB** (*derived*, A1). Bar, at 1 kHz, −20 dBFS, Fuzz and Bias centred: h2 **≥ −30 dBc** *and* the two output peaks **≥ 3 dB** apart | S1; S8 independently ("about half a volt on … (App. G1) | high for the … (App. G1) | h2 below −30 dBc, **or** peaks under 3 dB apart, at that level and setting. The two numbers are reported separately: a result that meets one and not the other is recorded as a partial, never rounded to a pass (the trait-critic pass closed a −40/−30 dBc dead band here in which a measurement could neither confirm nor disconfirm) | spectrum of a 1 kHz sine at −20 … (App. G1) |
| G2 | **No fixed threshold; the curve is not scale-invariant.** At fixed Fuzz, THD rises **strictly** across −40 → −6 dBFS in 6 dB steps — each step at least **0.5 dB** greater than the last, so "monotone" is a testable statement and not a tie — and h2/h1 at −26 dBFS differs from h2/h1 at −6 dBFS by **> 6 dB** | S1 ("soft asymmetric distortion to small signals … harder in both semi-cycles on big input signals"); S4 | high | h2/h1 moving **≤ 6 dB** between −26 and −6 dBFS, or THD failing to rise by 0.5 dB at any step. This is the failure mode the palette produces by construction: `audiofilters.Distortion` CLIP is `pow(\|x\|,d)`, homogeneous, and its harmonics measured **identical to the digit** at −20 and −6 dBFS — re-measured independently this run (h3 −10.8, h5 −15.9 dBc at both levels; §7, A2) | spectra at −40 / −26 / −12 / −6 dBFS in dBc; THD-vs-level over the same six 6 dB steps |
| G3 | **Fuzz is gain, not tone and not mix.** At five knob settings (0, 0.25, 0.5, 0.75, 1) the level-normalised magnitude response moves **< 1 dB** over 100 Hz–10 kHz, while THD at a fixed 1 kHz, −20 dBFS input rises at **every** one of the four steps | S1 (the pot removes Q2's emitter degeneration … (App. G3) | medium — read from … (App. G3) | the normalised shape moving > 1 dB anywhere in 100 Hz–10 kHz across the five settings; THD falling, or failing to rise, at any step | swept sine at Fuzz 0 / 0.25 / 0.5 … (App. G3) |
| G4 | **Full range: no tone stack.** Three first-order high-passes at 14 / 7.9 / 31 Hz and nothing else (S1): the **fundamental's** magnitude is flat within **1 dB** over 100 Hz–10 kHz at every Fuzz setting, and no more than **3 dB down at 40 Hz** (*derived*) | S1 — all three corner calculations re-read … (App. G4) | high (RC arithmetic … (App. G4) | any in-band deviation > 1 dB — a mid hump, a treble roll-off — or a −3 dB corner above 60 Hz | swept sine 20 Hz–20 kHz at Fuzz 0 … (App. G4) |

Character **`cascade`** (Big Muff Pi), and one shared with every drive class:

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| C1 | **Two cascaded symmetric clippers**, ±0.6 V after ~23 and ~25 dB: with the class's own tone-stack response divided out, h2 and h4 sit **≤ −40 dBc**, h3 is the **largest** harmonic above the fundamental, and the output peak grows **< 1 dB** for a 20 dB input rise at Sustain max | S5, re-read this run: "clip the signal when … (App. C1) | high | h2 or h4 above −40 dBc after that correction; h3 not the largest harmonic; the output peak growing ≥ 1 dB over the 20 dB rise | spectrum at Sustain max, 1 kHz … (App. C1) |
| C2 | **Sustain is a pre-clip level control**, not a mix and not a volume: from min to max at a fixed 1 kHz, −20 dBFS input, THD rises **≥ 25 dB** while output RMS moves **< 6 dB** | S5, re-read this run: "The 100K sustain … (App. C2) | high for the … (App. C2) | output RMS moving **≥ 6 dB**, or THD moving **< 25 dB**, across the knob at that level and frequency | THD and output RMS at Sustain 0 / … (App. C2) |
| C3 | **A fixed mid-scoop between the two tone arms.** With Tone centred the magnitude response has a **single local minimum**, lying **between the shipped revision's two arm corners** (§8 Q3 names the revision), at least **3 dB** below both shelves — S5 measures 6.5 dB on its own unit near 1 kHz — and across the knob 100 Hz and 5 kHz move in opposite directions by **> 15 dB** in total | S5 (depth and the ~1 kHz centre … (App. C3) | high for the blend … (App. C3) | no local minimum with Tone centred; a minimum outside the shipped revision's two arm corners; a scoop under 3 dB below both shelves; under 15 dB of total 100 Hz–5 kHz tilt | swept-sine magnitude at Tone 0 / … (App. C3) |
| C4 | **unmeasured as a circuit trait: whether the notch centre moves with the knob is not sourced, and was not derived.** The first draft asserted "< ⅓ octave" and labelled it *derived*; no derivation exists in this dossier, and neither reached page states it. S6 was re-read in full this run and says only that the pot "mixes the two filters" — it makes no statement either way about the centre, and the earlier quotation to that effect was already struck by the licence audit. The rebuild **reports** the notch centre at C3's five Tone settings as a number; it carries no pass/fail bar until a source or a written derivation fixes it | S6 (silent); S5 (silent) | — | — | reported by C3's sweep, not graded |
| A4 | **Alias floor.** A 1010 Hz sine at −6 dBFS, either character at maximum Fuzz, **on the shipped (non-lean) oversampling setting**: non-harmonic energy **≥ 60 dB** below the fundamental, 20 Hz–20 kHz, at 48 kHz. `Overdrive` T7 and `Distortion` A1's bar, worst here. The setting is named because patch 7 "Lean" drops oversampling to ×2, and an unqualified row would either fail on the lean patch or let it hide | S7 (4–8× oversampling as the norm) … (App. A4) | medium (design bar … (App. A4) | non-harmonic energy above −60 dB at either probe, on the P4 or the ESP32-S3 build, at the shipped setting. **The lean patch is measured at the same probes and reported, not graded here** — §8 Q4 owns whether it must also meet −60 dB | non-harmonic bin sum vs the … (App. A4) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

```
germanium:  source ─ Load ─ HP 14 Hz ─ [pre-gain] ─ curve(bias) ─ HP 31 Hz ─ Level ─ Mix
cascade:    source ─ HP ─ Sustain ─ curve1 ─ HP ─ curve2 ─ Splitter ─┬─ LP 1206 Hz ─┐
                                                                     └─ HP  482 Hz ─┴ Mixer(tone) ─ Level ─ Mix
```

**Palette-verifier corrections, 2026-09-06.** The first draft named
`audiofilters.Filter` / `synthio.Biquad` for the first-order sections. Four
things about that are wrong or unstated, each measured, not argued; the tables
are in A4.

- **There is no first-order section on that node.** All seven …  *(argument in full: App. R)*
- **The palette's first-order sections are in `audioecho.FeedbackDelay`**: …  *(argument in full: App. R)*
- **The biquad route holds DC, worst exactly where this class lives.** Burst …  *(argument in full: App. R)*
- **Nothing on the palette gains above unity except the drive node.** …  *(argument in full: App. R)*

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**A1 — the oversampled table waveshaper.** Asked already by the `Overdrive`
and `Distortion` seeds; this is the third claimant, with the sharpest
measurements (all numbers in A2, re-verified in A4).

- *Traits unblocked:* G1 (even harmonics at all), G2 (a level-dependent
  profile), C1 (a specific symmetric knee), A4 (the alias floor).
- *What the palette does instead:* four fixed curves in …  *(argument in full: App. R)*
- *Measurements showing it cannot reach them* (this run, CPython audioif; …  *(argument in full: App. R)*
- *What is asked:* a table-driven waveshaper in an audioif-own module taking …  *(argument in full: App. R)*
- *Refutation record (Phase 0):* all four palette curves were driven and …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Macros (7 of 16). Characters `germanium` (default) and `cascade` are
constructor options, not macros — switching rebuilds nodes, which the
real-time rule forbids.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Fuzz | UNIPOLAR | pre-gain 18…54 dB | the 1 kΩ Fuzz pot; `cascade`'s Sustain pot |
| 1 | Level | UNIPOLAR | −∞…0 dB | the 500 kΩ Volume pot |
| 2 | Tone | UNIPOLAR | 0…1, centre = the notch | the Big Muff tone pot; **inert on `germanium`**, which has no tone control (G4) — the docstring says so |
| 3 | Bias | BIPOLAR | 0 = the sourced −1.6 V point | the bias trimmer builders fit; one end is starved and gated |
| 4 | Load | UNIPOLAR | 0 = wire, 1 = the sourced 5–8 kΩ into a pickup-like source | the pedal's place in the chain (S1, S4) |
| 5 | Mix | UNIPOLAR | 0…1, 0 is the wire | the contract's Tier 1 wire |
| 6 | Output Tilt | BIPOLAR | ±6 dB above 1 kHz | no panel control — one concession to a host sitting a fuzz in a mix; defaults to 0, where G4 must hold |

Patches: 0 "Bias centred, fuzz half" (default), 1 "Full fuzz, volume back",
2 "Starved bias, gated", 3 "Cleaned up, load engaged", 4 "Cascade, scoop
centred", 5 "Cascade, sustain maximum", 6 "Cascade, treble end", 7 "Lean"
(the ESP32-S3 patch — oversampling ×2).

## 7. Defects in the current class the rebuild must not repeat

From one read of `drive.py:104-120` and one measurement run.

- `drive.py:117` — the class is `audiofilters.Distortion` in **CLIP** mode, …  *(argument in full: App. R)*
- `drive.py:115` — `drive=0.95` is an exponent of 0.0501
  (`audioif_distortion.c:57`), very nearly `sign(x)`; above about 0.6 nothing
  is distinguishable from a comparator.
- `drive.py:111` — `MACRO_LABELS = ()`: the Fuzz knob, the thing the pedal is …  *(argument in full: App. R)*
- `drive.py:118` — `pre_gain=18.0, post_gain=-9.0`, constants tuned at one
  input level; behind a scale-invariant curve they only place the 16-bit
  clamp.
- No second character: the Big Muff is absent, and `Fuzz` differs from
  `Distortion` only by 12 dB of pre-gain (`drive.py:118` against `:99`).

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **A germanium device model.** G1's asymmetry ratio is sourced, the knee is
   not; it wants Ebers-Moll parameters for an AC128 or NKT275 plus S3's
   leakage. Manufacturers' model files are not permissive, so the routes are
   a published parameter set or a fit to a measured curve in a document.
   *Station A;* failing that, the class ships the sourced ceilings with a
   stated knee and says so in the docstring.
2. **Gating** — whether the sputter is a signal-dependent bias shift at all,
   and what sources it. *Phase 0 audit, then the implementation session.*
3. **Which Big Muff** — S6 records era-to-era spread; the class names its
   revision in the docstring and C3's tolerance is stated against it.
   *Implementation session.*
4. **Oversampling factor** for A4 on the ESP32-S3 within Tier 3 — drive-family
   wide, answered once by Phase 1's cost/alias table.
5. **The ElectroSmash licence line** was read on the mirror for S1 and S5;
   the site's own rights page was not fetched. *Phase 0 audit.*
6. **What `Load` loads** — nothing sourcing a pickup's L/R/C was reached, so
   macro 4's far end is the sourced input impedance against a documented
   constant source. *Station A.*
7. **Does the Big Muff's notch centre move with the knob?** C4, raised by the
   trait-critic pass and left *unmeasured*: neither S5 nor S6 states it, and
   the "< ⅓ octave" the first draft asserted was never derived. Two routes,
   either of which turns C4 into a graded row — solve the five-part stack
   symbolically or in ngspice the way `Overdrive` solved the TS808 tone stack
   (`tools/spice/ts808/`), or find a source that measures it. Until then the
   rebuild reports the number and is not graded on it. *Station A.*

**Trait count after the critic pass.** `germanium` carries four graded rows
(G1–G4) and `cascade` three (C1–C3) plus the shared A4, so both characters
clear vision §3's three-per-character bar without counting C4. Nothing here
is short.

*(More of §8 is in **App. R** — moved under the length rule, nothing deleted.)*

## Appendix

### A1. Derivations from the sourced values

**Headroom asymmetry (G1).** S1's text says Q1's collector "sits around
-1.6V" with a 9 V supply and the Fuzz pot at its midpoint (500 Ω): it can
swing 1.6 V toward ground before saturation and 9 − 1.6 = 7.4 V toward the
rail before cutoff — 4.63:1, or 13.3 dB. *Audit note on attribution:* S1's
per-node bias table is an image and was not read, so −1.6 V is taken from
S1's prose, and the −4.5 V S1 gives for Q2 is a **target**, quoted in the same
sentence as the Q1 target — it is not a measurement this run reached, and it
is exactly mid-rail (V_CC/2), not "0.5 V off" it as the first draft said. The
first stage is what G1 names, as S1 does. S1's stated *target* for Q1 is
"Q1VC=-0.5 to -0.7"; S8 independently says Fuzz Faces "naturally tend to bias
with only about half a volt on the collector of the first transistor". At that
bias the asymmetry is larger still (0.6 V against 8.4 V, 23 dB), so G1's
13.3 dB is the conservative end of a range two sources agree on — which is the
end a trait should be stated at.

**Corners (G4).** S1's three high-passes: 14 Hz (2.2 µF into ≈5 kΩ), 7.9 Hz
(20 µF on the emitter network), 31 Hz (0.01 µF into the 500 kΩ Volume pot).
Cascaded as three first-order sections they are down **0.51 dB at 100 Hz**,
0.01 dB at 1 kHz, **2.71 dB at 40 Hz**, and reach −3 dB at **37.6 Hz** — hence
G4's two numbers, both of which still hold. *(The first draft printed "0.9 dB
at 100 Hz" and "−3.1 dB at 41 Hz"; the second audit pass recomputed the
cascade and neither reproduces. The trait as stated — flat within 1 dB from
100 Hz, no more than 3 dB down at 40 Hz — is unaffected and is if anything
comfortably met.)*

**Tone stack (C3).** S6 lists the 1973 Ram's Head as R5 33k / R8 33k / C8
0.01 µF / C9 0.004 µF and prints the pair "(482 / 1206 Hz)" itself; the
arithmetic checks — 1/(2π·33 kΩ·10 nF) = 482 Hz and 1/(2π·33 kΩ·4 nF) =
1206 Hz. S6's *text* introduces the pair as "high-pass and low-pass" in that
order, which is the wrong way round: the larger capacitor is the low-pass arm,
and it has to be, or the two arms would overlap between 482 and 1206 Hz and
give a mid *bump* instead of the scoop both sources describe. So 482 Hz is the
low-pass and 1206 Hz the high-pass. **Which resistor goes with which cap is
recoverable from S6's own asymmetric rows**, and the second audit pass did
that rather than assume it: the Civil War row (R₅ 22k, R₈ 20k, C₈ 10 nF, C₉
3.9 nF → "796 / 1855 Hz") only reproduces as R₈·C₈ then R₅·C₉, and the "Flat
mids" row (22k / 39k, 10 nF / 10 nF → "408 / 723 Hz") reproduces the same way.
So the first printed number is always R₈–C₈, the low-pass arm.

S5's independently measured 1 kHz notch sits between the '73 arms — but S5's
own BOM is **22 kΩ and 39 kΩ**, not two 33 kΩ, which on that pairing is
**408 / 1809 Hz**: S6's *Ram's Head '75* row. The depth/centre figures and the
arm values therefore come from different revisions, and further apart than the
first draft's "408 / 1020 Hz" (which assumed both arms were 39 kΩ) suggested
(C3).

**The S1/S2 "conflict" the audit could not reproduce.** The first draft
recorded S2 as calling the 8.2 kΩ an emitter resistor, against S1's collector
load. Re-read in full, S2 says no such thing: its only mention is that the
Analog.Man Sunface replaces "the 8.2k resistor … with a 2.2k resistor plus a
5k linear potentiometer" and that this "allows you to set the bias of the
second resistor" — S2's own words, *sic*; the first audit rendered them as
"the second [transistor]", which is what S2 evidently means but not what it
says, and S2 never assigns the part a role at all. That it is a collector load
is **S1's** statement, not S2's. **There is no conflict; the claim is
withdrawn.** S1 stands on its own: 470 Ω + 8.2 kΩ in
Q2's collector load, (470+8200)/1000 = 8.2 (18 dB) minimum stage gain, and S8
gives the same topology in words. Two further audit notes on S2: the page is a
*Sunface* analysis (a modified Fuzz Face), and its own comment thread carries
an author-acknowledged error in its schematic — R4 drawn as 470 kΩ where it
must be 470 Ω, acknowledged in 2017 and still uncorrected when a reader
re-reported it in 2020. Nothing in this dossier depends on S2's drawing.

### A2. Measurements of the existing palette, this run

CPython audioif from `audiocomponents/.venv`; `audiofilters.Distortion` on a
1 kHz sine, `soft_clip=False`, `pre_gain=post_gain=0`, `mix=1`; dBc:

| mode | drive | in | h2 | h3 | h4 | h5 |
|---|---|---|---|---|---|---|
| CLIP | 0.9 | −20 dBFS | −152.2 | −10.8 | −159.2 | −15.9 |
| CLIP | 0.9 | −6 dBFS | −152.2 | −10.8 | −159.2 | −15.9 |
| WAVESHAPE | 0.9 | −20 dBFS | −153.3 | −16.5 | −165.0 | −26.1 |
| WAVESHAPE | 0.9 | −6 dBFS | −152.4 | −11.7 | −160.4 | −18.0 |
| OVERDRIVE | 0.2 / 0.5 / 0.9 | −20 dBFS | −37.1 | −44.5 | −71.5 | −56.7 |
| OVERDRIVE | 0.2 / 0.5 / 0.9 | −6 dBFS | −25.4 | −35.7 | −51.2 | −50.6 |

CLIP's two rows are identical (the homogeneity of `pow(|x|,d)`); OVERDRIVE's
three drive values are identical to each other at both levels (the inert
argument, `upstream-diff.md:1228`); h2 sits at the numerical floor for CLIP
and WAVESHAPE at every setting.

Alias floor — non-harmonic energy relative to the whole spectrum, −6 dBFS:

| mode | drive | 1010 Hz | 3700 Hz |
|---|---|---|---|
| CLIP | 0.95 (the shipped `Fuzz`) | −19.6 dB (peak −29.5 dBc) | −13.1 dB (peak −17.9 dBc) |
| WAVESHAPE | 0.9 | −38.5 dB | −20.1 dB |
| OVERDRIVE | 0.5 | −71.7 dB | −47.1 dB |

**A probe note for the kit spec.** A 1000 Hz probe measures *nothing* here:
every alias of a harmonic of an exact sub-multiple of the sample rate folds
back onto the harmonic grid and hides inside it — measured −128.9 dB, which
is not an alias floor but an artefact of the probe. Absence reading as
agreement, this workspace's signature checker failure. 1010 Hz and 3700 Hz
are the honest probes; the kit spec should fix them as such.

### A4. Palette verification, 2026-09-06 (palette verifier)

Every §4 and §5 claim about what an audioif node can or cannot do, checked
against the C under `audioif/src/shared` and the bindings under
`audioif/src/<module>/` with `grep -n`, and probed on the CPython audioif in
`audiocomponents/.venv`. All at 48 kHz, mono, 16-bit.

**Distortion node, re-measured** (`soft_clip=False`, `pre_gain=post_gain=0`,
`mix=1`, 1 kHz, 48000-point DFT; dBc). Reproduces A2 for every graded figure:

| mode | drive | in | h2 | h3 | h4 | h5 |
|---|---|---|---|---|---|---|
| CLIP | 0.9 | −20 dBFS | −337.5 | −10.8 | −346.9 | −15.9 |
| CLIP | 0.9 | −6 dBFS | −332.0 | −10.8 | −333.5 | −15.9 |
| WAVESHAPE | 0.9 | −20 dBFS | −334.6 | −16.5 | −339.2 | −26.1 |
| WAVESHAPE | 0.9 | −6 dBFS | −333.6 | −11.7 | −335.9 | −18.0 |
| OVERDRIVE | 0.2 / 0.5 / 0.9 | −20 dBFS | −37.1 | −44.3 | −71.1 | −56.8 |
| OVERDRIVE | 0.2 / 0.5 / 0.9 | −6 dBFS | −25.4 | −35.7 | −51.2 | −50.5 |

The three OVERDRIVE drives are identical to the digit at both levels, which is
the inert argument (`upstream-diff.md:1228`, heading verified) confirmed a
second time by measurement rather than by the note; its h2 rises 11.7 dB over
a 14 dB input rise, 0.84 dB/dB. Alias floor, non-harmonic energy against the
fundamental at −6 dBFS: CLIP 0.95 reads −18.8 dB at 1010 Hz, −12.4 dB at
3700 Hz and −318.6 dB at 1000 Hz; WAVESHAPE 0.9 −38.1 / −19.7; OVERDRIVE 0.5
−78.9 / −55.9. (A2's OVERDRIVE figures, −71.7 / −47.1, differ by the width of
the harmonic mask; both are far above A4's −60 dB bar and nothing rests on
which.)

**The composition refutation for G1/G2** (§5): sine plus DC offset into CLIP
`drive=0.9`, DC removed after, 1 kHz.

| offset | THD across −40 → −6 dBFS in 6 dB steps (dB) |
|---|---|
| 0.05 | −26.79 → −20.51 → −12.60 → −3.08 → **−6.54** → **−7.51** → **−7.93** |
| 0.10 | −32.91 → −26.88 → −20.53 → −12.65 → −3.07 → **−6.54** → **−7.40** |
| 0.20 | −37.74 → −32.85 → −26.85 → −20.53 → −12.68 → −3.06 → **−5.62** |
| 0.30 | −40.77 → −36.32 → −30.48 → −24.32 → −17.68 → 2.15 → **−4.13** |

Bold entries are steps where THD *fell*. h2 tracks it: at offset 0.10 it runs
−32.9 → −26.9 → −20.6 → −13.1 → **−4.8 → −10.8 → −15.1** dBc.

**Filters.** `synthio.FilterMode` exposes seven modes, all second-order RBJ
(`audioif_biquad.c:76-112`); `audiofilters.Filter` accepts a cascade of
Biquads but no one-pole. Magnitude, measured against the closed form:

| asked for | probe | `audiofilters.Filter` | `audioecho.FeedbackDelay` one-pole | one-pole ideal |
|---|---|---|---|---|
| HP 31 Hz | 10 Hz | −19.70 | −10.27 | −10.27 |
| HP 31 Hz | 20 Hz | −8.31 | −5.34 | −5.34 |
| HP 31 Hz | 31 Hz | −3.01 | −3.03 | −3.03 |
| HP 31 Hz | 62 Hz | −0.26 | −0.99 | −0.99 |
| LP 5 Hz | 100 Hz | −52.03 | −26.03 | −26.03 |
| LP 5 Hz | 800 Hz | −87.12 | −44.08 | −44.08 |

The one-pole route is `audioecho.FeedbackDelay(feedback=0, mix=2.0,
delay_ms=1 frame, cut_hz=…)` for the high-pass and `damping_hz=…` for the
low-pass; it click-measures **1 sample** of latency.

**DC hold after a burst** (burst then silence in one non-looping RawSample, so
the node keeps pulling real zeros; 48 kHz; magnitude of the settled tail one
second on, in LSB):

| section | 5 Hz | 14 Hz | 31 Hz | 40 Hz q=8 | 100 Hz | 1000 Hz |
|---|---|---|---|---|---|---|
| `audiofilters.Filter` HIGH_PASS | 284 | 36 | 7 | 4 | 1 | 0 |
| `audiofilters.Filter` LOW_PASS | 284 | 36 | 7 | 4 | 1 | 0 |
| `audioecho.FeedbackDelay` one-pole | 0 | 0 | 0 | — | — | — |

The 100 Hz and 40 Hz/q=8 columns are audioif#23's own published numbers,
reproduced, which is what says the probe is reading the right thing.

*Checker discipline.* The first attempt at this measurement stopped the
source and read the filter's tail — and `audiofilters.Filter` renders exact
zeros the moment its source stops, so **every configuration read "clean"**.
That is absence reading as agreement, the workspace's signature failure
(`agent-knowledge/workspace-craft.md`). The table above comes from the fixed
harness, which carries a control that must pass (a wire reads 0) and a planted
fault that must fire (0.99 feedback at 250 ms reads 15775 one second on). The
loop-area measurement used for the sibling `Saturation` A5 refutation carries
the same pair: a wire reads exactly 0.0 area, a one-sample lag reads 2.78e−6.

**Gain.** MixerVoice level is clamped `0.0..1.0`
(`src/audiomixer/Mixer.c:332`; measured, level 2.0 and 4.0 render the same
peak as 1.0), `audiomath.Multiply` scales by `>> 15` so a full-scale modulator
is unity and never more (`audioif_multiply.c:38`), and
`audiofilters.Distortion`'s `pre_gain`/`post_gain` are the palette's only
above-unity gain (`audioif_distortion.c:53-54`).

### A3. What each source gave, in detail

**S1** — component values (33 kΩ, 470 Ω, 8.2 kΩ, 100 kΩ, 2.2 µF, 20 µF,
0.01 µF, 1 kΩ lin Fuzz, 500 kΩ log Volume, AC128 PNP pair); bias Q1 −1.6 V,
Q2 −4.5 V, target "Q1VC=-0.5 to -0.7 and Q2VC=-4.5V"; corners 14 / 7.9 /
31 Hz; input impedance "between 5.2KΩ and 8.4KΩ in the simulation"; output
impedance 15 kΩ at 1 kHz; input-stage gain 49 dB open-loop, 18.6 dB with
feedback; output stage "AVmin=(470+8K2)/1K= 8.2 : (18dB)", 19.5 dB at Q2's
collector; "the frequency response of the Fuzz Face is not very innovative,
it just removes some bass and keeps all the highs"; "soft asymmetric
distortion to small signals and clipping harder in both semi-cycles on big
input signals"; germanium leakage and gain inconsistency; β 70–80 / 110–130 recommended
(and 90–120 / 150–190 for "a more compressed sound"); the simulated pair is
β=85 / β=120; **and, at the foot of the article, two AC128 PSpice `.MODEL`
cards** — `GERPNP_LOWGAIN` (BF=85) and `GERPNP_HIGHGAIN` (BF=120), each a full
Gummel-Poon parameter set (IS, VAF, IKF, ISE/NE, ISC/NC, RB/RE/RC, CJE/CJC,
TF/TR, EG=0.670, …). Reached by the audit, not by the first pass. Per the
sources module's rule for device models, the *parameter values* are facts
about the part: they go into our own `.model` line with this URL cited, and
the file is not copied.
**S3** — β 70–85 / 120–140 (and 90–120 / 150–190 as an alternative pairing),
leakage under 300 µA at room temperature, "The temperature sensitivity of
older germanium transistors has to be seen to be believed", and the pointer
to S8: "if you want an explanation of how the Fuzz Face works and why gain
matters, go to the scriptures: R. G. Keen 'The Technology Of The Fuzz Face'".
**S8** — "Copyright 1998 R.G. Keen All Rights Reserved"; the voltage-feedback
topology and its "very low input impedance, which means that it heavily loads
anything trying to drive it"; the signal-dependent bias shift quoted in §3;
"Fuzz Faces naturally tend to bias with only about half a volt on the
collector of the first transistor"; "the Fuzz Face has asymetrical clipping
designed into it"; the second stage's gain "can vary from a low of about 8 to
as high as the transistor's basic internal gain when the pot is maxxed out";
and, for macro 4, that "the base can only move a few tens of millivolts before
cutting off or saturating the first transistor", so a series resistor ahead of
the input cap "raises the apparent source impedance of the pickup, making it
look more like a current source … allow[ing] you to radically clean up the
distortion".
**S5** — an "American Version 3 … released in 1976-1977"; BC239-class
transistors, 1N914/1N4148 pairs, R11/R12/R13/R18/R19 10 kΩ, R9/R15/R17 470 kΩ,
R2/R8 39 kΩ, R5 22 kΩ, R6 15 kΩ, R4 3.3 kΩ, C8 10 nF, C9 4 nF, C1/C4/C6/C7
1 µF; first stage ~23 dB and second ~25 dB, output stage 15 kΩ/3.3 kΩ = 13 dB,
tone notch, verbatim: "There is an overall 7dB loss and at the notch, the loss
is about 6.5db (-13.5db total) at 1KHz"; "The 100K sustain potentiometer
controls the level of the signal going into the clipping blocks". *Two audit
notes on S5's internal consistency, from the second pass:* its BOM puts 1 µF
on C6/C7 while its text calls C6/C7 "the Miller Capacitors … rolling-off
around 1KHz", which 1 µF across a 470 kΩ feedback loop cannot be — the BOM and
the text disagree and nothing in this dossier rests on either value; and it
calls R2 (39 kΩ) the input booster's input resistor, which is why the tone
arms it leaves are R8 39 kΩ and R5 22 kΩ (A1, C3).
**S6** — Ram's Head ('73) arms 33 kΩ + 4 nF and 33 kΩ + 10 nF, printed by S6
itself as "(482 / 1206 Hz)"; "the cutoff frequencies are clearly in the
midband range (between 200 - 2500 Hz approximately)"; "The tone potentiometer
mixes the two filters to let more or less bass / treble going through". *Two
audit corrections:* S6 does **not** contain the sentence "does not shift the
notch frequency" — that quotation was struck; and its Russian entries are
R5 22k / R8 20k / C8 0.01 µF / C9 0.0039 µF (796 / 1855 Hz), not "430 / 470 /
500 pF", which appears nowhere on the page. The page's actual era spread is
Triangle 22k/22k, Ram's Head '73 33k/33k, Ram's Head '75 22k/39k, Civil War
and both Russians 22k/20k.
**S9** — the Fuzz-Face and the Rangemaster as its two case studies; a Fuzz
Face schematic (Fig. 9); output cycles at maximum fuzz (Fig. 11); measurement
ranges (common-emitter Ib 26–1000 µA, Vec −5…5 V for the AC128); and a cost
table — DC Ebers-Moll 341.6 ms per second of Fuzz-Face simulation against
819.1 ms for DC Gummel-Poon, which is the trade §8 Q1's successor chooses
between. Its **AC128** parameters, extracted from its own measurements
(Table 1; Ebers-Moll then Gummel-Poon where both are given): Is 23.75 µA /
20.66 µA, βf 44.90 / 229.6, βr 4.568 / 14.66, Nf 1.168 / 1.133, Nr 1.171 /
1.140, Vt 25.5 mV; Gummel-Poon only — Vaf 19.68 V, Var 88.28 V, Ikf 463.0 mA,
Ikr 241.5 mA, Ise 2.190 µA, Isc 7.546 µA, Ne 1.796, Nc 1.364, Rb 1.885 Ω,
Re 306.4 mΩ, Rc 1.727 µΩ, Ccb 100 pF. Per the sources module's rule, these are
facts about the part: they go into our own model with S9's URL cited, and the
paper is not copied. Not consulted for §3 — the traits here stay as the first
pass fixed them, and fixing one from S9 is Station A's call.
**S7** — Ebers-Moll I-V equations; 8× oversampling of a 48 kHz system with
Backward Euler in the paper's own experiments; the nonlinearity solved
offline and stored as a table read by multidimensional linear interpolation,
with a 100×100 table "nearly identical to LTspice" for the BJT stage and
50×50 "clearly deficient". *Audit note:* the paper's body describes the coarse
table as "25 steps for each dimension" while its figure captions label the same
trace "50x50" — S7 is internally inconsistent there, and "clearly deficient" is
its verdict on the coarse table however it is sized.

### Trait-critic pass — the record

2026-09-06, after the two licence audits and independent of them. Every Tier 2
row re-read against vision §3's bar — a statement a measurement can fail —
with S1, S5 and S6 re-fetched with WebFetch and re-read, the G4 corner cascade
recomputed, and A2's palette measurements re-run against the CPython audioif
build. Nine rows after the pass: **G1–G4** (germanium, all graded), **C1–C3**
(cascade, all graded), **C4** (*unmeasured*, split out of the old C3), and the
shared **A4**.

**What was not falsifiable as written, and what each rewrite did.**

1. **G1 and C1 carried a dead band.** Each set a bar at −40 dBc and a
   disconfirmation at −30 dBc, leaving a 10 dB band in which a measurement
   could neither confirm nor disconfirm the trait. Both disconfirmations are
   now the complement of the bar, and G1 says explicitly that a partial result
   is recorded as a partial.
2. **C1 could be decided by the tone stack rather than the clippers.** Its h2
   and h4 land at 2 kHz and 4 kHz, which the Big Muff tone stack moves by many
   dB; the row now divides each harmonic by the class's own measured magnitude
   at that frequency, taken from C3's sweep.
3. **C2's two numbers read as S5's.** S5 gives no THD or level figure across
   the Sustain pot; the ≥ 25 dB and < 6 dB are this class's design bars and
   the confidence cell now says so.
4. **C3 hid an unsourced claim behind two sourced ones.** "Its centre moves
   < ⅓ octave" was labelled *derived* with no derivation anywhere in the file,
   and S6 — re-read in full this run — makes no statement either way; the
   clause is split out as **C4** and marked *unmeasured*, and C3 keeps the
   parts S5 and S6 do support. C3 is now graded against the arm corners of
   whichever revision §8 Q3 ships, not against a fixed 1 kHz that belongs to a
   different revision from its arm values.
5. **A4 did not name its oversampling setting.** Patch 7 "Lean" runs ×2; an
   unqualified alias-floor row would either fail on the lean patch or let it
   hide. It is now graded at the shipped setting and reported at the lean one.
6. **G3 ended in a dangling arithmetic fragment** ("S1's low end is
   (470+8200)/1000 = 8.2, 18 dB") that asserted nothing a measurement could
   fail; it moved to the source column as context. G3 and G4 now name the
   settings they are swept at, and G4 says the magnitude is the fundamental's
   — at −6 dBFS a broadband magnitude measures the distortion, not the
   response.

**What was re-verified rather than taken on trust.**

- S1 (ElectroSmash Fuzz Face, MAS Effects mirror), S5 (Big Muff analysis) and
  S6 (Coda tone stack) all answered HTTP 200 and every figure the Tier 2 rows
  use was re-read: Q1's collector "around -1.6V"; the three corner
  calculations 14 / 7.9 / 31 Hz; "AVmin=(470+8K2)/1K= 8.2 (18dB)"; the input
  impedance "between 5.2KΩ and 8.4KΩ"; S5's ±0.6 V clipping, 23 / 25 dB stage
  gains, the 6.5 dB notch sentence and its BOM (R₂ 39 k, R₅ 22 k, R₈ 39 k,
  C₈ 10 nF, C₉ 4 nF); S6's five era rows and its tone-pot sentence. S6's
  R₈–C₈ / R₅–C₉ arm pairing re-derived from its own asymmetric rows.
- **S6 confirms it says nothing about the notch centre moving** — the basis
  for C4.
- **G4's cascade recomputed independently:** three first-order high-passes at
  14 / 7.9 / 31 Hz give −0.510 dB at 100 Hz, −2.711 dB at 40 Hz and −3 dB at
  37.6 Hz, reproducing A1 to the digit.
- **A2 re-measured on the CPython audioif build:** CLIP's harmonics identical
  at −20 and −6 dBFS (h3 −10.8, h5 −15.9 dBc at both), h2/h4 at the numerical
  floor; WAVESHAPE odd-symmetric and level-dependent; OVERDRIVE asymmetric
  (h2 −37.1 → −25.4 dBc, 0.84 dB/dB) with `drive` inert at 0.2 / 0.5 / 0.9.
  Alias floor at −6 dBFS on the shipped `Fuzz` curve: **−319.5 dB with a
  1000 Hz probe, −11.8 dB at 1010 Hz, −11.0 dB at 3700 Hz** — the same
  conclusion the first pass reached, and the reason the probe frequencies are
  now written into A4.

**What this pass did not do.** No source was added, no bar was loosened, no
row was deleted, and §§1, 2, 4–7 were not edited. Two items were added to §8
(C4's route to becoming graded, and the trait count).

### Audit record — the second licence and citation pass

Independent of the first audit and of the research pass. Every row in §2 was
fetched again with `curl`, every PDF re-extracted with `pypdf`, and every
quotation and number in §1–§3 checked against the returned bytes rather than a
fetch-tool summary.

**What held.** All nine rows HTTP 200, S8 at 24 549 bytes and S9 at
728 338 bytes. Every licence call in §2 confirmed as written: S1's "Some
Rights Reserved, you are free to copy, share, remix and use all material" and
the mirror's "unofficial, non-commercial backup … All content and images
belong to their original authors/owners"; S2's and S6's "Coda Effects All
Right Reserved"; S3's article page carrying no rights line while
`diy.smallbearelec.com`'s home footer carries "Copyright © 2013 Small Bear
Electronics LLC All Rights Reserved"; S4's "Text is available under the
Creative Commons Attribution-ShareAlike 4.0 License"; **S5 still carrying no
ElectroSmash rights line at all**, which is what keeps it unverified rather
than "as S1"; S7's "Copyright (c) 2010 IEEE. Personal use of this material is
permitted"; S8's "Copyright 1998 R.G. Keen All Rights Reserved". No link is
dead and no licence call moved. `electrosmash.com` still does not resolve
(`getent hosts` → not found, third check). Both "not found" claims the first
audit overturned stay overturned: geofex answered on the first try again, and
S1's two AC128 `.MODEL` cards are on the page.

**What moved.**
1. **The Big Muff tone arms** (§1, C3, A1). The first draft read S5's BOM as
   two 39 kΩ and printed "408 / 1020 Hz". S5's BOM has *one* spare 39 kΩ (R₈);
   the other, R₂, S5 itself calls the input booster's input resistor, and its
   remaining tone-arm candidate is R₅ = 22 kΩ. With S5's C₈ 10 nF and C₉ 4 nF
   that is **408 / 1809 Hz** — S6's *Ram's Head '75* row exactly, which S6
   annotates "big scoop of the mids". The arm/cap pairing was *derived* from
   S6's own asymmetric rows rather than assumed: only R₈–C₈ then R₅–C₉
   reproduces its printed Civil War (796 / 1855 Hz) and "Flat mids"
   (408 / 723 Hz) pairs.
2. **The clipping stages' capacitors** (§1). "Each fed through a 1 µF series
   capacitor" is not S5's account: S5 puts 1 µF on C₆/C₇ and calls those the
   *Miller* caps of the clipping loops, with the series input decoupling caps
   named separately. S5's own BOM and text disagree about the Miller value —
   1 µF cannot give its stated ≈1 kHz corner across a 470 kΩ loop — so the
   value is recorded and used for nothing.
3. **One quotation of S2** (A1). The page reads "allows you to set the bias of
   the second **resistor**"; the first audit printed "the second
   [transistor]", which is what S2 means but not what it says, and S2 assigns
   the part no role at all — the collector-load reading is S1's.
4. **The cascaded corner arithmetic** (A1). Three first-order high-passes at
   14 / 7.9 / 31 Hz give −0.51 dB at 100 Hz and −3 dB at 37.6 Hz, not the
   "0.9 dB" and "41 Hz" the first draft printed. G4's stated bars are
   unaffected and comfortably met.
5. **A false "not found"** (§2). "A DAFx/AES/JAES paper on this circuit: none"
   is wrong; **S9** is one, with measured AC128 parameters, and it overturns
   §8 Q1's premise a second time.

**What was deliberately not done.** No trait was added, dropped, renumbered or
re-toleranced, and §4–§8 were not edited — including §8 Q1, Q2, Q5 and Q6,
which are written against premises two audits have now moved and are Arthur's
to update. Fixing a trait from S9 is Station A's call, not an auditor's.

<!-- Phase 0 seed, fuzz-saturation unit, 2026-09-06. S1-S7 fetched by the
research pass; geofex.com attempted there and timed out. Palette numbers
measured from audiocomponents/.venv (CPython audioif). No prior draft existed.

Licence and citation audit, same day, independent re-fetch of every row and
URL with curl + pypdf (not a fetch-tool summary). Corrections applied here:
S1's licence quoted verbatim and its AC128 model cards added; S2's licence
corrected to all-rights-reserved and the 8.2 kΩ "conflict" withdrawn (S2 is a
Sunface article whose schematic carries an author-acknowledged error); S3's
site-wide all-rights-reserved recorded; S5 separated from S1 — that page
carries no ElectroSmash rights line, so licence unverified/copyleft; S6's
licence corrected, one fabricated quotation struck and one fabricated
component range struck; S8 (GEOFEX/Keen) added, which overturns the "not
reached" claim and sources the gating mechanism; the Big Muff tone arms'
LP/HP labels corrected in §1; the mid-rail arithmetic in A1 corrected. §4-§8
were left untouched by the audit: §8 Q1, Q2, Q5 and Q6 are written against
premises the audit overturned and are Arthur's to update.

Second licence and citation audit pass, same day, independent of the first:
every row fetched again with curl/pypdf and every §1-§3 quotation checked
against the returned bytes. All eight original rows HTTP 200; every licence
call confirmed as written; electrosmash.com still does not resolve. New
corrections: S9 added (Holmes/Holters/van Walstijn, DAFx-17, measured AC128
Ebers-Moll and Gummel-Poon parameters with the Fuzz Face as a case study),
which withdraws the "no DAFx/AES/JAES paper on this circuit" claim and
overturns §8 Q1's premise a second time; the Big Muff arm values corrected to
S5's actual BOM (22k/39k, 408/1809 Hz, not "39k/408/1020 Hz") in §1, C3 and
A1, with S6's R8-C8 / R5-C9 pairing derived from its own asymmetric rows
rather than assumed; the clipping stages' "1 uF series capacitor" struck from
§1 (S5 puts its 1 uF on the Miller caps, and its BOM and text disagree there);
S2's "second [transistor]" restored to the page's own "second resistor" and
the collector-load role reattributed to S1; the cascaded corner arithmetic in
A1 recomputed (0.51 dB at 100 Hz, -3 dB at 37.6 Hz, not 0.9 dB and 41 Hz) with
G4's bars unaffected. Sections 4-8 untouched again; no trait was added,
dropped or renumbered. -->

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

*The wire is `Mix = 0`* — neither character is clean anywhere else. *Rate:*
A4 holds at 48 and 44.1 kHz; at 22.05 kHz a square's series cannot fit under
Nyquist, so A4 is not claimed there. *`capabilities` = `()`* (D10): no LFO,
no delay, nothing reads `transport()`.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 ElectroSmash, "Fuzz Face Analysis" (MAS Effects mirror) | topology, values, bias points, corners, Zin/Zout, stage gains, the clipping description — **and two AC128 PSpice `.MODEL` cards** (β=85 `GERPNP_LOWGAIN`, β=120 `GERPNP_HIGHGAIN`) at the end of the article | ElectroSmash's own footer, preserved by the mirror, reads verbatim: *"Some Rights Reserved, you are free to copy, share, remix and use all material."* No named licence instrument, so no permissive call is made: read as a document (vision §5), values and model parameters cited as facts about the circuit in our own words, nothing reproduced. The mirror adds *"An unofficial, non-commercial backup of ElectroSmash.com … All content and images belong to their original authors/owners."* `electrosmash.com` itself still does not resolve from this machine (`getent hosts` → not found, audit run), so the site's canonical rights page cannot be reached at all | https://electrosmash.mas-effects.com/fuzz-face.html | yes — audit run 2026-09-06, HTTP 200 |
| S2 Coda Effects, "Sunface / Fuzzface circuit analysis" | confirms the 100 kΩ feedback path and the 2.2 µF input coupling cap; describes the **Sunface**, a Fuzz Face "slightly modified", and treats the 8.2 kΩ as the resistor a Sunface swaps for a bias trimmer | **All rights reserved** — the page footer states "Copyright © Coda Effects 2015 – …" and "Coda Effects All Right Reserved". Document, read only | https://www.coda-effects.com/p/circuit-analysis-fuzz-face.html | yes — audit run 2026-09-06, HTTP 200 (article body is in the page's `post-body` div; a naive tag-strip returns only chrome) |
| S3 Small Bear, "5F" Fuzz Face FAQ | hFE 70–85 / 120–140 (and 90–120 / 150–190 as the "squishy" pairing), leakage "under 300 microamps", temperature sensitivity, and the pointer to S8 as "the scriptures" | The article page carries no rights line, but the site does: `diy.smallbearelec.com`'s own home page footer reads "Copyright © 2013 Small Bear Electronics LLC All Rights Reserved." — **verified all-rights-reserved**, not merely unverified. Document, read only | https://diy.smallbearelec.com/HowTos/FuzzFaceFAQ/FFFAQ.htm | yes — audit run 2026-09-06, HTTP 200 |
| S4 Wikipedia, "Fuzz Face" | germanium→silicon history; "The Fuzz Face has a low input impedance and thus is very sensitive to the guitar pickup"; clean-up on the guitar volume | CC BY-SA 4.0, stated on the page ("Text is available under the Creative Commons Attribution-ShareAlike 4.0 License") | https://en.wikipedia.org/wiki/Fuzz_Face | yes — audit run 2026-09-06, HTTP 200 |
| S5 ElectroSmash, "Big Muff Pi Analysis" (same mirror) | four stages (19.6 / 23 / 25 / 13 dB), ±0.6 V clipping in the collector–base loops, the 1 kHz 6.5 dB notch, Sustain's role, the full BOM — of an "American Version 3 … released in 1976-1977", whose tone-arm candidates are R₅ 22 kΩ and R₈ 39 kΩ with C₈ 10 nF and C₉ 4 nF (the second 39 kΩ, R₂, is the input booster's input resistor by S5's own text) | **Not "as S1".** This page carries **no ElectroSmash rights line at all** — only the mirror's disclaimer that content "belong[s] to their original authors/owners". **Licence unverified — treated as copyleft**: read as a document, nothing reproduced | https://electrosmash.mas-effects.com/big-muff-pi-analysis.html | yes — audit run 2026-09-06, HTTP 200 |
| S6 Coda Effects, "Big Muff tonestack" | the two arms as an era table (Triangle 22k/22k; **Ram's Head '73 33k/33k, C8 0.01 µF, C9 0.004 µF → 482 / 1206 Hz**; Ram's Head '75 22k/39k; Civil War and both Russians 22k/20k, 0.01 µF/0.0039 µF); "the tone potentiometer mixes the two filters"; "The cutoff frequencies are clearly in the midband range (between 200 - 2500 Hz approximately)". It does **not** say the knob leaves the notch frequency in place — that sentence was in the first draft and is not on the page | **All rights reserved** — same footer as S2. Document, read only | https://www.coda-effects.com/p/big-muff-tonestack-dealing-with-mids.html | yes — audit run 2026-09-06, HTTP 200 |
| S7 Yeh, *Automated Physical Modeling of Nonlinear Audio Circuits For Real-Time Audio Effects — Part II: BJT and Vacuum Tube Examples*, IEEE Trans. Speech and Audio Processing 18(3), March 2011 (author's CCRMA copy, read with `pypdf`) | Ebers-Moll eqs (10)–(12); oversampling "typically 4 to 8 times the audio sampling rate, e.g., 8x48 kHz"; solve offline, tabulate, interpolate | "Copyright (c) 2010 IEEE. Personal use of this material is permitted." — not permissive; read as a paper | https://ccrma.stanford.edu/~dtyeh/papers/yeh12_taslp.pdf | yes — audit run 2026-09-06, HTTP 200, 10 pages extracted |
| **S8** R. G. Keen, "The Technology of the Fuzz Face", GEOFEX — *added by the audit; the first pass recorded this as unreachable and it is not* | the voltage-feedback topology; **the signal-dependent bias shift** (below); "Fuzz Faces naturally tend to bias with only about half a volt on the collector of the first transistor"; "the Fuzz Face has asymetrical clipping designed into it"; the input-loading mechanism behind macro 4 | "Copyright 1998 R.G. Keen All Rights Reserved." — explicit, read as a document, nothing reproduced | http://www.geofex.com/article_folders/fuzzface/fftech.htm | yes — audit run 2026-09-06, HTTP 200, 24.5 kB; re-fetched by the second audit pass, HTTP 200, 24 549 bytes |
| **S9** B. Holmes, M. Holters & M. van Walstijn, *Comparison of Germanium Bipolar Junction Transistor Models for Real-Time Circuit Simulation*, DAFx-17, Edinburgh — *added by the second audit pass, which overturns this seed's "no DAFx/AES/JAES paper on this circuit" claim* | the Dallas Arbiter Fuzz-Face as one of its two case studies (the Rangemaster is the other), with its schematic (Fig. 9); **Ebers-Moll and Gummel-Poon parameter sets for a real AC128, extracted from the authors' own bench measurements** (Table 1, values in A3), the extraction procedure, and the per-model cost of running each. This is the "published parameter set" route §8 Q1 asked for, from measurement rather than a vendor file | **No licence statement in the PDF, and none on the DAFx paper archive index** (checked this run: `dafx.de/paper-archive/` carries no rights line). **Licence unverified — treated as copyleft**; read as a paper, nothing reproduced, parameter values cited as facts about the part | https://dafx.de/paper-archive/2017/papers/DAFx17_paper_28.pdf (the DAFx-17 host serves the identical bytes at `www.dafx17.eca.ed.ac.uk/papers/DAFx17_paper_28.pdf`) | yes — second audit pass 2026-09-06, HTTP 200, 728 338 bytes, 8 pages extracted |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| G1 | **Off-centre bias → asymmetric clipping.** Q1's collector sits "around -1.6V" on a −9 V supply (S1, re-read this run), leaving 1.6 V of room one way and 7.4 V the other — 4.63:1, **13.3 dB** (*derived*, A1). Bar, at 1 kHz, −20 dBFS, Fuzz and Bias centred: h2 **≥ −30 dBc** *and* the two output peaks **≥ 3 dB** apart | S1; S8 independently ("about half a volt on the collector of the first transistor" — *more* asymmetric than S1's −1.6 V, so 13.3 dB is the conservative end of a two-source range) | high for the asymmetry and its sign; medium for 3 dB (the knee — now solvable, since the audit reached S1's AC128 model cards) | h2 below −30 dBc, **or** peaks under 3 dB apart, at that level and setting. The two numbers are reported separately: a result that meets one and not the other is recorded as a partial, never rounded to a pass (the trait-critic pass closed a −40/−30 dBc dead band here in which a measurement could neither confirm nor disconfirm) | spectrum of a 1 kHz sine at −20 dBFS, Fuzz and Bias centred, harmonics in dBc; ± peak of the quasi-static transfer curve at the same setting |
| G3 | **Fuzz is gain, not tone and not mix.** At five knob settings (0, 0.25, 0.5, 0.75, 1) the level-normalised magnitude response moves **< 1 dB** over 100 Hz–10 kHz, while THD at a fixed 1 kHz, −20 dBFS input rises at **every** one of the four steps | S1 (the pot removes Q2's emitter degeneration and shunts the AC feedback; DC bias untouched — S1's minimum output-stage gain is "AVmin=(470+8K2)/1K= 8.2 (18dB)", re-read this run, which is context for the knob's low end and not itself a bar); S8 (same mechanism, and that the AC feedback also sets the *first* stage's gain) | medium — read from S1's and S8's prose, not a bias sweep. **Audit caveat:** S1's own response note records a fuzz-position-dependent low-frequency hump from the C₂–R_FUZZ filter, "more noticeable when the gain of the pedal is low"; its corner is S1's 7.9 Hz, under G3's band, which is why the band is stated — the measurement should still report what happens below 100 Hz | the normalised shape moving > 1 dB anywhere in 100 Hz–10 kHz across the five settings; THD falling, or failing to rise, at any step | swept sine at Fuzz 0 / 0.25 / 0.5 / 0.75 / 1, magnitude taken **on the fundamental** and normalised at 1 kHz; THD at 1 kHz, −20 dBFS at the same five settings; the sub-100 Hz magnitude reported but not graded |
| G4 | **Full range: no tone stack.** Three first-order high-passes at 14 / 7.9 / 31 Hz and nothing else (S1): the **fundamental's** magnitude is flat within **1 dB** over 100 Hz–10 kHz at every Fuzz setting, and no more than **3 dB down at 40 Hz** (*derived*) | S1 — all three corner calculations re-read verbatim this run ("1/(2π·5K·2.2uF)= 14Hz", "1/(2π·1K·20uF)= 7.9Hz", "1/(2π·500K·0.01uF)= 31Hz") | high (RC arithmetic on stated values), and the cascade was recomputed independently this run: **−0.51 dB at 100 Hz, −2.71 dB at 40 Hz, −3 dB at 37.6 Hz** — reproducing A1 to the digit | any in-band deviation > 1 dB — a mid hump, a treble roll-off — or a −3 dB corner above 60 Hz | swept sine 20 Hz–20 kHz at Fuzz 0 / 0.5 / 1, at −40 dBFS (near-clean) and at −6 dBFS with the magnitude taken **on the fundamental only** — at −6 dBFS an RMS or broadband magnitude measures the distortion products instead of the response, and the row would pass or fail for the wrong reason |

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| C1 | **Two cascaded symmetric clippers**, ±0.6 V after ~23 and ~25 dB: with the class's own tone-stack response divided out, h2 and h4 sit **≤ −40 dBc**, h3 is the **largest** harmonic above the fundamental, and the output peak grows **< 1 dB** for a 20 dB input rise at Sustain max | S5, re-read this run: "clip the signal when the voltage difference between the *input* (transistor base) and the *output* (transistor collector) is higher than the VF of the diode, which is around 0.6V"; stage gains 23 dB and 25 dB | high | h2 or h4 above −40 dBc after that correction; h3 not the largest harmonic; the output peak growing ≥ 1 dB over the 20 dB rise | spectrum at Sustain max, 1 kHz, Tone centred, **each harmonic divided by the class's own measured magnitude at that harmonic's frequency** (C3's swept sine supplies it) — the tone stack moves 2 kHz and 4 kHz by many dB, so without that correction the notch, not the clippers, decides whether this row passes; output peak at −26 and −6 dBFS |
| C2 | **Sustain is a pre-clip level control**, not a mix and not a volume: from min to max at a fixed 1 kHz, −20 dBFS input, THD rises **≥ 25 dB** while output RMS moves **< 6 dB** | S5, re-read this run: "The 100K sustain potentiometer controls the level of the signal going into the clipping blocks" | high for the mechanism, which is S5's own sentence. **The two numbers are this class's design bars, not S5's** — S5 gives no THD or output-level figure across the pot, and the trait-critic pass relabelled them rather than let the row read as sourced | output RMS moving **≥ 6 dB**, or THD moving **< 25 dB**, across the knob at that level and frequency | THD and output RMS at Sustain 0 / 0.25 / 0.5 / 0.75 / 1, 1 kHz, −20 dBFS |
| C3 | **A fixed mid-scoop between the two tone arms.** With Tone centred the magnitude response has a **single local minimum**, lying **between the shipped revision's two arm corners** (§8 Q3 names the revision), at least **3 dB** below both shelves — S5 measures 6.5 dB on its own unit near 1 kHz — and across the knob 100 Hz and 5 kHz move in opposite directions by **> 15 dB** in total | S5 (depth and the ~1 kHz centre, verbatim this run: "There is an overall 7dB loss and at the notch, the loss is about 6.5db (-13.5db total) at 1KHz"; its own BOM is R₅ 22 kΩ, R₈ 39 kΩ, C₈ 10 nF, C₉ 4 nF → **408 / 1809 Hz**); S6 (the era table and "The tone potentiometer mixes the two filters to let more or less bass / treble going through"; its Ram's Head '73 row is 33 kΩ / 33 kΩ → 482 / 1206 Hz). Both re-read in full this run, and S6's R₈–C₈ / R₅–C₉ pairing re-verified against its own asymmetric rows (Civil War 796 / 1855 Hz, Ram's Head '75 408 / 1809 Hz) | high for the blend mechanism and the arm arithmetic; **medium for the absolute depth and centre**, because S5's 6.5 dB at 1 kHz is measured on a 1976-77 V3 while S6's '73 arms are two 33 kΩ — two revisions. The row is graded against **whichever revision §8 Q3 ships**, and its arm corners, not against a fixed 1 kHz | no local minimum with Tone centred; a minimum outside the shipped revision's two arm corners; a scoop under 3 dB below both shelves; under 15 dB of total 100 Hz–5 kHz tilt | swept-sine magnitude at Tone 0 / 0.25 / 0.5 / 0.75 / 1, the minimum located by parabolic fit; the same sweep supplies C1's harmonic correction |
| C4 | **unmeasured as a circuit trait: whether the notch centre moves with the knob is not sourced, and was not derived.** The first draft asserted "< ⅓ octave" and labelled it *derived*; no derivation exists in this dossier, and neither reached page states it. S6 was re-read in full this run and says only that the pot "mixes the two filters" — it makes no statement either way about the centre, and the earlier quotation to that effect was already struck by the licence audit. The rebuild **reports** the notch centre at C3's five Tone settings as a number; it carries no pass/fail bar until a source or a written derivation fixes it | S6 (silent); S5 (silent) | — | — | reported by C3's sweep, not graded |
| A4 | **Alias floor.** A 1010 Hz sine at −6 dBFS, either character at maximum Fuzz, **on the shipped (non-lean) oversampling setting**: non-harmonic energy **≥ 60 dB** below the fundamental, 20 Hz–20 kHz, at 48 kHz. `Overdrive` T7 and `Distortion` A1's bar, worst here. The setting is named because patch 7 "Lean" drops oversampling to ×2, and an unqualified row would either fail on the lean patch or let it hide | S7 (4–8× oversampling as the norm); the bar is the family's | medium (design bar, not a circuit fact) | non-harmonic energy above −60 dB at either probe, on the P4 or the ESP32-S3 build, at the shipped setting. **The lean patch is measured at the same probes and reported, not graded here** — §8 Q4 owns whether it must also meet −60 dB | non-harmonic bin sum vs the fundamental at **1010 Hz and 3700 Hz**, 48 and 44.1 kHz, shipped and lean patches both reported. A 1000 Hz probe measures nothing — every alias of a harmonic folds back onto the harmonic grid: re-measured this run on the shipped `Fuzz` curve at −6 dBFS, a 1000 Hz probe reads −319.5 dB where 1010 Hz reads −11.8 dB and 3700 Hz −11.0 dB (A2). Absence reading as agreement, so the probe frequencies are part of the trait |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Second audit pass, same day.** The first audit run was cut off before its
report was written, so every row was fetched a *third* time, independently
(`curl` + `pypdf`), and every quotation in §1–§3 checked against the bytes
that came back. **All nine rows answered HTTP 200, every licence call was
confirmed as written, no link is dead and no licence call moved.** Five things
did move — the Big Muff arm values, two capacitor roles, one bracketed
quotation, the corner arithmetic, and one false "not found" (S9). The record
is under the Appendix, "Audit record".

*(from §2)*

**Two "not found" claims the audit overturned.** The first pass recorded
GEOFEX as timed out and a permissively-published germanium model as
unreachable. Neither holds: `geofex.com` answered on the first try in the
audit run (plain `curl`, HTTP 200) and is now **S8**; and S1's own article
carries AC128 PSpice model cards under ElectroSmash's permission line, which
is the "published parameter set" route §8 Q1 asked for. §8 Q1 and Q2 are
written against the older, wrong premise and are Arthur's to update.

*(from §2)*

**A third "not found" claim the second audit pass overturned.** "A DAFx/AES/
JAES paper on *this* circuit: none" is false. One search reached **S9**, whose
two case studies are the Fuzz Face and the Rangemaster and which carries
measured AC128 device parameters — the thing §8 Q1 says stands between the
sourced asymmetry ratio and a sourced knee shape. The claim is withdrawn;
nothing in §3 changed on its account, since fixing a trait from S9 is Station
A's call, not an auditor's.

*(from §3)*

**Gating — the audit found the source the first pass could not.** Vision §6
floats "a bias point that moves with the signal" as an input to the node
design, and this seed originally recorded it as unsourced. S8 sources it
explicitly, and as a property of the topology rather than an envelope: *"When
driven with a large signal on the base, the collector voltage moves toward the
emitter. This lowers the bias voltage through the 100K biasing resistor, and
steals some of the input signal. Saturation is mushy."* The mechanism is the
100 kΩ feedback path, not a follower — so **§5's decision not to ask for an
envelope-following bias input stands, but for a better reason than "no
source"**: the behaviour falls out of modelling the loop. No reached source
quantifies it and this audit fixes no new traits, so it stays out of the Tier 2
table; whether it becomes a trait, and whether the loop is modelled or the bias
made drive-dependent, is for the implementation session. §8 Q2 is written
against the older premise and is Arthur's to update. Temperature drift is
deliberately not modelled — nothing here has a temperature.

*(from §3)*

Fraction of one stereo block's deadline (256 frames at 48 kHz, 5.33 ms):
**ESP32-P4 0.08, ESP32-S3 0.20**. `germanium` is one oversampled table
lookup between three first-order sections; `cascade` is two lookups plus a
three-way split, and sets the number. Lean patch: **yes** on the ESP32-S3 —
it drops the oversampling factor and nothing else. RAM: one table per
character, four biquad states.

*(from §3)*

**Latency: zero.** Nothing here looks ahead — a waveshaper is memoryless and
the filters are first-order recursions. `latency_samples` is 0, verified by
the click measurement at the class gate. The only candidate is the
waveshaper's oversampling filters, so §5 asks for **polyphase IIR half-band**
filters: frequency-dependent phase delay, not lookahead. A linear-phase
option, if Phase 1 adds one, defaults **off** and reports its true latency
when enabled. No other option here adds a sample.

*(from §4)*

Both characters are a memoryless curve between first-order sections — the
cheapest shape in the library; the whole question is the curve. The crossfade
is `audioroute.Splitter` + `audiomixer.Mixer` with the arm levels as block
inputs, the shape `Distortion`'s tone stack already uses; **verified this
run** — the Splitter carries four taps (`audioif_splitter.h:21`, and
`audioroute.MAX_TAPS` reads 4 from Python) and a MixerVoice's `level` is a
synthio block slot (`src/audiomixer/MixerVoice.c:49`).

*(from §4)*

- **There is no first-order section on that node.** All seven
  `synthio.FilterMode` modes are second-order RBJ biquads
  (`audioif_biquad.c:76-112`); a `Filter` cascades them but has no one-pole.
  Three *biquad* high-passes at S1's 14 / 7.9 / 31 Hz give −1.41 dB at 40 Hz
  and a −3 dB corner at 31.7 Hz (closed form; the node was measured against it
  at 0.003 dB, A4), against the −2.71 dB and 37.6 Hz G4 derives from the
  first-order cascade. (For the trait side: G4's bars pass on
  *both*, so the row does not catch the substitution — §8 Q8.)

*(from §4)*

- **The palette's first-order sections are in `audioecho.FeedbackDelay`**:
  `damping_hz` and `cut_hz` are `one_pole_coefficient()` sections
  (`audioif_feedback_delay.c:31-38`, run per sample at `:231-240`), and at
  `feedback=0`, `mix=2.0`, `delay_ms` = one frame the node *is* a one-pole —
  matching the closed form to 0.01 dB where the biquad at the same corner is
  9.4 dB out at 10 Hz. The price is a delay line and **one sample of latency**
  per section (click-measured), which Tier 3's "latency: zero" must absorb or
  §5's node must carry the sections itself.

*(from §4)*

- **The biquad route holds DC, worst exactly where this class lives.** Burst
  then silence with the source still rendering: an `audiofilters.Filter`
  section settles to a permanent **±36 LSB at 14 Hz** and ±7 at 31 Hz, against
  the one-pole route's **exact zero**. That is audioif#23 (its published
  100 Hz and 40 Hz/q=8 figures reproduce to the digit), it is Tier 1's held-DC
  failure, and into an *asymmetric* waveshaper a stuck 36 LSB is also an
  uncommanded bias — G1's subject. **This seed's Gate 0 answer:** the one-pole
  route, compose-first and measured clean.

*(from §4)*

- **Nothing on the palette gains above unity except the drive node.**
  MixerVoice level is clamped `0.0..1.0` (`src/audiomixer/Mixer.c:332`,
  measured) and `audiomath.Multiply` scales by `>> 15`, so a full-scale
  modulator is unity and no more (`audioif_multiply.c:38`); only
  `audiofilters.Distortion`'s `pre_gain`/`post_gain`
  (`audioif_distortion.c:53-54`) exceed it. Macro 0's 18…54 dB is therefore
  §5's node `pre_gain`; macro 1 is attenuation and a Mixer carries it.

*(from §4)*

Python computes the
tables once on CPython and ships them as `array('h')` beside the class —
never rebuilt on a board, whose single-precision math would build a different
table (vision §6). A macro moves **pre-gain and bias**, never the table (S7:
solve offline, interpolate at runtime). `cascade`'s curve is the silicon pair
in a feedback loop — the Newton solution of
`(Vin − Vo)/R = 2·IS·sinh(Vo/(N·Vt))` that `Overdrive` and `Distortion` use,
run twice. `germanium`'s is an asymmetric soft saturator whose two ceilings
are the sourced headroom, 1.6 V and 7.4 V at Q1's collector (G1), with the
*knee* held as a parameter until a device model is reached (§8 Q1): the
asymmetry ratio is sourced and fixed now, the knee is not, and this dossier
says so rather than inventing one. Mono: both circuits are mono, applied per
channel, no cross-coupling. Portability tier: **audioif**.

*(from §5)*

- *What the palette does instead:* four fixed curves in
  `audiofilters.Distortion` at the base rate, no way to load a curve — the
  four cases are `audioif_distortion.c:16-33`, the loop is `:63-66`, and the
  binding's whole argument list is `drive`, `pre_gain`, `post_gain`, `mode`,
  `soft_clip`, `mix` (`src/audiofilters/Distortion.c:327-339`), with no curve
  or table among them. **All three citations re-checked line by line this
  run.** There is no oversampling anywhere in the palette either:
  `audiospeed.SpeedChanger` is the only rate-changing node and it reads
  `phase >> SPEED_SHIFT` with no interpolation and no anti-alias filter
  (`src/audiospeed/SpeedChanger.c:139`, `:160`), so it cannot serve as a
  half-band stage.

*(from §5)*

- *Measurements showing it cannot reach them* (this run, CPython audioif;
  full tables in A2): CLIP is `pow(fabs(value), drive)` with the sign
  restored (`audioif_distortion.c:17-18`) — homogeneous, so its harmonic
  profile is *exactly* level-invariant, measured identical to the digit at
  −20 and −6 dBFS, which is G2's disconfirmation condition met by the node
  itself; CLIP and WAVESHAPE are odd-symmetric (h2 at the numerical floor —
  −152 dBc on the first run's transform, −332 dBc on A4's 48000-point one; the
  figure is the analysis's, the symmetry is the node's), so G1 is unreachable
  on either; OVERDRIVE *is* asymmetric but its
  `drive` is inert (`upstream-diff.md:1228`, measured) and its level law is
  wrong (h2 rises 0.84 dB per dB where a second-order nonlinearity gives
  1.00); and CLIP at the shipped `Fuzz` drive leaves **−19.6 dB** of
  non-harmonic energy at 1010 Hz against A4's −60 dB.

*(from §5)*

- *What is asked:* a table-driven waveshaper in an audioif-own module taking
  the curve as data and `pre_gain` and `bias` as control inputs, oversampled
  ×2 / ×4 / ×8 with polyphase IIR half-band filters so it adds no lookahead.
  The ported `audiofilters.Distortion` is never modified (vision §2.2).

*(from §5)*

- *Refutation record (Phase 0):* all four palette curves were driven and
  measured rather than argued about — two disqualified by symmetry, one by a
  dead argument and the wrong level law, all four by the alias floor.
  **Re-run independently by the palette verifier, 2026-09-06** (A4): every
  number above reproduces — CLIP's h3/h5 identical to the digit at −20 and
  −6 dBFS, OVERDRIVE identical across `drive` 0.2 / 0.5 / 0.9 at both levels,
  CLIP's alias floor −19.6 dB at 1010 Hz and −13.1 dB at 3700 Hz, and the
  1000 Hz probe reading −319 dB where 1010 Hz reads −19.6. (One number is the
  analysis's, not the node's: h2 sits at −332 dBc on a 48000-point float64
  DFT where the first run's shorter transform floored at −152. The claim
  "odd-symmetric, h2 at the numerical floor" is what is verified; the figure
  is not a property of the node.)
  **And the strongest *composition* was driven, which the first run did not
  do.** Vision §6 says compose the palette first, so the palette's one route
  to an asymmetric, level-dependent curve was built and measured: a DC offset
  summed in ahead of the symmetric CLIP curve, removed after. It does produce
  asymmetry (h2 up to −5.9 dBc) and it does break CLIP's scale-invariance —
  but it fails G2 as stated at **every** offset tried, because THD *falls* at
  the top of the range instead of rising: at offset 0.10 the six 6 dB steps
  from −40 dBFS run +6.04, +6.35, +7.88, +9.58, **−3.47, −0.86** dB. The
  circuit gets more asymmetric as it is driven; the composition gets less,
  because once the signal dominates the offset `pow(|x|, 0.05)` returns to a
  symmetric square. It reaches G1's bar and misses G2's, and it reaches
  neither A4 nor C1. **Not refuted.**

*(from §5)*

**No other ask, with two corrections to what "reachable" meant.** The tone
crossfade is reachable exactly as drawn (verified in §4). The high-passes are
reachable only in the two forms §4 now measures — second-order on
`audiofilters.Filter`, which holds DC at these corners, or first-order on
`audioecho.FeedbackDelay` at one sample of latency and one delay line each —
and the *first* of those does not build the class G4 describes. Macro 0's
18…54 dB of pre-gain is not reachable on any node but this ask's, since Mixer
level clamps at unity and Multiply cannot exceed it (§4), so **`pre_gain` is
load-bearing in the ask above and not a convenience**; add `post_gain` to it
for the same reason if the class ever needs make-up above unity. The
envelope-following bias is still not asked for, for the reason §3 gives.

*(from §7)*

- `drive.py:117` — the class is `audiofilters.Distortion` in **CLIP** mode,
  whose curve is scale-invariant and odd-symmetric: measured h2 −152 dBc and
  *identical* harmonics at −20 and −6 dBFS. It has neither the asymmetry (G1)
  nor the touch response (G2) the circuit's identity rests on. Its docstring
  names the result — "the waveform leaves as a square" — for a whisper and a
  chord alike.

*(from §7)*

- `drive.py:111` — `MACRO_LABELS = ()`: the Fuzz knob, the thing the pedal is
  named after, is a constructor argument no host can reach, and so are level
  and mix. `drive.py:113` — one patch, `"Default"`.

*(from §8)*

8. **G4 does not distinguish a first-order cascade from a biquad one.**
   Raised by the palette verifier, 2026-09-06: the row's two bars (within 1 dB
   over 100 Hz–10 kHz, no more than 3 dB down at 40 Hz, corner below 60 Hz)
   are met by both builds, though they differ by 1.3 dB at 40 Hz and 5.9 Hz in
   corner (§4, A4). No single in-band magnitude point separates them either:
   the two curves cross near 25 Hz and differ by only 1.67 dB at 20 Hz. What
   does separate them is the **slope below the corner** — 9.4 dB/octave from
   10 to 20 Hz on the first-order cascade against 18.6 on the biquad one, and
   13.8 against 30.3 from 5 to 10 Hz. Either G4 gains a slope clause of that
   shape, or it accepts that it does not test the section order. *Station A.*
