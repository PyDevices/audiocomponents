# Accuracy Dossier — `pianet` (Hohner Pianet)

**Module:** `audiocomponents/lib/audioinstruments/pianet.py` (123 lines)
**Survey's grade:** gold (`accuracy-survey.md:55`, `:780-796`)
**Proposed grade:** **literature — downgraded from the survey's gold.**
**Reference settings (D3):** no known-knob capture of the correct machine
exists; criteria below are literature-derived and qualitative, not a
statistical envelope (D3 does not apply — there is no usable capture to
average across).

## 0. The finding that changes the grade

The Pianet line is two different instruments wearing one name, and they do
not sound alike:

- **1962–1977 ("first group"):** ground stainless-steel reeds, an
  **electrostatic (variable-capacitance) pickup**, leather-faced pads.
  Models C, L, M, N, N v2, Combo.
- **1977–1983 ("second group"), the Pianet T/M:** rolled spring-steel
  reeds, an **electro-magnetic pickup** "similar to the Rhodes," silicone
  pads.

(Both spans and the pickup-technology split are Wikipedia, "Hohner
Pianet," CC BY-SA — fetched fresh this session, not carried over from the
survey.)

This program's own `phase2-listening-guide.md` already states the
consequence plainly, sourced independently of the survey: *"A mellow,
chorus-y wash is the **later** magnetic-pickup Pianet T/M, not the machine
on the records"* (`phase2-listening-guide.md:277-278`). The record most
associated with the instrument, the Zombies' "She's Not There" (Rod
Argent), was recorded 12 June 1964 — thirteen years before the Pianet T
existed. So the "machine on the records" cannot be a T; it is necessarily
a first-group, electrostatic-pickup unit. (Recording date: search results
this session, corroborating the pre-1977 argument already implicit in the
listening guide; not independently re-verified against a primary Zombies
discography source.)

The survey's gold capture — Greg Sullivan's E-Pianos "Hohner Pianet T
(type 2)," CC BY 3.0 — is a real, well-documented hardware capture. It is
gold-tier evidence **for the wrong machine.** The mechanism these two
pickups produce is not a cosmetic difference: Wikipedia's "Electrostatic
pickup" article (CC BY-SA 4.0, fetched this session) states the Pianet's
fixed plate sits at 90° to the reed, so "capacitance changes most
dramatically when the reed is in the upper portion of its travel. The
result is a large second-harmonic content in the resulting signal,
similar to that produced by a fuzz box distortion pedal." Nothing in any
source read this session or carried from the survey makes the equivalent
claim about the T's magnetic pickup, and the listening guide's own ear-test
language ("mellow, chorus-y" vs. "bright, nasal, thin... buzzy at the
front") describes two different timbres, not one timbre at two
loudnesses. A rebuild measured against the T capture would be accurate to
a real machine that is not the one the reference brief, the listening
guide, and the instrument's own popular identity all point at.

**Conclusion: retarget the reference to the first-group (electrostatic)
Pianet.** That retargeting is what forces the grade down — see §1.

**A correction to the survey's own text, noted rather than silently
fixed:** the survey's pianet entry itself calls the capture "the later
Pianet T (**electrostatic** pickup)" (`accuracy-survey.md:782`). That is
backwards — Wikipedia's own model-year breakdown (§0, fetched fresh this
session) has the electrostatic pickup on the *earlier* (1962-1977) units
and the T on the *later* (1977-1983) electro-magnetic ones. The survey's
underlying conclusion (capture is of the wrong variant) was right; its
stated reason (which pickup the T has) had the two pickup types swapped.
Recorded here so the next reader of the survey does not inherit the
swap.

## 1. Reference and grade

