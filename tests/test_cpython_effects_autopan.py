"""`AutoPan`'s invariant and planted-fault tests (effects Phase 3).

Traits
frozen 2026-09-08 before the class. Exhaustive rate coverage lives in the
evidence pack; this file asserts at 48 kHz unless the test is about rate.
"""

import math
import os
import re
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                                # noqa: E402
from audioeffects import autopan                                # noqa: E402
import kit_faults as faults                                     # noqa: E402
import kit_probes as probes                                     # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

AutoPan = autopan.AutoPan

RATE = 48000
RATE_I, DEPTH_I, SHAPE_I, LAW_I, CENTRE_I, PHASE_I, SYNC_I = range(7)


def build(cls=None, rate=RATE, channels=2, frames=2048, probe=None,
          **options):
    cls = cls or AutoPan
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256, channels=channels)
    return cls.create(source, rate, **options)


def render_through(data, sample_rate=RATE, channels=2, cls=None, frames=None,
                   **options):
    """`rate` in `options` is AutoPan's LFO Hz. Sample rate is `sample_rate`."""
    cls = cls or AutoPan
    frames = frames or (len(data) // channels)
    source = probes.ArraySource(data, rate=sample_rate, channels=channels,
                                block=256)
    effect = cls.create(source, sample_rate, **options)
    try:
        reported = effect.latency_samples
        wet = probes.render(effect.output, frames, rate=sample_rate,
                            channels=channels, block=256,
                            class_name="AutoPan",
                            latency_samples=reported)
    finally:
        effect.deinit()
    dry = kit.Render(bytes(array("h", data[:frames * channels])), sample_rate,
                     channels, block=256, interpreter="cpython")
    return wet, dry, reported


def sine(hz, seconds, dbfs=0.0, rate=RATE, channels=2):
    return probes.sine(hz, seconds, dbfs, rate=rate, channels=channels)


def env_metrics(wet, rate):
    left, _win = kit.envelope(wet.float[:, 0], rate, hop_ms=1.0)
    right, _ = kit.envelope(wet.float[:, 1], rate, hop_ms=1.0)
    power = left * left + right * right
    power_db = 10.0 * np.log10(np.maximum(power, 1e-30))
    left_peak = float(left.max())
    right_peak = float(right.max())
    nearest = int(np.argmin(np.abs(left - right)))
    def att(value, peak):
        return -20.0 * math.log10(max(value, 1e-30) / max(peak, 1e-30))
    mono = 0.5 * (left + right)
    mono_db = 20.0 * np.log10(np.maximum(mono, 1e-30))
    return {
        "power_ripple_db": float(power_db.max() - power_db.min()),
        "centre_att_l_db": att(float(left[nearest]), left_peak),
        "centre_att_r_db": att(float(right[nearest]), right_peak),
        "mono_ripple_db": float(mono_db.max() - mono_db.min()),
        "mono_max_at_centre": abs(int(np.argmax(mono)) - nearest) <= 2,
        "far_min": int(min(wet.data[:, 0].min(), wet.data[:, 1].min())),
    }


def a1_reading(cls=None, seconds=0.8, rate_hz=5.0, **options):
    options.setdefault("rate", rate_hz)
    options.setdefault("depth", 1.0)
    data = sine(1000.0, seconds, 0.0)
    wet, _dry, _ = render_through(data, cls=cls, **options)
    m = env_metrics(wet, RATE)
    red = []
    if m["power_ripple_db"] > 0.2:
        red.append("power ripple %.3f dB" % m["power_ripple_db"])
    for name in ("centre_att_l_db", "centre_att_r_db"):
        if abs(m[name] - 3.01) > 0.1:
            red.append("%s %.3f dB" % (name, m[name]))
    return {"passed": not red, "red": red, "values": m}


def a4_reading(cls=None, seconds=0.8, rate_hz=5.0, law_db=None, **options):
    options.setdefault("rate", rate_hz)
    options.setdefault("depth", 1.0)
    if law_db is not None:
        options["law_db"] = law_db
    data = sine(1000.0, seconds, 0.0)
    wet, _dry, _ = render_through(data, cls=cls, **options)
    m = env_metrics(wet, RATE)
    target = 3.01 if law_db is None else 0.0
    red = []
    if abs(m["mono_ripple_db"] - target) > 0.2:
        red.append("mono ripple %.3f dB against %.2f" % (m["mono_ripple_db"],
                                                         target))
    if law_db is None and not m["mono_max_at_centre"]:
        red.append("constant-power mono max not at the centre")
    return {"passed": not red, "red": red, "values": m}


def a3_reading(cls=None, rate_hz=5.0, seconds=1.0, **options):
    if "patch" not in options:
        options.setdefault("rate", rate_hz)
        options.setdefault("depth", 1.0)
    data = sine(1000.0, seconds, -6.0)
    wet, _dry, _ = render_through(data, cls=cls, **options)
    start = wet.frames // 4
    x = wet.float[start:, 0]
    mags, bin_hz, _name, _n = kit.magnitude_spectrum(x, RATE, window="hann")
    fund = 1000.0
    block = RATE / 256.0
    tone = float(mags[max(0, int(round(fund / bin_hz)) - 2):
                      int(round(fund / bin_hz)) + 3].max())
    worst = -240.0
    for harmonic in (1, 2):
        for sign in (-1, 1):
            centre = fund + sign * harmonic * block
            lo = max(0, int((centre - 30.0) / bin_hz))
            hi = min(len(mags), int((centre + 30.0) / bin_hz) + 1)
            level = kit.db(float(mags[lo:hi].max()) / max(tone, 1e-30))
            worst = max(worst, level)
    red = []
    if worst > -80.0:
        red.append("block product %.1f dB re tone" % worst)
    return {"passed": not red, "red": red, "values": {"worst_db": worst}}


def a6_depth1_reading(cls=None, rate_hz=5.0, seconds=0.8, **options):
    if "patch" not in options:
        options.setdefault("rate", rate_hz)
        options.setdefault("depth", 1.0)
    data = sine(1000.0, seconds, 0.0)
    wet, _dry, _ = render_through(data, cls=cls, **options)
    left, _ = kit.envelope(wet.float[:, 0], RATE, hop_ms=1.0)
    right, _ = kit.envelope(wet.float[:, 1], RATE, hop_ms=1.0)
    far_lsb = float(min(left.min(), right.min())) * 32767.0
    red = []
    if far_lsb > 0.5:
        red.append("far-channel envelope min %.2f LSB" % far_lsb)
    return {"passed": not red, "red": red, "values": {"far_lsb": far_lsb}}


class MixerLaw(AutoPan):
    """A1/A4: the Mixer's far-channel-only law (A1/P2)."""

    NAME = 'AutoPan'
    FAULT = "mixer"


class HalfExponent(AutoPan):
    """A2: pan-law exponent 0.5, below every Law-macro position."""

    NAME = 'AutoPan'
    FORCED_EXPONENT = 0.5


class BlockHeld(AutoPan):
    """A3: gain held across each 256-frame block."""

    NAME = 'AutoPan'
    HOLD = 256


class MonoStillPans(AutoPan):
    """A5: Multiply still applied on a mono source."""

    NAME = 'AutoPan'

    def _build(self, rate=2.0, depth=1.0, shape=1.0, law_db=None,
               centre=0.0, phase=0.0, sync=0.0, patch=None):
        import audiomath
        if law_db is None:
            law_db = type(self).LAW_POWER_DB
        self._table = None
        self._q15 = None
        node = audiomath.Multiply(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, mix=1.0)
        node.play(self._source)

        def _release():
            stop = getattr(node, "deinit", None)
            if stop is not None:
                stop()
            table = self._table
            self._table = None
            if table is not None:
                closer = getattr(table, "deinit", None)
                if closer is not None:
                    closer()

        self._node = self._own(node, deinit=_release)
        self._output = node
        self._init_macros((rate, depth, shape, law_db, centre, phase, sync),
                          patch)

    def _rebuild_table(self):
        if self._channel_count != 1:
            AutoPan._rebuild_table(self)
            return
        if self._macros[DEPTH_I] <= 0.0:
            self._node.set(mix=0.0)
            return
        self._node.set(mix=1.0)
        values = array("h", [16384] * 256)
        sample = audiocore.RawSample(
            values, sample_rate=self._sample_rate, channel_count=1)
        previous = self._table
        self._table = sample
        self._node.modulate(sample)
        if previous is not None:
            closer = getattr(previous, "deinit", None)
            if closer is not None:
                closer()


class ShallowHardOver(AutoPan):
    """A6: Depth 1 never quite reaches ±1, the old LFO's defect.

    NEVER_ZERO replaces every exact-zero Q15 with 1 LSB so Centre at the
    rails cannot restore a far-channel mute. DEPTH_CAP alone was green on
    a snapped Centre of 0.008 (the clamp still wrote 0).
    """

    NAME = 'AutoPan'
    DEPTH_CAP = 0.999
    NEVER_ZERO = True
    NEVER_ZERO_LSB = 16


class ShortLatency(AutoPan):
    """CLICK: report 256 samples of latency the DSP does not have."""

    NAME = 'AutoPan'
    LATENCY_SAMPLES = 256


class SwappedSides(AutoPan):
    """The pre-10.3.0 note pairing: each gain table on the other column.

    CircuitPython 10.3.0 reversed synthio's panning sign, so the pairing the
    class shipped with put the left table on the right. Every sweep test is
    symmetric and stayed green through it; only Centre shows which side is
    which."""

    NAME = 'AutoPan'

    def _modulate_synth(self, rate_hz, wave_l, wave_r):
        AutoPan._modulate_synth(self, rate_hz, wave_r, wave_l)


def side_reading(cls=None, centre=-0.8):
    """Output RMS per channel after the first block, at a Centre offset."""
    data = sine(1000.0, 0.5, -6.0)
    source = probes.ArraySource(data, rate=RATE, channels=2, block=256)
    effect = (cls or AutoPan).create(source, RATE, rate=2.0, depth=0.1,
                                     centre=centre)
    try:
        wet = probes.render(effect.output, 16000, rate=RATE, channels=2,
                            block=256, class_name="AutoPan")
    finally:
        effect.deinit()
    rms = np.sqrt((wet.float[2048:] ** 2).mean(axis=0))
    return float(rms[0]), float(rms[1])


def _surface_reading(effect):
    cls = type(effect)
    return (
        round(effect.macro(RATE_I), 6), round(effect.macro(DEPTH_I), 6),
        round(effect.macro(LAW_I), 6),
        getattr(cls, "FAULT", None), getattr(cls, "HOLD", None),
        getattr(cls, "DEPTH_CAP", None), getattr(cls, "NEVER_ZERO", None),
        getattr(cls, "FORCED_EXPONENT", None),
        getattr(cls, "LATENCY_SAMPLES", 0),
    )


class TierOne(unittest.TestCase):

    def test_silence_in_is_silence_out(self):
        data = probes.silence(4800, 2)
        wet, dry, _ = render_through(data)
        self.assertTrue(not wet.data.any())
        self.assertEqual(wet.digest, dry.digest)

    def test_depth_zero_is_a_wire(self):
        data = sine(1000.0, 0.05, -6.0)
        wet, dry, _ = render_through(data, depth=0.0)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])

    def test_latency_and_tail_are_zero(self):
        effect = build()
        try:
            self.assertEqual(effect.latency_samples, 0)
            self.assertEqual(effect.tail_samples, 0)
        finally:
            effect.deinit()

    def test_click_agrees_at_48k(self):
        # Defaults put Depth 1 at hard-left on sample 0, so channel 1 of a
        # stereo click is silent. Depth 0 is the wire the latency claim is.
        data = probes.click_stereo(8192, 256, 2)
        wet, dry, _ = render_through(data, depth=0.0)
        result = kit.click(wet, dry, 0, subsample=False)
        self.assertTrue(result["passed"], result["red"])

    def test_reported_latency_short_goes_red(self):
        data = probes.click_stereo(8192, 256, 2)
        wet, dry, _ = render_through(data, cls=ShortLatency, depth=0.0)
        result = kit.click(wet, dry, 256, subsample=False)
        self.assertFalse(result["passed"])

    def test_capabilities_declare_tempo_sync_and_the_class_reads_transport(self):
        source = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..",
                         "lib", "audioeffects", "autopan.py"))
        with open(source) as handle:
            text = handle.read()
        self.assertIn("self._transport()", text)
        effect = build()
        try:
            self.assertEqual(effect.capabilities, ("tempo_sync",))
        finally:
            effect.deinit()

    def test_mono_is_a_wire(self):
        data = sine(1000.0, 0.05, -6.0, channels=1)
        wet, dry, _ = render_through(data, channels=1, rate=5.0, depth=1.0)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])

    def test_reset_and_deinit_leave_the_source(self):
        probe = sine(1000.0, 0.05, -12.0)
        holder = probes.SwitchableSource(
            probes.ArraySource(probe, rate=RATE, channels=2, block=256))
        effect = AutoPan.create(holder, RATE)
        silent = probes.ArraySource(probes.silence(2048, 2), rate=RATE,
                                    channels=2, block=256)

        def pull(blocks):
            return probes.render(effect.output, blocks * 256, rate=RATE,
                                 channels=2, block=256, class_name="AutoPan")

        result = kit.state(effect, pull=pull, swap=holder.swap,
                           probe_source=holder.inner, silent_source=silent,
                           blocks=8, alloc_pulls=20)
        self.assertTrue(result["passed"], result["red"])


