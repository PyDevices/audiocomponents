# Evidence Pack — `DeEsser` (dbx 902)

Written from `EVIDENCE-TEMPLATE.md` at Station C, 2026-09-07. Every figure
below carries the command that produced it, the interpreter and the rate. A
measurement nobody ran says `unmeasured`, with why. §11 is what is not done,
and it is a section rather than a clause.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `DeEsser` |
| Dossier | [`DeEsser.md`](DeEsser.md), traits frozen 2026-09-06 at the Phase 0 seed, Station A closed 2026-09-07 at `4dfe59b` with the table unchanged |
| Module | `lib/audioeffects/rebuilt/deesser.py` |
| Base | `_component.Component` |
| Family / phase | Dynamics, roadmap Phase 2 |
| Standout | dbx 902 De-Esser |
| Grade | literature |
| Portability tier | **audioif** — `REQUIRES = ("audiobiquad", "audiodynamics", "audioroute")` |
| Landed in commit | dossier `4dfe59b`; code and battery `0f936b2`; this file, the CHANGELOG line and two corrected readings `62364f3` — **three commits, not the one the gate asks for, see §11** |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed`; the venv carries that build |
| Interpreters | `audiocomponents/.venv/bin/python` (CPython 3.12); `cmods/bin/micropython`; `cmods/bin/circuitpython-effects` |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** yes. The Tier 2 table
was written in the Phase 0 seed of 2026-09-06 and Station A changed no row
of it; what Station A added is a reading of which clauses the palette can
reach, written before any code existed (`DeEsser.md` §3, "Station A's
reading of the table").

---

## 1. Traits

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| D1 | Threshold-free and level-independent: four levels, settled reductions within 1 dB | **demonstrated** | LEVEL/GAINTRACE on `sibilant_-6/-20/-40/-55`, 48 kHz, cpython: −14.108 / −14.112 / −14.263 / −14.906 dB, **spread 0.798 dB** | `relative_threshold=0` — the primitive de-esser of §7 — gives −7.257 / −0.002 / −0.018 dB, **spread 7.255 dB → RED** (clean control green in the same run) | *"The spread is small because the probe is small."* No: the same probe faulted spans 7.25 dB. *"It is the Range blend flattening everything."* No: the fault runs at the same Range and spreads. A second, independent axis agrees — D5's three renders hold the balance and raise the level 20 dB, and the depths are −4.350 / −4.280 / −4.239 dB. |
| D2 | Split settable 800 Hz–8 kHz, each half maximally flat, 12 dB/octave, −3 dB corner tracking the control within 5 % | **split verdict: tracking demonstrated, order disconfirmed** | Tracking: the crossover read at its own corner at 800 / 2500 / 8000 Hz gives −0.001 / −0.001 / −0.000 dB — the same number at all three, so the corner moved with the macro. 48 kHz, cpython | The order clause has no planted fault because the class does not claim it (see verdict) | The order is disconfirmed in **both** halves and the class says so in its docstring: the audio path is LR4 (−6 dB at the corner, 24 dB/octave) because HF-only mode sums the two halves, and the detector is `sidechain_poles=2`, a cascade of two one-poles, −6 dB at its corner and 10.31 dB/octave measured by Phase 1 (`upstream-diff.md:1035-1037`). Cause: no filter order satisfies D2 and D8 at once (dossier A-D1); §8.3 took the only direction the palette allows. |
| D3 | Two modes: broadband moves both bands together; HF-only leaves the low band alone | **demonstrated** | SPLIT under reduction, `sibilant_-6`, Range 12, Sensitivity 34, 48 kHz, cpython: broadband high **−9.580** low **−9.574** (0.006 dB apart, bar 0.5); HF-only high **−9.179** low **−0.000** (bar 0.25) | The low band routed into the gain cell in HF-only mode — broadband wearing HF-only's label — moves the low band **−21.827 dB → RED** | *"−0.000 dB is a rounding artefact of the DFT bin."* The same bin reads −21.827 dB on the fault, so it is not blind. *"The two modes could be the same graph."* They measure 9.2 dB apart on the low band. |
| D4 | Release is a straight line in dB at 925 dB/sec, 12 dB in 13.0 ms within 10 % | **rate demonstrated, shape disconfirmed** | GAINTRACE on a 200 Hz carrier with a 6 kHz burst, hop 2.5 ms — exactly half a period of the carrier, so the RMS window reads the gain and not the waveform — 48 kHz, cpython, at the 3.5 ms Release default: **7.01 dB of an 8.12 dB recovery in 7.50 ms = 935 dB/sec against the 902's 925, 1.1 % away**, inside the trait's own 10 %. The **shape** departs from a straight dB line by **0.82 dB** at its worst | The shape half needs no planted fault because it *is* the fault-detector: the assertion is `deviation > 0.3 dB`, so the test goes red the day the trace becomes straight — which is what N-DEESS-2 landing would do | *"The curve is the measurement's own hop."* At a 1 kHz carrier and a 0.1 ms hop the same rig read 23.5 ms for a recovery that takes 7.5, and at a 1 kHz carrier at Sensitivity 36 it read no recovery at all because the carrier itself was being ducted — both were the method's error, and both are why the carrier is 200 Hz at a Sensitivity that leaves it alone. *"An exponential could be tuned straight."* It cannot: a one-pole in linear gain is a curve in dB at every coefficient. Cause of the disconfirmation: no dB-linear release on the palette (N-DEESS-2). |
| D5 | Attack is program-dependent: time to 63 % shortens with the overshoot, ratio ~3.3 within 25 % | **direction demonstrated, ratio disconfirmed** | GAINTRACE, balance held and programme level raised 10 dB at a time, Sensitivity 23.5, Range 6, 48 kHz, cpython: t63 **4.424 → 3.494 → 2.458 ms** across 20 dB, a ratio of **1.80** against the trait's 3.3 ± 25 % | A fixed attack coefficient gives one time at every overshoot; the direction is the fault's own contrapositive, and the depths staying within 0.11 dB across the same 20 dB is D1 measured a second way | *"The axis is wrong — sensitivity should be the axis."* It was tried: t63 2.476 / 2.471 / 2.031 ms at overshoot 0 / +10 / +20 dB, i.e. flatter still. That is the finding: `program_attack` scales by `sqrt(level / db_to_gain(threshold_db))`, an **absolute** overshoot, while `relative_threshold` has moved the gain computer to a relative one, so the two options do not compose. Node ask **N-DEESS-7**. |
| D6 | RMS detection: sine and square of equal RMS within 0.5 dB | **unmeasurable as stated; the option is demonstrated** | XF, 48 kHz, cpython, split at 800 Hz so the whole tone is in the band. The dossier's own pair, `sine_1k_-6` against `square_1k_-6_rms`, reads **0.408 dB apart** — inside its 0.5 dB bar. **It cannot be cited**: the same reading with `detector="peak"` is **0.457 dB**, so it tells an RMS detector from a rectifier not at all, and a green result on it is absence reading as agreement. What is measurable: `sine_1k_-14` against `train10_1k_-14_rms`, a 10 %-duty train of the same RMS, separates by **4.958 dB on RMS and 3.538 dB on peak — 1.420 dB from the option alone** | `detector="peak"` is the fault, and the point of the row is that it moves the *discriminating* pair by 1.420 dB and the stated pair by 0.049 dB. Both numbers are asserted, so the day either changes this test says so | *"D6 passes — 0.408 is under 0.5."* That is the trap. The cause is in the C: with `relative_threshold` on, the full-band level the gain computer subtracts is `fabsf(sense)` peak-followed **whatever `detector` says** (`audioif_dynamics.c:594-600`), so `detector` governs the band level only, and a matched-RMS sine and square can never come out equal — their peaks differ by 3 dB and the reference is a peak. Node ask **N-DEESS-8**. |
| D7 | Range bounds the reduction, never exceeded; unity with no sibilant | **bound demonstrated, "within 0.5 dB" disconfirmed** | LEVEL/GAINTRACE on `sibilant_-6`, Sensitivity 44 (≈21 dB past the balance), 48 kHz, cpython: Range 5 → **−4.774**, Range 10 → **−9.384**, Range 20 → **−17.682**. Never exceeded, never reached. Resting gain on a 200 Hz tone with no sibilant: **−0.0009 dB** at the Sensitivity a patch uses (30); **−5.0085 dB** at the 44 the Range clause needed, which is the control working and is recorded rather than tidied away | The Range blend removed — the wet path at unity with no dry beside it, which is the third defect of §7 — takes a 5 dB Range to **−29.356 dB → RED** | *"An asymptote is not a bound."* It is: `1 - alpha` of the dry signal is in the sum at every setting, so `-20*log10(1 - alpha)` is a hard ceiling on the reduction, and all three measurements sit under it. What is disconfirmed is the *equality*: reaching within 0.5 dB of a 20 dB Range needs about 44 dB of excess, which no reachable setting supplies. Cause: `dynamics_gain_db()` bounds nothing above threshold (`audioif_dynamics.c:365-404`) and `audiomixer` clamps a voice level to 0..1 (`audiomixer.py:143`), so a hard clamp is not buildable. Node ask **N-DEESS-6**. |
| D8 | The audio path sums flat within 0.25 dB from 20 Hz to min(20 kHz, 0.45·rate) | **demonstrated** | SPLIT, HF-only at Range 0 (the crossover's own sum), steady sines at a quarter, one and two times the corner, three corners, 48 kHz, cpython: **0.000 dB at every one of the nine points** | One Butterworth section a side instead of two — the LR2 pair the dossier's A-D1 derives — reads **−29.348 dB at the corner → RED** | *"The measurement cannot see a null."* It reads −29.3 dB on the fault. *"Broadband mode is not being checked."* Broadband mode has no sum to check: it never splits the audio, and its flatness is WIRE's byte-identity, which is stronger than 0.25 dB. |

**Characters:** none.

**Refutation pass.** Run by this session, 2026-09-07, against the six
demonstrated verdicts. Each argument above was tried as a way to make a
green reading meaningless — a blind measurement, a tolerance too loose, a
second cause for the same number — and each is answered with a run rather
than an assertion. What it could not break: D1, D3, D8 and D7's bound. What it did break,
and which is why five rows carry split or negative verdicts: D2's order
clause, D4's shape, D5's ratio, D7's equality — and **D6 entirely**, which
had been written up as demonstrated on a 0.408 dB reading until the same
measurement was run with the detector faulted and returned 0.457 dB. That
one is the pass this session came closest to shipping.

---

## 2. Tier 1 invariants

Command for every cell:

```
PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_deesser.Tier1 -v
```

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`. The mp and cpy columns are the kit
spec's split — rendered there through `tools/render_effect.py`, analysed
here — and each names the probe the reading was taken on. **Read them
precisely:** `identical` means that probe's render is byte-for-byte the
CPython one, so the invariant CPython measured on those bytes holds on
those bytes there too. It is not a claim that the invariant's *own*
measurement ran under MicroPython, because the kit's analysis is numpy and
does not (kit spec §1).

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass, residual 0 | identical | identical | pass, residual 0 | identical | identical | pass, residual 0 | not rendered | not rendered |
| Range 0 is a wire, byte-identical to the source | WIRE | pass, 0 of 47104 samples differ | identical, **and equal to the source** | identical, **and equal to the source** | pass, 0 of 45056 | identical, equal to source | identical, equal to source | pass, 0 of 22528 | not rendered | not rendered |
| Level-honest: unity through the dry path | LEVEL | pass, −0.0009 / −0.0015 dB | not rendered | not rendered | pass, same | not rendered | not rendered | pass, same | not rendered | not rendered |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass, 0 measured / 0 reported; tail 170 max against 256 declared | identical | identical | pass, 0 / 0; tail 156 | identical | identical | tail 78 | not rendered | not rendered |
| `reset()` leaves every node silent and the borrowed source untouched | STATE | pass, **residual 0 LSB** | see §11 | see §11 | — | — | — | — | — | — |
| `deinit()` releases every node and leaves the source rendering | STATE | pass, `live_nodes_after_deinit: []` | — | — | — | — | — | — | — | — |
| `capabilities` names exactly what is honoured | STATE | pass, `()` and no transport read | — | — | — | — | — | — | — | — |
| Pulling `output` allocates nothing | STATE | pass, **−204736 bytes** across 200 single-block pulls | — | — | — | — | — | — | — | — |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass, mono WIRE 0 of 23552 | — | — | — | — | — | — | — | — |

