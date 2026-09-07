# The measurement kit — specification

**Program:** the effects rewrite (anchor `docs/effects-vision.md`,
`docs/effects-roadmap.md`). This is Phase 0's **measurement-kit spec** Work
item. Phase 1 builds what is specified here; every family phase's class gate
runs it.
**Written:** 2026-09-07, in the Phase 0 run that began 2026-09-06, from the
46 dossier seeds under `docs/effects/`.
**Status:** spec, refuted once. Nothing in it is built yet.

**Refutation pass, 2026-09-07.** Every measurement below was re-read against one
question — *would its planted fault actually turn it red?* Six would not (WIRE,
TAIL, CURVE, IFREQ, TRUEPEAK, ROUNDTRIP) and are rewritten; the row census, one
piece of arithmetic and one measured pair were wrong and are corrected against
the sources; a fourth axis, a twentieth measurement and seven probes were
missing and are added. What the pass could not settle is in §8.

The seeds' Tier 2 tables carry a Measurement cell per trait — **332 rows
across all 46 files**. (The first draft counted 275 + 37 and missed
`Compressor.md`'s 21 entirely: it is the one seed whose Tier 2 traits live in
four per-character sub-tables, so a census keyed on a single table per file
walks straight past the largest trait set in the program.) Read together they
name **twenty distinct measurements**, not three hundred. This document
specifies those twenty, says which existing tool carries each, and gives each
one the planted fault that must turn it red.

**The seeds already name their own measurements, and three names collide.**
`AutoPan`, `DeEsser`, `Expander`, `NoiseGate`, `MultibandCompressor` and
`Compressor` each define a short vocabulary in a paragraph above their table —
`ENV`, `LAW`, `KEY`, `ONESHOT`, `SPLIT`, `SUM`, `XOVER`, `ISO`, `LONG`,
`BLOCK`, `XF`, `REL`, `ATT`, and a *paired build*. Most map onto the twenty
below, but three names carry two meanings and a class gate reading only one
document will resolve them wrong: **`ENV`** is the amplitude envelope in
`AutoPan` (→ ENVELOPE) and the gain-reduction trace in
`NoiseGate`/`Expander`/`DeEsser` (→ GAINTRACE); **`LEVEL`** is a Tier 1
invariant here and a sibilance gain-reduction trace in `DeEsser`; **`CLICK`**
is Tier 1 latency here, an impulse-against-dry in `MultibandCompressor`, and a
zipper-artifact spectrum in `NoiseGate`. Phase 1 resolves every cell to a name
in this document, and where the two disagree this document's name wins.

---

## 1. Four axes, not three hundred measurements

Every measurement takes four parameters and records them in what it exports.
They are axes over the whole kit, never measurements of their own: **sample
rate** (48 000 / 44 100 / 22 050 Hz — Tier 2 at the first two, Tier 1 at all
three); **`channel_count`** (2 and 1, where a stereo-by-definition class states
in its dossier §4 what a mono source gets and the kit measures *that
statement*); **interpreter** (CPython and desktop MicroPython, plus the
patched CircuitPython build where the class's nodes exist); and **source block
size**, the number of frames the source hands back in one `get_buffer` call.

That fourth axis is not cosmetic and was missing from the first draft.
`MultibandCompressor.md`'s A-M5 measures the shipped class returning **zero
non-zero samples** from 16384-, 20000- and 32768-frame sources: the Splitter's
ring is 8192 frames and a longer write drags every cursor past the head
(`audioif_splitter.c:34-39`), while `audiocore.RawSample.get_buffer()` hands
back the whole array in one call. A kit that loads a probe WAV into one
`RawSample` therefore renders **silence** for the entire split family and calls
it a measurement. Every render states its block size; M5's five values (256,
8192, 16384, 20000, 32768) are the ladder, and TAPS' `_core.pcm()` 2048-byte
buffer is a sixth point on the same axis.

**The render is dual-runtime; the analysis is not.** The renderer is
stdlib-only and runs under both interpreters, writing WAV plus a digest. Every
FFT, fit and envelope runs afterwards on the desktop under CPython with numpy.
The kit never asks MicroPython to do an FFT — the one exception being the
board cost runner, whose arithmetic is a division.

**No measurement reads a silent render.** COST and ROUNDTRIP refuse one
explicitly below, but the rule is the kit's and not theirs: every measurement
asserts the render's FNV digest is not the digest of silence *before* it
analyses. Absence reading as agreement is this workspace's signature failure and
A-M5 is a live instance of it — silence produced on exactly the probe material
this kit is specified to use. The exceptions are the measurements whose subject
*is* an absence (TAIL's decay to zero, NULL's floor), and each states its own
floor instead.

---

## 2. What already exists, and is reused rather than rebuilt

Read `docs/agent-knowledge/vst3-test-infrastructure.md` before adding
anything: this workspace has rebuilt its own comparator and its own renderer
once each already.

