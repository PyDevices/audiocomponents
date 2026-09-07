# Evidence Pack — `BandPass` (no historical standout — design grade)

Read against the class gate in the anchor repo's `docs/effects-roadmap.md`,
one section per gate item, in the gate's order. Numbers come from runs on
2026-09-07 in the worktree `ac-wt-bandpass`, branch `effects/p2-bandpass`.
A measurement nobody ran is `unmeasured`, with why.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `BandPass` |
| Dossier | [`BandPass.md`](BandPass.md), traits frozen 2026-09-07 at `4b5f8c2` |
| Module | `lib/audioeffects/rebuilt/bandpass.py` |
| Base | `_component.Component` |
| Family / phase | EQ / Filter, roadmap Phase 2 |
| Standout | none — the two-pole resonant band-pass itself, RBJ's constant 0 dB peak-gain form |
| Grade | design |
| Portability tier | **audioif** (`REQUIRES = ("audiobiquad",)`) |
| Landed in commits | dossier `4b5f8c2` (Station A), class `80791ca` (Station B), this file + the class's tests + the CHANGELOG line (Station C, subject *"BandPass evidence pack: six traits measured, one disconfirmed, no board leg"*). **Three commits, not the gate's one** — the stations were asked for one commit each, and a commit cannot carry its own hash; see §11 |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed` |
| Interpreters | `.venv/bin/python` Python 3.12.3; `cmods/bin/micropython` MicroPython v1.28.0-dirty (2026-09-07); `cmods/bin/circuitpython-effects` CircuitPython 10.2.1-dirty (2026-09-07) |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** **yes** — commit
`4b5f8c2` (Station A) precedes `80791ca` (Station B) on this branch, and the
frozen §3 table is what §1 below is read against.

---

## 1. Traits

Every trait the dossier fixed, in the dossier's numbering. All six rows are
stated at Slope = 1 section (patch 0) unless the row says otherwise, which is
the dossier's own scoping line.

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| T1 | 0 dB peak at f₀, ±0.05 dB, at every Q | **demonstrated**, over the reachable span | RESPONSE (single-bin DFT on the settled half), 48 kHz, cpython: worst \|gain\| **0.0217 dB**, at Q 32 / f₀ 100 Hz; every other cell ≤ 0.0006 dB over Q ∈ {0.5, 0.707, 2, 8, 32} × f₀ ∈ {100, 1 k, 4.8 k} Hz. Two sections at 1 kHz: ≤ 0.0001 dB for Q ∈ {0.707, 2, 8} | a `PEAKING_EQ` section at the same centre and Q, `gain_db = 1` — the shape a wrong numerator takes: **+1.0000 dB → RED**; clean run −0.0001 dB → green | *"0.1 and 100 are in the row and not in your table."* True: the class's Width knob reaches Q 0.5…32 and the node's kernel clamps Q to 0.05…60, so Q 100 is unreachable on this palette at all. Recorded as a range restriction, not a pass — see §11 |
| T2 | −3 dB points at `f₀·(√(1+1/4Q²) ∓ 1/2Q)`, difference exactly f₀/Q | **demonstrated** | RESPONSE, 48 kHz, cpython, f₀ 1 kHz. Q 0.707: predicted 517.59 / 1932.02 (BW 1414.43 = f₀/Q) measured **−3.018 / −3.039 dB**. Q 2: 780.78 / 1280.78 (BW 500.00) → **−3.021 / −3.027**. Q 8: 939.45 / 1064.45 (BW 125.00) → **−3.022 / −3.024**. Two sections, compensated: −3.019/−3.044, −3.023/−3.030, −3.024/−3.027 | width knob 10 % out: **−3.455 dB at the predicted low edge → RED** (bar −3.00 ± 0.15). And the cascade with `_CASCADE_Q = 1.0`, which is the dossier's own reciprocal error: **−6.040 dB → RED**. Clean −3.021 → green | *"the second section could be hiding a width error the first one cancels."* Answered by the two-section row above: the same predicted edges, measured through the cascade, land within 0.044 dB of −3 dB |
| T3 | Exact zeros at DC and Nyquist — a held DC offset and a ±FS alternation both settle to bit-exact zero, at every f₀ | **demonstrated** | TAIL, 48/44.1/22.05 kHz, cpython (and byte-identical on mp and cpy, §3). `dc_step` with the offset removed **while the source still supplies frames**: `dc_residual_lsb = 0` at all three rates, and 0 at f₀ ∈ {20, 80, 1 k, 16 k} Hz with Q 4. `alt_fs`: settled peak over the second half **0 LSB** | +1 LSB of stuck DC in the settled state: **RED — "residual 1 LSB in the last 6240 frames (bar 0)" and "the state never returns to zero"**; clean run tail 116 samples, residual 0 → green | *"you are reading past the end of the source, where `Filter.c` memsets to zero — A3's own trap."* Answered by construction: the `dc_step` probe holds 96 000 frames of supplied zeros after the offset is removed, and the reading is taken inside them |
| T4a | Low skirt +6.005 dB/oct fitted over f₀/8…f₀/4, f₀ 20 Hz…2 kHz | **demonstrated** | RESPONSE with a 5-point grid per octave pair, 48 kHz, cpython: **+6.006 / +6.005 / +6.006 / +6.009 dB/oct** at f₀ = 100 / 500 / 1 k / 2 k Hz (bar +6.0 ± 0.3) | the two-section cascade read against the one-section bar: **+10.987 dB/oct → RED**; clean +6.005 → green | *"a 5-point fit over one octave can hit 6 dB/oct by accident."* Answered by the fault: the same fit refuses the cascade by 5 dB/oct |
| T4b | High skirt −6.0 ± 0.3 dB/oct over 4f₀…8f₀ while f₀ ≤ 600 Hz at 48 kHz | **demonstrated**, and the boundary confirmed | RESPONSE, 48 kHz, cpython: **−6.011 / −6.043 / −6.155 / −6.221** at f₀ = 100 / 250 / 500 / 600 Hz — inside the band; **−6.305 at 700 Hz and −6.646 at 1 kHz** — outside it, which is exactly where the row says the claim stops | same fault as T4a (the cascade), which the same fit refuses | *"600 Hz is a number someone picked."* Answered by the 700 Hz and 1 kHz readings: the band is crossed between 600 and 700 Hz, as the dossier's A12 derivation said |
| T4c | `\|H(f₀/100)\|` = −37.0 ± 0.1 dB at Q 0.707, **at every f₀** | **disconfirmed** — and the cause is the prototype, not the class | Single-tone gain, 48 kHz, cpython, against RBJ's closed form at the same rate: f₀ 500 Hz **−36.994** (form −36.991), 1 kHz **−37.001** (−37.001), 2 kHz **−37.037** (−37.038), 4.8 kHz **−37.279** (−37.281), 8 kHz **−37.837** (−37.837), 16 kHz **−41.350** (−41.359) | none needed for a disconfirmation, but the same-kind check is run: the class tracks the closed form to **≤ 0.009 dB** everywhere, so the deviation cannot be the build | *"your filter is wrong at high centres."* Answered by the closed-form column: the clause's ±0.1 dB band is what fails, above about 2.5 kHz, and for the same bilinear-warp reason A12 already fixed in T4's high-skirt clause and left standing here. Recorded in the class docstring, not only here |
| T5 | Geometric symmetry about the **prewarped** centre, 0.00000 dB for r ∈ 1…8, f₀ 20 Hz…0.1·F_s | **demonstrated** to the measurement's own floor | Folded pairs, 48 kHz, cpython. \|upper − lower\|: f₀ 100 Hz — 0.00132 / 0.00140 / 0.00108 / 0.00187 dB at r = 1.5 / 2 / 4 / 8; f₀ 1 kHz — 0.00077 / 0.00153 / 0.00055 / 0.00116; f₀ 4.8 kHz — 0.00004 / 0.00069 / 0.00084 / 0.00293. Bar 0.05 dB. The linear-axis half, f₀ 1 kHz r = 8: **0.8259 dB**, against the dossier's predicted 0.824 | the fold taken about 1.1·f₀: **1.4611 dB apart → RED** (bar 0.05); clean 0.00153 → green | *"0.001 dB is not 0.00000 dB, so the row is not met."* The row's exactness is a property of the closed form; a render is int16, and 0.001–0.003 dB is the quantisation floor of a −12 dBFS tone read through a single-bin DFT. Stated as "to the measurement's floor" rather than as 0.00000 |
| T6 | Rate-honest: centre within 0.1 %, T1/T2 to their own tolerances, and the response within 0.1 dB of the closed form **at the running rate** up to 0.45·F_s | **demonstrated** | Single tones at f₀/2, f₀, 2f₀ for f₀ ∈ {100, 1 k} Hz, Q 2, at 48 000 / 44 100 / 22 050 Hz, each differenced against its own rate's closed form: worst deviation **0.002 dB** (44.1 kHz, f₀ 100 Hz, probe 200 Hz); every other cell ≤ 0.001 dB. Gain at f₀ ≤ 0.05 dB at all three rates | the same readings taken against the **48 kHz** curve at 22.05 kHz: **worst 0.2137 dB → RED** (bar 0.1) while the same renders against their own rate read 0.0011 dB → green | *"you have only shown two centres."* True — 100 Hz and 1 kHz, three probes each. The centre-does-not-move check adds a third reading at every rate; a full sweep at every rate is not run and is named in §11 |

- **demonstrated** = a measurement, that measurement shown red on a planted
  fault of the same kind, and a surviving refutation.
- **Characters:** none. The dossier's §3 says a band-pass has one behaviour,
  and the Slope toggle is a slope switch: T1, T2, T3, T5, T6 are measured
  through the cascade too and hold unchanged.

**Refutation pass.** Run by this session, 2026-09-07, against the seven rows
above — **not independent, and that is a gate item this pack does not meet**
(§11). What it went after: the Q range T1 claims but the surface cannot
reach; whether T2's cascade row could hide a compensation error; whether T3's
DC reading was A3's own past-the-end trap; whether a one-octave slope fit can
pass by accident; whether T5's "0.00000 dB" survives int16; and whether T6's
two centres are enough. Two of the six landed: T1's range is restricted and
T4c is disconfirmed outright.

---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`.

