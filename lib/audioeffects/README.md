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
also expose `set_*` helpers (`DigitalDelay.set_time`, ...). A class that
has been rebuilt on the component contract drops those helpers for its macro
surface: `LadderFilter` is the first, and its cutoff is macro 0.

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

### Dynamic range - one file per class

The seven Dynamics classes of the effects program's Phase 2, each rebuilt from
scratch against a frozen trait table and an evidence pack. They live as
`compressor.py`, `limiter.py`, `expander.py`, `noisegate.py`, `deesser.py`,
`transientshaper.py` and `multibandcompressor.py` beside this README. Every
one of them is **audioif** tier - none runs on a stock CircuitPython board -
and every one adds **zero samples of latency** at its defaults. Dossiers and
evidence packs are in the private workspace.

**Cost** is the class's own share of one 256-frame stereo block at 48 kHz,
measured on an ESP32-P4 at 360 MHz and an ESP32-S3 at 240 MHz on 2026-09-07
([`workspace docs/effects-internal/audits/effects-cost-table.md`](../../workspace docs/effects-internal/audits/effects-cost-table.md), "Phase 2
classes"). It is the **marginal** figure - the same run's control subtracted,
so the harness floor is not charged to the class - taken at construction
defaults with no patch applied. Twelve of the sixteen are over the budget
their dossier set, and the board run names the reason: those budgets were
instruction-count arithmetic that cannot see the per-block Python of a node
graph. Every one of the sixteen runs in real time on both boards.

**Home.** Phase 2's sixteen have come home. `rebuilt/` keeps the substitution
machinery and the two Example fixtures for the phases still to come;
`rebuilt.ADOPTED` no longer lists these names.

| Class | Tier | Macros | Latency | Cost | Standout |
|---|---|---|---|---|---|
| `Compressor` | audioif (`audiodynamics`, `audioroute`) | 14 | 0 samples | working patch 13 is 22.0 % P4 / 40.9 % S3, **over** its 19 % / 36 % palette budget; patch 14 `Compressor - lean` is **13.6 % / 24.2 %** and fits | UREI 1176 (FET), Teletronix LA-2A (Optical), dbx 160 (VCA/RMS) and Fairchild 670 (Vari-Mu) - four characters that differ in *law*, not in three numbers: `optical`, the default, has no working time knobs at all. **F2 is demonstrated at Threshold −8 dB and below.** **Bounded:** not clean on bass with a fast release - 3.89 % THD at 50 Hz and 10 dB of gain reduction with Release at its fastest, and three of its four 1176 patches over the 0.5 % bar at 50 Hz beside the all-buttons-in one, with patch 0's own defaults reading 0.83 % there; the true-RMS detector is level-honest only above about 65 Hz at the shipped 10 ms window |
| `Limiter` | audioif (`audiodynamics`) | 6 | 0 samples at the default and at *Loud*; up to **480** at 10 ms of Lookahead, 143 at *Loud (True Peak)* | **13.8 % P4 / 27.6 % S3** at working *Loud* (`rebuilt:Limiter@2`), inside the redefined **15 % / 29 %** palette pair (2 × bare `Dynamics` + glue 0.0 ms); rt **4.90 / 2.65**. **Redefined 2026-09-07** (vision §7.2): the old ITU working graph cannot run on the S3. Patch 5 *Loud (True Peak)* is that old graph — P4 rt 1.64 (fits 61 %), S3 **rt 0.80, unavailable**. True Peak on both stages costs the +options row twice (1.611 / 3.461 ms each) | none - a two-stage **sample-peak** brickwall (Hämäläinen catch stage so lookahead does not overshoot). The ITU-R BS.1770-5 4× true-peak detector is optional and **P4-priced**: leave it off on an S3. **What the default surrenders:** with True Peak off (the default), a worst-phase tone at a quarter of the sample rate leaves a −6 dBFS ceiling **3.01 dB high** in the reconstructed waveform at 48000, 44100 and 22050 Hz. **True Peak on, Lookahead 0** is a different setting: it still holds the sample ceiling only — a full-scale ramp then escapes a −6 dBFS ceiling by **+2.22 dB TP** |
| `Expander` | audioif (`audiodynamics`) | 9 | 0 samples | 8.4 % P4 / 16.3 % S3 of a block, **over** its 6 % / 12 % budget; patch 6 `Expander - lean` does **not** close G6 — the only cost lever is worth 5–8 % where the budget needs 26–29 % | Drawmer DS201 with RaneNote 155 - downward, `ratio` dB out per dB in below threshold to a `Depth` floor, true-RMS detector, two-ended key band, external key. The `ratio` law is the **RMS** detector's: at the Detector's peak position the slope falls 7.5 % short at ratio 8 and 29 % at patch 5's settings, which is what that patch is for. And the detector reads the key **band**, so a sine and a square of equal RMS match only while the band is wide and the ratio moderate - 0.55 dB apart at ratio 4, 0.74 dB at ratio 2 with the band closed to 3 kHz. No Hold: that is `NoiseGate`'s, and the reason is measured |
| `NoiseGate` | audioif (`audiodynamics`, `audioroute`, `audiomath`) | 8 | 0 samples | 4.5 % P4 / 8.4 % S3 of a block, inside its 6 % / 12 % budget | Drawmer DS201 dual noise gate - the four-stage attack/hold/decay machine the ratio law does not have, with the key filters always in circuit |
| `DeEsser` | audioif (`audiobiquad`, `audiodynamics`, `audioroute`) | 7 | 0 samples | 27.5 % P4 / 50.8 % S3 of a block, **over** its 8 % / 15 % budget, and no patch changes it - the cost is the graph, and seven macros do not change the graph | dbx 902 De-Esser - the detector is high-passed at `Frequency`, so only sibilance ducks the signal. Three bounds a player meets: the same setting works from -6 to -40 dBFS and stops being level-independent at -55; `Range` is an asymptote rather than a clamp, and the deepest reduction any setting reaches is about 11.5 dB; the 925 dB/sec release is the default `Release`'s, and the knob dials it from 1643 dB/sec to 20 |
| `TransientShaper` | audioif (`audiodynamics`) | 5 | 0 samples | 14.9 % P4 / 31.3 % S3 of a block, **over** its 5 % / 10 % budget, and no `" - lean"` patch can fit: every patch costs 102–106 % of patch 0 and a node doing nothing at all still costs 75 %. The figures above were taken at defaults, where this class is a wire, so they are an *idle* cost; patch 1 (Snap) is the working one | SPL Transient Designer (RackPack 2715), Differential Envelope Technology - more stick **and** less room from one instance, with no threshold and no ratio. Level-independent over −20 to −40 dBFS at any Attack, and −6 to −40 dBFS below Attack +6, where the render stops clipping; **not** across −6 to −60 dBFS as first claimed. Sustain reaches its −24 dB end on a 10 dB/s decay and stops 8 dB short on a 3 dB/s one |
| `MultibandCompressor` | audioif (`audiobiquad`, `audiodynamics`, `audioroute`) | 14 | 0 samples | 44.3 % P4 / 83.6 % S3 of a block, **over** its 25 % / 45 % budget. The S3 row leaves 8 % of the block for everything else on the chip, and **no patch is cheaper**: all 243 macro positions and shipped patches walked, the graph is the same 18 nodes and 72 pulls at every one, and bypassed at `Mix` 0 the class costs 102 % of what it costs working. `bands=2` is the only lever - 12 nodes, 48 pulls, 75-79 % of the three-band desktop cost - and it is a constructor option, not a patch | none - RaneNote 155 Fig. 7 over a Linkwitz-Riley alignment (RaneNote 160): three bands split, compressed and summed back to +0.001/−0.119 dB of a wire; `Mix` at 0 is a true bypass. **A band does not compress evenly across its own passband**: out to its −6 dB corners the reduction tilts 1.82 / 1.31 / 1.42 dB (low / mid / high) against a 0.5 dB bar and lands 0.09 / 0.73 / 0.36 dB short of the depth dialled — the band's own skirt against a fixed threshold, disconfirmed with the arithmetic in the docstring |

### Frequency and EQ - one file per class

The nine EQ and filter classes of Phase 2, on the same terms, each in its
own file (`parametriceq.py`, `graphiceq.py`, `lowpass.py`, `highpass.py`,
`bandpass.py`, `notch.py`, `ladderfilter.py`, `combfilter.py`,
`dynamiceq.py`): all **audioif**
tier (`audiobiquad`, `audioladder` or `audioecho` - the float nodes, whose
tails reach exact zero where the ported integer kernel parks on DC), all
**zero latency** at every setting, none of them available on a stock
CircuitPython board.

Cost is read the same way as for the Dynamics table above: the
marginal share of one block on each board at construction defaults.

| Class | Tier | Macros | Latency | Cost | Standout |
|---|---|---|---|---|---|
| `ParametricEQ` | audioif (`audiobiquad`) | 16 | 0 samples | 15.2 % P4 / 25.3 % S3 of a block, inside its 26 % / 43 % budget; at defaults this class passes the probe through unchanged, so it is an *idle* cost | Pultec EQP-1A bottom and resonant top with three API 550A proportional-Q bells between: boost and cut the bass at once and you get the record trick, not silence; a bell's cut is the exact mirror of its boost **while the signal has headroom for the boost** - every section writes int16, so at -6 dBFS a +16 dB bell delivers +8.4 dB and the mirror is 8.05 dB out. Measured per trait: the mirror holds to -16 dBFS, the Bandwidth pot's peak-gain lift to -14, the bells' proportional-Q ratio to -10, and the Pultec low pair at every level tried (evidence pack section 1d) |
| `GraphicEQ` | audioif (`audiobiquad`) | 14 | 0 samples | 22.7 % P4 / 38.6 % S3 of a block, inside its 38 % / 64 % budget; at defaults this class passes the probe through unchanged, so it is an *idle* cost | MXR M-108 Ten Band - ten octave bands from 31.25 Hz whose bells **get wider as you back off**, 1.8 octaves at +3 dB and 0.71 at +12, so three sliders at +6 dB make a +8.78 dB hump. A band at its detent is a wire byte for byte. The 16 kHz **shelf** needs headroom: full lift to a source peaking about 13 000 LSB (-8.1 dBFS), +8.78 dB at 14 000, and `Gain` +9 dB against `Volume` -9 dB takes it to +7.40 dB, and a patch's own `Volume` trim comes off it as well - add the trim back and the lift is +11.98 to +12.08 dB at all six |
| `DynamicEQ` | audioif (`audiobiquad`, `audiodynamics`, `audioroute`) | 8 | 0 samples | 14.5 % P4 / 26.0 % S3 of a block at patch 0 against the palette-derived 17 % / 29 % (listed remainder; `Splitter` taps=3 is a named gap). T2/T5 miss above ~5 ms attack; T4/T6 out-of-band miss below Q 2 | none - the exactly complementary split: one bell that does nothing until the sound *in that band* crosses a threshold, and a measured **wire** when it is idle |
| `LowPass` | audioif (`audiobiquad`) | 5 | 0 samples | 5.6 % P4 / 9.6 % S3 of a block, **over** its 1.5 % / 5 % budget, and no `" - lean"` patch is possible: every section runs whatever its `mix` is, so no macro position is cheaper than any other | none - the two-pole analog prototype `H(s) = 1/(s² + 2Rs + 1)`: one knob slides the curve, one decides how loud the corner stands, −3 dB at Resonance 0.707 and +24 dB at 16. **Exact except at the bottom of the Frequency knob**: at f₀ 20 Hz with Q 16 at 24 dB/oct the corner stands 0.44 dB low and the curve stops being one shape below 25 Hz (float32 coefficients near z = 1), and "rings for Q periods" is a 12 dB/oct statement below about 0.17·F_s - at 24 dB/oct the ring runs 1.36× the Resonance number at Q 2 up to 1.71× at Q 16. The roll-off, −12.03 dB/oct on the warped axis with unity DC, holds everywhere |
| `HighPass` | audioif (`audiobiquad`) | 5 | 0 samples | 5.7 % P4 / 9.6 % S3 of a block, **over** its 1.5 % / 5 % budget, and no patch on this surface is cheaper - patch 0 is already one live section and two wires | none - RBJ's two-pole low-cut, with an exact transmission zero at DC: a held offset decays to zero rather than to the 71 LSB the ported node parks on at a 10 Hz corner. Two bounds, measured: the two numbers on the panel are exact only above about 40 Hz at 48 kHz - at a 10 Hz corner the peak is 0.6 dB shy of `Resonance` (Q 8, 24 dB/oct) and the curve is 0.21 dB off its own shape, both the node's `float` coefficients rather than the cut - and at 24 dB/oct the corner **rings 1.85x longer** than the knob says, which is the price of reading the same gain at both slopes. The cut, the 12/24 dB/oct skirt and the exact zero at DC hold everywhere |
| `BandPass` | audioif (`audiobiquad`) | 4 | 0 samples | 3.8 % P4 / 6.2 % S3 of a block, inside its 4 % / 13 % budget, and the same at every patch | none - the two-pole resonant band-pass in RBJ's constant 0 dB peak-gain form, so `Width` moves the skirts without moving the peak. **Above 100 Hz.** Below it, at Q >= 4, the peak loses up to 0.50 dB and the loss changes sign with the level: the kernel's float32 recursion, not the form (audioif#64). The +-6 dB/oct and -3 dB figures are Q 0.707 statements below about 2 kHz - above that the bilinear warp moves them, and this class tracks the warped prototype to 0.009 dB |
| `Notch` | audioif (`audiobiquad`) | 5 | 0 samples | 5.6 % P4 / 9.6 % S3 of a block, **over** its 1.5 % / 5 % budget; a `" - lean"` patch is still owed and none was invented | none (the Twin-T was weighed and dropped on scope) - a band-stop whose `Width` is a bandwidth and not a depth, with a Harmonics toggle for mains hum. A `float` coefficient set cannot put the zeros exactly on the unit circle, so at 60 Hz it is a hum *reducer*, not an eliminator |
| `LadderFilter` | audioif (`audioladder`) | 7 | 0 samples | 16.2 % P4 / 26.7 % S3 of a block at patch 4 against the palette-derived 17 % / 28 %; lean patch 6 is 8.6 % / 14.7 %. T5 and T1's stopband slope stay disconfirmed | the Moog transistor ladder - four one-pole stages round one global feedback loop with an odd saturator **inside** it, so the passband sinks as `Resonance` rises. That droop is the circuit |
| `CombFilter` | audioif (`audioecho`, `audiobiquad`) | 6 | 0 samples | 7.4 % P4 / 12.2 % S3 of a block at patch 0 against the palette-derived 8 % / 13 %. Above Feedback 0.5 the parked ring's period is the nearest whole number of samples to F_s/Frequency, not the fractional delay the comb was asked for: +17.4 cents at 1760 Hz / Feedback 0.8 (27 samples at 48 kHz) and at most a half-sample — about 70 cents — near 4 kHz. The first-repeat tap still lands within 0.01 cents. Below Feedback 0.5, and at half-sample tunings, the tail reaches exact zero. T2/T5 miss at fractional tunings | none - the naked textbook feedback comb `y(n) = x(n) + g·y(n−M)`: a delay short enough to be a pitch, fed back, so noise grows resonances on that note's harmonic series |

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
**0.03 dB from 50 Hz to 22 kHz**. Ten octave bands all read +6.01 dB or
better on a +6 dB request - the claim `GraphicEQ` used to carry, and read on
`ParametricEQ` since both were rebuilt onto `audiobiquad`. The pre-rebuild
`MultibandCompressor`'s three bands recombined flat to 0.23 dB from 30 Hz to
8 kHz on those Q15 biquads; the rebuilt class is on `audiobiquad`'s float
sections instead, for the tail rather than the shape, and sums to 0.12 dB
from 30 Hz to 20 kHz. [audioif's `docs/upstream-diff.md`](https://github.com/PyDevices/audioif/blob/main/docs/upstream-diff.md),
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
  upstream. It no longer reaches the catalogue's bells: `ParametricEQ`,
  `GraphicEQ` and `DynamicEQ` are all rebuilt onto `audiobiquad`, which
  computes the sign correctly in its own float kernel and never went
  through this. The old family `eq.py:ParametricEQ` used the ported
  kernel; that module is gone.
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
