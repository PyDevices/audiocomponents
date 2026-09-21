# audioeffects

Forty-five effect classes built out of audiodsp's audio nodes, for any host
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

Beneath the components sits a harder guarantee: the audiodsp core — the
CircuitPython-compatible `synthio`/`audiocore`/effects-module layer — is
held bit-exact to CircuitPython itself, verified by parity gates, and
that never changes release to release. Where we find CircuitPython and
audiodsp disagree, we treat it as a bug and report it upstream. The
components are where the sound evolves; the floor they stand on does
not.

## Catalogue

### Dynamic range - one file per class

The seven Dynamics classes of the effects program's Phase 2, each rebuilt from
scratch against a frozen trait table and an evidence pack. They live as
`compressor.py`, `limiter.py`, `expander.py`, `noisegate.py`, `deesser.py`,
`transientshaper.py` and `multibandcompressor.py` beside this README. Every
one of them is **audiodsp** tier - none runs on a stock CircuitPython board -
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
| `Compressor` | audiodsp (`audiodynamics`, `audioroute`) | 14 | 0 samples | working patch 13 is 22.0 % P4 / 40.9 % S3, **over** its 19 % / 36 % palette budget; patch 14 `Compressor - lean` is **13.6 % / 24.2 %** and fits | UREI 1176 (FET), Teletronix LA-2A (Optical), dbx 160 (VCA/RMS) and Fairchild 670 (Vari-Mu) - four characters that differ in *law*, not in three numbers: `optical`, the default, has no working time knobs at all. **F2 is demonstrated at Threshold −8 dB and below.** **Bounded:** not clean on bass with a fast release - 3.89 % THD at 50 Hz and 10 dB of gain reduction with Release at its fastest, and three of its four 1176 patches over the 0.5 % bar at 50 Hz beside the all-buttons-in one, with patch 0's own defaults reading 0.83 % there; the true-RMS detector is level-honest only above about 65 Hz at the shipped 10 ms window |
| `Limiter` | audiodsp (`audiodynamics`) | 6 | 0 samples at the default and at *Loud*; up to **480** at 10 ms of Lookahead, 143 at *Loud (True Peak)* | **13.8 % P4 / 27.6 % S3** at working *Loud* (`rebuilt:Limiter@2`), inside the redefined **15 % / 29 %** palette pair (2 × bare `Dynamics` + glue 0.0 ms); rt **4.90 / 2.65**. **Redefined 2026-09-07** (vision §7.2): the old ITU working graph cannot run on the S3. Patch 5 *Loud (True Peak)* is that old graph — P4 rt 1.64 (fits 61 %), S3 **rt 0.80, unavailable**. True Peak on both stages costs the +options row twice (1.611 / 3.461 ms each) | none - a two-stage **sample-peak** brickwall (Hämäläinen catch stage so lookahead does not overshoot). The ITU-R BS.1770-5 4× true-peak detector is optional and **P4-priced**: leave it off on an S3. **What the default surrenders:** with True Peak off (the default), a worst-phase tone at a quarter of the sample rate leaves a −6 dBFS ceiling **3.01 dB high** in the reconstructed waveform at 48000, 44100 and 22050 Hz. **True Peak on, Lookahead 0** is a different setting: it still holds the sample ceiling only — a full-scale ramp then escapes a −6 dBFS ceiling by **+2.22 dB TP** |
| `Expander` | audiodsp (`audiodynamics`) | 9 | 0 samples | 8.4 % P4 / 16.3 % S3 of a block, **over** its 6 % / 12 % budget; patch 6 `Expander - lean` does **not** close G6 — the only cost lever is worth 5–8 % where the budget needs 26–29 % | Drawmer DS201 with RaneNote 155 - downward, `ratio` dB out per dB in below threshold to a `Depth` floor, true-RMS detector, two-ended key band, external key. The `ratio` law is the **RMS** detector's: at the Detector's peak position the slope falls 7.5 % short at ratio 8 and 29 % at patch 5's settings, which is what that patch is for. And the detector reads the key **band**, so a sine and a square of equal RMS match only while the band is wide and the ratio moderate - 0.55 dB apart at ratio 4, 0.74 dB at ratio 2 with the band closed to 3 kHz. No Hold: that is `NoiseGate`'s, and the reason is measured |
| `NoiseGate` | audiodsp (`audiodynamics`, `audioroute`, `audiomath`) | 8 | 0 samples | 4.5 % P4 / 8.4 % S3 of a block, inside its 6 % / 12 % budget | Drawmer DS201 dual noise gate - the four-stage attack/hold/decay machine the ratio law does not have, with the key filters always in circuit |
| `DeEsser` | audiodsp (`audiobiquad`, `audiodynamics`, `audioroute`) | 7 | 0 samples | 27.5 % P4 / 50.8 % S3 of a block, **over** its 8 % / 15 % budget, and no patch changes it - the cost is the graph, and seven macros do not change the graph | dbx 902 De-Esser - the detector is high-passed at `Frequency`, so only sibilance ducks the signal. Three bounds a player meets: the same setting works from -6 to -40 dBFS and stops being level-independent at -55; `Range` is an asymptote rather than a clamp, and the deepest reduction any setting reaches is about 11.5 dB; the 925 dB/sec release is the default `Release`'s, and the knob dials it from 1643 dB/sec to 20 |
| `TransientShaper` | audiodsp (`audiodynamics`) | 5 | 0 samples | 14.9 % P4 / 31.3 % S3 of a block, **over** its 5 % / 10 % budget, and no `" - lean"` patch can fit: every patch costs 102–106 % of patch 0 and a node doing nothing at all still costs 75 %. The figures above were taken at defaults, where this class is a wire, so they are an *idle* cost; patch 1 (Snap) is the working one | SPL Transient Designer (RackPack 2715), Differential Envelope Technology - more stick **and** less room from one instance, with no threshold and no ratio. Level-independent over −20 to −40 dBFS at any Attack, and −6 to −40 dBFS below Attack +6, where the render stops clipping; **not** across −6 to −60 dBFS as first claimed. Sustain reaches its −24 dB end on a 10 dB/s decay and stops 8 dB short on a 3 dB/s one |
| `MultibandCompressor` | audiodsp (`audiobiquad`, `audiodynamics`, `audioroute`) | 14 | 0 samples | 44.3 % P4 / 83.6 % S3 of a block, **over** its 25 % / 45 % budget. The S3 row leaves 8 % of the block for everything else on the chip, and **no patch is cheaper**: all 243 macro positions and shipped patches walked, the graph is the same 18 nodes and 72 pulls at every one - the one exception is `Mix` 0, where `output` is the class's input node and nothing it owns is pulled at all, and no shipped patch sits there. `bands=2` is the only lever - 12 nodes, 48 pulls, 75-79 % of the three-band desktop cost - and it is a constructor option, not a patch | none - RaneNote 155 Fig. 7 over a Linkwitz-Riley alignment (RaneNote 160): three bands split, compressed and summed back to +0.001/−0.119 dB of a wire; `Mix` at 0 is a true bypass, with no mixer in the path: a voice at level 1.0 scales by 32768/32767 (audiodsp#95). **A band does not compress evenly across its own passband**: out to its −6 dB corners the reduction tilts 1.82 / 1.31 / 1.42 dB (low / mid / high) against a 0.5 dB bar and lands 0.09 / 0.73 / 0.36 dB short of the depth dialled — the band's own skirt against a fixed threshold, disconfirmed with the arithmetic in the docstring |

### Frequency and EQ - one file per class

The nine EQ and filter classes of Phase 2, on the same terms, each in its
own file (`parametriceq.py`, `graphiceq.py`, `lowpass.py`, `highpass.py`,
`bandpass.py`, `notch.py`, `ladderfilter.py`, `combfilter.py`,
`dynamiceq.py`): all **audiodsp**
tier (`audiobiquad`, `audioladder` or `audioecho` - the float nodes, whose
tails reach exact zero where the ported integer kernel parks on DC), all
**zero latency** at every setting, none of them available on a stock
CircuitPython board.

Cost is read the same way as for the Dynamics table above: the
marginal share of one block on each board at construction defaults.

