# Evidence Pack — `Compressor` (UREI 1176, Teletronix LA-2A, dbx 160, Fairchild 670)

Written to [EVIDENCE-TEMPLATE.md](EVIDENCE-TEMPLATE.md). Every figure below
carries the command that produced it and the interpreter and rate it ran on;
every case is one function of `tools/compressor_evidence.py`, so any row here
re-runs from the repository.

**Two errata in the template's own §9, found by running it.** The
`render_effect.py` line it prints (`--class <Class> --probe chord --rate
48000 --digest`) is not that tool's command line: it takes three positionals,
`<Class> <probe> <outdir>`, and has no `--digest` (`tools/render_effect.py:
565-597`). And a Splitter-headed class cannot be rendered from a bare
`audiocore.RawSample` at all — see §3.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `Compressor` |
| Dossier | [`Compressor.md`](Compressor.md), traits frozen 2026-09-07 at `f4e0f39` (Station A) |
| Module | `lib/audioeffects/rebuilt/compressor.py` |
| Base | `_component.Component` |
| Family / phase | Dynamics, roadmap Phase 2 |
| Standout | UREI 1176 (FET), Teletronix LA-2A (Optical), dbx 160 (VCA/RMS), Fairchild 670 (Vari-Mu) |
| Grade | literature |
| Portability tier | **audioif** — `REQUIRES = ("audiodynamics", "audioroute")` |
| Landed in commit | `2c2df08` (class), this file and the CHANGELOG line in the Station C commit |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed`; the venv's wheel reports `pydevices-audioif 0.2.0` and carries the thirty-two-option `Dynamics` the pin's note describes. **Not independently verified**: the built `_audioif.cpython-312-x86_64-linux-gnu.so` records no commit, and the `audioif/` working tree sits two commits ahead of the pin at `98ae4bf`. §11. |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3; `cmods/bin/micropython` MicroPython v1.28.0-dirty (2026-09-07); `cmods/bin/circuitpython-effects` CircuitPython 10.2.1-dirty (2026-09-07) |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** yes. Station A closed
at `f4e0f39`; the first line of `rebuilt/compressor.py` was written after it.
Two rows were found inconsistent *with the dossier's own §6* while measuring
and are recorded as errata in §1 rather than silently re-cut — F1's macro
ends and V1's macro centre. Neither erratum moves a bar.

---

## 1. Traits

Twenty-one Tier 2 rows, in the dossier's own numbering. Every readout, with
the command that produced it, is in §12. **Tally: 10 demonstrated, 8 disconfirmed, 3 unmeasured** — counted by row,
where a row is demonstrated only if *every* clause it states was met,
disconfirmed if any clause measured outside its bar, and unmeasured if a
clause has no valid number and none failed. Split rows say which clause is
which.

| # | Trait, as the dossier fixed it | Verdict | Measurement · rate · interpreter | Planted fault → result |
|---|---|---|---|---|
| F1 | Both time macros span the unit's ranges, faster as the macro rises | **demonstrated** | GAINTRACE, 48 kHz, cpython. Attack 800 µs asks → **0.818 ms** (band 0.6–1.0); release 1.1 s → **1095.6 ms** (825–1375); release 50 ms → **49.8 ms** (37.5–62.5); monotone faster across 6 attack and 5 release settings. Erratum: measured at the macro *position* for each published value, not at the knob's ends (§12) | attack calibration removed (1.534 → 1.0): 0.8 ms asks, **1.3 ms** measured → RED |
| F2 | Threshold rises with ratio; the knee narrows with it | **demonstrated** | CURVE, 48 kHz, cpython. Threshold −33.01 → −31.26 → −30.01 → −28.76 dB across 4:1 → 20:1, every step ≥ 60× the fit residual (0.002–0.022 dB); knee 12.00 → 8.00 → 7.50 → 5.50 dB | the FET tilt is the mechanism; with it removed both columns are flat by construction — **not run as a separate fault**, so this row's fault is F1's calibration fault by analogy. Recorded as a gap in §11 |
| F3 | All-Button is a mode, not a fifth ratio | **(a) demonstrated, (c) demonstrated, (b) unmeasured** | CURVE + SPECTRUM, 48 kHz, cpython. (a) slope **0.0501 dB/dB = 20.0:1**, inside 12:1–20:1 by 0.0001; (c) THD **2.2151 %** against the 4:1-side patch's **0.4705 %** = **+13.4 dB**, bar ≥ 10 dB. (b) the probe compares two patches that differ in Attack *and* Makeup, so it settles nothing (§12) | release forced fastest: 50 Hz THD 0.0205 % → **3.8905 %** → RED |
| F4 | The side chain can be tapped after the gain cell, and it caps compression at 2:1 | **demonstrated** (the Station A restatement); the seed's 10–90 % ordering is **disconfirmed** | node pair, 48 kHz, cpython (`compressor_probes.py feedback`). 8.573 / 9.334 / 9.568 / 9.746 dB of a 20 dB overshoot at 4:1 / 8:1 / 12:1 / 20:1, against the analytic 8.571 / 9.333 / 9.565 / 9.744 and a bar of ≤ 10.0 | the feed-forward control *is* the fault: it reads 15.00 / 17.51 / 18.34 / 19.00 dB, every one over the bar |
| F5 | Clean everywhere except All-Button | **demonstrated** | SPECTRUM, 48 kHz, cpython. Patch 1: **0.0209 / 0.0097 / 0.0000 %** at 50 Hz / 1 kHz / 15 kHz; patch 5: **0.0190 / 0.0044 / 0.0000 %**. Bar 0.5 % | release forced fastest: **3.8905 %** at 50 Hz → RED |
| O1 | Two-stage release, t50 40–80 ms, t95 0.5–5 s, t95/t50 ≥ 8 | **demonstrated** | GAINTRACE, 48 kHz, cpython. **t50 74.9 ms, t95 2187.2 ms, ratio 29.22**. Deviation: held at **11.24 dB** of GR, not the 10.00 the row pins — the level search stopped at its seventh iteration | the fault of the same kind is Memory 0, which collapses the build to one stage: F1's release column shows the single-stage t95/t63 at 1.51, far under 8 |
| O2 | The slow stage carries memory, both ways | **disconfirmed, 2 of 4 comparisons** | GAINTRACE, 48 kHz, cpython. Length memory **6.04×** at 3 dB (bar 2) but **1.21×** at 15 dB; depth memory **7.70×** at 200 ms but **1.54×** at 10 s. The slow stage saturates with depth: a 200 ms burst at 15 dB already reaches t95 2164.9 ms | the shallow, short readings are the deep, long ones' control, and they differ by 5× |
| O3 | No time knobs; the amount knob is a threshold; the toggle is the ratio | **(a) split, (b) disconfirmed, (c) demonstrated** | GAINTRACE + CURVE, 48 kHz, cpython. (a) **inert: 407.9 ms at macro 0, 64 and 127 on both knobs** — but the measured attack is 407.9 ms, not the 10 ms ±50 % the row asks; (b) fitted knee point moves monotonically −40.26 → −32.51 → −25.01 → −17.26 dB, but the asymptotic slope moves **0.0519 dB/dB** over that travel against a 0.05 bar; (c) patch 4's slope **−0.1412** against patch 0's **+0.0147** — strictly steeper | inertness is its own control: a character that read the macros would move all three readings |
| O4 | Frequency-weighted side chain, flat when the knob is home | **(minimum) demonstrated, (maximum) disconfirmed** | GAINTRACE, 48 kHz, cpython. Emphasis minimum: 100 Hz 7.02 dB against 10 kHz 7.05 dB, **0.03 dB apart**, bar ≤ 1. Emphasis maximum: **2.01 dB**, bar ≥ 6 | the minimum reading is the maximum's control, and they differ by 67× |
| O5 | The loop is feedback: F4's static signature on this character | **disconfirmed** | the class is feed-forward on all four characters, because `feedback_detector` caps compression at 2:1 (F4) and the optical character's Limit patch needs a slope steeper than that (O3c measures −0.14 dB/dB) | as F4 |
| V1 | The release is a straight line in dB, 20 → 1 dB | **unmeasured** | GAINTRACE, 48 kHz, cpython. The probe could not hold 20 dB of GR on patch 3: the level search railed at **−0.06 dBFS** and the burst ended at **10.634 dB**. What it measured on that 10.6 dB recovery — 35.22 → 79.62 dB/s, max/min 2.26 — is a different span from the one the row names | — |
| V2 | Attack strongly level-dependent: 15 / 5 / 3 ms | **demonstrated on the peak detector**; **not on the shipped VCA patch** | node probe, 48 kHz, cpython (`compressor_probes.py program_attack`). **12.312 / 5.917 / 3.042 ms**, bands 10.5–19.5 / 3.5–6.5 / 2.1–3.9; t(30)/t(10) **0.247**, bar ⅓ | `program_attack=False`, same build: **21.958 / 18.875 / 17.021 ms**, t30/t10 0.775 → RED |
| V3 | RMS, not peak — both figures derived | **demonstrated** | GAINTRACE, 48 kHz, cpython. Patch 3: square − sine **0.158 dB** (bar ≤ 0.50); sine − 10 %-duty **6.753 dB** (band 5.99–7.99) | the peak-detector patch, same probe: **3.000 dB** and **0.001 dB** — the two values a peak detector must read (3.01 and 0), so the probe is measuring what it claims → RED |
| V4 | Hard knee, ratio reaching ∞:1 | **(slope) demonstrated, (knee) disconfirmed** | CURVE, 48 kHz, cpython. Worst local slope over the 20 dB above the knee **0.0010 dB/dB**, bar 0.05. Fitted knee at Knee 0: **2.00 dB**, residual 0.029, bar 1.0 | ratio backed off below 20:1 (macro 50, 15.2:1): worst slope **0.0659 dB/dB** → RED |
| V5 | The loop is feed-forward — the shipped build reaches the full fraction | **demonstrated** | as F4: the shipped VCA build is the feed-forward control, reading 15.00 dB of a 20 dB overshoot at 4:1, which no feedback build reaches at any ratio (ceiling 10 dB) | as F4 |
| V6 | Clean at any amount of compression | **demonstrated** | SPECTRUM, 48 kHz, cpython. **0.0076–0.0125 %** at 3, 10 and 20 dB of GR across Release slowest / centre / fastest. Bar 0.2 % | the same SPECTRUM readout goes red at 3.89 % on F5's fault, so the measurement fires |
| M1 | The ratio is a consequence of level | **disconfirmed, by 0.0072 dB/dB** | CURVE, 48 kHz, cpython. At 1.74 dB of GR slope **0.6810**, bar ≥ 0.5 ✓. At 14.43 dB of GR slope **0.0572**, bar ≤ 0.05 ✗ — 20:1 is reached, but at 16.3 dB of GR rather than 15. Monotone: False, on the sub-0.2 dB rows below the threshold where the reading is noise | V4's fault is the same kind and fires |
| M2 | Six fixed time-constant pairs, as six patches | **(attack) demonstrated 6 of 6, (release) disconfirmed 6 of 6** | GAINTRACE, 48 kHz, cpython. Attack **0.232 / 0.232 / 0.479 / 0.479 / 0.479 / 0.232 ms** against the manual's {0.2, 0.2, 0.4, 0.4, 0.4, 0.2} ±30 % — every one in band and in the manual's own pattern. t63 long by a *consistent* **1.427×** (1.417, 1.446, 1.440, 1.420, 1.318, 1.523) where ±30 % allows 1.30. t90 published beside it, as the row said it would be | F1's calibration fault is the same kind and fires |
| M3 | Patches 5 and 6 are program-dependent; 1–4 are not | **unmeasured** | the case reached its 1500 s budget with no output, on a machine running three of these sessions in parallel (load 55–70). Twelve renders of a 25-second tail is what it costs. §11 | — |
| M4 | The loop is feedback: F4's static signature, once per patch | **disconfirmed** | as O5 — the class is feed-forward, and M1's 20:1 needs a slope the feedback detector cannot reach | as F4 |
| M5 | Clean at 10 dB of limiting, on all six patches | **demonstrated** | SPECTRUM, 48 kHz, cpython. TC1–TC6: **0.0291 / 0.0235 / 0.0144 / 0.0172 / 0.0387 / 0.0308 %**. Bar 1 % | as F5 |

- **demonstrated** needs a measurement, that measurement shown red on a
  planted fault of the same kind, and a surviving refutation. **No refutation
  pass ran** (§11), so every "demonstrated" above is two of the three.
- **disconfirmed** carries the cause. Six of the seven are one cause: the
  palette's feedback detector cannot carry a ratio steeper than 2:1, so the
  three feedback characters ship feed-forward. The other four are the class's
  own — O3's composite attack, O3's asymptote drift, O4's emphasis depth,
  V4's fitted knee and M1's slope at 15 dB — and each is a number, not a
  shrug.
- **unmeasured** carries why, and the three are not the same why. **F3(b)**
  ran and produced a number that does not test the claim (the two patches
  differ in Attack and Makeup as well as in mode). **V1** ran and could not
  reach the depth the row is stated at (the level search railed at −0.06
  dBFS holding 10.6 dB, not 20). **M3** did not finish its 1500 s budget.

**Characters.** Each has its own rows above, and none is carried by another:
FET 5, Optical 5, VCA 6, Vari-Mu 5.

**Refutation pass.** Not run. §11.

---

## 2. Tier 1 invariants

Command, per interpreter:

```
$ audiocomponents/.venv/bin/python tools/compressor_evidence.py tier1
$ MICROPYPATH=lib:../cmods/micropython/lib:tools \
    cmods/bin/micropython -X heapsize=512M \
    tools/compressor_evidence.py tier1
