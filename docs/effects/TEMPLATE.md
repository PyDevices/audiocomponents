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

### Tier 1 — invariants (the standard block, verbatim from vision §3)

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

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | Held fixed | Quantified over | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|---|---|
| T1 | | | | | | | |
| T2 | | | | | | | |
| T3 | | | | | | | |

**`Held fixed` and `Quantified over` are not optional, and a blank in either
is a trait that is not yet fixed** — Station A does not close until both are
filled. This is Phase 2's largest finding
([`../effects-phase2-pattern-revision.md`](../effects-phase2-pattern-revision.md)
§1.1): 28 of the 45 clauses an independent refutation pass broke across
sixteen classes broke for one reason — the row was quantified over a span
(*"every probe"*, *"any Q in 0.5…16"*, *"at any f₀"*, *"both slopes"*) and was
measured at one point in it, with the point chosen after the trait was frozen.

- **Held fixed** — the settings the trait is *stated at*: probe level and
  material, rate, render length, and every macro the row does not sweep. A
  bar with no level behind it is not a bar; `ParametricEQ` T3 read +7.95 dB at
  −16 dBFS and +0.74 dB at −6 dBFS on the same build.
- **Quantified over** — the span the row claims, **in the class's own macro
  units**, so the kit's sweep can run it. If the span is the macro's full
  travel, say so, and expect the row to be measured **at the stops**:
  `BandPass` T1 and `LowPass` T1 both miss their bar at a macro's end
  position, one `set_macro` call from a player's fingers.
- If the trait is true only over part of a control's travel, that belongs
  here, in advance — not in a verdict written after the measurement.

Characters (where the class carries several standouts) each get their own
rows; a character that fails its traits cannot hide behind one that passes.

**A trait's measurement must be able to fail.** State, per row, the *null
build* the measurement is required to go red on — the class at `mix` 0, the
trait's own mechanism removed, or the section wired out. Eleven of Phase 2's
broken clauses read green on a build that did nothing at all, including one
that read green on its own planted fault.

**A planted fault may not be reachable from the surface.** A "fault" the macro
grid can dial is a disconfirmation waiting to be written down, not a fault:
`CombFilter`'s `NoGlideCombFilter` and macro 5 at grid position 0 are the same
build, and `Compressor` filed a Release knob position as a planted fault twice.

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
<x>, ESP32-S3 <y>. Lean patch expected: yes | no.

**The settings the budget is stated at:** <patch, macros, the state the cost
is about — a compressor actually reducing gain, a drive stage above unity, a
filter with its sections engaged>. **How the budget was derived:**
instruction-count arithmetic | a measured graph on a board | a comparable
class's measured figure. Twelve of Phase 2's sixteen classes overran a budget
derived from instruction counts, for one reason the board run states: that
arithmetic cannot see the per-block Python of a node graph, which is most of
the cost. A budget from instruction counts alone is marked as such here, and
the first measured graph on a board **replaces** it rather than failing
against it.

Latency (vision §9a): algorithmic latency of the dry-to-wet path in samples
and in ms at 48 kHz — zero unless the algorithm must see ahead, and then the
smallest it can be, with the knob that trades CPU for it named. Options that
add latency (lookahead, partition length, pitch window): listed, each
defaulting off or to its shortest. Reported `latency_samples` is verified by
the click measurement at the class gate.

## 4. Modeling approach on the palette

Which audioif nodes, in what topology; what Python computes at construction
and on a macro move; what C runs per sample. Compose the existing palette
first (vision §6). Tables and coefficient sets are computed on CPython and
shipped as data, never rebuilt on a board (the ESP32 ports are
single-precision). State the portability tier (roadmap §3: **stock** or
**audioif**) and what a mono source gets.

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
