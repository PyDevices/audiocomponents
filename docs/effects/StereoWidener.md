# Effects Dossier — `StereoWidener` (no standout — design grade)

**Class:** `lib/audioeffects/pitch.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Pitch and stereo, roadmap Phase 6
**Standout:** none. Vision §4.2 grades this *design*, and that is
**confirmed**: a widener is not a box anyone built once and everyone copied,
it is two textbook mechanisms — precedence (Haas) and mid/side gain — and the
sources below are the textbook, not a schematic.
**Grade:** design
**Portability tier:** needs audioif-own nodes (`audioroute.Splitter`,
`audioecho.FeedbackDelay`, and for the Mid/Side character one new node — §5;
the character is composable on today's palette but not with W3, W5 and W6 all
holding at once, measured in A6)
**Status:** seed (Phase 0)

## 1. The mechanism, in one paragraph

Two mechanisms, and the class carries both as characters because each fails
where the other works. **Precedence (Haas).** Add a delayed copy of a signal
on the opposite side and the ear fuses the two into one event placed by the
*first* arrival: below about 2 ms the two sum into a phantom between them,
between 2 and 5 ms the leading sound alone fixes the location, and "A single
reflection arriving at a delay of between 5 and 30 ms can be up to 10 dB
louder than the direct sound without being perceived as a secondary auditory
event" (S1, citing Haas 1951); Sound On Sound puts the same finding as "For
time differences of up to 30ms, the first arrival determined the perceived
source location even if the second arrival was as much as 10dB louder. Only
when the second arrival was around 15dB louder did it become dominant" (S2).
Past the echo threshold — "about 50 ms" for speech, "approaching 100 ms" for
music (S1) — the copy stops being width and starts being a slap. The cost is
arithmetic and unavoidable: two copies of one signal a time τ apart form a
feedforward comb, H(z) = 1 + αz⁻ᴷ, whose minima for positive α fall at
f_s/2K, 3f_s/2K, 5f_s/2K … spaced f_s/K apart (S4; for negative α they fall at
0, f_s/K, 2f_s/K …) — so with the dry on one side and the delayed copy on the
other each channel stays spectrally intact and the comb appears only when
someone sums to mono — which is S4's arithmetic, not a claim of S3's *(audit
correction, §2)*. What this seed does take from S3 is the remedy it names for
a delayed copy's "lopsided" bass, "A high-pass filter at about 100Hz usually
works well", which W2's `Bass Mono` generalizes. **Mid/side gain.** Form
M = (L + R) and S = (L − R) — Sound On Sound writes the pair with a −3 dB
normalisation each way, "Mid = (left + right) –3dB", "Side = (left – right)
–3dB", "Left = (mid + side) –3dB", "Right = (mid – side) –3dB" (S3, which
calls the attenuations "optional … included so
that a complete round-trip process … doesn't result in an increase in signal
level") — and scale S. Width then costs nothing spectrally and is *perfectly*
mono-safe, because summing L + R cancels S exactly at every width; what it
cannot do is widen a mono source, whose S is zero. The
trade-off between the two is the whole design: Haas widens anything and
punishes a mono fold-down; mid/side is free in mono and does nothing to a mono
input. S3's own caution bounds the second — "the level of the Side signal
shouldn't exceed that of the Mid signal", beyond which the sound "will cause
phase and mono compatibility problems."

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Wikipedia, "Precedence effect" | Summing localization below 2 ms … (App. S1) | "Text is available under the Creative Commons … (App. S1) | https://en.wikipedia.org/wiki/Precedence_effect | 2026-09-06; re-fetched in the audit — the 5–30 ms / 10 dB sentence, the 2 ms and 2–5 ms bands, the 50 ms / 100 ms echo thresholds and the CC BY-SA 4.0 line all confirmed verbatim |
| S2 Sound On Sound glossary, "Haas Effect" | Fusion below 5 ms for transients … (App. S2) | "All contents copyright © SOS Publications … (App. S2) | https://www.soundonsound.com/glossary/haas-effect | 2026-09-06; re-fetched in the audit — "for time differences of up to 30ms … as much as 10dB louder. Only when the second arrival was around 15dB louder did it become dominant", the 5 ms / 40 ms fusion windows and the copyright line all confirmed verbatim |
| S3 Sound On Sound, "Processing Stereo Audio Files" | The M/S matrix with its −3 dB normalisation … (App. S3) | as S2 | https://www.soundonsound.com/techniques/processing-stereo-audio-files | 2026-09-06; re-fetched in the audit — the four matrix lines, "the level of the Side signal shouldn't exceed that of the Mid signal", the "interleaved comb-filters" sentence and the 100 Hz remedy confirmed verbatim, **and the mono-compatibility sentence that corrects §1 read for the first time** |
| S4 Wikipedia, "Comb filter" | H(z) = 1 + αz⁻ᴷ; notches at odd multiples of f_s/2K … (App. S4) | CC BY-SA 4.0 ("Text is available under the … (App. S4) | https://en.wikipedia.org/wiki/Comb_filter | 2026-09-06; re-fetched in the audit — the transfer function and the f_s/2K, 3f_s/2K, 5f_s/2K minima confirmed, **with the positive-α condition the seed had dropped** |

**Not reached, and therefore not cited:** Litovsky, Colburn, Yost & Guzman,
"The precedence effect" (*JASA* 1999) — the primary review S1 draws on — at
cogsci.msu.edu, which failed TLS ("certificate has expired"); no other
reachable copy was found this run. The 1–5 ms fusion window for clicks and the
7–8 ms echo threshold for equal-amplitude tones appeared in a search summary
of that paper and are **not** used, because the paper itself was not read.
Nothing here was read for code (vision §5).

**Audit, 2026-09-06 (licence and citation pass).** All four rows re-fetched
and every quotation re-read at source; all four licence calls stand as
written, and the Litovsky PDF was re-tested from this machine and still fails
to connect, so it stays *not reached*. Two corrections were applied in §1:

1. **The comb minima carry S4's positive-α condition.** The seed gave …  *(argument in full: App. R)*
2. **S3 was cited for the mono-sum comb it does not claim.** S3's …  *(argument in full: App. R)*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

A design grade is normally carried on Tier 1 and Tier 3 alone (vision §4.1).
This one states the textbook properties as Tier 2 anyway, because they are
falsifiable numbers rather than taste, and because one of them is what the
node ask in §5 rests on.

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — textbook properties, stated so a measurement can fail them

| # | Character | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|---|
| W1 | Haas | The widened copy is delayed by exactly the `Delay` macro's setting, to within **one sample**, anywhere in 1–40 ms and at every rate — and the class refuses to ship a delay it did not deliver | S1 fixes the span the class must reach (5–30 … (App. W1) | high | A delivered delay differing from the setting by more than one sample at any setting or rate; a floor below which shorter settings collapse; a delay that quantises to the block or buffer length rather than to the sample | Click through the class … (App. W1) |
| W2 | Haas | Mono-summing the output gives a comb whose first null is at 1/(2τ) and whose nulls are spaced 1/τ (S4), each within **one analyser bin**, and the class states its default τ's first null in its docstring. With `Bass Mono` engaged at corner f_c, no null appears below f_c | S4 (the α > 0 minima are 1/(2τ), 3/(2τ) … (App. W2) | high | No comb in the mono sum; nulls at a spacing other than 1/τ, or off the odd multiples of 1/(2τ) by more than a bin; nulls surviving below `Bass Mono`'s corner | Swept sine (**not noise** … (App. W2) |
| W3 | Mid/Side | The mono sum is **independent of width**: L + R is unchanged, to within 0.05 dB at every frequency, as `Width` moves across its whole 0–2 span, because L + R cancels S exactly (S3's matrix) | S3 | high | A mono sum that moves with width; any comb in the mono sum | Mono sum level, third-octave … (App. W3) |
| W4 | both | A mono source gets **a wire**, byte-identical, in both characters — not a mono-summed version of the stereo behaviour, and not a widened mono signal. The contract forces this: `create()` builds every node at the source's channel count (`_core.py:202`) and raises if the output's differs (`_core.py:218-223`), so a mono-in/stereo-out widener cannot exist here, and combing a mono signal against a delayed copy of itself is not width, it is a filter | `_core.py:202`, `:218-223` … (App. W4) | high | Any change to a mono source in either character; a class that raises on a mono source instead of passing it | Mono full-scale ramp through both … (App. W4) |
| W5 | both | `Width` at its neutral setting (1.0 for Mid/Side, 0 for Haas) is a **wire**, byte-identical, with the widening path built but contributing nothing — not merely quiet | Tier 1, made specific to this class's own knob | high | Any level, spectrum or channel-balance change at neutral width; a widening path whose contribution is a fixed literal (which is today's defect — A3) | Full-scale ramp … (App. W5) |
| W6 | Mid/Side | Width is exactly S3's matrix and nothing else, so the outputs follow L′ = M + w·S and R′ = M − w·S with M = (L+R)/2, S = (L−R)/2 at every setting. A hard-panned-left source (R = 0) therefore leaves the class as L′ = (1+w)/2·L, R′ = (1−w)/2·L: −6.02/−6.02 dB at w = 0, −2.50/−12.04 at w = 0.5, 0 dB and an **exactly zero** right channel at w = 1 (the byte-identical wire of W5), +1.94/−12.04 **inverted** at w = 1.5, and +3.52/−6.02 **inverted** at w = 2. Every level within 0.1 dB and every polarity exact | S3's four matrix lines ("Mid = (left + right) … (App. W6) | high | A channel pair off that law by more than 0.1 dB at any w; no polarity inversion in the right channel above w = 1; a law that saturates, soft-knees or clamps before w = 2 | Hard-panned-left sine at **−12 … (App. W6) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Haas character** — buildable today:

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

### `audioroute.MidSide` — a zero-latency mid/side matrix

*(Title and the first two bullets rewritten by the palette verifier,
2026-09-06. The ask was filed as "the one cross-channel operation the palette
lacks"; the palette does have one, and the ask now stands on the price of
using it rather than on its absence.)*

- **Traits it unblocks:** **W3**, **W6** and **W5's Mid/Side half** — not …  *(argument in full: App. R)*
- **What the palette does instead, and why it fails the trait set.** Two …  *(argument in full: App. R)*
- **The refutation, restated so it can actually fail.** The old bar — "name a …  *(argument in full: App. R)*
- **Design sketch.** `audioroute.MidSide(source, width=1.0)`, per frame in …  *(argument in full: App. R)*
- **Cost estimate.** Below `Multiply`'s, which is one multiply and one shift
  per sample (`audioif_multiply.c:38`) — call it under 1 % of a stereo block
  on the S3. No RAM.
- **Where it lives.** `audioroute`, beside `Splitter`: it is routing, not …  *(argument in full: App. R)*
- **Priority, and what to do if it is cut.** Lower than the Octaver's …  *(argument in full: App. R)*
- **Palette-verifier judgement, 2026-09-06: the ask SURVIVES**, on the
  restated bar above rather than the one it was filed under. Full measurement
  in A6.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Width` | UNIPOLAR | 0 … 2 | the one control a widener has. 0 = mono-ish/off, 1 = unchanged in Mid/Side, 2 = S3's upper caution ("the level of the Side signal shouldn't exceed that of the Mid") |