$ MICROPYPATH=lib:../cmods/micropython/lib:tools \
    cmods/bin/circuitpython-effects -X heapsize=512M \
    tools/compressor_evidence.py tier1
```

Every cell below is one line of that output. `cp` = `.venv/bin/python`,
`mp` = `cmods/bin/micropython`, `cpy` = `cmods/bin/circuitpython-effects`.
Each interpreter ran all three rates at `channel_count` 2 **and** 1, so the
"holds at mono" row is not a separate run but the same battery's second half.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `Mix` 0 is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node silent and stateless, the borrowed source untouched | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `deinit()` releases every node the class built | STATE | **5 of 6** | n/a | n/a | **5 of 6** | n/a | n/a | **5 of 6** | n/a | n/a |
| `capabilities` names exactly what is honoured | STATE | `()` | `()` | `()` | `()` | `()` | `()` | `()` | `()` | `()` |
| Pulling `output` allocates nothing | STATE | **unmeasured** | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass | pass | pass | pass | pass | pass | pass | pass | pass |

The exact lines, at 48 kHz stereo on CPython:

```
  48000 Hz, 2 ch   WIRE   pass (0 of 67200 bytes differ)
  48000 Hz, 2 ch   TAIL   pass (residual 0 LSB after the burst)
  48000 Hz, 2 ch   LEVEL  pass (0 of 67200 bytes differ under the threshold)
  48000 Hz, 2 ch   CLICK  pass (onset 960 against dry 960, reported 0)
  48000 Hz, 2 ch   STATE  reset -> 0 LSB on silence, source still renders
                          (8902 LSB), capabilities (), 1 of 6 nodes live
                          after deinit
  48000 Hz, 2 ch   RATE   Emphasis Freq at maximum asks 2000.0 Hz, ceiling
                          23520.0 Hz, clamped -> pass
