# Effects Dossier — `LowPass` (no historical standout — design grade)

**Class:** `lib/audioeffects/rebuilt/lowpass.py`. The old
`lib/audioeffects/eq.py` implementation is read once, for §7, and not
otherwise consulted.
**Family / phase:** EQ / Filter, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** **audioif** — `REQUIRES = ("audiobiquad",)`, §8 D1.
**Status:** traits frozen; Station A settled 2026-09-07 (§8, A15)

## 1. The circuit, in one paragraph

The referent is not a pedal but the analog prototype every second-order
low-pass in a synth or a console is a version of: `H(s) = 1/(s² + 2R·s + 1)`
in unit-cutoff form (S4 §4.1 p. 96), with two controls and no nonlinearity
anywhere — a plain low-pass is linear and time-invariant, and the growl that
makes a Moog a Moog belongs to `LadderFilter`, which the vision gives its own
standout. **Cutoff** ω_c slides the whole response along the log-frequency
axis without changing its shape (S4 §2.7, p. 16). **Damping** R sets how
high the peak stands at the corner (S4 §4.2 p. 100), with `Q = 1/2R` (same
page, n. 2). Digitised by the bilinear transform with RBJ's prewarping, the
prototype is one biquad — S1's LPF coefficient block, verbatim, with both
Zavalishin quotations, in **App. R**. The panel controls are *frequency*,
logarithmically, and *resonance*; slope, mix and trim (§6) are host
conveniences no single circuit had.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae …* (App. S) | the LPF coefficients (App. S) | licence unverified, treated as copyleft (App. S) | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* (App. S) | Q = f₀/bandwidth; e^{−π} in Q periods (App. S) | © CCRMA Stanford, no grant (App. S) | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html , …/Decay_Time_Q_Periods.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (App. S) | `H_LP(s) = 1/(s² + 2Rs + 1)` (App. S) | verbatim-copy-only (App. S) | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |

