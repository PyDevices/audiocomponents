# Keep an effect's output wire

Take an effect's `output` once, wire it anywhere (a mixer voice, a rack,
`audio_out.play()`, a C pump pulling the graph from another thread) and every
later control move is heard, including Mix from zero:

```python
fx = audioeffects.create("Overdrive", source, 48000)
mixer.voice[0].play(fx.output)      # take it once

fx.set_macro(fx.MACRO_LABELS.index("Mix"), 127)   # and now you hear it
fx.program_change(3)                              # and now you hear that
```

About twenty effect classes rebuild part of their graph when a control crosses a
threshold: a Phaser changing its number of stages, a Distortion rebuilding the
whole thing. They do not hand out a new node afterwards. An effect ends in a
wire that gets re-pointed rather than replaced, so the `output` object never
changes.

Two things follow from it being a wire and not a node. It is not the last
node the class built, and at Mix 0 it is a wire onto the source you handed in
rather than that source itself.

Instruments and racks have no wire: an instrument's `output` is its node, and a
rack's is its last child's, which is already stable.

## Where it does not hold

On an interpreter with no `audioroute.Port` the promise does not hold. A stock
CircuitPython board has no `audioroute`, and no C pump either. There `output`
is the node at the end of the graph and it changes when the effect re-points it.
A program that must work on both reads `output` again after any control change.
The contract, with the reasons, is in
[the runtime API](../reference/component-api.md#output-is-stable-for-the-life-of-the-component).
