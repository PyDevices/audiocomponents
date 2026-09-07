# Effects Dossier — `CabinetSim` (a 4×12 with Celestion V30s; a 1×12 combo)

**Class:** `lib/audioeffects/drive.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Drive, roadmap Phase 4
**Standout:** vision §4.2's pair — **confirmed, and pinned.** "A 4×12 with
Celestion V30s" becomes the manufacturer's own published Vintage 30 response
(S1) inside the box and mic Aiken measured (S3); "a 1×12 combo" was
under-specified, and this seed pins it to a G12M Greenback-class driver in an
open-backed box, because that is the combo driver whose response the
manufacturer publishes (S2) and whose enclosure type the literature describes
(S4). Two **characters**, not two classes.
**Grade:** literature — published measurements, no schematic and no circuit.
**Portability tier:** **stock** — a proposed change from today's **audioif**.
The response is a designed filter cascade, and `audiofilters.Filter` takes a
serial `synthio.Biquad` list (probed to twelve stages), which delivers it at
**zero latency** instead of the convolver's 256 frames. See §4.
**Capabilities:** `()` — nothing here is tempo-related (D10).
**Status:** seed (Phase 0), written 2026-09-06

## 1. The object, in one paragraph

A guitar cabinet has no nonlinearity, no LFO and no control law — it is a
transfer function, and three things make it. **The driver**: a paper cone on a
1.75 in voice coil with a free-air resonance of 75 Hz, rated 70–5000 Hz (V30)
or 75–5000 Hz (G12M), whose published on-baffle response (S1, S2, traced in
Appendix A) rises from about −16 dB at 40 Hz to a broad plateau from 200 Hz to
1.6 kHz, then breaks up into **two peaks around 2.2 and 3.2 kHz with a dip
between them**, then falls off a cliff above 5 kHz — 18 to 20 dB in the two
thirds of an octave to 8 kHz — and then **stops falling**, wandering between
18 and 28 dB below the midband all the way to 20 kHz without resuming the
cliff's slope. **The box**: a sealed 4×12 adds a second-order high-pass at the
box-loaded resonance ("12 dB/octave", S4), while
an open-backed combo lets the rear radiation cancel the front — "the forward-
and rearward-generated sounds are out of phase with each other", giving "a
loss of bass and … comb filtering, i.e., peaks and dips in the response
power". S4 states that for drivers *without* an enclosure and for open-baffled
(dipole) speakers, and ties the two to guitar practice only through one
sentence — a dipole baffle is "similar to older open-back cabinet designs";
the transfer to a 1×12 combo is ours, which is why T5b's confidence is medium.
**The microphone and where it sits**: Aiken's close-miked measurement of a
late-'70s Marshall 4×12 with G12M25s — SM57 "on the lower left hand speaker in
the center of the cone, at a 45 degree angle towards the side" — shows the sum
(S3, traced in Appendix A): within 3 dB of its maximum from about 115 Hz to
about 230 Hz, more than 20 dB down by 60 Hz (−21.6 dB) and more than 40 by
40 Hz, ±6 dB of comb structure with real notches through 1.2–5 kHz, and 33 dB
down by 8 kHz. What a rebuild follows is that shape. The panel this class
generalizes is not a pedal's but a cabinet's chosen parameters: which driver,
which box, and where the microphone is.

## 2. Sources and license calls

Every source reached in this run; the traced curves are Appendix A, quotations
Appendix D.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. Celestion, Vintage 30 datasheet (PDF) — the manufacturer's own | Fs 75 Hz, range 70–5000 Hz, 100 dB, 60 W, ceramic … (App. S1) | manufacturer datasheet: no terms line on the … (App. S1) | https://celestion.com/productpdf.php?id=888 | yes — **but the host 403s a plain fetch**: celestion.com sits behind Cloudflare and returns HTTP 403 to `curl`'s default User-Agent and to WebFetch; it serves the PDF to a browser User-Agent with an `Accept-Language` header. WebFetch, given the PDF, reports it cannot read the document (checked). Fetched with `curl` under those headers; the response plot — one 886×367 `DCTDecode` JPEG object — pulled out of the PDF and read |
| S2. Celestion, G12M Greenback datasheet (PDF) | Fs 75 Hz, range 75–5000 Hz, 98 dB, 25 W … (App. S2) | as S1 (same site-wide terms) | https://celestion.com/productpdf.php?id=899 | yes (same route, same 403-without-browser-headers wall) |
| S3. Randall Aiken, "Frequency Response of a Marshall 4x12 Cabinet" … (App. S3) | the only *cabinet-plus-microphone* measurement … (App. S3) | "Copyright © 1999 … (App. S3) | https://www.aikenamps.com/index.php/frequency-response-of-a-marshall-4x12-cabinet and its plot https://www.aikenamps.com/images/Images/Marshall4x12response_2.gif | yes |
| S4. Wikipedia, "Loudspeaker enclosure" | the sealed box's 12 dB/octave (stated in the article's … (App. S4) | CC BY-SA 4.0, read from the page footer | https://en.wikipedia.org/wiki/Loudspeaker_enclosure | yes |
| S5. Celestion, G12M Greenback product page | the same specifications as S2, independently | manufacturer page … (App. S5) | https://celestion.com/product/g12m-greenback/ | yes |
| S6. The palette, probed and fitted under … (App. S6) | §4's cascade fit and stage-count probe … (App. S6) | MIT (this organization) | `audioif/src/shared/audioif_convolve.h`, `audiofilters` | yes (local) |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

Two **characters**: `4x12 stack` (S1's driver, sealed box, close mic) and
`1x12 combo` (S2's driver, open back). Both carry T1–T4; the low end (T5)
differs and each carries its own row.

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Relative levels are re 1 kHz. Curve readings are traced from the published
plots, ±1.5 dB (Appendix A).

| # | Char. | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|---|
| T1 | both | **A cliff above 5 kHz:** the response falls at least 15 dB between 5 kHz and 8 kHz — steeper than 22 dB/octave (15 dB over log₂(8/5) = 0.678 oct), and steeper than two cascaded second-order low-passes can give. | S1 (−4.0 → −22.4 dB = 18.4) … (App. T1) | high | A fall under 15 dB across 5–8 kHz, i.e. a 24 dB/octave design or gentler | Swept-sine magnitude … (App. T1) |
| T2 | both | **And then a shelf, not a hole:** from 8 kHz to 16 kHz the response falls by **no more than 12 dB** from its 8 kHz value, per character; it does not keep falling at the cliff's slope (which, at the 27–29 dB/octave the 5–8 kHz fall measures, would be 27 dB or more over that octave). | S1 (−22.4 → −22.7 … (App. T2) | high | More than 12 dB of fall from 8 to 16 kHz — which every cascade of low-passes gives, and which the current class gives by 23 dB (§7) | The same sweep |
| T3 | both | **Two break-up peaks with a dip between:** the magnitude has two local maxima between 1.8 and 3.6 kHz, each at least 3 dB above the 1 kHz level, separated by a local minimum at least 2 dB below the lower peak. | S1 (+4.5 at 2.2 k, +1.6 at 2.8 k … (App. T3) | high | Fewer than two local maxima in the band (one peaking bell gives one, which is what the current class gives), either peak under 3 dB above the 1 kHz level, or a dip less than 2 dB below the lower peak | Local extrema of the same sweep … (App. T3) |
| T4 | both | **Nothing under 70 Hz:** the response at 40 Hz is at least 12 dB below the 1 kHz level, and at 20 Hz at least 20 dB below. | S1 (−15.7 at 40 Hz, −23.1 at 22 Hz) … (App. T4) | high | Less than 12 dB down at 40 Hz — the current class's shipped `4x12 Stack` is only 6.0 dB down (§7) — or less than 20 dB down at 20 Hz | The same sweep |
| T5a | `4x12 stack` | **Sealed and close-miked:** on a third-octave-smoothed sweep, within 3 dB of maximum from 115 ± 15 Hz to 230 ± 25 Hz, at least 20 dB down at 60 Hz, and the 200 Hz–1 kHz span *falls* by 3–6 dB rather than rising. | S3, re-traced by the critic pass from the … (App. T5a) | medium — one … (App. T5a) | A lower −3 dB point outside 100–130 Hz or an upper one outside 205–255 Hz; under 20 dB down at 60 Hz; or a 200 Hz–1 kHz change outside a 3–6 dB **fall** | The same sweep … (App. T5a) |
| T5b | `1x12 combo` | **Open-backed:** at least **3 dB** more level at 100 Hz relative to 1 kHz than `4x12 stack` has, and a cancellation notch of at least 3 dB somewhere between 100 and 300 Hz. | S2 vs S1: −2.6 vs −6.4 dB at 100 Hz … (App. T5b) | medium — the 3.8 dB … (App. T5b) | Under 3 dB of difference at 100 Hz between the two characters, or no ≥3 dB notch anywhere in 100–300 Hz on the combo character | The same sweep, both characters … (App. T5b) |

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's deadline: **ESP32-P4 0.05**,
**ESP32-S3 0.12** for the proposed 8-biquad cascade (16 biquad passes per
stereo block-sample). Lean patch expected: **yes** on the S3 — a five-section
variant that drops one break-up peak and one shelf stage, which costs T3.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One `audiofilters.Filter` carrying a serial `synthio.Biquad` cascade.** The
list form is already used in the library (`eq.py:185`, four stages for
`LadderFilter`), and probed here it accepts 4, 5, 6, 8, 10, 12, 16, 24 and 32
serial stages under CPython, all building and rendering (App. B). Eight sections reach the whole shape: a second-order
high-pass at the box corner, one low-mid peaking section, three peaking
sections for the two break-up peaks and the dip between them, and **two
high-shelf sections with negative gain** — which is what makes T2 possible,
because a shelf falls to a floor and stops, where a low-pass falls forever.

**Mono:** the cascade is per-channel and a mono source gets the mono form of
the same response; the class is not stereo by definition, and its optional
two-mic blend (§6) sums to the same response in mono.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None — and the palette verification of 2026-09-06 confirms it rather than
taking §4's word.** Every trait is reachable on stock CircuitPython nodes: the
seven-section fit was built and swept on `audiofilters.Filter` itself and holds
T1, T2 and T4 with margin (§4); `synthio.FilterMode.HIGH_SHELF` exists and a
negative-gain shelf floors rather than falling — one shelf at 8 kHz, A =
10^(−18/40), measures −0.04 dB at 100 Hz, −9.00 at 8 kHz, −17.60 at 16 kHz and
**−17.98 at 20 kHz**, which is what makes T2 possible and a low-pass cascade
impossible; and the stage list is not a constraint — 4, 5, 6, 8, 10, 12, 16, 24
and **32** serial stages all build and render under CPython, against the eight
§4 needs.

Two things this class *depends on* other decisions for, both already open
elsewhere and neither an ask of its own:

- **audioif#23, the fixed-point biquad's DC hold.** The class ends in …  *(argument in full: App. R)*
- **The stage cap on the target ports.** Twelve stages were probed under …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Eight macros against a ceiling of sixteen. Every one is a cabinet-building
choice, which is the panel this class actually has.

| # | Label | Mode | Range | Generalises |
|---|---|---|---|---|
| 0 | Character | TOGGLE | `4x12 stack` / `1x12 combo` | The two referents of vision §4.2 |
| 1 | Low Cut | UNIPOLAR | 55 … 140 Hz, log | The box-loaded corner (S4's sealed box; S3's ~90 Hz) |
| 2 | Body | UNIPOLAR | −6 … +6 dB at the low-mid section | The 100–250 Hz bump a close-miked box makes (S3) |
| 3 | Break-up | UNIPOLAR | 1.8 … 3.6 kHz, log — moves both peaks and the dip together | Where the cone stops behaving (S1, S2) |
| 4 | Bite | UNIPOLAR | 0 … +8 dB on the two break-up peaks | How hard the break-up region sits up |
| 5 | Top | UNIPOLAR | 4.5 … 7 kHz, log — where the cliff starts | The 5 kHz cliff (S1, S2, S3) |
| 6 | Air | UNIPOLAR | −30 … −12 dB shelf floor above the cliff | T2's shelf: how much of the 8–20 kHz band survives |
| 7 | Mix | UNIPOLAR | 0 … 1 | — |

**Patches** (names describe settings, never products): 0 `Sealed Four By
Twelve` (character `4x12 stack`, Low Cut 90 Hz, Break-up 2.6 kHz, Bite +5,
Top 5.2 kHz, Air −22 — the S1/S3 shape); 1 `Open-Backed Twelve` (character
`1x12 combo`, Low Cut 70 Hz, Body +3, Break-up 2.9 kHz, Top 5.4 kHz, Air −20 —
the S2/S4 shape); 2 `Off-Axis Close Mic` (Bite +1, Top 4.7 kHz — the cone-edge
position, darker); 3 `Cone Centre` (Bite +7, Top 6 kHz); 4 `Dark Practice Box`
(Low Cut 120 Hz, Top 4.5 kHz, Air −30); 5 `Bright Small Box` (Low Cut 140 Hz,
Bite +6, Air −12); 6 `Bass-Heavy Room` (Low Cut 55 Hz, Body +6); 7 `Lean`
(the five-section Tier 3 variant, for the S3 budget).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/drive.py`.