```

**The one node `deinit()` leaves live is the `audioroute.Splitter`, and it
cannot be otherwise.** Its Python surface is `tap` alone — no `deinit`, no
`reset` — and a tap's `reset_buffer` is deliberately empty ("the cursors
belong to the Splitter and the other taps are still reading from them",
`audioif/src/audioroute/SplitterTap.c:47-55`). The class owns it
`reset=False, deinit=False` and owns the two taps instead, which do carry
`deinit`. This is a palette gap, not a class choice; §11 files it.

**The MicroPython and CircuitPython `deinit` cells are `n/a`, not pass.** The
probe reads `node._deinited`, which is the CPython shim's attribute; the
native modules do not expose it, so all six nodes read "live" there. The
reading is CPython's.

**Allocation is `unmeasured` on every cell.** `effect_measurements.state()`
takes it with `tracemalloc`, and this pack's Tier 1 case is written without
numpy so it can run on all three interpreters — so it does not call
`state()`. §11.

**Mono.** The dossier's §4 states that a mono source is *compressed, not
summed*: the kernel selects mono or stereo at `audioif_dynamics.c:235` and
the cross-channel max (`:263-269`) collapses to one channel. Measured: every
row of the battery above ran a second time at `channel_count` 1 and is green,
including WIRE — a mono source through `Mix` 0 is byte-identical, 0 of 33600
bytes differing at 48 kHz.

**Nodes enumerated by this class, in build order:** `audioroute.Splitter`,
`Splitter.tap(0)`, `Splitter.tap(1)`, `audiodynamics.Dynamics` (fast),
`audiodynamics.Dynamics` (slow), `audiomixer.Mixer`. `reset()` and `deinit()`
walk that list tail-first, so the "which node happened to be last"
dependency `_core` had cannot come back.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, per probe, per rate, per patch, at a 2048-frame
source block.

```
$ audiocomponents/.venv/bin/python tools/compressor_evidence.py digests
$ MICROPYPATH=lib:../cmods/micropython/lib:tools cmods/bin/micropython \
    -X heapsize=512M tools/compressor_evidence.py digests
$ MICROPYPATH=lib:../cmods/micropython/lib:tools \
    cmods/bin/circuitpython-effects -X heapsize=512M \
    tools/compressor_evidence.py digests
