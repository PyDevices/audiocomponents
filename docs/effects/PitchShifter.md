# Effects Dossier — `PitchShifter` (Eventide H910 Harmonizer)

**Class:** `lib/audioeffects/pitch.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Pitch, roadmap Phase 6
**Standout:** Eventide H910 Harmonizer, proposed in vision §4.2 —
**confirmed**; the evidence is in §2 and the appendix. *(The seed's bare
date "(1975)" is dropped — audit correction, §2.)*
**Grade:** literature
**Portability tier:** needs audioif-own nodes (`audioroute.Splitter`)
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

No H910 schematic or service manual is public (§2), and the pitch change is
not a circuit trick in any case — "the processing [was] almost entirely
analog … Only delay was digital" (S1 p. 3) — it is what happens when a RAM
line is **written at one rate and read at another** (S2). A read pointer
moving at the ratio *r* drifts through the line and must be jumped back at an
end; the H910 crossfades that jump with "a pair of offset delays, fading one
in and the other out at the splice point" (S2), and the
discontinuity survives on purpose — "the glitch is back!" (S1 p. 3). The line
is short: pitch change is "a delay that is continuously varying over an
approximate **30 mS** range", so "even without both ADD'L DELAY buttons
pressed there will still be an audible delay" (S1 p. 6). Four panel controls
sit around it. **MANUAL** sets the ratio: centre = unity, full clockwise = 2,
full counter-clockwise = 0.5, "band-spread" around unity so small adjustments
are easier (S1 p. 8) — a law nearer linear in semitones than in ratio.
**ADD'L DELAY** switches 7.5 + 15 + 30 + 60 ms, summing to 112.5 ms in
delay-only mode and 60 ms alongside pitch change (S1 p. 6). **FEEDBACK**
"attenuates the signal coming from the main output and reapplies it to the
input" — after the shifter, so every repeat is transposed again — until the
gain exceeds unity and the system oscillates (S1 p. 6). **MIX** blends dry
against wet (S1 p. 9 — MIX/MAIN/OUT 2 and the envelope-follower times below
sit in the manual's *Additional Controls* section, the plug-in's rendering of
features "originally available through external connections or options"
(S1 p. 4), not on the hardware's own front panel; audit note, §2). Two more pitch
sources: the HK941 keyboard, low C = 0.5, middle C = 1.0, high C = 2.0, every
other note that many semitones from middle C, with a GLIDE slider for
portamento (S1 p. 10); and an envelope follower (attack 1–100 ms, release
10 ms–1 s) sweeping the ratio from 1.0 at silence to the MANUAL setting at
full scale (S1 pp. 8, 10). ANTI-FEEDBACK is a
different animal — "a small up and down frequency shift", not a ratio (S1
p. 9). Nothing is stable: the master clock was "a tuned LC oscillator",
drifting "slightly, slowly and unpredictably" (S1 p. 3). Dattorro states the
same mechanism as maths and names the splice as its unavoidable consequence
(S3, quoted in A0).

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Eventide, *Model H910 Harmonizer* manual, Part #141252 Rev A … (App. S1) | Every panel control's range and law … (App. S1) | Bare copyright notice "© 2015 Eventide Inc." … (App. S1) | https://media.uaudio.com/support/manuals/dd/Eventide%20H910%20Harmonizer%20Manual.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 11 pages, `pypdf`); every quotation and page number above re-checked against the extracted text |
| S2 Eventide, "Flashback #4.2: H910 Harmonizer® The Product" | Read-rate-vs-write-rate account … (App. S2) | "Copyright © 2026 Eventide Inc. All Rights … (App. S2) | https://www.eventideaudio.com/blog/50th-flashback-4-2-h910-harmonizer-the-product/ | 2026-09-06; re-fetched in the audit, quotations and licence line confirmed verbatim |
| S3 J. Dattorro, "Effect Design, Part 2", *JAES* 45(10), 1997 | Constant-pitch read-index law … (App. S3) | No rights statement anywhere in the file (the … (App. S3) | https://ccrma.stanford.edu/~dattorro/EffectDesignPart2.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 25 pages, `pypdf`); the read-index law, the autocorrelator/raised-cosine splice, the 60 ms figure and the interpolator quotations in A0 all re-checked verbatim |
| S4 Eventide, "H910 Harmonizer" product page | "up to 112.5 msec of delay"; "two-octave range" | "Copyright © 2026 Eventide Inc. All Rights … (App. S4) | https://www.eventideaudio.com/rackmount/h910-harmonizer/ | 2026-09-06; re-fetched in the audit, both figures and the licence line confirmed verbatim |

**Not reached, and therefore not cited:** ValhallaDSP's H910 article
(valhalladsp.com, HTTP 403 twice) — a search snippet calling the H910 "a
2-tap pitch shifter … triangle wave crossfading" was seen, never verified at
source, and is used for nothing; Reverb's H3000 article (403). No H910
schematic or service manual was found anywhere, which is why the grade is
*literature*. Nothing here was read for code (vision §5).

**Audit, 2026-09-06 (licence and citation pass).** Every row above was
re-fetched from this machine in the audit run and every quotation and page
number re-read at source; the two unreachable pages were re-tested and are
still unreachable (valhalladsp.com HTTP 403, reverb.com HTTP 403). Three
corrections were applied, none of which moves a trait:

1. **S1 is the manual for Eventide's H910 *plug-in***, not a hardware manual. …  *(argument in full: App. R)*
2. **S3's licence is downgraded** to *unverified — treated as copyleft*,
   which changes nothing in practice: it was only ever read as a paper.
3. **The date "(1975)" had no source** and is dropped. S2 says only "By 1975, …  *(argument in full: App. R)*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | The ratio span is exactly one octave each way (macro ends give r = 0.500 and 2.000) and an integer-semitone setting *n* gives r = 2^(n/12) within 1 % of ratio, matching the H910's own table (+7 → 1.4983, −7 → 0.6674) | S1 pp. 7-8 | high | An end stop away from 0.5/2.0; a table that is not 2^(n/12); a law linear in ratio rather than band-spread | Wet/input dominant-partial ratio … (App. T1) |
| T2 | The wet path is a **continuously varying** delay whose swing equals the stated window (order 30 ms) and whose minimum is the crossfade, not zero — a click's wet arrival moves repeat to repeat at r ≠ 1, and at r = 1 it is fixed and non-zero | S1 p. 6; S2 | high | A constant wet delay at r ≠ 1; zero wet delay at r = 1; a swing over 5 % from the reported window | Click train (20 ms) fully wet at … (App. T2) |
| T3 | The splice is periodic at f_splice = f_s·\|r − 1\| / W_frames, so a steady sine fully wet shows a **comb of sidebands at that spacing**, not one line: consecutive peaks in the 0–6 kHz peak list are spaced f_splice to within **one FFT bin** (0.73 Hz at 65 536 points, 48 kHz) at every window length | S3; S1 p. 3 for the mechanism; **the one-bin tolerance is this seed's**, set by the analyser and not by the circuit | high | No sidebands; a spacing more than one bin off f_s·\|r−1\|/W; sidebands persisting at r = 1 | 65 536-pt Hann STFT, 440 Hz, r = 2, W ∈ {512, 1024, 2048} frames; spacing off the peak list (A2). **Planted fault:** pin the kernel's `read_rate` to 1×2⁸ (`audioif_pitchshift.c:51`) so r is unity inside the node while the class still reports r = 2 — the comb must vanish and the check go red |
| T4 | The splice is unsynchronised to the input, so the **dominant** comb line sits at r·f_in − Δ, Δ = −wrap(f_in·W/f_s)·f_s/W, \|Δ\| ≤ f_splice/2 — transposition error in cents ≤ 600·f_splice/(r·f_in), shrinking as W grows. The class states its worst case at 110 Hz | derived from S3's read-index law; matched to 0.2 Hz at five window lengths (A2) | medium — the model is ours, the measurement is five for five | A dominant line at r·f_in for every W; error above f_splice/2; error not shrinking with W | Dominant line vs W at r = 2, 440 Hz, against predicted Δ. **Planted fault:** force the splice period to a whole number of input periods; the error must fall to zero |
| T5 | Feedback is taken **after** the shifter, so the n-th repeat is transposed n times (r^n·f_in) and the loop self-oscillates above unity gain | S1 p. 6; **the ±30 cent window is this … (App. T5) | high | Repeats at constant pitch (feedback tapped pre-shift); a loop that cannot oscillate | Click, r = 2^(7/12) … (App. T5) |
| T6 | The dry path never enters the line: at any mix the dry arrives at sample zero, and mix = 0 is byte-identical | S1 p. 9 | high | A dry component arriving late; any change at mix = 0 | Click at mix 0.5 → two events … (App. T6) |

Characters: none. The H910 is one machine with one algorithm.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

`audiodelays.PitchShift` **already is** the H910's algorithm. Its kernel
writes at a cursor advancing one frame per frame and reads at
`read_index >> 8`, where `read_index` advances by `2^(semitones/12)·256`
(`audioif_pitchshift.c:26`, `:51`; `audiodelays/PitchShift.c:106`) and wraps
at `window_samples << 8` (`:52-53`) — Dattorro's linear read index exactly.
Within `overlap_samples` of the write cursor it crossfades linearly between
the old line content and the newest samples (`audioif_pitchshift.c:27-38`) —
Eventide's pair of offset delays. Two things it does not do, recorded rather
than fixed (a ported node never changes, vision §2.2): the read is
**truncated, not interpolated** (`:26`) where S3 §4.5 treats linear
interpolation as the minimum for a swept read; and the crossfade is
**linear** where S3's splicer uses two quadrants of a raised cosine. Neither
blocks a Tier 2 trait (§5).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None.** Every Tier 2 trait is reachable on the existing palette, and the one
Tier 1 invariant the ported node cannot hold — the wire at mix 0 — is reachable
by composition, measured in §4. Recorded for the survey's node list as a
**refuted candidate**: an audioif-own shifter with an interpolated read and a
raised-cosine crossfade. It would lower T3/T4's artefact floor, but T1–T6 are
statements about *what* the splice does and the ported node does them, so no
fixed trait is shown unreachable. The ask re-opens only if Phase 6 measures
the truncated read's noise above what the evidence pack can call clean — not
on taste.

*Palette-verifier judgement, 2026-09-06: no ask stands here to refute. The
"no ask" itself was checked the other way round — the composition §4 proposes
was built and rendered, and it does hold the wire the ported node breaks (A5,
re-measured). Confirmed.*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Pitch` | BIPOLAR | −12 … +12 semitones | MANUAL; linear in semitones *is* the "band-spread around unity" of S1 p. 8 |
| 1 | `Fine` | BIPOLAR | −50 … +50 cents | the ratio table's quarter-tone columns (S1 p. 7) |
| 2 | `Mix` | UNIPOLAR | 0 … 1 | MIX slider |
| 3 | `Delay` | UNIPOLAR | 0 … 112.5 ms | ADD'L DELAY switch group, as one knob |
| 4 | `Feedback` | UNIPOLAR | 0 … 0.95 | FEEDBACK, stopping short of the oscillation S1 describes |
| 5 | `Window` | UNIPOLAR | 5 … 60 ms | no panel control; exposes the fixed ~30 ms line (S1 p. 6) and S3's 60 ms |
| 6 | `Glide` | UNIPOLAR | 0 … 1000 ms | GLIDE slider (S1 p. 10) |
| 7 | `Level` | UNIPOLAR | −24 … +6 dB | MAIN slider |

