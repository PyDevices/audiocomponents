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
all seventeen node targets were confirmed on the board to hand back exactly
1024 bytes per pull. It is the palette's own block.

The `audioeffects` classes are the one place that differs: `_core.pcm()` gives
its nodes `buffer_size=2048`, so five of the six classes hand back 512-frame
blocks (`Compressor`, whose `audiodynamics.Dynamics` has a fixed internal
buffer, still gives 256). The tool counts frames rather than pulls, so every
row in both tables is normalised to the same 256-frame block and the two are
directly comparable.

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

---

# With the Phase 1 nodes

**Measured 2026-09-07**, same tool, same probe material, same 256-frame
stereo block, on firmware carrying the eight additions of that day. The
section above is the "before"; this is the "after", and the two tables are
directly comparable because nothing about the method moved — only the
firmware and the rows.

## The boards, this run

| | ESP32-P4 (COM4) | ESP32-S3 (COM49) |
|---|---|---|
| `os.uname().version` | `v1.28.0-dirty on 2026-09-07` | `v1.28.0-dirty on 2026-09-07` |
| `os.uname().machine` | `Generic ESP32P4 module with WIFI module of external ESP32C6 with ESP32P4` | `Generic ESP32S3 module with Octal-SPIRAM with ESP32S3` |
| `os.uname().release` | `1.28.0` | `1.28.0` |
| `sys.implementation._build` | `ESP32_GENERIC_P4-C6_WIFI` | `ESP32_GENERIC_S3-SPIRAM_OCT` |
| `machine.freq()` | 360 MHz | 240 MHz |
| `gc.mem_free()` at rest | 33.1 MB | 8.3 MB |

**Both images are now dated the same day**, which the pre-node run's two were
not (P4 2026-09-07, S3 2026-09-03), and the S3 has moved off the
`SPIRAM_OCT_JTAG` variant onto plain `SPIRAM_OCT`. The gap the baseline named
is therefore *narrower* and not closed: neither firmware records the audioif
revision it was built from, and this run did not establish it either. What
this run *can* say, which the baseline could not, is that the desktop
`audiocomponents/.venv` holds audioif at
`2f6cbc3791efd38dfbf0fb263052400a69b976ed` (its `direct_url.json`
`vcs_info.commit_id`), and that every board digest below is reproduced
bit-exactly by that commit's CPython extension once one compiler flag is
matched — see *The digests* below. That is a stronger statement about which
core the boards hold than anything in the baseline run.

Verified before measuring, on each board:

```
mpftp eval -d COM4  "__import__('audioshaper') and __import__('audioladder') and __import__('audioverb') and __import__('audiobiquad') and 'ok'"
{"value": "'ok'"}
mpftp eval -d COM49 "…same…"
{"value": "'ok'"}
```

## The Phase 1 nodes

Columns as above. `RAM` was the same number on both boards for every row, so
one column carries both. Every row is one `mpftp run --follow` of
`measure_effect_cost.py`; **no row is BLOCKED — all fourteen targets
constructed and rendered on both boards.**

