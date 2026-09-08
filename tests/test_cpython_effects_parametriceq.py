"""`ParametricEQ`'s own invariant and planted-fault tests.

The class's Tier 2 traits are measured in the evidence pack with the kit;
what is here is the subset a rebuild must not be allowed to regress
silently, each one paired with the fault that turns it red. A checker that
has only ever passed has not been shown to work, so no assertion below
stands without its faulted twin.

The old-surface trait this replaces - `test_cpython_effects_dynamics_eq.py`'s
`test_a_bell_lands_where_it_was_asked_for`, written against the retired
`bands=[(hz, gain, q)]` constructor - was retired in the same commit
(roadmap section 3, "the class gate").

Numpy-free, like `tests/support/effects_measure`: the response readings here
are computed from the node's own `coefficients`, so they measure the section
the class actually built rather than a re-derivation of RBJ.
"""

import array
import cmath
import math
import os
import sys
import unittest

import audiocore

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
import effects_measure                                # noqa: E402
from effects_measure import SAMPLE_RATE, source        # noqa: E402

from audioeffects import _component                    # noqa: E402
from audioeffects import parametriceq          # noqa: E402
#: The subject is named directly. `ParametricEQ` has come home to
#: `audioeffects/parametriceq.py`; `rebuilt.ADOPTED` no longer lists it.
#: These tests still import the home module so a planted-fault subclass is
#: measured against this file, not only `create()`.


def magnitude_db(node, hz, rate=SAMPLE_RATE):
    """|H| of one built section, in dB, read off its live coefficients. A
    section at `mix` 0 is a wire and contributes exactly 0 dB."""
    if node.mix == 0.0:
        return 0.0
    b0, b1, b2, a1, a2 = node.coefficients
    z = cmath.exp(-2j * math.pi * hz / rate)
    return 20.0 * math.log10(abs((b0 + b1 * z + b2 * z * z)
                                 / (1.0 + a1 * z + a2 * z * z)))


def response_db(effect, hz):
    """The whole chain, in dB, at `hz`."""
    return sum(magnitude_db(node, hz) for node in effect._nodes)


def curve(effect, low, high, points=241):
    xs = [low * (high / low) ** (index / (points - 1.0))
          for index in range(points)]
    return xs, [response_db(effect, hz) for hz in xs]


def burst_then_silence(rate=SAMPLE_RATE, burst=4800, seconds=4, channels=2):
    """Tone then zeros **inside one sample**. The dossier's appendix B
    records why: once a `RawSample` ends, the node downstream is not asked to
    filter anything and every configuration reads clean, so a tail probe
    built that way would report a defect that is there as absent."""
    total = rate * seconds
    data = array.array('h', bytes(total * channels * 2))
    for frame in range(burst):
        value = int(20000 * math.sin(2 * math.pi * 200.0 * frame / rate))
        for channel in range(channels):
            data[frame * channels + channel] = value
    return audiocore.RawSample(data, sample_rate=rate,
                               channel_count=channels)


def frames_to_silence(output, rate, burst, limit_seconds=4):
    """Frames from the end of the burst to the first block that is exactly
    zero and stays that way for a second. `None` means it never arrived."""
    frames = 0
    quiet_from = None
    while frames < rate * limit_seconds:
        result, data = audiocore.get_buffer(output)
        block = memoryview(bytes(data)).cast('h')
        if not len(block):
            break
        loudest = max(abs(value) for value in block)
        if loudest == 0:
            if quiet_from is None:
                quiet_from = frames
        else:
            quiet_from = None
        frames += len(block) // 2
        if quiet_from is not None and frames - quiet_from > rate:
            return max(0, quiet_from - burst)
        if result != 1:
            break
    return None


