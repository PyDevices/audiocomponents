# What the effects palette costs, on both boards — the pre-node baseline

**Measured 2026-09-07** on the two boards in the room, with
[`tools/measure_effect_cost.py`](../tools/measure_effect_cost.py). Nothing has
been added to the palette yet: this is the "before" a native effects node has
to argue against.

Every number here was rendered on hardware. The tool is the same method as
`tools/measure_voice_headroom.py` — audio seconds produced over wall seconds
spent producing them, `time.ticks_us` on the board, no output device open.

## The boards

| | ESP32-P4 (COM4) | ESP32-S3 (COM49) |
|---|---|---|
| `os.uname().machine` | `Generic ESP32P4 module with WIFI module of external ESP32C6 with ESP32P4` | ` with ESP32S3` |
| `os.uname().release` | `1.28.0` | `1.28.0` |
| `os.uname().version` (build date) | `v1.28.0-dirty on 2026-09-07` | `v1.28.0-dirty on 2026-09-03` |
| `sys.implementation._build` | `ESP32_GENERIC_P4-C6_WIFI` | `ESP32_GENERIC_S3-SPIRAM_OCT_JTAG` |
| `machine.freq()` | 360 MHz | 240 MHz |
| `gc.mem_free()` at rest | 33.1 MB | 8.3 MB |
| `audioeffects` | not frozen in — put on `/lib` for this run | not frozen in — put on `/lib` for this run |

Both firmwares carry the audioif native modules (`audiocore`, `audiomixer`,
`synthio`, `audiofilters`, `audiodelays`, `audioecho`, `audiodynamics`,
`audiomath`, `audioroute`, `audioconvolve`, `audiofreeverb`, `audiospeed`,
`audiomp3`) frozen in. Neither carries `audioeffects` or `audioinstruments`,
so `lib/audioeffects/*.py` was copied to `/lib/audioeffects/` on each board
(`mpftp cp … --verify`, all ten modules verified) and imported from there. No
firmware was flashed.

**Gap worth naming: neither firmware records which audioif revision it was
built from,** and this run did not establish it. `AUDIOIF_PIN` names `v0.2.0`
(`ec3c67f`); the P4 image was built on 2026-09-07 and the S3 image on
2026-09-03, four days apart, and nothing on either board can confirm they hold
the same core. Treat cross-board comparisons as comparisons of *these two
images*, not of the two chips alone, until the firmware revisions are pinned.

## How to read it

The unit is one **256-frame stereo block at 48 kHz**, which is 5.333 ms of
audio. That block is not an arbitrary choice: `audioecho.FeedbackDelay`,
`audiodynamics.Dynamics`, `audiomath.Multiply`, `audioconvolve.Convolver` and
the `audioroute` splitter all work internally in exactly 256-frame blocks, and
every node in the table was confirmed to hand back exactly 1024 bytes per
pull. It is the palette's own block.

- **ms/blk** — wall milliseconds the whole chain (probe source + target) spent
  per block.
- **marg** — the same figure with the probe source's own cost subtracted,
  measured in the same run under the same heap conditions. It strips the
  harness floor, but read it with one caveat: the floor is measured at the
  *source's* pull rate, which is far higher than a heavy target's, so where
  the control is a large share of `ms/blk` the subtraction takes off more than
  the target ever paid. **Compare rows by `ms/blk`;** read `marg` as "how much
  of this row is not the harness". Within the node table, where every control
  landed between 0.118 and 0.150 ms on the P4, the marginals do add.
- **rt** — real-time factor, audio seconds produced per wall second. It is
  exactly `5.333 / ms-per-block`, so it doubles as the headroom multiple:
  `rt 3.8` means the target uses about a quarter of one core; **`rt` below 1.0
  means the board cannot render it in real time at all.**
- **RAM** — bytes `gc.mem_alloc()` grew by while the target was constructed,
  with the probe already standing.
- **digest** — sha256 (first 16 hex) of the first 128 blocks (683 ms) the
  target rendered from a freshly built chain. One per run. Where a single
  digest is shown, **both boards produced byte-identical audio.**

The probe source is a looping `RawSample` through a one-voice `Mixer`, and its
material is generated with integer arithmetic only, so the *input* is
byte-identical on both chips by construction. It is two detuned triangles plus
noise under a repeating decay: harmonics for a filter to remove, transients for
a compressor to chase, a moving level for a gate, and different content per
channel so a stereo effect is not silently measured in mono.

