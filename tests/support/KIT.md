# The effects kit

Nine mechanical checks that run on one effect class with no model in the
loop: every verdict is arithmetic on rendered bytes, or on the source. They
sit beside the [lifecycle matrix](LIFECYCLE.md) and catch the kinds of
defect that kept turning up class after class: a tail that outlasts
`tail_samples`, a planted fault a knob can reach, a docstring promise no
test holds, a control that does not read back what it was set to, an input
level that wraps, a citation that no longer resolves, a refused call that
leaves a trace, a class that only behaves where `audiocore.get_buffer`
exists, a reset that does not come back as a fresh instance, and a trait
that holds on a sine at one level and not on a plucked phrase at another.

To run all nine on one class, from the repo root:

    python tests/support/kit.py DigitalDelay
    python tests/support/kit.py DigitalDelay --only tail,ceiling --quick
    MICROPYPATH=lib:tests/support micropython -X heapsize=256M \
        tests/support/kit.py DigitalDelay --quick

Each check also runs alone (`python tests/support/kit_tail.py
DigitalDelay`). `--quick` trims the grid (below); `--no-run` makes the
claims check look the tests up without running them; `--plants-module` and
`--claims-module` name a test module other than the class's own.

It prints one line per cell, `name|check|key|V:verdict[|h:digest]`, a
`SUMMARY|name|check|cells N|red R|declared D|na A` line per check, and
`DONE`. A verdict is `ok`, `na(...)` (the cell cannot show anything, said
why), `RED(...)` with what was measured, or `decl`. `h:` is a CRC-32 of the
cell's render, so two interpreters' lines agree only when their bytes do.

The six render checks (tail, plants, args, ceiling, fresh, levels) are numpy-free
and print the same lines on CPython, MicroPython and CircuitPython. nogb
runs on all three too. The claims and paperwork checks read source,
unittest and git, and run on CPython only; a native run prints `SKIP` for
them.

A class that does nothing at all must not read as a pass: the tail and
args checks print `na(silent)` for a render that was zero throughout, and
the ceiling check is red on it.

## The checks

**tail** (`kit_tail.py`). The output reaches exact zero inside the tail
the class reports, read after every event. The material: a DC step to
-6 dBFS, noise at +-3 LSB, noise at -60 dBFS and full-scale noise, 4096
frames each, then silence. The events are the lifecycle matrix's own
(reset, each macro to each stop, Mix to 0, each patch change), plus none.
The move lands inside the material; with `back` its way back lands 1536
frames after the input stops. Bar: the output's last non-zero frame is
within `tail_samples` (read after the last action) + `latency_samples` +
one block of the input's end or the last action, whichever is later
(lifecycle P2's bound). A class whose `tail_samples` is None promises no
bound, so it must never fall silent: 3 s past the input the output must
still be non-zero in the last second, `na(tail None)`, or the cell is red
(the class could have stated a bound). Grid: every patch, 48 and 22.05 kHz,
stereo and mono; `--quick` runs the full events at the defaults and the
lifecycle's quick subset at the patches, with no `back` placements.

**plants** (`kit_plants.py`). Each planted fault the class's tests use
differs from the clean class, and no knob position or patch of the clean
class renders what it renders. The class's test module (by default
`tests/test_cpython_effects_<name>.py`) declares them:

    KIT_PLANTS = {"T1": JumpTimeSlapback, "T3": (SplitSlapback, 4)}

