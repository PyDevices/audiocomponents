"""The shared lifecycle matrix for audioeffects classes.

One fixed set of lifecycle EVENTS (reset, a host reset of the output,
deinit, macro stops, Mix to 0 and back, patch changes, a source that runs
dry or ends, odd source buffer sizes, moves before the first pull, several
moves before one pull), run the same way on every class, each cell judged by
the same PROPERTIES against a CONTROL instance that never met the event. No
model is in the loop: a cell is green or red by arithmetic on the bytes.

It is numpy-free and runs unchanged on CPython, MicroPython and
CircuitPython, so the three interpreters can be held to printing the same
line for every cell (P6, judged by `tests/test_lifecycle_matrix.py`).

    python tests/support/lifecycle.py DigitalDelay [--events E1,E5] [--quick]

`LIFECYCLE.md` beside this file says what each event and property is and
how a class declares an exception. `run_class()` is the entry point; the
planted faults at the bottom are the matrix's own proof that each property
can fail.
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")

import binascii

try:
    from array import array
except ImportError:                                   # pragma: no cover
    array = None

import audiocore
import audiofilters
import audiomixer

try:
    from audioroute import Port
except ImportError:                                   # pragma: no cover
    Port = None

try:
    from audioeffects import _component
except ImportError:                                   # pragma: no cover
    _component = None

#: `_component` reads VENDOR off the module a class is defined in, and the
#: planted classes are defined here.
VENDOR = "PyDevices"

BLOCK = 256
RATES = (48000, 22050)
CHANNELS = (2, 1)
#: The pull the mid-stream event lands before, and how many pulls later the
#: move comes back.
K0 = 12
GAP = 2
#: Frames compared (P4) or held to zero (P2) past each bound.
MARGIN = 2048
#: P5's factor, as a fraction: 3/2 = 1.5.
STEP_NUM = 3
STEP_DEN = 2
#: Frames of silence P3 waits for when a class reports no tail.
NO_TAIL_WAIT = 10 * 48000

#: The class's wet/dry control, by macro index. A class not named here uses
#: the macro labelled "Mix". A class whose wire is a level at 0 and has no
#: "Mix" label needs a row here, or in `DEPTH_INDEX`, or its E5 and E9 cells
#: never run; a class that has one and is not given a row is listed in
#: `UNRUN_WIRE_CONTROL` until it can be, and a class with none in
#: `NO_WIRE_CONTROL`.
MIX_INDEX = {
    "SlapbackDelay": 1,        # "Level": the slap's level; 0 is the dry
    "Octaver": 1,              # "Octave 1": 0 is the wire at patch 0
}

#: A wire that is a depth or a range: 0 is a bypass, but nothing in between
#: is a crossfade of dry and wet. Moving it jumps (an LFO's depth, a gate's
#: floor), so the matrix judges the move with the depth model below and
#: not with a crossfade's: at 0 the output is the source, byte for byte
#: (P1); everything the class does at its other settings is judged as it
#: is for any control (P2 to P4); and P5 allows the step the jump itself
#: makes, which is how far the class's output is from the dry at that
#: moment, and nothing more. A row names the macro index.
DEPTH_INDEX = {
    "AutoPan": 1,              # "Depth": 0 pans nothing
    "Tremolo": 2,              # "Depth": 0 is a wire
    "Notch": 3,                # "Depth": 0 is a wire
    "DeEsser": 1,              # "Range": 0 is a wire, broadband, not listening
    "NoiseGate": 4,            # "Range": 0 dB, the knob's bottom
    "Expander": 2,             # "Depth": 0 dB, the knob's bottom
}

#: The planted depth's own row, kept apart so the tables above name only
#: real classes.
PLANT_DEPTH_INDEX = {"LifecycleDepth": 0}

#: Settings at which a depth at 0 is not a byte compare, by design: class ->
#: ((macro index, MIDI value from which it holds, why), ...). A cell that
#: visits one of them (the patch it is built at, a patch it moves to, a
#: macro it moves) prints P1 `na`, as it does for a stated non-bypass.
DEPTH_NOT_A_WIRE = {
    "DeEsser": (
        (3, 64, "HF-only at Range 0 is the two band halves summed: flat, and"
                " not a byte compare (the class says so)"),
        (6, 64, "Listen puts the detector's band on the output"),
    ),
    "NoiseGate": (
        (7, 64, "Key Listen puts the detector's band on the output"),
    ),
    "Expander": (
        (7, 64, "Key Listen puts the detector's band on the output"),
    ),
}

#: Classes with a macro that is a wire at 0 and no "Mix" label, whose E5 and
#: E9 cells do not run yet: name -> (macro index, why). Empty since the
#: depth model (`DEPTH_INDEX`) took the six depths and ranges in.
UNRUN_WIRE_CONTROL = {}

#: The classes with no wet/dry control, and why, so that a new class has to
#: be sorted into one table or the other (`test_every_class_has_its_wire`).
#: A class here has no macro that renders the source byte for byte at 0 and
#: not at its defaults (checked by playing each macro at its stops).
NO_WIRE_CONTROL = {
    "GraphicEQ": "a flat curve is the wire, with every band at its detent",
    "Limiter": "Gain is make-up gain and Ceiling a threshold: the class is a"
    " wire at its defaults and at Gain 0, neither a level that mixes",
    "ParametricEQ": "a flat curve is the wire, with every gain at its"
    " detent",
    "Rack": "no macros of its own",
    "StereoWidener": "Width 0 is a wire in Haas character and mono in"
    " Mid/Side",
    "TransientShaper": "Attack and Sustain at their detent are the wire,"
    " the middle of a bipolar knob and not a level at 0",
    "Vibrato": "Depth 0 and Level 0 leave the delay line in the path, and"
    " neither renders the source byte for byte",
}

#: The interpreters a DECLARED or SKIP row can name.
IMPLS = ("cpython", "micropython", "circuitpython")
#: The events that move a control (P5 judges only these).
CONTROL_EVENTS = ("E4-", "E5-", "E6-", "E9-", "E11-")

#: Where a class cannot satisfy a property by design, it says so HERE, one
#: row per (class NAME, event name prefix, property[, scope...]): reason. A
#: matching cell prints `decl` instead of RED and is counted as a declared
#: exception. Nothing else skips a cell.
#:
#: The event prefix names at least one whole event number and its dash
#: ("E1-", "E10-reset", "E4-m2="): a bare "E" or "E1" is refused at import,
#: since it would also match events its reason does not describe.
#:
#: A scope narrows a row; give each kind at most once, in either order:
#:
#: - a tuple of patches, the configurations the row covers (None for the
#:   constructor defaults): ("Octaver", "E5-", "P1", (1, 2, 5, 6));
#: - a string naming the interpreters it holds on, `sys.implementation.name`,
#:   comma-separated: ("PitchShifter", "E10-reset", "P4", "circuitpython").
#:
#: A row without a scope matches every patch on every interpreter.
#: ShimmerHall on CircuitPython only (the rows below name it): Bloom's
#: shifter is CircuitPython's own `audiodelays.PitchShift`, which keeps its
#: read, write and overlap positions through a clear (audiodsp#240 is in
#: audiodsp's copy only), so a re-arm's or a reset's priming pulls leave it
#: at another splice phase than a control that was only built, and the
#: hall's tank then stays a few LSB off the control's. CPython and
#: MicroPython are ok; a ruled CircuitPython-own difference.
_SHIMMER_CP = (
    "CircuitPython only: its own audiodelays.PitchShift keeps its read,"
    " write and overlap positions through a clear (audiodsp#240 is in"
    " audiodsp's copy only), so the reset's or the re-arm's priming pulls"
    " leave Bloom's shifter at another splice phase than the control's"
    " and the hall's tank stays a few LSB off it; CPython and MicroPython"
    " are ok (ruled a CircuitPython-own difference)")

#: Saturation's AC coupling, under the rows that name it below.
_SAT_COUPLING = (
    "its AC coupling is a 5-20 Hz pole on a Q15 kernel, which keeps a 1 to"
    " 2 LSB rounding residue that never re-converges with the control's"
    " once what reached it differed")

DECLARED = {
    ("Harmonizer", "E1-", "P4"):
        "reset() empties the three lines and starts every splice where a"
        " new instance's starts, so a shifted voice then renders as a fresh"
        " instance (test_reset_renders_as_fresh), not as the uninterrupted"
        " control",
    ("Harmonizer", "E4-", "P4"):
        "a Pitch, Voice or Detune move runs a shifter's read head at another"
        " rate, so its splice lands elsewhere and stays there (the node's"
        " by-design cell); a Level off and back, or Mix 0 and back, empties"
        " the line and starts the splice as a fresh voice's (T6)",
    ("Harmonizer", "E5-", "P4"):
        "Mix 0 and back empties the lines and starts every splice as a"
        " fresh instance's, not the uninterrupted control's",
    ("Harmonizer", "E6-", "P4"):
        "a patch change moves intervals, so the splices land elsewhere, or"
        " turns a voice off and back, which starts its splice afresh",
    ("Harmonizer", "E9-", "P4"):
        "as E5: Mix 0 and back starts every splice afresh, at every source"
        " buffer size",
    ("Harmonizer", "E11-", "P4"):
        "moves that reach an interval, a Level's off step or Mix 0 move the"
        " splices, as E4 to E6",
    ("Harmonizer", "E10-reset", "P4", "circuitpython"):
        "CircuitPython only: its own audiodelays.PitchShift keeps its read"
        " and write positions across reset_buffer (audiodsp#240 is in"
        " audiodsp's port only), so a reset before the first pull cannot"
        " put the splices back where the constructor left them; CPython"
        " and MicroPython are ok (ruled a CircuitPython-own difference)",
    ("Harmonizer", "E10-mix0", "P4", "circuitpython"):
        "CircuitPython only: as E10-reset, the return from Mix 0 empties the"
        " lines but CircuitPython's PitchShift keeps its positions",
    ("Harmonizer", "E12-p", "P4", "circuitpython"):
        "CircuitPython only: a patch moved before the first pull switches"
        " voices on or off, which empties a shifter's line, and"
        " CircuitPython's own audiodelays.PitchShift keeps its read and"
        " write positions through that (audiodsp#240 is in audiodsp's port"
        " only), so the splices land off an instance built at the patch;"
        " CPython and MicroPython are ok (ruled a CircuitPython-own"
        " difference)",
    ("Harmonizer", "E12-p", "PF", "circuitpython"):
        "CircuitPython only: as E12-p under P4, the first block carries the"
        " splice CircuitPython's PitchShift keeps from the line it emptied",
    ("Harmonizer", "E4-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step",
    ("Harmonizer", "E5-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Mix)",
    ("Harmonizer", "E6-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (a patch change)",
    ("Harmonizer", "E9-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Mix)",
    ("Harmonizer", "E11-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step",
    # PitchShifter: the splice phase, the ruling's N2. A splice shifter's
    # output depends on where its read position sits in the window, and
    # nothing but a fresh start puts two shifters at the same place.
    ("PitchShifter", "E1-", "P4"):
        "reset() starts the shifter and the loop's splicer where new ones"
        " start (audiodsp#240: the restart is audiodsp's PitchShift;"
        " CircuitPython's own keeps its positions), so the class then plays"
        " what a fresh instance plays from that point, not what the"
        " uninterrupted control plays (N2)",
    ("PitchShifter", "E4-m0=", "P4"):
        "a Pitch move runs the read position at another speed, so the splice"
        " phase lands elsewhere; putting it back would click (N2)",
    ("PitchShifter", "E4-m1=", "P4"):
        "a Fine move that changes the ratio step moves the splice phase, as"
        " Pitch does (N2)",
    ("PitchShifter", "E4-m2=0", "P4"):
        "a return from Mix 0 starts the shifter and both lines empty, at a"
        " fresh splice phase, not the uninterrupted control's (N2)",
    ("PitchShifter", "E5-", "P4"):
        "a return from Mix 0 starts the shifter and both lines empty, at a"
        " fresh splice phase, not the uninterrupted control's (N2)",
    ("PitchShifter", "E9-", "P4"):
        "a return from Mix 0 starts the shifter and both lines empty, at a"
        " fresh splice phase, not the uninterrupted control's (N2)",
    ("PitchShifter", "E6-", "P4"):
        "a patch with another interval moves the splice phase (N2)",
    ("PitchShifter", "E11-", "P4"):
        "moves of the interval or of Mix through 0 before a pull move the"
        " splice phase (N2)",
    ("PitchShifter", "E10-reset", "P4", "circuitpython"):
        "CircuitPython only: its own audiodelays.PitchShift keeps its read"
        " and write positions across reset_buffer (audiodsp#240 is in"
        " audiodsp's port only), so the re-arm's priming pulls move its"
        " splice phase off the uninterrupted control's; CPython and"
        " MicroPython are ok (ruled a CircuitPython-own difference)",
    ("PitchShifter", "E10-mix0", "P4", "circuitpython"):
        "CircuitPython only: as E10-reset, the return from Mix 0 empties the"
        " lines but CircuitPython's PitchShift keeps its positions",
    ("PitchShifter", "E10-macros", "P4", "circuitpython"):
        "CircuitPython only: the macros move to 127 before the first pull,"
        " which changes the Mixer levels, so the graph is re-armed (only a"
        " move that changes a level re-arms) and the re-arm's priming pulls"
        " move CircuitPython's own PitchShift off the control's splice phase"
        " (it keeps its positions through a clear); CPython and MicroPython"
        " are ok (ruled a CircuitPython-own difference)",
    ("PitchShifter", "E10-patch", "P4", "circuitpython"):
        "CircuitPython only: as E10-macros, the patch loaded before the first"
        " pull changes the Mixer levels and is re-armed, and CircuitPython's"
        " PitchShift keeps its positions (28 of the 32 cells; the four that"
        " start at patch 2 are ok)",
    ("PitchShifter", "E12-p1", "P4", "circuitpython"):
        "CircuitPython only: patch 1 before the first pull moves the interval"
        " or the Mixer levels, so the shifter is primed again (a level move"
        " re-arms the graph) after the constructor primed it at the old"
        " ratio, and CircuitPython's own PitchShift keeps its read position"
        " through a clear, so it sits off the splice phase of an instance"
        " built at the setting; patch 4 and the defaults, which change"
        " neither, match, and CPython and MicroPython are ok (ruled a"
        " CircuitPython-own difference)",
    ("PitchShifter", "E12-p1", "PF", "circuitpython"):
        "CircuitPython only: the first block carries the same splice-phase"
        " difference as P4 (the shifter is primed again and CircuitPython's own"
        " PitchShift keeps its positions); which rates show it in the first"
        " block depends on where the phase lands",
    ("PitchShifter", "E12-p2", "P4", "circuitpython"):
        "CircuitPython only: patch 2 before the first pull moves the interval"
        " or the Mixer levels, so the shifter is primed again (a level move"
        " re-arms the graph) after the constructor primed it at the old"
        " ratio, and CircuitPython's own PitchShift keeps its read position"
        " through a clear, so it sits off the splice phase of an instance"
        " built at the setting; patch 4 and the defaults, which change"
        " neither, match, and CPython and MicroPython are ok (ruled a"
        " CircuitPython-own difference)",
    ("PitchShifter", "E12-p2", "PF", "circuitpython"):
        "CircuitPython only: the first block carries the same splice-phase"
        " difference as P4 (the shifter is primed again and CircuitPython's own"
        " PitchShift keeps its positions); which rates show it in the first"
        " block depends on where the phase lands",
    ("PitchShifter", "E12-p3", "P4", "circuitpython"):
        "CircuitPython only: patch 3 before the first pull moves the interval"
        " or the Mixer levels, so the shifter is primed again (a level move"
        " re-arms the graph) after the constructor primed it at the old"
        " ratio, and CircuitPython's own PitchShift keeps its read position"
        " through a clear, so it sits off the splice phase of an instance"
        " built at the setting; patch 4 and the defaults, which change"
        " neither, match, and CPython and MicroPython are ok (ruled a"
        " CircuitPython-own difference)",
    ("PitchShifter", "E12-p3", "PF", "circuitpython"):
        "CircuitPython only: the first block carries the same splice-phase"
        " difference as P4 (the shifter is primed again and CircuitPython's own"
        " PitchShift keeps its positions); which rates show it in the first"
        " block depends on where the phase lands",
    ("PitchShifter", "E12-p5", "P4", "circuitpython"):
        "CircuitPython only: patch 5 before the first pull moves the interval"
        " or the Mixer levels, so the shifter is primed again (a level move"
        " re-arms the graph) after the constructor primed it at the old"
        " ratio, and CircuitPython's own PitchShift keeps its read position"
        " through a clear, so it sits off the splice phase of an instance"
        " built at the setting; patch 4 and the defaults, which change"
        " neither, match, and CPython and MicroPython are ok (ruled a"
        " CircuitPython-own difference)",
    ("PitchShifter", "E12-p5", "PF", "circuitpython"):
        "CircuitPython only: the first block carries the same splice-phase"
        " difference as P4 (the shifter is primed again and CircuitPython's own"
        " PitchShift keeps its positions); which rates show it in the first"
        " block depends on where the phase lands",
    ("PitchShifter", "E12-p6", "P4", "circuitpython"):
        "CircuitPython only: patch 6 before the first pull moves the interval"
        " or the Mixer levels, so the shifter is primed again (a level move"
        " re-arms the graph) after the constructor primed it at the old"
        " ratio, and CircuitPython's own PitchShift keeps its read position"
        " through a clear, so it sits off the splice phase of an instance"
        " built at the setting; patch 4 and the defaults, which change"
        " neither, match, and CPython and MicroPython are ok (ruled a"
        " CircuitPython-own difference)",
    ("PitchShifter", "E12-p6", "PF", "circuitpython"):
        "CircuitPython only: the first block carries the same splice-phase"
        " difference as P4 (the shifter is primed again and CircuitPython's own"
        " PitchShift keeps its positions); which rates show it in the first"
        " block depends on where the phase lands",
    ("PitchShifter", "E12-mix127", "P4", "circuitpython"):
        "CircuitPython only: Mix 127 before the first pull moves the interval"
        " or the Mixer levels, so the shifter is primed again (a level move"
        " re-arms the graph) after the constructor primed it at the old"
        " ratio, and CircuitPython's own PitchShift keeps its read position"
        " through a clear, so it sits off the splice phase of an instance"
        " built at the setting; patch 4 and the defaults, which change"
        " neither, match, and CPython and MicroPython are ok (ruled a"
        " CircuitPython-own difference)",
    ("PitchShifter", "E12-mix127", "PF", "circuitpython"):
        "CircuitPython only: the first block carries the same splice-phase"
        " difference as P4 (the shifter is primed again and CircuitPython's own"
        " PitchShift keeps its positions); which rates show it in the first"
        " block depends on where the phase lands",
    ("PitchShifter", "E4-m2=", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Mix)",
    ("PitchShifter", "E4-m3=", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Delay jumps the line's read)",
    ("PitchShifter", "E4-m4=", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Feedback)",
    ("PitchShifter", "E5-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Mix)",
    ("PitchShifter", "E6-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (a patch change)",
    ("PitchShifter", "E9-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Mix)",
    ("PitchShifter", "E11-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Mix and a patch change)",
    ("StereoWidener", "E4-m0=", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Width: the copy's level, or the route to"
        " the wire at 0)",
    ("StereoWidener", "E4-m2=", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Character swaps Haas and Mid/Side)",
    ("StereoWidener", "E6-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (a patch change moves Width or Character)",
    ("StereoWidener", "E11-2patch", "P4"):
        "a Delay move glides by design (the card's H3): from patch 1 or 2,"
        " Mid/Side and then patch 0 empty the line and land it at 14 ms, and"
        " the way back walks the read head at 0.1875, 384 frames of delay in"
        " 2048 at 48 kHz, past the copy's reach that bounds P4; it matches"
        " once the head lands",
    ("StereoWidener", "E11-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Width, Character or a patch change)",
    ("Octaver", "E1-", "P4"):
        "a flip-flop divider keeps its count: a reset starts it in"
        " pass-through polarity part-way through the material, so the"
        " octave stays inverted against an instance that was never reset"
        " (it matches a fresh one; the OC-2's flip-flops do the same)",
    ("Octaver", "E4-", "P4"):
        "a flip-flop divider keeps its count: a move that adds or drops a"
        " crossing (Tracking, Tone 1, Sensitivity) or the clear on the way"
        " back from the wire leaves the octave inverted for good",
    ("Octaver", "E6-", "P4"):
        "a flip-flop divider keeps its count: a patch change that moves"
        " Tracking or Tone 1 adds or drops a crossing, and the octave stays"
        " inverted",
    ("Octaver", "E11-", "P4"):
        "a flip-flop divider keeps its count: moves that add or drop a"
        " crossing leave the octave inverted",
    ("Octaver", "E5-", "P4"):
        "a flip-flop divider keeps its count: the clear on the way back"
        " from the wire (Octave 1 at 0) leaves the octave inverted for good",
    ("Octaver", "E9-", "P4"):
        "a flip-flop divider keeps its count: the clear on the way back"
        " from the wire (Octave 1 at 0) leaves the octave inverted for good",
    ("Octaver", "E4-m0=", "P1"):
        "the event moves Direct off 1, so Octave 1 at 0 stops being the"
        " wire and the output is not the source by design",
    ("Octaver", "E4-m2=", "P1"):
        "the event moves Octave 2 up, so Octave 1 at 0 stops being the"
        " wire and the output is not the source by design",
    ("Octaver", "E6-p1", "P1"):
        "the event changes to patch 1, where Octave 1 at 0 is a level move,"
        " not the wire, so the output is not the source by design",
    ("Octaver", "E6-p2", "P1"):
        "the event changes to patch 2, where Octave 1 at 0 is a level move,"
        " not the wire, so the output is not the source by design",
    ("Octaver", "E6-p5", "P1"):
        "the event changes to patch 5, where Octave 1 at 0 is a level move,"
        " not the wire, so the output is not the source by design",
    ("Octaver", "E6-p6", "P1"):
        "the event changes to patch 6, where Octave 1 at 0 is a level move,"
        " not the wire, so the output is not the source by design",
    ("Octaver", "E12-p1", "P1"):
        "the move before the first pull is to patch 1, where Octave 1 at 0"
        " is a level move, not the wire, so the output is not the source by"
        " design",
    ("Octaver", "E12-p2", "P1"):
        "the move before the first pull is to patch 2, where Octave 1 at 0"
        " is a level move, not the wire, so the output is not the source by"
        " design",
    ("Octaver", "E12-p5", "P1"):
        "the move before the first pull is to patch 5, where Octave 1 at 0"
        " is a level move, not the wire, so the output is not the source by"
        " design",
    ("Octaver", "E12-p6", "P1"):
        "the move before the first pull is to patch 6, where Octave 1 at 0"
        " is a level move, not the wire, so the output is not the source by"
        " design",
    ("Octaver", "E11-mix+patch", "P1"):
        "the event ends on patch 6, where Octave 1 at 0 is a level move,"
        " not the wire, so the output is not the source by design",
    ("Octaver", "E11-3moves", "P1"):
        "the event ends on patch 6, where Octave 1 at 0 is a level move,"
        " not the wire, so the output is not the source by design",
    ("Octaver", "E5-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (the octave leaves and comes back)",
    ("Octaver", "E9-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (the octave leaves and comes back)",
    ("Octaver", "E4-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step",
    ("Octaver", "E6-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (a patch change moves the levels)",
    ("Octaver", "E11-", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step",
    ("AnalogDelay", "E2-", "P4"):
        "reset_buffer restarts the modulation triangle (the node's"
        " state_init), so a modulated patch then matches a fresh instance,"
        " not the uninterrupted control",
    ("AnalogDelay", "E4-", "P4"):
        "a Mod Rate move shifts the free-running triangle; after a Time move"
        " and back, a 1-LSB rounding difference circulates in the feedback"
        " loop past tail_samples",
    ("AnalogDelay", "E6-", "P4"):
        "a patch change shifts the free-running triangle, or leaves a 1-LSB"
        " rounding difference circulating in the feedback loop past"
        " tail_samples",
    ("AnalogDelay", "E11-", "P4"):
        "a patch change shifts the free-running triangle, or leaves a 1-LSB"
        " rounding difference circulating in the feedback loop past"
        " tail_samples",
    ("TapeDelay", 'E1-', 'P4'):
        'reset() restarts the wow and flutter table, so the wobble is never in phase with a fresh instance again',
    ("TapeDelay", 'E2-', 'P4'):
        'a host reset_buffer restarts the wow and flutter table, so the wobble is never in phase with a fresh instance again',
    ("TapeDelay", 'E4-m0=0', 'P4'):
        "a Time move and back leaves other rounding in the loop than a fresh instance's; while material plays a 1 LSB difference can outlast tail_samples, which bounds silence",
    ("TapeDelay", 'E4-m0=', 'P5'):
        "varispeed bends the pitch on a Time move: a bend up past 1.5x steepens the triangle past P5's limit, and T1a's step clause holds (no click)",
    ("TapeDelay", 'E11-2macro', 'P5'):
        "varispeed bends the pitch on a Time move: a bend up past 1.5x steepens the triangle past P5's limit, and T1a's step clause holds (no click)",
    ("TapeDelay", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("TapeDelay", 'E4-m4=', 'P5'):
        "family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Wow: a balance move swaps the table's shape)",
    ("TapeDelay", 'E5-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("TapeDelay", 'E6-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("TapeDelay", 'E9-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("TapeDelay", 'E11-mix+patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix and a patch change)',
    ("TapeDelay", 'E11-2patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("TapeDelay", 'E11-3moves', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Time and a patch change)',
    # Reverb: the tank's int16 lines truncate on every write and its
    # filters run in float, so once two tanks have heard different material
    # they stay a few LSB apart under the same input for good (seen at Mod
    # Depth 0 too); a reset or a re-cut also restarts the modulation phase.
    ("Reverb", "E1-", "P4"): "a reset tank never re-converges byte for byte (int16 lines, free modulation phase)",
    ("Reverb", "E2-", "P4"): "a reset_buffer tank never re-converges byte for byte (int16 lines, free modulation phase)",
    ("Reverb", "E4-", "P4"): "a move that reaches the loop leaves the tank a few LSB off a fresh one for good",
    ("Reverb", "E6-", "P4"): "a patch move reaches the loop and leaves the tank a few LSB off a fresh one for good",
    # Vibrato and Fuzz: a reset is a fresh instance exactly (PR holds it);
    # it is the control that never was reset that the output does not meet
    # again (the classes' TheReset... tests).
    ("Vibrato", "E1-", "P4"): "reset() restarts the LFO as a fresh instance starts it, so the sweep never meets the uninterrupted control's phase again",
    # Tremolo the same way (ruled 2026-10-14): red at every E1 cell, both
    # placements, every rate, channel count and patch; PR stays live.
    ("Tremolo", "E1-", "P4"): "reset() restarts the LFO as a fresh instance starts it, so the throb never meets the uninterrupted control's phase again",
    ("Fuzz", "E1-", "P4"): "the 10.5 and 12.4 Hz coupling sections keep a few LSB of the material before a reset in float state for seconds, and the 36 dB stage raises it to a few hundred LSB (held under 1024)",
    ("Reverb", "E11-", "P4"): "moves that reach the loop leave the tank a few LSB off a fresh one for good",
    # The ruling of 2026-09-28, disclosed in the docstring's "Limits
    # shared by the family" (audiocomponents#117, audiodsp#180).
    ("Reverb", "E4-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E5-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E6-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E9-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E11-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("DigitalDelay", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("DigitalDelay", 'E4-m6=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Repeat Tone)',
    ("DigitalDelay", 'E4-m7=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Repeat Cut)',
    ("DigitalDelay", 'E5-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("DigitalDelay", 'E6-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("DigitalDelay", 'E9-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("DigitalDelay", 'E11-mix+patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix and a patch change)',
    ("DigitalDelay", 'E11-2patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("DigitalDelay", 'E11-3moves', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (the patch change; the Time moves glide)',
    ("SlapbackDelay", "E1-", "P4"):
        "a reset restarts the Wow wobble where a fresh instance's starts;"
        " the control never stopped, so its wobble is further along and"
        " with Wow above 0 the two never line up again (ok at Wow 0)",
    ("SlapbackDelay", "E2-", "P4"):
        "reset_buffer restarts the Wow wobble where a fresh instance's"
        " starts; the control never stopped, so its wobble is further along"
        " and with Wow above 0 the two never line up again (ok at Wow 0)",
    ("MultiTapDelay", "E1-", "P4"):
        "reset() empties both lines where the control's hold older laps; they"
        " die to 1 LSB inside tail_samples, and a 1-LSB rounding difference"
        " then circulates in the loop past it (silence reaches zero inside"
        " it)",
    ("MultiTapDelay", "E5-", "P4"):
        "a return from Mix 0 starts both lines empty where the control's hold"
        " older laps; they die to 1 LSB inside tail_samples, and a 1-LSB"
        " rounding difference then circulates in the loop past it",
    ("MultiTapDelay", "E9-", "P4"):
        "a return from Mix 0 starts both lines empty where the control's hold"
        " older laps; they die to 1 LSB inside tail_samples, and a 1-LSB"
        " rounding difference then circulates in the loop past it",
    ("MultiTapDelay", "E4-m4=", "P4"):
        "a return from Mix 0 starts both lines empty where the control's hold"
        " older laps; they die to 1 LSB inside tail_samples, and a 1-LSB"
        " rounding difference then circulates in the loop past it",
    ("MultiTapDelay", "E4-m6=", "P4"):
        "crossing Repeat Tone's out stop swaps the loop that makes the laps"
        " and empties the lap node going in; the old laps die to 1 LSB inside"
        " tail_samples, and a 1-LSB rounding difference then circulates past"
        " it",
    ("MultiTapDelay", "E6-", "P4"):
        "a patch change that crosses Repeat Tone's out stop empties the lap"
        " node going in; the old laps die to 1 LSB inside tail_samples, and a"
        " 1-LSB rounding difference then circulates past it",
    ("MultiTapDelay", "E11-", "P4"):
        "Mix 0 or a crossing of Repeat Tone's out stop empties a line; the old"
        " laps die to 1 LSB inside tail_samples, and a 1-LSB rounding"
        " difference then circulates past it",
    ("MultiTapDelay", "E4-m0=", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a Time move and back replays it",
    ("MultiTapDelay", "E6-", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a patch change and back replays it",
    ("MultiTapDelay", "E11-2patch", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a patch change and back replays it",
    ("MultiTapDelay", "E11-3moves", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a patch change and back replays it",
    ("ConvolutionReverb", 'E1-', 'P1'):
        'by design, disclosed: reset() empties the room, so the block in flight, 256 frames, comes out as exact zero, dry included',
    ("ConvolutionReverb", 'E2-', 'P1'):
        'by design, disclosed: a host reset_buffer resets the node, so the block in flight, 256 frames, comes out as exact zero, dry included',
    ("ConvolutionReverb", 'E4-m5=0', 'P1'):
        'by design, disclosed: Mix acts from the end of the block in flight, so the block after a move to Mix 0 comes out at the old Mix',
    ("ConvolutionReverb", 'E5-', 'P1'):
        'by design, disclosed: Mix acts from the end of the block in flight, so the block after a move to Mix 0 comes out at the old Mix',
    ("ConvolutionReverb", 'E4-m1=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Damping re-synthesizes the room)',
    ("ConvolutionReverb", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Predelay re-synthesizes the room)',
    ("ConvolutionReverb", 'E4-m4=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Room re-synthesizes the room)',
    ("ConvolutionReverb", 'E4-m5=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("ConvolutionReverb", 'E5-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("ConvolutionReverb", 'E6-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("ConvolutionReverb", 'E9-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("ConvolutionReverb", 'E11-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (two or three moves before one pull)',
    ("PingPongDelay", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    # ShimmerHall: its hall is the rebuilt Reverb, whose rows above say why
    # a tank that was emptied, or fed differently for a moment, never meets
    # an uninterrupted one byte for byte; and Bloom's shifter is a splice
    # shifter, whose output depends on where its read position sits in the
    # window (the ruling's N2). A reset renders exactly as a fresh instance
    # does (the class's reset test); it is the control that never was reset.
    # Flanger: the sweep is the node's own free-running triangle, so
    # anything that restarts it or runs it at another rate leaves it off
    # the uninterrupted control's phase for good; PR holds (a reset is a
    # fresh instance). P5 is the family limit the docstring discloses (N1).
    ("Flanger", "E1-", "P4"): "a reset starts the sweep again from Manual, so the class matches a fresh instance (PR), not the uninterrupted control",
    ("Flanger", "E2-", "P4"): "as E1: the host's reset of the node starts the sweep again",
    ("Flanger", "E4-m0=", "P4"): "a Rate move runs the free-running sweep at another rate, so its phase lands elsewhere; putting it back would jump the sweep",
    ("Flanger", "E4-m6=", "P4"): "Sync on runs the sweep at the tempo's rate, so its phase lands elsewhere (as m0)",
    ("Flanger", "E4-m7=", "P4"): "a Division move with Sync on runs the sweep at another rate (as m0)",
    ("Flanger", "E6-", "P4"): "a patch with another Rate or Sync moves the sweep's phase (as E4-m0)",
    ("Flanger", "E11-", "P4"): "moves before a pull that reach Rate or the patch move the sweep's phase (as E4-m0)",
    ("Flanger", "E4-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step",
    ("Flanger", "E5-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Mix)",
    ("Flanger", "E6-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (a patch change)",
    ("Flanger", "E9-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Mix)",
    ("Flanger", "E11-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (two or three moves before one pull)",
    ("ShimmerHall", "E1-", "P4"): "reset() empties the hall and restarts its modulation, and restarts the shifter's splice, so it never re-converges with the uninterrupted control (Reverb's E1 P4; the splice phase, N2)",
    ("ShimmerHall", "E4-m0=", "P4"): "Character re-cuts the wet chain, so it empties the hall and restarts the shifter's splice, and leaves the hall's tank off the control's for good (Reverb's E4 P4; the splice phase, N2)",
    ("ShimmerHall", "E4-m1=", "P4"): "Shimmer changes what enters the hall, so it leaves the hall's tank off the control's for good (Reverb's E4 P4)",
    ("ShimmerHall", "E4-m3=", "P4"): "Bloom changes what enters the hall, so it leaves the hall's tank off the control's for good (Reverb's E4 P4)",
    ("ShimmerHall", "E4-m4=", "P4"): "Interval runs the shifter's read position at another speed, so its splice phase lands elsewhere; putting it back would click (N2)",
    ("ShimmerHall", "E4-m6=", "P4"): "Size re-cuts the hall, so it leaves the hall's tank off the control's for good (Reverb's E4 P4)",
    ("ShimmerHall", "E4-m8=", "P4"): "Mix to 0 and back empties the hall, so it leaves the hall's tank off the control's for good (Reverb's E4 P4)",
    ("ShimmerHall", "E5-", "P4"): "Mix to 0 and back empties the hall and restarts its modulation and the shifter's splice (as E1; N2)",
    ("ShimmerHall", "E6-", "P4"): "a patch move reaches the hall's input or its tank, or the shifter's interval and splice, and leaves them off the control's for good (Reverb's E6 P4; N2)",
    ("ShimmerHall", "E9-", "P4"): "the E5 move: Mix to 0 and back empties the hall and restarts the shifter's splice (as E1; N2)",
    ("ShimmerHall", "E11-", "P4"): "moves that reach the hall, empty it, or move the shifter's interval or splice leave them off the control's for good (Reverb's E11 P4; N2)",
    ("ShimmerHall", "E4-m0=", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Character)",
    ("ShimmerHall", "E4-m3=", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Bloom)",
    ("ShimmerHall", "E4-m6=", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Size, which also empties the hall, as the docstring says); at the Rise defaults the hall sounds at once, so the jump lands on sound",
    ("ShimmerHall", "E4-m8=", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Mix); at the Rise defaults the hall sounds at once, so the jump lands on sound",
    ("ShimmerHall", "E5-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Mix)",
    ("ShimmerHall", "E6-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (a patch change)",
    ("ShimmerHall", "E9-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Mix)",
    ("ShimmerHall", "E11-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (two or three moves before one pull)",
    ("ShimmerHall", "E10-reset", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E10-mix0", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E10-macros", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E10-patch", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E12-p1", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E12-p2", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E12-p6", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E12-mix64", "P4", "circuitpython"): _SHIMMER_CP,
    ("ShimmerHall", "E12-mix127", "P4", "circuitpython"): _SHIMMER_CP,
    # AirSpace: its chamber is the rebuilt Reverb, whose rows above say why
    # a tank that was emptied, or moved in its loop, never meets an
    # uninterrupted one byte for byte. A reset renders exactly as a fresh
    # instance does (the class's TheReset tests); it is the control that
    # never was reset.
    ("AirSpace", "E1-", "P4"): "reset() empties the chamber and restarts its modulation, so it never re-converges with the uninterrupted control (Reverb's E1 P4)",
    ("AirSpace", "E4-", "P4"): "a move that reaches the tape's loop or the chamber's, or Mix to 0 and back, leaves the tank off the control's for good (Reverb's E4 P4)",
    ("AirSpace", "E5-", "P4"): "Mix to 0 and back empties the chamber and restarts its modulation (as E1)",
    ("AirSpace", "E9-", "P4"): "the E5 move: Mix to 0 and back empties the chamber (as E1)",
    ("AirSpace", "E6-", "P4"): "a patch move reaches the chamber's loop and leaves its tank off the control's for good (Reverb's E6 P4)",
    ("AirSpace", "E11-", "P4"): "moves that reach the chamber's loop or empty it leave its tank off the control's for good (Reverb's E11 P4)",
    ("AirSpace", "E4-m6=", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Top Cut)",
    ("AirSpace", "E5-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Mix)",
    ("AirSpace", "E6-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (a patch change)",
    ("AirSpace", "E9-", "P5"): "family limit, disclosed (N1): a control that jumps makes the output step (Mix)",
    # Saturation: its AC coupling (the plate pole, the playback head's, the
    # flux high-pass) is a pole at 5-20 Hz on a Q15 kernel, and once what
    # reaches it has differed, it carries a rounding residue of 1 to 2 LSB
    # that never re-converges while signal plays (measured 1.4 s on). Tone
    # and Speed moves, which reach only the shelves after it, re-converge
    # and stay live.
    ("Saturation", "E1-", "P4"): _SAT_COUPLING,
    ("Saturation", "E4-m0=", "P4"): _SAT_COUPLING,
    ("Saturation", "E4-m1=", "P4"): _SAT_COUPLING,
    ("Saturation", "E4-m2=0", "P4"): _SAT_COUPLING,
    ("Saturation", "E4-m3=", "P4"): _SAT_COUPLING,
    ("Saturation", "E4-m4=", "P4"): _SAT_COUPLING,
    ("Saturation", "E4-m7=", "P4"): _SAT_COUPLING,
    ("Saturation", "E5-", "P4"): _SAT_COUPLING,
    ("Saturation", "E6-", "P4"): _SAT_COUPLING,
    ("Saturation", "E9-", "P4"): _SAT_COUPLING,
    ("Saturation", "E10-", "P4"): _SAT_COUPLING,
    ("Saturation", "E11-", "P4"): _SAT_COUPLING,
    ("Saturation", "E12-", "P4"): _SAT_COUPLING,
    # DeEsser: PR holds a reset to a fresh instance byte for byte.
    ("DeEsser", "E1-", "P4"): "reset() clears the detector and the"
    " crossover, which come back to an uninterrupted instance's bytes"
    " within five blocks of the reset (7 LSB, then 3, 1, 1), on signal,"
    " whatever Release and Attack are; the audio tail is 256 as declared",
}

#: A control that jumps steps the output (the family's ruled disclosure,
#: audiocomponents#117): P5 at every event that moves a control.
for _name, _why in (
    ("AnalogDelay",
     "a control that jumps steps the output (family, audiocomponents#117);"
     " a Time move bends the pitch while the line walks, by design"),
    ("SlapbackDelay",
     "a control that jumps steps the output (family, audiocomponents#117):"
     " Level, Tone and patch moves have no ramp"),
    ("MultiTapDelay",
     "family limit, disclosed (audiocomponents#117): a control that jumps"
     " makes the output step (Time and Heads move every head to a new"
     " grid, Mix, Tilt and a patch change jump a level)"),
):
    for _event in CONTROL_EVENTS:
        DECLARED[(_name, _event, "P5")] = _why

#: At patches 1, 2, 5 and 6 Octave 1 at 0 is a level move, not the wire, so
#: P1 (Mix 0 is the source) does not apply there, on any event.
for _event in ("E1-", "E2-", "E4-", "E5-", "E6-", "E8-", "E9-", "E10-",
               "E11-", "E12-"):
    DECLARED[("Octaver", _event, "P1", (1, 2, 5, 6))] = (
        "at patches 1, 2, 5 and 6 Octave 2 is up or Direct is under 1, so"
        " Octave 1 at 0 is a level move, not the wire, and the output is"
        " not the source by design")

#: Cells that are not run at all on one interpreter, one row per (class or
#: adapter NAME, event name prefix, `sys.implementation.name`): reason. A
#: skipped cell prints `na(skip: <reason>)` on every property and builds
#: nothing. It is for a cell that cannot finish there, such as a node that
#: never returns from a pull, so that the rest of the matrix still runs; a
#: cell that finishes and is red belongs in DECLARED or KNOWN_RED instead.
SKIP = {
    ("NodeEcho", "E8-", "circuitpython"):
        "upstream's Echo never returns from a pull on a looped source that"
        " ends empty; audiodsp#242 fixed it on CPython and MicroPython",
    ("NodeMultiTapDelay", "E8-", "circuitpython"):
        "upstream's MultiTapDelay never returns from a pull on a looped"
        " source that ends empty (the E8 run spun past 590 s at v0.6.6rc4);"
        " CPython and MicroPython finish it",
    ("NodePitchShift", "E8-", "circuitpython"):
        "upstream's PitchShift never returns from a pull on a looped source"
        " that ends empty; audiodsp#243 fixed it on CPython and MicroPython",
    ("NodeGranularPitchShift", "E8-", "circuitpython"):
        "upstream's GranularPitchShift never returns from a pull on a looped"
        " source that ends empty; audiodsp#243 fixed it on CPython and"
        " MicroPython",
    ("NodeFlanger", "E8-", "circuitpython"):
        "upstream's Flanger never returns from a pull on a looped source"
        " that ends empty; audiodsp 7b fixed it on CPython and MicroPython",
    ("Flanger", "E8-", "circuitpython"):
        "the class is upstream's Flanger, which never returns from a pull on"
        " a looped source that ends empty; audiodsp 7b fixed it on CPython"
        " and MicroPython",
    ("ShimmerHall", "E8-", "circuitpython"):
        "Bloom pulls upstream's PitchShift, which never returns from a pull"
        " on a looped source that ends empty (audiodsp#243 fixed it on"
        " CPython and MicroPython)",
}

#: The SKIP rows above that are there only because CircuitPython's own Echo,
#: PitchShift, GranularPitchShift, Flanger and MultiTapDelay never return
#: from a pull on a looped source that ends empty. A CircuitPython built with
#: micropython-pydevices' patches/circuitpython/0008 and 0009 returns there,
#: and the host lifts these rows (`--empty-source-returns`) once it has seen the
#: binary return from such a pull; stock CircuitPython keeps them.
#: ShimmerHall keeps its row on every CircuitPython: its E8 cells return
#: there and pass P1 to P5, but once they run, 444 of the quick matrix's
#: later ShimmerHall cells render other bytes than they do with E8 skipped.
EMPTY_SOURCE_SKIPS = (
    ("NodeEcho", "E8-", "circuitpython"),
    ("NodePitchShift", "E8-", "circuitpython"),
    ("NodeGranularPitchShift", "E8-", "circuitpython"),
    ("NodeFlanger", "E8-", "circuitpython"),
    ("NodeMultiTapDelay", "E8-", "circuitpython"),
    ("Flanger", "E8-", "circuitpython"),
)

#: PR (a reset or a return from Mix 0 renders as a fresh instance) is
#: excused only here, never in DECLARED: a class NAME -> the free-running
#: phase that keeps it from matching a fresh instance, named (an LFO, a
#: wow table). A red PR cell of a class named here prints `decl`.
FREE_PHASE = {
    "PitchShifter": "the splice phase of CircuitPython's own PitchShift,"
                    " which a clear does not restart: a reset or a return"
                    " from Mix 0 leaves it where it was, and a fresh"
                    " instance starts at 0 (CPython and MicroPython match)",
}

if sys.implementation.name == "circuitpython":
    #: Harmonizer: CircuitPython's own audiodelays.PitchShift keeps its read
    #: and write positions through reset_buffer (audiodsp#240 is in
    #: audiodsp's port only), so after a reset or a return from Mix 0 the
    #: splices sit where they stood, not where a fresh instance's do. Named
    #: on CircuitPython alone: CPython and MicroPython keep PR live.
    FREE_PHASE["Harmonizer"] = ("CircuitPython's own PitchShift splice, kept"
                                " through reset_buffer")

if sys.implementation.name == "circuitpython":
    # CircuitPython only, so CPython and MicroPython keep PR live for the
    # class: its own PitchShift keeps its positions through a clear, so a
    # reset or a return from Mix 0 (each re-primes Bloom's shifter) sits at
    # another splice phase than a fresh instance (E5-mix0 and E10-mix0 at
    # patch 1, the Short Stagger).
    FREE_PHASE["ShimmerHall"] = (
        "the splice phase of CircuitPython's own PitchShift, which keeps"
        " its positions through a clear (audiodsp#240)")

SOURCE_KINDS = ("256", "100", "512", "1000", "raw")

#: Every property a cell can print.
ALL_PROPS = ("P1", "P2", "P3", "P4", "P5", "PD", "PF", "PR")


def _whole_event(prefix):
    """True when `prefix` names at least one whole event number and its
    dash: "E4-" and "E10-reset" do, "E" and "E1" do not."""
    if len(prefix) < 3 or prefix[0] != "E":
        return False
    i = 1
    while i < len(prefix) and "0" <= prefix[i] <= "9":
        i += 1
    return i > 1 and i < len(prefix) and prefix[i] == "-"


def declared_scope(key):
    """(patches or None, interpreters or None) of a DECLARED key."""
    patches = impls = None
    for scope in key[3:]:
        if isinstance(scope, tuple):
            patches = scope
        else:
            impls = tuple(scope.split(","))
    return patches, impls


def check_declared(table=None, free=None):
    """Refuse a malformed DECLARED row with a ValueError that says which.
    Run at import, and again by `run_class` for rows added since."""
    table = DECLARED if table is None else table
    free = FREE_PHASE if free is None else free
    for key in table:
        what = "lifecycle DECLARED row %r: " % (key,)
        if not isinstance(key, tuple) or len(key) < 3:
            raise ValueError(what + "a row is (NAME, event prefix, property"
                             "[, scope...])")
        name, prefix, prop = key[:3]
        if not _whole_event(prefix):
            raise ValueError(
                what + "the event prefix %r is shorter than one whole event"
                " name, so it would match events its reason does not"
                " describe; name each event (\"E4-\", \"E10-reset\")"
                % (prefix,))
        if prop not in ALL_PROPS:
            raise ValueError(what + "no property %r" % (prop,))
        if prop == "PR":
            raise ValueError(what + "PR is excused only by FREE_PHASE, "
                             "which names the free-running phase")
        kinds = []
        for scope in key[3:]:
            if isinstance(scope, tuple):
                kinds.append("patches")
                for patch in scope:
                    if patch is not None and not isinstance(patch, int):
                        raise ValueError(what + "a patch scope holds patch"
                                         " numbers or None, not %r"
                                         % (patch,))
            elif isinstance(scope, str):
                kinds.append("interpreters")
                for impl in scope.split(","):
                    if impl not in IMPLS:
                        raise ValueError(what + "no interpreter %r (%s)"
                                         % (impl, ", ".join(IMPLS)))
            else:
                raise ValueError(what + "a scope is a tuple of patches or"
                                 " a string of interpreters, not %r"
                                 % (scope,))
        if len(kinds) != len(set(kinds)):
            raise ValueError(what + "each kind of scope at most once")
    for name, phase in free.items():
        if not isinstance(phase, str) or not phase.strip():
            raise ValueError("lifecycle FREE_PHASE[%r] must name the "
                             "free-running phase" % (name,))


check_declared()


# --------------------------------------------------------------------------
# Material


def _lcg(state):
    return (1103515245 * state + 12345) & 0x7FFFFFFF


def click_noise(frames, channels, spacing=64, seed=12345):
    """Clicks every `spacing` frames, each at its own amplitude (and the
    second channel at a different one), with an LCG noise burst in the
    middle eighth: a frame lost, repeated or swapped is visible."""
    values = array("h", bytes(2 * frames * channels))
    state = seed
    for frame in range(3, frames, spacing):
        state = _lcg(state)
        amp = 2000 + (state >> 8) % 24000
        if (state >> 4) & 1:
            amp = -amp
        values[frame * channels] = amp
        if channels == 2:
            values[frame * channels + 1] = -(amp // 2) - 7
    lo = frames // 2
    for frame in range(lo, lo + frames // 8):
        for channel in range(channels):
            state = _lcg(state)
            values[frame * channels + channel] = ((state >> 8) % 16001) - 8000
    return values


def triangle(frames, channels, rate, amp=12000, hz=100):
    """An integer triangle: the same bytes on every interpreter, and its
    largest step is small (4 * amp * hz / rate)."""
    values = array("h", bytes(2 * frames * channels))
    period = rate // hz
    for frame in range(frames):
        phase = (frame % period) * 4 * amp // period
        if phase < amp:
            value = phase
        elif phase < 3 * amp:
            value = 2 * amp - phase
        else:
            value = phase - 4 * amp
        for channel in range(channels):
            values[frame * channels + channel] = value
    return values


def _raw(values, rate, channels):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def _adapter(values, rate, channels, frames, loop):
    """A RawSample handed out `frames` at a time: the house re-blocker.
    With loop False it pads silence after the material, for ever."""
    block = audiofilters.Filter(filter=None, mix=1.0,
                                buffer_size=frames * channels * 2,
                                sample_rate=rate, channel_count=channels)
    block.play(_raw(values, rate, channels), loop=loop)
    return block


class Feed:
    """The source a class is built around: a Port the host re-points.

    `mat` is the material, `sil` silence, `empty` a sample that hands back
    an empty buffer (the only way a native source can run dry). A Port
    moves no bytes, so a class sees exactly what the source behind it
    hands."""

    def __init__(self, values, rate, channels, kind, loop):
        self.rate = rate
        self.channels = channels
        if kind == "raw":
            self.mat = _raw(values, rate, channels)
        else:
            self.mat = _adapter(values, rate, channels, int(kind), loop)
        self.sil = _adapter(array("h", bytes(4 * channels * BLOCK)), rate,
                            channels, BLOCK, True)
        # MicroPython's RawSample refuses an empty array but takes an
        # empty 16-bit memoryview.
        self.empty = _raw(memoryview(array("h", [0, 0]))[0:0], rate,
                          channels)
        self.port = Port(self.mat)
        self.current = self.mat
        self.sample_rate = rate
        self.channel_count = channels

    def point(self, node):
        self.current = node
        self.port.play(node)


# --------------------------------------------------------------------------
# Bytes


ZERO = bytes(BLOCK * 2 * 2 * 8)


def _is_zero(data):
    step = len(ZERO)
    for lo in range(0, len(data), step):
        chunk = data[lo:lo + step]
        if chunk != ZERO[:len(chunk)]:
            return False
    return True


def _samples(data):
    out = array("h")
    try:
        out.frombytes(bytes(data))
        return out
    except AttributeError:
        pass
    import struct
    out.extend(struct.unpack("<%dh" % (len(data) // 2), bytes(data)))
    return out


def _first_diff(a, b, lo, hi):
    """First byte index in [lo, hi) where a and b differ, or -1."""
    step = 4096
    pos = lo
    while pos < hi:
        end = min(hi, pos + step)
        if a[pos:end] != b[pos:end]:
            for i in range(pos, end):
                if a[i] != b[i]:
                    return i
        pos = end
    return -1


def _last_diff(a, b, lo, hi):
    """Last byte index in [lo, hi) where a and b differ, or -1."""
    step = 4096
    end = hi
    while end > lo:
        pos = max(lo, end - step)
        if a[pos:end] != b[pos:end]:
            for i in range(end - 1, pos - 1, -1):
                if a[i] != b[i]:
                    return i
        end = pos
    return -1


def _max_step(values, channels, lo, hi):
    top = 0
    for ch in range(channels):
        prev = None
        for i in range(lo * channels + ch, hi * channels, channels):
            v = values[i]
            if prev is not None:
                d = v - prev
                if d < 0:
                    d = -d
                if d > top:
                    top = d
            prev = v
    return top


def _max_gap(a, b, channels, lo, hi):
    """The largest distance between two renders over frames lo..hi."""
    top = 0
    for i in range(lo * channels, min(hi * channels, len(a), len(b))):
        d = a[i] - b[i]
        if d < 0:
            d = -d
        if d > top:
            top = d
    return top


# --------------------------------------------------------------------------
# The class under test


def _starts(text, prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False


def mix_index(cls):
    name = cls.NAME
    if name in MIX_INDEX:
        return MIX_INDEX[name]
    if name in DEPTH_INDEX:
        return DEPTH_INDEX[name]
    if name in PLANT_DEPTH_INDEX:
        return PLANT_DEPTH_INDEX[name]
    labels = cls.MACRO_LABELS
    for i in range(len(labels)):
        if labels[i] == "Mix":
            return i
    return None


def is_depth(cls):
    """True when the class's wire is a depth, judged by the depth model."""
    return cls.NAME in DEPTH_INDEX or cls.NAME in PLANT_DEPTH_INDEX


