# Evidence Pack — `ParametricEQ` (Pultec EQP-1A shelves, API 550A proportional-Q bells)

Written from runs on 2026-09-07 on branch `effects/p2-parametriceq`. Every
figure below carries the command that produced it and the interpreter and rate
it ran on. Section 11 says what is not done, on its own lines.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `ParametricEQ` |
| Dossier | [`ParametricEQ.md`](ParametricEQ.md), traits frozen 2026-09-07 at `f796f56` |
| Module | `lib/audioeffects/rebuilt/parametriceq.py` |
| Base | `_component.Component` |
| Family / phase | EQ, roadmap Phase 2 |
| Standout | Pultec EQP-1A (two low networks, resonant HF bell + bandwidth, HF shelf) and API 550A (proportional-Q bells, reciprocal cut) |
| Grade | literature |
| Portability tier | **audioif** (`REQUIRES = ("audiobiquad",)`) |
| Landed in commit | `077daf4` — code, tests, README row and CHANGELOG line; this file lands in the Station C commit that follows it |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed`; the venv's audioif is `v0.2.0-61-g98ae4bf`'s working tree at that pin |
| Interpreters | `audiocomponents/.venv/bin/python` CPython 3.12.3; `cmods/bin/micropython` MicroPython v1.28.0-dirty (2026-09-07); `cmods/bin/circuitpython-effects` CircuitPython 10.2.1-dirty (2026-09-07, coverage build) |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** **yes.** The five Tier 2
rows were frozen in `f796f56` ("Station A closed; trait table frozen
2026-09-07 … before a line of the rebuild was written"); the class landed in
`077daf4`, after it.

---

## 1. Traits

> **Revised by the Phase 2 gate audit, 2026-09-07.** The verdicts in the table
> below are the audited ones: every row the independent refutation pass broke
> was changed here, and the class was **not** touched. The *Gate audit* block
> at the end of this section carries the ruling and its cause per row; the
> *Refutation record* at the foot of the file carries the pass itself. Notes
> under the table that predate the pass are superseded by them — including any
> tally, any "all of them carry all three", and any sentence saying no
> refutation pass ran.

Measured by `tools/phase2_probes/parametriceq_traits.py`, which renders one
steady tone at a time through the class and through a bare wire and hands both
to `effect_measurements.response()`. Nothing in this table is computed from a
re-derivation of RBJ; every number is read off rendered audio.

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_traits.py --rate 48000
```

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation |
|---|---|---|---|---|---|
| T1 | Two low shelves on different corners; `Low Freq` 60 Hz, both at ¼ travel ⇒ ≥ +2.0 dB at 30 Hz, a minimum ≤ −1.0 dB in 100–400 Hz, flat within 0.5 dB above 1 kHz | **demonstrated** | RESPONSE, 45 tones 20 Hz–20 kHz, cpython. **48 kHz:** 30 Hz **+2.48 dB**, minimum **−4.46 dB at 154.0 Hz**, worst above 1 kHz **0.042 dB**. **44.1 kHz:** +2.47 / −4.46 at 154.0 / 0.042. **22.05 kHz:** +2.48 / −4.46 at 154.0 / 0.041 | one shared corner (`_low_atten.frequency = _low_boost.frequency`) → **RED**: minimum **+0.00 dB at 394.9 Hz**, i.e. no scoop at all, while 30 Hz still reads +2.79 dB. That is T1's own named disconfirmation and it is what the retired class builds | The thresholds are reachable only because the two dials have different tapers, so "did you tune the taper until the trait passed?" is the argument against it. Answered by exhausting the alternative: **210 linear combinations** (5 corner ratios × 6 boost shelf Qs × 7 cut shelf Qs, both dials at ¼ of a linear dB span) reach the three thresholds **zero** times. The taper is what the trait needs, not what the number needed |
| T2 | HF boost a bell, HF cut a shelf, independent selectors; boost full at 10 kHz and cut full at 5 kHz ⇒ a local maximum within ±⅓ oct of 10 kHz and a monotonic 3→5 kHz fall | **unmeasured** — REFUTED; all three clauses read green on a byte-flat wire | RESPONSE, 49 tones 1–20 kHz, cpython. **48 kHz:** local maximum **−5.16 dB at 10066 Hz (0.010 oct off)**; 3→5 kHz falls **−2.46 → −6.47 dB, monotonic**; that maximum moves **0.000 oct** when the atten selector goes 5 → 20 kHz. **44.1 kHz:** −5.28 dB at 10066 Hz (0.010 oct), −2.48 → −6.61 dB monotonic, 0.000 oct. **22.05 kHz: unmeasured**, see below | HF boost built as a `HIGH_SHELF` (`_high_boost.mode`) → **RED**: nearest local maximum **15582 Hz, 0.640 oct off** at 48 kHz (14639 Hz, 0.550 oct at 44.1 kHz). "The HF boost is a shelf, not a bell" is T2's own first disconfirmation | The measurement's own first version read the **global** maximum of the curve and called T2 missed on a build that meets it: with the attenuator at full cut the whole top of the band sits 20 dB down, so the loudest point of a 1–20 kHz grid is its low end whichever shape the boost has. Refuted by the shelf fault, which was *also* "red" under the global read — for the wrong reason. The local-maximum read separates them, and the comment in `parametriceq_traits.py:local_maximum_near` records it |
| T3 | Bandwidth changes peak gain, not just width: at full boost, sharp minus broad is +6…+12 dB and the −3 dB width at sharp is ≤ half broad's | **disconfirmed above −16 dBFS** — REFUTED | RESPONSE, 61 tones, cpython. **48 kHz:** sharp **+17.82 dB**, broad **+9.00 dB**, difference **+8.82 dB**; −3 dB width **0.231 oct** sharp against **1.441 oct** broad (16 % of it). **44.1 kHz:** +17.98 / +9.00 / **+8.98 dB**; 0.221 oct against 1.324 oct. **22.05 kHz: unmeasured**, see below | a constant-gain bandwidth knob (`_high_boost.gain_db = 9.0` at the sharp setting) → **RED**: difference **−0.05 dB** at 48 kHz, **−0.01 dB** at 44.1 kHz. T3 names "under 3 dB, the shape every constant-gain Q knob has" as its disconfirmation | The gain half is S2's measured 9 dB and the class hits 8.8–9.0, so the argument is against the **width** half, which the dossier itself marks low-confidence and ours. It is a design target, not a fact about the pedal, and §11 keeps it named as such. Nothing here claims a source for the 0.5/2.5 Q pair |
| T4 | Proportional Q: a 1 kHz bell at +2/+6/+12 dB holds its first +1 dB crossing within 5 % while mid-gain bandwidth falls ≥ 3× | **crossing clause unmeasured (REFUTED); bandwidth-ratio clause demonstrated** | RESPONSE, 121 tones 200 Hz–8 kHz, cpython. **48 kHz:** crossings **2299.4 / 2299.8 / 2300.0 Hz**, spread **0.02 %**; bandwidths **2.410 / 1.149 / 0.715 oct**, ratio **3.369×**. **44.1 kHz:** 2296.7 / 2297.3 / 2297.4 Hz, 0.03 %, 2.408 / 1.149 / 0.715, **3.369×**. **22.05 kHz:** 2249.0 / 2249.4 / 2249.5 Hz, 0.02 %, 2.372 / 1.136 / 0.707, **3.353×** | constant Q, reached through the class's own `Q Law` toggle (`set_macro(14, 127)`) → **RED**: crossings **1412.6 / 2961.5 Hz**, spread **109.65 %** at 48 kHz (109.27 % at 44.1 kHz, 102.71 % at 22.05 kHz) against T4's 5 % bar | "The law was fitted to the trait" — it was not: the law is derived in the dossier's App. A from holding a fixed skirt level, and its one free constant is the skirt, which was chosen **against T4's threshold** and is recorded in §8 Q2 with the two settings that fail it (0.1 dB → 18.0 %, 0.5 dB → 11.6 %). A law fitted to the trait would pass at every skirt |
| T5 | Cut is the exact reciprocal of boost: at G = 6, 12 and 16 dB the product of the +G and −G responses is unity within 0.1 dB, 20 Hz–20 kHz | **disconfirmed above −16 dBFS** — REFUTED | RESPONSE, 61 tones 20 Hz–20 kHz, cpython. **48 kHz:** max \|sum\| **0.0006 / 0.0002 / 0.0005 dB**. **44.1 kHz:** 0.0001 / 0.0003 / 0.0004 dB. **22.05 kHz:** 0.0002 / 0.0004 / 0.0006 dB. Three orders of magnitude under the bar | a signed-gain Q law (the cut's Q halved) → **RED**: max \|sum\| **3.5126 dB at 710 Hz**, while the **peak** error is only **0.0345 dB**. That is the sly failure T5 names, reproduced | The margin is so wide it invites "the measurement is not measuring anything". Answered by the fault above, which moves the same reading by 3.5 dB on the same grid with the same code path; and by the mechanism, which is exact rather than approximate — at gain −G the RBJ peaking numerator and denominator swap, so the product is 1 by construction **provided the Q is the same**, which is precisely what the fault breaks |

- **T2 and T3 at 22.05 kHz are `unmeasured`**, and the reason is the dossier's
  own, stated before the run (App. I): at that rate the 10 kHz bell and the
  16 kHz shelf do not exist — `self._hz()` clamps every corner to 10804.5 Hz —
  so a trait defined at 10 kHz has nothing to measure. What *is* measured at
  22.05 kHz is that the clamp happens and never refuses (§2, RATE row).
- **Characters:** none. The `Q Law` toggle is an option, not a character; the
  table is stated at its default (proportional) and at the default
  `Bandwidth` of 5, as the dossier's §3 says.

**Refutation pass.** **Not independent** — one session ran the build and the
measurements. What is recorded per trait above is this session's own
refutation: an exhaustive counter-search for T1, a measurement that was wrong
and had to be caught for T2, the skirt decision made against the threshold for
T4, and the mechanism plus its fault for T5. An independent pass is named in
§11 as not done.


### Gate audit — the refutation pass's verdicts, ruled on (2026-09-07)

Ruled by the Phase 2 gate auditor against the **Refutation record** at the
foot of this file. Where a refutation stands the verdict above was changed
and the class was **not** touched; where the auditor re-ran a figure itself
the run is named. The roadmap's class-gate rule is the test applied: a
*demonstrated* trait needs a measurement, that measurement shown red on a
planted fault of the same kind, **and** a surviving refutation.

| Row | Ruling | Cause recorded, and the auditor's check |
|---|---|---|
| T2 | **refutation stands** → unmeasured | All three clauses read green on a byte-flat wire: at construction defaults, `max abs(dB)` over the 1–20 kHz grid is **0.000000** and the row still reports a local maximum at 10 066 Hz, 0.010 oct off the bar's 0.333, monotone 3→5 kHz, peak moving 0.000 oct. Auditor's check: `tools/phase2_probes/parametriceq_traits.py:99` marks index *i* a maximum on `db[i] >= db[i-1] and db[i] >= db[i+1]`, so on a plateau **every** interior point qualifies and the routine returns the one nearest 10 kHz. The check separates a bell from a slope, never a bell from absence. §1's refutation column claims the opposite. |
| T3 | **refutation stands** → disconfirmed above −16 dBFS | T3 fixes the settings and not the probe level, and every section writes int16 and clips there (dossier §4). Same class, same settings: **−16 dBFS → +7.95 dB**, −14 → +6.43, −12 → **+4.70**, −10 → **+2.85**, −6 → **+0.74** — at −10 dBFS and below the reading is inside T3's own named disconfirmation ("under 3 dB, the shape every constant-gain Q knob has") and indistinguishable from the planted constant-gain fault at −0.05 dB. |
| T4 (crossing) | **refutation stands** → unmeasured | The 0.02 % spread is the law reading back its own free constant. Auditor's check: `sed -n '76p' lib/audioeffects/rebuilt/parametriceq.py` → `SKIRT_DB = 1.0`, and the law holds the response at exactly that level fixed across gains while T4 measures the +1 dB crossing. Read off the *same three rendered curves* at neighbouring levels: **+0.50 dB → 14.73 %, +0.75 → 7.33 %, +1.00 → 0.02 %, +1.25 → 8.05 %, +1.50 → 18.13 %, +1.75 → 32.60 %** — a knife edge 0.25 dB wide, centred on the constant. The bandwidth-ratio half (3.369×, bar 3×) is a genuine prediction and stands. |
| T5 | **refutation stands** → disconfirmed above −16 dBFS | T5 names no level. Same class, same G = 16 bell: **−16 dBFS → 0.0005 dB**, −14 → **0.9942**, −12 → **2.5382**, −10 → **4.2852**, −6 → **8.0459 dB** against a 0.1 dB bar — up to 80×; at −10 dBFS, G = 12 already reads 0.9960. The "product is 1 by construction" defence is a small-signal argument and the chain is not linear: each section clips to int16. Secondarily, a flat build reads 0.0000 dB and passes, so T5 alone cannot tell a reciprocal bell from no bell. |

T1 survives at all three rates and over −40…−6 dBFS.

**Rule applied to the two non-`disconfirmed` outcomes.** A refutation that
shows the class failing its own bar makes the row **disconfirmed**. A
refutation that shows the *demonstration* invalid — a fault that cannot fire,
a reading that is green on a bypass, a bar that was never asserted — leaves no
number that tests the trait, so the row becomes **unmeasured**, on this pack's
own precedent for a measurement that "produced a number that does not test the
claim". Neither outcome is a licence to edit the class.


---

## 2. Tier 1 invariants

The kit is CPython with numpy by design, so it cannot answer "green on CPython
**and** MicroPython at three rates, and on the patched CircuitPython build".
`tools/phase2_probes/parametriceq_tier1.py` does, in the standard library
only, and it is the only thing in this repository that does. It runs each
invariant twice — once clean, once with `--faults` — so no cell below is a
check that has never been shown able to fail.

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_tier1.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tools/phase2_probes/parametriceq_tier1.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      tools/phase2_probes/parametriceq_tier1.py
```

Each ran all three rates at `channel_count` 2 **and** 1 — 54 checks per
interpreter — and each ended `0 failures`.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass, 37696 | pass, 37696 | pass, 37696 | pass, 32832 | pass, 32832 | pass, 32832 | pass, 18240 | pass, 18240 | pass, 18240 |
| Patch 0 is a wire, byte-identical to the source | WIRE | pass, 0/16384 | pass, 0/16384 | pass, 0/16384 | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path | LEVEL | pass, +0.0000 dB | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass, 0 = 0 | pass | pass | pass, 0 = 0 | pass | pass | pass | pass | pass |
| `reset()` leaves every node the class built silent and stateless | STATE | pass, 0 LSB | pass | pass | pass | pass | pass | pass | pass | pass |
| `deinit()` releases every node and the source still renders | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `capabilities` names exactly what is honoured (`()`, transport never read) | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Pulling `output` allocates nothing | STATE | **601 bytes / 200 pulls** (bar 8192) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RATE | pass, 20000 ≤ 23520 | pass | pass | pass, 20000 ≤ 21609 | pass | pass | **pass, clamped to 10804.5** | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass | pass | pass | pass | pass | pass | pass | pass | pass |

The allocation row is `effect_measurements.state()`'s and is CPython-only:
`tracemalloc` does not exist on the other two. Its full reading:

```
STATE passed: True red: []
  reset_residual_lsb       0
  alloc_growth_bytes       601
  alloc_pulls              200
  capabilities             []
  live_nodes_after_deinit  []
  nodes                    ['low_atten', 'high_atten', 'bell1', 'bell2', 'bell3', 'low_boost', 'high_boost', 'output']
  probe_fnv1a              0daf70fd
  resumed                  True
```

**Mono.** The dossier's §4 says a mono source gets the same curve on one
channel — this class is not stereo by definition. Measured: every row above at
`channel_count` 1, on all three interpreters at all three rates, and the WIRE
row compares 8192 bytes rather than 16384 because that is the whole of a mono
render. `audiobiquad.Biquad` keeps per-channel state, so the stereo case is
two independent copies of the mono one.

**Planted faults for this block**, from the same file under `--faults`. All
three interpreters printed `planted-fault run: 0 faults failed to plant`.

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | no `FLAT_DB` floor: 64/127 on a ±16 dB bipolar macro asks for 0.126 dB and the section runs | 0 differing bytes | **RED, 8348 of 16384 bytes differ** |
| LEVEL | output trim nudged off centre | +0.0000 dB | **RED, +1.2284 dB** |
| CLICK | `latency_samples` reported 256 away from the truth, DSP unchanged | reported 0, measured 0 | **RED, reported 256, measured 0** |
| TAIL | a held ±1 LSB in the settled state (the audioif#23 shape) | 37696 frames | **RED, never reached zero** |
| STATE | `reset()` skipped entirely — the walk not taken | 0 LSB with a silent source | **RED, 7128 LSB** |

The STATE fault is worth its own line, because the first version of it was not
a fault at all: it re-armed a section **after** `reset()`, and a cleared
section fed silence outputs silence whatever its coefficients say, so the
check passed on a build that never resets. Skipping the walk is what "a node
the walk did not clear" actually looks like. The comment at
`parametriceq_tier1.py`'s STATE block records it.

The second Tier 1 fault lives in
`tests/test_cpython_effects_parametriceq.py::TailTest`: it builds the same
20 Hz/+16 dB section on the **ported** `synthio.Biquad` in an
`audiofilters.Filter` and requires it to *never* reach zero. That is
audioif#23 reproduced rather than cited, and it is the reason this class's
tier is audioif.

Nodes enumerated by this class, in build order: `low_atten`, `high_atten`,
`bell1`, `bell2`, `bell3`, `low_boost`, `high_boost`, `output`. `reset()` and
`deinit()` walk that list in reverse.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, `tools/render_effect.py`, patch 3
("Broad Warm Tilt" — a patch with five live sections, so the digest is of the
class working rather than of a wire), block 256, 2 channels.

```
$ PYTHONPATH=lib .venv/bin/python tools/render_effect.py ParametricEQ chord out --rate 48000 --patch 3
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tools/render_effect.py ParametricEQ chord out --rate 48000 --patch 3
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 256 | `5e6cf8e1` | `5e6cf8e1` | *(not run — heap)* | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | `1e3a278d` | `1e3a278d` | *(not run — heap)* | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | `d46e340d` | `d46e340d` | *(not run — heap)* | *(board run)* | *(board run)* |
| `chord` | 44100 | 256 | `3ccb3afd` | `3ccb3afd` | *(not run — heap)* | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 256 | `fd86c705` | `fd86c705` | *(not run — heap)* | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 256 | `f1fe3395` | `f1fe3395` | *(not run — heap)* | *(board run)* | *(board run)* |
| `ramp_fs` | 48000 | 256 | `f4c719e1` | `f4c719e1` | **`f4c719e1`** | *(board run)* | *(board run)* |
| `click_stereo` | 48000 | 256 | `0ede9ac1` | `0ede9ac1` | *(not run — heap)* | *(board run)* | *(board run)* |
| `burst_silence` | 48000 | 256 | `0128cc3d` | `0128cc3d` | *(not run — heap)* | *(board run)* | *(board run)* |

**Desktop agreement: yes.** CPython and desktop MicroPython render identical
bytes on every probe at both rates — nine of nine, all four values matching to
the digit.

**The circuitpython-effects column, and why the cause is not the class.**
`render_effect.probe_source` prefers `audiocore.WaveFile`, which streams. The
desktop CircuitPython build refuses it — `TypeError: file must be a file
opened in byte mode`, which `render_effect.py`'s own docstring already records
— so it takes the `RawSample` fallback and reads the whole probe into the
heap, and that heap will not hold a three-second stereo probe:
`MemoryError: memory allocation failed, allocating 576001 bytes` at
`render_effect.py:319`. On the one committed probe small enough to fit,
`ramp_fs` at 23552 frames, **the digest is identical to the other two**. That
is a renderer-plus-interpreter limit, measured, and it is separately confirmed
by §2, where the same interpreter runs every Tier 1 invariant on this class at
all three rates and agrees on every number including the tail frame counts.

**Build against build.** T3's is the pair that matters — the same class at
`Bandwidth` 0 and 10 — and it is exported as the two peak gains and the two
−3 dB widths in §1, not as digests.

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
target `effect:ParametricEQ`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: ESP32-P4 **26 %** of one stereo block's real-time deadline,
ESP32-S3 **43 %**, for the eight sections this class always builds. Lean patch
expected: **no** — a patch cannot change how many nodes exist.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("ParametricEQ", …)` | 892.4 | 1.121 (0.808 marginal) | 4.76 | 10 KB | **yes** — 15.2 % marginal, 21.0 % total, against 26 % |
| S3 | 0 | construction defaults, `audioeffects.create("ParametricEQ", …)` | 549.1 | 1.821 (1.350 marginal) | 2.93 | 10 KB | **yes** — 25.3 % marginal, 34.1 % total, against 43 % |
| P4 | 3 | — | — | — | — | — | *(not run — the run measured construction defaults)* |
| S3 | 3 | — | — | — | — | — | *(not run — the run measured construction defaults)* |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:ParametricEQ`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 26 %, S3 43 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`4169efd90ecf44dd` on the ESP32-P4 and `4169efd90ecf44dd` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is the **same value**.

It is also the bare probe's own digest (`4169efd90ecf44dd`): at construction
defaults (patch 0 `Flat`) this class hands the probe back unchanged. The
CPU figure above is the built graph running — every node is pulled every
block — but **the digest is not a check on the audio**, and a board run at
a working patch is still owed.

**Not measured by this run:** patch 3 `Broad Warm Tilt`, which is the patch the table above asked for. The run measures construction defaults — patch 0 `Flat`. The eight sections are built and run either way.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


Two things the board run must carry, both from the dossier's Tier 3: the
budget's arithmetic counts the **fixed-point** kernel (76 instructions/sample
on Cortex-M4/M7, `audioif/docs/upstream-diff.md:1172`) and this class runs the
**float** kernel, for which no instruction count exists on either port; and
the eight sections are eight nodes with eight block pulls where the arithmetic
assumed one `Filter` node holding a cascade. Patch 3 is the right subject
because five of its eight sections are live.

