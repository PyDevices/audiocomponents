# Accuracy Dossier — `karplus` (Karplus-Strong plucked string)

**Module:** `audiocomponents/lib/audioinstruments/karplus.py` (214 lines)
**Survey's grade:** gold (`accuracy-survey.md:44`, `:915-929`)
**Proposed grade:** **literature — downgraded from the survey's gold.**
**Reference settings (D3):** N/A for the reason this dossier exists (§0) —
the settings-documented capture the survey counted toward D3's 14-instrument
list is not being used as this instrument's reference at all.

## 0. The finding that changes the grade

The task brief's risk was right to flag: **Karplus-Strong is an algorithm,
not a machine, and this session found no hardware that ever shipped it.**
That is not "not yet found" — it is affirmatively closed, in the words of
the algorithm's own co-inventor:

> "I have yet to see a product on the market from any of them using the
> technology." — Kevin Karplus, on his own algorithm history page
> (https://users.soe.ucsc.edu/~karplus/digitar.html, fetched this session)

The same page states the patent (US 4,649,783, plus Australian 570,669 and
Canadian 1,215,869) was licensed first to Mattel Electronics, which "failed
as a company before any product using the algorithm was developed," and a
successor startup founded by ex-Mattel staff never secured funding either.
Wikipedia's "Karplus–Strong string synthesis" article (CC BY-SA 4.0,
https://en.wikipedia.org/wiki/Karplus%E2%80%93Strong_string_synthesis,
fetched this session) independently corroborates the Mattel collapse, adds
that Yamaha later licensed the technology as part of the Stanford "Sondius"
patent package, and states plainly: "It is unknown whether any hardware
using the algorithm was ever sold." It lists modern Eurorack modules (Moog,
Mutable Instruments, Arturia) that invoke Karplus-Strong *principles* but
explicitly notes they "may not adhere strictly to the algorithm" — proxy
candidates for a different, later design tradition, not a capture of *this*
algorithm's own hardware, because none exists.

