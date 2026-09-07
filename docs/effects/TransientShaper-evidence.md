# Evidence Pack — `TransientShaper` (SPL Transient Designer)

Written from `docs/effects/EVIDENCE-TEMPLATE.md`, one section per class-gate
item, in the gate's order (the anchor repo's `docs/effects-roadmap.md`, "The
class gate").

**Three rules this file is written under.** Numbers come from runs, and every
figure names the command, the interpreter and the rate. A measurement with no
planted fault is not cited. §11 says what is not done, as its own section.

Every number below comes from one of three commands, all run 2026-09-07:

```
$ audiocomponents/.venv/bin/python tools/phase2_probes/transientshaper_evidence.py
$ sh tools/phase2_probes/transientshaper_interpreters.sh <renderdir>
$ audiocomponents/.venv/bin/python tools/phase2_probes/transientshaper_across.py <renderdir>
```

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `TransientShaper` |
| Dossier | [`TransientShaper.md`](TransientShaper.md), traits frozen 2026-09-07 at `f93ec36` |
| Module | `lib/audioeffects/rebuilt/transientshaper.py` |
| Base | `_component.Component` |
| Family / phase | Dynamics, roadmap Phase 2 |
| Standout | SPL Transient Designer (RackPack module 2715) — Differential Envelope Technology |
| Grade | literature |
| Portability tier | **audioif** (`REQUIRES = ("audiodynamics",)`) |
| Landed in commits | `f93ec36` (Station A), `9a6d0bf` (Station B), `ad0d053` (Station C) — §12, and the deviation from the gate's one-commit rule is in §11 |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3`. Checked, not assumed: `git diff 2f6cbc3 HEAD` in audioif touches only `.flake8` and `apply_cp_patches.sh`, and `git diff 2f6cbc3 HEAD -- src/shared/audioif_dynamics.{c,h} src/audiodynamics/ lib/audiodynamics.py` is **empty**, so every reading here is the pin's behaviour whichever of the two the venv's `_audioif` was built from |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3 (`pydevices-audioif` 0.2.0); `cmods/bin/micropython` MicroPython v1.28.0-dirty, `_mpy=2822`; `cmods/bin/circuitpython-effects` CircuitPython 10.2.1-dirty, `_mpy=2822` |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** **yes.** Commit
`f93ec36` ("TransientShaper Station A") froze §3's T1–T6 and settled §8; the
class module was written after it and did not exist at that commit.

---

