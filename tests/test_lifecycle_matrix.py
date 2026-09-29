"""The lifecycle matrix (`tests/support/lifecycle.py`) on every Phase 5
class this branch carries, on CPython and on the two native interpreters.

What is red today is written down in KNOWN_RED below, one row per defect,
each with a one-line reason. The file passes while the red cells are exactly
those rows' cells, and goes red when a cell changes either way: a new red
cell nobody listed, or a listed cell that turned green (then delete the
row). A row is a finding, not an exception: a class opts out of a property
only through `lifecycle.DECLARED`.

The planted faults at the bottom are the matrix's proof that each property
can fail: every plant is red on its cell and its control is green there.

    OMP_NUM_THREADS=1 python -m unittest tests.test_lifecycle_matrix
    LIFECYCLE_CLASSES=DigitalDelay python -m unittest tests.test_lifecycle_matrix

`LIFECYCLE.md` beside the helper says what each event and property is.
"""

import os
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "lib"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import lifecycle                                          # noqa: E402
from audioeffects import rebuilt                          # noqa: E402

PHASE5 = ("DigitalDelay", "SlapbackDelay", "TapeDelay", "PingPongDelay",
          "MultiTapDelay", "AnalogDelay", "Reverb", "ConvolutionReverb")

#: What is red today. (class, event name prefix, property) ->
#: (red cells in the quick matrix, their digest, red cells in the full
#: matrix, their digest, reason). A red cell belongs to the row with the
#: longest matching prefix. The file goes red when a red cell belongs to no
#: row, or when a row's cells change in number or in which cells they are
#: (the message lists them). The full-matrix pair is None where the full
#: matrix has not been run (MultiTapDelay: it takes about 40 minutes on
#: CPython).
KNOWN_RED = {
    ('SlapbackDelay', 'E', 'P5'): (
        124, '01ddb3de', 198, '4cda9a29',
        'Level, Tone and patch moves step the output within one block (no ramp)'),
    ('SlapbackDelay', 'E1-', 'P4'): (
        56, 'c608fc28', 56, 'c608fc28',
        'reset() lands patch 0 at another moment than a fresh instance, so the Wow phase never re-converges'),
    ('SlapbackDelay', 'E2-', 'P4'): (
        28, 'cbf2eabb', 28, 'cbf2eabb',
        'a host reset_buffer shifts the Wow phase, so the output never re-converges'),
    ('SlapbackDelay', 'E8-dry', 'P3'): (
        16, '95d6ec10', 16, '95d6ec10',
    ('DigitalDelay', 'E', 'P5'): (
        36, 'cfa18482', 94, '4627b739',
        'Mix, Repeat Tone, Repeat Cut and patch moves step the output within one block'),
    ('DigitalDelay', 'E8-dry', 'P3'): (
        6, 'e155e27d', 6, 'e155e27d',
        'a source that stays dry through a pause and comes back: old audio plays out of silence'),
    ('TapeDelay', 'E', 'P5'): (
        34, '60c8dd58', 106, '4ce31e31',
        'Time, Mix, Wow and patch moves step the output within one block'),
    ('TapeDelay', 'E1-', 'P4'): (
        72, '407e821c', 72, '407e821c',
        'reset() lands patch 0 at another moment than a fresh instance, so wow and flutter never re-converge'),
    ('TapeDelay', 'E2-', 'P4'): (
        32, 'd3f42f25', 32, 'd3f42f25',
        'a host reset_buffer shifts the wow and flutter phase, so the output never re-converges'),
    ('TapeDelay', 'E4-m0=0', 'P4'): (
        0, '00000000', 10, '816d86bd',
        'Time to 0 and back at 22.05 kHz: the glide back outlasts tail_samples'),
    ('TapeDelay', 'E8-dry', 'P3'): (
        2, '1da480f7', 2, '1da480f7',
        'a source that stays dry through a pause and comes back: old audio plays out of silence'),
    ('PingPongDelay', 'E4-m2=127', 'P5'): (
        4, '31c4e1c7', 32, 'c9e4e06a',
        'Mix to 127 steps the output within one block'),
    ('MultiTapDelay', 'E', 'P3'): (
        20, '273472a7', None, None,
        'CPython only: a Time move or a patch change and back plays old audio out of silence (see KNOWN_P6)'),
    ('MultiTapDelay', 'E', 'P4'): (
        4, '11f966a4', None, None,
        'at 22.05 kHz stereo a Mix, Repeat Tone or patch move re-converges after tail_samples allows'),
    ('MultiTapDelay', 'E', 'P5'): (
        85, '511cd123', None, None,
        'Time, Heads, Tilt and patch moves step the output within one block (Time and Heads disclosed)'),
    ('MultiTapDelay', 'E1-', 'P4'): (
        16, '9a49aaf5', None, None,
        'at 22.05 kHz mono a reset re-converges about 1000 frames after tail_samples allows'),
    ('MultiTapDelay', 'E5-', 'P4'): (
        14, 'b3271a6f', None, None,
        'Mix 0 and back leaves the class out of step with a fresh instance for good'),
    ('MultiTapDelay', 'E8-dry', 'P4'): (
        15, '6743df4e', None, None,
        'a source that runs dry once leaves the class out of step with a fresh instance for good'),
    ('MultiTapDelay', 'E9-', 'P4'): (
        70, '123b91ee', None, None,
        'Mix 0 and back leaves the class out of step with a fresh instance for good'),
    ('AnalogDelay', 'E', 'P4'): (
        37, '1266f888', 150, 'bb0595c6',
        "the Modulation LFO's phase moves with the event, so a modulated patch never re-converges"),
    ('AnalogDelay', 'E', 'P5'): (
        74, 'b699cca1', 214, '8d248b43',
        'Time, Mix and patch moves step the output within one block'),
    ('AnalogDelay', 'E8-dry', 'P3'): (
        8, 'e1967d96', 8, 'e1967d96',
        'a source that stays dry through a pause and comes back: old audio plays out of silence'),
    ('Reverb', 'E', 'P4'): (
        322, '606b9d85', 1409, '722197fe',
        'a network move, reset or reset_buffer never re-converges to a fresh instance (modulation phase?)'),
    ('Reverb', 'E', 'P5'): (
        416, '8e447fac', 1166, '886ecc00',
        'almost every macro and patch move steps the output within one block'),
    ('Reverb', 'E1-reset@part', 'P1'): (
        44, 'df421423', 44, 'df421423',
        'reset() part-way through a source buffer drops the frames the input held: silence at Mix 0'),
    ('Reverb', 'E8-dry', 'P3'): (
        44, 'e23e44d7', 44, 'e23e44d7',
    ('AnalogDelay', 'E', 'P4'): (
        37, '1266f888', 150, 'bb0595c6',
        "the Modulation LFO's phase moves with the event, so a modulated patch never re-converges"),
    ('AnalogDelay', 'E', 'P5'): (
        74, 'b699cca1', 214, '8d248b43',
        'Time, Mix and patch moves step the output within one block'),
    ('AnalogDelay', 'E8-dry', 'P3'): (
        8, 'e1967d96', 8, 'e1967d96',
        'a source that stays dry through a pause and comes back: old audio plays out of silence'),
    ('ConvolutionReverb', 'E', 'P5'): (
        324, '9421d061', 678, 'e8b57cdc',
        'Mix, Damping, Predelay, Room and patch moves step the output within one block'),
    ('ConvolutionReverb', 'E1-', 'P1'): (
        72, '387f53ad', 72, '387f53ad',
        'reset() silences the next 256 frames, dry included (disclosed)'),
    ('ConvolutionReverb', 'E2-', 'P1'): (
        36, '78219cf4', 36, '78219cf4',
        'a host reset_buffer silences the next 256 frames at Mix 0, dry included'),
    ('ConvolutionReverb', 'E4-m5=0', 'P1'): (
        4, '2857f42f', 36, 'd4cc4837',
        'Mix to 0 lands one block late: the first block after the move is not the source'),
    ('ConvolutionReverb', 'E5-', 'P1'): (
        36, 'caf98973', 36, 'caf98973',
        'Mix to 0 lands one block late: the first block after the move is not the source'),
    ('ConvolutionReverb', 'E8-dry', 'P3'): (
        36, 'b7504caa', 36, 'b7504caa',
        'a source that stays dry through a pause and comes back: old audio plays out of silence'),
}

#: P6 differences today: class -> (cells whose line differs between CPython
#: and a native interpreter in the quick matrix, their digest, the same for
#: the full matrix, reason). Both native interpreters print the same lines
#: as each other for every class.
KNOWN_P6 = {
    "MultiTapDelay": (
        29, "cedec0fa", None, None,
        "after a Time move or a patch change CPython renders other bytes "
        "than both native interpreters, and on 20 cells plays old audio "
        "out of silence where they do not: the CPython audiodelays twin "
        "keeps the line past a shorter delay_ms, which the C node zeroes "
        "(audiodsp#177)"),
}

#: LIFECYCLE_FULL=1 runs the full matrix (every event at every patch);
#: otherwise the quick one (lifecycle.run_class(quick=True)).
FULL = bool(os.environ.get("LIFECYCLE_FULL"))


def digest(cells):
    text = "\n".join(sorted("|".join(map(str, c)) for c in cells))
    return "%08x" % (zlib.crc32(text.encode()) & 0xFFFFFFFF)


def parse(lines):
    """{(class, event, rate, ch, patch): {prop: verdict}}."""
    cells = {}
    for line in lines:
        parts = line.split("|")
        if len(parts) < 6 or parts[0] in ("SUMMARY", "DONE"):
            continue
        key = (parts[0], parts[1], int(parts[2]), int(parts[3]), parts[4])
        cells[key] = dict(p.split(":", 1) for p in parts[5:])
    return cells


def red_cells(cells):
    out = set()
    for key, props in cells.items():
        for prop, verdict in props.items():
            if verdict.startswith("RED"):
                out.add((key[0], key[1], prop, key[2], key[3], key[4]))
    return out


def row_of(cell, rows):
    best = None
    for row in rows:
        if row[0] == cell[0] and row[2] == cell[2] and \
                cell[1].startswith(row[1]):
            if best is None or len(row[1]) > len(best[1]):
                best = row
    return best


def group(name, red, table):
    rows = [row for row in table if row[0] == name]
    groups = dict((row, set()) for row in rows)
    loose = []
    for cell in sorted(red):
        row = row_of(cell, rows)
        if row is None:
            loose.append(cell)
        else:
            groups[row].add(cell)
    return groups, loose


def check_known(name, red, table=None, full=None):
    """Problems with class `name`'s red cells against KNOWN_RED."""
    table = KNOWN_RED if table is None else table
    full = FULL if full is None else full
    groups, loose = group(name, red, table)
    problems = ["new red: %s" % "|".join(map(str, c)) for c in loose]
    for row, got in sorted(groups.items()):
        entry = table[row]
        count, dig = (entry[2], entry[3]) if full else (entry[0], entry[1])
        if count is None:
            continue
        if (len(got), digest(got)) != (count, dig):
            problems.append("row %r changed: %d red cells (digest %s), "
                            "expected %d (%s); now red: %s" % (
                                row, len(got), digest(got), count, dig,
                                ", ".join("|".join(map(str, c[1:]))
                                          for c in sorted(got))[:1500]))
    return problems


def classes():
    wanted = os.environ.get("LIFECYCLE_CLASSES")
    names = wanted.split(",") if wanted else PHASE5
    return [n for n in names if rebuilt.module_class(n) is not None]


def native_binaries():
    """{"micropython": path or None, "circuitpython": path or None}: the
    workspace's `bin/`, or LIFECYCLE_MICROPYTHON / LIFECYCLE_CIRCUITPYTHON."""
    found = {}
    here = ROOT
    bindir = None
    for _up in range(5):
        here = os.path.dirname(here)
        if os.path.isfile(os.path.join(here, "bin", "micropython")):
            bindir = os.path.join(here, "bin")
            break
    for family in ("micropython", "circuitpython"):
        path = os.environ.get("LIFECYCLE_" + family.upper())
        if path is None and bindir is not None:
            path = os.path.join(bindir, family)
        found[family] = path if path and os.path.isfile(path) else None
    return found


def run_native(binary, names, extra=()):
    """The helper's printed lines for `names` under a native binary."""
    with tempfile.TemporaryDirectory() as scratch:
        env = dict(os.environ, MICROPYPATH="lib:tests/support",
                   GCOV_PREFIX=scratch, PYTHONDONTWRITEBYTECODE="1")
        done = subprocess.run(
            [binary, "-X", "heapsize=256M", "tests/support/lifecycle.py"]
            + list(names) + list(extra),
            capture_output=True, text=True, cwd=ROOT, env=env)
    lines = done.stdout.splitlines()
    if done.returncode != 0 or not lines or lines[-1] != "DONE":
        raise AssertionError("%s: %s%s" % (binary, done.stdout[-1500:],
                                           done.stderr[-1500:]))
    return lines


def start_native(binary, names, scratch):
    env = dict(os.environ, MICROPYPATH="lib:tests/support",
               GCOV_PREFIX=scratch, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.Popen(
        [binary, "-X", "heapsize=256M", "tests/support/lifecycle.py"]
        + list(names) + ([] if FULL else ["--quick"]), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=ROOT, env=env)


def run_cpython(name):
    lines = []
    lifecycle.run_class(rebuilt.module_class(name), emit=lines.append,
                        quick=not FULL)
    return lines


class TestMatrix(unittest.TestCase):
    """Each class's red cells are exactly KNOWN_RED's, and the three
    interpreters print the same line for every cell (P6)."""

    @classmethod
    def setUpClass(cls):
        cls.names = classes()
        cls.natives = native_binaries()
        cls.scratch = tempfile.TemporaryDirectory()
        cls.procs = {}
        for family, binary in cls.natives.items():
            if binary is not None and cls.names:
                cls.procs[family] = start_native(binary, cls.names,
                                                 cls.scratch.name)
        cls.cpython = {}
        for name in cls.names:
            cls.cpython[name] = run_cpython(name)
        cls.native_lines = {}
        for family, proc in cls.procs.items():
            out, err = proc.communicate()
            lines = out.splitlines()
            if proc.returncode != 0 or not lines or lines[-1] != "DONE":
                cls.native_lines[family] = AssertionError(
                    "%s: %s%s" % (family, out[-1500:], err[-1500:]))
            else:
                cls.native_lines[family] = lines

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_known_red_on_cpython(self):
        problems = []
        for name in self.names:
            cells = parse(self.cpython[name])
            problems += check_known(name, red_cells(cells))
        self.assertEqual(problems, [], "\n".join(problems[:60]))

    def _p6(self, family):
        if self.natives.get(family) is None:
            self.skipTest("no %s binary: set LIFECYCLE_%s or build the "
                          "workspace's bin/%s" % (family, family.upper(),
                                                  family))
        got = self.native_lines[family]
        if isinstance(got, Exception):
            raise got
        problems = []
        for name in self.names:
            ours = parse(self.cpython[name])
            theirs = parse([l for l in got if l.startswith(name + "|")])
            keys = [key for key in sorted(set(ours) | set(theirs))
                    if ours.get(key) != theirs.get(key)]
            entry = KNOWN_P6.get(name)
            if entry is not None:
                count, dig = (entry[2], entry[3]) if FULL else entry[:2]
                if count is None or (len(keys), digest(keys)) == (count,
                                                                  dig):
                    continue
            for key in keys:
                problems.append("%s: %s cpython %s, %s %s" % (
                    family, "|".join(map(str, key)), ours.get(key),
                    family, theirs.get(key)))
        self.assertEqual(problems, [], "\n".join(problems[:60]))

    def test_p6_micropython(self):
        self._p6("micropython")

    def test_p6_circuitpython(self):
        self._p6("circuitpython")


def plant_cell(plant, event, prop, patch=None, rate=48000, channels=2):
    lines = []
    lifecycle.run_class(lifecycle.PLANTS[plant], rates=(rate,),
                        channels=(channels,), patches=[patch],
                        only=[event.split("-")[0]], emit=lines.append,
                        name=plant)
    cells = parse(lines)
    return cells[(plant, event, rate, channels,
                  "d" if patch is None else str(patch))][prop]


class TestPlants(unittest.TestCase):
    """Every property can fail: each plant is red on its cell, and its
    control is green on the same cell."""

    CASES = (
        ("droponreset", "plain", "E1-reset@block", "P1"),
        ("holddc", "plain", "E1-reset@block", "P2"),
        ("stalemix", "routed", "E5-mix0", "P3"),
        ("latemove", "plain", "E4-m1=0", "P4"),
        ("hardswitch", "plain", "E4-m0=0", "P5"),
        ("busydeinit", "plain", "E3-deinit", "PD"),
    )

    def test_each_plant_is_red_and_its_control_green(self):
        for plant, control, event, prop in self.CASES:
            with self.subTest(plant=plant):
                self.assertTrue(plant_cell(plant, event, prop)
                                .startswith("RED"), plant)
                self.assertEqual(plant_cell(control, event, prop), "ok",
                                 control)

    def test_a_declared_exception_prints_decl(self):
        lifecycle.DECLARED[("LifecyclePlain", "E1-reset@block", "P1")] = \
            "planted declaration"
        try:
            got = plant_cell("droponreset", "E1-reset@block", "P1")
        finally:
            del lifecycle.DECLARED[("LifecyclePlain", "E1-reset@block",
                                    "P1")]
        self.assertEqual(got, "decl")

    def test_known_red_catches_both_directions(self):
        one = ("X", "E1-a", "P1", 48000, 2, "d")
        two = ("X", "E1-b", "P1", 48000, 2, "d")
        table = {("X", "E1-", "P1"): (2, digest([one, two]), None, None,
                                      "planted")}
        self.assertEqual(check_known("X", {one, two}, table, False), [])
        # A listed cell turned green, a cell swapped for another, a red
        # cell no row names: each is a problem.
        self.assertTrue(check_known("X", {one}, table, False))
        three = ("X", "E1-c", "P1", 48000, 2, "d")
        self.assertTrue(check_known("X", {one, three}, table, False))
        four = ("X", "E2-a", "P1", 48000, 2, "d")
        got = check_known("X", {one, two, four}, table, False)
        self.assertTrue(any(p.startswith("new red") for p in got))

    def test_p6_can_fail(self):
        """A plant whose level depends on the interpreter prints a
        different line natively than on CPython."""
        binary = native_binaries()["micropython"]
        if binary is None:
            self.skipTest("no micropython binary")
        extra = ["--events=E4"]
        ours = parse(run_native(sys.executable, ["implplant"], extra))
        theirs = parse(run_native(binary, ["implplant"], extra))
        self.assertNotEqual(ours, theirs)
        same = parse(run_native(binary, ["plain"], extra))
        self.assertEqual(parse(run_native(sys.executable, ["plain"], extra)),
                         same)


if __name__ == "__main__":
    unittest.main()
