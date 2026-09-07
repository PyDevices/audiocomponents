# Effects Dossier — `Chorus` (Electro-Harmonix Small Clone)

**Class:** `lib/audioeffects/modulation.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Modulation, roadmap Phase 3
**Standout:** Electro-Harmonix Small Clone (MN3007 variant), per vision §4.2 —
**confirmed**, §2.
**Grade:** circuit — two independently hosted schematics read this run (both
of adaptations, §2) plus the maker's panel spec; every Tier 2 trait derived
analytically from the values the two drawings share.
**Portability tier:** needs audioif-own nodes (`audioecho.FeedbackDelay`)
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

The guitar enters through a 33n/220k bias into half an
RC4558 wired non-inverting, feedback 33k with 6k8 + 10n: unity below 400 Hz,
+15.3 dB above 2.34 kHz — a **pre-emphasis shelf** that lifts the treble
before the noisy brigade sees it (S1, S3; App. A). The **dry is tapped at that
stage's output**, so dry and wet both carry the emphasis. The wet leg is
DC-biased by a 100k trimmer and passes a three-pole transistor Sallen–Key
low-pass (3k3/10k/10k with 3n3, 15n, 470p) into a 2N5087 follower and the
**MN3007**, a 1024-stage bucket brigade (S4 fn.1, S5). Its two-phase clock is
the complementary Q/Q̄ pair of a **CD4047B astable** (period 4.40·RC, S6),
timing capacitor 100 pF vintage and 150 pF in the 2002 reissue (S1), whose
RC-common node the LFO drives through 39k: **the LFO moves the clock, not the
delay**, so the delay — N/(2·f_clk), S4 §2.1 — is its reciprocal. The LFO is a
relaxation pair, half an LM358 integrating through the 1 MΩ Rate pot into
2.2 µF and the other half a Schmitt comparator (120k in, 470k hysteresis)
closing through 47k — **a triangle**, whose amplitude the two-position Depth
switch selects. The BBD output runs a second three-pole Sallen–Key
(10k/39k/39k with 4n7, 2n7, 180p) into a 2N5088 follower, and dry (22k) and
wet (27k vintage, 20k reissue) meet at a **passive summing node** feeding an
inverting RC4558 whose 33k ∥ (6k8 + 10n) feedback is the exact complement of
the input shelf: **de-emphasis**, which cancels the pre-emphasis on the dry and
puts the brigade's noise 15 dB down on the wet. There is **no feedback path,
no compander and no tone control**; Rate and Depth are the only panel controls.

## 2. Sources and license calls

Each was reached with WebFetch or curl on 2026-09-06. **What each gave, and
its licence text as read, is in App. F and App. G** — nothing here comes from memory.

| Source | Licence call |
|---|---|
| **S1** Aion FX, *Lithium Analog Chorus* … (App. S1) | the build doc's own **"LICENSE & USAGE"** … (App. S1) |
| **S2** [Guitar FX Layouts, *EHX Small … (App. S2) | site footer "Copyright © 2010-23 … (App. S2) |
| **S3** A second Small Clone drawing … (App. S3) | page "All rights reserved" … (App. S3) |
| **S4** [Raffel & Smith, *Practical Modeling of Bucket-Brigade Device … (App. S4) | **no rights statement anywhere in the PDF** … (App. S4) |
| **S5** [ElectroSmash, *BBDs: … (App. S5) | unofficial non-commercial mirror … (App. S5) |
| **S6** [TI *CD4047B* data … (App. S6) | "Copyright © 2003 … (App. S6) |
| **S7** [ElectroSmash, *Boss CE-2 … (App. S7) | "Some Rights Reserved, you are free to copy … (App. S7) |
| **S8** [Electro-Harmonix, *Small … (App. S8) | "© 2026 Electro-Harmonix. All Rights … (App. S8) |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Measurements are numbered M1…M6 and specified in App. H. Every row states the
conditions it is measured under; the arithmetic is App. C and App. I.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **One delayed voice, and only one** — one line, one tap, no regeneration. An impulse at the faithful patch, wet-only, Depth 0: after the first arrival's peak sample, no later sample within 2 s exceeds −60 dB of that peak. | S1, re-read this run: the complete parts list … (App. T1) | high | A second arrival above −60 dB of the first, or a decaying train | M1 |
| T2 | **The delay trajectory is the reciprocal of a triangle, not a triangle.** With the modulation running, the wet path's instantaneous pitch offset *ramps* within each half-cycle instead of holding a level: the largest:smallest \|offset\| inside one half equals (d_max/d_min)², taken from the same run's measured delay trajectory, within 20 %. A delay linear in the LFO gives exactly 1.0. Measured at a Depth whose measured swing d_max/d_min is ≥ 1.25 — below that the ±20 % window no longer excludes 1.0 and the probe stops discriminating (App. I) — and the swing is reported with the result. | S1, S3 (R31 39k runs from the LFO/Depth node into the CD4047's timing network: the clock moves, not the delay), S4 §2.1 (delay = N/(2·f_cp)) | medium — the injection law is read from the drawing; the 4047's transfer thresholds and D3 are unmodelled | An offset flat within each half (ratio 1.0 ± 20 %), or a ratio more than 20 % from (d_max/d_min)² at a measured swing ≥ 1.25 | M2 |
| T3 | **The wet voice is far darker than the dry, and darker than anti-aliasing requires.** At Depth 0, 48 kHz, with the delay set to a whole number of samples: the wet/dry third-octave magnitude ratio is within 1 dB of its 200 Hz value at every band centre below 500 Hz, falls monotonically from band centre to band centre between 1 kHz and 10 kHz, and at 10 kHz is at least 10 dB below its 200 Hz value. | S1's parts list, re-read this run for all six … (App. T3) | high | A ratio within ±1 dB from 100 Hz to 10 kHz, or less than 10 dB below its 200 Hz value at 10 kHz | M3 |
| T4 | **Wet and dry are summed at near-equal level, not as a polite wet trim** — there is no wet-level control on the pedal at all. Band-limited RMS over 100–500 Hz, where the reconstruction filter is flat: wet/dry 0.815 (−1.8 dB) at the vintage 27k and 1.10 (+0.8 dB) at the reissue 20k, against a fixed 22k dry. | S1's parts list and build notes … (App. T4) | high | Either patch's measured ratio more than 2.5 dB from its drawn value — vintage outside 0.61–1.09, reissue outside 0.82–1.47 | M4 |
| T5 | **Rate spans 0.43 Hz to 9.5 Hz across the knob's travel — a 22:1 range.** f = R28/(4·R27·R·C14) with R = R26 + the Rate pot (47k…1.047 MΩ) gives 9.47 Hz and 0.425 Hz. | S1's parts list, re-read this run (R26 47k … (App. T5) | medium — C-taper pot … (App. T5) | A measured LFO fundamental outside 0.3–12 Hz at either macro extreme, or a span between the extremes under 10:1 | M5 |
| T6 | **The clock is modulated, not the delay** — the discriminator §5's node ask turns on. The delay trajectory carries a **second harmonic at m/2 of its fundamental, in quadrature with it**, m being the clock swing the same run measures; a delay driven by an additive LFO carries no second harmonic at all. At m = 0.1225 that is −24.2 dB and at m = 0.35 it is −14.9 dB (App. I). | S1, S3 (the LFO drives the 4047's timing … (App. T6) | high for the … (App. T6) | No second harmonic above the trajectory's noise floor at any Depth, or one more than 6 dB from m/2 at the m the same run measures, or one in phase rather than quadrature with the fundamental | M6 |

Characters: none — one standout.

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's deadline: **P4 0.08, S3 0.15**.
Lean patch expected: **no** — one interpolated line plus one one-pole.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node.** `audioecho.FeedbackDelay` is the bucket brigade already: it
reads the line **per sample with linear interpolation between two neighbours**
(`audioif_feedback_delay.c:227-228`) under a **per-sample** oscillator
(`:209-213`) — the circuit's mechanism, and what the ported
`audiodelays.Chorus` lacks. `feedback=0.0` (T1); `delay_ms` = the mean; `mix`
= the wet/dry ratio **while it stays at or below 1**, the dry pinned at unity
(`:201-202`); `damping_hz` sets the wet voice's low-pass for T3, since the
in-loop one-pole reaches the output as well as the line (`:231-235`,
`:260-261`), so at zero feedback it is simply a low-pass on the wet voice.
One node, one line, one allocation (`audioecho/FeedbackDelay.c:110`; the
output block is a fixed struct member, `audioecho/FeedbackDelay.h:25`).
Python computes the mean delay, the depth, the damping corner, and — for T2
and **T6** — **one period of the clock law as a table** (`1/(1 + m·tri θ)`, normalised) on
CPython, shipped as data (§5); a macro move rewrites scalars only.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**Ask N-shape — a modulation shape table on `audioecho.FeedbackDelay`.**

- **Trait it unblocks:** T2 and **T6** (and `Vibrato`'s **T7** — one ask serves …  *(argument in full: App. R)*
- **What the palette does instead:** the kernel adds …  *(argument in full: App. R)*
- **Refutation record.** (1) *Step `delay_ms` from Python*: a config write …  *(argument in full: App. R)*
- **The ask, additive:** an optional `wow_shape` — a one-period table (int16, …  *(argument in full: App. R)*
- **Measurement that shows the gap:** T6's probe against a `FeedbackDelay` at …  *(argument in full: App. R)*

No other ask; the rest composes.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Rate` | UNIPOLAR | 0.3–10 Hz, log | the Rate knob (T5) |
| 1 | `Depth` | UNIPOLAR | clock swing 0…±35 % | the two-position Depth switch |
| 2 | `Mix` | UNIPOLAR | 0–1; 0.5 = the circuit's near-equal sum | the fixed 22k/27k network (T4) |
| 3 | `Delay` | UNIPOLAR | 3–20 ms mean | the 4047's timing capacitor |
| 4 | `Tone` | UNIPOLAR | 1–12 kHz wet −3 dB corner, Nyquist-clamped; Python pre-warps the node's nominal `damping_hz` (§4) | the reconstruction filter (T3) |
| 5 | `Width` | UNIPOLAR | 0–1; 0 is the circuit | nothing — declared a departure |
| 6 | `Level` | UNIPOLAR | −12…+6 dB | nothing — output trim |

