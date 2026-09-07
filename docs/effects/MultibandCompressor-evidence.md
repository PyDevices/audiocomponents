# Evidence Pack — `MultibandCompressor` (no standout; a crossover-split topology)

Written at Station C from the runs named in each section. The dossier is
[`MultibandCompressor.md`](MultibandCompressor.md); its Tier 2 rows are M1–M5
and every one of them has a section here.

**Three rules this file is written under.** Numbers come from runs, each with
its command. A measurement with no planted fault cannot be cited. And §11 says
what is not done, in its own section — including the whole of Tier 3.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `MultibandCompressor` |
| Dossier | [`MultibandCompressor.md`](MultibandCompressor.md), traits frozen 2026-09-06 by the seed; Station A pass at `e84353b` |
| Module | `lib/audioeffects/rebuilt/multibandcompressor.py` |
| Base | `_component.Component` |
| Family / phase | Dynamics, roadmap Phase 2 |
| Standout | none — a topology (RaneNote 155 Fig. 7) and an alignment (Linkwitz-Riley, RaneNote 160), not a box |
| Grade | **design** |
| Portability tier | **audioif** (`REQUIRES = ("audiobiquad", "audiodynamics", "audioroute")`) |
| Landed in commit | `7c7b183` — the class, its tests, the three probes, the README row and the CHANGELOG entry; this file in the commit after it |
| audioif pin | `2f6cbc3`. The six files this class runs on — `shared/audioif_filter_f32.c`, `shared/audioif_dynamics.c`, `shared/audioif_splitter.c`, `audiobiquad/Biquad.c`, `audioroute/Splitter.c`, `audiomixer/MixerVoice.c` — are **byte-identical between the pin and the checkout** (`git show 2f6cbc3:<file> \| sha256sum` against the working tree, six of six) |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3; `cmods/bin/micropython` 1.28.0; `cmods/bin/circuitpython-effects` 10.2.1 |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** **yes.** M1–M5 are the
seed's rows of 2026-09-06 and this rebuild did not touch them. The Station A
commit `e84353b` restructured §§1–8, settled all five of §8's open questions
and corrected three palette claims that were a day stale — the crossover node,
the detector and the all-pass — from runs committed as
`tools/phase2_probes/multiband_palette.py`. It added, removed, retired and
loosened no trait; App. T holds each row as the seed wrote it, and the gate
can read the two side by side.

---

## 1. Traits

