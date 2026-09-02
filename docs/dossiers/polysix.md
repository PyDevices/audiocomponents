# Accuracy Dossier — `polysix` (Korg Polysix)

**Module:** `audiocomponents/lib/audioinstruments/polysix.py` (149 lines)
**Survey's grade:** gold (`accuracy-survey.md:56`, `:565-578`)
**Proposed grade:** **literature — downgraded from the survey's gold.**
**Reference settings (D3):** no known-settings capture of a verified-stock
machine was found; the criteria below are literature-derived (largely
sourced numeric ranges from Korg's own owner's manual), not a statistical
envelope across a hardware pack.
**Pass-scope consequence:** per Brad's 2026-09-02 decision, this pass
rebuilds only instruments that hold a gold grade. Since this dossier drops
`polysix` to literature, the module is **not rebuilt this pass** — it is
left exactly as it stands, and this dossier is the record for a future
literature-tier pass.

## 0. The finding that changes the grade

The task brief's named risk is real and independently confirmed, not
hypothetical: **battery leakage is a well-documented failure mode across
surviving Polysix units**, and at least one of the two hardware-capture
packs reached this session is explicit that its own unit went through
exactly that failure and a subsequent modification, not a stock repair.

- Wikipedia, "Korg Polysix" (CC BY-SA, fetched fresh this session):
  "This battery would start leaking after a couple of years, and the
  alkaline battery fluid would eat away the traces on the programmer
  board PCB, damaging the synthesizer" — the affected part is the
  KLM-367 programmer board.
