# Accuracy Dossier — `clavinet` (Hohner Clavinet D6)

**Module:** `audiocomponents/lib/audioinstruments/clavinet.py` (133 lines)
**Proposed grade:** **literature** — confirmed, not merely inherited from the
survey. This session re-visited every survey source plus several the survey
did not check (vendor sample-pack sites), and found real hardware captures
*exist* — the survey's framing was "no hardware capture pack found," and the
more accurate framing is "hardware captures exist commercially; none were
reached as usable audio this session." That distinction matters for what
Brad should do next (§1), but it does not move the grade: nothing crossing
the gold bar (a capture actually fetched, provenance and license read) was
obtained.
**Reference settings (D3):** no known-settings capture was reached at all,
so this dossier has no statistical envelope to report either — the acceptance
criteria in §6 are literature- and code-derived, not pack-derived.

## 1. Reference and grade

**Primary — literature:**
- DAFx-12 paper, Remaggi/Gabrielli/de Paiva/Välimäki/Squartini, "A Pickup
  Model for the Clavinet"
  (https://www.dafx.de/paper-archive/2012/papers/dafx12_submission_62.pdf).
  Re-fetched and read in full this session (5 pages, all sections). Builds a
  physically grounded model of the D6's magnetic pickup: pickup position
  (comb-filter delay from string-termination distance) and pickup
  nonlinearity (magnetic-flux-vs-displacement curve, fit as a 4th-degree
  polynomial, Table 2). **The paper's own stated test rig is one string**:
  "For a string of 67.8 cm and fundamental frequency of 161 Hz the estimated
  N is 200 for the center pickup (equivalent to 4.2 ms), and 84 for the
  bridge pickup (equivalent to 1.8 ms)" (DAFX-2). Per the brief and the
  listening guide's own caution, **these two delay figures are not used as
  acceptance targets below** — they describe one string's geometry, not the
  instrument's range, and the paper gives no data for how N scales across
  the other 59 strings.
- Hohner Clavinet D6 schematic, hosted at
  https://www.clavinet.com/schematics.php (re-fetched this session; direct
  PDF link confirmed present). Read for topology only, never transcribed.
- Hohner Clavinet D6 owner's manual,
  https://www.clavinet.com/d6man.php (re-fetched this session) — the primary
  source for the Mute, tone-switch (AB/CD) and touch-dynamics language
  quoted in §3.
