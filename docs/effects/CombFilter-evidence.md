# Evidence Pack — `CombFilter` (no historical standout — design grade)

Written from the runs of 2026-09-07 on branch `effects/p2-combfilter`. Every
figure below carries the command that produced it and the interpreter and
rate it ran on. Where a number came from a scratch driver rather than a
committed test, the driver's method is described in enough detail to rebuild
it, and the committed reproduction is named beside it.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `CombFilter` |
| Dossier | [`CombFilter.md`](CombFilter.md), traits frozen 2026-09-07 at `3b36ba4` (Station A), before any class code existed |
| Module | `lib/audioeffects/rebuilt/combfilter.py` |
| Base | `_component.Component` |
| Family / phase | EQ / Filter, roadmap Phase 2 |
| Standout | none — the naked textbook feedback comb, `y(n) = x(n) + g·y(n−M)` |
| Grade | design |
| Portability tier | **audioif** (`REQUIRES = ("audioecho", "audiobiquad")`) |
| Landed in commit | `69c5fe4` — the class, its tests, the README row and the CHANGELOG line together. This file, and the tail correction it forced in all four of those, landed in `cd27a4b`. |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3`. The `audioif/` tree here sits two commits ahead at `98ae4bf`, and `git diff --stat 2f6cbc3..98ae4bf` is `.flake8` and `apply_cp_patches.sh` only — no DSP, no binding. `delay_slew`, the one option this class needs from the Phase 1 palette work, is present **at the pin** (`git show 2f6cbc3:src/shared/audioif_feedback_delay.h:80`, `src/cpython/audioecho.py:98`). |
| Interpreters | `audiocomponents/.venv/bin/python` — Python 3.12.3 [GCC 13.3.0]; `cmods/bin/micropython` — MicroPython v1.28.0-dirty on 2026-09-07; `cmods/bin/circuitpython-effects` — CircuitPython 10.2.1-dirty on 2026-09-07 |
| Boards | **not run.** ESP32-P4 and ESP32-S3 columns are left for the board run — §4 and §11. |

**Dossier trait set frozen before the rebuild began: yes.** Station A
(commit `3b36ba4`) froze §3's Tier 2 table and §6's surface and settled all
three of §8's open questions; Station B (`69c5fe4`) wrote the class. The two
commits are in that order and the dossier's own header says so.

---

## 1. Traits

The dossier's own numbering. Nothing is added here that the dossier did not
fix.

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation |
|---|---|---|---|---|---|
| T1 | Peaks on the harmonic series of the tuned frequency, spaced exactly f, 20 Hz…4 kHz | **demonstrated** | TAPS on the impulse response, 48 kHz, cpython — the repeat comb's spacing reads the tuned frequency at every probe (§1a); RESPONSE at 200 Hz puts every peak on an integer multiple (§1b) | the rounder (`WholeSampleCombFilter`) moves the spacing off the request at 880/1760/3520 Hz → RED | *"a comb has peaks whatever you do; the test cannot fail."* Answered by the fault: the same measurement reads a **different** comb when the tuning is rounded, and the seed's own A2 shows the class it replaces reading 46.88 Hz for every request from 47 to 880 Hz. |
| T2 | Wet-only gain is `1/(1−g)` at the peaks and `1/(1+g)` at the nulls, within 0.2 dB at and below 2 kHz | **demonstrated** | RESPONSE, steady tones at 100…800 Hz around a 200 Hz comb, wet-only, g ∈ {0.3, 0.5, 0.8, 0.95}, 48 kHz, cpython (§1b) | `SquaredFeedbackCombFilter` runs the loop at g² → RED | *"the probe level was chosen to make it fit."* Answered in the driver: the probe is scaled as `20000·(1−g)·0.8` **because** a fixed level clips at high g — measured, a level-8000 probe reads a uniform −0.82 dB at every frequency including ones where the interpolator cannot be the cause, which is the rail, not the filter (dossier A13 §2). |
| T3 | Fractional tuning: every request in 20 Hz…4 kHz lands within 5 cents | **demonstrated** | first-repeat centroid, 48/44.1/22.05 kHz, cpython — 0.000 to 0.002 cents at every probe (dossier A13 §1, and `tests/test_cpython_effects_combfilter.py::TheCombTunesFractionally`) | the rounder is RED at 880/1760/3520 Hz **and green at 110 Hz**, which is the trait's own statement about where it has teeth | *"a centroid is not a pitch."* Answered: linear interpolation preserves a pulse's first moment, so the centroid *is* the tap the node was asked for; and the same class reads the same tuning through a second, independent measurement (TAPS's arrival detector, §1a). |
| T4 | Negative feedback puts the peaks on the odd half-multiples | **unmeasured — the class does not build it** | none. The composition that reaches it was reproduced at Station A (dossier A13 §5): the impulse response alternates sign at 480, 720, 960, 1200 … frames, which is `z^(−2M)/(1+g z^(−M))`. What it would take is either a signed-feedback option on the node, or seven nodes and three delay lines in this class — dossier §4 has the count and the reason. | n/a | n/a |
| T5 | At g = 0, Mix 1: total nulls at odd multiples of f/2, peaks exactly +6.02 dB at multiples of f | **demonstrated** | RESPONSE at 500/1000/1500/2000/2500/3000 Hz around a 1 kHz comb, 48 kHz, cpython (§1c) | `NoUnitySnapCombFilter` — the Mix snap removed, so grid "Mix 1" is 1.0079 and the dry leg 0.9921 → the null fills in to well above −60 dB, RED | *"the null is total because the arithmetic is exact, not because the class is right."* That is the point of the fault: the same arithmetic one grid step away is **not** exact, and the class's snap is what keeps it. |
| T6 | The tuning knob is click-free (restated: no boundary step above the same render's off-boundary floor) | **demonstrated** | second difference at the block boundaries against the 99.9th percentile off them, 100 Hz → 1 kHz over one second, 48 kHz, cpython (dossier A13 §4 and `tests/…::TheTuningKnobIsClickFree`) | `NoGlideCombFilter` — `delay_slew` forced to 0 → RED, +5.5 dB above the floor | *"the estimator's floor moves with the slew, so it can hide the step."* Answered by the zero-step control, which reads its own floor at −31.8/−31.0, and by the fault, which is red **on the same estimator** at the same setting. |

**Characters:** none. A comb has one behaviour (dossier §3).

**Refutation pass.** Run by this session, 2026-09-07, against each row above
before the verdict was written. What it went after: whether any of the five
demonstrated rows could pass on a class that was not doing the thing. Two
survived only after their measurement was changed — T2's probe level (a
clipping render read as a filter error) and T5's probe frequency (a 1 kHz
tone cannot show a 500 Hz null). Neither change moved the trait; both moved
the measurement onto something that can fail.

---

### 1a. The tuning — first-repeat centroid, 20 Hz to 4 kHz

The impulse response's first repeat, as an amplitude-weighted centroid over
the seven samples around the ideal tap. Linear interpolation preserves a
pulse's first moment, so the centroid *is* the tap the node was asked for,
fraction and all. Feedback 0, Mix 2, 48 kHz, cpython:

```
  f0=   20.0  ideal 2400.0000  centroid 2400.0000   +0.000 cents
  f0=   55.0  ideal  872.7273  centroid  872.7273   +0.000 cents
  f0=  110.0  ideal  436.3636  centroid  436.3636   +0.000 cents
  f0=  440.0  ideal  109.0909  centroid  109.0909   +0.000 cents
  f0=  880.0  ideal   54.5455  centroid   54.5455   +0.000 cents
  f0= 1760.0  ideal   27.2727  centroid   27.2727   -0.001 cents
  f0= 3520.0  ideal   13.6364  centroid   13.6364   +0.002 cents
  f0= 4000.0  ideal   12.0000  centroid   12.0000   +0.000 cents
