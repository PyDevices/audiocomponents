# Effects Dossier — `ConvolutionReverb` (no standout — design grade)

**Class:** `lib/audioeffects/reverb.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Time, roadmap Phase 5
**Standout:** **none**, per vision §4.2 ("grade *design*; surface only") —
**confirmed** (§2). A convolver has no historical circuit to be informed by:
convolution with a measured impulse response *is* the room, and every
commercial unit that does it is doing this arithmetic. The traits are the
textbook properties of the operation and the measured behaviour of the node
that already exists.
**Grade:** **design** — graded on Tier 1 and Tier 3, plus the six design
traits of §3, each of which has now been measured against the shipped node
(D1 and D6 in the trait critic pass of 2026-09-07, App. A and App. F).
**Portability tier:** needs audioif-own nodes (`audioconvolve.Convolver`).
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

There is no circuit; there is an algorithm, and its shape is the whole
product. `audioconvolve.Convolver` is **uniform-partitioned overlap-save**:
the impulse is cut into 256-tap partitions transformed once at load time,
and each block the input's transform is pushed into a frequency-delay line
and multiplied bin by bin against them (`audioif_convolve.h:11-18`, `:80-94`).
Two consequences are the whole character. **A block cannot be transformed
until it is complete**, so the output trails the input by exactly one
partition — 256 frames, 5.33 ms at 48 kHz (`:20-26`) — and the only way out
is Gardner's hybrid of direct-form taps ahead of the blocks (S1), which the
node deliberately does not do. And **cost and memory grow linearly with
length**: 257 complex floats per partition, one frequency-delay line per
audio channel, one stored impulse per impulse channel (`:28-35`). With
nothing loaded the node is a **bypass, not silence** (`:112-115`), so a chain
built before its impulse arrives does not drift. Where no measured impulse
exists it synthesizes one — xorshift noise under an exponential giving −60 dB
over `decay_seconds`, a one-pole `damping_hz` roll-off, `predelay_ms` of
leading silence, a `diffusion_ms` fade-in, and a **two-pass normalisation to
unit energy** (`:138-151`; `audioif_convolve.c:168-253`, the two passes and
their reason at `:197-209`) — all from series, never libm, so a seed is the
same room on every interpreter. `mix` follows
`audiofreeverb`'s convention: 0–1, dry at unity until halfway (`:74-77`).

## 2. Sources and license calls

Three published sources, each re-fetched from this machine during the licence
and citation audit of 2026-09-06 (all HTTP 200): the Gardner scan carries no
extractable text and was rendered with `pypdfium2` and read as an image, the
Russo thesis and the Dattorro scan were extracted with `pypdf`. Everything
else in this seed is a repository fact with a line number, or a measurement
taken this session (App. A). Where no licence text exists the call is the
vision §5 default: **unverified is treated as copyleft** — read, never ported.

| # | Source | What it gave | Licence as read | Reached |
|---|---|---|---|---|
| S1 | [Gardner, *Efficient Convolution without Input–Output Delay* … (App. S1) | the abstract's own statement of the trade … (App. S1) | no rights statement anywhere on the scan's p. … (App. S1) | HTTP 200; p. 1 rendered at scale 3 in two halves and read — title, author, affiliation, abstract, the `*` footnote and the running foot "J. Audio Eng. Soc., Vol. 43, No. 3, 1995 March 127" |
| S2 | [Russo, *Physical Modeling and Optimisation of a EMT 140 Plate Reverb* … (App. S2) | the T60 definition D5 is measured against … (App. S2) | p. 2 carries the bare line "Copyright © … (App. S2) | HTTP 200; text extracted, copyright line read on p. 2, the Sabine sentence read in §1.2 "Basics of Room Reverberation" |
| S3 | [Dattorro, *Effect Design, Part 1*, JAES 45(9) … (App. S3) | the contrast this class exists for: an algorithmic … (App. S3) | no rights statement in the PDF … (App. S3) | HTTP 200; text extracted |

Repository facts, cited by line and not by URL: `audioif/src/shared/audioif_convolve.h`
and `.c`, `audioif/src/audioconvolve/Convolver.c`, and
`audioif/docs/upstream-diff.md` §"`audioconvolve`: audioif's own", which
records the design decisions and the cost table this seed re-derives.

**Audit, second pass — independent, 2026-09-06.** All three URLs re-fetched
from this machine by a second agent, the two extractable PDFs re-extracted,
the Gardner scan re-rendered and re-read, both host pages re-read for their
footers, and every repository line number in §§1 and 3 re-opened. **Five
corrections:**

1. **D5 cited the wrong section of S2.** Sabine's T60 definition is in …  *(argument in full: App. R)*
2. **S2's licence call overstated what the page says** — "all rights …  *(argument in full: App. R)*
3. **§1's `audioif_convolve.c:168-232` stopped short of the function**, …  *(argument in full: App. R)*
4. **D6 cited two files without a line in either.** It now names the code
   and the doc line that state the unit-energy invariant.
5. **S1's row now carries the page range** the AES e-library entry gives
   (127–136) and the host page's footer as it actually reads.

Everything else in §§1–3 was re-read against its source and stands; what was
checked — the quotations, and every node line number §§1 and 3 rest on — is
in **App. E**.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — design traits

A design grade states the textbook property as its trait (vision §4.1). Each
has been measured against the shipped node — D2–D5 on 2026-09-06, D1 and D6
in the trait critic pass of 2026-09-07, where D5 was also re-measured by two
estimators. The numbers are in App. A, the planted faults in App. C.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| D1 | **It is exactly convolution, to within one output LSB.** With an impulse loaded and the wet reference inside full scale, the output equals the double-precision direct sum ∑ h[k]·x[n−k−256] — h being the loaded int16 taps × 1/32768, the node's own load scale (`audioif_convolve.c:149`) — with a **peak error ≤ 1 LSB (−90.3 dBFS)** over the probe set. Levels are part of the trait: above full scale the int16 output saturates and the comparison means nothing. | the definition of an LTI filter … (App. D1) | high — measured … (App. D1) | Any peak error above 1 LSB on probe material whose direct-form reference stays inside ±32767 | M1 |
| D2 | **`seconds` is an allocation with a hard ceiling, and the class names it.** The ceiling is **512 partitions × 256 taps = 131 072 taps at every rate** (`audioif_convolve.h:58-60`) — 2.73 s at 48 kHz, 2.97 s at 44.1 kHz, 5.94 s at 22.05 kHz. Over it, construction raises before anything renders, and the message names the class and the ceiling in seconds at the running rate. | `audioif_convolve.h:58-60` … (App. D2) | high | A silent truncation, a clamp, or an error whose text does not name both the class and the ceiling in seconds at the running rate | M2 |
| D3 | **Latency is one partition when an impulse is loaded and zero when none is, and `latency_samples` follows the loaded state rather than the node's constant.** 256 frames at every rate — 5.33 ms at 48 kHz, 5.80 at 44.1, 11.61 at 22.05. Re-measured this run: loaded, a click at frame 0 first appears at frame **256**; unloaded, `max abs(out − in) = 0` over 1 s while `node.latency` still reports 256. | `audioif_convolve.h:20-26`, `:112-115` … (App. D3) | high — measured | A reported `latency_samples` that does not change when an impulse is loaded or cleared, or a measured first arrival other than 256 (loaded) or 0 (unloaded) at any of the three rates | M3 |
| D4 | **`mix` at zero is the source delayed by exactly `latency_samples`, byte for byte.** Re-measured this run: over 1 s of 440 Hz stereo, `out[i+512] == in[i]` for every sample and `out[0:512]` is all zero. The check is a byte digest and never a tolerance — a 1-LSB dry trim is a failure, not a rounding. | the mix law, `audioif_convolve.h:74-77` … (App. D4) | high — measured | Any altered sample at `mix = 0`, or any non-zero sample in the first 256 frames | M4 |
| D5 | **The synthesized room's T60 is the requested decay within 2 %, and the tail reaches exact zero.** T60 from a **least-squares slope fit of the log-envelope over −5…−35 dB**, extrapolated to −60 dB — never the first window that crosses −60 dB. Measured this run at 0.5 / 1.0 / 2.0 s: **+0.0 / +0.4 / +0.3 %** by the fit, and Schroeder backward integration over the same region agrees within 0.5 %; the same renders read **+8 / +6 / +2 %** by a −60 dB crossing on 20 ms windows, which is why the estimator is in the trait. A 1.0 s room is bit-zero beyond 2.5 s. | `audioif_convolve.h:138-143` … (App. D5) | high — measured by … (App. D5) | A fitted T60 more than 2 % from the request at any of the three, or any non-zero sample after the impulse has run out | M5 |
| D6 | **The synthesized room is unit-energy, so Decay is a time control and not a level control — and so is Damping.** Normalisation is the second pass over the *fully shaped* impulse: envelope, damping, predelay and diffusion all precede it (`audioif_convolve.c:211-248`), so the wet level is independent of every synthesis argument. Criterion: across the Decay macro's full span and across Damping, the wet RMS of the kit's held broadband probe varies by **≤ 0.5 dB**. Measured this run on the node over seven configurations (decay 0.25–2.0 s, damping 0 / 2 / 8 kHz): a **0.041 dB** spread, and noise returns at the level it went in (App. A). | `audioif_convolve.c:197-209` and `:211-248` … (App. D6) | high — measured … (App. D6) | A wet level that tracks decay time or damping by more than 0.5 dB: a longer or a darker room that is also a quieter one | M6 |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node, unchanged.** `audioconvolve.Convolver` already *is* this class;
the rebuild is a surface, an allocation contract and an honest report, not new
DSP. Python at construction: pick `partitions` from `seconds` and the running
rate, refuse over the ceiling with a message naming the class and the ceiling
in seconds (D2), build the node, then `load()` or `synthesize()`. On a macro
move: a scalar for `Mix` and `Level`, one re-synthesis for everything else —
and since re-synthesis is the expensive thing here, a patch change suppresses
the per-macro rebuild and does exactly one at the end (the current class gets
this right, `reverb.py:163-176`; it is the one thing carried forward).

**Portability tier: audioif.** On a stock CircuitPython board the module
imports and construction raises a clear `ImportError` — the class already has
the right shape here (`reverb.py:18-21`, `:125-128`) and it is kept.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None for Phase 1.** The class composes on a node that exists.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Macro | Mode | Range | What it moves |
|---|---|---|---|---|
| 0 | `Decay` | UNIPOLAR | 0.05–1.0 × `seconds` | the synthesized room's T60 (D5) |
| 1 | `Damping` | UNIPOLAR | 500 Hz–16 kHz log, Nyquist-clamped | the tail's HF roll-off as it decays |
| 2 | `Predelay` | UNIPOLAR | 0–200 ms (the node's own clamp) | leading silence before the room |
| 3 | `Diffusion` | UNIPOLAR | 0–500 ms | the fade-in that stops a synthetic room reading as a burst |
| 4 | `Room` | UNIPOLAR | seed 1–64, stepped | which room of this size — two seeds are two halls |
| 5 | `IR Gain` | UNIPOLAR | −24…+12 dB | the loaded impulse's level (measured mode) |
| 6 | `IR Start` | UNIPOLAR | 0–200 ms into the impulse | trimming a capture's pre-roll (measured mode) |
| 7 | `Width` | UNIPOLAR | 0–1 over the two IR channels | mono-summing a true-stereo room |
| 8 | `Tone` | BIPOLAR | ±12 dB wet tilt | post-convolution shaping, both modes |
| 9 | `Mix` | UNIPOLAR | 0–1; 0 is the delayed wire (D4) | dry/wet |
| 10 | `Level` | UNIPOLAR | −12…+6 dB | output trim |

Eleven of sixteen; 0–4 are inert and hidden in measured mode, 5–7 in
synthesized mode (§4). No characters — a convolver's character is its
impulse. `capabilities`: **`()`** — nothing here reads a beat, and a
tempo-synced predelay on a class that already carries 5.33 ms of latency
would be a trap rather than a feature.

Patches (all synthesized, so they ship with no assets): `Natural Room` ·
`Small Room` · `Concert Hall` · `Dark Chamber` · `Bright Plate` · `Cathedral`
· `Gated Slap` · `Short Room — lean` (0.25 s allocation, the S3 default).
Settings in App. D.

## 7. Defects in the current class the rebuild must not repeat

- **It reports zero latency while carrying 256 frames of it.** No
  `LATENCY_SAMPLES`, so `_core.py:245-248` returns 0; measured this run,
  `r.latency_samples` is 0 while `r.node.latency` is 256 and the first
  non-zero output frame is 256. The docstring admits the delay
  (`reverb.py:87-88`) — which makes the report a documented lie rather than an
  oversight. This is D3.
- **`tail_samples` is `None`** (`_core.py:250-253`) against an allocation the
  class knows exactly: `self._taps` (`reverb.py:132`).
- **The allocation ceiling surfaces as someone else's error.** Measured:
  `ConvolutionReverb(source, seconds=3.0)` raises the node's bare
  `ValueError: impulse is too long` — no class name, no mention that 2.73 s is
  the ceiling at 48 kHz, no hint that it is rate-dependent (`reverb.py:132-135`).
- **Four knobs are connected to nothing in measured mode.** `MACRO_LABELS`
  always advertises Decay, Damping, Predelay and Diffusion
  (`reverb.py:96`), while `_rebuild` returns immediately when `self.measured`
  (`:179-180`). The docstring explains it (`:139-141`); a host cannot read a
  docstring.
- **A single knob move re-synthesizes the whole room**: `_apply_macro` calls
  `_rebuild` for macros 0–3 (`reverb.py:186-190`) — at `seconds=1.0` that is
  188 partitions regenerated twice and re-transformed. Correct and expensive;
  the rebuild keeps the patch-level suppression (`:163-176`) and rate-limits.
- **`seconds` and `decay` interact confusingly**: `decay_seconds` is
  `macro(0) * seconds` (`:155-158`), so one knob position means different times
  on two instances. The rebuild reports both and names the allocation first.

## 8. Open questions

1. **Cost on the boards decides the default `seconds`.** Tier 3's budget is
   derived from the node's published MFLOPS, not measured on a P4 or an S3.
   *Settles:* Phase 1's cost runner; the `Short Room — lean` patch's
   allocation is set from that table, and the shipped default follows the S3.
2. **Where a measured impulse comes from.** Nothing ships one today, and no
   IR library was hunted this run (§2). A licence-clean set — recorded per
   file, with the capture chain stated, under the vision §5 gate — is a Phase
   5 acquisition, and it may end as "none ships; the class loads yours". Until
   then every patch is synthesized. *Settles:* the implementation session,
   with the licence call recorded per file in the evidence pack.
3. **`IR Start` and partial loads.** Trimming a capture's pre-roll is a load-
   time operation, and the node loads from frame 0 (`audioif_convolve.h:134-136`).
   Whether the class slices in Python before `load()` — allocating — or the ask
   grows a `start` argument, is a Phase 5 question. It is not a node ask
   because no trait needs it.
4. **Whether `Width` belongs at all.** Mono-summing a true-stereo room is a
   load-time recombination, not a runtime knob, so it may become a constructor
   option. *Settles:* the implementation session.
5. **The deferred Gardner ask** (§5) is reopened only by a Phase 1 round-trip
   measurement under 10 ms.

---


## Appendix

### A. Measurements taken this session

CPython, `audiocomponents/.venv`, 48 kHz stereo, `audioconvolve.FRAMES = 256`.

*Re-measured 2026-09-07 by the palette verifier, independently of the run that
first wrote them, and agreeing: unloaded `max|out − in| = 0` with `.latency`
still 256; loaded, a click first appears at frame **256** (value 19999 from an
input of 20000); at `mix = 0`, `out[i+512] == in[i]` for every sample with the
first 512 zero; `max_taps = 512·256 + 1` raises `ValueError: impulse is too
long` while 512·256 = 131 072 taps constructs; and D1's direct-sum comparison
against a 512-tap random impulse reads **0.500 LSB** at a 3000-peak probe and
**0.501 LSB** at 10 000, which is the same half-LSB rounding the first run
found.*

- **Allocation.** `Convolver(max_taps=48000, ir_channels=2)` reports
  `taps 48128` (188 partitions × 256) and `latency 256`.
  `max_taps=144000` (3.0 s) raises `ValueError: impulse is too long` —
  512 partitions is the ceiling (`audioif_convolve.h:58-60`), i.e. 131 072
  taps, **2.73 s at 48 kHz**, 2.97 s at 44.1 kHz, 5.94 s at 22.05 kHz.
- **Latency, loaded.** With a 1.0 s synthesized room, an impulse at frame 0
  gives its first non-zero output at **interleaved index 512 = frame 256**.
- **Latency, unloaded.** A fresh `Convolver` with nothing loaded, 1 s of
  440 Hz stereo: `max |out − in| = 0` over the whole render — a true wire with
  no delay — while `.latency` still reports 256. The class must report the
  loaded state, not the node's constant (D3, §7).
- **Wire at mix 0.** With a room loaded and `mix = 0`: comparing
  `out[i + 512]` with `in[i]` gives **max difference 0** over 1 s, and
  `out[0:512]` is all zero. Byte-identical, delayed by exactly the partition.
- **Synthesized T60** (impulse, 20 ms RMS windows, −60 dB from peak), damping
  off: request 0.5 s → **0.52 s**; 1.0 s → **0.98 s**; 2.0 s → **1.92 s**.
  *(These came from the first window to cross −60 dB, which is not the
  estimator D5 and M5 name. The 2026-09-07 slope fit of the same rooms reads
  0.500 / 1.004 / 2.006 s and the crossing method on that run's renders read
  0.540 / 1.060 / 2.040 s — the spread between the two methods is what set
  D5's tolerance. Kept for the record, superseded below.)*
- **Tail to zero.** A 1.0 s room, 3 s render: `max |out|` beyond 2.5 s is
  **0** — bit-zero, no held DC.
- **The current class.** `ConvolutionReverb(source, seconds=1.0)` reports
  `latency_samples 0`, `tail_samples None`, `seconds 1.0`,
  `decay_seconds 1.0`, while `node.latency` is 256 and `node.taps` is 48128.
  `seconds=3.0` raises the node's bare `ValueError: impulse is too long`.

**Trait critic pass, 2026-09-07 — measurements taken this run.** CPython,
`audiocomponents/.venv`, 48 kHz, against `audioconvolve.Convolver` directly
(the class is not rebuilt yet). Scripts were throwaway; every number below is
reproducible from the parameters stated.

- **D1, exactness against a direct-form reference.** A 1 024-tap impulse of
  decaying int16 noise (seed 7, 3 000 × e^(−i/300) × uniform(−1,1)), loaded
  mono at `gain=1.0`; probe a 997 Hz sine at peak **2 000 / 8 000 / 30 000**
  LSB, `mix=1.0`; reference `numpy.convolve` in float64 of the same int16
  probe against the taps × 1/32768, delayed 256 frames; compared over frames
  256 … 10 976. **Peak error 0.500 / 0.502 / 0.508 LSB = −96.33 / −96.30 /
  −96.19 dBFS**; RMS error 0.29 LSB. Half an LSB is rounding, so the node is
  exact convolution and D1's 1 LSB bar has a factor of two in hand. At a
  fourth level whose reference peaked at **34 751 LSB** — outside int16 —
  the peak "error" was **1 983 LSB**: saturation, not a defect, which is why
  D1 and M1 both state the level rule.
- **D3 and D4, re-measured.** Loaded (1.0 s synthesized room, seed 4): a
  stereo click at frame 0 first appears at interleaved index 512 = **frame
  256**. Unloaded: `max abs(out − in) = 0` over 1 s of 440 Hz stereo while
  `.latency` still reports 256 and `.taps` reports 0. At `mix = 0` with the
  room loaded: `out[0:512]` all zero and `max abs(out[i+512] − in[i]) = 0`
  over 1 s. All three reproduce the first run's numbers exactly.
- **D5, T60 by three estimators on the same renders.** Synthesized rooms at
  decay 0.5 / 1.0 / 2.0 s, damping off, seed 4, a 30 000-LSB stereo click,
  left channel: **least-squares slope fit of the log-envelope over −5…−35 dB
  → 0.500 / 1.004 / 2.006 s (+0.0 / +0.4 / +0.3 %)**; **Schroeder backward
  integration over the same region → 0.499 / 1.005 / 2.004 s (−0.2 / +0.5 /
  +0.2 %)**; **first 20 ms window crossing −60 dB → 0.540 / 1.060 / 2.040 s
  (+8.0 / +6.0 / +2.0 %)**. The two fits agree with each other and with the
  request; the crossing does not, and it is the method the first run's
  0.52 / 0.98 / 1.92 came from. D5's tolerance is 2 % *because* the estimator
  is now named — with the estimator left open, 5 % was a number either
  method could be steered through. Tail floor: `max abs(out)` beyond
  decay + 1.5 s is **0**.
- **D6, unit energy across decay and damping.** 2 s of white noise at
  ≈8 000 LSB RMS, stereo, `mix=1.0`, seed 4, first 0.5 s of each render
  discarded. Wet RMS: decay 0.25 / 0.5 / 1.0 / 2.0 s at damping off →
  **8 029.5 / 8 035.8 / 8 028.3 / 8 001.6**; decay 1.0 s at damping 0 / 2 /
  8 kHz → **8 028.3 / 8 039.9 / 8 033.2**; decay 0.25 s at 2 kHz → 8 017.4;
  decay 2.0 s at 8 kHz → 8 006.8. Spread over all seven: **0.041 dB**, and
  the wet comes back within 0.02 dB of the level that went in. The code
  reason is that normalisation is the *second* pass over the already-shaped
  impulse (`audioif_convolve.c:211-248`), so damping, predelay and diffusion
  are inside the energy it normalises — which is why D6 now claims Damping
  as well as Decay.

### B. Cost arithmetic

From `audioif/docs/upstream-diff.md` §"What it costs": 1024 taps (4
partitions) ≈ 3 MFLOPS and ~25 KB; one stereo second (188 partitions)
≈ 150 MFLOPS and ~1.5 MB. Both give **≈0.75 MFLOPS and ≈2 KB per partition**
(per stored IR channel; the frequency-delay line is per audio channel).

| Impulse at 48 kHz | Taps | Partitions | ≈ Memory / IR channel | ≈ Arithmetic |
|---|---|---|---|---|
| 0.25 s | 12 000 | 47 | 94 KB | 35 MFLOPS |
| 0.50 s | 24 000 | 94 | 189 KB | 70 MFLOPS |
| 1.00 s | 48 000 | 188 | 377 KB | 141 MFLOPS |
| 2.73 s (ceiling) | 131 040 | 512 | 1028 KB | 384 MFLOPS |

The S3's share in Tier 3 is what picks the default; the table is what makes
that a decision rather than a guess, and Phase 1's cost runner replaces the
MFLOPS column with measured blocks per second on both boards.

### C. Measurements, and the planted fault each must catch

All take the sample rate as a parameter and record it; all run at 48 kHz and
44.1 kHz, Tier 1 additionally at 22.05 kHz.

- **M1 — direct-form reference.** Convolve the probe with the loaded impulse
  in double precision on CPython (NumPy, in the kit, never on a board), delay
  by 256 frames, compare peak error against the **1 LSB** bar. The probe
  levels are part of the measurement: M1 asserts first that the reference
  itself stays inside ±32767, because above full scale the int16 output
  saturates and the comparison stops meaning anything — measured this run, a
  probe whose reference peaked at 34 751 LSB showed 1 983 LSB of "error" that
  was entirely clipping (App. A). *Planted fault:* transpose two partitions in
  the frequency-delay line — the error must exceed 1 LSB while every Tier 1
  test still passes, which is the point of having M1.
- **M2 — allocation contract.** Construct at the ceiling, one partition over,
  and at three rates; assert the message names the class and the ceiling.
  *Planted fault:* clamp silently instead of raising — M2 must go red.
- **M3 — click latency.** A click through the class against the same click
  through a wire, loaded and unloaded, at each rate. *Planted fault:* declare
  `LATENCY_SAMPLES = 0` while an impulse is loaded — this is the shipped
  class's actual behaviour (§7), so M3's first run against the *old* code is
  itself the demonstration that the measurement can fail.
- **M4 — delayed-wire byte check.** FNV digest of the output from frame 256
  against the source's from frame 0, at `mix = 0`. *Planted fault:* set the
  dry gain to `32767/32768` — one LSB — and M4 must go red; a tolerance-based
  check would not.
- **M5 — T60 and floor.** T60 from a **least-squares slope fit of the
  log-envelope over −5…−35 dB**, extrapolated to −60 dB — the shape
  `tools/measure_hits.py:80-90` already uses — and never the first window that
  crosses −60 dB, which read 2–8 % high on the same renders this run (App. A);
  plus a bit-exact zero test on the last second. *Planted fault:* add a 1-LSB
  DC offset to the synthesized tail; the floor test must catch what the decay
  fit cannot. *Second planted fault, for the estimator itself:* run M5 with
  the crossing method on a room whose fitted T60 is correct — it must not be
  able to pass D5's 2 %, which is how the kit records that the estimator was
  chosen and not assumed.
- **M6 — energy versus decay and damping.** Wet RMS of the kit's **held
  instrument chord** (the broadband held probe the kit spec already carries;
  this run used 2 s of white noise as a stand-in, App. A) across the Decay
  macro and at three Damping settings. *Planted fault:* skip the second
  normalisation pass — the level must track the decay time and D6 go red.

A **control** runs with every one of them: the same probe through a wire,
which must *pass* the Tier 1 tests and *fail* M1, M5 and M6, so the suite is
not one that only ever fails.

### D. Patch settings

Macro order is §6's; all synthesized, so no patch needs an asset. The
implementation session converts to the 0–127 integers `PATCHES` stores.

| Patch | Decay | Damping | Predelay | Diffusion | Room | Tone | Mix |
|---|---|---|---|---|---|---|---|
| Natural Room | 1.00 × | 6 kHz | 0 ms | 0 ms | 1 | 0 | 0.30 |
| Small Room | 0.20 × | 4 kHz | 4 ms | 12 ms | 3 | 0 | 0.35 |
| Concert Hall | 1.00 × | 7 kHz | 30 ms | 45 ms | 7 | 0 | 0.40 |
| Dark Chamber | 0.60 × | 2 kHz | 12 ms | 30 ms | 11 | −4 | 0.35 |
| Bright Plate | 0.75 × | 14 kHz | 0 ms | 8 ms | 5 | +4 | 0.45 |
| Cathedral | 1.00 × | 5 kHz | 50 ms | 70 ms | 13 | 0 | 0.50 |
| Gated Slap | 0.14 × | 9 kHz | 20 ms | 0 ms | 2 | +2 | 0.60 |
| Short Room — lean | 1.00 × | 6 kHz | 4 ms | 10 ms | 1 | 0 | 0.30 |

`Short Room — lean` is the vision §7.2 escape valve: it is the same patch on a
0.25 s **allocation**, which is the only thing that actually reduces this
class's cost. It is a separate patch and never a change to `Natural Room`.

### E. The second audit pass, 2026-09-06 — what was re-reached

**Re-verified and standing:** S1's abstract, verbatim and complete, and its
`*` footnote naming the 97th Convention, San Francisco, 1994 November 10–13;
S1's zero extractable text (which is why it is rendered, not extracted); S3's
§1.1 sentence "Fig. 1 shows one particular network for producing
reverberation"; and the node facts §§1 and 3 rest on —
`audioif_convolve.h:11-18` (uniform-partitioned overlap-save),
`:20-26` ("roughly triples the code… only when monitoring a live player.
Deliberately not done"), `:28-35` (2 KB per partition, one frequency-delay
line per audio channel, one stored impulse per impulse channel),
`:51` (`AUDIOIF_CONVOLVE_FRAMES 256`, hence 257 bins), `:58-60`
(`MAX_PARTITIONS 512`, "2.7 seconds at 48 kHz"), `:74-77` (the mix law),
`:112-115` ("a bypass rather than silence"), `:124-129` (the mono/stereo
impulse rule), `:134-136` (`load_s16`, no start offset),
`:138-151` (the synthesis arguments and the never-libm determinism), and the
two-pass unit-energy normalisation at `audioif_convolve.c:197-209` and
`upstream-diff.md:1360`. Tier 3's and App. B's arithmetic reproduce from
`upstream-diff.md:1383-1385` (≈0.75 MFLOPS per partition) and from the
header's own 2 KB: 47 / 94 / 188 / 512 partitions, 94 / 189 / 377 / 1028 KB,
and 131 072 taps = 2.73 s at 48 kHz, 2.97 s at 44.1 kHz, 5.94 s at
22.05 kHz.

### F. The trait critic pass, 2026-09-07 — what changed and why

Six rows in, six out. No source was re-fetched and none was added: everything
below is either a tightening of wording, a repository line this run re-opened
with `grep -n`, or a measurement this run took against the shipped node
(App. A).

| Row | Was | Is | Why |
|---|---|---|---|
| D1 | "within −80 dBFS peak error", confidence **high**, no measurement anywhere in the seed | ≤1 LSB (−90.3 dBFS), measured at three levels (0.500 / 0.502 / 0.508 LSB), with the reference definition and the full-scale rule in the row | the seed's own §3 preamble said every trait was measured against the node; D1 was not, and its threshold was 10 dB looser than the node's own rounding. The level rule is not pedantry: at a reference peak of 34 751 LSB the same probe reads 1 983 LSB of error, all of it saturation |
| D2 | ceiling stated once, in seconds at 48 kHz | ceiling stated as **131 072 taps at every rate** with the three second-figures derived, and the raise located at `Convolver.c:32` | "2.73 s" is a rate-dependent restatement of a rate-independent ceiling, and a class that reports the seconds without the taps cannot be checked at 22.05 kHz |
| D3 | unchanged in substance | re-measured this run, both states, and the three rates spelled out | — |
| D4 | unchanged in substance | re-measured this run, with "byte digest, never a tolerance" moved into the row | a 1-LSB dry trim is the failure this trait exists to catch, and a tolerance-based check would pass it |
| D5 | "within 5 %", estimator unnamed; App. A's numbers came from a −60 dB crossing while M5 named `measure_hits.py`'s slope fit | within **2 %**, estimator named in the row (slope fit over −5…−35 dB), measured 0.0 / +0.4 / +0.3 % by the fit and −0.2 / +0.5 / +0.2 % by Schroeder integration, with the crossing method's +8 / +6 / +2 % recorded beside them | the row and its measurement disagreed about how T60 is computed, and the two methods differ by more than the whole tolerance. A trait whose verdict depends on which estimator the runner reaches for is not falsifiable — this is the "what does the statistic cancel" failure from `workspace-craft.md`, in the estimator rather than in the sum |
| D6 | "less than 1 dB" over a **pink** probe the kit's list does not contain; confidence **medium — not yet measured across the decay range** | ≤0.5 dB over the kit's held broadband probe, across Decay **and Damping**, measured over seven configurations at a 0.041 dB spread; confidence high | a measurement that names a probe the kit does not carry cannot be run as written. And the node normalises *after* damping (`audioif_convolve.c:211-248`), so the trait was claiming less than the code guarantees |

Not changed, and worth saying: the six rows are a **design** grade's rows, so
vision §4.1's "graded on Tier 1 and Tier 3 alone" still governs — these are
the textbook properties of the operation, and they are here because a
convolver that quietly stops being a convolver is the failure this class can
actually have.

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

*Wire note.* "`mix` at zero is a wire" is met here **in time as well as in
level**, and the two are different claims: measured this run, at `mix = 0`
with an impulse loaded the output is the input **delayed by exactly 256
frames and byte-identical** (App. A). So the class's form of the invariant is
"the source delayed by exactly `latency_samples`, byte for byte" — which is
only honest if `latency_samples` is right, which is D3.

*Rate note.* Every trait holds at 44.1 and 22.05 kHz, but the *latency in
milliseconds* is rate-dependent and the partition is not: 256 frames is
5.33 ms at 48 kHz, 5.80 ms at 44.1 kHz and **11.61 ms at 22.05 kHz**. The
docstring states all three; `latency_samples` is 256 at every rate.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| # | Source | What it gave | Licence as read | Reached |
|---|---|---|---|---|
| S1 | [Gardner, *Efficient Convolution without Input–Output Delay*, JAES 43(3):127–136, 1995 March](https://people.montefiore.uliege.be/josmalskyj/files/Gardner1995Efficient.pdf) (presented at the 97th AES Convention, San Francisco, 1994 November 10–13 — the footnote on p. 127; the page range from the AES e-library entry, reached this run) | the abstract's own statement of the trade — "block processing incurs significant input–output delay, which is undesirable for real-time applications… A hybrid convolution method is proposed… The result is a zero-delay convolver" | no rights statement anywhere on the scan's p. 1; the host is a third party's staff page (Julien Osmalskyj, U. Liège), whose footer reads "© Julien Osmalskyj" followed by a credit to the CSS template it uses, and grants nothing → **licence unverified — treated as copyleft**; read as a paper, nothing ported | HTTP 200; p. 1 rendered at scale 3 in two halves and read — title, author, affiliation, abstract, the `*` footnote and the running foot "J. Audio Eng. Soc., Vol. 43, No. 3, 1995 March 127" |
| S2 | [Russo, *Physical Modeling and Optimisation of a EMT 140 Plate Reverb*, MSc, Aalborg, 2021](https://projekter.aau.dk/projekter/files/517547034/Master_Thesis_Russo.pdf) **§1.2** | the T60 definition D5 is measured against — Sabine's "time necessary for the sound to experience a 60 dB decay" | p. 2 carries the bare line "Copyright © Aalborg University 2021" and nothing else; no grant, no terms, and the words "all rights reserved" appear nowhere in the document → **licence unverified — treated as copyleft**; read as a paper, nothing ported | HTTP 200; text extracted, copyright line read on p. 2, the Sabine sentence read in §1.2 "Basics of Room Reverberation" |
| S3 | [Dattorro, *Effect Design, Part 1*, JAES 45(9), 1997](https://ccrma.stanford.edu/~dattorro/EffectDesignPart1.pdf) §1.1–1.2 | the contrast this class exists for: an algorithmic network is "one particular network for producing reverberation", chosen and tuned; a convolution is the measured room itself | no rights statement in the PDF, and none on the author's CCRMA index page → **licence unverified — treated as copyleft**; read as a paper | HTTP 200; text extracted |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| D1 | **It is exactly convolution, to within one output LSB.** With an impulse loaded and the wet reference inside full scale, the output equals the double-precision direct sum ∑ h[k]·x[n−k−256] — h being the loaded int16 taps × 1/32768, the node's own load scale (`audioif_convolve.c:149`) — with a **peak error ≤ 1 LSB (−90.3 dBFS)** over the probe set. Levels are part of the trait: above full scale the int16 output saturates and the comparison means nothing. | the definition of an LTI filter; S1 for the block method; **measured this run** — 0.500 / 0.502 / 0.508 LSB (−96.3 / −96.3 / −96.2 dBFS) at three probe levels, App. A | high — measured, and the margin is a factor of two | Any peak error above 1 LSB on probe material whose direct-form reference stays inside ±32767 | M1 |
| D2 | **`seconds` is an allocation with a hard ceiling, and the class names it.** The ceiling is **512 partitions × 256 taps = 131 072 taps at every rate** (`audioif_convolve.h:58-60`) — 2.73 s at 48 kHz, 2.97 s at 44.1 kHz, 5.94 s at 22.05 kHz. Over it, construction raises before anything renders, and the message names the class and the ceiling in seconds at the running rate. | `audioif_convolve.h:58-60`; measured — `ConvolutionReverb(s, seconds=3.0)` raises today, but with the node's bare `ValueError: impulse is too long` (`Convolver.c:32`), which is the half this trait fixes | high | A silent truncation, a clamp, or an error whose text does not name both the class and the ceiling in seconds at the running rate | M2 |
| D3 | **Latency is one partition when an impulse is loaded and zero when none is, and `latency_samples` follows the loaded state rather than the node's constant.** 256 frames at every rate — 5.33 ms at 48 kHz, 5.80 at 44.1, 11.61 at 22.05. Re-measured this run: loaded, a click at frame 0 first appears at frame **256**; unloaded, `max abs(out − in) = 0` over 1 s while `node.latency` still reports 256. | `audioif_convolve.h:20-26`, `:112-115`; both states measured this run (App. A) | high — measured | A reported `latency_samples` that does not change when an impulse is loaded or cleared, or a measured first arrival other than 256 (loaded) or 0 (unloaded) at any of the three rates | M3 |
| D4 | **`mix` at zero is the source delayed by exactly `latency_samples`, byte for byte.** Re-measured this run: over 1 s of 440 Hz stereo, `out[i+512] == in[i]` for every sample and `out[0:512]` is all zero. The check is a byte digest and never a tolerance — a 1-LSB dry trim is a failure, not a rounding. | the mix law, `audioif_convolve.h:74-77`; measured this run (App. A) | high — measured | Any altered sample at `mix = 0`, or any non-zero sample in the first 256 frames | M4 |
| D5 | **The synthesized room's T60 is the requested decay within 2 %, and the tail reaches exact zero.** T60 from a **least-squares slope fit of the log-envelope over −5…−35 dB**, extrapolated to −60 dB — never the first window that crosses −60 dB. Measured this run at 0.5 / 1.0 / 2.0 s: **+0.0 / +0.4 / +0.3 %** by the fit, and Schroeder backward integration over the same region agrees within 0.5 %; the same renders read **+8 / +6 / +2 %** by a −60 dB crossing on 20 ms windows, which is why the estimator is in the trait. A 1.0 s room is bit-zero beyond 2.5 s. | `audioif_convolve.h:138-143`; S2 §1.2 for the T60 definition; measured this run (App. A) | high — measured by two estimators that agree | A fitted T60 more than 2 % from the request at any of the three, or any non-zero sample after the impulse has run out | M5 |
| D6 | **The synthesized room is unit-energy, so Decay is a time control and not a level control — and so is Damping.** Normalisation is the second pass over the *fully shaped* impulse: envelope, damping, predelay and diffusion all precede it (`audioif_convolve.c:211-248`), so the wet level is independent of every synthesis argument. Criterion: across the Decay macro's full span and across Damping, the wet RMS of the kit's held broadband probe varies by **≤ 0.5 dB**. Measured this run on the node over seven configurations (decay 0.25–2.0 s, damping 0 / 2 / 8 kHz): a **0.041 dB** spread, and noise returns at the level it went in (App. A). | `audioif_convolve.c:197-209` and `:211-248`; `upstream-diff.md:1360`; measured this run | high — measured across the range (was medium and unmeasured) | A wet level that tracks decay time or damping by more than 0.5 dB: a longer or a darker room that is also a quieter one | M6 |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Standout confirmed.** Nothing was found to argue a swap toward: the
reachable literature is about *methods* (S1) and about *impulse responses*,
not about a machine a class should imitate. Vision §4.2's "design; surface
only" is right, and the consequence is that this seed's job is the surface,
the allocation contract and the latency report — not a sound.

*(from §2)*

**Not reached**, each re-tested in the audit's second pass: the AES-published
Gardner — the e-library entry *does* load and confirms the citation (title,
author, "Volume 43, Issue 3, Pages 127-136", 1995 March) but states *"This
paper costs $33 for non-members and is free for AES members and E-Library
subscribers"*, so the paper itself stays behind the paywall and the
staff-page copy is what was read; Springer's route to Parker's spring paper
(still 303 to `idp.springer.com/authorize`; the DAFx archive was used
instead, in `Reverb.md`). **No impulse-response library was hunted this
run** — which IRs ship and under what licence is §8.2, a Phase 5 acquisition
question, recorded as deliberately not attempted rather than as a failed
fetch.

*(from §2)*

1. **D5 cited the wrong section of S2.** Sabine's T60 definition is in
   §1.2 "Basics of Room Reverberation" (p. 5), not §2, which is "State of the
   Art". The S2 row had it right and D5 did not; D5 now agrees with the row.

*(from §2)*

2. **S2's licence call overstated what the page says** — "all rights
   reserved as read" was not read anywhere. Restated as the vision §5
   default, the same correction as in `Reverb.md`.

*(from §2)*

3. **§1's `audioif_convolve.c:168-232` stopped short of the function**,
   which runs to `:253`; the range is corrected and the two normalisation
   passes given their own line numbers, `:197-209`.

*(from §3)*

**Trait critic pass, 2026-09-07.** All six rows survive; four were rewritten
and none was struck. The pattern in three of the four is the same: the row
stated a threshold but not the estimator or the level the threshold is read
at, and a criterion an estimator can be chosen after the fact is not a
criterion. D1 gained the measurement it never had, and D6 the one it said it
was missing. Row by row in **App. F**; the numbers in **App. A**.

*(from §3)*

Budget as a fraction of one stereo block's deadline (256 frames, 5.333 ms at
48 kHz), **for the shipped default patch and not for an arbitrary impulse**:
**P4 0.35, S3 0.60.** Lean patch expected: **yes, and it is the point of the
class's sizing** — cost is linear in impulse length, so the S3's share is what
picks the default `seconds`. Derived from the node's own figures
(`upstream-diff.md` §"What it costs"): 1024 taps ≈ 3 MFLOPS, one stereo second
≈ 150 MFLOPS, i.e. **≈0.75 MFLOPS per partition**. So 0.25 s (47 partitions)
is ≈35 MFLOPS and 1.0 s (188) is ≈140 MFLOPS; memory is ≈2 KB per partition
per stored IR channel — 377 KB per second per channel (App. B). A one-second
stereo room is a desktop or a render; the board default is short.

*(from §3)*

**Latency: 256 frames — 5.33 ms at 48 kHz, 5.80 ms at 44.1 kHz, 11.61 ms at
22.05 kHz — and it is algorithmic, not an option.** It is the one class in
the family that has any, and vision §9a's rule applies directly: the figure is
in the dossier, in `latency_samples`, and in the docstring in milliseconds at
each rate, and the class gate verifies it with a click. **The knob that would
trade CPU for it is Gardner's hybrid scheme** (S1) — direct-form taps for the
first partition, blocks behind them. It is **not asked for in Phase 1** (§5);
until it exists there is no latency knob, and the honest statement is that
this class is the wrong one for a live stompbox and `Reverb` is the right one.
Every *other* latency-adding option is absent: no lookahead, no pitch window.

*(from §4)*

**Two modes, and the surface must not lie about which is live.** With a
measured impulse loaded, Decay / Damping / Predelay / Diffusion describe
nothing — the room is the file. So with `impulse=` given the class exposes
only `Mix`, `Level`, `IR Gain` and `IR Start`, reports `measured = True`, and
raises the contract's index error on a synthesis macro rather than returning
a number that means nothing.

*(from §4)*

**Mono.** Not stereo-by-definition. A mono source gets a mono convolution
against the impulse's first channel; a stereo source with a mono impulse gets
that impulse on both channels; a stereo source with a stereo impulse gets a
true-stereo room — the node's own rule (`audioif_convolve.h:124-129`), stated
in the docstring and measured by the kit.

*(from §5)*

One ask is **recorded and deliberately not made**, so a later phase does not
rediscover it. **Deferred — non-uniform partitioning (Gardner's hybrid).**
*Trait it would unblock:* D3's latency clause, 256 frames to zero. *Why not
now:* the node's header puts the cost at "roughly triple the code" for a
saving that matters only when monitoring a live player
(`audioif_convolve.h:20-26`), and S1's abstract is the same trade in the
author's words. Phase 1 releases audioif once (roadmap §5.2), and spending
that release here would spend it on the *wrong class* — the live-stompbox path
is `Reverb`, already at zero, and the platform path is 52–418 ms regardless
(vision §9a). *Settles:* an issue on audioif filed in Phase 0 beside the
surviving asks, reopened only if a Phase 1 round trip measures the platform
under 10 ms, at which point 5.33 ms stops being noise.

*(from §5)*

**Palette-verifier pass, 2026-09-07.** "None for Phase 1" holds: every §4 and
§5 claim about the node was re-read with `grep -n` and re-probed on the CPython
build this run (App. A's additions). The deferred ask is **not** reachable by
composing what exists — there is no arbitrary-FIR node on the palette
(`audiofilters.Filter` is biquads), and `Convolver.latency` is a compile-time
constant returned regardless of the loaded state
(`audioconvolve/Convolver.c:240-243`), which is a class-side fix and not a node
ask. One citation was wrong and is corrected above: D1's load scale is
`audioif_convolve.c:149` (`float scale = gain * (1.0f / 32768.0f);`), not
`:177`, which is the `diffusion_ms` clamp.
