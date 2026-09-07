# Evidence Pack — `DynamicEQ` (no historical standout — design grade)

Written from the template at Station C of the class build, from runs in this
worktree. Every figure carries the command and the interpreter and rate it
ran on; a measurement nobody ran is `unmeasured`, with why. §11 says what is
not done.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `DynamicEQ` |
| Dossier | [`DynamicEQ.md`](DynamicEQ.md), traits frozen 2026-09-07 at `0462960` |
| Module | `lib/audioeffects/rebuilt/dynamiceq.py` |
| Base | `_component.Component` |
| Family / phase | EQ, roadmap Phase 2 |
| Standout | none (vision §4.2); the circuit is the exactly complementary split |
| Grade | design |
| Portability tier | **audioif** — `REQUIRES = ("audiobiquad", "audiodynamics", "audioroute")` |
| Landed in commit | `d77543a` — code, tests, probes, README row and CHANGELOG line. This file, and the cost correction §4 records, land in the Station C commit that follows it, which also touches the class docstring, the README row, the CHANGELOG and the dossier's Tier 3 row |
| audioif pin | `2f6cbc3`, fixed for this program |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3; `cmods/bin/micropython`; `cmods/bin/circuitpython-effects` |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** yes. Commit `0462960`
froze six Tier 2 traits; `d77543a` is the class. The class was prototyped in
scratch scripts before the freeze — that is how §8's opens were answered —
and no trait was written or edited after `0462960`.

---

## 1. Traits

Command for every row below, unless another is named:

```
$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      -m unittest tests.test_cpython_effects_dynamiceq
Ran 33 tests in 79.841s

OK
```

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| T1 | The split is exact: detector idle, reconstruction within 0.05 dB from 20 Hz to 0.4·F_s, impulse out at its input peak | **demonstrated** | eight fixed sines at threshold 0 dBFS ratio 1, **worst 0.0000 dB**; impulses at (f₀, Q) = (100, 0.5), (3000, 2), (10000, 8) all peak 20000 at frame 50. 48 kHz, cpython; the same graph on mp and cpy renders byte-identical PCM (§3) | band branch detuned 1 % → worst **0.2218 dB**; Q 10 % apart → worst **0.4009 dB**, both against a 0.05 dB bar and a clean run at 0.0000 | *"Measured at f₀ this proves nothing — the notch is zero and the band-pass is unity there whatever Q is."* Correct, and it is why the first cut of both faults came back green at 0.0068 and 0.0000 dB. The sweep and both faults now read the skirt (2500 and 3600 Hz), where the fault lives |
| T2 | The band gain is the compressor law, knee 6 dB wide; five probe levels within 1 dB | **demonstrated** | five levels at f₀, deviations **+0.000 / +0.188 / +0.422 / +0.423 / +0.423 dB**, worst 0.423 against a 1 dB bar. 48 kHz, cpython. Also run at 44.1 and 22.05 kHz (§2's LAW row): −14.630 and −14.631 dB against −15.000 | knee dropped to 0 dB → the knee probe reads **+0.000** where the law says −0.562 and the class reads −0.374; ratio moved 4 → 2 → **−9.718** where the law says −15.000 and the class reads −14.577 | *"A 0.42 dB offset that is the same at three levels is a systematic error you are calling a pass."* It is systematic, and its cause is now measured rather than assumed: not notch leakage (that branch is exactly zero at f₀) but the detector's finite attack, which moves with attack time and frequency. App. R of the dossier carries the numbers |
| T3 | Below threshold it is a wire: 10 dB under, within 0.05 dB of unity | **demonstrated** | −41 dBFS at f₀ → **+0.0000 dB**. 48 kHz, cpython; **+0.0000 dB** on mp and cpy at 48, 44.1 and 22.05 kHz (§2 LEVEL) | threshold lifted −30 → −55 dBFS → **−10.1381 dB** against a 0.05 dB bar | *"A wire at one level is not a wire."* The row is one level by construction (10 dB under the threshold); the WIRE invariant carries the byte-identical claim across the whole probe, and T1 carries eight frequencies |
| T4 | Out of band untouched while the band works: less than 0.2 dB between idle and 19 dB down | **demonstrated** | 750 Hz (two octaves down) at −41 and −4 dBFS → **+0.0000 and −0.0553 dB**, delta **0.0553**. 48 kHz, cpython | the broadband-ducker topology — gain cell on the whole signal, keyed from the band — moves the same tone **17.157 dB** between the two levels | *"Keying the detector off the dry tap would be the natural fault and you did not use it."* It was used first and came back **0.045 dB** — out of band the band branch carries almost nothing, so ducking it moves the sum by nothing whatever the key hears. The topology is what T4 is about, so the topology is what is planted |
| T5 | The band gain is affine in the band-pass's own response; composite within 0.5 dB of the closed form built from S1 and T2 | **demonstrated** | eight frequencies at a fixed −10 dBFS: deviations **+0.005 / +0.007 / +0.011 / +0.027 / +0.423 / +0.029 / +0.011 / +0.009 dB**, worst 0.423 (at f₀, T2's detector offset) against a 0.5 dB bar. 48 kHz, cpython | the detector's key mistuned to a 6 kHz band → at 2500 Hz the class reads **+0.000** where the closed form says −4.112 and the clean class reads −4.084 | *"Every point but f₀ agrees to 0.03 dB — the closed form and the class share the same arithmetic and this is circular."* They do not: the closed form is Python from S1's coefficients and `audioif_dynamics.c`'s law, the class is C from `audioif_filter_f32.c`. The agreement is between two implementations, and the one point where they part is the detector, which the closed form does not model |
| T6 | A dry/wet blend and a band-range limit are the same control | **demonstrated** | six blends against `20·log10((1−m) + m·g₁)`: worst **0.0035 dB** against a 0.2 dB bar; 375 Hz across the sweep **+0.0000 / −0.0006 / +0.0000 dB** against a 0.05 dB bar. 48 kHz, cpython | dry voice left at unity while the wet voices blend — two mechanisms instead of one — reads **+0.775 dB** where the closed form says −4.534 and the class reads −4.535 | *"`g₁` is measured on the same class, so the closed form is fitted to it."* One number is measured; the shape across five other blends is predicted from it and from nothing else, and the fault shows the prediction is not automatic |