---

## 5. Latency

Reported `latency_samples` = **0**.

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0 | 0 | 0.000 |
| 44100 | 0 | 0 | 0 | 0.000 |
| 22050 | 0 | 0 | 0 | 0.000 |

Measured by the CLICK row of `parametriceq_tier1.py` — a click at frame 256
through the class against the same click through a wire — on all three
interpreters, at `channel_count` 2 and 1. Dossier latency budget: **zero
samples at every macro setting and every rate**. Met: **yes**.

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none)* | — | — | — | the docstring says so in as many words: "**Latency: zero samples, at every setting and every rate.** … no option on this class adds a lookahead, a partition or a window, so there is no latency-adding option to default off" |

Planted fault: `latency_samples` reported 256 away from the truth with the DSP
unchanged → CLICK **red at all three rates on all three interpreters**
("reported 256, measured 0"), and the audio digest is unchanged because the
fault is in the report, not the path.

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Low Freq | UNIPOLAR | 20–200 Hz, log | LOW FREQUENCY selector |
| 1 | Low Boost | UNIPOLAR | dial 0–10 → 0…+16 dB as `16·√(d/10)` | BOOST |
| 2 | Low Atten | UNIPOLAR | dial 0–10 → 0…−20 dB, linear | ATTEN |
| 3 | Bell 1 Freq | UNIPOLAR | 20 Hz–20 kHz, log | 550A band frequency switch |
| 4 | Bell 1 Gain | BIPOLAR | ±16 dB | 550A band gain |
| 5 | Bell 2 Freq | UNIPOLAR | 20 Hz–20 kHz, log | 550A band frequency switch |
| 6 | Bell 2 Gain | BIPOLAR | ±16 dB | 550A band gain |
| 7 | Bell 3 Freq | UNIPOLAR | 20 Hz–20 kHz, log | 550A band frequency switch |
| 8 | Bell 3 Gain | BIPOLAR | ±16 dB | 550A band gain |
| 9 | Bandwidth | UNIPOLAR | dial 0–10, broad → sharp | BANDWIDTH |
| 10 | High Freq | UNIPOLAR | 3–16 kHz, log | HIGH FREQUENCY selector |
| 11 | High Boost | UNIPOLAR | dial 0–10 → 0…+9 dB broad, 0…+18 dB sharp | HF BOOST |
| 12 | Atten Freq | UNIPOLAR | 5–20 kHz log, stepped to 5/10/20 kHz | ATTEN SEL |
| 13 | High Atten | UNIPOLAR | dial 0–10 → 0…−20 dB, linear | HF ATTEN |
| 14 | Q Law | TOGGLE | proportional \| constant (one octave, Q 1.4142) | none — the S3/S5 axis |
| 15 | Output | BIPOLAR | ±12 dB | the make-up amplifier |