### audioif palette nodes

| node | P4 ms/blk | P4 marg | P4 rt | S3 ms/blk | S3 marg | S3 rt | RAM (P4) | digest |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `audiofilters.Distortion` | 19.642 | 19.524 | 0.3 | 27.576 | 27.337 | 0.2 | 2208 B | `f775b2d577fbf41e` |
| `audioconvolve.Convolver` 48000 taps | 18.026 | 17.901 | 0.3 | 31.144 | 30.909 | 0.2 | 1528 KB | P4 `51823dd6eb0a2cb4`<br>S3 `b43ea63e39020a6e` |
| `audiodelays.MultiTapDelay` | 2.793 | 2.676 | 1.9 | 3.522 | 3.285 | 1.5 | 96 KB | `c6ced37eca9a5ba8` |
| `audiodelays.Echo` | 1.545 | 1.427 | 3.5 | 2.005 | 1.756 | 2.7 | 58 KB | `a805175d8783a830` |
| `audiofreeverb.Freeverb` | 1.412 | 1.294 | 3.8 | 3.146 | 2.909 | 1.7 | 52 KB | `7ae20a32d909a876` |
| `audioconvolve.Convolver` 1024 taps | 0.874 | 0.749 | 6.1 | 2.350 | 2.111 | 2.3 | 50 KB | P4 `ed99f212e015bdf3`<br>S3 `da0bc1e8bc1995fd` |
| `audiodelays.PitchShift` | 0.866 | 0.748 | 6.2 | 1.163 | 0.923 | 4.6 | 4368 B | `78af690c0764d8fe` |
| `audiofilters.Phaser` | 0.827 | 0.709 | 6.5 | 1.885 | 1.646 | 2.8 | 2240 B | `1a2f83e213e3e048` |
| `audiodelays.Chorus` | 0.526 | 0.408 | 10.1 | 0.844 | 0.604 | 6.3 | 12 KB | `2e33182e064de4ee` |
| `audiodynamics.Dynamics` | 0.512 | 0.394 | 10.4 | 0.993 | 0.753 | 5.4 | 1200 B | `a990b35874e3cfde` |
| `audioecho.FeedbackDelay` | 0.413 | 0.296 | 12.9 | 0.752 | 0.516 | 7.1 | 48 KB | `6e63708183d6d859` |
| `audiofilters.Filter`, modulatable cutoff | 0.326 | 0.208 | 16.4 | 0.616 | 0.378 | 8.7 | 3392 B | `2f191df093bf29e6` |
| `audiofilters.Filter` | 0.322 | 0.204 | 16.6 | 0.614 | 0.376 | 8.7 | 3328 B | `2f191df093bf29e6` |
| `audioroute.Splitter` 2 taps read | 0.315 | 0.165 | 16.9 | 0.645 | 0.395 | 8.3 | 34 KB | `4169efd90ecf44dd` |
| `audioroute.Splitter` 1 tap read | 0.182 | 0.065 | 29.3 | 0.376 | 0.139 | 14.2 | 34 KB | `4169efd90ecf44dd` |
| `audiomath.Multiply` | 0.158 | 0.028 | 33.7 | 0.271 | 0.047 | 19.7 | 2016 B | `17a7e6961683c978` |
| `audiomixer.Mixer` | 0.154 | 0.036 | 34.6 | 0.257 | 0.018 | 20.7 | 2272 B | `4169efd90ecf44dd` |
| *(probe source alone)* | 0.130 | 0.013 | 41.1 | 0.220 | -0.018 | 24.2 | 0 | `4169efd90ecf44dd` |

### audioeffects classes

| class | P4 ms/blk | P4 marg | P4 rt | S3 ms/blk | S3 marg | S3 rt | RAM (P4) | digest |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `Overdrive` | 19.178 | 18.947 | 0.3 | 27.395 | 27.022 | 0.2 | 9776 B | `150adbdfef291ea2` |
| `DigitalDelay` | 1.674 | 1.443 | 3.2 | 2.034 | 1.671 | 2.6 | 89 KB | `a20dc8f4b826bbf1` |
| `Reverb` | 1.407 | 1.062 | 3.8 | 3.008 | 2.644 | 1.8 | 54 KB | `7ae20a32d909a876` |
| `Compressor` | 0.614 | 0.382 | 8.7 | 1.147 | 0.781 | 4.7 | 1440 B | `b1d435a5c4d99ebb` |
| `Chorus` | 0.553 | 0.205 | 9.6 | 0.889 | 0.528 | 6.0 | 12 KB | `5c27a0a59957171e` |
| `LowPass` | 0.355 | 0.123 | 15.0 | 0.676 | 0.311 | 7.9 | 5600 B | `c234fc7558205e6a` |