def _not_a_wire(cls, ev, patch, options):
    """Why a depth at 0 is not a byte compare in this cell, or None: the
    cell builds the class at `patch`, takes the event's moves, and every
    setting it stands at is held to `DEPTH_NOT_A_WIRE`."""
    rows = DEPTH_NOT_A_WIRE.get(cls.NAME)
    if not rows:
        return None
    feed = Feed(material_for("once", 48000, 1), 48000, 1, "256", loop=False)
    e = _build(cls, feed, 48000, patch, options, False)
    try:
        ctx = Ctx(e, patch)
        for step in (None, ev.away, ev.back):
            if step:
                act(e, feed, ctx, step)
            for index, low, why in rows:
                if e.get_macro(index) >= low:
                    return why
    finally:
        e.deinit()
    return None


def stops(cls, index):
    mode = cls.MACRO_MODES.get(index, "UNIPOLAR")
    if mode == "BIPOLAR":
        return (0, 64, 127)
    return (0, 127)


class Ctx:
    """What one instance needs to undo a move: the patch it was built at,
    or its macros' exact positions at the default."""

    def __init__(self, e, patch):
        self.patch = patch
        self.positions = list(e._macros)
        self.midi = [e.get_macro(i) for i in range(len(self.positions))]
        self.inexact = 0


