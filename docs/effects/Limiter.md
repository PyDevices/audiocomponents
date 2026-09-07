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
**Status:** seeded 2026-09-06 (Phase 0), audited twice for licences and
citations (Appendices A, D) and attacked once by a trait critic (Appendix E);
both sources were reached in every run and both licence calls stand unchanged.
**Frozen for the rebuild on 2026-09-07** by the class builder, which settled
five of §8's six opens, re-ran every palette claim on the pin for itself, and
found three of them stale. The trait table below is the one the class is built
and measured against; **Appendix G** is the run record. *(The three passes'
own accounts of themselves: App. R.)*

## 1. The circuit, in one paragraph

There is no circuit; there is a signal flow, and it has four parts a
compressor does not. **(a) A delay on the audio path**, so the detector sees a
peak before the audio carrying it reaches the output — the *lookahead*, and the
only latency this class ever has. **(b) A running maximum over that window**
before the detector, so the gain stays down until the peak has physically left
the delay line; S2's central result is that a delay alone "is not a foolproof
cure for clipping". **(c) A gain computer with infinite ratio and no knee above
the ceiling**, with the gain *smoothed* — S2's tension is that smoothing alone
"causes overshoots and leads to either clipped output or non-maximal signal
levels". **(d) A true-peak detector**, because the ceiling is a promise about
the reconstructed waveform and not about the samples: S1's Annex 2 fixes 4×
oversampling and gives 3 dB as the sample-peak meter's under-read at f_s/4.
Panel-wise there is a Ceiling, a Release, a Lookahead, a gain into the ceiling
and a true-peak switch; everything else is a consequence.

*(The full derivation, with both sources quoted at length, is in **App. R**.)*

## 2. Sources and license calls

| # | Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|---|
| S1 | ITU-R, *Recommendation BS.1770-5* (11/2023) … (App. S1) | The true-peak algorithm (attenuate 12.04 dB → 4× … (App. S1) | "© ITU 2023. All rights reserved. No part of … (App. S1) | https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf | 2026-09-06 — PDF fetched; unreadable to the fetch tool, text extracted locally with `pypdf` |
| S2 | Perttu Hämäläinen, "Smoothing of the Control Signal without Clipped … (App. S2) | Why a delay alone does not prevent clipping … (App. S2) | No copyright or licence line is printed … (App. S2) | https://www.dafx.de/paper-archive/2002/DAFX02_Hamalainen_smoothing_peak_limiters.pdf | 2026-09-06 — PDF fetched, text extracted locally with `pypdf` |

**Looked for and not found.** *Giannoulis, Massberg & Reiss, "Digital Dynamic
Range Compressor Design—A Tutorial and Analysis"* (JAES 60(6), 2012) — the
standard tutorial for gain-computer and detector topology — is **still not
reached**, and nothing from it is cited. FabFilter's Pro-L help page was not
fetched and is not cited. A hardware brickwall was not hunted, deliberately
(the Standout note above). *(The host probing behind the first claim: App. R.)*

Copyleft sources are measured or read as papers, never read for code structure
(vision §5). Neither source here is code; S2 carries no licence at all and is
treated as copyleft, S1 is read under an explicit all-rights-reserved notice.
The audit record is Appendices A and D; where they disagree, D wins.

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — the textbook properties, stated so they can fail

A design grade "may state the textbook property as its traits" (vision §4.1).
These are those properties, each with the number that fails it. **The trait and
the number that disconfirms it are here in full — they are what the gate
checks; the source reading, the confidence and the measurement recipe are in
App. T**, one cell-level reference per row.

| # | Trait (falsifiable as stated) | Disconfirmed by |
|---|---|---|
| L1 | **The ceiling is a true-peak promise.** With Lookahead and True Peak on, the output's true-peak level by S1's Annex 2 method exceeds the Ceiling macro by no more than **0.5 dB *(own, anchored on S1's 0.554 dB worst case at 4×)*** on every probe, at 48 kHz and 44.1 kHz. **The probe set must contain a worst-phase tone at f_s/4** — material with no inter-sample peak in it cannot express what is being measured | Any probe reading more than +0.5 dB TP above the ceiling; **or an evidence pack whose probe set contains no f_s/4 worst-phase tone** |
| L2 | **Lookahead never creates overshoot.** Sweeping Lookahead 0 → maximum in 1 ms steps, the output's *sample* peak exceeds the ceiling by no more than **0.1 dB *(own)*** at every setting, **and does not grow with lookahead**. Two separate failures: a build could sit under the ceiling everywhere and still show S2's pathology as a rising trend | A sample peak more than 0.1 dB above the ceiling at any setting, **or** a peak that rises with lookahead |
| L3 | **A peak shorter than the lookahead is still caught — at every setting, not just the longest.** A single-sample impulse at 0 dBFS into a −12 dBFS ceiling leaves the output no more than **0.1 dB *(own)*** above the ceiling at **every non-zero lookahead setting** | The impulse passing more than 0.1 dB over the ceiling at any non-zero lookahead setting |
| L4 | **Reported latency equals the lookahead, exactly.** `latency_samples == floor(lookahead_ms × fs / 1000)` at 48 kHz, 44.1 kHz and 22.05 kHz, for every patch and every position of the Lookahead macro, and the click agrees **to the sample**. *(The seed said `round`; the node truncates, `audioif_dynamics.c:126-127` — G.3.)* | Any patch or macro position where the reported number and the measured click offset differ by one sample or more |
| L5 | **Zero by default.** Constructed with no options, and on the default patch, `latency_samples` is 0, Lookahead is 0 ms and True Peak is off | A non-zero default for either option, or a non-zero `latency_samples` on patch 0 |
| L6 | **Infinite ratio, hard knee.** Above the ceiling the static I/O curve's slope is ≤ **0.02 dB/dB *(own)*** over 24 dB of input, and at Knee zero the fitted knee width is ≤ **0.5 dB *(own)***. The 24 dB span is measured at a **−24 dBFS ceiling**: int16 has no headroom above 0 dBFS to put the other 24 dB in | A slope above 0.02 dB/dB anywhere in the 24 dB span, **or** a fitted knee wider than 0.5 dB at Knee zero |
| L7 | **Smoothing is a documented trade, not an accident.** At the default patch a 60 Hz sine driven 12 dB into the ceiling shows THD ≤ **1 % *(own)***; the Release macro's fastest setting is named in the docstring as a distortion setting, and its measured THD is recorded rather than bounded | THD above 1 % at the default patch, **or** a docstring that does not name the trade |

### Tier 3 — cost and latency

Options that add latency, each with its default:

| Option | Adds | Default |
|---|---|---|
| `lookahead_ms` (macro 2) | `floor(ms × fs/1000)` samples — the node truncates, it does not round (`audioif_dynamics.c:126-127`) — up to 480 at 10 ms / 48 kHz | **0 — off** |
| `true_peak` (macro 4) | **none.** The 4× detector runs on the detector signal only; its group delay never reaches the audio path, and the measured click delay with True Peak on and Lookahead at 0 is 0 samples (G.4) | **off** |

`hold_ms` is gone from this table: N-L1 was refuted by the palette (§5) and the
macro it would have driven is not on the surface. The module does carry a
`hold_ms` option, but it drives the *gate* machine only — `gate_machine =
config->hold_frames != 0u && config->mode == AUDIOIF_DYNAMICS_GATE`
(`audioif_dynamics.c:452-453`) — so it is not reachable from `DYN_LIMIT` or
`DYN_COMPRESS` (G.6).

Reported `latency_samples` is verified by the click measurement at the class
gate (L4). For the stompbox case (vision §9a): the default patch puts **zero**
in the effect and the whole round-trip budget in the platform's buffers.

`capabilities` = `()`. A ceiling has no tempo; the class does not read the
transport.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Nodes: two `audiodynamics.Dynamics` in series**, and the second is the one
that makes the promise. Portability tier **audioif**
(`audioif/docs/upstream-diff.md:661`), `REQUIRES = ("audiodynamics",)`.

1. **shape** — `DYN_COMPRESS` at `ratio=1e6`, carrying the Knee, the Lookahead
   and the true-peak detector. A compressor node because `DYN_LIMIT`'s gain
   computer has no knee term at all (`audioif_dynamics.c:369-370`), measured
   (G.5); at `ratio=1e6` and Knee 0 its slope above the threshold measures
   **0.0000 dB/dB**, which is L6's brickwall.
2. **catch** — `DYN_LIMIT` at the ceiling, `attack_ms=0`, no lookahead. This is
   the whole answer to L2 and L3: F.1's composition, reproduced on the pin
   (G.1).

Three Python-side choices carry the rest, each measured rather than argued, and
each derived in **App. R**: **the Gain macro costs no node** (`threshold =
ceiling − gain` with `makeup_db = gain` is algebraically gain-then-limit);
**the wire endpoint is Ceiling 0 dB with Gain 0**, byte-exact once the class
adds **+0.0002 dB** to every threshold to cancel the node's own detector
epsilon (`audioif_dynamics.c:749`, G.8); and **the lookahead is set to the
midpoint of the node's truncation bin**, so the reported `latency_samples`
cannot land one sample out (G.3).

A mono source is limited on one channel, not summed: the kernel selects mono or
stereo at `audioif_dynamics.c:470` and the cross-channel max (`:556-560`)
collapses. A stereo source is **always channel-linked** and it is not
switchable; the docstring says so and the kit measures it. *(The seed and the
palette verification both cited `:235` and `:263-269` for those two lines; at
the pin those are envelope and gate-state resets. The file wins.)*

*(More of §4 is in **App. R**, including the seed's "L1 is the one that is
genuinely not reachable" — which is **stale**, see §5 and G.2.)*

## 5. Node asks

Both are additive options on `audiodynamics`, audioif's own module (D1); neither
touches a CircuitPython-ported node.

**Neither ask stands. No issue is owed.**

- **N-L1 — a hold window on the detector. REFUTED BY PALETTE** (2026-09-07;
  reproduced G.1): two `Dynamics` in series hold −12.00 dBFS against a
  −12.00 dBFS ceiling at every lookahead setting, on both probes L2 and L3
  name.
- **N-L2 — a BS.1770-grade true-peak detector. LANDED** (class builder,
  2026-09-07): the node on the pin has three true-peak states, and
  `true_peak=2` is a four-phase twelve-tap polyphase FIR (taps
  `audioif_dynamics.c:310-345`, applied at `:576-589`). Measured **+0.17 dB TP**
  over a −6 dBFS ceiling at f_s/4 worst phase, where L1 allows 0.5 dB (G.2).

*(Both asks as the seed wrote them, and the refutation that failed at the time,
are in **App. R** — superseded by the two lines above.)*

## 6. Proposed surface

**Macros — 6 of the 16 allowed** (the seed proposed 8). A limiter with fourteen
knobs is a compressor, and two of the seed's eight had no node behind them.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Ceiling | UNIPOLAR | −24…0 dB | the output ceiling every mastering limiter has; at 0 dB the class is a wire (§4) |
| 1 | Gain | UNIPOLAR | 0…24 dB | drive into the ceiling — the "loudness" knob; folded into `threshold` + `makeup_db`, so it is *before* the limiter and costs no node (§4) |
| 2 | Lookahead | UNIPOLAR | 0…10 ms | how far ahead the detector reads; **0 by default**, and the class's only latency |
| 3 | Release | UNIPOLAR | 5 ms…2 s log | recovery after the peak has passed; **this is where L7's trade lives** |
| 4 | True Peak | TOGGLE | off / on | inter-sample peaks (S1); off → `true_peak=0`, on → `true_peak=2`, the 4× detector. **Off by default** |
| 5 | Knee | UNIPOLAR | 0…12 dB | 0 is the brickwall of L6; above zero it becomes a soft limiter |

**Dropped: Hold** (N-L1 refuted, and `hold_ms` reaches neither `DYN_LIMIT` nor
`DYN_COMPRESS` — G.6) **and Mix** (a parallel dry path walks peaks straight past
the ceiling, which is the one promise this class makes; Tier 1's wire endpoint
does not need it). `true_peak=1`, the half-band estimate, is not exposed
either: it reads +1.07 dB where L1 allows 0.5 (G.2). Each reason in full in
**App. R**.

**Patches** (names describe settings, never products). Patch 0 is the
constructor's defaults on the 0–127 grid.

| # | Name | Values | Shape |
|---|---|---|---|
| 0 | Safety Ceiling | `(122, 0, 0, 72, 0, 0)` | −0.94 dB, no gain, no lookahead, no true peak, 149 ms release — zero latency, the default, and the cheapest state the class has |
| 1 | Catch The Peaks | `(122, 0, 19, 53, 127, 0)` | −0.94 dB, 1.50 ms lookahead, true peak on, 61 ms release |
| 2 | Loud | `(125, 64, 38, 38, 127, 0)` | −0.38 dB, 12.1 dB of gain, 2.99 ms lookahead, 30 ms release, true peak on |
| 3 | Soft Ceiling | `(116, 0, 0, 78, 0, 95)` | −2.08 dB, knee 8.98 dB, 198 ms release, no lookahead |
| 4 | Delivery Ceiling | `(122, 0, 25, 72, 127, 0)` | −0.94 dB, true peak on, 1.97 ms lookahead, 149 ms release, no gain |

The seed's sixth patch, `"Safety Ceiling - lean"`, is **not shipped**: patch 0
already has True Peak off and Lookahead at 0, so it would have been patch 0
under a second name. The seed's 100 ms release default is raised to **149 ms**
(macro 72): at 100 ms the 60 Hz THD probe reads **1.05 %** against L7's 1 % bar
(G.4). Both, in full, in **App. R**.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/dynamics.py` and `_core.py`.

1. **It reports zero latency while delaying the audio.** `Limiter` never …  *(argument in full: App. R)*
2. **The lookahead makes the overshoot worse, and the docstring says the …  *(argument in full: App. R)*
3. **The true-peak docstring is stronger than the code.** `dynamics.py:88-91` …  *(argument in full: App. R)*
4. **Attack is hardcoded and not a brickwall.** `dynamics.py:122` passes …  *(argument in full: App. R)*
5. **`reset()` silently reverts the surface.** **Not a defect — the contract
   requires it.** `docs/audio-component-api.md:201-202`: "`reset()` releases all
   instrument notes, clears component DSP history, and restores patch `0`."
   `_component.Component.reset()` does the same on purpose. The rebuild does
   not "fix" this and must not. *(the seed's argument, in full: App. R)*
6. **The node takes the module's rate, not the source's.** `dynamics.py:123` …  *(argument in full: App. R)*
7. **No gain into the ceiling.** The surface (`dynamics.py:99`) has Ceiling, …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

Six were open in the seed. **Five are settled here; one is not this class's to
settle.** Each settlement's argument is in **App. R**; the run behind it is in
**App. G**.

1. **The smallest useful lookahead — SETTLED: there is no minimum.** On the
   two-node build L2 and L3 pass at *every* setting including 0 ms (G.1), and
   L7 is a function of Release, not Lookahead (G.4). The default stays 0, which
   is also what L5 requires.
2. **Is separate gain smoothing composable? — SETTLED: no.** Two `Dynamics` in
   series measure the same THD as one at every release (F.3, reproduced G.4).
   **The Release default is where the trade lives**, and §6 sets it from the
   measurement.
3. **The perceptible-monitoring-delay figure (vision §10.8) — STILL OPEN**, and
   Phase 0's survey owes it. Nothing in the rebuild depends on it: the default
   patch reports **0 samples**, and the docstring names the milliseconds when a
   musician turns Lookahead on.
4. **True-peak in the gain computer or only the detector? — SETTLED: only the
   detector.** The 4× detector alone holds the worst-phase f_s/4 tone to
   **+0.17 dB TP** over a −6 dBFS ceiling (G.2), inside L1's 0.5 dB.
5. **Does L1's probe set exist? — SETTLED: yes.** `tone_fs4` is in the kit at
   48 kHz and 44.1 kHz, levelled so its sample peak lands on −6.00 dBFS and its
   true peak on −2.99 dB TP (`docs/effects-kit-spec.md:152`).
6. **Stereo linking is fixed on. — Recorded, not asked.** Unchanged.

**Three of the seed's palette claims are stale, and the rebuild is built on the
corrections** — each re-read from the C and re-measured on the pin (App. G),
not inferred: `true_peak` is a **level, not a flag**, and `true_peak=2` is the
4× detector N-L2 asked for, so **L1 is reachable and no issue is owed** (G.2);
`DYN_LIMIT` **ignores `knee_db`**, so the Knee macro rides `DYN_COMPRESS` at
`ratio=1e6` (G.5); and the node **truncates** the lookahead in float32, so L4's
`round` becomes `floor` and a naive double-precision restatement disagrees with
the node in 22 of 489 cases at 44.1 kHz (G.3).

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

### G. The class builder's palette runs, 2026-09-07

Everything §§3–8 moved comes from one run of
`tools/phase2_probes/limiter_palette.py`, committed beside this file. It probes
the **node**, never the class; the class's own numbers are
`docs/effects/Limiter-evidence.md`. Command and output, verbatim:

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/limiter_palette.py
Limiter palette probes, audioif at the pin, CPython
========================================================================

G.1  the catch stage, reproduced on the pin (seed Appendix F.1)
     ceiling -12 dBFS, release 60 ms; sample peak of the output
     probe          lookahead   lone shape node    + catch stage
     1 ms burst         0.00 ms     -12.00 dBFS        -12.00 dBFS
     1 ms burst         0.50 ms     -11.93 dBFS        -12.00 dBFS
     1 ms burst         1.00 ms     -11.86 dBFS        -12.00 dBFS
     1 ms burst         2.00 ms     -11.71 dBFS        -12.00 dBFS
     1 ms burst         5.00 ms     -11.28 dBFS        -12.00 dBFS
     1 ms burst        10.00 ms     -10.55 dBFS        -12.00 dBFS
     1-sample impulse   0.00 ms     -12.00 dBFS        -12.00 dBFS
     1-sample impulse   0.50 ms     -11.93 dBFS        -12.00 dBFS
     1-sample impulse   1.00 ms     -11.86 dBFS        -12.00 dBFS
     1-sample impulse   2.00 ms     -11.71 dBFS        -12.00 dBFS
     1-sample impulse   5.00 ms     -11.28 dBFS        -12.00 dBFS
     1-sample impulse  10.00 ms     -10.55 dBFS        -12.00 dBFS

G.2  true_peak is a level, not a flag: the 4x detector N-L2 asked
     for is on the pin. Worst-phase f_s/4 tone, sample peak
     -0.50 dBFS, ceiling -6 dBFS, release 60 ms, catch stage on.
     true_peak  lookahead   sample peak    true peak   over ceiling
             0    0.00 ms      -6.00 dBFS      -2.99 dBTP    +3.01 dB
             0    1.50 ms      -6.00 dBFS      -2.99 dBTP    +3.01 dB
             0    5.00 ms      -6.00 dBFS      -2.99 dBTP    +3.01 dB
             1    0.00 ms      -7.94 dBFS      -4.93 dBTP    +1.07 dB
             1    1.50 ms      -7.94 dBFS      -4.93 dBTP    +1.07 dB
             1    5.00 ms      -7.94 dBFS      -4.93 dBTP    +1.07 dB
             2    0.00 ms      -8.84 dBFS      -5.83 dBTP    +0.17 dB
             2    1.50 ms      -8.84 dBFS      -5.83 dBTP    +0.17 dB
             2    5.00 ms      -8.84 dBFS      -5.83 dBTP    +0.17 dB
     L1 allows +0.50 dB. Only true_peak=2 is inside it.

G.3  the node truncates the lookahead in float32, and a naive
     double-precision restatement disagrees with it.
     `lookahead_frames = (uint32_t)(ms * fs / 1000.0f)`, audioif_dynamics.c:127-128
     naive: 44100 Hz, 0.294784580 ms -> wanted 12 samples, got 13
     naive: 44100 Hz, 0.566893424 ms -> wanted 25 samples, got 24
     naive: 44100 Hz, 0.589569161 ms -> wanted 25 samples, got 26
     naive: 44100 Hz, 0.657596372 ms -> wanted 29 samples, got 28
     489 cases: naive form wrong 22 times, bin-midpoint form wrong 0 times.
     The class sets the node to the midpoint of the truncation bin and reports floor().

G.4  L7 lives on the Release default. 60 Hz sine at 0 dBFS into a
     -12 dBFS ceiling; THD h2..h10 over 0.5 s of steady state.
     release    lone shape   + catch    catch + 1.5 ms lookahead
        1.0 ms     25.78 %     25.78 %      17.37 %
       10.0 ms      7.53 %      7.53 %       5.44 %
       30.0 ms      3.13 %      3.13 %       2.41 %
       60.0 ms      1.69 %      1.69 %       1.34 %
      100.0 ms      1.05 %      1.05 %       0.85 %
      150.0 ms      0.71 %      0.71 %       0.59 %
      200.0 ms      0.54 %      0.54 %       0.45 %
      300.0 ms      0.36 %      0.36 %       0.30 %
     L7's bar is 1 %. 100 ms reads 1.05 %; the patch uses 149 ms.

     True Peak on, Lookahead 0: click delay, 48 kHz
       0 samples - the 4x detector's group delay never reaches the audio path.

G.5  DYN_LIMIT ignores knee_db; DYN_COMPRESS at ratio 1e6 is the
     brickwall. 1 kHz sine, threshold -12 dBFS, steady state.
     in dBFS           -13.0     -12.0      -6.0      -0.1
     LIMIT knee 0    -13.000   -12.001   -12.001   -12.001
     LIMIT knee 12   -13.000   -12.001   -12.001   -12.001
     COMP 1e6 kn 0   -13.000   -12.001   -12.001   -12.001
     COMP 1e6 kn12   -14.043   -13.501   -12.001   -12.001
     The two LIMIT rows are identical: knee_db is not in that gain
     computer at all (audioif_dynamics.c:368-370).

G.6  hold_ms exists on the module and does nothing here.
     `gate_machine = hold_frames != 0 && mode == DYN_GATE`, audioif_dynamics.c:452-453
     hold_ms=  0.0 on DYN_COMPRESS, 5 ms lookahead -> peak   -11.28 dBFS
     hold_ms= 20.0 on DYN_COMPRESS, 5 ms lookahead -> peak   -11.28 dBFS

G7  audiomixer cannot be the Gain stage: voice level is clamped
    to 0..1 (audioif/src/cpython/audiomixer.py:143).
    level set to 4.0, reads back 4.0; in -20.00 dBFS -> out -20.00 dBFS

G.8  the wire endpoint, and the detector epsilon that spoils it.
     `gain_to_db(state->envelope + 1e-6f)`, audioif_dynamics.c:749
     threshold offset  +0.00000 dB ->    28 of 16384 samples differ
     threshold offset  +0.00005 dB ->     0 of 16384 samples differ
     threshold offset  +0.00020 dB ->     0 of 16384 samples differ
     threshold offset  +0.00100 dB ->     0 of 16384 samples differ
     and the offset does not move the ceiling:
     offset +0.00000 dB, ceiling  -24.00 dB -> out peak  -24.0022 dBFS
     offset +0.00000 dB, ceiling  -12.00 dB -> out peak  -12.0010 dBFS
     offset +0.00000 dB, ceiling   -1.00 dB -> out peak   -1.0002 dBFS
     offset +0.00020 dB, ceiling  -24.00 dB -> out peak  -24.0022 dBFS
     offset +0.00020 dB, ceiling  -12.00 dB -> out peak  -11.9999 dBFS
     offset +0.00020 dB, ceiling   -1.00 dB -> out peak   -0.9999 dBFS

G.9  gain into a high ceiling clips inside the shape node, and the
     catch stage still lands the ceiling exactly.
     ceiling -0.3 dBFS, 1 ms burst 12 dB under it
     gain  0.0 dB, lookahead  0.0 ms -> shape node  -12.000 dBFS (0 samples clipped), final  -12.000 dBFS
     gain 12.0 dB, lookahead  0.0 ms -> shape node   -0.300 dBFS (0 samples clipped), final   -0.300 dBFS
     gain 12.0 dB, lookahead  3.0 ms -> shape node   -0.000 dBFS (90 samples clipped), final   -0.300 dBFS
     gain 12.0 dB, lookahead 10.0 ms -> shape node   -0.000 dBFS (96 samples clipped), final   -0.300 dBFS
```

**What this run changed, and what it only confirmed.**

*Confirmed, unchanged:* G.1 reproduces Appendix F.1 to the hundredth of a dB on
both probes; G.4's lone-node column reproduces B.7 and F.3 (25.78 / 7.53 /
1.69 / 0.36 % against 25.79 / 7.53 / 1.69 / 0.36); G.5's `DYN_LIMIT` rows
confirm the gain computer is the one-line law B.10 and L6 both read off the C.

*Changed:* G.2 (N-L2 has landed, L1 is reachable), G.3 (L4's `round` is
`floor`), G.5 (the Knee macro needs `DYN_COMPRESS`), G.6 (`hold_ms` exists but
not for this mode), G.7 (`audiomixer` cannot be the Gain stage), G.8 (the wire
endpoint needs a +0.0002 dB threshold offset), and §6's Release default
(100 ms reads 1.05 %, over L7's 1 % bar).

*Recorded, and not a trait:* G.9. With 12 dB of Gain into a −0.3 dBFS ceiling
and lookahead on, the shape node's own output clamps at full scale for about
90 samples of a 1 ms burst. The final output still lands on −0.300 dBFS exactly,
because the catch stage would have pulled that region down in any case; what
differs is that the overshoot region is flattened rather than scaled. No trait
bounds it, and buying it back would cost an internal headroom stage — which
would in turn cost the byte-exact wire endpoint of G.8, since a −3 dB / +3 dB
round trip through int16 is not the identity. It is left as it is, on purpose.

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

*(from §1, moved 2026-09-07 under the length rule by the class builder; the section above is the compressed reading, this is what it was compressed from)*


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


*(from §2, moved 2026-09-07 under the length rule by the class builder; the section above is the compressed reading, this is what it was compressed from)*


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


*(from §3, moved 2026-09-07 under the length rule by the class builder; the section above is the compressed reading, this is what it was compressed from)*


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
| L4 | **Reported latency equals the lookahead, exactly.** `latency_samples == floor(lookahead_ms × fs / 1000)` at 48 kHz, 44.1 kHz and 22.05 kHz, for every patch and every position of the Lookahead macro, and the click measurement agrees with the report **to the sample**. *(The seed said `round`; the node truncates, `audioif_dynamics.c:126-127`, and the class builder measured the difference — G.3.)* | Vision §9a ("reported in `latency_samples` … (App. L4) | high | Any patch or macro position where the reported number and the measured click offset differ by one sample or more | Click through the class against … (App. L4) |
| L5 | **Zero by default.** Constructed with no options, and on the default patch, `latency_samples` is 0, Lookahead is 0 ms and True Peak is off | Vision §9a ("every latency-adding option … (App. L5) | high | A non-zero default for either option, or a non-zero `latency_samples` on patch 0 | Construct and read … (App. L5) |
| L6 | **Infinite ratio, hard knee.** Above the ceiling the static I/O curve's slope is ≤ **0.02 dB/dB *(own)*** over 24 dB of input, and at Knee-macro zero the fitted knee width is ≤ **0.5 dB *(own)*** — a brickwall, not a high-ratio compressor. The 24 dB span is measured at a **−24 dBFS ceiling**, because int16 has no headroom above 0 dBFS to put the other 24 dB in | The definition of the thing … (App. L6) | high | A slope above 0.02 dB/dB anywhere in the 24 dB span, **or** a fitted knee wider than 0.5 dB at Knee zero | Static I/O curve … (App. L6) |
| L7 | **Smoothing is a documented trade, not an accident.** At the default patch a 60 Hz sine driven 12 dB into the ceiling shows THD ≤ **1 % *(own)***; the Release macro's fastest setting is documented in the docstring as a distortion setting, and the measured THD there is recorded in the evidence pack rather than bounded | S2 §1–2 verbatim: the gain must be controlled … (App. L7) | high | THD above 1 % at the default patch, or a docstring that does not name the trade | Harmonic spectrum of a 60 Hz sine … (App. L7) |

### Tier 3 — cost and latency

Options that add latency, each with its default:

| Option | Adds | Default |
|---|---|---|
| `lookahead_ms` (macro 2) | `floor(ms × fs/1000)` samples — the node truncates, it does not round (`audioif_dynamics.c:126-127`) — up to 480 at 10 ms / 48 kHz | **0 — off** |
| `true_peak` (macro 4) | **none.** The 4× detector runs on the detector signal only; its group delay never reaches the audio path, and the measured click delay with True Peak on and Lookahead at 0 is 0 samples (G.4) | **off** |

`hold_ms` is gone from this table: N-L1 was refuted by the palette (§5) and the
macro it would have driven is not on the surface. The module does carry a
`hold_ms` option, but it drives the *gate* machine only — `gate_machine =
config->hold_frames != 0u && config->mode == AUDIOIF_DYNAMICS_GATE`
(`audioif_dynamics.c:452-453`) — so it is not reachable from `DYN_LIMIT` or
`DYN_COMPRESS` (G.6).

Reported `latency_samples` is verified by the click measurement at the class
gate (L4). For the stompbox case (vision §9a): the default patch puts **zero**
in the effect and the whole round-trip budget in the platform's buffers.

`capabilities` = `()`. A ceiling has no tempo; the class does not read the
transport.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*


*(from §4, moved 2026-09-07 under the length rule by the class builder; the section above is the compressed reading, this is what it was compressed from)*


**Nodes: two `audiodynamics.Dynamics` in series**, and the second is the one
that makes the promise. Portability tier **audioif**
(`audioif/docs/upstream-diff.md:661`), `REQUIRES = ("audiodynamics",)`.

1. **shape** — `DYN_COMPRESS` at `ratio=1e6`, carrying the Knee, the Lookahead
   and the true-peak detector. It is a compressor node because `DYN_LIMIT`'s
   gain computer has no knee term at all (`over > 0 ? -over : 0`,
   `audioif_dynamics.c:369-370`), so a Knee macro on `DYN_LIMIT` would move
   nothing — measured, the static curve is identical at Knee 0 and Knee 12
   (G.5). At `ratio=1e6` and Knee 0 the compress computer measures a slope of
   **0.0000 dB/dB** above the threshold (G.5), which is L6's brickwall.
2. **catch** — `DYN_LIMIT` at the ceiling, `attack_ms=0`, no lookahead. This is
   the whole answer to L2 and L3: F.1's composition, reproduced exactly on the
   pin by the class builder (G.1).

**Gain into the ceiling costs no node.** `threshold = ceiling − gain` with
`makeup_db = gain` is algebraically identical to gain-then-limit — below the
threshold the output is `L + G`, above it the output is `T + G = ceiling` — so
§7.7's defect is fixed inside the node the class already builds. The seed's
worry that `makeup_gain` is applied *after* the gain computer
(`audioif_dynamics.c:679`) is exactly what the threshold shift compensates.
Measured across the Gain macro's whole span in the evidence pack, not argued.
`audiomixer.Mixer` could not have done it in any case: its voice level is
clamped to 0..1 (`audioif/src/cpython/audiomixer.py:143`), measured (G.7).

**The wire endpoint is Ceiling at 0 dB with Gain at 0** — there is no Mix macro
(§6). It is byte-exact only once the class cancels the node's own detector
epsilon: `gain_to_db(envelope + 1e-6)` (`audioif_dynamics.c:749`) reads a
full-scale sample as very slightly over 0 dBFS, so 42 of 16384 ramp samples
came back 1 LSB down. The class adds **+0.0002 dB** to the threshold it hands
each node, which takes that to 0 of 16384 and moves the measured ceiling by at
most 0.0003 dB — four orders of magnitude under one LSB (G.8).

A mono source is limited on one channel, not summed: the kernel selects mono or
stereo at `audioif_dynamics.c:470` and the cross-channel max (`:556-560`)
collapses. *(The seed and the palette verification both cited `:235` and
`:263-269` for these two; at the pin those lines are envelope and gate-state
resets. The file wins: every citation in this section was re-read by
`grep -n` on 2026-09-07 and the wrong ones are corrected here rather than
carried.)* A stereo source is **always channel-linked** — the detector takes
the maximum across channels — which is the right default for a limiter and is
not switchable; the docstring says so and the kit measures it.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.
The seed's "L1 is the one that is genuinely not reachable" is there, and it is
**stale**: see §5 and G.2.)*


*(from §6, moved 2026-09-07 under the length rule by the class builder; the section above is the compressed reading, this is what it was compressed from)*


**Macros — 6 of the 16 allowed** (the seed proposed 8). A limiter with
fourteen knobs is a compressor, and two of the seed's eight had no node behind
them.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Ceiling | UNIPOLAR | −24…0 dB | the output ceiling every mastering limiter has; at 0 dB the class is a wire (§4) |
| 1 | Gain | UNIPOLAR | 0…24 dB | drive into the ceiling — the "loudness" knob; folded into `threshold` + `makeup_db`, so it is *before* the limiter and costs no node (§4) |
| 2 | Lookahead | UNIPOLAR | 0…10 ms | how far ahead the detector reads; **0 by default**, and the class's only latency |
| 3 | Release | UNIPOLAR | 5 ms…2 s log | recovery after the peak has passed; **this is where L7's trade lives** |
| 4 | True Peak | TOGGLE | off / on | inter-sample peaks (S1); off → `true_peak=0`, on → `true_peak=2`, the 4× detector. **Off by default** |
| 5 | Knee | UNIPOLAR | 0…12 dB | 0 is the brickwall of L6; above zero it becomes a soft limiter |

**Dropped from the seed's eight, each with its reason.**

- **Hold** — N-L1 is refuted (§5) and `hold_ms` reaches neither `DYN_LIMIT` nor
  `DYN_COMPRESS` (Tier 3, G.6). A knob with no node behind it is a lie on a
  panel.
- **Mix** — a parallel dry path walks peaks straight past the ceiling, which is
  the one promise this class makes; every Tier 2 row would have had to be
  restated "at Mix = 1". Tier 1's wire endpoint does not need it: Ceiling at
  0 dB with Gain at 0 is byte-identical to the source (§4, G.8). `true_peak=1`,
  the half-band estimate, is not exposed either — it reads +1.07 dB where L1
  allows 0.5 (G.2), so a "True Peak" switch that selected it would not keep the
  promise its label makes.

**Patches** (names describe settings, never products). Patch 0 is the
constructor's defaults on the 0–127 grid.

| # | Name | Values | Shape |
|---|---|---|---|
| 0 | Safety Ceiling | `(122, 0, 0, 72, 0, 0)` | −0.94 dB, no gain, no lookahead, no true peak, 149 ms release — zero latency, the default, and the cheapest state the class has |
| 1 | Catch The Peaks | `(122, 0, 19, 53, 127, 0)` | −0.94 dB, 1.50 ms lookahead, true peak on, 61 ms release |
| 2 | Loud | `(125, 64, 38, 38, 127, 0)` | −0.38 dB, 12.1 dB of gain, 2.99 ms lookahead, 30 ms release, true peak on |
| 3 | Soft Ceiling | `(116, 0, 0, 78, 0, 95)` | −2.08 dB, knee 8.98 dB, 198 ms release, no lookahead |
| 4 | Delivery Ceiling | `(122, 0, 25, 72, 127, 0)` | −0.94 dB, true peak on, 1.97 ms lookahead, 149 ms release, no gain |

The seed's sixth patch, `"Safety Ceiling - lean"`, is **not shipped**: patch 0
already has True Peak off and Lookahead at 0, so the lean patch would have been
patch 0 under a second name. Every macro that costs anything is already at zero
there. If the board run puts patch 0 over the S3 budget, the remedy is a
construction option that drops the catch stage, not a patch — and that would
cost L2 and L3, so it is a decision for the gate, not for this session.

The seed's release default of 100 ms is raised to **149 ms** (macro 72): at
100 ms the 60 Hz THD probe measures **1.05 %** and L7's bar is 1 % (G.4). The
seed proposed a number; the measurement moved it.


*(from §8, moved 2026-09-07 under the length rule by the class builder; the section above is the compressed reading, this is what it was compressed from)*


Six were open in the seed. **Five are settled here; one is not this class's to
settle.** Each settlement names the run in Appendix G or the seed evidence it
was read from.

1. **What is the smallest useful lookahead? — SETTLED: there is no minimum, and
   there is no "default when on".** The seed proposed 1.5 ms from S2's
   delay-vs-smoothing trade, with no sourced figure. On the two-node build, L2
   and L3 pass at **every** setting including 0 ms (G.1), and L7 is a function
   of Release and not of Lookahead — at a 60 ms release the THD is 1.69 % with
   no lookahead and 1.34 % with 1.5 ms of it (G.4), so lookahead only helps.
   The shortest window that passes all three is therefore 0 ms, which is also
   L5's required default, and the macro simply stays where the musician puts
   it. The patches that turn it on use 1.5 ms (patch 1), 1.97 ms (patch 4) and
   2.99 ms (patch 2), which are settings, not thresholds.
2. **Is separate gain smoothing composable? — SETTLED: no.** F.3 measured two
   `Dynamics` in series at the same ceiling as identical in THD to one, to two
   decimals, at every release; the class builder reproduced it (G.4: 25.78 /
   7.53 / 1.69 / 0.36 % against F.3's 25.79 / 7.53 / 1.69 / 0.36). The second
   node's detector sees an already-limited signal and computes no gain. **The
   Release default is where the trade lives**, and it is set from the
   measurement (149 ms, §6).
3. **How is the perceptible-monitoring-delay figure (vision §10.8) reached? —
   STILL OPEN, and not this class's to close.** Phase 0's survey owes it.
   Nothing in the rebuild depends on the answer: the default patch reports
   **0 samples** of latency, so the class contributes nothing to a stage
   chain's round trip until a musician turns Lookahead on, and the docstring
   names the milliseconds when they do.
4. **Does the ceiling need to be true-peak-aware in the gain computer, or only
   in the detector? — SETTLED: only in the detector.** The 4× reconstruction in
   the detector alone holds the worst-phase f_s/4 tone to **+0.17 dB TP** over
   a −6 dBFS ceiling (G.2), inside L1's 0.5 dB. Oversampling the whole gain
   path would buy 0.17 dB for four times the arithmetic; it is not proposed and
   is not needed.
5. **Does L1's probe set exist yet? — SETTLED: yes.** `tone_fs4` is in the kit,
   at 48 kHz and 44.1 kHz, levelled so its *sample* peak lands on −6.00 dBFS
   and its true peak on −2.99 dB TP (`docs/effects-kit-spec.md:152`,
   `tools/effect_probes/README.md`, and the manifest). L1's disconfirmation
   clause is satisfiable, and the evidence pack uses that probe.
6. **Stereo linking is fixed on. — Recorded, not asked.** Unchanged: the node
   maxes across channels with no option, no trait here needs an unlinked
   limiter, and it is not an ask.

**Three things the seed said about the palette are stale, and the rebuild is
built on the corrections** — each re-read from the C and re-measured on the pin
(Appendix G), not inferred:

- `true_peak` is a **level, not a flag**, and `true_peak=2` is the 4× detector
  N-L2 asked for. §4's "L1 is the one that is genuinely not reachable" and §5's
  "ASK STANDS" were both written against the older node (G.2).
- `DYN_LIMIT` **ignores `knee_db`** entirely, so the Knee macro rides a
  `DYN_COMPRESS` node at `ratio=1e6` instead (G.5).
- The node **truncates** the lookahead to whole samples in float32, so L4's
  `round` becomes `floor`, and a naive double-precision restatement of the same
  arithmetic disagrees with the node in 22 of 533 cases at 44.1 kHz (G.3).

---

*(the header's Status paragraph, moved 2026-09-07 under the length rule; the version above is what it was compressed to)*

**Status:** seed (Phase 0), written 2026-09-06; audited the same day by an
independent licence and citation pass that re-fetched both sources itself
(Appendix D); then attacked on 2026-09-06/07 by an independent **trait-critic**
pass that re-reached both sources from their own bytes (Appendix E). No earlier
draft existed; both sources were reached in every run and both licence calls
stand unchanged. The trait-critic pass changed no number and added no source
claim: it tightened four rows' wording and gave L1 the probe-material
requirement without which the row could pass on evidence that cannot express an
inter-sample peak (E.3). **Frozen for the rebuild on 2026-09-07** by the class
builder, which settled §8's six opens, re-ran every palette claim on the pin
for itself, and found three of them stale — the trait table below is the one
the class is built and measured against, and Appendix G is the run record.

*(§2's not-found account, moved 2026-09-07 under the length rule; the version above is what it was compressed to)*

**Looked for and not found this run.** *Giannoulis, Massberg & Reiss, "Digital
Dynamic Range Compressor Design—A Tutorial and Analysis"* (JAES 60(6), 2012) —
the standard tutorial for gain-computer and detector topology — was identified
and is **still not reached**. Nothing from it is cited. The three earlier
accounts of *why* are in **App. R**; the second audit's probe of the host is
the one that stands. A hardware brickwall with a published service manual was
not hunted, deliberately (see the Standout note above). FabFilter's Pro-L help
page appeared in search results with a lookahead figure; it was **not fetched**
and is not cited.

Copyleft sources are measured or read as papers, never read for code structure
(vision §5). Neither source here is code; S2 carries no licence at all and is
treated as copyleft, S1 is read under an explicit all-rights-reserved notice.
The licence and citation audit's record is Appendices A and D; where they
disagree, D is the later reading and wins.

*(§5's two ask entries, moved 2026-09-07 under the length rule; the version above is what it was compressed to)*

- **N-L1 — a hold window on the detector.** **REFUTED BY PALETTE**
  (palette verification, 2026-09-07; reproduced by the class builder, G.1).
  Two `Dynamics` in series hold −12.00 dBFS against a −12.00 dBFS ceiling at
  every lookahead setting, on both probes L2 and L3 name. *(argument in full:
  App. R)*
- **N-L2 — a BS.1770-grade true-peak detector.** **LANDED — no longer an ask**
  (class builder, 2026-09-07). The ask was written against a node that had one
  midpoint estimate; the node on the pin has three true-peak states, and
  `true_peak=2` selects a four-phase twelve-tap polyphase FIR
  (taps `audioif_dynamics.c:310-345`, read by `oversampled_peak` at `:349`, applied at `:576-589`) — BS.1770 Annex 2's
  shape, though not its coefficients. Measured on the worst-phase f_s/4 tone
  into a −6 dBFS ceiling: **+0.17 dB TP** at `true_peak=2`, against +1.07 dB at
  `true_peak=1` and +3.01 dB with it off, where L1 allows 0.5 dB (G.2).
  **L1 is reachable on the palette and no issue is owed.** *(the ask as
  written, and the refutation that failed at the time: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.
Both entries there are the seed's own wording and are superseded by the two
lines above.)*
