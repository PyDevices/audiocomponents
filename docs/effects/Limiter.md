# Effects Dossier — `Limiter` (no standout; a lookahead brickwall)

**Class:** `lib/audioeffects/dynamics.py` — read once, for §7.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed**. A brickwall limiter is not
a pedal; the thing being modelled is a *specification*, and two public ones
carry it: ITU-R BS.1770-5 Annex 2 fixes what "the peak did not exceed the
ceiling" means (S1), and Hämäläinen's DAFx-02 paper fixes what a lookahead
limiter has to do to keep that promise (S2). Naming a hardware referent here
would be worse, not better: the classic peak limiters (the 1176, the LA-2A's
Limit position, the Fairchild) are `Compressor`'s characters and are *not*
brickwalls — none of them looks ahead and none of them guarantees a ceiling.
**Grade:** **design** — the traits are the textbook properties of the thing,
stated so a measurement can fail them, with a standards document and a
peer-reviewed paper behind them rather than a schematic.
**Portability tier:** needs audioif-own nodes (`audiodynamics`), which is not a
CircuitPython port (`audioif/docs/upstream-diff.md:661`).
**Status:** seed (Phase 0), written 2026-09-06; audited the same day by an
independent licence and citation pass that re-fetched both sources itself
(Appendix D); then attacked on 2026-09-06/07 by an independent **trait-critic**
pass that re-reached both sources from their own bytes (Appendix E). No earlier
draft existed; both sources were reached in every run and both licence calls
stand unchanged. The trait-critic pass changed no number and added no source
claim: it tightened four rows' wording and gave L1 the probe-material
requirement without which the row could pass on evidence that cannot express an
inter-sample peak (E.3).

## 1. The circuit, in one paragraph

