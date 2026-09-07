# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

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
