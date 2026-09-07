# audioeffects

Forty-six effect classes built out of audioif's audio nodes, for any host
that can pull an audiosample:

```python
import audioeffects

comp = audioeffects.create("Compressor", source, 48000,
                           threshold_db=-20, ratio=3, character="optical")
tape = audioeffects.create("TapeDelay", comp.output, 48000,
                           time_ms=340, feedback=0.4, mix=0.25)
hall = audioeffects.create("Reverb", tape.output, 48000,
                           preset="hall", mix=0.3)
audio_out.play(hall.output)
```

The package factory is the host-facing construction boundary: it receives the
source and sample rate explicitly. Direct class construction remains
supported for local code after a call to `configure()`.

Every class takes its audio source as the first argument - a synthesizer, an
`audioinstruments` instrument's `output`, a host input, or another effect's
`.output` - and exposes its chain tail as `.output`. The underlying nodes are
kept as attributes (`.node`, `.mixer`, `.cutoff`, ...) so applications can
bind parameters straight to them; the classes with a natural swept control
also expose `set_*` helpers (`LadderFilter.set_cutoff`,
`DigitalDelay.set_time`, ...).

Every public effect class explicitly declares `NAME`, `MACRO_LABELS`,
`MACRO_MODES`, and `PATCHES`. `VENDOR` is declared once at module scope for
all effects in that source file. The complete provider rules are in
`docs/audio-components.md`.

For host integration, every public class also has the explicit factory
`EffectClass.create(source, sample_rate, **options)`, and the package helper
`audioeffects.create(name, source, sample_rate, **options)`. Direct class
construction remains supported for local code after a call to `configure()`.

Five nodes make the deeper processors possible: `audiodynamics.Dynamics` (an
envelope-follower gain computer with sidechain filtering, lookahead and
true-peak detection), `audioroute.Splitter` (fans one stream out to parallel
branches that a Mixer then sums), `audiomath.Multiply` (one stream times
another, which is ring modulation), `audioecho.FeedbackDelay` (a delay with
a filter, a soft-clip and a cross-feed inside its loop) and
`audioconvolve.Convolver` (an impulse response applied by partitioned FFT).
None of the five is CircuitPython's; a stock board does not have them.


## Sound stability

The API is our contract with you: class names, signatures, metadata, and
macro surfaces stay stable and change only deliberately. The *sound* is
not part of that contract. These components sound great, but they are not
all as accurate as they could be, and implementations will keep being
refined as the library matures — so a component may render audibly
differently from one release to the next. If a composition depends on the
exact sound of a release, pin that release rather than tracking the
latest; the code of every release stays available for exactly this
reason.

Beneath the components sits a harder guarantee: the audioif core — the
CircuitPython-compatible `synthio`/`audiocore`/effects-module layer — is
held bit-exact to CircuitPython itself, verified by parity gates, and
that never changes release to release. Where we find CircuitPython and
audioif disagree, we treat it as a bug and report it upstream. The
components are where the sound evolves; the floor they stand on does
not.

## Catalogue