1. **It pays 5.3 ms and ~25 KB for a filter's response.** The class designs an …  *(argument in full: App. R)*
2. **The reported latency is wrong.** The convolver lags 256 frames …  *(argument in full: App. R)*
3. **The top end falls forever.** Two cascaded second-order low-passes …  *(argument in full: App. R)*
4. **The low end is far too hot:** the same patch is only −6.0 dB at 40 Hz
   against S1's −15.7 and S3's much steeper cabinet roll-off, and is *up*
   +3.5 dB at 100 Hz (T4).
5. **One presence bell cannot make two peaks** (`drive.py:378`) where both
   published curves show two with a dip between (T3).
6. **The macro ranges are loosely tied to anything measured** — presence …  *(argument in full: App. R)*

**And one thing that is *not* a defect, checked rather than assumed:** the
1024-tap truncation is fine — all three shipped patches capture ≥99.9986 % of
the impulse's energy and agree within 0.2 dB from 40 Hz to 15 kHz (Appendix C).
The problem is the convolution, not its length.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Where the microphone sits should probably be a macro, and is not one
   here.** S3's ±6 dB of comb structure through 1–5 kHz is a mic-position
   artefact, and modelling it needs a short delay-and-sum, which would put the
   class back on `audioroute.Splitter` and the **audioif** tier. The seed
   leaves it out and keeps zero latency and the stock tier. *Settled by:* the
   implementation session, with T5a as the arbiter.
