# AGENTS.md — audiocomponents

`audioinstruments` (53 instruments) and `audioeffects` (46 effect classes,
racks included): the pure-Python audio component tier that PyDevices owns,
built on [audioif](https://github.com/PyDevices/audioif)'s nodes. Private
repository. **Nothing here publishes.**

## Read this before you change anything

This code exists in two places. audioif still carries `lib/audioinstruments/`
and `lib/audioeffects/`, and **audioif's copy is the one that ships** —
TestPyPI, the MIP index, every downstream consumer. This repository is the
rewrite room.

Three rules follow from that, and they are the whole reason this file leads
with them:

1. **A user-visible bug fix belongs in audioif first.** Fixing it only here
   fixes it for nobody. Fix it there, then replay it here.
2. **A rewrite belongs here and only here.** Do not push accuracy work back
   into audioif's copy; that copy's job is to keep sounding exactly as it did
   until publishing moves.
3. **Never delete audioif's copies.** The split is deliberately incomplete.
   Removing them is a separate decision, Brad's, taken when publishing moves.

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
  `pyproject.toml`'s `project.urls` still point at audioif, correctly — that
  is where these distributions come from today.
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

## What is not here

- No release, tag, or publication workflow. Adding one is not a cleanup task.
- No `VERSION` file. These packages have no release identity of their own yet;
  a local editable install reports `0.0.0`, which is cosmetic and matches
  audioif's behaviour today.
- No C. The native nodes these components call live in audioif; if a fix needs
  to go below the Python, it goes there.