| Class | Tier | Macros | Latency | Cost | Standout |
|---|---|---|---|---|---|
| `ParametricEQ` | audiodsp (`audiobiquad`) | 16 | 0 samples | 15.2 % P4 / 25.3 % S3 of a block, inside its 26 % / 43 % budget; at defaults this class passes the probe through unchanged, so it is an *idle* cost | Pultec EQP-1A bottom and resonant top with three API 550A proportional-Q bells between: boost and cut the bass at once and you get the record trick, not silence; a bell's cut is the exact mirror of its boost **while the signal has headroom for the boost** - every section writes int16, so at -6 dBFS a +16 dB bell delivers +8.4 dB and the mirror is 8.05 dB out. Measured per trait: the mirror holds to -16 dBFS, the Bandwidth pot's peak-gain lift to -14, the bells' proportional-Q ratio to -10, and the Pultec low pair at every level tried (evidence pack section 1d) |
| `GraphicEQ` | audiodsp (`audiobiquad`) | 14 | 0 samples | 22.7 % P4 / 38.6 % S3 of a block, inside its 38 % / 64 % budget; at defaults this class passes the probe through unchanged, so it is an *idle* cost | MXR M-108 Ten Band - ten octave bands from 31.25 Hz whose bells **get wider as you back off**, 1.8 octaves at +3 dB and 0.71 at +12, so three sliders at +6 dB make a +8.78 dB hump. A band at its detent is a wire byte for byte. The 16 kHz **shelf** needs headroom: full lift to a source peaking about 13 000 LSB (-8.1 dBFS), +8.78 dB at 14 000, and `Gain` +9 dB against `Volume` -9 dB takes it to +7.40 dB, and a patch's own `Volume` trim comes off it as well - add the trim back and the lift is +11.98 to +12.08 dB at all six |
| `DynamicEQ` | audiodsp (`audiobiquad`, `audiodynamics`, `audioroute`) | 8 | 0 samples | 14.5 % P4 / 26.0 % S3 of a block at patch 0 against the palette-derived 17 % / 29 % (listed remainder; `Splitter` taps=3 is a named gap). T2/T5 miss above ~5 ms attack; T4/T6 out-of-band miss below Q 2 | none - the exactly complementary split: one bell that does nothing until the sound *in that band* crosses a threshold, and a measured **wire** when it is idle |
| `LowPass` | audiodsp (`audiobiquad`) | 5 | 0 samples | 5.6 % P4 / 9.6 % S3 of a block, **over** its 1.5 % / 5 % budget, and no `" - lean"` patch is possible: every section runs whatever its `mix` is, so no macro position is cheaper than any other | none - the two-pole analog prototype `H(s) = 1/(s² + 2Rs + 1)`: one knob slides the curve, one decides how loud the corner stands, −3 dB at Resonance 0.707 and +24 dB at 16. **Exact except at the bottom of the Frequency knob**: at f₀ 20 Hz with Q 16 at 24 dB/oct the corner stands 0.44 dB low and the curve stops being one shape below 25 Hz (float32 coefficients near z = 1), and "rings for Q periods" is a 12 dB/oct statement below about 0.17·F_s - at 24 dB/oct the ring runs 1.36× the Resonance number at Q 2 up to 1.71× at Q 16. The roll-off, −12.03 dB/oct on the warped axis with unity DC, holds everywhere |
| `HighPass` | audiodsp (`audiobiquad`) | 5 | 0 samples | 5.7 % P4 / 9.6 % S3 of a block, **over** its 1.5 % / 5 % budget, and no patch on this surface is cheaper - patch 0 is already one live section and two wires | none - RBJ's two-pole low-cut, with an exact transmission zero at DC: a held offset decays to zero rather than to the 71 LSB the ported node parks on at a 10 Hz corner. Two bounds, measured: the two numbers on the panel are exact only above about 40 Hz at 48 kHz - at a 10 Hz corner the peak is 0.6 dB shy of `Resonance` (Q 8, 24 dB/oct) and the curve is 0.21 dB off its own shape, both the node's `float` coefficients rather than the cut - and at 24 dB/oct the corner **rings 1.85x longer** than the knob says, which is the price of reading the same gain at both slopes. The cut, the 12/24 dB/oct skirt and the exact zero at DC hold everywhere |
| `BandPass` | audiodsp (`audiobiquad`) | 4 | 0 samples | 3.8 % P4 / 6.2 % S3 of a block, inside its 4 % / 13 % budget, and the same at every patch | none - the two-pole resonant band-pass in RBJ's constant 0 dB peak-gain form, so `Width` moves the skirts without moving the peak. The peak holds within 0.05 dB in 55 of 56 measured cells, both knob stops included; the one miss is -0.09 dB at f0 31.5 Hz with Q 32 (audiodsp#64 fixed the rest). The +-6 dB/oct and -3 dB figures are Q 0.707 statements below about 2 kHz - above that the bilinear warp moves them, and this class tracks the warped prototype to 0.009 dB |
| `Notch` | audiodsp (`audiobiquad`) | 5 | 0 samples | 5.6 % P4 / 9.6 % S3 of a block, **over** its 1.5 % / 5 % budget; a `" - lean"` patch is still owed and none was invented | none (the Twin-T was weighed and dropped on scope) - a band-stop whose `Width` is a bandwidth and not a depth, with a Harmonics toggle for mains hum. A `float` coefficient set cannot put the zeros exactly on the unit circle, so at 60 Hz it is a hum *reducer*, not an eliminator |
| `LadderFilter` | audiodsp (`audioladder`) | 7 | 0 samples | 16.2 % P4 / 26.7 % S3 of a block at patch 4 against the palette-derived 17 % / 28 %; lean patch 6 is 8.6 % / 14.7 %. T5 and T1's stopband slope stay disconfirmed | the Moog transistor ladder - four one-pole stages round one global feedback loop with an odd saturator **inside** it, so the passband sinks as `Resonance` rises. That droop is the circuit |
| `CombFilter` | audiodsp (`audioecho`, `audiobiquad`) | 6 | 0 samples | 7.4 % P4 / 12.2 % S3 of a block at patch 0 against the palette-derived 8 % / 13 %. Above Feedback 0.5 the parked ring's period is the nearest whole number of samples to F_s/Frequency, not the fractional delay the comb was asked for: +17.4 cents at 1760 Hz / Feedback 0.8 (27 samples at 48 kHz) and at most a half-sample — about 70 cents — near 4 kHz. The first-repeat tap still lands within 0.01 cents. Below Feedback 0.5, and at half-sample tunings, the tail reaches exact zero. T2/T5 miss at fractional tunings | none - the naked textbook feedback comb `y(n) = x(n) + g·y(n−M)`: a delay short enough to be a pitch, fed back, so noise grows resonances on that note's harmonic series |
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
run on `audioecho.FeedbackDelay`, which is where audiodsp puts those. A
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

### Modulation - six at home, one still in `rebuilt/`

Phase 3's THROUGH classes (`AutoPan`, `Chorus`, `Phaser`, `Tremolo`,
`Vibrato`) and `RingMod` have come home as one file per effect beside this
README. `Flanger` stays parked under `rebuilt/`; the package still serves
`modulation.Flanger`. `modulation.py` cannot be deleted while Flanger
remains. Every one of them is **audiodsp** tier - none runs on a stock
CircuitPython board.

**Cost** is the class's own share of one 256-frame stereo block at 48 kHz
where the board stage has run, else the dossier palette budget. A
`" - lean"` patch is named only where one exists.

