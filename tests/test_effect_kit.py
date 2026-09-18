"""The measurement kit's planted-fault battery, measurements 1-10.

`docs/effects-kit-spec.md` section 6: every planted fault lands as a test
here, in `test_rig_comparator.py`'s shape - **a control that must pass beside
the fault**, or the battery only proves the checker always fails. A
measurement whose planted-fault run is not committed is not one a class gate
may cite.

One test per measurement, each holding both halves:

    WIRE       dry path x 32767/32768, on `ramp_fs` - and green on a quiet
               chord, which is the fault's own material clause
    TAIL       +1 LSB of DC left in the node's state (audioif#23)
    LEVEL      +0.1 dB of hidden gain against a 0.05 dB bar
    CLICK      `latency_samples` reported 256 short, DSP untouched
    STATE      a delay line left full after reset(); an intermediate node
               left live after deinit()
    DIGEST     +256 LSB and -1 LSB in one block, which moves the
               unsigned-byte sum by exactly zero
    RESPONSE   one coefficient moved so the corner shifts 15 %
    SPECTRUM   a -35 dB second harmonic injected under a -60 dB bar
    CURVE      the soft knee replaced by a hard one at the same threshold
               and ratio
    GAINTRACE  a two-stage release collapsed to one stage at the fast
               constant

Five of the ten faults are required to fire on *part* of their readout and
not all of it - that is what separates a measurement from a tripwire - and
each of those tests asserts the green half as hard as the red one.

Renders here are made in process and thrown away. Nothing is read from disk,
so no stale artifact can be mistaken for a fresh one; the committed probe
corpus and the renderer are section 3's and section 4's own deliverables.
"""

import json
import math
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audioeffects                                             # noqa: E402
import kit_faults as faults                                     # noqa: E402
import kit_probes as probes                                     # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

try:                                                            # noqa: E402
    from tools import render_effect                # part A's renderer
except ImportError:                                             # pragma: no cover
    render_effect = None

RATE = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = os.path.join(ROOT, "tools", "effect_probes")


def build(cls_or_name, source, rate=RATE, **options):
    """Through `create(source, sample_rate, **options)`, never the
    module-level `configure()` and never a `patch=` keyword - spec section
    4's construction boundary."""
    if isinstance(cls_or_name, str):
        return audioeffects.create(cls_or_name, source, rate, **options)
    return cls_or_name.create(source, rate, **options)


def render_through(cls_or_name, probe, frames, *, rate=RATE, block=256,
                   probe_name=None, node=None, **options):
    """Render `probe` through the class and return (Render, effect).

    `node` wraps the class's output in a planted-fault node - the cheap way
    to perturb a path without touching a library file.
    """
    source = probes.ArraySource(probe, rate=rate, block=block)
    effect = build(cls_or_name, source, rate, **options)
    tail = effect.output if node is None else node(effect.output)
    name = getattr(cls_or_name, "__name__", cls_or_name)
    return probes.render(tail, frames, rate=rate, block=block,
                         probe=probe_name, class_name=name,
                         latency_samples=effect.latency_samples), effect


def render_source(probe, frames, *, rate=RATE, block=256, probe_name=None):
    return probes.render(probes.ArraySource(probe, rate=rate, block=block),
                         frames, rate=rate, block=block, probe=probe_name,
                         class_name="source")


class WireTest(unittest.TestCase):
    """WIRE - the bypass invariant, byte compared against the source."""

    def test_one_lsb_on_the_dry_path_is_red_on_the_ramp(self):
        probe = probes.ramp_fs(8192)
        frames = len(probe) // 2
        source = render_source(probe, frames, probe_name="ramp_fs")

        clean, effect = render_through("ParametricEQ", probe, frames,
                                       probe_name="ramp_fs")
        control = kit.wire(clean, source,
                           latency_samples=effect.latency_samples)
        self.assertTrue(control["passed"], control["red"])
        self.assertEqual(control["values"]["differing_samples"], 0)

        faulted, effect = render_through("ParametricEQ", probe, frames,
                                         probe_name="ramp_fs",
                                         node=faults.OneLsbScale)
        result = kit.wire(faulted, source,
                          latency_samples=effect.latency_samples)
        self.assertFalse(result["passed"])
        self.assertGreater(result["values"]["differing_samples"], 0)
        self.assertEqual(result["values"]["max_abs_difference_lsb"], 1)

    def test_the_same_fault_is_invisible_below_minus_six_dbfs(self):
        """The fault's own material clause, worked rather than assumed.

        Under round-half-to-even `v * 32767 / 32768` returns `v` for every
        |v| <= 16384, so on material peaking below -6.02 dBFS the faulted
        render is byte-identical and `chord` alone would pass it green. That
        is why WIRE's probe is `ramp_fs` and why it is required.
        """
        probe = probes.quiet_chord(seconds=0.17)
        frames = len(probe) // 2
        source = render_source(probe, frames, probe_name="quiet_chord")
        self.assertLess(kit.peak_db(source.float), -6.02)

        faulted, effect = render_through("ParametricEQ", probe, frames,
                                         probe_name="quiet_chord",
                                         node=faults.OneLsbScale)
        result = kit.wire(faulted, source,
                          latency_samples=effect.latency_samples)
        self.assertTrue(result["passed"],
                        "the material clause has changed: the one-LSB fault "
                        "is visible below -6.02 dBFS after all")


