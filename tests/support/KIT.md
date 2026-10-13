# The effects kit

Six mechanical checks that run on one effect class with no model in the
loop: every verdict is arithmetic on rendered bytes, or on the source. They
sit beside the [lifecycle matrix](LIFECYCLE.md) and catch the kinds of
defect that kept turning up class after class: a tail that outlasts
`tail_samples`, a planted fault a knob can reach, a docstring promise no
test holds, a control that does not read back what it was set to, an input
level that wraps, and a citation that no longer resolves.

To run all six on one class, from the repo root:

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

The four render checks (tail, plants, args, ceiling) are numpy-free and
print the same lines on CPython, MicroPython and CircuitPython. The claims
and paperwork checks read source, unittest and git, and run on CPython
only; a native run prints `SKIP` for them.

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
the lifecycle matrix's DECLARED table. "Exists" is an AST lookup in the test
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
- `bad-m<i>`: NaN, +-inf, -1 and 128. The contract
  ([audio-component-api.md](../../docs/audio-component-api.md)) does not
  say whether an out-of-range macro value raises or clamps, so either
  passes: a raise is ValueError or TypeError and moves no macro (`r`); a
  clamp reads back a finite 0..127 (0 below, 127 above) and renders
  exactly what `set_macro(i, readback)` renders (`c`).
- `patch-p<k>`: `program_change(k)` sets `patch_index` and reads back the
  patch's values, and `program_change(0)` reads back what a fresh instance
  read (the contract: a fresh component and one given patch 0 are the
  same).
- `ctor-<option>`: each numeric keyword of `_build` at 0 and NaN. A raise is
  ValueError or TypeError; a build reports readable latency and tail,
  finite macros, renders without raising or sitting on a rail the input
  was not on; and a NaN build renders exactly what the defaults or the
  option at 0 render.

**ceiling** (`kit_ceiling.py`). At the level the class says it is clean
at, on the worst material, the output does not wrap, sit on a rail, or go
silent. The class states `INPUT_CEILING_DBFS` (dBFS, 0 or below); with
none it is held to 0 dBFS. The material, 2 s at the peak: a 100 Hz square,
a 50 Hz sine, one-sample clicks of alternating sign, noise, and a DC step,
at the defaults, every patch and each macro alone at each stop, at 48 and
22.05 kHz, stereo and mono (`--quick`: 48 kHz stereo). The bars:

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
prints `decl` and counts as declared. Nothing else skips a cell.

## The plants

`tests/test_kit.py` holds every check red on a planted fault and its
control green on the same cell, with the plants in `kit_planted.py`
(a Waveshaper and a level around the source; `KitPlain` is the control):
`ShortTail` and `EventTail` (tail; `EchoTail` the control), `NoneSilent`
and `NoneDC` (a None tail), `Inert`, `KnobReach` and `SoftOnly` (plants),
a fixture test module with a missing sentence, a missing test, a failing
and a skipped test and a loose claim (claims), `ReadbackOff`,
`StopRaises`, `NanLevel`, `PatchStale` and `CtorNan` (args), `WrapKit`,
`ClipKit` and `DeadStop` (ceiling), a missing CHANGELOG line and citations
past the end of a file or to no file (paperwork), and `Silent`, which does
nothing. Its native half holds the render checks to the same lines on all
three interpreters, and shows that agreement can fail with `ImplKit`,
whose level differs off CPython.
