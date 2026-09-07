"""`NoiseGate`'s own invariants and its planted faults (Phase 2, Drawmer
DS201).

The dossier is `docs/effects/NoiseGate.md`, its traits frozen 2026-09-07
before the class was written; the evidence pack that cites this file is
`docs/effects/NoiseGate-evidence.md`. Every Tier 2 trait here is a pair: the
clean run that must be green and a planted fault **of the same kind** that
must be red. A measurement with no fault beside it is a tripwire, not a
measurement (`docs/effects-kit-spec.md` section 6).

Three things about the kit that this file works around rather than hides,
each recorded in the evidence pack's "what the kit got wrong":

* **GAINTRACE's own `attack_t10_90_ms` and `release_t63_ms` read the dB
  trace**, which is right for a compressor's few-dB law and wrong for a
  gate's: a fraction of the way from -80 dB to 0 dB is not a fraction of the
  way from a gain of 0.0001 to a gain of 1.0. G5 names a transition of the
  *gain*, so `_linear` converts the exported trace back to gain before
  taking its fractions. The measurement is still GAINTRACE's; only the axis
  is the trait's.
* **`attack_gr_depth_db` is a minimum**, so on a gate - whose gain rises -
  it reports the closed state the attack started from.
* **A fully closed gate over quiet material renders exact silence**, and
  `require_signal` refuses a silent render. The level searches below catch
  `SilentRenderError` and read it as the deepest closure int16 can show,
  which is what it is.
"""

import math
import os
import sys
import unittest
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                             # noqa: E402
import audiodynamics                                         # noqa: E402
import audioeffects                                          # noqa: E402
import kit_probes as probes                                  # noqa: E402
from audioeffects import _component as component             # noqa: E402
from audioeffects.rebuilt import noisegate as noisegate_module  # noqa: E402
from audioeffects.rebuilt.noisegate import NoiseGate         # noqa: E402
from tools import effect_measurements as kit                 # noqa: E402

#: `_component` reads VENDOR off the defining module, and the planted-fault
#: subclasses below are defined here.
VENDOR = "PyDevices"

RATE = 48000
SPAN = NoiseGate._MACRO_RANGES
THRESHOLD, ATTACK, HOLD, RELEASE, RANGE, KEY_LOW, KEY_HIGH, KEY_LISTEN = \
    range(8)


def midi(index, value):
    """A macro's engineering value on the 0-127 grid."""
    return component.macro_of(SPAN[index], value)


def settings(threshold_db=-20.0, attack_ms=1.0, hold_ms=20.0,
             release_ms=10.0, range_db=-80.0, key_low_hz=25.0,
             key_high_hz=35000.0, key_listen=False):
    return [(THRESHOLD, midi(THRESHOLD, threshold_db)),
            (ATTACK, midi(ATTACK, attack_ms)),
            (HOLD, midi(HOLD, hold_ms)),
            (RELEASE, midi(RELEASE, release_ms)),
            (RANGE, midi(RANGE, range_db)),
            (KEY_LOW, midi(KEY_LOW, key_low_hz)),
            (KEY_HIGH, midi(KEY_HIGH, key_high_hz)),
            (KEY_LISTEN, 127 if key_listen else 0)]


# --------------------------------------------------------------------------
# The planted faults. Each is the class with one thing wrong, and each is
# wrong in the way its own trait is about.


class NoHoldGate(NoiseGate):
    """The class forgetting to keep the gate machine on: `hold_ms` at zero
    drops the node back to its memoryless computer, which has no trigger
    state, no hold and an `over * 8.0f` slope instead of a depth
    (`audioif_dynamics.c:452`, `:386-389`). G1, G2 and G4's fault."""

    NAME = 'NoHoldGate'

    def _build(self, **options):
        NoiseGate._build(self, **options)
        self._dyn.set(hold_ms=0.0)

    def _apply_macro(self, index, position):
        NoiseGate._apply_macro(self, index, position)
        self._dyn.set(hold_ms=0.0)


class OpenKeyBand(NoiseGate):
    """The key band never leaving its end stops, so the detector hears the
    whole spectrum whatever the Key Low and Key High knobs say. G3's
    fault."""

    NAME = 'OpenKeyBand'

    def _apply_macro(self, index, position):
        if index in (KEY_LOW, KEY_HIGH):
            position = 0.0 if index == KEY_LOW else 1.0
        NoiseGate._apply_macro(self, index, position)


