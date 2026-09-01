# Accuracy Dossier — `drumtraks` (Sequential Circuits Drumtraks)

**Module:** `audiocomponents/lib/audioinstruments/drumtraks.py` (146 lines)
**Proposed grade:** **literature.** One genuine capture lead was chased to
ground this session and measured — it clears the bar for a corroborative
data point on exactly one of the machine's 13 voices, not for the
instrument. A stronger, known-settings pack exists commercially and was
read but not obtained. Literature is the honest ceiling; §1 gives the
acquisition in full, following the precedent `sp1200.md`/`tr707.md` set
(grade reflects what was actually fetched and usable this session, not
what is believed to exist).
**Reference settings (D3):** no known-knob capture was obtained. One
single-hit capture (Clap) was measured as a statistical/corroborative data
point (roadmap D3), not a settings sweep; every other voice's criteria
below are literature-derived only.

## 1. Reference and grade — the acquisition, in full

**The capture lead the task named, chased to ground:** the local
`~/SamplesFromMars/extracted/free-drums/` tree (Brad's, outside this repo,
measured in place per the working scope — nothing copied into the repo)
is Samples From Mars' **"Free Drums From Mars"** promotional pack: 16 WAV
files at `Free Drums From Mars/Formats/WAV/`, confirmed by directory
listing this session (`ls`), one of which is `ClapDtrax15.wav` — the only
Drumtraks-prefixed (`Dtrax`) file in the tree; enumerated with
`find ~/SamplesFromMars/extracted -iname "*Dtrax*"` before naming it, per
citation discipline (10 hits, all the same file across format variants —
`WAV`, `Kontakt 5/Samples`, `Logic EXS/Samples`, an Ableton `.asd`
sidecar, plus `__MACOSX` resource forks; the canonical `WAV` copy is the
one measured).

**Provenance, stated honestly:** the pack's own installer text (read
locally, `Free Drums From Mars/Docs/.../Kontakt/Instructions.rtf`) is
generic ("Thank You For Your Purchase!", installation steps only — no
per-machine capture-chain statement). The pack's *public* description
(rekkerd.org's announcement of Samples From Mars' free drum-machine pack,
fetched this session,
https://rekkerd.org/samples-mars-releases-free-drum-machines-samples/)
names the vendor's house signal chain — "API Preamp, SSL 4000 Console,
Emu SP-1200 sampler, Otari MTR-12 Mastering reel to reel, and Apogee
Conversion," with "tape saturation... compression, gate, EQ, and
filters" — but names the pack's machines as "Linndrum, TR-808, TR-909,
Simmons & CR-78," **not Drumtraks**. The local file set does not match
that list exactly either (it has 909/Simmons/CR-78/808 files but no
Linndrum-prefixed file, and one Drumtraks-prefixed file the article never
mentions) — evidence the free pack's contents have been revised since
that article, not evidence against the file's authenticity. **Net
honest call:** `ClapDtrax15.wav` is very likely a genuine hardware
capture run through the same documented chain as its packmates, but no
source read this session states that chain *for this specific file* —
a real gap, stated plainly rather than papered over.

**The concrete unparking path to gold, found and read, not obtained:**
Samples From Mars sells a dedicated **"Drumtrax From Mars"** pack
(https://samplesfrommars.com/products/drumtrax-samples, fetched this
session) — "384 24bit WAV Drumtrax Samples" with "**16 tunings of every
hit**," captured via "a radial JDI direct box, fed into the mic preamp of
an API 512C," an "API 560 equalizer," onto "fresh 1/4" tape on our Otari
MTR-12 Mastering Reel to Reel," with the kick additionally through a
"Neve Tape Emulator." This is the exact known-settings-sweep shape that
made `sp1200.md` gold (16 SP-1200 tunings) — genuinely paid, not free,
and not present anywhere in Brad's local archive (`find` across
`~/SamplesFromMars` for `drumtrak`/`dtrax` turns up only the one free
Clap file). **Not obtained this session.** This is the specific,
concrete path to gold for whoever next has the $-purchase or a
license grant, recorded the way `tr707.md`'s Lead 2 was.

