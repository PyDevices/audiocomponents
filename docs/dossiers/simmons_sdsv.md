# Accuracy Dossier — `simmons_sdsv` (Simmons SDS-V)

**Module:** `audiocomponents/lib/audioinstruments/simmons_sdsv.py` (223 lines)
**Proposed grade:** **gold** — argued up from Phase 0's `literature` call now
that a capture leg exists and was reached, measured in place, and had its
provenance and license read this session. Coverage is real but partial;
§1 states exactly what is and isn't covered before the grade is claimed.
**Reference settings (D3):** partial known-settings. The two Bass Drum
hits are named by pitch (`KickSimB`/`KickSimG#`) and measure a clean
3-semitone interval matching those note names (§1) — genuine known-knob
capture for BD. Snare, the three toms, Open Hat and the bonus "TomFX"
hit are single default-setting captures, not swept grids like `tr909`'s
pack — a statistical, single-point envelope per voice, not a curve.

## 1. Reference and grade

**Primary — capture:** Samples From Mars' "Free Drums From Mars" pack,
already extracted at `~/SamplesFromMars/extracted/free-drums/Free Drums
From Mars/Formats/WAV/` (Brad's, outside the repo, measured in place this
session — never copied here). Of its 16 files, 8 carry the `Sim` suffix
naming the Simmons content: `KickSimB.wav`, `KickSimG#.wav`,
`SnareSim.wav`, `TomSim1.wav`, `TomSim2.wav`, `TomSim3.wav`, `OHSim.wav`,
`TomFXSim.wav`. Measured this session with `tools/measure_hits.py`
(`.reference-captures/simmons_sdsv/sfm_stats_raw.json`, run directly
against the in-place WAV directory, JSON output only — no audio copied
into the repo). Key numbers (44.1 kHz throughout):

| File | tau (s) | f_early / f_late (Hz) | centroid (Hz) | Read as |
|---|---|---|---|---|
| KickSimB | 0.186 | 64.6 / 60.0 | 758 | BD tuned to B (≈61.7 Hz for B1) |
| KickSimG# | 0.157 | 53.8 / 50.0 | 521 | BD tuned to G# (≈51.9 Hz for G#1) |
| SnareSim | 0.101 | 7817 / 4705 | 5777 | noise-dominated; see caution below |
| TomSim1 | 0.099 | 1141 / 860 | 2550 | pitched, clean |
| TomSim2 | 0.096 | 517 / 385 | 2496 | pitched, clean |
| TomSim3 | 0.093 | 215 / 160 | 3032 | pitched, clean |
| OHSim | 0.173 | 21587 / 14870 | 12213 | broadband noise, open-hat length |
| TomFXSim | 0.185 | 1066 / 1090 | 3090 | bent/FX tom, bonus (not NOTE_MAP) |

**Pitch corroboration, not just filenames:** B1→G#1 is a real 3-semitone
interval (12·log₂(61.74/51.91) ≈ 3.00); the measured f_late ratio
(60.0/50.0 = 1.20) gives 12·log₂(1.20) ≈ 3.16 semitones — matches within
measurement noise. This is a genuine known-setting capture, not just a
suggestive filename.

**Provenance — corroborated by vendor catalog, not self-documented on the
free page itself, and that distinction matters:**
- The free pack's own page, https://samplesfrommars.com/pages/free-drum-machine-samples
  (fetched this session), states only "16 Free Tape Drum Machine Samples"
  and "100% analog signal path - no plugin processing whatsoever" — it
  does **not** name Simmons/SDS-V specifically. The file count matches
  exactly (16 files in the WAV folder), which is corroborating but not
  proof of sourcing.
- Samples From Mars' flagship paid pack, **SDSV From Mars**
  (https://samplesfrommars.com/products/sdsv-from-mars, fetched this
  session), documents real hardware: the unit sampled was "in beautiful
  condition and owned by a former Simmons engineer," recorded "API or
  Neve preamp to tape, through Apogee conversion," and explicitly states
  "the flat (no pitch bend) Toms and kicks were tuned with a guitar
  tuner, and we captured every note possible" — which is exactly the
  character measured above (clean tonal toms, named kick pitches).
- The inference chain (same vendor, same "Sim"-suffixed naming
  convention, same file count as advertised, same "flat/tuned" character
  measured) is strong but not a first-party statement on the free page.
  Recorded honestly as **inferred, not confirmed**, provenance.

