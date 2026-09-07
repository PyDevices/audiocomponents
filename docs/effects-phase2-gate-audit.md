# Phase 2 — the class gate, audited

**Auditor:** the Phase 2 gate auditor, 2026-09-07, on `effects/p2-integration`.
**The checklist:** [`../../docs/effects-roadmap.md`](../../docs/effects-roadmap.md),
"The class gate" — ten items, read from each class's
`docs/effects/<Class>-evidence.md` and from the code, every citation checked
with `grep -n`.
**The refutation rulings:** each pack's `Gate audit` block in §1.
**The pattern revision:** [`effects-phase2-pattern-revision.md`](effects-phase2-pattern-revision.md).

**What ran in this session, and its last lines.** Every mechanical claim in
item G8 below is from these, not from the packs:

```
$ .venv/bin/python -m flake8 --exclude=scratch,.refute,.refute-lp,.venv,.git
(no output; exit 0)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.015s
OK

$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 588 tests in 104.493s
OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
46 classes, 163 patches, 0 failures
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tests/parity/effects_library_smoke.py
46 classes, 163 patches, 0 failures
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      tests/parity/effects_library_smoke.py
46 classes, 163 patches, 0 failures
```

The auditor's own re-runs of contested figures are in
`scratch/audit/` (untracked) and quoted in the packs' `Gate audit` blocks:
`Compressor` V3, `Limiter` L1, `BandPass` T1, `CombFilter`'s Glide macro floor.
All four reproduced the refuter's numbers.

---

## 1. The ten items, named

| | Gate item |
|---|---|
| **G1** | The dossier fixed the trait set before the rebuild began, and §1 lists every trait as demonstrated, disconfirmed (with cause) or unmeasured (with why) |
| **G2** | Every Tier 1 invariant green on CPython and MicroPython at 48 / 44.1 / 22.05 kHz, and on the patched CircuitPython where its nodes exist; every Tier 2 measurement names its rate |
| **G3** | Every demonstrated Tier 2 trait has a measurement, shown red on a planted fault of the same kind |
| **G4** | Every demonstrated trait survived an **independent** refutation attempt, recorded |
| **G5** | CPython and desktop MicroPython render identical bytes on the probe material; the board digests match the desktop's or their difference has a cause that is not the class |
| **G6** | Tier 3 cost measured on the P4 and the S3 and inside the dossier budget, or a `" - lean"` patch exists that is |
| **G7** | Reported `latency_samples` = measured click at 48 and 44.1 kHz; budget met; every latency-adding option defaults off and is named in the docstring in ms |
| **G8** | Macro surface (≤ 16) and ≥ 1 named patch beyond patch 0; `validate_api`, `validate_metadata`, the CPython tests, the portability-tier test, the three-interpreter smoke and flake8 all pass |
| **G9** | The README catalogue row and the docstring describe the standout, the portability tier **and the cost**, in a musician's terms |
| **G10** | The class's code, its evidence file and its CHANGELOG line landed in one audiocomponents commit, named in the pack |

**G9 and G10 fail on all sixteen, each for one cause**, so they are recorded
once here rather than sixteen times, and the per-class verdict turns on
G1–G8:

- **G9 — NOT MET, all sixteen.** `lib/audioeffects/README.md`'s catalogue
  columns are *Class · Tier · Macros · Latency · Standout*; there is **no cost
  column** (`sed -n '81,82p' lib/audioeffects/README.md`). The docstrings carry
  the dossier **budget**, not the measured figure — and one is now stale:
  `lib/audioeffects/rebuilt/bandpass.py:27` still reads *"not yet measured on
  either board"* after the board run of `42845a0`. Separately, the traits this
  audit newly moved to *disconfirmed* are not yet visible in the docstrings or
  the catalogue, which the evidence template requires of a disconfirmed trait.
- **G10 — NOT MET, fifteen of sixteen, and the item is wrong.** Every pack
  records the same deviation with the same reason: the dossier freeze has to be
  provably earlier than the code for G1 to mean anything, so the code, the
  evidence and the CHANGELOG cannot land in one commit. Verified on five:
  `26b80aa` (Limiter dossier), `f93ec36` (TransientShaper), `f796f56` before
  `077daf4` (ParametricEQ), `d2f0c0e` before `1cc8166` (HighPass), `8a43ef0`
  before `df1d4b8` (LadderFilter) — all 2026-09-07, all in the stated order.
  The revision proposes the item read *"on one branch whose commits are named
  in §0, with the dossier freeze provably first"*, which is what all sixteen
  did.

