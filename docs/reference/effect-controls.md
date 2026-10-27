# Effect controls

Every effect's knobs, what each one spans, and the patches it ships with.
The tables are rendered from the classes themselves, so they are always
the code's own answer. A knob turns on the 0 to 127 MIDI scale; "log" means
equal turns cover equal ratios, so the fine grain sits at the low end.
What each knob does is in the effect's own docstring.

## Air Space

`AirSpace`

| Knob | Spans |
|---|---|
| Time | 20 ms to 500 ms, log |
| Feedback | 0 to 0.85 |
| Glide | 1000 ms to 10000 ms, log |
| Drive | 0 to 1 |
| Loop Top | 1 kHz to 16 kHz, log |
| Loop Bass | 20 Hz to 1 kHz, log |
| Top Cut | 1 kHz to 16 kHz, log |
| Low Cut | 20 Hz to 500 Hz, log |
| Decay | 0.3 s to 10 s, log |
| Damping | 500 Hz to 16 kHz, log |
| Mix | 0 to 2 |

Patches: Chamber Send; Short Send; Long Send; Dark Loop; Bright Chamber; Driven Tape; Plain Chamber.

## Analog Delay

`AnalogDelay`

| Knob | Spans |
|---|---|
| Time | 20 ms to 600 ms, log |
| Feedback | 0 to 0.99 |
| Mix | 0 to 2 |
| Modulation | 0 ms to 5 ms |
| Mod Rate | 0.05 Hz to 8 Hz, log |
| Spread | 0 to 1 |
| Sync | off or on |
| Division | 0 to 15 |

Patches: Single Line Repeats; Short Bright Repeats; Long Dark Repeats; Modulated Repeats; Wet Vibrato; High Feedback Wash; Dotted Eighth, Synced.

## Auto Pan

`AutoPan`

| Knob | Spans |
|---|---|
| Rate | 2 Hz to 20 Hz, log |
| Depth | 0 to 1 |
| Shape | 0 to 1 |
| Law | +3.0103 dB to +6.0206 dB |
| Centre | -1 to 1 |
| Phase | -180 degrees to 180 degrees |
| Sync | off or on |

Patches: Slow Sweep; Quarter Note; Wide Triangle; Narrow Drift; Mono-Safe Sweep; Offset Left; Fast Flutter; Quarter Offset.

## Band Pass

`BandPass`

| Knob | Spans |
|---|---|
| Frequency | 20 Hz to 16 kHz, log |
| Width | 0.5 to 32, log |
| Slope | off or on |
| Mix | 0 to 1 |

Patches: Wide Mid; Telephone; Snare Crack; Presence Window; Narrow Probe; Sub Window.

## Bitcrusher

`Bitcrusher`

| Knob | Spans |
|---|---|
| Bits | 2 to 12 |
| Rate | 1 kHz to 48 kHz, log |
| Dither | 0 to 2 |
| Band Limit | off or on |
| Mix | 0 to 1 |
| Output | -24 dB to 0 dB |

Patches: Twelve Bit, Twenty-Six; Eight Bit Voice; Six Bit Drum; Telephone Grid; Grit Under The Note; Dithered Twelve; Broken Converter.

## Cabinet Sim

`CabinetSim`

| Knob | Spans |
|---|---|
| Character | off or on |
| Low Cut | 55 Hz to 140 Hz, log |
| Body | -6 dB to +6 dB |
| Break-up | 1.8 kHz to 3.6 kHz, log |
| Bite | 0 dB to +8 dB |
| Top | 4.5 kHz to 7 kHz, log |
| Air | -30 dB to -12 dB |
| Mix | 0 to 1 |

Patches: Sealed Four By Twelve; Open-Backed Twelve; Off-Axis Close Mic; Cone Centre; Dark Practice Box; Bright Small Box; Bass-Heavy Room.

## Chorus

`Chorus`

