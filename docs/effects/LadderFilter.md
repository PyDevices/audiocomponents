# Effects Dossier — `LadderFilter` (Moog transistor ladder)

**Class:** `lib/audioeffects/eq.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Filter, roadmap Phase 2
**Standout:** the Moog transistor ladder — four one-pole stages, global
feedback, the nonlinearity that makes it growl. Vision §4.2, **confirmed**. A
diode ladder (TB-303, EMS, Roland 100) is a *different circuit* — its stages are
not buffered from each other and its transfer function is "considerably harder
to derive" and not the same one (L1 §3.1) — and stays a separate ask.
**Grade:** **circuit.** Moog's own patent gives the topology, the four
sections, the capacitor per section, the control current and the feedback path
(L2); Stinchcombe derives the transfer function from that topology and gives the
poles, the tuning law and the frequency responses analytically (L1); Huovilainen
derives the differential equation and its discretisation with the nonlinearity
in place (L3). Every Tier 2 trait below is derived from a topology, not read off
a curve, and every derived number was re-checked numerically in this run
(Appendix A). Component values are not from a Moog service drawing — the ladder's
traits are topological once ω_c is set, which is why the grade holds; the
caveat is stated in Appendix D.
**Portability tier:** **audioif** — `TIER = _component.AUDIOIF`,
`REQUIRES = ("audioladder",)`. §5's one ask **landed**: `audioladder.Ladder`
is on the audioif pin, so the class is that one node rather than a biquad pair
with a hole where T3, T4 and T5 should be (§4, §5, **App. S**).
**Status:** **traits frozen — Station A closed 2026-09-07.** §§1–3 are the
contract the class gate is read against and are not edited after this line.
§§4–8 record what the node's arrival settled; the text they replace is in
App. S, verbatim, deleted nowhere.

## 1. The circuit, in one paragraph

Moog's filter is a ladder of **four identical sections, each one capacitor and
two transistors**, driven at the bottom by a control current, each stage fed by
the output current of the one below (L2: "four identical sections each
comprising a fixed capacitor and two transistors"; L3 §2). The transistors' beta
is high and their base currents negligible, so **the stages are buffered from
each other** — the ladder is literally four cascaded one-poles and its core is
`G(s) = −1/(s/ω_c + 1)⁴` (L1 eq. 17). The voltage control *is* the transistors'
base-to-emitter resistance, `R_equiv = 4V_T/I_f`, so `f_c = I_f/(8π·C·V_T)`
(L1 eq. 13) — cutoff proportional to control current "over an extremely wide
frequency range of the order of 1000:1" (L2), which is what makes it exponential
in a control voltage. Resonance is a **global** feedback path returning a
portion `k` of the output to the other side of the input differential pair (L2;
L3 §2), giving `H(s) = 1/((s+1)⁴ + k)` (L1 eq. 22). Everything a player
recognises falls out of that equation. Its poles are `s = −1 ± k^{1/4}e^{±jπ/4}`,
an X centred on (−1, 0) that opens as `k` rises, and **at k = 4 the rightmost
pair reaches the imaginary axis and the filter oscillates** (L1 §2.5). Because
the poles move apart the surface sags between them: the passband **droops** as
resonance rises, to about −14 dB at k = 4, and Stinchcombe offers that as *the*
test for the type — "open the filter right up … turn the resonance up, and if
the level of the signal drops, chances are the filter is of this type" (L1
§2.5). The **nonlinearity** is the differential pair itself,
`I₁ − I₂ = I·tanh((V₁−V₂)/2V_T)` (L1 eq. 5; L3 eq. 1) — an odd function at the
input of every stage, which is why the self-oscillation settles at a bounded
amplitude, why resonance depends on level, and why Huovilainen's model needs "no
extra coefficients that would need to be tuned by ear — the 'warmth' is
determined by the input amplitude" (L3 §1).

## 2. Sources and license calls

All reached 2026-09-06 in this run; nothing from memory.

| Source | What it gave | License call |
|---|---|---|
| **L1** Stinchcombe, *Analysis of the Moog Transistor Ladder and Derivative Filters*, 2008, 51 pp. | the whole derivation: `f_c = I_f/(8π C V_T)`, the core `−1/(s+1)⁴`, `H = 1/((s+1)⁴+k)`, the pole locus and k = 4, the −12 dB and −14 dB readings, the pair's `tanh`, and why a diode ladder differs | no licence line anywhere — **unverified, treated as copyleft**; read as a paper, maths re-derived, no code taken |
| **L2** Moog, US 3,475,623, granted 28 Oct 1969 | the primary topology: four identical sections of one capacitor and two transistors; the standing-current control; the variable feedback resistor; cutoff exponential over ~1000:1 | expired US patent — a public disclosure document |
| **L3** Huovilainen, *Non-Linear Digital Implementation of the Moog Ladder Filter*, DAFx-04, pp. 61–64 | the per-stage differential equation and its Euler solution; the `4r` feedback; `g = 1 − e^{−2πF_c/F_s}`; five `tanh` a sample; the half-sample feedback delay and its §5.3 tuning result; 2× oversampling | no licence line — **unverified, treated as copyleft**; read as a paper, no code taken |
| **L4** Stilson & Smith, *Analyzing the Moog VCF*, ICMC 1996, 11 pp. — **added by the audit**, at the URL L1's own reference list prints | an independent second derivation of T1's −12.04 dB, T2's mechanism and T3, from a source independent of L1; also the paper L3 §5.3 answers (quotations: App. F) | no licence line, author-hosted at CCRMA — **unverified, treated as copyleft**; read as a paper, no code taken |

What was **not** reached, and what was looked for and not found: Appendix D.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait, as it is frozen (falsifiable as stated) | Disconfirmed by |
|---|---|---|
| **T1** | **Four poles, and the cutoff is the asymptote's crossing, not the −3 dB point.** Cutoff 1 kHz, resonance 0 ⇒ **−12.0 ± 0.5 dB at 1 kHz**, a −3 dB point at **435 ± 20 Hz** (0.4350·f_c), and a stopband slope between **−23 and −27 dB/octave measured 4→8 kHz** *(band and tolerance are the audit's; its arithmetic, and the seed's failing "−24 ± 1 dB/octave over 2→4 kHz", are in App. T1)*. | any of the three outside its band; in particular a −3 dB point at the nominal cutoff, or 48 dB/octave |
| **T2** | **The passband droops as resonance rises** — DC gain is exactly `1/(1+k)`. At k = 0, 1, 2, 3, 4 the level at 0.1·f_c is **0.00, −6.02, −9.54, −12.04, −13.98 dB, each ±0.5 dB** (the ±0.5 covers the 0.1·f_c reading sitting up to 0.17 dB above the DC value it quotes, recomputed in Appendix A). | **any of the five outside ±0.5 dB**; in the limit, a passband moving under 3 dB in total across k = 0…4 — a resonance that only adds a peak, the current class's failure (§7) |
| **T3** | **Self-oscillation at k = 4, at the cutoff, and not before.** Cutoff 1 kHz: at the top of `Resonance` travel one impulse leaves a tone within **3 %** of 1 kHz decaying **less than 3 dB in 2 s**; at 90 % of travel the same impulse falls below **−40 dB within 2 s**. | oscillation below the top of travel, or none at the top; or an oscillation away from f_c |
| **T4** | **The nonlinearity is inside the loop, is odd, and is what bounds the oscillation.** Three measurable parts. **(a) Bounded:** at self-oscillation the peak stays within **±1 dB over 2 s** and total harmonic distortion is **under 15 %** — the tone is a rounded sine, not a flat-topped one (an ideal square reads 48.3 %). **(b) Odd:** **every even harmonic is below −40 dB re h1 and at least 20 dB below h3**, at self-oscillation and at every `Drive` position of (c). **(c) Present, and in the loop:** at cutoff 1 kHz and a fixed k = 3.9 (below oscillation), on a held 1 kHz tone sitting on the resonant peak, **h3 re h1 rises monotonically** across `Drive` = 0, +8, +16, +24 dB, by at least **10 dB** end to end — the floor is deliberately far below what a cubic-dominant odd nonlinearity gives (h3/h1 ∝ A², so up to 48 dB across a 24 dB drive rise before compression sets in), so that passing it is evidence and failing it is unambiguous. | **any of (a), (b), (c) missed** — each negation, and why (c) is the one place absence could read as a pass, in App. T4 |
| **T5** | **Drive is the only warmth control: character follows input level.** At fixed cutoff and k = 3, a 20 dB input rise moves the resonant peak's height by at least **3 dB** and raises THD monotonically; below −40 dBFS input, THD is under **0.5 %**. | **either half missed** — the peak moving under 3 dB across a 20 dB input rise, THD not rising monotonically, or THD ≥ 0.5 % below −40 dBFS in (App. T5) |

**Source, confidence and the kit measurement for every row are in App. T, in full and unedited.** This table is the part the class gate checks, and it is frozen as of Station A.

No characters. A diode ladder is a different circuit (L1 §3.1), not a character
of this class.

*(What the trait-critic pass changed in this table, and why: Appendix G.)*

### Tier 3 — cost and latency

**Latency budget: 0 samples, at every setting, and there is no
latency-adding option.** The node's 2× path is a linear interpolation up and a
two-tap average down — half a sample of group delay for the pair, which rounds
to the 0 it reports (`audioif/src/shared/audioif_ladder.c:305`, `:310`). Inside
the stompbox budget (vision §9a) with nothing spent; that is Q2's whole answer.

**Cost budget** (App. C's arithmetic; one stereo block is 256 frames = 5.33 ms
= 1,280,000 S3 cycles, 2,133,000 P4):

| Board | Patch | Share of one stereo block |
|---|---|---|
| ESP32-P4 | 0, `oversample` on | **8 %** |
| ESP32-S3 | 0, `oversample` on | **14 %** |
| ESP32-S3 | 6 `Ladder - lean`, `oversample` off | **7 %** |

Ceilings the gate measures against, not predictions — and App. C's estimate
assumed a *table-driven* saturator the shipped node does not have, so it is
likely generous. Left as it stands rather than re-guessed (App. S).

**`tail_samples` is `None`**: below k = 4 no source reached here bounds the
decay, and at and above k = 4 the class holds T3 instead of the silence
invariant (App. I) and does not decay at all.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node: `audioladder.Ladder`.** §5's ask landed between the seed and this
station, so the build is no longer a composition. `Ladder` is four
topology-preserving one-pole stages round a global feedback loop with the odd
cubic saturator *inside* the loop — the shape §1 derives — and every one of §6's
seven macros is one of its seven options
(`audioif/src/shared/audioif_ladder.h:52-60`).

Four decisions are the node's, not this class's, and each was read out of the C
rather than recalled *(the readings in full: **App. S**)*:

| | The node does | Consequence for the traits |
|---|---|---|
| the loop | **solved**, not delayed: `y + a·sat(y) = c`, four fixed passes (`audioif_ladder.c:194-217`) | T3 lands at **exactly** k = 4 and **exactly** at f_c. One sample of delay measured 3.5, six per cent flat (`:11-23`) |
| the tuning | `g = tan(πf_c/f_s′)/(1+tan(…))` (`:80-82`), **not** L3 eq. 21's exponential | the bilinear map is what makes four stages reach −180° at gain 1/4 at f_c, which is T1's numbers |
| the saturator | `x − x³/3`, clamped, two multiplies, **no table** (`:66-69`) | odd by construction (T4b); unity slope at the origin, so it does not move k = 4 |
| the clamp | `1 Hz … 0.49·f_s′` (`:79`), and the class clamps on top with `self._hz()` | rate-honest: at 22.05 kHz the top of `Cutoff` *becomes* 10.8 kHz rather than raising |

**Headroom** is the circuit's here, not the build's: the two-biquad build lost
usable input peak as `1/Q₁` (App. H(iii)), while the node works in ±1 float with
the saturator bounding the loop — but at self-oscillation its own tone is what
fills the output, so the signal's headroom still falls with `Resonance`.
**Mono:** the same filter on one channel, per-channel state
(`audioif_ladder.h:100-110`); not stereo-by-definition. **Tier: audioif.**

*(§4 as the seed wrote it, verbatim, is in **App. S**; more of §4 is in
**App. R**. Nothing deleted.)*

## 5. Node asks

**The one ask is DELIVERED.** `audioladder.Ladder` shipped in effects Phase 1
and is on the pin (`audioif/docs/upstream-diff.md`, "`audioladder`: the loop
CircuitPython's filters cannot close"). Nothing here is outstanding.

It unblocks **T3, T4, T5** — the three the seed named, in the order the seed
named them, and the node's own header names the same three independently
(`audioif/src/shared/audioif_ladder.h:8-17`). T1 and T2 were never asks: they
are reachable on stock biquads (App. H), which is why §7's defect 1 is about the
old cascade's *shape* and not about a missing node. The seed's four refutations
all still stand and the node closes the gap they left — (a) four low-passes at
one cutoff fails T1; (b) the pole factorisation fails T3/T4/T5 by construction;
(c) a block-rate level law makes no harmonics, so T4 would read absence as
agreement; (d) a series waveshaper satisfies T4(b) and T4(c) with nothing
nonlinear *inside* the loop (App. E, App. H(iv)).

*(§5 as the seed wrote it, verbatim, is in **App. S**; more of §5 is in
**App. R**. Nothing deleted.)*

## 6. Proposed surface

**Seven macros, frozen.** Each is one `Ladder` option, so nothing on this panel
is a Python-side reinterpretation of something the node already means.

| # | Label | Mode | Range | Node option | Generalizes |
|---|---|---|---|---|---|
| 0 | Cutoff | UNIPOLAR | 20 Hz–18 kHz, **log** | `cutoff_hz` | the Cutoff knob (exponential is the circuit's own law, L2) |
| 1 | Resonance | UNIPOLAR | k = 0…4.2 | `resonance` | the Emphasis / Regeneration knob; T3's k = 4 boundary sits at position **0.952** of travel, inside the span |
| 2 | Drive | UNIPOLAR | 0…+24 dB | `drive` (linear) | the input level — the only warmth control the circuit has (T5) |
| 3 | Passband Comp | UNIPOLAR | 0 faithful … 1 flat | `passband_comp` | none — how much of T2's `1/(1+k)` droop is given back; **defaults to 0** |
| 4 | Poles | UNIPOLAR | 1…4 | `poles` | the ladder's lower taps (6/12/18/24 dB an octave); defaults to 4 |
| 5 | Oversample | TOGGLE | off / 2× | `oversample` | none — Tier 3's CPU-versus-alias knob; **defaults to 2×** |
| 6 | Mix | UNIPOLAR | 0…1 | `mix` | none — the contract's wire-at-zero |

**Two changes from the seed's eight**, each argued in full in **App. S**:
**`Slew` is dropped** — the node has no slew option and `_component` calls
`_apply_macro` only when a knob *moves*
(`lib/audioeffects/_component.py:505-517`, `:588-594`), so a Python glide would
advance only while the knob was being turned. Filed as §8 Q6 rather than faked.
**`Poles` is UNIPOLAR, not TOGGLE** — it has four positions and the contract's
TOGGLE is two (`_component.py:314-317`).

**Characters:** none. A diode ladder is a different circuit (L1 §3.1), not a
character of this class.

**Patches**, on the 0–127 grid, in the macro order above:

| # | Name | Cutoff | Res | Drive | Poles | 2× | For |
|---|---|---|---|---|---|---|---|
| 0 | `Wide Open` | 12 kHz | 0.6 | 0 dB | 4 | on | the constructor's defaults |
| 1 | `Squelch At The Knee` | 700 Hz | 3.6 | +6 dB | 4 | on | the sound the knob is for |
| 2 | `Sustained Sine At Cutoff` | 1 kHz | 4.2 | 0 dB | 4 | on | **T3's boundary** |
| 3 | `Dark` | 300 Hz | 1.5 | 0 dB | 4 | on | the ladder as a tone control |
| 4 | `Growl With Drive` | 900 Hz | 3.9 | +18 dB | 4 | on | **T4(c), T5** |
| 5 | `Two Pole Soft` | 2.5 kHz | 1.0 | 0 dB | 2 | on | the lower tap, 12 dB/oct |
| 6 | `Ladder - lean` | 12 kHz | 0.6 | 0 dB | 4 | **off** | Tier 3's S3 valve |

`Passband Comp` is 0 and `Mix` is 1 in every patch.

**How T3 is read against this span.** T3's two measured positions are the
**top** of `Resonance` travel (k = 4.2 — sustains) and **90 %** of it (k = 3.78
— decays below −40 dB in 2 s). Its disconfirmation clause "oscillation below the
top of travel" means *at that 90 % position*: the trait's headline is "at
k = 4", which is position 0.952 and inside the span **by the seed's own
design** (§6, seed: "T3's boundary is a documented position inside the span").
A span topping out exactly at 4 would put a self-oscillating filter at the end
stop and make "and not before" unmeasurable from the panel.

`Passband Comp` defaults to 0 in every patch, deliberately: T2 is the trait that
identifies this filter, and a class shipping with the droop compensated away
would pass its own gate while sounding like something else.

**Every Tier 2 trait is measured at `Poles = 4`** (§8 Q3), and Station C states
the patch and the macro positions each figure was taken at.

*(§6 as the seed proposed it, verbatim, is in **App. S** — nothing deleted.)*

## 7. Defects in the current class the rebuild must not repeat

One read of `lib/audioeffects/eq.py`; the numbers are Appendix B(iii).

1. **It is not a ladder.** Four `synthio.Biquad(LOW_PASS, …)` in one cascade …  *(argument in full: App. R)*
2. **Resonance adds a peak and no droop.** `q = 0.55 + 6.0 * resonance` …  *(argument in full: App. R)*
3. **It cannot self-oscillate** — Q is bounded at `0.55 + 6.0` = 6.55, a finite
   peak (+11.61 dB at resonance 0.9). T3 is unreachable by construction.
4. **`resonance` has no macro** — `MACRO_LABELS = ()` (`eq.py:171`), …  *(argument in full: App. R)*
5. **`check_hz()` refuses instead of clamping** (`eq.py:177`, `:190`; the raise …  *(argument in full: App. R)*
6. **The docstring claims what the code does not do** — "four cascaded …  *(argument in full: App. R)*
7. **Inherited:** `Effect.__new__` mutates module-wide format state …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

Five were open at the seed. **Three are settled here**; one is Station C's first
measurement, by the seed's own instruction; one stays open and is not a blocker.
One new question is filed rather than faked. *(The readings behind each answer:
**App. S**.)*

1. **Saturator table resolution and oversampling factor.** **SETTLED — the
   premise is gone.** No table: `x − x³/3`, two multiplies
   (`audioif_ladder.c:66-69`). The factor is 1 or 2 and defaults to **2**
   (`:100-104`, `:158`); it is macro 5 and patch 6 is the lean valve, so vision
   §10.3's cost-versus-alias table is a *measurement* on this class, not a
   decision it waits on.
2. **The half-band filter's length and phase type.** **SETTLED — there is no
   half-band filter**, and no latency (§3 Tier 3). What the cheap 2× path costs
   instead is stopband rejection, which Station C reads as SPECTRUM.
3. **Whether `Poles` belongs on the surface.** **SETTLED — kept**, on the seed's
   own reasoning: it costs nothing (the tapped stage is computed either way,
   `:265-271`) and the feedback is always the fourth stage, so resonance and
   self-oscillation are the same filter's at every tap. The risk it named is
   answered by stating the setting: **every Tier 2 trait is measured at
   `Poles = 4`**.
4. **The sign of T5's peak-height move, and an absolute floor for h3 at
   self-oscillation.** **Still open, and Station C's to close** — the seed's own
   instruction: from its first measurement, "recorded as the trait's real
   number, not back-fitted into the threshold". T5's ±3 dB bar does not move to
   match what is measured.
5. **A Moog service drawing with values.** **Still not reached, still not a
   blocker** (App. D; no URL fetched at this station). The traits are
   topological once ω_c is set. Note the node's tuning law is bilinear, not the
   seed's exponential (§4), so a drawing would now check L1's simulation range
   and nothing in §3.
6. **New: `slew_ms` on `audioladder.Ladder`.** Raised by dropping `Slew` (§6). A
   glide has to run inside the node; Python cannot reach it. **Not this class's
   to build** — an audioif ask, to be filed as an audioif issue by the session
   that opens the Phase 1 node backlog, recorded here so it is not lost between
   the two repositories.

---


## Appendix

### A. The analytic numbers, re-derived in this run

`H(s) = 1/((s+1)⁴ + k)`, computed in Python on 2026-09-06:

- **−3 dB point at k = 0:** `ω/ω_c = √(2^{1/4} − 1) = 0.43498` ⇒ 522.0 Hz for a
  1200 Hz cutoff, 435.0 Hz for 1 kHz. (T1)
- **Level at ω = ω_c, k = 0:** −12.0412 dB — exactly 4 × −3.0103. (T1)
- **DC gain `1/(1+k)`:** k = 0 → 0.00 dB; 0.5 → −3.52; 1 → −6.02; 2 → −9.54;
  3 → −12.04; **4 → −13.98 dB**, which is Stinchcombe's "approximately −14dB".
  (T2)
- **The same five read at 0.1·f_c**, which is where T2 actually measures them:
  **−0.17, −5.93, −9.45, −11.95, −13.90 dB** for k = 0, 1, 2, 3, 4 — each within
  0.17 dB of its DC value — **0.17 dB below** at k = 0, where the roll-off has
  already begun and there is no resonance to offset it, and **0.08–0.09 dB
  above** at every k ≥ 1, where the resonant rise reaches down that far. That
  offset is why T2's tolerance is ±0.5 dB and not tighter; a
  rebuild reading 0.1·f_c and comparing against the DC figures is not making an
  error. (T2; computed in the trait-critic pass.)
- **Pole pairs**, `σ = −1 ± k^{1/4}/√2`, `ω = k^{1/4}/√2`, for f_c = 1 kHz:

  | k | pair 1 (f, Q) | pair 2 (f, Q) |
  |---|---|---|
  | ≈0 | 932 Hz, 0.501 | 1073 Hz, 0.501 |
  | 1 | 765 Hz, 1.307 | 1848 Hz, 0.541 |
  | 2 | 856 Hz, 2.689 | 2024 Hz, 0.550 |
  | 3 | 933 Hz, 6.724 | 2143 Hz, 0.555 |
  | 3.9 | 994 Hz, 78.75 | 2228 Hz, 0.559 |
  | **4** | **1000 Hz, ∞** | 2236 Hz, 0.559 |

  Pair 1's Q diverging at k = 4, at exactly f_c, **is** T3. Evaluating `H` at
  k = 4, f = f_c raises `ZeroDivisionError` — the pole is on the axis.

**Audit, 2026-09-06.** Every number in this appendix was recomputed independently
and reproduces to the digit: √(2^¼ − 1) = 0.4349794 ⇒ 521.98 Hz and 434.98 Hz;
−12.0412 dB at ω_c; the whole `1/(1+k)` ladder (0.00, −3.52, −6.02, −9.54, −12.04,
−13.98); every cell of the pole table, including 78.748 at k = 3.9 and
(1000 Hz, ∞) / (2236 Hz, 0.559) at k = 4; T1's slope figures (−21.26 dB over
2→4 kHz, −23.30 over 4→8, −23.88 over 8→16); and Appendix B(i)'s analytic row
(−0.17, −1.05, −3.01, −3.88, −12.04, −27.96, −49.22, −72.52). L1's own readings —
"approximately −14dB" at k = 4 and "the k = 0 (flattest) curve … cuts ω = 1 at
−12dB (being 4 × −3dB)" — were read at source, as was "open the filter right up …
turn the resonance up, and if the level of the signal drops, chances are the filter
is of this type".

### B. Measured: what the palette can and cannot do

CPython build of audioif (`audiocomponents/.venv/bin/python`), one
`audiofilters.Filter`, 48 kHz, 2026-09-06. Levels are steady-state magnitude
from a rendered sine.

**(i) Two `LOW_PASS` biquads at Q = 0.5 reproduce the linear ladder core**
(f_c = 1 kHz, k = 0):

| Hz | 100 | 250 | 435 | 500 | 1000 | 2000 | 4000 | 8000 |
|---|---|---|---|---|---|---|---|---|
| built (dB) | −0.17 | −1.05 | **−3.01** | −3.87 | **−12.04** | −28.07 | −49.94 | −75.56 |
| analytic | −0.17 | −1.05 | −3.01 | −3.88 | −12.04 | −27.96 | −49.22 | −72.52 |

The −3 dB point lands on 435 Hz and the cutoff on −12.04 dB, exactly as T1
states. The growing error past 2 kHz is the bilinear transform's warping.

**(ii) Two biquads from the pole factorisation follow the resonance to k = 3.8**
(peak level, f_c = 1 kHz, input level chosen so nothing clips — an earlier run at
a higher level reported a false "wall" at +6 dB that was the 16-bit output
clipping, not the filter):

| k | Q of pair 1 | built peak | analytic peak | shortfall |
|---|---|---|---|---|
| 2.0 | 2.69 | −1.77 | −1.76 | −0.00 |
| 3.0 | 6.72 | +3.49 | +3.50 | −0.00 |
| 3.4 | 12.07 | +7.70 | +7.71 | −0.01 |
| 3.6 | 18.74 | +11.14 | +11.14 | −0.00 |
| 3.8 | 38.75 | +17.07 | +17.07 | +0.00 |
| 3.9 | 78.75 | +22.71 ² | +23.05 | −0.34 ² |
| 3.95 | 158.75 | +22.78 ² | +29.05 | −6.27 ² |

and the near-oscillation decay tracks too: at k = 3.99 the analytic 34.1 dB/s
measures 33.8; at k = 3.999, 3.41 against 3.44. **T1 and T2 are reachable on the
palette.** k = 4 is not, and no linear build sustains from silence — which is
where T3 stops and §5's ask begins.

² **Audit correction — the last two rows are clipped, and the shortfall they
report is not real.** Re-rendered at an input peak of 100 (output peaks 6688 and
13509, well clear of the node's 28521 ceiling) and normalised for the two
biquads' unity DC gain against `H`'s `1/(1+k)`, the same build measures
**−0.35 dB** at k = 3.9 and **−0.33 dB** at k = 3.95, not −0.34 and −6.27 — and
most of that residue is the audit's coarse peak-search grid, not the filter.
The tell was in the table itself: +22.71 and +22.78 are the *same* number, which
is what a ceiling looks like, and it is the very artefact Appendix E's closing
note catches one section later. At k = 3.99 the audit's own run clips in turn
(peak 26863), so that row is not settled here either. **What this does not
change:** k = 4 needs an infinite Q, which no biquad represents, and a linear
build cannot sustain from silence, produces no harmonics for T4 to measure, and
has identically zero level dependence for T5. §5's node ask stands on those
three facts, not on a resonance shortfall below k = 4 — and §5's sentence
"falls 0.34 dB short at k = 3.9, 6.3 dB at k = 3.95" should be struck when
§5 is next edited (it is outside this audit's edit boundary).

**(iii) The current class, measured** (four `LOW_PASS` biquads at one cutoff,
`eq.py:179-184`), f_c = 1200 Hz:

| resonance | q | 50 Hz | 200 Hz | 1200 Hz | ladder at k = 4·res: 50 / 200 / 1200 Hz |
|---|---|---|---|---|---|
| 0.0 | 0.55 | −0.10 | −1.44 | **−23.94** | −0.03 / −0.48 / **−12.04** |
| 0.4 | 2.95 | **+0.02** | +0.31 | +5.24 | **−8.28** / −8.02 / −7.60 |
| 0.9 | 5.95 | **+0.02** | +0.37 | +17.42 ¹ | **−13.24** / −13.03 / +7.96 |

§7's defects 1–3 are these three rows.

¹ **Audit correction.** The first run recorded **+11.61 dB** here, and §7's
defect 3 still quotes that figure. Re-rendered through the same CPython
`audiofilters.Filter` at four input levels, the cascade gives **+17.42 dB** at
1200 Hz for resonance 0.9 (input peak 2000 → 14868; input peak 500 → 3712,
+17.41 dB), matching the analytic sum of the four RBJ sections, **+17.43 dB**.
At input peak 8000 the node's output saturates at 28521 and reads +11.04 dB; at
20000 it reads +3.08 dB. +11.61 dB is therefore **a clipped measurement** — the
same 16-bit ceiling this appendix's own note catches in B(ii), which was fixed
there and not re-run here. The res 0.0 and res 0.4 rows reproduce exactly
(−0.10 / −1.44 / −23.94 and +0.02 / +0.31 / +5.24), as do the −3 dB point near
305 Hz and every "ladder at k = 4·res" figure. The defect is *worse* than the
seed said, not better: the peak is 5.8 dB higher than recorded.

Probes: `probe_eq.py`, `probe_eq2.py`, `probe_eq3.py`, `probe_eq4.py`,
`probe_eq5.py`, `probe_eq6.py`, `probe_eq7.py` (scratch); every measurement here
is reproducible from the kit's swept-sine and impulse probes (Phase 0 kit spec).

### C. The cost arithmetic behind Tier 3

One stereo block is 256 frames (`SYNTHIO_MAX_DUR`, `src/synthio/__init__.h:126`) = 512 samples =
5.33 ms at 48 kHz: **1,280,000 cycles on a 240 MHz S3**, **2,133,000 on a
400 MHz P4**. The ladder node's inner loop is four one-poles (a multiply, a
subtract and an add each) plus five table lookups with interpolation, per sample
per channel — budgeted at **180 cycles/sample/channel**, against audioif's own
measured 76 instructions/sample for a biquad on Cortex-M4/M7
(`docs/upstream-diff.md:1167-1174`) as the calibration point. At 1×:
512 × 180 ≈ 92,000 cycles ⇒ **7 % of the S3's block, 4 % of the P4's**. At 2×,
doubled plus the half-band's cost ⇒ **14 % / 8 %**. Ceilings the class gate
measures against, not predictions; no Xtensa or RISC-V instruction count exists
yet, and Station C's job is to replace these with real ones.

### D. Sources not reached, and the grade's caveat

**Not reached:** Moog's own AES preprint 413, *A Voltage-Controlled Low-Pass
High-Pass Filter for Audio Signal Processing* (17th AES Convention, Oct 1965) —
cited by both L1 and L3, behind the AES paywall, no self-archived copy found —
**the audit did not re-attempt this one**; Zavalishin, *The Art of VA Filter
Design* — re-attempted by the audit at its canonical Native Instruments URL,
which returns **HTTP 404**, so it stays not reached.
~~Stilson & Smith, *Analyzing the Moog VCF with Considerations for Digital
Implementation* (ICMC 1996), searched for and not fetched in this run~~ —
**struck: the audit fetched it in one call** (HTTP 200, 11 pages) at
`https://ccrma.stanford.edu/~stilti/papers/moogvcf.pdf`, the URL printed in L1's
own reference list, and it is now **L4** in §2. Nothing in §3 changes — it
corroborates T1, T2 and T3 from a source independent of L1 — but a "not fetched"
line that a reference list makes reachable is exactly what this audit exists to
catch: the URL was in a source already read. **Deliberately not opened:** `ddiakopoulos/MoogLadders`
and other emulator repositories — the licences were not checked because no code
was read; the maths in this dossier comes from L1 and L3 as papers (vision §5).