Sixteen exactly; `_component` refuses a seventeenth at construction. The
EQP-1A's three-position ATTEN SEL is folded into macro 12 by quantizing a log
span onto the panel's own three positions rather than by spending a second
macro on it.

| Patch | Name | What it is for |
|---|---|---|
| 0 | Flat | the constructor's defaults on the 0–127 grid; every section under the 0.2 dB floor, so it is a wire |
| 1 | Low Lift And Clear | T1's pair, both low dials at 2.5 — the setting S2 measured |
| 2 | Air Above Ten | the HF bell at 10 kHz, mid bandwidth |
| 3 | Broad Warm Tilt | low boost, broad top, a little HF attenuation — five live sections, which is why §3 and §4 digest this one |
| 4 | Sharp Presence Bell | a 3 kHz bell at +8 dB with the bandwidth pot at sharp |
| 5 | Rumble Trim And Top Trim | low attenuation at 40 Hz and HF attenuation together |
| 6 | Wide Gentle Smile | low lift, top lift, a shallow 800 Hz dip |

`patch_index` is 0 on a fresh instance, `None` after any macro move and the
patch's index after `program_change`: `tests/test_cpython_effects_library.py`
holds that over `audioeffects.ALL`, and
`tests/test_cpython_effects_parametriceq.py::SurfaceTest` pins the fresh-instance
half for this class.