**Tier 1 (hardware capture) search, for the correct machine:** No
free/permissively-licensed capture of a first-group Pianet was found this
session. One real hardware capture exists — Purgatory Creek Soundware's
"Pianet N" Kontakt library, its own product page (fetched this session,
https://www.purgatorycreek.com/index.php/product/pianet-n-kontakt/)
stating a real "electro-mechanical reed-based piano manufactured between
1965 and 1967," eight velocity layers "recorded for the full duration...
neither loops nor artificial envelope decays," with note-off release
samples included. That is the correct model, described with real
provenance. It is also a **$9.95 paid product** with **no EULA or license
text found anywhere on the site** (the front page and product page were
both fetched this session; no terms link exists on either). Per this
task's hard constraint, it was not purchased, so **nothing was obtained
or measured** — recorded as found, not as evidence.

Two freeware plugins targeting a Pianet were also found and read directly
this session, neither usable as a tier-1 capture:
- **Artifake "Planet_N"** (https://sites.google.com/site/artifakelabs/,
  fetched this session): its own page calls it "a recreation of the
  Hohner Pianet N," freeware, with a single tremolo on/off parameter — no
  license text, and "recreation" plus a near-empty parameter list reads as
  a synthesized emulation rather than sample playback.
- **Mokafix "Glue Reeds"**
  (https://plugins4free.com/plugin/1518, fetched this session): its own
  description states it "is based on reactive synthesis and captures that
  reed EP sound by reproducing both the reed motion and pickup response"
  — explicitly a physical model, not samples. No license text on the
  download page. Freeware per multiple secondary listings (rekkerd.org,
  KVR), not independently confirmed on a page carrying license terms.

Neither is a hardware capture; at best each is a **tier-3 proxy-oracle
candidate** (§5 says why neither is used as one this pass either).

**Tier 2 (literature), for the correct machine:** Genuine OEM Hohner
schematics for the first-group Pianet family — models C, L, M, N, N v2,
CH-amp, Combo — are hosted at clavinet.com/schematics.php (fetched this
session; the same archive the survey already used for `clavinet`'s D6
schematic). The Pianet N schematic PDF
(https://www.clavinet.com/Pianet_N_schematic.pdf) was fetched and read in
full this session (not just confirmed to exist): it is a legible,
complete circuit — the reed/electrode pickup is DC-biased at **+400 V
through a 20 MΩ resistor**, feeding a germanium-transistor gain chain
(AC125/AC107 stages) with three tapped outputs (100/300/600 mV), plus an
optical vibrato modulator (a lamp and an ORP60 photoresistor driving a
light-dependent resistor in the signal path, with speed and depth pots).
This is real circuit detail sufficient to ground the pickup's high-bias,
high-impedance, nonlinear character described qualitatively by the
Wikipedia electrostatic-pickup article above — the two sources corroborate
each other independently.

**What this makes the grade.** Tier 1 exists and is usable — for the
wrong machine (T). Tier 1 exists for the right machine (Purgatory Creek)
but is unusable this pass (paid, unobtained, license unverified). Tier 2
exists and was read for the right machine. Per the hierarchy (vision §4),
that is **literature**, argued down from the survey's gold for the same
reason `clavinet` already carries that grade: a reachable capture is not
a capture *of the target*. This is not a new instance of the pattern —
it is the resolution the survey itself flagged as "left to dossier
stage" (`accuracy-survey.md:782`, `:796`).

**The T capture is not worthless — it is demoted to secondary.** The
pluck/damp *mechanism* (pad drags the reed until the bond breaks, pad
re-lands to kill it) is shared across every Pianet variant; only the
pickup differs. So the T pack remains usable as a corroborating source
for onset-transient *shape* and release *behavior* (§4), just not for
the pickup's tonal color, which is the trait most sources single out.

## 2. License call, per source

| Source | License as read | Where read |
|---|---|---|
| Greg Sullivan's E-Pianos, Pianet T (type 2) | CC BY 3.0 Unported | https://raw.githubusercontent.com/sfzinstruments/GregSullivan.E-Pianos/master/LICENSE (re-fetched this session) — wrong model, see §0 |
| Pianobook "Anne-Marie the Hohner T" | Pianobook standard terms: "used... on any commercial and non-commercial compositions"; "forbidden to sell or redistribute the sample libraries" | https://www.pianobook.co.uk/faq/ (re-fetched this session) — wrong model |
| Pianobook "Hohner Pianet T" (eBay-sourced) | same Pianobook standard terms | same FAQ page — wrong model |
| Hohner Pianet T Service Manual (archive.org) | license unverified — no `licenseurl`/rights field in the metadata record | https://archive.org/metadata/sm_Hohner_Pianet_T_Service_manual (re-fetched this session) — wrong model |
| Purgatory Creek "Pianet N" (Kontakt, paid) | **license unverified** — no EULA/terms found on the product page or the site's front page; paid, not obtained | https://www.purgatorycreek.com/index.php/product/pianet-n-kontakt/ and https://www.purgatorycreek.com/ (both fetched this session) |
| Artifake "Planet_N" (freeware) | no license text found on its own page; treated **unverified, copyleft-equivalent** until shown otherwise | https://sites.google.com/site/artifakelabs/ (fetched this session) |
| Mokafix "Glue Reeds" (freeware) | no license text on the download page | https://plugins4free.com/plugin/1518 (fetched this session) |
| Hohner Pianet-family schematics (C/L/M/N/N v2/CH-amp/Combo) | license unverified — spare-parts vendor site, no site-wide statement | https://www.clavinet.com/schematics.php (fetched this session) — correct model family |
| Wikipedia, "Hohner Pianet" | CC BY-SA (standard Wikipedia terms) | https://en.wikipedia.org/wiki/Hohner_Pianet (fetched this session) |
| Wikipedia, "Electrostatic pickup" | CC BY-SA 4.0 | https://en.wikipedia.org/wiki/Electrostatic_pickup (fetched this session) |

Nothing above is ported. The clavinet.com PDF was read for circuit
topology only, in full compliance with the license gate — no code or
schematic image is reproduced here or anywhere in the module; the
component values quoted in §1 are restated in prose, not copied as an
image or netlist.

## 3. What the machine is, mechanically

A sticky leather- (later silicone-) faced pad sits at the end of each
key. Pressing the key drags a tuned steel reed against the pad's grip
until the bond breaks at a roughly fixed tension and the reed snaps free,
ringing — a **pluck on the way down**, not a struck note. The same pad
returns to the reed on release and kills the vibration immediately: there
is no sustain pedal, and none is physically possible, because the damper
*is* the key (`phase2-listening-guide.md:221-224`, `:243-251`, itself
tracing to clavinet.com's Pianet history — not independently re-fetched
this session).

The first-group pickup reads the reed electrostatically: a fixed plate at
90° to the reed's swing, DC-biased through a very high resistance (20 MΩ
per the schematic, §1), so the reed's motion modulates capacitance rather
than inducing a current the way a magnetic pickup does. Because the plate
geometry makes capacitance change fastest near the top of the reed's
travel, the signal carries a strong second harmonic — described in the
literature as "similar to... a fuzz box distortion pedal" (§0). The
second-group (T) pickup is magnetic, reading the reed's velocity the way
a Rhodes tine pickup does, and the listening guide's own ear-test
description ("mellow, chorus-y") is consistent with that being a
smoother, less second-harmonic-forward mechanism — though no source read
this session puts a number on the T's own harmonic content specifically,
so that comparison is qualitative only.

## 4. Voice structure and polyphony

**Hardware:** fully polyphonic, one independent reed+pickup+pad per key,
no electronic voice limiter of any kind — 61 keys (F1–F6) on first-group
units, 60 on second-group (Wikipedia, "Hohner Pianet," fetched this
session, matching the survey's existing citation).

**Module:** `MAX_VOICES = 16` (`pianet.py:66`), an arbiter over *held
keys*, not raw oscillators — `len(voices) >= MAX_VOICES` triggers
`steal_oldest()` (`pianet.py:84-85`). Each held key allocates **two**
`synthio.Note` objects, `o_body` and `o_pluck` (`pianet.py:98-104`), both
released together through `voices[k]` (`_support.py:199-214` iterates
`voice[0]`, confirmed by reading, handles a multi-Note tuple correctly).

Two separate findings follow, and they should not be conflated:

1. **Hardware (60–61) vs. the module's own declared ceiling (16).**
   Same pattern as every other instrument in this family (survey:
   "sits well below that ceiling, consistent with the same pattern seen
   across this family," `accuracy-survey.md:792`). Not a defect on its
   face — fidelity is not a synonym for capability, and 16 held notes
   already exceeds what a two-hand comping part on a piano-family
   instrument typically wants. Flagged, not proposed to change, per the
   family precedent.

2. **The module's own declared ceiling (16 keys × 2 Notes = up to 32) vs.
   what its `synthio.Synthesizer` can actually deliver.** This is an
   internal-consistency question, independent of the hardware-fidelity
   one, and it is **read from code, not measured by ear or by render.**
   `synthio.Synthesizer.max_polyphony = 14` in the CPython target
   (`audioif/src/cpython/synthio.py:271`), and a press beyond that count
   is **silently refused, not stolen** — confirmed by reading
   `Synthesizer.press()`: `if len(self._notes) >= self.max_polyphony:
   continue` (`audioif/src/cpython/synthio.py:377-378`), with the
   surrounding comment stating this mirrors real CircuitPython's
   `synthio_span_change_note` exactly. The MicroPython usermod build
   matches that 14 for desktop/unix/wasm targets
   (`cmods/audioif/micropython.mk:98-113`,
   `CIRCUITPY_SYNTHIO_MAX_CHANNELS=14`), but the general CMake/MCU build
   sets it to **8** as "a deliberately modest middle ground... well below
   desktop/wasm's 14" (`cmods/audioif/micropython.cmake:173-190`) — and
   real upstream CircuitPython's own header default is **2**, raised
   per-board (raspberrypi: 24, nordic/mimxrt10xx: 12) per that same
   comment block. So on the CMake MCU default, an 8-Note chord — **four**
   pianet keys — already saturates the whole synth; a fifth key's second
   Note (whichever of `o_body`/`o_pluck` presses second) is silently
   dropped, not stolen from an older voice. On desktop/CPython's 14, an
   eighth key already exceeds it. `MAX_VOICES = 16` therefore promises
   more simultaneity than the underlying synth can seat on **any**
   target this workspace builds for, well before the module's own
   `steal_oldest()` ever engages (that only fires past 16 *keys*, i.e.
   32 Notes — a state the synth can never actually reach). **Not
   measured by rendering** this pass; Station B should render a
   6–8-note chord and check for a silently-missing pluck transient or
   body layer on one or more notes, on both the CPython and the
   MicroPython-usermod target.

This second finding is not unique to pianet — `rhodes`, `wurlitzer` and
`clavinet` all declare `MAX_VOICES = 16` too (`rhodes.py:78`,
`wurlitzer.py:67`, `clavinet.py:69`) and, from the one sibling checked
this session, `wurlitzer` also spends two Notes per key
(`o_reed`/`o_bite`, `wurlitzer.py:100-101`) — but confirming it as a
family-wide pattern is outside this instrument's deck; flagged here for
whoever next touches those modules, not claimed as measured fact about
them.

## 5. Proposed acceptance criteria

No numeric hardware measurements were taken this pass — the only reachable
capture of the *correct* machine is a paid product that was not obtained,
and the correctly-licensed capture that *was* measured-in-principle
(GregSullivan, CC BY) is of the wrong model (§0) and was not fetched for
measurement for that reason. Every criterion below is therefore
**qualitative / literature-derived**, not a statistical envelope; a
future pass that obtains a licensed first-group capture (Brad's call) can
convert these to numbers.

| # | Criterion | Target (source) | Status |
|---|---|---|---|
| 1 | Timbre is nearly velocity-invariant | fortissimo and pianissimo renders of the same note, level-matched, should be very hard to distinguish by spectral shape — "one-dimensional... similar to the electric guitar" (Logos Foundation, via `phase2-listening-guide.md:236-241`, not independently re-fetched this session) | **measurable now** — render the same pitch at multiple velocities (no note-off needed), compare spectral centroid/flatness while held |
| 2 | Onset carries a brief unpitched "pluck-pop," not a thud | "a small spring letting go" (`phase2-listening-guide.md:257-262`) | **measurable now** — analyze the first ~10–20 ms of a held-note render |
| 3 | Onset is harmonically complex, clears to a simpler tone within a fraction of a second, while still held | "a complex mixture of harmonics when the reed is first struck, which later reduces to a cleaner sustained tone" (Wikipedia, "Hohner Pianet," fetched this session) | **measurable now** — compare spectral flatness/harmonic count in the first ~100 ms vs. 1–2 s into a held note, no note-off required |
| 4 | Second-harmonic content is prominent — a "fuzz box"-like signature, not merely present | Wikipedia, "Electrostatic pickup," fetched this session (§0) | **measurable now** — measure the 2nd-harmonic:1st-harmonic ratio on a held steady-state tone; no numeric target sourced, only "large"/prominent, so pass/fail is comparative against the module's current wavetable (§6), not an absolute number |
| 5 | Brighter/thinner in the octave or two above middle C than in the bass | listening guide, flagged there as **unsourced** — "no source read this pass makes a register-by-register claim" (`phase2-listening-guide.md:272-276`) | **measurable now in principle**, but **not adopted as a criterion** — the listening guide's own caveat stands; carried here only so a later reader sees it was considered and declined, not overlooked |
| 6 | The note stops **dead** on release, not a fade, and a hold pedal makes no difference | "it dies immediately anyway, exactly as if the pedal weren't there. Not a fade — a stop" (`phase2-listening-guide.md:243-251`) | **blocked on #16** — this is entirely a release/note-off behavior; `render_component.py` never sends note-off, so nothing about the fall time or its "hard stop" quality can be checked yet |
| 7 | No hold-pedal (CC64) behavior exists or should exist | mechanically true of the hardware — the damper is the key, no pedal input exists (§3) | **blocked on #16**, and also currently untestable for a different reason: the listening guide separately notes "no hold-pedal handling exists anywhere in the framework" (`phase2-listening-guide.md:523-524`) — true of the module today, but the guide is explicit that it "isn't clear yet whether that's a decision or an accident" at the framework level, so this instrument can't resolve it alone |

## 6. What the module would need to change — read, not measured

Read from `pianet.py` only; nothing below was rendered or listened to
this pass.

- **Velocity is fully linear amplitude, nothing else**: `amp = volume *
  value0` (`pianet.py:88`), applied identically to both `o_body` and
  `o_pluck` (`pianet.py:98-99`). Given criterion 1 above, this may
  already be closer to correct than a "normal synth" curve would be — no
  source this session or the survey's puts a hard number on how flat it
  should be, so this is flagged as *worth checking against a real
  capture*, not proposed to change on today's evidence.
- **Release is a smooth macro-controlled fade, not a hard stop.**
  `amp_r` (Amp Release macro) ranges 0.05–2.05 s (`pianet.py:118`,
  `MACRO_LABELS[8]` at `pianet.py:11`), applied as `synthio.Envelope`'s
  `release_time` (`pianet.py:90`) on the sustained `o_body` voice. The
  default patch resolves this to ≈0.4 s (patch value 22/127,
  `pianet.py:32`). Criterion 6 (blocked on #16 today) is exactly what
  this parameter needs to be checked against once a DAW-style note-off
  is available; on the sourced mechanism (§3, a pad physically re-landing
  on the reed) the hardware's true release is closer to tens of
  milliseconds than hundreds. No `_support.release_filter` sweep or
  key-off transient exists for this voice (`_support.py:216-231` defines
  the helper; `pianet.py` does not call it) — consistent with a simple
  hard stop being the right model, not a filter-swept release.
  `sustain_level = amp_s`, default 0.1 (`pianet.py:90`,
  `pianet.py:117`), which per this task's stated measurement constraint
  is unmeasurable offline today (no note-off is ever sent, so the module
  holds indefinitely regardless of what `amp_s`/`amp_r` are set to).
- **The wavetable omits the second harmonic entirely.** `WAVE_PIANET =
  make_table(((1, 1.0), (3, 0.2)), ...)` (`pianet.py:44`) — first and
  third harmonics only, no second. Per §0/§4-criterion-4, the sourced
  electrostatic-pickup mechanism's most distinctive product is a
  *prominent* second harmonic. Adding a `(2, gain)` term to `WAVE_PIANET`
  is the cheapest possible fix — a table-content change with no new
  oscillator, no toolkit dependency, and direct precedent in this
  program: `tr808`'s METAL-bank correction was exactly this class of fix,
  a wavetable whose harmonic series didn't match its own cited mechanism
  (`tr808.md` §7, items 1–2). No specific gain value is sourced for the
  second harmonic — "large" is qualitative — so any added term is a
  starting point for the A/B listen, not a measured target.
- **`WAVE_PLUCK`'s onset layer looks structurally right, unverified in
  amount.** `WAVE_PLUCK = make_table(((1,1.0),(2,0.8),(3,0.6),(4,0.4),
  (5,0.2)), ...)` through a fixed `pluck_env` (`attack=0.001s,
  decay=0.1s, release=0.05s`, `pianet.py:91`, independent of the `Decay
  Time` macro) layered under the sustained body — this is the right
  *shape* for criterion 3 (buzzy-then-clean onset): a fast-decaying,
  harmonically dense layer riding on top of a simpler sustained tone.
  Whether 0.1 s is the right decay time for that clearing is not sourced
  either way; criterion 3 above is how Station B should check it once
  rendering is available, no note-off required.
- **The lowpass ("Mellow Tone") is a single static filter set once at
  note-on**, shared by both `o_body` and `o_pluck`
  (`lp = synthio.Biquad(...)`, `pianet.py:94`, reused at `pianet.py:98-99`)
  — not modulated over the note's life. No source this session claims the
  real machine's tone changes shape over a held note beyond the
  harmonic-clearing already covered by the two-layer design (criterion
  3), so this is noted as a read fact, not a proposed change.
- **No hold-pedal (CC64) path exists anywhere in `_support.py` or
  `pianet.py`.** True of the whole family per the listening guide
  (§5, criterion 7) — happens to match this hardware exactly, but is a
  framework-level fact, not something this dossier can resolve for
  `pianet` alone.
- **The toolkit expansion is available but unused here.**
  `Instrument.__init__` accepts an `output=` parameter that defaults to
  the raw `synth` (`_support.py:287-288`); no instrument in this library
  currently routes through a downstream `audiodynamics`/`audiofilters`
  node (checked by grep across `lib/audioinstruments/*.py`: no hits for
  `Distortion(`, `Dynamics(`, or `audioroute`). If the second-harmonic
  fix above is judged insufficient by ear, a light, fixed-amount
  `audiofilters.Distortion` stage on the body voice's output is the
  toolkit-level alternative to hand-adding wavetable harmonics — flagged
  as an option, not proposed as the plan, since the cheaper wavetable
  change should be tried first.

## 7. MCU budget and macro budget

Per-voice cost is already light: 2 `synthio.Note` objects, 1 shared
`Biquad` lowpass, at most 1 shared `LFO` (vibrato, only allocated when
`vib_depth > 0.01`, `pianet.py:96`) — no wavetable larger than 2048
samples, no convolution, no `audioconvolve.FRAMES` latency to disclose.
Adding a second-harmonic term to `WAVE_PIANET` costs nothing at runtime
(table-build time only, same class of change as `tr808`'s METAL fix). **No
`" - lean"` patch is expected** on today's evidence — the real MCU-relevant
finding this pass is the polyphony-ceiling mismatch in §4, which is a
correctness question about how many keys can actually sound, not a
per-voice cost problem.

`MACRO_LABELS` carries 10 of 16 slots (`pianet.py:9-13`) — six free. **No
new macro is proposed** by anything in this dossier: the second-harmonic
fix is a fixed wavetable change, and nothing else here calls for a new
front-panel control not already covered by `Mellow Tone`/`Pluck Attack`.

## 8. What was not found, stated plainly

- No free or CC-licensed capture of any first-group (electrostatic)
  Pianet model was located this session, despite searches naming Pianet
  C/L/M/N/Combo specifically alongside "sfz," "kontakt," "freesound,"
  "multisample," and "pianobook."
  Purgatory Creek's paid Kontakt library is the only real-hardware
  capture of the correct family found, and it was not obtained.
- No DAFx/AES paper modeling the Pianet's electrostatic-pickup circuit
  specifically was found this session (not re-searched independently;
  the survey's own search of the DAFx paper-archive API for "Pianet,"
  "Hohner," "reed piano" — `accuracy-survey.md:796` — returned nothing,
  and nothing found this session contradicts that).
- Neither freeware plugin found (Artifake, Mokafix) states a license, so
  neither is usable even as a tier-3 proxy oracle without further
  license work — recorded as found, not adopted.

**Awaiting Gate A:** `APPROVE ACCURACY DOSSIER pianet`