**Literature — carried forward from Phase 0, not re-fetched this
session per this task's operating mode** (`docs/accuracy-survey.md`,
read this session at lines 178–192): the archive.org Sequential Circuits
Drumtraks Service Manual and the elektrotanya SD400-I schematic were
both reached and audited there as sufficient to derive the
voice/architecture (tier 2); Angelspit's free-sample page and Full Bucket
Music's closed-source "DrumTraqs" Z80-simulation proxy were both found
insufficient there (unverified provenance; not open source, respectively).
Angelspit's page was **independently re-visited this session** per the
task's explicit instruction to verify it myself (below).

**New literature reached this session:**
- **vintagesynth.com**, Sequential Circuits DrumTraks page
  (https://www.vintagesynth.com/sequential-circuits/drumtraks, fetched
  this session): spec table gives **"Polyphony: 12 voices"** and
  **"Sounds: 13 tones,"** as two distinct numbers (not a typo — the
  table separates them), plus **"Six individual outputs, plus one mono
  mix output"** and "Thirteen drum sounds all with programmable tuning
  and level control."
- **Electronics & Music Maker, March 1984** review, muzines.co.uk archive
  (https://www.muzines.co.uk/articles/sequential-circuits-drumtraks/1581,
  fetched this session): the most detailed source found — names all 13
  voices, states the 6-output-channel grouping explicitly (§3), states
  levels and pitches are "programmable in steps from 00 to 15" (16
  discrete steps, both parameters), and states the digital engine uses
  "digital chip recordings" ("the single-chip voices from the LinnDrum
  will slide straight in to the Drumtraks" — corroborating a
  chip-per-voice-family ROM architecture, not one shared sample bank).
- **Wikipedia, "Drumtraks"** (https://en.wikipedia.org/wiki/Drumtraks,
  fetched this session): infobox states "13 voices," body text lists
  "bass drum, snare, snare rim, toms 1 and 2, crash and ride cymbal,
  open and closed hi-hat, handclaps, tambourine, cowbell, and cabasa"
  (13 named sounds, matching muzines exactly) and "8-bit digital
  samples" for the synthesis method. Release year 1984.
- **Angelspit's Drumtraks page**, re-verified this session as the task
  instructed (https://www.angelspit.net/sci-drumtraks/, fetched this
  session): confirms Phase 0's finding word-for-word — "This samples are
  free from 'THE INTERNET'. Not sure where they came from...but we did
  beef them up a little" — explicitly unverifiable provenance, still
  not usable at any tier above proxy-of-last-resort, and not relied on
  here. One new detail beyond what Phase 0 recorded: the page states
  samples are "provided @ 44.1kHz 16bit and **15625kHz** 16 bit" — an
  oddly specific non-round number that reads like a real hardware clock
  rate rather than an arbitrary resample target, and is flagged below as
  a possible (unconfirmed) native playback-rate lead for Station B to
  check against the schematic's clock circuitry. Not treated as
  confirmed.

Literature clears its bar: three independent sources (vintagesynth,
muzines, Wikipedia), reached this session, agree on 13 named voices, the
6-channel output grouping, and per-voice programmable tune+level — enough
to derive structure and macro surface with real numbers, not guesses.

## 2. License call, per source