| Knob | Spans |
|---|---|
| Rate | 0.3 Hz to 10 Hz, log |
| Depth | 0 to 0.35 |
| Mix | 0 to 1 |
| Delay | 3 ms to 20 ms |
| Tone | 1 kHz to 12 kHz, log |

Patches: Near-equal blend; Long line, deep; Short line, shallow; Slow swirl; Fast warble; Dark wet; Equal sum.

## Comb Filter

`CombFilter`

| Knob | Spans |
|---|---|
| Frequency | 20 Hz to 4 kHz, log |
| Feedback | 0 to 0.95 |
| Mix | 0 to 2 |
| Tone | 500 Hz to 24 kHz, log |
| Trim | -18 dB to +18 dB |
| Glide | 0 to 1 |

Patches: Metallic; Ringing Pitch; Soft Ripple; Dark Resonator; Single Slap; Filter Only.

## Compressor

`Compressor`

| Knob | Spans |
|---|---|
| Character | 0 to 3 |
| Threshold | -60 dB to 0 dB |
| Ratio | 1 to 1000, log |
| Attack | 300 ms to 0.02 ms, log |
| Release | 5000 ms to 20 ms, log |
| Release Slow | 25000 ms to 100 ms, log |
| Memory | 0 to 1 |
| Knee | 0 dB to +36 dB |
| Detector | off or on |
| RMS Window | 1 ms to 100 ms, log |
| Emphasis | 0 to 1 |
| Emphasis Freq | 30 Hz to 2 kHz, log |
| Makeup | -12 dB to +24 dB |
| Mix | 0 to 1 |

Patches: Level Ride; Fast Peak Catch; Everything At Once; Bus Glue; Voice Ride; Let The Stick Through; Parallel Squash; Wide Knee Glue; Vari-Mu TC1; Vari-Mu TC2; Vari-Mu TC3; Vari-Mu TC4; Vari-Mu TC5; Vari-Mu TC6; Compressor - lean.

## Convolution Reverb

`ConvolutionReverb`

| Knob | Spans |
|---|---|
| Decay | 0 to 1 |
| Damping | 500 Hz to 7.5 kHz, log |
| Predelay | 0 to 1 |
| Diffusion | 0 to 1 |
| Room | 1 to 64 |
| Mix | 0 to 2 |

Patches: Full Room; Short Room; Late Room; Dark Room; Bright Room; Soft Onset; Tight Room; Wet Only.

## De-Esser

`DeEsser`

| Knob | Spans |
|---|---|
| Frequency | 800 Hz to 8 kHz, log |
| Range | 0 dB to +20 dB |
| Sensitivity | 0 dB to +48 dB |
| Mode | off or on |
| Release | 1 ms to 200 ms, log |
| Attack | 0.1 ms to 10 ms, log |
| Listen | off or on |

Patches: Vocal; Bright Vocal; Whispered Verse; Guitar Pick Noise; Cymbal Edge; Hard De-Ess.

## Digital Delay

`DigitalDelay`

| Knob | Spans |
|---|---|
| Time | 12.5 ms to 800 ms, log |
| Feedback | 0 to 0.99 |
| Mix | 0 to 2 |
| Glide | 800 ms to 8000 ms, log |
| Sync | off or on |
| Division | 0 to 15 |
| Repeat Tone | 800 Hz to 16 kHz, log |
| Repeat Cut | 20 Hz to 400 Hz, log |

Patches: Clean Repeats; Eighth Notes; Dotted Eighths; Short Doubling; Long Ambient; Band Limited Repeats.

## Distortion

`Distortion`

| Knob | Spans |
|---|---|
| Distortion | 0 to 1 |
| Filter | 0 to 1 |
| Tone | -1 to 1 |
| Volume | 0 to 1 |
| Mix | 0 to 1 |
| Character | off or on |
| Ceiling | 0.5 to 2 |
| Boost | 0 dB to +35 dB |
| Asymmetry | 0 to 1 |
| Body | 0 to 1 |