2. **T5's confidence is medium on one measurement.** A second published
   cabinet-with-microphone response — from any source with a readable plot —
   would raise it. *Settled by:* whoever finds one; nothing blocks on it.
3. **Which Gate 0 answer the biquad gets** (audioif#23). This seed's §5 states
   both branches; the answer belongs in this file when it lands. *Settled by:*
   Gate 0.
4. **Does the eight-stage cascade build on the P4 and the S3?** Probed under
   CPython only. *Settled by:* the implementation session's three-interpreter
   smoke run, before the Tier 3 numbers are believed.

---


## Appendix

### A. The published curves, traced

The response plots inside S1's and S2's datasheet PDFs, and S3's GIF, are
converted to numbers here rather than read by eye: the plot frame is located by
its own gridlines, the curve's coloured pixels are sampled column by column
inside the frame, and pixel rows are mapped to the printed axes (Celestion: 50
to 110 dB against 20 Hz to 20 kHz). Readings are ±1.5 dB. **The S3 block below
is the audit's trace, not the seed's**: the readings the seed first printed for
S3 were eyeballed, and the audit's trace moved them by up to 9 dB where the
curve is steep (§2). The two Celestion tables were traced, and the audit's
independent trace reproduced them. Both Celestion sheets
label the vertical axis "(dB) Sound pressure" on the V30 and "(dB) Impedance"
on the G12M — the latter is a mislabel on the manufacturer's own sheet: the
scale, the shape and the sensitivity figure are all SPL.

Relative to 1 kHz:

| f (Hz) | V30 (S1) | G12M (S2) |
|---|---|---|
| 20 | −24.0 | −29.8 |
| 40 | −15.7 | −16.1 |
| 63 | −9.9 | −7.2 |
| 100 | −6.4 | −2.6 |
| 200 | −2.8 | −0.8 |
| 500 | −0.8 | 0.0 |
| 1000 | 0.0 | 0.0 |
| 1600 | 0.0 | −2.4 |
| 2200 | **+4.6** | **+7.0** |
| 2800 | +1.6 | +2.8 |
| 3150 | **+4.2** | **+7.5** |
| 4000 | +1.6 | +6.2 |
| 5000 | −4.0 | +1.0 |
| 6300 | −15.7 | −9.6 |
| 8000 | −22.4 | −18.9 |
| 10000 | −20.6 | −18.5 |
| 12500 | −25.7 | −23.2 |
| 16000 | −22.6 | −28.4 |
| 20000 | −25.7 | −24.2 |

Absolute figures: V30 100.9 dB at 1 kHz, peak 105.4 at 2.2 kHz; G12M 98.1 at
1 kHz, peak 105.6 at 3.15 kHz. Both are the bare driver on the manufacturer's
own baffle; neither is a cabinet.

**Audit, 2026-09-06.** Both datasheet PDFs were re-fetched (behind the
User-Agent wall noted in §2) and their response plots re-extracted — in each
sheet the plot is the one `DCTDecode` object, 886×367, among eight images — and
re-traced independently. The axis labels are as described: "(dB) Sound
pressure" on the V30, "(dB) Impedance" on the G12M, both 50–110 dB against
20 Hz–20 kHz. **All 19 points in the table above reproduced**, 18 of them to
0.0 dB and the G12M's 20 kHz reading to 0.4 dB. The absolute figures are the
values *at* the named frequency rather than the curve's true local maximum,
which sits 0.4 dB (V30, 2.26 kHz) and 1.2 dB (G12M, 3.31 kHz) higher — inside
the stated ±1.5 dB, but not a peak-finder's answer.

**S3, traced by the audit** (dB relative to its own maximum, which the trace
puts at ≈ 218 Hz with a 120–200 Hz plateau within 2 dB of it). Calibration read
off the plot's own axes: 0 dB at the frame's top border, −100 dB at the bottom,
and the decade gridlines landing on 20, 30, 40, 50, 60, 70, 80, 90, 100 Hz,
which is what pins the horizontal scale.

| f (Hz) | dB re max | | f (Hz) | dB re max |
|---|---|---|---|---|
| 20 | −45.9 | | 1000 | −6.6 |
| 40 | −41.7 | | 1100 | −10.8 (notch) |
| 60 | −21.6 | | 1500 | −15.9 |
| 80 | −17.7 | | 2000 | −13.1 |
| 90 | −13.4 | | 3000 | −11.7 |
| 100 | −9.2 | | 4000 | −5.7 |
| 115 | −2.9 | | 5000 | −13.1 |
| 150 | −1.2 | | 6000 | −21.0 |
| 200 | −1.8 | | 7000 | −27.2 |
| 250 | −3.9 | | 8000 | −33.3 |
| 400 | −6.3 | | 10000 | −36.0 |
| 800 | −5.3 | | 12000 | −59.3 |
| 900 | −14.0 (notch) | | 15000 | −48.8 |

−3 dB points at 115 Hz and 232 Hz; through 1.2–5 kHz the curve runs between
−4.1 and −16.5 dB, which is the ±6 dB of comb structure §1 describes. Below
40 Hz and above 10 kHz the trace is at the analyzer's floor and is not read as
response. **The seed's first readings for S3 were eyeballed and are replaced by
this table** — they had 100 Hz at −0.5 dB (it is −9.2), 5 kHz at −5 (it is
−13.1) and 10 kHz at −45 (it is −36). Setup, verbatim: "late 70's slant
Marshall 4x12 cabinet" with "original Celestion G12M25 'cream-back' speakers",
"Shure SM57 on the lower left hand speaker in the center of the cone, at a 45
degree angle towards the side", "Hewlett-Packard 3580A spectrum analyzer".
Drive level and distance are not stated, which is one reason T5a's confidence
is medium.

### B. Palette probes

- `audiofilters.Filter(filter=[...])` built and rendered with 4, 5, 6, 8, 10
  and 12 serial `synthio.Biquad` stages under
  `audiocomponents/.venv/bin/python`; all six built and returned a buffer. The
  four-stage form is already shipped (`eq.py:185`). Re-run by the audit
  (2026-09-06): all six reproduce, and 16 stages build and render as well, so
  the CPython ceiling is not at twelve. Re-run again by the palette
  verification the same day, which added **24 and 32** — both build and render
  a full buffer, so there is no ceiling near the eight §4 needs. The board
  question in §5 is untouched by that.
- `audioconvolve` latency and cost read from
  `audioif/src/shared/audioif_convolve.h:21-22` and `:51`, and
  `audioif/docs/upstream-diff.md:1348-1383`.

### C. The cascade fit, and the truncation check

**Fit.** Seven sections — two identical second-order high-passes, three peaking
sections, two negative-gain high shelves — fitted by simulated annealing to the
38 traced V30 points, minimising rms dB error after normalising both to 1 kHz.
Result: **1.18 dB rms**. Coefficient set: high-pass 40 Hz Q 0.40 (×2); peaking
170 Hz Q 0.30 −8.4 dB; peaking 1.32 kHz Q 1.62 −5.8 dB; peaking 3.70 kHz Q 2.51
−1.2 dB; high shelf 5.98 kHz Q 0.61 −21.8 dB; high shelf 5.41 kHz Q 2.14
−8.3 dB. Largest residuals: −2.4 dB at 20 Hz, +2.1 at 40 Hz, −2.2 at 10 kHz.
The eight-section variant (a fourth peaking section) reaches 1.23 dB rms and
places its peaks at 2.21 kHz (+3.95, Q 4.4) and 3.27 kHz (+1.96, Q 2.8) with a
−2.7 dB dip at 1.29 kHz — worse by rms, better by T3, which is the point.

These coefficients are a demonstration that the shape is reachable, not the
shipping design: the rebuild fits its own, per character, with the macro
parametrisation of §6 as the free variables.

**Truncation, checked rather than assumed.** Evaluating the current class's own
five-section design over 32768 taps and comparing the first 1024 against the
exact response: `4x12 Stack` captures 99.9986 % of the impulse's energy,
`1x12 Combo` 99.9999 %, `Studio Cabinet` 99.9998 %, and the truncated response
is within 0.2 dB of exact from 40 Hz to 15 kHz for all three. **The 1024-tap
window is not a defect** — §7 says so, and this is why.

**Planted faults, so the measurements can fail.** T1: replace the two shelves
with a single 24 dB/octave low-pass; the 5–8 kHz fall must read under 15 dB and
the check must go red. T2: swap the shelves for low-passes; the 8–16 kHz test
must go red — and the control, the shelf build, must pass. T3: delete the dip
section; the two-maxima test must go red. T4: move the high-pass to 40 Hz; the
40 Hz check must go red. T5b: build both characters from the same coefficients;
the two-character comparison must go red. And the one that matters most:
**feed every measurement a build whose cascade failed to construct** — an
all-zero response reads as "well below the 1 kHz level" at 40 Hz and passes T4,
which is the *absence-reads-as-agreement* shape
`agent-knowledge/workspace-craft.md` names. Every sweep therefore carries an
absolute check that the 1 kHz level is within 1 dB of unity before any relative
reading is believed.

### D. Source quotations, verbatim

**S1**: "Frequency range 70-5000Hz" · "Resonance frequency Fs 75Hz" ·
"Sensitivity 100dB" · "Power Rating 60W" · "Voice coil diameter 44mm / 1.75in".
**S2**: "Frequency range 75-5000Hz" · "Resonance frequency Fs 75Hz" ·
"Sensitivity 98dB" · "Power Rating 25W".
**S3**: "late 70's slant Marshall 4x12 cabinet" · "original Celestion G12M25
'cream-back' speakers" · "Shure SM57 on the lower left hand speaker in the
center of the cone, at a 45 degree angle towards the side" ·
"Hewlett-Packard 3580A spectrum analyzer" · "Copyright © 1999, Randall Aiken.
May not be reproduced in any form without written approval from Aiken
Amplification."
**S4**: sealed enclosures roll off at "12 dB/octave" below the cutoff; for an
unenclosed driver "the forward- and rearward-generated sounds are out of phase
with each other", giving "a loss of bass and in comb filtering, i.e., peaks and
dips in the response power". The article gives no formula relating the
box-loaded resonance to the driver's free-air Fs, which is why T5a's 90 Hz
comes from S3's measurement and not from an alignment calculation.

### F. Trait critic pass — 2026-09-06

All three response plots were fetched again in this pass and traced again by
the critic, independently of Appendix A's numbers and of the audit's.

**Reachability, this run.** `https://celestion.com/productpdf.php?id=888` (V30)
and `?id=899` (G12M) both return HTTP 200 to `curl` under a browser
User-Agent with `Accept-Language` — the 403 wall §2 describes is still there
for a default agent. The plot in each is the single 886×367 `DCTDecode` object.
`https://www.aikenamps.com/images/Images/Marshall4x12response_2.gif` returns
HTTP 200, 14 KB.

**Calibration, from each plot's own gridlines** (not from the axis captions):
Celestion — decade gridlines at columns 240 (100 Hz), 493 (1 kHz), 745
(10 kHz), so 252.5 px/decade; frame rows 30 and 332 against the printed
50–110 dB scale. The check that it is right: the traced absolute level at
1 kHz is **100.9 dB** for the V30 and **98.1 dB** for the G12M, against the
sheets' own printed sensitivities of 100 dB and 98 dB. Aiken — decade lines at
columns 104, 249, 394, 539 (145 px/decade, 10 Hz to 10 kHz), frame rows 160
(0 dB) and 486 (−100 dB); the curve is the one pixel value distinct from the
grid.

**Traced, re 1 kHz:**

| f | V30 (S1) | G12M (S2) | | f | V30 | G12M |
|---|---|---|---|---|---|---|
| 22 Hz | −23.1 | −28.0 | | 3.15 k | +4.3 | +7.8 |
| 40 | −15.7 | −16.1 | | 4 k | +1.6 | +6.2 |
| 63 | −10.0 | −7.2 | | 5 k | −4.0 | +1.0 |
| 100 | −6.4 | −2.6 | | 6.3 k | −16.0 | −10.0 |
| 200 | −2.8 | −0.8 | | 8 k | −22.4 | −18.9 |
| 500 | −0.8 | 0.0 | | 10 k | −21.1 | −18.5 |
| 1.6 k | 0.0 | −2.1 | | 12.5 k | −26.2 | −23.0 |
| 2.2 k | +4.5 | +7.0 | | 16 k | −22.7 | −28.4 |
| 2.8 k | +1.6 | +2.8 | | | | |

Appendix A's table reproduces within 0.5 dB at every point. The 20 Hz column
falls on the plots' left frame edge and cannot be read cleanly; 22 Hz is read
instead, and both drivers are already 23 and 28 dB down there.

**Aiken (S3), re its own maximum** (≈218 Hz): 20 Hz −46.6, 40 −42.6, 60 −22.2,
80 −18.1, 100 −9.7, 115 −3.2, 150 −0.6, 200 −1.8, 250 −4.0, 400 −5.8, 800
−4.4, 1 k −6.1 (the local peak at ≈1016 Hz), 1.1 k −11.7, 1.5 k −15.0, 2 k
−12.9, 3 k −10.4, 4 k −5.8, 5 k −11.8, 6 k −17.8, 7 k −25.3, 8 k −34.5, 10 k
−36.5, 12 k −56.9, 15 k −47.5. Appendix A's audited trace reproduces within
about 1 dB over most of the band and within 3 dB where the comb is steepest.
**The finding that changed a measurement:** between 950 Hz and 1080 Hz the raw
curve runs −14, −6, −12 dB — three decibels of swing in sixty hertz. A trait
that reads a single frequency there is measuring where a notch happens to land,
not the cabinet, so T5a now specifies third-octave smoothing as part of the
measurement.

**Rows rewritten, and why.**

- **T2 asked for something its own source fails.** The trait said the 8–16 kHz
  span stays within 8 dB; the G12M's own published curve falls 9.5 dB
  (−18.9 → −28.4), confirmed in this pass's trace. The bar is now the 12 dB the
  disconfirmation column already named — cleared by S1 (0.3 dB) and S2 (9.5 dB),
  and still failed by a low-pass cascade, which is what the row exists to catch.
- **T5b's 4 dB bar missed by 0.2 dB.** Its own evidence is a 3.8 dB difference
  between the two drivers' published curves; the bar is now 3 dB, and the row
  says plainly that the 100–300 Hz notch band and its 3 dB depth are our design
  choice, not a reading from S4.
- **T3, T4 and T5a disconfirmed on less than they claimed.** T3 claimed three
  things (two maxima, each ≥3 dB up, a ≥2 dB dip) and disconfirmed on one; T4's
  20 Hz clause had no disconfirmation at all; T5a's did not cover the 60 Hz
  clause or a 200 Hz–1 kHz fall that is too *large*. All three now disconfirm on
  the exact complement of the claim.
- **T1** gains the critic's own numbers for all three sources and states the
  22 dB/octave arithmetic that its 15 dB bar implies.

**Six Tier 2 rows after the pass (T1–T4, T5a, T5b), unchanged in count.** No row
was dropped and none needed the *unmeasured* mark. Both characters keep their
own row — `4x12 stack` T5a, `1x12 combo` T5b — on top of the four they share.

### E. Audit record — license and citation pass, 2026-09-06

Every URL in §2 was re-fetched by an independent auditor and every quotation in
Appendix D was located in the fetched text. Findings:

- **The Celestion licence call holds and is verified, not assumed.**
  `https://celestion.com/website-terms-of-use/` reads, under "How you may use
  material on our site": "We are the owner or the licensee of all intellectual
  property rights in our site … All such rights are reserved. Except as
  otherwise expressly provided for in the Terms of Use, no part of the site,
  including … any text, graphics … may be copied, reproduced, republished …
  without our express prior written consent." Verified all-rights-reserved.
  S5's footer reads "© Copyright Celestion 2026".
- **S1's and S2's spec figures reproduce** off the re-fetched sheets (V30
  70–5000 Hz / Fs 75 Hz / 100 dB / 60 W / 44 mm coil / ceramic; G12M
  75–5000 Hz / Fs 75 Hz / 98 dB / 25 W), and S5 states the G12M figures
  independently.
- **The two Celestion curves were re-traced independently** from the extracted
  JPEGs, with the frame found from the plot's own gridlines. Every one of the
  19 points in Appendix A's table reproduced: 18 of 19 to 0.0 dB and the
  G12M's 20 kHz reading to 0.4 dB. The axis labels are as described — "(dB)
  Sound pressure" on the V30, "(dB) Impedance" on the G12M, both 50–110 dB
  against 20 Hz–20 kHz — so the G12M sheet's mislabel is confirmed.
- **S3's setup sentences and its copyright notice reproduce verbatim**, and
  the plot GIF returns HTTP 200.
- **Correction — S3's readings did not reproduce, and are replaced.** The
  numbers an earlier draft printed for S3 are not a pixel trace: re-traced
  against the GIF's own axis labels (0 dB at the top border, −100 dB at the
  bottom, decade gridlines landing on 20/30/…/90/100 Hz), they are wrong by up
  to 9 dB where the curve is steep — 100 Hz reads −9.2 dB not −0.5, 5 kHz
  −13.1 not −5, 6 kHz −21.0 not −12, 10 kHz −36.0 not −45. Appendix A now
  carries the trace; §1, T1 and T5a are corrected to what it shows. **No trait
  is lost:** T1's 5→8 kHz fall is 20.2 dB against a bar of 15, T4's 40 Hz
  figure is −41.7 dB, and T5a's 200 Hz–1 kHz fall is 4.8 dB inside its 3–6 dB
  band. What moved is T5a's flat span, from "90 Hz to 250 Hz" to "115 Hz to
  230 Hz", and its disconfirmation threshold with it.