| node | P4 ms/blk | P4 marg | P4 rt | S3 ms/blk | S3 marg | S3 rt | RAM | digest (both boards) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `audioshaper.Waveshaper` ×8 | 1.942 | 1.818 | 2.7 | 3.452 | 3.211 | 1.5 | 5696 B | `36a0de432b9d5beb` |
| `audiodynamics.Dynamics` +options | 1.745 | 1.611 | 3.1 | 3.702 | 3.461 | 1.4 | 1440 B | `ab52977707cb42d9` |
| `audioshaper.Waveshaper` ×4 | 1.143 | 1.019 | 4.7 | 2.044 | 1.803 | 2.6 | 5696 B | `d4e8dde8c8d286cf` |
| `audioverb.Tank` | 1.130 | 1.002 | 4.7 | 1.973 | 1.732 | 2.7 | 91 KB | `5cec40f29c156e9f` |
| `audioladder.Ladder`, `oversample=2` | 1.005 | 0.871 | 5.3 | 1.734 | 1.493 | 3.1 | 1184 B | `0e5373fd35b5fd1f` |
| `audioshaper.Waveshaper` ×2 | 0.677 | 0.553 | 7.9 | 1.225 | 0.984 | 4.4 | 5696 B | `89dc160f8ca84e9d` |
| `audioladder.Ladder` | 0.601 | 0.467 | 8.9 | 1.030 | 0.790 | 5.2 | 1184 B | `6b89cece5e082c77` |
| `audioecho.FeedbackDelay` +options | 0.562 | 0.434 | 9.5 | 0.993 | 0.752 | 5.4 | 49760 B | `34c299bda16bc791` |
| `audiobiquad.AllPass`, 6 stages | 0.384 | 0.248 | 13.9 | 0.664 | 0.423 | 8.0 | 1248 B | `0b39903370981ac7` |
| `audioshaper.Waveshaper` ×1 | 0.347 | 0.223 | 15.4 | 0.651 | 0.410 | 8.2 | 5696 B | `4fb86344185e756c` |
| `audiobiquad.Biquad` | 0.235 | 0.100 | 22.7 | 0.411 | 0.169 | 13.0 | 1264 B | `129cb858074b6f17` |
| `audiomath.SubOctave` | 0.177 | 0.052 | 30.2 | 0.324 | 0.083 | 16.5 | 1104 B | `45ef8cbe813ce899` |
| `audioroute.MidSide`, `width=1.5` | 0.153 | 0.028 | 34.9 | 0.259 | 0.018 | 20.6 | 1088 B | `cd212534c62f60a6` |
| *(probe source alone)* | 0.126 | 0.003 | 42.3 | 0.233 | −0.001 | 22.9 | 0 | `4169efd90ecf44dd` |

**The settings**, which are the whole meaning of a row, are in the tool's
builder functions and were chosen so a row is comparable to the row it argues
against rather than so it flatters: the `Biquad` row is the same 1200 Hz
`LOW_PASS` at Q 0.707 the `audiofilters.Filter` row above uses, the `AllPass`
row is the same six stages at 800 Hz and feedback 0.6 as the
`audiofilters.Phaser` row, and both "+options" rows repeat their base row's
settings exactly and add only the paths that are new. `Ladder` is
`cutoff_hz=1200, resonance=3.5, drive=1.0, poles=4, passband_comp=0.5`;
`Tank` is Dattorro's default network with the modulation running
(`decay=0.7, diffusion=0.75, damping_hz=5000, bandwidth_hz=9000,
predelay_ms=20, mod_depth_ms=0.5, mod_rate_hz=1.0, width=1.0, mix=0.3`);
`Dynamics` +options adds `detector="rms", rms_ms=10, feedback_detector=True,
true_peak=2, sidechain_hz=120, sidechain_lp_hz=2500, sidechain_poles=2`, and
`FeedbackDelay` +options adds all four of the day's additions at once
(`wow_shape` a 256-point triangle, `wow_hz=1.5, wow_depth_ms=2.0,
delay_slew=0.5, wow_am_depth=0.25, loop_semitones=12, loop_window_ms=25`).

Two RAM figures need their arithmetic said out loud, because the builder's own
allocations are inside the measured window: the `Waveshaper`'s 5696 B is a
1024-point curve built in Python (2048 B) plus the node's own copy of it
(`waveshaper_load_curve` copies rather than borrows) plus the object; the
`FeedbackDelay` +options row's 49760 B is the base row's 48 KB line plus the
256-point wow table, which the node *borrows*. The Tank's 91 KB is the node's
alone and matches its documented 89.6 KB of line at 48 kHz with a 200 ms
predelay.

## What the new table says

### 1. The drive family stops being render-only

