# Effects Dossier — `Saturation` (a triode stage, a tape machine, console iron — three characters)

**Class:** `lib/audioeffects/drive.py` — read once, for §7.
**Family / phase:** Drive, roadmap Phase 4
**Standout:** vision §4.2 names three mediums rather than one pedal, and this
run **confirms all three** and pins a referent to each, because "tube" and
"tape" are not circuits until someone says which: `tube` is a **12AX7
common-cathode gain stage** (S1's netlist topology, S2's measured device
parameters); `tape` is a **reel-to-reel record → tape → playback chain**
(S3's model of a Sony TC-260); `console` is **a signal transformer with a
ferromagnetic core** (S4, and — added by the Phase 0 audit — S5). One honest correction to the
vision's wording: no mixing-desk schematic was reached, so the third character
is *iron* rather than any named desk (§8 Q3). It is no longer iron *in
general*, though: the audit reached measurements of two named transformers, a
Fender NSC041318 and the Hammond T1750V of the Vox AC30 (S5).
**Grade:** literature — no product schematic with values for tape or iron;
the triode has a published topology with values (S1) and a device model fitted
to measurements of real tubes (S2), and iron now has measurements of two named
transformers (S5, added by the audit). Every trait below is derived
analytically **this run** from those papers' own equations (Appendix A1–A3),
which is what lifts this above a reading of secondary sources.
**Portability tier:** needs audioif-own nodes (the §5 waveshaper; the
hysteresis state it asks for, if Phase 1 grants it)
**Status:** seed (Phase 0), 2026-09-06. Levels use the drive family's
convention (`Overdrive` §8): **0 dBFS ≡ 1.0 V peak at the jack**.

## 1. The circuit, in one paragraph

**`tube`.** A triode common-cathode stage — grid through a series resistor,
cathode to ground through a bypassed bias resistor, plate to the supply
through a load resistor, output at the plate; S1's netlist is Rp 100 kΩ,
Rk 1.5 kΩ, Ck 25 µF, Rg 70 kΩ, Vpp 250 V, and S2 calls the same stage one
"found in almost all preamplifiers designs". The nonlinearity is the tube's
own two currents: below cutoff the cathode current follows a power law in the
effective voltage Vg + Va/µ (S2 eqs 5, 10), and as the grid approaches and
passes zero volts the grid itself draws current (S2 eq 11), loading the source
and stealing current from the plate — S2 notes
that textbooks skip that region and guitar amplifiers have lived in it since
the 1960s. *(Audit correction: S2's eq 11 is a softplus in Vg plus a constant
Ig₀, and its own measurement has the grid current already rising exponentially
from small **negative** grid volts — small below zero, not zero. The mechanism
and the polarity stand; the first draft's hard switch at zero does not.)* The two limits are therefore *different mechanisms on different
polarities*, plate cutoff one way and grid conduction the other, which makes
a triode's asymmetry structural rather than a mismatch. Solved this run with
S2's parameters for a real 12AX7 (A1): Vk 1.23 V, plate 167.9 V, gain −65.6×
(36.3 dB), 82.1 V of room toward the supply against 166.7 V the other way.

**`tape`.** Record-head current makes a field, the field magnetises the tape
along a hysteresis loop (S3 eq 6, Jiles-Atherton, whose saturating part is
the Langevin function of the effective field), and the playback head reads it
back through three frequency-dependent losses — spacing, thickness and gap —
which S3 gives in closed form as `e^{-kd}·(1−e^{-kδ})/(kδ)·sinc(kg/2)` with
`k = 2πf/v` (eqs 13–14). Every term depends on frequency *only* through `k`,
so the response is a function of wavelength and slides exactly with tape
speed. A recorder also adds a high-frequency bias current an order of
magnitude above the signal, "to avoid the deadzone effect when the input
signal crosses zero, as well as to linearize the output" (S3) — 55 kHz on the
TC-260, recovered by a 24 kHz low-pass. The medium's memory is the loop:
magnetisation depends on which way the field is moving (S3 eqs 7–8).

**`console`.** A signal transformer's core follows the same Jiles-Atherton
loop (S4). What makes iron different from tape is *what drives the core*:
flux is the integral of the winding voltage, so at a fixed input level the
peak flux is inversely proportional to frequency and the core saturates from
the bottom up. S4 demonstrates exactly that on a simplified output-transformer
stage — at 5 V amplitude "for high frequencies f, as shown in Figure 7a for
f = 1 kHz, the circuit almost perfectly achieves the voltage scaling by
n2/n1 = 1/10", while "for lower frequencies like f = 100 Hz … the saturation
of the core yields a very non-linear behavior". S5 measures the same thing on
real iron and states the mechanism in the same terms — its two case studies
"introduce distortion at low frequencies only, below about 100 Hz for the
Fender and 30 Hz for the Hammond transformer", because "for the same input
voltage, the magnetic flux Φ is larger when the frequency is lower".

## 2. Sources and license calls

Every row below was **re-fetched and re-read in full by the Phase 0 licence
and citation audit on 2026-09-06** — each PDF downloaded again with `curl` and
extracted with `pypdf`, never read through a fetch-tool summary. The "Reached"
column records that pass; the corrections it forced are reported to Phase 0's
audit report (`effects-survey-audit.md`, not yet written).

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 D. T. Yeh, *Automated Physical Modeling of Nonlinear Audio Circuits … (App. S1) | the common-cathode netlist with values (`Rg 70e3 … (App. S1) | "Copyright (c) 2010 IEEE. Personal use of … (App. S1) | https://ccrma.stanford.edu/~dtyeh/papers/yeh12_taslp.pdf | yes — audit run 2026-09-06, HTTP 200, 10 pages extracted |
| S2 K. Dempwolf & U. Zölzer … (App. S2) | eqs (10)–(12) — Ik, Ig, Ia = Ik − Ig … (App. S2) | No licence statement in the PDF … (App. S2) | https://dafx.de/paper-archive/2011/Papers/76_e.pdf | yes — audit run 2026-09-06, HTTP 200, 8 pages extracted |
| S3 J. Chowdhury, *Real-Time Physical Modelling for Analog Tape … (App. S3) | Jiles-Atherton magnetisation (eqs 6–9) … (App. S3) | **CC BY 3.0 Unported**, stated in the paper … (App. S3) | https://www.dafx.de/paper-archive/2019/DAFx2019_paper_3.pdf | yes — audit run 2026-09-06, HTTP 200, 7 pages extracted |
| S4 M. Holters & U. Zölzer, *Circuit Simulation with Inductors and … (App. S4) | the JA model as a time-differential equation … (App. S4) | No licence statement in the PDF … (App. S4) | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2017/10/Holters_jamodel_DAFx16.pdf | yes — audit run 2026-09-06, HTTP 200, 6 pages extracted |
| **S5** R. C. D. Paiva, J. Pakarinen, V. Välimäki & M. Tikander … (App. S5) | measurements of two **named** transformers … (App. S5) | **Creative Commons Attribution License** … (App. S5) | https://aaltodoc.aalto.fi/handle/123456789/26495 → https://aaltodoc.aalto.fi/bitstreams/41199441-b13b-410f-9798-d904e4867d8c/download | yes — audit run 2026-09-06, HTTP 200, 3.06 MB, 16 pages extracted |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

Each character gets its own rows, so one that fails cannot hide behind one
that passes (vision §10.7). *Derived* = computed this run from the sources'
own equations; the scripts' outputs are in A1–A3.

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Each character gets its own rows. *Derived* = computed this run from the
sources' equations; the outputs are in A1–A3.

*Trait-critic pass, 2026-09-06:* ten rows, nine graded and one (**IR3**)
marked *unmeasured*. The record is under the Appendix.

Character **`tube`** (12AX7 common-cathode stage):

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| TU1 | **Even harmonics dominate below the clipping onset, on the power laws of a weak nonlinearity.** **Relative to the fundamental (dBc)** h2 rises **1.0 dB per dB** of input and h3 **2.0 dB per dB** — in absolute terms 2 and 3 dB/dB. The row is stated in dBc, so a measurement taken in absolute terms reads exactly one more and must not be scored against these numbers. h2 therefore leads h3 by 40 / 28 / 20 dB at 0.05 / 0.2 / 0.5 V peak grid drive (*derived*, A1). **"Below the onset" is 0.5 V peak grid drive:** by 1.0 V the lead has already collapsed to 5.5 dB, so the bar is claimed at or below 0.5 V and nowhere above it. Bar: **h2 − h3 ≥ 15 dB** at every drive ≤ 0.5 V, and h2 within **±4 dB** of A1 at the three tabulated drives | S1 (netlist and values) … (App. TU1) | high — two papers … (App. TU1) | h2 at or below h3 at any drive ≤ 0.5 V; h2's **dBc** slope outside 0.6–1.4 dB/dB across that span; h2 more than 4 dB from A1 at a tabulated drive | spectrum of a 1 kHz sine at 0.05 … (App. TU1) |
| TU2 | **Two different limits on the two polarities, and only one of them is a ceiling.** Plate cutoff pins the positive-going output excursion at the supply — **+82.06 V** above the 167.94 V idle, and no further however hard the stage is driven — while grid conduction on the other polarity merely compresses, so the negative-going excursion keeps growing. Bar: from the drive at which the positive peak first comes within 1 dB of that ceiling, a further **20 dB** of input grows the positive peak by **< 1 dB** and the negative peak by **> 1.5 dB**, and the smoothly-compressed side is the grid-conduction one | S1 — its netlist puts `Rg i2 g 70e3` **in … (App. TU2) | high for the … (App. TU2) | a positive peak that keeps growing past its ceiling — no hard cutoff limit — or a negative peak that stops growing with it, both sides limiting alike | ± output peak of the quasi-static … (App. TU2) |
| TU3 | **Gain and operating point are the character's, not a knob's:** inverting, **65.6× (36.3 dB)** small-signal, idling at Ia 0.821 mA, Vk 1.231 V, plate 167.94 V (*derived*, and reproduced to the digit by an independent solve this run). Bar: the **shipped table's** small-signal slope at its reference operating point — taken on the table, **before** the class's output level compensation, since macro 0 compensates level and a gain measured after it is a design choice rather than a measurement — within **±2 dB** of 36.3 dB, and the generator's printed DC solve within 5 % of those three values | S2's device parameters in S1's netlist. … (App. TU3) | **medium … (App. TU3) | small-signal slope outside 34.3–38.3 dB, or a DC solve more than 5 % from A1's Vk / Ia / plate | slope of the shipped table about … (App. TU3) |

Character **`tape`** (reel-to-reel chain):

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| TP1 | **Playback loss is a function of wavelength, so it slides exactly with speed.** All three terms depend on frequency only through `k = 2πf/v` (S3 eqs 13–14, re-read verbatim this run), so the 7.5 ips response equals the 15 ips response at twice the frequency **within 0.5 dB**, and the in-band loss is monotone. **Testable band, 20 Hz–12 kHz at 48 kHz:** the comparison needs the 15 ips curve at 2f, so any point above 12 kHz would need data past Nyquist — the first draft claimed 20 Hz–20 kHz, which cannot be measured at any supported rate. At 44.1 kHz the band is 20 Hz–11 kHz and at 22.05 kHz 20 Hz–5.5 kHz. **The gap null at v/g is not part of the bar:** it sits at 190.5 kHz at the class's geometry (76.2 kHz at S3's), so no audio sample rate reaches it, and it is checked on the design curve computed offline, never on rendered audio | S3 eqs 13–14. The A2 cross-check against … (App. TP1) | high — closed form | a speed control that changes level, or applies a shelf, instead of translating the curve; any point in the testable band where the two curves differ by more than 0.5 dB; non-monotone in-band loss | swept magnitude at 7.5 and 15 … (App. TP1) |
| TP2 | **The saturating curve is odd** (the Langevin anhysteretic, S3 eq 9), with `Bias` centred at 0. **The knee is defined operationally as the drive at which THD reaches 1 %**, located first by the THD-vs-drive sweep, so "below the knee" and "above it" are measurable rather than eyeballed. Bar: h2 and h4 **≤ −40 dBc**; h3 rises **2.0 ± 0.4 dB per dB in dBc** (3 dB/dB absolute — same convention note as TU1) over the 20 dB below the knee; and above it the output peak grows **< 3 dB** for a 20 dB input rise | S3 eqs 6–9 | high for the symmetry … (App. TP2) | h2 or h4 above −40 dBc with `Bias` centred; h3's dBc slope outside 1.6–2.4 dB/dB below the knee; the output peak still tracking the input to within 3 dB over the 20 dB above the knee | THD-vs-drive sweep to locate the … (App. TP2) |
| TP3 | **The medium has memory: the loop encloses area — and the area is the state variable's, not the filters'.** Magnetisation depends on the direction of travel (S3 eqs 6–8), so a slow triangle traces a loop whose area grows with drive. **Measured against a control, never against zero:** the same signal path with `Hysteresis` at 0 is a memoryless curve between the same first-order sections, and at 20 Hz those sections' own phase shift already encloses area, so "non-zero area" would be satisfied by a class with no hysteresis at all. Bar: at maximum drive the `Hysteresis` 1 loop's area exceeds the `Hysteresis` 0 control's by **≥ 6 dB**, and that excess grows monotonically with drive over three settings. The one trait the palette cannot reach (§5) | S3 eqs 6–8; **and S3's Figure 9 … (App. TP3) | high that the physics … (App. TP3) | the `Hysteresis` 1 loop's area within 6 dB of the `Hysteresis` 0 control's at maximum drive, or the excess not growing with drive | output-vs-input from a 20 Hz … (App. TP3) |

Character **`console`** (transformer iron), and one trait shared with every
drive class:

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| IR1 | **Saturation is flux-driven, so it starts at the bottom.** Peak flux is ∫v dt, so the input level that reaches **1 % THD** rises with frequency at **6.0 ± 1.5 dB per octave**, fitted by least squares in log-frequency over 50 / 100 / 200 / 400 / 800 Hz. **Precondition the rebuild must state and the measurement must check:** §4's flux low-pass is an integrator only well *above* its own corner, so that corner has to sit at least a decade below 50 Hz — otherwise the law flattens at the bottom of the band and the row fails for a modelling reason rather than a circuit one, which is a failure the evidence pack must be able to tell apart | S4 (the JA transformer stage: "for high … (App. IR1) | high — the flux law … (App. IR1) | a fitted slope outside 4.5–7.5 dB/octave; equal 1 % crossings at 100 Hz and 1 kHz; a knee that moves with level but not with frequency | THD-vs-level at 50 / 100 / 200 / … (App. IR1) |
| IR2 | **Odd by symmetry until the operating point moves.** At the drive IR1's sweep identifies as the 1 % THD crossing at 100 Hz: with `Bias` centred h2 is **≤ −40 dBc**; at `Bias` ±0.5, same drive and frequency, h2 is **≥ −25 dBc**. And `Bias` moves nothing else — the fundamental's level changes **< 1 dB** across that range, so it is an operating-point control and not a gain | S4 (the model; symmetric loops by … (App. IR2) | high for the … (App. IR2) | h2 above −40 dBc with `Bias` centred; h2 below −25 dBc at `Bias` ±0.5; or a fundamental level that moves ≥ 1 dB across the `Bias` range | spectrum at `Bias` −0.5 / 0 / … (App. IR2) |
| IR3 | **unmeasured: the cross-character ordering is fixed by a mapping this class chooses, so a rebuild cannot fail it.** "Iron is the gentlest of the three at matched drive" compares three different papers' circuits through the volts-to-dBFS mapping of §8 Q2 — the class's own free choice — so a rebuild that picks the mapping satisfies the ordering by construction, and no reached source compares the three mediums at a matched drive. The three-character THD-vs-drive plot at 1 kHz is still **produced and recorded** in the evidence pack as a voicing check; it carries no pass/fail bar. The sourced half of the old row lives in IR1, which is graded | S4, S5 — neither compares mediums … (App. IR3) | — | — | THD-vs-drive at 1 kHz … (App. IR3) |
| A4 | **Alias floor:** a 1010 Hz sine at −6 dBFS, any character at maximum drive, **on the shipped (non-lean) oversampling setting**: non-harmonic energy **≥ 60 dB** below the fundamental at 48 kHz. The drive family's shared bar. The setting is named because patch 7 "Lean" drops oversampling ×8 → ×2, and an unqualified row would either fail on the lean patch or let it hide | S1 (4–8×, verbatim this run: "typically 4 to … (App. A4) | medium — a design … (App. A4) | non-harmonic energy above −60 dB at either probe on the P4 or the ESP32-S3 build, at the shipped setting. **The lean patch is measured at the same probes and reported, not graded here** — §8 Q5 owns whether it must also meet −60 dB | non-harmonic bin sum vs the … (App. A4) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

```
tube:     source ─ HP ~5 Hz ─ [drive] ─ curve_tube ─ Tilt ─ Output ─ Mix
tape:     source ─ [drive] ─ curve_tape(bias) ─ loss(speed): LP + shelves ─ Output ─ Mix
console:  source ─ [drive] ─ LP 1st-order (flux) ─ curve_iron(offset) ─ HP 1st-order ─ Output ─ Mix
```

**Palette-verifier corrections, 2026-09-06 (measurements in `Fuzz` A4, run
against the C and the CPython audioif build).** Four claims in this section
and §5 needed fixing, each by measurement rather than argument:

- **`audiofilters.Filter` / `synthio.Biquad` has no first-order section.** …  *(argument in full: App. R)*
- **The palette's first-order sections live in `audioecho.FeedbackDelay`.** …  *(argument in full: App. R)*
- **The biquad route also holds DC, worst at exactly these corners.** Burst …  *(argument in full: App. R)*
- **Nothing on the palette gains above unity except the drive node.** …  *(argument in full: App. R)*

Mono: all three characters are per-channel with no cross-coupling; a mono
source gets one copy. Portability tier: **audioif**.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**A1 — the oversampled table waveshaper** (shared; `Fuzz` §5 and A4 carry the
measurements). *Traits unblocked here:* TU1, TU2 (an asymmetric curve at all
— CLIP and WAVESHAPE are odd-symmetric, h2 at the numerical floor, and the
palette's one asymmetric curve, OVERDRIVE, has an inert `drive`,
`upstream-diff.md:1228`, re-measured identical to the digit across drive
0.2 / 0.5 / 0.9 at two levels), TU3 and TP2 (a *specific* curve, not one of
four fixed shapes), A4. *Asked:* a curve loaded as data with `pre_gain`,
**`post_gain`** and `bias` as control inputs, oversampled ×2 / ×4 / ×8 with
polyphase IIR half-band filters. **`post_gain` added by the palette verifier**
— macro 1 asks for up to +12 dB of make-up and §4 shows no other node in the
palette can give it. *Refutation, re-run this run:* the four palette curves
were driven and measured rather than argued about, and the strongest
*composition* was driven too (a DC offset ahead of the symmetric CLIP curve,
removed after — the palette's only route to an asymmetric level-dependent
transfer), which produces asymmetry but a THD that *falls* at the top of its
range; the tables are in `Fuzz` A4. There is also no oversampling anywhere in
the palette: `audiospeed.SpeedChanger` is the only rate-changing node and it
reads `phase >> SPEED_SHIFT` with no interpolation and no anti-alias filter
(`src/audiospeed/SpeedChanger.c:139`, `:160`), so it cannot be a half-band
stage. **Not refuted.**

**A5 — one state variable inside the waveshaper, for hysteresis.**

- *Trait id:* TP3 (and IR2's loop, which is the same mechanism in iron).
- *What the palette would do instead:* a static table, whose output depends …  *(argument in full: App. R)*
- *What is asked:* an optional per-sample state in the same node — one …  *(argument in full: App. R)*
- *Refutation record (Phase 0):* **not refuted, and not yet earned.** The …  *(argument in full: App. R)*
- *Palette-verifier refutation attempt, 2026-09-06.* "The palette plainly …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Macros (8 of 16). `character` is a constructor option, not a macro:
switching rebuilds nodes, which the real-time rule forbids.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Drive | UNIPOLAR | −12…+24 dB into the curve | how hard the medium is hit; level is compensated so the knob buys harmonics, not volume |
| 1 | Output | UNIPOLAR | −24…+12 dB | make-up |
| 2 | Mix | UNIPOLAR | 0…1, 0 is the wire | the contract's Tier 1 wire |
| 3 | Headroom | UNIPOLAR | ±12 dB about each character's knee | tube: the operating point's room; tape: the level standard; iron: core size |
| 4 | Bias | BIPOLAR | 0 = centred | tube: grid bias; tape: under/over-bias (S3); iron: the DC offset of IR2 |
| 5 | Speed | UNIPOLAR | 3.75…30 ips, default 15 | tape only (TP1); documented inert on `tube` and `console` |
| 6 | Tilt | BIPOLAR | ±6 dB above 1 kHz | the medium's top end, riding TP1's loss curve on tape |
| 7 | Hysteresis | UNIPOLAR | 0 = the static table | the loop width of TP3; **defaults 0** and is inert unless A5 lands |

Patches: 0 "Gentle thickening" (default), 1 "Hot into the curve", 2 "Tape at
fifteen", 3 "Tape at seven and a half", 4 "Under-biased and bright", 5
"Iron, low end working", 6 "Offset, even harmonics", 7 "Lean" (oversampling
×2, hysteresis 0).

## 7. Defects in the current class the rebuild must not repeat

From one read of `drive.py:126-199` and this run's measurements.

- `drive.py:141` — the `tube` character is `_DM.OVERDRIVE`, whose `drive` …  *(argument in full: App. R)*
- The `tube` curve is not a triode's law. Measured at −20 dBFS: h2 −37.1, …  *(argument in full: App. R)*
- `drive.py:145`, `:149` — `tape` and `console` are both WAVESHAPE, measured …  *(argument in full: App. R)*
- `drive.py:194` — the shelves are scaled by `amount` (`gain_db * amount`), …  *(argument in full: App. R)*
- `drive.py:141-149` — `makeup_db` (0.0 / −2.6 / −1.06) levels the three …  *(argument in full: App. R)*
- `drive.py:170` — `MACRO_LABELS = ()`, on the class a host would automate …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Does hysteresis earn its node?** A5's two numbers, owed by Phase 1 (cost
   on the ESP32-S3; measured difference against the static curve). *Implementation
   session, from measurement.*
2. **The volts-to-dBFS mapping per character.** TU1's figures are grid volts
   and IR1's are flux; the class needs one documented mapping from 0 dBFS to
   each character's drive so the traits are testable at stated levels.
   *Station A — a documented constant, not a contract wall.*
3. **`console` has no named referent.** The character is iron in general
   (S4). If Phase 0's audit reaches a desk or preamp schematic with a
   transformer's turns ratio and core geometry, IR1's numbers get sharper and
   the character can be named more precisely. *Phase 0 audit.*
4. **Tape geometry defaults.** S3's own offline-test geometry (20 µm spacing)
   is far darker than a real 15 ips machine — computed −5.25 dB at 1 kHz
   (A2). The class picks its own (default 0.5 µm / 2 µm / 3 µm, −0.29 dB at
   1 kHz, −3 dB at 10.7 kHz) and TP1 is stated as the *scaling law*, not an
   absolute corner. Whether to expose the geometry as options: *Station A.*
5. **Oversampling factor** for A4 on the ESP32-S3 within Tier 3 — drive-family
   wide, answered once by Phase 1's cost/alias table.
6. **The two DAFx PDFs (S2, S4) carry no licence line.** Read as papers,
   nothing reproduced; the Phase 0 audit re-checks the proceedings' terms.
7. **`console` is one graded trait short.** After the trait-critic pass the
   character carries **two** graded rows (IR1, IR2) against vision §3's three,
   because IR3 could not be made falsifiable: the cross-character ordering is
   fixed by the drive mapping the class itself picks. Saying so here rather
   than leaving the count to be discovered is what §3's fixed-set rule asks
   for. The candidate third that two earlier audit passes already reached is
   **S5's measured corner** — distortion "below about 100 Hz for the Fender
   and 30 Hz for the Hammond" — which would become a falsifiable row the
   moment §8 Q2's mapping anchors the class's reference drive to it (the
   drive at which the 1 % THD corner lands at 100 Hz), turning a free
   parameter into a documented one. **This pass could not re-reach S5** (Aalto
   403, Springer auth redirect) and so does not write the row. *Station A,
   once S5 is reachable; the row is not an auditor's to fix.*
8. **A1's high-drive rows do not reproduce.** An independent re-solve of S2's
   equations in S1's netlist this run reproduces A1's DC point, headroom,
   small-signal gain and its 0.05 / 0.2 / 0.5 / 1.0 V harmonic rows to about
   0.1 dB, and does **not** reproduce its 2 V and 5 V rows under either
   reading of the netlist (with the 70 kΩ grid stopper loading the drive, or
   without). A1's narrative that h2 "collapses to −73 dBc" at 2 V is a
   knife-edge null a second solver puts at −44.5 dBc. TU2 has been restated so
   that no trait depends on those two rows, but **A1's table itself should be
   re-solved and its 2 V and 5 V rows corrected or struck** before Station A
   closes. *Station A.*


## Appendix

### A1. The triode stage, solved this run

S2's equations (10)–(12) with its RSD-1 parameters (G 2.242e-3, µ 103.2,
γ 1.26, C 3.40, Gg 6.177e-4, ξ 1.314, Cg 9.901, Ig0 8.025e-8) in S1's netlist
(Rp 100 kΩ, Rk 1.5 kΩ bypassed, Rg 70 kΩ, Vpp 250 V), solved by damped fixed
point for the DC point and then quasi-statically for the transfer curve;
harmonics from a 1 kHz sine at 192 kHz (numpy only, no scipy):

```
operating point: Vk = 1.231 V, Ia = 0.821 mA, plate = 167.9 V, Ig = 80 nA
headroom at the plate: 82.1 V toward the supply, 166.7 V toward the cathode
small-signal gain = -65.6x = 36.3 dB (inverting)

 Vin pk   out+ pk   out- pk   asym     h2      h3      h4      h5    THD
   0.05      3.27     -3.29  0.996   -54.1   -93.7  -122.5  -129.0   0.20%
   0.20     13.00    -13.21  0.984   -42.0   -70.4   -99.4  -139.3   0.79%
   0.50     31.86    -33.21  0.960   -33.8   -54.0   -76.4   -91.0   2.06%
   1.00     59.84    -63.35  0.945   -29.1   -34.7   -46.1   -47.4   4.01%
   2.00     82.74    -83.45  0.991   -73.4   -17.4   -44.7   -35.7  13.77%
   5.00     79.49   -130.38  0.610   -25.6    -9.3   -35.7   -18.3  39.86%
```

Read: h2 rises 12.1 dB for a 12 dB input rise (1.0 dB/dB) and h3 rises
23.3 dB (1.94 dB/dB) — the analytic signature of a weak nonlinearity, and
TU1's bar. The 2 V row is the trap and the reason TU1 is stated *below the
clipping onset*: the plate has just hit its 82 V cutoff ceiling on one side
while grid conduction compresses the other by a coincidentally similar
amount, so the peaks look symmetric (0.991) and h2 collapses to −73 dBc — a
measurement taken only there would disconfirm a true trait. At 5 V the two
mechanisms have separated again and the asymmetry is unmistakable (0.610).

### A2. The tape loss curve, computed this run

S3 eqs (13)–(14),
`|V/V0| = e^{-kd}·(1−e^{-kδ})/(kδ)·sinc(kg/2)`, `k = 2πf/v`. With S3's own
offline-test geometry (d 20 µm, g 5 µm, δ 35 µm) at 15 ips: −0.54 dB at
100 Hz, −5.25 dB at 1 kHz, −24.1 dB at 5 kHz, −44.2 dB at 10 kHz; total
−3 dB at 566 Hz; gap null at v/g = 76.2 kHz. That is much darker than a real
15 ips machine, which is why §8 Q4 has the class choose its own geometry —
d 0.5 µm, g 2 µm, δ 3 µm gives −0.29 dB at 1 kHz, −2.82 dB at 10 kHz, −3 dB
at 10.7 kHz, and at 7.5 ips exactly the same curve an octave down (−3 dB at
5.33 kHz), which is TP1.

Two checks that the computation is right rather than merely plausible: the
spacing term reproduces Wallace's classical 54.6·d/λ dB law to 0.001 dB
(2.8646 vs 2.8648 dB at 1 kHz, 15 ips, 20 µm); and doubling every geometry
dimension gives *exactly* the curve of halving the speed (−3 dB at 3061 Hz
either way), which is the wavelength scaling TP1 asserts, verified from two
directions.

### A3. The flux law, for IR1

Peak flux in a core is `Φ̂ = V̂/(2πfNA)` — the integral of the winding
voltage. At a fixed input level, halving the frequency doubles the peak flux,
so the level that reaches a given point on the BH curve falls 6 dB per octave
downward: that is IR1's slope, and S4's demonstration (5 V at 1 kHz nearly
linear, 5 V at 100 Hz "very non-linear" — a 20 dB flux difference across that
decade) is the same statement at two points.

### A4. Source excerpts kept out of §1–2

**S1** — "This circuit also provides about 30-dB amplification and saturates
with a deep crisp sound compared to the BJT preamp when overdriven"; the
netlist `Rp 100e3, Rk 1.5e3, Ck 25e-6, Rg 70e3, Vpp 250, T1 12ax7`; "the
nonlinearity must be computed offline … represented as a lookup table"; the
100×100 table "nearly identical to LTspice" for the BJT stage while the
coarse tables "exhibit unacceptable errors manifest as broadband" noise;
"most musical distortion algorithms apply the nonlinearity at an upsampled
rate, typically 4 to 8 times the audio sampling rate, e.g., 8x48 kHz".
**S2** — "This common-cathode amplifier can be found in almost all
preamplifiers designs"; "the flow of grid current introduces distortions and thus do not
satisfy the classical amplifier theory anymore … most guitar amplifier
designs since the 1960s are operated under these conditions"; "Even tubes
from the same type and same manufacturer may show up to 20 % deviation of
each other"; fitted RSD-1 / RSD-2 / EHX-1 parameter sets in its Table 1.
**S3** — "A typical analog recorder adds a high-frequency 'bias' current to
the signal to avoid the 'deadzone' effect when the input signal crosses zero,
as well as to linearize the output"; "For the Sony TC-260, the bias frequency
is 55 kHz, with a gain of 5 relative to the input signal. The lowpass filter
used to recover the audible signal has a cutoff at 24 kHz"; "since the TC-260
uses a bias frequency of 55 kHz and the minimum standard audio sampling rate
is 44.1 kHz, a minimum oversampling factor of 3x is required"; the loss
filter "implemented and tested offline in Python with tape-head spacing of 20
microns, head gap width of 5 microns, tape thickness of 35 microns, and tape
speed of 15 ips" at "a filter order of 100".
**S4** — "For high frequencies f, as shown in Figure 7a for f = 1 kHz, the
circuit almost perfectly achieves the voltage scaling by n2/n1 = 1/10. On the
contrary, for lower frequencies like f = 100 Hz shown in Figure 7b, the
saturation of the core yields a very non-linear behavior." Two further lines
the second audit pass kept, because IR1 and IR3 lean on that stage: it is "a
transformer circuit vaguely reminiscent of a tube amplifier's output
transformer stage", and "the inductor would be grossly undersized for a real
amplifier".
**S5** — "This is an open access article distributed under the Creative
Commons Attribution License, which permits unrestricted use, distribution, and
reproduction in any medium, provided the original work is properly cited";
"these practical transformer designs introduce distortion at low frequencies
only, below about 100 Hz for the Fender and 30 Hz for the Hammond
transformer"; "for the same input voltage, the magnetic flux Φ is larger when
the frequency is lower"; "a Hammond T1750V transformer, which is used in the
Vox AC30 guitar amplifiers"; a fitting procedure that "requires only the
measurement of basic electrical quantities but no knowledge of material
properties"; E = −N dΦ/dt (eq 1) and H = Ni (eq 3).

### Trait-critic pass — the record

2026-09-06, after the two licence audits and independent of them. Every Tier 2
row re-read against vision §3's bar — a statement a measurement can fail —
with S1, S2, S3 and S4 re-fetched with WebFetch and re-extracted with `pypdf`,
and **A1 and A2 re-solved independently** rather than taken from the draft.
Ten rows after the pass: **TU1–TU3**, **TP1–TP3**, **IR1–IR2** graded,
**IR3** *unmeasured*, and the shared **A4**.

**What was not falsifiable as written, and what each rewrite did.**

1. **TU1 and TP2 turned on an undefined threshold.** "Under the onset" and
   "below the knee" had no numeric definition, and A1's own table shows the
   15 dB bar already fails at 1.0 V grid drive — so a measurement could be
   scored anywhere and reach either answer. The onset is now **0.5 V peak grid
   drive** (the largest drive at which A1 and this run's re-solve both hold
   h2 − h3 ≥ 20 dB), and TP2's knee is defined operationally as **the drive at
   which THD reaches 1 %**, located by a sweep before the row is scored.
2. **The harmonic slopes did not name their convention.** "h2 rises 1.0 dB per
   dB, h3 2.0 dB per dB" is true in **dBc** and false in absolute terms, where
   the same physics gives 2 and 3 dB/dB. A measurer using the absolute
   convention would read 2.0 and disconfirm a correct rebuild against TU1's
   "faster than 1.4 dB/dB" clause. TU1 and TP2 now say dBc, print the absolute
   equivalent, and require the convention in what the measurement exports.
3. **TU2's bar rested on a row that does not reproduce.** Re-solving S2's
   eqs (10)–(12) with its RSD-1 parameters in S1's netlist reproduces A1's DC
   point (Vk 1.231 V, Ia 0.821 mA, plate 167.94 V, +82.06 / −166.7 V of
   headroom, gain −65.6× = 36.34 dB) **exactly**, and its 0.05 / 0.2 / 0.5 /
   1.0 V harmonic rows to 0.1 dB in h2 and h3 (h3 at the smallest drive is the
   one exception, 0.9 dB, close to the numerical floor) — and does **not** reproduce its 2 V or
   5 V rows under either reading of the netlist. S1's netlist puts
   `Rg i2 g 70e3` in series with the grid, so grid conduction loads the drive;
   with that loading the 5 V asymmetry is 0.87, not A1's 0.610, and without it
   the plate is driven above the 250 V supply, which is unphysical. A1's
   "the 2 V row is the trap … h2 collapses to −73 dBc" is a knife-edge null
   that this run's solve puts at −44.5 dBc. TU2 is restated on what *does*
   reproduce under both readings — **one polarity has a hard ceiling at the
   supply and the other does not** — with a bar written from this run's own
   numbers (positive peak 80.8 → 82.07 → 82.07 V at 2 / 5 / 10 V, +0.14 dB
   across the top 14 dB, against a negative peak of 82.6 → 94.3 → 103.9 V,
   +2.0 dB). §8 Q8 records that A1's own table still needs correcting.
4. **TU2's source cell carried a description S2 contradicts.** It read "grid
   current only for positive grid"; the licence audit had already corrected
   that in §1 and in S2's row but not in the trait. S2 §3.3, re-read this run:
   the measured grid current "increases when moving from small negative
   voltages towards the ordinate following an exponential shape" and rises
   "less steep" once positive.
5. **TU3's bar excluded the only figure a source gives.** ±2 dB about 36.3 dB
   does not contain S1's own "about 30-dB amplification" for the same stage.
   The row is kept — it catches a generator that has drifted from A1 — but
   relabelled for what it is, a **self-consistency check on the table
   generator**, with the reason the gap exists (S1 models the tube with
   Koren's equations, not S2's) stated. It also now says the slope is taken on
   the table **before** the class's output level compensation, which §6's
   macro 0 would otherwise make the number a design choice.
6. **TP1's stated band could not be measured at any supported rate.** Testing
   R(7.5 ips, f) = R(15 ips, 2f) over 20 Hz–20 kHz needs the 15 ips curve at
   40 kHz, past Nyquist at 48 kHz. The band is now 20 Hz–**12 kHz** at 48 kHz,
   with the 44.1 and 22.05 kHz bands given. Its gap-null clause sits at
   **190.5 kHz** at the class's geometry (76.2 kHz at S3's) and is explicitly
   not part of the bar — it is checked on the offline design curve.
7. **TP3's measurement would have passed a class with no hysteresis.** "A
   slow triangle traces a loop of non-zero area; a static curve encloses
   exactly zero" is true of the *curve* and false of the *signal path*: at
   20 Hz the first-order sections around the curve already enclose area, so
   the measurement as written could not fail. The row now measures the
   **difference against a `Hysteresis` 0 control** and states that a run in
   which both read zero is a broken measurement, not agreement.
8. **IR1 named no THD figure and no precondition.** The 1 % crossing is now in
   the trait, the 6 dB/octave is a fitted slope with a tolerance, and the row
   names the modelling precondition that would otherwise sink it: §4's flux
   low-pass integrates only well above its own corner, so that corner must sit
   a decade below 50 Hz.
9. **IR2 named no drive.** "At the same drive" is now the drive IR1's sweep
   identifies, and the row adds the clause that makes `Bias` an operating-point
   control rather than a gain (the fundamental moves < 1 dB).
10. **IR3 could not be failed by any rebuild.** Its ordering is fixed by the
    volts-to-dBFS mapping the class itself picks (§8 Q2), so a rebuild
    satisfies it by construction, and no reached source compares the three
    mediums at a matched drive. Marked *unmeasured*, its plot still produced
    and reported. That leaves `console` one graded row short of vision §3's
    three, recorded at §8 Q7.
11. **A4 did not name its oversampling setting.** Patch 7 "Lean" runs ×2
    against the shipped ×8; the row is now graded at the shipped setting and
    reported at the lean one, and it fixes 1010 and 3700 Hz as the probes.

**What was re-verified rather than taken on trust.**

- **S1** (Yeh, CCRMA) — netlist read verbatim, `Ci 0.047e-6 / Ri 1e6 /
  Rg 70e3 / Cf 2.5e-12 / Rp 100e3 / T1 12ax7 / Rk 1.5e3 / Ck 25e-6 /
  Vpp 250`; "about 30-dB amplification"; "typically 4 to 8 times the audio
  sampling rate, e.g., 8x48 kHz"; the 100×100 table "nearly identical to
  LTspice" against a coarse table of "25 steps for each dimension"; the IEEE
  personal-use line. Also read: S1's triode is **Koren's model with a grid
  current term**, not S2's — which is why TU3's 6 dB gap is not evidence of an
  error.
- **S2** (Dempwolf & Zölzer, DAFx-11) — eqs (10), (11), (12) and the RSD-1
  column of Table 1 (G 2.242E-3, µ 103.2, γ 1.26, C 3.40, Gg 6.177E-4,
  ξ 1.314, Cg 9.901, Ig0 8.025E-8) all match A1's inputs exactly; the "20 %
  deviation" sentence; the grid-current prose of item 4; no rights line.
- **S3** (Chowdhury, DAFx-19) — eqs (13) and (14) verbatim; CC BY 3.0
  Unported; the 55 kHz bias and 24 kHz recovery low-pass; the loss filter
  "implemented and tested offline in Python with tape-head spacing of 20
  microns, head gap width of 5 microns, tape thickness of 35 microns, and
  tape speed of 15 ips" at "a filter order of 100"; **16× oversampling**; and
  RK4 (eq 22) for the magnetisation, with the trapezoidal rule used only for
  the Ḣ derivative (eq 21) — which sharpens §2's standing flag on §5's A5.
  **New:** S3's **Figure 9** compares the model's hysteresis loop against one
  from a *physical* Sony TC-260, so a measured loop on a real machine *was*
  reached; TP3's source cell is corrected.
- **S4** (Holters & Zölzer, DAFx-16) — the 1 kHz / 100 Hz result verbatim,
  "vaguely reminiscent of a tube amplifier's output transformer stage",
  "the inductor would be grossly undersized for a real amplifier", and
  Figure 4's loops confirmed as compared against reference [2]'s published
  ones; no rights line.
- **S5** (Paiva et al.) — **not reached this run.** The Aalto bitstream and
  handle both returned HTTP 403 to WebFetch and the Springer DOI redirected to
  an authorisation endpoint. Two earlier audit passes reached it; its
  citations stand on those and **nothing new is built on it here**, which is
  why §8 Q7's proposed third `console` row is left to Station A.
- **A1 re-solved** (numpy, bisection on the load line): DC point, headroom and
  gain reproduce to the digit; harmonic rows reproduce to ≈0.1 dB at
  0.05–1.0 V; 2 V and 5 V do not (item 3).
- **A2 recomputed:** S3's own geometry at 15 ips gives −0.54 dB at 100 Hz,
  −5.25 dB at 1 kHz, −24.1 dB at 5 kHz, −44.2 dB at 10 kHz, −3 dB at 566 Hz;
  the class's geometry gives −0.29 dB at 1 kHz, −2.82 dB at 10 kHz, −3 dB at
  10 666 Hz, and 5 333 Hz at 7.5 ips; the wavelength identity holds to
  **0.0 dB exactly**; the loss is monotone over 20 Hz–20 kHz at both
  geometries. Every A2 figure reproduces.

**What this pass did not do.** No source was added, no bar was loosened, no
row was deleted, and §§1, 2, 4–7 were not edited. Two items were added to §8
(Q7, the `console` shortfall; Q8, A1's unreproduced rows).

### Audit record — the second licence and citation pass

Independent of the first audit and of the research pass. All five PDFs
downloaded again with `curl` and re-extracted with `pypdf`; every quotation
and number in §1–§3 checked against the extracted text rather than a
fetch-tool summary.

**What held.** Five of five HTTP 200 at the URLs in §2, page counts matching
(S1 10, S2 8, S3 7, S4 6, S5 16). Every licence call confirmed as written:
S1's "Copyright (c) 2010 IEEE. Personal use of this material is permitted";
S3's "Creative Commons Attribution 3.0 Unported License"; S5's "Creative
Commons Attribution License"; and **no rights line at all in S2's or S4's
PDF**, with `dafx.de/paper-archive/` re-checked and carrying none either —
which is what keeps both at *licence unverified, treated as copyleft*, and is
the answer §8 Q6 was waiting for. S1's netlist values, S2's RSD-1 parameter
set, S3's loss equations and 16× oversampling, S4's transformer parameters and
S5's two named transformers all reproduce verbatim. The Aalto handle in S5's
URL cell redirects to the item page and its open-access PDF downloads at the
bitstream id given; the Springer DOI page still returns a 3 kB script shell.

**What moved.**
1. **S2's grid current** (§1, S2's row). "Grid current only for positive grid"
   is harder than S2 says: its eq (11) is a softplus in Vg plus a constant
   Ig₀, and its §3.3 measurement has the current "increas[ing] when moving
   from small negative voltages towards the ordinate following an exponential
   shape", rising "less steep" once positive. Mechanism, polarity and TU2's
   claim are unchanged; only the description of the onset is.
2. **S4's hysteresis loops** (S4's row, TP3's source column). They are
   *simulated* and compared against reference [2]'s published loops — S4
   measures nothing on hardware. "S4 (same model, measured loops)" was wrong,
   and no reached source measures a loop on real tape, which makes TP3's
   already-hedged confidence the right one.
3. **S4's own caveat on its transformer stage** (S4's row, A4). The circuit is
   "vaguely reminiscent of a tube amplifier's output transformer stage" and
   "the inductor would be grossly undersized for a real amplifier". IR1's
   6 dB/octave law is the flux law and survives that caveat; IR3's
   cross-character comparison leans on the stage itself and should carry it.
4. **The CMJ 2009 not-found** sharpened from "not fetched" to reached-and-403,
   and the no-desk-schematic claim re-tested and upheld (§2).

**Flagged, not edited.** §5's A5 names the wrong solver: it asks for "S3's
eq (6) with the trapezoidal step S3 uses", and S3 uses fourth-order
Runge-Kutta (eq 22), having found lower-order implicit methods including the
trapezoidal rule unstable under a bias signal. §4–§8 are out of an auditor's
hands; Phase 1 must not build the state update from that sentence.

**What was deliberately not done.** No trait was added, dropped, renumbered or
re-toleranced. §8 Q3 (console has no named referent) and Q6 (the DAFx terms)
are written against premises both audits have moved, and are Arthur's.

<!-- Phase 0 seed, fuzz-saturation unit, 2026-09-06. S1-S4 fetched by the
research pass and read locally with pypdf; the Paiva transformer paper was
attempted there at Springer (auth redirect) and Aalto (403). Derivations A1-A3
were computed that pass with numpy; the scripts live in the session scratchpad,
not in the repo (§8 of the Overdrive seed raises where such probes should
live). Palette measurements are in Fuzz.md A2. No prior draft existed.

Licence and citation audit, same day, independent re-download and re-read of
all four PDFs (curl + pypdf, never a fetch-tool summary). Every content claim
in the rows checked verbatim and confirmed; corrections applied here: S1's
journal, issue and full title; S3's oversampling figure put back in its
sentence (3x is the bias-frequency minimum, S3 itself runs 16x) and the
consequence noted against Tier 3's lean patch; S4's own transformer geometry
and turns added; S2 and S4 recorded as licence-unverified rather than merely
"no line in the PDF", the DAFx archive index having no rights statement either;
S5 (Paiva et al.) added - reached on the first attempt at the same Aalto handle
the first pass recorded as 403, CC BY, with measurements of two named
transformers; TU3's 36.3 dB marked derived, since S1 says "about 30 dB"; TP1's
Wallace cross-check marked as arithmetic, not an independent source. Sections
4-8 untouched: §8 Q3 (console has no named referent) and Q6 (the DAFx terms)
are written against premises the audit moved and are Arthur's to update.

Second licence and citation audit pass, same day, independent of the first:
all five PDFs downloaded again with curl and re-extracted with pypdf, every
§1-§3 quotation and number checked against the returned text. All five HTTP
200 at the URLs in the table, page counts matching (10/8/7/6/16); every
licence call confirmed as written, including the two unverified ones - neither
DAFx PDF carries a rights line and dafx.de/paper-archive/ carries none either,
re-checked. No link dead, no licence call moved. New corrections: S2's grid
current restored to what S2 measures (a softplus plus Ig0, exponential from
small negative grid volts, not "only for positive grid") in §1 and its row;
S4's Figure 4 loops recorded as simulated and compared against reference [2],
not measured, in its row and in TP3's source column; S4's own "grossly
undersized for a real amplifier" caveat added to its row, since IR1 and IR3
lean on that stage; the CMJ 2009 not-found sharpened to a reached-and-403; the
no-desk-schematic claim re-tested and upheld. NOT edited, because sections 4-8
are out of an auditor's hands but Phase 1 must not build from it: §5's A5 asks
for "S3's eq (6) with the trapezoidal step S3 uses", and S3 uses fourth-order
Runge-Kutta (eq 22), having found the trapezoidal rule unstable under a bias
signal. Flagged in §2. No trait was added, dropped or renumbered. -->

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

*The wire is `Mix = 0`* — and unlike `Fuzz`, `Drive` at its minimum is also
within 0.1 % THD on every character, which the gate measures. *Rate:* TP1's
loss curve is stated in wavelength, so it holds at every rate; at 22.05 kHz
the tape character clamps its bias-derived top end below Nyquist (Tier 1's
clamp rule) and TU2/IR1 are re-measured at 44.1 kHz. *`capabilities` = `()`*
(D10): nothing here has an LFO, a delay or a tempo — nothing reads
`transport()`.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 D. T. Yeh, *Automated Physical Modeling of Nonlinear Audio Circuits For Real-Time Audio Effects — Part II: BJT and Vacuum Tube Examples*, IEEE Trans. Speech and Audio Processing **18(3), March 2011** (author's CCRMA copy) | the common-cathode netlist with values (`Rg 70e3, Rp 100e3, T1 12ax7, Rk 1.5e3, Ck 25e-6, Vpp 250`, plus `Ci 0.047e-6`, `Ri 1e6` and a `Cf 2.5e-12` Miller cap this dossier does not use); Koren's model with a grid-current term; the offline-table method and its resolution; oversampling "typically 4 to 8 times" (excerpts in A4) | "Copyright (c) 2010 IEEE. Personal use of this material is permitted." Not permissive — read as a paper for its mathematics; nothing reproduced | https://ccrma.stanford.edu/~dtyeh/papers/yeh12_taslp.pdf | yes — audit run 2026-09-06, HTTP 200, 10 pages extracted |
| S2 K. Dempwolf & U. Zölzer, *A Physically-Motivated Triode Model for Circuit Simulations*, DAFx-11, Paris | eqs (10)–(12) — Ik, Ig, Ia = Ik − Ig, the model used in A1 — with fitted parameters for three measured 12AX7s (RSD-1/RSD-2/EHX-1, Table 1); grid current as a **smooth softplus in Vg plus a constant Ig₀** (eq 11), measured rising exponentially from small *negative* grid volts and less steeply once positive — not the hard switch at zero the first draft's "only for positive grid" implied (corrected by the second audit pass); "up to 20 % deviation" between tubes of one type and maker | No licence statement in the PDF, **and none on the DAFx paper archive index either** (checked this run: `dafx.de/paper-archive/` carries no rights line). Licence unverified — treated as copyleft; read as a paper, nothing reproduced | https://dafx.de/paper-archive/2011/Papers/76_e.pdf | yes — audit run 2026-09-06, HTTP 200, 8 pages extracted |
| S3 J. Chowdhury, *Real-Time Physical Modelling for Analog Tape Machines*, DAFx-19, Birmingham | Jiles-Atherton magnetisation (eqs 6–9); the three playback losses in closed form (eqs 13–14, used in A2); the 55 kHz bias (gain 5) and its 24 kHz recovery low-pass; the loss filter as an order-100 FIR; its test geometry. **On oversampling, read the whole sentence:** 3× is only the minimum that fits the *bias frequency* — "since the biased signal is then fed into the hysteresis model, even more oversampling is required to avoid aliasing … our system uses an oversampling factor of 16x" | **CC BY 3.0 Unported**, stated in the paper — the only permissive source here besides S5 | https://www.dafx.de/paper-archive/2019/DAFx2019_paper_3.pdf | yes — audit run 2026-09-06, HTTP 200, 7 pages extracted |
| S4 M. Holters & U. Zölzer, *Circuit Simulation with Inductors and Transformers Based on the Jiles-Atherton Model of Magnetization*, DAFx-16, Brno | the JA model as a time-differential equation; two published parameter sets (Table 1); the output-transformer result — near-perfect at 1 kHz, "very non-linear" at 100 Hz, at the same 5 V. **And, which the first pass did not record, that stage's actual numbers:** `Ms=2.75e5, a=14.1, α=5e-5, k=17.8, c=0.55, D=2.4e-2 m, A=4.54e-5 m², ns=[230, 23]`, into R₁=R₂=10 Ω — turns ratio and core geometry, for an unnamed simplified stage. **And S4's own caveat on that stage, which the second audit pass added because IR1 and IR3 lean on it:** the circuit is "vaguely reminiscent of a tube amplifier's output transformer stage" and "the inductor would be grossly undersized for a real amplifier". Its Figure 4 hysteresis loops are **simulated** and compared against reference [2]'s published ones; nothing in S4 is measured on hardware | No licence statement in the PDF, none on the archive index. Licence unverified — treated as copyleft; read as a paper | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2017/10/Holters_jamodel_DAFx16.pdf | yes — audit run 2026-09-06, HTTP 200, 6 pages extracted |
| **S5** R. C. D. Paiva, J. Pakarinen, V. Välimäki & M. Tikander, *Real-Time Audio Transformer Emulation for Virtual Tube Amplifiers*, EURASIP J. Advances in Signal Processing 2011, doi 10.1155/2011/347645 (Aaltodoc copy) — *added by the audit; the first pass recorded this as unreachable and it is not* | measurements of two **named** transformers, a Fender NSC041318 and a Hammond T1750V "used in the Vox AC30 guitar amplifiers"; that these "introduce distortion at low frequencies only, below about 100 Hz for the Fender and 30 Hz for the Hammond"; the flux law stated as the cause — "for the same input voltage, the magnetic flux Φ is larger when the frequency is lower"; E = −N dΦ/dt, Φ = B·Ae, H = Ni; a hyperbolic-curve parameter-fitting procedure needing "only the measurement of basic electrical quantities but no knowledge of material properties" | **Creative Commons Attribution License**, stated in the paper: "This is an open access article distributed under the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited." **Permissive** — the first source in this dossier that could be ported from rather than only read, if the class ever wanted its fitting procedure | https://aaltodoc.aalto.fi/handle/123456789/26495 → https://aaltodoc.aalto.fi/bitstreams/41199441-b13b-410f-9798-d904e4867d8c/download | yes — audit run 2026-09-06, HTTP 200, 3.06 MB, 16 pages extracted |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| TU1 | **Even harmonics dominate below the clipping onset, on the power laws of a weak nonlinearity.** **Relative to the fundamental (dBc)** h2 rises **1.0 dB per dB** of input and h3 **2.0 dB per dB** — in absolute terms 2 and 3 dB/dB. The row is stated in dBc, so a measurement taken in absolute terms reads exactly one more and must not be scored against these numbers. h2 therefore leads h3 by 40 / 28 / 20 dB at 0.05 / 0.2 / 0.5 V peak grid drive (*derived*, A1). **"Below the onset" is 0.5 V peak grid drive:** by 1.0 V the lead has already collapsed to 5.5 dB, so the bar is claimed at or below 0.5 V and nowhere above it. Bar: **h2 − h3 ≥ 15 dB** at every drive ≤ 0.5 V, and h2 within **±4 dB** of A1 at the three tabulated drives | S1 (netlist and values); S2 (eqs 10–12 and the RSD-1 parameter set). Both re-fetched and re-read this run; A1 was re-solved independently and reproduces 40.5 / 28.4 / 20.2 dB with dBc slopes of 1.01 and 2.02 dB/dB | high — two papers, an analytic signature, and an independent re-derivation. **Not yet testable:** "grid drive" is in volts and the kit drives dBFS, so the row cannot be scored until §8 Q2 documents the volts-to-dBFS mapping. The trait-critic pass makes that dependency explicit rather than leaving it to be discovered at the bench | h2 at or below h3 at any drive ≤ 0.5 V; h2's **dBc** slope outside 0.6–1.4 dB/dB across that span; h2 more than 4 dB from A1 at a tabulated drive | spectrum of a 1 kHz sine at 0.05 / 0.1 / 0.2 / 0.35 / 0.5 V equivalent grid drive; h2 and h3 tracked **in dBc**, the slope fitted over the span, and the convention printed in what the measurement exports |
| TU2 | **Two different limits on the two polarities, and only one of them is a ceiling.** Plate cutoff pins the positive-going output excursion at the supply — **+82.06 V** above the 167.94 V idle, and no further however hard the stage is driven — while grid conduction on the other polarity merely compresses, so the negative-going excursion keeps growing. Bar: from the drive at which the positive peak first comes within 1 dB of that ceiling, a further **20 dB** of input grows the positive peak by **< 1 dB** and the negative peak by **> 1.5 dB**, and the smoothly-compressed side is the grid-conduction one | S1 — its netlist puts `Rg i2 g 70e3` **in series** with the grid (`Ri i2 0 1e6` is the leak), so grid conduction loads the source, and S1's own grid-current term is written across that same resistor; re-read verbatim this run. S2 — eqs (11)–(12): the grid current is a **softplus in Vg plus a constant Ig₀**, measured "increas[ing] when moving from small negative voltages towards the ordinate following an exponential shape" and "less steep" once positive. *(This cell previously read "grid current only for positive grid, eqs 11–12"; the licence audit corrected that description in §1 and in S2's row but not here, and the trait-critic pass carries the correction into the trait.)* | high for the mechanism, the sign and the +82.06 V ceiling, all reproduced by an independent solve this run. **The first draft's "peak asymmetry 0.61 at 5 V drive" did not reproduce and is no longer the bar:** re-solving S2's equations in S1's netlist *with* the 70 kΩ grid stopper in the drive path gives 0.87 at 5 V, and solving *without* it drives the plate above the 250 V supply, which is unphysical. A1's rows at 0.05–1.0 V reproduce to 0.1 dB in h2 and h3 (the one exception is h3 at the smallest drive, 0.9 dB, close to the numerical floor); its 2 V and 5 V rows do not reproduce at all, and no trait now rests on them | a positive peak that keeps growing past its ceiling — no hard cutoff limit — or a negative peak that stops growing with it, both sides limiting alike | ± output peak of the quasi-static transfer curve at 1 / 2 / 5 / 10 V equivalent grid drive; incremental gain either side of the idle point. *(Re-derived this run: positive peak 80.8 → 82.07 → 82.07 V at 2 / 5 / 10 V, +0.14 dB across the top 14 dB, against a negative peak of 82.6 → 94.3 → 103.9 V, +2.0 dB.)* |
| TU3 | **Gain and operating point are the character's, not a knob's:** inverting, **65.6× (36.3 dB)** small-signal, idling at Ia 0.821 mA, Vk 1.231 V, plate 167.94 V (*derived*, and reproduced to the digit by an independent solve this run). Bar: the **shipped table's** small-signal slope at its reference operating point — taken on the table, **before** the class's output level compensation, since macro 0 compensates level and a gain measured after it is a design choice rather than a measurement — within **±2 dB** of 36.3 dB, and the generator's printed DC solve within 5 % of those three values | S2's device parameters in S1's netlist. **Neither source states 36.3 dB.** S1's own figure for its own stage is "about 30-dB amplification", ~6 dB below the bar — and S1 models the triode with Koren's equations plus a grid-current term, not S2's, so part of that gap is a device-model difference and is not evidence either is wrong | **medium, and the row's reach is narrow:** it is a **self-consistency check on the table generator**, not a check against a source. It catches a generator that has drifted from A1; it cannot discriminate a correct implementation from a wrong parameter set, because the only reached figure for this stage — S1's "about 30 dB" — lies outside the bar it sets | small-signal slope outside 34.3–38.3 dB, or a DC solve more than 5 % from A1's Vk / Ia / plate | slope of the shipped table about its reference point, and the DC solve printed by the table generator; both on CPython, **not** on the rendered output after level compensation |

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| TP1 | **Playback loss is a function of wavelength, so it slides exactly with speed.** All three terms depend on frequency only through `k = 2πf/v` (S3 eqs 13–14, re-read verbatim this run), so the 7.5 ips response equals the 15 ips response at twice the frequency **within 0.5 dB**, and the in-band loss is monotone. **Testable band, 20 Hz–12 kHz at 48 kHz:** the comparison needs the 15 ips curve at 2f, so any point above 12 kHz would need data past Nyquist — the first draft claimed 20 Hz–20 kHz, which cannot be measured at any supported rate. At 44.1 kHz the band is 20 Hz–11 kHz and at 22.05 kHz 20 Hz–5.5 kHz. **The gap null at v/g is not part of the bar:** it sits at 190.5 kHz at the class's geometry (76.2 kHz at S3's), so no audio sample rate reaches it, and it is checked on the design curve computed offline, never on rendered audio | S3 eqs 13–14. The A2 cross-check against Wallace's 54.6·d/λ law is **arithmetic, not an independent source** — 54.6 = 2π·20·log₁₀(e) falls straight out of S3's own e^{−kd} term. The check that tests the claim is the wavelength scaling: doubling every geometry dimension equals halving the speed, verified from both directions and reproduced this run (the two curves agree to 0.0 dB exactly, and the loss is monotone over 20 Hz–20 kHz at S3's geometry and at the class's) | high — closed form | a speed control that changes level, or applies a shelf, instead of translating the curve; any point in the testable band where the two curves differ by more than 0.5 dB; non-monotone in-band loss | swept magnitude at 7.5 and 15 ips, one shifted an octave and subtracted from the other, over the band the running rate allows and with that band recorded in what the measurement exports |
| TP2 | **The saturating curve is odd** (the Langevin anhysteretic, S3 eq 9), with `Bias` centred at 0. **The knee is defined operationally as the drive at which THD reaches 1 %**, located first by the THD-vs-drive sweep, so "below the knee" and "above it" are measurable rather than eyeballed. Bar: h2 and h4 **≤ −40 dBc**; h3 rises **2.0 ± 0.4 dB per dB in dBc** (3 dB/dB absolute — same convention note as TU1) over the 20 dB below the knee; and above it the output peak grows **< 3 dB** for a 20 dB input rise | S3 eqs 6–9 | high for the symmetry and the slope, which are the Langevin's by construction; medium for where the knee lands, set by Ms, a and the class's drive scaling (§8 Q2) | h2 or h4 above −40 dBc with `Bias` centred; h3's dBc slope outside 1.6–2.4 dB/dB below the knee; the output peak still tracking the input to within 3 dB over the 20 dB above the knee | THD-vs-drive sweep to locate the 1 % knee, then spectra at four drives spanning the 20 dB below it and output peak at the knee and 20 dB above; `Bias` at 0 throughout |
| TP3 | **The medium has memory: the loop encloses area — and the area is the state variable's, not the filters'.** Magnetisation depends on the direction of travel (S3 eqs 6–8), so a slow triangle traces a loop whose area grows with drive. **Measured against a control, never against zero:** the same signal path with `Hysteresis` at 0 is a memoryless curve between the same first-order sections, and at 20 Hz those sections' own phase shift already encloses area, so "non-zero area" would be satisfied by a class with no hysteresis at all. Bar: at maximum drive the `Hysteresis` 1 loop's area exceeds the `Hysteresis` 0 control's by **≥ 6 dB**, and that excess grows monotonically with drive over three settings. The one trait the palette cannot reach (§5) | S3 eqs 6–8; **and S3's Figure 9, which prints the model's hysteresis loop beside one taken from a *physical* Sony TC-260** — read this run, and it corrects this cell's previous "no reached source measures a loop on real tape". S3 notes some of the difference between the two loops "may be due to the circuitry of the tape machine that we did not attempt to model". S4's Figure 4 loops are simulated and compared against its reference [2]'s published ones, not measured | high that the physics says so **and that a real machine shows one** (S3 Fig. 9 — upgraded from the first draft, which had no measured loop); **medium that it is audible at the levels a subtle-thickening class runs at** — Phase 1's refutation, not this seed's claim | the `Hysteresis` 1 loop's area within 6 dB of the `Hysteresis` 0 control's at maximum drive, or the excess not growing with drive | output-vs-input from a 20 Hz triangle at three drives, at `Hysteresis` 0 **and** 1, enclosed area by the shoelace formula. The `Hysteresis` 0 pass is a control that must itself show the filters' own non-zero area: a run in which **both** read zero is a broken measurement, not agreement |
| IR1 | **Saturation is flux-driven, so it starts at the bottom.** Peak flux is ∫v dt, so the input level that reaches **1 % THD** rises with frequency at **6.0 ± 1.5 dB per octave**, fitted by least squares in log-frequency over 50 / 100 / 200 / 400 / 800 Hz. **Precondition the rebuild must state and the measurement must check:** §4's flux low-pass is an integrator only well *above* its own corner, so that corner has to sit at least a decade below 50 Hz — otherwise the law flattens at the bottom of the band and the row fails for a modelling reason rather than a circuit one, which is a failure the evidence pack must be able to tell apart | S4 (the JA transformer stage: "for high frequencies f, as shown in Figure 7a for f = 1 kHz, the circuit almost perfectly achieves the voltage scaling by n2/n1 = 1/10", against "for lower frequencies like f = 100 Hz … the saturation of the core yields a very non-linear behavior", both at 5 V — a 20 dB flux difference across that decade; re-read verbatim this run). **S4's own caveat travels with the citation:** its stage is "vaguely reminiscent of a tube amplifier's output transformer stage" and "the inductor would be grossly undersized for a real amplifier". S5 independently, on measured hardware (**not reachable this run** — Aalto 403 and a Springer auth redirect; the citation stands on two earlier audit passes and nothing new is built on it here) | high — the flux law is both models' own, and S4 shows the consequence in simulation | a fitted slope outside 4.5–7.5 dB/octave; equal 1 % crossings at 100 Hz and 1 kHz; a knee that moves with level but not with frequency | THD-vs-level at 50 / 100 / 200 / 400 / 800 Hz, the 1 % crossings fitted; the flux low-pass's corner reported alongside so the precondition is visible in the same artefact |
| IR2 | **Odd by symmetry until the operating point moves.** At the drive IR1's sweep identifies as the 1 % THD crossing at 100 Hz: with `Bias` centred h2 is **≤ −40 dBc**; at `Bias` ±0.5, same drive and frequency, h2 is **≥ −25 dBc**. And `Bias` moves nothing else — the fundamental's level changes **< 1 dB** across that range, so it is an operating-point control and not a gain | S4 (the model; symmetric loops by construction) | high for the symmetric case, which the JA model gives by construction; **medium for −25 dBc and for the < 1 dB level clause, both design bars no reached source states** | h2 above −40 dBc with `Bias` centred; h2 below −25 dBc at `Bias` ±0.5; or a fundamental level that moves ≥ 1 dB across the `Bias` range | spectrum at `Bias` −0.5 / 0 / +0.5, 100 Hz, at the drive IR1's sweep fixes; h2 **and** the fundamental both tracked |
| IR3 | **unmeasured: the cross-character ordering is fixed by a mapping this class chooses, so a rebuild cannot fail it.** "Iron is the gentlest of the three at matched drive" compares three different papers' circuits through the volts-to-dBFS mapping of §8 Q2 — the class's own free choice — so a rebuild that picks the mapping satisfies the ordering by construction, and no reached source compares the three mediums at a matched drive. The three-character THD-vs-drive plot at 1 kHz is still **produced and recorded** in the evidence pack as a voicing check; it carries no pass/fail bar. The sourced half of the old row lives in IR1, which is graded | S4, S5 — neither compares mediums; and S4's own stage is "grossly undersized for a real amplifier", which is a thin basis for a cross-medium ranking | — | — | THD-vs-drive at 1 kHz, three characters on one plot: reported, not graded |
| A4 | **Alias floor:** a 1010 Hz sine at −6 dBFS, any character at maximum drive, **on the shipped (non-lean) oversampling setting**: non-harmonic energy **≥ 60 dB** below the fundamental at 48 kHz. The drive family's shared bar. The setting is named because patch 7 "Lean" drops oversampling ×8 → ×2, and an unqualified row would either fail on the lean patch or let it hide | S1 (4–8×, verbatim this run: "typically 4 to 8 times the audio sampling rate, e.g., 8x48 kHz"); S3 (3× is only the minimum that fits the *bias frequency*; S3's own system runs **16×**, re-read this run) | medium — a design bar, not a circuit fact | non-harmonic energy above −60 dB at either probe on the P4 or the ESP32-S3 build, at the shipped setting. **The lean patch is measured at the same probes and reported, not graded here** — §8 Q5 owns whether it must also meet −60 dB | non-harmonic bin sum vs the fundamental at **1010 Hz and 3700 Hz**, 48 and 44.1 kHz, shipped and lean patches both reported. A 1000 Hz probe measures nothing — its aliases fold onto the harmonic grid (`Fuzz` A2, re-measured this run: −319.5 dB at 1000 Hz against −11.8 dB at 1010 Hz on the same curve), so the probe frequencies are part of the trait |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Second audit pass, same day.** The first audit run was cut off before its
report was written, so all five PDFs were downloaded a *third* time,
independently, and every quotation and number in §1–§3 checked against the
extracted text. **All five answered HTTP 200 at the URLs above, every page
count matched, and every licence call was confirmed as written — the two CC BY
calls (S3, S5), the IEEE personal-use call (S1), and the two unverified ones
(S2, S4), whose PDFs carry no rights line and whose archive index carries none
either.** No link is dead and no licence call moved. Three things did move —
S2's grid-current description, S4's hysteresis loops, and S4's own caveat on
its transformer stage; the record is under the Appendix, "Audit record".

*(from §2)*

**One mis-citation flagged and deliberately not edited**, because §4–§8 are
out of an auditor's hands and Phase 1 must not build from it: **§5's A5 asks
for "S3's eq (6) with the trapezoidal step S3 uses". S3 uses fourth-order
Runge-Kutta (its eq 22) and says in as many words that "lower-order implicit
methods such as the trapezoidal rule … quickly became unstable for
high-frequency input, particularly when the input is modulated by a bias
signal".** The ask itself is unaffected; the solver named in it is wrong.

*(from §2)*

**The "not found" claim the audit overturned.** The first pass recorded the
Paiva transformer paper as unreachable (Springer auth redirect; Aalto 403). In
the audit run the same Aalto handle URL answered HTTP 200 and redirected to
the item page, whose open-access PDF downloaded on the first attempt; it is now
**S5**, it is CC BY, and `console` no longer rests on S4 alone. §8 Q3 is
written against the older premise and is Arthur's to update. (The Springer DOI
page does still come back as a 3 kB script shell with no article text.)

*(from §2)*

**Still looked for, not found — re-tested by the second audit pass, and all
three claims stand.** Pakarinen & Yeh's *Review of Digital Techniques for
Modeling Vacuum-Tube Guitar Amplifiers* (CMJ 2009): the publisher's own PDF at
`direct.mit.edu/comj/article-pdf/33/2/85/1855308/comj.2009.33.2.85.pdf`
answered **HTTP 403** — reached-for and refused, which is sharper than "not
fetched", and nothing is cited from it. Bertram's *Theory of Magnetic
Recording*, S3's own reference for the loss equations, was not sought (a
book). **No mixing-console or desk schematic with values was reached**: a
candidate page for the Neve 1073's Marinair transformers answered HTTP 200 and
carries no turns ratio, core geometry or specification text at all, and
everything else a search surfaced was a forum or vendor snippet, which the
sources module says to treat as unreachable rather than cite. §8 Q3's premise
stands. No hardware capture — none is on the bench (vision §2.3).

*(from §3)*

**Unmeasured, not a trait — tube-to-tube spread.** S2 records "up to 20 %
deviation" between triodes of the same type and maker, and fits three
different parameter sets for three real tubes. The class ships one set and
names it; the spread is why this is a *character* and not a clone, and it is
not something a measurement of ours can pass or fail.

*(from §3)*

Fraction of one stereo block's deadline (256 frames at 48 kHz, 5.33 ms):
**ESP32-P4 0.10, ESP32-S3 0.25**. `tube` is one oversampled table lookup;
`console` adds an integrator and a differentiator around its table; `tape` is
the expensive one — the loss chain plus, if §5's ask survives, a state update
per oversampled sample. Lean patch expected: **yes** on the ESP32-S3, and it
does two things and no others — oversampling ×8 → ×2, `Hysteresis` forced 0
(the static table, TP3 dropped with cause in the lean patch's docstring).
*Audit note:* S3's own tape system runs at **16×**, not the 3× the first draft
quoted, so ×2 in a lean patch is a long way below the source's own practice and
the A4 measurement is what has to justify it — not the citation.

*(from §3)*

**Latency: zero, and one option that is not.** All three characters are a
curve between recursive filters; nothing looks ahead. `latency_samples` is 0.
The one place latency could enter is TP1's loss filter: S3 realises it as an
order-100 FIR, which linear-phase would cost about 50 samples — **1.04 ms at
48 kHz**. This class fits the same magnitude with cascaded first-order and
biquad sections instead and keeps latency at zero; the FIR path stays
available as an option, **defaults off**, and reports its true
`latency_samples` the moment it is enabled. The waveshaper's oversampling
filters are polyphase IIR (`Fuzz` §5), so they add phase delay, not
lookahead.

*(from §4)*

Every character is a table between first-order sections, which is why one
node ask serves all three. The tables are computed on CPython by a generator
the dossier ships and stored as `array('h')` — never rebuilt on a board,
whose single-precision math would build a different table (vision §6), and
never rebuilt on a macro move: `Drive`, `Bias` and `Headroom` are pre-gain
and offset into a fixed normalised curve, exactly the structure S1 uses
(solve offline, interpolate at runtime).

*(from §4)*

Two things this buys cheaply. **The tape bias bakes in:** S3's 55 kHz bias
would force ≥ 3× oversampling before the nonlinearity's own requirement, but
its effect on the quasi-static transfer — filling the deadzone, linearising
near zero — is computed once offline and shipped inside the table, so the
board never sees 55 kHz. **The flux integrator is a filter:** IR1 needs
`∫v dt` before the curve and `d/dt` after, which a first-order low-pass and
its matching high-pass are — but *not* on the node the first draft implied.

*(from §4)*

- **`audiofilters.Filter` / `synthio.Biquad` has no first-order section.**
  All seven `synthio.FilterMode` modes are second-order RBJ biquads
  (`audioif_biquad.c:76-112`), and a biquad low-pass at 5 Hz measures
  **12.0 dB/octave**. Building the flux integrator on it turns IR1's
  6 dB/octave flux law into a 12 dB/octave one — the trait disconfirmed for a
  modelling reason, which is exactly the failure IR1's precondition clause
  exists to make visible. `tube`'s HP ~5 Hz and `console`'s post-curve
  high-pass are the same node and the same problem.

*(from §4)*

- **The palette's first-order sections live in `audioecho.FeedbackDelay`.**
  `damping_hz` (one-pole low-pass) and `cut_hz` (one-pole high-pass) are
  `one_pole_coefficient()` sections (`audioif_feedback_delay.c:31-38`, run per
  sample at `:231-240`); at `feedback=0`, `mix=2.0`, `delay_ms` = one frame
  the node *is* a one-pole, measured at 5 Hz at exactly **6.02 dB/octave** and
  matching the closed form to 0.01 dB. That is the integrator IR1 needs. It
  costs a delay line and **one sample of latency** per section — the two
  sections `console` draws are 2 samples, 41.7 µs at 48 kHz, which Tier 3's "latency: zero"
  must absorb or §5's node must carry the sections itself.

*(from §4)*

- **The biquad route also holds DC, worst at exactly these corners.** Burst
  then silence with the source still rendering: an `audiofilters.Filter`
  section settles to a permanent **±284 LSB at 5 Hz** (±36 at 14 Hz, ±7 at
  31 Hz) where the one-pole route reads **exact zero**. That is audioif#23
  (its published figures reproduce to the digit) and Tier 1's held-DC failure
  — and for `console` worse than a nuisance, because the flux low-pass sits
  *before* the curve, so a stuck 284 LSB is a permanent uncommanded operating
  point into a saturating nonlinearity: IR2's exact subject. **This seed's
  Gate 0 answer:** the one-pole route, compose-first and measured clean.

*(from §4)*

- **Nothing on the palette gains above unity except the drive node.**
  MixerVoice level is clamped `0.0..1.0` (`src/audiomixer/Mixer.c:332`,
  measured) and `audiomath.Multiply` scales by `>> 15`, so a full-scale
  modulator is unity and no more (`audioif_multiply.c:38`). Macro 0's +24 dB
  of `Drive` and macro 1's +12 dB of `Output` are therefore both §5's node,
  whose ask named only `pre_gain` and is corrected there.

*(from §4)*

What the composition cannot do is TP3 — a table has no memory. §5 asks for
it, and if the ask is refuted the class ships the anhysteretic curve, states
that hysteresis is not modelled, and drops TP3 with the reason recorded, per
vision §3's rule for a trait dropped after the fact.

*(from §5)*

- *What the palette would do instead:* a static table, whose output depends
  only on the present input. Its triangle-sweep loop encloses exactly zero
  area, by construction — which is TP3's disconfirmation condition, met a
  priori, with no measurement needed to know it.

*(from §5)*

- *What is asked:* an optional per-sample state in the same node — one
  previous-output term and a direction flag, updating S3's eq (6) with the
  trapezoidal step S3 uses, with the JA parameters shipped as data beside the
  curve. Cost per oversampled sample is one Langevin evaluation; S3's own
  continued-fraction `tanh` approximation (its eq 25) is the cheap form and
  needs no `exp`.

*(from §5)*

- *Refutation record (Phase 0):* **not refuted, and not yet earned.** The
  physics is sourced (S3, S4) and the palette plainly cannot reach it, but
  this seed does not claim the loop is audible at the levels a
  *subtle-thickening* class runs at. Phase 1 owes two numbers before the node
  is built: the ESP32-S3 cost of the state update, and the measured difference
  between the static curve and the loop on the probe material. If the second
  is under the ear's floor, the honest outcome is to drop TP3 rather than pay
  for it — and that is a legitimate result, not a failure (vision §3).

*(from §5)*

- *Palette-verifier refutation attempt, 2026-09-06.* "The palette plainly
  cannot reach it" was an argument, so it was measured. The palette does have
  a per-sample nonlinear recursion — `audioecho.FeedbackDelay` at a one-frame
  delay with `loop_drive` engaged is `line[n] = in[n] + f·soft_clip(line[n−1])`
  (`audioif_feedback_delay.c:241-243` and `:255-256`, delay clamped to a floor
  of one frame at `:83`) — and it does enclose loop area on a 20 Hz triangle.
  It fails TP3 as stated, and fails it in the direction that matters. Shoelace
  area of the input-output trajectory, normalised by the two peaks so it
  measures loop *shape* and not gain, in dB against the same input through
  `feedback = 0, loop_drive = 0`:

*(from §5)*

  | input | fb .5, no clip | fb .9, no clip | fb .9, clip .3 | fb .9, clip .6 | fb .9, clip 1.0 |
  |---|---|---|---|---|---|
  | −18 dBFS | +2.81 | +9.83 | +8.37 | +8.04 | +7.81 |
  | −12 dBFS | +2.85 | +9.91 | +8.03 | +7.46 | +7.30 |
  | −6 dBFS | +2.88 | +9.91 | +8.07 | +7.42 | +7.18 |

*(from §5)*

  The area clears TP3's ≥ 6 dB bar — and is **largest with the nonlinearity
  switched off entirely**, flat or falling as drive rises where a magnetic
  loop's grows. Engaging `loop_drive` *reduces* it. The excess is a one-pole
  phase lag, the same kind of area TP3's `Hysteresis` 0 control exists to
  subtract out.
  `audiodynamics.Dynamics` is the other candidate — an asymmetric
  attack/release is genuinely direction-dependent gain — and it fails the same
  two ways: at 20 Hz its normalised loop area *shrinks* with drive
  (3.24e−5 → 1.76e−5 → 1.37e−5 at −18 / −12 / −6 dBFS, 8:1 over −24 dBFS,
  0.1 ms / 50 ms), and at fixed drive it moves two orders of magnitude with
  frequency and not monotonically (−18 dBFS: 3.24e−5 at 20 Hz, 9.99e−6 at
  200 Hz, 1.15e−4 at 2 kHz), because its loop is set by the release time
  against the period. A JA loop is quasi-static; a compressor's is an envelope
  artefact.
  The measurement carries a control that must pass (a wire reads exactly 0.0
  area) and a planted fault that must fire (a one-sample lag reads 2.78e−6);
  an earlier version aligned the reference by correlation and so read zero for
  a *pure delay* too, and an earlier un-normalised version credited the loop
  with area that was really output gain. Both were caught by the control.
  **Not refuted — and now for a measured reason rather than an asserted one.**

*(from §5)*

No other ask, with one correction to what "reachable" meant. The loss chain
and the shelves are reachable on `audiofilters.Filter`. The **flux integrator
is not** — not on that node, whose second-order sections turn IR1's flux law
into a 12 dB/octave one; it is reachable on `audioecho.FeedbackDelay`'s
one-pole at one sample of latency and one delay line, or from this ask's node
(§4). And the gains above unity are reachable **only** from this ask's node,
which is why `post_gain` was added to A1 above.

*(from §7)*

- `drive.py:141` — the `tube` character is `_DM.OVERDRIVE`, whose `drive`
  argument the node never reads (`audioif/docs/upstream-diff.md:1228`;
  measured identical at 0.2 / 0.5 / 0.9). The module knows and works around
  it by moving `pre_gain` (`_push`, `drive.py:39-49`), so the class's own `drive`
  reaches the curve only as level.

*(from §7)*

- The `tube` curve is not a triode's law. Measured at −20 dBFS: h2 −37.1,
  h3 −44.5 dBc, i.e. **h2 − h3 = 7.4 dB** where the derived triode stage gives
  20–40 dB (TU1); and h2 rises **0.84 dB per dB** of input where a
  second-order nonlinearity gives 1.00.

*(from §7)*

- `drive.py:145`, `:149` — `tape` and `console` are both WAVESHAPE, measured
  odd-symmetric (h2 −153 dBc), so the two mediums differ only by a `drive`
  value and two shelves: no speed dependence, no loss law, no flux law, no
  hysteresis. The docstring's "distinguishable rather than cosmetic" holds
  only between `tube` and the other two.

*(from §7)*

- `drive.py:194` — the shelves are scaled by `amount` (`gain_db * amount`),
  welding the character's tone to the dry/wet control: a quarter mix gives a
  quarter of the EQ. And the shelf frequencies and gains (`:145-150`) are
  constants with no source behind them.

*(from §7)*

- `drive.py:141-149` — `makeup_db` (0.0 / −2.6 / −1.06) levels the three
  characters "measured on a -12 dBFS sine": with level-dependent curves that
  match holds at exactly one level.

*(from §7)*

- `drive.py:170` — `MACRO_LABELS = ()`, on the class a host would automate
  most; `drive.py:172` — one patch; `drive.py:174` — `character` reachable
  only as a constructor string.
