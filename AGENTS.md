# AGENTS.md — audiocomponents

`audioinstruments` (53 instruments) and `audioeffects` (46 effect classes,
racks included): the pure-Python audio component tier that PyDevices owns,
built on [audioif](https://github.com/PyDevices/audioif)'s nodes. **This
repository publishes both** — `pydevices-audioinstruments` and
`pydevices-audioeffects` on TestPyPI, and the `audioinstruments` and
`audioeffects` entries in the MIP index. audioif publishes the core only.

## Read this before you change anything

This is the canonical home of both packages and the one that ships. audioif
still carries a pre-rewrite copy of `lib/audioinstruments/` and
`lib/audioeffects/`; that copy is retired. Nothing ships from it, nothing is
gated against it, and no fix belongs in it.

Three rules follow from that, and they are the whole reason this file leads
with them:

1. **A bug fix belongs here.** Fixing it in audioif's copy fixes it for
   nobody.
2. **Accuracy work belongs here.** Do not push it into audioif's copy.
3. **Leave audioif's copies to Brad.** Deleting them, and replaying anything
   from them into this copy, are his decisions, taken with a diff in front
   of him — tracked in
   [#2](https://github.com/PyDevices/audiocomponents/issues/2). Never
   delete or sync them yourself.

## The floor is pinned

`AUDIOIF_PIN` names the exact audioif release every gate here runs against.
It is the same discipline as audioif's own `CIRCUITPYTHON_ORACLE`, for the
same reason: with a floating core underneath, a component failure is
unattributable — you cannot tell a rewritten instrument from a moved node
beneath it. Moving the pin is its own change, with the gates re-run, never a
side effect of other work.

## Layout

- `lib/<package>/` — the packages, each with its own `pyproject.toml`. That
  layout is load-bearing twice over: it is what makes each a standalone
  distribution, and the MIP publisher expects `<repo>/lib/<package>`.
  `pyproject.toml`'s `project.urls` point here, and its `dependencies` carry
  the audioif floor, `pydevices-audioif>=<release>` — the newest audioif
  *release*. That is not the pin: `AUDIOIF_PIN` may name a commit ahead of
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

The heavier gate is workspace-local:

```bash
python3 tests/parity/run_instruments_parity.py --verify --batch all
```

It renders each component under every interpreter it finds and holds it to a
hash captured from the original micropython-vst3 script — read out of that
repository's **git history** at `ac87f13`, not its working tree, because its
tree imports these packages now and would no longer be an independent oracle.
Needs `cmods/bin/micropython` and a `micropython-vst3` checkout as siblings.
Comparison is always within one interpreter; cross-interpreter agreement is
recorded as an observation, never enforced.

**`--capture-old` cannot absorb an accuracy rebuild, and never could.** It
re-reads micropython-vst3 at the fixed revision `ac87f13`, so re-running it
rewrites the same hashes. An instrument the accuracy program has deliberately
rebuilt against hardware references will never match that oracle again — this
paragraph used to claim re-capturing was "how the accuracy rewrite is supposed
to move", which was wrong and left 14 of 20 drums comparisons red with no
operation that could clear them.

**Rebuilt instruments are retired from this gate instead.** They are named in
`REBUILT` in `tests/parity/run_instruments_parity.py`, with the phase and the
date their sound was blessed, and `--verify` reports them as `rebuilt` and
excludes them from the failure count. Everything not named there is still held
to the old oracle exactly as before; `--include-rebuilt` compares them anyway.

**Adding a name to `REBUILT` is a re-blessing, and it is Brad's call every
time, never an agent's.**

## The release chain

- `prepare-release.yml` opens the release PR (`VERSION` + `CHANGELOG.md`);
  `tag-release.yml` tags the merged `VERSION`; `publish-release-packages.yml`
  runs the gates above against the pin, builds both packages from the tag
  (`working-directory: lib/<package>`), publishes them to TestPyPI, and
  requests the two MIP index entries (`mip-profile:
  audioinstruments,audioeffects`, on one call — mip serializes them).
- **Versions are Brad's to name.** An agent never edits `VERSION`, never
  tags, never dispatches a workflow. `VERSION` holds a placeholder until he
  names the release, and `tag-release.yml` refuses to tag anything that is
  not a release version, so the placeholder cannot leak into a tag.
- The two packages version and release together. A local editable install
  reports `0.0.0` because the build workflow writes `lib/<package>/VERSION`
  at build time; that is cosmetic.

## What is not here

- No C. The native nodes these components call live in audioif; if a fix needs
  to go below the Python, it goes there.