The six classes are one per `audioeffects` module — `dynamics`, `eq`, `delay`,
`reverb`, `modulation`, `drive` — chosen so the sample spans the library's
shapes rather than its cheap end. The `pitch` and `rack` modules were not
sampled.

## What the table says

### 1. `audiofilters.Distortion` is the most expensive node in the palette, and it does not fit

19.6 ms/block on the P4 and 27.6 ms/block on the S3, against a 5.333 ms
budget: `rt 0.27` and `rt 0.19`. It is **more expensive on the P4 than a
48000-tap convolution**, and it is the only cheap-looking node in the library
that cannot run in real time on either board.

The cause is visible in audioif's own source, `src/shared/audioif_distortion.c`:
the per-sample function computes in `double`, and OVERDRIVE mode calls `exp()`
three times plus `sqrt()`, with `soft_clip` adding a fourth `exp()` — four
double-precision transcendentals for every one of the 512 samples in a block.
Both chips have single-precision FPUs only, so every one of those is software
emulated.

**Consequence for the effects program:** every class in `audioeffects/drive.py`
— `Overdrive`, `Distortion`, `Fuzz`, `Saturation`, `Exciter`, and `CabinetSim`'s
drive path — is a render-only effect today, not a live one. The `Overdrive`
row confirms it end to end: 19.178 ms/block, essentially the bare node's cost.
This is an audioif matter, not an audiocomponents one; nothing in this
repository can fix it.

### 2. Convolution at reverb scale does not fit either; at cabinet scale it does