**Where the mp and cpy cells come from**, so nothing is inferred that was
not run. Each invariant's own probe, at its own setting, was rendered on all
three interpreters and its digest compared — not the default-patch renders
of §3:

| Invariant | Probe and setting | Rate | cpython | micropython | circuitpython-effects |
|---|---|---|---|---|---|
| WIRE | `ramp_fs --macro 1=0` (Range 0) | 48000 | `aef0fa61` | `aef0fa61` | `aef0fa61` |
| WIRE | `ramp_fs --macro 1=0` | 44100 | `aa6aeabd` | `aa6aeabd` | `aa6aeabd` |
| CLICK | `impulse --macro 1=0` | 48000 | `fcab2ba1` | `fcab2ba1` | `fcab2ba1` |
| CLICK | `impulse --macro 1=0` | 44100 | `06a09e61` | `06a09e61` | `06a09e61` |
| TAIL | `burst_silence`, patch 0 | 48000 | `6606e1ed` | `6606e1ed` | `6606e1ed` |
| TAIL | `burst_silence`, patch 0 | 44100 | `cd9035b4` | `cd9035b4` | `cd9035b4` |

The WIRE rows are the strongest of the six: `aef0fa61` and `aa6aeabd` are
also the **source** digests the CPython WIRE measurement reports
(`source_fnv1a`), so "byte-identical to the source at Range 0" is shown
directly on MicroPython and on the patched CircuitPython, not carried over
from CPython by an argument. LEVEL has no mp/cpy row because its subject is
a generated tone rather than a kit probe, and the renderer takes probes.

