# Effects Dossier — `DynamicEQ` (no historical standout — design grade)

**Class:** rebuilt as `lib/audioeffects/rebuilt/dynamiceq.py`. The old
`lib/audioeffects/eq.py` class is read once, for §7, and stands untouched
beneath.
**Family / phase:** EQ, roadmap Phase 2 · **Grade:** design ·
**Standout:** none, per vision §4.2 — confirmed (§2)
**Portability tier:** **audioif** — `REQUIRES = ("audiobiquad",
"audiodynamics", "audioroute")`, plus the stock `audiofilters.Filter` guard
and `audiomixer.Mixer`.
**Status:** traits frozen 2026-09-07, before the rebuild. Evidence:
[`DynamicEQ-evidence.md`](DynamicEQ-evidence.md).

## 1. The circuit, in one paragraph

A dynamic EQ is an equaliser band whose gain is driven by a detector watching
that same band, so the band moves only when something in it crosses a
threshold — S6's *"selective compression/expansion … kicking in only when the
signal you're EQing goes above a certain threshold at the frequency you've
selected"*, with *"width ('Q'), gain, range, threshold, attack, and release"*
per band (the quotations in full, and the distinction S6 draws from a
multiband compressor, are in **App. R**). The signal path has no
nonlinearity; the only one is the detector's gain law. The topology is the
**exactly complementary split** — band-pass at (f₀, Q) down one branch, notch
at the same (f₀, Q) down the other, process the band, sum — and it needs no
trimming, because RBJ's two numerators sum to their shared denominator, so
`H_notch + H_bandpass ≡ 1` for all z (S1, both blocks verbatim; Zavalishin's
`H_N = 1 − H_BP1`, S4 §4.7 p. 119; the arithmetic in **App. R**). Idle, the
processor is a wire; working, the composite is a bell of exactly the
detector's gain reduction, centred on f₀.

## 2. Sources and license calls

Each row's full reading and licence text is in **App. S**; the three audit
passes behind them are **App. A9** and **App. A10**.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae …* | the notch and BPF (0 dB peak) coefficients | unverified — treated as copyleft | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* | *"Q … resonance frequency divided by the resonator bandwidth"* | no grant; read as a paper | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* 2.1.0 | `H_N = 1 − H_BP1` (§4.7 p. 119) | verbatim-copy-only; read as a paper | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |
| **S6** Waves, *How and When to Use Dynamic EQ* | the definition and control set of §1 | all rights reserved; terminology only | https://www.waves.com/how-and-when-to-use-dynamic-eq | 2026-09-06 |
| **S7** Fontana & Karjalainen, DAFx-01 | magnitude-complementary structures; **context only** | no rights line in the PDF; copyleft | https://www.dafx.de/paper-archive/2001/papers/fontana_a.pdf | 2026-09-06, via `pypdf` |

Two audit corrections are applied above (S1's licence, S7's reachability) and
one in §3: the Waves page never uses the word *ratio* — that is the node's
(`audioif_dynamics.h:65`). Not reached: MDPI's *All About Audio
Equalization* (403, twice). **Standout confirmed none:** the candidate was
the dbx 902, which the vision gives to `DeEsser`.

## 3. Traits — fixed before measurement

Frozen 2026-09-07, before a line of the rebuild was written.

### Tier 1 — invariants

The standard block, verbatim from vision §3, is **App. I**, with its one
class-specific note: this class builds a splitter, two filters, a gain cell
and a mixer, so `reset()` and `deinit()` are the invariants with teeth.

### Tier 2 — circuit traits

Each row's source reading, worked numbers and confidence reasoning are in
**App. T**.

| # | Trait (falsifiable as stated) | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|
| T1 | **The split is exact**: detector idle, the processor is a wire — reconstruction within 0.05 dB from 20 Hz to 0.4·F_s, impulse out at its input peak | high | any reconstruction error above 0.05 dB with the detector below threshold, at any f₀ in 100 Hz…10 kHz and Q in 0.5…8 | fixed sines at threshold 0 dBFS ratio 1, differenced against a wire; plus an impulse peak |
| T2 | **The band gain is the compressor law, knee 6 dB wide**: composite `−(L−T)(1−1/R)` dB within 1 dB for `L−T ≥ 3`; `−(1−1/R)(L−T+3)²/12` inside the knee; exactly 0 for `L−T ≤ −3`. On the threshold at R 4 that is −0.56 dB, not 0 | high | any of the **five** probe levels more than 1 dB from the law that applies there | steady sine at f₀ at L ∈ {−41, −30, −21, −10, −4} dBFS, read after the detector settles; −30 is the knee probe |
| T3 | **Below threshold it is a wire**: a tone at f₀ 10 dB under the threshold passes within 0.05 dB of unity | high | more than 0.05 dB on a tone 10 dB below threshold | the T2 sweep's lowest level |
| T4 | **Out of band is untouched while the band works**: a tone two octaves from f₀ moves by less than 0.2 dB whether the band is idle or 19 dB down | high | more than 0.2 dB of movement out of band between the two states | a tone at f₀/8 at a level that leaves the band idle and one that drives it hard |
| T5 | **The band gain is affine in the band-pass's own response, and the bell is far narrower than f₀/Q**: the detector reads that branch, so the reduction is T2's law at `L + \|H_bp(f)\|_dB`. Worked at f₀ 3 kHz, Q 2, T −30, R 4, L −10 dBFS the half-depth width is **608 Hz against f₀/Q = 1500** (App. A11) | high | any probe in f₀/8…4f₀ more than 0.5 dB from the closed form built from S1 and T2 | steady sine **one frequency at a time at a fixed level**, f ∈ {1 k, 1.5 k, 2 k, 2.5 k, 3 k, 3.6 k, 4.5 k, 6 k}. Never a sweep: a sweep moves the detector while it measures |
| T6 | **A dry/wet blend and a band-range limit are the same control**: the class is `1 + m·B·(g−1)`, so the composite at f₀ is `20·log10((1−m) + m·g₁)`, the deepest cut reachable at blend m is `−20·log10(1−m)` dB, and out of band nothing moves as m sweeps | high | a composite at f₀ more than 0.2 dB from that closed form at any m ∈ {0, ¼, ½, ¾, 0.9, 1}, or more than 0.05 dB of out-of-band movement across the sweep | the same steady tone at f₀ at six blends, point by point; a tone at f₀/8 at three |

