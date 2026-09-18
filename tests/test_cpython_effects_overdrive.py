"""`Overdrive`'s own invariant and planted-fault tests.

Dossier: workspace docs/effects-internal/dossiers/Overdrive.md, frozen
2026-09-17. Exhaustive rate coverage lives in the evidence pack; this
file asserts at 48 kHz unless the test is about rate or latency.
"""

import math
import os
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import kit_faults                                               # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects import overdrive as rebuilt                   # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
Overdrive = rebuilt.Overdrive


def sine(hz, dbfs, frames=48000, rate=RATE, channels=2):
    index = np.arange(frames)
    values = 10.0 ** (dbfs / 20.0) * np.sin(2.0 * math.pi * hz * index / rate)
    quantised = np.clip(np.round(values * 32767.0), -32768, 32767).astype(
        np.int64)
    if channels == 2:
        quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist())


def square(hz, dbfs, frames=48000, rate=RATE, channels=2):
    index = np.arange(frames)
    values = 10.0 ** (dbfs / 20.0) * np.sign(
        np.sin(2.0 * math.pi * hz * index / rate) + 1e-18)
    quantised = np.clip(np.round(values * 32767.0), -32768, 32767).astype(
        np.int64)
    if channels == 2:
        quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist())


def build(cls=None, rate=RATE, channels=2, frames=48000, probe=None,
          **options):
    cls = cls or Overdrive
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, label=None, class_name="Overdrive",
                         latency_samples=effect.latency_samples)


class BiasedOverdrive(Overdrive):
    """T2: force even harmonics at Symmetry 0."""
    NAME = 'Overdrive'

    def _refresh(self):
        Overdrive._refresh(self)
        self._shaper.set(bias=0.25)
        self._clip_bias = 0.25


class BaseRateOverdrive(Overdrive):
    """T7: ×1 at the class's default macros."""
    NAME = 'Overdrive'

    def _build(self, **options):
        options["oversample"] = 1
        Overdrive._build(self, **options)


#: The hardest clip a 1025-point table can express - rail to rail across
#: one table step. Not a tuned number, the extreme: at the diode's own
#: 0.3 V threshold (knee 0.1) the fault goes healthy at 9 of 52 surface
#: positions under T7's restated bars, because a 6.9x overdrive of a 0.3 V
#: knee has edges soft enough to alias quietly at Drive minimum.
HARD_KNEE = 2.0 / 1024.0


def _hard_curve(knee=HARD_KNEE, points=1025):
    """A hard clipper over the same input span as the shipped diode curve."""
    out = array("h")
    last = points - 1
    for index in range(points):
        x = 2.0 * index / last - 1.0
        y = max(-1.0, min(1.0, x / knee))
        out.append(max(-32768, min(32767, int(round(y * 32767.0)))))
    return out


HARD_CURVE = _hard_curve()


class RawClipOverdrive(Overdrive):
    """T7's guard: the naive drive - a hard clip run at the sample rate.

    The alias floor the class claims comes from oversampling a *smooth*
    diode curve. This is the build that does neither, and it is the one
    the dossier's section 8 Q3 says never to write. Unlike
    `BaseRateOverdrive` it is red wherever the class is in circuit at all,
    because a discontinuous transfer puts high-order energy in the wet
    branch at every Drive position rather than only at the hot end - but
    only once the clip is as hard as the table can express (`HARD_KNEE`).
    At the diode's own 0.3 V threshold it went healthy at 9 of 52 surface
    positions under the restated bars.
    """
    NAME = "Overdrive"

    def _build(self, **options):
        options["oversample"] = 1
        Overdrive._build(self, **options)
        self._shaper.set(curve=HARD_CURVE)


class NoOutputPole(Overdrive):
    """The class as it shipped at `80d5a26`: no capacitor at the jack.

    The wet voice takes the shaper directly, so Symmetry's operating-point
    offset reaches the output and stands there. This is what proves
    `TestOverdriveTheOutputPole` can fail.
    """
    NAME = "Overdrive"

    def _prime_if_wet(self):
        Overdrive._prime_if_wet(self)
        if getattr(self, "_primed", False):
            self._circuit.voice[1].play(self._shaper)

    def _settle_dc(self):
        return False


class WetOnlyOverdrive(Overdrive):
    """T3: the circuit sum without its dry term.

    T3's fall is the dry note growing linearly while the clipped feedback
    voltage saturates. Drop the dry leg and the same measurement *rises*
    with level, which is what any clipper does - so the fall is the
    structure and not the curve. `NoClipAdd` and `NoHighPass` both still
    fall, which is why neither of them guards this clause.
    """
    NAME = "Overdrive"

    def _prime_if_wet(self):
        Overdrive._prime_if_wet(self)
        if getattr(self, "_primed", False):
            self._circuit.voice[0].level = 0.0


class NoClipAdd(Overdrive):
    """T5: drop the clipped add at the shipped default (circuit wet = 0)."""
    NAME = "Overdrive"

    def _prime_if_wet(self):
        Overdrive._prime_if_wet(self)
        self._circuit.voice[1].level = 0.0