### Dynamic range - `dynamics.py`
| Class | Notes |
|---|---|
| `Compressor` | four characters that differ in *law*, not in three numbers: `fet` (peak detector, both time knobs live and faster clockwise, threshold rising with ratio, dirty when you push it), `optical` — the default — (**no time knobs at all**: ten milliseconds of attack, half the recovery in sixty and the rest over a couple of seconds, slower after a long passage), `vca` (true-RMS, so a square and a sine of the same RMS get the same gain) and `varimu` (no ratio to speak of — the slope climbs with level; the six factory time constants are patches 8–13). Zero latency at every setting. Needs `audiodynamics` and `audioroute`, so it does not run on a stock CircuitPython board; **14 macros, 14 patches** |
| `Limiter` | brickwall against a ceiling, with a gain into it, a knee, lookahead (**0 ms by default**, up to 10 ms, reported in `latency_samples`) and a 4x true-peak detector; two `audiodynamics` nodes, **audioif tier**; **patches**. Release is the distortion knob and its docstring says so |
| `Expander` | **rebuilt** (Drawmer DS201 + RaneNote 155): downward, `ratio` dB out per dB in below threshold, to a `Depth` floor; true-RMS detector, two-ended 12 dB/oct key band, external key. Nine macros, six patches. **audioif tier** (`audiodynamics`), zero latency, one node. No Hold - that is `NoiseGate`'s, and the reason is measured ([dossier](../../docs/effects/Expander.md) §8.1) |
| `NoiseGate` | mutes below threshold |
| `DeEsser` | detector high-passed at `frequency`, so only sibilance ducks the signal |
| `TransientShaper` | SPL Transient Designer: more stick **and** less room from one instance, at any input level from −6 to −60 dBFS — no threshold, no ratio. Its time constants are fixed, not adaptive (T6 disconfirmed), and the attack section takes ~120 ms to settle on a held note (T5's 100 ms clause disconfirmed). 5 macros, 7 patches, **audioif** tier (`audiodynamics`), one node, 0.00 ms of latency; **patches** |
| `MultibandCompressor` | two or three bands (`bands=`), each with its own compressor, summed back flat to 0.12 dB; `Mix` at 0 is a true bypass; **audioif tier**, fourteen nodes at three bands and the most expensive class here. Isolation is exact - driving one band moves the others 0.00 dB - and the low band's own reduction tilts 0.7 dB across 30-100 Hz; **patches** |

### Frequency and EQ - `eq.py`
| Class | Notes |
|---|---|
| `ParametricEQ` | **rebuilt.** Pultec EQP-1A bottom and resonant top, three API 550A proportional-Q bells between: boost and cut the bass at once and you get the record trick, not silence; the top bell gets louder as `Bandwidth` sharpens; a bell's cut is the exact mirror of its boost. Sixteen macros, seven patches, zero latency. **Portability tier: audioif** (`audiobiquad`) - eight float biquads, so the tail reaches exact zero where the ported node parks on DC. Eight sections always built: budgeted at 43 % of an S3 stereo block and 26 % of a P4's. Dossier `docs/effects/ParametricEQ.md` |
| `GraphicEQ` | MXR M-108 Ten Band: ten octave bands from 31.25 Hz plus GAIN and VOLUME, and the bands **get wider as you back off** — 1.8 octaves at +3 dB, 0.71 at +12 — which is what makes three sliders at +6 dB a broad hump of +8.78 dB across 2.6 octaves rather than +6 dB. `Constant Q` on turns it into a studio graphic instead. A band at its centre detent is a wire byte for byte; a patch change starts the bank clean, a knob move rides through. 14 macros, 6 patches, **audioif** tier (`audiobiquad`, for a tail that reaches exact zero at 31.25 Hz), twelve sections, 0.00 ms of latency, 465 ms of tail; **patches** |
| `DynamicEQ` | notch+band split, band compressed, summed (the split is exact) |
| `LowPass` | **rebuilt.** The two-pole analog prototype: one knob slides the whole curve, one decides how loud the corner stands - 3 dB down at Resonance 0.707, 24 dB up at 16, where a click rings for seconds. A console's 12/24 dB/oct slope switch, a dry/wet Mix whose zero is a byte-exact wire, and a make-up Trim. Five macros, six patches, zero latency. **Portability tier: audioif** (`audiobiquad`) - three float biquads, so the tail reaches exact zero where the ported node parks on DC. Budgeted at 5 % of an S3 stereo block at 12 dB/oct and 9 % at 24, 1.5 % / 2.5 % on the P4. Dossier `docs/effects/LowPass.md` |
| `HighPass` `BandPass` `Notch` | single swept biquads |
| `HighPass` | **rebuilt.** The low-cut: one knob decides where the bottom stops and nothing above it is touched, one decides how loud the corner itself stands - 3 dB down at Resonance 0.707, 24 dB up at 16, where the filter whistles at its own corner. A desk's 12/24 dB/oct slope switch, a dry/wet Mix whose zero is a byte-exact wire, and a make-up Trim. Five macros, six patches, zero latency. Its transmission zero at DC is exact: a held offset decays to zero rather than to a residue. **Portability tier: audioif** (`audiobiquad`) - three float biquads, because the ported node parks on up to 71 LSB of DC at a 10 Hz corner and holds it. Budgeted at 5 % of an S3 stereo block at 12 dB/oct and 9 % at 24, 1.5 % / 2.5 % on the P4. Dossier `docs/effects/HighPass.md` |
| `LowPass` `BandPass` `Notch` | single swept biquads |
| `Notch` | **rebuilt.** Everything except one band: a tuned band-stop with a Width knob that is a bandwidth and not a depth, a Harmonics toggle that adds a second notch an octave up and half as wide in hertz for mains hum, a Depth blend whose zero is a byte-exact wire, and a make-up Trim. Five macros, six patches, zero latency. **Portability tier: audioif** (`audiobiquad`) - three float biquads, so the tail reaches exact zero where the ported node parks on 2 to 18 LSB of DC at exactly the hum settings. **What it does not do:** a `float` coefficient set cannot put the zeros exactly on the unit circle, so the centre is a true null from 500 Hz up but only −35.65 dB at 60 Hz Q 12 and −11.21 dB at 20 Hz Q 32 - a hum *reducer* at the bottom, not a hum eliminator. Budgeted at 5 % of an S3 stereo block with one notch and 9 % with two, 1.5 % / 2.5 % on the P4. Dossier `docs/effects/Notch.md` |
| `LowPass` `HighPass` `BandPass` | single swept biquads |
| `LadderFilter` | Moog-style 4-stage cascade, 24 dB/oct, resonant |
| `CombFilter` | tuned short feedback delay |

### Time and space - `reverb.py`, `delay.py`
| Class | Notes |
|---|---|
| `Reverb` | presets `room` `chamber` `hall` `plate` `spring` (spring adds pre-flutter) |
| `ConvolutionReverb` | a real impulse response, measured or synthesized; **patches** |
| `DigitalDelay` `SlapbackDelay` | clean repeats |
| `TapeDelay` | in-loop low-pass, soft-clip and per-sample wow; **patches** |
| `AnalogDelay` | BBD: band-limited both ends, `age` over the lot; **patches** |
| `PingPongDelay` | true cross-feed - repeats alternate sides; **patches** |
| `MultiTapDelay` | `(position, level)` tap patterns |

The delays split two ways. `DigitalDelay`, `SlapbackDelay` and
`MultiTapDelay` are clean and run on `audiodelays`, whose feedback path is
the echo times a decay. The other three are named after something that
happens *inside* that path - a filter taking a little more off each pass, a
soft-clip rounding it, a cross-feed sending it to the other speaker - so they
run on `audioecho.FeedbackDelay`, which is where audioif puts those. A
coloured delay's `max_time_ms` sizes its line and cannot change afterwards;
at 48 kHz a second of stereo line is 192 KB, so ask for what will be used.

The two reverbs are not the same kind of thing. `Reverb` is `audiofreeverb`:
a fixed network of delay lines that costs the same on a Cortex-M0 as on a
workstation, and that sounds like a plausible room. `ConvolutionReverb` is
`audioconvolve`: it applies an actual impulse response, so it sounds like a
*particular* room - and one second of stereo impulse is about 1.5 MB and
~150 MFLOPS, which is a desktop or an offline render. Reach for `Reverb`
first. The microcontroller-scale use of convolution is a **short** impulse:
`CabinetSim` is 1024 taps and about 3 MFLOPS.

`ConvolutionReverb`'s `seconds` is an allocation, not a setting - it fixes how
long an impulse that instance can ever hold, because the storage is carved
once and the audio path may already be pulling. Its Decay macro then works
within that allocation, which is why it is a proportion rather than a time.
Both convolution classes trail their input by `audioconvolve.FRAMES` (5.3 ms
at 48 kHz) once an impulse is loaded, and by nothing at all before one is.

### Modulation - `modulation.py`
| Class | Notes |
|---|---|
| `Chorus` | multi-voice with LFO-animated delay |
| `Flanger` | short modulated delay with feedback and doppler - the real swept comb |
| `Phaser` | all-pass stages with swept center |
| `Tremolo` | amplitude LFO |
| `Vibrato` | pitch LFO through the pitch shifter |
| `AutoPan` | panning LFO |
| `Rotary` | vibrato + tremolo + auto-pan at a shared slow/fast speed |
| `RingMod` | audio-rate multiply against a sine carrier; **patches** |

### Drive - `drive.py`
| Class | Notes |
|---|---|
| `Overdrive` | soft clip with tone control; `drive` is pre-gain into a fixed curve |
| `Distortion` | hard clip |
| `Fuzz` | pre-gained into a square |
| `Saturation` | `character="tube"/"tape"/"console"`, mostly dry |
| `Bitcrusher` | bit-depth reduction, by `bits` (2..16) or `crush` |
| `Exciter` | overdriven high-passed branch blended under the dry |
| `CabinetSim` | speaker cabinet by convolution with a short designed impulse; **patches** |

The three saturation characters are different curves, not one curve with
presets. `tube` runs the engine's asymmetric OVERDRIVE, so it generates a
2nd harmonic level with the 3rd; `tape` and `console` run its
odd-symmetric WAVESHAPE, whose 2nd harmonic measures 66 dB lower - the
numerical floor. On top of that `tape` has the head bump and the gap loss
that come with the medium (+1.4 dB at 40 Hz, −2.9 dB at 16 kHz) while
`console` gains a little air on top and nothing at the bottom, and
`console` is the gentlest of the three by about 4 dB of THD. All three are
level-matched at 1 kHz to within 0.3 dB,
so auditioning one against another does not mean re-balancing. `amount`
scales the whole character, tone shaping included.

### Pitch and stereo - `pitch.py`
| Class | Notes |
|---|---|
| `PitchShifter` | time-independent shift |
| `Harmonizer` | dry + up to three fixed intervals |
| `Octaver` | one or two octaves either way; only the branches asked for are built |
| `StereoWidener` | Haas: short-delayed copy panned wide against the dry |

### Effect racks - `rack.py`
| Class | Notes |
|---|---|
| `Rack` | a serial chain of this package's effects, described by a portable `chain` literal; owns its children, borrows the source |
| `ShimmerHall` | dry + octave-up through a tape echo into a long hall; **patches** |
| `AirSpace` | swept tone filter into a wobbling tape delay into a hall; **patches** |

A rack is one component with exactly the effect shape, however many effects
its internal graph holds - which is why racks live here rather than in a
package of their own. `Rack` is the reusable mechanism, ported from the way
micropython-vst3's soundtrack builds its custom racks:

```python
rack = audioeffects.create("Rack", source, 48000, chain=(
    ("Compressor", {"threshold_db": -24.0, "ratio": 3.0}),
    ("TapeDelay", {"time_ms": 340.0, "mix": 0.25}),
    ("Reverb", {"preset": "hall", "mix": 0.3}),
))
```

The chain entries are `NAME` strings or `(NAME, options)` pairs - portable
literals, so a host can carry a rack definition as data. Racks nest: an
entry may itself be `("Rack", {"chain": (...)})`, and a rack's `.output`
feeds anything an effect's can. A rack reports its complete graph's
latency (children summed) and tail (`None` as soon as any child's is
unbounded), and its `reset()` clears every child's DSP history without
reapplying the children's own patches over the options the rack built
them with. `ShimmerHall` and `AirSpace` are the two racks the vst3
soundtrack shares between pieces, ported whole: fixed topologies whose
macros move their children's controls.

## Deliberately absent

- **Pitch correction** - needs pitch detection (YIN or autocorrelation), and
  that is off the roadmap for good rather than pending. `PitchShifter` will
  shift by an interval you name; nothing here works out what interval to ask
  for.
- **Sample-rate reduction** - the other half of a lo-fi box. The engine's
  LOFI mode masks low bits and nothing else; decimation needs a
  sample-and-hold that is not in the palette. `Bitcrusher` does the bit
  depth alone.
- LFO-driven parameters update at the block rate (~187 Hz at 48 kHz),
  plenty for sweep rates but not audio-rate modulation. `RingMod` is the
  exception and does not use an LFO at all - see below.

## A note on how low a filter can go

Anywhere in the band, is the short answer - but it is worth knowing that
this was not always true, because the failure was silent and you may still
meet it on a stock CircuitPython board (below).

Every biquad in the engine used to keep its coefficients as Q15 integers,
which is the right trade on a microcontroller and costs low frequencies.
Below about 300 Hz they quantized into something that was no longer the
filter you asked for: a `LowPass` at 100 Hz returned **silence**, a
`HighPass` at 30 Hz returned **+21 dB of noise**, and a low shelf at 80 Hz
lifted the whole band by 13.4 dB instead of its 1.5. A second, unrelated
shortcut in the same file - one polynomial fitted to sine and cosine over
[0, π/2], which is only 12 kHz at 48 kHz - broke the *top* of the band too,
badly enough that a `HighPass` at 22 kHz passed its entire stopband.

Both are fixed. Coefficients now get as many fractional bits as each
individual filter has room for, the recursion accumulates in 64 bits and
keeps its feedback below the sample grid, and the trigonometry is a proper
series. Measured against the closed-form response, every mode lands within
**0.03 dB from 50 Hz to 22 kHz**. `GraphicEQ`'s ten ISO bands all read
+6.01 dB or better on a +6 dB request; the pre-rebuild `MultibandCompressor`'s
three bands recombined flat to 0.23 dB from 30 Hz to 8 kHz on those biquads.
(The rebuilt class is on `audiobiquad`'s float sections instead, for the tail
rather than the shape, and sums to 0.12 dB from 30 Hz to 20 kHz.) [audioif's `docs/upstream-diff.md`](https://github.com/PyDevices/audioif/blob/main/docs/upstream-diff.md),
**0.03 dB from 50 Hz to 22 kHz**. `ParametricEQ`'s ten octave bands all read
+6.01 dB or better on a +6 dB request (the claim `GraphicEQ` used to carry,
moved when it was rebuilt onto `audiobiquad`); `MultibandCompressor`'s three bands
recombine flat to 0.23 dB from 30 Hz to 8 kHz. [audioif's `docs/upstream-diff.md`](https://github.com/PyDevices/audioif/blob/main/docs/upstream-diff.md),
"The biquads were Q15, so they could not go low", has the arithmetic, the
before-and-after table, and what it cost in instructions on an M0.

Nothing refuses a low frequency and nothing ever did, because a
`LadderFilter` sweeping down through 40 Hz is a legitimate thing to do.
The only remaining rule is the one that was always real: stay below
Nyquist, which `check_hz` enforces.

## A note on patches

Some classes carry **patches**: named settings on the same 0-127 MIDI grid
`audioinstruments` uses, so a host or an app can offer presets and automate
knobs without knowing what any particular effect's arguments mean.

```python
mod = audioeffects.RingMod(source, patch=1)   # "Dalek"
mod.set_macro(0, 96)                          # Frequency, MIDI scale
name, values = audioeffects.RingMod.PATCHES[2]
```

A class declares `MACRO_LABELS` (the knob names), `MACRO_MODES` (the public
control behavior), and `PATCHES` (`{index: (name, (values,))}`). Private
engineering mappings may remain in `_MACRO_RANGES`; consumers never inspect
them. `set_macro(index, value)` takes the MIDI
scale and accepts floats, so a host with finer resolution need not quantize;
`macro(index)` reads a knob back in its own units; `program_change(index)`
applies a patch and ignores an index the class does not have, the way an
instrument does.

**Patch 0 is always the constructor's own defaults**, rendered onto the 7-bit
grid - close to a fresh instance, not identical to one, because 128 steps
cannot land exactly on every default. Constructor arguments are *not*
quantized: `RingMod(src, frequency=440)` gets 440 Hz, while patch 0's nearest
grid point for the 220 Hz default is 215.7.

An effect rack is one audio component whose internal graph chains or mixes
multiple effect nodes; `rack.py` above is where this package ships them,
declaring the same required metadata at class scope like any other effect
class. See `docs/audio-components.md` for the complete rack rule.

## A note on chaining after a Mixer

Several classes here end in an `audiomixer.Mixer` - anything that splits
into parallel branches and sums them. On MicroPython and CPython you can
chain freely after one. On CircuitPython you cannot: its Mixer stops its
voices when it is reset, and every effect resets its source when you
`play()` it, so the chain goes silent. audioif fixes that for its own
builds; see [audioif's `docs/upstream-diff.md`](https://github.com/PyDevices/audioif/blob/main/docs/upstream-diff.md), "Resetting a Mixer silenced it".

## A note on filters off a stock CircuitPython board

Every frequency in this library is the frequency you get - on audioif.
On stock CircuitPython two engine bugs are still in the way, and they
change what these classes sound like rather than breaking them, so they
are worth knowing about:

- A stereo `audiofilters.Filter` runs **one** biquad state across the
  interleaved stream, so the recursion advances twice per frame and every
  filter sits an **octave above** where it was asked to sit - and the
  feedback path leaks each channel into the other. Fixed upstream after
  10.2.1, so a current CircuitPython is fine; 10.2.1 itself is not.
- `PEAKING_EQ` computes `b2` with the wrong sign, which costs the filter
  its unity-outside-the-band property: a +6 dB bell at 1 kHz / Q 1 is
  about **+21 dB at DC**, worse the lower the center. Still present
  upstream. `ParametricEQ` and every shelf-free bell here depend on it;
  `audiobiquad`, and so the rebuilt `GraphicEQ`, computes the sign correctly
  in its own float kernel and never went through this.
- Biquad coefficients are Q15 and the recursion accumulates in 32 bits, so
  nothing below roughly 300 Hz is the filter it was asked to be, and one
  polynomial covers sine and cosine only as far as π/2 - 12 kHz at 48 kHz -
  so nothing near Nyquist is either. Both ends fail quietly. Still present
  upstream, and the section above is what a filter does here instead.

This library used to compensate for both - halving every frequency on the
way in, and synthesizing bells out of notch and band-pass sections. It no
longer does, because the engine is right. See [audioif's `docs/upstream-diff.md`](https://github.com/PyDevices/audioif/blob/main/docs/upstream-diff.md) for
the measurements and the one-line coefficient fix.

## Testing

`tests/test_cpython_effects_library.py` holds every class in
`audioeffects.ALL` to the contract - exports and metadata, the factory,
building and rendering, chaining, the patch surface - under CPython. What
each class *sounds* like is measured beside it, one module per family:
`test_cpython_effects_dynamics_eq.py`, `..._modulation.py`, `..._drive.py`,
`..._time.py`, `..._pitch.py` and `..._racks.py`, with
`test_cpython_convolve_node.py` for the audioconvolve node underneath the
convolvers. `tests/parity/effects_library_smoke.py` is the coarse half of
all that in portable Python, so MicroPython and patched CircuitPython can
walk the same catalogue - every class through `create()`, and every patch it
declares through `program_change()`. micropython-vst3's `tools/test-effects-lib.py`
additionally runs them inside a real VST3 host, feeding a quiet-then-loud sine and asserting
per-class behaviour: compressors and limiters squeeze the loud half,
gates and expanders mute the quiet one, everything else passes signal.