A value is a planted subclass, judged against the clean class at the
defaults, or `(plant, patch)`, judged at that patch (a class with two
characters plants faults in the one the defaults do not use); a third
element, a dict, may give `rate`, `channels` and constructor `options`. The
digest covers the render (an 8192-frame click and noise train, then
silence to the clean class's tail, 16384 frames to 4 s) and the reported
`tail_samples` and `latency_samples`. The walk: the clean class at the
defaults, each macro alone at each stop (0 and 127, and 64 for a bipolar
macro), and every patch. A module that does not import on an interpreter
prints `na(...)`; plants kept in a numpy-free module check natively.

**claims** (`kit_claims.py`). Every docstring sentence that makes a claim
names a test, which exists and passes. The class's test module holds a
`CLAIMS` table, one row per sentence, word for word:

    CLAIMS = (
        ("Level 0 is a wire.", "test_level_zero_is_a_wire"),
        ("Time runs from 40 to 250 ms.",
         ("TestKnobs.test_the_spans", "test_the_time_law")),
        ("A control that jumps makes the output step: ...",
         "DECLARED:TapeDelay,E4-m2=,P5"),
    )

A test is a method name (any TestCase that defines it), `Class.test_name`,
a tuple of those, or `DECLARED:<NAME>,<event prefix>,<property>`, a row of
the lifecycle matrix's DECLARED table. A scoped row is named with its
scopes after the property: `patches=1/2/d` (`d` the defaults) and each
interpreter by name, as in `DECLARED:PitchShifter,E10-reset,P4,circuitpython`. "Exists" is an AST lookup in the test
module; "passes" runs that test alone under unittest (a skip is not a pass).
The text is the class's module docstring and then its class docstring. A
sentence is a claim if it holds a digit, a number word, or a bound or
absolute word (always, never, exactly, every, each, all, no, only, at most,
at least, up to, within, under, over, same, unchanged, ...: `CLAIM_WORDS`).
The rule errs on catching too much: a sentence it catches that asserts
nothing is reworded or struck. Cells: `table`, `row<N>` per row, and
`loose<N>` per claim-shaped sentence no row covers.

**args** (`kit_args.py`). What the control surface does with what a host
hands it:

- `rt-m<i>`: `set_macro(i, get_macro(i))` mid-stream changes no byte, at
  the defaults and every patch.
- `stops-m<i>`: 0, 64 and 127 are accepted and read back within 1e-4.
- `bad-m<i>`: NaN, +-inf, -1, 128 and +-10**400 (an int past float's
  range), held to the contract's one answer
  ([component-api.md](../../docs/reference/component-api.md#macro-and-patch-state)):
  a value off the range is clamped, never refused. NaN, -inf, -1 and
  -10**400 read back 0, +inf, 128 and 10**400 read back 127, and each
  renders exactly what
  `set_macro(i, readback)` renders (`c`). A raise of any kind is red.
- `patch-p<k>`: `program_change(k)` sets `patch_index` and reads back the
  patch's values, and `program_change(0)` reads back patch 0's. Not what a
  fresh instance read: a declared default may sit off patch 0's grid
  ([metadata.md](../../docs/reference/metadata.md)), so the kit
  holds a reset to a fresh instance (`fresh`), not a fresh instance to
  patch 0.
- `ctor-<option>`: each numeric keyword of `_build` at 0 and NaN (a
  keyword whose default is `None`, left out to play patch 0's step, counts
  when the class names its number in `_OPTION_DEFAULTS`). A raise is
  ValueError or TypeError; a build reports readable latency and tail,
  finite macros, renders without raising or sitting on a rail the input
  was not on; and a NaN build renders exactly what the defaults or the
  option at 0 render.

- `refused-<trigger>/<d|last|opt>`: a call the contract's methods refuse
  leaves the instance exactly as it was. The triggers are
  `program_change` with a negative, boolean or float `sample_position`, or
  an index of 0.0, 1.0, True, -1, None or "0"; `set_macro` with an index
  or value of the wrong type, a negative or float `sample_position` or
  NaN; and the two no-ops the contract allows (an index past the last
  patch, `channel=-1`). The call lands before pull 8 on an instance built
  at the defaults (`d`), at the last patch (`last`) and with every numeric
  constructor option moved off its default (`opt`, which is where a
  constructor's exact value lives). A raise must be ValueError, TypeError
  or IndexError. Whether it raised or was accepted as a no-op, every macro
  reads back the same (on the 0-127 grid and as `macro()` plays it),
  `patch_index` is unchanged, and the render equals one from an instance
  that never saw the call. A call that is not a no-op and is accepted is
  not judged (`ok(a)`).

**ceiling** (`kit_ceiling.py`). At the level the class says it is clean
at, on the worst material, the output does not wrap, sit on a rail, or go
silent. The class states `INPUT_CEILING_DBFS` (dBFS, 0 or below); with
none it is held to 0 dBFS. The material, 2 s at the peak (longer for a
class with a long tail: the window is the tail the instance reports once
its settings are in, rounded up to whole seconds, at most 12; a long hall's
worst case builds up as its tail does): a 100 Hz square,
a 50 Hz sine, one-sample clicks of alternating sign, noise, a DC step, and
squares on the low notes 41, 55, 82, 110, 147, 163 and 220 Hz (`sq41` ...;
163 Hz is where ConvolutionReverb's default room peaks highest, between the
notes the others are on). The
settings: the defaults, every patch, each macro alone at 0, 64 and 127,
every macro at 127 together (`all=127`), and every level-like macro (a
label holding Level, Mix, Octave, Direct, Voice or Gain) at 127 with each
other macro at each of its stops (`lv=127+m<i>=<v>`), and the same on
every patch (`p<n>+lv=127+m<i>=<v>`, on the sine and the squares only). At 48 and 22.05 kHz,
stereo and mono (`--quick`: 48 kHz stereo). The bars:

- `wrap`: neighbouring samples of opposite sign more than 32768 apart,
  where the second, moved by 65536, lands within a quarter of the jump of
  the first and the signal runs the same way either side, and the input
  made no such jump: an int16 sum that overflowed. Not judged on the
  noise. A flat signal that wraps is not caught.
- `rail`: more than 8 frames in a row at |y| >= 32767 where the input was
  not.
- `silent`: the last second exactly zero while the input played through
  it (not judged on the DC step, which a high-pass rightly takes to zero).

**paperwork** (`kit_paperwork.py`). CHANGELOG.md has a bullet starting
``- **`<NAME>`**``, and every citation in the class's module
(`file.c:NN`, `path/file.h:NN-MM`, `file.py:NN`, and a bare `` `:NN` ``
citing the file named last) names lines inside a file of audiodsp at the
commit in `AUDIODSP_PIN`, or of this repository. The pinned audiodsp is
read from a checkout (`KIT_AUDIODSP`, or an `audiodsp` directory beside
this repository or a parent), never changed; with no checkout, or without
the pinned commit in it, an audiodsp citation prints `na(...)`. Line
numbers are all it can know: a citation whose lines moved still resolves.

It also holds `MACRO_LABELS` and `MACRO_MODES` to the surface table in
section 3 of the class's card (`<NAME>.md` in `KIT_CARDS`, or the cards
directory found above this repository): one `surface-m<i>` cell per macro,
a mismatch naming both sides. A class with no card, or a card with no
table whose header has `#`, `Label` and `Mode`, prints `na(...)`.

**nogb** (`kit_nogb.py`). A class whose primed voice is flushed by
`audiocore.get_buffer` misbehaves on the board builds that compile it out
of CircuitPython: the block the voice still holds plays later, source
frames from the start of the material at a point where they do not belong.
The check hides `get_buffer` from the class's module, its bases' modules
and `audioeffects` (it replaces the `audiocore` name they read with a
stand-in that has everything but `get_buffer`, and puts it back; the
matrix's own pulls keep the real one) and compares two things with the
run that has it.

- `run/48000/<channels>/<d|pK>`: the lifecycle events below, at the
  defaults and at each patch, each its own run. Red when the class raises
  there, with `get_buffer` or without, so a class that calls it
  unconditionally at one patch says which, and every other patch is still
  judged.
- Lifecycle cells (E1, E5, E6, E10 at 48 kHz, stereo and mono, every
  patch): P1 to P4 must be the same kind of verdict (ok, na, RED), so a
  cell is red when the class is fine with `get_buffer` and not without. The
  frames a red verdict names are not compared.
- `bytes-<scenario>/48000/<channels>/<d|pK>`: the whole render, every
  channel, byte for byte: a reset, two resets in a row, a reset before the
  first pull, a patch change and a reset in one block, and resets a block
  apart, at the defaults and every patch. A class whose first block is rightly gated differently without
  `get_buffer` declares the cell in `DECLARED`.

On all three interpreters. On MicroPython and CircuitPython the class's
own Python loses `get_buffer` while the native nodes under it are the real
ones, which is what a board build without it runs; a path a class takes
only off CPython is checked there and nowhere else. Run it on each:

    python tests/support/kit.py Saturation --only nogb
    MICROPYPATH=lib:tests/support micropython -X heapsize=256M \
        tests/support/kit.py Saturation --only nogb

A module that imports `get_buffer` inside a function is not reached.

**fresh** (`kit_fresh.py`). A reset comes back as a fresh instance at
patch 0, from every patch:

- `reset@<k>/<rate>/<ch>/<d|pK>`: built at the defaults or a patch, played
  `k` pulls (0, before the first pull, and 8), then `reset()`. From that
  pull on it renders byte for byte what a fresh instance built at patch 0
  (the constructor's `patch=`) renders, fed the source from the frame the
  reset left it at (found off a dry run), and reads back what the fresh one
  reads. No tail is forgiven: a block a voice still held, a line the reset
  kept, a filter's memory or a delay left from the patch before is red.
- `reset@8+m<i>=<v>/...`: the same, then the same move on both four pulls
  later, each macro to each stop, and the readback after it. A state the
  reset left that only a move wakes (a line length, a write head) is red
  here.
- `rpr<K>@8/<rate>/<ch>/d`: built at the defaults, played 8 pulls, then
  `reset()`, `program_change(K)` and `reset()` again, for every patch K,
  and held to the same fresh instance. A patch that builds part of the
  graph again between two resets must not leave the second one reaching
  for a node the rebuild released.
- `boot/<rate>/<ch>`, informational: whether a fresh instance at its
  defaults is patch 0 exactly. Patch values are integers and a declared
  default may sit off their grid ([metadata.md](../../docs/reference/metadata.md)),
  so a difference prints `na(info: ...)` and is never red.

Each cell compares 2 s from the reset and stops at the first difference.
Grid: 48 and 22.05 kHz, stereo and mono, the defaults and every patch;
`--quick` runs 48 kHz and the move cells from the defaults and the last
patch only. A class whose reset cannot meet a cell by design declares it
in `DECLARED`.

**levels** (`kit_levels.py`). Real material at three levels. The checks
above play their material at one level each, and a class whose behaviour
turns on the input level (a comparator, a dead band, a detector) can be right
there and wrong a few dB away. The material is `kit_common.phrase`: six
plucked strings one at a time (110, 82, 147, 196, 247 and 330 Hz, 300 ms
each), a triangle of displacement and a little pick noise round a
Karplus-Strong loop, so each note rings down through every level under its
peak; 2 s in integer arithmetic, after 1024 frames of silence, at -24, -12
and -3 dBFS. A level above the class's `INPUT_CEILING_DBFS` prints
`na(above ceiling)`. Each cell renders the phrase and then silence to the
class's tail (up to 6 s):

- `wrap` and `rail`: the ceiling check's bars, on this material.
- `live`: the output is not zero throughout while the phrase plays. Not
  judged with the wire at 0.
- `ring`: the output's last non-zero frame is inside `tail_samples` +
  `latency_samples` + one block of the phrase's end. A longer tail than 6 s,
  or none, is not judged.
- `wire`: with the class's wet/dry control at 0 (`lifecycle.mix_index`: a
  Mix, a row of `MIX_INDEX` or a depth of `DEPTH_INDEX`), the output is the
  input, byte for byte, `latency_samples` later. A patch where the lifecycle
  matrix declares Mix 0 no wire, and the settings a depth names in
  `DEPTH_NOT_A_WIRE`, print `na`.

Cells: `<level>/<rate>/<channels>/<config>`, the config `d` (the defaults),
`p<k>` (a patch), and `wire@d`, `wire@p<k>` for a class that has a wire. 48
and 22.05 kHz, stereo and mono, the defaults and every patch (`--quick`:
48 kHz stereo, the defaults and the last patch).

## What CI runs

The lifecycle matrix gates every class, and its quick mode over all 45
takes about 4.4 CPU hours on CPython, over an hour on a 4-core runner. So
CI doesn't run all of it on every pull request:

- A pull request runs the classes whose own module it changes. When it
  changes a shared file (the base class, the package modules,
  [`tests/support/`](./), the matrix test or `AUDIODSP_PIN`), it also runs a fixed
  sample of one class per mechanism family: Bitcrusher, Tremolo,
  DigitalDelay, Reverb, Octaver, LowPass, Rack, Saturation and Distortion.
  That takes about 13 minutes (`SAMPLE` in [`tests/test_lifecycle_matrix.py`](../test_lifecycle_matrix.py)).
- The node matrix ([`tests/test_node_matrix.py`](../test_node_matrix.py), the 13 audiodsp nodes the
  classes stand on) follows the same rule. A pull request runs the nodes
  whose own adapter class or table rows it changes, and a fixed sample
  (`NODE_SAMPLE`) when it changes a shared file: `AUDIODSP_PIN`, the base
  class, `lifecycle.py`, the class matrix test, or a line of the adapters
  outside every node's own.
- A push to main runs all 45 classes and every node, and so does a manual
  run of the workflow or a pull request labelled `lifecycle: all classes`.

To tell what changed, CI diffs the pull request against its base branch,
so the checkout fetches the history. A base git can't diff from fails the
run by name rather than quietly running everything: a depth-1 checkout once
did that, and a pull request's run took 1 h 43 min. The workflow prints
what each matrix will run in its "Show the lifecycle scope" step.

The sample is the cheapest class that covers each way a class can break:
the lazy re-arm, an LFO, a delay line, a reverb tank, a pitch shifter's
splice, a biquad, a rack's children, Saturation's recentre and
Distortion's graph rebuild. A shared change that breaks one class of a
family usually breaks the family, and main's full run catches the rest
before a release.

## Known gaps

- **Several levels, one phrase.** The levels check reads the wire, the
  ring-out and the rails at three levels on one plucked phrase. It has no
  model of what a class should do with a quieter note: a trait that turns on
  the input level (Octaver's tracking near Sensitivity) is held to the same
  phrase in the class's own tests (`T7` in
  [`tests/test_cpython_effects_octaver.py`](../test_cpython_effects_octaver.py)).

## Options

`kit_options.py` holds `KIT_OPTIONS`, the constructor options the kit
builds a class with, by `NAME`; every other class is built at its defaults.
It is for a class whose defaults are trivial, such as the generic `Rack`,
whose default chain is empty.

## Declaring an exception

A class that cannot meet a cell by design adds a row to `DECLARED` in
`kit_common.py`:

    DECLARED = {
        ("TapeDelay", "ceiling", "sine/"): "the tape saturates by design",
    }

The key is (class `NAME`, check, cell key prefix); a matching red cell
prints `decl` and counts as declared. A fourth element names the one
interpreter the row holds on (`circuitpython`), so the cell stays live on
the other two. Nothing else skips a cell.

## The plants

[`tests/test_kit.py`](../test_kit.py) holds every check red on a planted fault and its control
green on the same cell, with the plants in `kit_planted.py` (a Waveshaper
and a level around the source; `KitPlain` is the control): `ShortTail` and
`EventTail` (tail; `EchoTail` the control), `NoneSilent` and `NoneDC` (a
None tail), `Inert`, `KnobReach` and `SoftOnly` (plants), a fixture test
module with a missing sentence, a missing test, a failing and a skipped test
and a loose claim (claims), `ReadbackOff`, `StopRaises`, `NanLevel`,
`NanRaises`, `NanTop`, `PatchStale` and `CtorNan` (args; `NanRaises`
refuses a NaN and `NanTop` puts it on the top stop, both green before the
clamp was the contract; `ClearsFirst` and `ClearsMacro` for the
refused calls: one zeroes the cached level, the other drops the patch or
moves a macro, before validating), `WrapKit`, `ClipKit` and `DeadStop`
(ceiling; `MidWrap`, `ComboWrap`, `AllWrap` and `LowWrap` wrap only at
Level 64, at the level-like macros at 127 with Tone at 0, with every macro
at 127, and on a square below 60 Hz, against `CondKit` and `KitPlain`), a
missing CHANGELOG line, citations past the end of a file or to no file, and
a fixture card whose surface table differs (paperwork), `FlushOnly` and `DoubleReset` (nogb: the first leans
on `get_buffer` to flush a primed voice, the second drops a block on a
second reset in a row without it; `FlushKit`, which primes a voice of its own
and plays it again where it cannot flush, is the control; `MidPatchReset`
does it at a middle patch only, against `FlushKit3`; `PatchPulls` calls
`get_buffer` unconditionally at a middle patch, which an earlier nogb read
as one `run` cell for the whole class, and is red on that patch's `run`
cells alone; `NativeFlush` leans on `get_buffer` only off CPython, so it
is clean on CPython and red on MicroPython and CircuitPython, where the
check once did not run), `PatchLeak`
and `MoveLeak` (fresh: a reset from patch 1 only that keeps the repeat line;
a first move after a reset that lands 1 % off, against `FreshKit` and
`OffGrid`, whose Gain default sits a hair off patch 0 and is never red), `LeakBand` (levels: the wire at Mix 0 leaks 2 LSB
between 3000 and 12000, which the phrase at -24 dBFS never reaches and at
-12 dBFS does; `WrapKit` is red at -3 dBFS alone, `WrapKitQuiet` states a
ceiling and is not played above it, and `ShortTail` rings past its tail at
every level), and `Silent`, which
does nothing. Its native half
holds the render checks to the same lines on all three interpreters, and
shows that agreement can fail with `ImplKit`, whose level differs off
CPython.