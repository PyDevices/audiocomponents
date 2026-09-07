# Effects Dossier — `Harmonizer` (Eventide H910 Harmonizer, ×3)

**Class:** `lib/audioeffects/pitch.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Pitch, roadmap Phase 6
**Standout:** Eventide H910 Harmonizer, proposed in vision §4.2 —
**confirmed**, and sharpened: the referent is not one H910 but the
*three-H910-from-one-keyboard* rig Eventide themselves describe (§1).
**Grade:** literature
**Portability tier:** needs audioif-own nodes (`audioroute.Splitter`)
**Status:** seed (Phase 0)

Shares the standout and most of its sources with
[`PitchShifter.md`](PitchShifter.md); that seed carries the H910's mechanism,
the splice model and the palette measurements in full, and this one does not
repeat them. What is different here is *plurality*: many fixed-interval
voices from one control.

## 1. The circuit, in one paragraph

One H910 shifts one voice by one ratio (mechanism and controls:
`PitchShifter.md` §1). What makes a *harmonizer* is the rig around it:
"The Keyboard was designed to control up to three H910s making it possible for
a vocalist to create three part harmonies live" (S2). Each unit runs its own
independent delay line, its own read pointer and therefore **its own splice**
at its own rate — three machines, three glitch periods, one keyboard note
choosing all three ratios at fixed offsets from it. The keyboard's law is the
one PitchShifter's T1 fixes: "The low C represents a PITCH RATIO of 0.5 …
middle C … 1.0 … high C … 2.0. Each other note represents a PITCH CHANGE equal
to that number of semitones away from the middle C" (S1 p. 10). Two
consequences follow from that law and matter musically. The intervals are
**fixed ratios**, not scale degrees: a voice set a major third up stays a
major third up on every note of a melody, wherever the key wants a minor
third. And the voices are **transposed, not re-synthesised**, so each carries
its own delay-line transport time and its own splice comb; the smear that
gives a harmonizer stack its thickness is those independent artefacts, not a
chorus. Key-aware harmony is a later machine's trick — the H3000 of 1987 was
marketed as an "intelligent pitch-changer that could generate stereo harmonies
in a user-specified key" (S5) — and it is out of this class's reach for a
reason the library already states: `pitch.py:3-4` records that pitch
correction "is deliberately absent: it needs pitch detection, which the DSP
palette does not provide." That is why the H910, not the H3000, is the right
referent for a `Harmonizer` on this palette (§8.1).

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Eventide, *Model H910 Harmonizer* manual, Part #141252 Rev A … (App. S1) | The keyboard's C-to-C semitone law; the ratio table … (App. S1) | Bare copyright notice "© 2015 Eventide Inc." … (App. S1) | https://media.uaudio.com/support/manuals/dd/Eventide%20H910%20Harmonizer%20Manual.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 11 pages, `pypdf`); the keyboard law on p. 10 and the ratio table on p. 7 re-read verbatim |
| S2 Eventide, "Flashback #4.2: H910 Harmonizer® The Product" | "The Keyboard was designed to control up to three … (App. S2) | "Copyright © 2026 Eventide Inc. All Rights … (App. S2) | https://www.eventideaudio.com/blog/50th-flashback-4-2-h910-harmonizer-the-product/ | 2026-09-06; re-fetched in the audit — the three-H910 keyboard sentence and the licence line confirmed verbatim |
| S3 J. Dattorro, "Effect Design, Part 2", *JAES* 45(10), 1997 | The splice's necessity … (App. S3) | No rights statement anywhere in the file (the … (App. S3) | https://ccrma.stanford.edu/~dattorro/EffectDesignPart2.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 25 pages, `pypdf`); the detune passage re-read verbatim, including "The primary distinguishing feature of the two is that the pitch is necessarily undulating in the chorus effect" |
| S5 Premier Guitar, "The Eventide H3000: Break Out of the (Stomp) Box" | The H3000 (1987) as an "intelligent pitch-changer that … (App. S5) | No licence statement found … (App. S5) | https://www.premierguitar.com/eventide-h3000 | 2026-09-06; re-fetched in the audit — the "intelligent pitch-changer" sentence, the 1987 date and patch 217 all confirmed |

**Not reached, and therefore not cited:** Reverb's "The Tech Behind the
Eventide H3000" (403); ValhallaDSP's H910 article (403 twice). Whether the
H3000's diatonic mode *detects* the input's pitch or only maps a specified key
is **unsourced** here — S5 says only "user-specified key" — so no claim about
its detection mechanism appears in the trait table. Nothing was read for code
(vision §5).

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| H1 | Every enabled voice is present **simultaneously and independently**: a steady sine produces a line at 2^(n_k/12)·f_in for each voice *k*, each within 1 % of ratio **after the `PitchShifter.md` T4 correction is applied per voice**, with the dry line unchanged | S2 (three units, three voices); S1 p. 10; **the 1 % and 0.1 dB windows are this seed's** | high | A voice missing; voices that alternate rather than sum; a dry line moved or attenuated by adding a voice | 65 536-pt Hann STFT of 440 Hz with voices at +4, +7, +12; each corrected line within 1 % of ratio and the dry line within 0.1 dB of its solo level. The correction is not optional here: each voice's *raw* dominant line is displaced by up to f_splice/2 = f_s·\|r_k−1\|/2W, which at the default 1024-frame window is 6.1 Hz at +4 against a 1 % window of 5.5 Hz, and 23.4 Hz at +12 against 8.8 Hz — so an uncorrected measurement fails this trait on a correct build. **Planted fault:** hold one voice's Mixer level at zero while its node still runs — that line must vanish and the check go red |
| H2 | The voices' splices are **mutually incoherent**: each voice's sideband comb has its own spacing f_s·\|r_k − 1\|/W, so with distinct intervals no two voices share a comb spacing, and the composite has no single modulation rate | `PitchShifter.md` T3 applied per voice; S2 (independent units); **the one-bin tolerance is this seed's**, set by the analyser | high | One comb spacing across all voices (a shared read pointer); voices whose combs lock together as the intervals change | Peak-list of the same STFT: the sideband spacing measured around each voice's line must equal its own f_s·\|r_k−1\|/W to within **one FFT bin** (0.73 Hz at 65 536 points, 48 kHz), and no two of the three spacings may agree to within that bin — at +4/+7/+12 and W = 1024 frames the three are 12.2, 23.4 and 46.9 Hz, sixteen bins apart at the closest. **Planted fault:** drive two voices from one shared line — the spacings must collapse to one and the check go red |
| H3 | Intervals are **fixed in cents, not corrected to a key**: a voice at +4 semitones sits 400 cents above the input at *every* input pitch across C2–C6, constant within the larger of **5 cents** and the cents equivalent of 0.25 Hz at the measured line (5.2 cents at C2's +4 line, 0.3 cents at C6's) | S1 p. 10 (the keyboard's law is semitones … (App. H3) | high | An interval that changes with input pitch; any snapping to a scale; a drift that grows with the note, which would mean the correction rather than the class | Chromatic sweep of the input … (App. H3) |
| H4 | One master control moves **all** voices in parallel, preserving the interval structure — the HK941's one keyboard driving three units (S2). Moving `Pitch` by +2 semitones moves every voice's output by 200 ± 10 cents **after the T4 correction** and leaves every voice-to-voice interval unchanged within the same window | S2; S1 p. 10; **the ±10 cent window is this … (App. H4) | high | Voices that move by different amounts; intervals that change when the master moves; a master that moves only the dry | Two-point measurement of H3's … (App. H4) |
| H5 | The stack is a **detune-family thickening, not a chorus**: with all voices at unison-plus-cents offsets the composite has no undulating pitch — each voice's instantaneous pitch is constant between splices | S3 ("When fixed microtonal pitch shift is … (App. H5) | medium — the … (App. H5) | A periodic pitch modulation in any single voice at any LFO-like rate; a voice whose instantaneous frequency traces a sinusoid | Instantaneous-frequency track … (App. H5) |

Characters: none.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

```
source ─ audioroute.Splitter(taps = 1 + N) ┬─ tap 0 ─────────────────► Mixer.voice[0]      dry
                                           ├─ tap 1 ─ PitchShift(r₁) ► Mixer.voice[1]
                                           ├─ tap 2 ─ PitchShift(r₂) ► Mixer.voice[2]
                                           └─ tap 3 ─ PitchShift(r₃) ► Mixer.voice[3]