## 1. Traits

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| T1 | Level-independent, thresholdless — one hit at −6, −20, −40, −60 dBFS, traces agreeing within 0.5 dB | **demonstrated on the peak readout; the strict point-by-point clause holds only over −6…−40 dBFS** | LEVELS, 48 kHz, cpython. Peak gain at Attack +12: **+12.000, +12.000, +11.996, +11.953** dB, spread over −6…−60 **0.047 dB** (bar 0.500). −80 dBFS recorded not held: **+11.076 dB** | the node swapped for a threshold (`DYN_COMPRESS`, −30 dB, 4:1): **+16.292, +5.794, +0.000, +0.000, +0.000** dB, spread **16.292 dB** → **RED** | **R1 — "the peak agrees; the trace need not."** It does not. Point-by-point over 0–200 ms reads **3.422 dB** at Attack +12 and **0.731 dB** at Attack +3. Two causes, both measured, neither the shaper's arithmetic: at +12 the −6 dBFS render **clips** (578 samples at full scale; adjacent pairs −6/−20 3.422, −20/−40 0.163, −40/−60 1.203 dB), and at +3, where nothing clips, the residue is all in the quiet leg (−6/−20 **0.014**, −20/−40 **0.113**, −40/−60 **0.649** dB). The −60 leg's own cause is named: `gain_to_db(env + 1e-5f)` (`audioif_dynamics.c:628-630`) is a −100 dBFS pedestal on each envelope — 1 % of a −60 dBFS envelope, 10 % of a −80 dBFS one — so the difference of logs stops being scale-free as the signal approaches it, which is exactly the graded departure +12.000 → +11.996 → +11.953 → +11.076. **The claim is narrowed, not rescued: see §11.** |
| T2 | Attack and Sustain are two circuits acting at once, each within 0.5 dB of its effect alone | **demonstrated** | BOTH, 48 kHz, cpython, `hit_levels_-6`, Attack +12 with Sustain −12, hop 1 ms: **43 of 203 hops** carry an attack boost (> +0.5 dB) and a sustain cut (< −0.5 dB) at the same instant; each section's effect moves **0.092 dB** between alone and in company (bar 0.500) | `transient_dual=False` — the shipped gain computer, which selects one section by the sign of one difference: **0 of 203 hops** → **RED** | **R2 — "43 of 203 is the 1 ms analysis hop."** At hop 0.25 ms it reads **172 of 811** — the same 21 % of the trace, so the overlap is the class's and not the window's. *(Recorded because Station A got it wrong first: the superposition statistic alone scores the faulted build **perfectly** — 0.000 dB — because a selector decomposes exactly. See the dossier's App. A2.)* |
| T3 | Attack spans ±15 dB and Sustain ±24 dB, peak gain tracking the setting within 1 dB | **demonstrated** | RANGE, 48 kHz, cpython. Attack −15 → **−15.005**, −12 → −12.004, −6 → −6.002, 0 → +0.000, +6 → +6.000, +12 → +12.000, +15 → **+14.615**. Sustain −24 → **−24.321**, −12 → −12.079, +12 → +12.000, +24 → **+24.000**. Worst error **0.385 dB** (bar 1.000) | the Attack span halved inside `_apply_macro`, so the knob still reads ±15 and the node gets half: Attack +12 → **+6.000 dB** → **RED**. *(A fault written into `_build` is undone by the macro seeding that follows it — worth knowing, and why this one is in `_apply_macro`.)* | **R3 — "+14.615 at +15 dB is the control saturating."** It is the container: **884 of 96000 samples** of that render sit at full scale, because the probe peaks at −6 dBFS and +15 dB of gain does not fit in int16. Nothing in the node saturates: the two spans below the ceiling track to within 0.005 dB. |
| T4 | The sustain envelope is a peak-hold: monotone growth within 0.25 dB through 200 ms, and a t90 differing at least 2:1 between a 10 dB/s and a 40 dB/s decay | **demonstrated** | DECAY, 48 kHz, cpython, Sustain −12, Sustain Hold 150 ms. Monotone drop over 0–200 ms **0.008 / 0.006 dB** (bar 0.250); t90 **902 vs 371 ms = 2.43:1** (bar 2.00:1); depth at 400 ms 3.887 dB | **two, on the two clauses.** Sustain Hold forced to 0 — a plain follower: t90 **920 vs 479 ms = 1.92:1** → **RED** on the ratio clause, depth at 400 ms halved to 1.923 dB. `sustain_fast_attack_ms` back at its 1 ms default: monotone drop **11.832 / 11.704 dB** → **RED** on the monotone clause | **R4 — "2.43:1 depends on the arbitrary 0.9 of peak."** It does not: **t80 2.36:1**, t90 2.43:1, **t95 2.46:1**, all above the bar, and the ordering is stable. |
| T5 | Attack acts only on the transient: peak in the first 5 ms within 1 dB of +12, steady section 100 ms later within 0.5 dB of 0, ratio at least 10 dB | **disconfirmed on the middle clause, by 0.041 dB** | SPLIT, 48 kHz, cpython, 1 kHz burst at −6 dBFS, Attack +12, hop 0.1 ms: peak over 0–5 ms **+12.000 dB** ✓, ratio **11.46 dB** ✓, steady at 100 ms **+0.541 dB** ✗ (bar 0.500). The same trace at 150 ms **+0.211**, 200 ms **+0.116**, 240 ms **+0.083 dB**; the RMS ratio across the whole steady section 100–240 ms is **+0.205 dB** | the rectified peak detector instead of the 3 ms RMS: steady at 100 ms **+3.505 dB**, ratio **8.50 dB** → **RED on both** the steady and the ratio clause | **Cause, and what the class does instead.** The attack pair's slow envelope has a 25 ms attack, so at 100 ms it is still ~2 % short and the difference has not finished decaying; this is convergence, not a standing gain, and the trace is inside 0.5 dB by 122 ms. **Attack Speed 2×** reads **+0.119 dB** at 100 ms and **5×** reads **+0.045 dB**, both with the transient peak still at +12.000 — so the trait is reachable from the panel, at a faster attack character than the default. The class ships the 1× default and says so; the docstring does not claim the 100 ms figure. |
| T6 | Time constants adapt to the material: a 4:1 spread of onset times giving at least a 5:1 spread of gain-trace rise times | **disconfirmed** | ONSET, 48 kHz, cpython, hop 0.05 ms: gain-trace 10–90 % rise **0.042, 0.042, 0.041 ms** for material 10–90 % rises of 0.40, 1.60, 6.40 ms — **1.02:1** where T6 asks 5:1 | not applicable: a disconfirmed trait needs no fault. The mechanism is cited instead — the four coefficients are computed once per block from fixed config fields (`audioif_dynamics.c:417-436`), and `norm = diff/6` clamps at ±1 (`:630-636`), so the gain reaches full value as soon as the two envelopes are 6 dB apart | **R6 — "0.042 ms is the analysis floor, not the class."** Re-read ten times finer, at hop 0.005 ms: **0.0210 ms** for the 0.4 ms material against **0.0410 ms** for the 6.4 ms material — **1.95:1**, still far under 5:1, and in the direction T6's own disconfirmer names ("tracking the hits' own difference and no more"). The finer read strengthens the disconfirmation rather than overturning it. |