Command for every row below:

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_traits.py
```

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| M1 | **Unity sum**: every band at unity, flat within ±0.25 dB from 30 Hz to min(20 kHz, 0.45 fs) — at two bands for every setting, at three for every setting 8:1 or wider | **demonstrated** | SUM, 57 tones at 1/6 octave, 48 kHz, cpython. Three bands: **+0.005/−0.009** at 40/8000, **+0.001/−0.117** at 200/2000, **+0.001/−0.168** at the closest legal pair (800 → clamped to 800/6400). Two bands: **+0.001/−0.002**, **+0.001/−0.001**, **+0.006/−0.009** at 200, 800 and 40 Hz | `NoRatioClamp` — the 8:1 push-up *and* the 800 Hz floor on Crossover High's span both removed — at 200/400 (2:1) → **RED, −7.780 dB**; at 200/800 (4:1) → **RED, −0.987 dB**. **Control:** the same faulted build at 200/1600 (8:1) is **green at −0.189 dB**, so the fault is the setting and not a broken class | *"The clamp makes the trait unfalsifiable — the class simply refuses the settings that would fail it."* It does not refuse: it clamps and reports both numbers (`macro(1)` the request, `crossover_high_hz` what landed), and the fault build reaches 2:1 and fails. The trait is stated against the clamp because A-M6 derived the ratio dependence before the surface existed. |
| M2 | **LR4 crossovers**: at 200/2000 each band is −6 dB at its corner on a 24 ± 2 dB/octave skirt, and the halves are in phase there — the sum at the corner is unity, not a null | **demonstrated** | XOVER, soloed band against the dry tone, 48 kHz, cpython. Low band at 200 Hz **−6.06 dB**, skirt **23.7 dB/octave** over 400–800 Hz; high band at 2000 Hz **−6.05 dB**, skirt **23.7 dB/octave** over 500–1000 Hz. Sum at both corners **−0.088 dB** | `LinkwitzRiley2` — one Butterworth section a side, which RaneNote 160 says needs a polarity inversion nothing here performs → **RED: corner −3.03 / −3.02 dB, skirt 11.8 dB/octave, and the sum at both corners collapses to −20.93 dB**, which is the null S3 predicts | *"−6.06 could be a −6 dB target hit by tuning rather than by the alignment."* Nothing is tuned: both sections are Q = 0.7071 at the same frequency, which is the definition, and the fault build differs from it by exactly one section and lands on −3.03 — the Butterworth number. |
| M3 | **Band isolation**: 12 dB on one band moves that band's passband by 12 dB within 0.5 dB, evenly (tilt ≤ 0.5 dB), and leaves every other band within 0.5 dB | **depth demonstrated · isolation demonstrated · evenness DISCONFIRMED for the low band** | ISO, per band, **soloed**, 48 kHz, cpython. Depth: **−12.18 / −11.76 / −11.91 dB** mean for low / mid / high, all inside ±0.5. Isolation: **0.00 dB** on every idle band, all three rows. Evenness: **0.27 dB** (mid) and **0.37 dB** (high) — and **0.73 dB across 30–100 Hz on the low band**, over the 0.5 dB bar | `SharedDetector` — one threshold and ratio on every band's gain computer, a full-band compressor wearing a crossover → **RED on both clauses, on different rows**: driving the low band pulls the other two down **12.01 dB**, and driving the mid or high band moves nothing at all (**+0.00 dB** where 12 were asked) | *"The low band's tilt is the measurement's, not the class's — read it off the sum and it would be worse."* It would: on the sum the low band 12 dB down reads **−10.4 dB at 100 Hz**, because the mid band's skirt is only 24.6 dB down there. The per-band read removes that, and 0.73 dB survives it. The two halves of what survives are measured separately in §1a. |
| M4 | **Zero latency**: the impulse leaves in the frame it entered, at every setting | **demonstrated** | CLICK, integer onset (`subsample=False`, tolerance 0), impulse at frame 64. **Reported 0, measured 0** in all six configurations — 3 bands at 200/2000 and at 40/8000, and 2 bands at 200 — at **48 kHz and 44.1 kHz**, cpython | `LookaheadLatency` — 128 samples of `audiodynamics` lookahead, which this class deliberately does not expose, applied before the Mixer's voices take their first chunk and still reported as 0 → **RED at all six, measured [128.0, 128.0] against a reported 0** | *"An all-pass network has group delay, so 'zero latency' is a claim about the reading, not the class."* It is a claim about onset, and the row says which reading it wants: the integer one. The sub-sample reading of a minimum-phase filter is group delay and not processing latency (`effect_measurements.click` says so in its own docstring); the fault moves the integer reading by 128 and the trait's own words are "in the frame it entered". |
| M5 | **The sum survives its source**: the same probe at 256, 8192, 16384, 20000 and 32768-frame `get_buffer` calls renders byte-identically and non-silently | **demonstrated** | LONG, 48 kHz, cpython. A 220 Hz tone at every block: **`7d18736d` five times over**. Burst-then-silence material: **5094 non-zero samples at every block** | `NoGuard` — the Splitter fed straight off the source, which is the shipped class's topology (`dynamics.py:239`) → **RED**: `7d18736d, 7d18736d, 1372899d, 1e78366d, ef869b3d`, three different renders; and on burst material **5094, 5094, 0, 0, 0** — exact silence at three of the five | *"A guard node is a workaround for a node defect and should have been an audioif ask."* It was, and the palette refuted it: the defect fires only when the Splitter's immediate source hands back more than 8192 frames, and every processing node on the palette hands back its own block. The ask is a defect report on audioif; the class needs one node it was going to build anyway. |

- **demonstrated** = a measurement, that measurement red on a planted fault of
  the same kind, and a surviving refutation. M1, M2, M4 and M5 have all three,
  and so do two of M3's three clauses.
- **disconfirmed**: **one clause of M3**, evenness, on the low band only — see
  §1a. It is in the class docstring and in the README row, not only here.
- **unmeasured**: none at Tier 2. Tier 3 is entirely unmeasured — §4 and §11.

**Tally: 4 traits demonstrated, 1 disconfirmed in one of its three clauses,
0 unmeasured at Tier 2; 0 of 3 Tier 3 rows measured.**

**Refutation pass.** Run by the class builder against its own build,
2026-09-07, immediately after each measurement went green; the arguments are
in the last column. What it could not break: M5, because the faulted build
reproduces the dossier's A-M5 numbers — exact zeros on burst material at
16384 frames and up — and the guarded build reproduces none of them. What it
**did** break, twice, and what changed as a result: the first M1 fault could
not reach 2:1 at all (Crossover High's span floors at 800 Hz, so a request for
400 landed on 800 and the "2:1" row was a second copy of the 4:1 row, at
−0.987 dB); the fault now removes both halves of the clamp. And the first M4
fault set its lookahead after the Mixer's voices had taken their first chunk,
so it read 64 samples where 128 were asked for; it now lands with the last
macro, before the voices play, and reads exactly 128.

### 1a. Where the low band's tilt comes from

Two effects, pulling the same way, both measured in `_m3_causes`:

| | 30 Hz | 45 Hz | 63 Hz | 80 Hz | 100 Hz | tilt |
|---|---|---|---|---|---|---|
| `rms_ms` at the node default (10 ms) | −12.51 | −12.35 | −12.20 | −12.05 | −11.78 | **0.73 dB** |
| `rms_ms` 30 ms | −12.18 | −12.10 | −12.02 | −11.90 | −11.66 | **0.52 dB** |

1. **The band's own skirt.** An octave inside its LR4 corner the low band is
   0.53 dB down, so a fixed threshold buys `(1 − 1/ratio) × 0.53` = **0.40 dB**
   less reduction at 100 Hz than at 30. That is arithmetic and no setting
   removes it.
2. **The detector's window.** Below about 50 Hz the RMS detector's 10 ms window
   is shorter than one period of the tone, its envelope ripples at twice the
   tone and the gain follows it. Lengthening the window to 30 ms takes the
   30 Hz reading from −12.51 to −12.18 dB — **0.33 dB of the rest** — and is
   the control that separates this cause from the first.

**What the class does instead: nothing, and it says so.** A per-band `rms_ms`
would need either a fifteenth macro or a rule the dossier does not have, and
30 ms only takes the tilt to 0.52 dB — still over the bar. The class docstring
states the number and what a musician hears: the low band compresses a couple
of tenths deeper than the dial at the bottom of its range and a couple of
tenths shallower at the top.

---

## 2. Tier 1 invariants

The block runs on **all three interpreters**, at all three rates, at both
channel counts, in `tools/phase2_probes/multiband_tier1.py`. Every check is
integer work — a byte compare, a last-non-zero index, an onset index, a peak
or a read of the live surface — so the MicroPython and CircuitPython columns
are runs and not "the same class, so presumably the same answer".

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_tier1.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      -X heapsize=512M tools/phase2_probes/multiband_tier1.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=512M tools/phase2_probes/multiband_tier1.py
```

