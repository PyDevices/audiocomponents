"""What the delay and reverb classes do to a signal today.

The dry path left alone, a repeat darkening once per lap, ping-pong
alternating, a line that can be emptied, and the synthesized room's
decay, decorrelation and normalization.

Retired by the effects program's **phase 5 - time**. Every assertion here
is written against a surface that phase replaces, so when its classes have
been rebuilt - each carrying its own invariant and planted-fault tests -
this module is deleted whole and nothing else in the suite moves. Until
then the contract-level tests over `audioeffects.ALL` in
`test_cpython_effects_library.py` hold the catalogue, and these hold the
character.

Covers `TapeDelay`, `PingPongDelay`, `AnalogDelay` and `ConvolutionReverb`.
"""

import math
import os
import sys
import unittest

import audiocore
import audioeffects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import (SAMPLE_RATE, burst, channels, loudest_in, peak,
                             source, tone_gain_db)  # noqa: E402


class TimeTest(unittest.TestCase):
    def test_a_tape_delay_leaves_the_dry_path_alone(self):
        # It used not to. The tone filter sat after the delay's own dry/wet
        # blend, so at mix=0.14 a TapeDelay took 19 dB off 10 kHz and 33 dB
        # off 16 kHz of the signal that was supposed to pass straight
        # through. The filter is inside the feedback loop now.
        def chain(source):
            return audioeffects.TapeDelay(source, mix=0.14,
                                          feedback=0.0).output

        low = tone_gain_db(1000.0, chain)
        high = tone_gain_db(10000.0, chain)
        self.assertAlmostEqual(high, low, delta=0.5)

    def test_a_tape_delay_darkens_each_repeat_more_than_the_last(self):
        # The point of putting the filter in the loop: a repeat passes
        # through it once per lap, so the third is darker than the first.
        # Measured as how much of each tone survives three laps.
        def survival(hz):
            delay = audioeffects.TapeDelay(burst(hz), time_ms=100.0,
                                           feedback=0.7, mix=1.0, wow=0.0,
                                           tone_hz=3000.0, drive=0.0)
            left, _ = channels(delay.output, 200)
            step = int(0.1 * SAMPLE_RATE)
            first = loudest_in(left, step, 2000)
            third = loudest_in(left, step * 3, 2000)
            self.assertGreater(first, 0)
            return third / float(first)

        self.assertLess(survival(8000.0), survival(500.0) * 0.5)

    def test_ping_pong_repeats_alternate_between_the_channels(self):
        # Two delays panned apart, which is what this used to be, puts a
        # repeat on both sides at once. Alternation needs each channel's
        # output in the other channel's line.
        delay = audioeffects.PingPongDelay(burst(1000.0, on=400),
                                           time_ms=100.0, feedback=0.7,
                                           mix=1.0, tone_hz=16000.0)
        left, right = channels(delay.output, 200)
        step = int(0.1 * SAMPLE_RATE)
        sides = [(loudest_in(left, step * n, 800),
                  loudest_in(right, step * n, 800)) for n in range(1, 5)]
        for index, (on_left, on_right) in enumerate(sides):
            if index % 2 == 0:
                self.assertGreater(on_left, on_right * 8 + 1, sides)
            else:
                self.assertGreater(on_right, on_left * 8 + 1, sides)

    def test_an_older_analog_delay_is_darker_and_narrower(self):
        # `age` is one knob over the loop's low-pass, its high-pass and its
        # drift. Only the first two are measurable as a level.
        def repeat_level(hz, age):
            delay = audioeffects.AnalogDelay(burst(hz), time_ms=100.0,
                                             feedback=0.6, mix=1.0, age=age,
                                             drive=0.0)
            left, _ = channels(delay.output, 200)
            return loudest_in(left, int(0.2 * SAMPLE_RATE), 2000)

        self.assertLess(repeat_level(6000.0, 1.0), repeat_level(6000.0, 0.0))
        self.assertLess(repeat_level(80.0, 1.0), repeat_level(80.0, 0.0))

    def test_a_delay_line_can_be_emptied(self):
        delay = audioeffects.TapeDelay(burst(1000.0), time_ms=100.0,
                                        feedback=0.8, mix=1.0)
        channels(delay.output, 40)
        delay.clear()
        self.assertEqual(peak(delay.output, 4), 0.0)

    def test_a_synthesized_room_decays_at_the_time_it_was_asked_for(self):
        verb = audioeffects.ConvolutionReverb(source(), seconds=0.5)
        verb.set_macro(4, 127)          # full wet, so only the tail is measured
        low, high = audioeffects.ConvolutionReverb._MACRO_RANGES[0][:2]
        for knob in (127, 64, 0):
            verb.set_macro(0, knob)
            expected = 0.5 * (low + (high - low) * knob / 127.0)
            self.assertAlmostEqual(verb.decay_seconds, expected, delta=1e-9)

    def test_a_synthesized_room_is_not_the_same_noise_on_both_sides(self):
        # A stereo impulse whose channels agreed would be a mono impulse, and
        # the whole reason to spend twice the memory is that they do not.
        verb = audioeffects.ConvolutionReverb(source(), seconds=0.25,
                                              stereo=True)
        verb.set_macro(4, 127)
        left, right = [], []
        for _ in range(12):
            data = memoryview(bytes(audiocore.get_buffer(verb.output)[1])).cast("h")
            left.extend(data[0::2])
            right.extend(data[1::2])
        window = slice(len(left) // 2, None)
        a, b = left[window], right[window]
        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        covariance = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
        spread_a = math.sqrt(sum((x - mean_a) ** 2 for x in a))
        spread_b = math.sqrt(sum((y - mean_b) ** 2 for y in b))
        correlation = covariance / (spread_a * spread_b)
        self.assertLess(abs(correlation), 0.25)

    def test_a_synthesized_room_is_normalized_rather_than_clipped(self):
        # An unnormalized tail of unit-amplitude noise is tens of thousands
        # of times the input. This is the check that the energy scaling in
        # audioif_convolve_synthesize is doing its job.
        verb = audioeffects.ConvolutionReverb(source(), seconds=0.5)
        verb.set_macro(4, 127)
        self.assertLess(peak(verb.output, 12, skip=2), 0.95)


if __name__ == "__main__":
    unittest.main()
