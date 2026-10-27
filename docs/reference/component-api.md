# Audio component runtime API

This document defines the runtime contract for an **audio component**: an
instrument, an effect, or an effect rack. The metadata contract is documented
separately in [the metadata manifest](metadata.md).

The contract is structural. A provider does not have to inherit from an
`audiodsp` helper class, but it must expose the required attributes and methods.
The helper classes in `audioinstruments._support` and `audioeffects._component` are
implementation conveniences, not a requirement imposed on consumers.

## Construction

The package factories are the canonical consumer entry points. They discover
the provider from its stable `NAME`, construct a live component, and return it
without requiring the consumer to know the source module or class.

```python
instrument = audioinstruments.create(
    "minimoog", sample_rate=48000, channel_count=2,
    transport=transport,
)

effect = audioeffects.create(
    "Reverb", instrument.output, sample_rate=48000,
    transport=transport, character="hall",
)
```

An instrument factory has this shape:

```python
create(sample_rate, channel_count=2, transport=None, **options)
```

An effect or rack factory has this shape:

```python
create(source, sample_rate, transport=None, **options)
```

`sample_rate` is a positive integer; audiodsp v1 supports `channel_count` 1 or
2. An instrument creates audio at the requested rate and channel count. An
effect obtains its channel count from `source` and preserves it. The source
must have the requested sample rate; construction must reject a mismatch
rather than silently
resampling, downmixing, or upmixing.

`options` are provider-specific construction options. They may allocate or
select resources needed to build the graph, such as a convolution impulse
length or a fixed topology. Musical behavior that a user should change while
the component is running belongs in macros and patches instead. Options must
be portable values or explicitly documented portable services; a consumer
must not need a CPython-only object to construct a component.

An effect borrows `source`. It owns the nodes it creates, but its `deinit()`
must not deinitialize the source. This permits explicit graph teardown,
fan-out, and sharing one source between branches.

Provider-level class or module factories may remain available for local code,
but consumers use `audioinstruments.create()` and `audioeffects.create()`.
`audioinstruments.ALL` and `audioeffects.ALL` enumerate the stable names
accepted by those factories without constructing audio graphs.

## Common live component surface

Every live component provides:

```python
component.output             # audiodsp-compatible pull source
component.sample_rate        # read-only integer
component.channel_count      # read-only integer
component.latency_samples    # read-only non-negative integer
component.tail_samples       # read-only non-negative integer or None
component.capabilities       # read-only tuple of strings
component.patch_index         # integer, or None for custom macro state

component.set_macro(index, value, sample_position=0)
component.program_change(index, sample_position=0)
component.get_macro(index)
component.transport_changed()
component.reset()
component.deinit()
```

The method names are part of API v1. New optional arguments may be
added compatibly, but existing names and their basic call patterns remain
valid.

`output` is the only audio-processing interface. It is an audiodsp-compatible
pull source suitable for `audio_out.play()` and for the surrounding audiodsp
graph. Components do not exchange NumPy arrays, ulab arrays, or
runtime-specific buffers at the public boundary. A provider may use NumPy on
CPython or ulab on MicroPython/CircuitPython internally only when it supplies
the portable fallback required by the provider contract.

`sample_rate` and `channel_count` describe `output`. An effect or rack reports
the same channel count as its source. `latency_samples` is input-to-output
latency at the component's sample rate. Instruments normally report zero. A
finite effect tail is reported in samples; `None` means that the tail is
unknown or not finitely bounded. The tail counts from the end of the latency:
more than `latency_samples + tail_samples` frames after the input's last
non-zero frame, the output is exact zero. Read it after a control move: it
describes the settings in force. A rack reports the latency and tail of its
complete graph.

`capabilities` is a static tuple of ASCII strings. An empty tuple is valid.
Names describe meaningful optional behavior, for example
`"polyphonic"`, `"pitch_bend"`, `"control_change"`, `"channel_pressure"`,
`"poly_pressure"`, or `"tempo_sync"`. Capability discovery is advisory; the
optional methods remain safe to call even when a capability is absent.

Only the effects with a Sync control declare a capability, `"tempo_sync"`. No
instrument declares any, so a host cannot use discovery to find, say, a
pitch-bend-aware instrument.

### `output` is stable for the life of the component

Take it once and keep it. An effect's `output` is the same object from
construction until `deinit()`, whatever the component does to its graph in
between. Move a Mix macro to 0 and back, step through the patches, sweep a
control that rebuilds a whole section: the object a consumer is holding does
not change, and it goes on playing what the component is playing.

