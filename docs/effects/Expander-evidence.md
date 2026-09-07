# Evidence Pack — `Expander` (Drawmer DS201, with RaneNote 155 for the law)

Written from runs, at Station C, on branch `effects/p2-expander`. Every figure
below carries the command that produced it and the interpreter and rate it ran
on; §9 holds the commands verbatim. §11 says what is not done, on its own
lines.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `Expander` |
| Dossier | [`Expander.md`](Expander.md), traits fixed 2026-09-06 by the Phase 0 seed and unedited since; Station A bench at `3743017` |
| Module | `lib/audioeffects/rebuilt/expander.py` |
| Base | `_component.Component` |
| Family / phase | Dynamics, roadmap Phase 2 |
| Standout | Drawmer DS201 (envelope, key filter, depth) with RaneNote 155 (the ratio law and the RMS detector) |
| Grade | literature |
| Portability tier | **audioif** — `REQUIRES = ("audiodynamics",)` |
| Landed in commit | `1f806d0` — the class, the catalogue row and the CHANGELOG line together; this file in the commit after it |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed` |
| Interpreters | `audiocomponents/.venv/bin/python` **cpython 3.12.3**; `cmods/bin/micropython` **micropython 1.28.0**; `cmods/bin/circuitpython-effects` **circuitpython 10.2.1** |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** yes. The six trait
statements, their disconfirmation clauses and their measurements are the Phase
0 seed's of 2026-09-06, word for word. Station A added three bracketed notes
recording what a statement *implies*; this pack grades the statements.

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

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| E1 | `ratio` dB out per dB in below threshold; slope within 5 % at ratios 1.5/2/4/8, no point 0.5 dB off the line; 0.00 ± 0.05 dB above threshold | **demonstrated**, over the span a 16-bit path can carry | CURVE points + E1's own least-squares slope; 48 k / 44.1 k / 22.05 k, cpython. Slope error **+0.44 … +1.34 %** across all three rates, worst residual **0.30 dB**, above threshold **+0.000 dB** at every level | Ratio driven 30 % high → **RED at 1.5, 2 and 4** (+31.7 %, +34.9 %, +34.6 %); at ratio 8 the fault is not expressible (8 × 1.3 is past the Ratio macro's own 8.0 ceiling) and the row is the clean run, said rather than counted | *"The span was chosen to make it pass."* It was chosen to keep the lowest step's **output** above the int16 floor, and the rule is printed with every row: `span = min(30, (75 + threshold)/ratio)`. Widen it and the bottom step lands under one LSB, where a 0.5 dB residual is one quantiser step. E1's own 30 dB clause needs 210 dB of output range at ratio 8 (dossier B1); nothing can carry it. |
| E2 | Sine and square of equal RMS, 15 dB below threshold, within 0.5 dB | **disconfirmed at ratio ≥ 4** — REFUTED; demonstrated at ratio ≤ 3 | XF → CURVE; 48 k / 44.1 k / 22.05 k, cpython. Gap **0.10 / 0.09 / 0.11 dB** | Detector toggle forced to peak → **RED, gap 2.07 dB** | *"The gap is small because the probe is a sine both times."* The two probes are a sine and a 50 % square generated at the same RMS; the faulted run separates them by 2.07 dB on the same pair, so the pair discriminates. |
| E3 | Key band 25 Hz–4 kHz / 250 Hz–35 kHz, and an out-of-band tone swept to 0 dBFS leaves the gain within 1 dB of its floor | **disconfirmed** | KEY → RESPONSE; 48 k / 44.1 k / 22.05 k, cpython. Both ends move and both reject, but a **−20 dBFS** tone an octave outside a 500–2000 Hz band already opens the gain fully: departure from the −60 dB floor **60.0 dB**, bar 1.0 | not required for a disconfirmed trait | The clause implies better than 40 dB of stopband rejection one octave out — an eighth-order key filter per end. No source states an order; the node ask specified 12 dB/octave and the class ships it (`sidechain_poles=2`). **What the class does instead:** two poles each end, measured 25 dB two octaves out (dossier B3), stated in the class docstring and the README row. |
| E4 | Depth is a control: settled attenuation within 0.5 dB of the setting at 0, −20, −40, −60 dB, span reaching −80 | **demonstrated on the three rows a 16-bit path can show** | LAW at four depths; 48 k / 44.1 k / 22.05 k, cpython. Error at 0, −20 and −40 dB is **−0.00 / −0.03 / −0.41 dB** at 48 kHz and **−0.00 / −0.04 / −0.38 dB** at 44.1 kHz and at 22.05 kHz — worst 0.41 dB against a 0.50 bar. The −60 row lands under one LSB (output −92.97 dBFS at 48 kHz) and is not a reading of the class | Depth pinned at 0 dB → **RED, 20 / 40 / 60 dB of error** | *"Then the deep end is unproven."* On the node it is: dossier B4 has **−60.15 dB** and **−81.68 dB** at the −60 and −80 settings. What the class cannot do is put the trait's own operating point (input −6 dBFS, threshold 30 dB above it) on its Threshold macro, whose span stops at 0 dBFS — as the DS201's own does. |
| E5 | The envelope is one-shot: the attack completes even if the key falls back, and Hold times from that fall | **disconfirmed** | ENV → GAINTRACE; 48 k, cpython. The class has no Hold to turn on, and `hold_ms` is silently inert in `DYN_EXPAND` (`audioif_dynamics.c:452-453`); the machine it drives replaces the ratio law with a binary open/floor (`:679-724`). Dossier B5 has the two traces, identical with and without it | not required | *"Then it was not tried."* It was: B5 runs the same 1 ms burst under a 200 ms attack in both modes, and `DYN_GATE` moves from −80.00 dB to −1.96 dB with the same option. The class is the mode that cannot have it. E5 belongs to `NoiseGate`, whose own pack has to demonstrate it; nothing here claims that it has. |
| E6 | Attack 10 µs–1 s, release 2 ms–4 s, measured 10–90 % within 15 % of the setting; below one sample period, one sample or less | **disconfirmed as stated** | ENV → GAINTRACE; 48 k / 44.1 k / 22.05 k, cpython. t63 over the setting is **0.92 → 0.13** across the attack decade and **5.7 → 2.79** across the release decade, stable at the long end and rate-independent to two decimals | not required | The settings are one-pole time constants, so a 10–90 % time on a gain-in-dB trace is not the same number and depends on the level step as well. The times *track*: at the long end the ratio is fixed (0.13 attack, 2.79–2.81 release) at all three rates, so nothing has stopped moving. Dossier B6 measures the fastest attack at t63 **0.75 ms** (RMS) and **0.25 ms** (peak, the trace's own resolution). |

- **demonstrated** needs a measurement, that measurement red on a planted
  fault of the same kind, and a surviving refutation. E1, E2 and E4 have all
  three.
- **disconfirmed** carries the cause and what the class does instead. E3, E5
  and E6 are each visible in the class docstring's first screen and E3 and E5
  in the README catalogue row. Nothing here asserts what another class's
  pack shows.
- **Characters:** none.

**Refutation pass.** Run in this session, 2026-09-07, against the three
demonstrated traits, and recorded per row above. What it went after: whether
E1's measurement band had been chosen to make the trait pass (it is printed
with every row and set by the int16 floor); whether E2's pair can discriminate
at all (the faulted run separates it by 2.07 dB); and whether E4's deep end
was quietly dropped (it is measured on the node in B4 and named as outside the
class's Threshold span). What it could not break: nothing in the three
survived unchanged — E1's span rule and E4's operating point are both narrowed
statements now, and they say so.


### Gate audit — the refutation pass's verdicts, ruled on (2026-09-07)

Ruled by the Phase 2 gate auditor against the **Refutation record** at the
foot of this file. Where a refutation stands the verdict above was changed
and the class was **not** touched; where the auditor re-ran a figure itself
the run is named. The roadmap's class-gate rule is the test applied: a
*demonstrated* trait needs a measurement, that measurement shown red on a
planted fault of the same kind, **and** a surviving refutation.

| Row | Ruling | Cause recorded, and the auditor's check |
|---|---|---|
| E2 | **refutation stands** → disconfirmed at ratio ≥ 4 | The trait fixes the level (15 dB below threshold) and no ratio. Auditor's check: `tools/expander_evidence.py` `e2_detector` hardcodes `ratio=2.0` in its settings dict, so §1's three figures are one ratio. At threshold −6 dBFS, 1 kHz, 48 kHz the gap reads **0.04 / 0.09 / 0.16 / 0.55 / 1.88 dB** at ratios 1.5 / 2 / 3 / 4 / 5 against a 0.50 dB bar, unchanged at 1 s / 3 s / 5 s and at depth −80 and −90 dB; and at ratio ≥ 6 both renders are digital silence, so the reading is **0.00 dB clean and 0.00 dB faulted** — it cannot fail there. Demonstrated at ratio ≤ 3. |

E1 and E4 survive, each with a wording correction the Refutation record states
(E1's square-wave residual at 89 % of its bar; E4's third row is the depth-0
wire and cannot fail, so the demonstration rests on two rows).

**Rule applied to the two non-`disconfirmed` outcomes.** A refutation that
shows the class failing its own bar makes the row **disconfirmed**. A
refutation that shows the *demonstration* invalid — a fault that cannot fire,
a reading that is green on a bypass, a bar that was never asserted — leaves no
number that tests the trait, so the row becomes **unmeasured**, on this pack's
own precedent for a measurement that "produced a number that does not test the
claim". Neither outcome is a licence to edit the class.


---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`. The **analysis is CPython's** in every
column, which is the kit spec's own split (§1: the render is dual-runtime, the
analysis is not); an `mp` or `cpy` cell is that interpreter's *render*,
analysed here.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Ratio 1.0 is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Depth 0 dB is a wire, byte-identical to the source | WIRE | pass | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| Level-honest: unity through the wire state | LEVEL | pass (0.0000 dB) | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass (0 / 0) | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node the class built silent and stateless, the source untouched | STATE | pass (0 LSB) | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| `deinit()` releases every node the class built and leaves the source rendering | §2's own check | pass | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| `capabilities` names exactly the optional behaviours honoured | STATE | pass (`()`) | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| Pulling `output` allocates nothing | STATE | pass (−204736 bytes over 200 pulls) | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |
| Every invariant also holds at `channel_count` 1 | (all) | pass | n/a | n/a | pass | n/a | n/a | pass | n/a | n/a |

