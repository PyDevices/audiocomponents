# Accuracy Dossier — `linndrum` (Linn LinnDrum, LM-2)

**Module:** `audiocomponents/lib/audioinstruments/linndrum.py` (284 lines)
**Proposed grade:** **literature**, matching Phase 0's survey grade — not
re-litigated, per the brief. The acquisition this run found and measured a
materially stronger capture than the survey's own candidates (below); it is
the strongest hardware evidence reached this session, but its license is
unverified rather than clean, so it is used as the dossier's numeric
backbone without inflating the top-line grade. It is also the concrete,
named unparking path to gold.

## 1. Reference and grade — the acquisition, in full

**Primary capture, fetched and measured — `machines.hyperreal.org`'s
LinnDrum sample set (aka the archive oramics.github.io/sampled mirrors as
`DM/LM-2`).** Reached via oramics' `DM/LM-2` page
(https://oramics.github.io/sampled/DM/LM-2/), which credits its source as
`http://machines.hyperreal.org/manufacturers/Linn/LinnDrum/` — the original
"Music Machines" archive (Hyperreal Organization, a well-known mid-1990s
community archive). That original page was reached directly this session
(`curl`, HTTP 200) and its own manifest text,
`samples/linndrum.txt`, was read in full:

> "These are 44.1 Khz/16 Bit samples of the LinnDrum. The Lin is fitted
> with the standard EPROMs (# 1) except for the conga (#2) and the Tom
> (#6). These samples are brought to you by majortom@muc.de"

This is real provenance, not a bare label: it names the exact sample
rate/bit depth, states which voice families used non-standard (swapped)
EPROMs on this specific unit, and names a contributor — detail that would
be strange to fabricate. `samples/linndrum.zip` (1,135,153 bytes,
`Last-Modified: 31 Jan 1996`) was fetched whole to
`.reference-captures/linndrum/hyperreal/linndrum.zip`, unzipped, and
confirmed to match the manifest exactly: 30 files, 44.1 kHz/16-bit mono,
single hits (one 4.1 s loop, `reallinn.wav`, excluded from measurement).
All 29 one-shots were grouped by voice and run through
`tools/measure_hits.py`; results and per-voice `stats.json` files live
under `.reference-captures/linndrum/hyperreal/by_voice/` (gitignored, not
redistributed). Numbers are in §5.

**Why this stays literature, not gold:** provenance is strong but no
license was ever granted for these files — not even a restrictive one.
oramics' own page tags the LM-2 set "Public Domain," but that tag is
oramics' *own* characterization, not the upstream page's, and this
program's own Phase 0 audit already caught oramics overclaiming a "Public
Domain" tag for a sibling instrument this same way (`cr78`'s oramics entry
was refuted: its true upstream source, Boxed Ear, actually requires "a
license for personal [use]," not public domain — accuracy-survey.md's
license-audit appendix). Applying that same skepticism here: the actual
`linndrum.txt` manifest states no rights at all, just an attribution line.
Per the house rule, absence of a license is recorded as "license
unverified, treated as copyleft" — safe to *measure* (nothing here is
redistributed), not safe to call gold on. Contrast with `tr909`'s gold
capture, which had an explicit "free for personal & commercial use"
statement, or `sp1200`'s, which had a real EULA. This source has neither.
**The unparking path:** confirm the Hyperreal Organization's own
archive-wide terms (defunct since the 2000s, may require an archived
copy) or reach `majortom@muc.de` directly.

**Literature — Elektrotanya's LINN LINNDRUM service manual.** Fetched this
session: https://elektrotanya.com/linn_linndrum_drum-machine_sm.pdf/download.html
— 15.8 MB, 29 pages. Site terms read directly on the download page:
"Please do not offer the downloaded file for sell only use it for personal
usage!" — personal-use only, matching the same restriction already on
record for `drumtraks` and `simmons_sdsv`'s Elektrotanya manuals. Read for
circuit-derivation facts only; nothing copied or redistributed. (The PDF
itself was not text-mined this session — no extraction tool was available,
matching the caution already on record from `tr707.md`; block-diagram
detail beyond what's cited below is unread.)

**Literature — archive.org's LinnDrum Service Notes and Owner's Manual.**
https://archive.org/details/synthmanual-linndrum-service-notes (metadata
re-checked this session at https://archive.org/metadata/synthmanual-linndrum-service-notes:
no `licenseurl`/rights field — license unverified, matching the pattern
this program has found on nearly every archive.org scan). The companion
Owner's Manual (https://archive.org/details/synthmanual-linndrum-owners-manual)
was also opened this session; its page carries no rights field either and
its manual text was not extractable through this tool, so it contributes
nothing beyond confirming the item exists and is unlicensed.

**Corroborating literature — independent technical write-ups, all read
this session:**
- Wikipedia, LinnDrum (https://en.wikipedia.org/wiki/LinnDrum, CC BY-SA) —
  the spec-table source for polyphony, timbrality, sample format, and the
  "tuning for snare, tom and conga only" statement central to §6.
- Vintage Synth Explorer, Linn Electronics LinnDrum
  (https://www.vintagesynth.com/linn-electronics/linndrum) — independently
  confirms the 12-voice/15-sound spec and gives the plain-English sound
  list used to cross-check §3.
- Morphoice, "LinnDrum LM-2 — Architecture, Sound and Legacy"
  (https://www.morphoice.com/linndrum) — the most detailed circuit-level
  source found: confirms µ-law-companded 8-bit EPROM storage, per-voice
  analog output stages, and the shared hi-hat circuit.
- Vintage Synth Explorer forum thread, "LINNDRUM no differences with some
  drum sounds" (https://forum.vintagesynth.com/viewtopic.php?t=57574) —
  a repair/tech thread with first-hand circuit description: "the same
  sample is run through a VCA that is level-controlled and enveloped
  according to which button is pressed," and confirms the hat decay pot
  affects only the closed hat.
- MOD WIGGLER thread on the LM-1's hi-hat circuit
  (https://modwiggler.com/forum/viewtopic.php?t=277962) — the LM-1
  predecessor's hi-hat PROM/VCA mechanism (§6), plus mentions later
  LM-1 revisions added CEM3320 low-pass filters "to minimize the remaining
  8-bit noise" on the kick/tom/conga voices.

**OSS/emulator tier — checked, empty.** The survey's cited wavosaur blog
post (https://blog.wavosaur.com/3-free-linndrum-lm-1-vsti-plugins/) was
re-fetched this session per the brief's instruction to verify the
audit-corrected list myself. It does **not** name GForce iconDrum or Aly
James Lab VLinn (the original survey's mistaken citation, already flagged
"refuted" in the license-audit appendix) — it names **JM-1** (Jun's
Factory) and **DJinnDrum** (SimpleRecorder), plus a third, "Linn LM-1 VST"
(MH Music). All three are described as **freeware**, confirmed
independently at plugins4free.com/plugin/175 (JM-1: "no license type
explicitly stated... free... no link to source code") and via search
corroboration for DJinnDrum (freeware, Windows/Mac binary downloads, no
source). None publishes source code anywhere found this session — freeware
is not open source, so none clears the vision's tier-3 bar ("the best
open-source emulation," §4.3), the same disqualification the survey
originally reached, now confirmed against the corrected names rather than
the wrong ones. No genuinely open-source LinnDrum/LM-1 emulator was found
in a dedicated search this session either.

**Not found / checked and empty this session:**
- **SamplesFromMars, `~/SamplesFromMars/extracted/free-drums`** —
  enumerated in full (`Free Drums From Mars/Formats/WAV/`): 15 files, all
  CR-78, TR-808, TR-909, or Simmons-SDS-V-family ("Sim" prefix) hits. **No
  LinnDrum material of any kind is in this pack.** (A commercial "LinnDrum
  From Mars" collection may exist on samplesfrommars.com, but it was not
  purchased, downloaded, or otherwise reached this session, and is not
  claimed as a source.)
- **Wave Alchemy's "LinnDrum Tape" pack** — the survey's other lead. This
  session went one step further and found the actual download mechanism
  (a base64-encoded S3 URL embedded on wavealchemy.co.uk's product page,
  decoding to `https://wave-alchemy.s3.amazonaws.com/downloads/free_samples/wa_free_drum_machine_collection.zip`)
  and requested it directly: **HTTP 403 Forbidden from S3** — dead this
  session, consistent with (and now stronger than) the survey's
  "unreachable" finding. Wave Alchemy's site-wide Terms & Conditions
  (https://www.wavealchemy.co.uk/terms-conditions/, fetched this session)
  state general no-republish restrictions but nothing specific to free
  sample licensing — moot, since the file itself cannot be reached.

## 2. License call, per source

| Source | Kind | License as read | Where read |
|---|---|---|---|
| Hyperreal "Music Machines" LinnDrum set (`linndrum.zip`, via oramics `DM/LM-2` mirror) | capture (fetched, measured) | **No license stated anywhere in the primary source** (`linndrum.txt`: attribution only, no rights grant). oramics' own "Public Domain" tag is not corroborated by the upstream page and is not relied on, per this program's own `cr78` precedent for the same site overclaiming. Recorded as **license unverified — treated as copyleft**: measured locally as an oracle, nothing redistributed. | http://machines.hyperreal.org/manufacturers/Linn/LinnDrum/samples/linndrum.txt ; https://oramics.github.io/sampled/DM/LM-2/ |
| Elektrotanya LINN LINNDRUM service manual | literature | "Please do not offer the downloaded file for sell only use it for personal usage!" — personal-use only | https://elektrotanya.com/linn_linndrum_drum-machine_sm.pdf/download.html |
| archive.org LinnDrum Service Notes | literature | license unverified — no `licenseurl`/rights field in item metadata | https://archive.org/metadata/synthmanual-linndrum-service-notes |
| archive.org LinnDrum Owner's Manual | literature (unmined) | license unverified — no rights field | https://archive.org/details/synthmanual-linndrum-owners-manual |
| Wikipedia, LinnDrum | literature | CC BY-SA | https://en.wikipedia.org/wiki/LinnDrum |
| Vintage Synth Explorer, LinnDrum page | literature | license unverified — no rights statement; facts only | https://www.vintagesynth.com/linn-electronics/linndrum |
| Morphoice, "LinnDrum LM-2" article | literature | license unverified — no rights statement; facts only | https://www.morphoice.com/linndrum |
| Vintage Synth Explorer forum thread | literature | license unverified — community forum, facts only | https://forum.vintagesynth.com/viewtopic.php?t=57574 |
| MOD WIGGLER forum thread (LM-1 hi-hat) | literature | license unverified — community forum, facts only | https://modwiggler.com/forum/viewtopic.php?t=277962 |
| JM-1 (Jun's Factory) | oss candidate — disqualified | freeware, closed-source, no license text, no source available | https://plugins4free.com/plugin/175 ; https://blog.wavosaur.com/3-free-linndrum-lm-1-vsti-plugins/ |
| DJinnDrum (SimpleRecorder) | oss candidate — disqualified | freeware, closed-source, no license text, no source available | https://blog.wavosaur.com/3-free-linndrum-lm-1-vsti-plugins/ |
| Wave Alchemy "LinnDrum Tape" | capture — unreachable | moot (file 403s); site T&C carry no free-sample-specific grant | https://www.wavealchemy.co.uk/terms-conditions/ ; direct S3 link (403) |

Nothing above is source code and nothing is ported; no emulator qualified
for even a proxy-oracle role this session.

## 3. Hardware structure vs the module

**The real machine: 15 physical output circuits, 16 named sounds (two
share one circuit), 12-voice polyphony.** Independently confirmed by
Wikipedia's spec table ("Polyphonic 12 voices," "Multitimbral 15 parts")
and Vintage Synth Explorer ("Up to 12 sounds are available simultaneously"
across "15 sounds"). Morphoice resolves the 15-vs-16 count precisely:
"sixteen names but fifteen output channels, as the two hi-hat sounds share
a voice with a decay control for the open hat" — i.e. **closed and open
hi-hat are one circuit** (one EPROM loop, gated by an analog VCA; §6), and
every other named sound — bass drum, snare, rimshot, hand clap, hi/mid/lo
tom, hi/lo conga, cabasa, tambourine, cowbell, crash, ride — is its own
circuit with its own rear-panel output. **This is 12 voices of polyphony
across 15 channels** — the channel count itself is not the polyphony
ceiling, unlike `tr707`/`tr909`/`sp1200`, where circuit count and
polyphony matched exactly. That distinction matters for §6.

**Only three voice families are front-panel tunable.** Wikipedia, verbatim:
"Individual level and pan for all sounds, tuning for snare, tom and conga
only." Bass drum, rimshot, clap, cowbell, hats, cymbals, cabasa and
tambourine have **no pitch control on the real machine** — level and pan
only. This is corroborated by the hyperreal capture's own naming
convention: pitch-variant files exist only for `sd`/`snare`
(h/m/l = tune-knob positions), `tom` (h/hh/m/l/ll — see below), and
`conga` (h/hh/m/l/ll), while every other voice has exactly one file.

**The module today: 16 `NOTE_MAP` entries, `MAX_VOICES = 16`
(`linndrum.py:118`), fully dynamic allocation.** No fixed-circuit map, no
per-voice choking beyond the open/closed hat pair
(`linndrum.py:225-238` — this one choke is already correctly modeled).
Two concrete mismatches against the reference found this session:

1. **Crash and Ride are conflated into one "Cymbal" sound.**
   `NOTE_MAP` (`linndrum.py:42-59`) lists only `(49, "Cymbal")`; the code's
   `elif pitch in (49, 51, 57, 59):` block (`linndrum.py:241-247`) already
   *handles* note 51 (Ride) identically to 49 (Crash), it just isn't named.
   Every sibling ROMpler in this family that models cymbals at all
   (`tr909`, `tr808`, `dmx`) keeps Crash (49) and Ride (51) as distinct
   named sounds, matching the hardware fact that LinnDrum's crash and
   ride are two separate circuits with two separate rear outputs
   (Morphoice's voice list). Proposed: split into `Crash`/`Ride`,
   matching sibling convention and the reference both.
2. **`MAX_VOICES = 16` exceeds the reference's 12-voice polyphony ceiling**
   (already flagged by the Phase 0 survey; independently re-confirmed here
   against two sources). Extra headroom, not missing capability — still a
   mismatch worth reconciling (§6).

**Conga count: the reference's baseline is 2, not 3 — with a documented
exception.** Every independent spec source (Wikipedia, Vintage Synth
Explorer, Morphoice) lists exactly **"hi conga" and "lo conga"** — two
voices, matching MIDI convention loosely (module currently uses 62/63/64,
"Conga Hi/Mid/Lo," matching `tr808`'s sibling convention exactly, but
`tr808`'s real hardware genuinely has three congas where LinnDrum's
official spec has two). The hyperreal capture is the one piece of evidence
against a flat "drop the third": its own manifest explicitly flags "the
conga (#2)" as a **non-standard EPROM** on that unit (as opposed to snare,
kick, clap etc., which used "the standard EPROMs (#1)") — and that
non-standard EPROM produced a third, distinct "mid conga" sample
(`conga.wav`, listed in the manifest as plain `Conga = mid conga`) between
the hi and lo files. This is single-source, non-stock evidence, not a
second confirmation — it explains *how* a third conga tone could exist on
a real unit without contradicting the two-conga baseline spec. Proposed
resolution in §6 keeps all three MIDI notes playable without asserting
three independent stock circuits.

**Tom variants:** similarly, the manifest flags "the Tom (#6)" as also
non-standard on this unit, and the archive holds five tom files
(`tomhh`/`tomh`/`tom`/`toml`/`tomll`) against the stock spec's three named
toms (hi/mid/lo, confirmed by every source, and already matching the
module's `41/45/48` note numbers exactly — no note-number change needed).
Read the same way as the congas: five pitch samples from a modified EPROM,
useful as *tuning-range* evidence for three stock circuits, not as
evidence of five stock circuits.

**Kick: possible second stock voice, not acted on.** The archive includes
`kick.wav` and `kickme.wav` ("special Kick") as two *differently-named*
files — unlike the tom/conga pitch variants, this pair was **not** flagged
non-standard (kick used "the standard EPROMs (#1)" per the same manifest
line), which is weak evidence LinnDrum's stock kick EPROM may hold two
selectable tones (paralleling `tr707`'s real BD1/BD2 alternates). No other
source in this session corroborates a second stock kick voice, so this is
recorded as a single-source finding and **not** built into the circuit
budget below — the module's existing single "Bass Drum" matches every
spec-table source's plain "bass drum" (singular).

## 4. Modeling approach: synthesis-to-match, not sample playback

Same posture as `tr707.md`: this is a ROMpler (8-bit, µ-law-companded
EPROM samples per Morphoice — "resolutions of 8-bit"; no analog signal
path worth deriving as a circuit), so there is no DAFx-style circuit paper
to expect, and none was found. Each circuit below is synthesized from
primitives and tuned against the hyperreal measurements (§5), the same
discipline `tr707.md`/`sp1200-evidence.md` used.

**One sample, one VCA/VCF — not a layered analog kick.** The Vintage
Synth Explorer forum's first-hand account is explicit: "the same sample
is run through a VCA that is level-controlled and enveloped according to
which button is pressed." Unlike `tr707`/`tr808`'s swept-VCO analog kicks,
LinnDrum's voices are architecturally a single tone/noise source per
circuit, filtered and enveloped once — the accuracy-correct match is
**one `synthio.Note` per circuit**, not the module's current
`BD`/`SD` two-Note tone-plus-click layering (`linndrum.py:154-160`,
`163-171`). This single-Note match is also what makes the note budget in
§6 work.

**The hi-hat is the one circuit with a real, well-documented analog
gating mechanism.** Three independent sources agree: one hi-hat EPROM
loop is read continuously and gated by an analog VCA; the closed-hat
button additionally opens a discharge path that shortens the VCA
envelope, while the open-hat button lets it ring longer — "every
individual hi-hat has a slightly different sound and volume depending on
where in the loop the sound is" (Vintage Synth Explorer forum, describing
the closely-related LM-1 circuit reused in LinnDrum), and "the hat decay
knob only affect[s] the closed hat's sound" (same thread, LinnDrum-
specific). This matches the module's existing structure almost exactly —
one shared hat circuit, two envelope shapes, closed choking open
(`linndrum.py:225-238`) — and is the one part of this file that needed no
structural correction, only the decay-time recalibration in §5.

**Kick/tom/conga went through an analog VCF, cleaning up 8-bit noise.**
The MOD WIGGLER thread on later LM-1 revisions: CEM3320 low-pass filters
"configured as a lowpass filter with no resonance to minimize the
remaining 8-bit noise from the other voices" on exactly these three
families — the module's existing low-pass filtering on BD (`linndrum.py:155`)
and its bare tone on toms/congas (no filter currently, `linndrum.py:198`,
`205`) should both carry a gentle LP matched to this.

**Bandwidth ceiling, measured.** Wikipedia states "8-bit digital samples,
28–35 kHz" for the ROM sample rate — Nyquist ≈ 14–17.5 kHz. The
hyperreal capture (44.1 kHz redigitization of the real analog output)
confirms this: FFT energy above 17 kHz on the four highest-frequency
voices measured (tambourine, cabasa, crash, open hat) is ≤1.3% of total
spectral energy in every case (measured this session, see §5). Proposed
criterion: **≤~2% of spectral energy above 17 kHz**, matching `sp1200`'s
analogous bandwidth-ceiling criterion in kind.

**Noise floor, measured, not just estimated.** `tr707.md` proposed a
literature-only "-30 to -40 dBFS" plateau target for its cymbal family and
flagged it unmeasured. This dossier has an actual number: the last 20 ms
of `crash.wav`, `ride.wav`, and `ohh.wav` (the pack's three longest-decay,
noise-heaviest voices) settle at **-43.1, -42.2, and -42.5 dBFS relative
to peak** respectively (measured this session). Proposed criterion:
cymbal/hat-family release tails should plateau in the **-38 to -46 dBFS**
range relative to peak.

## 5. Acceptance criteria — measured against the hyperreal capture

All numbers from `tools/measure_hits.py` against
`.reference-captures/linndrum/hyperreal/by_voice/*/stats.json`
(gitignored). Per §1, this capture's license is unverified, so treat
these as strong-but-unlicensed literature numbers, not gold-tier
certainty — same posture `tr707.md` took toward its own best pack.
`n` counts individual pitch-variant files folded into each circuit's
group (§3's tuning-range reading, not independent circuits).

| Voice | τ (s, min/median/max, n) | f_early (Hz, min/median/max) | Centroid (Hz, median) | Note |
|---|---|---|---|---|
| Bass Drum | 0.015/0.026/0.037 (n=2) | 65/65/65 | 455 | both files land on the same fundamental — matches the module's existing default `bd_pitch = 65.0` exactly; **decay is far shorter than the module's default** (`bd_decay = 0.35`; measured T60 only 0.11–0.26 s) |
| Snare | 0.022/0.033/0.051 (n=3, h/m/l tune positions) | 97/151/248 | 6644 | tune-knob range spans roughly 100–250 Hz |
| Rimshot | 0.013/0.024/0.044 (n=3) | 528/1238/2024 | 4691 | no panel tune control (§3); range reflects natural variation, not a knob |
| Clap | 0.036 (n=1) | 1217 | 2614 | single sample only |
| Low Tom | 0.162/0.222/0.282 (n=2) | 65/86/108 | ~809 | |
| Mid Tom | 0.106 (n=1) | 162 | 1026 | single sample |
| Hi Tom | 0.062/0.070/0.079 (n=2) | 205/232/258 | ~1228 | |
| Conga Hi | 0.029/0.036/0.044 (n=2) | 323/409/495 | 1032 | |
| Conga Mid | 0.070 (n=1) | 237 | 812 | non-stock EPROM sample, §3 — reference only, not a stock circuit |
| Conga Lo | 0.112/0.163/0.233 (n=3) | 65/97/151 | ~757 | |
| Cabasa | 0.010 (n=1) | 3079 | 8500 | |
| Tambourine | 0.050 (n=1) | 6320 | 8864 | |
| Cowbell | 0.034 (n=1) | 506 | 1755 | module's current default (`cowbell_pitch` resolves to ≈915 Hz via patch 0) is roughly 1.8x the measured fundamental — recalibrate down |
| Closed Hat | 0.010/0.031/0.044 (n=3) | 4996 (all three) | ~8346 | |
| Open Hat | 0.139 (n=1) | 4996 | 7974 | matches closed hat's onset frequency, differs only in decay — consistent with "one loop, two envelopes" (§4) |
| Crash | 0.336 (n=1) | 538 | 6454 | tail floor -43.1 dBFS rel. peak |
| Ride | 0.417 (n=1) | 2928 | 5569 | tail floor -42.2 dBFS rel. peak; centroid measured *lower* than Crash's — counterintuitive but this is what the one sample shows, not adjusted to expectation |

Plus the two §4 structural criteria: bandwidth ceiling ≤~2% spectral
energy above 17 kHz; noise-floor plateau -38 to -46 dBFS on cymbal/hat
tails (both measured, not literature-estimated, this time).

## 6. Structure, MCU budget, and macro budget

**Proposed: 13 fixed circuits, 13 resident `synthio.Note` objects —
exactly the charter's ceiling**, following the `tr707`/`tr909`/`sp1200`
fixed-circuit pattern. Because each LinnDrum voice is architecturally
"one sample, one VCA" (§4), every circuit gets exactly **one** Note — no
BD/SD tone-plus-click luxury the way analog-voice machines earn one. That
frees the whole budget for circuit *count* rather than per-circuit
layering, which is what this machine's 15-channel reference actually
needs:

| # | Circuit | MIDI notes | Sounds | Basis for sharing |
|---|---|---|---|---|
| 1 | BD | 36 | Bass Drum | reference: one stock circuit (§3) |
| 2 | SD | 38 | Snare | reference: one circuit, tunable |
| 3 | Rim | 37 | Rimshot | reference: one circuit |
| 4 | Clap | 39 | Hand Clap | reference: one circuit |
| 5 | Low Tom | 41 | Low Tom | reference: one circuit, tunable |
| 6 | Mid Tom | 45 | Mid Tom | reference: one circuit, tunable |
| 7 | Hi Tom | 48 | Hi Tom | reference: one circuit, tunable |
| 8 | Congas | 62, 63, 64 | Conga Hi/Mid/Lo | **budget-forced**, not a documented hardware share (contrast `tr707`'s RS/CB, which *is* schematic-confirmed); justified by congas' rolling, rarely-simultaneous performance practice and by §3's own finding that the reference's 12-voice polyphony ceiling is already below its 15-channel count, i.e. *some* cross-circuit contention is a real, if unlocated, hardware property |
| 9 | Cabasa/Tambourine | 69, 54 | Cabasa, Tambourine | **budget-forced**; supported only by the two voices' close measured centroids (8500 vs 8864 Hz, §5) as a spectrally-plausible pairing, not a hardware fact |
| 10 | Cowbell | 56 | Cowbell | reference: one circuit, not tunable (§3) — fixed to the measured ≈506 Hz fundamental, not macro-controlled |
| 11 | Hats | 42, 46 | Closed/Open Hat | **reference-accurate share** — the hardware's own one-loop-two-envelopes circuit (§4), already correctly modeled by the current file |
| 12 | Crash | 49 | Crash | reference: separate circuit (§3) — was conflated with Ride in the current file |
| 13 | Ride | 51 | Ride | reference: separate circuit (§3) — **new**, split out of "Cymbal" |
| | | | **Total** | **13** |

13 circuits, 13 resident Notes, matching the ceiling exactly (synthio's
core caps at 14 simultaneous notes on every runtime; audioif#8/#9 make 13
the safe maximum, same reasoning `tr707.md`/`tr909-evidence.md` used).
Two of the 13 slots (Congas, Cabasa/Tambourine) are budget-forced
consolidations without direct hardware support, flagged plainly above —
if the batch listen or a future capture refutes either, the fix is to
promote it back to its own circuit and find a slot elsewhere, the same
degrade-gracefully posture `tr909-evidence.md` took for its crash/ride
share. **Residual polyphony gap:** 13 simultaneous circuits is still one
above the reference's stated 12-voice ceiling; not solved here, flagged
for Station B's kit-residency check (`tr909-evidence.md`'s "BD survival
through a full-kit hit" pattern is the model to follow).

**MCU:** 13 permanently-resident Notes, each with at most one filter — no
`" - lean"` patch expected, matching the budget every sibling ROMpler in
this family passed at this size. No convolution proposed; no
`audioconvolve.FRAMES` latency incurred.

**Macros: 16 of 16, a genuine squeeze, not headroom.** The reference's own
front panel is bigger than 16 slots can ever hold — "individual level...
for all sounds" alone is 15 independent knobs, on top of the four real
tune knobs (snare, three toms treated together or separately, congas).
The current file spends its 16 macros almost entirely the wrong way for
this machine: 8 of 16 are per-voice **pitch** macros and 4 are **decay**
macros, while only **2 of 15 real per-voice level knobs** (Tambourine,
Cabasa) are represented at all — the reference's actual emphasis (level
balance across a fixed sample set) is nearly absent from the current
macro set. Proposed rebalance, still 16 macros, still fitting exactly:

| # | Label | Mode | Traces to |
|---|---|---|---|
| 0 | Level | UNIPOLAR | master output (kept) |
| 1 | BD Level | UNIPOLAR | panel level knob (new) |
| 2 | SD Level | UNIPOLAR | panel level knob (new) |
| 3 | SD Tune | UNIPOLAR | panel tune knob (kept, renamed from "SD Pitch"; range ≈90–260 Hz per §5) |
| 4 | Rim Level | UNIPOLAR | panel level knob (new) |
| 5 | Clap Level | UNIPOLAR | panel level knob (new) |
| 6 | Tom Level | UNIPOLAR | panel level knobs, folded 3→1 (new, budget fold) |
| 7 | Tom Tune | BIPOLAR | panel tune knobs, folded 3→1 relative offset (consolidated from 3 separate UNIPOLAR macros; defaults at §5's measured medians, ±enough to cover the measured 65–258 Hz spread) |
| 8 | Conga Level | UNIPOLAR | panel level knobs, folded 2(-3)→1 (new, budget fold) |
| 9 | Conga Tune | UNIPOLAR | panel tune knob (kept, already a single macro in the current file; range ≈65–500 Hz per §5) |
| 10 | Cabasa/Tambourine Level | UNIPOLAR | panel level knobs, folded 2→1 (**trade-off**: current file has these as 2 *separate* macros already — this proposal spends that slot elsewhere; flagged, reversible) |
| 11 | Cowbell Level | UNIPOLAR | panel level knob (new; **replaces** the current file's "Cowbell" macro, which is mislabeled — it actually controls pitch, not level, `linndrum.py:276` (`elif data0 == 11: cowbell_pitch = logmap(...)`) vs. the label — cowbell is not panel-tunable per §3, so pitch becomes a fixed ≈506 Hz constant and the slot becomes a real level control) |
| 12 | Hats Level | UNIPOLAR | panel level knob, shared circuit (new) — reference-accurate share, not just a budget fold (§4) |
| 13 | CH Decay | UNIPOLAR | panel/rear decay pot (kept; target τ ≈0.01–0.044 s per §5) |
| 14 | OH Decay | UNIPOLAR | panel/rear decay pot (kept; target τ ≈0.14 s per §5, n=1, wide tolerance) |
| 15 | Cymbals Level | UNIPOLAR | **weakest link**: Crash and Ride are separate reference circuits with (presumably) separate real level knobs; sharing one macro here is a pure budget compromise with no hardware support, parallel in kind to the Congas/Cabasa-Tambourine circuit folds above |

**Dropped from the current file, with reasoning:** BD Pitch, BD Decay,
Clap Decay, SD Snappy, and the old pitch-valued "Cowbell" macro — none
traces to a documented panel control (§3's "tuning for snare, tom and
conga only" explicitly excludes BD/Clap/Cowbell), and Rim Pitch likewise
lacks panel support (§3). Their synthesis roles do not disappear; they
become fixed constants calibrated to §5's measurements (BD decay ≈26 ms
τ, not 350 ms; Clap decay ≈36 ms τ; Cowbell ≈506 Hz) rather than exposed
knobs, freeing the slots for the level controls the reference actually has
many of.

Net: 16 macros in, 16 out — no headroom, unlike `tr707`'s 3 free slots.
If a future revision wants Crash/Ride split back to independent level
macros, something else in this table has to give.

**Operating mode v2:** built unattended; deviations stated in the
evidence pack; blessed at the phase batch listen.
