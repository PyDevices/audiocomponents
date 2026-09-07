# Effects Dossier — `GraphicEQ` (MXR M-108 Ten Band)

**Class:** `lib/audioeffects/eq.py` — read once, for §7, and not otherwise
consulted. Rebuilt at `lib/audioeffects/rebuilt/graphiceq.py`.
**Family / phase:** EQ, roadmap Phase 2
**Standout:** the MXR Ten Band Graphic EQ (M-108 / M108S) — vision §4.2,
**confirmed**: ten octave-spaced bands, ±12 dB, two level sliders, which is
exactly a `GraphicEQ`'s surface.
**Grade:** **literature.** Two manufacturer sheets agreeing across two
revisions (G1, G2), a JAES paper defining and measuring this class of design
against constant-Q (G3), and Elliott's circuit theory for the gyrator band it
is built from (G5, G6, G8). The M108 schematic was reached and is an
image-only PDF (App. A), so no component values were read.
**Portability tier:** **audioif** — `REQUIRES = ("audiobiquad",)`. The seed
said *stock, unless Gate 0 answers audioif#23 with a float biquad node*. It
did: audioif#39 shipped `audiobiquad` in Phase 1
(`audioif/docs/upstream-diff.md:1953-2075`), and this class is on it. §4.
**Status:** **Station A complete**, 2026-09-07. Trait table frozen below,
unchanged from the seed. Citations are against audioif `2f6cbc3`.

## 1. The circuit, in one paragraph

The M-108 is **ten band sections whose sliders vary the gain of one op-amp
stage across a tuned circuit**, boosting toward the feedback end and cutting
toward the input, with **unity gain at the centre detent**: without the
frequency-selective network "the pot sliders simply vary the gain of the
circuit and unity gain is achieved when the slider(s) are centred" (G5), and
of exactly this topology Winer's 1982 description says "no noise or
distortion is ever contributed when the pot is centered" (G7). Nine of the
ten are **gyrator** bandpass sections — an op-amp simulating an inductor,
`L = R2 × R1 × C1`, `Q ≈ 2π·f₀·L / R2` (G6) — at **31.25, 62.5, 125, 250,
500, 1k, 2k, 4k and 8 kHz**, each ±12 dB; the tenth is a **±12 dB shelf at
16 kHz** on both specification sheets (G1, G2), corroborated by a schematic
reading finding nine active filters and "the last (16 kHz) is a passive
filter" (G7). The behaviour that defines it is the one Bohn wrote a paper
about: the tuned circuit is loaded by the slider, so **Q moves with the
slider** and the band is narrow **only at the extremes** — at low boost "the
conventional design's bandwidth is in excess of one octave … it has degraded
into something nearer to a 10-band octave equalizer" (G3 §2). Bands therefore
overlap and add: three adjacent sliders at +6 dB give a conventional design
+12.5 dB over 2.5 octaves against a constant-Q design's +6 dB over one
octave (G3 §2, fig. 6). Around the bank sit **GAIN** and **VOLUME**; G1, G2
and G7 give **neither a dB range nor a position in the signal path**, so
"GAIN before the bank, VOLUME after, each ±12 dB" is this dossier's design
choice, not a fact about the pedal. The pedal runs on 18 V; its sheet gives a
frequency response of "±1 dB, 20 Hz to 20 kHz" (G1).

*(The audit corrections behind this paragraph are in **App. R**, verbatim.)*

## 2. Sources and license calls

All reached 2026-09-06; nothing from memory. **What each row gave, and the
audit's re-fetch of every one, are in App. C and App. R** — moved there under
the length rule. Copyleft and unverified sources are read as papers, never for
code structure (vision §5).

| id | Source | Licence as read | Reached |
|---|---|---|---|
| **G1** | Dunlop, *M108S Ten Band Graphic EQ* instructions, 92503020568 REV D | no copyright or terms line on the sheet | `pypdf`, twice |
| **G2** | MXR *M108 Ten Band Graphic EQ*, 92503002230 revC | no copyright or terms line on the sheet | `pypdf`, twice |
| **G3** | Bohn, *Constant-Q Graphic Equalizers*, JAES **34**(9), 1986 | no licence line in the PDF; host's Terms of Use are all-rights-reserved — **unverified, treated as copyleft** | `pypdf` |
| **G4** | Bohn, RaneNote 101/117 | "© 2005 Rane" — **all rights reserved** | HTML |
| **G5** | Elliott, *Equalisers, The Various Types And How They Work* | "© 2015", personal use only — **all rights reserved** | HTML |
| **G6** | Elliott, *Gyrator Filters* | "© May 2014", same notice — **all rights reserved** | HTML |
| **G7** | gr33nonline, *Changing up Op-amps* (M108 schematic reading + Winer 1982) | no licence notice on the page — **unverified, treated as copyleft** | HTML |
| **G8** | Elliott, *Guitar/Bass Graphic Equaliser Mk II* (Project 149) | "© May 2014", same notice — **all rights reserved** | HTML |

What was **not** reached, and what was looked for: App. A.

## 3. Traits — frozen 2026-09-07, before any code

### Tier 1 — invariants

The standard block, verbatim from vision §3, is in **App. I**, with this
class's notes on it (the 22.05 kHz clamp, the silence-to-zero exception).
**One note there is now out of date.** The seed called silence-to-zero "the
invariant this class is known to fail", at +7 / +2 / +5 LSB held forever. That
is the *ported* biquad; on `audiobiquad` the same three configurations reach
**exact zero** (App. S(i)), and the ported readings become the positive
control.

### Tier 2 — circuit traits

**Unchanged from the seed. Nothing was added, dropped or renumbered at
Station A, and no threshold was moved.** The rows in full — source,
confidence and the reasoning behind each cell — are in **App. T**; the
statement, the disconfirmation and the measurement stay here, because they
are what the gate checks.

| # | Trait (falsifiable as stated) | Disconfirmed by | Measurement (kit) |
|---|---|---|---|
| **T1** | **The top band is a shelf, the other nine are bells.** 16 kHz macro at +12 dB alone ⇒ the level at 20 kHz is within **1.5 dB** of the level at 16 kHz and at least **+9 dB**; the 8 kHz macro at +12 dB alone ⇒ the level at 16 kHz is at least **6 dB** below its own peak. | **either half missed** — the shelf returning toward flat above its centre, or the 8 kHz band still within 6 dB of its peak at 16 kHz | RESPONSE, swept to 22 kHz at 48 kHz, one macro at a time |
| **T2** | **Proportional Q — the bands narrow as the slider travels.** For the 1 kHz band, mid-gain bandwidth at **+3 dB is ≥ 1.5 oct** and at **+12 dB is ≤ 0.8 oct**, while the first +1 dB crossing moves **less than 10 %** between them. | **any of the three missed** — in the limit a bandwidth that does not change at all, which is constant-Q | RESPONSE at +3, +6, +12 dB on one band |
| **T3** | **Adjacent bands overshoot when summed.** 500 Hz, 1 kHz and 2 kHz all at +6 dB give a combined peak of at least **+9 dB**, and the region within 3 dB of it spans more than **two octaves**. | **either half missed** — in the limit a peak within 1 dB of +6 dB, which is a bank adding nothing | RESPONSE, three adjacent macros at +6 dB |
| **T4** | **A band at zero is out of the circuit.** With band *k* at 0 dB and its neighbours at ±12 dB, the render is **byte-identical** to the same setting built without band *k* at all. | any difference at all between the two renders | DIGEST, both builds over the full probe set, 48 and 44.1 kHz |
| **T5** | **All ten together are smooth but hot.** Every band at +6 dB ⇒ peak-to-peak ripple from 60 Hz to 8 kHz under **2 dB**, and the mean level over that span above **+9 dB**. | **either half missed** — ripple above 2 dB, or a mean at or below +9 dB | RESPONSE, all macros at +6 dB |