**Rate honesty, in full.** The Frequency span tops at 8 kHz, which is below
Nyquist at all three rates, so it never clamps: the macro at 127 reads
8000.0 Hz at 48 000, 44 100 and 22 050 Hz. The clamp is still shown to
exist — `_hz(1e9)` returns 23520.0 / 21609.0 / 10804.5 Hz, which is
0.98·Nyquist at each — so the invariant is demonstrated rather than
vacuously true.

**Tail, measured rather than declared.** Broadband mode has no tail at all:
the audio never enters a filter, and TAIL finds no non-zero sample after the
burst at any of the three rates. HF-only mode is the crossover, and its tail
is longest at the bottom of the Frequency span:

| corner | 48 kHz | 44.1 kHz | 22.05 kHz |
|---|---|---|---|
| 800 Hz | 170 samples (3.54 ms) | 156 (3.54 ms) | 78 (3.54 ms) |
| 2500 Hz | 51 (1.06 ms) | 47 (1.07 ms) | 23 (1.04 ms) |
| 8000 Hz | 14 (0.29 ms) | 15 (0.34 ms) | 16 (0.73 ms) |

Every one reaches **exact zero**, residual 0 LSB. `TAIL_SAMPLES = 256` is
one node block, declared as a bound over the 170-sample worst case.

