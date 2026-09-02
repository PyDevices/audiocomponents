# Accuracy Dossier — `wurlitzer` (Wurlitzer 200A Electric Piano)

**Module:** `audiocomponents/lib/audioinstruments/wurlitzer.py` (125 lines)
**Proposed grade:** **gold**, confirming Phase 0's call — re-verified this
session, not inherited. All license text below was re-fetched today; one
of the survey's three capture legs (`GregSullivan.E-Pianos`) turns out to
be the most readily obtainable of the three, which changes the acquisition
story for the better. No audio was downloaded or measured this session —
Station A scope, and the hard constraint on obtaining sample libraries
(§1).
**Reference settings (D3):** known-settings. `wurlitzer` is one of the 14
of 53 instruments the survey found at least one capture source that states
its recording chain and per-note/per-velocity structure
(`accuracy-survey.md:18`); confirmed again this session for two of the
three capture sources (below).

## 1. Reference and grade

Three capture-tier sources were re-visited this session, all reachable,
all license-read directly (not taken from the survey's word):

**Capture 1 — freesound, OldBassMan, single-note pack.**
https://freesound.org/people/OldBassMan/sounds/88000/ — re-fetched this
session. 13-file pack (https://freesound.org/people/OldBassMan/packs/,
"Wurlitzer 200a," published 2010-01-18, 381 downloads at fetch time), one
note per file (`f#6.wav` etc.), 48 kHz/24-bit mono. Description: "sampled
thru a Lundal[h] Transformer and a real Tube Preamp," instrument reported
in good tune. The specific file checked (`f#6.wav`) runs 7.061 s — long
enough that, once obtained, it would carry the note's full decay past a
struck-and-released hammer, not just the attack. **Confirmed this
session, independently of the survey's own note:** the download itself is
login-gated. `curl -I` on the pack's own download link
(`/people/OldBassMan/sounds/88000/download/88000__oldbassman__f6.wav`)
302-redirects to `/home/login/?next=...` — the preview stream is public,
the actual WAV is not. Same acquisition shape as `tr808`'s Splice pack
(`tr808.md` §1): reached, license read, real download step needs an
account — Brad's call, not exercised here.

**Capture 2 — Pianobook, "Unplugged 200A."**
https://www.pianobook.co.uk/packs/unplugged-200a/. Recording chain fully
named: 2× Neumann KM184, Neve 1073 preamp, 48 kHz/24-bit, 3 dynamic
layers + 2 round robins, model confirmed as 200A. Terms re-fetched at
https://www.pianobook.co.uk/faq/ this session (quoted in §2). Download is
behind Pianobook's free account wall — not exercised.

**Capture 3 — `sfzinstruments/GregSullivan.E-Pianos`, Wurlitzer EP200
(the strongest acquisition path of the three).**
https://github.com/sfzinstruments/GregSullivan.E-Pianos — checked this
session via the GitHub contents API rather than assumed from the survey.
**Correction to the survey's own citation:** its `LICENSE` link used
`/blob/main/LICENSE`, which 404s — the repo's default branch is `master`,
not `main` (confirmed via `api.github.com/repos/.../license`, which
resolves on `master`). The license itself is exactly as the survey
recorded — Creative Commons Attribution 3.0 Unported, full legal text
decoded from the API's base64 payload this session — but the citation URL
needed the branch fixed; recorded so the next reader doesn't hit the same
dead link. Corrected URL:
https://github.com/sfzinstruments/GregSullivan.E-Pianos/blob/master/LICENSE.

Contents of `Wurlitzer EP200/Samples/` (checked via the contents API):
**42 FLAC files**, named by key and dynamic layer (`a1pp.flac`,
`a1mp.flac`, `a1f.flac`, `a1ff.flac`, `ab2pp.flac`, ...) — pp/mp/f/ff, up
to four velocity layers per note, some notes fewer. The `.sfz` mapping
(`Wurlitzer EP200.sfz`, fetched raw this session) documents this
explicitly in its `<group>`/`<region>` blocks — e.g. `lovel=1 hivel=37
group_label=pp`, each `<region>` naming its own `sample=`, `tune=`, and
`pitch_keycenter=`. This is a real, checkable, known-settings multisample,
not a single hit. It also states its own playback envelope —
`ampeg_attack=0.001`, `ampeg_hold=5`, `ampeg_decay=25`, `ampeg_sustain=0`
— which describes how the *mapper* chose to play the samples back (a very
long hold/decay so the raw captured decay is heard essentially unedited,
sustain forced to zero since a struck reed does not sustain), not a
hardware-measured time constant; recorded as SFZ authoring metadata, not
cited as a hardware envelope target in §5.

**Unlike the other two, this pack's audio is not behind a login.** The raw
sample bytes are reachable directly at
`raw.githubusercontent.com/sfzinstruments/GregSullivan.E-Pianos/master/Wurlitzer%20EP200/Samples/<file>.flac`
with no authentication (checked by fetching the `.sfz` file itself over
plain `curl`, which succeeded with no redirect). **Still not downloaded
this session** — the instruction to stop and let Brad decide on
obtaining a sample library applies regardless of how easy the fetch would
be; recorded here because it changes which acquisition gap is actually
the blocker for Station B (an account, not a technical wall).

**Literature.** Pfeifle, DAFx-17, "Real-Time Physical Model of a
Wurlitzer and Rhodes Electronic Piano"
(https://www.dafx.de/paper-archive/2017/papers/DAFx17_paper_79.pdf) —
re-fetched in full this session. Confirms the survey's read: an explicit
model of the reed resonator and electrostatic pickup, validated against
hardware measurement, and confirms no copyright/CC statement anywhere in
the PDF or on the DAFx site. One new fact pulled this session that the
survey's note didn't carry: the paper states a reed **fundamental
frequency of 110 Hz** for its worked example — useful as a sanity check
on pitch mapping, not as a program-wide constant (110 Hz is one note, not
a tuning law). No attack/decay time constant in milliseconds was cleanly
extractable from the PDF text this pass; flagged rather than guessed at
(see §5).

Wurlitzer 200/200A factory service manual on archive.org
(https://archive.org/details/wurlitzer-200-and-200-a-service-manual) —
metadata re-checked this session
(`archive.org/metadata/wurlitzer-200-and-200-a-service-manual`): no
`licenseurl` or rights field present, confirming "license unverified,
treat as all-rights-reserved, circuit-derivation reading only."

**OSS — proxy oracle only.** OpenWurli
(https://github.com/hal0zer0/openwurli) — re-fetched this session,
license file re-read directly: GPLv3, confirmed word-for-word ("GNU
GENERAL PUBLIC LICENSE Version 3, 29 June 2007" plus the project's own
copyright footer). Its README (re-read this session) claims seven
modeled stages — modal reed oscillator, electrostatic-pickup
nonlinearity, hammer model, a 12-node Modified-Nodal-Analysis preamp
solver "generated by melange from the actual SPICE netlist," a tremolo
oscillator, power-amp saturation, and a small-speaker cabinet response —
and states the whole chain was "drawn from the real 200A schematic
diagram." Per the license gate (vision §5), this is read for its prose
description of *approach* only; nothing is ported, nothing is read for
implementation detail. Its rendered output was not obtained or measured
this session (would itself need a build/run step outside Station A's
scope).

**Grade rationale.** All three tiers of the hierarchy were reached with
usable, freshly-verified evidence: two independent hardware captures with
documented recording chains (one now known to be obtainable without an
account), a DAFx paper modeling the exact mechanism, a factory service
manual, and a GPL reference implementation traceable to the real
schematic and usable as a measured-output oracle later. That clears the
vision's gold bar — "a hardware-capture source reached, provenance and
license read" — even though no audio was pulled into a measurement this
session. **What would move this from gold-as-reached to gold-as-measured**
is a single acquisition step (an account, or Brad choosing to let a
future Station pull the GregSullivan FLACs given their permissive
license) — recorded as the open item, not treated as done.

## 2. License call, per source

| Source | Kind | License as read | Where read |
|---|---|---|---|
| freesound OldBassMan, "Wurlitzer 200a" pack | capture | Creative Commons Attribution 4.0 (CC BY 4.0) — "You are free to share... and to remix... as long as you credit the author" | https://freesound.org/people/OldBassMan/sounds/88000/ (re-fetched this session) |
| Pianobook "Unplugged 200A" | capture | Pianobook standard terms: "free... to be downloaded and used... on any commercial and non-commercial compositions"; redistributing the library itself forbidden | https://www.pianobook.co.uk/faq/ (re-fetched this session) |
| `sfzinstruments/GregSullivan.E-Pianos`, Wurlitzer EP200 | capture | Creative Commons Attribution 3.0 Unported (CC BY 3.0) — full legal text decoded this session | https://github.com/sfzinstruments/GregSullivan.E-Pianos/blob/master/LICENSE (branch corrected this session; survey's `main` link 404s) |
| Pfeifle, DAFx-17 paper | literature | license unverified — no copyright/CC statement found in the PDF text or on dafx.de; treated copyleft-equivalent (re-derive math, never copy) | https://www.dafx.de/paper-archive/2017/papers/DAFx17_paper_79.pdf (re-fetched in full this session) |
| Wurlitzer 200/200A Service Manual (archive.org) | schematic | license unverified — no `licenseurl`/rights field in the metadata record; all-rights-reserved, circuit-derivation reading only | https://archive.org/metadata/wurlitzer-200-and-200-a-service-manual (re-fetched this session) |
| OpenWurli | oss | GPL-3.0 — confirmed verbatim | https://github.com/hal0zer0/openwurli/blob/main/LICENSE (re-fetched this session; this branch link works) |
| Wikipedia, "Wurlitzer electronic piano" | literature | CC BY-SA 4.0 | https://en.wikipedia.org/wiki/Wurlitzer_electronic_piano (re-fetched this session; the survey's `Wurlitzer_electric_piano` URL is a same-article redirect, confirmed via the API) |

Nothing above is source code and nothing is ported. OpenWurli's GPL code
is never read for structure; only its README's prose description of
approach is used, and its rendered audio (not obtained this session)
would be the only legitimate way to use it as an oracle. The DAFx paper's
math may be re-derived from its equations, never transcribed. No sample
audio was downloaded, copied, or redistributed this session, consistent
with the task's hard constraint.

## 3. What the machine is, mechanically

A felt hammer, driven by conventional piano action, strikes a flat steel
reed. The reed sits inside a cutout in a metal plate held at 170 V DC;
reed and plate form a capacitor, and the changing gap between them *is*
the signal — an electrostatic, not electromagnetic, pickup (Wikipedia,
re-confirmed this session: "striking a metal reed with a felt hammer...
induces an electrical current in an electrostatic pickup system running
at 170 V DC"). Because the pickup's output grows nonlinearly as the gap
closes, a harder strike is not just louder — it drives the reed into a
distorting region of the pickup's response, which is the physical root
of the instrument's signature "bark" at high velocity and "sweet,
vibraphone-like" tone at low velocity (`phase2-listening-guide.md:170-`
onward; Wikipedia's own framing, re-read this session, agrees the
Wurlitzer's output is "closer to a sawtooth wave" against the Rhodes'
"closer to a sine wave"). The 200A specifically added a shield over the
reed/pickup assembly to reduce mains hum versus the plain 200
(Wikipedia). The model 140's onboard tremolo was, per the same source,
"incorrectly labelled 'vibrato'" on the actual panel — it modulates
loudness, not pitch, which the current module's implementation already
respects (§6).

**Not asserted here, per the task's own instruction:** that the
Wurlitzer is *more* velocity-dependent than a Rhodes in magnitude. Each
machine's own velocity mechanism is independently sourced (§3 above for
this one; the Rhodes' tine/pickup mechanism is the survey's own concern,
not re-derived here), but a cross-machine magnitude comparison was
searched for again this session — a fresh read of `phase2-listening-
guide.md` and a re-search of this session's own fetched sources — and not
found stated anywhere. The closest existing statement is a *module-code*
comparison, not a hardware one: the guide's own source-reading pass notes
that among the five modules, only `wurlitzer.py` gives velocity a path to
tone at all, where `rhodes.py` has "no velocity path to the bark"
(`phase2-listening-guide.md:497-501,506`) — a fact about the code as
written, not a claim about which real machine's dynamics swing further.
This dossier does not conflate the two.

## 4. Voice structure and polyphony vs `MAX_VOICES`

**Hardware:** fully polyphonic by construction — every key has its own
independent reed, hammer, and pickup, with no shared oscillator or
voice-stealing circuitry of any kind. Wikipedia, re-confirmed this
session: "Most Wurlitzer pianos are 64-note instruments whose keyboard
range is from A an octave above the lowest note of a standard 88-note
piano to the C an octave below its top note," and "the instrument has
full polyphony." So the real ceiling is the keybed: up to 64 simultaneous
notes, bounded only by how many keys a player's hands can hold down.

**Module:** `MAX_VOICES = 16` (`wurlitzer.py:67`). Each voice allocates
**two** `synthio.Note` objects (`o_reed`, `o_bite` at `wurlitzer.py:100-
101`), so the pool is 16 logical voices / up to 32 raw `synthio.Note`
objects, not 16 raw oscillators.

**Structure verdict, matching the survey's own call for this instrument
(`accuracy-survey.md:830`) and the same shape as its `rhodes` finding
(`accuracy-survey.md:812`):** 16 is well below the
hardware's ~64-note ceiling, and per Brad's both-directions rule (roadmap
§3, "if it was monophonic in real life, it's monophonic here" — read the
other direction here) a genuinely fully-polyphonic reference is a
legitimate case *for* raising `MAX_VOICES`, not evidence the module is
wrong as it stands. This dossier flags it rather than resolving it:
raising it to something nearer 64 doubles at 2 Notes/voice to as many as
128 raw `synthio.Note` objects at full-keybed density, which is a real
MCU-budget question for Station B (§7), not a free change. Recorded as a
proposed structural change, justified by the Wikipedia polyphony source
above; the exact target number is Station B's call once the MCU budget
for this instrument is measured, not proposed here as a specific number.

## 5. Modeling approach, read against the expanded toolkit

The current model (`wurlitzer.py:83-106`) is a two-oscillator additive
design per voice: `o_reed` (fundamental-heavy, `WAVE_REED` at
`wurlitzer.py:44`, harmonics 1-5 with a 0.25 asymmetric soft-clip stage)
carries the body; `o_bite` (`WAVE_BITE` at `wurlitzer.py:45`, odd
harmonics 1-9 with a stronger 0.4 asymmetric clip) carries the grit, with
its own independent, non-macro'd envelope (`attack_time=0.001,
decay_time=0.2, sustain_level=0.0` at `wurlitzer.py:92`) that always
fully decays within about 0.2-0.3 s regardless of what the main `Amp
Decay` macro is set to. Both oscillators share one `synthio.Biquad`
low-pass (`wurlitzer.py:96`) whose cutoff is set once, at note-on, from
`1000 + value0*bark*5000` (`wurlitzer.py:95`) — velocity-dependent, but
frozen for the note's whole life. Tremolo is done correctly in kind: a
`ring_depth_table` biased between unity and a bipolar sine
(`_support.py:139-150`) applied via `ring_frequency`/`ring_waveform`
(`wurlitzer.py:100-101`), which modulates loudness only and cannot move
pitch — matching the sourced "mislabelled vibrato" fact in §3, and the
listening guide's char. 3 ("the pitch never moves") by construction, not
by luck.

Two toolkit-driven improvements the sources above point toward, neither
requiring a new macro:

1. **A time-varying cutoff instead of a frozen one**, using the
   corrected wide biquad already in the expanded toolkit. The listening
   guide's char. 4 — "a hard note should sweeten as it rings out" —  is
   explicitly flagged there as *reasoned from the sourced mechanism, not
   itself documented* (`phase2-listening-guide.md:207-209`, "the guide's
   own §5 also names this as not attempted": `phase2-listening-
   guide.md:513-516`). The physical story in §3 (grit is a function of
   how far the gap has closed, and the gap opens as the reed's swing
   decays) supports tying the low-pass cutoff's decay to the same `Amp
   Decay` macro already driving the amplitude envelope, rather than
   introducing a new control — an envelope-following filter, which
   `audiodynamics`/the wide biquad combination in the expanded toolkit
   supports and the original `synthio.Biquad`-at-note-on approach
   cannot.
2. **Cutoff tracking pitch.** The guide's §5 also flags that a fixed-Hz
   cutoff (rather than one that scales with the played note) may behave
   differently in the bass than the treble (`phase2-listening-
   guide.md:515-517`) — not sourced to a specific hardware fact this session,
   recorded as a plausible toolkit-era fix (key-tracked biquad corner) to
   verify by ear against the captures once obtained, not asserted as
   required.

No convolution is used and none is proposed — no `audioconvolve.FRAMES`
latency is incurred by this instrument, and nothing found this session
argues for adding one (the reference is an electrostatic pickup circuit,
not a cabinet+mic capture chain in need of an impulse response).

## 6. Proposed acceptance criteria

Per the task's measurement constraint: `tools/render_component.py` never
sends a note-off (issue #16), and this instrument's main envelope has a
nonzero sustain level (`amp_s`, default ≈0.197 from patch 0's raw macro
value 25 — `wurlitzer.py:31,61,119`; matches the task brief's "wurlitzer
0.2"). Every criterion below is marked **measurable now** (checkable from
a note-on-only offline render) or **blocked on #16** (needs a real
note-off to observe). A criterion that is measurable now but has no
sourced numeric target this session is marked so explicitly rather than
given a fabricated number.

| # | Criterion | Status | Target / basis |
|---|---|---|---|
| 1 | Fundamental pitch tracks MIDI note × `Master Tune` | **measurable now** | `synthio.midi_to_hz(data0+value1)*master_tune` (`wurlitzer.py:88`) is a deterministic computation; a render's dominant onset frequency should match to well under a cent. Sanity check, not a hardware-fidelity number. |
| 2 | Attack is fast and reed-like | **measurable now**, no numeric target sourced | Default `amp_a` ≈ 8.9 ms (patch 0 raw 2 → `0.001+2/127*0.5`, `wurlitzer.py:59,117`). The DAFx paper describes the reed strike but no clean millisecond attack constant was extracted from its text this session (§1) — this row needs either a re-read of the paper's figures/equations directly (not just its extracted text) or a captured onset, neither done this pass. |
| 3 | Velocity moves both level *and* brightness together (the "bark") | **measurable now** | Render the same note at two velocities (e.g. 20 and 120); `o_bite`'s amplitude and the shared low-pass cutoff both scale with `value0` (`wurlitzer.py:89,95,101`), so spectral centroid / high-frequency energy ratio should rise with velocity. No numeric magnitude target — none of the three capture sources were measured this session (§1), and no cross-machine magnitude vs. Rhodes may be asserted (§3). |
| 4 | Bite decays out faster than the body, independent of the `Amp Decay` macro | **measurable now** | `o_bite`'s envelope is hard-coded (`attack_time=0.001, decay_time=0.2, sustain_level=0.0`, `wurlitzer.py:92`) — this is a self-consistency check on the code, not a hardware-measured number: does the high-harmonic content in a render actually fall away by ~0.2-0.3 s after onset while the fundamental continues per the main envelope? |
| 5 | Tremolo modulates loudness only, never pitch | **measurable now** | With `Tremolo Depth` > 0, a render's amplitude envelope should oscillate at `Tremolo Rate` while the fundamental's frequency bin stays fixed — matches the sourced "mislabelled vibrato" fact (§3) and is structurally guaranteed by the ring-modulation implementation (§5), but worth confirming a render actually shows it. |
| 6 | Held note continues to lose energy rather than plateauing forever | **measurable now, and currently expected to fail** | Real reed physics (§3) says a struck reed continuously loses energy — a Wurlitzer note has no mechanism to hold a fixed loudness indefinitely while a key is held, the same category of finding the listening guide raised for `rhodes`'s sustain plateau (`phase2-listening-guide.md:506-508`, "a held plateau... where characteristic 1 wants one continuous fade"). The module's ADSR literally holds at `amp_s` once the decay phase ends (`wurlitzer.py:91`) — this is checkable **without any note-off**, by rendering several seconds of a held note and confirming the envelope goes flat. No source states a numeric decay-past-sustain curve; this criterion is a structural pass/fail against the physics in §3, not a literature number. |
| 7 | Release/damping character after key-up | **blocked on #16** | `release_time` (`amp_r`, default ≈0.4 s, `wurlitzer.py:62,120`) governs how the note dies once a real note-off arrives; `render_component.py` never sends one, so nothing about how fast, how cleanly, or with what timbral shape the note actually stops can be checked today. This is very likely one of the instrument's most identifying behaviours (§3's "growl melts to sweetness" story plays out over the note's whole life, release included) and is explicitly unmeasurable until #16 lands. |
| 8 | Whether a hard-struck note's bark genuinely "melts" into the sweet tail as it rings out (char. 4) | **partially blocked** | The decay-phase portion (before any note-off) is measurable now per criterion 6's method combined with criterion 3's spectral read; the release-phase portion is blocked per criterion 7. Since the guide itself calls this trait "reasoned, not documented" (§5 above), a failure here is a question to chase, not a verdict to render, per the guide's own framing (`phase2-listening-guide.md:207-209`). |

**Measurement method, once a capture is obtained:** `tools/measure_hits.py`
is built for one-shot drum hits (attack + decay to silence) and is not a
drop-in fit for a sustaining note with no note-off in the render — it
would need either a modified render (a fixed-length hold, analyzed only
over its decay-to-plateau segment) or a genuine note-on/note-off render
once #16 is fixed. `tools/render_component.py` itself has no mode for a
non-drum, non-`NOTE_MAP` instrument like this one: `oneshots`/`kit`
iterate `NOTE_MAP` (`render_component.py:89-107`, wurlitzer has none) and
`phrase` hard-codes drum note numbers (`render_component.py:108-134`).
Station B/C will need a render mode for a single held (and, post-#16,
released) melodic note — noted as a tooling gap, not something this
research-only pass may build (`tools/` is out of scope here).

## 7. MCU budget and macro budget

**MCU, read from the code, not measured:** 2 `synthio.Note` objects per
active voice, one shared `synthio.Biquad` low-pass per voice
(`wurlitzer.py:96`, referenced by both notes), no convolution, no
per-sample custom filter chain. At `MAX_VOICES=16` that is up to 32
resident Notes; §4 flags that a hardware-matched voice count would be
meaningfully higher, which is a real MCU-budget question this dossier
raises but does not settle — Station B should measure the actual
per-Note cost on a target MCU before choosing a new ceiling, and a
`" - lean"` patch (fewer voices, or one oscillator instead of two) is the
natural escape valve (roadmap §7.1) if a hardware-scaled voice count
proves too expensive on small chips. No lean patch is proposed for the
*current* 16-voice, 2-oscillator design — it is already the cheaper of
the two toolkit changes in §5 (an envelope-following filter costs no new
oscillators, only a per-block coefficient recompute).

**Macros: 10 of 16 used** (`MACRO_LABELS` at `wurlitzer.py:9-12`), 6 free
under the ceiling. **No new macro is proposed** for the toolkit changes
in §5 — the time-varying cutoff folds onto the existing `Amp Decay`
macro, and cutoff pitch-tracking (if pursued) needs no macro at all, just
a formula change. The `MAX_VOICES` question in §4, if it lands on a
specific new number, is a code constant, not a macro, and does not touch
this ceiling either. `PATCHES` has one entry (`wurlitzer.py:30-32`),
contiguous from 0, far under the 128-patch limit.

**A read-not-measured note on the wavetables:** both `WAVE_REED` and
`WAVE_BITE` are built with `fast=False` (`wurlitzer.py:44-45`), forcing
the pure-Python scalar table-build path (`_support.py:83-118`) rather
than the `ulab`/NumPy-vectorized one — already a portability-safe choice
per the file's own comment convention (`_support.py:65-67`), unrelated to
and unaffected by the open D6 numerics question (`accuracy-
roadmap.md` §8a), which concerns the vectorized path this file doesn't
use.

**Awaiting Gate A:** `APPROVE ACCURACY DOSSIER wurlitzer`
