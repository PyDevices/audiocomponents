# Effects Dossier — `Overdrive` (Ibanez TS808 Tube Screamer)

**Class:** `lib/audioeffects/drive.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Drive, roadmap Phase 4
**Standout:** Ibanez TS808 (vision §4.2) — **confirmed.** The schematic with
values was reached and read (S1), our netlist of it runs under ngspice here
(S2, re-run today), and the DAFx literature models this exact circuit stage by
stage (S3–S5). Nothing argues for a swap.
**Grade:** circuit
**Portability tier:** **audioif** — `audioroute.Splitter` for the
dry-plus-clipped sum that is the circuit's defining structure, plus the
oversampled waveshaper asked for in §5.
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

One non-inverting op-amp stage carries the whole effect. Its inverting input
goes to bias through R4 4K7 + C3 0.047 µF; its feedback path is R6 51K plus the
500K Drive pot, with C4 51 pF and an anti-parallel pair of *like* diodes across
the whole network (S1). Gain is 1 + Zf/Zs, so the stage is a **shelf, not a
high-pass**: unity at DC, rising through the R4·C3 pole at 720 Hz to a plateau
of about 12 (Drive minimum) to 108 (Drive maximum), rolling off again through
the 51 pF near 6 kHz at full Drive (S2). Because the diodes sit *in the
feedback loop*, what they limit is the feedback voltage, not the output:
`Vo = V + Vi`, `V` solving the loop's ODE (S3 eq. 20–23). That one fact is the
pedal — the note always passes at unity and a clipped copy of its high-passed
self is added on top. Two like diodes make the clipping symmetric by topology,
so the harmonics are odd-only; asymmetry is a component mismatch and belongs to
a character, not the standout. The tone stage is a fixed R7 1K / C5 0.22 µF
low-pass node loaded by R9 10K (796 Hz analytic; S1's 723.4 Hz omits R9), then
an op-amp whose 20K Tone pot is strung between its two inputs with R8 220 Ω /
C6 0.22 µF on the wiper and 1K feedback (S1; S3 eq. 24): a follower with an
extra shunt at the bass end, a +14.9 dB shelf zeroed at 3.3 kHz at the treble
end (those two numbers are **S2's** arithmetic — 1 + R11/R8 and 1/(2π·R8·C6) —
not S1's or S3's; S1 states 3.2 kHz for the same corner). Then C7 1 µF / R12 1K into the 100K Level pot. **Overdrive** moves the
plateau gain and the 51 pF pole together, **Tone** slides between the shelf's
two ends, **Level** is a passive divider. There is no LFO.

## 2. Sources and license calls

Every source reached in this run, none from memory; the quotations each
supplied, and the license text as read, are in **Appendix E**. The three DAFx
PDFs were fetched by `WebFetch` — which cannot render PDF text — and their
bytes read with `pypdf`, so Appendix E quotes the papers' own words.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. ElectroSmash, "Tube Screamer Circuit Analysis" (MAS Effects mirror) | every value in §1; the 12–118 gain range … (App. S1) | **License unverified … (App. S1) | https://electrosmash.mas-effects.com/tube-screamer-analysis.html | yes (`www.electrosmash.com` does not resolve here) |
| S2. Our TS808 ngspice decks | every number in §3 and Appendix A | MIT (this repo, `LICENSE`) … (App. S2) | `audiocomponents/tools/spice/ts808/README.md` | yes (local; `run.sh` + `analyze.py` re-run by the audit 2026-09-06, output identical line for line to Appendix A) |
| S3. Yeh, Abel, Smith, DAFx-07, "Simplified … (App. S3) | the block model, eq. 20–23, tone eq. 24 … (App. S3) | "© 2007 D. T. Yeh. All rights reserved." … (App. S3) | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_distortion.pdf | yes (WebFetch + pypdf) |
| S4. Yeh, Abel, Smith, DAFx-07, "Simulation of the diode limiter …" | the static DC approximation implemented "using a … (App. S4) | as S3 (rights line at … (App. S4) | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_clipode.pdf | yes (WebFetch + pypdf) |
| S5. Yeh, Smith, DAFx-08 | §3.2.3: "The sampling rate was 8× oversampled the … (App. S5) | as S3 (rights line at … (App. S5) | https://ccrma.stanford.edu/~dtyeh/papers/yeh08_dafx_sim.pdf | yes (WebFetch + pypdf) |
| S6. Nexperia 1N4148 SPICE model | the ten diode parameters used in every Newton solve … (App. S6) | no license text in the file (re-read in full … (App. S6) | https://assets.nexperia.com/documents/spice-model/1N4148.prm | yes |
| S7. The palette, probed under `audiocomponents/.venv/bin/python` | every measured palette number in §4–§5 and Appendices … (App. S7) | MIT (this organization): SPDX line in the … (App. S7) | `audioif/src/shared/audioif_distortion.c` | yes (re-imported and Appendix F re-measured by the audit 2026-09-06) |
| S8. Nisshinbo (New Japan Radio) NJM4558 datasheet, Ver.2013-11-05 … (App. S8) | the three numbers in `models.lib`'s behavioural … (App. S8) | no terms on the aggregator page … (App. S8) | https://pdf.datasheet.support/50c18840/njr.com/NJM4558LD.html | yes (2026-09-07) |
| S9. Texas Instruments RC4558 product page | the GBW cross-check. **The page disagrees with itself … (App. S9) | facts | https://www.ti.com/product/RC4558 | yes (2026-09-07) |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

The rebuild works in normalized units under the proposed mapping **0 dBFS ≡
1.0 V peak at the input jack** (§8 Q1), so SPICE's 50 / 200 / 500 mV read
−26 / −14 / −6 dBFS.

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Pitch-dependent drive.** The pre-clip path is a shelf: at max Drive the small-signal gain is 23.3 / 38.8 / 37.7 dB at 100 Hz / 1 kHz / 5 kHz, pole fitted 720.6 Hz vs 720.5 analytic. A 100 Hz tone shows less THD than a 1 kHz tone at equal input. | S2; S1; S3 eq. 20 | high | 100 Hz gain within 10 dB of 1 kHz at max Drive; the fitted shelf pole outside 720 ± 110 Hz (±15 %, this dossier's band); or 100 Hz THD ≥ 1 kHz THD at −14 dBFS | pre-clip transfer (STFT out/in) … (App. T1) |
| T2 | **Symmetric, odd-only clipping.** h2 and h4 at or below −60 dB (SPICE −90); h3 runs −21.5 dB (Drive min, 50 mV) → −12.6 (Drive max, 50 mV), h5 −46.0 → −18.4. | S2; S1; S3 §4.2 | high | h2 **or h4** above −40 dB at any Drive — the 20 dB between the claim and the bar is this dossier's allowance for the rebuild's own numeric floor, not a second claim; h3 at Drive max outside −12.6 ± 2 dB; h5 at the same point outside −18.4 ± 3 dB | harmonic spectrum … (App. T2) |
| T3 | **Output = input plus a clipped feedback voltage.** Output peak = input peak + 0.37–0.48 V (0.415 / 0.633 / 0.978 V for 50 / 200 / 500 mV at Drive max), so THD at Drive max *falls* as input rises: 28.3 → 26.6 → 21.0 %. | S2; S3 eq. 23 | high | **output peak minus input peak outside 0.30–0.55 V** at any of −26 / −14 / −6 dBFS at Drive max (SPICE 0.365 / 0.433 / 0.478 V; the band this dossier's); or THD at Drive max rising from −14 to −6 dBFS | output peak vs input peak … (App. T3) |
| T4 | **A fixed low-pass and a movable shelf, not a moving corner.** 796 Hz first-order low-pass that never moves; the shelf spans −9.64 → +0.53 dB at 1 kHz and −19.95 → −3.51 at 5 kHz while 100 Hz moves 0.34 dB. Brightest is still 3.5 dB down at 5 kHz. | S2 (SPICE and an independent nodal solve … (App. T4) | high | Tone moving 100 Hz > 1 dB; brightest flat within 1 dB at 5 kHz; a −3 dB corner tracking the knob; or any of Appendix A's nine tone points (three positions × 100 Hz / 1 kHz / 5 kHz) missed by more than 2 dB | magnitude response from a swept … (App. T4) |
| T5 | **The control law.** Plateau gain 12 → about 108 (fitted 107.8 with the pair's 5.66 MΩ zero-bias shunt — 11.3 MΩ each, and it is the pair that parallels the 551 kΩ; 118.2 ideal); THD at 50 mV rises monotonically with the pot, 8.4 → 26.7 → 28.3 %. | S2; S1 | high for the span … (App. T5) | **small-signal plateau at Drive minimum outside 10–15** (20.0–23.5 dB) **or at Drive maximum outside 90–130** (39.1–42.3 dB) — 11.85 analytic at Drive min (11.76 with the pair's shunt; the deck sweeps AC only at pot max) and 107.8 SPICE-fitted at Drive max, the bands this dossier's; or THD at −26 dBFS not monotonic in Drive | pre-clip gain at Drive 0 / 0.5 / … (App. T5) |
| T6 | **It is never clean.** At Drive minimum a 50 mV input already shows 8.4 % THD, a 200 mV input 20.8 %. | S2 (pos 0) | high | THD outside 10–40 % at Drive minimum with a −14 dBFS input, or outside 4–20 % at −26 dBFS (SPICE 20.8 and 8.4 %; the bands this dossier's — the lower bound is the claim, the upper stops a build that is merely broken from passing) | THD of a 1 kHz sine at −14 dBFS … (App. T6) |
| T7 | **Alias floor.** Inharmonic energy in a 1010 Hz sine at Drive max, −6 dBFS, is ≥ 60 dB below the fundamental over 20 Hz–20 kHz. | mechanism from S3/S4/S5 … (App. T7) | medium (bar is a … (App. T7) | inharmonic energy above −60 dB at that point on **any** target, the P4's single-precision build included | sum of every FFT bin more than … (App. T7) |

Characters: none — the class has one standout. §6's `Symmetry` macro is a
knob, not a character: every row is stated at its centre, the matched pair.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

From S3 eq. 20–23 the clipping stage is not "a curve": it is
`Vo = Vi + f(In·R2)`, with `In·R2 = (R2/R1)·HP720(Vi)` the unclipped feedback
voltage and `f` its diode-limited version.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**A1 — the oversampled, table-driven waveshaper. Trait: T7.**
*The palette instead* runs one of four fixed curves at the base rate with no
anti-aliasing (`audioif_distortion.c:63-66` is a plain per-sample loop) and
offers no way to load a curve. *The measurement that shows it cannot reach the
trait:* on a 1010 Hz sine at −6 dBFS the `soft_clip` path measures −64.8 /
−50.9 / −43.5 / −22.3 dB of inharmonic energy at THD 14.8 / 28.2 / 34.5 /
45.0 % (Appendix D); the standout's own Drive-max THD is 28.3 % (T5), where the
palette sits **9.1 dB above T7's bar**, and `WAVESHAPE` and `OVERDRIVE` are
worse at equal THD. *What is asked:* a table-driven waveshaper in an
audioif-own module, oversampling ×2 / ×4 / ×8 (costed in Phase 1),
**minimum-phase IIR** interpolation and decimation so the node adds no latency,
an optional first-order pre-filter per S4, and the curve supplied as data
computed on CPython — which is also what lets a dossier show its arithmetic.
Drive is gain into one normalised curve, never a table rebuilt on a knob move
(vision §6). *Refutation record (Phase 0):* both saturating palette curves were
fitted and measured at matched THD and both fail T7 by 9–21 dB; the `CLIP` path
is disqualified separately (§8 Q3); the ported node cannot gain an option.
**Not refuted.** Shared with `Distortion`, `Fuzz` and `Saturation`.

*Palette-verifier refutation pass, 2026-09-06 — two compose-first routes tried
and measured, both refuted:*

- **Oversample by composing `audiospeed.SpeedChanger`.** The palette does carry …  *(argument in full: App. R)*
- **Build the curve from `audiomath.Multiply` instead of a table.** `Multiply` …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

`capabilities = ()`; the transport is not read (D10) — the standout has no
time-varying element, so a tempo has nothing here to move.

Macros — 7 of 16, MIDI 0..127:

| # | Label | Mode | Range and law | Generalizes |
|---|---|---|---|---|
| 0 | Drive | UNIPOLAR | plateau gain 12 → 108 (21.6 → 40.7 dB), log in gain; the 51 pF pole tracks it, ≈61 → 6 kHz | Overdrive (500K log) |
| 1 | Tone | UNIPOLAR | bass → treble end of the shelf: 1 kHz −9.6 → +0.5 dB, 5 kHz −20.0 → −3.5, 100 Hz within 0.4 | Tone (20K) |
| 2 | Level | UNIPOLAR | −∞ → 0 dB, audio taper | Level (100K) |
| 3 | Mix | UNIPOLAR | 0 → 1; 0 is the Tier 1 wire | none (contract convenience) |
| 4 | Body | UNIPOLAR | shelf pole 360 → 1440 Hz, an octave either side of R4·C3's 720; default 720 | none; what C3 fixes |
| 5 | Ceiling | UNIPOLAR | clipped feedback voltage 0.5 → 1.0 × stock (≈0.37–0.48 V-equivalent) | none; the three diode types S1 lists |
| 6 | Symmetry | BIPOLAR | one diode's threshold 0.5 → 2× the other's; centre = matched pair (stock, T2) | none; a character knob, centred |

Patches (names describe settings, never products):

| # | Name | Drive | Tone | Level | Mix | Body | Ceiling | Symmetry |
|---|---|---|---|---|---|---|---|---|
| 0 | Mid Drive Flat | 64 | 64 | 100 | 127 | 64 | 127 | 64 |
| 1 | Low Drive Bright | 16 | 110 | 100 | 127 | 64 | 127 | 64 |
| 2 | Full Drive Dark | 127 | 20 | 90 | 127 | 64 | 127 | 64 |
| 3 | Full Drive Bright | 127 | 118 | 84 | 127 | 64 | 127 | 64 |
| 4 | Thick Body Mid Drive | 72 | 60 | 100 | 127 | 12 | 127 | 64 |
| 5 | Tight Body High Drive | 100 | 80 | 96 | 127 | 118 | 127 | 64 |
| 6 | Asymmetric Mid Drive | 64 | 64 | 100 | 127 | 64 | 127 | 108 |
| 7 | Edge Boost | 0 | 96 | 127 | 127 | 64 | 127 | 64 |

Patch 7 is *Edge*, not *Clean*, because of T6.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/drive.py` (`grep -n`, 2026-09-06):