class HalvedTimes(NoiseGate):
    """Attack and release coefficients computed from half the setting. G5's
    fault: the class sounds the same shape and is twice as fast."""

    NAME = 'HalvedTimes'

    def _apply_macro(self, index, position):
        NoiseGate._apply_macro(self, index, position)
        if index == ATTACK:
            self._dyn.set(attack_ms=component.macro_value(SPAN[ATTACK],
                                                          position) * 0.5)
        elif index == RELEASE:
            self._dyn.set(release_ms=component.macro_value(SPAN[RELEASE],
                                                           position) * 0.5)


class RmsDetector(NoiseGate):
    """An RMS detector where the trait says peak. G6's fault."""

    NAME = 'RmsDetector'

    def _build(self, **options):
        NoiseGate._build(self, **options)
        self._dyn.set(detector="rms", rms_ms=10.0)


class AddingDuck(NoiseGate):
    """The duck's inverter modulated at +32767 instead of -32768, so the
    branch is added rather than subtracted - and 32767/32768 is not a wire
    either. G7's fault."""

    NAME = 'AddingDuck'

    def _build(self, **options):
        options["duck"] = True
        NoiseGate._build(self, **options)
        self._plus = audiocore.RawSample(
            array("h", [32767] * self._channel_count),
            sample_rate=self._sample_rate,
            channel_count=self._channel_count)
        self._invert.modulate(self._plus)


class UnderReportedLatency(NoiseGate):
    """A look-ahead build reporting zero latency, the DSP untouched.
    CLICK's fault."""

    NAME = 'UnderReportedLatency'

    @property
    def latency_samples(self):
        return 0


class UnclearedGate(NoiseGate):
    """A node the class built but left out of the reset walk, so a gate
    left wide open stays wide open across `reset()`. STATE's fault."""

    NAME = 'UnclearedGate'

    def _own(self, node, reset=True, deinit=True):
        if isinstance(node, audiodynamics.Dynamics):
            reset = False
        return NoiseGate._own(self, node, reset=reset, deinit=deinit)


# --------------------------------------------------------------------------
# Rendering helpers


def render(data, frames, macros=(), cls=NoiseGate, rate=RATE, channels=2,
           block=256, **options):
    source = probes.ArraySource(data, rate=rate, channels=channels,
                                block=block)
    effect = cls.create(source, rate, **options)
    for index, value in macros:
        effect.set_macro(index, value)
    out = probes.render(effect.output, frames, rate=rate, channels=channels,
                        block=block, class_name=cls.NAME,
                        latency_samples=effect.latency_samples)
    effect.deinit()
    return out


def dry(data, frames, rate=RATE, channels=2):
    return probes.render(probes.ArraySource(data, rate=rate,
                                            channels=channels),
                         frames, rate=rate, channels=channels,
                         class_name="source")


def joined(*chunks):
    out = array("h")
    for chunk in chunks:
        out.extend(chunk)
    return out


def square(hz, seconds, dbfs, rate=RATE, channels=2):
    amplitude = 10 ** (dbfs / 20.0) * 32767.0
    out = array("h")
    for index in range(int(seconds * rate)):
        value = int(round(amplitude * (
            1.0 if math.sin(2 * math.pi * hz * index / rate) >= 0 else -1.0)))
        for _ in range(channels):
            out.append(value)
    return out


def trace(wet, dry_render, **options):
    return kit.gaintrace(wet, dry_render, **options)


def settled_gr(data, macros, cls=NoiseGate, rate=RATE, **options):
    """The settled gain reduction, with a silent render read as the deepest
    closure 16 bits can carry rather than refused."""
    frames = len(data) // 2
    try:
        result = kit.gaintrace(render(data, frames, macros, cls=cls,
                                      rate=rate, **options),
                               dry(data, frames, rate=rate), hop_ms=5.0)
    except kit.SilentRenderError:
        return -999.0
    return result["values"]["settled_gr_db"]


def _linear(result, from_ms):
    """GAINTRACE's exported trace, back on the gain axis the trait names."""
    return [(t, 10.0 ** (v / 20.0))
            for t, v in zip(result["values"]["trace_ms"],
                            result["values"]["trace_gr_db"])
            if v is not None and t >= from_ms]


def _crossing(points, target):
    for index in range(1, len(points)):
        low, high = points[index - 1][1], points[index][1]
        if (low - target) * (high - target) <= 0 and low != high:
            weight = (target - low) / (high - low)
            return (points[index - 1][0]
                    + weight * (points[index][0] - points[index - 1][0]))
    return None


def rise_10_90_ms(result, from_ms):
    points = _linear(result, from_ms)
    start = points[0][1]
    end = max(gain for _, gain in points)
    span = end - start
    first = _crossing(points, start + 0.1 * span)
    last = _crossing(points, start + 0.9 * span)
    return None if None in (first, last) else last - first


