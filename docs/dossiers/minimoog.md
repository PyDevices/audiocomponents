# Accuracy Dossier — `minimoog` (Moog Minimoog Model D)

**Module:** `audiocomponents/lib/audioinstruments/minimoog.py` (177 lines)
**Survey's grade:** gold (`accuracy-survey.md:48`, `:258-268`)
**Proposed grade:** **literature — held down from the survey's gold.**
**Reference settings (D3):** no known-knob capture was found this session
either; every criterion below is qualitative/literature-derived, consistent
with the survey's own D3 finding for this family
(`accuracy-survey.md:264`).

## 0. The finding that changes the grade

The survey's gold rested on one capture — Monosounds' "100+ Free Minimoog
Model D Samples Vol. 1" — plus three corroborating tier-2/tier-3 sources. This
pass re-fetched all four this session and could not sustain the capture as
gold-tier evidence, for a reason different in *kind* from the pianet/cp70
drops: those were captures of a verifiably real but wrong machine; this one's
claim to be *hardware at all* does not hold up.

**What the product page actually says, fetched fresh this session
(https://monosounds.studio/product/100-free-minimoog-model-d-samples-vol-1/):**
"Every sample in Vol.1 was recorded directly from a hardware Minimoog Model D
through a professional signal chain." That is the entire provenance
statement — no unit photo, no serial number, no engineer credit, no stated
era (see below), nothing beyond the sentence itself.

**Why that sentence doesn't clear the bar, on its own evidence:**

- **The seller's own business is not hardware capture.** Monosounds'
  homepage (fetched this session, https://monosounds.studio/) describes the
  company as "Serum 2 presets, sample packs & MIDI, made by one working
  producer," and its front page markets Serum 2 presets and plugin content
  as the flagship product line, not hardware recording. The Minimoog claim
  is a single line on one product page from a one-person software-preset
  shop, not a house whose credibility rests on hardware capture the way
  Samples From Mars' or Legowelt's does (see below).
- **A real Minimoog Model D is a $5,000–$25,000 instrument.** Vintage
  1970s units run $8,000–$25,000+ and even the 2016/2017 reissue now
  resells for $4,999–$7,000+, per multiple listings surveyed this session
  (Reverb, Curio Comp, ModWiggler — search results only, not independently
  read page-by-page, so recorded as a price range from multiple
  corroborating listings rather than one authoritative source). That is a
  real cost barrier for a single-producer freebie-marketing pack, and
  raises rather than answers the question the task asked to check: is this
  a genuine Minimoog Model D, a much cheaper Behringer "Model D" clone
  (US $399, a different manufacturer's circuit reproduction, not Moog's
  own — confirmed via Synthtopia's coverage,
  https://www.synthtopia.com/content/2017/04/22/behringer-399-minimoog-model-d-clone-hands-on-demo/,
  fetched this session), or a plugin? The page does not say, and nothing
  found this session resolves it either way — this is a genuine "cannot
  confirm" rather than a disproof.
- **The era is unstated, and — unlike Pianet's pickup swap — that gap
  matters less than it first appears.** "Minimoog Model D" names both the
  1970–1981 original and Moog Music's own 2016/2017 reissue. Retailer copy
  for the reissue (Vintage King, Perfect Circuit — fetched this session)
  states "the signal path is identical to Robert Moog's original design...
  the exact same three-oscillator monophonic sound engine, rich low-pass
  ladder filter and saturating mixer section... the exact circuit boards
  retain the same component placement and through-hole design," with the
  reissue's additions (independent LFO, MIDI, aftertouch-sensitive keybed)
  being auxiliary, not core-signal-path changes. This is retailer marketing
  copy, not Moog's own primary spec sheet — Moog's own product page
  returned only navigation/footer content to this session's fetch
  (https://www.moogmusic.com/synthesizers/minimoog-model-d/, JS-rendered,
  no body content reached) — but it is at least consistent across two
  independent retailers. Separately, the original 1970–1981 run itself saw
  three circuit-board revisions, described in secondary sources
  (Vintage Synth Explorer via search snippet; secretlifeofsynthesizers.com)
  as "minor... a revision of the oscillator board," not a change of
  transduction mechanism the way Pianet's electrostatic→magnetic pickup
  swap was. **So even if Monosounds' unit turns out to be the 2016
  reissue rather than a vintage original, that alone would not be the kind
  of wrong-machine problem that sank pianet or cp70** — the open question
  here is real-hardware-vs-not, not which-generation.

**A stronger-provenance alternative was found and could not be used.**
Legowelt (Danny Wolfers) offers "223 samples from my 1970s Moog Minimoog
synthesizer Serial number #5529" — a named producer, an explicit unit serial
number, and an explicit vintage-original era, all directly on his own site
(https://legowelt.org/samples/, fetched this session) — provenance the
Monosounds page does not come close to. But the pack's only download link on
that page, a 2018 WeTransfer link (`https://we.tl/AjC4FCLeMv`), resolves to
WeTransfer's generic "we couldn't load some important parts of our website"
error this session — dead, not obtainable. And the page states only "please
consider a donation," no usable commercial license. Recorded as found, not
usable: unreachable and unlicensed both, either one alone would have
disqualified it.

**Conclusion: the capture leg does not clear gold.** Not because it is
provably the wrong machine (pianet/cp70's failure mode), but because its
claim to be a hardware Minimoog *at all* rests on one unverified marketing
sentence from a seller whose core business is software presets, for an
instrument expensive enough that the claim itself needs corroboration this
session could not find. That is short of "actually reached, provenance
read" — the task's own bar for gold.

## 1. Reference and grade

**Tier 1 (hardware capture):** Reached, license read, provenance
insufficient (§0) — Monosounds. Reached, provenance strong, unobtainable —
Legowelt (§0). Two paid packs were also found and read at the product-page
level this session, not purchased, not used as evidence, recorded in
`paywalled` below (Sonic Freaks "The MINI Sampled," €30; OXIDE Sound Lab
Bandcamp one-shots, $4 minimum). One Freesound-mirrored sound (Pixabay,
"Minimoog lead solo," credited to Freesound user "Analogist" under a real
Pixabay Content License) surfaced via search but could **not** be confirmed
against the user's actual Freesound sound list when fetched directly this
session — the two fetches disagreed, so it is recorded as an unresolved
contradiction, not cited as evidence either way.

**Tier 2 (literature), for the correct machine:**
- Moog's own Minimoog D service manual (archive.org) — reached at the
  metadata level this session; its scanned schematic pages were **not**
  rendered or read this session (no page-content fetch attempted, unlike
  pianet's clavinet.com PDF). Usable only as "a service manual exists and
  its rights are unverified," not as read circuit detail.
- Huovilainen, "Non-Linear Digital Implementation of the Moog Ladder
  Filter" (DAFx 2004) — fetched and confirmed this session
  (https://dafx.de/paper-archive/2004/P_061.PDF): title, author, venue all
  verified from the document itself. This is the load-bearing literature
  source — it models the exact 4-pole transistor-ladder VCF topology that
  is this machine's defining circuit, independent of which Model D unit
  any capture came from.

**Tier 3 (OSS proxy):** zynthian/moog, an LV2 "Minimoog emulator" — MIT
license confirmed via the GitHub API this session
(`api.github.com/repos/zynthian/moog` → `"license": {"key": "mit", ...}`).
Permissive enough that its math could in principle be read for structure
under the license gate (vision §5), not just measured as output — not
attempted this session; it is written in Assembly, which limits how
directly its structure ports to this codebase regardless of license.

**What this makes the grade.** No hardware capture this session cleared
both "reached" and "provenance read" at once (§0). The DAFx ladder-filter
paper alone is sufficient to derive the circuit's defining nonlinear
behavior — literature's bar — and the service manual and MIT-licensed
emulator back it up as secondary and tertiary legs respectively. **Literature**,
argued down from the survey's gold on provenance grounds, not source
scarcity — there was no shortage of *candidate* captures, only of ones that
actually held up.

## 2. License call, per source

| Source | License as read | Where read |
|---|---|---|
| Monosounds "100+ Free Minimoog Model D Samples Vol. 1" | "100% royalty-free for unlimited commercial use... the only thing not allowed is reselling or redistributing the files themselves" (stated on-page) | https://monosounds.studio/product/100-free-minimoog-model-d-samples-vol-1/ (fetched this session) — real license text, insufficient hardware provenance, see §0 |
| Legowelt Minimoog samples (Serial #5529) | No commercial license stated — "please consider a donation for good musical magic and sonic karma" only | https://legowelt.org/samples/ (fetched this session) — strong provenance, but link dead and no usable license, see §0 |
| Sonic Freaks "The MINI Sampled" | Not stated beyond a trademark disclaimer ("Minimoog Model D is a trademark by Moog Music Inc.; Sonic Freaks is in no way affiliated") | https://www.sonicfreaks.com/shop/themini/ (fetched this session) — €30, paywalled, not obtained |
| OXIDE Sound Lab "Minimoog Model D Synth Samples" | Self-contradictory: page text claims "Creative Commons license — no need to credit," Bandcamp page footer separately states "all rights reserved" | https://oxidesoundlab.bandcamp.com/album/minimoog-model-d-synth-samples-basses-synthwave-80s (fetched this session) — $4 minimum, paywalled, not obtained, and license unresolved even if it had been |
| Pixabay "Minimoog lead solo" (credited to Freesound "Analogist") | Pixabay Content License, per the Pixabay page | https://pixabay.com/sound-effects/minimoog-lead-solo-48367/ (fetched this session) — **not used as evidence**: a direct fetch of the credited Freesound uploader's own sound list this session did not show this title among their 23 sounds; the discrepancy is unresolved, so this source is recorded as found-and-contradicted, not cited |
| Minimoog Model D Service Manual (archive.org) | License unverified — no `licenseurl`/rights field in the item metadata | https://archive.org/metadata/moog_MINIMOOG-D_SERVICE_MANUAL (fetched this session, metadata only — schematic pages not rendered) |
| Huovilainen, "Non-Linear Digital Implementation of the Moog Ladder Filter" (DAFx 2004) | Conference-proceedings copyright; no CC/open designation found. Math is portable per vision §5 regardless of the writeup's copyright | https://dafx.de/paper-archive/2004/P_061.PDF (fetched and read this session) |
| zynthian/moog (LV2 Minimoog emulator) | MIT | https://api.github.com/repos/zynthian/moog (fetched this session) |
| Wikipedia, "Minimoog" | CC BY-SA (standard Wikipedia terms) | https://en.wikipedia.org/wiki/Minimoog (fetched this session) |
| Behringer Model D coverage (Synthtopia) | Not a license source — cited only for the clone's existence and price, to support the plugin/clone-confusion risk in §0 | https://www.synthtopia.com/content/2017/04/22/behringer-399-minimoog-model-d-clone-hands-on-demo/ (fetched this session) |
| Reissue circuit-continuity claims (Vintage King, Perfect Circuit) | Not license sources — retailer marketing copy, not Moog's own primary documentation (Moog's own product page returned no body content to this session's fetch) | https://vintageking.com/blog/moog-minimoog-model-d-reissue/ ; https://www.perfectcircuit.com/signal/moog-minimoog-model-d-2022 (both fetched this session via search-result synthesis) |

Nothing above is ported. The DAFx paper's math may be re-derived from the
publication per the license gate; the MIT-licensed zynthian/moog could be
read for structure if a rebuild wants a second implementation to check
against, but its content was not read this session beyond the license file.

## 3. What the machine is, mechanically

Three voltage-controlled oscillators (waveform options per-oscillator: saw,
triangle, square-family pulse) plus a white/pink noise generator, summed in
a mixer stage, driven into a single 4-pole (24 dB/octave) transistor-ladder
low-pass VCF with resonance capable of self-oscillation, then a VCA — the
architecture Wikipedia's "Minimoog" article (CC BY-SA, fetched this session)
and the Huovilainen paper's own motivation both describe. **Monophonic**:
one voice, no polyphony, across the original run and (per §0) apparently
across the reissue as well
(https://en.wikipedia.org/wiki/Minimoog, fetched this session).

## 4. Voice structure and polyphony

**Hardware:** monophonic — single voice, 3 VCOs + noise generator through
one shared filter/VCA signal path, no polyphony on any Model D variant
(Wikipedia, fetched this session, §3).

**Module:** `MAX_VOICES = 1` (`minimoog.py:90`). Matches exactly. Per
`accuracy-roadmap.md` §3 (Brad, 2026-09-01): *"If it was monophonic in real
life, it's monophonic here"* — minimoog is named directly among the nine
`MAX_VOICES = 1` instruments the roadmap already expects to be correct as
they stand, and nothing found this session argues otherwise. **No structural
change proposed.**

The module does allocate 3 `synthio.Note` oscillators plus a conditional
noise `Note` per held key (`minimoog.py:141-144`) — internally polyphonic in
*oscillator count* while remaining `MAX_VOICES = 1` at the note-arbitration
level (`minimoog.py:107`, `len(voices) >= MAX_VOICES` triggers
`steal_oldest()`), which is the correct shape for a 3-VCO monosynth: one
playable voice built from several simultaneous oscillators, not several
playable voices.

## 5. Proposed acceptance criteria

No numeric hardware measurements were taken this pass — no capture reached
this session cleared both provenance and license, so every criterion below
is qualitative/literature-derived, matching the survey's own D3 finding for
this family (no known-settings capture found for minimoog by the survey
either, `accuracy-survey.md:264`).

| # | Criterion | Target (source) | Status |
|---|---|---|---|
| 1 | Filter slope is 24 dB/octave with resonance capable of full self-oscillation | Huovilainen 2004, ladder-filter topology (fetched this session) | measurable once rendered — sweep resonance to its top value and check for a sustained sine at cutoff with no input |
| 2 | Filter saturates nonlinearly as resonance/drive increase, not a clean linear response | Huovilainen 2004's whole subject is this nonlinearity (fetched this session) | measurable once rendered — compare THD at low vs. high resonance/drive settings |
| 3 | Three-oscillator detune produces continuous chorusing rather than a fixed beat rate | General characterization only — no numeric beat-rate target found this session; not adopted as a strict criterion, recorded so it isn't silently dropped | not adopted — no source this session puts a number on it |
| 4 | Monophonic legato/glide behavior | Not sourced this session beyond the module's own implementation (`minimoog.py:112-127`) — no circuit-level portamento time-constant found in the Huovilainen paper or the unread service manual | not adopted — flagged as a literature gap, not a criterion |

## 6. What the module would need to change — read, not measured

Read from `minimoog.py` only; nothing below was rendered or listened to
this pass.

- **The filter is a single generic 2-pole `synthio.Biquad`, not a 4-pole
  ladder.** `lp = synthio.Biquad(synthio.FilterMode.LOW_PASS, cutoff,
  Q=resonance)` (`minimoog.py:137`), shared across all three oscillators
  and the noise generator (`minimoog.py:141-144`). This is the single
  largest gap against §3/§5: the machine's defining circuit character —
  24 dB/octave, self-oscillating, saturating — is not modeled at all
  today. The toolkit already has the building block:
  `audioeffects.LadderFilter` (`eq.py:162`), documented in its own
  docstring as "Moog-style: four cascaded one-pole-pair low-passes
  sharing one cutoff, resonance concentrated in the last stages. 24
  dB/octave slope with the familiar squelch when resonance is pushed"
  (`eq.py:163-165`) — built as a downstream `Effect`, not a `synthio`
  filter object, so using it means routing the oscillator mix through
  `Instrument`'s `output=` parameter (`_support.py:293-294`) rather than
  passing a filter into each `synthio.Note`, the same routing change
  `pianet.md` §6 flagged as unused across the whole library (confirmed
  again here: no `LadderFilter(` hits found when checking this module).
- **The "Overdrive" macro is a bare linear gain multiplier, not
  saturation.** `overdrive = logmap(value0, 1.0, 3.0)` (`minimoog.py:173`)
  feeds directly into `amp = volume * value0 * overdrive`
  (`minimoog.py:139`) — a louder signal, not a different-shaped one. The
  toolkit has two purpose-built nodes this macro could route through
  instead: `audioeffects.Overdrive` ("soft clipping with a tone control —
  tube breakup territory," `drive.py:52-53`) or `audioeffects.Saturation`
  (`drive.py:154-156`). Whichever is chosen is a modeling decision, not
  sourced by anything read this session — flagged as a real mismatch
  between the macro's name and what it does, independent of the grade
  question.
- **Glide is an exponential-ratio bend clamped to ±1 octave**
  (`minimoog.py:112-127`, with the clamp explained in the code's own
  comment as an `array("h")` overflow guard, not a hardware-sourced
  choice). No source reached this session — including the unread service
  manual — confirms or contradicts this shape against the real Model D's
  portamento circuit.
- **Noise routes through the same shared filter as the oscillators**
  (`minimoog.py:144`, same `lp` object). Plausible — the schematic would
  need to be read to confirm the real mixer stage does the same before
  this is claimed as verified, and it was not read this session (§1).

## 7. MCU budget and macro budget

Per-voice cost today: up to 4 `synthio.Note` objects (3 oscillators + noise)
sharing 1 `synthio.Biquad`, 1 `synthio.Math` node for the filter-envelope
sum, and a conditional glide `synthio.LFO` — no wavetable over 40 partials
(`SAW`/`SQUARE`, `minimoog.py:56-57`), no convolution, no
`audioconvolve.FRAMES` latency to disclose. Swapping the shared `Biquad` for
`audioeffects.LadderFilter`'s 4-stage cascade (`eq.py:166-186`) would raise
per-note filter cost roughly 4x for whichever voices route through it —
**read, not measured**; whether that needs a `" - lean"` patch on small
targets is a Station B question this dossier cannot answer without a
render/profile pass. `MACRO_LABELS` carries all 16 of 16 slots already
(`minimoog.py:9-14`) — **no new macro slot is available** without dropping
an existing one; a rebuild reaching for e.g. an ARTICULATION or per-oscillator
waveform-select macro would have to fold it into a patch or trade out an
existing macro, not add a seventeenth.

## 8. What was not found, stated plainly

- No hardware capture reached this session cleared both "provenance read"
  and "obtainable" at once (§0).
- No known-settings capture (front-panel knob positions per sample) was
  found for any Minimoog source this session — matching the survey's own
  D3 finding for this family.
- The Minimoog D service manual's actual schematic pages were not rendered
  or read this session — only its archive.org metadata record. A future
  pass should attempt to read it directly, the way `pianet.md` did for
  clavinet.com's Pianet N schematic.
- The Pixabay/Freesound "Minimoog lead solo" lead was not resolved — two
  fetches this session disagreed on whether it belongs to the credited
  uploader — and is not used as evidence either way (§1, §2).
- Moog's own product page for the current Model D reissue returned no
  readable body content to this session's fetch (JS-rendered); the
  circuit-continuity claim in §0 rests on two retailers, not on Moog's own
  copy.

## `paywalled`

- Sonic Freaks "The MINI Sampled" — €30, real-hardware claim backed by a
  named preamp (Universal Audio 4-710D) but no production year/serial
  disclosed and no license terms stated. https://www.sonicfreaks.com/shop/themini/
  (fetched this session, page-level only, not purchased).
- OXIDE Sound Lab "Minimoog Model D Synth Samples (Basses)" — $4 minimum,
  "vintage Moog Minimoog Model D" claimed with no era/hardware-vs-plugin
  detail, and a self-contradictory license (CC claim vs. "all rights
  reserved" footer). https://oxidesoundlab.bandcamp.com/album/minimoog-model-d-synth-samples-basses-synthwave-80s
  (fetched this session, page-level only, not purchased).

Per this pass's hard constraint, neither was purchased and neither is
counted toward the grade — recorded so the next pass doesn't re-spend time
rediscovering them.

**Awaiting Gate A:** `APPROVE ACCURACY DOSSIER minimoog`