| Source | Kind | License as read | Where read |
|---|---|---|---|
| Samples From Mars, "Free Drums From Mars" (local, `ClapDtrax15.wav`) | capture | Samples From Mars site-wide Audio Product EULA: "licensed, not sold, to you to be used for and reproduced within your new musical compositions and productions only... All copying, lending, duplicating, re-selling or trading of any Audio Product or other Content is strictly prohibited" — production-use OK, no redistribution; nothing is shipped from this dossier or the repo | https://samplesfrommars.com/pages/terms-conditions (fetched this session) |
| Samples From Mars, "Drumtrax From Mars" (paid pack, not obtained) | capture (unobtained) | Same site EULA as above (not independently re-confirmed on this specific product page beyond its stated 7-day money-back guarantee); moot since unobtained | https://samplesfrommars.com/products/drumtrax-samples (fetched this session) |
| rekkerd.org, Samples From Mars free-pack announcement | literature (corroboration only) | license unverified — news/blog site, no rights statement on the article; facts and short quotes only, nothing copied beyond attribution | https://rekkerd.org/samples-mars-releases-free-drum-machines-samples/ (fetched this session) |
| Angelspit free Drumtraks samples | capture (rejected) | no license stated; uploader states provenance itself is unknown ("free from THE INTERNET, not sure where they came from") — treated copyleft-equivalent per the charter's default; not obtained, not relied on | https://www.angelspit.net/sci-drumtraks/ (fetched this session) |
| Sequential Circuits Drumtraks Service Manual (archive.org) | literature | per Phase 0's audited entry (not re-fetched this session): no `licenseurl`/rights field present in item metadata | https://archive.org/metadata/sequential_circuits_Drumtraks_SM (per `docs/accuracy-survey.md:183`) |
| Drumtraks SD400-I schematic (elektrotanya) | schematic | per Phase 0's audited entry (not re-fetched this session): site terms "do not offer the downloaded file for sell only use it for personal usage" — personal-use only, read for circuit derivation only | https://elektrotanya.com/drumtraks_sequential_circuits_inc_sd400-i_sch.pdf/download.html (per `docs/accuracy-survey.md:184`) |
| Full Bucket Music DrumTraqs (Z80 sim + factory ROM samples) | oss (rejected) | per Phase 0's audited entry (not re-fetched this session): closed-source freeware, no license stated — fails the vision's tier-3 open-source requirement | https://www.fullbucket.de/music/drumtraqs.html (per `docs/accuracy-survey.md:186`) |
| vintagesynth.com, DrumTraks page | literature | license unverified — hobbyist reference site, no rights statement found; facts and short quotes only | https://www.vintagesynth.com/sequential-circuits/drumtraks (fetched this session) |
| Electronics & Music Maker, Mar 1984 (muzines.co.uk archive) | literature | license unverified — magazine-archive site, no rights statement found on the article; facts and short quotes only | https://www.muzines.co.uk/articles/sequential-circuits-drumtraks/1581 (fetched this session) |
| Wikipedia, "Drumtraks" | literature | CC BY-SA (Wikipedia standard) | https://en.wikipedia.org/wiki/Drumtraks (fetched this session) |

Nothing above is source code and nothing is ported. The one capture
measured (`ClapDtrax15.wav`) is analyzed in place under
`~/SamplesFromMars/extracted/free-drums/` per the working scope; the
measurement JSON lives at
`.reference-captures/drumtraks/sfm_free_drums_wav_stats.json`
(gitignored), and nothing from either location is copied into the repo.

## 3. Hardware structure vs the module

**Reference structure:** **13 named percussion voices, 6 individual
output channels (+1 mono mix), 12-voice polyphony** — three separate
numbers, all confirmed this session (§1): vintagesynth's own spec table
literally distinguishes "Sounds: 13" from "Polyphony: 12," and muzines'
1984 review gives the channel grouping explicitly:

| Channel | Voices |
|---|---|
| 1 | Bass Drum |
| 2 | Snare, Snare Rim |
| 3 | Tom 1, Tom 2 |
| 4 | Crash Cymbal, Ride Cymbal |
| 5 | Open Hi-Hat, Closed Hi-Hat |
| 6 | Handclaps, Tambourine, Cowbell, Cabasa |