class SurfaceTest(unittest.TestCase):
    def test_the_declared_shape_is_what_the_class_builds(self):
        effect = parametriceq.ParametricEQ.create(source(), SAMPLE_RATE)
        self.addCleanup(effect.deinit)
        self.assertEqual(effect.TIER, 'audioif')
        self.assertEqual(effect.REQUIRES, ("audiobiquad",))
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(len(effect.MACRO_LABELS), 16)
        self.assertEqual(len(effect._nodes), 8)
        self.assertEqual(effect.patch_index, 0)

    def test_the_transport_is_never_read(self):
        # `capabilities` names exactly what the class honours, so a class
        # declaring () must be shown not to read the transport. A transport
        # that raises is the fault: if the class touched it, this would err.
        def explode():
            raise AssertionError("ParametricEQ read the transport")

        effect = parametriceq.ParametricEQ.create(source(), SAMPLE_RATE,
                                     transport=explode)
        self.addCleanup(effect.deinit)
        for patch in range(len(effect.PATCHES)):
            effect.program_change(patch)
        audiocore.get_buffer(effect.output)

    def test_a_span_above_nyquist_clamps_rather_than_refuses(self):
        low = audiocore.RawSample(array.array('h', [4000, -4000] * 2048),
                                  sample_rate=22050, channel_count=2)
        effect = parametriceq.ParametricEQ.create(low, 22050,
                                     high_hz=16000.0, high_boost=10.0,
                                     atten_hz=20000.0, high_atten=10.0)
        self.addCleanup(effect.deinit)
        ceiling = 22050 * 0.5 * 0.98
        self.assertLessEqual(effect._high_boost.frequency, ceiling)
        self.assertLessEqual(effect._high_atten.frequency, ceiling)
        result, data = audiocore.get_buffer(effect.output)
        self.assertTrue(len(bytes(data)))


class WireTest(unittest.TestCase):
    """Patch 0 is a wire, and a section left at unity is not one."""

    #: 12 of the chain's own 256-frame blocks, stereo, 16-bit. Compared by
    #: byte count rather than by pull count, because a `RawSample` hands its
    #: whole buffer back in one call and a chain of nodes hands back 256
    #: frames at a time; comparing pulls would compare different lengths.
    BYTES = 12 * 256 * 2 * 2

    def rendered(self, holder):
        out = bytearray()
        while len(out) < self.BYTES:
            result, data = audiocore.get_buffer(holder.output)
            chunk = bytes(data)
            if not chunk:
                break
            out.extend(chunk)
        return bytes(out[:self.BYTES])

    def test_patch_zero_is_byte_identical_to_the_source(self):
        plain = source()
        effect = parametriceq.ParametricEQ.create(source(), SAMPLE_RATE)
        self.addCleanup(effect.deinit)
        self.assertEqual(self.rendered(effect), self.rendered(_Wrap(plain)))

    def test_an_exactly_zero_db_section_is_a_wire_at_unity_mix_too(self):
        # Worth pinning, because it is the reason the floor is about the
        # 0-127 grid and not about float error: at gain 0 the RBJ numerator
        # and denominator are the same three numbers, so after normalisation
        # b == a bitwise and the recursion reproduces its input exactly.
        plain = source()
        effect = parametriceq.ParametricEQ.create(source(), SAMPLE_RATE)
        self.addCleanup(effect.deinit)
        for node in effect._nodes:
            node.mix = 1.0
        self.assertEqual(self.rendered(effect), self.rendered(_Wrap(plain)))

    def test_planted_fault_the_grid_centre_is_not_flat_without_the_floor(self):
        # Drop `FLAT_DB` and this is what patch 0 becomes: a BIPOLAR macro
        # has no exact centre on the 0-127 grid, so 64/127 on a +/-16 dB bell
        # asks for +0.126 dB and the section runs. Audible or not, it is not
        # a wire, and WIRE has to be able to say so.
        plain = source()
        effect = parametriceq.ParametricEQ.create(source(), SAMPLE_RATE)
        self.addCleanup(effect.deinit)
        bell = effect._bells[0]
        asked = _component.macro_value(effect._MACRO_RANGES[4], 64 / 127.0)
        self.assertAlmostEqual(asked, 0.126, delta=0.001)
        bell.frequency = 1000.0
        bell.Q = parametriceq.proportional_q(asked)
        bell.gain_db = asked
        bell.mix = 1.0
        self.assertNotEqual(self.rendered(effect), self.rendered(_Wrap(plain)))