```

Against a 5-cent bar: the worst reading is **0.002 cents**, three orders of
magnitude inside it. The same measurement at 44.1 kHz and 22.05 kHz is in
`tests/test_cpython_effects_combfilter.py::TheClassIsRateHonest`.

The fault is the whole point of this row. `WholeSampleCombFilter` rounds the
requested delay to the nearest whole sample and changes nothing else; it goes
**red at 880, 1760 and 3520 Hz** and **green at 110 Hz** — which is the
trait's own statement about where a 5-cent bar can discriminate, turned into
two assertions.

**The kit's `taps()` is the second, independent reading of the same thing**
— the smoothed-energy arrival detector rather than the centroid — and it
agrees. Impulse in, Feedback 0.7, Mix 2, 48 kHz, cpython, bar 0.5 ms:

```
      55.0 Hz  first tap  18.16667 ms  asked  18.18182  taps  12  pass
     110.0 Hz  first tap   9.08333 ms  asked   9.09091  taps  12  pass
     440.0 Hz  first tap   2.27083 ms  asked   2.27273  taps  12  pass
     880.0 Hz  first tap   1.12500 ms  asked   1.13636  taps  12  pass
    1760.0 Hz  first tap   0.56250 ms  asked   0.56818  taps  12  pass
    3520.0 Hz  first tap   0.27083 ms  asked   0.28409  taps  12  pass
