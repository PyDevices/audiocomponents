# Effects Dossier — `BandPass` (no historical standout — design grade)

**Class:** `lib/audioeffects/eq.py` — the current implementation is read once,
for §7, and not otherwise consulted.
**Family / phase:** EQ / Filter, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** **audioif** — `REQUIRES = ("audiobiquad",)`. The seed
proposed stock (`audiofilters.Filter` + `synthio.Biquad`); Phase 1 granted the
DC-clean biquad A3 routed to Gate 0, and §4 records the move with its
measurements. The stock reading is kept, unchanged, in App. R.
**Status:** **traits frozen 2026-09-07** for the Phase 2 rebuild (was: seed,
Phase 0). Sections 1–8 are the five-minute read; every figure moved out of
them sits in an appendix, and nothing has been deleted.

## 1. The circuit, in one paragraph

The referent is the two-pole resonant band-pass — the middle output of every
state-variable filter ever built, and the thing a wah pedal, a telephone
simulator and a multiband crossover's mid leg all are. Zavalishin takes it
from the low-pass by the LP→BP substitution and notes that a state-variable
core hands the low-pass, band-pass and high-pass out at once, everything else
being a linear mix of the three (S4 §4.7 p. 117: *"By mixing the lowpass,
bandpass and highpass outputs one can obtain further filter types"*). Two
controls, no nonlinearity: **centre frequency** f₀, and a **width** that is
the resonator's Q — *"quality factor (Q) of a resonator may be defined as the
resonance frequency divided by the resonator bandwidth"* (S3), so the −3 dB
bandwidth is exactly f₀/Q. The variant this class wants is RBJ's *constant
0 dB peak gain* form, `b0 = α, b1 = 0, b2 = −α` (S1, verbatim): its numerator
has zeros at both `z = 1` and `z = −1`, so the filter is **exactly zero at DC
and at Nyquist** and its peak is 0 dB **for every Q** — the width knob
narrows the band without changing the level of what passes, which is the
property that makes it usable as a musical control rather than a gain
staircase. Panel controls: *frequency*, logarithmically, and *width*.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* … (App. S1) | the BPF (constant 0 dB peak gain) coefficients … (App. S1) | the `.txt` itself carries **no license … (App. S1) | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* … (App. S3) | *"Q … resonance frequency divided by the resonator … (App. S3) | © J. O. Smith III / CCRMA Stanford … (App. S3) | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html , …/Decay_Time_Q_Periods.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP … (App. S4) | the SVF's simultaneous LP/BP/HP outputs and linear-mix … (App. S4) | verbatim-copy-only … (App. S4) | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |
| **S5** Lazzarini & Timoney … (App. S5) | context on the SVF's LP/BP/HP transfer functions and … (App. S5) | **CC BY 4.0** — permissive … (App. S5) | https://arxiv.org/abs/2111.05592 | 2026-09-06 |

Every S1 formula was cross-checked against the W3C/WebAudio HTML+MathML
rendering (https://webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html,
reached). **Looked for, not found:** musicdsp.org's RBJ page carries no
license text (fetched); archive.org's Zavalishin item has **no `licenseurl`
field**, so the discoDSP mirror's own front-matter grant is the license read.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

The source reading and the confidence call for every row are in **App. T**,
where that appendix's own rule puts them.

| # | Trait (falsifiable as stated) | Disconfirmed by | Measurement (kit) |
|---|---|---|---|
| T1 | **0 dB peak, at every Q**: the gain at f₀ is 0.00 dB ± 0.05 for every Q from 0.1 to 100 — narrowing the band does not change the level of what passes | any Q in 0.1…100 whose gain at f₀ is more than 0.05 dB from 0 | steady-state sine at f₀ for Q ∈ … (App. T1) |
| T2 | **Width is f₀/Q**: the −3 dB points sit at `f₀·(√(1+1/4Q²) ∓ 1/2Q)`, so their difference is exactly f₀/Q — at f₀ 1 kHz, Q 2 that is 780.8 Hz and 1280.8 Hz | either predicted edge reading outside −3.0 ± 0.15 dB, for any Q in 0.5…16 | swept sine; the two −3 dB … (App. T2) |
| T3 | **Exact zeros at DC and Nyquist**: the numerator `(α, 0, −α)` vanishes at `z = ±1`, so a DC offset and a Nyquist-rate alternation both produce exactly zero, at every f₀ | a settled output that is not bit-exactly zero for a held DC offset, at any f₀ ≥ 20 Hz | DC step, and a ±FS alternating … (App. T3) |
| T4 | **±6 dB/oct skirts, and the two skirts do not have the same span**: the **low** skirt is +6.005 dB/oct fitted over f₀/8…f₀/4 at every f₀ from 20 Hz to 2 kHz, and \|H(f₀/100)\| is −37.0 ± 0.1 dB at every f₀ at Q 0.707 (the 1/Q·(f/f₀) law). The **high** skirt is −6.0 ± 0.3 dB/oct over 4f₀…8f₀ only while **f₀ ≤ 600 Hz at 48 kHz** — above that, 8f₀ runs into the bilinear compression and the claim is the closed form itself … (App. T4) | low skirt outside +(5.7…6.3) dB/oct at any f₀ ≤ 2 kHz, or \|H(f₀/100)\| outside −37.0 ± 0.1 dB at any f₀; high skirt outside −(5.7…6.3) dB/oct at any f₀ ≤ 600 Hz; or, at any f₀, a rendered point more than 0.1 dB from S1's closed form | swept sine, low skirt fitted f₀/8…f₀/4 … (App. T4) |
| T5 | **Geometric symmetry — about the *prewarped* centre**: folded about f_a0 on the bilinear-warped axis `f_a = (F_s/π)·tan(πf/F_s)`, the response at f_a0·r equals the response at f_a0/r to **0.00000 dB** for every r in 1…8 and every f₀ from 20 Hz to 0.1·F_s. On the *linear* axis it holds within 0.1 dB only while f₀·r stays below about 0.06·F_s … (App. T5) | on the warped axis, any r in 1…8 at any f₀ ≤ 0.1·F_s where the two gains differ by >0.05 dB; on the linear axis, any r whose upper probe is below 0.06·F_s and whose two gains differ by >0.1 dB | swept sine, response resampled … (App. T5) |
| T6 | **Rate-honest — against the closed form at the running rate, not against the 48 kHz curve**: at 44.1 kHz and 22.05 kHz the centre stays at f₀ within 0.1 %, T1's peak and T2's edges hold to their own tolerances, and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s. The 48 kHz *curve* is not required to repeat … (App. T6) | centre displaced >0.1 %, T1 or T2 outside its own tolerance at either rate, or any swept point more than 0.1 dB from the closed form **at that rate** | the T1, T2 and T4 measurements at … (App. T6) |

No characters: a band-pass has one behaviour.

**Every row above is stated at Slope = 1 section**, patch 0's setting. At
Slope = 2 sections T1, T2, T3, T5 and T6 hold unchanged (§4's Q compensation
keeps T2's width) and **only T4's slope figure doubles** — ±12 dB/oct, and
\|H(f₀/100)\| = −74.0 dB. A slope switch, not a second character.

### Tier 3 — cost and latency

**Latency: zero**, at every rate and every setting, and no option this class
offers adds any. `latency_samples` = 0, held to the measured click delay at
48 kHz and 44.1 kHz (A8; Station C's CLICK).

**Tail: the ring time, reported from the build**, because a band-pass *is* a
resonator and its tail is a function of both knobs: `ceil(4·Q·F_s/f₀)` samples
for one section, `ceil(6·Q·F_s/f₀)` for two (App. R). The surface's widest
setting — Q 32 at 20 Hz, 48 kHz — is 307 200 samples, 6.4 s, and that is the
class-level `TAIL_SAMPLES` upper bound; the instance property narrows it to
the settings in force.

**Tier 3 budget** (fraction of one stereo block's real-time deadline):
P4 ≤ 2.5 % / S3 ≤ 8 % at Slope = 1, P4 ≤ 4 % / S3 ≤ 13 % at Slope = 2. Lean
patch expected: **no** — patch 0 *is* the lean path. Basis and its
arithmetic: App. R. **Desktop-derived; neither board has been measured.**

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One `audiobiquad.Biquad` in `BAND_PASS` mode per section**, playing the
source directly — audioif's float-state biquad, not the ported Q15 one.
`frequency`, `Q` and `mix` are `synthio` block slots the kernel reads once per
chunk, so Python runs nothing per block, and the node carries the same RBJ
constant-0 dB numerator the seed measured on the stock palette (`b2 = −b0`,
`b1 = 0`; `gain_db` discarded in this mode — A14).

**Why the tier moved from stock to audioif.** Tier 1's *silence in, silence
out; the tail reaches exact zero* is **red on the stock palette**, and this
seed routed it to Gate 0 rather than working round it (A3, §5). Gate 0's
answer landed in Phase 1 — `audiobiquad`, float state with a 1e-20 flush
(`upstream-diff.md:1953`) — and on it the same probe reads **0 LSB at every
f₀/Q the surface allows**, where `synthio.Biquad` holds −1 LSB for ever at
80 Hz Q 4 (A14). It also removes A9's `Filter.c:234` divergence in
`(0, 0.01]`: this kernel crossfades with no bypass threshold
(`audioif_filter_f32.c:222-223,239`), and `mix = 0` is **byte-identical to the
source** (A14) — Tier 1's wire test, exactly.

**Steeper skirts** are a second identical section in series, with the
requested Q compensated so T2's width still holds:
**Q_used = Q_requested · √(√2 − 1) = 0.643594 · Q**. The seed's App. R says
"dividing … by √(√2 − 1)", the reciprocal, which narrows the band to 206.1 Hz
where 500.0 Hz was asked for (A14). Corrected here.

**Mix rides on both sections** — `section2.mix` is the same `m` when Slope is
on and `0` when it is off — which is what makes `mix = 0` a wire in *both*
settings. Slope off is the exact linear dry/wet `(1−m)x + m·H(x)`; Slope on is
that mixed section run twice, `((1−m)I + mH)²x`, because per-section
crossfades cannot cancel their own cross terms. The docstring says so.

**No trim macro.** The seed proposed one as a shelf pair; dropped on two
measurements (A14). A shelf is **not** bit-transparent at 0 dB (3 586 of
4 096 samples differ, up to 8 LSB), so an always-present trim node forfeits
the wire invariant; and one shelf is flat only to 0.02–0.21 dB, so the flat
version is the *pair* — two more float sections, which is where the S3 budget
goes.

*Mono:* identical filter, measured exact (A4).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None new, and the one this seed made was granted.** The ask it routed to
Gate 0 — a DC-clean biquad in an audioif-own module (A3; §5's full paragraph
in App. R) — is on the pin as `audiobiquad.Biquad`, and §4 records the
measurement that says it answers. Every Tier 2 trait is reachable on that
palette; nothing here needs a node audioif does not have.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Surface — frozen 2026-09-07

| # | Label | Mode | Engineering span | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 Hz … 16 kHz, log; clamped to `min(16 kHz, 0.4·F_s)` at the running rate | the centre-frequency knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 32, log; displayed as bandwidth f₀/Q | the bandwidth/Q knob |
| 2 | Slope | TOGGLE | 1 section (default) / 2 sections | a filter bank's skirt switch |
| 3 | Mix | UNIPOLAR | 0 … 1, linear; 0 is a byte-exact wire | a dry/wet blend, kept because Tier 1's wire test needs it |

Four macros, not the seed's five: **Trim is dropped** (§4). The 16 kHz span
top is a class constant and the `0.4·F_s` ceiling is applied per instance, so
a 22.05 kHz graph gets 8 820 Hz at the top of the knob rather than a
`ValueError`. The seed's five-macro proposal is kept verbatim in App. R.

`capabilities = ()`: nothing in a band-pass is measured in beats — the class
never reads `self._transport()` (D10, answered).

Patches, on the 0-127 grid, `(Frequency, Width, Slope, Mix)`:

| # | Name | Grid | What it is |
|---|---|---|---|
| 0 | Wide Mid | (74, 11, 0, 127) | 983 Hz, Q 0.72 — the constructor's defaults (1 kHz, Q 0.707) on the grid |
| 1 | Telephone | (81, 27, 127, 127) | 1 421 Hz, Q 1.21, 2 sections — the handset band |
| 2 | Snare Crack | (44, 42, 0, 127) | 203 Hz, Q 1.98 — a snare's body, isolated |
| 3 | Presence Window | (101, 34, 0, 127) | 4 072 Hz, Q 1.52 — the presence band a host can ride |
| 4 | Narrow Probe | (74, 118, 0, 127) | 983 Hz, Q 23.8 — a resonant probe (the seed's −6 dB trim goes with the dropped macro) |
| 5 | Sub Window | (21, 55, 127, 127) | 60 Hz, Q 3.03, 2 sections — the sub band, steep-sided |

**Latency budget 0 samples; Tier 3 budget in §3.**

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/eq.py`.

- **No surface at all.** `MACRO_LABELS = ()` (`eq.py:144`).
- **The width knob does not exist and cannot be made to exist.** `q` is …  *(argument in full: App. R)*
- **`mix` is accepted and then hidden** (taken `eq.py:101`, forwarded
  `eq.py:105`, unreachable after).
- **`set_frequency` is off-contract and it raises** — `_core.check_hz`
  raises at or above Nyquist (`_core.py:471-474`) instead of clamping,
  against the rate-honest invariant.
- **No tail is declared**, and for a resonator this is the worst place in the …  *(argument in full: App. R)*
- **Held DC at low centres** — §5.
- **`reset()` reaches one node** (`_core.py:366-374`) and the `Filter` it
  reaches resets its source recursively, so the borrowed source *is* reset,
  which the contract forbids.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions — settled 2026-09-07

1. **Gate 0's biquad answer** (§5). **Settled:** granted. Phase 1 landed
   `audiobiquad.Biquad` and the class is built on it, so the tier is
   **audioif**, `REQUIRES = ("audiobiquad",)` (§4).
2. **Width as Q or as bandwidth in octaves.** **Settled: store Q, label the
   knob *Width*, display the bandwidth f₀/Q** — the seed's own "display one
   and store the other". Q is what T2 is stated in and what the node takes;
   the octave form needs RBJ's second α and a second measurement for the same
   curve.
3. **Two identical band-passes, or a low-pass/high-pass pair.** **Settled:
   two identical band-passes.** The pair needs two macros (the seed's own
   objection) and would break T2 — two independently moving edges have no
   f₀/Q width to state — and T5, whose symmetry belongs to the band-pass
   prototype and not to an arbitrary LP/HP product. The identical pair keeps
   T1, T2, T3, T5 and T6 as stated and moves only T4's slope figure.

Nothing in §§1–7 is left open. Not settled here, and belonging to a run:
both Tier 3 budget cells (no board measured) and every Tier 2 verdict
(Station C).

## Appendix

Run 2026-09-06 on this machine. CPython target:
`audiocomponents/.venv/bin/python`. MicroPython: `cmods/bin/micropython` with
`MICROPYPATH=audiocomponents:audiocomponents/lib`. Probes were scratch
scripts, not committed; every number is reproducible from its description.
A0, A3, A5, A7 and A9 share their runs with `LowPass.md`.

### A0. The Zavalishin license, verbatim

*"© Vadim Zavalishin. The right is hereby granted to freely copy this
revision of the book in software or hard-copy form, as long as the book is
copied in its full entirety (including this copyright note) and its contents
are not modified."* Verbatim-copy-only, no derivatives — a paper for our
purposes. The PDF is not text-extractable by the fetch tool; `pypdf` read it
in two lines.

### A1. Magnitude response against the closed form (48 kHz, stereo, level 6000, `mix=1`)

```
  bp f0= 1000.0 Q=2.000 probe=   500.0  measured  -10.011 dB  ideal  -10.014 dB  dev  +0.003 dB
  bp f0= 1000.0 Q=2.000 probe=  1000.0  measured    0.002 dB  ideal    0.000 dB  dev  +0.002 dB
  bp f0= 1000.0 Q=2.000 probe=  2000.0  measured  -10.056 dB  ideal  -10.056 dB  dev  +0.000 dB
```

### A2. T1 and T2, measured

Peak gain at f₀ = 1 kHz for a wide Q sweep:

```
  Q=  0.100  measured   +0.002 dB   ideal   +0.000 dB
  Q=  0.500  measured   +0.002 dB   ideal   -0.000 dB
  Q=  0.707  measured   +0.002 dB   ideal   -0.000 dB
  Q=  2.000  measured   +0.002 dB   ideal   +0.000 dB
  Q=  8.000  measured   +0.002 dB   ideal   -0.000 dB
  Q= 30.000  measured   +0.002 dB   ideal   -0.000 dB
  Q=100.000  measured   -0.002 dB   ideal   -0.000 dB
```

−3 dB edges at the closed-form positions:

```
  Q=0.707 predicted edges   517.59 /  1932.02 (BW  1414.43 = f0/Q  1414.43)  measured -3.018 / -3.039 dB
  Q=2.000 predicted edges   780.78 /  1280.78 (BW   500.00 = f0/Q   500.00)  measured -3.021 / -3.027 dB
  Q=8.000 predicted edges   939.45 /  1064.45 (BW   125.00 = f0/Q   125.00)  measured -3.022 / -3.024 dB
```

T2's planted fault: feed the measurement a Q that is 10 % wrong and the two
crossings must move off −3 dB by more than 0.15 dB (they move by ≈ 0.5 dB at
Q 2).

### A3. Held DC after silence, and the probe design that hid it

The first version of this probe pulled a few blocks past the end of the
`RawSample`. When a `Filter`'s source is exhausted, `Filter.c:202-223` takes
the `sample == NULL` branch and **memsets the output to zero without running
the biquads at all** — every configuration read exactly 0 and the defect
looked absent. Corrected by staying strictly inside a source still supplying
digital silence (0.09 s of 440 Hz at 12 000, then 3.0 s of zeros; 287 of 289
available 1024-sample blocks). That correction is the planted fault: two
blocks longer and it goes green on a filter still holding DC.

CPython target; MicroPython identical in every row:

```
  LowPass f=100                last     -1     HighPass f=30          last     -8
  LowPass f=40 q=8             last     -4     HighPass defaults(1k)  last     +0
  LowPass defaults(1k)         last     +0     BandPass f=80 q=4      last     -1
  BandPass defaults(1k q.707)  last     +0     Notch f=60 q=8         last     -2
  Notch defaults(1k q.707)     last     +0     CombFilter defaults    last     +0
  DynamicEQ defaults           last     +0
```

**Reading it.** Of Gate 0's three candidates, a *block-rate tail gate in
Python* cannot see the residual — it lives in the biquad's sub-sample state
(`audioif_biquad.h:14`) and surfaces only as an integer offset — so it would
have to zero the output on a silence heuristic and would clip quiet material;
recommended against. A *DC-clean biquad in an audioif-own module*, decided
once with the per-sample phaser question, is what this seed recommends. A
*recorded disconfirmation* is honest and leaves up to −72 dBFS of DC in every
rest at low corners.

### A4–A7. Mono, rates, DC/Nyquist, cost

Mono matched the closed form to 0.001 dB. Gain at f₀, Q 0.707: −3.013 /
−3.011 / −3.012 dB at 48 000 / 44 100 / 22 050 Hz, and the band-pass peak
read 0.002 / −0.001 / 0.000 dB at the three rates. DC and Nyquist, f₀ 1 kHz,
Q 0.707: `BAND_PASS @10 Hz −37.07 dB, @23 000 Hz −44.34 dB` — the low figure
is the analytic `(f/f₀)/Q = 0.01414` exactly, the high figure is limited by
the probe's own quantisation floor, not by the filter. Cost: 146.6 ns per
stereo frame for one section, 195.1 ns for four, against 20 833 ns of real
time per frame.

### A8. Latency

Impulse at frame 50 through `BandPass()`: first non-zero output at frame
**50**, peak 3 068 of 20 000 (a Q 0.707 band-pass passes about a seventh of
an impulse's peak); `latency_samples` reports **0**. Agreed.

### A9. `mix` cross-target divergence

```
             CPython   MicroPython
  mix=0.0          0             0
  mix=0.005       80             0
  mix=0.01       159             0
  mix=0.02       317           317
```

`Filter.c:234` bypasses the cascade when `mix <= 0.01`; the CPython target
(`src/cpython/_audioif.c:605-613` via `src/cpython/audiofilters.py:137-147`)
has no such threshold, so below 0.02 the two interpreters are not
byte-identical.

### A10. Licence and citation audit, 2026-09-06

This seed's §2 carries the corrections themselves; this is the full
re-verification record behind them. Every source row in §2 and every URL
anywhere in this seed was re-fetched by a second agent that read none of the
first run's notes. Corrections applied in place: **S1's licence call** now
records the repository's root `LICENSE.md` (full CC BY 4.0), which the first
draft did not mention — downgraded to *licence unverified, treated as
copyleft*, because that grant is the mirror's and the chain to RBJ is unshown;
treatment unchanged. **T5 (geometric symmetry)** rested on an inference from
S1; the claim is stated outright in Zavalishin §4.6 p. 114 and is now cited
there. Per-claim page numbers added to the S4 row.
Re-verified exactly as the seed states them: RBJ's coefficient blocks and the
`α`/`w0` definitions in the `.txt`; the CCRMA pages' *"Copyright © … Julius O.
Smith III / CCRMA, Stanford University"* with **no** licence grant anywhere on
them; Zavalishin's front-matter grant (A0, verbatim, p. ii of rev. 2.1.0);
musicdsp.org's RBJ page carrying no licence, copyright or terms text at all;
native-instruments.com's copy of the book **404** (still not reached); and the
archive.org item `the-art-of-va-filter-design-rev.-2.1.2` carrying **no**
`licenseurl` and no `rights` field (metadata API, per the sources module).
**S5** re-verified independently: arXiv:2111.05592 is
*Improving the Chamberlin Digital State Variable Filter*, Victor Lazzarini and
Joseph Timoney, and the abstract page's licence link resolves to
`creativecommons.org/licenses/by/4.0` — **CC BY 4.0**, the one permissive
source in this unit, as the seed says.

**Unsourced, and flagged as such:** the dropped candidate's attributes above
(a Vox/Cry Baby-style inductor wah — a Q that falls as the sweep rises, and
inductor loss) are stated from general knowledge; no wah schematic was reached
in either run. The candidate is dropped on scope, not on those values, and
nothing in §3 rests on them.

### A11. Second licence and citation audit, 2026-09-06 (the re-fetch pass)

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

**No correction was needed to this seed on this pass.** Both Zavalishin
quotes were opened in the extracted text and are verbatim where cited:
*"By mixing the lowpass, bandpass and highpass outputs one can obtain further
filter types"* at §4.7 p. 117, and *"the result of the LP to BP substitution
has an amplitude response which is symmetric in the logarithmic frequency
scale"* at §4.6 p. 114; the split identity `H_LP + 2R·H_BP + H_HP = 1` is
equation (4.4) on p. 97. **S5 re-verified independently**: `arxiv.org/abs/2111.05592`
was reached; the title is *Improving the Chamberlin Digital State Variable
Filter*, the authors Victor Lazzarini and Joseph Timoney, the abstract does
derive *"the transfer functions describing its three basic responses,
highpass, bandpass, and lowpass"*, and the page's licence element links to
`creativecommons.org/licenses/by/4.0/` — **CC BY 4.0**, the one permissive
source in this unit, so it may be ported with attribution if it is ever
needed. T1, T2 and T4 were re-derived from S1's own coefficients and hold:
0.000 dB at f₀ for Q ∈ {0.1 … 100}, −3.02/−3.03 dB at the two predicted
edges at Q 2, −37.00 dB at f₀/100 at Q 0.707.

### A12. Trait-critic pass, 2026-09-06 — the bilinear-warp derivations

Re-derivations from S1's own coefficients at 48 kHz, Q 0.707 unless stated, in
float64 (`audiocomponents/.venv/bin/python`, numpy 2.5.2). Arithmetic on the
published formulae, not a render.

**T4, the two skirts.** Fitted slopes and the f₀/100 value:

| f₀ | low skirt f₀/8→f₀/4 | high skirt 4f₀→8f₀ | \|H(f₀/100)\| |
|---|---|---|---|
| 100 Hz | +6.005 dB/oct | −6.011 dB/oct | −36.989 dB |
| 250 Hz | +6.005 | −6.042 | −36.989 |
| 500 Hz | +6.005 | −6.157 | −36.991 |
| 600 Hz | +6.005 | −6.226 | — |
| 700 Hz | +6.006 | **−6.309** | — |
| 1 kHz | +6.005 | −6.653 | −37.001 |
| 2 kHz | +6.007 | −9.531 | −37.038 |

600 Hz is the last f₀ whose high skirt is inside −(5.7…6.3) dB/oct; the low
skirt never leaves its band, because f₀/8…f₀/4 is far from Nyquist at every
audio f₀.

**T1, re-derived.** Gain at f₀ for Q ∈ {0.1, 0.5, 0.707, 2, 8, 30, 100}:
0.0000 dB at every Q, at f₀ = 100 Hz, 1 kHz and 4.8 kHz. The constant-0 dB-peak
numerator `(α, 0, −α)` makes this exact, not approximate.

**T5, the two axes.** \|H(f₀·r)\| − \|H(f₀/r)\| on the **linear** axis:

| f₀ | r = 1.5 | r = 2 | r = 4 | r = 8 |
|---|---|---|---|---|
| 100 Hz | −0.000 dB | −0.000 | −0.002 | −0.008 |
| 500 Hz | −0.001 | −0.006 | −0.043 | −0.195 |
| 1 kHz | −0.006 | −0.025 | −0.176 | −0.824 |
| 2 kHz | −0.024 | −0.102 | −0.747 | −4.271 |
| 4.8 kHz | −0.156 | −0.680 | −7.199 | above Nyquist |

Folded about the **prewarped** centre instead — upper probe at
`f = (F_s/π)·arctan(π·r·f_a0/F_s)`, lower at the reciprocal — every one of
those cells reads **±0.0000 dB**, including f₀ = 4.8 kHz at r = 8. Sweeping r
continuously, the linear-axis 0.1 dB band survives while the upper probe stays
below roughly 0.06·F_s: r ≤ 8 at f₀ ≤ 200 Hz, r ≤ 7.17 at 400 Hz, r ≤ 3.79 at
800 Hz, r ≤ 2.26 at 1.6 kHz, r ≤ 1.61 at 3.2 kHz.

**T6, the cross-rate deviation.** Same f₀, compared against the 48 kHz
response over f ≤ 0.1·22 050 = 2205 Hz: at 44.1 kHz ≤ 0.011 dB at every f₀
from 31.5 Hz to 2 kHz; at 22.05 kHz **0.232 dB at 31.5 Hz, 0.231 at 100 Hz,
0.229 at 250 Hz, 0.219 at 500 Hz, 0.171 at 1 kHz, 0.190 at 2 kHz** — the old
row's 0.1 dB band was unreachable at 22.05 kHz at any centre. Measured against
its *own* rate's closed form the filter is exact (A1, A5).


### A13. Palette verification pass, 2026-09-07

Every §4/§5 claim about what an audioif node can and cannot do re-measured
independently; the run and its numbers are in `LowPass.md` A14, which covers
the whole simple-filter unit. What it changed here:

- **`BAND_PASS` against the closed form:** worst deviation **−0.001 dB** over
  f₀ ∈ {50, 100, 1 k, 10 k, 15 k, 20 k} Hz and probes 50 Hz…20 kHz; the peak
  is +0.0002 dB from 0 dB for Q 0.1, 0.5, 1, 4 and 16, and −0.0017 dB at
  Q 100 with the source dropped to 600 for headroom. §4's figures stand and
  are conservative. `audioif_biquad.c:83` reads as §4 quotes it.
- **A3's −1 LSB at `BandPass(80 Hz, q=4)` and exact zero at the 1 kHz default
  reproduced**, same probe, same 287 blocks. §5's DC-canary argument stands:
  at 1 kHz the settled output is bit-exact zero, so any non-zero reading is
  unambiguously arithmetic.
- **Trim cannot fold into the biquad's `b` coefficients** — no route from
  Python, and `A` is discarded outside the shelf and peaking modes (measured).
  §4 now names the shelf pair.
- **A new cross-target divergence**, recorded in §4: `mix` strictly between 0
  and 1 over a two-biquad cascade renders different bytes on MicroPython and
  CPython. Not in `audioif/docs/upstream-diff.md`; it needs an audioif issue.
- **The stock-CircuitPython citation was pointing at the wrong column** and is
  corrected in §4.
- **No node ask survives or arises here.** §5's "None" stands.

### A14. Class-builder pass, 2026-09-07 — the palette move and the surface

Run on this machine at branch `effects/p2-bandpass`, interpreter
`audiocomponents/.venv/bin/python` (CPython 3.12, audioif pin `2f6cbc3`,
numpy 2.5.2), 48 000 Hz, stereo, `audiobiquad` unless the row says otherwise.
Every number below is from this run; the probes are scratch scripts and each
row states what reproduces it.

**1. `mix = 0` is a byte-exact wire.** 440 Hz at level 12 000, 4 096 samples
compared against the same source rendered alone:

```
mix=0  compared 4096 samples, differing 0, max |d| 0
```

Tier 1's wire test, met exactly, and it is the reason Mix stays on the
surface. `audioif_filter_f32.c:222-223,239` is a straight crossfade
(`dry = 1.0f - mix`; `out[index] = to_s16(dry * x0 + mix * y0)`) with **no
`mix <= 0.01` bypass**, so A9's cross-target divergence does not arise on this
node.

**2. The held-DC residual is gone.** A3's probe, unchanged — 0.09 s of 440 Hz
then 3.0 s of zeros, read strictly inside a source still supplying silence,
peak over the last 1 024 frames:

```
dc  f0=80      q=4     last-1024-frame peak 0 LSB
dc  f0=1000    q=0.707 last-1024-frame peak 0 LSB
dc  f0=40      q=8     last-1024-frame peak 0 LSB
dc  f0=20      q=32    last-1024-frame peak 0 LSB
```

A3 read −1 LSB at `f0=80 q=4` on `synthio.Biquad` and reproduced it again in
A13. On `audiobiquad` every one of the four is exact zero, including the
corner of the frozen surface (Q 32 at 20 Hz).

**3. The trim stage is not bit-transparent at 0 dB.** A single `HIGH_SHELF`,
`gain_db = 0`, against its own source:

```
shelf 0 dB corner 5: differing 3586 of 4096, max |d| 8
shelf 0 dB corner 20: differing 2784 of 4096, max |d| 6
```

and a single shelf is not flat enough to be a trim on its own — worst
deviation from the requested gain over 20 Hz…20 kHz, from the node's own
`coefficients`:

```
shelf corner 2     gain  -12.0 dB: worst deviation 0.1673 dB
shelf corner 5     gain  -12.0 dB: worst deviation 0.0246 dB
shelf corner 5     gain   -6.0 dB: worst deviation 0.1663 dB
shelf corner 10    gain  -12.0 dB: worst deviation 0.8601 dB
shelf corner 20    gain  -12.0 dB: worst deviation 6.0402 dB
```

Both readings point the same way: an always-present trim node costs the wire
invariant, and the flat version is the *pair*, two more sections. Trim is
dropped (§4, §6).

**4. Desktop cost, like for like.** Two seconds of audio per row, one build
per row, ns per stereo frame against the 20 833 ns real-time budget:

```
audiofilters.Filter(filter=None)           19.8 ns/stereo frame   0.10 %
stock synthio.Biquad in a Filter           36.2 ns/stereo frame   0.17 %
audiobiquad.Biquad x1                      61.0 ns/stereo frame   0.29 %
audiobiquad.Biquad x2                      90.0 ns/stereo frame   0.43 %
```

These are **not** comparable with A7's 146.6 ns — a different session on a
different machine state — which is why the stock build was re-measured here
beside the new one. The ratio, 1.69× and 2.49× over the stock single section,
is what §3's Tier 3 budget scales the seed's figures by.

**5. The seed's Q compensation is a reciprocal out.** −3 dB edges located by
bisection on S1's closed form, `k = √(√2 − 1) = 0.643594`, `1/k = 1.553774`:

```
f0=1000  Q=2   want BW  500.00 | 1 sect  497.22 | 2 sect Q*k  497.39 | 2 sect Q/k  206.09
f0=200   Q=2   want BW  100.00 | 1 sect   99.75 | 2 sect Q*k   99.78 | 2 sect Q/k   41.33
f0=1000  Q=8   want BW  125.00 | 1 sect  124.34 | 2 sect Q*k  124.39 | 2 sect Q/k   51.52
f0=60    Q=3   want BW   20.00 | 1 sect   19.95 | 2 sect Q*k   19.96 | 2 sect Q/k    8.27
```

`Q·k` reproduces the single-section width to better than 0.6 %; `Q/k`, which
is what App. R's sentence says, narrows the band to 41 % of it. The class
multiplies. App. R's sentence is left standing with this note beside it.

**6. `gain_db` is discarded in `BAND_PASS` mode**, so a trim cannot be folded
into the band-pass section's own coefficients — the seed's A13 finding,
re-confirmed on the new node:

```
gain_db 0.0  ['0.031600378', '0.000000000', '-0.031600378', '-1.920229673', '0.936799228']
gain_db 6.0  ['0.031600378', '0.000000000', '-0.031600378', '-1.920229673', '0.936799228']
gain_db 12.0 ['0.031600378', '0.000000000', '-0.031600378', '-1.920229673', '0.936799228']
```

`b2 = −b0` and `b1 = 0`: RBJ's constant-0 dB-peak numerator, as §1 states it.

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

Two already carry Phase 0 measurements. **Byte-identity is green** except for
`mix` in `(0, 0.01]`, where `Filter.c:234` bypasses the cascade on
MicroPython while the CPython target blends (A9) — §6 keeps the macro out of
that band. **Exact zero after silence is red at low centres**:
`BandPass(frequency=80.0, q=4.0)` holds −1 LSB for ever on both interpreters,
while the 1 kHz default reaches exact zero (A3). Routed to Gate 0, §5.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* (plain text, shepazu mirror) | the BPF (constant 0 dB peak gain) coefficients, `α = sin(w0)/(2Q)`, `w0 = 2π f0/Fs`, and *"the bandwidth in octaves (between −3 dB frequencies for BPF and notch)"*, verbatim | the `.txt` itself carries **no license, copyright or warranty line** (re-verified 2026-09-06, all five terms searched) — but the repository serving it does: its root `LICENSE.md` is the full **CC BY 4.0** text (read at https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/LICENSE.md; GitHub's own licence API reports the repo as `NOASSERTION`). That is the *mirror's* grant, not RBJ's: the mirror's HTML rendering says only *"Adapted from Audio-EQ-Cookbook.txt, by Robert Bristow-Johnson, with permission"*, so the chain to the author is **not** shown (sources module: a repackager's label is an assertion). **License unverified — treated as copyleft:** read as a document for its mathematics, never ported | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Quality Factor (Q)", "Decay Time is Q Periods" | *"Q … resonance frequency divided by the resonator bandwidth"*; the envelope reaches e^{−π} in Q periods | © J. O. Smith III / CCRMA Stanford; no license granted. Read as a paper | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html , …/Decay_Time_Q_Periods.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP mirror, text via `pypdf`) | the SVF's simultaneous LP/BP/HP outputs and linear-mix property (§4.7 p. 117, verbatim; the split identity `H_LP + 2R·H_BP + H_HP = 1` at §4.1 p. 97); the log-scale symmetry of the LP→BP substitution (§4.6 p. 114); R as damping and `Q = 1/2R` (§4.2 p. 100, and its n. 2) | verbatim-copy-only, no derivatives (grant quoted in A0). Read as a paper | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |
| **S5** Lazzarini & Timoney, *Improving the Chamberlin Digital State Variable Filter*, arXiv:2111.05592 | context on the SVF's LP/BP/HP transfer functions and their known defects | **CC BY 4.0** — permissive; portable if ever needed | https://arxiv.org/abs/2111.05592 | 2026-09-06 |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **0 dB peak, at every Q**: the gain at f₀ is 0.00 dB ± 0.05 for every Q from 0.1 to 100 — narrowing the band does not change the level of what passes | S1 ("constant 0 dB peak gain" form); measured 0.002 dB across Q 0.1…100 (A2) | high | any Q in 0.1…100 whose gain at f₀ is more than 0.05 dB from 0 | steady-state sine at f₀ for Q ∈ {0.1, 0.5, .707, 2, 8, 30, 100} |
| T2 | **Width is f₀/Q**: the −3 dB points sit at `f₀·(√(1+1/4Q²) ∓ 1/2Q)`, so their difference is exactly f₀/Q — at f₀ 1 kHz, Q 2 that is 780.8 Hz and 1280.8 Hz | S3 (Q = f₀/bandwidth), S1 (bandwidth is *between −3 dB frequencies for BPF and notch*); measured −3.02 dB at both predicted edges for Q ∈ {0.707, 2, 8} (A2) | high | either predicted edge reading outside −3.0 ± 0.15 dB, for any Q in 0.5…16 | swept sine; the two −3 dB crossings located by interpolation and compared with the closed form |
| T3 | **Exact zeros at DC and Nyquist**: the numerator `(α, 0, −α)` vanishes at `z = ±1`, so a DC offset and a Nyquist-rate alternation both produce exactly zero, at every f₀ | S1 (BPF numerator), verified analytically | high | a settled output that is not bit-exactly zero for a held DC offset, at any f₀ ≥ 20 Hz | DC step, and a ±FS alternating sequence, each read while the source still supplies it |
| T5 | **Geometric symmetry — about the *prewarped* centre**: folded about f_a0 on the bilinear-warped axis `f_a = (F_s/π)·tan(πf/F_s)`, the response at f_a0·r equals the response at f_a0/r to **0.00000 dB** for every r in 1…8 and every f₀ from 20 Hz to 0.1·F_s — the symmetry is exact, on the right axis. Folded about f₀ on the *linear* axis it holds within 0.1 dB only while the upper probe f₀·r stays below about 0.06·F_s (≈ 2.9 kHz at 48 kHz): at f₀ = 1 kHz, r = 8 the two sides differ by 0.824 dB, and at f₀ = 0.1·F_s r = 8 is above Nyquist and cannot be probed at all — which is what the old "f₀ ≤ 0.1·F_s" qualifier hid | S4 §4.6 p. 114, verbatim: *"the result of the LP to BP substitution has an amplitude response which is symmetric in the logarithmic frequency scale"*; S1 for the digital coefficients; both axes re-derived from S1 in A12 | high (was medium; the warped-axis form is exact, so the confidence is no longer hedged) | on the warped axis, any r in 1…8 at any f₀ ≤ 0.1·F_s where the two gains differ by >0.05 dB; on the linear axis, any r whose upper probe is below 0.06·F_s and whose two gains differ by >0.1 dB | swept sine, response resampled onto log(f_a/f_a0) and folded about 0; the linear-axis half repeated at f₀ ∈ {100, 250} Hz |
| T6 | **Rate-honest — against the closed form at the running rate, not against the 48 kHz curve**: at 44.1 kHz and 22.05 kHz the centre stays at f₀ within 0.1 %, T1's 0 dB peak and T2's f₀/Q edges hold to their own tolerances, and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s. The 48 kHz *curve* is not required to repeat: at 22.05 kHz the same f₀ sits up to 0.23 dB from its 48 kHz shape even below 2205 Hz, at every f₀ from 31.5 Hz to 2 kHz — so the old 0.1 dB cross-rate band was unreachable at any centre, and reaching it would mean the filter was wrong at one of the two rates | S1 (the BLT prewarps f₀ at whatever rate is running); measured at three rates (A5); the cross-rate deviation re-derived in A12 | high | centre displaced >0.1 %, T1 or T2 outside its own tolerance at either rate, or any swept point more than 0.1 dB from the closed form **at that rate** | the T1, T2 and T4 measurements at 48 000 / 44 100 / 22 050 Hz, each differenced against its own closed form |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Standout confirmed.** The candidate weighed and dropped was a **wah
pedal's inductor band-pass** (a Vox/Cry Baby-style network): it is a real
circuit with real values, but its distinguishing traits — a fixed Q that
falls as the sweep rises, and an inductor's loss — are a *wah*, and this
program has no `Wah` class among the frozen 46 while `BandPass` is a utility
filter a host sweeps. Naming it would import traits this class must not have.
Design grade stands; Tier 2 is stated anyway because it is free and
falsifiable.

*(from §2)*

**Independent licence and citation audit, 2026-09-06** (a second agent, none
of the first run's notes read; full record in Appendix A10). Corrections
applied above: **S1's licence call** now records the root `LICENSE.md` (full
CC BY 4.0) the serving repository carries — downgraded to *licence unverified,
treated as copyleft* because that grant is the mirror's and the chain to RBJ
is unshown; treatment unchanged. **T5** rested on an inference from S1; the
claim is stated outright at Zavalishin §4.6 p. 114 and is now cited there.
**S5** was re-verified independently and stands: arXiv:2111.05592's licence
link resolves to `creativecommons.org/licenses/by/4.0`. The dropped wah
candidate's attributes are **unsourced** general knowledge — no wah schematic
was reached; the candidate is dropped on scope, not on those values.

*(from §2)*

**Second licence-and-citation audit, 2026-09-06** (a third pass, independent
of the first audit; **every URL in this seed re-fetched in this run**). **No
correction was needed to this seed.** The S1 and S4 calls are re-confirmed
unchanged; both Zavalishin quotes are verbatim where cited (§4.7 p. 117 and
§4.6 p. 114); and **S5 re-verified independently** — arXiv:2111.05592's own
licence element links to `creativecommons.org/licenses/by/4.0/`, so **CC BY
4.0** stands and it is the one portable source in this unit. Full record, with
every quote and status code, in `A11`.

*(from §3)*

**Trait-critic pass, 2026-09-06.** T4, T5 and T6 rewritten in place for the
root defect shared across this family: the *analog* prototype's log-axis
properties were stated as though digitisation preserved them at every f₀, and
the bilinear warp does not. T4 now separates the two skirts (the low one is
robust everywhere, the high one is not); T5 states the symmetry about the
prewarped centre, where it is exact; T6 is measured against the closed form at
the running rate rather than the 48 kHz curve — a band it could not have met at
any centre. Figures re-derived from S1's coefficients in A12; no row deleted.
T1, T2 and T3 unchanged (T1 re-derived as exactly 0.0000 dB at f₀ for every Q
in 0.1…100). **Six Tier 2 rows after the pass.**

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 1.5 %, ESP32-S3 ≤ 5 %** for the single section, **≤ 2.5 % / ≤ 9 %** for the
two-section (steeper skirts) setting. Lean patch expected: **no**. Basis:
76 instructions per sample per biquad on Cortex-M4/M7
(`audioif/docs/upstream-diff.md:1172`); desktop anchor 147 ns per stereo
frame against a 20 833 ns budget, +16 ns per extra section (A7).

*(from §3, the tail derivation and the Tier 3 budget's arithmetic, added
2026-09-07 with the frozen surface)*

**The tail.** One RBJ band-pass section is a two-pole resonator whose
envelope decays with a time constant of `Q·F_s/(π·f₀)` samples (S3: the
envelope reaches e^(−π) in Q periods). From a full-scale burst, the output
reaches half an int16 LSB — −96 dBFS — after `ln(65536) = 11.09` time
constants, i.e. `3.53·Q·F_s/f₀` samples; `4·Q·F_s/f₀` is that rounded up, and
is the seed's own figure. Two cascaded sections share the pole pair, so the
envelope is `t·e^(−t/τ)` rather than `e^(−t/τ)` and reaches the same floor
about 1.5 time constants later: `6·Q·F_s/f₀`, again rounded up. Both are
upper bounds and the kit's TAIL goes red only when the *measured* tail
exceeds the declared one, never when it undershoots.

**The Tier 3 budget's arithmetic.** The seed's stock-palette budget was
P4 ≤ 1.5 % / S3 ≤ 5 % for one section and P4 ≤ 2.5 % / S3 ≤ 9 % for two. A14
measured, on one machine in one run, 36.2 ns per stereo frame for the stock
build, 61.0 ns for one `audiobiquad` section and 90.0 ns for two — 1.69× and
2.49× the stock single section. Applying those ratios to the seed's
single-section cells gives P4 ≤ 2.5 % / S3 ≤ 8.5 % and P4 ≤ 3.7 % /
S3 ≤ 12.4 %, rounded in §3 to ≤ 2.5 % / ≤ 8 % and ≤ 4 % / ≤ 13 %. A desktop
ratio is not a board measurement and the budget is not a result: the P4 and
S3 columns of the evidence pack are empty until the board run fills them.

*(from §3)*

**Latency: zero.** Nothing looks ahead; `latency_samples` is 0 at every rate
and setting and **no option this class offers adds any**. Measured: impulse
at frame 50 in, frame 50 out, peak 3 068 of 20 000 (A8). `tail_samples` is
declared from the ring time: a band-pass *is* a resonator, so the tail is
`ceil(4·Q·F_s/f₀)` and at Q 30 / 200 Hz that is nearly 30 000 samples — a
number the class must report honestly rather than leave at `None`.

*(from §4)*

*Steeper skirts* are a second identical `Biquad` in the same cascade — two
cascaded band-passes give ±12 dB/oct and a narrower −3 dB width, and the
class compensates by dividing the requested Q by √(√2 − 1) so T2's stated
width still holds; that compensation is a construction-time float, no table.
*Mix* is `Filter`'s own slot (`Filter.c:232`), clamped away from `(0, 0.01]`.
*Trim* is a `LOW_SHELF` + `HIGH_SHELF` pair at one corner sharing one `A`,
appended to the same cascade — flat to 0.002 dB from 50 Hz to 15 kHz over
−6…+12 dB (`LowPass.md` A14), stock, one float store per shelf. It cannot
fold into the band-pass section's own coefficients: `synthio.Biquad` exposes
only `mode`, `frequency`, `Q` and `A`
(`audioif/src/synthio/Biquad.c:228-233`) and `A` is read only when
`mode >= PEAKING_EQ` (`:82-83`), so in `BAND_PASS` mode it is discarded.
*Mono:* identical filter, measured exact (A4).

*(from §4)*

**One palette hazard the rebuild must document.** `Filter`'s `mix` blends the
source against the **whole cascade's** output on MicroPython/CircuitPython
(`audioif/src/audiofilters/Filter.c:279-283` then `:288`) and against the
**last stage's input** on the CPython target
(`audioif/src/cpython/audiofilters.py:140`). One biquad at any `mix`, and any
cascade at `mix` 0 or 1, agree byte for byte; two biquads at `mix = 0.5`
render different bytes on the two desktop targets (`LowPass.md` A14) — which
is Steeper Skirts with the Mix macro off its ends, and breaks Tier 1's
identical-bytes invariant as §6 proposes the surface. Either the mixed stage
stays single or the divergence is fixed in audioif. A palette defect, not a
class defect.

*(from §4)*

**Portability tier: stock.** A *stock CircuitPython* board runs upstream's
Q15 biquad, where low-centre coefficients quantise badly — upstream's own
measured numbers are a `LOW_PASS` at 100 Hz reading −3.94 dB at its corner and
a `HIGH_PASS` at 30 Hz reading +9.03 dB
(`audioif/docs/upstream-reports/biquad-band-edges.md:145-147`), and the
stock-board note is `audioif/docs/upstream-diff.md:1223-1226`. The much worse
"before" column at `upstream-diff.md:1111-1121` is *this port's* pre-fix
arithmetic, not upstream's — `:1127-1135` disowns it in terms. Either way
T1–T4 hold only above a few hundred hertz on such a board. Documented on the
class, not fixed by it.

*(from §5)*

One **Tier 1** item is red and is routed to Gate 0 rather than asked here:
the held-DC residual (audioif#23), which for this class shows as −1 LSB at
`BandPass(80 Hz, q=4)` and 0 at the 1 kHz default (A3). It is worth noting
that T3 makes the band-pass the *sharpest* test of that residual in the whole
family — a band-pass has an exact zero at DC by construction, so **any**
settled non-zero output is unambiguously the arithmetic and not the design.
The kit should use `BandPass` as the family's DC canary for that reason.
Recommendation and reasoning: A3.

*(from §7)*

- **The width knob does not exist and cannot be made to exist.** `q` is
  passed to `synthio.Biquad` as a bare float (`eq.py:104`) while `frequency`
  gets a block (`eq.py:102-103`) — for a band-pass, whose entire second
  control *is* Q, that is the class's central omission, not a detail.

*(from §7)*

- **No tail is declared**, and for a resonator this is the worst place in the
  family to leave `TAIL_SAMPLES = None` (`_core.py:141`): a Q 30 band-pass
  rings for the better part of a second.

*(from §6, the seed's proposed surface, superseded 2026-09-07 by the frozen
surface in §6 — kept here in full)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 Hz … min(16 kHz, 0.4·F_s), log | the centre-frequency knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 32, log; displayed as bandwidth f₀/Q | the bandwidth/Q knob |
| 2 | Slope | TOGGLE | 1 section (default) / 2 sections | a filter bank's skirt switch |
| 3 | Mix | UNIPOLAR | 0 exactly … 1; values in (0, 0.01] snap to 0 | a dry/wet blend, kept because Tier 1's wire test needs it |
| 4 | Trim | BIPOLAR | −12 … +12 dB, default 0 | make-up for a narrow band |

`capabilities = ()`: nothing in a band-pass is measured in beats (D10,
answered).

Patches: 0 **Wide Mid** (1 kHz, Q 0.707, 1 section — the constructor's
defaults on the grid), 1 **Telephone** (1.4 kHz, Q 1.2, 2 sections),
2 **Snare Crack** (200 Hz, Q 2, 1 section), 3 **Presence Window** (4 kHz,
Q 1.5, 1 section), 4 **Narrow Probe** (1 kHz, Q 24, 1 section, −6 dB trim),
5 **Sub Window** (60 Hz, Q 3, 2 sections).

*(from §4, on the seed's Q compensation)*

The seed's sentence reads "the class compensates by dividing the requested Q
by √(√2 − 1)". Measured in A14, that is the reciprocal of what the cascade
needs: dividing narrows the −3 dB width to 41 % of the requested one, and the
class **multiplies** by √(√2 − 1) = 0.643594. The sentence stands above as
written; the correction is §4's.

*(from §3, T4's source and measurement cells, moved under the length rule)*

**Source:** S1, derived analytically; measured −37.07 dB (A6); both spans
re-derived from S1 in A12. **Measurement:** swept sine, low skirt fitted
f₀/8…f₀/4 at f₀ ∈ {100, 500, 1 k, 2 k} Hz, high skirt fitted 4f₀…8f₀ at
f₀ ∈ {100, 250, 500, 600} Hz, and the whole sweep differenced against the
closed form at f₀ ∈ {1 k, 2 k} Hz.