Patches: Filter Half Mid Gain; Filter Open Low Gain; Filter Closed Full Gain; High Ceiling Full Gain; Low Ceiling Mid Gain; Flat Legs Mid Gain; Scoop Centre Full Boost; Scoop Bright Mid Gain; Scoop Bass Low Gain; Scoop Low Boost Even; Clean Edge.

## Dynamic EQ

`DynamicEQ`

| Knob | Spans |
|---|---|
| Frequency | 30 Hz to 16 kHz, log |
| Width | 0.5 to 12, log |
| Threshold | -60 dBFS to 0 dBFS |
| Ratio | 1 to 20, log |
| Attack | 0.1 ms to 100 ms, log |
| Release | 5 ms to 1000 ms, log |
| Mix | 0 to 1 |
| Listen | off or on |

Patches: Wide Band; Boxiness Control; Harshness Control; Low End Tamer; Sibilance; Half Measure.

## Exciter

`Exciter`

| Knob | Spans |
|---|---|
| Tune | 600 Hz to 6 kHz, log |
| Harmonics | 0 to 1 |
| Mix | 0 to 0.7 |
| Character | off or on |
| Output | -24 dB to 0 dB |

Patches: Voice Air; Percussive Edge; Mix Sheen; Mid Presence; Transient Bite; Transient Soft; Wet Sidechain.

## Expander

`Expander`

| Knob | Spans |
|---|---|
| Threshold | -80 dBFS to 0 dBFS |
| Ratio | 1 to 8, log |
| Depth | 0 dB to -80 dB |
| Attack | 0.01 ms to 1000 ms, log |
| Release | 2 ms to 4000 ms, log |
| Key Low | 25 Hz to 4 kHz, log |
| Key High | 250 Hz to 35 kHz, log |
| Key Listen | off or on |
| Detector | off or on |

Patches: Gentle Lift; Noise Floor Trim; Snare Tighten; Guitar Amp Hum; Room Reduction; Hard Downward; Expander - lean.

## Flanger

`Flanger`

| Knob | Spans |
|---|---|
| Rate | 0.05 Hz to 10 Hz, log |
| Range | 0 to 1 |
| Manual | 0.25 ms to 5 ms, log |
| Color | 0 to 0.95 |
| Mix | 0 to 1 |
| Polarity | off or on |
| Sync | off or on |
| Division | 0 to 6 |

Patches: Slow jet; Fast metallic; Held comb; Negative jet; Gentle; Synced one bar.

## Fuzz

`Fuzz`

| Knob | Spans |
|---|---|
| Fuzz | +18 dB to +54 dB |
| Level | 0 to 1 |
| Tone | 0 to 1 |
| Bias | -1 to 1 |
| Load | 0 to 1 |
| Mix | 0 to 1 |
| Output Tilt | -6 dB to +6 dB |

Patches: Bias centred, fuzz half; Full fuzz, volume back; Starved bias, gated; Cleaned up, load engaged; Cascade scoop centred; Cascade sustain maximum; Cascade treble end; Full fuzz, mix back; Fuzz - lean.

## Graphic EQ

`GraphicEQ`

| Knob | Spans |
|---|---|
| 31 | -12 dB to +12 dB |
| 63 | -12 dB to +12 dB |
| 125 | -12 dB to +12 dB |
| 250 | -12 dB to +12 dB |
| 500 | -12 dB to +12 dB |
| 1k | -12 dB to +12 dB |
| 2k | -12 dB to +12 dB |
| 4k | -12 dB to +12 dB |
| 8k | -12 dB to +12 dB |
| 16k Shelf | -12 dB to +12 dB |
| Gain | -12 dB to +12 dB |
| Volume | -12 dB to +12 dB |
| Band Q | 0.7 to 2.5 |
| Constant Q | off or on |