```

Twelve arrivals at every tuning, which is **T1's other half**: the repeats
are evenly spaced, so the resonances are on the harmonic series of the
tuning. The first-tap readings are 0.2 to 0.6 samples short of the request —
that is the detector's own resolution on a smoothed energy envelope, not the
tuning, and it is why the 5-cent claim is made from the centroid: the same
renders read 0.002 cents there.

**`taps(..., spacing=True)` was not usable and that is the kit's problem,
not this class's.** `comb_spacing_hz` autocorrelates the magnitude spectrum
with `np.correlate(m, m, mode="full")`
(`tools/effect_measurements.py:1715`), which is a direct O(n²) convolution;
at the function's own default `pad_seconds=2.0` and 48 kHz that array is
48 001 points, and the call did not return in the minutes it was given.
Shrinking the pad is not the workaround: at 0.05, 0.10 and 0.20 seconds it
returns in 0.04 s and reads **−0.647 Hz**, a negative spacing, on a render
whose spacing is 440. Recorded in §11 as a kit finding.

### 1b. RESPONSE — the peak and null law, and every peak on a multiple

`effect_measurements.response()` over steady tones at 100, 200, 300, 400,
500, 600, 700 and 800 Hz, around a comb tuned to **200 Hz** (48 000/200 =
240.000 frames, so the tap is exact and the interpolator cannot be a
confound), wet-only through the class's own Mix macro at 127, 48 kHz,
cpython. The probe level is `20000·(1−g)·0.8` and the render is
`2·g` seconds plus a quarter second, so the loop is settled and the peak is
inside int16 at every g. Peaks are the readings at 200/400/600/800 Hz; nulls
at 100/300/500/700.

```
   g=0.30  peaks [3.1, 3.1, 3.1, 3.1]           ideal  +3.10   worst err +0.00
           nulls [-2.28, -2.28, -2.28, -2.28]   ideal  -2.28   worst err +0.00
   g=0.50  peaks [6.02, 6.02, 6.02, 6.02]       ideal  +6.02   worst err +0.00
           nulls [-3.52, -3.52, -3.52, -3.52]   ideal  -3.52   worst err +0.00
   g=0.80  peaks [13.98, 13.98, 13.98, 13.98]   ideal +13.98   worst err -0.00
           nulls [-5.11, -5.11, -5.11, -5.11]   ideal  -5.11   worst err -0.00
   g=0.95  peaks [26.01, 26.01, 26.01, 26.01]   ideal +26.02   worst err -0.01
           nulls [-5.8, -5.8, -5.8, -5.8]       ideal  -5.80   worst err +0.00
```

That single block carries **T2** (the heights, to 0.01 dB at the worst, bar
0.2) and half of **T1** (the peaks are on 200, 400, 600 and 800 and the nulls
on the odd half-multiples between them, at every g — four peaks reading one
number and four nulls reading another is what "on the harmonic series"
means when the grid is the harmonic series).

**Above 2 kHz T2 is a curve, not a tolerance**, which is what Station A froze
it as. Same measurement, g = 0.8, one tuning per row (dossier A13 §2): 0.00 dB
error at 55, 110, 440, 1000, 2000, 3000, 4000 and 6000 Hz; −0.07 at 880,
−0.23 at 1760, −0.37 at 2500, −1.02 at 3520, −2.06 at 5000. Every exact row
is a tuning where `F_s/f` is a whole number of frames, and every row that
sags is one where it is not.

### 1c. RESPONSE — the feedforward comb at Feedback 0

Same function, comb tuned to 1 kHz, Feedback 0, **Mix macro 64** — the grid
value patch 0 carries, which is where the class's unity snap is doing its
work:

```
     500.0 Hz    -240.00 dB      (bit-exact zero)
    1000.0 Hz      +6.02 dB
    1500.0 Hz    -240.00 dB      (bit-exact zero)
    2000.0 Hz      +6.02 dB
    2500.0 Hz    -165.67 dB
    3000.0 Hz      +6.02 dB
```

**T5**, to the letter: the nulls are total — two of them are the digest of
silence and the third is 105 dB below the −60 the trait asks for — and the
peaks are +6.02 dB, not +6.0 and not +6.05. The planted fault is one grid
step of Mix away.

---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`. Every cell below is one run of a kit
measurement over a render the interpreter in that column produced; the
renders are the Station C sweep in §9. **Stereo unless the row says
otherwise.**

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC — **at patch 0; §2a is the whole answer** | TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `mix` 0 is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node silent and stateless, the source untouched | STATE | pass | n/r | n/r | n/r | n/r | n/r | n/r | n/r | n/r |
| `deinit()` releases every node and leaves the source rendering | STATE | pass | n/r | n/r | n/r | n/r | n/r | n/r | n/r | n/r |
| `capabilities` names exactly the optional behaviours honoured | STATE | pass | n/r | n/r | n/r | n/r | n/r | n/r | n/r | n/r |
| Pulling `output` allocates nothing | STATE | pass | n/r | n/r | n/r | n/r | n/r | n/r | n/r | n/r |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Every invariant also holds at `channel_count` 1 | WIRE (1ch) | pass | pass | pass | pass | pass | pass | pass | pass | pass |