This is the headline, and it is the row `audiofilters.Distortion` failed. The
baseline's `Overdrive` costs **19.178 ms/block on the P4** and 27.395 on the
S3 — `rt 0.3` and `rt 0.2`, four times over budget on the better board. A
`Waveshaper` at ×4 costs **1.143 ms/block on the P4 and 2.044 on the S3**,
`rt 4.7` and `rt 2.6`. That is a 17-fold drop on the P4 and a 13-fold drop on
the S3, and it moves the whole of `audioeffects/drive.py` from "render-only"
to a live effect with room beside it.

At ×8 it is 1.942 and 3.452 ms/block — `rt 2.7` and `rt 1.5`. **×8 fits on
both boards**, but on the S3 it takes 65 % of the block budget and leaves
1.88 ms for everything else, which is about one `Freeverb` (2.909 marginal)
too little. The lean patch the drive dossiers already carry has a
measurement behind it now.

The factor is not free and does not double cleanly. P4 marginals are 0.223 /
0.553 / 1.019 / 1.818 at ×1 / ×2 / ×4 / ×8: ×2 costs 2.5× ×1 because ×1 runs
no half-band at all, and each doubling after that costs about 1.8×.

### 2. Both float replacements are cheaper than the ported nodes they replace

`audiobiquad` exists for the tail, not for the cost, and it wins on cost
anyway:

