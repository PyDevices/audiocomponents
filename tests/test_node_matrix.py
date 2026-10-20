"""The lifecycle matrix on the audiodsp nodes the effects stand on
(`tests/support/node_matrix.py`), on CPython and on the two native
interpreters.

The same rules as `tests/test_lifecycle_matrix.py`: a red cell is either a
row of KNOWN_RED below (a finding, with its reason) or a declared exception
in `node_matrix.DECLARED` (a behaviour the node has by design); the file goes
red when a cell changes either way, and the three interpreters must print
the same line for every cell.

    OMP_NUM_THREADS=1 python -m unittest tests.test_node_matrix
    LIFECYCLE_CLASSES=NodePitchShift python -m unittest tests.test_node_matrix

A pull request's CI runs only the nodes its change can move, by the same
rule as the class matrix (`changed_nodes` below, and "What CI runs" in
`tests/support/KIT.md`).
"""

import ast
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "lib"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import lifecycle                                          # noqa: E402
import node_matrix                                        # noqa: E402
from tests.test_lifecycle_matrix import (FULL, check_known,  # noqa: E402
                                   digest, native_binaries, native_extra,
                                   parse, red_cells, skipped,
                                   split_lifted_e8)
from tests.test_lifecycle_matrix import changed_files  # noqa: E402

VENDOR = "PyDevices"

#: What is red today, in the same shape as test_lifecycle_matrix.KNOWN_RED.
KNOWN_RED = {}

#: P6 differences today, in the same shape as test_lifecycle_matrix.KNOWN_P6:
#: node -> (cells whose line differs between CPython and a native
#: interpreter in the quick matrix, their digest, the same for the full
#: matrix, reason). MicroPython prints CPython's lines for every node; these
#: are CircuitPython's. Each is a fix in audiodsp v0.6.6rc1 that CPython and
#: MicroPython take and CircuitPython does not, because there these nodes
#: are upstream's own and keep upstream's behaviour (audiodsp's
#: docs/upstream-diff.md records each).
KNOWN_P6 = {
    "NodeEcho": (
        30, "206fe02a", None, None,
        "a Time move or a patch change shortens the line under the write "
        "head: upstream's Echo plays one stray sample when it grows back "
        "(audiodsp#241)"),
    "NodeMultiTapDelay": (
        12, "60b768a5", None, None,
        "upstream's MultiTapDelay keeps its write heads across a reset, so "
        "a Time move or a patch change after one reads another stretch of "
        "the line; audiodsp v0.6.6rc4 puts them back at the top (E4, E6 and "
        "E11; counted at rc4, one event at a time, E8 skipped)"),
    "NodePitchShift": (
        285, "3c88af12", None, None,
        "upstream's splice lands wherever the window does and ours moves "
        "each splice's incoming side into phase (audiodsp 7b), so nearly "
        "every cell that splices live audio renders other bytes; and "
        "upstream's reset keeps the read and write positions (audiodsp#240)"),
    "NodeGranularPitchShift": (
        4, "91e67a25", None, None,
        "upstream's reset_buffer keeps the jitter sequence, so the grains "
        "after it start at other offsets (audiodsp#240)"),
    "NodeSplitMix": (
        32, "4f7dcebd", None, None,
        "a host reset of upstream's Mixer re-primes its voices and drops the "
        "source frames they held (audiodsp#229)"),
}

#: The E8 cells a CircuitPython that returns from a looped empty source
#: runs, in the shape of test_lifecycle_matrix.KNOWN_P6_E8: upstream's
#: PitchShift splices other bytes (NodePitchShift's KNOWN_P6 reason), with
#: the same verdicts. Counted at audiocomponents 52cc6e0.
KNOWN_P6_E8 = {
    "NodePitchShift": (14, "f36d3780", None, None),
}


#: Files whose change can move every node's cells: the nodes themselves
#: (the audiodsp pin), the base class the adapters stand on, the matrix and
#: the helpers this file shares with the class matrix. The two files that
#: name nodes one by one, the adapters and this file, are read by the line:
#: a change inside one node's adapter class or table rows moves that node
#: alone, and a change anywhere else in them is shared.
NODE_SHARED = ("AUDIODSP_PIN", "lib/audioeffects/_",
               "lib/audioeffects/__init__.py", "tests/support/lifecycle.py",
               "tests/support/kit_options.py", "tests/test_lifecycle_matrix.py")
NODE_FILES = ("tests/support/node_matrix.py", "tests/test_node_matrix.py")