`n/r` = **not run on that interpreter**, not "n/a": STATE drives the class
between renders (`effect_measurements.py:19-21` says so), and the kit's
`state()` is CPython-with-numpy. The three-interpreter leg that *is* run for
this class is the digest table in §3, which is byte-for-byte identical on all
three — a class whose `reset()` behaved differently under MicroPython would
have to render differently to do it. That is weaker than running STATE
there, and it is stated as weaker. §11 carries it.

**The numbers behind the passes.** WIRE reports **0 of 47 104 samples
differing** at 48 kHz stereo and 0 at every other rate and channel count, and
the render's own FNV equals the probe's (`aef0fa61` at 48 k/2ch,
`7bbcbf39` 48 k/1ch, `aa6aeabd` 44.1 k/2ch, `9fa9cd6d` 44.1 k/1ch,
`4a36acb1` 22.05 k/2ch, `215e1a09` 22.05 k/1ch) on all three interpreters.
LEVEL reads **[0.0, 0.0] dB** RMS and peak on both channels everywhere.
CLICK reads **measured [0.0, 0.0] samples against a reported 0, error 0.0**
everywhere. TAIL at patch 0 (Feedback 0.703, Mix 1) reads **residual 0 LSB**
with a measured tail of **6242 samples at 48 kHz, 5430 at 44.1 k, 1914 at
22.05 k** — the same three numbers on all three interpreters.

**The tail invariant above Feedback 0.5 is a different answer**, and it is
the one thing in this block that is not simply green: see §2a.

### 2a. The tail: which settings reach exact zero, and which park

The Tier 1 row above is green because it is read at **patch 0**, and patch 0
reaches exact zero. That is true and it is not the whole answer, so here is
the whole answer.

`effect_measurements.tail()` over an eight-second render, 0.2 s of 1 kHz
burst at −6 dBFS into silence, the class at **438.3 Hz**, Mix 1, 48 kHz,
cpython:

```
   feedback 0.45  residual 0 LSB  tail  1414 samples  pass
   feedback 0.70  residual 0 LSB  tail  6234 samples  pass
   feedback 0.80  residual 0 LSB  tail  7439 samples  pass
   feedback 0.90  residual 0 LSB  tail 10944 samples  pass
   feedback 0.95  residual 0 LSB  tail 17733 samples  pass
```

Every one green — and that is *not* a general result. Ten-second renders
through the class, the largest |y| in the last second and the last non-zero
frame (480 000 = still running when the render ended):

```
  tuned    burst    g      residue   last non-zero   frac of F_s/f
   440.0    440.0  0.70      1 LSB   479999          0.09
   440.0   1000.0  0.70      1 LSB   479999
   440.0    440.0  0.95      8 LSB   479999
   440.0   1000.0  0.95      8 LSB   479999
   438.3   1000.0  0.70      0 LSB    17881          0.51
   438.3    438.3  0.70      0 LSB    19904
   438.3   1000.0  0.95      0 LSB    29380
   438.3    438.3  0.95      0 LSB    34360
   220.0    220.0  0.95      6 LSB   479999          0.18
   110.0    110.0  0.70      0 LSB   114465          0.36
   110.0    110.0  0.95      3 LSB   479999
  1000.0   1000.0  0.70      1 LSB   479999          0.00
  1000.0   1000.0  0.95     10 LSB   479999
  3520.0   3520.0  0.70      0 LSB    12078          0.64
  3520.0   3520.0  0.95      3 LSB   479999
```

**The burst's frequency does not matter. The tuning's does.** `to_s16`
rounds (`audioif_feedback_delay.c:308-316`), so every |c| ≤ 0.5/(1−g) is a
fixed point of `line ← to_s16(g·line)`; whether the loop can sit on one
depends on how exactly it reads its own line. Near a whole sample the read is
nearly exact and a lone LSB survives its round trip; near half a sample the
interpolator averages it with a zero neighbour and rounds it away.
`floor(0.5/(1−g))` is hit **exactly** at 1 kHz, where 48 000/f is 48.000
frames, and is an upper bound everywhere else.

