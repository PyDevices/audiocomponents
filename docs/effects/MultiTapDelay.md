# Effects Dossier — `MultiTapDelay` (Roland RE-201 multi-head modes; Binson Echorec)

**Class:** `lib/audioeffects/delay.py` — read once, for §7.
**Family / phase:** Time, roadmap Phase 5
**Standout:** the RE-201's multi-head modes, proposed in vision §4.2 —
**confirmed**, and joined by a **second reference, the Binson Echorec**, which
supplies a fourth tap, a *fixed* base rate, and the only head geometry this run
could reach with numbers (S3). The swap argument, and why it was declined, is
in §8.1.
**Grade:** **literature.** No schematic was read *for a trait*: the tap law
comes from Roland's own current manual for the machine that models this one
(S1), the head order from the RE-201 service notes (S2), and the geometry from
a repair-house teardown whose own arithmetic is internally consistent to about
1 % (S3, checked in Appendix A). The Phase 0 audit did read one page of S2's
RE-201 circuit diagram (page n5 at 216 ppi) for its mode-selector table
(Appendix C) and to confirm that the feedback question is traceable there; the
echo board itself is still unread, so the grade stays *literature*.
**Portability tier:** **audioif** for the full trait set — the §5 ask is
refused, and T5 is instead reached by composing `audioecho.FeedbackDelay` with
the ported `audiodelays.MultiTapDelay` (§4, measured in Appendix D), which is
an audioif-own node. **stock** remains available on the ported node alone, and
then T5 is disconfirmed-by-decision: no stock node has a filter inside a loop.
The class states which it shipped; the trait set differs by one row.
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

