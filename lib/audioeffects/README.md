# audioeffects

Forty-five effects for any host that can pull an audiosample: compressors and
EQs, reverbs and delays, modulation, drive and amp simulation, pitch
shifters, and three ready-made racks. Pick one by name, hand it your audio,
and play what comes out.

```python
import audioeffects

comp = audioeffects.create("Compressor", source, 48000,
                           threshold_db=-20, ratio=3, character="optical")
tape = audioeffects.create("TapeDelay", comp.output, 48000,
                           time_ms=340, feedback=0.4, mix=0.25)
hall = audioeffects.create("Reverb", tape.output, 48000,
                           character="hall", mix=0.3)
audio_out.play(hall.output)
```

`audioeffects.ALL` lists every name `create()` accepts. `create()` takes the
audio source and the sample rate explicitly; a source can be a synthesizer,
an `audioinstruments` instrument's `output`, a host input, or another
effect's `.output`. Every effect hands back its chain tail as `.output`, keeps
its underlying nodes as attributes (`.node`, `.mixer`, `.cutoff`, ...) so you
can bind parameters straight to them, and follows the common component
surface in [`docs/reference/component-api.md`](../../docs/reference/component-api.md): `set_macro()`, `program_change()`,
`latency_samples`, `tail_samples` and the rest. Every class declares `NAME`,
`MACRO_LABELS`, `MACRO_MODES` and `PATCHES`; the provider rules are in
[`docs/reference/metadata.md`](../../docs/reference/metadata.md). Constructing a class directly also works, and
reads the format off the source it is handed.

Nearly everything here needs the audiodsp tier of nodes
(`audiodynamics`, `audiobiquad`, `audioecho`, `audioverb`, `audioconvolve`,
`audiomath`, `audioshaper`, `audioladder` and friends), which a stock
CircuitPython board does not have.