So: **the invariant holds below Feedback 0.5 everywhere, and above it holds
or fails by the tuning.** The class declares `TAIL_SAMPLES = None`, the
docstring carries both ends, and the two committed tests assert both
(`…::TheTailIsBoundedRatherThanZero::test_a_whole_sample_tuning_parks_inside_the_closed_form_bound`
and `…::test_a_half_sample_tuning_still_reaches_exact_zero`). The first
reading of this, at Station A, said only that it parks — that was measured on
one tuning and stated as though it were the class. It is corrected here and
in the dossier.

**STATE, in full**, since the table above only says "pass":

```
   alloc_growth_bytes               -204704      (200 pulls, bar 8192)
   alloc_last_fnv1a                 7fd14c4d     (not the digest of silence)
   capabilities                     []
   live_nodes_after_deinit          []
   nodes                            ['_trim', '_comb']
   probe_fnv1a                      a9a1ac89
   reset_residual_lsb               0
   resumed                          True
   resumed_fnv1a                    b9256875
   tempo_sync_observed              None         (no transport digests given)
   -> pass
```

`tempo_sync_observed` is `None` because the two transport digests were not
handed to the measurement; the class declares `capabilities = ()` and does
not read `self._transport()` at all, which §6 shows by grep. That is a
weaker check than the kit can make, and §11 carries it.

### 2b. Mono

The dossier's §4 states that a mono source gets the identical comb: the node
runs one lane and forces the cross-feed term to zero. Measured here as the
WIRE row's `channel_count` 1 leg — byte-identical at all three rates on all
three interpreters — and as the tuning at `channel_count` 1
(`tests/test_cpython_effects_combfilter.py::MonoIsTheSameComb`, first-repeat
centroid within 5 cents of 880 Hz).

### 2c. Planted faults for this block

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | `LeakyWireCombFilter` — the dry path × 32767/32768 | 0 differing samples | differs (`…::TheBypassIsAWire::test_one_lsb_off_the_dry_path_is_red`) |
| STATE / reset | `UnresetCombFilter` — the comb owned with `reset=False`, i.e. a delay line left full | residue 0 after `reset()` | residue > 0 (`…::ResetEmptiesTheLine::test_a_line_left_full_is_red`) |
| CLICK | `ShortLatencyCombFilter` — `LATENCY_SAMPLES = 256`, DSP untouched | reported 0 = measured 0 | reported ≠ measured (`…::TheLatencyIsZero::test_a_class_that_reports_256_short_is_red`) |
| TAIL | the Feedback sweep in §2a is its own fault: the same measurement is green at 0.45 and red above 0.5, on one class, with one knob moved | — | — |

The kit's own twenty faults are `tests/test_effect_kit.py`, which runs in the
suite quoted in §9.

**Nodes this class enumerates, in build order:** `_trim`
(`audiobiquad.Biquad`, HIGH_SHELF at 5 Hz), `_comb`
(`audioecho.FeedbackDelay`, 60 ms line). `reset()` and `deinit()` walk that
list tail-first, so the comb's line is cleared before the trim's state.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, per probe, per rate, at the renderer's 256-frame
source block. `sum(data)` is never the comparison.

Command (one row; §9 has the sweep):

```
PYTHONPATH=lib .venv/bin/python tools/render_effect.py CombFilter chord <dir> --rate 48000 --patch 0
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 256 | `0c3dce0d` | `0c3dce0d` | `0c3dce0d` | *(board run)* | *(board run)* |
| `chord` | 44100 | 256 | `95324dcd` | `95324dcd` | `95324dcd` | *(board run)* | *(board run)* |
| `chord` | 22050 | 256 | `b9f32595` | `b9f32595` | `b9f32595` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | `783dcd7d` | `783dcd7d` | `783dcd7d` | *(board run)* | *(board run)* |
| `noise_det` | 44100 | 256 | `c8c5b0c1` | `c8c5b0c1` | `c8c5b0c1` | *(board run)* | *(board run)* |
| `noise_det` | 22050 | 256 | `946f0d4d` | `946f0d4d` | `946f0d4d` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | `19757269` | `19757269` | `19757269` | *(board run)* | *(board run)* |
| `sweep_log` | 44100 | 256 | `a87be715` | `a87be715` | `a87be715` | *(board run)* | *(board run)* |
| `sweep_log` | 22050 | 256 | `ab4687e1` | `ab4687e1` | `ab4687e1` | *(board run)* | *(board run)* |

**Desktop agreement: yes.** All three interpreters render identical bytes on
every probe at every rate — nine probes × three interpreters, no exception.
That is a stronger claim here than for most classes: the loop is recursive
and runs in `float`, so a one-ulp disagreement would be fed back and
amplified rather than staying one ulp (`upstream-diff.md`, `audioecho`'s
own parity note).

**Board agreement:** not taken. The P4 and S3 columns are the board run's,
and §11 says so.

---

## 4. Tier 3 — cost on the boards

**Not run.** No board leg was taken in this session: `tools/measure_effect_cost.py`
drives a board over a serial port and no P4 or S3 was attached to this run.
The table below is left empty on purpose rather than filled from the desktop
figure, which would be a different machine's number wearing a board's label.

Dossier budget: **ESP32-P4 ≤ 2 %** of one stereo block's real-time deadline,
**ESP32-S3 ≤ 7 %**. Lean patch expected: **no**.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | | | | | | |
| S3 | 0 | | | | | | |

**Desktop anchor, for the board run to be read against** (not a board
figure). Four seconds of 48 kHz stereo pulled block by block through the same
one-voice source pump, best of three, so the pump's own cost subtracts out:

```
  source alone                    1316.4 ns/frame
  + FeedbackDelay                 1361.1 ns/frame   (+44.7)
  + FeedbackDelay + trim biquad   1415.2 ns/frame   (+98.8 over the source)
  real time per stereo frame at 48 kHz = 20833.3 ns   ->  0.47 %
