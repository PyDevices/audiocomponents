# AGENTS.md — audiocomponents

`audioinstruments` (55 instruments) and `audioeffects` (45 effect classes,
racks included): the pure-Python audio component tier that PyDevices owns,
built on [audiodsp](https://github.com/PyDevices/audiodsp)'s nodes. **This
repository publishes both** — `pydevices-audioinstruments` and
`pydevices-audioeffects` on TestPyPI, and the `audioinstruments` and
`audioeffects` entries in the MIP index. audiodsp publishes the core only.

## Read this before you change anything

This is the only home of both packages. audiodsp's pre-rewrite copy of
`lib/audioinstruments/` and `lib/audioeffects/` was deleted on 2026-09-03
([#2](https://github.com/PyDevices/audiocomponents/issues/2)), so every bug
fix and every piece of accuracy work belongs here.

## The floor is pinned

`AUDIODSP_PIN` names the exact audiodsp release every gate here runs against.
It is the same discipline as audiodsp's own `CIRCUITPYTHON_ORACLE`, for the
same reason: with a floating core underneath, a component failure is
unattributable — you cannot tell a rewritten instrument from a moved node
beneath it. Moving the pin is its own change, with the gates re-run, never a
side effect of other work.

## Layout

- `lib/<package>/` — the packages, each with its own `pyproject.toml`. That
  layout is load-bearing twice over: it is what makes each a standalone
  distribution, and the MIP publisher expects `<repo>/lib/<package>`.
  `pyproject.toml`'s `project.urls` point here, and its `dependencies` carry
  the audiodsp floor, `pydevices-audiodsp>=<release>` — the newest audiodsp
  *release*. That is not the pin: `AUDIODSP_PIN` may name a commit ahead of
  the floor, and the gates use the pin.
- `docs/audio-component-api.md` — the runtime contract (construction,
  methods, properties). `docs/audio-components.md` — the static metadata
  manifest. `tools/validate_api.py` and `tools/validate_metadata.py` enforce
  them, and the tests import the latter.
- `tests/parity/` — the instrument parity harness, its probes and goldens.

## Gates

What CI runs, and what you should run before committing:

```bash
python -m unittest discover -s tests -p "test_*.py"
python tools/validate_api.py
python tests/parity/effects_library_smoke.py
python -m flake8
```

`.flake8` selects defect checks only (`F,E9,W6`) — no layout rules. The
instrument modules are deliberately compact and generated modules put
`MACRO_LABELS` above their imports; gating layout here would be a fight with
the house style, not a check.

The heavier gates are workspace-local:

```bash
python3 tests/parity/run_instruments_parity.py --verify --batch all
MICROPYPATH=$PWD:$PWD/lib ../bin/micropython \
    tests/parity/scheduling_seam_live.py
```

The second is the scheduling seam against the **real** pump
(audiocomponents#92). `tests/test_scheduling_seam.py` proves which events
the seam writes, against a Python stand-in for `audiopump_events.c`, and
runs anywhere; this one asks what was *heard*, off `audiopump.Tap`, with
the loop advanced by `audiopump.service()` on the calling thread. It needs
a MicroPython build carrying audiodsp as a usermod, because `audiopump`
exists only where the pump does. Four cases, each with a planted fault that
must make it exit non-zero: `--fault early|flat|held|armed`.

It renders each component under every interpreter it finds and holds it to a
hash captured from the original micropython-vst3 script — read out of that
repository's **git history** at `ac87f13`, not its working tree, because its
tree imports these packages now and would no longer be an independent oracle.
Needs `../bin/micropython` (or `--micropython`) and an `mpvst` checkout beside this one (or `--old-root`).
Comparison is always within one interpreter; cross-interpreter agreement is
recorded as an observation, never enforced.

**`--capture-old` cannot absorb a deliberate change.** It re-reads
micropython-vst3 at the fixed revision `ac87f13`, so re-running it rewrites the
same hashes. An instrument whose sound was changed on purpose will never match
that oracle again.

**Changing an instrument's sound on purpose.** Instruments are tuned by ear, by
whoever is playing them: change the voice, play it, keep it or don't. When a
change is kept, the same commit names the instrument in `REBUILT` in
`tests/parity/run_instruments_parity.py`, with the date, and `--verify` then
reports it as `rebuilt` instead of failing. No separate ruling, dossier or
re-capture is needed. Everything not named there is still held to the old
oracle exactly as before, because the gate's job is to catch sound that changes
by accident: a refactor, a moved node, an audiodsp bump. `--include-rebuilt`
compares the rebuilt ones anyway.

What stays mechanical for a kept change is only breakage: the instrument still
plays, isn't silent, doesn't clip, and still runs in real time on a board.

## The release chain

- `prepare-release.yml` opens the release PR (`VERSION` + `CHANGELOG.md`);
  `tag-release.yml` tags the merged `VERSION`; `publish-release-packages.yml`
  runs the gates above against the pin, builds both packages from the tag
  (`working-directory: lib/<package>`), publishes them to TestPyPI, and
  requests the two MIP index entries (`mip-profile:
  audioinstruments,audioeffects`, on one call — mip serializes them).
- **Versions are the maintainer's to name.** An agent never edits `VERSION`,
  never tags, never dispatches a workflow. `VERSION` holds a placeholder until
  the maintainer names the release, and `tag-release.yml` refuses to tag anything that is
  not a release version, so the placeholder cannot leak into a tag.
- The two packages version and release together. A local editable install
  reports `0.0.0` because the build workflow writes `lib/<package>/VERSION`
  at build time; that is cosmetic.

## What is not here

- No C. The native nodes these components call live in audiodsp; if a fix needs
  to go below the Python, it goes there.