Three independent sources this session (the algorithm's co-author in his
own words, Wikipedia, and the absence of any product mention anywhere in
CCRMA's textbook chapter on the algorithm) agree: **there is no
"Karplus-Strong machine" for tier 1 of the hierarchy to apply to.**

**What the survey did instead:** it reasoned that since no KS hardware
exists, the algorithm's "real hardware analog is the physical instrument it
emulates: a plucked string," and graded gold on a real guitar capture (the
University of Iowa's Raimundo 118 classical-guitar recordings) on that
basis. Re-reached and re-read this session — the capture itself checks out
exactly as the survey described (§1, §2) — but the reasoning that makes it
*gold* does not survive scrutiny, for the same category of reason the task
brief anticipated:

- `karplus.py`'s own inline commentary describes what it is building as
  "the real Karplus-Strong algorithm" (`karplus.py:52-56`) — a specific,
  deliberately simplified DSP technique — not an attempt at photorealistic
  guitar-body physical modeling. That more ambitious goal belongs to a
  different family in this same library (`vl1`, digital waveguide
  synthesis), and even *that* instrument was argued down to literature
  because no capture of the *actual* modeled hardware (a Yamaha VL1) could
  be reached (`accuracy-survey.md:1069-1075`) — real clarinet/wind
  recordings were correctly *not* treated as a stand-in gold reference
  there. The same logic applies here with the roles reversed: a real guitar
  is not a capture of "the machine" `karplus.py` implements, because that
  machine doesn't exist to be captured.
- The algorithm's own literature is explicit that this gap is deliberate,
  not an oversight to be measured away. Jaffe & Smith's 1983 extension
  (described secondhand via CCRMA, §1) exists specifically because the
  bare 1983 loop is audibly short of a real string in named, itemized ways
  — pick direction, pick position, string damping/stiffness, tuning,
  dynamic-level brightness. Measuring the module against a real guitar
  recording would be measuring it against a standard its own founding
  papers say the bare algorithm isn't trying to meet outright. It's a
  useful sanity check ("does this still sound like a plucked string at
  all?"), not a gold-tier fidelity oracle.

**Conclusion:** gold doesn't fit this instrument's category, and forcing it
to fit — capture-shaped grade for a reference that has no capture-shaped
target — is exactly the grade inflation this pass exists to catch. Dropped
to **literature**: the algorithm's own founding and extending papers, plus
a permissively-licensed reference implementation, are the correct ceiling
for an instrument whose only real "reference" is a published algorithm.

## 1. Reference and grade

**Tier 1 (hardware capture):** searched and closed, not merely unreached —
see §0. No paywalled hardware-KS capture exists to record either, because
there is no hardware-KS product at any price. (The UIowa guitar pack itself
is free/unrestricted, not paywalled — recorded below as a real, well-
licensed source, just not a tier-1 one for *this* instrument.)

**Tier 2 (literature), reached this session:**
- The founding paper itself, previously unreached by the survey (it
  reported JSTOR-gated, 404s and timeouts): Karplus, K. & Strong, A.
  "Digital Synthesis of Plucked-String and Drum Timbres," *Computer Music
  Journal* 7(2), Summer 1983, pp. 43–55 — self-archived by co-author Kevin
  Karplus at https://users.soe.ucsc.edu/~karplus/papers/digitar.pdf,
  **fetched this session** (395 KB PDF, confirmed retrieved). The file is a
  scanned image (JBIG2-encoded); its text could not be machine-extracted,
  so it is recorded as *reached* but not *read in detail* — citation and
  companion-page corroboration (below) are what this dossier draws from it,
  not paragraph-level content.
- CCRMA's "The Karplus-Strong Algorithm"
  (https://ccrma.stanford.edu/~jos/pasp/Karplus_Strong_Algorithm.html,
  fetched this session): describes the delay-line-plus-averaging-filter
  structure directly — random-noise-filled delay line, output formed by
  averaging adjacent samples each pass (the "one-zero" loop filter), noise
  optionally lowpass-filtered before injection as a dynamic-level/
  brightness control. Matches `karplus.py`'s own implementation almost
  exactly (`karplus.py:59-108`: noise-filled buffer, per-lap
  `avg = (cur + prev) * 0.5 * fb` loop filter).
- CCRMA's "The Extended Karplus-Strong Algorithm"
  (https://ccrma.stanford.edu/~jos/pasp/Extended_Karplus_Strong_Algorithm.html,
  fetched this session; cites Jaffe & Smith 1983): names the standard
  refinements over the bare algorithm — pick-direction filter, pick-
  position comb filter, string-damping filter, string-stiffness allpass,
  string-tuning allpass (fractional-delay pitch correction), dynamic-level
  lowpass. `karplus.py` already implements the pick-position comb
  (`karplus.py:73-75`, subtracting a delayed copy of the burst from
  itself — matches EKS's H_β description exactly) and a per-lap damping
  filter (`karplus.py:76-108`). It does **not** implement a tuning allpass
  for fractional-sample delay — see §6.
- *oss*: STK (Synthesis ToolKit in C++), `src/Plucked.cpp`
  (https://raw.githubusercontent.com/thestk/stk/master/src/Plucked.cpp,
  fetched this session): "a simple plucked string physical model based on
  the Karplus-Strong algorithm," explicitly flagging patent coverage
  ("at least two patents, assigned to Stanford, bearing the names of
  Karplus and/or Strong"). Loop filter (`loopFilter_`) plus `loopGain_`
  (0.995–0.99999) for decay; `pluck()` injects filtered noise, with the
  pick filter's pole and gain both keyed off amplitude (brighter/louder at
  higher velocity) rather than a separate onset layer. **No explicit pick-
  position control** in this class (per this session's read) — `karplus.py`
  actually implements pick position more closely to the EKS literature
  than STK's base `Plucked` class does; STK may have a sibling class that
  models it (not checked this session, out of scope once the license
  question was already settled by `Plucked.cpp`/`LICENSE` directly).

**What this makes the grade.** Tier 1 does not apply to this instrument
(§0) — not a gap to be filled later, a structural fact about what
Karplus-Strong is. Tier 2 is reached, complete enough to derive the
algorithm precisely (this is the unusual case in this program where the
literature *is* the primary source, not a step removed from a physical
device), and corroborated by a permissively-licensed working
implementation. Per the hierarchy (vision §4), that is **literature**.

## 2. License call, per source

| Source | License as read | Where read |
|---|---|---|
| Karplus & Strong 1983, "Digital Synthesis of Plucked-String and Drum Timbres" (self-archived PDF) | license unverified — no rights/terms statement on the hosting page; self-archived by a co-author on his own faculty page, treated per the license gate as read-for-citation/description only, not a portable-code source | https://users.soe.ucsc.edu/~karplus/digitar.html and the linked PDF (both fetched this session) |
| CCRMA, "The Karplus-Strong Algorithm" (ch. 9, *Physical Audio Signal Processing*, J.O. Smith III) | All rights reserved — Copyright Julius O. Smith III / W3K Publishing, 2010; read for algorithm math/description only (vision §5: reading published math creates no derivative work) | https://ccrma.stanford.edu/~jos/pasp/Karplus_Strong_Algorithm.html (fetched this session) |
| CCRMA, "The Extended Karplus-Strong Algorithm" (same book, cites Jaffe & Smith 1983) | Same as above — All rights reserved, read for math/description only | https://ccrma.stanford.edu/~jos/pasp/Extended_Karplus_Strong_Algorithm.html (fetched this session) |
| STK, `src/Plucked.cpp` | MIT ("Permission is hereby granted, free of charge, to any person obtaining a copy of this software..."; non-binding request that modifications be sent back upstream) — permissive, portable **and could be ported**, not just measured, per vision §5 | https://raw.githubusercontent.com/thestk/stk/master/LICENSE (fetched this session) |
| University of Iowa Electronic Music Studios — Guitar (Raimundo 118, Brian Penkrot, Dec 2011) | Explicit unrestricted-use grant: "these recordings have been freely available on this website and may be downloaded and used for any projects, without restrictions." Real, usable, well-provenanced — but not the instrument's reference; see §0 for why it is not counted toward the grade | https://theremin.music.uiowa.edu/MIS.html (fetched this session; per-file settings on https://theremin.music.uiowa.edu/MISguitar.html, also fetched this session) |
| Wikipedia, "Karplus–Strong string synthesis" | CC BY-SA 4.0 | https://en.wikipedia.org/wiki/Karplus%E2%80%93Strong_string_synthesis (fetched this session) |

Nothing above is ported into `karplus.py`. STK's MIT license would in
principle permit porting `Plucked.cpp`'s loop-filter/pluck logic directly,
but the module's existing implementation already independently reaches the
same algorithm from the papers (and, on pick position, is closer to the
EKS literature than STK's base class) — no porting is proposed.

## 3. What "the machine" is — there isn't one

Mechanically, Karplus-Strong is a digital delay-line/feedback loop, not a
physical object: fill a buffer of length `sample_rate / f0` with noise,
then repeatedly read a sample out, average it with the previous sample
(a one-zero lowpass), write the averaged value back into the same slot,
and output the running stream (§1). High harmonics die faster than the
fundamental every pass, producing a decaying, pitched pluck — the "physics"
is entirely in the loop's arithmetic, not in any string, pickup, or
circuit that could be photographed, schematic'd, or captured on tape as
"the karplus." §0 establishes there is no commercial hardware unit that
ever ran this loop.

`karplus.py`'s own build comment states this plainly and correctly
(`karplus.py:52-56`): "The real Karplus-Strong algorithm: fill a delay line
... with noise, then repeatedly read it back and feed each sample into a
leaky lowpass ... before writing it back into the same slot." That is a
correct, literature-accurate one-sentence description of the algorithm —
the module was evidently built with real understanding of the source
material, whether or not that source was recorded at the time (the
micropython-vst3 archaeology quick-look elsewhere in the survey found no
provenance notes for this instrument specifically, and none were sought
fresh this session — out of scope for a dossier, in scope only for the
one-time history quick-look).

## 4. Voice structure and polyphony

**Hardware:** none exists (§0), so there is no sourced polyphony number to
check the module against. The survey's own fallback reasoning — that the
algorithm's "most natural physical referent, a standard 6-string guitar...
is itself 6-voice-capable" (`accuracy-survey.md:927`) — is carried forward
here as the same kind of *inference*, not upgraded to a citation: it is
not a hardware fact, it is an analogy to the instrument most commonly used
to demonstrate the technique (and the one the UIowa capture happens to be).
Re-confirmed this session: the UIowa capture set does document all six
guitar strings (E, A, D, G, B, high E) by filename, which is the entire
basis for "6."

**Module:** `MAX_VOICES = 6` (`karplus.py:142`), an arbiter over held notes
(`karplus.py:159-160`, `steal_oldest()` on overflow). Given no reference
number exists to check it against, **no mismatch can be claimed in either
direction** — 6 is neither confirmed correct nor confirmed wrong. It is a
reasonable, self-consistent choice (matches the guitar analogy, matches
the capture set used for corroboration) and no change is proposed on
today's evidence.

## 5. Proposed acceptance criteria

Because the reference is the algorithm's own literature rather than a
hardware capture, criteria here are "does the implementation match the
published algorithm's structure and named refinements," not "does it match
a measured waveform." Where the UIowa guitar recordings are cited below,
they are used only as a general plausibility check (§0), never as a
pass/fail target.

| # | Criterion | Target (source) | Status |
|---|---|---|---|
| 1 | Loop filter is a one-zero average of adjacent samples, feedback gain < 1 sets decay rate | CCRMA, Karplus-Strong Algorithm chapter (§1) | **already matches** — `avg = (cur + prev) * 0.5 * fb` (`karplus.py:93-95`) is exactly this filter; `fb = 0.90 + damping*0.09` (`karplus.py:76`) is the macro-controlled decay-rate knob |
| 2 | Pick-position comb filter subtracts a delayed copy of the excitation from itself | EKS's H_β (§1) | **already matches** — `karplus.py:73-75`, and the module's own inline note explains why it reads from a separate copy (`src`) rather than `buf` itself, to keep the notch a clean single subtraction rather than an unintended recursive comb |
| 3 | Pitch is set by delay-line length in samples, `≈ sample_rate / f0` | basic KS algorithm (§1) | **already matches, with a known literature-flagged limitation** — `delay_len = int(SR / hz)` (`karplus.py:58`) truncates to an integer sample count with no fractional correction; see §6 |
| 4 | Excitation is a full-spectrum noise burst, optionally shaped for dynamic level | basic KS + STK's `pluck()` (§1) | **already matches in spirit, different mechanism** — the module uses a *separate* short high-pass-filtered noise layer (`env_pick`/`hp_pick`, `karplus.py:173-174`) driven by the `Pick Hardness` macro, rather than STK's approach of varying the loop filter's own pole/gain by amplitude; not a literature violation (EKS treats "dynamic-level filter" as one of several valid places to put this), but worth an A/B ear-check at Station B against the "hardness" macro specifically |
| 5 | General plausibility: rendered output should sound like *a* plucked string, not merely filtered noise | UIowa guitar recordings, used qualitatively only (§0) | **measurable now** — spectral/decay shape comparison for sanity, not a fidelity target |

## 6. What the module would need to change — read, not measured

Read from `karplus.py` only; nothing below was rendered or listened to
this pass.

- **No fractional-delay tuning allpass.** `delay_len = max(4, min(KS_TABLE_LEN,
  int(SR / hz)))` (`karplus.py:58`) truncates to an integer number of
  samples. At 48 kHz this makes the achievable fundamental quantized in
  steps that widen with pitch — a well-known, literature-named limitation
  of the bare algorithm (EKS's string-tuning allpass, H_η, exists
  specifically to correct it via a fractional-sample delay, §1). Not
  proposed as a required fix — the literature treats this as an optional
  refinement, and the effect is small in the mid-range most patches will
  actually use — but it is the one concrete, sourced gap between this
  module and the *extended* algorithm it otherwise already implements
  closely (pick position, per-lap damping).
- **Dynamic-level (velocity) brightness is a separate noise layer, not a
  loop-filter modulation.** Per §5 item 4, this is a legitimate
  implementation choice within the literature, not an error — flagged as
  worth an ear-check, not a proposed rewrite.
- **The toolkit expansion is available but unused here**, same finding as
  other dossiers in this program: no `audiodynamics`/`audiofilters`
  downstream stage is used; the whole voice is two `synthio.Note` layers
  (body + pick transient) through per-note `Biquad`s (`karplus.py:169-175`).
  No specific toolkit addition is proposed on today's evidence — the
  literature's refinements (pick direction, stiffness allpass, tuning
  allpass) are more naturally table/delay-line changes than new audioif
  nodes.

## 7. MCU budget and macro budget

**A real, code-visible MCU cost, flagged here for the record even though
this dossier proposes no structural change:** `karplus_strong_table()`
(`karplus.py:49-128`) rebuilds a full `KS_TABLE_LEN = 8192`-sample table
**in pure Python, on every note-on** — three full passes over up to 8192
elements (noise fill, `delay_len`-sized comb pass, the main averaging
loop) plus a final int16 scale-and-copy pass, with no `ulab`/NumPy
vectorization (none is used anywhere in this file — confirmed by reading;
consistent with the portability rule, but pure-Python loops of this length
are the more expensive path on a small MCU). The file's own comment marks
`KS_TABLE_LEN`'s value as chosen to "bound the per-note-on cost"
(`karplus.py:47`), so the author was aware of the cost, not blind to it.
Station B should measure actual per-note-on latency on an M0+/M4 target
before deciding whether a `" - lean"` patch (e.g., a smaller `KS_TABLE_LEN`,
or a precomputed/cached table set for common pitches) is needed — **not
measured this pass**, read from code only.

`MACRO_LABELS` carries 7 of 16 slots (`karplus.py:9-16`) — nine free. **No
new macro is proposed**: nothing in §6 calls for a front-panel control the
current seven (Volume, Pluck Position, String Damping, Body Resonance,
Pick Hardness, Decay, Master Tune) don't already cover. `PATCHES` has one
entry (`karplus.py:27-29`), well within the 128-patch ceiling.

## 8. What was not found, stated plainly

- No hardware Karplus-Strong product exists to find — closed, not merely
  unreached (§0).
- Jaffe & Smith's 1983 extension paper itself was not independently
  reached this session (same gap the survey reported) — its content here
  is entirely secondhand via CCRMA's description, which cites it directly.
- The 1983 Karplus & Strong CMJ paper was reached this session (a new find
  relative to the survey, which reported it JSTOR-gated/dead-link) but
  only as an unparseable scanned PDF — its exact wording was not read,
  only its existence, citation, and companion-page context.
- STK's sibling classes beyond `Plucked.cpp` (e.g., any that might model
  pick position or two-polarization string coupling) were not checked this
  session — the license question was already settled by `Plucked.cpp`/
  `LICENSE` directly, and going further wasn't needed to reach a grade.
- No paid/paywalled source is recorded — none was found to paywall, since
  there is no hardware category to paywall (§0). This is not a budget
  shortfall; it's the honest shape of this particular instrument.

**Awaiting Gate A:** `APPROVE ACCURACY DOSSIER karplus`