class TestOverdrive(unittest.TestCase):
    def test_mix_zero_is_wire(self):
        probe = sine(1000, -14)
        effect = build(probe=probe, mix=0.0)
        wet = render(effect, 48000)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            48000, rate=RATE, channels=2, block=256)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])

    def test_even_harmonics_quiet_at_default(self):
        effect = build(probe=sine(1000, -14))
        wet = render(effect, 48000)
        spec = kit.spectrum(wet, 1000, harmonics=10, size=4800)
        h2 = spec["values"]["harmonic_db"]["h2"]
        self.assertLess(h2, -40.0)

    def test_t2_fault_bias_raises_h2_at_default(self):
        clean = build(probe=sine(1000, -14))
        dirty = build(BiasedOverdrive, probe=sine(1000, -14))
        h2_clean = kit.spectrum(render(clean, 48000), 1000, harmonics=6,
                                size=4800)["values"]["harmonic_db"]["h2"]
        h2_fault = kit.spectrum(render(dirty, 48000), 1000, harmonics=6,
                                size=4800)["values"]["harmonic_db"]["h2"]
        self.assertLess(h2_clean, -40.0)
        self.assertGreater(h2_fault, -40.0)

    def test_t7_alias_at_the_constructor_default(self):
        """Clause 1, the headline: -70 dB at the default, wet branch."""
        floor = _alias(Overdrive)
        self.assertLess(floor, rebuilt.ALIAS_DEFAULT_DB,
                        "default read %.3f dB" % floor)

    def test_t7_alias_at_the_worst_macro_corner(self):
        """Clause 3: -40 dB anywhere, and the corner that parked the class.

        Drive max with Body at the bottom of its travel and Tone open is
        the worst cell on the whole shipped surface. Under the old -60 dB
        bar it read -47.7 and was a park; the committed suite never saw it
        because every T7 test held Body at 720.
        """
        floor = _alias(Overdrive, drive=108.0, level=1.0, tone=1.0,
                       body=360.0)
        self.assertLess(floor, rebuilt.ALIAS_SURFACE_DB,
                        "worst corner read %.3f dB" % floor)
        self.assertGreater(floor, -60.0,
                           "this cell is the reason T7 was restated; if it "
                           "now meets -60 the restatement is stale")

    def test_t7_at_the_worst_corner_up_to_full_scale(self):
        """Clause 4, the thin one: the input level axis.

        T7's frozen row holds the input at -6 dBFS, but a source can be
        louder and the floor rises with level above -14 dBFS. At the worst
        corner, full scale is where the class has the whole of its margin:
        1.3 dB at 22.05 kHz.
        """
        for rate in (48000, 44100, 22050):
            worst = None
            for dbfs in (-26, -20, -14, -10, -6, -3, -1, 0):
                floor = _alias(Overdrive, rate=rate, dbfs=dbfs, drive=108.0,
                               level=1.0, tone=1.0, body=360.0)
                worst = floor if worst is None else max(worst, floor)
                self.assertLess(floor, rebuilt.ALIAS_SURFACE_DB,
                                "%d Hz at %+d dBFS read %.3f dB"
                                % (rate, dbfs, floor))
            self.assertGreater(worst, -55.0,
                               "%d Hz: if the level axis no longer bites, "
                               "T7d has stopped measuring anything" % rate)

    def test_t7_over_the_body_travel_at_drive_max(self):
        """The axis the pack held fixed: Body from 360 to 1440 Hz."""
        for body in (360.0, 480.0, 720.0, 1020.0, 1440.0):
            for tone in (0.0, 0.5, 1.0):
                floor = _alias(Overdrive, drive=108.0, level=1.0, tone=tone,
                               body=body)
                self.assertLess(floor, rebuilt.ALIAS_SURFACE_DB,
                                "Body %g Tone %g read %.3f dB"
                                % (body, tone, floor))

    def test_t7_guard_is_red_at_the_default(self):
        """`RawClipOverdrive` - no oversampling, the hardest table clip."""
        clean = _alias(Overdrive)
        fault = _alias(RawClipOverdrive)
        self.assertLess(clean, rebuilt.ALIAS_DEFAULT_DB)
        self.assertGreater(fault, rebuilt.ALIAS_DEFAULT_DB)
        self.assertGreater(fault - clean, 40.0,
                           "clean %.3f fault %.3f" % (clean, fault))

    def test_t7_null_build_red(self):
        def measure_with(cls):
            try:
                alias = _alias(cls)
            except kit.MeasurementRefused as error:
                # A wire has no wet branch, so T7's instrument cannot even
                # be pointed at it. That is red, and it is the strongest
                # kind of red: the measurement is not available, so the
                # trait is certainly not demonstrated.
                return {"passed": False, "why": str(error)}
            return {"passed": alias <= rebuilt.ALIAS_DEFAULT_DB,
                    "alias": alias}

        result = kit_faults.null_build_red(Overdrive, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t3_thd_falls_as_input_rises(self):
        thds = []
        for dbfs in (-14, -6):
            effect = build(probe=sine(1000, dbfs), drive=108.0, level=1.0)
            spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                size=4800)
            thds.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
        self.assertLess(thds[1], thds[0])

    def test_latency_zero_click(self):
        probe = probes.click_stereo(frames=8192, offset=256, channels=2)
        effect = build(probe=probe, frames=8192)
        wet = render(effect, 8192)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            8192, rate=RATE, channels=2, block=256)
        result = kit.click(wet, dry, 0, subsample=False)
        self.assertTrue(result["passed"], result["red"])

    def test_never_uses_distortion_node(self):
        with open(rebuilt.__file__, encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("audiofilters.Distortion", text)
        self.assertIn("audioshaper.Waveshaper", text)

    def test_capabilities_and_tail_match_what_was_built(self):
        effect = build(probe=probes.silence(256, 2), frames=256)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.tail_samples, 4096)
        effect.reset()
        effect.deinit()
        leftover = probes.ArraySource(sine(440, -12, frames=256), rate=RATE,
                                      block=256, channels=2)
        leftover_out = probes.render(leftover, 256, rate=RATE, channels=2,
                                     block=256)
        self.assertTrue(any(leftover_out.data.reshape(-1)))

    def test_level_honest_on_mix_zero(self):
        probe = sine(1000, -20)
        effect = build(probe=probe, mix=0.0)
        wet = render(effect, 48000)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            48000, rate=RATE, channels=2, block=256)
        result = kit.level(wet, dry)
        self.assertTrue(result["passed"], result["red"])

    def test_t1_bass_cleaner_than_1k_at_default(self):
        def thd(hz):
            effect = build(probe=sine(hz, -14))
            spec = kit.spectrum(render(effect, 48000), hz, harmonics=10,
                                size=4800)
            return 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))

        self.assertLess(thd(100), thd(1000))

    def test_t3_thd_falls_at_default(self):
        thds = []
        for dbfs in (-14, -6):
            effect = build(probe=sine(1000, dbfs))
            spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                size=4800)
            thds.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
        self.assertLess(thds[1], thds[0])

    def test_t5_thd_rises_with_drive_at_minus26(self):
        thds = []
        for drive in (12.0, 36.0, 108.0):
            effect = build(probe=sine(1000, -26), drive=drive, level=1.0)
            spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                size=4800)
            thds.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
        self.assertLess(thds[0], thds[1])
        self.assertLess(thds[1], thds[2])

    def test_t6_never_clean_at_default(self):
        effect = build(probe=sine(1000, -14))
        spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                            size=4800)
        thd = 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))
        self.assertGreater(thd, 8.0)

    def test_t3_null_build_red(self):
        def measure_with(cls):
            thds = []
            for dbfs in (-14, -6):
                effect = build(cls, probe=sine(1000, dbfs))
                spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                    size=4800)
                thds.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
            passed = thds[0] > 8.0 and thds[1] < thds[0] - 0.4
            return {"passed": passed, "thds": thds}

        result = kit_faults.null_build_red(Overdrive, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_bias_fault_not_on_the_macro_surface(self):
        out = kit_faults.fault_reachability(
            Overdrive, BiasedOverdrive,
            lambda effect: float(effect._clip_bias),
            lambda cls: build(cls, probe=probes.silence(512, 2), frames=512),
            label="Overdrive T2 BiasedOverdrive")
        self.assertGreater(abs(out["target"] - out["clean"]), 0.05)

    def test_t1_null_build_red(self):
        def measure_with(cls):
            def one(hz):
                effect = build(cls, probe=sine(hz, -14))
                spec = kit.spectrum(render(effect, 48000), hz, harmonics=10,
                                    size=4800)
                return 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))

            bass, mid = one(100), one(1000)
            return {"passed": bass < mid and mid >= 5.0,
                    "thd100": bass, "thd1000": mid}

        result = kit_faults.null_build_red(Overdrive, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t2_null_build_red(self):
        def measure_with(cls):
            effect = build(cls, probe=sine(1000, -14))
            spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                size=4800)
            thd_pct = 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))
            h2 = spec["values"]["harmonic_db"]["h2"]
            return {"passed": h2 < -40.0 and thd_pct >= 5.0,
                    "h2": h2, "thd": thd_pct}

        result = kit_faults.null_build_red(Overdrive, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t5_null_build_red(self):
        def measure_with(cls):
            thds = []
            for drive in (12.0, 36.0, 108.0):
                effect = build(cls, probe=sine(1000, -26), drive=drive,
                               level=1.0)
                spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                    size=4800)
                thds.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
            return {"passed": thds[0] < thds[1] < thds[2] and thds[2] >= 5.0,
                    "thds": thds}

        result = kit_faults.null_build_red(Overdrive, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t5_fault_no_clip_add_at_default(self):
        def thd(cls):
            effect = build(cls, probe=sine(1000, -26))
            spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                size=4800)
            return 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))

        self.assertGreater(thd(Overdrive), 5.0)
        self.assertLess(thd(NoClipAdd), 1.0)

        def rising(cls):
            values = []
            for drive in (12.0, 36.0, 108.0):
                effect = build(cls, probe=sine(1000, -26), drive=drive,
                               level=1.0)
                spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                    size=4800)
                values.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
            return values

        faulted = rising(NoClipAdd)
        self.assertFalse(faulted[0] < faulted[1] < faulted[2])

        checked = 0
        for patch in range(8):
            effect = build(NoClipAdd, probe=sine(1000, -26, frames=4800),
                           frames=4800, patch=patch)
            self.assertEqual(effect._circuit.voice[1].level, 0.0)
            checked += 1
            effect.deinit()
        for midi in (0, 32, 64, 96, 127):
            effect = build(NoClipAdd, probe=sine(1000, -26, frames=4800),
                           frames=4800)
            effect.set_macro(0, midi)
            self.assertEqual(effect._circuit.voice[1].level, 0.0)
            checked += 1
            effect.deinit()
        self.assertEqual(checked, 13)

        out = kit_faults.fault_reachability(
            Overdrive, NoClipAdd,
            lambda effect: float(effect._circuit.voice[1].level),
            lambda cls: build(cls, probe=probes.silence(512, 2), frames=512),
            label="Overdrive T5 NoClipAdd")
        self.assertGreater(abs(out["target"] - out["clean"]), 0.5)