**The grade's caveat.** L2 gives the topology and L1 the derivation, but no Moog
service drawing with component values was reached. The capacitor and current
figures quoted anywhere in this dossier (47 nF, I_f 10–500 µA, CA3083) are
**Stinchcombe's simulation circuit** (L1 §2.4 — re-read at source in the audit
run: "all transistors use the SPICE model for the CA3083 … all capacitors are
47nF, calculated as giving practical cut-off frequencies for If ranging from
around 10 µA to 500µA"), not a production Moog's, and are
used only to show the `f_c = I_f/(8π C V_T)` law spans a musical range. Every
Tier 2 trait is stated in normalised form and is independent of those values
once ω_c is set — which is why this seed claims a circuit grade with an analytic
derivation rather than a SPICE deck, per vision §4.1. If a service drawing is
reached later, the traits do not change; only the tuning range's provenance
does.

### E. Refutation record — three ways to compose the ask away

Phase 0, this run. Each attempt ends on a measurement, not an argument.

**(a) Four `LOW_PASS` biquads at one cutoff** — the current class's shape. Eight
poles: −23.94 dB at its own nominal cutoff where the ladder gives −12.04, and a
−3 dB point at ~305 Hz against 522 Hz. **Fails T1 outright**, before resonance
is even considered (Appendix B(iii)).

