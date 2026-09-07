# Effects Dossier — `TapeDelay` (Maestro Echoplex EP-3; Roland RE-201 Space Echo)

**Class:** `lib/audioeffects/delay.py` — read once, for §7.
**Family / phase:** Time, roadmap Phase 5
**Standout:** both machines, per vision §4.2 — **confirmed, and split into two
characters.** They differ in the one thing this class's Time knob does: the
EP-3 moves a head (*length-type*), the RE-201 moves the motor (*speed-type*),
and the pitch of a moving delay follows from that and nothing else (S4 §1).
**Grade:** **literature** — S1's transport numbers are a real service
document; the traits come from two published models with equations (S3, S4)
plus a derivation run here (Appendix A). *Audit, 2026-09-06:* "the circuit
pages are 110 DPI and were not read" was an artifact of reading the **PDF**,
whose page images are 945x1229 (~110 DPI on A4). The archive item's own page
images are **1785x2526** (`ppi 216` in its metadata) and fetch one at a time
from `https://archive.org/download/Roland_RE-101_RE-201_Service_Manual/page/n<N>.jpg`;
page **n5** is the RE-201's own `OP-13 / OP-14B / FL-7` circuit diagram
(page n14 is the RE-101's `OP-16 / OP-17B / FL-7`), and n5 was read at that
resolution in this audit. Route to *circuit*: read n5 and SPICE the echo
board — the grade stays *literature* until that is done.
**Portability tier:** needs audioif-own nodes (`audioecho.FeedbackDelay`)
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

A tape echo is a loop of tape dragged past four things in order. The RE-201's
order is `ERASE → RECORD → PH-1 → PH-2 → PH-3` (S1 Fig. 6); the Echoplex has
fixed playback and erase heads and a **movable record head**, at roughly 8 ips
(S2). Delay is head separation over tape speed, so the two machines put the
knob in different places: the RE-201's Repeat Rate moves the **motor**,
12–40 cm/s — a 3.33:1 span on fixed heads (S1, "Tape Speed 12cm – 40cm/sec
(approx)") — while the Echoplex slides a head along a fixed-speed transport.
The nonlinearity is the tape itself, a hysteresis loop between record current
and magnetisation (S3 eq. 6/18), with a high-frequency **bias** current an
order above the signal keeping it off the dead zone (S3 §3.3); the RE-201 runs
50–60 Vrms of bias across the erase head and a trap coil holding leakage below
2.5 Vrms (S1 §2-1). The filtering is not a tone control but the playback
head's geometry — spacing loss `e^{-kd}`, thickness loss `(1-e^{-kδ})/(kδ)`,
gap loss `sinc(kg/2)`, all with `k = 2πf/v` (S3 eq. 13/14) — so the top comes
off **once per pass round the loop**, by an amount that moves with the tape
speed. Above that sit a real tone control (RE-201 Bass **±10 dB** at 100 Hz,
Treble **±10 dB** at 5 kHz, S1 — the page image prints `±`; the OCR text drops
the sign, and this dossier said `+10 dB` until the audit read the page) and a
feedback control (Intensity, whose factory trim VR12 is set "so that multiple
repetition of noises occurs with Intensity Control as shown", S1 §2-7 — the
service notes say nothing about self-oscillation, and the earlier claim that
the top of its travel runs away is **withdrawn as unsourced**). Transport
speed is not constant: a real machine fluctuates **quasiperiodically**, with
separate capstan and pinch-wheel components plus a slow drift (S2), not one
sine.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Roland, *RE-201/101 Service Notes* … (App. S1) | tape speed 12–40 cm/s ("Other Reference Data") … (App. S1) | **license unverified … (App. S1) | https://archive.org/download/Roland_RE-101_RE-201_Service_Manual/Roland_RE-101__RE-201_Service_Manual_djvu.txt (metadata: https://archive.org/metadata/Roland_RE-101_RE-201_Service_Manual; page images: `…/page/n5.jpg`, `…/page/n23.jpg`) | yes — text, metadata and pages n5/n14/n23 re-read in the audit |
| **S2** Arnardottir, Abel & Smith III … (App. S2) | "fixed playback and erase heads … (App. S2) | "Audio Engineering Society … (App. S2) | https://aes.org/publications/elibrary-page/?id=14800 | abstract only (re-fetched in the audit; the three quotes above are verbatim from it) |
| **S3** Chowdhury, *Real-time Physical Modelling for Analog Tape … (App. S3) | the three loss terms and `k = 2πf/v` (eq. 13/14) … (App. S3) | **no rights statement printed** anywhere in … (App. S3) | https://ccrma.stanford.edu/~jatin/420/tape/TapeModel_DAFx.pdf | yes, full text — re-downloaded and re-extracted in the audit, every figure above checked against the paper |
| **S4** Zavalishin & Parker … (App. S4) | §1: "we call these length-type delays … we call these … (App. S4) | **no rights statement printed** anywhere in … (App. S4) | https://dafx.de/paper-archive/2018/papers/DAFx2018_paper_9.pdf | yes, full text — re-downloaded and re-extracted in the audit; the quotes above are verbatim |
| **S5** Holters & Parker, *A Combined Model for a Bucket Brigade … (App. S5) | T1's contrast: "This is in contrast to a simple … (App. S5) | **no rights statement printed** anywhere in … (App. S5) | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2018/09/Holters-Parker-2018-A-Combined-Model-for-a-Bucket-Brigade-Device-and-its-Input-and-Output-Filters.pdf | yes, full text — re-downloaded and re-extracted in the audit; the quote is verbatim |
| **S6** Soundgas, on maximum Space Echo delay | "If you read the RE-201 Manual or the Service Notes you won't find a number quoted anywhere"; "The number you will find in forums etc online most often is 600ms"; unit spread is large and ageing-dependent | page footer reads "**© 2025, Soundgas** \| VAT No.: GB460672980" — the earlier cell said "Content © Soundgas Tech Ltd", which is **not** the page's wording (Soundgas Tech Ltd appears only in the address block); all rights reserved by default, read as a document | https://soundgas.com/blogs/resources/whats-the-maximum-delay-time-of-a-roland-space-echo | yes — re-fetched in the audit, quotes verbatim |

**Looked for, not found:** a dimensioned head-spacing drawing — S1 Fig. 6 is
undimensioned, and the audit re-read it at the archive's full 216 ppi (page
n19) rather than the PDF's ~110 DPI: it names `ERASE HEAD / RECORD HEAD /
PH-1 MODE 1 / PH-2 MODE 2 / PH-3 MODE 3` along the tape and carries no
dimension at all, so the gap is a property of the drawing, not of the scan
(the heads are drawn at what looks like equal spacing, which is a picture and
not a measurement); a Roland maximum-delay figure (S6: none exists); an EP-3
schematic (not searched to exhaustion — Station A's); S2's full text
(paywalled, $33). **Reachable and not yet read:** S1's own RE-201 circuit
diagram, page n5 at 1785×2526 — the audit read its mode-selector table (it is
transcribed in `MultiTapDelay.md` Appendix C) but not its echo board.
Copyleft sources are measured or read as papers, never for code structure
(vision §5); nothing here was read for code.

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Characters `"varispeed"` (RE-201) and `"sliding-head"` (EP-3) take one T1 row
each and share T2–T5. **Every shared row is measured and reported separately
for each character**; a character that fails cannot hide behind the other.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1a** | *varispeed:* the Time control commands the **speed**, so `T(t)` obeys the tape equation (S4 eq. 3/6) and can never step. A `Time` step from `T_old` to `T_new` glides at exactly `dT/dt = 1 − T_old/T_new` and the wet path holds a **constant** pitch ratio `T_old/T_new` for exactly `T_new` seconds, then returns to unity. For 200 → 100.4 ms: **+1193 cents held for 100.4 ms**, then unity | S4 §1, eq. (3)/(6)/(8); ratio and duration derived and simulated here (Appendix D) | high | an offset more than 10 cents from +1193; a hold shorter or longer than 100.4 ms by more than 5 %; any residual beyond ±2 cents once one `T_new` has elapsed; or a sample-to-sample step above the probe tone's own maximum slope at the step | instantaneous frequency of a 1 kHz wet tone (wet only, feedback 0) through the 200 → 100.4 ms step at a block boundary, by analytic-signal phase slope; report offset in cents, its duration, and worst `\|x[n]−x[n−1]\|` vs `2πf/f_s·A` |
| **T1b** | *sliding-head:* the Time control commands the **length**, so `T` follows the knob directly: while the knob moves the wet pitch is exactly `1 − dT/dt` and returns to unity the moment it stops — a 200 → 400 ms ramp over 500 ms gives **−884 cents for the 500 ms of the ramp**, and a *step* gives **no pitch offset at all**, a discontinuity instead. Under feedback the excursion is **baked in**: after a Time gesture that returns to its starting value at least one recirculating repeat is left more than 100 cents off and stays there, where varispeed returns every repeat to the source pitch | S4 §1 verbatim (length-type gives "erratic … (App. T1b) | high | a ramp offset more than 10 cents from `1 − dT/dt`; a pitch offset surviving more than 20 ms past the end of the ramp; the two characters leaving the same permanent transposition after the out-and-back gesture; sliding-head returning every repeat to within 5 cents; or varispeed leaving any repeat more than 5 cents off | the ramp, on both characters … (App. T1b) |
| **T2** | one pass applies the **three-term playback loss of S3 eq. (13)** — spacing `e^{−kd}`, thickness `(1−e^{−kδ})/(kδ)`, gap `sinc(kg/2)`, all at `k = 2πf/v` — evaluated at the class's declared `d`, `g`, `δ` and the character's speed, to **±2 dB from 1 to 10 kHz**; and `n` passes give `n×` the one-pass loss in dB to **±2 dB at 10 kHz**. At the shipped `d = 5 µm, g = 5 µm, δ = 35 µm` that is **−9.1 dB at 1 kHz and −50.6 dB at 10 kHz at 12 cm/s**, **−3.0 and −21.9 dB at 40 cm/s** (Appendix A). It is **not a one-pole**: the best single one-pole fit to even the spacing term alone is **2.9 dB out at 12 cm/s** over 1–10 kHz | S3 eq. 13/14, read in full this run … (App. T2) | high on the law … (App. T2) | a one-pass curve more than 2 dB from eq. (13) anywhere in 1–10 kHz; `n`-pass differing from `n×` one-pass by more than 2 dB at 10 kHz; or a curve a single one-pole fits better than 2 dB at 12 cm/s, which would mean the loss law did not ship | per-pass darkening: impulse at … (App. T2) |
| **T3** | that loss **moves with `Time` on varispeed and not on sliding-head**, because `k = 2πf/v` and only `v` changes: across the RE-201's own **12–40 cm/s** (S1) the 10 kHz per-pass loss changes by **28.8 dB** on the full eq. (13) at the shipped `d`/`g`/`δ` (**15.9 dB** on the spacing term alone), and by **less than 1 dB** on sliding-head, whose speed is fixed. The bar: **≥ 15 dB** varispeed, **≤ 1 dB** sliding-head | S1 (12–40 cm/s, re-read this run) + S3 eq. … (App. T3) | medium — the span is … (App. T3) | varispeed moving the 10 kHz per-pass loss by less than 15 dB across the Time range; or sliding-head moving it by more than 1 dB | T2's measurement at Time = 60 … (App. T3) |
| **T4** | the fluctuation is **quasiperiodic: at least two components plus a slow drift** (S2) — over 60 s the recovered delay's modulation spectrum shows **two lines each ≥ 20 dB above the median floor between them**, whose ratio is **not within 1 % of `p/q` for any integers `p, q ≤ 8`**, plus **non-line energy below 0.1 Hz at least 10 dB above that floor** | S2 abstract, re-fetched this run (full text … (App. T4) | medium — the abstract … (App. T4) | one line; two lines whose ratio is within 1 % of a small-integer ratio (`q ≤ 8`); either line under 20 dB above the floor; or sub-0.1 Hz energy under 10 dB above it | LFO extraction: instantaneous … (App. T4) |
| **T5** | record level into tape is **compressive with memory**: at `Record Level` 0.5 the H3 of a 1 kHz tone through one pass differs by **≥ 1 dB** between a rising and a falling approach to that same knob value, against a **±0.2 dB** repeatability floor established by running one approach twice; a memoryless soft-clip gives 0 dB by construction | S3 §1.2, §2.2 (Jiles-Atherton, eq. 6/18) … (App. T5) | medium — a memoryless … (App. T5) | the two approaches agreeing within the 0.2 dB repeatability floor | harmonic spectrum at level: 1 kHz … (App. T5) |

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's deadline: **P4 0.06, S3 0.15** —
proposals against Phase 1's cost table, not measurements. Lean patch **yes**:
`" - lean"` drops the second modulation term (T4 → one line plus drift) and
tape memory (T5 → the node's existing cubic `loop_drive`), keeping T1–T3.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node: `audioecho.FeedbackDelay`** (audioif's own → tier **audioif**).
Everything the class is named after happens *inside* the loop, and this is the
only palette node with an inside. The line is read **per sample with linear
interpolation** (`audioif_feedback_delay.c:226-228`) under a **per-sample**
magic-circle sine (`:209-210`, `:212-213`), so modulation glides instead of
stepping — what T4 needs. What `audiodelays.Echo` cannot give is the *loop*:
its feedback path is `buffer[j]*decay + sample` and nothing else
(`audioif_echo.c:23-26`, `:31`), so T2, T3 and T5 have nowhere to live. It
*can* reach T1a, on a mechanism this seed had not credited — measured in §5 N1
and Appendix E. The in-loop one-pole low-pass `damping_hz` (`:231-235`,
coefficient `1−exp(−2πf_c/f_s)` at `:31-38`) compounds once per pass by
construction, which is T2's mechanism; `cut_hz` (`:236-240`) trims the loop's
bottom; the cubic soft-clip `loop_drive` (`:180-184`, applied `:241-243`) is
odd-symmetric and memoryless — enough for the lean patch's T5, not the
faithful one; `cross_feed`/`input_pan` (`:249`, `:126-141`) give Spread.
Python computes the line length at construction and, per macro move, the loss
corner from `Spacing`, `Time` and the character's speed law (T2/T3 are a Python
control law: `damping_hz` follows `d/v`, and on varispeed `v` follows `Time`),
the `tail_samples` recomputation, and the sync division from `transport()`.
Nothing is tabulated on the target — the loss law is a closed form in three
floats. **Mono:** not stereo by definition; at `channel_count` 1 the node sets
`feed_own[0]=1`, `feed_other[0]=0` (`:62-71`) — but **`Spread` is not inert
there, it is destructive, and the class holds it off in Python rather than
documenting it as harmless.** With one channel `other` is forced to zero
(`:248`) while `sent` still scales by `direct = 1 − cross_feed` (`:203`,
`:249`), and `input_pan` still rewrites `feed_own[0]` (`:135-141`, read at
`:253-254`): measured mono at 48 kHz, feedback 0.7, `cross_feed` 1.0 leaves the
dry alone and **no repeats at all**, and `input_pan` +1.0 **silences the wet
path** (Appendix E). Every other trait holds.
**`capabilities` (D10): `("tempo_sync",)`** — the class reads `transport()` and
quantises `Time` to a beat division when `Sync` is on. **What does not fit on
one node:** T1a (§5 N1) and T4's drift term (§5 N2′); T4's two components fit
on a **second** `FeedbackDelay` in series, measured in Appendix E.5.
Sliding-head is reachable today but for the step discontinuity, which N1 also
fixes.

## 5. Node asks

**N1 — delay-time slew, with a speed-type mode, on `audioecho.FeedbackDelay`.**
*Unblocks* **T1a**, and removes the discontinuity T1b forbids. *The palette
instead:* `config->delay_frames` is written straight by `OPT_DELAY_MS`
(`audioif_feedback_delay.c:77-84`) and read unsmoothed per frame (`:212`), so a
`Time` change lands in one sample, and Python can only step it once per block
(256 frames, 5.33 ms at 48 kHz, measured). *The measurement:* stepping
`delay_ms` 200 → **100.4 ms** gives a worst sample-to-sample step of **15960
LSB at exactly that frame**, against **1566** anywhere else and 1570.8 for the
tone's analytic maximum slope — **10.2×**, 0.49 of full scale (Appendix B).
*The palette does reach the pitch law, on a node this seed had not credited:*
**`audiodelays.Echo(freq_shift=True)` is a speed-type medium by construction**
— the line stays at `max_delay_ms` and Time moves the read/write *rate*
(`Echo.c:116-120`, applied at `audioif_echo.c:19-28`). Stepped 200 → 100.4 ms
it holds **+1189.8 cents for 100.59 ms** and returns to unity, **click-free**,
against T1a's +1193.1 cents for 100.4 ms. What stops it carrying this class is
not the pitch but the loop: no filter, drive or cross-feed
(`audioif_echo.c:23-26`, `:31`), so T2/T3/T5 have nowhere to sit and it is
ported and never gains one; a nearest-neighbour read (`audioif_echo.c:20`) that
costs **−30.8 dB** of jitter off the exact rates where `FeedbackDelay` is at
−67.8 dB; and a delay resolution of ≈`T²/(256·max_delay_ms)`, 0.78 ms at the
top of a 200 ms line. All of it in Appendix E. **The ask stands, and its shape
is now demonstrated rather than proposed.**
*Shape:* two additive options, `delay_slew_ms` (a one-pole on the read offset,
per sample in the existing loop) and `slew_mode ∈ {length, speed}`, `speed`
integrating the tape equation in its **difference** form `V(t)−V(t−T(t))=L`
(S4 eq. 6) — S4 §2.1 shows the differential form drifts without bound, and
`Echo`'s rate-driven read is the same equation already running in the tree.
Cost: one add and one compare per frame per channel. *Refutation:* Appendix C,
and Appendix E for the `Echo` route. This is the ask vision §6 already names,
reached here from a second class.

No ask for T2, T3 or T5's lean form — the palette reaches all three.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Time | UNIPOLAR | 20–1200 ms, log | RE-201 Repeat Rate; EP-3 head slide |
| 1 | Feedback | UNIPOLAR | 0.00–0.99 | RE-201 Intensity; EP-3 Sound-on-Sound |
| 2 | Mix | UNIPOLAR | 0.0–2.0 (`Echo`'s convention) | Echo Volume, both |
| 3 | Glide | UNIPOLAR | 0–2000 ms, log (0 = instant) | the transport's ramp; no panel control |
| 4 | Wow | UNIPOLAR | 0.0–1.0 | none — slow transport component |
| 5 | Flutter | UNIPOLAR | 0.0–1.0 | none — fast transport component |
| 6 | Treble | BIPOLAR | −10…+10 dB shelf at 5 kHz | RE-201 Treble (S1) |
| 7 | Bass | BIPOLAR | −10…+10 dB shelf at 100 Hz | RE-201 Bass (S1) |
| 8 | Record Level | UNIPOLAR | 0.0–1.0 into the tape's knee | EP-3 Record Level |
| 9 | Spacing | UNIPOLAR | 1–25 µm equivalent, log | none — the head gap behind T2/T3 |
| 10 | Spread | UNIPOLAR | 0.0–1.0 | none — stereo, under D2; inert at 1 channel |
| 11 | Sync | TOGGLE | off / on | none — reads `transport()` |

**Characters:** `"varispeed"` (default), `"sliding-head"`.
**Patches:** 0 *Long Repeats, Slow Glide*; 1 *Short Slap, No Glide*; 2 *Dark
Repeats, Heavy Wow*; 3 *Swell To Self-Oscillation*; 4 *Worn Heads*; 5 *Clean
Transport*; 6 *Dotted Eighth, Synced*.

## 7. Defects in the current class the rebuild must not repeat

1. `delay.py` declares neither `LATENCY_SAMPLES` nor `TAIL_SAMPLES`, so
   `tail_samples` reports `None` — "unknown" — for a class holding a
   0.95-feedback loop (`_core.py:140-141`, `:251-253`).
2. A patch's milliseconds do not port: `_MACRO_RANGES[0]` is a fixed
   20–1000 ms (`delay.py:132`) but the line is `max(time_ms*2.0, 400.0)`
   (`delay.py:80`, `:85`), so 900 ms is silently clamped on a default
   instance. The docstring calls this "the honest failure" (`:75`); it is
   still one patch meaning two things.
3. Wow rate is a class constant with no knob — `WOW_HZ = 0.7`
   (`delay.py:147`), one sine, where T4 wants two components and a drift.
4. `Time` steps: `_apply_macro` writes `delay_ms` straight into the node
   (`delay.py:159`) — §5's 15960 LSB click, on a class named after machines
   whose defining behaviour is what happens while the time moves.
5. A patch is named after a product: `PATCHES[2]` is `"Space Echo"`
   (`delay.py:137`).
6. One in-loop low-pass called `Tone` (`delay.py:167`, 800–16000 Hz at
   `:133`) stands in for both the playback loss law and the Bass/Treble
   controls — different things at different points in the path.
7. `capabilities` is empty and the transport is never read (no
   `CAPABILITIES` in `delay.py`; default `_core.py:139`), so a host cannot
   sync the delay to the session tempo.

## 8. Open questions

1. **Does `"sliding-head"` earn its place?** It doubles T1's measurement work
   and its machine is the one this run could read least about. *Settles:* the
   implementation session, Phase 5; recommendation is keep — it is the cheaper
   of the two and it makes T1a falsifiable by contrast.
2. **Which head does the Echoplex move?** S2 says the **record** head; S4 §1
   says "the read head … moved". Both are length-type so no trait turns on it,
   but the contradiction should not sit silently. *Settles:* Station A.
3. **The absolute head–tape spacing `d`.** T3 fixes the span; the absolute
   figure is a design choice inside S3's 1.5–20 µm. *Settles:* the
   implementation session, from what makes `Spacing` usable.
4. **Is tape hysteresis (T5) affordable on the S3?** S3 needed 16×
   oversampling to keep Jiles-Atherton stable — out of the question here — so
   a cheaper memory model must be found or T5 recorded disconfirmed by design.
   **Cross-phase dependency: `TapeDelay` is Phase 5 and the waveshaper lands
   in Phase 1**, so the waveshaper's need statement should carry a memory/bias
   input or this trait dies. *Settles:* Phase 4's waveshaper work.
5. **N2's fate** — settled by the Phase 0 palette verification, 2026-09-06:
   the two-line half is **refuted** (two nodes in series reach it, measured),
   and what remains is the drift term alone (§5, Appendix E). The shape table
   is still the cheapest home for it, and the chorus's ask decides that.
6. **T2 and §4's `damping_hz` are in conflict, and the conflict is measured.**
   T2 fixes the per-pass loss as S3 eq. (13); §4 proposes to carry it with the
   node's one-pole `damping_hz`. Over 1–10 kHz at 12 cm/s the best possible
   one-pole is **2.9 dB** from even the spacing term alone (Appendix A), and
   the error compounds once per pass, so a one-pole build fails T2 by design at
   the slow end while passing it at 40 cm/s (0.22 dB). Three honest exits, and
   this seed picks none of them: narrow T2's band, add a second in-loop pole as
   a fourth node ask, or record T2 disconfirmed-by-decision with the residual
   measured. *Settles:* Station A, before any code.
7. **How close this class runs to the three-trait floor.** Six Tier 2 rows are
   fixed, but three of them can legitimately end disconfirmed: T2 by the
   conflict above, T4 if Phase 0 refuses N2 (§5), T5 if a memoryless
   approximation ships (§8.4). If all three go, `TapeDelay` finishes on exactly
   **three** demonstrated circuit traits — T1a, T1b and T3 — which is the
   vision §3 floor and no margin. Nothing here is padding, and none of the
   three survivors may be dropped without the class falling below the bar.
   *Settles:* recorded now so the count is watched rather than discovered at
   Station C.

---


## Appendix

### A. The loss arithmetic behind T2 and T3

Run here 2026-09-06 from S3 eq. 13/14 (`k = 2πf/v`; spacing `e^{-kd}`, gap
`sinc(kg/2)`), with S1's speed span; 8.6859 dB per neper.

Spacing loss at 10 kHz:

| tape speed | d = 5 µm | d = 20 µm |
|---|---|---|
| 12 cm/s (RE-201 slowest, S1) | −22.7 dB | −91.0 dB |
| 19.05 cm/s (RE-201 mid) | −14.3 dB | −57.3 dB |
| 40 cm/s (RE-201 fastest, S1) | −6.8 dB | −27.3 dB |
| 20.32 cm/s (EP-3 ≈ 8 ips, S2) | −13.4 dB | −53.7 dB |

T3's 15.9 dB is the 12 → 40 cm/s row at 5 µm. 20 µm is S3's stated worst case
for a tape machine, clearly too wide for an echo unit; it is tabled so
`Spacing`'s range has a documented ceiling.

Gap-loss first null (`f = v/g`) across S3's stated play-gap range:

| tape speed | g = 1.5 µm | g = 5 µm | g = 6 µm |
|---|---|---|---|
| 12 cm/s | 80.0 kHz | 24.0 kHz | 20.0 kHz |
| 19.05 cm/s | 127.0 kHz | 38.1 kHz | 31.8 kHz |
| 40 cm/s | 266.7 kHz | 80.0 kHz | 66.7 kHz |

At the slowest speed with a wide gap the null lands at the top of the audio
band — why T2's tolerance is stated over 1–10 kHz and why the Tier 1 rate
note excludes the gap term at 22.05 kHz.

RE-201 delay span from S1's speed range alone: **3.33 : 1** (40 ÷ 12).

**The full three-term loss, added in the trait-critic pass (2026-09-06)**,
because T2 and T3 now cite eq. (13) whole rather than one term of it. At the
shipped `d = 5 µm, g = 5 µm, δ = 35 µm`, per pass, in dB:

| speed | term | 1 kHz | 3 kHz | 5 kHz | 10 kHz |
|---|---|---|---|---|---|
| 12 cm/s | spacing | −2.27 | −6.82 | −11.37 | −22.74 |
| | thickness | −6.78 | −14.84 | −19.24 | −25.26 |
| | gap | −0.02 | −0.22 | −0.63 | −2.64 |
| | **total** | **−9.07** | **−21.89** | **−31.24** | **−50.64** |
| 40 cm/s | **total** | **−2.96** | **−8.27** | **−12.82** | **−21.89** |

Two consequences the earlier draft did not carry. **Spacing is not the
dominant term at the slow end** — at 12 cm/s the thickness term is the larger
of the two at 10 kHz (−25.3 against −22.7 dB), so "dominant term `e^{−kd}`"
was wrong and T2 now names all three. And **the total is not a straight line
in dB against linear Hz**: the thickness term goes as `1/(kδ)` for large `kδ`,
which is logarithmic, so the best straight-line fit to the total over
1–10 kHz leaves **3.45 dB** of residual at 12 cm/s (1.06 dB at 40 cm/s) —
outside the ±2 dB the earlier T2 asserted. That is why T2 is now stated
against eq. (13) itself rather than against a linearity claim.

T3's span is the 10 kHz row: **28.75 dB** on the total, **15.9 dB** on the
spacing term alone.

**Best one-pole against the loss law** (the figure T2's last clause and §8.6
cite), worst-case dB error over 1–10 kHz against the spacing term alone:
**2.86 dB at 12 cm/s** (best `f_c` 321 Hz), **0.22 dB at 40 cm/s** (best `f_c`
5503 Hz). Against the full three-term total the one-pole is further out still.
The filter is in the loop, so the error compounds once per pass.

### B. The `delay_ms` step measurement behind N1

`audioecho.FeedbackDelay` on the CPython build
(`audiocomponents/.venv/bin/python`), 48 kHz stereo, wet only (`mix=2.0`),
`feedback=0.0`, `max_delay_ms=1000`, 1 kHz sine at 12000 LSB. The node
renders **256 frames per pull** (1024 bytes, measured). `delay_ms` stepped
from 200 ms at block 46.

| step target | worst `\|x[n]−x[n−1]\|` in the wet path | where |
|---|---|---|
| 100.4 ms | **15960** | exactly frame 11776 = block 46 |
| 100.0 ms | 1566 | nowhere near the step |

Reference: the largest step this tone makes anywhere else is **1566**, against
an analytic maximum slope `2πf/f_s·A = 1570.8`.

*Reproduced in the Phase 0 audit, 2026-09-06*, on the same CPython build with
an independently written probe: worst step **15961** at frame 11776 for the
100.4 ms target (the one-LSB difference from 15960 is probe phase, not a
different result), **1566** at frame 9601 — the wet path's onset — for the
100.0 ms control, which again shows nothing at the step. Ratio 10.2×, 0.487 of
full scale. The `set(delay_ms=…)` call is what applies the change; assigning
the attribute does nothing and silently produces the control's result.

**The 100.0 ms row is the control, and it is the point.** At 1 kHz both 200 ms
and 100 ms are a whole number of periods, so the discontinuity is invisible
and the measurement agrees nothing happened. A probe that only ever stepped
to round delays would have certified this node click-free. The material must
be able to express the fault (workspace-craft.md: "ask what the comparison's
material can express"), so the kit's delay probe must step to a **non-integer
number of probe-tone periods** — a requirement that belongs in the Phase 0
kit spec, not only here.

### C. Refutation records for N1 and N2

**N1.** The compose-first alternative is a Python ramp of `delay_ms` across
many blocks. Refuted by the same measurement: at a musically ordinary sweep
(200 → 400 ms over 500 ms, 94 blocks) the residual per-block step is 2.1 ms of
delay, two orders above the 20.8 µs that one sample of line represents, so the
staircase is a 187 Hz buzz rather than a glide. No arrangement of the node's
existing options removes it.

**N2.** The refutation to run in Phase 0: build the beat-period shape table on
CPython, measure its modulation spectrum, and check whether two lines survive
T4's 20 dB separation after the table's own period quantisation. If they do,
N2 collapses into the chorus's table ask and costs nothing extra. If Phase 0
refuses N2, **T4 is recorded disconfirmed-by-decision with this paragraph as
the written reason** and the class ships one modulation line plus drift.

### D. The two pitch laws, derived and simulated

Run here 2026-09-06 from S4's own equations, read in full this run. Both
media obey `pitch = 1 − dT/dt` at every instant — for the speed-type that is
S4 eq. (8) rearranged, so the two are **not** distinguished by that formula,
and the earlier draft's contrast ("`v(t)/v(t−T(t))`, *not* `1 − dT/dt`") was
a false one. They are distinguished by **what the knob is allowed to command**.

*Varispeed (speed-type).* The knob sets `v`; `L` is fixed, so `T` can only
move as eq. (3) allows. For a step `v_old → v_new` at `t₀`, the read head
sees old tape for the whole transient, so `dT/dt = 1 − v_new/v_old` is
constant and

    T(t) = T_old − (t − t₀)·(r − 1),   r = v_new/v_old = T_old/T_new

which reaches `T_new` after exactly `T_new` seconds. Pitch is `r` throughout
and unity after. For 200 → 100.4 ms, `r = 1.99203` = **+1193.1 cents**, held
**100.4 ms**.

*Sliding-head (length-type).* The knob sets `L`, so `T` follows it directly
and may step. During a ramp `dT/dt = 0.4` (200 → 400 ms over 500 ms) the
pitch is `0.6` = **−884.4 cents**, and it is unity the instant the ramp ends.

Both checked numerically at 48 kHz on a 1 kHz tone through an
interpolated-read reference implementation of each medium:

| gesture | varispeed | sliding-head |
|---|---|---|
| step 200 → 100.4 ms | 1992.0 Hz for 100.4 ms, then 1000.0 Hz | 1000.0 Hz throughout — no pitch change, a discontinuity instead |
| ramp 200 → 400 ms over 500 ms | — | 600.0 Hz during, 1000.0 Hz after |

*The feedback discriminator.* A 1 kHz burst at feedback 0.7 through a
**200 → 300 → 200 ms** gesture over 400 ms, pitch of each repeat in cents
against the source:

| repeat | sliding-head | varispeed |
|---|---|---|
| 0 (dry) | 0.0 | 0.0 |
| 1 | +702.0 | −518.0 |
| 2 | +702.0 | −10.4 |
| 3 | +702.0 | 0.0 |
| 4 | +702.0 | 0.0 |

The speed ratios **telescope** on a speed-type medium, so once the speed is
back the whole loop is back at the source pitch; on a length-type the
transposition of the moment each copy was read is written into the loop and
never leaves. That is S4 §1's "erratic overlapping pitch changes" against
"can be cleanly pitched up and down", as two numbers rather than two
adjectives, and it is what T1b's second clause measures.

*What this appendix is and is not.* These are simulations of the two **media**
from S4's equations, not measurements of a pedal and not measurements of the
rebuild. They fix what the rebuild must produce; Station C measures whether it
does.

### E. Palette verification (Phase 0, 2026-09-06)

Every number below was measured in this run on the CPython build
(`audiocomponents/.venv/bin/python`) at 48 kHz, and every line citation was
taken with `grep -n`. Nothing here is read off the old class.

**E.1 The `delay_ms` step, re-reproduced.** Appendix B's measurement stands:
`audioecho.FeedbackDelay`, stereo, wet only, `feedback` 0, 1 kHz at 12000 LSB,
`delay_ms` stepped from 200 ms at block 46 — worst `|x[n]−x[n−1]|` **15961** at
frame 11776 for the 100.4 ms target, **1566** (the tone's own slope, analytic
1570.8) for the 100.0 ms control and for no step at all. The node returns 256
frames per pull.

**E.2 `audiodelays.Echo(freq_shift=True)` is the varispeed medium.** Mono,
`max_delay_ms` 200, `decay` 0, wet only, 1 kHz. At `delay_ms` = 200 the wet is
at 1000.0 Hz. Stepped 200 → 100.4 ms at a block boundary the wet holds
**1988.245 Hz = +1189.8 cents** and returns to 1000 Hz between +90 and +105 ms.
The 3.3-cent shortfall against T1a's +1193.1 is the node's **integer rate**:
`(uint32_t)(max/delay·256)` = 509 (`Echo.c:118`), so the ratio is 509/256 and
`T_new` is 100.589 ms. Worst `|x[n]−x[n−1]|` around the step is **3132**, which
is the *pitched-up* tone's own maximum slope (3123) — the step is click-free,
where `FeedbackDelay`'s is 10.2× its tone's slope.

**E.3 What that costs: a nearest-neighbour read.** `audioif_echo.c:20` reads
`delay_buffer[position >> 8]` with no interpolation. Wet-only residual against
a least-squares 1 kHz fundamental, 16384 samples:

| node | delay | rate | residual / fundamental |
|---|---|---|---|
| `Echo` freq_shift | 200.0 ms | 256 | **−67.8 dB** |
| `Echo` freq_shift | 100.0 ms | 512 | **−67.8 dB** |
| `Echo` freq_shift | 150.0 ms | 341 | **−30.8 dB** |
| `Echo` freq_shift | 66.667 ms | 767 | **−23.7 dB** |
| `FeedbackDelay` | 150.0 / 150.007 / 137.3 ms | — | **−67.8 dB** |

The two clean `Echo` rows are the **control**: at a rate that is a whole
multiple of 256 the read lands on samples and the probe reads the same floor as
the interpolated node, so the measurement is shown to pass as well as fail.

**E.4 Mono is not inert.** `audioecho.FeedbackDelay`, `channel_count` 1,
`delay_ms` 100, `feedback` 0.7, impulse 12000, first four repeat peaks:

| setting | repeats |
|---|---|
| `cross_feed` 0, `input_pan` 0 | 12000, 8400, 5880, 4116 |
| `cross_feed` 0.5 | 12000, 4200, 1470, 515 |
| `cross_feed` 1.0 | 12000, **0, 0, 0** |
| `input_pan` −1.0 | 6000, 4200, 2940, 2058 |
| `input_pan` +1.0 | **0, 0, 0, 0** |

Cause, read in the C: at one channel `other` is 0 (`:248`) but `sent` still
scales by `1 − cross_feed` (`:203`, `:249`), and `input_pan` still writes
`feed_own[0]` (`:135-141`, read at `:253-254`). A `Spread` macro handed
straight to either option silences a mono instance.

**E.5 Two modulation lines without a node change.** Two `FeedbackDelay` nodes
in series (300 ms, `wow_hz` 0.72, `wow_depth_ms` 2.0 → 20 ms, `wow_hz` 5.13,
`wow_depth_ms` 0.6), 1 kHz tone, 30 s; instantaneous frequency by analytic
phase, `−dT/dt` integrated to the delay's modulation spectrum:

| build | lines found | above the 0.2–12 Hz median floor |
|---|---|---|
| one node, one wow | 0.712 Hz | +133 dB (second peak −57.6 dB below it) |
| two nodes in series | 0.712 and **5.120 Hz** | **+123 and +112 dB** |

Ratio 7.1905; the nearest `p/q` with `p, q ≤ 8` is 7/1, 2.7 % away, so T4's
incommensurability clause is met by choosing the rates. The second node sits
*outside* the feedback loop, so its component does not accumulate per pass —
T4 as written does not require that; if the class means it to, T4 must say so
and the ask returns.

**E.6 The drift is the part the palette cannot write.** A random walk in
`set(delay_ms=…)` at block rate, 1 kHz tone, worst `|x[n]−x[n−1]|`:

| walk | frames per block | worst step (tone's own is 1571) |
|---|---|---|
| none | 0 | 1566 |
| node's own wow, 1.5 ms at 0.05 Hz | per sample | **1566** |
| σ = 0.0005 ms/block | 0.024 | 1675 |
| σ = 0.002 ms/block | 0.096 | 2042 |
| σ = 0.03 ms/block | 1.44 | **8752** |

Per-sample modulation of any depth costs nothing; a block-rate walk large
enough to hear is a staircase. **And the detector must be shown to fail:** the
sub-0.1 Hz statistic used here read **+62 dB above the floor with the walk
switched off**, so it cannot tell drift from no drift. The kit's drift
measurement needs a no-drift control before any build is credited with T4's
last clause.

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

Rate note: **T2's gap term cannot hold at 22.05 kHz** — at the slowest speed
the gap null sits at 20–24 kHz (Appendix A), above Nyquist there; T2 and T3
are then checked on the spacing and thickness terms alone, the gap term
recorded out of band, not failed.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Roland, *RE-201/101 Service Notes*, 2nd ed. 1978 (OCR text + page images at 1785×2526) | tape speed 12–40 cm/s ("Other Reference Data"); head order (Fig. 6); S/N 60 dB "A" weighted; bias 50–60 Vrms across the erase head, trap coil L21 leakage below 2.5 Vrms (§2-1); Bass **±10 dB** @100 Hz, Treble **±10 dB** @5 kHz; §2-7 "Adjust VR12 so that multiple repetition of noises occurs with Intensity Control as shown" | **license unverified — treated as copyleft.** The archive.org metadata API carries **no `licenseurl` and no `rights` field** (re-checked in the audit, 2026-09-06); read as a document, nothing reproduced | https://archive.org/download/Roland_RE-101_RE-201_Service_Manual/Roland_RE-101__RE-201_Service_Manual_djvu.txt (metadata: https://archive.org/metadata/Roland_RE-101_RE-201_Service_Manual; page images: `…/page/n5.jpg`, `…/page/n23.jpg`) | yes — text, metadata and pages n5/n14/n23 re-read in the audit |
| **S2** Arnardottir, Abel & Smith III, *A Digital Model of the Echoplex Tape Delay*, AES Convention 125, 2008 | "fixed playback and erase heads, a movable record head"; "a tape loop moving at roughly 8 ips"; "the quasiperiodic capstan and pinch wheel components and drift of the observed fluctuating time delay" | "Audio Engineering Society, Inc. All rights reserved" (read on the page, audit 2026-09-06); full text **paywalled**, $33 non-member | https://aes.org/publications/elibrary-page/?id=14800 | abstract only (re-fetched in the audit; the three quotes above are verbatim from it) |
| **S3** Chowdhury, *Real-time Physical Modelling for Analog Tape Machines*, DAFx-19 | the three loss terms and `k = 2πf/v` (eq. 13/14); Jiles-Atherton (eq. 6/18); play gap "1.5 to 6 microns"; spacing "can be as high as 20 microns"; bias "usually about one order of magnitude larger than the input" (§3.3); "our system uses an oversampling factor of 16x" (§4.1) | **no rights statement printed** anywhere in the PDF (searched in the audit) — **license unverified, treated as copyleft**: read as a paper, never for code | https://ccrma.stanford.edu/~jatin/420/tape/TapeModel_DAFx.pdf | yes, full text — re-downloaded and re-extracted in the audit, every figure above checked against the paper |
| **S4** Zavalishin & Parker, *Efficient emulation of tape-like delay modulation behavior*, DAFx-18 | §1: "we call these length-type delays … we call these speed-type delays. This difference is exemplified by two famous tape-based delay devices - the EchoPlex, and the Roland Space Echo series. The former allows the read head of the tape machine to be moved, whereas the latter allows the speed of the motor driving the tape to be changed"; length-type pitch "dictated purely by the rate of change of the length", speed-type "defined by the ratio of speeds"; the tape equation integral (3), difference (6), differential (8), and §2.1 on (8)'s unbounded drift | **no rights statement printed** anywhere in the PDF (searched in the audit) — **license unverified, treated as copyleft**: read as a paper, never for code | https://dafx.de/paper-archive/2018/papers/DAFx2018_paper_9.pdf | yes, full text — re-downloaded and re-extracted in the audit; the quotes above are verbatim |
| **S5** Holters & Parker, *A Combined Model for a Bucket Brigade Device…*, DAFx-18 | T1's contrast: "This is in contrast to a simple digital delay-line, which would exhibit a discontinuity at the output when subjected to a discontinuous change in delay time" (fig. 8) | **no rights statement printed** anywhere in the PDF (searched in the audit) — **license unverified, treated as copyleft**: read as a paper, never for code | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2018/09/Holters-Parker-2018-A-Combined-Model-for-a-Bucket-Brigade-Device-and-its-Input-and-Output-Filters.pdf | yes, full text — re-downloaded and re-extracted in the audit; the quote is verbatim |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1b** | *sliding-head:* the Time control commands the **length**, so `T` follows the knob directly: while the knob moves the wet pitch is exactly `1 − dT/dt` and returns to unity the moment it stops — a 200 → 400 ms ramp over 500 ms gives **−884 cents for the 500 ms of the ramp**, and a *step* gives **no pitch offset at all**, a discontinuity instead. Under feedback the excursion is **baked in**: after a Time gesture that returns to its starting value at least one recirculating repeat is left more than 100 cents off and stays there, where varispeed returns every repeat to the source pitch | S4 §1 verbatim (length-type gives "erratic overlapping pitch changes", speed-type "can be cleanly pitched up and down"), eq. (8); both figures derived and simulated here (Appendix D) | high | a ramp offset more than 10 cents from `1 − dT/dt`; a pitch offset surviving more than 20 ms past the end of the ramp; the two characters leaving the same permanent transposition after the out-and-back gesture; sliding-head returning every repeat to within 5 cents; or varispeed leaving any repeat more than 5 cents off | the ramp, on both characters; then a 1 kHz burst at feedback 0.7 through a 200 → 300 → 200 ms gesture over 400 ms, pitch of repeats 1–4 by windowed FFT with parabolic peak interpolation, in cents against the source |
| **T2** | one pass applies the **three-term playback loss of S3 eq. (13)** — spacing `e^{−kd}`, thickness `(1−e^{−kδ})/(kδ)`, gap `sinc(kg/2)`, all at `k = 2πf/v` — evaluated at the class's declared `d`, `g`, `δ` and the character's speed, to **±2 dB from 1 to 10 kHz**; and `n` passes give `n×` the one-pass loss in dB to **±2 dB at 10 kHz**. At the shipped `d = 5 µm, g = 5 µm, δ = 35 µm` that is **−9.1 dB at 1 kHz and −50.6 dB at 10 kHz at 12 cm/s**, **−3.0 and −21.9 dB at 40 cm/s** (Appendix A). It is **not a one-pole**: the best single one-pole fit to even the spacing term alone is **2.9 dB out at 12 cm/s** over 1–10 kHz | S3 eq. 13/14, read in full this run; `d`, `g`, `δ` chosen inside S3 §3.2's own stated ranges; arithmetic Appendix A | high on the law, medium on `d`/`g`/`δ` — they are design parameters, not Roland figures | a one-pass curve more than 2 dB from eq. (13) anywhere in 1–10 kHz; `n`-pass differing from `n×` one-pass by more than 2 dB at 10 kHz; or a curve a single one-pole fits better than 2 dB at 12 cm/s, which would mean the loss law did not ship | per-pass darkening: impulse at feedback 0.7, isolate repeats 1–5 by arrival time, fit `loss_dB(f)` each, report worst deviation from eq. (13) and from `n×` repeat 1, on both characters |
| **T3** | that loss **moves with `Time` on varispeed and not on sliding-head**, because `k = 2πf/v` and only `v` changes: across the RE-201's own **12–40 cm/s** (S1) the 10 kHz per-pass loss changes by **28.8 dB** on the full eq. (13) at the shipped `d`/`g`/`δ` (**15.9 dB** on the spacing term alone), and by **less than 1 dB** on sliding-head, whose speed is fixed. The bar: **≥ 15 dB** varispeed, **≤ 1 dB** sliding-head | S1 (12–40 cm/s, re-read this run) + S3 eq. 13/14; Appendix A | medium — the span is the claim; `d` is a design parameter, not a Roland figure | varispeed moving the 10 kHz per-pass loss by less than 15 dB across the Time range; or sliding-head moving it by more than 1 dB | T2's measurement at Time = 60, 200, 600 ms on both characters; report the 10 kHz loss at each and the span |
| **T4** | the fluctuation is **quasiperiodic: at least two components plus a slow drift** (S2) — over 60 s the recovered delay's modulation spectrum shows **two lines each ≥ 20 dB above the median floor between them**, whose ratio is **not within 1 % of `p/q` for any integers `p, q ≤ 8`**, plus **non-line energy below 0.1 Hz at least 10 dB above that floor** | S2 abstract, re-fetched this run (full text paywalled, $33) | medium — the abstract names the capstan, pinch-wheel and drift components; no rate or depth was read, so the structure is fixed here and the numbers are the rebuild's to choose and report | one line; two lines whose ratio is within 1 % of a small-integer ratio (`q ≤ 8`); either line under 20 dB above the floor; or sub-0.1 Hz energy under 10 dB above it | LFO extraction: instantaneous delay by cross-correlating wet against dry over 60 s of broadband probe, then a Welch spectrum of the delay trace; report the two largest lines, their ratio against every `p/q` with `q ≤ 8`, and the band power below 0.1 Hz |
| **T5** | record level into tape is **compressive with memory**: at `Record Level` 0.5 the H3 of a 1 kHz tone through one pass differs by **≥ 1 dB** between a rising and a falling approach to that same knob value, against a **±0.2 dB** repeatability floor established by running one approach twice; a memoryless soft-clip gives 0 dB by construction | S3 §1.2, §2.2 (Jiles-Atherton, eq. 6/18), read this run | medium — a memoryless approximation may ship, and then T5 is recorded disconfirmed by design | the two approaches agreeing within the 0.2 dB repeatability floor | harmonic spectrum at level: 1 kHz at −12 dBFS, `Record Level` swept 0→1→0 over 4 s, H3 read at the two crossings of 0.5; run the rising leg twice first to fix the floor |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §3)*

**Latency is zero.** The dry path is the input frame, unfiltered and
undelayed; a tape echo has nothing to look ahead for. `latency_samples` is
**0** at every rate, macro setting and character, and the class ships **no
option that adds latency** — no lookahead, convolution partition, pitch window
or oversampling. The wet path's delay is the effect, not latency, on the same
reasoning `Rack` uses for a chorus's mean delay; verified at the class gate by
the click measurement at 48 and 44.1 kHz. `tail_samples` is **not** constant:
recomputed on every `Time`/`Feedback` move as `T · ln(0.001)/ln(feedback)`
frames, clamped to the line length at `feedback` 0 and to a declared ceiling
as `feedback → 0.99`. A fixed number, or `None`, fails Tier 1.

*(from §5)*

**N2 — a second modulation term on the same node.** *Unblocks* **T4**. *The
palette instead:* one magic-circle sine at `wow_hz` (`:111-115`, `:209-210`),
depth at `:116-119` — one oscillator, one line, no home for the drift term;
moving `wow_depth_ms` from Python is block-rate and re-introduces N1's
staircase.

*(from §5)*

**REFUTED BY PALETTE (as asked):** two `audioecho.FeedbackDelay` nodes in
series, each with its own `wow_hz`/`wow_depth_ms`, put **two lines in the
recovered delay** — measured at 0.712 Hz and 5.120 Hz, **+123 dB and +112 dB**
above the 0.2–12 Hz median floor over 30 s, ratio 7.19, no `p/q` with
`p, q ≤ 8` within 1 % (Appendix E). T4's two-component clause needs no node
change; it needs a second node, and the price is Tier 3's, not the palette's.
**What survives is narrower: the drift.** T4's sub-0.1 Hz clause wants
*non-line* energy, and the only way to write a random walk today is
`set(delay_ms=…)` at block rate, which is N1's staircase again: measured on a
1 kHz tone, a walk of 1.44 frames per block puts a worst sample-to-sample jump
of **8752** into the wet path against the tone's own 1571, and even 0.096
frames per block reads 2042 (Appendix E). The node's own per-sample wow at any
depth stays at 1566 — the control. *Restated ask (N2′):* **one per-sample
drift state** on `audioecho.FeedbackDelay` — the slow random walk, four floats
and one add per frame — or the same read taken from the **one-period shape
table** vision §6 proposes for the chorus, one option serving both classes.
Not a second oscillator. *Honesty note for whoever measures T4:* the sub-0.1 Hz
detector used here read **+62 dB above the floor with the drift switched off**,
so the kit's drift measurement must be shown to fail on a no-drift control
before any build is credited with that clause (Appendix E).
