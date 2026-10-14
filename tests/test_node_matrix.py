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
"""

import os
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
                                   digest, native_binaries, parse,
                                   red_cells, skipped)

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


def names():
    wanted = os.environ.get("LIFECYCLE_CLASSES")
    picked = wanted.split(",") if wanted else sorted(node_matrix.NODES)
    return [n for n in picked if n in node_matrix.NODES]


def start_native(binary, picked, scratch):
    env = dict(os.environ, MICROPYPATH="lib:tests/support",
               GCOV_PREFIX=scratch, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.Popen(
        [binary, "-X", "heapsize=256M", "tests/support/lifecycle.py"]
        + list(picked) + ([] if FULL else ["--quick"]),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=ROOT, env=env)


class TestNodeMatrix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.names = names()
        cls.natives = native_binaries()
        cls.scratch = tempfile.TemporaryDirectory()
        cls.procs = {}
        for family, binary in cls.natives.items():
            if binary is not None and cls.names:
                cls.procs[family] = start_native(binary, cls.names,
                                                 cls.scratch.name)
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