def _alias(cls, rate=RATE, midi=None, frames=None, wet=True, dbfs=-6,
           **options):
    """T7's reading: 101 exact periods of 1010 Hz at -6 dBFS.

    **Wet branch by default.** T7 is stated on the clip branch with the
    dry copy muted, because the dry note flatters every floor by 5.6 to
    6.6 dB. This class's dry voice is on the circuit mixer, one stage
    before the output, and `tools/effect_measurements.mute_dry` searched
    the output mixer alone until audiocomponents#81 moved the reach into
    it; it finds the inner voice now (audiocomponents#68).
    """
    size = int(round(101 * rate / 1010.0))
    frames = frames or size * 3
    effect = build(cls, rate=rate,
                   probe=sine(1010, dbfs, frames=frames + 2048, rate=rate),
                   frames=frames, **options)
    try:
        if midi:
            for index, position in midi.items():
                effect.set_macro(index, position)
        if wet:
            rendered = probes.wet_render(
                effect, frames, allow_tail_frames=4, rate=rate, channels=2,
                block=256, class_name="Overdrive",
                latency_samples=effect.latency_samples)
        else:
            rendered = render(effect, frames, rate=rate)
        spec = kit.spectrum(rendered, 1010, harmonics=10, size=size)
        return spec["values"]["alias_floor_db"]
    finally:
        effect.deinit()