```

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None.** Every Tier 2 trait is measurable on the existing palette, and the
one thing a harmonizer's user really wants that this palette cannot give —
harmony corrected to a key — is blocked by pitch detection, not by a node.
A pitch detector is a different kind of component from the ones this program
adds (it is analysis, not a DSP node in the graph), the 46 names are frozen,
and `pitch.py:3-4` already records the absence as deliberate. It is therefore
recorded here as **out of scope for this program**, with the reasoning, rather
than raised as an ask that would be refused. See §8.1.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Pitch` | BIPOLAR | −12 … +12 semitones | the master keyboard note (S2) — moves every voice together (H4) |
| 1 | `Voice 1` | BIPOLAR | −24 … +24 semitones | unit 1's MANUAL/keyboard offset |
| 2 | `Voice 2` | BIPOLAR | −24 … +24 semitones | unit 2's offset |
| 3 | `Voice 3` | BIPOLAR | −24 … +24 semitones | unit 3's offset |
| 4 | `Level 1` | UNIPOLAR | −∞ … 0 dB | unit 1's MAIN slider; 0 removes the voice and its cost |
| 5 | `Level 2` | UNIPOLAR | −∞ … 0 dB | unit 2's |
| 6 | `Level 3` | UNIPOLAR | −∞ … 0 dB | unit 3's |
| 7 | `Dry` | UNIPOLAR | −∞ … 0 dB | the desk's dry return |
| 8 | `Detune` | BIPOLAR | −50 … +50 cents | spread applied ±across the voices; the "detune" of S3 |
| 9 | `Window` | UNIPOLAR | 5 … 60 ms | shared line length; trades splice rate against wet delay |

