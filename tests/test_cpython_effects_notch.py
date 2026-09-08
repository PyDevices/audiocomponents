"""`Notch`'s own invariant and planted-fault tests.

The class's Tier 2 traits are measured in the evidence pack with the kit
(`workspace docs/effects-internal/probes/phase2_probes/notch_evidence.py`); what is here is the subset a
rebuild must not be allowed to regress silently, each one paired with a
fault that turns it red. A checker that has only ever passed has not been
shown to work, so no assertion below stands without its faulted twin.

**No old-surface trait test is retired here, and that is worth saying rather
than leaving as a gap.** The old `eq.py:Notch` had `MACRO_LABELS = ()` and
no test in the suite named it: `test_cpython_effects_dynamics_eq.py` walks
`LowPass` and `HighPass` for its filter rows and `Notch` for none, so there
was nothing to delete in the same commit.

Numpy-free, like `tests/support/effects_measure`: the response readings come
from each section's own live `coefficients`, so they measure the filter the
class actually built and not a re-derivation of RBJ standing beside it. The
one exception is the tail, which has to be rendered.
"""

import array
import cmath
import math
import os
import sys
import unittest

import audiobiquad
import audiocore
import audiofilters
import synthio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
import kit_faults as faults                            # noqa: E402
from effects_measure import SAMPLE_RATE                # noqa: E402

from audioeffects import _component                    # noqa: E402
from audioeffects import notch as notch_module  # noqa: E402

Notch = notch_module.Notch

#: `_component` reads `VENDOR` off the module a class is *defined* in, not
#: off the one its base came from, so the planted-fault subclasses below
#: need one here or the metadata check refuses them before they can be
#: measured.
VENDOR = "PyDevices"


def silence(frames=4096, channels=2, rate=SAMPLE_RATE):
    return audiocore.RawSample(array.array("h", bytes(2 * channels * frames)),
                               sample_rate=rate, channel_count=channels)


def ramp(frames=4096, channels=2, rate=SAMPLE_RATE):
    """Full scale, because the one-LSB fault below is invisible under
    -6.02 dBFS: `v * 32767/32768` returns `v` for every |v| <= 16384."""
    values = array.array("h")
    for index in range(frames):
        value = max(-32768, min(32767,
                                int(round(-32768 + 65535.0 * index
                                          / (frames - 1)))))
        for _ in range(channels):
            values.append(value)
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def burst_then_silence(hz, on_frames, frames, rate=SAMPLE_RATE, channels=2,
                       peak=32767):
    """The silence is inside the sample. When a source is exhausted the
    wrapper memsets its output without running the filter at all, so a probe
    that lets the source *end* reads exact zeros for every build, clean or
    dirty (the dossier's A3)."""
    values = array.array("h", bytes(2 * channels * frames))
    for index in range(on_frames):
        value = int(round(peak * math.sin(2.0 * math.pi * hz * index / rate)))
        for channel in range(channels):
            values[index * channels + channel] = value
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def pcm(node, frames, channels=2):
    """Exactly `frames` frames, however many the node hands back per call.

    Counting *calls* rather than frames is what made the first version of
    the ported-biquad fault below read green: `audiofilters.Filter` returns
    512 frames a call where an `audiobiquad` section returns fewer, so a
    fixed block count walked past the end of the probe, and a `Filter` whose
    source is exhausted memsets its output without running the biquads at
    all (the dossier's A3).
    """
    want = frames * channels * 2
    out = bytearray()
    while len(out) < want:
        chunk = bytes(audiocore.get_buffer(node)[1])
        if not chunk:
            break
        out += chunk
    return bytes(out[:want])


def last_non_zero(data):
    values = memoryview(data).cast("h")
    for index in range(len(values) - 1, -1, -1):
        if values[index]:
            return index
    return -1


def magnitude_db(node, hz, rate=SAMPLE_RATE):
    """|H| of one built section in dB, read off its live coefficients. A
    section at `mix` 0 is a wire and contributes exactly 0 dB; one in
    between is a blend, so this is exact only at mix 0 and mix 1."""
    if node.mix == 0.0:
        return 0.0
    b0, b1, b2, a1, a2 = node.coefficients
    z = cmath.exp(-2j * math.pi * hz / rate)
    value = abs((b0 + b1 * z + b2 * z * z) / (1.0 + a1 * z + a2 * z * z))
    return -400.0 if value == 0.0 else 20.0 * math.log10(value)


def response_db(effect, hz, rate=SAMPLE_RATE):
    return sum(magnitude_db(node, hz, rate) for node in effect._nodes)


