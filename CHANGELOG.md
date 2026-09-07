# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

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
