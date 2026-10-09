# The lifecycle matrix

`lifecycle.py` runs one fixed set of lifecycle events on an effect class and
judges every cell by the same properties, with no model in the loop. It
replaces hunting for the same defects class by class: audio lost across a
reset, a stale block when a control comes back, a tail that outlasts
`tail_samples`, a source that runs dry, source buffers that are not 256
frames, two moves before one pull.

To run it on one class (CPython, or a native binary with
`MICROPYPATH=lib:tests/support`), from the repo root:

    python tests/support/lifecycle.py DigitalDelay
    python tests/support/lifecycle.py DigitalDelay --events=E1,E5
    python tests/support/lifecycle.py MultiTapDelay --quick

It prints one line per cell, `class|event|rate|channels|patch|P1:..|...|h:..`,
and a `SUMMARY` line per class: cells run, cells with any red property,
declared exceptions. `tests/test_lifecycle_matrix.py` runs it on every Phase 5
class on the branch, on CPython and both native interpreters, and holds the
red cells to its `KNOWN_RED` table.

## The grid

Every event runs at 48 000 and 22 050 Hz, stereo and mono, at the
constructor defaults (`d`) and at every shipped patch. `--quick` keeps the
full event list at the defaults and runs the patch configurations on the
events that do not multiply by the macro count (no E4, E10-macros or E11,
and E6 only to patch 0 and the last patch). The material is deterministic
and identical on every interpreter: a click train whose clicks each have
their own amplitude (the second channel another), an LCG noise burst, and an
integer triangle for P5.

## Events

The move lands before pull 12 (mid-stream), and "and back" comes 2 pulls
later (6 for Mix).

- **E1** `reset()`, with 256-frame source buffers (on a block boundary) and
  100-frame buffers (part-way through one).
- **E2** the host's `audiocore.reset_buffer(effect.output)`.
- **E3** `deinit()`: the source still renders, every public method and
  property raises, a second `deinit()` is harmless.
- **E4** each macro to each stop (0 and 127; and 64 for a bipolar one) and
  back.
- **E5** Mix (the class's wet/dry control) to 0 and back.
- **E6** `program_change` to each other patch and back.
- **E8** the source ends part-way through a block (`E8-end`). A native
  source can only run dry by handing back an empty buffer with
  `GET_BUFFER_DONE`, so that is what the matrix does, through an
  `audioroute.Port` it re-points. Since audiodsp#213 a node takes that as
  the source's end, lets go of it and rings out on silence, so a dry spell
  that carries on afterwards cannot be told from an end; the `E8-dry` event
  that tried is retired.
- **E9** source buffers of 256, 100, 512 and 1000 frames and one whole
  RawSample: P1 is Mix 0 all along; the other properties use the E5 move.
- **E10** reset, every macro to 127 and back, Mix to 0 and back, a patch
  change and back, all before the first pull.
- **E11** two macro moves; a Mix move and a patch change; two patch changes;
  three moves; all before one pull, back later.

"Back" is `program_change(patch)` at a patch, and `set_macro` with the
values `get_macro` read at the defaults (landed exactly where that
round trip is not bit-exact).

## Properties

Each is judged against a control instance that never met the event, fed the
same material. A reset returns a class to patch 0, so E1's control is built
at patch 0.

- **P1** At Mix 0 the output is the source, byte for byte, on time (shifted
  by `latency_samples`). Events that do not move Mix take Mix back to 0 in
  the same gap; E5 is judged over the stretch it holds Mix at 0. After
  `E8-end` the output is the frames the source handed, then silence.
- **P2** Silence in gives silence out: after the event and `tail_samples`
  (read after it) + `latency_samples` + one block + the last source buffer,
  every sample is exactly 0 for 2048 frames.
- **P3** Nothing plays out of silence: the move away as the input stops, a
  wait until the output is exactly silent, the move back; the next four
  blocks are exactly 0. A single action is taken in the silence instead.
- **P4** From `tail_samples + latency_samples + one block` after the last
  move on, the output is byte-identical to the control's, over 2048 frames
  of material.
- **P5** No step within one block of the move larger than 1.5 x the larger
  of the triangle's own largest step and the control's. Control moves only
  (E4, E5, E6, E9, E11): a reset, a deinit and a source fault are cuts by
  definition, and E10 has nothing before it.
- **P6** The three interpreters print identical lines for every cell. Each
  line carries `h:`, a CRC-32 of the event instance's whole render, so P6
  compares bytes, not only verdicts.
- **PD** E3's surface check.

A verdict is `ok`, `na(...)` (the property does not apply to that cell,
said why: `tail None`, a whole RawSample, a class that never falls silent),
`RED(...)` with what was measured, or `decl`.

## Declaring an exception

A class that cannot satisfy a property by design (a glide, a reverb tail, a
free-running LFO) adds a row to `DECLARED` in `lifecycle.py`:

    DECLARED = {
        ("TapeDelay", "E1-", "P4"): "wow and flutter run free across a reset",
    }

The key is (class `NAME`, event name prefix, property); the cell then prints
`decl` and counts as a declared exception. Nothing else skips a cell. The
test file's `KNOWN_RED` is different: it records what is red today, as
findings, one row per (class, event prefix, property) with the number and a
digest of its red cells, so the suite goes red when a cell changes either
way. The test runs the quick matrix; `LIFECYCLE_FULL=1` runs the full one,
and `LIFECYCLE_CLASSES=DigitalDelay,TapeDelay` limits it to some classes.

## The plants

The helper ships a control and a planted fault for every property, and
`TestPlants` holds each plant red on its cell with its control green there:
`DropOnReset` (P1), `HoldDC` (P2), `StaleMix` against `Routed` (P3),
`LateMove` (P4), `HardSwitch` (P5), `BusyDeinit` (PD) and `ImplPlant`
(P6, a level a hair different off CPython).
