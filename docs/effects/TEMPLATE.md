# Effects Dossier — `<Class>` (<standout>)

**Class:** `lib/audioeffects/<module>.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** <family>, roadmap Phase <n>
**Standout:** <the circuit>, per vision §4.2 — confirmed here, or swapped
with the evidence in §2.
**Grade:** circuit | literature | proxy | design
**Portability tier:** stock CircuitPython | needs audioif-own nodes (<which>)
**Status:** seed (Phase 0) | Station A complete | rebuilt | through the gate

## 1. The circuit, in one paragraph

Topology in words: where the nonlinearity sits, what filters surround it,
what the control law is, what shape the LFO has, what the panel controls
actually move. This paragraph is what the rebuild follows. It is not a
component-value clone.

## 2. Sources and license calls

Every source reached during the run, none from memory.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| | | | | |

Copyleft sources are measured or read as papers, never read for code
structure (vision §5).

## 3. Traits — fixed before measurement

Recorded at the moment the set is fixed; a trait dropped later carries a
written reason.

### Tier 1 — invariants (the standard block)

- [ ] Silence in gives silence out; a decaying tail reaches exact zero.
- [ ] Mix at zero, or drive at zero, is a wire (byte-identical to source).
- [ ] Level-honest: unity through the dry path.
- [ ] Reported `latency_samples` / `tail_samples` match what is measured.
- [ ] Pulling `output` allocates nothing.
- [ ] CPython and MicroPython render identical bytes, or the cause is here.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | | | | | |
| T2 | | | | | |
| T3 | | | | | |

Characters (where the class carries several standouts) each get their own
rows; a character that fails its traits cannot hide behind one that passes.

### Tier 3 — cost

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
<x>, ESP32-S3 <y>. Lean patch expected: yes | no.

## 4. Modeling approach on the palette

Which audioif nodes, in what topology; what Python computes at construction
and on a macro move; what C runs per sample. Compose the existing palette
first (vision §6).

## 5. Node asks

For each: the trait id it unblocks; what the palette does instead and the
measurement showing it cannot reach the trait; the refutation record from
Phase 0.

## 6. Proposed surface

Macros (at most sixteen), each with its mode, its engineering range, and the
panel control it generalizes; characters; patches with names.

## 7. Defects in the current class the rebuild must not repeat

From one read of the old code. Nothing else about it is carried forward.

## 8. Open questions

What the run could not settle, and who settles it (Phase 0, the
implementation session, or Brad — the last only for a contract wall).