- `drive.py:64` — `MACRO_LABELS = ()`: no knob a host can turn.
- `drive.py:72-75` — Drive goes into `pre_gain` with the level put back by …  *(argument in full: App. R)*
- `drive.py:73-74` — the OVERDRIVE curve is asymmetric. Measured on the shipped …  *(argument in full: App. R)*
- `drive.py:75` — a hidden fixed `−3.0` dB output trim; measured −3.08 dB of
  fundamental gain at −60 dBFS, against the level-honest invariant.
- `drive.py:77-81` — "tone" is a second-order Q = 0.707 low-pass at 4.5 kHz …  *(argument in full: App. R)*
- `drive.py:68` — no tone law, no level, no body; `tone_hz` is a raw frequency
  with no relation to the pedal.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **The 0 dBFS reference** — 1.0 V peak at the input jack. A documented
   constant; implementation session at Station A, shared with `Distortion`.
2. **Oversampling factor and pre-filter** — which of ×2 / ×4 / ×8 reaches T7's
   −60 dB on the S3 within Tier 3, and whether S4's pre-filter buys a factor.
   Phase 1's cost/alias table.
3. **The `CLIP` clamp wraps to the negative rail** — a ported-node defect, not
   a defect of the current class, which is why it is here and not in §7.
   Measurement and line numbers in Appendix F; `upstream-emissary` decides on a
   report and the rebuild never uses that path.
4. **Pot tapers → knob laws.** S1's BOM says the Tone pot is "20K/22K Lin"
   while its prose calls it a G-taper with "more control in the middle" — the
   page disagrees with itself, and SPICE positions are resistance fractions
   either way. Log-in-gain for Drive and a mid-weighted Tone are proposed; the
   curves are the implementation session's, under the constraint that §6's
   patches stay musically where they are named.
5. **Static curve vs the ODE.** At Drive max / 500 mV the feedback voltage
   shows 0.55 V of memory spread, yet the static fit lands inside every trait
   tolerance — S3's and S4's own finding. If Station C misses h5 by more than
   2 dB the candidate is S4's semi-implicit trapezoidal step: a different,
   costlier node. Implementation session, after measurement.
6. **Where the analytic probes live.** The fits in Appendices B–D ran from
   scratch scripts this session, reproducible from the formulas and values
   stated here. Whether they join `tools/spice/ts808/analyze.py` is Arthur's.
7. **The ElectroSmash license line** was read on the mirror's Rat page, not on
   ElectroSmash's own rights page, unreachable here. The Phase 0 audit
   re-fetches.


## Appendix


### A. The SPICE run, re-run 2026-09-06

`tools/spice/ts808/run.sh` then `analyze.py`, output identical to that
README's recorded table. Drive stage, small-signal AC at Drive max: peak gain
39.7 dB at 1905 Hz; 23.3 / 38.8 / 37.7 dB at 100 Hz / 1 kHz / 5 kHz; fitted
high-pass corner 720.6 Hz against 720.5 Hz analytic (+0.0 %); fitted low-pass
6046 Hz against 5664 Hz analytic, 6215 Hz with the diodes' 11.3 MΩ shunt in
parallel; fitted plateau gain 107.8 against 118.2 ideal and 107.8 with the
diodes (−0.0 %); fit residual 0.001 dB rms over 150 points. An ideal-op-amp
fit of the same data reads 741.9 Hz (+3.0 %) — the 4558's finite GBW read as
a corner shift — and the naive "−3 dB below the peak" reading, 583.8 Hz, is
not the corner at all.

Transients (1 kHz, window 20–30 ms, THD over harmonics 2–20):

| pos | in pk | out pk | h1 gain | THD | h2 | h3 | h4 | h5 |
|---|---|---|---|---|---|---|---|---|
| 0 | 50 mV | 0.356 V | 17.7 dB | 8.4 % | −94.6 | −21.5 | −109.0 | −46.0 |
| 0.5 | 50 mV | 0.412 V | 19.7 dB | 26.7 % | −90.4 | −12.9 | −92.6 | −19.1 |
| 1 | 50 mV | 0.415 V | 19.9 dB | 28.3 % | −90.3 | −12.6 | −92.1 | −18.4 |
| 0 | 200 mV | 0.619 V | 10.8 dB | 20.8 % | −90.8 | −14.8 | −94.1 | −21.6 |
| 0.5 | 200 mV | 0.632 V | 11.1 dB | 26.2 % | −90.4 | −13.6 | −92.3 | −18.9 |
| 1 | 200 mV | 0.633 V | 11.1 dB | 26.6 % | −90.3 | −13.5 | −92.2 | −18.8 |
| 0 | 500 mV | 0.972 V | 6.4 dB | 19.2 % | −90.9 | −16.2 | −94.1 | −21.7 |
| 0.5 | 500 mV | 0.978 V | 6.5 dB | 20.8 % | −90.8 | −15.8 | −93.5 | −20.9 |
| 1 | 500 mV | 0.978 V | 6.5 dB | 21.0 % | −90.8 | −15.8 | −93.5 | −20.9 |