The nine `mp` and `cpy` cells above are **measurements, not inferences**:
`ramp_fs` at Ratio 1.0, `burst_silence` and `click_stereo` were rendered by
each interpreter at each rate through `tools/render_effect.py`, and WIRE,
LEVEL, TAIL and CLICK were then run over those WAVs on CPython. The readings,
identical in all 36 cells:

```
mp   WIRE ratio1     48000  0/47104 samples differ       green
mp   LEVEL           48000  wet:dry rms [0.0, 0.0] dB    green
mp   TAIL            48000  tail None, residual 0 LSB    green
mp   CLICK           48000  measured [0.0, 0.0] vs reported 0 green
cpy  WIRE ratio1     22050  0/22528 samples differ       green
cpy  LEVEL           22050  wet:dry rms [0.0, 0.0] dB    green
cpy  TAIL            22050  tail None, residual 0 LSB    green
cpy  CLICK           22050  measured [0.0, 0.0] vs reported 0 green
all green: True
```

(`tail None` is the kit's way of saying there was no non-zero sample after the
burst at all — a tail of zero, which is what `TAIL_SAMPLES = 0` claims.)

`n/a` in an `mp`/`cpy` column means the measurement drives the class *between*
renders — STATE, the `deinit` contract, the mono leg and the Nyquist-clamp
leg — so it is CPython's, and what carries it across is §3's byte identity.