def fall_t63_ms(result, from_ms):
    points = _linear(result, from_ms)
    start = points[0][1]
    end = min(gain for _, gain in points)
    reached = _crossing(points, start + 0.63 * (end - start))
    return None if reached is None else reached - points[0][0]


def open_hold_ms(result, drop_ms, bar_db=-0.5):
    """How long the gain stays within `bar_db` of full open after the key
    falls, read off GAINTRACE's own trace."""
    began = None
    for when, value in zip(result["values"]["trace_ms"],
                           result["values"]["trace_gr_db"]):
        if value is None:
            continue
        if when >= drop_ms and began is None and value > bar_db:
            began = when
        if began is not None and when > began and value <= bar_db:
            return when - drop_ms
    return None


def opening_level_db(hz, macros, cls=NoiseGate, low=-70.0, high=0.0,
                     steps=12, seconds=0.2):
    """The input level at which the gate first opens, bisected."""
    for _ in range(steps):
        middle = (low + high) / 2.0
        if settled_gr(probes.sine(hz, seconds, middle), macros,
                      cls=cls) > -40.0:
            high = middle
        else:
            low = middle
    return (low + high) / 2.0


def opening_threshold_db(data, cls=NoiseGate, low=-80.0, high=0.0, steps=14):
    """The Threshold setting at which this material first opens the gate."""
    for _ in range(steps):
        middle = (low + high) / 2.0
        if settled_gr(data, settings(threshold_db=middle),
                      cls=cls) > -40.0:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


# --------------------------------------------------------------------------


class TheRegistryServesIt(unittest.TestCase):
    def test_the_package_exports_the_rebuilt_class(self):
        self.assertIs(audioeffects.NoiseGate, NoiseGate)
        self.assertIn("NoiseGate", audioeffects.ALL)
        source = probes.ArraySource(probes.sine(1000.0, 0.05, -6.0),
                                    rate=RATE)
        effect = audioeffects.create("NoiseGate", source, RATE)
        self.assertIsInstance(effect, NoiseGate)
        effect.deinit()

    def test_the_old_class_is_untouched_beneath(self):
        from audioeffects import dynamics
        self.assertIsNot(dynamics.NoiseGate, NoiseGate)
        self.assertEqual(dynamics.NoiseGate.MACRO_LABELS, ())