- Wikipedia, "Clavinet" (https://en.wikipedia.org/wiki/Clavinet), re-fetched
  this session for the exact mechanism and string-count language in §3 and
  §4.

**Hardware-capture leg — found, not obtained, and richer than the survey
recorded:**
- **Straight Ahead Samples, "Freeky Free Clav"**
  (https://www.straightaheadsamples.com/freekyfreeclav), fetched this
  session. **Free** ($0.00), and states plainly it is sampled from "an
  original early-70's Hohner D6 Clavinet," chromatically sampled, 3
  dynamic layers, release samples, with built-in wah/delay/distortion FX
  options. This is a real, free, hardware-provenance find the survey did
  not turn up (its search covered Pianobook, archive.org and freesound, not
  vendor storefronts). It does **not** clear gold this session: the library
  "requires the FULL version of Kontakt 6.71 or higher" — the raw samples
  are locked inside a proprietary Kontakt instrument, not plain WAVs, so
  reaching them needs a licensed copy of full Kontakt as well as the
  download. **Not obtained — flagged for Brad, not acted on**, per the
  task's hard constraint on acquiring packs.
- **Soniccouture "Clav"** (https://www.soniccouture.com/en/products/g45-clav/,
  fetched this session): a genuine hardware-capture product — Soniccouture
  states they "extensively restored and then modified" a real D6 over 12
  months, adding a direct XLR output "to record each pickup separately" and
  an input "to capture the EQ response" of the D6's own preamp. 14,800
  samples, 24-bit/48 kHz, 31 velocity layers, full F1–E5 range. **Paid**
  ($89 at the time of this fetch), no free tier. Not obtained.
- **Keyboard Waves "Clavinet D6"**
  (https://www.keyboardwaves.com/clavinet-d6-pack/, fetched this session):
  "Hohner Clavinet D6 Model sampled thru Radial ProD2 Direct Box," four
  pickup configurations (DA/DB/CA/CB). **Paid** (€17.90 per volume, €29.90
  bundled). Not obtained.

None of the three above were fetched as usable audio this session, so none
clears "captures obtained and usable" — the gold bar stated in the charter.
**If Brad wants to spend an acquisition step, "Freeky Free Clav" is the
cheapest path to a real capture** (free, just Kontakt-locked); the other
two are commercial purchases and squarely his call, not this session's.

**Not found, checked directly this session:**
- archive.org: `title:(hohner clavinet service)` returns 0 results;
  `title:(clavinet)` returns 7 results, all irrelevant (a meme video, two
  3D-printable battery-cover/bezel parts, a plugin-database stub, a
  synth-strings VST bundle, an unrelated composition) — checked via the
  metadata search API directly
  (`https://archive.org/advancedsearch.php?q=title%3A(hohner+clavinet+service)`),
  not just the item-page UI.
- Pianobook: no dedicated Clavinet pack (re-checked by search this
  session — same null result as the survey).
- freesound.org: no isolated single-hit real-hardware Clavinet capture
  surfaced (re-checked this session).
- freewavesamples.com's "Clavinet" instrument tag
  (https://freewavesamples.com/instrument/clavinet, fetched this session):
  ten entries, every one a synth patch named "Clav" (Casio MT-600, Kawai K1/
  K1r/K3, Korg DW-8000/M3R, Ensoniq ESQ-1, M-Audio Venom) — **no real Hohner
  hardware here at all**, useful only as a reminder that "clav" search hits
  are mostly imitations, not the machine.
- TwinCl (https://github.com/thecowgoesmoo/TwinCl) — re-verified this
  session via the GitHub API (`license.key: "mit"`, not archived). Confirms
  the survey's MIT call independently. Still not evidence about the D6: its
  own description is "a modern clavinet design & its digital twin," a new
  low-cost instrument merely inspired by the concept, built and simulated
  from scratch — not counted toward the grade, consistent with the survey.

**A correction to the survey's license framing for clavinet.com** (§2) —
found by checking the site's own terms page, which the survey did not visit:
its `/schematics.php` and `/d6man.php` pages are not merely
"license-unverified," they sit under an explicit **site-wide copyright**
statement reachable from the homepage footer. That does not change how the
sources are treated (already read-only, never ported) but it does replace an
"unverified" call with a verified "all rights reserved" one, which is the
more honest record.

## 2. License call, per source

| Source | License as read | Where read |
|---|---|---|
| DAFx-12 pickup paper | License unverified — read the full 5-page PDF this session, no copyright/CC line anywhere in the text, headers, or references | https://www.dafx.de/paper-archive/2012/papers/dafx12_submission_62.pdf |
| clavinet.com `/schematics.php` (D6 schematic link) | **Verified, not unverified**: site-wide copyright — "All content and materials available on www.clavinet.com... are the intellectual property of Clavinet.Com," reproduction/distribution "strictly prohibited" without authorization | https://www.clavinet.com/terms.php (linked from the homepage footer, fetched this session) |
| clavinet.com `/d6man.php` (D6 owner's manual) | Same site-wide copyright as above | https://www.clavinet.com/terms.php |
| Wikipedia, "Clavinet" | CC BY-SA (confirmed via page footer this session) | https://en.wikipedia.org/wiki/Clavinet |
| TwinCl (GitHub) | MIT (confirmed via GitHub API `license.key: mit` this session) — not evidence about the real D6, not counted toward the grade | https://github.com/thecowgoesmoo/TwinCl |
| Straight Ahead Samples "Freeky Free Clav" | License unverified — no EULA/terms visible on the product page, the site's `/support` FAQ page (checked this session), or a guessed terms URL (404). Per the gate's default rule, treated as copyleft-equivalent: not ported, not measured (not obtained at all) | https://www.straightaheadsamples.com/freekyfreeclav |
| Soniccouture "Clav" | Not read — page shows no EULA text, only a "Terms and Conditions" footer link not followed since the product itself was not pursued (paid, not obtained) | https://www.soniccouture.com/en/products/g45-clav/ |
| Keyboard Waves "Clavinet D6" | Not read, same reason (paid, not obtained) | https://www.keyboardwaves.com/clavinet-d6-pack/ |
| archive.org (search only, nothing found) | N/A — no item reached | https://archive.org/advancedsearch.php?q=title%3A(hohner+clavinet+service) |

Nothing above is ported. The DAFx paper's math is re-derived in prose in
§3/§5, never transcribed as code; the schematic and manual are read for
facts, never redistributed, consistent with their explicit all-rights-
reserved status.

## 3. What the machine is, mechanically

The Clavinet D6 is not a piano — it's closer to a keyboard-controlled
electric guitar. Per key: a rubber-tipped pad "frets the string like a
hammer-on on a guitar" (clavinet.com D6 manual), pressing a tensioned steel
string down onto a fixed anvil. A magnetic pickup reads the resulting
string vibration. Release the key and "the end of each string farthest from
the pick-ups passes through a weave of yarn, which damps the vibrating
string after a key is released" (Wikipedia) — the damper is permanently in
contact except during the instant the anvil holds the string down.

**The pickup system, precisely** (DAFx-12, §2): not one pickup coil per
string. Two pickup **bars**, each "six metal bar coils intended to
transduce ten strings each" — a center pickup and a bridge pickup, sitting
at different distances from the string termination (18.5–6.5 cm center,
4 cm constant bridge), which is *why* they sound different: the comb-filter
notch positions from that fixed geometric distance land at different
frequencies for each. Two panel switches (the manual's "AB, CD" register
tabs) select among four passive combinations (paper's Table 1): center only,
bridge only, both summed anti-phase (thin, damped fundamental), both summed
in-phase (full, deep) — "one of four tabs must be engaged, or the instrument
remains silent" (D6 manual).

**Touch and the "bark."** The manual states plainly: "the string impinges on
the anvil with greater or less strength according to the heaviness of key
pressure, thus affecting the dynamics of the sounding string" — velocity is
real and it is not just loudness. The DAFx paper adds a *sourced mechanism*
the listening guide could not cite: the pickup's flux-vs-displacement curve
is explicitly nonlinear (§3.2, fit to a 4th-degree polynomial, Table 2) — a
harder strike drives a larger string displacement, which pushes further into
the nonlinear part of that curve and injects more high-frequency content
into the pickup's output, on top of any effect of hitting harder. That is a
literature-level basis (not just guitar-string physics in general) for a
velocity-to-brightness path, which the module currently lacks entirely (§6).

**Mute.** A physical slide, "if pushed away from the player, puts a damper
on the strings and produces a dull, dry sound" (D6 manual) — the manual's
own wording ties the mute to *tone* ("dull") as well as *duration* ("dry"),
not duration alone.

**No sustain pedal, structurally.** The manual documents only a foot
*swell* (an optional volume pedal on a separate output jack) — nothing that
holds a note past key-release. The permanent yarn damper is why: unlike a
piano's dampers, it is never lifted by a pedal mechanism.

## 4. Voice structure and polyphony vs the module's `MAX_VOICES`

**Hardware:** 60 keys, F1–E6, "a harp of 60 tensioned steel strings"
(Wikipedia), each with its own key, pad, anvil contact point and yarn
damper — fully independent triggering and damping per note. The pickup
coils are shared in groups of ten strings per bar (DAFx-12 §2), but that
sharing is a passive electromagnetic summation, not a switched or
voice-stolen resource — every struck string contributes to the pickup
output simultaneously regardless of how many others are also sounding. That
refines, not contradicts, the survey's conclusion: **hardware polyphony is
the full 60 keys, no voice-stealing**, for a more precise reason than
"individually pickup-monitored" (survey's phrasing) — the strings are
independently *struck and damped*; the pickups are shared per ten-string
bar and simply sum.

**Module:** `MAX_VOICES = 16` (clavinet.py:69) gates `len(voices)`
(clavinet.py:87), i.e. **held keys**, not raw oscillators — each held key
costs **two** `synthio.Note` objects (`o_cb`, `o_da`, clavinet.py:107-108),
so a full pool is 32 concurrent oscillators for 16 concurrent notes.

That is well below the reference's 60, the same pattern the survey already
noted across this whole instrument family (rhodes, wurlitzer, pianet, cp70
all cap similarly below their hardware's full keybed). Given no sustain
pedal exists on this instrument (§3) — held notes are bounded by how many
fingers and how long a chord decays, not by an indefinite pedal-held stack —
16 is a much less severe practical limit here than it would be for an
instrument with a working sustain pedal (e.g. rhodes). Per Brad's rule the
reference decides structure in both directions; nothing here argues for
raising `MAX_VOICES` to 60, and this dossier does not propose it — it costs
2 oscillators/key already, doubling to accommodate 60-key clusters that no
player's two hands can physically produce would spend MCU budget with no
audible payoff. It is recorded as a real, measured gap rather than silently
accepted, in case Station B's own judgment differs.

## 5. Modeling approach, with the expanded toolkit

The module today is plain `synthio`: two fixed wavetables
(`WAVE_CB`/`WAVE_DA`, clavinet.py:45-46), one shared `Biquad`
(low-pass or band-pass, clavinet.py:105), one shared `Envelope`
(clavinet.py:97), one optional `LFO`-driven `Math` node for wah
(clavinet.py:101-103). None of the toolkit additions the vision names
(`audiodynamics`, `audioroute`, convolution, ring mod, feedback delay,
saturation curves, the corrected wide biquad) are used. Three concrete,
sourced places they could go, without exceeding the 16-macro ceiling
(11 of 16 used today, clavinet.py:9-13):

1. **Velocity-to-brightness, sourced to DAFx-12 §3.2.** The pickup
   nonlinearity model gives a literature basis (not just guess-work) for
   a harder strike injecting extra harmonic content, which the module has
   no path for today (§6). A saturation-curve stage from the toolkit,
   driven by `value0` (velocity) rather than a fixed constant, would give
   this a home without a new macro — or with one, if the character needs
   an amount knob (room exists: 5 of 16 macro slots free).
2. **True in-phase/anti-phase pickup mixing, sourced to DAFx-12 Table 1 and
   the D6 manual's AB/CD switches.** Today `pickup_mix` (clavinet.py:56)
   is a linear amplitude crossfade between two *different* wavetables —
   it never phase-inverts one against the other, so the hollow,
   fundamental-cancelling "anti-phase" register the paper and the manual
   both document cannot be reached. `audioroute`'s parallel branches with a
   polarity option are a natural fit, replacing the two-oscillator sum with
   an explicit 4-position or continuous phase parameter. This is the same
   gap the listening guide's characteristic 4 already flagged from the
   listening side ("never phase-inverted"); this session found the circuit
   reason it can't be, in the paper's own switch table.
3. **No convolution is proposed.** The DAFx paper describes only "an
   amplifier stage, with tone control and pickup switches" internal to the
   instrument (DAFx-12 §2) — no speaker cabinet in the signal path, unlike
   the Rhodes/Wurlitzer's amp-and-speaker chain. Nothing here calls for
   `audioconvolve`, so no `FRAMES` latency is incurred by this proposal.

## 6. Proposed acceptance criteria — measurable now vs blocked on #16

Per the task's framing: attack, onset timbre, and steady-state tone while a
key is held can be rendered and measured today (`render_component.py` never
sends note-off, but that only removes the *release* phase — the envelope's
attack→decay→sustain-plateau transition happens automatically at note-on and
needs no note-off to observe). What depends on key-release — and that is
most of what makes this instrument recognizable per the listening guide's
own characteristic 2 — is blocked.

No numeric hardware target is available from any source reached this
session (no capture was obtained; the DAFx paper's only numbers, the 4.2 ms
/ 1.8 ms comb delays, are explicitly one-string figures the guide already
warned not to generalize, so they're excluded here rather than misused as a
tolerance band). Every row below is therefore a **qualitative pass/fail**,
sourced to a specific claim, not a measured tolerance — a materially weaker
evidentiary footing than Phase 1's drum criteria, and that gap is the
honest state of a literature-graded instrument with no reachable capture.

**Measurable now:**

| # | Criterion | Source | What "pass" looks like |
|---|---|---|---|
| 1 | Attack transient differs in brightness, hard vs. soft velocity, level-matched | DAFx-12 §3.2 (pickup nonlinearity vs. displacement); guide char. 1 | Spectral centroid or high-frequency energy in the first ~20 ms is measurably higher at velocity 127 than at velocity 1, after loudness-matching. **Predicted to fail as coded** — `amp = volume * value0` (clavinet.py:91) is the only velocity path; brightness is untouched by velocity anywhere in the file |
| 2 | Pickup-mix extremes are two distinct timbres, not one filtered continuum | DAFx-12 §2 (bright bridge vs. warm center); guide char. 4 | Spectral centroid/odd-even harmonic ratio measurably differs between `pickup_mix=0` (WAVE_DA, odd harmonics only, clavinet.py:46) and `pickup_mix=1` (WAVE_CB, full series, clavinet.py:45) |
| 3 | An anti-phase pickup sum is thinner/hollower than an in-phase sum | DAFx-12 Table 1; D6 manual AB/CD switches; guide char. 4 | **Cannot pass as coded** — no phase-invert path exists (§5 item 2); this criterion currently has no macro setting that produces it at all |
| 4 | Brilliance macro sweeps a real spectral rolloff | clavinet.py:99 (`cutoff = 1000 + brilliance*6000`) | Measured -3dB rolloff point tracks the macro's 1–7 kHz range across its sweep |
| 5 | Wah produces a periodic, audible cutoff sweep during a held note | clavinet.py:101-103 | Time-varying spectral centroid oscillates at `wah_rate` (0.5–10.5 Hz per clavinet.py:123) with amplitude scaling with `wah_depth` |
| 6 | Mute shortens decay/sustain but — per the manual's own "dull" wording — should also darken the tone | D6 manual ("dull, dry sound"); clavinet.py:93-95 (decay/sustain shortened, no cutoff term) | **Predicted to fail as coded**: `cutoff` (clavinet.py:99) has no `mute_lvl` term at all, so spectral rolloff is identical at Mute 0 and Mute max — only duration changes, contradicting "dull" |
| 7 | A struck string's decay is a continuous fade, not a hold at a fixed nonzero plateau | Physical mechanism, §3; DAFx-12's own DWG model has no discrete "sustain" stage at all — excite, then a continuously decaying resonant string | **Predicted to fail as coded**: `sustain_level=actual_s` (clavinet.py:97) defaults to 0.1 and holds there indefinitely once decay completes — a real plucked/struck string keeps decaying rather than plateauing. This is measurable now because it concerns what happens *while a key is still down*, before any release |

**Blocked on #16 (needs a real note-off, per the task's framing):**

| # | Criterion | Source | Why blocked |
|---|---|---|---|
| 8 | Note dies immediately on key-up, pedal or no pedal | D6 manual ("negated the possibility of obtaining sustain via a foot pedal"); guide char. 2 | Needs `note_off` to observe the release phase at all |
| 9 | Release is nearly instantaneous, not a fade | Same | `release_time` (`amp_r`, clavinet.py:64/128) ranges 0.01–1.01 s — whether that tail is audible can't be checked without a render that actually releases |
| 10 | Fast repeated notes stay discrete ("nothing rings, so nothing smears") | Guide char. 3 | Depends on real silence between hits, i.e. on note-off timing relative to the next onset |

**A structural note, not a criterion, worth recording here:** the module
never handles `EVENT_CONTROL_CHANGE` at all (clavinet.py's `handle_event`
only branches on `EVENT_NOTE_ON`/`EVENT_NOTE_OFF`/`EVENT_PARAMETER`) — CC64
sustain pedal is a silent no-op today. That happens to be **exactly
correct** per the manual's own statement that the pedal cannot sustain a
note — a rare case where doing nothing is already the right answer, and
worth stating so it is not "fixed" by accident later.

## 7. MCU budget and macro budget

**Tables:** `WAVE_CB`, `WAVE_DA` (2048 samples/4 KB each) and `SINE`
(2048/4 KB) build once at import (clavinet.py:45-47, module scope, not
inside `create()`), ~12 KB fixed, shared across every instance — no
per-instance or per-note table cost.

**Per-note cost, current:** 2 `synthio.Note` objects + 1 shared `Biquad`
filter + up to 1 `LFO`/`Math` node (wah) + 1 shared `Envelope`, per held
key. At the 16-voice ceiling that's up to 32 Notes, 32 filters (one per
Note — `filter=lp` is passed to both `o_cb` and `o_da` individually,
clavinet.py:107-108, so it's actually shared *object* but bound per-Note)
and up to 32 wah LFO/Math nodes live at once. **Not measured this session**
(no render harness exists yet for a melodic sustaining instrument — see
§6's opening note) — flagged for Station C rather than asserted.

If Station B adopts the toolkit's corrected wide biquad in place of the
plain `synthio.Biquad` (§5), the vision's own caution applies directly:
"the wide biquad already tripled Cortex-M0+ cost." With up to 32 filter
instances already in play at full polyphony, that tripling is a real budget
question on small targets — this dossier flags it as **an open question for
Station B to measure, not resolved here**, and a `" - lean"` patch (fewer
voices, or the plain biquad retained) is a plausible outcome if the number
comes back high.

**Macros:** 11 of 16 used (clavinet.py:9-13); 5 free. The two additions
proposed in §5 (a velocity-brightness amount, a phase/pickup-position
control) both fit without contract escalation.

## 8. What the module would need to change (read from `clavinet.py`, not measured)

- **Add a velocity-to-brightness path.** Today `value0` only scales `amp`
  (clavinet.py:91); nothing touches `cutoff` or the wavetable mix by
  velocity. §5/§6 items 1 give the sourced justification.
- **Give the mute macro a tone term, not just a duration term.** `cutoff`
  (clavinet.py:99) has no `mute_lvl` input; only `actual_d`/`actual_s`
  (clavinet.py:94-95) do. The manual's own "dull" language wants the
  cutoff to drop as `mute_lvl` rises.
- **Reconsider the nonzero default `sustain_level`.** A struck/plucked
  string has no physical "hold" stage; `synthio.Envelope`'s ADSR shape
  forces one. Either drive `sustain_level` toward 0 as the honest target,
  or treat the "sustain" plateau as a very slow continuation of the same
  decay rather than a flat hold — a modeling choice, not a bug, but one
  worth an explicit decision rather than the current default inherited
  from a generic ADSR template.
- **Give the pickup switches real phase behavior**, replacing the linear
  `pickup_mix` crossfade (clavinet.py:107-108) with an in-phase/anti-phase
  sum per DAFx-12 Table 1 / the D6 manual's AB-CD tabs (§5 item 2).
- **Tighten `release_time`'s ceiling.** `amp_r` (clavinet.py:64,128)
  reaches just over 1 second at the macro's top; the manual describes an
  instrument that "negates the possibility of obtaining sustain" at all.
  Once #16 unblocks measurement, this is the first place to look for an
  audible mismatch against char. 2.
- **`EVENT_CONTROL_CHANGE` needs no change** — see §6's structural note;
  recorded here only so a future pass doesn't "add" pedal handling that
  the reference says should not exist.

None of the above has been built or measured; every line in this section is
a reading of `clavinet.py`, stated as such.

---

**Awaiting Gate A:** `APPROVE ACCURACY DOSSIER clavinet`
