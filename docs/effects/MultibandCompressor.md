# Effects Dossier — `MultibandCompressor` (no historical standout — grade *design*)

**Class:** `lib/audioeffects/dynamics.py` — read once, for §7.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** none — split-band compression is a topology, not a box, and
nothing reached names a canonical unit (the full reading is in **App. R**).
**Grade:** design.
**Portability tier:** audioif — `audiobiquad`, `audiodynamics`, `audioroute` (§4).
**Status:** seed 2026-09-06; **§§3–8 restructured, §8 settled and §6 frozen
2026-09-07** at Station A of the rebuild.

## 1. The mechanism, in one paragraph

There is no circuit, so this states the textbook object. A split-band
compressor "divides the incoming signal into two or more frequency bands …
Each band has its own side-chain detector and gain reduction is applied
equally to all frequencies in the passband. After dynamics processing, the
individual bands are re-combined into one signal" (S2, Fig. 7). Everything
interesting is in the divide-and-recombine, because the sum must be a wire
when nothing is compressing. The alignment that makes it one is
**Linkwitz-Riley**: "in-phase outputs (0° between outputs) at all frequencies"
and "the outputs sum to unity at all frequencies", got by "cascading … two
Butterworth filters to create the desired −6 dB crossover points" (S3). The
consequence a rebuild must not forget is that **unity is not identity**: the
summed outputs have "a flat amplitude response with a smoothly changing phase
response", the network itself "behav[ing] like an all-pass" (S4) — a multiband
at rest is flat, not transparent, so a true bypass has to be a real bypass.
Polarity follows the order: LR-2 and LR-6 "need inverting, while LR-4 and LR-8
do not" (S3), which is why fourth order is the sane default. Above that the
object is just compressors: each band its own threshold, ratio and make-up,
and the bands that are not working staying out of the way of the ones that
are.

## 2. Sources and license calls

All fetched 2026-09-06; nothing from memory.

Every reading, licence line and quotation check is in **App. S**; the gate
conditions — id, URL, reached — are here.

| Source | License | URL | Reached |
|---|---|---|---|
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | all rights reserved, read only | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF, text via `pypdf` |
| **S3** Bohn, *Linkwitz-Riley Crossovers: A Primer*, RaneNote 160 | all rights reserved, read only | <https://www.ranecommercial.com/legacy/note160.html> | yes — HTML |
| **S4** Wikipedia, *Linkwitz–Riley filter* | **CC BY-SA 4.0** | <https://en.wikipedia.org/wiki/Linkwitz%E2%80%93Riley_filter> | yes — HTML |
| **Local** the audioif C named throughout, `upstream-diff.md`, `dynamics.py`, this dossier's probes | MIT | — | yes |

Two licence and citation audits, and the second needed no correction: **App. R**.

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — the textbook properties, stated so a measurement can fail them

**Frozen. M1–M5 are the seed's own rows of 2026-09-06.** The Station A pass of
2026-09-07 restructured §§1–8, settled §8 and corrected three palette claims
(§§4, 5); it added, removed, retired and loosened nothing. Each row's full
statement, its source reading and its confidence reasoning are in **App. T**,
which the gate reads; the column below is the claim in one line.