There is no circuit; there is a signal flow, and it has four parts that a
compressor does not. **(a) A delay on the audio path** so the detector can see a
peak before the audio carrying it reaches the output — the *lookahead*, and the
only latency this class ever has. **(b) A running maximum over that delay
window** before the level detector, so that once a peak has been seen the gain
stays down until the peak has physically left the delay line; without it the
detector starts releasing while the peak is still in flight, and the peak
escapes. This is S2's central result: a delay alone "is not a foolproof cure for
clipping", because "the output peaks above the threshold when the limiter goes
to release mode", and "clipping will generally also happen if a peak is shorter
than N samples", so the fix is "a max filter (running max selection) and a
clipping control block to the limiter side-chain before the level detection",
`x_max(n) = max[c(n−N), …, c(n)]` with the filter order N equal to the delay
length. **(c) A gain computer with infinite ratio and no knee above the
ceiling**, so the output cannot exceed it, together with a *smoothed* gain — S2
opens by noting the goal is "to control the time-varying gain smoothly enough to
avoid frequency artifacts", and the tension it resolves is that smoothing alone
"causes overshoots and leads to either clipped output or non-maximal signal
levels". **(d) A true-peak detector**, because the ceiling is a promise about
the reconstructed waveform, not about the samples: S1's Annex 2 defines the
measurement as 12.04 dB of attenuation, **4× oversampling to 192 kHz** through
an "order 48, 4-phase, FIR interpolating" filter, absolute value, and
conversion to **dB TP**, and its Attachment gives the worst-case under-read of a
peak-sample reading as `20·log(cos(π·f_norm/n))` for oversampling ratio *n* —
0.554 dB at 4× for f_norm 0.45, and — the same formula at *n* = 1 — 3.01 dB for
a sample-peak meter at a quarter of the sampling frequency, which S1 itself
states rounded ("it is easy to demonstrate, for example, a 3 dB under-read for
an unfortunately-phased tone at a quarter of the sampling frequency"). Panel-wise
there is a Ceiling, a Release, a Lookahead, a gain into the ceiling, and a
true-peak switch; everything else is a consequence.

## 2. Sources and license calls

| # | Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|---|
| S1 | ITU-R, *Recommendation BS.1770-5* (11/2023) … (App. S1) | The true-peak algorithm (attenuate 12.04 dB → 4× … (App. S1) | "© ITU 2023. All rights reserved. No part of … (App. S1) | https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf | 2026-09-06 — PDF fetched; unreadable to the fetch tool, text extracted locally with `pypdf` |
| S2 | Perttu Hämäläinen, "Smoothing of the Control Signal without Clipped … (App. S2) | Why a delay alone does not prevent clipping … (App. S2) | No copyright or licence line is printed … (App. S2) | https://www.dafx.de/paper-archive/2002/DAFX02_Hamalainen_smoothing_peak_limiters.pdf | 2026-09-06 — PDF fetched, text extracted locally with `pypdf` |

**Looked for and not found this run.** *Giannoulis, Massberg & Reiss, "Digital
Dynamic Range Compressor Design—A Tutorial and Analysis"* (JAES 60(6), 2012) —
the standard tutorial for gain-computer and detector topology — was identified
and is **still not reached**, and the earlier two accounts of why were both
wrong. What the second audit pass actually observed on 2026-09-06, probing the
host directly: `http://eecs.qmul.ac.uk/~josh/…` answers **302** to the same URL
over https, and that https host then **resets the connection**;
`http://www.eecs.qmul.ac.uk/~josh/…` answers **301 to
`https://webspace.eecs.qmul.ac.uk/josh`** — not to `qmul.ac.uk/eecs/`;
`https://www.eecs.qmul.ac.uk/…` fails certificate verification ("unable to get
local issuer certificate"); and the author's webspace page, which does resolve
(HTTP 200), reads "The owner of this web page hasn't added any content, yet."
The Semantic Scholar landing page returned no content. Nothing from it is
cited. A hardware brickwall limiter with a
published service manual was not hunted, deliberately: the class is a design
grade and adding a unit would make it a fifth `Compressor` character, not a
limiter (see the Standout note above).
FabFilter's Pro-L help page appeared in search results with a lookahead figure;
it was **not fetched** and is not cited.

Copyleft sources are measured or read as papers, never read for code structure
(vision §5). Neither source here is code; S2 carries no licence at all and is
treated as copyleft, S1 is read under an explicit all-rights-reserved notice.

The licence and citation audit's record is Appendices A and D: A is the first
pass (five corrections and one licence question for Gate 0), D the independent
re-fetch of 2026-09-06 that audited A's own work. Where the two disagree, D is
the later reading and wins.

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — the textbook properties, stated so they can fail

A design grade "may state the textbook property as its traits" (vision §4.1).
These are those properties, each with the number that fails it.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| L1 | **The ceiling is a true-peak promise.** With Lookahead and True Peak on, the output's true-peak level measured by S1's Annex 2 method (12.04 dB attenuation, 4× oversampling to 192 kHz, the order-48 4-phase FIR, absolute value, dB TP) exceeds the Ceiling macro by no more than **0.5 dB *(own, anchored on S1's 0.554 dB worst case at 4×)*** on every probe, at 48 kHz and 44.1 kHz. **The probe set must contain a worst-phase tone at f_s/4** — the case S1 singles out — because material with no inter-sample peak in it cannot express the thing being measured, and a pack of such material would read green on a limiter with no true-peak detection at all | S1: the five processing stages and the … (App. L1) | high | Any probe reading more than +0.5 dB TP above the ceiling; **or an evidence pack whose probe set contains no f_s/4 worst-phase tone** | BS.1770 4× true-peak reading of … (App. L1) |
| L2 | **Lookahead never creates overshoot.** Sweeping the Lookahead macro 0 → maximum in 1 ms steps, the output's *sample* peak **exceeds the ceiling by no more than 0.1 dB *(own)*** at every setting, **and does not grow with lookahead** — the peak at any setting is no higher than the peak at 0 ms plus the measurement's own repeat spread. The two clauses are separate failures: a build could sit under the ceiling everywhere and still show the S2 pathology as a rising trend | S2 §3.1 verbatim: a delay "is not a foolproof … (App. L2) | high | A sample peak more than 0.1 dB above the ceiling at any setting, or a peak that rises with lookahead | 1 ms burst at 0 dBFS into a −12 … (App. L2) |
| L3 | **A peak shorter than the lookahead is still caught — at every setting, not just the longest.** A single-sample impulse at 0 dBFS into a −12 dBFS ceiling leaves the output no more than **0.1 dB *(own)*** above the ceiling at **every non-zero lookahead setting**. The short-peak case is the one S2 says a plain delay always loses, and it loses it worst at the settings between the ends | S2 §3.1 verbatim: "Clipping will generally … (App. L3) | high | The impulse passing more than 0.1 dB over the ceiling at any non-zero lookahead setting | Impulse probe at 0.5, 1, 2 … (App. L3) |
| L4 | **Reported latency equals the lookahead, exactly.** `latency_samples == round(lookahead_ms × fs / 1000)` at 48 kHz, 44.1 kHz and 22.05 kHz, for every patch and every position of the Lookahead macro, and the click measurement agrees with the report **to the sample** | Vision §9a ("reported in `latency_samples` … (App. L4) | high | Any patch or macro position where the reported number and the measured click offset differ by one sample or more | Click through the class against … (App. L4) |
| L5 | **Zero by default.** Constructed with no options, and on the default patch, `latency_samples` is 0, Lookahead is 0 ms and True Peak is off | Vision §9a ("every latency-adding option … (App. L5) | high | A non-zero default for either option, or a non-zero `latency_samples` on patch 0 | Construct and read … (App. L5) |
| L6 | **Infinite ratio, hard knee.** Above the ceiling the static I/O curve's slope is ≤ **0.02 dB/dB *(own)*** over 24 dB of input, and at Knee-macro zero the fitted knee width is ≤ **0.5 dB *(own)*** — a brickwall, not a high-ratio compressor | The definition of the thing … (App. L6) | high | A slope above 0.02 dB/dB anywhere in the 24 dB span, **or** a fitted knee wider than 0.5 dB at Knee zero | Static I/O curve … (App. L6) |
| L7 | **Smoothing is a documented trade, not an accident.** At the default patch a 60 Hz sine driven 12 dB into the ceiling shows THD ≤ **1 % *(own)***; the Release macro's fastest setting is documented in the docstring as a distortion setting, and the measured THD there is recorded in the evidence pack rather than bounded | S2 §1–2 verbatim: the gain must be controlled … (App. L7) | high | THD above 1 % at the default patch, or a docstring that does not name the trade | Harmonic spectrum of a 60 Hz sine … (App. L7) |

### Tier 3 — cost and latency

Options that add latency, each with its default:

| Option | Adds | Default |
|---|---|---|
| `lookahead_ms` (macro 2) | `round(ms × fs/1000)` samples, up to 480 at 10 ms / 48 kHz | **0 — off** |
| `hold_ms` (macro 3) | none — the max filter reads backwards over the existing delay | tracks the lookahead |
| `true_peak` (macro 4) | none today (the node's estimator is causal over a 3-sample history, `audioif_dynamics.c:167-171`); **≈6 samples, 0.12 ms** if the BS.1770-grade detector of N-L2 lands — the group delay of the 12-tap-per-phase FIR, which the lookahead delay absorbs at no extra cost whenever lookahead is on | **off** |

Reported `latency_samples` is verified by the click measurement at the class
gate (L4). For the stompbox case (vision §9a): the default patch puts **zero**
in the effect and the whole round-trip budget in the platform's buffers.

`capabilities` = `()`. A ceiling has no tempo; the class does not read the
transport.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Nodes:** one `audiodynamics.Dynamics` in `DYN_LIMIT`. Portability tier
**audioif** (`audioif/docs/upstream-diff.md:661`). A mono source is limited on
one channel, not summed: the kernel selects mono or stereo at
`audioif_dynamics.c:235` and the cross-channel max (`:263-269`) collapses. A
stereo source is **always channel-linked** — the detector takes the maximum
across channels — which is the right default for a limiter and is not
switchable; the docstring says so and the kit measures it.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

Both are additive options on `audiodynamics`, audioif's own module (D1); neither
touches a CircuitPython-ported node.

- **N-L1 — a hold window on the detector.** Unblocks **L2 and L3**. …  *(argument in full: App. R)*
- **N-L2 — a BS.1770-grade true-peak detector.** Unblocks **L1**. …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

**Macros — 8 of the 16 allowed.** A limiter with fourteen knobs is a compressor.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Ceiling | UNIPOLAR | −24…0 dB | the output ceiling every mastering limiter has |
| 1 | Gain | UNIPOLAR | 0…24 dB | drive into the ceiling — the "loudness" knob; applied *before* the limiter, not as makeup (§4) |
| 2 | Lookahead | UNIPOLAR | 0…10 ms | how far ahead the detector reads; **0 by default**, and the class's only latency |
| 3 | Hold | UNIPOLAR | 0…20 ms | how long the gain stays down after a peak; defaults to the lookahead (N-L1) |
| 4 | Release | UNIPOLAR | 5 ms…2 s log | recovery after the peak has passed |
| 5 | True Peak | TOGGLE | off / on | inter-sample peaks (S1); **off by default** |
| 6 | Knee | UNIPOLAR | 0…12 dB | 0 is the brickwall of L6; above zero it becomes a soft limiter |
| 7 | Mix | UNIPOLAR | 0…1 | parallel limiting, and Tier 1's wire invariant |

**Patches** (names describe settings, never products):

| # | Name | Shape |
|---|---|---|
| 0 | Safety Ceiling | −1 dB, no lookahead, no true peak, 100 ms release — zero latency, the default |
| 1 | Catch The Peaks | −1 dB, 1.5 ms lookahead and hold, true peak on, 60 ms release |
| 2 | Loud | −0.3 dB, 12 dB of gain, 3 ms lookahead, 30 ms release, true peak on |
| 3 | Soft Ceiling | −2 dB, knee 9 dB, 200 ms release, no lookahead |
| 4 | Delivery Ceiling | −1 dB, true peak on, 2 ms lookahead, 150 ms release, no gain |
| 5 | Safety Ceiling - lean | patch 0 with true peak explicitly off and the hold window at 0 — the S3 escape valve (vision §7.2) |

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/dynamics.py` and `_core.py`.

1. **It reports zero latency while delaying the audio.** `Limiter` never …  *(argument in full: App. R)*
2. **The lookahead makes the overshoot worse, and the docstring says the …  *(argument in full: App. R)*
3. **The true-peak docstring is stronger than the code.** `dynamics.py:88-91` …  *(argument in full: App. R)*
4. **Attack is hardcoded and not a brickwall.** `dynamics.py:122` passes …  *(argument in full: App. R)*
5. **`reset()` silently reverts the surface.** `_core.Effect.reset()` ends with …  *(argument in full: App. R)*
6. **The node takes the module's rate, not the source's.** `dynamics.py:123` …  *(argument in full: App. R)*
7. **No gain into the ceiling.** The surface (`dynamics.py:99`) has Ceiling, …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **What is the smallest useful lookahead?** Tier 3 proposes 1.5 ms as the
   default when the macro is turned on, from S2's argument that the delay length
   and the smoothing quality trade against each other — but S2 gives no
   millisecond figure and none was sourced. **The implementation session**
   settles it at Station C, by sweeping the lookahead against L2, L3 and L7 on
   the probe material and taking the shortest window that passes all three; the
   number and the sweep go in the evidence pack.
2. **Is separate gain smoothing composable?** Two `Dynamics` in series, the
   first fast and the second slow, may reach L7 without a node change. Untried.
   **Phase 0 or the implementation session**, before any third ask is filed.
3. **How is the perceptible-monitoring-delay figure (vision §10.8) reached?**
   This dossier states the class's latency honestly but cannot say whether
   1.5 ms of lookahead is affordable in a stage chain, because the acceptable
   round trip is not yet a sourced number. **Phase 0's survey** owes it; nothing
   in this seed depends on the answer except the Lookahead macro's default.
4. **Does the ceiling need to be true-peak-aware in the gain computer, or only
   in the detector?** N-L2 puts the 4× reconstruction in the detector. A limiter
   that also *shapes* the reconstructed waveform (oversampling the whole gain
   path) is a bigger and more expensive thing and is deliberately not proposed.
   **Arthur, at Gate 0**, on the node list.
5. **Does L1's probe set exist yet?** The trait-critic pass made L1 require a
   worst-phase tone at f_s/4 in the probe material, because "on every probe" is
   only a bar if the material can carry an inter-sample peak — otherwise the
   row passes on evidence that cannot express what it measures. The kit spec
   (roadmap Phase 0) lists "an impulse, sines at three levels, a swept sine, a
   burst then silence, and one held instrument chord" and **none of those is
   phased against f_s/4**. **Phase 0's kit spec** owes the probe; until it is in
   `tools/effect_probes/`, L1 cannot be closed, and a green L1 without it should be
   read as unmeasured rather than met.
6. **Stereo linking is fixed on.** The node maxes across channels
   (`audioif_dynamics.c:263-269`) with no option, so an unlinked or partly
   linked limiter is not on this palette. No trait here needs it, so it is not
   an ask — but if a future dossier does need it, it is the same file.
   **Recorded, not asked.**

---


## Appendix

### A. Licence and citation audit, 2026-09-06 (first pass)

Both PDFs were re-fetched independently by `curl` (HTTP 200) and re-extracted
with `pypdf` 6.16.2, and every quotation in §1, §3 and the Appendix was checked
against that text. All of
S1's numbers check out verbatim — the five processing stages, the printed
order-48 4-phase coefficient table, "Higher sampling rates and over-sampling
ratios are preferred", the under-read formula and its table (4×: 0.554/0.688;
8×: 0.136/0.169; 16×: 0.034/0.042), and the 3 dB f_s/4 sentence — as do all of
S2's (§3.1's three sentences, §3.2's max filter, equations 6, 12 and 13, the
abstract's tension, pages DAFX-195…198). `audioif_dynamics.c:167-171`,
`:178-179`, `:245-253` and `:302-305` were re-read with `grep -n` and say what
§3 and §5 say they say.

Five corrections were applied: S1's licence cell restated from the "© ITU 2023…
All rights reserved" page; S2's licence cell downgraded to **unverified —
treated as copyleft**, since no licence line is printed anywhere on the paper
and vision §5 makes an unfound licence copyleft; S2's clipping-control symbols
restored to the paper's own notation (the draft had `a` as the input magnitude,
where the paper uses `a` for the detector coefficient); §1's 3.01 dB marked as
the formula at *n* = 1 rather than as something S1 states (it states 3 dB); and
the Giannoulis failure re-diagnosed as a 301 the fetch tool will not follow,
not a TLS failure. No value in §1 or §3 was found without a source row, and no
trait lost its source.

**Two of this pass's own claims did not survive the second audit** (Appendix D),
and are marked here so nobody reads A as settled: its account of the Giannoulis
failure is not what the host does (see §2, corrected); and "No value in §1 or §3
was found without a source row" was too strong — the seven Tier 2 thresholds are
this dossier's own numbers, now said so in §3, and Tier 3's budget percentages
rest on an unsourced newlib cycle cost.

One licence question the audit raises and does not settle, for Gate 0: §5's
N-L2 would put S1's 48 published coefficients into audioif's source. ITU's
notice forbids reproducing any part of the publication without written
permission, and the workspace rule for manufacturer model files
(`docs/agent-knowledge/instrument-sources.md`) is that a handful of parameter
values are facts about a part while the file is not ours to copy — a 48-entry
table sits between those two cases. Either the coefficients are re-derived here
(they are a windowed 4-phase interpolating FIR and a designer can regenerate an
equivalent set, which also removes the question), or the ask states plainly that
it reproduces an ITU table and Brad decides. Nothing in this dossier depends on
the answer; the measurement in B.8 uses them without redistributing them.

### B. Probes run against the palette node, 2026-09-06

CPython, `audiodynamics` from the audioif CPython build in
`audiocomponents/.venv`. Shared with `Compressor.md`; the rows that matter to
this class are repeated here in full.

**B.3 — lookahead creates overshoot.** A 1 ms burst at −0.5 dBFS between
silences, `DYN_LIMIT`, ceiling −12 dBFS, `attack_ms=0`, `release_ms=60`:

```
  lookahead  0.00 ms  output peak  8230 = -12.00 dBFS
  lookahead  0.50 ms  output peak  8299 = -11.93 dBFS
  lookahead  1.00 ms  output peak  8369 = -11.86 dBFS
  lookahead  2.00 ms  output peak  8509 = -11.71 dBFS
  lookahead  5.00 ms  output peak  8946 = -11.28 dBFS
  lookahead 10.00 ms  output peak  9723 = -10.55 dBFS
```

The mechanism, read off the kernel and confirmed by the numbers: the output
sample carrying the burst is `input[m]`, and it is multiplied by the gain
computed at index `m + held` — by which time the detector has passed the burst
and been releasing for `held − 48` samples. With a 60 ms release and 10 ms of
lookahead that is `exp(−9/60) = 0.86`, or 1.3 dB of gain given back; measured
1.45 dB. S2 §3.1 predicts exactly this ("the output peaks above the threshold
when the limiter goes to release mode"), and its max filter is the fix (N-L1).

**B.7 — the gain is unsmoothed, so a fast release distorts low notes.** 60 Hz
sine, `DYN_LIMIT`, ceiling −12 dBFS, about 12 dB of gain reduction,
`attack_ms=0`; THD over h2..h10, with the output peak sitting exactly on the
ceiling in every row:

```
  release   1.0 ms  THD 25.66 %   peak -12.00 dBFS
  release  10.0 ms  THD  7.53 %   peak -12.00 dBFS
  release  60.0 ms  THD  1.69 %   peak -12.00 dBFS
  release 300.0 ms  THD  0.36 %   peak -12.00 dBFS
```

The gain is computed per sample straight from the envelope
(`audioif_dynamics.c:306-311`) with no smoothing of its own, so release time and
smoothing are one knob — S2's opening tension, on this palette, in numbers.
L7's 1 % bound puts the default patch's release above about 80 ms.

**B.8 — true peak.** A sine at exactly f_s/4 with π/4 phase (the worst case S1
names), `DYN_LIMIT`, ceiling −6 dBFS, `attack_ms=0`, `release_ms=5`. The output
was measured both as a sample peak and by S1's Annex 2 method — 4× polyphase
interpolation with the order-48 4-phase FIR coefficients printed in Annex 2,
implemented in the probe:

```
  true_peak=False   sample peak -6.00 dBFS   BS.1770 4x true peak -2.95 dB TP
  true_peak=True    sample peak -7.93 dBFS   BS.1770 4x true peak -4.88 dB TP
```

With the flag off the limiter holds its sample-peak ceiling *exactly* and lets
**3.05 dB** through in the reconstructed waveform — S1's own figure for a
sample-peak meter at f_s/4 is 3 dB, so the palette is behaving exactly as the
standard says an unprotected limiter would. With the flag on, **1.12 dB** still
escapes, against S1's analytic 0.688 dB for an ideal 2× at f_norm 0.25 — the
node's 4-point midpoint interpolator is about 0.4 dB worse than an ideal 2×
reconstruction as well as being 2× rather than the required 4×.

**B.10 — instantaneous attack exists.** `attack_ms=0` makes `ms_to_coef` return
1.0 (`audioif_dynamics.c:10-11`); on a step to −2 dBFS against a −20 dBFS
ceiling the first sample after the step is already 18.00 dB down. A true
brickwall attack is available on the palette today and the current class does
not use it (§7.4).

**B.11 — cost on CPython**, 180 blocks of 256 stereo frames, per stereo frame,
against a bare `RawSample` at 0.038 µs: plain 0.043, `true_peak` 0.047,
`lookahead_ms=5` 0.046. A desktop number, recorded only to show the relative
weight of the options; the board numbers are Station C's.

**Construction check.** `Limiter.create(...)` then `program_change(2)`
("Brickwall") returns `macro(2) == 8.031496 ms` of lookahead and
`latency_samples == 0` — §7.1's defect, reproduced rather than inferred. Both
`Compressor` and `Limiter` build on a mono source and report
`channel_count == 1`, `tail_samples is None`, `capabilities == ()`.

### C. Cost arithmetic

See `Compressor.md` Appendix C for the base node's per-frame transcendental
count and the S3/P4 cycle estimates it implies. This class adds, per frame: one
comparison per sample for the running max (amortised, monotonic deque), zero for
the hold window's storage (it reuses the lookahead buffer the node already
allocates — `audioif_dynamics.h:87-92` notes an unconditional 50 ms of stereo
would be 9.6 KB per instance, which is why the buffer is allocated only on
demand and why the hold window must reuse it), and 4 phases × 12 taps = 48
multiply-adds per channel per frame if N-L2's BS.1770 detector lands. That last
figure is the whole reason a lean patch is expected on the S3.

### D. Licence and citation audit, second pass, 2026-09-06

An independent auditor re-fetched both sources and every URL in the file, from
this machine, without relying on Appendix A's record. Method: `curl` to disk
(status and byte count recorded), then `pypdf` 6.16.2 from
`audiocomponents/.venv/bin/python`. Results: S1 HTTP 200, 1 996 355 B, 32 pages,
PDF title metadata "Recommendation ITU-R BS.1770-5 (11/2023) Algorithms to
measure audio programme loudness and true-peak audio level"; S2 HTTP 200,
459 145 B, 4 pages, PDF title "Smoothing of the Control Signal without Clipped
Output in Digital Peak Limiters", author "Perttu Hämäläinen".

**Both licence calls stand, re-read this run.** S1's page ii carries "© ITU 2023
/ All rights reserved. No part of this publication may be reproduced, by any
means whatsoever, without written permission of ITU." S2 carries no copyright,
licence or rights line anywhere on its four pages — `grep -i` for copyright, ©,
licence, license and "all rights" returns nothing — so **unverified, treated as
copyleft** is the right call under vision §5. Neither is code; nothing from
either is reproduced here, and the auditor confirmed by search that S1's 48
published coefficients appear nowhere in this dossier.

**Every claim attributed to either source checks out verbatim.** From S1: the
five processing stages ("1 Attenuate: 12.04 dB attenuation / 2 4× over-sampling
/ 3 Low-pass filter / 4 Absolute: Absolute value / 5 Conversion to dB TP"); "The
4× over-sampling filter increases the sampling rate of the signal from 48 kHz to
192 kHz"; "Higher sampling rates and over-sampling ratios are preferred"; "One
set of filter coefficients (for the order 48, 4-phase, FIR interpolating)…"
followed by a table of 12 rows × 4 phases, which is where §3's "4 phases × 12
taps = 48 multiply-adds" and Tier 3's ≈6-sample group delay come from; the dB TP
definition; the Attachment's derivation "maximum under-read (in dB) =
20.log(cos(π.fnorm/n))" and its table (4 → 0.554 / 0.688; 8 → 0.136 / 0.169;
16 → 0.034 / 0.042); and, verbatim, "it is easy to demonstrate, for example, a
3 dB under-read for an unfortunately-phased tone at a quarter of the sampling
frequency". §1's 3.01 dB was re-derived from the same formula at n = 1,
f_norm = 0.25, and is correct. From S2: "a delay is not a foolproof cure for
clipping"; "the output peaks above the threshold when the limiter goes to
release mode"; "Clipping will generally also happen if a peak is shorter than N
samples. In that case the gain first begins to decrease, but when the peak ends,
gain begins to increase even though the peak has not yet reached the output";
"add a max filter (running max selection) and a clipping control block to the
limiter side-chain before the level detection"; equation (6),
`xmax(n) = max[c(n − N), ..., c(n)]`, "where c is the output of the clipping
control block… and N is the filter order, here same as the delay length";
equations (13) and (14), which confirm §2's symbols — `a` is the detector
coefficient of equation (1) and `|x(n)|` the input magnitude, the way §2 now has
them; the abstract's "control the time-varying gain smoothly enough to avoid
frequency artifacts" and "causes overshoots and leads to either clipped output
or non-maximal signal levels"; and "the shorter the delay, the less time the
limiter has to react and the less smoother the gain control is", quoted in
Tier 3. Pagination DAFX-195…198 confirmed.

`audioif_dynamics.h:32`, `.c:167-171`, `:178-179`, `:245-253`, `:302-305`,
`:307`, `:310` and `upstream-diff.md:661` were re-read with `grep -n`: all eight
say what §3, §4 and §5 say they say — in particular `:178-179` is
`case AUDIOIF_DYNAMICS_LIMIT: return over > 0.0f ? -over : 0.0f;`, exactly L6's
quotation, and `:167-171` is the single-midpoint 4-point estimator L1 measures
against.

**Three corrections, each applied where it lands:**

1. §2 "not found" — the Giannoulis diagnosis replaced with what the host
   actually does (302 to https, https resets; `www.` 301s to
   `webspace.eecs.qmul.ac.uk`, whose page reads "The owner of this web page
   hasn't added any content, yet."; `https://www.eecs…` fails certificate
   verification). Still not reached, still cited nowhere.
2. §3 Tier 2 preamble — the seven failure thresholds are named as this dossier's
   own numbers rather than sourced ones, since only L1's is anchored to a
   published figure.
3. §3 Tier 3 — the newlib transcendental cost the budget percentages rest on is
   flagged **unsourced**, matching the same correction in `Compressor.md`.

**Checked and found sound:** both "Reached — 2026-09-06" claims; the FabFilter
note (that page was not fetched by this auditor either, and nothing in the seed
depends on it); the 1.5 ms lookahead proposal, which the seed already declares
unsourced and hands to the class gate; and Appendix A's open licence question
about putting S1's coefficient table into audioif source, which this pass
endorses and leaves for Gate 0 — ITU's notice forbids reproducing any part of
the publication, and a 48-entry table is not the "handful of parameter values"
the workspace's model-file rule covers.

### E. Sources re-reached by the trait-critic pass, 2026-09-06/07

Both sources were fetched again in this run, by this pass, and read from their
own text rather than from the rows citing them. Neither WebFetch could read its
PDF; both were extracted locally with `pypdf` 6.16.2 from the bytes the fetch
saved.

**E.1 — S1, Recommendation ITU-R BS.1770-5**
(`https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf`,
HTTP 200, 1.9 MB, 32 pages). Annex 2, verbatim: "The stages of processing are:
1 Attenuate: 12.04 dB attenuation / 2 4 over-sampling / 3 Low-pass filter /
4 Absolute: Absolute value / 5 Conversion to dB TP"; "The 4 over-sampling filter
increases the sampling rate of the signal from 48 kHz to 192 kHz … Higher
sampling rates and over-sampling ratios are preferred"; "One set of filter
coefficients (for the order 48, 4-phase, FIR interpolating) that would satisfy
the requirements would be as follows" — a table of **4 phases × 12 taps**, read
but not reproduced here (§2's licence call). Attachment 1, verbatim: "maximum
under-read (in dB) = 20.log(cos(π.fnorm/n))", with the table giving **4× →
0.554 / 0.688 dB** at f_norm 0.45 / 0.5, 8× → 0.136 / 0.169, 16× → 0.034 /
0.042; and "it is easy to demonstrate, for example, a 3 dB under-read for an
unfortunately-phased tone at a quarter of the sampling frequency". That last
sentence is why L1 now *requires* an f_s/4 worst-phase tone in the probe set:
it is the one signal that separates a true-peak limiter from a sample-peak one,
and a probe pack without it cannot fail the row.

**E.2 — S2, Hämäläinen, DAFx-02**
(`https://www.dafx.de/paper-archive/2002/DAFX02_Hamalainen_smoothing_peak_limiters.pdf`,
HTTP 200, 448 KB, 4 pages). Verbatim, §3.1: "the output stays below the
threshold when the input signal level increases rapidly, but the output peaks
above the threshold when the limiter goes to release mode … the case
demonstrates that a delay is not a foolproof cure for clipping. Clipping will
generally also happen if a peak is shorter than N samples. In that case the gain
first begins to decrease, but when the peak ends, gain begins to increase even
though the peak has not yet reached the output." §3.2: "The key idea used in
this paper is to add a max filter (running max selection) and a clipping control
block to the limiter side-chain before the level detection"; "x_max(n) = max
[c(n − N), ..., c(n)] … where c is the output of the clipping control block …
and N is the filter order, here same as the delay length"; and the clipping
control, "c(n) ≥ (|x(n)| − β·e_max(n − 1)) / (1 − β), β = (1 − a)^(N+1)", with
"To allow the level detector block to determine the release behavior of the
limiter, c(n) should be at least equal to |x(n)|", i.e. `c(n) = max[...]` of the
two. Also verbatim, and the source of Tier 3's statement that the Lookahead
macro is the CPU-for-latency knob: "Having to optimize gain according to the
contents of the delay line can cause a heavy computational load if the delay
line is long. On the other hand, the shorter the delay, the less time the
limiter has to react and the less smoother the gain control is." The paper still
carries **no copyright or licence line**; §2's call is unchanged.

**E.3 — what this pass changed in Tier 2.** L1 gained the probe-material
requirement (an f_s/4 worst-phase tone), because "on every probe" is only a bar
if the probe set can express an inter-sample peak — the workspace's
absence-reads-as-agreement failure, in the one row where it would be invisible.
L2's "stays within 0.1 dB of the ceiling" became "exceeds the ceiling by no more
than 0.1 dB", which is what the row means: a limiter is allowed to sit *under*
its ceiling, and the old wording failed a correct build. L3's "with lookahead at
its maximum" became "at every non-zero lookahead setting", matching the
measurement column, which already swept four. L6 gained the knee-width
definition it referred to but never gave, and its disconfirmation gained the
knee clause. No number in any row was changed and no source claim was added.


### F. Palette verification, 2026-09-07

An independent **palette verifier** re-read every claim in §4 and §5 about what
an `audiodynamics` node can and cannot do against the C
(`audioif/src/shared/audioif_dynamics.c`, `audioif_dynamics.h`) and the bindings
(`audioif/src/audiodynamics/Dynamics.c`), by `grep -n`, and re-ran every
behavioural claim on the CPython build of audioif in `audiocomponents/.venv`.

**What the re-read confirmed.** Every line citation in §4 and §5 is correct as
written: `:10-11` (`ms_to_coef` returning 1.0 for ms ≤ 0), `:167-171` (the
three-sample-history half-sample estimator), `:178-179` (`DYN_LIMIT`'s
`over > 0 ? -over : 0`), `:235` (mono/stereo selection), `:245-253` (the
lookahead ring), `:263-269` (`fabsf` and the cross-channel max, which is why a
stereo source is always channel-linked), `:302-305` (the envelope follower),
`:310-311` (makeup applied *after* the gain computer),
`audioif_dynamics.h:32` (256 frames per block),
`AUDIOIF_DYNAMICS_MAX_LOOKAHEAD_MS 50.0f` (`audioif_dynamics.h:53`),
`upstream-diff.md:661`. `Dynamics` exposes eleven options
(`Dynamics.c:20-30`) — `lookahead_ms` and `true_peak` among them — plus
`play`, `set`, `stop`, `deinit` and one reader, `gain_reduction_db()`
(`Dynamics.c:144-149`). There is no `hold_ms`, no side-chain input and no
oversampling anywhere in the module.

**F.1 — the overshoot, and a two-node composition that removes it.** 1 ms burst
at 0 dBFS into a −12 dBFS ceiling; release 60 ms; sample peak of the output.
"Catch" is a second `audiodynamics.Dynamics` in `DYN_LIMIT` at the same ceiling
with `lookahead_ms=0`, `attack_ms=0`, `release_ms=5`.

```
  lookahead   one node (attack 0)   one node (attack 0.05 ms)   + catch stage
     0.0 ms       -12.00 dBFS              -2.65 dBFS            -12.00 dBFS
     1.0 ms       -11.86 dBFS             -11.86 dBFS            -12.00 dBFS
     2.0 ms       -11.71 dBFS             -11.71 dBFS            -12.00 dBFS
     5.0 ms       -11.28 dBFS             -11.28 dBFS            -12.00 dBFS
    10.0 ms       -10.55 dBFS             -10.55 dBFS            -12.00 dBFS

  L3, single-sample impulse at 0 dBFS
     0.0 ms       -12.00 dBFS              -2.65 dBFS            -12.00 dBFS
     0.5 ms       -11.93 dBFS              -2.58 dBFS            -12.00 dBFS
     1.0 ms       -11.86 dBFS              -2.50 dBFS            -12.00 dBFS
     2.0 ms       -11.71 dBFS              -2.36 dBFS            -12.00 dBFS
     5.0 ms       -11.28 dBFS              -1.93 dBFS            -12.00 dBFS
    10.0 ms       -10.55 dBFS              -1.20 dBFS            -12.00 dBFS

  seven-tone bed plus a 1 ms transient (attack 0.05 ms build in column two)
     0.0 ms              -                 -9.14 dBFS            -12.00 dBFS
     2.0 ms              -                -10.97 dBFS            -12.00 dBFS
     5.0 ms              -                -10.64 dBFS            -12.00 dBFS
    10.0 ms              -                -10.12 dBFS            -12.00 dBFS
```

B.3's own table is reproduced exactly by the `attack_ms=0` column. The catch
stage's −12.00 dBFS is exact rather than fortunate: with `attack_ms=0` the
envelope equals the current sample (`:10-11`, `:302-305`), `DYN_LIMIT` returns
`−over` (`:179`), and that gain multiplies the same sample (`:313`), so
`|out| = |x|·ceiling/|x|` for every sample over the ceiling, whatever the
signal.

**F.2 — the true-peak escape, measured independently of S1's filter.**
Worst-phase tone at f_s/4 (samples at ±A/√2, true peak A), limited to a
−6 dBFS ceiling, `attack_ms=0.05`, `release_ms=60` (B.8 used `attack_ms=0`,
`release_ms=5`, which is why the two readings differ in the second decimal).
The reading is an 8×
windowed-sinc (Blackman, 64 taps) interpolation peak — **not** S1's order-48
4-phase FIR, which is not reproduced here; it reads the input's own true peak as
−0.04 dBFS against an analytic 0.00, which is the check that it is measuring
what it claims.

```
  true_peak=False   output sample peak -6.00 dBFS   true peak -3.03 dBFS   escape 2.97 dB
  true_peak=True    output sample peak -7.94 dBFS   true peak -4.96 dBFS   escape 1.04 dB
```

B.8's −2.95 / −4.88 dB TP are reproduced to within the difference between the
two measurement filters. Sweeping the tone and its phase, the escape with the
flag on is **1.18 dB at f_s/4, 0.39 dB at 0.30·f_s, 0.06 dB at 0.35·f_s,
0.41 dB at 0.40·f_s and 0.04 dB at 0.45·f_s** — signal-dependent by an order of
magnitude, which is why a fixed Python-side ceiling offset is headroom rather
than a detector.

**F.3 — gain smoothing is not composable, and the release default is where L7
lives.** 60 Hz sine driven 12 dB into a −12 dBFS ceiling, THD(h2..h10):

```
  release   one node   two Dynamics in series at the same ceiling
    1 ms     25.79 %                  25.79 %
   10 ms      7.53 %                   7.53 %
   60 ms      1.69 %                   1.69 %
  300 ms      0.36 %                   0.36 %
```

Identical to two decimals: the second node's detector sees a signal already at
the ceiling and computes no gain, so it smooths nothing. (Compressor.md's B.7,
whose 25.66 % / 0.36 % are the same measurement, is reproduced at 25.79 % /
0.36 %; the 0.13 % difference at the 1 ms end is the probe's own level and
window, not the node.) A lookahead-plus-catch build measures 1.14 % at 60 ms
against the lone node's 1.69 %, so the catch stage does not make L7 worse
either.

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

**Tier 1 note that this class has to answer twice.** `latency_samples` is the
invariant the current class fails (§7.1), and it is also L4 below — the
lookahead is a *variable* latency the class must report the moment a macro or a
patch turns it on.

**Rate note.** L1's true-peak measurement is defined by S1 at 48 kHz and its
worst case is at a fixed *normalised* frequency, so the trait holds at 44.1 kHz
and 22.05 kHz unchanged; only the millisecond values of the lookahead and hold
windows move with the rate, and they are stored in samples.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| # | Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|---|
| S1 | ITU-R, *Recommendation BS.1770-5* (11/2023), Annex 2 and its Attachment 1 | The true-peak algorithm (attenuate 12.04 dB → 4× oversample to 192 kHz → low-pass → absolute → dB TP); the order-48 4-phase FIR coefficients; "Higher sampling rates and over-sampling ratios are preferred"; the under-read formula `20·log(cos(π·f_norm/n))` and its table (4× → 0.554/0.688 dB, 8× → 0.136/0.169, 16× → 0.034/0.042 at f_norm 0.45/0.5); the 3 dB sample-peak under-read at f_s/4; the definition of dB TP | "© ITU 2023. All rights reserved. No part of this publication may be reproduced, by any means whatsoever, without written permission of ITU" (p. ii, read this run) — freely downloadable is not a licence (vision §5). Read as a specification; the coefficients were used to *measure* our own output (Appendix B.8) and are not reproduced in this dossier | https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf | 2026-09-06 — PDF fetched; unreadable to the fetch tool, text extracted locally with `pypdf` |
| S2 | Perttu Hämäläinen, "Smoothing of the Control Signal without Clipped Output in Digital Peak Limiters", *Proc. DAFx-02*, Hamburg, pp. 195–198 | Why a delay alone does not prevent clipping; why a peak shorter than the delay always clips; the max-filter solution with `x_max(n) = max[c(n−N),…,c(n)]`, filter order = delay length; the clipping-control term in the paper's own notation, `c(n) = max[ abs(x(n)), (abs(x(n)) − β·e_max(n−1))/(1−β) ]` with `β = (1−a)^{N+1}`, where `abs(x(n))` is the paper's own absolute-value notation for the input magnitude, and `a` is the detector coefficient (the earlier draft swapped these two symbols); the framing that smoothing and non-clipping are in tension | No copyright or licence line is printed anywhere on the paper (DAFx-02 proceedings; re-checked this run) — **licence unverified, treated as copyleft** per vision §5's "an unfound license is copyleft until shown otherwise". Read as a paper; the math is re-derived, no code is taken | https://www.dafx.de/paper-archive/2002/DAFX02_Hamalainen_smoothing_peak_limiters.pdf | 2026-09-06 — PDF fetched, text extracted locally with `pypdf` |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| L1 | **The ceiling is a true-peak promise.** With Lookahead and True Peak on, the output's true-peak level measured by S1's Annex 2 method (12.04 dB attenuation, 4× oversampling to 192 kHz, the order-48 4-phase FIR, absolute value, dB TP) exceeds the Ceiling macro by no more than **0.5 dB *(own, anchored on S1's 0.554 dB worst case at 4×)*** on every probe, at 48 kHz and 44.1 kHz. **The probe set must contain a worst-phase tone at f_s/4** — the case S1 singles out — because material with no inter-sample peak in it cannot express the thing being measured, and a pack of such material would read green on a limiter with no true-peak detection at all | S1: the five processing stages and the 4-phase × 12-tap coefficient table verbatim; the under-read formula 20·log(cos(π·f_norm/n)) and its table (4× → 0.554 / 0.688 dB at f_norm 0.45 / 0.5); and "it is easy to demonstrate, for example, a 3 dB under-read for an unfortunately-phased tone at a quarter of the sampling frequency" (App. E.1) | high | Any probe reading more than +0.5 dB TP above the ceiling; **or an evidence pack whose probe set contains no f_s/4 worst-phase tone** | BS.1770 4× true-peak reading of the rendered output, per probe, against the ceiling. Today's palette reads **+3.05 dB TP** with the flag off and **+1.12 dB TP** with it on (B.8) |
| L2 | **Lookahead never creates overshoot.** Sweeping the Lookahead macro 0 → maximum in 1 ms steps, the output's *sample* peak **exceeds the ceiling by no more than 0.1 dB *(own)*** at every setting, **and does not grow with lookahead** — the peak at any setting is no higher than the peak at 0 ms plus the measurement's own repeat spread. The two clauses are separate failures: a build could sit under the ceiling everywhere and still show the S2 pathology as a rising trend | S2 §3.1 verbatim: a delay "is not a foolproof cure for clipping … the output peaks above the threshold when the limiter goes to release mode"; §3.2's max filter is the fix (App. E.2) | high | A sample peak more than 0.1 dB above the ceiling at any setting, or a peak that rises with lookahead | 1 ms burst at 0 dBFS into a −12 dBFS ceiling, lookahead 0…10 ms in 1 ms steps. Today's palette: −12.00 dBFS at 0 ms rising to **−10.55 dBFS at 10 ms** (B.3) |
| L3 | **A peak shorter than the lookahead is still caught — at every setting, not just the longest.** A single-sample impulse at 0 dBFS into a −12 dBFS ceiling leaves the output no more than **0.1 dB *(own)*** above the ceiling at **every non-zero lookahead setting**. The short-peak case is the one S2 says a plain delay always loses, and it loses it worst at the settings between the ends | S2 §3.1 verbatim: "Clipping will generally also happen if a peak is shorter than N samples. In that case the gain first begins to decrease, but when the peak ends, gain begins to increase even though the peak has not yet reached the output" (App. E.2) | high | The impulse passing more than 0.1 dB over the ceiling at any non-zero lookahead setting | Impulse probe at 0.5, 1, 2, 5 and 10 ms of lookahead; sample peak of the output, at 48 kHz and 44.1 kHz |
| L4 | **Reported latency equals the lookahead, exactly.** `latency_samples == round(lookahead_ms × fs / 1000)` at 48 kHz, 44.1 kHz and 22.05 kHz, for every patch and every position of the Lookahead macro, and the click measurement agrees with the report **to the sample** | Vision §9a ("reported in `latency_samples` the moment it is turned on"); the contract's live surface (roadmap §3) | high | Any patch or macro position where the reported number and the measured click offset differ by one sample or more | Click through the class against its dry path, per patch and at six macro positions, at three rates |
| L5 | **Zero by default.** Constructed with no options, and on the default patch, `latency_samples` is 0, Lookahead is 0 ms and True Peak is off | Vision §9a ("every latency-adding option defaults off or to its shortest") | high | A non-zero default for either option, or a non-zero `latency_samples` on patch 0 | Construct and read; one line, run at all three rates |
| L6 | **Infinite ratio, hard knee.** Above the ceiling the static I/O curve's slope is ≤ **0.02 dB/dB *(own)*** over 24 dB of input, and at Knee-macro zero the fitted knee width is ≤ **0.5 dB *(own)*** — a brickwall, not a high-ratio compressor | The definition of the thing; and the palette's `DYN_LIMIT` gain computer is exactly `over > 0 ? -over : 0` (`audioif_dynamics.c:178-179`), which is that law in one line, so the row is checkable against a reading as well as a measurement | high | A slope above 0.02 dB/dB anywhere in the 24 dB span, **or** a fitted knee wider than 0.5 dB at Knee zero | Static I/O curve, 60 steady levels from 24 dB below to 24 dB above the ceiling, at Knee zero and at Knee maximum |
| L7 | **Smoothing is a documented trade, not an accident.** At the default patch a 60 Hz sine driven 12 dB into the ceiling shows THD ≤ **1 % *(own)***; the Release macro's fastest setting is documented in the docstring as a distortion setting, and the measured THD there is recorded in the evidence pack rather than bounded | S2 §1–2 verbatim: the gain must be controlled "smoothly enough to avoid frequency artifacts", and smoothing alone "causes overshoots and leads to either clipped output or non-maximal signal levels" (App. E.2) | high | THD above 1 % at the default patch, or a docstring that does not name the trade | Harmonic spectrum of a 60 Hz sine at 12 dB of gain reduction, per patch, at 48 kHz and 44.1 kHz. Today's palette: 25.66 % at a 1 ms release, 0.36 % at 300 ms (B.7) |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §3)*

**Shared definitions.** *Knee width* — the input span over which the static
curve's local slope moves from 0.95 dB/dB to within 5 % of the asymptotic slope,
fitted on a 60-point curve with the fit residual reported beside it. *THD* —
harmonics 2–10 re the fundamental, over a 10-period analysis window, at the rate
the row names. *Sample peak* and *true peak* are never used interchangeably: L1
is the only true-peak row and it names S1's method explicitly.

*(from §3)*

**The properties are sourced; the numbers that fail them are marked *(own)*** —
0.5 dB in L1, 0.1 dB in L2 and L3, 0.02 dB/dB and 0.5 dB in L6, 1 % in L7. Only
L1's is anchored to a published figure (S1's 0.554 dB worst-case under-read at
4×). A class gate is free to move any of them with a written reason rather than
treating it as a fact it must reproduce. Both sources were re-fetched and
re-read by the trait-critic pass of 2026-09-06/07; the verbatim text is in
**Appendix E**.

*(from §3)*

**Trait count after the trait-critic pass of 2026-09-06/07: 7 Tier 2 rows.** The
grade is *design*, which vision §4.1 grades on Tier 1 and Tier 3 alone, so the
roadmap's "at least three Tier 2 traits" bar does not bind this class — it is
met anyway, and each of the seven carries a source, a confidence, a
disconfirmation condition and a measurement. Nothing here is *unmeasured*.

*(from §3)*

Budget as a fraction of one stereo block's deadline (256 frames = 5.33 ms at
48 kHz, `audioif_dynamics.h:32`): **ESP32-P4 ≤ 6 %, ESP32-S3 ≤ 18 %** with true
peak on; **≤ 4 % / ≤ 12 %** with it off. Lean patch expected: **yes** — a
`"Safety Ceiling - lean"` with True Peak off and Lookahead at 0, for the S3.
The base cost is `Compressor`'s (one `logf` and one `expf` per frame,
`audioif_dynamics.c:307`, `:310`; Appendix C of `Compressor.md` — whose one
imported number, "a single-precision `expf` or `logf` from newlib costs of the
order of 100–200 cycles", the audit of 2026-09-06 flags as **unsourced**, so
these percentages are budgets rather than findings and Station C measures them);
the running
max costs one comparison per sample amortised with a monotonic deque; a
BS.1770-grade 4× true-peak detector is the expensive part at 4 phases × 12 taps
= 48 multiply-adds per channel per frame.

*(from §3)*

**Latency.** Algorithmic latency of the dry-to-wet path is **zero** by default
and equals the lookahead when it is on. A brickwall limiter is the one class in
this program whose algorithm genuinely must see ahead, and the smallest it can
be is the smallest window the gain can ramp down across without the ramp itself
becoming the distortion of L7 — proposed at **1.5 ms (72 samples at 48 kHz)** as
the default *when a musician turns lookahead on*, to be replaced by a measured
number at the class gate (§8.1). **The knob that trades CPU for latency is the
Lookahead macro**, which sets both the delay and the max filter's order (S2:
"the shorter the delay, the less time the limiter has to react and the less
smoother the gain control is"), so a shorter lookahead costs less RAM and less
comparison work and buys worse smoothing.

*(from §4)*

**Python at construction and on a macro move** sets `threshold_db` (the
ceiling), `release_ms`, `lookahead_ms`, `true_peak`, and — for the drive-into-
the-ceiling macro — the input gain, which has to be a separate node or a
`makeup_db` on a second instance, since `makeup_gain` is applied *after* the
limiter (`audioif_dynamics.c:310-311`) and would push the output back through
the ceiling. **C per sample** is `audioif_dynamics.c:236-323`.

*(from §4)*

**Reachable today, measured this run (Appendix B).** L6 is exact: `DYN_LIMIT`'s
gain computer is `over > 0 ? -over : 0` (`:178-179`), infinite ratio and no
knee, and `attack_ms=0` makes the detector instantaneous (`ms_to_coef` returns
1.0 for ms ≤ 0, `:10-11`), giving 18 dB of gain change in one sample (B.10) — so
a zero-lookahead limiter already holds its sample-peak ceiling exactly (B.3, the
0 ms row reads −12.00 dBFS against a −12.00 dB ceiling). That row needs
`attack_ms=0` and nothing slower: re-run at the 0.05 ms the class ships today
(`dynamics.py:122`) the same probe reads **−2.65 dBFS**, 9.35 dB over the
ceiling (Appendix F.1). L5 and L7's default are
Python-side choices. L4 is a Python-side arithmetic fix, not a node question.

*(from §4)*

**A single node cannot hold the ceiling once lookahead is on — but two can, and
that is measured (Appendix F.1).** **L2 and L3** fail on a lone `Dynamics` and
fail *worse* the more lookahead is asked for: the node delays the audio
(`:245-253`) but releases the envelope on the live input (`:302-305`), so by the
time a peak reaches the output the detector has been releasing for the whole
lookahead window. Measured: a 1 ms burst into a −12 dBFS ceiling comes out at
−12.00 dBFS with no lookahead and **−10.55 dBFS with 10 ms of it** (B.3,
reproduced exactly) — the class's own headline feature makes its promise worse,
which is exactly S2 §3.1's result. Putting a **second `Dynamics` after the
first**, at the same ceiling, with `lookahead_ms=0` and `attack_ms=0`, removes
the escape entirely and at every setting: the same burst reads **−12.00 dBFS at
0, 1, 2, 3, 4, 5, 6, 8 and 10 ms of lookahead**, the single-sample impulse of L3
reads **−12.00 dBFS at 0.5, 1, 2, 5 and 10 ms**, and a seven-tone bed with a
1 ms transient in it reads −12.00 dBFS where the lone node reads −10.12 dBFS at
10 ms. The reason is in the C rather than in luck: with `attack_ms=0`,
`ms_to_coef` returns 1.0 (`:10-11`), so `state->envelope` becomes the current
sample's level (`:302-305`), `DYN_LIMIT` returns exactly `−over` (`:179`), and
that gain multiplies *that same sample* (`:313`) — a sample-exact brickwall by
construction, not an approximation. What it costs is the second instance's
per-frame `logf` (`:307`) and `expf` (`:310`).

*(from §4)*

**L1 is the one that is genuinely not reachable.** It fails because the node's
true-peak estimator evaluates a single midpoint by 4-point interpolation
(`:167-171`), i.e. an effective 2× reading against S1's required 4×: measured,
a worst-phase sine at f_s/4 limited to a −6 dBFS ceiling reads **−2.95 dB TP**
with the flag off and **−4.88 dB TP** with it on (B.8), so 1.12 dB still escapes
where L1 allows 0.5 dB — re-measured this run against an independent 8×
windowed-sinc reading rather than S1's filter, **−3.03 dB TP** with the flag off
and **−4.96 dB TP** with it on, so 1.04 dB escapes (F.2). It is not composable:
there is no per-block hook in the contract (roadmap §3's live surface has none,
and `docs/audio-component-api.md` names no callback — `:65-117` is the whole
live surface, `:209-236` the whole of timing and transport), the delay line is
inside the node, Python cannot see individual samples, and no node on the
palette resamples. Nor is a Python-side ceiling offset a substitute: the
estimator's under-read is signal-dependent — measured on worst-phase tones,
1.18 dB at f_s/4 but 0.39 dB at 0.30·f_s and 0.04 dB at 0.45·f_s (F.2) — so any
single offset either leaves the f_s/4 case over the ceiling or holds everything
else about a decibel under it.

*(from §5)*

**Verdict after the palette verification of 2026-09-07** — every claim in §4 and
§5 about what a node can and cannot do re-read against
`audioif/src/shared/audioif_dynamics.c` and `audioif/src/audiodynamics/`, and
every behavioural claim re-probed on the CPython build of audioif (Appendix F):
**N-L1 is refuted by the palette; N-L2 stands.** One issue, not two.

*(from §5)*

- **N-L1 — a hold window on the detector.** Unblocks **L2 and L3**.
  *Palette instead:* the audio is delayed (`audioif_dynamics.c:245-253`) while
  the envelope releases on the live input (`:302-305`). *Measurement showing it
  cannot reach the trait:* B.3 — overshoot grows monotonically with lookahead,
  0.00 dB at 0 ms to **1.45 dB at 10 ms**, where L2 allows 0.1 dB at every
  setting. *Shape:* a `hold_ms` option, defaulting to the lookahead length,
  implemented as S2's running max over the same delay line the lookahead already
  allocates — `x_max(n) = max[c(n−N),…,c(n)]` — so the RAM cost is zero and the
  CPU cost is one comparison per sample amortised. S2's clipping-control term
  `c(n)` is the second half of the same change and closes L3's short-peak case.
  **REFUTED BY PALETTE** (palette verification, 2026-09-07): the refutation this
  seed left unrun was run, and the reasoning it rested on was wrong. A second
  `Dynamics` in series does *not* catch the escape "after the fact with its own
  attack", because with `attack_ms=0` it has no attack: `ms_to_coef` returns 1.0
  (`audioif_dynamics.c:10-11`), the envelope becomes the current sample's level
  (`:302-305`), `DYN_LIMIT` returns `−over` (`:179`) and that gain is applied to
  the same sample (`:313`). Measured, the composition holds **−12.00 dBFS
  against a −12.00 dBFS ceiling at every lookahead setting** on all three probes
  L2 and L3 name — the 1 ms burst at 0…10 ms, the single-sample impulse at
  0.5…10 ms, and a seven-tone bed with a transient — where the lone node runs
  from −11.86 to −10.55 dBFS (Appendix F.1). L2's second clause is met the same
  way: the peak does not grow with lookahead, it does not move at all. What the
  composition does not give is S2's *mechanism* — the gain stays up and the
  residual is limited instantaneously instead of the gain staying down until the
  peak has left the line — so a trait about the smoothness of the gain **during**
  a caught peak would revive this ask; §3 states no such trait, and L7's THD
  probe at the default patch does not exercise one (with 5 ms of lookahead and a
  catch stage it measures 1.14 % against the lone node's 1.69 % at the same
  60 ms release, F.3). The cost is the second instance's `logf`/`expf` pair.

*(from §5)*

- **N-L2 — a BS.1770-grade true-peak detector.** Unblocks **L1**.
  *Palette instead:* one midpoint estimate per channel (`:167-171`), an
  effective 2× oversampling. *Measurement:* B.8 — 1.12 dB TP escapes a −6 dBFS
  ceiling at f_s/4 worst phase with the flag on, where L1 allows 0.5 dB. S1's own
  analytic bound for an ideal 2× at f_norm 0.25 is 0.688 dB, so the node's
  estimator is about 0.4 dB worse than an ideal 2× as well as being 2× rather
  than 4×. *Shape:* `true_peak=2` selecting a 4-phase polyphase FIR (S1's Annex 2
  coefficients are a published specification; we would implement them, not copy a
  file), leaving `true_peak=True` exactly as it is so no existing render changes.
  Costs 48 multiply-adds per channel per frame and about 6 samples of group
  delay, both stated in Tier 3. **ASK STANDS** (palette verification,
  2026-09-07). *Refutation run and failed:* per-sample reconstruction cannot be
  composed from Python and no node on the palette resamples, so the only
  candidate was a Python-side ceiling offset — and the estimator's under-read is
  signal-dependent, measured 1.18 dB at f_s/4, 0.39 dB at 0.30·f_s and 0.04 dB
  at 0.45·f_s on worst-phase tones (F.2), so one offset cannot serve both ends.
  The escape was re-measured independently of S1's filter, with an 8×
  windowed-sinc reading: **1.04 dB** above a −6 dBFS ceiling at f_s/4 with the
  flag on, against L1's 0.5 dB.

*(from §5)*

**Not an ask, on purpose.** Separate gain smoothing (a second one-pole on the
gain, after the gain computer) would help L7. The composition that might have
reached it has now been tried and it does **nothing**: two `Dynamics` in series
at the same ceiling measure the same THD as one, to two decimals, at every
release setting — 25.79 % at 1 ms, 7.53 % at 10 ms, 1.69 % at 60 ms, 0.36 % at
300 ms, identical in both builds (F.3), because the second node's detector sees
an already-limited signal and computes no gain. It still is not an ask: what
reaches L7's 1 % bound is the **release default**, a Python-side choice (0.36 %
at 300 ms), so §8.2's open question is answered "the composition fails, and the
default is where the trade lives" rather than "file a node".

*(from §7)*

1. **It reports zero latency while delaying the audio.** `Limiter` never
   overrides `_core.Effect.LATENCY_SAMPLES = 0` (`_core.py:140`), and three of
   its five shipped patches set lookahead: `dynamics.py:113` "Safety Catch"
   32/127 → 5.04 ms, `:114` "Brickwall" 51/127 → **8.03 ms**, `:116`
   "Broadcast" 64/127 → 10.08 ms on the 0–20 ms span at `:109`. Confirmed by
   construction this run: `program_change(2)` gives `macro(2) == 8.031 ms` and
   `latency_samples == 0`. A host aligning tracks by the reported number is out
   by up to 484 samples. This is a **Tier 1** failure, not a nicety.

*(from §7)*

2. **The lookahead makes the overshoot worse, and the docstring says the
   opposite.** `dynamics.py:82-86` claims lookahead means "the gain is already
   down when the transient arrives instead of a fraction of a millisecond after
   it — which is the difference between a limiter that catches peaks and one
   that lets the first cycle of each through." Measured (B.3), turning it on
   raises the escaping peak from 0.00 dB over the ceiling to 1.45 dB over. The
   claim is the reverse of the behaviour.

*(from §7)*

3. **The true-peak docstring is stronger than the code.** `dynamics.py:88-91`
   says `true_peak` "adds the level *between* samples to what the detector
   sees"; the node estimates **one** midpoint (`audioif_dynamics.c:167-171`) and
   still lets 1.12 dB TP through at f_s/4 (B.8). The C's own comment is honest
   about this ("proper true-peak metering oversamples by four and this does not
   pretend to be that"); the Python docstring is not.

*(from §7)*

4. **Attack is hardcoded and not a brickwall.** `dynamics.py:122` passes
   `attack_ms=0.05` and never exposes it, so the detector always ramps; the node
   supports a genuinely instantaneous attack at `attack_ms=0`
   (`audioif_dynamics.c:10-11`, measured at 18 dB in one sample, B.10). A
   brickwall's attack is not a taste knob.

*(from §7)*

5. **`reset()` silently reverts the surface.** `_core.Effect.reset()` ends with
   `self.program_change(0)` (`_core.py:374`), so resetting a limiter a host has
   set up throws away the ceiling it was given. Shared with `Compressor`.

*(from §7)*

6. **The node takes the module's rate, not the source's.** `dynamics.py:123`
   passes `_core.SAMPLE_RATE` and `_core.channel_count()`, globals set by
   `configure()` — the pre-contract shape roadmap §3 retires.

*(from §7)*

7. **No gain into the ceiling.** The surface (`dynamics.py:99`) has Ceiling,
   Release, Lookahead and True Peak but nothing that drives the signal *at* the
   ceiling, so the class cannot do the one thing a limiter is usually reached
   for. `makeup_db` would be the wrong fix (it is applied after the gain,
   `audioif_dynamics.c:310-311`).
