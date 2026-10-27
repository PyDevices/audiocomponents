# How it works

audiocomponents is a pure-Python library of playable instruments and audio
effects, published as two packages:

- `audioinstruments`: 55 synthesizers, keyboards and drum machines.
- `audioeffects`: 45 effect classes, including ready-made racks.

They run on CPython, MicroPython and CircuitPython by building on
[audiodsp](https://github.com/PyDevices/audiodsp)'s audio nodes. If you have
not run one yet, start with [Install](../get-started/install.md) and
[Your first program](../get-started/first-program.md).

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
MIDI-style control methods, state reset, `deinit()`, format properties and
the `output` property. Instrument modules add note handling; effect modules
transform an upstream source. The complete contract, including latency, tail
and real-time rules, is in [the runtime API](../reference/component-api.md).

Your host chooses the final sink: on a board that may be `audio_out.play()`,
while a desktop host or audio pump can pull the graph itself. Keep the
component's `output` rather than reaching into its internal nodes. An effect
may rebuild its implementation after a parameter change, but its output wire
stays the same for the component's lifetime
([why](../reference/component-api.md#output-is-stable-for-the-life-of-the-component)).

## How the factories work

`audioinstruments.ALL` lists module names. `audioinstruments.create()` imports
the selected module and calls its `create()` factory. Every instrument uses the
shared support layer to translate MIDI-scale input (notes, velocity, macros
and program changes) into its `synthio` graph. Drum machines declare a
`NOTE_MAP`; the other modules are melodic instruments.

`audioeffects.ALL` is derived from the package's exported provider classes.
`audioeffects.create()` finds the class whose stable `NAME` matches the
requested effect. Its factory checks that the source exposes a matching sample
rate and channel count, constructs the graph, applies an optional patch, and
returns the live component. Prefer this package factory when a host discovers
components by name; constructing a class directly remains useful in local code
after `audioeffects.configure()` records a default format.

This separation is deliberate: consumers deal in stable names and the common
contract, while the library can change an effect's internal graph or module
organization without changing a host integration.

## Metadata, macros and patches

Providers declare their public shape as module or class data:

- `MACRO_LABELS` and `MACRO_MODES` describe up to 16 controls.
- `PATCHES` maps contiguous program numbers to named, MIDI-scale settings.
- `NOTE_MAP` identifies the actual voices of a drum machine, and `PAD_MAP`
  says what each pad key from 36 to 51 plays on it.

[`tools/validate_metadata.py`](../../tools/validate_metadata.py) checks those declarations; the runtime API and
[`tools/validate_api.py`](../../tools/validate_api.py) check that a constructed provider implements the live
surface. If a host needs finer automation, macro values may be floats even
though patch values are the 0-127 MIDI grid. The declarations are specified in
[the metadata manifest](../reference/metadata.md).

## Pages in this section

- [Sound stability](sound-stability.md)
- [Smoothing control moves](control-smoothing.md)
- [How accurate a scheduled part is](sequencing-accuracy.md)

```{toctree}
:hidden:

sound-stability
control-smoothing
sequencing-accuracy
```
