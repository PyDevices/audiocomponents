"""The lifecycle matrix (`tests/support/lifecycle.py`) on every effect
class the package serves (`audioeffects.ALL`, all 45), on CPython and on the
two native interpreters.

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

#: `_component` reads VENDOR off the module a class is defined in, and the
#: skip test's plant is defined here.
VENDOR = "PyDevices"

#: Every class the package serves. Until Phase 7 this was the eight Phase 5
#: classes alone, and the Phase 2 to 4 classes' red cells stood unlisted for
#: a month because nothing gated them.
import audioeffects                                         # noqa: E402

GATED = tuple(audioeffects.ALL)

#: What is red today. (class, event name prefix, property) ->
#: (red cells in the quick matrix, their digest, red cells in the full
#: matrix, their digest, reason). A red cell belongs to the row with the
#: longest matching prefix. The file goes red when a red cell belongs to no
#: row, or when a row's cells change in number or in which cells they are
#: (the message lists them). The full-matrix pair is None where the full
#: matrix has not been counted. The rows live in
#: `tests/support/lifecycle_known.py`, one reason per cause, each naming the
#: issue that tracks it.
import lifecycle_known                                    # noqa: E402

KNOWN_RED = dict(lifecycle_known.KNOWN_RED)

#: P6 differences today: class -> (cells whose line differs between CPython
#: and a native interpreter in the quick matrix, their digest, the same for
#: the full matrix, reason). MicroPython prints CPython's lines for every
#: class; the entries below are CircuitPython's.
#:
#: Restated at audiodsp v0.6.6rc1 (30cbbf6). Up to eb2d20d every class,
#: MultiTapDelay included, printed the same lines on all three
#: interpreters, and this table was empty. audiodsp#241 fixed a stray
#: sample in `audiodelays.MultiTapDelay` (and Echo): a line shortened under
#: the write head wrote one more sample past its new end, which played out
#: of the silence when the delay grew back. CPython and MicroPython take the
#: fix; CircuitPython builds upstream's own audiodelays, which still plays
#: the sample, as audiodsp's upstream-diff.md records. So E4's Time-to-0
#: move renders other bytes there, with the same verdicts on P1 to P5.
KNOWN_P6 = {
    "MultiTapDelay": (
        4, "2320dde0", None, None,
        "Time to 0 and back: CircuitPython's own audiodelays plays one "
        "stray sample when the line grows back, which audiodsp#241 fixed "
        "on CPython and MicroPython only"),
    # audiodsp v0.6.6's splice lands each splice in phase (audiodsp#245),
    # and its reset starts the splices where a new node does (#240);
    # CircuitPython's own PitchShift does neither, so nearly every cell
    # that splices live audio renders other bytes there, with the same
    # verdicts but PR. Counted at v0.6.6rc4.
    "Harmonizer": (
        644, "7c09e916", None, None,
        "CircuitPython's own PitchShift: upstream's splice and reset "
        "(audiodsp#245, #240)"),
    "PitchShifter": (
        600, "6aea4833", None, None,
        "CircuitPython's own PitchShift: upstream's splice and reset "
        "(audiodsp#245, #240)"),
    # Counted one event at a time (E9 and E10 a patch at a time on CPython).
    "ShimmerHall": (
        144, "83d529d2", None, None,
        "Bloom's PitchShift is CircuitPython's own there: upstream's splice "
        "and reset (audiodsp#245, #240)"),
}
KNOWN_P6.update(lifecycle_known.KNOWN_P6)

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


def skipped(props):
    """True for a cell `lifecycle.SKIP` kept from running: P6 leaves it
    out, since the interpreter that ran it prints real verdicts."""
    return props is not None and all(
        verdict.startswith("na(skip") for prop, verdict in props.items())


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


def effect_class(name):
    """The class `lifecycle.py NAME` runs: the one the package serves."""
    cls = getattr(audioeffects, name, None)
    return cls


#: Files whose change can move any class's cells: the shared base and
#: package modules, the matrix and the kit it reads, its tables, and the
#: audiodsp pin. A class module's change moves that class alone.
SHARED = ("lib/audioeffects/_", "lib/audioeffects/__init__.py",
          "lib/audioeffects/pyproject.toml", "tests/support/",
          "tests/test_lifecycle_matrix.py", "AUDIODSP_PIN")


#: What a pull request that changes a shared file runs instead of all 45:
#: one class per mechanism family, the cheapest that covers it. A lazily
#: re-armed class (Bitcrusher), an LFO (Tremolo), a delay (DigitalDelay), a
#: reverb (Reverb), a pitch shifter (Octaver), a filter on the biquad
#: (LowPass), Rack, Saturation (the recentre path) and Distortion (the graph
#: rebuild). Measured on CPython at audiodsp v0.6.6rc8: 3 114 CPU seconds,
#: about 13 minutes on a 4-core runner, where all 45 take 4.4 CPU hours.
#: A push to main runs all 45, and so does a manual run or a pull request
#: labelled `lifecycle: all classes` (.github/workflows/tests.yml).
SAMPLE = ("Bitcrusher", "Tremolo", "DigitalDelay", "Reverb", "Octaver",
          "LowPass", "Rack", "Saturation", "Distortion")


def changed_classes(files):
    """The gated classes a change to `files` (repository paths) runs: the
    classes whose own module changed, and SAMPLE beside them when a shared
    file changed, in GATED's order."""
    owners = {}
    for name in GATED:
        module = getattr(effect_class(name), "__module__", "")
        path = "lib/" + module.replace(".", "/") + ".py"
        owners.setdefault(path, []).append(name)
    picked = set()
    for path in files:
        if any(path == s or (s.endswith(("/", "_")) and path.startswith(s))
               for s in SHARED):
            picked.update(SAMPLE)
        picked.update(owners.get(path, ()))
    return [name for name in GATED if name in picked]