def _macro_walk(rate=RATE):
    """Every macro at 0 / 64 / 127 and every shipped patch, as MIDI maps.

    Level MIDI 0 is skipped and named: at Mix 1 the one mixer leg carrying
    the graph is at zero, so the render is silence and SPECTRUM refuses.
    That is the class being off, not a fault being dialled back.
    """
    walk = []
    for index in range(7):
        for position in (0, 64, 127):
            if index == 2 and position == 0:
                continue
            effect = build(rate=rate, probe=probes.silence(512, 2),
                           frames=512)
            effect.set_macro(index, position)
            walk.append(((index, position),
                         {i: effect.get_macro(i) for i in range(7)}))
            effect.deinit()
    for patch in range(8):
        effect = build(rate=rate, probe=probes.silence(512, 2), frames=512,
                       patch=patch)
        walk.append((("patch", patch),
                     {i: effect.get_macro(i) for i in range(7)}))
        effect.deinit()
    return walk


class TestOverdriveRatePolicy(unittest.TestCase):
    """The oversample factor is derived from the rate, not a constant."""

    def test_factor_by_rate(self):
        self.assertEqual(rebuilt.shipped_oversample(48000), 4)
        self.assertEqual(rebuilt.shipped_oversample(44100), 8)
        self.assertEqual(rebuilt.shipped_oversample(22050), 8)
        self.assertEqual(rebuilt.shipped_oversample(96000), 4)

    def test_the_rule_below_24_kHz_is_what_the_docstring_says(self):
        """x8 at every rate under 48 kHz, and the 192 kHz floor is a target
        rather than a guarantee: under 24 kHz nothing reaches it, because
        x8 is where the node stops. The docstring used to read as though
        the floor were always met."""
        for rate in (8000, 16000, 22050, 24000, 32000, 44100):
            self.assertEqual(rebuilt.shipped_oversample(rate), 8, rate)
        for rate in (48000, 96000, 192000):
            self.assertEqual(rebuilt.shipped_oversample(rate), 4, rate)
        under = [rate for rate in (8000, 16000, 22050)
                 if rate * rebuilt.shipped_oversample(rate)
                 < rebuilt.OVERSAMPLE_FLOOR_HZ]
        self.assertEqual(under, [8000, 16000, 22050])

    def test_class_takes_the_factor_its_rate_asks_for(self):
        for rate, factor in ((48000, 4), (44100, 8), (22050, 8)):
            effect = build(rate=rate, probe=probes.silence(512, 2),
                           frames=512)
            self.assertEqual(effect._oversample, factor)
            effect.deinit()

    def test_t7_at_the_default_at_every_rate(self):
        """Clause 1 at all three rates, on the wet branch."""
        for rate in (48000, 44100, 22050):
            floor = _alias(Overdrive, rate=rate)
            self.assertLess(floor, rebuilt.ALIAS_DEFAULT_DB,
                            "%d Hz read %.3f dB" % (rate, floor))

    def test_t7_at_drive_max_at_every_rate(self):
        """Clause 3 at Drive max, every rate, at the worst Body/Tone."""
        for rate in (48000, 44100, 22050):
            floor = _alias(Overdrive, rate=rate, drive=108.0, level=1.0,
                           tone=1.0, body=360.0)
            self.assertLess(floor, rebuilt.ALIAS_SURFACE_DB,
                            "%d Hz read %.3f dB" % (rate, floor))

    def test_t7_on_every_shipped_patch_at_every_rate(self):
        """Clause 2: -50 dB at all eight patches, as shipped, all rates."""
        for rate in (48000, 44100, 22050):
            for patch in range(8):
                floor = _alias(Overdrive, rate=rate, patch=patch)
                self.assertLess(floor, rebuilt.ALIAS_PATCH_DB,
                                "%d Hz patch %d read %.3f dB"
                                % (rate, patch, floor))

    def test_x8_is_the_node_ceiling_and_22k_still_misses_minus_60(self):
        """Why T7 was restated: x8 is all there is, and at 22.05 kHz it
        reads about -47 dB at the worst corner. No factor reaches -60."""
        readings = [_alias(Overdrive, rate=22050, drive=108.0, level=1.0,
                           tone=1.0, body=360.0, oversample=factor)
                    for factor in (1, 2, 4, 8)]
        self.assertEqual(readings, sorted(readings, reverse=True), readings)
        self.assertGreater(readings[-1], -60.0, readings)
        with self.assertRaises(ValueError):
            build(probe=probes.silence(512, 2), frames=512, oversample=16)

    def test_the_lean_position_surrenders_t7(self):
        """`oversample=2` is the documented lean handle and it is red on
        clause 1 at the constructor default."""
        floor = _alias(Overdrive, oversample=2)
        self.assertGreater(floor, rebuilt.ALIAS_DEFAULT_DB,
                           "x2 read %.3f dB" % floor)