- **demonstrated** = a measurement, that measurement red on a planted fault of
  the same kind, and a surviving refutation. T1's refutation did **not**
  survive intact; its verdict is narrowed in the cell and carried into §11.
- **Characters:** none. DET is one mechanism and both sections use it.

**Refutation pass.** Run by this session, 2026-09-07, as a written adversarial
pass (`refute()` in the driver) — **not by an independent agent**; that is a
gap, and it is in §11. What it went after: whether each headline number was
an artefact of the readout rather than the class. It broke one claim (T1's
strict point-by-point clause, twice, and both causes turned out to be int16
rather than the shaper), it hardened three (T2 across hops, T3's ceiling,
T4 across t80/t90/t95), and it strengthened one disconfirmation (T6 at a
tenfold finer hop).

---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`. The `cp` column is measured in process by
the driver; `mp` and `cpy` are `tools/render_effect.py` renders on those
interpreters, analysed on CPython (kit spec §1).

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Defaults are a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node silent and stateless, source untouched | STATE | pass | n/a | n/a | pass¹ | n/a | n/a | pass¹ | n/a | n/a |
| `deinit()` releases every node, source still renders | STATE | pass | n/a | n/a | pass¹ | n/a | n/a | pass¹ | n/a | n/a |
| `capabilities` names exactly what is honoured | STATE | pass | n/a | n/a | pass¹ | n/a | n/a | pass¹ | n/a | n/a |
| Pulling `output` allocates nothing | STATE | pass | n/a | n/a | pass¹ | n/a | n/a | pass¹ | n/a | n/a |
| Rate-honest: no Hz-valued span exists on this surface | — | n/a² | n/a² | n/a² | n/a² | n/a² | n/a² | n/a² | n/a² | n/a² |
| Every invariant also holds at `channel_count` 1 | (all) | pass | — | — | — | — | — | — | — | — |

¹ **STATE is CPython-only, and is run at 48 kHz** — it drives the class
between renders (`tracemalloc`, node enumeration), which the kit spec keeps on
the desktop. The `pass¹` cells are **not measured**; they are marked so rather
than left blank, and they are in §11.

² The class carries no Hz-valued setting: its five macros are two dB gains, a
dB trim, a dimensionless factor and a time in milliseconds, and
`audioif_dynamics_ms_to_coef` converts the milliseconds against the running
rate in C (`:9-14`). There is nothing for `self._hz()` to clamp, so RESPONSE's
Nyquist leg has no subject here. Every other invariant *is* run at all three
rates, above.

**Numbers behind the cp column** (48 kHz / 44.1 kHz / 22.05 kHz):
WIRE `0 of 47104 / 45056 / 22528` samples differ; TAIL tail `0` samples
against a declared 0, residual `0` LSB, `dc_step` residual `0` LSB; LEVEL
wet:dry RMS `0.0 dB` both channels; CLICK measured `[0.0, 0.0]` samples
against a reported `0`, at the defaults *and* at patch 1 (Snap), so the
reading is not simply the wire's; STATE reset residual `0` LSB, live nodes
after `deinit()` `[]`, source resumed `True`, `32` bytes retained across 100
single-block pulls (bar 8192).

**Mono.** The dossier's §3 says a mono source gets one channel-linked gain —
SPL's Link switch, and this class's default. Measured: the whole Tier 1 block
at `channel_count` 1, 48 kHz, is green (WIRE `0 of 23552`, TAIL residual 0,
LEVEL `[0.0]`, CLICK `[0.0]`, STATE clean), and the class builds a 1-channel
node from a 1-channel source, which `_component` checks at construction.

**Planted faults for this block**, each beside its clean control, all at
every rate and at `channel_count` 1:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | `makeup_db=0.002` on the node after `_build` | green, 0 differ | **RED**, 40756 / 38984 / 19492 samples differ |
| TAIL | `+1 LSB` of DC held once the node has seen signal (`kit_faults.StuckDc`) | green, tail 0, residual 0 | **RED**, tail 144000 / 132300 / 66150 samples, residual 1 LSB, `dc_step` residual 1 LSB |
| CLICK | `latency_samples` reported 256 short, DSP untouched | green | **RED** at all three rates, audio digest unchanged (`29fa03a1` / `59db6aa1` / `55222081`) |
| STATE | the node registered with `deinit=False` | green, `[]` | **RED**, `live_nodes_after_deinit = ['_output']` |

`reset()` and `deinit()` walk the list `_component` requires the class to
enumerate with `self._own()`. **Nodes this class owns, in build order:** one —
`audiodynamics.Dynamics(DYN_TRANSIENT)`, registered with the default
`reset=True, deinit=True`.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, block 256, stereo, from
`tools/render_effect.py` on each interpreter.

```
$ sh tools/phase2_probes/transientshaper_interpreters.sh <renderdir>
$ audiocomponents/.venv/bin/python tools/phase2_probes/transientshaper_across.py <renderdir>
```

| Probe | Rate | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|
| `chord` (defaults — the wire) | 48000 | `7bd32675` | `7bd32675` | `7bd32675` | *(board run)* | *(board run)* |
| `chord` | 44100 | `4d20fe71` | `4d20fe71` | `4d20fe71` | *(board run)* | *(board run)* |
| `chord` | 22050 | `21b734dd` | `21b734dd` | `21b734dd` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | `1fe01e81` | `1fe01e81` | `1fe01e81` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | `ff5e866d` | `ff5e866d` | `ff5e866d` | *(board run)* | *(board run)* |
| `noise_det` | 22050 | `d3edbfcd` | `d3edbfcd` | `d3edbfcd` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | `662782d1` | `662782d1` | `662782d1` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | `b1e4eb69` | `b1e4eb69` | `b1e4eb69` | *(board run)* | *(board run)* |
| `sweep_log` | 22050 | `1ccee039` | `1ccee039` | `1ccee039` | *(board run)* | *(board run)* |
| **`chord` patch 1 (Snap)** | 48000 | `4711c4f1` | `4711c4f1` | `4711c4f1` | *(board run)* | *(board run)* |
| `chord` patch 1 | 44100 | `3a54a111` | `3a54a111` | `3a54a111` | *(board run)* | *(board run)* |
| `chord` patch 1 | 22050 | `00ee59a5` | `00ee59a5` | `00ee59a5` | *(board run)* | *(board run)* |
| **`noise_det` patch 1** | 48000 | `6608b78d` | `6608b78d` | `6608b78d` | *(board run)* | *(board run)* |
| `noise_det` patch 1 | 44100 | `2373eccd` | `2373eccd` | `2373eccd` | *(board run)* | *(board run)* |
| `noise_det` patch 1 | 22050 | `26949211` | `26949211` | `26949211` | *(board run)* | *(board run)* |
| **`burst_silence` Attack +12 / Sustain −12** | 48000 | `cf0af8f5` | `cf0af8f5` | `cf0af8f5` | *(board run)* | *(board run)* |
| `burst_silence` Attack +12 / Sustain −12 | 44100 | `80f92725` | `80f92725` | `80f92725` | *(board run)* | *(board run)* |
| `burst_silence` Attack +12 / Sustain −12 | 22050 | `cb1ddff5` | `cb1ddff5` | `cb1ddff5` | *(board run)* | *(board run)* |

**Desktop agreement: yes**, all eighteen rows, three interpreters each.

**The first nine rows are the class at its defaults, which is a wire** —
they prove the render path agrees, not the shaper. The nine bold rows are the
shaper working, and `chord` moves from `7bd32675` to `4711c4f1` under patch 1,
so the comparison has a subject.

**Board agreement:** not taken — see §4 and §11.

**Block-size ladder:** not run. This class holds no ring or partition whose
size a block could straddle (it is one per-sample gain cell with no buffer of
its own), so the ladder has no mechanism to reach here; every render above is
at block 256. Recorded rather than silently skipped.

**Board columns — what the 2026-09-07 board run did and did not settle.** The run
in §4 put the class on both boards with a *different* tool and a *different*
probe (`tools/measure_effect_cost.py`, its own integer probe, 128 blocks at
48 kHz), so it does not fill the cells above, which are this table's probes at
this table's rates: those are still owed. What it does establish is that the
**ESP32-P4 and the ESP32-S3 render this class byte for byte identically** —
§4 carries the digest.

---

## 4. Tier 3 — cost on the boards

**Measured on both boards, 2026-09-07.** `tools/measure_effect_cost.py`,
target `effect:TransientShaper`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: ESP32-P4 **5 %** of one stereo block's real-time deadline;
ESP32-S3 **10 %**. Lean patch expected: **no**.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("TransientShaper", …)` | 904.0 | 1.106 (0.793 marginal) | 4.82 | 1776 B | **no** — 14.9 % marginal, 20.7 % total, against 5 % |
| S3 | 0 | construction defaults, `audioeffects.create("TransientShaper", …)` | 466.5 | 2.144 (1.672 marginal) | 2.49 | 1776 B | **no** — 31.3 % marginal, 40.2 % total, against 10 % |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:TransientShaper`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 5 %, S3 10 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`4169efd90ecf44dd` on the ESP32-P4 and `4169efd90ecf44dd` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is the **same value**.

It is also the bare probe's own digest (`4169efd90ecf44dd`): at construction
defaults (patch 0 `Flat`) this class hands the probe back unchanged. The
CPU figure above is the built graph running — every node is pulled every
block — but **the digest is not a check on the audio**, and a board run at
a working patch is still owed.

**Owed: a `" - lean"` patch.** At 31.3 % of the deadline the class is over
its ESP32-S3 budget of 10 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** patch 1 `Snap`, the expensive path this section names. The run measures patch 0 `Flat`.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**When it is run, the expensive path is patch 1 (Snap) or Attack +12 with
Sustain −12** — the class at its defaults is a wire, and a cost figure taken
there would be a figure for a multiply by 1.0. `measure_effect_cost.py`
refuses a silent render; a *wire* is not silent, so the refusal will not catch
this one, and the settings column is what has to.

**There is no `" - lean"` patch and there will not be one from the surface.**
The class is a single node; its only cost-bearing choices — the RMS detector
and the second envelope pair — are fixed in `_build` and are not on any macro,
deliberately (a macro that turns off the RMS detector would put T5's
disconfirmer in the player's hands). If the S3 figure misses 10 %, the lever
is a node-level one and it belongs in a follow-up, not in a patch.

---

## 5. Latency

Reported `latency_samples` = **0**. `tail_samples` = **0**.

| Rate | Reported | Measured (sub-sample, per channel) | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | `[0.0, 0.0]` | 0.0 | 0.0000 |
| 44100 | 0 | `[0.0, 0.0]` | 0.0 | 0.0000 |
| 22050 | 0 | `[0.0, 0.0]` | 0.0 | 0.0000 |

Measured at the defaults **and** at patch 1 (Snap), so the reading is not the
wire's alone; both give `[0.0, 0.0]`. `channel_count` 1 at 48 kHz reads
`[0.0]`.

Dossier latency budget: **0 samples / 0.00 ms**. Met: **yes**.

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| — | — | — | — | — |

**There are none.** The class builds `audiodynamics.Dynamics` without
`lookahead_ms`, which is the node's only latency-bearing option, and exposes
no way to set it: it is absent from `_build`'s signature, from
`MACRO_LABELS` and from `_apply_macro`. The docstring states "0 samples,
0.00 ms, at every setting and every sample rate" and says why a differential
envelope cannot look ahead.

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
CLICK **RED** at 48 kHz, 44.1 kHz and 22.05 kHz, with the audio digest
identical to the clean run's (`29fa03a1`, `59db6aa1`, `55222081`).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Attack | BIPOLAR | −15 … +15 dB | SPL Attack |
| 1 | Sustain | BIPOLAR | −24 … +24 dB | SPL Sustain |
| 2 | Output | BIPOLAR | −22 … +6 dB | SPL Output Gain (module 2715) |
| 3 | Attack Speed | UNIPOLAR | 0.2 … 5 ×, log | the attack detector's four time constants, which S1 leaves internal |
| 4 | Sustain Hold | UNIPOLAR | 0 … 500 ms | Env 4's "longer period of time" |

Five of a permitted sixteen. `Mix` was proposed by the seed and **dropped** at
Station A with its reason (dossier §8 Q3).

| Patch | Name | What it is for |
|---|---|---|
| 0 | Flat | the constructor's defaults on the 0–127 grid |
| 1 | Snap | attack up, sustain flat — the box's headline move |
| 2 | Room Off | sustain down: less room on a close-miked kit |
| 3 | Room On | sustain up: more decay on a dry room |
| 4 | Soften Pick | attack down: pull the pick out of a DI guitar |
| 5 | Kick Punch | attack up, sustain slightly down |
| 6 | Ambient Swell | attack well down, sustain up |

All seven render, on all three interpreters, with distinct peaks — from the
three-interpreter smoke on `cmods/bin/micropython`:

```
ok   TransientShaper          patch 0   peak 11211
ok   TransientShaper          patch 1   peak 15318
ok   TransientShaper          patch 2   peak 13908
ok   TransientShaper          patch 3   peak 8832
ok   TransientShaper          patch 4   peak 13858
ok   TransientShaper          patch 5   peak 11099
ok   TransientShaper          patch 6   peak 7010
```

**Patch 0 is the defaults quantized, not an exact wire.** Measured
(dossier App. A2): Attack +0.118 dB, Sustain +0.189 dB, Output +0.047 dB,
Attack Speed 1.013 ×, Sustain Hold 149.606 ms. A fresh instance from the
constructor's defaults carries none of that, because `_init_macros` seeds
through `macro_position()` unquantized — and that is the state WIRE is
measured in above.

**`capabilities` = `()`.** The class never reads `self._transport()` (the name
does not appear in `transientshaper.py`), and the dossier's reason is quoted:
*"the Transient Designer has no tempo input"*. STATE reads the declared tuple
and finds `()`.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiodynamics",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Dynamics(DYN_TRANSIENT)` with `transient_dual`, `slow_hold_ms`, `sustain_fast_attack_ms`, `detector="rms"` | `audiodynamics` | T1, T2, T3, T4, T5 | `audiodynamics` is audioif's own module and has no CircuitPython ancestor at all (`audioif/docs/upstream-diff.md:661`); the differential-envelope gain computer, the second envelope pair and the peak-hold exist nowhere in the ported C |

