# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

- **`Compressor` rebuilt from scratch** (effects program, Phase 2), against
  `docs/effects/Compressor.md`'s frozen trait table and on the Phase 2
  construction module. The four characters now differ in detector law,
  release law, ratio law and side-chain weighting rather than in three time
  constants: `fet` has both time knobs live and faster clockwise with the
  threshold rising with ratio, `optical` — the default — has **no working
  time knobs at all**, `vca` runs a true-RMS detector and a level-dependent
  attack, and `varimu`'s slope climbs with level with the six factory time
  constants as patches. Two `audiodynamics.Dynamics` in series carry the
  two-stage release with a memory; the surface is fourteen macros and
  fourteen patches; latency is zero at every setting. Portability tier
  **audioif**, `REQUIRES = ("audiodynamics", "audioroute")`. Evidence:
  `docs/effects/Compressor-evidence.md`.
- The kit's CURVE and paired-build fixtures name `character="fet"`
  explicitly: their subject is the textbook single-stage law, and
  `Compressor`'s default character is now the LA-2A.
- **`audioeffects.Limiter` rebuilt** on `_component.Component`, the first of
  the effects program's Phase 2 classes. It is two `audiodynamics.Dynamics` in
  series now: a shaping stage carrying the Knee, the Lookahead and a **4x
  polyphase true-peak detector**, and a catch stage that is the reason
  lookahead no longer overshoots — a 1 ms burst into a −12 dBFS ceiling used
  to come out **1.45 dB over** at 10 ms of lookahead and now sits on the
  ceiling at every setting. `latency_samples` finally reports the lookahead
  instead of a hardcoded zero; three of the old class's five patches were
  delaying the audio by up to 484 samples while claiming none. The surface
  gains **Gain** (drive into the ceiling) and **Knee**, and its Release
  default moves to 149 ms so the class's own THD bound is met. Its dossier is
  `docs/effects/Limiter.md` and its evidence pack is
  `docs/effects/Limiter-evidence.md`.
- **`Expander` rebuilt** on the effects program's construction module, as
  `lib/audioeffects/rebuilt/expander.py`; the old class stands untouched in
  `dynamics.py` until Phase 6 retires `_core`. It had no macros and no patch
  at all; it has nine macros and six patches now — Threshold, Ratio, Depth,
  Attack, Release, Key Low, Key High, Key Listen, Detector — a true-RMS
  detector, a two-ended 12 dB/octave key band, an external key input, and a
  Depth floor that reaches −80 dB where the old class was stuck at the node's
  −60 dB literal without saying so. Portability tier **audioif**
  (`audiodynamics`); `latency_samples` 0 with no look-ahead option at all.
  The dossier's Hold macro is deliberately absent: `hold_ms` does nothing in
  `DYN_EXPAND` and the reason is measured, not assumed
  (`docs/effects/Expander.md` §8.1, `docs/effects/Expander-evidence.md`).
- `NoiseGate` is rebuilt from scratch on the construction module, after the
  Drawmer DS201 (effects program, Phase 2). It gains the eight controls the
  DS201 has and the shipped class had none of: Threshold, Attack, **Hold**,
  Release, **Range**, a two-ended **key band** and **Key Listen**, with six
  named patches. Its closed state is now the Range you set - -15 dB, say,
  where the old class could only slam to -80 - and its law is a depth rather
  than the 8 dB-per-dB slope it inherited from the node's memoryless gain
  computer. `duck=True` builds the ducking version for voice-overs;
  `lookahead_ms` is off by default and is the class's only latency. The old
  class stands untouched in `lib/audioeffects/dynamics.py` beneath the
  registry.
  Evidence: `docs/effects/NoiseGate-evidence.md`.
- `tools/render_effect.py` takes `--option name=value`, so a render can
  reach a class's construction options - a duck graph and a look-ahead are
  build choices, not knobs.
- `DeEsser` is rebuilt on the effects program's Phase 1 palette and served
  from `lib/audioeffects/rebuilt/deesser.py`; the old class stands untouched
  beneath it. It is the dbx 902's mechanism now — the sibilant band's level
  compared with the programme's rather than with a threshold knob — so one
  setting works on a whisper and a belt: measured across the kit's four
  sibilant probes from -6 to -55 dBFS, the reduction spreads 0.772 dB where
  the class it replaces spent its whole range inside 14 dB. Seven macros
  (Frequency, Range, Sensitivity, Mode, Release, Attack, Listen) and six
  patches, where there were none; a broadband and an HF-only mode, where
  there was only broadband; and Range is a real maximum, where `ratio` was
  not. Portability tier **audioif** (`audiobiquad`, `audiodynamics`,
  `audioroute`), latency zero, and no option that adds any. Three traits the
  palette cannot reach are stated in its docstring rather than hidden: the
  release curves where the 902's is a straight line in dB, Range is an
  asymptote rather than a clamp, and the program-dependent attack does not
  reach the 902's ratio. Evidence:
  [`docs/effects/DeEsser.md`](docs/effects/DeEsser.md) and
  [`docs/effects/DeEsser-evidence.md`](docs/effects/DeEsser-evidence.md).
