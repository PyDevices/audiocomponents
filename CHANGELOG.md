# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

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
