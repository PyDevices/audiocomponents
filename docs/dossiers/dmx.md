# Accuracy Dossier — `dmx` (Oberheim DMX)

**Module:** `audiocomponents/lib/audioinstruments/dmx.py` (292 lines)
**Proposed grade:** **literature** — carried forward from Phase 0's survey
finding and reconfirmed this session: the primary literature sources were
re-fetched and read in full, the flagged capture candidate was re-checked
against its own metadata and rejected exactly as the survey warned, and no
new capture route was found. No hardware audio was obtained or measured.
**Reference settings (D3):** no capture reached — criteria in §6 are
literature-derived only, with no measured numbers.

## 1. Reference and grade — the acquisition, in full

**Literature, fetched and read this session, in full text (not just cited
by title):**

- **Oberheim DMX Service Manual** (March 1982), archive.org
  (https://archive.org/details/Oberheim_DMX_Service_Manual). Unlike the
  survey's summary-level citation, this session pulled the item's own
  `_djvu.txt` OCR layer in full (64,477 bytes, 6,806 lines — saved to
  `.reference-captures/dmx/Oberheim_DMX_Service_Manual_djvu.txt`) and the
  source PDF (13.2 MB, saved alongside it). The OCR is clean prose (a
  typed manual, not a scanned schematic), and it is the load-bearing
  source for this whole dossier — see §3 for what it says about the
  8-voice-card architecture, quoted directly. A companion `.epub` and
  `.xml`/`.sqlite` metadata files exist on the item but were not needed.
- **Oberheim DMX Schematics (81-12-21)**, archive.org, item `JL11363`
  (https://archive.org/details/JL11363, John Leimseider archive). Its
  `_djvu.txt` was also pulled (saved to
  `.reference-captures/dmx/Oberheim_DMX_Schematics_djvu.txt`) but turned
  out to be OCR noise from schematic *drawings*, not a text scan — the
  title blocks are legible ("DMX VOICE CARD", "VOICE CARD - CYMBAL # 1")
  but the actual circuit traces/values are not machine-readable this
  session. Kept as confirmation that a companion schematic set exists
  and that individual voice-card PCBs are physically distinct objects,
  not used for any circuit-value derivation below.
- **synthxl.com, Oberheim DMX page** (https://www.synthxl.com/oberheim-dmx/)
  — fetched this session; hosts the same service/owner's manuals under
  its own stated terms (§2). No technical content beyond the download
  links themselves.
- **soundprogramming.net, Oberheim DMX page**
  (https://soundprogramming.net/drum-machines/oberheim/oberheim-dmx/) —
  fetched this session; independently corroborates "8 notes" polyphony,
  "24" pads, and "11 samples at 8-bit resolution," and names the
  interchangeable voice-card categories (Timbale, Toms, Shaker/Claps,
  Electric Snare, Cymbal) referenced in period parts listings.
- **electrongate.com/dmxfiles** FAQ and 1554E voice-card page
  (http://www.electrongate.com/dmxfiles/dmxfiles_faq.html,
  https://www.electrongate.com/dmxfiles/dmx1554e.html) — fetched this
  session; confirms per-card pitch trim pots and describes the modern
  aftermarket voice-card ecosystem (six reprogrammable card categories:
  Bass, Snare, Hi-hat, Tom, Perc 1, Perc 2 — see §3).
- **forum.vintagesynth.com, "FOUND IT! Oberheim DMX Cowbell voice card"**
  (https://forum.vintagesynth.com/viewtopic.php?t=72527) — fetched this
  session; a real owner's account of sourcing and installing a
  Cowbell/Claps voice card, with a direct quote on how its two trigger
  buttons are wired (§3).
- **Wikipedia, "Oberheim DMX"** (https://en.wikipedia.org/wiki/Oberheim_DMX)
  — fetched this session (raw wikitext, not just a summary): "24
  individual drum sounds derived from 11 original samples," "a maximum
  8-voice polyphony; one voice per card," "eight separate outputs," 8-bit
  PCM with μ-law companding "increasing sound resolution to approximately
  12 bits in the analog domain." No card-by-card sound list is given here
  — that came from the service manual instead (§3).

**Capture, checked and rejected, per the charter's explicit warning:**
`https://archive.org/details/dmx-stock-dmx-sounds` ("Oberheim DMX Drums -
Stock DMX Sounds"). Its metadata was re-fetched this session
(`https://archive.org/metadata/dmx-stock-dmx-sounds`): `licenseurl: None`,
`rights: None`, and — exactly as the warning predicted —
`description: "Custom Fairlight CMI sample pack 48."`, mismatched with
its own "Oberheim DMX Drums" title and matching the batch-uploaded
Community Audio red flag already on record in
`docs/agent-knowledge/instrument-sources.md`. **Rejected, not fetched,
not relied on.**

**Capture, checked and still unreachable:** Sample Focus's "Oberheim DMX
Snare" page was not re-fetched this session — the Phase 0 survey already
recorded a live HTTP 403 there
(`docs/accuracy-survey.md` line 170/952) and re-hitting a source already
confirmed dead this same week would not change the evidence; carried
forward as context, not re-claimed as a fresh visit.

**elektrotanya.com, checked and empty for this instrument:** a live
search this session (`https://elektrotanya.com/search.php?text=oberheim+dmx`)
returned zero hits for the DMX specifically — elektrotanya's Oberheim
holdings found this session are for the **DSX** (a sequencer, a different
product) only, not the DMX drum machine. The charter's pointer to
elektrotanya did not pan out for this instrument; noted rather than
silently dropped.

**Samples From Mars, enumerated in place per the charter:**
`~/SamplesFromMars/extracted/` was listed this session (`find ... -iname
"*dmx*" -o -iname "*oberheim*"`, zero matches). The two packs actually
present — `free-drums` ("Free Drums From Mars") and `sp` ("Free SP From
Mars") — were inspected file-by-file; `free-drums`'s WAV folder holds
CR-78, TR-808, TR-909 and Simmons-family names (`CHCR78.wav`,
`Clave808.wav`, `Kick909.wav`, `KickSimB.wav`, etc.) — no DMX content.
Confirms the roadmap ledger's own note that DMX is not among the
instruments with a Samples From Mars capture leg identified (cr78,
drumtraks, simmons_sdsv are; dmx is not).

**No open-source DMX emulator** was found by the Phase 0 survey (GForce's
DMX plugin is commercial/closed-source, built with the original
designer's cooperation) — carried forward from `docs/accuracy-survey.md`
line 176 as prior-session context, not re-verified this run.

**Grade call:** literature is the honest ceiling. What changed this
session versus Phase 0's citation-level pass is depth, not tier: the full
service-manual text is now actually in hand and quoted (§3), not just
cited as existing.

## 2. License call, per source

| Source | Kind | License as read | Where read |
|---|---|---|---|
| Oberheim DMX Service Manual (archive.org) | literature | No `licenseurl`/`rights` field in item metadata | https://archive.org/metadata/Oberheim_DMX_Service_Manual (fetched this session) |
| Oberheim DMX Schematics, `JL11363` (archive.org) | schematic | No `licenseurl`/`rights` field in item metadata | https://archive.org/metadata/JL11363 (fetched this session) |
| "Oberheim DMX Drums - Stock DMX Sounds" (archive.org Community Audio) | capture (rejected) | license unverified; no rights field, and description mismatched with title ("Custom Fairlight CMI sample pack 48") — treated as unreliable provenance, not fetched | https://archive.org/metadata/dmx-stock-dmx-sounds (fetched this session) |
| synthxl.com | literature (facts only) | Explicit site-wide terms: "All manuals are collected from the World Wide Web and provided for hobby, historical curiosity, study and research, and may not be used for any commercial purposes." | https://www.synthxl.com/oberheim-dmx/ (fetched this session) |
| soundprogramming.net | literature (facts only) | "The Sound Programming site is copyright © 2006-2026 Jason Champion." No further reuse terms stated; short factual citation only, nothing reproduced wholesale | https://soundprogramming.net/drum-machines/oberheim/oberheim-dmx/ (fetched this session) |
| electrongate.com/dmxfiles (FAQ + 1554E page) | literature (facts only) | No license/terms statement found; hobbyist/commercial parts site, facts-only citation | http://www.electrongate.com/dmxfiles/dmxfiles_faq.html, https://www.electrongate.com/dmxfiles/dmx1554e.html (fetched this session) |
| forum.vintagesynth.com thread | literature (facts only) | No license statement; public forum post, short quote only | https://forum.vintagesynth.com/viewtopic.php?t=72527 (fetched this session) |
| Wikipedia, "Oberheim DMX" | literature | CC BY-SA (Wikipedia standard) | https://en.wikipedia.org/wiki/Oberheim_DMX (fetched this session, raw wikitext) |
| elektrotanya.com search | literature (negative result) | n/a — zero DMX-specific results returned; site's own stated terms elsewhere are personal-use-only, moot here since nothing was retrieved | https://elektrotanya.com/search.php?text=oberheim+dmx (fetched this session) |
| Sample Focus "Oberheim DMX Snare" | capture (unreachable) | license unverified — Phase 0 recorded HTTP 403; not re-fetched this session, carried forward as context only | docs/accuracy-survey.md (read this session) |
| GForce DMX plugin | oss (negative result) | commercial/closed-source per Phase 0's survey; carried forward, not re-verified this session | docs/accuracy-survey.md (read this session) |

Nothing above is source code and nothing is ported. The service manual's
prose is quoted directly in short excerpts (it is the object of study,
the way `sp1200.md` treated its own service manual), never redistributed
whole; the PDF and OCR text live only in `.reference-captures/dmx/`
(gitignored).

## 3. Hardware structure vs the module

**The real machine, from the service manual's own Specifications page**
(quoted directly): **"Number of Sounds: 24"** — "3 Bass Drum (loud,
medium, soft)," "3 Snare Drum (loud, medium, soft)," "3 Hi-Hat (closed,
accent, open)," "6 Tom-Toms (high to low)," "2 Ride Cymbal (loud, soft),"
"1 Crash Cymbal," "2 Tambourine (loud, soft)," "1 Rim shot," "2 Shakers
(loud, soft)," "1 Clap" (3+3+3+6+2+1+2+1+2+1 = 24, checks out). Notably
**no cowbell** appears anywhere in this factory list — see the Cowbell
finding below. Polyphony is stated three independent ways in the same
manual: "Maximum number of notes: 2000 events, each of which may contain
up to **8 notes** occuring simultaneously"; the trigger bus is "TR1 -
TR16" (8 cards × 2 trigger inputs each); and the Diagnostic Test EPROM's
"Test 4 sounds all the voice cards at once." Wikipedia corroborates
independently: **"a maximum 8-voice polyphony; one voice per card"** and
**"eight separate outputs."**

**How 24 sounds fit on 8 cards — quoted directly, then applied.** The
manual's Voice Boards section states there are exactly **three card
types**: *"1. Normal; provides 3 variations of one sound. Variation may
be either pitch or volume... 2. Split; where the sound memory is divided
into two separate sounds. The first sound has two variations (pitch or
volume), while triggering both inputs to the card plays a completely
separate sound... 3. Dual slot; the cymbal voice is currently the only
one of these. The combination of high bandwidth and long decay requires
more memory than can be fit... onto one board. Thus one board contains
all the control circuitry and the other contains all the memory. The
Cymbal 1 and Cymbal 2 slots..."* This directly and explicitly confirms
Ride(2)+Crash(1) share one logical voice across two physical boards —
high confidence, a manual-stated fact, not an inference. Two more facts
from the same section matter structurally: each card holds **"a
triggerable 12-bit counter"** and **"an 8-bit companding DAC"** —
singular, one of each per card — which is why this dossier reads a card
as **monophonic within itself**: a trigger to any sound assigned to a
card starts that one counter and that one DAC over again, regardless of
which of the card's 2-3 sounds is selected. This reading is not spelled
out in so many words in the manual (moderate confidence, the same
epistemic status `tr909.md` gave its own crash/ride sharing call from a
block diagram) but follows directly from "a" counter and "a" DAC, singular.

Applying the card-type rules to the 24-sound list, at high confidence for
Bass Drum, Snare, Hi-Hat and Cymbal (each cleanly one Normal or Dual-slot
card, matching the type definitions exactly) and at lower confidence for
the remaining four sound families, which the manual's own text does not
individually assign to cards:

| Card | Type | Sounds | Confidence |
|---|---|---|---|
| 1 | Normal | Bass Drum (loud/med/soft) | high — one 3-variant family, fits Normal exactly |
| 2 | Normal | Snare (loud/med/soft) | high |
| 3 | Normal | Hi-Hat (closed/accent/open) | high — also the one place the *module* already independently implements a choke (`dmx.py:236-239`), corroborating the sharing |
| 4-5 | Normal ×2 | Tom-Toms ×6 (high to low), split across two cards | low — the manual gives the sound count and the card-type rule but not which 3 pitches share which card; soundprogramming.net's parts listing separately confirms a generic "Toms" voice-card category exists (https://soundprogramming.net/drum-machines/oberheim/oberheim-dmx/), not the pairing |
| 6 | Dual slot | Ride (loud/soft) + Crash | high — quoted directly above |
| 7-8 | Split ×2 | Rim shot, Clap, Tambourine (loud/soft), Shakers (loud/soft) — 5 sounds across 2 cards (max 3 each) | low — card-type math and soundprogramming.net's/electrongate's "Perc 1 / Perc 2" card-category naming both corroborate two flexible percussion cards existing, but which sounds pair (Tambourine+Rimshot vs Shaker+Clap, or another split) is this dossier's own proposal, not manual-stated |

**The Cowbell finding.** The module's `NOTE_MAP` includes a Cowbell
(`dmx.py:54`, note 56) that **is not one of the factory 24 sounds** —
confirmed absent from the manual's own Specifications list above. It is
not invented from nothing, though: a forum account of a real DMX owner
sourcing a **"Cowbell voice card"**
(https://forum.vintagesynth.com/viewtopic.php?t=72527) confirms Cowbell
is a genuine, documented DMX sound obtainable by reprogramming one of the
flexible Perc-type cards' EPROM — the same thread quotes the specific
wiring: *"your cowbell/claves card is... configured to pitch the cowbell
two ways along two buttons and the third button has the clap"* — i.e. on
that real, modified unit, Cowbell (2 pitches) and Clap (1) occupy one
physical Split card together, sharing its one counter/DAC. This dossier
treats Cowbell as authentic-but-non-stock: real and DMX-native, but not
part of the base 24-sound kit, and — per the reference-decides-structure
rule — not deserving of a 9th independent circuit. §5 proposes it share
Card 8 with Clap, following this specific sourced precedent rather than
inventing a new pairing.

**The module today: `MAX_VOICES = 16`** (`dmx.py:134`) — **double** the
hardware's 8-voice-card ceiling, the largest headroom mismatch Phase 0
found in the sample-drum family (`docs/accuracy-survey.md` line 33).
`NOTE_MAP` (`dmx.py:42-56`) names 13 sounds across the 8 physical cards
(the collapsed set: Bass Drum, Snare, Rimshot, Clap, 3 named toms instead
of 6, Closed/Open Hat, one "Cymbal" instead of Ride+Crash separately,
Tambourine, Cowbell, Shaker). `handle_event` builds fresh `synthio.Note`
objects per hit and calls `trigger_voice`/`steal_oldest`
(`dmx.py:139-150`) against that 16-voice pool — a general-purpose
allocator with no card-sharing/choking model at all except the one
already-correct Hi-Hat case (`dmx.py:234-246`). **Proposed structural
change**, justified entirely by the manual quotes above: rebuild as
**8 fixed circuits**, one per physical voice card, each monophonic within
itself (a trigger to any of that card's assigned sounds retriggers the
shared circuit), replacing `MAX_VOICES`/`steal_oldest` entirely — the
same move `tr909.py`'s already-built rebuild made (`tr909.py:113-141`:
a `circuits` dict keyed by voice name, `synth.press()` directly on
permanently-allocated Notes, no `MAX_VOICES` anywhere in that file). "If
it was monophonic in real life, it's monophonic here" applies at the
*card* level for the DMX, not just the whole-instrument level.

## 4. Modeling approach: synthesis-to-match, not sample playback

Same ROMpler posture `tr707.md` argued for the 707: this is 8 parallel
EPROM-playback-and-shape chains, not an analog circuit to re-derive from
a DAFx paper, and none should be expected — the manual's own Voice Boards
section describes the physical chain plainly: *"a triggerable 12-bit
counter... a 4096 x 8 EPROM for voice data storage... an 8-bit companding
DAC... with associated output filter... a six-pole elliptic response
low-pass filter. The cutoff frequency of the filter is set above the
frequency band of the sound, and is used as a smoothing filter to
integrate between the discrete samples coming out of the DAC."* Each of
the 8 circuits in §5 is synthesized from primitives and tuned against the
targets in §6, not sampled.

**The bit-crushed, companded character — a real target, already
attempted.** `dmx.py:68-82`'s `crush_noise()`/`GRIT` is explicitly
commented as modeling *"the DMX's crunchy, gritty sample chip
character"* via a **48-level, hold-3** stair-stepped LCG noise table.
The manual and Wikipedia together describe a more specific mechanism:
**8-bit PCM with μ-law companding**, "increasing sound resolution to
approximately 12 bits in the analog domain" (Wikipedia, sourced from the
DAC's own non-linear companding curve, not a flat linear quantizer). A
flat 48-level linear staircase is a reasonable proxy but is not the same
shape as a companded 256-level (8-bit) code — companding concentrates
resolution near zero and coarsens it near full scale, which a linear
staircase does not. **Not changed here** (Station A proposes the target,
not the fix): worth Station B considering whether `crush_noise` should
apply a μ-law-shaped step size instead of a flat one, measurable as
whether the quantization-noise floor rises with signal level the way a
companded system's does.

**Frequency response and dynamic range, quoted as targets.** The
Specifications page states **"Frequency Response: 10-16,000 Hz (varies
among voices, and is dependent on tuning)"** and **"Dynamic Range: 80
dB."** Both are literature-only targets (§6), not measured against any
capture this session.

**Hi-Hat decay is circuit-confirmed continuous, not stepped** — the
manual has a dedicated note: *"HI-HAT DECAY: The decay of the CLOSED and
ACCENT Hi-Hat may be changed by changing the value of C3... A useful
range is about 2 mF to 10 mF. A smaller value will give a shorter decay,
and a larger value will provide a longer decay time."* This is a real,
continuously-variable RC-style decay stage, corroborating the module's
`ch_decay`/`oh_decay` macros (`dmx.py:128-129,241`) as modeling something real
— no absolute time-constant value can be derived without the paired
resistor value, which this session's sources do not give, so §6 states
the shape as a target (smooth, not stepped) without a number.

**Pitch macros model the External CV input, not the front-panel preset
buttons.** The front-panel "3 variations" per Normal/Split card are
discrete triggered alternates (loud/medium/soft, or two pitched buttons),
not a sweepable knob. But the manual's External Control Voltages section
describes a real, continuously-variable, per-voice control: *"The
external control voltage inputs (one for each voice), can be used to
control either the pitch or the volume of the voice. All voices come
from the factory strapped for control of pitch... the response is
approximately 2-1/2 volts per octave, and... the pitch decreases with
increasing voltage."* This is the literature justification for the
module's continuous `BD Pitch`/`SD Pitch`/`Rim Pitch`/tom-pitch/`Cowbell`
pitch macros (§7): they model the rear-panel CV input's real behavior,
not an invented front-panel sweep. `BD Decay`/`Clap Decay`/`SD Snappy`
have no such literature anchor found this session — kept as
synthesis-calibration globals (the same honest label `tr707.md` used for
its own unanchored macros), not asserted as real panel controls.

No convolution is proposed anywhere in this instrument; no
`audioconvolve.FRAMES` latency is incurred.

## 5. The FIXED-CIRCUIT map (mandatory)

Per the unattended charter and the pattern already built for `tr909.py`
(`tr909.py:113-141`, no `MAX_VOICES`, a `circuits` dict of permanently
allocated `synthio.Note`s retriggered via `synth.press()`): **8 circuits,
one per physical voice card**, matching the hardware's own 8-voice
ceiling exactly (replacing today's `MAX_VOICES = 16`, `dmx.py:134`).
Cards sharing sounds choke on retrigger — the hardware's own "one
counter, one DAC" limit (§3), not an invented rule:

| # | Circuit | MIDI notes (today's NOTE_MAP) | Resident Notes | Confidence |
|---|---|---|---|---|
| 1 | Bass Drum | 36 | 2 (tone + grit click, keeps `dmx.py:171,174`'s existing pair) | high |
| 2 | Snare | 38 | 2 (body + noise snap, keeps `dmx.py:180,184`'s existing pair) | high |
| 3 | Hi-Hat (closed+open, shared) | 42, 46 | 1 (retriggered, decay swapped by which key — already the module's intent at `dmx.py:234-246`, just not yet a permanent Note) | high |
| 4 | Tom A | 41, 45 (Low+Mid choke) | 1 | low — which toms pair is this dossier's own guess (§3), not sourced |
| 5 | Tom B | 48 (Hi, standalone) | 1 | low, same caveat |
| 6 | Cymbal (Ride+Crash, shared) | 49 | 2 (bp+hp noise pair, keeps `dmx.py:253-254`'s existing pair) | high — Dual-slot sharing is manual-quoted (§3) |
| 7 | Perc A | 37 (Rimshot), 54 (Tambourine) — choke | 1 | low — pairing is this dossier's proposal (§3), not sourced |
| 8 | Perc B | 70 (Shaker), 39 (Clap), 56 (Cowbell) — choke | 1 | low for the Shaker/Clap pairing; the Cowbell+Clap pairing specifically follows the forum's sourced real-hardware example (§3) |
| | | | **Total** | **11** |

11 resident `synthio.Note`s, 2 below the charter's 13-note ceiling —
margin for Station B, same posture `tr909.md`/`sp1200.md` took rather
than spending every slot. The Clap collapses from today's 3 staggered
Notes (`dmx.py:198-200`) to 1: unlike the TR-909's analog sawtooth-flutter
clap circuit (`tr909-evidence.md`'s finding), the DMX's clap is one
EPROM-recorded sample on one channel, so a single retriggered Note is
*more* accurate here, not a corner cut — the same reasoning `sp1200.md`
§4 gave its own single-Note clap. Toms drop from 3 independent Notes to 2
(one shared pair), and Perc drops from what would otherwise be 4-5
independent Notes (Rimshot, Tambourine, Shaker, Clap, Cowbell each on
its own) to 2, because on real hardware they are never more than 2
independent circuits regardless of how many named buttons/MIDI notes
target them.

**The two low-confidence rows (Tom A/B split, Perc A/B split) are the
map's honest weak points**, exactly the epistemic status `tr909.md` gave
its own crash/ride call: proposed because the card-count math demands
*some* split and the general "shared card chokes" principle is
well-sourced, but the *specific* groupings are this dossier's own
proposal, not read from a source. Station B should ship them as
proposed; the batch listen can refuse a specific pairing (e.g. un-choke
Rimshot from Tambourine) without invalidating the 8-circuit/11-Note
structure itself.

## 6. Acceptance criteria — literature-derived, nothing measured

No DMX capture was reachable this session (§1) — `tools/measure_hits.py`
was not run; there is no reference audio to point it at. Every row below
is a literature target, not a measured tolerance, and should be replaced
with real numbers the moment a capture is obtained.

| Criterion | Target | Source |
|---|---|---|
| Frequency response ceiling | 10-16,000 Hz, varying per voice and tuning | manual Specifications page (quoted §4) |
| Dynamic range | ≈80 dB | manual Specifications page (quoted §4) |
| Companding character | 8-bit μ-law-companded PCM, ≈12-bit effective resolution; a companded (non-linear) step size, not a flat linear one | Wikipedia; manual Voice Boards section |
| DAC smoothing | discrete DAC steps integrated by a 6-pole elliptic low-pass set above each voice's own band — i.e. no audible stepping artifact should survive to the output | manual Voice Boards section (quoted §4) |
| Hi-Hat decay shape | smooth (RC-style), continuously variable, not stepped; no absolute time constant derivable this session | manual, HI-HAT DECAY note (quoted §4) |
| Per-card monophony | at most 1 of a card's assigned sounds audible at once; a new trigger to any sound on a card retriggers/replaces whatever that card was already playing | manual Voice Boards section, moderate confidence (§3) |
| Voice ceiling | 8 concurrent circuits, not 16 | manual (3 independent internal confirmations, §3); Wikipedia |
| Card typology | Normal (3 pitch/volume variants of one sound); Split (2 variants + 1 separate sound on the 3rd trigger); Dual-slot (Cymbal only, 2 physical boards for 1 logical voice) | manual Voice Boards section, quoted directly (§3) |

## 7. MCU budget and macro budget

**MCU:** 11 permanently-resident `synthio.Note` objects across 8 fixed
circuits (§5), each retriggered rather than allocated per hit — down from
today's worst-case allocation (BD 2 + SD 2 + Rim 1 + Clap 3 + Toms 3 + HH
1 + Cymbal 2 + Tamb/Shaker 1 + Cowbell 2 = 17 ephemeral Notes if every
named sound fired in the same block). Structurally simpler for the MCU
than today's unbounded allocate-and-hope code, the same direction
`tr909.md`/`sp1200.md` both moved. **No `" - lean"` patch is expected.**

**Macros: 16 of 16, no new macro proposed** (the file is already at the
charter's ceiling, `dmx.py:9-13`). Traced to their literature basis,
honestly, including where none was found:

| # | Label | Traces to |
|---|---|---|
| 0 | Level | master mix output (kept) |
| 1 | BD Pitch | rear-panel External CV pitch input, ~2.5 V/octave, one per voice (§4) |
| 2 | BD Decay | **not** a documented panel/CV control — synthesis-calibration global, kept for the reason `tr707.md` kept its own unanchored macros |
| 3 | SD Pitch | External CV pitch input (§4) |
| 4 | SD Snappy | not documented this session — synthesis-calibration global |
| 5 | Rim Pitch | External CV pitch input, Card 7 (§4) |
| 6 | Clap Decay | not documented this session — synthesis-calibration global |
| 7 | LT Pitch | External CV pitch input, Tom Card A (§4) |
| 8 | MT Pitch | External CV pitch input — note Tom Cards A/B (§5) give only 2 independent CV inputs across the hardware's 6 tom pitches, so 3 independently-macro'd tom pitches is a musical convenience beyond the literal CV count, not contradicted by it |
| 9 | HT Pitch | External CV pitch input, Tom Card B (§4) |
| 10 | Tambourine | front-panel per-voice fader (level), Perc Card A (§3, Theory of Operation: "mixed into the main outputs via the front panel fader") |
| 11 | Shaker | front-panel per-voice fader, Perc Card B |
| 12 | Cowbell | External CV pitch input, Perc Card B — shares that card's one CV/DAC with Clap (§3, §5); the two macros (`Cowbell`, `Clap Decay`) implying independent simultaneous control is a minor tension with the shared-card model, noted rather than fixed here |
| 13 | Cymbal Pitch | External CV pitch input, Card 6 (Dual-slot, Ride primarily per §3) |
| 14 | CH Decay | manual's own dedicated "HI-HAT DECAY" note, C3 component (§4) — the single most literature-grounded macro in the set |
| 15 | OH Decay | same source as #14 |

No room remains to add a macro without cutting one; none of §3-§5's
findings demand one (the structural changes are all inside the fixed
circuits, not the macro surface).

**Operating mode v2:** built unattended; deviations stated in the
evidence pack; blessed at the phase batch listen.