def changed_files(base):
    """The paths `git diff base...HEAD` names.

    A base git cannot diff from is an error, not a reason to run every
    class: a checkout of depth 1 has no history and no base, and falling
    back to all 45 is how a pull request's gate once ran for 80 minutes
    unnoticed. The workflow fetches the history a pull request needs."""
    done = subprocess.run(["git", "diff", "--name-only", base + "...HEAD"],
                          capture_output=True, text=True, cwd=ROOT)
    if done.returncode != 0:
        raise LookupError(
            "LIFECYCLE_CHANGED_FROM=%s, but git cannot diff from it (a "
            "shallow checkout, or a base that was never fetched): %s"
            % (base, done.stderr.strip()))
    return [line for line in done.stdout.splitlines() if line]


def classes():
    """The classes to run: LIFECYCLE_CLASSES; or, with
    LIFECYCLE_CHANGED_FROM set to a git base (a pull request's CI), the
    classes `changed_classes` picks for the change since that base; or
    every class the package serves. A name that resolves to no class is an error, not a
    run with nothing in it, whichever list named it."""
    wanted = os.environ.get("LIFECYCLE_CLASSES")
    if not wanted:
        missing = [n for n in GATED if effect_class(n) is None]
        if missing:
            raise LookupError("audioeffects.ALL names no class: %s"
                              % ", ".join(missing))
        base = os.environ.get("LIFECYCLE_CHANGED_FROM")
        if base:
            return changed_classes(changed_files(base))
        return list(GATED)
    names = wanted.split(",")
    missing = [n for n in names if effect_class(n) is None]
    if missing:
        raise LookupError("LIFECYCLE_CLASSES names no class: %s"
                          % ", ".join(missing))
    return names


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


def run_cpython(name, **only):
    lines = []
    import kit_options
    lifecycle.run_class(effect_class(name), emit=lines.append,
                        options=kit_options.lifecycle_options_for(name),
                        quick=not FULL, **only)
    return lines


def _run_cpython_part(part):
    name, rate, ch, patch = part
    return run_cpython(name, rates=(rate,), channels=(ch,), patches=[patch])


def run_cpython_all(names):
    """{name: lines}, the CPython matrix for each class.

    The CPython matrix is most of this file's time, and no cell depends on
    another, so each class's rates, channel counts and patches run side by
    side in processes of their own and their lines are joined in run_class's
    order. Each part prints its own SUMMARY line, which parse() skips.
    LIFECYCLE_JOBS=1 runs every class in this process, one after another.
    """
    jobs = int(os.environ.get("LIFECYCLE_JOBS", "0")) or os.cpu_count() or 1
    if jobs <= 1 or not names:
        return {name: run_cpython(name) for name in names}
    import concurrent.futures
    import multiprocessing
    parts = [(name, rate, ch, patch) for name in names
             for rate in lifecycle.RATES for ch in lifecycle.CHANNELS
             for patch in [None] + sorted(effect_class(name).PATCHES)]
    out = {name: [] for name in names}
    # spawn on every platform: a fork of a process already running threads
    # (a test runner's, say) can deadlock.
    with concurrent.futures.ProcessPoolExecutor(
            min(jobs, len(parts)),
            mp_context=multiprocessing.get_context("spawn")) as pool:
        for part, lines in zip(parts, pool.map(_run_cpython_part, parts)):
            out[part[0]] += lines
    return out


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
        cls.cpython = run_cpython_all(cls.names)
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
                    if ours.get(key) != theirs.get(key)
                    and not skipped(theirs.get(key))
                    and not skipped(ours.get(key))]
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


