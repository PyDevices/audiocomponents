"""`Expander`'s own planted-fault tests, and the two checks that say a fault
and a reading are worth citing at all.

The Phase 2 gate audit ruled this class **Y\\*** on G3
(`docs/effects-phase2-gate-audit.md` section 3): E4's depth-0 row was green
clean *and* green faulted, and E1's ratio-8 row needed the fault driven
downward before it fired. Both faults are replaced here, and this file is
what stops either defect coming back:

* the replacement faults, each red beside its clean control;
* the fault the audit caught, shown **REACHABLE** by
  `kit_faults.fault_reachability()`, so the check is exercised on the input
  it exists to reject;
* the pack's original E2 reading, shown **GREEN on a wire** by
  `kit_faults.null_build_red()`, and this pack's reading shown red on the
  same wire;
* the bound the patch sweep put on E1 - the slope law is the RMS detector's,
  and patch 5 ships the other position.

Every measurement is computed here from renders rather than taken from the
kit's numpy path, so this file runs in the ordinary CPython suite.
"""

import array
import math
import os
import sys
import unittest

import audiocore
import audiofilters

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
import kit_faults as faults                            # noqa: E402

from audioeffects import _component                    # noqa: E402
from audioeffects import expander as _expander  # noqa: E402

#: The subject is named directly. `Expander` has come home to
#: `audioeffects/expander.py`; `rebuilt.ADOPTED` no longer lists it. These
#: tests still import the home module so a planted-fault subclass is
#: measured against this file, not only `create()`.
Expander = _expander.Expander

#: `_component` reads `VENDOR` off the module a class is *defined* in, not
#: off the one its base came from, so the planted-fault subclasses below
#: need one here or the metadata check refuses them before they can be
#: measured.
VENDOR = "PyDevices"

RATE = 48000
CHANNELS = 2
BLOCK = 2048

THRESHOLD, RATIO, DEPTH, ATTACK, RELEASE = 0, 1, 2, 3, 4
KEY_LOW, KEY_HIGH, KEY_LISTEN, DETECTOR = 5, 6, 7, 8


# -- the two replacement faults -------------------------------------------

class RatioPinnedExpander(Expander):
    """E1's fault: the gain computer's ratio is pinned at 12.0 whatever the
    panel says. The Ratio macro's span stops at 8.0, so no position of it
    and no shipped patch can reach that state - which is exactly what the
    fault this replaces could not manage at the top of the span, where
    8 x 1.3 left the span and the faulted build *was* the clean one."""

    _FAULT_RATIO = 12.0

    def _apply_macro(self, index, position):
        Expander._apply_macro(self, index, position)
        if index == RATIO:
            self._node.set(ratio=self._FAULT_RATIO)


class DepthSignFlippedExpander(Expander):
    """E4's fault: `depth_db` reaches the node positive, which the node
    reads as *unset* and answers with its own fixed -60 dB literal
    (`audioif/src/shared/audioif_dynamics.c:377-380`), so the Depth knob is
    dead. The panel's span is 0 ... -80 dB and never reads a positive
    number, so no macro position and no patch can dial it."""

    def _apply_macro(self, index, position):
        if index == DEPTH:
            value = _component.macro_value(self._MACRO_RANGES[index],
                                           position)
            self._node.set(depth_db=abs(value) + 1.0)
        else:
            Expander._apply_macro(self, index, position)


class DepthPinnedAtZeroExpander(Expander):
    """The fault the gate audit caught, kept so the check that rejects it is
    exercised on a real input. Depth pinned at 0 dB **is** macro 2 at grid
    position 0."""

    def _apply_macro(self, index, position):
        if index == DEPTH:
            self._node.set(depth_db=0.0)
        else:
            Expander._apply_macro(self, index, position)


# -- renders ---------------------------------------------------------------

def tone(hz, dbfs, seconds, square=False):
    frames = int(RATE * seconds)
    amplitude = 10.0 ** (dbfs / 20.0)
    data = array.array("h", [0] * frames * CHANNELS)
    for index in range(frames):
        phase = (index * hz / RATE) % 1.0
        if square:
            value = amplitude * (1.0 if phase < 0.5 else -1.0)
        else:
            value = amplitude * math.sqrt(2.0) * math.sin(2 * math.pi * phase)
        word = int(max(-32768, min(32767, round(value * 32767))))
        for channel in range(CHANNELS):
            data[index * CHANNELS + channel] = word
    return data


def source_of(data):
    raw = audiocore.RawSample(data, sample_rate=RATE,
                              channel_count=CHANNELS)
    adapter = audiofilters.Filter(
        filter=None, mix=1.0, sample_rate=RATE, channel_count=CHANNELS,
        bits_per_sample=16, samples_signed=True,
        buffer_size=BLOCK * CHANNELS * 2)
    adapter.play(raw, loop=False)
    return adapter