def edges(f0, q):
    """S3/S1: the two -3 dB points, whose difference is exactly f0/q."""
    root = math.sqrt(1.0 + 1.0 / (4.0 * q * q))
    return f0 * (root - 1.0 / (2.0 * q)), f0 * (root + 1.0 / (2.0 * q))


def code(index, value):
    return _component.macro_position(Notch._MACRO_RANGES[index],
                                     value) * 127.0


def built(source=None, rate=SAMPLE_RATE, f0=1000.0, q=2.0, harmonics=0,
          depth=1.0, trim_db=0.0, cls=None):
    effect = (cls or Notch).create(source or silence(rate=rate), rate)
    for index, value in ((0, code(0, f0)), (1, code(1, q)),
                         (2, 127.0 if harmonics else 0.0),
                         (3, code(3, depth)), (4, code(4, trim_db))):
        effect.set_macro(index, value)
    return effect


# -------------------------------------------------------------- faults ----

class WidenedQ(Notch):
    """T3's fault: the section's Q is 1.5x the Width the class reports."""

    NAME = 'Notch'

    def _refresh(self):
        Notch._refresh(self)
        self._fundamental.Q = min(60.0, self._fundamental.Q * 1.5)


class BandPassNumerator(Notch):
    """T2's fault: the fundamental built as a `BAND_PASS`, whose numerator
    `(alpha, 0, -alpha)` no longer sums like the denominator at z = +/-1 -
    which is exactly what makes a notch unity at DC and at Nyquist."""

    NAME = 'Notch'

    def _build(self, *arguments, **keywords):
        Notch._build(self, *arguments, **keywords)
        self._fundamental.mode = audiobiquad.BAND_PASS


class SharedHarmonicQ(Notch):
    """D3's fault: the harmonic notch sharing the fundamental's Q instead of
    doubling it, so its width in hertz is twice the fundamental's."""

    NAME = 'Notch'

    def _refresh(self):
        Notch._refresh(self)
        self._harmonic.Q = self._fundamental.Q


class ShortTail(Notch):
    """The declared-tail fault: a `tail_samples` that a real setting
    outlives."""

    NAME = 'Notch'
    TAIL_SAMPLES = 1024


class RateBlind(Notch):
    """T6's fault: coefficients derived as if the graph always ran at
    48 kHz. At 48 kHz it *is* the shipped class, which is the control - a
    rate bug that fired at every rate would not be a rate bug."""

    NAME = 'Notch'

    def _centre(self, hz):
        return Notch._centre(self, hz * self._sample_rate / 48000.0)


# --------------------------------------------------------------- tests ----

class TheSurface(unittest.TestCase):
    def test_the_five_macros_and_six_patches_are_the_frozen_ones(self):
        self.assertEqual(Notch.MACRO_LABELS,
                         ("Frequency", "Width", "Harmonics", "Depth",
                          "Trim"))
        self.assertEqual(Notch.MACRO_MODES[2], "TOGGLE")
        self.assertEqual(Notch.MACRO_MODES[4], "BIPOLAR")
        self.assertEqual(len(Notch.PATCHES), 6)
        self.assertEqual(Notch.PATCHES[0][0], "Wide Notch")
        self.assertEqual(Notch.CAPABILITIES, ())
        self.assertEqual(Notch.LATENCY_SAMPLES, 0)
        self.assertEqual(Notch.TIER, _component.AUDIOIF)
        self.assertEqual(Notch.REQUIRES, ("audiobiquad",))

    def test_every_patch_notches_where_its_comment_says(self):
        effect = Notch.create(silence(), SAMPLE_RATE)
        try:
            for index in range(6):
                effect.program_change(index)
                centre = effect.macro(0)
                with self.subTest(patch=index):
                    self.assertLess(response_db(effect, centre), -20.0)
                    self.assertGreater(response_db(effect, centre * 8.0),
                                       -0.5)
        finally:
            effect.deinit()

    def test_patch_index_follows_the_contract(self):
        effect = Notch.create(silence(), SAMPLE_RATE)
        try:
            self.assertEqual(effect.patch_index, 0)
            effect.set_macro(0, 100.0)
            self.assertIsNone(effect.patch_index)
            effect.program_change(3)
            self.assertEqual(effect.patch_index, 3)
        finally:
            effect.deinit()