#: What a pull request that changes a shared file runs instead of all 13,
#: one node per mechanism the others share: a biquad's recursion
#: (NodeBiquad), a delay line (NodeEcho), the Mixer a host resets
#: (NodeSplitMix) and a free-running phase (NodeShimmerLoop, cheaper than
#: NodeFlanger's LFO by minutes). Measured on CPython at audiodsp
#: v0.6.6rc9: 86 s, where all 13 take 541 s (about 30 minutes on CI).
#: A push to main runs every node, and so does a manual run or a pull
#: request labelled `lifecycle: all classes` (.github/workflows/tests.yml).
NODE_SAMPLE = ("NodeBiquad", "NodeEcho", "NodeSplitMix", "NodeShimmerLoop")


def _owned_lines(source, known):
    """{node name: [(first, last) line]} in a file's text: each class whose
    NAME is a node, and each row of a module-level table whose key is a
    node's name or a tuple that starts with one."""
    owned = {}
    for stmt in ast.parse(source).body:
        if isinstance(stmt, ast.ClassDef):
            for item in stmt.body:
                if (isinstance(item, ast.Assign)
                        and any(getattr(t, "id", None) == "NAME"
                                for t in item.targets)
                        and isinstance(item.value, ast.Constant)
                        and item.value.value in known):
                    owned.setdefault(item.value.value, []).append(
                        (stmt.lineno - len(stmt.decorator_list),
                         stmt.end_lineno))
        elif (isinstance(stmt, (ast.Assign, ast.AnnAssign))
              and isinstance(stmt.value, ast.Dict)):
            for key, value in zip(stmt.value.keys, stmt.value.values):
                head = key.elts[0] if isinstance(key, ast.Tuple) else key
                if isinstance(head, ast.Constant) and head.value in known:
                    owned.setdefault(head.value, []).append(
                        (key.lineno, value.end_lineno))
    return owned


def _changed_lines(base, path):
    """The lines of `path` at HEAD that `git diff base...HEAD` touches; a
    deletion touches the lines either side of it."""
    done = subprocess.run(["git", "diff", "-U0", base + "...HEAD", "--", path],
                          capture_output=True, text=True, cwd=ROOT)
    if done.returncode != 0:
        raise LookupError("git cannot diff %s from %s: %s"
                          % (path, base, done.stderr.strip()))
    lines = set()
    for match in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", done.stdout,
                             re.M):
        first = int(match.group(1))
        count = 1 if match.group(2) is None else int(match.group(2))
        lines.update(range(first, first + count) if count
                     else (first, first + 1))
    return lines


def changed_nodes(files, lines_of, sources):
    """The nodes a change runs, sorted: those whose own lines in NODE_FILES
    changed, and NODE_SAMPLE beside them when a shared file changed or a
    line of NODE_FILES outside every node's own did. `lines_of(path)` is
    the changed lines of a NODE_FILES path and `sources(path)` its text."""
    known = set(node_matrix.NODES)
    picked = set()
    for path in files:
        if any(path == s or (s.endswith(("/", "_")) and path.startswith(s))
               for s in NODE_SHARED):
            picked.update(NODE_SAMPLE)
        elif path in NODE_FILES:
            owned = _owned_lines(sources(path), known)
            for line in lines_of(path):
                hits = [name for name, spans in owned.items()
                        if any(a <= line <= b for a, b in spans)]
                picked.update(hits or NODE_SAMPLE)
    return sorted(picked)


def names():
    wanted = os.environ.get("LIFECYCLE_CLASSES")
    if wanted:
        picked = wanted.split(",")
    else:
        base = os.environ.get("LIFECYCLE_CHANGED_FROM")
        if base:
            def source(path):
                with open(os.path.join(ROOT, path)) as handle:
                    return handle.read()
            picked = changed_nodes(changed_files(base),
                                   lambda path: _changed_lines(base, path),
                                   source)
        else:
            picked = sorted(node_matrix.NODES)
    return [n for n in picked if n in node_matrix.NODES]