- **Two traits ask for slightly more than their own source gives**, both
  flagged in the Tier 2 rows rather than quietly widened. **T2** asks the
  8–16 kHz span to stay within 8 dB of the 8 kHz value; S1's V30 spans 0.2 dB
  there, but S2's G12M spans 9.5 dB (−18.9 → −28.4), so the G12M's own
  published curve fails the trait its own row cites. **T5b** asks for at least
  4 dB more level at 100 Hz than the stack character; the two drivers' curves
  differ by 3.8 dB. Neither number is a licence question and neither is the
  audit's to re-cut — both go to whoever freezes the set.
- **One source recorded as dead is alive** — next paragraph.

### G. Palette verification pass — 2026-09-06

Run by the palette verifier for the bitcrusher–exciter–cabinet unit, under
`audiocomponents/.venv/bin/python`, against the C in `audioif/src/`. §5 asks for
no node, so the job here was to try to break that claim rather than to price a
node.

**The seven-section fit, rendered on the node itself.** Appendix C's
coefficients built as `synthio.Biquad`s inside one `audiofilters.Filter` —
`HIGH_PASS` 40 Hz Q 0.40 (×2), `PEAKING_EQ` 170 Hz Q 0.30 A = 10^(−8.4/40),
`PEAKING_EQ` 1.32 kHz Q 1.62 A = 10^(−5.8/40), `PEAKING_EQ` 3.70 kHz Q 2.51
A = 10^(−1.2/40), `HIGH_SHELF` 5.98 kHz Q 0.61 A = 10^(−21.8/40), `HIGH_SHELF`
5.41 kHz Q 2.14 A = 10^(−8.3/40) — swept with 48 000-frame sines at 20000 peak,
24 000 frames of settling discarded, coherent DFT at the probe frequency, all
re 1 kHz:

| f | dB | | f | dB |
|---|---|---|---|---|
| 20 | −26.40 | | 3150 | +3.29 |
| 40 | **−13.91** | | 4000 | +2.18 |
| 63 | −9.25 | | 5000 | **−4.58** |
| 100 | −6.63 | | 6300 | −16.45 |
| 200 | −4.25 | | 8000 | **−21.63** |
| 500 | −0.33 | | 10000 | −22.69 |
| 1000 | 0.00 | | 12500 | −23.66 |
| 1600 | +0.15 | | 16000 | **−24.33** |
| 2200 | +2.99 | | 20000 | −24.57 |
| 2800 | +3.47 | | | |

Against the trait bars: T1's 5→8 kHz fall **17.06 dB** (≥15 ✓), T2's 8→16 kHz
fall **2.70 dB** (≤12 ✓), T4 **−13.91 dB** at 40 Hz (≥12 ✓) and **−26.40 dB**
at 20 Hz (≥20 ✓). T3 fails on seven sections — 2.2 k / 2.8 k / 3.15 k read
+2.99 / +3.47 / +3.29, one broad maximum, no dip — which is what §4's eighth
section is for and is worth having on record as the control that must fail.
Appendix C's own predictions (−4.7 at 5 k, −21.7 to −24.4 across 8–16 k, −13.9
at 40 Hz) land within 0.1 dB of the rendered node, so the fit was not an
artefact of the design maths.