class TierTwo(unittest.TestCase):

    def test_centre_left_sounds_left_and_right_sounds_right(self):
        # The law puts pan -1 at theta 0: left gain 1, right gain 0.
        left, right = side_reading(centre=-0.8)
        self.assertGreater(left, 4.0 * right, (left, right))
        left, right = side_reading(centre=0.8)
        self.assertGreater(right, 4.0 * left, (left, right))

    def test_swapped_sides_are_red(self):
        left, right = side_reading(cls=SwappedSides, centre=-0.8)
        self.assertGreater(right, 4.0 * left, (left, right))

    def test_a1_constant_power_at_defaults_rate(self):
        # Default Rate is 2 Hz; two periods is enough to see the sweep.
        result = a1_reading(seconds=1.0, rate_hz=2.0)
        self.assertTrue(result["passed"], result["red"])

    def test_a1_mixer_law_is_red_at_defaults(self):
        clean = a1_reading(seconds=1.0, rate_hz=2.0)
        faulted = a1_reading(cls=MixerLaw, seconds=1.0, rate_hz=2.0)
        self.assertTrue(clean["passed"], clean["red"])
        self.assertFalse(faulted["passed"], faulted["values"])

    def test_a2_three_laws(self):
        data = sine(1000.0, 0.8, 0.0)
        points = []
        for law in (AutoPan.LAW_POWER_DB, 4.5, AutoPan.LAW_LINEAR_DB):
            wet, _dry, _ = render_through(data, rate=5.0, depth=1.0,
                                          law_db=law)
            m = env_metrics(wet, RATE)
            att = 0.5 * (m["centre_att_l_db"] + m["centre_att_r_db"])
            points.append(att)
            self.assertLess(abs(att - law), 0.1, (law, att))
        self.assertLess(points[0], points[1])
        self.assertLess(points[1], points[2])

    def test_a2_half_exponent_is_red_at_defaults(self):
        data = sine(1000.0, 1.0, 0.0)
        wet, _dry, _ = render_through(data, cls=HalfExponent, rate=2.0,
                                      depth=1.0)
        m = env_metrics(wet, RATE)
        att = 0.5 * (m["centre_att_l_db"] + m["centre_att_r_db"])
        self.assertGreater(abs(att - 3.01), 0.1, att)

    def test_a3_per_sample_at_floor_five_and_twenty(self):
        for rate_hz in (2.0, 5.0, 20.0):
            result = a3_reading(rate_hz=rate_hz, seconds=1.0)
            self.assertTrue(result["passed"], (rate_hz, result))

    def test_a3_block_held_is_red_at_defaults(self):
        # Defaults are 2 Hz, which is also Rate MIDI 0.
        clean = a3_reading(rate_hz=2.0, seconds=1.0)
        faulted = a3_reading(cls=BlockHeld, rate_hz=2.0, seconds=1.0)
        self.assertTrue(clean["passed"], clean)
        self.assertFalse(faulted["passed"], faulted)

    def test_a4_complement_and_mixer_fault(self):
        clean = a4_reading(seconds=1.0, rate_hz=2.0)
        linear = a4_reading(seconds=0.8, rate_hz=5.0,
                            law_db=AutoPan.LAW_LINEAR_DB)
        faulted = a4_reading(cls=MixerLaw, seconds=1.0, rate_hz=2.0)
        self.assertTrue(clean["passed"], clean)
        self.assertTrue(linear["passed"], linear)
        self.assertFalse(faulted["passed"], faulted)

    def test_a5_mono_wire_and_fault(self):
        data = sine(1000.0, 0.1, -6.0, channels=1)
        wet, dry, _ = render_through(data, channels=1, rate=5.0, depth=1.0)
        self.assertTrue(kit.wire(wet, dry)["passed"])
        faulted, fdry, _ = render_through(data, channels=1, cls=MonoStillPans,
                                          rate=5.0, depth=1.0)
        self.assertFalse(kit.wire(faulted, fdry)["passed"])

    def test_a6_hard_over_and_shallow_fault(self):
        clean = a6_depth1_reading(rate_hz=2.0, seconds=1.0)
        faulted = a6_depth1_reading(cls=ShallowHardOver, rate_hz=2.0,
                                    seconds=1.0)
        self.assertTrue(clean["passed"], clean)
        self.assertFalse(faulted["passed"], faulted)

    def test_a6_depth_zero_wire(self):
        data = sine(1000.0, 0.05, -6.0)
        wet, dry, _ = render_through(data, depth=0.0, rate=2.0)
        self.assertTrue(kit.wire(wet, dry)["passed"])

    def test_a3_and_a6_plants_stay_red_on_every_patch(self):
        """G3: A3/A6 plants fire at the default and on every shipped patch."""
        for index in range(8):
            a3 = a3_reading(cls=BlockHeld, seconds=0.6, patch=index)
            self.assertFalse(a3["passed"], (index, a3))
            a6 = a6_depth1_reading(cls=ShallowHardOver, seconds=0.6,
                                   patch=index)
            self.assertFalse(a6["passed"], (index, a6))

    def test_faults_are_not_on_the_surface(self):
        def make(cls):
            return build(cls=cls, frames=512)

        checked = 0
        for faulted in (MixerLaw, HalfExponent, BlockHeld, ShallowHardOver):
            result = faults.fault_reachability(
                AutoPan, faulted, _surface_reading, make)
            checked += result["checked"]
        self.assertGreater(checked, 100)