Patches: Flat; Scooped Mids; Pushed Mids; Trimmed Bottom; Rolled Top; Full Boost.

## Harmonizer

`Harmonizer`

| Knob | Spans |
|---|---|
| Pitch | -12 semitones to 12 semitones |
| Voice 1 | -12 semitones to 12 semitones |
| Voice 2 | -12 semitones to 12 semitones |
| Voice 3 | -12 semitones to 12 semitones |
| Level 1 | -40.3175 dB to 0 dB |
| Level 2 | -40.3175 dB to 0 dB |
| Level 3 | -40.3175 dB to 0 dB |
| Detune | 0 cents to 25 cents |
| Spread | 0 to 1 |
| Mix | 0 to 2 |

Patches: Third and fifth above, octave below; Octave below, doubled; Wide unison; Fourths and fifths; Octave up and down; Minor triad, voices alone; Third and fifth - lean.

## High Pass

`HighPass`

| Knob | Spans |
|---|---|
| Frequency | 10 Hz to 20 kHz, log |
| Resonance | 0.5 to 16, log |
| Slope | off or on |
| Mix | 0 to 1 |
| Trim | -12 dB to +12 dB |

Patches: Flat; Rumble Cut; Stage Low-Cut; Thin It Out; Radio; Whistle.

## Ladder Filter

`LadderFilter`

| Knob | Spans |
|---|---|
| Cutoff | 20 Hz to 18 kHz, log |
| Resonance | 0 to 4.2 |
| Drive | 0 dB to +24 dB |
| Passband Comp | 0 to 1 |
| Poles | 1 to 4 |
| Oversample | off or on |
| Mix | 0 to 1 |

Patches: Wide Open; Squelch At The Knee; Sustained Sine At Cutoff; Dark; Growl With Drive; Two Pole Soft; Ladder - lean.

## Limiter

`Limiter`

| Knob | Spans |
|---|---|
| Ceiling | -24 dBFS to 0 dBFS |
| Gain | 0 dB to +24 dB |
| Lookahead | 0 ms to 10 ms |
| Release | 5 ms to 2000 ms, log |
| True Peak | off or on |
| Knee | 0 dB to +12 dB |

Patches: Safety Ceiling; Catch The Peaks; Loud; Soft Ceiling; Delivery Ceiling; Loud (True Peak); Delivery Ceiling - lean.

## Low Pass

`LowPass`

| Knob | Spans |
|---|---|
| Frequency | 20 Hz to 20 kHz, log |
| Resonance | 0.5 to 16, log |
| Slope | off or on |
| Mix | 0 to 1 |
| Trim | -12 dB to +12 dB |

Patches: Open; Soft Roll; Steep Cut; Resonant Peak; Squelch; Sub Only.

## Multi-Tap Delay

`MultiTapDelay`

| Knob | Spans |
|---|---|
| Time | 20 ms to 400 ms, log |
| Pattern | 0 to 11 |
| Heads | 3 to 8 |
| Feedback | 0 to 0.95 |
| Mix | 0 to 2 |
| Tilt | -1 to 1 |
| Repeat Tone | 800 Hz to 16 kHz, log |
| Sync | off or on |
| Division | 0 to 15 |

Patches: Three Heads, Even; Three Heads, Even - lean; Two Heads, Near Loudest; Four Heads, Far Loudest; Eight Heads, Dense; One Head, Long Repeats; Triplet Grid, Synced.

## Multiband Compressor

`MultibandCompressor`

| Knob | Spans |
|---|---|
| Crossover Low | 40 Hz to 800 Hz, log |
| Crossover High | 800 Hz to 8 kHz, log |
| Low Threshold | -60 dBFS to 0 dBFS |
| Mid Threshold | -60 dBFS to 0 dBFS |
| High Threshold | -60 dBFS to 0 dBFS |
| Low Ratio | 1 to 20, log |
| Mid Ratio | 1 to 20, log |
| High Ratio | 1 to 20, log |
| Low Gain | -12 dB to +12 dB |
| Mid Gain | -12 dB to +12 dB |
| High Gain | -12 dB to +12 dB |
| Attack | 0.1 ms to 100 ms, log |
| Release | 5 ms to 1000 ms, log |
| Mix | 0 to 1 |

