# Effects Dossier — `Compressor` (four characters: FET, Optical, VCA/RMS, Vari-Mu)

**Class:** `lib/audioeffects/dynamics.py` — read once, for §7.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** UREI 1176, Teletronix LA-2A, dbx 160, Fairchild 670 (vision §4.2)
— **all four confirmed, no swap argued**. The vision's framing is confirmed
too: the four differ in *detector law*, *release law*, *ratio law* and
*sidechain topology*, not in three time constants. Each carries its own trait
rows (vision §10.7).
**Grade:** **literature**, not circuit. One character reaches a schematic with
values (Optical — S2 carries the LA-2A's gain-reduction, side-chain and output
schematics with designators); the other three rest on manufacturer
specification plus published analysis, and no 1176 schematic was reached (§2,
"not found"). The traits are not weaker for it: three of the four standouts
publish the *numbers* — attack/release spans, a release rate in dB/s, six
time-constant pairs — that a schematic would only let us re-derive.
**Portability tier:** needs audioif-own nodes (`audiodynamics`), which is not a
CircuitPython port (`audioif/docs/upstream-diff.md:661`).
**Status:** seed (Phase 0), written 2026-09-06; audited the same day by an
independent licence and citation pass that re-fetched every row itself
(Appendix F); then attacked on 2026-09-06/07 by an independent **trait-critic**
pass that re-reached every Tier 2 source from its own bytes and rewrote the
rows (Appendix G, changes listed in G.7). No earlier draft existed; every source
below was reached, and S10 — the Fairchild 670 manual the seed had recorded as
unreachable — was added by that audit. The trait-critic pass found two arithmetic
errors the licence audit had recorded as "re-derived", one bar a single-stage
release could clear, and four rows whose disconfirmation contradicted their own
trait; it added three traits, each from a manufacturer specification page it
fetched itself.

## 1. The circuit, in one paragraph

