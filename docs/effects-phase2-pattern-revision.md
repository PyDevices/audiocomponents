# Phase 2 — the station pattern's one revision

**Asked for by** [`effects-roadmap.md`](../../docs/effects-roadmap.md)
Phase 2 Work: *"The station pattern's one revision, written down: what the kit
lacked, what the dossier template got wrong, what the refutation pass
caught."*
**Written by** the Phase 2 gate auditor, 2026-09-07, on
`effects/p2-integration`, from the sixteen evidence packs, their refutation
records, and the auditor's own re-runs.
**Companion:** [`effects-phase2-gate-audit.md`](effects-phase2-gate-audit.md)
— the per-class gate table and the verdicts.
**Changes landed with it:** [`effects/TEMPLATE.md`](effects/TEMPLATE.md) and
[`effects/EVIDENCE-TEMPLATE.md`](effects/EVIDENCE-TEMPLATE.md).

Sixteen classes went through three stations. An independent refutation pass
then attacked every clause the packs graded **demonstrated** — 45 of them
broke, across all sixteen classes, and the gate audit upheld all 45. This
document is what those 45 have in common. It is not a list of the breaks;
those are in each pack's *Refutation record* and *Gate audit* block.

---

## 1. What the kit lacked

### 1.1 It measures a point. The traits quantify over a span.

This is the single largest finding of Phase 2: **28 of the 45 broken clauses
are the same defect** — the row was measured at one setting inside a span its
own disconfirming condition quantifies over, and the measurer chose the
setting after the trait was frozen.

| Class | The row says | The pack measured | It breaks at |
|---|---|---|---|
| `Limiter` L1 | "every probe" | one probe (`worst_phase_fs4`) | `ramp_fs` **+2.22 dB TP**, `dc_step` +1.12 |
| `Expander` E2 | no ratio named | ratio 2 (hardcoded) | ratio 4 → **0.55 dB**, ratio 5 → 1.88 |
| `LowPass` T1/T2/T4/T5 | 20 Hz–20 kHz, Q 0.5–16, both slopes | f₀ 1 kHz, Q 0.707, slope 12 | f₀ 20 Hz Q 16 slope 24 → **−0.444 dB** |
| `HighPass` T2/T6 | "both slopes", "at every rate" | 12 dB/oct, one rate | 24 dB/oct f₀ 10 Hz → **0.600 dB out**; 44.1 kHz Q 16 → **2.682** |
| `BandPass` T2/T4a/T4b | "any Q in 0.5…16", "any f₀ ≤ 2 kHz" | f₀ 1 kHz, Q 0.707 | f₀ 4 kHz Q 0.5 → **−3.803 dB**; Q 8 → +6.435 dB/oct |
| `Notch` T1/T4/T6 | no f₀, no Q | one f₀/Q pair | f₀ 100 Hz → **3.319 dB out**; f₀ 20 Q 32 → −0.724 |
| `CombFilter` T2/T5 | no tuning named | 200 Hz and 1 kHz — whole-sample delays | 1760 Hz g 0.95 → **0.873 dB**; 3520 Hz null **−25.2 dB** |
| `DynamicEQ` T2/T4/T5/T6 | the declared macro spans | attack 2 ms, Q 2, ratio 4 | attack 100 ms → **4.269 dB**; Q 0.5 → 1.015 |
| `DeEsser` D1/D7 | "level-independent", "never exceeded" | Sensitivity 34, one probe | Sensitivity 44 → spread **2.668 dB** |
| `GraphicEQ` T1, `ParametricEQ` T3/T5 | no probe level | one level, 6 dB inside headroom | −10 dBFS → **+2.85 dB** where +8 is claimed |
| `TransientShaper` T1/T3/T4 | no level, no note, no render length | one of each | 3 dB/s note → **−10.8 dB** where −24 is claimed |
| `MultibandCompressor` M3 | "that band's passband" | 1.3 of the mid band's 3.3 octaves | tilt **1.31 dB** where 0.37 was reported |