**Negative-gain high shelf, alone.** `HIGH_SHELF` 8 kHz Q 0.7071
A = 10^(−18/40), re input: 100 Hz −0.04, 500 Hz +0.01, 1 kHz −0.01, 2 kHz
−0.09, 4 kHz −1.33, 6 kHz −4.77, 8 kHz −9.00, 10 kHz −12.68, 12 kHz −15.32,
16 kHz −17.60, **20 kHz −17.98**. It floors. That is the whole of T2's
mechanism, and it is in a CircuitPython-ported node.

**Cascade depth.** 4, 5, 6, 8, 10, 12, 16, 24 and 32 serial `synthio.Biquad`
stages each built and rendered 2048 frames under CPython.

**The `A` trap.** `A = 0` → digital silence at every frequency. `A = −18`
(decibels passed where the linear amplitude belongs) → a constant 28521-peak
output with the input frequency 25–62 dB down. See §4.

**Not re-run here:** the traced curves of Appendix A, the truncation check of
Appendix C, and every source fetch in §2.

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

**Rate-honest note, and the one trait a low rate breaks.** **T2 cannot hold at
22.05 kHz**: its shelf lives from 8 kHz to 20 kHz and there is no band above
11 kHz to put it in. At 22.05 kHz the class states T2 as *not applicable*,
holds T1 and T3–T5, and clamps every corner below Nyquist. **audioif#23 reaches
this class**: the proposed build ends in `audiofilters.Filter`, whose
fixed-point biquad holds DC at low W0, and the cabinet's high-pass sits near
70–90 Hz. Gate 0's single answer for the EQ family governs here, and this seed
records which one it was when it lands.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. Celestion, Vintage 30 datasheet (PDF) — the manufacturer's own | Fs 75 Hz, range 70–5000 Hz, 100 dB, 60 W, ceramic; **and its published response curve**, traced in Appendix A | manufacturer datasheet: no terms line on the sheet itself, but celestion.com's site-wide Website Terms of Use (read this run, https://celestion.com/website-terms-of-use/) reserve **all rights** — "All such rights are reserved … no part of the site … may be copied, reproduced, republished" — so **verified all-rights-reserved**, not unverified; read as a document under vision §5, the curve traced, nothing reproduced | https://celestion.com/productpdf.php?id=888 | yes — **but the host 403s a plain fetch**: celestion.com sits behind Cloudflare and returns HTTP 403 to `curl`'s default User-Agent and to WebFetch; it serves the PDF to a browser User-Agent with an `Accept-Language` header. WebFetch, given the PDF, reports it cannot read the document (checked). Fetched with `curl` under those headers; the response plot — one 886×367 `DCTDecode` JPEG object — pulled out of the PDF and read |
| S2. Celestion, G12M Greenback datasheet (PDF) | Fs 75 Hz, range 75–5000 Hz, 98 dB, 25 W; **its published response curve**, traced in Appendix A | as S1 (same site-wide terms) | https://celestion.com/productpdf.php?id=899 | yes (same route, same 403-without-browser-headers wall) |
| S3. Randall Aiken, "Frequency Response of a Marshall 4x12 Cabinet" (1999, rev. 2014) | the only *cabinet-plus-microphone* measurement reached: setup, and the plotted response traced in Appendix A | "Copyright © 1999, Randall Aiken. May not be reproduced in any form without written approval" — **all rights reserved**; read as a document, values traced, nothing reproduced (vision §5) | https://www.aikenamps.com/index.php/frequency-response-of-a-marshall-4x12-cabinet and its plot https://www.aikenamps.com/images/Images/Marshall4x12response_2.gif | yes |
| S4. Wikipedia, "Loudspeaker enclosure" | the sealed box's 12 dB/octave (stated in the article's ported-vs-sealed comparison) and the out-of-phase cancellation and combing of an *unenclosed / open-baffled* driver — the article does not discuss guitar open-back cabinets beyond calling a dipole baffle "similar to older open-back cabinet designs" | CC BY-SA 4.0, read from the page footer | https://en.wikipedia.org/wiki/Loudspeaker_enclosure | yes |
| S5. Celestion, G12M Greenback product page | the same specifications as S2, independently | manufacturer page, footer "© Copyright Celestion 2026"; same site-wide all-rights-reserved terms as S1 | https://celestion.com/product/g12m-greenback/ | yes |
| S6. The palette, probed and fitted under `audiocomponents/.venv/bin/python` | §4's cascade fit and stage-count probe; §7's truncation check | MIT (this organization) | `audioif/src/shared/audioif_convolve.h`, `audiofilters` | yes (local) |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Char. | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|---|
| T1 | both | **A cliff above 5 kHz:** the response falls at least 15 dB between 5 kHz and 8 kHz — steeper than 22 dB/octave (15 dB over log₂(8/5) = 0.678 oct), and steeper than two cascaded second-order low-passes can give. | S1 (−4.0 → −22.4 dB = 18.4), S2 (+1.0 → −18.9 = 19.9), S3 (−11.8 → −34.5 = 22.7) — **all three re-traced by the critic pass from freshly fetched originals** (App. F) | high | A fall under 15 dB across 5–8 kHz, i.e. a 24 dB/octave design or gentler | Swept-sine magnitude, 20 Hz–20 kHz, at 48 and 44.1 kHz |
| T2 | both | **And then a shelf, not a hole:** from 8 kHz to 16 kHz the response falls by **no more than 12 dB** from its 8 kHz value, per character; it does not keep falling at the cliff's slope (which, at the 27–29 dB/octave the 5–8 kHz fall measures, would be 27 dB or more over that octave). | S1 (−22.4 → −22.7, a 0.3 dB fall) and S2 (−18.9 → −28.4, a 9.5 dB fall) — both re-traced by the critic pass (App. F). **The bar was 8 dB and S2's own published curve failed it by 1.5 dB**; the critic pass re-cut it to the 12 dB the disconfirmation already named, which both sources clear and which still separates a shelf from a low-pass cascade | high | More than 12 dB of fall from 8 to 16 kHz — which every cascade of low-passes gives, and which the current class gives by 23 dB (§7) | The same sweep |
| T3 | both | **Two break-up peaks with a dip between:** the magnitude has two local maxima between 1.8 and 3.6 kHz, each at least 3 dB above the 1 kHz level, separated by a local minimum at least 2 dB below the lower peak. | S1 (+4.5 at 2.2 k, +1.6 at 2.8 k, +4.3 at 3.15 k), S2 (+7.0, +2.8, +7.8) — critic-pass re-trace, App. F | high | Fewer than two local maxima in the band (one peaking bell gives one, which is what the current class gives), either peak under 3 dB above the 1 kHz level, or a dip less than 2 dB below the lower peak | Local extrema of the same sweep over 1.5–4 kHz |
| T4 | both | **Nothing under 70 Hz:** the response at 40 Hz is at least 12 dB below the 1 kHz level, and at 20 Hz at least 20 dB below. | S1 (−15.7 at 40 Hz, −23.1 at 22 Hz), S2 (−16.1, −28.0), S3 (−42.6 at 40 Hz) — critic-pass re-trace; **the 20 Hz column sits on the plots' own left frame edge**, so the re-trace reads 22 Hz, where both drivers are already past the 20 dB bar and still falling (App. F) | high | Less than 12 dB down at 40 Hz — the current class's shipped `4x12 Stack` is only 6.0 dB down (§7) — or less than 20 dB down at 20 Hz | The same sweep |
| T5a | `4x12 stack` | **Sealed and close-miked:** on a third-octave-smoothed sweep, within 3 dB of maximum from 115 ± 15 Hz to 230 ± 25 Hz, at least 20 dB down at 60 Hz, and the 200 Hz–1 kHz span *falls* by 3–6 dB rather than rising. | S3, re-traced by the critic pass from the freshly fetched GIF (App. F): −3 dB points at ≈115 Hz and ≈230 Hz, maximum at ≈218 Hz, −22.2 dB at 60 Hz, −1.8 → −6.1 dB from 200 Hz to 1 kHz (a 4.3 dB fall); S4 (sealed box, 12 dB/octave) | medium — one measurement, one mic position | A lower −3 dB point outside 100–130 Hz or an upper one outside 205–255 Hz; under 20 dB down at 60 Hz; or a 200 Hz–1 kHz change outside a 3–6 dB **fall** | The same sweep, per character. **Smoothing is part of the measurement, not a convenience:** S3's comb structure moves the raw curve 3 dB in 60 Hz around 1 kHz (App. F), so an unsmoothed single-frequency read would go red or green on where a notch lands |
| T5b | `1x12 combo` | **Open-backed:** at least **3 dB** more level at 100 Hz relative to 1 kHz than `4x12 stack` has, and a cancellation notch of at least 3 dB somewhere between 100 and 300 Hz. | S2 vs S1: −2.6 vs −6.4 dB at 100 Hz, a **3.8 dB** difference from the two drivers' own published curves, re-traced by the critic pass (App. F). **The bar was 4 dB, which its own source missed by 0.2 dB**; the critic pass re-cut it to 3 dB, which the traced difference clears without leaning on the open back to make up the gap. S4 gives the notch's mechanism — out-of-phase rear radiation, "loss of bass and … comb filtering" — for unenclosed and open-baffled drivers, **not** for guitar combos, and gives no frequency: **the 100–300 Hz band and the 3 dB depth are ours** | medium — the 3.8 dB is driver-to-driver, not box-to-box; the notch band is a design choice, not a reading | Under 3 dB of difference at 100 Hz between the two characters, or no ≥3 dB notch anywhere in 100–300 Hz on the combo character | The same sweep, both characters, compared |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Attempted and failed, therefore not evidence:** the Celestion guitar-speaker
catalogue at toutlehautparleur.com (**HTTP 403**) and the zzounds mirror of the
Vintage 30 datasheet (**403** — the manufacturer's own copy was used instead);
neither attempt recorded a URL, so this audit could not re-check them.
`https://www.jensentone.com/frequency-response-chart/16/8` **resolves**
(HTTP 200 — re-checked by the audit) but its HTML carries no chart image at
all: the only `<img>` on the page is the site logo, and the chart is drawn by
script. That is what "no chart content" meant. No AES or DAFx paper on
guitar-cabinet measurement was found by search. **Nothing copyleft was
consulted.**

*(from §2)*

**Audit, 2026-09-06 (license and citation pass).** Every URL above was
re-fetched by an independent auditor and every Appendix D quotation was located
in the fetched text. The license calls all survived, and the two Celestion
curves re-traced to within 0.4 dB of Appendix A's table. **S3's readings did
not**: they were eyeballed, are wrong by up to 9 dB where the curve is steep,
and are replaced by the audit's trace — §1, T1 and T5a are corrected with them,
and no trait is lost. Two traits asked marginally more than their own
source gave (T2, T5b); the **trait critic pass** of the same day re-fetched
both datasheets and the Aiken plot and re-traced all three itself, and re-cut
both bars to what the sources actually show — **Appendix F**. Full audit
record: **Appendix E**.

*(from §2)*

**Correction (audit, 2026-09-06): `loudspeakerdatabase.com/Jensen/C12N` is not
dead.** It was recorded here as a 404; re-fetched by the audit it returns
HTTP 200 and a full page for the Jensen C12N printing "Resonance 113 Hz",
"Q factor 1.02" and "Sensitivity 96.8 dB", with script-rendered SPL/impedance
plots and no copyright, licence or terms line of any kind on the page. Nothing
from it is cited — its curve is drawn by script and no static plot was
obtained — but it is **reachable**, and it is the obvious place to start for
§8 Q2's second driver.

*(from §2)*

**S3 is all-rights-reserved and is still usable.** Vision §5: a measurement
published on a site is a document; it was read, its plot traced into numbers
here, and nothing from it is reproduced. It is also the only source reached
that measures a *cabinet* rather than a driver, which is why it alone carries
the box-and-microphone trait (T5a, confidence medium; §8 Q2 says what would
raise it).

*(from §3)*

**Latency: zero samples, 0.0 ms at 48 kHz — a proposed change from 256
samples, 5.33 ms.** Today's class is a convolution and inherits the convolver's
partition: "the output lags the input by AUDIOIF_CONVOLVE_FRAMES frames --
5.3 ms at 48 kHz" (`audioif/src/shared/audioif_convolve.h:21-22`,
`AUDIOIF_CONVOLVE_FRAMES 256u` at `:51`). A biquad cascade has none. This
matters beyond tidiness: vision §9a's working target is a **round trip under
ten milliseconds**, so a cabinet at the end of a stompbox chain was spending
more than half the whole budget on a response a filter delivers for nothing.
**No option in the proposed class adds latency.** `LATENCY_SAMPLES = 0`,
verified by the click measurement; `tail_samples` is the cascade's settling
time, dominated by the 90 Hz high-pass — order 2000 samples at 48 kHz, measured
by the burst-then-silence probe rather than asserted.