**Mono.** The dossier's §4 says a mono source gets identical processing and
the same graph. Measured: at `channel_count` 1 the class builds, reports
`channel_count == 1`, and Range 0 is byte-identical over 23552 frames
(`render_fnv1a 7bbcbf39` against `source_fnv1a 7bbcbf39`).

**Planted faults for this block**, each with its clean control in the same
test:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | the dry voice at 32767/32768 on `ramp_fs` | green, 0 differing | **RED**, 23552 of 47104 samples differ, first at frame 0 channel 1, max 2 LSB |
| TAIL | +1 LSB held in the settled state | green, residual 0 | **RED**, `returns_to_zero: False`, residual 1 LSB, "tail" 143901 samples |
| CLICK | `latency_samples` reported 256 short, DSP unchanged | green, error 0.0 samples | **RED**, error 256.0 samples, audio digest unchanged (`01ccc3a1` both) |
| STATE | the reset walk without the ring flush — what the class did before `_reset_chain` existed | green, residual **0 LSB** | **RED**, residual **2150 LSB** |

Nodes this class enumerates with `self._own()`, in build order: `out`
(mixer), `pre` (mixer), `duck` (`audiodynamics.Dynamics`), `highs[1]`,
`highs[0]`, `lows[1]`, `lows[0]` (`audiobiquad.Biquad`), `band`, `raw`,
`top` (`audioroute.Splitter`), `adapter` (`audioroute.MidSide`), plus the
`tail` MidSide registered first. STATE was handed that list explicitly and
reported nine deinitialisable nodes, all `[]` live afterwards — see §11 for
why the list is passed rather than discovered.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, per probe, per rate, at source block 256.
`sum(data)` is printed beside it and is never the comparison.

