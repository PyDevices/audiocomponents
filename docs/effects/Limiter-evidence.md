# Evidence Pack — `Limiter` (no standout; a lookahead brickwall)

Written at Station C from the runs named in each section. The dossier is
[`Limiter.md`](Limiter.md); its Tier 2 rows are L1–L7 and every one of them has
a section here.

**Three rules this file is written under.** Numbers come from runs, each with
its command. A measurement with no planted fault cannot be cited. And §11 says
what is not done, in its own section.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `Limiter` |
| Dossier | [`Limiter.md`](Limiter.md), traits frozen 2026-09-07 at `26b80aa` |
| Module | `lib/audioeffects/rebuilt/limiter.py` |
| Base | `_component.Component` |
| Family / phase | Dynamics, roadmap Phase 2 |
| Standout | none — a specification (ITU-R BS.1770-5 Annex 2) and a paper (Hämäläinen, DAFx-02), not a circuit |
| Grade | **design** |
| Portability tier | **audioif** (`REQUIRES = ("audiodynamics",)`) |
| Landed in commit | `7399979` — the class, its tests, the README row and the CHANGELOG line; this file in the commit after it |
| audioif pin | `2f6cbc3`; the venv's `audiodynamics` is that build, and `audioif_dynamics.c` is byte-identical between the pin and the checkout |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3; `cmods/bin/micropython` v1.28.0-dirty (2026-09-07); `cmods/bin/circuitpython-effects` 10.2.1-dirty (2026-09-07) |
| Boards | ESP32-P4 (COM4) and ESP32-S3 (COM49) — Tier 3 cost and digest measured 2026-09-07, §4 |

**Dossier trait set frozen before the rebuild began:** **yes**. Commit `26b80aa`
froze §3 and settled §8; the class's first line was written after it. That
commit also corrected three palette claims the seed had wrong, from runs
committed as `tools/phase2_probes/limiter_palette.py` — the correction is in
the dossier's Appendix G, not invented here.

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