def start_native(binary, picked, scratch, extra=()):
    env = dict(os.environ, MICROPYPATH="lib:tests/support",
               GCOV_PREFIX=scratch, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.Popen(
        [binary, "-X", "heapsize=256M", "tests/support/lifecycle.py"]
        + list(picked) + ([] if FULL else ["--quick"]) + list(extra),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=ROOT, env=env)


class TestNodeMatrix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.names = names()
        cls.natives = native_binaries()
        cls.scratch = tempfile.TemporaryDirectory()
        cls.procs = {}
        cls.lifted = {}
        for family, binary in cls.natives.items():
            if binary is not None and cls.names:
                extra = native_extra(family, binary, cls.scratch.name)
                cls.lifted[family] = bool(extra)
                cls.procs[family] = start_native(binary, cls.names,
                                                 cls.scratch.name, extra)
        cls.cpython = {}
        for name in cls.names:
            lines = []
            lifecycle.run_class(node_matrix.NODES[name], emit=lines.append,
                                quick=not FULL)
            cls.cpython[name] = lines
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
            problems += check_known(name, red_cells(parse(self.cpython[name])),
                                    KNOWN_RED)
        self.assertEqual(problems, [], "\n".join(problems[:60]))

    def _p6(self, family):
        if self.natives.get(family) is None:
            self.skipTest("no %s binary" % family)
        got = self.native_lines[family]
        if isinstance(got, Exception):
            raise got
        problems = []
        for name in self.names:
            ours = parse(self.cpython[name])
            theirs = parse([l for l in got if l.startswith(name + "|")])
            keys = [key for key in sorted(set(ours) | set(theirs))
                    if ours.get(key) != theirs.get(key)
                    and not skipped(theirs.get(key))]
            keys = split_lifted_e8(name, keys, KNOWN_P6_E8,
                                   self.lifted.get(family), problems,
                                   family, ours, theirs)
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


class TestScope(unittest.TestCase):
    """A pull request's node scope: the nodes its change can move."""

    @staticmethod
    def _source(path):
        with open(os.path.join(ROOT, path)) as handle:
            return handle.read()

    def _line(self, path, text):
        lines = self._source(path).splitlines()
        return [i + 1 for i, line in enumerate(lines) if text in line][0]

    def _pick(self, changes):
        files = [path for path, _ in changes]
        lines = {}
        for path, line in changes:
            if line is not None:
                lines.setdefault(path, set()).add(line)
        return changed_nodes(files, lambda path: lines.get(path, set()),
                             self._source)

    def test_a_change_picks_the_nodes_it_can_move(self):
        adapters, here = NODE_FILES
        sample = sorted(NODE_SAMPLE)
        cases = (
            ([("AUDIODSP_PIN", None)], sample),
            ([("lib/audioeffects/_component.py", None)], sample),
            ([("tests/support/lifecycle.py", None)], sample),
            ([("lib/audioeffects/fuzz.py", None)], []),
            ([("tests/support/kit_tail.py", None)], []),
            ([(adapters, self._line(adapters, "Reverb's predelay and the Haas"))],
             ["NodeEcho"]),
            ([(adapters, self._line(adapters, 'NAME = "NodeEcho"')),
              (adapters, self._line(adapters, '("NodeFlanger", "E6-"'))],
             ["NodeEcho", "NodeFlanger"]),
            ([(adapters, self._line(adapters, "BLOCK = 256"))], sample),
            ([(here, self._line(here, '"NodeSplitMix": ('))],
             ["NodeSplitMix"]),
            ([(here, self._line(here, "def start_native"))], sample),
        )
        for changes, want in cases:
            with self.subTest(changes=changes):
                self.assertEqual(self._pick(changes), want)
        self.assertTrue(set(NODE_SAMPLE) <= set(node_matrix.NODES))

    def test_every_node_owns_its_adapter(self):
        owned = _owned_lines(self._source(NODE_FILES[0]),
                             set(node_matrix.NODES))
        self.assertEqual(sorted(owned), sorted(node_matrix.NODES))


class TestAdapters(unittest.TestCase):
    """An adapter can show a reset defect: one whose reset leaves the node
    where it was instead of where a fresh one starts is red on P4 where the
    clean adapter is green."""

    def test_a_reset_that_keeps_state_is_red(self):
        def cell(cls):
            lines = []
            lifecycle.run_class(cls, rates=(48000,), channels=(2,),
                                patches=[None], only=["E1"],
                                emit=lines.append)
            return parse(lines)[(cls.NAME, "E1-reset@block", 48000, 2,
                                 "d")]["P4"]

        class KeepsState(node_matrix.NodeBiquad):
            NAME = "NodeBiquadKeepsState"

            def reset(self):
                self._check_live()
                self._clear_nodes()

        self.assertEqual(cell(node_matrix.NodeBiquad), "ok")
        self.assertTrue(cell(KeepsState).startswith("RED"))


if __name__ == "__main__":
    unittest.main()