```
PYTHONPATH=lib .venv/bin/python tools/render_effect.py DeEsser <probe> out --rate <rate>
MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython tools/render_effect.py ...
MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects -X heapsize=256M tools/render_effect.py ...
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 256 | `7b54b825` (sum 91883162) | `60e704cb` (sum 91883156) | `60e704cb` (sum 91883156) | *(board run)* | *(board run)* |
| `chord` | 44100 | 256 | `e92754bd` (sum 84171808) | `6be3d64e` (sum 84171805) | `6be3d64e` (sum 84171805) | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | `bd6dc40f` | `bd6dc40f` | `bd6dc40f` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 256 | `9a8b3694` | `9a8b3694` | `9a8b3694` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | `4af3f995` | `4af3f995` | `4af3f995` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 256 | `11f4f8af` | `11f4f8af` | `11f4f8af` | *(board run)* | *(board run)* |
| `sibilant_-6` | 48000 | 256 | `bdf58cfc` | `bdf58cfc` | `bdf58cfc` | *(board run)* | *(board run)* |
| `sibilant_-6` | 44100 | 256 | `995d32a2` | `995d32a2` | `995d32a2` | *(board run)* | *(board run)* |

**Desktop agreement: yes on three probes of four, and the fourth's cause is
not the class.** MicroPython and the patched CircuitPython are byte-identical
to each other on **every** row, and identical to CPython on `noise_det`,
`sweep_log` and `sibilant_-6` at both rates. On `chord` CPython differs from
the other two by **6 samples of 288000 at 48 kHz and 3 of 264600 at
44.1 kHz, every one of them 1 LSB** (first at frame 3040, channel 1:
−5354 against −5355).

**The cause, reproduced without this class in the graph.** `audiomixer` is a
pure-Python shim on CPython — `int(value * (multiplier / 32767.0))`,
`audiomixer.py:143-160` — and CircuitPython's own C module on the other two.
Feeding one deterministic xorshift signal through a bare
`audiomixer.Mixer` at voice level 0.7488113568490 (the class's own `alpha`
at Range 12) and hashing the result:

```
$ .venv/bin/python  scratch/mixdiff.py   ->  mixer-only digest 97cde075
$ ../cmods/bin/micropython scratch/mixdiff.py -> mixer-only digest f85018ba
   audiomixer alone: 1 of 15360 samples differ, max |delta| 1