A multi-head echo records once and reads several times. The RE-201 puts an
erase head, a record head and then **three** playback heads in a row along one
tape — `ERASE → RECORD → PH-1 → PH-2 → PH-3`, labelled MODE 1 / 2 / 3 on the
drawing (S2 Fig. 6) — and the Echorec puts **four** playback heads round a
magnetic drum, 1.3 in apart on a 15 in circumference turning at 71 rpm, giving
taps at 74, 148, 222 and 296 ms (S3). Because the heads are **equally spaced**
— S3 measures one inter-head distance and multiplies it (Appendix A), and S2's
Fig. 6 is drawn evenly but dimensions nothing, so equal spacing is an inference
on both machines rather than a measured fact — the taps are integer multiples
of the first, and Roland's own manual for the current model states that flatly — "the delay times for playback heads 2, 3 and 4
are 2x, 3x and 4x the delay time of playback head 1 respectively" (S1). What a
player selects is not tap positions but a **subset** of that fixed grid. S1
tabulates twelve modes for the RE-202 (1–3 single heads, 4–7 the pairs and the
triple, 8–12 adding the fourth head the RE-201 did not have), and S3 gives the
Echorec "12 separate echo selections from one head alone to complex multi-tap
effects". **Audit correction, 2026-09-06 — the RE-201's own twelve positions
are not those twelve.** Its service notes carry their own `MODE SELECTOR
POSITION vs ACTIVATED PB HEAD` table on the OP-13/OP-14B/FL-7 circuit-diagram
page, read at 216 ppi in the audit and transcribed in Appendix C: only
positions **1–4 are echo alone** (head 1; head 2; head 3; heads 2+3), 5–11 add
the spring reverb and 12 is reverb only — so the RE-201 never offers the 1+2
pair the RE-202's mode 4 has, and seven of its twelve positions are about
reverb rather than about heads. The 1:2:3:4 tap law (S1, S3) is unaffected;
what changes is that "a 12-position mode selector on both machines, whose
combinations S1 tabulates" was wrong, and T3's grid is the **RE-202's**, taken
deliberately. One control moves the whole grid: on the RE-201 the
Repeat Rate changes the **motor**, 12–40 cm/s (S2), so every tap moves together
and the ratios are preserved; on the Echorec S3 measures a drum turning at
71 rpm and describes no speed control, so the base is taken here as fixed —
an inference from a measured constant, not a stated absence. Every tap is one pass of the same
recording past a different head — the service notes' own alignment procedure
asks for "all playback heads' output to be equal in levels" (S2 §2-2) — so
within a lap the taps differ in level and arrival, not in timbre. The feedback
control — Intensity on the RE-201; the Echorec's own control name is **not** in
any source this dossier reached, so the earlier "Swell" is dropped as
unsourced — returns audio to the record head, so darkening and saturation
accumulate **once per lap of the medium**, not once per tap. That last clause
is a **mechanism inference, not a sourced fact**: neither S2 nor S3 states
where the feedback is tapped or returned (§2, and the gap carried into §8.2),
and T5 rests on it.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Roland, *RE-202 Reference Manual* … (App. S1) | the full 12-mode × 4-head table … (App. S1) | **no rights statement appears on the page** … (App. S1) | https://static.roland.com/manuals/re-202_reference/eng/25633275.html | yes — re-fetched again in the trait-critic pass and parsed **from the raw HTML**, not from a summary: the four `Playback head` rows against the twelve `MODE` columns give 1/2/3 = heads 1/2/3; 4 = 1+2; 5 = 2+3; 6 = 1+3; 7 = 1+2+3; 8 = 1+4; 9 = 3+4; 10 = 1+3+4; 11 = 1+2+4; 12 = all four — confirming the audit's transcription. A summarising fetch of the same URL in the same pass returned a **different** table (mode 8 = head 4 alone, mode 11 duplicating mode 10); the raw parse is what T3 cites |
| **S2** Roland, *RE-201/101 Service Notes* … (App. S2) | head order `ERASE, RECORD, PH-1 (MODE 1) … (App. S2) | **license unverified … (App. S2) | https://archive.org/download/Roland_RE-101_RE-201_Service_Manual/Roland_RE-101__RE-201_Service_Manual_djvu.txt (page images: `…/page/n5.jpg` circuit diagram, `…/page/n19.jpg` Fig. 6, `…/page/n23.jpg` §2-7) | yes — text, metadata and pages n5/n19/n23 read in the audit |
| **S3** Effectrode, *Binson Echorec precision parts and memory system* | drum 4.7 in dia., ~15 in circumference … (App. S3) | "The entire effectrode.com website is … (App. S3) | https://www.effectrode.com/knowledge-base/binson-echorec-memory-system/ | yes — re-fetched in the audit; the drum, head, gap, spacing and tap figures are all verbatim, and the page names **no** control called "Swell" and discusses feedback nowhere |
| **S4** Zavalishin & Parker … (App. S4) | the *speed-type* medium: when the transport's speed … (App. S4) | **no rights statement printed** anywhere in … (App. S4) | https://dafx.de/paper-archive/2018/papers/DAFx2018_paper_9.pdf | yes, full text — re-downloaded and re-extracted in the audit |
| **S5** Soundgas, on maximum Space Echo delay | "If you read the RE-201 Manual or the Service Notes you won't find a number quoted anywhere"; "The number you will find in forums etc online most often is 600ms"; unit spread is large | page footer reads "**© 2025, Soundgas** \| VAT No.: GB460672980" — the earlier cell's "Content © Soundgas Tech Ltd" is not the page's wording; all rights reserved by default, read as a document | https://soundgas.com/blogs/resources/whats-the-maximum-delay-time-of-a-roland-space-echo | yes — re-fetched in the audit, quotes verbatim |

**Looked for, not found:** a dimensioned RE-201 head drawing. The audit read
S2's Fig. 6 as a **216 ppi page image** rather than the PDF's ~110 DPI copy,
and it carries no dimension at all — so this is a property of the drawing, not
of the scan, and the RE-201's own tap ratios still rest on S1's statement about
the model that copies it rather than on a measurement. **Any source for where
the feedback is tapped when a mode selects two or three heads** on either
machine is still missing — the single most load-bearing gap in this dossier,
carried into §8.2 — but the audit found the route: S2's own RE-201 circuit
diagram (page n5, `OP-13 / OP-14B / FL-7`) is legible at 216 ppi and shows
SW1's three mode-selector wafers wired to PH-1/PH-2/PH-3 beside the INTENSITY
and ECHO controls, so the question is traceable off a page this dossier already
cites rather than needing a new source. Also still missing: an Echorec
schematic or service manual, and any reference for the Echorec's control names
(which is why "Swell" has gone from §1). Copyleft sources are measured or read
as papers, never for code structure (vision §5).

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

No characters: the two machines differ only in tap count and in whether the
base moves, and both of those are macros (§6), not separate mechanisms.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1** | taps land on **integer multiples of one base**: `t_k = k·t_1`, each within **±0.5 %** of the exact multiple, at every Time setting **and in every mode except mode 12**. Mode 12 is excluded by S1's own words — "MODE 12 differs from the other modes, in that the positions of the four playback heads are optimized to create a highly dense sound" — so a build that puts mode 12 on the plain 1:2:3:4 grid is claiming something the source denies, and one that moves it must say where to (§8.4) | S1 ("2x, 3x and 4x" … (App. T1) | high | any shipped grid position in modes 1–11 whose measured arrival is more than 0.5 % off `k·t_1`; or mode 12 landing on exactly `k·t_1` while the class still claims to follow S1 | delay tracking: impulse in … (App. T1) |
| **T2** | **one control moves the whole grid**, ratios preserved: sweeping Time over its full range leaves every `t_k/t_1` within **±0.5 %** of `k`, and the measured span of `t_1` itself (longest reachable ÷ shortest reachable) is **at least 3.33 : 1**, the RE-201's own 12–40 cm/s | S2 ("12cm - 40cm/sec (approx)" … (App. T2) | high | any ratio outside ±0.5 % anywhere in the Time range; or a measured `t_1` span below 3.33 : 1 | T1's measurement repeated at Time … (App. T2) |
| **T3** | the pattern control is a **subset selector over that grid, not free tap placement**, and its 12 positions reproduce S1's table exactly: 1={1}, 2={2}, 3={3}, 4={1,2}, 5={2,3}, 6={1,3}, 7={1,2,3}, 8={1,4}, 9={3,4}, 10={1,3,4}, 11={1,2,4}, 12={1,2,3,4} | S1's own `Head Combinations for Each Mode` … (App. T3) | high | any of the 12 positions sounding a head set that row does not list, or omitting one it does | pattern walk: for each of the 12 … (App. T3) |
| **T4** | **within one lap every tap has the same timbre**, because they are one recording read at several places: after normalisation to its own peak, the magnitude spectrum of any two simultaneously enabled taps agree to **±0.5 dB from 100 Hz to 10 kHz**, and the agreement must hold **in every multi-head mode and with feedback engaged at 0.6**, not only on the first lap | the mechanism (S2, S3: one record head … (App. T4) | medium — S2 supports … (App. T4) | two taps in the same lap differing by more than 0.5 dB anywhere in that band after normalisation. The planted fault is a per-tap low-pass at 6 kHz on one head, which this measurement must turn red — without it the row is trivially true on any build that reads one line at several offsets | per-tap spectra: impulse at … (App. T4) |
| **T5** | **darkening accumulates once per lap, not once per tap**: with feedback engaged, `loss_dB(f)` of tap `k` at lap `n` minus tap `k` at lap 1 is the same for every `k` to **±0.5 dB** over 100 Hz–10 kHz, against a **±0.15 dB** repeatability floor from fitting lap 1 twice — so a pattern returns as the same rhythm, uniformly darker, never as a rhythm that also changes shape | the mechanism (feedback returns to the record … (App. T5) | medium — the … (App. T5) | per-lap loss differing between taps by more than 0.5 dB, which is what any build that filters each tap separately produces — and that build is this measurement's planted fault | per-pass darkening: impulse at … (App. T5) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose-first build: `audiodelays.MultiTapDelay`** (CircuitPython-ported →
tier **stock**). Measured on the CPython build, 48 kHz stereo, and every claim
below is a measurement, not a reading of the source:

- tap positions are exact fractions of `delay_ms` — taps at 1/3, 2/3, 1.0 of a …  *(argument in full: App. R)*
- one tap at level 1.0 comes out at the input's own peak — level-honest below …  *(argument in full: App. R)*
- **feedback recirculates at `delay_ms`, not at any tap** — one tap at 1/3 of a …  *(argument in full: App. R)*
- `delay_ms`, `taps`, `decay` and `mix` are all settable live, so Pattern and
  Time are real-time macros; 4, 8, 16, 32 and 64 taps were all accepted;
- the node renders **128 frames per pull** (512 bytes at the default …  *(argument in full: App. R)*
- **`mix` is 0–1 here, not 0–2.** The binding limits it to 0…1 and doubles it …  *(argument in full: App. R)*
- **the soft knee sits on the dry path too, so `mix = 0` is not a wire above …  *(argument in full: App. R)*

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**N1 — multiple read heads on `audioecho.FeedbackDelay`.** *Trait it
unblocks:* **T5**, and only T5. *What the palette does instead:*
`audiodelays.MultiTapDelay`, which reaches T1–T4 exactly (measured, §4) but
has no filter in or out of its loop, so per-lap darkening has no home; the
alternative of an `audiofilters.Filter` after the node applies one fixed loss
to every lap alike (and, unless the dry is fanned around it through an
`audioroute.Splitter` and summed back in an `audiomixer.Mixer` — both
byte-transparent, `AnalogDelay.md` Appendix E.4 — takes the dry path with it). *Shape:* `audioecho.FeedbackDelay` already carries the in-loop
low-pass, high-pass and soft-clip that T5 needs and reads its line per sample
with interpolation; the ask is an additional `heads` option — a small array of
(fraction, level) read positions summed into the wet output, the existing
single read staying as the recirculation tap. That is `k` extra interpolated
reads per frame per channel and no new state. Vision §6 already lists
"multiple heads in the feedback loop" as a candidate; this dossier is its need
statement. *Refutation, run in Phase 0 (2026-09-06):*

No other asks. T1–T4 are reachable today, measured.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Time | UNIPOLAR | 20–800 ms, log — the **base** tap `t_1` | RE-201 Repeat Rate (the motor) |
| 1 | Pattern | UNIPOLAR | quantised to 12 positions | the 12-position mode selector on both machines (S1, S3) |
| 2 | Feedback | UNIPOLAR | 0.00–0.95 | RE-201 Intensity (S2 §2-7); the Echorec's equivalent control is unnamed in any source reached |
| 3 | Mix | UNIPOLAR | 0.0–2.0 (`Echo`'s convention) | RE-201 Echo Volume |
| 4 | Heads | UNIPOLAR | quantised 2–8 | 3 on the RE-201, 4 on the Echorec; the grid's size |
| 5 | Tilt | BIPOLAR | −1…+1, level slope across the grid | none — the near-vs-far head balance, one knob |
| 6 | Tone | UNIPOLAR | 800–16000 Hz, log | none — the per-lap darkening of T5 |
| 7 | Spread | UNIPOLAR | 0.0–1.0 | none — taps across the stereo field, under D2; inert at 1 channel |
| 8 | Sync | TOGGLE | off / on | none — reads `transport()` |
| 9 | Division | UNIPOLAR | quantised: 1/16, 1/8T, 1/8, dotted 1/8, 1/4, dotted 1/4 | none — what `Sync` quantises `Time` to |

**Patches:** 0 *Three Heads, Even*; 1 *Two Heads, Two To One*; 2 *Four Heads,
Near Loudest*; 3 *All Heads, Dense*; 4 *One Head, Long Swell*; 5 *Triplet
Grid, Synced*.

## 7. Defects in the current class the rebuild must not repeat

1. **No surface at all.** `MACRO_LABELS = ()` (`delay.py:292`) and
   `PATCHES = {0: ("Default", ())}` (`:294`) — a host has nothing to turn on a
   class whose entire identity is a pattern selector.
2. **The pattern can never repeat.** `decay=0.0` is hardcoded into the node
   (`delay.py:301`), so the taps sound once and the feedback path is dead —
   the Intensity/Swell control, which is half of what these machines are, does
   not exist.
3. **The delay can never change.** The line is `max_delay_ms=int(time_ms)+100`
   (`delay.py:300`), sized to the constructor's argument, and the class has no
   `set_time` and no macro, so `time_ms` is fixed for the object's life.
4. **The default taps have no source.** `((0.25,0.8),(0.5,0.6),(0.75,0.4),
   (1.0,0.3))` (`delay.py:297`) is a linear ramp of positions and a linear fall
   of levels, matching no head geometry — T1 says the grid is integer multiples
   of a base and S1 says the levels are meant to be equal.
5. **No `clear()`**, unlike its three siblings on `_LoopDelay`
   (`delay.py:101-104`), so emptying the line means `reset()` — which also
   snaps the patch back to 0 (`_core.py:366-374`).
6. **`latency_samples`, `tail_samples` and `capabilities` are base-class
   defaults** (`_core.py:139-141`), so the tail of a feedback delay reports
   `None` and the transport is never read.

## 8. Open questions

1. **Should the Echorec replace the RE-201 outright?** The case for it is
   strong: four taps rather than three, a 12-position selector that is the
   whole instrument, a *fixed* base so the pattern is the only variable, and
   the only geometry this run could reach with numbers that check out
   (Appendix A). The case against, and the reason the swap was declined: the
   RE-201 is the standout Brad accepted, the RE-202 manual gives the tap law
   in Roland's own words for a machine still in production, and the Echorec
   contributes everything it has as a second reference without displacing
   anything. *Settles:* recorded here as declined; reopened only if Station A
   cannot source the RE-201's head ratios independently of S1.
2. **Where is the feedback tapped when a mode selects more than one head?**
   Not sourced on either machine (§2). If it is the longest selected head, the
   pattern period is the longest tap and §4's mapping is exact; if every
   selected head feeds back, the recirculation is itself a comb and T5's
   statement needs rewording before any code is written. **This must be
   settled before Station B**, not during it. *Settles:* Station A, from an
   RE-201 circuit diagram page or an Echorec service document.
3. **Where does mode 12 put its heads?** S1 states its positions are
   "optimized", not `1:2:3:4`, and publishes no figure for them, so T1
   excludes it. The class must either drop mode 12 to the plain grid and say in
   its docstring that it departs from S1 there, or choose a denser set and
   record the choice as a design decision with no source behind it. Silence is
   the one option that is not available, because T1 would then be measuring a
   grid the dossier never fixed. *Settles:* Station A.
4. **The Time knob steps.** The ported node's tap offsets are integers
   (`audioif_multitap.c:20-21`) and Python can only write them at block rate
   (2.67 ms, measured), so moving Time clicks. This dossier deliberately fixes
   **no glide trait** — the Echorec's base does not move at all and the
   RE-201's glide is `TapeDelay`'s varispeed trait, not this class's — but the
   class must document the click rather than let a user find it. *Settles:*
   the implementation session. N1 is refused (§5), so the free ride is gone;
   what remains is `TapeDelay`'s slew ask, which would cover the composed
   build's `FeedbackDelay` half but not the ported node's integer tap offsets.

---


## Appendix

### A. Checking S3's geometry against itself

S3 gives four independent numbers for one drum; computed here 2026-09-06, they
agree, which is why a repair-house page is treated as circuit-grade evidence
for the geometry:

| S3 states | derived from the others | agreement |
|---|---|---|
| circumference ≈ 15 in | π × 4.7 in dia. = **14.77 in** | 1.5 % |
| 18 ips | 15 in × 71 rpm ÷ 60 = **17.75 ips** | 1.4 % |
| taps 74 / 148 / 222 / 296 ms | 1.3 in ÷ 17.75 ips = **73.2 ms** per head, ×1…4 | 1.1 % |

The tap ratios are exactly 1 : 2 : 3 : 4, which is S1's "2x, 3x and 4x" law
arrived at from a different machine and a different source — the two-derivation
standard the vision asks for where the circuit is simple enough (§4.2).
**Audit precision note, 2026-09-06:** S3 measures **one** inter-head distance
("the measured distance between heads which is 1.3″ (34mm)") and then derives
taps 2–4 by multiplying it ("Second tap = 2 × 74 … Third tap = 3 × 74 … Fourth
tap = 4 × 74"), so the Echorec's 1:2:3:4 is one measurement plus an
equal-spacing assumption rather than four measured arrivals — a real second
derivation, but a thinner one than "four independent numbers" suggests. The
three consistency checks themselves were recomputed in the audit and all agree
(14.77 vs 15 in; 17.75 vs 18 ips; 73.2 vs 74 ms).

RE-201 base-tap span from S2's speed range alone: **3.33 : 1** (40 ÷ 12 cm/s).

### B. What `audiodelays.MultiTapDelay` actually does — measured, not read

CPython build (`audiocomponents/.venv/bin/python`), 48 kHz stereo, impulse of
12000 LSB, `mix = 2.0` (wet only), `max_delay_ms = 400`, `delay_ms = 300`.

| probe | result |
|---|---|
| taps at 1/3, 2/3, 1.0, decay 0 | arrivals at **100.0, 200.0, 300.0 ms**, each at 12000 |
| single tap at 0.9 / 0.95 / 0.98 / 0.99 / 0.995 / 0.999 | 270.0 / 285.0 / 294.0 / 297.0 / 298.5 / 299.69 ms — position × `delay_ms`, exactly |
| single tap at 1/3, decay 0.5 | echoes at **100, 400, 700, 1000, 1300 ms**, amplitudes 12000 → 6000 → 3000 → 1500 → 750 |
| three *coincident* taps at level 1.0, impulse 12000 | output **28050**, not 36000 — the soft knee at ±28000 (`audioif_synth_dsp.c:20-28`) |
| tap count | 4, 8, 16 and 32 all accepted |
| block size | 512 bytes = **128 frames** per pull |

**A control this measurement needed, and the cost of not having it.** The first
run of the tap-position probe rendered `int(0.5*SR/BLOCK)` blocks with `BLOCK`
assumed to be 256 frames. The node returns 128, so the render stopped at 248 ms
and every tap at or beyond 0.999 came back **silent** — which read exactly like
a node bug, and was written up as one before the block size was measured
instead of assumed. The lesson belongs in the Phase 0 kit spec: `render_effect`
must take its frame count from the buffer the node actually returns, and any
"the tap did not sound" result must be re-run past the longest tap before it is
believed. Absence reading as a finding is the same failure shape
workspace-craft.md records four times over.

### C. The RE-201's own mode table (read in the Phase 0 audit)

From S2's `OP-13 / OP-14B / FL-7` circuit-diagram page — archive page **n5** at
1785×2526, the resolution at which the block is legible; the PDF's ~110 DPI
copy of the same page is not. The block is titled `MODE SELECTOR POSITION vs
ACTIVATED PB HEAD`, grouped `REPEAT` (1–4), `REVERB + ECHO` (5–11),
`REVERB ONLY` (12):

| position | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PB head 1 | + | | | | + | | | + | | + | + | |
| PB head 2 | | + | | + | | + | | + | + | | + | |
| PB head 3 | | | + | + | | | + | + | + | | + | |
| Reverb | | | | | + | + | + | + | + | + | + | + |

Read off the drawing and transcribed, not reproduced. Two things follow. First,
the RE-201's echo-only grid is `{1}, {2}, {3}, {2,3}` — **no 1+2 and no 1+3
pair**, where the RE-202 has both — so the two machines' selectors are not the
same object, and §1 no longer says they are. Second, the RE-101's own diagram
(page n14, `OP-16 / OP-17B / FL-7`) carries the same block without the reverb
row, and there the six positions read `{1}, {2}, {3}, {1,3}, {2,3}, {1,2,3}`,
which is a different set again — worth knowing before anyone cites "the Space
Echo's modes" from a single page. Neither table says where the feedback is
tapped.

### D. The composed build, measured (Phase 0 palette verification, 2026-09-06)

CPython build (`audiocomponents/.venv/bin/python`), 48 kHz stereo, impulse
24000 LSB, `P` = 300 ms, three heads at 1/3, 2/3, 1.0, `feedback` 0.7,
`damping_hz` 3000. Spectra by 4096-point DFT with the arrival **centred** in a
Hann window — an earlier run put the arrival four samples from the window's
edge, where the window is ~0, and produced a reference 8 dB too small; the
relative columns survived it, the absolute ones did not.

**The grid.** `FeedbackDelay(delay_ms=300, feedback=0.7, mix=1.0)` →
`MultiTapDelay(delay_ms=300, decay=0, taps=(1/3, 2/3, 1.0), mix=wet)`:
arrivals at 100.00, 200.00, 300.00, 400.00, 500.00, 600.00, 700.04, 800.04,
900.04 ms, peaks 24000 / 24000 / 24000, 7794 ×3, 2424 ×3.

**T4 and T5, three builds.** Loss in dB re lap 1 tap 1 at 500 Hz / 1 / 2 / 4 /
8 kHz, then the two spreads the traits are stated against:

| build | lap 2 | lap 3 | lap 4 | T4 spread | T5 spread |
|---|---|---|---|---|---|
| composed (above) | −0.12 −0.45 −1.57 −4.34 −8.69 | −3.33 −4.00 −6.24 −11.77 −20.48 | −6.55 −7.55 −10.91 −19.21 −32.29 | **0.000 dB** | **0.000 dB** |
| control A: `Filter(3 kHz)` → `MultiTapDelay(decay 0.7)` | −3.10 ×5 | −6.20 ×5 | −9.30 ×5 | 0.000 dB | 0.000 dB |
| control B: composed, tap 2 darkened alone (planted) | as composed | as composed | as composed | **4.049 dB** | 0.000 dB |

Control A is the seed's own compose-first candidate: it decays but never
darkens, and it passes both traits as written. Control B is the planted fault
T4 must catch, and it does — while leaving T5's number untouched, so the
per-tap-filter build the seed said T5's measurement would catch is in fact
T4's to catch. Both controls are the point: a measurement that only ever
returns 0.000 has not been shown to be measuring anything.

**Node behaviour re-measured for §4** (same session): 128 frames per pull at
`buffer_size=512`; taps at 1/3, 2/3, 1.0 of a 300 ms line arriving at
100.0/200.0/300.0 ms and 0.9…0.999 at 270.0/285.0/294.0/297.0/298.5/299.69 ms;
one tap at 1/3 with `decay` 0.5 giving 100/400/700/1000/1300 ms at
12000/6000/3000/1500/750; three coincident taps at 12000 summing to **28050**;
4, 8, 16, 32 and 64 taps all accepted; `mix = 0` returning **28218** for a
30000-LSB impulse and **28436** for 32000 (`audioecho.FeedbackDelay` returns
both unchanged).

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

Rate note: every Tier 2 trait below holds at 22.05 kHz. The tap grid is
integer-quantised, so the worst case is one whole sample of tap error: 45.4 µs
at 22.05 kHz, which against the shortest shipped base tap (20 ms) is **0.23 %**
— inside T1's ±0.5 %, against 0.11 % at 44.1 kHz and 0.10 % at 48 kHz. Nothing is
relaxed, but T1's tolerance is what makes the lowest rate legal and must not be
tightened without re-checking this line.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Roland, *RE-202 Reference Manual*, "Head Combinations for Each Mode" | the full 12-mode × 4-head table; "the delay times for playback heads 2, 3 and 4 are **2x, 3x and 4x** the delay time of playback head 1"; "Modes 8–12 feature the sound of playback head 4, **which was not on the Roland Space Echo RE-201**"; and — added by the trait-critic pass, 2026-09-06 — "**MODE 12 differs from the other modes, in that the positions of the four playback heads are optimized to create a highly dense sound**" and "When you use tap input, this is set as the delay time (tap delay time) for playback head 1, **which is the base delay time for each mode**" | **no rights statement appears on the page** (checked in the audit) — manufacturer documentation, **license unverified and treated as all-rights-reserved**; read as a document, the table restated not reproduced as an image | https://static.roland.com/manuals/re-202_reference/eng/25633275.html | yes — re-fetched again in the trait-critic pass and parsed **from the raw HTML**, not from a summary: the four `Playback head` rows against the twelve `MODE` columns give 1/2/3 = heads 1/2/3; 4 = 1+2; 5 = 2+3; 6 = 1+3; 7 = 1+2+3; 8 = 1+4; 9 = 3+4; 10 = 1+3+4; 11 = 1+2+4; 12 = all four — confirming the audit's transcription. A summarising fetch of the same URL in the same pass returned a **different** table (mode 8 = head 4 alone, mode 11 duplicating mode 10); the raw parse is what T3 cites |
| **S2** Roland, *RE-201/101 Service Notes*, 2nd ed. 1978 (OCR text **and**, added by the audit, the archive's own 1785×2526 page images) | head order `ERASE, RECORD, PH-1 (MODE 1), PH-2 (MODE 2), PH-3 (MODE 3)` — **three** playback heads (Fig. 6, read as an image at 216 ppi in the audit: it carries **no dimension of any kind**, and the heads are merely *drawn* evenly spaced); tape speed 12–40 cm/s; §2-2 "The ideal is for all playback heads' output to be equal in levels"; S/N 60 dB "A" weighted; §2-7 "Adjust VR12 so that multiple repetition of noises occurs with Intensity Control as shown" — the notes say nothing about **self-oscillation**, and that earlier wording is withdrawn; and the RE-201's own mode-selector table (Appendix C) | **license unverified — treated as copyleft**: the archive.org metadata API carries **no `licenseurl` and no `rights` field** (re-checked in the audit) | https://archive.org/download/Roland_RE-101_RE-201_Service_Manual/Roland_RE-101__RE-201_Service_Manual_djvu.txt (page images: `…/page/n5.jpg` circuit diagram, `…/page/n19.jpg` Fig. 6, `…/page/n23.jpg` §2-7) | yes — text, metadata and pages n5/n19/n23 read in the audit |
| **S3** Effectrode, *Binson Echorec precision parts and memory system* | drum 4.7 in dia., ~15 in circumference, **71 rpm ≈ 18 ips**; one record head (400–500 Ω, 10 µm gap) and **four** playback heads (600–700 Ω, 5 µm gap); **1.3 in (34 mm)** between successive heads; taps at 74 / 148 / 222 / 296 ms; "12 separate echo selections from one head alone to complex multi-tap effects"; and, on wow and flutter, "there's no reason why a properly serviced Echorec should not approach this figure" — the figure being a Garrard 401 turntable's **0.05 %**, not a measurement of an Echorec, where this cell previously quoted the Echorec itself as "should approach 0.05 %" | "The entire effectrode.com website is copyright © EFFECTRODE THERMIONIC. All Rights Reserved." (verbatim) — read as a document | https://www.effectrode.com/knowledge-base/binson-echorec-memory-system/ | yes — re-fetched in the audit; the drum, head, gap, spacing and tap figures are all verbatim, and the page names **no** control called "Swell" and discusses feedback nowhere |
| **S4** Zavalishin & Parker, *Efficient emulation of tape-like delay modulation behavior*, DAFx-18 | the *speed-type* medium: when the transport's speed changes, every tap's delay changes together and the pitch follows the speed ratio, not the rate of knob movement (§1) | **no rights statement printed** anywhere in the PDF (searched in the audit) — **license unverified, treated as copyleft**; read as a paper | https://dafx.de/paper-archive/2018/papers/DAFx2018_paper_9.pdf | yes, full text — re-downloaded and re-extracted in the audit |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1** | taps land on **integer multiples of one base**: `t_k = k·t_1`, each within **±0.5 %** of the exact multiple, at every Time setting **and in every mode except mode 12**. Mode 12 is excluded by S1's own words — "MODE 12 differs from the other modes, in that the positions of the four playback heads are optimized to create a highly dense sound" — so a build that puts mode 12 on the plain 1:2:3:4 grid is claiming something the source denies, and one that moves it must say where to (§8.4) | S1 ("2x, 3x and 4x", and the mode-12 sentence, both re-read from the page's raw HTML this run); S3 (74/148/222/296 ms from a 1.3 in spacing, Appendix A) | high | any shipped grid position in modes 1–11 whose measured arrival is more than 0.5 % off `k·t_1`; or mode 12 landing on exactly `k·t_1` while the class still claims to follow S1 | delay tracking: impulse in, feedback 0; for each mode report every tap's arrival to the sample and `t_k/(k·t_1)`; mode 12 reported separately against whatever §8.4 settles |
| **T2** | **one control moves the whole grid**, ratios preserved: sweeping Time over its full range leaves every `t_k/t_1` within **±0.5 %** of `k`, and the measured span of `t_1` itself (longest reachable ÷ shortest reachable) is **at least 3.33 : 1**, the RE-201's own 12–40 cm/s | S2 ("12cm - 40cm/sec (approx)", re-read this run); S4 §1 (a speed-type medium moves every tap together, read in full this run) | high | any ratio outside ±0.5 % anywhere in the Time range; or a measured `t_1` span below 3.33 : 1 | T1's measurement repeated at Time = 60, 150, 300, 600 ms; report the ratio matrix at each, and the arrival at the two ends of the Time macro |
| **T3** | the pattern control is a **subset selector over that grid, not free tap placement**, and its 12 positions reproduce S1's table exactly: 1={1}, 2={2}, 3={3}, 4={1,2}, 5={2,3}, 6={1,3}, 7={1,2,3}, 8={1,4}, 9={3,4}, 10={1,3,4}, 11={1,2,4}, 12={1,2,3,4} | S1's own `Head Combinations for Each Mode` table, re-read **cell by cell from the page's raw HTML** in this pass (a summarising fetch of the same page returned a different and self-contradictory table — mode 11 duplicating mode 10 — which is why the raw read is the citation). **Not** the RE-201's own twelve, which are four echo modes plus seven reverb combinations and a reverb-only position (S2, Appendix C): the grid here is the RE-202's by choice | high | any of the 12 positions sounding a head set that row does not list, or omitting one it does | pattern walk: for each of the 12 positions, an impulse at feedback 0, and the set of tap arrivals compared against the head sets above converted to multiples of `t_1` |
| **T4** | **within one lap every tap has the same timbre**, because they are one recording read at several places: after normalisation to its own peak, the magnitude spectrum of any two simultaneously enabled taps agree to **±0.5 dB from 100 Hz to 10 kHz**, and the agreement must hold **in every multi-head mode and with feedback engaged at 0.6**, not only on the first lap | the mechanism (S2, S3: one record head, several playback heads); S2 §2-2 "The ideal is for all playback heads' output to be equal in levels", re-read this run | medium — S2 supports equal **levels** as the alignment target and in the same paragraph warns that the level adjustment can "cause ill affect on the high frequency response by tilting or azimuth error", so ±0.5 dB of *spectral* agreement is this dossier's modelling bar, not a machine measurement | two taps in the same lap differing by more than 0.5 dB anywhere in that band after normalisation. The planted fault is a per-tap low-pass at 6 kHz on one head, which this measurement must turn red — without it the row is trivially true on any build that reads one line at several offsets | per-tap spectra: impulse at feedback 0 and again at 0.6, all heads on, window each tap, normalise to its peak, report worst pairwise dB difference per lap |
| **T5** | **darkening accumulates once per lap, not once per tap**: with feedback engaged, `loss_dB(f)` of tap `k` at lap `n` minus tap `k` at lap 1 is the same for every `k` to **±0.5 dB** over 100 Hz–10 kHz, against a **±0.15 dB** repeatability floor from fitting lap 1 twice — so a pattern returns as the same rhythm, uniformly darker, never as a rhythm that also changes shape | the mechanism (feedback returns to the record head — **an inference: neither S2 nor S3 states the tap point**, see §2 and §8.2); the same in-loop reasoning `upstream-diff.md` gives for `audioecho` | medium — the mechanism is clear but no source states the RE-201's or the Echorec's per-lap response, so ±0.5 dB is this dossier's threshold | per-lap loss differing between taps by more than 0.5 dB, which is what any build that filters each tap separately produces — and that build is this measurement's planted fault | per-pass darkening: impulse at feedback 0.6, isolate laps 1–4, fit `loss_dB(f)` per tap per lap, report the spread across taps at each lap and the two-fit repeatability |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §3)*

Budget as a fraction of one stereo block's deadline: **P4 0.04, S3 0.10** —
the lowest of the three delay classes, because with no interpolation and no
in-loop filtering the ported node is integer arithmetic and one add per tap
per frame. Proposals against Phase 1's cost table, not measurements. Lean
patch **no**: eight taps at 48 kHz is a handful of adds, and the fallback
build (§5) is already the cheap one.

*(from §3)*

**Latency is zero.** The dry path is the input frame; nothing looks ahead.
`latency_samples` is **0** at every rate and macro setting, and the class ships
**no option that adds latency**. `tail_samples` is recomputed on every Time or
Feedback move from the pattern period and the feedback: `P · ln(0.001)/ln(f)`
frames plus the longest enabled tap, clamped as `f → 0.95`.

*(from §4)*

- tap positions are exact fractions of `delay_ms` — taps at 1/3, 2/3, 1.0 of a
  300 ms line arrive at **100.0, 200.0, 300.0 ms**, and 0.9/0.95/0.98/0.99/
  0.995/0.999 arrive at 270.0/285.0/294.0/297.0/298.5/299.69 ms. **T1 and T3
  are reachable exactly**, with the grid expressed as `k/K`;

*(from §4)*

- one tap at level 1.0 comes out at the input's own peak — level-honest below
  the node's soft knee. Three coincident taps at 12000 LSB each sum to
  **28050**, not 36000: `audioif_mix_down_sample` (`audioif_synth_dsp.c:20-28`)
  is transparent below ±28000 and soft-limits above, so the surface must keep
  the summed grid under that knee rather than discover it;

*(from §4)*

- **feedback recirculates at `delay_ms`, not at any tap** — one tap at 1/3 of a
  300 ms line at decay 0.5 gives echoes at **100, 400, 700, 1000, 1300 ms**,
  amplitudes halving. That is exactly T5's lap structure, provided `delay_ms`
  is set to the *pattern period* and the grid is written as fractions of it;

*(from §4)*

- the node renders **128 frames per pull** (512 bytes at the default
  `buffer_size=512`, stereo), half `FeedbackDelay`'s fixed 256 — but this one
  is a **constructor argument**, not a node constant, so the class chooses it
  and the kit must read it rather than assume it;

*(from §4)*

- **`mix` is 0–1 here, not 0–2.** The binding limits it to 0…1 and doubles it
  into the C convention (`src/audiodelays/MultiTapDelay.c:349`; the CPython
  shim does the same), where `audioecho.FeedbackDelay` takes the raw 0…2
  (`audioif_feedback_delay.c:92-99`). §6's `Mix` macro is halved on the way to
  this node or it silently saturates at wet-only halfway up its travel;

*(from §4)*

- **the soft knee sits on the dry path too, so `mix = 0` is not a wire above
  ±28000.** An impulse of 30000 LSB through the node at `mix = 0` comes back at
  **28218**, and 32000 at **28436** (`audioif_multitap.c:33-37`), where
  `audioecho.FeedbackDelay` at `mix = 0` returns 30000 and 32000 unchanged.
  Tier 1's wire test has to be met by bypassing the node, not by trusting it.

*(from §4)*

Python holds the grid: on a Pattern or Heads move it rewrites `taps` as
`(k/K, level_k)` for the selected `k`, with `level_k` from the Tilt macro; on a
Time move it writes `delay_ms = K · t_1`. Nothing is tabulated on the target.
**Mono:** not stereo by definition — but **§6's `Spread` has no node behind it
on this build**: the ported node applies one `tap_offsets`/`tap_levels` pair to
both channels, each channel reading its own plane of the same line
(`audioif_multitap.c:15-16`, `:19-23`), so taps cannot be placed per channel.
Spread costs an `audioroute.Splitter` and two nodes into an `audiomixer.Mixer`,
or it comes from `cross_feed` on the composed build below; either way it is
inert at `channel_count` 1 because there is no other channel, not because the
node ignores it. **`capabilities` (D10): `("tempo_sync",)`** — Time quantises to
a beat division when `Sync` is on, and a tap grid is the one place a host user
will expect that.

*(from §4)*

**T5 needs a second node, not a new one.** `audioif_multitap.c` is 43 lines
with no filter of any kind — the loop is `delayed·decay + sample`
(`audioif_multitap.c:30`) — so the per-lap darkening cannot live in *this*
node, and it is CircuitPython-ported and never modified (vision §2.2). But it
can live in the one next to it. **`audioecho.FeedbackDelay` (delay = the
pattern period `P`, `feedback` = the lap decay, `damping_hz` in the loop,
`mix = 1.0`) feeding `audiodelays.MultiTapDelay` (`decay = 0`, taps = the
grid)** puts the laps in a real filtered loop and the heads on each lap.
Measured (Appendix D): the grid is 100/200/300, 400/500/600, 700/800/900 ms;
tap-to-tap spectra agree to **0.000 dB** inside every lap (T4); and the per-lap
increment is identical across taps to **0.000 dB** while accumulating −8.7,
−20.5, −32.3 dB at 8 kHz over laps 2–4 (T5). The cost is the **audioif** tier
instead of stock, and two nodes' per-sample work. Hence §5's ask is refused.

*(from §5)*

**REFUTED BY PALETTE.** The per-lap darkening does not need a new read head; it
needs the loop that already exists next door. `audioecho.FeedbackDelay` at
`delay_ms = P` (the pattern period), `feedback` = the lap decay, `damping_hz`
in the loop and `mix = 1.0` — dry plus every lap — feeding
`audiodelays.MultiTapDelay` at `decay = 0` with the grid as `taps` puts each
lap through the filter one more time and then spreads that lap across the
heads. Measured on the CPython build at 48 kHz (Appendix D): arrivals at
100/200/300, 400/500/600, 700/800/900 ms; **T4** tap-to-tap spectral agreement
**0.000 dB** in every lap; **T5** per-lap increment identical across taps to
**0.000 dB**, accumulating −8.7, −20.5, −32.3 dB at 8 kHz over laps 2–4. No
node change, and `heads` on `FeedbackDelay` is not asked for.

*(from §5)*

*Two things the refutation costs, recorded rather than buried.* The class is
**audioif** tier, not stock — the header's "stock if built on
`audiodelays.MultiTapDelay`" now means "stock **and** T5 disconfirmed", because
no stock node has a filter in a loop. And it pays two nodes per sample instead
of one, which is Tier 3's problem, not the palette's.

*(from §5)*

*And the seed's own prediction was wrong, in a way that matters more than the
ask.* The front-filter build was measured too: it does **not** fail T4 — its
tap-to-tap spread is also 0.000 dB — and it **passes T5 as T5 is written**,
because its per-lap increment is a flat −3.10 dB at every frequency and every
tap, so the spread across taps is zero. A build in which nothing darkens at all
scores exactly what a correct one scores. **T5 needs a second clause** — that
the increment is frequency-shaped and accumulates, e.g. lap 4 at 8 kHz at least
15 dB below lap 1 and within 2 dB of 3× lap 2's increment — or the trait is
passed by absence, which is the failure shape `workspace-craft.md` records four
times over. *Settles:* Station A, before any code.
