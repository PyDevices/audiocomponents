"""The audioconvolve node itself: the arithmetic under the convolvers.

Not an effect-class test, and no family phase retires it. `Convolver` is an
audioif node - the palette layer - so the three-tap convolution checked
against its own arithmetic, the no-impulse wire with no latency, the refused
oversized impulse and the transform inverting itself hold whatever
`ConvolutionReverb` and `CabinetSim` are rebuilt into. The classes built on
the node are covered by `test_cpython_effects_time.py` and
`test_cpython_effects_drive.py`, which their phases do retire.
"""

import math
import os
import sys
import unittest
from array import array

import audiocore

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import SAMPLE_RATE, source  # noqa: E402


class ConvolveNodeTest(unittest.TestCase):
    def test_a_convolver_actually_convolves(self):
        # The claim is arithmetic, so check it against the arithmetic: a
        # three-tap impulse against a sine has to give the sine plus two
        # delayed, scaled copies of it, sample for sample.
        import audioconvolve
        taps = array("h", [0] * 700)
        taps[0], taps[300], taps[650] = 32767, 16000, -8000
        level, hz = 6000, 440.0
        values = array("h")
        for frame in range(4096):
            value = int(level * math.sin(2.0 * math.pi * hz * frame
                                         / SAMPLE_RATE))
            values.append(value)
            values.append(value)
        node = audioconvolve.Convolver(impulse=taps, max_taps=1024, mix=1.0)
        node.play(audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                                      channel_count=2))
        rendered = []
        for _ in range(6):
            rendered.extend(
                memoryview(bytes(audiocore.get_buffer(node)[1])).cast("h")[0::2])

        latency = audioconvolve.FRAMES
        worst = 0.0
        for index in range(latency, len(rendered)):
            expected = 0.0
            for offset, gain in ((0, 32767), (300, 16000), (650, -8000)):
                position = index - latency - offset
                if 0 <= position < len(values) // 2:
                    expected += (level * math.sin(2.0 * math.pi * hz * position
                                                  / SAMPLE_RATE)
                                 * gain / 32768.0)
            worst = max(worst, abs(rendered[index] - expected))
        # The gains sum to 1.73, so a source quantized to whole int16 steps
        # can be that far out on its own before the convolution adds anything.
        self.assertLess(worst, 2.5)

    def test_a_convolver_with_no_impulse_is_a_wire(self):
        # And a wire with no latency: a chain built before its impulse
        # arrives must not drift against its neighbours. Compared against the
        # source's own values rather than a second RawSample, because a
        # RawSample hands back its whole buffer per pull and the convolver
        # hands back 256 frames.
        import audioconvolve
        node = audioconvolve.Convolver(max_taps=512)
        node.play(source())
        self.assertEqual(node.taps, 0)
        rendered = []
        for _ in range(4):
            rendered.extend(
                memoryview(bytes(audiocore.get_buffer(node)[1])).cast("h"))
        expected = list(memoryview(
            bytes(audiocore.get_buffer(source())[1])).cast("h"))
        self.assertEqual(rendered, expected[:len(rendered)])

    def test_an_impulse_longer_than_the_convolver_is_refused(self):
        # Not truncated. The capacity was chosen at construction and
        # something downstream may already be pulling.
        import audioconvolve
        node = audioconvolve.Convolver(max_taps=256)
        with self.assertRaises(ValueError):
            node.load(array("h", [0] * 4000), 1)

    def test_the_transform_inverts_itself(self):
        # The FFT underneath all of this is not exposed, so it is exercised
        # here: a convolver loaded with a unit impulse is a forward transform
        # and an inverse transform with a multiply by one in between, and has
        # to hand back exactly what it was given.
        import audioconvolve
        unit = array("h", [0] * 256)
        unit[0] = 32767
        node = audioconvolve.Convolver(impulse=unit, max_taps=256, mix=1.0)
        node.play(source())
        latency = audioconvolve.FRAMES
        rendered = []
        for _ in range(5):
            rendered.extend(
                memoryview(bytes(audiocore.get_buffer(node)[1])).cast("h"))
        expected = list(memoryview(
            bytes(audiocore.get_buffer(source())[1])).cast("h"))
        worst = max(abs(a - b) for a, b in
                    zip(rendered[latency * 2:], expected))
        # 32767/32768 of the input, plus rounding: one step, never two.
        self.assertLessEqual(worst, 1)


if __name__ == "__main__":
    unittest.main()