class TailTest(unittest.TestCase):
    """TAIL - silence in, silence out, and the held-DC defect."""

    def test_one_lsb_of_dc_in_the_settled_state_is_red(self):
        probe, burst_end = probes.burst_silence(hz=1000.0, on_ms=200.0,
                                                total_s=1.0)
        frames = len(probe) // 2

        clean, _ = render_through("LowPass", probe, frames,
                                  probe_name="burst_silence",
                                  frequency=1000.0)
        control = kit.tail(clean, burst_end_frame=burst_end)
        self.assertTrue(control["passed"], control["red"])
        self.assertEqual(control["values"]["residual_lsb"], 0)
        self.assertIsNotNone(control["values"]["tail_samples"])

        faulted, _ = render_through("LowPass", probe, frames,
                                    probe_name="burst_silence",
                                    frequency=1000.0,
                                    node=faults.StuckDc)
        result = kit.tail(faulted, burst_end_frame=burst_end)
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["residual_lsb"], 1)
        # A state that never returns to zero has no last non-zero sample,
        # so the tail-length readout goes red with the residual and cannot
        # serve as this measurement's own control.
        self.assertFalse(result["values"]["returns_to_zero"])
        self.assertEqual(len(result["red"]), 2)


class LevelTest(unittest.TestCase):
    """LEVEL - level honesty on the path."""

    def test_a_tenth_of_a_decibel_of_hidden_gain_is_red(self):
        probe = probes.sine(1000.0, 0.5, -26.0)
        frames = 24000
        dry = render_source(probe, frames, probe_name="sine_1k_-26")

        clean, _ = render_through("ParametricEQ", probe, frames,
                                  probe_name="sine_1k_-26")
        control = kit.level(clean, dry, tolerance_db=0.05)
        self.assertTrue(control["passed"], control["red"])

        faulted, _ = render_through(
            "ParametricEQ", probe, frames, probe_name="sine_1k_-26",
            node=lambda source: faults.HiddenGain(source, gain_db=0.1))
        result = kit.level(faulted, dry, tolerance_db=0.05)
        self.assertFalse(result["passed"])
        for measured in result["values"]["rms_db"]:
            self.assertAlmostEqual(measured, 0.1, delta=0.01)


class ClickTest(unittest.TestCase):
    """CLICK - reported latency_samples against measured, at both rates."""

    def test_reporting_256_samples_short_is_red_at_both_rates(self):
        for rate in (48000, 44100):
            # 10 ms of lookahead: the rebuilt `Limiter`'s Lookahead macro
            # tops out there, and the node truncates rather than rounds.
            expected = int(10.0 * rate / 1000.0)
            probe = probes.click_stereo(16384, offset=256)
            dry = render_source(probe, 16384, rate=rate,
                                probe_name="click_stereo")
            digests = []
            for reported, must_pass in ((expected, True),
                                        (expected - 256, False)):
                cls = faults.under_reporting_limiter(reported)
                wet, effect = render_through(cls, probe, 16384, rate=rate,
                                             probe_name="click_stereo",
                                             ceiling_db=-1.0,
                                             lookahead_ms=10.0)
                result = kit.click(wet, dry, effect.latency_samples)
                digests.append(wet.digest)
                self.assertEqual(result["passed"], must_pass,
                                 "%d Hz, reported %d: %s"
                                 % (rate, reported, result["red"]))
                for measured in result["values"]["measured_latency_samples"]:
                    self.assertAlmostEqual(measured, expected, delta=1.0)
            # The DSP is untouched: a latency check that only fires when the
            # sound also changes is not a latency check.
            self.assertEqual(digests[0], digests[1])