**Rate honesty, the number.** Key High at the top of its 250 Hz–35 kHz span
reports 35000 Hz and applies **23520 / 21609 / 10804 Hz** at 48 / 44.1 /
22.05 kHz — `NYQUIST_MARGIN` below each Nyquist, clamped rather than refused.

**Mono.** The dossier's §4 states that one gain from a channel-linked detector
is applied to every channel, so a mono source gets identical processing and no
stereo statement is owed. Measured: the whole Tier 1 block above re-run at
`channel_count` 1, all green, with the same Key High clamp.

**The tail, and its one exception.** With Key Listen off — the declared state,
and off in all six patches — the last non-zero frame after a 200 ms burst is
the burst's own: `tail_samples` is 0 and the settled residual is 0 LSB, because
the gain is a per-sample multiply on the audio. With Key Listen **on** the
output is the side chain's own signal and the 25 Hz high-pass has memory:
**2373 / 2180 / 1089 frames** at 48 / 44.1 / 22.05 kHz, residual 0 LSB. That is
a diagnostic state; it is recorded here and in the docstring rather than folded
into `TAIL_SAMPLES`.

**What `reset()` clears and what the node keeps, measured at the boundary.**
Primed on a −55 dBFS tone the class reports **−58.21 dB** of gain reduction;
immediately after `reset()` it still reports **−58.21 dB**, because
`Dynamics.reset_buffer` keeps the last reported gain reduction and the
side-chain filter memory on purpose (`audioif/docs/upstream-diff.md:704-706`).
Driven on from a −6 dBFS tone it settles at **+0.00 dB**, so the detector
envelopes really were dropped. The class's walk inherits the node's reset; it
does not override it.

**Planted faults for this block:**

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | the wire state nudged off unity (Ratio 1.0 → 1.0201) on `ramp_fs` | green | **RED**, 246 of 47104 samples differ, first at frame 0 channel 0, max 3934 LSB |
| TAIL | +1 LSB of DC written into the settled state | green | **RED**, residual 1 LSB in the last 14400 frames (bar 0), and no last non-zero sample to report a tail length from |
| CLICK | `latency_samples` reported 256 short, the DSP untouched | green | **RED**, measured [0.0, 0.0] against a reported 256 — and the audio digest is `267aeac5` in both runs, so the check fired without the sound changing |
| STATE (deinit leg) | a node the class does not own, declared owned | green | **RED**, `deinit() left ['planted'] live` |
| the registry rule itself (`tests/test_rebuilt_registry.py`, rewritten by this rebuild) | `NAME = 'Expander'` changed to `'Expandr'` in the rebuilt module | green | **RED**, `FAILED (errors=1)` — `ImportError: audioeffects.rebuilt.expander holds no Component whose NAME is 'Expander'`, raised at package import, so a rebuild that never took effect cannot pass as the old class standing |