| 1 | `Delay` | UNIPOLAR | 1 … 40 ms | the Haas delay; the useful window is 5–30 ms (S1) and the span reaches past both ends so the class can be measured failing |
| 2 | `Bass Mono` | UNIPOLAR | 0 … 300 Hz | S3's remedy for lopsided bass — high-passes the widened path only; 0 disables |
| 3 | `Dry` | UNIPOLAR | −∞ … 0 dB | the centre's own level |
| 4 | `Level` | UNIPOLAR | −24 … +6 dB | output trim |

Characters: **Haas** (default) and **Mid/Side** (needs §5's node; until it
lands, selecting it raises with the reason). Patches: 0 *Moderate width,
14 ms* (constructor defaults) · 1 *Narrow* · 2 *Wide, bass kept centre* ·
3 *Mono* · 4 *Doubling, 30 ms* · 5 *Side-only shimmer* · 6 *Mid/side, gentle* ·
7 *Mid/side, wide*.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/pitch.py`. Four of these are measured, not
inferred; the measurements are in the appendix.

- `pitch.py:138` — `self.mixer.voice[1].level = 0.8` is a **fixed literal …  *(argument in full: App. R)*
- `pitch.py:129-131` — `audiodelays.Echo` floors its line at the output …  *(argument in full: App. R)*
- `pitch.py:130` — `max_delay_ms=int(delay_ms) + 20` truncates a float, so
  `delay_ms=14.9` sizes a line for 14, not 15.
- `pitch.py:136`, `:139` — pan constants `-0.3 * width` and `0.9 * width` are …  *(argument in full: App. R)*
- `pitch.py:123` — `MACRO_LABELS = ()`. `width` is the class's only real
  control and it is constructor-only, so a host cannot widen anything.
- `pitch.py:115-117` — no statement anywhere of what a mono source gets, …  *(argument in full: App. R)*
- `_core.py:140-141` — `LATENCY_SAMPLES = 0` / `TAIL_SAMPLES = None`
  inherited: zero latency is right, but the 21.3 ms line's tail is reported as
  unknown.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Whether the Mid/Side character ships at all.** It depends on §5's node
   surviving Gate 0. The class is useful without it and useless in a mono
   fold-down without it; the recommendation is to build it, and the fallback
   — one character, with the mono-sum comb documented in the docstring and the
   first null frequency printed — is written down here so nobody has to invent
   it later. *(Gate 0, then Phase 6.)*
2. **The pan law.** The Mixer only attenuates (A2), so `Width` at the Haas
   character's extreme narrows the field by turning things down rather than by
   moving them. Whether the rebuild should compensate with a level trim so
   width is loudness-neutral is a measurement — third-octave level of the mono
   sum across the `Width` sweep — not a preference. *(Phase 6.)*
3. **`Width` above 1 in the Haas character.** S3 bounds side level in the
   mid/side world; there is no equivalent published bound for a Haas widener's
   opposite-pan depth, and none was found this run. The span in §6 stops at 2
   for symmetry with the other character, which is a convention, not a source.
   *(Phase 6; flag it as unsourced in the evidence pack rather than dressing
   it up.)*
4. **Mono-in/stereo-out — asked and answered in this run, not left open.**
   The obvious question for a widener is whether it may turn a mono source
   into a stereo one. It may not: `_core.py:202` builds every node at the
   source's channel count and `_core.py:218-223` raises if the output's
   differs. §4 and W4 are written to that answer — a mono source gets a wire.
   What remains is only whether the README catalogue should say so loudly
   enough that nobody buys the class expecting a mono pedal. *(Phase 6, one
   line of docs.)*


## Appendix

All measurements 2026-09-06 on this machine with
`audiocomponents/.venv/bin/python` (the CPython build of audioif), 48 kHz,
16-bit signed stereo, `_core.pcm()` defaults.

### A1 — `audiodelays.Echo` floors the delay at the output buffer length

`Echo(max_delay_ms=34, delay_ms=14.0, decay=0.0, mix=1.0, freq_shift=False,
buffer_size=2048)` fed a single click at frame 64: the delayed copy comes out
at frame **1088**, i.e. 1024 frames = **21.33 ms**, not the 672 frames
(14 ms) requested. Cause, read from the source: `Echo.c:122` computes the line
length in bytes from the requested milliseconds, and `Echo.c:126-128` raises
it to `self->buffer_len` — the output buffer, 2048 bytes — whenever it is
shorter. With `_core.pcm()`'s 2048-byte buffer the **minimum reachable delay
is 21.33 ms at 48 kHz**, which sits at the far end of Haas's useful window
before the class has said anything. A smaller `buffer_size` moves the floor
(512 bytes → 5.33 ms) at the cost of more per-block overhead;
`audioecho.FeedbackDelay` removes it entirely, clamping at one frame
(`audioif_feedback_delay.c:82-83`). That is why §4 chooses the latter.

### A2 — the Mixer's pan runs backwards, and only attenuates

`Mixer(voice_count=1)`, one voice at `level=1.0`, `panning=+0.9`, fed a
full-scale click: **left peak 20000, right peak 1999**. Positive panning
attenuates the *right* channel. Read back in the source, `Mixer.c:337-341`:
`panning >= 0` sets `right_panning_scaled = 32767 - panning`, `panning < 0`
sets `left_panning_scaled = 32767 + panning`, and `:343-347` applies each to
its own channel. Two consequences for any class that pans: the sign is
inverted from the usual convention, and the near channel is never boosted, so
panning a stereo signal is a balance control.

### A3 — the current class is not a wire at zero width

`StereoWidener(width=0.0)` fed a 440 Hz sine: output RMS **8004** in both
channels against the source's **8484** — 0.5 dB down, with the 21.33 ms comb
of A1 present in both channels, because `pitch.py:138` holds the delayed
voice at 0.8 regardless of width. At `width=0.7` the same source gives
L 6371 / R 8198, the asymmetry of `pitch.py:136`/`:139`.

### A4 — the mono-sum comb, measured, with its predicted nulls

`StereoWidener(delay_ms=14.0, width=0.7)` fed 8000 frames of Gaussian noise;
output summed to mono and divided, bin by bin, by the source's spectrum
(4096-point Hann):

| f | measured | predicted null for τ = 21.33 ms |
|---|---|---|
| 23.4 Hz | −2.96 dB | null #1 |
| 46.9 Hz | +1.04 dB | — |
| **70.3 Hz** | **−10.58 dB** | **null #2** |
| 93.8 Hz | +6.01 dB | — |
| 117.2 Hz | −1.70 dB | null #3 |
| 140.6 Hz | −0.29 dB | — |
| **164.1 Hz** | **−7.87 dB** | **null #4** |
| 187.5 Hz | +4.09 dB | — |
| 210.9 Hz | −2.91 dB | null #5 |

The deepest points land on odd multiples of 1/(2τ) = 23.44 Hz and the peaks
land between them, which is S4's comb with the τ that A1 says the node
actually delivers — not the 14 ms the class asks for. A note for the kit spec:
**noise is the wrong probe for this measurement.** The per-bin variance of a
single noise realisation swamped a naive minimum-finder, which reported *no
notches at all* on data that plainly has them; a swept sine, or noise averaged
over many realisations, is what W2 must use. That near-miss is the shape
`workspace-craft.md` names — a checker whose material could not express the
thing it was cited to rule out.

### A5 — the palette's cross-channel operations, enumerated *(corrected)*

**Corrected 2026-09-06 by the palette verifier.** This appendix originally
concluded "No node reads one channel while writing the other", and §5's
refutation rested on it. It is wrong, and it is wrong in a way worth naming:
the enumeration reached `audioecho.FeedbackDelay`, looked at `cross_feed`,
correctly ruled *that* out — and stopped, missing `input_pan` on the same
node, four lines away in the same switch. Ruling out one path through a node
is not ruling out the node.

Enumerated again, with the line each was read at:

- `audioif_splitter.c:29-31` — writes L and R straight through, or duplicates
  a mono frame into both. No swap.
- `Mixer.c:343-347` — independent per-channel gains; `:332` clamps the level
  to 0…1 at render time, so no voice can invert.
- `audioif_multiply.c:32-45` — element-wise, index for index.
- `audioif_pitchshift.c:14-16`, `audioif_echo.c:13-16` — channel-major planes
  processed independently.
- **`audioif_feedback_delay.c` — the one exception, and it crosses twice.**
  `cross_feed` (`:120-121`, applied `:248-249`) mixes the two *delayed* lines
  inside the feedback write, never the dry path, and is clamped non-negative,
  so it cannot difference. But **`input_pan`** (`:126-141`, applied
  `:251-254`) mixes the two *inputs*: at hard over it feeds one lane
  `0.5·L + 0.5·R` and the other nothing. That is (L+R)/2 — the mid signal —
  and A6 measures it.

Reproducible: grepping `src/shared/*.{c,h}` and `src/*/*.{c,h}` for
`1u - channel|1 - channel|channel ^ 1|other_source|other_channel|cross_feed|
feed_other` returns `audioif_feedback_delay.c` (12 hits) and its header (2),
`audioecho/FeedbackDelay.c` (1, the option name), and three false positives
that are **not** signal paths — `synthio/__init__.c` and
`audiomp3/MP3Decoder.c` use `other_channel` for the render-once-hand-back-twice
cache in single-channel-output mode, and `audiocore/WaveFile.c:235` is
unrelated arithmetic. No other node reads one channel while writing the
other.

### A6 — the mid/side matrix, composed on today's palette and measured

Palette verifier, 2026-09-06, `audiocomponents/.venv/bin/python`, 48 kHz
16-bit stereo, `buffer_size` 2048.

**The mid extraction.** `FeedbackDelay(delay_ms=0.0, feedback=0.0, mix=2.0,
input_pan=−1.0, max_delay_ms=50)` fed L = 300 Hz at 10 000 and R = 700 Hz at
6 000: the left output tracks (L+R)/2 **delayed exactly one frame**, maximum
absolute error **0.5 LSB** over 200 frames, and the right output is exactly 0
at every frame. `delay_ms=0.0` is clamped to one frame by
`audioif_feedback_delay.c:82-83`, which is where the one sample comes from and
why it cannot be avoided.

**The matrix.** `Splitter(taps=3)`; taps 0 and 1 → `FeedbackDelay` at
`input_pan` −1 and +1 → `Mixer` voices 0 and 1 at level 1−w; tap 2 → the
source → voice 2 at level w. W6's probe (hard-panned-left 1 kHz sine at
−12 dBFS), source path delayed to match:

| w | L measured | L ideal (1+w)/2 | R measured | R ideal (1−w)/2 |
|---|---|---|---|---|
| 0.00 | −6.020 dB | −6.021 dB | −6.020 dB | −6.021 dB |
| 0.25 | −4.083 | −4.082 | −8.522 | −8.519 |
| 0.50 | −2.499 | −2.499 | −12.045 | −12.041 |
| 0.75 | −1.161 | −1.160 | −18.069 | −18.062 |
| 1.00 | +0.000 | 0.000 | silent (−600 dB floor) | −∞ |

Within **0.005 dB** everywhere. W3's probe (mono sum re its w = 1 value,
Goertzel per frequency), both alignments:

| f | source undelayed | source delayed to match |
|---|---|---|
| 100 Hz | +0.004 / +0.001 / +0.000 / −0.001 dB | ≤ 0.002 dB |
| 1 kHz | +0.000 / −0.016 / −0.020 / −0.016 | ≤ 0.001 |
| 5 kHz | +0.001 / −0.351 / **−0.474** / −0.351 | ≤ 0.001 |
| 10 kHz | +0.002 / −1.414 / **−2.010** / −1.414 | ≤ 0.001 |

(columns are `Width` 0, 0.25, 0.5, 0.75; the w = 1 column is the reference and
reads 0.000 by construction.) W3's tolerance is 0.05 dB, so the undelayed
composition passes below about 2 kHz and fails by 40× at 10 kHz. **W5 runs the
other way:** at `Width` 1.0 the undelayed composition is byte-identical
(0 of 8192 samples differ) and the delayed one differs in 4095 of 8192 — the
one-sample shift. That is the whole of §5's case.

`Mixer` cannot rescue `w > 1` by inverting a voice: `level = −1.0` is accepted
by the Python object and renders **silence**, because
`synthio_block_slot_get_limited(&voice->level, 0.0, 1.0)` clamps it
(`Mixer.c:332`). Inversion needs `audiomath.Multiply` against a constant
−32768 stream, which is a fourth node and a fourth tap.

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

This class is **stereo by definition**, so the last invariant is not a
formality: §4 states the mono answer (a wire, forced by the contract) and W4
measures it. The wire invariant also means `Width` at its neutral setting, not
only `mix` at zero — today's class fails that, measured (A3).

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Wikipedia, "Precedence effect" | Summing localization below 2 ms; localization dominance 2–5 ms; the 5–30 ms / 10 dB Haas result (cited to Haas 1951); echo thresholds ~50 ms speech, ~100 ms music; HF-attenuated reflections extending the window | "Text is available under the Creative Commons Attribution-ShareAlike 4.0 License" | https://en.wikipedia.org/wiki/Precedence_effect | 2026-09-06; re-fetched in the audit — the 5–30 ms / 10 dB sentence, the 2 ms and 2–5 ms bands, the 50 ms / 100 ms echo thresholds and the CC BY-SA 4.0 line all confirmed verbatim |
| S2 Sound On Sound glossary, "Haas Effect" | Fusion below 5 ms for transients, up to 40 ms for speech; first-arrival dominance up to 30 ms even when the second is 10 dB louder; 15 dB as the crossover | "All contents copyright © SOS Publications Group and/or its licensors, 1985-2026. All rights reserved." Read as a document | https://www.soundonsound.com/glossary/haas-effect | 2026-09-06; re-fetched in the audit — "for time differences of up to 30ms … as much as 10dB louder. Only when the second arrival was around 15dB louder did it become dominant", the 5 ms / 40 ms fusion windows and the copyright line all confirmed verbatim |
| S3 Sound On Sound, "Processing Stereo Audio Files" | The M/S matrix with its −3 dB normalisation, both directions; side level must not exceed mid; the mono-compatibility warning; delayed-copy "fake" stereo producing interleaved comb filters and lopsided bass unless high-passed above ~100 Hz | as S2 | https://www.soundonsound.com/techniques/processing-stereo-audio-files | 2026-09-06; re-fetched in the audit — the four matrix lines, "the level of the Side signal shouldn't exceed that of the Mid signal", the "interleaved comb-filters" sentence and the 100 Hz remedy confirmed verbatim, **and the mono-compatibility sentence that corrects §1 read for the first time** |
| S4 Wikipedia, "Comb filter" | H(z) = 1 + αz⁻ᴷ; notches at odd multiples of f_s/2K; notch spacing f_s/K | CC BY-SA 4.0 ("Text is available under the Creative Commons Attribution-ShareAlike 4.0 License") | https://en.wikipedia.org/wiki/Comb_filter | 2026-09-06; re-fetched in the audit — the transfer function and the f_s/2K, 3f_s/2K, 5f_s/2K minima confirmed, **with the positive-α condition the seed had dropped** |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Character | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|---|
| W1 | Haas | The widened copy is delayed by exactly the `Delay` macro's setting, to within **one sample**, anywhere in 1–40 ms and at every rate — and the class refuses to ship a delay it did not deliver | S1 fixes the span the class must reach (5–30 ms is the useful window, so a class that cannot deliver 5 ms is not a Haas widener); **the one-sample tolerance is this seed's**, chosen because `audioecho.FeedbackDelay` reads its line per sample with linear interpolation (`audioif_feedback_delay.c:212-228`) and can therefore hold it | high | A delivered delay differing from the setting by more than one sample at any setting or rate; a floor below which shorter settings collapse; a delay that quantises to the block or buffer length rather than to the sample | Click through the class; inter-channel arrival difference in samples, swept over `Delay` ∈ {1, 5, 14, 20, 30, 40} ms at 48 and 44.1 kHz, each against round(ms·f_s/1000). **Planted fault:** build the line on `audiodelays.Echo(freq_shift=False)` at `_core.pcm()`'s 2048-byte buffer instead — a fault already measured, not hypothetical (A1): the 1, 5 and 14 ms settings all deliver 21.33 ms, so those three points must go red while 30 and 40 ms stay green, which also proves the check is not simply always-red. **`freq_shift=False` is load-bearing in that sentence:** the node defaults to `True` (`Echo.c:461`), where there is no floor and every setting is delivered to within 0.02 ms (re-measured 2026-09-06, §4) — plant this fault with the default and it does not fire, and the checker is one that cannot fail |
| W2 | Haas | Mono-summing the output gives a comb whose first null is at 1/(2τ) and whose nulls are spaced 1/τ (S4), each within **one analyser bin**, and the class states its default τ's first null in its docstring. With `Bass Mono` engaged at corner f_c, no null appears below f_c | S4 (the α > 0 minima are 1/(2τ), 3/(2τ), 5/(2τ) …); S3 (the "lopsided bass" warning and the ~100 Hz high-pass remedy); **the one-bin tolerance is this seed's** | high | No comb in the mono sum; nulls at a spacing other than 1/τ, or off the odd multiples of 1/(2τ) by more than a bin; nulls surviving below `Bass Mono`'s corner | Swept sine (**not noise** — A4 records a single noise realisation defeating a naive minimum-finder on data that plainly had the notches), mono sum divided by the source's spectrum; null frequencies against 1/(2τ)·(2k+1). Verified on the current class at the τ its node actually delivers (A4). **Planted fault:** invert one path's polarity at equal gain. Per S4 that moves the minima to 0, 1/τ, 2/τ … — so the frequencies this measurement reports as nulls become *maxima* and every one of them must go red. Reporting only "a deep null exists somewhere" would pass that fault, which is why the measurement is null **positions** and not null depth |
| W3 | Mid/Side | The mono sum is **independent of width**: L + R is unchanged, to within 0.05 dB at every frequency, as `Width` moves across its whole 0–2 span, because L + R cancels S exactly (S3's matrix) | S3 | high | A mono sum that moves with width; any comb in the mono sum | Mono sum level, third-octave, at `Width` ∈ {0, 0.5, 1.0, 1.5, 2.0}; flat within 0.05 dB. This is the trait §5's node ask exists for |
| W4 | both | A mono source gets **a wire**, byte-identical, in both characters — not a mono-summed version of the stereo behaviour, and not a widened mono signal. The contract forces this: `create()` builds every node at the source's channel count (`_core.py:202`) and raises if the output's differs (`_core.py:218-223`), so a mono-in/stereo-out widener cannot exist here, and combing a mono signal against a delayed copy of itself is not width, it is a filter | `_core.py:202`, `:218-223`; S3 (S = L − R is zero in mono); vision §3 Tier 1 | high | Any change to a mono source in either character; a class that raises on a mono source instead of passing it | Mono full-scale ramp through both characters at `Width` extremes: zero differing samples in every case |
| W5 | both | `Width` at its neutral setting (1.0 for Mid/Side, 0 for Haas) is a **wire**, byte-identical, with the widening path built but contributing nothing — not merely quiet | Tier 1, made specific to this class's own knob | high | Any level, spectrum or channel-balance change at neutral width; a widening path whose contribution is a fixed literal (which is today's defect — A3) | Full-scale ramp; zero differing samples in both channels at neutral width, in both characters |
| W6 | Mid/Side | Width is exactly S3's matrix and nothing else, so the outputs follow L′ = M + w·S and R′ = M − w·S with M = (L+R)/2, S = (L−R)/2 at every setting. A hard-panned-left source (R = 0) therefore leaves the class as L′ = (1+w)/2·L, R′ = (1−w)/2·L: −6.02/−6.02 dB at w = 0, −2.50/−12.04 at w = 0.5, 0 dB and an **exactly zero** right channel at w = 1 (the byte-identical wire of W5), +1.94/−12.04 **inverted** at w = 1.5, and +3.52/−6.02 **inverted** at w = 2. Every level within 0.1 dB and every polarity exact | S3's four matrix lines ("Mid = (left + right) –3dB" … "Right = (mid – side) –3dB"); the per-w values are arithmetic on them, and the ÷2 convention rather than S3's −3 dB pair is §5's sketch — both give the same round trip at w = 1 | high | A channel pair off that law by more than 0.1 dB at any w; no polarity inversion in the right channel above w = 1; a law that saturates, soft-knees or clamps before w = 2 | Hard-panned-left sine at **−12 dBFS** (L′ reaches +3.52 dB at w = 2, so a full-scale probe would clip the measurement rather than the class); per-channel level in dB against (1±w)/2, and the sign of the L/R cross-correlation, at `Width` ∈ {0, 0.5, 1.0, 1.5, 2.0}. **Planted fault:** clamp w at 1.0 inside the node while the macro still reports 2.0 — the w = 1.5 and w = 2.0 points must go red and the w ≤ 1 points must stay green |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

1. **The comb minima carry S4's positive-α condition.** The seed gave
   f_s/2K, 3f_s/2K, 5f_s/2K … flatly; S4 gives those for positive α and
   0, f_s/K, 2f_s/K … for negative α. It matters to W2's planted fault, which
   flips one path's polarity — that moves the nulls as well as deepening them.

*(from §2)*

2. **S3 was cited for the mono-sum comb it does not claim.** S3's
   "interleaved comb-filters in the left and right channels" and its lopsided
   bass belong to a different construction — a delayed copy matrixed into the
   Side signal — and S3 says that one is the mono-*safe* one: "summing the
   left-right channels to mono completely removes the (fake) Side component,
   leaving only the original mono source — hence perfect mono compatibility",
   with the lopsidedness sitting between L and R rather than in the sum. The
   Haas topology's mono-sum comb is S4's arithmetic, which is what W2 already
   cited, so no trait moves.

*(from §3)*

**Trait-critic pass, 2026-09-06.** W6 was added because the Mid/Side
character had exactly one row of its own (W3) — W4 and W5 are shared wire
invariants — and vision §10.7's rule is that a character which fails its
traits must not be able to hide behind one that passes. Haas carries W1, W2,
W4, W5; Mid/Side carries W3, W6, W4, W5. W1's and W2's planted faults were
restated: W1's is the `audiodelays.Echo` floor already measured in A1, and
W2's polarity flip **moves** the minima as well as deepening them (S4's α < 0
case, the audit's own correction 1), so the measurement has to report null
positions for that fault to turn it red.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**0.02**, ESP32-S3 **0.05**. Lean patch expected: **no**. Per sample the Haas
character is one interpolated line read plus two Mixer gains; the Mid/Side
character is four multiply-adds. RAM is the Splitter's fixed 32 kB ring
(`audioif_splitter.h:20`) plus the delay line — 40 ms stereo is 7.7 kB.

*(from §3)*

Latency (vision §9a). **Zero samples on the dry path in both characters**, and
`latency_samples` = 0. The Haas character's delayed copy is the *effect*, on
one side of the stereo field, exactly as a chorus's mean delay is the effect
(vision §9a) — it is reported as the class's `Delay` macro and named in the
docstring in ms, and it is *not* added to `latency_samples`, because the dry
arrives at sample zero. Mid/Side is exactly zero everywhere. No option in
either character adds latency; there is no lookahead, no window and no
convolution. `tail_samples` is the delay line's length in the Haas character
(feedback is zero, so the line empties once) and zero in Mid/Side.

*(from §4)*

```
source ─ Splitter(taps=2) ┬─ tap 0 ─────────────────────────────► Mixer.voice[0]  dry, pan −w·k
                          └─ tap 1 ─ Filter(HP, Bass Mono) ─
                                     FeedbackDelay(feedback 0, mix 2) ► Mixer.voice[1]  wet, pan +w·k