Command for every row below:

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/limiter_traits.py
```

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| L1 | The ceiling is a true-peak promise: ≤ 0.5 dB TP over the Ceiling on every probe, and the probe set must carry a worst-phase f_s/4 tone | **disconfirmed** — REFUTED on the committed probe corpus | TRUEPEAK on the worst-phase f_s/4 tone into a −6 dBFS ceiling: **+0.17 dB TP** at 48 kHz and at 44.1 kHz, cpython | the kit's faulted read (`read="sample_peak"`) judges the same render green at **−6.00 dBFS** while the correct read is **RED at +3.01 dB** | *"The tone is generated in the test, so it could be the wrong tone."* Its true peak reads 3.01 dB above its sample peak, which is S1's own analytic figure for f_s/4, and the committed probe `tone_fs4` has the same shape and the same pair (`effect_probes/README.md`). The digests in §3 are taken on that committed probe. |
| L2 | Lookahead never creates overshoot: ≤ 0.1 dB over at every setting, **and** no rise with lookahead | **demonstrated** | 1 ms burst into a −12 dBFS ceiling, Lookahead 0→10 ms in 1 ms steps: **+0.000 dB at every one of the eleven settings**, 48 kHz, cpython | `NoCatchStage` — the catch stage removed, which is the one-node limiter — goes **RED from 1 ms (+0.144 dB) to 10 ms (+1.447 dB)**, and rises monotonically, so both clauses fire | *"+0.000 dB at every setting is suspiciously flat — is the measurement reading the ceiling instead of the output?"* The same measurement on the same probe reads +1.447 dB on the faulted build, so it is reading the output. The flatness is the C: with `attack_ms=0` the envelope is the current sample, `DYN_LIMIT` returns exactly `−over`, and that gain multiplies that same sample. |
| L3 | A peak shorter than the lookahead is still caught, at **every** non-zero setting | **demonstrated** | single-sample impulse at 0 dBFS into a −12 dBFS ceiling, 0.5/1/2/5/10 ms: **+0.000 dB at all five**, 48 kHz, cpython | `NoCatchStage`: +0.073 dB at 0.5 ms (inside the bar — the trait is right that it loses it *worst between the ends*) then **RED at 1, 2, 5 and 10 ms**, to +1.447 dB | *"The 0.5 ms fault row is green, so the fault is weak there."* It is, and that is the trait's own point; the row is disconfirmed by *any* setting over the bar and four of the five fire. |
| L4 | `latency_samples == floor(lookahead_ms × fs / 1000)` at three rates, for every patch and macro position, and the click agrees to the sample | **demonstrated** | 18 combinations of {48000, 44100, 22050} × {0, 0.5, 1.5, 3, 7.3, 10 ms}: reported == floor() == measured click in **all 18**, cpython. Every patch, at all three rates, in `tests/test_cpython_effects_limiter.py` | report 256 samples short with the DSP untouched → **RED**, "measured 480 samples against a reported 224"; the two audio digests are both `176dfba1`, so nothing but the report moved | *"The class picks the number it reports, so of course it matches."* It does not: the node truncates in single precision and the class's naive form disagreed with it 22 times in 489 (dossier G.3). The click is measured off the render, not read off the class. |
| L5 | Zero by default: `latency_samples` 0, Lookahead 0 ms, True Peak off | **demonstrated** | constructed with no options at 48000, 44100 and 22050: latency 0, tail 0, Lookahead 0.000 ms, True Peak 0.00, patch 0 | patch 2 ("Loud") → latency **143 samples**, True Peak 1.00 — the same read, red | *"A default is not a measurement."* The read is against a constructed instance and against patch 0 after a `program_change`, and the fault shows the same read moving. |
| L6 | Infinite ratio, hard knee: slope ≤ 0.02 dB/dB over 24 dB, knee width ≤ 0.5 dB at Knee 0 | **unmeasured** — REFUTED; the slope clause cannot fail and the knee clause is grid-dependent | 25-point static curve, −24…−0.2 dBFS into a −24 dBFS ceiling: slope **−0.00000 dB/dB**, highest output −24.0022 dBFS; knee width at Knee 0 **0.000 dB** on a 0.25 dB grid, cpython | the same width measurement at Knee 12 → **10.500 dB**, red against the 0.5 dB bar | *"A zero-width knee could mean the grid cannot resolve one."* The grid is 0.25 dB and the same grid resolves 10.5 dB at the other end of the macro, so it can. |
| L7 | Smoothing is a documented trade: THD ≤ 1 % at the default patch, and the fastest Release named in the docstring as a distortion setting | **demonstrated** | 60 Hz sine 12 dB into a −12 dBFS ceiling: **0.710 %** at 48 kHz and **0.710 %** at 44.1 kHz on the default patch's 149 ms release, cpython | the Release macro at its fastest, 5 ms → **11.994 %**, red; 100 ms reads 1.047 %, also red, which is why the patch is not at 100 ms | *"1 % is the class's own number, chosen after the fact to fit."* It was chosen before: the dossier fixed 1 % on 2026-09-06 and the **patch** moved to meet it — the seed proposed 100 ms and the measurement pushed it to 149 ms (dossier §6). |

- **demonstrated** = a measurement, that measurement red on a planted fault of
  the same kind, and a surviving refutation. **After the gate audit five have all three (L2, L3, L4, L5, L7); L1 is disconfirmed and L6 unmeasured.**
- **disconfirmed**: none.
- **unmeasured**: none at Tier 2. Tier 3 is a separate matter — see §4 and §11.

**Refutation pass.** Run by the class builder against its own build,
2026-09-07, immediately after each measurement went green; the arguments are in
the last column above. What it could not break: L2 and L3, because the faulted
build reproduces the dossier's Appendix F.1 numbers exactly and the correct
build reproduces none of them. What it *did* break, and what changed as a
result: the class docstring first said "25.8 % THD at the 5 ms end" of the
Release macro. That number is the node's reading at a **1 ms** release, which
this macro cannot reach; at the macro's own floor the measurement reads
**11.994 %**. The docstring and the CHANGELOG were corrected to the measured
number before this file was written.

**Verbatim run:**

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/limiter_traits.py
Limiter Tier 2 traits, CPython, audioif at the pin
========================================================================

L1  the ceiling is a true-peak promise (bar: +0.50 dB TP)
    rate    True Peak   sample peak   true peak   over ceiling
    48000   on            -8.84 dBFS     -5.83 dBTP   +0.17 dB  green
    48000   off           -6.00 dBFS     -2.99 dBTP   +3.01 dB  RED
    44100   on            -8.84 dBFS     -5.83 dBTP   +0.17 dB  green
    44100   off           -6.00 dBFS     -2.99 dBTP   +3.01 dB  RED
    planted fault: the kit's faulted read judges the ceiling on
    the sample peak instead of the reconstructed one.
      read=true_peak    judged    -2.99 -> RED   true_peak: -2.99 against a ceiling of -6.00 (3.01 dB over, bar 0.50)
      read=sample_peak  judged    -6.00 -> green   

L2/L3  lookahead never creates overshoot (bar: +0.10 dB, and no
       rise with lookahead). Ceiling -12 dBFS, release 60 ms.
    L2  1 ms burst
      lookahead    the class    fault: no catch stage
        0.00 ms    +0.000 dB    +0.000 dB   green / green
        1.00 ms    +0.000 dB    +0.144 dB   green / RED
        2.00 ms    +0.000 dB    +0.290 dB   green / RED
        3.00 ms    +0.000 dB    +0.434 dB   green / RED
        4.00 ms    +0.000 dB    +0.579 dB   green / RED
        5.00 ms    +0.000 dB    +0.724 dB   green / RED
        6.00 ms    +0.000 dB    +0.868 dB   green / RED
        7.00 ms    +0.000 dB    +1.013 dB   green / RED
        8.00 ms    +0.000 dB    +1.158 dB   green / RED
        9.00 ms    +0.000 dB    +1.303 dB   green / RED
       10.00 ms    +0.000 dB    +1.447 dB   green / RED
    L3  1-sample impulse
      lookahead    the class    fault: no catch stage
        0.50 ms    +0.000 dB    +0.073 dB   green / green
        1.00 ms    +0.000 dB    +0.144 dB   green / RED
        2.00 ms    +0.000 dB    +0.290 dB   green / RED
        5.00 ms    +0.000 dB    +0.724 dB   green / RED
       10.00 ms    +0.000 dB    +1.447 dB   green / RED

L4  reported latency equals floor(lookahead_ms * fs / 1000)
    rate     asked      floor()   reported   click   verdict
    48000    0.00 ms         0          0       0  green
    48000    0.50 ms        24         24      24  green
    48000    1.50 ms        72         72      72  green
    48000    3.00 ms       144        144     144  green
    48000    7.30 ms       350        350     350  green
    48000   10.00 ms       480        480     480  green
    44100    0.00 ms         0          0       0  green
    44100    0.50 ms        22         22      22  green
    44100    1.50 ms        66         66      66  green
    44100    3.00 ms       132        132     132  green
    44100    7.30 ms       321        321     321  green
    44100   10.00 ms       441        441     441  green
    22050    0.00 ms         0          0       0  green
    22050    0.50 ms        11         11      11  green
    22050    1.50 ms        33         33      33  green
    22050    3.00 ms        66         66      66  green
    22050    7.30 ms       160        160     160  green
    22050   10.00 ms       220        220     220  green
    planted fault: report 256 samples short, DSP untouched.
      reported   0 short -> green   
      reported 256 short -> RED   measured [480.0, 480.0] samples against a reported 224 (256.0 samples out, bar 1.0) at 48000 Hz
      audio digests 176dfba1 and 176dfba1 - identical, so only the report moved

L5  zero by default
    48000 Hz  latency 0, tail 0, Lookahead 0.000 ms, True Peak 0.00, patch 0
    44100 Hz  latency 0, tail 0, Lookahead 0.000 ms, True Peak 0.00, patch 0
    22050 Hz  latency 0, tail 0, Lookahead 0.000 ms, True Peak 0.00, patch 0
    planted fault: patch 2 ('Loud'), which turns both on.
      patch 2 -> latency 143 samples, True Peak 1.00  RED against L5's bar, as it should be

L6  infinite ratio, hard knee. Ceiling -24 dBFS, so a full 24 dB
    of input above it fits under 0 dBFS in int16.
    slope above the ceiling over 24 dB: -0.00000 dB/dB (bar 0.02)  green
    highest output over the whole span: -24.0022 dBFS
    knee width at Knee 0:  0.000 dB (bar 0.50)  green
    planted fault: the same measurement at Knee 12 -> 10.500 dB  RED

L7  smoothing is a documented trade (bar: 1 % at the default
    patch). 60 Hz sine at 0 dBFS into a -12 dBFS ceiling.
    48000 Hz, the default patch's 149 ms release: 0.710 %  green
    44100 Hz, the default patch's 149 ms release: 0.710 %  green
    planted fault: the Release macro at its fastest, 5 ms.
      release    5.0 ms ->  11.994 %   RED
      release   30.0 ms ->   3.134 %   RED
      release  100.0 ms ->   1.047 %   RED
      release  149.0 ms ->   0.715 %   green
      release  300.0 ms ->   0.362 %   green
    The docstring names the 5 ms end as a distortion setting; that number is recorded, not bounded.
```


### Gate audit — the refutation pass's verdicts, ruled on (2026-09-07)

Ruled by the Phase 2 gate auditor against the **Refutation record** at the
foot of this file. Where a refutation stands the verdict above was changed
and the class was **not** touched; where the auditor re-ran a figure itself
the run is named. The roadmap's class-gate rule is the test applied: a
*demonstrated* trait needs a measurement, that measurement shown red on a
planted fault of the same kind, **and** a surviving refutation.