```

**The expensive path is reachable and is what the board run must use**: patch
0 is Feedback 0.703 at Mix 1 with the tone filter *off*, which is the loop
running with no branch skipped. Patch 3 (**Dark Resonator**) additionally
turns the in-loop damping on, which is the only optional per-sample branch
this class has (`audioif_feedback_delay.c:455-459`); the board run should
take both.

---

## 5. Latency

Reported `latency_samples` = **0**. Measured click delay against the dry
path, per channel, at patch 0, on the committed `click_stereo` probe:

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | [0.0, 0.0] | 0.0 | 0.000 |
| 44100 | 0 | [0.0, 0.0] | 0.0 | 0.000 |
| 22050 | 0 | [0.0, 0.0] | 0.0 | 0.000 |

Identical on all three interpreters (§2). Dossier latency budget: **0
samples. Met: yes.**

**Every latency-adding option, each defaulting off or to its shortest:**
there are none. Every macro this class has changes what the loop does to a
sample it has already been given; none of them holds audio back.

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none)* | — | 0 | — | the docstring says so in as many words |

The one number the docstring does state in milliseconds is **not** latency:
at Mix 2 there is no dry path, so the first sound arrives one line-length
late — 0.25 ms at 4 kHz, 50 ms at 20 Hz. That is the delay the user asked for
by tuning it, which vision §9a distinguishes from latency, and the class's
own CLICK reading at patch 0 (Mix 1, dry present) is 0.

Planted fault: `ShortLatencyCombFilter` reports 256 samples with the DSP
untouched → the reported/measured comparison goes red at both rates while the
audio digest is unchanged (`tests/test_cpython_effects_combfilter.py::TheLatencyIsZero::test_a_class_that_reports_256_short_is_red`).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 Hz … 4 kHz, log | the tuning knob |
| 1 | Feedback | UNIPOLAR | 0 … 0.95 | resonance / regeneration |
| 2 | Mix | UNIPOLAR | 0 … 2 (0 wire, 1 dry+wet, 2 the filter alone) | the blend knob |
| 3 | Tone | UNIPOLAR | 500 Hz … 24 kHz log; the top of the travel is off | the darkening a resonator's own losses give it |
| 4 | Trim | BIPOLAR | −18 … +18 dB, **in front of the comb** | input headroom |
| 5 | Glide | UNIPOLAR | 0 … 1 delay-seconds per second, default 0.05 | how fast the comb walks to a new pitch |

Six of the sixteen the contract allows.

| Patch | Name | What it is for |
|---|---|---|
| 0 | Metallic | the constructor's defaults on the 0-127 grid — 440 Hz, 0.7, Mix 1, tone off |
| 1 | Ringing Pitch | 220 Hz at 0.92, a note you can play; −3 dB of headroom |
| 2 | Soft Ripple | 110 Hz at 0.3, half wet — the comb as a colour, not a pitch |
| 3 | Dark Resonator | 150 Hz at 0.85 with the in-loop tone at 2 kHz, −6 dB — the ring goes dull as it dies |
| 4 | Single Slap | 55 Hz at Feedback 0 — the feedforward comb of T5, one reflection |
| 5 | Filter Only | 1 kHz at 0.8, Mix 2 — no dry at all, which is where T2's law is read |

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change`: `_component.Component.set_macro` and
`program_change` do that for every class, and
`tests/test_cpython_effects_combfilter.py::TheSurface::test_every_patch_is_reachable_and_moves_the_comb`
holds this class's six.