**(b) Two biquads from the pole factorisation.** Succeeds — which is why it is
the build in §4, not a rejected candidate: T1 and T2 to 0.01 dB, resonance
tracked to k = 3.8 to 0.01 dB, near-oscillation decay rates within 10 %
(Appendix B(i), B(ii)). **Fails T3**: k = 4 needs an infinite Q, and no linear
filter sustains from silence. **Fails T4 and T5 by construction**: there is no
nonlinearity, so the harmonic ladder does not exist and level dependence is
identically zero.

**(c) Two biquads plus a block-rate level law**, moving the biquad Q with input
level to fake T5's level dependence. It does move the peak height with level —
and produces **no harmonics at all**, so T4's measurement has nothing to find
and would return "no even harmonics above −40 dB" as a *pass*. That is absence
reading as agreement, the failure shape this workspace watches for
(`agent-knowledge/workspace-craft.md`), and (c) is refused for that reason
rather than for its cost.

One methodological note, recorded because it nearly produced a wrong finding:
the first run of (b) reported the palette hitting a hard wall at +6 dB of
resonance for every k above 3.4. That wall was the **16-bit output clipping at
the probe's input level**, not the filter. Re-run at a level that cannot clip,
the shortfall vanished up to k = 3.8. The measurement was the first suspect and
it was the culprit.