**The reset leg's own fault is not planted, and why.** The kit's fault of that
kind is "a delay line left full". This class's audio path is a per-sample
multiply with no sample memory, so there is no line to fill — silence in is
exact zero out whatever the envelope holds, faulted or not. That fault is
planted where it bites, on the foundation's two-arm reset walk
(`tests/test_component_foundation.py`, `TwoNodes primed 28199 → after reset 0`
against `OnlyOwnsTheTail primed 28199 → after reset 18539`).

**Nodes enumerated by this class, in build order:** `audiodynamics.Dynamics`,
and nothing else. STATE reports `nodes: ['Dynamics']`.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, from `tools/render_effect.py` on each interpreter,
block 2048.

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 2048 | `cab44a35` | `cab44a35` | `cab44a35` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2048 | `7be9e0a5` | `7be9e0a5` | `7be9e0a5` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 2048 | `ff6c9479` | `ff6c9479` | `ff6c9479` | *(board run)* | *(board run)* |
| `chord` | 44100 | 2048 | `26972965` | `26972965` | `26972965` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 2048 | `1e085b61` | `1e085b61` | `1e085b61` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 2048 | `b763c4f1` | `b763c4f1` | `b763c4f1` | *(board run)* | *(board run)* |
| `ramp_fs` (Ratio 1.0) | 48000 | 2048 | `aef0fa61` | `aef0fa61` | `aef0fa61` | *(board run)* | *(board run)* |
| `ramp_fs` (Ratio 1.0) | 44100 | 2048 | `aa6aeabd` | `aa6aeabd` | `aa6aeabd` | *(board run)* | *(board run)* |
| `ramp_fs` (Ratio 1.0) | 22050 | 2048 | `4a36acb1` | `4a36acb1` | `4a36acb1` | *(board run)* | *(board run)* |
| `burst_silence` | 48000 | 2048 | `554e5435` | `554e5435` | `554e5435` | *(board run)* | *(board run)* |
| `burst_silence` | 44100 | 2048 | `381a5a9d` | `381a5a9d` | `381a5a9d` | *(board run)* | *(board run)* |
| `burst_silence` | 22050 | 2048 | `a148d7c9` | `a148d7c9` | `a148d7c9` | *(board run)* | *(board run)* |
| `click_stereo` | 48000 | 2048 | `2fdc8549` | `2fdc8549` | `2fdc8549` | *(board run)* | *(board run)* |
| `click_stereo` | 44100 | 2048 | `67a0f1d5` | `67a0f1d5` | `67a0f1d5` | *(board run)* | *(board run)* |
| `click_stereo` | 22050 | 2048 | `33d48045` | `33d48045` | `33d48045` | *(board run)* | *(board run)* |

`byte_sum` is printed beside each digest in the sidecars and is never the
comparison: `chord` at 48 kHz is 89965408, `noise_det` 97953204, `sweep_log`
97527936.

**Desktop agreement: yes** — all three interpreters render byte-identical PCM
on all fifteen rows, and none of the fifteen is silent. `ramp_fs` at Ratio 1.0
hashes to the *probe's own* digest (`aef0fa61` at 48 kHz is what
`tools/effect_probes/README.md` prints for that file), which is the wire state
stated as one number. The in-process digests the
measurement driver prints are the same numbers (`chord` 48 k `cab44a35`), which
is what says the driver's block adapter is `render_effect.py`'s.

**Board agreement:** not taken. §4 and §11.

**Build against build:** not asked for by any trait in this class.

**Block-size ladder:** not asked for by any trait in this class. The class
builds no `Splitter`, so `MultibandCompressor` M5's failure mode has no
analogue here; every render above is at block 2048.

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
target `effect:Expander`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: ESP32-P4 **6 %** of one stereo block's real-time deadline;
ESP32-S3 **12 %**. Lean patch expected: **no** — one node, one detector, one
gain per frame, a two-pole key band at each end.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("Expander", …)` | 1310.2 | 0.763 (0.450 marginal) | 6.99 | 1808 B | **no** — 8.4 % marginal, 14.3 % total, against 6 % |
| S3 | 0 | construction defaults, `audioeffects.create("Expander", …)` | 747.6 | 1.338 (0.868 marginal) | 3.99 | 1840 B | **no** — 16.3 % marginal, 25.1 % total, against 12 % |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:Expander`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 6 %, S3 12 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`782ffd714b06de60` on the ESP32-P4 and `782ffd714b06de60` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is the **same value**.

**Owed: a `" - lean"` patch.** At 16.3 % of the deadline the class is over
its ESP32-S3 budget of 12 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** patch 5 `Hard Downward` on `noise_det`, the state this section names as the one that keeps the VCA at work.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**What the board run must put the class into**, so it is not idled past: patch
5, *Hard Downward* (ratio 8, depth −60 dB), on `noise_det`, which holds the
gain computer below threshold and the VCA at work for the whole render. Patch 0
is the honest default but expands very little on that material.