For a complete program to start from, see [audioeffects_simpletest.py](https://github.com/PyDevices/audiocomponents/blob/main/examples/audioeffects_simpletest.py).

## What is in it

Each class below is a name you give to `audioeffects.create()`. The module
docstring of any of them lists its controls and limits.

### Dynamics

- `Compressor` evens out loud and quiet with four characters: a fast FET, a slow optical, a VCA and a vari-mu.
- `Limiter` stops the signal at a ceiling, with optional lookahead and true-peak detection.
- `Expander` makes quiet passages quieter by a ratio, down to a floor you set.
- `NoiseGate` shuts the signal off when it falls under a threshold, with hold and a key filter.
- `DeEsser` turns down sibilance without dulling the rest of a voice.
- `TransientShaper` gives you more attack or more sustain from one pair of knobs, with no threshold.
- `MultibandCompressor` compresses two or three bands on their own and sums them back flat.

### EQ and filters

- `ParametricEQ` is a shelving and bell EQ with three bells and a Q law you choose.
- `GraphicEQ` is a ten-band octave graphic equalizer.
- `LowPass` cuts the highs above a corner, with resonance and a 12 or 24 dB/oct slope.
- `HighPass` cuts the lows below a corner, with the same resonance and slope choices.
- `BandPass` keeps one band and drops the rest.
- `Notch` removes one band, or a hum and its harmonics.
- `LadderFilter` is a four-pole Moog-style low-pass that can sing at high resonance.
- `CombFilter` is a tuned feedback comb that puts a pitch on whatever goes through it.
- `DynamicEQ` is a bell that only appears when its band gets loud.

### Reverb

- `Reverb` is a plate, room, chamber or hall, built from a fixed network of delay lines.
- `ConvolutionReverb` puts your signal in a synthesized room, or in the room your own impulse was recorded in.

### Delay

- `DigitalDelay` is a clean delay whose Time knob bends the repeats instead of clicking.
- `SlapbackDelay` is the single short tape repeat behind a vintage rockabilly voice.
- `TapeDelay` is a tape echo with a motor or a sliding head, wow and flutter.
- `AnalogDelay` is a bucket-brigade echo whose repeats darken as Time grows.
- `PingPongDelay` bounces the repeats between the two speakers.
- `MultiTapDelay` reads one recording with several heads for rhythmic patterns.

### Modulation

- `Chorus` thickens a part with one analog-style swept voice.
- `Flanger` sweeps a comb of notches through the sound.
- `Phaser` sweeps an all-pass cascade for a softer, swirling version of the same idea.
- `Tremolo` pulses the level, in bias-vary or optical style. Default is bias, Depth 0.5, Rate 5 Hz — not the optical standout and not L1's Depth 1. Wet peak at the default is −1.341 dB vs a 16000-LSB tone, not the ~6 dB `synthio` `>>16` ceiling; Depth 0 is still a wire. At 22.05 kHz the default's L1 bar is measured at the constructor, not assumed. Optical L1/L2 are disconfirmed; O1–O4 unmeasured at the constructor. L1 holds on sine at every rate, and misses by 0.16 dB on SQUARE material at 44.1 kHz only (−79.844 against −80; 48 kHz holds at −82.01).
- `AutoPan` moves the sound left and right on an LFO.
- `Vibrato` wobbles the pitch.
- `RingMod` multiplies your signal by a carrier for bell-like and metallic tones.

### Drive

- `Overdrive` is a diode-limited, Tube Screamer style push.
- `Distortion` is hard clipping after a shaped gain stage.
- `Fuzz` is a germanium fuzz box, or a cascaded Big Muff style one.
- `Saturation` is the warmth of a tube stage, a tape machine or transformer iron.
- `Bitcrusher` lowers the word length and the sample rate for a lo-fi crunch.
- `Exciter` adds high harmonics to the top of the sound.
- `CabinetSim` runs the signal through a designed 4x12 or 1x12 cabinet.

### Pitch and stereo

- `PitchShifter` plays your part again a fixed interval up or down.
- `Harmonizer` blends up to three fixed intervals under the dry for instant harmony.
- `Octaver` adds an octave or two below the note you play.
- `StereoWidener` widens a stereo part with a Haas delay or Mid/Side scaling.

### Racks

- `Rack` chains the other effects in the order you name, and hands back a single effect.
- `ShimmerHall` is a pitch-shifted bloom around a long hall.
- `AirSpace` is a swept filter into a wobbling tape echo into a chamber.

## Chaining effects with a rack

A rack is one component with the shape of a single effect, however many
effects sit inside it. `Rack` takes a `chain` of effect names, or
`(name, options)` pairs, in the order the signal passes through them:

```python
rack = audioeffects.create("Rack", source, 48000, chain=(
    ("Compressor", {"threshold_db": -24.0, "ratio": 3.0}),
    ("TapeDelay", {"time_ms": 340.0, "mix": 0.25}),
    ("Reverb", {"character": "hall", "mix": 0.3}),
))
```

The chain is plain data, so a host can store a rack as a literal. Racks nest:
an entry may itself be `("Rack", {"chain": (...)})`. A rack owns its children
and borrows the source. It reports its whole graph's latency (the children
summed) and tail (`None` as soon as any child's is unbounded), and
`reset()` clears every child's history. `ShimmerHall` and `AirSpace` are
fixed racks whose macros move their children's controls.

## Latency

`latency_samples` is how late the output arrives behind the input. The table
gives it in milliseconds at 48 kHz, read from each class's own report, at the
default patch, at the worst of its shipped patches, and at the widest setting
any one macro can reach. Zero means the effect adds no delay to the dry path.
A delay's repeats, a reverb's tail and a compressor's release are not
latency; `tail_samples` reports those.

| Class | Default patch | Worst shipped patch | Widest setting of any knob |
|---|---|---|---|
| `Compressor` | 0 | 0 | 0 |
| `Limiter` | 0 | 2.98 | 10 |
| `Expander` | 0 | 0 | 0 |
| `NoiseGate` | 0 | 0 | 0 |
| `DeEsser` | 0 | 0 | 0 |
| `TransientShaper` | 0 | 0 | 0 |
| `MultibandCompressor` | 0 | 0 | 0 |
| `ParametricEQ` | 0 | 0 | 0 |
| `GraphicEQ` | 0 | 0 | 0 |
| `LowPass` | 0 | 0 | 0 |
| `HighPass` | 0 | 0 | 0 |
| `BandPass` | 0 | 0 | 0 |
| `Notch` | 0 | 0 | 0 |
| `LadderFilter` | 0 | 0 | 0 |
| `CombFilter` | 0 | 0 | 0 |
| `DynamicEQ` | 0 | 0 | 0 |
| `Reverb` | 0 | 0 | 0 |
| `ConvolutionReverb` | 5.33 | 5.33 | 5.33 |
| `DigitalDelay` | 0 | 0 | 0 |
| `SlapbackDelay` | 0 | 0 | 0 |
| `TapeDelay` | 0 | 0 | 0 |
| `AnalogDelay` | 0 | 0 | 0 |
| `PingPongDelay` | 0 | 0 | 0 |
| `MultiTapDelay` | 0 | 0 | 0 |
| `Chorus` | 0 | 0 | 0 |
| `Flanger` | 0 | 0 | 0 |
| `Phaser` | 0 | 0 | 0 |
| `Tremolo` | 0 | 0 | 0 |
| `AutoPan` | 0 | 0 | 0 |
| `Vibrato` | 4 | 10 | 12 |
| `RingMod` | 0 | 0 | 0 |
| `Overdrive` | 0 | 0 | 0 |
| `Distortion` | 0.04 | 0.04 | 0.04 |
| `Fuzz` | 0.08 | 0.08 | 0.08 |
| `Saturation` | 0.02 | 0.02 | 0.02 |
| `Bitcrusher` | 0.02 | 0.17 | 0.98 |
| `Exciter` | 0 | 0 | 0 |
| `CabinetSim` | 0 | 0 | 0 |
| `PitchShifter` | 0 | 0 | 0 |
| `Harmonizer` | 0 | 0 | 0 |
| `Octaver` | 0 | 0 | 0 |
| `StereoWidener` | 0 | 0 | 0 |
| `Rack` | 0 | 0 | 0 |
| `ShimmerHall` | 0 | 0 | 0 |
| `AirSpace` | 0 | 0 | 0 |

Racks report the sum of their children. A `Rack` built from the five-effect
chain `NoiseGate`, `Compressor`, `Overdrive`, `Chorus`, `Reverb` (the usual
order on a guitar or a voice: clean up, level, colour, move, place) reports
**0 ms** at defaults, and **0 ms** with each effect on its worst shipped
patch. Latency adds up along a chain, so the effects to watch are the few
with a number: `ConvolutionReverb` (5.33 ms while an impulse is loaded),
`Limiter` (up to 10 ms of lookahead, 2.98 ms on its true-peak patch),
`Vibrato` (its mean delay, 4 ms by default), and the drive effects that
oversample, which add a few samples.

Two things the figure does not say. `PitchShifter`, `Harmonizer` and
`Octaver` leave the dry untouched, so they report zero, yet the shifted
voice they add trails the dry by the shifter's window. `StereoWidener`'s Haas
delay puts the right channel behind the left on purpose, and that is not
counted either.

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

Beneath the components sits a harder guarantee: the audiodsp core — the
CircuitPython-compatible `synthio`/`audiocore`/effects-module layer — is
held bit-exact to CircuitPython itself, verified by parity gates, and
that never changes release to release. Where we find CircuitPython and
audiodsp disagree, we treat it as a bug and report it upstream. The
components are where the sound evolves; the floor they stand on does
not.


## Deliberately absent

- **Pitch correction** - needs pitch detection (YIN or autocorrelation), and
  that is off the roadmap for good rather than pending. `PitchShifter` will
  shift by an interval you name; nothing here works out what interval to ask
  for.
- **Sample-rate reduction as a stock Distortion mode** - CircuitPython's
  LOFI masks low bits and nothing else. `Bitcrusher` holds both
  word length and hold rate on `audioshaper`, and it is what the package
  serves.
- LFO-driven parameters update at the block rate (~187 Hz at 48 kHz),
  plenty for sweep rates but not audio-rate modulation. `RingMod` is the
  exception and does not use an LFO at all - see below.


## A note on how low a filter can go

Anywhere in the band on `audiobiquad`, which is what the filters and
EQs here are built on. On `synthio.Biquad` - and so `audiofilters.Filter` and
a `Note.filter` chain - the low end is CircuitPython's, on every target, and
it is worth knowing why.

CircuitPython keeps a biquad's coefficients as Q15 integers, which is the
right trade on a microcontroller and costs low frequencies. Below about
300 Hz they quantize into something that is no longer the filter you asked
for: a `LowPass` at 100 Hz returned **silence**, a `HighPass` at 30 Hz
returned **+21 dB of noise**, and a low shelf at 80 Hz lifted the whole band
by 13.4 dB instead of its 1.5. A low-pass fed a DC burst can also park at a
fixed point for ever - half of full scale from a 40 Hz low-pass.

audiodsp widened that arithmetic once for every biquad. Since audiodsp#77 the
split is by ownership: `synthio.Biquad` is a node CircuitPython also has, so
it runs CircuitPython's arithmetic everywhere (at the current floor that
80 Hz shelf reads -7.65 dB), and the widened kernel belongs to
`audiobiquad`, which is audiodsp's own. There, coefficients get as many
fractional bits as each filter has room for, the recursion accumulates in
64 bits and keeps its feedback below the sample grid, and the trigonometry
is a proper series. Measured against the closed-form response, every mode
lands within **0.03 dB from 50 Hz to 22 kHz**. Ten octave bands all read
+6.01 dB or better on a +6 dB request, read on `ParametricEQ`. The
`MultibandCompressor` sums to 0.12 dB from 30 Hz to 20 kHz on
`audiobiquad`'s float sections. `Saturation` builds its shelves there too,
and falls back to `synthio.Biquad` only where `audiobiquad` is missing.
[audiodsp's `docs/upstream-diff.md`](https://github.com/PyDevices/audiodsp/blob/main/docs/upstream-diff.md),
"The biquads were Q15, so they could not go low", has the arithmetic.

Nothing refuses a low frequency and nothing ever did, because a
`LadderFilter` sweeping down through 40 Hz is a legitimate thing to do.
The only remaining rule is the one that was always real: stay below
Nyquist, which `check_hz` enforces.

## A note on patches

Some classes carry **patches**: named settings on the same 0-127 MIDI grid
`audioinstruments` uses, so a host or an app can offer presets and automate
knobs without knowing what any particular effect's arguments mean.

```python
mod = audioeffects.RingMod(source, patch=1)   # "Textbook AM"
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
class. See `docs/reference/metadata.md` for the complete rack rule.

## A note on chaining after a Mixer

Several classes here end in an `audiomixer.Mixer` - anything that splits
into parallel branches and sums them. On MicroPython and CPython you can
chain freely after one. On CircuitPython you cannot: its Mixer stops its
voices when it is reset, and every effect resets its source when you
`play()` it, so the chain goes silent. audiodsp fixes that for its own
builds; see [audiodsp's `docs/upstream-diff.md`](https://github.com/PyDevices/audiodsp/blob/main/docs/upstream-diff.md), "Resetting a Mixer silenced it".

## A note on filters off a stock CircuitPython board

Every frequency in this library is the frequency you get - on audiodsp.
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
  upstream. It no longer reaches the catalogue's bells: `ParametricEQ`,
  `GraphicEQ` and `DynamicEQ` are all built on `audiobiquad`, which
  computes the sign correctly in its own float kernel and never went
  through this.
- Biquad coefficients are Q15 and the recursion accumulates in 32 bits, so
  nothing below roughly 300 Hz is the filter it was asked to be, and one
  polynomial covers sine and cosine only as far as π/2 - 12 kHz at 48 kHz -
  so nothing near Nyquist is either. Both ends fail quietly. Still present
  upstream, and the section above is what a filter does here instead.

This library used to compensate for both - halving every frequency on the
way in, and synthesizing bells out of notch and band-pass sections. It no
longer does, because the engine is right. See [audiodsp's `docs/upstream-diff.md`](https://github.com/PyDevices/audiodsp/blob/main/docs/upstream-diff.md) for
the measurements and the one-line coefficient fix.

## Testing

[`tests/test_cpython_effects_library.py`](../../tests/test_cpython_effects_library.py) holds every class in
`audioeffects.ALL` to the contract - exports and metadata, the factory,
building and rendering, chaining, the patch surface - under CPython. What
each class *sounds* like is measured beside it, one module per family:
`test_cpython_effects_dynamics_eq.py` and `..._modulation.py`, plus one
module per class that has its own, with
`test_cpython_convolve_node.py` for the audioconvolve node underneath the
convolvers. [`tests/parity/effects_library_smoke.py`](../../tests/parity/effects_library_smoke.py) is the coarse half of
all that in portable Python, so MicroPython and patched CircuitPython can
walk the same catalogue - every class through `create()`, and every patch it
declares through `program_change()`. micropython-vst3's `tools/test-effects-lib.py`
additionally runs them inside a real VST3 host, feeding a quiet-then-loud sine and asserting
per-class behaviour: compressors and limiters squeeze the loud half,
gates and expanders mute the quiet one, everything else passes signal.