class TailTest(unittest.TestCase):
    """Silence in, silence out - the invariant this family fails on the
    ported node, with that node as the planted fault."""

    SETTINGS = dict(bell1_hz=20.0, bell1_db=16.0)

    def test_the_worst_section_reaches_exact_zero(self):
        effect = parametriceq.ParametricEQ.create(
            burst_then_silence(), SAMPLE_RATE, **self.SETTINGS)
        self.addCleanup(effect.deinit)
        arrived = frames_to_silence(effect.output, SAMPLE_RATE, 4800)
        self.assertIsNotNone(arrived, "the tail never reached exact zero")
        self.assertLessEqual(arrived, effect.tail_samples)

    def test_planted_fault_the_ported_kernel_holds_dc_for_ever(self):
        # audioif#23, reproduced here rather than cited: the same section on
        # `synthio.Biquad` in an `audiofilters.Filter` parks on a non-zero
        # word and holds it. This is the fault the measurement above must go
        # red on, and it is why the class's tier is audioif.
        import audiofilters
        import synthio
        node = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.LOW_SHELF, 20.0,
                                  Q=0.707, A=10.0 ** (16.0 / 40.0)),
            sample_rate=SAMPLE_RATE, channel_count=2, bits_per_sample=16,
            samples_signed=True, buffer_size=2048)
        self.addCleanup(node.deinit)
        node.play(burst_then_silence())
        self.assertIsNone(frames_to_silence(node, SAMPLE_RATE, 4800),
                          "the ported kernel reached zero, so this fault no "
                          "longer plants the defect it is here to plant")


class LowNetworksTest(unittest.TestCase):
    """T1 - two shelves on different corners, so both at once is not
    cancellation."""

    def measured(self, effect):
        at30 = response_db(effect, 30.0)
        xs, ys = curve(effect, 100.0, 400.0)
        floor = min(ys)
        where = xs[ys.index(floor)]
        _, high = curve(effect, 1000.0, 20000.0, points=81)
        return at30, floor, where, max(abs(value) for value in high)

    def build(self):
        return parametriceq.ParametricEQ.create(source(), SAMPLE_RATE,
                                   low_hz=60.0, low_boost=2.5, low_atten=2.5)

    def test_boost_and_atten_together_lift_the_bottom_and_scoop_above_it(self):
        effect = self.build()
        self.addCleanup(effect.deinit)
        at30, floor, where, flat = self.measured(effect)
        self.assertGreaterEqual(at30, 2.0)
        self.assertLessEqual(floor, -1.0)
        self.assertTrue(100.0 <= where <= 400.0, "minimum at %g Hz" % where)
        self.assertLessEqual(flat, 0.5)

    def test_planted_fault_one_shared_corner_cancels(self):
        # T1's own disconfirmation: put both shelves on one corner - which is
        # what the retired class built - and the scoop disappears.
        effect = self.build()
        self.addCleanup(effect.deinit)
        effect._low_atten.frequency = effect._low_boost.frequency
        at30, floor, where, flat = self.measured(effect)
        self.assertGreater(floor, -1.0,
                           "a shared corner still produced T1's minimum")


