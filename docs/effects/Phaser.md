# Effects Dossier — `Phaser` (MXR Phase 90)

**Class:** `lib/audioeffects/modulation.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Modulation, roadmap Phase 3
**Standout:** MXR Phase 90, per vision §4.2 — **confirmed**. Four
first-order all-pass stages, one Speed knob, a JFET per stage as the
voltage-controlled resistor. Three independent published models of this exact
pedal were reached (S3, S4, S5), two carrying the component values and one
measured against a real unit. No swap argued.
**Grade:** **circuit** — schematic with values reached and read (S1, S3), the
traits derived analytically from it (Appendix A), cross-checked against a
second published derivation (S5) and against S1's own arithmetic to 0.2 %.
**Portability tier:** **stock** if Gate 0 keeps `audiofilters.Phaser`;
**needs audioif-own nodes** (a DC-clean all-pass cascade with unclamped
feedback) if Gate 0 takes ask A1 (§5). §4 says what each costs.
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

An op-amp follower lifts the signal onto a 5.1 V rail (R1 10 kΩ, C1 0.01 µF,
R2 470 kΩ — S3) and feeds **four identical first-order all-pass stages** (S1,
S3, S4, S5 all say four). Each is one op-amp with equal resistors around it
(R3 = R4 = 10 kΩ) and, on its non-inverting input, C2 = 47 nF from the
previous stage plus R5 = 24 kΩ to bias **in parallel with an n-channel JFET**
(2N5952) whose channel is the variable half of that resistance (S1, S3).
There is no clipper: **the nonlinearity is the JFET**, sitting inside the
element that sets the corner, so filter and distortion are the same
component. A stage's break frequency is ω_b = tan(φ/2)/((R5‖R_JFET)·C2)
(S3 eq. 10; S4 eq. 17; S1 as f = tan(φ/2)/(2πRC)), and because the ohmic
channel conductance goes as (V_gs − V_p), **1/(R5‖R_JFET) is affine in the
gate voltage** — S5's eq. 17. Four stages summed with the dry signal notch
where the cascade reaches 180° and 540°, i.e. where each stage gives 45° and
135°, so the notches sit at tan(22.5°)·f_b and tan(67.5°)·f_b and their
**ratio is fixed at 5.828** wherever the sweep goes. The one panel control,
Speed, is the resistor in a Schmitt-trigger/integrator relaxation oscillator
(C7 0.01 µF, R36 470 kΩ) whose **triangle** drives all four gates in parallel
(S1; "tenths of Hz to some Hertzs"); S3 models it as a 65 %-duty triangle,
S4 measured the real one with "slightly curved edges" and "the falling edge …
a little longer than the rising edge" (§8.2). The output sums dry and wet at
a PNP common-emitter's base through **equal 150 kΩ resistors** — S1: "This
last stage is a PNP Common Emitter Amplifier. Both signals are applied through
the base of Q1, the ratio of R8 and R16 (all same value) indicates that the
original and processed signals are mixed at 50%", with R8 and R16 both 150 K
in its parts list; S3 puts R6 = 150 kΩ in series with the dry input V1 and
with the wet input V2 of the same summing node — then a 22 Hz high-pass. Later "block logo" units add one
resistor, R28 = 24 kΩ (S1) / R15 (S4), from the last stage's output to the
**second** stage's inverting input; the 1974 script version has no feedback
at all. It "makes the effect stronger and more pronounced, causing boost and
even distortion in the midrange" (S1) — S4: "amplification of certain
frequencies [and] … harmonic distortion of the amplified frequencies".

## 2. Sources and license calls

Reached 2026-09-06 from this machine; nothing from memory. **Appendix C**
carries what each source gave, quoted, with the licence text as read.
Every row below was re-fetched and re-read by the licence-and-citation audit
of the same day; rows marked *(audit)* were added or rewritten by that pass,
and its corrections are listed at the end of this section.

| Source | License call | URL | Reached |
|---|---|---|---|
| S1. ElectroSmash, "MXR Phase 90 Analysis" (MAS Effects mirror) | The page carries a rights line … (App. S1) | https://electrosmash.mas-effects.com/mxr-phase90.html | yes (HTTP 200; re-fetched in both audit passes) |
| S2. ElectroSmash original host | — | https://www.electrosmash.com/mxr-phase90 | **no** — `getaddrinfo ENOTFOUND`, as on the TS808 run and re-tested in the second audit; the archived original is S10 |
| S3. Giampiccolo *et al.*, DAFx24 … (App. S3) | **CC BY 4.0**, stated on p.1 — permissive … (App. S3) | https://www.dafx.de/paper-archive/2024/papers/DAFx24_paper_13.pdf | yes (PDF, pypdf) |
| S4. Eichas, Fink, Holters, Zölzer, DAFx-14 … (App. S4) | No copyright or licence statement in the PDF … (App. S4) | https://dafx.de/paper-archive/2014/dafx14_felix_eichas_physical_modeling_of_the_.pdf | yes (PDF, pypdf) |
| S5. Huovilainen, DAFx-05, "Enhanced Digital Models for Analog … (App. S5) | No licence statement in the PDF … (App. S5) | https://www.dafx.de/paper-archive/2005/P_155.pdf | yes (PDF, pypdf) |
| S6. `polimi-ispl/mxrphase90` (S3's companion code) | Plug-in **CC BY-NC 4.0** … (App. S6) | https://github.com/polimi-ispl/mxrphase90 | yes (page only) |
| S7. R. G. Keen, GEOFEX, "The technology of Phase Shifters and Flangers" … (App. S7) | *"Copyright 1999 R.G.Keen. All rights … (App. S7) | http://www.geofex.com/Article_Folders/phasers/phase.html | yes (**plain HTTP only** — the https URL fails, which is the "connection reset" earlier runs recorded) |
| S8. Dunlop, "M101 Phase 90" product manual *(audit)* | Manufacturer product documentation … (App. S8) | https://www.jimdunlop.com/content/manuals/M101.pdf | yes (HTTP 200, PDF, pypdf) |
| S9. Central Semiconductor, "2N5949 2N5951 2N5952 2N5953 Silicon … (App. S9) | Manufacturer datasheet, no licence line … (App. S9) | https://my.centralsemi.com/datasheets/2N5949_SERIES.PDF | yes (HTTP 200, PDF, pypdf) |
| S10. ElectroSmash, "MXR Phase 90 Analysis" … (App. S10) | The rights line of S1 … (App. S10) | http://web.archive.org/web/20260514234042/https://www.electrosmash.com/mxr-phase90 | yes — **`curl` only**: `web.archive.org` is blocked for the fetch tool, and answers `curl` from this machine |
| Local: `audioif/src/audiofilters/Phaser.c`, `src/shared/audioif_phaser.c`, `src/synthio/{LFO.c,Biquad.c,__init__.h}`, `audiocomponents/lib/audioeffects/{modulation.py,_core.py}` | MIT | — | yes |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| P1 | **Four stages give exactly two notches, and the ratio of their centres is fixed.** At `Stages` 4, anywhere in §6's `Centre` × `Depth` range and at every `Feedback`: exactly two notches below Nyquist, and their ratio is tan(67.5°)/tan(22.5°) = **5.8284 (3052 cents)** within **30 cents in every analysis frame**. The ratio is the claim, not the pair's position — on the ported node feedback translates both by up to ~170 cents (B.3) and the ratio survives it, 4 cents off at feedback 0.9 (E1) | S1, S3, S4, S5, S7 … (App. P1) | high — topology … (App. P1) | a third notch below Nyquist at `Stages` 4; the ratio outside 30 cents in any frame; or a ratio drifting monotonically with `Feedback`, `Depth` or `Centre` | notch tracking: white-noise … (App. P1) |
| P2 | **The sweep is linear in hertz, not exponential.** At `Depth` 1 and `Shape` 0.5, over one monotone ramp with the turnarounds excluded: the ramp's mid-point f_b is within **50 cents** of the *arithmetic* mean of that ramp's **own measured endpoints** and at least **300 cents** from their geometric mean. Measured against the build's own span, never against a fixed 328–2998 Hz. Below a 4:1 span the two laws are too close to separate and the evidence pack records the measurement as inconclusive rather than passing it (E2) | S5 eq. 17; S3 eqs. 11/15 and Table 1 … (App. P2) | high — two … (App. P2) | a mid-ramp f_b nearer the geometric mean of its own endpoints than the arithmetic one; or an affine fit to log f_b(t) with a smaller RMS residual than the affine fit to f_b(t) | notch tracking as P1 at `Rate` … (App. P2) |
| P3 | **The low end is the fixed resistor, not the knob.** At the `Centre`/`Depth` that drive the model to pinch-off, notch 1's minimum over one LFO period is **58.4 Hz within 30 cents** (A), and **no** combination of `Centre`, `Depth` and `Rate` in §6's ranges puts notch 1 more than 30 cents below it. That floor moves less than 30 cents between `Rate` 0.2 and 2 Hz and between `Depth` 0.5 and 1 | S1 — its own arithmetic gives 58.5 / 340.8 … (App. P3) | high | notch 1 more than 30 cents below 58.4 Hz at any macro setting; or a floor that moves more than 30 cents with `Depth` or `Rate` | notch tracking at `Centre` … (App. P3) |
| P4 | **With no feedback the notch is a true null.** At `Feedback` 0, `Rate` 0 so the notch stands still, and `Mix` at the equal-weight position (§6 macro 4 = 0.5; on the ported node the node's `mix = 1.0`, which forms dry + `mix`·wet with a soft limit above ±28000, never a halving — `audioif_phaser.c:39-40` with `audioif_synth_dsp.c:20-28`, corrected and measured this run, §4): the deepest bin of \|H\| is at least **40 dB** below the mean of the same transfer over 100 Hz–8 kHz, read at **2.93 Hz** resolution (16384-point Hann, ≥ 2¹⁸ samples of white noise) | S1 — its mixing sentence re-read on the mirror this run: *"the ratio of R8 and R16 (all same value) indicates that the original and processed signals are mixed at 50%"*; S3 (R6 = 150 kΩ in series with both the dry input V1 and the wet input V2 of its output stage); S4 (dry summed with wet at Q5; the script version has no feedback); S7 ("perfect cancellation possible") | high for the topology; **medium for the 40 dB**, this seed's threshold and meaningful only at the stated resolution | a floor shallower than 40 dB at `Feedback` 0, `Rate` 0, equal weight, at 2.93 Hz resolution | notch depth as stated. **Control that must pass:** the same measurement at `Mix` 0 must read 0.0 dB everywhere (B.5) — a render that came back silent reads infinitely deep and must fail the pair |
| P5 | **Feedback raises a resonant peak between the notches.** At `Rate` 0 and fixed `Centre`, the gain at the inter-notch maximum rises **monotonically** across `Feedback` 0 / 0.3 / 0.5 / 0.7 and by at least **5 dB** end to end | S1, re-read on the mirror this run: *"Adding … (App. P5) | high — three sources … (App. P5) | a flat or non-monotonic inter-notch peak across `Feedback` | inter-notch peak gain … (App. P5) |
| P6 | **The sweep trajectory is piecewise linear — a triangle, not a sine.** At `Shape` 0.5, a straight-line fit to f_b(t) over the middle 80 % of each monotone ramp leaves an RMS residual under **1 % of the peak-to-peak span**; a half-cosine of the same period and endpoints leaves 2.29 % over the same window (E3). The middle-80 % window is what allows S4's measured "slightly curved edges" without weakening the test | S1 (Schmitt-trigger/integrator: *"the output … (App. P6) | high for … (App. P6) | an RMS residual over 1 % of span in the linear window, or a trajectory whose best straight line is no better than a half-cosine's | LFO extraction: notch-centre … (App. P6) |
| P7 | **The stage is level-dependent: it makes harmonics that grow with level.** At `Drive` 0.5, `Rate` 0, `Mix` at equal weight, a 1 kHz tone: h2+h3 re the fundamental rises **monotonically** across −40 / −20 / −6 dBFS and by at least **10 dB** end to end. At `Mix` 0 the class is a wire and it is gone | S3 eq. 15 (the −v_ds/2 term) … (App. P7) | medium — mechanism … (App. P7) | h2+h3 flat within 3 dB across the three levels, or non-monotonic | harmonic spectrum at level: … (App. P7) |
| P8 | **Does feedback fill the notches, or keep them?** From `Feedback` 0 to 0.7 at `Rate` 0 the notch floor rises by at least **10 dB**, monotonically. **This is the one row whose own sources contradict it,** and the measurement is run to settle which reading is right, not to confirm this one | **No reached source supports it and two … (App. P8) | **low** — split out … (App. P8) | a floor that holds within 3 dB as `Feedback` rises — **the sources agreeing and this row disconfirmed**, a legitimate result (vision §3) that points the rebuild at the stages-2–4 loop | notch depth (dB re the wideband … (App. P8) |
| P9 | **The ramp asymmetry is a control, and it reaches the duty S3 documents.** The two ramp durations differ by (2·`Shape` − 1) of the period within **2 % of the period** across `Shape` 0.35 → 0.65, monotonically, and are equal within 2 % at `Shape` 0.5. Corroborated by h2, absent at 0.5 and rising monotonically with \|`Shape` − 0.5\| (E4) | **Unmeasured as a circuit trait: the pedal's own asymmetry has no sourced magnitude or sign.** S3's 65 % is the duty *it chose for its own LTspice/WDF test* (re-read this run), not a measurement of a unit; S4's is qualitative ("the falling edge is a little longer than the rising edge") and disagrees with S3 in direction (§8.2). The row fixes what the class's control must do and asserts nothing about the circuit | n/a — **a surface requirement, not a circuit trait**, labelled so it cannot be counted as one | ramp durations that do not track `Shape`, or that differ by more than 2 % of the period at `Shape` 0.5 | LFO extraction as P6: ramp durations at `Shape` 0.35 / 0.5 / 0.65 as a fraction of the period, plus h2 of the trajectory |
| P10 | **The notch centre moves with input level.** At a held `Centre`, `Rate` 0 and `Drive` 0.5, the notch-1 centre at −6 dBFS differs from the centre at −40 dBFS by more than **30 cents** — P1's own tracker tolerance, so the claim is exactly "the shift is larger than the instrument that measures it" | S3 eq. 15 — R_ohm carries a −v_ds/2 term … (App. P10) | low. **Unmeasured as … (App. P10) | the two centres agreeing within 30 cents | notch tracking at −40 and −6 … (App. P10) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose first.** `audiofilters.Phaser` is a first-order all-pass cascade
with feedback (`audioif_phaser.c:24-41`) and already carries P1 exactly — the
notch ratio is topology. Its `frequency` argument is **not** the notch
frequency: the coefficient is `(1 − f/nyquist)/(1 + f/nyquist)`
(`Phaser.c:225`, `audioif_phaser.c:14`), so a stage's −90° point sits at
(fs/π)·atan(2f/fs). The class therefore computes in Python, per macro move,
(1) f_b from P2's affine law with Appendix A's constants, `Centre` and
`Depth` moving V_g, then (2) the pre-warp `f_req = (fs/2)·tan(π·f_b/fs)`,
clamped below Nyquist (`Phaser.c:210` clamps again). **Verified this run**
(B.2, re-run at feedback 0 through the shared kernel in F.1): at
`frequency=500` the measured notches are 131.8 / 770.5 Hz against 131.8 /
768.4 predicted; at 1100, 290.0 / 1684.6 against 289.9 / 1689.4.
Coefficient and shape tables are computed on CPython and shipped as data.

What the ported node cannot do, all measured this run:

- **P4 is unreachable *through the node*.** `feedback` is clamped to …  *(argument in full: App. R)*
- **Tier 1 silence fails.** Burst then 500 ms of silence leaves **all of the …  *(argument in full: App. R)*
- **Control is block-rate, capped at 256 frames** whatever `buffer_size` says …  *(argument in full: App. R)*
- **16-bit with per-stage saturation** (`audioif_phaser.c:28-37`), so P7's
  level dependence would be the node's clipping, not the JFET's law.
- `mix` clamps at 1.0 (`Phaser.c:212`): 1.0 and 2.0 render byte-identically …  *(argument in full: App. R)*

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**A1 — a DC-clean first-order all-pass cascade in an audioif-own module,
per-sample coefficient, unclamped feedback including zero and negative.**
Unblocks **P4** (feedback must reach 0 for the script null) and the **Tier 1
silence invariant** (the −6 / −10 LSB hold), and tightens **P2/P6**. This is
the same node decision Gate 0 already reserves (audioif#23, plus "a
per-sample phaser … only if the measurement shows the ported node's
block-rate stepping, or that the pre-warped control law or the `0.1..0.9`
feedback clamp leaves a Phase 90 trait unreachable"). The measurements that
decide it are B.1, B.3, B.4 and F.1–F.5.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Ten macros, all `UNIPOLAR` unless marked. `capabilities = ("tempo_sync",)` —
the class reads `transport()` for macros 8–9 (D10: an LFO-driven modulation
class is exactly the candidate the roadmap names).

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Rate` | UNIPOLAR | 0.05–10 Hz, log | the Speed knob |
| 1 | `Depth` | UNIPOLAR | 0–1 of the gate swing | the internal LFO-swing trimmer |
| 2 | `Centre` | UNIPOLAR | notch 1 at mid-sweep, 60 Hz–2 kHz, log | the bias trimmer |
| 3 | `Feedback` | UNIPOLAR | 0–0.9, default 0 | R28 / R15; 0 is the script topology |
| 4 | `Mix` | UNIPOLAR | 0–1, default 0.5 | the pedal's fixed equal sum; 0 is a wire |
| 5 | `Stages` | UNIPOLAR | quantised 4/6/8/10/12, default 4 | the pedal has none; the vision allows more |
| 6 | `Shape` | UNIPOLAR | ramp duty 0.35–0.65, default 0.5 | the LFO's ramp asymmetry (P6) |
| 7 | `Drive` | UNIPOLAR | 0–1, default 0.3 | how hard the stage's own nonlinearity works (P7) |
| 8 | `Sync` | TOGGLE | off / on | tempo-locks Rate to the transport |
| 9 | `Division` | UNIPOLAR | quantised 4, 2, 1, ½, ⅓, ¼, ⅛ bars | the sync division; ignored when Sync is off |