class TestOverdriveT7Guard(unittest.TestCase):
    def test_raw_clip_fault_is_red_at_the_default_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            clean = _alias(Overdrive, rate=rate)
            fault = _alias(RawClipOverdrive, rate=rate)
            self.assertLess(clean, rebuilt.ALIAS_DEFAULT_DB, rate)
            self.assertGreater(fault, rebuilt.ALIAS_DEFAULT_DB, rate)

    def test_raw_clip_fault_not_restorable_from_the_surface(self):
        """Red at every position where the class is in circuit at all.

        Mix 0 is the Tier 1 wire - `output` **is** the source there - so
        there is no wet branch to read, which is the class out of circuit
        and not the guard dialled back. The pack's walk goes wider (54
        positions, three rates, 0 healthy); this is the short version the
        suite can afford.
        """
        healthy = []
        walk = _macro_walk()
        for where, midi in walk:
            try:
                floor = _alias(RawClipOverdrive, midi=midi)
            except kit.MeasurementRefused:
                continue                       # Mix 0, the wire
            if floor <= rebuilt.ALIAS_SURFACE_DB:
                healthy.append((where, floor))
        self.assertEqual(len(walk), 28)
        self.assertEqual(healthy, [], healthy)

    def test_base_rate_is_red_wherever_the_clip_stage_is_in_circuit(self):
        """T7e: what the shipped oversampling is worth, position by
        position, with the clean class printed beside the fault.

        Under the three absolute bars alone this fault was healthy at 17
        of 54 surface positions and the pack called it "a diagnostic, not
        a guard" on the grounds that switching the oversampling off
        removes nothing there. Audit 3 (p)2 counted it: that is true at
        five of them and **false at twelve**, seven of which are worth 34
        to 40 dB. What makes the fault green there is the class's own 30
        to 40 dB of margin, not the factor being idle.

        So T7 gained a clause the fault cannot be healthy under.
        `ALIAS_OVERSAMPLE_COST_DB` is what the factor is worth - the
        shipped build's wet floor against the same build at the base
        rate - **at every position where the clip stage is in circuit**,
        which is Drive above its floor and Body below the top of its
        travel. `BaseRateOverdrive`'s own cost is 0 dB by construction,
        so it is red at every position the clause is claimed over.

        Outside the region the clause is not claimed and the numbers are
        recorded rather than asserted: at 48 kHz the factor is worth
        0.813 dB at `patch 1 Body 127`, 1.300 at `patch 7 Body 127`,
        4.866 at `drive=12`, and 7.649 at patch 7 - and the class meets
        its absolute bar at x1 at all four. The pack walks 54 positions
        at three rates; this walks the suite's 28 at 48 kHz.
        """
        floor_drive = rebuilt.Overdrive._MACRO_RANGES[0][0]
        top_body = rebuilt.Overdrive._MACRO_RANGES[4][1]
        claimed = []
        outside = []
        for where, midi in _macro_walk():
            effect = build(probe=probes.silence(512, 2), frames=512)
            for index, position in midi.items():
                effect.set_macro(index, position)
            drive = effect._value(0)
            body = effect._value(4)
            effect.deinit()
            try:
                clean = _alias(Overdrive, midi=midi)
                base = _alias(BaseRateOverdrive, midi=midi)
            except kit.MeasurementRefused:
                continue                       # Mix 0, the wire
            row = (where, round(clean, 3), round(base, 3),
                   round(base - clean, 3))
            if drive > floor_drive and body < top_body:
                claimed.append(row)
            else:
                outside.append(row)
        self.assertTrue(claimed)
        thin = [row for row in claimed
                if row[3] < rebuilt.Overdrive.ALIAS_OVERSAMPLE_COST_DB]
        self.assertEqual(
            thin, [],
            "the oversampling is worth less than %s dB where the clip "
            "stage is in circuit; rows are (position, clean, x1, cost): "
            "%r of %d claimed, %d outside the region %r"
            % (rebuilt.Overdrive.ALIAS_OVERSAMPLE_COST_DB, thin,
               len(claimed), len(outside), outside))
        for where, clean, base, _cost in outside:
            self.assertLessEqual(
                base, rebuilt.ALIAS_SURFACE_DB,
                "outside T7e's region the class is claimed to meet its "
                "absolute bar without the oversampling, and %r does not "
                "(clean %s, x1 %s)" % (where, clean, base))


class TestOverdriveTheOutputPole(unittest.TestCase):
    """audiocomponents#68, audit 3 ruling (n): the capacitor at the jack.

    Every circuit this family models is DC-coupled inside and AC-coupled
    at the output. `Overdrive` had the first half only: Symmetry is a bias
    into the shaper, and at shipped patch 6 that bias walked out as
    **+4461 LSB of standing DC into digital silence, for ever**, at all
    three rates. `DC_BLOCK_HZ` is the missing pole.

    `NoOutputPole` below is the class as it shipped at `80d5a26`, and it
    is what proves these rows can fail.
    """

    def peak_into_silence(self, cls, patch, rate=RATE, frames=16384):
        effect = build(cls, rate=rate, probe=probes.silence(frames, 2),
                       frames=frames, patch=patch)
        try:
            quiet = render(effect, frames, rate=rate)
            data = quiet.data.reshape(-1)
            return int(np.abs(data).max()), int(abs(data[-2]))
        finally:
            effect.deinit()

    def test_the_planted_class_stands_dc_where_this_one_does_not(self):
        for rate in (RATE, 44100, 22050):
            planted = self.peak_into_silence(NoOutputPole, 6, rate=rate)
            shipped = self.peak_into_silence(Overdrive, 6, rate=rate)
            self.assertGreater(
                planted[1], 1000,
                "the planted class has to stand DC at patch %d or this "
                "row proves nothing (rate %d, peak %d, last frame %d)"
                % (6, rate, planted[0], planted[1]))
            self.assertEqual(shipped, (0, 0),
                             "patch 6 at %d Hz: peak %d, last frame %d"
                             % (rate, shipped[0], shipped[1]))

    def test_the_computed_offset_is_the_one_the_shaper_emits(self):
        """`_shaper_dc()` reads the table in Python; the node reads it in
        C. The charge is only as good as those two agreeing."""
        for symmetry in (-1.0, -0.35, 0.35, 0.6984, 1.0):
            effect = build(probe=probes.silence(512, 2), frames=512,
                           symmetry=symmetry)
            try:
                computed = effect._shaper_dc()
                effect._shaper.play(effect._quiet, loop=True)
                block = None
                for _ in range(4):
                    _state, data = probes.audiocore.get_buffer(effect._shaper)
                    block = array("h", bytes(data))
                emitted = block[0]
            finally:
                effect.deinit()
            self.assertLess(
                abs(computed - emitted), 2.0,
                "Symmetry %+.4f: Python reads the curve at %.3f LSB and "
                "the node emits %d" % (symmetry, computed, emitted))


