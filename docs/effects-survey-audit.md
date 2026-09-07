# Effects Program — Phase 0 Survey Audit

**Program:** the effects program (**`GO effects` GIVEN** — Brad, 2026-09-07 04:15 CDT) —
[vision](https://github.com/PyDevices/workspace/blob/main/docs/effects-vision.md) and
[roadmap](https://github.com/PyDevices/workspace/blob/main/docs/effects-roadmap.md) live in the anchor repo's `docs/`.
**Companion to:** [effects-survey.md](effects-survey.md), which carries the map, the node list and the gate status.
**Roadmap item:** Phase 0 Work — *"The audit report, `audiocomponents/docs/effects-survey-audit.md`: every circuit grade,
OSS claim and license call in the survey re-fetched by independent agents, each correction applied to the survey and
listed."* — and Phase 0 Gate — *"The audit's corrections are applied and its report is committed."*
**Assembled:** 2026-09-07.

---

## 0. What this report is, and what it is not

**It is an assembly, not a fifth pass.** Every correction listed here was made during the Phase 0 run of 2026-09-06/07
by an agent that had not written the seed it audited, and was applied to the survey and to the seed at the time it was
made. This document exists because the roadmap requires the corrections to be *listed* in one place and the audit's
report to be *committed*; the corrections themselves are already in the files.

**Nothing was fetched to write it.** No URL was re-opened, no measurement was re-run, no source was reached for this
report. Where a figure below is the run's own record rather than something re-derived here, it says so. The one number
re-derived for this document is the corpus trait census, and it is stated with its counting rule.

**It is therefore not independent evidence.** An audit report assembled from the audit's own record cannot catch a
correction the audit failed to make. Its value is that the record is now enumerable and that its **floors are labelled
as floors**, which the survey's headline numbers were not.

---

## 1. Scope and independence

Four passes ran over the sixteen units' seeds after the research pass. Three of them produced corrections; the fourth
produced verdicts and is reported in the survey, not here.

| Pass | What it re-did | Independence | Corrections recorded |
|---|---|---|---|
| **1. Licence and citation audit** | every URL re-fetched; every quotation located in the fetched bytes; every line citation checked with `grep -n` | run by an agent that had not written the seed | **160 — a floor** |
| **2. Trait critic** | every Tier 2 row re-cut for falsifiability: a disconfirmation that is the complement of the claim, a stated threshold, a stated level and rate, and a *control that must pass* | run by an agent that had not written the seed | **160 — a floor** |
| **3. Palette verifier** | every §4 and §5 claim re-read against the C under `audioif/src/shared` and the bindings under `audioif/src/<module>/`, and **probed on the CPython build** rather than argued | run by an agent that had not written the seed | **158 — a floor** |
| 4. Node refutation | 51 raw asks merged into 28 candidates, each given two independent refuters on different lenses | two refuters per candidate, neither the asker | verdicts, not corrections — reported in [effects-survey.md](effects-survey.md) §"The node list" |

**Why every count is a floor.** The run's record **caps each unit's correction list at ten**. Sixteen units × a ten-item
cap = 160, and passes 1 and 2 both hit that ceiling exactly, which is the signature of a cap rather than of a count.
Pass 3's 158 sits two under it. So the true totals are **at least** 160 / 160 / 158 and the real figures are unknown and
unrecoverable from the record. **These are not to be quoted as measured totals anywhere.** A unit that made more than
ten corrections lost the eleventh from the record, not from the file: the correction itself is in the seed.

The same cap applies to the survey's **"200 sources reached"**: the per-class figure caps at five and 28 of 46 classes
report exactly five, while `Compressor`'s §2 alone runs to S10 and `Distortion`, `Flanger` and `Rotary` to S14. 200 is a
floor.

---

## 2. Grades, after the audit

Re-derived for this report by extracting each seed's own `**Grade:**` line — a mechanical parse of all 46 files, not a
count copied from the survey.

| Grade | Count | Meaning (vision §4.1) |
|---|---|---|
| **circuit** | **10** | a schematic with values reached and read, plus a SPICE model or an analytic derivation of the traits from it |
| **literature** | **22** | no usable schematic, but a published model sufficient to fix the traits |
| **proxy** | **0** | no class rests on an emulator's output |
| **design** | **14** | no historical standout; traits from the textbook definition |

Portability tiers, parsed the same way: **9 stock**, **37 audioif**.

**Grades the audit held down.** In every case below the seed's grade *hint* or its first draft reached for **circuit**
and the audit refused it, because the schematic with values was never obtained. These are the audit's most consequential
corrections, because a grade is what licenses a trait to be called a circuit fact:

| Class | Grade held at | What was missing |
|---|---|---|
| `Compressor` | literature | **no 1176 schematic reached at all**; no Fairchild 670 schematic with values. Only the Optical character reaches a schematic with values |
| `Flanger` | literature | the original 1976 Electric Mistress drawing. Tonepad's *Rev.2.Nov.1.2005* redraw **was** reached (S15) but is the 9 V single-battery unit; **no trait rests on it**, which is why the grade did not move |
| `Expander`, `NoiseGate` | literature | the full Drawmer DS201 schematic. elektrotanya's first two preview pages were legible — enough to overturn "'VCA' is unsourced" — but **no trait is derived from the previews** |
| `MultiTapDelay` | literature | the RE-201 echo board. Page n5 was read at 216 ppi for the mode-selector table; the echo board itself is unread |
| `Reverb` | literature | any primary EMT document. §6's 0.2–12 s decay span is stated as **our design range**, not a claim about the machine |
| `ParametricEQ` | literature | the factory EQP-1A schematics, which S1 states are not public. Two hobbyist redraws with values were reached **by the audit** — including Gyraf's own drawing, which the seed had written off "as nothing usable" without opening it |
| `GraphicEQ` | literature | component values — the M-108 schematic is an **image-only PDF** |
| `DigitalDelay` | literature | the DD-2 schematic drawing (text read, drawing is an image) |
| `Rotary` | literature | the Leslie 122's schematic scan, **re-fetched by the audit and confirmed unusable** |
| `Bitcrusher` | literature | the SP-1200 scan's schematic pages |
| `Saturation` | literature | a console or preamp schematic with a turns ratio and core geometry — so the `console` character has **no named referent** |

---

## 3. Licence calls the audit changed

Under vision §5 an unfound licence is **copyleft until shown otherwise**, and copyleft sources are measured or read as
papers, never read for code structure.

### 3.1 Downgraded to "licence unverified — treated as copyleft"

Each was re-fetched and grepped, and no rights line was found:

- `Overdrive` S1 and `Distortion` S2 — ElectroSmash on the MAS mirror: **no rights line on either page**. The seed's
  assertion that S1's line "is taken to cover this article too" was **removed**.
- The Waves **dbx 160 User Guide** — no rights line on any of 9 pages.
- **Dattorro, *Effect Design*** (PDF) — no rights statement anywhere in 25 pages.
- The **Boss DD-2/DD-3 archive item** — no `licenseurl`, no `rights` field, re-read this run.
- **Raffel & Smith, DAFx-10.**
- **Zhang's CCRMA course report.**
- The **Roland VB-2 owner's manual** — no rights notice anywhere: cover, specification page and back page all checked;
  the back carries only "BOSS Products of Roland" and "Printed in Japan '82 Mar."
- The **Panasonic MN3207** sheet — no rights notice, and the host serves the PDF without terms.

### 3.2 Corrected upward — a licence better than the seed recorded

- **Aion FX build doc** — page 13 is headed "LICENSE & USAGE" and **grants commercial use**. The seed had recorded
  "no licence granted".
- **SP-1200 service manual** — Public Domain Mark 1.0, re-checked against the document itself rather than against a
  catalogue field.
- **`schematicheaven.net/copyright.html`** — reached, and it **grants free copying but not sale**. It is linked only
  from the homepage footer: the footer-link trap that
  [`agent-knowledge/instrument-sources.md`](https://github.com/PyDevices/workspace/blob/main/docs/agent-knowledge/instrument-sources.md)
  names, and the audit walked into it and then out of it.
- Two sources the seeds had marked "states no terms" do carry a **bare copyright with no grant** — `guitar-gear.ru`,
  `moogfoundation.org`. Recorded precisely, because "no terms" and "copyright, no grant" are different findings.

### 3.3 A wrong call in the other direction

- **McQuillan & van Walstijn (DAFx-20in21)** was recorded as "no rights statement → treated as copyleft" when the PDF's
  own page 1 carries one. **Corrected.** This is the audit's own most useful catch: the copyleft default is safe, and a
  safe default applied without reading is still a defect, because it costs the run a usable source.

### 3.4 Licence calls that stand

No OSS or public-domain claim survives in the survey that the audit did not locate in the fetched bytes. Where the
licence could not be verified, the source is treated as copyleft and **is not read for code structure** — the vision §5
gate, applied rather than asserted.

---

## 4. Network findings the audit produced

These are the audit's, and they matter beyond Phase 0 because several are **false negatives**: a source recorded as
unreachable that is in fact reachable by another route.

- **`www.electrosmash.com` does not resolve** from this machine (`getent hosts` empty; `curl` http=000). The archive
  mirror `electrosmash.mas-effects.com` serves the same articles and drawings, and four classes (`Phaser`, `Overdrive`,
  `Distortion`, `Fuzz`) read their primary source there.
- **`web.archive.org` is blocked for the fetch tool but ANSWERS `curl`** (HTTP 200). What the first pass recorded as
  unreachable was a **tool limit, not a network one** — this re-opens every 403'd route in the run. It was proven on the
  `Phaser` (capture `20260514234042`, the ElectroSmash rights line finally read at the rights holder) and **retried on
  nothing else**. Recorded as open in the survey's §"Still open at the gate"; the retries are Station A's.
- **A default `curl` User-Agent is refused where a browser's is not.** `celestion.com` (Cloudflare) returns 403 to both
  `curl` and WebFetch and serves the datasheets to a browser UA with `Accept-Language`; `hobby-hour.com`'s DM-2 page was
  recorded 403 and returns 200 with a browser UA. **Both were false negatives.**
- **PDFs are often unreadable by the fetch tool and readable with `pypdf`** — that is how S1s for `Limiter`,
  `Compressor`, `Reverb`, `SlapbackDelay` and `Saturation` were actually read.
- Genuinely unreached: `valhalladsp.com` and `reverb.com` (403), `apiaudio.com` (OpenSSL `sslv3 alert handshake
  failure`), `help.uaudio.com` (403). Genuinely dead: the NI *VAFilterDesign 2.1.0* PDF (404), CCRMA's
  `Comb_Filters.html` (404), Griesinger's AES pan-laws paper (404, two guessed CCRMA/JOS URLs also 404).
- One failure was **mis-diagnosed twice** before being recorded correctly — the Giannoulis, Massberg & Reiss compressor
  paper, first written up as a TLS failure, then as a 301 the tool will not follow. The lesson is in the record: a
  failure mode written from memory is not a finding.

---

## 5. Trait corrections

The trait critic re-cut every Tier 2 row so that the disconfirmation is the complement of the claim, the threshold is
stated, the level and rate are stated, and there is a **control that must pass** — so a suite of only-failures cannot
pass itself off as a checker that always fires.

**Two shapes of defect it caught, both named in
[`agent-knowledge/workspace-craft.md`](https://github.com/PyDevices/workspace/blob/main/docs/agent-knowledge/workspace-craft.md):**

- **Rows a correct build would have failed** — `Flanger` F6, `Exciter` T1, `Compressor` F1/F4, `Overdrive` T5,
  `Distortion` F1, `SlapbackDelay` T2.
- **Rows a null build would have passed** — `MultiTapDelay` T5, `RingMod` W2. These are the dangerous ones: absence
  reading as agreement.

**Recurring corrections**, from the per-seed records:

- A trait and its disconfirmation that **did not meet** — a gap between "confirms above 3" and "disconfirms below 5", so
  a measurement landing between them settled nothing. `Reverb` T2, T3, T5 and T10 all carried this.
- **Monotonicity over a continuum**, which cannot be measured. Replaced by named positions and an end-to-end margin
  (`Reverb` T3, T6).
- **Estimators left unstated**, where the estimator matters more than the threshold — RT60 from a least-squares
  log-envelope slope fit over −5…−35 dB, never a −60 dB crossing.
- **Characters sharing one row**, so one tuning under three names passed everything. Split per vision §10.7 — a character
  that fails its traits cannot hide behind one that passes. `Reverb` T9 exists only because of this pass.
- **A section pointer the seed never quoted and the run never reached**, cited as though it were read
  (`Reverb`'s S1 §1.3.7). Narrowed to the three passages the appendix actually quotes.

**Census after the pass**, re-derived here by parsing each seed's Tier 2 section from the file start to its first
`## Appendix`: **327 traits** across 46 seeds, minimum 5, median 6, maximum 21 (`Compressor`); **32 of 32** non-design
seeds clear the gate's three-row bar and the 14 design seeds carry rows anyway. Two rows are deliberately labelled
*unmeasured* rather than dressed up — `Fuzz` C4 and `Saturation` IR3.

**The 332-against-327 gap is closed, not left standing.** The kit refuter's 332 counted *non-header table lines*; 327
counts traits. The five-line difference was four character sub-header rows in `Reverb.md` (`| **Plate** — … | | | | | |`
and siblings, which wore a trait row's shape with five empty cells) plus one prose line in `RingMod.md` §5 that began
with the absolute-value bar of `|3f₁ − f₂|` and which Markdown rendered as a stray row. Both are fixed at the source —
`Reverb`'s sub-headers are now bold paragraphs between separate tables, the `RingMod` maths is in backticks — and the
corpus now parses to **327 either way**, with `Reverb` returning 10.

---

## 6. Palette corrections

The palette verifier read every §4 and §5 claim against the C in `audioif/src/shared` and the bindings in
`audioif/src/<module>/`, and **probed the CPython build** rather than arguing from the source. **158 corrections — a
floor.** Its two most consequential classes of finding:

- **Node asks killed outright.** Twenty-five asks were raised and refuted *inside the seeds* by this pass, before the
  two-refuter list ever saw them; six of them reappear there because a later seed or the merge re-raised them. The
  survey's §"Asks killed inside the seeds, before the node list" is that table.
- **Palette claims that were simply wrong** — a seed's account of what an existing node does, corrected against the
  kernel. Two that the node list rests on: **there is no oversampling anywhere in the palette**
  (`audiospeed.SpeedChanger` reads `phase >> SPEED_SHIFT` with no interpolation and no anti-alias filter), and
  **nothing on the palette gives gain above unity** except a drive node itself (`MixerVoice.level` clamps 0..1 silently;
  `Multiply` scales by `>> 15`).

**No CircuitPython-ported node is proposed for modification anywhere in the 46 seeds.** The verifier checked this as a
property of the corpus, not as an assurance.

---

## 7. What the audit could not verify

Listed because the gate condition is that dead links are **recorded as not found**, never quietly dropped. Each item
below is labelled in its seed rather than dressed up.

**Recorded as not reached:** 109 entries, each with its failure mode (dead link, 403, unreadable scan, TLS failure).

**Values a trait or a default rests on that no reached source prints** — carried as *unsourced* and kept out of the
trait table:

- `Rotary`: the **horn radius r_s** (it fixes T3's absolute Doppler depth, macro 9's default and the class's stated
  latency); the **"2 kHz horn band-pass"**, which Penniman attributes to Henricksen and a targeted re-read of Henricksen
  **does not support** — either the attribution is wrong or the claim is; and `c = 343 m/s`, left in place and named
  rather than struck, as a physical constant.
- `Fuzz`: **the gating mechanism.** Vision §6 assumes "the Fuzz Face's gating is a bias point that moves with the
  signal" as an *input to the waveshaper node's design*, and **nothing reached this run sources it** — S1 describes a
  static DC bias with an AC-shunted emitter.
- `NoiseGate`, `Expander`: **hysteresis.** Every practitioner's account names it; **no source reached states a figure
  for any unit**, the DS201 included, both manual editions grepped. The Hysteresis macro is provisional and ships only
  if a source is reached.
- `Phaser`: the **Speed knob's range in Hz** (the proposed 0.05–10 Hz is the seed's own), and **which LFO ramp is
  longer** — S3 models a 65 % duty triangle while S4 *measured* a real unit and reports the falling edge longer. The two
  sources **disagree in direction**, so P9 fixes only the magnitude of the asymmetry and is labelled a surface
  requirement, not a circuit trait.
- `Chorus`: whether the LFO injection is frequency-linear or resistance-modulating — T2's probe discriminates against
  the model, not against hardware.
- `Vibrato`: what Roland's "Delay Time … 4 ms (Depth)" means.
- `RingMod`: the ring diodes' part number — the drawing marks the four only as "SELECT DIODES". And a **sourced tension
  recorded rather than resolved**: Bode's own 1984 history credits multiplier-type behaviour to **germanium** diodes in
  their square-law region and names silicon separately.
- `SlapbackDelay`: the tape speed — 134–137 ms and the Ampex 350's speed list imply 1.03 in at 7½ ips or 2.06 in at
  15 ips; the derivation is labelled as one.
- `Compressor`, `Limiter`: the ESP32-P4/S3 budget percentages rest on one number **stated from memory** — "a
  single-precision `expf` or `logf` from newlib costs of the order of 100–200 cycles" — flagged unsourced in the seed.
  The budgets are therefore provisional until Phase 1's cost table replaces them with measurements.

---

## 8. Limits of this report

Stated on their own lines, not folded into a paragraph that ends "nothing else is pending".

1. **The three correction counts are floors and their true values are unrecoverable.** The record caps each unit's list
   at ten; passes 1 and 2 hit 160 = 16 × 10 exactly. Nothing in the record distinguishes a unit that made ten
   corrections from one that made thirty.
2. **This report is assembled, not independent.** It cannot catch a correction the audit failed to make. A genuinely
   independent re-audit is not scheduled and is not proposed here.
3. **The source-row census is not re-derived.** The survey's figure is **288 labelled source rows carried in the seeds'
   §2, counted mechanically**. A parse for this report — table rows in §2 whose first cell begins with an `S` followed by
   a digit — returns **252** (265 if the whole file including the appendices is scanned). The survey's counting rule for
   288 is not written down, so the two cannot be reconciled from the record. **Owner: Station A**, which should state the
   rule and settle the number the way §5's 332-vs-327 gap was settled.
4. **The reopened archive route was proven once and retried on nothing.** §4 records it; the survey's open list records
   it; no retry was run in the audit or in this assembly. Every source recorded 403 in this run may be reachable.
5. **`Overdrive` is the only class whose circuit facts were independently re-derived**, through the TS808 SPICE proof
   (`tools/spice/ts808/`). Every other circuit-graded class rests on a schematic read once and transcribed once — R3 in
   the roadmap's risk register, retired for exactly one class.

---

## 9. Verdict against the gate condition

The roadmap's Phase 0 gate reads: *"The audit's corrections are applied and its report is committed."*

- **Corrections applied: yes.** They were applied to the survey and to the seeds as they were made, by the pass that
  made them, during the run of 2026-09-06/07. Sections 2–6 above list them by class and by kind.
- **Report committed: this file.**

The gate's other conditions are tracked in [effects-survey.md](effects-survey.md) §"Gate status — roadmap Phase 0", not
here.
