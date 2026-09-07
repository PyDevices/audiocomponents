# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

- **`audioeffects.DynamicEQ` rebuilt** on `_component.Component`, one of the
  effects program's Phase 2 classes. The old class had **no macros at all**
  on the processor with the most to expose: frequency, Q, threshold and ratio
  were constructor-only, attack and release were hardcoded at 2 ms and 80 ms,
  and there was no range, no direction and no way to move the band once it was
  built. It has **eight macros and six patches** now, every one of them live.
  Three changes under the surface. The split moved to **`audiobiquad.Biquad`**,
  which takes the idle reconstruction from 0.015 dB to **0.0000 dB** from
  100 Hz to 12 kHz and takes a low band's held DC to **0 LSB** at 60, 80, 120,
  400 and 3000 Hz - on the Q12 ported biquad the same 60 Hz section holds
  2 LSB for ever, which is audioif#23. The Splitter is fed through a
  **block-sized guard**, so an impulse inside a 40000-frame source no longer
  vanishes (measured: guarded peak 20000, unguarded peak 0), and renders are
  byte-identical at 256, 8192, 16384, 20000 and 32768 frames. And the class
  **does not end in its Mixer**: upstream CircuitPython's `Mixer.reset_buffer`
  stops every voice permanently, and anything upstream resets what it is
  handed - so an `audioroute.MidSide` identity carries the output, without
  which every kit render on `cmods/bin/circuitpython-effects` came back
  silent.
  **`Mix` is the Range control**, and that is arithmetic rather than a saving:
  with `H_notch + H_bandpass` identically 1 the whole class is
  `1 + m*B*(g - 1)`, so a dry/wet blend and a ceiling on how far the band may
  move are the same number. Measured against that closed form at six blends,
  worst **0.0035 dB**, with a tone two octaves away moving **0.0006 dB**
  across the sweep. `Mix` 0 is a byte-identical bypass; `range_db` reports
  `-20 log10(1 - Mix)`.
  `expand=True` is a **constructor option** rather than a knob, because
  `audiodynamics` fixes its mode at construction and a second, idle detector
  would cost a full block every block. Neither direction boosts.
  Measured: the composite follows the node's gain law within **0.42 dB** over
  five levels; the bell matches the closed form built from the band-pass's own
  response within **0.03 dB** everywhere but the centre; a tone two octaves
  out moves **0.055 dB** between idle and 19 dB of reduction; latency is
  **0 samples** at 48 kHz and 44.1 kHz and no option can add any. One seed
  claim did not survive: the 0.42 dB by which the centre sits above the law is
  **not** the notch branch leaking - that branch measures exactly zero at f0 -
  it is the detector's finite attack, and it moves with attack time and with
  frequency. Its dossier is `docs/effects/DynamicEQ.md` and its evidence pack
  is `docs/effects/DynamicEQ-evidence.md`.

### Fixed

- `tests/parity/effects_library_smoke.py` walked one instance through all of
  a class's patches on a **4096-frame** probe and pulled eight output blocks
  per patch, so a class whose output block is the contract's own 256 frames
  used the whole probe on its first two patches and read as **silent** for the
  rest. The probe is 8000 frames now - under `audioroute.Splitter`'s
  8192-frame ring, so no unguarded Splitter class in the catalogue changes -
  and one patch may pull at most 1024 frames off it, which leaves room for
  seven patches and puts every class on the same budget.

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
