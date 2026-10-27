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
and cells with any declared property (a cell with two declared properties
counts once). [`tests/test_lifecycle_matrix.py`](../test_lifecycle_matrix.py) runs it on every class the
package serves (`audioeffects.ALL`), on CPython and both native
interpreters, and holds the red cells to its `KNOWN_RED` table, whose rows
live in `lifecycle_known.py` beside this file.

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
- **E12** a move before the first pull that stays: each patch, and Mix to
  0, 64 and 127. At the defaults only. Its control is not the
  uninterrupted instance but a fresh one built at the move's setting
  (`patch=`, or the Mix keyword, `mix` unless `MIX_KEYWORD` names another);
  a constructor that takes no such keyword prints `na(no fresh build)`.

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
- **PF** (E12) The first block equals the fresh instance's, byte for
  byte: a level that waits for a zero crossing or a block before it moves
  plays its first block at the old setting, which P4's bound forgives.
- **PR** (E1-reset@block, E10-reset, E5-mix0, E10-mix0) From the move that
  lands the class on a state it can be built at (a reset: patch 0; a
  return from Mix 0 that routed around the graph, a rejoin: the cell's own
  configuration; a Mix 0 that keeps the graph running prints `na`) on,
  4096 frames are byte-identical to a fresh instance built there and fed
  the source from the same frame. Where the source stands is read off a
  dry run to the move. No tail is forgiven: a child left at its own patch 0, a line kept
  across a reset or a block primed twice is red here.
  PR runs on the reset events at the cell's own configuration. The kit's
  `fresh` check ([KIT.md](KIT.md)) holds the same property more widely: a
  reset from every patch, before the first pull and mid-stream, the
  readback after it, and each macro moved after the reset.
- **P6** The three interpreters print identical lines for every cell. Each
  line carries `h:`, a CRC-32 of the event instance's whole render, so P6
  compares bytes, not only verdicts.
- **PD** E3's surface check.

A verdict is `ok`, `na(...)` (the property does not apply to that cell,
said why: `tail None`, a whole RawSample, a class that never falls silent),
`RED(...)` with what was measured, or `decl`.

## A wire that is a depth

E5 and E9 move "Mix", the class's wet/dry control: the macro labelled Mix,
or the one a row of `MIX_INDEX` names (Octaver's Octave 1, SlapbackDelay's
Level). A class whose wire is a depth or a range has no crossfade: AutoPan,
Tremolo, Notch and Expander have a Depth, DeEsser and NoiseGate a Range.
At 0 each is the input, but nothing between 0 and full is a dry/wet blend,
and moving it jumps (an LFO's depth, a gate's floor). A row of `DEPTH_INDEX`
gives such a class the same events, judged by the depth model:

- **P1** at 0 is the same byte compare. `DEPTH_NOT_A_WIRE` names the
  settings where 0 is not one by design (DeEsser in HF-only mode or
  Listening, a gate's or expander's Key Listen); a cell that visits one
  prints `na(not a wire: ...)`, and only that cell.
- **P2 to P4** are judged as for any control.
- **P5** on a move of the depth allows the step the jump itself makes: the
  limit is the usual one plus how far the class's output stands from the dry
  at that moment, and no more. Read as a crossfade's, the same jump is a
  click on every cell that moves the wire.
- The constructor keyword `E12` builds a fresh instance with is named in
  `MIX_KEYWORD` (`depth`, `range_db`, `depth_db`).

`DepthJump` is the planted control (a depth handed over at once), `DepthLeak`
(0 leaves the source 3 % down) and `DepthPop` (a click on top of the jump)
the plants that show P1 and P5 can fail under the model.

## Without `get_buffer`

CircuitPython's default board builds compile `audiocore.get_buffer` out.
The kit's nogb check ([KIT.md](KIT.md#the-checks), `kit_nogb.py`) runs
E1, E5, E6 and E10 of this matrix at 48 kHz, at the defaults and at every
patch, each its own run, once as it is and once with `get_buffer` hidden
from the class's own modules, on CPython, MicroPython and CircuitPython.
A run that raises is a red `run/<rate>/<channels>/<patch>` cell; a cell
whose P1 to P4 verdicts change kind without `get_buffer` is red.

## Declaring an exception

A class that cannot satisfy a property by design (a glide, a reverb tail, a
free-running LFO) adds a row to `DECLARED` in `lifecycle.py`:

    DECLARED = {
        ("TapeDelay", "E1-", "P4"): "wow and flutter run free across a reset",
    }

The key is (class `NAME`, event name prefix, property); the cell then prints
`decl` and counts as a declared exception. The prefix names at least one
whole event and its dash (`E4-`, `E10-reset`); a bare `E` or `E1` is
refused at import, because it also matches cells its reason does not
describe.

A row can be narrowed by scopes after the property, each kind at most
once: a tuple of patches (None for the defaults), and a string naming the
interpreters (`sys.implementation.name`, comma-separated):

    ("PitchShifter", "E10-reset", "P4", "circuitpython"): "...",
    ("Octaver", "E5-", "P1", (1, 2, 5)): "...",

A row whose reason holds on one interpreter only names it, so the cell
stays a live check on the other two. A row written with a patch tuple as
its fourth element keeps working as it is; one with a bare `E` prefix is
split into one row per event its reason covers.

E1's P4 and PR ask different things. PR holds the reset to a fresh
instance; P4 holds it to the control that never was reset. A class whose
reset is exactly a fresh instance can still never meet that control again:
`Vibrato` restarts its LFO as a fresh one starts it, and `Fuzz`'s 10.5 and
12.4 Hz coupling sections keep a few LSB of the earlier material in float
state for seconds. Such a class declares E1 P4 with the cause, keeps PR
live, and its own test holds the cause (for `Fuzz`, the residue under 1024
LSB).

Values a host hands the controls are not lifecycle events. The kit's args
check holds them, including the refused-values contract (`bad-m<i>` in
[KIT.md](KIT.md#the-checks): a macro value off 0-127 is clamped, NaN to the
bottom stop).

PR is excused only by `FREE_PHASE`, class `NAME` -> the free-running
phase (an LFO, a wow table) that keeps a reset or a rejoin from matching a
fresh instance, named.

A cell that cannot finish on one interpreter, such as a node there that
never returns from a pull, is skipped there instead: a row in `SKIP`, keyed
(class `NAME`, event name prefix, `sys.implementation.name`), makes the cell
print `na(skip: <reason>)` on every property without building anything, and
P6 leaves it out. Today's rows are the E8 cells of the three nodes
CircuitPython takes from upstream's `audiodelays` (Echo, PitchShift and
GranularPitchShift); a class built on them adds its own. Nothing else skips
a cell. The test file's `KNOWN_RED` is different: it records what is red today, as
findings, one row per (class, event prefix, property) with the number and a
digest of its red cells, so the suite goes red when a cell changes either
way. The test runs the quick matrix; `LIFECYCLE_FULL=1` runs the full one,
and `LIFECYCLE_CLASSES=DigitalDelay,TapeDelay` limits it to some classes.

## The plants

The helper ships a control and a planted fault for every property, and
`TestPlants` holds each plant red on its cell with its control green there:
`DropOnReset` (P1), `HoldDC` (P2), `StaleMix` against `Routed` (P3),
`LateMove` (P4), `HardSwitch` (P5), `BusyDeinit` (PD), `LatePatch` (PF, a
pre-pull patch that lands a block late), `ResetLeak` against `Routed` (PR,
a reset that keeps its echo line; P4 reads both as ok) and `ImplPlant`
(P6, a level a hair different off CPython).