1+2+2+2+2+4 = 13, matching the named-voice count exactly. **Why 13 named
voices but 12-voice polyphony is not resolved by any source read this
session** — no schematic detail was pulled to settle it (per this task's
scope, the schematic was not independently re-read; Phase 0's entry only
established it as *sufficient to derive architecture*, not as read in
this dossier's own session). The single most likely explanation, by
analogy with every sibling in this family already rebuilt
(`tr909.md` §3, `tr707.md` §3, `sp1200.md` §3 all found Open/Closed
Hi-Hat sharing one physical circuit) and the exact 13→12 arithmetic, is
that **Open and Closed Hi-Hat share one circuit** the same way they do on
every other machine in this survey family — that reading is used in §5's
budget below, but it is an **inference from convention and a numeric
match, not a schematic finding**, and Station B should confirm it against
the elektrotanya schematic before locking in the choke behavior, exactly
as `tr909.md` flagged its own crash/ride sharing.

**Module today: 7 of 13 named voices, and a tom count the hardware does
not have.** `NOTE_MAP` (`drumtraks.py:32-40`) covers Kick (36), Snare
(38), Low/Mid/**Hi** Tom (45/47/50 — **three** toms), Closed Hat (42),
Open Hat (46) — 7 entries. Missing entirely: Snare Rim, Crash, Ride,
Handclaps, Tambourine, Cowbell, Cabasa (6 of the 13 named voices have no
`NOTE_MAP` entry and no code path at all — `data0` values outside
`{36,38,42,45,46,47,50}` fall through `handle_event`'s `if/elif` chain
with `notes` left empty, `drumtraks.py:94-123`, silently producing no
sound). Present but structurally wrong: the module's **three** toms
(Low/Mid/Hi) against the hardware's documented **two** ("toms 1 and 2,"
Wikipedia and muzines both, independently) — the module invented a third
tom pitch the real machine does not have.

**No voice cap at all — the same bug class the task named.** Enumerated
before naming: `grep -n MAX_VOICES lib/audioinstruments/*.py` lists 40
sibling modules that declare one (e.g. `cs80.py:81`, `cr78.py:100`,
`linndrum.py:118`, `dmx.py:134`, `tr606.py:102`) — `drumtraks.py` is not
among them (confirmed by the same enumeration returning no line for this
file), matching the same absence already found and rebuilt-around in
`sp1200.md` §3 and `tr707.md` §3. `handle_event` releases only the same
key (`release_voice(k)`, `drumtraks.py:75-76,85`) and then presses new
notes unconditionally (`drumtraks.py:125-129`), never calling
`_support.trigger_voice`/`steal_oldest` (confirmed: the file's only
`_support` import, `drumtraks.py:44-49`, does not include either name).
And because `key_of()` (`_support.py:194-196`) keys by
`(channel, note_id or pitch)`, Closed Hat (42) and Open Hat (46) get
**distinct keys and do not choke each other** in the current code
(`drumtraks.py:113-117`), even though §3's structural finding above says
they most likely share one physical circuit — the same choke bug
`tr707.md` §3 found in its own hi-hat handling.

**Proposed structural change**, justified by §1/§3's own citations:
rebuild as **12 fixed circuits** (13 named voices, Open/Closed Hi-Hat
sharing one, per the inference above), following the fixed-circuit
pattern `tr909.md`/`tr707.md`/`sp1200.md` already proved out — permanent
`synthio.Note`s retriggered in place, matching how a voltage/ROM-triggered
digital drum machine's circuits actually behave (nothing allocated at
strike time). §5 gives the resident-note budget.

## 4. Modeling approach: synthesis-to-match a ROMpler, not a circuit

Per the module's own file header and Wikipedia's "8-bit digital samples"
(§1), this is a ROM-sample playback machine like `tr707`/`sp1200`, not an
analog circuit — there is no DAFx-style circuit paper to expect and none
was found (§1's "not found" list). Each of the 12 circuits in §5 is
synthesized from primitives and tuned against whatever measurement
exists, the same discipline `tr707.md`/`sp1200.md` used for their own
ROMplers.

**The "8-bit companded PCM" claim, stated as unverified.** The module's
own existing comment (`drumtraks.py:90`, pre-existing code, not written
this session) asserts "Drumtraks uses 8-bit companded PCM, sounded very
gritty when pitched down." This session confirms the "8-bit digital
samples" half (Wikipedia, §1) but found **no source stating companding
specifically** — not the service manual (not re-read this session per
scope) and not the muzines review ("digital chip recordings" is as
specific as it gets). Carried forward as a plausible, unconfirmed legacy
claim, not asserted as fact.

**A candidate native sample rate, flagged, not confirmed.** Angelspit's
page (§1) offers the pack "@ 44.1kHz 16bit and 15625kHz 16 bit" — 15,625
Hz is not a round resampling target, and reads like a genuine hardware
clock division (a companded 8-bit ROM playback engine at a modest sample
rate is exactly the shape of early-80s digital drum machines in this
survey's family). **Not confirmed against the schematic this session.**
If real, Nyquist ≈ 7.8 kHz would be the honest bandwidth ceiling for
every voice, a full octave-plus below `tr707`'s ~13 kHz reference and
consistent with a "grittier"/narrower-band character than that machine's
own ROMpler. Proposed as a literature-flagged target for Station C to
check once the schematic's clock circuit is actually read, not locked in
here.

**Per-circuit approach**, keyed to §5's 12-circuit map, reusing the
module's own existing idioms wherever they already fit:
- **Bass Drum** (`drumtraks.py:94-101`) — keep the SINE tone
  (`hz = 40 + kick_p*60`); the existing conditional SQUARE "grit" layer
  (pressed only `if crunch > 0.1`) is dropped as a *separate resident
  Note* per §5's budget arithmetic (a fixed-circuit voice cannot
  conditionally allocate a second Note at strike time) — its character
  folds into the existing crunch-driven low-pass cutoff
  (`c_filter = 8000 - crunch*4000`, `drumtraks.py:91-92`, already
  present and already doing real work).
- **Snare** (`drumtraks.py:103-111`) — keep the body (SQUARE) + snap
  (NOISE, high-passed) pair unchanged; this is the module's best-matched
  existing voice already.
- **Snare Rim** (new, note 37 per sibling convention — confirmed used by
  `tr808.py:45`, `tr909.py:45`, `tr707.py:40`, `cr78.py:45`, `dmx.py:45`,
  `linndrum.py:45`) — 1 Note, filtered noise click, the same idiom the
  module already uses for hats.
- **Tom 1 / Tom 2** (renamed from Low/Mid/Hi Tom; keep the outer two note
  numbers `45`/`50`, drop `47` — the module's existing tone+bend
  structure, `drumtraks.py:119-123`, unchanged per-tom) — the hardware's
  documented 2-tom count (§3), not the module's invented 3.
- **Hi-Hat** (Open+Closed shared, per §3's inference) — keep the existing
  noise+high-pass structure (`drumtraks.py:113-117`) but move both note
  numbers onto one shared circuit key so they actually choke, closing
  the bug §3 found.
- **Crash** (new, note 49) / **Ride** (new, note 51) — 1 Note each,
  noise-through-bandpass at different center frequencies (Ride more
  tonal/less noisy, matching every sibling's own crash-vs-ride voicing
  choice, e.g. `tr707.md` §4).
- **Clap** (new, note 39, "Handclaps" on the real panel) — 1 Note, noise
  shaped by an amplitude LFO for the flutter, the same idiom
  `tr909.md` §4 proposed and `sp1200.md` §4 used for the same reason
  (budget-constrained single-chain approximation of a recorded sample).
- **Tambourine** (new, note 54) — 1 Note, high-passed noise burst.
- **Cowbell** (new, note 56) — 1 Note, a short metallic tone; the
  codebase has no bell-partial table in this file today (only
  SINE/SQUARE/NOISE, `drumtraks.py:51-53`) — Station B should add one
  via `make_table` the way `tr808.py`'s cowbell does, not invent a new
  toolkit primitive.
- **Cabasa** (new, note 69, matching `linndrum.py:58`'s own convention
  for the same instrument) — 1 Note, short filtered noise, distinct
  from Tambourine mainly by decay/filter shape.

No convolution is proposed anywhere in this instrument; no
`audioconvolve.FRAMES` latency is incurred. No `audiodynamics` need was
identified in anything read this session (no compression/limiting
character documented for this machine's signal path).

## 5. The fixed-circuit map (mandatory)

Per the operating mode's charter and the pattern `tr909.md`/`tr707.md`/
`sp1200.md` all proved: every voice becomes a **permanent set of
`synthio.Note` objects, retriggered in place**, matching how a
ROM-triggered digital drum machine's own voice chips work (each circuit
is always "there," not allocated per hit).

| Voice | Resident Notes | Justification |
|---|---|---|
| Bass Drum | 1 | tone only; crunch folds into the existing filter-cutoff modulation rather than a second Note (§4) |
| Snare | 2 (body + snap) | matches the module's own existing, best-corroborated design (§4) |
| Snare Rim | 1 | filtered-noise click, sibling idiom |
| Tom 1 | 1 | tone, hardware has 2 toms not 3 (§3) |
| Tom 2 | 1 | tone |
| Hi-Hat (Open+Closed) | 1 (shared, retriggered; decay/filter swapped by which key hit) | most likely one physical circuit — the 13-named/12-polyphony arithmetic and family convention (§3); **moderate confidence, not schematic-confirmed this session** |
| Crash | 1 | filtered noise, budget-constrained (see stretch note below) |
| Ride | 1 | filtered noise, more tonal than Crash |
| Clap | 1 | one noise/amplitude-LFO chain, sibling idiom (§4) |
| Tambourine | 1 | filtered noise burst |
| Cowbell | 1 | short tone |
| Cabasa | 1 | filtered noise, shorter/tighter than Tambourine |
| **Total** | **12** | 1 below the 13-note ceiling; matches the hardware's own 12-voice polyphony figure exactly (§3) |

**Optional stretch, if Station B wants it and the schematic confirms
Crash/Ride are independently triggerable (not the shared circuit §3
flags as unconfirmed either way):** the one free resident-Note slot
under the 13-ceiling could go to a second Bass Drum or Snare layer
instead, restoring some of the "grit" character §4 folded into the
filter. Recommendation: ship the 12-Note baseline first — it already
lands exactly on the hardware's own polyphony number, which is a
stronger structural argument than any single stretch choice.

## 6. Acceptance criteria

**Measured (n=1, corroborative only — read with the §1 caveat in
force):** `ClapDtrax15.wav`, measured via
`tools/measure_hits.py "~/SamplesFromMars/extracted/free-drums/Free Drums From Mars/Formats/WAV"
--json .reference-captures/drumtraks/sfm_free_drums_wav_stats.json`
(command run this session against the file in place; 16 WAV files in
that folder measured in total, one per represented machine, only the
Drumtraks-prefixed row used here):

| Statistic | Value |
|---|---|
| Duration | 0.213 s |
| Peak | -1.0 dBFS |
| tau (1/e decay) | 0.030 s |
| T60 (extrapolated) | 0.207 s |
| f_early (0-50ms post-peak) | 1679.6 Hz |
| f_late (100-300ms post-peak) | 1353.8 Hz |
| Spectral centroid | 2804.6 Hz |

Proposed band for Clap: **tau 0.015-0.06 s** (2x either side, single-hit,
no round-robin to average — the same wide-tolerance posture `tr707.md`
§5 used for its own single-hit, unconfirmed-settings rows). Settings are
unconfirmed; the "15" filename suffix may index a tune-grid position
(the paid "Drumtrax From Mars" pack's own naming scheme sweeps "16
tunings of every hit," §1) but nothing read this session confirms that
reading for the free promotional file specifically — **not** treated as
a known setting.

**Literature-derived, unmeasured (every other voice):**

| Criterion | Target | Source |
|---|---|---|
| Voice/channel count | 13 named voices across 6 output channels, 12-voice polyphony | vintagesynth.com spec table; muzines 1984 review (§1, §3) |
| Tune/level range | 16 discrete steps (00-15) per voice, both parameters | muzines 1984 review, "programmable in steps from 00 to 15" (§1) |
| Bandwidth ceiling | possibly ≈7.8 kHz (Nyquist of a candidate 15,625 Hz native rate) | Angelspit page's stated alternate format — **flagged, not confirmed** (§4) |
| Hi-Hat choke | Open and Closed hi-hat should choke each other | inference from the 13-named/12-polyphony arithmetic + family convention — **moderate confidence** (§3) |
| Tom count | 2 toms, not 3 | Wikipedia + muzines, independently corroborating (§3) |

**Measurement method for Station C:** re-run `tools/measure_hits.py`
against `~/SamplesFromMars/extracted/free-drums/.../WAV` exactly as this
session did (in place, nothing copied) for the Clap row; every other row
above has no measured anchor and should be treated as a structural/range
check, not a tau/centroid target, unless the paid "Drumtrax From Mars"
pack (§1) becomes available.

## 7. MCU budget and macro budget

**MCU:** today's module allocates ad-hoc `synthio.Note`s per hit with no
cap at all (§3) — strictly worse for the MCU than a bounded design, the
same finding `sp1200.md`/`tr707.md` made about their own pre-rebuild
code. The fixed-circuit rebuild moves to **12 permanently resident
`synthio.Note` objects** (§5), one below the charter's 13-note ceiling
and matching the hardware's own polyphony figure — a reduction in
worst-case resident state, not an increase. **No `" - lean"` patch is
expected.**

**Macros: 8 today, 16 proposed (the full ceiling).** The panel evidence
justifies going further than `tr707.md`'s per-channel-only design: unlike
the 707 ("the only sound parameter available... is volume"), Drumtraks'
muzines review states plainly that **both tune and level are individually
programmable per voice**, all 13 of them — a real, documented,
per-instrument (not per-channel) control surface. 16 slots cannot cover
26 independent parameters (13 voices × 2), so the same channel-style
grouping `tr707.md` used is applied for the least-central voices, while
the module's four most important existing voices each keep independent
Tune+Level:

| # | Label | Mode | Traces to |
|---|---|---|---|
| 0 | Volume | UNIPOLAR | master output (kept) |
| 1 | Kick Tune | UNIPOLAR | per-voice tune (kept, renamed from "Kick Pitch") |
| 2 | Kick Level | UNIPOLAR | per-voice level (new — muzines: individually programmable level) |
| 3 | Snare Tune | UNIPOLAR | per-voice tune (kept) |
| 4 | Snare Level | UNIPOLAR | per-voice level (new) |
| 5 | Tom Tune | UNIPOLAR | shared Tom 1/2 tune (kept, now correctly 2 toms not 3) |
| 6 | Tom Level | UNIPOLAR | shared Tom 1/2 level (new) |
| 7 | HiHat Tune | UNIPOLAR | shared Open/Closed tune (kept) |
| 8 | HiHat Level | UNIPOLAR | shared Open/Closed level (new) |
| 9 | Cymbal Tune | UNIPOLAR | shared Crash/Ride tune (new voices) |
| 10 | Cymbal Level | UNIPOLAR | shared Crash/Ride level (new) |
| 11 | Percussion Tune | UNIPOLAR | shared Rim/Clap/Tambourine/Cowbell/Cabasa tune — budget consolidation of 5 individually-programmable voices into 1 macro |
| 12 | Percussion Level | UNIPOLAR | same 5-voice group, level |
| 13 | Overall Decay | UNIPOLAR | **not** a panel control — no per-voice decay pot documented anywhere read this session; kept as a synthesis-calibration global, same rationale `tr707.md` §6 used |
| 14 | Crunch/Bandwidth | UNIPOLAR | **not** a panel control — rebound from today's grab-bag (`drumtraks.py:87,91,100-101,116`) to the one thing it can honestly represent: the machine's low-bit/companded-PCM character (§4), itself an unconfirmed legacy claim, flagged accordingly |
| 15 | Master Tune | BIPOLAR | global fine-tune (kept) |

Net: 8 new macros against the charter's 8 free slots — lands exactly at
16/16, the same ceiling `tr909.md` §7 reached and justified the same way
(every slot traces to a real or explicitly-flagged-synthetic need, none
free-floating). The Percussion Tune/Level consolidation (5 voices, 2
macros) is the explicit budget trade that makes 16 fit; if Station C's
listen wants finer control there, the honest escape is dropping "Overall
Decay" (the least panel-grounded of the 16) before adding a 17th, which
would need a contract escalation this dossier does not ask for.

`PATCHES`' patch-0 tuple (`drumtraks.py:29`) must grow from 8 to 16
values to match — Station B's job, not specified further here.

**Operating mode v2:** built unattended; deviations stated in the
evidence pack; blessed at the phase batch listen.