class Tier1Invariants(unittest.TestCase):
    """The standard block from the dossier's section 3, in process, at
    48 kHz. The evidence pack carries the same rows at 44.1 and 22.05 kHz
    and on the other two interpreters."""

    def test_range_zero_is_a_wire(self):
        # A gate has no mix knob; its wire setting is Range at 0 dB, which
        # `depth_db = 0.0` makes an exact unity floor (`:387-388`). The
        # threshold is at the top so the gate stays shut, which is the
        # state that floor is written in; the next test measures what the
        # first opening costs.
        data = probes.ramp_fs(8192)
        wet = render(data, 8192, settings(range_db=0.0, threshold_db=0.0))
        result = kit.wire(wet, dry(data, 8192), latency_samples=0)
        self.assertEqual(result["red"], [], result["values"])
        self.assertEqual(result["values"]["differing_samples"], 0)

    def test_the_first_opening_ramps_from_the_nodes_cold_zero(self):
        """A measured Tier 1 qualification, committed rather than described.

        `state_init` and `clear_extras` set the machine's gain to 0.0
        (`audioif_dynamics.c:265`), and only the CLOSED branch ever writes
        `floor_gain` (`:719-722`). So the *first* opening after
        construction or a reset ramps from silence rather than from the
        Range floor, and at Range 0 dB - where the class should be a wire -
        that costs one attack's worth of fade-in. Measured here at 6.9 ms
        for patch 0's 1.0 ms attack, which is the 6.8 time constants the
        machine's 0.999 snap needs; byte-identical from 10 ms on. The class
        cannot reach that state through any API the node offers.
        """
        import numpy as np
        data = probes.ramp_fs(8192)
        wet = render(data, 8192, [(RANGE, 0)])
        reference = dry(data, 8192)
        difference = np.abs(wet.data.astype(np.int32)
                            - reference.data.astype(np.int32))
        differing = np.nonzero(difference.any(axis=1))[0]
        self.assertEqual(int(differing[0]), 0)
        self.assertLess(1000.0 * len(differing) / RATE, 8.0)
        after = int(0.010 * RATE)
        self.assertEqual(int(np.count_nonzero(difference[after:])), 0)

    def test_planted_fault_a_wire_that_is_one_lsb_light(self):
        import kit_faults as faults
        data = probes.ramp_fs(8192)
        source = probes.ArraySource(data, rate=RATE)
        effect = NoiseGate.create(source, RATE)
        for index, value in settings(range_db=0.0, threshold_db=0.0):
            effect.set_macro(index, value)
        wet = probes.render(faults.OneLsbScale(effect.output), 8192,
                            rate=RATE, class_name="NoiseGate+1lsb")
        effect.deinit()
        result = kit.wire(wet, dry(data, 8192))
        self.assertNotEqual(result["red"], [])

    def test_silence_in_silence_out_and_the_tail_reaches_zero(self):
        data = joined(probes.sine(1000.0, 0.2, -6.0),
                      probes.silence(int(0.8 * RATE)))
        frames = len(data) // 2
        wet = render(data, frames, settings(release_ms=50.0))
        result = kit.tail(wet, burst_end_frame=int(0.25 * RATE),
                          declared_tail_samples=0)
        self.assertEqual(result["values"]["residual_lsb"], 0)
        self.assertEqual(result["red"], [], result["values"])

    def test_planted_fault_a_tail_that_never_returns_to_zero(self):
        import kit_faults as faults
        data = joined(probes.sine(1000.0, 0.2, -6.0),
                      probes.silence(int(0.8 * RATE)))
        frames = len(data) // 2
        source = probes.ArraySource(data, rate=RATE)
        effect = NoiseGate.create(source, RATE)
        wet = probes.render(faults.StuckDc(effect.output), frames, rate=RATE,
                            class_name="NoiseGate+dc")
        effect.deinit()
        result = kit.tail(wet, burst_end_frame=int(0.25 * RATE),
                          declared_tail_samples=0)
        self.assertNotEqual(result["red"], [])

    def test_the_open_gate_is_level_honest(self):
        data = probes.sine(1000.0, 0.4, -14.0)
        frames = len(data) // 2
        wet = render(data, frames, settings(threshold_db=-80.0))
        result = kit.level(wet, dry(data, frames), skip_frames=2048)
        self.assertEqual(result["red"], [], result["values"])

    def test_reported_latency_is_zero_and_measured_zero(self):
        data = probes.click_stereo(8192, offset=1024)
        wet = render(data, 8192, settings(threshold_db=-80.0))
        result = kit.click(wet, dry(data, 8192), 0, subsample=False)
        self.assertEqual(result["red"], [], result["values"])

    def test_a_lookahead_build_reports_the_latency_it_has(self):
        data = probes.click_stereo(8192, offset=1024)
        wet = render(data, 8192, settings(threshold_db=-80.0),
                     lookahead_ms=1.0)
        result = kit.click(wet, dry(data, 8192), 48, subsample=False)
        self.assertEqual(result["red"], [], result["values"])
        self.assertEqual(result["values"]["measured_latency_samples"],
                         [48.0, 48.0])

    def test_planted_fault_a_lookahead_build_reporting_zero(self):
        data = probes.click_stereo(8192, offset=1024)
        wet = render(data, 8192, settings(threshold_db=-80.0),
                     cls=UnderReportedLatency, lookahead_ms=1.0)
        result = kit.click(wet, dry(data, 8192), 0, subsample=False)
        self.assertNotEqual(result["red"], [])

    def _state(self, cls=NoiseGate):
        data = joined(probes.silence(2048), probes.sine(1000.0, 0.3, -6.0))
        holder = probes.SwitchableSource(probes.ArraySource(data, rate=RATE))
        effect = cls.create(holder, RATE)
        for index, value in settings(release_ms=2000.0, hold_ms=2000.0):
            effect.set_macro(index, value)

        def pull(blocks):
            return probes.render(effect.output, blocks * 256, rate=RATE,
                                 class_name=cls.NAME)

        capabilities = effect.capabilities
        return capabilities, kit.state(
            effect, pull=pull, swap=holder.swap,
            probe_source=probes.ArraySource(data, rate=RATE),
            silent_source=probes.ArraySource(probes.silence(48000),
                                             rate=RATE),
            blocks=48,
            nodes=[("node[%d]" % index, node)
                   for index, node in enumerate(effect._nodes)])

    def test_reset_deinit_capabilities_and_no_allocation(self):
        capabilities, result = self._state()
        self.assertEqual(capabilities, ())
        self.assertEqual(result["red"], [], result["values"])

    def _after_reset(self, cls=NoiseGate, loud_dbfs=-20.0,
                     threshold_db=-30.0):
        """The gate's own reset check, because STATE's cannot see it.

        The kit's step 3 is `reset()` plus a *silent* source, and a gate
        holds no audio: a machine left wide open renders silence out of
        silence just as a cleared one does. What survives a missed reset is
        the **stage** - a gate left in HOLD passes the next material at
        unity for the rest of its hold - so the probe here is quiet
        material, not silence, and the readout is the first block after the
        reset.

        The loud pass is at -20 dBFS rather than full scale for a reason
        the next test measures: `audioif_dynamics_reset` keeps the
        side-chain filter memory on purpose (`audioif_dynamics.c:281-288`),
        and after a full-scale pass that stale state alone is loud enough
        to reopen the gate - which would mask the fault instead of
        exposing it.
        """
        loud = probes.sine(1000.0, 0.2, loud_dbfs)
        quiet = probes.sine(1000.0, 0.2, -60.0)
        holder = probes.SwitchableSource(probes.ArraySource(loud, rate=RATE))
        effect = cls.create(holder, RATE)
        for index, value in settings(threshold_db=threshold_db,
                                     hold_ms=2000.0, release_ms=2000.0,
                                     range_db=-80.0):
            effect.set_macro(index, value)
        probes.render(effect.output, 9600, rate=RATE, class_name=cls.NAME)
        effect.reset()
        holder.swap(probes.ArraySource(quiet, rate=RATE))
        rendered = probes.render(effect.output, 2048, rate=RATE,
                                 class_name=cls.NAME)
        effect.deinit()
        return int(abs(rendered.data).max())

    def test_reset_returns_the_gate_machine_to_closed(self):
        # Patch 0's Range is -80 dB, so a -60 dBFS tone through a closed
        # gate is well below one LSB: exact zero is the correct reading.
        self.assertEqual(self._after_reset(), 0)

    def test_planted_fault_a_gate_left_open_across_reset(self):
        # The node kept out of the reset walk. The kit's own STATE stays
        # green on this class either way, which is why this test exists.
        self.assertGreater(self._after_reset(cls=UnclearedGate), 16)
        _, result = self._state(cls=UnclearedGate)
        self.assertEqual(result["red"], [], "STATE is structurally blind to "
                         "a memoryless class's reset; see this class's own "
                         "reset test")

    def test_reset_does_not_clear_the_key_filters_and_the_node_says_so(self):
        """A measured Tier 1 miss, committed rather than described.

        `audioif_dynamics_reset` keeps the side-chain filter memory on
        purpose (`audioif_dynamics.c:281-288`), and the class has no way to
        clear it: the state is private to the node and nothing in the
        keyword table reaches it. So after a loud pass the detector reads a
        stale high-pass state as signal for a few milliseconds and opens
        the gate on material that should leave it shut - here, a -60 dBFS
        tone under a -39.7 dB threshold, on a class whose reset walk did
        everything it could. Committed so the number is in the record; if
        audioif ever clears those filters this test goes red on purpose,
        and the evidence pack's Tier 1 reset row is what should then
        change.
        """
        self.assertGreater(self._after_reset(loud_dbfs=-6.0), 16)

    def test_a_duck_build_still_renders_after_reset(self):
        """Upstream CircuitPython's `Mixer.reset_buffer` stops its voices
        (`audioif/src/audiomixer/MixerVoice.c:91`), so a duck build reset
        through the plain walk goes silent on `circuitpython-effects` and
        nowhere else. The class hands the voices back; this holds it to
        that on every interpreter, this one included."""
        data = probes.sine(1000.0, 0.2, -6.0)
        holder = probes.SwitchableSource(probes.ArraySource(data, rate=RATE))
        effect = NoiseGate.create(holder, RATE, duck=True)
        for index, value in settings(threshold_db=-40.0, range_db=-20.0):
            effect.set_macro(index, value)
        first = probes.render(effect.output, 2048, rate=RATE,
                              class_name="NoiseGate")
        effect.reset()
        holder.swap(probes.ArraySource(data, rate=RATE))
        for index, value in settings(threshold_db=-40.0, range_db=-20.0):
            effect.set_macro(index, value)
        second = probes.render(effect.output, 2048, rate=RATE,
                               class_name="NoiseGate")
        effect.deinit()
        self.assertGreater(int(abs(first.data).max()), 1000)
        self.assertGreater(int(abs(second.data).max()), 1000)

    def test_every_node_the_class_built_is_walked(self):
        source = probes.ArraySource(probes.sine(1000.0, 0.1, -6.0),
                                    rate=RATE)
        effect = NoiseGate.create(source, RATE, duck=True)
        nodes = list(effect._nodes)
        self.assertEqual(len(nodes), 7)
        self.assertNotIn(source, nodes)
        effect.deinit()
        for node in nodes:
            if not hasattr(node, "deinit"):
                continue
            with self.assertRaises(RuntimeError):
                audiocore.get_buffer(node)
        effect.deinit()          # idempotent

    def test_mono_gets_the_same_gate_as_stereo(self):
        # The detector is channel-linked, so one gain lands on every
        # channel and a mono source is processed identically.
        data = probes.sine(1000.0, 0.3, -6.0, channels=1)
        frames = len(data)
        wet = render(data, frames, settings(threshold_db=0.0,
                                            range_db=-40.0), channels=1)
        result = kit.gaintrace(wet, dry(data, frames, channels=1),
                               hop_ms=5.0)
        self.assertAlmostEqual(result["values"]["settled_gr_db"], -40.0,
                               delta=0.5)

    def test_hz_spans_clamp_below_nyquist_rather_than_refusing(self):
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                data = probes.sine(1000.0, 0.05, -6.0, rate=rate)
                source = probes.ArraySource(data, rate=rate)
                effect = NoiseGate.create(source, rate)
                effect.set_macro(KEY_HIGH, 127)     # asks for 35 kHz
                ceiling = rate * 0.5 * component.NYQUIST_MARGIN
                self.assertLessEqual(effect._hz(35000.0), ceiling)
                _, data_out = audiocore.get_buffer(effect.output)
                self.assertTrue(len(bytes(data_out)) > 0)
                effect.deinit()

    def test_the_hold_floor_keeps_the_gate_machine_on_at_every_rate(self):
        # 2 ms is 96 frames at 48 kHz and 44 at 22.05 kHz; the node turns
        # the four-stage machine off when the frame count rounds to zero.
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                frames = int(noisegate_module.MINIMUM_HOLD_MS * rate / 1000.0)
                self.assertGreater(frames, 0)