`audioconvolve.Convolver` with a 1-second impulse (48000 taps, which is
`ConvolutionReverb`'s default) costs 18.0 ms/block on the P4 and 31.1 ms/block
on the S3, and needs 1.5 MB — `rt 0.30` and `rt 0.17`. `ConvolutionReverb`'s
own docstring says as much; this is the measurement behind it.

At 1024 taps — `CabinetSim`'s scale — it is 0.874 ms/block on the P4 and
2.350 ms/block on the S3, so a cabinet fits comfortably on the P4 and takes
44% of the S3's budget on its own.

### 3. `audioconvolve` is the one node whose output depends on the chip

Every other row in both tables shows a single digest: the two boards rendered
byte-identical audio, biquads, freeverb, dynamics, phaser, pitch shift and the
four-`exp()` distortion included. The two `Convolver` rows are the exception.

That is not the synthesized impulse's doing. Running the same convolver with a
**byte-identical integer impulse loaded via `load()`** instead of
`synthesize()` still gives different digests — `f95bcf76be4a93e5` on the P4
against `6226b85c56ceb4f5` on the S3 — so the divergence is in the convolution
path itself, not in the IR that goes into it. Anything that gates
`audioconvolve` output on a hash must hold each board to its own value.

### 4. A modulatable cutoff is free

`audiofilters.Filter` with a plain float cutoff and the same filter with its
cutoff behind a `synthio.Math` block — which is how every `_SingleFilter`
subclass in `audioeffects/eq.py` builds one so `set_frequency` can move it —
measure the same to within noise: 0.322 against 0.326 ms/block on the P4,
0.614 against 0.616 on the S3, identical digests. There is no cost to keeping
a filter sweepable.

### 5. The Python wrapper costs nothing measurable

Where a class is one node, the class and the node measure the same thing:
`Reverb` (1.407) against `audiofreeverb.Freeverb` (1.412) — with **the same
digest**, `7ae20a32d909a876`, because the class is that node at its hall
preset. `Chorus` 0.553 against `audiodelays.Chorus` 0.526, `Overdrive` 19.178
against `audiofilters.Distortion` 19.642. Whatever the effects library costs,
it is not the Python.

### 6. The routing primitives are nearly free; the delay lines are not

`audiomath.Multiply` (0.028 ms marginal on the P4), `audiomixer.Mixer`
(0.036) and a one-tap `audioroute.Splitter` (0.065) cost almost nothing, so
building an effect out of parallel branches is not what makes it expensive. A
second splitter tap costs about as much again as the first (0.065 → 0.165).
What costs is the lines: `audiodelays.MultiTapDelay` at 2.676 ms marginal is
nine times a `Filter` and forty times a `Mixer`, and it takes 96 KB.

### 7. What fits on each board

At 5.333 ms per block, and taking marginal cost so the numbers add:

- **P4** has roughly 5.3 ms to spend. `audiofreeverb.Freeverb` (1.294) plus
  `audiodelays.Echo` (1.427) plus `audiodynamics.Dynamics` (0.394) plus two
  `audiofilters.Filter` (0.204 each) is 3.52 ms — a real pedalboard, with
  margin. Add one drive class and it is four times over.
- **S3** has the same 5.333 ms and spends it 1.7 to 2.7 times faster. The same
  reverb alone is 2.909, over half the budget; add the same echo (1.756) and
  one filter (0.376) and 5.04 of 5.33 ms is gone. Two heavy effects is the
  S3's ceiling, not four.

Those are node marginals, which add within the node table for the reason given
above. They are a planning arithmetic, not a measurement: a real chain also
pays for the splitters and mixers between its branches, and nobody has
measured an assembled rack yet.

Neither figure includes an instrument. `measure_voice_headroom.py` measures
that side; a patch has to fit both in the same 5.333 ms.

## What is NOT done

- **No I2S device was opened, and no `audiodev` pump ran.** Every number is
  the DSP alone. The stompbox latency seam — the pump plus the I2S ring, 52 to
  418 ms — is untouched by this table and is not predicted by it.
- **The firmware's audioif revision was not established** on either board. See
  the note under "The boards".
- **6 of the 46 effect classes were measured.** The `pitch` module
  (`PitchShifter`, `Harmonizer`, `Octaver`, `StereoWidener`) and the `rack`
  module (`Rack`, `ShimmerHall`, `AirSpace`) have no rows at all, and a rack is
  where the splitter-and-mixer costs actually accumulate.
- **One parameter setting per node.** A `Dynamics` in gate mode, a `Distortion`
  in LOFI mode, a `Phaser` with 12 stages are all different numbers from the
  ones here. The settings used are the ones `audioeffects` itself passes, and
  they are in the tool's builder functions.
- **`audiospeed` and `audiomp3` were not measured.** No effect class uses them.
- **Nothing here was listened to.** The digests say two boards rendered the
  same bytes; they say nothing about whether those bytes are right.

## Reproducing it

```bash
# once per board, since audioeffects is not frozen into either firmware
mpftp mkdir -d COM4 /lib
mpftp cp -d COM4 lib/audioeffects :/lib/audioeffects --verify
mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify

# one target per run; `mpftp run` soft-resets first, so each is a fresh VM
printf 'import measure_effect_cost as m\nm.main("node:audiofilters.Filter")\n' > one.py
mpftp run -d COM4 one.py --follow

# the catalogue of targets
mpftp exec -d COM4 'import measure_effect_cost as m; m.main()'
```

Each run prints a `ROW` line, tab separated:
`target, blocks/s, rt, ms/block, control ms/block, marginal ms, RAM bytes, digest`.

**One trap the tool now handles, and it cost a whole first sweep.** On a board
where `audioeffects` is not frozen in, importing it compiles 100 KB of Python,
and on a fresh VM that compile lands inside the run that follows. Before the
tool primed the chain, `effect:LowPass` returned **1.966, 1.133 and 0.356
ms/block on three consecutive runs of the identical script** — a 5.5x spread on
audio whose digest never moved. The first sweep published 1.959 for it. With
priming the same three runs give 0.353, 0.354, 0.352. Every number in this
document comes from the primed tool; nothing from the first sweep survives in
it.

**And one the tool handles because it was caught failing.** The digest window
was 64 blocks (341 ms) to begin with, and `DigitalDelay`'s default time is
350 ms — so its first repeat had not arrived yet, the dry passed at unity, and
the effect hashed **byte-identical to the bare source**. A digest that cannot
tell a delay from a piece of wire is not a check. The window is 128 blocks
(683 ms) now, and `DigitalDelay` hashes `a20dc8f4b826bbf1` against the source's
`4169efd90ecf44dd`. Rows that still share the source's digest —
`audioroute.Splitter` and `audiomixer.Mixer` — do so because they genuinely
pass the signal through unchanged, which is the check working, not failing.
