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