Characters: none. `capabilities`: **`()`** — the rate is a free-running
relaxation oscillator and nothing in the circuit references a beat (§8.3).

Patches: `Near-equal blend` (mix 0.5, 8.8 ms, depth 0.35, 0.8 Hz, tone 3 kHz —
the drawn vintage values) · `Long line, deep` (13.2 ms, depth 0.7, mix 0.52,
0.5 Hz) · `Short line, shallow` (4 ms, depth 0.2, 1.6 Hz) · `Slow and wide`
(0.35 Hz, width 0.8) · `Fast warble` (6 Hz, depth 0.5, 6 ms) · `Dark wet`
(tone 1.5 kHz, mix 0.6) · `Mono faithful` (width 0, the drawn values, 0 dB).

## 7. Defects in the current class the rebuild must not repeat

- **No surface:** `MACRO_LABELS = ()` (`modulation.py:26`), `PATCHES = {0:
  ("Default", ())}` (`:28`).
- **Three voices where the circuit has one** (`:29`), and the node cannot have
  one: with `voices == 1` the kernel copies the input and reads nothing from
  the line (`audioif_chorus.c:15-16`). Measured this run at `delay_ms=20`,
  `mix=1.0`: `voices=1` → one arrival (the dry); `voices=2` → samples 0 and
  959; `voices=3` → 0, 479, 958 — **whole-sample, evenly spaced, no
  interpolation** (`audioif_chorus.c:18`, `:22`).
- **Block-rate modulation:** the delay is a `synthio.LFO` (`:30-33`), updated
  ~187 Hz at 48 kHz; at the shipped `rate=0.6`, `depth_ms=6.0` the step
  reaches ≈0.06 ms — about three whole samples, 187 times a second.
- **Not level-honest:** the kernel forms `sample + word*mix` then soft-clips
  (`audioif_chorus.c:27-28`) — the dry is at full scale before the wet is added.
- **Latency and tail undeclared:** neither `LATENCY_SAMPLES` nor
  `TAIL_SAMPLES` is set, so `_core.py:245-248` reports 0 and `:250-253`
  reports `None`, against a 42 ms line (`:33`).
- **`reset()`/`deinit()` reach one node** (`_core.py:366-374`, `:376-384`).

## 8. Open questions

1. **The absolute delay range.** App. B brackets 8.8 ms (100 pF) and 13.2 ms
   (150 pF) from the drawn 39k, but D3 and the LFO's DC level sit in that path
   and no unit measurement was found. *Settles:* the implementation session
   adopts the bracket as the Delay macro's centre and records it as derived;
   only a hardware capture closes it, and none is on the bench.
2. **Frequency-linear or resistance-modulating injection.** T2 assumes the LFO
   moves the charging current; if it moves the timing resistance the delay is
   *linear* and T2 fails. T2's probe discriminates against the model, not
   against hardware. *Settles:* the implementation session; a SPICE deck of
   the 4047 injection node would raise T2 to high.
3. **`tempo_sync`** — declared `()` from the standout; whether to offer a
   synced rate as a generalization is the implementation session's call.
4. **Width's second node.** A stereo spread needs a second `FeedbackDelay`.
   Whether that pushes Tier 3 past the S3's share — and so whether Width
   belongs in a `" - wide"` patch — is a Phase 3 cost measurement.
5. **The emphasis pair is only balanced on the vintage unit.** §4 declines to
   model it because it cancels; S1's build notes, read this run, add that the
   reissue "change[s] R8 to 9k1 … it puts the pre/de-emphasis filters out of
   balance". T3 and T4 are ratios and are unaffected, but the reissue patch
   claims half a pair. *Settles:* the implementation session.
6. **The interpolator's HF loss sweeps with the delay** (App. I): up to
   −1.99 dB at 10 kHz at 48 kHz, −16.65 dB at 22.05 kHz, and the *fractional*
   part moves at the LFO rate, so the wet top end wobbles where the circuit's
   fixed reconstruction filter does not. It is a rough analogue of the BBD's own
   clock-dependent insertion loss (S4 §4.2) and is not that function. *Settles:*
   a Phase 3 measurement characterises it — reported as an artefact, never
   claimed as a modelled trait.
7. **T4's reissue ratio versus Tier 1's level honesty.** The node reaches
   wet/dry 1.10 only by dropping the dry to 0.900 (§4, App. J). Either the
   class takes the 0.9 dB on the dry path and says so, or it holds the dry at
   unity and trims the whole output. *Settles:* the implementation session,
   when the Mix law is written; it is a design choice, not a node ask.