*(from §4)*

**Fitted, not asserted — and now rendered.** A seven-section cascade of that
form was fitted to S1's traced Vintage 30 curve here and lands at **1.18 dB rms
over 38 points from 20 Hz to 20 kHz**, holding the 5 kHz cliff (−4.7 against
−4.0), the 8–16 kHz shelf (−21.7 to −24.4 against −22.4 to −22.6) and the 40 Hz
corner (−13.9 against −15.7). The palette verification of 2026-09-06 **built
those seven sections as `synthio.Biquad`s inside one `audiofilters.Filter` and
swept them** — the fixed-point node, not the design maths — and read, re 1 kHz:
−26.40 at 20 Hz, **−13.91 at 40 Hz**, −6.63 at 100, +2.99 at 2.2 k, +3.47 at
2.8 k, **−4.58 at 5 k**, −21.63 at 8 k, −24.33 at 16 k, −24.57 at 20 k. That is
T1's 5→8 kHz fall at **17.06 dB** (bar: ≥15), T2's 8→16 kHz fall at **2.70 dB**
(bar: ≤12), T4 at **−13.91 dB** at 40 Hz and **−26.40 dB** at 20 Hz (bars: ≥12
and ≥20). The fit's own numbers reproduce on the node to 0.1 dB. T3 does not
pass on seven sections — the 2.2–3.15 kHz region comes back as one broad hump
with a single maximum. That is what the eighth section is for: it resolves
T3's two peaks explicitly, at 2.21 kHz (+3.95 dB, Q 4.4) and 3.27 kHz
(+1.96 dB, Q 2.8) with a dip at 1.29 kHz, for 1.23 dB rms. Coefficients and residuals are in
Appendix C. **This is the reason for the tier change:** the convolver was being
paid 4 partitions, ~25 KB and 5.3 ms (`audioif/docs/upstream-diff.md:1383`) to
deliver the impulse response of a filter cascade that the palette can simply
run.