| Class | Tier | Macros | Latency | Cost | Standout |
|---|---|---|---|---|---|
| `Chorus` | audiodsp (`audioecho`) | 5 | 0 samples; wet Delay 3–20 ms is the effect, not lookahead | **8.1 % P4 / 9.8 % S3** at patch 0 (ROW marg 0.431 / 0.524 ms), inside palette **P4 ≤ 9 % / S3 ≤ 15 %**; no lean patch | Electro-Harmonix Small Clone - one BBD voice, clock-law triangle, Mix 0 a wire. **What the default surrenders:** the within-half pitch-offset ratio is 1.98, not (d_max/d_min)² = 3.60 (T2). Tone 12 kHz is 2.4 dB down at 10 kHz, not ≥10 dB (T3). The constructor Tone 3 kHz still meets T3 |
| `Flanger` | audiodsp (`audioecho`; `audioroute` only when Through Zero is on) | 12 | 0 samples at defaults; Through Zero off by default, **10 ms / 480 samples at Range max / 48 kHz** when on | **0.672 ms/block P4 (rt 7.94) / 1.081 ms S3 (rt 4.93)** at patch 0, inside palette **9 % / 15 %** (FeedbackDelay +options; no extra looping RawSample); no lean patch | Electro-Harmonix Electric Mistress - BBD swept comb, Filter Matrix, Mix 0–2. **What the default gives up:** Color 0.55 / Matrix off is about −22 dB and 0.1 s, not the Color-0 −37 dB null or the 2 s Color-max ring; Color 0→0.9 holds +15 dB at 48 / 44.1 / 22.05 kHz on noise (held 3 ms, Matrix on). Color max (0.99, 3 ms, Matrix on) is the 2 s ring on a 200–440 Hz burst; the default is not, and a click is not that bar. |
| `Phaser` | audiodsp (`audiobiquad`, `audioshaper`) | 10 | 0 samples at every setting | Palette **15 % P4 / 24 % S3** (AllPass-6 0.248 / 0.423 + Waveshaper ×1 0.223 / 0.410 + extra synthio 0.317 / 0.408 + glue 0.0). The old **9 % / 16 %** bar omitted the LFO: the palette could not price a `synthio` source. Quoted ROW **8.5 % / 15.6 %**. Patch 8 `Phaser - lean` (Drive 0) is AllPass alone → **5/8 %**. | MXR Phase 90 — four first-order all-pass stages, JFET as the variable resistor. **What the default surrenders:** Drive 0.3 is on at construction. Feedback's inter-notch peak then misses the 5 dB bar (600–1800 Hz rise −0.633 dB at 48 kHz) and the notch floor is not monotone (0.5→0.7 −1.204 dB). Both hold at Drive 0. The floor's 0.5→0.7 step also deepens at 22.05 kHz with Drive 0 (−1.286 dB). |
| `Tremolo` | audiodsp (`audiomath`) | 9 | 0 samples; Lag is table shape, not a delay | Palette **7 % P4 / 9 % S3** (Multiply 0.028 / 0.047 + extra synthio 0.317 / 0.408 + glue 0.0). 1024-point board ROW **2.4 % / 4.9 %** (P4 marg 0.128 / ctrl 0.346, rt 11.23; S3 marg 0.265 / ctrl 0.532, rt 6.69). Prior 256-point ROW **2.3 / 4.9** is a shorter waveform. No lean patch | Fender Princeton 6G2 bias-vary and AB763 optical. **What the default surrenders:** Default is bias, Depth 0.5, Rate 5 Hz — not the optical standout and not L1's Depth 1. Wet peak at the default is −1.341 dB vs a 16000-LSB tone, not the ~6 dB `synthio` `>>16` ceiling; Depth 0 is still a wire. At 22.05 kHz the default's L1 bar is measured at the constructor, not assumed. Optical L1/L2 are disconfirmed; O1–O4 unmeasured at the constructor. L1 holds on sine at every rate, and misses by 0.16 dB on SQUARE material at 44.1 kHz only (−79.844 against −80; 48 kHz holds at −82.01). |
| `Vibrato` | audiodsp (`audioecho`) | 8 | **mean Delay**; default **192 samples / 4.0 ms at 48 kHz** (wet alone); constructor and `program_change(0)` stay on that whole-sample bin | Palette **9 % P4 / 15 % S3** (`FeedbackDelay` +options, Mixer optioned off at Level 0 dB). Prior Mixer-in-path ROW **9.5 / 15.3 %** is stale. Board ROW of the Delay-only graph **unmeasured**. No lean patch | BBD clock-law vibrato (VB-2). Level 0 dB leaves the Mixer out of the pull. **What the default surrenders:** T1's any-2 kHz-window no-dry clause (Tone −3 dB at 17 kHz). At 22.05 kHz a 2 kHz window can tilt past 1 dB. The 17 kHz −3 dB band is at 48 kHz with a whole-sample Delay. T4 and T7 magnitude are Published defaults only. T7 quadrature is disconfirmed |
| `AutoPan` | audiodsp (`audiomath`) | 7 | 0 samples | Palette **6 % P4 / 10 % S3** (`Multiply` 0.028 / 0.047 + extra synthio 1500 0.263 / 0.472 + glue 0.0). The old **1 % / 1 %** bar counted Multiply only: the palette could not price a `synthio` source. Quoted ROW **2.5 % / 4.5 %**. No lean patch | none (grade *design*). **What the default surrenders:** Rate starts at 2 Hz, not a slow 0.05 Hz wander — a 256-frame hold at 0.05 Hz reads under −80 dB, so A3's plant cannot fire on the old floor. The oscillator is two `synthio.Note`s, which top out at half scale (P12): hard-over is −6 dB vs the source. A mono source is a wire. |
| `RingMod` | audiodsp (`audiomath`) | 12 | 0 samples | Palette **7 % / 9 %** at Clean Ring (Multiply 0.028 / 0.047 + extra synthio 0.317 / 0.408 + glue 0.0). The old **3 % / 5 %** bar used a 256-frame RawSample stand-in: the palette could not price a `synthio` source. The **18 % / 52 %** bar counted a 1964-frame looping RawSample. Quoted ROW **4.4 % / 4.8 %**. Demonstrated traits are **M1** and **M3** only. | Bode four-diode ring (Moog 6401). **What the default surrenders:** Default is the multiplier at Frequency 220 Hz, Depth 1, Mix 1 — not the switching standout and not W1's Shape 1. At that default, 3·f₂+f₁ sits at **−92.2 dB** (1 s rect, 48 kHz), not in W1's −9.5±3 dB window, so W1 is disconfirmed at the constructor default. Wet RMS is **−9.03 dB** vs the program (M2 disconfirmed): Q15 product −3.01 dB plus the `synthio` voice sum. Squelch, Threshold and Release do not move the audio (M5 disconfirmed). Shape is a byte no-op until Character is flipped. Switching products at Character 1 Shape 1 are not a demonstrated row. Carrier Low's 5 Hz HPF is **not a demonstrated claim** (M4 disconfirmed): a same-kind plant moves **0.0022 dB** at Frequency 220 and **8.6 dB** only at 2 Hz. |

### Drive - four at home, three adopted and on their way

Phase 4's first four (`Overdrive`, `Distortion`, `Bitcrusher`, `CabinetSim`)
have come home as one file per effect beside this README. `Saturation`,
`Fuzz` and `Exciter` were **adopted on 2026-09-18** under Brad's G6 ruling -
the cost gate is a real-time ceiling, 80 % of one stereo block on both
chips, and all three are inside it at every shipped patch - so
`audioeffects.create()` serves the rebuilds now, from
`lib/audioeffects/rebuilt/`, until they come home too. Every one of the
seven is **audiodsp** tier - none runs on a stock CircuitPython board.

**Cost** is the dossier's palette budget of a 256-frame stereo block at
48 kHz, re-derived after the 2026-09-17 fix round for the graphs each class
now has - five of the seven lost nodes, so five of these numbers came down.
Every row now carries a measured board ROW beside its budget; where a row
quotes a number for a graph the boards have not seen since, it says so. A
`" - lean"` patch is named only where one exists; constructor `oversample=`
is not a patch.