No characters. `Constant Q` (§6) is an option, not a character: the table is
stated at its default — proportional, `Band Q` 2.0 — and Station C measures
there. Where the thresholds came from: App. B.

### Tier 3 — cost and latency

**Latency: zero, at every setting and every rate.** Every section is a
biquad; **no option on this class adds latency** — no lookahead, no
partition, no window. `latency_samples` is 0.

**Tail: 22314 frames (465 ms) at 48 kHz**, measured on the worst case (all
ten bands at +12 dB, 40 Hz burst then silence) and constant in *time* across
rates — 20520 at 44.1 kHz, 10262 at 22.05 kHz (App. S(ii)). The class reports
the rate-scaled bound, 470 ms.

**Twelve sections, always running** — ten bands plus the two level macros
(§4), one `audiobiquad.Biquad` node each. By `ParametricEQ.md` Appendix C's
arithmetic (100 instructions per sample per section per channel, 256-frame
stereo block) one stereo section is **4.00 %** of the S3's block and
**2.40 %** of the P4's, so twelve are 48 % / 28.8 % raw and, with that
appendix's one-third overhead, **S3 64 %, P4 38 %**. That is the budget — the
seed's palette-verifier pass already flagged these as the honest
twelve-section figures, and they are promoted here from a flag to the budget.

**Lean patch: no — corrected from the seed's "yes", and it is a real loss.**
A patch sets macro values; it cannot change the node count, and a flat band is
*not* free: `audioif_filter_f32.c:222-241` has no `mix == 0` short-circuit, so
the recursion runs for every section at every setting. No patch on this class
can reduce its cost. A `mix == 0` fast path in that kernel would make one
real; it is recorded as a want in §5, not filed as a node ask, because it
unblocks no trait.

## 4. Modeling approach on the palette

**Twelve chained `audiobiquad.Biquad` nodes.** Head to tail: `Gain`
(HIGH_SHELF at 5 Hz) → nine `PEAKING_EQ` bells at 31.25 Hz × 2ⁿ → one
`HIGH_SHELF` at 16 kHz → `Volume` (HIGH_SHELF at 5 Hz). Python computes each
band's `Q` from its gain on a macro move; C runs every sample. Nothing is
added to the palette. **Tier: audioif.** Mono gets the same curve on one
channel; not stereo by definition.

- **Why `audiobiquad`, not the stock bank.** On `audiofilters.Filter` over
  `synthio.Biquad` this class holds **+7 LSB** after silence at 31.25 Hz/+6 dB
  and **+5 LSB** with all ten — reproduced here, a third independent
  reproduction of audioif#23's figures. On `audiobiquad` every one reads
  **exact zero**. App. S(i).
- **A flat band is a `mix = 0` wire, not an unbuilt node**, and that is what
  makes T4 reachable. A `PEAKING_EQ` at `gain_db = 0` is *not* bit-transparent
  at this bank's lowest centres — up to **5 LSB at 31.25 Hz** over 24 000
  frames of noise, exact from 250 Hz up (App. S(iv)). At `mix = 0` the kernel
  computes `1.0f * x0 + 0.0f * y0` (`audioif_filter_f32.c:240`), byte-exact at
  every centre. **Every band is built; a band at the detent is muted, not
  absent** — stronger than the seed's "flat bands are not built", because the
  knob still turns.
- **The detent is one macro step wide.** ±12 dB over 0–127 makes a step
  0.189 dB, so codes 63 and 64 land at ∓0.094 dB and nothing else is within
  0.1 dB of zero: `|gain| < 0.1 dB` *is* the M-108's mechanical centre detent
  in the macro's own units.
- **Q from gain**, by `ParametricEQ.md` Appendix A's law with the anchor
  exposed as a macro: `Q(G) = Q₁₂ · sqrt((A² − L²/A²) / (A₁₂² − L²/A₁₂²))`,
  `A = 10^(|G|/40)`, `L = 10^(1/20)`. One `sqrt` and one `10**` per move,
  never per block; it reproduces Appendix A's table to three decimals at
  `Q₁₂ = 2` (App. S(v)). Below +1 dB the law has no root and `Q` floors at the
  kernel's 0.05 — the limit of the law, not a fudge.
- **Two level macros cost two more sections, because no palette node gives
  gain above unity** (`Mixer.c:332` clamps silently, `audioif_multiply.c:38-45`
  can only attenuate). A HIGH_SHELF at **5 Hz** measures +11.97 dB at 30 Hz
  and +12.00 at 100 Hz, 1 kHz and 10 kHz; at a 10 Hz corner 30 Hz is 0.16 dB
  short and at 20 Hz 2.3 dB short (App. S(vi)).
- **Panel order kept — a headroom rule, not a commutation.** Each node writes
  int16 between sections and `to_s16` saturates at ±32767
  (`audioif_filter_f32.c:43-50`), so +12 dB of Gain into a hot source clips at
  the first boundary. An M-108's op-amps clip too, and the docstring says so.
- **Centres clamp below Nyquist through `self._hz()` (0.98 × Nyquist).** This
  is stability, not tidiness: the ported biquad over Nyquist rails into a
  full-scale square at f_s/4 while raising nothing, and renders exact zeros on
  silence, so construct-and-catch and silence-in-silence-out both pass it
  (App. E(iv)).