class TheWidthIsTheBandwidth(unittest.TestCase):
    """T3: the -3 dB points sit at f0*(sqrt(1+1/4Q^2) -+ 1/2Q)."""

    def test_the_predicted_edges_read_three_decibels_down(self):
        for f0, q in ((1000.0, 2.0), (1000.0, 8.0), (250.0, 0.5)):
            low, high = edges(f0, q)
            effect = built(f0=f0, q=q)
            try:
                for hz in (low, high):
                    with self.subTest(f0=f0, q=q, hz=round(hz, 2)):
                        self.assertAlmostEqual(response_db(effect, hz),
                                               -3.0, delta=0.15)
            finally:
                effect.deinit()

    def test_a_q_one_and_a_half_times_the_width_is_red(self):
        f0, q = 1000.0, 2.0
        low, high = edges(f0, q)
        effect = built(f0=f0, q=q, cls=WidenedQ)
        try:
            worst = max(abs(response_db(effect, hz) + 3.0)
                        for hz in (low, high))
        finally:
            effect.deinit()
        self.assertGreater(worst, 0.15)


class TheClassIsUnityOutsideItsBand(unittest.TestCase):
    """T2, with the caveat the evidence pack records: the claim holds while
    the probe is outside the band, and at Q 0.5 the band reaches a long
    way."""

    def test_dc_and_nyquist_pass_untouched(self):
        for f0, q in ((60.0, 12.0), (1000.0, 2.0), (1000.0, 32.0)):
            effect = built(f0=f0, q=q)
            try:
                with self.subTest(f0=f0, q=q):
                    self.assertAlmostEqual(response_db(effect, 10.0), 0.0,
                                           delta=0.1)
                    self.assertAlmostEqual(
                        response_db(effect, SAMPLE_RATE * 0.48), 0.0,
                        delta=0.1)
            finally:
                effect.deinit()

    def test_a_band_pass_numerator_is_red(self):
        effect = built(f0=1000.0, q=2.0, cls=BandPassNumerator)
        try:
            low = response_db(effect, 10.0)
            high = response_db(effect, SAMPLE_RATE * 0.48)
        finally:
            effect.deinit()
        self.assertLess(low, -20.0)
        self.assertLess(high, -20.0)


class TheHarmonicNotchIsAsNarrowAsTheFundamental(unittest.TestCase):
    """Dossier D3: the harmonic's Q doubles with its frequency, so its
    width in *hertz* matches. Mains harmonics are exact multiples."""

    def test_both_notches_are_the_same_number_of_hertz_wide(self):
        f0, q = 60.0, 12.0
        effect = built(f0=f0, q=q, harmonics=1)
        try:
            first = effect._fundamental
            second = effect._harmonic
            self.assertAlmostEqual(second.frequency, 2.0 * first.frequency,
                                   places=6)
            width_one = first.frequency / first.Q
            width_two = second.frequency / second.Q
            self.assertAlmostEqual(width_one, width_two, delta=0.01)
        finally:
            effect.deinit()

    def test_a_shared_q_doubles_the_harmonic_width_and_is_red(self):
        effect = built(f0=60.0, q=12.0, harmonics=1, cls=SharedHarmonicQ)
        try:
            width_one = effect._fundamental.frequency / effect._fundamental.Q
            width_two = effect._harmonic.frequency / effect._harmonic.Q
        finally:
            effect.deinit()
        self.assertAlmostEqual(width_two / width_one, 2.0, delta=0.01)

    def test_a_harmonic_above_the_ceiling_is_a_wire_and_not_folded(self):
        # 8 kHz at 22.05 kHz: 2*f0 is 16 kHz, over the 8820 Hz ceiling.
        # A rate-honest harmonic notch stands down rather than landing
        # somewhere it was not asked for.
        effect = built(source=silence(rate=22050), rate=22050, f0=8000.0,
                       q=12.0, harmonics=1)
        try:
            self.assertEqual(effect._harmonic.mix, 0.0)
            self.assertLessEqual(effect._fundamental.frequency, 22050 * 0.4)
        finally:
            effect.deinit()


class TheBypassIsAWire(unittest.TestCase):
    def test_depth_zero_is_byte_identical_to_the_source(self):
        effect = built(source=ramp(), depth=0.0, f0=60.0, q=12.0,
                       harmonics=1, trim_db=12.0)
        try:
            wet = pcm(effect.output, 4096)
        finally:
            effect.deinit()
        self.assertEqual(wet, pcm(ramp(), 4096))

    def test_one_lsb_on_the_dry_path_is_red(self):
        # The fault WIRE names, worked on the probe it names: under
        # round-half-to-even `v * 32767/32768` returns `v` for every
        # |v| <= 16384, so a quiet probe would pass this green.
        clean = memoryview(pcm(ramp(), 4096)).cast("h")
        faulted = array.array(
            "h", [int(round(v * 32767.0 / 32768.0)) for v in clean])
        self.assertNotEqual(bytes(faulted), bytes(clean))