class StateTest(unittest.TestCase):
    """STATE - reset(), deinit(), capabilities, and the allocation rule."""

    def _run(self, cls, extra_nodes=(), **options):
        probe, _ = probes.burst_silence(hz=1000.0, on_ms=200.0, total_s=2.0)
        source = probes.ArraySource(probe, rate=RATE, block=256)
        quiet = probes.ArraySource(probes.silence(96000), rate=RATE,
                                   block=256)
        switch = probes.SwitchableSource(source)
        effect = build(cls, switch, RATE, **options)
        name = getattr(cls, "__name__", cls)

        def pull(blocks):
            return probes.render(effect.output, blocks * 256, rate=RATE,
                                 block=256, probe="burst_silence",
                                 class_name=name)

        nodes = None
        if extra_nodes:
            nodes = kit.enumerate_nodes(effect) + list(extra_nodes)
        return kit.state(effect, pull=pull, swap=switch.swap,
                         probe_source=source, silent_source=quiet,
                         blocks=64, alloc_pulls=100, nodes=nodes)

    def test_a_delay_line_left_full_after_reset_is_red(self):
        options = {"time_ms": 150.0, "feedback": 0.5, "mix": 0.5}
        control = self._run(audioeffects.DigitalDelay, **options)
        self.assertTrue(control["passed"], control["red"])
        self.assertEqual(control["values"]["reset_residual_lsb"], 0)
        self.assertTrue(control["values"]["resumed"])

        result = self._run(faults.NoResetDelay, **options)
        self.assertFalse(result["passed"])
        self.assertGreater(result["values"]["reset_residual_lsb"], 0)
        # The fault fires on the reset readout and nowhere else.
        self.assertEqual(result["values"]["live_nodes_after_deinit"], [])
        self.assertEqual(len(result["red"]), 1)

    def test_an_intermediate_node_left_live_after_deinit_is_red(self):
        options = {"time_ms": 150.0, "feedback": 0.5, "mix": 0.5}
        result = self._run(faults.LiveIntermediateDelay, **options)
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["live_nodes_after_deinit"], ["pre"])
        self.assertEqual(result["values"]["reset_residual_lsb"], 0)
        self.assertEqual(len(result["red"]), 1)

    # -- the register, and the two faults that used to read green ---------
    #
    # STATE walks `enumerate_nodes()`, and until audiocomponents#53 that was
    # an attribute scan skipping private names. Every node a
    # `_component.Component` builds hangs off a private one, so the walk
    # found the output node alone - one of three on `LowPass`, one of eight
    # on `ParametricEQ`, one of twelve on `GraphicEQ` and on `DeEsser` - and
    # a fault in any other node was invisible. Both tests below assert the
    # count as well as the verdict, because a red for the wrong reason on a
    # one-node walk would look the same as a red on the whole register.

    def test_the_walk_covers_the_register_and_not_one_attribute(self):
        result = self._run(audioeffects.LowPass, frequency=2000.0)
        self.assertTrue(result["passed"], result["red"])
        self.assertEqual(len(result["values"]["nodes"]), 3)
        self.assertEqual(result["values"]["leaked_nodes_after_deinit"], [])
        self.assertEqual(result["values"]["nodes_without_deinit"], [])

    def test_a_section_the_class_declines_to_release_is_red(self):
        result = self._run(faults.UnreleasableSectionLowPass,
                           frequency=2000.0)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["values"]["nodes"]), 3)
        self.assertEqual(result["values"]["leaked_nodes_after_deinit"],
                         ["_pole_one"])
        # The fault fires on the deinit readout and nowhere else.
        self.assertEqual(result["values"]["reset_residual_lsb"], 0)
        self.assertEqual(len(result["red"]), 1)

    def test_a_section_built_and_never_registered_is_red(self):
        result = self._run(faults.UnregisteredSectionLowPass,
                           frequency=2000.0)
        self.assertFalse(result["passed"])
        # Reported by the attribute it still hangs off, and named for what
        # is wrong with it: nothing the class walks will ever reach it.
        self.assertEqual(result["values"]["leaked_nodes_after_deinit"],
                         ["_pole_two (unregistered)"])
        self.assertEqual(result["values"]["reset_residual_lsb"], 0)
        self.assertEqual(len(result["red"]), 1)

    def test_a_node_with_no_deinit_is_recorded_and_is_not_a_leak(self):
        """The other half of the split, and the reason there is one.

        A node type with no `deinit()` cannot be released by anybody, so a
        class that builds one is not at fault for it. Reported as one number
        with real leaks, it made every audioif-tier class read like a leak.
        `audioroute.Splitter` was that node until audioif#58 gave it a
        `deinit()`; Compressor now releases everything, and the gap half is
        held to its behaviour with a planted node that has none.
        """
        result = self._run(audioeffects.Compressor)
        self.assertEqual(result["values"]["leaked_nodes_after_deinit"], [])
        self.assertEqual(result["values"]["nodes_without_deinit"], [])

        class NoDeinit:
            channel_count = 2

        planted = self._run(audioeffects.Compressor,
                            extra_nodes=[("planted", NoDeinit())])
        self.assertEqual(planted["values"]["leaked_nodes_after_deinit"], [])
        self.assertEqual(planted["values"]["nodes_without_deinit"],
                         ["planted [NoDeinit]"])


class DigestTest(unittest.TestCase):
    """DIGEST - FNV-1a over the PCM bytes, and the statistic it replaces."""

    def _render(self):
        probe = probes.sine(1000.0, 0.2, -12.0)
        render, _ = render_through("LowPass", probe, 9600,
                                   probe_name="sine_1k_-12",
                                   frequency=2000.0)
        return render

    def test_plus_256_and_minus_one_lsb_move_the_byte_sum_by_zero(self):
        one, other = self._render(), self._render()
        control = kit.digest({"cpython": one, "cpython_again": other})
        self.assertTrue(control["passed"], control["red"])

        pcm, raised, lowered = faults.corrupt_one_block(other.pcm)
        perturbed = kit.Render(pcm, RATE, 2, block=256, interpreter="cpython",
                               label="perturbed")
        self.assertLess(raised, 256 * 2 * 2)
        self.assertLess(lowered, 256 * 2 * 2)

        # The documented blindness, computed rather than recalled: the +256
        # raises one sample's high byte by one and the -1 lowers another's
        # low byte by one, so the unsigned-byte sum moves by exactly zero.
        self.assertEqual(perturbed.byte_sum, one.byte_sum)
        self.assertNotEqual(perturbed.digest, one.digest)

        result = kit.digest({"cpython": one, "perturbed": perturbed})
        self.assertFalse(result["passed"])
        self.assertIn("differ", result["red"][0])


class ResponseTest(unittest.TestCase):
    """RESPONSE - magnitude and phase against frequency."""

    TONES = (200.0, 400.0, 700.0, 900.0, 1000.0, 1100.0, 1150.0, 1300.0,
             1600.0, 2000.0, 4000.0)

    #: The control and the fault must be the same class, and
    #: `ShiftedCornerLowPass` is a subclass of the *rebuilt* `LowPass` -
    #: which is parked, so `faults.LowPass` is the old one
    #: (`kit_faults.LowPass` names the rebuilt class).
    def _curve(self, cls):
        wet, dry = {}, {}
        for hz in self.TONES:
            probe = probes.sine(hz, 0.3, -12.0)
            wet[hz], _ = render_through(cls, probe, 14400,
                                        probe_name="tones_step",
                                        frequency=1000.0, q=0.707)
            dry[hz] = render_source(probe, 14400, probe_name="tones_step")
        return kit.response(wet, dry, reference_hz=200.0,
                            expected={"corner_hz": (1000.0, 5.0),
                                      "passband_db": (0.0, 0.2)})

    def test_a_corner_moved_fifteen_percent_is_red(self):
        control = self._curve(faults.LowPass)
        self.assertTrue(control["passed"], control["red"])
        self.assertAlmostEqual(control["values"]["corner_hz"], 1000.0,
                               delta=10.0)

        result = self._curve(faults.ShiftedCornerLowPass)
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(result["values"]["corner_hz"], 1150.0,
                               delta=15.0)
        # The corner goes red while the passband gain stays green: a fault
        # that fires on part of the readout and not all of it.
        self.assertEqual(len(result["red"]), 1)
        self.assertIn("corner", result["red"][0])
        self.assertAlmostEqual(result["values"]["passband_db"], 0.0,
                               delta=0.2)