class BellLawTest(unittest.TestCase):
    """T4 and T5 - the proportional law and its exact reciprocal."""

    def bell_curve(self, gain_db, hz=1000.0):
        effect = parametriceq.ParametricEQ.create(source(), SAMPLE_RATE,
                                     bell2_hz=hz, bell2_db=gain_db)
        self.addCleanup(effect.deinit)
        return effect

    def upper_one_db_crossing(self, effect):
        xs, ys = curve(effect, 1000.0, 21000.0, points=2001)
        for index in range(len(xs) - 1, 0, -1):
            if (ys[index - 1] - 1.0) * (ys[index] - 1.0) <= 0.0:
                span = ys[index] - ys[index - 1]
                share = (1.0 - ys[index - 1]) / (span if span else 1e-30)
                return xs[index - 1] * (xs[index] / xs[index - 1]) ** share
        return None

    def test_the_skirt_stays_put_while_the_curve_narrows(self):
        crossings = [self.upper_one_db_crossing(self.bell_curve(gain))
                     for gain in (2.0, 6.0, 12.0)]
        self.assertNotIn(None, crossings)
        spread = (max(crossings) - min(crossings)) / min(crossings)
        self.assertLess(spread, 0.05, "crossings %r" % (crossings,))
        widths = [parametriceq.proportional_q(gain)
                  for gain in (2.0, 12.0)]
        self.assertGreaterEqual(widths[1] / widths[0], 3.0)

    def test_planted_fault_constant_q_moves_the_skirt(self):
        # The other half of the S3/S5 axis, reached through the class's own
        # `Q Law` toggle: a fixed Q is what T4 disconfirms on.
        crossings = []
        for gain in (2.0, 12.0):
            effect = self.bell_curve(gain)
            effect.set_macro(14, 127)
            crossings.append(self.upper_one_db_crossing(effect))
        spread = (max(crossings) - min(crossings)) / min(crossings)
        self.assertGreater(spread, 0.05,
                           "constant Q held the skirt, so T4's measurement "
                           "cannot tell the two laws apart")

    def test_cut_is_the_exact_reciprocal_of_boost(self):
        for gain in (6.0, 12.0, 16.0):
            boost = self.bell_curve(gain)
            cut = self.bell_curve(-gain)
            worst = 0.0
            hz = 20.0
            while hz <= 20000.0:
                total = response_db(boost, hz) + response_db(cut, hz)
                worst = max(worst, abs(total))
                hz *= 1.02
            self.assertLess(worst, 0.1, "G = %g dB reached %g dB" %
                            (gain, worst))

    def test_planted_fault_a_signed_gain_q_law_breaks_the_skirts(self):
        # T5's named way of failing: read the sign of the gain in the Q law
        # and the cut comes out a different width from the boost, while the
        # peak still looks right.
        for gain in (12.0,):
            boost = self.bell_curve(gain)
            cut = self.bell_curve(-gain)
            cut._bells[1].Q = parametriceq.proportional_q(gain) * 0.5
            at_peak = response_db(boost, 1000.0) + response_db(cut, 1000.0)
            worst = 0.0
            hz = 20.0
            while hz <= 20000.0:
                worst = max(worst, abs(response_db(boost, hz)
                                       + response_db(cut, hz)))
                hz *= 1.02
            self.assertLess(abs(at_peak), 0.1, "the peak should still look "
                            "right, which is what makes this fault sly")
            self.assertGreater(worst, 0.1)


class HeadroomTest(unittest.TestCase):
    """The level bound the gate audit put on T3 and T5, held as a
    regression.

    Everything above reads the built sections' coefficients, which is a
    small-signal statement: it is true of the filter and says nothing about
    the chain, because every section writes int16 and clips there
    (`audioif_filter_f32.c:43-51`). Rendered, the boost stops being
    delivered while the cut is untouched, and that asymmetry is what breaks
    T5's reciprocal and T3's peak-gain difference above -16 dBFS. The
    numbers are this session's, at 1 kHz through the middle bell.
    """

    def gain_db(self, level, gain):
        dry = effects_measure.rms(effects_measure.sine(1000.0, level=level))
        effect = parametriceq.ParametricEQ.create(
            effects_measure.sine(1000.0, level=level), SAMPLE_RATE,
            bell2_hz=1000.0, bell2_db=gain)
        self.addCleanup(effect.deinit)
        wet = effects_measure.rms(effect.output)
        return 20.0 * math.log10(wet / dry)

    #: -20.0 dBFS and -6.0 dBFS on the int16 scale. The first is the level
    #: every Tier 2 row in the evidence pack was measured at.
    QUIET = 3277
    HOT = 16422

    def test_the_boost_arrives_whole_at_the_level_the_traits_were_measured(self):
        self.assertAlmostEqual(self.gain_db(self.QUIET, 16.0), 16.0,
                               delta=0.1)
        self.assertAlmostEqual(self.gain_db(self.QUIET, -16.0), -16.0,
                               delta=0.1)

    def test_a_hot_probe_clips_the_boost_away_and_leaves_the_cut_alone(self):
        # Not a planted fault: the class's own behaviour at a level a player
        # reaches, and the cause of T3's and T5's disconfirmation. If this
        # test ever goes green at the -6 dBFS end, the bound in the module
        # docstring and the catalogue row has moved and both must be redone.
        boost = self.gain_db(self.HOT, 16.0)
        cut = self.gain_db(self.HOT, -16.0)
        self.assertLess(boost, 11.0, "the +16 dB bell read %+0.2f dB" % boost)
        self.assertGreater(boost, 5.0, "the +16 dB bell read %+0.2f dB" % boost)
        self.assertAlmostEqual(cut, -16.0, delta=0.1)