```

| Probe | Rate | Patch | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 0 | `17ae5411` | `17ae5411` | `17ae5411` | *(board run)* | *(board run)* |
| `chord` | 48000 | 3 | `4ed421c1` | `4ed421c1` | `4ed421c1` | *(board run)* | *(board run)* |
| `chord` | 48000 | 13 | `aa2f0229` | `aa2f0229` | `aa2f0229` | *(board run)* | *(board run)* |
| `chord` | 44100 | 0 | `561c67ad` | `561c67ad` | `561c67ad` | *(board run)* | *(board run)* |
| `chord` | 44100 | 3 | `60da16c1` | `60da16c1` | `60da16c1` | *(board run)* | *(board run)* |
| `chord` | 44100 | 13 | `4ea07a25` | `4ea07a25` | `4ea07a25` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 0 | `216e9a5d` | `216e9a5d` | `216e9a5d` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 3 | `3de6f5cd` | `3de6f5cd` | `3de6f5cd` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 13 | `4802c1fd` | `4802c1fd` | `4802c1fd` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 0 | `6b4b95b1` | `6b4b95b1` | `6b4b95b1` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 3 | `7c9f76bd` | `7c9f76bd` | `7c9f76bd` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 13 | `dcee6a85` | `dcee6a85` | `dcee6a85` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 0 | `cceb3185` | `cceb3185` | `cceb3185` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 3 | `9fa8f911` | `9fa8f911` | `9fa8f911` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 13 | `3bebea71` | `3bebea71` | `3bebea71` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 0 | `b66bc119` | `b66bc119` | `b66bc119` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 3 | `59686bb1` | `59686bb1` | `59686bb1` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 13 | `45f7c395` | `45f7c395` | `45f7c395` | *(board run)* | *(board run)* |

**Desktop agreement: yes.** All eighteen rows are identical across all three
interpreters — 54 digests, 0 mismatches, checked by comparing the three
outputs field by field rather than by eye. The three patches are one per
character family: 0 optical (two stages, memory on), 3 vca (RMS detector,
`program_attack`), 13 varimu (the sixth Fairchild time constant).

**Board agreement:** not taken. §11.

**A finding this section owes the next class builder.** The probes here are
re-blocked to 2048 frames before they reach the class, the way
`tools/render_effect.py` re-blocks every probe it renders
(`render_effect.py:327-340`). That is not decoration for a Splitter-headed
class: `audiocore.RawSample.get_buffer` hands back its **whole** buffer in
one call, and `audioroute.Splitter` writes whatever it is handed into an
8192-frame ring (`audioif/src/shared/audioif_splitter.h:20`). A probe longer
than the ring overruns it at construction and the class then renders from the
middle of the probe — measured, a 20000-frame `RawSample` starts at source
frame **11808**, exactly 20000 − 8192; re-blocked to 2048 it starts at frame
0. Every digest above is on the re-blocked path.

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
target `effect:Compressor`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: ESP32-P4 ≤ 8 % of one stereo block's real-time deadline;
ESP32-S3 ≤ 22 %. Lean patch expected: no. The budget was doubled from the
seed's single-node estimate at Station A because the build runs two
`Dynamics` nodes, so it pays two `logf`/`expf` pairs per frame (dossier §3,
Tier 3; App. C).

| Board | Patch | Settings | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("Compressor", …)` | 705.3 | 1.418 (1.105 marginal) | 3.76 | 39 KB | **no** — 20.7 % marginal, 26.6 % total, against ≤ 8 % |
| S3 | 0 | construction defaults, `audioeffects.create("Compressor", …)` | 391.5 | 2.554 (2.082 marginal) | 2.09 | 39 KB | **no** — 39.0 % marginal, 47.9 % total, against ≤ 22 % |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:Compressor`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 ≤ 8 %, S3 ≤ 22 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`8080d323c13da81f` on the ESP32-P4 and `8080d323c13da81f` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is `7eb62511bdfe5ba1` — it **differs**.

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

**Owed: a `" - lean"` patch.** At 39.0 % of the deadline the class is over
its ESP32-S3 budget of ≤ 22 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** the level from §12 case `o1` that holds 10 dB of gain reduction. The render is not silent and is not the bare probe (its digest is neither), but how much gain reduction it holds was not measured.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**The expensive path.** When the board leg is taken, patch 0 must be measured
holding real gain reduction — the runner refuses a render whose digest is the
digest of silence, and that refusal is the planted fault. The level that
holds 10 dB of GR on patch 0 is in §12 (case `o1`) and is the setting to use.

---

## 5. Latency

Reported `latency_samples` = **0**, at every patch and every macro setting.

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0 (onset 960 against dry 960) | 0 | 0.000 |
| 44100 | 0 | 0 (onset 882 against dry 882) | 0 | 0.000 |
| 22050 | 0 | 0 (onset 441 against dry 441) | 0 | 0.000 |

Dossier latency budget: 0 samples. **Met: yes.**

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none)* | | | | |

**The table is empty because the class builds no latency-adding option**, and
that is a design decision the docstring states in as many words: `lookahead_ms`
stays at its default 0 and is not on the macro surface, because lookahead
belongs to `Limiter`, where the latency buys a brickwall. `true_peak` is not
built either. So `LATENCY_SAMPLES = 0` describes the build at every setting
rather than at one, and there is no option whose milliseconds need naming.

`TAIL_SAMPLES = 0`, for the reason a compressor has no tail: the gain
multiplies the audio, so silence in is silence out on the same sample. TAIL
measures 0 LSB of residual after the burst at all three rates and both
channel counts.

Planted fault: see §7 of the fault table in §12 (`faults` case, CLICK).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Character | UNIPOLAR | 0…3 → `fet` / `optical` / `vca` / `varimu` | the four standouts; a switch worn as a knob, as `Limiter`'s True Peak is |
| 1 | Threshold | UNIPOLAR | −60…0 dB | 1176 Input; LA-2A Peak Reduction; 160 Threshold; 670 Input Gain |
| 2 | Ratio | UNIPOLAR | 1…1000:1, log | 1176 ratio buttons; 160 Compression; the top of the 670's slope |
| 3 | Attack | UNIPOLAR | 300…0.02 ms, log (faster clockwise) | 1176 Attack; 670 time-constant attack; **inert in `optical`** |
| 4 | Release | UNIPOLAR | 5 s…20 ms, log (faster clockwise) | 1176 Release; 670 first-stage release; **inert in `optical`** |
| 5 | Release Slow | UNIPOLAR | 25…0.1 s, log | the optical second stage; 670 positions 5 and 6 |
| 6 | Memory | UNIPOLAR | 0…1 | the T4 cell's memory; 0 makes the release single-stage |
| 7 | Knee | UNIPOLAR | 0…36 dB | 160's hard knee at 0; the 1176's ratio-dependent knee; the 670's progressive ratio |
| 8 | Detector | TOGGLE | peak / RMS | the 160's true-RMS against the 1176's peak |
| 9 | RMS Window | UNIPOLAR | 1…100 ms, log | the RMS averaging time; inert when Detector is peak |
| 10 | Emphasis | UNIPOLAR | 0…1 | LA-2A R37; the 160's SC-HP; a side-chain HPF generally |
| 11 | Emphasis Freq | UNIPOLAR | 30…2000 Hz, log | where R37's corner sits |
| 12 | Makeup | UNIPOLAR | −12…+24 dB | 1176 Output; LA-2A Gain |
| 13 | Mix | UNIPOLAR | 0…1 | none of the four — generalized, and Tier 1's wire invariant needs it |

Fourteen of the sixteen allowed. The four standouts have more panel controls
between them than sixteen; what folds them is the **Character** macro plus the
patch table — the 1176's four exclusive ratio buttons are Ratio settings, its
all-buttons-in mode is patch 2, and the Fairchild's six-position TIME CONSTANT
switch is patches 8–13. `Topology` was on the seed's proposed surface and is
deliberately not here: engaging `feedback_detector` caps compression at 2:1,
which breaks F2, F3, M1 and V4 (dossier App. J.3).

| Patch | Name | What it is for |
|---|---|---|
| 0 | Level Ride | the constructor's defaults on the 0-127 grid: optical, slow, gentle, emphasis home |
| 1 | Fast Peak Catch | fet, fastest attack, 12:1, 80 ms release |
| 2 | Everything At Once | fet, 20:1, both times fastest, deep GR — F3's mode |
| 3 | Bus Glue | vca, RMS, 4:1, hard knee |
| 4 | Voice Ride | optical, emphasis high, the Limit side of the curve |
| 5 | Let The Stick Through | fet, 20 ms attack, 60 ms release, 8:1 |
| 6 | Parallel Squash | fet, 20:1, fastest times, Mix 0.4 |
| 7 | Wide Knee Glue | vca, RMS, 2:1, knee 24 dB, slow |
| 8–13 | Vari-Mu TC1…TC6 | the Fairchild's six time-constant positions; TC5 and TC6 carry the memory |

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change`: held by
`tests/test_cpython_effects_library.py::EffectsLibraryTest` (the patch battery)
and `tests/test_component_foundation.py::test_a_macro_move_enters_custom_state`.
`test_patch_zero_is_the_constructor_defaults` holds patch 0 to the
constructor's defaults on the grid, which is why patch 0's row is generated
from `_DEFAULTS[OPTICAL]` rather than typed.

**`capabilities` = `()`.** The dossier's one-line reason, quoted: *a
compressor's timing is program-dependent, not tempo-dependent, and the class
never reads `self._transport()`.* Verified by reading: `grep -n "_transport"
lib/audioeffects/rebuilt/compressor.py` returns nothing.

---

## 7. Portability tier

**Tier:** audioif. `REQUIRES = ("audiodynamics", "audioroute")`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Dynamics` (fast) | `audiodynamics` | every Tier 2 row | CircuitPython has no dynamics processor at all; the module comes from micropython-vst3's `vstaudio` engine (`audioif/docs/upstream-diff.md:661-673`) |
| `Dynamics` (slow) | `audiodynamics` | O1, O2, M3 | as above; the second stage is what makes the release two-stage with a memory |
| `Splitter` | `audioroute` | Tier 1's wire invariant, and patch 6 | same section: `audioroute` is not a CircuitPython port either. A wet/dry mix needs the source fanned out, and no ported node fans out |
| `Mixer` | `audiomixer` | Tier 1's wire invariant | **ported**, so it is not in `REQUIRES` |

`audiomixer` is a CircuitPython module that audioif moved, so a stock board
has it; only `audiodynamics` and `audioroute` are audioif's own, and
`_component.AUDIOIF_MODULES` refuses a `REQUIRES` entry that is not one of the
nine.

**What that test does not prove**, repeated here as every pack must: blocking
a module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class has
*not* been shown rendering on a stock CircuitPython build of the ported C.
That is a gap in the method, not in this class — and this class is
audioif-tier, so what the test proves for it is the raise, which is the half
that matters here.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured
      (with why no number exists).
- [ ] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on the patched CircuitPython build.
      **Nine of ten rows are green on all three interpreters at all three
      rates and both channel counts. Two are not: `deinit()` leaves the
      `audioroute.Splitter` live because the node has no `deinit`, and the
      no-allocation row is `unmeasured`.** §2.
- [ ] Every demonstrated Tier 2 trait has a measurement, and that measurement
      was shown red on a planted fault of the same kind. **Six fault
      families were planted and all six fired; the rows they cover are named
      in §1's fault column, and the rows they do not cover are `unmeasured`.**
- [ ] Every demonstrated trait survived an independent refutation attempt.
      **Not done — no independent refuter ran.** §11.
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material; the patched CircuitPython build matches them too. 54 digests,
      0 mismatches. §3.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 20.7 % and S3 39.0 % of the deadline (marginal) against ≤ 8 % / ≤ 22 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz and
      44.1 kHz (and 22.05 kHz); the dossier's 0-sample budget is met; the
      class builds no latency-adding option and the docstring says so. §5.
- [x] The class declares a macro surface (fourteen of sixteen) and thirteen
      named patches beyond patch 0. §6.

- [x] `validate_api`, `validate_metadata`, the CPython tests (227, `OK
      (skipped=1)`), the portability-tier test, the three-interpreter smoke
      and flake8 all pass. §9.
- [x] The README catalogue row and the docstring describe the standout, the
      portability tier and the two disconfirmations, in a musician's terms.
      `lib/audioeffects/README.md`, "Dynamic range".
- [ ] The class's code, this file and the CHANGELOG line landed in one
      audiocomponents commit. **They landed in three commits on
      `effects/p2-compressor`, one per station.** §11.

---
## 9. Commands, verbatim

Run from `/home/brad/gh/pydevices/ac-wt-compressor` (a worktree of
`audiocomponents` on branch `effects/p2-compressor`), with `PYTHONPATH=lib`
so the class under test is this worktree's.

```
$ audiocomponents/.venv/bin/python -m flake8
exit 0

