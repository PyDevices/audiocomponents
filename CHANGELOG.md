## v0.2.0 (2026-09-03)

- wurlitzer dossier: the attack figure described the grid we no longer use
- tr808: rimshot tail, claves tail, tom tuning -- the three Brad heard
- instruments: replay audioif af837de — log-map time and filter macros, re-derive patch 0 against this tree
- parity: carry audioif's 79ae343 retirement and f7a370a re-captures across; fix #25; bring _vstaudio_shim.py
- pin: move AUDIOIF_PIN to v0.2.0, raise both floors to match, --no-deps on the gates' editable installs
- ci: install numpy for the two tests that import it
- CHANGELOG: the first release from here
- docs: this repository is the shipping source
- pyproject: urls point here, pydevices-audioif>=0.1.1 as the floor
- VERSION: a placeholder that cannot be tagged
- ci: add the release chain, adapted from audioif's workflows
- tr808: cymbal corner sat above the machine's centre of mass
- tr808: rimshot band-pass was parked off its own fundamental
- _support: remove trigger_voice, dead code carrying a hang
- listening guide: add cs80, and reframe for the gold pass
- tr808: per-pitch tom and conga criteria, because the pooled rows excluded the reference
- ci: bump the actions group across 1 directory with 2 updates (#1)
- docs: mirror the home note from audioif
- spec: mirror audioif's patch-value rationale
- Fix #18: the pianos steal a voice instead of silently refusing the note
- Gold scrutiny: seven of nine tested golds did not survive
- Retire the eleven-phase plan: one pass over the remaining golds
- _support: replay the asym/ulab fix from audioif
- rig: the Rhodes listening prototype, with the blockers its own review found
- rig: the comparator passed on two silences - fix it, and prove it fails
- Add Phase 2 accuracy dossier for clavinet (Hohner Clavinet D6)
- Phase 1 close-out: what we achieved, and what we did not establish
- cr78: correct the record - the merge defect was CPython-only
- transitions: play the control first, halving the comparison gap
- tr808: give the cymbal its own voicing of the metal bank
- Phase 2 listening guide, with the level-matching trap closed
- Make the shared-circuit fault mechanical instead of perceptual
- Move AUDIOIF_PIN to d84470a: envelope reassignment is live on CPython
- parity: retire rebuilt instruments from the pre-rewrite oracle
- cr78: give the snare its tone oscillator, and pay for it with a 14th Note
- cr78: WIP snare rebuild - NOT MERGEABLE, preserved for review
- tr808: rebuild the METAL bank so the hats stop being filtered into silence
- Move AUDIOIF_PIN onto the fixed synthio floor
- Phase 1 complete: the last six goldens re-blessed at the phase batch listen
- phase1 evidence: clap residuals point at audioif#11, the core feature ask
- Phase 1 remainder: six drums rebuilt as fixed circuits (Station B/C)
- Phase 1 remainder: six Station A dossiers (mode v2's first batch)
- tr909, tr707, sp1200 goldens re-blessed at the batch listen
- sp1200 to gold: measured against the real pack, role map corrected
- sp1200 Station B/C: the sampler's architecture, literature-verified
- tr707 Station B/C: full ROMpler rebuild against clean captures
- tr909 Station B/C: fixed-circuit rebuild against the gold dossier
- golds run: three Station A dossiers (tr909, tr707, sp1200)
- tr808 golden re-blessed at Gate B (APPROVE ACCURACY tr808)
- tr808 Station B: fixed-circuit rebuild against the approved dossier
- accuracy: tr808 dossier - Phase 1's first, awaiting Gate A
- accuracy: measure_hits.py, the shared Station A/C measurement kit
- accuracy Phase 0: the survey, all 53 graded (M0)
- Stand the repository up around the seeded packages

# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

The first release from this repository. Brad names the version; this heading
becomes it in the release PR.

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