class Construction(unittest.TestCase):

    def test_adopted_autopan_is_the_rebuild(self):
        import audioeffects
        self.assertIs(audioeffects.AutoPan, AutoPan)
        self.assertTrue(issubclass(audioeffects.AutoPan,
                                   audioeffects._component.Component))
        self.assertEqual(audioeffects.AutoPan.__module__,
                         "audioeffects.autopan")

    def test_patch_zero_is_the_constructor(self):
        effect = build()
        try:
            self.assertEqual(effect.patch_index, 0)
            self.assertAlmostEqual(effect.macro(RATE_I), 2.0, places=5)
            self.assertEqual(effect.macro(DEPTH_I), 1.0)
        finally:
            effect.deinit()


def _made(**options):
    source = probes.ArraySource(probes.silence(2048, 2), rate=RATE,
                                channels=2, block=256)
    return AutoPan.create(source, RATE, **options)


def pan_of(left, right):
    """The pan position a pair of Q15 gains says, -1 left to +1 right, at
    the constant-power law."""
    return math.atan2(right, left) / (math.pi * 0.25) - 1.0


class TheClaims(unittest.TestCase):
    """The class docstring's claims that the tiers above do not already
    hold."""

    def test_shape_runs_from_a_triangle_to_a_sine(self):
        effect = _made()
        try:
            frames = 16
            for shape, law in ((0.0, lambda ph: 1.0 - 4.0 * abs(ph - 0.5)),
                               (1.0, lambda ph: -math.cos(2 * math.pi * ph))):
                wave_l, wave_r, _ = effect._bake_period(
                    frames, 0.9, shape, AutoPan.LAW_POWER_DB, 0.0, 0.0)
                for i in range(frames):
                    want = 0.9 * law(i / float(frames))
                    self.assertAlmostEqual(pan_of(wave_l[i], wave_r[i]), want,
                                           delta=2e-4)
        finally:
            effect.deinit()

    def test_phase_moves_where_the_sweep_starts(self):
        data = sine(1000.0, 0.1, -6.0)
        for phase, louder in ((0.0, 0), (180.0, 1)):
            wet, _dry, _ = render_through(data, rate=2.0, depth=1.0,
                                          phase=phase)
            rms = np.sqrt((wet.float[:960] ** 2).mean(axis=0))
            self.assertGreater(rms[louder], 10.0 * rms[1 - louder], phase)

    def test_sync_snaps_to_the_beat_and_stays_without_a_tempo(self):
        source = probes.ArraySource(probes.silence(2048, 2), rate=RATE,
                                    channels=2, block=256)
        effect = AutoPan(source, sample_rate=RATE, rate=5.0, sync=1.0,
                         transport=lambda: (True, 0.0, 120.0, 4, 4))
        try:
            # 120 bpm: one, two, four or eight sweeps a beat is 2, 4, 8 or
            # 16 Hz, and 5 Hz is nearest 4.
            self.assertEqual(AutoPan.SYNC_BEATS, (1.0, 0.5, 0.25, 0.125))
            self.assertEqual(effect._macro_engineering()[0], 4.0)
        finally:
            effect.deinit()
        effect = _made(rate=5.0, sync=1.0)
        try:
            self.assertAlmostEqual(effect._macro_engineering()[0], 5.0,
                                   places=9)
        finally:
            effect.deinit()

    def test_the_sweep_sits_six_db_under_the_source(self):
        data = sine(1000.0, 0.3, -6.0)
        peak = int(np.abs(np.array(data)).max())
        for centre, near in ((-1.0, 0), (1.0, 1)):
            wet, _dry, _ = render_through(data, rate=2.0, depth=1e-4,
                                          centre=centre)
            got = wet.data[4096:]
            self.assertLessEqual(abs(int(got[:, near].max()) - peak // 2), 2)
            # A hair off the rail (depth 1e-4), the far side leaks an LSB.
            self.assertLessEqual(int(np.abs(got[:, 1 - near]).max()), 1)

    def test_construction_needs_audiomath(self):
        saved = sys.modules.get("audiomath", False)
        sys.modules["audiomath"] = None
        try:
            with self.assertRaises(ImportError):
                _made()
        finally:
            if saved is False:
                del sys.modules["audiomath"]
            else:
                sys.modules["audiomath"] = saved
        _made().deinit()


#: Each claim sentence of the player text (module and class docstrings),
#: and the tests that hold it.
CLAIMS = (
    ("`AutoPan` - an auto-panner: a pan law under an LFO.",
     ("TierTwo.test_a1_constant_power_at_defaults_rate",
      "TierTwo.test_a3_per_sample_at_floor_five_and_twenty")),
    ("The player's text is the class docstring; the `CLAIMS` table in the "
     "class's test file ties its claim sentences to tests.",
     ("Claims.test_every_claim_is_in_the_docstring_and_tested",)),
    ("An auto-panner: an LFO sweeps your signal between the speakers, with "
     "a new pan position on every sample, under a pan law.",
     ("TierTwo.test_a3_per_sample_at_floor_five_and_twenty",
      "TierTwo.test_a3_block_held_is_red_at_defaults",
      "TierTwo.test_a1_constant_power_at_defaults_rate")),
    ("Depth is how far it swings: at Depth 1 it reaches each side, where "
     "the far speaker is silent, and at Depth 0 the output is the input.",
     ("TierTwo.test_a6_hard_over_and_shallow_fault",
      "TierOne.test_depth_zero_is_a_wire",
      "TierTwo.test_a6_depth_zero_wire")),
    ("Shape runs the sweep from a triangle at 0 to a sine at 1.",
     ("TheClaims.test_shape_runs_from_a_triangle_to_a_sine",)),
    ("Law is how far the centre dips; at 3.01 dB the power holds "
     "steady across the sweep.",
     ("TierTwo.test_a2_three_laws",
      "TierTwo.test_a1_constant_power_at_defaults_rate",
      "TierTwo.test_a4_complement_and_mixer_fault")),
    ("Centre moves the middle of the sweep towards one side.",
     ("TierTwo.test_centre_left_sounds_left_and_right_sounds_right",
      "TierTwo.test_swapped_sides_are_red")),
    ("Phase moves where the sweep starts: at 0 it starts on the left.",
     ("TheClaims.test_phase_moves_where_the_sweep_starts",)),
    ("With Sync on, Rate snaps to the nearest of one, two, four or eight "
     "sweeps a beat of the host's tempo; with no host tempo, Rate stays "
     "where the knob is.",
     ("TheClaims.test_sync_snaps_to_the_beat_and_stays_without_a_tempo",
      "TierOne.test_capabilities_declare_tempo_sync_and_the_class_reads_"
      "transport")),
    ("The sweep sits 6 dB under your source: hard over, the near speaker "
     "plays it at half level.",
     ("TheClaims.test_the_sweep_sits_six_db_under_the_source",)),
    ("A mono source passes untouched, and silence in is silence out.",
     ("TierOne.test_mono_is_a_wire", "TierTwo.test_a5_mono_wire_and_fault",
      "TierOne.test_silence_in_is_silence_out")),
    ("Latency is zero at every setting, and so is the tail: nothing looks "
     "ahead and nothing rings on.",
     ("TierOne.test_latency_and_tail_are_zero",
      "TierOne.test_click_agrees_at_48k",
      "TierOne.test_reported_latency_short_goes_red")),
    ("The class needs audiodsp's `audiomath`, and on a board without it "
     "construction raises `ImportError`.",
     ("TheClaims.test_construction_needs_audiomath",)),
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
        doc = autopan.__doc__ + " " + AutoPan.__doc__
        self.assertEqual(claim_problems(doc), [])
        # The checker can fail: a figure outside a claim, a claim the
        # docstring does not carry, a test that does not exist.
        self.assertTrue(claim_problems(doc + " It reads 12 ms."))
        self.assertTrue(claim_problems(doc.replace("nothing looks ahead",
                                                   "nothing looks back")))
        self.assertTrue(claim_problems(doc, CLAIMS + (
            ("A mono source passes untouched, and silence in is silence "
             "out.", ("TierOne.test_nothing_here",)),)))


#: Not here, because they change only a reported tail or latency:
#: `ShortLatency`.
KIT_PLANTS = {
    "MixerLaw": MixerLaw,
    "HalfExponent": HalfExponent,
    "BlockHeld": BlockHeld,
    "ShallowHardOver": ShallowHardOver,
    "SwappedSides": (SwappedSides, 5),
    "MonoStillPans": (MonoStillPans, None, {"channels": 1}),
}


if __name__ == "__main__":
    unittest.main()