class TestOverdriveTheInputCeiling(unittest.TestCase):
    """Audit 3 ruling (o): a class that runs out of headroom says where.

    `Overdrive` adds a clipped shelf to a dry note at unity, so it reaches
    the int16 rail somewhere, and until the third fix round it named no
    level at all. Patch 7 `Edge Boost` railed at **-3 dBFS** at 700 Hz and
    1 kHz before the output pole took the standing offset off the peaks;
    behind the pole it takes 0 dBFS to reach the rail at all.
    """

    def rails(self, dbfs, hz, patch=None, cells=None, rate=RATE):
        frames = 4800
        effect = build(rate=rate, frames=frames,
                       probe=sine(hz, dbfs, frames=frames, rate=rate),
                       **({} if patch is None else {"patch": patch}))
        try:
            for index, position in (cells or {}).items():
                effect.set_macro(index, position)
            data = render(effect, frames, rate=rate).data.reshape(-1)
            return int(np.sum((data >= 32767) | (data <= -32768)))
        finally:
            effect.deinit()

    def test_no_shipped_patch_rails_at_the_stated_ceiling(self):
        for patch in sorted(Overdrive.PATCHES):
            for hz in (100.0, 400.0, 700.0, 1000.0, 2000.0):
                rails = self.rails(rebuilt.INPUT_CEILING_DBFS, hz,
                                   patch=patch)
                self.assertEqual(
                    rails, 0,
                    "patch %d rails %d samples at the stated ceiling "
                    "(%s dBFS, %.0f Hz)"
                    % (patch, rails, rebuilt.INPUT_CEILING_DBFS, hz))

    def test_the_ceiling_is_where_it_says_it_is(self):
        """Above it, the rail is reachable - or the number is charity."""
        self.assertGreater(self.rails(0.0, 400.0, patch=7), 0)
        self.assertGreater(
            self.rails(-3.0, 700.0, cells={0: 127, 1: 127, 2: 127}), 0)

    def test_the_surface_ceiling_holds_at_the_hot_corner(self):
        for hz in (100.0, 400.0, 700.0, 1000.0, 2000.0):
            rails = self.rails(rebuilt.SURFACE_CEILING_DBFS, hz,
                               cells={0: 127, 1: 127, 2: 127})
            self.assertEqual(
                rails, 0,
                "Drive max, Tone open, Level max rails %d samples at the "
                "surface ceiling (%s dBFS, %.0f Hz)"
                % (rails, rebuilt.SURFACE_CEILING_DBFS, hz))


class TestOverdriveT5OverSymmetry(unittest.TestCase):
    """T5's law is a claim at Symmetry centred, and now says so.

    "THD at -26 dBFS rises with Drive" was stated with no Symmetry
    qualifier. Symmetry biases the shaper, so it decides which part of the
    curve the drive pushes into: off centre the law turns over at Drive
    MIDI 64 and falls above it, at all three rates (audit 3 (p)6).
    """

    def thd(self, drive, symmetry, rate=RATE, dbfs=-26):
        frames = rate // 2
        effect = build(rate=rate, frames=frames,
                       probe=sine(1000, dbfs, frames=frames, rate=rate))
        try:
            effect.set_macro(0, drive)
            effect.set_macro(6, symmetry)
            spec = kit.spectrum(render(effect, frames, rate=rate), 1000,
                                harmonics=10, size=frames)
            return 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))
        finally:
            effect.deinit()

    def test_the_law_holds_at_the_centre_detent(self):
        for rate in (RATE, 44100, 22050):
            row = [self.thd(drive, 64, rate=rate)
                   for drive in (0, 64, 127)]
            self.assertEqual(sorted(row), row, (rate, row))

    def test_the_law_turns_over_off_centre(self):
        for symmetry in (0, 32, 96, 127):
            row = [self.thd(drive, symmetry) for drive in (0, 64, 127)]
            self.assertGreater(
                row[1], row[2],
                "Symmetry MIDI %d: the docstring says the law turns over "
                "at Drive MIDI 64 and it did not (%r)" % (symmetry, row))


class TestOverdriveT3Kind(unittest.TestCase):
    def test_wet_only_inverts_the_fall(self):
        def thds(cls):
            out = []
            for dbfs in (-14, -6):
                effect = build(cls, probe=sine(1000, dbfs))
                spec = kit.spectrum(render(effect, 48000), 1000,
                                    harmonics=10, size=4800)
                out.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
            return out

        clean = thds(Overdrive)
        fault = thds(WetOnlyOverdrive)
        self.assertLess(clean[1], clean[0])
        self.assertGreater(fault[1], fault[0])

    def test_the_other_two_faults_still_fall(self):
        """The kind gap the refutation found, kept as a test so it stays
        shut: neither `NoClipAdd` nor `NoHighPass` inverts T3."""
        def thds(cls):
            out = []
            for dbfs in (-14, -6):
                effect = build(cls, probe=sine(1000, dbfs))
                spec = kit.spectrum(render(effect, 48000), 1000,
                                    harmonics=10, size=4800)
                out.append(100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0)))
            return out

        for cls in (NoClipAdd, NoHighPass):
            values = thds(cls)
            self.assertLess(values[1], values[0], cls.__name__)

    def test_wet_only_not_on_the_macro_surface(self):
        out = kit_faults.fault_reachability(
            Overdrive, WetOnlyOverdrive,
            lambda effect: float(effect._circuit.voice[0].level),
            lambda cls: build(cls, probe=probes.silence(512, 2), frames=512),
            label="Overdrive T3 WetOnlyOverdrive")
        self.assertGreater(abs(out["target"] - out["clean"]), 0.5)