Characters: none. Patches (names describe settings, never products):
0 *Unity, wet only* (constructor defaults) · 1 *Octave up* · 2 *Octave down* ·
3 *Fifth above, half wet* · 4 *Slight detune, doubled* · 5 *Long window for
chords* · 6 *Short window, splice showing* · 7 *Rising stack — fifth with
feedback* · 8 *Glide to the octave*.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/pitch.py`.

- `pitch.py:22` — `MACRO_LABELS = ()`. The class offers a host nothing; its …  *(argument in full: App. R)*
- `pitch.py:27` — `mix` is handed to the node, so mix = 0 is not a wire (A4).
- `pitch.py:27` — `window=2048` is a fixed literal **in bytes**. Stereo that …  *(argument in full: App. R)*
- `pitch.py:27` — `overlap` is left at the node's 128-byte default: a 0.67 ms
  linear crossfade, 6 % of a 10.7 ms cycle.
- `pitch.py:25` — no feedback, no delay, no glide; three of the H910's four
  panel controls are absent.
- `_core.py:140-141` — `LATENCY_SAMPLES = 0` and `TAIL_SAMPLES = None` …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Default window.** 21.3 ms comes from T3/T4 arithmetic, not from a
   measurement across the class's real range. The implementation session fixes
   it from the T4 error table at 82 Hz and records the number. *(Phase 6.)*
2. **Glide.** A ramped `semitones` moves `read_rate` once per block; whether
   that steps audibly at the 187 Hz block rate is a measurement. *(Phase 6.)*
3. **ANTI-FEEDBACK** is a single-sideband *frequency* shift (S1 p. 9) the
   palette cannot do; it is left out of §6 rather than faked with a ratio.
   Whether it earns a node is `RingMod`'s question. *(Phase 0 survey.)*
4. **Where the `Delay` macro's line lives.** `audiodelays.Echo` floors its
   delay at the output buffer size (`Echo.c:126-128`; measured in the
   `StereoWidener` seed) — but **only in its `freq_shift = False` branch**
   (`Echo.c:116`), and `freq_shift` defaults to `True` (`Echo.c:461`), where
   the line is always the full `max_delay_ms` and the delay is set by a read
   *rate* instead (`Echo.c:118-120`); re-measured 2026-09-06, `freq_shift`
   left at its default delivers 1, 5, 14, 20, 30 and 40 ms to within 0.02 ms
   at `buffer_size` 2048. So 7.5 ms is reachable on `Echo` in doppler mode,
   at the cost of a pitch-bend on every time change — which is why
   `audioecho.FeedbackDelay`, clamping at one frame
   (`audioif_feedback_delay.c:82-83`) with no rate trick, is still the
   recommendation. *(Phase 6.)*


## Appendix

All measurements 2026-09-06 on this machine with
`audiocomponents/.venv/bin/python` (the CPython build of audioif), 48 kHz,
16-bit signed stereo, `buffer_size` 2048 bytes unless stated. Probe scripts
live in the session scratchpad, not the repo; the implementation session
re-writes them against `tools/render_effect.py` and `tools/effect_probes/` when the
kit spec lands.

### A0 — what Dattorro actually says

Constant pitch change: *"i.frac = NOMINAL_DELAY + (1 − pitch change ratio)·n
… This verifies that the pitch change is indeed constant when i.frac varies
linearly. Unfortunately i.frac will eventually pass one or the other
delay-line boundary, so this technique cannot be used indefinitely."* The
splice: *"Each jump target is determined by a very high-speed custom
autocorrelator seeking periodicity within the delay-line contents. Cross
fading is employed by the splicer using two quadrants of a raised cosine."*
The delay cost: *"To perform well upon polyphonic music, the time compansion
and pitch shift algorithms require as much as 60 ms. That much delay is
easily perceptible, and a compromise is nearly always necessary. Vibrato, on
the other hand, can be performed well using only about 1-ms nominal delay."*
Also: the all-pass interpolator's *"useful transposition range … about plus or
minus one semitone"*, which rules it out here; and linear interpolation's
instantaneous transfer traversing *"from an all-pass transfer function … to an
averaging transfer function (1 + z⁻¹)/2 in the middle"* — the HF loss a swept
read costs.

### A1 — the wet path's minimum delay is the crossfade, not zero

A full-scale click at frame 100 into `PitchShift(semitones=0, mix=1,
window=2048, overlap=128)` comes out at frame **132**: 32 frames =
`overlap_bytes / 2 / channel_count`, 0.67 ms. Supports T2's "not zero at r = 1".

Re-measured 2026-09-06 at three overlaps, stereo, window 2048 bytes: overlap
128 → first non-zero output frame 132 (delay **32** frames), 256 → 164
(**64**), 512 → 228 (**128**). The minimum wet delay is exactly the overlap
in frames at every setting, so Tier 3's "minimum = the crossfade" is a
measured identity and not an approximation.

### A2 — the splice comb and the dominant line's displacement

440 Hz sine, r = 2, 65 536-pt Hann STFT of a steady segment. Comb spacing
matches f_s·|r−1|/W in every case; the dominant line is displaced by what T4
predicts:

| window (bytes) | W (frames) | f_splice | dominant line | predicted | error |
|---|---|---|---|---|---|
| 1024 | 256 | 187.50 Hz | 815.19 Hz | 815.0 Hz | −132.5 cents |
| 2048 | 512 | 93.75 Hz | 908.94 Hz | 908.75 Hz | +56.0 cents |
| 4096 | 1024 | 46.88 Hz | 862.06 Hz | 861.87 Hz | −35.7 cents |
| 8192 | 2048 | 23.44 Hz | 885.50 Hz | 885.31 Hz | +10.8 cents |
| 16384 | 4096 | 11.72 Hz | 885.50 Hz | 885.31 Hz | +10.8 cents |

The model is Δ = −wrap(f_in·W/f_s)·f_s/W, `wrap` mapping to (−0.5, 0.5]. It
predicts every measured line to within 0.2 Hz — under one FFT bin (0.73 Hz).
Raising `overlap` from 128 to 1024 bytes at window 8192 lifted the fraction of
0–6 kHz energy in the dominant line from 0.846 to 0.871 and **moved no line**:
the crossfade trades sideband level, not sideband position, which is why T3
and T4 are separate traits. A first, cruder pass over the same data using
`argmax` alone read the shift at +54.6 cents where the ratio was exactly 2 —
the number that first looked like a tuning bug and turned out to be this.

### A3 — the tail reaches exact zero

A 1024-frame 440 Hz burst then silence, +7 semitones, window 2048 bytes: the
last non-zero output frame is **1390**, i.e. 367 frames (7.6 ms) after the
input ends, and every frame from 2000 on is exactly 0. No held DC; this node
is not in audioif#23's class.

### A4 — `mix = 0` is not a wire inside the node

Full-scale ramp (−32768 … +32767) through `PitchShift(semitones=0, mix=0)`:
**1192 of 8192 samples differ**, largest deviation 4247 LSB, −32768 → −28521.
Cause: `audioif_pitchshift.c:42` → `audioif_synth_dsp.c:20-27`, which
soft-knees everything outside ±28000.

**Corrected 2026-09-06 (palette verifier), one LSB:** the seed read the
identity band off a ramp whose steps skipped ±28000 and recorded "largest
input surviving unchanged 27999". Re-measured against a probe that holds
27998, 27999, 28000, 28001, 28002 and their negatives explicitly:
28000 → 28000, **28001 → 28000**, 28002 → 28000, −28000 → −28000,
+32767 → 28520, −32768 → −28521. So the band is |x| ≤ **28000** inclusive,
which is what `audioif_synth_dsp.c:22-24` says — the compression arms fire on
`sample < range_low` and `sample > range_high`, both strict. Nothing about
§4's conclusion moves: the node is still not a wire at `mix = 0`.

### A5 — the composed dry path is a wire

The same ramp through `Splitter(taps=2) → Mixer.voice[0]` (level 1.0, pan 0)
with `voice[1]` playing a live `PitchShift` at level 0.0: **0 of 2048 samples
differ**. A single Mixer voice at level 1.0 is byte-identical too. This is the
measurement §4's topology rests on.

### A6 — a note for the kit spec: the Splitter's ring drops sparse probes

A `RawSample` longer than 8192 frames (`audioif_splitter.h:20`) returns its
whole buffer on one pull, and the Splitter drags every laggard tap's cursor
forward past what it never collected. A sparse probe (one click in 40 000
frames) is therefore silently discarded before any tap reads it — the class
renders exact silence and looks broken. Probe material for every Splitter-fed
class must be **at most 8192 frames**, or fed in chunks. This cost the first
pass of A1 real time and belongs in the measurement-kit spec, not only here.

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

Rate note: window and crossfade are specified in **milliseconds** and
converted to frames at the running rate, so T2 holds at every rate, and T3/T4
depend only on window *time* and ratio. No Tier 2 trait is rate-limited.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Eventide, *Model H910 Harmonizer* manual, Part #141252 Rev A — **the manual for Eventide's H910 *plug-in*** (UA-hosted), which states the modelled front panel's "controls have the same range and characteristics as the front panel controls of the hardware" and "The pitch change splicing method is the same as the hardware's – the glitch is back!" (p. 3) | Every panel control's range and law; the ~30 ms varying delay; the switched delays; the ratio table; the keyboard law; the free-running LC clock | Bare copyright notice "© 2015 Eventide Inc." (p. 11) with no rights or licence statement — treated as all rights reserved; read as a document | https://media.uaudio.com/support/manuals/dd/Eventide%20H910%20Harmonizer%20Manual.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 11 pages, `pypdf`); every quotation and page number above re-checked against the extracted text |
| S2 Eventide, "Flashback #4.2: H910 Harmonizer® The Product" | Read-rate-vs-write-rate account; buffer "typically 20-30 msec"; the offset-delay crossfade at the splice; one keyboard drove three H910s | "Copyright © 2026 Eventide Inc. All Rights Reserved." | https://www.eventideaudio.com/blog/50th-flashback-4-2-h910-harmonizer-the-product/ | 2026-09-06; re-fetched in the audit, quotations and licence line confirmed verbatim |
| S3 J. Dattorro, "Effect Design, Part 2", *JAES* 45(10), 1997 | Constant-pitch read-index law; the delay-line-boundary problem; raised-cosine splice with autocorrelated jump targets; 60 ms for polyphonic material; linear-interpolation HF loss (quoted in A0) | No rights statement anywhere in the file (the author's own CCRMA copy of a JAES 1997 paper) — **licence unverified, treated as copyleft**: read as a paper, nothing ported | https://ccrma.stanford.edu/~dattorro/EffectDesignPart2.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 25 pages, `pypdf`); the read-index law, the autocorrelator/raised-cosine splice, the 60 ms figure and the interpolator quotations in A0 all re-checked verbatim |
| S4 Eventide, "H910 Harmonizer" product page | "up to 112.5 msec of delay"; "two-octave range" | "Copyright © 2026 Eventide Inc. All Rights Reserved." | https://www.eventideaudio.com/rackmount/h910-harmonizer/ | 2026-09-06; re-fetched in the audit, both figures and the licence line confirmed verbatim |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | The ratio span is exactly one octave each way (macro ends give r = 0.500 and 2.000) and an integer-semitone setting *n* gives r = 2^(n/12) within 1 % of ratio, matching the H910's own table (+7 → 1.4983, −7 → 0.6674) | S1 pp. 7-8 | high | An end stop away from 0.5/2.0; a table that is not 2^(n/12); a law linear in ratio rather than band-spread | Wet/input dominant-partial ratio, 440 Hz sine, n ∈ {−12,−7,−5,0,+5,+7,+12}, with T4's correction |
| T2 | The wet path is a **continuously varying** delay whose swing equals the stated window (order 30 ms) and whose minimum is the crossfade, not zero — a click's wet arrival moves repeat to repeat at r ≠ 1, and at r = 1 it is fixed and non-zero | S1 p. 6; S2 | high | A constant wet delay at r ≠ 1; zero wet delay at r = 1; a swing over 5 % from the reported window | Click train (20 ms) fully wet at r = 2^(7/12): arrivals form a sawtooth of `window_ms` ± 5 % with minimum `crossfade_ms` |
| T5 | Feedback is taken **after** the shifter, so the n-th repeat is transposed n times (r^n·f_in) and the loop self-oscillates above unity gain | S1 p. 6; **the ±30 cent window is this seed's** | high | Repeats at constant pitch (feedback tapped pre-shift); a loop that cannot oscillate | Click, r = 2^(7/12), feedback 0.6, delay 60 ms; four repeats, each 700 ± 30 cents above the last **after the T4 correction is applied to each repeat's dominant line**. Uncorrected the measurement cannot pass on a correct build: at the default 1024-frame window and r = 2^(7/12), f_splice = 23.4 Hz, so the raw line is displaced by up to 11.7 Hz — **±30 cents at the first repeat** (659 Hz), the whole of the stated window before any real error, and more at every repeat after |
| T6 | The dry path never enters the line: at any mix the dry arrives at sample zero, and mix = 0 is byte-identical | S1 p. 9 | high | A dry component arriving late; any change at mix = 0 | Click at mix 0.5 → two events, first at offset 0; full-scale ramp at mix 0 → zero differing samples (the node fails this internally, A4) |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

1. **S1 is the manual for Eventide's H910 *plug-in***, not a hardware manual.
   Its front-panel descriptions carry the manual's own claim that they match
   the hardware's; MIX/MAIN/OUT 2, the envelope-follower times and GLIDE sit
   in its *Additional Controls* section, the plug-in's rendering of features
   "originally available through external connections or options" (p. 4). The
   licence cell now records what the file carries — a bare copyright notice,
   no rights statement.

*(from §2)*

3. **The date "(1975)" had no source** and is dropped. S2 says only "By 1975,
   IC technology had sufficiently advanced to the point that it became
   practical to design a digital pitch change effects box — the H910"; S1 p. 2
   captions its marketing scan "circa 1976". No source reached states a
   release year.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**0.04**, ESP32-S3 **0.10**. Lean patch expected: **no** — the kernel is one
add, one compare and at most one crossfade multiply per sample
(`audioif_pitchshift.c:13-55`); the cost is RAM, not CPU — 4.2 kB of line
stereo at the proposed default window, 11.8 kB at 60 ms, plus the Splitter's
fixed 8192-frame stereo ring (32 kB, `audioif_splitter.h:20`), which is the
larger number and is noted as a cross-class question in `Octaver.md` §8.5.

*(from §3)*

Latency (vision §9a). **Dry path: zero samples**, by construction — the dry
never enters the line (T6), so `latency_samples` is 0. The wet path carries
the effect's own transport delay, which is not latency while a dry path
exists but *is* the whole latency at mix = 1, and a stompbox runs at mix = 1;
the docstring therefore states the fully-wet figure in ms at 48 kHz:
minimum = the crossfade (default 64 frames, **1.33 ms**), mean ≈ window/2,
maximum = the window (default 1024 frames, **21.3 ms**). The knob that trades
CPU-and-RAM for artefact is `window_ms`, 5–60 ms, defaulting to **21.3 ms** —
the shortest window that keeps f_splice under 50 Hz across the whole ratio
range, so T3's comb stays out of the middle of the band. Dattorro's 60 ms for
polyphonic material (S3) is offered, not defaulted. `crossfade_ms`
(0.5–5 ms) defaults to its shortest, 1.33 ms. There is no lookahead and no
other latency-adding option.

*(from §4)*

```
source ─ audioroute.Splitter(taps=2) ┬─ tap 0 ─────────────────► Mixer.voice[0]   dry
                                     └─ tap 1 ─ PitchShift ────► Mixer.voice[1]   wet (node mix = 1)
                        audioecho.FeedbackDelay in the wet return, only when
                        feedback > 0 or the Delay macro > 0