| Row | Ruling | Cause recorded, and the auditor's check |
|---|---|---|
| L1 | **refutation stands** → disconfirmed | §1 measures one probe (`l1_true_peak`, `tools/phase2_probes/limiter_traits.py:107-124`, `worst_phase_fs4` only) while the trait's disconfirmer is "any probe". **Reproduced by the auditor** through the kit's own renderer and read with `kit.truepeak` (`scratch/audit/l1.py`, `scratch/audit/l1b.py`): at ceiling −6 dBFS, True Peak on, release 60 ms, the committed `ramp_fs` reads sample −6.00 dBFS / true peak **−3.78 dBTP / +2.22 dB over → RED**, and `dc_step` −6.02 / −4.88 / **+1.12 dB → RED**. The cause is the class's own: the catch stage (`limiter.py:174-180` — `DYN_LIMIT`, `attack_ms=0.0`) is a *sample*-peak brickwall running after the true-peak detector and re-clamps to the sample ceiling. This is a gap in the promise, not only in the measurement. |
| L6 | **refutation stands** → unmeasured | The slope clause cannot fail: with `_BRICKWALL_RATIO` (`limiter.py:68`) swapped at build time the reading is **−0.00000 dB/dB at ratio 4, 1.5 and 1.0** — a build that does no compression at all — and only tracks the ratio with the catch stage removed (+0.25007 / +0.99996 dB/dB). The knee clause is a property of the grid: the same Knee-0 build reads **0.000 dB on the run's 0.25 dB grid and 7.900 dB, RED, on a 0.05 dB grid**. |

L2, L3, L4, L5 and L7 survive; L4's answer sentence and L7's docstring clause
carry corrections the Refutation record states.

**Rule applied to the two non-`disconfirmed` outcomes.** A refutation that
shows the class failing its own bar makes the row **disconfirmed**. A
refutation that shows the *demonstration* invalid — a fault that cannot fire,
a reading that is green on a bypass, a bar that was never asserted — leaves no
number that tests the trait, so the row becomes **unmeasured**, on this pack's
own precedent for a measurement that "produced a number that does not test the
claim". Neither outcome is a licence to edit the class.


---

## 2. Tier 1 invariants

The block is run on **all three interpreters**, at all three rates, by
`tools/phase2_probes/limiter_tier1.py`. Every one of these ten is integer work
— a byte compare, a last-non-zero index, an onset index, a peak, or a read of
the live surface — so the MicroPython and CircuitPython columns are runs rather
than "the same class, so presumably the same answer".

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/limiter_tier1.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      -X heapsize=512M tools/phase2_probes/limiter_tier1.py
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=512M tools/phase2_probes/limiter_tier1.py
```

Last line of each: **`0 failing invariants`** — cpython, micropython and
circuitpython-effects alike.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| The defeated setting is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node the class built silent and stateless, and the borrowed source untouched | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `deinit()` releases every node the class built and leaves the source rendering | STATE | pass | **partial** | **partial** | pass | **partial** | **partial** | pass | **partial** | **partial** |
| `capabilities` names exactly the optional behaviours honoured | STATE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Pulling `output` allocates nothing | STATE | n/a | pass | pass | n/a | pass | pass | n/a | pass | pass |
| Rate-honest: options clamp at the running rate, never refuse | RESPONSE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass | pass | pass | pass | pass | pass | pass | pass | pass |

**`deinit()`, and why six cells say *partial* rather than *pass*.**
`audiodynamics.Dynamics` has **no `deinit()` at all** on the two native builds
— `hasattr(node, "deinit")` is `False` on `cmods/bin/micropython` and on
`cmods/bin/circuitpython-effects`, and `True` only in the CPython shim.
`_component.Component.deinit()` walks the class's node list and calls
`getattr(node, "deinit", None)`, so on those builds it finds nothing to call.
What **is** shown there: the class's surface closes (`output` raises
`RuntimeError`), a second `deinit()` is safe, and the borrowed source still
renders afterwards. What is **not** shown there: that the nodes themselves
released anything, because there is nothing to observe. `audioecho.FeedbackDelay`
is in the same position; `audiofilters.Filter` and `audiomixer.Mixer` are not.
This is a node-surface gap, not a class defect, and it is in §11.

**The allocation row's `n/a` on CPython** is `gc.mem_alloc()`, which is a
MicroPython read. On the two builds that have it, the number is a **difference
against a control**: 200 pulls through the class and 200 through the bare
source, because `audiocore.get_buffer` allocates its own `(result, buffer)` per
call whatever is behind it — 1088 bytes a pull, measured with no class in the
path. The class's own figure is `217600 − 217600 = **+0 bytes**`, on a render
whose peak is 8231 LSB and therefore not silence.

**Mono.** The dossier's §4 says a mono source is limited on its one channel and
not summed. Measured: `channel_count` 1, and a full-scale burst into a −12 dBFS
ceiling comes out at **+0.000 dB** over it, at all three rates on all three
interpreters (the `MONO` row of the run).

**Planted faults for this block**, each with its clean control:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | `rebuilt._EPSILON_DB` set to 0, so the detector's own `envelope + 1e-6` is left uncorrected | green, 0 of 16384 samples differ | **RED**, 28 of 16384 differ by 1 LSB (`tests/test_cpython_effects_limiter.py::TierOne::test_without_the_epsilon_correction_the_wire_is_red`) |
| CLICK | `latency_samples` reported 256 short, DSP untouched | green | **RED** at 48 kHz and 44.1 kHz, both audio digests `176dfba1` |
| STATE | the catch stage removed (`NoCatchStage`) — the same subclass L2 and L3 use | green | **RED**: the class overshoots the ceiling by up to 1.447 dB |
| TAIL | the lookahead at its maximum, so the class holds 480 samples it must still drain to exact zero | tail 0 samples at Lookahead 0 | tail **480 samples, declared 480, residual 0 LSB** — the declared number is what makes this checkable, and reporting 0 there would be red |

`reset()` and `deinit()` walk the node list `_component` requires the class to
enumerate with `self._own()`. Nodes enumerated by this class, in build order:
**`shape`** (`audiodynamics.Dynamics`, `DYN_COMPRESS`) and **`catch`**
(`audiodynamics.Dynamics`, `DYN_LIMIT`). The borrowed source is not among them,
and the run asserts that.

**Verbatim, CPython:**

```
Limiter Tier 1 invariants - cpython
========================================================================

48000 Hz
   WIRE ceiling 0 dB, gain 0          pass  0 of 16384 samples differ
   TAIL lookahead  0.0 ms             pass  tail 0 samples (declared 0), residual 0 LSB
   TAIL lookahead 10.0 ms             pass  tail 480 samples (declared 480), residual 0 LSB
   LEVEL ceiling   +0.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling   -6.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling  -24.0 dB            pass  worst deviation from the source 0 LSB
   GAIN  0.0 dB into the ceiling      pass  measured +0.000 dB
   GAIN  6.0 dB into the ceiling      pass  measured +5.994 dB
   GAIN 12.0 dB into the ceiling      pass  measured +11.995 dB
   GAIN 24.0 dB into the ceiling      pass  measured +23.999 dB
   CLICK lookahead  0.0 ms            pass  reported 0, measured 0, floor(ms*fs/1000) 0
   CLICK lookahead  1.5 ms            pass  reported 72, measured 72, floor(ms*fs/1000) 72
   CLICK lookahead 10.0 ms            pass  reported 480, measured 480, floor(ms*fs/1000) 480
   STATE reset clears the ring        pass  primed 16423 LSB, after reset 0 LSB
   STATE the source is not owned      pass  2 nodes owned
   STATE deinit closes the surface    pass  output raises after deinit, and deinit twice is safe
   STATE the source still renders     pass  20000 LSB off the borrowed source after the class over it was deinited
   STATE the nodes refuse work        pass  2 of 2 refused after deinit
   CAPS () and no transport read      pass  capabilities (), transport called 0 times
   MONO channel_count 1               pass  channel_count 1, peak +0.000 dB over the ceiling
   RATE lookahead 10 ms clamps        pass  480 samples at 48000 Hz
   ALLOC pulling output               n/a   gc.mem_alloc() is a MicroPython read; CPython's leg is tracemalloc, in the kit's STATE