- **demonstrated** needs all three of: a measurement, that measurement shown
  red on a planted fault of the same kind, and a surviving refutation.

**Characters.** None. One band, one behaviour; a second band is a second
instance. `expand=True` is a second *build* rather than a character, and it
carries one check of its own rather than a trait row: over the threshold it
is a wire (**+0.000 dB** at −6 dBFS), under it the band goes away (**−inf**,
i.e. exact zero, at −46 dBFS against a −30 dBFS threshold at 4:1).

**Refutation pass.** Run by this session against its own results, before the
pack was written, on 2026-09-07. It went after the two rows whose faults came
back green — T1's mistune and T4's key — and both are re-cut above with the
first attempt recorded rather than deleted. It also went after T2's
systematic 0.42 dB and got a cause out of it that contradicts the seed. What
it could not break: T1's 0.0000 dB (four decimal places on eight
frequencies), T6's closed form, and the byte-identity of the three
interpreters. **It is not an independent pass** — nobody but this session has
looked at these numbers, and §11 says so.

---

## 2. Tier 1 invariants

Every cell below is a run, not an inference. The unittest battery is CPython
only, so the per-interpreter table is filled from
`tools/phase2_probes/dynamiceq_tier1.py`, which is the same measurements in
the subset all three interpreters have:

```
$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      tools/phase2_probes/dynamiceq_tier1.py
0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      -X heapsize=512M tools/phase2_probes/dynamiceq_tier1.py
0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=512M tools/phase2_probes/dynamiceq_tier1.py
0 failures
```

