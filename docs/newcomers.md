# Newcomer's guide to audiocomponents

`audiocomponents` is PyDevices' pure-Python library of playable instruments
and audio effects. It publishes two packages:

- `audioinstruments`: 53 synthesizers, keyboards, and drum machines.
- `audioeffects`: 45 effect classes, including ready-made racks.

They run on CPython, MicroPython, and CircuitPython by building on
[`audiodsp`](https://github.com/PyDevices/audiodsp)'s audio nodes. This
repository is the shipping source for both packages. The older copies under
audiodsp are retired: do not fix, synchronize, or delete them here.

## Start by using the packages

Both distributions are published to TestPyPI:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices-audioinstruments pydevices-audioeffects
```

The current TestPyPI `0.2.0` packages predate this repository's move to the
audiodsp core, so their installed dependency is `pydevices-audioif`. The source
tree's next release instead declares `pydevices-audiodsp>=0.5.1`. That release
boundary affects contributors and release work; the public factories below are
the normal starting point for either installed package.

An instrument is created by its stable catalogue name. Effects take an audio
source, then expose their own `output`, so they chain naturally:

```python
import audioeffects
import audioinstruments

instrument = audioinstruments.create("minimoog", sample_rate=48_000)
effect = audioeffects.create(
    "TapeDelay", instrument.output, sample_rate=48_000,
)

instrument.note_on(60)
# Give effect.output to your audio sink, mixer, or next effect.
```

Your host chooses the final sink: on a board that may be `audio_out.play()`,
while a desktop host or audio pump can pull the graph itself. Keep the
component's `output` rather than reaching into its internal nodes. An effect
may rebuild its implementation after a parameter change, but its output wire
remains stable for the component's lifetime.

## The mental model

```text
your program
  |-- audioinstruments.create(name, sample_rate)
  |     `-- named module -> Instrument -> Instrument.output
  |
  `-- audioeffects.create(name, source, sample_rate)
        `-- public effect class -> effect graph -> stable effect.output
                                                   |
                                                   `-- mixer or audio sink
```

Instruments and effects share a live-component vocabulary: macros, patches,
MIDI-style control methods, state reset, `deinit()`, format properties, and
the `output` property. Instrument modules add note handling; effect modules
transform an upstream source. The complete contract, including latency, tail,
and real-time rules, is in [the runtime API](audio-component-api.md).

## Repository map

| Path | What to find there |
|---|---|
| `lib/audioinstruments/` | One module per instrument plus `_support.py` for shared voices, MIDI/event handling, and wavetable helpers. |
| `lib/audioeffects/` | Public effect classes, shared component bases, effect racks, and a small transition area for staged rewrites. |
| `docs/audio-component-api.md` | The authoritative runtime contract for all components. |
| `docs/audio-components.md` | Static provider metadata, discovery, and validation rules. |
| `docs/sequencing.md` | Frame-clocked instrument sequencing and its limits. |
| `tests/` | CPython contract and component tests. |
| `tests/parity/` | The instrument rendering parity harness and golden data. |
| `tools/` | API and metadata validators plus rendering and measurement tools. |
| `AUDIODSP_PIN` | The exact audiodsp revision used by the component gates. |

Each library has its own `pyproject.toml` inside `lib/`. That layout is
intentional: it produces two independent Python distributions and is also the
shape expected by the MIP publisher.

## How the factories work

`audioinstruments.ALL` lists module names. `audioinstruments.create()` imports
the selected module and calls its `create()` factory. Every instrument uses the
shared support layer to translate MIDI-scale input—notes, velocity, macros,
and program changes—into its `synthio` graph. Drum machines declare a
`NOTE_MAP`; the other modules are melodic instruments.

`audioeffects.ALL` is derived from the package's exported provider classes.
`audioeffects.create()` finds the class whose stable `NAME` matches the
requested effect. Its factory checks that the source exposes matching sample
rate and channel count, constructs the graph, applies an optional patch, and
returns the live component. Prefer this package factory when a host discovers
components by name; direct class construction remains useful in local code
after `audioeffects.configure()` establishes a default format.

This separation is deliberate: consumers deal in stable names and the common
contract, while the library can evolve an effect's internal graph or module
organization without changing a host integration.

## Metadata, macros, and patches

Providers declare their public shape as module or class data:

- `MACRO_LABELS` and `MACRO_MODES` describe up to 16 controls.
- `PATCHES` maps contiguous program numbers to named, MIDI-scale settings.
- `NOTE_MAP` identifies the actual voices of a drum machine.

`tools/validate_metadata.py` checks those declarations; the runtime API and
`tools/validate_api.py` check that a constructed provider implements the live
surface. Preserve these contracts when adding a component. If a host needs
finer automation, macro values may be floats even though patch values are the
0--127 MIDI grid.

## Contributor boundary

Normal users should install the published packages. For repository work,
create a virtual environment, install the `audiodsp` revision named by
`AUDIODSP_PIN`, then install both local packages editable without resolving a
different dependency version. The root [README](../README.md#developing) has
the commands and explains why the pin, rather than a floating release, makes
a test result attributable.

The portable checks are:

```bash
python -m unittest discover -s tests -p "test_*.py"
python tools/validate_api.py
python tests/parity/effects_library_smoke.py
python -m flake8
```

The full instrument parity run needs the larger PyDevices workspace and its
MicroPython build, so it is intentionally not a normal CI requirement. Read
[AGENTS.md](../AGENTS.md) before changing the pin, parity goldens, release
files, or the retired audiodsp copies; several of those actions require
maintainer decisions.

## Good first contributions

Start with a small documentation correction, metadata improvement, or focused
test for an existing provider. Then use the metadata and API validators before
broader rendering checks. A new instrument or effect should follow the common
runtime contract and provide explicit metadata, rather than relying on an
implementation detail of a neighboring module.

For deeper work, read [the runtime API](audio-component-api.md) first, then
[the metadata manifest](audio-components.md); use
[the sequencing guide](sequencing.md) when a component needs sample-clocked
musical events.