Tone stage at the op-amp's pin 7 (Level at max), dB: tone 0 → −1.12 / −9.64 /
−19.95; tone 0.5 → −0.91 / −4.50 / −16.13; tone 1 → −0.78 / +0.53 / −3.51 at
100 Hz / 1 kHz / 5 kHz. An independent ideal-op-amp nodal solve agrees to
0.03 dB. Analytic low-pass node 1/(2π(R7‖R9)C5) = 796 Hz (S1's 723.4 Hz omits
R9); treble shelf zero 1/(2π R8 C6) = 3288 Hz, maximum boost 1 + R11/R8 =
14.9 dB.

### B. The palette's curves against the SPICE feedback voltage

The nine transients re-analysed as `V = v(out) − v(inp)` against the drive
voltage `In·R2` (v(inp) through `s·Cz/(1 + s·R1·Cz)` scaled by R2/R1), with
each palette curve fitted for amplitude and scale by least squares, then
`Vi + f` re-spectrumed. Fit residual `rms` in volts.

| pos | in | SPICE THD/h3/h5 | dry + `soft_clip` | rms | dry + `WAVESHAPE` | rms |
|---|---|---|---|---|---|---|
| 0 | 50 mV | 8.41 % / −21.5 / −46.0 | 8.13 % / −22.0 / −35.2 | 0.006 | 7.94 % / −22.3 / −34.3 | 0.007 |
| 0 | 200 mV | 20.76 % / −14.8 / −21.6 | 21.21 % / −14.4 / −22.0 | 0.012 | 20.15 % / −15.1 / −22.0 | 0.013 |
| 0 | 500 mV | 19.15 % / −16.2 / −21.7 | 20.27 % / −15.3 / −21.2 | 0.021 | 19.14 % / −16.0 / −21.8 | 0.016 |
| 0.5 | 50 mV | 26.68 % / −12.9 / −19.1 | 25.66 % / −12.7 / −20.4 | 0.035 | 24.30 % / −13.4 / −20.4 | 0.036 |
| 0.5 | 200 mV | 26.21 % / −13.6 / −18.9 | 26.82 % / −12.9 / −18.9 | 0.041 | 24.99 % / −13.6 / −19.6 | 0.040 |
| 0.5 | 500 mV | 20.85 % / −15.8 / −20.9 | 22.04 % / −14.9 / −20.3 | 0.042 | 22.04 % / −15.2 / −20.4 | 0.043 |
| 1 | 50 mV | 28.31 % / −12.6 / −18.4 | 26.23 % / −12.6 / −20.1 | 0.045 | 24.79 % / −13.3 / −20.2 | 0.047 |
| 1 | 200 mV | 26.58 % / −13.5 / −18.8 | 26.77 % / −12.9 / −18.9 | 0.046 | 27.96 % / −13.0 / −18.4 | 0.050 |
| 1 | 500 mV | 20.96 % / −15.8 / −20.9 | 22.09 % / −14.9 / −20.2 | 0.045 | 23.42 % / −14.9 / −19.8 | 0.054 |

### C. First-order sections from a low-Q biquad

`synthio.Biquad` takes mode / frequency / Q / A only, so a first-order section
is built as two real poles with the second parked at 40 kHz: for a 1 kHz pole,
f0 = √(1000·40000) = 6324.6 Hz, Q = 0.1543. Measured through
`audiofilters.Filter` on the audioif CPython build, against a true first-order
1 kHz pole (dB):

| f | measured | first-order | diff |
|---|---|---|---|
| 100 | −0.04 | −0.04 | 0.00 |
| 250 | −0.23 | −0.26 | +0.03 |
| 500 | −0.87 | −0.97 | +0.10 |
| 1000 | −2.77 | −3.01 | +0.24 |
| 2000 | −6.63 | −6.99 | +0.36 |
| 4000 | −12.05 | −12.30 | +0.26 |
| 8000 | −18.64 | −18.13 | −0.51 |
| 12000 | −23.71 | −21.61 | −2.10 |

Good to 0.51 dB through 8 kHz; the parked pole shows above 10 kHz, which is
why T4's stated points stop at 5 kHz.

### D. The alias floor the palette actually reaches

1010 Hz sine at −6 dBFS, `soft_clip` path, no post-gain compensation, one
4800-sample window (101 exact periods), inharmonic energy summed over every
non-harmonic bin:

| pre-gain | THD | inharmonic |
|---|---|---|
| +12 dB | 14.84 % | −64.8 dB |
| +16 dB | 21.17 % | −58.1 dB |
| +18 dB | 24.68 % | −54.5 dB |
| +20 dB | 28.20 % | −50.9 dB |
| +24 dB | 34.51 % | −43.5 dB |
| +28 dB | 39.20 % | −36.5 dB |
| +40 dB | 44.97 % | −22.3 dB |

The standout's Drive-max THD is 28.3 %; the palette at that THD is 9.1 dB
above T7's bar. Every row above was re-measured by the palette verifier on
2026-09-06 and came back identical. The two other saturating paths, re-measured
the same way and **corrected** — the draft named the wrong drive position:
`WAVESHAPE` reads −31.0 dB at 36.2 % THD at **drive 0.95** (at drive 0.90 it is
−38.1 dB at 30.7 %), and `OVERDRIVE` reads −31.8 dB at 42.1 % at +28 dB of
pre-gain (−28.9 dB at 43.3 % at +30 dB). Both are far above the bar wherever
they are hot enough to be a drive pedal.

### E. What each source said, verbatim

**S1, ElectroSmash "Tube Screamer Circuit Analysis"** (MAS Effects mirror,
fetched 2026-09-06). Values: R6 51K, R4 4K7, R5 10K, P1 500K, C4 51 pF,
C3 0.047 µF; R7 1K, R8 220 Ω, R14 10K, C5/C6 0.22 µF, C9 10 µF. Diodes:
"2 Diode MA150/1N4148/1N914 (D1, D2)". Gain: "the top gain will be around 12
and the additional the range from 12 to 118". Corner: "Harmonics above 720Hz
get the full gain of the distortion stage". C4: "The small 51pF C4 capacitor
across the diodes works as a low pass filter, softening the corners"; "The
RDISTORTION potentiometer will shift the fc frequency". Tone: low-pass
"723.4 Hz", treble boost at "3.2KHz". BOM pots: "1 Potentiometer 500K/470K Log
(P1) / 1 Potentiometer 20K/22K Lin (P2) / 1 Potentiometer 100K Lin (P3)" —
while the body text reads "The 20K Tone Control G Taper Potentiometer … gives
to the user more control in the middle". **The BOM contradicts the prose on the
tone network too** (added by the licence audit 2026-09-06 — the earlier audit
block claimed this was recorded here and it was not): the BOM reads "4 Resistors
1K (R1, R8, R11, R12) / 1 Resistor 220 (R10)", while the prose reads "220 ohm
R8 resistor and a 0.22uF C6 capacitor, from ground to the wiper of a 20K
potentiometer". §1, S2's decks and S3's eq. 24 all use the prose/drawing
assignment (220 Ω on the wiper, 1K in the feedback), which is also the only one
that yields the page's own 3.2 kHz corner and the 14.9 dB boost —
`tools/spice/ts808/README.md` documents the same conflict and the same
resolution. Rights: the mirror's footer reads "An unofficial, non-commercial
backup of ElectroSmash.com, preserved by MAS Effects from the Internet Archive.
All content and images belong to their original authors/owners."; **this page
carries no rights line of its own.** ElectroSmash's own line, read this run in
the body of the same mirror's Rat article and on no other page fetched, is
"Some Rights Reserved, you are free to copy, share, remix and use all material.
Trademarks, brand names and logos are the property of their respective owners."

**S3, Yeh/Abel/Smith DAFx-07 (distortion & overdrive).** §4: the Tube Screamer
"is characterized by high pass filters, followed by the summation of a
high-pass filtered and clipped signal summed with the input signal. This is
followed by low-pass tone filtering and a high pass in the output buffer." §4.1: "fc1 =
15.9 Hz, fc2 = 15.6 Hz". Eq. 20 `In = Vi·s/(R1(s+ωz))`, "R1 = 4.7kΩ, Cz =
0.047µF"; eq. 22 `dV/dt = In/Cc − V/(R2·Cc) − (2Is/Cc)·sinh(V/Vt)`, "CC = 51pF,
R2 = 51k + D500k"; eq. 23 `Vo = V + Vi`. Fig. 14 labels the op-amp "JRC4580".
Eq. 24 with "Rf = 1k, Rr = (1−T)20k, Rl = T20k, Rz = 220, Cz = 0.22µF, Ri =
10k, Rs = 1k, Cs = 0.22µF". §1: "typical digital implementations of distortion
upsample by a factor of eight or ten, process the nonlinearities, and
downsample back to typical audio rates". §3.4 — the sentence Appendix E's S4 block used
to carry: "the DC transfer curve is computed by setting dVo/dt = 0 in (18), and
tabulating the function Vo = f(Vi) by Newton iteration." §5: "The measured
spectra exhibit a strong even-order nonlinearity that is not modeled in the
digital implementation." Rights, read this run at
<https://ccrma.stanford.edu/~dtyeh/papers/pubs.html>: "© 2007 D. T. Yeh. All
rights reserved." — the PDF itself carries no rights line.