**How the mp and cpy columns were obtained, and what they are worth.** The
kit's analysis is CPython-with-numpy; the *renders* are not. Every probe below
was rendered on all three interpreters at all three rates through
`tools/render_effect.py`, and **all eighteen digests are identical across the
three** (§3). So each measurement is computed once, on the cp render, and the
mp and cpy cells say that those interpreters produced the same bytes — which
is what makes the verdict transfer, and is stated rather than implied.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass (tail 116 samples, residual **0 LSB**) | pass (same bytes) | pass (same bytes) | pass (107, **0**) | pass | pass | pass (54, **0**) | pass | pass |
| `mix` 0 is a wire, byte-identical to the source | WIRE | pass (**0 of 47 104** samples differ) | pass | pass | pass (**0 of 45 056**) | pass | pass | pass (**0 of 22 528**) | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass (rms +0.0000/+0.0000 dB) | pass | pass | pass (0.0000) | pass | pass | pass (0.0000) | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass (0 vs **0.0** samples) | pass | pass | pass (0 vs **0.0**) | pass | pass | pass (0 vs **0.0**) | pass | pass |
| `reset()` leaves every node silent and stateless, the source untouched | STATE | pass (residual **0 LSB**; source renders again) | n/a (STATE drives the class, cpython only) | n/a | pass | n/a | n/a | pass | n/a | n/a |
| `deinit()` releases every node the class built, source still rendering | STATE | pass (`['section0', 'section1']`, none live after) | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| `capabilities` names exactly what is honoured | STATE | pass (`[]`, the transport is never read) | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| Pulling `output` allocates nothing | STATE | pass (**32 bytes** over 200 single-block pulls, bar 8192) | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass (16 kHz asked, 16 000.0 Hz got) | pass | pass | pass (16 000.0) | pass | pass | pass (**8 820.0 Hz**, = 0.4·F_s) | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass (WIRE 0 differing; tail residual 0 LSB; f₀ gain <0.05 dB) | pass | pass | pass | pass | pass | pass | pass | pass |