def restore(e, ctx):
    if ctx.patch is not None:
        e.program_change(ctx.patch)
        return
    for i in range(len(ctx.midi)):
        e.set_macro(i, ctx.midi[i])
    # set_macro(get_macro()) is not always bit-exact at the constructor's
    # unquantised defaults; land exactly, so P4 measures the event and not
    # the width of a float, and count it.
    for i in range(len(ctx.positions)):
        if e._macros[i] != ctx.positions[i]:
            ctx.inexact += 1
            e._macros[i] = ctx.positions[i]
            e._apply_macro(i, ctx.positions[i])


def act(e, feed, ctx, actions):
    for a in actions:
        op = a[0]
        if op == "reset":
            e.reset()
        elif op == "rb":
            audiocore.reset_buffer(e.output)
        elif op == "macro":
            e.set_macro(a[1], a[2])
        elif op == "patch":
            e.program_change(a[1])
        elif op == "mixto":
            # Land exactly where a constructor given the same value lands,
            # so the fresh instance E12 compares with stands at the same
            # position, not one float step away.
            e.set_macro(a[1], a[2])
            want = fresh_position(type(e), a[1], a[2])
            if e._macros[a[1]] != want:
                e._macros[a[1]] = want
                e._apply_macro(a[1], want)
        elif op == "restore":
            restore(e, ctx)
        elif op == "end":
            feed.point(feed.empty)
        else:
            raise ValueError(op)