No characters: one band, one behaviour. A second band is a second instance.

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 8 %, ESP32-S3 ≤ 25 %**, unchanged. **Lean patch expected: no, and one is
not possible** (D2). Desktop anchor, `tools/measure_effect_cost.py`,
256-frame stereo blocks at 48 kHz, five interleaved repeats of each build:
the rebuild is **1.458–1.560 ms/block, 27–29 % of real time**, against the
shipped class's **1.100–1.154 ms/block, 21–22 %**. **The rebuild is about
45 % more expensive per block**, and it is buying three nodes the shipped
class does not have: the guard, the third splitter tap and the identity tail.
The board budget is what governs; App. A13 carries the run and the warning
about taking a desktop figure off a shared machine.

**Latency: zero**, and **no option on this class adds any** —
`audiodynamics`' `lookahead_ms` is the only one that could and is not
exposed, so there is no millisecond figure to name. `tail_samples` is
declared `4·Q·F_s/f₀ + 1`; the pole pair's worst measured ring is 3.21
periods of `Q/f₀` across both spans (App. A13), so it is long, never short.

## 4. Modeling approach on the palette

    source -> guard -> Splitter(taps=3)
                         tap 0 -----------------------------> dry   voice 0
                         tap 1  Biquad NOTCH ---------------> notch voice 1
                         tap 2  Biquad BAND_PASS -> Dynamics -> band voice 2
                                                        Mixer -> output