| | P4 marginal | S3 marginal |
|---|---:|---:|
| `audiofilters.Filter` (Q12, ported) | 0.210 | 0.386 |
| `audiobiquad.Biquad` (float, audioif's own) | **0.100** | **0.169** |
| `audiofilters.Phaser`, 6 stages (ported) | 0.704 | 1.659 |
| `audiobiquad.AllPass`, 6 stages | **0.248** | **0.423** |

Half the cost for the biquad and about a third for the all-pass, on both
chips, at the same settings. The ported rows here are **re-measured on this
firmware**, not carried over from the baseline table — see *The six
comparison rows, re-measured* below. The ported kernels' saturating fixed-point
write-backs are not buying speed on parts with an FPU; they are the reason
those tails never reach zero (audioif#23, audioif#36).

### 3. The tank is cheaper than Freeverb on hardware too, but not by 3.7×

`upstream-diff.md` measured 13.1 ms against Freeverb's 48.7 ms on the desktop
and said plainly that the ratio "is a desktop fact and does not transfer".
The board fact, both nodes measured on this firmware:
`audioverb.Tank` 1.130 ms/block against `audiofreeverb.Freeverb` 1.472 on the
P4, and 1.973 against 3.284 on the S3. Same direction, far smaller margin —
23 % cheaper on the P4 and 40 % on the S3, not 3.7×. Both fit on both
boards, and the tank is the one that fits on the S3 with room beside it.

### 4. The `Dynamics` options are the most expensive thing added

Against the base `audiodynamics.Dynamics` **re-measured on this same
firmware** (0.426 marginal on the P4, 0.862 on the S3), the option set costs
3.8× on the P4 and 4.0× on the S3. At 3.702 ms/block the S3 spends 69 % of a
block on one compressor. The set measured is the expensive half on purpose —
the `true_peak=2` 4× reconstruction is 48 multiplies per channel per sample by
its own docstring, and the second side-chain pole adds one multiply-add per
channel per sample per end of the band. The four `FeedbackDelay` options, by
contrast, cost 1.33× over their own re-measured base (0.327 → 0.434 on the P4,
0.565 → 0.752 on the S3) — a real but affordable addition.

### 5. The two integer nodes are as cheap as the routing primitives

`audioroute.MidSide` at 0.028 marginal on the P4 sits between `audiomath.Multiply`
(0.028) and `audiomixer.Mixer` (0.036); on the S3 it is 0.018, the cheapest
non-source row in either table. `audiomath.SubOctave` is 0.052 and 0.083.
Driving the mid and leaving the side alone costs a drive class nothing it
will notice.

### 6. The six comparison rows, re-measured — and one baseline digest moved

Every comparison in points 1–5 is between a new node and an old one, and the
old ones' numbers in the section above were measured on **different firmware**
(the S3's was four days older). Quoting them across that gap would be an
unmeasured claim, so all six were re-run on this firmware, both boards, same
tool, same settings:

| node | P4 ms/blk | P4 marg | S3 ms/blk | S3 marg | RAM | digest, this firmware | digest, pre-node firmware |
|---|---:|---:|---:|---:|---:|---|---|
| `audiofilters.Distortion` | 19.667 | 19.540 | 27.614 | 27.372 | 2208 B | `f775b2d577fbf41e` | `f775b2d577fbf41e` |
| `audiofreeverb.Freeverb` | 1.472 | 1.344 | 3.284 | 3.042 | 52960 B | `7ae20a32d909a876` | `7ae20a32d909a876` |
| `audiofilters.Phaser` | 0.831 | 0.704 | 1.901 | 1.659 | 2240 B | `1a2f83e213e3e048` | `1a2f83e213e3e048` |
| `audiodynamics.Dynamics` | 0.550 | 0.426 | 1.103 | 0.862 | 1440 B | **`d99590c3e97d923c`** | **`a990b35874e3cfde`** |
| `audioecho.FeedbackDelay` | 0.455 | 0.327 | 0.806 | 0.565 | 49232 B | `6e63708183d6d859` | `6e63708183d6d859` |
| `audiofilters.Filter` | 0.336 | 0.210 | 0.627 | 0.386 | 3328 B | `2f191df093bf29e6` | `2f191df093bf29e6` |

Costs are within a few percent of the baseline's throughout, which is the
expected result and is why the cross-firmware comparisons above are safe once
the rows are re-measured rather than quoted.

**One digest moved, and it is worth stating on its own line.**
`audiodynamics.Dynamics` at its baseline settings renders *different bytes* on
this firmware than on the pre-node one — `d99590c3e97d923c` against
`a990b35874e3cfde`, on both boards — and its construction footprint grew from
1200 B to 1440 B. Five other nodes, one of which (`audioecho.FeedbackDelay`)
also gained options this phase, render byte-identically across the same
firmware change.

**The twenty-one options are not the cause of the byte change**, and that was
tested rather than assumed: audioif was built at `1ad72ad~1` — the commit
before the options landed — and at the pinned `2f6cbc3`, and the *same* target
renders `e9d39fe10823e8a1` on both. The options are genuinely default-off on
the desktop at these settings; the struct growth is theirs, the moved bytes
are not.

So something else in `audiodynamics` moved between the two firmware images'
audioif revisions, and **neither image records which revision it holds** —
which is exactly the gap the baseline section named and this run has still not
closed. It should be closed before any board digest is read as evidence about
which core a board is running. Nothing in audiocomponents can close it.

### 7. The digests: both boards agree, and the desktop's difference is one compiler flag

**Every row's digest is the same on the P4 and the S3.** Fourteen for
fourteen, `audioconvolve`-style divergence included — that node is not in this
table, and nothing here reproduces its behaviour.

Against the desktop (`audiocomponents/.venv`, audioif `2f6cbc3`) the picture
splits, and it splits cleanly:

| agrees with the desktop | differs from the desktop |
|---|---|
| `audiomath.SubOctave` `45ef8cbe813ce899` | `audiobiquad.Biquad` board `129cb858074b6f17` / desktop `4f722f765d2a6cf6` |
| `audioroute.MidSide` `cd212534c62f60a6` | `audiobiquad.AllPass` `0b39903370981ac7` / `34170db78b0d5e54` |
| `audioshaper.Waveshaper` ×1 `4fb86344185e756c` | `audioladder.Ladder` `6b89cece5e082c77` / `f8086c7b11859c3f` |
| `audiodynamics.Dynamics` +options `ab52977707cb42d9` | `audioladder.Ladder` ×2 `0e5373fd35b5fd1f` / `5240528619206f5f` |
| *(probe source)* `4169efd90ecf44dd` | `audioverb.Tank` `5cec40f29c156e9f` / `e1e802c7d5906a8d` |
| | `audioshaper.Waveshaper` ×2 `89dc160f8ca84e9d` / `896d1d80ad6f0e31` |
| | `audioshaper.Waveshaper` ×4 `d4e8dde8c8d286cf` / `d8c6fca071a9790c` |
| | `audioshaper.Waveshaper` ×8 `36a0de432b9d5beb` / `58d9d5360ed515c4` |
| | `audioecho.FeedbackDelay` +options `34c299bda16bc791` / `a216253d3b1b17b2` |

**The cause is fused multiply-add contraction, and it was not guessed — it was
reproduced.** audioif's own `setup.py:6-14` already names the mechanism, for
macOS: clang's default `-ffp-contract=on` "fuses multiply-adds into fmadd
(baseline on AArch64, so contraction actually happens there, unlike x86-64
without `-mfma`), which perturbs last-ulp float results". Both ESP32 FPUs have
a fused multiply-add and GCC's default is `-ffp-contract=fast`; no
`-ffp-contract` flag appears anywhere in `audioif/micropython.mk`. The x86-64
desktop wheel, built without `-mfma`, does not contract.

So the extension was rebuilt at the same commit with `CC="gcc -mfma
-ffp-contract=fast"` — 138 `vfmadd`/`vfmsub` instructions in the resulting
`.so` against 0 in the shipped one — and the whole sweep re-run. **All nine
differing digests came back bit-identical to the boards':**
`129cb858074b6f17`, `0b39903370981ac7`, `6b89cece5e082c77`,
`0e5373fd35b5fd1f`, `5cec40f29c156e9f`, `89dc160f8ca84e9d`,
`d4e8dde8c8d286cf`, `36a0de432b9d5beb`, `34c299bda16bc791`. The two integer
kernels and the un-oversampled shaper path did not move, which is the control:
`audiomath.SubOctave` is Q15 and `audioroute.MidSide` is Q14, and neither has
a float multiply-add to contract.

**Contraction is not the only cause of board/desktop divergence in the
palette, only of these nine.** The six re-measured baseline rows split three
ways against the shipped desktop build: `audiofilters.Phaser` and
`audiofreeverb.Freeverb` agree with the boards outright;
`audioecho.FeedbackDelay` agrees only with the FMA rebuild (board and
fma-desktop `6e63708183d6d859`, shipped desktop `e7118d0485c800bd`); and
`audiofilters.Filter`, `audiodynamics.Dynamics` and `audiofilters.Distortion`
differ from *both* desktop builds, so they have a second cause — the obvious
candidates being `mp_float_t` (single on these boards, double on the CPython
target) in the coefficient paths and newlib against glibc in the per-sample
transcendentals, which the baseline's own analysis of `Distortion` already
counted four of per sample. That was not chased further here.

Nothing here is a bug in a node, and nothing here needs fixing in
audiocomponents. What it *does* mean is worth stating in one line, because
Phase 1's Gate turns on it: **`tests/parity/golden/dsp_nodes.json` cannot see
this class of divergence.** All four gated targets — MicroPython unix, the
CPython extension, patched CircuitPython, wasm — are built on this x86-64
host, where contraction is off; a board is not one of them. The gate's claim
is "every interpreter renders the same bytes *on this machine*", and it
remains true. A hash-gated claim about a board is a different claim and this
table is the first evidence for it.

## Reproducing the node rows

Exactly as the pre-node section's *Reproducing it*, with the new keys — the
catalogue lists them:

```bash
mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py --verify
printf 'import measure_effect_cost as m\nm.main("node:audioshaper.Waveshaper@x4")\n' > one.py
mpftp run -d COM4 one.py --follow
mpftp exec -d COM4 'import measure_effect_cost as m; m.main()'   # the catalogue
```

New keys: `audiobiquad.Biquad`, `audiobiquad.AllPass`, `audioladder.Ladder`,
`audioladder.Ladder@os2`, `audioverb.Tank`, `audiomath.SubOctave`,
`audioroute.MidSide`, `audioshaper.Waveshaper@x1|x2|x4|x8`,
`audioecho.FeedbackDelay@options`, `audiodynamics.Dynamics@options`.

The desktop leg is the same file: `measure_effect_cost.py` falls back to
`time.perf_counter_ns` where `time.ticks_us` does not exist, so
`audiocomponents/.venv/bin/python -c 'import sys; sys.path.insert(0, "tools");
import measure_effect_cost as m; m.main("node:audioverb.Tank")'` renders the
same 683 ms and prints the digest to hold a board's against. Its timings are
not board numbers and no table here quotes them.

---

# The waveshaper's alias floor at each factor

The roadmap wants this beside the CPU figure, and it belongs there: the
oversampling factor is the one knob that buys alias rejection with block time,
and neither number means anything without the other. Raw values, per segment,
with every hash:
[`effects-alias-floor.json`](effects-alias-floor.json). Produced by
[`tools/alias_floor/`](../tools/alias_floor/).

## The bar, and the method

−60 dB of non-harmonic energy relative to the fundamental, **over 20 Hz–20 kHz** —
the band all four drive dossiers name: `Overdrive` T7, `Distortion` A1,
`Fuzz` A4, `Saturation` A4. The measurement is Overdrive T7's own stated
method, verbatim: *"sum of every FFT bin more than two bins from a harmonic of
1010 Hz and from DC, against the fundamental's bin; 4800 samples at 48 kHz, no
window (101 exact periods, so every harmonic lands on a bin)"*. The 44.1 kHz
leg uses 4410 samples for the same reason — 101 cycles of 1010 Hz and 370 of
3700 Hz land on bins there too.

## The probe

A **full-scale** sine (32767) into `audioshaper.Waveshaper` at `pre_gain=1.0`,
`bias=0.0`, `post_gain=0.5`, `mix=1.0`, `channel_count=1`, through a
**1024-point int16 Q15 hard clip**, `y = clamp(4x, −1, +1)` — linear to a
quarter of full scale, flat past it. Computed on CPython and shipped to both
boards as bytes (`curve.bin`, sha256 `87fbf34f…`), which is exactly what the
node's table format is for: the boards and the desktop shape against the same
table rather than three tables built by three libms. The sines are shipped the
same way.

**This is a harder probe than any dossier's own.** They specify −6 dBFS
(Overdrive T7, Fuzz A4, Saturation A4) or −20 dBFS (Distortion A1); this one
sits 12 dB into a hard clip at full scale, which is a near-square, which is
the worst case Distortion A1 calls "the harder of the two". `post_gain 0.5`
keeps that near-square off the int16 rails, so nothing measured here is output
clipping. A class's own floor at its own drive will be *better* than this
table, never worse.

Render: 2×4800 (or 2×4410) frames per cell, the first half discarded as
settle, the second half — a whole number of cycles of steady state —
transferred off the board and analysed on the host with
`tools/effect_measurements.py`'s `spectrum()`.

## Factor × rate × board

Non-harmonic energy, 20 Hz–20 kHz, dB re fundamental. **Lower is better;
−60 dB or lower meets the bar.**

| tone | rate | factor | P4 | S3 | desktop | meets −60 dB |
|---|---:|---:|---:|---:|---:|---|
| 1010 Hz | 48000 | ×1 | −41.65 | −41.65 | −41.65 | no |
| 1010 Hz | 48000 | ×2 | −56.43 | −56.43 | −56.43 | no |
| 1010 Hz | 48000 | ×4 | −69.10 | −69.10 | −69.10 | **yes** |
| 1010 Hz | 48000 | ×8 | −80.76 | −80.76 | −80.76 | **yes** |
| 1010 Hz | 44100 | ×1 | −41.22 | −41.22 | −41.22 | no |
| 1010 Hz | 44100 | ×2 | −54.70 | −54.70 | −54.70 | no |
| 1010 Hz | 44100 | ×4 | −67.08 | −67.08 | −67.08 | **yes** |
| 1010 Hz | 44100 | ×8 | −79.24 | −79.24 | −79.24 | **yes** |
| 3700 Hz | 48000 | ×1 | −26.98 | −26.98 | −26.98 | no |
| 3700 Hz | 48000 | ×2 | −39.41 | −39.41 | −39.41 | no |
| 3700 Hz | 48000 | ×4 | −52.16 | −52.16 | −52.16 | no |
| 3700 Hz | 48000 | ×8 | −63.72 | −63.72 | −63.72 | **yes** |
| 3700 Hz | 44100 | ×1 | −20.64 | −20.64 | −20.64 | no |
| 3700 Hz | 44100 | ×2 | −36.54 | −36.54 | −36.54 | no |
| 3700 Hz | 44100 | ×4 | −49.57 | −49.57 | −49.57 | no |
| 3700 Hz | 44100 | ×8 | −61.60 | −61.60 | −61.60 | **yes** |

## What it says

### 1. The factor a drive class needs is set by the highest note it must pass

At 1010 Hz, **×4 clears the bar on both boards at both rates** with 7–9 dB in
hand. At 3700 Hz — the fifth fret of a guitar's top string is 440 Hz, but the
*harmonics* a hard clipper makes from it are what fold, and 3700 Hz is where a
lead line and a bright pick attack actually live — **only ×8 clears it**, and
at 44.1 kHz it clears by 1.6 dB. There is no factor at which a hard clip at
full scale is clean at 3700 Hz with margin to spare on this node.

So: **×4 is the floor for a class whose probe is 1 kHz, ×8 for one that has to
hold up at 3.7 kHz**, and a "Lean" patch dropping to ×2 is a −55 dB effect at
1 kHz and a −37 dB one at 3.7 kHz. That is a real audible difference and it is
what the lean patches are trading away. The dossiers already name their bar at
1010 Hz; on this evidence a drive class that ships ×4 should say so and should
not claim a floor at pitches it was never measured at.

### 2. 44.1 kHz is worse than 48 kHz, by 1–3 dB, at every factor but one

−54.70 against −56.43 at 1010 Hz ×2, −67.08 against −69.10 at ×4, −79.24
against −80.76 at ×8; at 3700 Hz the gap is wider — −49.57 against −52.16 at
×4. The mechanism is not subtle: the half-band coefficients were designed
against a 48 kHz chain's last decimation stage (a 20–28 kHz transition band,
`design_halfband.py`), and at 44.1 kHz that transition band is scaled down
with the rate, so it starts biting inside the audible top octave. **Nothing
here is broken; the design point is 48 kHz and 44.1 kHz costs a couple of dB.**
A class that is asked for 44.1 kHz should not report the 48 kHz figure.

### 3. Above 20 kHz the floor stops improving at 48 kHz, and that is by design

The bar is band-limited for a reason, and the unrestricted reading shows why.
Read to Nyquist instead of to 20 kHz (P4 figures; the other legs match):

| tone | rate | factor | 20 Hz–20 kHz | to Nyquist | loudest single line | at |
|---|---:|---:|---:|---:|---:|---:|
| 1010 Hz | 48000 | ×4 | −69.10 | −67.97 | −77.76 | 21310 Hz |
| 1010 Hz | 48000 | ×8 | −80.76 | −79.49 | −90.44 | 22750 Hz |
| 3700 Hz | 48000 | ×2 | −39.41 | −38.26 | −42.58 | 18300 Hz |
| 3700 Hz | 48000 | ×4 | −52.16 | −43.44 | −44.07 | 22100 Hz |
| 3700 Hz | 48000 | ×8 | −63.72 | −44.52 | −44.57 | 22100 Hz |

At 3700 Hz and 48 kHz the full-band figure is stuck at −43 to −44 dB from ×4
onwards, and the whole of it is **one line at 22100 Hz** — the seventh
harmonic, 25 900 Hz, folded. 25 900 Hz sits inside the last decimator's
declared 20–28 kHz transition band, so it is only partly attenuated and it
lands between 20 kHz and Nyquist. Doubling the factor again does not move it,
because the fold happens in the *last* stage whichever factor was used.

That is the design working as documented, not a defect — but it means a class
must not quote the unrestricted number, and a downstream stage that
resamples, or an ear that is not 20 kHz-limited, would meet it. The full JSON
carries both readings for every cell so a dossier can cite the one it means.

### 4. The two boards are byte-identical, and the desktop differs by 10 samples

`out_48000.raw` and `out_44100.raw` came off the P4 and the S3 with the **same
sha256** (`9b8367a6…` and `2cac752e…`), verified against each board's own hash
after transfer, and reproduced identically on a second full run from the
repo-resident kit. The desktop's are different files —
`81f8dbd0…` / `6d269de4…` — and the difference is **10 samples out of 76 880,
every one of them ±1 LSB**, all in cells where oversampling actually runs
(×1 differs nowhere). No figure in the table above moves by as much as
0.01 dB.

Same cause as the digests in the section above, and proved the same way: the
desktop extension rebuilt at the same commit with `CC="gcc -mfma
-ffp-contract=fast"` produces `9b8367a6…` and `2cac752e…` — **bit-identical to
both boards**, for all sixteen cells.

## Reproducing it

```bash
cd audiocomponents
python3 tools/alias_floor/make_material.py tools/alias_floor/work

# per board, once
mpftp mkdir -d COM4 /alias
for f in curve.bin sine_48000_1010.raw sine_48000_3700.raw \
         sine_44100_1010.raw sine_44100_3700.raw; do
  mpftp put -d COM4 tools/alias_floor/work/$f /alias/$f --verify
done
mpftp run -d COM4 tools/alias_floor/render_alias.py --follow
mpftp get -d COM4 /alias/out_48000.raw tools/alias_floor/work/alias_out_COM4/out_48000.raw --verify
mpftp get -d COM4 /alias/out_44100.raw tools/alias_floor/work/alias_out_COM4/out_44100.raw --verify

.venv/bin/python tools/alias_floor/render_desktop.py tools/alias_floor/work
.venv/bin/python tools/alias_floor/analyse_alias.py  tools/alias_floor/work
```

## What is NOT done in this half of the table

- **The round-trip latency table does not exist.** No I2S device was opened in
  either half of this run; the Phase 1 Gate's second table — output→input
  loopback, a click through a wire and through a five-effect chain, at the
  smallest `ibuf`/chunk that does not starve — is untouched, and nothing here
  predicts it.
- **No assembled chain or rack was measured**, only single nodes, so the
  baseline's warning still stands: the marginals are a planning arithmetic,
  not a measurement of a chain.
- **One parameter setting per node**, as before. A `Tank` on a shorter
  `delays` table, a `Ladder` at `poles=2`, a `Waveshaper` on a 256-point curve
  are all different numbers from these.
- **The alias floor was measured for one curve at one drive.** A soft knee at
  a gentler `pre_gain` will read better at every factor; the near-square at
  full scale is the worst case and no class has yet been measured at its own.
- **`hysteresis` was not measured at all** — neither its cost nor its effect
  on the alias floor. It is off in every row here.
- **Nothing was listened to.** The digests say three legs rendered the same
  bytes to within 10 LSBs; they say nothing about whether those bytes are
  right.
- **`audiodynamics.Dynamics`' moved digest is recorded, not explained.** The
  options were ruled out by a desktop A/B at `1ad72ad~1` and `2f6cbc3`; what
  actually moved between the two firmware images is unknown and needs the
  audioif revision each image was built from, which neither records. **This
  wants an issue of its own on audioif; none was filed from this run.**
- **The board/desktop divergence of `audiofilters.Filter`,
  `audiodynamics.Dynamics` and `audiofilters.Distortion` was not chased.**
  Contraction is ruled out for all three (they differ from the FMA rebuild
  too); the remaining candidates are named above and not tested.