```

So the divergence is the mixer's last-bit rounding at a fractional voice
level, present with no `DeEsser` anywhere, and it shows on `chord` and not
on the other three because `chord` is the only probe dense enough to land a
scaled sample on a rounding boundary. That is a recorded cause that is not
the class. It is also why `sum(data)` is never the comparison: the sums
differ by 6 and 3, which a byte-sum could have hidden entirely.

**Board agreement:** not taken — §4 and §11.

**Block-size ladder:** not run. The class's traits do not ask for one, and
the guard against the failure it exists to catch — a Splitter's 8192-frame
ring overrun by a longer source — is structural here rather than measured:
the class's own `audioroute.MidSide` adapter re-blocks every source to
256 frames before the first Splitter, and the renderer's `--block` check
would have refused a render that did not.

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
target `effect:DeEsser`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: ESP32-P4 8 % of one stereo block's real-time deadline,
ESP32-S3 15 %; lean patch expected: no.

What the board run should expect to find, from the graph rather than from a
figure copied out of the Phase 1 node table: four audio-path biquads (only
HF-only mode routes audio through them, but broadband still runs them,
because a mixer voice at level 0 still pulls its source), two side-chain
one-poles inside `Dynamics`, one RMS detector, one full-band detector, one
VCA, three `Splitter` rings, two `MidSide` identities and two `Mixer`s. If
the S3 misses its budget the next lever named in the dossier is a
construction-time Mode rather than a lean patch.

| Board | Patch | Settings | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("DeEsser", …)` | 562.7 | 1.777 (1.464 marginal) | 3.00 | 115 KB | **no** — 27.5 % marginal, 33.3 % total, against 8 % |
| S3 | 0 | construction defaults, `audioeffects.create("DeEsser", …)` | 314.0 | 3.184 (2.711 marginal) | 1.67 | 115 KB | **no** — 50.8 % marginal, 59.7 % total, against 15 % |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:DeEsser`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 8 %, S3 15 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`a4d62601c70389fb` on the ESP32-P4 and `a4d62601c70389fb` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is the **same value**.

**Owed: a `" - lean"` patch.** At 50.8 % of the deadline the class is over
its ESP32-S3 budget of 15 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** the HF-only / broadband Mode split; only construction defaults were run.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


---

## 5. Latency

Reported `latency_samples` = **0**. Measured click delay against the dry
path, per channel, `impulse` probe, Range 0:

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0.0, 0.0 (both channels) | 0.0 | 0.0 |
| 44100 | 0 | 0.0, 0.0 | 0.0 | 0.0 |

Dossier latency budget: zero samples, and no option may add any. **Met.**

**Every latency-adding option:** there are none. The class ships no
look-ahead, no oversampling and no delay line; `audiodynamics`' own
`lookahead_ms` is left at its default of 0 and is not exposed as a macro or
a constructor argument, because a de-esser that ducked before the "s"
arrived would be a fault. There is therefore nothing to name in
milliseconds in the docstring, and the docstring says so.

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none)* | — | 0 | — | the docstring states that no option adds latency |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
CLICK **RED at both rates**, error 256.0 samples, audio digest unchanged
(`01ccc3a1` in the clean and faulted reads alike, which is what says the
fault moved the *claim* and not the audio).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 800 Hz … 8 kHz, log | 902 Frequency (12 o'clock = 2.5 kHz) |
| 1 | Range | UNIPOLAR | 0 … 20 dB | 902 Range |
| 2 | Sensitivity | UNIPOLAR | 0 … 48 dB below the full-band level | the 902's fixed internal comparison, made adjustable |
| 3 | Mode | TOGGLE | broadband / HF only | 902 Mode switch |
| 4 | Release | UNIPOLAR | 1 … 200 ms, log | the 902's fixed 925 dB/sec, as a time constant |
| 5 | Attack | UNIPOLAR | 0.1 … 10 ms, log | the 902's program-dependent rate, as its base coefficient |
| 6 | Listen | TOGGLE | off / on | no panel control; the detector's own band on the output |

Seven of a possible sixteen. The 902 has two knobs and a switch; the other
four are behaviours it specifies and hides, exposed under vision D2.

| Patch | Name | What it is for |
|---|---|---|
| 0 | Vocal | the constructor's defaults on the grid: 2.5 kHz, Range 12 dB, Sensitivity 30, broadband, Release 3.5 ms, Attack 2 ms |
| 1 | Bright Vocal | frequency and range up, for a bright or close-miked take |
| 2 | Whispered Verse | sensitivity and range down, so a quiet take is not over-worked |
| 3 | Guitar Pick Noise | the manual's own instrumental case: HF only, frequency high, fast |
| 4 | Cymbal Edge | HF only, higher still, more range |
| 5 | Hard De-Ess | range at maximum |

Patch 0 round-trips to the constructor's own defaults: the class built with
no arguments reads `[2500.0, 12.0, 30.0, 0.0, 3.5, 2.0, 0.0]` and after
`program_change(0)` reads `[2506.99, 11.97, 29.86, 0.0, 3.496, 2.028, 0.0]`
— the same settings on the 7-bit grid.

`patch_index` is 0 on a fresh instance, 4 after `program_change(4)`, and
`None` after any macro move: shown by
`tests/test_cpython_effects_deesser.py::Tier1::test_patch_index_follows_the_contract`.

**`capabilities` = `()`.** The dossier's one-line reason, quoted: *sibilance
has nothing to do with tempo.* Nothing in the class reads
`self._transport()`, and STATE confirms the declaration is `[]`.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad", "audiodynamics",
"audioroute")`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Dynamics(relative_threshold=1)` | `audiodynamics` | D1 | `audiodynamics` is not a CircuitPython module at all (`upstream-diff.md:661`), and the option is Phase 1's own: a stock board has no gain computer that compares two levels |
| `Dynamics(detector="rms", rms_ms=…)` | `audiodynamics` | D6 | same module; the ported palette's only follower is a rectifier |
| `Dynamics(sidechain_poles=2)` | `audiodynamics` | D2, detector half | same module |
| `Dynamics(program_attack=1)` | `audiodynamics` | D5 | same module |
| `Biquad(LOW_PASS/HIGH_PASS)` ×4 | `audiobiquad` | D8, and the Tier 1 tail | `synthio.Biquad` keeps its state in Q12 and lands on fixed points, so its tail does not reach zero (audioif#23); this class's tail invariant would be unmeetable on it |
| `Splitter` ×3, `MidSide` ×2 | `audioroute` | the parallel routing, the block adapter and the non-mixer tail | not a CircuitPython module (`upstream-diff.md:661`); `MidSide` has no ancestor anywhere |

`audiomixer` and `audiocore` are ported CircuitPython and cost no tier
claim.

```
PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
```

```
Ran 7 tests in 0.058s

