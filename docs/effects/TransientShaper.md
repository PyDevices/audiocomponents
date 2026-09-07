# Effects Dossier — `TransientShaper` (SPL Transient Designer)

**Class:** `lib/audioeffects/rebuilt/transientshaper.py` (rebuild);
`lib/audioeffects/dynamics.py:202` is the old class, read once, for §7.
**Family / phase:** Dynamics, roadmap Phase 2 · **Grade:** literature
**Standout:** SPL Transient Designer *(vision §4.2)* — **confirmed**, no
swap argued. SPL's manual for the RackPack module 2715 (S1) names the
mechanism Differential Envelope Technology, describes it, gives both control
ranges and prints the four envelope diagrams the design turns on; an
independent review (S2) calls the box "a new type of dynamic control" that
"could not fairly be described as either" a compressor or an expander. No
schematic and no component values were reached (§2). *(What "originator"
rests on, and the audit's attribution corrections: **App. A1**.)*
**Portability tier:** **audioif**, `REQUIRES = ("audiodynamics",)` —
audioif's own module, not a CircuitPython port (`upstream-diff.md:661`).
**Latency budget:** **0 samples, 0.00 ms** at every setting and every rate.
**Tier 3 budget:** ESP32-P4 **5 %** of one stereo block's real-time
deadline, ESP32-S3 **10 %**. Lean patch expected: **no.**
**Status:** seed written 2026-09-06 (Phase 0); **traits frozen and §8's
three opens settled at Station A, 2026-09-07**, before any line of the
rebuild.

## 1. The circuit, in one paragraph

Two independent envelope pairs drive one THAT 2181 VCA, and there is no
threshold anywhere in the box. In the **ATTACK** circuitry one generator
follows the waveform (Env 1) and a second follows it "with a slower attack"
(Env 2); "from the difference of both envelopes the VCA control voltage is
derived", positive settings raising the shaded difference and negative
reducing it (S1, Diagrams 1–3). The **SUSTAIN** circuitry runs the same
trick the other way: Env 3 follows the waveform while "Env 4 maintains the
level of the sustain on the peak-level over a longer period of time", and
the control voltage is again the difference (Diagrams 4–6). The two
"operate simultaneously and don't affect each other". Both control voltages
being *differences of envelopes of the same signal*, absolute level cancels
— DET "makes any threshold settings unnecessary" — so the panel carries only
**Attack ±15 dB**, **Sustain ±24 dB** and, on this module, an **Output Gain
−22 … +6 dB**. S2 from outside: "no meters, no threshold controls, no ratio
knobs and no make-up gain controls". *(Full quotations, the VCA-count
attribution and the corrections: **App. A1**, **App. S**.)*

## 2. Sources and license calls

All fetched 2026-09-06; nothing from memory. What each gave and how its
licence reads, in full: **App. S**.

| Source | Lead | Licence | URL | Reached |
|---|---|---|---|---|
| **S1** SPL, *Manual — Transient Designer … Model 2715*, v1.2, 5/2011 | DET, both circuitries, Diagrams 1–6, the three control ranges | all rights reserved; read only, short quotation only | <https://spl.audio/wp-content/uploads/RackPack_2715_TD_BA_E.pdf> | yes — PDF, `pypdf` |
| **S2** Paul White, "SPL Transient Designer", *Sound On Sound*, Oct 1998 | independent corroboration of the mechanism and both ranges | all rights reserved; read only | <https://www.soundonsound.com/reviews/spl-transient-designer> | yes — HTML, not paywalled |
| **Local** `audioif/src/shared/audioif_dynamics.c`, `audioif/docs/upstream-diff.md` | what the palette's transient mode actually does | MIT (audioif) | — | yes |

*Two licence-and-citation passes ran on 2026-09-06; both calls stand and
every S1/S2 quotation was verified verbatim (**App. R**).*

## 3. Traits — frozen 2026-09-07, before the rebuild

### Tier 1 — invariants

The standard block, verbatim from vision §3, is in **App. I** with this
class's notes beside it: **mono** gets one channel-linked gain, which is
SPL's Link switch and this class's default; **rate** — no trait below
carries a frequency, so T1–T6 stand unchanged at 44.1 and 22.05 kHz;
**`capabilities` = `()`**, reason in §6.

### Tier 2 — circuit traits

The statements are the gate. Source reading, confidence reasoning and the
"this figure is the dossier's own" notes are in **App. T** per row; the kit
material each id names is in **App. R**, from §3.

| # | Trait (falsifiable as stated) | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|
| T1 | **Level-independent, thresholdless.** One recorded hit at −6, −20, −40 and −60 dBFS gives gain traces agreeing within 0.5 dB at every point, aligned on the onset. The −80 dBFS render is taken and **recorded, not held to the bound** — there a 16-bit hit is a few LSBs and the trace is quantisation-limited | high | a gain trace that changes with input level; any level at which the processing stops | LEVELS |
| T2 | **Attack and Sustain are two circuits acting at once.** With Attack +12 dB and Sustain −12 dB set together, one hit shows positive gain during its transient **and** negative gain during its decay, each within 0.5 dB of what that setting produces alone | high | one control's setting moving the other's measured effect by more than 0.5 dB; or a trace that can only ever have one sign | BOTH |
| T3 | **Attack spans ±15 dB and Sustain ±24 dB**, and the measured peak gain tracks the setting within 1 dB across both spans | high | a control that saturates before its stated end, or overshoots it | RANGE |
| T4 | **The sustain envelope is a peak-hold, not a slow follower.** On an exponentially decaying note the sustain gain **grows monotonically** — no sample more than 0.25 dB below the trace's running maximum — through at least the first 200 ms after the onset; and its shape follows the note's own decay, so the time to reach 90 % of its peak differs by at least 2:1 between a note decaying at 10 dB/s and one at 40 dB/s | medium | a sustain gain that peaks early and falls back, or one whose shape is the same for a fast and a slow decay | DECAY |
| T5 | **Attack acts only on the transient.** With Attack at +12 dB the peak gain in the first 5 ms of a burst is +12 dB within 1 dB, the gain in the steady section 100 ms later is 0 dB within 0.5 dB, and the ratio between them is at least 10 dB | high | a steady section more than 0.5 dB off unity at any Attack setting; a transient peak more than 1 dB from the setting; a ratio under 10 dB | SPLIT |
| T6 | **Time constants adapt to the material:** two hits whose own 10–90 % onset times differ by 4:1 give gain traces whose 10–90 % rise times differ by at least 5:1 — more than the hits' own difference, which is what a fixed coefficient cannot give | **low** | rise times differing by 4:1 or less, i.e. tracking the hits' own difference and no more; identical rise times on both hits | ONSET |