- Independent corroboration via web search this session (Vintage Synth
  Explorer forum, ModWiggler, tubbutec.de, Korg Forums, Gearspace, Old
  Crow's Synth Shop — titles read, not all individually fetched): the
  issue is described repeatedly as common enough that "more and more
  Polysix units end up broken" and a battery swap is "standard
  procedure."
- **wavparty.com's own "Polysix sample pack #1" page** (fetched this
  session, https://wavparty.com/downloads/polysix-sample-pack-01/) states
  outright, in the pack author's own words: *"This year I finally took a
  gamble on a broken one — Polysixes are notorious for their 'leaking
  battery' issue that can destroy circuit boards. Mike Walters at Mystery
  Circuits got it up and running again, and a few Tubbutec mods have added
  a few tricks up its sleeve."* That is a real, named hardware-capture pack
  of the *exact target instrument*, and its own author says the specific
  unit sampled was both battery-damage-repaired **and** post-repair
  modified (Tubbutec sells CV/gate, MIDI and voice-modification retrofit
  kits for the Polysix). This is not the stock instrument, by the pack's
  own account — disqualifying it as a gold-tier stock-machine reference,
  but strong, independent, first-hand confirmation that the task brief's
  risk is exactly the kind of thing that shows up when you actually check
  a specific pack's provenance instead of trusting a brand name.

The survey's cited gold capture — Producer Hive's "KORG Polysix Samples &
One-Shots" — makes **no statement at all** about the sampled unit's
condition, service history, or modification status, in either direction.
Re-read in full this session (product description body, fetched via raw
HTTP and via the Shopify product JSON, not just the summarized page): "All
sounds were recorded directly from the KORG Polysix... This collection has
been carefully recorded, cleaned up, and key-labeled for ease of use...
100% royalty-free licensing." That confirms the pack is of the real
**hardware** (not the 2004 Korg Legacy Collection software recreation,
which Wikipedia — fetched this session — separately confirms exists as a
distinct product and which this pack's own wording does not describe), so
the task's second named risk (software-vs-hardware) is cleanly dismissed
for this pack. But "recorded directly from the KORG Polysix" is silent on
stock-vs-repaired-vs-modified, and given how "notorious" (wavparty's own
word) the failure mode is, silence cannot be read as an implicit "stock"
claim. Combined with "100% royalty-free licensing" being a marketing
bullet rather than an actual license document (Producer Hive's own Terms
of Service page, fetched this session, contains no product- or
sample-specific license terms at all), the pack that was gold-graded does
not clear this pass's bar: a hardware capture with its provenance **and**
its license actually read, not asserted.

**Conclusion: drop to literature.** A real, well-documented, primary-source
circuit and architecture reference does exist and was reached this
session — Korg's own owner's manual — and is sufficient to derive the
instrument's behavior in the vision's tier-2 sense, even though no capture
this session cleared tier 1.

## 1. Reference and grade

**Tier 1 (hardware capture) search — four candidates reached, none usable
as gold:**

1. **Producer Hive, "KORG Polysix Samples & One-Shots"**
   (https://shop.producerhive.com/products/korg-polysix-samples-one-shots,
   fetched this session, price confirmed **$0.00** via the page's own
   product JSON — not a paywalled source). 26 bass + 25 lead + 61 "pads &
   chords" + 13 stab/FX one-shots, 48kHz/24-bit stereo. Real hardware per
   its own text (§0). **Not usable as gold**: no documented settings, no
   documented unit condition, no formal license (only a marketing
   "royalty-free" bullet). Content is also a mix of single notes and
   multi-note chords ("pads & chords" is the single largest category),
   which further limits its use as a per-voice measurement source even if
   the provenance gap were closed.
2. **wavparty.com, "Polysix sample pack #1"**
   (https://wavparty.com/downloads/polysix-sample-pack-01/, fetched this
   session). Free, 56 one-shots + 12 Ableton Live instruments, 44.1kHz
   16-bit mono WAV. Real hardware, but **explicitly a repaired-from-
   battery-damage, subsequently Tubbutec-modified unit** by the pack
   author's own account (§0) — disqualified from representing the stock
   instrument regardless of license.
3. **Freesound, "Korg Polysix FX" pack (JimPurbrick)**
   (https://freesound.org/people/JimPurbrick/packs/584/, fetched this
   session). Content is processed performance/FX material — "a slowing,
   retro sci-fi laser zap," "a thick, rich, chorused rising filter
   sweep" — not single notes at identifiable settings, and per-sound
   Freesound licenses (which the task brief correctly notes vary per
   sound) were not individually resolved because the content type already
   rules this pack out as a measurement source. Recorded as found, not
   pursued further.
4. **Samples From Mars, "Free SP From Mars" — "Polysix Chord LFO"**
   (Brad's windfall library, `~/SamplesFromMars/extracted/sp/Free SP From
   Mars/`, enumerated locally this session; originating site
   https://samplesfrommars.com/products/sp-1200-from-mars, named in the
   pack's own `ReadMe.rtf`, read this session). This is **not** a clean
   Polysix capture: the filename and the parent product ("SP-1200 From
   Mars") both say the material is a Polysix **chord**, played with the
   onboard ensemble/LFO effect engaged, then run back through an E-mu
   SP-1200 sampler for that pack's own lo-fi-resample product — two
   layers of coloration (chorus effect + 8-bit resampling) between the
   listener and the bare hardware voice. License, read this session at
   https://samplesfrommars.com/pages/faq: royalty-free for music use,
   explicit no-redistribution and no-use-in-software terms — compatible
   with measuring in place, but the content itself is unsuitable as a
   primary reference for this instrument's own voice.

**Tier 2 (literature) — one strong primary source, plus corroboration:**

- **Korg's own Polysix Owner's Manual**, PDF hosted at
  https://www.vintagesynth.com/sites/default/files/2017-05/p6user.pdf,
  **fetched and read in full this session** (24 pages extracted with
  `pypdf`, not just summarized — the first automated summary of this same
  PDF incorrectly said "two VCOs per voice," which the extracted text
  directly contradicts; see §3 for the correct, sourced figure). This is
  the primary factory document: full VCO/VCF/VCA/EG/MG section text,
  control-by-control, with several numeric ranges (§5).
- **Korg Polysix Service Manual** (archive.org,
  https://archive.org/details/Korg_Polysix_Service_Manual_1, metadata
  checked this session at https://archive.org/metadata/
  Korg_Polysix_Service_Manual_1 — no `licenseurl`/rights field present).
  Existence and license status confirmed this session; the manual's own
  schematic pages were not read in depth this session (the owner's manual
  above carries this dossier's architecture claims).
- **Electric Druid, "SSM2044 LP Filter Designs"**
  (https://electricdruid.net/ssm2044-lp-filter-designs/, fetched and read
  this session). Confirms the Polysix runs its SSM2044 filter chip on a
  non-datasheet **±5V** supply (vs. the typical ±15V) and uses the chip's
  second input to cancel DC offset — a trick made necessary specifically
  *because* the Polysix has only one oscillator per voice, independently
  corroborating the Owner's Manual's "1 VCO per voice" claim from a
  different kind of source (circuit analysis vs. factory documentation).
- **Wikipedia, "Korg Polysix"**
  (https://en.wikipedia.org/wiki/Korg_Polysix, fetched this session) and
  **Vintage Synth Explorer, "Korg PolySix"**
  (https://www.vintagesynth.com/korg/polysix, fetched this session):
  corroborate voice count, production year (1981), and the "1 VCO + 1
  sub-oscillator per voice, 6 voices" architecture from two more
  independent angles.

**What was not found:** No DAFx/AES paper modeling the Polysix's DCO or
SSM2044 filter circuit specifically (consistent with the survey's own null
result — not deeply re-searched this session beyond one query that
returned nothing new). No open-source, buildable Polysix emulator (the
survey's finding that MOODYSIX/Eightysix/Kp6 are closed-source freeware
VSTs was not re-litigated this session).

**Grade rationale.** Tier 1 was searched honestly and reached four real
candidates; none clears gold (§0). Tier 2 was reached and is unusually
strong for this program — a primary factory document, read in full, not
just cited — sufficient to derive the circuit's architecture and several
of its numeric ranges. Per the vision's hierarchy, that is **literature**.

## 2. License call, per source

| Source | License as read | Where read |
|---|---|---|
| Producer Hive, "KORG Polysix Samples & One-Shots" | No formal license text found; "100% royalty-free licensing" is a marketing bullet, not a license document. Treated **license unverified**. | https://shop.producerhive.com/products/korg-polysix-samples-one-shots and https://shop.producerhive.com/policies/terms-of-service (both fetched this session) |
| wavparty.com, "Polysix sample pack #1" | Stated directly: free use of "sounds, loops, instruments and other products," with three named exceptions (no redistributing pack files without permission; no using demo tracks in film/video/podcasts/games without permission; no releasing demo tracks as your own music). Usable as a measurement oracle under these terms. **Disqualified from gold on provenance (§0), not license.** | https://wavparty.com/license/ (fetched this session) |
| Freesound, "Korg Polysix FX" (JimPurbrick) | Not resolved — Freesound licenses vary per sound and this pack's individual sound licenses were not opened, since the content type (processed FX) already rules it out as a measurement source. | https://freesound.org/people/JimPurbrick/packs/584/ (pack page fetched this session; per-sound pages not opened) |
| Samples From Mars, "Free SP From Mars" ("Polysix Chord LFO") | Royalty-free for music production; explicit no-redistribution, no-use-in-software/application terms; license revoked if refunded (n/a, this is the free pack). Compatible with in-place measurement, not with shipping. | https://samplesfrommars.com/pages/faq (fetched this session); local `ReadMe.rtf` in Brad's windfall copy read this session, states no license terms of its own beyond a link to the product page |
| Korg Polysix Owner's Manual (PDF, vintagesynth.com mirror) | No rights statement found on the hosting page; a Korg factory document hosted by a fan archive. Treated **license unverified / publisher-copyright**, read for engineering derivation only — nothing reproduced here beyond short, attributed quotations for citation. | https://www.vintagesynth.com/sites/default/files/2017-05/p6user.pdf (fetched and read in full this session) |
| Korg Polysix Service Manual (archive.org) | No `licenseurl` field in the item's metadata record. Treated **license unverified / Korg-copyright**, per the same convention already established for Korg service manuals in `docs/agent-knowledge/instrument-sources.md`. | https://archive.org/metadata/Korg_Polysix_Service_Manual_1 (fetched this session) |
| Electric Druid, "SSM2044 LP Filter Designs" | **CC BY-NC-SA 4.0**, per site footer: "Druid code and schematics are released under a CC BY-NC-SA 4.0 license... feel free to download and use Electric Druid code in your personal synth, pedal, or sonic blastertron 2000." Commercial use requires contacting the site. | https://electricdruid.net/ssm2044-lp-filter-designs/ (fetched this session) |
| Wikipedia, "Korg Polysix" | CC BY-SA (standard Wikipedia terms) | https://en.wikipedia.org/wiki/Korg_Polysix (fetched this session) |
| Vintage Synth Explorer, "Korg PolySix" | No explicit license found; used for corroborating spec facts only, short quotations. Treated **license unverified / site-copyright**. | https://www.vintagesynth.com/korg/polysix (fetched this session) |

Nothing above is ported. The Owner's Manual was read for architecture and
numeric-range facts only; every figure below is restated in prose, and no
page image, schematic, or verbatim block is reproduced.

## 3. What the machine is, mechanically

Per Korg's own Owner's Manual (§1, §2, read in full this session — every
figure below is a direct or closely-paraphrased quotation from it, not an
inference):

- **"There are 6 VCOs in the Polysix, one per voice."** Each VCO offers
  Sawtooth or Pulse/PWM waveforms, three octave settings (16'/8'/4'), and
  a **Sub OSC** switch adding a square-wave tone one or two octaves below
  the VCO pitch (a "waveform staircasing" effect makes the 1-octave sub
  tone inherit much of the main waveform's timbral character). Pulse
  width is either manually set (PW mode) or continuously swept by a
  dedicated **PWM SPEED** oscillator, described as "completely separate
  from the MG oscillator used for vibrato... allowing vibrato and PWM
  effects to occur simultaneously."
- **"There are 6 VCFs in the Polysix, one for each voice. Each VCF is a 4
  pole, 24dB/octave low pass filter"** with Cutoff, Resonance (to
  self-oscillation, "purest tone... at about 7"), EG Intensity (±10
  octaves of sweep, direction switchable), and Keyboard Tracking
  (0%–150%, with over/under-tracking as a deliberate creative option).
  Electric Druid's circuit analysis (§1) independently confirms this
  filter runs the SSM2044 chip at a non-datasheet **±5V** supply (rather
  than ±15V) with a DC-offset-cancellation trick on the chip's spare
  input — necessary specifically because there is only one oscillator
  feeding each voice, corroborating the manual's "1 VCO per voice" figure
  from circuit design rather than factory prose.
- **"There are six EGs in the Polysix, one per voice"** — a standard
  ADSR, Attack/Decay/Release independently variable "from about 1
  millisecond to over 15 seconds," Sustain Level 0%–100%.
- **"There are 7 VCAs in the Polysix, one for each voice plus one overall
  VCA"** for a whole-program attenuator (±20 dB range, non-destructive
  program-to-program level matching).
- **A single Modulation Generator (MG)** — one LFO, Frequency (~1 cycle/30s
  to ~50 Hz) and Delay (up to ~8s) controls, whose **destination is
  switch-selected**: VCO (vibrato), VCF ("waa-waa"), or VCA (tremolo) —
  one at a time, not simultaneously, though the front-panel Mod Wheel adds
  an independent vibrato regardless of the MG's own destination setting.
- **UNISON mode**: all 6 voices assigned to a single note, individually
  detuned, for "incredibly fat six-VCO soloing and bass sounds" — a
  switchable **monophonic** performance mode with last-note priority and
  note-return-on-release, distinct from the instrument's default 6-voice
  polyphonic mode (POLY).
- A separate **Chorus/Phaser/Ensemble** effect switch, plus **Chord
  Memory** (memorize up to a 6-note chord to a single key) and a built-in
  3-pattern **Arpeggiator** with Hold/Latch.

## 4. Voice structure and polyphony

**Hardware:** true 6-voice polyphony as the default mode, each voice with
its own complete signal path — independent VCO+sub-osc, VCF (with its own
EG), and VCA (§3) — not paraphonic (a paraphonic design would share a
filter or envelope across voices; the Polysix does not). Confirmed from
three independent kinds of source this session: Korg's own manual (primary
factory documentation), Electric Druid's circuit analysis (independent
derivation from the SSM2044 application), and Wikipedia/Vintage Synth
Explorer (secondary corroboration). The machine also has a switchable
**UNISON** mode that collapses all 6 voices onto one note for a fat
monophonic lead/bass sound — a real, sourced structural mode the survey's
original one-line description did not mention.

**Module:** `MAX_VOICES = 6` (`polysix.py:75`) — **matches the hardware's
6-voice polyphony exactly.** This specific finding from the survey holds
up under this session's scrutiny even though the overall grade does not:
the voice-count claim was correct, just cited to a capture whose
provenance couldn't support the grade it was used to justify.

As with the electromechanical-piano family (see `pianet.md` §4 for the
same class of finding, cited there for the sibling instruments), `voices`
is keyed per held note (`key_of`, imported at `polysix.py:40`), and
`len(voices) >= MAX_VOICES` triggers `steal_oldest()`
(`polysix.py:93-94`) — an arbiter over held keys, not raw `synthio.Note`
objects. Each held key allocates **two to four** `synthio.Note` objects
depending on macro state, all read this session directly from
`handle_event` (`polysix.py:84-124`):

- Two DCO layers, always: `PULSE_NARROW`/`PULSE_WIDE`, crossfaded by the
  PWM LFO (`polysix.py:116-117`).
- One ensemble-detune layer (`SAW`, `bend=ens_lfo2`), only when `ens_depth
  > 0.01` (`polysix.py:119-120`).
- One sub-oscillator layer (`SQUARE` at `hz * 0.5`, i.e. one octave down —
  matching the hardware's "1 OCT" Sub OSC setting; the hardware's "2 OCT"
  option is not modeled), only when `sub_osc > 0.01` (`polysix.py:123-124`).

The default patch (`PATCHES[0]`, `polysix.py:33-35`) sets macro 4
(Ensemble Depth) to 64/127 and macro 1 (Sub-Osc Level) to 64/127 — both
well above the 0.01 gate — so **the default patch uses all four Note
layers per key**, i.e. up to 24 `synthio.Note` objects for a full 6-key
chord. This is the same internal-consistency question `pianet.md` §4
raised for that family: `synthio.Synthesizer.max_polyphony = 14` on the
CPython target (`audioif/src/cpython/synthio.py:271`, confirmed by
`grep -n` this session) and desktop/unix/wasm MicroPython
(`audioif/micropython.mk:113`, `CIRCUITPY_SYNTHIO_MAX_CHANNELS=14`,
corrected path from `pianet.md`'s citation — verified this session), while
the general CMake/MCU build sets it to **8**
(`audioif/micropython.cmake:190`, same corrected path). At 4 Notes/key,
the MCU default (8) saturates after exactly **2** keys, and desktop's 14
after **3** keys with 2 Notes to spare — well short of the 6-key ceiling
`MAX_VOICES` and `steal_oldest()` imply. **Not measured by rendering**
this pass (no render is in scope); Station B, if this instrument is ever
promoted past literature tier, should check for silently-dropped Note
layers on a 4+-note chord on both targets, the same way `pianet.md`
flagged for its family.

## 5. Proposed acceptance criteria

All literature-derived, all sourced to Korg's own manual (§1, §3) unless
otherwise noted — no hardware capture cleared this pass's bar for a
statistical envelope, so nothing here is a number pulled from measuring
audio.

| # | Criterion | Target (source) | Status |
|---|---|---|---|
| 1 | Filter is a 4-pole (24 dB/oct) resonant low-pass, self-oscillating at high resonance | Owner's Manual, VCF section, §3 | **measurable in principle** once a render pipeline exists — slope and self-oscillation onset are checkable against the module's `synthio.Biquad` (`polysix.py:101`), which is a single 2-pole (12 dB/oct, or whatever `synthio.Biquad` implements) filter per note, not the hardware's 4-pole design — flagged as a real topology gap, not proposed to fix this pass |
| 2 | EG (Attack/Decay/Release) ranges roughly 1 ms to 15+ s | Owner's Manual, EG section, §3 | module's macro ranges (`polysix.py:141-142,144`: attack 0.001–2.001s, decay 0.05–3.05s, release 0.01–4.01s) fall well inside the hardware's stated range at the fast end but cap well short of the hardware's slow end (15s+) — **read only**, not measured |
| 3 | Filter cutoff is EG-modulatable (±10 octaves) and keyboard-trackable (0–150%) | Owner's Manual, VCF EG Intensity / KBD Track, §3 | module's filter is a **static** `Biquad` set once at note-on from a macro-controlled `cutoff_val` and `res` (`polysix.py:101`), with no envelope or keyboard-tracking modulation on cutoff at all — a real, sourced, unmodeled feature (§6) |
| 4 | PWM is a genuine duty-cycle sweep, LFO-driven, speed-controllable, independent of vibrato | Owner's Manual, VCO PWM section, §3 | the module's own comment (`polysix.py:107-109`) states the same intent and crossfades two fixed-duty tables (`PULSE_NARROW`/`PULSE_WIDE`) via a `pwm_rate`-controlled LFO (`polysix.py:110-112`) — architecturally the right idea for a table-based synth; **not measured** against the hardware's continuous sweep |
| 5 | Sub-oscillator is a plain square wave, one or two octaves below, with a "waveform staircasing" timbral link to the main waveform | Owner's Manual, VCO Sub OSC section, §3 | module implements the 1-octave-down case only (`polysix.py:124`), no staircasing effect (uses an independent `SQUARE` table, not the main waveform's own shape shifted) — **read only** |
| 6 | UNISON mode exists as a distinct, switchable, monophonic, 6-voice-detuned mode | Owner's Manual, UNISON section, §3 | **not modeled at all** — no macro or patch state corresponds to it; flagged as a real, sourced, missing mode, not proposed to add this pass |
| 7 | MG (single LFO) is destination-selectable among VCO/VCF/VCA, not three simultaneous fixed assignments | Owner's Manual, MG section, §3 | module instead runs two *always-pitch* ensemble LFOs (`ens_lfo1`/`ens_lfo2`, `polysix.py:104-105`) plus a separate always-PWM LFO (`pwm_lfo`, `polysix.py:110`) — a different, fixed-assignment architecture rather than the hardware's one-LFO/one-destination-at-a-time design; **read only**, no criterion number attached since the manual gives no measurable target beyond "one at a time" |

## 6. What the module would need to change — read, not measured

Everything below is read from `polysix.py` and Korg's manual only; nothing
was rendered or listened to this pass, and — per pass scope — none of it
is proposed for action now, since the grade did not reach gold.

- **The filter is static, not enveloped or keyboard-tracked.**
  `lp = synthio.Biquad(synthio.FilterMode.LOW_PASS, cutoff_val, Q=res)`
  (`polysix.py:101`) is built once at note-on from macro state and never
  modulated over the note's life. The hardware's own manual calls the VCF
  "perhaps the single most expressive module in the Polysix" specifically
  because of its EG Intensity (±10 octave sweep) and Keyboard Tracking
  controls (§3, §5 criterion 3) — this is the largest sourced gap between
  the module and the documented hardware.
- **UNISON mode is entirely unmodeled** (§5 criterion 6) — a real,
  switchable, monophonic 6-detuned-voice mode with its own note-priority
  behavior, not present anywhere in `handle_event`.
- **The MG's single, destination-selectable LFO is replaced by three
  always-on, fixed-assignment LFOs** — `ens_lfo1`/`ens_lfo2` always modulate
  pitch (`bend=`, `polysix.py:116-117,120`), `pwm_lfo` always modulates
  pulse width (`polysix.py:110-112`) — architecturally reasonable for a
  fixed-function synth voice, but not what the sourced hardware does
  (§5 criterion 7).
- **`MACRO_LABELS` carries 11 of 16 slots** (`polysix.py:9-20`) — five
  free. If this instrument is ever promoted to a rebuild, `EG Intensity`
  (VCF) and `KBD Track` are the two most strongly hardware-sourced
  candidates for new macros, both directly named and ranged in Korg's own
  manual (§3).
- **The sub-oscillator only implements the "1 OCT" option**
  (`polysix.py:124`); the hardware's "2 OCT" setting is unmodeled.
- **Real hardware features entirely absent from the module and not
  proposed here**: Chord Memory, the Arpeggiator, and the Chorus/Phaser/
  Ensemble effect switch (the module's "Ensemble Depth" macro approximates
  *an* ensemble-style pitch-modulation effect via `bend=`, but is not
  sourced to the hardware's actual BBD-based Chorus/Phaser/Ensemble
  circuit — no schematic for that section was reached this session).

## 7. MCU budget and macro budget

Not applicable this pass — no rebuild is proposed (§0 pass-scope note).
For the record, read-only: per-key cost at default-patch settings is up
to 4 `synthio.Note` objects, 1 shared `Biquad`, and up to 3 `LFO`/`Math`
nodes (`polysix.py:104-112`) — a heavier per-voice budget than `pianet`'s
2-Note voices, and the §4 `max_polyphony` ceiling finding applies more
severely here (2 keys saturate the MCU default of 8, vs. 4 keys for a
2-Note-per-key instrument). **No `" - lean"` patch is proposed**, since no
patch is proposed at all this pass.

## 8. What was not found, stated plainly

- No hardware capture with both (a) documented settings and (b) a
  verifiably stock (non-repaired, non-modified) unit was found this
  session. Given how commonly-cited the battery-leak failure is (§0), this
  is treated as a real evidentiary gap, not an oversight — a future pass
  should ask any candidate pack directly about unit provenance before
  crediting gold, the same way `wavparty.com`'s own page volunteers it.
- No DAFx/AES paper specific to the Polysix's DCO or SSM2044 filter
  circuit was found this session (one search query, no hits; the survey's
  own null result was not otherwise re-litigated).
- No open-source, buildable Polysix emulator was found or re-searched for
  this session; the survey's finding (MOODYSIX, Eightysix, Kp6 are
  closed-source freeware VSTs, not proxy-oracle candidates) was not
  challenged.
- The archive.org Korg Polysix Service Manual's actual schematic pages
  were not read in depth this session — only its license/metadata status
  was confirmed. The Owner's Manual (§1, §3) carries this dossier's
  architecture and numeric claims instead.

**Awaiting Gate A:** `APPROVE ACCURACY DOSSIER polysix`
