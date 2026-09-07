# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

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