### Tier 3 — cost and latency

P4 **5 %** of one stereo block's real-time deadline, S3 **10 %**. Lean patch
expected: **no** — one `Dynamics` node: four one-pole followers, a
peak-hold, an RMS one-pole and one multiply per frame. **Latency: zero, and
no option adds any.** A differential envelope cannot look ahead — the
difference is between two envelopes of the *same past* — so
`latency_samples` is 0 at every setting, the class ships **no look-ahead
option**, and the docstring says 0.00 ms; vision §9a's live pedalboard gets
one of its cheapest members. **`tail_samples` is 0**: a VCA multiplies, so
silence in is exactly zero out in the same frame.

## 4. Modeling approach on the palette

**One node, no composition.** `audiodynamics.Dynamics(DYN_TRANSIENT)` is a
differential envelope shaper already, and it takes its difference **in
decibels** (`audioif/src/shared/audioif_dynamics.c:628-676`), which is what
cancels absolute level: **T1 is met by the node's own arithmetic** —
+12.000 dB of attack gain at every level from −6 to −72 dBFS (A9, V-T1).
**Phase 1 delivered both node asks** (`upstream-diff.md:969-1097`):
`transient_dual=True` applies a second pair's difference *at the same time*
as the first (`:637-672`) — N-TRAN-1, unblocking T2 — and `slow_hold_ms`
makes that pair's slow envelope a peak-hold (`:645-657`) — N-TRAN-2,
unblocking T4. `transient_fast_attack_ms` and its three siblings, the
attack-pair constants that were literals, are what Attack Speed moves.

**Two further node settings this class fixes, neither in the seed, both
measured at Station A (runs in App. A2):** `sustain_fast_attack_ms=0.0`,
because the peak-hold rises instantaneously (`:646-649`) and a 1 ms fast
envelope beside it fires the sustain setting **on the transient** — T4's
monotone clause red by **11.832 dB** against **0.008 dB** at zero, and the
attack peak paying for it when Sustain is set too (**+11.484** against
**+11.998 dB**); and `detector="rms", rms_ms=3.0`, because
peak-detected the two attack envelopes never converge on a periodic signal
and leave a steady tone under a standing gain — T5's own disconfirmer:
+2.187 dB against +0.211 dB, transient peak +12.000 dB either way.

Python sets five node options at construction and up to four on a macro
move; C runs the followers, the hold, the two differences and the VCA per
sample. No table is computed on a board. Guarded import, construction-time
`ImportError` on a stock board. *(Why the seed's two-node series
composition was not used — 10.36 dB of interaction — **App. R**, from §4.)*

## 5. Node asks — both **delivered** in Phase 1

- **N-TRAN-1**, two independent gains from one node (T2) — delivered as
  `transient_dual`. Station A: **43 of 203 hops** carry an attack boost and
  a sustain cut at the same instant where the single pair carries **0**, and
  each section's effect moves by at most **0.092 dB** between running alone
  and running in company, where T2 allows 0.5 (§8 Q1).
- **N-TRAN-2**, a peak-hold sustain envelope (T4) — delivered as
  `slow_hold_ms`, on the sustain pair whenever `transient_dual` gives
  sustain its own (`:645`). Station A adds the companion the ask did not
  foresee, `sustain_fast_attack_ms=0.0` (§4).
- **Not asked for:** adaptive time constants (T6). No source gives a
  mechanism or a number, so a node option would be our invention wearing the
  standout's name. §8 Q2 says what the class does instead.

*(Full need statements and refutation records: **App. R**, from §5.)*

## 6. Surface — settled at Station A

**Five macros.** The box has three controls; two more expose behaviours S1
describes but does not knob, under vision D2. `Mix` is **dropped** (§8 Q3).
**Characters:** none.

| # | Macro | Mode | Range | Node option | Generalizes |
|---|---|---|---|---|---|
| 0 | Attack | BIPOLAR | −15 … +15 dB | `attack_gain_db` | SPL Attack |
| 1 | Sustain | BIPOLAR | −24 … +24 dB | `sustain_gain_db` | SPL Sustain |
| 2 | Output | BIPOLAR | −22 … +6 dB | `makeup_db` | SPL Output Gain (module 2715) |
| 3 | Attack Speed | UNIPOLAR | 0.2 … 5 ×, log | the attack pair's four `transient_*_ms` | the attack time constants S1 leaves internal |
| 4 | Sustain Hold | UNIPOLAR | 0 … 500 ms | `slow_hold_ms` | Env 4's "longer period of time" |

Attack Speed divides all four attack-pair constants by its factor: 5 × is
five times faster, 1 × is the node's own 1 / 50 / 25 / 300 ms. At 0 ms
Sustain Hold is a plain follower again — T4's planted fault, reachable from
the panel.