class Event:
    """`away` before pull K0 (or before the first pull when `first`),
    `back` GAP pulls later (in the same gap when `first`)."""

    def __init__(self, name, away, back=None, kind="256", moves_mix=False,
                 control_move=True, post0=False, first=False, gap=GAP,
                 fresh=None, landing=False):
        self.name = name
        #: E12: the constructor keywords of the fresh instance the cell is
        #: judged against, in place of the uninterrupted control.
        self.fresh = fresh
        #: PR: True when the cell's last action lands the class on a state
        #: a fresh instance can be built at ("reset": patch 0; "config": the
        #: configuration the cell runs at).
        self.landing = landing
        self.away = away
        self.back = back or []
        self.kind = kind
        self.moves_mix = moves_mix
        self.control_move = control_move
        self.post0 = post0
        self.first = first
        self.gap = gap


def events(cls, patch, quick=False):
    """Every event for `cls` at `patch` (None: the constructor defaults)."""
    mix = mix_index(cls)
    labels = cls.MACRO_LABELS
    npatch = len(cls.PATCHES)
    full = (not quick) or patch is None
    out = [
        Event("E1-reset@block", [("reset",)], kind="256",
              control_move=False, post0=True, landing="reset"),
        Event("E1-reset@part", [("reset",)], kind="100",
              control_move=False, post0=True),
        Event("E2-reset_buffer", [("rb",)], control_move=False),
    ]
    if full:
        for i in range(len(labels)):
            for v in stops(cls, i):
                out.append(Event("E4-m%d=%d" % (i, v), [("macro", i, v)],
                                 [("restore",)], moves_mix=(i == mix)))
    if mix is not None:
        out.append(Event("E5-mix0", [("macro", mix, 0)], [("restore",)],
                         moves_mix=True, gap=6, landing="config"))
    targets = range(npatch) if full else (0, npatch - 1)
    for q in targets:
        if q == patch:
            continue
        out.append(Event("E6-p%d" % q, [("patch", q)], [("restore",)],
                         moves_mix=True))
    out.append(Event("E8-end", [("end",)], kind="100", control_move=False))
    for kind in SOURCE_KINDS:
        if mix is not None:
            out.append(Event("E9-src%s" % kind, [("macro", mix, 0)],
                             [("restore",)], kind=kind, moves_mix=True,
                             gap=6))
    out.append(Event("E10-reset", [("reset",)], control_move=False,
                     post0=True, first=True, landing="reset"))
    if full:
        out.append(Event("E10-macros",
                         [("macro", i, 127) for i in range(len(labels))],
                         [("restore",)], moves_mix=True, first=True))
    if mix is not None:
        out.append(Event("E10-mix0", [("macro", mix, 0)], [("restore",)],
                         moves_mix=True, first=True, landing="config"))
    out.append(Event("E10-patch", [("patch", npatch - 1 if patch != npatch - 1
                                    else 0)], [("restore",)],
                     moves_mix=True, first=True))
    if full and labels:
        out.append(Event("E11-2macro", [("macro", 0, 0), ("macro", 0, 127)],
                         [("restore",)], moves_mix=(mix == 0)))
        if mix is not None:
            out.append(Event("E11-mix+patch",
                             [("macro", mix, 0), ("patch", npatch - 1)],
                             [("restore",)], moves_mix=True))
    if full:
        out.append(Event("E11-2patch", [("patch", npatch - 1), ("patch", 0)],
                         [("restore",)], moves_mix=True))
    if full and labels:
        out.append(Event("E11-3moves",
                         [("macro", 0, 0), ("macro", 0, 127),
                          ("patch", npatch - 1)],
                         [("restore",)], moves_mix=True))
    if patch is None:
        # A move before the first pull that stays, against an instance
        # built there: each patch, and Mix to 0, 64 and 127.
        for q in sorted(cls.PATCHES):
            out.append(Event("E12-p%d" % q, [("patch", q)], moves_mix=True,
                             first=True, fresh={"patch": q}))
        if mix is not None:
            for v in (0, 64, 127):
                out.append(Event("E12-mix%d" % v, [("mixto", mix, v)],
                                 moves_mix=True, first=True,
                                 fresh={"mix": v}))
    return out