**`capabilities` = `()`.** The dossier's one-line reason: an equaliser has no
tempo-dependent behaviour and the class never reads `self._transport()`. Shown
rather than asserted — `SurfaceTest::test_the_transport_is_never_read` and the
Tier 1 STATE row both hand the class a transport callable that raises, then
walk all seven patches and pull the output.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Biquad` × 8 (LOW_SHELF ×2, PEAKING_EQ ×4, HIGH_SHELF ×2) | `audiobiquad` | every one of T1–T5, and the Tier 1 tail | The ported `synthio.Biquad` keeps its output memory in Q12 sample units and rounds to nearest with no dither and no leak, so the recursion has fixed points. At this class's own useful settings it parks on them and holds: a 20 Hz/+10 dB low shelf on ±32 LSB, the +16 dB edge of the span on −45 LSB, a 31.25 Hz bell on +7 LSB, for three seconds of silence (dossier App. B). `audiobiquad`'s state is float and anything under 1e-20 is written as exact zero, so the tail arrives |

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.073s

OK
```

The class enters that battery automatically — it walks `audioeffects.ALL` and
`rebuilt.known()` — so `test_audioif_tier_classes_raise_a_clear_import_error`
holds this class to raising a clear `ImportError` naming `ParametricEQ`,
`audiobiquad` and "stock CircuitPython board" when the module is blocked, and
`test_control_the_same_audioif_classes_build_when_nothing_is_blocked` holds it
to building when it is not.