def position(index, value):
    return _component.macro_position(Expander._MACRO_RANGES[index],
                                     value) * 127.0


def render(cls, data, settings):
    adapter = source_of(data)
    effect = cls.create(adapter, RATE)
    for index, value in settings.items():
        effect.set_macro(index, position(index, value))
    audiocore.reset_buffer(effect.output)
    frames = len(data) // CHANNELS
    out = array.array("h")
    got = 0
    while got < frames:
        _result, buffer = audiocore.get_buffer(effect.output, False, 0)
        chunk = bytes(buffer)
        if not chunk:
            break
        out.frombytes(chunk)
        got += len(chunk) // (2 * CHANNELS)
    effect.deinit()
    adapter.deinit()
    return out[:frames * CHANNELS]


def rms_db(words, start):
    total = 0.0
    count = 0
    for index in range(start * CHANNELS, len(words), CHANNELS):
        value = words[index] / 32768.0
        total += value * value
        count += 1
    if count == 0 or total <= 0.0:
        return -240.0
    return 10.0 * math.log10(total / count)


def gain_db(cls, data, settings):
    """Settled wet:dry gain over the second half of the render."""
    wet = render(cls, data, settings)
    half = (len(data) // CHANNELS) // 2
    return rms_db(wet, half) - rms_db(data, half)


LAW = {THRESHOLD: -20.0, DEPTH: -90.0, ATTACK: 5.0, RELEASE: 50.0,
       DETECTOR: 1.0, KEY_LOW: 25.0, KEY_HIGH: 35000.0}


def law_settings(overrides=None):
    """The E1 operating point, macro-index keyed, with `overrides` applied.
    Keyed by index rather than by name because a macro index is not a
    Python identifier and `**kwargs` refuses it."""
    settings = dict(LAW)
    settings.update(overrides or {})
    return settings


def build_for_check(cls):
    adapter = source_of(tone(1000.0, -30.0, 0.05))
    instance = cls.create(adapter, RATE)
    instance._probe_adapter = adapter
    return instance


class TheReplacementFaultsFire(unittest.TestCase):
    """Each fault red beside its clean control, at every setting the row is
    claimed over - including the two the old faults could not reach."""

    #: 1 dB below the threshold, so the reading is a gain and not a slope
    #: fit: at ratio r the clean class attenuates (r - 1) dB there.
    PROBE = None

    def setUp(self):
        if TheReplacementFaultsFire.PROBE is None:
            TheReplacementFaultsFire.PROBE = tone(1000.0, -21.0, 0.4)
        self.probe = TheReplacementFaultsFire.PROBE

    def test_ratio_pinned_is_red_at_every_ratio_including_the_span_top(self):
        for ratio in (1.5, 2.0, 4.0, 8.0):
            settings = law_settings({RATIO: ratio})
            clean = gain_db(Expander, self.probe, settings)
            dirty = gain_db(RatioPinnedExpander, self.probe, settings)
            self.assertAlmostEqual(clean, -(ratio - 1.0), delta=0.15,
                                   msg="clean control moved at ratio %g"
                                       % ratio)
            self.assertLess(dirty, clean - 3.0,
                            "the pinned ratio did not redden ratio %g: "
                            "clean %.2f dB, faulted %.2f dB"
                            % (ratio, clean, dirty))

    def test_the_old_multiplier_fault_is_the_clean_run_at_the_span_top(self):
        """8 x 1.3 is past the Ratio macro's 8.0 ceiling, so the fault the
        pack shipped could not fire on E1's own top row."""
        settings = law_settings({RATIO: 8.0})
        clean = gain_db(Expander, self.probe, settings)
        old_fault = gain_db(Expander, self.probe,
                            law_settings({RATIO: min(8.0 * 1.3, 8.0)}))
        self.assertAlmostEqual(clean, old_fault, delta=0.01)

    def test_depth_sign_flipped_is_red_at_every_depth_including_zero(self):
        for depth in (0.0, -11.43, -22.86, -34.29):
            level = min(-6.0, depth / 7.0 - 3.0)
            probe = tone(8000.0, level, 0.4)
            settings = law_settings({RATIO: 8.0, THRESHOLD: 0.0,
                                       DEPTH: depth})
            clean = gain_db(Expander, probe, settings)
            dirty = gain_db(DepthSignFlippedExpander, probe, settings)
            self.assertAlmostEqual(clean, depth, delta=0.5,
                                   msg="clean control moved at depth %g"
                                       % depth)
            self.assertGreater(abs(dirty - depth), 0.5,
                               "the sign-flipped depth did not redden "
                               "depth %g: clean %.2f dB, faulted %.2f dB"
                               % (depth, clean, dirty))

    def test_the_old_depth_fault_is_inert_at_depth_zero(self):
        """The defect the gate audit named: at Depth 0 the fault and the
        setting are the same value, so the row was green both ways."""
        probe = tone(8000.0, -6.0, 0.4)
        settings = law_settings({RATIO: 8.0, THRESHOLD: 0.0, DEPTH: 0.0})
        clean = gain_db(Expander, probe, settings)
        old_fault = gain_db(DepthPinnedAtZeroExpander, probe, settings)
        self.assertAlmostEqual(clean, old_fault, delta=0.01)


class TheFaultRunnerRejectsTheOldFault(unittest.TestCase):
    """`kit_faults.fault_reachability()` on the fault the audit caught, and
    on the two that replace it."""

    def test_depth_pinned_at_zero_is_a_macro_position(self):
        with self.assertRaises(faults.FaultReachable) as caught:
            faults.fault_reachability(Expander, 0.0,
                                      lambda e: e.macro(DEPTH),
                                      build_for_check, label="E4 old")
        self.assertIn("macro 2 'Depth' at grid position 0",
                      str(caught.exception))

    def test_the_replacement_states_are_off_the_grid(self):
        for state, macro, label in ((12.0, RATIO, "E1 new"),
                                    (21.0, DEPTH, "E4 new")):
            got = faults.fault_reachability(
                Expander, state, lambda e, i=macro: e.macro(i),
                build_for_check, label=label)
            self.assertGreater(got["checked"], 100)


class TheReadingsGoRedOnAWire(unittest.TestCase):
    """`kit_faults.null_build_red()` on what this pack cites, and on the
    reading it replaces."""

    def gap(self, cls, ratio):
        gains = []
        for square in (False, True):
            probe = tone(1000.0, -21.0, 0.5, square=square)
            gains.append(gain_db(cls, probe, law_settings(
                {THRESHOLD: -6.0, RATIO: ratio, DEPTH: -80.0,
                 RELEASE: 150.0})))
        return abs(gains[0] - gains[1]), gains[0]

    def test_the_packs_own_e2_reading_is_green_on_a_wire(self):
        with self.assertRaises(faults.NullBuildGreen):
            faults.null_build_red(
                Expander,
                lambda cls: {"passed": self.gap(cls, 2.0)[0] <= 0.5},
                label="E2 gap only")

    def test_e2_with_the_expansion_clause_is_red_on_a_wire(self):
        def measure(cls):
            gap, sine = self.gap(cls, 2.0)
            return {"passed": gap <= 0.5 and sine <= -3.0}
        got = faults.null_build_red(Expander, measure, label="E2")
        self.assertFalse(got["null"]["passed"])
        self.assertTrue(got["control"]["passed"])

    def test_e4_is_red_on_a_wire(self):
        def measure(cls):
            probe = tone(8000.0, -6.0, 0.4)
            error = gain_db(cls, probe, law_settings(
                {RATIO: 8.0, THRESHOLD: 0.0, DEPTH: -20.0})) + 20.0
            return {"passed": abs(error) <= 0.5}
        got = faults.null_build_red(Expander, measure, label="E4")
        self.assertFalse(got["null"]["passed"])
        self.assertTrue(got["control"]["passed"])


class TheDetectorBoundsTheLaw(unittest.TestCase):
    """E1's slope law is the RMS detector's. The patch sweep found it: at
    ratio 8 the peak position reads -7.52 % against a 5 % bar, and patch 5
    ships that position. The docstring and the catalogue row say so, and
    this test is what holds them to it."""

    def slope_error(self, detector, ratio):
        settings = law_settings({RATIO: ratio, DETECTOR: detector})
        first = gain_db(Expander, tone(1000.0, -21.0, 0.5), settings)
        second = gain_db(Expander, tone(1000.0, -27.0, 0.5), settings)
        # Two points of the staircase: 6 dB of input travel should produce
        # 6 * ratio dB of output travel.
        slope = ((second + -27.0) - (first + -21.0)) / -6.0
        return 100.0 * (slope - ratio) / ratio

    def test_rms_holds_the_law_at_the_top_of_the_ratio_span(self):
        self.assertLess(abs(self.slope_error(1.0, 8.0)), 5.0)

    def test_peak_does_not(self):
        self.assertGreater(abs(self.slope_error(0.0, 8.0)), 5.0)


if __name__ == "__main__":
    unittest.main()
