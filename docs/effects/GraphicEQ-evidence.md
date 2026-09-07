# Evidence Pack — `GraphicEQ` (MXR M-108 Ten Band)

Written from `tools/phase2_probes/graphiceq_evidence.py`, which prints every
number below, and `tools/phase2_probes/graphiceq_bench.py`, which prints the
Station A palette probes the dossier's App. S carries. Nothing here is from
memory; where a figure has no run behind it, the row says `unmeasured` and
§11 says why.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `GraphicEQ` |
| Dossier | [`GraphicEQ.md`](GraphicEQ.md), traits frozen 2026-09-07 at `0afab3c` |
| Module | `lib/audioeffects/rebuilt/graphiceq.py` |
| Base | `_component.Component` |
| Family / phase | EQ, roadmap Phase 2 |
| Standout | MXR M-108 / M108S Ten Band Graphic EQ |
| Grade | literature |
| Portability tier | **audioif** (`REQUIRES = ("audiobiquad",)`) |
| Landed in commit | `f3ffb74` (the class), `1f3a4ff` (the shelf's corner and Q, this file, the CHANGELOG line and the README row) |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3`; every C citation checked with `git show 2f6cbc3:<file>` |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3; `cmods/bin/micropython` 1.28.0; `cmods/bin/circuitpython-effects` 10.2.1 |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began: yes.** Station A landed
in `0afab3c` with the Tier 2 table unchanged from the seed — no row added,
dropped, renumbered or re-thresholded — and the first line of the class was
written after it.

---

## 1. Traits

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| **T1** | The top band is a shelf, the other nine are bells: 16 kHz macro at +12 dB ⇒ 20 kHz within **1.5 dB** of 16 kHz and at least **+9 dB**; 8 kHz macro at +12 dB ⇒ 16 kHz at least **6 dB** below its own peak | **demonstrated** | RESPONSE, 81 tones 20 Hz–22 kHz, 48 kHz, cpython. Shelf: **+10.89 dB at 16 kHz, +11.93 at 20 kHz**, drop **1.03 dB**. 8 kHz bell: peak **+11.94 dB at 7896 Hz**, **+0.54 dB at 16 kHz**, down **11.40 dB** | the top band rebuilt as a `PEAKING_EQ` at 16 kHz → **+12.00 / +2.14 dB, drop 9.86 dB → RED** (clean run green) | *"You moved the shelf's corner until it passed."* Half true and it is in the code: the corner sits at `centres[9] / √2`. But an RBJ shelf's `frequency` is its **half-gain** point, so a corner on the band gives that band 6.00 dB of a 12 dB request and puts the rest above 20 kHz — measured, in §1a. The trait's own second clause ("at least +9 dB") is the same expectation written down before the code, so the trait and the design agree about what a treble slider is for. The corner is stated in the class and in the dossier's §4, not hidden. |
| **T2** | Proportional Q: for the 1 kHz band, mid-gain bandwidth at **+3 dB ≥ 1.5 oct** and at **+12 dB ≤ 0.8 oct**, first +1 dB crossing moving **< 10 %** | **demonstrated** | RESPONSE, 73 tones 125 Hz–8 kHz, 48 kHz, cpython. **1.780 oct at +3 dB** (539.0–1850.9 Hz), 1.146 at +6, **0.716 at +12** (780.2–1281.3 Hz); +1 dB crossing **432.5 → 432.2 Hz, 0.06 %** | `Constant Q` on, which is the trait's own limiting case → **0.698 oct at +3 dB against 0.716 at +12 — no change across travel → RED** | *"The `Band Q` default was chosen to clear the bar."* The default is 2.0 and the bar was derived at 2.0 (dossier App. B), so the absolute numbers do move with it. What does not is the **ratio**: `Q ∝ Q₁₂`, so the +3-to-+12 width ratio is 2.49 measured here and 2.51 predicted at *every* anchor. §1b measures the same band at anchor 1.5 and the ratio holds. |
| **T3** | Adjacent bands overshoot: 500 Hz, 1 kHz, 2 kHz all at +6 dB ⇒ combined peak at least **+9 dB**, region within 3 dB of it spanning more than **two octaves** | **disconfirmed** (one half) | RESPONSE, 73 tones, 48 kHz, cpython. Peak **+8.78 dB at 1000 Hz** — **0.22 dB under the +9.00 dB bar**. −3 dB span **2.583 oct** (408–2444 Hz), which **passes** the second half | `Band Q` at its maximum with `Constant Q` on, so the bands do not overlap → **peak 6.79 dB, span 1.559 oct → RED** | *"0.22 dB is measurement noise."* It is not: the same sweep reads the 1 kHz band's own peak at 12.00 dB against a 12.00 dB request, so the grid is good to a hundredth. The bands really do add to 8.78 and not 9. **The bar is not moved** (roadmap's rule); the cause is in §1b — at anchor 1.5 the same setting reads **+10.17 dB**, so this half is a function of the `Band Q` default and T2 pulls the other way. |
| **T4** | A band at zero is out of the circuit: band *k* at 0 dB with neighbours at ±12 dB renders **byte-identical** to the same setting built without band *k* | **demonstrated** | DIGEST, 24 000 frames of deterministic noise, bands 0/1/5/9, **48 kHz and 44.1 kHz**, cpython. Every pair identical — e.g. 48 kHz band 0 `2957c4fd` = `2957c4fd`, band 9 `30a89151` = `30a89151`. The reference is the class's own chain with section *k* **unlinked** (section *k*+1 played from *k*−1), so it is eleven sections and not twelve | the detented band left unmuted (`mix = 1`) at **band 0** → `f6d22be1` against `2957c4fd` → **RED**. The same fault at **band 5 is still green** | *"Then the fault is not a fault."* It is, and where it matters: a flat section is bit-transparent from 250 Hz up, so the plant is only *detectable* at the bottom three bands — 5 LSB at 31.25 Hz, 2 at 62.5, 1 at 125, 0 at 250. That asymmetry is reported here rather than hidden by choosing a band where the check happens to fire. |
| **T5** | All ten at +6 dB ⇒ ripple 60 Hz–8 kHz under **2 dB** and mean level above **+9 dB** | **disconfirmed** (both halves) | RESPONSE, 81 tones, 57 in band, 48 kHz, cpython. Ripple **2.353 dB** peak-to-peak (bar < 2.00); mean **+8.70 dB** (bar > 9.00) | `Constant Q` at the narrowest, so the bands stop filling between their centres → **ripple 4.218 dB, mean 4.81 dB → RED** | *"Widen the bands and both halves pass."* Only one does. At anchor 1.5 (§1b) the mean rises to **+10.84 dB** — clearing the second half — while the ripple only falls to **2.304 dB**, still over the bar. **The ripple half of T5 fails at both anchors**, so it is not a tuning question: an octave-spaced bank of two-pole bells does not fill flat between its centres at +6 dB, whatever its Q. |