**What that test does not prove**, and every pack repeats it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class has
not been shown rendering on a stock CircuitPython build of the ported C. For
*this* class the gap is narrower than usual — it is audioif-tier, so its claim
is that it refuses cleanly on a stock board, not that it runs there — but the
refusal itself has still only been seen in a blocked-import substitute, never
on a board.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began (`f796f56`
      before `077daf4`), and §1 lists every trait as demonstrated,
      disconfirmed or unmeasured. Five demonstrated; T2 and T3 additionally
      `unmeasured` at 22.05 kHz with the dossier's own pre-stated reason.
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz **and** on `circuitpython-effects`, at
      `channel_count` 2 and 1; every Tier 2 measurement names its rate.
- [x] Every demonstrated Tier 2 trait has a measurement, and that measurement
      was shown red on a planted fault of the same kind.
- [ ] **Every demonstrated trait survived an *independent* refutation
      attempt.** Not met: the refutations in §1 are this session's own. See
      §11.
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material. The `circuitpython-effects` column carries a recorded cause
      that is not the class (§3), and the P4/S3 legs are not taken.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 15.2 % and S3 25.3 % of the deadline (marginal) against 26 % / 43 %: **inside budget**.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz and
      44.1 kHz (and at 22.05 kHz); the budget of zero is met; there is no
      latency-adding option, and the docstring says so.