OK
```

The class appears in that battery automatically — it walks
`audioeffects.ALL` and `rebuilt.known()` — so a tier claim here that
`DeEsser.TIER` does not match is a test failure, not a wrong sentence in a
document.

**What that test does not prove.** Blocking a module in `sys.modules` is
not a board without the module. No stock CircuitPython interpreter exists in
this workspace, so no stock-tier class has been shown rendering on a stock
CircuitPython build of the ported C. That is a gap in the method rather than
in this class — and it does not touch this class's own claim, which is the
opposite one: that it needs audioif and refuses to build without it.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured.
- [x] Every Tier 1 invariant is green on CPython at 48 kHz, 44.1 kHz and
      22.05 kHz; on MicroPython and the patched CircuitPython the renders are
      byte-identical to CPython's at 48 kHz and 44.1 kHz, which carries them.
      **22.05 kHz was not rendered on mp or cpy — §11.** Every Tier 2
      measurement names its rate.
- [x] Every demonstrated Tier 2 trait has a measurement, and that
      measurement was shown red on a planted fault of the same kind — which
      is how D6 stopped being one of them: its reading sat inside its bar
      and its fault did too, so it is `unmeasurable` rather than green.
- [x] Every demonstrated trait survived a refutation attempt, recorded with
      the argument and the answer (§1, last column). **The refuter was this
      session, not an independent agent — §11.**
- [ ] CPython and desktop MicroPython render identical bytes on the probe
      material — see §3 for the one probe where they do not and its cause.
      The P4 and S3 digests are **not taken**.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 27.5 % and S3 50.8 % of the deadline (marginal) against 8 % / 15 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the latency budget is met; no option adds latency and the
      docstring says so.
- [x] The class declares seven macros and five named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython suite, this class's
      own battery, the portability-tier test, the three-interpreter smoke and
      flake8 all pass — §9.
- [ ] The README catalogue row: **the README has no per-class catalogue** to
      add a row to (checked: `grep -n -i "de-esser\|Dynamics" README.md`
      returns one line, a directory description). The docstring carries the
      standout, the tier and the cost in a musician's terms; the catalogue
      rewrite is Phase 2's own Gate item, not this class's.
- [ ] The code, this file and the CHANGELOG line did **not** land in one
      commit — §11.

One item outside the class's own gate, recorded because it touched a shared
file: `tests/test_rebuilt_registry.py`'s three "nothing is rebuilt yet"
assertions are rewritten so they survive a rebuild — see §9.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_deesser -v
Ran 24 tests in 640.221s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 251 tests in 223.930s

OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.058s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ PYTHONPATH=lib .venv/bin/python -m flake8
exit 0
```

The smoke was 46 classes and 83 patches before this class; `DeEsser`'s six
take it to 88, on all three interpreters. The suite was 227 tests at the
foundation's head and is 251 with this class's battery.

**One shared test file had to change, and it is worth naming.**
`tests/test_rebuilt_registry.py` held three assertions written for the
moment before any class was rebuilt — "every one of the 46 is a miss
today", `known() == ["ExampleAudioif", "ExampleStock"]`, and "no name in
`known()` is among the 46". All three go red the instant *any* class lands,
so each of Phase 2's sixteen would have had to edit them in turn — a shared
file to conflict over, in the one test file whose subject is that the
registry rule leaves no shared file to conflict over. They are rewritten to
the invariant that does not expire: a name with a module under `rebuilt/`
resolves to a Component carrying that NAME, a name without one misses, the
catalogue is 46 either way, and the two *fixtures* are what must stay out
of it. `Ran 14 tests in 0.064s / OK`.

The board leg, taken on both boards on 2026-09-07 (§4):