| # | Trait | Bar | Disconfirmed by | Meas. |
|---|---|---|---|---|
| M1 | **Unity sum**: every band at unity, the summed magnitude is flat, 30 Hz to min(20 kHz, 0.45 fs) — at **two** bands for every crossover setting, at **three** for every setting 8:1 or wider, which §6 enforces | ±0.25 dB | any tone past the bar at a legal setting; any two-band deviation; a surface accepting a pair closer than 8:1 | SUM at 40/8000, 200/2000 and the closest legal pair per band count |
| M2 | **LR4 crossovers**: at 200/2000 Hz each band is −6 dB at its corner on a 24 dB/octave skirt, and the halves are in phase there — the sum at the corner is unity, not a null | ±0.5 dB, 24 ± 2 dB/oct, ±0.25 dB | a −3 dB corner (plain Butterworth); a skirt outside the band; a null at the corner (S3's LR-2/LR-6 case) | XOVER |
| M3 | **Band isolation**: 12 dB of reduction on one band lowers *that* band's passband by 12 dB, evenly, and leaves the others where they were more than half an octave from a crossover | ±0.5 dB; tilt and leak ≤ 0.5 dB | an idle band moving when a neighbour compresses; a driven band off 12 dB or tilted | ISO, per band |
| M4 | **Zero latency**: an impulse emerges in the frame it entered, at every setting | 0 samples | any non-zero click offset; a partitioned or FIR crossover chosen instead | CLICK |
| M5 | **The sum survives its source**: the same probe at 256, 8192, 16384, 20000 and 32768-frame `get_buffer` calls renders byte-identically and non-silently | identical digests | any render differing from the 256-frame one; any of them silent | LONG |

No characters. M5 is in the set because A-M5 measures the shipped class
returning **pure silence** on exactly the material the Phase 0 kit specifies,
and a trait saying "and it must still be there" is the only way that reads as
a failure rather than as agreement. The five kit measurements are defined in
App. R.

### Tier 3 — cost and latency

**Budget**, of one stereo block's real-time deadline: **P4 25 %, S3 45 %.**
Lean build expected: **yes**. Three bands is **fourteen nodes** — guard,
four-tap `Splitter`, eight biquads, three detectors, four-voice `Mixer` — the
most expensive class in this unit by about four. `bands=2` is the valve: four
biquads, two detectors, three voices (§8.5).

**Latency: 0 samples at every setting, and no option can add any** — the
crossover is IIR, no detector looks ahead, and per-band look-ahead and any
linear-phase crossover are deliberately not offered (App. R).
`tail_samples` is not zero and not a constant: it is the lower crossover's
ring-down, reported per instance.

## 4. Modeling approach on the palette — settled 2026-09-07

All of it composes; nothing is asked for. Every run behind a line here is in
**App. P**.

- **Fan-out.** `source → audiofilters.Filter(filter=None) → audioroute.Splitter(taps = bands + 1)`,
  tap 0 dry. The guard is not optional: without it a whole-buffer source loses
  the first *n* − 8192 frames (**P4**, re-running V-M1/V-M3).
- **Crossover.** LR4: two `audiobiquad.Biquad` sections a side at Q = 0.7071
  — **not** the `synthio.Biquad` cascade inside `audiofilters.Filter` the
  seed's §4 mapped, which holds DC for ever and cannot pass Tier 1's first
  invariant (**P1**). *(Correction: `audiobiquad` landed in Phase 1, after
  the seed.)*
- **Detectors.** One `audiodynamics.Dynamics(DYN_COMPRESS, detector="rms")`
  per band: RMS landed with the node's twenty-one options and S2's Fig. 7
  draws RMS detectors (**P3**). *(Correction: §5's "the palette's are peak"
  is stale.)*
- **Sum.** One `audiomixer.Mixer`, a dry voice plus one per band. Make-up
  rides `makeup_db` on the detectors — a Mixer voice level is clamped to 0..1
  and cannot carry +12 dB.
- **Reset order.** The Mixer is owned **first** so the walk resets it **last**:
  its reset resets each voice's source and then pulls a chunk through it, so
  resetting it tail-first lands the crossover's ring-down in the voice buffer,
  where nothing later can reach it (**P5**).

**M1 is reachable and its margin is the topology's own**, not the nodes'.
Rebuilt on `audiobiquad` the 200/2000 Hz three-way sums to **+0.001 / −0.119
dB** — A-M2's analytic floor, with the shipped class's Q12 rounding gone — and
that floor tracks the crossover **ratio**: **−0.192 dB at 8:1, −0.986 at 4:1,
−7.954 at 2:1** (**P6**, reproducing A-M6 and V-M4). Hence §6's clamp.

**Portability tier: audioif** — `audiobiquad`, `audiodynamics`, `audioroute`
(`upstream-diff.md:661`, `:1953`): guarded import, construction-time
`ImportError` on a stock board. C runs everything per sample. **Mono:** the
split and the detectors are per band, not per channel, so a mono source is
processed identically (App. I).

## 5. Node asks — none

- **N-MB-1 (a bounded pull on `audioroute.Splitter`) — REFUTED and it stays
  refuted:** any block-sized node in front removes the drop, and the class
  builds that node (§4, P4). What survives is a **defect report on audioif**,
  filed with the V-M1/V-M2 reproduction — the Splitter still destroys audio
  for anyone who hands it a long buffer directly, silently and consistently.
  It gates no trait here.
- **RMS detection — no longer an ask:** it landed (`detector="rms"`,
  `upstream-diff.md:969`) and the rebuild uses it (P3).
- **An all-pass — still not asked for, for a corrected reason:** the palette
  *has* `audiobiquad.AllPass`, which the seed did not know about, but it is a
  cascade of **first-order** sections and the three-way correction needs a
  **second-order** all-pass at Q = 0.7071 — what LP4 + HP4 sums to — which no
  palette node produces (**P2**). M1 is met without it (§8.1).

## 6. Surface — frozen 2026-09-07

**Fourteen macros.** *(The seed proposed fifteen, with `Bands` as macro 0;
§8.5 settles that as a constructor option instead.)*

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Crossover Low | UNIPOLAR | 40 … 800 Hz, log | the lower LR corner; at two bands the only one |
| 1 | Crossover High | UNIPOLAR | 800 Hz … 8 kHz, log | the upper LR corner, clamped to ≥ 8 × macro 0 |
| 2–4 | Low / Mid / High Threshold | UNIPOLAR | −60 … 0 dB | per-band threshold |
| 5–7 | Low / Mid / High Ratio | UNIPOLAR | 1 … 20, log | per-band ratio |
| 8–10 | Low / Mid / High Gain | BIPOLAR | −12 … +12 dB | per-band make-up (`makeup_db`) |
| 11 | Attack | UNIPOLAR | 0.1 … 100 ms, log | one attack, all bands (§8.2) |
| 12 | Release | UNIPOLAR | 5 … 1000 ms, log | one release, all bands |
| 13 | Mix | UNIPOLAR | 0 … 100 % | parallel compression; **0 % is the Tier 1 bypass**, a real one (App. I) |

**The clamp is one-directional** — the lower corner is authoritative, the
upper one is pushed up to meet it, because a mutual clamp has no defined
answer when both macros move — and it is a clamp, never a refusal.
`crossover_high_hz` reports what was applied; `macro(1)` what was asked.

**`bands` is a constructor option, 2 or 3**, the only thing that changes the
topology. At two bands Crossover High and the three Mid macros are inert;
`macro_is_live(index)` says which. Characters: none. **`capabilities` = `()`**
— nothing here refers to tempo, so the transport is never read (App. I, D10).

**Patches:** 0 **Master Glue** (the constructor's defaults on the grid),
1 **Bass Control**, 2 **Vocal Bus**, 3 **De-Boom**, 4 **Loudness** (mix 60 %).
The seed's *Master Glue - lean* is gone: a patch cannot change the node graph,
so it could never have been the escape valve it was proposed as (§8.5).

## 7. Defects in the current class the rebuild must not repeat

Five, and the rebuild's answer to each; the readings, line numbers and the
seed's own prose are in **App. D**, which is what Station B works from.

1. **The Splitter is fed straight off the source** (`dynamics.py:239`), so a
   long buffer loses its head — silence on head-loaded material (A-M5).
   *Answer: a block-sized guard in front (§4).*
2. **No surface, nothing live** — no macros, one empty patch, everything
   constructor-only, attack and release hard-coded, no make-up, no mix.
   *Answer: fourteen macros, five patches (§6).*
3. **A dead parameter** — `band(tap, biquads)` never uses `tap`, and three
   call sites pass one. *Answer: `_band_chain(band)` uses its argument.*
4. **Three block sizes with nothing saying why** — 2048 / 1024 / 256.
   *Answer: one, 256 frames.*
5. **The docstring's flatness claim is measured nowhere** (`:223-226`).
   *Answer: M1, at six settings, red on a planted fault.*

## 8. Open questions — all five settled, 2026-09-07

1. **Spend an all-pass to close the last 0.12 dB? — No.** M1 passes without it
   (−0.119 dB against ±0.25 dB, P6) and the correction is not buildable
   anyway (P2). *(The seed's answer kept; its reason corrected.)*
2. **One attack/release for all bands, or three? — One pair, shared.** Three
   would need six macros and break the sixteen-macro wall against the per-band
   gains; no source asks for per-band times. No patch-selected offset either.
3. **Does N-MB-1 belong to this program? — No.** §5 now says so in its own
   right: a defect report on audioif, outside the node list. *Arthur's.*
4. **Is an 8:1 minimum ratio too coarse? — Keep the clamp.** The alternative
   is an M1 stated per ratio, which is a bar that can be passed by claiming
   less. The cost is named: at three bands 200/1000 Hz is unreachable
   (−0.55 dB, A-M6); the surface offers 200/1600 at −0.192 dB.
5. **Is the two-band lean patch honest as a patch? — No; it is a constructor
   option.** A `program_change` moves macro positions, so a patch cannot drop
   a node — and a `Bands` *macro* would have been worse than useless: the
   Mixer pulls a voice at level 0 exactly as hard as one at unity, so a muted
   middle band still costs four biquads and a detector every block. The escape
   valve has to be a different build. **What that costs**, recorded rather
   than hidden: the band count is not automatable from a host's macro lane.


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

### App. P — palette verification, 2026-09-07 (Station A of the rebuild)

Run by `tools/phase2_probes/multiband_palette.py` against the CPython build
of audioif in `audiocomponents/.venv`, 48 kHz, stereo, 16-bit, audioif at the
pin. Every number here is that run's own. Three of the seed's palette claims
did not survive it; each correction is marked in §4 or §5 as well as here.
Nothing in §3 moved.

**P1 — the tail, and it decides the crossover node.** A 256-frame full-scale
DC burst into a two-section LOW_PASS cascade, then three seconds of silence:

| corner | `audiobiquad.Biquad` ×2 | `audiofilters.Filter` + `synthio.Biquad` ×2 |
|---|---|---|
| 100 Hz | last non-zero frame **1895**, held **0 LSB** | last non-zero frame 144511 of 144512, held **2 LSB** |
| 40 Hz | last non-zero frame **3987**, held **0 LSB** | last non-zero frame 144511 of 144512, held **8 LSB** |

The ported cascade never arrives — that is audioif#23's fixed points, in the
one place this class cannot avoid them — and Tier 1's first invariant is that
a decaying tail reaches exact zero. **Correction to §4:** the crossover is
`audiobiquad`, not `audiofilters` over `synthio.Biquad`. The seed could not
have known: `audiobiquad` landed in Phase 1, after it was written.

**P2 — the palette does have an all-pass, and it is the wrong order.**
`audiobiquad.AllPass(stages=…, frequency=…, feedback=…, mix=…)`, up to
`MAX_STAGES` 16, is a cascade of **first-order** sections;
`audiobiquad.MODES` is the same seven as `synthio.FilterMode` and carries no
all-pass either. The textbook three-way correction needs a **second-order**
all-pass at Q = 0.7071 — it is what LP4 + HP4 sums to — and no palette node
produces one. **Correction to §5:** the reason changes, the answer does not
(§8.1).

**P3 — RMS detection landed.** A 220 Hz sine against a square, into
`DYN_COMPRESS` at −40 dB, ratio 4:

| detector | equal amplitude | equal RMS |
|---|---|---|
| `peak` | sine −21.38, square −21.58 dB → spread **0.20 dB** | sine −21.38, square −19.34 → spread **2.05 dB** |
| `rms` | sine −19.43, square −21.58 dB → spread 2.15 dB | sine −19.43, square −19.34 → spread **0.10 dB** |

Each detector is flat on the quantity it detects, which is the point: S2's
Fig. 7 draws RMS detectors, and `detector="rms"` is on the pin
(`upstream-diff.md:969`). **Correction to §5:** "the palette's are peak" is
stale; the rebuild uses RMS.

**P4 — the guard, V-M3 re-run.** One impulse at frame 64, through
`audioroute.Splitter(taps=4)`, tap 0, non-zero output samples:

| source frames | 256 | 8192 | 16384 | 20000 | 32768 |
|---|---|---|---|---|---|
| straight off the source | 2 | 2 | **0** | **0** | **0** |
| through one block-sized node | 2 | 2 | 2 | 2 | 2 |

**P5 — `audiomixer`'s reset pulls.** `MixerVoice.reset()` resets the voice's
source and then takes a chunk from it, so the order the class's enumerated
walk resets in is not cosmetic. On the class, primed to the end of an 80 Hz
burst and then reset:

| walk | after `reset()` | per band |
|---|---|---|
| the Mixer owned first, so reset **last** | **0 LSB** | 0, 0, 0 |
| the Mixer reset first (tail-first, the natural order) | **1790 LSB** | low **4775**, mid **2985**, high 0 |

The per-band figures are taken on their own instances with the solo set
*before* the first pull after the reset: read them after a pull and the
residual is already gone, which reads as a clean reset and is not one.

**P6 — the three-way sum, rebuilt on `audiobiquad`, every band at unity.**
Steady sines, 30 Hz–20 kHz. At 200/2000 Hz: **max +0.001 / min −0.119 dB**,
which is A-M2's analytic floor with the shipped class's Q12 rounding gone
(A-M3 measured +0.143 / −0.141 on the ported nodes). The ratio table, worst
deviation over the same tones:

| f₁/f₂ | ratio | min dB |
|---|---|---|
| 200/400 | 2:1 | **−7.954** |
| 200/800 | 4:1 | −0.986 |
| 200/1600 | 8:1 | **−0.192** |

A-M6 derived −7.95 / −0.99 / −0.19 analytically and V-M4 measured −7.96 /
−0.99 / −0.19 on the ported nodes. Three runs, three methods, the same three
numbers.

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

Moved here under the length rule. §3 carries each row's claim, bar,
disconfirmation and measurement — that is what the gate reads — and the
**full statement as the seed wrote it on 2026-09-06**, with its source
reading and confidence reasoning, is here. Where the two differ it is
compression, never a change of claim: the Station A pass of 2026-09-07 did
not add, remove, retire or loosen a trait, and this table is the record that
says so.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| M1 | **Unity sum.** With every band at unity the summed magnitude is flat within **±0.25 dB** from 30 Hz to min(20 kHz, 0.45 × sample rate) — at two bands for **every** crossover setting, and at three bands for every setting whose crossovers are **at least 8:1 apart**, which the surface enforces (§6). *(Critic pass, 2026-09-06: the first draft claimed "every crossover setting" and it is false by construction — the parallel three-way sums to **−7.94 dB** at 400/800 Hz, a legal setting on the first draft's own surface. A-M6 has the ratio table.)* | S3 ("the outputs sum to unity at all frequencies"); the three-way floor derived and measured here (A-M2, A-M3, A-M6) | high | Any tone in the sweep beyond ±0.25 dB at a legal setting; a two-band sum that deviates at any setting; a three-band sum that deviates at 8:1 or wider; a surface that accepts a crossover pair closer than 8:1 | SUM at 40/8000, 200/2000 and the closest legal pair at each band count |
| M2 | **Each crossover is −6 dB at its corner with a fourth-order skirt**: at a 200/2000 Hz split each band is −6.0 ± 0.5 dB at its corner and its skirt fits 24 ± 2 dB/octave over the octave-to-two-octaves band on the side that lies below Nyquist; and the two halves are in phase there — summed with no polarity inversion the level at the corner is 0.0 ± 0.25 dB, not a null | S3 ("−6 dB crossover points"; "in-phase outputs (0° between outputs) at all frequencies"; LR-4 needs no inversion) | high | A −3.0 dB corner (plain Butterworth rather than LR4); a fitted skirt outside 24 ± 2 dB/octave; a corner more than 0.25 dB off unity in the sum, or a null there (the LR-2/LR-6 polarity case S3 names) | XOVER |
| M3 | **Band isolation.** Driving one band to 12 dB of gain reduction lowers that band's passband magnitude by 12.0 dB within 0.5 dB, evenly across the passband (no more than 0.5 dB of tilt from one passband edge to the other), and leaves every other band's magnitude within 0.5 dB of its idle value everywhere more than half an octave from a crossover; the test is run for each band in turn | S2 ("gain reduction is applied equally to all frequencies in the passband") | high | An idle band moving more than 0.5 dB when a neighbour compresses; a driven band whose reduction is more than 0.5 dB off 12 dB or tilted by more than 0.5 dB across its passband | ISO, once per band |
| M4 | **Zero latency.** The dry-to-wet path adds no samples at any setting: an impulse emerges in the frame it entered | S3/S4 (an IIR crossover delays phase, not onset); measured on the shipped class (A-M4) | high | Any non-zero click offset; a partitioned or FIR crossover being chosen instead | CLICK |
| M5 | **The sum survives its source.** M1 holds whatever block size the source hands out: with the same probe delivered as 256, 8192, 16384, 20000 and 32768-frame `get_buffer` calls, the rendered output is byte-identical across all five and non-silent in all five | derived — no external source; the failure is measured at A-M5, where three of those five give exactly zero non-zero samples on the shipped class | high | Any of the five renders differing from the 256-frame one; any of them silent; a non-zero-sample count that falls as the source's buffer grows | LONG |

### App. D — §7 in full, the seed's reading of each defect

Moved under the length rule; nothing deleted. §7 carries the finding and the
rebuild's answer, which is what the gate checks.

- **The source goes straight into the Splitter** (`dynamics.py:239`) — a
  source handing back more than 8192 frames loses the head of every buffer,
  which on head-loaded material is the whole signal (A-M5). *The rebuild puts
  a block-sized guard in front (§4).*
- **No surface, nothing live.** `MACRO_LABELS = ()` (`:232`),
  `PATCHES = {0: ("Default", ())}` (`:234`), everything constructor-only
  (`:236-238`), attack and release hard-coded (`:267`), no make-up, no output
  gain, no mix. *Fourteen macros, five patches (§6).*
- **A dead parameter.** `def band(tap, biquads)` (`:242-243`) never uses
  `tap`; three call sites pass one (`:254-256`). *`_band_chain(band)` uses its
  argument.*
- **Mismatched block sizes with nothing saying why**: 2048 / 1024 / 256
  (`:243`, `:262`, `audioif_dynamics.h:32`). *One block size, 256 frames.*
- **The docstring's flatness claim is measured nowhere** (`:223-226`). *M1 is
  measured at six settings and shown red on a planted fault.*


### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

**Three passages below are superseded and kept anyway**, because nothing is
deleted: the §3 Tier 3 paragraph's `" - lean"` **patch** (it is a constructor
option — §8.5), the §4 paragraph mapping the crossover onto
`audiofilters.Filter` over a `synthio.Biquad` cascade (it is `audiobiquad` —
App. P, P1), and the §5 note that the palette's detectors are peak (RMS
landed — App. P, P3). Each is marked where it sits.

*(from the preamble)*

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

*(SUPERSEDED in part — the lean build is a constructor option, not a patch;
§8.5. The budget itself stands.)* Budget as a fraction of one stereo block's
real-time deadline: ESP32-P4 **25 %**, ESP32-S3 **45 %**. Lean patch
expected: **yes** — a `" - lean"` patch drops to two bands (one crossover, four biquads, two detectors), which
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

*(SUPERSEDED — the crossover is `audiobiquad.Biquad`; the ported cascade
cannot reach Tier 1's tail invariant, App. P, P1.)* The topology is
`audioroute.Splitter(taps=n)` → one `audiofilters.Filter` per
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
- *(SUPERSEDED — `detector="rms"` landed with the node's twenty-one options;
  App. P, P3.)* **Not asked for:** RMS detection per band. S2's Fig. 7 shows
  RMS detectors, and the palette's are peak (`audioif_dynamics.c:265`) — but M1–M5 do not
  depend on the detector type, and the ask already exists as `Expander`'s
  N-EXP-1. Recorded here so the survey counts it once.
- *(SUPERSEDED in part — `audiobiquad.AllPass` exists; it is first-order and
  so is still not the section the correction needs, App. P, P2.)* **Not asked
  for:** an all-pass biquad. `synthio.FilterMode` offers
  LOW_PASS, HIGH_PASS, BAND_PASS, NOTCH, PEAKING_EQ, LOW_SHELF and HIGH_SHELF
  and no all-pass (read from the CPython build this run), so closing M1's last
  0.12 dB by the textbook three-way correction would need one. M1 is met
  without it, so no ask is filed; §8.1 records the choice, and the EQ family's
  Gate 0 biquad decision is where an all-pass would properly be argued.
