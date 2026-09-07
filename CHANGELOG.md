# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

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
  Q ≤ 12 but −35.6 dB at 60 Hz Q 12 and −11.0 dB at 20 Hz Q 32, against
  −78.9 and −40.0 dB on the integer kernel it replaces. The dossier's T1 is
  recorded disconfirmed below about 250 Hz with that cause, and its §5
  carries the audioif node ask that would recover 17–36 dB of it.
  The old class stays in `eq.py`, untouched, beneath the registry.

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