*(from §4)*

**What the convolver keeps.** Nothing in this class. A *measured* impulse
response is a different thing from a designed one and already has a home — the
current docstring says so itself (`drive.py:285-288`): hand it to
`reverb.ConvolutionReverb` or to `audioconvolve` directly. Keeping the option
here would put the class in two portability tiers at once, which roadmap §3
does not allow, and would put 5.3 ms back on a stompbox path.

*(from §4)*

**Python computes, C runs — but the split is not where this paragraph first
put it.** Corrected 2026-09-06 by the palette verification: `synthio.Biquad`
has **no raw-coefficient constructor**. It takes `mode`, `frequency`, `Q` and
`A` and nothing else (`audioif/src/synthio/Biquad.c:148-152`), and the RBJ
coefficients are derived from those **in C**, by `audioif_biquad_configure_w0`
(`audioif/src/shared/audioif_biquad.c:70`). So Python computes eight
*(mode, f, Q, A)* tuples on a macro move; C computes the coefficients and runs
eight biquads per sample per channel. The conclusion the paragraph drew still
holds, for a better reason: the C is deterministic on every target because it
uses this port's own sin/cos (`audioif_trig.c`) and picks its fixed-point scale
per filter (`audioif_biquad.c:54-68`) rather than libm's transcendentals — so
the board builds the same coefficients CPython does, and no table is shipped.
Note for §6's Air macro: `A` is the **linear** RBJ amplitude 10^(dB/40), not
decibels — the shelf branch multiplies every numerator term by it
(`audioif_biquad.c:98-113`), and the library's own `_core.db_to_amplitude`
(`_core.py:79-81`) is the conversion. Passing decibels straight through is a
real trap, and it fails loudly rather than quietly. Measured here: `A = 0`
zeroes every shelf numerator and the node returns digital silence at every
frequency; `A = −18` reaches `fast_sqrt` (`audioif_biquad.c:98`) with a
negative argument and the node saturates to a constant 28521-peak output whose
component at the input frequency is 25–62 dB down — a filter that has stopped
being one. In the peaking branch `A = 0` is a division by zero
(`audioif_biquad.c:96`). Worth a clamp at the class edge; the correct value for
a −18 dB shelf is A = 0.3548, which measures −0.04 dB at 100 Hz, −9.00 at
8 kHz and **−17.98 at 20 kHz** — a floor, which is T2.

*(from §5)*

- **audioif#23, the fixed-point biquad's DC hold.** The class ends in
  `audiofilters.Filter` and its high-pass sits at 70–90 Hz, so Tier 1's
  no-held-DC invariant depends on Gate 0's single answer for the EQ family
  (roadmap Phase 0). If Gate 0 chooses a DC-clean float biquad in an
  audioif-own module, this class's tier becomes **audioif** and its Tier 3
  numbers are re-measured; if it chooses the Python-side tail gate, the class
  stays **stock**. No separate ask.

*(from §5)*

- **The stage cap on the target ports.** Twelve stages were probed under
  CPython only (App. B). If a board build caps the list shorter than eight, the
  lean patch of Tier 3 becomes the shipping patch there and T3 is recorded as
  unmet on that target — a measurement, not an ask.

*(from §7)*

1. **It pays 5.3 ms and ~25 KB for a filter's response.** The class designs an
   RBJ cascade in Python (`drive.py:363-405`), runs it over a unit impulse
   (`drive.py:437-475`) and hands the result to a convolver — for a response
   the same biquads deliver directly at zero latency (§4). Its docstring
   already says the response is designed, not measured (`drive.py:285-288`);
   the convolution is the part that does not follow.

*(from §7)*

2. **The reported latency is wrong.** The convolver lags 256 frames
   (`audioif_convolve.h:21-22`) and the class reports 0, because no class
   overrides `LATENCY_SAMPLES = 0` (`_core.py:140`). A Tier 1 failure, not a
   style point.

*(from §7)*

3. **The top end falls forever.** Two cascaded second-order low-passes
   (`drive.py:380-381`) give 24 dB/octave with no floor: evaluated here, the
   shipped `4x12 Stack` patch is −32.7 dB at 10 kHz, −55.9 at 15 kHz and −87.7
   at 20 kHz re 1 kHz, against S1's measured −20.6, −25.7 and −25.7 — **30 dB
   too dark at 15 kHz and 62 dB at 20 kHz** (T2).

*(from §7)*

6. **The macro ranges are loosely tied to anything measured** — presence
   1.5–6 kHz, top 2.5–12 kHz (`drive.py:314-317`) — and the top corner is tied
   to the box resonance by a fixed 0.7 factor (`drive.py:376`), a coupling
   neither published curve supports.