**The kit gives no way to do better.** Every measurement takes a probe and a
setting the caller names. Nothing in `tools/effect_measurements.py` reads a
class's own macro grid, and nothing walks `tools/effect_probes/`.

**The revision.** The kit gains a sweep driver — one entry point that takes a
measurement, a class, and a *span* expressed in the class's own macro units,
and runs the measurement across that span's grid, reporting the worst cell
rather than a chosen one. Two rules go with it:

- A Tier 2 measurement whose trait quantifies over a span and whose driver
  hardcodes a point is **not a demonstration**. It is a demonstration *at that
  point*, and the point belongs in the verdict.
- Every row whose span includes the class's own macro stops is run **at the
  stops**. `BandPass` T1's −0.486 dB and `LowPass` T1's −0.444 dB are both at
  a macro's end position, one `set_macro` call from a player's fingers.

### 1.2 It has no falsifiability check

Eleven clauses read green on a build that does nothing:

- `ParametricEQ` T2 — all three clauses green on a **byte-flat wire**, because
  `local_maximum_near` marks every interior point of a plateau a maximum
  (`tools/phase2_probes/parametriceq_traits.py:99`).
- `Notch` T6 — green on **its own planted fault**: `measured_centre()`
  bisects inside a bracket around f₀, so when nothing crosses −3 dB it reports
  0 % displacement by construction.
- `HighPass` T3's Nyquist leg — **+0.0000 dB with both poles wired out**.
- `Limiter` L6 — **−0.00000 dB/dB at ratio 1.0**, a build that does no
  compression at all, because the reading is the catch stage's clip.
- `DeEsser` D2's tracking clause — green with **the crossover frozen** at one
  frequency.
- `CombFilter` T1's `taps()` leg — green on the class's own T1/T3 fault at all
  six tunings.
- `GraphicEQ` T4 — cannot fire above band 3; six of ten bands are vacuous and
  two of the four the pack reports are among them.
- `Expander` E2 at ratio ≥ 6 and E4's depth-0 row — the clean run and the
  faulted run are the same number.
- `LadderFilter` T4(a) and `DynamicEQ` T6's out-of-band clause — cited with no
  planted fault at all.

**The revision.** Before a measurement may be cited, the kit runs it against a
**null build** — the class at `mix` 0, or with the trait's own mechanism
removed — and requires a red. This is the workspace's own "prove a checker can
fail" rule, and Phase 2 shows it has to be a kit function rather than a habit:
every one of the eleven was written by a session that believed it had already
applied the rule.

### 1.3 Its fault runner does not check that a fault is unreachable

Three faults in Phase 2 are positions of the class's own surface:

- `CombFilter`'s `NoGlideCombFilter` forces `delay_slew = 0`; macro 5 `Glide`
  spans 0…1 and grid position 0 **is** `delay_slew = 0` (verified this session:
  `e.set_macro(5, 0); e.macro(5)` → `0.0`). The "fault" and the clean class read
  the same **+8.28 dB**.
- `Compressor` F5 and V6 file **Release macro 127** as a planted fault. It is a
  knob a player turns, and at 50 Hz the class reads 3.89 % THD there.
- `Compressor` O1's fault (Memory 0) never reaches the character the row is
  measured on — `compressor.py:331-333` forces `memory = OPTICAL_MEMORY` and
  never reads macro 6 — so it reads identically to the clean run.

**The revision.** The fault runner asserts two things: that the faulted build
is reachable from **no** macro position or patch, and that the clean control
and the faulted run differ. A fault that the surface can reach is a
**disconfirmation waiting to be written down**, not a fault.

### 1.4 The cost runner refuses silence but not a bypass