*(The composition the seed refuted and what re-trying it actually showed:
App. S(iii). The seed's §4 bullets, verbatim, are in App. R.)*

## 5. Node asks

**None.** The one this family had — a DC-clean biquad — was Gate 0's, was
answered, and shipped: `audiobiquad`, audioif#39. T1–T5 are all reachable on
it. The palette's EQ math is inside **0.03 dB of the closed form from 50 Hz
to 22 kHz** (`audioif/docs/upstream-diff.md:1123`).

One **want**, not a node ask, because it unblocks no trait: a `mix == 0`
short-circuit in `audioif_biquad_f32_process_s16`, which would make a lean
patch real (§3).

## 6. Surface — frozen

Fourteen macros, two under the ceiling. Ranges are engineering spans; the
host sees 0–127.

| # | Label | Mode | Range | Default | Generalizes |
|---|---|---|---|---|---|
| 0–8 | `31` `63` `125` `250` `500` `1k` `2k` `4k` `8k` | BIPOLAR | ±12 dB | 0 dB | the nine gyrator band sliders (centres 31.25 Hz × 2ⁿ) |
| 9 | `16k Shelf` | BIPOLAR | ±12 dB | 0 dB | the tenth slider — a shelf, not a bell (T1) |
| 10 | `Gain` | BIPOLAR | ±12 dB | 0 dB | the GAIN slider, before the bank |
| 11 | `Volume` | BIPOLAR | ±12 dB | 0 dB | the VOLUME slider, after the bank |
| 12 | `Band Q` | UNIPOLAR | 0.7…2.5 | **2.0** | no panel control — the anchor of the proportional-Q law |
| 13 | `Constant Q` | TOGGLE | off \| on | **off** | no panel control — the G3/G5 axis |

**Two changes from the seed's proposal, both Station A's to make.** Macro 13
was `Q Law`, TOGGLE, "proportional | constant": renamed `Constant Q` so that
**off is the default and off is proportional** — a TOGGLE whose 0 is the
non-default state is a surface a host gets wrong once. `Band Q`'s default is
pinned at **2.0**, the anchor both Appendix A's table and this dossier's T2
thresholds were computed at (App. B); G6's gyrator Q of 1.51, nominal 1.57,
sits inside the span. **The refuter's obvious argument is that the default
was chosen to pass T2, and it is half right:** the absolute thresholds move
with the anchor, T2's content does not — `Q ∝ Q₁₂`, so the **ratio** between
the +3 dB and +12 dB widths is 2.51 at every anchor. At `Band Q` 1.5 the
+12 dB half would not be met, and Station C reports 1.5 beside 2.0.

**Characters:** none. **Patches:** `0 Flat` · `1 Scooped Mids` ·
`2 Pushed Mids` · `3 Trimmed Bottom` · `4 Rolled Top` · `5 Full Boost`.
`6 Ten Band - lean` is **dropped**, with the reason in §3.

The constructor keeps a `gains_db` sequence so local code can set the whole
curve in one call, and a `centres` option — **exactly ten ascending
frequencies**, because the macro surface is fixed at fourteen and a shorter
list would leave macros addressing nothing, which is this workspace's
signature failure. The 16 kHz shelf is always `centres[9]`, so it tracks a
retune by construction (§8.3).

## 7. Defects in the current class the rebuild must not repeat

One read of `lib/audioeffects/eq.py`. The full argument behind rows 2, 4, 5
and 6 is in **App. R**.

1. **No surface at all** — `MACRO_LABELS = ()` (`eq.py:81`),
   `PATCHES = {0: ("Default", ())}` (`:83`): no knob a host can turn.
2. **Every band is a bell, including the top one** (`eq.py:93-95`, `:47-49`).
   T1 is not implemented at any setting.
3. **Q is a hard-coded 1.4 for every band at every gain** (`eq.py:94`) — the
   class is constant-Q by omission and T2 is not expressible.
4. **Bands above Nyquist are dropped silently** (`eq.py:92`, `:95`): at
   22.05 kHz the top two bands vanish and nothing says so.
5. **Centres are the ISO preferred series** (`eq.py:67-68`) where the
   standout's are exact octave doublings from 31.25 Hz (G1, G2), hard-coded
   at module level where a constructor cannot reach them.
6. **Inherited from `ParametricEQ`:** `check_hz()` refuses instead of
   clamping (`eq.py:48`, `_core.py:471-474`); the all-flat case returns the
   source itself (`eq.py:56-61`) and so takes a different path through
   `reset()`/`deinit()`; `Effect.__new__` mutates module-wide format state
   (`_core.py:149-152`).

## 8. Open questions — all four settled at Station A

1. **audioif#23's one answer.** *Settled, and not by this session:* Gate 0
   answered it with a node — `audiobiquad`, audioif#39, shipped in Phase 1 and
   on the pin. The seed's own conditional fired exactly as written: §4 changed,
   the tier moved to **audioif**, no trait moved.
2. **T2's and T3's thresholds are scaled, not measured.** *Settled as
   standing, on the seed's own evidence:* Appendix A's law — which this class
   implements literally (App. S(v)) — predicts 1.795 oct at +3 dB and 0.714 at
   +12 against thresholds of 1.5 and 0.8, so they are floors with margin.
   **Not moved. Station C records the real numbers whatever they are.**
3. **Whether the 16 kHz shelf tracks a `centres` change.** *Settled by
   construction:* `centres` takes exactly ten ascending frequencies and the
   shelf is always `centres[9]`. It cannot silently become a bell mid-bank.
4. **The M-108 schematic could not be read** (App. A). *Settled as closed,
   not deferred:* image-only PDF, no OCR on this machine, and the three other
   hosts carrying per-band values return 403 or do not resolve. Grade stays
   **literature**; T2's Q is derived, not read off the hardware.

**What Station A did not settle:** the board leg. Every Tier 3 number above
is arithmetic from audioif's instruction counts, not a measurement on a P4 or
an S3, and the per-node overhead of a twelve-node chain is not in it — the
desktop cannot see it, because the desktop's `audiobiquad` is a Python shim
over the same kernel.
## Appendix

### A. Sources not reached, and what was looked for

**Reached, unreadable:** the *MXR Ten Band Graphic Equalizer M-108 PCB RevE*
schematic, https://schematicsonline.com/wp-content/uploads/2022/11/MXR-M108-10-Band-Eq.pdf
— one page, **zero extractable text** under `pypdf`; a scanned drawing, and this
machine has no OCR. (Re-fetched twice: HTTP 200, 125,595 B, one page; the second audit's `pypdf`
extraction returns **zero** non-whitespace characters. The claim holds.) **Not
reached:** `zikinf.com`'s mirror of the earlier
M108 manual (HTTP 403 to both `curl` and the fetch tool in the audit run — the
same document number is served by the manufacturer, and G2 now cites that copy);
the freestompboxes.org M-108 schematic
thread (HTTP 403, re-confirmed in the audit run), which search results suggest carries the
per-band capacitor values and the Q-setting resistor discussion;
`www.electrosmash.com` (does not resolve from this machine — re-confirmed in the
audit run — and its MAS Effects mirror, whose index the audit re-read, lists 29
articles, four of them MXR pedals (Distortion +, Dyna Comp, MicroAmp, Phase 90)
and none the EQ; the index says in its own words it is "not a complete backup of
the site — just these 29 articles", and the audit's own count is 19 pedals,
4 chips, 6 amps). **Looked for and not found:** any published
measurement of the M-108's per-band Q or bandwidth at any slider position, and
any DAFx or AES paper modelling this pedal. Search results quoting per-band
component values were read as snippets only and are **not cited anywhere in this
dossier** — one of them gave a "simulated L" in nanofarads, which is enough to
show the snippet is garbled rather than a source.

**Audit, 2026-09-06 — the failure each host actually returns.**
`schematicsonline.com`: HTTP 200, unreadable as above. `zikinf.com`: **HTTP 403**
(the body is an HTML error page, not a PDF). `freestompboxes.org`: **HTTP 403**.
`www.electrosmash.com`: `Could not resolve host` — no DNS record at all; its
mas-effects mirror: HTTP 200. Nothing recorded here as not reached turned out to
be reachable in this run.

### B. Where the trait thresholds came from

Bohn's figures (G3) are all for one-third-octave units, and this class is
octave-band, so T2's and T3's numbers are scaled rather than quoted. The scaling
rests on the octave↔Q closed form `Q = √(2^N)/(2^N − 1)`, which returns
**4.3185** at N = ⅓ — Bohn's own 4.318 (G3 §4.1), so the form is corroborated
rather than assumed — and **1.4142** at N = 1. *(Audit: both re-read at source —
Bohn's "Using this formula, Q is calculated to be 4.318" in §4.1 and his
"one-third-octave bandwidths require a Q of 4.3185" in §4.6; the closed form
returns 4.31846 and 1.41421, so the check stands.)* G5 states a one-octave design
"needs Q of 2", which disagrees with the closed form at the third decimal place
of a different definition; the closed form is used here because Bohn's own
number checks against it, and the disagreement is recorded rather than smoothed.

- **T2's +12 dB threshold (≤ 0.8 octave).** A well-behaved octave-band bank at
  full boost should be at or near its nominal one-octave width; 0.8 leaves room
  for the section to be slightly narrower than nominal, which is what "narrow
  only at the extremes" (G3 §2) predicts.
- **T2's +3 dB threshold (≥ 1.5 octaves).** Bohn measures a ⅓-octave unit
  degrading past one octave at +3 dB — a factor of at least three. Applying the
  same factor to a one-octave nominal gives three octaves; 1.5 is deliberately
  the conservative half of that, so passing it is evidence and failing it is
  unambiguous.
- **T3's +9 dB and two-octave thresholds.** Bohn's conventional design turns
  three adjacent +6 dB sliders into +12.5 dB over 2.5 octaves. On octave centres
  the overlap is smaller; +9 dB (half the overshoot) and two octaves are the
  conservative halves again.

- **T5's 2 dB ripple bound.** G8's own looser figure ("less than 2dB" in the
  text, "generally below 1dB" on Figure 7) for a nine-band octave gyrator bank,
  taken as the bound rather than the 1 dB the figure claims — because G8's
  setting is not this trait's setting (§2, G8's caveats) and the looser number
  is the one the article states in prose.