class SpectrumTest(unittest.TestCase):
    """SPECTRUM - harmonic, inharmonic and sideband readouts."""

    BARS = {"h2": -60.0, "alias_floor_db": -50.0}

    def test_an_injected_second_harmonic_is_red_on_the_harmonic_readout(self):
        probe = probes.sine(1000.0, 0.5, -6.0)
        clean, _ = render_through("ParametricEQ", probe, 24000,
                                  probe_name="sine_1k_-6")
        control = kit.spectrum(clean, 1000.0, harmonics=10, bars=self.BARS)
        self.assertTrue(control["passed"], control["red"])

        faulted, _ = render_through(
            "ParametricEQ", probe, 24000, probe_name="sine_1k_-6",
            node=lambda source: faults.H2Inject(source, h2_db=-35.0,
                                                amplitude=10 ** (-6.0 / 20)))
        result = kit.spectrum(faulted, 1000.0, harmonics=10, bars=self.BARS)
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(result["values"]["harmonic_db"]["h2"], -35.0,
                               delta=1.0)
        # Red on the harmonic readout, green on the alias readout.
        self.assertEqual(len(result["red"]), 1)
        self.assertIn("h2", result["red"][0])
        self.assertLess(result["values"]["alias_floor_db"],
                        self.BARS["alias_floor_db"])


def _rounded_length(frames, rate, hz):
    """`exact_bin_size` as it was until the fix below: the largest whole
    number of periods that fits, with the product rounded to an integer.

    It is here as SPECTRUM's eleventh planted fault. The rounding is a
    fraction of a sample - 11976 instead of 4800 or 9600 at 1010 Hz /
    48 kHz, a quarter of a sample short of whole periods - and a
    rectangular transform charges tens of dB for it.
    """
    period = rate / float(hz)
    periods = int(frames / period)
    if periods < 1:
        return None
    return max(64, min(int(round(periods * period)), frames))


class ExactBinSizeTest(unittest.TestCase):
    """SPECTRUM's transform length, and the fault it used to be.

    Every Phase 4 gate reads its alias floor through `spectrum()` with the
    default length, so the length is the instrument and not a detail. A pure
    16-bit sine has no alias products at all: the whole reading is the
    quantisation floor, about -95 dB here, and anything above that is the
    transform's own leakage being counted as the class's.

    The fault and its control are the same render read twice. At 1010 Hz /
    48 kHz over 12000 settled frames the old rounding's 11976 samples read
    **-47.0 dB**, and the exact 9600 reads **-95.1 dB** - so a class whose
    gate says "alias floor below -60 dB" failed on 48 dB of arithmetic. The
    fault fires on the inharmonic readout and not on the harmonic one: THD
    over the same two lengths moves from -88.9 dB to -117.4 dB, which is
    wrong by less than a gate's margin and is why this went unnoticed.
    """

    #: Rate, fundamental, and the exact length `exact_bin_size` owes each
    #: over 12000 settled frames. 3700 Hz at 48 kHz is the control the other
    #: way round: 12000 frames is already 925 whole periods, so the old
    #: rounding had nothing to round and both lengths agree.
    CASES = ((48000, 1010.0, 9600), (44100, 1010.0, 8820),
             (22050, 1010.0, 11025), (48000, 3700.0, 12000),
             (44100, 3700.0, 11907), (22050, 3700.0, 11907))

    def _tone(self, hz, rate, frames=24000, dbfs=-3.0):
        """A pure tone as a `Render`, nothing rendered through anything.

        `settled_ratio` defaults to 0.5, so a 24000-frame render is the
        12000 settled frames the numbers above are quoted at.
        """
        pcm = probes.sine(hz, frames / float(rate), dbfs, rate=rate,
                          channels=2)
        return kit.Render.from_pcm(pcm, rate, 2)

    def test_the_default_length_is_whole_periods_at_every_rate(self):
        for rate, hz, expected in self.CASES:
            settled = 12000
            self.assertEqual(kit.exact_bin_size(settled, rate, hz), expected)
            # Whole periods is the claim; this is the claim as arithmetic.
            cycles = expected * hz / rate
            self.assertEqual(cycles, round(cycles))

    def test_a_pure_tone_reads_the_quantisation_floor_not_the_leakage(self):
        for rate, hz, expected in self.CASES:
            tone = self._tone(hz, rate)
            result = kit.spectrum(tone, hz, harmonics=10)
            values = result["values"]
            # The floor first, because it is the reading a gate cites: put
            # the old rounding back and this is the line that fires,
            # -47.046 dB against a -90 dB bar at 1010 Hz / 48 kHz.
            self.assertLess(values["alias_floor_db"], -90.0,
                            "%g Hz at %d on %d samples: %s"
                            % (hz, rate, values["transform_length"], values))
            self.assertEqual(values["transform_length"], expected)

    def test_the_old_rounding_reads_the_same_render_tens_of_dB_high(self):
        """The planted fault, one line of it: the same render, the same
        measurement, the old length passed in by hand."""
        for rate, hz, expected in self.CASES:
            tone = self._tone(hz, rate)
            old = _rounded_length(12000, rate, hz)
            faulted = kit.spectrum(tone, hz, harmonics=10, size=old)
            floor = faulted["values"]["alias_floor_db"]
            if old == expected:
                # 3700 Hz at 48 kHz - the rounding had nothing to round.
                self.assertLess(floor, -90.0)
                continue
            self.assertGreater(floor, -60.0, "%g Hz at %d read %.1f dB on "
                               "%d samples - the fault has stopped firing"
                               % (hz, rate, floor, old))
            self.assertGreater(
                floor - kit.spectrum(tone, hz,
                                     harmonics=10)["values"]["alias_floor_db"],
                25.0)

    def test_the_fallback_returns_a_sane_length_and_still_reads_low(self):
        """1000.3 Hz is commensurable - 10003/10 - but its exact length is
        480000 samples, ten seconds, so nothing that fits is exact. A
        frequency with no rational behind it at all (1000 * sqrt 2) reaches
        the same branch. Both fall back to rounding, and the fallback owes
        the caller the *least wrong* period count rather than the largest:
        139 periods of 1000.3 Hz is 0.0002 samples short, where the old
        rule's 250 was 0.4 short and read -42.6 dB.
        """
        for hz in (1000.3, 1000.0 * math.sqrt(2.0)):
            size = kit.exact_bin_size(12000, 48000, hz)
            self.assertIsNotNone(size)
            self.assertGreaterEqual(size, 64)
            self.assertLessEqual(size, 12000)
            # Shorter than the render, and honestly so: the whole point is
            # that it is closer to whole periods than any longer count.
            period = 48000 / hz
            self.assertLess(abs(size / period - round(size / period)), 0.01)
            floor = kit.spectrum(self._tone(hz, 48000), hz,
                                 harmonics=10)["values"]["alias_floor_db"]
            self.assertLess(floor, -90.0, "%g Hz on %d samples" % (hz, size))

    def test_less_than_one_period_has_no_length_to_offer(self):
        # 1000 Hz at 48 kHz is 48 samples a period; 47 frames cannot hold
        # one, and the answer is None rather than a length nobody can use.
        self.assertIsNone(kit.exact_bin_size(47, 48000, 1000.0))
        # One period fits, and the 64-sample floor beats it - the one case
        # where the length is padded rather than periodic, unchanged from
        # before the fix and far below any render a gate measures.
        self.assertEqual(kit.exact_bin_size(48, 48000, 1000.0), 64)