---


## Appendix

### A. Arithmetic on the drawn values

Computed this run with the repository's CPython, from S1 and S3 values only.

**Pre-emphasis** (non-inverting, R_f = 33k, R_g = 6k8 + 10n): zero
1/(2π(33k+6k8)·10n) = **399.9 Hz**; pole 1/(2π·6k8·10n) = **2340.5 Hz**;
plateau 1 + 33/6.8 = 5.853 = **+15.35 dB**.

**De-emphasis** (inverting, R_in = 10k, Z_f = 33k ∥ (6k8 + 1/sC)): LF gain
3.300 (+10.37 dB), HF gain 0.5638 (−4.98 dB), difference **15.35 dB** — the
exact complement about the same corners.

**The summing node** (dry through 22k, wet through R_w, loaded by 10k to the
op-amp's virtual ground and 220k to the reference):

| Wet resistor | dry coeff | wet coeff | wet/dry | dry through-gain |
|---|---|---|---|---|
| 27k (vintage) | 0.2430 | 0.1980 | 0.815 (−1.78 dB) | 0.802 (−1.92 dB) |
| 20k (reissue) | 0.2273 | 0.2500 | 1.100 (+0.83 dB) | 0.750 (−2.50 dB) |

The through-gain includes the de-emphasis stage's LF gain of 3.3; the pedal's
dry path is about 2 dB down overall, which the rebuild normalises (Tier 1).

*Audit correction (2026-09-06).* Re-reading S3's drawing at full resolution,
the 220k sits between the **wet** node (the follower's 1 µF output, ahead of
the wet resistor) and the +4.5 V reference, not at the summing node; the table
above sums it as a shunt at the summing node. That changes the absolute
coefficients by about 2 % and **does not change the wet/dry ratio at all** —
the ratio is 22/R_w whatever shunts the node, so T4's 0.815 and 1.100 stand as
stated. Recorded rather than silently corrected.

**LFO rate.** Half-period = 2·(R27/R28)·R·C, so f = R28/(4·R27·R·C14) with
R27 = 120k, R28 = 470k, C14 = 2.2 µF, R = 47k + Rate pot: **9.47 Hz** at
R = 47k, **0.425 Hz** at R = 1.047 MΩ.

**Reconstruction filter**, read as three independent RC sections (a
conservative reading — the middle capacitor returns to the follower's emitter,
making that a bootstrapped Sallen–Key section, which sharpens the knee):
corners 3386 Hz (10k/4n7), 1511 Hz (39k/2n7), 22672 Hz (39k/180p); magnitude
−1.95 dB at 1 kHz, −9.53 dB at 3 kHz, **−27.2 dB at 10 kHz**. Under the
Sallen–Key reading the same chain is roughly −16 dB at 10 kHz. T3 is stated
at "≥10 dB down at 10 kHz" so it holds either way; the measurement fixes which.

### B. The delay bracket

CD4047B astable period t_A = 4.40·R·C (S6), C the timing capacitor, R the
drawn 39k:

| Timing cap | f_clk | delay = 1024/(2·f_clk) |
|---|---|---|
| 100 pF (vintage) | 58.3 kHz | **8.79 ms** |
| 150 pF (2002 reissue) | 38.9 kHz | **13.18 ms** |

Both sit inside the MN3007's 5.12–51.2 ms span (S5) and inside the "5 to
40 ms … needed" for chorus (S7). Nyquist at 58 kHz is 29 kHz — nine times the
reconstruction filter's *highest* audio-band corner (3.39 kHz) and nineteen
times its lowest (1.51 kHz). S4's stated norm is a cutoff between
1/3 and 1/2 of the sampling frequency; this circuit's highest reconstruction
corner is about 1/17 of it and its lowest about 1/39.
**The Small Clone's darkness is a voicing choice, not an anti-alias
necessity** — that is T3's reason for existing.

*Caveat, re-read at full resolution this run.* S3 draws the 4047's pin 2 (R),
pin 3 (R-C common) and the far side of the 150 pF on **one node**, with D3 in
the pin-2 leg and the 39k running from the LFO/Depth node to that same node.
So the 39k is the resistor between the LFO and the timing network, **not a
measured timing resistance**, and D3 and the LFO's DC level sit in the path.
S6's own recommended astable ranges — C ≥ 100 pF, 10 kΩ ≤ R ≤ 1 MΩ — bracket
both drawn values, which is the only independent check available. Treat the
delay bracket as an order, not a figure.

### C. Why the reciprocal law has a measurable signature

With f_clk(t) = f₀(1 + m·u(t)), u the unit triangle, d(t) = d₀/(1 + m·u).
Pitch offset through a time-varying delay is Δf/f = −d′(t), and
d′(t) = −d₀·m·u′(t)/(1 + m·u(t))². On a triangle u′ is ±4/T, constant on each
half, so the only within-half variation is the squared denominator: over one
half the offset sweeps by ((1+m)/(1−m))² = (d_max/d_min)², **3.45 at m = 0.3**
— m = 0.3 is an **illustrative** modulation index, not a sourced value; no
source reached this run fixes the Small Clone's clock swing, and T2 is stated
against the swing the measurement itself finds.
The laws separate cleanly:

- **delay linear in the LFO** (what the palette's additive sine does): d′ is
  constant on each half — the pitch offset is a **two-level square wave**.
- **delay reciprocal in the LFO** (the clock-modulated circuit): the offset
  **ramps** within each half, by (d_max/d_min)².

One probe separates them and the separation grows with depth.

**A correction to vision §3's illustration, recorded rather than dropped.**
§3 says of a chorus that "the pitch deviation is unequal on the rising and
falling halves of the cycle". Under a symmetric triangle and a
frequency-linear injection that is *not* what falls out: the halves stay
mirror-symmetric in magnitude, traversing the same deviation range in opposite
order. The signature that does fall out is the within-half ramp, and T2 states
that instead. Same shape as the TS808 run's correction to §3's overdrive
illustration.

Expanded for a sinusoidal s, 1/(1 + m·s) = (1 + m²/2) − m·s − (m²/2)·cos 2θ − …
: the second harmonic is m/2 of the fundamental and in **quadrature** with it.
That quadrature term is why §5's cascade workaround cannot reach the trait.

**S5's formula, read.** The seed's first draft recorded S5 as stating
"Total delay time = N / fclock" and contradicting its own quoted range. **That
is withdrawn: it is not what the page says.** S5 sets the formula as an image
(`images/mn3007-bucket-brigade-devices/gif.latex`) whose surrounding text is
only "the total delay time can be calculated as: … where: N: is the number of
stages. f clock: is the circuit clock frequency." The image was downloaded and
read this run: it renders **time_delay = N / (2 · f_clock)** — the same law as
S4, and consistent with S5's own 5.12–51.2 ms at 10–100 kHz. There is no
contradiction and nothing to discount. (One mirror artefact worth recording:
both `<img>` tags on that page point at the same `gif.latex` file, so the
article's *second* formula — the filter-cutoff one — is not preserved on the
mirror.)

### D. Where the two drawings agree

Checked value by value between S1 (vector, with designators) and S3
(independently hosted): input 33n / 220k / 1k / 33k / 6k8 / 10n; anti-alias
3k3 / 10k / 10k with 3n3, 15n, 470p; reconstruction 10k / 39k / 39k with 4n7,
2n7, 180p; mixer 22k dry, 20k wet, 10k in, 33k / 6k8 / 10n feedback; LFO 1 M
Rate pot, 2.2 µF, 120k / 470k, 68k / 82k / 180k, 47k, 47n; clock 39k into the
CD4047 with 150 pF (S3, the reissue value) or 100 pF (S1's vintage default)
and a diode; BBD input 12k / 33k / 39k with a diode (S3 draws these as
D3 and D1 with no type; the 1N914 part number is S1's BOM alone, and is not a
point of agreement between the drawings). S2's comment thread
independently confirms the IC complement. **No disagreement was found.**

*Provenance, corrected on audit.* Neither drawing is EHX's factory schematic.
S1 is Aion's *Lithium*, "an expanded adaptation" that adds a Mix pot (250kC in
series with the 20k wet resistor), a Depth pot in place of the switch, a 2M2
input pull-down of Aion's own (part `RPD`, "Input pull-down resistor"), and a
vintage/modern slide switch putting 47 pF beside the 100 pF; its build notes
name the original's values where they differ, and those notes are what §1 and
App. A rely on. S3 is titled "Schematic (Depth pot mod included)". The values
listed above are the ones both drawings carry and neither modification
touches. The 2M2 was carried into the seed's §1 as a Small Clone part in the
first draft; it is Aion's, and §1 no longer names it.

### E. What was looked for and not found

A factory or laboratory capture of a Small Clone (clock, delay or LFO period)
— searched, none reached, none on the bench.

**One measurement was found, and the first draft's blanket "none" is
withdrawn.** S2's comment thread carries a builder's meter readings from a
completed MN3007 Small Clone build: node voltages for every pin of the 4558,
MN3007, CD4047 and LM358, including "CD4047 - IC3 … 10 4.16 VAC, 4.377 VDC 11
4.17 VAC, 4.38 VDC" and, on the LFO integrator, "LM358 - IC4 1 3.73VAC,
**9.0 Hz with rate all the way up**". That last figure is the only measured
number on this circuit reached anywhere this run, and it sits 5 % from App. A's
drawn 9.47 Hz — corroboration for T5's fast end. It is a hobby build of S2's
layout, not a factory unit, so it raises no confidence to high on its own.

A DAFx or AES paper on this specific circuit — none found; S4 is the family
paper and is used as such. EHX's own published specifications — reached this
run (S8): they give the panel (a Depth **switch**, a Rate knob), the circuit
("Analog"), true bypass, mono, 12 mA draw and a 2000 release year, and **no**
delay, clock or LFO figure. A SPICE model of the CD4047's timing node — not
attempted this run; named in §8.2 as what would raise T2 from medium.

### F. What each source gave, and its licence text

**S1** gave the complete vector schematic with every reference designator and
value, plus build notes recording that EHX used a CD4047 rather than the
MN3101 and tied VGG to VDD, that the vintage timing capacitor is 100 pF and
the 2002 reissue's 150 pF, that the wet mix resistor moved from 27k to 20k
("a more prominent wet mix"), and that the original Depth control was a
2-position slide switch. **S2**'s body is a vero layout with no parts table; everything cited from it
is in its **comment thread** — the IC complement (4558 = IC1, MN3007 = IC2,
CD4047 = IC3, LM358 = IC4; 2N5087 = Q1, 2N5088 = Q2 and Q3, from a builder's
voltage list), a 150 pF cap "on pin 1 of IC3" / "the 150pF cap that's on the
CD4047", and the builder's 9.0 Hz LFO reading (App. E). The word *reissue*
does not appear on that page: the vintage/reissue attribution of 100 pF versus
150 pF is **S1's**, not S2's, and the first draft mis-assigned it. **S3** gave the
second drawing collated in App. D. **S4** gave "For any BBD, the total time
delay is given by Delay Time (s) = N/(2·f_cp)", the f_cp/2 Nyquist bound, the
footnote naming MN3007/MN3207 as 1024-stage variants, the third-order
anti-alias plus third-and-second-order reconstruction Sallen–Key norm, the
"between 1/3 and 1/2 of the sampling frequency" cutoff rule, THD =
1.01^(N/1024) − 1 as a distortion that "does not vary greatly depending on
the signal level—in other words, it is not a clipping distortion" and is
"typically left out" for choruses,
and that companders are "not typically used" in short-delay circuits. **S5**
gave 1024 PMOS stages, a 10–100 kHz clock range, 5.12–51.2 ms of delay, S/N
80 dB and THD 0.5 % typical, and the two-phase clock requirement. **S6**'s text layer holds only the header and the legal
boilerplate, so its pages were extracted as images and read: §1 "Astable Mode
Design Information" gives t_A = 2(t₁+t₂) with "Typ: V_TR = 0.5 V_DD, **t_A =
4.40 RC**" (and 4.62 RC at the 33 %/67 % transfer-voltage extremes), and Fig.
32 "Astable mode waveforms" draws terminal 13 at t₁,t₂,t₁,t₂ against terminal
10 at t_A/2, t_A/2 — so t_A is the period at terminals 10/11 and pin 13 runs
at twice it, which PDF page 2's "CD4047B FUNCTIONAL TERMINAL CONNECTIONS"
table states outright: "t_A (10,11) = 4.40 RC", "t_A (13) = 2.20 RC". That
same table's note places C on pin 1, R on pin 2 and
R-C COMMON on pin 3 (hence "R across 2–3, C across 1–3"), and names pins 10/11
Q and Q̄ ("IN ALL CASES EXTERNAL RESISTOR BETWEEN TERMINALS 2 AND 3,
EXTERNAL CAPACITOR BETWEEN TERMINALS 1 AND 3"; the block diagram draws
C-TIMING 1, R-TIMING 2, RC COMMON 3, OSCILLATOR OUT 13 and a ÷2 divider to
Q 10 / Q̄ 11). PDF page 7 adds the design range "C ≥ 100 pF, up to any
practical value, for astable modes" and "10 kΩ ≤ R ≤ 1 MΩ" — recommended "to
maintain agreement with previously calculated formulas without trimming",
after the same page states there is "no upper or lower limit for either R or C
value to maintain oscillation". **S7** gave the CE-2's triangle LFO on the MN3101 clock
("This simple circuit provides a variable frequency triangular waveform whose
amplitude is also variable"), its ±15 dB emphasis pair with the corner
computed at "2.341 KHz", and "To create the chorus effect a delay from 5 to
40ms is needed". **S8** gave EHX's own spec block — "Circuit Analog / Bypass
True Bypass / Audio Mono / Current Draw 12mA / Year Released 2000" — and the
panel text "DEPTH SWITCH: Controls the amount of frequency change that occurs
in the altered signal" and "RATE KNOB: Controls the rate of alteration
between raising and lowering the frequency".

### G. Licence notices as read

S1's page footer: "Trademarks and brands are the property of their respective
owners. Any usage of trademarks on this website is for comparative purposes
only, intended under fair use, and is not endorsed by the trademark holders";
no licence granted on the web page. **Audit correction:** the first draft
said the build-doc PDF "carries no rights line (searched)"; it does — page 13
is headed "LICENSE & USAGE" and reads "Projects may be used for commercial
endeavors in any quantity unless specifically noted. No attribution is
necessary, though a link back is always greatly appreciated. The only usage
restrictions are that (1) you cannot resell the PCB as part of a kit without
prior arrangement, and (2) you cannot 'goop' the circuit, scratch off the
screenprint, or otherwise obfuscate the circuit to disguise its source." That
is a **grant**, not a silence, and it is more permissive than the seed
claimed; the treatment is unchanged, because this dossier reproduces nothing
and there is no code here to take. (The same page's revision log — "Changed
recommendation for IC3 to LM358 as used in the original" — independently
corroborates §1's LM358.) S2's page body shows no notice, but the site footer reads
"Copyright © 2010-23, tagboardeffects." — all rights reserved by default, no
licence granted. S3's host page: "Trademarks are the property of
their respective owners…Copyright © 2023 All rights reserved", layouts "for
the hobbyist (so commercial use of any of these layout is not allowed without
permission)"; the image itself is hosted at guitar-gear.ru, whose own site
footer reads "© 2009 - 2026 Guitar Gear" — a bare copyright with no licence
granted (checked this run at the site root, the pattern
`agent-knowledge/instrument-sources.md` records for footer-only terms). S5's mirror footer: "An unofficial, non-commercial backup of
ElectroSmash.com, preserved by MAS Effects from the Internet Archive. All
content and images belong to their original authors/owners" — ElectroSmash's
own rights page could not be fetched (its host does not resolve). S7, same
mirror, page footer: "Some Rights Reserved, you are free to copy, share, remix
and use all material." S4 carries no rights statement anywhere in the PDF.
S6: "Data sheet acquired from Harris Semiconductor / SCHS044C − Revised
September 2003 / Copyright © 2003, Texas Instruments Incorporated." S8's
footer: "© 2026 Electro-Harmonix. All Rights Reserved." Every one of these is
read as a document or as facts; nothing is reproduced and no code was taken.
Where a source states no terms at all — S4's PDF alone, of the eight — the
call is **licence unverified, treated as copyleft** under vision §5: measured
or read, never a structure to copy. Every other source either grants nothing
explicitly (S1, S2, S3, the guitar-gear.ru host, S8) or is read for published
facts (S5, S6), and none is a structure to copy either.

*Audit, 2026-09-06.* Every source row above and every URL in this file was
re-fetched independently on 2026-09-06 (curl from this machine; the two PDFs
and the CD4047B scan re-extracted, the `gif.latex` formula image re-rendered
and re-read). All eight resolved and carried what this dossier says they
carry; the licence text of each was re-read at its own URL. Corrections made
by that pass are marked in place: **S1's licence call** (the build doc has a
LICENSE & USAGE page and grants commercial use — the seed had recorded silence
where there is a grant), the S3 image host's terms, App. B's Nyquist ratio,
App. D's diode attribution, App. F's TI page references and the paraphrase of
S4's THD statement, and App. F's completed EHX quotation. The
three not-reached claims were re-probed and all three stand:
`www.electrosmash.com` does not resolve (`Could not resolve host`), and both
`diystompboxes.com` Small Clone threads return HTTP 403.

### H. The measurements, specified

- **M1 (T1).** Impulse into the class, wet-only, Depth 0; count arrivals above
  −60 dB over 2 s, at 48 kHz and 44.1 kHz. *Planted fault:* set feedback to
  0.3 — a train must appear and M1 must go red.
- **M2 (T2).** A 1 kHz sine, wet-only, rendered over ≥4 LFO periods; take the
  instantaneous frequency by STFT phase derivative and, separately, the delay
  trajectory from an impulse train at the same settings. Report the
  within-half sweep ratio. *Planted fault:* drive the delay from a linear
  triangle instead of the table — the ratio must collapse to 1.0.
- **M3 (T3).** Swept sine at 48 kHz, wet-only and dry-only renders, third-
  octave magnitude ratio, Depth 0, **the delay set to a whole number of samples
  and the fractional part reported with the result** (App. I). *Planted fault:*
  set `damping_hz` above Nyquist — the ratio must go flat and M3 must go red.
  *Control that must pass:* the same render at fraction 0 with `damping_hz`
  in place, so a red M3 cannot be the interpolator.
- **M4 (T4).** Wet-only and dry-only RMS at the faithful patch, band-limited
  100–500 Hz where T3's filter is flat. *Planted fault:* halve the wet gain.
- **M5 (T5).** LFO period extracted from the delay trajectory at both Rate
  extremes. *Planted fault:* double `wow_hz`.
- **M6 (T6).** Delay trajectory over ≥8 LFO periods from an impulse train;
  FFT; report the second harmonic's **magnitude relative to the fundamental and
  its phase**, and the m the trajectory implies. *Planted fault:* run the node
  on its internal additive sine (no `wow_shape`) — the second harmonic must
  vanish into the noise floor and M6 must go red. *Control that must pass:* the
  shape table at m = 0, where fundamental and second harmonic are both absent
  and the measurement must report "no modulation", not "agreement".

Every measurement takes the sample rate as a parameter and records it in what
it exports (roadmap Phase 0, kit spec).

### I. The trait critic's arithmetic and probes, 2026-09-06

Everything here was computed or measured **in this run** — the probes on the
repository's CPython build of audioif (`audiocomponents/.venv/bin/python`), the
arithmetic in plain CPython. No source supplies these numbers; they constrain
how the traits above may be *measured*, not what the circuit does.

**1. The node's interpolated read is itself a low-pass.**
`audioif_feedback_delay.c:227-228` is a linear interpolation between two
neighbours, whose magnitude response at a fractional delay of half a sample is
cos(π·f/f_s). Measured wet-only, `feedback=0`, `mix=2.0`, no damping, level
referred to 1 kHz:

| f_s | delay | fraction | 10 kHz | 17 kHz |
|---|---|---|---|---|
| 48 000 | 4.000 ms (192.000 samples) | 0.000 | 0.00 dB | 0.00 dB |
| 48 000 | 4.01042 ms (192.5) | 0.500 | −1.99 dB (theory −2.01) | −7.07 dB (theory −7.09) |
| 44 100 | 4.000 ms (176.400) | 0.400 | −2.27 dB | −7.97 dB |
| 44 100 | 4.00227 ms (176.5) | 0.500 | −2.40 dB (theory −2.42) | −9.05 dB (theory −9.07) |
| 22 050 | 8.77551 ms (193.5) | 0.500 | **−16.65 dB** (theory −16.74) | above Nyquist |

Measurement and theory agree within 0.1 dB. **Control that passes:** the
fraction-0 row, where the loss is exactly zero — without it a run of losses
would only prove the probe always finds one. The first attempt at this probe
set `delay_ms` as an *attribute*, which the CPython shim ignores (options go
through the constructor or `set()`), and every row came back +0.00 dB: absence
reading as agreement, caught by the impulse control below.

**2. The impulse control.** Impulse at index 10, 48 kHz, mono: `mix=2.0`,
`delay_ms=4.0` → a single arrival at index 202 (192 samples); `delay_ms=4.005`
→ 15200/4800 split across 202/203; `mix=1.0` → arrivals at both 10 and 202.
This reproduces App. D's probe and is what proves the node was actually in the
path.

**3. Why T2 needs a swing floor.** For d = d₀/(1 + m·u) with u a unit triangle,
|d′| on each half is proportional to 1/(1 + m·u)², so the within-half ratio is
((1+m)/(1−m))² = (d_max/d_min)². T2's ±20 % window has to exclude the
delay-linear law's 1.0:

| swing d_max/d_min | predicted ratio | ±20 % window | excludes 1.0? |
|---|---|---|---|
| 1.10 | 1.21 | 0.97–1.45 | **no** |
| 1.25 | 1.56 | 1.25–1.88 | yes |
| 1.86 (m = 0.30) | 3.45 | 2.76–4.14 | yes |

Hence the "measured swing ≥ 1.25" condition in the row.

**4. The second harmonic, T6's number.** FFT of one period of
1/(1 + m·u), u the unit triangle, 4096 points:

| m | 2nd/1st | m/2 | 3rd/1st |
|---|---|---|---|
| 0.1225 | 0.0614 (−24.2 dB) | 0.0613 | 0.115 |
| 0.35 | 0.180 (−14.9 dB) | 0.175 | 0.142 |

A *delay-linear* triangle gives second/first = 0.000 and third/first = 1/9
(−19.08 dB). So the **second** harmonic separates the two laws cleanly and the
third does not — which is why T6 is stated on the second and `Vibrato` T4,
which is about the LFO's own shape, is stated on the third.

### J. Palette verification, 2026-09-06

Run by the unit's palette verifier against the CPython build of audioif in
`audiocomponents/.venv` (`audioecho`, `audiodelays`, `audiocore`), sources
read with `grep -n` in `audioif/src/shared/` and `audioif/src/audioecho/`.
Nothing here is arithmetic about the node; every number came out of a render.

**Probes.** (a) *Impulse* — one full-scale stereo impulse into a
`FeedbackDelay` at `feedback=0`, arrivals read out of the rendered block.
(b) *Steady sine* — RMS of the wet path against an unfiltered reference node
at the same delay, 24000 frames after a 4096-frame skip. (c) *Trajectory* —
an impulse every 1024 frames, the delay recovered per impulse as the
amplitude centroid of the two-sample interpolated arrival, then fitted for
its mean, fundamental and second harmonic. The trajectory probe's own floor
is −28 dB relative to the fundamental (measured on a node whose modulation
has no second harmonic by construction), which is what a "no harmonic"
reading below means.

**Fractional read.** `delay_ms=4.0` at 48 kHz: one arrival, frame 192, full
amplitude. `delay_ms=4.005`: 15200 at frame 192 and 4800 at 193 — the linear
interpolation of `audioif_feedback_delay.c:227-228`, exactly.

**The wow oscillator is a per-sample sine on the delay.** `delay_ms=8`,
`wow_hz=2`, `wow_depth_ms=2`: over 23 recovered points the trajectory matched
`384 + 96·sin(2π·2·t/fs)` frames, evaluated at the arrival, to a maximum
error of **0.047 frames**. That is `:212-213` and nothing else.

**`mix`.**

| `mix` | dry | wet | wet/dry |
|---|---|---|---|
| 0.000 | 1.000 | 0.000 | wire |
| 0.500 | 1.000 | 0.500 | 0.5000 |
| 0.815 | 1.000 | 0.815 | 0.8150 |
| 1.000 | 1.000 | 1.000 | 1.0000 |
| 1.100 | 0.900 | 1.000 | 1.1111 |
| 2.000 | 0.000 | 1.000 | wet alone |

**The one-pole low-pass: nominal `damping_hz` against the frequency it puts
3 dB down**, 48 kHz, from the closed form of `y += a(x − y)` with
`a = 1 − exp(−2π·f/fs)` (`audioif_feedback_delay.c:29-38`), each spot-checked
against a rendered sine.

| nominal | actual −3 dB |
|---|---|
| 500 Hz | 500.2 Hz |
| 1 kHz | 1.001 kHz |
| 3 kHz | 3.039 kHz |
| 5 kHz | 5.189 kHz |
| 8 kHz | 8.859 kHz |
| 12 kHz | 16.08 kHz |
| 13.46 kHz | 23.47 kHz |
| ≥13.47 kHz | never, below Nyquist |

Rendered wet/dry at nominal 3 kHz, delay 8 ms (a whole number of samples):
100 Hz +0.01, 200 Hz 0.00, 500 Hz −0.10, 1 kHz −0.43, 2 kHz −1.55,
5 kHz −5.60, **10 kHz −10.19 dB**, all relative to the 200 Hz value.

**The primed cascade.** `set()` reaches only `audioif_feedback_delay_configure`
(`audioecho/FeedbackDelay.c:32-58`, `:135-141`), which writes config; the
oscillator state is initialised at construction and at `reset_buffer`
(`:200-211`) and nowhere else. Holding a node at `wow_hz = 0` therefore
freezes `wow_sine`/`wow_cosine` (`audioif_feedback_delay.c:209-210` multiply
by a zero `wow_step`) and advances its phase relative to a sibling by one
block per block held — 5.33 ms, 256 frames (`audioif_feedback_delay.h:39`).
Demonstrated on a single node: freezing 0, 8, 16 and 24 blocks moved the
trajectory's phase by 0°, 31°, 61° and 92°. Applied to a cascade at
d₀ = 8 ms, m = 0.30, f = 5 Hz — where the law `d₀/(1+m·sin θ)` wants a
fundamental of 2.40 ms and a second harmonic of 0.36 ms (−16.5 dB) in
quadrature — a single node measured **|A1| 115.6 frames, |A2| −28.2 dB**
(the floor), and the primed two-node cascade at 5 Hz and 10 Hz measured
**|A1| 115.8 frames, |A2| −14.6 dB at −87.8°**. The cascade reaches a
quadrature second harmonic; it does not reach a triangle.

**`audiodelays.Chorus`, impulse at `delay_ms=20`, `mix=1.0`, `max_delay_ms=40`:**
`voices=1` → one arrival, frame 0, the dry (`audioif_chorus.c:15-16`);
`voices=2` → frames 0 and 960; `voices=3` → frames 0, 480 and 959 — whole
samples, evenly spaced, no interpolation (`:18`, `:22`). `delay_ms` is read
once per `_process` call (`audioif/src/cpython/audiodelays.py:75`), which is
the block-rate stepping §7 names.

**Other palette paths checked and rejected for T2/T6.**
`audiodelays.Echo` reads whole samples in both its modes
(`audioif_echo.c:20`, `:30`) and interpolates nowhere;
`audiodelays.MultiTapDelay`'s taps are integer offsets
(`audioif_multitap.c:20-23`); `audiomath.Multiply` multiplies two audio
streams (`audioif_multiply.c:32-39`) and cannot reach a delay time at all —
no `FeedbackDelay` option is a stream input, they are all floats
(`audioecho/FeedbackDelay.c:19-30`).

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

*Rate note.* T1, T2, T4, T5 and T6 hold at 44.1 kHz and 22.05 kHz.
**T3 is stated at 48 kHz and 44.1 kHz only.** The node's interpolated read is
itself a low-pass — magnitude cos(π·f/f_s) at a half-sample fractional delay —
measured this run on the CPython build at **−16.65 dB at 10 kHz at 22.05 kHz**
against −1.99 dB at 48 kHz and −2.40 dB at 44.1 kHz (App. I), so at 22.05 kHz
T3's ≥10 dB criterion is met by the interpolator alone whatever the wet filter
does. The Tone macro's Hz value clamps below Nyquist at every rate.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | Licence call |
|---|---|
| **S1** Aion FX, *Lithium Analog Chorus* ([page](https://aionfx.com/project/lithium-analog-chorus/), [build-doc PDF](https://aionfx.com/app/files/docs/lithium_documentation.pdf)) — a schematic with every value, of Aion's own *adaptation*; its build notes give the original's values where the two differ (App. D) | the build doc's own **"LICENSE & USAGE"** page grants use "for commercial endeavors in any quantity", no attribution required, restricted only against reselling the PCB in a kit and against obfuscating the circuit's source → document, read only anyway (nothing is reproduced and no code exists to take) |
| **S2** [Guitar FX Layouts, *EHX Small Clone*](https://tagboardeffects.blogspot.com/2014/06/ehx-small-clone.html) — a vero layout; its IC complement, its 150 pF clock cap and one builder's **measured** LFO rate are all in the comment thread, not the body (App. E, F) | site footer "Copyright © 2010-23, tagboardeffects." → document, read only |
| **S3** A second Small Clone drawing ([page](http://effectslayouts.blogspot.com/2022/09/ehx-small-clone.html), [image](http://guitar-gear.ru/wp-content/uploads/2016/04/Small-Clone.jpg)) — titled "Schematic (**Depth pot mod included**)", drawn to reissue values; agrees with S1 on **every value checked** (App. D) | page "All rights reserved", hobbyist use → document, read only; the image host asserts a bare site-wide copyright ("© 2009 - 2026 Guitar Gear") and grants nothing → **no licence granted, treated as copyleft** |
| **S4** [Raffel & Smith, *Practical Modeling of Bucket-Brigade Device Circuits*, DAFx-10, CCRMA](https://colinraffel.com/publications/dafx2010practical.pdf) — the BBD delay law, the filter norms, the BBD nonlinearity | **no rights statement anywhere in the PDF** (searched this run) → **licence unverified, treated as copyleft**: read as a paper, no code taken |
| **S5** [ElectroSmash, *BBDs: MN3007*](https://electrosmash.mas-effects.com/mn3007-bucket-brigade-devices) — the part's stages, clock span, delay span, and the delay law (set as an image; downloaded and read, App. C) | unofficial non-commercial mirror, "All content and images belong to their original authors/owners" → document, read only |
| **S6** [TI *CD4047B* data sheet](https://www.ti.com/lit/ds/symlink/cd4047b.pdf), SCHS044C — the astable timing law and pinout; the body is a scan, read by extracting the page images (App. F) | "Copyright © 2003, Texas Instruments Incorporated" → facts from a data sheet |
| **S7** [ElectroSmash, *Boss CE-2 Analysis*](https://electrosmash.mas-effects.com/boss-ce-2-analysis.html) — the sibling BBD chorus | "Some Rights Reserved, you are free to copy, share, remix and use all material" |
| **S8** [Electro-Harmonix, *Small Clone*](https://www.ehx.com/products/small-clone/) — the **maker's** own spec block and panel text for the reissue, including "DEPTH SWITCH" (App. F). 403 to WebFetch, HTTP 200 to curl | "© 2026 Electro-Harmonix. All Rights Reserved." → facts from a maker's page |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **One delayed voice, and only one** — one line, one tap, no regeneration. An impulse at the faithful patch, wet-only, Depth 0: after the first arrival's peak sample, no later sample within 2 s exceeds −60 dB of that peak. | S1, re-read this run: the complete parts list and the usage page ("The Lithium has three controls" — Rate, Depth, Mix), with no feedback element and no repeats control; S3 (App. D) | high | A second arrival above −60 dB of the first, or a decaying train | M1 |
| T3 | **The wet voice is far darker than the dry, and darker than anti-aliasing requires.** At Depth 0, 48 kHz, with the delay set to a whole number of samples: the wet/dry third-octave magnitude ratio is within 1 dB of its 200 Hz value at every band centre below 500 Hz, falls monotonically from band centre to band centre between 1 kHz and 10 kHz, and at 10 kHz is at least 10 dB below its 200 Hz value. | S1's parts list, re-read this run for all six reconstruction and six anti-alias values (App. D), S3; S4 §2.2 for the norm this circuit does *not* follow | high | A ratio within ±1 dB from 100 Hz to 10 kHz, or less than 10 dB below its 200 Hz value at 10 kHz | M3 |
| T4 | **Wet and dry are summed at near-equal level, not as a polite wet trim** — there is no wet-level control on the pedal at all. Band-limited RMS over 100–500 Hz, where the reconstruction filter is flat: wet/dry 0.815 (−1.8 dB) at the vintage 27k and 1.10 (+0.8 dB) at the reissue 20k, against a fixed 22k dry. | S1's parts list and build notes, re-read this run: R5 22k, R24 20k, and "the vintage Small Clone used a 27k resistor for R24, while the 2002 reissue reduced this to 20k"; S3; App. A | high | Either patch's measured ratio more than 2.5 dB from its drawn value — vintage outside 0.61–1.09, reissue outside 0.82–1.47 | M4 |
| T5 | **Rate spans 0.43 Hz to 9.5 Hz across the knob's travel — a 22:1 range.** f = R28/(4·R27·R·C14) with R = R26 + the Rate pot (47k…1.047 MΩ) gives 9.47 Hz and 0.425 Hz. | S1's parts list, re-read this run (R26 47k, R27 120k, R28 470k, C14 2.2 µF, RATE 1MC), S3; App. A. S2's comment thread, re-fetched this run (HTTP 200), carries a builder's "9.0 Hz with rate all the way up" — 5 % from the drawn 9.47 Hz (App. E) | medium — C-taper pot, asymmetric single-supply swing; the corroborating reading is a hobby build, not a factory unit | A measured LFO fundamental outside 0.3–12 Hz at either macro extreme, or a span between the extremes under 10:1 | M5 |
| T6 | **The clock is modulated, not the delay** — the discriminator §5's node ask turns on. The delay trajectory carries a **second harmonic at m/2 of its fundamental, in quadrature with it**, m being the clock swing the same run measures; a delay driven by an additive LFO carries no second harmonic at all. At m = 0.1225 that is −24.2 dB and at m = 0.35 it is −14.9 dB (App. I). | S1, S3 (the LFO drives the 4047's timing node), S4 §2.1 | high for the mechanism; medium for m, which the class's Depth law sets and the measurement reports | No second harmonic above the trajectory's noise floor at any Depth, or one more than 6 dB from m/2 at the m the same run measures, or one in phase rather than quadrature with the fundamental | M6 |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Standout confirmed.** Vision §4.2's clause — "one BBD voice, triangle LFO,
Rate knob and a two-position Depth switch that becomes a knob" — is what S1
and S3 draw, independently hosted and separately drawn, and **the maker's own
page still calls it a Depth switch** (S8). Neither drawing is EHX's factory
schematic and each carries a modification (App. D); the values used here are
the ones both agree on. No swap.

*(from §2)*

**Not reached:** `www.electrosmash.com` (re-confirmed: does not resolve, so the
mirror is used and ElectroSmash's own rights page could not be read);
`diystompboxes.com` Small Clone threads (403, twice, re-confirmed). `ehx.com`
**was** reached (S8) and carries no delay, clock or LFO figure, so it fixes no
Tier 2 value. **No factory or laboratory measurement of a unit was found**, so
App. B is arithmetic, never a capture; the one measurement reached is a
builder's, in S2's comments, and it corroborates T5's fast end (App. E).

*(from §3)*

*Which sources this trait-critic pass re-reached for itself (2026-09-06):* **S1**
(build doc, HTTP 200, md5 `997dd44c…` — parts list, build notes, schematic text
layer and the LICENSE & USAGE page), **S2** (HTTP 200, the builder's 9.0 Hz
comment), **S4** (HTTP 200, md5 `316a6848…`, every sentence quoted from it
re-searched), **S6** (HTTP 200, md5 `6201cfd4…`, identity confirmed; its 4.40·RC
figure was *not* re-read from the page images, so no row above rests on it).
**Carried from the seed run and not re-reached here:** S3, S5, S7, S8. Every row
above rests on at least one source this pass read for itself.

*(from §3)*

**Latency: zero.** Nothing looks ahead; the dry path is the node's
`dry * source` term from the current frame (`audioif_feedback_delay.c:261`),
so a click through the class and through the wire coincide to the sample. The
8–13 ms mean delay (App. B — **derived from drawn values, never measured**) is
on the **wet** path and is the effect, not latency
(vision §9a). No option adds latency — no lookahead, no partition, no pitch
window; line length is memory, not delay. `latency_samples` is 0 at every
macro setting and patch.

*(from §4)*

**Deliberately not modelled: the pre/de-emphasis pair.** It exists to push the
brigade's noise 15 dB down and **cancels exactly** in the audio path (App. A);
a digital line gains nothing but two filters and their rounding. What does
*not* cancel — the reconstruction filter, wet-path only — is `damping_hz`.

*(from §4)*

**Portability tier: audioif**; on a stock board the module imports and
construction raises a clear `ImportError` (`drive.py:30-33`/`:331-334`). The
stock alternative is refuted: `audiodelays.Chorus` reads whole-sample taps
with no interpolation (`audioif_chorus.c:22`) at fixed integer spacing
(`:18`), moves them once per block, and **with `voices=1` emits no delayed
voice at all** (`:15-16`; measured, §7) — T1 alone rules it out.

*(from §4)*

**Palette verification (2026-09-06; probes and numbers in App. J).** Three
things the first draft stated loosely, each now measured against the node.
**`damping_hz` is the node's one-pole *coefficient* argument, not a −3 dB
point** (`:29-38`), and the two diverge above about a quarter of the rate: at
48 kHz nominal 3 kHz lands at 3.04 kHz, nominal 12 kHz at 16.1 kHz, and no
nominal above ≈13.46 kHz reaches −3 dB below Nyquist at all — so the Tone
macro states the corner and Python pre-warps, the move the class already makes
for `audiofilters.Phaser`'s `frequency` (vision §6). **T3 is reachable and
thin:** at the drawn 3 kHz the wet is 10.19 dB down at 10 kHz relative to
200 Hz, monotone from band to band, against a ≥10 dB bar — so the faithful
Tone is set from T3's criterion, not the reverse. **T4's reissue ratio costs
the dry path 0.9 dB:** `mix` ≤ 1 leaves the dry at unity and makes wet/dry
exactly `mix` (0.815 → 0.8150 measured), but above 1 the node attenuates the
dry (`mix = 1.10` → dry 0.900, wet 1.000, ratio 1.1111), which Tier 1's
level-honesty has to answer — §8.7, a design choice and not a node ask.

*(from §4)*

**Mono and stereo.** A mono source gets the mono chorus; a stereo source gets
the same delay and modulation on both channels, since the node runs two lanes
from one oscillator (`:209-213` is outside the channel loop). That is
faithful, not a limitation. Width's non-zero settings are explicitly *not* the
circuit and need a second node (§8.4).

*(from §5)*

- **Trait it unblocks:** T2 and **T6** (and `Vibrato`'s **T7** — one ask serves
  all three and is filed once). It does **not** unblock `Vibrato` T4: a
  smoothness test is passed by the node's own additive sine, and the seed that
  claimed otherwise is corrected in `Vibrato` §5.

*(from §5)*

- **What the palette does instead:** the kernel adds
  `wow_depth_frames * wow_sine` to the delay (`:212-213`) — an additive
  **sine on the delay**, where the circuit puts a **triangle on the clock**.
  The palette's trajectory is missing every harmonic above the first; at
  m = 0.3 the second alone is ≈15 % of the fundamental and is in
  **quadrature** (App. C).

*(from §5)*

- **Refutation record.** (1) *Step `delay_ms` from Python*: a config write
  with no slew (`:82-83`, read unsmoothed at `:212`) — one jump per 256-frame
  block (`audioif_feedback_delay.h:39`), several samples wide at musical
  depths; that is the defect being rebuilt away from (§7). (2) *Cascade two
  nodes at f and 2f.* **The first draft said the required cosine term cannot
  be produced; that is wrong, and is corrected here.** `set()` writes config
  only and never touches the oscillator state
  (`audioecho/FeedbackDelay.c:32-58`, `:135-141`; `state_init` runs at
  construction and at `reset_buffer` alone,
  `audioecho/FeedbackDelay.c:200-211`), so holding a node at
  `wow_hz = 0` freezes its phase and primes it in 5.33 ms steps. Measured: a
  primed two-node cascade at 5 Hz/10 Hz put a second harmonic 14.6 dB below
  the fundamental at **−87.8°, in quadrature** (App. J). What no practical
  cascade reaches is **T2**: the Small Clone's LFO is a *triangle* and the
  node's oscillator is a pure sine, so one node carries none of the
  triangle's odd harmonics, and T2's within-half ramp is a statement about
  the whole half-cycle's shape rather than about one harmonic. Under a sine the
  instantaneous offset goes as \|cos θ\|, which reaches zero inside every half,
  so the within-half ratio is arbitrarily large — neither the linear law's 1.0
  nor the reciprocal's (d_max/d_min)². **T2 is what carries this ask; T6 alone
  would not.** The cascade also doubles line memory and the interpolated
  read, and its prime is a startup ritual every `reset()` destroys, which
  Tier 1 forbids depending on.

*(from §5)*

- **The ask, additive:** an optional `wow_shape` — a one-period table (int16,
  power-of-two length, computed on CPython, shipped as data) read in place of
  the internal sine at `:212-213`, `wow_hz` still setting the period and
  `wow_depth_ms` the amplitude. One detail the issue must carry: today's
  oscillator is a magic-circle pair whose state is a sine and a cosine
  (`:163-164`, stepped at `:209-210`) and whose rate is
  `2·sin(π·f/fs)` (`:113-114`), which has no index to look a table up with —
  so the shaped path needs its own phase accumulator alongside, advanced from
  the same `wow_hz`. Absent a shape, the node behaves exactly as today.
  Additive on an audioif-own module (D1); no ported node touched.

*(from §5)*

- **Measurement that shows the gap:** T6's probe against a `FeedbackDelay` at
  the correct mean and depth — the additive sine puts **no** second harmonic in
  the trajectory, where the modelled law's is m/2 of the fundamental (−24.2 dB
  at m = 0.1225, App. I). Measured this run at m = 0.30, where the law's
  second harmonic is −16.5 dB: a single node's recovered trajectory carried
  one at −28.2 dB, which is the impulse-centroid probe's own floor rather
  than a real harmonic (App. J). T2's within-half ramp is the second,
  independent reading of the same gap, and the one no cascade closes.