The three transcripts are **identical line for line**, numbers included
(`diff` over both pairs, empty). Each runs every row at 48 000, 44 100 and
22 050 Hz and at `channel_count` 2 and 1 — thirty rows an interpreter.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass, 0 LSB | pass, 0 LSB | pass, 0 LSB | pass, 0 LSB | pass, 0 LSB | pass, 0 LSB | pass, 0 LSB | pass, 0 LSB | pass, 0 LSB |
| `mix` 0 is a wire, byte-identical to the source delayed by `latency_samples` | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass, +0.0000 dB | pass | pass | pass, +0.0000 dB | pass | pass | pass, +0.0000 dB | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass, 0 = 0 | pass | pass | pass, 0 = 0 | pass | pass | pass, 0 = 0 | pass | pass |
| `reset()` leaves every node the class built silent and stateless, and the borrowed source untouched | STATE | pass, 0 LSB | pass | pass | pass, 0 LSB | pass | pass | pass, 0 LSB | pass | pass |
| `deinit()` releases every node the class built and leaves the source rendering | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `capabilities` names exactly the optional behaviours honoured | STATE | pass, read 0× | pass | pass | pass, read 0× | pass | pass | pass, read 0× | pass | pass |
| Pulling `output` allocates nothing | STATE | pass, +/−2 objects over 20 pulls | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Rate-honest: Hz spans and options clamp below Nyquist, never refuse | RESPONSE | pass, 16 000 Hz applied (0.4·F_s is 19 200) | pass | pass | pass, 16 000 applied (0.4·F_s is 17 640) | pass | pass | pass, **8820 applied** for 16 000 asked | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass | pass | pass | pass | pass | pass | pass | pass | pass |

The allocation row is CPython-only on purpose: it counts `gc.get_objects()`
across twenty pulls (14 557 → 14 555), and neither MicroPython build exposes
that. On a board it is `gc.mem_alloc()` in the cost run, which is §4's and is
**not done**.

**Mono.** The dossier's §4 says a mono source gets the same processing, not a
mono sum of a stereo behaviour: every node honours `channel_count` 1 and the
Splitter duplicates a mono frame across its ring. Measured: **−14.577 dB at
f₀ at one channel and −14.577 dB at two**, and the whole Tier 1 block above
is run at both. The mono render digest is identical on all three
interpreters (§3).