**What this pack does not cover:** no Closed Hat sample, no Cymbal
sample, no isolated "click" sample, and no swept grid across
Pitch/Decay/Noise/Bend — one hit per voice (two for BD). §6's criteria
table is measured where this pack reaches and stated as literature/
carried-calibration, flagged, where it doesn't.

**Literature (visited this session, corroborates and extends Phase 0's
findings — not re-litigated, re-read):**
- Wikipedia, Simmons SDS-V (https://en.wikipedia.org/wiki/Simmons_SDS-V,
  fetched this session): "The standard SDSV was loaded with five
  modules: Bass Drum, Snare and three Tom Toms, which looked almost
  identical, with controls for noise level, tone level, bend, decay
  time, noise tone (a simple filter) and click drum control which added
  extra attack derived from pad impact... Each module's parameters were
  optimised for the drum it was designed to emulate... Optional Cymbal
  and Hi-Hat modules were also available with open and closed hi-hats
  controlled from an external pedal." This is the load-bearing
  architecture fact for §3–§5: **six independent controls per module**
  (noise level, tone level, bend, decay, noise tone, click), same set on
  every standard module, differentiated only by tuning.
- Simmons SDSV service manual (elektrotanya,
  https://elektrotanya.com/simmons_sdsv_sm.pdf/download.html, fetched
  this session): confirmed as the SDSV service manual; site states
  "Please do not offer the downloaded file for sell only use it for
  personal usage!" — personal-use only, read for circuit-behavior
  derivation, nothing copied or redistributed. Not mined further this
  session (Phase 0 already established this as the literature floor;
  no new page-level circuit detail pulled beyond the Wikipedia
  architecture quote above, which is independently corroborating rather
  than sourced from the manual).