class CurveTest(unittest.TestCase):
    """CURVE - the static level-in/level-out law."""

    LEVELS = (-48, -42, -36, -33, -30, -28, -26, -24, -22, -20, -18, -15,
              -12, -9, -6)
    EXPECTED = {"threshold_db": (-23.5, 1.0), "knee_db": (12.0, 2.0),
                "ratio": (4.05, 0.3)}

    def _curve(self, knee_db):
        renders = {}
        for level in self.LEVELS:
            probe = probes.sine(1000.0, 0.5, level)
            # `character="fet"` because CURVE's subject is the textbook
            # single-stage law, and the Phase 2 rebuild's default character
            # is the LA-2A: two stages, its own fixed times, and a memory.
            # Naming the character here pins the fixture; it does not move
            # a bar.
            renders[level], _ = render_through(
                "Compressor", probe, 24000,
                probe_name="sine_1k_%d" % level, character="fet",
                threshold_db=-24.0, ratio=4.0, attack_ms=1.0,
                release_ms=50.0, knee_db=knee_db, makeup_db=0.0)
        return kit.curve(renders, detector="peak", expected=self.EXPECTED)

    def test_a_hard_knee_at_the_same_threshold_and_ratio_is_red(self):
        control = self._curve(12.0)
        self.assertTrue(control["passed"], control["red"])
        self.assertAlmostEqual(control["values"]["knee_db"], 12.0, delta=2.0)

        result = self._curve(0.0)
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(result["values"]["knee_db"], 0.0, delta=2.0)
        # The knee width goes red while the threshold and the slope above it
        # stay green, and the move is far larger than the fit's own residual.
        self.assertEqual(len(result["red"]), 1)
        self.assertIn("knee_db", result["red"][0])
        self.assertLess(result["values"]["fit_residual_db"], 0.5)


class GaintraceTest(unittest.TestCase):
    """GAINTRACE - gain reduction against time.

    No shipped class has a two-stage release to perturb - the node carries
    one `release_ms` - so the control and the fault are both the kit's own
    `TwoStageRelease`, built to the spec's shape.
    """

    EXPECTED = {"release_t63_ms": (34.4, 5.0), "release_t95_ms": (605.0,
                                                                  60.0)}

    def _trace(self, collapsed):
        probe, _ = probes.step_tone(1000.0, [(0.5, -6.0), (2.0, -40.0)])
        frames = len(probe) // 2
        source = probes.ArraySource(probe, rate=RATE, block=256)
        effect = faults.TwoStageRelease(source, collapsed=collapsed)
        wet = probes.render(effect.output, frames, rate=RATE, block=256,
                            probe="step_tone", class_name="TwoStageRelease")
        dry = render_source(probe, frames, probe_name="step_tone")
        return kit.gaintrace(wet, dry, hop_ms=1.0, release_from_ms=500.0,
                             attack_from_ms=0.0, expected=self.EXPECTED)

    def test_a_two_stage_release_collapsed_to_one_stage_is_red_on_t95(self):
        control = self._trace(collapsed=False)
        self.assertTrue(control["passed"], control["red"])
        self.assertAlmostEqual(control["values"]["release_from_gr_db"],
                               -13.5, delta=0.5)

        result = self._trace(collapsed=True)
        self.assertFalse(result["passed"])
        # t95 red, t63 green - the fault fires on part of the readout.
        self.assertEqual(len(result["red"]), 1)
        self.assertIn("t95", result["red"][0])
        self.assertAlmostEqual(result["values"]["release_t63_ms"],
                               control["values"]["release_t63_ms"],
                               delta=1.0)
        self.assertLess(result["values"]["release_t95_ms"],
                        0.25 * control["values"]["release_t95_ms"])


