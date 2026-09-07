# Effects Dossier — `MultibandCompressor` (no historical standout — grade *design*)

**Class:** `lib/audioeffects/dynamics.py` — read once, for §7.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** none. Vision §4.2 lists this class with a dash and grade
*design*, and this run **confirms that rather than arguing a swap.** Split-band
compression is a topology, not a box: RaneNote 155 draws it as a general
variation on the compressor (Fig. 7) and shows it built in software from
ordinary parts, and the crossover it needs is a published alignment with a
name and two authors rather than a pedal (S2, S3). Nothing reached this run
names a canonical multiband unit anyone would point at.
**Grade:** design — the traits below are the textbook properties of a
crossover-split dynamics processor, stated as falsifiable Tier 2 rows rather
than left to Tier 1 and Tier 3 alone, because the palette's own summing and
fan-out fail two of them (§4) and a seed that did not say so would hand the
rebuild a trap.
**Portability tier:** needs audioif-own nodes (`audiodynamics`, `audioroute`)
**Status:** seed (Phase 0), written 2026-09-06

## 1. The mechanism, in one paragraph

There is no circuit, so this paragraph states the textbook object. A
split-band compressor "divides the incoming signal into two or more frequency
bands … Each band has its own side-chain detector and gain reduction is
applied equally to all frequencies in the passband. After dynamics processing,
the individual bands are re-combined into one signal" (S2, Fig. 7). Everything
interesting is in the divide-and-recombine, because the sum must be a wire
when nothing is compressing. The alignment that makes it one is
**Linkwitz-Riley**: two characteristics, "in-phase outputs (0° between
outputs) at all frequencies" and "constant voltage (the outputs sum to unity
at all frequencies)", obtained by "cascading … two Butterworth filters to create
the desired −6 dB crossover points (since each contributes −3 dB)" (S3). The
consequence a rebuild must not forget is that unity is not identity: the
summed outputs have "a flat amplitude response with a smoothly changing phase
response", the network itself "behav[ing] like an all-pass" (S4) — so a multiband
at rest is flat, not transparent, and a true bypass has to be a real bypass.
Order matters for polarity: "starting with LR-2, every other solution requires
inverting one output. That is, LR-2 and LR-6 need inverting, while LR-4 and
LR-8 do not" (S3), which is why fourth order is the sane default. Above that
the object is just compressors: each band gets its own threshold, ratio and
make-up, and the bands that are not working must stay out of the way of the
ones that are.

## 2. Sources and license calls