# --------------------------------------------------------------------------
# Rendering


def fresh_position(cls, index, midi):
    """The 0..1 position a constructor lands macro `index` on when handed
    the value MIDI `midi` stands for."""
    span = cls._MACRO_RANGES[index]
    value = _component.macro_value(span, _component.position_of_midi(
        cls.MACRO_MODES.get(index, "UNIPOLAR"), midi))
    return _component.macro_position(span, value)


#: The constructor keyword of a class's wet/dry control, where it is not
#: `mix`.
MIX_KEYWORD = {
    "SlapbackDelay": "level",
    "Octaver": "octave1",
    "AutoPan": "depth",
    "Tremolo": "depth",
    "Notch": "depth",
    "DeEsser": "range_db",
    "NoiseGate": "range_db",
    "Expander": "depth_db",
}


def build_fresh(cls, feed, rate, options, fresh):
    """A fresh instance built at `fresh`: {"patch": q} is the constructor's
    `patch=q`, {"mix": v} its Mix keyword at the value MIDI v stands for,
    and {} the defaults. Raises TypeError when the constructor takes no
    such keyword."""
    keywords = dict(options)
    if "patch" in fresh and fresh["patch"] is not None:
        keywords["patch"] = fresh["patch"]
    if "mix" in fresh:
        index = mix_index(cls)
        span = cls._MACRO_RANGES[index]
        keywords[MIX_KEYWORD.get(cls.NAME, "mix")] = _component.macro_value(
            span, _component.position_of_midi(
                cls.MACRO_MODES.get(index, "UNIPOLAR"), fresh["mix"]))
    e = cls(feed.port, sample_rate=rate, **keywords)
    if "mix" in fresh:
        index = mix_index(cls)
        if e._macros[index] != fresh_position(cls, index, fresh["mix"]):
            e.deinit()
            raise TypeError("the constructor's %s did not land on Mix %d"
                            % (MIX_KEYWORD.get(cls.NAME, "mix"),
                               fresh["mix"]))
    return e


