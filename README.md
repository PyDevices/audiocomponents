# audiocomponents

The PyDevices audio component tier: **`audioinstruments`** — 53 classic
synthesizers, electromechanical keyboards and drum machines — and
**`audioeffects`** — 46 effect classes, effect racks included. Both are pure
Python built on [audioif](https://github.com/PyDevices/audioif)'s audio nodes,
and both run unchanged on CPython, MicroPython and CircuitPython.

```python
import audioinstruments, audioeffects

audioeffects.configure(48000)
minimoog = audioinstruments.create("minimoog", sample_rate=48000)
chain = audioeffects.create("TapeDelay", minimoog.output, sample_rate=48000)
```

## Status: private, and not the shipping source

This repository is **private** and **publishes nothing**. There are no
release, tag, or publication workflows here, deliberately.

`audioinstruments` and `audioeffects` still ship out of
[PyDevices/audioif](https://github.com/PyDevices/audioif), which owns the
`pydevices-audioinstruments` and `pydevices-audioeffects` distributions on
TestPyPI and the `audioinstruments`/`audioeffects` entries in the MIP index.
This repository was seeded from audioif at **v0.1.1** with the components'
own history intact, and it exists so the accuracy rewrite has a room of its
own — one where the sound of an instrument can change without a live release
chain watching.

**So there are two copies of this code, and they will drift.** That is the
point, not an accident, but it has a cost worth stating plainly:

| | audioif's copy | this copy |
|---|---|---|
| Ships to users | yes | no |
| Where bug fixes land | yes | replay them here |
| Where the rewrite happens | no | yes |

A fix made in audioif's copy has to be replayed here by hand; a change made
here reaches nobody until publishing moves. When publishing does move, the
rewiring is known and written down — audioif's publish workflow drops two
jobs and its `mip-profile`, the MIP lockfile's `repository` keys change,
micropython-vst3's `MPVST_AUDIOIF_LIB` retargets, and the org repo database
gains an entry.

## Layout

- `lib/audioinstruments/` — one module per instrument, plus `_support.py`
  (the shared voice/patch/wavetable machinery) and `midi_cc.py`
- `lib/audioeffects/` — the effect catalogue by family (`dynamics`, `eq`,
  `delay`, `reverb`, `modulation`, `drive`, `pitch`) plus `rack.py` and
  `_core.py`
- `docs/audio-component-api.md` — the runtime contract every component
  satisfies; `docs/audio-components.md` — the static metadata manifest
- `tools/validate_api.py`, `tools/validate_metadata.py` — the two validators
  that enforce those documents
- `tests/` — the CPython suites; `tests/parity/` — the instrument parity
  harness and its goldens
- `AUDIOIF_PIN` — the exact audioif release every gate runs against

Each package keeps its own `pyproject.toml` under `lib/<package>/`, which is
both what makes it a standalone distribution and what the MIP publisher
expects. Leave that layout alone.

## Developing

```bash
python3 -m venv .venv
.venv/bin/pip install "pydevices-audioif @ git+https://github.com/PyDevices/audioif@v0.1.1"
.venv/bin/pip install -e lib/audioinstruments -e lib/audioeffects
```

The pin matters. `AUDIOIF_PIN` names the audioif release the gates are read
against, for the same reason audioif pins CircuitPython in
`CIRCUITPYTHON_ORACLE`: with a floating core underneath, a component failure
is unattributable — you cannot tell a rewritten instrument from a moved node
beneath it. A local install from TestPyPI (`pip install -i
https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
pydevices-audioif`) is fine for poking around; it is not what a gate result
may be reported against.

## Testing

CI covers the structural contract, which is everything that can run without a
workspace:

```bash
python -m unittest discover -s tests -p "test_*.py"
python tools/validate_api.py
python tests/parity/effects_library_smoke.py
python -m flake8
```

The instrument parity gate is workspace-local by design. It renders each
component under every interpreter it can find and holds it to a hash captured
from the original micropython-vst3 script, read out of that repository's git
history at a fixed revision so the oracle cannot drift:

```bash
python3 tests/parity/run_instruments_parity.py --verify --batch all
```

It needs `cmods/bin/micropython` and a `micropython-vst3` checkout as siblings
in the workspace, so CI does not attempt it. Comparison is always *within* one
interpreter — `ulab`'s vectorized sine and libm's are different functions, so
two interpreters agreeing is an observation, never a gate.

**During the accuracy rewrite these goldens are the thing being changed.**
A failure there is the expected outcome of a deliberate rebuild, not a
regression — but it stops being a gate the moment it is re-captured casually.
Re-capture is a blessing, and blessings are Brad's.

## Sound stability

The API is our contract: class names, signatures, metadata, and macro surfaces
stay stable and change only deliberately. The *sound* is not part of that
contract. These components sound great, but they are not all as accurate as
they could be, and implementations will keep being refined as the library
matures — so a component may render audibly differently from one release to
the next. If a composition depends on the exact sound of a release, pin that
release rather than tracking the latest.

Beneath the components sits a harder guarantee, and it is audioif's, not
ours: the CircuitPython-compatible `synthio`/`audiocore`/effects-module core
is held bit-exact to CircuitPython itself and does not change release to
release. Where CircuitPython and audioif disagree, that is a bug and it is
reported upstream. The components are where the sound evolves; the floor they
stand on does not.

## License

MIT — see [LICENSE](LICENSE).