No characters — one circuit, one trait set.

**Patches:** 0 `Four stage, no feedback`; 1 `Four stage with resonance`;
2 `Slow wide sweep`; 3 `Fast tight sweep`; 4 `Six stage deep`; 5 `Held notch
pair` (Rate 0; `Centre` positions it); 6 `Bass-safe shallow`; 7 `Synced half
bar`.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/modulation.py`. Nothing else is carried.

1. **No surface.** `MACRO_LABELS = ()` (`:68`), `MACRO_MODES = {}` (`:69`),
   `PATCHES = {0: ("Default", ())}` (`:70`) — nothing a host can turn.
2. **Six stages, three notches** (`:71`) where the standout is four/two, and
   `stages` is a constructor argument no host can reach.
3. **The constructor's numbers do not mean what they look like.** The LFO is …  *(argument in full: App. R)*
4. **Feedback 0.5 by default** (`:72`) fills the notches to about −9.6 dB
   (B.3) — the shipped default is the shallow one.
5. **A DC residue that never decays**: −6 LSB for ever after silence at these
   exact settings (B.1).
6. **Nothing declared** — no `CAPABILITIES`, `LATENCY_SAMPLES` or …  *(argument in full: App. R)*
7. **`reset()` and `deinit()` reach one node** — `_core.py:366-374` and …  *(argument in full: App. R)*
8. **The sample rate comes from module state** (`_core.pcm()`,
   `_core.py:64-72`), not from the factory.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **The Speed knob's range in Hz** — unsourced (§2). The macro's 0.05–10 Hz
   is this seed's choice. *Settles:* Phase 3, from S1's integrator values if
   the hysteresis resistors can be read off the drawing; otherwise it stays a
   design choice and the dossier says so.
2. **Which LFO ramp is longer, and by how much** — neither is sourced for the
   pedal. S3's 65 % duty is the LFO *it set in its own LTspice/WDF test*, not a
   measurement of a unit; S4's "the falling edge is a little longer than the
   rising edge" is qualitative and points the other way. **P9** therefore
   carries the `Shape` control as a surface requirement and asserts nothing
   about the circuit; **P6** carries triangle-not-sine, which is sourced.
   *Settles:* Phase 3, or stays open with the symmetric default.
3. **A1's fate** — the same decision Gate 0 owns for audioif#23. This seed
   supplies the Phaser configuration's settled-state number (−6 LSB) that the
   Gate 0 item asks for. *Settles:* Gate 0.
4. **Stereo spread** — two nodes in quadrature behind a `Splitter` double the
   cost for something the pedal never had. *Settles:* Phase 3, on cost.
5. **P7's oversampling factor**, and whether the level-dependent stage earns
   its cost on the S3. *Settles:* Phase 1's oversampling table, then Phase 3.
6. **Which `Mix` position is equal weight** *(trait critic, 2026-09-06;
   answered by the palette verifier the same day)*. §6 gives `Mix` as
   "0–1, default 0.5"; on `audiofilters.Phaser` the node forms
   **dry + `mix`·wet** — `audioif_mix_down_sample(word, 2, …)` at
   `audioif_phaser.c:39-40` is a soft limiter above ±28000, not a halving
   (`audioif_synth_dsp.c:20-28`), and the measured low-frequency gain at
   `mix = 1.0` is 1.666× rather than 0.84× (§4, F.2). So the pedal's equal sum
   **is** the node's `mix = 1.0`, wet-only is unreachable because `mix` clamps
   at 1.0 (`Phaser.c:212`, byte-identical at 1.0 and 2.0, F.3), and the class
   owes an output trim the Tier 1 level-honesty invariant can pass. **P4's
   40 dB null depends on this mapping**; §4 now states it. *Settles:*
   Station A, in §4 — the open half is only the trim, not the mapping.

---


## Appendix

### A. The affine sweep law, derived

Two published forms agree. S5 eq. 17, for a JFET all-pass with R_p in
parallel:

    f_c = [ 1/R_p + (2·I_DSS/V_p²)·(V_g − V_p) ] / (2π·C)

S3 gives the same in two pieces — eq. 10, ω_b = tan(φ/2)/((R5‖R_JFET)·C2),
and eq. 15, R_ohm = V_p²/(2·I_S0·(v_gs − V_p − v_ds/2)). Drop the v_ds/2 term
(that term *is* P7), take the parallel combination, and S5's form falls out.

With S3 Table 1 for the 2N5952 (V_p = −2.021 V, I_S0 = 5.367 mA) and S1/S3's
stage values (R5 = 24 kΩ, C2 = 47 nF): k = 2·I_S0/V_p² = 2.628 mS/V.

| V_gs (V) | r_DS (Ω) | R5‖r_DS (Ω) | f_b (Hz) | notch 1 | notch 2 |
|---|---|---|---|---|---|
| −2.021 (pinch-off) | ∞ | 24000 | 141.1 | 58.4 | 340.6 |
| −2.000 | 18120 | 10325 | 328.0 | 135.9 | 791.8 |
| −1.925 | 3964 | 3402 | 995.4 | 412.3 | 2403.2 |
| −1.850 | 2225 | 2036 | 1662.9 | 688.8 | 4014.5 |
| −1.775 | 1547 | 1453 | 2330.3 | 965.2 | 5625.8 |
| −1.700 | 1185 | 1130 | 2997.7 | 1241.7 | 7237.2 |
| 0 (full on) | 188 | 187 | 18126 | 7508 | 43761 |

Over S3's stated LFO (offset 3.25 V, amplitude 0.15 V against V_ref 5.1 V,
i.e. V_gs = −2.00 … −1.70): f_b = **328.0 … 2997.7 Hz**, 3.19 octaves; notch 1
135.9 … 1241.7 Hz, notch 2 791.8 … 7237.2 Hz. Mid-ramp is **1662.9 Hz** — the
arithmetic mean (1662.9), not the geometric mean (991.6): the **895 cents**
of P2. Cross-check for P3: the pinch-off row gives 58.4 / 340.6 Hz where S1's
own arithmetic gives 58.5 / 340.8 — 0.2 %, by an independent route from the
same two component values. Notch ratio tan(67.5°)/tan(22.5°) = **5.8284** =
2.543 octaves = 3052 cents.

### B. Probes run in this session

CPython, `audiocomponents/.venv/bin/python` against audioif's CPython build,
48 kHz stereo 16-bit signed.

**B.1 — the DC hold.** `audiofilters.Phaser(frequency=1100.0, feedback=0.5,
stages=6, mix=0.6)` — the current class's shipped settings — fed 100 ms of a
20000-LSB 1 kHz tone then 500 ms of digital silence. Last 8000 samples:
min −6, max −6, non-zero 8000 of 8000. The tail never reaches zero.
(audioif#23's own comment reports −4 LSB at *its* Phaser configuration; the
difference is configuration, which is why Gate 0 asks for the number per
shipped configuration.)

**B.2 — the pre-warp.** White noise in, magnitude ratio averaged over
2¹⁶ samples in 16384-point Hann segments; `stages=4, feedback=0.1, mix=1.0`.

| `frequency=` | predicted f_b | predicted notches | measured notches |
|---|---|---|---|
| 500 | 318.3 Hz | 131.8 / 768.4 Hz | **131.8 / 776.4 Hz** |
| 1100 | 699.8 Hz | 289.9 / 1689.4 Hz | **290.0 / 1693.4 Hz** |
| 4000 | 2523.3 Hz | 1045.2 / 6091.8 Hz | **≈5988 Hz** (upper only resolved) |

*These rows were taken at the node's minimum `feedback` of 0.1, which
translates the pair (B.3); F.1 repeats the 500 and 1100 rows through the
shared kernel at feedback exactly 0 and lands on 131.8 / 770.5 and
290.0 / 1684.6, closer to the prediction on the upper notch. The two tables
agree; they are different feedback settings.*

**B.3 — feedback fills the notches** (`frequency=1100, stages=4, mix=1.0`):

| feedback | notch 1 | notch 2 | peak between |
|---|---|---|---|
| 0.00 | −21.1 dB @ 290.0 Hz | −21.3 dB @ 1693.4 Hz | +6.5 dB @ 700.2 Hz |
| 0.10 | −21.1 dB @ 290.0 Hz | −21.3 dB @ 1693.4 Hz | +6.5 dB @ 700.2 Hz |
| 0.30 | −12.8 dB | −13.0 dB @ 1740.2 Hz | +7.7 dB |
| 0.50 | −9.6 dB | −9.9 dB @ 1816.4 Hz | +9.6 dB |
| 0.70 | −7.9 dB | −8.4 dB @ 1869.1 Hz | +12.8 dB |
| 0.90 | −8.4 dB @ 316.4 Hz | −10.1 dB @ 1848.6 Hz | +21.0 dB |
| 1.00 | −8.4 dB @ 316.4 Hz | −10.1 dB @ 1848.6 Hz | +21.0 dB |

0.00 ≡ 0.10 and 0.90 ≡ 1.00: the `0.1 .. 0.9` clamp at `Phaser.c:211`, seen
from outside. Note also that the node's feedback wraps **all four** stages
(`audioif_phaser.c:28-29, 38`) where the pedal's wraps stages 2–4 (S3, S4) —
which is why the notch centres move up to ~170 cents with feedback here. The
rebuild's own topology decides whether that is kept.

**B.4 — block-rate stepping.** 1 kHz tone, `synthio.LFO` on `frequency`
sweeping f_b 328–2998 Hz, `stages=4, feedback=0.1, mix=1.0`; spurious energy
200 Hz–4 kHz excluding ±20 Hz around the carrier, re carrier:

| control update | 5 Hz sweep | 0.2 Hz sweep |
|---|---|---|
| 64 frames (750 Hz) | −15.9 dB | **−64.8 dB** |
| 128 frames (375 Hz) | −15.8 dB | −60.0 dB |
| 256 frames (187.5 Hz) | −15.2 dB | **−53.9 dB** |
| 1024 frames | −15.2 dB | −53.9 dB |
| 4096 frames | −15.2 dB | −53.9 dB |

At 5 Hz the figure is dominated by the legitimate modulation sidebands and
says nothing. At 0.2 Hz it is the staircase, improving ~6 dB per halving of
the update interval — until 256 frames, past which nothing changes because
`Phaser.c:204` caps the update at `SYNTHIO_MAX_DUR` = 256 frames whatever
`buffer_size` says.

**B.5 — the wire.** At `mix=0.0`, max |output − input| over 2¹⁶ samples is
**0.0** (`Phaser.c:214` copies through below mix 0.01).

### C. What each source gave

**S1 (ElectroSmash mirror).** Four stages / two notches ("2 stages = 1 notch,
4 stages = 2 notches"); R 24K at R6, R23, R25, R26, R28; C 47 nF; 2N5952
("The rDS values are normally between some hundred ohms to some megaohms");
TL061/UA741CP op-amps; f = tan(φ/2)/(2πRC) with the two notches worked at
58.5 and 340.8 Hz; LFO "based in a Schmitt Trigger - Integrator modified
topology", C7 0.01 µF ramping, R36 470 K as the speed resistor, "the output
of the op-amp creates a square waveform while at the 'OUT' point is the
triangular LFO signal", swing "from 5.1V to 3.8V/1.6V (depending on the FET
batch cut-off voltage)", "tenths of Hz to some Hertzs"; input buffer C5
0.01 µF / R14 470 K, 33 Hz; output mixer Q1 2N4125 PNP with R2/R8/R16 150 K —
"the original and processed signals are mixed at 50 %" — and the output
high-pass C2·R2, 22 Hz (C2 is 47 nF in S1's own parts list; 15 µF is C8/C10,
and 22 Hz with R2 = 150 K needs 47 nF — corrected by the second audit);
R28 "makes the effect stronger and more pronounced, causing boost and even
distortion in the midrange", routed "back … to the 1st, 2nd (default in MXR
Phase 90), 3rd and 4th stage"; "The first Script Logo units do not include
this component, later schematics (Block Logo) added it".

**S3 (DAFx24).** Input R1 10 kΩ, C1 0.01 µF, R2 470 kΩ, V_ref 5.1 V. Stage
R3 = R4 = 10 kΩ, C2 = 47 nF, R5 = 24 kΩ, JFET Q1 in parallel with R5; eq. 8/9
the digital all-pass, eq. 10 ω_b = tan(φ_ss/2)/((R5‖R_JFET)C2), "for the
considered phaser pedal, F = 4 holds true"; eqs. 11/15/16 the JFET's ohmic
and saturation regions; Table 1, 2N5952: V_p = −2.021 V, I_S0 = 5.367 mA,
λ = 4×10⁻³. Output C3 47 nF, R6 150 kΩ, R7 56 kΩ, high-pass 22 Hz, PNP
omitted as negligible. "we aim at modeling the first version … 1974 … the
first lacks a feedback resistor (or potentiometer) that connects the negative
terminal of the second unit opamp to the output of the last unit". Their
LTspice/WDF test: "the LFO equal to a triangular wave with an offset of
3.25 V, an amplitude of 0.15 V, a fundamental frequency of 2 Hz, and a duty
cycle of 65 %".

**S4 (DAFx-14).** Eq. 17 f_c = 1/(2π(R_fix‖R_JFET)C_fix), R_fix =
[R5, R8, R11, R14], C_fix = C2..C5 at the (+) input; "the amount of spectral
notches is half the number of used allpass stages … The Phase90 circuit
contains 4 stages and hence, two notches"; V_lift ≈ 5 V from the zener;
"The resistance R15 introduces a feedback in the allpass cascade which leads
to an amplification of certain frequencies. This resonance introduces a
harmonic distortion of the amplified frequencies"; the 1974 script version
"did not include the feedback path with resistor R15"; "signal (A) is added
to signal (B) at the base of the PNP-BJT Q5". Measured against a real unit:
Fig. 6, output spectrum for a 1 kHz 1 V input; Figs. 7–8, noise spectrograms
at maximum and minimum speed showing two notch lines; "the output voltage of
the LFO was approximated by a triangular function while the actual LFO output
voltage has slightly curved edges and the falling edge is a little longer
than the rising edge"; "it was important to use a matched set of four JFETs
… an unmatched set … would not have the same operating point and thus the
allpass-filters would not be tuned correctly".

**S5 (DAFx-05).** "Analog phasers have four or more first-order allpass
filters connected in series whose output is mixed with the input. Each
allpass filter generates a total phase shift of 180 degrees, producing one
notch for every two stages"; "Later in the 70s, Field Effect Transistors
(FETs) were used as voltage controlled resistors in units such as MXR
Phase90"; Fig. 4 the JFET stage with R_p in parallel "to ensure that the
signal is never completely cut off"; eqs. 9a/9b the JFET I–V; eq. 17 the
affine centre-frequency law; Fig. 5 the transfer curve, Fig. 7 the harmonics
the nonlinearity makes.

### D. Scripts

`probe_phaser.py` (B.1), `probe_notch.py` (B.2), `probe_fb.py` (B.3, B.5),
`probe_step.py` (B.4) and `p90_math.py` (Appendix A) were written and run in
this session's scratchpad. Station A re-writes them under
`audiocomponents/tools/` as part of the measurement kit (notch tracking, LFO
extraction, harmonic spectrum at level, silence-after-burst) so the dossier's
numbers and the evidence pack's come from one piece of arithmetic.

### E. Trait-critic calibration (2026-09-06)

Arithmetic run this session under `audiocomponents/.venv` (numpy); every figure
is reproducible from the statement beside it, and no source is cited here that
this run did not reach.

**E1 — the notch ratio survives feedback.** B.3's feedback-0.9 pair, 316.4 and
1848.6 Hz, is a ratio of 5.843 — **4 cents** from tan(67.5°)/tan(22.5°) =
5.8284. The pair translates by up to ~170 cents under the ported node's
all-four-stage loop; the ratio does not. P1's 30-cent tolerance is therefore not
endangered by that loop, which is why the row can claim the ratio "at every
`Feedback`" while B.3 shows the centres moving.

**E2 — arithmetic versus geometric mean, and where the test stops working.**
For a sweep linear in Hz the mid-ramp value is the arithmetic mean of the
endpoints. The two means are **386 cents** apart over a 4:1 span and **895
cents** over S3's 328–2998 Hz (9.14:1); over a 2:1 span only **102 cents**. A
least-squares affine fit to log f over the S3 span leaves an RMS residual of
**257 cents** (max 920); over 4:1, **114 cents** (max 341). Below about 2.5:1
the two laws are inside P2's own tolerances of each other, which is why P2
states its span condition instead of passing quietly on a short sweep.

**E3 — piecewise linearity versus a sine.** Straight-line fit over the middle
80 % of one monotone ramp, residual as a fraction of the peak-to-peak span: an
exact triangle leaves **0.00 %**; a half-cosine with the same endpoints leaves
**2.29 % RMS, 5.89 % max**. Over the *whole* ramp the half-cosine leaves 4.26 %
RMS. P6's 1 % threshold sits between them with a factor of 2.3 in hand and the
middle-80 % window keeps S4's curved turnarounds out of the fit.

**E4 — why h3 cannot be P6's criterion, and what h2 does instead.** Third
harmonic of an ideal duty-D ramp, period-aligned FFT over 8 periods, re its
fundamental: D = 0.5 → **−19.1 dB**; 0.55 → −20.0; 0.60 → −23.3; **0.65 →
−34.2**; 0.75 → −19.1; a sawtooth → −9.5. h3 passes through a null near ⅔ duty,
so the seed's earlier *"the trajectory's h3 is above −25 dB re its fundamental"*
would have been **failed by exactly the 65 %-duty triangle S3 documents** — a
threshold that rejects the shape it was written to assert. h2 is the monotone
measure of ramp asymmetry and is what P9 uses: absent at D = 0.5, **−22.1 dB**
at 0.55, −16.2 at 0.60, **−12.9 dB** at 0.65.

### F. Palette-verifier probes (2026-09-06)

Run by the palette verifier against the CPython build of audioif under
`audiocomponents/.venv/bin/python`, 48 kHz stereo 16-bit signed. Every claim
in §4 and §5 about what `audiofilters.Phaser` can and cannot do was checked
against the C first (`audioif/src/shared/audioif_phaser.c`,
`audioif/src/audiofilters/Phaser.c`, `audioif/src/synthio/Biquad.c`,
`audioif/src/synthio/__init__.h`) and then probed.

**F.1 — the notch floor at feedback exactly 0, through the shared kernel.**
The node cannot be given feedback 0 (`Phaser.c:211`), so the same kernel was
driven directly through `_audioif.phaser_s16` — the entry point
`audioif/src/cpython/audiofilters.py:231-237` uses — in 256-frame calls, white noise, 2¹⁸ samples,
16384-point Hann, `frequency=1100, stages=4, mix=1.0`:

| feedback | deepest notch, dB re the 100 Hz–8 kHz mean |
|---|---|
| **0.00** | **−49.2** |
| 0.05 | −28.5 |
| 0.10 (the node's floor) | −23.0 |
| 0.30 | −15.2 |

P4's bar is 40 dB. **Sixteen-bit arithmetic clears it by 9 dB; the clamp is
what does not.** The pre-warp holds at feedback 0 as well: `frequency=500`
predicts 131.8 / 768.4 Hz and measures 131.8 / 770.5; `frequency=1100`
predicts 289.9 / 1689.4 and measures 290.0 / 1684.6. One caveat the class
gate should carry: at feedback 0 the two notches are **not** equally deep —
−27.5 and −41.2 dB absolute at `frequency=500`, −36.6 and −47.4 at 1100 — so
P4's "deepest bin" wording is the reachable claim and "both notches" would
not be.

**F.2 — the node sums, it does not average.** 100 Hz tone at 8000 LSB,
`frequency=1100, stages=4, feedback=0.1, mix=1.0`: output peak **13328**
against the input's 8000, a ratio of **1.666**. Four first-order all-pass
stages at f_b = 699.8 Hz rotate 100 Hz by −65.0°, so a dry sum predicts
2·cos(32.5°) = **1.687** and a `(dry + wet)/2` node would predict 0.84.
`audioif_mix_down_sample(word, 2, -28000, 28000)` returns its argument
unchanged inside ±28000 (`audioif_synth_dsp.c:20-28`); the `2` is the
compression slope outside the range, not a divisor.

**F.3 — the clamps, seen from outside as byte-identity.** White noise, 4096
frames, `frequency=1100, stages=4`, renders compared byte for byte:
`feedback` 0.0 ≡ 0.1 and 0.9 ≡ 1.0 (`Phaser.c:211`); `mix` 1.0 ≡ 2.0
(`Phaser.c:212`); `mix` 0.0 and 0.009 both return the source **unchanged**,
max |out − in| = 0 (`Phaser.c:214`, `audioif_phaser.c:12`, `:23`).

**F.4 — the DC hold at the seed's own configuration.** 100 ms of a
20000-LSB 1 kHz tone then 500 ms of digital silence. `stages=6, feedback=0.5,
mix=0.6, frequency=1100` (the current class's settings) holds **−6** on all
16000 of the last 8000 frames, reproducing B.1; `stages=4, feedback=0.1,
mix=1.0` — this seed's own configuration — holds **−10**. Gate 0's audioif#23
item wants the number per shipped configuration: these are two of them.

**F.5 — can a downstream high-pass clean it?** The same probe with
`audiofilters.Filter` on a `synthio.Biquad` HIGH_PASS (Q 0.707) after the
phaser, held value over the last 8000 frames:

| high-pass corner | held value |
|---|---|
| none | −6 |
| 20 Hz | **+18** |
| 40 Hz | +4 |
| 60 Hz | +2 |
| 80 Hz | +1 |
| 100 Hz | +1 |
| **120 Hz and above** | **0** |

At this seed's `stages=4, feedback=0.1, mix=1.0` the crossing is the same:
−10 with no filter, −1 at 100 Hz, 0 at 150 Hz and above. The only corners
that reach exact zero sit above the 58.4 Hz floor P3 is a claim about. A
control in the same run: `audiofilters.Filter` alone on a NOTCH biquad at
290 Hz and at 1690 Hz settles to exact zero, so the residue is the phaser's
state and #23 is configuration-dependent, not universal to fixed point.

*Scripts:* written and run in this session's scratchpad. Station A folds them
into `audiocomponents/tools/` with B's, so the dossier's numbers and the
evidence pack's come from one piece of arithmetic.

<!-- author: phaser-flanger unit, effects Phase 0, 2026-09-06. S1, S3-S6
reached this run; S2 recorded as not reached. Every measurement in Appendix B
was taken this run on the CPython build of audioif.
Trait-critic pass, same day: Tier 2 rewritten in place (7 rows -> 10), Appendix E
added. Palette-verifier pass, same day: every node claim in SS4 and SS5 checked
against the C and probed; the (dry+wet)/2 reading corrected, the SYNTHIO_MAX_DUR
citation corrected to synthio/__init__.h:126, A1 restated as unclamped rather
than float-because-P4, two refutations added (a downstream high-pass, a biquad
NOTCH pair), Appendix F added. Sources re-reached in that pass and not taken from the draft: the
ElectroSmash mirror (S1) and the DAFx24 PDF (S3), both fetched and read again;
every other row's citation is left exactly as the audits recorded it. -->

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

*Rate note:* P1 and P3 hold at 22.05 kHz; P2's upper end does not — notch 2
reaches Nyquist before the sweep does, so `Centre` clamps and the stated span
shortens. That is the clamp the invariant asks for, not a refusal.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | License call | URL | Reached |
|---|---|---|---|
| S1. ElectroSmash, "MXR Phase 90 Analysis" (MAS Effects mirror) | The page carries a rights line, read verbatim: *"Some Rights Reserved, you are free to copy, share, remix and use all material. Trademarks, brand names and logos are the property of their respective owners."* But it is served by a repackager — *"An unofficial, non-commercial backup of ElectroSmash.com … All content and images belong to their original authors/owners"* — and electrosmash.com does not resolve (S2). The second audit closed that gap the other way: the **same rights line stands on ElectroSmash's own page** in an Internet Archive capture (S10), so it is the rights holder's own line and not the mirror's addition. It still names no licence, no version and no commercial term, and the site's own "Rights" footer licenses only Bootstrap and Font Awesome — so the call is unchanged: **licence unverified — treated as copyleft.** Nothing is reproduced; **a schematic on a hobby site is a document** (vision §5), read for topology and values | https://electrosmash.mas-effects.com/mxr-phase90.html | yes (HTTP 200; re-fetched in both audit passes) |
| S2. ElectroSmash original host | — | https://www.electrosmash.com/mxr-phase90 | **no** — `getaddrinfo ENOTFOUND`, as on the TS808 run and re-tested in the second audit; the archived original is S10 |
| S3. Giampiccolo *et al.*, DAFx24, "Wave Digital Model of the MXR Phase 90 …" | **CC BY 4.0**, stated on p.1 — permissive; math re-derived here, no code taken | https://www.dafx.de/paper-archive/2024/papers/DAFx24_paper_13.pdf | yes (PDF, pypdf) |
| S4. Eichas, Fink, Holters, Zölzer, DAFx-14, "Physical Modeling of the MXR Phase 90 …" | No copyright or licence statement in the PDF — unverified, **read as a paper** (vision §5) | https://dafx.de/paper-archive/2014/dafx14_felix_eichas_physical_modeling_of_the_.pdf | yes (PDF, pypdf) |
| S5. Huovilainen, DAFx-05, "Enhanced Digital Models for Analog Modulation Effects" | No licence statement in the PDF — unverified, read as a paper | https://www.dafx.de/paper-archive/2005/P_155.pdf | yes (PDF, pypdf) |
| S6. `polimi-ispl/mxrphase90` (S3's companion code) | Plug-in **CC BY-NC 4.0**, no licence file for the repo code. Non-commercial ⇒ **not permissive**: not ported, not read for structure; nothing taken | https://github.com/polimi-ispl/mxrphase90 | yes (page only) |
| S7. R. G. Keen, GEOFEX, "The technology of Phase Shifters and Flangers" *(audit)* | *"Copyright 1999 R.G.Keen. All rights reserved. No portion of these materials may be reproduced without written permission of the author."* — all rights reserved, read as a document, nothing reproduced | http://www.geofex.com/Article_Folders/phasers/phase.html | yes (**plain HTTP only** — the https URL fails, which is the "connection reset" earlier runs recorded) |
| S8. Dunlop, "M101 Phase 90" product manual *(audit)* | Manufacturer product documentation, no licence line — quoted as facts about the panel | https://www.jimdunlop.com/content/manuals/M101.pdf | yes (HTTP 200, PDF, pypdf) |
| S9. Central Semiconductor, "2N5949 2N5951 2N5952 2N5953 Silicon N-Channel JFETs", rev. R1 (25-April-2018) *(audit)* | Manufacturer datasheet, no licence line — **ten numbers are facts about a part**: transcribed into our own text with the URL cited, the file itself not redistributed (the rule the TS808 run set for SPICE models). *(Second audit, narrowed:* no **content** licence anywhere on the sheet; its only terms link is a Terms & Conditions of **Sale** page, https://www.centralsemi.com/terms, HTTP 200 this run, which grants nothing over the document.*)* | https://my.centralsemi.com/datasheets/2N5949_SERIES.PDF | yes (HTTP 200, PDF, pypdf) |
| S10. ElectroSmash, "MXR Phase 90 Analysis" — Internet Archive capture `20260514234042` of the original host *(second audit)* | The rights line of S1, read on **electrosmash.com's own page**: *"Some Rights Reserved, you are free to copy, share, remix and use all material. Trademarks, brand names and logos are the property of their respective owners."* The site's own "Rights" footer licenses only Bootstrap (MIT) and Font Awesome (SIL OFL 1.1) and says nothing about the articles. No named licence ⇒ treatment unchanged: read as a document, nothing reproduced | http://web.archive.org/web/20260514234042/https://www.electrosmash.com/mxr-phase90 | yes — **`curl` only**: `web.archive.org` is blocked for the fetch tool, and answers `curl` from this machine |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| P1 | **Four stages give exactly two notches, and the ratio of their centres is fixed.** At `Stages` 4, anywhere in §6's `Centre` × `Depth` range and at every `Feedback`: exactly two notches below Nyquist, and their ratio is tan(67.5°)/tan(22.5°) = **5.8284 (3052 cents)** within **30 cents in every analysis frame**. The ratio is the claim, not the pair's position — on the ported node feedback translates both by up to ~170 cents (B.3) and the ratio survives it, 4 cents off at feedback 0.9 (E1) | S1, S3, S4, S5, S7 — all state one notch per two stages (S7: "Each pair of stages adds one more notch"; S1's own 58.5 and 340.8 Hz are in that ratio). S3 re-read this run: *"for the considered phaser pedal, F = 4 holds true"* | high — topology, not a component value | a third notch below Nyquist at `Stages` 4; the ratio outside 30 cents in any frame; or a ratio drifting monotonically with `Feedback`, `Depth` or `Centre` | notch tracking: white-noise transfer, 16384-point Hann segments (2.93 Hz bins at 48 kHz), both centres per frame over one LFO period at `Rate` 0.5 Hz; ratio per frame in cents; repeated at `Feedback` 0 / 0.5 / 0.9. **Control that must pass:** `Stages` 6 must show three notches |
| P2 | **The sweep is linear in hertz, not exponential.** At `Depth` 1 and `Shape` 0.5, over one monotone ramp with the turnarounds excluded: the ramp's mid-point f_b is within **50 cents** of the *arithmetic* mean of that ramp's **own measured endpoints** and at least **300 cents** from their geometric mean. Measured against the build's own span, never against a fixed 328–2998 Hz. Below a 4:1 span the two laws are too close to separate and the evidence pack records the measurement as inconclusive rather than passing it (E2) | S5 eq. 17; S3 eqs. 11/15 and Table 1 — S3's R5 = 24 kΩ, C2 = 47 nF and eq. 10 for ω_b re-read this run. **Audit note kept:** 328–2998 Hz is a *typical-unit* figure (S9's 2:1 I_DSS and 2.7:1 V_GS(off) spreads scale the span and leave the law affine), which is why the trait now reads the endpoints off the run | high — two independent published derivations agree, and the claim is a shape, not a span | a mid-ramp f_b nearer the geometric mean of its own endpoints than the arithmetic one; or an affine fit to log f_b(t) with a smaller RMS residual than the affine fit to f_b(t) | notch tracking as P1 at `Rate` 0.5 Hz, `Depth` 1: fit f_b(t) and log f_b(t) affine over the middle 80 % of each ramp; report both RMS residuals in cents, the measured endpoints, and the mid-point's distance from both means |
| P3 | **The low end is the fixed resistor, not the knob.** At the `Centre`/`Depth` that drive the model to pinch-off, notch 1's minimum over one LFO period is **58.4 Hz within 30 cents** (A), and **no** combination of `Centre`, `Depth` and `Rate` in §6's ranges puts notch 1 more than 30 cents below it. That floor moves less than 30 cents between `Rate` 0.2 and 2 Hz and between `Depth` 0.5 and 1 | S1 — its own arithmetic gives 58.5 / 340.8 Hz, 0.2 % from Appendix A by an independent route; S3 (R5 = 24 kΩ, C2 = 47 nF, eq. 10 — all three re-read this run); S5 (the 1/R_p term *is* the floor) | high | notch 1 more than 30 cents below 58.4 Hz at any macro setting; or a floor that moves more than 30 cents with `Depth` or `Rate` | notch tracking at `Centre` minimum, `Depth` 0.5 and 1, `Rate` 0.2 and 2 Hz; minimum of notch 1 per run, in Hz and in cents re 58.4 |
| P5 | **Feedback raises a resonant peak between the notches.** At `Rate` 0 and fixed `Centre`, the gain at the inter-notch maximum rises **monotonically** across `Feedback` 0 / 0.3 / 0.5 / 0.7 and by at least **5 dB** end to end | S1, re-read on the mirror this run: *"Adding the feedback resistor creates a mid-hump and additional gain"*; S4 (*"amplification of certain frequencies … harmonic distortion of the amplified frequencies"*); S7 ("frequency peaks at the places where the signals reinforce"); direction confirmed on the ported node (B.3, +6.5 → +12.8 dB) | high — three sources, one measured against a real unit | a flat or non-monotonic inter-notch peak across `Feedback` | inter-notch peak gain, dB re the wideband mean, at `Feedback` 0 / 0.3 / 0.5 / 0.7 / 0.9, `Rate` 0 |
| P6 | **The sweep trajectory is piecewise linear — a triangle, not a sine.** At `Shape` 0.5, a straight-line fit to f_b(t) over the middle 80 % of each monotone ramp leaves an RMS residual under **1 % of the peak-to-peak span**; a half-cosine of the same period and endpoints leaves 2.29 % over the same window (E3). The middle-80 % window is what allows S4's measured "slightly curved edges" without weakening the test | S1 (Schmitt-trigger/integrator: *"the output of the op-amp creates a square waveform while at the 'OUT' point is the triangular LFO signal"*); S3 — its LTspice/WDF test LFO is *"a triangular wave … a fundamental frequency of 2 Hz, and a duty cycle of 65%"*, re-read this run; S4 (measured on a real unit) | high for triangle-not-sine; the 1 % is this seed's, calibrated against the sine (E3) | an RMS residual over 1 % of span in the linear window, or a trajectory whose best straight line is no better than a half-cosine's | LFO extraction: notch-centre trajectory over 8 s at `Rate` 1 Hz; the fit above, per ramp. h2/h3/h5 are **reported, never the criterion** — h3 nulls near ⅔ duty, so this row's earlier "h3 above −25 dB" form was failed by exactly the 65 %-duty shape S3 documents (E4) |
| P7 | **The stage is level-dependent: it makes harmonics that grow with level.** At `Drive` 0.5, `Rate` 0, `Mix` at equal weight, a 1 kHz tone: h2+h3 re the fundamental rises **monotonically** across −40 / −20 / −6 dBFS and by at least **10 dB** end to end. At `Mix` 0 the class is a wire and it is gone | S3 eq. 15 (the −v_ds/2 term); S5 §4, Figs. 5 and 7; S4 Fig. 6 (measured spectrum of the real pedal) | medium — mechanism sourced three ways, the 10 dB is this seed's | h2+h3 flat within 3 dB across the three levels, or non-monotonic | harmonic spectrum at level: h2..h5 re fundamental at the three levels, LFO stopped. **Control that must pass:** the same run at `Drive` 0 must show no rise (within 3 dB), so a measurement reading its own analysis floor cannot satisfy the trait |
| P8 | **Does feedback fill the notches, or keep them?** From `Feedback` 0 to 0.7 at `Rate` 0 the notch floor rises by at least **10 dB**, monotonically. **This is the one row whose own sources contradict it,** and the measurement is run to settle which reading is right, not to confirm this one | **No reached source supports it and two contradict it.** S1, re-read on the mirror this run: *"Feedbacking part of the output signal into the Shifting Stage chain will reinforce keeping the cancellation points"*; S7 says the same ("…and keep the cancellation notches"). The rising floor is what **this palette's** summing topology does (B.3: −21.1 → −7.9 dB), where the node's loop wraps **all four** stages (`audioif_phaser.c:28-29`, `:38`) while the pedal's wraps stages 2–4 (S3, S4) | **low** — split out of P5 by the trait critic so a rebuild can neither pass on P5's well-sourced peak while this half is wrong, nor fail P5 because this half turns out right | a floor that holds within 3 dB as `Feedback` rises — **the sources agreeing and this row disconfirmed**, a legitimate result (vision §3) that points the rebuild at the stages-2–4 loop | notch depth (dB re the wideband mean, 2.93 Hz resolution) at `Feedback` 0 / 0.3 / 0.5 / 0.7 / 0.9, `Rate` 0 — the same run as P5, reported separately |
| P10 | **The notch centre moves with input level.** At a held `Centre`, `Rate` 0 and `Drive` 0.5, the notch-1 centre at −6 dBFS differs from the centre at −40 dBFS by more than **30 cents** — P1's own tracker tolerance, so the claim is exactly "the shift is larger than the instrument that measures it" | S3 eq. 15 — R_ohm carries a −v_ds/2 term, so the corner is a function of the signal across the channel and not only of the gate | low. **Unmeasured as to size and sign:** no reached source states either, and v_ds swings both ways within a cycle, so the seed fixes only that a shift exists and exceeds the tracker's resolution | the two centres agreeing within 30 cents | notch tracking at −40 and −6 dBFS, LFO stopped, `Drive` 0.5. **Control that must pass:** the same pair at `Drive` 0 must agree within 30 cents |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

S1 and S3 carry the component values; S3, S4 and S5 each derive the control
law independently; S4 is the only one measured against a real unit. S7 and S8
were added by the audit pass: S7 is the analysis S1 itself cites and it
corroborates P1 and P4 independently (*"The most common commercial phase
shifters stop with four stages (such as the MXR Phase 90, Univibe)"*, *"Each
pair of stages adds one more notch"*, *"the places where they cancel can be
pretty dramatic, with perfect cancellation possible"*); S8 is the pedal
maker's own manual and it settles the one-knob claim (*"SPEED knob controls
overall effect rate"*, the only control listed besides the footswitch).

*(from §2)*

**Looked for and not reached.** Nothing, in the end. `web.archive.org` is
blocked for the *fetch tool* but **answers `curl`**, and the second audit used
it to read the original ElectroSmash page (S10) — a tool limit this workspace
had on record as a network one. The earlier entry "a 2N5952 datasheet with I_DSS/V_p
spreads" was wrong: the audit found and read one, and it is now S9.

*(from §2)*

**The part spread, now sourced (S9), and what it does and does not move.**
For the 2N5952 the datasheet gives **I_DSS 4.0–8.0 mA** (V_DS = 15 V,
V_GS = 0) and **V_GS(off) 1.3–3.5 V** (V_DS = 15 V, I_D = 100 nA) — a 2:1
spread in the first and 2.7:1 in the second, which is why S1 says the LFO
swing depends "on the FET batch" and why S4 needed a matched set. S3's fitted
pair (I_S0 = 5.367 mA, V_p = −2.021 V) sits inside both ranges, so the seed's
one parameter set is a **typical** unit, not a fixed one. **P3 is unaffected**
— its 58.4 / 340.6 Hz floor is set at pinch-off, where the JFET is out of
circuit and only R5 = 24 kΩ and C2 = 47 nF remain. **P2 is unaffected in
kind and affected in scale** — the part spread scales the slope
k = 2·I_S0/V_p² and hence the 328–2998 Hz span, but the law stays affine in
V_gs, and "the mid-point is the arithmetic mean, not the geometric" is what
P2 fixes; a rebuild is measured against its own span, not against 328 Hz.

*(from §2)*

**Unsourced, kept out of the trait table:** the Speed knob's endpoints in Hz — S8, the maker's own manual, was
read in the audit pass and gives **no rate in Hz at all**, so no reached
source goes beyond S1's "tenths of Hz to some Hertzs" and the macro's
proposed span stays this seed's own choice; the LFO's actual swing at the
gates (S1 says 5.1→3.8/1.6 V "depending on the FET batch", S3 uses
3.10–3.40 V — a 4× difference in span); the JFET matching *tolerance* — that a
matched set is *required* is sourced twice (S1 "the best way to achieve it is
to match the FETs", S4 "it was important to use a matched set of four JFETs")
and the *population* spread is now sourced (S9), but how closely MXR matched
within a unit is not.

*(from §2)*

**Audit corrections (2026-09-06).** (1) S1's licence call was "rights page
not fetched"; the mirror page does carry a rights line and it is quoted above,
but because a repackager's label is an assertion the call is now *licence
unverified — treated as copyleft*, which is the stricter reading and changes
nothing in practice. (2) GEOFEX was recorded as not reached; it is reachable
over plain HTTP and is now S7, with its all-rights-reserved notice. (3) The
Dunlop M101 manual was recorded as "listed by search but not fetched"; it was
fetched and read, and is now S8 — the Speed-range gap it was invoked for is
confirmed rather than assumed. (4) §1's "three equal 150 kΩ" is replaced by
what the two sources actually name. (5) P5's *fills-the-notches* half is
contradicted by S1, one of its own cited sources, and by S7; the row now says
so and its confidence drops to low. (6) "A 2N5952 datasheet with I_DSS/V_p
spreads" was recorded as not found; one was found and read, and is now S9 —
which turns "the seed claims no unit-to-unit variation" into a sourced
statement of what the variation is and which traits it touches. No licence call was found to be too
permissive; every row marked *reached* was reached again by the audit, and the
one row marked *not reached* (S2) is still not reachable — `www.electrosmash.com`
does not resolve, re-tested this day.

*(from §2)*

**Second audit pass (2026-09-06) — licence and citation, independent.** Every
row above was re-fetched and every quotation in §1, §2, §3 and Appendix C was
re-read against its source. Five changes, all recorded above. (1) S1's rights
line was found on **ElectroSmash's own page** through an Internet Archive
capture, now S10: `web.archive.org` is blocked for the fetch tool but answers
`curl`, so what the first pass recorded as unreachable was a tool limit. The
licence call does not move — the line names no licence and nothing is
reproduced. (2) S9's call is narrowed: no content licence, and the only terms
link is a Terms & Conditions of *Sale* page. (3) Appendix C said the output
high-pass is "C2 15 µF"; S1's own parts list puts C2 at 47 nF, 15 µF is
C8/C10, and the 22 Hz corner S1 states needs 47 nF against R2 = 150 K —
corrected. (4) **S1 contradicts itself and the seed follows the right half:**
its §5.2 prose says "The 22K resistor parallel with the FET" where its parts
list (`R6,R23,R25,R26,R28: 24K`), its own notch arithmetic (58.5 / 340.8 Hz
from 24 K · 47 nF) and S3 (R5 = 24 kΩ) all say **24 kΩ** — the same
text-versus-drawing inconsistency the TS808 run found on this site. Nothing in
§1 or §3 changes; the inconsistency is now on the record. (5) Everything else
held: S3's CC BY 4.0 is on p.1 (*"open-access article distributed under the
terms of the Creative Commons Attribution 4.0 International License"*), S4 and
S5 contain no copyright or licence statement at all, S6 has **no LICENSE
file** (GitHub's API returns `license: null`; the repo is a README, `main.m`,
`nJFETresistanceApprox.m` and an `LTspice` directory) and its CC BY-NC 4.0
line is as quoted, S7 returns 200 over plain HTTP and a connection reset over
https (re-tested) and all four sentences quoted from it are on the page with
its all-rights-reserved notice, S8 lists SPEED and the footswitch and gives no
rate in Hz, and S9's 2N5952 column reads I_DSS **4.0–8.0 mA** and V_GS(off)
**1.3–3.5 V** as §2 states. Every component value, equation number and quoted
sentence in §1 and §3 traces to a row in this table, and every local line
number was re-run under `grep -n`: `Phaser.c:204`, `:210`, `:211`, `:214`,
`:225`, `audioif_phaser.c:14` and `:24`-`:41`, `Biquad.c:120-126` (seven modes,
no all-pass) and `LFO.c:139` (the 4-point triangle) are all exact. **One is
not:** `SYNTHIO_MAX_DUR` is defined at `synthio/__init__.h:126`, not `:119` as
§5 cites — the value (256) and the argument are right, the pointer is seven
lines off. The audit does not edit §§4–8, so §5 carries it until Station A
fixes it.

*(from §3)*

Numbers marked (A) are derived in Appendix A, (B) measured in Appendix B, (E)
calibrated by the trait critic in Appendix E. Every row is stated at **48 kHz**
and names the macro settings it is read at; every spectral threshold names its
resolution, because a null's measured depth is a property of the analysis as
much as of the filter.

*(from §3)*

**Trait-critic pass (2026-09-06).** Seven rows in, ten out; nine are circuit
traits and P9 is labelled a surface requirement so it cannot be counted as one.
P1–P4 were falsifiable already and are tightened: each states the rate, the
macro settings, and — where it reads a spectrum — the resolution, without which
P4's "40 dB below" describes an FFT rather than a filter. P1, P4, P7 and P10
gained a **control that must pass**, so a silent or flat render cannot satisfy
them (workspace-craft: a suite of only failures proves a checker always fails).
Three rows were split, each having conjoined a well-sourced claim with one that
was not — the vision's rule that a character cannot hide behind a passing
sibling applies inside a row as much as across a class: P5 keeps the feedback
*peak* and its contested *floor* half becomes **P8**; P6 keeps
triangle-not-sine and the *asymmetry* becomes **P9**; P7 keeps
harmonics-with-level and the *notch shift* becomes **P10**. Two thresholds were
wrong rather than loose: P6's "h3 above −25 dB" is failed by the very 65 %-duty
shape S3 documents (E4), and P9 replaces "ramps differ by at least 10 % of the
period **at the shipped default**", which §6's own `Shape` default of 0.5
disconfirms by construction. Nothing was deleted, and no source is cited here
that this run did not reach.

*(from §3)*

Budget as a fraction of one stereo 256-frame block's deadline (5.333 ms at
48 kHz): **ESP32-P4 0.04, ESP32-S3 0.10** — about 18 multiplies per stereo
frame (four stages at two multiplies and two adds each, plus the feedback add
and the dry/wet sum), five times `Tremolo`'s one multiply-add and a fifth of
`Rotary`'s chain. RAM is trivial: eight all-pass words of state plus a
1024-entry int16 shape table for P6 (2 KB), computed on CPython and shipped,
never rebuilt on a board. Lean patch expected: **no** — if P7 needs 2×
oversampling and the S3 cannot pay it, the lean patch drops the
level-dependent stage and says so, rather than shortening the cascade,
because the cascade length *is* P1.

*(from §3)*

**Latency: 0 samples, 0 ms at 48 kHz.** An all-pass cascade is recursive and
reads nothing ahead; the dry path is untouched. **No option adds latency** —
not more stages, not feedback. P7's oversampling is specified with a
minimum-phase filter so it adds none; should Phase 1 pick a linear-phase
half-band instead, that option defaults off, its group delay is reported in
`latency_samples` the moment it is on, and the docstring names it in ms at
48 kHz. Reported `latency_samples = 0` is verified by the click measurement
at the class gate.

*(from §4)*

**How the node sums dry and wet** *(corrected by the palette verifier,
2026-09-06)*. It computes **`dry + mix·wet`, not `(dry + mix·wet)/2`**:
`audioif_mix_down_sample(word, 2, -28000, 28000)`
(`audioif_phaser.c:39-40`, `Phaser.c:263-264`) returns its argument unchanged
inside ±28000 and compresses only the excess (`audioif_synth_dsp.c:20-28`).
So `mix = 1.0` is the pedal's equal-weight sum, which is what P4's null needs
— but the passband gain reaches **+6 dB**, so the class owes Tier 1's
level-honesty invariant an explicit output trim. Measured 1.666× at 100 Hz
against 1.687 predicted, where a halving node would read 0.84 (F.2).

*(from §4)*

- **P4 is unreachable *through the node*.** `feedback` is clamped to
  `0.1 .. 0.9` (`Phaser.c:211`): 0.0 and 0.1 render **byte-identically**
  (F.3), as do 0.9 and 1.0, and the notch floor stops at **−21.1 dB**
  absolute, −23.0 dB re the wideband mean (B.3, F.1) where P4 asks for 40.
  **The clamp is the cause, not the fixed point:** driving the same shared
  kernel directly with feedback exactly 0 (`_audioif.phaser_s16`, the code
  the node runs) gives a notch **49.2 dB below the wideband mean** at
  `frequency=1100, stages=4, mix=1.0` (F.1). Sixteen-bit arithmetic reaches
  P4's depth; the ported binding's clamp is what does not.

*(from §4)*

- **Tier 1 silence fails.** Burst then 500 ms of silence leaves **all of the
  last 8000 samples at exactly −6** (B.1) — audioif#23 on the Phaser rather
  than on the biquad. Re-measured at the seed's own `stages=4, feedback=0.1,
  mix=1.0`: **−10** for ever (F.4).

*(from §4)*

- **Control is block-rate, capped at 256 frames** whatever `buffer_size` says
  (`Phaser.c:204`; `SYNTHIO_MAX_DUR` = 256, `synthio/__init__.h:126`) —
  187.5 Hz at 48 kHz. Staircase at a 0.2 Hz sweep: **−53.9 dB** at 256
  frames, −60.0 at 128, **−64.8 at 64** (B.4). The CPython build caps the
  same way (`audioif/src/cpython/audiofilters.py:71-73`), which is why B.4's 1024- and
  4096-frame rows do not move.

*(from §4)*

- `mix` clamps at 1.0 (`Phaser.c:212`): 1.0 and 2.0 render byte-identically
  (F.3), so **wet-only is unreachable on the ported node** — a phaser has no
  wet-only setting on the pedal, but the class cannot offer one either.
  Below `mix` 0.01 the node copies the source through untouched
  (`Phaser.c:214`, `audioif_phaser.c:12`, `:23`): byte-identical at `mix` 0.0
  and 0.009 (F.3), which is Tier 1's wire.

*(from §4)*

**Mono and stereo.** The Phase 90 is a mono pedal: a mono source gets the
full effect, not a wire, and a stereo source gets the same trajectory in both
channels (per-channel state, `audioif_phaser.c:26`). A quadrature stereo
spread would need two nodes behind an `audioroute.Splitter` at twice the
cost; left out of the seed (§8.4).

*(from §5)*

**Which half of the ask each trait actually needs** *(palette verifier,
2026-09-06 — the ask was written as "DC-clean **float**"; the measurement
splits it).* P4 needs only the **clamp gone**: the same 16-bit kernel with
feedback exactly 0 nulls 49.2 dB below the wideband mean (F.1), 9 dB past
P4's bar, so the depth is not an argument for float. The **Tier 1 silence**
invariant is the half that indicts the arithmetic: an int16 all-pass state
updated as `sat16(allpass·c, 15) + word` (`audioif_phaser.c:34-35`) settles
on a non-zero word and holds it, and no coefficient makes it decay. Float is
the cheap fix for that; a rounding rule that provably reaches zero would also
do, and Phase 1 owns the choice. Stating it this way keeps the ask
falsifiable: if Phase 1 finds a fixed-point form that reaches exact zero,
A1 shrinks to "unclamped feedback and a per-sample coefficient" rather than
being quietly justified by a claim the measurement did not make.

*(from §5)*

*Palette instead, and why it fails.* (a) `feedback=0.0` is clamped; the
renders at 0.0 and 0.1 are **byte-identical** (F.3) and the floor stops 17 dB
short of P4 (−23.0 dB re the wideband mean, F.1). (b) There is **no all-pass
mode on `synthio.Biquad`** (`Biquad.c:120-126` lists LOW_PASS, HIGH_PASS,
BAND_PASS, NOTCH, LOW_SHELF, HIGH_SHELF, PEAKING_EQ and nothing else) and no
raw-coefficient constructor, so a biquad cascade cannot stand in. (c) A
Python tail-gate that mutes after silence hides the DC and breaks "silence
in, silence out" on any signal that legitimately decays slowly.
(d) **A high-pass after the phaser does not clean the residue at any corner
this class can afford** — tested this run (F.5). `audiofilters.Filter` on a
`synthio.Biquad` HIGH_PASS (Q 0.707) downstream of the phaser leaves, after
the same burst-then-silence probe: **+18** LSB at 20 Hz, +4 at 40, +2 at 60,
+1 at 80 and 100, and exact **0** only at 120 Hz and above. The corner that
works sits above the class's own 58.4 Hz notch-1 floor (P3) and above the
60 Hz bottom of `Centre` (§6), so the composition buys Tier 1 by deleting the
band P3 is a claim about. Worth recording for the EQ family too: at these two
settings the biquad itself reaches exact zero (a NOTCH at 290 Hz and at
1690 Hz both settle to 0, F.5), so #23 is configuration-dependent, which is
why Gate 0 asks for the number per shipped configuration.

*(from §5)*

*Refutation record (Phase 0).* Three counter-cases were put to this ask and
all three failed. (i) "−53.9 dB of stepping is inaudible; keep the ported
node and accept the 0.1-clamped floor" — survives for P2/P6, fails outright
on Tier 1 silence and on P4. (ii) "Compose the DC away with a downstream
high-pass" — measured, fails as (d) records. (iii) "Two `synthio.Biquad`
NOTCH sections placed at f and 5.83·f give P1's pair without an all-pass
cascade" — refuted on the traits rather than on the depth: a notch pair has
none of P5's feedback peak, none of P7's level dependence and no dry/wet
cancellation to make P4 a *null*, and P1's own control that must pass
(`Stages` 6 → three notches) has no meaning on it. The ask therefore stands
**on Tier 1 and P4**; the per-sample argument is a bonus, not the case.

*(from §5)*

No second ask: P1, P3, P5, P7, P9 and P10 are reachable as composed (P7 and
P10 with oversampling in the class, not in a node). **P8** is the one further
row A1 would move: the ported node's loop wraps all four stages
(`audioif_phaser.c:28-29`, `:38`) where the pedal's wraps stages 2–4 (S3, S4),
so the ported node cannot present the pedal's own feedback topology to the
measurement that decides P8. That is a reason to record the result carefully,
not a second ask.

*(from §7)*

3. **The constructor's numbers do not mean what they look like.** The LFO is
   `scale=900·depth, offset=1100` (`:73-74`) handed straight to `frequency=`
   (`:76`) — a raw node argument, not a notch frequency, not pre-warped. At
   the shipped `depth=0.7` the apparent 470–1730 Hz sweep actually puts the
   three notches at 80–295 Hz, 299–1099 Hz and 1117–4103 Hz: the lowest never
   leaves the bass and nothing sits where the numbers imply.

*(from §7)*

6. **Nothing declared** — no `CAPABILITIES`, `LATENCY_SAMPLES` or
   `TAIL_SAMPLES`, so `latency_samples` is 0 by accident (`_core.py:245-248`)
   rather than by measurement, and the transport is never read.

*(from §7)*

7. **`reset()` and `deinit()` reach one node** — `_core.py:366-374` and
   `:376-385` touch `self._output` only. It happens to be right here because
   the class builds one node; the rebuild must enumerate what it builds.