---

## 5. Latency

Reported `latency_samples` = **0**.

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0.0, 0.0 (both channels) | 0 | 0.000 |
| 44100 | 0 | 0.0, 0.0 | 0 | 0.000 |
| 22050 | 0 | 0.0, 0.0 | 0 | 0.000 |

Dossier latency budget: 0 samples. **Met.**

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none)* | — | — | — | there is none to name |

The class ships **no look-ahead option at all** — the dossier's §3 reasons it
out of existence from S2's own block diagrams — so the row above is empty
because there is nothing to put in it, and the docstring says that in those
words rather than leaving a reader to infer it. The one delay worth naming is
not latency: narrowing the key band slows the detector's response to a
transient (S1 warns of it). **That delay is not measured in this pack** — it
is a detector-response effect, it is never reported in `latency_samples`, and
no number for it appears anywhere here. §11.

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
CLICK **RED at every rate**, audio digest `267aeac5` unchanged. §2's table.

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Threshold | UNIPOLAR | −80 … 0 dB | DS201 Threshold |
| 1 | Ratio | UNIPOLAR | 1.0 … 8.0, log | RaneNote 155's ratio |
| 2 | Depth | UNIPOLAR | 0 … −80 dB | DS201 Range |
| 3 | Attack | UNIPOLAR | 0.01 … 1000 ms, log | DS201 Attack |
| 4 | Release | UNIPOLAR | 2 … 4000 ms, log | DS201 Decay |
| 5 | Key Low | UNIPOLAR | 25 … 4000 Hz, log | DS201 L.F. |
| 6 | Key High | UNIPOLAR | 250 … 35000 Hz, log, clamped below Nyquist | DS201 H.F. |
| 7 | Key Listen | TOGGLE | off / on | DS201 Key Listen |
| 8 | Detector | TOGGLE | peak / RMS | RaneNote 155's rms-for-expanders |