class BellCheckTest(unittest.TestCase):
    """T2's reading, and the retired one that could not fail.

    The evidence probe's own analysis, held here because the gate audit
    broke it: `local_maximum_near` marked every interior point of a plateau
    a maximum, so all three of T2's clauses read green on a byte-flat wire
    (`docs/effects-phase2-gate-audit.md` section 1, T2). The probe is
    imported lazily - it pulls numpy in through the kit, and nothing else in
    this file does.
    """

    def probe(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                        "tools", "phase2_probes"))
        import parametriceq_traits
        return parametriceq_traits

    def grid(self, points=97):
        return [1000.0 * (20.0 ** (index / (points - 1.0)))
                for index in range(points)]

    def test_a_flat_curve_holds_no_bell(self):
        traits = self.probe()
        hz = self.grid()
        flat = traits.Curve.from_points(hz, [0.0] * len(hz))
        self.assertIsNone(flat.local_maximum_near(10000.0))

    def test_planted_fault_the_retired_rule_calls_a_wire_a_bell(self):
        # The rule as it stood, in one line: `db[i] >= db[i-1] and
        # db[i] >= db[i+1]`. On a plateau every interior point qualifies,
        # and the routine returned the one nearest 10 kHz - 0.010 oct off,
        # whatever the build.
        hz = self.grid()
        db = [0.0] * len(hz)
        found = [index for index in range(1, len(hz) - 1)
                 if db[index] >= db[index - 1] and db[index] >= db[index + 1]]
        self.assertEqual(len(found), len(hz) - 2)
        nearest = min(found, key=lambda i: abs(math.log(hz[i] / 10000.0)))
        self.assertLess(abs(math.log(hz[nearest] / 10000.0, 2.0)), 1.0 / 3.0,
                        "the retired rule put a bell inside T2's bar on a "
                        "curve that is 0.000 dB from flat")

    def test_a_real_bell_is_found_with_its_prominence(self):
        traits = self.probe()
        hz = self.grid()
        # A 13.5 dB peaking response at 10 kHz, Q 1.118 - the section the
        # class builds at T2's settings - written from RBJ's magnitude so the
        # test does not depend on a render.
        peak_db = 13.5
        q = 1.118
        db = []
        for point in hz:
            ratio = point / 10000.0
            detune = (ratio - 1.0 / ratio) * q
            db.append(peak_db - 10.0 * math.log10(1.0 + detune * detune
                                                  * (10.0 ** (peak_db / 10.0)
                                                     - 1.0)
                                                  / (10.0 ** (peak_db / 10.0))
                                                  * 1.0))
        found = traits.Curve.from_points(hz, db).local_maximum_near(10000.0)
        self.assertIsNotNone(found)
        _level, where, distance, prominence = found
        self.assertAlmostEqual(where, 10000.0, delta=200.0)
        self.assertLess(distance, 1.0 / 3.0)
        self.assertGreater(prominence, traits.PROMINENCE_DB)


class _Wrap:
    """The bare source behind the same `output` attribute the renderer
    above reads, so one helper can render either."""

    def __init__(self, sample):
        self.output = sample


if __name__ == "__main__":
    unittest.main()