**Planted faults for this block**, each with its clean control:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | dry voice at 32767/32768 on a 1 kHz tone | byte-identical | RED, first differing sample **3** |
| TAIL | the same 60 Hz section on the ported Q12 biquad (audioif#23's own shape) | 0 LSB residual | RED, **2 LSB** held for ever |
| CLICK | `latency_samples` reported 256 short, DSP untouched | 0 = 0 | RED, measured **0** against a reported **256** |
| STATE | the tail alone reset, nothing upstream — `_core.reset()`'s shape and §7's defect | **0 LSB** | RED, **3516 LSB** of ring-down replayed |
| (the guard) | the Splitter fed straight off a 40000-frame `RawSample` | peak **20000** | RED, peak **0** |

The STATE fault only works because the reset lands **32 frames after** a
300 Hz burst at Q 12, inside a 7680-sample ring-down. A reset taken after the
tail had already reached zero left 0 LSB either way — the first cut of this
measurement, recorded here rather than quietly fixed.

`reset()` and `deinit()` walk the node list `_component` requires the class
to enumerate with `self._own()`. Nodes enumerated by this class, in
registration order — which is reset order reversed, so the walk is guard,
notch, band, cell, taps, mixer, tail:

`MidSide` tail · `Mixer` (its own `_reset_mixer`) · `SplitterTap` 0, 1, 2 ·
`Splitter` (reset and deinit both `False`: it is a container with neither on
any build here) · `Dynamics` · `Biquad` band-pass · `Biquad` notch ·
`Filter` guard.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, from `tools/render_effect.py`, which prints the
blind `sum(data)` beside it.

```
$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      tools/render_effect.py DynamicEQ chord <out> --rate 48000
DynamicEQ chord 48000 Hz 2ch block 256 -> 144000 frames  fnv 8680ecc9  sum 90043706  audio
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 2048 | `8680ecc9` | `8680ecc9` | `8680ecc9` | *(board run)* | *(board run)* |
| `chord` | 44100 | 2048 | `c6bb5a2d` | `c6bb5a2d` | `c6bb5a2d` | *(board run)* | *(board run)* |
| `chord` | 22050 | 2048 | `b2fb14e5` | `b2fb14e5` | `b2fb14e5` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2048 | `db568f0d` | `db568f0d` | `db568f0d` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 2048 | `29950e55` | `29950e55` | `29950e55` | *(board run)* | *(board run)* |
| `noise_det` | 22050 | 2048 | `cf4de099` | `cf4de099` | `cf4de099` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 2048 | `6864c2fd` | `6864c2fd` | `6864c2fd` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 2048 | `3dd2b899` | `3dd2b899` | `3dd2b899` | *(board run)* | *(board run)* |
| `sweep_log` | 22050 | 2048 | `45eeaaa9` | `45eeaaa9` | `45eeaaa9` | *(board run)* | *(board run)* |
| `chord`, `channel_count` 1 | 48000 | 2048 | `8ce8a468` | `8ce8a468` | `8ce8a468` | *(board run)* | *(board run)* |

The "Block" column is `render_effect.py`'s output buffer; the source block
size is its own axis and is the ladder below.

**Desktop agreement:** CPython, desktop MicroPython **and the patched
CircuitPython build** render identical bytes on every probe, rate and channel
count above — ten renders, three interpreters, thirty digests, no
disagreement.

**That was not true when this class was first built.** Every
`circuitpython-effects` render came back `sum 0 SILENT` — `319d7901`,
`9ae7a5c5` and the rest, all of them the digest of silence — while the smoke
and a hand-pumped probe passed on the same interpreter. The cause is not the
class's DSP: `render_effect.py:717` calls `audiocore.reset_buffer(effect.output)`
before every render, and upstream CircuitPython's `audiomixer.Mixer` **stops**
every voice on reset rather than rewinding it. A class that ends in a Mixer
is silent there from the first thing that resets it. The fix is an
`audioroute.MidSide` identity carrying the output; the digests above are with
it. **`MultibandCompressor` has the same defect on its own branch** —
`MultibandCompressor chord 48000 … fnv 9ae7a5c5 sum 0 SILENT` on
`circuitpython-effects`, run here 2026-09-07 — and its evidence pack does not
record it.

**Board agreement:** **not measured.** No P4 or S3 leg was taken in this
session; §11.

**Block-size ladder** (the source's `get_buffer` size, `--block`), `chord` at
48 kHz on CPython:

```
block   256  fnv 8680ecc9
block  8192  fnv 8680ecc9
block 16384  fnv 8680ecc9
block 20000  fnv 8680ecc9
block 32768  fnv 8680ecc9
```

Byte-identical at every point on `MultibandCompressor` M5's ladder. Its
planted fault is the guard: the same graph with the Splitter fed straight off
a 40000-frame `RawSample` renders peak **0** where the guarded one renders
peak **20000**.

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
target `effect:DynamicEQ`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: **ESP32-P4 ≤ 8 %** of one stereo block's real-time deadline,
**ESP32-S3 ≤ 25 %**. Lean patch expected: **no, and one is not possible** —
§8 D2 of the dossier: a patch only moves macros and every node here runs
every block whatever they say, and the lean *build* the seed proposed needs
node ask N-DEQ-1.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("DynamicEQ", …)` | 951.9 | 1.051 (0.738 marginal) | 5.08 | 46 KB | **no** — 13.8 % marginal, 19.7 % total, against ≤ 8 % |
| S3 | 0 | construction defaults, `audioeffects.create("DynamicEQ", …)` | 549.2 | 1.821 (1.349 marginal) | 2.93 | 46 KB | **no** — 25.3 % marginal, 34.1 % total, against ≤ 25 % |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:DynamicEQ`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 ≤ 8 %, S3 ≤ 25 %.

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`f5c99d1ed5e84f81` on the ESP32-P4 and `f5c99d1ed5e84f81` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is `ef4ac9527a734709` — it **differs**.

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

**Owed: a `" - lean"` patch.** At 25.3 % of the deadline the class is over
its ESP32-S3 budget of ≤ 25 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** anything beyond construction defaults.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**The desktop anchor, which is not a board figure and is not a substitute for
one.** `tools/measure_effect_cost.py`, 256-frame stereo blocks at 48 kHz, on
this x86-64 machine under CPython 3.12.3 — where the cost is dominated by
per-block Python overhead rather than by the DSP, so it ranks builds against
each other on one machine and says nothing about either board. **Five
interleaved repeats of each build**, so the two meet the same machine:

```
rebuilt  blocks/s 686.0  rt 3.66  ms/block 1.458  control 0.342  marginal 1.116
shipped  blocks/s 866.3  rt 4.62  ms/block 1.154  control 0.391  marginal 0.763
rebuilt  blocks/s 663.6  rt 3.54  ms/block 1.507  control 0.356  marginal 1.150
shipped  blocks/s 884.0  rt 4.71  ms/block 1.131  control 0.358  marginal 0.773
rebuilt  blocks/s 640.9  rt 3.42  ms/block 1.560  control 0.360  marginal 1.200
shipped  blocks/s 888.5  rt 4.74  ms/block 1.125  control 0.365  marginal 0.761
rebuilt  blocks/s 683.0  rt 3.64  ms/block 1.464  control 0.349  marginal 1.115
shipped  blocks/s 893.8  rt 4.77  ms/block 1.119  control 0.350  marginal 0.769
rebuilt  blocks/s 678.1  rt 3.62  ms/block 1.475  control 0.354  marginal 1.121
shipped  blocks/s 909.1  rt 4.85  ms/block 1.100  control 0.347  marginal 0.753

node:audiobiquad.Biquad      blocks/s 2810.6  rt 14.99  ms/block 0.356  marginal 0.014
node:audiodynamics.Dynamics  blocks/s 2809.3  rt 14.98  ms/block 0.356  marginal 0.011
node:audioroute.Splitter     blocks/s 2782.0  rt 14.84  ms/block 0.359  marginal 0.014
```

**The rebuild costs about 45 % more per block than the class it replaces**
(1.458–1.560 against 1.100–1.154 ms, 27–29 % of the 5.333 ms deadline against
21–22 %), and that is the price of three nodes the shipped class does not
have: the guard that keeps a long source from vanishing, the third splitter
tap that makes `Mix` 0 a real bypass, and the identity tail that keeps the
class from rendering silence on CircuitPython.

**An earlier pair from this session is withdrawn.** It read 1.696 against
1.958 ms/block with the rebuild *ahead*, and it was taken with three other
class-builder sessions running on this machine at a load average above 20;
the pair above was taken at a load average under 4 and reverses the ordering.
It is recorded rather than deleted because a cost number off a shared machine
is exactly the kind that gets quoted later.

The expensive path is reached rather than idled past: the run uses patch 0 at
its defaults, threshold −30 dBFS against material that crosses it, so the
gain cell is working and not sitting at unity — the runner refuses a render
whose digest is the digest of silence, and it did not refuse this one. Digest
printed beside the CPU figure: `ef4ac9527a734709` (rebuild),
`000270daf6433885` (shipped).

---

## 5. Latency

Reported `latency_samples` = **0**, at every setting, for the life of the
instance.

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0 (impulse in at frame 50, peak 20000 out at frame 50) | 0 | 0.000 |
| 44100 | 0 | 0 (same) | 0 | 0.000 |
| 22050 | 0 | 0 (`dynamiceq_tier1.py` CLICK row) | 0 | 0.000 |

Dossier latency budget: zero. Met: **yes**.

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none)* | — | — | — | — |

There is no such option on this class. `audiodynamics`' `lookahead_ms` is the
only one on the palette that could add any and it is **deliberately not
exposed** — a dynamic EQ that ducked before the note arrived would be a
different instrument — so there is no millisecond figure to name in the
docstring, and the docstring says that rather than leaving it out.

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
**RED**, measured 0 against a reported 256, and the audio is unchanged
(the fault is a subclass override, not a graph change).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 30 Hz … 16 kHz, log, clamped to 0.4·F_s | the band's frequency knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 12, log, shown as Q | the Q knob (S6) |
| 2 | Threshold | UNIPOLAR | −60 … 0 dBFS | the threshold knob (S6) |
| 3 | Ratio | UNIPOLAR | 1 … 20, log | the ratio knob (the node's) |
| 4 | Attack | UNIPOLAR | 0.1 … 100 ms, log | the attack knob (S6) |
| 5 | Release | UNIPOLAR | 5 … 1000 ms, log | the release knob (S6) |
| 6 | Mix | UNIPOLAR | 0 … 1 | the range/depth knob (S6) **and** parallel processing — T6 |
| 7 | Listen | TOGGLE | off / the processed band alone | the band-solo button |

Eight, under the sixteen the module refuses a seventeenth of. The dossier's
proposed ninth and its Direction toggle are **not** here and the reasons are
in the dossier: Range is Mix (D4), and direction is a constructor argument
because `audiodynamics` fixes its mode at construction (D6).

| Patch | Name | What it is for |
|---|---|---|
| 0 | Wide Band | the constructor's defaults on the 0-127 grid — 3 kHz, Q 2, −30 dBFS, 4:1, 2 ms, 80 ms, mix 1 |
| 1 | Boxiness Control | 400 Hz, Q 2.5, −24 dBFS, 3:1, 10 ms, 150 ms |
| 2 | Harshness Control | 3.2 kHz, Q 3, −28 dBFS, 4:1, 1 ms, 60 ms |
| 3 | Low End Tamer | 80 Hz, Q 1.2, −20 dBFS, 4:1, 20 ms, 250 ms |
| 4 | Sibilance | 7 kHz, Q 4, −30 dBFS, 8:1, 0.2 ms, 40 ms |
| 5 | Half Measure | 3 kHz, Q 1, −34 dBFS, 6:1, 5 ms, 200 ms, **mix 0.5** — the same band held to a 6 dB ceiling |

Patch 0 is held to the constructor's defaults **span by span** rather than to
a copied list (`Surface.test_patch_zero_is_the_constructors_defaults`).

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change`; a program index this class does not
have is ignored and leaves `patch_index` where it was. Shown by
`tests/test_cpython_effects_dynamiceq.py::Surface::test_patch_index_follows_the_contract`.

**`capabilities` = `()`.** The dossier's one-line reason: *attack and release
are absolute times, not beat fractions, and nothing else here is measured in
bars.* Held to it by a test that hands the class a transport which records
being called, renders a second of audio, moves every macro and changes patch:
**read 0 times**.

---

## 7. Portability tier

**Tier:** audioif. `REQUIRES = ("audiobiquad", "audiodynamics", "audioroute")`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Biquad` NOTCH, `Biquad` BAND_PASS | `audiobiquad` | T1, T5, and the Tier 1 tail row | `audiofilters.Filter` keeps its state in Q12 sample units and rounds to nearest with no dither, so the recursion has fixed points: the same 60 Hz section holds **2 LSB for ever** (measured here as TAIL's planted fault), against 0 LSB on the float node |
| `Dynamics` | `audiodynamics` | T2, T3, T5 | Not a CircuitPython module at all — it is audioif's, from micropython-vst3's engine. There is no gain computer on the ported palette |
| `Splitter` | `audioroute` | T1, T4, T6 — the split needs the same stream down three branches | Also audioif's own; `audiomixer` can sum but nothing ported can fan out |
| `MidSide` (identity tail) | `audioroute` | the CircuitPython Mixer-reset defect in §3 | Added 2026-09-07; the identity at width 1 is exact, bit for bit |

```
$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      -m unittest tests.test_portability_tier
Ran 7 tests in 0.031s

OK
```

The class appears in that battery automatically — it walks `audioeffects.ALL`
and `rebuilt.known()`.

**What that test does not prove**, and every pack must repeat it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class has
not been shown rendering on a stock CircuitPython build of the ported C. That
is a gap in the method, not in this class — and it does not bite this class,
whose tier is audioif and whose claim is that it *raises*.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed or unmeasured. **Six
      demonstrated, none disconfirmed, none unmeasured.**
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on the patched CircuitPython build; every
      Tier 2 measurement names its rate.
- [x] Every demonstrated Tier 2 trait has a measurement shown red on a
      planted fault of the same kind.
- [ ] Every demonstrated trait survived an independent refutation attempt.
      **Not met.** The refutation pass was run by this session against its own
      results; nobody else has looked. §1 and §11 say so.
- [x] CPython and desktop MicroPython render identical bytes — and so does
      `circuitpython-effects`. The P4 and S3 digests are **not taken**.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 13.8 % and S3 25.3 % of the deadline (marginal) against ≤ 8 % / ≤ 25 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz (and at 22.05 kHz); the budget is met; there is no
      latency-adding option, and the docstring says so.
- [x] The class declares eight macros and five named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass
      (§9). **No old-surface trait test needed retiring**: the pre-rebuild
      `DynamicEQ` had no test of its own in
      `tests/test_cpython_effects_dynamics_eq.py`.
- [x] The README catalogue row and the docstring describe the standout, the
      portability tier and the cost, in a musician's terms.
- [x] The class's code, its battery, the README row and the CHANGELOG line
      landed together in `d77543a`; this file lands in the commit that
      follows it, which §0 names.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      -m unittest discover -s tests -p "test_*.py"
Ran 260 tests in 1250.201s

OK (skipped=1)

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      -m unittest tests.test_portability_tier
Ran 7 tests in 0.031s

OK

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      -m unittest tests.test_cpython_effects_dynamiceq
Ran 33 tests in 79.841s

OK

$ PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \
      tools/phase2_probes/dynamiceq_tier1.py            # and on mp and cpy
0 failures

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:DynamicEQ")'
ROW	effect:DynamicEQ	951.9	5.08	1.051	0.313	0.738	46656	f5c99d1ed5e84f81
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:DynamicEQ")'   # the S3
ROW	effect:DynamicEQ	549.2	2.93	1.821	0.472	1.349	46688	f5c99d1ed5e84f81
```

The three smoke runs and the three `dynamiceq_tier1.py` runs are separate
invocations of the same file under three interpreters; their last lines are
quoted above, one per interpreter.

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

- **No surface at all** (`eq.py:231`) → eight macros and six patches, every
  one live.
- **Nothing is live** (`eq.py:235-236`, `:240`, `:243`) → Frequency and Width
  reach both sections from one place on every macro move; threshold, ratio,
  attack and release go through `Dynamics.set()`.
- **Attack and release hard-coded** at 2 ms and 80 ms (`eq.py:248`) → macros
  4 and 5, spans 0.1–100 ms and 5–1000 ms.
- **No range, no direction** (`eq.py:247`) → `Mix` is the range control
  (T6, `range_db`), and `expand=True` is the other direction, as a build.
- **The Mixer at a 1024-byte buffer** (`eq.py:250`) against the Filters' 2048
  → one 256-frame block through the whole graph. It did **not** make the
  class cheaper: the rebuild costs about 45 % more per block on the desktop
  (§4), because it also added a guard, a third tap and an identity tail. What
  the single block size buys is that every node in the chain is doing the same
  amount of work per pull.
- **`reset()` and `deinit()` reach the Mixer only** (`_core.py:366-374`,
  `:376-385`) → nine nodes enumerated with `self._own()` and both walks go
  over all of them; the old shape is this class's STATE planted fault and it
  leaves 3516 LSB.
- **No tail declared** (`TAIL_SAMPLES = None`) → `tail_samples` is the pole
  pair's ring, `4·Q·F_s/f₀ + 1`, longer than the worst measured ring at every
  corner of both spans.
- **Built on the Q12 ported biquad** → `audiobiquad`, and the reconstruction
  goes from 0.015 dB to 0.0000 dB while a low band's held DC goes from the
  family's 1–4 LSB to 0.

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 13.8 % and S3 25.3 % of the deadline (marginal)
  against ≤ 8 % / ≤ 25 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **The refutation pass is not independent.** It was run by the session that
  wrote the class, against its own results. Two faults it caught are recorded
  in §1; what a second reader would catch is unknown.
- **Tier 2 is measured at 48 kHz only**, except T2's law, which is also run
  at 44.1 and 22.05 kHz in §2. T1, T4, T5 and T6 have no reading at the lower
  rates.
- **`expand=True` carries no trait row.** It has one check in the battery
  (a wire above the threshold, exact zero well below it) and no dossier trait
  of its own, so it is exercised rather than demonstrated.
- **The `-inf` in that check is a floor, not a measurement.** At −46 dBFS
  against a −30 dBFS threshold the band comes out below one LSB, so the
  number is "exact zero" rather than a depth in decibels.
- **`MultibandCompressor` renders silent on `circuitpython-effects` through
  the kit** (§3) and its evidence pack does not record it. Found here, not
  fixed here — it is another class on another branch.
- **The library smoke's probe budget was changed** in `d77543a` to make room
  for six patches. It is a shared file, so every other Phase 2 worktree will
  meet it as a conflict or a surprise.
- **The desktop cost figures come off a machine shared with other sessions.**
  The first pair taken in this session had the ordering the wrong way round
  and is withdrawn in §4. Even the accepted pair is a ranking on one x86-64
  machine under CPython; it is not evidence about the P4 or the S3, and
  nothing here says the class fits its budget.
- **The rebuild is more expensive than the class it replaces**, by about 45 %
  per block on the desktop. That is a fact about this build, not a
  measurement that is still to come.