Patches: Master Glue; Bass Control; Vocal Bus; De-Boom; Loudness.

## Noise Gate

`NoiseGate`

| Knob | Spans |
|---|---|
| Threshold | -80 dBFS to 0 dBFS |
| Attack | 0.01 ms to 1000 ms, log |
| Hold | 2 ms to 2000 ms, log |
| Release | 2 ms to 4000 ms, log |
| Range | 0 dB to -80 dB |
| Key Low | 25 Hz to 4 kHz, log |
| Key High | 250 Hz to 35 kHz, log |
| Key Listen | off or on |

Patches: Default; Tom Tighten; Gated Reverb; Vocal Breath Trim; Amp Hiss; Drum Bleed.

## Notch

`Notch`

| Knob | Spans |
|---|---|
| Frequency | 20 Hz to 16 kHz, log |
| Width | 0.5 to 32, log |
| Harmonics | off or on |
| Depth | 0 to 1 |
| Trim | -12 dB to +12 dB |

Patches: Wide Notch; Hum 50; Hum 60; Feedback Tamer; Mud Scoop; Whistle Kill.

## Octaver

`Octaver`

| Knob | Spans |
|---|---|
| Direct | 0 to 1 |
| Octave 1 | 0 to 1 |
| Octave 2 | 0 to 1 |
| Tracking | 40 Hz to 400 Hz, log |
| Tone 1 | 100 Hz to 2 kHz, log |
| Tone 2 | 40 Hz to 800 Hz, log |
| Sensitivity | -90 dBFS to -40 dBFS |

Patches: Octave down under the dry; Both octaves; Octaves alone, no dry; Bass guitar; High on the neck; Two octaves down alone; Both octaves - lean.

## Overdrive

`Overdrive`

| Knob | Spans |
|---|---|
| Drive | 12 to 108, log |
| Tone | 0 to 1 |
| Level | 0 to 1 |
| Mix | 0 to 1 |
| Body | 360 Hz to 1.44 kHz, log |
| Ceiling | 0.5 to 1 |
| Symmetry | -1 to 1 |

Patches: Mid Drive Flat; Low Drive Bright; Full Drive Dark; Full Drive Bright; Thick Body Mid Drive; Tight Body High Drive; Asymmetric Mid Drive; Edge Boost.

## Parametric EQ

`ParametricEQ`

| Knob | Spans |
|---|---|
| Low Freq | 20 Hz to 200 Hz, log |
| Low Boost | 0 to 10 |
| Low Atten | 0 to 10 |
| Bell 1 Freq | 20 Hz to 20 kHz, log |
| Bell 1 Gain | -16 dB to +16 dB |
| Bell 2 Freq | 20 Hz to 20 kHz, log |
| Bell 2 Gain | -16 dB to +16 dB |
| Bell 3 Freq | 20 Hz to 20 kHz, log |
| Bell 3 Gain | -16 dB to +16 dB |
| Bandwidth | 0 to 10 |
| High Freq | 3 kHz to 16 kHz, log |
| High Boost | 0 to 10 |
| Atten Freq | 5 kHz to 20 kHz, log |
| High Atten | 0 to 10 |
| Q Law | off or on |
| Output | -12 dB to +12 dB |

Patches: Flat; Low Lift And Clear; Air Above Ten; Broad Warm Tilt; Sharp Presence Bell; Rumble Trim And Top Trim; Wide Gentle Smile.

## Phaser

`Phaser`