**Mono.** The dossier's §4 says *identical filter*. Measured at all three
rates: the `mix = 0` wire is byte-identical, the burst-then-silence tail
settles to **0 LSB**, and the gain at f₀ is within 0.05 dB of 0 dB.
`tests/test_cpython_effects_bandpass.py::TierOne::
test_every_invariant_also_holds_at_one_channel`.

**Planted faults for this block**, each with its clean control beside it:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | dry path × 32767/32768, on `ramp_fs` at mix 0 | green: 0 of 16 384 differ | **RED**: `8192 of 16384 samples differ, first at frame 0 channel 0 (max 1 LSB)` |
| TAIL | +1 LSB of DC in the settled state | green: tail 116 samples, residual 0 LSB | **RED**: `residual 1 LSB in the last 6240 frames (bar 0 LSB)` and `the state never returns to zero` |
| LEVEL | +0.1 dB of hidden gain on a quiet chord | green: rms `[0.0, 0.0]` dB | **RED**: `channel 0 wet:dry RMS +0.100 dB (bar 0.050 dB)`, and channel 1 |
| CLICK | `latency_samples` reported 256 short, DSP untouched | green: measured `[0.0, 0.0]` | **RED**: `measured [0.0, 0.0] samples against a reported 256 (256.0 samples out, bar 1.0) at 48000 Hz`, and the audio digest is unchanged: `79b8300d == 79b8300d` |
| STATE | `reset()` that skips the node walk | green: residual 0 LSB | **RED**: `after reset() and a silent source the output still reaches 14748 LSB (bar 0)` |
| STATE | the first section left out of the deinit walk | green: `live_nodes_after_deinit []` | **RED**: `deinit() left ['section0'] live` |