**`capabilities` = `()`.** The dossier's one-line reason, quoted: *"a comb's
delay is a pitch, not a rhythm — 1/f seconds, where f is the note you hear —
so syncing it to the transport would be meaningless"*. The class never reads
`self._transport()`; `grep -n "_transport" lib/audioeffects/rebuilt/combfilter.py`
returns nothing.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audioecho", "audiobiquad")`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `FeedbackDelay` | `audioecho` | T1, T2, T3, T5, T6 — the whole comb | `audiodelays.Echo` quantises its line to whole samples and floors it at the node's own buffer length: measured, every request from 47 to 880 Hz comes out as one 46.88 Hz comb, and the floor tracks `buffer_size` exactly (dossier A2, A12). Even a 512-byte buffer only reaches 187.5 Hz, which is short of most of the class's span. And `delay_slew`, which T6 rests on, exists only here. |
| `Biquad` (HIGH_SHELF) | `audiobiquad` | the Trim, and through it the headroom the high-Feedback patches need | `synthio.Biquad` through `audiofilters.Filter` is the ported route, and it parks on held DC at low corners (audioif#23, `LowPass` A3/A14) — a subsonic shelf is exactly that corner. |

Test:

```
PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
```

Result:

```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.004s

OK
```

The class enters that battery automatically — it walks `audioeffects.ALL`
and `rebuilt.known()` — so a tier claim here that `TIER` does not match is a
test failure, not a wrong sentence.

**What that test does not prove**, and every pack repeats it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class has
not been shown rendering on a stock CircuitPython build of the ported C.
That is a gap in the method, not in this class — and it does not bear on
this one's claim, which is the opposite: that it needs audioif and says so.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed or unmeasured. **T4 is
      `unmeasured` with its reason and what it would take.**
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on the patched CircuitPython build —
      **except that STATE runs on CPython only** (§2, `n/r`), and **except
      the tail above Feedback 0.5** (§2a), which is a stated disconfirmation
      with a measured bound, not a pass. Every Tier 2 measurement names its
      rate.
- [x] Every demonstrated Tier 2 trait has a measurement, and that
      measurement was shown red on a planted fault of the same kind (§1).
- [x] Every demonstrated trait survived a refutation attempt, recorded with
      the argument and the answer (§1).
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material, and so does the patched CircuitPython build (§3). **The P4
      and S3 digests are not taken.**
- [ ] Tier 3 cost measured on the P4 and the S3 — **not run** (§4, §11).
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz (and 22.05 kHz); the dossier's budget of 0 is met; there
      is no latency-adding option to default off, and the docstring says so.
- [x] The class declares six macros and five named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass
      (§9).
- [x] The README catalogue row and the docstring describe the standout, the
      tier and the cost in a musician's terms, and both name the two things
      the class does not do.
- [x] The class's code, its tests, the README row and the CHANGELOG line
      landed together in `69c5fe4`; this file lands in the Station C commit
      named in §0.

Two boxes are unticked and both are the board run.

---

## 9. Commands, verbatim

Run from `/home/brad/gh/pydevices/ac-wt-combfilter`.

```
$ .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.004s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_combfilter
.........................
----------------------------------------------------------------------
Ran 25 tests in 7.876s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
ok   Tremolo                  patch 0   peak 8319
ok   Vibrato                  patch 0   peak 11000

46 classes, 88 patches, 0 failures
```

**The Station C render sweep**, which every cell in §2 and §3 is read from —
nine probe/setting combinations × three rates × three interpreters, 81
renders:

```
for who in cp mp cpy; do for rate in 48000 44100 22050; do
  render CombFilter ramp_fs       --rate $rate --macro 2=0        # WIRE
  render CombFilter ramp_fs       --rate $rate --channels 1 --macro 2=0
  render CombFilter burst_silence --rate $rate --patch 0          # TAIL
  render CombFilter click_stereo  --rate $rate --patch 0          # CLICK wet
  render CombFilter click_stereo  --rate $rate --macro 2=0        # CLICK dry
  render CombFilter noise_det     --rate $rate --macro 2=0        # LEVEL
  render CombFilter chord         --rate $rate --patch 0          # DIGEST
  render CombFilter noise_det     --rate $rate --patch 0          # DIGEST
  render CombFilter sweep_log     --rate $rate --patch 0          # DIGEST
done; done
```

where `render` is `tools/render_effect.py` under

```
PYTHONPATH=lib .venv/bin/python                       # cp
MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython      # mp
MICROPYPATH=... ../cmods/bin/circuitpython-effects -X heapsize=256M    # cpy
```

The analysis is CPython-with-numpy over those WAVs, calling
`tools/effect_measurements.py`'s `wire()`, `level()`, `tail()`, `click()`
and the `Render.digest`; the driver is a scratch script, and every number it
printed is quoted above rather than summarised.

```
$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 252 tests in 25.469s

OK (skipped=1)
```

252 = the foundation's 227 plus this class's 25. The first attempt at this
run was killed by its own `timeout 1200` with 193 tests done: this machine
was carrying fifteen other class-builder worktrees at a load average of 65
while it ran, and the suite that takes 25 s idle took over twenty minutes.
The number above is from a run that finished.

```
$ PYTHONPATH=lib .venv/bin/python tools/measure_effect_cost.py --subject CombFilter --port <COMn>
not run - no board attached to this session (§4, §11)
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

| The old defect | What the rebuild does |
|---|---|
| **The class does not tune. At all.** `delay_ms = 1000/frequency` into `audiodelays.Echo`, whose line floors at the node's buffer length: 47, 110, 220, 440 and 880 Hz all measured as one 46.88 Hz comb. | `audioecho.FeedbackDelay`, whose line is read with per-sample linear interpolation. Measured: the first-repeat centroid lands on the request to **0.002 cents** from 20 Hz to 4 kHz. |
| Even without the floor, the tuning would quantise — 45 cents at 4 kHz, 111 at 5 kHz. | Fractional taps. T3 is demonstrated, and its planted fault is exactly a rounder. |
| **No guard on `feedback`.** It went straight to `decay`, so 1.0 was a non-decaying ring the docstring did not mention. | The Feedback macro's span stops at **0.95**, inside the node's own 0.99 clamp, and the docstring names the peak gain it buys (+26 dB) and the residue it leaves. |
| **No surface at all** — `MACRO_LABELS = ()`, three constructor-only arguments and no setter for any of them. | Six macros, six patches, every one reachable and moving the sound (`…::TheSurface`). |
| **`max_delay_ms=50` hard-coded**, so the class silently clamped below 20 Hz. | `MAX_DELAY_MS = 60.0`, chosen so the node's one-frame headroom does not bite at the bottom of the span: a 50 ms line tunes 20 Hz to 20.02 Hz, a 60 ms one to 20.00. |
| **No tail declared** for a class whose whole point is a feedback loop. | `TAIL_SAMPLES = None`, with the reason and the measured residue per feedback setting in the docstring and in §2a — rather than a number that would be wrong. |
| **`reset()` and `deinit()` reach one node each**, which happened to be enough for a one-node class. | Both walk `self._own()`'s list, tail first. §2c's fault is a line left full, and it is red. |

---

## 11. What is not done

- **The board run.** No ESP32-P4 or ESP32-S3 leg was taken: Tier 3 cost (§4)
  is empty and the P4/S3 digest columns in §3 are empty. The class gate is
  not through until they are filled.
- **STATE runs on CPython only** (§2). `reset()`, `deinit()`, the
  `capabilities` clause and the allocation check are not exercised under
  desktop MicroPython or the patched CircuitPython. What stands in for them
  is the digest table, which is weaker, and this line says so.
- **T4 is unmeasured.** The negative comb is not built (dossier §4), so
  there is no class measurement to take. The composition that reaches it was
  reproduced (dossier A13 §5) but is not this class.
- **The tail invariant is disconfirmed above Feedback 0.5** (§2a). It is
  bounded and stated, not fixed: fixing it needs either a float line or
  truncation toward zero in `to_s16`, both of which are audioif changes on a
  frozen pin. **An issue should be filed against audioif** for the
  `FeedbackDelay` limit cycle — this session did not file it, and that is a
  gap, not a decision.
- **A program change into a ringing line can reach the rail** (the class
  docstring measures it: patches 1, 3 and 4 peak at 32 768 in the library
  smoke's own six-patch sequence, where each of those patches on a fresh
  instance peaks between 8 210 and 18 925). It is what a feedback line is,
  and no reset is issued between patches by design — but nobody has decided
  whether the library wants that, and no issue is filed.
- **The kit's `comb_spacing_hz` is unusable at its own default.**
  `tools/effect_measurements.py:1715` autocorrelates a 48 001-point spectrum
  with a direct O(n²) `np.correlate`, so `taps(spacing=True)` does not return
  in a per-class run at 48 kHz; and at the small pads that do return it
  reads a negative spacing. T1's spacing leg is carried by the twelve evenly
  spaced arrivals `taps()` does report and by the RESPONSE grid instead. No
  issue is filed against the kit; it should be.
- **The Tier 2 measurements in §1a–§1c come from a scratch driver**, not from
  a committed tool. The committed reproduction of the same traits is
  `tests/test_cpython_effects_combfilter.py`, which is narrower: it checks
  the criterion, not the whole curve.
