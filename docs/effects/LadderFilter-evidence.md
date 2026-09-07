# Evidence Pack — `LadderFilter` (the Moog transistor ladder)

Written from `tools/ladderfilter_evidence.py` and
`tools/ladderfilter_state_probe.py`, both committed with this file. Every
figure below is a line of one of their runs; nothing here is recalled.

**Three rules this file is written under.** Numbers come from runs. A
measurement with no planted fault cannot be cited. §11 says what is not done,
on its own lines.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `LadderFilter` |
| Dossier | [`LadderFilter.md`](LadderFilter.md), **traits frozen at Station A, 2026-09-07, commit `8a43ef0`** — before any of this class's code was written |
| Module | `lib/audioeffects/rebuilt/ladderfilter.py` |
| Base | `_component.Component` |
| Family / phase | Filter, roadmap Phase 2 |
| Standout | four one-pole stages round a global feedback loop with an odd saturator **inside** the loop |
| Grade | **circuit** (dossier §2: Moog's patent for the topology, Stinchcombe for the derivation, Huovilainen and Stilson & Smith independently) |
| Portability tier | **audioif** — `REQUIRES = ("audioladder",)` |
| Landed in | code `df1d4b8`; this file, the CHANGELOG line and the drivers in the Station C commit (§11 names the deviation from "one commit") |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed`. The venv's `audioladder.py` is **byte-identical** to `2f6cbc3:src/cpython/audioladder.py`, and `git diff 2f6cbc3 98ae4bf -- src/shared/audioif_ladder.{c,h} src/audioladder/ src/cpython/ docs/upstream-diff.md` is **empty**, so every line citation in the dossier and in the class holds at the pin |
| Interpreters | `audiocomponents/.venv/bin/python` **CPython 3.12.3**; `cmods/bin/micropython` **MicroPython 1.28.0** (`_mpy=2822`, standard); `cmods/bin/circuitpython-effects` **CircuitPython 10.2.1** (`_mpy=2822`, coverage) |
| Library `VERSION` | 0.2.0; class `VERSION` 0.0.2 |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began: yes.** Station A closed
in commit `8a43ef0`; the class's first line was written in `df1d4b8`. **No
threshold in this pack differs from the one the dossier fixed**, and the
dossier's Tier 1 block and Tier 2 trait table have not been edited since
`8a43ef0`.

Two dossier edits were made *after* the measurements, and both record results
rather than move a bar, so they are named here rather than left for a reader
to find: **§3's Tier 3** gained a "Measured at Station C" paragraph carrying
the latency reading and saying the cost budget is still unmeasured, and
**§8 Q4** — which the dossier explicitly left for this station to close —
gained the sign of T5's peak-height move and the h3 number. The T5 ±3 dB bar
and T4's "no absolute h3 floor" are unchanged.

---

## 1. Traits

| # | Trait, as the dossier fixed it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| **T1** | Four poles; **−12.0 ± 0.5 dB at f_c**, **−3 dB at 435 ± 20 Hz**, **−23…−27 dB/octave over 4→8 kHz** | **demonstrated** | RESPONSE, 16 tones, 48 kHz cp: **−12.055 dB** at 1 kHz, **434.9 Hz**, **−24.10 dB/octave**. 44.1 kHz: **−12.058**, **434.9 Hz**, **−23.84** | class built at 1150 Hz (corner moved 15 %), bars unchanged → **RED**: level at 1 kHz −9.79 dB, corner 500.1 Hz. Clean run green | *"the corner is whatever your reference tone happens to read"* — the first run reported 446.4 Hz because `response()`'s corner is 3 dB below the **passband reference**, and at 100 Hz the ladder is already 0.173 dB down. Answer: 50 Hz added to the grid and the **absolute** −3.0103 dB crossing computed as well. Both are exported; 434.9 Hz is the absolute one, against the analytic 434.98 |
| **T2** | Passband droops as `1/(1+k)`: at k = 0,1,2,3,4 the level at 0.1·f_c is **0.00, −6.02, −9.54, −12.04, −13.98 dB ± 0.5** | **demonstrated** | RESPONSE at 0.1·f_c, read frequency-selectively, 48 kHz cp: **−0.173, −5.931, −9.444, −11.953, −13.902 dB**. Identical to three decimals at 44.1 kHz | `Passband Comp` at 1 — the droop's own negation — → **RED** on four of five rows: **−0.17, +0.09, +0.10, +0.09, +0.08**. Clean run green | *"±0.5 dB is loose enough to pass anything"* — the deltas are **−0.173** at k = 0 and **+0.078…+0.096** at k ≥ 1, which is dossier App. A's own prediction (−0.17, and +0.08…+0.09) to the second decimal, computed before the node existed. The tolerance is not doing the work |
| **T3** | **Self-oscillation at k = 4, at the cutoff, and not before**: top of travel, a tone within 3 % of f_c decaying < 3 dB in 2 s; 90 % of travel, below −40 dB within 2 s | **demonstrated** | impulse + 3 s silence, 48 kHz cp: top of travel **999.82 Hz** (0.018 % out), **+0.01 dB** over 2 s; 90 % of travel **exact zero** in the last second, **207.3 dB** below its own peak. 44.1 kHz: **999.95 Hz**, **+0.00 dB**, **208.1 dB** | `Resonance` travel capped at k = 3.9 — the old class's defect 3 — → **RED**: "nothing sustains at the top of travel". Clean run green | *"both windows read −240 dB, so the 90 % leg proves nothing"* — true of the **first** run, which compared two windows that were both on the floor and reported "0.0 dB of decay". Answer: the two positions are read differently because the trait states them differently — a settled window against a later settled window at the top, the last second against the render's own peak at 90 % |
| **T4** | The nonlinearity is **(a) bounded** (±1 dB over 2 s, THD < 15 %), **(b) odd** (evens < −40 dB re h1 and ≥ 20 dB below h3), **(c) in the loop** (h3 rises monotonically ≥ 10 dB across `Drive` 0→+24 dB) | **demonstrated** | 48 kHz cp. (a) tone 999.82 Hz, drift **0.010 dB**, THD **0.068 %**. (b) h2 **−131.11 dB**, h4 −135.47, h5 −138.68, h6 −135.05, h7 −135.10, against h3 **−63.35** — h2 is **67.8 dB** below h3. (c) h3 **−65.69 → −58.98 → −52.92 → −26.06 dB**, monotonic, **+39.62 dB** end to end | (b) `y + 0.05·y²` on the same render → **RED**, worst even **−39.17 dB**; clean **−131.11 dB**. (c) the `Drive` knob frozen at 0 dB → **RED**, h3 flat at −65.69 four times, **+0.00 dB** end to end | *"h2 at −74.5 dB is only 8.6 dB below h3, so this thing is not odd"* — that was the first run, and it was **spectral leakage**. The fundamental is the **filter's own** 999.82 Hz, which `exact_bin_size()` cannot land on a bin, and a rectangular window's skirt from a full-scale fundamental reads −74 dB two thousand bins away. Measured three ways: rectangular −74.49, hann −134.53, blackman-harris −131.11, with h3 within 0.3 dB of itself in all three. Both readings are printed by the driver so the artefact is on the record |
| **T5** | Character follows input level: at k = 3 a **20 dB input rise moves the resonant peak ≥ 3 dB** and THD rises monotonically; **below −40 dBFS in, THD < 0.5 %** | **demonstrated** | 48 kHz cp, peak read over a 9-tone grid 800–1050 Hz. Peak **+3.360 dB (−20 dBFS in) → −0.496 dB (0 dBFS in)** = **−3.857 dB**, the peak going **DOWN**. THD **0.0036 → 0.0066 → 0.0245 → 0.0537 → 0.1351 → 0.2385 → 0.3861 %**, monotonic from −26 to 0 dBFS. Below −40 dBFS in: **0.0055 %** at −40 and **0.0598 %** at −60, both under the 0.5 % bar | the frozen-`Drive` fault above is the same kind and is **RED** (a level-independent loop reads flat); and the k = 3.9 T3 fault removes the loop's oscillation | *"the 0.93 % THD you measured at −60 dBFS in is the class"* — no: the **wire** at the same level, through the same analysis, reads **0.1679 %**, three times higher. That is the 16-bit render's quantization floor and the driver now prints a wire control at every level. *"and your peak barely moved"* — the first run read the transfer **at f_c**; at k = 3 the peak is at **925 Hz**, and reading it where it is turns 1.15 dB into 3.86 dB |

**Tally: 5 demonstrated, 0 disconfirmed, 0 unmeasured.**

**Characters:** none. A diode ladder is a different circuit (dossier §3).

**Two numbers the dossier's §8 Q4 left open for this station, now measured
and recorded as the trait's real numbers — neither threshold was moved to
match:**

- **The sign of T5's peak-height move: DOWN.** The resonant peak *falls* as
  input level rises — +3.490 dB at −60 dBFS in, +3.360 at −20, −0.496 at 0.
  The saturator inside the loop reduces the effective feedback as it is
  driven harder, so the resonance loses height and the peak also walks down
  in frequency (925 → 900 → 875 → 850 Hz).
- **h3 at self-oscillation: −63.35 dB re h1**, at k = 4.2, f_c = 1 kHz,
  48 kHz, Blackman-Harris. T4 states no absolute floor and this pack does not
  invent one; the number is recorded for whoever fixes one.

**Refutation pass.** **No independent refuter ran.** Every argument in the
last column above is one this session made against its own measurement and
then answered, and four of them changed a number: T1's corner, T3's 90 %
reading, T4(b)'s window, T5's peak frequency and its quantization control.
That is a self-refutation pass, not an independent one, and the gate line
that asks for an independent one is **not met** — §11.

---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`. WIRE, TAIL, LEVEL and CLICK are **rendered
on each interpreter through `tools/render_effect.py` and analysed here**,
which is the kit spec's split. STATE drives the class rather than reading a
render, so it has its own dual-runtime file,
`tools/ladderfilter_state_probe.py`.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass⁵ | pass⁵ | pass⁵ | pass⁵ | pass⁵ | pass⁵ | pass⁵ | pass⁵ | pass⁵ |
| `mix` 0 is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node silent and stateless, the source untouched | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `deinit()` releases every node the class built, the source still renders | STATE | pass | pass¹ | pass¹ | pass | pass¹ | pass¹ | pass | pass¹ | pass¹ |
| `capabilities` names exactly what is honoured | STATE | `()` | `()` | `()` | `()` | `()` | `()` | `()` | `()` | `()` |
| Pulling `output` allocates nothing | STATE | pass | n/a² | n/a² | pass | n/a² | n/a² | pass | n/a² | n/a² |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass | — | — | pass | — | — | **pass³** | — | — |
| Every invariant also holds at `channel_count` 1 | (all) | pass⁴ | pass⁴ | pass⁴ | — | — | — | — | — | — |

**⁵ TAIL, and the one invariant this class deliberately does not hold.** The
row is green **below** self-oscillation and **red at and above it, on
purpose** — the dossier's App. I declares that boundary and this is it,
measured. `burst_silence`, 200 ms then 3 s of silence, CPython:

| Patch | k | 48 kHz | 44.1 kHz | 22.05 kHz | Residual |
|---|---|---|---|---|---|
| 0 `Wide Open` | 0.595 | **14 samples, 0.29 ms** | 13, 0.29 ms | 8, 0.36 ms | **0 LSB** |
| 4 `Growl With Drive` | 3.9 | **13662 samples, 284.62 ms** | 12552, 284.63 ms | 6289, 285.22 ms | **0 LSB** |
| 2 `Sustained Sine At Cutoff` | 4.2 | **never returns to zero** | never | never | 14300 / 14298 / 14271 LSB |

Two things this shows that a bare "pass" would not. The tail is a **time**,
not a sample count — 284.62, 284.63 and 285.22 ms at three different rates,
which is why `TAIL_SAMPLES` is `None` and not a number. And patch 2's row is
**T3 holding instead of the silence invariant**: the class says so in its
docstring, the dossier says so in App. I, and here is the measurement that
makes the claim falsifiable rather than a caveat. Everywhere below the
boundary the invariant holds to **0 LSB**, exactly, and `reset()` stops the
tone at any setting (§2's STATE row, whose probe leads with patch 2 charged).

**WIRE is exact, not near.** The render's digest at `Mix` 0 **equals the
probe's own manifest digest** — `aef0fa61` at 48 kHz stereo, `aa6aeabd` at
44.1 k, `4a36acb1` at 22.05 k, `7bbcbf39` at 48 k mono — on all three
interpreters. The dry path takes the raw input, never the driven one
(`audioif_ladder.c:294-295` reads it, `:318-319` crossfades it).

**¹ `deinit()` on the two native builds, and why this is a pass.** `Ladder`
exposes no `deinit` there (`dir()` gives `clear`, `set`, `play`,
`sample_rate`, `bits_per_sample`, `channel_count` and nothing else), so the
base class's walk finds nothing to call. It is a pass rather than a gap
because the node holds **no external resource**: its output block is inline
in the object (`src/audioladder/Ladder.h:26`,
`int16_t buffer[AUDIOIF_LADDER_FRAMES * 2]`), so releasing it *is* dropping
the reference, which `Component.deinit()` does. On all three interpreters
`effect.output` raises `RuntimeError` afterwards. On CPython the shim does
carry `deinit` and `node._deinited` is `True` after the walk.

**² Allocation.** Measured on CPython by `effect_measurements.state()` —
green, across 120 single-block pulls on a render whose digest is not the
digest of silence. **Unmeasured on the other two**: `tracemalloc` is
CPython's and a byte count from `gc.mem_free()` is a different number.

**³ Rate honesty, measured.** `Cutoff` at macro 127 asks for 18 kHz; `_hz()`
applies **18000.0 Hz** at 48 kHz and 44.1 kHz and **10804.5 Hz** at
22.05 kHz — exactly `0.49·f_s` — **with no exception raised**. Macro 0 applies
20.0 Hz at every rate. This is the dossier §7 defect 5 (`check_hz()` refusing)
not repeated.

**⁴ Mono.** The dossier §4 states a mono source gets the same filter on one
channel, per-channel state (`audioif_ladder.h:100-110`); not
stereo-by-definition. Measured: the whole Tier 1 block re-run at
`channel_count` 1 at 48 kHz, green on all three interpreters, digests
identical.

**Nodes this class enumerates with `self._own()`, in build order:** one —
`audioladder.Ladder`, `reset=True`, `deinit=True`.

**Planted faults for this block.** Every clean control is green in the same
run.

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | the dry path × 32767/32768, on `ramp_fs` | green | **RED** — 23552 of 47104 samples differ, first at frame 0 channel 0 (max 1 LSB) |
| TAIL | +1 LSB of DC held in the settled state | green | **RED** — residual 1 LSB in the last 14400 frames (bar 0); "the state never returns to zero" |
| LEVEL | 0.5 dB of hidden gain on the wet path | green | **RED** — channel 0 wet:dry RMS +0.499 dB (bar 0.050) |
| CLICK | `latency_samples` reported 256 short, **the DSP untouched** — audio digest `5ce2cc9d` both ways | green | **RED** — measured [0.0, 0.0] against a reported 256 (256.0 out, bar 1.0) |
| STATE | `reset()` made a no-op, the loop left charged at patch 4 | green | **RED** — after `reset()` and a silent source the output still reaches **11732 LSB** (bar 0) |

**The STATE fault is only a fault because the loop was charged first.** The
probe leads with patch 4 (`Growl With Drive`, k = 3.9) on CPython and patch 2
(`Sustained Sine At Cutoff`, k = 4.2, self-oscillating) on the portable file.
A reset walk that is handed nothing to clear passes on a class with no reset
at all.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, through `tools/render_effect.py` on each
interpreter. `sum(data)` is never the comparison.

```
python tools/render_effect.py LadderFilter chord <outdir> --rate 48000 --block 2048 --patch 0
```

| Probe | Rate | Ch | Block | Patch | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 2 | 2048 | 0 | `c0ac32bd` | `c0ac32bd` | `c0ac32bd` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2 | 2048 | 0 | `87fc6d09` | `87fc6d09` | `87fc6d09` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 2 | 2048 | 0 | `090163bd` | `090163bd` | `090163bd` | *(board run)* | *(board run)* |
| `chord` | 44100 | 2 | 2048 | 0 | `fec70255` | `fec70255` | `fec70255` | *(board run)* | *(board run)* |
| `chord` | 22050 | 2 | 2048 | 0 | `181a31b1` | `181a31b1` | `181a31b1` | *(board run)* | *(board run)* |
| `chord` | 48000 | 1 | 2048 | 0 | `ef78ec4d` | `ef78ec4d` | `ef78ec4d` | *(board run)* | *(board run)* |
| `impulse` | 48000 | 2 | 2048 | **2** | `6bc8588d` | `6bc8588d` | `6bc8588d` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2 | **256** | **4** | `281d889d` | `281d889d` | `281d889d` | *(board run)* | *(board run)* |

Plus §2's sixteen Tier 1 render specifications — WIRE, TAIL, LEVEL and CLICK
at four axis combinations — whose digests are printed per interpreter there
and are identical on all three. **Twenty-four render specifications, each
rendered on all three interpreters: 72 renders, 0 mismatches.**

**Patch 2 and patch 4 are in this table on purpose.** Patch 2 self-oscillates
and patch 4 drives the saturator hard: the node's own upstream note calls its
parity fixture "the most sensitive in that file" because the loop is
recursive, runs in `float` **and** is solved, so a one-ulp disagreement has
the solver's seed to grow through and nothing damps it where the loop
sustains. Those are the two renders where a float-width difference would show,
and they are byte-identical.

**Desktop agreement: yes** — CPython and desktop MicroPython render identical
bytes on every probe above.

**Board agreement:** not taken. §4, §11.

**Block-size ladder**, `chord` at 48 kHz through `--block` 256, 2048, 8192,
16384, 20000, 32768: **`c0ac32bd` at every one**. The class holds no ring and
no splitter, so this is expected rather than surprising — it is here because
`MultibandCompressor` A-M5 is the case where it was not.

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
target `effect:LadderFilter`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget (§3, Tier 3): **ESP32-P4 8 %** of one stereo block's real-time
deadline, **ESP32-S3 14 %**, **S3 on patch 6 `Ladder - lean` 7 %**.

| Board | Patch | Settings | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("LadderFilter", …)` | 846.0 | 1.182 (0.869 marginal) | 4.51 | 1472 B | **no** — 16.3 % marginal, 22.2 % total, against 8 % |
| S3 | 0 | construction defaults, `audioeffects.create("LadderFilter", …)` | 524.3 | 1.907 (1.436 marginal) | 2.80 | 1504 B | **no** — 26.9 % marginal, 35.8 % total, against 14 % |
| S3 | 6 `Ladder - lean` | — | — | — | — | — | *(not run)* |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:LadderFilter`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 8 %, S3 14 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`b5e3a1e71748a465` on the ESP32-P4 and `b5e3a1e71748a465` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is `8a36f0931d7a19e7` — it **differs**.

**Cause of the desktop/board difference — not this class, and not the
interpreter.** `cmods/bin/micropython` on the same desktop reproduces the
CPython digest exactly (checked this session on `LowPass`, `Compressor`,
`Expander` and `BandPass`), so the interpreter is ruled out. The split is in
audioif's C, and it is visible one level below this class: re-measured this
session, host and board agree byte for byte on the integer-path nodes
(`audiomixer.Mixer` `4169efd90ecf44dd`, `audiomath.Multiply`
`17a7e6961683c978`, x86 and P4 alike) and differ on every float-path node
(`audiofilters.Filter` x86 `5e74668045b152d3` / P4 `2f191df093bf29e6`;
`audiobiquad.Biquad` x86 `4f722f765d2a6cf6` / P4 `129cb858074b6f17`;
`audiodynamics.Dynamics` x86 `e9d39fe10823e8a1` / P4 `d99590c3e97d923c`;
`audioecho.FeedbackDelay` x86 `e7118d0485c800bd` / P4 `6e63708183d6d859`).
The mechanism for most of the palette is already settled in
[`../effects-cost-table.md`](../effects-cost-table.md) §7 — fused
multiply-add contraction, reproduced there by rebuilding the desktop
extension with `-mfma -ffp-contract=fast` — with `audiofilters.Filter` and
`audiodynamics.Dynamics` named as nodes that differ from *both* desktop
builds and so carry a second cause (`mp_float_t` single on the boards
against double on the CPython target; newlib against glibc in the
transcendentals). No FMA rebuild was made in this run; the citation is to
that one.

**Owed: a `" - lean"` patch.** At 26.9 % of the deadline the class is over
its ESP32-S3 budget of 14 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** the S3 `Ladder - lean` row (patch 6), and patch 4. Only construction defaults were run.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**The expensive path a board run must reach**, so the figure is not taken on
an idling filter: patch 4 `Growl With Drive` (k = 3.9, `Drive` +18 dB,
`Oversample` 2×) is the class in the state its cost is about — the solver
iterating against a loop gain near 1 with the saturator engaged. Patch 0's
`Resonance` 0.6 exercises the same per-sample path but a solver seeded closer
to its answer. Patch 6 is the same as patch 0 with the loop at 1×, which is
the lean valve the budget's third row prices.

**The dossier's budget is probably generous and is left as it stands.**
App. C's 180 cycles/sample/channel assumed a table-driven `tanh`; the node
that shipped has two multiplies and a four-pass solver. Loosening a budget by
argument is not measuring it.

---

## 5. Latency

**Reported `latency_samples` = 0.** Measured click delay against the dry path
(`Mix` 0), per channel, at patch 0, on `click_stereo`:

| Rate | Reported | Measured (integer) | Δ | ms | Sub-sample reading |
|---|---|---|---|---|---|
| 48000 | 0 | **[0.0, 0.0]** | 0 | 0.000 | [2.119, 2.119] = [0.0441, 0.0441] ms |
| 44100 | 0 | **[0.0, 0.0]** | 0 | 0.000 | [2.017, 2.017] = [0.0457, 0.0457] ms |
| 22050 | 0 | **[0.0, 0.0]** | 0 | 0.000 | [1.015, 1.015] = [0.0460, 0.0460] ms |

**The row is judged on the integer reading, and that is the kit's own rule,
not a convenience.** `effect_measurements.click`'s docstring: a minimum-phase
filter's group delay "is a real property of the class and *not* the
processing latency `latency_samples` declares", and "a class whose latency is
a pure delay reads the same both ways". This one does **not** read the same
both ways, which is the evidence that what it has is group delay and not
latency. The sub-sample figure is that group delay and is exported beside it.

Dossier latency budget: **0 samples**. **Met.**

**Every latency-adding option, each defaulting off or to its shortest.**
There are none. `Oversample` is the only option that touches the signal path's
timing at all and it adds no integer latency at either setting:

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| `Oversample` (macro 5) | **2× (on)** | **0 samples** integer (sub-sample 2.119 at 48 k, 2.017 at 44.1 k, 1.015 at 22.05 k) | **0 samples** integer with it **off** (sub-sample 1.897 / 1.760 / 0.006) | yes — "0 samples — 0.000 ms — at every setting, and there is no latency-adding option on this class" |

The sub-sample difference between the two settings — 2.119 against 1.897 at
48 kHz — is the resampler's half sample at the doubled rate, arriving as
about a fifth of a sample at the output rate. It is the class's group delay
moving, not its latency.

**Planted fault:** `latency_samples` reported 256 short with the DSP
unchanged → CLICK **RED** at 48 kHz, audio digest `5ce2cc9d` identical to the
clean run's. Result: the check fires on the report alone, which is what a
latency check has to do.

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Node option | Panel control it generalizes |
|---|---|---|---|---|---|
| 0 | Cutoff | UNIPOLAR | 20 Hz – 18 kHz, **log** | `cutoff_hz` | the Cutoff knob; exponential is the circuit's own law |
| 1 | Resonance | UNIPOLAR | k = 0 … 4.2 | `resonance` | Emphasis / Regeneration; k = 4 sits at position **0.952** |
| 2 | Drive | UNIPOLAR | 0 … +24 dB | `drive` (linear at the node) | the input level — the only warmth control the circuit has |
| 3 | Passband Comp | UNIPOLAR | 0 faithful … 1 flat | `passband_comp` | none; **defaults to 0** |
| 4 | Poles | UNIPOLAR | 1 … 4 | `poles` | the ladder's lower taps, 6/12/18/24 dB an octave |
| 5 | Oversample | TOGGLE | off / 2× | `oversample` | none; **defaults to 2×** |
| 6 | Mix | UNIPOLAR | 0 … 1 | `mix` | the contract's wire-at-zero |

Seven, against a ceiling of sixteen. The dossier's eighth, `Slew`, is dropped
with its reason in §6 there and filed as an audioif ask (Q6).

| Patch | Name | What it is for |
|---|---|---|
| 0 | `Wide Open` | the constructor's defaults on the 0-127 grid — 11.73 kHz, k 0.595 |
| 1 | `Squelch At The Knee` | 700 Hz, k 3.6, +6 dB — the sound the knob is for |
| 2 | `Sustained Sine At Cutoff` | 1 kHz, k 4.2 — **T3's boundary as a patch** |
| 3 | `Dark` | 300 Hz, k 1.5 — the ladder as a tone control |
| 4 | `Growl With Drive` | 900 Hz, k 3.9, +18 dB — **T4(c) and T5's territory**, and §4's cost patch |
| 5 | `Two Pole Soft` | 2.5 kHz, k 1.0, `Poles` 2 |
| 6 | `Ladder - lean` | patch 0 with `Oversample` off — Tier 3's S3 valve |

Patch 0 is the constructor's defaults **quantized onto the grid**, so a fresh
instance carries 12000.0 Hz and k 0.600 while `program_change(0)` snaps to
11726.77 Hz and k 0.595. `macro_position()` is unquantized on the
construction path on purpose (`_component.py:190-198`).

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change` — held by
`tests/test_component_foundation.py` for every `Component` subclass and
exercised on this class by `tests/test_rebuilt_registry.py`'s walk over
`rebuilt.known()`.

**`capabilities` = `()`.** The dossier's one-line reason, quoted: *"a filter
has no tempo-dependent behaviour and does not read the transport"*
(App. I, D10). The class contains no reference to `self._transport`.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audioladder",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Ladder` | `audioladder` | **T3, T4, T5** | The palette's `audiofilters.Filter` tracks the analytic ladder to 0.05 dB at every resonance short of oscillation (dossier App. H(ii)) — and it is **linear**: from silence it stays silent at any Q, so T3 fails at its own definition; it makes no harmonics, so T4 has nothing to measure; and its level dependence is identically zero, which is T5's own stated disconfirmation. T1 and T2 are **not** what this node is for — they are reachable on stock biquads and the dossier says so |

```
$ audiocomponents/.venv/bin/python -m unittest tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.015s

OK
```

The class enters that battery automatically — it walks `audioeffects.ALL` and
`rebuilt.known()` — so a tier claim here that `TIER` does not match is a test
failure, not a wrong sentence.

**What that test does not prove, repeated because every pack must repeat it:**
blocking a module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace. That is a gap in the
method, not in this class — and it bites this class less than most, because
this class is **audioif tier** and its claim is that it does *not* run on a
stock board.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began (`8a43ef0`
      before `df1d4b8`), and §1 lists all five traits as demonstrated.
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on `circuitpython-effects`; every Tier 2
      measurement names its rate. *(Two cells carry footnotes rather than a
      plain pass: `deinit()` on the native builds, and allocation, which is
      measured on CPython only.)*
- [x] Every demonstrated Tier 2 trait has a measurement, and that measurement
      was shown red on a planted fault of the same kind — T1 corner moved,
      T2 droop compensated away, T3 resonance capped, T4(b) an even
      nonlinearity, T4(c)/T5 the drive frozen.
- [ ] **Every demonstrated trait survived an *independent* refutation
      attempt.** Not met — the refutations in §1 are this session's own. §11.
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material — 24 render specifications × 3 interpreters = 72 renders, 0
      mismatches. The P4 and S3 columns are empty, not matched: §4, §11.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 16.3 % and S3 26.9 % of the deadline (marginal) against 8 % / 14 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz (and 22.05 kHz); the budget is met; there is no
      latency-adding option, and the docstring says so in milliseconds.
- [x] The class declares seven macros and six named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass.
- [x] The README catalogue row and the docstring describe the standout, the
      portability tier and the cost, in a musician's terms.
- [ ] **The class's code, this file and the CHANGELOG line landed in one
      commit.** Not met — the station structure put the code in `df1d4b8` and
      this file plus the CHANGELOG in the Station C commit. §11.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib audiocomponents/.venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib audiocomponents/.venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 228 tests in 30.326s

OK (skipped=1)

$ PYTHONPATH=lib audiocomponents/.venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib audiocomponents/.venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib audiocomponents/.venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.015s

OK

$ PYTHONPATH=lib audiocomponents/.venv/bin/python tests/parity/effects_library_smoke.py
46 classes, 89 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
46 classes, 89 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
46 classes, 89 patches, 0 failures

$ PYTHONPATH=lib audiocomponents/.venv/bin/python tools/ladderfilter_evidence.py all
(220 lines; every RED line in it is a planted fault, at lines 153-196)

$ PYTHONPATH=lib audiocomponents/.venv/bin/python tools/ladderfilter_state_probe.py
STATE  cpython 3.12.3           48000 Hz 2 ch  LadderFilter 0.0.2
  probe render          peak  15320 LSB  in 32 of 32 blocks  -> green
  reset() + silence     peak      0 LSB (bar 0)               -> green
  source handed back    peak  15320 LSB                       -> green
  capabilities          ()                                     -> green
  deinit()              node exposes deinit: True   _deinited True
  deinit() -> output    raises RuntimeError: True              -> green
  allocation            unmeasured on this file: tracemalloc is CPython's; see the pack
  STATE  green

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tools/ladderfilter_state_probe.py --rate 22050
STATE  micropython 1.28.0       22050 Hz 2 ch  LadderFilter 0.0.2
  probe render          peak  16536 LSB  in 32 of 32 blocks  -> green
  reset() + silence     peak      0 LSB (bar 0)               -> green
  source handed back    peak  16536 LSB                       -> green
  capabilities          ()                                     -> green
  deinit()              node exposes deinit: False  _deinited None
  deinit() -> output    raises RuntimeError: True              -> green
  allocation            unmeasured on this file: tracemalloc is CPython's; see the pack
  STATE  green

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    -X heapsize=256M tools/ladderfilter_state_probe.py --rate 44100
STATE  circuitpython 10.2.1     44100 Hz 2 ch  LadderFilter 0.0.2
  probe render          peak  15824 LSB  in 32 of 32 blocks  -> green
  reset() + silence     peak      0 LSB (bar 0)               -> green
  source handed back    peak  15824 LSB                       -> green
  capabilities          ()                                     -> green
  deinit()              node exposes deinit: False  _deinited None
  deinit() -> output    raises RuntimeError: True              -> green
  allocation            unmeasured on this file: tracemalloc is CPython's; see the pack
  STATE  green

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:LadderFilter")'
ROW	effect:LadderFilter	846.0	4.51	1.182	0.313	0.869	1472	b5e3a1e71748a465
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:LadderFilter")'   # the S3
ROW	effect:LadderFilter	524.3	2.80	1.907	0.471	1.436	1504	b5e3a1e71748a465
```

The tail table of §2 footnote 5, verbatim, from
`effect_measurements.tail()` over `burst_silence` at three patches:

```
48000 Hz patch 0          tail       14 samples (0.29 ms)  residual 0 LSB  -> green
48000 Hz patch 4 (k 3.9)  tail    13662 samples (284.62 ms)  residual 0 LSB  -> green
48000 Hz patch 2 (k 4.2)  tail   144000 samples (3000.0 ms)  residual 14300 LSB  -> RED: residual 14300 LSB in the last 14400 frames (bar 0 LSB); the state never returns to zero: no last non-zero sample, so there is no tail length to report
44100 Hz patch 0          tail       13 samples (0.29 ms)  residual 0 LSB  -> green
44100 Hz patch 4 (k 3.9)  tail    12552 samples (284.63 ms)  residual 0 LSB  -> green
44100 Hz patch 2 (k 4.2)  tail   132300 samples (3000.0 ms)  residual 14298 LSB  -> RED: ...
22050 Hz patch 0          tail        8 samples (0.36 ms)  residual 0 LSB  -> green
22050 Hz patch 4 (k 3.9)  tail     6289 samples (285.22 ms)  residual 0 LSB  -> green
22050 Hz patch 2 (k 4.2)  tail    66150 samples (3000.0 ms)  residual 14271 LSB  -> RED: ...
```

The nine clean/faulted pairs, verbatim from the `all` run:

```
  WIRE      clean
  WIRE      green -
  WIRE      fault: the dry path x 32767/32768
  WIRE      RED   23552 of 47104 samples differ, first at frame 0 channel 0 (max 1 LSB)
  TAIL      clean
  TAIL      green -
  TAIL      fault: +1 LSB of DC held in the settled state
  TAIL      RED   residual 1 LSB in the last 14400 frames (bar 0 LSB); the state never returns to zero: no last non-zero sample, so there is no tail length to report
  LEVEL     clean
  LEVEL     green -
  LEVEL     fault: 0.5 dB of hidden gain on the wet path
  LEVEL     RED   channel 0 wet:dry RMS +0.499 dB (bar 0.050 dB); channel 1 wet:dry RMS +0.499 dB (bar 0.050 dB)
  CLICK     clean (the integer reading, which is what latency_samples declares)
  CLICK     green -
  CLICK     fault: latency_samples reported 256 short, the DSP untouched (digest 5ce2cc9d both ways)
  CLICK     RED   measured [0.0, 0.0] samples against a reported 256 (256.0 samples out, bar 1.0) at 48000 Hz
  STATE     clean
  STATE     green -
  STATE     fault: reset() made a no-op, the loop left charged
  STATE     RED   after reset() and a silent source the output still reaches 11732 LSB (bar 0)
  T1        clean
    level at f_c -12.055 dB, absolute -3 dB 434.9 Hz, slope -24.10 dB/octave -> green
  T1        fault: the class built at 1150 Hz - the corner moved 15 % - with the trait's grid and bars still stated at 1 kHz
    level at 1000 Hz -9.79 dB, corner 500.1 Hz, slope -23.78  -> RED
      RED level at 1000 Hz reads -9.79 dB (bar -12.0 +- 0.5)
      RED -3 dB corner 500.1 Hz (bar 435 +- 20)
  T2        fault: Passband Comp at 1, which is the droop's own negation
    k=0 -0.17  k=1 +0.09  k=2 +0.10  k=3 +0.09  k=4 +0.08  -> RED
      RED k=1 reads +0.09 against -6.02
      RED k=2 reads +0.10 against -9.54
      RED k=3 reads +0.09 against -12.04
      RED k=4 reads +0.08 against -13.98
  T3        clean
    top of travel    macro 127.0  render peak    -7.20 dBFS  ...  decay   +0.01 dB  ...  tone 999.82 Hz
    90 % of travel   macro 114.3  render peak   -32.66 dBFS  ...  last second  -240.00 (-207.34 dB re peak)  tone -
  T3        green -
  T3        fault: the Resonance travel capped at k = 3.9 - the old class's defect 3, a filter that cannot oscillate. The same measurement, with the top of travel at macro 118.
    top of travel    macro 117.9  render peak   -32.70 dBFS  ...  last second  -240.00 (-207.30 dB re peak)  tone -
  T3        RED   nothing sustains at the top of travel
  T4(b)     fault: an even nonlinearity, y + 0.05*y^2, on the self-oscillation render
    clean    worst even harmonic  -131.11 dB re h1 -> green
    faulted  worst even harmonic   -39.17 dB re h1 -> RED
  T4(c)/T5  fault: the Drive knob frozen at 0 dB while the measurement believes it moved
    h3 [-65.69, -65.69, -65.69, -65.69]   end to end +0.00 dB -> RED
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

1. **It was not a ladder** — four `LOW_PASS` biquads in one cascade, eight
   poles, −23.94 dB at its own nominal cutoff where a ladder gives −12.04.
   **Now:** one `audioladder.Ladder`, four one-poles round a real feedback
   loop; measured **−12.055 dB** at f_c and **−24.10 dB/octave** (T1).
2. **Resonance added a peak and no droop** (`q = 0.55 + 6.0 * resonance`).
   **Now:** the droop is the node's own `1/(1+k)`; measured **0.00 → −13.90 dB**
   across k = 0…4 (T2).
3. **It could not self-oscillate** — Q bounded at `0.55 + 6.0` = 6.55, a
   finite peak. **Now:** sustains at the top of `Resonance` travel,
   **999.82 Hz**, **+0.01 dB over 2 s** (T3). The old ceiling is this pack's
   T3 planted fault, and it is red. *(The dossier's §7 defect 3 quotes
   +11.61 dB for that peak; its own Appendix B(iii) audit corrected the
   figure to **+17.42 dB** — the first reading was clipped — and §7 was not
   updated. This pack cites the corrected number. Nothing else follows from
   it: the defect is that the peak is finite, and it is worse than §7 says,
   not better.)*
4. **`resonance` had no macro** — `MACRO_LABELS = ()`. **Now:** macro 1, with
   k on the panel and k = 4 a documented position inside the travel.
5. **`check_hz()` refused instead of clamping.** **Now:** `self._hz()`
   clamps; measured at 22.05 kHz, 18 kHz asked becomes **10804.5 Hz applied,
   no exception** (§2 footnote 3).
6. **The docstring claimed what the code did not do.** **Now:** the module
   docstring says what the class is, what tier it is, what it costs, that its
   cost is unmeasured on hardware, and which invariant it deliberately does
   not hold.
7. **Inherited:** `Effect.__new__` mutated module-wide format state. **Now:**
   `_component.Component`; the format arrives with the source and
   `create()` confirms it. The class never calls `configure()`.

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 16.3 % and S3 26.9 % of the deadline (marginal)
  against 8 % / 14 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **No independent refutation pass.** The refutations in §1 are this
  session's own, made against its own measurements. Four of them changed a
  number, which is worth something, but it is not what that gate line asks
  for. What it would take: a session that did not write this class running the
  five Tier 2 measurements against the dossier's thresholds.
- **Allocation is measured on CPython only.** `tracemalloc` is CPython's;
  `tools/ladderfilter_state_probe.py` reports that leg as unmeasured on
  MicroPython and CircuitPython rather than substituting `gc.mem_free()`.
- **The code and this file are in two commits, not one.** `df1d4b8` carries
  the class; this file, the drivers and the CHANGELOG line are in the Station
  C commit. The station structure of this run is the reason; the gate line
  asks for one commit and it is not met.
- **`slew_ms` on `audioladder.Ladder` is not filed as an audioif issue.** The
  dossier's §8 Q6 records it — a cutoff glide has to run inside the node and
  Python cannot reach it — but no issue exists in the audioif repository yet.
  It needs one.
- **No stock-tier class has been shown rendering on stock ported C**, which
  the foundation already states and every pack repeats. It does not affect
  this class's own claim, which is that it needs audioif.
- **T4 states no absolute floor for h3** at self-oscillation and this pack
  does not invent one. The measured number, **−63.35 dB re h1**, is in §1 for
  whoever fixes a floor.

Nothing else is outstanding.