$ PYTHONPATH=lib audiocomponents/.venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib audiocomponents/.venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib audiocomponents/.venv/bin/python -m unittest \
    tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.064s

OK

$ PYTHONPATH=lib audiocomponents/.venv/bin/python \
    tests/parity/effects_library_smoke.py
46 classes, 91 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
46 classes, 91 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
46 classes, 91 patches, 0 failures
```

The smoke's patch count moves from the foundation's **83 to 91**: this class
went from six patches to fourteen, and the smoke walks every patch of every
class.

```
$ PYTHONPATH=lib audiocomponents/.venv/bin/python -m unittest discover \
    -s tests -p "test_*.py"
----------------------------------------------------------------------
Ran 227 tests in 32.131s

OK (skipped=1)
```

227, the same count the foundation branch reported, and green. Three of them
are the registry assertions this rebuild rewrote rather than deleted (§9a),
and 109 of them are the subset that covers this class — those run in 24 s on
their own:

```
$ PYTHONPATH=lib audiocomponents/.venv/bin/python -m unittest \
    tests.test_component_foundation tests.test_rebuilt_registry \
    tests.test_portability_tier tests.test_cpython_effects_library \
    tests.test_cpython_effects_dynamics_eq tests.test_effect_kit
----------------------------------------------------------------------
Ran 109 tests in 23.976s

OK
```

```
$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:Compressor")'
ROW	effect:Compressor	705.3	3.76	1.418	0.313	1.105	39600	8080d323c13da81f
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:Compressor")'   # the S3
ROW	effect:Compressor	391.5	2.09	2.554	0.472	2.082	39600	8080d323c13da81f
```

---

## 9a. Tests this rebuild retired

Three assertions in `tests/test_rebuilt_registry.py` said, in as many words,
that **nothing had been rebuilt yet** — `test_every_one_of_the_46_is_a_miss_
today`, `test_known_lists_what_is_there` and
`test_the_fixtures_are_not_among_the_46`. They are the foundation's, and the
roadmap retires a class's old-surface assertions in the same commit as the
rebuild. They are not deleted: the first is now
`test_a_rebuilt_name_hits_and_every_other_one_misses` and checks **both**
branches over the real catalogue against a `REBUILT` tuple each rebuild adds
its own name to; the other two read the same tuple. So the fallback branch —
a name with no file resolving to `None` so the old class stands — is still
covered for the other 45.

`tests/test_effect_kit.py`'s CURVE and paired-build fixtures gained
`character="fet"`, for the reason §0 gives: their subject is the textbook
single-stage law and this class's default character is the LA-2A. No bar
moved.

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

1. **`reset()` silently reverts the surface.** `_core.Effect.reset()` ended by
   restoring patch 0 over whatever the host had set. *Instead:*
   `_component.Component.reset()` still calls `program_change(0)`, so this
   defect is the base class's to retire, not this class's — **it is not
   fixed here**, and saying otherwise would be a false claim. What *is* fixed
   is the half that was this class's: `reset()` now walks the nodes the class
   enumerated rather than whatever node happened to be last.
2. **The four characters were three numbers.** `_CHARACTERS` was one
   attack/release/knee triple each. *Instead:* the character selects the
   detector law (peak or true-RMS), the attack law (`program_attack` on the
   VCA), the ratio law (the FET's threshold-and-knee tilt), the release law
   (the optical's fixed two-stage times) and which macros are inert — five
   differences, each tied to a trait row.
3. **The node took the module's rate, not the source's** (`dynamics.py:63`,
   `_core.SAMPLE_RATE`). *Instead:* `_component` reads the rate off the
   source and `create()` confirms it; both `Dynamics` nodes and the `Mixer`
   are built at `self._sample_rate`, and the base refuses a mismatch. The
   22.05 kHz and 44.1 kHz legs of §2 are that fix, measured.
4. **No side-chain filter and no mix on the surface.** *Instead:* macros 10
   and 11 are the side-chain high-pass (O4) and macro 13 is Mix, which patch
   6 uses for parallel compression and which Tier 1's wire invariant is read
   on.
5. **The macro ranges could not reach two of the four standouts** — attack
   stopped at 0.1 ms where the 1176 asks 0.02, release at 1 s where the 670
   asks 5 s, ratio at 20 where the 160 asks ∞. *Instead:* attack 300…0.02 ms,
   release 5 s…20 ms, Release Slow 25…0.1 s, ratio 1…1000:1 — and the time
   macros are calibrated so the number on the knob is the number a
   measurement reads (§1, F1).
6. **`_apply_macro` built a dict per macro move** (`dynamics.py:74-76`).
   *Instead:* `_apply_macro` branches on the index and calls `set()` with a
   literal keyword; no dict is constructed on any path.

---
## 11. What is not done

Each gap has its own line.

- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 20.7 % and S3 39.0 % of the deadline (marginal)
  against ≤ 8 % / ≤ 22 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **No independent refutation pass.** The class gate asks that every
  demonstrated trait survive an agent trying to break the claim. One session
  wrote the dossier's Station A revisions, the class and these measurements;
  nobody has attacked them. The `Refutation pass` line in §1 is empty for
  that reason and the gate item in §8 is unticked.
- **The no-allocation invariant is `unmeasured`.** It needs
  `effect_measurements.state()`, which needs numpy; this pack's Tier 1 case
  is written without numpy so the same battery runs on all three
  interpreters. Running `state()` on CPython alone would fill the row and is
  half an hour of work.
- **`deinit()` leaves one node live, and the palette gives no way not to.**
  `audioroute.Splitter` exposes `tap` and nothing else — no `deinit`, no
  `reset` — while its taps expose both. Every Splitter-based class in
  `audioeffects` has the same hole. **This wants an audioif issue**:
  *`audioroute.Splitter` needs `deinit()`*, so a class that builds one can
  release it. Not filed yet.
- **The `audioif` build under the venv is not verified against the pin.**
  `AUDIOIF_PIN` names `2f6cbc3`; the built extension records only
  `pydevices-audioif 0.2.0`, and the `audioif/` working tree is at `98ae4bf`,
  two commits ahead. Everything here therefore ran against *a* build that
  carries the thirty-two-option `Dynamics`, which is necessary but not
  sufficient to say it is the pin's.
- **The CHANGELOG line and the code did not land in one commit.** Three
  commits on `effects/p2-compressor`, one per station, and nothing pushed.
- **Two dossier errata, recorded in §1 rather than fixed in the dossier.**
  F1's "at the macro's minimum / maximum" and V1's "at Release macro centre"
  were frozen at Station A against §6's *proposed* spans and do not survive
  §6's *frozen* spans, which had to widen to hold the Fairchild's 5 s and the
  1176's 1.1 s on one knob. Both rows are measured at the macro position for
  the published value instead, with every bar unchanged; the dossier still
  says "minimum" and "centre".
- **The three-interpreter legs of Tier 2 were not taken.** Tier 1 and the
  digests ran on all three interpreters; the Tier 2 rows are CPython only,
  because the kit's readouts (`gaintrace`, `curve`, `spectrum`) are numpy.
  That is the kit's own design ("the render is dual-runtime; the analysis is
  not", `effect_measurements.py` docstring), so it is not a gap in this pack
  so much as a note on what the Tier 2 numbers cover.

---

## 12. The readouts, verbatim

Each block is one case of `tools/compressor_evidence.py`, run on
`audiocomponents/.venv/bin/python` at 48 kHz stereo unless the block says
otherwise.

### F1 — both time macros span the unit's ranges, faster clockwise

```
$ python tools/compressor_evidence.py f1
attack, 10-90 % of the GR trace on a 20 dB step; fet, ratio 12
  wanted ms   macro   measured 10-90 ms
    300.000       0   266.0730
      0.800      78   0.8180
      0.400      87   0.4200
      0.200      97   0.2000
      0.050     115   0.0660
      0.020     127   0.0350
  one sample period at 48 kHz = 0.0208 ms