- **T5's +9 dB mean.** The same conservative-half construction as T3's, applied
  to the whole bank: over 60 Hz–8 kHz every band has neighbours on both sides,
  so the three-adjacent-sliders figure of T3 is the floor the mean must clear.
  Stating the mean rather than the peak keeps T5 about the bank adding, and
  leaves the peak to T3.

Every one of these is a threshold this dossier chose, and each is stated so a
measurement can land outside it. If one does, the roadmap's rule applies: a
disconfirmed trait is a legitimate result, recorded with its real number.

### C. Audit source notes — the excerpts the §2 rows point to

Read at source in the licence-and-citation audit run, 2026-09-06. Kept here so
§2 stays a table.

**G1's Filtering line, and the digit that goes missing.** `pypdf` extracts
"±12db at: 31.25, 62.5, 125, / 50, 500, 1k, 2k, / 4k, 8kHz / ±12dB shelf at
16kHz" — the 250 loses its leading digit at the column break. The same sheet's
panel legend renders "GAIN 16K 8K 4K 2K 1K 500 250 125 62.5 31.25 VOL", and G2's
copy of the line has the 250 intact, so the band list is not in doubt.

**G2's self-contradiction.** Spec table: "±12db at: 31.25 … 8kHz / ±12dB shelf at
16kHz". CONTROLS block on the same page: "PARAGRAPHIC SLIDERS boost or attenuate
up to ±18dB at six different frequency centers". Ten bands at ±12 dB is what G1,
the panel legend and G7's schematic reading all support; the ±18 dB/six-band
sentence is boilerplate from another pedal and is evidence for nothing.

**G5, the two circuits that must not be mixed.** Figure 8 (inductor/gyrator, the
class this pedal belongs to): "Without the frequency selective networks (C1, L1,
etc.), the pot sliders simply vary the gain of the circuit and unity gain is
achieved when the slider(s) are centred"; and "when the pot is near the centre
position, the load on the tuned circuit is no longer 470 ohms, it's 470 ohms plus
the equivalent resistance of the pot and the feed resistors (2.7k as shown). As
the pot position varies, so does the Q". Figure 9 (constant-Q, virtual-earth):
"the pots control the output from each band-pass filter … When the pot is centred,
the signal to U1 and U2 is identical, so it cancels and there's no boost or cut
for that frequency. The Q remains constant." The second is not this pedal.

**G6's ten-band table and its centred-pot statement.** 1 kHz row: C1 3.9 nF,
C2 220 nF, R1 62 kΩ, R2 470 Ω → 113 mH, f₀ 1.0 kHz; "Q ≈ 2 π × 1k × 113m / 470 =
1.51"; "The nominal Q is 1.57 for the filters shown". On level: "With all values
as given in the schematic and table, maximum boost or cut would be quoted as
±10dB, although it measures about ±11dB. To get ±12dB, R2 and R3 (both 2.7k in
the equaliser section) can be increased to 5.6k, but this will result in greater
noise." And, of a ten-band gyrator bank: "the noise gain of U12 is 16dB, even
though the audio gain is unity when all pots are centred."

**G7's Winer reproduction.** "There are several ways to make an octave or
third-octave graphic equalizer, and my favorite is shown generically in Figure 5.
In this circuit only one op-amp (A1) handles the actual equalizing, regardless of
how many bands are needed. Notice that instead of using inductors, a gyrator
circuit is used to simulate an inductor. And like the parametric equalizer, no
noise or distortion is ever contributed when the pot is centered." And, on
proportional Q from the same author: "the bandwidth of any equalizer will vary
depending on the setting of its boost/cut control." G7 then states: "Comparing
Ethan Winer's description with the schematic of the MXR, it can be seen that U5A
forms the gyrator circuit."

**G8's own framing, which T5 must not overstate.** "Unlike most conventional
graphic equalisers, each slider ranges from fully off to fully on, and not the
more conventional +/-12dB or so that is normally available … As a result, there is
no flat setting (other than all off!)"; "With all sliders at maximum, the response
is passably flat, and it's unlikely that you'll be able to hear the slight ripple
(less than 2dB)"; and of Figure 7, "There is some ripple in the response as you
would expect, but it's generally below 1dB." Its nine bands are 42, 87, 195, 420,
870, 1.95k, 4.2k, 8.7k and 15.6k Hz.

### D. Trait-critic pass — what changed in the Tier 2 table

2026-09-07. Five rows, all kept, four rewritten in place;
none needed marking unmeasured. **T1, T2, T3 and T5** each stated two or three
thresholds and disconfirmed on one, so a measurement could miss the trait
without meeting its disconfirmation — 8 dB against T3's "+9 dB or more" would
have failed the trait while sitting outside the "within 1 dB of +6 dB" the row
called disconfirming. All four now read "either/any half missed", with the old
wording kept as the limiting case that names the mechanism (constant-Q, a
non-adding bank). **T2** gains the two numbers the law of `ParametricEQ.md`
Appendix A actually predicts at the anchor `Q(12 dB) = 2`, which sits inside
this class's `Band Q` span — 1.795 oct at +3 dB
and 0.714 at +12 — so a reader can see both thresholds are floors with margin
rather than the prediction itself. **T1** gains a disconfirmation for its 8 kHz
half. **T5**'s two thresholds are traced in Appendix B, which previously covered
only T2's and T3's; the +9 dB mean is the same conservative-half construction as
T3's, and the 2 dB ripple is G8's own prose figure rather than its plot's. **T4**
passes as written — byte-identity is the strongest falsifiable form a trait can
take, and the row is already honest that it is a design rule the sources
motivate rather than a measured property of the pedal. Tier 1 block verbatim;
Tier 3 carries both boards.

### E. Palette-verifier pass — the probes behind §4 and §5

2026-09-06, CPython build of audioif (`audiocomponents/.venv/bin/python`),
audioif at `v0.2.0-14-g0b640b3`. Every line citation in §4 and §5 was
re-checked with `grep -n` against the tree at that commit; the shared probe
detail lives in `ParametricEQ.md` Appendix G and is not repeated here.

**Cites corrected:** `src/synthio/Biquad.c:45` is the `set_Q` *signature* (the
slot assignment is `:46`), and the per-block slot reads are `:79-83`, not
`:81-83`. **Confirmed as written:** `Biquad.h:21-23` for the seven modes,
`HIGH_SHELF` among them; `shared/audioif_biquad.c:88-95` for the peaking-`b2`
sign fix; `docs/upstream-diff.md:983-1020` for the per-channel biquad state.

**(i) Unity-plus gain does not exist on the palette.** `audiomixer.Mixer`
accepts `voice[0].level = 2.0`, reads it back as 2.0, and renders a 4000-peak
sine at **4000**: the limiter is `synthio_block_slot_get_limited(&voice->level,
0.0, 1.0)` at `src/audiomixer/Mixer.c:332`, and it does not raise. That is the
absence-reads-as-agreement shape `agent-knowledge/workspace-craft.md` names —
a `Gain` macro built on `Mixer.level` would test green and do nothing above
unity — so the class gate's level check must push a **known** +12 dB and
assert the level, never assert only that no exception was raised.
`audiomath.Multiply` cannot exceed unity by construction
(`shared/audioif_multiply.c:38-45`). A `HIGH_SHELF` biquad at 5 Hz,
A = 10^(12/40), measures +11.99 / +12.00 / +12.00 / +12.01 dB at
30 Hz / 100 Hz / 1 kHz / 10 kHz.

**(ii) Gain and the bank do not commute.** +12 dB shelf-gain and a −12 dB
1 kHz band, both in one `Filter`, 1 kHz sine:

| input peak | gain→bank | THD | bank→gain | THD |
|---|---|---|---|---|
| 2000 | 2003 | 0.09 % | 2009 | 0.26 % |
| 6000 | 6012 | 0.19 % | 6003 | 0.05 % |
| **12000** | 12941 | **67.3 %** | 12017 | **0.14 %** |
| 20000 | 14548 | 82.7 % | 28521 | 9.4 % |

The clamp is the biquad's own state limit at ±32767
(`shared/audioif_biquad.c:163-164`, `:174-175`) hitting the *intermediate*
section; 28521 is that limit read through the `Filter`'s ±28000 mix-down knee
(`src/audiofilters/Filter.c:288`).

**(iii) audioif#23 at this class's own settings, reproduced.** Probe shape as
`ParametricEQ.md` Appendix B — tone then zeros **inside one sample**, 200 Hz at
20000 for 0.1 s then 3 s of silence, `buffer_size` 2048, read at
+0.1/+0.5/+1/+2 s. `PEAKING_EQ` 31.25 Hz/+6 dB/Q 1.4 → **+7**; 62.5 Hz/+6 dB →
**+2**; the whole ten-band bank at +6 dB → **+5**; `LOW_PASS` 100 Hz → **+1**
(audioif#23's own figure, carried as the probe's positive control); a 1 kHz
bell → **0**, which is the negative control. Appending a stock `HIGH_PASS` to
clear the residue **adds** one: after a 20 Hz/+10 dB shelf, a 20 Hz high-pass
reads +18, a 40 Hz one +4, a 5 Hz one **−284**. `audiodynamics.Dynamics` in
`DYN_GATE` reaches exact zero only at `threshold_db=-50` (at `-70` the output
still reads −32, because a −32 LSB residue is −60 dBFS and sits under that
threshold), and it is an audioif-own node, so that composition costs the stock
tier as well as the reverb tails.

**(iv) A corner above Nyquist rails the node; it does not refuse.** 22.05 kHz
mono, one section, a 500 Hz sine at peak 1000 into a `LOW_PASS` at 16 kHz,
Q 0.707. The first two dozen output samples:

```
0, 270, 804, -200, -1181, 6431, 5120, -28521, 10715, 28520, -28521, -28521,
28520, 28520, -28521, -28521, 28520, 28520, -28521, -28521, ...
```

and it stays there for the whole render — a full-scale square wave at f_s/4.
`HIGH_SHELF` 16 kHz/+12 dB and `PEAKING_EQ` 16 kHz/+12 dB/Q 1.4 do the same, all
three reading a uniform "+17.06 dB" at every probe frequency, which is the
28521 ceiling divided by the 4000-peak probe rather than any response. **No
exception is raised at construction or at render**, and with a silent input the
same section renders exact zeros — so a build-it-and-catch test and a
silence-in-silence-out test both go green on a section that destroys any real
signal. The kit's rate sweep must therefore drive **signal**, not silence, at
22.05 kHz with the top bands engaged, and that is the planted fault for the
rate-honesty measurement: un-clamp one centre and the probe must go red.

**One warning the whole survey needs.** `src/synthio/__init__.h` **moved
between the commit vision §6 names (`7455577`) and this one**: `SYNTHIO_MAX_DUR`
was line 119 there and is line 126 here, and the mix-down range/scale pair was
`:126-127` there and is `:133-134` here. Every other file cited in §4 and §5 —
`Biquad.c`, `Biquad.h`, `audiofilters/Filter.c`, `shared/audioif_biquad.c`,
`shared/audioif_multiply.c`, `audiomixer/Mixer.c`, `docs/upstream-diff.md` — is
byte-identical across those seven commits, so their line numbers hold either
way. `LadderFilter.md` §5 and its Appendix C disagreed with each other on this
exact line, which is how the drift was found. **Seeds should state the audioif
commit their citations are against;** these do now.

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

**Notes.** `capabilities = ()` — no tempo-dependent behaviour, the transport is
not read (D10). Not stereo-by-definition; mono gets the same curve on one
channel. **Rate:** at 22.05 kHz the 16 kHz shelf and the 8 kHz band are above or
at Nyquist. They **clamp** — the shelf to just under Nyquist, the 8 kHz bell to
the highest centre a bell can hold — and the class **reports** the clamp rather
than dropping the band silently (§7 defect 4). T1 cannot hold at 22.05 kHz and
this is where that is stated. **Silence-to-zero is the invariant this class is
known to fail, and at exactly its own bands**: measured here, the 31.25 Hz band
at +6 dB / Q 1.4 settles on **+7 LSB and holds it for three seconds**, the
62.5 Hz band on **+2 LSB**, all ten bands at +6 dB together on **+5 LSB**
(`ParametricEQ.md` Appendix B) — **all three reproduced exactly by an independent
third probe in the licence-and-citation audit run**, alongside the two controls
that must read zero. That audit also found the trap this class's tail probe will
fall into: the residue exists only while the node is actually processing samples,
so a probe that lets the source *end* and then keeps pulling reads exact zeros for
every configuration, including the ones known to be dirty. The silence must be
inside the sample, and the gate needs a positive control
(`ParametricEQ.md` Appendix B). Gate 0 owns the one answer (§5).

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1** | **The top band is a shelf, the other nine are bells.** 16 kHz macro at +12 dB alone ⇒ the level at 20 kHz is within **1.5 dB** of the level at 16 kHz and at least **+9 dB**; the 8 kHz macro at +12 dB alone ⇒ the level at 16 kHz is at least **6 dB** below its own peak. | G1 and G2, two revisions, verbatim; G7's structural corroboration | high | **either half missed.** The 16 kHz band returning toward flat above its centre — more than 1.5 dB down at 20 kHz, or not reaching +9 dB at all (it is a bell, not a shelf); or the 8 kHz band still within 6 dB of its own peak at 16 kHz, which is a bank too wide for the shelf to be told apart from its neighbour | swept-sine to 22 kHz at 48 kHz, one macro at a time; report the 16 and 20 kHz levels for the shelf and the 8 kHz band's peak level and its level at 16 kHz |
| **T2** | **Proportional Q — the bands narrow as the slider travels.** For the 1 kHz band, mid-gain bandwidth at **+3 dB is ≥ 1.5 oct** and at **+12 dB is ≤ 0.8 oct**, while the first +1 dB crossing moves **less than 10 %** between them. | G3 §2; G5 for the mechanism; G4 | medium-high — the law is well sourced; the two thresholds are ours, scaled (Appendix B) | **any of the three missed.** Mid-gain bandwidth under 1.5 oct at +3 dB, or over 0.8 oct at +12 dB — in the limit a bandwidth that does not change at all across travel, which is constant-Q; or the +1 dB crossing moving > 10 %. The law of `ParametricEQ.md` Appendix A gives 1.795 oct at +3 dB and 0.714 at +12 at the anchor `Q(12 dB) = 2`, so both thresholds are floors with margin, not the prediction | swept-sine at +3, +6, +12 dB on one band; report mid-gain bandwidth in octaves and the +1 dB crossings |
| **T3** | **Adjacent bands overshoot when summed.** 500 Hz, 1 kHz and 2 kHz all at +6 dB give a combined peak of at least **+9 dB**, and the region within 3 dB of it spans more than **two octaves**. | G3 §2, fig. 6 | medium — direction and mechanism are Bohn's, the thresholds ours (Appendix B) | **either half missed.** A combined peak under +9 dB — in the limit within 1 dB of +6 dB, which is a constant-Q bank adding nothing; or the region within 3 dB of the peak spanning two octaves or less | swept-sine with three adjacent macros at +6 dB; report peak level and frequency and the −3 dB span |
| **T4** | **A band at zero is out of the circuit.** With band *k* at 0 dB and its neighbours at ±12 dB, the render is **byte-identical** to the same setting built without band *k* at all. | **Re-sourced by the audit.** G6 ("the audio gain is unity when all pots are centred", of a ten-band gyrator bank) and G5's Figure 8 ("unity gain is achieved when the slider(s) are centred"); G7's reproduction of Winer, of this exact topology: "no noise or distortion is ever contributed when the pot is centered". *G3 §3.1's grounded-centre-tap guarantee is Bohn's own **constant-Q** Case 1 and is quoted here only as the parallel, not as this pedal's mechanism (§1).* | high as a **design rule** the sources motivate — note the real pedal's own flatness claim is ±1 dB, 20 Hz–20 kHz (G1), not exactness, so byte-identity is the rebuild's bar, not a measured property of the hardware | any difference at all between the two renders | FNV digest of both builds over the full probe set, at 48 and 44.1 kHz |
| **T5** | **All ten together are smooth but hot.** Every band at +6 dB ⇒ peak-to-peak ripple from 60 Hz to 8 kHz under **2 dB**, and the mean level over that span above **+9 dB**. | G8's ripple figure on a nine-band octave gyrator EQ with every slider at maximum (Figure 7: "generally below 1dB"; text: "less than 2dB"); G3 figs. 6 and 27 | medium, and the audit narrows why: G8's unit is not a ±12 dB bank at all — its sliders run fully-off to fully-on with **no flat setting**, so its "all sliders at maximum" is a different setting from "+6 dB on every band", and the article does not say whether its curve is measured or simulated. Direction and mechanism are sourced; both thresholds are ours, the ripple bound scaled from G8 and the mean built the same conservative-half way as T3's (Appendix B) | **either half missed.** Peak-to-peak ripple **above 2 dB** over 60 Hz–8 kHz (the bands do not overlap enough to fill between their centres); or a mean level **at or below +9 dB** over that span — in the limit at or below +6 dB, which is bands that do not add at all | swept-sine with all macros at +6 dB; report ripple peak-to-peak and mean level, 60 Hz–8 kHz |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Audit, 2026-09-06.** Every row above was independently re-fetched and re-read by
the licence-and-citation audit, not taken from this seed: G1, G2 and G3 downloaded
and read with `pypdf`; G4–G8 fetched and read as HTML, each licence line read on the
page itself and, for G3/G4, chased to the hosting site's own Terms of Use. Corrections
are marked in place. Nothing in §1 or §3 was found without a source row, and one §1
sentence and one §3 trait were re-sourced because the page did not say what the seed
said it said.

*(from §3)*

Ten sections is the class's whole cost, and only non-flat bands are built (T4).
Budget as a fraction of one stereo block's deadline (256 frames, 5.33 ms at
48 kHz): **typical, four non-flat bands — P4 13 %, S3 21 %**; **worst case, all
ten non-flat plus the two level macros — P4 32 %, S3 53 %**. Arithmetic follows
`ParametricEQ.md` Appendix C from audioif's own instruction counts.
*(**Audit correction, 2026-09-06.** This line read "P4 11 %, S3 20 %" and
"P4 26 %, S3 48 %", and neither pair reproduces from the arithmetic it cites: one
stereo biquad section is 4.00 % of the S3's block and 2.40 % of the P4's, so four
sections are 16.0 % / 9.6 % raw and 21 % / 13 % with Appendix C's one-third
overhead, and ten are 40 % / 24 % raw and **53 % / 32 %** with it. The old worst
case had borrowed `ParametricEQ.md`'s **eight**-section P4 figure. The corrected
S3 number crosses half the block, which is the strongest argument in this seed for
the lean patch below — it was hidden by the wrong arithmetic.)*
**Lean patch expected: yes** — `"Ten Band - lean"` caps the bank at the five
largest-magnitude non-flat bands and reports which were dropped, rather than
compromising the faithful patch.

