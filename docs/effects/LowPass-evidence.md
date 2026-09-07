# Evidence Pack — `LowPass` (no historical standout — design grade)

Written at Station C from [`EVIDENCE-TEMPLATE.md`](EVIDENCE-TEMPLATE.md),
one section per gate item, in the gate's order
(`docs/effects-roadmap.md`, "The class gate").

**Three rules this file is written under.** Numbers come from runs, each
carrying its command, interpreter and rate. A measurement with no planted
fault beside it is not cited. §11 is a section, not a clause.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `LowPass` |
| Dossier | [`LowPass.md`](LowPass.md), traits fixed 2026-09-06, seven decisions settled 2026-09-07 at `331ba1c` |
| Module | `lib/audioeffects/rebuilt/lowpass.py` |
| Base | `_component.Component` |
| Family / phase | EQ / Filter, roadmap Phase 2 |
| Standout | none — the two-pole analog low-pass prototype, `H(s) = 1/(s² + 2Rs + 1)` |
| Grade | design |
| Portability tier | **audioif** (`REQUIRES = ("audiobiquad",)`) |
| Landed in commits | `331ba1c` dossier · `3548ae4` class, README row, CHANGELOG line, this class's tests and the three files that had to move with it · this file's own commit. Not one commit: Station A froze the dossier before any code was written, which is the order the roadmap asks for. |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed`. The `audioif` checkout the venv was built from is at `98ae4bf`, which differs from the pin only in `.flake8` and `apply_cp_patches.sh` — `git diff --stat 2f6cbc3 HEAD -- src/` is empty, so every line of C and Python that renders here is the pin's. |
| Interpreters | `audiocomponents/.venv/bin/python` CPython 3.12.3, numpy 2.5.2 · `cmods/bin/micropython` MicroPython v1.28.0-dirty (2026-09-07) · `cmods/bin/circuitpython-effects` CircuitPython 10.2.1-dirty (2026-09-07) |
| Boards | **not run.** No P4 or S3 leg was taken in this session — §4 and §11. |

**Dossier trait set frozen before the rebuild began:** yes. T1–T5 were fixed
in the Phase 0 seed and are unchanged here; Station A settled §8's questions
and froze §6's surface, and both landed in `331ba1c` before
`lib/audioeffects/rebuilt/lowpass.py` existed.

---

## 1. Traits

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation |
|---|---|---|---|---|---|
| T1 | \|H(f₀)\| = Q exactly, within 0.05 dB, for Q ∈ {0.5…16} | **demonstrated** | steady sine at f₀ = 1 kHz, exact-bin DFT over the settled half; 48 kHz, cpython. Worst deviation **0.000 dB** over seven Qs **at both slopes** (bar 0.05) | (a) A2's own fault — one source level for every Q, so Q·level > 28 000: Q 16 reads **+21.473** against +24.082, **−2.609 dB RED**, while Q 8 at the same level stays green. (b) the kit's RESPONSE fault, `ShiftedCornerLowPass`: corner **1148.9 Hz** against 1000, **14.9 % out, RED**, passband green at −0.004 dB | "It only holds because the second section is a wire." Answered: the 24 dB/oct rows are the same to 0.001 dB, and that is a design decision, not luck — the resonance rides section 2 alone against a fixed Butterworth 0.5412 in section 1. Scaling both is the fault `tests/test_cpython_effects_lowpass.py::test_scaling_both_butterworth_qs_is_red` plants, and it lands on 40·log₁₀(Q)+3.01 |
| T2 | shape invariance on the bilinear-warped axis, f₀-independent for 20 Hz…0.4·F_s; bar 0.05 dB between any two f₀ at the same f_a/f_a0 | **demonstrated** | six corners 31.5 Hz…4 kHz × six ratios 1/8…8, each an exact-bin DFT; 48 kHz, cpython. Worst spread across corners **0.0135 dB** (bar 0.05) | one section retuned 15 % at 24 dB/oct: worst deviation **2.871 dB, RED** | "0.0135 dB is not zero — the dossier says 0.00000." Answered: the dossier's 0.00000 is A13's *arithmetic* on the coefficients; this is a render through int16, and the whole 0.0135 sits in the 31.5 Hz row's 1/8 ratio — a 3.94 Hz tone, the lowest thing the probe set can carry. Every other row agrees to 0.002 dB |
| T3 | −12.03 dB/oct on the warped axis: −24.10 dB at 4·f_a0, −36.13 at 8·f_a0, at every f₀; DC 0.00 ± 0.1 dB | **demonstrated** | four corners 31.5 Hz…2 kHz, stopband probes at −6 dBFS; 48 kHz, cpython. **−24.099/−24.100 dB** at 4·f_a0 and **−36.125** at 8·f_a0 at every corner, fitted **−12.025 dB/oct**; DC within **0.014 dB** | the second section left as a wire at 24 dB/oct: fitted **−11.754 dB/oct** against −23.983, **RED** | "The first run read −22.2 dB/oct at 24 dB/oct — was that hidden?" No: it is recorded here. At −20 dBFS the 8·f_a0 point of a fourth-order roll-off lands at −92 dBFS, under one LSB, so that run measured the quantizer. Re-run at −6 dBFS it reads −23.97…−24.00. Both runs are in §9 |
| T4 | struck with a click it rings at f₀, envelope to e^{−π} in Q periods, for Q ∈ {2,4,8,16}, bar 0.8–1.25 Q | **demonstrated** | `click_stereo` through a 500 Hz corner, Hilbert envelope; 48 kHz, cpython. 1.74 / 3.62 / 7.53 / 15.43 periods for Q 2 / 4 / 8 / 16 — every one inside its band | the resonance halved on the section: Q 4 reads **1.74 periods** against a 3.20–5.00 bar and Q 16 reads **7.53** against 12.80–20.00, **both RED**, with the clean run green beside each | "1.74 periods for Q 2 is near the 1.60 floor." True, and S3 states the law for Q ≫ ½, which is why the dossier's own bar starts at Q 2 and the band is asymmetric. Q 4, 8 and 16 sit at 0.90, 0.94 and 0.96 of Q |
| T5 | rate-honest against the closed form **at the running rate**: corner within 0.1 %, \|H(f₀)\| = Q, swept points within 0.1 dB | **demonstrated** | \|H(f₀)\| at 1 kHz: **−3.010 / −3.011 / −3.009 dB** at 48 000 / 44 100 / 22 050 Hz (want −3.010). Against S1's closed form evaluated at each rate, six probes 125 Hz…4 kHz: worst **0.0009 / 0.0009 / 0.0011 dB** (bar 0.1) | a corner expressed in 48 kHz units on a 22.05 kHz graph — the "designed at 48 kHz and never scaled" bug: corner built at 2176.9 Hz, worst **13.711 dB** from the closed form, **RED**, against 0.001 dB clean | "Your first T5 fault didn't fire." It did not, and that is recorded: removing the class's Nyquist clamp changed nothing measurable, because a corner at 0.9·F_s and one at 0.49·F_s both warp to at-or-past Nyquist and both render flat. The clamp is a second line of defence, not the only one; the fault that fires is the one above |

**Characters.** None. A low-pass has one behaviour (dossier §3).

**Refutation pass.** Run by this session against its own results, 2026-09-07,
before the pack was written. What it went after: whether T1 held at 24 dB/oct
for a reason or by accident (it is a design decision, and the alternative is
planted as a fault); whether T3's shortfall at 24 dB/oct was the class or the
measurement (the measurement — the int16 floor — and both runs are recorded);
and whether the T5 fault was a fault at all (it was not, and it was replaced
rather than quietly dropped). What it could not break: T2 and T4.

---

## 2. Tier 1 invariants

Two kinds of run stand behind this block, and the difference matters.

* **The kit's own measurements** (WIRE, TAIL, LEVEL, CLICK, STATE) are numpy
  and run under CPython only — spec §1, "the render is dual-runtime, the
  analysis is not". Command:
  `PYTHONPATH=.../ac-wt-lowpass/lib .venv/bin/python station_c.py tier1`,
  at 48 000 / 44 100 / 22 050 Hz and at `channel_count` 1 and 2.
* **A numpy-free twin** runs the same invariants natively on all three
  interpreters — WIRE, WIRE-with-a-trim, TAIL, reset/resume, deinit and the
  Nyquist clamp, as integers. Command:
  `MICROPYPATH=.../ac-wt-lowpass/lib:.../cmods/micropython/lib
  cmods/bin/micropython -X heapsize=512M tier1_native.py`
  (and the CircuitPython and CPython equivalents).

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass (0 LSB) | pass (0) | pass (0) | pass (0) | pass (0) | pass (0) | pass (0) | pass (0) | pass (0) |
| `mix` 0 is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| …and still a wire with a trim asked for | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path | LEVEL | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ |
| `reset()` leaves every node silent and the borrowed source untouched | STATE | pass (0 LSB, source resumes) | pass | pass | pass | pass | pass | pass | pass | pass |
| `deinit()` releases every node the class built and leaves the source rendering | STATE | pass (0 live) | **n/a²** | **n/a²** | pass | **n/a²** | **n/a²** | pass | **n/a²** | **n/a²** |
| `capabilities` names exactly what is honoured (`tempo_sync` iff the transport is read) | STATE | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ |
| Pulling `output` allocates nothing | STATE | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ | pass | n/a¹ | n/a¹ |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass (20 000 Hz) | pass | pass | pass (20 000 Hz) | pass | pass | pass (10 804.5 Hz) | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass | pass | pass | pass | pass | pass | pass | pass | pass |

¹ **n/a: the analysis is CPython-only.** These four read an FFT, a
`tracemalloc` count or a sub-sample onset. What carries them to the other two
interpreters is §3: every probe renders **byte-identical** on all three, so a
measurement over those bytes has the same answer whichever build produced
them. That is an inference, and it is stated as one.

² **n/a: `audiobiquad.Biquad` has no `deinit()` on the native builds.**
Surveyed across all three interpreters (§9): on the CPython target every
audioif-own class has one; on MicroPython and CircuitPython **none of them
does** — `audiobiquad`, `audioladder`, `audioshaper`, `audioverb`,
`audiomath`, `audioecho`, `audioroute` and `audiodynamics` all lack it, and
only the ported `audiofilters` and `audiomixer` have it there. So
`Component.deinit()`'s walk finds nothing to call, harmlessly, and there is
no flag to read back. This is a node gap that reaches **every audioif-tier
rebuilt class**, not this one — §11.

**Mono.** The dossier's §4 says a mono source gets the identical filter.
Measured: at `channel_count` 1 and 2, same settings (f₀ 1 kHz, Q 2), the
gains agree to **+0.0000 dB** at every probe and every rate —

```
  48000 Hz  probe   250  1ch  +0.4827  2ch  +0.4827  diff +0.0000 dB
  48000 Hz  probe  1000  1ch  +6.0207  2ch  +6.0207  diff +0.0000 dB
  48000 Hz  probe  4000  1ch -23.9998  2ch -23.9998  diff +0.0000 dB
  22050 Hz  probe  4000  1ch -25.6155  2ch -25.6155  diff +0.0000 dB