**Patches**, seven, contiguous from 0: **0 Flat** (the defaults on the
grid), **1 Snap** (attack up, sustain flat — the box's headline move),
**2 Room Off** (sustain down), **3 Room On** (sustain up), **4 Soften
Pick** (attack down), **5 Kick Punch** (attack up, sustain slightly down),
**6 Ambient Swell** (attack well down, sustain up).

**`capabilities` = `()`** (vision D10): the Transient Designer has no tempo
input, and the class never reads `self._transport()`.

**Patch 0 is the defaults quantized, not an exact wire** — a bipolar span's
zero does not land on the 7-bit grid. A fresh instance built from the
constructor's defaults *is* an exact wire, and that is the state WIRE is
measured in (**App. A2**).

## 7. Defects in the current class the rebuild must not repeat

- **No surface; the two controls are frozen at construction** —
  `MACRO_LABELS = ()` (`dynamics.py:210`), `PATCHES = {0: ("Default", ())}`
  (`:212`), `attack_db`/`sustain_db` passed once (`:214-217`). → five
  macros, seven patches, all live.
- **The docstring promises what the node cannot do** (`:203-204`): two
  independent actions where the node applies one at a time (A10). →
  `transient_dual=True`, and the docstring says what was measured.
- **No output gain**, so the class changes level with every setting; SPL's
  module added that control for that reason (S1). → macro 2.
- **The 6 dB normalisation is invisible** — `norm = diff / 6.0f` clamped to
  ±1 (`:630-636`), so every transient sharper than 6 dB gets the full
  setting and no more. → named in the class docstring; it is also the
  mechanism that disconfirms T6.

## 8. Open questions — all three settled at Station A

1. **Does the series pair meet T2? — moot, and the discriminator is not the
   one Station A first reached for.** The seed measured **10.36 dB** of
   interaction between two `DYN_TRANSIENT` nodes in series (V-T3) where T2
   allows 0.5, and filed N-TRAN-1; Phase 1 delivered it, so no series
   composition is built and the class is one node. Station A measured the
   delivered option on `hit_levels_-6` at 48 kHz, hop 1 ms, Attack +12 with
   Sustain −12: **43 of 203 hops** carry both at once, and each section's
   effect moves by at most **0.092 dB** between alone and in company.
   **The superposition figure on its own proves nothing**, and Station A had
   to be shown that: `transient_dual=False` decomposes at **0.000 dB** —
   perfectly — because a gain computer that *selects* one section by the
   sign of one difference is trivially additive. Its hop count is **0 of
   203**, and that is T2's planted fault.
2. **T6's fate — expect a disconfirmation, keep macro 3 as the manual
   stand-in.** Coefficients are computed once per block from config fields
   (`:417-436`), nothing varies them with the material, and the 6 dB clamp
   takes the gain to full value a sample or two after any onset. Measured at
   hop 0.05 ms: gain-trace 10–90 % rise times of **0.042, 0.042 and
   0.041 ms** for material rises of 0.40, 1.60 and 6.40 ms — a ratio of
   **1.02:1** where T6 asks 5:1, and the material's own 16:1 spread leaving
   no trace at all. Station C runs ONSET through the class and records the
   disconfirmation with its cause; the class ships fixed constants, says so
   in its docstring, and keeps **Attack Speed** so a player can do by hand
   what the box claims to do by itself.
3. **Whether `Mix` belongs here — dropped.** The class is a single
   time-varying gain, so a parallel blend is not a second signal path: it is
   `(m·g + 1 − m)·x`, a re-mapping of the same gain law driven by the same
   envelope difference. It would cost a Splitter, a Mixer, their per-frame
   cost against a 5 %/10 % budget and the byte-exact wire — for a curve
   Attack and Sustain already reach in kind. Neither source has such a
   control. Five macros, not six.

## Appendix

Probes ran 2026-09-06 against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit.

**A9 — level independence, already met by the palette.** An exponentially
decaying 220 Hz note, `DYN_TRANSIENT` with `attack_gain_db=12`,
`sustain_gain_db=0`, rendered at −3, −20, −40, −60 and −72 dBFS: peak attack
gain **+12.00 dB at every level**. A second run with a smaller step and levels
down to −85 dBFS: **+12.000 dB at every level**. The dB-domain difference is
what buys this, and it is the standout's headline claim satisfied without a
node ask.

**A10 — attack and sustain are mutually exclusive on the palette.** The same
decaying note with `attack_gain_db=12` and `sustain_gain_db=-12`. Reported
gain per 256-frame block, first twenty: `+12.0 +12.0 +12.0 +12.0 +12.0 +11.5
+10.1 +8.9 +7.9 +6.9 +6.0 +4.9 +4.0 +3.0 +1.9 +0.9 −0.2 −1.3 −2.3 −3.4`,
reaching −12.0 later in the render. One signed value, one control at a time.
This is the **planted fault for T2**: the measurement is already red on
today's node.

**A11 — the series composition, which partly works.** Two `DYN_TRANSIENT`
nodes, A with `attack_gain_db=12, sustain_gain_db=0` feeding B with
`attack_gain_db=0, sustain_gain_db=-12`, on the same note. Over 60 blocks, A's
gain ran `+12.0 +12.0 +12.0 +12.0 +12.0 +10.7 +9.1 +7.8 +6.6 +5.7 …` while B
reached its cut later, and **2 blocks had A boosting and B cutting at the same
time**. So both gains can coexist on the existing palette; what is not yet
measured is whether B's detectors, reading A's output, shift either setting's
effect beyond T2's 0.5 dB allowance.

---

### Palette verification, 2026-09-06

Independent run against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit. Material: a 180 Hz tone with
a 300 ms exponential decay, rendered at each level.

**V-T1 — T1 is met by the node, and the node's own arithmetic says why.**
`DYN_TRANSIENT` with `attack_gain_db=12`, peak reported gain over 80 blocks:

| input | −6 | −20 | −40 | −60 | −72 | −85 dBFS |
|---|---|---|---|---|---|---|
| peak attack gain | +12.000 | +12.000 | +12.000 | +12.000 | +12.000 | +12.000 dB |

The difference is taken between two envelopes *in decibels* (`:290-292`), so
absolute level cancels exactly. A9 reproduced, and extended two levels lower.

**V-T2 — one node cannot hold both signs; two in series can.** With
`attack_gain_db=12` and `sustain_gain_db=−12` on one node, the reported gain
runs +12.0 → 0 → −12.0 across the render and never carries both: `gain_db` is
one scalar chosen by the sign of one normalised difference (`:299-300`). Two
nodes in series (attack-only, then sustain-only) had **9 of 60 blocks** with
the upstream boosting while the downstream cut.

**V-T3 — and the series pair's interaction is 10.36 dB.** The same sustain-only
node (`sustain_gain_db=−12`) reading the same hit, traced per block, once alone
and once downstream of the attack-only node. The two traces diverge to a
maximum of **10.36 dB**; T2 allows 0.5 dB between a control's effect alone and
in company. This is the measurement the first draft made N-TRAN-1 conditional
on, and it discharges the condition against the composition.

**V-T4 — `slow_env` is not a peak-hold.** A 2400-frame decaying hit then
silence, `sustain_gain_db=−12`: the reported gain sits at 0.00 dB for 14 blocks
and then walks down −0.59, −2.13, −3.68, −5.22, −6.76, −8.31, −9.85, −11.40 to
−12.00, where it pins. A peak-hold sustain envelope would keep the differential
near zero while the note decayed; a 300 ms one-pole falls away from the peak
and the differential opens up, which is what this trace shows. T4 unreachable
on the node as it stands.

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

**Mono:** one gain from a channel-linked detector applied to every channel, so
a mono source gets identical processing. SPL's Link switch (S1) is the stereo
case and is what this class does by default. **Rate:** no trait below carries
a frequency, so all of T1–T6 hold unchanged at 44.1 and 22.05 kHz; the only
rate sensitivity is that the envelope coefficients are computed from the
running rate rather than baked (Tier 1). **`capabilities` (D10): `()`** — the
Transient Designer has no tempo input and the class reads no transport.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** SPL electronics, *Manual — Transient Designer, Dynamic Envelope Processor, RackPack Module Model 2715*, v1.2, 5/2011, 26 pp. | The DET description, both control circuitries verbatim, Diagrams 1–6, Attack ±15 dB, Sustain ±24 dB, Output Gain −22/+6 dB, "operate simultaneously and don't affect each other", the adaptive-time-constant claim, the THAT 2181 VCA, the audio specification table (10 Hz–70 kHz, THD+N 0.019 %, dynamic range 111.0 dB) | "This document is the property of SPL and may not be copied or reproduced in any manner, in part or fully, without prior authorization by SPL.", and on the same page "© 2011 SPL electronics GmbH. All rights reserved." (the second line added by the audit run) — **verified all rights reserved; read only, nothing reproduced beyond short quotation** | <https://spl.audio/wp-content/uploads/RackPack_2715_TD_BA_E.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Paul White, "SPL Transient Designer", *Sound On Sound*, October 1998 — a review of the **four-channel** unit ("you get four full channels of processing"), not S1's RackPack module; the mechanism described is the same | Independent corroboration: "one generator follows accurately the original signal amplitude while the second does the same thing but with a slower attack. Subtracting these envelopes produces a control signal"; "the process is independent of input level"; "no meters, no threshold controls, no ratio knobs and no make-up gain controls"; attack "cut or boosted by up to 15dB", sustain "increased or decreased by up to 24dB"; "dynamic attack/sustain time constants respond to the dynamics of the input signal" | "All contents copyright © SOS Publications Group and/or its licensors, 1985-2026. All rights reserved." — **verified all-rights-reserved**. Read only | <https://www.soundonsound.com/reviews/spl-transient-designer> | yes — HTML, full article, not paywalled |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **Level-independent, thresholdless.** One recorded hit rendered at −6, −20, −40 and −60 dBFS produces gain traces that agree within 0.5 dB at every point of the trace, aligned on the hit's onset. The kit's −80 dBFS render is taken too and **recorded, not held to the bound**: at −80 dBFS a 16-bit hit is a handful of LSBs and the trace is quantisation-limited, so a deviation there is the probe's, not the class's | S1 ("level-independent envelope processing … makes any threshold settings unnecessary … pianissimo to fortissimo are treated the same way"); S2 | high — stated by the manufacturer and corroborated independently | A gain trace that changes with input level; any level at which the processing stops | LEVELS |
| T2 | **Attack and Sustain are two circuits acting at once.** With Attack +12 dB and Sustain −12 dB set together, a single hit shows positive gain during its transient **and** negative gain during its decay, and each within 0.5 dB of what the same setting produces alone | S1 ("Both ATTACK and SUSTAIN control circuitries operate simultaneously and don't affect each other") | high — stated as a design property, twice | One control's setting changing the other's measured effect by more than 0.5 dB; or a gain trace that can only ever have one sign | BOTH |
| T3 | **Attack spans ±15 dB and Sustain ±24 dB**, and the measured peak gain tracks the setting within 1 dB across both spans | S1 (panel scales and text); S2 | high | A control that saturates before its stated end, or overshoots it | RANGE |
| T4 | **The sustain envelope is a peak-hold, not a slow follower.** Env 4 "maintains the level of the sustain on the peak-level over a longer period of time", so on an exponentially decaying note the sustain gain **grows monotonically** — no sample more than 0.25 dB below the trace's running maximum — through at least the first 200 ms after the onset; and the trace's shape follows the note's own decay rate, so the time to reach 90 % of its peak differs by at least 2:1 between a note decaying at 10 dB/s and one at 40 dB/s. *(The 0.25 dB, 200 ms and 2:1 figures are the dossier's own criteria — S1 gives no time constant — chosen so the row can fail; a slow one-pole follower fails the first clause outright, as §4 records.)* | S1 (Sustain Control Circuitry, Diagram 4) | medium — the sentence is unambiguous; of Diagram 4 only the caption and the curve labels ("Env 3", "Env 4 (Prolongued Sustain)", "Original Waveform") survive text extraction, the plotted curves being an image; no time constant is given | A sustain gain that peaks early and falls back, or one whose shape is the same for a fast and a slow decay | DECAY |
| T5 | **Attack acts only on the transient.** With Attack at +12 dB, the peak gain in the first 5 ms of a burst is +12 dB within 1 dB, and the gain in the steady section 100 ms later is 0 dB within 0.5 dB — the ratio between the two is at least 10 dB | S1 (Diagrams 2 and 3: the shaded difference exists only where the two attack envelopes diverge) | high | A steady section more than 0.5 dB off unity at any Attack setting; a transient peak gain more than 1 dB from the setting; a transient-to-steady ratio under 10 dB | SPLIT |
| T6 | Time constants adapt to the material: two hits whose own 10–90 % onset times differ by 4:1 produce gain traces whose 10–90 % rise times differ by at least 5:1 — more than the hits' own difference, which is what a fixed coefficient cannot give. *(The 4:1 and 5:1 figures are the dossier's own criteria; neither source gives a number, which is why the confidence is low.)* | S1 ("automated and optimized adaptively in a musical manner according to the characteristics of the input signal"); S2 | **low** — asserted by the manufacturer, no mechanism and no numbers in either source | Gain-trace rise times that differ by 4:1 or less, i.e. tracking the hits' own difference and no more — what fixed coefficients give; identical rise times on both hits | ONSET |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