That is what a consumer may rely on, and it is all of it. `output` may be
held in a mixer voice, in a rack, in a `play()` call, or by a C pump pulling
the graph from another thread, for the life of the component. It may not be
assumed to be any particular node type, to be the last node the component
built, or to be identical to the source that was handed in. It is a wire, not
a node: at Mix 0 an effect bypasses its whole graph and `output` is then a
wire onto the consumer's own source rather than that source itself.

Where the node is wanted instead of the wire — a `reset()` that must not
rewind a borrowed source, or a class appending one more stage to its own
graph — `audioeffects._component.port_target(output)` returns what the wire
is playing.

**A class appends a stage to `port_target(self._output)`, never to
`self._output`.** Wrapping the wire and assigning the wrapper points the wire
at something that reads the wire, and a pull on that never returns. On CPython
it is refused with a `ValueError` naming `port_target`. On a native build the
check has nothing to read and the loop is built, so the rule is the protection
there.

Underneath, an effect ends in an `audioroute.Port` — a zero-copy pass-through
whose `play()` re-points it — and `Component._output` is a property that
builds one on the first assignment and re-points it on every one after
([`lib/audioeffects/_component.py`](../../lib/audioeffects/_component.py)). A class author writes `self._output =
node` exactly as before. The port moves no bytes: it hands back its source's
own buffer, length and result.

**Instruments have no port**, and neither does a rack. An instrument's graph
is fixed at construction, so `Instrument.output` is the node itself and always
was — stable because nothing re-points it, not because anything guarantees it.
A rack's output is its last child's, which is already a stable one, and an
empty rack is a wire, so its output is the source it was handed.

**On an interpreter with no `audioroute.Port` the promise does not hold.** A
stock CircuitPython board has no `audioroute`, and no C pump either; there
`_component.PORT` is `None`, `output` is the node at the end of the graph, and
it changes identity when the component re-points it, exactly as it did before
ports existed. A consumer that takes `output` once and keeps it across a Mix
move stops hearing that effect. `TIER` and `REQUIRES` do not change for this —
a class does not *need* `audioroute`, it degrades — so a host that must work
on both reads `output` after any control change, or checks `_component.PORT`.

## MIDI and control methods

All public control values use MIDI-native units:

| Value | API range/unit |
| --- | --- |
| note pitch | integer `0..127` |
| velocity | `0..127` |
| channel | integer `0..15` |
| controller and CC value | integer `0..127` |
| macro value | `0..127`; fractional values may be accepted for fine automation |
| channel/poly pressure | `0..127` |
| pitch bend | unsigned `0..16383`, center `8192` |
| program/patch index | non-negative integer |
| detune | floating-point semitones |
| sample position | non-negative frame offset |

An instrument provides these required methods:

```python
note_on(pitch, velocity=127, detune=0.0, channel=0, note_id=-1,
        sample_position=0)
note_off(pitch, channel=0, note_id=-1, sample_position=0)
all_notes_off()
```

and says how many notes it can sound at once:

```python
instrument.voices    # 1 for a monophonic instrument, its voice limit
                     # otherwise, or None for a drum machine (voices per pad)
```

A note past the limit takes a sounding note's voice, so a part that overlaps
itself wants an instrument whose `voices` covers the overlap. A SoundFont
instrument's count is its pool's `voice_count`, which can be set lower while
it plays, and higher up to the voices the pool's sampler was made with.

It also provides the optional MIDI methods below. They are present as safe
no-ops when the instrument does not use a message:

```python
pitch_bend(value, channel=0, sample_position=0)
control_change(controller, value, channel=0, sample_position=0)
channel_pressure(value, channel=0, sample_position=0)
poly_pressure(pitch, value, channel=0, note_id=-1, sample_position=0)
```

Effects and racks never receive notes. They provide the same non-note control
methods as safe no-ops or meaningful handlers, plus the common macro and
program methods. `set_macro()` is the stable control surface. The API does
not assign MIDI CC numbers to macro indices; a host, sequencer, or controller
maps CCs explicitly. `midi_cc.py` may convert between normalized values and
MIDI values, but it does not define a hidden CC-to-macro map.

`detune` is a pitch offset in semitones and is not a controller value. A note
with velocity zero is equivalent to `note_off()`.