Last line of each: **`0 failing invariants`** — cpython, micropython and
circuitpython-effects alike.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `Mix` at zero is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the summed path | LEVEL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node silent and stateless, and the source untouched | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| …**and the class renders again afterwards** | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `deinit()` releases every node and leaves the source rendering | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `capabilities` names exactly the optional behaviours honoured | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Pulling `output` allocates nothing | STATE | n/a | pass | pass | n/a | pass | pass | n/a | pass | pass |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass | pass | pass | pass | pass | pass | pass | pass | pass |

**The "renders again" row is not decoration, and it is the one this class
needed.** `audiomixer.Mixer.reset_buffer` **stops** every voice on upstream
CircuitPython's node and **rewinds** them on audioif's, and a stopped voice
never plays again (audioif `docs/upstream-diff.md`, "Resetting a Mixer
silenced it, permanently"). Measured on `cmods/bin/circuitpython-effects`:
after `audiocore.reset_buffer(mixer)` the bare node reads `voice[0].playing`
**False** and renders 0 LSB for ever, where the same call on the other two
builds leaves it playing at 12000. So "silent after reset" is *both* what a
clean reset looks like and what a dead class looks like — the
absence-reads-as-agreement shape — and a row that only checks the silence
cannot tell them apart. The class's `_reset_mixer` clears the Mixer and then
hands its voices back their sources; the row above proves the sound returns,
against the probe's **second burst**, because the invariant forbids rewinding
the borrowed source to arrange it.

**The allocation row's `n/a` on CPython** is `gc.mem_alloc()`, a MicroPython
read. Where it exists the figure is a difference against a control that is
pulled the same number of times — a one-node `Filter` at the Mixer's own
128-frame block, not the bare `RawSample`, which hands back its whole array in
one call and would make the class look free. Stereo: **1158496 against
1158496, +0 bytes**, on a render whose peak is 7713 LSB.

**Mono.** The dossier's §4 says the split and the detectors are per band, not
per channel, so a mono source is processed identically. Measured: every row
above runs at `channel_count` 1 as well as 2, and WIRE at mono is **0 of
14400 samples differing** at 48 kHz on all three interpreters.

**Planted faults for this block**, each with its clean control:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| TAIL | `PortedBiquads` — the crossover on `audiofilters.Filter` over a `synthio.Biquad` cascade, which is the topology the dossier's §4 mapped | green, residual **0 LSB** | **RED**, residual > 0 and no last non-zero sample at all: the state never returns to zero (`tests/…::TierOne::test_the_ported_biquads_hold_dc_for_ever`) |
| STATE (reset) | `MixerResetTailFirst` — the Mixer put back at the end of the walk, where owning it in build order would have put it | green, **0 LSB** after reset | **RED**, the crossover's ring-down still in the voice buffer |
| STATE (renders again) | `ClearOnly` — the Mixer cleared and its voices left stopped, which is the ported node's own behaviour | green, the second burst comes through | **RED**, silence from the reset on |
| WIRE / head of render | `PlayBeforeMacros` — the voices played before `_init_macros`, so the first 256 frames go through biquads still at 1 kHz | green | **RED**, a different digest for the first 256 frames |
| CLICK | `latency_samples` reported 256 short, DSP untouched | green | **RED** at both rates |
| M5 / LONG | `NoGuard` — the Splitter fed straight off the source | green | **RED**, three different renders and exact silence on burst material |

`reset()` and `deinit()` walk the node list `_component` requires the class to
enumerate with `self._own()`. **Nodes enumerated by this class, in build
order** (18 at three bands): the `Mixer` **first, deliberately, so the reverse
walk resets it last**; then the guard `Filter`; the `Splitter` (owned
`reset=False, deinit=False` — it is a container with neither method on any
build in this workspace); its four `SplitterTap`s; two `audiobiquad.Biquad`s
and a `Dynamics` for the low band; four and a `Dynamics` for the mid; two and
a `Dynamics` for the high. The borrowed source is not among them, and the run
asserts it.

**Verbatim, CPython, 48 kHz stereo:**

```
MultibandCompressor Tier 1 invariants - cpython
========================================================================

48000 Hz, 2 channels
   WIRE mix 0, 3 bands                pass  0 of 28800 samples differ, worst 0 LSB
   WIRE mix 0, 2 bands                pass  0 of 28800 samples differ, worst 0 LSB
   LEVEL 1 kHz, 3 bands at unity      pass  -0.089 dB against the source
   LEVEL 1 kHz, 2 bands at unity      pass  +0.000 dB against the source
   TAIL crossover   200 Hz            pass  tail 710 samples (declared 864), residual 0 LSB
   TAIL crossover    40 Hz            pass  tail 3086 samples (declared 4321), residual 0 LSB
   TAIL dc_step, crossover 40 Hz      pass  0 LSB held in the last quarter second after the step was removed
   CLICK impulse at frame 64          pass  reported 0, measured 0
   CLICK impulse at frame 64          pass  reported 0, measured 0
   STATE reset clears every node      pass  primed 25845 LSB, after reset 0 LSB
   STATE it renders again after reset pass  26123 LSB on the probe's second burst after reset()
   STATE the source is not owned      pass  18 nodes owned, none of them the source
   STATE deinit closes the surface    pass  output raises after deinit, and deinit twice is safe
   STATE the source still renders     pass  26000 LSB off the borrowed source after the class over it was deinited
   CAPS () and no transport read      pass  capabilities (), transport called 0 times
   RATE both corners at maximum       pass  low 800.0 Hz, high 8000.0 Hz, Nyquist margin 23520.0 Hz
   RATE both corners at maximum       pass  low 800.0 Hz, high n/a, Nyquist margin 23520.0 Hz
   ALLOC pulling output               pass  n/a  gc.mem_alloc() is a MicroPython read; CPython's leg is tracemalloc, in the kit's STATE
```

The MicroPython run's 48 kHz stereo block is **the same eighteen rows with the
same numbers**, plus `ALLOC pulling output   pass  1158496 against a one-node
control's 1158496, +0 bytes, on a render whose peak is 7713 LSB`.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, per probe, per rate, at the source block size the
kit's own adapter delivers. `sum(data)` is never the comparison.

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_digest.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      -X heapsize=512M tools/phase2_probes/multiband_digest.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=512M tools/phase2_probes/multiband_digest.py
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 256 | `708f7289` | `708f7289` | `708f7289` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | `2552bc2d` | `2552bc2d` | `2552bc2d` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | `0e4af4bd` | `0e4af4bd` | `0e4af4bd` | *(board run)* | *(board run)* |
| `chord` | 44100 | 256 | `69e6f029` | `69e6f029` | `69e6f029` | *(board run)* | *(board run)* |

**Desktop agreement: yes**, and all three, not two — CPython, desktop
MicroPython **and** the patched CircuitPython render identical bytes on every
probe. The source route differs (`WaveFile` on the first two,
`RawSample` on CircuitPython, which refuses every stream the renderer can
open) and the bytes do not.

**Why the digests are not `render_effect.py`'s, and it is not the class.**
`render_effect.py:717` calls `audiocore.reset_buffer(effect.output)` before it
renders. This class's `output` is a `Mixer`, and on `circuitpython-effects`
that one call stops every voice for ever (§2), so the renderer produces
**exact silence** there — `chord` at 48 kHz reads `sum 0 SILENT` — while
`Compressor` and `Limiter`, whose outputs are not Mixers, render normally on
the same interpreter and the same probe. `multiband_digest.py` is
`render_effect.py`'s own probe resolution, source route, block adapter and
FNV-1a, imported rather than copied, with that one line absent. The class's
`reset()` is unaffected: it re-plays its voices for exactly this reason. The
renderer's incompatibility with any Mixer-output class on the ported node is
in §11.

**Block-size ladder** (M5's own measurement, in the traits run): byte-identical
at **256, 8192, 16384, 20000 and 32768**-frame sources — `7d18736d` five times.

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
target `effect:MultibandCompressor`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: **ESP32-P4 25 %** of one stereo block's real-time deadline,
**ESP32-S3 45 %**. Lean build expected: **yes** — `bands=2`.

| Board | Build | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | `bands=3`, patch 0 | construction defaults, `audioeffects.create("MultibandCompressor", …)` | 374.4 | 2.671 (2.361 marginal) | 2.00 | 55 KB | **no** — 44.3 % marginal, 50.1 % total, against 25 % |
| S3 | `bands=3`, patch 0 | construction defaults, `audioeffects.create("MultibandCompressor", …)` | 203.7 | 4.910 (4.458 marginal) | 1.09 | 55 KB | **no** — 83.6 % marginal, 92.1 % total, against 45 % |
| S3 | `bands=2`, patch 0 | — | — | — | — | — | *(not run — the runner passes no construction options)* |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:MultibandCompressor`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 25 %, S3 45 % (`bands=3`).

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`3239279a24c17a93` on the ESP32-P4 and `3239279a24c17a93` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is `2a0820b67a5028ea` — it **differs**.

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

**Owed: a `" - lean"` patch.** At 83.6 % of the deadline the class is over
its ESP32-S3 budget of 45 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** the `bands=2` lean build. `measure_effect_cost.py` builds through `audioeffects.create()` and passes no construction options, so the valve is still unmeasured.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


What is known without a board: the three-band build is **18 owned nodes**
(guard, Splitter, four taps, eight biquads, three detectors, Mixer) against
the two-band build's **13** (guard, Splitter, three taps, four biquads, two
detectors, Mixer) — a count from the run, not an estimate: `STATE the source
is not owned  pass  18 nodes owned`. That is a node count and **not** a cost
figure, and it may not be read as one.

**The lean build is a build, not a patch.** `MultibandCompressor(source,
bands=2)` is the escape valve; a `" - lean"` patch cannot be one, because
`program_change` moves macro positions and cannot drop a node (dossier §8.5).
If the board run finds the three-band build over budget, the valve exists and
is measured with the same runner.

---

## 5. Latency

Reported `latency_samples` = **0**, at every setting, for the life of an
instance. Measured click delay against the dry path, integer onset:

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0 (both channels, all six configurations) | 0 | 0.000 |
| 44100 | 0 | 0 (both channels, all six configurations) | 0 | 0.000 |

Dossier latency budget: **0 samples**. Met: **yes**.

**Every latency-adding option, each defaulting off or to its shortest:**
there are none. `audiodynamics` offers a lookahead of up to 50 ms
(`AUDIOIF_DYNAMICS_MAX_LOOKAHEAD_MS`, `audioif_dynamics.h:105`) and this class does not expose it; no linear-phase
or partitioned crossover is offered either. Both refusals are in the class
docstring, with the reason (a multiband's job is the balance between bands,
and the ceiling belongs to `Limiter`, which is built on that lookahead and
reports it).

Planted fault: `LookaheadLatency` — 128 samples of that lookahead turned on,
applied before the Mixer's voices take their first chunk, with the DSP
otherwise untouched and the report still 0 → **CLICK red at both rates,
measured [128.0, 128.0]**.

`tail_samples` is not a constant: it is the lower crossover's ring-down at the
running rate, `int(3.6 × fs / f_low) + 1`. Measured against it — declared must
never be short — 200 Hz at 48 kHz: **tail 710, declared 864**; 40 Hz at
48 kHz: **3086 against 4321**; 40 Hz at 22.05 kHz: **1420 against 1985**.

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Crossover Low | UNIPOLAR | 40 … 800 Hz, log | the lower LR corner; at two bands, the only one |
| 1 | Crossover High | UNIPOLAR | 800 Hz … 8 kHz, log | the upper LR corner, clamped to ≥ 8 × macro 0 |
| 2–4 | Low / Mid / High Threshold | UNIPOLAR | −60 … 0 dB | per-band threshold |
| 5–7 | Low / Mid / High Ratio | UNIPOLAR | 1 … 20, log | per-band ratio |
| 8–10 | Low / Mid / High Gain | BIPOLAR | −12 … +12 dB | per-band make-up (`makeup_db`) |
| 11 | Attack | UNIPOLAR | 0.1 … 100 ms, log | one attack, all bands |
| 12 | Release | UNIPOLAR | 5 … 1000 ms, log | one release, all bands |
| 13 | Mix | UNIPOLAR | 0 … 100 % | parallel compression; 0 % is the Tier 1 bypass |

Fourteen, inside the sixteen-macro wall. The seed proposed fifteen, with
`Bands` as macro 0; §8.5 settles it as a constructor option because the Mixer
pulls a voice at level 0 exactly as hard as one at unity, so a muted band is
not a cheaper build and the knob would have lied about its cost. What that
costs is recorded in the dossier: the band count is not automatable from a
host's macro lane. `macro_is_live(index)` reports which macros do anything at
each band count — at two bands, Crossover High and the three Mid macros do
not, and the test asserts exactly that list.

| Patch | Name | What it is for |
|---|---|---|
| 0 | Master Glue | the constructor's defaults on the 0-127 grid — 200/2000 Hz, −18 dB, 3:1, 10 ms / 150 ms, mix 100 % |
| 1 | Bass Control | the low band only: 120 Hz split, −24 dB at 4:1, the other two idle at ratio 1 |
| 2 | Vocal Bus | 250/3000 Hz, gentle 2.5:1 across all three, a faster 15 ms attack |
| 3 | De-Boom | 90 Hz split, low threshold down to −30 dB at 6:1, the rest idle |
| 4 | Loudness | all three at 2:1 from −24 dB with +3 / +1.5 / +3 dB of make-up, mix 60 % |

Patch 0 is held to the constructor's defaults **by span, not by a hand-copied
list**: `test_patch_zero_is_the_constructor_defaults_on_the_grid` recomputes
`macro_of(span, default)` for all fourteen. `patch_index` is 0 on a fresh
instance, `None` after any macro move, and the patch's index after
`program_change` — the contract tests over `audioeffects.ALL` cover that for
every class.

**`capabilities` = `()`.** The class never reads `self._transport()`; the
dossier's one-line reason is "no band's behaviour refers to tempo" (App. I,
D10). The Tier 1 run asserts it with a counting transport: `capabilities (),
transport called 0 times`, on all three interpreters at all three rates.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad", "audiodynamics",
"audioroute")`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Biquad` ×8 | `audiobiquad` | Tier 1's tail; M1; M2 | the ported `synthio.Biquad` cascade keeps Q12 state and rounds to nearest, so it has fixed points: 2 LSB of DC held for ever at a 100 Hz corner, 8 LSB at 40 Hz (App. P, P1) |
| `Dynamics` ×3 | `audiodynamics` | M3 | not a CircuitPython port at all (`upstream-diff.md:661`); `detector="rms"` is what S2's Fig. 7 draws |
| `Splitter` + 4 taps | `audioroute` | M1; M5 | the only fan-out on the palette; also not a port |

`audiomixer` and `audiofilters` are ported modules and are **not** in
`REQUIRES` — but the class's behaviour does depend on which copy of
`audiomixer` it meets, and §2 records exactly how.

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.005s

OK
```

The class appears in that battery automatically — it walks `audioeffects.ALL`
and `rebuilt.known()` — so a tier claim here that `TIER` does not match is a
test failure and not a wrong sentence in a document.

**What that test does not prove**, and every pack must repeat it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so no stock-tier class has
been shown rendering on a stock CircuitPython build of the ported C. That is a
gap in the method, not in this class — and for *this* class it is moot in one
direction: an audioif-tier class cannot run on a stock board at all, and the
construction-time `ImportError` is what it does there instead.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured.
- [x] Every Tier 1 invariant is green on CPython, MicroPython and the patched
      CircuitPython at 48 kHz, 44.1 kHz and 22.05 kHz, at one and two
      channels; every Tier 2 measurement names its rate.
- [x] Every demonstrated Tier 2 trait has a measurement shown red on a
      planted fault of the same kind.
- [x] Every demonstrated trait survived an independent refutation attempt,
      recorded with the argument and the answer.
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material — and so does circuitpython-effects.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 44.3 % and S3 83.6 % of the deadline (marginal) against 25 % / 45 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the budget is met; there are no latency-adding options,
      and the docstring says which two were refused and why.
- [x] The class declares fourteen macros and four named patches beyond
      patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass.
- [x] The README catalogue row and the docstring describe the topology, the
      tier, the cost shape and the one disconfirmed clause, in a musician's
      terms.
- [x] The class's code, its tests, the README row and the CHANGELOG entry
      landed in `7c7b183`; this file in the commit after it.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 255 tests in 34.919s

OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.005s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_multiband
Ran 28 tests in 5.110s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
ok   MultibandCompressor      patch 0   peak 15716
ok   MultibandCompressor      patch 1   peak 19350
ok   MultibandCompressor      patch 2   peak 15244
ok   MultibandCompressor      patch 3   peak 20933
ok   MultibandCompressor      patch 4   peak 4005
...
46 classes, 87 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    -X heapsize=512M tests/parity/effects_library_smoke.py
46 classes, 87 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    -X heapsize=512M tests/parity/effects_library_smoke.py
46 classes, 87 patches, 0 failures

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_tier1.py
0 failing invariants
  (and the same last line on cmods/bin/micropython and
   cmods/bin/circuitpython-effects)

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_traits.py
FAILED    low: evenness
1 failing rows
  (the disconfirmed clause of M3, §1a — every other row green, and every
   planted fault red)

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_digest.py
  chord        48000 Hz  block   256    144000 frames  fnv 708f7289  audio  (WaveFile)
  noise_det    48000 Hz  block   256    192000 frames  fnv 2552bc2d  audio  (WaveFile)
  sweep_log    48000 Hz  block   256    192000 frames  fnv 0e4af4bd  audio  (WaveFile)
  chord        44100 Hz  block   256    132300 frames  fnv 69e6f029  audio  (WaveFile)
0 silent renders

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_palette.py
  (App. P of the dossier is written from this run)

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:MultibandCompressor")'
ROW	effect:MultibandCompressor	374.4	2.00	2.671	0.310	2.361	56032	3239279a24c17a93
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:MultibandCompressor")'   # the S3
ROW	effect:MultibandCompressor	203.7	1.09	4.910	0.452	4.458	56032	3239279a24c17a93
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

1. **The Splitter fed straight off the source** (`dynamics.py:239`) — the head
   of any buffer over 8192 frames was dropped, which on head-loaded material
   is the whole signal. *Now: a block-sized guard in front, and M5 is the
   trait that keeps it honest.*
2. **No surface, nothing live** — no macros, one empty patch, everything
   constructor-only, attack and release hardcoded, no make-up, no gain, no
   mix. *Now: fourteen macros, five patches, per-band make-up on `makeup_db`
   and a Mix that bypasses.*
3. **A dead parameter** — `band(tap, biquads)` never used `tap` and three call
   sites passed one. *Now: `_band_chain(band)` uses its argument for the tap
   and for the modes.*
4. **Three block sizes with nothing saying why** — 2048 / 1024 / 256. *Now:
   one, 256 frames, named at `_GUARD_FRAMES` with the reason.*
5. **The docstring's flatness claim was measured nowhere** (`:223-226`). *Now:
   M1, at six settings over fifty-seven tones, red on a planted fault.*

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 44.3 % and S3 83.6 % of the deadline (marginal)
  against 25 % / 45 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **M3's evenness clause is disconfirmed for the low band**, at 0.73 dB of
  tilt across 30–100 Hz against a 0.5 dB bar (§1a). It is measured, its two
  causes are separated by measurement, and it is in the class docstring and
  the README row. What would close it: a per-band `rms_ms`, which is a
  fifteenth macro or a rule the dossier does not have — and 30 ms only reaches
  0.52 dB, so it would not close it on its own.
- **`render_effect.py` cannot render any Mixer-output class on
  `cmods/bin/circuitpython-effects`.** Its `audiocore.reset_buffer(
  effect.output)` at `:716` stops the ported Mixer's voices for ever; this
  class reads `sum 0 SILENT` there while `Compressor` and `Limiter` render
  normally. `multiband_digest.py` works around it for this class only. It
  wants an audiocomponents issue and a one-line fix in the kit — either drop
  the pre-reset or route it through the class's own `reset()` — and **no
  issue has been filed**, because this session cannot push.
- **The Splitter defect is still unfiled on audioif.** The dossier's §5 says
  it should be, with the V-M1/V-M2 reproduction; P4 re-runs the reproduction
  and this session filed nothing.
- **The dossier's §§1–8 run to 13.8 KB**, above the vision's 8–12 KB. The
  restructure moved the standout paragraph, the whole of §7 and the full Tier 2
  rows into appendices; what remains is the settlements of §8 and the frozen
  §6, and nothing further can move without taking gate material with it.
- **No listen.** Nobody has heard this class. Phase 2 is a mechanical gate by
  Brad's direction, so that is by design and not an omission — but it is worth
  writing down that the evidence above is entirely measurement.

---

## Refutation record (2026-09-07)

Written by a refuter who did not build the class, against §1 as it stands.
Every trait marked **demonstrated** was re-run here at settings, rates, block
sizes and tone positions §1 did not use, all inside the trait's own words;
each planted fault was re-checked for firing. One command:

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_refute.py
```

(`tools/phase2_probes/multiband_refute.py` is this pass, added by the
refuter; the class was not touched.) The baseline `multiband_traits.py` run
was reproduced first, last line **`1 failing rows`** — `low: evenness`, as §1
says.

| # | Verdict | The argument, and the numbers behind it |
|---|---|---|
| M1 | **not refuted** | The claim is universal over settings, and §1 measures six. I added four *exactly* 8:1 pairs at 48 kHz (40/320 **−0.029**, 100/800 **−0.190**, 400/3200 **−0.184**, 800/6400 **−0.168** dB), five more two-band splits spanning the whole 40–800 macro (60/120/300/500/650, worst **−0.002**), the same settings at 44.1 kHz (**−0.117 / −0.164 / −0.001**) and at 22.05 kHz, where the grid is 51 tones to 9676 Hz (**−0.112 / −0.094 / −0.002**), and the 200/2000 case on material 20 dB quieter, in case flatness was riding on 16-bit headroom (**−0.117**, unchanged). Nothing crossed ±0.25 dB. What the gate should see anyway: the **margin at the clamp is 0.06 dB** — the worst legal setting found is 100/800 at −0.190 against a 0.25 dB bar, so M1 passes by a quarter of its bar at exactly the ratio §6 permits. |
| M2 | **not refuted** | The row names 200/2000 but no rate. At 44.1 kHz: corners **−6.06 / −6.05 dB**, skirts **23.7 dB/octave**, sum **−0.088 dB** at both. At 22.05 kHz, where bilinear warping is worst: **−6.06 / −6.07**, **23.8 dB/octave**, sum **−0.084 / −0.085**. A pair the class was never measured at, 100/4000 at 48 kHz: **−5.85 / −5.67 dB**, **23.7 / 23.8 dB/octave**, sum **−0.005**. The `LinkwitzRiley2` fault is a real cut — it changes `_band_modes` only — and it lands on the Butterworth number. |
| M3 | **REFUTED — the "demonstrated" half of the row** | §1 marks depth and evenness demonstrated for the mid and high bands and disconfirms evenness for the low band only. Both survive on a **tone window chosen at measurement time**: `BAND_TONES` sits no closer than an octave to either corner, which is 400–1000 Hz out of the mid band's 200–2000 — **1.3 of its 3.3 octaves**. Widen it to 283 and 1414 Hz, still inside the band's own corners and only **1.75 dB** below its own peak, and, **soloed, at the evidence's own 200/2000 setting**: mid band `283:−10.61 400:−11.64 700:−11.89 1000:−11.62 1414:−10.58`, **mean −11.27 dB (depth bar ±0.5 → RED), tilt 1.31 dB (bar 0.5 → RED)**; high band `2828:−10.58 … 16000:−12.01`, tilt **1.42 dB → RED**; low band with 141 Hz added, tilt **1.82 dB**, not 0.73. The shortfall is §1a's cause 1 and nothing else — measured against it tone by tone, `B − C` runs **+0.05 to +0.13 dB** across 200–2000 Hz — so the low band is not a special case: **every band tilts, by its own skirt, and only the window hides it.** (One control the other way: at 40/8000 the mid band is wide enough that a one-octave-inside window still spans 80–4000 Hz, and there the tilt really is **0.37 dB**, green.) |
| M3 (isolation) | **not refuted, but read the bar it is measured against** | I tried to break the isolation clause on the harder read — the **summed output**, no solo, at tones the trait's own "more than half an octave from a crossover" admits — and it held: worst idle-band movement **0.30 dB** (141 Hz while the mid band is driven) and **0.29 dB** (283 Hz while the low band is driven), both inside 0.5. That is a real result and it is stronger than §1's. The soloed read §1 uses, though, is not a small number: it is a **byte-identical compare** — with the low band driven to 12 dB, the soloed mid band at 700 Hz renders `9083457d` and the idle build renders `9083457d`, the same bytes. So "0.00 dB on every idle band" is not evidence of acoustic isolation; it is evidence that a band's chain has no path to another band's macros, and the only defect it can catch is the routing defect `SharedDetector` plants. |
| M4 | **not refuted** | Thirteen configurations §1 did not run, all **reported 0, measured [0.0, 0.0]**: 22.05 kHz at three and at two bands; the closest legal crossover pair (800/6400); two bands at 800; `mix` 0.5 and 0.0; the fastest, deepest dynamics the surface allows (attack 0.1 ms, release 5 ms, ratio 20, threshold −60 on every band); and all five patches. There is no delay line in the graph to find, which is why this row is cheap to hold — but it is not unfalsifiable: `LookaheadLatency` cuts one seam and reads 128. |
| M5 | **not refuted, and it survives a harder run than §1's** | §1's tone ladder digests only the first **8192** frames (`multiband_traits.py:m5`, `render(effect, min(frames, 8192), …)`) and its burst ladder checks a non-zero **count**, not a digest. I removed both limits and added blocks §1 did not use: seven sizes — 256, 8193, 12000, 16384, 32768, 65536, **100000** — over the whole 36000-frame tone give **`0c5b0385` seven times** at three bands and **`53511519`** seven times at two, and the burst material gives **`a82e5695` seven times**, digest-identical rather than merely non-silent. The same seven on the `NoGuard` fault: **seven different digests, and 0 non-zero samples at 65536 and 100000** — the erasure §1 describes, worse than §1 shows it. |

**What the class author must answer (M3 only).**

1. M3's frozen words are "*that* band's passband", and the dossier's Meas.
   column says only "ISO, per band". `BAND_TONES`' one-octave-inside window
   is a reading of "passband" that was settled after the measurement and that
   covers under half of the mid band. Either the window belongs in the trait
   — which is a change to a frozen row, and the gate's business — or the
   verdict changes.
2. On the trait as frozen, **evenness is disconfirmed for all three bands**,
   not one: 1.82 / 1.31 / 1.42 dB of tilt, and **depth is disconfirmed for
   the mid band** at **−11.27 dB**. The class docstring's "The driven band
   itself lands within 0.25 dB of the number asked for in the mid and high
   bands" and the README row are written from the narrow window and would
   need the same correction.
3. §1a's account is right and should be generalised: the tilt is the band's
   own LR4 skirt against a fixed threshold, `B − C` inside ±0.13 dB across
   the whole mid band. It is arithmetic, not a bug — but it is arithmetic
   that applies to **every** band, and the low band is only where the
   evidence's window happened to be narrow enough to expose it.