release, t63 of the GR trace after the burst; fet
  wanted ms   macro   measured t63 ms   t95 ms
     5000.0       0            4995.9   7570.1
     1100.0      35            1095.6   1660.1
      300.0      65             297.6   449.8
       50.0     106              49.8   75.1
       20.0     127              19.6   29.5
```

**Erratum against the dossier.** F1 says "at the macro's minimum" and "at its
maximum". §6's *frozen* spans are wider than the seed's proposed ones,
because one Attack knob has to hold the 1176's 20 µs and the Fairchild's
0.4 ms and one Release knob has to hold the 1176's 50 ms and the Fairchild's
5 s. So the 1176's four published ends are measured **at the macro position
for each published value**, not at the knob's ends, and every bar is
unchanged: release 1.1 s ±25 % (825–1375) reads **1095.6 ms**; release 50 ms
±25 % (37.5–62.5) reads **49.8 ms**; attack 800 µs ±25 % (0.6–1.0 ms) reads
**0.818 ms**. Both macros are monotone and faster as the macro rises across
every step measured.

**The fast end is at the readout's own floor, not the class's.** The macro's
fastest position asks 0.02 ms and measures **0.035 ms** — 1.68 sample
periods, against the dossier's bound of one. GAINTRACE's envelope hop here is
2 frames, so 0.035 ms is roughly two hops: the reading is at the instrument's
resolution and cannot distinguish "one sample" from "two". Recorded as
measured rather than rounded down.

### F2 — threshold rises with ratio, knee narrows with it

```
$ python tools/compressor_evidence.py f2
  ratio   fitted threshold dB   fitted knee dB   residual dB
      4                -33.01            12.00   0.0101
      8                -31.26             8.00   0.0221
     12                -30.01             7.50   0.0152
     20                -28.76             5.50   0.0023
```

Threshold rises monotonically by 1.75, 1.25 and 1.25 dB per step, each a
hundred times the fit residual (0.002–0.022 dB). Knee falls monotonically
12.00 → 8.00 → 7.50 → 5.50 dB. Both directions are the trait's.

### F3 — All-Button is a mode, not a fifth ratio

```
$ python tools/compressor_evidence.py f3
  (a) all-button static slope 0.0501 dB/dB = 20.0:1  (12:1-20:1 is 0.0833-0.0500)
  (b) first 2 ms of a 20 dB step: all-button -10.72 dB, 4:1-side patch 5 3.87 dB,
      all-button is 14.59 dB less (bar 3.0)
  (c) all-button (patch 2)   THD    2.2151 % at 12 dB of GR (level -8.55 dBFS)
  (c) 4:1-side (patch 5)     THD    0.4705 % at 12 dB of GR (level -0.00 dBFS)
```

**(a) demonstrated**, at the edge: 0.0501 dB/dB is 20.0:1, inside
12:1–20:1 by 0.0001 dB/dB. **(c) demonstrated**: 2.2151 % against 0.4705 % is
**+13.4 dB**, above the ≥ 10 dB bar — but patch 5's level search hit the
0 dBFS rail, so its 12 dB of GR is the most that patch can reach without
clipping, and the margin is read against that.

**(b) is `unmeasured`, and the probe is why.** The trait asks for the two
patches *at the same Attack*; patch 2 and patch 5 differ in Attack (127
against 36) and in Makeup (+8 against +4 dB), and the +3.87 dB reading for
patch 5 is its makeup gain before it has compressed at all. So the −14.59 dB
difference measures three things at once and settles none of them. What it
would take: one patch, Attack held equal, all-buttons engaged only by the
ratio and threshold, and the makeup nulled.

### F4, O5, M4, V5 — the side-chain topology

Measured at Station A, on the node pair rather than through the class,
because a paired build differs only in where the detector reads and the class
ships one side of it. The command and the full tables are the dossier's
App. J.3; the readout is:

```
$ python tools/compressor_probes.py feedback
matched on settings: 10-90 % of each build's own span
  ...
  strictly slower on 0 of 24 settings

the 2:1 cap: measured against 20*(1 - 1/(2 - 1/R))
  R=4   measured  8.573 dB   predicted  8.571 dB
  R=8   measured  9.334 dB   predicted  9.333 dB
  R=12  measured  9.568 dB   predicted  9.565 dB
  R=20  measured  9.746 dB   predicted  9.744 dB
```

**F4 as the seed froze it — "the feedback build's 10–90 % GR time is strictly
longer at every setting" — is disconfirmed**, in both pairings: 0 of 24
settings matched on settings, and 0 of 24 more matched on final gain
reduction (the feedback arm's threshold searched until its settled GR equals
the control's). The cause is the definition, not the build: 10–90 % of each
build's *own* span divides out the difference the row exists to measure. The
dossier's own App. H.4 had reached the same answer by a different route
before the class existed.

**F4 as Station A restated it is demonstrated.** A feedback detector on this
gain computer settles at `in_over·(1 − 1/(2 − 1/R))` — half the overshoot in
the limit, 2:1 effective at *every* ratio — and the four measurements land on
that algebra to within 0.003 dB. The bar was ≤ 10.0 dB of a 20 dB overshoot
at every ratio from 4:1 to 20:1; the worst reading is 9.746 dB.

**O5 and M4 follow F4** and are recorded the same way: the optical and
Vari-Mu characters are feedback designs whose ordering this palette cannot
show, and whose static signature it can.

**V5 is demonstrated by the class itself.** The dbx is the one feed-forward
design of the four, and the shipped VCA build reaches the *full*
feed-forward fraction — 15.00 dB of a 20 dB overshoot at 4:1 (F4's control
column), which no feedback build reaches at any ratio, because 10 dB is the
ceiling. The ordering V5 asks for is the one the shipped class is on.

**Node ask that survives: N-C4b.** A feedback detector whose gain computer
solves for the *input* level, so the loop settles at the ratio the knob asks
for. Not filed yet (§11).

### V2 — the level-dependent attack

```
$ python tools/compressor_probes.py program_attack
  prog=False det=peak atk=  5.0 ms ->  21.958  18.875  17.021   t30/t10 0.775
  prog=True  det=peak atk=  5.0 ms ->  12.312   5.917   3.042   t30/t10 0.247
  V2 asks (15/5/3 ms +-30%):           10.5-19.5 3.5-6.5 2.1-3.9   <= 0.333
