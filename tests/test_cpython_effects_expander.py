"""`Expander`'s own planted-fault tests, and the two checks that say a fault
and a reading are worth citing at all.

The Phase 2 gate audit ruled this class **Y\\*** on G3: E4's depth-0 row was green
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
import re
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
    (`audiodsp/src/shared/audiodsp_dynamics.c:377-380`), so the Depth knob is
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


class ZeroTailKeyListenExpander(Expander):
    """The fault behind audiocomponents#146: the class declares no tail
    with Key Listen on, as it did when `tail_samples` was a constant 0."""

    @property
    def tail_samples(self):
        return 0


class TheKeyListenTailIsFinite(unittest.TestCase):
    """With Key Listen on the output is the key filters' signal, which
    rings after the input stops. `tail_samples` bounds that ring at every
    Key Low and Key High, and is 0 with Key Listen off."""

    KEYS = ((25.0, 250.0), (25.0, 35000.0), (100.0, 3000.0),
            (1000.0, 35000.0), (4000.0, 250.0))

    def ring(self, cls, key_low, key_high, listen=1.0):
        """(frames of non-zero output after a loud 1 kHz burst, the class's
        tail_samples at those settings)."""
        burst = tone(1000.0, -3.0, 0.2)
        silent = array.array("h", [0] * (RATE * CHANNELS))
        data = array.array("h", burst)
        data.extend(silent)
        settings = {KEY_LISTEN: listen, KEY_LOW: key_low,
                    KEY_HIGH: key_high, THRESHOLD: -80.0}
        adapter = source_of(data)
        effect = cls.create(adapter, RATE)
        try:
            for index, value in settings.items():
                effect.set_macro(index, position(index, value))
            tail = effect.tail_samples
        finally:
            effect.deinit()
        out = render(cls, data, settings)
        last = 0
        for index in range(len(out) - 1, -1, -1):
            if out[index]:
                last = index // CHANNELS + 1
                break
        return max(0, last - len(burst) // CHANNELS), tail

    def test_the_tail_bounds_the_ring_at_every_key_setting(self):
        for key_low, key_high in self.KEYS:
            ring, tail = self.ring(Expander, key_low, key_high)
            self.assertGreater(ring, 0, (key_low, key_high))
            self.assertLessEqual(ring, tail, (key_low, key_high))
            self.assertLess(tail, 6000, (key_low, key_high))

    def test_the_tail_is_zero_with_key_listen_off(self):
        ring, tail = self.ring(Expander, 25.0, 250.0, listen=0.0)
        self.assertEqual((ring, tail), (0, 0))

    def test_a_tail_of_zero_with_key_listen_on_is_red(self):
        ring, tail = self.ring(ZeroTailKeyListenExpander, 25.0, 35000.0)
        self.assertGreater(ring, tail)


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

    def test_patch_five_keeps_the_peak_position_and_its_own_number(self):
        """audiocomponents#50, the decision: the class ships **one** ratio
        law, the RMS detector's, stated with its scope - and patch 5 keeps
        the peak position it is named for.

        A peak follower riding each cycle of the waveform is what a peak
        follower does; the shortfall is the position working, not a defect
        in the law. `Hard Downward` is the class's gate-adjacent patch and
        the peak detector is what makes it one. Moving it to RMS would have
        changed a shipped sound to tidy a trait table, which is backwards:
        the shipped patch is the product.

        So the number is pinned here instead, at the patch's own settings,
        because a figure quoted in the docstring and the catalogue row and
        asserted nowhere is a figure that drifts. Measured -29.33 %; the
        bar is wide enough to be about the detector rather than about the
        third decimal.
        """
        error = self.slope_error(0.0, 8.0)
        self.assertLess(error, 0.0, "the peak slope over-reads: %r" % error)
        settings = law_settings({RATIO: 8.0, DETECTOR: 0.0})
        patched = Expander.create(source_of(tone(1000.0, -21.0, 0.05)), RATE)
        try:
            patched.program_change(5)
            self.assertEqual(patched.get_macro(DETECTOR), 0,
                             "patch 5 stopped shipping the peak detector")
        finally:
            patched.deinit()
        # And the law's own position is still RMS, so the two do not drift
        # into each other.
        self.assertGreater(settings[DETECTOR], -1.0)
        self.assertEqual(LAW[DETECTOR], 1.0,
                         "E1's operating point is no longer the RMS one")


class TheClaims(unittest.TestCase):
    """The class docstring's figures that the rows above do not reach."""

    def test_there_is_no_hold_and_the_detector_defaults_to_rms(self):
        self.assertNotIn("Hold", Expander.MACRO_LABELS)
        effect = build_for_check(Expander)
        try:
            self.assertEqual(effect.get_macro(DETECTOR), 127)
        finally:
            effect.deinit()

    def test_above_the_threshold_it_is_a_wire(self):
        self.assertAlmostEqual(gain_db(Expander, tone(1000.0, -10.0, 0.5),
                                       law_settings({RATIO: 8.0})),
                               0.0, delta=0.01)

    def test_depth_is_the_floor(self):
        for depth in (-10.0, -20.0):
            got = gain_db(Expander, tone(1000.0, -40.0, 0.5),
                          law_settings({RATIO: 8.0, DEPTH: depth}))
            self.assertAlmostEqual(got, depth, delta=0.5)

    def test_ratio_one_and_depth_zero_are_wires(self):
        ramp = array.array("h", [((i // CHANNELS) * 7 % 65536) - 32768
                                 for i in range(8192 * CHANNELS)])
        for overrides in ({RATIO: 1.0}, {DEPTH: 0.0}):
            out = render(Expander, ramp, law_settings(overrides))
            self.assertEqual(list(out), list(ramp), overrides)

    def test_a_loud_tone_outside_the_key_band_opens_it(self):
        settings = {THRESHOLD: -40.0, RATIO: 4.0, DEPTH: -60.0,
                    KEY_LOW: 4000.0}
        loud = gain_db(Expander, tone(1000.0, -3.0, 0.5), settings)
        quiet = gain_db(Expander, tone(1000.0, -30.0, 0.5), settings)
        self.assertGreater(loud, -1.0)
        self.assertLess(quiet, -10.0)

    def test_an_external_key_drives_the_detector(self):
        settings = law_settings({RATIO: 4.0, DEPTH: -40.0})
        quiet = tone(1000.0, -40.0, 0.5)
        alone = gain_db(Expander, quiet, settings)
        key = source_of(tone(200.0, -6.0, 0.5))
        adapter = source_of(quiet)
        effect = Expander.create(adapter, RATE, key=key)
        for index, value in settings.items():
            effect.set_macro(index, position(index, value))
        frames = len(quiet) // CHANNELS
        out = array.array("h")
        while len(out) < frames * CHANNELS:
            chunk = bytes(audiocore.get_buffer(effect.output, False, 0)[1])
            if not chunk:
                break
            out.frombytes(chunk)
        effect.deinit()
        keyed = rms_db(out[:frames * CHANNELS], frames // 2) - rms_db(
            quiet, frames // 2)
        self.assertLess(alone, -20.0)
        self.assertGreater(keyed, -0.5)

    def test_sine_and_square_of_equal_rms_match(self):
        settings = law_settings({RATIO: 2.0, THRESHOLD: -6.0})
        sine = gain_db(Expander, tone(1000.0, -21.0, 0.5), settings)
        square = gain_db(Expander, tone(1000.0, -21.0, 0.5, square=True),
                         settings)
        self.assertLess(sine, -10.0)
        self.assertLess(abs(sine - square), 0.1)

    def test_latency_is_zero(self):
        data = array.array("h", [0] * (2048 * CHANNELS))
        data[100 * CHANNELS] = data[100 * CHANNELS + 1] = 30000
        out = render(Expander, data, {THRESHOLD: -80.0})
        peak = max(range(0, len(out), CHANNELS), key=lambda i: abs(out[i]))
        self.assertEqual(peak // CHANNELS, 100)
        self.assertEqual(Expander.LATENCY_SAMPLES, 0)

    def test_construction_needs_audiodynamics(self):
        saved = sys.modules["audiodynamics"]
        sys.modules["audiodynamics"] = None
        try:
            with self.assertRaises(ImportError):
                build_for_check(Expander)
        finally:
            sys.modules["audiodynamics"] = saved


CLAIMS = (
    ("`Expander` - a downward expander in the Drawmer DS201's shape.",
     ("TheDetectorBoundsTheLaw.test_rms_holds_the_law_at_the_top_of_the_"
      "ratio_span",)),
    ("A downward expander in the Drawmer DS201's shape: below the threshold, "
     "quiet passages get quieter, by a ratio you set and down to a floor you "
     "set, without the slam of a gate.",
     ("TheDetectorBoundsTheLaw.test_rms_holds_the_law_at_the_top_of_the_"
      "ratio_span", "TheClaims.test_depth_is_the_floor")),
    ("Above the threshold it is a wire.",
     ("TheClaims.test_above_the_threshold_it_is_a_wire",)),
    ("Ratio is how many dB the output falls for every dB the input "
     "falls below the threshold; with the RMS detector the slope "
     "stays within 5 % of it even at 8.",
     ("TheDetectorBoundsTheLaw.test_rms_holds_the_law_at_the_top_of_the_ratio_span",)),
    ("Depth is the floor: a quiet passage falls no further than "
     "that, to within 0.5 dB.",
     ("TheClaims.test_depth_is_the_floor",)),
    ("Ratio 1 and Depth 0 are each a wire, byte for byte.",
     ("TheClaims.test_ratio_one_and_depth_zero_are_wires",)),
    ("Key Low and Key High, the top just under Nyquist, narrow the "
     "band the detector hears, at 12 dB/octave at each end, so a "
     "loud tone outside the band can still open it.",
     ("TheClaims.test_a_loud_tone_outside_the_key_band_opens_it",)),
    ("Pass `key=` another stream and the detector reads that instead of "
     "your signal, the DS201's external key.",
     ("TheClaims.test_an_external_key_drives_the_detector",)),
    ("RMS, the default, gives a sine and a square of equal RMS the "
     "same gain, to within 0.1 dB at Ratio 2 with the band wide "
     "open.",
     ("TheClaims.test_sine_and_square_of_equal_rms_match",
      "TheClaims.test_there_is_no_hold_and_the_detector_defaults_to_rms")),
    ("Peak rides each cycle of the waveform, so the slope falls short of the "
     "ratio and the expander turns into a soft, slightly gritty gate; the "
     "Hard Downward patch is built on it.",
     ("TheDetectorBoundsTheLaw.test_peak_does_not",
      "TheDetectorBoundsTheLaw.test_patch_five_keeps_the_peak_position_and_"
      "its_own_number")),
    ("There is no Hold and no one-shot envelope: the expander "
     "follows the level continuously.",
     ("TheClaims.test_there_is_no_hold_and_the_detector_defaults_to_rms",)),
    ("Latency is zero at every setting.",
     ("TheClaims.test_latency_is_zero",)),
    ("So is the tail, except with Key Listen on, when the key filters ring "
     "on after your signal stops: `tail_samples` bounds that ring, under "
     "6000 frames at 48 kHz.",
     ("TheKeyListenTailIsFinite.test_the_tail_is_zero_with_key_listen_off",
      "TheKeyListenTailIsFinite.test_the_tail_bounds_the_ring_at_every_key_"
      "setting")),
)


def _flat(text):
    return " ".join(text.split())


def claim_problems(doc, claims=CLAIMS):
    """What is wrong between a docstring and `claims`: a sentence missing, a
    named test that does not exist, a figure outside every claim."""
    doc = _flat(doc)
    problems = []
    rest = doc
    for sentence, tests in claims:
        if sentence not in doc:
            problems.append("missing: %s" % sentence)
        rest = rest.replace(sentence, " ")
        for name in tests:
            owner, _, test = name.partition(".")
            if not hasattr(globals().get(owner), test):
                problems.append("no test %s" % name)
    for match in re.finditer(r"\S*\d\S*", rest):
        problems.append("figure outside a claim: %s" % match.group())
    return problems


class Claims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        doc = _expander.__doc__ + " " + Expander.__doc__
        self.assertEqual(claim_problems(doc), [])
        # The checker can fail: a figure outside a claim, a claim the
        # docstring does not carry, a test that does not exist.
        self.assertTrue(claim_problems(doc + " It reads 12 ms."))
        self.assertTrue(claim_problems(doc.replace("within 0.1 dB",
                                                   "within 1 dB")))
        self.assertTrue(claim_problems(
            doc, CLAIMS + (("Latency", ("TheClaims.test_nothing_here",)),)))


#: Not here, because they show only when a knob moves, on a reset or a
#: rejoin, or not at all on a fresh build: `ZeroTailKeyListenExpander`; they
#: render what a knob or a patch renders, so the kit cannot tell them from a
#: setting: `DepthSignFlippedExpander`, `DepthPinnedAtZeroExpander`.
KIT_PLANTS = {
    "RatioPinnedExpander": RatioPinnedExpander,
}


if __name__ == "__main__":
    unittest.main()