**Playing from MIDI.** These are component *methods*; to drive them from
MIDI itself, put `audioinstruments.midi_dispatch.MidiDispatcher` in front.
It takes raw bytes (running status included), `adafruit_midi` message
objects, or one message at a time as a status byte and its data, and calls
the methods above on the instrument each channel is routed to, passing the
channel so note identity is `(channel, pitch)`. A velocity-0 note-on is a
note-off, Control Change 120 and 123 call `all_notes_off()`, and every other
controller reaches `control_change()` as it is. Channel 9 (General MIDI's
channel 10) goes to a drum kit when you give one. `read_midi_file()` turns
a Standard MIDI File into timed events for it. The module docstring has
the routing calls and an example: [midi_dispatch.py](https://github.com/PyDevices/audiocomponents/blob/main/lib/audioinstruments/midi_dispatch.py).

Notes are identified by `(channel, note_id)` when `note_id >= 0`. If no note
ID is supplied (`note_id == -1`), the identity is `(channel, pitch)`. A note
off releases only the matching identity, allowing overlapping same-pitch
notes when a host supplies note IDs.

Macros are global component state. Channel and note identifiers carried with a
macro event are context, not a request for per-channel or per-note macro
storage. Program changes are also global to one live component instance.

`sample_position` is a frame offset within the current render/event interval.
Zero means the first frame. Providers must honor non-zero positions rather
than interpreting them as seconds; an adapter may establish the current
interval and schedule the event at that frame. Callers that do not schedule
within a block use the default zero.

### Scheduling a note at a frame

`sample_position` places an event inside the block a host is *about to*
render. It cannot say "a bar from now", because nobody has rendered that bar
yet. That is what these three are for, and they are separate from it:

```python
inst.schedulable                     # can this instrument take a frame?
with inst.scheduled(queue, frame) as tokens:
    inst.note_on(36, 127)            # heard at `frame`, not now
inst.at(queue, frame).note_on(38, 90)
```

Inside the block, the instrument does **all** of its usual Python on the
calling thread — validating, tracking held keys, building notes — and only
its final presses and releases go on `queue`, which is an
`audiopump.Events`. `tokens` collects one token per event in schedule order;
a `0` is an event a full queue refused.

Schedule in time order, and schedule a note-off with every note-on: the
instrument's own bookkeeping is updated at schedule time, so a note-off
written before its note-on finds nothing to release, and a live press of a
key the queue is still holding can leave a scheduled note sounding forever.

`schedulable` is `False` when an instrument's note-on reaches the audio by
some route other than a press — a modal bank retuned in place. Those
instruments still play live. `audioinstruments.sequencer.Sequencer` refuses
one rather than playing its part early.

Writing a part against this, and the two traps that cost a run: the
[sequencing guide](../guides/sequence-a-part.md).

## Macro and patch state

`get_macro(index)` returns the current public macro value in MIDI units. The
value may be fractional even though patch declarations use integer MIDI
values. An invalid macro index raises `IndexError`.

A macro value off the 0-127 range is clamped, never refused: below 0, minus
infinity and NaN set the macro's bottom stop, and above 127 and plus infinity
its top stop. `get_macro()` then reads back 0 or 127, and the component plays
exactly what `set_macro(index, 0)` or `set_macro(index, 127)` plays.

Construction applies patch `0` automatically. A fresh component and a fresh
component followed by `program_change(0)` have the same observable state.
`program_change(index)` applies a known patch and safely ignores an unknown
index. Applying a patch sets `patch_index` to that index. Changing any macro
manually sets `patch_index` to `None`, meaning custom state.

`reset()` releases all instrument notes, clears component DSP history, and
restores patch `0`. It leaves the component constructed and ready for use.

### After a reset, a rejoin or a control move

A few effects do not come back to exactly where an untouched copy of the
same effect is, and none of it is a fault. If you compare one against a
twin that never saw the event, expect these differences.

**Free-running phase.** `Chorus`, `Phaser`, `Tremolo` and `Vibrato` run an
LFO that `reset()` or `reset_buffer()` restarts, and that a Rate, Sync or
patch change moves. `Bitcrusher` does the same with its sample-and-hold
count and dither tables, restarted by a reset or a move of Rate, Dither,
Band Limit or Mix. The sound is the same, but a fresh pass starts at a
different point in its cycle, so a copy that took the event never lines up
sample for sample with one that did not.

**Detector and coupling state.** `tail_samples` bounds the output once the
input is silent; it does not bound the effect's internal state. After a
reset, a rejoin or a control move, the level detectors and coupling filters
of `Compressor`, `DynamicEQ`, `MultibandCompressor`, `DeEsser`,
`CombFilter`, `Exciter`, `Fuzz`, `Overdrive` and `Distortion` can take
longer to settle than the tail says. The worst measured differences from a
freshly built instance are `Compressor` up to 1,575 LSB for 20 to 50 blocks
after a Mix move, `DynamicEQ` about 1,000 LSB for 18 to 27 blocks,
`MultibandCompressor` under 16 LSB within three blocks, and `DeEsser` up to
20 LSB for one block after a reset. `CombFilter` stays within 1 LSB of its
tail and `Exciter` carries about 1 LSB of float residue. `Overdrive` carries a
few LSB after a control move and about 43 LSB that persists after a reset.
`Fuzz` keeps 200 to 300 LSB that persists, and `Distortion` up to about
800 LSB of slow coupling-pole residue that persists. What you hear is a
re-attack, the same as switching a pedal on.

After a patch change, `Compressor` can be 10,000 to 13,000 LSB from an
untouched copy for up to about 110 blocks while its detector re-attacks,
because the characters a patch moves between have releases of up to two
seconds. A reset in the middle of a source buffer is the same as one on a
block boundary.

**Behaviours that are not a bypass.** Three are stated, not accidental:

- `Fuzz` takes its lean shaper from the selected patch, not from the
  macros. After `program_change(8)`, moving the macros back stays lean;
  only another `program_change()` leaves it. At patch 2 with Bias at -0.85
  it also puts 6 to 9 LSB out of silence, inside its stated 16 LSB wander.
- `DynamicEQ` with Listen on outputs the detector's own band, so Listen is
  not a bypass, and `Mix` 0 only bypasses with Listen off.
- `Exciter` multiplies Output into the result at every Mix, so Mix 0 is an
  exact bypass only at 0 dB Output.

`deinit()` releases resources owned by the component but not a borrowed effect
source. It is idempotent. After the first deinitialization, further use raises
a clear `RuntimeError` (or the equivalent runtime-specific error), except that
calling `deinit()` again remains safe.

## Timing, transport, and real-time behavior

`transport` is an optional callable shared by instruments, effects, and racks.
It returns:

```python
(playing, position_seconds, bpm,
 time_signature_numerator, time_signature_denominator)
```

When omitted, the component sees `(False, 0.0, 120.0, 4, 4)`. Components may
ignore transport. A tempo-aware component advertises `"tempo_sync"`.

A component reads the transport when it needs a reading, never while its
output is pulled. Call `transport_changed()` when the tempo may have moved,
and a synced component reads the transport again and follows it; without the
call it keeps the tempo it last read until a control moves. The call is
cheap enough to make once a block: with Sync off it reads nothing, and with
the tempo unchanged it reads the transport once and returns. A component
that does not sync to tempo takes the call and does nothing, and a rack
passes it to its children.

```python
for block in host_blocks():
    effect.transport_changed()
    audio_out.write(effect.output)
```

The effects with a Sync control consume the transport: the delays
(`DigitalDelay`, `TapeDelay`, `AnalogDelay`, `PingPongDelay`,
`MultiTapDelay`), `Flanger`, `Phaser`, `AutoPan` and `Tremolo`. No instrument
syncs to tempo.

Construction may allocate the complete graph and bounded resources. Pulling
from `output` must not allocate, block, perform I/O, or depend on garbage
collection. Event methods may update state and perform bounded voice work, but
must not allocate unbounded storage. Any fixed resource or voice limit must be
bounded by construction or explicitly enforced.

## Component kinds

An instrument has MIDI input and audio output. It has no audio source input.
An effect has audio source input and audio output and uses MIDI only for
control. An effect rack has exactly the effect shape even when its internal
graph contains serial, parallel, or mixed effects. Racks may contain and be
used by other racks.

Rack providers ship in [`lib/audioeffects/`](https://github.com/PyDevices/audiocomponents/tree/main/lib/audioeffects)
(`rack.py`, `shimmerhall.py`, `airspace.py`).
`Rack` is the generic mechanism — a serial chain of the package's own
effects described by portable literals
(`create("Rack", source, rate, chain=(("Reverb", {"character": "hall"}),))`) —
and `ShimmerHall` and `AirSpace` are fixed-topology racks with a macro
surface over their children. A rack is one more `audioeffects` provider: it is
discovered through `audioeffects.ALL`, constructed by
`audioeffects.create()`, and reports its complete graph's latency
(children summed) and tail (`None` as soon as any child's is unbounded).

The provider metadata rules remain authoritative for classification and
catalog presentation: a `NOTE_MAP` identifies a percussion instrument, while
the runtime API identifies behavior through its kind and capabilities.