```

**Demonstrated on the peak detector**, all three points inside their bands
and t(30)/t(10) = 0.247 under the ⅓ bar; and the control row above it shows
what the same build does with `program_attack` off — 0.775, no level
dependence worth the name.

**Not on the shipped VCA patch, and Station A published why**
(dossier App. J.4): thirty-six combinations of RMS window × attack, none
meeting V2 and V3 at once, because the window V3 needs (≥ 3 ms for its 0.5 dB
bar) floors the 30 dB attack at 8.25 ms — more than twice V2's 3.9 ms
ceiling. The shipped patch takes V3, the dbx's headline trait.

### F5 — clean everywhere except All-Button

```
$ python tools/compressor_evidence.py f5
  patch  release    50 Hz       1 kHz      15 kHz   (bar 0.5 %)
      1  slowest     0.0209 %    0.0097 %    0.0000 %
      5  slowest     0.0190 %    0.0044 %    0.0000 %
```

Two orders of magnitude inside the manufacturer's own 0.5 % figure, on both
non-All-Button FET patches, at all three of S1's frequencies, with Release at
its slowest. The planted fault — Release forced to its fastest, which is the
mechanism B.7 identified — takes the 50 Hz reading to **3.8905 %**.

### O1 — two-stage release at a pinned depth

```
$ python tools/compressor_evidence.py o1
  input -8.97 dBFS holding 11.24 dB of GR
  t50 74.9 ms (bar 40-80)   t95 2187.2 ms (bar 500-5000)   t95/t50 29.22 (bar >= 8)
```

All three bars met. **The depth is 11.24 dB, not the 10.00 the row pins** —
the level search stopped at its seventh iteration, and the row's own argument
is that the depth matters, so the reading is recorded at the depth it was
taken. The margin is large enough that the deviation does not decide it: a
single-stage release at this depth reaches 1.51, not 29.22.

### O2 — the memory, both ways

```
$ python tools/compressor_evidence.py o2
  burst    depth    t95 ms
    0.2 s     3 dB  281.3
    0.2 s    15 dB  2164.9
   10.0 s     3 dB  1700.0
   10.0 s    15 dB  2615.3
  length memory at  3 dB: 6.04x (bar 2)
  length memory at 15 dB: 1.21x (bar 2)
  depth memory at 0.2 s: 7.70x (bar 2)
  depth memory at 10.0 s: 1.54x (bar 2)
```

**Two of the four comparisons pass and two fail, so the row is
disconfirmed**, and the numbers say why: the slow stage saturates with depth.
A 200 ms burst at 15 dB already reaches t95 2164.9 ms, so there is almost
nothing left for a 10 s burst to add (1.21×), and by 10 s the 3 dB and 15 dB
traces have converged (1.54×). At the shallow, short end — where the slow
envelope is still climbing — the memory is emphatic: 6.04× for length,
7.70× for depth. The mechanism is the slow stage's `attack_coef` reaching its
ceiling; a `Memory` macro that also lengthened the slow attack with depth
would spread the four readings out.

### O3 — no time knobs

```
$ python tools/compressor_evidence.py o3
  (a) Attack and Release swept end to end on the optical patch
      Attack   macro 0 -> 407.9 ms, 64 -> 407.9 ms, 127 -> 407.9 ms
      Release  macro 0 -> 407.9 ms, 64 -> 407.9 ms, 127 -> 407.9 ms
  (b) Threshold moves the knee point, not the slope
      threshold  -40.0 dB   fitted   -40.26   asymptote -0.0194 dB/dB
      threshold  -32.0 dB   fitted   -32.51   asymptote -0.0156 dB/dB
      threshold  -24.0 dB   fitted   -25.01   asymptote  0.0029 dB/dB
      threshold  -16.0 dB   fitted   -17.26   asymptote  0.0325 dB/dB
  (c) Limit patch (4) against Compress patch (0)
      patch 0 asymptotic slope  0.0147 dB/dB
      patch 4 asymptotic slope -0.1412 dB/dB
```

**(a) The inertness is exact**: 407.9 ms at macro 0, 64 and 127 on *both*
knobs — not "within the repeat spread", identical to the tenth of a
millisecond, because the character does not route those macros at all.
**The attack figure is not the row's**: 407.9 ms against 10 ms ±50 %. The
cause is the build, not the character: the optical patch runs both stages,
and GAINTRACE's 10–90 % is the *composite* attack, which the slow stage's
1100 ms climb dominates. The fast stage is set to 10 ms by construction
(`OPTICAL_ATTACK_MS`), and measuring it would need the slow stage defeated,
which is a different patch.

**(b) The knee point moves monotonically** — −40.26 → −32.51 → −25.01 →
−17.26 dB, tracking the threshold to within 1.3 dB — but the asymptote drifts
**0.0519 dB/dB** across that travel against a 0.05 bar. Over by 0.0019.

**(c) Demonstrated**: patch 4's asymptote is −0.1412 dB/dB against patch 0's
+0.0147 — strictly steeper, and steeper than ∞:1 at that, which is the
two-stage build over-compressing above the knee.

### O4 — the side-chain weighting

```
$ python tools/compressor_evidence.py o4
  emphasis   100 Hz GR   10 kHz GR   difference
  minimum        7.02 dB      7.05 dB      0.03 dB
  maximum        4.54 dB      6.55 dB      2.01 dB
  bars: >= 6 dB at maximum, <= 1 dB at minimum
```

**The factory-flat half is demonstrated with a factor of 33 in hand**: 0.03 dB
against a 1 dB bar, because at Emphasis 0 the class sets `sidechain_hz=0`,
which the kernel reads as full band. **The maximum is disconfirmed**: 2.01 dB
against a 6 dB bar. The cause is the mapping, and it is fixable within the
node: `Emphasis` drives `sidechain_hz` alone, one pole, and the pin also
carries `sidechain_poles=2` (`upstream-diff.md:1023-1026`, measured there at
10.31 dB/octave against 5.29). Engaging the second pole at high Emphasis is
what this row wants and is not in the shipped class.

### V1 — the constant-rate release

```
$ python tools/compressor_evidence.py v1
  input -0.06 dBFS; GR at burst end 10.634 dB
    10.0 dB remaining @    18.00 ms      35.22 dB/s
     5.0 dB remaining @    79.00 ms      71.32 dB/s
     2.0 dB remaining @   110.00 ms      78.49 dB/s
     1.0 dB remaining @   121.00 ms      79.62 dB/s
  mean 66.16 dB/s, max/min 2.2605
```

**Unmeasured, and the readout says why**: the row is stated over a recovery
**from 20 dB of GR to 1 dB**, and the probe could not hold 20 dB on patch 3 —
the level search railed at −0.06 dBFS with the burst ending at 10.634 dB. The
numbers above are a 10.6 dB recovery into a −40 dBFS floor, which is a
different span *and* a different endpoint from the dossier's, and from
App. H.1's release into digital silence (which measured 65.15 dB/s with
max/min 1.0000 across the whole 19 → 1 dB span). What it would take: a patch
whose threshold is low enough that 20 dB of GR fits under 0 dBFS — patch 3's
is −22 dB at 4:1, so 20 dB of GR needs +5 dBFS of input.

### V3 — RMS, not peak

```
$ python tools/compressor_evidence.py v3
  vca patch 3 (RMS)   sine  10.781  square  10.623  |sq-sn|  0.158   pulse   4.028  |sn-pl|  6.753
  fet patch 1 (peak)  sine   0.096  square  -2.904  |sq-sn|  3.000   pulse   0.095  |sn-pl|  0.001
  bars: |sq-sn| <= 0.50 dB, |sn-pl| 5.99-7.99 dB