`reset()` and `deinit()` walk the list `_component` requires the class to
enumerate with `self._own()`, so `_core`'s "whichever node happened to be
last" dependency cannot come back. Nodes enumerated by this class, in build
order: **`section0`, `section1`** — both `audiobiquad.Biquad`, `BAND_PASS`.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, per probe, per rate, per source block size.
`sum(data)` is printed by the renderer beside it and is never the comparison.

Command (one row of eighteen):

```
PYTHONPATH=lib .venv/bin/python tools/render_effect.py BandPass chord OUT --rate 48000
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 256 | `e2215e65` | `e2215e65` | `e2215e65` | *(board run)* | *(board run)* |
| `chord` | 44100 | 256 | `19f39551` | `19f39551` | `19f39551` | *(board run)* | *(board run)* |
| `chord` | 22050 | 256 | `acea4785` | `acea4785` | `acea4785` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | `075bd0ad` | `075bd0ad` | `075bd0ad` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 256 | `70f28d19` | `70f28d19` | `70f28d19` | *(board run)* | *(board run)* |
| `noise_det` | 22050 | 256 | `11565631` | `11565631` | `11565631` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | `5bc60bc1` | `5bc60bc1` | `5bc60bc1` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 256 | `6ba0e5a9` | `6ba0e5a9` | `6ba0e5a9` | *(board run)* | *(board run)* |
| `sweep_log` | 22050 | 256 | `cc1d3519` | `cc1d3519` | `cc1d3519` | *(board run)* | *(board run)* |

The Tier 1 probes, same three interpreters, same three rates, all identical:

| Probe | 48 kHz | 44.1 kHz | 22.05 kHz |
|---|---|---|---|
| `ramp_fs` at `--macro 3=0` | `aef0fa61` | `aa6aeabd` | `4a36acb1` |
| `burst_silence` | `45a29e59` | `fb1eef85` | `773c6f41` |
| `dc_step` at `--macro 0=44 --macro 1=64` | `faa00e3d` | `5e6f2b6d` | `c92d0f4d` |
| `alt_fs` | `462bb249` | `abebfe59` | `f218ca39` |
| `click_stereo` | `8da5480d` | `c5de7739` | `53738ed1` |
| `impulse` | `6d76f80d` | `56fa04f9` | `58e4ed51` |

**Desktop agreement:** **yes** — CPython, desktop MicroPython and
circuitpython-effects render identical bytes on all fifteen probe/rate
combinations above. The dossier's A9 divergence (`Filter.c:234` bypassing the
cascade at `mix <= 0.01` on the native builds while the CPython target
blends) does not arise on this class: `audiobiquad`'s kernel crossfades with
no threshold and is the same C on all three targets.

**Board agreement:** **not run.** The P4 and S3 columns stay empty until the
board leg (§4, §11).

**Block-size ladder**, `noise_det` at 48 kHz through `--block`:

```
BandPass noise_det 48000 Hz 2ch block 256   -> 192000 frames  fnv 075bd0ad  sum 98162376  audio
BandPass noise_det 48000 Hz 2ch block 8192  -> 192000 frames  fnv 075bd0ad  sum 98162376  audio
BandPass noise_det 48000 Hz 2ch block 16384 -> 192000 frames  fnv 075bd0ad  sum 98162376  audio
BandPass noise_det 48000 Hz 2ch block 20000 -> 192000 frames  fnv 075bd0ad  sum 98162376  audio
BandPass noise_det 48000 Hz 2ch block 32768 -> 192000 frames  fnv 075bd0ad  sum 98162376  audio
```

Byte-identical across the whole ladder — this class holds no ring, so
`MultibandCompressor` M5's 8192-frame Splitter trap has no analogue here.
The control beside it: two different centres on the same probe render
different digests (`tests/test_cpython_effects_bandpass.py`,
`Digests.test_two_settings_render_different_bytes`).

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
target `effect:BandPass`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: **ESP32-P4 ≤ 4 %, ESP32-S3 ≤ 13 %**, at every setting. Lean
patch expected: **no**, and there is no lean path to add — both sections are
always built, so a `" - lean"` patch would cost what patch 0 costs.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("BandPass", …)` | 1941.8 | 0.515 (0.202 marginal) | 10.36 | 2864 B | **yes** — 3.8 % marginal, 9.7 % total, against ≤ 4 % |
| S3 | 0 | construction defaults, `audioeffects.create("BandPass", …)` | 1237.2 | 0.808 (0.332 marginal) | 6.60 | 2896 B | **yes** — 6.2 % marginal, 15.2 % total, against ≤ 13 % |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:BandPass`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 ≤ 4 %, S3 ≤ 13 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`b2e883b33ad63557` on the ESP32-P4 and `b2e883b33ad63557` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is `409d7d7a402b00d0` — it **differs**.

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

**Not measured by this run:** patch 1, the two-section setting. The run measures construction defaults — patch 0 `Wide Mid`, one section.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**Desktop anchor, for the board run to be read against** (two seconds of
audio per row, `audioeffects.create("BandPass", …)`, 48 kHz stereo, against
20 833 ns of real time per frame):

```
patch 0, one section        91.2 ns/stereo frame  0.44 % of 20833 ns
patch 1, two sections       95.5 ns/stereo frame  0.46 % of 20833 ns
```

**The expensive path is reached, not idled past:** patch 1 is the two-section
setting with both sections at `mix = 1`, and every render above is non-silent
(the renderer refuses a render whose digest is the digest of silence, and
`effects_library_smoke.py` fails a class that renders below 32 LSB — both are
green for all six patches on all three interpreters).

---

## 5. Latency

Reported `latency_samples` = **0**. Measured click delay against the dry
path, per channel, `click_stereo`, integer-onset reading:

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | `[0.0, 0.0]` | 0 | 0.0000 |
| 44100 | 0 | `[0.0, 0.0]` | 0 | 0.0000 |
| 22050 | 0 | `[0.0, 0.0]` | 0 | 0.0000 |

Dossier latency budget: 0 samples / 0 ms. **Met: yes.**

**Which reading, and why.** The kit's CLICK offers an integer-onset reading
and a sub-sample one, and its own docstring says a row must name which it
wants. This row wants the integer one: `BandPass` is a minimum-phase filter,
not a pure delay, so it has **group delay** that is a property of the circuit
and not the processing latency `latency_samples` declares. The sub-sample
reading, recorded here beside the number rather than hidden: **+1.166 samples
at 48 kHz, +1.147 at 44.1 kHz, +0.970 at 22.05 kHz** at patch 0 — the group
delay of a Q 0.72 section at 983 Hz, about 24 µs.

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none — the class has no latency-adding option)* | — | 0 | — | the docstring says so in terms |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
**CLICK red at both rates**, audio digest unchanged:

```
measured [0.0, 0.0] samples against a reported 256 (256.0 samples out, bar 1.0) at 48000 Hz
audio digest unchanged: 79b8300d == 79b8300d -> True
```

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 Hz … 16 kHz, log; clamped per instance to `min(16 kHz, 0.4·F_s)` | the centre-frequency knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 32, log; `bandwidth_hz` reads it back as f₀/Q | the bandwidth/Q knob |
| 2 | Slope | TOGGLE | 1 section (default) / 2 sections | a filter bank's skirt switch |
| 3 | Mix | UNIPOLAR | 0 … 1, linear; 0 is a byte-exact wire | a dry/wet blend |

Four of the sixteen `_component` allows. The dossier's fifth macro, Trim, was
dropped at Station A on two measurements (dossier §4 and A14).

| Patch | Name | What it is for |
|---|---|---|
| 0 | Wide Mid | the constructor's defaults (1 kHz, Q 0.707) on the 0-127 grid |
| 1 | Telephone | 1 421 Hz, Q 1.21, two sections — the handset band |
| 2 | Snare Crack | 203 Hz, Q 1.98 — a snare's body, isolated |
| 3 | Presence Window | 4 072 Hz, Q 1.52 — the presence band a host can ride |
| 4 | Narrow Probe | 983 Hz, Q 23.8 — a resonant probe |
| 5 | Sub Window | 60 Hz, Q 3.03, two sections — the sub band, steep-sided |

Five named patches beyond patch 0. All six build and render non-silent on all
three interpreters (§9's smoke, `46 classes, 88 patches, 0 failures`).

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change`: held by `tools/validate_api.py`, which
walks every class in `audioeffects.ALL` and fails a class that does not do
exactly that.