**S4, Yeh/Abel/Smith DAFx-07 (diode limiter ODE).** Abstract: "The diode
clipper circuit with an embedded low-pass filter lies at the heart of both
diode clipping 'Distortion' and 'Overdrive' or 'Tube Screamer' effects
pedals"; "the filter/static nonlinearity approximation is often perceptually
adequate". §2.1, **corrected by the audit 2026-09-06** — this paper does not contain the
Newton-iteration sentence previously quoted here (that is S3 §3.4, above); what
it says is: "The nonlinearity used is the DC approximation of the actual
nonlinearity (Fig. 2), which can be derived from (2) by setting C dV/dt = 0.
This is implemented using a lookup table as in [1] and is also known as
waveshaping distortion. It is found that using a first-order low-pass filter
before the nonlinearity with a cutoff frequency determined by the R and C of
the diode limiter reduces aliasing while maintaining accurate output." §3.1: "The approximation shows noticeably larger
error than the numerical solvers, but it is typically less than -40 dB."

**S5, Yeh/Smith DAFx-08.** §3.2.3 (the licence audit corrected the section
number from §3.2 on 2026-09-06): "The sampling rate was 8× oversampled the
audio sampling rate of 48000 Hz to reduce signal aliasing in the output."

**S6, Nexperia 1N4148 `.prm`.** IS 4.352E-9, N 1.906, BV 110, IBV 0.0001,
RS 0.6458, CJO 7.048E-13, VJ 0.869, M 0.03, FC 0.5, TT 3.48E-9, inside
`.SUBCKT 1N4148 1 2` with a 5.827E+9 Ω reverse-mode shunt; the file's own
header reads "*NXP Semiconductors". No license or copyright text is present in
it — re-read in full by the licence audit 2026-09-06 (plain `curl` returns
HTTP 403 with an Akamai "Access Denied" page; `WebFetch` reaches the file),
which also re-read Nexperia's Terms of Use
(<https://www.nexperia.com/about/terms-and-policies/terms-of-use>): "Copyright
and all other proprietary rights in the Content … rests with NEXPERIA or its
licensors"; "Except as otherwise provided, the Content published on this Web
Site may be reproduced or distributed in unmodified form for personal
non-commercial use only"; "Software made available for downloading from or
through this Web Site is licensed subject to the terms of the applicable
license agreement"; content is "PROVIDED 'AS IS'". **Not permissive**; treated
as a document, and the ten parameter values live in our own `.model` line.

### F. The `CLIP` clamp's int16 wrap (§8 Q3)

`audioif_distortion.c:43-46` clamps the negative side at −32767 but the
positive side at **32768**, and the value is stored as `int16_t` — in the
shared kernel at `audioif_distortion.c:64` and again in the binding at
`audiofilters/Distortion.c:272` — so every sample the positive clamp catches
lands at −32768, a full-scale negative spike. Measured this run on a 1 kHz sine
at −20 dBFS through `audiofilters.Distortion` in `CLIP` mode with `drive = 0`
and no post-gain compensation: **10 of 480** output samples at −32768 with
+20 dB of pre-gain, **230 of 480** at +40 dB; `WAVESHAPE` at drive 0.9 wraps
identically at +40 dB. The path is only reachable when the post-gain-scaled
curve output exceeds 1.0, which the shipped `Overdrive` (`drive.py:72-75`),
`Distortion` (`:97-99`) and `Fuzz` (`:116-118`) settings never do — checked at
−3, −6, −12 and −20 dBFS, zero wrapped samples in each. So this is a defect of
a CircuitPython-ported node, not of the current classes, and it is recorded as
an open question rather than as a §7 defect.

### G. The Phase 0 licence-and-citation audit (2026-09-06)

Every source in §2 was re-reached **by the audit itself** in this run; nothing
below rests on an earlier run's claim, and nothing is cited that this run did
not fetch.

**What was re-reached, and how.** The ElectroSmash mirror page by `curl`
(HTTP 200, 38,555 bytes) and its text extracted and grepped locally, so the
absence of a rights line on it is a checked fact and not an impression; the
mirror's *Rat* page (HTTP 200, 21,360 bytes), which is the one page of the
three that carries ElectroSmash's own "Some Rights Reserved" line, in the
article body. All three DAFx PDFs downloaded from `ccrma.stanford.edu`
(HTTP 200; 347,276 / 442,111 / 198,922 bytes), re-extracted with `pypdf` under
`audiocomponents/.venv`, and **every quotation in Appendix E located in the
extracted text** — including eq. 20's "R1 = 4.7k, Cz = 0.047 F", eq. 22's
"CC = 51pF, R2 = 51k + D500k", eq. 24's "Rf = 1k … Rz = 220 …", Fig. 14's
"JRC4580" label, §5's measured-spectra sentence, the clipode paper's lookup
table and pre-filter sentences and its "typically less than -40 dB", and
DAFx-08's 8× sentence. The author's index page `papers/pubs.html` (HTTP 200):
"© 2007 D. T. Yeh. All rights reserved."; a grep of all three extracted PDFs
finds no copyright or rights text in the papers themselves. The Nexperia
`.prm` read in full through `WebFetch` (plain `curl` gets HTTP 403) — ten
parameters as Appendix E lists them, no licence text — and Nexperia's Terms of
Use. `electrosmash.com` re-tried and confirmed non-resolving. The TS808 decks
**re-run here** (`run.sh` under `/usr/bin/ngspice`, then `analyze.py`), output
identical line for line to Appendix A. The palette re-imported under
`audiocomponents/.venv` and **Appendix F re-measured independently**: 10 of 480
samples at −32768 at +20 dB pre-gain, 230 of 480 at +40 dB, `WAVESHAPE` at
drive 0.9 the same at +40 dB, and zero wrapped samples at each of the three
shipped class settings at −3, −6, −12 and −20 dBFS. Every `grep -n` line number
cited in §2–§5, §7 and Appendix F was re-checked against the tree and holds
(`audioif_distortion.c:17/:24/:31-32/:37/:43-46/:63-66`,
`audioif_multiply.h:24`, `audioif_splitter.h:21`,
`audiofilters/Distortion.c:244-249/:272`, `upstream-diff.md:661/:818/:1228`).

**What was corrected in this run.**

1. **S1's licence call is now "license unverified — treated as copyleft."**
   The Tube Screamer page carries no rights line; the "Some Rights Reserved"
   line is in the body of a *different* article on the same mirror, and the
   origin does not resolve, so no page licensing this one has been reached. A
   mirror is a repackager, and its copy of a line is an assertion about a page
   it does not own (`agent-knowledge/instrument-sources.md`).
2. **Appendix E's S1 block now records the BOM-versus-prose conflict on the
   tone network** (BOM "1K (R1, R8, R11, R12) / 220 (R10)" against the prose's
   "220 ohm R8 … on the wiper"), with the resolution §1 and the decks use. An
   earlier audit block in this file claimed it had recorded exactly this; the
   file did not contain it. That claim is the one item this run found an
   earlier audit asserting about itself that was not true of the text.
3. **S5's section number** corrected from §3.2 to §3.2.3, and the row now
   carries the sentence rather than a fragment.
4. **S6's row and Appendix E block** now name how the file is reachable (403
   to `curl`, readable through `WebFetch`), quote the personal-non-commercial
   sentence from the Terms of Use as well as the copyright sentence, and
   record the file's own "*NXP Semiconductors" header.
5. **S2, S3, S4 and S7's rows** now state what was verified rather than
   asserting it: the repository `LICENSE` text for the MIT calls, the grep for
   rights text inside the PDFs, and the fact that the decks and the palette
   probes were actually re-run by the audit.
6. §2's "not reached" paragraph now records the DNS result itself, and its
   claim about coverage is restated as "reached by this run", not "reached by
   an earlier audit".

**What this audit did not re-run.** Appendix B's curve fits against the SPICE
feedback voltage and Appendix C's biquad measurement are this dossier's own
arithmetic on sources that were re-reached; they were read for consistency and
not recomputed, and Appendix D's alias-floor table was not re-measured (only
Appendix F's wrap count was). Nothing in B, C or D is a sourced claim, and
none of them carries a Tier 2 trait: T1–T6 rest on S2, which **was** re-run,
and T7's bar is stated as the dossier's own.

**What could not be reached.** ElectroSmash's origin rights page, at both
`www.electrosmash.com/rights` and `electrosmash.com/rights` — neither host
resolves from this machine (`getent hosts`: no answer; `curl`: `http=000`).
GEOFEX and `web.archive.org` were not attempted, per
`agent-knowledge/instrument-sources.md`, and are cited nowhere.

**Not touched:** §§4–8, which this audit may not edit. One item there needs a
later hand: §4 cites `audioif/src/synthio/Biquad.c:37-61` for "Biquad takes
mode / frequency / Q / A only" — the claim is true, but the argument list
proper is `biquad_properties[]` at `Biquad.c:148-153`; :37-61 is the slot
assignment. A citation-precision fix for whoever owns §4.

### H. The trait-critic pass (2026-09-06)

Independent pass over the Tier 2 table alone: is every row falsifiable as
stated, does each name a source, a confidence, a disconfirmation condition and
a measurement someone could actually run? Sources were **not** re-fetched here
(the licence audit in Appendix G did that); what was re-run is the local
evidence — `tools/spice/ts808/run.sh` then `analyze.py`, output identical line
for line to Appendix A — and one analytic check of its own, below. **Rows
after the pass: 7 (T1–T7). None removed, none added, none marked unmeasured.**