| Knob | Spans |
|---|---|
| Rate | 0 Hz to 10 Hz |
| Depth | 0 to 1 |
| Centre | 60 Hz to 2 kHz, log |
| Feedback | 0 to 0.9 |
| Mix | 0 to 1 |
| Stages | 0 to 4 |
| Shape | 0.35 to 0.65 |
| Drive | 0 to 1 |
| Sync | off or on |
| Division | 0 to 6 |

Patches: Four stage, no feedback; Four stage with resonance; Slow wide sweep; Fast tight sweep; Six stage deep; Held notch pair; Bass-safe shallow; Synced half bar; Phaser - lean.

## Ping-Pong Delay

`PingPongDelay`

| Knob | Spans |
|---|---|
| Time | 20 ms to 1000 ms, log |
| Feedback | 0 to 0.99 |
| Mix | 0 to 2 |
| Spread | 0 to 1 |
| First Side | off or on |
| Sync | off or on |
| Division | 0 to 15 |
| Repeat Tone | 800 Hz to 16 kHz, log |
| Repeat Cut | 20 Hz to 400 Hz, log |

Patches: Wide Bounce; Eighth Note Bounce; Quarter Note Bounce; Narrow Bounce; Two Delays; Dark Bounce; Right First.

## Pitch Shifter

`PitchShifter`

| Knob | Spans |
|---|---|
| Pitch | -12 semitones to 12 semitones |
| Fine | -50 cents to 50 cents |
| Mix | 0 to 2 |
| Delay | 0 ms to 112.5 ms |
| Feedback | 0 to 0.95 |

Patches: Fifth Above; Octave Up; Octave Down; Doubler; Rising Fifths; Falling Fourths; Shifted Only.

## Reverb

`Reverb`

| Knob | Spans |
|---|---|
| Character | 0 to 4 |
| Decay | 0.3 s to 10 s, log |
| Size | 0.5 to 1.5 |
| Predelay | 0 ms to 200 ms |
| Diffusion | 0 to 0.9 |
| Damping | 500 Hz to 16 kHz, log |
| Bandwidth | 500 Hz to 20 kHz, log |
| Low Cut | 20 Hz to 500 Hz, log |
| Mod Depth | 0 ms to 2 ms |
| Mod Rate | 0.1 Hz to 5 Hz, log |
| Width | 0 to 1 |
| Tone | -12 dB to +12 dB |
| Mix | 0 to 2 |

Patches: Steel Plate; Short Plate; Damped Plate; Bass-Free Plate; Small Room; Live Room; Concert Hall; Dark Chamber; Bright Chamber; Slow Bloom.

## Ring Modulator

`RingMod`

| Knob | Spans |
|---|---|
| Frequency | 0.1 Hz to 8 kHz, log |
| Depth | 0 to 1 |
| Mix | 0 to 1 |
| Shape | 0 to 1 |
| Balance | -1 to 1 |
| Program Bal | -1 to 1 |
| Squelch | off or on |
| Threshold | -72 dBFS to 0 dBFS |
| Release | 5 ms to 500 ms, log |
| Carrier Low | 2 Hz to 200 Hz, log |
| Stereo Phase | -180 degrees to 180 degrees |
| Character | off or on |

Patches: Clean Ring; Textbook AM; Clangour; Bell Strike; Chopper; Soft Chopper; Detuned Ring; Wide Ring; Growl.

## Saturation

`Saturation`

| Knob | Spans |
|---|---|
| Drive | -12 dB to +15 dB |
| Output | -24 dB to +12 dB |
| Mix | 0 to 1 |
| Headroom | -12 dB to +12 dB |
| Bias | -1 to 1 |
| Speed | 3.75 ips to 30 ips, log |
| Tilt | -6 dB to +6 dB |
| Hysteresis | 0 to 1 |

Patches: Gentle thickening; Hot into the curve; Tape at fifteen; Tape at seven and a half; Under-biased and bright; Iron, low end working; Offset, even harmonics; Mix back; Saturation - lean.