```
$ audiocomponents/.venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.043s

OK
```

The class enters that battery automatically — it walks `audioeffects.ALL` and
`rebuilt.known()`, and `rebuilt.known()` now returns
`('ExampleAudioif', 'ExampleStock', 'TransientShaper')`, with
`audioeffects.TransientShaper.__module__` resolving to
`audioeffects.rebuilt.transientshaper`, `TIER` `audioif` and `REQUIRES`
`('audiodynamics',)`.

**What that test does not prove**, repeated here as every pack must: blocking
a module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace. For *this* class the gap
is smaller than for a stock-tier one — the claim being made is that it needs
audioif, and it demonstrably renders on `circuitpython-effects`, the patched
build — but the converse, that a stock board raises rather than misbehaves,
rests on the `sys.modules` proxy.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began (`f93ec36`),
      and §1 lists every trait as demonstrated, disconfirmed with cause, or
      unmeasured — **T5 disconfirmed** on its middle clause by 0.041 dB with
      the cause and the lever, **T6 disconfirmed** with its mechanism, **T1
      narrowed** to −6…−40 dBFS on the strict point-by-point clause.
- [x] Every Tier 1 invariant green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz and on the patched CircuitPython, **except
      STATE**, which is CPython-and-48-kHz-only by the kit's own design and
      is marked so in §2 and §11. Every Tier 2 measurement names its rate.