**`audiobiquad`, not `audiofilters`** — the seed mapped the ported node and
the palette has had the float one since Phase 1. It matters twice: the
reconstruction measures **0.0000 dB** against the ported node's 0.015, and a
low band reaches **exact zero** after silence where a Q12 biquad holds
1–4 LSB for ever (audioif#23). Both measured (App. A12, §8 D1).

**A guard in front of the splitter.** `audioif_splitter.c:35-38` drags an
unread tap's cursor forward when the writer laps the 8192-frame ring and
`RawSample.get_buffer()` hands its whole array back in one call, so an
impulse inside a 40 000-frame probe reaches this class as **silence**. An
`audiofilters.Filter(filter=None, mix=1)` at 256 frames removes that, and its
`reset_buffer` does not touch its source — which is what keeps the borrowed
source untouched by `reset()`.

**Every parameter is live**, and Frequency and Width reach both sections from
one place, so the branches cannot drift out of complement. **Mix is the Range
control** (T6, D4), so the class ships one knob and not two. **`expand=True`
is a build, not a knob**: `audiodynamics` fixes its mode at construction and
an unused second detector would cost a full block every block; neither
direction boosts (D6). **Mono:** every node honours `channel_count` 1 and the
Splitter duplicates a mono frame across its ring
(`audioif_splitter.c:30-31`).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**One**, and it is Tier 3's escape valve rather than a trait's.
**N-DEQ-1 — a gain reduction a filter can read.** `audiodynamics` reports its
gain reduction only through `gain_reduction_db()`, a method; nothing turns it
into a `synthio` block input, and `audiobiquad.Biquad`'s `gain_db` accepts
one. So the textbook "moving bell" — a `PEAKING_EQ` section whose `A` is
driven from a sidechain detector — cannot be built here at all: it needs
Python once per block, and nothing in the pull model calls Python per block.
All six Tier 2 traits are reachable without it.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Surface — as built

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 30 Hz … 16 kHz, log, clamped to 0.4·F_s | the band's frequency knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 12, log; **displayed as Q** (§8 D5) | the Q knob (S6) |
| 2 | Threshold | UNIPOLAR | −60 … 0 dBFS | the threshold knob (S6) |
| 3 | Ratio | UNIPOLAR | 1 … 20, log | the ratio knob (the node's) |
| 4 | Attack | UNIPOLAR | 0.1 … 100 ms, log | the attack knob (S6) |
| 5 | Release | UNIPOLAR | 5 … 1000 ms, log | the release knob (S6) |
| 6 | Mix | UNIPOLAR | 0 … 1; **also the Range knob** — deepest move `−20·log10(1−Mix)` dB | the range/depth knob (S6), and parallel processing |
| 7 | Listen | TOGGLE | off / the processed band alone | the band-solo button |

Eight macros. `capabilities = ()`: attack and release are absolute times, not
beat fractions, and nothing here is measured in bars — the class never reads
`transport()` (D10, answered). `expand` and `patch` are constructor
arguments, not macros.

Patches, all at mix 1 but the last: 0 **Wide Band** (the constructor's
defaults on the grid — 3 kHz, Q 2, −30 dBFS, 4:1, 2 ms, 80 ms), 1 **Boxiness
Control** (400 Hz, Q 2.5, −24 dBFS, 3:1, 10 ms, 150 ms), 2 **Harshness
Control** (3.2 kHz, Q 3, −28 dBFS, 4:1, 1 ms, 60 ms), 3 **Low End Tamer**
(80 Hz, Q 1.2, −20 dBFS, 4:1, 20 ms, 250 ms), 4 **Sibilance** (7 kHz, Q 4,
−30 dBFS, 8:1, 0.2 ms, 40 ms), 5 **Half Measure** (3 kHz, Q 1, −34 dBFS,
6:1, 5 ms, 200 ms, **mix 0.5** — the same band held to a 6 dB ceiling).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/eq.py`; the evidence pack's §10 says what
the rebuild does instead of each.

- **No surface at all**, on the class with the most to expose:
  `MACRO_LABELS = ()` (`eq.py:231`) against S6's six per-band controls, and
  **nothing is live** — `frequency`, `threshold_db`, `ratio`, `q` are
  constructor arguments only (`eq.py:235-236`) and the biquads take bare
  floats (`eq.py:240`, `:243`).
- **Attack and release are hard-coded** at 2 ms and 80 ms (`eq.py:248`); there
  is **no range and no direction** — `DYN_EXPAND` is one argument away
  (`eq.py:247`) and never offered.
- **The Mixer is built at a 1024-byte buffer** (`eq.py:250`) while both
  Filters use `_core.pcm()`'s 2048 (`_core.py:64`).
- **`reset()` and `deinit()` reach the Mixer only** (`_core.py:366-374`,
  `:376-385`): the Splitter, both Filters and the Dynamics are neither.
- **No tail is declared** (`TAIL_SAMPLES = None`, `_core.py:141`) although the
  class holds two resonators.
- **It is built on the Q12 ported biquad**, so the split reconstructs to
  0.015 dB and a low band would hold DC for ever.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions — settled

All five of the seed's, from runs in this worktree
(`tools/phase2_probes/dynamiceq_opens.py`); one new one is opened.

**D1. Does a low band inherit the family's DC residual? No — 0 LSB.** Burst
then 3 s of silence, residual over the last 4800 frames: **0 LSB at 60, 80,
120, 400 and 3000 Hz**. `audiobiquad`'s float state is flushed to exact zero
below 1e-20, so audioif#23 does not touch this class at any band.

**D2. Is the lean patch acceptable, and what does it cost? There cannot be
one.** A patch only moves macros and every node here runs every block whatever
the macros say. The seed's lean idea is a different *build* and is not
buildable on this palette — node ask N-DEQ-1. If the S3 misses its 25 %, the
answer is that ask; the board leg is the board run's.

**D3. The Fontana & Karjalainen paper.** Stale, and closed: §2 records it
reached and read (S7) in two independent passes.

**D4. Range on the Mixer's level, or on the Dynamics' ratio? Neither —
Range *is* Mix.** With `H_notch + H_bp ≡ 1` the class is `1 + m·B·(g−1)`, so
a blend against the dry input and a ceiling on the band branch are the same
number. Measured: the composite at f₀ tracks `20·log10((1−m) + m·g₁)` within
**0.003 dB** at m ∈ {0, ¼, ½, ¾, 0.9, 1}, and a tone two octaves down moves
by **0.0006 dB** across the sweep. One control ships; it is Mix, its 0 is the
byte-identical bypass Tier 1 asks for, and `range_db` reports
`−20·log10(1−Mix)`. Frozen as T6.

**D5. What should the Width macro display? Q.** The composite bell's
half-depth width over the ratio-and-overshoot plane at f₀ 3 kHz, Q 2
(f₀/Q = 1500 Hz) runs from **919 Hz** (ratio 2, 6 dB over) to **164 Hz**
(ratio 20, 40 dB over) — 0.61 down to 0.11 of f₀/Q, monotone in both. No
number in hertz is honest across that plane, so the macro shows **Q** and the
class docstring carries the relationship.

**D6 (new). Should either direction *boost*? Not in this revision.**
`expand=True` cuts the band when the band falls *under* the threshold;
neither direction lifts it. An upward dynamic EQ is reachable —
`makeup_db = +R` against `depth_db = −R` on `DYN_EXPAND` gives unity below
threshold and exactly +R above — but R is a target gain that fights the
threshold-and-ratio law T2 holds this class to, so it is not half-built here.
*Settled by:* a later revision, on an issue, with its own trait.

---


## Appendix

Run 2026-09-06 on this machine. CPython target:
`audiocomponents/.venv/bin/python`. MicroPython: `cmods/bin/micropython`.
Probes were scratch scripts, not committed; every number is reproducible from
its description. A0 and A3 share their runs with `LowPass.md`.

### A2. The measurements this seed rests on

**T1, the exact split.** The shipped class with its compressor idle
(threshold 0 dBFS, ratio 1), f₀ 3 kHz, Q 2, swept by fixed sines:

```
     500.0 Hz  reconstruction gain  -0.010 dB
    1500.0 Hz  reconstruction gain  -0.000 dB
    3000.0 Hz  reconstruction gain  +0.000 dB
    6000.0 Hz  reconstruction gain  -0.001 dB
   12000.0 Hz  reconstruction gain  +0.000 dB
```

and an impulse of amplitude 20 000 came out at peak **20 000**. T1's planted
fault: detune one branch by 1 % and the reconstruction must break by more
than 0.05 dB near f₀ — it breaks by about 0.4 dB.

**T2 and T3, the gain law.** f₀ 3 kHz, Q 2, threshold −30 dBFS, ratio 4;
tone at f₀, composite gain after the detector settles:

```
  in  -40.77 dBFS @3 kHz ->  -0.002 dB      (T3: below threshold, a wire)
  in  -30.31 dBFS @3 kHz ->  -0.288 dB
  in  -20.77 dBFS @3 kHz ->  -6.504 dB      (law predicts -6.92)
  in  -10.31 dBFS @3 kHz -> -14.347 dB      (law predicts -14.77)
  in   -4.29 dBFS @3 kHz -> -18.861 dB      (law predicts -19.28)
```

The composite sits consistently ~0.4 dB above the pure band law because the
notch branch passes a little of the tone; the trait's 1 dB tolerance covers
it, and the *consistency* of the offset is itself checkable.

**T4, out of band.** A 300 Hz tone through the same processor (f₀ 3 kHz):

```
  300 Hz at  -30.31 dBFS ->  -0.015 dB
  300 Hz at   -4.29 dBFS ->  -0.016 dB
```

Unchanged between a level that leaves the band idle and one that would drive
it 19 dB down — the property that separates a dynamic EQ from a multiband
compressor (S6).

**The Splitter hazard, and the probe that caught it.** An impulse inside a
40 000-frame `RawSample` produced **nothing at all** through `DynamicEQ`, and
`LowPass` passed the same impulse normally. Bisecting the chain put it on the
Splitter, and the cause is `audioif_splitter.c:35-38`: a `RawSample` hands
back its entire buffer in one pull, the ring is 8192 frames
(`audioif_splitter.h:20`), and everything older than the last 8192 frames is
dragged past. Confirmed by shortening the source:

```
  RawSample of    256 frames, impulse at  50 -> DynamicEQ peak  20000
  RawSample of   8192 frames, impulse at  50 -> DynamicEQ peak  20000
  RawSample of  40000 frames, impulse at 200 -> DynamicEQ peak      0
```

This is a *harness* hazard rather than a product defect — a real pump asks
for a block at a time — but it will silently zero every Splitter-based
measurement, so the kit spec must say that probe material is delivered in
blocks. It is also a ready-made planted fault for any Splitter class: feed
the probe as one long `RawSample` and the measurement must go red.

### A3. Held DC after silence

`DynamicEQ` at its shipped defaults (3 kHz) settles to exact zero on both
interpreters. The family's low-frequency residuals and the probe design that
hid them are in `LowPass.md` A3; §8 question 1 is the open part.

### A7. Desktop cost anchor (CPython target, x86-64, ns per stereo frame)

```
  Filter 1 biquad         frames= 512    146.6 ns/frame
  FeedbackDelay comb      frames= 256    141.7 ns/frame
  DynamicEQ               frames= 128   3268.4 ns/frame
  real time per stereo frame at 48 kHz = 20833.3 ns
```

The 128-frame block is the shipped class's Mixer buffer (`eq.py:250`), and
part of the 22× is paying every per-block overhead four times as often as the
Filters need.

### A8. Latency

Impulse at frame 50 through `DynamicEQ()` on an 8192-frame source: first
non-zero output at frame **50**, peak **20 000** of 20 000;
`latency_samples` reports **0**. Agreed. `audiodynamics.Dynamics`'
`lookahead_ms` is the one option that would change this and is off by
default.

### A9. Licence and citation audit, 2026-09-06

This seed's §2 carries the corrections themselves; this is the full
re-verification record behind them. Every source row in §2 and every URL
anywhere in this seed was re-fetched by a second agent that read none of the
first run's notes. Two corrections applied in place. **S1's licence call** now
records the repository's root `LICENSE.md` (full CC BY 4.0), which the first
draft did not mention — downgraded to *licence unverified, treated as
copyleft*, because that grant is the mirror's and the chain to RBJ is unshown;
treatment unchanged. And the **Fontana & Karjalainen paper is reachable after
all**: it is now S7, fetched from the DAFx archive's own path and read with
`pypdf`. §8's third open question is answered by that and should be closed
when the seed is next edited.

Re-verified exactly as the seed states them: RBJ's notch and BPF numerator
blocks; the CCRMA Q page's *"the resonance frequency divided by the resonator
bandwidth"* under a copyright with no grant; Zavalishin's `H_N = 1 − H_BP1 =
1 − 2R·H_BP` at §4.7 p. 119, verbatim, under the front-matter grant quoted in
A0; and all four **S6** quotations — the *"combines precision equalization
with selective compression/expansion and sidechain triggers, kicking in only
when the signal you're EQing goes above a certain threshold"* definition, the
*"full control over width ('Q'), gain, range, threshold, attack, and release"*
control set, the crossover-filters distinction, and the footer *"Copyright ©
2026 Waves Audio Ltd. All rights reserved."* The three repository citations
behind §3 were re-read with `grep -n`: `audioif_dynamics.h:65` is `float
ratio` and `:69` is `float release_coef` (one of each, as claimed);
`src/cpython/audiodynamics.py:19` and `:53` are the `lookahead_ms` prose and
its default; `eq.py:250` is the `audiomixer.Mixer(voice_count=2,
**_core.pcm(1024))` line.

**Unsourced, and flagged as such:** the dbx 902's attributes above (a fixed
high band, a specific detector time constant) are stated from general
knowledge — no dbx schematic or manual was reached in either run. They carry
the scope argument only; nothing in §3 rests on them.

### A10. Second licence and citation audit, 2026-09-06 (the re-fetch pass)

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

**One correction from this pass**, applied above in T2: **S6 was cited for
"threshold/ratio semantics" and the Waves page never uses the word *ratio*.**
It was re-fetched and searched in this run: the page names *"width ('Q'),
gain, range, threshold, attack, and release"* and nothing else, so S6 carries
the threshold half of T2 and the node's own header carries the ratio. §1's
long quote is verbatim and complete on the page — *"Whereas regular EQ is
applied to the sound from start to finish, dynamic EQ combines precision
equalization with selective compression/expansion and sidechain triggers,
kicking in only when the signal you're EQing goes above a certain threshold at
the frequency you've selected"* — as is the multiband-compressor distinction,
and the foot of the page reads *"Copyright © 2026 Waves Audio Ltd. All rights
reserved."* **S7 re-verified independently and stands**:
`www.dafx.de/paper-archive/2001/papers/fontana_a.pdf` was reached in this run
(HTTP 200, 118 KB, five pages, footers DAFX-1…DAFX-5) and read with `pypdf` —
PDF metadata title *Magnitude-Complementary Filters For Dynamic Equalization*,
authors *Federico Fontana, Matti Karjalainen*, header *Proceedings of the COST
G-6 Conference on Digital Audio Effects (DAFX-01), Limerick, Ireland, December
6-8, 2001*. All 20 259 extracted characters were searched for *licen*,
*copyright*, *(c)*, *©*, *warrant*, *public domain* and *rights*: **not one
occurrence**, so *licence unverified — treated as copyleft* is the correct
call. The Aalto portal record was reached again and confirms title, authors,
venue and year, with only the site-wide *"All content on this site: Copyright
© 2026 Aalto University's research portal, its licensors, and contributors.
All rights are reserved…"*. MDPI's *All About Audio Equalization*
(`mdpi.com/2076-3417/6/5/129`) was re-checked and is still **HTTP 403** — not
reached. Zavalishin §4.7 p. 119 was opened in the extracted text and carries
`H_N(s) = 1 − H_BP1(s) = 1 − 2R·H_BP(s)` exactly as cited. T1 was re-derived
from S1's own coefficients: notch plus band-pass sums to 1.000000 at 20 Hz,
100 Hz, 1 kHz, 5 kHz and 19 kHz.

**One thing this pass could not fix, because §8 is out of its scope:** §8's
third open question ("the Fontana & Karjalainen paper, identified but not
read") is **stale** — the paper is reached and read, and §2 already says so.
Station A should close it.

### A11. Trait-critic pass, 2026-09-06 — the composite-bell derivation

Arithmetic on S1's coefficients and the node's own gain law
(`audioif_dynamics.c:196-206`, `knee_db = 6.0f` at `:31`), in float64
(`audiocomponents/.venv/bin/python`, numpy 2.5.2). Not a render — it is the
prediction the render has to match.

Setting: f₀ = 3 kHz, Q 2, T = −30 dBFS, R 4, steady tone at L = −10 dBFS,
48 kHz. Band gain is the node's law at `L + |H_bp(f)|`; composite is
`|H_notch(f) + 10^(g/20)·H_bp(f)|`.

| f | \|H_bp(f)\| | band gain | composite |
|---|---|---|---|
| 1000 Hz | −14.811 dB | −3.892 dB | −0.086 dB |
| 1500 Hz | −10.127 | −7.405 | −0.360 |
| 2000 Hz | −5.892 | −10.581 | −1.163 |
| 2500 Hz | −1.936 | −13.548 | −4.112 |
| 3000 Hz | 0.000 | −15.000 | −15.000 |
| 3600 Hz | −1.967 | −13.525 | −4.062 |
| 4500 Hz | −6.045 | −10.466 | −1.114 |
| 6000 Hz | −10.518 | −7.111 | −0.322 |

The band gain column is exactly `−0.75·(L + |H_bp| − T)` at every row here,
because every one is above the knee; it reaches 0 where `|H_bp| = −23 dB`,
which is 429 Hz and 14 569 Hz.

**Widths, which is what refutes the old T5.** Depth at f₀ is −15.000 dB.
Half-depth (−7.500 dB) crossings: **2710.6 and 3318.3 Hz — 608 Hz apart**.
−3 dB absolute crossings: 2382.4 and 3766.7 Hz — 1384 Hz apart. The
band-pass's own −3 dB edges are 2342.3 and 3842.3 Hz — 1500 Hz apart, i.e.
f₀/Q. The old row asserted the third pair; the class produces the first. The
−3 dB-absolute pair lands near f₀/Q only because the depth happens to be
15 dB at this setting, and moves away as soon as ratio or level does.


### A12. Palette verification pass, 2026-09-07

Every §4/§5 claim about what an audioif node can and cannot do re-measured
independently. CPython target `audiocomponents/.venv/bin/python`, running the
same `src/shared` C the boards do. Probes were scratch scripts, not committed.

**The split reconstructs.** `DynamicEQ(frequency=3000, q=2)` with the
compressor idle (probe at −44 dBFS against a −6 dB threshold), source pumped
in 512-frame blocks, gain per probe:

```
   100 Hz  +0.0021 dB     1500 Hz  -0.0049 dB     6000 Hz  -0.0129 dB
   500 Hz  -0.0048 dB     3000 Hz  +0.0019 dB    12000 Hz  +0.0000 dB
```

Worst **0.013 dB** from unity — §4's 0.015 dB stands.

**The Splitter hazard is real and reproduces on demand.** An impulse at frame
0, `DynamicEQ` on the front, peak |y| over the first 3000 frames:

```
  4096-frame RawSample  (fits the 8192-frame ring)   peak 20000
  40000-frame RawSample (one get_buffer, one write)  peak     0   <-- lost
  the same 40000 frames pumped in 512-frame blocks   peak 20000
```

`audioif_splitter.c:35-38` drags an unread tap's cursor forward when the write
laps it, so the whole impulse is dropped and the class measures as silence.
§4's warning is confirmed and it belongs in the kit spec, not only here.

**`gain_reduction_db()` already exists.** `DYN_COMPRESS`, threshold −20 dBFS,
ratio 4, attack 2 ms, release 80 ms, full-scale 440 Hz tone:

```
  block 0  -9.570 dB    block 3  -11.270 dB
  block 1 -10.639 dB    block 4  -11.319 dB
  block 2 -11.078 dB    after set(threshold_db=-40, ratio=8): -30.939 dB
```

`audioif/src/audiodynamics/Dynamics.c:144-149` and `:208-209` expose it on
MicroPython, `audioif/src/cpython/audiodynamics.py:103-105` on CPython, and
`audioif_dynamics.h:86` is the field. `DYN_EXPAND` constructs on the same node.
§5's first "considered and not asked" is corrected accordingly: nothing was
missing.

**`audioif_splitter.h:21` caps taps at 4** — read, confirmed, and the mono
duplication §4 cites is `audioif_splitter.c:30-31`, also confirmed.

**No node ask survives or arises here.** §5's "None" stands, on firmer ground
than it was written on.

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

This is the only class in the unit that builds **four** nodes plus a splitter,
so `reset()` and `deinit()` are the invariants with teeth: today's `_core`
reaches the output `Mixer` alone (`_core.py:366-374`, `:376-385`), and
`audioroute.SplitterTap` deliberately does nothing on reset (its own comment:
rewinding one branch would desynchronise the rest), so the rebuild must
enumerate the Splitter, both Filters, the Dynamics and the Mixer and walk
that list. The residual measurement (A3) shows the class at its shipped
defaults reaching exact zero, so audioif#23 does not touch it — but a
low-frequency band would inherit the family's residual through its two
biquads, which §8 leaves open.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* (plain text, shepazu mirror) | the notch and BPF (constant 0 dB peak) coefficient blocks, from which the complementary identity follows; `α = sin(w0)/(2Q)` | the `.txt` itself carries **no license, copyright or warranty line** (re-verified 2026-09-06, all five terms searched) — but the repository serving it does: its root `LICENSE.md` is the full **CC BY 4.0** text (read at https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/LICENSE.md; GitHub's own licence API reports the repo as `NOASSERTION`). That is the *mirror's* grant, not RBJ's: the mirror's HTML rendering says only *"Adapted from Audio-EQ-Cookbook.txt, by Robert Bristow-Johnson, with permission"*, so the chain to the author is **not** shown (sources module: a repackager's label is an assertion). **License unverified — treated as copyleft:** read as a document for its mathematics, never ported | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Quality Factor (Q)" | *"Q … resonance frequency divided by the resonator bandwidth"* | © J. O. Smith III / CCRMA Stanford; no license granted. Read as a paper | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP mirror, text via `pypdf`) | `H_N = 1 − H_BP1 = 1 − 2R·H_BP` (§4.7 p. 119) — the complementary identity in the analog domain | verbatim-copy-only, no derivatives (grant quoted in A0). Read as a paper | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |
| **S6** Waves, *How and When to Use Dynamic EQ* | the working definition and the per-band control set quoted in §1; the distinction from a multiband compressor | *"Copyright © 2026 Waves Audio Ltd. All rights reserved."* Trade documentation, read for terminology only | https://www.waves.com/how-and-when-to-use-dynamic-eq | 2026-09-06 |
| **S7** Fontana & Karjalainen, *Magnitude-Complementary Filters for Dynamic Equalization*, Proc. COST G-6 Conf. on Digital Audio Effects (DAFx-01), Limerick, 6–8 Dec 2001, DAFX-1…5 | first- and second-order equalization structures whose gain and selectivity parameters are mapped so the gain can be varied dynamically and stay magnitude-complementary; **context only** | **no copyright, licence or rights line anywhere in the PDF** (all five terms searched across all five pages); licence unverified — treated as copyleft: read as a paper, never ported | https://www.dafx.de/paper-archive/2001/papers/fontana_a.pdf | 2026-09-06 — WebFetch reached it (HTTP 200, 118 KB) but could not read a PDF; text extracted with `pypdf` |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **The split is exact**: with the detector idle the processor is a wire — reconstruction within 0.05 dB from 20 Hz to 0.4·F_s, and an impulse comes out at its input peak | S1 (the two numerators sum to the denominator), derived analytically; S4 §4.7 p. 119; measured to 0.015 dB and impulse peak 20 000 → 20 000 (A2) | high | any reconstruction error above 0.05 dB with the detector below threshold, at any f₀ in 100 Hz…10 kHz and Q in 0.5…8 | swept sine through the class with threshold at 0 dBFS; response differenced against a wire; plus an impulse peak comparison |
| T2 | **The band gain follows the compressor law — above the knee, and the knee is 6 dB wide by default**: for a tone at f₀ at level L with threshold T and ratio R, the composite gain is `−(L−T)(1−1/R)` dB within 1 dB **whenever L−T ≥ 3 dB**. Inside the knee the node is quadratic — `−(1−1/R)·(L−T+3)²/12` for −3 < L−T < 3 — and exactly 0 for L−T ≤ −3. So a probe sitting *on* the threshold is predicted to read −0.56 dB at R 4, not 0; stating the hard law alone would score a correct node 0.56 dB wrong at that point | S6 for the threshold semantics **only** — the word *ratio* appears nowhere on that page (re-fetched and searched, 2026-09-06); the ratio, the knee and its shape are the node's: `audioif_dynamics.h:65` (`float ratio`), `:66` (`float knee_db`), `:69` (`float release_coef`), with `knee_db = 6.0f` set at `audioif_dynamics.c:31`, `over = env_db − threshold_db` at `:176` and the three-branch law at `:196-206`; measured −6.50 / −14.35 / −18.86 dB against a predicted −6.92 / −14.77 / −19.28 at T = −30 dBFS, R = 4 (A2) | high | any of the **five** probe levels more than 1 dB from the law that applies at that level — hard above the knee, quadratic inside it, exactly 0 below it | steady-state sine at f₀ at L ∈ {−41, −30, −21, −10, −4} dBFS, gain read after the detector settles; L = −30 sits exactly on the threshold and is the knee probe |
| T3 | **Below threshold it is a wire**: a tone at f₀ at 10 dB under the threshold passes within 0.05 dB of unity | S6 (*"kicking in only when the signal … goes above a certain threshold"*); measured −0.002 dB (A2) | high | more than 0.05 dB of gain change on a tone 10 dB below threshold | the T2 sweep's lowest level |
| T4 | **Out of band is untouched while the band is working**: a tone two octaves from f₀ moves by less than 0.2 dB whether the band is idle or 19 dB down | S6 (the precise-frequency distinction from a multiband compressor); measured −0.015 dB at 300 Hz with f₀ = 3 kHz, identical at −30 and −4 dBFS (A2) | high | more than 0.2 dB of movement out of band between the two states — i.e. audible pumping of the whole signal | a tone at f₀/8 rendered twice, once with a co-existing f₀ tone below threshold and once well above |
| T5 | **The band gain is affine in the band-pass branch's own response, and the audible bell is far narrower than f₀/Q**: band gain (dB) = `−(1−1/R)·(L + \|H_bp(f)\|_dB − T)` above the knee, 0 where `L + \|H_bp(f)\|_dB ≤ T − 3`. Worked at f₀ = 3 kHz, Q 2, T = −30 dBFS, R 4, L = −10 dBFS: band gain −15.00 dB at f₀, −13.55 at 2.5 kHz, −7.41 at 1.5 kHz, −3.89 at 1 kHz, 0 below 429 Hz and above 14.6 kHz; composite output −15.00 / −4.11 / −0.36 / −0.09 dB, half-depth width 608 Hz against f₀/Q = 1500 Hz | S1 for `\|H_bp\|`, T2 for the law, `audioif_dynamics.c:176` and `:196-206` for the knee and the clamp; re-derived independently in A13's D5 table, which lands 607.6 Hz | high (the affine form removes the hedge: the detector's selectivity **is** `\|H_bp\|`, so it is known rather than something the kit must hold still) | at the worked setting, any probe in f₀/8…4f₀ whose composite gain is more than 0.5 dB from the closed form built from S1 and T2 | steady-state sine, **one frequency at a time at a fixed level** — f ∈ {1 k, 1.5 k, 2 k, 2.5 k, 3 k, 3.6 k, 4.5 k, 6 k} Hz — each composite gain compared point by point with the closed form. Never a swept sine: a sweep moves the detector while it measures |
| T6 | **A dry/wet blend and a band-range limit are the same control**: with `H_notch + H_bp ≡ 1` the whole class is `1 + m·B·(g−1)` at blend `m`, so a blend against the dry input and a ceiling on the band branch are the same number; the composite at f₀ is `20·log10((1−m) + m·g₁)` with `g₁` the composite at `m = 1`, the deepest cut reachable at `m` is `−20·log10(1−m)` dB, and out of band nothing moves as `m` sweeps | T1 (the identity), and the algebra: `(1−m)·1 + m·(H_notch + g·H_bp) = 1 + m·H_bp·(g−1)` because `H_notch = 1 − H_bp`. This row is why the class ships one knob where S6's control list implies two, and it is what settles §8 D4 | high | a composite at f₀ more than 0.2 dB from that closed form at any m ∈ {0, ¼, ½, ¾, 0.9, 1}, or more than 0.05 dB of out-of-band movement across the sweep | the same steady tone at f₀ rendered at six blends and compared point by point with the closed form; a tone at f₀/8 rendered at three |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Independent licence and citation audit, 2026-09-06** (a second agent, none
of the first run's notes read; full record in Appendix A9). Two corrections
are applied above. **S1's licence call** now records the root `LICENSE.md`
(full CC BY 4.0) the serving repository carries — downgraded to *licence
unverified, treated as copyleft* because that grant is the mirror's and the
chain to RBJ is unshown; treatment unchanged. And the **Fontana &
Karjalainen paper is reachable after all** — it is now S7, fetched from the
DAFx archive's own path and read with `pypdf`; §8's third open question is
answered by it and should be closed when the seed is next edited. The dbx
902's attributes are **unsourced** general knowledge — no dbx schematic or
manual was reached; nothing in §3 rests on them.

*(from §2)*

**Second licence-and-citation audit, 2026-09-06** (a third pass, independent
of the first audit; **every URL in this seed re-fetched in this run**). S1,
S3, S4, S6 and S7 are all re-confirmed at their own sources, and **S7 was reached
and read again in this run** — `dafx.de/paper-archive/2001/papers/fontana_a.pdf`,
HTTP 200, five pages, PDF metadata naming Fontana and Karjalainen, and not one
occurrence of *licen*, *copyright*, *©*, *warrant*, *public domain* or
*rights* in its 20 259 extracted characters. **One correction, applied above
in T2:** S6 was cited for "threshold/ratio semantics" and the Waves page never
uses the word *ratio*; the ratio is the node's. Full record in `A10`.

*(from §3)*

**Trait-critic pass, 2026-09-06.** T2 and T5 rewritten in place. T5 was the
serious one: it claimed the composite bell's −3 dB points sit at the
band-pass's `f₀·(√(1+1/4Q²) ∓ 1/2Q)` edges, and the arithmetic of the class's
own topology refutes that — at the worked setting the half-depth width is
**608 Hz where f₀/Q is 1500**. Its measurement was unrunnable as written too
(*"a swept sine at a level that holds the detector at a constant gain
reduction"* — with the detector fed from the band branch, no level does that),
so the row now states the mechanism that governs the shape and is measured with
steady tones one frequency at a time. T2 gained the node's 6 dB soft knee
(`audioif_dynamics.c:31`, `:196-206`), without which a correct node reads
0.56 dB wrong at the threshold probe the row already lists; its "four measured
levels" is corrected to the five it names. T1, T3, T4 unchanged. Worked case in
A11. **Five Tier 2 rows after the pass.**

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 8 %, ESP32-S3 ≤ 25 %**. Lean patch expected: **yes** — a `" - lean"` patch
dropping the notch branch and driving a `PEAKING_EQ` section's `A` from the
detector (one Filter, one Dynamics as sidechain only) is the escape valve if
the S3 misses; it costs T1's exactness, which is why it is a patch and not
the default. This is the unit's most expensive class by a wide margin:
desktop anchor **3 268 ns per stereo frame** against 20 833 ns of real time,
against 147 ns for a single `Filter` (A7) — 22×. Part is the topology, part
is the shipped Mixer's 1024-byte buffer (`eq.py:250`) making the chain a
128-frame graph; §4 fixes the second half.

*(from §3)*

**Latency: zero** — impulse at frame 50 in, frame 50 out, full 20 000 peak
(A8); `latency_samples` reports **0**. **One option adds latency and it
defaults off**: `audiodynamics.Dynamics`' `lookahead_ms`
(`src/cpython/audiodynamics.py:19`, `:53`) holds the audio back while the
detector reads ahead. Off by default; if §6 exposes it at all its span starts
at 0 and stops at 5 ms, is reported in `latency_samples` the moment it is
non-zero, and is named in the docstring in ms at 48 kHz (vision §9a).
`tail_samples` is the pole pair's ring `ceil(4·Q·F_s/f₀)` plus the release.

*(from §4)*

- **Every parameter becomes live.** `frequency` and `Q` become `synthio`
  block slots on both biquads — one `synthio.Math` shared by the pair, so the
  branches can never drift out of complement; threshold, ratio, attack and
  release go through `Dynamics.set()`, which already takes them live —
  measured, one `set(threshold_db=…, ratio=…, attack_ms=…, release_ms=…)` call
  moves the reported gain reduction on the next block (A12).

*(from §4)*

- **Range** (a control S6 lists and the class lacks) is the Mixer's
  band-voice ceiling combined with the ratio, computed in Python on a macro
  move. **Expansion** is one constructor argument: `DYN_EXPAND` is on the
  same node.

*(from §4)*

**Portability tier: audioif.** `audioroute` and `audiodynamics` are both
audioif's own (`upstream-diff.md:661`), so on a stock CircuitPython board the
class imports cleanly and raises a clear `ImportError` at construction, in
`CabinetSim`'s shape (`drive.py:30-33`, `:331-334`), leaving the other
`eq.py` classes importable.

*(from §4)*

**One palette hazard the rebuild must document.** `audioif_splitter.c:35-38`
drags an unread tap's cursor forward when the writer laps it, so an upstream
that hands back more than the ring's 8192 frames in one `get_buffer` call
loses everything but the last 8192. A real pump never trips it; a `RawSample`
trips it immediately, and an impulse inside a 40 000-frame one vanished
entirely (A2). **The kit's probe material must be delivered in blocks**, or
every Splitter-based class measures as silence and looks broken.

*(from §5)*

Two things were considered and are *not* asks. A **gain-reduction read-out**
on `audiodynamics.Dynamics` would let the class drive a `PEAKING_EQ`
section's `A` directly — the textbook "moving bell" architecture — instead of
splitting and summing. **It is already on the node**: `gain_reduction_db()`
exists on both targets (`audioif/src/audiodynamics/Dynamics.c:144-149`,
`:208-209`; `audioif/src/cpython/audiodynamics.py:103-105`) and reads live —
measured 2026-09-07, a −20 dBFS-threshold 4:1 compressor on a full-scale
440 Hz tone reads −9.57 dB after one block and settles to −11.32 dB by the
fifth, and −30.94 dB after a live `set(threshold_db=-40, ratio=8)` (A12). So
there was never a node ask here, only an architecture choice, and this seed
keeps the split-and-sum for the reason it gave: the split is already exact
(T1, measured 0.015 dB; independently 0.013 dB, A12). The moving-bell
alternative is available to the lean patch at no node cost, and the seed
records it as such rather than as something the palette lacks. A **fifth
Splitter tap** would let one instance carry more than three bands; it is not
asked for because a second band is a second instance, and
`audioif_splitter.h:21` caps taps at 4 for a reason the class does not need to
fight.

*(from §7)*

- **Nothing is live.** `frequency`, `threshold_db`, `ratio` and `q` are
  constructor arguments only (`eq.py:235-236`); the two biquads take bare
  floats (`eq.py:240`, `:243`) rather than blocks, so the band cannot be
  moved at all after construction, and there is no setter for any of them.

*(from §7)*

- **The Mixer is built at a 1024-byte buffer** (`eq.py:250`) while both
  Filters use `_core.pcm()`'s 2048 (`_core.py:64`), so the class's block is
  128 frames and every per-block overhead is paid four times as often.
  Measured 3 268 ns per stereo frame, 22× a single `Filter` (A7).

*(from §7)*

- **`reset()` and `deinit()` reach the Mixer only** (`_core.py:366-374`,
  `:376-385`). The Splitter, both Filters and the Dynamics are neither reset
  nor deinitialised — the vision's planted fault "an intermediate node left
  live" is this class's, exactly.

*(from §7)*

- **No tail is declared** (`TAIL_SAMPLES = None`, `_core.py:141`) although
  the class holds two resonators and a release envelope; `latency_samples` 0
  is right and measured right (A8).

*(from §1, moved under the length rule 2026-09-07)*

The S6 quotations in full, verbatim from the page (re-fetched and searched in
the A10 pass): *"Whereas regular EQ is applied to the sound from start to
finish, dynamic EQ combines precision equalization with selective
compression/expansion and sidechain triggers, kicking in only when the signal
you're EQing goes above a certain threshold at the frequency you've
selected"*; *"full control over width ('Q'), gain, range, threshold, attack,
and release"*; and the distinction from a multiband compressor, *"multiband
compressors use crossover filters, which affect fairly broad frequency areas,
[while] a dynamic EQ allows you to specify the precise frequencies"*. The
page's footer reads *"Copyright © 2026 Waves Audio Ltd. All rights
reserved."*

And the identity, in full: RBJ's notch numerator is `(1, −2cos ω₀, 1)` and
his band-pass (constant 0 dB peak) numerator is `(α, 0, −α)` with
`α = sin(ω₀)/(2Q)`; they share the denominator
`(1+α, −2cos ω₀, 1−α)`, and the two numerators add up to exactly it.
So `H_notch(z) + H_bandpass(z) = 1` at every z, not only in magnitude. That
is the same statement as Zavalishin's `H_N = 1 − H_BP1 = 1 − 2R·H_BP`
(§4.7 p. 119). `audioif/src/shared/audioif_filter_f32.c:139-157` builds both
sections from exactly those coefficients — read 2026-09-07, `b0 = alpha,
b1 = 0, b2 = -b0` at `:150-152` and `b0 = 1, b1 = -2*sc.c, b2 = 1` at
`:154-156`, against `a0 = 1 + alpha, a1 = -2*sc.c, a2 = 1 - alpha` at
`:140-142` — which is why the split is exact on this node and not merely
close.

*(from §4, moved under the length rule 2026-09-07)*

**Where the 0.42 dB at the band centre comes from, and where it does not.**
With a tone at f₀ the composite reads about 0.42 dB *above* the gain
computer's law (measured −14.577 dB against a predicted −15.000 at f₀ 3 kHz,
Q 2, T −30 dBFS, R 4, L −10 dBFS). The seed put that down to the notch
branch passing a little of the tone. It does not: the notch branch measured
**exactly zero** at f₀ — RMS 0.00 of a 10 360 LSB source, on `audiobiquad`.
The cause is the detector. A one-pole peak follower never quite reaches the
peak of a fast sine, so `env_db` reads low and the cell cuts that much less:
the node's own `gain_reduction_db()` reports −14.771 dB at a 0.1 ms attack,
−14.678 at 0.5 ms, −14.370 at 2 ms and −13.820 at 10 ms, and at a fixed
2 ms attack it reports −14.510 at 200 Hz, −14.450 at 1 kHz, −14.370 at
3 kHz and −13.771 at 8 kHz. Moving with attack time and with frequency is
what a lagging follower does and what notch leakage would not. The remaining
0.2 dB between the node's reported reduction and the measured composite is
the ripple in the applied gain: an RMS over a rippling gain is not the gain
at the instant the node last reported.

### A13. Tail and cost, 2026-09-07 (Station A run)

`tools/phase2_probes/dynamiceq_opens.py` on
`audiocomponents/.venv/bin/python`, the rebuilt class, 48 kHz stereo.

Ring-down of the split, full-scale DC burst to the last non-zero frame,
against the declared `tail_samples`:

```
  f0     60 Hz  Q   0.5  ring    1284 samples  3.21 periods of Q/f0  (declared 1601)
  f0     60 Hz  Q   2.0  ring    4575 samples  2.86 periods of Q/f0  (declared 6401)
  f0     60 Hz  Q  12.0  ring   23869 samples  2.49 periods of Q/f0  (declared 38401)
  f0    400 Hz  Q   0.5  ring     156 samples  2.60 periods of Q/f0  (declared 241)
  f0    400 Hz  Q   2.0  ring     248 samples  1.03 periods of Q/f0  (declared 961)
  f0    400 Hz  Q  12.0  ring    3102 samples  2.15 periods of Q/f0  (declared 5761)
  f0   3000 Hz  Q  12.0  ring      34 samples  0.18 periods of Q/f0  (declared 768)
```

Every declaration is longer than the measurement, which is the direction
`tail_samples` is allowed to be wrong in. The constant is 4.0 periods of
`Q/f0` against a worst measured 3.21.

Held DC after silence, burst then 3 s of silence, residual over the last
4800 frames:

```
     60.0 Hz  last non-zero frame  19673   residual 0 LSB
     80.0 Hz  last non-zero frame  18355   residual 0 LSB
    120.0 Hz  last non-zero frame  17038   residual 0 LSB
    400.0 Hz  last non-zero frame  15191   residual 0 LSB
   3000.0 Hz  last non-zero frame  14511   residual 0 LSB
```

Desktop cost, `tools/measure_effect_cost.py`, 256-frame stereo blocks at
48 kHz on this machine (x86-64, CPython 3.12.3):

**The first pair taken in this session is withdrawn.** It read the rebuild at
1.696 ms/block against the shipped class's 1.958 and had the rebuild ahead;
it was taken while three other class-builder sessions were running on this
machine at a load average above 20, and a back-to-back pair an hour later
reversed the ordering. Recorded rather than deleted, because a cost figure off
a shared machine is exactly the kind of number that gets quoted later.

The pair below is five interleaved repeats of each build at a load average
under 4, so the two builds meet the same machine:

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

So the rebuild costs about **45 % more per block** than the class it replaces,
and that is the price of the three nodes it added: the guard that keeps a long
source from vanishing, the third splitter tap that makes `Mix` 0 a real
bypass, and the identity tail that keeps the class from rendering silence on
CircuitPython. Every one of those is a defect the shipped class has and this
one does not.

These are CPython numbers on a desktop, dominated by per-block Python
overhead rather than by the DSP: they rank builds against each other on one
machine and say nothing about either board. The P4 and S3 columns are the
board run's.

Mix against the closed form, and the out-of-band control (D4):

```
  g1 = -14.577 dB
  mix 0.00 ->   +0.000 dB (closed form   +0.000, d +0.000)   range -0.0 dB
  mix 0.25 ->   -1.975 dB (closed form   -1.974, d -0.001)   range 2.5 dB
  mix 0.50 ->   -4.535 dB (closed form   -4.534, d -0.001)   range 6.0 dB
  mix 0.75 ->   -8.180 dB (closed form   -8.178, d -0.002)   range 12.0 dB
  mix 0.90 ->  -11.440 dB (closed form  -11.437, d -0.003)   range 20.0 dB
  mix 1.00 ->  -14.577 dB (closed form  -14.577, d +0.000)   range inf dB
  375 Hz, two octaves down:  mix 0.00 +0.0000 dB   0.50 -0.0006 dB   1.00 +0.0000 dB
```

Half-depth width of the composite bell over the ratio-and-overshoot plane
(D5), closed form from S1 and the node's gain law, f0 3000 Hz, Q 2, so
f0/Q = 1500 Hz:

```
  ratio  over    depth        width    width / (f0/Q)
    2.0    6.0   -3.000 dB    919.0 Hz     0.61
    2.0   20.0  -10.000 dB    794.5 Hz     0.53
    2.0   40.0  -20.000 dB    460.9 Hz     0.31
    4.0    6.0   -4.500 dB    882.1 Hz     0.59
    4.0   20.0  -15.000 dB    607.6 Hz     0.41
    4.0   40.0  -30.000 dB    259.8 Hz     0.17
    8.0    6.0   -5.250 dB    862.9 Hz     0.58
    8.0   20.0  -17.500 dB    528.9 Hz     0.35
    8.0   40.0  -35.000 dB    194.9 Hz     0.13
   20.0    6.0   -5.700 dB    851.1 Hz     0.57
   20.0   20.0  -19.000 dB    486.2 Hz     0.32
   20.0   40.0  -38.000 dB    164.0 Hz     0.11
```

The 607.6 Hz row is A11's 608 Hz, re-derived by a second implementation.