class TestOverdriveT1Span(unittest.TestCase):
    """T1's THD pair, at the Body travel and the material it is stated on."""

    def _thd(self, hz, rate=RATE, kind="sine", **options):
        frames = rate
        size = int(round(100 * rate / hz))
        probe = (sine(hz, -14, frames=frames, rate=rate) if kind == "sine"
                 else square(hz, -14, frames=frames, rate=rate))
        effect = build(rate=rate, probe=probe, frames=frames, **options)
        try:
            spec = kit.spectrum(render(effect, frames, rate=rate), hz,
                                harmonics=10, size=size)
            return 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))
        finally:
            effect.deinit()

    def test_pair_holds_at_the_default_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            low = self._thd(100, rate=rate)
            high = self._thd(1000, rate=rate)
            self.assertLess(low, high, "%d Hz: %.3f vs %.3f"
                            % (rate, low, high))

    def test_pair_reverses_at_the_bottom_of_the_body_travel(self):
        """Disconfirmed, with its cause: Body 360 lets 100 Hz into the
        clipper, and at 22.05 kHz that is enough to cross over."""
        low = self._thd(100, rate=22050, body=360.0)
        high = self._thd(1000, rate=22050, body=360.0)
        self.assertGreater(low, high)

    def test_pair_reverses_on_a_square_at_the_default(self):
        """The frozen row is stated on a tone. A square's own harmonics are
        most of the 100 Hz reading."""
        self.assertGreater(self._thd(100, kind="square"),
                           self._thd(1000, kind="square"))


class TestOverdriveSourceShapes(unittest.TestCase):
    """What an app hands an effect, not what the kit hands it."""

    def test_renders_from_a_plain_rawsample(self):
        """A bare `audiocore.RawSample` - what an app hands an effect -
        hands back its whole array at once rather than the palette's
        blocks. The input `MidSide` adapter re-blocks it. Without that
        adapter this probe renders **silence from the first pull** while
        every `ArraySource` test in this file still passes; the mechanism
        inside `audioroute.Splitter` is not established here, the
        reproduction is.
        """
        import audiocore
        # 24000 frames: the threshold this starve appears above sits
        # between 18000 and 36000 frames of source in one buffer.
        probe = array("h", sine(1000, -14, frames=12000))
        for _ in range(12000 * 2):
            probe.append(0)
        source = audiocore.RawSample(probe, sample_rate=RATE,
                                     channel_count=2)
        effect = Overdrive.create(source, RATE)
        try:
            _state, data = audiocore.get_buffer(effect.output)
            first = array("h", bytes(data))
            self.assertTrue(first, "first pull was empty")
            self.assertGreater(max(abs(v) for v in first), 1000,
                               "first pull rendered silence")
        finally:
            effect.deinit()
            source.deinit()


class TestOverdriveDisclosure(unittest.TestCase):
    def test_level_zero_at_mix_one_is_silence(self):
        """Not a wire: both the dry and the clipped leg reach the output
        through one mixer voice, and Level is that voice."""
        effect = build(probe=sine(1000, -14, frames=4800), frames=4800,
                       level=0.0)
        out = render(effect, 4800)
        self.assertFalse(any(out.data.reshape(-1)))
        effect.deinit()

    def test_mix_does_not_attenuate_the_dry(self):
        """Mix rides the clipped voltage. Halving it leaves the note where
        it was and takes half the overdrive away."""
        def thd(mix):
            effect = build(probe=sine(1000, -14), mix=mix)
            spec = kit.spectrum(render(effect, 48000), 1000, harmonics=10,
                                size=4800)
            effect.deinit()
            return 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))

        self.assertLess(thd(0.5), thd(1.0))


class NoHighPass(Overdrive):
    NAME = "Overdrive"

    def _refresh(self):
        Overdrive._refresh(self)
        self._hp.mix = 0.0


class TestOverdriveT1Fault(unittest.TestCase):
    def test_hp_off_raises_100hz_thd_at_default(self):
        def thd(cls, hz):
            effect = build(cls, probe=sine(hz, -14))
            spec = kit.spectrum(render(effect, 48000), hz, harmonics=10,
                                size=4800)
            return 100.0 * (10.0 ** (spec["values"]["thd_db"] / 20.0))

        self.assertLess(thd(Overdrive, 100), thd(Overdrive, 1000))
        self.assertGreater(thd(NoHighPass, 100), thd(Overdrive, 100))


class TestOverdriveCurveFillsTheRange(unittest.TestCase):
    """The table reaches the rails, and the generator will not emit one
    that does not ([audiocomponents#77]).

    The shipped `CURVE` used to peak at ±11381 - 35 % of int16 - because
    it held volts directly, so every entry was quantised nine times more
    coarsely than it had to be for nothing. `CURVE_VOLTS` carries the
    scale out in `post_gain` instead.
    """

    def _generator(self):
        from tools.curves import overdrive_curve
        return overdrive_curve

    def _quiet_check(self, gen):
        """`--check` with its report swallowed; returns the exit code."""
        import io
        import contextlib
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            return gen.main(["--check"])

    def test_shipped_table_reaches_both_rails(self):
        self.assertEqual((min(rebuilt.CURVE), max(rebuilt.CURVE)),
                         (-32767, 32767))

    def test_module_holds_what_the_generator_writes(self):
        self.assertEqual(self._quiet_check(self._generator()), 0)

    def test_generator_refuses_a_table_that_leaves_the_range_empty(self):
        """Planted: the pre-fix normalisation, volts straight into Q15."""
        gen = self._generator()
        keep = gen.peak_volts
        try:
            gen.peak_volts = lambda: 1.0
            self.assertLess(gen.fill(gen.table_words()), 0.95)
            self.assertNotEqual(self._quiet_check(gen), 0)
        finally:
            gen.peak_volts = keep
        self.assertEqual(self._quiet_check(gen), 0)