`tools/measure_effect_cost.py` refuses a render whose digest is the digest of
silence. It does not refuse a render whose digest is the **source's**. The
Phase 2 board run measured all sixteen classes at construction defaults, and
four of them — `GraphicEQ`, `Limiter`, `ParametricEQ`, `TransientShaper` —
handed the probe back unchanged, so their board digests are not a check on the
class's audio at all. The commit says so plainly (`42845a0`), which is right,
but the runner should have refused.

**The revision.** The cost runner takes its settings from the evidence pack's
§4 row — the state the cost is *about* — and refuses a render whose digest
equals the bare source's, exactly as it refuses silence.

---

## 2. What the dossier template got wrong

### 2.1 A trait may be frozen without its axis

Every Tier 2 row in the sixteen dossiers has a "what would disconfirm it"
cell, and most of them name a bar and leave the probe level, the rate, the
corner, the Q, the ratio, the attack, the render length or the tuning free.
The row then reads as universal, is measured at one point, and is refuted the
first time anyone moves the free variable. §1.1 above is the whole cost of
this one omission.

**The revision (landed in `TEMPLATE.md`).** The Tier 2 table gains two
columns — **Held fixed** and **Quantified over** — and a rule: a row with a
blank in either is a trait that is not yet fixed, and Station A does not
close until both are filled. *Quantified over* is written in the class's own
macro units, so the sweep of §1.1 can run it.

### 2.2 There is no verdict for "the demonstration is invalid"

The template offers three: *demonstrated*, *disconfirmed*, *unmeasured*.
Eleven of the 45 broken clauses are none of them — the class may well do the
thing, but nothing that has been run can tell. The packs coped by stretching
`unmeasured`, and `Compressor` had already written the precedent in prose
("ran and produced a number that does not test the claim").

**The revision (landed in `EVIDENCE-TEMPLATE.md`).** `unmeasured` is defined
to cover both cases explicitly — no number was produced, **or** a number was
produced that cannot test the claim — and the second carries the
demonstration of vacuity beside it (the bypass reading, the inert fault, the
grid the figure moves on).

### 2.3 The refutation column and the refutation pass are the same field

The template gives §1 a column headed *"Refutation: argument, and the
answer"*, and the gate item says the trait must survive an **independent**
attempt. Eight of sixteen packs filled the column from the builder's own
session and ticked the gate item on it; four of the eight said so honestly and
left the box unticked. The column is still valuable — `DeEsser` D6 and
`NoiseGate` G2 and G5 were each *changed* by the builder's own pass — but it
is not the gate's evidence.

**The revision (landed in `EVIDENCE-TEMPLATE.md`).** The column stays, renamed
**Self-refutation**, and §1 gains a required, dated **Refutation record**
section, signed by whoever ran it, with the rule that the gate item is read
only from that section and only when its author is not the class's builder.
A `Gate audit` block is added beside it, which is where a ruling on a
refutation lands and where a verdict changes.

### 2.4 The Tier 3 block asks for a budget it cannot source

Twelve of sixteen classes are over their dossier budget on both boards, and
the board run names the reason: *"the budgets were instruction-count
arithmetic and cannot see the per-block Python of a node graph, which is most
of the overrun."* The block also never asks for the settings the figure was
taken at, which is how sixteen cost figures came to be measured at
construction defaults.

**The revision (landed in `TEMPLATE.md`).** Tier 3 carries the **settings the
budget is stated at** and a line naming the budget's derivation; a budget from
instruction counts alone is marked as such, and the first measured graph on a
board replaces it rather than failing against it.

### 2.5 "One commit" contradicts the station structure the same gate mandates

Fifteen of sixteen packs record the same deviation with the same reason: the
dossier freeze has to be provably earlier than the code for the gate's first
item to mean anything, so the code, the evidence and the CHANGELOG cannot land
together. The gate asks for a thing the method forbids.

**The revision (proposed to the roadmap, landed in `EVIDENCE-TEMPLATE.md`'s
checklist).** The item reads: the class's code, its evidence file and its
CHANGELOG line land **on one branch whose commits are named in §0, with the
dossier freeze provably first**. That is what all sixteen actually did.