| Existing | What the kit takes from it |
|---|---|
| `tools/render_component.py` | The renderer's *shape*: stdlib-only, dual-runtime, events delivered on block boundaries, streamed to disk and hashed incrementally (`render()` at `:39`, `wav_header()` at `:29`). Its instrument modes are not reused. |
| `tests/test_cpython_effects_library.py` | Its **analysis primitives**, which are already numpy-free and portable: `_fft` (`:143`), `spectrum` (`:121`), `harmonic_db` (`:174`), `rms`/`peak` with the detector `skip` (`:90`, `:63`), `tone_gain_db` (`:103`), `tilt_db` (`:112`), `sine` (`:80`), `burst` (`:192`), `channels` (`:204`), `loudest_in` (`:214`). These move into the kit's analysis module. |
| `tools/measure_hits.py` | `load_wav` (16/24/32-bit), `envelope()`, and the least-squares log-envelope τ→T60 fit — the DECAY measurement's estimator, already written. |
| `tools/measure_voice_headroom.py` | The cost method entire: `time.ticks_us` around a fixed block count, audio-seconds ÷ wall-seconds as a real-time factor (`:78`–`:88`, `:138`), `gc.collect()` before timing, a ladder that stops when it fails, and the honest caveat that no I2S device was opened. |
| `tools/compare_rig.py` + `tests/test_rig_comparator.py` | Not the code — the **discipline**. A comparator needs a floor (`SILENCE_FLOOR_DB = -60.0`, `:36`) or two silences agree, and a fault battery needs a control that must pass (`test_identical_renders_pass`) or the suite only proves the checker always fails. |
| `audioif/tests/parity/effects_component_probe.py` | `checksum()` at `:15` — FNV-1a over the bytes, with the comment saying exactly why `sum(data)` is blind. The kit's digest is this function, unchanged. |
| `tests/parity/effects_library_smoke.py` | Already walks the whole catalogue on three interpreters and exports nothing. It becomes the renderer's driver (roadmap Phase 1 rewrites it to go through `create()`). |
| `tools/spice/ts808/` | The oracle side: netlist → `wrdata` → CSV (`out/*.csv`), `analyze.py` reads it with numpy only. Tier 2 traits with a SPICE source are checked against these CSVs; the kit reads them directly and does not re-derive them. |
| micropython-vst3 `reaper/verify_song.py`, `tools/harness.py` | The dead-air and peak-sanity checks, and `EffectRun` as a CPython stand-in. Consulted before writing anything new that resembles them. |
| `audioif/lib/audiorender/` | The **event schema and the transport** — the two things §8 listed as unsettled and this workspace had already settled. `events.py:27` `build_events(..., block=256)` returns plain number tuples, so a timeline is serialisable where a closure would not be; `events.py:79` `deliver(instrument, event, sample_position)` is the delivery seam; `tempo.py:12` `TempoMap` is the transport stub `Rack.md` R7 asks for and STATE's `tempo_sync` clause needs something to read; `wav.py:8` `write_wav`. The render loop itself is **not** reusable — `audiorender` is numpy-throughout and desktop-only on purpose — but omitting the row was the documented mistake repeating: `docs/agent-knowledge/vst3-test-infrastructure.md` records this repo proposing a renderer with source/timeline/sink seams once already while that directory held the first two. |

**`tools/measure_effect_cost.py` is a flag, not a file.** Its method is
`measure_voice_headroom.py`'s entire — `_render` at `:78`, `gc.collect()` at
`:81`, `ticks_us` at `:82`–`:88`, the real-time factor at `:138`. A second file
carrying the same loop under a new name is the third entry in this workspace's
rebuild ledger; the subject (a voice ladder, or one effect class or node) is an
argument to the tool that already exists.