Every S1 formula was cross-checked against the W3C/WebAudio rendering; the
three licences were re-read at their own sources twice more (A11, A12). What
was looked for and not found is in **App. R**.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **The corner gain is the resonance**: \|H(f₀)\| = Q exactly — Q 0.707 → −3.01 dB, Q 2 → +6.02, Q 8 → +18.06, within 0.05 dB | S1, derived analytically and measured (A2) | high | any Q in 0.5–16 more than 0.05 dB from 20·log₁₀(Q) at f₀ | steady-state sine at f₀ for Q ∈ {0.5, .707, 1, 2, 4, 8, 16}, source level set so Q·level < 28 000 (A2) |
| T2 | **Shape invariance under cutoff — on the warped axis**: the response is one curve for every f₀, and the axis it is one curve on is the **bilinear-warped** one. Plotted against f_a/f_a0 with `f_a = (F_s/π)·tan(πf/F_s)` it is f₀-independent to **0.00000 dB** for every f₀ from 20 Hz to 0.4·F_s. Plotted against the linear f/f₀ it slides without deforming only while **f₀ ≤ 250 Hz at 48 kHz** (the octave-pair deviations that fix that span are A13's) | S4 §2.7, p. 16 for the prototype's … (App. T2) | high | on the warped axis, any two f₀ in 20 Hz…0.4·F_s differing by >0.05 dB at the same f_a/f_a0; on the linear axis, two f₀ an octave apart, both ≤ 250 Hz, differing by >0.1 dB anywhere in f₀/8 … 8f₀ | swept sine at f₀ ∈ {31.5, 63 … (App. T2) |
| T3 | **−12 dB/oct asymptote, unity DC**: on T2's warped axis, \|H\| is −24.10 dB at f_a = 4·f_a0 and −36.13 dB at 8·f_a0 — −12.03 dB/oct — at **every** f₀ (Q 0.707). On the linear axis that reads as −24.10 ± 0.10 dB two octaves above f₀ with a fitted 4f₀…8f₀ slope of −12.0 ± 0.3 dB/oct **only for f₀ ≤ 450 Hz at 48 kHz**, by design, because the transform compresses 8f₀ toward Nyquist (the per-f₀ figures, and where 450 Hz comes from, are A13's). DC gain is 0.00 ± 0.1 dB at f₀/100 at every f₀ | S4 §4.1 p. 97, verbatim: *"The slope rolloff speed is obviously −12dB/oct for the low- and high-pass"*; S1 for the coefficients; every figure re-derived from S1 in A13 | high | warped axis: \|H\| at 4·f_a0 outside −24.10 ± 0.05 dB at any f₀ ≤ 0.4·F_s. Linear axis, f₀ ≤ 450 Hz: fitted slope outside −11.7…−12.3 dB/oct, or DC outside ±0.1 dB | swept sine; warped-axis check at f₀ ∈ {31.5 … 4 k}; linear slope fitted 4f₀…8f₀ at f₀ ∈ {31.5, 125, 250, 450} Hz; DC from the step response's settled value |
| T4 | **Q is the ringing**: struck with a click it rings at f₀, envelope down to 4.3 % of peak after Q periods | S3, "Decay Time is Q Periods" | medium — stated for Q … (App. T4) | e^{−π} reached in <0.8 Q or >1.25 Q periods for Q ∈ {2, 4, 8, 16} | impulse, Hilbert envelope … (App. T4) |
| T5 | **Rate-honest — against the closed form at the running rate, not against the 48 kHz curve**: at 44.1 kHz and 22.05 kHz the corner stays at f₀ within 0.1 % and \|H(f₀)\| stays at Q (−3.012 / −3.011 / −3.012 dB measured, A5), and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s. The 48 kHz *curve* is deliberately not required to repeat: the warp is a property of the rate, so at 22.05 kHz the same f₀ sits up to 0.46 dB from its 48 kHz shape even below 2205 Hz (A13), and a class that reproduced the 48 kHz shape at 22.05 kHz would be the wrong filter | S1 (the BLT prewarps f₀ at whatever rate is running); measured at three rates (A5); the cross-rate deviation re-derived in A13 | high | corner displaced >0.1 %, gain at f₀ more than 0.1 dB from 20·log₁₀(Q), or any swept point more than 0.1 dB from the closed form **at that rate** | T2's sweep at 48 000 / 44 100 / 22 050 Hz, each differenced against its own closed form |

No characters: a low-pass has one behaviour.

### Tier 3 — cost and latency

**Latency budget: 0 samples, 0.000 ms**, at every rate and every setting.
No option this class offers adds a lookahead, a partition or a window, so
there is no latency-adding option to default off (A8; re-measured on the
rebuild in the evidence pack).

**Cost budget**, as a fraction of one stereo block's real-time deadline:
**ESP32-P4 ≤ 1.5 %, ESP32-S3 ≤ 5 %** at the 12 dB/oct default;
**≤ 2.5 % / ≤ 9 %** with 24 dB/oct engaged. Lean patch expected: **no** —
if the S3 misses the steeper budget, the Slope macro's high setting is what
gives. The basis the budget was set from is in **App. R**.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Three `audiobiquad.Biquad` sections in series, and nothing else.** The DSP
was never what was wrong with this class; the surface was, and the tail was.
All three sections are the same node over `shared/audioif_filter_f32.c` —
float coefficients, float state, any state word below 1e-20 written as exact
zero — which is the whole reason the tier moved (§8 D1). Every section's
`frequency`, `Q`, `gain_db` and `mix` is a live slot read once per chunk, so
a macro move is a float store and Python computes nothing per block.

| Section | Mode | What it is | Patch 0 |
|---|---|---|---|
| 1 | `LOW_PASS` | the prototype's two poles; Resonance at 12 dB/oct, the fixed Butterworth 0.5412 at 24 | active |
| 2 | `LOW_PASS` | the second pole pair; Resonance at 24 dB/oct | wire |
| 3 | `HIGH_SHELF` @ 5 Hz | the make-up trim; a subsonic shelf is the palette's only route to gain above unity | wire |

At `mix = 0` the kernel writes `to_s16(x0)` — the input sample unchanged
(`audioif_filter_f32.c:239`) — so a section that is not in use costs a pass
and changes no byte (A15). **The A14 cascade-mix hazard does not reach this
class**: it is `audiofilters.Filter`'s, and this class builds no `Filter`.

*(The seed's stock-palette version of this section, the resonance and slope
laws, the mono reading and the stock-board caveat are all in **App. R** —
moved under the length rule, nothing deleted.)*

## 5. Node asks

**None.** Every Tier 2 trait above is reachable on the Phase 1 palette as it
stands, and §4 shows how; an ask without a trait id is not an ask. The one
ask this seed did carry — a DC-clean biquad, for Tier 1 rather than for a
Tier 2 trait — was answered by `audiobiquad` in Phase 1, which is what §8 D1
adopts.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Surface — frozen at Station A

Five macros, well inside the sixteen the contract allows.

| # | Label | Mode | Span (`_MACRO_RANGES`) | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 … 20 000 Hz, log; `_hz()` clamps at 0.49·F_s | the cutoff knob |
| 1 | Resonance | UNIPOLAR | Q 0.5 … 16, log (R = 1/2Q, S4) | the resonance knob |
| 2 | Slope | TOGGLE | 0 = 12 dB/oct (default), 1 = 24 | a console's slope switch |
| 3 | Mix | UNIPOLAR | 0 exactly … 1 | a dry/wet blend; no analog filter had one, kept because Tier 1's wire test needs it |
| 4 | Trim | BIPOLAR | −12 … +12 dB, default 0; under 0.2 dB the section is a wire | the make-up a resonant peak needs |

`capabilities = ()` (§8 D7). The span top and the dropped `(0, 0.01]` snap
are §8 D5 and D6.

**Patches**, named for settings and never for products; the grid column is
`macro_of()` of the setting beside it, so patch 0 is the constructor's own
defaults to within one step of the grid (Q 0.7071 lands on 13/127 = 0.713).

| # | Name | Setting | Grid |
|---|---|---|---|
| 0 | Open | 20 kHz, Q 0.71, 12 dB/oct, mix 1, trim 0 | `(127, 13, 0, 127, 64)` |
| 1 | Soft Roll | 6 044 Hz, Q 0.71, 12 dB/oct | `(105, 13, 0, 127, 64)` |
| 2 | Steep Cut | 2 980 Hz, Q 0.71, 24 dB/oct | `(92, 13, 127, 127, 64)` |
| 3 | Resonant Peak | 1 182 Hz, Q 5.99, 12 dB/oct, −5.95 dB | `(75, 91, 0, 127, 32)` |
| 4 | Squelch | 495 Hz, Q 11.85, 24 dB/oct, −8.98 dB | `(59, 116, 127, 127, 16)` |
| 5 | Sub Only | 120 Hz, Q 0.71, 24 dB/oct | `(33, 13, 127, 127, 64)` |

**`tail_samples` = 204 800** (4.27 s at 48 kHz) — a ceiling over the whole
span, because the contract reads it off the class. Measured worst case:
20 Hz at Resonance 16 and 24 dB/oct, full-scale burst, **203 731** samples
after the source goes silent (A15). There is no per-setting number: the
contract reads `tail_samples` off the class, so the seed's
`ceil(4·Q·F_s/f₀)`, recomputed on every macro move, is not expressible and
the declaration is the measured ceiling instead. It is loose by design at
every setting but the worst one — patch 0's own tail is 0.20 s.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/eq.py`.

- **No surface at all.** `MACRO_LABELS = ()` (`eq.py:120`) — a host has
  nothing to turn.
- **`q` is frozen at construction.** `synthio.Biquad(self.MODE, …  *(argument in full: App. R)*
- **`mix` is accepted and then hidden.** Taken at `eq.py:101`, forwarded at
  `eq.py:105`, unreachable afterwards.
- **`set_frequency` is off-contract and it raises.** `eq.py:110-111` calls …  *(argument in full: App. R)*
- **No tail is declared.** `TAIL_SAMPLES = None`, `LATENCY_SAMPLES = 0` from …  *(argument in full: App. R)*
- **Held DC at low corners** — §5's table.
- **`reset()` reaches one node** — `audiocore.reset_buffer` on `self._output` …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Decisions — every open settled at Station A, 2026-09-07

Nothing here is open. Each decision's argument and the run behind it are in
**A15**; none of them is a number recalled from another class.

| # | Decision | Settled by |
|---|---|---|
| D1 | **Portability tier: audioif**, on `audiobiquad`. A3 asked for a DC-clean audioif-own biquad; Phase 1 shipped one. Every configuration in this class's span reaches exact zero on it; on `synthio.Biquad` the same corners hold −1…−4 LSB for ever. The cost, stated not hidden: a stock CircuitPython board cannot construct this class, where the old one ran there and quietly failed Tier 1 | A3, A14, A15 |
| D2 | **The trim is one `HIGH_SHELF` at 5 Hz**, not the stock shelf pair: flat to 0.010 dB from 50 Hz to 15 kHz, 0.100 dB worst at 20 Hz, all three rates, ±6 and ±12 dB | A15 |
| D3 | **Slope stays 12 / 24 dB/oct.** No 36, no 48 | A15 |
| D4 | **`LowPass` and `HighPass` do not share an implementation class.** One class per file is what lets sixteen rebuilds run in parallel | A15 |
| D5 | **Frequency spans a fixed 20 Hz … 20 kHz**, clamped by `self._hz()` at 0.49·F_s, not the seed's `min(20 kHz, 0.45·F_s)`: `_MACRO_RANGES` is a class attribute and cannot know the rate. It clamps and never refuses, which is the invariant | A15 |
| D6 | **The `(0, 0.01]` mix snap is dropped** with the node it was for: `Filter.c:234` has the threshold, `audiobiquad` does not | A9, evidence pack |
| D7 | **`capabilities = ()`.** Nothing in a low-pass is measured in beats; the class never reads `self._transport()` | — |

---


## Appendix

Run 2026-09-06 on this machine. CPython target:
`audiocomponents/.venv/bin/python` (the `pydevices-audioif` extension built
from `src/cpython` + `src/shared`). MicroPython: `cmods/bin/micropython` with
`MICROPYPATH=audiocomponents:audiocomponents/lib`. Probes were scratch
scripts, not committed; every number is reproducible from its description.

### A0. The Zavalishin license, verbatim

Front matter, p. ii of rev. 2.1.0 as read: *"© Vadim Zavalishin. The right
is hereby granted to freely copy this revision of the book in software or
hard-copy form, as long as the book is copied in its full entirety
(including this copyright note) and its contents are not modified."*
Verbatim-copy-only, no derivatives — a paper for our purposes. The PDF is
not text-extractable by the fetch tool; `pypdf` read it in two lines, the
route `agent-knowledge/instrument-sources.md` already recommends.

### A1. Magnitude response against the closed form (48 kHz, stereo, level 6000, `mix=1`)

Steady-state sine RMS out / RMS in, against a float64 evaluation of the RBJ
transfer function at the same f, Q and rate.

```
  lp f0= 1000.0 Q=0.707 probe=   500.0  measured   -0.263 dB  ideal   -0.263 dB  dev  +0.000 dB
  lp f0= 1000.0 Q=0.707 probe=  1000.0  measured   -3.013 dB  ideal   -3.012 dB  dev  -0.001 dB
  lp f0= 1000.0 Q=0.707 probe=  2000.0  measured  -12.375 dB  ideal  -12.376 dB  dev  +0.000 dB
  lp f0=  100.0 Q=0.707 probe=    50.0  measured   -0.279 dB  ideal   -0.264 dB  dev  -0.015 dB
  lp f0=  100.0 Q=0.707 probe=   100.0  measured   -3.016 dB  ideal   -3.012 dB  dev  -0.004 dB
  lp f0=  100.0 Q=0.707 probe=   200.0  measured  -12.310 dB  ideal  -12.306 dB  dev  -0.004 dB
```

### A2. |H(f₀)| = Q, and the trap in measuring it

```
  Q=0.500  20log10(Q)= -6.021   LPF@f0  -6.022
  Q=0.707  20log10(Q)= -3.012   LPF@f0  -3.013
  Q=1.000  20log10(Q)= +0.000   LPF@f0  -0.001
  Q=2.000  20log10(Q)= +6.021   LPF@f0  +6.019
  Q=4.000  20log10(Q)=+12.041   LPF@f0 +12.040
  Q=8.000  20log10(Q)=+18.062   LPF@f0 +14.152     <-- source level 6000
```

The Q = 8 row is **not** a filter error. At level 6000 the wet path wants
±47 600; the biquad clamps to the sample range (`audioif_biquad.c:174-175`)
and `synthio_mix_down_sample` soft-limits above ±28 000 (`Filter.c:288`).
Repeated with headroom:

```
  Q=  8.0 src   2000  LPF@f0  +18.061 dB   ideal  +18.062
  Q=  8.0 src    600  LPF@f0  +18.061 dB   ideal  +18.062
  Q= 16.0 src    600  LPF@f0  +24.082 dB   ideal  +24.082
  Q= 16.0 src    200  LPF@f0  +24.081 dB   ideal  +24.082
```

**The kit's T1 measurement must choose its source level from Q**, or it
reports a clipping artefact as a coefficient error. That is also T1's
planted fault: set the level so Q·level > 28 000 and the measurement must go
red.

### A3. Held DC after silence, and the probe design that hid it

The first version of this probe pulled a few blocks past the end of the
`RawSample`. When a `Filter`'s source is exhausted, `Filter.c:202-223` takes
the `sample == NULL` branch and **memsets the output to zero without running
the biquads at all** — so every configuration read exactly 0 and the defect
looked absent. Corrected by keeping every pull strictly inside a source that
is still supplying digital silence (0.09 s of 440 Hz at amplitude 12 000,
then 3.0 s of zeros; 287 of the 289 available 1024-sample blocks pulled).
That correction is this measurement's planted fault: run the same probe two
blocks longer and it goes green on a filter that is still holding DC.

CPython target:

```
  LowPass f=100                last     -1  max|.| final block 1
  LowPass f=40 q=8             last     -4  max|.| final block 4
  LowPass defaults(1k)         last     +0  max|.| final block 0
  HighPass defaults(1k)        last     +0  max|.| final block 0
  HighPass f=30                last     -8  max|.| final block 8
  BandPass defaults(1k q.707)  last     +0  max|.| final block 0
  BandPass f=80 q=4            last     -1  max|.| final block 1
  Notch defaults(1k q.707)     last     +0  max|.| final block 0
  Notch f=60 q=8               last     -2  max|.| final block 2
  CombFilter defaults          last     +0  max|.| final block 0
  DynamicEQ defaults           last     +0  max|.| final block 0
```

MicroPython, same configurations and block count: identical in every row.

**Reading it.** Of the roadmap's three candidate answers for Gate 0, a
*block-rate tail gate in Python* cannot see this residual — it lives in the
biquad's sub-sample state (`audioif_biquad.h:14`) and surfaces only as an
integer offset — so it would have to zero the output on a silence heuristic
and would clip quiet material; recommended against. A *DC-clean biquad in an
audioif-own module*, decided once alongside the per-sample phaser question,
is what this seed recommends. A *recorded disconfirmation* is the honest
third option and leaves −72 dBFS of DC in every rest at a 30 Hz corner.

### A4. Mono

```
  mono lp f0=1000 probe=  500.0  measured   -0.263  ideal   -0.263  dev  +0.000
  mono lp f0=1000 probe= 1000.0  measured   -3.011  ideal   -3.012  dev  +0.001
  mono lp f0=1000 probe= 2000.0  measured  -12.375  ideal  -12.376  dev  +0.000
```

### A5. Three rates, gain at f₀ = 1 kHz, Q 0.707

```
   48000 Hz lp @f0  measured   -3.013  ideal   -3.012  dev  -0.001 dB
   44100 Hz lp @f0  measured   -3.011  ideal   -3.012  dev  +0.001 dB
   22050 Hz lp @f0  measured   -3.012  ideal   -3.012  dev  -0.000 dB
```

### A7. Desktop cost anchor (CPython target, x86-64, ns per stereo frame)

```
  Filter 1 biquad         frames= 512    146.6 ns/frame
  Filter 4 biquads        frames= 512    195.1 ns/frame
  real time per stereo frame at 48 kHz = 20833.3 ns
```

### A8. Latency

Impulse at frame 100 through `LowPass(frequency=1000.0)`: first non-zero
output at frame **100**; `latency_samples` reports **0**. Agreed.

### A9. `mix` cross-target divergence

Same source, same biquad, `mix` varied; max |out − src| over eight blocks:

```
             CPython   MicroPython
  mix=0.0          0             0
  mix=0.005       80             0
  mix=0.01       159             0
  mix=0.02       317           317
```

`Filter.c:234` bypasses the cascade when `mix <= 0.01`; the CPython target
(`src/cpython/_audioif.c:605-613`, reached through
`src/cpython/audiofilters.py:137-147`) has no such threshold. Below 0.02 the
two interpreters are not byte-identical.

### A10. Allocation while pulling

MicroPython, `gc.mem_alloc()` delta over 20 pulls: 2 112 bytes per pull for
the `Filter` chain, 24 006 for a bare `RawSample`. Both are
`audiocore.get_buffer()`'s own copy of the block — the Python-visible helper
— not the class's audio path, which runs entirely in C. The Tier 1
allocation check therefore needs a pump that uses the C `get_buffer`, or it
measures the harness.

### A11. Licence and citation audit, 2026-09-06

This seed's §2 carries the corrections themselves; this is the full
re-verification record behind them. Every source row in §2 and every URL
anywhere in this seed was re-fetched by a second agent that read none of the
first run's notes. Corrections applied in place: **S1's licence call** now
records that the repository serving the `.txt` carries a root `LICENSE.md`
(full CC BY 4.0) which the first draft did not mention — the call is
downgraded to *licence unverified, treated as copyleft* because that grant is
the mirror's and the chain to RBJ is unshown, so the treatment (read, never
port) is unchanged; **the unit-cutoff prototype** is Zavalishin §4.1 p. 96,
not §4.2 p. 100 (p. 100 is right for the damping quote and `Q = 1/2R`); **the
shape-invariance quote** is printed on p. 16, not p. 15 (§2.7 opens on p. 15).
Re-verified exactly as the seed states them: RBJ's coefficient blocks and the
`α`/`w0` definitions in the `.txt`; the CCRMA pages' *"Copyright © … Julius O.
Smith III / CCRMA, Stanford University"* with **no** licence grant anywhere on
them; Zavalishin's front-matter grant (A0, verbatim, p. ii of rev. 2.1.0);
musicdsp.org's RBJ page carrying no licence, copyright or terms text at all;
native-instruments.com's copy of the book **404** (still not reached); and the
archive.org item `the-art-of-va-filter-design-rev.-2.1.2` carrying **no**
`licenseurl` and no `rights` field (metadata API, per the sources module).

**Unsourced, and flagged as such:** the attributes given above to the two
dropped candidates (a Sallen-Key or Steiner-Parker VCF; a console
channel-strip low-pass) are stated from general knowledge — no schematic for
either was reached in either run. They carry the scope argument only; nothing
in §3 rests on them.

### A12. Second licence and citation audit, 2026-09-06 (the re-fetch pass)

**Second licence-and-citation audit, 2026-09-06** — a third pass, run
independently of the first audit, in which **every URL in this seed was
re-fetched in this run** and every licence read again at its own source. What
came back, so the calls above rest on this run and not on a prior one:

- `raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt`
  — reached; the file carries **no** occurrence of *license*, *licence*,
  *copyright*, *(c)*, *warranty* or *public domain*.
- `…/master/LICENSE.md` — reached; it is the full **Creative Commons
  Attribution 4.0 International Public License** text.
- `api.github.com/repos/shepazu/Audio-EQ-Cookbook` — reached; `license.key`
  `"other"`, `license.name` `"Other"`, `license.spdx_id` **`"NOASSERTION"`**.
- `webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html` — reached;
  the only rights language is *"Adapted from Audio-EQ-Cookbook.txt, by Robert
  Bristow-Johnson, with permission"* and *"Special thanks to Robert
  Bristow-Johnson for creating the Audio EQ Cookbook and permitting its
  adaption and use for the Web Audio API"*. The chain from the mirror to the
  author is still **not** shown, so the S1 call stands as *licence unverified,
  treated as copyleft*.
- `ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html` — reached; the
  definition is verbatim *"The quality factor (Q) of a resonator may be
  defined as the resonance frequency divided by the resonator bandwidth"*, and
  the page's only rights line is *"Copyright © 2026-08-21 by Julius O. Smith
  III, Center for Computer Research in Music and Acoustics (CCRMA), Stanford
  University"* — no licence granted, so *read as a paper* stands.
- `www.discodsp.net/VAFilterDesign_2.1.0.pdf` — reached (4.9 MB, 520 pages,
  rev. 2.1.0 of 28 October 2018); WebFetch could not read it, `pypdf` could.
  The front matter (printed p. ii) carries the whole grant, verbatim:
  *"© Vadim Zavalishin. The right is hereby granted to freely copy this
  revision of the book in software or hard-copy form, as long as the book is
  copied in its full entirety (including this copyright note) and its contents
  are not modified."* Verbatim-copy-only, no derivatives — confirmed.
- Re-checked and still not reached: `musicdsp.org`'s RBJ page (reached, but
  carries no licence text at all); `native-instruments.com`'s
  `VAFilterDesign_2.1.0.pdf` (**HTTP 404**);
  `archive.org/metadata/the-art-of-va-filter-design-rev.-2.1.2` (reached; **no
  `licenseurl` field and no `rights` field**), which is why the discoDSP
  mirror's own grant is the licence actually read.

Every Zavalishin page number cited in this seed was checked against the
extracted text, page by page.

**Corrections from this pass**, both in §3 and both recorded there in full:
T3's slope citation moved from S4 §2.7 p. 16 (which states no slope) to
§4.1 p. 97, and the Cortex reference narrowed from
`upstream-diff.md:1172-1173` to `:1172` — `:1173` is the Cortex-M0+ row.
§1's four Zavalishin citations were each opened and are **all correct as
printed**: `H_LP(s) = 1/(s² + 2Rs + 1)` at §4.1 p. 96, the shape-invariance
sentence on p. 16, and the damping quote with `Q = 1/2R` in n. 2 on p. 100.
T1's `|H(f₀)| = Q` was re-derived from S1's own coefficients and holds to
0.001 dB for Q ∈ {0.5 … 16}; Zavalishin p. 97 states the same fact
analytically (*"the amplitude response at the cutoff is 1/2R for all three
filter types"*).

**The T3 arithmetic, recomputed from S1's coefficients at 48 kHz, Q 0.707**
(this is the audit's own re-derivation, not a render):

| f₀ | \|H(4f₀)\| | fitted slope 4f₀→8f₀ |
|---|---|---|
| 31.5 Hz | −24.10 dB | −12.03 dB/oct |
| 125 Hz | −24.11 dB | −12.04 dB/oct |
| 500 Hz | −24.19 dB | −12.33 dB/oct |
| 1 kHz | −24.48 dB | −13.32 dB/oct |
| 2 kHz | −25.69 dB | −19.07 dB/oct |

`HighPass`'s version of the same trait looks two octaves *below* f₀ and is
robust for that reason: −24.10 dB and +12.03 dB/oct at every f₀ from 20 Hz to
1280 Hz.

### A13. Trait-critic pass, 2026-09-06 — the bilinear-warp derivations

Every number below is a re-derivation from S1's own coefficients at 48 kHz,
Q 0.707, evaluated in float64 (`audiocomponents/.venv/bin/python`, numpy
2.5.2). It is arithmetic on the published formulae, not a render.

**T3, the linear-axis span.** `|H(4f₀)|` and the slope fitted 4f₀…8f₀:

| f₀ | \|H(4f₀)\| | fitted 4f₀→8f₀ |
|---|---|---|
| 31.5 Hz | −24.100 dB | −12.026 dB/oct |
| 125 Hz | −24.105 dB | −12.044 dB/oct |
| 250 Hz | −24.123 dB | −12.100 dB/oct |
| 450 Hz | −24.175 dB | −12.270 dB/oct |
| 500 Hz | −24.193 dB | −12.329 dB/oct |
| 1 kHz | −24.477 dB | −13.321 dB/oct |
| 2 kHz | −25.692 dB | −19.073 dB/oct |

450 Hz is the last f₀ inside −11.7…−12.3 dB/oct, which is where the row's
span comes from. DC gain at f₀/100 is −0.0000 dB at every f₀ in the table.

**T2, the two axes.** Maximum \|deviation\| between octave-adjacent f₀ over
f₀/8…8f₀, on the linear f/f₀ axis: 31.5–63 Hz 0.005 dB, 63–125 0.018,
125–250 0.074, 250–500 **0.299**, 500–1 k 1.275, 1–2 k 6.968, 2–4 k 44.252.
On the warped axis `f_a = (F_s/π)·tan(πf/F_s)`, the spread across
f₀ ∈ {31.5, 125, 500, 1 k, 2 k, 4 k} at a fixed f_a/f_a0 is **0.00000 dB** at
every ratio from 1/8 to 8 — the invariance is exact, on the right axis. The
warped-axis values at those ratios are −0.001 / −0.264 / −3.012 / −12.305 /
−24.099 / −36.125 dB for r = 1/8, 1/2, 1, 2, 4, 8, which is where T3's
f₀-independent pair comes from.

**T5, the cross-rate deviation.** Same f₀, response compared against the
48 kHz response, over f ≤ 0.1·22 050 = 2205 Hz: at 44.1 kHz the deviation is
≤ 0.023 dB at every f₀ from 31.5 Hz to 2 kHz; at 22.05 kHz it is 0.464 dB at
f₀ = 31.5 Hz, 0.463 at 100 Hz, 0.458 at 250 Hz, 0.440 at 500 Hz and 0.356 at
1 kHz — i.e. **the old row's 0.1 dB band was unreachable at 22.05 kHz at any
cutoff**, because the deviation lives in the stopband near 0.1·F_s where the
warp differs most between the two rates. Measured against its *own* rate's
closed form the filter is exact (A1, A5: 0.001 dB).

### A14. Palette verification pass, 2026-09-07

Independent re-measurement of every §4/§5 claim about what an audioif node
can and cannot do. CPython target `audiocomponents/.venv/bin/python`
(`src/cpython/*.py` over the same `src/shared` C the boards run); MicroPython
`cmods/bin/micropython`. Probes were scratch scripts, not committed; each
number is reproducible from its description. Sources were pulled through a
`Mixer` pump so nothing ever hands a downstream node more than 512 frames at
once — a bare `RawSample` hands its whole array over in one call, which is the
trap `DynamicEQ` A2 records.

**Magnitude against the closed form** (steady sine, DFT at the probe bin over
the second half of a two-second render, level 6000, `mix=1`), fifteen f₀/probe
pairs, f₀ ∈ {50, 100, 1 k, 10 k, 15 k, 20 k} Hz, probes 50 Hz…20 kHz:

```
  LOW_PASS   worst deviation  +0.005 dB   (f0 10 kHz, probe 18 kHz)
  HIGH_PASS  worst deviation  -0.008 dB   (f0 20 kHz, probe 10 kHz)
  BAND_PASS  worst deviation  -0.001 dB
  NOTCH      passband worst   -0.0004 dB
```

So the §4 figure of 0.015 dB is conservative, and the vision's 0.03 dB more
so. `audioif_biquad.c:70-125`, `:54-68` and `audioif_biquad.h:14` read as §4
cites them.

**`A` is discarded outside the shelf/peaking modes.** `LOW_PASS` at 1 kHz,
Q 0.707, gain at 200 Hz: `A=0.5` → −0.0072 dB, `A=1.0` → −0.0072 dB,
`A=2.0` → −0.0072 dB. The C says why: `Biquad.c:82-83` reads the `A` slot only
when `mode >= SYNTHIO_PEAKING_EQ`, and `Biquad.c:228-233` is the whole Python
surface — `mode`, `frequency`, `Q`, `A`. There is no route from Python to a
biquad's `b` coefficients.

**The shelf pair as a broadband trim** (both sections in the same `Filter`
cascade, same corner 1 kHz, same `A`; `A = 10^(dB/40)`):

```
  want   -6.0 dB ->  -6.000 / -6.001 / -6.000 / -6.001 / -6.002 dB
  want   +6.0 dB ->  +6.000 / +6.000 / +6.000 / +6.000 / +6.000 dB
  want  +12.0 dB -> +12.000 / +12.000 / +12.000 / +12.000 / +12.000 dB
                     at 50 / 200 / 1 k / 5 k / 15 k Hz
```

Flat to 0.002 dB. The cut-only alternative, one `audiomixer.Mixer` voice
level: 0.5 → −6.021 dB, 0.251 → −12.013 dB, 1.0 → −0.000 dB.

**`mix` over a cascade diverges between the desktop targets.** 3 kHz sine at
9000 into `LOW_PASS` 1 kHz sections, eight blocks, FNV-1a over the rendered
bytes:

```
                        MicroPython            CPython
  1 stage  mix=1.0   peak 2051 d3d48017   peak 2051 d3d48017   same
  1 stage  mix=0.5   peak 4721 76f4a5ca   peak 4721 76f4a5ca   same
  2 stages mix=1.0   peak 1258 170a7648   peak 1258 170a7648   same
  2 stages mix=0.5   peak 5129 a3a89610   peak 1211 a94ddf6d   DIFFERENT
```

`Filter.c:279-283` runs every stage and `:288` then blends the *source*
against the cascade's output; `src/cpython/audiofilters.py:140` gives the mix
to the last stage alone, so on CPython the dry half of the blend is already
filtered by the earlier stages. Not recorded in `audioif/docs/upstream-diff.md`
(grepped 2026-09-07). It reaches `LowPass`, `HighPass` and `BandPass` through
the Slope macro and `Notch` through the harmonic option, at any `mix` strictly
between 0 and 1.

**Mono is the same filter.** At `channel_count = 1` and at 2, `LOW_PASS`,
`HIGH_PASS`, `BAND_PASS` and `NOTCH` at f₀ 1 kHz render the same gain to
0.0000 dB of each other and match the closed form to 0.002 dB. §4's mono line
holds for all four filter classes.

**Held DC after silence** — A3 reproduced row for row on the CPython target,
same probe (0.09 s of 440 Hz at 12 000 then 3.0 s of zeros, 287 blocks pulled,
every pull strictly inside the source): `LowPass` 100 Hz −1, `LowPass` 40 Hz
q 8 −4, `HighPass` 30 Hz −8, `BandPass` 80 Hz q 4 −1, `Notch` 60 Hz q 8 −2,
and exact zero at every 1 kHz default and for `CombFilter` and `DynamicEQ`.
−8 LSB is −72.2 dBFS. A3 stands as written.

### App. I — Tier 1 invariants, the standard block

Verbatim from vision §3, moved out of §3 under the length rule. It is the
same block in every seed; a class-specific note on it is kept with it here.

- [ ] Silence in gives silence out; a decaying tail reaches exact zero — no
      held DC (the audioif#23 class of defect).
- [ ] `mix` at zero, or drive at zero, is a wire (byte-identical to source).
- [ ] Level-honest: unity through the dry path, no hidden gain.
- [ ] Reported `latency_samples` / `tail_samples` match what is measured —
      latency by a click against the dry path at 48 kHz and 44.1 kHz, tail
      by the burst-then-silence probe.
- [ ] `reset()` leaves every node the class built silent and stateless and
      the borrowed source untouched (planted faults: a delay line left full;
      an upstream instrument reset through a Filter- or Phaser-tailed chain).
- [ ] `deinit()` deinitialises every node the class built and leaves the
      source rendering (planted fault: an intermediate node left live).
- [ ] `capabilities` names exactly the optional behaviours the class honours
      (`"tempo_sync"` declared if and only if the transport is read).
- [ ] Pulling `output` allocates nothing.
- [ ] CPython and desktop MicroPython render identical bytes on the probe
      material, or the cause is recorded here; the P4 and S3 digests match
      the desktop's or carry a recorded cause (float width is the expected
      one, never the class).
- [ ] Rate-honest: designed and stated at 48 kHz; every invariant also holds
      at 44.1 kHz and 22.05 kHz; Hz-valued spans and options clamp below
      Nyquist at the running rate, never refuse; any Tier 2 trait that cannot
      hold at a lower rate is named here with why.
- [ ] Every invariant also holds at `channel_count` 1; a stereo-by-definition
      class states in §4 what a mono source gets (a wire, or the mono sum of
      its stereo behaviour), and the kit measures that statement.

Two already carry Phase 0 measurements. **Byte-identity is green** except
for `mix` in `(0, 0.01]`, where `Filter.c:234` bypasses the cascade on
MicroPython while the CPython target blends (A9) — §6 keeps the macro out of
that band. **Exact zero after silence is red at low corners** — audioif#23
reproduced on both interpreters; §5 has the numbers and the Gate 0 routing.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* (plain text, shepazu mirror) | the LPF coefficients, `α = sin(w0)/(2Q)`, `w0 = 2π f0/Fs`, verbatim | the `.txt` itself carries **no license, copyright or warranty line** (re-verified 2026-09-06, all five terms searched) — but the repository serving it does: its root `LICENSE.md` is the full **CC BY 4.0** text (read at https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/LICENSE.md; GitHub's own licence API reports the repo as `NOASSERTION`). That is the *mirror's* grant, not RBJ's: the mirror's HTML rendering says only *"Adapted from Audio-EQ-Cookbook.txt, by Robert Bristow-Johnson, with permission"*, so the chain to the author is **not** shown (sources module: a repackager's label is an assertion). **License unverified — treated as copyleft:** read as a document for its mathematics, never ported | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Quality Factor (Q)", "Decay Time is Q Periods" | Q = f₀/bandwidth; the envelope reaches e^{−π} in Q periods | © J. O. Smith III / CCRMA Stanford; no license granted. Read as a paper | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html , …/Decay_Time_Q_Periods.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP mirror, text via `pypdf`) | the 2-pole prototype `H_LP(s) = 1/(s² + 2Rs + 1)` (§4.1 p. 96); cutoff shape-invariance (§2.7, p. 16); R as damping and `Q = 1/2R` (§4.2 p. 100, and its n. 2) | verbatim-copy-only, no derivatives (grant quoted in A0). Read as a paper | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T2 | **Shape invariance under cutoff — on the warped axis**: the response is one curve for every f₀, and the axis it is one curve on is the **bilinear-warped** one. Plotted against f_a/f_a0 with `f_a = (F_s/π)·tan(πf/F_s)` it is f₀-independent to **0.00000 dB** for every f₀ from 20 Hz to 0.4·F_s. Plotted against the linear f/f₀ it slides without deforming only while **f₀ ≤ 250 Hz at 48 kHz**: 125 vs 250 Hz differ by 0.074 dB, 250 vs 500 Hz by 0.299, 1 k vs 2 k by 6.97 | S4 §2.7, p. 16 for the prototype's invariance; the warped-axis form and every figure here re-derived from S1's own coefficients in A13 | high | on the warped axis, any two f₀ in 20 Hz…0.4·F_s differing by >0.05 dB at the same f_a/f_a0; on the linear axis, two f₀ an octave apart, both ≤ 250 Hz, differing by >0.1 dB anywhere in f₀/8 … 8f₀ | swept sine at f₀ ∈ {31.5, 63, 125, 250, 500, 1k, 2k, 4k} Hz, resampled onto f_a/f_a0 and differenced; the linear-axis half repeated on the first four |
| T4 | **Q is the ringing**: struck with a click it rings at f₀, envelope down to 4.3 % of peak after Q periods | S3, "Decay Time is Q Periods" | medium — stated for Q ≫ ½, so the kit tests Q ≥ 2 | e^{−π} reached in <0.8 Q or >1.25 Q periods for Q ∈ {2, 4, 8, 16} | impulse, Hilbert envelope, time to −27.3 dB ÷ (1/f₀) |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

**Length, said plainly.** After Station A, §§1–8 measure **13.5 KB** against
the vision's 8–12 KB band, and this is where the excess is: §3's frozen
Tier 2 table is 4.7 KB on its own and App. T's rule keeps every trait's
statement, disconfirmation and measurement in §3; §6 now carries the frozen
macro and patch tables and §8 the seven settled decisions, neither of which
the seed had. Everything that could move without cutting a gate condition
has moved here or to A15. It is over the band by 1.5 KB and the band is not
met.

*(from §1)*

The two Zavalishin quotations §1 stands on, verbatim as printed: *"the
variation of the cutoff parameter doesn't change the shape of the amplitude
response graph"* (§2.7, p. 16) and *"at R = 0 the resonance peak becomes
infinitely high … R actually has the function of decreasing or damping the
resonance"* (§4.2, p. 100, whose n. 2 is `Q = 1/2R`).

And the biquad §1 digitises to, S1 verbatim: `b0 = b2 = (1−cos ω₀)/2`,
`b1 = 1−cos ω₀`, `a0 = 1+α`, `a1 = −2cos ω₀`, `a2 = 1−α`,
`α = sin(ω₀)/(2Q)`, `ω₀ = 2π f₀/F_s` — exactly the arithmetic at
`audioif_biquad.c:76-86`, and, on the node this class actually builds, at
`audioif_filter_f32.c`'s float version of the same block.

*(from §2)*

**Looked for, not found:** musicdsp.org's RBJ page carries no license text
(fetched); native-instruments.com's `VAFilterDesign_2.1.0.pdf` 404s; the
archive.org item for rev. 2.1.2 has **no `licenseurl` field**, so the
discoDSP mirror's own front-matter grant is the license actually read. Every
S1 formula was cross-checked against the W3C/WebAudio HTML+MathML rendering
(https://webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html,
reached; *"Adapted … with permission"*, nothing further).

*(from §4, the seed's stock-palette version — superseded by §8 D1, kept
verbatim)*

**Compose first, and the palette already fits.** One `synthio.Biquad` in
`LOW_PASS` mode inside one `audiofilters.Filter`, as today — the DSP is not
what is wrong with this class, the surface is. `audioif_biquad.c:70-125`
computes RBJ's coefficients in `double`; `choose_shift()` (`:54-68`) gives
each filter as many fractional bits as it individually has room for, and the
state keeps 12 bits below the sample grid (`audioif_biquad.h:14`). Measured
against the closed form the node lands within **0.015 dB** from 50 Hz to
20 kHz (A1) — better than the 0.03 dB the vision's palette table claims; an
independent re-measurement on 2026-09-07 over fifteen f₀/probe pairs,
probes 50 Hz…20 kHz, read **0.005 dB** worst (A14).
Python computes nothing per block: `frequency` and `Q` are `synthio` block
slots C ticks (`Filter.c:281`), so a macro move is a float store.

*(from §4, Station A)*

**The A14 cascade-mix hazard, and why it is gone.** `audiofilters.Filter`
blends `mix` against the whole cascade's output on MicroPython
(`Filter.c:279-283` then `:288`) and against the last stage's input on the
CPython target (`src/cpython/audiofilters.py:140`), so two biquads at
`mix = 0.5` render peak 5129 against 1211 with different FNV digests (A14) —
which is exactly Slope 24 dB/oct with Mix anywhere between the ends, and
would have broken Tier 1's identical-bytes invariant on the desktop pair.
This class builds no `Filter`: `mix` is per-section, in one C kernel both
desktop targets share. The palette defect is still audioif's to fix, and the
numbers stay in A14 for whoever files it.

*(from §2)*

**Standout confirmed.** Two candidates were weighed and dropped: a Sallen-Key
or Steiner-Parker VCF, whose distinguishing traits are its nonlinearity and
resonance-versus-level behaviour and so belong to `LadderFilter` (vision
§4.2) — two classes must not chase one circuit; and a console channel-strip
low-pass, which contributes only the slope switch §6 adopts without needing a
referent.

*(from §2)*

**Independent licence and citation audit, 2026-09-06** (a second agent, none
of the first run's notes read; full record in Appendix A11). Three
corrections are applied above: **S1's licence call** now records the root
`LICENSE.md` (full CC BY 4.0) the serving repository carries and the first
draft did not mention — downgraded to *licence unverified, treated as
copyleft* because that grant is the mirror's and the chain to RBJ is unshown,
so the treatment is unchanged; **the unit-cutoff prototype** is Zavalishin
§4.1 p. 96, not §4.2 p. 100 (p. 100 is right for the damping quote and
`Q = 1/2R`); **the shape-invariance quote** is printed on p. 16, not p. 15.
The two dropped candidates' attributes are **unsourced** general knowledge —
no schematic for either was reached; they carry the scope argument only.

*(from §2)*

**Second licence-and-citation audit, 2026-09-06** (a third pass, independent
of the first audit; **every URL in this seed re-fetched in this run**, every
licence read again at its own source, every Zavalishin page opened in the
extracted text). The S1 and S4 calls above are re-confirmed unchanged — the
cookbook `.txt` still carries no rights line of any kind, the serving repo's
`LICENSE.md` is CC BY 4.0 but is the *mirror's* grant, and Zavalishin's front
matter still grants verbatim copying only. **Two corrections, both in §3:**
T3's slope citation moved from S4 §2.7 p. 16 — which states no slope — to
§4.1 p. 97, quoted; and the Cortex reference narrowed to
`upstream-diff.md:1172` (`:1173` is the Cortex-M0+ row). Full record, with
every quote and status code, in `A12`.

*(from §3)*

**Trait-critic pass, 2026-09-06.** T2, T3 and T5 rewritten in place for one
root defect: they stated the *analog* prototype's log-axis properties as though
digitisation preserved them at every f₀, and the bilinear warp does not. Each
now names the axis and the span its claim holds on, with the closed form
carrying the claim outside it. Figures re-derived from S1's coefficients in
A13; no row deleted. T1 and T4 unchanged. **Five Tier 2 rows after the pass.**

*(from §3)*

**Audit note, 2026-09-06 (the re-fetch pass).** T3's source is corrected in
the table above — printed p. 16 is §2.7, the *1-pole* cutoff-parameterization
page, and states no slope; the −12 dB/oct figure for the 2-pole is at §4.1
p. 97. And **T3's −24.1 dB is the low-f₀ value, not an f₀-independent one**:
re-deriving from S1's own coefficients at 48 kHz gives −24.10 dB two octaves
above f₀ for f₀ ≤ 125 Hz but −24.48 at 1 kHz and −25.69 at 2 kHz, because the
bilinear transform warps 8f₀ toward Nyquist, so the fitted 4f₀…8f₀ slope
leaves the stated −11.7…−12.3 dB/oct band above about 500 Hz. The trait
wording is left exactly as the run fixed it — a fixed trait set is not the
auditor's to re-cut — and the f₀ span it holds over is Station A's to state.
Numbers in `A12`.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 1.5 %, ESP32-S3 ≤ 5 %** at the 12 dB/oct default, **≤ 2.5 % / ≤ 9 %** with
24 dB/oct engaged. Lean patch expected: **no** — if the S3 misses the steeper
budget, the Slope macro's high setting is what gives. Basis, so Phase 1 has
something to fail: `audioif_biquad_process()` is 76 instructions per sample
on Cortex-M4/M7 (`audioif/docs/upstream-diff.md:1172`; :1173 is the
Cortex-M0+ row, 154), ~7.3 M
instructions/s for two channels at 48 kHz; desktop anchor 147 ns per stereo
frame against a 20 833 ns budget, +16 ns per extra section (A7).

*(from §3)*

**Latency: zero.** A biquad is a difference equation over samples already in
hand; nothing looks ahead. `latency_samples` is 0 at every rate and setting,
and **no option this class offers adds any** — no lookahead, no partition, no
window; measured impulse in at frame 100, out at frame 100 (A8).
`tail_samples` is not zero and must be declared: T4 gives the number, so the
class reports `ceil(4·Q·F_s/f₀)` (≈ −109 dB), recomputed when frequency or
resonance moves.

*(from §4)*

*Slope 24 dB/oct* is a second `Biquad` in the same cascade with the
Butterworth Q pair (0.5412, 1.3066) scaled by the resonance macro, computed
on CPython at construction; no table ships. *Mix* is `Filter`'s own slot
(`Filter.c:232`), clamped away from `(0, 0.01]` for the cross-target reason
in §3. *Trim* is a `LOW_SHELF` + `HIGH_SHELF` pair at one corner sharing one
`A`, appended to the same cascade: measured flat to **0.002 dB** from 50 Hz
to 15 kHz at −6, +6 and +12 dB (A14), stock, and a macro move is still one
float store per shelf. It cannot fold into the low-pass section's own
coefficients — `synthio.Biquad` exposes only `mode`, `frequency`, `Q` and `A`
(`audioif/src/synthio/Biquad.c:228-233`) and `A` is read only when
`mode >= PEAKING_EQ` (`:82-83`), so in `LOW_PASS` mode `A` is discarded;
measured, `A` of 0.5, 1.0 and 2.0 give the identical gain (A14). A single
`audiomixer.Mixer` voice level is the cut-only stock alternative and
`audiomath.Multiply` against a constant table is exact but audioif-tier (§8).
*Mono:* a mono source gets the identical filter, measured exact (A4);
nothing here is stereo by definition.

*(from §4)*

**One palette hazard the rebuild must document.** `Filter`'s `mix` blends
against the **whole cascade's** output on MicroPython/CircuitPython
(`audioif/src/audiofilters/Filter.c:279-283` then `:288`) and against the
**last stage's input** on the CPython target
(`audioif/src/cpython/audiofilters.py:140`). One biquad at any `mix`, and any
cascade at `mix` 0 or 1, agree byte for byte; two biquads at `mix = 0.5`
render peak 5129 on MicroPython against 1211 on CPython, different FNV
digests (A14). That is exactly Slope 24 dB/oct with the Mix macro anywhere
between the ends, so §6's surface as proposed **breaks Tier 1's
identical-bytes invariant on the desktop pair**. The rebuild either keeps the
mixed stage single (one biquad, or a second `Filter` after the first) or the
divergence is filed against audioif and fixed there; it is a palette defect,
not a class defect.

*(from §4)*

**Portability tier: stock.** The caveat the docstring and README row carry: a
*stock CircuitPython* board runs upstream's Q15 biquad, not this one, so
below a few hundred hertz T1–T3 do not hold there
(`audioif/docs/upstream-diff.md:1223-1226`). Upstream's own measured number is
a `LOW_PASS` at 100 Hz reading **−3.94 dB** at its corner
(`audioif/docs/upstream-reports/biquad-band-edges.md:145`); the far worse
"before" column at `upstream-diff.md:1111-1121` is *this port's* pre-fix
arithmetic, which `:1127-1135` disowns in terms — do not quote it as
upstream's. The class still constructs and runs; it is a property of the
board, not of the class.

*(from §5)*

One **Tier 1** item is red and is routed to Gate 0 rather than asked here:
the held-DC residual (audioif#23) belongs to the whole EQ family and
`Phaser`, and the roadmap reserves one answer for all of them. This seed
contributes the measurement that answer is owed — the issue's two
configurations extended to nine, on both interpreters (Appendix A3), worst
case **−8 LSB = −72.2 dBFS of DC that never decays**, on a 30 Hz high-pass —
and recommends the DC-clean audioif-own biquad, for the reason given in A3.
§3's Tier 1 line is amended to name whatever Gate 0 takes, and the numbers go
to audioif#23 either way.

*(from §7)*

- **`q` is frozen at construction.** `synthio.Biquad(self.MODE,
  self.frequency, Q=q)` (`eq.py:104`) passes a bare float while `frequency`
  gets a `synthio.Math` block (`eq.py:102-103`), so the corner can be swept
  and the resonance cannot.

*(from §7)*

- **`set_frequency` is off-contract and it raises.** `eq.py:110-111` calls
  `_core.check_hz`, which raises `ValueError` at or above Nyquist
  (`_core.py:471-474`) instead of clamping — a direct violation of the
  rate-honest invariant's *"never refused at construction or at `set_macro`"*.

*(from §7)*

- **No tail is declared.** `TAIL_SAMPLES = None`, `LATENCY_SAMPLES = 0` from
  the base (`_core.py:140-141`): latency 0 is right and measured right (A8);
  the tail of a ringing filter is simply unstated.

*(from §7)*

- **`reset()` reaches one node** — `audiocore.reset_buffer` on `self._output`
  only (`_core.py:366-374`); here that is the `Filter`, which resets its
  source recursively, so the borrowed source *is* reset, which the contract
  forbids. The rebuild enumerates its own nodes.

### A15. Station A's own runs, 2026-09-07 — the six decisions

Every number below is from a run made for this section on
`audiocomponents/.venv/bin/python` with `audioif` at the pin, through the
worktree's own `lib`. Probes were scratch scripts, not committed; each is
reproducible from its description.

**D1, the tail.** Burst then digital silence, the source still supplying
zeros at every pull, last non-zero output frame counted from the start of
the burst. Every row reaches exact zero and stays there — which is the
invariant `synthio.Biquad` cannot meet at these corners (A3).

```
  rate  slope     f0      Q   last non-zero frame        s
 48000     12   20.0   16.0              119575     2.491
 48000     12   20.0  0.707               14332     0.299
 48000     12  100.0   16.0               40840     0.851
 48000     12 1000.0  0.707                9708     0.202
 48000     24   20.0   16.0              191558     3.991
 48000     24   20.0  0.707               18989     0.396
 48000     24  100.0   16.0               67116     1.398
 48000     24 1000.0  0.707                9804     0.204
 44100     24   20.0   16.0              174968     3.968
 22050     24   20.0   16.0               87219     3.956
```

The rows above are struck with a 200 ms burst at amplitude 12 000. The
declared `TAIL_SAMPLES` comes from the same probe at **full scale**: 20 Hz,
Q 16, 24 dB/oct, 48 kHz, last non-zero frame **213 331**, which is 203 731
samples after the 9 600-frame burst ends. Declared 204 800.

**D2, the trim.** Steady sine, exact-bin DFT over the second half of a 0.5 s
render, wet minus dry, level 4 000, one `audiobiquad.Biquad` `HIGH_SHELF` at
Q 0.707. Worst deviation from the asked-for gain over probes at 20, 50, 100,
1 k, 5 k, 10 k and 15 kHz:

```
              corner 5 Hz            corner 10 Hz
  want   worst dev   where     worst dev   where
  -12.0    -0.019 dB  20 Hz      +0.926 dB  20 Hz
   -6.0    +0.033 dB  20 Hz      +0.384 dB  20 Hz
   +6.0    -0.100 dB  20 Hz      -0.387 dB  20 Hz
  +12.0    -0.041 dB  20 Hz      -0.951 dB  20 Hz
```

At 50 Hz and above the 5 Hz shelf is within 0.010 dB at every rate and every
gain in the table; the same run at 44 100 and 22 050 Hz reads the same to
0.01 dB. So one section carries the trim, where A14's stock alternative
needed two.

**D2's rejected alternatives, from A14, restated in one line each:** a
`audiomixer.Mixer` voice level is cut-only (0.5 → −6.021 dB, 1.0 → −0.000)
and cannot be the make-up a +24 dB corner needs to come back from;
`audiomath.Multiply` is exact but also cannot exceed unity; and folding the
trim into `b0/b1/b2` is not available at all — there is no route from Python
to a biquad's coefficients.

**The resonance law at both slopes.** At 24 dB/oct the first section holds
the lower Butterworth Q (0.5412) fixed and the resonance rides the second
(1.3066·Q/0.7071) alone, so `|H(f₀)|` is the product and reads as Q at both
slopes — T1 holds at both settings rather than at one. Scaling *both* Qs
would square it: Resonance 2 would stand +15.05 dB up rather than +6.02.
Measured, 1 kHz corner, source level scaled from Q so nothing clips:

```
       Q     20log10(Q)   12 dB/oct   dev      24 dB/oct   dev
   0.500       -6.021       -6.021   -0.000       -6.021   -0.000
   0.707       -3.010       -3.010   -0.000       -3.010   -0.000
   1.000       +0.000       +0.000   +0.000       +0.000   +0.000
   2.000       +6.021       +6.021   -0.000       +6.020   -0.000
   4.000      +12.041      +12.041   -0.000      +12.041   -0.000
   8.000      +18.062      +18.062   +0.000      +18.062   -0.000
  16.000      +24.082      +24.082   +0.000      +24.083   +0.000
```

The source level is chosen from Q, which A2 records as this measurement's
own trap: at a fixed level the Q 8 row reads +14.15 dB and looks like a
coefficient error when it is a clip.

**The 24 dB/oct slope itself**, fitted 4f₀→8f₀ at f₀ = 125 Hz, Q 0.707:
−48.179 dB at 4f₀, −72.066 dB at 8f₀, **−23.886 dB/oct**.

**`mix = 0` is a byte-exact wire over the whole chain.** 997 Hz at amplitude
20 000, three `audiobiquad` sections in series, every `mix` at 0, 0.2 s
pulled: the chain's FNV-1a is `85b80d99` and the source's own is `85b80d99`,
and the bytes compare equal. Through the built class the same test reads
`4dd480f1` on both sides.

**D3, why the slope stops at 24 dB/oct.** Three reasons, in order of weight.
The dossier's S3 budget is already 9 % of one stereo block's deadline at
24 dB/oct, and a third and fourth section would take one filter past a tenth
of a block on the part it is tightest on. No source in §2 describes a
steeper console filter, so a 48 dB/oct position would be a feature with no
referent, which §1's design grade does not license. And every extra section
would have to be built at construction and left as a wire at every other
setting, because a node cannot join a running graph — so the cost of the
positions nobody selects is paid by everybody. A crossover leg is a
different class's job.

**D4, why `LowPass` and `HighPass` stay separate files.** The registry rule
is one class per file named after its `NAME`, with nothing else edited; that
is exactly what lets sixteen classes be rebuilt in parallel with no shared
file to conflict over. A shared mode-parameterised base would be a third
file both rebuilds must edit, and `HighPass` is not in this batch. The form
stays available later, as a private helper module, if the EQ family ever
lands in one session.

**D5, the span top.** `_MACRO_RANGES` is a class attribute; `macro_value()`
reads it off the class, so it cannot depend on an instance's rate and the
seed's `min(20 kHz, 0.45·F_s)` is not expressible there. The rate-honest
clamp is `self._hz()` — 0.49·F_s, so 10 804 Hz on a 22.05 kHz graph — which
clamps rather than refusing, which is what the invariant asks. A14 measured
the node at f₀ 20 kHz reading within 0.005 dB of the closed form, so the
band between 0.45 and 0.49·F_s is not a band the arithmetic gives up in.