All fetched 2026-09-06; nothing from memory.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | Split-band compression as a topology (Fig. 7) and its … (App. S2) | PDF line "© 2005 Rane Corporation" … (App. S2) | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **S3** Bohn, *Linkwitz-Riley Crossovers: A Primer*, RaneNote 160 | The two LR characteristics verbatim … (App. S3) | Page foot "© 2005 Rane" beside a Terms of Use … (App. S3) | <https://www.ranecommercial.com/legacy/note160.html> | yes — HTML |
| **S4** Wikipedia, *Linkwitz–Riley filter* | "a flat amplitude response with a smoothly changing … (App. S4) | **CC BY-SA 4.0** (confirmed at the page foot … (App. S4) | <https://en.wikipedia.org/wiki/Linkwitz%E2%80%93Riley_filter> | yes — HTML |
| **Local** `audioif/src/shared/audioif_splitter.{c,h}`, `audioif/src/audioroute/Splitter.c`, `audioif_dynamics.c`, `audioif/docs/upstream-diff.md`, `audiocomponents/lib/audioeffects/dynamics.py`, the probes in the Appendix | What the shipped class and the palette actually do | MIT (audioif, audiocomponents) | — | yes |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — the textbook properties, stated so a measurement can fail them

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| M1 | **Unity sum.** With every band at unity the summed magnitude is flat within **±0.25 dB** from 30 Hz to min(20 kHz, 0.45 × sample rate) — at two bands for **every** crossover setting, and at three bands for every setting whose crossovers are **at least 8:1 apart**, which the surface enforces (§6). *(Critic pass, 2026-09-06: the first draft claimed "every crossover setting" and it is false by construction — the parallel three-way sums to **−7.94 dB** at 400/800 Hz, a legal setting on the first draft's own surface. A-M6 has the ratio table.)* | S3 ("the outputs sum to unity at all … (App. M1) | high | Any tone in the sweep beyond ±0.25 dB at a legal setting; a two-band sum that deviates at any setting; a three-band sum that deviates at 8:1 or wider; a surface that accepts a crossover pair closer than 8:1 | SUM at 40/8000 … (App. M1) |
| M2 | **Each crossover is −6 dB at its corner with a fourth-order skirt**: at a 200/2000 Hz split each band is −6.0 ± 0.5 dB at its corner and its skirt fits 24 ± 2 dB/octave over the octave-to-two-octaves band on the side that lies below Nyquist; and the two halves are in phase there — summed with no polarity inversion the level at the corner is 0.0 ± 0.25 dB, not a null | S3 ("−6 dB crossover points" … (App. M2) | high | A −3.0 dB corner (plain Butterworth rather than LR4); a fitted skirt outside 24 ± 2 dB/octave; a corner more than 0.25 dB off unity in the sum, or a null there (the LR-2/LR-6 polarity case S3 names) | XOVER |
| M3 | **Band isolation.** Driving one band to 12 dB of gain reduction lowers that band's passband magnitude by 12.0 dB within 0.5 dB, evenly across the passband (no more than 0.5 dB of tilt from one passband edge to the other), and leaves every other band's magnitude within 0.5 dB of its idle value everywhere more than half an octave from a crossover; the test is run for each band in turn | S2 ("gain reduction is applied equally to all … (App. M3) | high | An idle band moving more than 0.5 dB when a neighbour compresses; a driven band whose reduction is more than 0.5 dB off 12 dB or tilted by more than 0.5 dB across its passband | ISO, once per band |
| M4 | **Zero latency.** The dry-to-wet path adds no samples at any setting: an impulse emerges in the frame it entered | S3/S4 (an IIR crossover delays phase … (App. M4) | high | Any non-zero click offset; a partitioned or FIR crossover being chosen instead | CLICK |
| M5 | **The sum survives its source.** M1 holds whatever block size the source hands out: with the same probe delivered as 256, 8192, 16384, 20000 and 32768-frame `get_buffer` calls, the rendered output is byte-identical across all five and non-silent in all five | derived — no external source … (App. M5) | high | Any of the five renders differing from the 256-frame one; any of them silent; a non-zero-sample count that falls as the source's buffer grows | LONG |

No characters. M5 is in the set because the measurement in A-M5 shows the
shipped class returning **pure silence** on exactly the probe material the
Phase 0 kit is specified to use, and a trait that says "and it must still be
there" is the only way that failure gets caught rather than read as agreement.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

Compose first; almost all of it composes, and the two things that do not are
measured rather than argued.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

One, and it is a defect report rather than a feature.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Fifteen macros, inside the sixteen-macro wall.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Bands | TOGGLE | 2 / 3 | the band count S2's Fig. 7 leaves open |
| 1 | Crossover Low | UNIPOLAR | 40 … 800 Hz, log | the lower LR corner |
| 2 | Crossover High | UNIPOLAR | 800 Hz … 8 kHz, log | the upper LR corner; **at three bands it clamps to ≥ 8 × Crossover Low**, and Crossover Low clamps to ≤ ⅛ × Crossover High, so M1's ±0.25 dB is reachable at every setting the surface can produce (A-M6). The clamp is a clamp, never a refusal — the Tier 1 rate rule's shape |
| 3–5 | Low / Mid / High Threshold | UNIPOLAR | −60 … 0 dB | per-band compressor threshold |
| 6–8 | Low / Mid / High Ratio | UNIPOLAR | 1 … 20, log | per-band ratio |
| 9–11 | Low / Mid / High Gain | BIPOLAR | −12 … +12 dB | per-band make-up |
| 12 | Attack | UNIPOLAR | 0.1 … 100 ms, log | one attack, all bands |
| 13 | Release | UNIPOLAR | 5 … 1000 ms, log | one release, all bands |
| 14 | Mix | UNIPOLAR | 0 … 100 % | parallel compression; 0 % is the Tier 1 bypass |

At **Bands = 2** the High macros address the upper band and the Mid ones are
inert; the docstring says so, and the kit measures it. Characters: none.
Patches: **Master Glue**, **Bass Control** (low band only), **Vocal Bus**,
**De-Boom** (low threshold down, ratio up), **Loudness** (all three, gentle,
mix 60 %), and **Master Glue - lean** (two bands, the Tier 3 escape valve).

## 7. Defects in the current class the rebuild must not repeat

- **The source goes straight into the Splitter.** The class builds
  `audioroute.Splitter(source, taps=3)` at `dynamics.py:239` with nothing in
  front of it, so it inherits the ring behaviour of V-M1: a source that hands
  back more than 8192 frames in one call loses the first `n − 8192` of them,
  which on head-loaded material (a burst, an impulse) is the whole signal and
  renders the class silent (A-M5). The rebuild puts a block-sized node between
  the source and the Splitter (§4). The class ships today with no test that
  would notice.
- **No surface, nothing live.** `MACRO_LABELS = ()` at `dynamics.py:232`,
  `PATCHES = {0: ("Default", ())}` at `:234`; crossovers, thresholds and
  ratios are constructor-only (`:236-238`) and the per-band attack and release
  are hard-coded at `:267`. There is no make-up gain, no output gain and no
  mix; `mixer.voice[index].level = 1.0` at `:272` is fixed.
- **A dead parameter.** `def band(tap, biquads)` at `:242-243` never uses
  `tap`, and is called as `band(0, …)`, `band(1, …)`, `band(2, …)` at
  `:254-256` — three call sites passing an argument that does nothing, which
  reads as a tap assignment and is not one.
- **Mismatched block sizes with nothing saying why.** The `Filter`s take
  `_core.pcm()`'s 2048-byte default (`:243`), the `Mixer` takes 1024
  (`:262`), and `Dynamics` hands out at most 256 frames per call
  (`audioif_dynamics.h:32`). The comment at `:247-249` records that an earlier
  crossover error was "invisible while the filters themselves were wrong" —
  the right instinct, aimed at the wrong layer.
- **The docstring's claim is not measured anywhere.** `:223-226` states the
  bands "recombine flat to a fraction of a decibel"; that is true as measured
  (A-M3) and nothing in the repository checks it, so it has been a claim, not
  a fact, for the class's whole life.

## 8. Open questions

1. **Spend an all-pass to close the last 0.12 dB?** The parallel three-way's
   floor is −0.117 dB (A-M2); the textbook correction is to pass the outer
   band through an all-pass matching the other crossover, which the palette
   cannot build (§5). M1 passes without it. The recommendation is **no** —
   record the floor in the evidence pack and spend nothing. *Implementation
   session, Phase 2.*
2. **One attack/release for all bands, or three?** Three would need six macros
   and would break the sixteen-macro wall against the per-band gains. The
   surface above chooses one pair, shared; whether a patch-selected per-band
   offset is worth it is open. *Implementation session.*
3. **Does N-MB-1 belong to this program at all?** No — the palette
   verification refuted it as a node ask (§5). It remains a defect in an
   audioif-own node that predates the effects program and affects every class
   built on `Splitter`, and should be filed on audioif with the V-M1/V-M2
   reproduction, outside the node list. *Arthur.*
4. **Is an 8:1 minimum crossover ratio too coarse a surface?** It forbids, at
   three bands, a 200/1000 Hz split a mastering engineer might want (−0.55 dB,
   A-M6). The alternatives are a looser M1 bound stated per ratio, or the
   all-pass of §8.1 — which the palette cannot build (§5). The recommendation
   is the clamp, because a trait that holds only at some settings is the kind
   of bar that can be passed by claiming less. *Implementation session,
   Phase 2, with the measured table.*
5. **Whether the two-band lean patch is honest as a patch** or should be a
   constructor option — a patch that changes the topology is unlike every
   other patch in this library. *Implementation session.*


## Appendix

Probes ran 2026-09-06 against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit, on the shipped class with
`ratios=(1,1,1)` and `thresholds_db=(0,0,0)` so no band compresses.

**Method note, and it changed the answer.** Measure a summed response with
**steady sines, not an int16 impulse.** The first pass here measured the
shipped class's sum by impulse-FFT and reported a −0.88 dB dip at 1 kHz; the
same claim measured with steady sines came back at −0.087 dB. The impulse
method under-reads because each band's low-amplitude impulse tail quantises
away in int16 — a `HIGH_PASS` at 200 Hz measured −0.86 dB of passband gain by
impulse and −0.024 dB by sine. **The 0.88 dB was the measurement's error, not
the node's**, and it was caught only by running the claim two ways. The kit
spec should carry this: a control that must *pass* — here, a two-way LR4 sum,
which is flat to 0.0000 dB analytically — beside every response measurement.

**A-M1 — the control.** A two-way LR4 split at 200 Hz sums, analytically at
double precision, to max **+0.0000** / min **−0.0000** dB across
30 Hz–20 kHz. Any three-way number below that is not a real deviation.

**A-M2 — the three-way topology's own floor, analytic.** low = LP4(200),
mid = HP4(200)·LP4(2000), high = HP4(2000), double precision, RBJ
coefficients: max **+0.000** / min **−0.117 dB**, the worst point at
**1493 Hz**. The low band never passes through the upper crossover's all-pass,
and this is what that costs.

**A-M3 — the shipped class, measured with steady sines** (30 Hz–20 kHz, gain
in dB re input): 30 −0.097, 50 +0.143, 80 +0.070, 100 +0.006, 141 −0.021,
200 −0.101, 283 −0.141, 400 −0.086, 500 −0.066, 700 −0.061, 1 k −0.087,
1414 −0.122, 2 k −0.087, 2828 −0.027, 4 k −0.004, 6 k −0.001, 8 k +0.001,
12 k −0.000, 16 k +0.000. Max **+0.143** / min **−0.141 dB** — the topology's
floor plus int16 rounding, and inside M1's ±0.25 dB.

**A-M4 — latency.** An impulse at frame 64 through the shipped class came out
at frame 64, peak in the same frame. Zero, as M4 requires.

**A-M6 — how close the crossovers may get, derived this run.** The parallel
three-way of §4 (low = LP4(f₁), mid = HP4(f₁)·LP4(f₂), high = HP4(f₂)), RBJ
coefficients at Q = 0.70710678, double precision, 6000 log-spaced points
30 Hz–20 kHz, 48 kHz. Worst deviation of the sum against crossover spacing,
f₁ = 200 Hz:

| f₂ | ratio | min dB |
|---|---|---|
| 400 | 2:1 | **−7.95** |
| 600 | 3:1 | −2.27 |
| 800 | 4:1 | −0.99 |
| 1000 | 5:1 | −0.55 |
| 1200 | 6:1 | −0.36 |
| 1400 | 7:1 | −0.25 |
| 1600 | 8:1 | **−0.19** |
| 2000 | 10:1 | −0.12 |
| 3000 | 15:1 | −0.05 |

Spot checks away from f₁ = 200 behave the same way: 300/600 gives −7.95 dB,
400/800 −7.94, 600/1200 −7.92, 800/1600 −7.88, and 800/800 −2.50 — the
deviation tracks the *ratio*, not the absolute frequencies. A-M2's 200/2000 floor of −0.117 dB is
reproduced exactly by this derivation (two equal minima, 269 Hz and 1493 Hz),
which is the control that says the two runs agree.

**This is why M1 now carries a minimum crossover ratio.** The first draft's
surface allowed Crossover Low up to 800 Hz and Crossover High from 800 Hz, so
400/800 — an 8 dB dip — was a legal setting under a trait claiming ±0.25 dB at
every setting. The surface clamps instead (§6), and a class-gate probe at the
closest legal pair is the check that keeps the clamp honest.

**A-M5 — the Splitter drops the head of a long buffer.** *(Title and last
paragraph corrected by the palette verification, 2026-09-06: the node does not
erase the stream, it discards the first `n − 8192` frames of any buffer longer
than the ring — see V-M1/V-M2. This probe's material is one impulse at the
head, which is exactly the dropped part, so it reads as total erasure.)* The
shipped class, same settings, fed an `audiocore.RawSample` carrying one
impulse, driven until the source was exhausted:

| source frames | non-zero output samples |
|---|---|
| 8192 | 894 |
| 16384 | **0** |
| 20000 | **0** |
| 32768 | **0** |

Reduced to the node: a bare `audioroute.Splitter(taps=3)` with only tap 0
pulled gives 2 non-zero samples from an 8192-frame `RawSample` and **0** from
a 16384-frame one. `RawSample.get_buffer()` returns the whole array in one
call (16384 frames, confirmed), `Splitter.c:14-26` writes all of it, and
`audioif_splitter.c:34-39` drags every cursor past it. **This is the planted
fault for M5**: it is already red on today's build — and V-M3 shows the same
probe going green when one block-sized node is put in front of the Splitter,
which is the control that keeps the check from being a suite of only failures.

---

### Palette verification, 2026-09-06

Independent run against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit. Every number below is this
run's own; nothing is carried from the seed's first draft.

**V-M1 — what the Splitter actually drops.** Index-marked material (sample
value = frame index) through `audioroute.Splitter(taps=1)`, first output frame
decoded:

| source frames | first output frame decodes as source index |
|---|---|
| 4096 | 0 |
| 8192 | 0 |
| 16384 | **8192** |
| 32768 | **24576** |

The tap resumes at `write_pos − 8192`. Nothing is erased; the head of the
buffer is discarded.

**V-M2 — why it reads as total.** Burst-then-silence material (a 2048-frame
440 Hz burst, then silence) through the same one-tap Splitter: 8192-frame
source → 4088 non-zero samples (no loss); 16384 and 32768 → **0**. The burst
lives entirely inside the dropped head. Steady material of the same lengths
loses nothing audible: a 1 kHz sine gives 31404 and 62800 non-zero samples
respectively, at full amplitude.

**V-M3 — the guard, and the control.** Frames one `get_buffer` hands back:
`audiofilters.Filter` 512 (at `buffer_size=2048`), `audiomixer.Mixer` 256,
`audiodynamics.Dynamics` 256. Three-band split-and-sum over the same material
delivered as 8192-, 16384- and 32768-frame `RawSample`s, first 8192 output
frames hashed:

| guard node | 8192 | 16384 | 32768 |
|---|---|---|---|
| none | `786109…` | `32cd66…` | `958a37…` |
| `Mixer` in front | `786109…` | `786109…` | `786109…` |

Byte-identical with the guard, three different renders without it. The
`RawSample` chunking is confirmed directly: `audiocore.get_buffer` on a
32768-frame `RawSample` returns 131072 bytes — the whole array — in one call.

**V-M4 — M1, M2 and M4 rebuilt from the nodes.** Three-way parallel
LR4 split at 200/2000 Hz, every band at unity, steady sines:

| Hz | 30 | 200 | 800 | 1200 | 1493 | 2000 | 4000 | 20000 |
|---|---|---|---|---|---|---|---|---|
| sum (dB) | −0.000 | −0.091 | −0.074 | −0.108 | **−0.121** | −0.091 | −0.006 | 0.000 |

Ratio table, worst deviation 30 Hz–20 kHz: 8:1 (200/1600) **−0.19 dB**,
4:1 (200/800) **−0.99 dB**, 2:1 (200/400) **−7.96 dB**. An impulse at frame 64
leaves the composed chain at frame **64**. The two-way control that shows the
measurement can go red: one Butterworth section a side (LR2) at 4 kHz sums to
a true null at the corner (all-zero output) and −6.75 / −2.65 / −0.55 dB at
2828 / 2000 / 1000 Hz, while the LR4 pair sums to **0.00 dB at every one of
those frequencies**.

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

**A Tier 1 clause this class must read carefully.** "`mix` at zero is a wire
(byte-identical to source)" is satisfiable **only by a real bypass**, because
S4's all-pass result means the band sum is never byte-identical to the input
even with every band at unity. The class therefore implements `mix` at zero as
a bypass of the whole split, and M1 — not Tier 1 — is what holds the summed
path honest. This is stated here so the invariant is not quietly reinterpreted
at Station C. **Mono:** the split and the three detectors are per-band, not
per-channel, so a mono source gets identical processing. **Rate:** the upper
crossover's span tops at 8 kHz, below Nyquist at all three rates, so it never
clamps; M1–M3 hold as stated at every rate, with M1's sweep truncated at the
running Nyquist.
**`capabilities` (D10): `()`** — no band's behaviour refers to tempo.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | Split-band compression as a topology (Fig. 7) and its wording verbatim; the compressor block diagram it reuses; RMS detection for compressor modes | PDF line "© 2005 Rane Corporation"; the site's Terms of Use (reached this run, <https://www.ranecommercial.com/legacy/terms-of-use.html>) is "Copyright © 2012-2018 inMusic Brands, Inc. All rights reserved." — personal, non-commercial viewing only, no redistribution without written permission. **Verified all-rights-reserved**, not "no further terms". Read only | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **S3** Bohn, *Linkwitz-Riley Crossovers: A Primer*, RaneNote 160 | The two LR characteristics verbatim; cascaded-Butterworth construction and the −6 dB crossover point; the polarity rule (LR-2 and LR-6 invert, LR-4 and LR-8 do not) | Page foot "© 2005 Rane" beside a Terms of Use link; that page (reached this run) is "Copyright © 2012-2018 inMusic Brands, Inc. All rights reserved.", personal and non-commercial only. **Verified all-rights-reserved**, not merely ungranted. Read only | <https://www.ranecommercial.com/legacy/note160.html> | yes — HTML |
| **S4** Wikipedia, *Linkwitz–Riley filter* | "a flat amplitude response with a smoothly changing phase response"; the crossover network as one that "behaves like an all-pass"; −6 dB at cut-off; second-order needing a polarity inversion | **CC BY-SA 4.0** (confirmed at the page foot in the audit run) | <https://en.wikipedia.org/wiki/Linkwitz%E2%80%93Riley_filter> | yes — HTML |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| M1 | **Unity sum.** With every band at unity the summed magnitude is flat within **±0.25 dB** from 30 Hz to min(20 kHz, 0.45 × sample rate) — at two bands for **every** crossover setting, and at three bands for every setting whose crossovers are **at least 8:1 apart**, which the surface enforces (§6). *(Critic pass, 2026-09-06: the first draft claimed "every crossover setting" and it is false by construction — the parallel three-way sums to **−7.94 dB** at 400/800 Hz, a legal setting on the first draft's own surface. A-M6 has the ratio table.)* | S3 ("the outputs sum to unity at all frequencies"); the three-way floor derived and measured here (A-M2, A-M3, A-M6) | high | Any tone in the sweep beyond ±0.25 dB at a legal setting; a two-band sum that deviates at any setting; a three-band sum that deviates at 8:1 or wider; a surface that accepts a crossover pair closer than 8:1 | SUM at 40/8000, 200/2000 and the closest legal pair at each band count |
| M2 | **Each crossover is −6 dB at its corner with a fourth-order skirt**: at a 200/2000 Hz split each band is −6.0 ± 0.5 dB at its corner and its skirt fits 24 ± 2 dB/octave over the octave-to-two-octaves band on the side that lies below Nyquist; and the two halves are in phase there — summed with no polarity inversion the level at the corner is 0.0 ± 0.25 dB, not a null | S3 ("−6 dB crossover points"; "in-phase outputs (0° between outputs) at all frequencies"; LR-4 needs no inversion) | high | A −3.0 dB corner (plain Butterworth rather than LR4); a fitted skirt outside 24 ± 2 dB/octave; a corner more than 0.25 dB off unity in the sum, or a null there (the LR-2/LR-6 polarity case S3 names) | XOVER |
| M3 | **Band isolation.** Driving one band to 12 dB of gain reduction lowers that band's passband magnitude by 12.0 dB within 0.5 dB, evenly across the passband (no more than 0.5 dB of tilt from one passband edge to the other), and leaves every other band's magnitude within 0.5 dB of its idle value everywhere more than half an octave from a crossover; the test is run for each band in turn | S2 ("gain reduction is applied equally to all frequencies in the passband") | high | An idle band moving more than 0.5 dB when a neighbour compresses; a driven band whose reduction is more than 0.5 dB off 12 dB or tilted by more than 0.5 dB across its passband | ISO, once per band |
| M4 | **Zero latency.** The dry-to-wet path adds no samples at any setting: an impulse emerges in the frame it entered | S3/S4 (an IIR crossover delays phase, not onset); measured on the shipped class (A-M4) | high | Any non-zero click offset; a partitioned or FIR crossover being chosen instead | CLICK |
| M5 | **The sum survives its source.** M1 holds whatever block size the source hands out: with the same probe delivered as 256, 8192, 16384, 20000 and 32768-frame `get_buffer` calls, the rendered output is byte-identical across all five and non-silent in all five | derived — no external source; the failure is measured at A-M5, where three of those five give exactly zero non-zero samples on the shipped class | high | Any of the five renders differing from the 256-frame one; any of them silent; a non-zero-sample count that falls as the source's buffer grows | LONG |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

*Licence and citation audit, 2026-09-06 — **two passes**. Second pass (unit
`gate-deesser-transient-multiband`): every URL above re-fetched from this
machine with `curl` (all HTTP 200), every PDF re-extracted with `pypdf` and
every quotation re-read against the document's own text, every licence line
read on the page that carries it, and every "not reached" claim re-tested.
Corrections are marked inline.*

*(from §2)*

*Second-pass result: **no correction needed.** All three licence calls stand as
written (S3's "© 2005 Rane" foot and its Terms-of-Use link, S4's CC BY-SA 4.0
foot, S2's "© 2005 Rane Corporation" and the inMusic terms), every quotation in
§1 and §3 verified verbatim against the source, and the first pass's own
correction re-confirmed: the strings "three-way", "three way" and "3-way" occur
nowhere in RaneNote 160, and "For simplicity, only a two way system is being
modeled" is on the page as quoted.*

*(from §2)*

No copyleft source was reached, so none was measured; no emulator was opened.
**Looked for and not found:** a three-way LR crossover treatment — S3 covers
two-way only: the string "three-way" does not occur anywhere in the note, and it
says of its own model "For simplicity, only a two way system is being modeled".
It does discuss Butterworth all-pass designs, but gives no all-pass correction
for a three-way split, and neither S4 nor S2 does either. *Corrected by the
audit: the first draft put "does not address three-way designs or allpass
corrections for such configurations" in quotation marks; that sentence is not on
the page — it was a fetch tool's summary of it — and the finding is restated
above as what the note actually contains.* M1's three-way number below is
therefore **derived here and measured here** (A-M2, A-M3), not cited. **Unsourced, therefore absent from the trait
table:** any claim about how many bands a multiband should have, any preferred
crossover frequency, and any claim about the audibility of the all-pass phase
rotation S4 describes.

*(from §3)*

Kit: **SUM** = steady sines at 1/6-octave spacing, 30 Hz–20 kHz, every band at
unity, output RMS against input RMS per tone (**not** an impulse — see the
Appendix's method note); **XOVER** = the same sweep with one band muted, its
−6 dB point and skirt fitted; **ISO** = the sweep with one band driven into
12 dB of reduction and the others idle; **CLICK** = an impulse against the dry
path; **LONG** = the SUM sweep from a source that hands back more than 8192
frames in one `get_buffer` call.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**25 %**, ESP32-S3 **45 %**. Lean patch expected: **yes** — a `" - lean"`
patch drops to two bands (one crossover, four biquads, two detectors), which
is roughly two thirds of the three-band cost. The three-band build is one
`Splitter`, eight biquads across three `Filter` chains, three `Dynamics`
detectors and one `Mixer` per frame; it is the most expensive class in this
unit by a factor of four and the only one expected to need the escape valve.

*(from §3)*

**Latency: zero, and no option adds any.** The crossover is IIR and the
detectors do not look ahead, so `latency_samples` is 0 — measured on the
shipped chain, an impulse at frame 64 came out at frame 64 (A-M4). Two
latency-adding options are deliberately **not offered**: per-band look-ahead
(`Dynamics` supports it, capped at 50 ms, `audioif_dynamics.h:53`) and any
linear-phase or partitioned crossover. If a later revision adds look-ahead it
defaults to 0, is reported in `latency_samples` the moment it is set, and is
named in the docstring in milliseconds at 48 kHz, per vision §9a.

*(from §4)*

The topology is `audioroute.Splitter(taps=n)` → one `audiofilters.Filter` per
band carrying a cascade of `synthio.Biquad`s at Q = 0.707 → one
`audiodynamics.Dynamics(DYN_COMPRESS)` per band → `audiomixer.Mixer`. Band
count is capped at **four** by the ring's tap limit
(`audioif_splitter.h:21`), which is enough for the surface in §6. Crossovers
are LR4 — two cascaded Butterworth sections a side — so no polarity inversion
is needed (S3).

*(from §4)*

**M1 is reachable, and by a smaller margin than it looks.** The shipped
parallel three-way arrangement — low = LP4(f₁), mid = HP4(f₁)·LP4(f₂), high =
HP4(f₂) — is not the textbook two-way case, and its own analytic floor is
**−0.117 dB at 1493 Hz** for the shipped 200/2000 Hz split, because the low
band never passes through the upper crossover's all-pass (A-M2). Measured with
steady sines, the shipped class lands at **+0.143 / −0.141 dB** across
30 Hz–20 kHz (A-M3), essentially at that floor. So M1's ±0.25 dB is reachable
today with the existing nodes **at the shipped 200/2000 Hz spacing**, and the
rebuild's choice is whether to spend an all-pass section to close the last
0.12 dB — a decision, not an ask, and §8 carries it. What the first draft did
not say, and the critic pass measured, is that this floor is a function of the
crossover *ratio* and grows fast as the corners close: −0.19 dB at 8:1,
−0.99 dB at 4:1, **−7.95 dB at 2:1** (A-M6). The surface therefore clamps the
ratio at 8:1 (§6) and M1 is stated against that clamp. *(Palette verification,
2026-09-06, rebuilt independently from the nodes: the 200/2000 Hz three-way sum
floors at **−0.121 dB at 1493 Hz**, the ratio table reproduces at **−0.19 /
−0.99 / −7.96 dB** for 8:1 / 4:1 / 2:1, and an impulse at frame 64 leaves the
composed chain at frame 64 — M1, M2 and M4 confirmed on the palette as it
stands, V-M4.)*

*(from §4)*

**M5 is reachable, but only if the class guards its own fan-out — and the
first draft's account of the failure was wrong.** *(Palette verification,
2026-09-06; the mechanism below is measured, V-M1/V-M2/V-M3 in the Appendix.)*
`audioroute_splitter_pull` takes whatever the source hands back in one call and
writes all of it into the ring (`Splitter.c:14-26`), and
`audioif_splitter_write` advances every tap's cursor whenever the write laps it
— including the cursor of the tap that asked for the refill
(`audioif_splitter.c:34-39`). The ring is 8192 frames
(`audioif_splitter.h:20`), so a write of `n > 8192` frames leaves every cursor
at `write_pos − 8192`: **the Splitter discards the first `n − 8192` frames of
that buffer and the tap resumes part-way in.** It does not erase the stream.
Decoded with index-marked material, a 16384-frame `RawSample` gives a tap whose
first output frame is source frame **8192**, and a 32768-frame one gives source
frame **24576** (V-M1). On steady material the audio therefore survives,
time-shifted; on **burst-then-silence material — which the Phase 0 kit
specifies — the dropped part is the whole signal and the output is exactly
zero** (V-M2: 8192-frame source, 4088 non-zero samples; 16384 and 32768, zero).
That is how the first draft read the failure as "total"; it is the probe
material, not the node's reach.

*(from §4)*

**The guard is one node, and it is complete.** The defect fires only when the
Splitter's *immediate source* hands back more than 8192 frames in one call,
which only a whole-buffer source such as `audiocore.RawSample` does — every
processing node on the palette hands back its own block (`Filter` 512 frames at
`buffer_size=2048`, `Mixer` 256, `Dynamics` 256, measured V-M3). Putting any
one of them between the source and the Splitter removes the drop entirely:
measured, a three-band split-and-sum renders **byte-identical output (sha256
`786109593641…`) from 8192-, 16384- and 32768-frame sources with a `Mixer` in
front, and three different hashes without it** (V-M3). So the class builds its
fan-out as `source → block-sized node → Splitter`, and M5 is met with the
palette as it stands. The trait stays in the set: it is the only thing that
turns the silent-and-*consistent* render workspace-craft warns about into a red
result.

*(from §4)*

**Portability tier: audioif** (`audiodynamics`, `audioroute`;
`upstream-diff.md:661`) — guarded import, construction-time `ImportError` on a
stock board. Python computes the biquad coefficients at construction and on a
crossover move; C runs the filters, three detectors and the mixer per sample.
No table is built on a board.

*(from §5)*

- **N-MB-1 — a bounded pull on `audioroute.Splitter` (unblocks M5).** The
  Splitter must not write more into the ring than the least-advanced tap has
  read, or must keep the remainder pending until it has. Palette today: it
  writes everything and drags every cursor, the requesting tap's included
  (`Splitter.c:14-26`, `audioif_splitter.c:34-39`), so a write of `n > 8192`
  frames drops the first `n − 8192` of them.

*(from §5)*

  **REFUTED BY PALETTE: a block-sized node between the source and the Splitter
  removes the drop entirely, and the class controls that node.** The defect
  fires only when the Splitter's immediate source hands back more than 8192
  frames in one call, which only a whole-buffer source such as
  `audiocore.RawSample` does; `Filter`, `Mixer` and `Dynamics` all hand back
  their own block (512 / 256 / 256 frames, measured V-M3). With a `Mixer` in
  front, a three-band split-and-sum renders byte-identical output from 8192-,
  16384- and 32768-frame sources — M5 met with the palette as it stands
  (V-M3). The class builds `source → block-sized node → Splitter` and needs no
  node. *(Palette verification, 2026-09-06. The first draft's refutation —
  "a class cannot pre-chunk its source, because the Splitter owns the pull" —
  is true and beside the point: the class does not need to pre-chunk, only to
  put one node it already builds in front.)*

*(from §5)*

  **What survives is a defect report, not a node ask.** The Splitter still
  destroys audio for anyone who hands it a long buffer directly, silently and
  consistently — the shape workspace-craft warns about. `audioroute` is
  audioif's own module with no upstream (`upstream-diff.md:661`), so it is an
  audioif issue, filed with the V-M1/V-M2 reproduction, and **it is not
  additive** — a fix changes an existing own node's behaviour. It does not
  block Phase 1 and it does not gate any trait in this seed.
- **Not asked for:** RMS detection per band. S2's Fig. 7 shows RMS detectors,
  and the palette's are peak (`audioif_dynamics.c:265`) — but M1–M5 do not
  depend on the detector type, and the ask already exists as `Expander`'s
  N-EXP-1. Recorded here so the survey counts it once.
- **Not asked for:** an all-pass biquad. `synthio.FilterMode` offers
  LOW_PASS, HIGH_PASS, BAND_PASS, NOTCH, PEAKING_EQ, LOW_SHELF and HIGH_SHELF
  and no all-pass (read from the CPython build this run), so closing M1's last
  0.12 dB by the textbook three-way correction would need one. M1 is met
  without it, so no ask is filed; §8.1 records the choice, and the EQ family's
  Gate 0 biquad decision is where an all-pass would properly be argued.