def _build(cls, feed, rate, patch, options, post0=False):
    e = cls(feed.port, sample_rate=rate, **options)
    if patch is not None:
        e.program_change(patch)
    if post0:
        e.program_change(0)
    return e


def _pull(e, out):
    """One host pull, appended as the class handed it. An empty pull adds
    nothing; the caller counts them."""
    data = bytes(audiocore.get_buffer(e.output)[1])
    out.extend(data)
    return len(data)


def _pull_to(e, out, nbytes, fsize):
    """Pull until `out` holds `nbytes`. 64 empty pulls in a row is a source
    that has ended at Mix 0: silence from there, which is what a host
    playing it hears."""
    empties = 0
    while len(out) < nbytes:
        if _pull(e, out) == 0:
            empties += 1
            if empties >= 64:
                out.extend(bytes(nbytes - len(out)))
                return True
        else:
            empties = 0
    return False


def _tail(e):
    t = e.tail_samples
    return t


class Control:
    """A control instance per (kind, material, rate, channels, patch,
    post0), rendered lazily and shared by every cell that needs it."""

    def __init__(self, cls, rate, channels, patch, options, kind, material,
                 post0):
        values = material_for(material, rate, channels)
        self.feed = Feed(values, rate, channels, kind,
                         loop=(material == "loop"))
        self.e = _build(cls, self.feed, rate, patch, options, post0)
        self.out = bytearray()
        self.fsize = 2 * channels
        self.ended = False

    def upto(self, frames):
        nbytes = frames * self.fsize
        if len(self.out) < nbytes and not self.ended:
            self.ended = _pull_to(self.e, self.out, nbytes, self.fsize)
        return self.out

    def close(self):
        self.e.deinit()


_MATERIAL = {}


def material_for(which, rate, channels):
    key = (which, rate, channels)
    if key not in _MATERIAL:
        if which == "loop":
            _MATERIAL[key] = click_noise(2400, channels, spacing=150,
                                         seed=777)
        elif which == "once":
            _MATERIAL[key] = click_noise(8192, channels)
        elif which == "tri":
            _MATERIAL[key] = triangle(8192, channels, rate)
        elif which == "loud":
            # Loud from the first frame, and never sparse: a level that
            # lands late in the Mixer has something to scale in every
            # block. 2400 frames is whole periods at 100 Hz and 48 kHz.
            _MATERIAL[key] = triangle(2400, channels, rate, amp=24000)
        else:
            raise ValueError(which)
    return _MATERIAL[key]