**The defect the pass was looking for, and found: three rows named no
measurement level.** T1, T4 and T5 asked for a "pre-clip transfer" or a
"plateau gain" without saying how loud the sweep is. The anti-parallel pair is
across the *whole* feedback network, so it is a shunt whose value depends on
the very signal being measured: the pair's small-signal resistance is
`N·Vt / (2·IS·cosh(V/(N·Vt)))`, 5.66 MΩ at V = 0 with S6's parameters, and it
parallels the 551 kΩ. Solved at Drive maximum, with the plateau
`1 + (551 kΩ ‖ Rpair)/4.7 kΩ`:

| Sweep level | feedback voltage V | plateau read | error vs the 107.8 the row claims |
|---|---|---|---|
| −60 dBFS | 107 mV | 82.9 | **−2.29 dB** |
| −66 dBFS | 53 mV | 102.0 | −0.48 dB |
| −72 dBFS | 27 mV | 106.4 | −0.12 dB |
| −78 dBFS | 13 mV | 107.5 | −0.03 dB |

At V = 0 the same expression gives 107.84, which is the 107.8 the SPICE fit
returns — so the arithmetic agrees with Appendix A where the two meet. A kit
that swept at a plausible-sounding −60 dBFS would have read the plateau 2.3 dB
low and failed a rebuild that was exactly right, which is the shape
`agent-knowledge/workspace-craft.md` calls absence-reading-as-agreement, one
step round: a wrong answer that looks like a wrong build. T1 now carries a
**self-validating** level rule — halve the level and the reading must not move
more than 0.3 dB — which needs no table to apply and cannot go stale if the
diode model changes. T4 side-steps it instead by measuring the tone stage at
Drive *minimum*, where the plateau is 11.85 and −60 dBFS puts only 11 mV
across the pair (0.02 dB).

**The five rewrites.**