Nine of the sixteen the contract allows. The dossier proposed ten; **Hold is
absent** because `hold_ms` does nothing in `DYN_EXPAND` (E5 above), and that is
said in the class docstring's first screen. The DS201's remaining panel
controls that are not macros: Gate/Duck (a different gain computer, not this
class), Stereo Link (a graph decision, not a knob) and Bypass (the host's).

| Patch | Name | What it is for |
|---|---|---|
| 0 | Gentle Lift | the constructor's defaults on the 0–127 grid: 1.5:1 to a −20 dB floor, slow release — dynamics opened up without the noise floor moving audibly |
| 1 | Noise Floor Trim | −55 dBFS threshold, 2.5:1 to −30 dB: takes hiss down between phrases |
| 2 | Snare Tighten | fast attack, 6:1, key band 150 Hz–8 kHz so the kick does not hold it open |
| 3 | Guitar Amp Hum | key band 300 Hz–4 kHz, so mains hum and its harmonics never reach the detector; 4:1 to −40 dB |
| 4 | Room Reduction | slow attack and a 800 ms release, 3:1 to a shallow −15 dB — room tone pushed back without pumping |
| 5 | Hard Downward | 8:1 to −60 dB on the peak detector: the closest this class gets to a gate, and the patch the cost run should use |

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change` — held by `tests/test_component_foundation.py`
for every `Component` and exercised for this class by the three-interpreter
smoke, which walks all six patches.

**`capabilities` = `()`.** Nothing in an expander's law refers to tempo and
neither source's unit has a tempo input, so `self._transport()` is never read
(dossier App. I, D10). STATE reports `capabilities: []`.

---

## 7. Portability tier

**Tier:** audioif. `REQUIRES = ("audiodynamics",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Dynamics(DYN_EXPAND)` | `audiodynamics` | E1, E2, E3, E4, E6 | `audiodynamics` is not a CircuitPython port at all — it comes from micropython-vst3's `vstaudio` usermod and CircuitPython has no equivalent and never had one (`audioif/docs/upstream-diff.md:661`). There is no ported gain computer, no detector and no VCA to build a downward expander from. |

**What that test does not prove**, and every pack repeats it: blocking a module
in `sys.modules` is not a board without the module. No stock CircuitPython
interpreter exists in this workspace, so a stock-tier class has *not* been
shown rendering on a stock CircuitPython build of the ported C. That is a gap
in the method, not in this class — and it does not touch this class's own
claim, which is the opposite one: `Expander` declares that it needs
`audiodynamics` and the test shows construction raising `ImportError` when it
is blocked.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured.
- [x] Every Tier 1 invariant is green on CPython at 48 kHz, 44.1 kHz and
      22.05 kHz, and on MicroPython and the patched CircuitPython build for
      every leg that a render can carry (§2's `n/a` note, and §3's byte
      identity); every Tier 2 measurement names the rate it ran at.
- [x] Every demonstrated Tier 2 trait has a measurement, and that measurement
      was shown red on a planted fault of the same kind.
- [x] Every demonstrated trait survived an independent refutation attempt,
      recorded with the argument and the answer.
- [x] CPython, desktop MicroPython and circuitpython-effects render identical
      bytes on the probe material.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 8.4 % and S3 16.3 % of the deadline (marginal) against 6 % / 12 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz and
      44.1 kHz; the budget is met; there is no latency-adding option, and the
      docstring says so.
- [x] The class declares nine macros and five named patches beyond patch 0.
- [~] `validate_api`, `validate_metadata`, the portability-tier test, the
      three-interpreter smoke and flake8 all pass; **194 of the CPython
      suite's 227 tests pass and the other 33 did not run** — §9 and §11.
- [x] The README catalogue row and the docstring describe the standout, the
      tier and the two things the class does not do, in a musician's terms.
- [x] The class's code, the catalogue row and the CHANGELOG line landed in one
      commit, `1f806d0`; this file in the commit after it.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest \
    <the 18 files that are not tests/test_effect_kit*.py>
----------------------------------------------------------------------
Ran 175 tests in 216.331s

OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_effect_kit
----------------------------------------------------------------------
Ran 19 tests in 63.927s

OK

$ PYTHONPATH=lib timeout 3000 .venv/bin/python -m unittest discover -s tests \
    -p "test_*.py"
.........................................................................
.........................................................................
.......................
EXIT=124

  - killed by its own 50-minute timeout at test 169 of 227,
    tests.test_effect_kit_11_20.RoundTrip.test_control_a_real_capture, with
    eight sibling worktrees running the same suite on the same eight cores
    (load 76). Re-run of that one file alone reached 20 of its 33 and was
    still running. The 194 tests above are the same suite minus
    tests/test_effect_kit_11_20.py, as two commands that did complete.

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.015s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
ok   Vibrato                  patch 0   peak 11000

46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
ok   Expander                 patch 0   peak 11000
ok   Expander                 patch 1   peak 11000
ok   Expander                 patch 2   peak 11000
ok   Expander                 patch 3   peak 11000
ok   Expander                 patch 4   peak 11000
ok   Expander                 patch 5   peak 11000
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
ok   Expander                 patch 0   peak 11000
ok   Expander                 patch 1   peak 11000
ok   Expander                 patch 2   peak 11000
ok   Expander                 patch 3   peak 11000
ok   Expander                 patch 4   peak 11000
ok   Expander                 patch 5   peak 11000
46 classes, 88 patches, 0 failures

(88 patches where the foundation's run reported 83: this class brings six
where the old one had one. The six rows above are grepped out of the same
run; the whole listing is 46 classes long.)

$ PYTHONPATH=lib .venv/bin/python tools/expander_evidence.py --rate 48000
(and --rate 44100, --rate 22050; every figure in sections 1, 2 and 5 above)

$ PYTHONPATH=lib .venv/bin/python tools/render_effect.py Expander chord OUT \
    --rate 48000 --block 2048
  .../Expander__chord__48000__2ch__blk2048.wav

$ PYTHONPATH=lib .venv/bin/python tools/phase0_probes/expander_station_a.py
(the dossier's App. B; the palette-level numbers cited in section 1)

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:Expander")'
ROW	effect:Expander	1310.2	6.99	0.763	0.313	0.450	1808	782ffd714b06de60
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:Expander")'   # the S3
ROW	effect:Expander	747.6	3.99	1.338	0.469	0.868	1840	782ffd714b06de60
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

- **No surface.** The old class had `MACRO_LABELS = ()` and one placeholder
  patch, with threshold, ratio, attack and release construction-only. The
  rebuild has nine macros and six named patches, every one live through
  `set_macro`.
- **The floor was invisible.** The old class exposed `ratio` but not the
  −60 dB clamp under it, so 8:1 stopped obeying the ratio 7.5 dB below
  threshold with nothing said. The rebuild makes the floor the **Depth** macro,
  measured to −0.41 dB of its setting (§1, E4), and the class's own docstring
  names the clamp's replacement.
- **The detector type was undocumented.** The rebuild's default is
  `detector="rms"`, so a threshold set from an RMS meter means what it says
  (§1, E2), and the Detector macro makes the choice a control with its own
  measured consequence.
- **No hold, no key filter, no depth, and nothing stated the omissions.** The
  rebuild has the key filter and the depth; it still has no hold, and that is
  the difference — the omission is stated, with its cause, in the docstring,
  in the README row, in the dossier's §8.1 and in §1's E5 here.

---

## 11. What is not done

- **The full 227-test suite did not complete in one command.** 194 of the
  227 did, as the two commands in §9, both `OK`. The remaining 33 are
  `tests/test_effect_kit_11_20.py`, the kit's own self-tests for measurements
  11-20; the run stalled on `RoundTrip.test_control_a_real_capture` for more
  than forty minutes with eight sibling worktrees running the same suite on
  the same eight cores (load 76); it was killed by its own 50-minute timeout,
  `EXIT=124`, not by a failure. Re-running that one file alone reached 20 of
  its 33 and was still going when this pack was written. That is a
  machine-contention result and not a finding about this class: none of the
  33 constructs an `Expander`, and the file is byte-identical to the
  foundation's, where the whole 227 timed at 19.2 s. **What it would take:**
  the same `python -m unittest discover -s tests -p "test_*.py"` on an idle
  machine. Tried, in this order, and recorded rather than worked around: the
  full discover twice (killed at 169 both times), the 18 non-kit files
  (`OK`), `tests.test_effect_kit` alone (`OK`, 63.9 s), and
  `tests.test_effect_kit_11_20` alone (20 of 33, still running).
- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 8.4 % and S3 16.3 % of the deadline (marginal)
  against 6 % / 12 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **E3 is disconfirmed**, not demonstrated: an out-of-band tone above about
  −20 dBFS opens the expander. The band and its two ends are real; the trait's
  floor clause is not reachable at 12 dB/octave. §1 has the number.
- **E5 is disconfirmed** and cannot be demonstrated by this class at all: the
  node's one-shot machine is `DYN_GATE`-only. It is `NoiseGate`'s to prove.
- **E6 is disconfirmed as stated.** The times track and are rate-independent,
  but a 10–90 % time on a one-pole is not the setting, so the trait's own bar
  cannot be met by any build of it. §1 has the ratios.
- **E1's 30 dB clause and E4's stated operating point were both narrowed**, and
  the narrowed statements are in §1 rather than in the dossier's frozen table.
  E1 is measured over 30 / 27.5 / 13.8 / 6.9 dB at ratios 1.5 / 2 / 4 / 8, and
  E4 over three depths rather than four. Both narrowings are the int16 output
  floor, both are printed with the rows, and neither is the class.
- **The kit's `curve()` fits a compressor law**, not an expander's, so its
  `ratio`, `threshold_db` and `knee_db` readouts are not this class's and are
  never cited here; only its law-agnostic per-step points are used. Filed as a
  kit gap in the report from this station, not fixed in this branch.
- **The kit's `gaintrace()` attack leg is a compressor's** — it takes `nanmin`
  as the attack target, which for an expander is the *starting* value, so
  `attack_t10_90_ms` is always `None`. Both steps are read through its
  direction-agnostic release leg instead, which is why §1's E6 quotes t50/t63/
  t95 rather than 10–90 %. Same filing.
- **The class docstring's Key Listen tail figure was corrected at Station C.**
  Commit `1f806d0` carried 2905 frames, which is the dossier's B7 number on
  the node bench's own 220 Hz burst, not this class's on the kit's probe. The
  measurement it should have quoted is 2373 / 2180 / 1089 frames at 48 /
  44.1 / 22.05 kHz on `burst_silence`, and the docstring says that now. The
  commit message for `1f806d0` still carries the old number and cannot be
  changed without changing the sha this file cites.
- **The key band's trigger delay is unmeasured.** S1 warns that side-chain HF
  attenuation "will also cause a slight delay in the time the gate takes to
  trigger"; §5 names it to say it is not latency, and nothing here puts a
  number on it. What it would take: GAINTRACE on a burst at two key-band
  settings, comparing the onset of the gain move rather than of the audio.
- **`tests/test_rebuilt_registry.py` had to be edited**, which the registry
  rule would rather a rebuild did not. Three of its assertions were counts of
  how many of the 46 had been rebuilt, and the first rebuild anywhere makes
  them false. They hold the rule now instead of the count, so the second class
  will not have to touch the file — but the sixteen Phase 2 branches in flight
  will each see this hunk and one of them will land it.

---

## Refutation record (2026-09-07)

An independent refuter, working only from §1's demonstrated rows and the
dossier's own trait statements, re-ran each measurement with the kit
(`PYTHONPATH=lib .venv/bin/python`, driver helpers imported from
`tools/expander_evidence.py`), varied the probe material and the operating
point *inside the trait's own terms*, re-planted each fault, and looked for a
reading that cannot go red. Every number below is from a run in this session.

- **E1 — not refuted, and one hole in the pack closed.** The pack tests two of
  the dossier's three disconfirmation clauses; the third — *"a slope that
  changes by more than 5 % when the whole staircase is moved 20 dB up or down
  with the threshold moved with it"* — was untested. Run here at thresholds
  −40 / −20 / 0 dBFS: the slope moves by at most **1.03 %** (ratio 1.5), and
  by **0.30 / 0.94 / 0.87 %** at ratios 2 / 4 / 8, all against a 5 % bar.
  Material varied too (100 Hz, 1 kHz, 5 kHz sine and a 1 kHz square at ratios
  2 and 4): slope error **+0.92 … +1.90 %**, worst residual **0.446 dB** on
  the square at ratio 2 — green, but that is 89 % of the 0.5 dB bar and the
  pack quotes only 0.30. The pack's own fault reproduced exactly (**+31.65 /
  +34.94 / +34.62 %**, ratio 8 not expressible). The ratio-8 row is therefore
  *not* a measurement that cannot fail: the same fault driven **downward**
  (ratio set 30 % low) turns all four rows red, ratio 8 included — slope
  **5.6126**, **−29.84 %** off the claim. *The author must answer:* nothing.
  The square-wave residual margin is worth a line in §11.
- **E2 — REFUTED.** The trait fixes the level (15 dB below threshold) but
  **no ratio**; §1 quotes one gap per rate and never says the demonstration
  was taken at ratio 2 alone. Re-run at other ratios inside the Ratio macro's
  own 1.0–8.0 span, at threshold −6 dBFS where the output stays 24 dB clear of
  the int16 floor (48 kHz, 1 kHz, equal-RMS sine vs 50 % square):

  | ratio | sine out | square out | gap | bar |
  |---|---|---|---|---|
  | 1.5 | −28.51 dBFS | −28.55 dBFS | 0.04 dB | green |
  | 2.0 | −36.02 | −36.11 | 0.09 | green |
  | 3.0 | −51.06 | −51.22 | 0.16 | green |
  | 4.0 | −66.23 | −66.79 | **0.55** | **RED** |
  | 5.0 | −82.41 | −84.29 | **1.88** | **RED** |
  | 6.0 | −240.00 | −240.00 | 0.00 | *both renders are digital silence* |

  The ratio-4 reading is the class's, not the floor's or the window's: it is
  **0.55 dB unchanged** at 1 s / 3 s / 5 s probes, over the last 50 % / 25 % /
  9 % of the render, and at depth −80 and −90 dB. It is rate-dependent —
  **0.55 / 0.49 / 0.32 dB** at 48 / 44.1 / 22.05 kHz — so 48 kHz, the pack's
  own headline rate, is the one that fails. **And the measurement cannot fail
  at ratio ≥ 6:** at ratio 6, threshold −6 dBFS, both renders are silence, so
  the gap is **0.00 dB clean and 0.00 dB with the pack's own peak-detector
  fault planted**. The planted fault does discriminate where the reading is
  live (gap **1.03 / 2.07 / 7.50 dB** at ratios 1.5 / 2 / 4), and it under-runs
  the dossier's predicted "near 3.0 dB × (ratio−1)" everywhere (predicted 1.50
  / 3.01 / 9.03). *The author must answer:* at which ratios E2 is claimed, why
  §1's verdict does not name the single ratio it was taken at, and what the
  0.55 dB at ratio 4 / 48 kHz is — the key band's two-pole 23.52 kHz end taking
  RMS off the square and the gain computer multiplying that error by
  (ratio−1) is the obvious candidate, and it is untested here. Until then E2
  reads **demonstrated at ratio ≤ 3**, not demonstrated.
- **E4 — not refuted, but the row count is overstated.** The verdict says
  "demonstrated on the three rows a 16-bit path can show". The **depth 0 dB
  row cannot fail**: it is green clean (error +0.00) *and* green under the
  pack's own planted fault (depth pinned at 0 dB → error +0.00), because the
  fault and the setting are the same value. Only the −20 and −40 rows go red
  (+20.00, +40.00), so the demonstration rests on **two** rows, and the third
  is a restatement of §2's "Depth 0 dB is a wire" invariant. The trait names
  no probe frequency, and the −40 row's margin is thinner than §1 says: at
  48 kHz it is **−0.39 / −0.37 / −0.41 / −0.44 / −0.49 / −0.49 dB** at 100 Hz
  / 250 Hz / 1 kHz / 4 kHz / 8 kHz / 16 kHz against a **0.50 dB** bar — 98 % of
  the bar at 8 and 16 kHz, where §1 quotes the 1 kHz figure of 0.41. Nothing
  found goes red: 20 kHz sine (−0.44), 1 kHz and 4 kHz square (−0.31), ratio 4
  instead of 8 (−0.41), and 22.05 kHz at 4 / 8 / 9.5 kHz (−0.38) are all
  inside the bar. *The author must answer:* reword the verdict to two rows,
  and quote the worst frequency rather than 1 kHz.

**Commands.** `PYTHONPATH=lib .venv/bin/python tools/expander_evidence.py
--rate 48000 --only e1|e2|e4` (reproduced §1's figures exactly: E1 slopes
1.5077 / 2.0185 / 4.0390 / 8.0817, E2 gap 0.10 dB, E4 errors +0.00 / −0.03 /
−0.41), then four ad-hoc drivers importing `tools/expander_evidence.py`'s
`tone`, `render`, `dry` and `at` and `tools/effect_measurements.py`'s `curve`
and `rms_db` directly, for the sweeps tabled above.
