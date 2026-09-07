# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

- `CombFilter` is rebuilt from scratch on `_component.Component` for the
  effects program's Phase 2 (`lib/audioeffects/rebuilt/combfilter.py`;
  dossier `docs/effects/CombFilter.md`, evidence
  `docs/effects/CombFilter-evidence.md`). **The old class did not tune.** It
  sat on `audiodelays.Echo`, which floors its line at the node's own buffer
  length, so every frequency from 47 to 880 Hz came out as the same 46.88 Hz
  comb - the frequency argument did nothing over almost the whole of its
  range. The rebuild sits on `audioecho.FeedbackDelay`, which reads its line
  with per-sample interpolation and tunes to 0.002 cents, and adds the
  surface the old class had none of: six macros - Frequency, Feedback, Mix,
  Tone, Trim, Glide - six patches, `capabilities = ()`, and zero latency at
  every setting and every rate. **Its portability tier is `audioif`**
  (`audioecho`, `audiobiquad`); there is no honest stock fallback, because
  even a 512-byte buffer floors the comb at 187.5 Hz.
  - Trim is **input** headroom, not make-up, and it runs to -18 dB: a comb's
    peak gain is `1/(1-Feedback)`, +26 dB at the top of the knob, and a trim
    behind the comb attenuates a signal that has already hit the rail.
  - Two things stated rather than hidden. The **negative comb** - peaks on
    the odd half-multiples, the hollow one - is not built: it composes out of
    nodes that exist, but only at seven nodes, three delay lines and a
    tuning-dependent 2M pre-delay, about four times the class's cost budget.
    And **above Feedback 0.5 the tail may never reach zero**: the node's line
    is int16 and `to_s16` rounds, so the loop can park on a limit cycle
    bounded by `floor(0.5/(1-g))`. Whether it does is decided by the tuning -
    at 1 kHz, where 48 000/f is a whole 48 frames, it parks on exactly that
    bound (10 LSB, -70.3 dBFS, at Feedback 0.95); at 438.3 Hz, half a sample
    off the grid, it reaches exact zero at every setting. `TAIL_SAMPLES` is
    `None` and `reset()` clears it.
  The old class stays in `eq.py`, untouched, beneath the registry; it had no
  macro surface and so no old-surface trait tests to retire, and
  `tests/test_cpython_effects_combfilter.py` is new.

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