- [x] Every demonstrated Tier 2 trait has a measurement shown red on a
      planted fault of the same kind (T1, T2, T3, T4 — T4 with two, one per
      clause).
- [ ] Every demonstrated trait survived an independent refutation attempt —
      **the pass was run, and it was not independent**: this session wrote
      both the claims and the refutations. §11.
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material (eighteen rows, §3); the P4 and S3 legs are not taken.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 14.9 % and S3 31.3 % of the deadline (marginal) against 5 % / 10 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz (and 22.05 kHz); the budget of 0 samples is met; there is
      no latency-adding option, and the docstring says 0.00 ms.
- [x] Five macros and six named patches beyond patch 0; `validate_api`,
      `validate_metadata`, the CPython suite — including this class's own
      `tests/test_cpython_effects_transientshaper.py`, eight tests, each
      trait assertion paired with its faulted counterpart in the same test —
      the portability-tier test, the three-interpreter smoke and flake8 all
      pass (§9) — but the **whole** `discover` suite did not complete on this
      contended machine; 110 of its 235 tests ran, chosen as the modules the
      gate names, and §11 says so. **No old-surface trait tests were
      retired**, because the
      old class had none: `grep -rn TransientShaper tests/` before this work
      returned nothing.
- [x] The README catalogue row and the class docstring describe the standout,
      the tier and the cost in a musician's terms.