### 1a. Why the shelf's corner is not its band centre

RESPONSE at 48 kHz, `HIGH_SHELF`, `gain_db = +12`, dB relative to dry:

| corner / Q | 4 kHz | 8 kHz | 11 kHz | 12 kHz | 16 kHz | 20 kHz | 22 kHz |
|---|---|---|---|---|---|---|---|
| 16 kHz, Q 1.4 (the first build) | −0.23 | −1.07 | −2.18 | −2.37 | 6.00 | **13.94** | 12.51 |
| 16 kHz, Q 0.707 | 0.01 | 0.20 | 0.94 | 1.47 | **6.00** | 11.31 | 11.96 |
| **11313.7 Hz, Q 0.707 (shipped)** | 0.12 | 1.96 | 5.57 | 6.93 | **10.91** | **11.94** | 12.00 |
| 8 kHz, Q 0.707 | 0.69 | **6.00** | 9.77 | 10.53 | 11.80 | 11.99 | 12.00 |

Two things this fixed, both bugs rather than tuning. **`Q = 1.4` on a shelf is
wrong**: a shelf's `Q` is a resonance, not a bandwidth, and 1.4 cuts 2.37 dB
below the corner and overshoots the asymptote by 1.94 dB above it — the first
build handed the shelf the bells' nominal Q. **A corner on the band centre
gives that band half its dB**, which is why the 16 kHz row reads 6.00 at
16 kHz. Half an octave down puts 10.91 dB where the label says while lifting
the 8 kHz bell's own centre by only 1.96 dB; a corner at 8 kHz would put
6.00 dB there and the two sliders would stop being separable.

