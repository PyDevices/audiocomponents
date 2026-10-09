# Roadmap

audiocomponents is heading toward a complete rebuilt effects library, measured
the same way on every interpreter and board, and drums that sound more like
the real thing.

## Next: effects

- Pitch and stereo effects rebuilt: PitchShifter, Harmonizer, Octaver,
  StereoWidener, Rack, ShimmerHall and AirSpace. The README gains a latency
  table for every class, each rack and a five-effect chain.
- A release that carries the rebuilt effects, with a changelog.
- Flanger rebuilt after the Electric Mistress. Until it measures up on every
  target, the package keeps serving today's `modulation.Flanger`.
- The two placeholder classes in `audioeffects/rebuilt/` (`ExampleStock`,
  `ExampleAudioif`) go once shipped classes cover both portability tiers.

- Control moves that ramp instead of stepping: Mix, levels and depths over
  20 ms in audiodsp's nodes, then filter corners, then crossfaded patch
  changes. The policy is in [docs/control-smoothing.md](docs/control-smoothing.md).

## Later: effects

- Every effect compared with its counterpart in hexefx_audiolib, adopting that
  algorithm where it does measurably better on our tests. Licences are
  respected file by file: GPL-3.0 code informs a design and is never ported.
- CabinetSim with real cabinet impulse responses, if their licence allows
  shipping them. Until then they serve as a reference for the synthetic one.
- AmpSim, an amp and DI model after the Tech 21 SansAmp GT2, built from
  measurements of a hardware unit rather than a component trace alone.

## Later: instruments

- acoustickit: a shallow pitch drop on hard tom hits, a reworked hi-hat, and
  a sourced model for the snare wires.
- acoustickit cymbals: a bloom shaped into the strike, and mode sets that
  change with velocity. A linear bank has a ceiling here; expect better, not real.

## Tools

- One renderer core behind `tools/render_component.py` and MPVST's harness.
  Events become data, so a MIDI file or a DAW export can drive a render, and
  it keeps running on MicroPython.
- A listening rig that plays instruments in a DAW through MPVST, with lanes
  named by voice, so you can see which voice hit and when.

Bugs, and things you need that don't work yet, go to
[issues](https://github.com/PyDevices/audiocomponents/issues).