- [ ] "The class's code, this file and the CHANGELOG line landed in **one**
      audiocomponents commit" — they landed in **three**, one per station, as
      the working instruction for this rebuild asked. §11.

---

## 9. Commands, verbatim

```
$ audiocomponents/.venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.043s

OK

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python -m unittest tests.test_cpython_effects_transientshaper
........
----------------------------------------------------------------------
Ran 8 tests in 2.213s

OK

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python -m unittest \
    tests.test_audio_component_api tests.test_component_foundation \
    tests.test_metadata_contract tests.test_rebuilt_registry \
    tests.test_portability_tier tests.test_cpython_effects_transientshaper \
    tests.test_cpython_effects_dynamics_eq tests.test_cpython_effects_library
----------------------------------------------------------------------
Ran 110 tests in 87.069s

OK

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python -m unittest discover -s tests -p "test_*.py"
did not complete in this session - see below

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 7700
ok   Vibrato                  patch 0   peak 11000

46 classes, 89 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 89 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 89 patches, 0 failures

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:TransientShaper")'
ROW	effect:TransientShaper	904.0	4.82	1.106	0.313	0.793	1776	4169efd90ecf44dd
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:TransientShaper")'   # the S3
ROW	effect:TransientShaper	466.5	2.49	2.144	0.472	1.672	1776	4169efd90ecf44dd
```