def _schedule_run(e, feed, ctx, ev, out, fsize, upto_frames, mixfix=None):
    """Pull to `upto_frames`, taking `ev.away` before pull K0 (or before
    the first pull) and `ev.back` `ev.gap` pulls later. Returns the frame
    positions the actions landed at."""
    at = []
    ctx.lats = []
    k0 = 0 if ev.first else K0
    kb = k0 if ev.first else k0 + ev.gap
    k = 0
    nbytes = upto_frames * fsize
    empties = 0
    while len(out) < nbytes:
        if k == k0:
            at.append(len(out) // fsize)
            act(e, feed, ctx, ev.away)
            if mixfix:
                mixfix(e)
            ctx.lats.append(e.latency_samples)
        if k == kb and ev.back:
            if kb != k0:
                at.append(len(out) // fsize)
            act(e, feed, ctx, ev.back)
            if mixfix:
                mixfix(e)
            if kb != k0:
                ctx.lats.append(e.latency_samples)
        if _pull(e, out) == 0:
            empties += 1
            if empties >= 64:
                out.extend(bytes(nbytes - len(out)))
                break
        else:
            empties = 0
        k += 1
    ctx.pulls = k
    return at


# --------------------------------------------------------------------------
# The properties


def p1(cls, ev, rate, channels, patch, options):
    """At Mix 0 the output is the source, byte for byte, on time."""
    mix = mix_index(cls)
    if mix is None:
        return "na"
    if ev.name.startswith("E4-m%d=" % mix) and not ev.name.endswith("=0"):
        return "na"
    if _starts(ev.name, ("E10-mix", "E12-mix")):
        return "na"
    why = _not_a_wire(cls, ev, patch, options) if is_depth(cls) else None
    if why is not None:
        return "na(not a wire: %s)" % why.replace("|", "/")[:60]
    values = material_for("once", rate, channels)
    feed = Feed(values, rate, channels, ev.kind, loop=False)
    e = _build(cls, feed, rate, patch, options, False)
    ctx = Ctx(e, patch)
    fsize = 2 * channels
    if _starts(ev.name, ("E5", "E4-m%d=0" % mix)):
        # The event itself takes Mix to 0: judge the stretch it holds it.
        mixfix = None
        window = None
    else:
        e.set_macro(mix, 0)

        def mixfix(effect):
            effect.set_macro(mix, 0)
        window = "all"
    if ev.name.startswith("E9"):
        # E9's P1 is the baseline: Mix 0 from the start, no move, this
        # source shape.
        ev = Event(ev.name, [], kind=ev.kind)
    out = bytearray()
    total = (K0 + 8 + 8) * BLOCK
    try:
        at = _schedule_run(e, feed, ctx, ev, out, fsize, total, mixfix)
        lat = e.latency_samples
    finally:
        e.deinit()
    expect = bytes(values)
    if ev.kind == "raw":
        total = min(total, len(values) // channels)
    if window == "all":
        lo, hi = 0, total
    else:
        if not at:
            return "na"
        lo = at[0]
        hi = at[1] if len(at) > 1 else total
        if ev.first:
            return "na"
        # Mix 0's own latency, read while the event holds it there.
        lat = ctx.lats[0]
    shifted = bytes(lat * fsize) + expect
    shifted = shifted + bytes(max(0, total * fsize - len(shifted)))
    d = _first_diff(out, shifted, lo * fsize, hi * fsize)
    if d < 0:
        return "ok"
    frame = d // fsize
    if ev.name.startswith("E8-end") and at and frame >= at[0]:
        # The source's frames up to where it ended (it may have handed
        # some past the pull it ended at), then silence.
        if _is_zero(out[d:hi * fsize]):
            return "ok"
    return "RED(first wrong frame %d%s)" % (frame - lo, _diagnose(
        out, shifted, frame, fsize, hi))


def _diagnose(out, expect, frame, fsize, hi):
    """Where the wrong frame's run came from in the source."""
    want = out[frame * fsize:(frame + 16) * fsize]
    if want == bytes(len(want)):
        return ", silence"
    for off in range(1, 4097):
        for sign in (1, -1):
            src = frame + sign * off
            if src < 0:
                continue
            if expect[src * fsize:(src + 16) * fsize] == want:
                if sign > 0:
                    return ", %d frames of source lost" % off
                return ", %d frames of source repeated" % off
    return ", not the source near there"


def _decl(cls, ev, prop, patch=None, impl=None):
    """True when a DECLARED row covers this cell: its class, property and
    event prefix, and its scopes, if it has any, hold `patch` (None: the
    defaults) and this interpreter."""
    impl = impl or sys.implementation.name
    for key in DECLARED:
        name, prefix, p = key[:3]
        if name != cls.NAME or p != prop or not ev.name.startswith(prefix):
            continue
        patches, impls = declared_scope(key)
        if patches is not None and patch not in patches:
            continue
        if impls is not None and impl not in impls:
            continue
        return True
    return False


def main_render(cls, ev, rate, channels, patch, options, controls):
    """P2, P3, P4 from one instance, against a shared control."""
    fsize = 2 * channels
    res = {}
    # E12 moves a control before the first pull and judges the first block,
    # so its source must already be loud there.
    values = material_for("loud" if ev.fresh is not None else "loop", rate,
                          channels)
    feed = Feed(values, rate, channels, ev.kind, loop=True)
    e = _build(cls, feed, rate, patch, options, False)
    ctx = Ctx(e, patch)
    ctx.cls = cls
    ctx.options = options
    # The control is rendered in step with the instance, pull for pull,
    # and compared as it goes: nothing tail-long is kept.
    cfeed = Feed(values, rate, channels, ev.kind, loop=True)
    c = None
    if ev.fresh is not None:
        # E12: judged against an instance built at the move's setting.
        try:
            c = build_fresh(cls, cfeed, rate, options, ev.fresh)
        except TypeError as err:
            res["P4"] = res["PF"] = "na(no fresh build: %s)" % (
                str(err).replace("|", "/")[:60])
    if c is None:
        c = _build(cls, cfeed, rate, patch, options, ev.post0)
    try:
        out = bytearray()
        at = _schedule_run(e, feed, ctx, ev, out, fsize,
                           ((0 if ev.first else K0) + ev.gap + 1) * BLOCK)
        cout = bytearray()
        for k in range(ctx.pulls):
            if k == K0 and ev.name.startswith("E8-end"):
                # The control's source goes silent where the instance's
                # ended, and stays silent.
                cfeed.point(cfeed.sil)
            _pull(c, cout)
        if ev.fresh is not None and "PF" not in res:
            # The first block: the move must already have landed in it.
            n = BLOCK * fsize
            d = _first_diff(out, cout, 0, min(n, len(out), len(cout)))
            res["PF"] = "ok" if d < 0 else (
                "RED(first block differs from a fresh instance's at"
                " frame %d)" % (d // fsize))
        last = at[-1] if at else 0
        tail = _tail(e)
        lat = e.latency_samples
        if tail is None:
            res["P4"] = "na(tail None)"
            bound = last + BLOCK + lat
        else:
            bound = last + tail + lat + BLOCK
        stop = bound + MARGIN
        verdict, crc, s0 = _p4_stream(e, c, out, cout, last, bound, stop,
                                      fsize)
        if "P4" not in res:
            res["P4"] = verdict
        out = None
        # P2: silence in, silence out after the tail.
        feed.point(feed.sil)
        tail = _tail(e)
        if ev.kind == "raw":
            # A whole RawSample is one buffer the class may still be
            # playing through: the input is not silent until it has.
            res["P2"] = "na(whole RawSample)"
            wait = (tail or NO_TAIL_WAIT) + lat + BLOCK + MARGIN
        elif tail is None:
            res["P2"] = "na(tail None)"
            wait = NO_TAIL_WAIT
        else:
            # Silence starts once the class has used the source buffer it
            # was handed last.
            b2 = s0 + tail + lat + BLOCK + int(ev.kind)
            # Streamed: only the frames P2 reads are kept.
            crc, left = _stream(e, (b2 - s0) * fsize, crc)
            out = bytearray(left)
            _pull_to(e, out, MARGIN * fsize, fsize)
            out = out[:MARGIN * fsize]
            crc = binascii.crc32(bytes(out), crc)
            res["P2"] = _zero_after(out, 0, MARGIN, fsize, s0 - b2)
            wait = tail + lat + BLOCK + MARGIN
        res["h"] = "%08x" % (crc & 0xFFFFFFFF)
        # P3: an event during silence plays nothing. Not for a whole
        # RawSample, whose one buffer the class may hold part of.
        if ev.kind == "raw":
            res["P3"] = "na(whole RawSample)"
        else:
            res["P3"] = _p3(e, feed, ctx, ev, fsize, wait)
    finally:
        e.deinit()
        c.deinit()
    return res


def _pull_some(x, fsize):
    """One pull that hands back bytes: 64 empty pulls in a row are a block
    of silence."""
    for _ in range(64):
        data = bytes(audiocore.get_buffer(x.output)[1])
        if data:
            return data
    return bytes(BLOCK * fsize)


def _p4_stream(e, c, out, cout, last, bound, stop, fsize):
    """P4, streamed: the instance's and the control's bytes compared as
    they are pulled, from the last move to `stop`. Returns the verdict,
    the CRC of every byte the instance handed, and its frame count."""
    crc = binascii.crc32(bytes(out))
    base = 0
    lo = last * fsize
    hi = stop * fsize
    lastdiff = -1
    while base < hi:
        if not out:
            data = _pull_some(e, fsize)
            crc = binascii.crc32(data, crc)
            out = bytearray(data)
        if not cout:
            cout = bytearray(_pull_some(c, fsize))
        n = min(len(out), len(cout), hi - base)
        a = out[:n]
        b = cout[:n]
        if base + n > lo and a != b:
            d = _last_diff(a, b, max(0, lo - base), n)
            if d >= 0:
                lastdiff = base + d
        out = out[n:]
        cout = cout[n:]
        base += n
    s0 = (base + len(out)) // fsize
    if lastdiff < 0 or lastdiff // fsize < bound:
        return "ok", crc, s0
    return ("RED(differs at +%d, bound +%d)" % (lastdiff // fsize - last,
                                               bound - last), crc, s0)


def _stream(e, nbytes, crc):
    """Pull `nbytes` without keeping them, folded into `crc`. Returns the
    crc and the bytes the last pull handed past `nbytes`."""
    got = 0
    empties = 0
    while got < nbytes:
        data = bytes(audiocore.get_buffer(e.output)[1])
        if not data:
            empties += 1
            if empties >= 64:
                data = bytes(nbytes - got)
            else:
                continue
        empties = 0
        take = min(len(data), nbytes - got)
        crc = binascii.crc32(data[:take], crc)
        got += take
        if take < len(data):
            return crc, data[take:]
    return crc, b""


def _zero_after(out, lo, hi, fsize, s0):
    seg = out[lo * fsize:hi * fsize]
    if _is_zero(seg):
        return "ok"
    vals = _samples(seg)
    top = 0
    first = -1
    for i in range(len(vals)):
        v = vals[i]
        if v:
            if first < 0:
                first = i
            if v < 0:
                v = -v
            if v > top:
                top = v
    return "RED(peak %d at +%d after input end, bound +%d)" % (
        top, lo - s0 + first // (fsize // 2), lo - s0)


def _p3(e, feed, ctx, ev, fsize, wait):
    """Ring on the material, take the move away as the input stops, wait
    for the output to reach exact silence, take the move back: the four
    blocks after it are exactly zero. A single action is taken in the
    silence instead."""
    out = bytearray()
    if ev.first:
        if not ev.back:
            return "na"
        # The first-pull variant: the move away before anything is pulled,
        # a fresh instance, the material through it, then silence.
        e = _build(ctx.cls, feed, feed.rate, ctx.patch, ctx.options, False)
        ctx = Ctx(e, ctx.patch)
        act(e, feed, ctx, ev.away)
    feed.point(feed.mat)
    try:
        return _p3_body(e, feed, ctx, ev, fsize, wait, out)
    finally:
        if ev.first:
            e.deinit()


def _p3_body(e, feed, ctx, ev, fsize, wait, out):
    _pull_to(e, out, 8 * BLOCK * fsize, fsize)
    feed.point(feed.sil)
    if ev.back and not ev.first:
        act(e, feed, ctx, ev.away)
    blk = BLOCK * fsize
    # Wait the whole tail, not only for a quiet stretch: a delay is quiet
    # between the input and its first repeat.
    tail = _tail(e)
    hold = BLOCK if ev.kind == "raw" else int(ev.kind)
    if tail is None:
        need = max(wait, NO_TAIL_WAIT)
    else:
        need = max(wait, tail + e.latency_samples + BLOCK + hold + MARGIN)
    _crc, left = _stream(e, (need - 8 * BLOCK) * fsize, 0)
    seg = bytearray(left)
    _pull_to(e, seg, 8 * blk, fsize)
    if not _is_zero(seg):
        return "na(never silent)"
    if ev.back:
        act(e, feed, ctx, ev.back)
    else:
        act(e, feed, ctx, ev.away)
    seg = bytearray()
    _pull_to(e, seg, 4 * blk, fsize)
    if _is_zero(seg):
        return "ok"
    vals = _samples(seg)
    top = 0
    first = -1
    for i in range(len(vals)):
        v = vals[i]
        if v:
            if first < 0:
                first = i
            if v < 0:
                v = -v
            if v > top:
                top = v
    return "RED(peak %d from silence, first at +%d)" % (
        top, first // (fsize // 2))


def p5(cls, ev, rate, channels, patch, options, controls):
    """No step at the move larger than 1.5 x the larger of the material's
    and the control's own largest step, on a triangle."""
    if not ev.control_move or ev.first:
        return "na"
    fsize = 2 * channels
    values = material_for("tri", rate, channels)
    key = ("tri", ev.kind, rate, channels, patch)
    ctl = controls.get(key)
    if ctl is None:
        ctl = Control(cls, rate, channels, patch, options, ev.kind, "tri",
                      False)
        controls[key] = ctl
    total = (K0 + ev.gap + 6) * BLOCK
    feed = Feed(values, rate, channels, ev.kind, loop=False)
    e = _build(cls, feed, rate, patch, options, False)
    ctx = Ctx(e, patch)
    out = bytearray()
    try:
        at = _schedule_run(e, feed, ctx, ev, out, fsize, total)
    finally:
        e.deinit()
    ref = _samples(bytes(ctl.upto(total)[:total * fsize]))
    got = _samples(bytes(out[:total * fsize]))
    own = _max_step(values, channels, 0, total)
    base = max(own, _max_step(ref, channels, 0, total))
    limit = base * STEP_NUM // STEP_DEN
    depth = is_depth(cls) and any(
        a[0] == "macro" and a[1] == mix_index(cls) for a in ev.away)
    worst = 0
    where = 0
    for a in at:
        lo = max(0, a - 1)
        hi = min(total, a + BLOCK + 64)
        s = _max_step(got, channels, lo, hi)
        if depth:
            # A depth jumps, and the jump steps the output by as far as the
            # class's output stands from the dry there: no more.
            s -= _max_gap(ref, values, channels, lo, hi)
        if s > worst:
            worst = s
            where = a
    if worst <= limit:
        return "ok"
    return "RED(step %d at %d, limit %d)" % (worst, where, limit)


def e3(cls, rate, channels, patch, options):
    """deinit(): the source still renders, the surface raises, a second
    deinit is harmless."""
    fsize = 2 * channels
    values = material_for("loop", rate, channels)
    feed = Feed(values, rate, channels, "256", loop=True)
    e = _build(cls, feed, rate, patch, options, False)
    out = bytearray()
    _pull_to(e, out, K0 * BLOCK * fsize, fsize)
    e.deinit()
    res = {}
    try:
        got = bytes(audiocore.get_buffer(feed.port)[1])
        res["P1"] = "ok" if len(got) == BLOCK * fsize else (
            "RED(source handed %d bytes)" % len(got))
    except Exception as err:                        # noqa: BLE001
        res["P1"] = "RED(source: %s)" % type(err).__name__
    quiet = []
    for name in sorted(dir(type(e))):
        if name.startswith("_") or name.upper() == name or name in (
                "deinit", "create"):
            continue
        try:
            value = getattr(e, name)
            if callable(value):
                args = {"set_macro": (0, 64), "get_macro": (0,),
                        "program_change": (0,), "macro": (0,),
                        "pitch_bend": (8192,), "control_change": (1, 64),
                        "channel_pressure": (64,),
                        "poly_pressure": (60, 64)}.get(name, ())
                value(*args)
            quiet.append(name)
        except Exception:                           # noqa: BLE001
            pass
    try:
        e.deinit()
        second = ""
    except Exception as err:                        # noqa: BLE001
        second = "; second deinit raised %s" % type(err).__name__
    if quiet or second:
        res["PD"] = "RED(no raise after deinit: %s%s)" % (
            ",".join(quiet), second)
    else:
        res["PD"] = "ok"
    return res


#: PR compares this many frames from the landing on.
PR_FRAMES = 16 * BLOCK


def _land_pull(ev):
    """The pull the cell's last action is taken before."""
    if ev.first:
        return 0
    return K0 + ev.gap if ev.back else K0


def _drive(e, feed, ctx, ev, upto, land):
    """Pull up to pull `upto`, taking `ev`'s actions before the pulls they
    are due at; with `land` the actions due before pull `upto` are taken
    too (and that pull is not)."""
    k0 = 0 if ev.first else K0
    kb = k0 if ev.first else k0 + ev.gap
    out = bytearray()
    for k in range(upto + 1):
        if k == upto and not land:
            return
        if k == k0:
            act(e, feed, ctx, ev.away)
        if k == kb and ev.back:
            act(e, feed, ctx, ev.back)
        if k == upto:
            return
        _pull(e, out)


def _locate(material, block, fsize):
    """The frame `block` starts at in `material`, or -1."""
    i = material.find(block)
    while i >= 0 and i % fsize:
        i = material.find(block, i + 1)
    return -1 if i < 0 else i // fsize


def _diverge(a, b, frames, fsize):
    """The first frame where `a` and `b` render differently, pulled in
    step for `frames`, or -1."""
    abuf = bytearray()
    bbuf = bytearray()
    base = 0
    total = frames * fsize
    while base < total:
        if not abuf:
            abuf = bytearray(_pull_some(a, fsize))
        if not bbuf:
            bbuf = bytearray(_pull_some(b, fsize))
        n = min(len(abuf), len(bbuf), total - base)
        if abuf[:n] != bbuf[:n]:
            return (base + _first_diff(abuf, bbuf, 0, n)) // fsize
        abuf = abuf[n:]
        bbuf = bbuf[n:]
        base += n
    return -1


def _routes_around(cls, ev, rate, channels, patch, options):
    """True when the event's move away routes the output around the graph
    (`_route_around`), so the way back is a rejoin."""
    feed = Feed(material_for("once", rate, channels), rate, channels, "256",
                loop=False)
    e = _build(cls, feed, rate, patch, options)
    try:
        act(e, feed, Ctx(e, patch), ev.away)
        return bool(getattr(e, "_stranded", False))
    finally:
        e.deinit()


def pr(cls, ev, rate, channels, patch, options):
    """PR: from the move that lands the class (a reset, a return from Mix
    0) on, it renders byte for byte what a fresh instance built at the
    landing state renders, fed the same source from the same frame."""
    fsize = 2 * channels
    values = material_for("once", rate, channels)
    upto = _land_pull(ev)
    if ev.landing == "config" and not _routes_around(cls, ev, rate, channels,
                                                     patch, options):
        # Mix 0 that keeps the graph running is not a rejoin: the class
        # comes back to its own state, not a fresh one's.
        return "na(Mix 0 keeps the graph running)"
    landing = 0 if ev.landing == "reset" else patch
    fresh = {} if landing is None else {"patch": landing}
    start = 0
    if not ev.first:
        # Where the source stands at the landing: a dry run to it, then
        # the source's next block, found in the material.
        feed = Feed(values, rate, channels, "256", loop=False)
        e = _build(cls, feed, rate, patch, options)
        try:
            _drive(e, feed, Ctx(e, patch), ev, upto, False)
            block = bytes(audiocore.get_buffer(feed.mat)[1])
        finally:
            e.deinit()
        start = _locate(bytes(values), block, fsize)
        if start < 0:
            return "na(source position not found)"
    feed = Feed(values, rate, channels, "256", loop=False)
    e = _build(cls, feed, rate, patch, options)
    f = None
    try:
        _drive(e, feed, Ctx(e, patch), ev, upto, True)
        ffeed = Feed(values[start * channels:], rate, channels, "256",
                     loop=False)
        try:
            f = build_fresh(cls, ffeed, rate, options, fresh)
        except TypeError as err:
            return "na(no fresh build: %s)" % (
                str(err).replace("|", "/")[:60])
        d = _diverge(e, f, PR_FRAMES, fsize)
    finally:
        e.deinit()
        if f is not None:
            f.deinit()
    if d < 0:
        return "ok"
    return "RED(differs from a fresh instance at +%d)" % d


def _skip(cls, ev, impl=None):
    """SKIP's reason for this cell on `impl` (this interpreter by
    default), or None."""
    impl = impl or sys.implementation.name
    for (name, prefix, where), reason in SKIP.items():
        if name == cls.NAME and where == impl and ev.name.startswith(prefix):
            return reason
    return None


PROPS = ("P1", "P2", "P3", "P4", "P5")


def run_cell(cls, ev, rate, channels, patch, options, controls):
    res = {}
    res["P1"] = p1(cls, ev, rate, channels, patch, options)
    res.update(main_render(cls, ev, rate, channels, patch, options,
                           controls))
    res["P5"] = p5(cls, ev, rate, channels, patch, options, controls)
    if ev.landing:
        res["PR"] = pr(cls, ev, rate, channels, patch, options)
        if res["PR"].startswith("RED") and cls.NAME in FREE_PHASE:
            res["PR"] = "decl"
    for prop in PROPS + ("PF",):
        if prop in res and res[prop].startswith("RED") and \
                _decl(cls, ev, prop, patch):
            res[prop] = "decl"
    return res


def fmt(name, event, rate, channels, patch, res):
    parts = [name, event, str(rate), str(channels),
             "d" if patch is None else str(patch)]
    for prop in sorted(res):
        parts.append("%s:%s" % (prop, res[prop]))
    return "|".join(parts)


def run_class(cls, options=None, rates=RATES, channels=CHANNELS,
              patches=None, only=None, quick=False, emit=print, name=None):
    """Run the matrix on `cls`, emitting one line per cell and a summary
    line last. Returns (cells, red, declared)."""
    options = options or {}
    name = name or cls.NAME
    check_declared()
    if patches is None:
        patches = [None] + sorted(cls.PATCHES)
    cells = red = decl = 0
    for rate in rates:
        for ch in channels:
            for patch in patches:
                controls = {}
                try:
                    if only is None or "E3" in only:
                        res = e3(cls, rate, ch, patch, options)
                        line = fmt(name, "E3-deinit", rate, ch, patch, res)
                        emit(line)
                        cells += 1
                        red += 1 if "RED" in line else 0
                    for ev in events(cls, patch, quick):
                        if only is not None and ev.name.split("-")[0] \
                                not in only:
                            continue
                        reason = _skip(cls, ev)
                        if reason is not None:
                            res = dict((prop, "na(skip: %s)" % reason)
                                       for prop in PROPS)
                        else:
                            res = run_cell(cls, ev, rate, ch, patch, options,
                                           controls)
                        line = fmt(name, ev.name, rate, ch, patch, res)
                        emit(line)
                        cells += 1
                        red += 1 if "RED" in line else 0
                        decl += 1 if ":decl" in line else 0
                finally:
                    for ctl in controls.values():
                        ctl.close()
    emit("SUMMARY|%s|cells %d|red %d|declared %d" % (name, cells, red, decl))
    return cells, red, decl


# --------------------------------------------------------------------------
# Planted faults: the matrix's proof that each property can fail.
#
# `Plain` is the control for P1, P2, P4, P5 and PD: one mixer voice whose
# level is the dry/wet law (Mix 0 is level 1.0, the source bit for bit;
# Mix 1 is the Gain macro's level), so nothing is ever routed around.
# `Routed` is the control for P3: Mix 0 routes around to the source and the
# way back rejoins and re-arms, the house pattern. Each plant breaks exactly
# one thing.

_COMPONENT = _component.Component if _component is not None else object


class Plain(_COMPONENT):
    NAME = "LifecyclePlain"
    TIER = "audiodsp" if _component is None else _component.AUDIODSP
    REQUIRES = ("audioroute",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0
    MACRO_LABELS = ("Mix", "Gain")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (0.0, 1.0))
    PATCHES = {0: ("Unity", (127, 127)), 1: ("Soft", (127, 96))}

    def _build(self, mix=1.0, gain=1.0, patch=None):
        pcm = self._pcm(BLOCK * self._channel_count * 2)
        self._mixer = self._own(audiomixer.Mixer(voice_count=2, **pcm))
        self._dc = _raw(array("h", bytes(4 * self._channel_count)),
                        self._sample_rate, self._channel_count)
        self._arm()
        self._output = self._mixer
        self._macros = [mix, gain]
        self._init_macros((mix, gain), patch)

    def _arm(self):
        self._mixer.voice[0].play(self._source, loop=True)
        self._mixer.voice[1].play(self._dc, loop=True)

    def _level(self):
        mix = self._macros[0]
        return 1.0 - mix + mix * self._macros[1]

    def _apply_macro(self, index, position):
        self._mixer.voice[0].level = self._level()


class Routed(Plain):
    """Mix 0 routes around a 5 ms echo line to the source; the way back
    rejoins, clearing the line, and re-arms."""
    NAME = "LifecycleRouted"
    REQUIRES = ("audioroute",)
    TAIL_SAMPLES = 512

    def _build(self, mix=1.0, gain=1.0, patch=None):
        import audiodelays
        pcm = self._pcm(BLOCK * self._channel_count * 2)
        self._echo = self._own(audiodelays.Echo(
            max_delay_ms=10, delay_ms=5, decay=0.0, mix=1.0, **pcm))
        Plain._build(self, mix, gain, patch)

    def _arm(self):
        self._echo.play(self._source, loop=True)
        self._mixer.voice[0].play(self._echo, loop=True)
        self._mixer.voice[1].play(self._dc, loop=True)

    def _apply_macro(self, index, position):
        if index == 0 and position == 0.0:
            self._route_around(self._source)
            return
        if index == 0:
            if self._rejoin():
                self._arm()
            self._output = self._mixer
        self._mixer.voice[0].level = self._macros[1]


class DropOnReset(Plain):
    """P1: reset() swallows one block of the borrowed source."""

    def reset(self):
        Plain.reset(self)
        audiocore.get_buffer(self._source)


class HoldDC(Plain):
    """P2: after a reset the output sits on a DC offset for ever."""

    def reset(self):
        Plain.reset(self)
        ch = self._channel_count
        self._dc_on = _raw(array("h", [9] * (2 * ch)), self._sample_rate, ch)
        self._mixer.voice[1].play(self._dc_on, loop=True)


class StaleMix(Routed):
    """P3: Mix back from 0 takes the graph back untouched, so the echo line
    plays what it held out of silence (stale_blocks.StaleRejoin)."""

    def _rejoin(self, keep=()):
        self._stranded = False
        return False


class LateMove(Plain):
    """P4: a move is answered one move late, so away-and-back leaves the
    class where it went."""

    def _apply_macro(self, index, position):
        late = getattr(self, "_late", None)
        self._late = self._level()
        self._mixer.voice[0].level = self._late if late is None else late


class HardSwitch(Plain):
    """P5: Mix below half re-points the output to a primed silent mixer,
    mid-waveform, a hard switch."""

    def _build(self, mix=1.0, gain=1.0, patch=None):
        pcm = self._pcm(BLOCK * self._channel_count * 2)
        self._quiet = self._own(audiomixer.Mixer(voice_count=1, **pcm))
        self._quiet.voice[0].level = 0.0
        Plain._build(self, mix, gain, patch)

    def _arm(self):
        Plain._arm(self)
        self._quiet.voice[0].play(self._dc, loop=True)

    def _apply_macro(self, index, position):
        Plain._apply_macro(self, index, position)
        if self._constructing:
            return
        self._output = self._quiet if self._macros[0] < 0.5 else self._mixer


class ImplPlant(Plain):
    """P6: the level is a hair different off CPython, so the bytes differ
    between interpreters while every verdict stays the same."""

    def _level(self):
        level = Plain._level(self)
        if sys.implementation.name != "cpython":
            level = level * 0.99
        return level


class BusyDeinit(Plain):
    """PD: tail_samples still answers after deinit."""

    @property
    def tail_samples(self):
        return 0


class _FirstPull:
    """A Python-level output (CPython only) that calls `hook` once, after
    the first block it hands on."""

    def __init__(self, inner, hook):
        self.inner = inner
        self.hook = hook
        self.sample_rate = inner.sample_rate
        self.channel_count = inner.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        audiocore.reset_buffer(self.inner)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        got = audiocore.get_buffer(self.inner)
        hook = self.hook
        if hook is not None:
            self.hook = None
            hook()
        return got


class LatePatch(Plain):
    """PF: a move made before the first pull lands one block late, so the
    first block plays at the level the class was built at (CPython only:
    its output is a Python-level node)."""
    NAME = "LifecycleLatePatch"

    def _build(self, mix=1.0, gain=1.0, patch=None):
        self._pulled = False
        Plain._build(self, mix, gain, patch)
        self._output = _FirstPull(self._mixer, self._first)

    def _first(self):
        self._pulled = True
        Plain._apply_macro(self, 0, self._macros[0])

    def _apply_macro(self, index, position):
        if self._constructing or self._pulled:
            Plain._apply_macro(self, index, position)


class ResetLeak(Routed):
    """PR: reset() keeps the echo line, so the 5 ms it held plays after the
    reset where a fresh instance plays silence; inside tail_samples, so P4
    reads it as ok."""
    NAME = "LifecycleResetLeak"

    def reset(self):
        self._check_live()
        self._clear_nodes(keep=(self._echo,))
        self._stranded = False
        self.program_change(0)


class _Scaled:
    """A Python-level output (CPython only) that scales every block the
    mixer hands on by the owner's factor, at once: a control that jumps,
    which no mixer level does (the mixer ramps it)."""

    def __init__(self, inner, owner):
        self.inner = inner
        self.owner = owner
        self.sample_rate = inner.sample_rate
        self.channel_count = inner.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        audiocore.reset_buffer(self.inner)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        result, data = audiocore.get_buffer(self.inner)
        values = array("h")
        values.frombytes(bytes(data))
        factor, offset = self.owner._shape()
        for i in range(len(values)):
            v = int(values[i] * factor) + offset
            values[i] = max(-32768, min(32767, v))
        return result, values.tobytes()


class DepthJump(Plain):
    """The depth model's control: Depth 0 is the source and any other
    Depth is the source at half level, handed over at once, as an LFO's
    depth or a gate's floor is. Not a crossfade, and P5 would read its jump
    as a click if it judged it as one (CPython only: its output is a
    Python-level node)."""
    NAME = "LifecycleDepth"
    MACRO_LABELS = ("Depth", "Gain")

    def _build(self, mix=1.0, gain=1.0, patch=None):
        self._pop = False
        Plain._build(self, mix, gain, patch)
        self._output = _Scaled(self._mixer, self)

    def _level(self):
        return 1.0

    def _factor(self):
        return 1.0 if self._macros[0] == 0.0 else 0.5

    def _shape(self):
        return self._factor(), 0

    def _apply_macro(self, index, position):
        Plain._apply_macro(self, index, position)


class DepthLeak(DepthJump):
    """P1: Depth 0 is not the wire, it leaves the source 3 % down."""

    def _factor(self):
        return 0.97 if self._macros[0] == 0.0 else 0.5


class DepthPop(DepthJump):
    """P5: the first block after a Depth move carries a DC offset, a click
    on top of the jump the model allows."""

    def _apply_macro(self, index, position):
        self._pop = not self._constructing
        Plain._apply_macro(self, index, position)

    def _shape(self):
        pop, self._pop = self._pop, False
        return self._factor(), 20000 if pop else 0


PLANTS = {"plain": Plain, "routed": Routed, "droponreset": DropOnReset,
          "holddc": HoldDC, "latepatch": LatePatch, "resetleak": ResetLeak,
          "stalemix": StaleMix, "latemove": LateMove,
          "hardswitch": HardSwitch, "busydeinit": BusyDeinit,
          "implplant": ImplPlant, "depthjump": DepthJump,
          "depthleak": DepthLeak, "depthpop": DepthPop}


def _cli(argv):
    only = None
    quick = False
    names = []
    for arg in argv:
        if arg.startswith("--events="):
            only = arg.split("=", 1)[1].split(",")
        elif arg == "--quick":
            quick = True
        elif arg == "--empty-source-returns":
            for row in EMPTY_SOURCE_SKIPS:
                SKIP.pop(row, None)
        else:
            names.append(arg)
    for name in names:
        if name in PLANTS:
            cls = PLANTS[name]
        elif name.startswith("Node"):
            import node_matrix
            cls = node_matrix.NODES.get(name)
            if cls is None:
                print("MISSING|%s" % name)
                continue
        else:
            import audioeffects
            cls = getattr(audioeffects, name, None)
            if cls is None:
                print("MISSING|%s" % name)
                continue
        # The kit's options table: a class whose defaults are trivial (the
        # generic Rack's empty chain) runs on something real.
        import kit_options
        run_class(cls, options=kit_options.lifecycle_options_for(cls.NAME),
                  only=only,
                  quick=quick, name=name if name in PLANTS else None)
    print("DONE")


if __name__ == "__main__":
    # Run as the module `lifecycle`, not `__main__`: `_component` reads
    # VENDOR off the module a planted class is defined in.
    sys.path.insert(0, "tests/support")
    import lifecycle
    lifecycle._cli(sys.argv[1:])