44100 Hz
   WIRE ceiling 0 dB, gain 0          pass  0 of 16384 samples differ
   TAIL lookahead  0.0 ms             pass  tail 0 samples (declared 0), residual 0 LSB
   TAIL lookahead 10.0 ms             pass  tail 441 samples (declared 441), residual 0 LSB
   LEVEL ceiling   +0.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling   -6.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling  -24.0 dB            pass  worst deviation from the source 0 LSB
   GAIN  0.0 dB into the ceiling      pass  measured +0.000 dB
   GAIN  6.0 dB into the ceiling      pass  measured +5.994 dB
   GAIN 12.0 dB into the ceiling      pass  measured +11.994 dB
   GAIN 24.0 dB into the ceiling      pass  measured +23.999 dB
   CLICK lookahead  0.0 ms            pass  reported 0, measured 0, floor(ms*fs/1000) 0
   CLICK lookahead  1.5 ms            pass  reported 66, measured 66, floor(ms*fs/1000) 66
   CLICK lookahead 10.0 ms            pass  reported 441, measured 441, floor(ms*fs/1000) 441
   STATE reset clears the ring        pass  primed 16423 LSB, after reset 0 LSB
   STATE the source is not owned      pass  2 nodes owned
   STATE deinit closes the surface    pass  output raises after deinit, and deinit twice is safe
   STATE the source still renders     pass  19999 LSB off the borrowed source after the class over it was deinited
   STATE the nodes refuse work        pass  2 of 2 refused after deinit
   CAPS () and no transport read      pass  capabilities (), transport called 0 times
   MONO channel_count 1               pass  channel_count 1, peak +0.000 dB over the ceiling
   RATE lookahead 10 ms clamps        pass  441 samples at 44100 Hz
   ALLOC pulling output               n/a   gc.mem_alloc() is a MicroPython read; CPython's leg is tracemalloc, in the kit's STATE

22050 Hz
   WIRE ceiling 0 dB, gain 0          pass  0 of 16384 samples differ
   TAIL lookahead  0.0 ms             pass  tail 0 samples (declared 0), residual 0 LSB
   TAIL lookahead 10.0 ms             pass  tail 220 samples (declared 220), residual 0 LSB
   LEVEL ceiling   +0.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling   -6.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling  -24.0 dB            pass  worst deviation from the source 0 LSB
   GAIN  0.0 dB into the ceiling      pass  measured +0.000 dB
   GAIN  6.0 dB into the ceiling      pass  measured +5.994 dB
   GAIN 12.0 dB into the ceiling      pass  measured +11.994 dB
   GAIN 24.0 dB into the ceiling      pass  measured +23.999 dB
   CLICK lookahead  0.0 ms            pass  reported 0, measured 0, floor(ms*fs/1000) 0
   CLICK lookahead  1.5 ms            pass  reported 33, measured 33, floor(ms*fs/1000) 33
   CLICK lookahead 10.0 ms            pass  reported 220, measured 220, floor(ms*fs/1000) 220
   STATE reset clears the ring        pass  primed 16423 LSB, after reset 0 LSB
   STATE the source is not owned      pass  2 nodes owned
   STATE deinit closes the surface    pass  output raises after deinit, and deinit twice is safe
   STATE the source still renders     pass  19999 LSB off the borrowed source after the class over it was deinited
   STATE the nodes refuse work        pass  2 of 2 refused after deinit
   CAPS () and no transport read      pass  capabilities (), transport called 0 times
   MONO channel_count 1               pass  channel_count 1, peak +0.000 dB over the ceiling
   RATE lookahead 10 ms clamps        pass  220 samples at 22050 Hz
   ALLOC pulling output               n/a   gc.mem_alloc() is a MicroPython read; CPython's leg is tracemalloc, in the kit's STATE

0 failing invariants
```

**MicroPython** (`0 failing invariants`, last block):

```
22050 Hz
   WIRE ceiling 0 dB, gain 0          pass  0 of 16384 samples differ
   TAIL lookahead  0.0 ms             pass  tail 0 samples (declared 0), residual 0 LSB
   TAIL lookahead 10.0 ms             pass  tail 220 samples (declared 220), residual 0 LSB
   LEVEL ceiling   +0.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling   -6.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling  -24.0 dB            pass  worst deviation from the source 0 LSB
   GAIN  0.0 dB into the ceiling      pass  measured +0.000 dB
   GAIN  6.0 dB into the ceiling      pass  measured +5.994 dB
   GAIN 12.0 dB into the ceiling      pass  measured +11.994 dB
   GAIN 24.0 dB into the ceiling      pass  measured +23.999 dB
   CLICK lookahead  0.0 ms            pass  reported 0, measured 0, floor(ms*fs/1000) 0
   CLICK lookahead  1.5 ms            pass  reported 33, measured 33, floor(ms*fs/1000) 33
   CLICK lookahead 10.0 ms            pass  reported 220, measured 220, floor(ms*fs/1000) 220
   STATE reset clears the ring        pass  primed 16423 LSB, after reset 0 LSB
   STATE the source is not owned      pass  2 nodes owned
   STATE deinit closes the surface    pass  output raises after deinit, and deinit twice is safe
   STATE the source still renders     pass  19999 LSB off the borrowed source after the class over it was deinited
   STATE the nodes refuse work        n/a   audiodynamics.Dynamics has no deinit() on this build - _component's walk finds nothing to call, so there is nothing to observe. See the evidence pack, section 11
   CAPS () and no transport read      pass  capabilities (), transport called 0 times
   MONO channel_count 1               pass  channel_count 1, peak +0.000 dB over the ceiling
   RATE lookahead 10 ms clamps        pass  220 samples at 22050 Hz
   ALLOC 200 blocks of output         pass  217600 bytes through the class, 217600 through the bare source (+0), render peak 8231 LSB