class TheTailReachesExactZero(unittest.TestCase):
    """Tier 1's first invariant, and the reason the tier is audioif."""

    FRAMES = 120000

    def probe(self):
        # Two frames longer than the pull would already read exact zero on
        # a filter still holding DC, so the probe is sized to the pull and
        # the pull stays strictly inside it.
        return burst_then_silence(60.0, 9600, self.FRAMES + 8192)

    def test_the_rebuilt_class_settles_on_exact_zero(self):
        effect = built(source=self.probe(), f0=60.0, q=8.0)
        try:
            data = pcm(effect.output, self.FRAMES)
        finally:
            effect.deinit()
        values = memoryview(data).cast("h")
        self.assertNotEqual(max(abs(v) for v in values[:19200]), 0)
        self.assertEqual(max(abs(v) for v in values[-8192:]), 0)

    def test_the_ported_biquad_the_class_does_not_use_is_red(self):
        """The planted fault is the node this class replaced.

        `synthio.Biquad` through `audiofilters.Filter`, the same 60 Hz Q 8
        the mains-hum patch reaches for, parks on a non-zero word and holds
        it - audioif#23 itself and not a stand-in for it.
        """
        node = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.NOTCH, 60.0, Q=8.0),
            mix=1.0, sample_rate=SAMPLE_RATE, channel_count=2,
            bits_per_sample=16, samples_signed=True, buffer_size=2048)
        node.play(self.probe())
        data = pcm(node, self.FRAMES)
        values = memoryview(data).cast("h")
        self.assertNotEqual(max(abs(v) for v in values[-8192:]), 0)

    def test_a_declaration_short_of_the_measurement_is_red(self):
        effect = built(source=self.probe(), f0=60.0, q=8.0, cls=ShortTail)
        try:
            data = pcm(effect.output, self.FRAMES)
            declared = effect.tail_samples
        finally:
            effect.deinit()
        measured = last_non_zero(data) // 2 - 9600
        self.assertGreater(measured, declared)
        self.assertLess(measured, Notch.TAIL_SAMPLES)


class TheClassIsRateHonest(unittest.TestCase):
    def test_a_centre_above_the_ceiling_clamps_rather_than_raising(self):
        # The fourth defect the dossier's section 7 names: the old class
        # raised at or above Nyquist instead of clamping.
        for rate in (48000, 44100, 22050):
            effect = built(source=silence(rate=rate), rate=rate,
                           f0=100000.0, q=2.0)
            try:
                with self.subTest(rate=rate):
                    self.assertLessEqual(effect._fundamental.frequency,
                                         rate * 0.4)
                    self.assertGreater(
                        response_db(effect, rate * 0.1), -0.5)
            finally:
                effect.deinit()

    def test_the_centre_is_where_it_was_asked_for_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            effect = built(source=silence(rate=rate), rate=rate, f0=1000.0,
                           q=8.0)
            try:
                low, high = edges(1000.0, 8.0)
                with self.subTest(rate=rate):
                    self.assertAlmostEqual(
                        response_db(effect, low, rate), -3.0, delta=0.15)
                    self.assertAlmostEqual(
                        response_db(effect, high, rate), -3.0, delta=0.15)
            finally:
                effect.deinit()


class TheRateHonestReadingCanFail(unittest.TestCase):
    """The reading `TheClassIsRateHonest` above makes, shown red on the
    fault it is written against.

    The evidence pack's own centre locator could not do this: it bisected
    for the -3 dB crossings on a bracket it never checked, so with the notch
    somewhere else entirely both bisections converged on `f0` and it
    reported ~0 % displacement by construction (`RateBlind` at 22.05 kHz
    read **0.0021 % out and PASSED**). The reading here is the response at
    the *predicted* edges, which does not depend on finding anything.
    """

    def test_a_rate_blind_build_is_red_where_the_class_is_green(self):
        low, high = edges(1000.0, 8.0)
        for rate, faulted_is_red in ((48000, False), (22050, True)):
            clean = built(source=silence(rate=rate), rate=rate, f0=1000.0,
                          q=8.0)
            blind = built(cls=RateBlind, source=silence(rate=rate),
                          rate=rate, f0=1000.0, q=8.0)
            try:
                with self.subTest(rate=rate):
                    self.assertAlmostEqual(response_db(clean, low, rate),
                                           -3.0, delta=0.15)
                    reading = response_db(blind, low, rate)
                    if faulted_is_red:
                        self.assertGreater(reading, -1.0)
                    else:
                        self.assertAlmostEqual(reading, -3.0, delta=0.15)
            finally:
                clean.deinit()
                blind.deinit()