class Tier2Traits(unittest.TestCase):
    """G1-G7, each with the planted fault its own trait names."""

    def test_g1_the_envelope_is_one_shot(self):
        # A 1 ms full-scale burst, then a tone 40 dB under the threshold
        # that the gate would never open for: what comes through afterwards
        # is the committed attack and nothing else.
        data = joined(probes.silence(int(0.02 * RATE)),
                      probes.sine(1000.0, 0.001, -0.5),
                      probes.sine(1000.0, 1.6, -60.0))
        frames = len(data) // 2
        options = settings(threshold_db=-20.0, attack_ms=200.0,
                           hold_ms=100.0, release_ms=500.0)
        result = kit.gaintrace(render(data, frames, options),
                               dry(data, frames), hop_ms=1.0)
        reached = max(v for v in result["values"]["trace_gr_db"]
                      if v is not None)
        self.assertGreater(reached, -0.5)

        faulted = kit.gaintrace(render(data, frames, options,
                                       cls=NoHoldGate),
                                dry(data, frames), hop_ms=1.0)
        self.assertLess(max(v for v in faulted["values"]["trace_gr_db"]
                            if v is not None), -50.0)

    def test_g2_hold_is_a_real_stage(self):
        data = joined(probes.sine(1000.0, 0.3, -6.0),
                      probes.sine(1000.0, 2.0, -60.0))
        frames = len(data) // 2
        for hold in (20.0, 100.0, 500.0, 1000.0):
            with self.subTest(hold=hold):
                options = settings(hold_ms=hold, release_ms=2.0)
                result = kit.gaintrace(render(data, frames, options),
                                       dry(data, frames), hop_ms=0.5,
                                       release_from_ms=300.0)
                held = open_hold_ms(result, 300.0)
                self.assertIsNotNone(held)
                self.assertLess(abs(held - hold), 0.10 * hold)
        faulted = kit.gaintrace(
            render(data, frames, settings(hold_ms=1000.0, release_ms=2.0),
                   cls=NoHoldGate),
            dry(data, frames), hop_ms=0.5, release_from_ms=300.0)
        held = open_hold_ms(faulted, 300.0)
        self.assertTrue(held is None or held < 100.0)

    def test_g3_the_key_path_is_a_band(self):
        options = settings(threshold_db=-40.0, key_low_hz=500.0,
                           key_high_hz=2000.0)
        centre = opening_level_db(1000.0, options)
        for hz in (250.0, 4000.0):
            with self.subTest(hz=hz):
                shift = opening_level_db(hz, options) - centre
                self.assertGreater(shift, 4.0)
        faulted_centre = opening_level_db(1000.0, options, cls=OpenKeyBand)
        for hz in (250.0, 4000.0):
            with self.subTest(hz=hz, fault=True):
                shift = (opening_level_db(hz, options, cls=OpenKeyBand)
                         - faulted_centre)
                self.assertLess(shift, 1.0)

    def test_g3_key_listen_puts_the_band_on_the_output(self):
        data = probes.sine(220.0, 0.2, -6.0)
        frames = len(data) // 2
        heard = render(data, frames, settings(threshold_db=-60.0,
                                              key_low_hz=4000.0,
                                              key_listen=True))
        ordinary = render(data, frames, settings(threshold_db=-60.0,
                                                 key_low_hz=4000.0))
        self.assertLess(int(abs(heard.data).max()),
                        int(abs(ordinary.data).max()) // 10)

    def test_g4_the_closed_state_is_range_not_zero(self):
        data = probes.sine(1000.0, 0.6, -6.0)
        for range_db in (0.0, -20.0, -40.0, -60.0):
            with self.subTest(range_db=range_db):
                got = settled_gr(data, settings(threshold_db=0.0,
                                                range_db=range_db))
                self.assertAlmostEqual(got, range_db, delta=0.5)

    def test_g4_the_law_is_a_depth_not_a_slope(self):
        options = settings(threshold_db=0.0, range_db=-20.0)
        first = settled_gr(probes.sine(1000.0, 0.6, -20.0), options)
        second = settled_gr(probes.sine(1000.0, 0.6, -30.0), options)
        self.assertLess(abs(first - second), 0.5)

    def test_planted_fault_g4_the_memoryless_slope(self):
        # Two dB under the threshold, where the memoryless computer's
        # `over * 8.0f` has not yet reached its clamp: a depth reads -40,
        # a slope reads about -16.
        options = settings(threshold_db=-4.0, range_db=-40.0)
        clean = settled_gr(probes.sine(1000.0, 0.6, -6.0), options)
        self.assertAlmostEqual(clean, -40.0, delta=0.5)
        got = settled_gr(probes.sine(1000.0, 0.6, -6.0), options,
                         cls=NoHoldGate)
        self.assertGreater(abs(got - (-40.0)), 5.0)

    def test_g5_attack_and_decay_time_constants(self):
        for attack in (1.0, 10.0, 100.0):
            with self.subTest(attack=attack):
                data = joined(probes.silence(int(0.05 * RATE)),
                              probes.sine(1000.0, 6.0, -6.0))
                frames = len(data) // 2
                result = kit.gaintrace(
                    render(data, frames, settings(attack_ms=attack,
                                                  hold_ms=2.0)),
                    dry(data, frames), hop_ms=max(0.05, attack / 200.0),
                    attack_from_ms=50.0)
                got = rise_10_90_ms(result, 50.0)
                self.assertLess(abs(got - 2.197 * attack),
                                0.15 * 2.197 * attack)
        for release in (10.0, 100.0, 1000.0):
            with self.subTest(release=release):
                data = joined(probes.sine(1000.0, 0.3, -6.0),
                              probes.sine(1000.0, max(2.0, release / 250.0),
                                          -60.0))
                frames = len(data) // 2
                result = kit.gaintrace(
                    render(data, frames, settings(hold_ms=2.0,
                                                  release_ms=release)),
                    dry(data, frames), hop_ms=max(0.2, release / 400.0),
                    release_from_ms=303.0)
                got = fall_t63_ms(result, 303.0)
                self.assertLess(abs(got - release), 0.15 * release)

    def test_planted_fault_g5_coefficients_from_half_the_setting(self):
        data = joined(probes.silence(int(0.05 * RATE)),
                      probes.sine(1000.0, 6.0, -6.0))
        frames = len(data) // 2
        result = kit.gaintrace(
            render(data, frames, settings(attack_ms=100.0, hold_ms=2.0),
                   cls=HalvedTimes),
            dry(data, frames), hop_ms=0.5, attack_from_ms=50.0)
        got = rise_10_90_ms(result, 50.0)
        self.assertGreater(abs(got - 2.197 * 100.0), 0.15 * 2.197 * 100.0)

    def test_g5_the_fastest_attack_opens_inside_a_fifth_of_a_millisecond(
            self):
        data = joined(probes.silence(512), probes.sine(1000.0, 0.05, -6.0))
        frames = len(data) // 2
        wet = render(data, frames, settings(threshold_db=-40.0,
                                            attack_ms=0.01))
        reference = dry(data, frames)
        opened = None
        for frame in range(512, frames):
            if all(wet.data[frame][channel] == reference.data[frame][channel]
                   for channel in range(2)) and reference.data[frame].any():
                opened = frame
                break
        self.assertIsNotNone(opened)
        self.assertLess(1000.0 * (opened - 512) / RATE, 0.2)

    def test_g6_the_detector_is_peak_not_rms(self):
        # The equal-RMS pair is the clause that separates the two
        # detectors: a square and a sine of equal RMS reach different
        # peaks, and only a peak detector cares.
        sine = probes.sine(1000.0, 0.2, -14.0)
        equal_rms_square = square(1000.0, 0.2, -14.0 - 3.0103)
        spread = (opening_threshold_db(equal_rms_square)
                  - opening_threshold_db(sine))
        self.assertLess(spread, -2.0)

        faulted = (opening_threshold_db(equal_rms_square, cls=RmsDetector)
                   - opening_threshold_db(sine, cls=RmsDetector))
        self.assertGreater(faulted, -1.0)

    def test_g6_equal_peak_material_is_disconfirmed_and_stays_measured(self):
        # Recorded as a *disconfirmation*, not skipped: the trait asks for
        # 0.5 dB and the class as built gives about 0.63, because its key
        # high-pass is always in circuit and overshoots a square's edges.
        # The bare node, with no key filters, opens both at exactly the
        # same threshold - which is what says the cause is the band and not
        # the detector.
        sine = probes.sine(1000.0, 0.2, -14.0)
        equal_peak_square = square(1000.0, 0.2, -14.0)
        spread = (opening_threshold_db(equal_peak_square)
                  - opening_threshold_db(sine))
        self.assertGreater(spread, 0.5)
        self.assertLess(spread, 1.0)
        self.assertAlmostEqual(self._bare_node_opens(equal_peak_square),
                               self._bare_node_opens(sine), delta=0.05)

    def _bare_node_opens(self, data, low=-30.0, high=0.0, steps=16):
        for _ in range(steps):
            middle = (low + high) / 2.0
            node = audiodynamics.Dynamics(
                audiodynamics.DYN_GATE, threshold_db=middle, attack_ms=1.0,
                release_ms=10.0, hold_ms=20.0, depth_db=-80.0,
                sample_rate=RATE, channel_count=2)
            node.play(probes.ArraySource(data, rate=RATE))
            out = probes.render(node, len(data) // 2, rate=RATE,
                                class_name="Dynamics")
            if int(abs(out.data).max()) > 100:
                low = middle
            else:
                high = middle
        return (low + high) / 2.0

    def test_g7_duck_inverts_the_sense(self):
        loud = probes.sine(1000.0, 0.6, -6.0)
        for range_db in (0.0, -6.0, -20.0, -40.0):
            with self.subTest(range_db=range_db):
                got = settled_gr(loud, settings(threshold_db=-40.0,
                                                range_db=range_db),
                                 duck=True)
                self.assertAlmostEqual(got, range_db, delta=0.5)
        frames = len(loud) // 2
        below = kit.level(render(loud, frames,
                                 settings(threshold_db=0.0, range_db=-20.0),
                                 duck=True),
                          dry(loud, frames), skip_frames=4096)
        self.assertEqual(below["red"], [], below["values"])

    def test_planted_fault_g7_a_duck_that_adds(self):
        loud = probes.sine(1000.0, 0.6, -6.0)
        got = settled_gr(loud, settings(threshold_db=-40.0, range_db=-20.0),
                         cls=AddingDuck)
        self.assertGreater(got, 0.0)

    def test_g7_the_duck_runs_on_the_same_hold(self):
        data = joined(probes.sine(1000.0, 0.3, -6.0),
                      probes.sine(1000.0, 2.0, -60.0))
        frames = len(data) // 2
        for hold in (100.0, 500.0):
            with self.subTest(hold=hold):
                result = kit.gaintrace(
                    render(data, frames, settings(hold_ms=hold,
                                                  release_ms=2.0,
                                                  range_db=-20.0),
                           duck=True),
                    dry(data, frames), hop_ms=0.5, release_from_ms=300.0)
                ducked = None
                began = None
                for when, value in zip(result["values"]["trace_ms"],
                                       result["values"]["trace_gr_db"]):
                    if value is None:
                        continue
                    if when >= 300.0 and began is None and value < -0.5:
                        began = when
                    if began is not None and when > began and value >= -0.5:
                        ducked = when - 300.0
                        break
                self.assertIsNotNone(ducked)
                self.assertLess(abs(ducked - hold), 0.10 * hold)


if __name__ == "__main__":
    unittest.main()