0 failing invariants
```

**circuitpython-effects** (`0 failing invariants`, last block):

```
22050 Hz
   WIRE ceiling 0 dB, gain 0          pass  0 of 16384 samples differ
   TAIL lookahead  0.0 ms             pass  tail 0 samples (declared 0), residual 0 LSB
   TAIL lookahead 10.0 ms             pass  tail 220 samples (declared 220), residual 0 LSB
   LEVEL ceiling   +0.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling   -6.0 dB            pass  worst deviation from the source 0 LSB
   LEVEL ceiling  -24.0 dB            pass  worst deviation from the source 0 LSB
   GAIN  0.0 dB into the ceiling      pass  measured +0.000 dB
   GAIN  6.0 dB into the ceiling      pass  measured +5.994 dB
   GAIN 12.0 dB into the ceiling      pass  measured +11.994 dB
   GAIN 24.0 dB into the ceiling      pass  measured +23.999 dB
   CLICK lookahead  0.0 ms            pass  reported 0, measured 0, floor(ms*fs/1000) 0
   CLICK lookahead  1.5 ms            pass  reported 33, measured 33, floor(ms*fs/1000) 33
   CLICK lookahead 10.0 ms            pass  reported 220, measured 220, floor(ms*fs/1000) 220
   STATE reset clears the ring        pass  primed 16423 LSB, after reset 0 LSB
   STATE the source is not owned      pass  2 nodes owned
   STATE deinit closes the surface    pass  output raises after deinit, and deinit twice is safe
   STATE the source still renders     pass  19999 LSB off the borrowed source after the class over it was deinited
   STATE the nodes refuse work        n/a   audiodynamics.Dynamics has no deinit() on this build - _component's walk finds nothing to call, so there is nothing to observe. See the evidence pack, section 11
   CAPS () and no transport read      pass  capabilities (), transport called 0 times
   MONO channel_count 1               pass  channel_count 1, peak +0.000 dB over the ceiling
   RATE lookahead 10 ms clamps        pass  220 samples at 22050 Hz
   ALLOC 200 blocks of output         pass  217600 bytes through the class, 217600 through the bare source (+0), render peak 8231 LSB