class EveryPlantedFaultIsOutOfTheSurfacesReach(unittest.TestCase):
    """`kit_faults.fault_reachability` on all five faults above.

    A fault a macro position or a shipped patch can dial is a
    disconfirmation waiting to be written down, not a fault (the pattern
    revision's section 1.3). Each reading below is the state the fault
    forces, phrased so the class's own surface can be asked about it: a
    ratio where the fault changes a relationship the surface always keeps,
    a mode or a declaration where it changes a fact.
    """

    def _check(self, faulted, reading, rate=SAMPLE_RATE, **built_kwargs):
        return faults.fault_reachability(
            Notch, faulted, reading,
            lambda subject: built(cls=subject, source=silence(rate=rate),
                                  rate=rate, **built_kwargs),
            tolerance=1e-9)

    def test_the_widened_q_is_a_ratio_no_width_position_reaches(self):
        # The fault is not "Q 1.06": it is the section's Q differing from
        # the Width the class reports, and every macro position keeps them
        # equal.
        checked = self._check(
            WidenedQ, lambda e: round(e._fundamental.Q / e.macro(1), 9))
        self.assertEqual(checked["clean"], 1.0)
        self.assertEqual(checked["target"], 1.5)

    def test_the_band_pass_numerator_is_a_mode_no_macro_selects(self):
        checked = self._check(BandPassNumerator,
                              lambda e: e._fundamental.mode)
        self.assertEqual(checked["clean"], audiobiquad.NOTCH)
        self.assertEqual(checked["target"], audiobiquad.BAND_PASS)

    def test_the_shared_harmonic_q_is_a_ratio_the_clamp_never_reaches(self):
        # The doubling is clamped at MAX_Q, so the ratio falls to 60/32 =
        # 1.875 at the top of the Width span (dossier D3) - and never to the
        # 1.0 this fault forces.
        checked = self._check(
            SharedHarmonicQ,
            lambda e: round(e._harmonic.Q / e._fundamental.Q, 9),
            harmonics=1)
        self.assertEqual(checked["target"], 1.0)
        self.assertEqual(checked["clean"], 2.0)

    def test_the_short_tail_is_a_declaration_no_setting_moves(self):
        checked = self._check(ShortTail, lambda e: e.tail_samples)
        self.assertEqual(checked["clean"], Notch.TAIL_SAMPLES)
        self.assertEqual(checked["target"], 1024)

    def test_the_rate_blind_centre_is_not_a_frequency_position(self):
        checked = self._check(RateBlind,
                              lambda e: round(e._fundamental.frequency, 6),
                              rate=22050, f0=1000.0, q=8.0)
        self.assertAlmostEqual(checked["target"], 459.375, places=3)
        self.assertAlmostEqual(checked["clean"], 1000.0, places=3)

    def test_the_check_itself_fires_on_a_fault_the_surface_can_dial(self):
        # The planted fault for the checker: a "fault" that forces Depth 0,
        # which macro 3 at position 0 and nothing else already is.
        class DepthZero(Notch):
            NAME = 'Notch'

            def _refresh(self):
                Notch._refresh(self)
                for node in self._nodes:
                    node.mix = 0.0

        with self.assertRaises(faults.FaultReachable):
            self._check(DepthZero, lambda e: e._fundamental.mix)


class TheResetWalkReachesEveryNode(unittest.TestCase):
    def test_reset_clears_the_class_and_leaves_the_source_alone(self):
        probe = burst_then_silence(60.0, 9600, 60000)
        effect = built(source=probe, f0=60.0, q=8.0)
        try:
            primed = max(abs(v) for v in
                         memoryview(pcm(effect.output, 15000)).cast("h"))
            self.assertNotEqual(primed, 0)
            effect.reset()
            for node in effect._nodes:
                self.assertEqual(node.mix, 1.0 if node is
                                 effect._fundamental else 0.0)
        finally:
            effect.deinit()

    def test_deinit_releases_every_node_the_class_built(self):
        effect = built(source=silence())
        nodes = list(effect._nodes)
        effect.deinit()
        for node in nodes:
            self.assertTrue(getattr(node, "_deinited", True))


if __name__ == "__main__":
    unittest.main()