```

*(from §4)*

Two node choices are decided by measurement rather than convenience. The delay
is `audioecho.FeedbackDelay`, **not** `audiodelays.Echo`: Echo floors its line
at the output buffer's length (`Echo.c:122-128`), so with `_core.pcm()`'s
2048-byte buffer a requested 14 ms is silently delivered as 21.33 ms — measured
(A1) — which fails W1 outright and quietly moves every null in W2. **That
floor lives in Echo's `freq_shift = False` branch only** (`Echo.c:116`), and
`freq_shift` **defaults to `True`** (`Echo.c:461`), where the line is always
the full `max_delay_ms` and the requested time is reached by scaling the read
*rate* instead (`Echo.c:118-120`) — re-measured at the default, Echo delivers
1, 5, 14, 20, 30 and 40 ms to within 0.02 ms at `buffer_size` 2048. So the
choice against Echo is not "Echo cannot reach 14 ms": it is that Echo reaches
it either by a floor that silently lies (`freq_shift=False`) or by a read-rate
trick that pitch-bends on every time change (`freq_shift=True`), and W1 wants
neither. *(Palette-verifier correction, 2026-09-06 — and it matters twice
over: W1's planted fault must pass `freq_shift=False` explicitly, or the
fault will not fire and the checker will be one that cannot fail.)*
`FeedbackDelay` clamps at one frame (`audioif_feedback_delay.c:82-83`) and
reads the line per sample with linear interpolation (`:212-228`), so W1's
one-sample tolerance is reachable and a fractional millisecond setting means
something. And the panning **runs backwards from the usual convention**:
`Mixer.c:337-341` attenuates the *right* channel for positive `panning` and
the left for negative, measured (A2) — a class that pans must be written to
that, and must also know that the Mixer's pan only ever attenuates one side
and never boosts the other, so for a stereo source it is a balance control,
not a panner.

*(from §4)*

**Mid/Side character** — buildable today, but not with all its traits at
once. *(Rewritten by the palette verifier, 2026-09-06; the seed said "not
buildable today … the palette has no cross-channel operation", and that is
**wrong**.)* One node does cross the channels: `audioecho.FeedbackDelay`'s
`input_pan` sends the *average* of the two inputs into one lane
(`audioif_feedback_delay.c:126-141`, applied at `:251-254`), and at
`input_pan = −1` with `feedback 0`, `mix 2` it renders exactly **M = (L+R)/2**
in the left channel and silence in the right — measured, error ≤ 0.5 LSB (A6).
`input_pan = +1` puts the same M in the right. Two of those, plus the source
itself, give the whole matrix without any subtraction at all, because
M + w·S = (1−w)·M + w·L and M − w·S = (1−w)·M + w·R:

*(from §4)*

```
source ─ Splitter(taps=3) ┬─ tap 0 ─ FeedbackDelay(input_pan −1, fb 0, mix 2) ─► Mixer.voice[0]  M left,  level 1−w
                          ├─ tap 1 ─ FeedbackDelay(input_pan +1, fb 0, mix 2) ─► Mixer.voice[1]  M right, level 1−w
                          └─ tap 2 ─────────────────────────────────────────────► Mixer.voice[2]  source,  level w