### F. Audit source notes — the quotations behind §2's L4 row

Read at source in the licence-and-citation audit run, 2026-09-06.

**L4, Stilson & Smith (ICMC 1996), on the traits this seed fixes.** On the core:
"the four one-pole sections comprise a lowpass filter with cut-off frequency
ω = ωc, which is inverting at cut-off. Therefore, the use of inverting feedback
provides resonance at the cut-off frequency" — and at that point "the total gain
is 1/4 and the phase is −180 degrees", i.e. T1's −12.04 dB, from a derivation
independent of L1's. On resonance: "as the feedback gain k approaches 4, the total
loop gain approaches 1, and the gain at resonance goes to infinity"; and, of their
Figure 2, "as k increases, corner peaking develops at the cut-off frequency. At
k = 4, the lowpass filter oscillates at its cut-off frequency." On the pole locus:
"as the feedback gain g goes from 0 to 4, the poles of the overall filter expand
outward in an 'X' pattern from s = ωc until the two poles on the right reach the
jω axis at ω = ωc." No copyright or licence line appears anywhere in the PDF.

### G. Trait-critic pass — what changed in the Tier 2 table

2026-09-07. Five rows, all kept, three rewritten in
place. **T2** — the disconfirmation named only the extreme case ("less than 3 dB
of total movement") and so could not fail a build that missed the five stated
levels by 1 dB each; it is now "any of the five outside ±0.5 dB", with the
extreme kept as the limit. The 0.1·f_c-versus-DC offset that the ±0.5 dB
tolerance actually covers is now computed in Appendix A, and the k = 4 row is
told to read the probe tone frequency-selectively, since the filter is
self-oscillating at f_c at that setting and a broadband reading there measures
T3 instead of T2. **T4** — "not flat-topped" is not a measurement; it is now
THD under 15 % against an ideal square's 48.3 %. The row claimed *odd* symmetry
but tested only one side of it, and its h3 bound could be passed by a build with
no harmonics at all; it now has three lettered parts, with the even harmonics
held against h3 as well as against h1 and a `Drive` sweep carrying the presence
test. **T5** — the disconfirmation named only "independent of level", so a peak
that moved 1 dB failed the trait without meeting it; it is now the complement of
both halves, and the row states that the *sign* of the peak-height move is
unsourced here rather than leaving a reader to assume it. T1 and T3 pass as
written. Tier 1 block verbatim; Tier 3 carries both boards.

### H. Palette-verifier pass — §4 and §5 re-checked against the C

2026-09-06, CPython build of audioif (`audiocomponents/.venv/bin/python`),
audioif at `v0.2.0-14-g0b640b3`. Every line citation in §4 and §5 re-checked
with `grep -n`; two were wrong (`src/synthio/__init__.h:119`, and the
"four orders" arithmetic) and are corrected in place with the correction noted.
Corrected: `Biquad.c:45` is the `set_Q` *signature*, so the `Q` slot's
assignment is `:46` and `frequency`'s is `:62`. Confirmed as written: `shared/audioif_feedback_delay.c:231-243` for the loop's low-pass,
high-pass and cubic clip (the clip itself at `:180-184`, odd by construction);
`:83` for the one-frame delay clamp; `:90` for the 0.99 feedback clamp; `:225`
for the `int16` line; `shared/audioif_distortion.c:17`, `:24`, `:31` for the
four fixed curves; `drive.py:30-33` and `:331-334` for the guarded-import
pattern; `cmods/micropython/ports/esp32/mpconfigport.h:69` for
`MICROPY_FLOAT_IMPL_FLOAT`.

**(i) The pole factorisation reproduces exactly.** §4's `σ = −1 ± k^{1/4}/√2`,
`ω = k^{1/4}/√2`, `f = f_c·|σ+jω|`, `Q = |σ+jω|/(2|σ|)` gives, at f_c = 1 kHz,
first-section Q of 2.689 / 6.724 / 12.068 / 18.740 / 38.745 / 78.748 / 158.749
at k = 2.0 / 3.0 / 3.4 / 3.6 / 3.8 / 3.9 / 3.95 — the Appendix B(ii) column,
to three decimals. At k = 0 both sections collapse to 1 kHz at Q 0.5 and the
render reads −0.17 / −1.05 / −3.00 / −12.04 dB at 100 / 250 / 435 / 1000 Hz
against the closed form's −0.17 / −1.05 / −3.01 / −12.04.

**(ii) Resonance tracking, at a level that cannot clip.** Input peak 100,
steady-state peak searched around the analytic maximum, both normalised to
unity DC gain:

| k | built (dB) | analytic (dB) | Δ | at input peak 400 |
|---|---|---|---|---|
| 2.0 | +7.75 | +7.80 | −0.05 | −0.00 |
| 3.0 | +15.50 | +15.54 | −0.04 | −0.00 |
| 3.4 | +20.55 | +20.59 | −0.04 | −0.00 |
| 3.6 | +24.35 | +24.40 | −0.05 | −0.00 |
| 3.8 | +30.65 | +30.70 | −0.05 | −0.00 |
| **3.9** | +36.81 | +36.85 | **−0.05** | **−0.44** |
| **3.95** | +42.89 | +42.93 | **−0.05** | **−6.38** |

The right-hand column is the struck sentence's −0.34 / −6.27, reproduced: it is
the first section's ±32767 state clamp, not the filter.

**(iii) The headroom rule, measured.** First-section output and cascade output
at f_c, by input level:

| k (Q₁) | in 100 | in 200 | in 300 | in 400 | in 800 |
|---|---|---|---|---|---|
| 3.8 (38.7) | 3850 | 7724 | 11599 | 15473 | **28325** ← clipping |
| 3.9 (78.7) | 7822 | 15698 | 23573 | **28377** | **28521** |
| 3.95 (158.7) | 15768 | **28398** | **28521** | **28521** | **28521** |

28521 is the biquad's ±32767 clamp read through the `Filter`'s ±28000 mix-down
knee (`src/audiofilters/Filter.c:288`, `src/synthio/__init__.h:133-134`,
`shared/audioif_synth_dsp.c:20-28`: 28000 + (32767 − 28000)·7151/65536 = 28520).
Usable input peak ≈ 32767/Q₁.

**(iv) Refutation (d) — a series waveshaper is not an in-loop nonlinearity.**
Read, not measured, because the reading settles it: `audiofilters.Distortion`
in `CLIP` mode computes `pow(|v|, drive)` and restores the sign
(`shared/audioif_distortion.c:17-19`), so it is odd and generates a rising odd
harmonic series with drive. Placed after §4's linear two-biquad ladder it would
satisfy **T4(b)** (every even harmonic down) and **T4(c)** (h3 rising
monotonically with `Drive`) with **nothing nonlinear inside the ladder loop** —
the same absence-reads-as-agreement shape Appendix E(c) refuses, one node
further out. It fails **T3** and **T4(a)**, which require self-oscillation the
linear core cannot produce, and it fails T4's own "is inside the loop" clause,
which is why that clause is stated as part of the trait rather than as prose.
`audioecho.FeedbackDelay`'s clip cannot stand in for it either: the clip is
applied to the **delayed** signal inside the loop, never to the dry path
(`shared/audioif_feedback_delay.c:230-243`), so it is not available as a series
waveshaper at all.

Probe scripts are scratch (`ladder_probe.py`, `ladder_res.py`, `head.py`);
all are reproducible from the Phase 0 kit's swept-sine probe, and every level
sweep here exists because the first run of B(ii) mistook a clipped probe for a
filter limit.

**One warning the whole survey needs.** `src/synthio/__init__.h` **moved
between the commit vision §6 names (`7455577`) and this one**: `SYNTHIO_MAX_DUR`
was line 119 there and is line 126 here, and the mix-down range/scale pair was
`:126-127` there and is `:133-134` here. Every other file cited in §4 and §5 —
`Biquad.c`, `Biquad.h`, `audiofilters/Filter.c`, `shared/audioif_biquad.c`,
`shared/audioif_multiply.c`, `audiomixer/Mixer.c`, `docs/upstream-diff.md` — is
byte-identical across those seven commits, so their line numbers hold either
way. `LadderFilter.md` §5 and its Appendix C disagreed with each other on this
exact line, which is how the drift was found. **Seeds should state the audioif
commit their citations are against;** these do now.

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

**Notes.** `capabilities = ()` — a filter has no tempo-dependent behaviour and
does not read the transport (D10). Not stereo-by-definition; mono gets the same
filter on one channel. **Tier 1 and T3 are in tension and the tension is
stated here**: a self-oscillating filter does not return to silence. `Resonance`
at or above self-oscillation is therefore declared to hold **T3 instead of the
silence invariant**, the boundary is a documented macro position, and everywhere
below it the silence invariant holds exactly. **Rate:** cutoff clamps below
Nyquist; T1's 24 dB/octave asymptote cannot be measured above F_s/4, and T3's
180° feedback phase is only guaranteed to F_s/4 (L3 **§5.3** — audit
correction, re-verified against the paper in the second audit: §5.2 is
*Resonance*, and "addition of half-unit delay causes the phase shift to be almost
exactly 180 degrees at cutoff up to about Fs/4 … the error in tuning is less than
10% for f < Fs/4" is §5.3 *Compensation*. **§4 still cites "L3 §5.2" for the same
half-unit delay, and §5 still cites `src/synthio/__init__.h:119` for the 256-frame
block, whose real line is `:126` — as Appendix C already has it; both are outside
this audit's edit boundary and must be fixed when §4 and §5 are next edited**),
so at 22.05 kHz the
top of the cutoff span carries T1 and T3 only up to ~5.5 kHz. Held DC is not
expected: the rebuilt node is `float`, not the fixed-point biquad of audioif#23,
and the shipped biquad cascade already measures exact zero here
(`ParametricEQ.md` Appendix B, last row).

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1** | **Four poles, and the cutoff is the asymptote's crossing, not the −3 dB point.** Cutoff 1 kHz, resonance 0 ⇒ **−12.0 ± 0.5 dB at 1 kHz**, a −3 dB point at **435 ± 20 Hz** (0.4350·f_c), and a stopband slope between **−23 and −27 dB/octave measured 4→8 kHz** *(audit correction — the trait first read "−24 ± 1 dB/octave measured 2→4 kHz", a threshold the ideal fourth-order response itself fails: `1/((s+1)⁴)` falls **−21.26 dB** from 2→4 kHz at f_c = 1 kHz, −23.30 from 4→8, −23.88 from 8→16, and the shipped two-biquad build measures −21.87 and **−25.62** over the first two (Appendix B(i)) because the bilinear transform steepens the response toward Nyquist. 4→8 kHz keeps the band below F_s/4 at both 48 and 44.1 kHz, and −23…−27 admits the ideal and the digital build while still failing a two-pole (−12) or eight-pole (−48) one)*. | L1 eq. 17 and §2.5 (the asymptote through 0 dB at ω = 1 *is* the cutoff); L2 for the four sections; **L4** independently: at cut-off "the total gain is 1/4 and the phase is −180 degrees" | high — analytic, re-derived numerically here (Appendix A) and again by the audit | any of the three outside its band; in particular a −3 dB point at the nominal cutoff, or 48 dB/octave | swept-sine 20 Hz–20 kHz at resonance 0, 48 and 44.1 kHz; report the level at f_c, the −3 dB frequency and the 4→8 kHz slope |
| **T2** | **The passband droops as resonance rises** — DC gain is exactly `1/(1+k)`. At k = 0, 1, 2, 3, 4 the level at 0.1·f_c is **0.00, −6.02, −9.54, −12.04, −13.98 dB, each ±0.5 dB** (the ±0.5 covers the 0.1·f_c reading sitting up to 0.17 dB above the DC value it quotes, recomputed in Appendix A). | L1 eq. 22 and §2.5 (the droop is the type's own test) | high — analytic (Appendix A) | **any of the five outside ±0.5 dB.** In the limit, a passband moving less than 3 dB in total from k = 0 to k = 4 — a resonance that only adds a peak, which is the current class's failure (§7) | magnitude at 0.1·f_c across a resonance sweep; report the five levels. The k = 4 row is read **frequency-selectively at the probe tone only**: at that setting the filter is also self-oscillating at f_c (T3), and a broadband level reading there measures the oscillation, not the passband |
| **T3** | **Self-oscillation at k = 4, at the cutoff, and not before.** Cutoff 1 kHz: at the top of `Resonance` travel one impulse leaves a tone within **3 %** of 1 kHz decaying **less than 3 dB in 2 s**; at 90 % of travel the same impulse falls below **−40 dB within 2 s**. | L1 §2.5 (the pole locus reaching the axis at k = 4); L3 eq. 13 (feedback `4r`, `0 < r ≤ 1`); L2; **L4** independently: "at k = 4, the lowpass filter oscillates at its cut-off frequency", the poles expanding "in an 'X' pattern from s = ωc until the two poles on the right reach the jω axis at ω = ωc" | high | oscillation below the top of travel, or none at the top; or an oscillation away from f_c | impulse then 3 s of silence; report dominant frequency and decay in dB/s at both positions |
| **T4** | **The nonlinearity is inside the loop, is odd, and is what bounds the oscillation.** Three measurable parts. **(a) Bounded:** at self-oscillation the peak stays within **±1 dB over 2 s** and total harmonic distortion is **under 15 %** — the tone is a rounded sine, not a flat-topped one (an ideal square reads 48.3 %). **(b) Odd:** **every even harmonic is below −40 dB re h1 and at least 20 dB below h3**, at self-oscillation and at every `Drive` position of (c). **(c) Present, and in the loop:** at cutoff 1 kHz and a fixed k = 3.9 (below oscillation), on a held 1 kHz tone sitting on the resonant peak, **h3 re h1 rises monotonically** across `Drive` = 0, +8, +16, +24 dB, by at least **10 dB** end to end — the floor is deliberately far below what a cubic-dominant odd nonlinearity gives (h3/h1 ∝ A², so up to 48 dB across a 24 dB drive rise before compression sets in), so that passing it is evidence and failing it is unambiguous. | L1 eq. 5 (the odd series); L3 eq. 1 and eqs. 13–17 (a `tanh` at each stage input); L3 §1 for (c)'s mechanism | high for the odd symmetry (the topology's algebra); medium for the thresholds, which are ours | **any of (a), (b), (c) missed.** An even harmonic above −40 dB, or h2 within 20 dB of h3 (the nonlinearity is not odd); THD above 15 %, or a peak drifting more than ±1 dB — in particular one growing without bound (nothing bounds the loop); h3 flat or falling across `Drive`, or moving under 10 dB (nothing nonlinear is in the loop — the shape §5(c)'s refuted fallback produces, and the one place absence could otherwise read as a pass) | STFT of a 2 s self-oscillation capture and of a held tone at the four `Drive` positions; report h2…h7 against h1, the THD, and the peak envelope over the 2 s |
| **T5** | **Drive is the only warmth control: character follows input level.** At fixed cutoff and k = 3, a 20 dB input rise moves the resonant peak's height by at least **3 dB** and raises THD monotonically; below −40 dBFS input, THD is under **0.5 %**. | L3 §1 and §4.2's per-stage `tanh` | medium — the mechanism is certain, the two thresholds ours, and the **sign** of the peak-height move is deliberately not asserted: no source reached in this run states which way a Moog ladder's resonant peak goes with input level, so the trait fixes the magnitude and Phase 2 records the direction it measures | **either half missed.** The peak height moving less than 3 dB across a 20 dB input rise, or THD not rising monotonically with level — in the limit both independent of level, i.e. a linear loop, which is exactly what §5's composed fallback gives; or THD at or above 0.5 % below −40 dBFS in, which is a nonlinearity that never gets out of the way | swept-sine and a held chord at four input levels; report peak height (with its sign of movement), THD and the harmonic ladder at each |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Audit, 2026-09-06.** Every row above was independently re-fetched and re-read by
the licence-and-citation audit, not taken from this seed: L1, L3 and L4 downloaded
and read with `pypdf`; L2 read as HTML. Corrections are marked in place. Nothing in
§1 or §3 was found without a source row; every equation number, section number and
quotation in §1 and §3 was matched against the source text, and every derived number
in Appendix A was recomputed (see the note there).

*(from §2)* — the source table's **URL** and **Reached** columns, and the licence cells in full, as the licence-and-citation audit wrote them:

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **L1** Stinchcombe, *Analysis of the Moog Transistor Ladder and Derivative Filters*, 25 Oct 2008, 51 pp. | the whole derivation: `f_c = I_f/(8π C V_T)` (eq. 13), core `−1/(s+1)⁴` (eq. 17), `H = 1/((s+1)⁴+k)` (eq. 22), the pole locus `s = −1 ± k^{1/4}e^{±jπ/4}` and k = 4, the −12 dB and −14 dB readings, the pair's tanh (eq. 5), and why a diode ladder differs (§3.1) | **No licence and no copyright line in the PDF, and none on the hosting site's pages** — re-checked independently in this audit run against the PDF (51 pages, its own metadata dated 2008-10-25) and against `timstinchcombe.co.uk`'s home page and synth index. An author-hosted paper: **license unverified, treated as copyleft**, read as a paper and its mathematics re-derived, no code taken | https://www.timstinchcombe.co.uk/synth/Moog_ladder_tf.pdf | fetched and read via `pypdf` in the audit run; every equation, quotation and section number cited in §1 and §3 was matched against the text |
| **L2** Moog, *Electronic High-pass and Low-pass Filters Employing the Base to Emitter Diode Resistance of Bipolar Transistors*, US 3,475,623, granted 28 Oct 1969 | the primary topology: four identical sections of one capacitor and two transistors; the standing-current control; the variable feedback resistor from output to input; cutoff exponential in control voltage over ~1000:1 | expired US patent — a public disclosure document; the page names Robert A Moog as inventor, gives 1969-10-28 as the publication date, and shows legal status "Expired - Lifetime" (all three re-read in the audit run) | https://patents.google.com/patent/US3475623A/en | re-read in the audit run; the three quoted phrases were matched in the patent's own text |
| **L3** Huovilainen, *Non-Linear Digital Implementation of the Moog Ladder Filter*, Proc. DAFx-04, Naples, pp. 61–64 | the per-stage differential equation and its Euler solution; the four-stage difference equations with `4r` feedback (eqs. 13–17); `g = 1 − e^{−2πF_c/F_s}` (eq. 21); "only five tanh calculations per sample are required" (§4.2); the half-sample feedback delay — "almost exactly 180 degrees at cutoff up to about Fs/4", "the error in tuning is less than 10%" (**§5.3**); 2× oversampling | **No copyright or licence line in the paper** — re-checked in this audit run; `dafx.de/paper-archive/2004/` still returns **404** while the PDF itself serves (HTTP 200), and the file's own page furniture confirms the proceedings and page numbers. **License unverified, treated as copyleft**: read as a paper and its mathematics re-derived, no code taken | https://dafx.de/paper-archive/2004/P_061.PDF | fetched and read via `pypdf` in the audit run; eq. (1), eqs. (13)–(15), eq. (21), the five-`tanh` sentence and the §5.3 result were each matched in the text |
| **L4** Stilson & Smith, *Analyzing the Moog VCF with Considerations for Digital Implementation*, ICMC 1996, 11 pp. — **added by the audit: this seed recorded it as not fetched, and it is one fetch away**, at the URL L1's own reference list prints | an independent second derivation of traits this seed already fixes: the four one-pole sections are "inverting at cut-off" with "total gain … 1/4" (**T1's −12.04 dB**); "as the feedback gain k approaches 4 … the gain at resonance goes to infinity"; "at k = 4, the lowpass filter oscillates at its cut-off frequency", the poles expanding "in an 'X' pattern from s = ωc until the two poles on the right reach the jω axis at ω = ωc" (**T2's mechanism and T3, from a source independent of L1**). It is also the paper L3 §5.3 answers. Quotations in Appendix F | **no copyright or licence line in the PDF**; author-hosted at CCRMA — **license unverified, treated as copyleft**, read as a paper, no code taken | https://ccrma.stanford.edu/~stilti/papers/moogvcf.pdf | fetched (HTTP 200, 11 pages) and read via `pypdf` **in the audit run** |

*(from §3)*

**One sub-claim is left unmeasured, on purpose.** T4 states no *absolute* floor
for h3 at self-oscillation — only that h3 must move with `Drive`. **Unmeasured:
the third harmonic's level at the oscillation boundary.** Two things push it
down and no source reached here fixes where it lands: just above k = 4 the
`tanh` is barely compressing, so the harmonic it generates is small; and the
ladder's own fourth-order path attenuates the third harmonic by **28.0 dB**
relative to f_c before it reaches the output (at k = 0, `|H(3ω_c)|/|H(ω_c)|` =
4/100; the fifth is 44.6 dB down — both computed from L1 eq. 17 in the
trait-critic pass), with the resonance widening the gap further. A threshold
guessed here would produce a false disconfirmation of a faithful build, which is
worse than an honest gap. T4(c) carries the presence test instead, where the
nonlinearity is actually being driven.

*(from §3)*

Budget as a fraction of one stereo block's deadline (256 frames, 5.33 ms at
48 kHz): **P4 8 %, S3 14 %** at the default 2× oversampling; **P4 4 %, S3 7 %**
with oversampling off. Arithmetic in Appendix C. **Lean patch expected: yes** —
`"Ladder - lean"` runs at 1× with a shorter `tanh` table, trading alias floor for
budget, and never compromises the faithful patch.

*(from §3)*

**Latency: zero from the filter itself.** A ladder is recursive: every stage
reads only samples it has already been given, and the dry path through `mix` is a
wire. The one latency source is the **anti-aliasing filter around oversampling**,
which is an option and defaults to its shortest: the default is a short
minimum-phase half-band whose group delay is reported in `latency_samples` the
moment oversampling is on, and `Oversample = off` reports exactly **0**. The knob
that trades CPU for latency is therefore `Oversample`, and the knob that trades
alias floor for latency is the half-band's length — Phase 1 fixes both numbers,
Station C measures the reported value against a click. No lookahead, no
partition, no window anywhere in this class.

*(from §4)*

- **Linear core:** two `synthio.Biquad(LOW_PASS, f, Q)` in one
  `audiofilters.Filter`, `f` and `Q` as block slots (`src/synthio/Biquad.c:46`,
  `:62`) recomputed in Python on a macro move from `k` — `σ = −1 ± k^{1/4}/√2`,
  `ω = k^{1/4}/√2`, `f = f_c·|σ+jω|`, `Q = |σ+jω|/(2|σ|)` — plus a `1/(1+k)`
  gain that *is* T2's droop.

*(from §4)*

- **Nonlinear core:** the one thing the palette cannot do (§5). Where the node
  is present the class builds it; where it is not, construction raises a clear
  `ImportError` behind a guarded import, the pattern `CabinetSim` already uses
  (`drive.py:30-33`, `:331-334`).

*(from §4)*

- **Tables** — the `tanh` lookup L3 §4.2 recommends in place of five
  transcendental calls per sample — are computed once on CPython by a generator
  script and shipped as data, never rebuilt on a board, whose floats are
  single-precision (`cmods/micropython/ports/esp32/mpconfigport.h:69`).

*(from §4)*

- **Tuning:** `g = 1 − e^{−2πF_c/F_s}` (L3 eq. 21) with the half-unit feedback
  delay that holds loop phase near 180° at cutoff up to F_s/4 (L3 §5.2), under
  2× oversampling, the residual folded into one table with the resonance
  compensation as L3 does.

*(from §4)*

- **The Nyquist clamp goes on the derived section frequencies, not on the
  `Cutoff` macro.** The factorisation puts the second pole pair at
  `f_c·|σ+jω|`, rising to **2.236·f_c** at k = 4 (σ = −2, ω = 1), so at
  22.05 kHz a cutoff above ~**4.9 kHz** puts that section over Nyquist at full
  resonance — and a `synthio.Biquad` over Nyquist does not refuse, it rails
  into a full-scale ±28521 square wave at f_s/4 within ten samples, silently
  (`GraphicEQ.md` Appendix E(iv)). A `Cutoff` clamped only to Nyquist still
  rails. The kit must drive **signal** at 22.05 kHz, not silence — silence
  renders exact zeros through the same broken section.

*(from §4)*

- **The build's headroom falls with resonance, and that is a palette fact.**
  Each biquad clamps its own state at ±32767
  (`shared/audioif_biquad.c:163-164`, `:174-175`), and the factorisation puts
  *all* the resonance in the first section — Q 38.7 at k = 3.8, **158.7 at
  k = 3.95** — so the *intermediate* value clips long before the output does.
  Measured at f_c = 1 kHz the cascade stays linear to an input peak of ~400 at
  k = 3.8, ~300 at k = 3.9 and **~150 at k = 3.95**, about −47 dBFS in
  (Appendix H(iii)). Usable input peak ≈ 32767/Q₁: **six dB of headroom per
  doubling of Q₁**. The ladder node has no such intermediate word — a fourth,
  independent reason for it, not a restatement of T3/T4/T5.

*(from §5)*

- **What the palette does instead, and the measurement that ends it.** §4's
  two-biquad build is *linear*. It reproduces T1 and T2 to 0.01 dB and follows
  the resonance **to within 0.05 dB at every k from 2.0 to 3.95**
  (Appendix B(ii)), and cannot reach k = 4 at all because that Q is infinite
  and not representable. Being linear it can never sustain from silence, so
  **T3 fails at its own definition**; it has no nonlinearity, so **T4's
  harmonic ladder does not exist** and **T5's level dependence is identically
  zero** — which is T5's stated disconfirmation condition. Not close calls.
  *(Palette-verifier correction, 2026-09-06: this read "then falls 0.34 dB
  short at k = 3.9, 6.3 dB at k = 3.95". Appendix B's audit had already found
  those to be **the probe clipping, not the filter** and could not edit here; a
  third run settles it — at input peak 100 the build tracks analytic by
  −0.05 dB at every k through 3.95, and at input peak 400 the same build
  reproduces −0.44 and −6.38 with the first section on its ±32767 clamp
  (Appendix H(ii)). The ask never rested on a shortfall below k = 4, and now
  does not appear to.)*

*(from §5)*

- **Why nothing else in the palette covers it.** *(Every citation in this
  bullet re-checked by `grep -n` in the palette-verifier pass, 2026-09-06; two
  were wrong and are corrected in place.)* An audioif graph is a **pull DAG** —
  a node takes its source at construction or `play()` and nothing accepts its
  own output — so a feedback loop can only exist **inside one node's C kernel**,
  and the kernels that have one are these. `audioecho.FeedbackDelay`'s loop
  holds one one-pole low-pass, one one-pole high-pass and a cubic odd soft clip
  (`shared/audioif_feedback_delay.c:231-243`, the clip at `:180-184`), with the
  delay clamped to at least one frame (`:83`), feedback to 0.99 (`:90`), and the
  line stored as `int16` (`:225`) — one one-pole behind a delay of a frame or
  more is a comb, not four one-poles round a zero-delay loop, and its resonances
  are harmonics of 1/delay rather than one movable cutoff.
  `audiofreeverb.Freeverb` is a fixed comb/all-pass network and `audiofilters.
  Phaser` a first-order all-pass cascade whose stages are magnitude-flat, so
  neither has a fourth-order low-pass to feed back. `audiofilters.Filter` has no
  feedback path at all, and Python drives it at block rate
  (256 frames = 5.33 ms, `SYNTHIO_MAX_DUR` at **`src/synthio/__init__.h:126`**),
  **256× too slow** for a per-sample loop. `audiofilters.Distortion` offers four
  fixed curves (`shared/audioif_distortion.c:17`, `:24`, `:31`) and, being a
  source-taking node, cannot sit inside another node's loop.
  *(Two corrections, and the first is a finding about the survey, not this
  seed. `__init__.h:119` **was** `SYNTHIO_MAX_DUR` at audioif `7455577`, the
  commit vision §6 names; it moved to `:126` in the seven commits since. So the
  citation was right when written and is wrong now — and **no seed states which
  audioif commit its numbers are against**, which the whole survey needs.
  Second: 48 kHz against a 187.5 Hz block rate is 256×, ~2.4 orders of
  magnitude, where this read four.)*

*(from §5)*

- **The ask.** A **new audioif-own module** — `audiofilters` is a CircuitPython
  port and never changes — call it `audioladder.Ladder`: four one-pole stages in
  `float` with a table-lookup odd saturator at each stage input; global feedback
  `k` in 0…4.2 (past 4, so T3's boundary sits inside the span); `frequency` and
  `resonance` as synthio block inputs; optional 2× oversampling reported in
  `latency_samples`; and a passband-compensation coefficient so `1/(1+k)` can be
  dialled from faithful to flat without leaving the topology. The saturator's
  table is generated on CPython and shipped as data (§4).

*(from §5)*

- **Refutation record:** **four** attempts to compose the ask away, each ended
  by a measurement or a reading — Appendix E, plus (d) in Appendix H(iv). (d)
  is the palette-verifier pass's addition and the one most likely to be
  mistaken for a pass: the linear two-biquad ladder followed by
  `audiofilters.Distortion` in `CLIP`, a genuinely odd waveshaper
  (`shared/audioif_distortion.c:17-19` restores the sign after a power law),
  which would **satisfy T4(b) and T4(c) with nothing nonlinear inside the
  ladder loop at all**. It fails T3 and T4(a), which need self-oscillation.
  **The ask stands on T3, T4(a), T4's in-loop clause and T5** — not on the
  resonance shortfall the struck sentence claimed, and not on §4's headroom
  rule, which is a separate additional reason.

*(from §7)*

1. **It is not a ladder.** Four `synthio.Biquad(LOW_PASS, …)` in one cascade
   (`eq.py:179-184`) is **eight poles**, not four: at the shipped default cutoff
   1200 Hz with resonance 0 it measures **−23.94 dB at 1200 Hz** where T1
   requires −12.04, with a −3 dB point near **305 Hz** against the ladder's
   522 Hz. It filters an octave and a half below where it says it does.

*(from §7)*

2. **Resonance adds a peak and no droop.** `q = 0.55 + 6.0 * resonance`
   (`eq.py:178`) pushes the last two biquads' Q; measured at 50 Hz, well inside
   the passband, the level reads **−0.10 / +0.02 / +0.02 dB** at resonance
   0 / 0.4 / 0.9 where T2 requires 0.00 / −8.28 / −13.24. **The most
   recognisable behaviour of the circuit is absent at every setting.**

*(from §7)*

4. **`resonance` has no macro** — `MACRO_LABELS = ()` (`eq.py:171`),
   `PATCHES = {0: ("Default", ())}` (`:173`) — so a host cannot sweep the one
   control this filter exists for; `set_cutoff()` (`:189-190`) is a Python
   method, not a surface.

*(from §7)*

5. **`check_hz()` refuses instead of clamping** (`eq.py:177`, `:190`; the raise
   at `_core.py:471-474`). A cutoff macro at the top of its span must clamp
   below Nyquist at 22.05 kHz, not raise from `set_macro`.

*(from §7)*

6. **The docstring claims what the code does not do** — "four cascaded
   one-pole-pair low-passes", "24 dB/octave slope" (`eq.py:163-165`) against an
   eight-pole 48 dB/octave build. The rebuild's docstring states its measured
   latency in ms and its measured slope, and the gate checks the docstring
   against the measurement.

*(from §7)*

7. **Inherited:** `Effect.__new__` mutates module-wide format state
   (`_core.py:149-152`); `reset()` (`_core.py:368`) touches only the output
   node, while a `Filter` resets its source recursively — so a chain's reset
   today depends on which node happens to be last (roadmap §3).

### App. S — Station A: what the node's arrival settled, and the text it replaced

**2026-09-07, Station A.** The seed was written in Phase 0, when §5's node was
an ask. It landed as `audioladder.Ladder` in effects Phase 1 and is on the pin
this program builds against. Sections 4, 5 and 6 are rewritten above against
the node that exists; **nothing is deleted** — what they said before is
reproduced here verbatim, and the seed's own reasoning is what the reader
should compare the node against.

**What changed, in one line each.**

| Seed said | Node shipped | Consequence |
|---|---|---|
| build the linear core from two `synthio.Biquad` sections factored from `(s+1)⁴+k` | one `audioladder.Ladder` | the composition is not built at all; App. H's measurements become the *refutation record*, not the design |
| a `tanh` lookup table, resolution TBD (Q1) | `x − x³/3`, two multiplies, no table (`audioif_ladder.c:66-69`) | **Q1 settled by removing its premise** |
| a half-band filter whose length and phase type set the class's only latency (Q2) | linear interpolation up, two-tap average down, half a sample for the pair (`audioif_ladder.c:305`, `:310`) | **Q2 settled: `latency_samples = 0`, no latency-adding option** |
| `g = 1 − e^{−2πF_c/F_s}` (L3 eq. 21) with a half-unit feedback delay | `g = tan(πf_c/f_s′)/(1+tan(...))`, no delay in the loop at all (`audioif_ladder.c:80-82`, `:194-217`) | T3 lands at k = 4 and at f_c exactly, which the delayed form did not (3.5, six per cent flat) |
| eight macros including `Slew` | no slew option on the node | **`Slew` dropped**, reason in §6; filed as Q6 |
| `Poles` as a TOGGLE | four taps | **`Poles` is UNIPOLAR**; the contract's TOGGLE is two-state |

**What did NOT change: §§1–3.** The circuit paragraph, the sources, and every
Tier 1 and Tier 2 trait are the seed's and the trait-critic pass's, unedited.
A node arriving is not a reason to move a threshold, and if the node misses one
of them that is the node's result to record, not the trait's to soften.


#### The Station A text these sections replace, verbatim

##### §3 Tier 3, the reasoning behind the two budgets

###### Tier 3 — cost and latency  *(parked verbatim)*

**Latency budget: 0 samples**, at every setting, and there is **no
latency-adding option**. The node's 2× path is a linear interpolation up and a
two-tap average down — half a sample of group delay for the pair, which rounds
to the 0 it reports (`audioif/src/shared/audioif_ladder.c:305`, `:310`;
`docs/upstream-diff.md`, "which is why the node reports no latency"). That is
inside the stompbox budget (vision §9a) with nothing spent, which is the whole
of Q2's answer (§8).

**Cost budget**, from Appendix C's arithmetic — one stereo block is 256 frames
= 512 samples = 5.33 ms, so **1,280,000 cycles on a 240 MHz S3** and
**2,133,000 on a 400 MHz P4**:

| Board | Patch | Budget, share of one stereo block |
|---|---|---|
| ESP32-P4 | 0 (`oversample` on) | **8 %** |
| ESP32-S3 | 0 (`oversample` on) | **14 %** |
| ESP32-S3 | 6 `Ladder - lean` (`oversample` off) | **7 %** |

These are ceilings the class gate measures against, not predictions, and the
arithmetic behind them is Appendix C's 180 cycles/sample/channel estimate for a
*table-driven* saturator. The node that shipped has **no table** — its
saturator is two multiplies (`audioif_ladder.c:66-69`) and its solver four
fixed passes of three multiplies (`audioif_ladder.h:49`,
`audioif_ladder.c:211-213`) — so the estimate is very likely generous. It is
left as it stands rather than re-guessed: Station C's board run replaces it
with a measured number, and a budget loosened by argument is not a budget.

**`tail_samples` is `None`, and that is a statement about the circuit**: below
k = 4 the tail is a decaying resonance with no finite bound stated by any
source reached here, and at and above k = 4 the class holds T3 instead of the
silence invariant (App. I) and does not decay at all.

##### §4's four decisions, with the C read out in full

###### 4. Modeling approach on the palette  *(parked verbatim)*

**One node: `audioladder.Ladder`.** §5's ask landed between the seed and this
station, so the build is no longer a composition. `Ladder` is four
topology-preserving one-pole stages round a global feedback loop with the odd
cubic saturator *inside* the loop — the shape §1 derives — and every option §6
puts on a macro is one of its seven
(`audioif/src/shared/audioif_ladder.h:52-60`).

The four decisions that used to be this section's argument are now the node's,
and each is checked against the C rather than recalled:

- **The loop is solved, not delayed.** `y + a·sat(y) = c` with `a = k·g⁴`, four
  fixed passes seeded by extrapolating the last two solved samples
  (`audioif_ladder.c:194-217`, `audioif_ladder.h:44-49`). This is what puts
  self-oscillation at **exactly** k = 4 and **exactly** at the cutoff — T3's
  two clauses. One sample of feedback delay, the obvious way to write it,
  measured 3.5 and six per cent flat (`audioif_ladder.c:11-23`), which would
  fail T3 as stated.
- **Tuning is `g = tan(πf_c/f_s′)/(1 + tan(πf_c/f_s′))`, not L3 eq. 21's
  `1 − e^{−2πF_c/F_s}`** (`audioif_ladder.c:80-82`). A bilinear one-pole is
  what makes the four stages reach −180° with a gain of exactly 1/4 at the
  cutoff; the seed's exponential mapping is the impulse-invariant form and does
  not. **T1's numbers are unchanged** — they are the analytic ladder's, and the
  bilinear map is the one that lands on them. `f_s′` is the rate times
  `oversample`, and `cutoff_hz` is stored as asked for and clamped where it is
  used (`:79`, `:116-119`), so turning oversampling off cannot leave a stale
  coefficient behind.
- **The saturator is `x − x³/3`, clamped, not a `tanh` table**
  (`audioif_ladder.c:66-69`). Odd by construction, unity slope at the origin —
  so it does not move the feedback at which the loop sustains — and the same
  curve `audioif_feedback_delay.c` already puts in its own loop. This answers
  Q1 (§8) by removing its premise: there is no table to size.
- **The Nyquist clamp is the node's own**, `1 Hz … 0.49·f_s′`
  (`audioif_ladder.c:79`), and the class clamps on top of it with
  `self._hz()` — `0.49·f_s` exactly, which is the node's clamp at
  `oversample = 1` and conservative at 2. Rate-honest: at 22.05 kHz the top of
  the `Cutoff` span *becomes* 10.8 kHz rather than raising (App. I).

- **Headroom.** The old two-biquad build lost usable input peak as `1/Q₁`
  (App. H(iii)); the node does not have that failure — its working domain is
  ±1 float and the saturator bounds the loop — but it has its own: at
  self-oscillation the node's own tone is what fills the output, so the
  measurable headroom for the *signal* falls as `Resonance` rises. That is the
  circuit, not the build.
- **Mono:** the same filter on one channel, per-channel state
  (`audioif_ladder.h:100-110`); not stereo-by-definition.
  **Portability tier: audioif.**

*(§4 as it stood before the node landed, verbatim, is in **App. S**. More of
§4 is in **App. R** — both moved under the length rule, nothing deleted.)*

##### §5's delivery note in full

###### 5. Node asks  *(parked verbatim)*

**The one ask is DELIVERED.** `audioladder.Ladder` shipped in effects Phase 1
and is on the audioif pin this program builds against
(`audioif/docs/upstream-diff.md`, "`audioladder`: the loop CircuitPython's
filters cannot close"). Nothing here is outstanding.

- **What it unblocks: T3, T4, T5** — exactly the three the seed named, and for
  exactly the reason the seed gave. The node's own header states the same three
  in the same order (`audioif/src/shared/audioif_ladder.h:8-17`), reached
  independently.
- **T1 and T2 were never asks** and the seed said so. They are reachable on
  stock biquads (App. H), and that is why this dossier's §7 defect 1 is about
  the *shape* of the old cascade and not about a missing node.
- **The seed's four refutations still stand**, and the node closes the same
  gap they left open: (a) four low-passes at one cutoff fails T1; (b) the pole
  factorisation reaches T1 and T2 and fails T3/T4/T5 by construction; (c) a
  block-rate level law fakes T5 and makes no harmonics, so T4 would read absence
  as agreement; (d) a series waveshaper after a linear core satisfies T4(b) and
  T4(c) with nothing nonlinear inside the loop (App. E, App. H(iv)).
- **One ask, one module, as asked.** `audioladder` is a module of its own and
  not an argument on `audiofilters.Filter`, for the reason §5 gave: an argument
  on audioif's copy of a CircuitPython module would not exist on a stock board,
  so the class would silently be a different effect there
  (`audioif/src/shared/audioif_ladder.h:1-27`).

*(§5 as it stood before the node landed, verbatim, is in **App. S**. More of
§5 is in **App. R** — both moved under the length rule, nothing deleted.)*

##### §6's two surface changes, argued in full

**Two changes from the seed's eight, each with its reason:**

- **`Slew` is dropped.** It was "cutoff glide, the click-free knob every swept
  filter needs", and there is nowhere honest to run it. `Ladder` has no slew
  option, and `_component.Component` gives a class no per-block hook —
  `_apply_macro` is called only when a macro *moves*
  (`lib/audioeffects/_component.py:505-517`, `:588-594`), so a Python glide
  would advance only while the knob was being turned, which is the opposite of
  what a glide is for. A macro move already lands once a block (~187 Hz at
  48 kHz), which is the resolution a host gives it. **Filed rather than faked:**
  the honest place for this is a `slew_ms` option on the node, and it is §8 Q6.
- **`Poles` is UNIPOLAR, not TOGGLE.** It has four positions, and the contract's
  TOGGLE is two — `_check_patches` refuses a TOGGLE patch value that is not 0 or
  127 (`lib/audioeffects/_component.py:314-317`). A four-way selector on a
  two-state mode would be a metadata lie that happens to construct.

##### §8's five answers, with the readings behind them

###### 8. Open questions  *(parked verbatim)*

Five were open at the seed. **Three are settled here**, from the node that
landed and from the seed's own evidence; one is Station C's first measurement
by the seed's own instruction; one stays open and is not a blocker. One new
question is filed rather than faked.

1. **The saturator's table resolution and the oversampling factor.**
   **SETTLED — the premise is gone.** `Ladder`'s saturator is `x − x³/3`,
   clamped, two multiplies and no table at all
   (`audioif/src/shared/audioif_ladder.c:66-69`). There is no resolution to
   choose. The factor is settled too: `oversample` is 1 or 2 and **defaults to
   2** (`:100-104`, `:158`), on the node's own reasoning — "half the cost is
   the wrong saving on the one node whose job is to distort". It is macro 5 and
   patch 6 is the lean valve, so the cost-versus-alias table the vision §10.3
   owns for the waveshaper is a *measurement* on this class, not a decision it
   is waiting on.
2. **The half-band filter's length and phase type.** **SETTLED — there is no
   half-band filter.** The 2× path is a linear interpolation up and a two-tap
   average down (`audioif_ladder.c:302-311`); the pair costs half a sample of
   group delay and the node reports none. So `latency_samples = 0` at every
   setting, **there is no latency-adding option to default off**, and the
   stompbox budget (vision §9a) is met with nothing spent. What it costs
   instead is stopband rejection, and that is what Station C measures as SPECTRUM
   rather than as latency.
3. **Whether `Poles` belongs on the surface.** **SETTLED — kept, as the seed
   recommended**, and its own reasoning is what settles it: it costs nothing to
   offer (the node taps a stage that is computed either way, `:265-271`), the
   feedback is always the fourth stage so resonance and self-oscillation are the
   same filter's at every tap, and the risk it named is answered by stating the
   setting. **Every Tier 2 trait is measured at `Poles = 4`**, in §6 and again
   in the evidence pack. It is UNIPOLAR, not the seed's TOGGLE (§6).
4. **The sign of T5's peak-height move, and an absolute floor for h3 at
   self-oscillation.** **Still open, deliberately, and it is Station C's to
   close** — the seed's own instruction: "from its own first measurement,
   recorded as the trait's real number, not back-fitted into the threshold".
   Nothing in the seed's evidence fixes either, and the node's own upstream note
   reports neither as a signed quantity. Station C records what it measures and
   does not move T5's ±3 dB bar to match it.
5. **A Moog service drawing with values.** **Still not reached, still not a
   blocker.** Appendix D has the searches; no URL was fetched at this station.
   The traits are topological once ω_c is set, which is the grade's whole
   argument, and the node's tuning law is bilinear rather than the seed's
   exponential (§4) — so a drawing would now check L1's simulation range
   against a shipped instrument's, and nothing in §3.
6. **New: `slew_ms` on `audioladder.Ladder`.** Raised by dropping the seed's
   `Slew` macro (§6). A cutoff glide has to run per sample or per block *inside*
   the node; Python cannot reach it, because `_component` calls `_apply_macro`
   only on a macro move. **Not this class's to build** — it is a node option, so
   it is an audioif ask, and the class ships without a glide rather than
   shipping a Python one that only moves while the knob does. To be filed as an
   audioif issue by the session that opens the Phase 1 node backlog; recorded
   here so it is not lost between the two repositories.

#### §8 as the seed wrote it, verbatim


1. **The saturator's table resolution and the oversampling factor**, as a
   cost-versus-alias-floor table on both boards. The vision's §10.3 already owns
   this question for the waveshaper; this node's answer should be taken with it
   rather than separately. *Phase 1, the implementation session.*
2. **The half-band filter's length and phase type**, which sets the only latency
   this class has. Minimum-phase costs less delay and some phase error inside
   the band; linear-phase costs more delay. *Phase 1*, decided against the
   stompbox budget (vision §9a), reported in `latency_samples` either way.
3. **Whether `Poles` belongs on the surface.** It is not on a Moog panel; it is
   on several derivatives'. It costs nothing to offer and it weakens T1 if a
   gate is run at the wrong setting. Recommendation: keep it, and state that
   every Tier 2 trait is measured at `Poles = 4`. *Implementation session.*
4. **Two numbers the trait-critic pass refused to guess.** The **sign** of T5's
   peak-height move with input level, and an **absolute floor for h3** at
   self-oscillation (T4's note). Both are stated as unknown rather than
   assumed, because a guessed threshold here would disconfirm a faithful build.
   *Implementation session, Phase 2*, from its own first measurement — recorded
   as the trait's real number, not back-fitted into the threshold.
5. **A Moog service drawing with values** was not reached (Appendix D). The
   traits are topological and do not depend on the values, but a drawing would
   let the `f_c = I_f/(8π C V_T)` law be checked against a shipped instrument's
   real range instead of Stinchcombe's simulation values. Not a blocker.

#### §4 as the seed wrote it, verbatim


Compose-first, and the composing goes further than expected. **The linear ladder
is exactly two biquads**: `(s+1)⁴ + k` factors into two conjugate pole pairs, so
`H(s)` is a cascade of two second-order low-passes whose centres and Qs Python
computes from `k`. Measured here against the analytic response, that build
agrees **within 0.05 dB at every k from 0 to 3.95** — the whole span short of
oscillation (Appendix H(ii); the earlier "0.01 dB to k = 3.8, then a
shortfall" reading was the probe clipping, §5). The near-oscillation decay
rate tracks to within 10 % at k = 3.999, and that row alone is **not settled**:
Appendix B's audit re-run clipped at k = 3.99 and this pass did not re-take it.
At k = 0 the pair collapses
to two `LOW_PASS` biquads at Q = 0.5, reproducing `1/(s/ω_c+1)⁴` to 0.00 dB
through the passband. So the build is:

- **Linear core:** two `synthio.Biquad(LOW_PASS, f, Q)` in one …  *(argument in full: App. R)*
- **Nonlinear core:** the one thing the palette cannot do (§5). Where the node …  *(argument in full: App. R)*
- **Tables** — the `tanh` lookup L3 §4.2 recommends in place of five …  *(argument in full: App. R)*
- **Tuning:** `g = 1 − e^{−2πF_c/F_s}` (L3 eq. 21) with the half-unit feedback …  *(argument in full: App. R)*
- **The Nyquist clamp goes on the derived section frequencies, not on the …  *(argument in full: App. R)*
- **The build's headroom falls with resonance, and that is a palette fact.** …  *(argument in full: App. R)*
- **Mono:** the same filter on one channel; not stereo-by-definition.
  **Portability tier: audioif.**

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

#### §5 as the seed wrote it, verbatim


**One ask: the nonlinearity inside the feedback loop.**

- **Traits it unblocks: T3, T4, T5.** T1 and T2 are **not** asks — they are
  reachable on stock biquads (§4), and this seed says so rather than bundling
  them in.
- **What the palette does instead, and the measurement that ends it.** §4's …  *(argument in full: App. R)*
- **Why nothing else in the palette covers it.** *(Every citation in this …  *(argument in full: App. R)*
- **The ask.** A **new audioif-own module** — `audiofilters` is a CircuitPython …  *(argument in full: App. R)*
- **Refutation record:** **four** attempts to compose the ask away, each ended …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

#### §6 as the seed proposed it, verbatim


Eight macros, well under the ceiling — a ladder has few knobs and should.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Cutoff | UNIPOLAR | 20 Hz–18 kHz, exponential | the Cutoff knob (exponential is the circuit's own law, L2) |
| 1 | Resonance | UNIPOLAR | k = 0…4.2 | the Emphasis / Regeneration knob; T3's boundary is a documented position inside the span |
| 2 | Drive | UNIPOLAR | 0…+24 dB into the ladder | the input level — the only warmth control the circuit has (T5) |
| 3 | Passband Comp | UNIPOLAR | 0 faithful … 1 flat | none — how much of T2's `1/(1+k)` droop is compensated; **defaults to 0** |
| 4 | Poles | TOGGLE | 1 / 2 / 3 / 4 | the ladder's lower taps, which several derivatives put on the panel; defaults to 4 |
| 5 | Slew | UNIPOLAR | 0…50 ms | none — cutoff glide, the click-free knob every swept filter needs |
| 6 | Oversample | TOGGLE | off / 2× | none — Tier 3's CPU-versus-alias knob; defaults to 2×, and `off` reports `latency_samples` 0 |
| 7 | Mix | UNIPOLAR | 0…1 | none — the contract's wire-at-zero |

**Characters:** none. **Patches:** `0 Wide Open` · `1 Squelch At The Knee` ·
`2 Sustained Sine At Cutoff` (T3's boundary as a patch) · `3 Dark Slow Sweep` ·
`4 Growl With Drive` · `5 Two Pole Soft` · `6 Ladder - lean`.

`Passband Comp` defaults to 0 deliberately: T2 is the trait that identifies this
filter, and a class shipping with the droop compensated away would pass its own
gate while sounding like something else.