*(from §4)*

- Nine `PEAKING_EQ` sections and one `HIGH_SHELF` — the shelf is what makes T1
  reachable and it is already one of the seven modes
  (`src/synthio/Biquad.h:21-23`); peaking `b2` carries audioif's sign fix
  (`shared/audioif_biquad.c:88-95`).

*(from §4)*

- `frequency`, `Q` and `A` are block slots (`src/synthio/Biquad.c:46`, `:54`,
  `:62`) read once per block (`:79-83`) behind a change guard (`:87-90`), so a
  slider can be a synthio block and sweep with no Python in the loop. The
  `Filter` drives the tick (`src/audiofilters/Filter.c:281`) and scales
  `frequency` by the **running** rate (`Biquad.c:80`, the global set at
  `Filter.c:231`), so centres are stated in Hz and never pre-warped.
  *(Cites corrected in the palette-verifier pass, Appendix E.)*

*(from §4)*

- **Two-pole sections, deliberately.** Bohn's optimisation shows four-pole
  bandpass sections cancel in the middle when adjacent bands sum (G3 §4.1,
  figs. 19, 23) and that two-pole is the optimum order — so the right answer and
  the available answer coincide.

*(from §4)*

- **Q from gain, per macro move**, by the proportional-Q law derived in
  `ParametricEQ.md` Appendix A: one `sqrt` and two `10**`, never per block and
  never on a board's float path. The `Q Law` toggle swaps it for a fixed Q.

*(from §4)*

- **Clamping the centres below Nyquist is not tidiness; the node rails without
  it.** A `synthio.Biquad` over the running Nyquist is **unstable**: at
  22.05 kHz the 16 kHz band — the tenth, at its shipped centre — rails within
  ten samples into a full-scale ±28521 square wave at f_s/4, in `HIGH_SHELF`,
  `PEAKING_EQ` and `LOW_PASS` alike, **raising nothing**; on silence the same
  section renders exact zeros, so construct-and-catch and silence-in-
  silence-out both pass it (Appendix E(iv)). Tier 1's "clamp, never refuse" is
  a **stability** requirement here, and the gate must drive signal at
  22.05 kHz with the top bands engaged.

*(from §4)*

