# Contributing to audiocomponents

audiocomponents is `audioinstruments` and `audioeffects`, two pure-Python
packages built on [audiodsp](https://github.com/PyDevices/audiodsp)'s nodes.
A small documentation correction, a metadata improvement or a focused test for
an existing instrument or effect is a good first contribution. A new component
follows the [runtime API](docs/reference/component-api.md) and declares its
[metadata](docs/reference/metadata.md) explicitly, rather than relying on how a
neighbouring module happens to work.

## Where things are

| Path | What's there |
|---|---|
| [`lib/audioinstruments/`](lib/audioinstruments/) | One module per instrument, plus `_support.py` (the shared voice, patch and wavetable machinery) and `midi_cc.py`. |
| [`lib/audioeffects/`](lib/audioeffects/) | One module per effect, plus `_component.py` (the base every effect is built on) and `rebuilt/`, which only keeps the old `audioeffects.rebuilt.<module>` import paths working. |
| [`tools/validate_api.py`](tools/validate_api.py), [`tools/validate_metadata.py`](tools/validate_metadata.py) | The validators that enforce the runtime API and the metadata manifest. |
| `tools/` | Rendering and measurement tools besides. |
| `tests/` | The CPython suites. [`tests/parity/`](tests/parity/) holds the instrument parity harness and its goldens. |
| `docs/` | The documentation site. |
| `AUDIODSP_PIN` | The exact audiodsp release every gate runs against. |
| `VERSION` | The version the next tag carries. |
| `.github/workflows/` | CI (`tests.yml`, `lint.yml`, `docs.yml`) and the release chain. |

Each package keeps its own `pyproject.toml` under `lib/<package>/`. That is what
makes it a standalone distribution and what the MIP publisher expects, so leave
the layout alone. Each one carries the audiodsp floor,
`pydevices-audiodsp>=<release>`, the newest audiodsp *release*. The floor is not
the pin: `AUDIODSP_PIN` may name a commit ahead of it, and the gates use the pin.

## Set up

```bash
python3 -m venv .venv
.venv/bin/pip install "pydevices-audiodsp @ git+https://github.com/PyDevices/audiodsp@v0.6.9"
.venv/bin/pip install -e lib/audioinstruments -e lib/audioeffects
```

The ref after `@` is the one `AUDIODSP_PIN` names (its last line). The pin matters: with a
floating core underneath, a component failure is unattributable, because you
cannot tell a rewritten instrument from a moved node beneath it. A TestPyPI
install of `pydevices-audiodsp` is fine for poking around, but it is not what a
gate result may be reported against.

## Run the tests

CI runs the structural contract:

```bash
python -m unittest discover -s tests -p "test_*.py"
python tools/validate_api.py
python tests/parity/effects_library_smoke.py
python -m flake8
```

Most work does not need the whole suite. [`tools/scoped_tests.py`](tools/scoped_tests.py) picks the
files a change can break:

| Work | Scope |
|---|---|
| One class | `tools/scoped_tests.py class:DeEsser` (that class's tests plus the contract) |
| Kit, `__init__`, or `_component` | `tools/scoped_tests.py auto` (widens from `git diff`) |
| Every effect, no instruments | `tools/scoped_tests.py effects` |
| Shared promises only | `tools/scoped_tests.py contract` |
| Gate, integration, audit, release | `tools/scoped_tests.py full` |

`--list` prints the choice and runs nothing. Instrument tests
(`test_cpython_instruments`, `test_cpython_piano_polyphony`) run only when
`lib/audioinstruments/` or `AUDIODSP_PIN` moved, or when `full` is named.

## The instrument parity gate

It renders each component under every interpreter it can find and holds it to a
hash captured from the original micropython-vst3 script, read out of that
repository's git history at a fixed revision so the oracle cannot drift:

```bash
python3 tests/parity/run_instruments_parity.py --verify --batch all
```

It needs a MicroPython binary with audiodsp built in at `../bin/micropython`
(or pass `--micropython`) and an `mpvst` checkout beside this one (or
`--old-root`), so CI does not run it. Comparison is always within one
interpreter, because `ulab`'s vectorized sine and libm's are different
functions: two interpreters agreeing is an observation, never a gate.

Re-capturing a golden is a maintainer's decision, not a routine step. A failure
here during a deliberate rebuild is expected; it stops being a gate the moment
a golden is re-captured casually.

## Build the docs

```bash
pip install -r docs/requirements.txt
sphinx-build -W --keep-going -b html docs _site
```

`-W` fails on any warning, as Read the Docs does. The API pages under
[`docs/reference/`](docs/reference/) are generated on every build; don't edit or commit them. The
instrument and effect reference pages include [`lib/audioinstruments/README.md`](lib/audioinstruments/README.md)
and [`lib/audioeffects/README.md`](lib/audioeffects/README.md), which also go into the wheels.

## Release

The version is a maintainer's to name, in the release pull request, which
changes `VERSION` and `CHANGELOG.md`. `tag-release.yml` refuses to tag anything
that is not a release version. The chain lives in `.github/workflows/` and calls
the organization's reusable workflows:

1. `prepare-release.yml` opens the release pull request (`VERSION` and
   `CHANGELOG.md`).
2. `tag-release.yml` tags the merged `VERSION`.
3. `publish-release-packages.yml` runs the gates, builds both packages from the
   tag, publishes `pydevices-audioinstruments` and `pydevices-audioeffects` to
   TestPyPI, and requests the `audioinstruments` and `audioeffects` MIP entries.

audiodsp publishes only the core; this repository is the only source of both
component packages. Moving `AUDIODSP_PIN` is its own change, with the gates
re-run, never a side effect of other work.