| Class | Tier | Macros | Latency | Cost | Standout |
|---|---|---|---|---|---|
| `Overdrive` | audiodsp (`audioshaper`, `audiobiquad`, `audioroute`) | 7 | **0 samples** at every macro setting; the dry tap is a copy. `oversample` puts group delay on the clip branch only - 0.069 ms at x4, 0.088 ms at x8 - and it is not on the macro surface. `tail_samples` **4096** over a worst measured ring of **2692 frames** (48 kHz, patch 6, 0 dBFS burst), **level-free**: it was 512 over 222 frames until the third fix round put a 30 Hz output pole behind the shaper | Palette **32 % P4 / 55 % S3** (MidSide 0.028 / 0.018 + Splitter-2 0.165 / 0.395 + **4** x Biquad 0.400 / 0.676 + Waveshaper x4 1.019 / 1.803 + 2 x Mixer 0.072 / 0.036 + glue 0.0 = 1.684 / 2.928 ms). The fourth Biquad is the **30 Hz output pole** the third fix round put behind the shaper; it was 30 % / 52 % with three. The old **36 % / 63 %** priced the graph before the fix round, which took out two nodes. Board ROW of the fixed graph **34.1 % P4 / 64.7 % S3**, measured 2026-09-18 on both boards at audiodsp `e3b95e7`, inside the budget re-derived from that day's palette (**34 % / 66 %**); rt 2.41 / 1.28; the pre-fix graph read 35.3 % / 68.5 %. Lean position `oversample=2` **21 % / 37 %**, and it surrenders T7 | Ibanez TS808 - dry plus a diode-limited high-passed copy, then a movable low-pass. `oversample` is derived from the rate: **x8 at every rate below 48 kHz, x4 at 48 kHz and above**, and every rate under 24 kHz leaves the internal rate under the 192 kHz target because x8 is where the node stops. 48 kHz keeps x4 because x8 there costs +0.799 ms a block on the P4 and **+1.408 ms on the S3**, which projects the S3 to a real-time factor of about 1.00. The clip table fills Q15 ([#77](https://github.com/PyDevices/audiocomponents/issues/77)) - it held diode volts and peaked at 35 % of int16 - and the even-harmonic floor at the default drops from -97.6 to **-106.7 dBc**. **What the default surrenders:** Drive is never clean, but at Drive *minimum* it is 8.305 % THD at -14 dBFS, under the standout's 10-40 % band. **Mix rides the clipped voltage, not a crossfade to bypass**: Mix 0 is the wire, and one step above it the tone stack is in circuit on the dry note too, so stepping off zero is a tone change. **At Mix 1, Level MIDI 0 is silence, not a wire.** The 100 Hz-cleaner-than-1 kHz claim is a **sine at Body 720 Hz**: it reverses at the bottom of the Body travel, at Drive max, on a square wave, **on a sawtooth at all three rates** (86.2 % against 70.5 % at 48 kHz), and on shipped patches 2 and 4. T2 names h2 **and h4**, and patch 6 is h4 **-31.8 dB** beside its h2 -25.8. **T5's law - THD rises with Drive - is a claim at Symmetry centred**: off centre it turns over, peaking at Drive MIDI 64 and falling above it (Symmetry 0: 8.601 / 19.875 / 24.900 / 20.291 / 17.660 % over Drive 0 / 32 / 64 / 96 / 127, all three rates). **Silence in is silence out at every shipped patch** since the third fix round gave the class the output capacitor a pedal has - patch 6 stood +4461 LSB on the output for ever without it - and the pole costs 3.4 dB of alias floor at the default at 48 kHz and one block of input on a live macro move that shifts the offset. **Input ceiling -1 dBFS at the shipped patches, -6 dBFS anywhere on the surface**; patch 7 reaches the rail at 0 dBFS / 400 Hz (4 samples of 9600) and Drive max with Level max and Tone open at -3 dBFS (570 of 9600). T3's level law is **not monotone outside its stated -14 -> -6 pair**: THD rises -20 -> -14 dBFS, turns back up at -1 dBFS at 22.05 kHz, and rises with level at 100 Hz. **T7's alias floor was restated 2026-09-17 under vision §7.2 and is read on the wet branch**, with the dry copy muted - the dry note flatters every floor by 5.6-6.6 dB, and this class's dry voice is on the circuit mixer, which `mute_dry` searched past until the reach moved into the kit ([#68](https://github.com/PyDevices/audiocomponents/issues/68), [#81](https://github.com/PyDevices/audiocomponents/issues/81)). **Four** bars, 1010 Hz at **-6 dBFS** except the fourth: **-70 dB at the constructor default** (-77.9 / -78.7 / -75.6 at 48 / 44.1 / 22.05 kHz), **-50 dB at every shipped patch as shipped** (worst patch 3, -56.1 / -71.4 / -54.4), **-40 dB anywhere on the macro surface** (worst -47.6 / -61.0 / -46.6, at Drive max with Body at the bottom of its travel and Tone open) and **-40 dB at that corner at every input level up to full scale** (worst -42.0 / -52.2 / **-41.3**, all three **at 0 dBFS**, which is **1.3 dB of margin** and the thinnest this class has anywhere). A fifth, T7e, says what the oversampling is worth: **at least 20 dB** of wet floor against the same class at the base rate, at every surface position where Drive is above its floor and Body below its top (47 of 52 gradable cells at 48 and 44.1 kHz, all 52 at 22.05; worst carried cell +20.5 dB). The old single -60 dB bar is **kept at 44.1 kHz**, where the shipped x8 build meets it everywhere (worst surface cell -61.0 dB), and replaced at the other two: at 48 kHz x4 reads -47.6 and x8 would read -63.9 but projects the S3 to rt 1.00 - **a projection with no board behind it** - and at 22.05 kHz x8 is the node's maximum (`AUDIODSP_SHAPER_MAX_OVERSAMPLE`, [audiodsp#104](https://github.com/PyDevices/audiodsp/issues/104)). The **3700 Hz diagnostic does not hold**, and the -37.7 dB the pack published for it was a **mixed** reading: wet it is **-33.9 dB** at 48 kHz, -32.1 at the worst corner, and **5000 Hz is worse and was named nowhere** - -27.8 held at 48 kHz and **-24.1 at 22.05 kHz**. End-to-end gain is not the op-amp's 10-15 / 90-130 plateau, and the tone stack is not the TS wiper network |
| `Distortion` | audiodsp (`audioshaper`, `audiobiquad`, `audioroute`) | 10 | **2 samples** at Mix > 0 - the ×4 half-band, read as the click's integer onset, the same at 48 / 44.1 / 22.05 kHz, mono and stereo, on both characters; **0** at Mix 0. Every one of the eleven shipped patches reads it: the four scoop patches were unmeasurable while Asymmetry was a bias, and are not now. `oversample` default 4 is the latency-adding option and it is on. The sub-sample click is 15.2 / 14.3 / 8.7 samples: minimum-phase group delay, not latency | Palette **35 % P4 / 63 % S3** at patch 0 Mix 1 ×4 (1.849 / 3.323 ms, glue 0.0), re-derived 2026-09-17 for a graph three nodes smaller; the old **43 / 78** priced the graph the board ran. Board ROW **36.9 % P4 / 71.8 % S3**, measured 2026-09-18, inside the budget re-derived from that day's palette (**38 % / 73 %**), and **rt 1.16-1.18 on the S3 at all eleven patches** - the old graph read 49.2 % / 91.8 % with **rt 0.94 on the S3**, and the desktop marginal has since fallen 21.8 % (1.743 → 1.363 ms). Constructor `oversample=2` is **26 % / 47 %**, not a named lean patch | ProCo Rat (`filter`) with Boss DS-1 (`scoop`) - a hard clip to ground after a gain stage. Mix 0 is the wire; Distortion 0 is clean only in `filter`, and `scoop` starts with its 35 dB booster in circuit. **What the default surrenders:** F1's 11-18 dB bass-to-treble tilt is a *low Distortion* claim - at the shipped Distortion 64 the tilt is **+1.1 dB**. F5's 5 kHz clause is **false at 22.05 kHz** (default 1 k→5 k fall −13.7 dB against −11.7 ±1.5) because `_fo_lp` parks its second pole at 0.45·Fs. **A1 is a −20 dBFS number and its row carries the span**: −60 dB at 1010 Hz over **−22 to −16 dBFS**, graded at both ends and the middle (−62.4 / −63.3 / −60.6 at −22, −62.4 / −60.6 / −60.7 at −19, −68.4 / −67.0 / −65.1 at −16). Outside it the bar does not hold - **−55.7 dB at −12 dBFS and −46.5 dB at −6** - and it is a 1010 Hz claim: **7010 Hz reads −42.2 / −34.3 / −30.1** at −20 dBFS. "It is not aliasing" describes ×4: the ladder at −20 dBFS / 48 kHz is ×1 −36.1, ×2 −56.4, ×4 −61.7, ×8 −62.6. It holds up to Distortion 80 and is **redefined above that** (vision §7.2): at maximum Distortion it is −58.5 dB at 1010 Hz and −48.1 dB at 3700 Hz, which is the ×4 `Waveshaper`'s own decimation floor - the bare node reads −52.2 dB at 3700 Hz. On `scoop` with the booster up it is **−40.4 dB at patch 6**, −39.0 at the worst scoop cell. **Asymmetry is a second table, not a bias** (third fix round): `_CURVE_DS1_ASYM` is the DS-1's one-diode-against-two clipping section, both tables answer zero with zero, and silence in is silence out at every shipped patch - the bias model sat at up to **−6.8 dBFS of DC** and started a −20 dBFS note on −0.28 of full scale. It costs 1.8-2.3 dB of level on the four scoop patches. **Volume and Mix stop above a knee and `wet_ceiling()` says where**: 1.0 at the shipped Ceiling MIDI 42 (the whole travel works), 0.6317 at Ceiling MIDI 108, where Volume MIDI 84 to 127 is one number. **The Filter macro works over its whole travel on `scoop` now** - it was one section from MIDI 8 up and ran backwards below it. Scoop traits are not the shipped character |
| `Fuzz` | audiodsp (`audioshaper`, `audiobiquad`, `audioroute`) | 7 | Mix 1 at oversample 8 reports **4** (3.9 samples / 0.083 ms at 48 kHz); oversample 4 reports **3** (0.069 ms), oversample 2 and patch 8 report **2** (0.046 ms), oversample 1 and Mix 0 report **0**. **`cascade` ships at x2, so it reports 2 where `germanium` reports 4**; `LATENCY_SAMPLES` is the germanium constant and the instance property is the one to read | Palette **42 % P4 / 75 % S3** at patch 0 germanium x8, re-derived 2026-09-18 at the rows both boards took that morning (3 x Biquad 0.324 / 0.612 + Waveshaper x8 1.933 / 3.368 + glue 0.0 = 2.257 / 3.980 ms). Patch 8 **`Fuzz - lean`** shapes at x2 through a second shaper the tilt stage plays instead - **17 % / 31 %** (0.882 / 1.629 ms) - and that patch, not the constructor, is the S3's germanium position. Board ROW, second pass 2026-09-18 on the 256-frame graph, **44.4 % P4 / 76.8 % S3** at patch 0, **18.5 % / 32.8 %** at patch 8 and **44.6 % / 77.7 %** at its costliest shipped patch - still **over the palette sum by 2.1 / 2.2 points**, which under Brad's G6 ruling of that day (the cost gate is a real-time ceiling, 80 % of a block, and the palette sum is a planning estimate) is a note and not a park: this class is **adopted** (audiocomponents#74). **Alone on an ESP32-S3 this uses 77 % of a block at its default germanium patch, 78 % at its costliest; use patch 8 `Fuzz - lean` (33 %) to stack.** **That palette miss is not located**: the census confirms the node count, the shaper's own settings price the same as the palette row (0.0691 against 0.0718 ms/block on desktop MicroPython, order-balanced), germanium builds no Mixer and no Splitter and hands back a 256-frame block already - and the miss is **0.122 ms on the P4 against 0.116 on the S3**, the same absolute number on two chips that differ by 1.8x, which is not the shape of CPU work. rt 1.81 / 1.05 on germanium. **`cascade` ships at `oversample=2` since the fifth fix round**: at x8 the board read **89.7 % / 161.0 %, rt 1.00 on the P4 and 0.56 on the S3** - it does not run on a T-Embed S3 - while `create()` defaulted to 8 for both characters and only a docstring said otherwise. At x2 it is **40.7 % / 74.3 %, rt 1.97 / 1.09** against a palette sum of 2 x Splitter-2 + 6 x Biquad + 2 x Waveshaper x2 + Mixer = 2.228 / 4.169 ms (**42 % / 78 %**): inside on both boards. x4 is 3.250 / 5.971 ms, **61 % / 112 %**, so it does not run on an S3 either. **What x2 gives up is 2.9 dB at 1010 Hz and 5.3 at 3700 of alias floor at the default Fuzz, and 5.6 / 5.6 at maximum Fuzz** - cascade's floor spans only 2.5 / 5.6 dB from x2 to x8 because the second clipper folds what the first already put above the output Nyquist (x8 buys it 12.3 / 12.7 dB over x1, against germanium's 20.9 / 18.7). **`cascade` is outside A4's span at every factor** - A4 is a germanium row and at x8 cascade reads -29.8 / -26.0 against bars of 35 / 28 dB. `oversample=` still takes 1, 2, 4 or 8 | Fuzz Face (`germanium`) and Ram's Head 1973 Big Muff (`cascade`). Mix 0 is the wire; on `germanium` Mix is the shaper's own blend. **What the default surrenders:** Tone is inert on germanium. G2's 0.5 dB-per-step THD staircase is not met (the last steps are +0.17 / +0.04 / +0.008 dB). Cascade C2's 25 dB THD-vs-Sustain bar is not met at -20 dBFS - both ends of Sustain are already hard-clipped. Gating is the Bias macro's starved end, not a moving bias. **G1's peak clause is bounded to Tilt 0**: at Tilt +6 dB the 9.02 dB peak split reads 0.000 dB while h2 is still -19.58 dBc, and G1 holds at **patch 0** and misses at patches **1, 4, 5, 6 and 7** - every patch at Fuzz 48 dB or above. **A4's alias floor was redefined 2026-09-17 under vision §7.2**: the old 60 dB bar at 3700 Hz fails at every position of the macro, so the claim is now >= 50 dB at 1010 Hz and >= 35 dB at 3700 Hz at the default (measured -55.5 / -38.4), x8 at least 20 dB better than x1, worst case at maximum Fuzz ≥ 35 / ≥ 25 dB. **The worst cell is the joint one**, not the one-macro-at-a-time sweep the pack published: Fuzz 127 with Tilt 127 reads **−35.407 dB at 44.1 kHz** against a published −38.154, so the margin is **0.4 dB**. **The tail is 24 576 samples** since the third fix round — 16 384 was a 1 kHz number and a 40 Hz burst rings 18 750 frames at patch 5. **The output pole is charged before the first block**, so patch 2's starved bias emits 11 LSB into digital silence where it banged **21 971** (−3.5 dBFS); what is left is a stated residual of 16 LSB, bounded and tested. **Nothing reaches the rail between 100 Hz and 3700 Hz** (worst 30 185) — below 100 Hz it does: at Fuzz maximum a 30 Hz sine pins 10 samples of 6 400 at 0 dBFS, and the worst shipped patch below 100 Hz has a 0.16 dB margin. **G1 is level-free over −46 … −20 dBFS**, walked at both ends and the middle. **`cascade` has its output coupling capacitor** since the fourth fix round ([#89](https://github.com/PyDevices/audiocomponents/issues/89), ruling (n)). Without it the low arm of the tone stack is a LOW_PASS, which passes DC, and Bias off centre held **-16 383 to +16 382 LSB (-6.0 dBFS) on the output for ever** at eight of the nine stops of a front-panel macro. Walked over 108 cells - 3 rates x 2 characters x 9 Bias stops, built at the value and moved to it live - the settled mean is now at most **7.1 LSB** and the peak at most **13**, both on germanium; cascade's worst is 6 LSB of each, inside the stated 16 LSB residual. **Two rows moved with it, and C1 did not.** **C3's Bias clause is restated**: Bias off centre gates the LEVEL (three probe tones average -15.5 dBFS at centre, -26.8 at +-0.25, -43.9 at +-0.5, -56.2 at +-0.85, -67.8 at +-1) and the **scoop survives the whole travel** (+3.93 ... +7.63 dB); the old "three probe tones come out at one level, scoop 0.002 dB" was the offset, not the tone stack, and patch 2's miss reads 2.561 dB against the 3 dB bar where the offset made it 1.1. **C4's span narrows to Fuzz 18 ... 32 dB and is disconfirmed above it, which includes the cascade constructor's own 36 dB and eight of the nine shipped patches** - above the span the clipper has filled the notch in and the Tone 0.75 curve is a monotone slope across the whole 150-2000 Hz grid; the old claim to 36 dB rested on a **0.041 dB** dip between two grid points an octave apart. C1 is unmoved (h2 -79.059 -> -79.379, peak growth 0.012 -> 0.013 dB) |
| `Saturation` | audiodsp (`audioshaper`, `audiobiquad`, `audioroute`, `audioecho`) | 8 | Mix 1 at oversample 8 reports **4** (3.9 samples / 0.083 ms at 48 kHz); patch 8 and oversample 4 report **3** (0.069 ms); oversample 2 reports **2** (0.046 ms); oversample 1 and **Mix 0** report **0**. `console` adds **2 samples** | Palette **31 % P4 / 58 % S3** at patch 0 (tube, x4), re-derived 2026-09-18 from the rows both boards took that morning: Splitter-2 0.207/0.368 + Waveshaper x4 1.069/1.918 + **3**xBiquad 0.324/0.612 + Mixer 0.050/0.175 + glue 0.0 = 1.650 / 3.073 ms. **Three sections and not four** - `_after` **is** `_couple`, so the board's attribute census counted one node under two names. Patch 8 **`Saturation - lean`** shapes one factor down - **21 % / 41 %** (1.139 / 2.172 ms). Board ROW of the 128-frame graph was **34.3 % / 62.2 %** at patch 0 and **24.7 % / 46.4 %** at patch 8 - over by 3.4 / 4.6 and 3.3 / 5.7 points. The 256-frame graph it ships now, measured on both boards in the second pass of 2026-09-18, reads **29.4 % / 55.4 %** at patch 0, **20.8 % / 39.6 %** at patch 8 and **29.9 % / 56.4 %** at its costliest shipped patch: inside the palette sum, and inside Brad's G6 real-time ceiling of 80 % of a block at all nine patches, so this class is **adopted** (audiocomponents#70). **Alone on an ESP32-S3 this uses 55 % of a block at its default patch, 56 % at its costliest; use patch 8 `Saturation - lean` (40 %) to stack.** **The miss the 128-frame graph had is not the node count:** every node the class drops leaves the sum by exactly its palette row, so trimming does not move it. It is the **per-block glue** every budget here prices at 0.0 - the class handed back a **128-frame** block (`Mixer._render_size` is `buffer_size // 2 // 4 * 4` bytes), so everything behind it was pulled twice per 256-frame block, and one Python-level pull is worth **0.178 ms P4 / 0.109 ms S3** by the board's own rows (`Splitter+3 - Splitter+tap` against `Mixer@3active - Mixer@2active`) - 3.3 and 2.0 points, the whole P4 miss. It hands back the palette's own 256-frame block now and **no byte moved** (`ffb5e07e33e2732d` / `58444f96ff950621` at either length, three interpreters), and the second board pass measured that graph: the miss is gone. rt 1.35-1.73 on the S3, 2.41-3.10 on the P4. `tape` adds a fourth biquad (33 % / 61 %) and `console` replaces one with two bare `FeedbackDelay` sections, which have no Phase 4 row at all; neither is this bar. `hysteresis` has no palette row | 12AX7 (`tube`), Langevin tape (`tape`), transformer iron (`console`). **Mix 0 is the wire, and it is the borrowed source itself** - no mixer in the path, because a voice at level 1.0 scales by 32768/32767 and lifts every sample at or above 32736 by an LSB (audiodsp#95). **What the default surrenders:** **Drive stops at +15 dB, not +24** - that is where the alias floor still holds 60 dB down at 1010 and 3700 Hz on the shipped x8 (-72.9 / -64.2 dB; +18 dB reads -63.0 / -50.9). It costs the top of the range, 21.7 % THD at the ceiling against 34.9 % at +24, and the plate has long since pinned by then. Speed is inert on tube and the Hysteresis macro is off; **TP3 is not a graded trait** (dossier §8 Q1). Drive compensation keeps small-signal level from jumping with the knob, which also means a rendered peak never sits on the plate ceiling - so **TU2 is measured without it**. Switching into or out of patch 8 re-routes the pull chain and steps at the block boundary like the patch change it is (3357 LSB against 1281 for an ordinary one): a setup choice, not a knob to ride. **Output delivers what it says since the third fix round**: the excess the node gave up at `NODE_CEILING` used to go onto the wet mixer voice as `level > 1.0`, which clamps, so Output +12 delivered **+7.866 dB**; a 10 Hz `HIGH_SHELF` carries it now and +3/+6/+9/+12 all land within **0.25 dB**, rendered, on both builds. **The tube table no longer inverts** — it did, so Mix was a notch rather than a blend (−33.580 dBFS at Mix 0.75 against −23.125 at Mix 1) — and every unit this models has an even number of gain stages. **The plate coupling pole is charged before the first block**, so patches 4 and 6 emit **1 LSB** into digital silence where they banged 8 489 and 7 044; the stated residual is 2 LSB. **`latency_samples` is the measured integer onset**, per character and factor — tube 1 / tape 2 / console 4 at ×4 — and all 18 build × rate cells read within the kit's 1-sample bar; the sub-sample group delay (3.912 / 4.753 / 6.418) is the graph's property and not what this declares. **A4 is a −6 to 0 dBFS row and TU2 is a 0 dBFS row**, and both say so; TU2 also holds **Tilt** fixed (Tilt −6 reads plate 0.3380, 8.4× the bar). TU1's guard is graded against **17 readable positions of 51**, not the 49 the row published. **Insertion loss at the default is 8.1 / 13.4 / 33.5 dB** (tube / tape / console) — Mix 1 is not unity — and the tail declaration is **3.4×** the worst measured, not 4.8×: `console` at 40 Hz rings 19 317 frames |
| `Bitcrusher` | audiodsp (`audioshaper`, `audiobiquad`, `audioroute`; every node is audiodsp's own since 2026-09-17 - `audiospeed` is gone) | 6 | **The hold's displacement.** `latency_samples` reports `ceil(num/den) - 1` off `audioshaper.SampleHold`'s own reduced pair: **1** sample at the default at 48 and 44.1 kHz, **0** at 22.05 kHz where Rate clamps to the running rate, and **0** at Mix 0. `SampleHold.latency` is 0 at every ratio. Band Limit is an IIR and is not in the reported path. `tail_samples` is 0 with Band Limit off, **640** with it on, measured at the knob's lowest corner | Palette **8 % P4 / 15 % S3 priced** at patch 0 Mix 1 x1 (Splitter 2 taps 0.165 / 0.395 + Waveshaper x1 0.223 / 0.410 + Mixer 0.036 / 0.018 = 0.424 / 0.823 ms) plus one `audioshaper.SampleHold`, **priced on the boards 2026-09-18 at 0.050 / 0.089 ms**, against the 0.039 / 0.230 the `SpeedChanger` pair it replaced cost. Board ROW **13.3 % P4 / 25.5 % S3** at patch 0, rt 4.74 / 2.54, against a budget re-derived from that day's palette over the nodes the class actually builds - three Mixer stages, not one, and the shaper at its own 8193-point curve (0.241 / 0.464, only 0.018 / 0.033 more than the 1024-point row) - of **13 % / 28 %**. Desktop whole-class marginal **0.025 ms/block** (rt 17.83). Band Limit is not in the sum - the knob re-sources the hold, so the filtered path is not pulled; turning it on adds **0.200 / 0.338 ms** (two sections, not four), 4 and 6 points. Board ROW **unmeasured**. No lean patch | SP-1200's two numbers as knobs: 12-bit linear hold. Mix 0 is the wire. **What the default surrenders** (12 bits at 26.04 kHz, dither off, band limit off): the **hold**, not the quantizer, is what you hear - on a sine through patch 0 the residual is a thousand times the quantizer's. **The quantizer is soft, and at 12 bits soft by half**: the `Waveshaper` interpolates its table, so every riser is 8 input codes wide and the error power is `(D - 8)/D` of a hard converter's - 0.50 at 12 bits, 0.75 at 11, 0.97 at 8 - and the same riser rounds up 4 codes early, so the mean error is **+0.25 LSB at 12 bits** (a rounding asymmetry: f(0) is 0 and silence in is silence out). The hold's **images stand at their own level** and that is the Rate knob working: a 1 kHz image under a 7 kHz tone held at 8 kHz reads -0.22 dB against the input, and Band Limit puts **27.5 dB** under it; above the hold's own Nyquist the image spreads and reads 4.6 to 6.4 dB down, which is **disconfirmed** against the row's +-3 dB. The run alphabet is **99.98 %** 1s and 2s at 12 bits and falls below 99 % under 8 bits (99.41 / 97.59 / 90.52 / 66.76 at 8 / 6 / 4 / 2), so patches 2 and 6 are outside that clause. **An event can be dropped, and not only a single-sample one** — 45 % of one-sample offsets vanish at 48 kHz, 40 % at 44.1, 0 % at 22.05, and at shipped patch 6 **60 of 120 FOUR-sample offsets vanish at 48 kHz** (55 at 44.1). **The dither is gated on the input** since the third fix round: patch 5 put ±16 counts out into digital silence to the last frame, and silence in is silence out at every patch now, at the cost of a **8 192-sample tail** wherever the dither is on. **`latency_samples` carries the band limit's own delay** — patch 3 measured 2 to 8 samples over 120 offsets against a declared 6 and declares **8** now. **T1, T2 and T6 hold where the probe spans at least 16 steps of the depth in force** (−48 dBFS at 12 bits, −24 at 8) **and sweeps the codes**: a sine's mean wanders with the phase at every level (+0.28648 LSB at −55 dBFS against a +0.25 law), which is the precondition the rebuild dropped. T4's one excluded stop is 48 kHz / Rate MIDI 80, **1.495 dB** out, where the 5th image lands 1.25 Hz from the tone. **At 22.05 kHz the default does not reduce the rate at all** and the top four of the Rate knob's seventeen stops are the same identity; `hold_rate_hz` says what you got. **Dither is two coprime loops, not noise** - 1021 and 1024 frames, so it repeats every 21.8 s rather than 42.7 ms, with autocorrelation 0.47 / 0.43 at each half's own lag. A mono source is the same graph, not a downmix |
| `Exciter` | audiodsp (`audioshaper`, `audiobiquad`, `audioroute`, `audiodynamics`) | 5 | **0 samples** at every macro setting; the dry tap is a copy. `oversample` delays the wet branch only - x4 is 3.3 samples / 0.069 ms at 48 kHz, x8 is 3.9 / 0.083 ms - and it is not on the macro surface. `tail_samples` is **4096** since the third fix round — the 30 Hz output coupling pole rings, worst measured **3 085 frames** across three rates and eight builds; it was 512. There is no delay line | Palette **29 % P4 / 54 % S3** on `classic` at patch 0, re-derived 2026-09-18 at the rows both boards took that morning (Splitter-2 0.207 / 0.368 + **2 x** Biquad 0.216 / 0.408 + Waveshaper x4 1.069 / 1.918 + Mixer 0.050 / 0.175 = 1.542 / 2.869 ms). Two Biquads and not three: `_chain` is an **alias** - `_hp` on `classic`, `_dyn` on `transient` - never a node of its own. `transient` adds `Dynamics@transient` 0.495 / 0.985: 2.037 / 3.854 ms, **39 % / 73 %** (`transient_fast_release_ms` is a config field, not an option that costs). Board ROW of the 128-frame graph was **32.3 % P4 / 57.8 % S3** on `classic` and **42.5 % / 81.6 %** on `transient`. The 256-frame graph it ships now, measured on both boards in the second pass of 2026-09-18, reads **28.9 % / 54.3 %** on `classic` and **39.3 % / 77.0 %** on `transient`, worst shipped patch **39.4 % / 77.5 %** - still over the palette sum by 1.1 / 4.7 points, which under Brad's G6 ruling of that day (the cost gate is a real-time ceiling, 80 % of a block, and the palette sum is a planning estimate) is a note and not a park: this class is **adopted** (audiocomponents#72). **Alone on an ESP32-S3 this uses 54 % of a block on `classic` and 77 % on `transient`, 78 % at its costliest patch; there is no lean patch, so run it alone or with something cheap.** **The `Dynamics` row is NOT priced at the wrong settings**, which is what the board suspected: this class's own +6 / -12 dB gains measure **1.034x and 1.062x** the palette's 0 dB build on desktop MicroPython, order-balanced - a few per cent, not the 27 % the S3 is missing. What the S3's five extra points are is the `Dynamics` costing the class 1.234 ms against a 0.985 row (0.537 against 0.495 on the P4), and the suspect - **unproven** - is that the class handed back a **128-frame** block while a `Dynamics` renders in 256-frame blocks by construction (`audiodsp_dynamics.h:56`). It hands back the palette's own 256-frame block now and **no byte moved**, and the second board pass measured that graph: the 128-frame block was worth 3.2 / 4.6 points of it and the rest is still unexplained. rt 2.06 / **1.07** on `transient`, the thinnest margin of the seven, and measured with the probe source in the graph and nothing else - an app's source is not free. The old **33 % / 59 %** charged every build for the Dynamics wire; `classic` no longer pays it. **No lean position**: `oversample=2` was documented as one and is red at **12 of 48** T7 readings, worst **-45.1 dB**, and at the old drive on shipped patch 2 as well. **x8** would hold T7 at the old drive and does not fit the S3 (3.804 ms `classic`, rt 1.04; 4.557 `transient`, rt 0.91). Board ROW **unmeasured** | Aphex Aural Exciter - dry plus a one-sided high-passed 1N914 branch. Mix 0 is the wire. **What the default surrenders** (Tune 4 kHz, Harmonics 0.25, Mix 0.3, `classic`, Output 0 dB): **no makeup gain** - Output is -24…0 dB and the dry path is already unity. **At 22.05 kHz the corner tops out at 3150 Hz** (rate/7) whatever Tune reads back. **At 22.05 kHz T7 is disconfirmed**: "the whole 22.05 kHz column is green (worst −64.4 dB)" was read at the Tune grid's own stops, and walked at every eighth stop with Harmonics at maximum **6 of 12 readable stops are over the −60 dB bar** — worst **−41.661 at Tune MIDI 56** (1656 Hz). The row is claimed at 48 and 44.1 kHz. **T7 is also claimed only up to the stated input ceiling**: at 48 kHz with Tune and Harmonics at maximum it reads −63.461 at −6 dBFS and −63.475 at −3, and −59.856 at −1 and −59.058 at 0. **The class states an input ceiling of −3 dBFS** (`INPUT_CEILING_DBFS`) because it only attenuates and had no headroom control at all: the first railed sample anywhere is at −2 dBFS. **T1 is a -40 dBFS row and says so**: it holds Harmonics 0 and -40 dBFS fixed, where the clipper is within 0.05 dB of linear, and it is inside its 10.8-13.8 dB bar at 27 of 27 cells at -40, -30 and -20 dBFS at all three rates. Up the level axis it leaves the bar at **32 of 72 readings in 9 of 9 rows**, every one at -12 dBFS or hotter, worst **-9.635 dB** (48 kHz, Harmonics 0.25, 0 dBFS). **The harmonic reader has its control** ([#72](https://github.com/PyDevices/audiocomponents/issues/72) item 6): an identity curve - a build that makes no h2 at all - reads no h2 over T2's own 240-cell grid, worst **-64.822 dB** against the shipped class's **-15.430** at the same cells, so the four macro-surface fault walks stand at **250 / 276 / 273 / 273 RED and 0 HEALTHY**. **There is a coupling capacitor behind the diode now** — the rectified offset used to walk out at −122 to −1601 LSB on the shipped patches and −4310 LSB at Harmonics 1.0 / Mix max / −1 dBFS, where a silence test never saw it; the same cells read −1.8 and −0.1 LSB. **What the x4 is worth against x1** is a clause now (`ALIAS_OVERSAMPLE_COST_DB`, at least 15 dB wherever Tune is at or above 1900 Hz, measured +19.1 to +46.2 dB there and −2.2 to +7.1 below it), because under the absolute bar alone `BaseRate` was healthy at 21 of 276 positions — all of them the bottom of the Tune macro. And a tone whose harmonics reach past the output Nyquist folds where no oversampling factor reaches - 1010 Hz at full drive puts its 11th harmonic at 11110 Hz against a Nyquist of 11025 and reads **-48.7 dB at 10940.8 Hz**, a 3010 Hz tone puts its 4th there (-51.9) and a 8662.5 Hz tone its second (-54.9), where at 48 and 44.1 kHz the same sweep is green to rate/8. **On material with step edges the wet exceeds the dry** - at Mix maximum a 1 kHz square puts the wet at **164.7 %** of the dry, because the high-pass differentiates the edge and the reverse side of the 1N914 curve is a wire. **Harmonics is 0…+14 dB of drive across the diode, not 0…+24** - the top ten decibels bought **1.76 dB** of h2 at -6 dBFS and cost **6.7 dB** of alias, so the knob's 0…1 span is unchanged and what it commands is not. **The class adds content BELOW the corner**: the high-pass is upstream of the diode, so two tones both above it (5000 + 5500 Hz at -6 dBFS) put their **500 Hz difference tone at -17.7 dB** on the wet branch and **-31.7 dB** on the mixed output at the shipped Mix 0.3, and on noise the wet carries 12.3 dB less below the corner than the dry, not none - a low rumble that follows the music's intervals rather than its pitches, louder with Harmonics and with Mix. **T7 is a `classic` claim**: on `transient` the Dynamics stage's gain ripple folds at base rate, ahead of the shaper, 12 of 36 grid readings above the bar, worst **-52.3 dB**, the same at x2, x4 and x8 where `classic` reads -90.6. **On `transient` T4 is read after the onset**: 59.6-61.9 % of the dry on a steady sine at Mix maximum once the render's own start has passed, 124-135 % over a window that still contains it, and the boost is spent within ~25 ms. **T6 is a `transient` row and is disconfirmed** (17.6 dB of emphasis at -30 dBFS against 6.7 at -6, an 11.0 dB spread against a 3 dB bar); **T5's shape holds on `transient`** (12.75 dB at 5 kHz / -18 dBFS) and is false at the shipped `classic` default, which is the control: 0.00 dB |
| `CabinetSim` | audiodsp (`audiobiquad`) | 8 | **0 samples** at the synthetic default. Constructor `impulse` is off by default; a user IR costs the convolver partition **256 samples / 5.333 ms at 48 kHz**, and it is the only latency-adding option. Room-scale IRs do not fit the boards (48000 taps: 18.0 / 31.1 ms). `tail_samples` is **6144**, measured burst-to-exact-zero over the whole shipped surface: 1850 samples at the default, 4421 at patch 1, **5565** at the worst corner (combo, Low Cut 55, Body +6, a 0 dBFS burst at the bell's own 115 Hz). The longest ring is the combo's bell, not the lowest Low Cut | Palette **15 % P4 / 26 % S3** at patch 0, eight live sections, Mix 1 (0.800 / 1.352 ms). **Board ROW 17.2 % / 31.1 %, re-measured 2026-09-18** at audiodsp `e3b95e7` (17.1 % / 27.7 % on 2026-09-17 at the older pin), against the same eight-section arithmetic re-priced on those boards, **17 % / 31 %**. rt 4.07 / 2.27. The gap is the palette's, not the graph's: its `audiobiquad.Biquad` row prices ONE node whose upstream is the harness, and the eighth node of a serial chain costs more than the first (0.1138 / 0.1848 ms per section here). There is no Splitter, no Mixer, no second source and no per-block Python in this graph. No lean patch, no extra source-pull | Vintage 30 on-baffle in a sealed close-miked box (`4x12 stack`); G12M-class open back (`1x12 combo`). Mix 0 is the wire. Default is a designed cascade, not a third-party impulse. **What the class gives up:** **this cabinet clips above −13 dBFS, and at the constructor default above −6 dBFS**, with stated no-railed-sample ceilings of **−14 and −6** — the −11 and −5 published before were read through a `macro_surface()` that moves **one macro at a time** and never swept Low Cut 55 with Body +6, which is shipped patch 6's own settings; read in combination the analytic peak there is **+13.148 dB** against a published +10.91. Every one of the eight sections hands the next an int16 and audiodsp's converter saturates at the rail, and the designed response is a boost (+10.9 dB at the corner the old sweep found - combo, Body +6, 118 Hz - and +5.3 dB at the default). There is no output trim. Shipped patch 6 is the worst cell (150 Hz: 8.28 % THD at -9 dBFS, 27.69 % at -3); shipped patch 1 at 115 Hz reads 2.01 % at -9 and 31.11 % at 0; the default at 2112 Hz clips above -5. Below the ceiling it is linear and no alias row is owed; above it one is - the non-harmonic floor at 3700 Hz goes from -90 dB at -20 dBFS to **-42.0 dB at 0 dBFS** (patch 0, 48 kHz) and **-25.7 dB** at 22.05 kHz. A 1 kHz guard cannot see any of it, because 1 kHz is the one frequency the class does not boost. **It is not the same cabinet at 22.05 kHz**: 48 and 44.1 kHz agree within 0.3 dB, but at 22.05 kHz 5 kHz sits **+4.34 dB** higher re 1 kHz and 7 kHz 4.37 dB lower, the worst cell over the seven patches is **4.95 dB** (patch 3 at 8 kHz), and T5a's upper -3 dB point moves 4551 -> 5050 Hz - the bilinear warping of the two top shelves, one design reinterpreted at each rate. **The macro surface is the 128 MIDI positions** - `set_macro` snaps a float, because only those are proved to hand a board and a desktop the same filter. **Every Tier 2 trait is a Mix 1 claim** - Mix blends every section at once, so T1 holds down to Mix MIDI 112 (14.6 dB at MIDI 96, under its 15 dB bar) and T4 down to Mix MIDI 48 (-8.6 dB at MIDI 32, over its -12); between those and Mix 0 neither is claimed. **T2 is not claimed above Top 5.6 kHz at every Air, nor above 6.3 kHz at any** - the shelves separate as Top rises (3.8 dB at 5.6 kHz, 10.3 at 6.3, 14.0 at 6.6, 17.4 at the 7 kHz stop) and T1 goes with it at 14.6 dB at the stop; **T2 is not applicable at 22.05 kHz**. **T3 is not claimed below the default Bite**: at Bite 0 the two break-up sections are switched off entirely, and shipped patch 2 ships Bite +1 and misses T3's 3 dB bar. **T5a's 115-230 Hz plateau is disconfirmed** - the three high-pass poles put 115 Hz **4.02 dB** under the low-frequency maximum - and its **60 Hz clause holds while its 200 Hz-1 kHz clause holds at Body 0 and nowhere else** (Body −6 reads −1.31, a rise; Body +6 reads +7.48, over the 6 dB the trait allows); the lower −3 dB point lands at **121 Hz**. **T4 is a 40.00 Hz row and the pack read 41.0156 Hz** — the tone snapped to the render's bin grid, worth **1.28 dB** on a six-pole rolloff: at an exact 40.00 Hz the default reads **−42.443 / −42.441 / −42.483 dB** against a published −41.16 / −41.96 / −42.01, and patch 6 **−19.009** against −17.94. **`tail_samples` carries a user impulse now** — it returned the eight-section constant whatever `impulse=` held, and an 8 192-tap IR measures 8 447 samples of tail while a 48 000-tap room measures 48 255 against a declared 6 144. **Three Tier 2 readings go red above the ceiling** (T3 at 0 dBFS, T5a's 200 Hz clause at +1.21, T5b's level clause at −6 dBFS with Low Cut 55 and Body +6) and each row takes its level span. **T5b is a claim about the character**, read at identical macros, not about the patch pair. Every hertz and decibel is quantised onto a coarse grid, and the macro position onto the MIDI integers, so an ESP32's single-precision Python and a desktop's double produce the same float32 (audiocomponents#75) |

The three saturation characters are different curves, not one curve with
presets. `tube` is a 12AX7 common-cathode stage; `tape` is odd Langevin
saturation plus a playback-loss curve that slides with Speed; `console` is
transformer iron saturating from the bottom up. Mix 0 is the wire on all
three. Drive compensation keeps small-signal level from jumping with the
knob.

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
- **Sample-rate reduction as a stock Distortion mode** - CircuitPython's
  LOFI masks low bits and nothing else. The rebuilt `Bitcrusher` holds both
  word length and hold rate on `audioshaper`, and it is what the package
  serves: it came home to `bitcrusher.py` on 2026-09-18.
- LFO-driven parameters update at the block rate (~187 Hz at 48 kHz),
  plenty for sweep rates but not audio-rate modulation. `RingMod` is the
  exception and does not use an LFO at all - see below.

## A note on how low a filter can go

Anywhere in the band on `audiobiquad`, which is what the rebuilt filters and
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
+6.01 dB or better on a +6 dB request, read on `ParametricEQ`. The rebuilt
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
class. See `docs/audio-components.md` for the complete rack rule.

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
longer does, because the engine is right. See [audiodsp's `docs/upstream-diff.md`](https://github.com/PyDevices/audiodsp/blob/main/docs/upstream-diff.md) for
the measurements and the one-line coefficient fix.

## Testing

`tests/test_cpython_effects_library.py` holds every class in
`audioeffects.ALL` to the contract - exports and metadata, the factory,
building and rendering, chaining, the patch surface - under CPython. What
each class *sounds* like is measured beside it, one module per family:
`test_cpython_effects_dynamics_eq.py`, `..._modulation.py`, `..._time.py`,
`..._pitch.py` and `..._racks.py` - plus one module per rebuilt class, which
is what a family module's phase leaves behind - with
`test_cpython_convolve_node.py` for the audioconvolve node underneath the
convolvers. `tests/parity/effects_library_smoke.py` is the coarse half of
all that in portable Python, so MicroPython and patched CircuitPython can
walk the same catalogue - every class through `create()`, and every patch it
declares through `program_change()`. micropython-vst3's `tools/test-effects-lib.py`
additionally runs them inside a real VST3 host, feeding a quiet-then-loud sine and asserting
per-class behaviour: compressors and limiters squeeze the loud half,
gates and expanders mute the quiet one, everything else passes signal.