class ReadoutsTest(unittest.TestCase):
    """The legs of these ten measurements that the fault battery above does
    not walk: TAIL's `dc_step` leg, DIGEST's paired-build mode and its
    ordering export, GAINTRACE's level search, and SPECTRUM's sideband and
    block-rate readouts. A readout nobody has run is a readout nobody has
    proven, and a class gate would be citing it first.
    """

    def test_tail_reads_the_dc_step_leg_and_the_residue_turns_it_red(self):
        burst, burst_end = probes.burst_silence(hz=1000.0, on_ms=200.0,
                                                total_s=1.0)
        step, removed = probes.dc_step(level=0.5, hold_s=0.5, total_s=1.5)

        def measure(node):
            one, _ = render_through("LowPass", burst, len(burst) // 2,
                                    probe_name="burst_silence",
                                    frequency=1000.0, node=node)
            two, _ = render_through("LowPass", step, len(step) // 2,
                                    probe_name="dc_step", frequency=1000.0,
                                    node=node)
            return kit.tail(one, burst_end_frame=burst_end, dc_render=two,
                            dc_removed_frame=removed)

        control = measure(None)
        self.assertTrue(control["passed"], control["red"])
        # The offset is there while the source supplies it and gone the
        # moment it is removed - the audioif#23 shape, read both ways.
        self.assertAlmostEqual(control["values"]["dc_while_supplied_lsb"],
                               16384.0, delta=2.0)
        self.assertEqual(control["values"]["dc_residual_lsb"], 0)

        result = measure(faults.StuckDc)
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["dc_residual_lsb"], 1)
        self.assertIn("dc_step", result["red"][-1])

    def test_digest_paired_build_mode_and_its_ordering(self):
        def compressor(knee_db):
            probe = probes.sine(1000.0, 0.2, -12.0)
            render, _ = render_through("Compressor", probe, 9600,
                                       probe_name="sine_1k_-12",
                                       character="fet",
                                       threshold_db=-24.0, ratio=4.0,
                                       knee_db=knee_db, makeup_db=0.0)
            return render

        soft, hard = compressor(12.0), compressor(0.0)
        paired = kit.digest({"soft_knee": soft, "hard_knee": hard},
                            mode="distinct")
        self.assertTrue(paired["passed"], paired["red"])

        # A paired build whose two sides are byte-identical is the failure
        # that mode exists to catch.
        same = kit.digest({"soft_knee": soft, "soft_knee_again": soft},
                          mode="distinct")
        self.assertFalse(same["passed"])

        # The comparison fails on an ordering, never on a magnitude, so the
        # ordering is the export.
        broken = kit.digest({"soft_knee": soft, "hard_knee": hard},
                            mode="distinct",
                            ordering=[("soft_gr_db", 3.0),
                                      ("hard_gr_db", 1.0)])
        self.assertFalse(broken["passed"])
        self.assertIn("ordering", broken["red"][0])

    def test_gaintrace_finds_the_level_that_holds_a_stated_reduction(self):
        """Many rows are stated at a gain-reduction depth rather than at an
        input level - "at 3, 10 and 20 dB of GR". Without the search they
        are not measurable at all."""

        def pair(level_db):
            probe, _ = probes.step_tone(1000.0, [(1.0, level_db)])
            source = probes.ArraySource(probe, rate=RATE, block=256)
            effect = faults.TwoStageRelease(source)
            wet = probes.render(effect.output, len(probe) // 2, rate=RATE,
                                block=256, probe="step_tone",
                                class_name="TwoStageRelease")
            return wet, render_source(probe, len(probe) // 2,
                                      probe_name="step_tone")

        result = kit.gaintrace_level_search(pair, 10.0, low_db=-40.0,
                                            high_db=-1.0, hop_ms=1.0)
        search = result["values"]["level_search"]
        self.assertAlmostEqual(abs(search["settled_gr_db"]), 10.0,
                               delta=0.1)
        self.assertLess(search["found_input_db"], 0.0)

    def test_spectrum_reads_sidebands_and_block_rate_lines(self):
        probe = probes.sine(1000.0, 0.5, -12.0)
        render, _ = render_through("RingMod", probe, 24000,
                                   probe_name="sine_1k_-12",
                                   frequency=300.0, depth=1.0, mix=1.0)
        result = kit.spectrum(render, 1000.0, harmonics=4,
                              modulator_hz=300.0, block_frames=256)
        sidebands = result["values"]["sideband_db"]
        # A ring modulator keeps neither original: the sum and difference
        # lines stand far above what is left of the carrier.
        self.assertGreater(sidebands["upper1"], 60.0)
        self.assertGreater(sidebands["lower1"], 60.0)
        self.assertAlmostEqual(result["values"]["block_rate_db"]
                               ["block_rate_hz"], 187.5, places=3)


@unittest.skipIf(render_effect is None or not os.path.exists(
    os.path.join(PROBES, "probes.json")),
    "tools/render_effect.py and tools/effect_probes/ are part A's")