class TestWireControl(unittest.TestCase):
    """E5 and E9 move the wet/dry control, and need to know which macro it
    is. Every class either has one (a macro labelled "Mix", or a row in
    `lifecycle.MIX_INDEX`), or is listed in `lifecycle.NO_WIRE_CONTROL` with
    the reason it has none, or in `lifecycle.UNRUN_WIRE_CONTROL` with the
    reason its wire is not judged yet: a class whose wire is a level at 0
    under another name cannot go unnoticed."""

    def test_every_class_has_its_wire_or_says_why_not(self):
        tables = (lifecycle.NO_WIRE_CONTROL, lifecycle.UNRUN_WIRE_CONTROL)
        loose = []
        for name in GATED:
            has = lifecycle.mix_index(effect_class(name)) is not None
            listed = [t for t in tables if name in t]
            if not has and not listed:
                loose.append("%s has no wet/dry control and no reason"
                             % name)
            if has and listed:
                loose.append("%s has a wet/dry control and a reason it has"
                             " none" % name)
            if len(listed) > 1:
                loose.append("%s is in both tables" % name)
        self.assertEqual(loose, [], "\n".join(loose))

    def test_the_tables_name_real_classes(self):
        for table in (lifecycle.MIX_INDEX, lifecycle.NO_WIRE_CONTROL,
                      lifecycle.UNRUN_WIRE_CONTROL, lifecycle.MIX_KEYWORD):
            for name in table:
                self.assertIn(name, GATED, name)

    def test_a_row_names_a_macro_the_class_has(self):
        rows = dict(lifecycle.MIX_INDEX)
        rows.update((n, row[0])
                    for n, row in lifecycle.UNRUN_WIRE_CONTROL.items())
        for name, index in rows.items():
            self.assertLess(index, len(effect_class(name).MACRO_LABELS),
                            name)


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
        ("latepatch", "plain", "E12-p1", "PF"),
        ("resetleak", "routed", "E1-reset@block", "PR"),
        ("stalemix", "routed", "E5-mix0", "PR"),
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

    def test_p4_misses_what_pf_and_pr_catch(self):
        """P4 forgives a block (and a tail) after the move; PF and PR do
        not, so these plants are ok on P4 and red only on the new
        properties."""
        self.assertEqual(plant_cell("latepatch", "E12-p1", "P4"), "ok")
        self.assertEqual(plant_cell("resetleak", "E1-reset@block", "P4"),
                         "ok")

    def test_e12_is_judged_against_a_fresh_instance(self):
        lines = []
        lifecycle.run_class(lifecycle.Plain, rates=(48000,), channels=(2,),
                            patches=[None], only=["E12"], emit=lines.append)
        got = sorted(k[1] for k in parse(lines))
        self.assertEqual(got, ["E12-mix0", "E12-mix127", "E12-mix64",
                               "E12-p0", "E12-p1"])
        for props in parse(lines).values():
            self.assertEqual(props["PF"], "ok")
            self.assertEqual(props["P4"], "ok")

    def test_a_scoped_row_matches_only_its_scope(self):
        here = sys.implementation.name
        other = "circuitpython" if here != "circuitpython" else "cpython"
        cases = (
            (("LifecyclePlain", "E1-reset@block", "P1", here), None, "decl"),
            (("LifecyclePlain", "E1-reset@block", "P1", other), None, "RED"),
            (("LifecyclePlain", "E1-reset@block", "P1", (1,)), None, "RED"),
            (("LifecyclePlain", "E1-reset@block", "P1", (1,)), 1, "decl"),
            (("LifecyclePlain", "E1-reset@block", "P1", (None, 1), here),
             None, "decl"),
            # The Octaver form, a patch tuple as the fourth element.
            (("LifecyclePlain", "E1-", "P1", (0, 1)), 1, "decl"),
        )
        for row, patch, want in cases:
            with self.subTest(row=row, patch=patch):
                lifecycle.DECLARED[row] = "planted"
                try:
                    got = plant_cell("droponreset", "E1-reset@block", "P1",
                                     patch=patch)
                finally:
                    del lifecycle.DECLARED[row]
                self.assertTrue(got.startswith(want), got)

    def test_a_row_shorter_than_an_event_is_refused(self):
        for prefix in ("E", "E1", "", "X1-"):
            with self.subTest(prefix=prefix):
                with self.assertRaises(ValueError) as caught:
                    lifecycle.check_declared({("X", prefix, "P1"): "r"})
                self.assertIn("shorter than one whole event name",
                              str(caught.exception))
        for bad in (("X", "E1-", "P9"), ("X", "E1-", "P1", "pypy"),
                    ("X", "E1-", "P1", ("1",)), ("X", "E1-", "PR"),
                    ("X", "E1-", "P1", (1,), (2,))):
            with self.subTest(row=bad):
                with self.assertRaises(ValueError):
                    lifecycle.check_declared({bad: "r"})
        lifecycle.check_declared({("X", "E10-reset", "P4", "circuitpython"):
                                  "r", ("X", "E4-m2=", "P5"): "r"})
        # run_class checks rows added after import too.
        lifecycle.DECLARED[("LifecyclePlain", "E", "P1")] = "planted"
        try:
            with self.assertRaises(ValueError):
                plant_cell("plain", "E1-reset@block", "P1")
        finally:
            del lifecycle.DECLARED[("LifecyclePlain", "E", "P1")]
        with self.assertRaises(ValueError):
            lifecycle.check_declared({}, {"X": ""})

    def test_free_phase_excuses_pr_and_the_summary_counts_cells(self):
        def e10():
            lines = []
            lifecycle.run_class(lifecycle.PLANTS["routed"], rates=(48000,),
                                channels=(2,), patches=[None], only=["E10"],
                                emit=lines.append)
            return lines
        before = parse(e10())
        self.assertTrue(before[("LifecycleRouted", "E10-reset", 48000, 2,
                                "d")]["PR"].startswith("RED"))
        row = ("LifecycleRouted", "E10-reset", "P1")
        lifecycle.DECLARED[row] = "planted"
        lifecycle.FREE_PHASE["LifecycleRouted"] = "a planted phase"
        try:
            lines = e10()
        finally:
            del lifecycle.DECLARED[row]
            del lifecycle.FREE_PHASE["LifecycleRouted"]
        cell = parse(lines)[("LifecycleRouted", "E10-reset", 48000, 2, "d")]
        self.assertEqual((cell["P1"], cell["PR"]), ("decl", "decl"))
        # Three declared properties in two cells: the SUMMARY counts cells.
        self.assertEqual(sum(l.count(":decl") for l in lines), 3)
        self.assertTrue(lines[-1].endswith("|declared 2"), lines[-1])

    def test_a_skipped_cell_prints_na_and_never_runs(self):
        class Raises(lifecycle.Plain):
            NAME = "LifecycleRaises"

            def _build(self, *args, **kwargs):
                raise RuntimeError("the skipped cell ran")

        def e8(emit):
            lifecycle.run_class(Raises, rates=(48000,), channels=(2,),
                                patches=[None], only=["E8"], emit=emit)

        # The control: without the row the cell runs, and the plant raises.
        with self.assertRaises(RuntimeError):
            e8(lambda line: None)
        row = ("LifecycleRaises", "E8-", sys.implementation.name)
        lifecycle.SKIP[row] = "planted skip"
        try:
            lines = []
            e8(lines.append)
        finally:
            del lifecycle.SKIP[row]
        props = parse(lines)[("LifecycleRaises", "E8-end", 48000, 2, "d")]
        self.assertEqual(props, dict((prop, "na(skip: planted skip)")
                                     for prop in lifecycle.PROPS))
        self.assertTrue(skipped(props))
        # A row for another interpreter leaves the cell to run.
        lifecycle.SKIP[("LifecycleRaises", "E8-", "elsewhere")] = "planted"
        try:
            with self.assertRaises(RuntimeError):
                e8(lambda line: None)
        finally:
            del lifecycle.SKIP[("LifecycleRaises", "E8-", "elsewhere")]

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

    def test_a_change_picks_the_classes_it_can_move(self):
        sample = [n for n in GATED if n in SAMPLE]
        cases = (
            (["lib/audioeffects/_component.py"], sample),
            (["tests/support/kit_common.py"], sample),
            (["AUDIODSP_PIN"], sample),
            (["lib/audioeffects/_component.py", "lib/audioeffects/fuzz.py"],
             [n for n in GATED if n in SAMPLE or n == "Fuzz"]),
            (["lib/audioeffects/bitcrusher.py",
              "tests/test_bypass_return.py"], ["Bitcrusher"]),
            (["lib/audioeffects/tapedelay.py"], ["TapeDelay"]),
            (["lib/audioeffects/phaser.py", "lib/audioeffects/vibrato.py"],
             ["Phaser", "Vibrato"]),
            (["docs/control-smoothing.md", "CHANGELOG.md"], []),
            (["tests/test_cpython_effects_tapedelay.py"], []),
        )
        for files, want in cases:
            with self.subTest(files=files):
                self.assertEqual(changed_classes(files), want)
        self.assertEqual(len(SAMPLE), 9)
        self.assertTrue(set(SAMPLE) <= set(GATED))

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