0 failing invariants
```

**One of these checks was rewritten because it could not fail.** The first form
of "the source still renders" read the *same* source the reset check had
already pulled past its burst, so it read 0 LSB on a healthy build and the
report was hardcoded green. It now takes its own source and a continuous tone,
and reads 20000 LSB off the borrowed source after the class over it was
deinited - a number that goes to zero if anything ever does reset or release
the borrowed source.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, per probe, per rate, per source block size, from the
committed probe corpus — `render_effect.py` verifies each probe against
`probes.json` before it renders and refuses a drifted one.

```
$ PYTHONPATH=lib .venv/bin/python tools/render_effect.py \
      Limiter <probe> <outdir> --rate <rate> --patch <n> [--block <n>]
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      -X heapsize=512M tools/render_effect.py ...
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=512M tools/render_effect.py ...
```

| Probe | Rate | Block | Patch | cpython | micropython | circuitpython-effects | latency | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|---|---|
| `chord` | 44100 | 256 | 0 | `4d20fe71` | `4d20fe71` | `4d20fe71` | 0 | *(board run)* | *(board run)* |
| `chord` | 44100 | 256 | 1 | `ec64bb01` | `ec64bb01` | `ec64bb01` | 65 | *(board run)* | *(board run)* |
| `chord` | 48000 | 256 | 0 | `7bd32675` | `7bd32675` | `7bd32675` | 0 | *(board run)* | *(board run)* |
| `chord` | 48000 | 256 | 1 | `11d367a5` | `11d367a5` | `11d367a5` | 71 | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | 0 | `1fe01e81` | `1fe01e81` | `1fe01e81` | 0 | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | 1 | `bfbd36f1` | `bfbd36f1` | `bfbd36f1` | 71 | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | 0 | `662782d1` | `662782d1` | `662782d1` | 0 | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | 1 | `0d542e81` | `0d542e81` | `0d542e81` | 71 | *(board run)* | *(board run)* |
| `tone_fs4` | 44100 | 256 | 0 | `2e870f35` | `2e870f35` | `2e870f35` | 0 | *(board run)* | *(board run)* |
| `tone_fs4` | 44100 | 256 | 1 | `5570b305` | `5570b305` | `5570b305` | 65 | *(board run)* | *(board run)* |
| `tone_fs4` | 48000 | 256 | 0 | `d0c11fc5` | `d0c11fc5` | `d0c11fc5` | 0 | *(board run)* | *(board run)* |
| `tone_fs4` | 48000 | 256 | 1 | `955eeff5` | `955eeff5` | `955eeff5` | 71 | *(board run)* | *(board run)* |

**Desktop agreement: yes.** All three interpreters render **byte-identical**
output on every probe, rate and patch above — sixteen renders, three
interpreters, no exceptions and therefore no cause to record.

**Board agreement:** *(board run — see §11.)*

**Block-size ladder.** `chord` at 48 kHz on patch 1, from 256-, 8192-, 16384-,
20000- and 32768-frame sources: **`11d367a5` in all five**. The class holds a
lookahead ring, so this is the ladder that would show a ring indexed off the
block rather than off the sample.

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
target `effect:Limiter`, on the ESP32-P4 (COM4) and the ESP32-S3 (COM49)
over `mpftp exec`. The figures are below; the method, the shared findings
and the two boards' identities are in
[`../effects-cost-table.md`](../effects-cost-table.md), “Phase 2 classes”.

Dossier budget: ESP32-P4 ≤ 6 % of one stereo block's deadline, ESP32-S3 ≤ 18 %
with true peak on; ≤ 4 % / ≤ 12 % with it off. Those are budgets, and the
dossier says so — the base figure behind them is flagged unsourced in
`Compressor.md`'s own audit.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | construction defaults, `audioeffects.create("Limiter", …)` | 1002.1 | 0.998 (0.685 marginal) | 5.34 | 3200 B | **no** — 12.8 % marginal, 18.7 % total, against ≤ 4 % |
| S3 | 0 | construction defaults, `audioeffects.create("Limiter", …)` | 577.3 | 1.732 (1.263 marginal) | 3.08 | 3232 B | **no** — 23.7 % marginal, 32.5 % total, against ≤ 12 % |

**How the figures were taken.** `tools/measure_effect_cost.py`, target
`effect:Limiter`, over `mpftp exec` on each board after a soft reset, with
`lib/audioeffects` (28 files, `mpftp cp … --verify`, 28 verified) on `/lib`
of both boards — neither firmware freezes the package in. 256-frame stereo
blocks at 48 kHz; 5.333 ms per block is real time. `ms/block` is the whole
chain, probe source and class together; the **marginal** in brackets is the
same run's control (the probe source alone, under the same heap) subtracted,
and it is the figure the budget verdict uses. RAM is `gc.mem_alloc()` growth
across construction, with the probe already standing. Applicable budget:
P4 ≤ 4 %, S3 ≤ 12 % (true peak off, which is the constructor default — `limiter.py:163`).

**Digest** (first 128 blocks, 683 ms of the tool's own integer probe):
`4169efd90ecf44dd` on the ESP32-P4 and `4169efd90ecf44dd` on the ESP32-S3 — **identical**.
The desktop digest for the same tool and target, taken this session on
`audiocomponents/.venv/bin/python`, is the **same value**.

It is also the bare probe's own digest (`4169efd90ecf44dd`): at construction
defaults (patch 0 `Safety Ceiling`) this class hands the probe back unchanged. The
CPU figure above is the built graph running — every node is pulled every
block — but **the digest is not a check on the audio**, and a board run at
a working patch is still owed.

**Owed: a `" - lean"` patch.** At 23.7 % of the deadline the class is over
its ESP32-S3 budget of ≤ 12 %, so the roadmap's class gate owes one. It is
recorded as owed; this runner does not invent one. Where the dossier says a
lean patch is not expected or not possible, that claim now has a
measurement against it and the lever has to be chosen by the class's own
session — a construction option, or a node ask.

**Not measured by this run:** the true-peak-on budget row. `true_peak` defaults to `False` (`lib/audioeffects/rebuilt/limiter.py:163`), so these figures are the true-peak-off case.
No I2S device was opened, so the `audiodev` pump and the I2S ring — the
stompbox latency seam of the vision's §9a — are in none of these numbers.
One run per class per board; repeatability was checked on the S3 only, on
three classes, three runs each (DynamicEQ and NoiseGate identical to the
millisecond, BandPass 0.808/0.801/0.801 ms).


**Lean patch: none shipped, on purpose.** The dossier's §6 settles it: patch 0
already has True Peak off and Lookahead at 0, which is every macro that costs
anything at its cheapest, so a `" - lean"` patch would be patch 0 under a second
name. If the board run puts patch 0 over the S3 budget the remedy is a
construction option that drops the catch stage — and that costs L2 and L3, so
it is a decision for the gate and not for this session.

**A desktop number, recorded as a desktop number and nothing more.** Two
`Dynamics` where the old class had one is the class's whole cost change. The
dossier's Appendix B.11 measured the base node on CPython at 0.043 µs per
stereo frame against a bare `RawSample` at 0.038; this class runs two of them.
That predicts roughly twice the node cost and says nothing about a board.

---

## 5. Latency

Reported `latency_samples` = **0 on the default patch**, and
`floor(lookahead_ms × rate / 1000)` wherever the Lookahead macro is put.

| Rate | Lookahead | Reported | Measured click | Δ | ms |
|---|---|---|---|---|---|
| 48000 | 0 ms | 0 | 0 | 0 | 0.000 |
| 48000 | 1.5 ms | 72 | 72 | 0 | 1.500 |
| 48000 | 10 ms | 480 | 480 | 0 | 10.000 |
| 44100 | 0 ms | 0 | 0 | 0 | 0.000 |
| 44100 | 1.5 ms | 66 | 66 | 0 | 1.497 |
| 44100 | 10 ms | 441 | 441 | 0 | 10.000 |
| 22050 | 10 ms | 220 | 220 | 0 | 9.977 |

Eighteen (rate, setting) pairs in the L4 run, plus every patch at all three
rates in `tests/test_cpython_effects_limiter.py::L4LatencyIsTheLookahead`. Δ is
zero in all of them.

Dossier latency budget: **zero on the default patch**. **Met.**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| Lookahead (macro 2) | **0 ms** | 0 samples | 72 at 1.5 ms, 480 at 10 ms (48 kHz) | yes — "spans **0 ms to 10 ms** (up to **480 samples** at 48 kHz)" |
| True Peak (macro 4) | **off** | 0 samples | **0 samples** — measured, click delay 0 with True Peak on and Lookahead 0 | yes — "True Peak adds no latency at all" |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
CLICK **red at both rates**, audio digest unchanged (`176dfba1` both sides).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Ceiling | UNIPOLAR | −24…0 dB | the output ceiling; at 0 dB the class is a wire |
| 1 | Gain | UNIPOLAR | 0…24 dB | drive into the ceiling — the "loudness" knob |
| 2 | Lookahead | UNIPOLAR | 0…10 ms | how far ahead the detector reads; the class's only latency |
| 3 | Release | UNIPOLAR | 5 ms…2 s, log | recovery after the peak; **L7's trade lives here** |
| 4 | True Peak | TOGGLE | off / on → `true_peak=2` | inter-sample peaks |
| 5 | Knee | UNIPOLAR | 0…12 dB | 0 is L6's brickwall; above zero, a soft limiter |

Six of the sixteen allowed. The dossier's §6 records the two the seed proposed
that are not here — Hold (no node reaches it) and Mix (a parallel dry path
walks peaks past the ceiling) — each with its reason.

| Patch | Name | Values | What it is for |
|---|---|---|---|
| 0 | Safety Ceiling | `(122, 0, 0, 72, 0, 0)` | the constructor's defaults on the grid: −0.94 dB, zero latency, nothing switched on |
| 1 | Catch The Peaks | `(122, 0, 19, 53, 127, 0)` | 1.50 ms of lookahead and the 4× detector, for transient material |
| 2 | Loud | `(125, 64, 38, 38, 127, 0)` | 12.1 dB into a −0.38 dB ceiling — the loudness setting |
| 3 | Soft Ceiling | `(116, 0, 0, 78, 0, 95)` | a 9 dB knee: limiting you hear arrive rather than land |
| 4 | Delivery Ceiling | `(122, 0, 25, 72, 127, 0)` | true peak on, 1.97 ms lookahead, for anything to be converted or encoded |

`patch_index` is 0 on a fresh instance, `None` after any macro move and the
patch's index after `program_change`: shown by
`tests/test_cpython_effects_limiter.py::TheSurface::test_patch_index_follows_the_contract`.

**`capabilities` = `()`.** The dossier's one-line reason: *a ceiling has no
tempo; the class does not read the transport.* Measured, not asserted: a
transport callable is passed in, 24000 frames are rendered, and it is called
**0 times**
(`TierOne::test_capabilities_is_empty_and_the_transport_is_never_read`, and the
`CAPS` row of the Tier 1 run on all three interpreters).

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiodynamics",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `shape` — `Dynamics(DYN_COMPRESS, ratio=1e6)` | `audiodynamics` | L6 (the knee and the brickwall slope), L1 (the 4× true-peak detector), L4 (the lookahead delay), L7 (the release) | `audiodynamics` is audioif's own; it is not a CircuitPython module (`audioif/docs/upstream-diff.md:661`). Nothing in the ported palette has an envelope follower with a gain computer behind it. |
| `catch` — `Dynamics(DYN_LIMIT, attack_ms=0)` | `audiodynamics` | L2, L3 — the whole overshoot answer | same module, and the zero-attack sample-exact behaviour is `DYN_LIMIT`'s gain computer specifically |

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.077s

OK
```

The class appears in that battery automatically — it walks `audioeffects.ALL`
and `rebuilt.known()` — so a tier claim here that `TIER` does not match is a
test failure, not a wrong sentence.

**What that test does not prove**, repeated because every pack must: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so no stock-tier class has
been shown rendering on a stock CircuitPython build of the ported C. That is a
gap in the method. It does not touch this class's own claim — `Limiter` is
audioif tier and needs the module either way — but the tier machinery it is
checked by carries it.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began (`26b80aa`), and
      §1 lists all seven as **demonstrated**.
- [x] Every Tier 1 invariant is green on CPython, MicroPython and
      circuitpython-effects at 48 kHz, 44.1 kHz and 22.05 kHz, with the
      `deinit()` row's *partial* on the two native builds explained in §2 and
      §11; every Tier 2 measurement names its rate.
- [x] Every demonstrated Tier 2 trait has a measurement shown red on a planted
      fault of the same kind.