1. **T1** — added the level rule above, and a band on the shelf pole (720 ±
   110 Hz, this dossier's), which the row asserted to 0.1 Hz and then failed
   nothing on.
2. **T2** — the row claimed "≤ −60 dB" and disconfirmed at "above −40 dB",
   two different bars with nothing saying which one fails a build. The claim
   stands at −60 dB and the 20 dB is now named as the allowance it is. h4 was
   claimed and never tested; it is in the disconfirmation now. h5 was quoted
   (−46.0 → −18.4) with no band; it has one. Added: Symmetry at centre, so the
   row cannot be run against §6's asymmetry knob and reported as a failure.
3. **T3** — "output peak growing > +2 dB per +6 dB of input" tests something
   adjacent to the claim; the claim is that the *difference* is a diode drop.
   Disconfirmation restated as the difference itself, 0.30–0.55 V against
   SPICE's 0.365 / 0.433 / 0.478.
4. **T5** — "plateau gain outside 10–130 at either end" is passed by a build
   whose Drive-minimum plateau is 130, which is the trait inverted. Split into
   a band per end (10–15 and 90–130 against SPICE's 11.85 and 107.8).
5. **T6** — one-sided ("below 2 %"), so a build with 60 % THD at Drive
   minimum passed a trait about how *little* it distorts there. Two-sided now,
   and a −26 dBFS point added so the row tests the pair 8.4 / 20.8 % rather
   than one number.

**One number corrected.** T5 read "fitted 107.8 with the diodes' 11.3 MΩ
shunt". 11.3 MΩ is *one* diode (`N·Vt/IS`); what parallels the 551 kΩ is the
pair, 5.66 MΩ, and 551 ‖ 5660 = 502 kΩ gives 107.8. With 11.3 MΩ the same
arithmetic gives 112.7, which is not what Appendix A reports. The SPICE
README states both figures correctly; the seed row picked up the per-diode
one. T4's and T7's edits are scope, not arithmetic: T4 gained a tolerance on
its nine quoted points, T7 gained a definition of "inharmonic" (bins more than
two from a harmonic or DC, no window) and lost "on the P4 build", which read
as though a desktop failure would not count.

**Not touched:** §§1–2 and 4–8, and the Tier 1 and Tier 3 blocks, which were
checked and not edited — Tier 1 is byte-identical to the template's standard
block, and Tier 3 carries both boards (P4 0.08, S3 0.20), the zero-latency
statement and "options that add latency: none".

### I. The netlist transcription check (2026-09-07)

The check the SPICE proof had not had: **every component value in the S2 decks
read back to S1**, element by element, rather than trusting that the netlists
say what the schematic says. S1 was re-reached this run by `curl` (HTTP 200,
38,555 bytes, text extracted and grepped locally) and **its two stage drawings
were fetched as images and read** —
`.../images/tube-screamer-analysis/tube-screamer-clipping-amplifier.png`
(HTTP 200, 22,730 bytes) and `.../tube-screamer-tone-volume.png` (HTTP 200,
22,135 bytes). S6's `.prm` was re-read in full through `WebFetch` (plain `curl`
now returns a bot-challenge page, not the 403 the earlier audit recorded — the
file is still unreachable to `curl`, for a different reason). S8 and S9 were
read for the op-amp model's three numbers. `run.sh` then `analyze.py` were
re-run after deleting `out/` (a stale-artifact habit —
`agent-knowledge/workspace-craft.md`), and the output is identical line for
line to Appendix A.

**Result: all 21 component values S1 supplies are confirmed — most of them
twice, in the drawing and in the BOM — and `models.lib`'s fourteen model
numbers check against S6, S8 and S9. No mismatch, nothing unverifiable, no
trait row marked "netlist unverified."**

#### `ts808_drive.cir`

| Deck | Value | What S1 gives | |
|---|---|---|---|
| `:37` `Vcc` | 9 V | §1.2 "The 9V supply is common to all circuit components" | ✓ |
| `:38` `Vb` | 4.5 V | §1.2 "the resistors junction (+4.5V)"; drawing "4V5" | ✓ |
| `:41` `C2` | 1 µF | drawing "C2 1uF/50V NP"; BOM "2 Capacitors 1uF NP/50V (C2, C7)"; §1.4 "1uF non-polarized electrolytic coupling cap C2" | ✓ ×3 |
| `:42` `R5` | 10 kΩ | drawing "R5 10K"; BOM's 10K group; §1.4 "biased to the 4V5 voltage source with a single moderate value R5 resistor (10K)" | ✓ ×3 |
| `:44` `R4` | 4.7 kΩ | drawing "R4 4K7"; BOM "1 Resistor 4K7 (R4)" | ✓ ×2 |
| `:45` `C3` | 47 nF | drawing "C3 0.047"; BOM "1 Capacitor 0.047uF (C3)" | ✓ ×2 |
| `:47` `R6` | 51 kΩ | drawing "R6 51K"; BOM "1 Resistor 51K (R6)"; §1.4.1 "the series combination of a 51K resistor and the 500K Distortion control" | ✓ ×3 |
| `:48` `Rp1` | 0–500 kΩ | drawing "P1 Distortion 500K Log"; BOM "1 Potentiometer 500K/470K Log (P1)"; §1.4.1 "from 500K to 0Ω" | ✓ ×3 |
| `:49`–`:50` `XD1`/`XD2` | anti-parallel pair across R6+P1 and C4 | drawing: D1 and D2, both "MA150", anti-parallel between the output and the (−) input; BOM "2 Diode MA150/1N4148/1N914 (D1, D2)"; §1.4.1 "Z2 … the parallel combination of the clipping diodes, a 51pF capacitor and the series combination of a 51K resistor and the 500K Distortion control" | ✓ topology and part — the deck models the 1N4148 of the three the BOM names, as its header says |
| `:51` `C4` | 51 pF | drawing "C4 51p"; BOM "1 Capacitor 51pF (C4)"; §1.4.4 "The small 51pF C4 capacitor across the diodes" | ✓ ×3 |
| `:53` `XU1` | JRC4558, behavioural | drawing "JNR4558 U1"; BOM "1 IC JRC4558/RC4559/RC4558" | ✓ part; its three numbers are S8/S9's, below |
| — `RA` omitted | — | the drawing shows RA between C2 and the (+) input with **no value**, but the BOM's closing note reads "R A 0Ω" | ✓ and **better than the README claimed**: RA is a wire by S1's own note, so omitting it is exact, not a simplification |

#### `ts808_tone.cir`

| Deck | Value | What S1 gives | |
|---|---|---|---|
| `:33`/`:34` rails | 9 V / 4.5 V | as above | ✓ |
| `:37` `R7` | 1 kΩ | drawing "R7 1K"; §1.5.1 "The C5 cap 0.22uF and the 1K resistor R7"; §1.5.2 "the 1K/0.22uF R7C5 network" | ✓ ×2 — and **R7 has no BOM line at all**: the BOM's resistor list runs R1, R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, RB, RC, R32, R33 and skips R7 |
| `:38` `C5` | 220 nF | drawing "C5 0.22 35V"; BOM "2 Capacitors 0.22uF (C5, C6)"; §1.5.1 | ✓ ×3 |
| `:39` `R9` | 10 kΩ | drawing "R9 10K" to 4V5; BOM's 10K group names R9 | ✓ ×2 |
| `:41`–`:42` `Rp2a`/`Rp2b` | 20 kΩ total | drawing "P2 Tone 20K" strung between pins 5 and 6; BOM "1 Potentiometer 20K/22K Lin (P2)"; §1.5.2 "a 20K potentiometer strung from the (-) to the (+) input of the second opamp section" | ✓ ×3 (taper: prose "G Taper", BOM "Lin" — the deck simulates resistance fraction, not rotation) |
| `:43` `R8` | 220 Ω on the wiper | drawing "R8 220" from the wiper; §1.5.2 "220 ohm R8 resistor and a 0.22uF C6 capacitor, from ground to the wiper" — **the BOM says otherwise**: "4 Resistors 1K (R1, R8, R11, R12) / 1 Resistor 220 (R10)" | ✓ against drawing and prose; ✗ against the BOM. Resolved below |
| `:44` `C6` | 220 nF | drawing "C6 0.22"; BOM; §1.5.2 | ✓ ×3 |
| `:46` `R11` | 1 kΩ, pin 7 to pin 6 | drawing "R11 1K" in the feedback; BOM's 1K group names R11 | ✓ ×2 |
| `:49` `C7` | 1 µF | drawing "C7 1uF/50V NP"; BOM "2 Capacitors 1uF NP/50V (C2, C7)" | ✓ ×2 |
| `:50` `R12` | 1 kΩ, after C7 | the drawing gives this second series resistor 1K and **labels it "R11" as well** — the same designator twice on one drawing; the BOM's 1K group carries an R12 | ✓ **value**; the designator is the deck's own reading, as its header says |
| `:51` `Rp3` | 100 kΩ | drawing "P3 Level 100K"; BOM "1 Potentiometer 100K Lin (P3)"; §1.5.3 "a 100K audio potentiometer P3" (prose says audio, i.e. log; BOM says Lin) | ✓ value; the deck fixes Level at maximum, so the taper never enters |

#### `models.lib`

| Deck | Value | Source | |
|---|---|---|---|
| `:24` `Rrev` | 5.827E+9 Ω | S6's file: "R1 1 2 5.827E+9", with its own comment that the resistor "does not reflect a physical device … improves modeling in the reverse mode" | ✓ |
| `:27`–`:28` diode | IS 4.352E-9, N 1.906, BV 110, IBV 0.0001, RS 0.6458, CJO 7.048E-13, VJ 0.869, M 0.03, FC 0.5, TT 3.48E-9 | S6's `.MODEL 1N4148 D`, read in full this run: **all ten identical** | ✓ |
| `:23` node order | "Node 1 = anode, node 2 = cathode" | S6 has `D1 1 2`, i.e. anode 1 / cathode 2 for the *model*; its header's "Package pinning does not match Spice model pinning. Package Pin 1: Cathode" is about the physical part, not the netlist | ✓ the comment is right, and the trap it steps over is real |
| `:61` `aol` | 1e5 | S8: "Large Signal Voltage Gain … MIN. 86 dB, TYP. 100 dB" at RL≥2kΩ, VO=±10V → 1e5 | ✓ |
| `:61` `gbw` | 3e6 | S8: "Gain Bandwidth Product … 3 MHz". S9's specification table also 3 MHz; **S9's prose says "4MHz typical"** — the deck uses the figure both the datasheet and the table give | ✓, with the disagreement recorded |
| `:61` `vsat` | 1.0 | S8: "Maximum Output Voltage Swing 1 … MIN. ±12 V, TYP. ±14 V" at RL≥10kΩ → 1 V inside each rail. (The ±15 V test-supply line was not separately quoted in this run's fetch; the swing rows and their load conditions were.) | ✓ |

#### The three places S1 contradicts itself, and what each costs

1. **R8 versus R10 (220 Ω versus 1 K), and it is the only one that moves a
   number.** Drawing and prose put 220 Ω on the tone pot's wiper; the BOM puts
   1 K on R8 and 220 Ω on an R10 that appears in neither tone drawing nor tone
   prose. The arithmetic decides it without preference: with 220 Ω the shelf
   zero is 1/(2π·220·0.22 µF) = 3288 Hz and the maximum boost 1 + R11/R8 =
   14.9 dB — S1's own sentence is "the network shunts feedback frequencies
   above 3.2KHz to ground", and PedalPCB reports 14.9 dB independently. With
   the BOM's 1 K the zero falls to 723.4 Hz, landing on top of the fixed
   low-pass, and the boost drops to 6.0 dB, which S1 claims nowhere. The decks,
   §1 and T4 use the drawing-and-prose reading; T4's source cell now says so.
2. **"R11" appears twice on the tone drawing**, on the feedback resistor and on
   the series resistor after C7, both 1 K. The deck calls the second one R12,
   after the BOM's 1K group. No value is affected.
3. **The prose and the BOM disagree about R12 and R13 as well.** §1.6 describes
   the output buffer as having "a 10K emitter resistor R13, biased from the
   4.5V bias source with R12 510K", while the BOM reads "2 Resistors 510K (R2,
   R13)" and lists R12 among the 1 Ks. That stage is not modelled, so nothing
   in this dossier depends on it — but it is a third instance, which is what
   makes the designator scheme, not any single line, the thing not to trust.

#### Two corrections this check produced

- **The SPICE README's claim that S1's "text summary gives the (−) input
  resistor as 1K" is not supported by S1.** The page names R4 exactly once, in
  the BOM, as "1 Resistor 4K7 (R4)"; the drawing says 4K7; and a grep of the
  raw HTML for `1K` returns only the BOM's 1 K group, the R7C5 sentences and
  the output impedance "1K2". There is no 1 K claim about R4 anywhere on the
  page. The netlist's 4.7 kΩ was never in doubt — **only the README's account
  of a conflict was wrong**, and it is corrected there (`tools/spice/ts808/
  README.md`, "Sources reached"), along with the RA note.
- **The mirror serves one GIF for every formula.** All eighteen `gif.latex`
  `<img>` tags on the page point at the same path, and that path returns a
  single 370-byte, 81×16 GIF reading `r_π << R12` — one equation from the
  output-buffer small-signal section, standing in for every other. So **no
  equation on this mirror is readable**, the origin does not resolve, and every
  numeric claim taken from S1 must come from its prose, its drawing or its BOM.
  Any figure a future run attributes to "the article's formula" was not read
  there.

#### One method note, because it nearly went the other way

A `WebFetch` of S1 asking for the parts list returned a *clean, self-consistent*
list with "R8: 220" and "R10: 220" — reconciling a contradiction the page
actually contains, and dropping the 1 K assignment that is the whole conflict.
The BOM's real line is "4 Resistors 1K (R1, R8, R11, R12)". The conflict was
only visible because the page was fetched with `curl`, converted to text and
grepped. This is the rule
`agent-knowledge/instrument-sources.md` already states for PDFs — a fetch
summary is a lead, not a citable fact — holding for HTML too, and specifically
for the case where the source is *internally inconsistent*: a summarizer's
instinct is to make the list agree with itself, which is exactly the evidence a
transcription check exists to find.

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

Three notes. **The wire is `mix` = 0, not drive = 0**: at Drive minimum the
standout is still a 12× stage putting 20.8 % THD on a 200 mV input (T6), so
"drive at zero is a wire" would contradict the circuit. **Level-honest** means
the dry leg passes at exactly unity (T3), measured far below the diode
threshold. **At 22.05 kHz** T7 is stated over 20 Hz–11 kHz, there being no band
above; T1–T6 hold unchanged.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. ElectroSmash, "Tube Screamer Circuit Analysis" (MAS Effects mirror) | every value in §1; the 12–118 gain range, the 720 and 723.4 Hz corners, the 3.2 kHz treble boost, the diode types, the pot tapers | **License unverified — treated as copyleft.** Re-fetched and grepped by the licence audit 2026-09-06: **no rights line on this page**, only the mirror's "unofficial, non-commercial backup" footer; ElectroSmash's own "Some Rights Reserved" line is in the body of the mirror's *Rat* article, not here, and the origin does not resolve. Read for topology and values, nothing reproduced (vision §5); detail in Appendix G | https://electrosmash.mas-effects.com/tube-screamer-analysis.html | yes (`www.electrosmash.com` does not resolve here) |
| S2. Our TS808 ngspice decks | every number in §3 and Appendix A | MIT (this repo, `LICENSE`); the netlists are ours | `audiocomponents/tools/spice/ts808/README.md` | yes (local; `run.sh` + `analyze.py` re-run by the audit 2026-09-06, output identical line for line to Appendix A) |
| S3. Yeh, Abel, Smith, DAFx-07, "Simplified, physically-informed models of distortion and overdrive guitar effects pedals" | the block model, eq. 20–23, tone eq. 24; the 8–10× oversampling practice; the unmodelled even-order nonlinearity of measured pedals | "© 2007 D. T. Yeh. All rights reserved.", read on the author's index page <https://ccrma.stanford.edu/~dtyeh/papers/pubs.html>; the PDFs carry no rights text (grepped this run). **Not permissive**; a paper, so the math is portable and no code was copied | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_distortion.pdf | yes (WebFetch + pypdf) |
| S4. Yeh, Abel, Smith, DAFx-07, "Simulation of the diode limiter …" | the static DC approximation implemented "using a lookup table", its "typically less than -40 dB" error, the pre-filter that reduces aliasing. *Audit 2026-09-06: the Newton-tabulation sentence this row used to claim is **S3's** (§3.4), not this paper's* | as S3 (rights line at <https://ccrma.stanford.edu/~dtyeh/papers/pubs.html>; the PDF itself carries no rights text — grepped this run) | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_dafx_clipode.pdf | yes (WebFetch + pypdf) |
| S5. Yeh, Smith, DAFx-08 | §3.2.3: "The sampling rate was 8× oversampled the audio sampling rate of 48000 Hz to reduce signal aliasing in the output." | as S3 (rights line at <https://ccrma.stanford.edu/~dtyeh/papers/pubs.html>; the PDF itself carries no copyright or rights text — grepped this run) | https://ccrma.stanford.edu/~dtyeh/papers/yeh08_dafx_sim.pdf | yes (WebFetch + pypdf) |
| S6. Nexperia 1N4148 SPICE model | the ten diode parameters used in every Newton solve here | no license text in the file (re-read in full this run; `curl` gets HTTP 403, `WebFetch` reaches it). Nexperia's Terms of Use (<https://www.nexperia.com/about/terms-and-policies/terms-of-use>, re-read this run) reserve all rights and permit reproduction "for personal non-commercial use only" — **not permissive**; the parameter values are facts about a part, in our own `.model` line | https://assets.nexperia.com/documents/spice-model/1N4148.prm | yes |
| S7. The palette, probed under `audiocomponents/.venv/bin/python` | every measured palette number in §4–§5 and Appendices C–D | MIT (this organization): SPDX line in the file, `audioif/LICENSE` | `audioif/src/shared/audioif_distortion.c` | yes (re-imported and Appendix F re-measured by the audit 2026-09-06) |
| S8. Nisshinbo (New Japan Radio) NJM4558 datasheet, Ver.2013-11-05, HTML rendering | the three numbers in `models.lib`'s behavioural op-amp, on which every S2 figure rests: AOL 1e5 ("Large Signal Voltage Gain … MIN. 86 dB, TYP. 100 dB", RL≥2kΩ, VO=±10V), GBW 3e6 ("Gain Bandwidth Product … 3 MHz"), VSAT 1.0 ("Maximum Output Voltage Swing 1 … MIN. ±12 V, TYP. ±14 V", RL≥10kΩ) | no terms on the aggregator page; datasheet figures are facts about a part | https://pdf.datasheet.support/50c18840/njr.com/NJM4558LD.html | yes (2026-09-07) |
| S9. Texas Instruments RC4558 product page | the GBW cross-check. **The page disagrees with itself as read today**: its prose gives "4MHz typical" where its specification table gives 3 MHz. `models.lib` uses 3 MHz, which is the table's figure and S8's | facts | https://www.ti.com/product/RC4558 | yes (2026-09-07) |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Pitch-dependent drive.** The pre-clip path is a shelf: at max Drive the small-signal gain is 23.3 / 38.8 / 37.7 dB at 100 Hz / 1 kHz / 5 kHz, pole fitted 720.6 Hz vs 720.5 analytic. A 100 Hz tone shows less THD than a 1 kHz tone at equal input. | S2; S1; S3 eq. 20 | high | 100 Hz gain within 10 dB of 1 kHz at max Drive; the fitted shelf pole outside 720 ± 110 Hz (±15 %, this dossier's band); or 100 Hz THD ≥ 1 kHz THD at −14 dBFS | pre-clip transfer (STFT out/in) from a swept sine at Drive max, Mix 1, Tone fixed, **at a level low enough that halving it moves every reported point by less than 0.3 dB** — the diode pair is its own level-dependent shunt, and −60 dBFS reads the plateau 2.3 dB low where −72 dBFS reads it 0.12 dB low (Appendix H); then THD of 100 Hz and 1 kHz sines at −14 dBFS |
| T2 | **Symmetric, odd-only clipping.** h2 and h4 at or below −60 dB (SPICE −90); h3 runs −21.5 dB (Drive min, 50 mV) → −12.6 (Drive max, 50 mV), h5 −46.0 → −18.4. | S2; S1; S3 §4.2 | high | h2 **or h4** above −40 dB at any Drive — the 20 dB between the claim and the bar is this dossier's allowance for the rebuild's own numeric floor, not a second claim; h3 at Drive max outside −12.6 ± 2 dB; h5 at the same point outside −18.4 ± 3 dB | harmonic spectrum, 1 kHz sine at −26 dBFS, Drive min and max, **Symmetry macro at centre** (matched pair) |
| T3 | **Output = input plus a clipped feedback voltage.** Output peak = input peak + 0.37–0.48 V (0.415 / 0.633 / 0.978 V for 50 / 200 / 500 mV at Drive max), so THD at Drive max *falls* as input rises: 28.3 → 26.6 → 21.0 %. | S2; S3 eq. 23 | high | **output peak minus input peak outside 0.30–0.55 V** at any of −26 / −14 / −6 dBFS at Drive max (SPICE 0.365 / 0.433 / 0.478 V; the band this dossier's); or THD at Drive max rising from −14 to −6 dBFS | output peak vs input peak, and THD, on a 1 kHz sine at −26 / −14 / −6 dBFS, Drive max, Tone fixed and Level at unity |
| T4 | **A fixed low-pass and a movable shelf, not a moving corner.** 796 Hz first-order low-pass that never moves; the shelf spans −9.64 → +0.53 dB at 1 kHz and −19.95 → −3.51 at 5 kHz while 100 Hz moves 0.34 dB. Brightest is still 3.5 dB down at 5 kHz. | S2 (SPICE and an independent nodal solve agree to 0.03 dB); S1's drawing and prose, **not its BOM** (Appendix I); S3 eq. 24 | high | Tone moving 100 Hz > 1 dB; brightest flat within 1 dB at 5 kHz; a −3 dB corner tracking the knob; or any of Appendix A's nine tone points (three positions × 100 Hz / 1 kHz / 5 kHz) missed by more than 2 dB | magnitude response from a swept sine at Tone 0 / 0.5 / 1, read at 100 Hz, 1 kHz, 5 kHz, **at Drive minimum and −60 dBFS**, where the feedback voltage is 11 mV and the drive stage is linear to 0.02 dB (Appendix H) |
| T5 | **The control law.** Plateau gain 12 → about 108 (fitted 107.8 with the pair's 5.66 MΩ zero-bias shunt — 11.3 MΩ each, and it is the pair that parallels the 551 kΩ; 118.2 ideal); THD at 50 mV rises monotonically with the pot, 8.4 → 26.7 → 28.3 %. | S2; S1 | high for the span; medium for the knob law (§8 Q4) | **small-signal plateau at Drive minimum outside 10–15** (20.0–23.5 dB) **or at Drive maximum outside 90–130** (39.1–42.3 dB) — 11.85 analytic at Drive min (11.76 with the pair's shunt; the deck sweeps AC only at pot max) and 107.8 SPICE-fitted at Drive max, the bands this dossier's; or THD at −26 dBFS not monotonic in Drive | pre-clip gain at Drive 0 / 0.5 / 1 by T1's level-independent sweep; THD of a 1 kHz sine at −26 dBFS at the same three settings |
| T6 | **It is never clean.** At Drive minimum a 50 mV input already shows 8.4 % THD, a 200 mV input 20.8 %. | S2 (pos 0) | high | THD outside 10–40 % at Drive minimum with a −14 dBFS input, or outside 4–20 % at −26 dBFS (SPICE 20.8 and 8.4 %; the bands this dossier's — the lower bound is the claim, the upper stops a build that is merely broken from passing) | THD of a 1 kHz sine at −14 dBFS and at −26 dBFS, Drive minimum, Mix 1 |
| T7 | **Alias floor.** Inharmonic energy in a 1010 Hz sine at Drive max, −6 dBFS, is ≥ 60 dB below the fundamental over 20 Hz–20 kHz. | mechanism from S3/S4/S5; the −60 dB *bar* is this dossier's, 20 dB under S4's "typically less than -40 dB" static-approximation error so aliasing is never the dominant error | medium (bar is a design choice; mechanism certain) | inharmonic energy above −60 dB at that point on **any** target, the P4's single-precision build included | sum of every FFT bin more than two bins from a harmonic of 1010 Hz and from DC, against the fundamental's bin; 4800 samples at 48 kHz, no window (101 exact periods, so every harmonic lands on a bin) |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Attempted and not reached:** ElectroSmash's own rights page, re-tried this
run at `www.electrosmash.com/rights` and `electrosmash.com/rights` — neither
host resolves here (`getent hosts`: no answer; `curl`: `http=000`), so no page
licensing the Tube Screamer article has been reached, which is S1's call.
(§8 Q7 asks for exactly this re-fetch; it is done, with that result.) **Not
attempted, and therefore not cited:** R. G. Keen's GEOFEX article, which S3
names as its own schematic source, and `web.archive.org` — both recorded in
`agent-knowledge/instrument-sources.md` as unreachable from this machine.
**Every source in the table above was reached by this run's own audit**, not
carried over from an earlier run's claim. No emulator was consulted, so no
copyleft-porting call arose.

*(from §2)*

**Audit note:** the Phase 0 licence-and-citation audit re-fetched every row
above on 2026-09-06 — every URL, the local decks and the palette — and
corrected the licence and citation defects listed in **Appendix G**, which
also records what it re-ran, what it could not verify, and one claim an
earlier audit block made about itself that was not true of the file.

*(from §2)*

**Netlist transcription check (2026-09-07).** Every value in the S2 decks was
read back to S1 element by element, against its two stage drawings (fetched as
images and read), its prose and its BOM, and against S6's file. **All 21
component values S1 supplies are confirmed; `models.lib`'s fourteen model
numbers check against S6, S8 and S9; nothing could not be checked, and no
trait row is marked "netlist unverified."** The decks were re-run the same
day, output identical to Appendix A. What the check found is three places
where **S1 contradicts itself on a designator** (one moves a number in T4),
one component its BOM omits, one claim the SPICE README made about S1 that S1
does not support, and one property of the mirror: **all eighteen of its
formula images resolve to a single 81×16 GIF**, so no equation on it is
readable and every number must come from prose, drawing or BOM. **Appendix I**.

*(from §3)*

**Trait-critic pass, 2026-09-06.** Rows after the pass: **7 (T1–T7)**; none
removed, none added, none unmeasured. Every SPICE figure above was re-run here
(`tools/spice/ts808/run.sh`, then `analyze.py`) and came back identical line
for line to Appendix A. Five rows were rewritten and one number corrected —
Appendix H.

*(from §3)*

**Netlist transcription check, 2026-09-07.** Every value these rows rest on
was read back to S1 (Appendix I). The drive rows — T1, T2, T3, T5, T6 — rest
on R4 4K7, C3 0.047 µF, R6 51K, P1 500K, C4 51 pF and an anti-parallel
like-diode pair, each of which S1 gives **twice**, in its drawing and in its
BOM, in agreement. T4 rests on R7 1K, C5 0.22 µF, R9 10K, P2 20K, R8 220 Ω,
C6 0.22 µF and R11 1K, and **R8 is the one value S1 states two ways**: drawing
and prose put 220 Ω on the pot wiper, the BOM puts 1 K there. The arithmetic
decides it, not a preference: 220 Ω gives a shelf zero at 3288 Hz and a
maximum boost of 1 + R11/R8 = 14.9 dB, which is S1's own "3.2KHz" sentence
and the 14.9 dB PedalPCB reports independently, while the BOM reading gives
723 Hz — on top of the fixed low-pass — and 6.0 dB, which S1 claims nowhere.
No trait number changes; T4 now names which reading it is.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline (256 frames at
48 kHz = 5.33 ms, the block audioif's own nodes carry —
`audioif_multiply.h:24`): **ESP32-P4 0.08, ESP32-S3 0.20.** Lean patch
expected: **yes** on the S3, the oversampling factor being the knob (vision
§7.2), fixed by Phase 1's cost/alias table. RAM: one waveshaper table
(proposed 1025 × int16) plus five biquad states.

*(from §3)*

**Latency (vision §9a): algorithmic latency zero — 0 samples, 0.00 ms at
48 kHz.** Nothing here looks ahead; the dry leg through the Splitter is a copy.
The one thing that *could* add latency is §5's waveshaper anti-aliasing, so the
ask requires minimum-phase IIR interpolation and decimation — which also
matches an analog circuit's phase; a linear-phase FIR decimator would add its
group delay and is refused. **Options that add latency: none.**
`tail_samples` = 0 (no delay line, no reverberant state; biquad ringing is
bounded by the tail probe, not reported as latency). Reported
`latency_samples` = 0, verified by the click measurement at the class gate.

*(from §4)*

```
source ─ Splitter(2) ─ tap0 ───────────────────────────────────────────┐
                     └ tap1 ─ HP(720 Hz, 1st order) ─ ×(R2/R1) ─ curve f ┤
   Mixer: tap0 at 1.0, shaped branch at a ─ LP(796 Hz) ─ treble shelf ─ Level
```

*(from §4)*

`audioroute.Splitter` (audioif's own, `upstream-diff.md:661`; four taps,
`audioif_splitter.h:21`) fans the source out; `audiomixer.Mixer` sums the dry
tap at unity with the shaped branch; low-pass and shelf are
`audiofilters.Filter` biquads whose coefficients Python recomputes on a macro
move. A mono source gets exactly this graph — the class is not stereo by
definition.

*(from §4)*

Measured on the palette this run (S7; Appendices B–D): dropping either fixed
palette curve — `soft_clip` (`audioif_distortion.c:37`) or `WAVESHAPE`
(`:31-32`) — into that structure already carries **T2, T3, T5 and T6** at all
nine SPICE operating points, because the structure makes them, not the curve.
First-order sections do not exist on the palette (`synthio.Biquad` takes mode /
frequency / Q / A only, `audioif/src/synthio/Biquad.c:37-61`) but a
two-real-pole biquad with its second pole parked at 40 kHz tracks one within
0.51 dB to 8 kHz, covering **T1 and T4**. The Tier 1 wire is `mix` **exactly
0**, not `mix ≤ 0.01`: the `mix <= 0.01` copy branch is the MicroPython /
CircuitPython binding's alone (`audiofilters/Distortion.c:244-251`), and the
CPython build does not run that binding — its shim calls the shared kernel
(`src/cpython/audiofilters.py:163` → `audioif_distortion.c:47`), which has no
such branch. Measured this run on the same graph: at `mix = 0.005` and
`mix = 0.01` MicroPython (`cmods/bin/micropython`) returns the source bytes
unchanged while CPython mixes, 306 counts of difference at `mix = 0.01` on a
20000-count sine; both agree byte-for-byte at `mix = 0` and both differ from
the source at `mix = 0.02`. So the `Mix` macro's bottom 1 % is a Tier 1
cross-runtime divergence of the **ported node**, and the rebuild reaches the
wire by not building the branch (or by holding `mix` at 0), never by leaning
on the ≤ 0.01 shortcut. The one Tier 2 trait the palette cannot reach is
**T7** — §5. **audioif#23 does not reach this class**, verified rather than
assumed: burst-then-silence through `audiofilters.Filter` at every corner this
graph uses — LOW_PASS 360 Hz (the `Body` macro's floor), LOW_PASS 796 Hz,
HIGH_PASS 720 Hz (each at the Q = 0.1543 the first-order trick uses) and the
3.3 kHz treble shelf at Q = 0.707 — settles to **exact zero, 0 counts**, in the
last 500 ms and in the final sample. The fixed-point node's DC
hold sets in below about 100 Hz (measured at Q = 0.707: HIGH_PASS 60 Hz 2 counts,
30 Hz 8, 10 Hz 71, 3 Hz 789), and nothing here goes there. So this class takes no
position on the Gate 0 biquad answer.

*(from §4)*

Python computes, at construction and on a macro move, the plateau gain and the
curve's amplitude and scale for the Drive position (the Newton solution of S3
eq. 22 at `dV/dt = 0` with S6's diode, tabulated once on CPython and shipped as
data — never rebuilt on a board, the ESP32 ports being single-precision) plus
three biquads' coefficients. C runs per sample: the splitter copy, one biquad,
a table lookup at the oversampled rate with its decimation, the mixer sum, two
biquads, the level.

*(from §5)*

- **Oversample by composing `audiospeed.SpeedChanger`.** The palette does carry
  a rate changer, so ×4 could in principle be `SpeedChanger(rate=0.25)` →
  `Distortion` → `SpeedChanger(rate=4.0)`. Measured on T7's own probe (1010 Hz,
  −6 dBFS, `soft_clip` at +20 dB pre-gain, whose base-rate floor is −50.9 dB):
  the composed chain reads **−6.9 dB**, 44 dB *worse*. The cause is in the node,
  not the wiring — `SpeedChanger` is a zero-order hold with no interpolation and
  no decimation filter (`src/cpython/audiospeed.py:56-66`, index `phase >> 16`,
  frame copied whole), so the upsample adds hold images and the downsample folds
  everything back. It is a CircuitPython port (`src/audiospeed/SpeedChanger.c:1`)
  and therefore may never gain an interpolator.

*(from §5)*

- **Build the curve from `audiomath.Multiply` instead of a table.** `Multiply`
  takes two arbitrary streams (`src/cpython/audiomath.py:29-31`), so a `Splitter`
  feeding both inputs is x², and a chain of them is an odd polynomial — a real
  compose-first waveshaper, and one that would *pass* T7 for a single tone,
  because an order-N polynomial makes no harmonic above N·f. It fails elsewhere:
  a polynomial does not saturate. Fitted so that h3 = −12.6 dB and h5 = −18.4 dB
  at −26 dBFS (T2 at Drive max), `f(u) = u − 1.4504·u³ + 0.8348·u⁵` reads THD
  26.3 % at the fit point and then **53.3 % at −14 dBFS and 51.4 % at −6 dBFS,
  with output peak 8204× the input** — where T3 requires the output peak to
  track the input peak plus 0.37–0.48 V and THD to *fall* over exactly that
  span. The composition trades T7 for T3 and T5, so it is not a substitute for
  a saturating table.

*(from §5)*

No ask for the curve *shape*, the dry sum (`Splitter` + `Mixer` exist), or
first-order sections (0.51 dB to 8 kHz). The dry sum was re-verified this run:
a `Splitter` (measured at `taps=3`, the worst case of the pair) tap 0 through
`audiomixer.Mixer` at level 1.0 is byte-identical to the source and puts a
click back on its original frame — unity and zero latency on the dry leg,
which is what Tier 3's `latency_samples` = 0 rests on.

*(from §7)*

- `drive.py:72-75` — Drive goes into `pre_gain` with the level put back by
  `post_gain`, because the node ignores `drive` in OVERDRIVE mode
  (`upstream-diff.md:1228`). That compensation destroys T3 — the output peak no
  longer tracks input peak plus a diode drop — and nothing sums a dry signal at
  unity anywhere in the chain.

*(from §7)*

- `drive.py:73-74` — the OVERDRIVE curve is asymmetric. Measured on the shipped
  configuration: h2 −37.4 dB against h3 −38.6 at −20 dBFS, h2 −27.4 against h3
  −33.6 at +12 dB of pre-gain — the *second* harmonic is the larger. That fails
  T2 outright, and `drive.py:8-10` calls the asymmetry a feature.

*(from §7)*

- `drive.py:77-81` — "tone" is a second-order Q = 0.707 low-pass at 4.5 kHz
  applied *after* the node's own mix, so at `mix < 1` the dry path is filtered
  too (the defect `TapeDelay` had, `upstream-diff.md:818`) — and a moving
  low-pass corner is exactly what T4 says the standout does not have.
