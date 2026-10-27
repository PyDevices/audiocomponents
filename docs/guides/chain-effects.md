# Chain effects

Every effect takes a source and has an `output`, so one effect's `output` is
the next one's source. This chain compresses an electric piano, puts a tape
delay behind it and a hall reverb behind that:

```python
import audioeffects
import audioinstruments

RATE = 48000
synth = audioinstruments.create("rhodes", sample_rate=RATE)
comp = audioeffects.create("Compressor", synth.output, RATE,
                           threshold_db=-20, ratio=3, character="optical")
tape = audioeffects.create("TapeDelay", comp.output, RATE,
                           time_ms=340, feedback=0.4, mix=0.25)
hall = audioeffects.create("Reverb", tape.output, RATE,
                           character="hall", mix=0.3)
audio_out.play(hall.output)    # or pull hall.output yourself
```

Keyword arguments after the sample rate are the effect's construction options.
Each class's module docstring lists its controls and limits, and the
[effects reference](../reference/effects.md) groups the classes by what they do.

Ask the end of the chain how much it adds: `hall.latency_samples` is how late
the output arrives behind the input, and `hall.tail_samples` is how long the
sound goes on after the input stops (`None` means no bound).

## As a rack

A rack is one component with the shape of a single effect, however many
effects sit inside it. `Rack` takes a `chain` of effect names, or
`(name, options)` pairs, in the order the signal passes through them:

```python
rack = audioeffects.create("Rack", synth.output, RATE, chain=(
    ("Compressor", {"threshold_db": -20, "ratio": 3}),
    ("TapeDelay", {"time_ms": 340, "mix": 0.25}),
    ("Reverb", {"character": "hall", "mix": 0.3}),
))
```

The chain is plain data, so a host can store a rack as a literal. Racks nest:
an entry may itself be `("Rack", {"chain": (...)})`. A rack owns its children
and borrows the source. Its latency is the children's summed, its tail is
`None` as soon as any child's is unbounded, and `reset()` clears every child's
history. `ShimmerHall` and `AirSpace` are fixed racks whose macros move their
children's controls.

## After an effect that ends in a mixer

Several effects end in an `audiomixer.Mixer`, because they split into parallel
branches and sum them. On MicroPython and on a desktop you can chain freely
after one. On stock CircuitPython you cannot: its Mixer stops its voices when
it is reset, and every effect resets its source when you `play()` it, so the
chain goes silent. audiodsp's builds fix that. The
[effects reference](../reference/effects.md) has the details under "A note on
chaining after a Mixer".