```

*(from §4)*

Built and rendered, it holds W6 to **0.005 dB** and W3 to **0.002 dB** (A6).
The cost is the reason §5's ask still stands: **`FeedbackDelay`'s delay
clamps at one frame minimum** (`audioif_feedback_delay.c:82-83`), so M arrives
one sample late. Leave the source path undelayed and W5's byte-identical wire
at `Width` 1.0 holds exactly — but the one-sample skew combs the mono sum, and
W3 misses by **2.01 dB at 10 kHz** and 0.47 dB at 5 kHz (it passes at 1 kHz).
Delay the source path through a third `FeedbackDelay` to match, and W3 and W6
come right — but the class now has one sample of latency at every width and
W5's wire is gone. There is no composition that holds W3, W5 and W6 together,
and the obvious escape does not work either: switching the source voice
between the delayed and undelayed tap as `Width` passes 1.0 would satisfy both
measurements, but `latency_samples` is one number for the class, so the class
would then be reporting a latency that is wrong at every width on one side of
the switch — a Tier 1 failure traded for a Tier 1 pass.
Two further limits belong on the record: `Mixer` voice level is clamped to
0…1 at render time (`Mixer.c:332`; a Python `level = −1.0` renders silence,
measured), so `w > 1` needs the M path inverted through `audiomath.Multiply`
against a constant −1 stream; and every other node in the palette is
lane-independent — `Splitter` copies both channels or duplicates a mono one
(`audioif_splitter.c:29-31`), `Mixer` scales each channel independently
(`Mixer.c:343-347`), `Multiply` is element-wise (`audioif_multiply.c:32-45`),
and `audioif_feedback_delay.c` is the only DSP kernel in the tree that indexes
the opposite channel (A5 carries the grep and what else it turns up).

*(from §4)*

**Mono.** Stated here, per Tier 1, and settled by reading the contract rather
than left open: `create()` calls `configure(sample_rate, source_channels)`
(`_core.py:202`), so every node the class builds takes the *source's* channel
count, and `_finish_component` raises if the output's channel count differs
from the source's (`_core.py:218-223`). A mono-in/stereo-out widener therefore
**cannot be built under this contract at all** — not as a design choice, as a
fact of the factory. So a mono source gets **a wire** in both characters,
byte-identical, which is one of the two answers vision §3 allows; the
docstring says it in one line, and the class does not raise. (Haas widening of
a mono source, which is what a player would want from a pedal, is a chain
question — put a `StereoWidener` after something that has already made the
signal stereo — and the docstring says that too.)

*(from §4)*

Python computes at construction: delay frames from ms, the `Bass Mono`
biquad's mode/corner/Q, and the two pan values from `Width`. On a macro move
it writes the node's `delay_ms`, the biquad's `frequency`, or two voice levels
and pans. It never computes a coefficient set: `synthio.Biquad` takes only
`(mode, frequency, Q, A)` and the RBJ coefficients are derived in C
(`audioif_biquad.c:70-125`) — *palette-verifier correction, 2026-09-06, the
seed said "the biquad coefficients".* Nothing per
sample, no table. `capabilities` = `()` (D10) — a width control has no tempo.

*(from §5)*

- **Traits it unblocks:** **W3**, **W6** and **W5's Mid/Side half** — not
  because W3 and W6 are unreachable one at a time, but because no composition
  reaches them *and* keeps W5. Without the node the class has one character,
  and that character is the one that breaks in mono.

*(from §5)*

- **What the palette does instead, and why it fails the trait set.** Two
  things, and the second is the one that decides it.
  1. The Haas character alone cannot stand in: its mono sum is a comb by
     construction (W2, measured at A4: nulls at 70.3 and 164.1 Hz, −10.6 and
     −7.9 dB, exactly where 1/(2τ)·(2k+1) puts them for the τ delivered),
     where W3 asks for a mono sum flat within 0.05 dB across width.
  2. A real mid/side composition **does** exist —
     `Splitter(3) → two FeedbackDelay(input_pan ∓1) + the source → Mixer`,
     §4 — and it was built and rendered rather than argued about. It reaches
     W6 to 0.005 dB and W3 to 0.002 dB, **but only when the source path is
     delayed one sample to match the mid path**, because `FeedbackDelay`
     cannot deliver less than one frame (`audioif_feedback_delay.c:82-83`).
     Delayed, the class carries one sample of latency at every width and W5's
     byte-identical wire at `Width` 1.0 is gone. Undelayed, W5 holds byte for
     byte and W3 fails by **2.01 dB at 10 kHz**, 40× its tolerance. Measured
     both ways, A6.

*(from §5)*

- **The refutation, restated so it can actually fail.** The old bar — "name a
  composition that produces L − R" — is met (A6), and is withdrawn. The bar
  is now: **name a composition that holds W3, W5 and W6 simultaneously, on
  one topology, at one `latency_samples`.** None was found, and the reason is
  structural rather than incidental: every cross-channel path in the palette
  runs through `audioecho.FeedbackDelay`, and every `FeedbackDelay` path is
  delayed at least one frame.

*(from §5)*

- **Design sketch.** `audioroute.MidSide(source, width=1.0)`, per frame in
  Q15: M = (L + R) >> 1, S = (L − R) >> 1, out L = M + w·S, R = M − w·S, with
  `w` clamped 0…2 and the identity exact at w = 1 so W5's wire holds byte for
  byte. Zero latency, no state, four multiply-adds and two shifts per frame.
  A second option, `side_highpass_hz`, would fold S3's bass-mono advice into
  the node; the recommendation is **not** to — the class already has a biquad
  for that and a node with an opinion about bass is harder to reuse.

*(from §5)*

- **Where it lives.** `audioroute`, beside `Splitter`: it is routing, not
  arithmetic, and `audioroute` is already audioif's own (upstream-diff,
  "`audiodynamics` and `audioroute`: not CircuitPython ports at all"). Additive
  under D1; nothing ported is touched.

*(from §5)*

- **Priority, and what to do if it is cut.** Lower than the Octaver's
  `SubOctave` ask in the same unit: that one has no composed substitute at
  all, this one has an imperfect one. If Gate 0 cuts `MidSide`, the Mid/Side
  character does **not** have to be dropped — build it as §4's composition
  with the source path delayed to match, ship it with `latency_samples = 1`
  (0.021 ms at 48 kHz) and restate W5 for that character as "byte-identical
  after a one-sample alignment", with the reason in the docstring. That
  substitute costs four extra nodes and 32 kB of Splitter ring
  (`audioif_splitter.h:29`) where the node costs four multiply-adds per frame
  and no RAM, which is the honest trade for Gate 0 to weigh.

*(from §7)*

- `pitch.py:138` — `self.mixer.voice[1].level = 0.8` is a **fixed literal
  independent of `width`**, so at `width=0` the delayed copy is still at 0.8
  and the class is not a wire. Measured: at width 0 the output RMS is 8004
  against the source's 8484, and both channels carry the comb (A3). A widener
  at zero width that changes the sound is the plainest kind of broken.

*(from §7)*

- `pitch.py:129-131` — `audiodelays.Echo` floors its line at the output
  buffer's length (`Echo.c:122-128`), so the class's documented 14 ms default
  is delivered as **21.33 ms**. Measured: click at frame 64, delayed copy at
  1088 — 1024 frames (A1). Every number in the class's own docstring is
  therefore wrong by 52 %, and nothing in the class could have noticed.

*(from §7)*

- `pitch.py:136`, `:139` — pan constants `-0.3 * width` and `0.9 * width` are
  asymmetric, undocumented, and (with the Mixer's inverted pan law, A2) put
  the dry on the **right** and the delayed copy on the **left**, where the
  docstring at `:116-117` says the dry is centred. Three separate things
  disagree: the code, the comment, and the convention.

*(from §7)*

- `pitch.py:115-117` — no statement anywhere of what a mono source gets,
  though this is the one class in the family that is stereo by definition and
  vision §3's Tier 1 requires the statement.