All four are **detector → gain computer → gain cell**, and all four differ in
every one of those three. Quotations behind every claim here are in Appendix D.
**FET (1176):** the cell is a field-effect transistor used as a
voltage-controlled resistor, "arranged in a feedback configuration to obtain
gain reduction" (S9); S1's own specification line gives the input as "600 Ω,
bridged T-control (floating)", but **no source reached this run says the FET is
the control element of that bridged-T network**, so that topology detail is
recorded here as unsourced and is not a trait. The side chain is tapped
*after* the cell, so the loop is **feedback** (S3). The panel
gives Input (drive *and* threshold), Output, Attack **20–800 µs** and Release
**50 ms–1.1 s** — both faster clockwise — and four exclusive ratios **4:1 / 8:1
/ 12:1 / 20:1**, with higher ratios also setting the threshold higher (S1) and,
per S3 reading UREI's own transfer plot, hardening the knee. All four buttons at
once is a fifth *mode*, not a fifth ratio: S1 attributes its radical distortion
to a lag on the attack of initial transients, constantly changing times, and a
shift in the bias points. **Optical (LA-2A):** the cell is the lower leg of a
divider formed by a **T4** — an electroluminescent panel facing a
cadmium-sulfide photocell — driven by Peak Reduction pot → 12AX7 → **R37
pre-emphasis** → 6AQ5 EL driver, again **feedback** (S2). There are no time
knobs; both are set entirely by the T4. The release is **two-stage** —
about 0.06 s for 50 %, then 0.5–5 s for the rest depending on how much reduction
came before — with a **memory**: the release is slower after longer or deeper
compression (S2). Peak Reduction is side-chain gain, i.e. a *threshold*; a
Limit/Compress switch raises the ratio. **VCA/RMS (dbx 160):** a decilinear
(Blackmer) VCA driven by a **true-RMS** detector and, uniquely of the four,
**feed-forward** (S5). There are no time knobs because the times fall out of the
detector: attack "15 ms for 10 dB, 5 ms for 20 dB, 3 ms for 30 dB" and release
"8 ms for 1 dB, 80 ms for 10 dB, 400 ms for 50 dB; 125 dB/sec Rate" (S4) —
three points on one straight line in dB. Hard knee (S5 models the original as
"a classic feed-forward hard-knee VCA-based compressor"); the 1:1–∞:1 ratio span
is the **160X**'s specification line (S4, whose scan OCRs as "Variable 1:1 -
c2:1 thru to —1:1") and the Waves plug-in's control range ("1:1 to inf:1", S5),
not a figure read from an original-160 specification (§8.3).
**Vari-Mu (670):** the cell is a push-pull stage of paralleled **6386**
remote-cutoff triodes whose µ falls with control voltage, side chain again
tapped after the cell (**feedback**, S6). There is no ratio knob — the slope
starts between 1:1 and 2:1 on small peaks and climbs to about 20:1 on loud ones
(S6; the manual's own line is "Variable from 1:1 to 1:20 above a predetermined
level", S10, whose control list has no ratio control) — and a six-position TIME
CONSTANT switch selects fixed attack/release *pairs*, the last two of which are
themselves program-dependent (S10, corroborated by S6 except at position 4).

## 2. Sources and license calls

Full quotations and the component values taken from each are in Appendix D.

| # | Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|---|
| S1 | Universal Audio, *Model 1176LN Solid-State Limiting Amplifier* manual … (App. S1) | Attack/release spans and knob sense; the four ratios … (App. S1) | "© 2009 Universal Audio … (App. S1) | https://media.uaudio.com/assetlibrary/1/1/1176ln_manual.pdf | 2026-09-06 — PDF fetched; unreadable to the fetch tool, text extracted locally with `pypdf` (Appendix A) |
| S2 | Universal Audio, *Model LA-2A Leveling Amplifier* manual … (App. S2) | The two-stage release spec and the 40–80 ms first … (App. S2) | "Copyright 2000 Universal Audio … (App. S2) | https://media.uaudio.com/assetlibrary/l/a/la-2a_manual.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S3 | Austin Moore, "All Buttons In: An investigation into the use of the … (App. S3) | Feedback topology, stated and contrasted with … (App. S3) | Huddersfield repository cover sheet … (App. S3) | https://eprints.hud.ac.uk/id/eprint/27391/1/Journal%20on%20the%20Art%20of%20Record%20Production%20%C2%BB%20All%20Buttons%20In_%20An%20investigation%20into%20the%20use%20of%20the%201176%20FET%20compressor%20in%20popular%20music%20production.pdf (from the item page https://eprints.hud.ac.uk/id/eprint/27391/) | 2026-09-06 — PDF fetched, `pypdf` |
| S4 | dbx, *160X / 160XT Service Manual* (full text) | The attack and release specifications quoted in §1 … (App. S4) | Licence unverified … (App. S4) | https://archive.org/stream/dbx_160X-XT_Service_Manual/160X-XT_Service_Manual_djvu.txt | 2026-09-06 |
| S5 | Waves, *dbx® 160 Compressor/Limiter User Guide* | The original 160 (1976) as "decilinear VCA … (App. S5) | **Licence unverified … (App. S5) | https://assets.wavescdn.com/pdf/plugins/dbx-160.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S6 | Hannes Bieger, "Fairchild 660 & 670", *Sound On Sound*, May 2016 | The six TIME CONSTANT pairs … (App. S6) | "All contents copyright © SOS Publications … (App. S6) | https://www.soundonsound.com/reviews/fairchild-660-670 | 2026-09-06 |
| S7 | R. Simionato & S. Fasciani … (App. S7) | Independent restatement of the LA-2A's dynamics … (App. S7) | "© 2023 Riccardo Simionato et al. … Creative … (App. S7) | https://www.dafx.de/paper-archive/2023/DAFx23_paper_10.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S8 | J. Najnudel, R. Müller, T. Hélie, D. Roze … (App. S8) | The mechanism under the optical two-stage release and … (App. S8) | "© 2023 Judy Najnudel et al. … Creative … (App. S8) | https://www.dafx.de/paper-archive/2023/DAFx23_paper_50.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S9 | Wikipedia, "1176 Peak Limiter" | Cross-check only: FET "in a feedback configuration" … (App. S9) | CC BY-SA 4.0 | https://en.wikipedia.org/wiki/1176_Peak_Limiter | 2026-09-06 |
| S10 | Fairchild Recording Equipment Corporation, *Instruction Manual … (App. S10) | **The Fairchild primary source … (App. S10) | Licence chain, per `instrument-sources.md` … (App. S10) | https://archive.org/download/fairchild_670-im/fairchild_670-im_djvu.txt (item https://archive.org/details/fairchild_670-im), corroborated by the independent scan https://archive.org/download/Fairchild_670_owners_manual/Fairchild_670_owners_manual_djvu.txt | 2026-09-06 — both full texts fetched (HTTP 200) and the specification page read in each; both scans' OCR renders "4" as "U"/"h" throughout ("10-40 45th Avenue", "14\" panel space"), which is how ".U milliseconds" and "«4, milliseconds" read as 0.4 ms |

Copyleft sources are measured or read as papers, never read for code structure
(vision §5). No source here is copyleft code; S7 and S8 are CC BY papers. S4 has
no stated licence at all and is treated as copyleft, as do S5 and S10; S1, S2
and S6 are read under explicit all-rights-reserved notices, quoted only as short
excerpts.

The licence and citation audit's record is Appendices E and F: E is the first
pass (twelve corrections), F is the independent re-fetch of 2026-09-06 that
audited E's own work and applied nine further corrections. Where the two
disagree, F is the later reading and wins.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

#### Character FET — the 1176

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| F1 | **Both time macros span the unit's ranges and both get *faster* as the macro rises.** Release 1.1 s ±25 % *(own)* at the macro's minimum, 50 ms ±25 % at its maximum. Attack 800 µs ±25 % (29–48 samples at 48 kHz) at the minimum; at the maximum, 20 µs is **0.96 of a sample period at 48 kHz**, below any rate here, so the fast end is a **bound** — 10–90 % time ≤ one sample period. Every intermediate setting faster than the one below | S1 spec page and both knob paragraphs (G.1) … (App. F1) | high (spans) … (App. F1) | Any of the four ends outside its band; a fast-end time longer than one sample period; either macro non-monotone or inverted | 10–90 % of the GR trace on a DC … (App. F1) |
| F2 | **Threshold rises with ratio; the knee narrows with it.** With everything else fixed, the fitted knee point rises monotonically across 4:1 → 8:1 → 12:1 → 20:1 by more than the fit residual at every step, and the fitted knee width falls monotonically across the same four | S1 verbatim, "higher Ratio settings also set … (App. F2) | high (direction) … (App. F2) | A knee point that does not move, moves down, or moves by less than the fit residual at any step; a width that widens or is flat | Static curve … (App. F2) |
| F3 | **All-Button is a mode, not a fifth ratio.** On one patch: (a) static slope between **12:1 and 20:1**; (b) GR in the first 2 ms of a 20 dB step at least **3 dB *(own)*** *less* than the 4:1 patch's at the same Attack; (c) THD on a 100 Hz sine at 12 dB of GR at least **10 dB *(own)*** above the 4:1 patch's, whose own ceiling is F5 | S1's All-Button paragraph carries all three … (App. F3) | high (the range) … (App. F3) | Slope outside 12:1–20:1; first-2 ms GR within 3 dB of the 4:1 patch's or above it; THD less than 10 dB above the 4:1 patch's | Static curve … (App. F3) |
| F4 | **The loop is feedback, and the paired build proves it.** The feedback build's 10–90 % GR time on a 20 dB step is **strictly longer than the feed-forward control's at every setting measured** — six Attack settings × four ratio patches — no tie, no reversal, excluding only settings where the control's own time is under two sample periods and the rate sets the answer. Magnitude recorded, never required; the earlier "at least twice" is withdrawn as a pass condition, unsourced (G.7) | Topology: S1 verbatim … (App. F4) | high | Any measured setting where the feedback build ties or beats the control | GR trace on a 20 dB step … (App. F4) |
| F5 | **Clean everywhere except All-Button.** On every non-All-Button patch, a sine held at 10 dB of GR with Release at its slowest measures THD(h2..h10 re fundamental) ≤ **0.5 %** at 50 Hz, 1 kHz and 15 kHz. Without it, a build that distorts on every patch passes F3 by distorting slightly less at 4:1 | S1 spec page verbatim … (App. F5) | high (the figure) … (App. F5) | THD above 0.5 % at any of the three frequencies, on any non-All-Button patch, at the slowest release | Harmonic spectrum at 50 Hz … (App. F5) |

#### Character Optical — the LA-2A

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| O1 | **Two-stage release, measured at exactly 10 dB of GR.** After a 10 s tone holding 10 dB of GR stops: t50 **40–80 ms**, t95 **0.5–5 s**, **t95/t50 ≥ 8**. The depth is pinned because the ratio moves with it: at 10 dB a one-pole in the *linear* envelope — what the palette node is (B.1) — gives **5.61**, a GR exponential in dB gives **4.32**, a ramp linear in dB **1.90**; the same one-pole reaches **7.69** at 20 dB, so an unpinned probe lets a single-stage release pass (G.6) | S2's spec line and theory section (G.2) … (App. O1) | high | t50 outside 40–80 ms, t95 outside 0.5–5 s, or **t95/t50 < 8** | GR trace after a 10 s tone … (App. O1) |
| O2 | **The slow stage carries memory, both ways the source names it.** Four burst-then-silence traces (200 ms / 10 s × 3 dB / 15 dB): t95 after 10 s is ≥ **2× *(own)*** t95 after 200 ms at the same depth, **and** t95 after 15 dB is ≥ 2× t95 after 3 dB at the same length | S2 verbatim on the cell's recovery depending … (App. O2) | high (direction) … (App. O2) | Either comparison below 2×, or either in the wrong direction | Four GR traces as above … (App. O2) |
| O3 | **No time knobs; the amount knob is a threshold; the toggle is the ratio.** (a) Attack and Release are **inert** — sweeping either end to end moves no measured time beyond the repeat spread — and the measured attack sits at **10 ms ±50 % *(own)***; (b) Peak Reduction moves the fitted knee point monotonically while changing the asymptotic slope by ≤ **0.05 dB/dB *(own)*** over its travel; (c) the Limit position's asymptotic slope is **strictly steeper** than Compress at every Peak Reduction setting measured | S2 on the T4 determining both times … (App. O3) | high (a, c) … (App. O3) | Either time macro changing a measured time; attack outside 5–15 ms; Peak Reduction moving the slope by more than 0.05 dB/dB; the toggle not changing the slope, or changing it the wrong way at any setting | Static curves at five Peak … (App. O3) |
| O4 | **Frequency-weighted side chain, flat when the knob is home.** At Emphasis maximum the steady GR on a 10 kHz sine exceeds that on a 100 Hz sine **of equal RMS** by ≥ **6 dB *(own)***; at Emphasis minimum — the factory setting — the two agree within **1 dB *(own)*** | S2 verbatim on R37 being factory-flat and … (App. O4) | high (direction … (App. O4) | No difference at maximum; a difference in the wrong direction; more than 1 dB at minimum | Steady GR on 100 Hz and 10 kHz … (App. O4) |
| O5 | The loop is **feedback**: F4's paired-build ordering, unchanged, on this character's settings | S2 verbatim, "The LA-2A is a feed-back style … (App. O5) | high | As F4 | As F4, on the optical default … (App. O5) |

#### Character VCA/RMS — the dbx 160

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| V1 | **The release is a straight line in dB.** Over one recovery from **20 dB** of GR to **1 dB**, the instantaneous rate stays within **±20 % *(own)*** of its mean across the span, and at Release macro centre the mean is within ±20 % of **125 dB/s** | S4's spec line, whose three points *are* 125 … (App. V1) | high | Rate anywhere in the 20 → 1 dB span more than 20 % off the mean, or a mean outside 100–150 dB/s at macro centre | GR trace after a burst holding 20 … (App. V1) |
| V2 | **Attack strongly level-dependent, on the three published points.** On DC steps 10, 20, 30 dB over threshold the time for GR to first reach the full overshoot is within **±30 % *(own)*** of **15, 5 and 3 ms**; the consequence t(30) ≤ ⅓·t(10) is checked too | S4 verbatim, "!5ms for 10dB, Sms for 20dB … (App. V2) | high (the figures) … (App. V2) | Any of the three outside its band, or t(30)/t(10) above ⅓ | GR traces on 10, 20 … (App. V2) |
| V3 | **RMS, not peak — and both comparison figures are derived, not asserted.** At ratio ∞:1, knee 0, so the GR difference equals the level difference: (a) square and sine of **equal RMS** give GR within **0.5 dB *(own)***, where a **peak** detector differs by 20·log₁₀√2 = **3.01 dB**; (b) a bipolar **10 %-duty** train and a sine of **equal peak** differ by **6.99 ± 1 dB *(tolerance own)*** — 20·log₁₀(√0.5/√0.1) — where a peak detector differs by **0 dB**. *(The earlier "9–11 dB" is a 5 %-duty figure; G.6.)* | S4, "true-RMS level detector … and … (App. V3) | high | Square/sine at equal RMS differing by more than 0.5 dB; the pulse/sine pair outside 5.99–7.99 dB — in particular near 0 dB (a peak detector) or near 10 dB (a 5 %-duty probe used by mistake) | Steady GR on sine, square … (App. V3) |
| V4 | **Hard knee, ratio reaching ∞:1.** At Ratio maximum the static slope above the knee is ≤ **0.05 dB/dB *(own)*** over 20 dB of input, and at Knee zero the fitted width is ≤ **1 dB *(own)*** | S4's control description … (App. V4) | high | A slope above 0.05 dB/dB anywhere in the 20 dB span, or a fitted knee wider than 1 dB at Knee zero | Static curve, 60 levels … (App. V4) |
| V5 | The loop is **feed-forward** — the only one of the four — so F4's ordering **reverses**: the shipped VCA build is the control and a feedback build of identical settings is strictly slower at every setting whose control time exceeds two sample periods | Topology: S4 ("feed-forward circuitry") … (App. V5) | high | Any such setting where the pair ties, or where the shipped build is slower | As F4, same probe … (App. V5) |
| V6 | **Clean at any amount of compression.** A 1 kHz sine measures THD ≤ **0.2 %** at 3, 10 and 20 dB of GR, on every VCA patch and at every Release setting — the tightest of the four characters, and what separates the VCA from the FET by measurement rather than adjective | S4 spec page verbatim, "THD <0.2% … (App. V6) | high (the figure) … (App. V6) | THD above 0.2 % at any of the three depths, at any Release setting | Harmonic spectrum of a 1 kHz sine … (App. V6) |

#### Character Vari-Mu — the Fairchild 670

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| M1 | **The ratio is a consequence of level, not a setting.** Local slope ≥ **0.5 dB/dB** (no steeper than 2:1) where measured GR is **2 dB**, ≤ **0.05 dB/dB** (at least 20:1) where it is **15 dB**, falling monotonically between | S10's ratio line, "Variable from 1:1 to 1:20 … (App. M1) | high (span) … (App. M1) | Slope below 0.5 dB/dB at 2 dB of GR (20:1 arriving too early); above 0.05 dB/dB at 15 dB (never reaching 20:1); a non-monotone stretch wider than one curve step | Static curve, 60 levels … (App. M1) |
| M2 | **Six fixed time-constant pairs, as six patches.** Attack within ±30 % *(own)* of **{0.2, 0.2, 0.4, 0.4, 0.4, 0.2} ms** — the manual publishes two attack values — and release within ±30 % *(own)* of **{0.3, 0.8, 2, 5, 2, 0.3} s**, the fifth and sixth being the manual's **individual-peak** figures (the multiple-peak ones are M3's). **The release measurement is this dossier's definition, not the manual's:** the manual says "from 10 db of limiting" and names no endpoint, so the kit holds exactly 10 dB, releases, tests **t63** against the table and publishes **t90** beside it, so the endpoint can be re-argued from data | S10's SPECIFICATIONS page … (App. M2) | high — read from the … (App. M2) | Any pair outside its band; fewer or more than six patches; a t63/t90 pair whose ordering says the release is not monotone | 10–90 % attack and both t63 and … (App. M2) |
| M3 | **Patches 5 and 6 are program-dependent; 1–4 are not.** With "multiple peaks" defined here as **ten 10 ms bursts at 200 ms spacing, each reaching 10 dB of GR**, t63 after the train is ≥ **3× *(own)*** t63 after a single such burst on patches 5 and 6, while 1–4 move **< 25 % *(own)*** between the two probes | S10 verbatim on positions 5 and 6 (G.4) … (App. M3) | high (the … (App. M3) | Patches 5 or 6 below 3×; any of 1–4 above 25 % | Two GR traces per patch … (App. M3) |
| M4 | The loop is **feedback**: F4's paired-build ordering, once per patch | S6, "the side-chain signal is tapped after … (App. M4) | medium | As F4, on any of the six patches | As F4, once per patch |
| M5 | **Clean at 10 dB of limiting.** A 1 kHz sine held at 10 dB of GR measures THD ≤ **1 %** on every one of the six patches, patch 6's fast 0.3 s release included | S10 spec page verbatim … (App. M5) | high (the figure) … (App. M5) | THD above 1 % on any patch at 10 dB of GR | Harmonic spectrum of a 1 kHz sine … (App. M5) |

### Tier 3 — cost and latency

`capabilities` = `()` — a compressor's timing is program-dependent, not
tempo-dependent, and the class does not read the transport (§8.6 keeps the
question open).

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Nodes:** one `audiodynamics.Dynamics` in `DYN_COMPRESS` per instance, as
today. Portability tier **audioif** (`audioif/docs/upstream-diff.md:661`,
`:673`); on a stock CircuitPython board the module imports and construction
raises a clear `ImportError` (roadmap §3). **A mono source is compressed, not
summed**: the kernel selects mono or stereo at `audioif_dynamics.c:235` and the
cross-channel max (`:263-269`) collapses to one channel. That is the statement
the kit measures.

Any coefficient table the rebuild ships is computed on CPython and shipped as
data; nothing is rebuilt on a board.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

All four are additive options on `audiodynamics`, audioif's own module (D1);
none touches a CircuitPython-ported node. Each is filed as an audioif issue only
after its refutation.

- **N-C1 — a second release stage with memory.** Unblocks **O1, O2, M3**. …  *(argument in full: App. R)*
- **N-C2 — an RMS detector option.** Unblocks **V3**. *Palette instead:* `fabsf` …  *(argument in full: App. R)*
- **N-C3 — a constant-rate release.** Unblocks **V1**. *Palette instead:* the …  *(argument in full: App. R)*
- **N-C4 — a feedback detector.** Unblocks **F4, O5, M4**, three of the four …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

**Characters** (constructor `character=`, one trait set each): `"fet"`,
`"optical"`, `"vca"`, `"varimu"`. Default `"optical"`.

**Macros — 14 of the 16 allowed.**

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Threshold | UNIPOLAR | −60…0 dB | 1176 Input; LA-2A Peak Reduction; 160 Threshold; 670 Input Gain |
| 1 | Ratio | UNIPOLAR | 1…1000:1 log | 1176 ratio buttons; 160 Compression; the top of the 670's slope |
| 2 | Attack | UNIPOLAR | 0.02…300 ms log | 1176 Attack; 670 time-constant attack; inert in `optical` (O3) |
| 3 | Release | UNIPOLAR | 20 ms…5 s log | 1176 Release; 670 first-stage release; the optical fast stage |
| 4 | Release Slow | UNIPOLAR | 0.1…25 s log | the optical second stage; 670 positions 5 and 6 |
| 5 | Memory | UNIPOLAR | 0…1 | the T4 cell's memory; 0 makes the release single-stage |
| 6 | Knee | UNIPOLAR | 0…36 dB | 160 hard knee at 0; the 1176's ratio-dependent knee; 670's progressive ratio at the top |
| 7 | Detector | TOGGLE | peak / RMS | the 160's RMS against the 1176's peak |
| 8 | RMS Window | UNIPOLAR | 1…100 ms log | the RMS averaging time; inert when Detector is peak |
| 9 | Emphasis | UNIPOLAR | 0…1 | LA-2A R37; the 160's SC-HP; a side-chain HPF generally |
| 10 | Emphasis Freq | UNIPOLAR | 30…2000 Hz log | where R37's corner sits |
| 11 | Topology | TOGGLE | feed-forward / feedback | the 160 against the other three; ships only if N-C4 lands |
| 12 | Makeup | UNIPOLAR | −12…+24 dB | 1176 Output; LA-2A Gain |
| 13 | Mix | UNIPOLAR | 0…1 | none of the four — generalized, and Tier 1's wire invariant needs it |

**Patches** (names describe settings): 0 *Level Ride* (optical, slow, gentle,
low emphasis — the default); 1 *Fast Peak Catch* (fet, 30 µs, 12:1, 80 ms);
2 *Everything At Once* (fet, 20:1, fastest times, deep GR — F3's mode);
3 *Bus Glue* (vca, RMS, 4:1, hard knee, 125 dB/s); 4 *Programme Ride* (varimu,
knee 30 dB, 0.4 ms, 2 s); 5 *Voice Ride* (optical, emphasis high, Limit side of
the curve); 6 *Let The Stick Through* (fet, 20 ms attack, 60 ms release, 8:1);
7 *Parallel Squash* (fet, 20:1, fastest times, Mix 0.4); 8 *Wide Knee Glue*
(vca, RMS, 2:1, knee 24 dB, slow); 9 *Slow Hand* (varimu, the sixth
time-constant pair: program-dependent long release).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/dynamics.py` and `_core.py`.

1. **`reset()` silently reverts the surface.** `_core.Effect.reset()` ends with …  *(argument in full: App. R)*
2. **The four characters are three numbers.** `_CHARACTERS` …  *(argument in full: App. R)*
3. **The node takes the module's rate, not the source's.** `dynamics.py:63` …  *(argument in full: App. R)*
4. **No side-chain filter and no mix on the surface.** Six macros …  *(argument in full: App. R)*
5. **The macro ranges cannot reach two of the four standouts.** `_MACRO_RANGES` …  *(argument in full: App. R)*
6. **`_apply_macro` builds a dict per macro move** (`dynamics.py:74-76`). Off
   the audio path, so not a Tier 1 failure; the rewrite should not inherit it.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Is the two-stage release composable?** N-C1's refutation: two `Dynamics` in
   series, fast then slow — does the composite reach O1's t95/t50 ≥ 8 without a
   node change? **Phase 0 settles it**, before the audioif issue is filed. If it
   does, only the memory (O2) remains an ask.
2. **Vision §10.4 asked whether four characters over one detector are honest.**
   This dossier's answer is **no — and that is why each character has its own
   rows.** Three of the four need something the current detector has not got
   (N-C1, N-C2, N-C4). A character whose traits cannot be met is recorded unmet,
   not quietly widened. **Arthur, at Gate 0**, on the node list.
3. **The dbx numbers are the 160X's.** The original 1976 unit's manual was not
   reached, so V1's 125 dB/s and V2's table are the *family's*. Re-check if an
   original-160 specification is ever reached; the traits stand meanwhile. **The
   implementation session**, opportunistically.
4. **The Fairchild table is now read, not transcribed** — this question is
   answered and the entry is kept only so the change is visible. The audit of
   2026-09-06 reached the manual (S10) and the trait-critic pass of
   2026-09-06/07 re-read the scan itself (App. G.4), so M2 is **high**
   confidence, not medium. What is still open is narrower: the manual gives no
   endpoint for "release time from 10 db of limiting", so M2 measures t63 by
   this dossier's own definition and publishes t90 beside it. **The
   implementation session** may tighten the ±30 % bands once one endpoint is
   shown to fit all six positions.
5. **`Emphasis` and `reset()`.** The node's side-chain filter keeps its memory
   across `reset()` (`audioif_dynamics.c:149-152`), so a class that leaves
   emphasis engaged is not stateless afterwards. Either the rebuild rebuilds the
   node on reset or this becomes a fifth ask. It is a **Tier 1** item, so it
   cannot pass the class gate unresolved. **The implementation session**, at
   Station B.
6. **Tempo-synced release.** It would make `capabilities` `("tempo_sync",)` and
   is a real feature, but no standout has it, so it is deliberately out of this
   seed. **The implementation session** may propose it, with its own trait and
   the declare-if-and-only-if rule.
7. **Is gain smoothing composable, or a fifth ask?** Raised by the trait-critic
   pass, which added three distortion traits (F5 0.5 %, V6 0.2 %, M5 1 %) from
   the three manufacturers' own specification pages. The palette applies its
   gain per sample off an unsmoothed detector, and that is exactly what gives
   B.7's 25.66 % at a 1 ms release — so at fast settings these three rows are
   not obviously reachable. It is **not filed as an ask**, because no
   measurement yet shows the palette cannot reach them: two `Dynamics` in
   series, or a slow-release patch, may be enough, and vision §6's rule is
   compose first. **Phase 0 or the implementation session** measures the
   composition against F5, V6 and M5 before any fifth issue is opened; if it
   fails, the ask is a one-pole on the gain after the gain computer — one state
   variable, two multiplies, no transcendental (Tier 3).
8. **Does `Limiter` share these characters?** **Settled here: no.** `Limiter` is
   a design grade with its own dossier and its own control law; sharing one node
   must not become sharing one surface by accident.

---


## Appendix

### A. How the manufacturer PDFs were read

Both Universal Audio manuals (S1, S2) fetch as PDFs the fetch tool cannot read.
The tool saved them to the session's tool-results directory and they were
extracted locally with `pypdf` 6.16.2 from `audiocomponents/.venv/bin/python`,
following `docs/agent-knowledge/instrument-sources.md` ("a WebFetch summary of a
PDF is not guaranteed to match the PDF's actual text").

S1 uses a shifted font encoding: lowercase letters are plain, uppercase are
encoded as lowercase shifted +37 (`T`→`y`, `A`→`f`, `R`→`w`, `D`→`i`), and
spaces, digits and brackets are shifted +35 (space→`C`, `0`→`S`, `1`→`T`,
`(`→`K`, `)`→`L`). Decoding by that rule recovers the specification page —
"Attack Time Adjustable, from 20 to 800 microseconds"; "Release Time Adjustable,
from 50 milliseconds to 1.1 seconds"; "Input Impedance 600 Ω, bridged T-control
(floating)"; "Gain 45 dB, ± 1 dB"; "Distortion < 0.5% T.H.D. from 50 Hz – 15 kHz
with limiting, at 1.1 seconds release setting" — and the front-panel text quoted
in §1 and §3. The decoder is four lines of Python, recorded here so the next
reader does not conclude the manual is a scan.

The Fairchild 670 datasheet PDF fetched at 184 KB, one page, and
`page.extract_text()` returned the empty string: an image-only scan, which is an
OCR problem and not a missing-library one, and this environment has no OCR
tooling.

### B. Probes run against the palette node, 2026-09-06

CPython, `audiodynamics` from the audioif CPython build in
`audiocomponents/.venv`. These are what the node did, not what the C reads as
though it would do.

**B.1 — release law.** DC step 16000 → 1600 (−6.2 → −26.2 dBFS), COMPRESS,
threshold −30 dB, ratio 4:1, knee 0, attack 1 ms, release 100 ms:

```
   ms  gain_dB   dB/s
    0  -17.847
    5  -17.556   58.3
   10  -17.274   56.4
   20  -16.698   57.5
   40  -15.552   57.3
   80  -13.377   54.4
  160   -9.581   47.5
```

Near-constant while the envelope is far above its destination, then falling —
the envelope is a one-pole in the *linear* domain, so its dB slope is
`8.686·(A_hi−A_lo)/(A·τ)` and flattens as `A` approaches `A_lo`. V1 asks for
±20 % over a 20 dB recovery; this is −19 % by 160 ms and worsening.

**B.2 — attack law.** DC step from silence, LIMIT, ceiling −20 dBFS, attack
1 ms; time to 90 % of final GR:

```
  in −14.0 dBFS  overshoot  6 dB  final GR  −6.00 dB  t90 2.688 ms
  in −10.0 dBFS  overshoot 10 dB  final GR −10.00 dB  t90 2.208 ms
  in  −6.0 dBFS  overshoot 14 dB  final GR −14.00 dB  t90 1.896 ms
  in  −2.0 dBFS  overshoot 18 dB  final GR −18.00 dB  t90 1.667 ms
```

A one-pole detector already gives *some* level dependence — 1.6× over 12 dB.
V2 wants ≥ 3× over 20 dB, from S4's 15/5/3 ms table: the palette's dependence
is the wrong order of magnitude, not absent.

**B.4 — `sidechain_hz` high-passes the detector.** Threshold −30 dB, ratio 8:1,
`sidechain_hz=200`, equal-level sines: 60 Hz → 10.73 dB of GR, 4 kHz →
20.12 dB. The kernel low-passes the source and subtracts it (`:255-262`), so the
option's name describes the internal filter, not the detector's response.

**B.6 — the ratio clamp.** `ratio=0.5` on a −6.3 dBFS DC over a −30 dB threshold
gives 0.000 dB of gain: the kernel clamps ratio to ≥ 1 (`:60`). Upward
compression is not on this palette; no trait here needs it.

**B.7 — the gain is unsmoothed, so fast times distort low notes.** 60 Hz sine,
LIMIT, ceiling −12 dBFS, ~12 dB of GR, attack 0: THD(h2..h10) is 25.66 % at a
1 ms release, 7.53 % at 10 ms, 1.69 % at 60 ms, 0.36 % at 300 ms. S3's account
of the All-Button sound, reproduced on the palette with no node change; F3's
≥ 10 dB THD margin is reachable.

**B.9 — the knee is the standard quadratic.** Threshold −20 dB, ratio 4:1,
static curve (input dB → output dB) at knee 0 and knee 12 dB:

```
  in    −26     −24     −22     −20     −18     −16     −14     −10      −6
  k0  −26.00  −24.00  −22.00  −20.00  −19.50  −19.00  −18.50  −17.50  −16.50
  k12 −26.00  −24.13  −22.50  −21.13  −20.00  −19.13  −18.50  −17.50  −16.50
```

The knee-12 curve's local slope rises from 1 dB/dB at −26 to 0.25 dB/dB at −14:
a progressive ratio over 12 dB. M1 wants that rise spread over about 15 dB of
gain reduction, which a knee of 24–36 dB should give; the implementation session
fixes the number by measurement.

**B.10 — instantaneous attack exists.** `attack_ms=0` makes `ms_to_coef` return
1.0 (`:10-11`); on a step to −2 dBFS against a −20 dBFS ceiling the first sample
after the step is already 18.00 dB down. F1's 20 µs end sits comfortably inside
the node's range.

**B.11 — cost on CPython**, 180 blocks of 256 stereo frames, per stereo frame,
against a bare `RawSample` at 0.038 µs: plain 0.043, `true_peak` 0.047,
`lookahead_ms=5` 0.046, `sidechain_hz=120` 0.051, all three 0.049. A desktop
number, recorded only to show the options are not free and not expensive
relative to each other; the board numbers are Station C's.

### C. Where the Tier 3 budget numbers come from

One stereo block is 256 frames (`audioif_dynamics.h:32`) = 5.33 ms at 48 kHz.
Per frame the kernel calls `logf` once (`audioif_dynamics.c:307`) and `expf`
once (`:310`), plus the branchy gain computer and 2–4 multiply-adds per channel.
Neither ESP32 core has a transcendental instruction; a single-precision `expf`
or `logf` from newlib costs of the order of 100–200 cycles, so 256 frames is
roughly 51 000–102 000 cycles per block. On an S3 at 240 MHz that is
0.21–0.43 ms, **4–8 %** of the 5.33 ms deadline; on a P4 at 400 MHz, **2.5–5 %**.
The stated budgets (S3 ≤ 14 %, P4 ≤ 5 %) leave room for the RMS detector and the
second release stage and still fit several instances in a rack. These are
estimates from instruction counts; Station C replaces them with measurements on
both boards.

### D. What each source gave, in full

**S1 (1176LN manual).** Specification page: attack "Adjustable, from 20 to 800
microseconds"; release "Adjustable, from 50 milliseconds to 1.1 seconds"; input
impedance "600 Ω, bridged T-control (floating)"; output load "600 Ω (floating)";
frequency response "20 Hz to 20 kHz ± 1 dB"; gain "45 dB, ± 1 dB"; distortion
"< 0.5% T.H.D. from 50 Hz – 15 kHz with limiting, at 1.1 seconds release
setting. Output of +22 dBm with no greater than 0.5% T.H.D."; S/N "< 81 dB…over
a bandwidth of 30 Hz to 18 kHz". Front panel: Input "Determines the level of the
signal entering the 1176LN, as well as the threshold"; attack "fastest when the
Attack knob is in its fully clockwise position"; release likewise; ratios "4:1
(moderate compression)", "8:1 (severe compression)", "12:1 (mild limiting)",
"20:1 (hard limiting)"; "Note that higher Ratio settings also set the threshold
higher"; "Unlike many other devices, the 1176LN Attack and Release times get
faster, not slower, as their corresponding knobs are turned up (clockwise)";
"Pressing all four Ratio buttons in simultaneously yields an extreme form of
compression… When the 1176LN is in this 'All-Button' mode, distortion increases
radically due to a lag time on the attack of initial transients and there are
constant changes in the attack and release times, as well as a change in the
bias points"; turning Attack fully counter-clockwise "disables compression
altogether; however, signal continues to pass through the 1176LN circuitry".

**S2 (LA-2A manual).** Specifications: "Gain Reduction: up to 40 dB";
"Distortion: less than 0.35% total harmonics at +10 dBm"; "Response: +/- 0.1 dB,
30 cycles to 15 kilocycles"; "Gain: 40 +/- 1 dB"; "Very fast attack time";
"Release Time: approximately 0.06 seconds for 50% release, 0.5 to 5 seconds for
complete release depending upon the amount of previous reduction". Theory: "the
attack and release of the LA-2A are completely determined by the T4"; "After the
light is removed from the cell, it releases quickly (40-80 milliseconds) to
approximately half of its off resistance. The remainder of its release can take
place over as much as several seconds"; "the release time is slower if the unit
has either been in compression for a while, or the amount of compression is
large. This signal dependent release characteristic is critical to the sound of
the unit"; "The LA-2A is a feed-back style compressor"; Peak Reduction
"controls the gain of the side-chain circuit. The greater the gain of this
circuit, the lower the threshold and the greater the amount of compression";
R37 "controls the amount of high-frequency compression… Increasing the
resistance of this potentiometer by turning it counter clockwise will result in
compression which is increasingly more sensitive to the higher frequencies",
factory-set flat, answering FM pre-emphasis' "17 dB boost at 15 KHz"; the
Limit/Compress switch "changes the characteristics of the compressor IO curve.
When in the Compress position, the curve is more gentle, and presents a low
compression ratio". Component values read from the three schematic figures —
gain reduction: R5 68K, R6 68K, R7 2.7K, R1 100K, HA-100X, .0047 µF; side
chain: R2 100K (Peak Reduction), R30 47K, R31/R32/R36 1K, R33/R35 220K, R34
22K 2W, C8 .03, C9 .02, C10 50 µF, C11 .1, C12 .001, C7D 30 µF, V3 12AX7A, V4
6AQ5A, R37 (LIM RESP), R3 1M (stereo adjust); output: R9/R13 220K, R10 1.5K,
R11/R16 68K, R12/R15/R19 470K, R14 2.7K, R17 10K, R18/R20 1K, R21 100K, C1 .02,
C2/C3 .1, C7C 30 µF. Signal chain per the block diagram: input transformer →
T4 optical attenuator → 12AX7A voltage amplifier → 12BH7 cathode follower →
output transformer, with the side chain 12AX7A → pre-emphasis → 6AQ5
electroluminescent driver.

**S3 (Moore 2012).** "the 1176 is a feedback compressor. This type of design
sees the control side chain 'fed from the [output]'… Consequently the feed-forward
design can react a little quicker than the feedback"; "from analysis of a
transfer function diagram… from an out of print Urei 1176 manual the author
noted that the threshold changes depending on the ratio. The current manual
confirms this observation"; "Looking at Fig. 1 you can see that the knee also
appears to change. At higher ratio/thresholds the knee is harder"; Shanks
quoted: "The 1176 will faithfully compress or limit at the selected ratio for
transients, but the ratio will always increase a bit after the transient";
all-buttons ratio "somewhere between 12:1 and 20:1"; and, on distortion,
low-frequency distortion occurs when the compressor acts "within each cycle
rather than on the overall dynamic envelope of the signal" (S3 quoting Izhaki
2008) and when attack and release are faster "than a fraction of the period of
the sine wave" (S3 quoting Case 2007).

**S4 (dbx 160X/XT service manual).** "Compression Ratio Variable 1:1 - c2:1
thru to —1:1; >60dB Maximum Compression" — the scan's OCR, read as 1:1 to ∞:1
and on through the 160X's negative-ratio INFINITY+ range;
"Threshold Range: −40 dBu to +20 dBu"; "Attack Time: Program-Dependent; 15ms for
10dB, 5ms for 20dB, 3ms for 30dB"; "Release Time: Program-Dependent; 8ms for
1dB, 80ms for 10dB, 400ms for 50dB; 125dB/sec Rate"; "THD <0.2%, Any amount of
compression @ 1kHz"; "true-RMS level detector, wide-range Blackmer
voltage-controlled amplifier (VCA) and feed-forward circuitry".

**S5 (Waves dbx 160 guide).** "In 1976, dbx introduced the dbx 160 compressor.
Using dbx's decilinear VCA, RMS level-detection circuits and feed-forward gain
reduction, this compressor allowed much smoother gain reduction than its
counterparts. The feed-forward gain reduction allowed infinite compression
without excessive distortion or oscillation. It also allowed the compressor to
track the attack and release times of compression based on the signal's
envelope. In addition, the dbx compressor introduced overeasy compression,
which created a soft knee at the start of the compression process" — read
plainly this sentence credits the 160's maker, not a later unit, so it does
**not** support "OverEasy postdates the 160"; what does is S4's own feature list,
"the classic 'Hard Knee' curve popularized by the original dbx 160, 161 and
162". Also "a digital model of a classic feed-forward hard-knee VCA-based
compressor"; the dbx 202 "Black Can" VCA; plug-in ranges
threshold −60…−9 dBFS, compression 1:1 to inf:1 default 4:1, SC-HP "around
90 Hz".

**S6 (Sound On Sound, Bieger 2016).** Time constants, from the article's
"Time-constant Settings" box (attack ms / release s): 1 → 0.2 / 0.3;
2 → 0.2 / 0.8; 3 → 0.4 / 2; 4 → 0.8 / 5; 5 → 0.4 / 2 (peaks), 10 (multiple
peaks); 6 → 0.2 / 0.3 (peaks), 10 (multiple peaks), 25 (programme material).
**One of those twelve cells is wrong.** The audit of 2026-09-06 reached the
manual itself (S10), whose specification page gives the attack as ".2
milliseconds in positions 1, 2, and 6" and ".4 milliseconds in positions 3, 4,
and 5" — so position 4 is 0.4 ms, not 0.8 ms, and the manual's grouping (two
values across six positions) is what S6's box breaks. Two independent
archive.org scans of the manual agree. Every release value in the box matches
the manual exactly. M2 now follows S10. "no fewer than four 6386
dual-triode valves" per channel, "each half of the push/pull stage relies on
four triode elements wired in parallel"; "gain reduction starts with a very low
ratio, between 1:1 and 2:1 for smaller peaks, and gradually increases to a ratio
of up to 20:1 on loud input signals"; on the knee, "an inherent feature of the
variable-mu compression principle is the soft knee of the compression curve" and
an internal trim pot "allows for a broad range from a very smooth transition
between compression and harder limiting, to a more pronounced, harder knee" (the
earlier draft's "gets progressively softer with lower ratios" is not in the
article and is struck); "the side-chain signal is tapped after the gain cell,
something which helps to stabilise the circuit"; "20 valves with 30 systems and
11 transformers"; L-R or M-S on the 670, the 660 mono. *Struck in the audit:* a
sentence calling the input gain "a passive attenuator placed before the main
amplification stage" — no such wording, and no mention of an attenuator, appears
anywhere in the article as re-fetched.

**S7 (DAFx-23, Simionato & Fasciani).** "the LA-2A presents an average attack
time of 10 ms and a multi-stage release. The duration of the first stage is 0.06
seconds, while the second stage of release is controlled by the photocell's
memory, which depends on the brightness and time the light-emitting has been on.
The duration of the second stage ranges from 0.5 to 5 seconds for the complete
release… if the compression is heavy and/or the signal has been above the
threshold for a long time, the LA-2A's release will be slower. Therefore the
attack and release times of the LA-2A are unknown a priori but depend on the
past input signal." Its Table 1, "Selected variable parameters and respective
ranges for the software compressors", lists those numbers — attack [20, 800] µs,
release [0.05, 1.1] s — against **"Fet Compressor"**, one of three *plug-ins*
(Softube's, per the paper's own footnote 3) whose parameters the authors swept.
They are not an 1176 measurement, and nothing in this dossier may cite them as
one. *(Corrected by the audit of 2026-09-06: this sentence still said "lists the
1176 as", contradicting §2 S7 and F1, which the first audit pass had already
fixed.)*

**S8 (DAFx-23, Najnudel et al.).** The photoresistor's internal dynamics are
Shockley–Read–Hall recombination, in which "the ionized defect acts as a 'trap'
for electrons" (or, in their reformulation, the bounded defect traps holes);
free carriers are two populations with separate surface mobilities µ⁺₀ and µ⁻₀,
and the total resistance is `R_LDR(q⁺,q⁻) = R_d(R(q⁺,q⁻)+R_ℓ) /
(R_d+R(q⁺,q⁻)+R_ℓ)` with `R(q⁺,q⁻) = 1/(µ⁺₀q⁺ + µ⁻₀q⁻)`, tending to the dark
resistance R_d with no light and to R_ℓ at maximum light. Two carrier
populations with different mobilities is the mechanism under O1's two stages,
and trap occupancy is the mechanism under O2's memory.

**S10 (Fairchild 670 Instruction Manual, December 1959).** SPECIFICATIONS page,
read from the archive.org full text this run: "ATTACK TIME (adjustable) — .2
milliseconds in positions 1, 2, and 6. / .4 milliseconds in positions 3, 4, and
5."; "RELEASE TIME (from 10 db of limiting) — Position 1: .3 seconds. Position
2: .8 seconds. Position 3: 2 seconds. Position 4: 5 seconds. Position 5:
Automatic function of program material: 2 seconds for individual peaks, 10
seconds for multiple peaks. Position 6: Automatic function of program material:
.3 seconds for individual peaks, 10 seconds for multiple peaks, 25 seconds for
consistently high program level."; "COMPRESSION RATIO — Variable from 1:1 to
1:20 above a predetermined level. Predetermined level factory-adjusted to +2
dbm."; "TUBE COMPLEMENT — 8-6386; 1-6084; 1-5651; 2-12AX7; 2-12BH7; 1-EL34;
4-6973; 1-GZ34"; controls "2 Input Gain Controls… 2 Threshold Controls… 2 Time
Constant Switches — 6 positions each… 2 Metering Switches… Mode Switch…" with no
ratio control anywhere in the list. General description: "Each half of the MODEL
670 uses only a single push-pull stage of audio amplification and an extremely
high control voltage"; "the release time is made adjustable from 0.3 seconds to
25 seconds in six steps. Two of these have release times which are automatic
functions of the program material". The scan reached at
`Fairchild_670_owners_manual` carries a page headed "670 DUAL LIMITER SCHEMATIC"
whose OCR yields adjustment designators (R117/R217 DC THRESHOLD, R142/R242 ZERO,
R313 REG B+ ADJ.) and **no component values** — an image, and there is no OCR
tooling here, which is why the Vari-Mu character stays literature and not
circuit.

### E. Licence and citation audit, 2026-09-06 (first pass)

Every row in §2 was re-fetched independently this run: S1, S2, S5, S7 and S8 by
`curl` + `pypdf` 6.16.2 (all HTTP 200; S1 re-decoded with Appendix A's rule, and
its PDF title metadata reads `1176LN Manual_v3-090908-DC`, confirming the
revision in the header), S3 from its item page after the seed's URL turned out
to be an unusable ellipsis, S4 as the `/stream/…_djvu.txt` page plus the
archive.org metadata API, S6 and S9 as HTML. Every quotation in §1, §3 and
Appendix D was checked against that re-fetched text, and `audioif_dynamics.h:32`,
`.c:178-179`, `:245-253`, `:254`, `:263-269`, `:302-305` and
`upstream-diff.md:661` were re-read with `grep -n`.

What holds, verbatim: S1's attack/release/ratio/threshold paragraphs and its
specification page; S2's release specification, its 40–80 ms cell paragraph, its
memory paragraph, "a feed-back style compressor", R37, and component values on
three schematics; S3's feedback, threshold-and-knee-with-ratio and 12:1–20:1;
S4's attack, release and 125 dB/s lines; S5's 1976 paragraph; S6's six
time-constant pairs, its 6386 count, its 1:1→20:1 and its "tapped after the gain
cell"; S7's and S8's LA-2A and vactrol passages, both CC BY 4.0.

Twelve corrections, each applied where it lands:

1. §1 — the FET-in-a-bridged-T topology is not in S1 (its line is an *input
   impedance* spec) nor in S3 or S9; flagged unsourced.
2. §1 — the dbx hard-knee/∞:1 sentence separated into what S5 says, what S4's
   160X spec line says, and what is the plug-in's control range.
3. §2 S1 — licence restated from the manual's own copyright page.
4. §2 S3 — URL replaced (the draft's contained a literal ellipsis and could not
   be fetched); item page added.
5. §2 S3 — licence restated from the repository cover sheet, including the
   hyperlink condition the draft omitted.
6. §2 S4 — "what it gave" now quotes the OCR as it reads and scopes every number
   to the 160X; licence downgraded to unverified/treated as copyleft on the
   metadata API's empty `rights` and `licenseurl`.
7. §2 S5 — "OverEasy postdates the 160" removed: S5's sentence credits the dbx
   160's maker with introducing OverEasy, and S4 is what actually places Hard
   Knee with the original 160/161/162.
8. §2 S6 — the table is the article's box, not a manual transcription; licence
   quoted from the page footer.
9. §2 S7 — its [20, 800] µs row is a *plug-in's* parameter range ("Fet
   Compressor"), not an 1176 measurement.
10. §2/§3 F1 — S7 struck from F1's sources for the same reason; S1 and S9 carry
    it.
11. §3 V4 — the ∞:1 end re-sourced precisely (160X spec line, plug-in range).
12. §2 "not found" — the Giannoulis failure is a 301 to `qmul.ac.uk/eecs/` that
    the fetch tool will not follow, not a TLS failure; the dbx 160/161/162 item
    re-verified as a factory test procedure; the two thehistoryofrecording.com
    URLs recorded as un-rechecked because they were never written down.

Struck in Appendix D as unfindable in the re-fetched S6: the knee "gets
progressively softer with lower ratios", and the input gain as "a passive
attenuator placed before the main amplification stage".

**Three of this pass's own claims did not survive the second audit** (Appendix
F), and are marked here so nobody reads E as settled: correction 3 restated S1's
licence from the copyright page but copied the year wrong (the page reads
© **2009**); correction 12's account of the Giannoulis failure is not what the
host does; and this pass's closing sentence — "Nothing else in §1–§3 was found
unsourced" — was too strong, since F found three quantitative criteria in §3
with no source behind them. F also reached a source E had recorded as
unreachable, the Fairchild 670 manual, and that manual contradicts one cell of
the S6 table E had passed as holding verbatim.

### F. Licence and citation audit, second pass, 2026-09-06

An independent auditor re-fetched every row of §2 and every URL in the file, from
this machine, without relying on Appendix E's record. Method: `curl` to disk
(HTTP status and byte count recorded per URL), then `pypdf` 6.16.2 from
`audiocomponents/.venv/bin/python` for the seven PDFs, the archive.org
**metadata API** for every archive.org item's `rights`/`licenseurl`, and a
regex-stripped text render for the three HTML pages. S1's shifted font encoding
was handled by *encoding the claimed quotation and searching for it*, which
removes the ambiguity in decoding: the map is +35 for characters 32–56, 93 for
`9`, +37 for 58–90, lowercase unchanged (the first pass's rule missed the `9`
glyph). Every quotation in §1, §3 and Appendix D was checked against the
re-fetched text; `audioif_dynamics.h:32`, `.c:167-171`, `:178-179`, `:307`,
`:310` and `upstream-diff.md:661` were re-read with `grep -n` and all six say
what the dossier says they say.

**Fetch results, all this run:** S1 HTTP 200 (2 457 675 B, 39 pp, PDF title
metadata `1176LN Manual_v3-090908-DC` — the header's revision confirmed);
S2 200 (236 501 B, 21 pp); S3 200 (1 278 039 B, 31 pp) and its item page 200;
S4 200 plus `https://archive.org/metadata/dbx_160X-XT_Service_Manual` 200;
S5 200 (436 297 B, 9 pp); S6 200; S7 200 (8 pp); S8 200 (8 pp); S9 200;
S10 200 on both scans plus both metadata endpoints.

**What holds.** S1's specification page and both knob paragraphs verbatim,
including "Note that higher Ratio settings also set the threshold higher" and
the All-Button paragraph; S2's release specification, its 40–80 ms cell
sentence, its memory paragraph, "The LA-2A is a feed-back style compressor",
R37's "increasingly more sensitive to the higher frequencies" and the schematic
component values; S3's licence cover sheet word for word, its feedback
paragraph, its threshold-and-knee-with-ratio passage and its Shanks quotation;
S4's attack, release, ratio, threshold-range and THD lines, and its Hard-Knee
feature sentence; S5's 1976 paragraph and its "1:1 to inf:1" range; S6's
6386 count, its 1:1→20:1 sentence, its "tapped after the gain cell", its "20
valves with 30 systems and 11 transformers" and its footer copyright; S7's and
S8's passages and both CC BY 4.0 lines; S9's four ratios, both time spans and
its CC BY-SA 4.0 footer.

**Nine corrections, each applied where it lands:**

1. §2 S1 — the copyright year is **2009**, not 2008 ("© 2009 Universal Audio,
   Inc. All rights reserved.", p. ii).
2. §2 S5 — licence downgraded to **unverified, treated as copyleft**. The Waves
   guide prints no copyright, licence or all-rights-reserved line anywhere in
   its nine pages; the only rights statement is that HARMAN's trademarks are
   used with written permission. "Vendor guide, all rights reserved" was an
   assumption, not a reading.
3. §2 — **S10 added**: the Fairchild 670 instruction manual, reached on
   archive.org (two independent scans), which the seed had recorded as
   unreachable. Its licence chain is recorded rather than its uploader's label:
   one item asserts CC BY-NC-ND 4.0, which no uploader can grant over a 1959
   Fairchild document, so the call is unverified/copyleft.
4. §3 M2 — **position 4's attack corrected from 0.8 ms to 0.4 ms.** The manual
   gives two attack values across six positions (0.2 ms in 1, 2, 6; 0.4 ms in
   3, 4, 5); S6's box prints 0.8 ms at position 4 and is wrong there. M2's
   confidence rises from medium to high, and its release figures now carry the
   manual's own qualifier, "from 10 db of limiting".
5. §3 M1, M3, M4 and §1 — re-sourced to S10 where the manual is the primary,
   with the anchor points and thresholds that are this dossier's own marked as
   such.
6. §3 F4 (and M4 and V5, which mirror it) — **the factor of two, and V5's
   ±25 % window, are flagged unsourced.** S3, cited for it, says the opposite in degree: "the feed-forward
   design can react a little quicker than the feedback", and "in real terms any
   delay introduced by the feed-forward design will be almost imperceptible".
   The topology claim is strengthened instead, with S1's own sentence: "Note
   that the 1176LN is a feedback style compressor since the sidechain circuit
   samples the signal level after the gain reduction." That sentence also
   strengthens §5's node ask N-C1 rather than weakening it: the topology
   mismatch it rests on is now attested by the manufacturer, not only by S3.
7. §3 F3 — the 12:1–20:1 range is in **S1** ("The ratio goes to somewhere
   between 12:1 and 20:1"), not only in S3; the row now cites the manual first.
8. §3 Tier 3 — the newlib transcendental cost ("100–200 cycles") that the budget
   percentages rest on is flagged **unsourced**; no datasheet or benchmark for
   it was reached.
9. §2 "not found" — the Giannoulis diagnosis replaced with what the host
   actually does (302 to https, https resets; `www.` 301s to
   `webspace.eecs.qmul.ac.uk`, whose page reads "The owner of this web page
   hasn't added any content, yet."; `https://www.eecs…` fails certificate
   verification). Still not reached, and still cited nowhere.
   Appendix D's S7 entry, which still said the DAFx-23 table "lists the 1176",
   corrected to name the Softube plug-in the paper actually swept.

**Checked and found sound:** every "Reached — 2026-09-06" claim in §2 (all ten
sources answered HTTP 200 to this auditor); the licence text of S2, S3, S4, S6,
S7, S8 and S9 as quoted; the `dbx_160-161-162_Schematic` item, re-read and
confirmed to be a May 1991 "Preliminary Technical Service Manual… INITIAL
FACTORY TEST & ALIGNMENT PROCEDURE" with no specification table (`grep -i` for
attack, release and specification returns nothing); and the arithmetic in O1's
parenthetical single-stage ratios and V3's crest factor for a 10 %-duty pulse
train, which this pass recorded as "re-derived here rather than taken on trust".

> **Both of those re-derivations were wrong, and the trait-critic pass of
> 2026-09-06/07 caught them** (Appendix G.6). 4.32 is the t95/t50 of a decay
> exponential **in dB**, not "in linear gain" — the linear-gain one-pole the
> node actually implements gives 5.61 at 10 dB of GR and 7.69 at 20 dB — and
> 10 dB is the crest-factor difference for a **5 %**-duty train, not the 10 %
> the row named, which computes to 6.99 dB. Neither error was visible to the
> audit because both were checked by restating them, not by evaluating them:
> an arithmetic claim that is verified by being read again has not been
> verified. Both rows are rewritten above and both now carry the value a
> **wrong** build would land on, so the measurement can fail rather than merely
> agree.

### G. Sources re-reached and arithmetic re-run by the trait-critic pass, 2026-09-06/07

Every source below was fetched again in this run, by this pass, and read from
its own text — not from the rows that cited it. Where a fetch tool's summary and
the document's own bytes disagreed, the bytes win and the disagreement is
recorded, per `instrument-sources.md`.

**G.1 — S1, the 1176LN manual** (`https://media.uaudio.com/assetlibrary/1/1/1176ln_manual.pdf`,
HTTP 200, 2.3 MB, 39 pages). WebFetch could not read the PDF; text extracted
locally with `pypdf` 6.16.2, which returns it under a custom font encoding
(spaces as `C`, digits as `S`–`\`, uppercase mapped into the lowercase range),
decoded here before reading. Verbatim, decoded: **specification page** —
"Input Impedance 600 Ω, bridged T-control (floating)"; "Gain 45 dB, ± 1 dB";
"Distortion < 0.5 % T.H.D. from 50 Hz – 15 kHz with limiting, at 1.1 seconds
release setting. Output of +22 dBm with no greater than 0.5 % T.H.D.";
"Attack Time Adjustable, from 20 to 800 microseconds"; "Release Time Adjustable,
from 50 milliseconds to 1.1 seconds". **Knob paragraphs** — "The 1176LN attack
time is adjustable from 20 microseconds to 800 microseconds (both extremely
fast). The attack time is fastest when the Attack knob is in its fully clockwise
position"; the same sentence shape for Release over "50 milliseconds to 1100
milliseconds (1.1 seconds)". **Ratio** — the four buttons "4:1 (moderate
compression)", "8:1 (severe compression)", "12:1 (mild limiting)", "20:1 (hard
limiting)", and "Note that higher Ratio settings also set the threshold higher."
**Topology** — "Note that the 1176LN is a feedback style compressor since the
sidechain circuit samples the signal level after the gain reduction."
**All-Button** — "distortion increases radically due to a lag time on the attack
of initial transients (a phenomenon which might be described as a 'reverse
look-ahead'). The ratio goes to somewhere between 12:1 and 20:1, and the bias
points change all over the circuit, thus changing the attack and release times
as well." The 0.5 % distortion line is new to this pass and is now F5.

**G.2 — S2, the LA-2A manual** (`https://media.uaudio.com/assetlibrary/l/a/la-2a_manual.pdf`,
HTTP 200, 231 KB, 21 pages; `pypdf`, plain text). Verbatim: "Release Time:
approximately 0.06 seconds for 50% release, 0.5 to 5 seconds for complete
release depending upon the amount of previous reduction"; "Very fast attack
time" — **the specification gives no attack figure**; "After the light is
removed from the cell, it releases quickly (40-80 milliseconds) to approximately
half of its off resistance. The remainder of its release can take place over as
much as several seconds."; "The amount of time it takes for the cell to recover
after the light is removed depends on how long light had been shining on it and
how bright the light. In the case of the LA-2A this results in behavior where
the release time is slower if the unit has either been in compression for a
while, or the amount of compression is large."; "the attack and release of the
LA-2A are completely determined by the T4"; "This potentiometer controls the
gain of the side-chain circuit. The greater the gain of this circuit, the lower
the threshold and the greater the amount of compression will be."; "The
Limit/Compress Switch changes the characteristics of the compressor IO curve.
When in the Compress position, the curve is more gentle, and presents a low
compression ratio. A higher compression ratio results when the switch is set to
the Limit position."; "The LA-2A is a feed-back style compressor. This is due to
the fact that the signal that is used to drive the side-chain circuit is
affected by the gain reduced signal."; and R37 — "The audio signal in FM
broadcasting undergoes pre-emphasis and results in a 17 dB boost at 15 KHz …
This potentiometer is factory set for a 'flat' side-chain response (clockwise).
Increasing the resistance of this potentiometer by turning it counter clockwise
will result in compression which is increasingly more sensitive to the higher
frequencies."

**G.3 — S4, the dbx 160X/160XT service manual**
(`https://archive.org/stream/dbx_160X-XT_Service_Manual/160X-XT_Service_Manual_djvu.txt`
via WebFetch, then the same text read directly, 54.8 KB). Verbatim from the
specification page: "Threshold Characteristics Selectable OverEasy™ or Hard
Knee"; "Compression Ratio Variable 1:1 - c2:1 thru to —1:1; >60dB Maximum
Compression"; "Attack Time Program-Dependent; !5ms for 10dB, Sms for 20dB, 3ms
for 30dB"; "Release Time Program-Dependent; 8ms for 1dB, 80ms for 10dB, 400ms
for 50dB; 125dB/sec Rate"; "Distortion THD <0.2%, Any amount of compression @
1kHz". From the body: "True RMS Level Detection — senses the power in the
program in a musical manner"; and the control description that supersedes the
OCR-mangled ratio line — "Rotating this control clockwise increases the amount
of compression from 1:1 (no compression) up to infinity:1 (no increase in output
level, regardless of input level increases above threshold); further clockwise
rotation increases compression into the INFINITY+ region, up to a maximum of
-1:1". The 0.2 % distortion line is new to this pass and is now V6.

**G.4 — S10, the Fairchild 670 manual**
(`https://archive.org/download/fairchild_670-im/fairchild_670-im_djvu.txt`;
WebFetch returned a 302 to `ia801508.us.archive.org`, which was fetched, and the
same text was then read directly, 16.6 KB). **A fetch-summary trap, recorded
because it is the exact failure `instrument-sources.md` warns about:** the
summarising fetch returned position 1's release as "3 seconds", dropping the
leading decimal point that the scan renders as `*`. The raw OCR reads
"*3 seconds." and the manual's own introduction settles it — "the release time
is made adjustable from 0.3 seconds to 25 seconds in six steps". M2's
{0.3, …} stands. Verbatim from the SPECIFICATIONS page: ATTACK TIME "(adjustable)
.2 milliseconds in positions 1, 2, and 6. [.]4 milliseconds in positions 3, 4,
and 5" (the scan renders 4 as `U`); RELEASE TIME "(from 10 db of limiting)"
Position 1 ".3 seconds", 2 ".8 seconds", 3 "2 seconds", 4 "5 seconds", 5
"Automatic function of program material: 2 seconds for individual peaks, 10
seconds for multiple peaks", 6 "Automatic function of program material: .3
seconds for individual peaks, 10 seconds for multiple peaks, 25 seconds for
consistently high program level"; COMPRESSION RATIO "Variable from 1:1 to 1:20
above a predetermined level. Predetermined level factory-adjusted to +2 dbm";
HARMONIC DISTORTION "Less than 1% at any level up to +18 dbm output (no
limiting)" and "Less than 1% at 10 db limiting and +12 dbm output"; TUBE
COMPLEMENT "8-6386; 1-6084; 1-5651; 2-12AX7; 2-12BH7; 1-EL34; 4-6973; 1-GZ34".
The distortion line is new to this pass and is now M5. The manual gives **no
endpoint** for "release time from 10 db of limiting", which is why M2 defines
its own and publishes both t63 and t90.

**G.5 — S7, Simionato & Fasciani, DAFx-23**
(`https://www.dafx.de/paper-archive/2023/DAFx23_paper_10.pdf`, HTTP 200, 987 KB,
8 pages; `pypdf`). Verbatim: "the LA-2A presents an average attack time of 10 ms
and a multi-stage release. The duration of the first stage is 0.06 seconds,
while the second stage of release is controlled by the photocell's memory …
The duration of the second stage ranges from 0.5 to 5 seconds for the complete
release." And its Table 1, confirming the caveat F1 carries: the row is
"Fet Compressor — input [-6, +6] dB, attack time [20, 800] µs, release time
[0.05, 1.1] s", a **plug-in's** parameter range, listed among "software
compressors", not a measurement of an 1176.

**G.6 — the arithmetic, re-run rather than restated.** Evaluated in CPython:

- t95/t50 of a gain reduction decaying **exponentially in dB** is
  ln 20 / ln 2 = **4.3219**, independent of depth.
- t95/t50 of a **one-pole in the linear envelope** — the palette node's law
  (B.1) — depends on depth: **4.65** at 3 dB of GR, **5.61** at 10 dB,
  **6.53** at 15 dB, **7.69** at 20 dB.
- t95/t50 of a ramp **linear in dB** is 0.95 / 0.50 = **1.90**.
- Consequence, and the reason O1 now pins its probe to 10 dB: at 20 dB of GR a
  single-stage linear-envelope release reaches 7.69, inside the old
  disconfirmation of "< 6" and within 4 % of the old bar of "≥ 8". The old row
  could have been passed by the very node §5's N-C1 exists to replace.
- Crest-factor difference between a sine and a bipolar duty-D pulse train **of
  equal peak**: 20·log₁₀(√0.5/√D) — **6.99 dB** at D = 10 %, **10.00 dB** at
  D = 5 %, **3.98 dB** at D = 20 %. The old V3 named 10 % duty and 9–11 dB;
  those are two different probes.
- Square against sine **of equal peak**: 20·log₁₀ √2 = **3.01 dB** — the value a
  peak detector lands on, which V3 now carries as its control.

**G.7 — what the trait-critic pass changed, row by row.** No source claim was
invented; where a number moved, the source or the arithmetic that moved it is
above.

- **F1** — the row asserted 20 µs ±25 % and then set its disconfirmation at
  40 µs: two conditions that cannot both be met at any rate. Worse, 20 µs is
  0.96 of a sample period at 48 kHz, so the ±25 % window is half a sample wide
  and unmeasurable. Restated as a **bound** at the fast end, a ±25 % band at the
  other three ends, and a monotonicity clause; disconfirmation aligned to all
  four. The Tier 1 rate note is rewritten to match, and **no Tier 2 row now
  fails at a lower rate**.
- **F1 vs F4** — they contradicted each other. F1 required the measured 10–90 %
  time to *equal* the nominal attack within ±25 %; F4 required it to be *at
  least twice* the nominal. Both were "true" only because neither said what
  "nominal" meant. F1 now measures macro ends against the manual's spans; F4
  measures a paired build against itself.
- **F2** — "moves up monotonically" could be passed by a 0.01 dB move. Bar is
  now "monotone **and** larger than the curve fit's own residual", with the
  residual reported; knee width given a definition.
- **F3** — the trait required THD ≥ +10 dB and the disconfirmation fired only
  below +3 dB, leaving a 3–10 dB band where the row was neither confirmed nor
  disconfirmed; same gap on the attack lag. Both closed. The two thresholds are
  marked *(own)*; the 12:1–20:1 range is S1's own words.
- **F4 / O5 / V5 / M4** — the factor of two, and V5's mirrored ±25 %, were
  unsourced numbers doing the work of a topology claim. Replaced by a **paired
  build** whose pass condition is a strict ordering across every setting
  measured, which needs no published magnitude and cannot be satisfied by a tie.
  Settings where the control's own time is under two sample periods are excluded
  so the sample rate cannot decide the result.
- **F5, V6, M5** — new, one per character that publishes a distortion figure:
  0.5 % (S1), 0.2 % (S4), 1 % (S10). Each is a manufacturer's own number, each
  is failable, and together they stop "the character sounds like the unit" from
  resting on time constants alone. They also give F3(c) a floor to sit above.
- **O1** — two defects. The disconfirmation fired at t95/t50 < 6 while the trait
  claimed ≥ 8, and neither number was tied to a depth of gain reduction. At
  20 dB of GR a plain one-pole reaches 7.69 (G.6), so the row as written could
  have been passed by the single-stage palette node that §5's N-C1 exists to
  replace — a bar that the thing it rules out can clear. Probe pinned to 10 dB,
  bar and disconfirmation both at 8, and the three single-stage reference values
  corrected (the draft called 4.32 "exponential in linear gain"; it is
  exponential in dB).
- **O2** — trait required ≥ 2×, disconfirmation fired only within 20 %. Aligned,
  and the second comparison given the same factor instead of a bare "exceeds".
- **O3** — "attack fixed near 10 ms" had no tolerance and the toggle clause no
  direction. Both given one, from S2's own Limit/Compress sentence and S7's
  10 ms; S2's silence on an attack figure is now stated in the row.
- **O4** — the 6 dB was presented as sourced; it is not. Marked *(own)*, with
  S2's 17 dB-at-15 kHz broadcast curve given as the reason a maximum setting
  worth having is several dB. "Equal level" made "equal RMS".
- **V1, V2** — same trait-vs-disconfirmation gaps (±20 % against 30 %, ⅓ against
  ½). Closed. V2 restated on S4's three published points, which is stronger than
  the ratio it implied.
- **V3** — the arithmetic was wrong: 9–11 dB is a 5 %-duty figure, and the row
  named a 10 % duty, which is 6.99 dB. Corrected, and each half now carries the
  value a **peak** detector would land on (3.01 dB and 0 dB), so the measurement
  fails visibly rather than agreeing quietly.
- **V4** — re-sourced to S4's control description, which states the ∞:1 end in
  words, rather than to the OCR-mangled specification line; knee width defined;
  the INFINITY+ region explicitly not claimed.
- **M1** — disconfirmation now covers both anchors and the monotonicity, not one
  anchor plus an unrelated condition.
- **M2** — the measurement column read t63 while the trait quoted a manual
  figure with no endpoint defined. The row now states the definition as its own
  and publishes t90 alongside, so the ambiguity is visible instead of buried;
  positions 5 and 6 are identified as the individual-peak figures. §8.4, which
  still said the table was transcribed rather than read, is corrected.
- **M3** — "a train of ten peaks" had no spacing or level, so two runs could
  disagree legitimately. Defined; the source's own implied ratios (5× and 33×)
  recorded so the 3× bar is visibly one with margin.
- **§5, N-C1** — its refutation said a single stage reaches "4.3 at best". The
  node is a one-pole in the linear envelope, which reaches 5.61 at 10 dB and
  7.69 at 20 dB. Corrected; the ask survives, and the reason it survives is now
  stated at a pinned depth rather than at whichever depth the probe happened to
  use.


### H. Palette verification, 2026-09-07

An independent **palette verifier** re-read every claim in §4 and §5 about what
an `audiodynamics` node can and cannot do against the C
(`audioif/src/shared/audioif_dynamics.c`, `audioif_dynamics.h`) and the bindings
(`audioif/src/audiodynamics/Dynamics.c`, `module.c`), by `grep -n`, and re-ran
every behavioural claim on the CPython build of audioif in
`audiocomponents/.venv`. Probes are DC or tone material through
`audiocore.RawSample`, pulled with `audiocore.get_buffer`; gain reduction is
read either from the audio (input known, so `20·log10(out/in)` is the gain, per
sample) or from `Dynamics.gain_reduction_db()` (`Dynamics.c:144-149`, one
reading per 256-frame block).

**What the re-read confirmed.** Every line citation in §4 and §5 is correct as
written: `:10-11` (`ms_to_coef` returning 1.0 for ms ≤ 0), `:60` (the ratio
clamp), `:167-171` (the half-sample estimator), `:178-179` (`DYN_LIMIT`'s gain
computer), `:196-205` (the quadratic knee), `:235` (mono/stereo selection),
`:245-253` (the lookahead delay), `:254` (the detector reading the node's own
input), `:255-262` (the sidechain low-pass-and-subtract), `:263-269`
(`fabsf` and the cross-channel max), `:302-305` (the one attack and one release
coefficient), `:307`/`:310` (the per-frame `logf` and `expf`),
`:310-311` (makeup applied after the gain), `audioif_dynamics.h:32` (256
frames), `upstream-diff.md:661` and `:673` (audiodynamics is not a
CircuitPython port). `Dynamics` exposes exactly eleven options
(`Dynamics.c:20-30`) and one reader, `gain_reduction_db()`; there is no
side-chain input and no detector-source selection.

**Reproduced from Appendix B, unchanged.** B.1's table to three decimals
(−17.847 dB then 58.3 / 56.4 / 57.5 / 57.3 / 54.4 / 47.5 dB/s); B.6 (ratio 0.5
gives 0.000 dB); B.9's two static curves cell for cell; B.10 (18.00 dB down on
the first sample after the step). B.4 was re-run at a different level and
reproduces the *difference* it is cited for — 9.42 dB more GR at 4 kHz than at
60 Hz with `sidechain_hz=200`, against B.4's 9.39 dB — so the high-passed
detector claim stands.

**H.1 — the release into silence is exactly straight in dB.** COMPRESS,
threshold −30 dBFS, ratio 4, knee 0, attack 1 ms, release 100 ms; DC at
−3.31 dBFS for 300 ms, then digital silence; GR read per block.

```
  GR at burst end 19.761 dB
   19 dB remaining @  16.00 ms   65.15 dB/s
   15 dB remaining @  74.67 ms   65.15 dB/s
   10 dB remaining @ 154.67 ms   65.15 dB/s
    5 dB remaining @ 229.33 ms   65.15 dB/s
    2 dB remaining @ 277.33 ms   65.15 dB/s
    1 dB remaining @ 288.00 ms   65.14 dB/s
  max/min across the span 1.0000
```

LIMIT at the same ceiling gives the same result at 86.86 dB/s. Sweeping the
release macro, `release_ms = 52` puts the mean rate over 19 → 1 dB at
**125.00 dB/s**. V1 is met by the node as V1 is written; B.1's flattening is
its probe stepping down to a second level, which is a different measurement.

**H.2 — two `Dynamics` in series reach the optical and Fairchild release
traits.** Fast stage: threshold −20 dBFS, ratio 2.5, knee 0, attack 1 ms,
release 45 ms. Slow stage as noted. Burst then a −45 dBFS floor (low enough that
GR reaches zero, high enough to read the gain out of the audio per sample).

```
  slow = -25 dBFS, ratio 2, attack 2500 ms, release 2200 ms
    10 s burst, drive -9 dBFS   GR0 11.33 dB  t50   48.8 ms  t95 2192.6 ms  t95/t50 44.9
    fast stage alone (control)  GR0  6.62 dB  t50   29.2 ms  t95   56.2 ms  t95/t50  1.9
    slow stage alone (control)  GR0  8.04 dB  t50 2033.1 ms  t95 3987.6 ms  t95/t50  2.0
  length memory, same drive
      200 ms burst              GR0  6.62 dB  t95   56.2 ms
     1000 ms burst              GR0  6.62 dB  t95   56.2 ms
     3000 ms burst              GR0  9.89 dB  t95 1470.8 ms
    10000 ms burst              GR0 11.33 dB  t95 2192.6 ms          -> 39x
  depth memory, 10 s burst (same pair, slow release 2500 ms)
      drive -21.5 dBFS          GR0  1.73 dB  t95 1016.2 ms
      drive  -4.0 dBFS          GR0 15.48 dB  t95 2954.8 ms          -> 2.9x
  program dependence (slow = -38 dBFS, ratio 2, attack 120 ms, release 6000 ms)
    one 10 ms burst             GR0  9.89 dB  t63   53.1 ms
    ten 10 ms bursts @200 ms    GR0 18.07 dB  t63 4020.6 ms          -> 75.7x
    fast stage alone, both      GR0  8.53 dB  t63   46.8 ms          -> 0 %
```

O1 asks t50 40–80 ms, t95 0.5–5 s and t95/t50 ≥ 8; O2 asks ≥ 2× both ways; M3
asks ≥ 3× on patches 5–6 and < 25 % on 1–4. All four bars are cleared by the
composition. The mechanism is the slow stage's own `attack_coef`
(`audioif_dynamics.c:303`): an envelope with a 2.5 s time constant is still
climbing after 200 ms and settled after 10 s, which is a memory of time over
threshold without a new state variable. The cost is the second instance's
`logf`/`expf` pair.

**H.3 — the follower is a peak detector, or an average detector, never RMS.**
LIMIT, ceiling −30 dBFS, knee 0; steady GR read per block; 200 Hz material.

```
  detector setting                        square-sine @ equal RMS   sine-pulse @ equal peak
  attack 0.5 ms / release 50 ms  (peak)          -2.73 dB                  +0.48 dB
  attack = release = 200 ms      (average)       +0.91 dB                 +16.06 dB
  attack = release = 1000 ms     (average)       +0.91 dB                 +15.55 dB
  what a true peak detector reads                 3.01 dB                   0.00 dB
  what a mean-|x| detector reads                  0.91 dB                  16.1  dB
  what V3 requires                             <= 0.50 dB                6.99 +- 1 dB
```

Both available shapes miss both of V3's figures, and the measured values land on
the analytic values for a peak and a mean-|x| detector to two decimals, which is
the check that the probe is measuring what it claims.

**H.4 — a static-matched cascade moves the attack the wrong way.** A cascade of
k stages at ratio `R**(1/k)` and the same threshold reproduces a single stage's
static curve exactly — after k stages the output is `T + (1−s)^k·(L−T)`, so
`(1−s)^k = 1/R` — which makes it a fair paired build against the single stage.
20 dB DC step over a −30 dBFS threshold, 10–90 % of final GR, k = 3:

```
  ratio  attack    1 stage    3 stages
      4  0.10 ms   0.1458 ms  0.1042 ms
      4  0.20 ms   0.2917 ms  0.1667 ms
      4  2.00 ms   2.8958 ms  1.6667 ms
      8  0.20 ms   0.2917 ms  0.1458 ms
     12  0.20 ms   0.2917 ms  0.1250 ms
     20  0.20 ms   0.2917 ms  0.1042 ms
     20  2.00 ms   2.8958 ms  0.9792 ms
```

24 of 24 ratio × attack settings run *faster*, not slower. F4 requires the
feedback build to be strictly slower at every setting, so the cascade is not a
refutation of N-C4 — it is a demonstration that the palette cannot produce the
ordering at all.

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

**Rate note.** The FET character's fastest attack, 20 µs, is 0.96 of a sample
period at 48 kHz, 0.88 at 44.1 kHz and 0.44 at 22.05 kHz — i.e. below what any
of the three rates can resolve. The macro clamps to one sample rather than
refusing, and **F1's fast end is therefore stated as a bound (≤ one sample
period), not as a match to 20 µs**, at every rate; what changes with the rate is
only how coarse that bound is (20.83 µs at 48 kHz, 45.4 µs at 22.05 kHz). Stated
that way F1 holds at all three rates, and **no Tier 2 row here fails at a lower
rate**. The earlier draft asserted 20 µs ±25 % and then named a disconfirmation
of 40 µs, two conditions that cannot both be met at any rate this program
supports; the bound replaces both.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| # | Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|---|
| S1 | Universal Audio, *Model 1176LN Solid-State Limiting Amplifier* manual, rev. v3-090908-DC | Attack/release spans and knob sense; the four ratios; threshold-rises-with-ratio; the All-Button paragraph; "bridged T-control" | "© 2009 Universal Audio, Inc. All rights reserved… No part of this document may be reproduced, in any form, without prior written permission" (p. ii, read this run; the audit of 2026-09-06 corrected the year from 2008) — read as a document (vision §5), nothing reproduced | https://media.uaudio.com/assetlibrary/1/1/1176ln_manual.pdf | 2026-09-06 — PDF fetched; unreadable to the fetch tool, text extracted locally with `pypdf` (Appendix A) |
| S2 | Universal Audio, *Model LA-2A Leveling Amplifier* manual, LA2A-M01 Rev 1.3 | The two-stage release spec and the 40–80 ms first stage; the cell-memory paragraph; feed-back topology; T4 construction; R37; three schematics with component values | "Copyright 2000 Universal Audio, Inc. All rights reserved… No part of this document may be reproduced" — read as a document, values cited as facts | https://media.uaudio.com/assetlibrary/l/a/la-2a_manual.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S3 | Austin Moore, "All Buttons In: An investigation into the use of the 1176 FET compressor in popular music production", *Journal on the Art of Record Production* 6 (2012), ISSN 1754-9892 | Feedback topology, stated and contrasted with feed-forward; threshold *and* knee move with ratio; All-Button "between 12:1 and 20:1"; the low-frequency distortion mechanism | Huddersfield repository cover sheet, read this run: reproducible for "personal research or study, educational or not-for-profit purposes without prior permission or charge", provided the authors/title/bibliographic details are credited, a hyperlink or URL to the metadata page is included, and "the content is not changed in any way" | https://eprints.hud.ac.uk/id/eprint/27391/1/Journal%20on%20the%20Art%20of%20Record%20Production%20%C2%BB%20All%20Buttons%20In_%20An%20investigation%20into%20the%20use%20of%20the%201176%20FET%20compressor%20in%20popular%20music%20production.pdf (from the item page https://eprints.hud.ac.uk/id/eprint/27391/) | 2026-09-06 — PDF fetched, `pypdf` |
| S4 | dbx, *160X / 160XT Service Manual* (full text) | The attack and release specifications quoted in §1 (verbatim, allowing for OCR: "!5ms"=15 ms, "Sms"=5 ms); the ratio line, which OCRs as "Compression Ratio Variable 1:1 - c2:1 thru to —1:1; >60dB Maximum Compression"; "true-RMS level detector, wide-range Blackmer voltage-controlled amplifier (VCA) and feed-forward circuitry" — all of it the **160X/160XT**, not the 1976 160 | Licence unverified — the archive.org metadata API for `dbx_160X-XT_Service_Manual` returns no `licenseurl` and no `rights` field (checked this run); treated as copyleft, read as a document, nothing reproduced | https://archive.org/stream/dbx_160X-XT_Service_Manual/160X-XT_Service_Manual_djvu.txt | 2026-09-06 |
| S5 | Waves, *dbx® 160 Compressor/Limiter User Guide* | The original 160 (1976) as "decilinear VCA, RMS level-detection circuits and feed-forward gain reduction"; times that "track the attack and release times of compression based on the signal's envelope"; the plug-in as a model of "a classic feed-forward **hard-knee** VCA-based compressor". (S5 does *not* place OverEasy after the 160 — its next sentence credits "the dbx compressor" with introducing it; what puts OverEasy after the original is S4, whose feature list calls Hard Knee "the classic 'Hard Knee' curve popularized by the original dbx 160, 161 and 162".) | **Licence unverified — treated as copyleft** (vision §5). No copyright, licence or all-rights-reserved line is printed anywhere in the nine-page PDF; its only rights statement is that HARMAN's trademarks are used "with written permission from HARMAN INTERNATIONAL INDUSTRIES". Read as a document, nothing reproduced | https://assets.wavescdn.com/pdf/plugins/dbx-160.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S6 | Hannes Bieger, "Fairchild 660 & 670", *Sound On Sound*, May 2016 | The six TIME CONSTANT pairs, as printed in the article's "Time-constant Settings" box — the article does not say where its table came from, and the audit of 2026-09-06, reaching the manual itself (S10), found the box **wrong at position 4** (0.8 ms where the manual says 0.4 ms) and right at the other eleven cells, so M2 follows S10 and this row is a cross-check; four paralleled 6386 triodes per push-pull half; the progressive-ratio soft knee 1:1→20:1; side chain "tapped after the gain cell" | "All contents copyright © SOS Publications Group… All rights reserved… reproduction in whole or part… is expressly forbidden" (page footer, read this run); read as a document | https://www.soundonsound.com/reviews/fairchild-660-670 | 2026-09-06 |
| S7 | R. Simionato & S. Fasciani, "Fully Conditioned and Low-Latency Black-Box Modeling of Analog Compression", *Proc. DAFx-23*, Copenhagen | Independent restatement of the LA-2A's dynamics, incl. "an average attack time of 10 ms and a multi-stage release"; **not** an 1176 measurement: its Table 1 ("Selected variable parameters and respective ranges for the software compressors") lists a *plug-in*, "Fet Compressor", at attack [20, 800] µs and release [0.05, 1.1] s | "© 2023 Riccardo Simionato et al. … Creative Commons Attribution 4.0 International License" — permissive, cited | https://www.dafx.de/paper-archive/2023/DAFx23_paper_10.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S8 | J. Najnudel, R. Müller, T. Hélie, D. Roze, "Power-Balanced Dynamic Modeling of Vactrols: Application to a VTL5C3/2", *Proc. DAFx-23* | The mechanism under the optical two-stage release and its memory: Shockley–Read–Hall recombination, two carrier populations, the R_LDR law | "© 2023 Judy Najnudel et al. … Creative Commons Attribution 4.0 International License" — permissive, cited | https://www.dafx.de/paper-archive/2023/DAFx23_paper_50.pdf | 2026-09-06 — PDF fetched, `pypdf` |
| S9 | Wikipedia, "1176 Peak Limiter" | Cross-check only: FET "in a feedback configuration", the four ratios, both time spans, All-Button mode | CC BY-SA 4.0 | https://en.wikipedia.org/wiki/1176_Peak_Limiter | 2026-09-06 |
| S10 | Fairchild Recording Equipment Corporation, *Instruction Manual, Model 670 Stereo Limiter*, A-96039, December 1959 | **The Fairchild primary source, reached by the audit of 2026-09-06 where the first run had recorded the manual as unreachable.** Its SPECIFICATIONS page gives the attack (two values across the six positions), the six release times "from 10 db of limiting", the ratio line "Variable from 1:1 to 1:20 above a predetermined level", a controls list with **no ratio control**, and the tube complement "8-6386" — all quoted in full in Appendix D. **It disagrees with S6 at one cell:** the manual's attack is 0.4 ms at position 4 where S6's box prints 0.8 ms, and two independent scans of the manual agree with each other, so M2 follows the manual | Licence chain, per `instrument-sources.md` ("a repackager's label is an assertion, not a licence"): item `fairchild_670-im` **asserts** `licenseurl` = CC BY-NC-ND 4.0, which no uploader can grant over a 1959 Fairchild document; item `Fairchild_670_owners_manual` carries no `licenseurl` and no `rights` (both checked this run via the metadata API). The manual itself grants nothing, so **licence unverified — treated as copyleft**. Read as a document; specification values cited as facts about the unit, nothing reproduced | https://archive.org/download/fairchild_670-im/fairchild_670-im_djvu.txt (item https://archive.org/details/fairchild_670-im), corroborated by the independent scan https://archive.org/download/Fairchild_670_owners_manual/Fairchild_670_owners_manual_djvu.txt | 2026-09-06 — both full texts fetched (HTTP 200) and the specification page read in each; both scans' OCR renders "4" as "U"/"h" throughout ("10-40 45th Avenue", "14\" panel space"), which is how ".U milliseconds" and "«4, milliseconds" read as 0.4 ms |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| F1 | **Both time macros span the unit's ranges and both get *faster* as the macro rises.** Release 1.1 s ±25 % *(own)* at the macro's minimum, 50 ms ±25 % at its maximum. Attack 800 µs ±25 % (29–48 samples at 48 kHz) at the minimum; at the maximum, 20 µs is **0.96 of a sample period at 48 kHz**, below any rate here, so the fast end is a **bound** — 10–90 % time ≤ one sample period. Every intermediate setting faster than the one below | S1 spec page and both knob paragraphs (G.1); S9 cross-check. **Not** S7, whose identical figures are a plug-in's parameter range (G.5) | high (spans), medium (±25 %) | Any of the four ends outside its band; a fast-end time longer than one sample period; either macro non-monotone or inverted | 10–90 % of the GR trace on a DC step 20 dB over threshold, at both ends and four intermediate settings of each macro, 48 and 44.1 kHz |
| F2 | **Threshold rises with ratio; the knee narrows with it.** With everything else fixed, the fitted knee point rises monotonically across 4:1 → 8:1 → 12:1 → 20:1 by more than the fit residual at every step, and the fitted knee width falls monotonically across the same four | S1 verbatim, "higher Ratio settings also set the threshold higher" (G.1); S3 for the knee. S1 gives **no magnitude**, so the bar is "monotone and above the fit residual" *(own)*, not an invented dB figure | high (direction), medium (the narrowing, which rests on S3 reading a plot) | A knee point that does not move, moves down, or moves by less than the fit residual at any step; a width that widens or is flat | Static curve, 60 levels −60…0 dBFS, per ratio patch; knee point, width and residual per the definitions above |
| F3 | **All-Button is a mode, not a fifth ratio.** On one patch: (a) static slope between **12:1 and 20:1**; (b) GR in the first 2 ms of a 20 dB step at least **3 dB *(own)*** *less* than the 4:1 patch's at the same Attack; (c) THD on a 100 Hz sine at 12 dB of GR at least **10 dB *(own)*** above the 4:1 patch's, whose own ceiling is F5 | S1's All-Button paragraph carries all three, and the range quantitatively — "The ratio goes to somewhere between 12:1 and 20:1" (G.1); S3 quotes the same. S1 gives no number for (b) or (c) | high (the range), medium (the two thresholds) | Slope outside 12:1–20:1; first-2 ms GR within 3 dB of the 4:1 patch's or above it; THD less than 10 dB above the 4:1 patch's | Static curve; GR over the first 2 ms of a 20 dB step, both patches, same Attack; harmonic spectrum of a 100 Hz sine at 12 dB of GR, both patches |
| F4 | **The loop is feedback, and the paired build proves it.** The feedback build's 10–90 % GR time on a 20 dB step is **strictly longer than the feed-forward control's at every setting measured** — six Attack settings × four ratio patches — no tie, no reversal, excluding only settings where the control's own time is under two sample periods and the rate sets the answer. Magnitude recorded, never required; the earlier "at least twice" is withdrawn as a pass condition, unsourced (G.7) | Topology: S1 verbatim, the sidechain "samples the signal level after the gain reduction" (G.1); S3. The strict-ordering criterion is *(own)* and needs no published magnitude to fail | high | Any measured setting where the feedback build ties or beats the control | GR trace on a 20 dB step, six Attack settings × four ratio patches, feedback build against its feed-forward control on the same probe |
| F5 | **Clean everywhere except All-Button.** On every non-All-Button patch, a sine held at 10 dB of GR with Release at its slowest measures THD(h2..h10 re fundamental) ≤ **0.5 %** at 50 Hz, 1 kHz and 15 kHz. Without it, a build that distorts on every patch passes F3 by distorting slightly less at 4:1 | S1 spec page verbatim, "< 0.5 % T.H.D. from 50 Hz – 15 kHz with limiting, at 1.1 seconds release setting" (G.1) — the manufacturer's figure, not ours. **New in the trait-critic pass** | high (the figure), medium (mapping "+22 dBm output" to a dBFS probe, *(own)*: held at −6 dBFS out) | THD above 0.5 % at any of the three frequencies, on any non-All-Button patch, at the slowest release | Harmonic spectrum at 50 Hz, 1 kHz, 15 kHz; GR held at 10 dB; Release at maximum time; on the FET patches |

| # | Trait | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| O1 | **Two-stage release, measured at exactly 10 dB of GR.** After a 10 s tone holding 10 dB of GR stops: t50 **40–80 ms**, t95 **0.5–5 s**, **t95/t50 ≥ 8**. The depth is pinned because the ratio moves with it: at 10 dB a one-pole in the *linear* envelope — what the palette node is (B.1) — gives **5.61**, a GR exponential in dB gives **4.32**, a ramp linear in dB **1.90**; the same one-pole reaches **7.69** at 20 dB, so an unpinned probe lets a single-stage release pass (G.6) | S2's spec line and theory section (G.2); S7 restates both. **Note what each source measures:** the 40–80 ms is the *cell's resistance*, the 0.06 s a "50 % release" with no unit; this row measures GR in dB, which is *(own)* | high | t50 outside 40–80 ms, t95 outside 0.5–5 s, or **t95/t50 < 8** | GR trace after a 10 s tone holding exactly 10 dB of GR stops; t50 and t95 in dB, at 48 and 44.1 kHz |
| O2 | **The slow stage carries memory, both ways the source names it.** Four burst-then-silence traces (200 ms / 10 s × 3 dB / 15 dB): t95 after 10 s is ≥ **2× *(own)*** t95 after 200 ms at the same depth, **and** t95 after 15 dB is ≥ 2× t95 after 3 dB at the same length | S2 verbatim on the cell's recovery depending on "how long light had been shining on it and how bright the light" (G.2); S7; S8 for the mechanism. S2 gives the **direction only**; the 2× is *(own)* | high (direction), medium (factor) | Either comparison below 2×, or either in the wrong direction | Four GR traces as above; t95 per trace |
| O3 | **No time knobs; the amount knob is a threshold; the toggle is the ratio.** (a) Attack and Release are **inert** — sweeping either end to end moves no measured time beyond the repeat spread — and the measured attack sits at **10 ms ±50 % *(own)***; (b) Peak Reduction moves the fitted knee point monotonically while changing the asymptotic slope by ≤ **0.05 dB/dB *(own)*** over its travel; (c) the Limit position's asymptotic slope is **strictly steeper** than Compress at every Peak Reduction setting measured | S2 on the T4 determining both times, on Peak Reduction as side-chain gain, and on the Limit/Compress curve (G.2). S2 gives **no attack number** ("Very fast attack time"); the 10 ms is S7's (G.5), the ±50 % *(own)* | high (a, c), medium (the attack figure) | Either time macro changing a measured time; attack outside 5–15 ms; Peak Reduction moving the slope by more than 0.05 dB/dB; the toggle not changing the slope, or changing it the wrong way at any setting | Static curves at five Peak Reduction settings × both toggle states; attack and release at both ends of both time macros |
| O4 | **Frequency-weighted side chain, flat when the knob is home.** At Emphasis maximum the steady GR on a 10 kHz sine exceeds that on a 100 Hz sine **of equal RMS** by ≥ **6 dB *(own)***; at Emphasis minimum — the factory setting — the two agree within **1 dB *(own)*** | S2 verbatim on R37 being factory-flat and, turned back, giving "compression which is increasingly more sensitive to the higher frequencies", and on the 17 dB-at-15 kHz FM pre-emphasis the control exists to answer (G.2). S2 states **no dB figure for R37 itself** | high (direction, flat default), low (the 6 dB) | No difference at maximum; a difference in the wrong direction; more than 1 dB at minimum | Steady GR on 100 Hz and 10 kHz sines at equal RMS, both ends of Emphasis, threshold fixed |
| O5 | The loop is **feedback**: F4's paired-build ordering, unchanged, on this character's settings | S2 verbatim, "The LA-2A is a feed-back style compressor" (G.2) | high | As F4 | As F4, on the optical default patch |
| V1 | **The release is a straight line in dB.** Over one recovery from **20 dB** of GR to **1 dB**, the instantaneous rate stays within **±20 % *(own)*** of its mean across the span, and at Release macro centre the mean is within ±20 % of **125 dB/s** | S4's spec line, whose three points *are* 125 dB/s (1/0.008, 10/0.08, 50/0.4) — the source's own arithmetic, not a reading of it (G.3); S5 | high | Rate anywhere in the 20 → 1 dB span more than 20 % off the mean, or a mean outside 100–150 dB/s at macro centre | GR trace after a burst holding 20 dB of GR; rate by finite difference at 19, 15, 10, 5, 2 dB remaining. Palette fails today: 58.3 → 47.5 dB/s (B.1) |
| V2 | **Attack strongly level-dependent, on the three published points.** On DC steps 10, 20, 30 dB over threshold the time for GR to first reach the full overshoot is within **±30 % *(own)*** of **15, 5 and 3 ms**; the consequence t(30) ≤ ⅓·t(10) is checked too | S4 verbatim, "!5ms for 10dB, Sms for 20dB, 3ms for 30dB" (OCR: 15, 5; G.3) | high (the figures), medium (±30 %, and reading "attack" as time-to-full-overshoot, which S4 never defines) | Any of the three outside its band, or t(30)/t(10) above ⅓ | GR traces on 10, 20, 30 dB steps at 48 and 44.1 kHz. Palette gives 1.6× over 12 dB (B.2) — wrong order of magnitude, not absent |
| V3 | **RMS, not peak — and both comparison figures are derived, not asserted.** At ratio ∞:1, knee 0, so the GR difference equals the level difference: (a) square and sine of **equal RMS** give GR within **0.5 dB *(own)***, where a **peak** detector differs by 20·log₁₀√2 = **3.01 dB**; (b) a bipolar **10 %-duty** train and a sine of **equal peak** differ by **6.99 ± 1 dB *(tolerance own)*** — 20·log₁₀(√0.5/√0.1) — where a peak detector differs by **0 dB**. *(The earlier "9–11 dB" is a 5 %-duty figure; G.6.)* | S4, "true-RMS level detector … and feed-forward circuitry" (G.3); S5. Both figures derived here from the waveform definitions, each carrying the value a **wrong** detector lands on | high | Square/sine at equal RMS differing by more than 0.5 dB; the pulse/sine pair outside 5.99–7.99 dB — in particular near 0 dB (a peak detector) or near 10 dB (a 5 %-duty probe used by mistake) | Steady GR on sine, square, 10 %-duty bipolar train and one held chord, at matched RMS and again at matched peak, ratio ∞:1, knee 0 |
| V4 | **Hard knee, ratio reaching ∞:1.** At Ratio maximum the static slope above the knee is ≤ **0.05 dB/dB *(own)*** over 20 dB of input, and at Knee zero the fitted width is ≤ **1 dB *(own)*** | S4's control description, reached verbatim this run and better than the OCR-mangled spec line: compression rises "from 1:1 (no compression) up to infinity:1"; plus "Selectable OverEasy™ or Hard Knee" (G.3); S5. S4's INFINITY+ region ("to a maximum of -1:1") is deliberately **not** claimed — the palette clamps ratio ≥ 1 (B.6) and no trait needs it | high | A slope above 0.05 dB/dB anywhere in the 20 dB span, or a fitted knee wider than 1 dB at Knee zero | Static curve, 60 levels, at Ratio maximum and Knee zero |
| V5 | The loop is **feed-forward** — the only one of the four — so F4's ordering **reverses**: the shipped VCA build is the control and a feedback build of identical settings is strictly slower at every setting whose control time exceeds two sample periods | Topology: S4 ("feed-forward circuitry"), S5. Same *(own)* strict-ordering criterion as F4, which retires the earlier mirrored "±25 % of nominal" | high | Any such setting where the pair ties, or where the shipped build is slower | As F4, same probe, opposite expectation |
| V6 | **Clean at any amount of compression.** A 1 kHz sine measures THD ≤ **0.2 %** at 3, 10 and 20 dB of GR, on every VCA patch and at every Release setting — the tightest of the four characters, and what separates the VCA from the FET by measurement rather than adjective | S4 spec page verbatim, "THD <0.2%, Any amount of compression @ 1kHz" (G.3). **New in the trait-critic pass** | high (the figure), medium (mapping the unit's operating level to a dBFS probe, *(own)*: held at −6 dBFS out) | THD above 0.2 % at any of the three depths, at any Release setting | Harmonic spectrum of a 1 kHz sine at 3, 10, 20 dB of GR, swept across Release. The unsmoothed per-sample gain behind B.7's 25.66 % is the mechanism this bounds |
| M1 | **The ratio is a consequence of level, not a setting.** Local slope ≥ **0.5 dB/dB** (no steeper than 2:1) where measured GR is **2 dB**, ≤ **0.05 dB/dB** (at least 20:1) where it is **15 dB**, falling monotonically between | S10's ratio line, "Variable from 1:1 to 1:20 above a predetermined level" (G.4); S6 for where each end sits. Neither ties a slope to a depth of GR, so **the 2 dB and 15 dB anchors are *(own)*** | high (span), medium (anchors) | Slope below 0.5 dB/dB at 2 dB of GR (20:1 arriving too early); above 0.05 dB/dB at 15 dB (never reaching 20:1); a non-monotone stretch wider than one curve step | Static curve, 60 levels; local slope by finite difference against measured GR |
| M2 | **Six fixed time-constant pairs, as six patches.** Attack within ±30 % *(own)* of **{0.2, 0.2, 0.4, 0.4, 0.4, 0.2} ms** — the manual publishes two attack values — and release within ±30 % *(own)* of **{0.3, 0.8, 2, 5, 2, 0.3} s**, the fifth and sixth being the manual's **individual-peak** figures (the multiple-peak ones are M3's). **The release measurement is this dossier's definition, not the manual's:** the manual says "from 10 db of limiting" and names no endpoint, so the kit holds exactly 10 dB, releases, tests **t63** against the table and publishes **t90** beside it, so the endpoint can be re-argued from data | S10's SPECIFICATIONS page, read from the scan directly this run (G.4), where the OCR's "*3 seconds" is settled by the manual's own "adjustable from 0.3 seconds to 25 seconds in six steps". **S6's box is wrong at position 4** and right at the other eleven, so it is a cross-check, not the source | high — read from the manufacturer's manual, in two independent scans | Any pair outside its band; fewer or more than six patches; a t63/t90 pair whose ordering says the release is not monotone | 10–90 % attack and both t63 and t90 release from the step probe, once per patch, at 48 and 44.1 kHz |
| M3 | **Patches 5 and 6 are program-dependent; 1–4 are not.** With "multiple peaks" defined here as **ten 10 ms bursts at 200 ms spacing, each reaching 10 dB of GR**, t63 after the train is ≥ **3× *(own)*** t63 after a single such burst on patches 5 and 6, while 1–4 move **< 25 % *(own)*** between the two probes | S10 verbatim on positions 5 and 6 (G.4); S6's box agrees. The source's figures imply **5×** at position 5 and **33×** at 6, so the 3× bar has margin; the bars and the probe shape are *(own)* — the manual defines neither "individual" nor "multiple" | high (the dependence), medium (thresholds and probe) | Patches 5 or 6 below 3×; any of 1–4 above 25 % | Two GR traces per patch — one burst, then the ten-burst train — same level, same rate |
| M4 | The loop is **feedback**: F4's paired-build ordering, once per patch | S6, "the side-chain signal is tapped after the gain cell". **S10 does not describe the side-chain topology** (G.4), so this is the only topology row of the four resting on a secondary source alone | medium | As F4, on any of the six patches | As F4, once per patch |
| M5 | **Clean at 10 dB of limiting.** A 1 kHz sine held at 10 dB of GR measures THD ≤ **1 %** on every one of the six patches, patch 6's fast 0.3 s release included | S10 spec page verbatim, HARMONIC DISTORTION "Less than 1% at 10 db limiting and +12 dbm output" (G.4). **New in the trait-critic pass** | high (the figure), medium (mapping "+12 dbm output" to a dBFS probe, *(own)*: held at −6 dBFS out) | THD above 1 % on any patch at 10 dB of GR | Harmonic spectrum of a 1 kHz sine at 10 dB of GR, once per patch |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Looked for and not found this run.** *A 1176 schematic with values*, from a
host that resolves: `www.electrosmash.com` does not resolve from this machine,
`geofex.com` resets, `web.archive.org` is blocked for the fetch tool, and the
hobbyist Rev-D analyses came back as search snippets that were never reached —
so none is cited and the class is graded literature. *The original 1976 dbx 160
manual*: the archive.org item `dbx_160-161-162_Schematic` ("DBX: 160 161 162
Schematic") was reached again in the audit and is a "Preliminary Technical
Service Manual… INITIAL FACTORY TEST & ALIGNMENT PROCEDURE" — trim and
calibration steps, designators but no values and no specification table — so the
dbx numbers here are the **160X**'s (§8.3). *The Fairchild 670 manual and
datasheet* on thehistoryofrecording.com: the manual exceeded the fetch tool's
10 MB limit; the datasheet fetched (184 KB, one page) and `extract_text()`
returned the empty string — an image-only scan, and there is no OCR tooling in
this environment. Neither URL was written down at the time, so neither could be
re-checked. **This entry is superseded**: the licence and citation audit of
2026-09-06 reached the manual itself on archive.org (S10), so the six
time-constant pairs no longer rest on S6's box — and reading the manual showed
S6's box wrong at position 4. What is still *not* reached is a Fairchild 670
**schematic with component values**: the `Fairchild_670_owners_manual` scan
contains a page headed "670 DUAL LIMITER SCHEMATIC", but it is an image whose
OCR yields designators (R117, R217, R142, R242, R313) and no values, and this
environment has no OCR tooling. The Vari-Mu character therefore stays at
literature grade. *Giannoulis, Massberg & Reiss, "Digital Dynamic Range Compressor
Design—A Tutorial and Analysis"* (JAES 60(6), 2012) was identified and is
**still not reached**, and the earlier two accounts of why were both wrong. What
the licence and citation audit actually observed on 2026-09-06, probing the host
directly: `http://eecs.qmul.ac.uk/~josh/…` answers **302** to the *same* URL over
https, and that https host then **resets the connection**;
`http://www.eecs.qmul.ac.uk/~josh/…` answers **301 to
`https://webspace.eecs.qmul.ac.uk/josh`** (not to `qmul.ac.uk/eecs/`);
`https://www.eecs.qmul.ac.uk/…` fails certificate verification ("unable to get
local issuer certificate"); and the author's webspace page, which does resolve
(HTTP 200), reads "The owner of this web page hasn't added any content, yet."
The Semantic Scholar landing page returned no content. Nothing from it is cited
here.

*(from §3)*

**Shared definitions, so no row repeats them.** *GR trace* — output over input
in dB, per sample, on the probe the row names. *Attack time* — the 10–90 % rise
of the GR trace after a step; one sample period (20.83 µs at 48 kHz) is that
measurement's floor, so any claim faster than it is stated as a **bound**, never
a match. *Release time* — t63 unless a row says otherwise; t50/t95 are the times
to 50 %/95 % of full recovery **in dB**, used where a source's own wording is a
percentage. *Knee point and width* — fitted on a 60-point static I/O curve, the
width being the input span over which the local slope goes from 0.95 dB/dB to
within 5 % of the asymptotic slope; the fit residual is reported beside every
fitted number. *Paired build* — the same class built twice from identical
settings, differing only in where the detector reads (the input, or the previous
output sample), rendered on one probe; **the comparison fails on an ordering,
never on a magnitude**, so it needs no figure nobody published.

*(from §3)*

Numbers marked ***(own)*** are this dossier's operational thresholds, not
findings; a class gate may move one with a written reason. Everything else is
read from the cited source. Every verbatim quotation behind these rows, and
every derived comparison value in them, is in **Appendix G**, where each source
was re-fetched and re-read on 2026-09-06/07.

*(from §3)*

**Trait count after the trait-critic pass of 2026-09-06/07: 21 Tier 2 rows** —
FET 5, Optical 5, VCA 6, Vari-Mu 5 (18 before the pass; F5, V6 and M5 are new,
each read off a manufacturer specification page reached in this run). The grade is *literature*, so the roadmap's
"at least three, each with a source and a disconfirmation condition" binds, and
this dossier holds each **character** to it separately (vision §10.7): every
character carries at least five and none is carried by another's. Nothing here
is recorded *unmeasured*. What that pass changed, row by row, is in Appendix G.7.

*(from §3)*

Budget as a fraction of one stereo block's deadline (256 frames = 5.33 ms at
48 kHz, `audioif_dynamics.h:32`): **ESP32-P4 ≤ 5 %, ESP32-S3 ≤ 14 %**. Lean
patch expected: **no**. The dominant cost is one `logf`
(`audioif_dynamics.c:307`) and one `expf` (`:310`) per *frame* — 96 000
transcendental calls a second per instance at 48 kHz. The call sites and the
frame count are read from the tree; the arithmetic that turns them into a
percentage is in Appendix C, and the audit of 2026-09-06 flags its one imported
number — "a single-precision `expf` or `logf` from newlib costs of the order of
100–200 cycles" — as **unsourced**: no datasheet, benchmark or measurement for
it was reached this run. The percentages are therefore budgets, not findings,
and Station C replaces them with board measurements. An RMS detector (V3) adds
one multiply-accumulate per channel per frame and no transcendental; a second
release stage with memory (O1, O2, M3) adds one state variable and two
multiplies; and the **gain smoothing** that F5, V6 and M5 require — the palette
applies its gain per sample off an unsmoothed detector, which is what makes
B.7's 25.66 % — is one more one-pole on the gain, one state variable and two
multiplies, no transcendental. None of the three moves the budget, which is
dominated by the two per-frame transcendentals.

*(from §3)*

**Latency: zero, in every character, at every macro setting.** All four
standouts are analogue and none looks ahead; the LA-2A's ~10 ms attack (S7) is
envelope behaviour on the wet path, not delay. **No option on this class adds
latency** — the emphasis filter (O4) is one causal pole, the RMS window (V3) is
a causal average, and lookahead is deliberately not offered here (it belongs to
`Limiter`). `latency_samples` is 0 and the class gate verifies it with the click
test at 48 kHz and 44.1 kHz. `Compressor` is therefore a class a live stompbox
chain can use with no latency budget at all (vision §9a).

*(from §4)*

**Python at construction and on a macro move** computes the character's control
law: threshold-from-ratio (F2) is arithmetic before `node.set(threshold_db=…)`;
the Fairchild's progressive ratio (M1) is a wide `knee_db`, since the kernel's
soft knee is the standard quadratic (`audioif_dynamics.c:196-205`) whose local
slope rises smoothly from 1:1 to the set ratio across the knee width — measured
in Appendix B.9; the six Fairchild patches and the emphasis corner are Python
numbers. **C per sample** is the follower and gain computer
(`audioif_dynamics.c:236-323`).

*(from §4)*

**Reachable today, measured this run (Appendix B).** Attack from 0 µs
(`ms_to_coef` returns 1.0 for ms ≤ 0, `:10-11`, giving 18 dB in one sample,
B.10) upward, so F1's whole span fits. The quadratic knee covers F2's narrowing
and M1's progression (B.9). `sidechain_hz` gives a **high-passed** detector —
the kernel low-passes the source and subtracts it (`:255-262`), measuring
20.1 dB of GR at 4 kHz against 10.7 dB at 60 Hz for the same level (B.4) — so
O4 and a de-esser side chain both fit. Hard knee and ∞:1 (V4) come from
`knee_db=0` with a large ratio, or `DYN_LIMIT`. F3's distortion mechanism is
already present: the gain is applied per sample off an unsmoothed detector, so a
60 Hz tone at 12 dB of GR measures 25.7 % THD at a 1 ms release and 0.36 % at
300 ms (B.7) — S3's account of the All-Button sound, reproduced without a node
change.

*(from §4)*

**A two-stage release *with memory* is composable — run and measured this
run (Appendix H.2).** Two `Dynamics` in series apply their gains in sequence,
so their dB reductions add, and the *slow* stage's attack coefficient is the
memory: a stage whose envelope takes seconds to rise contributes nothing after
a short burst and its full share after a long one. A fast stage (threshold
−20 dBFS, ratio 2.5, knee 0, attack 1 ms, release 45 ms) into a slow one
(−25 dBFS, ratio 2, attack 2500 ms, release 2200 ms), 10 s burst then silence:
**t50 48.8 ms, t95 2192.6 ms, t95/t50 = 44.9** where O1 asks 40–80 ms,
0.5–5 s and ≥ 8. The same pair moves t95 from **56.2 ms after a 200 ms burst
to 2192.6 ms after a 10 s one (39×)** and, with the slow release at 2500 ms,
from **1016 ms at 1.7 dB of depth to 2955 ms at 15.5 dB (2.9×)**, where O2 asks
≥ 2× both ways. Retimed to the
train (slow stage −38 dBFS, attack 120 ms, release 6000 ms), M3's t63 moves
from **53.1 ms after one 10 ms burst to 4020.6 ms after ten at 200 ms spacing
(75.7×)** where M3 asks ≥ 3×, while the fast stage alone — the patches M3 says
are *not* program-dependent — reads 46.8 ms on both probes, a 0 % move under
M3's 25 % bar. What the composition costs is the second instance: the
per-frame `logf` (`:307`) and `expf` (`:310`) twice.

*(from §4)*

**One earlier "not reachable" is withdrawn on measurement.** B.1's trace is
reproduced exactly this run (H.1), but it steps the input *down to a second
level*, not to silence, and the flattening it shows is the envelope
approaching its new destination — not the release law. V1's own probe is a
**burst**, and into silence `state->envelope += release_coef * (level −
envelope)` with `level = 0` (`:302-305`) is exactly geometric, so the dB trace
is exactly straight: measured **65.15 dB/s at every one of 19, 15, 10, 5, 2
and 1 dB remaining, max/min = 1.0000** (H.1). Landing the mean on the dbx's
125 dB/s is then a Python mapping — `release_ms = 52` gives 125.00 dB/s at
ratio 4. V1 is reachable today; only a release rate that stays constant while
the signal falls to a *non-silent* floor is not, and no trait here asks for
that.

*(from §4)*

**Not reachable, with the reading or the measurement that shows it.** A peak
detector, `fabsf` of the sample (`:263-269`), so V3 has no RMS — and the
follower's other available shape is no better: with attack = release the
detector averages, and measured (H.3) it reads square-minus-sine at equal RMS
as **+0.91 dB** (a mean-|x| detector) against V3's 0.5 dB, and sine-minus-pulse
at equal peak as **+16.06 dB** against V3's 6.99 ± 1; with fast times it reads
**−2.73 dB** and **+0.48 dB**, a peak detector's 3.01 and 0. A detector fed
from the input (`:254`), so F4/O5/M4's feedback loop does not exist — and the
one composition that looks like feedback runs the ordering **backwards**: a
static-matched cascade of k stages at ratio R^(1/k), same threshold, reaches
10–90 % *faster* than the single stage it matches at every one of 24
ratio × attack settings (0.1667 ms against 0.2917 ms at 4:1 with a 0.2 ms
attack; H.4).
And there is **no per-block hook** anywhere in the contract — roadmap §3 lists
the live surface and nothing in it is called per block;
`docs/audio-component-api.md` names no callback (`:65-117` is the whole live
surface, `:209-236` the whole of timing and transport) — so a Python-side
control law has nowhere to run between blocks either. That is why these two
are node questions rather than composition questions.

*(from §5)*

**Verdict after the palette verification of 2026-09-07** — every claim in §4 and
§5 about what a node can and cannot do re-read against
`audioif/src/shared/audioif_dynamics.c` and `audioif/src/audiodynamics/`, and
every behavioural claim re-probed on the CPython build of audioif (Appendix H):
**N-C1 and N-C3 are refuted by the palette; N-C2 and N-C4 stand.** Two issues,
not four.

*(from §5)*

- **N-C1 — a second release stage with memory.** Unblocks **O1, O2, M3**.
  *Palette instead:* one `release_coef` (`audioif_dynamics.c:304`), a single
  stage whose t95/t50 at O1's pinned depth of 10 dB is **5.61** — a one-pole in
  the *linear* envelope, which is what the node is (B.1), not the 4.3 of an
  exponential in dB that the first draft quoted here — where O1 requires ≥ 8;
  and nothing that lengthens with time over threshold, which O2 requires to move
  t95 by ≥ 2×. The correction matters to the ask rather than just to the
  arithmetic: the same one-pole reaches **7.69** at 20 dB of GR, so an O1 probe
  that did not pin the depth could have been passed by the very node this ask
  says cannot reach it (App. G.6).
  *Shape:* `release2_ms` and `memory` — fast and slow envelope pools, the slow
  one's coefficient scaled by an integrator of time-over-threshold, which is the
  carrier-trap behaviour S8 models physically.
  **REFUTED BY PALETTE** (palette verification, 2026-09-07): the refutation this
  seed left open was run, and it succeeded. Two `Dynamics` in series reach all
  three traits — O1's **t95/t50 = 44.9** against ≥ 8 (t50 48.8 ms, t95 2.19 s,
  both inside their bands); O2's length memory **39×** and depth memory **2.9×**
  against ≥ 2×; M3's train-versus-burst t63 **75.7×** against ≥ 3×, with the
  fast stage alone flat at **0 %** for the patches M3 says are not
  program-dependent (Appendix H.2). The memory does not need a new state
  variable: the slow stage's own `attack_coef` is the integrator of
  time-over-threshold, because an envelope with a 2.5 s time constant is still
  climbing after 200 ms and settled after 10 s. What the ask would buy is the
  second instance's cost — the per-frame `logf` (`audioif_dynamics.c:307`) and
  `expf` (`:310`) twice — which is a Tier 3 argument, not an unreachable trait,
  and the vision's compose-first rule (§6) asks for a node only when a fixed
  trait is shown unreachable. If the implementation session wants the option
  back it must come as a **cost** ask with the board measurement behind it, not
  as this one.

*(from §5)*

- **N-C2 — an RMS detector option.** Unblocks **V3**. *Palette instead:* `fabsf`
  per channel, max across channels (`:263-269`) — measured on the node,
  square-minus-sine at equal RMS reads **−2.73 dB** (a peak detector's
  −3.01 dB) and sine-minus-pulse at equal peak **+0.48 dB** (a peak detector's
  0.00 dB), where V3 asks for ≤ 0.5 dB and 6.99 ± 1 dB (H.3).
  *Shape:* `detector="rms"` plus `rms_ms`, a one-pole on the squared signal with
  the square root folded into the existing `gain_to_db` (`:307`), so no extra
  transcendental. **ASK STANDS** (palette verification, 2026-09-07). *Refutation
  run and failed:* the follower's second available shape is an average detector
  — set `attack_ms == release_ms` and the one-pole becomes mean-|x| — and it
  misses V3 in both directions, measured: square-minus-sine at equal RMS
  **+0.91 dB** where V3 allows 0.5, sine-minus-pulse at equal peak **+16.06 dB**
  where V3 wants 6.99 ± 1 (Appendix H.3). And the signal cannot be squared
  *outside* the node and fed back in: `audiomath.Multiply` does take two streams
  (`src/audiomath/Multiply.c:15-17`, `source` and `modulator`), but `Dynamics`
  exposes exactly eleven options (`src/audiodynamics/Dynamics.c:20-30`) and none
  of them is a side-chain input, the detector is hard-wired to the node's own
  input (`audioif_dynamics.c:254`), and no node on the palette divides — so the
  gain a `Dynamics` computes from a squared stream cannot be taken off it and
  applied to the dry path.

*(from §5)*

- **N-C3 — a constant-rate release.** Unblocks **V1**. *Palette instead:* the
  rate falls 58.3 → 47.5 dB/s across one recovery (B.1) because the envelope is
  a one-pole in the linear domain; V1 allows ±20 % and this is −19 % by 160 ms
  and worsening. *Shape:* `release_mode="linear_db"` — subtract a fixed dB per
  sample from the *gain* rather than scaling the envelope; one branch in the
  existing loop.
  **REFUTED BY PALETTE** (palette verification, 2026-09-07): scaling the
  envelope geometrically *is* subtracting a fixed dB per sample, whenever the
  envelope's destination is far below where it starts. V1's own measurement is a
  **burst**, and after a burst `level` is zero, so `envelope +=
  release_coef * (0 − envelope)` (`audioif_dynamics.c:302-305`) multiplies the
  envelope by a constant every sample — exactly a straight line in dB. Measured
  on the node: **65.15 dB/s at 19, 15, 10, 5, 2 and 1 dB remaining, max/min =
  1.0000**, where V1 allows ±20 %; and `release_ms = 52` puts the mean at
  **125.00 dB/s** at ratio 4, which is V1's second clause (Appendix H.1). B.1's
  58.3 → 47.5 dB/s is reproduced exactly this run and is not a counter-example:
  that probe steps the input *down to a second level* rather than ending, so
  what flattens is the envelope arriving at its new destination. The distinction
  is worth carrying into Station B — a release rate that stays constant while
  the signal falls to a non-silent floor is a different claim, and no trait in
  §3 makes it — but as V1 is written the palette meets it and there is no ask.

*(from §5)*

- **N-C4 — a feedback detector.** Unblocks **F4, O5, M4**, three of the four
  characters. *Palette instead:* the detector reads `source` (`:254`), the
  pre-gain signal, so every character is feed-forward and three standouts' attack
  shape is wrong by construction. *Shape:* `topology="feedback"`, the detector
  reading the previous output sample — two lines, one state variable, no cost.
  **ASK STANDS** (palette verification, 2026-09-07).
  *Refutation run and failed:* the one composition
  that resembles a feedback loop is an unrolled one — a cascade of k `Dynamics`
  at ratio R^(1/k) and the same threshold, which reproduces the single stage's
  static curve exactly (`(1−s)^k = 1/R`), so it is a fair paired build. It moves
  the attack time the **wrong way**: three stages reach 10–90 % of full GR
  faster than the one stage they match, at every one of 24 ratio × attack
  settings (4:1 at 0.2 ms attack: **0.1667 ms against 0.2917 ms**; 20:1 at
  2 ms: 0.9792 ms against 2.8958 ms), where F4 requires the feedback build to be
  strictly *slower* (Appendix H.4). Python cannot close the loop either: the
  detector reads the node's own input (`audioif_dynamics.c:254`), the contract
  has no per-block hook, and feedback is a one-sample loop.

*(from §7)*

1. **`reset()` silently reverts the surface.** `_core.Effect.reset()` ends with
   `self.program_change(0)` (`_core.py:374`), so resetting a compressor a host
   has set up discards every macro and reloads patch 0. Reset must clear state,
   not settings.

*(from §7)*

2. **The four characters are three numbers.** `_CHARACTERS`
   (`dynamics.py:20-25`) differs only in attack, release and knee — `"optical"`
   is `(15.0, 400.0, 12.0)`, a single-stage release with no memory. The class
   docstring (`dynamics.py:3-7`) says so plainly. Nothing expresses the detector
   law, the ratio law or the topology, which is where all four circuits differ.

*(from §7)*

3. **The node takes the module's rate, not the source's.** `dynamics.py:63`
   passes `_core.SAMPLE_RATE` and `_core.channel_count()`, globals set by
   `configure()`, rather than what the factory was handed — the pre-contract
   shape roadmap §3 retires.

*(from §7)*

4. **No side-chain filter and no mix on the surface.** Six macros
   (`dynamics.py:37-38`) and no way to high-pass the detector, though the node
   has had `sidechain_hz` since phase 11
   (`audioif/docs/upstream-diff.md:837`) — O4 is unreachable from the surface
   even though the palette can do it.

*(from §7)*

5. **The macro ranges cannot reach two of the four standouts.** `_MACRO_RANGES`
   (`dynamics.py:47-48`) gives Ratio `(1.0, 20.0, "log")`, so ∞:1 is
   unreachable and V4 fails from the surface alone; and Attack
   `(0.1, 100.0, "log")`, so the 1176's fastest 20 µs (0.02 ms) is a fifth of
   the way below the knob's floor and F1 fails from the surface alone — even
   though the node reaches both (B.10, and `audioif_dynamics.c:60`). A range is
   a claim about the circuit, and these two are the wrong claim.