```

and the 1-channel render is byte-identical across the three interpreters
(§3).

**Planted faults for this block**, each with its clean control beside it. All
at 48 kHz, cpython; the same faults fire at 44.1 and 22.05 kHz.

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | dry path × 32767/32768 (`kit_faults.OneLsbScale`) on `ramp_fs` | green, 0 differing samples | **RED** — 8192 of 16384 samples differ, first at frame 0, max 1 LSB |
| TAIL | +1 LSB of DC in the settled state (`kit_faults.StuckDc`) | green, residual 0, `tail_samples` 1122 | **RED** — residual 1 LSB in the last 13 440 frames; no last non-zero sample; and the `dc_step` leg leaves 1 LSB after the offset is removed |
| LEVEL | +0.1 dB of hidden gain (`kit_faults.HiddenGain`) | green | **RED** — +0.100 dB on both channels against a 0.050 dB bar |
| CLICK | `latency_samples` reported 256 short, DSP untouched | green, measured [0.0, 0.0] against a reported 0 | **RED** — measured [0.0, 0.0] against a reported 256, 256.0 samples out |
| STATE | a node left live after `deinit()` (`_deinits[0] = False`) | green, `live_nodes_after_deinit` `[]` | **RED** — `deinit() left ['section 0'] live` |
| STATE | a section not cleared by `reset()` (`_resets[0] = False`) | green, residual 0 LSB | **RED** — after `reset()` and a silent source the output still reaches **7232 LSB** |
| STATE | `capabilities` claims `tempo_sync` while the transport is not read | green, `capabilities []` | **RED** — `capabilities ['tempo_sync'] against a transport read that does not change the render` |

`reset()` and `deinit()` walk the node list `_component` requires the class
to enumerate with `self._own()`. **Nodes enumerated by this class, in build
order:** `_pole_one` (`audiobiquad.Biquad`, `LOW_PASS`), `_pole_two`
(`audiobiquad.Biquad`, `LOW_PASS`), `_trim` (`audiobiquad.Biquad`,
`HIGH_SHELF` at 5 Hz). All three are `reset=True, deinit=True`.

**One thing the kit could not do, and what was done instead.**
`effect_measurements.enumerate_nodes()` walks the instance's **public**
attributes; every node a `_component` class owns is private, so it would have
found `_output` alone and a fault in either other section would have been
invisible. The `STATE` runs above pass `nodes=` built from the class's own
`_own()` list — which is exactly what `reset()` and `deinit()` walk. The
faults in the table are the proof that this matters: `deinit() left ['section
0'] live` is a row `enumerate_nodes()` would have reported green.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes. `sum(data)` is never the comparison.

Command (one line per interpreter):

```
PYTHONPATH=<worktree>/lib .venv/bin/python tools/render_effect.py \
    LowPass chord <out> --rate 48000
MICROPYPATH=<worktree>/lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tools/render_effect.py LowPass chord <out> --rate 48000
MICROPYPATH=<worktree>/lib:../cmods/micropython/lib \
    ../cmods/bin/circuitpython-effects -X heapsize=256M \
    tools/render_effect.py LowPass chord <out> --rate 48000
```

| Probe | Rate | Ch | Block | Settings | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 2 | 256 | patch 0 | `85052551` | `85052551` | `85052551` | *(board run)* | *(board run)* |
| `chord` | 44100 | 2 | 256 | patch 0 | `8629ae91` | `8629ae91` | `8629ae91` | *(board run)* | *(board run)* |
| `chord` | 22050 | 2 | 256 | patch 0 | `03746041` | `03746041` | `03746041` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2 | 256 | patch 0 | `5dda3399` | `5dda3399` | `5dda3399` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 2 | 256 | patch 0 | `5c156905` | `5c156905` | `5c156905` | *(board run)* | *(board run)* |
| `noise_det` | 22050 | 2 | 256 | patch 0 | `c5347fc9` | `c5347fc9` | `c5347fc9` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 2 | 256 | patch 0 | `8fe32021` | `8fe32021` | `8fe32021` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 2 | 256 | patch 0 | `bf925e2d` | `bf925e2d` | `bf925e2d` | *(board run)* | *(board run)* |
| `sweep_log` | 22050 | 2 | 256 | patch 0 | `bd2ae839` | `bd2ae839` | `bd2ae839` | *(board run)* | *(board run)* |
| `chord` | 48000 | 1 | 256 | patch 4 Squelch | `c4733a0b` | `c4733a0b` | `c4733a0b` | *(board run)* | *(board run)* |
| `chord` | 48000 | 2 | 256 | 24 dB/oct, **mix 0.005** | `7306a6f1` | `7306a6f1` | `7306a6f1` | *(board run)* | *(board run)* |
| `chord` | 48000 | 2 | 256 | 24 dB/oct, **mix 0.5** | `07e050f1` | `07e050f1` | `07e050f1` | *(board run)* | *(board run)* |

**Desktop agreement: yes.** All three interpreters render identical bytes on
every row, at every rate, in mono and in stereo.

**The two rows that were the reason for asking.** The dossier's A9 records
that `audiofilters.Filter` bypasses its cascade below `mix = 0.01` on
MicroPython while the CPython target blends, and A14 records that a
*cascade* at `mix = 0.5` renders peak 5129 on one and 1211 on the other with
different digests. Both are the shapes this class's surface would have hit —
Slope 24 dB/oct with Mix anywhere between the ends. Neither reaches it:
`audiobiquad`'s `mix` is per-section in one C kernel both targets share, and
the two rows above are byte-identical. That settles the dossier's **D6** —
the `(0, 0.01]` snap §6 proposed is not needed and is not implemented.

**Board agreement:** not measured. No P4 or S3 leg was taken — §11.

**Block-size ladder.** `chord`, 48 kHz, patch 3, at the spec's whole ladder —
block 256, 8192, 16384, 20000, 32768 — on all three interpreters: **fifteen
renders, one digest, `68d7ac39`**. The rung that matters is 16384 and above:
`MultibandCompressor` M5 renders zero non-zero samples there because the
Splitter's ring is 8192 frames, and this class builds no Splitter.

---

## 4. Tier 3 — cost on the boards

*(Left for the board run. Nothing in this section is filled in.)*

Dossier budget: **ESP32-P4 ≤ 1.5 %** of one stereo block's real-time deadline
and **ESP32-S3 ≤ 5 %** at the 12 dB/oct default; **≤ 2.5 % / ≤ 9 %** with
24 dB/oct engaged. Lean patch expected: **no** — if the S3 misses the steeper
budget, the Slope macro's high setting is what gives.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | | | | | | *not run* |
| S3 | 0 | | | | | | *not run* |
| S3 | 2 Steep Cut (24 dB/oct) | | | | | | *not run* |

**The expensive path** a board run must reach: patch 2 or 4, which put both
LOW_PASS sections at `mix = 1` and (patch 4) the trim section too — three
active biquads. Patch 0 idles two of the three as wires and would understate
the class by roughly a factor of three. `tools/measure_effect_cost.py` was
**not run**: it needs a board on a serial port and there is none in this
session.

---

## 5. Latency

Reported `latency_samples` = **0**, at every setting and every rate.

| Rate | Reported | Measured (integer onset) | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | [0.0, 0.0] | 0 | 0.0000 |
| 44100 | 0 | [0.0, 0.0] | 0 | 0.0000 |
| 22050 | 0 | [0.0, 0.0] | 0 | 0.0000 |

Dossier latency budget: 0 samples / 0.000 ms. **Met: yes.**

**The sub-sample reading, and why it is not the latency.** The same renders
read sub-sample give **+1.333 samples at 48 kHz, +1.220 at 44.1 kHz and
+0.708 at 22.05 kHz** through an 8 kHz corner. That is a minimum-phase
filter's group delay — a real property of the class, and not the processing
latency `latency_samples` declares. The kit says so in `click()`'s own
docstring and the row here wants the integer reading.

**Every latency-adding option:** there are none.

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| — | — | — | — | The docstring states there is no lookahead, partition or window anywhere in the class, so there is no option to default off |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
**CLICK red at all three rates**, audio digest unchanged
(`measured [0.0, 0.0] samples against a reported 256`).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 … 20 000 Hz, log; `_hz()` clamps at 0.49·F_s | the cutoff knob |
| 1 | Resonance | UNIPOLAR | Q 0.5 … 16, log | the resonance/emphasis knob |
| 2 | Slope | TOGGLE | 12 dB/oct (0) / 24 dB/oct (127) | a console filter's slope switch |
| 3 | Mix | UNIPOLAR | 0 … 1; 0 is a byte-exact wire | a dry/wet blend |
| 4 | Trim | BIPOLAR | −12 … +12 dB; under 0.2 dB the section is a wire | the make-up a resonant peak needs |

Five, against a limit of sixteen.

| Patch | Name | What it is for | Grid |
|---|---|---|---|
| 0 | Open | the constructor's defaults on the grid: 20 kHz, Q 0.71, 12 dB/oct — the filter out of the way | `(127, 13, 0, 127, 64)` |
| 1 | Soft Roll | 6 044 Hz, Q 0.71, 12 dB/oct — take the top off without hearing a corner | `(105, 13, 0, 127, 64)` |
| 2 | Steep Cut | 2 980 Hz, Q 0.71, 24 dB/oct — the top actually gone | `(92, 13, 127, 127, 64)` |
| 3 | Resonant Peak | 1 182 Hz, Q 5.99, 12 dB/oct, −5.95 dB — a whistle at the corner, trimmed back | `(75, 91, 0, 127, 32)` |
| 4 | Squelch | 495 Hz, Q 11.85, 24 dB/oct, −8.98 dB — the filter as an instrument | `(59, 116, 127, 127, 16)` |
| 5 | Sub Only | 120 Hz, Q 0.71, 24 dB/oct — everything but the bottom | `(33, 13, 127, 127, 64)` |

Five named patches beyond patch 0, and every one of them renders a different
corner (`tests/test_cpython_effects_lowpass.py::test_every_patch_is_reachable_and_moves_the_filter`
asserts six distinct corners, so a table whose entries all sounded the same
would fail).

`patch_index` is 0 on a fresh instance, `None` after any macro move and the
patch's index after `program_change`: `tests/test_audio_component_api.py`
holds every class in `ALL` to that, and this class is in `ALL`.

**`capabilities` = `()`.** The dossier's one-line reason: *nothing in a
low-pass is measured in beats — its two controls are hertz and a
dimensionless Q — so the class never reads `self._transport()`* (§8 D7).
Measured rather than asserted: the same probe rendered under transports at
90 and 160 BPM gives `86eb85a1` and `86eb85a1` at 48 kHz, `89b7ecfd` twice at
44.1 kHz and `692a10ed` twice at 22.05 kHz — identical, which is what an
empty `capabilities` claims. A subclass that declares `tempo_sync` over the
same two digests goes **RED** (§2).

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Biquad` `LOW_PASS` ×2 | `audiobiquad` | Tier 1's *silence in, silence out; the tail reaches exact zero* | `synthio.Biquad`'s recursion keeps its output memory in Q12 sample units and rounds to nearest with no dither and no leak, so it lands on states that reproduce themselves: a `LowPass` at 100 Hz holds +1 LSB and one at 40 Hz Q 8 holds −4 LSB, for ever (audioif#23; dossier A3 reproduces it on nine configurations and A14 re-measures it). Those are exactly the corners this class exists for |
| `Biquad` `HIGH_SHELF` @ 5 Hz | `audiobiquad` | the Trim macro | same tail argument, plus: it is the only route on the palette to gain **above** unity — `audiomixer.MixerVoice.level` clamps to 0…1 and `audiomath.Multiply` only attenuates (dossier §8 D2) |

Test:

```
$ PYTHONPATH=<worktree>/lib .venv/bin/python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.003s

OK
```

The class appears in that battery automatically — it walks
`audioeffects.ALL` and `rebuilt.known()` — so a tier claim here that the
class's `TIER` does not match is a test failure, not a wrong sentence.

**What that test does not prove**, and every pack must repeat it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class has
*not* been shown rendering on a stock CircuitPython build of the ported C.
That is a gap in the method, not in this class — and for this class the
consequence runs the other way: it is audioif tier, so a stock board cannot
construct it at all, by design and by the dossier's §8 D1.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed or unmeasured. **Five
      demonstrated, none disconfirmed, none unmeasured.**
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on the patched CircuitPython build where
      its nodes exist; every Tier 2 measurement names the rate it ran at.
      **With two `n/a` classes recorded in §2 and repeated in §11: the
      numpy-only analyses run on CPython alone and reach the other two by
      byte-identity, and `deinit()` cannot be read back on the native builds
      because no audioif-own node has a `deinit()` there.**
- [x] Every demonstrated Tier 2 trait has a measurement, and that measurement
      was shown red on a planted fault of the same kind.
- [x] Every demonstrated trait survived a refutation attempt, recorded with
      the argument and the answer — **by this session, not an independent
      one. §11.**
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material. **The P4 and S3 digests are not taken.**
- [ ] Tier 3 cost is measured on the P4 and the S3. **Not run — §4, §11.**
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz (and 22.05 kHz); the budget is met; there is no
      latency-adding option to default off, and the docstring says so.
- [x] The class declares a macro surface (five, at most sixteen) and five
      named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass.
- [x] The README catalogue row and the docstring describe the standout, the
      portability tier and the cost, in a musician's terms.
- [ ] The class's code, this file and the CHANGELOG line landed in **one**
      commit. **They did not**, and the reason is in §0: the dossier had to
      be frozen before the code, so this is three commits, named there.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=<worktree>/lib .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=<worktree>/lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 248 tests in 21.013s

OK (skipped=1)

$ PYTHONPATH=<worktree>/lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=<worktree>/lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=<worktree>/lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.003s

OK

$ PYTHONPATH=<worktree>/lib .venv/bin/python -m unittest tests.test_cpython_effects_lowpass
Ran 21 tests in 0.825s

OK

$ PYTHONPATH=<worktree>/lib .venv/bin/python tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=<worktree>/lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=<worktree>/lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ ... tools/measure_effect_cost.py --subject LowPass --port <COMn>
NOT RUN - no board attached in this session (§4, §11)
```

**T3 at 24 dB/oct, both runs**, because the first is the reason the second
exists:

```
  # stopband probes at -20 dBFS - the int16 floor, not the filter
  slope 24  f0    31.5  |H(4fa)|  -48.132  fitted -22.231 dB/oct
  slope 24  f0  2000.0  |H(4fa)|  -48.141  fitted -22.810 dB/oct

  # the same points at -6 dBFS
  slope 24  f0    31.5  |H(4fa)|  -48.164  |H(8fa)|  -72.135  fitted -23.972 dB/oct
  slope 24  f0  2000.0  |H(4fa)|  -48.165  |H(8fa)|  -72.161  fitted -23.995 dB/oct
```

**The `deinit` survey** behind §2's footnote 2, run on each interpreter
(`*` = the class has no `deinit`):

```
cpython
  audiobiquad    AllPass Biquad
  audioladder    Ladder
  audioshaper    Waveshaper
  audioverb      Tank
  audiomath      Multiply SubOctave
  audioecho      FeedbackDelay
  audiodynamics  Dynamics
micropython / circuitpython
  audiobiquad    AllPass* Biquad*
  audioladder    Ladder*
  audioshaper    Waveshaper*
  audioverb      Tank*
  audiomath      Multiply* SubOctave*
  audioecho      FeedbackDelay*
  audiodynamics  Dynamics*
  audiofilters   Distortion Filter Phaser        (ported - these do have it)
  audiomixer     Mixer                           (ported - has it)
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

1. **No surface at all** — `eq.py:120`, `MACRO_LABELS = ()`. Now five macros
   and six patches (§6).
2. **`q` frozen at construction** — `eq.py:104` passed a bare float while
   `frequency` got a `synthio.Math` block. Now every setting is a live slot
   on `audiobiquad`, and Resonance moves the running filter.
3. **`mix` accepted and then hidden** — taken at `eq.py:101`, forwarded at
   `:105`, unreachable afterwards. Now macro 3, and its zero is a byte-exact
   wire on all three interpreters (§2, §3).
4. **`set_frequency` off-contract, and it raised** — `eq.py:110-111` called
   `_core.check_hz`, which raises at or above Nyquist (`_core.py:471-474`)
   instead of clamping. The method is gone; `self._hz()` clamps and never
   refuses (§2, RATE row). `AirSpace` was the one caller and now drives the
   Frequency macro.
5. **No tail declared** — `TAIL_SAMPLES = None` from the base. Now 204 800,
   from a measurement at the worst setting the span offers (dossier A15).
6. **Held DC at low corners** — audioif#23. Now exact zero at every
   configuration measured, on all three interpreters (§2).
7. **`reset()` reached one node** — `_core.py:366-374` reset `self._output`
   only, which recursed into the borrowed source. Now the enumerated walk,
   and the borrowed source is never named; the STATE run shows the source
   still rendering afterwards, and a section left out of the walk is a
   planted fault that goes red (§2).

---

## 11. What is not done

- **No board leg.** Neither the ESP32-P4 nor the ESP32-S3 was run: §4 is
  empty and the Tier 3 budget is unverified. It needs a board on a serial
  port and `tools/measure_effect_cost.py --subject LowPass --port <COMn>`.
- **The refutation pass was not independent.** §1's refutations were run by
  the session that built the class. The gate asks for an independent one.
- **`deinit()` is unverifiable on the two native builds**, because **no
  audioif-own node exposes `deinit()` there** — surveyed, §9. This is not
  specific to `LowPass`: it reaches every audioif-tier class in Phase 2 and
  every one after it. Worth an audioif issue; none filed by this session.
- **Four Tier 1 rows are CPython-only analyses** (LEVEL, CLICK, the
  allocation and `tempo_sync` legs of STATE). They reach the other two
  interpreters by byte-identity of the renders, which is an inference and is
  labelled as one in §2.
- **`effect_measurements.enumerate_nodes()` cannot see a `_component`
  class's nodes**, because they are private. Worked around here by passing
  `nodes=` from the class's own `_own()` list; the kit would otherwise report
  a missing `deinit` as green. Worth a fix in the kit; none made by this
  session.
- **The dossier is over its length band.** §§1–8 measure 13.5 KB against the
  vision's 8–12 KB. Recorded in the dossier's App. R with where the excess
  is.
- **No issue was filed** for any of the above.