## Shimmer Hall

`ShimmerHall`

| Knob | Spans |
|---|---|
| Character | off or on |
| Shimmer | 0 to 1 |
| Rise | 0 to 0.9 |
| Bloom | 20 ms to 800 ms, log |
| Interval | 0 to 5 |
| Decay | 0.3 s to 10 s, log |
| Size | 0.5 to 1.5 |
| Damping | 500 Hz to 16 kHz, log |
| Mix | 0 to 2 |

Patches: Octave Rise; Short Stagger; Fifth Halo; Slow Rise; Rise Damped; Falling Octaves; Octave Bloom.

## Slapback Delay

`SlapbackDelay`

| Knob | Spans |
|---|---|
| Time | 40 ms to 250 ms, log |
| Level | 0 to 2 |
| Saturation | 0 to 1 |
| Tone | 2 kHz to 20 kHz, log |
| Wow | 0 cents to 3.5 cents |
| Repeats | 0 to 0.6 |

Patches: Single Slap; Short Slap; Doubling; Hot Return; Two Repeats; Dark Slap.

## Stereo Widener

`StereoWidener`

| Knob | Spans |
|---|---|
| Width | 0 to 2 |
| Delay | 1 ms to 40 ms, log |
| Character | off or on |

Patches: Haas 14 ms; Haas Tight; Haas Wide; Haas Recentred; Mid/Side Wide; Mid/Side Narrow; Mono.

## Tape Delay

`TapeDelay`

| Knob | Spans |
|---|---|
| Time | 20 ms to 1200 ms, log |
| Feedback | 0 to 0.99 |
| Mix | 0 to 2 |
| Glide | 1200 ms to 12000 ms, log |
| Wow | 0 cents to 8 cents |
| Flutter | 0 cents to 4 cents |
| Record Level | 0 to 1 |
| Spacing | 2 um to 20 um, log |
| Spread | 0 to 1 |
| Sync | off or on |
| Division | 0 to 15 |

Patches: Warm Repeats; Long Repeats, Slow Glide; Short Slap; Dark Repeats, Heavy Wow; High Intensity; Worn Heads; Clean Transport; Dotted Eighth, Synced; Tape Delay - lean.

## Transient Shaper

`TransientShaper`

| Knob | Spans |
|---|---|
| Attack | -15 dB to +15 dB |
| Sustain | -24 dB to +24 dB |
| Output | -22 dB to +6 dB |
| Attack Speed | 0.2 to 5, log |
| Sustain Hold | 0 ms to 500 ms |

Patches: Flat; Snap; Room Off; Room On; Soften Pick; Kick Punch; Ambient Swell.

## Tremolo

`Tremolo`

| Knob | Spans |
|---|---|
| Character | 0 to 1 |
| Rate | 0.5 Hz to 15 Hz, log |
| Depth | 0 to 1 |
| Shape | 0 to 1 |
| Lag | 5 ms to 100 ms |
| Bias | 0 to 1 |
| Speed Link | off or on |
| Stereo Phase | -180 degrees to 180 degrees |
| Sync | off or on |

Patches: Bias Wobble; Bias Deep Slow; Bias Warm Fast; Opto Chop; Opto Soft; Opposed Pair; Helicopter; Slow Swell; Eighth Note Chop.

## Vibrato

`Vibrato`

| Knob | Spans |
|---|---|
| Rate | 2 Hz to 15 Hz, log |
| Depth | 0 cents to 60 cents |
| Rise | 0.15 s to 5 s, log |
| Engage | off or on |
| Delay | 1 ms to 12 ms |
| Tone | 2 kHz to 18 kHz, log |
| Body | 20 Hz to 200 Hz, log |
| Level | -12 dB to 0 dB |

Patches: Published defaults; Ramp in slow; Instant on; Shallow fast; Deep slow; Short line bright; Long line.