---

## 3. What the refutation pass caught

**Forty-five clauses, across all sixteen classes. The gate audit upheld every
one of them,** re-running four itself (`Compressor` V3, `Limiter` L1,
`BandPass` T1, `CombFilter` T6's macro floor) and checking every code citation
with `grep -n`. Not one refutation was overturned.

They fall in three kinds, and the third is the one that matters:

| Kind | Count | What it means | Whose problem |
|---|---|---|---|
| **Scope** | 28 | measured at a point in a span the row quantifies over | the *dossier's* — the trait's axis was never written down |
| **Vacuity** | 11 | the reading, or its fault, cannot fail | the *kit's* — §1.2 and §1.3 |
| **Build** | 6 | the class misses its own bar at reachable settings | the **class's** |

The six build breaks are the ones that park a class, and they are worth naming
in full:

1. **`Limiter` L1** — the true-peak ceiling is broken by committed probe
   material: `ramp_fs` reads **+2.22 dB TP** over a −6 dBFS ceiling and
   `dc_step` +1.12 dB. The cause is in the class: the catch stage
   (`limiter.py:174-180`, `DYN_LIMIT`, `attack_ms=0.0`) is a sample-peak
   brickwall running *after* the true-peak detector, and it reinstates the
   inter-sample overshoot the shape stage had just made room for.
2. **`BandPass` T1** — at the two macros' own stops (f₀ 20 Hz, Q 32) the
   settled gain at f₀ is **−0.486 dB** where RBJ's closed form says 0.000. It
   is level-dependent, so it is the recursion's arithmetic, not a coefficient
   error.
3. **`HighPass`'s `tail_samples`** — declared 305 152, measured **403 375** on
   a DC step at the dossier's own worst case. The declaration was taken from a
   burst; a step is the longer excitation.
4. **`DynamicEQ` T2/T4/T5/T6** — the composite law is missed by **1.44 dB at
   patch 3's own shipped settings** and the two-octave isolation bar by
   0.27 dB at patch 5's. Shipped patches, not corners.
5. **`MultibandCompressor` M3** — every band tilts by its own LR4 skirt
   (1.82 / 1.31 / 1.42 dB against a 0.5 bar); only the measurement window hid
   two of the three.
6. **`Compressor` F5 / V6** — clean at Release slowest, 3.89 % THD at Release
   fastest on 50 Hz material. The "planted fault" was a knob position.

**And the finding that would have saved the pass most of its work: read the
patches back off the instance and re-run every row at those settings.**
`DynamicEQ` broke at patches 1, 3 and 5; `BandPass` at the centre patch 3
ships and the width patch 4 ships; `DeEsser` at the Sensitivity its own D7 row
uses; `GraphicEQ` at a probe level its own §6 patch table sits near.
A shipped patch is a setting the class's author chose, published and expects a
player to use — so a trait the class does not meet there is not a corner case,
it is the product. **Station C's first run should be the patch sweep**, before
any chosen operating point, and the evidence pack should carry it as a table:
every trait × every patch, worst cell.

---

## 4. The five changes, as a checklist for Phase 3

- [ ] Kit: a sweep driver that runs a measurement over a span in the class's
      own macro units, reporting the worst cell (§1.1).
- [ ] Kit: a null-build check every Tier 2 measurement must go red on before
      it can be cited, and a fault runner that rejects a fault the macro
      surface can reach (§1.2, §1.3).
- [ ] Kit: `measure_effect_cost.py` takes §4's settings and refuses a
      source-digest render as it refuses silence (§1.4).
- [ ] Dossier: **Held fixed** and **Quantified over** on every Tier 2 row, and
      Tier 3's budget carries its settings and its derivation (§2.1, §2.4).
- [ ] Evidence: Station C opens with the patch sweep — every trait at every
      shipped patch — and the independent refutation record is a signed
      section the gate is read from, never the builder's own column (§2.3, §3).