```
$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:DeEsser")'
ROW	effect:DeEsser	562.7	3.00	1.777	0.313	1.464	118160	a4d62601c70389fb
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:DeEsser")'   # the S3
ROW	effect:DeEsser	314.0	1.67	3.184	0.473	2.711	118144	a4d62601c70389fb
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

- **It was the de-esser RaneNote 155 draws as the wrong one** — a
  `DYN_COMPRESS` with a fixed `threshold_db=-30.0`, so identical sibilance
  got 10.57 dB of reduction at −6 dBFS and none at −20 dBFS. The rebuild
  uses `relative_threshold=1` and measures 0.772 dB of spread across 49 dB
  (D1); planting the old behaviour back reproduces the old defect exactly
  (7.252 dB of spread), which is the fault beside D1.
- **No surface** — `MACRO_LABELS = ()`, one unnamed patch, and frequency,
  threshold, ratio, attack and release construction-only. The rebuild
  declares seven macros and six patches (§6).
- **No maximum** — `ratio=6.0` bounds nothing, so a loud sibilant on a quiet
  track could duck the whole signal. Range is now a hard ceiling on the
  reduction: `1 - alpha` of the dry signal is always in the sum, and
  removing it takes a 5 dB Range to −29.6 dB (D7's fault).
- **Broadband only** — the 902's HF-only mode was unreachable because the
  class never split the audio. It is macro 3 now, and it moves the low band
  by −0.000 dB (D3).

The old class stands untouched in `lib/audioeffects/dynamics.py`; the
registry rule serves `DeEsser` from `rebuilt/deesser.py` without either
module being edited.

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 27.5 % and S3 50.8 % of the deadline (marginal)
  against 8 % / 15 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **22.05 kHz was not rendered on MicroPython or CircuitPython.** The
  cross-interpreter matrix covers 48 kHz and 44.1 kHz on all three; the
  22.05 kHz leg is CPython only. The gate asks for all three rates on all
  three interpreters.
- **The refutation pass was not independent.** The template asks for a
  separate agent given one trait and told to break it; §1's last column is
  this session arguing against its own readings. That is weaker evidence and
  the arguments are written out so someone else can attack them.
- **`reset()` and `deinit()` were exercised on CPython only.** STATE is a
  numpy measurement and does not run on the other two interpreters; the
  ring-flush routine `_reset_chain` uses only calls that exist on all three
  (`audiocore.get_buffer` with one argument, `MixerVoice.play`), and the
  smoke builds and renders the class on both, but nobody has *measured* a
  reset there.
- **The kit's `enumerate_nodes` finds nothing on this class.** It walks an
  effect's public attributes and every node here is private, so left to
  itself STATE's deinit leg would have passed on an empty list — an
  absence reading as agreement. The battery passes the node list explicitly
  and says so; the kit should probably read `_nodes` when a class is a
  `_component.Component`.
- **A `Splitter`'s ring cannot be cleared through any public API on any
  target**, so `reset()` has to push it empty against a silent sample. That
  works and is measured at 0 LSB, but it is a workaround for a missing
  `Splitter.clear()`, and the whole structure disappears if N-DEESS-6 lands
  (broadband mode would need no splitter at all).
- **Four node asks are open and unfiled as issues**: N-DEESS-2 (a dB-linear
  release, which is D4's shape), N-DEESS-6 (a floor on the reduction above
  threshold, which is D7's equality), N-DEESS-7 (`program_attack` should
  read the same overshoot the gain computer does when `relative_threshold`
  is on, which is D5's ratio) and N-DEESS-8 (`detector="rms"` should govern
  the full-band reference too, which is D6 entire). They are written up in
  `DeEsser.md` §5 and have no audioif issue numbers yet — this session ran
  in an isolated worktree beside fifteen others and did not file into a
  shared tracker on its own.
- **D6 has no measurement this class can cite.** The dossier's criterion
  reads inside its own bar and does not discriminate, so the trait is
  neither demonstrated nor honestly disconfirmed — it is unmeasurable on a
  relative-threshold class until N-DEESS-8 lands. What replaced it in the
  battery is a weaker claim: that the option is active.
- **The code and this file did not land in one commit.** The gate asks for
  one; this is three — `4dfe59b` (the dossier at Station A), `0f936b2` (the
  class and its battery) and `62364f3` (this file, the CHANGELOG line, and
  the two readings Station C had to correct in the class itself). The
  station pattern the roadmap sets out asks for a commit per station, and
  the gate asks for one commit for the class; they do not agree, and this
  session followed the stations.
