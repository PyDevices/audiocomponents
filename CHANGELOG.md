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