**`capabilities` = `()`.** The dossier's one-line reason, quoted: *"nothing
in a band-pass is measured in beats"* — the class never reads
`self._transport()`. STATE reports `tempo_sync_observed` as **unmeasured**
(no transport digests were handed to it), which is the honest state for a
class that declares nothing: see §11.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Biquad`, `BAND_PASS` mode, ×2 | `audiobiquad` | T3, and Tier 1's *the tail reaches exact zero* | `synthio.Biquad` keeps its output memory in Q12 sample units with no dither and no leak (`audioif_biquad.h:14`), so the recursion lands on states that reproduce themselves: the dossier's A3 measures `BandPass(80 Hz, q=4)` holding −1 LSB for ever on both desktop interpreters. `audiobiquad` is float state with a 1e-20 flush (`upstream-diff.md:1953`), and A14 measures 0 LSB at every f₀/Q the surface reaches |

Test:

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.005s

OK
```

The class appears in that battery automatically — it walks `audioeffects.ALL`
and `rebuilt.known()`. Confirmed by listing its subjects:

```
BandPass audioif ('audiobiquad',)
ExampleAudioif audioif ('audioecho',)
ExampleStock stock ()
```

With `audiobiquad` blocked, `BandPass.create()` raises
`ImportError` naming the class, the module and *"stock CircuitPython board"*;
with nothing blocked it builds and renders. Both legs are in that battery.