**`test_cpython_effects_library.py` — what survives and what is discarded.**
Survives: the primitives above, and the *shape* of a dozen assertions that
become parameterised measurements — the bell-centre read, the −3 dB corner
crossing, the ISO-centre band walk, the multiband sum-to-a-wire, the lookahead
overshoot, the true-peak read, per-repeat darkening, ping-pong alternation,
the emptied delay line, ring-mod sidebands, `Rack`'s latency/tail sum.
Discarded: every test asserting the **old surface** (saturation characters,
`amount` scaling, tape-vs-console tilt, the overdrive knob, `bit_depth=`, the
octaver's reach, the analog-delay comparison) — roadmap Phase 1 already splits
those out so each family phase retires its own. Discarded too: the
module-level `configure()` at `:22`, and `spectrum()`'s hardcoded
`SAMPLE_RATE / float(size)` bin width at `:140`, wrong the moment a
measurement takes its rate as a parameter. All of it is pass/fail at one rate
exporting no numbers; the kit exports numbers with units and a stated rate.

---

## 3. The probe material — `tools/effect_probes/`

A fixed set, committed as data, generated once on CPython by
`tools/effect_probes/make_probes.py` and never recomputed on a board (the ESP32
ports are single-precision). One manifest, `probes.json`, names each probe,
its rate, its length, its level and its FNV digest, so a stale probe cannot
be mistaken for a fresh one. Every probe exists at all three rates and at
`channel_count` 1 and 2.

| Probe | What it is | Feeds |
|---|---|---|
| `impulse` | one full-scale sample, then silence | CLICK, TAPS, DECAY, RESPONSE (IR route) |
| `click_stereo` | the same, identical in both channels, at a known offset | CLICK, TAPS, STEREO |
| `click_train` | 20 ms spacing | TAPS (splice periods) |
| `sine_<f>_<L>` | steady sines, f ∈ {100, 440, 1 k, 5 k} Hz and the trait's own f, at −6, −14, −26, −40, −60 dBFS | SPECTRUM, CURVE, ENVELOPE, IFREQ |
| `sweep_log` | 20 Hz–20 kHz log sweep, 4 s, −40 dBFS default | RESPONSE |
| `tones_step` | 1/6-octave stepped tones, **30 Hz–20 kHz**, each held long enough for the class's own detector to settle (0.25 s is the floor, not the value) | RESPONSE (stepped excitation), and the seeds' SUM / SPLIT / XOVER / ISO |
| `staircase` | 1 kHz sine, 1 dB steps, −80 → −10 dBFS | CURVE |
| `burst_silence` | 200 ms burst then 3 s silence | TAIL, GAINTRACE, DECAY |
| `dc_step` | ±0.5 FS held 5 s, then removed while the source still supplies frames | TAIL (the audioif#23 shape) |
| `alt_fs` | ±FS alternating (Nyquist) | TAIL, RESIDUAL |
| `ramp_fs` | full-scale ramp | WIRE |
| `noise_det` | deterministic PRNG, fixed seed | RESPONSE (averaged), RESIDUAL |
| `chord` | one held instrument chord from `audioinstruments` | DIGEST, COST |
| `hit_levels` | one recorded percussive hit at −6/−20/−40/−60/−80 dBFS | GAINTRACE, TRUEPEAK |
| `square_<f>_<L>`, `train10_<f>_<L>` | a square, and a 10 %-duty bipolar train, generated in matched-RMS **and** matched-peak pairs with `sine_<f>_<L>` | the crest-factor rows: `Compressor` V3, `Expander` and `DeEsser` XF, `NoiseGate` G6 |
| `sibilant` | 200 Hz + 6 kHz at a fixed amplitude ratio, at −6/−20/−40/−55 dBFS | `DeEsser`'s LEVEL |
| `tone_fs4` | a tone at exactly f_s/4 with **π/4 phase** — S1's worst case — at 48 kHz and 44.1 kHz | TRUEPEAK; `Limiter` L1 fails its own disconfirmation clause on a probe set without it |
| `step_over` | a 1 kHz tone stepping from silence to N dB over a stated threshold, N ∈ {10, 20, 30} | GAINTRACE: `Compressor` V2's three published attack points |
| `burst_train` | ten 10 ms bursts at 200 ms spacing, each reaching a stated GR depth | GAINTRACE: `Compressor` M3's program dependence |

Levels are stated in dBFS and generated to land on exact int16 values where a
trait's tolerance is tighter than an LSB. **Frequency, level and phase are the
trait's to name; the fixed sets above are defaults, and three seeds already
fall outside them.** `StereoWidener` W6 needs −12 dBFS because L′ reaches
+3.52 dB at w = 2 and a full-scale probe would clip the measurement rather than
the class; `Overdrive` T1 needs −72 dBFS, where the diode pair's own level
dependence reads the plateau 0.12 dB low against 2.3 dB at −60 dBFS, and states
its own convergence rule (halving the level must move every reported point by
less than 0.3 dB) — a rule the probe table cannot express and the measurement
must carry. The first draft's `tones_step` (1/12-octave, 50 Hz–10 kHz, a fixed
0.25 s) could not serve `MultibandCompressor`'s SUM (1/6-octave, 30 Hz–20 kHz)
or `DeEsser`'s SPLIT (1/6-octave through a detector) at all.

---

## 4. The renderer — `tools/render_effect.py` (new)

One file, stdlib-only, in `render_component.py`'s shape:

```
render_effect.py <Class> <probe> <outdir> [--rate 48000] [--channels 2]
                 [--block 256] [--macro n=v ...] [--patch n]
                 [--events events.json] [--transport tempo.json]
```

Builds through `create(source, sample_rate, **options)` — never the
module-level `configure()`, never a `patch=` keyword — applies macro and
patch events on block boundaries, streams PCM to a WAV and returns an FNV-1a
digest of the PCM bytes (header excluded). `--block` is §1's fourth axis — the frames the probe source hands back per
`get_buffer` — and it is recorded in every export, because a render that does
not state it cannot be compared with one that does. `--transport` advances a
tempo stub (`audiorender/tempo.py:12`'s `TempoMap` is the model) so `Rack` R7
and STATE's `tempo_sync` clause have something to read; without it neither row
is measurable. It runs under
`audiocomponents/.venv/bin/python`, under
`MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython`, and
under `../cmods/bin/circuitpython`, from the one file.

Analysis lives beside it in `tools/effect_analysis.py` (the primitives lifted
from the test file, rate-parameterised) with a CLI `tools/measure_effect.py`
that runs one named measurement over one render and writes JSON: value, unit,
rate, channel count, interpreter, probe digest, class version.

---

## 5. The twenty measurements

Format: **name** — traits served · probe · algorithm · exports · tool ·
**planted fault**.

### Tier 1 — the invariants

**WIRE** — the bypass invariant (mix 0, depth 0, drive 0). `ramp_fs` and
`chord`. Byte compare of the render against the source, both channels.
Exports: differing sample count, first differing offset. New, in
`measure_effect.py`. **Planted fault:** scale the dry path by 32767/32768 —
one LSB — **on `ramp_fs`, which is required and not one of two options.**
Worked here rather than assumed: under round-half-to-even, `v·32767/32768`
returns `v` for every `|v| ≤ 16384`, so the faulted render is *byte-identical*
to the clean one on any material peaking below −6.02 dBFS, and `chord` alone
would pass it green. That is the material-cannot-reach-the-mechanism shape,
planted inside the kit's own control. On the ramp the byte compare must go red;
an RMS or dB check would not see it even there, which is why this measurement is
a byte compare. **The compare is against the source delayed by the class's
reported `latency_samples`** — a class carrying a convolver partition or a
lookahead is not a wire at sample zero, and a wrong report is CLICK's to catch,
not WIRE's to absorb.

**TAIL** — silence-in/silence-out, decay to *exact* zero, `tail_samples`, and
the held-DC class of defect (audioif#23). `burst_silence`, `dc_step`,
`alt_fs`. Last non-zero sample index after the burst; settled value of the
step; the same read while the source still supplies the offset **and** after
it is removed. Exports: tail length in samples, residual in LSB.
`measure_effect.py`. **Planted fault:** add +1 LSB of DC to the node's state
after settling — the real audioif#23 residue (LowPass 100 Hz reads +1 LSB,
40 Hz/q=8 −4 LSB). Red on residual. The first draft claimed the tail-length
readout stays green and treated that as this measurement's own control; it does
not. A state that never returns to zero has no last non-zero sample, so tail
length goes red as well, on `burst_silence` as much as on `dc_step`. The control
is a separate **unfaulted** run of the same measurement (§6), never a second
readout of the faulted one.

**LEVEL** — level-honesty: unity through the dry path, no hidden gain.
`sine_1k_-26`, `noise_det`. Wet:dry RMS and peak ratio at mix 0 and at the
class's unity setting. Exports: dB, both channels. `measure_effect.py`.
**Planted fault:** +0.1 dB on the dry path. Red at a 0.05 dB bar. At mix 0 this
is strictly weaker than WIRE, which catches a one-LSB change where this bar is
0.05 dB; the mix-0 leg is kept only as the readable number beside WIRE's offset,
and the measurement's own subject is the **wet path at the class's unity
setting**.

**CLICK (latency)** — reported `latency_samples` against measured, at 48 kHz
**and** 44.1 kHz, per vision §9a. `click_stereo`. Onset of the class's output
against the onset of its dry path, to the sample; sub-sample by parabolic
interpolation on the energy envelope where a fractional delay exists.
Exports: latency in samples and ms at each rate, per channel, per patch, and
the reported value beside it. `measure_effect.py`. Also re-run with every
latency-adding option (convolver partition, `Dynamics` lookahead, pitch
window) turned on one at a time, to check each defaults off or shortest.
**Planted fault:** report `latency_samples` 256 short while leaving the DSP
alone. Red at both rates; the audio digest unchanged, so nothing else fires —
a latency check that only fires when the sound also changes is not a latency
check.

**STATE** — `reset()`, `deinit()`, `capabilities`, and the no-allocation rule.
`burst_silence` then `reset()`; `chord` then `deinit()`. Reads, in this order:
render `burst_silence`, call `reset()`, **swap the borrowed source for a silent
one**, pull — the output must be exactly zero, and the original source must
still render when handed back. (The first draft asked for both at once, which is
red on a correct build and gets loosened by the first person to run it.) Then:
every node the class enumerated is deinitialised; `capabilities` declares
`"tempo_sync"` iff a transport read changes the render, which needs `--transport`
(§4); `gc.mem_alloc()` / `tracemalloc` across 200 pulls is flat **on a render
whose digest is not the digest of silence**, since a class that allocates
nothing because nothing was pulled is flat too. `Limiter` L5's constructed-state
read — defaults at all three rates: `latency_samples` 0, every latency-adding
option off or at its shortest — is this measurement's, not a twenty-first.
`measure_effect.py` + `tests/test_effect_kit.py`. **Planted faults**, both
named by the vision: a delay line left full after `reset()`; an
intermediate node left live after `deinit()` — plus an upstream instrument
reset through a Filter- or Phaser-tailed chain, where the ported-versus-own
recursion difference bites (roadmap §3).

**DIGEST** — CPython and desktop MicroPython render identical bytes; P4 and S3
digests match the desktop's or carry a recorded cause. `chord`, `noise_det`,
`sweep_log`. FNV-1a over the PCM bytes — `effects_component_probe.py:15`,
used unchanged. `sum(data)` is printed alongside only so older
per-architecture records stay comparable; it is **never** the comparison.
Exports: digest per interpreter per board per rate **and per source block
size**. `render_effect.py`.
**Planted fault:** the documented blindness — perturb one sample by +256 LSB
and another in the same block by −1 LSB. Computed here rather than recalled: the
unsigned-byte sum moves by **exactly zero** — the +256 raises one sample's high
byte by one, the −1 lowers another's low byte by one — which is the probe
docstring's own claim and a stronger statement than the first draft's "moves by
255". FNV must go red. Float width is the only accepted cause of a board/desktop
difference (`docs/accuracy-roadmap.md:612-616`), never the class.

**Three comparison modes, not one.** (a) Cross-interpreter and cross-board, as
above. (b) **Build against build**, which the seeds already ask for and the
first draft had no place for: `GraphicEQ` T4 ("FNV digest of both builds over
the full probe set, at 48 and 44.1 kHz"), `Rack` R3 and R6, and `Compressor`'s
*paired build*, where the two renders differ only in where the detector reads
and **the comparison fails on an ordering, never on a magnitude** — so the
export is the ordering, not the digests alone. (c) The same class and settings
at two source block sizes: `MultibandCompressor` M5 requires byte-identical
output from 256-, 8192-, 16384-, 20000- and 32768-frame sources, and its planted
fault is red on today's build already. A digest cannot express a floor, so a
comparison that needs one is NULL, below.

### Tier 2 — the circuit traits

**RESPONSE** — magnitude, phase and group delay against frequency; the
most-used measurement in the seeds (corners, skirts, Q, tone stacks, notch
depth and tracking, cabinets, crossovers, per-repeat filtering, warped-axis
symmetry). Two excitations with a **stated selection rule**: `sweep_log` by
default; `tones_step`, one steady tone at a time, wherever the class holds a
detector or a rotating source that a sweep would move while it measures (the
DeEsser, the compressors, `Rotary`). Extractors on top of the curve: −3 dB
crossings by interpolation, local extrema, least-squares skirt slope over a
named octave pair, response folded onto log(f/f₀), and a ratio mode dividing
one render by another of the same class where the read interpolator's own loss
must divide out. Smoothing, where used, is part of the measurement and stated.
Exports: dB and degrees on a named grid, beside the closed form where one
exists and the `tools/spice/` CSV where one exists. New, `measure_effect.py`.
**Planted fault:** move one coefficient so a corner shifts 15 %; the fitted
corner goes red while the passband gain stays green. And a second, which
proves the *selection rule*: run the swept excitation on the DeEsser and show
it returns the wrong band edges — the reason `tones_step` exists is a measured
one, not a preference.

**A third excitation, and a moving read.** `Phaser` P1 and `Flanger` F2 measure
a *white-noise transfer per STFT frame* — 16384-point Hann, 2.93 Hz bins at
48 kHz, both notch centres tracked across one LFO period — and `AirSpace` AS7,
`Bitcrusher` T5, `Exciter` T7, `Octaver` O2 and O6, `LadderFilter` T4,
`PitchShifter` T3, `Harmonizer` H2 and `ShimmerHall` SH1/SH2/SH4 each name an
STFT rather than a static curve. Fourteen Tier 2 cells do; a static-curve-only
RESPONSE cannot serve them. The frame length is part of the measurement and is
exported with the result, together with the lowest feature it can carry:
`Flanger` F1 states the trade in one line — at 12 ms the first comb notch is
41.7 Hz, which a frame short enough to track a sweep cannot resolve.

**And the selection rule has an exception the first draft forbade.**
`NoiseGate` G3 and `Expander` E3 (their `KEY`) deliberately drive a detector
with a swept sine at fixed amplitude and read the gain-reduction trace. That is
legal when the sweep rate is slower than the detector's release, and the sweep
rate is then a stated parameter of the measurement. The rule is *name the sweep
rate against the detector's release*, not *never sweep a detector* — as written,
the first draft's rule would have sent two seeds' rows to a probe that cannot
express what they measure.

**SPECTRUM** — one FFT, three readouts: **harmonic** (h2…hN re fundamental,
THD), **inharmonic** (alias floor: every bin more than two bins from a
harmonic and from DC, summed against the fundamental), **sideband** (ring
modulation, FM). Probe `sine_<f>_<L>`, length chosen so the fundamental lands
on an exact bin (no window), or Blackman–Harris where sidebands are dense.
Exports dB re fundamental per named line and the alias floor, per rate, **with
the window, the transform length and the harmonic count N stated**: `Compressor`
F5 defines its THD as h2..h10 re fundamental, `Octaver` O2 and `PitchShifter` T3
each name a 65 536-point Hann, and a THD figure without its N is not comparable
to the source it is checked against. A fourth readout: **block-rate lines** —
`AutoPan` A3's `BLOCK` reads the sidebands a per-block rather than per-sample
modulator leaves at multiples of the block rate on a 1 kHz tone. That readout is
a measurement of §1's block-size axis and moves when it does. Built
on `harmonic_db`/`spectrum`, rate-parameterised. **Planted fault:** inject a
−35 dB second harmonic into a class whose trait says h2 ≤ −60 dB. Red on the
harmonic readout, green on the alias readout; for the alias readout, turn the
oversampler off.

**CURVE** — static level-in/level-out: drive laws, clipping,
compressor/expander/gate static curves, knee, threshold, ratio,
output-peak-versus-input-peak. `staircase` and `sine_1k_*` at five levels.
Output RMS or peak per step over the settled half of each render; local slope
by finite difference against measured gain reduction. Exports dB out vs dB in,
fitted slope, knee width, threshold, **and the fit residual beside every fitted
number** (`Compressor`'s shared definitions require it, and a knee point that
moves by less than its own residual is not a finding).
**Planted fault:** replace the soft knee with a hard knee at the same threshold
and the same asymptotic ratio. The fitted knee width goes red while the
threshold and the slope above it stay green — a fault that fires on part of the
readout and not all of it. (The first draft planted a clamped drive control and
named the red readout *THD monotonicity in Drive*. That is SPECTRUM's readout,
not CURVE's: a planted fault whose red appears in a different measurement leaves
this one unproven. The clamp survives, as SPECTRUM's second fault.)

**GAINTRACE** — gain reduction against time: attack, release, hold, two-stage
release, one-shot envelopes, lookahead overshoot, transient shaping.
`burst_silence`, `hit_levels`. Per-block (per-sample where a trait needs it)
ratio of output envelope to input envelope in dB; 10–90 % transitions, **t50**,
t63, t95 — `Compressor` O1 and O2 are stated in t50/t95, not t63, so all three
are exported. Exports the trace and the named times in ms, on `measure_hits.py`'s
envelope.

**A level search, because many rows are stated at a gain-reduction depth rather
than at an input level** — "after a 10 s tone holding 10 dB of GR stops"
(`Compressor` O1), "at 3, 10 and 20 dB of GR" (V6), "12 dB of reduction"
(`DeEsser` REL). The measurement bisects the input level until the settled GR is
within 0.1 dB of the target and exports the level it found beside the trace.
Without it those rows are not measurable at all. Renders are deterministic, so a
*repeat spread* is exactly zero unless a measurement resamples — which is what
makes `Limiter` L2's "no higher than the peak at 0 ms plus the measurement's own
repeat spread" a strict comparison here, and it is exported as one. **Planted fault:** collapse a two-stage release to one stage at the
fast constant. t95 red, t63 green — a fault that fires on part of the readout
and not all of it.

**ENVELOPE** — the amplitude envelope of a carrier tone, and everything read
off it: depth in dB, duty, steepest slopes, harmonics of the modulation rate,
inter-channel phase **with its sign**, the extracted LFO rate itself, and rate
tracking across a speed change (sliding window). `sine_1k_-6` over ≥ 8
modulation periods, or ≥ 20 rotations where the trait is a rotor's.
Peak-track at 1 ms hop, then a **least-squares fit of the rate component** —
never max-minus-min, which reads the noise floor. The record length is part of
the measurement: rate resolution must be finer than the trait's tolerance
(120 s at 0.667 Hz to resolve ±2.5 %; a 20 s record passes anything). Where a
seed's own cell names a shorter record than this rule requires — `AutoPan` A3
says four LFO periods — the rule wins and the cell is resolved to it in Phase 1.
Exports: depth dB, rate Hz, duty %, slope ratio, harmonic dB, φL−φR degrees.
`measure_effect.py`. **Planted fault:** replace the shaped LFO with a pure
sine at the same rate and depth. Rate and depth stay green; duty, slope ratio
and the rate harmonics all go red — the control and the fault in one run.

**IFREQ** — instantaneous frequency from the analytic signal: doppler, wow and
flutter, vibrato, pitch-shift ratio, per-repeat pitch. `sine_440_-6` held, or
`click_stereo` through a feedback path. Hilbert transform, unwrapped phase
derivative, least-squares sinusoid fit at the rate ENVELOPE extracted. Exports
fitted peak deviation in cents and Hz, residual RMS, second-harmonic ratio.
Where a granular shifter is in the path the splice-period correction is
applied before the reading and stated — uncorrected, the measurement cannot
pass on a correct build. **Planted fault:** omit the splice-period correction where a granular shifter is
in the path, and watch a **correct** build read red. That is the fault worth
planting here, because the first draft's — hold the modulation depth at zero
while the class still reports it — is an inert modulator: it flattens every
readout at once and proves only that the measurement notices nothing happening,
which is the always-red shape §6 forbids. The class-side pair is already in the
seeds: `PitchShifter` T3 pins the kernel's `read_rate` at
`audioif_pitchshift.c:51` so the ratio is unity while the class still reports 2,
and T4 forces the splice period to a whole number of frames. The control that
must pass beside them is the same measurement on a path with no shifter in it,
where the uncorrected reading must stay green.

**TAPS** — arrival structure. Delay time against the mapped value, per-repeat
arrival and level, inter-channel arrival difference, comb spacing from the
impulse spectrum, splice period. `impulse`, `click_stereo`, `click_train`.
Onset detection per repeat with sub-sample interpolation; comb spacing fitted
from a zero-padded magnitude spectrum (20 s of padding → 0.05 Hz bins).
Exports: lag in samples and ms per tap, level per tap, spacing in Hz.
`measure_effect.py`. **Planted fault — the model for the whole kit,** because
it is already measured rather than hypothetical: build the line on
`audiodelays.Echo(freq_shift=False)` at `_core.pcm()`'s 2048-byte buffer. The
1, 5 and 14 ms settings all deliver 21.33 ms and must go red, while 30 and
40 ms stay green. Note the load-bearing detail: with the node's default
`freq_shift=True` there is no floor and every setting lands within 0.02 ms —
plant it that way and the fault does not fire, and the checker is one that
cannot fail.

**DECAY** — how a tail evolves: per-pass darkening, RT60/EDR, echo density,
per-repeat band energy. `impulse`, `burst_silence`. Hilbert envelope,
Schroeder backward integration for EDR, `measure_hits.py`'s least-squares
log-envelope τ/T60 fit, three-band energy share per repeat. Exports T60 per
band, per-repeat band shares in dB, echo density in events/s. **Planted
fault:** apply the darkening once at the input instead of inside the loop.
Repeat 1 stays correct; the *progression* goes flat and red — the fault a
single-repeat check cannot see.

**STEREO** — the stereo field. L−R RMS, mono sum against the source,
correlation, width, per-channel arrival and level. `click_stereo`,
`noise_det`, `sine_1k_-6`. **The probe must be identical in both channels**,
or L−R is not silent at width zero and a correct endpoint reads as broken.
Exports: L−R in dBFS, mono-sum deviation in dB, correlation. **Planted
fault:** the seeds' own — measure down one channel instead of across both. A
ping-pong that is really two independent delays at half rate reads a plausible
0.36 and passes. The corrected measurement, interleaving repeats by time
across both channels, must go red on that build.

**RESIDUAL** — quantisation and decimation error: bit depth, sample-rate
reduction, dither. `sweep_log`, `alt_fs`, `noise_det`. Output minus an
ideally-quantised reference — mean and RMS residual per word length,
run-length histogram of held samples, peak-to-median of the residual spectrum,
swept magnitude against sinc(fT). Exports LSB, run lengths, dB. **Planted
fault:** replace truncation with rounding at the same word length. The RMS
barely moves; the **mean** goes to zero and fires, which is why the mean is
exported and not only the RMS. That holds for *floor* truncation only.
Truncation **toward zero** also has zero mean on material symmetric about zero,
so on `sweep_log`, `alt_fs` and `noise_det` the fault would not fire and a
rounding build would read as a truncating one. This measurement's probe
therefore carries a **DC offset** (a half-scale-biased ramp), where every
truncation mode leaves a mean and only round-to-nearest does not.

**TRUEPEAK** — inter-sample peak, BS.1770 4× oversampled. Serves limiter
ceilings and the level-honesty of any class that can overshoot. `hit_levels`,
`click_stereo`, **and `tone_fs4`, which is required**: `Limiter` L1 says in its
own disconfirmation clause that a probe set containing no worst-phase f_s/4 tone
reads green on a limiter with no true-peak detection at all. Exports: dB TP
against the ceiling, beside the sample peak.
**Planted fault:** read the sample peak instead of the oversampled peak.
Corrected against the seed's own measured pair (`Limiter.md:557`–`558`): the
palette reads **sample peak −6.00 dBFS / true peak −2.95 dB TP** with the flag
off, and **sample peak −7.93 dBFS / −4.88 dB TP** with it on. The two sample
peaks do *not* collapse to one number, so the first draft's stated red never
appears — the faulted measurement returns a different but entirely plausible
pair and passes. What appears instead is worse, and is the real fault: with the
flag off the sample peak reads **−6.00 dBFS, exactly its ceiling**, so the
faulted measurement certifies L1's +0.5 dB bar as met while 3.05 dB escapes in
the reconstructed waveform. The red is against the **ceiling in dB TP**, not
against the other setting.

**NULL** — one path defeated, and what must then vanish. The seeds ask for this
in four places and the first draft had nowhere to put it: `Octaver` O3 ("null
OCT1's modulator; OCT2 must fall below −80 dBFS"), `Phaser` P4 and P7 and P10
and `Flanger` F2 (each *control that must pass* is a null — `Mix` 0 must read
0.0 dB everywhere), and every paired build whose two renders must differ only in
the way the row names. Sample-wise difference of two renders of the same class,
reported as a level in dBFS against a **stated floor**. The floor *is* the
measurement: two silences agree without one, which is the lesson
`compare_rig.py:36` was written from. Exports: null depth in dBFS, the first
offset above the floor, and the digest of both sides. `measure_effect.py`.
**Planted fault:** the seed's own — re-wire OCT2 from the dry tap, and the null
must go red. The control that must pass beside it is the unmodified build, which
must null below −80 dBFS.

### Tier 3 and the platform

**COST** — CPU on the boards. Blocks per second **per class and per node**, on
the ESP32-P4 and the ESP32-S3, as a real-time factor. A **`--subject` mode of `tools/measure_voice_headroom.py`**, not a new file
(§2): its method entire, with one class or node per run instead of a voice ladder — `gc.collect()`,
`time.ticks_us` around a fixed block count, audio-seconds ÷ wall-seconds, and
its honest caveat carried forward (no I2S device opened, one class measured,
derate). It also renders `chord` through the class and prints the FNV digest
beside the CPU figure, so the same run produces the board leg of DIGEST.

Driven with mpftp per `docs/agent-knowledge/device-debugging.md`: `--follow`
for short runs, **write-to-file-then-`mpftp get`** for long ones, because
`--follow` discards everything it captured on timeout and a healthy board then
looks silent. Heartbeat every ~2 s against the ~10 s quiet timeout; hard reset
between runs with `/main.py` renamed aside, or autostart boots the app instead
of the probe; every connect interrupts the running program. `mpremote` is not
installed on this machine.

Exports: blocks/s, ms/block, rt factor, RAM, per class and node, per board,
per rate. **Planted fault:** run the cost table against a class whose output
is never pulled (or whose source returns silence immediately). It is the
fastest entry in the table, and "absence reads as agreement" is exactly the
shape that produces it. The runner therefore refuses a run whose render
digest is the digest of silence, and the planted fault is a muted class that
must be refused rather than ranked. **The probe must also reach the expensive
path**: a compressor idling below threshold, a drive stage at Drive 0 or a
reverb at Mix 0 costs what a wire costs and is a second way to rank fast
without being fast. The settings and the measured gain reduction the figure was
taken at are exported beside it.

**ROUNDTRIP** — the platform path, not the effect graph (vision §9a). Output
looped back to input on the board; a click through a **wire**, then through a
**five-effect chain**, at each buffer setting. The settings are named:
`sample_out.py:86`'s `chunk_ms` (40) and `lookahead_chunks` (2),
`audiodev.LOW_LATENCY_QUEUE_MS` (`__init__.py:46`, 100 ms) and the `ibuf`
bytes `queue_bytes()` derives from it, and capture's `queue_ms` — swept down
to the smallest that does not starve, with starvation **counted**, not guessed
(wrap the transport's write and count buffer-empty events). New:
`tools/measure_roundtrip.py`, board-side. Exports: round trip in ms per board
per setting, wire and chain, with the starvation count and the settings used;
compared against Phase 0's sourced target (working assumption under 10 ms).
**Planted fault:** run it with the loopback wire out, or analyse the playback
buffer instead of the capture buffer. The number collapses toward zero, so the
runner asserts a cross-correlation peak above a floor between the emitted click
and the captured one and refuses a run without it. **That guard catches the
first fault and not the second**, which is why the second is planted: correlating
the emitted click against the *playback* buffer is correlating it with itself,
which peaks perfectly at lag ≈ 0 and satisfies the guard while the reported
latency collapses. Two further conditions, both cheap: the analysed stream's
digest must **differ** from the emitted stream's, and the correlation peak must
sit at a lag above a stated floor of one block. A round-trip figure obtained
without a wire in the loop is the most expensive possible green; one obtained
from the wrong buffer looks exactly like it and, without these two, passes.

---

## 6. Planting the fault — the discipline this kit is held to

`docs/agent-knowledge/workspace-craft.md` names three ways a check fails to
fail, and each has a counterpart above:

1. **Absence reads as agreement.** Two silences agreed in `compare_rig.py`
   until a −60 dB floor was added. Here: **no measurement reads a silent
   render** (§1), COST refuses one, ROUNDTRIP refuses a run with no correlated
   capture *and* one whose analysed stream is the emitted one, NULL states a
   floor, and STEREO's probe is identical in both channels so silence at width
   zero means something.
2. **A summarising statistic cancels.** `sum(data)` over unsigned bytes hid a
   +256 LSB error paid for by −1 LSB. Here DIGEST is FNV-1a over the bytes,
   and its planted fault is that exact pair.
3. **The material cannot reach the mechanism.** A swept sine cannot measure a
   detector the sweep is moving. Here: RESPONSE's three excitations with a
   stated rule (and the sweep rate named against the detector's release, so the
   rule does not forbid `KEY`), ENVELOPE's record-length rule, TAPS'
   `freq_shift=False` note, DECAY's per-repeat progression, TRUEPEAK's required
   `tone_fs4`, RESIDUAL's DC-offset probe, COST's expensive-path clause — and
   WIRE, whose own planted fault is invisible below −6.02 dBFS and so names the
   probe it must run on.

   This was the pass's most common finding: **six of the nineteen planted
   faults in the first draft did not turn their own measurement red.** Three
   were the material (WIRE below half scale, RESIDUAL under truncation toward
   zero, TRUEPEAK's two sample peaks that do not collapse); one queried a
   mechanism the fault does not touch (CURVE's red appearing in SPECTRUM); one
   was always-red rather than partly red (IFREQ's inert modulator); one had a
   guard the fault walks straight past (ROUNDTRIP's self-correlation). A fault
   nobody has arithmetic for is a fault nobody has planted.

**Twenty-four Tier 2 rows already carry a planted fault or a control that must
pass of their own** — sixteen name a fault, eight a control: `AirSpace` AS3b,
`Distortion` SC4, `Flanger` F1/F2/F8, `Harmonizer` H1/H2/H3/H5, `Octaver`
O1/O2/O3/O6, `Phaser` P1/P4/P7/P10, `PingPongDelay` T2, `PitchShifter` T3/T4,
`Rack` R6, `StereoWidener` W1/W2/W6 — and `MultibandCompressor` M5 beside
them. Those are the *class's* and live in the class's
evidence pack; the twenty here are the *measurement's* and live in
`tests/test_effect_kit.py`. A class gate cites both. M5's is the one already
red on today's build, with V-M3 as the control that must pass — the shape to
copy.

Every planted fault lands as a test in `tests/test_effect_kit.py`, in
`test_rig_comparator.py`'s shape: **a control that must pass** beside the
faults, or the battery only proves the checker always fails. A measurement
whose planted-fault run is not committed is not one the class gate may cite.
Delete the artifact before re-running and confirm a fresh marker — a stale
render is worse than no render, because absence prompts a re-run and staleness
does not.

---

## 7. Summary

| Measurement | Traits served | Tool | Planted fault |
|---|---|---|---|
| WIRE | Tier 1 bypass | new, `measure_effect.py` | dry path × 32767/32768, **on `ramp_fs`** — invisible below −6.02 dBFS |
| TAIL | Tier 1 silence, DC, `tail_samples` | new | +1 LSB DC in the settled state (audioif#23); control is a separate clean run |
| LEVEL | Tier 1 level-honesty | new | +0.1 dB hidden dry gain |
| CLICK | Tier 1 `latency_samples`; vision §9a | new | report 256 samples short, DSP unchanged |
| STATE | Tier 1 `reset`/`deinit`/`capabilities`/alloc | new + `tests/` | delay line left full; intermediate node left live |
| DIGEST | cross-interpreter bytes; build-vs-build; block-size ladder | `effects_component_probe.py:15` | +256 LSB and −1 LSB in one block (unsigned-byte sum moves by exactly 0) |
| RESPONSE | filters, tone stacks, notches, cabinets, crossovers | new, from `spectrum`/`_fft` | corner moved 15 %; and sweep-vs-step on a detector class |
| SPECTRUM | THD, harmonics, alias floor, sidebands | new, from `harmonic_db` | −35 dB h2 injected; oversampler off |
| CURVE | drive laws, ratio, knee, threshold, peak tracking | new | soft knee replaced by a hard one at the same threshold and ratio |
| GAINTRACE | attack, release, hold, lookahead, transients | new, from `measure_hits.envelope` | two-stage release collapsed to one |
| ENVELOPE | tremolo, pan, rotor AM, LFO rate, ramps | new | shaped LFO replaced by a pure sine |
| IFREQ | doppler, wow/flutter, vibrato, pitch ratio | new | splice-period correction omitted — a correct build must read red |
| TAPS | delay time, repeats, ping-pong, comb spacing | new | `Echo(freq_shift=False)` on a 2048-byte buffer |
| DECAY | RT60/EDR, per-pass darkening, echo density | new, from `measure_hits` τ fit | darkening applied once at the input |
| STEREO | width, mono sum, correlation, arrivals | new | measure down one channel instead of across both |
| RESIDUAL | bit depth, decimation, dither | new | truncation replaced by rounding, **on a DC-offset probe** |
| TRUEPEAK | limiter ceilings, overshoot | new | sample peak instead of 4× oversampled — red against the *ceiling*, not against the other setting |
| NULL | defeated-path rows and the seeds' controls-that-must-pass | new | `Octaver` O3's — OCT2 re-wired from the dry tap |
| COST | Tier 3 CPU/RAM on P4 and S3 | a `--subject` mode of `measure_voice_headroom.py` | a muted class, which ranks fastest; and one idling below threshold |
| ROUNDTRIP | vision §9a platform latency | new, board-side | loopback wire out (correlation guard); playback buffer analysed (digest + lag guards) |

## 8. What this spec does not settle

The renderer's event format — but it is now a *choice*, not a blank:
`audiorender/events.py:27`'s serialisable tuple form exists and Phase 1 either
adopts it or says why not. The **transport** format the same way, against
`tempo.py:12`'s `TempoMap`. Which classes need
which measurements — that is each dossier's own Measurement column, and this
document is the vocabulary those cells draw on; Station A may add a
measurement here under the same planted-fault requirement. ROUNDTRIP's
smallest non-starving buffer settings, which are a Phase 1 measurement rather
than a Phase 0 assumption. And the latency target itself: vision §10.8's
sourced figure lands in the survey, working assumption under 10 ms.

**Left open by the refutation pass of 2026-09-07**, each of them a decision
rather than a gap in the argument:

- **The cell-by-cell resolution of the seeds' own vocabularies.** §1 names the
  three collisions; resolving all 332 Measurement cells to the twenty names is
  Phase 1's, and it is the moment a cell that no name serves will surface.
- **The cost of the block-size axis.** Five block sizes × three rates × two
  channel counts × three interpreters is a large product, and nothing here says
  which measurements run the full ladder and which run 256 and 16384 only.
  `MultibandCompressor` M5 runs all five because that is its trait.
- **GAINTRACE's level-search tolerance** (0.1 dB is written above and unsourced)
  and what it does on a class whose GR never reaches the target.
- **The `staircase` range against a high ceiling.** `Limiter` L6 wants 24 dB
  above the ceiling; at a −6 dBFS ceiling that is off the scale, so either the
  row's ceiling is constrained or the measurement states the clamp.
- ~~**`tools/probes/` next to the existing `tools/probes_scratch/`**, which holds
  SPICE netlist composers, not audio probes.~~ **SETTLED in this spec, 2026-09-07:**
  the probe directory is **`tools/effect_probes/`**, named here before Phase 1
  builds it, so the kit is never built against a directory this spec itself
  calls the naming half of a stale-artifact bug. `tools/probes_scratch/` keeps
  its name and its SPICE netlist composers; nothing named `tools/probes/` is
  created.
- **Whether COST's per-node figures can be taken at all** on nodes that only
  exist inside a class's graph.