- [x] Every demonstrated trait survived a refutation attempt, recorded with the
      argument and the answer — including one the refutation **changed**
      (L7's docstring number).
- [x] CPython, desktop MicroPython and circuitpython-effects render identical
      bytes on the probe material.
- [x] **Tier 3 cost is measured on the P4 and the S3.** Measured 2026-09-07 — §4.
      P4 12.8 % and S3 23.7 % of the deadline (marginal) against ≤ 4 % / ≤ 12 %: **over budget**. A `" - lean"` patch is owed.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz and
      44.1 kHz (and 22.05 kHz); the budget of zero on the default patch is met;
      both latency-adding options default off and are named in the docstring in
      milliseconds.
- [x] The class declares six macros and four named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass —
      §9. The old-surface trait tests were retired in the same commit.
- [x] The README catalogue row and the docstring describe the standout, the
      tier and the trade, in a musician's terms.
- [x] The class's code, its tests, the README row and the CHANGELOG line landed
      in `7399979`; this file is the commit after it, which is a deviation from
      "one commit" and is recorded in §11.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m flake8
(exit 0, no output)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_limiter
----------------------------------------------------------------------
Ran 33 tests in 36.528s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.077s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_metadata_contract
----------------------------------------------------------------------
Ran 7 tests in 0.025s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_rebuilt_registry
----------------------------------------------------------------------
Ran 15 tests in 0.013s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 7700
ok   Vibrato                  patch 0   peak 11000

46 classes, 83 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 83 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 83 patches, 0 failures

$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
----------------------------------------------------------------------
Ran 258 tests in 348.161s

OK (skipped=1)

$ mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify   # 28 files, 28 verified
$ mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
$ mpftp soft-reset -d COM4
$ mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:Limiter")'
ROW	effect:Limiter	1002.1	5.34	0.998	0.313	0.685	3200	4169efd90ecf44dd
$ mpftp exec -d COM49 'import measure_effect_cost as m; m.main("effect:Limiter")'   # the S3
ROW	effect:Limiter	577.3	3.08	1.732	0.469	1.263	3232	4169efd90ecf44dd
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

1. **Reported zero latency while delaying the audio.** Three of the old class's
   five patches set lookahead — up to 484 samples — against a hardcoded
   `LATENCY_SAMPLES = 0`. The rebuild reports `floor(ms × fs/1000)` from a
   property, matched to the click in eighteen (rate, setting) pairs (§5).
2. **Lookahead made the overshoot worse, and the docstring claimed the
   opposite.** The rebuild's catch stage holds the ceiling at every setting
   (L2, L3), and the docstring states the mechanism *and* the measured numbers
   for both builds.
3. **The true-peak docstring was stronger than the code.** The old class's
   `true_peak=True` selected a one-midpoint estimate that leaves 1.07 dB over
   the ceiling. The rebuild's toggle selects `true_peak=2`, the 4× detector,
   measured at 0.17 dB; the half-band estimate is deliberately not reachable
   from the surface, and the docstring quotes the number it actually delivers.
4. **Attack was hardcoded at 0.05 ms and was not a brickwall.** Both nodes run
   `attack_ms=0`, which is the node's genuinely instantaneous path.
5. **`reset()` reverts the surface** — **not a defect, and the rebuild keeps
   it.** The contract requires it: "`reset()` releases all instrument notes,
   clears component DSP history, and restores patch `0`"
   (`docs/audio-component-api.md:201-202`). The dossier called the contract a
   defect; the file wins.
6. **The node took the module's rate, not the source's.** `_component` takes
   the format from the source and the factory confirms it; `configure()` is
   never called.
7. **No gain into the ceiling.** The Gain macro, folded into the threshold and
   the makeup, measured within 0.006 dB at 0, 6, 12 and 24 dB (§2's `GAIN`
   rows).

---

## 11. What is not done

- **The board leg was taken on 2026-09-07, and the class is over its budget on both boards.**
  §4 carries the figures: P4 12.8 % and S3 23.7 % of the deadline (marginal)
  against ≤ 4 % / ≤ 12 %. Two things it does **not** close: the P4/S3 digest
  columns in §3, which want this file's own probes re-run on a board rather
  than the cost runner's, and the state the class was measured in —
  construction defaults, not the expensive patch §4 names. A `" - lean"` patch is owed.
- **`audiodynamics.Dynamics` has no `deinit()` on the native builds.**
  `hasattr(node, "deinit")` is `False` on `cmods/bin/micropython` and
  `cmods/bin/circuitpython-effects`, so `_component`'s deinit walk finds nothing
  to call there. The class's own surface still closes and the source still
  renders, both measured, but "every node the class built was released" is
  **unmeasured** on those two builds because there is nothing to observe.
  `audioecho.FeedbackDelay` is in the same position. This is an audioif node
  surface gap that affects every audioif-tier class, not just this one, and it
  needs an issue on `audioif` — **not filed, because this session cannot
  push**.
- **This file is a second commit, not the same one as the code.** The gate asks
  for the class, the evidence and the CHANGELOG line in one audiocomponents
  commit. The code, tests, README row and CHANGELOG line are in `7399979`; this
  file follows it, because it is written from runs against the committed code.
- **The stock-tier gap in §7** is the method's, and every pack repeats it: no
  stock CircuitPython interpreter exists in this workspace.
- **The dossier's Tier 3 budget percentages are budgets, not findings.** The
  cycle figure behind them is flagged unsourced by `Compressor.md`'s own audit,
  and nothing in this session measured it.
- **The lean-patch question is open until the board run.** §4 says what the
  remedy would be and why it is the gate's call.

Nothing else is outstanding at Stations A, B and C.

---

## Refutation record (2026-09-07)

An independent refuter, working from §1's seven **demonstrated** rows and the
dossier's §3 trait statements, re-ran every measurement with the kit
(`PYTHONPATH=lib .venv/bin/python`, helpers imported from
`tools/phase2_probes/limiter_traits.py`), varied the probe material and the
operating point *inside each trait's own terms*, re-planted each fault, and
looked for a reading that cannot go red. `tools/phase2_probes/limiter_traits.py`
reproduced §1 line for line first. Every number below is from a run in this
session.

- **L1 — REFUTED.** The trait's disconfirming clause is *"any probe reading
  more than +0.5 dB TP above the ceiling"*, and §1 measures exactly **one**
  probe. Run over the **committed corpus** (65 of the 66 probes at 2ch, the
  silent one excepted), ceiling −6 dBFS, True Peak **on**, release 60 ms, the
  kit's own `truepeak`: **2 probes RED at 48 kHz and 3 at 44.1 kHz.** Worst is
  `ramp_fs` — the kit's own WIRE probe — at **+2.22 dB TP**; then `dc_step`
  **+1.12 dB**, and `train10_1k_-6_peak` **+0.74 dB** at 44.1 kHz. Confirmed
  through the kit's own renderer, not a private harness:
  `tools/render_effect.py Limiter ramp_fs … --option ceiling_db=-6.0 --option
  true_peak=1 --option release_ms=60.0` → `sample peak −6.23 dBFS, true peak
  −4.05 dBTP, over +1.95 dB, RED`; `dc_step` → `−6.02 dBFS / −4.88 dBTP /
  +1.12 dB, RED`. Non-committed material agrees: a 1 ms full-scale burst reads
  **+1.15 dB** and white noise at −0.5 dBFS **+2.38 dB**, at both rates, with
  Lookahead at 0 **and** at 5 ms. The mechanism is the class's own §4: the
  **catch** stage is `DYN_LIMIT` with `attack_ms=0`, a *sample*-peak brickwall,
  and it runs **after** the true-peak detector — so it re-clamps the output to
  the sample ceiling (measured: exactly −6.00 dBFS on `ramp_fs`) and reinstates
  the inter-sample overshoot the shape stage had just made room for. The
  f_s/4 tone escapes this only because its true-peak reduction leaves it below
  the catch stage's threshold. *The author must answer:* either narrow L1 to
  the material it actually holds for (steady tones), or make the catch stage
  true-peak-aware so the promise survives transients and DC steps; and either
  way state which committed probes L1 was measured over, since "every probe"
  as written is false. Trait L1's grade should not stand at **demonstrated**.
- **L2 — not refuted.** The flatness survives every variation inside the
  trait's terms: burst into ceilings −6/−12/−24 dBFS at releases 5/60/500 ms,
  the full 0→10 ms sweep in 1 ms steps, at 48 000, 44 100 **and** 22 050 Hz —
  27 sweeps, worst reading **+0.000 dB** (**−0.002 dB** at the −24 dBFS
  ceiling), never a rise with lookahead. The "is it reading the ceiling?"
  suspicion was retested from a second angle: rendering with the latency trim
  **removed** (`latency_samples=0`) gives the same +0.000 dB at 0, 5 and 10 ms,
  so no overshoot is being cut off by the trim, and the −0.002 dB row proves
  the read is not pinned to the ceiling value. `NoCatchStage` reproduces
  +0.144 … +1.447 dB as §1 states. *The author must answer:* nothing.
- **L3 — not refuted.** Impulse at **every 0.5 ms step from 0.5 to 10 ms**
  (20 settings, not 5) at all three rates: worst **+0.000 dB** over the
  ceiling. *The author must answer:* nothing.
- **L4 — not refuted, with one wording correction owed.** Swept the Lookahead
  macro over its **full 0–127 grid, 128 positions × 3 rates = 384 cases**, each
  click-measured: **0 report mismatches and 0 click failures.** All **five
  patches** × 3 rates likewise agree to the sample (patch 1 → 71/71/71 at
  48 kHz, patch 2 → 143, patch 4 → 94). But §1's refutation answer — *"The
  class picks the number it reports … It does not"* — is wrong as written for
  the first clause: `_apply_lookahead` computes `samples = int(macro_value(…) *
  rate / 1000.0)` (`lib/audioeffects/rebuilt/limiter.py:250-252`, method at `:236`), which **is**
  `floor(ms × fs / 1000)` in Python, so `reported == floor()` is tautological.
  The non-tautological half is the *click*, and that half holds over all 384
  cases. *The author must answer:* correct that sentence to say the click is
  what carries L4.
- **L5 — not refuted.** Extended past construction: after `program_change(2)`
  (latency 143 / LA 2.992 ms / TP 1.00) a `program_change(0)` returns
  **latency 0, tail 0, Lookahead 0.000 ms, True Peak 0.00, patch 0** at all
  three rates, so the zero is the patch's and not just the constructor's.
  *The author must answer:* nothing.
- **L6 — REFUTED, and its slope clause is a measurement that cannot fail.**
  The trait's first clause is *"above the ceiling the static I/O curve's slope
  is ≤ 0.02 dB/dB over 24 dB"*, offered as the demonstration of **infinite
  ratio**. §1 cites it with **no planted fault of its own** — the only fault in
  the L6 block is the Knee-12 width. Planted one here (`_BRICKWALL_RATIO`
  swapped at build time, class otherwise untouched), 25-point curve, ceiling
  −24 dBFS:

  | build | slope | verdict |
  |---|---|---|
  | the class as shipped | −0.00000 dB/dB | green |
  | ratio 1e6 → **4**, catch stage in place | **−0.00000 dB/dB** | **green** |
  | ratio 1e6 → **1.5**, catch stage in place | **−0.00000 dB/dB** | **green** |
  | ratio 1e6 → **1.0** (no compression at all), catch stage in place | **−0.00000 dB/dB** | **green** |
  | ratio 4, catch stage **removed** (control) | +0.25007 dB/dB | RED |
  | ratio 1.0, catch stage **removed** (control) | +0.99996 dB/dB | RED |

  The two controls prove the fault is live — with the catch stage out, the
  reading tracks the ratio exactly. With it in, the reading is **−0.00000
  dB/dB for every ratio from 1.0 to 1e6**: it is measuring the catch stage's
  hard clip, not the shape stage's ratio, so the number §1 quotes for "infinite
  ratio" would be identical on a build that does no compression whatever.
  The knee half is weak too: the estimator is `max(bending levels) −
  min(bending levels)`, so a single bending point yields **0.000 dB by
  construction** — that is what Knee 0 produces (1 bending point) — and
  Knee 0.25, 0.50 and 0.75 all read the same quantized **0.500 dB** (3 points).
  On a 0.05 dB grid instead of the run's 0.25 dB, the **same** Knee-0 build
  reads **7.900 dB, RED**, from slopes of 0.93–0.94 that are peak-read noise;
  so the quoted 0.000 dB is a property of the grid the measurer picked, not of
  the class. *The author must answer:* give the slope clause a fault of its own
  that can turn it red — the ratio fault above only fires with the catch stage
  bypassed, so the honest form is to measure the **shape** stage's curve, not
  the class output; and replace the bending-band width with an estimator that
  cannot return 0.000 from one point and does not move 8 dB when the grid
  changes. Trait L6's grade should not stand at **demonstrated**.
- **L7 — not refuted, one clause unmeasured.** THD held at every operating
  point inside the trait's terms: 60 Hz at 12 dB into ceilings −12 and
  −24 dBFS, at 48 000 / 44 100 / 22 050 Hz, reads **0.708–0.711 %** against the
  1 % bar (the −36 and −48 dBFS "ceilings" clamp to the macro's −24 dBFS floor
  and are not a separate case). The Release fault reproduces: 5 ms → 11.994 %,
  30 ms → 3.134 %, 100 ms → 1.047 %. But the trait's **second** disconfirming
  clause — *"or a docstring that does not name the trade"* — has no automated
  check and no planted fault; it is true on inspection
  (`lib/audioeffects/rebuilt/limiter.py:41-47` and `:103-110` both name the
  5 ms end and the 12.0 % figure) but it is not demonstrated under this file's
  own rule. *The author must answer:* either add a check that reads the
  docstring and can be shown to fail, or move that clause out of the
  demonstrated column.

**Summary: 2 of 7 refuted (L1, L6); 5 survive (L2, L3, L4, L5, L7).**
L1 is a real gap in the promise, not only in the measurement — the class's
true-peak ceiling is broken by committed probe material. L6's slope reading is
a measurement that cannot fail and its knee reading is grid-dependent, so the
"infinite ratio, hard knee" claim is undemonstrated even though nothing here
shows it to be false.