**What that test does not prove**, and every pack repeats it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace. For this class the gap
cuts the other way from a stock-tier class's — `BandPass` *needs* the module,
so the claim under test is that it refuses cleanly without it, and a refusal
is what `sys.modules` blocking models best. What is still unproved is the
positive half on real hardware: that `audiobiquad` behaves on the P4 and S3
as it does on the desktop (§4, §11).

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured.
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on circuitpython-effects; every Tier 2
      measurement names the rate it ran at.
- [x] Every demonstrated Tier 2 trait has a measurement, and that measurement
      was shown red on a planted fault of the same kind.
- [ ] **Every demonstrated trait survived an independent refutation attempt.**
      The pass was run, and it changed two rows — but by this session, not by
      an independent refuter. **Not met** (§11).
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material (and so does circuitpython-effects); the P4 and S3 digests are
      **not taken**.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 3.8 % and S3 6.2 % of the deadline (marginal) against ≤ 4 % / ≤ 13 %: **inside budget**.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the budget is met; the class has no latency-adding option
      and the docstring says so.
- [x] The class declares a macro surface (four of sixteen) and five named
      patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests (the contract
      suite plus this class's own invariant and planted-fault module), the
      portability-tier test, the three-interpreter smoke and flake8 all pass.
      No old-surface trait tests were retired: `BandPass` had none — `grep -rn
      BandPass tests/` finds nothing.
- [ ] **The README catalogue row.** There is no per-class catalogue in this
      repository's README to add a row to (§11). The docstring carries the
      standout, the tier and the cost in a musician's terms.
- [~] **The class's code, this file and the CHANGELOG line in one commit.**
      Three commits, one per station, named in §0 — the trait freeze has to
      be provably earlier than the code for §0's first gate item to mean
      anything, and one commit would have destroyed that ordering. Deviation,
      recorded in §11.

---

## 9. Commands, verbatim

All from the worktree `/home/brad/gh/pydevices/ac-wt-bandpass`, with
`PYTHONPATH=lib` and `PY=/home/brad/gh/pydevices/audiocomponents/.venv/bin/python`.

```
$ PYTHONPATH=lib $PY -m flake8
(no output, exit 0)

$ PYTHONPATH=lib $PY -m unittest discover -s tests -p "test_*.py"
----------------------------------------------------------------------
Ran 263 tests in 34.109s
OK (skipped=1)

$ PYTHONPATH=lib $PY tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib $PY -c "import audioeffects, audioinstruments;
    from tools.validate_metadata import validate_effects, validate_instruments;
    validate_effects(audioeffects); validate_instruments(audioinstruments);
    print('validate_metadata: ok')"
validate_metadata: ok

$ PYTHONPATH=lib $PY -m unittest tests.test_cpython_effects_bandpass
----------------------------------------------------------------------
Ran 36 tests in 7.928s

OK

$ PYTHONPATH=lib $PY -m unittest tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.005s

OK

$ PYTHONPATH=lib $PY tests/parity/effects_library_smoke.py
ok   Vibrato                  patch 0   peak 11000

46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
ok   Vibrato                  patch 0   peak 11000

46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
ok   Vibrato                  patch 0   peak 11000

46 classes, 88 patches, 0 failures

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:BandPass")'
ROW	effect:BandPass	1941.8	10.36	0.515	0.313	0.202	2864	b2e883b33ad63557
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:BandPass")'   # the S3
ROW	effect:BandPass	1237.2	6.60	0.808	0.476	0.332	2896	b2e883b33ad63557
```

The class's own six patch rows in that smoke, identical on all three
interpreters:

```
ok   BandPass                 patch 0   peak 2832
ok   BandPass                 patch 1   peak 2023
ok   BandPass                 patch 2   peak 32767
ok   BandPass                 patch 3   peak 4858
ok   BandPass                 patch 4   peak 15047
ok   BandPass                 patch 5   peak 2834
```

Patch 2's 32 767 is the program-change transient, not a steady-state gain:
the smoke walks six patches on one instance without resetting between them,
so the state ringing at patch 1's 1 421 Hz centre meets patch 2's 203 Hz
coefficients. Steady state at patch 2 on the same material is peak 415.
§11 carries the measurement and the comparison against the stock palette.

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

- **No surface at all** (`eq.py:144`, `MACRO_LABELS = ()`) → four macros,
  five named patches, all four reachable from `set_macro` and
  `program_change`.
- **The width knob does not exist and cannot be made to exist** — `q` was a
  bare float on `synthio.Biquad` (`eq.py:104`) → `Width` is macro 1, live,
  and `bandwidth_hz` reads it back as the f₀/Q a panel shows.
- **`mix` accepted and then hidden** (taken `eq.py:101`, unreachable after) →
  `Mix` is macro 3, and at 0 it is a byte-exact wire (§2).
- **`set_frequency` off-contract and raising** — `_core.check_hz` raises at or
  above Nyquist (`_core.py:471-474`) → `self._hz()` plus the class's own
  `0.4·F_s` ceiling clamp; asking for 16 kHz on a 22.05 kHz graph yields
  8 820 Hz and renders (§2).
- **No tail declared** (`TAIL_SAMPLES = None`, `_core.py:141`) → `tail_samples`
  is computed from the build, `ceil(4·Q·F_s/f₀)` for one section and
  `ceil(6·Q·F_s/f₀)` for two — measured across the six patches: **140**
  samples at patch 0 (2.9 ms), 246 at patch 1, 1 874 at patch 2, 72 at
  patch 3, 4 655 at patch 4 (97 ms) and **14 438 at patch 5** (301 ms), which
  is the number a host would otherwise have had to guess for a 60 Hz Q 3
  resonator.
- **Held DC at low centres** → the tier moved to `audiobiquad` and the residual
  is 0 LSB at every f₀/Q the surface reaches (§2, T3).
- **`reset()` reached one node and reset the borrowed source through it** →
  `reset()` walks the two nodes `_own()` enumerated, tail first, and never
  names the source; STATE's third read confirms the source renders again.

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is inside its budget on both boards.**
  §4 carries the figures: P4 3.8 % and S3 6.2 % of the deadline (marginal)
  against ≤ 4 % / ≤ 13 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names.
- **The refutation pass is not independent.** It was run by the session that
  built the class. It found two things worth having (T1's range restriction,
  T4c's disconfirmation), which is evidence that it was a real pass and not
  evidence that it was a sufficient one.
- **T1's stated Q range is not fully exercisable.** The row says Q 0.1…100;
  the Width macro reaches 0.5…32 and `audioif_filter_f32.c` clamps Q to
  0.05…60, so Q 100 is unreachable on this palette at all. Measured over
  0.5…32; the ends are `unmeasured`, and no surface change would reach the
  top one.
- **T4c is disconfirmed** — `|H(f₀/100)|` leaves the row's ±0.1 dB band above
  about 2.5 kHz. The cause is the bilinear warp in RBJ's own closed form, not
  the class, and the class tracks that form to ≤ 0.009 dB. It is recorded in
  the class docstring as the template requires. **Worth an issue against the
  dossier corpus**: the trait-critic pass of 2026-09-06 fixed exactly this
  defect in T4's high-skirt clause and left it standing in this one, so the
  sibling filter seeds (`LowPass`, `HighPass`, `Notch`) likely carry it too.
- **`tempo_sync` is reported `unmeasured` by STATE**, because no transport
  digests were handed to it. The class declares `()` and never reads
  `self._transport()`, which is checkable by reading the module — but the
  positive-and-negative pair the kit wants was not rendered.
- **T6 is measured at two centres**, 100 Hz and 1 kHz, three probes each, at
  each of the three rates. A full sweep at every rate is not run.
- **There is no README catalogue row**, because this repository's README has
  no per-class effect catalogue — `README.md:48` points at
  `lib/audioeffects/` itself as the catalogue. The gate item asks for a row
  that has nowhere to go; the docstring carries what the row would say.
- **A program change that jumps the centre a long way clicks.** Measured: a
  1 421 Hz → 203 Hz jump takes the peak from 2 637 to 11 964 on the smoke's
  own material, and in the smoke's exact six-patch sequence patch 2 reaches
  full scale (32 767). The same jump on the stock palette reads 9 442, so it
  is the circuit and not the rebuild — the biquad's coefficients are
  deliberately not interpolated (`upstream-diff.md:1953`). It is in the class
  docstring. **Nothing on this palette fixes it**, and it deserves an issue
  if a host is going to automate the knob.
- **The landing is three commits, not one.** The gate asks for the code, this
  file and the CHANGELOG line in one commit; the stations ask for a commit
  each, and §0's "the trait set was frozen before the rebuild began" is only
  checkable if the dossier commit is provably earlier than the class commit.
  The three are consecutive on `effects/p2-bandpass` and nothing else is
  between them.
- **No `" - lean"` patch exists**, deliberately: both sections are always
  built, so a lean patch would cost what patch 0 costs. If the S3 misses the
  budget at the board run, the fix is a build-time option to drop the second
  section, not a patch — and that would take the Slope toggle off the live
  surface.