---

## 2. The matrix

`Y` = met · `N` = not met · `Y*` = met with a deviation recorded in the pack,
cause not the class.

| Class | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 | G10 | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Compressor` | Y | **N** | Y* | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `Limiter` | Y | Y* | **N** | Y | **N** | **N** | Y | Y | N | N | **PARKED** |
| `Expander` | Y | Y* | Y* | Y | Y | **N** | Y | Y | N | N | **PARKED** |
| `NoiseGate` | Y | Y* | Y* | Y | Y | Y | Y | Y | N | N | **THROUGH** |
| `DeEsser` | Y | **N** | Y | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `TransientShaper` | Y | **N** | Y | Y | **N** | **N** | Y | Y | N | N | **PARKED** |
| `MultibandCompressor` | Y | Y | Y | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `ParametricEQ` | Y | Y | Y | Y | **N** | Y | Y | Y | N | N | **PARKED** |
| `GraphicEQ` | Y | Y | **N** | Y | **N** | Y | Y | Y | N | N | **PARKED** |
| `LowPass` | Y | Y* | Y | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `HighPass` | Y | **N** | Y | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `BandPass` | Y | Y | Y | Y | Y* | Y | Y | Y | N | N | **PARKED** |
| `Notch` | Y | Y | Y | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `LadderFilter` | Y | Y* | Y* | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `CombFilter` | Y | **N** | Y* | Y | Y* | **N** | Y | Y | N | N | **PARKED** |
| `DynamicEQ` | Y | Y | **N** | Y | Y* | **N** | Y | Y | N | N | **PARKED** |

**One class through: `NoiseGate`.** Fifteen park. **G4 is met on all sixteen
for the first time** — the independent pass ran, is recorded in every pack, and
its 45 broken clauses have been ruled on and re-graded; that is what this audit
closed.

---

## 3. Every `N` and `Y*`, with its evidence

### G2 — Tier 1

| Class | Ruling | Evidence |
|---|---|---|
| `Compressor` | **N** | Two rows are not green: `deinit()` leaves the `audioroute.Splitter` live because the node has no `deinit`, and the no-allocation row is `unmeasured`. §2 and §8, unticked by the pack itself. |
| `DeEsser` | **N** | **22.05 kHz was never rendered on MicroPython or the patched CircuitPython.** The gate asks for all three rates on both. §8 and §11. |
| `TransientShaper` | **N** | STATE is CPython-and-48-kHz-only, by the kit's own design. §2, §11. |
| `HighPass` | **N** | The `tail_samples` declaration is **red**, found by the refutation pass: `kit.tail(declared_tail_samples=305152)` on a DC step at the dossier's own worst case (10 Hz, Q 16, 24 dB/oct, +12 dB trim) returns `tail 403375 samples exceeds the declared 305152`, identical at 12 s and 16 s. The declaration was taken from a burst (196 330, passes). |
| `CombFilter` | **N** | The TAIL invariant is a stated disconfirmation above Feedback 0.5, not a pass (§2a), and STATE runs on CPython only. The refutation pass sharpened it: at 1760 Hz / Feedback 0.8 an impulse render is still non-zero at frame 262 143, parked on a ±1 LSB square wave at 1777.77 Hz — **17.4 cents sharp of the tuning and +4.33 dB above the tuned resonance**, which is a different musical statement from the docstring's "a low ring at the tuned pitch". |
| `Limiter`, `Expander`, `NoiseGate`, `LowPass`, `LadderFilter` | **Y\*** | `deinit()`/`reset()` cells carry `n/a` or `pass*` with a cause below the class — audioif's own nodes implement neither on the native builds, and `audioif_dynamics_reset` deliberately keeps the side-chain filter memory (`audioif/src/shared/audioif_dynamics.c:281-288`; measured consequence 33 LSB on the first block after `reset()`). **`NoiseGate`'s pack says no audioif issue was filed for it — one is owed.** |

### G3 — a planted fault of the same kind

| Class | Ruling | Evidence |
|---|---|---|
| `Limiter` | **N** | L7's second disconfirming clause — *"or a docstring that does not name the trade"* — has **no automated check and no planted fault**. It is true on inspection (`lib/audioeffects/rebuilt/limiter.py:41-47` and `:103-110` both name the 5 ms end and the 12.0 % figure, verified) but it is not demonstrated under the pack's own rule. |
| `GraphicEQ` | **N** | T4's fault (the detented section left at `mix = 1`) **cannot fire above band 3** at any probe tried: `b0..b2 RED, b3 green at peak 8000 / RED at peak 30000, b4..b9 green`. Six of ten bands are vacuous and two of the four the pack reports (5 and 9) are among them. |
| `DynamicEQ` | **N** | T3's planted fault (threshold lifted to −55 dBFS) *"moves the detector, not the claim T3 makes"* — the refuter's words and the auditor's ruling: it is not a fault of the same kind. T3 also has no independent power (10 dB under a 6 dB knee the law returns exactly 0, so T3 reduces to T1). |
| `Compressor` | **Y\*** | Met only through the refutation record's faults: §1's F2 fault was never run (the refuter ran it: `FET_RATIO_REFERENCE = 1e9` flattens both columns, red), §1's O1 fault is **inert** (`compressor.py:331-333` forces `memory = OPTICAL_MEMORY`; the refuter's `OPTICAL_MEMORY = 0.0` reads ratio **2.09 → RED**), and M5's fault was "as F5", which is a reachable knob. The pack must re-record all three. |
| `Expander` | **Y\*** | E4's depth-0 row is green clean **and** green faulted — the fault and the setting are the same value — so the demonstration rests on two rows, not three; and E1's ratio-8 row needed the fault driven downward to fire (the refuter ran it: slope 5.6126, −29.84 %). |
| `NoiseGate` | **Y\*** | G5's fastest-attack clause had **no planted fault**; the refuter planted one of its own kind (the Attack macro's floor moved 0.01 → 1.0 ms) and it reads **6.9167 ms against a 0.2 ms bar → RED**. It is not yet in `tests/test_noisegate.py`; that is owed. |
| `LadderFilter` | **Y\*** | T4(a) was cited with no fault of its own; the refuter planted four that fire (flat-topped at 0.1 → THD **37.226 % RED**; +2 dB drift → 1.008 dB RED) against a clean control of drift 0.010 dB / THD 0.0680 %. Owed in `tools/ladderfilter_evidence.py`'s battery. |
| `CombFilter` | **Y\*** | T3's rounder fault is legitimately green at 110 Hz; the refuter's +6 cent bias fault reads **−6.000 cents**, catching a bias an eighth the bar. Owed in the pack. |

### G5 — bytes, desktop and board

| Class | Ruling | Evidence |
|---|---|---|
| `Limiter`, `ParametricEQ`, `GraphicEQ`, `TransientShaper` | **N** | The board run's own commit (`42845a0`): these four *"render the bare probe's own digest at their defaults, so their CPU figures are real but their digests are not a check on the audio; a board run at a working patch is still owed."* The board leg of G5 does not exist for them. |
| `DeEsser` | **Y\*** | CPython differs from MicroPython and the patched CircuitPython on the `chord` probe by **6 samples of 288 000 at 48 kHz and 3 of 264 600 at 44.1 kHz, every one 1 LSB**. Cause reproduced with the class out of the graph: `audiomixer` is a pure-Python shim on CPython (`audiomixer.py:143-160`) and C on the other two. Not the class. |
| the other eleven | **Y\*** | CPython and desktop MicroPython are byte-identical on the probe material. **Nine of sixteen classes differ from the desktop on the boards**, and `42845a0` records the cause below the class: host and board agree on the integer-path nodes and differ on every float-path node, `cmods/bin/micropython` on the desktop reproduces the CPython digest exactly, and the mechanism is the Phase 1 FMA-contraction finding. Float width is the accepted cause under the anchor's `docs/accuracy-roadmap.md:612-616`. |

### G6 — cost

Measured on both boards 2026-09-07 (`42845a0`), `tools/measure_effect_cost.py`,
**at construction defaults — the runner applies no patch**, 256-frame stereo
blocks at 48 kHz. Marginal figures against the dossier budget:

| Class | P4 | budget | S3 | budget | Ruling |
|---|---|---|---|---|---|
| `BandPass` | 3.8 % | ≤ 4 % | 6.2 % | ≤ 13 % | **Y** |
| `NoiseGate` | 4.5 % | 6 % | 8.4 % | 12 % | **Y** |
| `ParametricEQ` | 15.2 % | 26 % | 25.3 % | 43 % | **Y** |
| `GraphicEQ` | 22.7 % | 38 % | 38.6 % | 64 % | **Y** |
| `LowPass` | 5.6 % | ≤ 1.5 % | 9.6 % | ≤ 5 % | **N** |
| `HighPass` | 5.7 % | ≤ 1.5 % | 9.6 % | ≤ 5 % | **N** |
| `Notch` | 5.6 % | ≤ 1.5 % | 9.6 % | ≤ 5 % | **N** |
| `CombFilter` | 7.0 % | ≤ 2 % | 12.2 % | ≤ 7 % | **N** |
| `Expander` | 8.4 % | 6 % | 16.3 % | 12 % | **N** |
| `Limiter` | 12.8 % | ≤ 4 % | 23.7 % | ≤ 12 % | **N** |
| `DynamicEQ` | 13.8 % | ≤ 8 % | 25.3 % | ≤ 25 % | **N** |
| `TransientShaper` | 14.9 % | 5 % | 31.3 % | 10 % | **N** |
| `LadderFilter` | 16.3 % | 8 % | 26.9 % | 14 % | **N** |
| `Compressor` | 20.7 % | ≤ 8 % | 39.0 % | ≤ 22 % | **N** |
| `DeEsser` | 27.5 % | 8 % | 50.8 % | 15 % | **N** |
| `MultibandCompressor` | 44.3 % | 25 % | 83.6 % | 45 % | **N** |

Twelve over on both boards. **No `" - lean"` patch was measured.**
`LadderFilter` is the only class that ships one — patch 6 `Ladder - lean`
(`lib/audioeffects/rebuilt/ladderfilter.py:121`) — and the board run did not
run it, so the gate's escape clause is unexercised on all twelve. Every class
runs in real time on both boards; `MultibandCompressor` on the S3 is the edge
at 4.910 ms of a 5.333 ms block.

**A caveat that belongs to all sixteen, not to any one:** the figures are at
construction defaults, and `42845a0` says *"no class was put into the expensive
path its evidence pack names"*. No I2S device was opened, so the `audiodev`
pump and the I2S ring — the stompbox seam of the vision's §9a — are in none of
these numbers.

---

## 4. Parked, with the issue to file

Each is a `PyDevices/audiocomponents` issue, stakes first, per roadmap §2a.
Six of them are the class's own defect; the rest are budget and coverage.

### 4.1 The class's own — a defect at reachable settings

**`Limiter` — the true-peak ceiling is broken by committed probe material.**
> A `Limiter` set to a −6 dBFS true-peak ceiling passes **+2.22 dB TP** on
> `ramp_fs` and +1.12 dB on `dc_step` — two of the 65 committed probes at
> 48 kHz, three at 44.1 kHz. A player who sets a ceiling to protect a converter
> does not get it on transients or DC steps; the promise holds for steady tones
> only. Cause, in the class: the catch stage (`lib/audioeffects/rebuilt/limiter.py:174-180`
> — `DYN_LIMIT`, `attack_ms=0.0`) is a *sample*-peak brickwall running after the
> true-peak detector, so it re-clamps to the sample ceiling and reinstates the
> inter-sample overshoot the shape stage had just made room for. Reproduced
> through the kit's own renderer plus `kit.truepeak`. Fix: make the catch stage
> true-peak-aware, or narrow L1 to the material it holds for and say so in the
> docstring and the catalogue row. Also: L6's slope clause is a measurement that
> cannot fail (−0.00000 dB/dB at ratio 1.0, a build that does no compression)
> and its knee clause moves 8 dB with the measurement grid.

**`BandPass` — half a decibel lost at the two knobs' own stops.**
> At Frequency 0 and Width 127 — `centre_hz 20.000`, `Q 32.000`, read back off
> the instance — the settled gain at f₀ is **−0.486 dB** where the trait's bar
> is ±0.05 dB and RBJ's closed form says **0.000**. It is not settling
> (−0.4858 / −0.4820 / −0.4801 over three window rules) and not the prototype;
> it is level-dependent (+0.095 dB at −3 dBFS), which points at the recursion's
> arithmetic at w₀ = 0.0026 rad. A `Sub Window` patch is two knob turns from it.
> Fix or bound: identify the arithmetic, or carry f₀ ≤ 25 Hz at Q ≥ 16 as out of
> tolerance in the docstring and the catalogue row. Three further rows (T2,
> T4a, T4b) are disconfirmed as *statements of the prototype* whose conditions
> the dossier never wrote down — the bilinear warp above ~2 kHz and above Q 8.

**`HighPass` — `tail_samples` under-declares by a third.**
> `HighPass.TAIL_SAMPLES` is 305 152; a DC step at the dossier's own worst case
> (10 Hz, Q 16, 24 dB/oct, +12 dB trim) measures **403 375** samples, RED at 12 s
> and 16 s alike. The contract reads `tail_samples` off the class, so a host
> that trusts it truncates the tail. The declaration was taken from a burst
> (196 330, passes); a step is the longer excitation. Fix: re-measure with the
> `dc_step` leg and raise the declaration (next multiple of 2048 is 405 504), or
> state why a step is out of scope. Also disconfirmed: T2 and T6 at 24 dB/oct
> with a low corner — **f₀ = 10 Hz is patch 0's own default** — and T5, whose
> stimulus was changed after measurement.

**`DynamicEQ` — the composite law is missed at three shipped patches.**
> The trait *"the composite is −(L−T)(1−1/R) within 1 dB"* is missed by
> **+1.439 dB at patch 3 "Low End Tamer"'s own shipped settings** and +0.888 dB
> at patch 1's; the two-octave isolation bar (0.2 dB) is missed by 0.271 dB at
> patch 5 "Half Measure"'s shipped Q 1.01. The deviation is monotone in attack
> and in ratio and reaches 4.269 dB at the macro's own 100 ms end. The class's
> own module docstring (`lib/audioeffects/rebuilt/dynamiceq.py:78-81`) names the
> cause — the follower lags the peak — and the evidence never ran the axis. Fix:
> bound the traits by attack and by Q, or move the patches off settings the
> traits cannot survive.

**`MultibandCompressor` — every band tilts, and the window hid two of three.**
> The depth and evenness clauses were measured on a tone window that covers 1.3
> of the mid band's 3.3 octaves. Widened inside the band's own −6 dB corners:
> mid band mean **−11.27 dB** against a ±0.5 bar and tilt **1.31 dB** against
> 0.5; high band tilt 1.42; low band 1.82, not the 0.73 reported. It is the
> band's own LR4 skirt against a fixed threshold — arithmetic, not a bug — but
> it applies to **every** band, and the class docstring and the catalogue row
> are written from the narrow window.

**`Compressor` — clean at Release slowest, a fuzz box at Release fastest.**
> F5 and V6 both claim "clean"; at 50 Hz with the Release macro at 127 — a
> position a player dials — the class reads **3.89 % THD** against a 0.5 % bar
> and 0.58 % against V6's 0.2 %. What §12 files as F5's *planted fault* is the
> class's own behaviour at an ordinary setting. Also: V3's RMS/peak bar is
> frequency-dependent (0.629 dB at 50 Hz against 0.50); F4 measures a palette
> node no configuration of the class can reach (`grep -n feedback_detector`
> returns one hit, prose at `:44`); and O1's planted fault is inert because
> `compressor.py:331-333` forces `memory = OPTICAL_MEMORY`.

### 4.2 Coverage — a gate item with no run behind it

**`DeEsser` — 22.05 kHz was never rendered on MicroPython or CircuitPython.**
> The gate asks every Tier 1 invariant at three rates on both native builds;
> `DeEsser`'s third rate exists on CPython only. Until it runs, nothing says the
> class behaves at 22.05 kHz where it ships. Also disconfirmed by the refutation
> pass: D1's level independence is a property of Sensitivity 34 (spread
> **2.668 dB** at Sensitivity 44 — the setting this pack's own D7 row uses);
> D3's 12 dB clause is unreachable (best 11.463 dB); D2's corner-tracking test
> passes with the crossover frozen; D4's 925 dB/sec is printed and never
> asserted, and the test is green at 132 dB/sec.

**`TransientShaper` — STATE runs on CPython at 48 kHz only, and the board digest is a bypass.**
> Two coverage holes, both recorded and neither closed: the STATE invariant is
> CPython-and-48-kHz-only, and the board run rendered the bare probe's own
> digest, so the P4/S3 leg is not a check on this class's audio. Also
> disconfirmed: T1 over −6…−40 dBFS at Attack +12 (spread **3.422 dB** against
> 0.500), T3's Sustain leg on a 3 dB/s note (saturates **8 dB short** of its
> stated end), and T4's planted fault is red only at the one render length the
> pack used.

**`GraphicEQ` — T4's fault cannot fire on six of the ten bands it is claimed over.**
> The detented-band identity is real and byte-exact on all ten bands at three
> rates, but the fault offered against it fires only on bands 0–3; a class that
> never muted a detented band would pass at bands 5 and 9, two of the four the
> evidence reports. And T1's +9 dB shelf clause has no probe amplitude behind
> it: at peak 14 000 it reads **+8.76 / +8.93 dB, under its own bar**, and the
> wet render first clips at peak 9 000 — the §6 patch table's own 11 000-peak
> source already halves the margin.

**`ParametricEQ` — the board digest is the bare probe's, and two traits are level-bound.**
> The P4/S3 leg is a bypass render, so it checks nothing about this class's
> audio. T3 and T5 are disconfirmed above −16 dBFS (T5 reads **8.05 dB** against
> a 0.1 dB bar at −6 dBFS, because every section writes int16 and clips), T2 is
> green on a byte-flat wire (`tools/phase2_probes/parametriceq_traits.py:99`
> marks every interior point of a plateau a local maximum), and T4's crossing
> clause reads back the class's own `SKIRT_DB = 1.0` on a knife edge 0.25 dB
> wide.

### 4.3 Budget — twelve classes, one issue

**Phase 2's Tier 3 budgets were derived from instruction counts and twelve of sixteen overran them.**
> Every Phase 2 class runs in real time on both boards, and twelve still fail
> gate item G6 because their dossier budget was instruction-count arithmetic
> that cannot see the per-block Python of a node graph. The gate's escape —
> a `" - lean"` patch that fits — is unexercised: only `LadderFilter` ships one
> (patch 6, `ladderfilter.py:121`) and the board run did not measure it.
> Decide once, for the phase: re-derive the budgets from the measured graphs
> (the honest reading of `42845a0`), or require and measure a lean patch on all
> twelve. Related and unmeasured either way: the figures are at construction
> defaults, no class was put in the expensive path its pack names, and no I2S
> device was opened, so the `audiodev` pump and I2S ring of vision §9a are in
> none of these numbers.

**Also owed, and not filed by the sessions that found them:**

- an **audioif** issue for `audioif_dynamics_reset` keeping the side-chain
  filter memory (`audioif/src/shared/audioif_dynamics.c:281-288`), which
  `NoiseGate`'s pack measures at 33 LSB on the first block after `reset()` and
  names as unfiled;
- an **audiocomponents** issue for the `LowPass` regression net's blind spot:
  `tests/test_cpython_effects_lowpass.py:45-46` short-circuits only at
  `node.mix == 0.0`, so a fault leaving every section at `mix = 0.001` — the
  class audibly a wire — leaves the T1/T2/T3 tests green.

---

## 5. Through

**`NoiseGate`.** G1–G8 all met, and its two `Y*` cells carry causes below the
class: `reset()` cannot clear the node's key filters
(`audioif_dynamics.c:281-288`, measured at 33 LSB, committed as a test that
goes red on purpose if audioif ever clears them), and G5's board digests carry
the FMA cause. Its one broken trait, **G4's refutation of the closed-gain
row**, is a disconfirmation with a measured cause that is *not* the build —
int16's own output floor, the error tracking output level rather than depth
below threshold. Cost is inside both budgets (4.5 % / 8.4 % against 6 % /
12 %). It owes G9's catalogue cost column and G10's wording, which the whole
phase owes, and one audioif issue.