- **The two level macros are two more biquad sections, and they do not
  commute.** *(Palette-verifier correction, 2026-09-06 — this read "In a linear
  chain they commute exactly". The chain is not linear.)* Both halves measured,
  Appendix E(i)–(ii):
  - **No palette node gives gain above unity.**
    `audiomixer.MixerVoice.level` clamps to 0–1 and does so **silently**
    (`src/audiomixer/Mixer.c:332`: `level = 2.0` reads back as 2.0 and renders
    at unity, no exception), and `audiomath.Multiply` can only attenuate
    (`shared/audioif_multiply.c:38-45`). So `Gain` and `Volume` are each a
    **`HIGH_SHELF` at a subsonic corner** — 5 Hz at A = 10^(12/40) measures
    +12.00 ± 0.01 dB from 30 Hz to 10 kHz. That is **twelve** sections at the
    full bank, not ten, so Tier 3's ten-section worst case is short by two:
    nearer **P4 38 %, S3 64 %** than the 32 / 53 printed there. Flagged, not
    edited — Tier 3 is outside this pass's boundary.
  - **Order changes the sound, because the cascade saturates.** Each biquad
    clamps its state at ±32767 (`shared/audioif_biquad.c:163-164`, `:174-175`)
    and the `Filter` output passes a soft knee at ±28000
    (`src/audiofilters/Filter.c:288`, `src/synthio/__init__.h:133-134`;
    ceiling 28521). +12 dB `Gain` **before** a −12 dB band measures **67.3 %
    THD at input peak 12000**; reversed, **0.14 %**. Keeping the panel order is
    defensible — an M-108's op-amps clip too — but it is a headroom rule, not
    a commutation.

*(from §5)*

The **Tier 1** exception is inherited, not decided here: **audioif#23**, the
fixed-point biquad's held DC, bites this class at its two lowest bands —
measured **+7 LSB** at 31.25 Hz and **+2 LSB** at 62.5 Hz, held for three
seconds after silence, and **+5 LSB** with all ten bands engaged (all three
reproduced in the palette-verifier run, Appendix E). Gate 0 gives one answer
for the whole EQ family and the Phaser; `ParametricEQ.md` §5 carries this
unit's recommendation (the block-rate tail gate first, compose-first, no node)
**and the two palette compositions that were tried and refuted** — appending a
stock `HIGH_PASS`, which adds a larger residue of its own (a 5 Hz high-pass
after a 20 Hz/+10 dB shelf reads −284 LSB where the shelf alone reads −32), and
gating with `audiodynamics.Dynamics`, which zeroes the residue only at a
−50 dBFS threshold and moves the class off the stock tier. If a float biquad
node lands instead, this class's tier moves to **audioif** and §4's node list
changes; nothing else here does.

*(from §7)*

2. **Every band is a bell, including the top one.** `GraphicEQ.__init__` hands
   all ten to `ParametricEQ`'s `bands=` argument (`eq.py:93-95`), which builds
   `PEAKING_EQ` only (`eq.py:47-49`). **T1 is not implemented at any setting.**

*(from §7)*

4. **Bands above Nyquist are dropped silently** — `if abs(gain) > 0.01 and
   freq < limit` (`eq.py:95`) with `limit = _core.sample_rate() * 0.5`
   (`eq.py:92`): at 22.05 kHz the top two bands vanish and nothing says so. That
   is the workspace's signature failure shape, absence reading as agreement;
   Tier 1 says clamp and report.

*(from §7)*

5. **Centres are the ISO preferred series** (`ISO_BANDS`, `eq.py:67-68`: 31.5,
   63.0, …) where the standout's are exact octave doublings from 31.25 Hz
   (G1, G2) — musically small, worth getting right, and worth not hard-coding at
   module level where a constructor cannot reach it.

*(from §7)*

6. **Inherited from `ParametricEQ`:** `check_hz()` refuses instead of clamping
   (`eq.py:48`, raise at `_core.py:471-474`); the all-flat case returns the
   source itself (`eq.py:56-61`) and so takes a different path through
   `reset()`/`deinit()` (`_core.py:368`, `:380`); `Effect.__new__` mutates
   module-wide format state (`_core.py:149-152`).

*(from §1 — the seed's paragraph in full, with the audit corrections it
carried in place. Moved here at Station A under the length rule; §1 keeps the
substance and every source id.)*

The M-108 is **ten band sections whose sliders vary the gain of one op-amp
stage across a tuned circuit**, boosting when the wiper sits toward the
feedback end and cutting when it sits toward the input, with **unity gain at
the centre detent**: without the frequency-selective network "the pot sliders
simply vary the gain of the circuit and unity gain is achieved when the
slider(s) are centred" (G5), a bank of ten of them has "audio gain … unity
when all pots are centred" (G6), and of exactly this topology Winer's 1982
description says "no noise or distortion is ever contributed when the pot is
centered" (G7). Nine of the ten are **gyrator** bandpass sections — an op-amp
simulating an inductor, `L = R2 × R1 × C1`, `Q ≈ 2π·f₀·L / R2` (G6) — at
**31.25, 62.5, 125, 250, 500, 1k, 2k, 4k and 8 kHz**, each ±12 dB; the tenth
is a **±12 dB shelf at 16 kHz** on both specification sheets (G1, G2) and
corroborated by a schematic reading finding nine active filters and "the last
(16 kHz) is a passive filter" (G7). The behaviour that defines it is the one
Bohn wrote a paper about: the tuned circuit is loaded by the slider, so **Q
moves with the slider** — the band is narrow **only at the extremes**, and at
low boost "the conventional design's bandwidth is in excess of one octave …
it has degraded into something nearer to a 10-band octave equalizer" (G3 §2).
Bands therefore overlap and add: three adjacent sliders at +6 dB give a
conventional design +12.5 dB over 2.5 octaves against a constant-Q design's
+6 dB over one octave (G3 §2, fig. 6). Around the bank are two more sliders,
**GAIN** and **VOLUME**; G1, G2 and G7 give **neither a dB range nor a
position in the signal path**, so "GAIN before the bank, VOLUME after, each
±12 dB" is this dossier's design choice, not a fact about the pedal. The
pedal runs on 18 V; its sheet gives a frequency response of "±1 dB, 20 Hz to
20 kHz" (G1).

*(The audit corrections behind this paragraph are in **App. R**, verbatim.)*


*(from §4 — the seed's palette bullets in full, as Station A found them.
Superseded by §4's audioif-tier mapping; kept because the arguments about
section order, the four-pole question and the block-slot reads are unchanged
by the node swap.)*

**Twelve chained `audiobiquad.Biquad` nodes.** Head to tail: `Gain`
(HIGH_SHELF at 5 Hz) → nine `PEAKING_EQ` bells at 31.25 Hz × 2ⁿ → one
`HIGH_SHELF` at 16 kHz → `Volume` (HIGH_SHELF at 5 Hz). Python computes each
band's `Q` from its gain on a macro move; C runs every sample. Nothing is
added to the palette.

- **Why `audiobiquad` and not the stock bank.** The seed's tier was stock
  *conditionally*, and the condition fired. On `audiofilters.Filter` over
  `synthio.Biquad` this class holds **+7 LSB** after silence with the
  31.25 Hz band at +6 dB and **+5 LSB** with all ten — reproduced here
  (App. S(i)), a third independent reproduction of audioif#23's figures. On
  `audiobiquad` every one of those reads **exact zero**.
- **The composition the seed refuted, re-tried and now half-rehabilitated.**
  §5 recorded that appending a **stock** `HIGH_PASS` to clear the residue
  adds a larger residue of its own. An `audiobiquad` high-pass at 5 Hz behind
  the stock bank *does* clear it to exact zero (App. S(iii)) — so the seed's
  refutation is correct about the stock node and wrong if read as being about
  any high-pass. It is not the design here anyway: it leaves a node holding
  DC forever and hides it at the output, and it costs the same twelve
  sections.
- **A flat band is a `mix = 0` wire, not an unbuilt node** — and that is what
  makes T4 reachable at all. A `PEAKING_EQ` section at `gain_db = 0` is *not*
  bit-transparent at this bank's lowest centres: over 24 000 frames of noise
  it deviates by up to **5 LSB at 31.25 Hz**, 2 at 62.5 Hz and 1 at 125 Hz,
  and is exact from 250 Hz up (App. S(iv)) — Direct Form I in float32 with
  poles that close to z = 1. At `mix = 0` the kernel computes
  `1.0f * x0 + 0.0f * y0` (`audioif_filter_f32.c:240`), which is the input
  sample exactly, so the section is byte-exact a wire at every centre and
  every rate. **Every band is built; a band at the detent is muted, not
  absent.** That is stronger than the seed's "flat bands are not built": the
  node is there, so a host can turn the knob.
- **The detent is one macro step wide.** ±12 dB over 0–127 makes one step
  0.189 dB, so codes 63 and 64 land at ∓0.094 dB and nothing else is within
  0.1 dB of zero. `|gain| < 0.1 dB` is therefore exactly the two centre
  codes — the M-108's mechanical centre detent, in the macro's own units.
- **Q from gain, per macro move**, by `ParametricEQ.md` Appendix A's law,
  rearranged so the anchor is a macro:
  `Q(G) = Q₁₂ · sqrt((A² − L²/A²) / (A₁₂² − L²/A₁₂²))`, `A = 10^(|G|/40)`,
  `L = 10^(1/20)` (a 1 dB skirt). One `sqrt` and one `10**` per move, never
  per block. At `Q₁₂ = 2` it reproduces Appendix A's table to three decimals
  — 0.532 / 0.754 / 1.220 / 1.609 / 2.000 at 2 / 3 / 6 / 9 / 12 dB
  (App. S(v)). Below +1 dB the law has no root (a 1 dB skirt cannot sit on a
  1 dB bell) and `Q` floors at the kernel's own 0.05, which is the limit of
  the law, not a fudge. `Constant Q` swaps the whole law for `Q₁₂`.
- **Two level macros, two more sections, because no palette node gives gain
  above unity.** `audiomixer.MixerVoice.level` clamps to 0–1 *silently*
  (`src/audiomixer/Mixer.c:332`) and `audiomath.Multiply` can only attenuate
  (`shared/audioif_multiply.c:38-45`). A HIGH_SHELF at 5 Hz with
  `gain_db = +12` measures **+12.00 dB at 30 Hz, 100 Hz, 1 kHz and 10 kHz**
  (App. S(vi)); at a 10 Hz corner 30 Hz is already 0.22 dB short, and at
  20 Hz 2.3 dB short, which is why the corner is 5 Hz and not "subsonic,
  roughly".
- **Panel order is kept, and it is a headroom rule, not a commutation.**
  Gain sits before the bank and Volume after, as the panel reads. Each node
  writes int16 between sections and `to_s16` **saturates** at ±32767
  (`audioif_filter_f32.c:43-50`), so +12 dB of Gain into a hot source clips
  at the first node boundary — an M-108's op-amps clip too, and the
  docstring says so in the musician's terms.
- **Clamping the centres below Nyquist is stability, not tidiness.** The
  ported `synthio.Biquad` over Nyquist rails into a full-scale square wave
  at f_s/4 while raising nothing, and renders exact zeros on silence, so
  construct-and-catch and silence-in-silence-out both pass it (App. E(iv)).
  Every centre goes through `self._hz()`, which clamps at 0.98 × Nyquist.
- **Mono:** the same curve on one channel. Not stereo by definition.


### S. Station A bench — the probes §§3, 4 and 6 rest on

2026-09-07, `audiocomponents/.venv/bin/python` with
`PYTHONPATH=ac-wt-graphiceq/lib`, audioif at the pin `2f6cbc3`. Every probe
here drives its source through an `audiofilters.Filter(filter=None, mix=1)`
adapter played `loop=False`, which is `tools/render_effect.py`'s own
re-blocking seam — **the first draft of these probes fed an
`audiocore.RawSample` straight in, it looped, and every "tail" reading was
the probe playing again.** The scripts are transcribed in the evidence pack;
the numbers below are what they printed.

**(i) The tail, three compositions, burst then in-sample silence.** 200 Hz at
peak 20000 for 0.1 s, then 3.0 s of digital silence, 48 kHz stereo; the value
is the last sample of the render. `tools/phase2_probes/graphiceq_bench.py`
prints all six of these.

| bank | all ten at +6 dB | 31.25 Hz at +6 dB | all flat |
|---|---|---|---|
| ten chained `audiobiquad.Biquad` | **0** | **0** | **0** |
| one `audiofilters.Filter`, ten `synthio.Biquad` | **+5** | **+7** | 0 |
| the same, then an `audiobiquad` HIGH_PASS at 5 Hz | **0** | **0** | 0 |

The middle row reproduces audioif#23 at this class's own settings for the
third independent time (the seed's Appendix E(iii), and the licence audit's
own probe, are the first two). The top row is why the tier moved.

**(ii) Ring-down, for `TAIL_SAMPLES`.** All ten bands at +12 dB, `Band Q` 2.0,
40 Hz burst at peak 24000 for 0.25 s, then silence; the frame of the last
non-zero sample, minus the burst end:

```
48000 Hz: tail 22314 frames (464.9 ms)
44100 Hz: tail 20520 frames (465.3 ms)
22050 Hz: tail 10262 frames (465.4 ms)
```

Constant in time, so the class reports `int(rate * 0.47)` rather than one
number — 22560 / 20727 / 10363, each above its measurement.

**(iii) The seed's refuted composition, re-tried.** §5 recorded that
appending a **stock** `HIGH_PASS` to clear the residue adds a larger residue
of its own — a 5 Hz stock high-pass after a 20 Hz/+10 dB shelf reading −284
LSB where the shelf alone read −32. An **`audiobiquad`** high-pass is a
different node and does not do that:

```
  1.0 Hz high-pass on a held +7 LSB: last sample 0
  5.0 Hz high-pass on a held +7 LSB: last sample 0
 20.0 Hz high-pass on a held +7 LSB: last sample 0
```

and behind the stock ten-band bank the reading in (i) goes from +5 / +7 to
**0**. So the seed's refutation is right about the ported node and would be
wrong if read as being about any high-pass. **It is still not the design**:
it leaves a node holding DC for ever and hides it at the output, and it costs
the same twelve sections. *(This probe's own first draft ran the DC for
exactly the length of the render and read −7 / −6 / −4 — the trailing edge of
its own stimulus, the adapter having begun handing out silence. The DC now
runs a second longer than the render, and the note is in the script.)*

**(iv) A flat section is not a wire at the bottom of this bank.** One
`audiobiquad.Biquad`, `PEAKING_EQ`, `Q = 1.4`, `gain_db = 0`, `mix = 1`, over
24 000 frames of deterministic noise at peak 8000, against the bare source:

```
    31.25 Hz: 39316 differing samples, first at 1414, worst 5
    62.50 Hz: 18680 differing samples, first at  520, worst 2
   125.00 Hz:  1078 differing samples, first at 12024, worst 1
   250 Hz .. 16 kHz: 0 differing samples
```

Ten *chained* flat sections at 1 kHz differ in **0** samples, so this is not
about depth: it is Direct Form I in float32
(`audioif_filter_f32.c:222-241`) with poles that close to z = 1, where
`b == a` exactly and the cancellation still loses the last bits. At
`mix = 0` the same section is byte-identical to the source at every centre
tested, which is what §4 builds on and what T4's planted fault inverts.

**(v) The Q law reproduces `ParametricEQ.md` Appendix A.** At `Q₁₂ = 2`,
`L = 1 dB`:

```
1 dB: 0.050 (floored)   2 dB: 0.532   3 dB: 0.754
6 dB: 1.220             9 dB: 1.609  12 dB: 2.000
```

Appendix A's table reads 0.532, 0.754, 1.220, 1.609, 2.000 at the same
gains. The rearrangement in §4 is therefore the same law, not a new one.

**(vi) A subsonic HIGH_SHELF is a clean broadband gain, and the corner
matters.** `gain_db = +12`, `Q = 0.707`, wet-minus-dry RMS on a sine at each
frequency:

| corner | 30 Hz | 100 Hz | 1 kHz | 10 kHz |
|---|---|---|---|---|
| 2 Hz | +12.04 | +12.00 | +12.00 | +12.00 |
| **5 Hz** | **+11.97** | **+12.00** | **+12.00** | **+12.00** |
| 10 Hz | +11.84 | +12.00 | +12.00 | +12.00 |
| 20 Hz | +9.71 | +11.98 | +12.00 | +12.00 |

5 Hz is the corner the class uses, at `Q = 0.707`: 0.03 dB short at 30 Hz and
exact from 100 Hz up, against 0.16 dB at a 10 Hz corner and 2.3 dB at 20 Hz.
The 2 Hz row *overshoots* — a shelf has its own Q and the corner is below the
band, so pushing it lower is not monotonically better. The seed's Appendix
E(i) measured +12.00 ± 0.01 dB on the *ported* shelf; this is that reading
re-taken on the node the class actually builds.

**What this bench does not show.** No board. No P4 or S3 figure in §3 comes
from a measurement, and the twelve-node chain's per-block overhead cannot be
seen from the desktop at all, because the desktop's `audiobiquad` is a Python
shim over the same kernel the board runs natively.