**The full `discover` run did not complete, and this is what was tried.**
Four attempts, each printing exactly **177 dots and then stopping for tens
of minutes**. The suite loads 235 tests; enumerating them by hand names the
178th as `test_effect_kit_11_20.RoundTrip.test_control_a_real_capture`, and
that class alone, run by itself, also exceeds two minutes. The cause is not
this class and not the kit: **five sibling class-builder worktrees are
running the same suite on this machine at the same time** — `ps` showed 18
concurrent `unittest discover` processes, and the process in this worktree
was accumulating CPU (1066 s → 1082 s of CPU in 20 s of wall clock), so it
was working rather than hung. Attempts: a plain run, a run with
`timeout 900` (killed at 900 s, exit 124), a run with `timeout 3000`, and a
run with `timeout 3600`. What is quoted above instead is the eight modules
the class gate actually names — the contract-level suite, the portability
tier and this class's own tests, **110 tests, OK** — plus every other gate
command in full. The remaining modules are the kit's own fault battery, which
this class does not touch. **The full-suite line of the gate is therefore not
met in this session; it is in §11.**

`tests/test_cpython_effects_transientshaper.py` is the fast subset of the
driver that a suite can carry: eight tests, and every trait assertion in it
has its faulted counterpart asserted in the same test (a wire against a
+0.002 dB output trim; `transient_dual` against the selector; the peak-hold
against a plain follower; the RMS detector against the rectified peak).

The full output of `transientshaper_evidence.py`,
`transientshaper_interpreters.sh` and `transientshaper_across.py` is what
§§1–5 quote, figure by figure; the three scripts are committed beside the
class so any figure here can be re-derived by re-running one command.

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

- **No surface, both controls frozen at construction** (`dynamics.py:210-217`)
  → five live macros and seven patches; `set_macro` and `program_change` both
  reach the node, shown by the seven distinct patch peaks in §6.
- **A docstring promising two independent actions the node applied one at a
  time** (`:203-204`) → `transient_dual=True`, and T2 measured at 43 of 203
  hops carrying both at once against 0 for the old behaviour.