class TestOverdriveWetBranchReach(unittest.TestCase):
    """The kit has to reach this class's dry voice (audiocomponents#68).

    `Overdrive` sums its dry copy on the **circuit** mixer, one stage
    before the output, because a Tube Screamer's tone stack is after the
    sum. `tools/effect_measurements.mute_dry` searched the output mixer
    only, refused, and the pack that read around it was quoting mixed
    floors - about 6 dB optimistic - as wet ones. The reach lived in the
    tests-side wrapper for one round and now lives in the kit itself
    (audiocomponents#81), so both spellings below find the same voice.
    """

    def _effect(self):
        return build(probe=sine(1010, -6, frames=48000 + 2048))

    def test_kit_mute_dry_reaches_the_inner_mixer_too(self):
        effect = self._effect()
        try:
            muted = kit.mute_dry(effect)
            self.assertEqual(len(muted), 1)
            mixer, index, level = muted[0]
            self.assertIs(mixer, effect._circuit)
            self.assertEqual(index, 0)
            self.assertEqual(level, 1.0)
            self.assertEqual(mixer.voice[index].level, 0.0)
            mixer.voice[index].level = level
        finally:
            effect.deinit()

    def test_probes_mute_dry_finds_the_inner_dry_voice(self):
        effect = self._effect()
        try:
            muted = probes.mute_dry(effect)
            self.assertEqual(len(muted), 1)
            mixer, index, level = muted[0]
            self.assertIs(mixer, effect._circuit)
            self.assertEqual(index, 0)
            self.assertEqual(level, 1.0)
            self.assertEqual(mixer.voice[index].level, 0.0)
            mixer.voice[index].level = level
        finally:
            effect.deinit()

    def test_the_dilution_the_mixed_read_was_hiding(self):
        """5.6 to 6.6 dB at every cell, so T7 is stated wet."""
        for options in ({}, dict(drive=108.0, level=1.0, tone=1.0,
                                 body=360.0)):
            mixed = _alias(Overdrive, wet=False, **options)
            wet = _alias(Overdrive, wet=True, **options)
            self.assertGreater(wet - mixed, 5.0, (options, mixed, wet))
            self.assertLess(wet - mixed, 7.0, (options, mixed, wet))


class TheTierOneRowsAtEveryShippedPatch(unittest.TestCase):
    """audiocomponents#87.

    Tier 1's silence and tail rows were taken at the constructor default,
    and the default was the one state whose Symmetry was exactly 0: the
    grid could not ask for the centre of a bipolar span, so MIDI 64 was
    +0.007874 and `bias = +0.000945` reached the shaper on *every* shipped
    patch. All eight then held +56 to +85 LSB of DC that never decayed
    (patch 6: +4469, -17.3 dBFS), so `TAIL_SAMPLES = 512` was false at all
    of them and a `program_change` out of digital silence made sound. The
    default measured green throughout, which is why nothing caught it.

    So the rows walk the patches now. The centre detent was half the fix;
    patch 6 asks for asymmetry on purpose (Symmetry MIDI 108, +0.349) and
    a detent cannot help a setting that is genuinely off-centre, so it
    still stood +4461 LSB on the output for ever - audit 3 ruling (n),
    the output capacitor the class did not have.

    **The third fix round gave it one**: `DC_BLOCK_HZ`, a 30 Hz pole on
    the clip branch behind the shaper, charged at build and on any macro
    move that changes the offset. There is no exception left in these
    rows: every shipped patch is silent into silence, at the peak and not
    only at the last frame, and settles inside the declared tail.
    """

    #: `{patch: why}`. Empty since the third fix round. A patch that
    #: cannot hold this row is a defect, not a footnote.
    RED = {}

    #: The same patch is the one that never settles.
    RED_TAIL = RED

    def peaks(self):
        """`{patch: (silence_peak, tail_samples, residual, declared)}`."""
        rows = {}
        for patch in sorted(Overdrive.PATCHES):
            effect = build(probe=probes.silence(RATE, 2), patch=patch)
            quiet = render(effect, RATE)
            effect.deinit()
            probe, burst_end = probes.burst_silence(
                hz=1000.0, on_ms=200.0, total_s=1.0, dbfs=-6.0, rate=RATE,
                channels=2)
            effect = build(probe=probe, patch=patch)
            wet = render(effect, len(probe) // 2)
            declared = effect.tail_samples
            effect.deinit()
            result = kit.tail(wet, burst_end_frame=burst_end,
                              declared_tail_samples=declared)
            rows[patch] = (int(np.abs(quiet.data).max()),
                           result["values"]["tail_samples"],
                           result["values"]["residual_lsb"], declared)
        return rows

    def test_silence_in_is_silence_out_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                if patch in self.RED:
                    self.assertGreater(row[0], 0, self.RED[patch])
                    continue
                self.assertEqual(row[0], 0,
                                 "patch %d emits %d LSB into digital "
                                 "silence" % (patch, row[0]))

    def test_the_declared_tail_holds_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            _quiet, tail_samples, residual, declared = row
            with self.subTest(patch=patch, why=self.RED_TAIL.get(patch)):
                if patch in self.RED_TAIL:
                    self.assertGreater(residual, 0, self.RED_TAIL[patch])
                    continue
                self.assertEqual(residual, 0,
                                 "patch %d never returns to zero (%d LSB "
                                 "left)" % (patch, residual))
                self.assertLessEqual(tail_samples or 0, declared,
                                     "patch %d rings %s samples against a "
                                     "declared %s"
                                     % (patch, tail_samples, declared))

    def test_program_change_onto_digital_silence_stays_silent(self):
        """A patch change is a wire message and can arrive between notes.
        `Fuzz`'s did, at 329 LSB out of nothing; this one's did at 66."""
        for patch in sorted(Overdrive.PATCHES):
            effect = build(probe=probes.silence(RATE, 2), patch=0)
            before = render(effect, RATE // 2)
            effect.program_change(patch)
            after = render(effect, RATE // 2)
            effect.deinit()
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                self.assertEqual(int(np.abs(before.data).max()), 0)
                peak = int(np.abs(after.data).max())
                if patch in self.RED:
                    self.assertGreater(peak, 0, self.RED[patch])
                    continue
                self.assertEqual(peak, 0,
                                 "program_change(%d) on silence emitted %d "
                                 "LSB" % (patch, peak))


if __name__ == "__main__":
    unittest.main()