### Added

- `TransientShaper` rebuilt from scratch on the Phase 2 construction module
  (`lib/audioeffects/rebuilt/transientshaper.py`), the effects programme's
  first rebuilt class. SPL Transient Designer: Attack ±15 dB and Sustain
  ±24 dB acting **at the same time** on one `audiodynamics.Dynamics` node
  through Phase 1's `transient_dual`, a peak-hold sustain envelope through
  `slow_hold_ms`, an Output trim, an Attack Speed scaler and a Sustain Hold
  time — five macros and seven patches where the old class had none, and
  latency 0 samples at every setting. `docs/effects/TransientShaper.md`
  (traits frozen at Station A) and
  `docs/effects/TransientShaper-evidence.md` (the class gate's record) land
  with it. T6, the adaptive time constants both sources assert, is
  **disconfirmed** and said so in the docstring.
- **`audioeffects.MultibandCompressor` rebuilt** on `_component.Component`,
  one of the effects program's Phase 2 classes. The old class had **no macros
  and one empty patch**: crossovers, thresholds and ratios were
  constructor-only, attack and release were hardcoded, and there was no
  make-up, no output gain and no mix. It has **fourteen macros and five
  patches** now, and `Mix` at 0 is a **true bypass** — byte-identical to the
  source, which the summed bands can never be, because a Linkwitz-Riley
  network at unity is an all-pass and not a wire.
  Three changes under the surface. The crossover moved to
  **`audiobiquad.Biquad`**: on the ported `synthio.Biquad` cascade the old
  class held **2 LSB of DC for ever at a 100 Hz corner and 8 LSB at 40 Hz**,
  which is audioif#23 sitting in the one node a multiband cannot do without.
  The Splitter is fed through a **block-sized guard**, so a source that hands
  back more than 8192 frames in one call no longer loses the head of every
  buffer — the old class rendered **exact silence** from 16384-, 20000- and
  32768-frame sources on burst material. And the detectors are **RMS**, which
  is what RaneNote 155's Fig. 7 draws and what the node grew this cycle.
  Two bands or three is `bands=`, a **constructor option** rather than a knob:
  the Mixer pulls a voice at level 0 exactly as hard as one at unity, so a
  muted band is not a cheaper build. `bands=2` is four biquads and two
  detectors against three bands' eight and three.
  Measured: the bands sum flat to **+0.001 / −0.119 dB** from 30 Hz to 20 kHz
  at three bands and **±0.000 dB** at two; each crossover is **−6.06 dB at its
  corner on a 23.7 dB/octave skirt**; driving any band to 12 dB of reduction
  moves the others by **0.00 dB**; latency is **0 samples** at every setting.
  One dossier claim did not survive: the **low** band's own reduction tilts
  **0.73 dB across 30–100 Hz** against a 0.5 dB bar, which is its LR4 skirt
  near its corner plus the RMS detector's 10 ms window, and the class
  docstring carries the arithmetic. Its dossier is
  `docs/effects/MultibandCompressor.md` and its evidence pack is
  `docs/effects/MultibandCompressor-evidence.md`.
- `ParametricEQ` is rebuilt from scratch on `_component.Component` for the
  effects program's Phase 2 (`lib/audioeffects/rebuilt/parametriceq.py`;
  dossier `docs/effects/ParametricEQ.md`, evidence
  `docs/effects/ParametricEQ-evidence.md`). It is a Pultec EQP-1A bottom and
  resonant top with three API 550A proportional-Q bells between: sixteen
  macros in the panel's own units, seven patches, `capabilities = ()`, zero
  latency at every setting and rate. **Its portability tier is `audioif`** -
  eight `audiobiquad.Biquad` sections, whose float state lets a decaying tail
  reach exact zero where the ported `synthio.Biquad` parks on DC (audioif#23).
  The old class stays in `eq.py`, untouched, beneath the registry; its
  old-surface trait test in `tests/test_cpython_effects_dynamics_eq.py` is
  retired in the same commit and replaced by
  `tests/test_cpython_effects_parametriceq.py`.
- **`audioeffects.GraphicEQ` rebuilt from scratch** on the Phase 2
  construction module (`lib/audioeffects/rebuilt/graphiceq.py`), after the
  MXR M-108 Ten Band. Ten octave bands on the pedal's own centres from
  **31.25 Hz** (not the ISO series), a **shelf** on top rather than a tenth
  bell, and GAIN and VOLUME around the bank — fourteen macros and six named
  patches where the old class had **no surface at all**. Its bands now
  **widen as you back off**, measured at 1.780 octaves at +3 dB against
  0.716 at +12, where the old class was constant-Q by omission at Q 1.4; a
  `Constant Q` toggle makes the studio-graphic behaviour a choice instead of
  an accident. A band at its centre detent is a **wire byte for byte**, and
  patch 0 is byte-identical to the source. Bands above Nyquist **clamp and
  say so** (`clamped`, `built_centres`) instead of vanishing silently.
- **`GraphicEQ` moves to the `audioif` portability tier** (`audiobiquad`).
  On the ported `synthio.Biquad` it held **+7 LSB** after silence at
  31.25 Hz/+6 dB and +5 LSB with all ten bands engaged, for ever
  (audioif#23); on `audiobiquad`'s float sections the same settings reach
  exact zero. Twelve sections, `latency_samples` 0, `tail_samples` 465 ms.
  Costs about two thirds of an ESP32-S3's stereo block by arithmetic — not
  yet measured on a board.
- `GraphicEQ` can now be built with no `gains_db` at all (flat, and flat is a
  wire), so its entry in the test and renderer `EXTRA_ARGUMENTS` tables is
  gone. A short `gains_db` still sets the bottom of the bank, as before.
- `LowPass` is rebuilt from scratch on `_component.Component` for the effects
  program's Phase 2 (`lib/audioeffects/rebuilt/lowpass.py`; dossier
  `docs/effects/LowPass.md`, evidence `docs/effects/LowPass-evidence.md`).
  Where the old class had no macros at all, a frozen `q`, a hidden `mix` and
  a `set_frequency` that raised above Nyquist, this one has five macros -
  Frequency, Resonance, Slope, Mix, Trim - six patches, `capabilities = ()`,
  zero latency at every setting and rate, and a declared `tail_samples`.
  **Its portability tier is `audioif`** - three `audiobiquad.Biquad`
  sections, whose float state lets a decaying tail reach exact zero where the
  ported `synthio.Biquad` parks on 1 to 4 LSB of DC at exactly the corners a
  low-pass is for (audioif#23). The old class stays in `eq.py`, untouched,
  beneath the registry; its two old-surface trait tests in
  `tests/test_cpython_effects_dynamics_eq.py` are retired in the same commit
  and replaced by `tests/test_cpython_effects_lowpass.py`.
- `AirSpace` drives its tone filter's Frequency macro instead of calling
  `LowPass.set_frequency()`, which the rebuilt class does not have: hertz
  reach a component through its macro grid, which is what the contract has.
- **`audioeffects.HighPass` is rebuilt from scratch** for the effects
  program's Phase 2, against `docs/effects/HighPass.md`, as
  `lib/audioeffects/rebuilt/highpass.py` on the `_component` construction
  module. It gains the five-macro surface the old class did not have
  (Frequency 10 Hz - 20 kHz, Resonance Q 0.5 - 16, a 12/24 dB/oct Slope
  switch, Mix and a +/-12 dB Trim), six named patches, a declared
  `tail_samples` of 305 152 measured rather than assumed, and a `frequency`
  that clamps below Nyquist instead of raising.
- **`HighPass`'s portability tier moves to audioif** (`REQUIRES =
  ("audiobiquad",)`). Its three sections are `audiobiquad.Biquad`, whose
  float state reaches exact zero; the ported `synthio.Biquad` holds up to
  71 LSB of DC at a 10 Hz corner for ever (audioif#23), which is the Tier 1
  invariant failing at exactly the corners a low-cut is for. A stock
  CircuitPython board can no longer construct this class, where the old one
  ran there and quietly failed that invariant.
- `tests/test_rebuilt_registry.py` no longer asserts that every one of the 46
  names misses: it asserts that a name either misses and keeps its old class
  or resolves to a `Component` of that `NAME`, so no rebuild has to edit it.
- The `HighPass` leg of
  `test_cpython_effects_dynamics_eq.py::test_a_filter_sits_at_its_corner_across_the_whole_band`
  is retired above 20 kHz - outside the frozen span. Its replacement,
  `tests/test_cpython_effects_highpass.py::CornerTest`, walks the whole span
  at both slopes and at three rates.
- Phase 2 of the effects program: **`BandPass` rebuilt from scratch** on the
  component contract (`lib/audioeffects/rebuilt/bandpass.py`). It gains a
  four-macro surface where it had none — Frequency, Width, Slope and Mix —
  six patches, and a `tail_samples` computed from the build rather than left
  `None`, which for a resonator is 301 ms at the Sub Window patch and 3 ms at
  the default. Its portability tier moves from stock to **audioif**
  (`REQUIRES = ("audiobiquad",)`): on the ported Q15 biquad a low centre
  holds DC for ever (audioif#23), and on audioif's float-state node every
  setting the surface reaches settles to bit-exact zero. The old class stays
  in `eq.py` untouched; the registry adopts the rebuild by `NAME`. Dossier
  `docs/effects/BandPass.md`, evidence `docs/effects/BandPass-evidence.md` —
  the board leg is not taken and one trait, T4's `|H(f0/100)|` clause, is
  disconfirmed above about 2.5 kHz for a reason that is RBJ's closed form and
  not this class.
- `Notch` is rebuilt from scratch on `_component.Component` for the effects
  program's Phase 2 (`lib/audioeffects/rebuilt/notch.py`; dossier
  `docs/effects/Notch.md`, evidence `docs/effects/Notch-evidence.md`).
  Where the old class had no macros at all, no width knob, a hidden `mix`,
  no declared tail and a `set_frequency` that raised above Nyquist, this one
  has five macros — Frequency, Width, Harmonics, Depth, Trim — six patches,
  `capabilities = ()`, zero latency at every setting and rate, and a
  declared `tail_samples` measured at its own worst corner.
  **Its portability tier is `audioif`** — three `audiobiquad.Biquad`
  sections, whose float state lets a decaying tail reach exact zero where
  the ported `synthio.Biquad` parks on 2 LSB of DC at `Notch(60 Hz, q=8)`
  and 18 at `Notch(20 Hz, q=32)`, which are the settings a notch is most
  used at (audioif#23).
  **The trade that move costs, stated because a caller has to know it:** a
  `float` coefficient set cannot hold the notch's zeros exactly on the unit
  circle, so the rejection at the centre is a true null from 500 Hz up at
  Q ≤ 12 but −35.65 dB at 60 Hz Q 12 and −11.21 dB at 20 Hz Q 32, against
  −78.87 and −40.04 dB on the integer kernel it replaces. The dossier's T1 is
  recorded disconfirmed below about 250 Hz with that cause, and its §5
  carries the audioif node ask that would recover 17–36 dB of it.
  The old class stays in `eq.py`, untouched, beneath the registry.
- `LadderFilter` rebuilt on the component contract, as
  `lib/audioeffects/rebuilt/ladderfilter.py` — one `audioladder.Ladder`, so
  the class is **audioif tier** (`REQUIRES = ("audioladder",)`) and does not
  run on a stock CircuitPython board. It is a ladder now rather than four
  low-passes in a row: the passband droops as `Resonance` rises, it
  self-oscillates at the top of the knob at the cutoff, and `Drive` is the
  only warmth control, all three of which the old class could not do. Seven
  macros where it had none, seven patches where it had one, and
  `latency_samples` 0 at every setting with no latency-adding option.
  Evidence: `docs/effects/LadderFilter-evidence.md` — five traits
  demonstrated, five Tier 1 invariants green on three interpreters at three
  rates, nine planted faults all red, 48 renders byte-identical across
  CPython, MicroPython and the patched CircuitPython. **Cost is unmeasured on
  both boards.**

## v0.2.0 (2026-09-03)

The first release from this repository. These packages continue a version
history begun in audioif, which published them up to 0.1.1 — that is why
the first release from this repository is 0.2.0.

### Added

- Publishing. `pydevices-audioinstruments` and `pydevices-audioeffects` build,
  publish to TestPyPI and request their MIP index entries from here
  (`prepare-release.yml`, `tag-release.yml`, `publish-release-packages.yml`),
  with `project.urls` pointing here. The two MIP entries ride on one call
  (`mip-profile: audioinstruments,audioeffects`).
- Seeded from audioif at `v0.1.1` (`eefc673`) with the components' own commit
  history preserved: `lib/audioinstruments/`, `lib/audioeffects/`, their
  tests, the two validators, the component API and metadata documents, and
  the instrument parity harness with its goldens.
- `AUDIOIF_PIN`, naming the audioif release every gate runs against.

### Changed

- Phase 1 of the accuracy program: the ten drum machines — `cr78`, `dmx`,
  `drumtraks`, `linndrum`, `simmons_sdsv`, `sp1200`, `tr606`, `tr707`,
  `tr808`, `tr909` — rebuilt as fixed circuits against named references, each
  with a dossier, and blessed at the phase batch listen on 2026-09-02. They
  sound different from audioif's v0.1.1 copies on purpose: the cr78 snare had
  no audible backbeat, the tr808 hats were filtered into near-silence and its
  cymbal was all sizzle and no clang. `docs/phase1-closeout.md` records what
  was and was not established.
- `pydevices-audioif>=0.1.1` is a real dependency floor in both
  `pyproject.toml`s (it was unbounded). The gates still run against the exact
  commit in `AUDIOIF_PIN`, which may sit ahead of the floor.
