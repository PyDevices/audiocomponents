# Accuracy Dossier — `rhodes` (Fender Rhodes electric piano)

**Module:** `audiocomponents/lib/audioinstruments/rhodes.py` (149 lines)
**Proposed grade:** **gold** — confirmed, not re-derived from nothing. The
survey's call holds after independently re-checking the pack's own
per-sound licenses this session (freesound licenses vary by sound, not by
pack, so the pack-level license line was not trusted on its own).
**Reference settings (D3):** partial. The primary capture states the
instrument model and the full signal chain (Fender Rhodes Mark II 73
Stage → Bellari tube preamp → Zoom H4) per sound, but not mic placement or
tine-gap/voicing-screw position — a documented recording chain, not a
fully instrumented lab capture. Treated per D3 as the "known settings at
the level the source actually gives," not required to be knob-exact.

## 1. Reference and grade

**Primary — capture:** tim.kahn, "C_S Fender Rhodes Mark II," Freesound
pack 3957 (https://www.freesound.org/people/tim.kahn/packs/3957/). One
note per file, WAV/AIFF, spanning roughly A#1–G2 (about one octave, low
register) — 12 files total as listed on the pack page; not a full-keyboard
capture. **Re-verified this session, per-sound, not per-pack** (freesound
license is a per-sound field): fetched three individual sound pages
spanning the low and high ends of the pack —
[65762 "G1"](https://freesound.org/people/tim.kahn/sounds/65762/),
[65754 "A#1"](https://freesound.org/people/tim.kahn/sounds/65754/),
[65728 "F2"](https://freesound.org/people/tim.kahn/sounds/65728/) — all
three read **"Attribution 4.0"** (CC BY 4.0), no per-file override found
on any of the three checked (3 of 12, not exhaustive). 65762's page
documents the source: "individual notes sampled from a Fender Rhodes Mark
II 73 Stage Piano, recorded directly from the harp into a Bellari tube
preamp, captured with a Zoom H4." This alone clears gold's bar — capture
reached, provenance read, license read — independent of the Pianobook
pack below, so the grade does not hinge on completing that download.

**Secondary — capture, not independently downloaded:** Pianobook "Wonder
Rhodes," 1976 Rhodes **Mark I** Stage 73, 365 samples across 4 velocity
layers over the full 73-key range
(https://www.pianobook.co.uk/packs/wonder-rhodes/). Re-fetched this
session: the page states the model explicitly as "1976 Rhodes Mk I (Stage
73)" and requires a free-account login to download ("Log in to
download") — same gate the survey found, re-confirmed rather than
inherited. Terms re-fetched at
https://www.pianobook.co.uk/faq/: "all sample packs... should be
copyright free... used... on any commercial and non-commercial
compositions"; redistributing the library itself is forbidden. Corroborates
the freesound capture (a second, larger, real-hardware Rhodes source) but
is not itself the measurement oracle this pass, and is a **different
model era** from the primary capture (§3).

**Literature:** Florian Pfeifle, "Real-time Physical Model of a Wurlitzer
and Rhodes Electronic Piano," DAFx-17
(https://www.dafx.de/paper-archive/2017/papers/DAFx17_paper_79.pdf) —
fetched in full this session; contains an explicit §4.2 "Rhodes
measurements" section validating the model against a real instrument. 1979
CBS/Fender factory service manual, "piano73"
(https://archive.org/details/fender_rhodes-sm) — re-fetched this session
via `archive.org/metadata/fender_rhodes-sm`, confirms `licenseurl:
https://creativecommons.org/licenses/by-nc-nd/4.0/`.

**Also found, not usable:** a JASA paper, "The Rhodes Electric Piano:
Analysis and Simulation of the Inharmonic Overtones" — found this session
via web search, appears to have moved from "under review" (the survey's
prior finding) to a formal JASA listing (vol. 148), but
https://pubs.aip.org/asa/jasa/article-abstract/148/5/3052/631688 returned
**HTTP 403** this session — a dead link is not evidence, so it is not
counted as a source. Its companion code repo,
https://github.com/LOGUNIVPM/rhodes-companion-files, was re-checked this
session: still no LICENSE file, README still says "currently under
review," no DOI or author name visible — unchanged from the survey's
finding, independently re-verified rather than trusted.

**OSS (proxy oracle only):** two MDA ePiano ports were both fetched this
session to resolve a CONFLICT the survey flagged (two passes recorded
different licenses for what looked like one project). They are, in fact,
two different repos with two different, correctly-recorded licenses —
**resolved, not a data error**:
- `elk-audio/mda-vst3` — GPL-3.0, confirmed by fetching
  https://github.com/elk-audio/mda-vst3/blob/master/COPYING this session
  (opens "GNU GENERAL PUBLIC LICENSE / Version 3").
- `elk-audio/mda-vst2` — MIT, confirmed by fetching
  https://github.com/elk-audio/mda-vst2/blob/master/LICENSE this session
  ("MIT License / Copyright (c) 2008 Paul Kellett / Copyright (c) 2019 Elk
  Audio OS").

Neither is a physical model of the tine circuit (Paul Kellett's 2008
FM-style heuristic); neither is used as the primary reference. The GPL
port's *output* is usable as a measure-only proxy per the license gate;
the MIT port's code would be portable if ever wanted, but is not proposed
for porting here — the DAFx paper's physical model is the stronger
reference and is being re-derived, not the MDA heuristic.

Grade verdict: **gold holds.** A real hardware capture was reached this
session with its own provenance and license read at the individual-sound
level (not assumed from the pack), reinforced by a second real-hardware
capture family (Pianobook, corroborating but login-gated) and a
DAFx paper that explicitly validates its physical model against hardware
measurement.

## 2. License call, per source

| Source | License as read | Where read |
|---|---|---|
| Freesound, tim.kahn "C_S Fender Rhodes Mark II" (sounds 65762, 65754, 65728 individually checked) | CC BY 4.0 ("Attribution 4.0") | https://freesound.org/people/tim.kahn/sounds/65762/ (and the two others above), re-fetched this session |
| Pianobook "Wonder Rhodes" | Pianobook standard terms: free for commercial/non-commercial compositions; no redistribution of the library; download gated behind a free account, not exercised | https://www.pianobook.co.uk/faq/, re-fetched this session |
| Pfeifle, "Real-time Physical Model of a Wurlitzer and Rhodes Electronic Piano," DAFx-17 | License unverified — full PDF fetched this session, no copyright/CC statement found in the text; DAFx's own site carries no visible licensing policy. Treated as academic all-rights-reserved: math re-derived below, nothing transcribed | https://www.dafx.de/paper-archive/2017/papers/DAFx17_paper_79.pdf |
| Rhodes Service Manual "piano73" (CBS/Fender, 1979) | CC BY-NC-ND 4.0 | https://archive.org/metadata/fender_rhodes-sm, re-fetched this session |
| `elk-audio/mda-vst3` (GPL physical/heuristic EP plugin) | GPL-3.0 | https://github.com/elk-audio/mda-vst3/blob/master/COPYING, fetched this session |
| `elk-audio/mda-vst2` (MDA ePiano, Paul Kellett) | MIT | https://github.com/elk-audio/mda-vst2/blob/master/LICENSE, fetched this session |
| JASA "inharmonic overtones" paper | Not reachable — HTTP 403 this session; not counted as evidence | https://pubs.aip.org/asa/jasa/article-abstract/148/5/3052/631688 |
| `LOGUNIVPM/rhodes-companion-files` (code for the above) | No LICENSE file, "under review," no DOI — unverified, treated as all-rights-reserved, not used | https://github.com/LOGUNIVPM/rhodes-companion-files, re-fetched this session |
| Wikipedia, "Rhodes piano" (key counts, per-key independence) | CC BY-SA | https://en.wikipedia.org/wiki/Rhodes_piano, fetched this session |
| Chicago Electric Piano Co., "Mark I vs Mark II" (era/tone claim, §3) | No license statement found; used for a factual claim (a commercial dealer's technical page), not ported or redistributed | https://chicagoelectricpiano.com/rhodes/fender-rhodes-mark-i-vs-rhodes-mark-ii/, fetched this session |

Nothing above is ported. The GPL repo's code was not read for structure;
its output would be a measure-only proxy if ever exercised, and was not
exercised this session (no audio was rendered from it). The DAFx paper's
math is described in prose in §3/§6, not transcribed.

## 3. What the machine is, mechanically

Each key drives one independent, purely-decaying mechanical/electrical
chain: a felt- or neoprene-tipped hammer strikes a thin steel **tine**; a
heavier steel **tonebar** clamped beside it stores strike energy and keeps
the tine ringing; a magnetic pickup faces the tine's tip and reads its
motion like a guitar pickup reads a string. Nothing re-excites the tine
after the strike — a Rhodes note can only ever be decaying — and the
pickup's response is not linear with tine displacement: a hard strike
swings the tine through a wider excursion, closer to the pickup, into a
region where the pickup's output is nonlinear (Vintage Vibe / Chicago
Electric Piano's description, cited in `docs/phase2-listening-guide.md`
§3 rhodes item 2; the exact circuit mechanism was not independently
sourced this session either, matching the listening guide's own
"mechanism not sourced" caveat there). That is the origin of the **bark**:
harder playing does not just raise the level, it changes the *timbre*
by driving the pickup nonlinearly, and the effect should vanish — not
merely get quieter — at low velocity.

Because nothing feeds the tine once struck, its upper partials die faster
than the fundamental the tonebar keeps sustaining — a held note is
identified by a continuously falling amplitude that never plateaus, with
the metallic "bell" shimmer of the attack fading into a smoother,
flute-like tone within about a second
(`docs/phase2-listening-guide.md` §3 rhodes item 1). Key-up applies a felt
damper directly to the tine, producing a soft percussive thump distinct
from the ringing tone (item 4, weakly sourced there — only a sample
library documenting deliberately-captured key-off sounds; not
independently re-sourced this session).

**Which era/model the module targets is not stated, and cannot be from
its own code.** The task brief's framing — "1970-73 brighter vs Mark II
darker" — was not found stated that way in any source read this session,
but the underlying claim is real and independently sourced this session:
Chicago Electric Piano Co. describes the early **Mark I** (introduced
late 1969) as having "warmer bass and mids and brighter highs," and the
**Mark II** (introduced 1979) as "a more balanced moderately bright tone
with more bell-like highs and cooler mids and lows" — and notes most of
the actual tonal drift happened gradually across Mark I production, not
at the Mark II relaunch itself. This matters here because the dossier's
two capture families sit on opposite sides of that line: the primary,
license-clear Freesound capture is explicitly a **Mark II**; the
corroborating Pianobook capture is explicitly a **1976 Mark I**. The
module's default patch (`PATCHES[0]`, rhodes.py:35) sets `Tine Level` and
`Body Level` macros to fixed values with no metadata, macro, or comment
saying which era it approximates — there is no way to read the answer out
of the code, and no source read this session pins the module's own
history to one. This is a real gap, not a defect: whichever era Station B
targets should be a stated choice, made against one of these captures, not
left implicit.

## 4. Voice structure and polyphony

**Hardware:** fully polyphonic by construction. Every key has its own
hammer, tine, tonebar and pickup — there is no shared oscillator, no
voice-stealing, and no electronic ceiling at all; the only limit is the
keybed and the player's hands. Production units shipped with 54-, 73- and
88-key keybeds (Wikipedia, "Rhodes piano" —
https://en.wikipedia.org/wiki/Rhodes_piano, the 88-key model introduced
1971). The sampled reference unit (Freesound pack) is a 73-key Stage
piano.

**Module, as read (not measured):** `MAX_VOICES = 16` (rhodes.py:78) caps
`len(voices)` — held **keys**, not raw oscillators — at 16
(rhodes.py:102-103). Each key presses **two** `synthio.Note` objects, a
body oscillator and a tine oscillator (rhodes.py:121-122, 126-127), so 16
"voices" means the module intends up to **32** simultaneous raw Notes.

**A finding independent of any hardware reference, found by reading code,
not by listening:** `synthio.Synthesizer.press()` does not steal a slot
when it is full — it **silently refuses** the press
(`audioif/src/cpython/synthio.py:377-378`: `if len(self._notes) >=
self.max_polyphony: continue`), a deliberate change from the old
evict-the-oldest behavior that used to leak slots (documented in the same
function's own comment, `synthio.py:343-351`, referencing audioif#8/#9).
`max_polyphony` is a compile-time ceiling, not something rhodes.py
controls: **14** in this workspace's own build (confirmed directly —
`python -c "import synthio; print(synthio.Synthesizer(sample_rate=48000).max_polyphony)"`
→ `14`; also the default in the pure-Python fallback,
`synthio.py:271`, and set explicitly for the unix-port build at
`audioif/micropython.mk:113`), **8** in the vst3 plugin build
(`audioif/micropython.cmake:190`), and as low as **2** by CircuitPython's
own stated minimum-guarantee default, "some CP boards raise it to 12"
(`audioif/src/synthio/__init__.h:9-11`).

Because rhodes presses 2 raw Notes per key, the actual silent-drop point
is **7 simultaneous keys** on the most generous build measured here
(14 ÷ 2) — well below the module's own `MAX_VOICES=16` bookkeeping, which
therefore never triggers its own `steal_oldest()` (rhodes.py:90-91,
102-103) before the engine has already started dropping oscillators with
no error, no fallback, and (per the comment above) no theft of a
bystander's slot either — a note just does not sound. This is not a
hardware-fidelity gap; the reference has no such ceiling at all. It is an
internal-consistency defect between the instrument's own housekeeping and
the substrate it runs on. The same `if len(voices) >= MAX_VOICES:
steal_oldest()` idiom with the identical `MAX_VOICES = 16` value appears
verbatim in the other three sustaining pianos in this family
(`wurlitzer.py:67,85`; `pianet.py:66,84`; `clavinet.py:69,87`) — noted
here so whoever drafts those dossiers does not have to re-derive it, not
solved here since it is shared code this dossier's scope does not cover
alone.

**Structure verdict:** hardware polyphony is essentially uncapped (bounded
only by key count, up to 88); the module's stated ceiling (16 keys) is far
below that and, per the program's both-directions rule (roadmap §3), that gap alone would be a
legitimate "raise it, or document the CPU budget" choice like the other
gold pianos. But the more urgent finding is that even the module's own
stated ceiling of 16 is not actually reachable on any build measured here
— the real number the module can deliver today is nearer 7 (desktop) or 4
(vst3 plugin), silently. Station B should treat "what `MAX_VOICES` should
be" and "make the module's own steal-before-drop logic actually protect
against the real ceiling" as two separate fixes, not one.

## 5. Proposed acceptance criteria

Each row is marked **measurable now** (a `tools/render_component.py`- or
`tools/measure_hits.py`-style offline render, note-on only, is sufficient)
or **blocked on #16** (`render_component.py` never sends a note-off —
confirmed this session by grep, no `note_off` call anywhere in that file
— and every one of the four sustaining pianos, rhodes included, holds a
nonzero `sustain_level` with nothing to bring it back down offline).

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Fundamental pitch tracks MIDI note number (A440 reference, equal temperament) within reasonable cents | **measurable now** | Basic sanity check; no reference-specific tuning claim found this session beyond standard equal temperament. |
| 2 | `Master Tune` macro range is a small detune, not a transposition | **measurable now** | Code range is 0.95–1.05× (rhodes.py:145), ±~87 cents; plausible for a "master tune" trim knob, not independently sourced to a factory spec this session. |
| 3 | Attack transient: is there a distinct unpitched "click" in the first ~5-10 ms, separate from the tuned tone? | **measurable now** (offline render + onset spectral analysis) | Listening-guide trait 3 ("a brief unpitched tap... a hair before the note speaks"). **The module has no such element today** — `o_body`/`o_tine` are the only two oscillators pressed on note-on (rhodes.py:121-122, 126-127); read-not-measured finding, not yet a pass/fail number. |
| 4 | Held-note envelope never plateaus at a nonzero level for the render's duration | **measurable now** | This is the single most identifying Rhodes trait per the listening guide ("never plateaus... held or not") and is fully testable with note-on only — no release needed to observe whether the *sustain* portion itself is flat. **The module currently fails this by construction**: `env` has `sustain_level=amp_s` with default `amp_s=0.2` (rhodes.py:71,108) — a classic flat-sustain ADSR, which the guide explicitly names as the *wrong* answer ("it drops after the attack then holds steady like an organ"). |
| 5 | Spectral centroid / high-frequency content falls monotonically over the first ~1-2 s of a held note (tine shimmer fading faster than the body fundamental) | **measurable now** | The two-envelope split (`env` for body, `tine_env` with a fixed fast `decay_time=0.3`, `sustain_level=0.0` at rhodes.py:109) is a reasonable existing approximation of this trait and should largely pass; worth confirming the 0.3 s constant isn't audibly rushed against the reference captures' natural tine decay (not measured this session — captures were not downloaded/analyzed, per the "never redistribute, measure in place" rule, and no local access to the pack's audio was exercised this pass). |
| 6 | Loudness-matched timbre changes with velocity ("the bark") — spectral shape (e.g. high-frequency energy ratio, spectral centroid) differs between a hard and a level-matched soft hit | **measurable now** | The listening guide's own top methodology (play hard/soft, then level-match and re-judge). **The module currently fails this by construction**: velocity only scales `amp` uniformly (`amp = volume * value0 * overdrive`, rhodes.py:106) and the `overdrive` macro (rhodes.py:138: `1.0 + value0*2.0`) is *also* a linear amplitude multiplier — there is no waveshaping, filter, or nonlinearity anywhere in the note path (`lp` is a fixed low-pass at the `tone` macro's cutoff, rhodes.py:111, independent of velocity or "overdrive"). Two identical waveforms scaled by different constants are, by definition, timbrally identical once level-matched — this is exactly the "Wrong: velocity just moves a fader" case the guide names. |
| 7 | Accented note peak stays under clipping at max velocity across the macro ranges | **measurable now** | Straightforward headroom check; not sourced to a specific target, follows the Phase 1 pattern of a hard ceiling. |
| 8 | 7+ simultaneous keys held: does the instrument silently drop notes below its own stated `MAX_VOICES`? | **measurable now, and code already shows it will** | Per §4 — measurable by rendering a chord/cluster beyond the real `max_polyphony` ceiling and checking for missing oscillators in the output, but the defect is already established by reading `synthio.py:377-378` together with rhodes.py's press pattern; a render would confirm, not discover. |
| 9 | Key-off produces an audible, brief, unpitched "thud" distinct from the sustained tone | **blocked on #16** | `release_voice` (rhodes.py:81-88) already builds a noise-through-bandpass burst gated on `key_off > 0.01` — this looks like an existing attempt at the trait, but it is *only* reachable via `EVENT_NOTE_OFF`/a zero-velocity `note_on`, which `render_component.py` never sends (confirmed: no `note_off` call in that file). Cannot be verified offline today. |
| 10 | Release-phase decay: does the tone stop within `Amp Release` rather than ringing indefinitely, and is the release tail audibly different from the sustain-phase tail? | **blocked on #16** | `amp_r` (`Amp Release` macro, rhodes.py:72,143) only affects `synthio.Envelope.release_time`, which is only entered on note-off. |
| 11 | Stereo tremolo: does `Tremolo Depth`/`Tremolo Rate` produce audible amplitude modulation, and is it observable within a held note (no release needed)? | **measurable now** | The ring-mod-plus-opposite-panning trick (rhodes.py:115, 121-122) runs entirely within the note-on/sustain phase; a long render can directly measure the modulation frequency and depth against the `Tremolo Rate`/`Tremolo Depth` macro settings. Not compared against a real Suitcase amp's tremolo circuit this session — no source specifically measuring that circuit's rate/depth range was sought or found. |

**A tooling caveat, found while drafting these:** `tools/measure_hits.py`
fits an exponential decay to silence (down to −50 dB, `measure_hits.py:81`)
and reports a `tau`. With `sustain_level=0.2` and no note-off ever
sent, a rhodes render never approaches −50 dB — the fit would either run
off the end of the render or fit a curve that doesn't describe what's
actually happening (decay toward a nonzero plateau, not toward silence).
Criterion 4 above needs a different, simpler measurement (does the
smoothed amplitude envelope keep falling, yes/no, and by how much per
second) rather than `measure_hits.py`'s existing `tau`/`t60` columns as
they stand. Not fixed here — read-not-measured, a Station B/C tooling
note.

**Found off this dossier's deck, not exercised or relied on:** the
working tree carries **git-untracked** files —
`tools/generate_rig.py`, `tools/render_rig_offline.py`,
`tools/rig_instruments/rhodes.py`, `tools/render_rig.sh`,
`tools/compare_rig.py`, `tools/rig_verify.lua` (confirmed untracked via
`git status --short` this session) — that appear to be in-progress work
toward issue #15 (the DAW listening rig), including a `rig_instruments/
rhodes.py` gesture script that already encodes all five
`phase2-listening-guide.md` rhodes characteristics as timed MIDI
events, and an offline renderer (`render_rig_offline.py:104`:
`inst.note_on(p, 0)`) that **already sends real note-offs**. This was
read (its existence and shape only) but not run and not used to produce
any number in this dossier: issue #16 is explicitly "held deliberately
until the DAW rig lands," and this dossier keeps to that hold rather than
using an uncommitted, unlanded side door around it. Flagged because it
bears directly on this dossier's central constraint and because
uncommitted work sitting in a shared working tree is itself worth Brad
knowing about.

## 6. What the module would need to change (read from `rhodes.py`, not measured)

- **Give the sustain phase a genuine decay, not a flat plateau.** The
  single biggest gap against criterion 4: `synthio.Envelope`'s
  attack/decay/**sustain**/release shape cannot express "keeps fading
  forever" — sustain is definitionally a held level. A tine's free decay
  wants either a very long `decay_time` with `sustain_level` near (not
  at) 0, or a slow one-shot `LFO`-driven amplitude ramp riding under the
  note the way `release_filter` (`_support.py:216-232`) already rides a
  filter cutoff through a release — the same pattern applied to
  amplitude, but starting at note-on instead of note-off, since a Rhodes
  note has nothing resembling a real "sustain" state at all.
- **Make velocity change timbre, not just level, for the bark.** `audiofilters.Distortion`
  (`audioif/src/cpython/audiofilters.py:150-171`) has a `DistortionMode.OVERDRIVE`
  and a `drive` parameter already in the expanded toolkit; wiring `drive`
  (or `pre_gain`) to velocity — rather than the current `overdrive` macro's
  flat amplitude multiply (rhodes.py:138) — would let a hard hit
  genuinely distort while a soft one stays clean, instead of both being
  the same waveform at different volumes. This reuses the existing
  `Overdrive` macro's *name* for a different, toolkit-native mechanism.
- **Add a percussive attack-click element.** No noise/tap component exists
  today (only `o_body`/`o_tine`); the drum dossiers' pattern of a short,
  separately-enveloped noise Note (e.g. `tr808.py`'s click stage) is a
  precedent already in this codebase for the same idea.
- **Fix the `MAX_VOICES`/`max_polyphony` mismatch** per §4: either lower
  `MAX_VOICES` to something the target's real `max_polyphony` can honor
  (2 raw Notes/voice), document per-build behavior explicitly, or restructure
  so `steal_oldest()` is driven by the actual Note count pressed rather
  than the key count, matching `_support.trigger_voice`'s existing
  per-Note accounting (`_support.py:250-257`) rather than rhodes.py's
  own hand-rolled per-key count (rhodes.py:102-103).
- **State the era/model target.** Per §3, pin the default patch (and any
  future "vintage"/"stage" patch) to one of the two capture families on
  record (Mark II via Freesound, or Mark I via Pianobook) rather than
  leaving it implicit, so a later listener knows what "right" means for
  that patch.
- **Key-off thump and release behavior already have code** (rhodes.py:
  81-88) that looks reasonable on inspection but is entirely unverified —
  nothing here proposes changing it before it can actually be exercised
  (#16/#15).

No convolution is proposed anywhere above, so no `audioconvolve.FRAMES`
latency is incurred by any of these changes.

## 7. MCU budget and macro/patch budget

Oscillator count would grow only if the attack-click proposal (§6) is
taken — one additional short-lived noise Note per press, in the same
family as the existing key-off noise burst (rhodes.py:86), not a new DSP
class. The sustain-decay and bark proposals reuse existing
`synthio.Envelope`/`LFO` and the toolkit's own `audiofilters.Distortion`
node respectively — no new oscillator per voice. Whether any of this
exceeds a small-MCU budget, and whether a `" - lean"` patch becomes
necessary, is a Station B/C measurement; nothing here is proposed as
`" - lean"` yet, since nothing has been built or measured.

`MACRO_LABELS` is at 13 of 16 (rhodes.py:9-13), so there is room for a
new macro if the bark rework (§6) needs one (e.g. an explicit "Bark"
amount separate from the current, purely-linear `Overdrive`) without
approaching the 16-macro ceiling. `PATCHES` has one entry today
(rhodes.py:35); nothing here proposes a specific new patch, only that a
future era-specific patch state which capture family it targets (§6).

---

**Awaiting Gate A:** `APPROVE ACCURACY DOSSIER rhodes`