- [x] Sixteen macros and six named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the portability-tier test, this
      class's own invariant and planted-fault tests, the three-interpreter
      smoke and flake8 all pass — §9. The old-surface trait test was retired
      in the same commit as the code.
- [x] The README catalogue row and the docstring describe the standout, the
      portability tier and the cost in a musician's terms
      (`lib/audioeffects/README.md:86`).
- [ ] **The class's code, this file and the CHANGELOG line landed in one
      commit.** Not met as written: the code, tests, README row and CHANGELOG
      line landed in `077daf4` and this file lands in the Station C commit
      after it, because it is written from runs against `077daf4`.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
----------------------------------------------------------------------
Ran 240 tests in 20.838s

OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.073s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_parametriceq
..............
----------------------------------------------------------------------
Ran 14 tests in 3.899s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_dynamics_eq
............
----------------------------------------------------------------------
Ran 12 tests in 65.788s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 7700
ok   Vibrato                  patch 0   peak 11000

46 classes, 89 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 89 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 89 patches, 0 failures

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_tier1.py
  ... 54 checks over three rates and both channel counts ...
0 failures

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_tier1.py --faults
planted-fault run: 0 faults failed to plant

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tools/phase2_probes/parametriceq_tier1.py
0 failures
$ MICROPYPATH=... ../cmods/bin/micropython tools/phase2_probes/parametriceq_tier1.py --faults
planted-fault run: 0 faults failed to plant

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      tools/phase2_probes/parametriceq_tier1.py
0 failures
$ MICROPYPATH=... ../cmods/bin/circuitpython-effects tools/phase2_probes/parametriceq_tier1.py --faults
planted-fault run: 0 faults failed to plant

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_traits.py --rate 48000
T1   demonstrated   30 Hz +2.48 dB (bar +2.0) - minimum -4.46 dB at 154.0 Hz (bar -1.0 in 100-400) - worst above 1 kHz 0.042 dB (bar 0.5)
T1   fault RED      one shared corner: minimum +0.00 dB at 394.9 Hz, 30 Hz +2.79 dB
T2   demonstrated   local maximum -5.16 dB at 10066 Hz (0.010 oct from 10 kHz, bar 0.333) - 3->5 kHz monotonic fall True (-2.46 -> -6.47 dB) - that maximum moves 0.000 oct when the atten selector goes 5 -> 20 kHz
T2   fault RED      HF boost built as a shelf: nearest local maximum -5.09 dB at 15582 Hz (0.640 oct off)
T3   demonstrated   sharp +17.82 dB, broad +9.00 dB, difference +8.82 dB (bar 6-12) - -3 dB width 0.231 oct sharp against 1.441 oct broad (bar half)
T3   fault RED      constant-gain bandwidth: difference -0.05 dB
T4   demonstrated   +1 dB crossings ['2299.4', '2299.8', '2300.0'] Hz (spread 0.02 %, bar 5) - mid-gain bandwidth ['2.410', '1.149', '0.715'] oct, +2 -> +12 ratio 3.369x (bar 3)
T4   fault RED      constant Q: crossings ['1412.6', '2961.5'] Hz, spread 109.65 %
T5   demonstrated   max |sum| 0.0006 dB at 2000 Hz (G=6), 0.0002 dB at 1262 Hz (G=12), 0.0005 dB at 20000 Hz (G=16)
T5   fault RED      signed-gain Q law: max |sum| 3.5126 dB at 710 Hz, and only 0.0345 dB at the peak - which is what makes it sly