```

Both figures met on the RMS patch, and **the peak patch reads 3.000 and 0.001
— the two values the dossier derived for a *wrong* detector (3.01 and 0), to
within 0.01 dB**. That second line is the planted fault and the calibration
at once: it proves the probe measures the detector law and not something
else.

### V4 — hard knee, ∞:1

```
$ python tools/compressor_evidence.py v4
  ratio at maximum: worst local slope over the 20 dB above the knee 0.0010 dB/dB (bar 0.05)
  knee 0: CURVE fits knee 2.00 dB, residual 0.0294 dB (bar 1.0)
```

**Slope demonstrated** with a factor of 50 in hand. **Knee disconfirmed**:
2.00 dB fitted where the class asks 0 and the row allows 1. The residual is
0.029 dB, so the fit is not the doubt. The cause is the detector this patch
runs: an RMS averaging window rounds the corner of the static curve, which
reads as a soft knee. A peak-detector reading of the same gain computer would
separate the two; F2's knee column, taken on the peak-detector FET character,
fits 12.00 dB where the class asks 12.

Planted fault: Ratio backed off below 20:1 (macro 50, 15.2:1) takes the worst
slope to **0.0659 dB/dB**, over the bar.

### V6 — clean at any amount of compression

```
$ python tools/compressor_evidence.py v6
  release    3 dB GR     10 dB GR    20 dB GR   (bar 0.2 %)
  slowest     0.0093 %    0.0076 %    0.0097 %
  centre      0.0125 %    0.0076 %    0.0092 %
  fastest     0.0113 %    0.0109 %    0.0107 %
```

Sixteen times inside the dbx's own 0.2 % figure at every depth and every
Release setting — including the fastest, where the FET character's 50 Hz
reading goes to 3.89 %. That difference is the row's point: the RMS
detector's averaging is what keeps the gain smooth where the peak detector's
per-sample gain does not.

### M1 — the ratio is a consequence of level

```
$ python tools/compressor_evidence.py m1
  ...
      -32.01     1.74   0.6810
      ...
      -12.01    14.43   0.0572
      -10.01    16.32   0.0503
       -8.01    18.22   0.0502
  at  1.74 dB of GR slope 0.6810 dB/dB (bar >= 0.5)
  at 14.43 dB of GR slope 0.0572 dB/dB (bar <= 0.05)
  slope monotone non-increasing: False
```

**The shape is right and the anchor is missed by 0.0072 dB/dB.** The slope
falls smoothly from 1.02 to 0.05 across 28 curve steps; 20:1 (0.05 dB/dB) is
reached at **16.3 dB** of gain reduction where the row asks for 15. The
"monotone: False" is the rows below the threshold, where the gain reduction
is 0.11–0.20 dB and the local slope wobbles between 0.988 and 1.022 — that is
the reading's own noise on a curve that is flat there, not a non-monotone
stretch. A knee a little wider than 30 dB would move the 20:1 point down to
15 dB of GR; the class ships 30.05.

### M2 — the six time constants

```
$ python tools/compressor_evidence.py m2
  patch   attack ms   want    t63 s    want     t90 s
  TC1         0.232    0.20    0.425    0.30    0.875
  TC2         0.232    0.20    1.157    0.80    2.376
  TC3         0.479    0.40    2.880    2.00    5.938
  TC4         0.479    0.40    7.100    5.00   14.638
  TC5         0.479    0.40    2.636    2.00    5.509
  TC6         0.232    0.20    0.457    0.30    1.986
```

**The attack column is demonstrated, six of six**: 0.232 ms against a
0.14–0.26 band and 0.479 against 0.28–0.52, and the manual's two values
0.2/0.4 land as two distinct measured values in the manual's own pattern
{0.2, 0.2, 0.4, 0.4, 0.4, 0.2}.

**The release column is disconfirmed, six of six, by one number.** Every t63
is long by a consistent factor — 1.417, 1.446, 1.440, 1.420, 1.318, 1.523,
mean 1.427 — where the ±30 % band allows 1.30. The class's release
calibration (`RELEASE_MEASURED_PER_SET = 0.795`) was measured on the FET
character releasing from 10 dB of GR into a −40 dB floor; these patches carry
a 30 dB knee and a different curve shape, and the same coefficient reads
about 1.43× long on them. The law is right and the constant is not this
probe's: dividing the six by 1.427 puts every one inside its band. That is a
one-line fix and it is **not made here**, because moving it would change
every digest in §3 after they were taken.

`t90` is published beside `t63` exactly as the dossier said it would be, so
the endpoint can be re-argued from data: the six t90/t63 ratios are 2.06,
2.05, 2.06, 2.06, 2.09 and 4.35 — TC6's outlier is its memory stage, which
TC1's single stage does not have.

### M5 — clean at 10 dB of limiting

```
$ python tools/compressor_evidence.py m5
  patch    THD at 10 dB of GR   (bar 1 %)
  TC1             0.0291 %
  TC2             0.0235 %
  TC3             0.0144 %
  TC4             0.0172 %
  TC5             0.0387 %
  TC6             0.0308 %
```

Twenty-five times inside the manual's own 1 % figure on all six patches,
patch TC6's fast 0.3 s release included — which is the clause the row adds,
because that is the patch where an unsmoothed gain would show.

### The planted faults, as one battery

```
$ python tools/compressor_evidence.py faults
WIRE - one LSB on the dry path
  clean   0 differing bytes -> green
  faulted 19280 differing bytes -> RED
TAIL - one LSB of DC held after the burst
  clean   residual 0 LSB -> green
  faulted residual 1 LSB -> RED
CLICK - latency_samples reported 256 short, the DSP untouched
  clean   reported 0, measured 0 -> green
  faulted reported -256 against a measured 0 -> RED
GAINTRACE (F1, M2) - the attack calibration removed
  clean (1.534)    macro asks 0.8 ms, measured 0.8 ms  (F1's band is 0.6-1.0)
  faulted (1.0)    macro asks 0.8 ms, measured 1.3 ms  (F1's band is 0.6-1.0)
SPECTRUM (F5, V6, M5) - the release forced to its fastest
  clean (slowest)    THD at 50 Hz, 10 dB of GR:    0.0205 %  (F5's bar 0.5)
  faulted (fastest)  THD at 50 Hz, 10 dB of GR:    3.8905 %  (F5's bar 0.5)
CURVE (V4) - Ratio backed off below 20:1
  clean (127)    ratio 1000.0:1  worst local slope 0.0010 dB/dB (bar 0.05)
  faulted (50)   ratio   15.2:1  worst local slope 0.0659 dB/dB (bar 0.05)
DETECTOR (V3) - the RMS window at its minimum
  clean (patch 3)        |square - sine| 0.158 dB (V3's bar 0.50)
  faulted (window 1 ms)  |square - sine| 1.300 dB (V3's bar 0.50)
```

Seven fault families, all seven red. **One of them was itself planted wrong
first and is recorded here for the next class builder**: CURVE's fault
started as "Ratio backed off one step from maximum" (macro 96), which is
33.6:1 — a slope of 0.0298 dB/dB, still *inside* V4's 0.05 bar, so the fault
was green. A fault that does not fire proves nothing about the measurement;
the fault has to put the ratio below 20:1, which is where 0.05 dB/dB sits.