Characters: none. **Feedback is deliberately absent** — the H910 has one, but
a harmonizer with feedback is a rising shimmer, and `ShimmerHall` is already a
name in the frozen 46. Patches: 0 *Third and fifth above* (constructor
defaults) · 1 *Octave below, doubled* · 2 *Two voices, wide detune* ·
3 *Fifths, thin* · 4 *Octave up and down* · 5 *Three-part stack* ·
6 *Two voices — lean* · 7 *Unison thickener*.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/pitch.py`.

- `pitch.py:42` — `MACRO_LABELS = ()`. Nothing on the class is reachable from
  a host, including the intervals, which are constructor-only.
- `pitch.py:47` — `intervals = tuple(intervals)[:_core.SPLITTER_TAPS - 1]` …  *(argument in full: App. R)*
- `pitch.py:46` — one `level` for every voice. A harmonizer whose voices
  cannot be balanced against each other is not a harmonizer.
- `pitch.py:56` — `window=2048` fixed **in bytes**, so the window is 512 …  *(argument in full: App. R)*
- `pitch.py:56` — every voice gets the same window, so at different intervals …  *(argument in full: App. R)*
- `pitch.py:35` — the docstring says "up to three fixed-interval shifted …  *(argument in full: App. R)*
- `_core.py:140-141` — `LATENCY_SAMPLES = 0` / `TAIL_SAMPLES = None`
  inherited, so three delay lines report no latency and no tail.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Diatonic harmony.** The thing a musician means by "harmonizer" after 1987
   is key-aware, and this class cannot be that (S5; `pitch.py:3-4`). The
   docstring and the README catalogue row must say so in one line, in the
   user's words, rather than leaving it to be discovered. Whether a pitch
   detector is a separate future component is **not** this program's question;
   the recommendation is to state the limit and stop. *(Phase 6 for the
   wording; the component question is outside the 46.)*
2. **Detune spread law.** §6's `Detune` macro spreads voices ±across the
   stack; whether the spread should be symmetric, or weighted so the highest
   voice detunes most (as a real three-singer stack drifts), is unsourced.
   *(Phase 6, from H5's instantaneous-frequency measurement.)*
3. **Voice count and the lean patch.** Tier 3 proposes three voices with a
   two-voice lean patch; the split between them is a cost measurement on the
   S3, not a judgement. *(Phase 6, device-runner.)*


## Appendix

### A1 — what the palette measurements here inherit

Every node-level measurement this seed relies on was taken for
`PitchShifter.md` on 2026-09-06 with `audiocomponents/.venv/bin/python` at
48 kHz, and is not repeated: A1 (wet minimum delay = the crossfade), A2 (the
splice comb and the dominant line's displacement, five window lengths), A3
(the tail reaches exact zero), A4 (`mix = 0` is not a wire inside the node),
A5 (the composed `Splitter → Mixer` dry path is byte-identical), A6 (the
Splitter's ring drops sparse probes longer than 8192 frames).

### A2 — the current class, rendered

`Harmonizer()` with its constructor defaults (intervals 4.0 and 7.0, level
0.5), fed a single full-scale click at frame 64 of an 8000-frame source,
stereo, 48 kHz:

```
L: (64, 20000)  (77, 4062)  (407, 10000)  (484, 10000)
```

The dry click arrives at frame 64 at full scale — the dry path is already
outside the shifters, which is the one thing the current class gets right.
The two transposed copies arrive at frames 407 and 484, i.e. **7.1 and 8.8 ms
after the dry**, at exactly half scale (the shared `level` of `pitch.py:46`);
their different arrival times are the two lines' independent read pointers,
which is H2 showing itself on a single click. The 4062 at frame 77, 13 frames
after the dry, is consistent with a crossfade region blending the overlap
buffer while it still holds the click — a 0.67 ms linear crossfade on a
10.7 ms window (`pitch.py:56`, the node's 128-byte `overlap` default). That
reading is an interpretation of one click, not a measurement of the crossfade;
the class gate measures the splice properly with H2's STFT.

### A3 — Mixer voices sum without normalisation

Two Mixer voices, both level 1.0, both playing the same 10 000-peak sine:
output peak **20 000**. There is no auto-gain to hide behind, which is why §4
puts the gain structure in the class and the default patch under full scale.

### A4 — the three-voice topology, built and rendered

Palette verifier, 2026-09-06, `audiocomponents/.venv/bin/python`, 48 kHz
stereo, 8192 frames of a 440 Hz sine at 9000 peak.
`audioroute.Splitter(taps=4)`; tap 0 → `Mixer.voice[0]` at level 1.0; taps
1–3 → `audiodelays.PitchShift(semitones = 4, 7, 12; mix=1, window=4096,
overlap=128)` → voices 1–3 at level 0.5. Output peak 22365, and a Goertzel
over the settled tail finds the dry line at **8750** (its solo level) with
energy at all three transposed voices present at once — so the four taps
carry four independent voices and the dry is not disturbed by adding them.

The transposed lines read **1923 / 1075 / 531** at their *nominal*
frequencies rather than at the 4500 their voice levels imply, and that is the
expected result, not a defect: the splice spreads each voice into the comb
`PitchShifter.md` T3 fixes, and its dominant line sits off the nominal by the
T4 displacement. It is the concrete reason H1's per-voice T4 correction is
marked "not optional" — a naive level check at the nominal frequency would
report every voice 7–19 dB light on a correct build.

### App. I — Tier 1 invariants, the standard block

Verbatim from vision §3, moved out of §3 under the length rule. It is the
same block in every seed; a class-specific note on it is kept with it here.

- [ ] Silence in gives silence out; a decaying tail reaches exact zero — no
      held DC (the audioif#23 class of defect).
- [ ] `mix` at zero, or drive at zero, is a wire (byte-identical to source).
- [ ] Level-honest: unity through the dry path, no hidden gain.
- [ ] Reported `latency_samples` / `tail_samples` match what is measured —
      latency by a click against the dry path at 48 kHz and 44.1 kHz, tail
      by the burst-then-silence probe.
- [ ] `reset()` leaves every node the class built silent and stateless and
      the borrowed source untouched (planted faults: a delay line left full;
      an upstream instrument reset through a Filter- or Phaser-tailed chain).
- [ ] `deinit()` deinitialises every node the class built and leaves the
      source rendering (planted fault: an intermediate node left live).
- [ ] `capabilities` names exactly the optional behaviours the class honours
      (`"tempo_sync"` declared if and only if the transport is read).
- [ ] Pulling `output` allocates nothing.
- [ ] CPython and desktop MicroPython render identical bytes on the probe
      material, or the cause is recorded here; the P4 and S3 digests match
      the desktop's or carry a recorded cause (float width is the expected
      one, never the class).
- [ ] Rate-honest: designed and stated at 48 kHz; every invariant also holds
      at 44.1 kHz and 22.05 kHz; Hz-valued spans and options clamp below
      Nyquist at the running rate, never refuse; any Tier 2 trait that cannot
      hold at a lower rate is named here with why.
- [ ] Every invariant also holds at `channel_count` 1; a stereo-by-definition
      class states in §4 what a mono source gets (a wire, or the mono sum of
      its stereo behaviour), and the kit measures that statement.

The wire invariant is reachable only with the dry routed outside the shifter
nodes; the measurement that shows why is `PitchShifter.md` A4/A5 and it
applies here unchanged.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Eventide, *Model H910 Harmonizer* manual, Part #141252 Rev A — **the manual for Eventide's H910 *plug-in*** (UA-hosted), which states the modelled front panel's "controls have the same range and characteristics as the front panel controls of the hardware" (p. 3); the HK941 keyboard section it describes is the plug-in's rendering of a feature "originally available through external connections or options" (p. 4) | The keyboard's C-to-C semitone law; the ratio table; per-unit controls | Bare copyright notice "© 2015 Eventide Inc." (p. 11) with no rights or licence statement — treated as all rights reserved; read as a document | https://media.uaudio.com/support/manuals/dd/Eventide%20H910%20Harmonizer%20Manual.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 11 pages, `pypdf`); the keyboard law on p. 10 and the ratio table on p. 7 re-read verbatim |
| S2 Eventide, "Flashback #4.2: H910 Harmonizer® The Product" | "The Keyboard was designed to control up to three H910s making it possible for a vocalist to create three part harmonies live"; the splice crossfade | "Copyright © 2026 Eventide Inc. All Rights Reserved." | https://www.eventideaudio.com/blog/50th-flashback-4-2-h910-harmonizer-the-product/ | 2026-09-06; re-fetched in the audit — the three-H910 keyboard sentence and the licence line confirmed verbatim |
| S3 J. Dattorro, "Effect Design, Part 2", *JAES* 45(10), 1997 | The splice's necessity; "When fixed microtonal pitch shift is mixed with the original signal, we get the **detune** effect … subjectively 'fattening' the sound", and that detune is *not* chorus because chorus's pitch necessarily undulates | No rights statement anywhere in the file (the author's own CCRMA copy of a JAES 1997 paper) — **licence unverified, treated as copyleft**: read as a paper, nothing ported | https://ccrma.stanford.edu/~dattorro/EffectDesignPart2.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 25 pages, `pypdf`); the detune passage re-read verbatim, including "The primary distinguishing feature of the two is that the pitch is necessarily undulating in the chorus effect" |
| S5 Premier Guitar, "The Eventide H3000: Break Out of the (Stomp) Box" | The H3000 (1987) as an "intelligent pitch-changer that could generate stereo harmonies in a user-specified key"; the H3000's own patch 217 "DUAL H910s" preserving the older glitch | No licence statement found; footer carries only an affiliate-link notice ("Premier Guitar features affiliate links to help support our content"). Read as a document | https://www.premierguitar.com/eventide-h3000 | 2026-09-06; re-fetched in the audit — the "intelligent pitch-changer" sentence, the 1987 date and patch 217 all confirmed |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| H3 | Intervals are **fixed in cents, not corrected to a key**: a voice at +4 semitones sits 400 cents above the input at *every* input pitch across C2–C6, constant within the larger of **5 cents** and the cents equivalent of 0.25 Hz at the measured line (5.2 cents at C2's +4 line, 0.3 cents at C6's) | S1 p. 10 (the keyboard's law is semitones from middle C, with nothing about key); S5 (key awareness is the H3000's, not the H910's); **the tolerance is this seed's**, floored by the T4 model's own 0.2 Hz residual (`PitchShifter.md` A2) | high | An interval that changes with input pitch; any snapping to a scale; a drift that grows with the note, which would mean the correction rather than the class | Chromatic sweep of the input, C2–C6, one voice at +4; interval in cents, T4-corrected per `PitchShifter.md`, from a frequency estimate **finer than the tolerance** — parabolic interpolation on a 65 536-pt Hann STFT, whose raw 0.73 Hz bin is 15.3 cents at C2's +4 line and cannot resolve 5 cents on its own. **Planted fault:** snap the requested ratio to the nearest note of a C-major scale; the sweep must go red at every non-diatonic input |
| H4 | One master control moves **all** voices in parallel, preserving the interval structure — the HK941's one keyboard driving three units (S2). Moving `Pitch` by +2 semitones moves every voice's output by 200 ± 10 cents **after the T4 correction** and leaves every voice-to-voice interval unchanged within the same window | S2; S1 p. 10; **the ±10 cent window is this seed's** | high | Voices that move by different amounts; intervals that change when the master moves; a master that moves only the dry | Two-point measurement of H3's sweep at master 0 and master +2; per-voice shift and pairwise intervals, T4-corrected. Uncorrected the splice displacement alone is ±27 cents at the +6 line (f_splice = 19.4 Hz at the default window) — wider than the whole window, so the raw line cannot be the measurement |
| H5 | The stack is a **detune-family thickening, not a chorus**: with all voices at unison-plus-cents offsets the composite has no undulating pitch — each voice's instantaneous pitch is constant between splices | S3 ("When fixed microtonal pitch shift is mixed with the original signal, we get the detune effect"; chorus's pitch "is necessarily undulating"); **the 2 cent window and the 1 Hz probe rate are this seed's** | medium — the distinction is Dattorro's, the numbers are ours | A periodic pitch modulation in any single voice at any LFO-like rate; a voice whose instantaneous frequency traces a sinusoid | Instantaneous-frequency track (analytic-signal phase derivative) of one voice at +10 cents: flat within 2 cents between splice events, with steps only at the splice. **Planted fault:** drive that voice's `semitones` from a 1 Hz ±5 cent LFO — the track must show the sinusoid and the check go red, which is what separates this measurement from one that would pass on any steady signal |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Audit, 2026-09-06 (licence and citation pass).** Every row above was
re-fetched from this machine in the audit run and every quotation re-read at
source; both unreachable pages were re-tested and are still unreachable
(reverb.com HTTP 403, valhalladsp.com HTTP 403). Two corrections were applied,
the same two as in [`PitchShifter.md`](PitchShifter.md): S1 is the *plug-in*
manual rather than a hardware manual, and its licence cell now records what
the file carries; S3's licence is downgraded to *unverified — treated as
copyleft*. `pitch.py:3-4` was re-read in the tree and quotes correctly.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline, at the default
three voices: ESP32-P4 **0.12**, ESP32-S3 **0.30**. Lean patch expected:
**yes** — `" - lean"` runs two voices with a shorter window, because the cost
is linear in voice count and the S3 has to carry the rest of a chain. RAM at
three voices and the 21.3 ms default window: ~12.6 kB of line, plus the
Splitter's fixed 32 kB ring (`audioif_splitter.h:20`).

*(from §3)*

Latency (vision §9a). **Dry path: zero samples**, so `latency_samples` = 0.
Each wet voice carries the H910's transport delay, documented per
`PitchShifter.md` Tier 3 — minimum the crossfade (1.33 ms default), maximum
the window (21.3 ms default) — and the voices' delays are independent, so the
stack has no single arrival time and the docstring says so. `window_ms`
(5–60 ms) is shared by all voices and is the only latency-affecting option;
it defaults to the shortest that keeps the splice comb out of the middle of
the band. No lookahead.

*(from §4)*

N = 3 is the ceiling, and the two reasons for it agree: the Splitter fans out
to four taps (`AUDIOIF_SPLITTER_MAX_TAPS 4`, `audioif_splitter.h:21`), and the
standout's own ceiling is three units from one keyboard (S2). That agreement
is a coincidence, not a design, and is recorded as one so nobody later reads
the palette limit as musical. If a fourth voice is ever wanted, a `SplitterTap`
is itself a source and a second Splitter can hang off one — available, not
needed, and not in the proposed surface.

*(from §4)*

Each voice is exactly `PitchShifter`'s wet path: `audiodelays.PitchShift` with
its own `semitones` and the node's own `mix` pinned at 1, the dry carried
outside on tap 0 because the node is not a wire at mix 0
(`audioif_pitchshift.c:42` → `audioif_synth_dsp.c:20-27`; measured,
`PitchShifter.md` A4). Voice gains are Mixer voice levels, which are exact:
one voice at level 1.0 with others at 0.0 is byte-identical to the source
(`PitchShifter.md` A5). Mixer voices sum without normalisation — two copies of
a 10 000-peak sine give 20 000, measured — so the class states its own gain
structure rather than relying on the mixer to protect it, and the default
patch keeps dry + three voices under full scale.

*(from §4)*

Python computes only at construction (window/crossfade frames, byte sizes) and
on a macro move (`node.semitones` per voice, Mixer levels). No table, nothing
per sample, nothing float-width sensitive. **Mono** needs no special
behaviour: every voice is sized in frames from milliseconds, so a mono source
gets the same intervals and traits at half the *line* RAM — the Splitter's
ring does not halve with it, being declared stereo whatever the source is
(`int16_t ring[8192 * 2]`, `audioif_splitter.h:29`; a mono frame is
duplicated into both lanes on write, `audioif_splitter.c:30-31`), so Tier 3's
32 kB stands at either channel count. `capabilities` = `()`
(D10): nothing here reads a transport.

*(from §4)*

**Palette verification, 2026-09-06 (pitch-stereo unit).** Re-read and
re-measured on this machine: the four-tap ceiling
(`AUDIOIF_SPLITTER_MAX_TAPS 4`, `audioif_splitter.h:21`; the binding raises
"taps must be 1..4" at `audioroute/Splitter.c:43-44`); a `SplitterTap` is
itself an audiosample and can source a second Splitter
(`audioroute/SplitterTap.c:63-64`); the node's `mix = 1` is fully wet, since
the binding scales it ×2 before the kernel (`PitchShift.c:217`,
`audioif_pitchshift.c:39-41`); the mix-0 non-wire and the composed wire
(`PitchShifter.md` A4, A5, both re-measured); and Mixer summation without
normalisation (A3 here, re-measured: peak **20000** from two 10 000-peak
voices, and **10000** when one live node is handed to two voices instead of
two Splitter taps — which is the "one consumer per node" fact this topology
and `Octaver`'s Splitter B both rest on).

*(from §5)*

*Palette-verifier judgement, 2026-09-06: no ask stands here to refute, and
the "none" was checked the other way round. §4's topology —
`Splitter(taps=4)` → dry on tap 0 and three `PitchShift` voices at +4, +7 and
+12 on taps 1–3, all four into one `Mixer` — was built and rendered on the
CPython build of audioif at 48 kHz: 8192 frames out, all four voices sounding
at once, dry line intact at its solo level. See A4.*

*(from §7)*

- `pitch.py:47` — `intervals = tuple(intervals)[:_core.SPLITTER_TAPS - 1]`
  **silently drops** a fourth interval. One class over, `Octaver` raises for
  the same overflow (`pitch.py:92-96`); two classes in one file disagree about
  whether asking for too much is an error. The rebuild raises.

*(from §7)*

- `pitch.py:56` — `window=2048` fixed **in bytes**, so the window is 512
  frames on a stereo source and 1024 on a mono one; the effect's splice rate
  changes with the source's channel count.

*(from §7)*

- `pitch.py:56` — every voice gets the same window, so at different intervals
  their splice rates differ only through the ratio. That is right by accident
  (H2 holds) and should be right on purpose.

*(from §7)*

- `pitch.py:35` — the docstring says "up to three fixed-interval shifted
  copies", which is correct, but the class never says *why* three, and the
  Splitter limit is a mirror constant (`_core.py:61`) rather than a stated
  design ceiling.