*Licence and citation audit, 2026-09-06 — **two passes**. Second pass (unit
`gate-deesser-transient-multiband`): every URL above re-fetched from this
machine with `curl` (all HTTP 200), every PDF re-extracted with `pypdf` and
every quotation re-read against the document's own text, every licence line
read on the page that carries it, and every "not reached" claim re-tested.
Corrections are marked inline.*

*(from §2)*

No copyleft source was reached, so none was measured; no emulator was opened.
**Looked for and not found:** the **DET patent** — searched by inventor and by
mechanism, and no patent document was reached; nothing in this seed rests on
one. A **schematic** — SPL publishes a block diagram page in S1 whose figure
did not survive text extraction, and no service manual was found.
**Unsourced, therefore absent from the trait table:** every time constant. S1
says the times are "automated and optimized adaptively" and gives no numbers,
S2 repeats the claim ("the dynamic attack/sustain time constants respond to the
dynamics of the input signal") and gives no figure either — the article contains
no time constant anywhere, checked in the audit run. *Corrected by the audit:
the first draft put "provides no specific measurements" in quotation marks; that
phrase is not in the article and the quotation is withdrawn.* So no
millisecond figure for Env 1–4 appears anywhere below, and T6 is stated at low
confidence as the claim it is.

*(from §3)*

Kit: **LEVELS** = one recorded hit rendered at −6, −20, −40, −60 and −80 dBFS,
gain trace per block (the −80 dBFS render is recorded, not held to T1's bound —
see the row); **BOTH** = a hit with a clear attack and a long decay, Attack at
+12 and Sustain at −12 simultaneously, gain trace at sample resolution;
**DECAY** = two exponentially decaying notes, one at 10 dB/s and one at
40 dB/s, sustain gain trace against time; **SPLIT** = a burst with a flat
steady section, the gain in the first 5 ms against the gain 100 ms later;
**RANGE** = the measured peak gain against the setting, across each control's
full span; **ONSET** = two hits of equal peak whose own 10–90 % onset times
differ by 4:1, gain trace at sample resolution (added by the critic pass for
T6, which the first draft pointed at DECAY + SPLIT — neither of which varies
the onset rate).

*(from §3)*

*Trait ids were **S1–S6** in the first draft and collided with §2's source ids;
the critic pass of 2026-09-06 renumbered them **T1–T6** and updated every
reference in §3–§8. A bare `S1`/`S2` anywhere in this file is now always a
source; `T1`…`T6` are always traits.*
(Audit note — collision found, not renumbered, because §5–§8 already reference
the trait ids.)*

*(from §3)*

No characters. T6 is deliberately kept in the set at low confidence rather
than dropped: it is the one claim in the sources that the rebuild might
legitimately disconfirm, and vision §3 says a disconfirmed trait is a result,
not a failure. If it is disconfirmed the class ships with fixed constants and
the evidence pack records why.

*(from §3)*

**Latency: zero, and no option adds any.** DET is four envelope followers and
a VCA; nothing in S1 or S2 looks ahead, and a differential envelope cannot —
the difference is between two envelopes of the *same* past. `latency_samples`
is 0 at every setting and the class ships **no look-ahead option**. That makes
this class one of the cheapest members of a live pedalboard chain under vision
§9a, and the docstring says so in milliseconds (0.00 ms at every rate).
Measured, `DYN_TRANSIENT` with look-ahead off returns an impulse in the frame
it arrived (`Expander.md` A5).

*(from §4)*

**T2 is the one the node fails, and the failure is structural.** One
difference of one sign selects one control, so attack boost and sustain cut
can never coexist: measured on a decaying note with Attack +12 and Sustain
−12, the reported gain marched monotonically from +12.0 through zero to −12.0
across the render, never both (A10). SPL's two circuits are independent; this
is one circuit with a switch.

*(from §4)*

**The composition that nearly works — measured, and it does not.**
Two `DYN_TRANSIENT` nodes in series — the first with `sustain_gain_db=0`, the
second with `attack_gain_db=0` — do produce both gains at once: measured, 2 of
60 blocks in the first draft's run and 9 of 60 in the palette verification's
(A11, V-T2). But T2's second half fails, and the palette verification of
2026-09-06 put a number on it that the first draft left for the rebuild:
the downstream node's detectors see the upstream node's *output*, and the same
sustain node reading the same hit reports gains that differ by up to
**10.36 dB** between running alone and running behind the attack node — twenty
times T2's 0.5 dB allowance (V-T3). The interaction is not a tuning matter; it
is the second detector hearing a boosted transient. T4 is unreachable either
way: `slow_env` is a one-pole with a 300 ms release (`:221`), not a peak-hold,
so its trace falls away from the peak instead of holding at it (V-T4).

*(from §4)*

**Portability tier: audioif** — `audiodynamics` is audioif's own module, not a
CircuitPython port (`upstream-diff.md:661`); guarded import, construction-time
`ImportError` on a stock board. Python sets **two** values on this node —
`attack_gain_db` and `sustain_gain_db` — at construction and on a macro move;
the four follower coefficients are compiled-in literals recomputed inside the
process loop (`audioif_dynamics.c:215-222`) and no keyword reaches them, which
is why T4 and T6 are node questions rather than surface ones. *(Corrected by
the palette verification, 2026-09-06: the first draft said Python sets four
coefficients.)* C runs the followers, the difference and the VCA per sample.
No table is computed on a board.

*(from §5)*

- **N-TRAN-1 — two independent gains from one node (unblocks T2).** A second
  envelope pair, so `attack_gain_db` and `sustain_gain_db` are applied
  together from two differences rather than selected by the sign of one.
  Palette: one shared difference (`:290-300`), measured never to produce both
  signs at once (A10, V-T1) — `gain_db` is one scalar selected by the sign of
  one normalised difference (`:299-300`), so both signs at once is impossible
  by construction, not by tuning. **Refutation attempted; it half succeeded in
  the first draft and the condition is now discharged.** Two nodes in series do
  produce both gains (A11, V-T2), which is why the first draft filed the ask
  *conditionally* — on the series pair's interaction staying inside T2's 0.5 dB
  allowance. The palette verification of 2026-09-06 measured that interaction:
  the same sustain node reading the same hit reports gains up to **10.36 dB**
  apart alone versus behind the attack node (V-T3). The condition is met by a
  factor of twenty, so **the ask stands unconditionally** and the Phase 1 issue
  carries V-T3 as its evidence.

*(from §5)*

- **N-TRAN-2 — a peak-hold sustain envelope (unblocks T4).** An option making
  the slow envelope hold at its peak for a settable time before releasing,
  default off (today's one-pole). Palette: `slow_env` is a plain one-pole
  (`:288-289`, `:221`), and its time constants are compiled in, not settable —
  `fast_att`/`fast_rel`/`slow_att`/`slow_rel` are recomputed from the literals
  1, 50, 25 and 300 ms on every call (`:215-222`), so no keyword reaches them
  at all. *Refutation:* a hold cannot be composed from a one-pole at any
  coefficient — a follower that holds and one that decays are different shapes,
  not different tunings — and there is no coefficient to re-set from Python in
  the first place, nor a per-block hook to do it from
  (`docs/audio-component-api.md:231-233`). Ask stands, independent of
  N-TRAN-1.

*(from §5)*

- **Not asked for:** adaptive time constants (T6). No source gives a mechanism
  or a number, so a node option would be our invention wearing the standout's
  name. If T6 is disconfirmed at Station C the class ships fixed constants and
  says so; if the implementation session finds a source, the ask is made then.

### App. A2 — Station A's own runs, 2026-09-07

Every figure §§4, 5, 6 and 8 state comes from one run of
`tools/phase2_probes/transientshaper_station_a.py`, which drives
`audiodynamics.Dynamics(DYN_TRANSIENT)` directly — at Station A the class
does not exist yet — and reads the gain through the measurement kit's
GAINTRACE (`tools/effect_measurements.py:1182`) over an in-process render,
so the readout is the one Station C uses rather than a second implementation
of it. CPython, `audiocomponents/.venv/bin/python`, audioif at the pin.

```
$ audiocomponents/.venv/bin/python tools/phase2_probes/transientshaper_station_a.py
Station A probes -- TransientShaper, 48000 Hz, stereo, 16-bit
audiodynamics.Dynamics(DYN_TRANSIENT) driven directly; gain trace = kit GAINTRACE over an in-process render

Q1 -- are the two sections two circuits, or one switch? (dossier section 8 Q1, section 5 N-TRAN-1, T2)
  transient_dual=True  hops with attack boost AND sustain cut at once:  43 of 203
                       each section's effect, alone vs in company: max 0.092 dB (T2 allows 0.500)
  transient_dual=False hops with attack boost AND sustain cut at once:   0 of 203
                       each section's effect, alone vs in company: max 0.000 dB (T2 allows 0.500)
  the superposition figure alone cannot tell the two apart -- a gain computer that
  SELECTS one section by the sign of one difference decomposes exactly too. The
  hop count is the discriminator, and 0 of them is T2's planted fault.

section 4 -- sustain_fast_attack_ms beside an instantaneous peak-hold
  sustain_fast_attack_ms=1.0: T4 monotone drop over 0-200 ms  11.832 dB; attack peak with Sustain -12 also set +11.484 dB
  sustain_fast_attack_ms=0.0: T4 monotone drop over 0-200 ms   0.008 dB; attack peak with Sustain -12 also set +11.998 dB

section 4 -- the detector, on a 1 kHz burst at Attack +12 (T5's steady clause)
  detector peak     peak over 0-5 ms +12.000 dB; steady at 150 ms  +2.187 dB
  detector rms 3 ms peak over 0-5 ms +12.000 dB; steady at 150 ms  +0.211 dB

Q2 -- do the time constants follow the material? (dossier section 8 Q2, T6)
  material 10-90%  0.40 ms -> gain-trace 10-90%  0.042 ms (peak +12.000 dB)
  material 10-90%  1.60 ms -> gain-trace 10-90%  0.042 ms (peak +12.000 dB)
  material 10-90%  6.40 ms -> gain-trace 10-90%  0.041 ms (peak +12.000 dB)

section 6 -- what patch 0's quantization costs
  Attack        default    0.000 -> MIDI  64 ->    0.118  (delta +0.118)
  Sustain       default    0.000 -> MIDI  64 ->    0.189  (delta +0.189)
  Output        default    0.000 -> MIDI 100 ->    0.047  (delta +0.047)
  Attack Speed  default    1.000 -> MIDI  64 ->    1.013  (delta +0.013)
  Sustain Hold  default  150.000 -> MIDI  38 ->  149.606  (delta -0.394)
```

**What the run settles, and one thing it corrected.**

- **Q1.** `transient_dual=True` puts an attack boost and a sustain cut on
  the same hop 43 times in 203, and each section's effect moves by at most
  0.092 dB between running alone and running in company — inside T2's 0.5 dB.
  The single pair does it 0 times, which is the planted fault.
- **The superposition test was wrong, and the run is what showed it.**
  Station A's first pass measured only `|both − (alone + alone)|` and read
  **0.000000 dB** for `transient_dual=False` against 0.092 dB for
  `True` — i.e. the *faulted* configuration scored better. A gain computer
  that selects one section by the sign of one difference decomposes exactly,
  so that statistic cannot see the defect at all; the 0.092 dB on the dual
  path is int16 quantisation in two separately-rendered traces. The hop
  count is the discriminator, and the fault was planted before the claim was
  written rather than after.
- **The peak-hold needs an instantaneous partner.** With
  `sustain_fast_attack_ms` at its 1 ms default the sustain gain fires at the
  onset and falls back — 11.832 dB below its running maximum inside the
  first 200 ms, where T4 allows 0.25 — and costs the attack peak half a
  decibel when both controls are set. At 0.0 the drop is 0.008 dB and the
  attack peak is +11.998 dB.
- **The detector decides T5's steady clause.** A 1 kHz burst at Attack +12
  reads +2.187 dB in its steady section peak-detected and +0.211 dB with a
  3 ms RMS window; the transient peak is +12.000 dB either way. The two
  attack envelopes have different attack/release ratios, so on a periodic
  signal they never converge and the shaper applies a standing gain — which
  is T5's own disconfirmer, reached with the shipped detector.
- **T6 has no signal in it.** Gain-trace 10–90 % rise times of 0.042, 0.042
  and 0.041 ms across material whose own rises span 16:1. Station C states
  the disconfirmation through the class.
- **Patch 0's quantization** costs +0.118 dB of Attack, +0.189 dB of
  Sustain, +0.047 dB of Output, 1.3 % of Attack Speed and 0.4 ms of Sustain
  Hold. A fresh instance from the constructor's defaults carries none of it.


### App. A1 — §§1–8 as the seed left them, 2026-09-06

Station A rewrote §§1–8 on 2026-09-07 to the five-minute read vision §7 asks
for, moved the derivations into **App. A2**, and settled §8's three opens.
Nothing was dropped: the seed's own §§1–8, verbatim and complete, are kept
here — including the standout paragraph's attribution discussion, the
VCA-count correction, the second-pass note, the six-macro surface with
`Mix`, and the three questions in their open form.

<!-- begin verbatim: TransientShaper.md sections 1-8, seed of 2026-09-06 -->

# Effects Dossier — `TransientShaper` (SPL Transient Designer)

**Class:** `lib/audioeffects/dynamics.py` — read once, for §7.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** SPL Transient Designer *(proposed, vision §4.2)* — **confirmed.**
SPL's own manual for the RackPack module 2715 was reached (S1) and describes
the mechanism, names it (Differential Envelope Technology), gives both control
ranges and prints the four envelope diagrams the design turns on. It is the
originator of the mechanism's *name*: SPL calls it Differential Envelope
Technology, "a registered trademark" (S2), and the vision calls SPL "the
originator of the differential-envelope design". The independent review reached
this run calls the box "a new type of dynamic control" that, "though it is
related to both the compressor and the expander … could not fairly be described
as either", and closes that "there's nothing else on the market like it" (S2).
*Corrected by the audit: the first draft attributed the phrase "for the first
time" to S2 — that phrase does not appear in the article, and no source reached
establishes priority, so "originator" remains the vision's claim and is not
treated as sourced here.* No swap is argued.
**Grade:** literature — a manufacturer's manual with a stated mechanism and
labelled envelope diagrams, plus an independent review; no schematic and no
component values were reached (§2).
**Portability tier:** needs audioif-own nodes (`audiodynamics`)
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

Two independent envelope pairs drive one THAT 2181 VCA — the *singular* gain
element is S2's ("the audio signal path is exceptionally clean with a THAT 2181
used as the gain control element"); S1 says only "THAT 2181-VCAs", plural, and
never states a count per channel (audit correction to the attribution) — and
there is no threshold anywhere in the box. In the **ATTACK** circuitry, "the first one
generates a voltage (Env 1) that follows the original waveform. The second
envelope generator creates the envelope Env 2 with a slower attack", and
"from the difference of both envelopes the VCA control voltage is derived";
positive settings raise the shaded difference, negative settings reduce it
(S1, Diagrams 1–3). In the **SUSTAIN** circuitry the same trick runs the other
way: "the envelope tracker Env 3 again follows the original waveform. The
envelope generator Env 4 maintains the level of the sustain on the peak-level
over a longer period of time", the control voltage is again the difference,
and "the gradient of the control voltage matches the time flow of the original
signal" (S1, Diagrams 4–6). SPL states plainly that the two "operate
simultaneously and don't affect each other". Because both control voltages are
*differences of envelopes of the same signal*, absolute level cancels: "SPL's
DET is capable of level-independent envelope processing and thus makes any
threshold settings unnecessary … both low and loud signals (pianissimo to
fortissimo) are treated the same way", and "other common controls of dynamic
processing, such as ratio or parameters for time-constants are automated and
optimized adaptively in a musical manner according to the characteristics of
the input signal". What is left on the panel is **Attack, ±15 dB**,
**Sustain, ±24 dB**, and on this module an **Output Gain** from −22 to +6 dB
with 0 dB at 12 o'clock (S1). The independent review reached puts it the same
way from the outside: "no meters, no threshold controls, no ratio knobs and no
make-up gain controls" (S2).

## 2. Sources and license calls

All fetched 2026-09-06; nothing from memory.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** SPL electronics, *Manual … (App. S1) | The DET description, both control circuitries … (App. S1) | "This document is the property of SPL and may … (App. S1) | <https://spl.audio/wp-content/uploads/RackPack_2715_TD_BA_E.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Paul White, "SPL Transient Designer", *Sound On Sound* … (App. S2) | Independent corroboration: "one generator follows … (App. S2) | "All contents copyright © SOS Publications … (App. S2) | <https://www.soundonsound.com/reviews/spl-transient-designer> | yes — HTML, full article, not paywalled |
| **Local** `audioif/src/shared/audioif_dynamics.{c,h}`, `audioif/docs/upstream-diff.md`, the probes in the Appendix | What the palette's transient mode actually does | MIT (audioif) | — | yes |

*Second-pass result: both licence calls stand as written and S1's is
strengthened by a second line; every S1 and S2 quotation verified verbatim
(including the absence of "for the first time" from S2); two flags, marked
inline.*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **Level-independent, thresholdless.** One recorded hit rendered at −6, −20, −40 and −60 dBFS produces gain traces that agree within 0.5 dB at every point of the trace, aligned on the hit's onset. The kit's −80 dBFS render is taken too and **recorded, not held to the bound**: at −80 dBFS a 16-bit hit is a handful of LSBs and the trace is quantisation-limited, so a deviation there is the probe's, not the class's | S1 ("level-independent envelope processing … … (App. T1) | high — stated by the … (App. T1) | A gain trace that changes with input level; any level at which the processing stops | LEVELS |
| T2 | **Attack and Sustain are two circuits acting at once.** With Attack +12 dB and Sustain −12 dB set together, a single hit shows positive gain during its transient **and** negative gain during its decay, and each within 0.5 dB of what the same setting produces alone | S1 ("Both ATTACK and SUSTAIN control … (App. T2) | high — stated as a … (App. T2) | One control's setting changing the other's measured effect by more than 0.5 dB; or a gain trace that can only ever have one sign | BOTH |
| T3 | **Attack spans ±15 dB and Sustain ±24 dB**, and the measured peak gain tracks the setting within 1 dB across both spans | S1 (panel scales and text); S2 | high | A control that saturates before its stated end, or overshoots it | RANGE |
| T4 | **The sustain envelope is a peak-hold, not a slow follower.** Env 4 "maintains the level of the sustain on the peak-level over a longer period of time", so on an exponentially decaying note the sustain gain **grows monotonically** — no sample more than 0.25 dB below the trace's running maximum — through at least the first 200 ms after the onset; and the trace's shape follows the note's own decay rate, so the time to reach 90 % of its peak differs by at least 2:1 between a note decaying at 10 dB/s and one at 40 dB/s. *(The 0.25 dB, 200 ms and 2:1 figures are the dossier's own criteria — S1 gives no time constant — chosen so the row can fail; a slow one-pole follower fails the first clause outright, as §4 records.)* | S1 (Sustain Control Circuitry, Diagram 4) | medium — the sentence … (App. T4) | A sustain gain that peaks early and falls back, or one whose shape is the same for a fast and a slow decay | DECAY |
| T5 | **Attack acts only on the transient.** With Attack at +12 dB, the peak gain in the first 5 ms of a burst is +12 dB within 1 dB, and the gain in the steady section 100 ms later is 0 dB within 0.5 dB — the ratio between the two is at least 10 dB | S1 (Diagrams 2 and 3: the shaded difference … (App. T5) | high | A steady section more than 0.5 dB off unity at any Attack setting; a transient peak gain more than 1 dB from the setting; a transient-to-steady ratio under 10 dB | SPLIT |
| T6 | Time constants adapt to the material: two hits whose own 10–90 % onset times differ by 4:1 produce gain traces whose 10–90 % rise times differ by at least 5:1 — more than the hits' own difference, which is what a fixed coefficient cannot give. *(The 4:1 and 5:1 figures are the dossier's own criteria; neither source gives a number, which is why the confidence is low.)* | S1 ("automated and optimized adaptively in a … (App. T6) | **low** — asserted by … (App. T6) | Gain-trace rise times that differ by 4:1 or less, i.e. tracking the hits' own difference and no more — what fixed coefficients give; identical rise times on both hits | ONSET |

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**5 %**, ESP32-S3 **10 %**. Lean patch expected: **no** — four one-pole
followers and one multiply per frame.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose first, and the palette gets further here than anywhere else in this
unit.** `audiodynamics.Dynamics(DYN_TRANSIENT)` already implements a
differential envelope: a fast follower (1 ms attack, 50 ms release) and a slow
one (25 ms, 300 ms) at `audioif_dynamics.c:215-222`, whose difference **in
decibels** is normalised by 6 dB, clamped to ±1 and mapped to
`attack_gain_db` when positive and `sustain_gain_db` when negative
(`:290-300`). Because the difference is taken in dB, absolute level cancels —
and **T1 is already met**: measured, the same hit at −6, −20, −40, −60, −72
and −85 dBFS produced a peak attack gain of **+12.000 dB at every level**
(A9). That is the standout's headline claim, satisfied by the existing node,
and the seed records it so the rebuild does not go looking for a node it does
not need.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

Both additive on `audiodynamics` (D1), defaulting to today's behaviour so
`dynamics_probe.py`'s hash is unchanged.

- **N-TRAN-1 — two independent gains from one node (unblocks T2).** A second …  *(argument in full: App. R)*
- **N-TRAN-2 — a peak-hold sustain envelope (unblocks T4).** An option making …  *(argument in full: App. R)*
- **Not asked for:** adaptive time constants (T6). No source gives a mechanism …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Six macros. The box has three controls; the extra three expose behaviours S1
describes but does not knob, under vision D2.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Attack | BIPOLAR | −15 … +15 dB | SPL Attack |
| 1 | Sustain | BIPOLAR | −24 … +24 dB | SPL Sustain |
| 2 | Output | BIPOLAR | −22 … +6 dB | SPL Output Gain (RackPack module) |
| 3 | Attack Speed | UNIPOLAR | 0.2 … 5 ×, log | the pair of attack time constants S1 leaves internal |
| 4 | Sustain Hold | UNIPOLAR | 0 … 500 ms, log | Env 4's "longer period of time" |
| 5 | Mix | UNIPOLAR | 0 … 100 % | no panel control; parallel shaping, and the Tier 1 wire at 0 |

Characters: none — DET is one mechanism and both sections use it. Patches:
**Snap** (attack up, sustain flat), **Room Off** (sustain down), **Room On**
(sustain up), **Soften Pick** (attack down), **Kick Punch** (attack up,
sustain slightly down), **Ambient Swell** (attack well down, sustain up).

## 7. Defects in the current class the rebuild must not repeat

- **No surface, and the two controls are frozen at construction.**
  `MACRO_LABELS = ()` at `dynamics.py:210`, `PATCHES = {0: ("Default", ())}`
  at `:212`, and `attack_db`/`sustain_db` are passed once at `:214-217`. A
  transient shaper whose two knobs cannot move is not a transient shaper.
- **The docstring promises what the node cannot do.** `:203-204` — "Positive
  attack_db pushes the hit forward … sustain_db does the same for what rings
  after it" — reads as two independent actions, and the node applies exactly
  one of them at a time (A10).
- **No output gain**, so the class changes level with every setting and gives
  the caller nothing to put it back with; SPL's own module added exactly that
  control for exactly that reason (S1).
- **The 6 dB normalisation is invisible.** `norm = diff / 6.0f` clamped to ±1
  (`audioif_dynamics.c:293-298`) means every transient sharper than 6 dB gets
  the full setting and no more; the class neither exposes it nor documents it.

## 8. Open questions

1. **Does the series pair meet T2?** The measurement in A11 shows both gains
   can coexist; what it does not show is whether the interaction stays inside
   T2's 0.5 dB. That measurement decides whether N-TRAN-1 is filed at all, and
   it is the first thing the implementation session should run. *Phase 1, from
   this seed.*
2. **T6's fate.** Adaptive time constants are asserted by both sources and
   measured by neither. If Station C disconfirms it, does the class keep macro
   3 (Attack Speed) as a manual stand-in, or drop it? *Implementation session,
   with the disconfirmation recorded either way.*
3. **Whether `Mix` belongs here.** Parallel transient shaping is common
   practice and is not in either source; it is proposed under D2 as a surface
   choice, not as a trait, and the seed flags it so a later reader does not
   mistake it for something the Transient Designer does. *Implementation
   session.*

<!-- end verbatim -->