- **No output gain** → macro 2, `makeup_db`, −22 … +6 dB, SPL's own span.
- **The 6 dB normalisation invisible** → named in the class docstring, and
  cited in §1 as the mechanism that disconfirms T6.

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 14.9 % and S3 31.3 % of the deadline (marginal)
  against 5 % / 10 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **The refutation pass was not independent.** The same session wrote the
  traits' measurements and the arguments against them. It did find and record
  a real error (Station A's superposition test, which scored the faulted build
  perfectly) and it did break T1's strict clause, so it was not a formality —
  but the roadmap asks for a second agent, and this is not one.
- **T1's strict point-by-point clause is met over −6…−40 dBFS, not
  −6…−60 dBFS.** Measured 0.113 dB over the narrower span and 0.649 dB
  including −60. Two causes, both named and measured (§1 R1); the −60 one is
  the node's `+1e-5f` envelope floor, which is a real class-side level
  dependence at low level, not only a probe artefact. What it would take to
  settle it: probe material with more headroom than int16, or a node change to
  that epsilon — the second is a node ask, not a class fix, and none is filed.
- **T5 is disconfirmed on its middle clause** (steady section +0.541 dB at
  100 ms against a 0.500 bar). The class is inside the bar by 122 ms and at
  Attack Speed 2×; the default is not. The dossier's frozen 100 ms was not
  moved to fit the result.
- **STATE is CPython-only and 48 kHz-only.** `reset()`, `deinit()`,
  `capabilities` and the allocation rule are not measured on MicroPython, on
  `circuitpython-effects`, or at 44.1 / 22.05 kHz — the kit's STATE drives the
  class between renders and lives on the desktop. §2's `pass¹` cells say so.
- **No stock CircuitPython board exists in this workspace**, so the
  portability tier's negative half rests on blocking a module in
  `sys.modules` (§7).
- **The full `discover` suite did not complete.** Four attempts, each
  stalling at the same place (the 178th of 235 tests,
  `test_effect_kit_11_20.RoundTrip.test_control_a_real_capture`) under five
  concurrent sibling suites on the same machine. The eight modules the gate
  names ran and passed — 110 tests, OK — but the whole-suite line is
  unverified here. What it takes: one run on an idle machine.
- **One shared file had to be edited: `tests/test_rebuilt_registry.py`.**
  The registry rule's promise is that a rebuild adds one file and edits
  nothing else, so sixteen can run in parallel. Three of the foundation's
  own tests encoded the *state* "nothing has been rebuilt yet" —
  `rebuilt.known()` equal to the two fixtures, and every one of the 46
  missing — so the first rebuild of the phase falsifies them whichever class
  it is. They are rewritten here to be rebuild-agnostic: `known()` must hold
  the two fixtures and nothing that is not one of the 46, and every
  catalogue name must either miss (old class stands) or resolve to a
  `Component` whose `NAME` matches and which is what the package exports.
  **Shown to still fail:** re-exporting `audioeffects.dynamics.TransientShaper`
  under the name and running the same test gives
  `AssertionError: <class 'audioeffects.dynamics.TransientShaper'> is not
  <class 'audioeffects.rebuilt.transientshaper.TransientShaper'>`. The
  sibling class-builders on this phase will conflict on this file once each;
  the resolution is to take this version, not to re-add a hand-written list.
- **The landing is three commits, not one.** The class gate asks for the
  code, the evidence file and the CHANGELOG line in a single audiocomponents
  commit; this rebuild was run station by station and committed at each, so
  `f93ec36` carries the dossier, `9a6d0bf` the class, and this file's own
  commit the evidence. Nothing is missing, but the gate's wording is not met
  literally and the phase can squash the three if it wants the letter.
- **No issue has been filed** for any of the above. The board run and the
  independent refutation are the phase's to schedule; the T1 epsilon and the
  T5 convergence are findings, not defects, and belong in the phase packet.

---

## 12. Commits

| Commit | What landed |
|---|---|
| `f93ec36` | Station A — the dossier's traits frozen, §8's three opens settled, `tools/phase2_probes/transientshaper_station_a.py` |
| `9a6d0bf` | Station B — `lib/audioeffects/rebuilt/transientshaper.py`, the README catalogue row, the CHANGELOG line |
| `ad0d053` | Station C — this file, `tests/test_cpython_effects_transientshaper.py`, the three measurement scripts, and the docstring and README amendments that carry T5's and T6's disconfirmations |