class RendererIntegrationTest(unittest.TestCase):
    """Part B's measurements over part A's renderer and part A's committed
    probes, end to end.

    The battery above renders in process, which keeps a planted fault cheap
    but proves nothing about the file a class gate will actually read. This
    runs one measurement each way through the real path: the probe from
    `tools/effect_probes/`, the render from `tools/render_effect.py`, the
    WAV off disk, the number from `tools/effect_measurements.py`.
    """

    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="effect-kit-")
        self.addCleanup(shutil.rmtree, self.directory, True)
        with open(os.path.join(PROBES, "probes.json")) as handle:
            self.manifest = json.load(handle)

    def probe(self, name, rate=RATE, channels=2):
        entry = self.manifest["probes"][name]["files"]["%d/%d"
                                                       % (rate, channels)]
        path = os.path.join(PROBES, entry["path"])
        render = kit.Render.from_wav(path, block=None, interpreter="cpython",
                                     probe=name)
        # Section 3's stale-probe guard, and a cross-check of the two FNV
        # implementations at the same time: the manifest's digest was
        # written by make_probes.py, this one is read back here.
        self.assertEqual("%08x" % render.digest, entry["fnv1a"])
        return path, render

    def render_through(self, name, path, frames, *, node=None, rate=RATE,
                       channels=2, block=256, **options):
        source, handle, route, _ = render_effect.probe_source(path, rate,
                                                              channels)
        self.addCleanup(lambda: handle and handle.close())
        adapter = render_effect.block_adapter(source, rate, channels, block)
        effect = audioeffects.create(name, adapter, rate, **options)
        tail = effect
        if node is not None:
            tail = _Tail(node(effect.output))
        out = os.path.join(self.directory, "%s-%s.wav" % (name, id(tail)))
        digest, byte_sum, nonzero, written, blocks = render_effect.render(
            tail, out, rate, channels, frames)
        render = kit.Render.from_wav(out, block=block, interpreter=route,
                                     probe=os.path.basename(path),
                                     class_name=name,
                                     latency_samples=effect.latency_samples)
        # The renderer hashes incrementally as it streams; this reads the
        # finished file. A kit whose two FNVs disagree has a bug in one of
        # them and no way to tell which render a gate cited.
        self.assertEqual(render.digest, digest)
        self.assertEqual(render.byte_sum, byte_sum)
        self.assertEqual(render.frames, written)
        return render, effect

    def test_wire_reads_a_rendered_file_and_the_planted_fault_is_red(self):
        path, source = self.probe("ramp_fs")
        clean, effect = self.render_through("ParametricEQ", path,
                                            source.frames)
        control = kit.wire(clean, source,
                           latency_samples=effect.latency_samples)
        self.assertTrue(control["passed"], control["red"])

        faulted, effect = self.render_through("ParametricEQ", path,
                                              source.frames,
                                              node=faults.OneLsbScale)
        result = kit.wire(faulted, source,
                          latency_samples=effect.latency_samples)
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["max_abs_difference_lsb"], 1)

    def test_click_reads_the_committed_click_probe(self):
        path, dry = self.probe("click_stereo")
        wire, effect = self.render_through("ParametricEQ", path, dry.frames)
        result = kit.click(wire, dry, effect.latency_samples)
        self.assertTrue(result["passed"], result["red"])
        self.assertEqual(result["values"]["measured_latency_samples"],
                         [0.0, 0.0])

        # A minimum-phase filter is not a wire at sample zero, and the two
        # readings say different true things about it: the integer onset is
        # 0 samples - the class adds no processing latency, which is what
        # `latency_samples` declares - while the sub-sample read is +1.3
        # samples of group delay. A row must say which one it wants.
        filtered, effect = self.render_through("LowPass", path, dry.frames,
                                               frequency=8000.0)
        integer = kit.click(filtered, dry, effect.latency_samples,
                            subsample=False)
        self.assertTrue(integer["passed"], integer["red"])
        fine = kit.click(filtered, dry, effect.latency_samples)
        self.assertFalse(fine["passed"])
        for value in fine["values"]["measured_latency_samples"]:
            self.assertAlmostEqual(value, 1.333, delta=0.1)

    def test_digest_over_two_renders_of_the_same_settings(self):
        path, _ = self.probe("noise_det")
        one, _ = self.render_through("LowPass", path, 24000,
                                     frequency=2000.0)
        two, _ = self.render_through("LowPass", path, 24000,
                                     frequency=2000.0)
        result = kit.digest({"first": one, "second": two})
        self.assertTrue(result["passed"], result["red"])