```

*(from §4)*

**The dry must not pass through the shifter node**, and that is measured, not
assumed: with the node's own `mix` at 0, a full-scale ramp comes back changed
— 1192 of 8192 samples differ, −32768 reads back −28521 — because
`audioif_pitchshift.c:42` runs every sample through
`audioif_mix_down_sample(word, scale, −28000, 28000)`, identity only for
|x| ≤ **28000** (`audioif_synth_dsp.c:22-26`: it compresses below `range_low`
and above `range_high` and returns the sample untouched between them, so the
band is closed at both ends — the seed's earlier "27999" was one LSB narrow
and is corrected, A4). The same ramp through
`Splitter → Mixer.voice[0]` with a second voice at level 0 is byte-identical,
0 of 2048 differing (A4, A5). That single measurement is what makes this class
*audioif* tier rather than *stock*, and it buys Tier 1's wire.

*(from §4)*

Python computes, at construction only: window and crossfade frames from
milliseconds and the running rate, then the node's `window`/`overlap` in
**bytes** (`frames·2·channel_count`; the node divides them back at
`PitchShift.c:167`, `:173`). On a macro move it writes `node.semitones` and
two Mixer voice levels. Nothing per sample in Python, no table, so nothing
here is float-width sensitive. **Mono:** the window is sized in frames from
milliseconds, so a mono source gets the same window *time*, the same traits
and half the *line* RAM — the Splitter's ring does **not** halve, because it
is declared stereo whatever the source is (`int16_t ring[8192 * 2]`,
`audioif_splitter.h:29`) and a mono frame is duplicated into both lanes on
write (`audioif_splitter.c:30-31`). `capabilities` = `()` (D10) — nothing in
the H910 reads a transport and `Delay` is a millisecond span, not a note
value.

*(from §4)*

**Palette verification, 2026-09-06 (pitch-stereo unit).** Every node claim in
this section was re-read in the audioif tree and re-measured on
`audiocomponents/.venv/bin/python`: the truncated read and the linear
crossfade (`audioif_pitchshift.c:26`, `:27-38`), `read_rate =
2^(semitones/12) · 256` (`audiodelays/PitchShift.c:106`, `PitchShift.h:18`),
the wrap at `window_samples << 8` (`audioif_pitchshift.c:52-53`), the
bytes→frames division (`PitchShift.c:167`, `:173`), the node's `mix` scaled
×2 before the kernel so `mix = 1` is fully wet (`PitchShift.c:217`,
`audioif_pitchshift.c:39-41`), the mix-down band (above), and the composed
wire (A5, re-measured: 0 of 4096 samples differ). A1 was re-measured at three
overlap settings and generalised: the wet minimum delay at r = 1 is exactly
`overlap_bytes / 2 / channel_count` frames (A1).

*(from §7)*

- `pitch.py:22` — `MACRO_LABELS = ()`. The class offers a host nothing; its
  only handle, `set_semitones` (`pitch.py:31`), is not on the contract's live
  surface, so a host cannot reach the one thing the effect does.

*(from §7)*

- `pitch.py:27` — `window=2048` is a fixed literal **in bytes**. Stereo that
  is 512 frames (10.7 ms); mono, the same literal silently becomes 1024
  frames (21.3 ms), so the effect's character changes with the source's
  channel count. The rebuild specifies the window in milliseconds.

*(from §7)*

- `_core.py:140-141` — `LATENCY_SAMPLES = 0` and `TAIL_SAMPLES = None`
  inherited unchanged, so the class reports zero latency while its whole
  output *is* the delayed line, and reports no tail. Measured tail after a
  burst: 367 frames (A3).