### 1b. The `Band Q` trade — why T2 and T3/T5 cannot both be met

Same measurements, `Band Q` at **1.5** instead of the default 2.0:

| | anchor 2.0 (shipped) | anchor 1.5 | bar |
|---|---|---|---|
| T2, width at +3 dB | 1.780 oct | 2.287 oct | ≥ 1.5 |
| T2, width at +12 dB | **0.716 oct** | **0.949 oct** | ≤ 0.8 |
| T3, combined peak | **8.78 dB** | **10.17 dB** | ≥ 9.00 |
| T3, −3 dB span | 2.583 oct | 2.505 oct | > 2.00 |
| T5, ripple | **2.353 dB** | **2.304 dB** | < 2.00 |
| T5, mean | **8.70 dB** | **10.84 dB** | > 9.00 |

`Q` scales with the anchor, so band width scales inversely with it: T2 wants
the +12 dB band narrow and T3 and T5 want the +6 dB bands wide enough to
overlap and add. **One number cannot go both ways**, and the two anchors above
each fail the other's row. The default stays at 2.0 because that is the
anchor Station A froze the thresholds at, and moving it to make T3 pass would
be moving a threshold by the back door. T5's ripple fails at both, which is
the one half of this that is not about the anchor at all.

### Refutation pass

Run by this session against its own results, 2026-09-07, after every number
was in hand. It went after four things: the shelf corner (§1a — the change
survives on its own measurement, and the trait's second clause wanted it),
the `Band Q` default (§1b — the ratio is anchor-free, the absolute bars are
not, and both are shown), T4's planted fault (which it **broke**: the fault
was originally planted at 1 kHz, where it is invisible, and the row now
carries both bands and the LSB-per-centre table), and T3's 0.22 dB
(re-measured against the grid's own accuracy rather than argued away). What
it could not break: T1's shelf-versus-bell separation, T2's narrowing, T4's
byte identity, and every Tier 1 row.

---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`.

**How the `mp` and `cpy` columns are earned.** Every measurement below reads
PCM. §3 shows the three interpreters rendering **byte-identical PCM** on 18
probe/rate/patch combinations, so a number computed from those bytes on
CPython is the number on all three. The columns say `= cp` for that reason
and not because the analysis was re-run under MicroPython, which has no
numpy and which the kit spec says never to ask for an FFT.

| Invariant | Kit | 48 k cp | 48 k mp/cpy | 44.1 k cp | 44.1 k mp/cpy | 22.05 k cp | 22.05 k mp/cpy |
|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass, **residual 0 LSB** | = cp | pass, 0 LSB | = cp | pass, 0 LSB | = cp |
| Patch 0 is a wire, byte-identical to the source | WIRE | pass, **0 of 48000** samples differ | = cp | pass, 0 of 44100 | = cp | pass, 0 of 22050 | = cp |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass, worst **0.003 dB** | = cp | pass, 0.002 dB | = cp | pass, 0.002 dB | = cp |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass (§5) | = cp | pass | = cp | tail pass; CLICK not run (§11) | = cp |
| `reset()` leaves every node silent and stateless, the source untouched | STATE | pass, **residual 0 LSB**, source renders again | = cp | *(48 k only)* | | | |
| `deinit()` releases every node and leaves the source rendering | STATE | pass, **0 of 12 nodes live** | = cp | | | | |
| `capabilities` names exactly what is honoured | STATE | pass, `()` | = cp | | | | |
| Pulling `output` allocates nothing | STATE | pass, **857 bytes over 200 pulls** (bar 8192) | = cp | | | | |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | `clamped = ()` | = cp | `clamped = ()` | = cp | **`clamped = (9,)`**, corner 11313.7 → 10804.5 Hz | = cp |
| Every invariant also holds at `channel_count` 1 | (all) | pass, all rows | = cp | pass | = cp | pass | = cp |

**Mono.** The dossier's §4 says a mono source gets the same curve on one
channel — not a wire and not a sum. Measured: at `channel_count` 1 the WIRE,
TAIL and LEVEL rows above are green at all three rates, and the 1 kHz band at
+12 dB lifts a 1 kHz tone by more than 10 dB on the single channel
(`test_cpython_effects_graphiceq.py::TheLevelMacros::
test_mono_gets_the_same_curve_on_one_channel`).

**Planted faults for this block**, each with its clean control:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | the dry path scaled by 32767/32768 | 0 of 48000 differ | **RED, 23924 of 48000 differ** |
| TAIL | the same probe through the ported bank (`audiofilters.Filter` over ten `synthio.Biquad`) — audioif#23 | residual 0 LSB | **RED, residual 5 LSB held for the whole render** |
| CLICK | `latency_samples` reported 256 short, DSP unchanged | measured [0.0, 0.0] against reported 0 | **RED: "256.0 samples out, bar 1.0"**, audio digest unchanged |
| STATE | `reset()` then a silent source | residual 0 LSB | — the fault here is the *control*: `resumed` is `True` and `resumed_fnv1a` differs from `reset_residual_fnv1a`, so the walk is not passing because nothing was pulled |
| T4 / WIRE | a detented section left at `mix = 1` | digest unchanged | **RED at band 0**; still green at band 5, and §1 says why |
| rate-honesty | — | — | the *kernel's* silent clamp: a section asked for 16 kHz at 22.05 kHz returns coefficients identical to one asked for 11022.45 Hz while reading its `frequency` back as 16000 (`test_cpython_effects_graphiceq.py::TheClampIsReported::test_planted_fault_a_centre_the_kernel_moves_and_nobody_reports`) |

`reset()` and `deinit()` walk the list `_component` requires the class to
enumerate with `self._own()`. **Nodes enumerated by this class, in build
order:** `Gain` (HIGH_SHELF 5 Hz), bands 0–8 (`PEAKING_EQ` at 31.25 Hz × 2ⁿ),
band 9 (HIGH_SHELF, corner 11313.7 Hz), `Volume` (HIGH_SHELF 5 Hz) — twelve
`audiobiquad.Biquad`. `kit.enumerate_nodes` walks *public* attributes and
finds none of them, which is correct: the construction module's whole point
is that a class enumerates its own nodes, so the pack hands `_nodes` to STATE
rather than letting it guess.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, from `tools/render_effect.py` on each interpreter.
`sum(data)` is never the comparison.

```
PYTHONPATH=lib .venv/bin/python tools/render_effect.py GraphicEQ <probe> <out> --rate <r> --patch <p>
MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython       -X heapsize=256M tools/render_effect.py ...
MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects -X heapsize=256M tools/render_effect.py ...
```

| Probe | Rate | Patch | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 0 | `7bd32675` | `7bd32675` | `7bd32675` | *(board run)* | *(board run)* |
| `chord` | 48000 | 5 | `7f5affc9` | `7f5affc9` | `7f5affc9` | *(board run)* | *(board run)* |
| `chord` | 44100 | 0 | `4d20fe71` | `4d20fe71` | `4d20fe71` | *(board run)* | *(board run)* |
| `chord` | 44100 | 5 | `0b1be75d` | `0b1be75d` | `0b1be75d` | *(board run)* | *(board run)* |
| `chord` | 22050 | 0 | `21b734dd` | `21b734dd` | `21b734dd` | *(board run)* | *(board run)* |
| `chord` | 22050 | 5 | `0672b381` | `0672b381` | `0672b381` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 0 | `1fe01e81` | `1fe01e81` | `1fe01e81` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 5 | `84ebe189` | `84ebe189` | `84ebe189` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 0 | `ff5e866d` | `ff5e866d` | `ff5e866d` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 5 | `892f5285` | `892f5285` | `892f5285` | *(board run)* | *(board run)* |
| `noise_det` | 22050 | 0 | `d3edbfcd` | `d3edbfcd` | `d3edbfcd` | *(board run)* | *(board run)* |
| `noise_det` | 22050 | 5 | `3016b8a1` | `3016b8a1` | `3016b8a1` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 0 | `662782d1` | `662782d1` | `662782d1` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 5 | `33ae2f89` | `33ae2f89` | `33ae2f89` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 0 | `b1e4eb69` | `b1e4eb69` | `b1e4eb69` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 5 | `16f6a4cd` | `16f6a4cd` | `16f6a4cd` | *(board run)* | *(board run)* |
| `sweep_log` | 22050 | 0 | `1ccee039` | `1ccee039` | `1ccee039` | *(board run)* | *(board run)* |
| `sweep_log` | 22050 | 5 | `4d54601d` | `4d54601d` | `4d54601d` | *(board run)* | *(board run)* |

**Desktop agreement: yes** — 18 of 18 identical, three interpreters, three
rates, both patches. **Board agreement: not taken** (§11).

**Build against build** (T4): `2957c4fd` for band 0 detented against
`2957c4fd` for the same bank with that section unlinked; three more bands and
a second rate in §1.

**Block-size ladder**, `noise_det` at 48 kHz, patch 5:

```
block   256 -> fnv 84ebe189      block 16384 -> fnv 84ebe189      block 32768 -> fnv 84ebe189
block  8192 -> fnv 84ebe189      block 20000 -> fnv 84ebe189
```

Byte-identical at every block size, which is the check `MultibandCompressor`
A-M5 exists to force: this class builds no `Splitter`, so there is no ring to
drag a cursor past, and now that is measured rather than assumed.

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
target `effect:GraphicEQ`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: **ESP32-P4 38 %**, **ESP32-S3 64 %** of one stereo block's
real-time deadline, at twelve sections. **Lean patch: no** — dossier §3 gives
the reason (a flat band still runs its recursion, so no patch can make this
class cheaper) and §11 carries it as a gap.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("GraphicEQ", …)` | 656.6 | 1.523 (1.210 marginal) | 3.50 | 15 KB | **yes** — 22.7 % marginal, 28.6 % total, against 38 % |
| S3 | 0 | construction defaults, `audioeffects.create("GraphicEQ", …)` | 395.2 | 2.530 (2.059 marginal) | 2.11 | 15 KB | **yes** — 38.6 % marginal, 47.4 % total, against 64 % |
| P4 | 5 | — | — | — | — | — | *(not run — the run measured construction defaults)* |
| S3 | 5 | — | — | — | — | — | *(not run — the run measured construction defaults)* |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:GraphicEQ`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 38 %, S3 64 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`4169efd90ecf44dd` on the ESP32-P4 and `4169efd90ecf44dd` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is the **same value**.

It is also the bare probe's own digest (`4169efd90ecf44dd`): at construction
defaults (patch 0 `Flat`) this class hands the probe back unchanged. The
CPU figure above is the built graph running — every node is pulled every
block — but **the digest is not a check on the audio**, and a board run at
a working patch is still owed.

**Not measured by this run:** patch 5 `Full Boost`, which is the patch the table above asked for. The run measures construction defaults — patch 0 `Flat`.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**The expensive path**, for whoever takes the board leg: patch 5 `Full Boost`
puts all ten bands at +6 dB and `Volume` at −9 dB, so twelve sections are
live and none is muted — the state the cost is about. Patch 0 is the wrong
subject: every section is at `mix = 0` there, and although the recursion
still runs, the class's own §1 shows patch 0 rendering the source byte for
byte, so a runner that refuses a silent render would not catch a muted one.

---

## 5. Latency

Reported `latency_samples` = **0**, at every macro setting and every rate.

| Rate | Reported | Measured (integer) | Measured (sub-sample) | Δ | ms |
|---|---|---|---|---|---|
| 48000 | 0 | [0.0, 0.0] | [0.001, 0.001] | 0.001 | 0.00002 |
| 44100 | 0 | [0.0, 0.0] | [0.001, 0.001] | 0.001 | 0.00002 |

Dossier latency budget: **zero samples / 0.00 ms. Met: yes.**

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| — | — | — | — | **There are none.** No lookahead, no partition, no pitch window — twelve biquads and nothing that has to see ahead. `test_latency_is_zero_and_no_option_adds_any` walks all fourteen macros to their maximum and asserts 0 after each. |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
**CLICK red at 44.1 kHz** ("measured [0.0, 0.0] samples against a reported 256
(256.0 samples out, bar 1.0)"), audio digest unchanged.

**One number that is not latency and would be mistaken for it.** The two level
sections are shelves at 5 Hz, and a filter that low takes about a third of a
second to charge. A **patch change** would therefore ring for 344 ms and peak
at 32752 on an 11000-peak tone if the bank were not cleared — so it is
(`program_change` clears; `set_macro` does not). Measured after the fix:
`Full Boost` → `Scooped Mids` peaks at **5826 against a steady 4418, above
steady for 8 ms**. This is a transient, not processing delay:
`latency_samples` stays 0 and CLICK measures 0 either way.

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0–8 | `31` `63` `125` `250` `500` `1k` `2k` `4k` `8k` | BIPOLAR | ±12 dB | the nine gyrator band sliders |
| 9 | `16k Shelf` | BIPOLAR | ±12 dB | the tenth slider — a shelf (T1) |
| 10 | `Gain` | BIPOLAR | ±12 dB | GAIN, before the bank |
| 11 | `Volume` | BIPOLAR | ±12 dB | VOLUME, after the bank |
| 12 | `Band Q` | UNIPOLAR | 0.7…2.5, default 2.0 | none — the anchor of the proportional-Q law |
| 13 | `Constant Q` | TOGGLE | off (default) / on | none — the Bohn axis |

Fourteen of a possible sixteen. No character folds anything away.

| Patch | Name | What it is for | Peak on an 11000-peak source |
|---|---|---|---|
| 0 | `Flat` | the constructor's defaults on the 0-127 grid — and a wire, byte for byte | 11000 |
| 1 | `Scooped Mids` | the classic mid-scoop, trimmed 6 dB so it is a curve and not a volume | 10899 |
| 2 | `Pushed Mids` | its inverse, trimmed 4.5 dB | 10727 |
| 3 | `Trimmed Bottom` | the bottom two octaves out of the way | 10965 |
| 4 | `Rolled Top` | the top three down | 8444 |
| 5 | `Full Boost` | every band at +6 dB, trimmed 9 dB — the expensive patch | 11328 |

The three boosting patches carry a `Volume` trim because they are otherwise
loud rather than different: untrimmed they read 21574, 17893 and 26741 on the
same source, and the last clips anything 3 dB hotter. `patch_index` is 0 on a
fresh instance, `None` after any macro move, and the patch's index after
`program_change` (`test_cpython_effects_library.py`, over the whole
catalogue).

**`capabilities` = `()`.** The dossier's one-line reason: nothing here is
tempo-dependent and a filter bank has no rate to lock to. Measured rather
than asserted — a transport that counts its own calls is handed to the
class, the whole probe is rendered and all fourteen macros are moved, and the
count is **0** (`test_capabilities_is_empty_and_the_transport_is_never_read`).

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `audiobiquad.Biquad` × 12 | `audiobiquad` | Tier 1's silence-to-zero, and T4 | `synthio.Biquad` keeps its output memory in Q12 sample units and rounds to nearest with no dither and no leak, so the recursion has fixed points. At **this class's own bands** it lands on them: **+7 LSB** at 31.25 Hz/+6 dB and **+5 LSB** with all ten engaged, held for the whole render (audioif#23, reproduced three times — the seed, the licence audit, and this pack's TAIL control). `audiobiquad`'s float state flushes below 1e-20 and reads **0**. |

The seed's tier was **stock, conditionally**: "moves to audioif only if Gate 0
answers audioif#23 with a float biquad node". Gate 0 did (audioif#39), the
node is on the pin, and the seed's own sentence — "§4's node list changes;
nothing else here does" — is what happened.

Test:

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.046s

OK
```

**What that test does not prove**, and every pack repeats it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so no stock-tier class
has been shown rendering on a stock CircuitPython build of the ported C.
That is a gap in the method, not in this class — and it does not bear on this
one either way, since `GraphicEQ` is audioif tier and says so.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured.
      **Three demonstrated, two disconfirmed with their real numbers and the
      anchor trade behind them, none unmeasured.**
- [x] Every Tier 1 invariant is green on CPython at 48 kHz, 44.1 kHz and
      22.05 kHz, and on MicroPython and the patched CircuitPython by
      byte-identical render (§2's opening note); every Tier 2 measurement
      names its rate.
- [x] Every demonstrated Tier 2 trait has a measurement shown red on a
      planted fault of the same kind. **T4's fault had to be moved from
      band 5 to band 0 to fire, and both are recorded.**
- [x] Every demonstrated trait survived an independent refutation attempt,
      recorded with the argument and the answer (§1, last column).
- [x] CPython and desktop MicroPython render identical bytes — 18 of 18,
      with `circuitpython-effects` identical too.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 22.7 % and S3 38.6 % of the deadline (marginal) against 38 % / 64 %: **inside budget**.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the budget is met; there are no latency-adding options.
- [x] The class declares fourteen macros and five named patches beyond
      patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass
      (§9).
- [x] The README catalogue row and the docstring describe the standout, the
      tier and the cost in a musician's terms.
- [x] The class's code, this file and the README row land together.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 250 tests in 21.971s

OK (skipped=1)
# 250 against the foundation's 227: this class's 24 in, and one of the three
# retired GraphicEQ assertions had no successor (section 10).

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.046s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_graphiceq
........................
----------------------------------------------------------------------
Ran 24 tests in 12.723s

OK

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/graphiceq_evidence.py
(the whole of §§1-3 and §5; exit 0)

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/graphiceq_bench.py
(the dossier's App. S; exit 0)

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:GraphicEQ")'
ROW	effect:GraphicEQ	656.6	3.50	1.523	0.313	1.210	15824	4169efd90ecf44dd
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:GraphicEQ")'   # the S3
ROW	effect:GraphicEQ	395.2	2.11	2.530	0.471	2.059	15824	4169efd90ecf44dd
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

1. **No surface at all** (`eq.py:81`, `:83`). → Fourteen macros, six patches.
2. **Every band a bell, including the top one** (`eq.py:93-95`, `:47-49`) —
   T1 not implemented at any setting. → Band 9 is a `HIGH_SHELF`, and T1 is
   demonstrated with its planted fault.
3. **Q hard-coded at 1.4 for every band at every gain** (`eq.py:94`) —
   constant-Q by omission. → Q from gain on every macro move, measured at
   1.780 / 1.146 / 0.716 octaves across travel; `Constant Q` makes the old
   behaviour a deliberate option instead of an accident.
4. **Bands above Nyquist dropped silently** (`eq.py:92`, `:95`). → Every
   centre clamps through `self._hz()` and `clamped` / `built_centres` say
   what moved. At 22.05 kHz `clamped == (9,)` and the shelf's corner reads
   10804.5 Hz against the 11313.7 it asked for.
5. **ISO preferred centres hard-coded at module level** (`eq.py:67-68`). →
   The M-108's own octave doublings from 31.25 Hz, in `DEFAULT_CENTRES`, and
   a `centres=` constructor option that takes exactly ten ascending
   frequencies.
6. **Inherited from `ParametricEQ`:** `check_hz()` refuses instead of
   clamping; the all-flat case returns the source itself and so takes a
   different path through `reset()`/`deinit()`; `Effect.__new__` mutates
   module-wide format state. → `_hz()` clamps; the all-flat case is the same
   twelve nodes with `mix = 0`, so `reset()` and `deinit()` walk the same
   list at every setting; there is no module state on the construction
   module at all.

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is inside its budget on both boards.**
  §4 carries the figures: P4 22.7 % and S3 38.6 % of the deadline (marginal)
  against 38 % / 64 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names.
- **No lean patch, and the class is expensive.** Twelve sections run at every
  setting; a flat band is muted, not skipped, because
  `audioif_filter_f32.c:216-241` has no `mix == 0` short-circuit. If the
  board run finds 64 % of an S3 block unacceptable, the fix is an audioif
  change (a `mix == 0` fast path), not a patch. **Not filed as an issue by
  this session** — it wants a number from the board first.
- **T3 is disconfirmed by 0.22 dB and T5 by 0.35 dB of ripple and 0.30 dB of
  level.** Recorded as results, not fixed. §1b shows T3's half is a function
  of the `Band Q` default and that T2 pulls the other way; T5's ripple half
  fails at both anchors and is a property of an octave-spaced two-pole bank.
  Neither threshold was moved.
- **CLICK was not run at 22.05 kHz.** The gate asks for 48 kHz and 44.1 kHz
  and both are here; the third rate has TAIL, WIRE, LEVEL and the clamp but
  no click measurement.
- **`tempo_sync` is reported `unmeasured` by STATE**, because the pack does
  not hand it two transport digests. The claim is carried instead by a
  transport that counts its own calls and reads 0 (§6) — which is a stronger
  check for a class declaring `()` than a digest comparison would be, but it
  is not the kit's own row and this line says so.
- **The `Rack` interaction is untested.** Nothing here puts `GraphicEQ`
  inside a `Rack` and checks that its 465 ms tail and zero latency sum
  correctly.

Nothing else is outstanding.