class NullBuildTest(unittest.TestCase):
    """The NULL-BUILD RED check (`kit_faults.null_build_red`).

    Pattern revision section 1.2: eleven of Phase 2's forty-five broken
    clauses read green on a build that did nothing, and every one of them
    was written by a session that believed it had already applied the
    workspace's "prove a checker can fail" rule. So it is a kit function
    with a battery, in the shape of every other fault here - the red beside
    a control that must pass, and a demonstration of the check itself going
    off on a deliberately wrong input.
    """

    TONES = ResponseTest.TONES

    def _response(self, cls):
        wet, dry = {}, {}
        for hz in self.TONES:
            probe = probes.sine(hz, 0.3, -12.0)
            wet[hz], _ = render_through(cls, probe, 14400,
                                        probe_name="tones_step",
                                        frequency=1000.0, q=0.707)
            dry[hz] = render_source(probe, 14400, probe_name="tones_step")
        return kit.response(wet, dry, reference_hz=200.0,
                            expected={"corner_hz": (1000.0, 5.0),
                                      "passband_db": (0.0, 0.2)})

    def _level(self, cls):
        probe = probes.sine(1000.0, 0.5, -26.0)
        dry = render_source(probe, 24000, probe_name="sine_1k_-26")
        wet, _ = render_through(cls, probe, 24000, probe_name="sine_1k_-26",
                                frequency=1000.0, q=0.707)
        return kit.level(wet, dry, tolerance_db=0.05)

    def test_response_goes_red_on_the_class_built_as_a_wire(self):
        checked = faults.null_build_red(faults.LowPass, self._response)
        self.assertFalse(checked["null"]["passed"])
        # It is red for the right reason: a wire has no -3 dB crossing at
        # all, so the corner the trait is about does not exist.
        self.assertIn("no -3.0 dB crossing", checked["null"]["red"][0])
        self.assertIsNone(checked["null"]["values"]["corner_hz"])
        # And the control on the real class passes, so the red is the null
        # build's and not the measurement's.
        self.assertTrue(checked["control"]["passed"],
                        checked["control"]["red"])
        self.assertAlmostEqual(checked["control"]["values"]["corner_hz"],
                               1000.0, delta=10.0)

    def test_the_wire_build_really_is_a_wire(self):
        probe = probes.sine(1000.0, 0.2, -12.0)
        dry = render_source(probe, 9600, probe_name="sine_1k_-12")
        wet, _ = render_through(faults.wire_build(faults.LowPass),
                                probe, 9600, probe_name="sine_1k_-12",
                                frequency=1000.0, q=0.707)
        # Byte-identical to the source, which is what "output == source"
        # means and what makes the check above worth anything.
        self.assertEqual(wet.digest, dry.digest)

    def test_the_check_fires_on_a_measurement_that_cannot_fail(self):
        # The deliberately wrong input. LEVEL reads the wet:dry ratio, and a
        # wire's ratio is exactly 0.00 dB - so LEVEL is green on a build
        # that does nothing, and may not stand behind a Tier 2 trait on its
        # own. This is `ParametricEQ` T2's defect in one line.
        with self.assertRaises(faults.NullBuildGreen) as caught:
            faults.null_build_red(faults.LowPass, self._level)
        self.assertIn("built as a wire", str(caught.exception))
        # And the reading that makes it fire, stated as a number.
        self.assertEqual(self._level(faults.wire_build(faults.LowPass))
                         ["values"]["rms_db"], [0.0, 0.0])

    def test_the_check_fires_when_the_control_is_red_too(self):
        # The second wrong input: a measurement that reddens everything.
        # The null build's red says nothing if the real class fails the same
        # bar, which is the "a battery without a control" half of section 6.
        def always_red(cls):
            return {"passed": False, "red": ["a bar nothing can meet"]}

        with self.assertRaises(faults.ControlRed) as caught:
            faults.null_build_red(faults.LowPass, always_red)
        self.assertIn("a red that fires on everything",
                      str(caught.exception).lower())


class FaultReachabilityTest(unittest.TestCase):
    """The FAULT-REACHABILITY check (`kit_faults.fault_reachability`).

    Pattern revision section 1.3: three of Phase 2's planted faults were
    positions of the class's own surface, and one was inert. A fault the
    macro grid can dial is a disconfirmation waiting to be written down.
    """

    def build(self, cls):
        probe = probes.sine(1000.0, 0.2, -20.0)
        return build(cls, probes.ArraySource(probe, rate=RATE), RATE)

    def test_a_fault_no_knob_reaches_passes(self):
        # The control. `lookahead_ms` is a construction option with no macro
        # behind it, so 10 ms of look-ahead is a state the surface cannot
        # dial, and `latency_samples` reads it back.
        checked = faults.fault_reachability(
            audioeffects.NoiseGate, faults.UnderLookaheadNoiseGate,
            lambda effect: effect.latency_samples, self.build)
        self.assertEqual(checked["target"], int(0.010 * RATE))
        self.assertEqual(checked["clean"], 0)
        # Every macro position and every shipped patch was actually walked.
        self.assertEqual(checked["checked"],
                         len(audioeffects.NoiseGate.MACRO_LABELS) * 17
                         + len(audioeffects.NoiseGate.PATCHES))

    def test_the_check_fires_on_a_fault_the_macro_grid_can_dial(self):
        # The deliberately wrong input, and the real one: `CombFilter`'s
        # `NoGlideCombFilter` forces `delay_slew = 0`, and macro 5 `Glide`
        # spans 0...1 with grid position 0 sitting exactly there.
        combfilter = faults.CombFilter
        with self.assertRaises(faults.FaultReachable) as caught:
            faults.fault_reachability(combfilter, 0.0,
                                      lambda effect: effect.macro(5),
                                      self.build)
        self.assertIn("macro 5 'Glide' at grid position 0",
                      str(caught.exception))

    def test_the_check_fires_on_an_inert_fault(self):
        # The second wrong input: a fault that forces a state the clean
        # class is already in. `TrimOffLowPass` sets the trim section's mix
        # to 0, which is where `LowPass` leaves it at Trim 0 dB.
        with self.assertRaises(faults.FaultInert) as caught:
            faults.fault_reachability(
                faults.LowPass, faults.TrimOffLowPass,
                lambda effect: effect._trim.mix, self.build)
        self.assertIn("clean class at its own defaults reads",
                      str(caught.exception))


class _Tail:
    """What `render_effect.render()` wants: an object with `.output`.

    A planted fault lives in a node wrapped around the class's output, and
    the renderer renders effects, not nodes.
    """

    def __init__(self, output):
        self.output = output


if __name__ == "__main__":
    unittest.main()
