# The effects kit

Seven mechanical checks that run on one effect class with no model in the
loop: every verdict is arithmetic on rendered bytes, or on the source. They
sit beside the [lifecycle matrix](LIFECYCLE.md) and catch the kinds of
defect that kept turning up class after class: a tail that outlasts
`tail_samples`, a planted fault a knob can reach, a docstring promise no
test holds, a control that does not read back what it was set to, an input
level that wraps, a citation that no longer resolves, a refused call that
leaves a trace, and a class that only behaves where `audiocore.get_buffer`
exists.

To run all seven on one class, from the repo root:

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
print the same lines on CPython, MicroPython and CircuitPython. The claims,
paperwork and nogb checks read source, unittest and git, or patch modules,
and run on CPython only; a native run prints `SKIP` for them.

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
none it is held to 0 dBFS. The material, 2 s at the peak: a 100 Hz square,
a 50 Hz sine, one-sample clicks of alternating sign, noise, a DC step, and
squares on the low notes 41, 55, 82, 110 and 147 Hz (`sq41` ...). The
settings: the defaults, every patch, each macro alone at 0, 64 and 127,
every macro at 127 together (`all=127`), and every level-like macro (a
label holding Level, Mix, Octave, Direct, Voice or Gain) at 127 with each
other macro at each of its stops (`lv=127+m<i>=<v>`). At 48 and 22.05 kHz,
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

- Lifecycle cells (E1, E5, E6, E10 at 48 kHz, stereo and mono, every
  patch): P1 to P4 must be the same kind of verdict (ok, na, RED), so a
  cell is red when the class is fine with `get_buffer` and not without. The
  frames a red verdict names are not compared.
- `bytes-<scenario>/48000/<channels>/<d|pK>`: the whole render, every
  channel, byte for byte: a reset, two resets in a row, a reset before the
  first pull, a patch change and a reset in one block, and resets a block
  apart, at the defaults and every patch. A class whose first block is rightly gated differently without
  `get_buffer` declares the cell in `DECLARED`.

CPython only. A module that imports `get_buffer` inside a function is not
reached.

## Known gaps

- **Several levels.** Every render check plays its material at one level
  (the ceiling at the stated peak, the others where they are set). A class
  whose behaviour turns on input level, such as a comparator or a dead
  band, can be wrong a few dB below the level any cell plays. No check
  sweeps the input level yet.

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

`tests/test_kit.py` holds every check red on a planted fault and its control
green on the same cell, with the plants in `kit_planted.py` (a Waveshaper
and a level around the source; `KitPlain` is the control): `ShortTail` and
`EventTail` (tail; `EchoTail` the control), `NoneSilent` and `NoneDC` (a
None tail), `Inert`, `KnobReach` and `SoftOnly` (plants), a fixture test
module with a missing sentence, a missing test, a failing and a skipped test
and a loose claim (claims), `ReadbackOff`, `StopRaises`, `NanLevel`,
`PatchStale` and `CtorNan` (args; `ClearsFirst` and `ClearsMacro` for the
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
does it at a middle patch only, against `FlushKit3`), and `Silent`, which
does nothing. Its native half
holds the render checks to the same lines on all three interpreters, and
shows that agreement can fail with `ImplKit`, whose level differs off
CPython.