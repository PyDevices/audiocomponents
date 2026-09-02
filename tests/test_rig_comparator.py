"""Planted-fault coverage for tools/compare_rig.py.

A comparator that has only ever been shown to PASS has not been shown to
work. This file plants a known fault of each shape and asserts the
comparator catches it - including the one it originally missed.

That miss is worth recording: with two silent renders every gesture window
read the same level, the difference was zero, and the comparator reported
"all gesture windows agree". A plug-in that never loaded and an offline path
that produced nothing would have passed the rig's own check. The same shape
of bug had a sibling verifier in this workspace reporting 4273 backed-up
files missing across three runs while the backup was fine.
"""

import os
import subprocess
import sys
import tempfile
import unittest
import wave

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPARE = os.path.join(HERE, "tools", "compare_rig.py")
SAMPLE_RATE = 48000


def _write(path, mono):
    handle = wave.open(path, "wb")
    handle.setnchannels(2)
    handle.setsampwidth(2)
    handle.setframerate(SAMPLE_RATE)
    stereo = np.repeat(np.clip(mono, -1, 1)[:, None], 2, axis=1)
    handle.writeframes((stereo * 32767).astype("<i2").tobytes())
    handle.close()


class RigComparatorFaults(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="rig-compare-")
        seconds = np.arange(int(3.0 * SAMPLE_RATE)) / SAMPLE_RATE
        self.tone = 0.4 * np.sin(2 * np.pi * 220 * seconds) * np.exp(-seconds * 0.8)
        self.silence = np.zeros_like(self.tone)
        self.rpp = os.path.join(self.dir, "rig.RPP")
        with open(self.rpp, "w") as handle:
            handle.write('MARKER 1 0.0 "gesture one" 0\n'
                         'MARKER 2 1.0 "gesture two" 0\n'
                         'MARKER 3 2.0 "gesture three" 0\n')

    def run_compare(self, bounce, offline):
        bounce_path = os.path.join(self.dir, "bounce.wav")
        offline_path = os.path.join(self.dir, "offline.wav")
        _write(bounce_path, bounce)
        _write(offline_path, offline)
        return subprocess.run(
            [sys.executable, COMPARE, self.rpp, bounce_path, offline_path],
            capture_output=True, text=True, cwd=HERE).returncode

    def test_identical_renders_pass(self):
        """The control: without this the rest proves only that it always fails."""
        self.assertEqual(self.run_compare(self.tone, self.tone), 0)

    def test_two_silent_renders_are_not_agreement(self):
        """The fault it originally missed."""
        self.assertEqual(self.run_compare(self.silence, self.silence), 1)

    def test_one_side_silent_is_caught(self):
        self.assertEqual(self.run_compare(self.tone, self.silence), 1)

    def test_level_difference_is_caught(self):
        """6 dB, comfortably past the 3.5 dB tolerance."""
        self.assertEqual(self.run_compare(self.tone, self.tone * 0.5), 1)

    def test_a_single_dropped_gesture_is_caught(self):
        """One window silent, the others fine - a voice that failed to sound."""
        dropped = np.concatenate([self.tone[:SAMPLE_RATE],
                                  np.zeros(SAMPLE_RATE),
                                  self.tone[2 * SAMPLE_RATE:]])
        self.assertEqual(self.run_compare(self.tone, dropped), 1)


if __name__ == "__main__":
    unittest.main()