0 of 10 results off

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_traits.py --rate 44100
0 of 10 results off
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_traits.py --rate 22050 --traits T1,T4,T5
0 of 6 results off

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:ParametricEQ")'
ROW	effect:ParametricEQ	892.4	4.76	1.121	0.313	0.808	10592	4169efd90ecf44dd
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:ParametricEQ")'   # the S3
ROW	effect:ParametricEQ	549.1	2.93	1.821	0.471	1.350	10624	4169efd90ecf44dd
```

240 tests against the foundation's 227: the thirteen new ones are
`tests/test_cpython_effects_parametriceq.py`'s fourteen minus the one
old-surface trait test retired from
`tests/test_cpython_effects_dynamics_eq.py`.

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

1. **No surface at all** (`eq.py:40`, `:42`) → sixteen macros and seven
   patches, §6.
2. **Both shelves forced to Q 0.707 from one `low_shelf` argument at one
   frequency** (`:54`) → two `LOW_SHELF` sections on corners a fixed 5:1 apart
   with independent dials, which is what makes T1 measurable at all.
3. **`check_hz()` refuses instead of clamping** (`:48`, `:54`;
   `_core.py:471-474`) → `self._hz()` clamps to 0.98·Nyquist and never raises;
   measured at 22.05 kHz, where a 16 kHz `High Freq` and a 20 kHz `Atten Freq`
   both become 10804.5 Hz and the class still renders (§2, RATE row).
4. **Q an argument, not a law** (`:47-49`) → `proportional_q()`, derived from
   the dossier's App. A and reading the **magnitude** of the gain, which is
   what T4 and T5 measure.
5. **The empty-EQ passthrough returns the source itself** (`:59-60`), so
   `reset()` and `deinit()` behaved differently on the two paths → there is
   one path: eight owned nodes always, and a flat section is `mix = 0` rather
   than an absent one. `reset()` and `deinit()` walk the enumerated list.
6. **Constructing an effect mutates module-wide state** (`_core.py:149-152`)
   → `_component.Component` takes the format from the source it is handed and
   `configure()` is never called; building this class at 44.1 kHz re-points
   nothing.

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is inside its budget on both boards.**
  §4 carries the figures: P4 15.2 % and S3 25.3 % of the deadline (marginal)
  against 26 % / 43 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names.
- **No independent refutation pass.** One session built the class and ran
  every measurement. The refutations recorded in §1 are that session's own —
  including one measurement (T2's) that was wrong and was caught — but the
  gate asks for an independent agent given one demonstrated trait and told to
  break it, and that has not happened for any of T1–T5.
- **T2 and T3 are `unmeasured` at 22.05 kHz**, for the dossier's own
  pre-stated reason: the 10 kHz bell and the 16 kHz shelf do not exist at that
  rate. This is a stated limit, not a missing run, but it is a gap in the
  trait coverage and it is named here rather than left in a table cell.
- **T3's width half is a design target, not a fact about the pedal.** The
  0.5/2.5 Q pair and the 0.5 halving bar are ours; no source reached in the
  dossier states the EQP-1A's bandwidth range in octaves at either extreme
  (dossier §8 Q4, still open). The measurement demonstrates the class does
  what the dossier asked; it does not demonstrate the pedal does.
- **`circuitpython-effects` has no digest on the three probes §3 names.** Its
  heap cannot hold them through `render_effect.py`'s `RawSample` fallback, and
  that build refuses the streaming `WaveFile` path. The one small probe that
  fits agrees to the digit, and §2 exercises the same interpreter on every
  Tier 1 invariant. What it would take: a streaming path that build accepts,
  or committed probes short enough to fit — either is a kit change, filed as
  audiocomponents#xx when this lands.
- **Three foundation-era registry tests had to be generalized, not just
  passed.** `test_rebuilt_registry.py` asserted that *every* one of the 46
  misses, that `rebuilt.known()` is exactly the two fixtures, and that
  nothing under `rebuilt/` is in `ALL` — all three true only while nothing
  had been rebuilt. They are rewritten to hold the same thing under a
  catalogue that is being rebuilt one class at a time, and each carries the
  reason in place. Any sibling Phase 2 branch will hit the same three
  failures and only the first to land needs to fix them.
- **This file and the code are in two commits, not one.** §8's last box says
  so.
- **The dossier's §§1–8 are 18 KB against vision §7's 8–12 KB band.** Station
  A settled three of the four open questions and removed every elided cell,
  but did not reach the length target; three tables account for 5.8 KB of it.

---

## Refutation record (2026-09-07)

An independent refuter pass, run against the branch as it stands. Every trait
marked **demonstrated** in §1 was re-measured with the kit
(`PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_traits.py`),
then attacked by varying the probe material and the rate *within each trait's
own terms* and by asking whether the check can fail. All ten §1 cells
reproduced to the digit at 48 kHz, 44.1 kHz and 22.05 kHz. Four of the five
traits did not survive the attack. Scripts: `.refute/r1.py`–`.refute/r6.py`.

| # | Verdict | Argument | What the class author must answer |
|---|---|---|---|
| **T1** | **stands** | Reproduced at all three rates (`30 Hz +2.48 / min −4.46 at 154.0 Hz / 0.042 dB` at 48 k; identical at 44.1 k and 22.05 k). Attacked on probe level, which the trait does not fix: at −40, −20, −10 and −6 dBFS the three figures move by at most 0.01 dB and the verdict holds. Attacked on absence: a flat (patch 0) build reads `30 Hz +0.00, min +0.00` and **misses** T1, so the check is not passing on nothing. The shared-corner fault is red for the reason T1 names. | *(nothing)* Note only that `minimum(100, 400)` returns the window minimum, so §1's "at 154.0 Hz" clause is inside the window by construction and carries no information; the load-bearing clause is the −1.0 dB floor, and that one does fail on absence. |
| **T2** | **REFUTED** | The whole of T2 reads **demonstrated on a byte-flat wire.** Construction defaults (patch 0), `max abs(dB)` over the 1–20 kHz grid `= 0.000000`: local maximum `+0.00 dB at 10066 Hz, 0.010 oct off` (bar 0.333) — pass; 3→5 kHz monotonic `True` (+0.000 → +0.000) — pass; peak moves `0.000 oct` under the atten selector — pass. `.refute/r3.py`. The cause is `parametriceq_traits.py:99`: `local_maximum_near` marks index *i* a maximum when `db[i] >= db[i-1] and db[i] >= db[i+1]`, so on a plateau **every** interior point qualifies and the routine then returns the one nearest 10 kHz — distance 0.010 oct, whatever the build. `.refute/r2.py` confirms the same on a build with the HF boost at 0 and the attenuator full (`None`, correctly) versus fully flat (`+0.00 dB at 10066 Hz`, wrongly). The shelf fault is red only because a shelf is *monotone* through 10 kHz; the check separates bell from slope, never bell from absence. This is the absence-reads-as-agreement shape, and §1's refutation column claims the opposite — that the local-maximum read "separates them". | Add a clause that requires the bell to exist — a prominence bar (peak minus the higher of the two adjacent minima, or peak minus the level ⅓ oct out) — and re-run; and strike the plateau from `local_maximum_near` (strict `>` on one side). Then say whether T2 still holds. Also: no planted fault exercises T2's third clause (the cut selector moving the boost's peak), and `moved = 0.000 oct` is one grid step at 0.090 oct resolution, so that clause has never been shown able to fail. |
| **T3** | **REFUTED** | T3 fixes the settings ("at full boost", both bandwidth extremes) but **not the probe level**, and the class clips to int16 in every section by its own §4. Same class, same settings, louder probe: `−16 dBFS → +7.95 dB` (still in band), **`−14 dBFS → +6.43 dB`**, **`−12 dBFS → +4.70 dB`**, **`−10 dBFS → +2.85 dB`**, **`−6 dBFS → +0.74 dB`** (`.refute/r4.py`, `.refute/r5.py`). At −10 dBFS and below the reading is *inside T3's own named disconfirmation*, "under 3 dB, the shape every constant-gain Q knob has" — indistinguishable from the planted constant-gain fault (−0.05 dB). The −20 dBFS figure in §1 is therefore a statement about one probe level, not about the class, and §1 does not say so. | State the level T3 is claimed at, as part of the trait or as a stated precondition, and justify it against the class's own clipping headroom; or measure the peak gains before the clipping section. Then say at which input level T3 stops holding and whether that level is inside the pedal's normal operating range. |
| **T4** | **REFUTED (first half)** | The 0.02 % spread is the law reading back its own free constant. `parametriceq.py:76` sets `SKIRT_DB = 1.0`, and the law holds the response at exactly that level fixed across gains; T4 measures the **+1 dB** crossing. Reading the *same three rendered curves* at a neighbouring level (`.refute/r1.py`) gives: `+0.50 dB → 14.73 %`, `+0.75 dB → 7.33 %`, **`+1.00 dB → 0.02 %`**, `+1.25 dB → 8.05 %`, `+1.50 dB → 18.13 %`, `+1.75 dB → 32.60 %` — the pass is a knife edge 0.25 dB wide, centred on the constant. §1's defence — "a law fitted to the trait would pass at every skirt" — is backwards: a law fitted to the trait is precisely one whose skirt equals the level the trait reads, and §8 Q2's own record (0.1 dB → 18.0 %, 0.5 dB → 11.6 %) shows the constant was moved until the trait passed. The trait's *second* half (bandwidth ratio 3.369×, bar 3×) is a genuine prediction of App. A and stands; the crossing half tests the implementation of the chosen constant, not proportional-Q behaviour. T4 is level-robust (0.02 % at −18 through −12 dBFS). | Either restate T4's crossing level so it is not `SKIRT_DB` (e.g. hold the crossing at 0.5 dB *and* 1.5 dB and give the spread at both), or cite a source that fixes the API 550A's skirt at 1 dB. As written, the 5 % bar cannot distinguish "the bells are proportional-Q" from "one constant was set to 1.0". |
| **T5** | **REFUTED** | T5 says "unity within **0.1 dB**, 20 Hz–20 kHz" and names no level. Same class, same G = 16 bell, louder probe (`.refute/r4.py`, `.refute/r5.py`): `−16 dBFS → 0.0005 dB`, **`−14 dBFS → 0.9942 dB`**, **`−12 dBFS → 2.5382 dB`**, **`−10 dBFS → 4.2852 dB`**, **`−6 dBFS → 8.0459 dB`** — up to 80× the bar, and at −10 dBFS G = 12 already reads 0.9960 dB. §1's defence is a mechanism argument ("the product is 1 by construction … the RBJ numerator and denominator swap"), and that argument is false for this class as built: §4 of the dossier says each section writes int16 and clips there, so the chain is not linear and reciprocity is a small-signal property only. The margin in §1 is three orders under the bar because the probe is 6 dB inside the headroom, not because the mechanism is exact. Secondary: on a flat build the same check reads `0.0000 dB` and passes, so T5 alone cannot tell a reciprocal bell from no bell. | Restate T5 with the input level it holds at, and give the level at which it stops holding (measured: between −16 and −14 dBFS at G = 16). Replace the "exact by construction" argument with one that accounts for the per-section int16 clip, or measure reciprocity ahead of the clip. |

**Refuter's method, stated so it can be checked.** Re-ran §1 at all three
rates; swept the probe level over −40 … −6 dBFS holding every trait's own
settings; re-read T4's crossings off the already-rendered curves at six
levels; ran each trait's clauses against a patch-0 wire; re-ran T2 on a
193-point grid. Not done: no board run, no MicroPython or CircuitPython run,
and §§2–4 (Tier 1, digests, Tier 3) were not attacked — this pass covers §1
only.
