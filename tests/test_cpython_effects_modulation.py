"""What the modulation classes do to a signal today.

Ring modulation is the one modulation trait the old surface pinned: the
sidebands are there, both originals are gone, and zero depth is a wire.

Retired by the effects program's **phase 3 - modulation**. Every assertion
here is written against a surface that phase replaces, so when its classes
have been rebuilt - each carrying its own invariant and planted-fault tests
- this module is deleted whole and nothing else in the suite moves. Until
then the contract-level tests over `audioeffects.ALL` in
`test_cpython_effects_library.py` hold the catalogue, and these hold the
character.

Covers `RingMod`.
"""

import math
import os
import sys
import unittest

import audioeffects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import sine, spectrum, tone_gain_db  # noqa: E402


class ModulationTest(unittest.TestCase):
    def test_a_ring_modulator_makes_sidebands_and_keeps_neither_original(
            self):
        # The definition of ring modulation, and the thing no LFO can do: a
        # 1 kHz tone against a 220 Hz carrier comes back as 780 and 1220 and
        # nothing at 1000. A Tremolo at the same settings would keep the
        # 1 kHz and could not reach 220 Hz in the first place.
        effect = audioeffects.RingMod(sine(1000.0, frames=80000),
                                      frequency=220.0)
        # The carrier table holds a whole number of cycles, so it lands a
        # fraction of a hertz off what was asked for; the sidebands are around
        # what it actually is, not around 220.
        carrier = effect.macro(0)
        magnitudes, bin_hz = spectrum(effect.output)

        def peak_near(frequency):
            lo = max(0, int(frequency * 0.97 / bin_hz))
            hi = min(len(magnitudes), int(frequency * 1.03 / bin_hz) + 1)
            return max(magnitudes[lo:hi]) if hi > lo else 0.0

        lower = peak_near(1000.0 - carrier)
        upper = peak_near(1000.0 + carrier)
        self.assertGreater(lower, 0.0)
        self.assertAlmostEqual(20.0 * math.log10(upper / lower), 0.0, delta=1.5)
        self.assertLess(20.0 * math.log10(peak_near(1000.0) / lower), -25.0)
        self.assertLess(20.0 * math.log10(peak_near(carrier) / lower), -25.0)

    def test_a_ring_modulator_at_zero_depth_is_a_wire(self):
        # Depth folds into the carrier table rather than being a second
        # multiply, so zero depth has to come out as a constant carrier -
        # which is the one setting that proves the table is built the way the
        # docstring says it is.
        self.assertAlmostEqual(
            tone_gain_db(1000.0,
                         lambda s: audioeffects.RingMod(s, depth=0.0).output),
            0.0, delta=0.05)
        self.assertAlmostEqual(
            tone_gain_db(1000.0,
                         lambda s: audioeffects.RingMod(s, mix=0.0).output),
            0.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()