- Cyborg Studio SDS-V page (https://www.cyborgstudio.com/simmons-sds-v,
  fetched this session): offers owner's manual, product overview,
  schematics, and a 45-sample WAV pack (16-bit/44.1kHz) — confirmed to
  carry **no module-architecture description of its own** (checked this
  session; the architecture facts above come from Wikipedia, not this
  page). Site-wide notice: "Copyright © 2010-2025 Cyborgstudio.com All
  Rights Reserved," no specific grant for the reproduced manual/schematic
  or the sample pack. Read for circuit derivation only; its own 45-sample
  pack was not pursued as a second capture source this session since the
  SFM pack already cleared gold and Cyborg Studio's page states no usage
  terms at all for the samples (per Phase 0's own finding, reconfirmed).

**OSS — visited, proxy-oracle value only:** OneTrick SIMIAN
(https://punklabs.com/ot-simian, fetched this session): confirmed GPLv3
("Open source to inspect, learn from, adapt, and improve"); confirmed
"inspired by hexagonal classics like the Simmons SDS-V," not a
schematic-accurate recreation. Per the license gate, usable only as a
rendered-output oracle, never read for structure or ported. Not measured
this session (the SFM capture is the stronger reference and was
prioritized).

**Not found, still:** no DAFx/AES paper on the SDS-V's analog circuits
(none searched this session beyond re-confirming Phase 0's negative); the
GroupDIY forum schematic-scan lead from Phase 0 was not independently
pursued here either, per the same "poor quality, not chased" call.

## 2. License call, per source

| Source | Kind | License as read | Where read |
|---|---|---|---|
| Free Drums From Mars (Samples From Mars), `Sim`-suffixed files | capture | SFM standard Audio Product EULA: "The Audio Products are licensed, not sold, to you to be used for and reproduced within your new musical compositions and productions only... All copying, lending, duplicating, re-selling or trading of any Audio Product or other Content is strictly prohibited" | https://samplesfrommars.com/pages/terms-conditions (fetched this session) |
| Free Drums From Mars, product page | capture (provenance, partial) | n/a — no per-file license text beyond the site EULA above; states only "16 Free Tape Drum Machine Samples," no Simmons-specific claim | https://samplesfrommars.com/pages/free-drum-machine-samples (fetched this session) |
| SDSV From Mars (flagship paid pack), product page | literature/provenance | n/a — not purchased, not measured; read only for the recording-chain and hardware-provenance description quoted in §1 | https://samplesfrommars.com/products/sdsv-from-mars (fetched this session) |
| Wikipedia, Simmons SDS-V | literature | CC BY-SA (Wikipedia standard); facts and short quotes only | https://en.wikipedia.org/wiki/Simmons_SDS-V (fetched this session) |
| Simmons SDSV service manual (elektrotanya) | literature | personal-use only: "please do not offer the downloaded file for sell only use it for personal usage" | https://elektrotanya.com/simmons_sdsv_sm.pdf/download.html (fetched this session) |
| Cyborg Studio SDS-V page (schematics/manual/45-sample pack) | schematic/capture | site-wide "Copyright © 2010-2025 Cyborgstudio.com All Rights Reserved," no specific grant; samples carry no stated terms at all | https://www.cyborgstudio.com/simmons-sds-v (fetched this session) |
| OneTrick SIMIAN (Punk Labs) | oss | GPLv3 | https://punklabs.com/ot-simian (fetched this session) |

Nothing above is source code and nothing is ported. The SFM capture is
analyzed locally under `.reference-captures/simmons_sdsv/` (JSON
statistics only, gitignored); the audio itself stays at
`~/SamplesFromMars`, never copied into this repo, per its EULA and the
task's own scope.

## 3. Hardware structure vs the module

**The real machine: 5 to 7 permanent, independent analog circuits — not
a shared voice pool.** Per Wikipedia (§1, re-confirmed this session): the
standard unit shipped with **5 modules** (Bass Drum, Snare, 3 Tom Toms),
each "almost identical" with its own noise level, tone level, bend,
decay time, noise tone (filter) and click control; **optional Cymbal and
Hi-Hat modules** extended this to 7, with open/closed hi-hat sharing one
physical circuit switched by an external pedal — the same
one-circuit-two-states pattern `tr909.md` found for that machine's
hi-hat.

The module's `NOTE_MAP` (`simmons_sdsv.py:42-51`) already names exactly
these 8 sounds — Bass Drum, Snare, Low/Mid/Hi Tom, Closed Hat, Open Hat,
Cymbal — mapping cleanly onto the hardware's 7 physical modules (hi-hat's
two names collapse to 1 circuit). No `NOTE_MAP` change is proposed.

**But the module today is a dynamic 16-voice pool, not fixed circuits.**
`MAX_VOICES = 16` (`simmons_sdsv.py:99`) drives a generic
`trigger_voice`/`steal_oldest` allocator (`simmons_sdsv.py:104-115`,
`_support.py:237-263`) keyed by `key_of(channel, note_id, data0)`
(`simmons_sdsv.py:123`), building fresh `synthio.Envelope`/`LFO`/
`Biquad`/`Note` objects on every `NOTE_ON` (`simmons_sdsv.py:131-195`) —
the same per-hit-allocation shape `tr808.py` had before its rebuild. This
is more than double even the extended 7-module hardware configuration,
and the SDS-V's "voices" are not an allocatable pool at all: every pad
has its own permanently wired circuit that can sound independently of
every other pad, all the time. Per Brad's rule that the reference decides
structure in both directions, this is a genuine mismatch in the
over-provisioned direction — proposed fix in §5.

**One dispatch detail worth flagging, not fixing here:** the cymbal/hat
branch (`simmons_sdsv.py:177-187`) also catches MIDI notes 44, 51, 57, 59
(pedal-hat, ride, and two more) with no `NOTE_MAP` entry, and currently
renders every one of them identically (noise + high-pass, differing only
by the `is_hat`/`is_open` decay switch) — i.e. today's "Ride" is
indistinguishable from "Cymbal." The hardware has no Ride circuit at all
(only optional Cymbal and Hi-Hat), so this is dead/unlabeled reach, not a
missing voice; §5 proposes dropping it along with the generic
"other percussion" fallback (`simmons_sdsv.py:190-195`), which likewise
has no hardware counterpart.

## 4. Modeling approach, by voice group

**Every standard module gets three signal components, not the module's
current mix.** The Wikipedia architecture quote (§1) names six controls
per module: noise level, tone level, bend, decay, noise tone (filter),
click. Mapped onto `synthio` primitives, that is a **tone oscillator +
bend LFO** (tone level, bend, decay), a **continuous filtered-noise
layer** (noise level, noise tone), and a **short click transient** (click
control) — three independent signal paths per module, uniformly, on
**Bass Drum, Snare, and all three Toms**. The module's current code
already does this for Snare and the Toms (`body`, `noise_note`, `click`
at `simmons_sdsv.py:147-154` and `167-174`) but gives Bass Drum only
`body` + `click` (`simmons_sdsv.py:138-141`), with no continuous noise
layer — an inconsistency against the hardware's own "looked almost
identical" description. §5 proposes closing that gap.

**Bass Drum, pitch confirmed by capture.** KickSimB/KickSimG# (§1) land
within measurement noise of literal B/G# tuning, and both settle around
50-65 Hz — matching the module's existing `bd_pitch` range,
`logmap(30.0, 80.0)` (`simmons_sdsv.py:206`), and its literal default of
50 Hz reasonably well. Decay: measured tau 0.157-0.186 s sits inside the
module's `bd_decay` range `logmap(0.1, 1.0)` (`simmons_sdsv.py:208`), and
its default of 0.4 s is the right order of magnitude, if on the slow
side of what was captured — Station C should retune toward the measured
band, not just confirm the range.

**Snare — pitch not verifiable from this capture; a measurement-ruler
caution, not a finding.** `SnareSim.wav` measures f_early 7817 Hz /
f_late 4705 Hz and centroid 5777 Hz — read plainly, that says "bright
noise," and it is: the SDS-V snare, like its siblings, mixes a pitched
tone with noise, and naive dominant-frequency/centroid measurement is
dominated by the noise energy rather than the underlying ~100-300 Hz
tone the module's `sd_pitch` macro targets (`simmons_sdsv.py:81,209`,
range `logmap(100.0, 300.0)`). This is the same class of ruler problem
`tr909-evidence.md` flagged for centroids computed without band-limiting
— noted here rather than asserted as a wrong pitch. Decay: measured tau
0.101 s is well inside `sd_decay`'s `logmap(0.1, 0.8)` range
(`simmons_sdsv.py:211`), consistent with the module's default 0.3 s.

**Toms — the cleanest pitch data in the pack, and it disagrees with
today's calibration.** All three `TomSim*.wav` files read as genuinely
tonal (low noise content, monotonic f_early→f_late settle): measured
f_late spans roughly **160-860 Hz** across the three files. **The pack
does not label which file is Low/Mid/Hi** — the numbering (`TomSim1`
highest at 860 Hz, `TomSim3` lowest at 160 Hz) is not itself a
documented assignment, so this dossier does not claim which file is
which named tom. What is solid regardless of assignment: the module's
current tom ranges — `lt_pitch` `logmap(50,120)`, `mt_pitch`
`logmap(80,160)`, `ht_pitch` `logmap(120,220)` (`simmons_sdsv.py:212-214`)
— top out at 220 Hz, while the measured span reaches 860 Hz. At least two
of the three measured toms sit above the module's entire Hi Tom range.
This is a real finding for Station B to retune against, not just a
one-voice nuance. `TomFXSim.wav` (bonus, not in `NOTE_MAP`: tau 0.185 s,
f_late 1090 Hz) reads as a heavily bent variant — useful corroboration
for `tom_sweep`'s bend depth, not a fourth criterion.

**Hi-Hat — open captured, closed not; decay is currently hardcoded, not
macro-controlled.** `OHSim.wav` (tau 0.173 s, centroid 12,213 Hz, broadband
noise) is long and bright, consistent with an open hat. The module's
open-hat decay is a **hardcoded 0.3 s constant**
(`simmons_sdsv.py:180-182`: `decay = 0.3 if is_open else 0.05`), not
driven by any macro — `Cymbal Decay` only reaches the non-hat branch of
the same `elif`. Measured 0.173 s is the same order of magnitude as the
hardcoded 0.3 s; Station C should tighten it, and Station B should
decide whether Hi-Hat decay deserves its own macro path or stays
hardcoded (no macro budget exists to give it one — see §7).

**Cymbal, Closed Hat — no capture, literature/current-calibration only,
stated plainly.** Neither sound is in this pack. Their acceptance
criteria (§6) carry forward the module's existing calibration as the
literature-tier target, flagged as unmeasured.

## 5. The FIXED-CIRCUIT map (mandatory)

Per the family pattern `tr909`/`tr707`/`sp1200` proved and the same
rationale (§3): every voice becomes a **permanent set of `synthio.Note`
objects, retriggered in place**, matching how five to seven independent,
always-live analog circuits actually work — nothing allocated at strike
time, nothing released mid-play, no tail ever occupying a slot borrowed
from another pad.

| Voice | Resident Notes | Justification |
|---|---|---|
| Bass Drum | 3 (tone + noise + click) | closes the tone/noise/click gap vs. Snare/Toms (§4); matches the hardware's uniform 6-control module |
| Snare | 3 (tone + noise + click) | already the module's shape; kept |
| Low/Mid/Hi Tom | 3 (1 tone each) | tone only per tom — noise/click consolidated below, the same trade `tr909-evidence.md` made for its own tom-click layer |
| Tom noise/click (shared) | 1 | one shared filtered-noise+click voice, retimbred per tom hit — a budget compression, not a documented circuit-sharing fact (unlike tr909's schematic-confirmed "Tom Noise" line); flagged as such |
| Hi-Hat (open+closed) | 1 | one physical circuit, pedal-switched (§3), matching `tr909`'s hat |
| Cymbal | 1 | one physical circuit, no capture to further decompose |
| **Total** | **12** | 1 below the 13 ceiling, the same margin `tr909`'s rebuild landed on |

The Ride/pedal-hat/"other percussion" dispatch branches noted in §3
(`simmons_sdsv.py:177-187, 190-195`) are dropped entirely — no resident
voice, since the hardware has no circuit behind them and `NOTE_MAP`
never named them.

**The Tom noise/click consolidation is the one structural compromise
here that isn't a hardware fact** — it is a budget trade, not a reading
of a schematic (no SDS-V schematic detail was mined to the block-diagram
level `tr909`'s was). Flagged for Station B and the batch listen the same
way `tr909`'s crash/ride choke was flagged: proposed because it's the
best fit under the ceiling, not asserted as what the circuit does.

## 6. Acceptance criteria

**Measured this session** (`.reference-captures/simmons_sdsv/sfm_stats_raw.json`),
tolerances following the family convention (±30% tau, ±25% pitch unless
noted):

| Voice | tau (s) | pitch (Hz, f_late) | Tolerance | Basis |
|---|---|---|---|---|
| Bass Drum | 0.157-0.186 | 50-65 | ±30% tau, ±25% pitch | measured (2 hits, named pitches) |
| Snare | 0.101 | not usable — see §4 | ±30% tau only; pitch criterion literature-derived from `sd_pitch`'s existing 100-300 Hz range | measured tau; pitch flagged unmeasurable |
| Toms (pooled, identity unassigned) | 0.093-0.099 | 160-860 (span, not per-tom) | ±30% tau; pitch criterion is "module's Hi Tom ceiling must reach ≥860 Hz," not a per-tom point | measured, identity caveat in §4 |
| Open Hat | 0.173 | n/a (noise) | ±30% tau | measured |

**Literature/current-calibration only, not measured this session:**

| Voice | Criterion | Basis |
|---|---|---|
| Closed Hat | decay materially shorter than Open Hat's 0.173 s measured target | module's own hardcoded 0.05 s constant (`simmons_sdsv.py:182`), no capture to check it against |
| Cymbal | decay/spectral profile as currently calibrated (`cymbal_decay` `logmap(0.2, 1.5)`, default 0.8 s) | no capture; carried forward, not verified |

Plus one structural criterion: **12 resident notes, fixed-circuit, per
§5** — a pass/fail on architecture, not a number.

## 7. MCU budget and macro budget

**MCU:** the fixed-circuit map (§5) holds 12 permanently-resident
`synthio.Note` objects, allocated once at `create()` — down from the
current worst-case ~24 ephemeral Notes if all 8 named voices fired in
the same block under today's per-hit-allocation code (3 each for
BD/SD/3-Toms plus 1 each for Hat/Cymbal, using today's shapes). No new
oscillator classes are needed: `SINE`/`NOISE` tables already exist in
the file (`simmons_sdsv.py:62-63`); the shared tom noise/click voice
reuses the same `Biquad`+`Envelope` idiom already used for Snare's noise
layer. **No `" - lean"` patch is expected.** No convolution is proposed
anywhere in this instrument; no `audioconvolve.FRAMES` latency is
incurred. One optional toolkit upgrade, not required: `audiodynamics`
transient shaping on the click layer instead of a raw HP-filtered noise
burst, the same optional recommendation `tr707.md`/`tr808.md` made for
their own click/attack layers.

`MACRO_LABELS` is already at the 16/16 ceiling
(`simmons_sdsv.py:9-13`). **No new macro is proposed, and none is
possible** — the real hardware's 5-7 modules × up to 6 independent
controls each (30-40+ physical knobs, per §4) vastly exceeds any
16-macro surface, so the module's existing choice to share `Click Level`,
`Noise Tone`, and `Noise Level` globally while giving Bass Drum, Snare,
and each Tom their own `Pitch` is already the right kind of compression
— defensible, not hardware-literal. `Tom Sweep`/`Tom Decay` sharing one
macro across all three toms is the same trade. This dossier finds no
macro that lacks a real panel-control ancestor worth reassigning; the
16 stay as they are.

**Unattended run:** built immediately against this dossier; deviations
will be stated in the evidence pack.

**Operating mode v2:** built unattended; deviations stated in the evidence pack; blessed at the phase batch listen.
