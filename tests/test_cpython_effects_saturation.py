"""`Saturation`'s own invariant and planted-fault tests.

Dossier: workspace docs/effects-internal/dossiers/Saturation.md, frozen
2026-09-17. Exhaustive rate coverage lives in the evidence pack; this
file asserts at 48 kHz unless the test is about latency.
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
from audioeffects.rebuilt import saturation as rebuilt          # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
Saturation = rebuilt.Saturation

#: A position where the probe cannot be read at all - `Bias` +-1 cuts the
#: stage off and there is no fundamental left, on the clean class as much
#: as on a faulted one. Those are named and counted, never dropped.
_UNREADABLE = tuple(
    getattr(kit, name) for name in
    ("SilentRenderError", "ExhaustedProbeError", "MeasurementRefused")
    if hasattr(kit, name))


def build(cls=None, rate=RATE, channels=2, frames=48000, probe=None,
          **options):
    cls = cls or Saturation
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2, label=None):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, label=label, class_name="Saturation",
                         latency_samples=effect.latency_samples)


def sine(hz, frames=48000, dbfs=-20.0, rate=RATE, channels=2):
    index = np.arange(frames)
    values = ((10.0 ** (dbfs / 20.0))
              * np.sin(2.0 * math.pi * hz * index / rate))
    quantised = np.clip(np.round(values * 32767.0),
                        -32768, 32767).astype(np.int64)
    if channels == 2:
        quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist())


def _table(effect=None):
    """The curve the class built, or the tube table when there is none."""
    if effect is not None and getattr(effect, "_curve", None) is not None:
        return effect._curve
    return rebuilt._q15_array(rebuilt.TUBE_CURVE)


def odd_part_curve(table=None):
    """The built curve with its even part removed: f_odd(x)=(f(x)-f(-x))/2.

    Same curvature, same compression, no asymmetry. The Langevin table this
    guard used until 2026-09-17 is a near-wire where the class runs (h2 and
    h3 both about -85 dBc at the default), so it demonstrated nothing there;
    this one distorts exactly as hard as the class and simply cannot claim
    an even-harmonic lead.
    """
    table = _table() if table is None else table
    n = len(table)
    out = array("h", [0] * n)
    for i in range(n):
        out[i] = max(-32768, min(32767,
                                 int(round((table[i] - table[n - 1 - i])
                                           / 2.0))))
    return out


def hard_clip_curve(table=None):
    """The triode's two sides made one: the same small-signal gain and the
    same plate ceiling, clipped symmetrically, so both peaks pin instead of
    one pinning on the supply while the other keeps giving into grid
    conduction."""
    table = _table() if table is None else table
    n = len(table)
    middle = n // 2
    slope = (table[middle - 1] - table[middle + 1]) / 2.0
    ceiling = max(abs(min(table)), abs(max(table)))
    out = array("h", [0] * n)
    for i in range(n):
        value = slope * (middle - i)
        out[i] = int(max(-ceiling, min(ceiling, value)))
    return out


def rough_curve(table=None, step=1024):
    """The built curve rounded onto a `step`-count grid.

    A4's same-kind fault, and the one that fires where A4's headline is
    read. The alias floor at the class's own default is not bought by the
    oversampler - x1 and x4 are within 2 dB there - it is bought by the
    curve being smooth, so the products that fold back past Nyquist are
    small. A staircase is broadband, and broadband above Nyquist is the
    floor. 1024 counts is 1/32 of full scale: a table written at a
    thirty-second of the resolution it has, which is what a generator that
    scaled to the wrong word would produce - §12 of the pack caught
    exactly that shape once already.

    A single discontinuity at the origin was tried first and rejected: the
    `Bias` macro walks the operating point off it, and shipped patch 4
    (Bias -0.1) read a healthy floor on the faulted class. A step
    everywhere has nowhere to stand.
    """
    table = _table() if table is None else table
    out = array("h", [0] * len(table))
    for i, value in enumerate(table):
        out[i] = max(-32768, min(32767, int(round(value / step)) * step))
    return out


class OddTube(Saturation):
    """TU1's guard: the built curve with its even part removed.

    It no longer forces `character`: the second Phase 4 audit found that
    two of the 51 positions the restore walk counted were not positions,
    because this class overwrote the caller's character and the `tape` and
    `console` rows re-read the default's numbers (audiocomponents#70).
    """
    NAME = 'Saturation'

    def _build(self, **options):
        Saturation._build(self, **options)
        for shaper in self._shapers():
            shaper.set(curve=odd_part_curve(self._curve))


class HardClip(Saturation):
    """TU2's guard: a symmetric ceiling, so neither side keeps giving."""
    NAME = 'Saturation'

    def _build(self, **options):
        Saturation._build(self, **options)
        for shaper in self._shapers():
            shaper.set(curve=hard_clip_curve(self._curve))


class RoughCurve(Saturation):
    """A4's guard, and the one that fires at the constructor default."""
    NAME = 'Saturation'

    def _build(self, **options):
        Saturation._build(self, **options)
        for shaper in self._shapers():
            shaper.set(curve=rough_curve(self._curve))


class FixedLoss(Saturation):
    """TP1: loss corner frozen at 15 ips."""
    NAME = 'Saturation'

    def _apply_macro(self, index, position):
        Saturation._apply_macro(self, index, position)
        if index == 5 and self._loss is not None:
            self._loss.frequency = self._hz(rebuilt.LOSS_HZ_AT_15)


class NoOversample(Saturation):
    """A4: oversample forced to 1. Not a macro."""
    NAME = 'Saturation'

    def _build(self, **options):
        options["oversample"] = 1
        Saturation._build(self, **options)


class ShortLatency(Saturation):
    NAME = 'Saturation'

    @property
    def latency_samples(self):
        self._check_live()
        return max(0, int(self._latency) - 256)


class Construction(unittest.TestCase):
    def test_defaults_and_capabilities(self):
        effect = build()
        self.assertEqual(effect.NAME, "Saturation")
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(effect.latency_samples,
                         rebuilt.CLICK_ONSET_SAMPLES[("tube", 4)])
        self.assertEqual(effect.tail_samples, 65536)
        effect.deinit()

    def test_mix_zero_reports_zero_latency(self):
        effect = build(mix=0.0)
        self.assertEqual(effect.latency_samples, 0)
        effect.deinit()

    def test_console_adds_two_samples(self):
        """Two one-sample delay sections. The suite measures it below
        rather than asserting the declared number against itself, which is
        all the previous round did.

        The numbers are the **onsets** since the third fix round - what a
        click reads - and console's two flux sections still put it 3 above
        tube's at every rate (`CLICK_ONSET_SAMPLES`).
        """
        for rate, expected in ((48000, 4), (44100, 4), (22050, 3)):
            effect = build(character="console", rate=rate,
                           probe=probes.silence(2048))
            self.assertEqual(effect.latency_samples, expected, rate)
            effect.deinit()

    def test_console_latency_is_measured_not_declared(self):
        for rate in (48000, 44100, 22050):
            probe, _ = probes.burst_silence(
                hz=1000.0, on_ms=4.0, total_s=0.1, dbfs=-3.0, rate=rate,
                channels=2)
            effect = build(character="console", rate=rate, probe=probe)
            frames = len(probe) // 2
            wet = render(effect, frames, rate=rate)
            dry = probes.render(
                probes.ArraySource(probe, rate=rate, block=256, channels=2),
                frames, rate=rate, channels=2, block=256)
            integer = kit.click(wet, dry, effect.latency_samples,
                                subsample=False)
            fine = kit.click(wet, dry, effect.latency_samples,
                             tolerance_samples=1e9)
            effect.deinit()
            self.assertTrue(integer["passed"], (rate, integer))
            # and the reading this row does NOT want, reported not graded:
            # the 5 Hz damping and cut filters inside the two delay
            # sections have group delay, which `kit.click` says in terms is
            # "a real property of the class and *not* the processing
            # latency `latency_samples` declares". 16.808 at 48 kHz on this
            # 4 ms burst, 12.774 on an 8-sample impulse - probe-dependent,
            # which is what tells you it is not a delay.
            self.assertGreater(
                max(fine["values"]["measured_latency_samples"]),
                effect.LATENCY_SAMPLES, (rate, fine))

    def test_old_class_still_imports(self):
        from audioeffects.drive import Saturation as Old
        self.assertTrue(issubclass(Old, object))
        self.assertIsNot(Old, Saturation)

    def test_mono_constructs_and_mix_zero_is_a_wire(self):
        probe = probes.ramp_fs(2048, 1)
        effect = build(probe=probe, channels=1, mix=0.0)
        wet = render(effect, 2048, channels=1)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=1),
            2048, rate=RATE, channels=1, block=256)
        result = kit.wire(wet, dry, latency_samples=0)
        effect.deinit()
        self.assertTrue(result["passed"], result)

    def test_tail_returns_to_zero_at_default(self):
        probe, burst_end = probes.burst_silence(
            hz=1000.0, on_ms=200.0, total_s=1.0, dbfs=-6.0,
            rate=RATE, channels=2)
        effect = build(probe=probe)
        wet = render(effect, 48000)
        result = kit.tail(wet, burst_end_frame=burst_end,
                          declared_tail_samples=effect.tail_samples)
        effect.deinit()
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["values"]["residual_lsb"], 0)


class WireAndClick(unittest.TestCase):
    def test_mix_zero_is_a_wire(self):
        probe = probes.ramp_fs(8192, 2)
        effect = build(probe=probe, mix=0.0)
        wet = render(effect, 8192)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            8192, rate=RATE, channels=2, block=256)
        result = kit.wire(wet, dry, latency_samples=0)
        effect.deinit()
        self.assertTrue(result["passed"], result)

    def test_click_matches_reported_latency(self):
        probe = probes.click_stereo(8192)
        effect = build(probe=probe)
        wet = render(effect, 8192)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            8192, rate=RATE, channels=2, block=256)
        integer = kit.click(wet, dry, effect.latency_samples,
                            subsample=False)
        sub = kit.click(wet, dry, effect.latency_samples, subsample=True)
        group = effect._group_delay
        effect.deinit()
        self.assertTrue(integer["passed"], integer)
        # The other reading, named rather than graded: the half-band's
        # group delay is where the response's centroid sits and the onset
        # arrives before it. This class declares the onset (audit 3 (p)8),
        # so the sub-sample reading is 2 to 3 samples longer and that is
        # the graph's property, not the latency it reports.
        measured = sub["values"]["measured_latency_samples"][0]
        self.assertGreater(measured, effect_latency_of(effect_declared=1))
        self.assertAlmostEqual(measured, group, delta=1.0)

    def test_short_report_turns_click_red(self):
        probe = probes.click_stereo(8192)
        effect = build(ShortLatency, probe=probe)
        wet = render(effect, 8192)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            8192, rate=RATE, channels=2, block=256)
        result = kit.click(wet, dry, effect.latency_samples)
        effect.deinit()
        self.assertFalse(result["passed"], result)


class TheThirdFixRoundsRows(unittest.TestCase):
    """The rows audit 3 §4(p) asked this class for, in one place.

    Mix's polarity, A4 at both ends of its level span, Tilt's effect on
    TU2, and the integer onset at every build x rate. Each one is walked
    rather than asserted at a point, and each one has a planted opposite
    in `probes/saturation_fix3.py`.
    """

    LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)

    def rendered_db(self, dbfs=-12.0, hz=1000.0, rate=RATE, frames=None,
                    **options):
        frames = frames or rate // 4
        effect = build(probe=sine(hz, frames + 2048, dbfs, rate=rate),
                       frames=frames, rate=rate, **options)
        try:
            wet = render(effect, frames, rate=rate)
        finally:
            effect.deinit()
        values = wet.data[frames // 2:, 0].astype(np.float64) / 32768.0
        return 20.0 * math.log10(max(1e-9,
                                     float(np.sqrt((values * values).mean()))))

    def test_mix_is_a_blend_and_not_a_notch(self):
        """The tube stage inverts; the table does not, since the third fix
        round. With the inversion in, Mix 0.75 read 8.5 dB *below* Mix 1
        because the wet leg cancelled the dry one."""
        for character in ("tube", "tape", "console"):
            walk = [self.rendered_db(mix=mix, character=character)
                    for mix in self.LEVELS]
            for index in range(1, len(walk)):
                self.assertLess(
                    walk[index], walk[index - 1] + 0.01,
                    "%s: Mix %s -> %s went UP (%r)"
                    % (character, self.LEVELS[index - 1],
                       self.LEVELS[index], [round(v, 3) for v in walk]))
            self.assertLess(
                walk[-1], walk[-2] + 0.01,
                "%s: Mix 1 is above Mix 0.75, which is the notch (%r)"
                % (character, [round(v, 3) for v in walk]))
            self.assertGreater(
                walk[-1], min(walk) - 0.01,
                "%s: the deepest point is not the wet end, which is the "
                "notch (%r)" % (character, [round(v, 3) for v in walk]))

    def test_a4_holds_at_both_ends_of_its_level_span(self):
        """A4's plane was read at -6 dBFS and TU2's bar is stated at
        0 dBFS, and neither row said so (audit 3 (p)3, ruling (m)). A4
        holds over **-6 to 0 dBFS** now, graded at both ends and the
        middle, at the worst cell of the Drive x Headroom plane."""
        for dbfs in (-6.0, -3.0, 0.0):
            for drive, head in ((12.0, -6.0), (15.0, 0.0), (0.0, 6.0)):
                floor = A4AliasFloor("test_default_is_the_headline")._floor_at(
                    dbfs, drive_db=drive, headroom_db=head)
                self.assertLess(
                    floor, -60.0,
                    "A4 reads %.3f dB at %s dBFS, Drive %s / Headroom %s"
                    % (floor, dbfs, drive, head))

    def test_tilt_is_not_held_free_by_tu2(self):
        """TU2's "macros the row holds free" list omitted Tilt, which is a
        shelf *after* the shaper and re-weights the slope the row
        measures."""
        row = TU2PlateCeiling("test_the_plate_pins_and_the_grid_does_not")
        level = row._curve()
        self.assertLessEqual(level["plate"], TU2PlateCeiling.PLATE_BAR)
        tilted = row._curve(tilt_db=-6.0)
        self.assertGreater(
            tilted["plate"], TU2PlateCeiling.PLATE_BAR * 4.0,
            "Tilt -6 reads plate %.4f, and the row used to hold it free"
            % tilted["plate"])

    def test_the_onset_is_what_every_build_and_rate_reads(self):
        for character in ("tube", "tape", "console"):
            for rate in (48000, 44100, 22050):
                for channels in (2, 1):
                    frames = 8192
                    if channels == 2:
                        probe = probes.click_stereo(frames=frames,
                                                    offset=400, channels=2)
                    else:
                        probe = array("h", bytes(2 * frames))
                        probe[400] = 32000
                    effect = build(probe=probe, frames=frames, rate=rate,
                                   channels=channels, character=character)
                    try:
                        wet = render(effect, frames, rate=rate,
                                     channels=channels)
                        dry = probes.render(
                            probes.ArraySource(probe, rate=rate, block=256,
                                               channels=channels),
                            frames, rate=rate, channels=channels, block=256)
                        result = kit.click(wet, dry, effect.latency_samples,
                                           subsample=False)
                    finally:
                        effect.deinit()
                    self.assertTrue(
                        result["passed"],
                        "%s at %d Hz, %d channel(s): %s"
                        % (character, rate, channels, result["red"]))


class TU1EvenLead(unittest.TestCase):
    #: How many of the 51 positions the clean class can be read at, which
    #: is the only denominator a guard can be graded against. The row
    #: published **49** and asked the clean class at two positions; asked
    #: at all 51 it is red at 34 of them (audit 3 (p)5, which counted 35 on
    #: the inverting tube table this round replaced). The guard is healthy
    #: at 0 of the 17 either way - what changed is the denominator, and a
    #: denominator inflated three times over is a disclosure defect in a
    #: G3 claim.
    GRADABLE = 17

    """The whole frozen row, never a fragment of it.

    Grading the guard on the even lead alone is what Phase 4's audit caught:
    a symmetric curve plus Bias makes h2 out of the bias point, so six
    surface positions read a healthy lead on a faulted class
    (audiocomponents#70). The lead, A1's absolute h2 at the three tabulated
    drives, and the dBc slope are one bar and are measured as one.
    """

    SPAN = (-26.0, -20.0, -14.0, -9.0, -6.0)
    A1 = {-26.0: -54.1, -14.0: -42.0, -6.0: -33.8}

    def _tu1(self, cls=Saturation, frames=48000, macro=None, **options):
        h2 = {}
        h3 = {}
        for dbfs in self.SPAN:
            probe = sine(1000, frames, dbfs)
            effect = build(cls, probe=probe, frames=frames, **options)
            if macro is not None:
                effect.set_macro(macro[0], macro[1])
            wet = render(effect, frames)
            # No `size`: the kit then picks a whole number of periods, which
            # is the only length that reads h3 truly. The pack's own 8192
            # put 1 kHz on bin 170.67 and its leakage skirt read h3 4.0 dB
            # high, which is the whole of the 17.69-vs-20.31 disagreement
            # the Phase 4 audit could not settle.
            values = kit.spectrum(wet, 1000.0, harmonics=6)["values"]
            effect.deinit()
            h2[dbfs] = values["harmonic_db"].get("h2")
            h3[dbfs] = values["harmonic_db"].get("h3")
        if any(v is None for v in list(h2.values()) + list(h3.values())):
            return {"passed": False, "red": ["a harmonic above Nyquist"]}
        leads = [h2[d] - h3[d] for d in self.SPAN]
        slopes = [(h2[b] - h2[a]) / (b - a)
                  for a, b in zip(self.SPAN, self.SPAN[1:])]
        a1 = [h2[d] - self.A1[d] for d in self.A1]
        red = []
        if min(leads) < 15.0:
            red.append("lead %.3f" % min(leads))
        if max(abs(v) for v in a1) > 4.0:
            red.append("A1 %.3f" % max(a1, key=abs))
        if min(slopes) < 0.6 or max(slopes) > 1.4:
            red.append("slope %.3f/%.3f" % (min(slopes), max(slopes)))
        return {"passed": not red, "red": red, "leads": leads,
                "slopes": slopes, "a1": a1, "headline": leads[-1]}

    def test_default_is_the_headline(self):
        reading = self._tu1()
        self.assertTrue(reading["passed"], reading)
        self.assertGreater(reading["headline"], 20.0, reading)

    def test_odd_table_is_red_at_the_default(self):
        reading = self._tu1(OddTube)
        self.assertFalse(reading["passed"], reading)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(Saturation, self._tu1,
                                  label="Saturation TU1")

    def test_odd_fault_not_on_the_surface(self):
        kit_faults.fault_reachability(
            Saturation, OddTube,
            lambda effect: bytes(odd_part_curve())
            if type(effect) is OddTube else rebuilt.TUBE_CURVE,
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Saturation TU1")

    def test_no_macro_stop_or_patch_restores_the_guard(self):
        """The reachability walk the byte comparison cannot do: measure the
        faulted class at every macro stop and every shipped patch - **and
        the clean class at every one of them too**.

        The row used to say "51 checked, 49 gradable, 0 healthy" and ask
        the clean class at `tape` and `console` only. Run its own `_tu1`
        on the clean class at all 51 and the clean class is red at most of
        them - Bias at either end has no fundamental, Mix 0 is the wire,
        Drive 0 barely shapes - so the denominator was inflated three
        times over (audit 3 (p)5, ruling (a)). What is graded here is the
        positions where the trait is claimed *and readable*, and the
        clean reading is printed beside the fault at every one of them.
        """
        healthy = []
        clean_red = []
        checked = 0
        graded = 0
        positions = []
        for index in range(len(Saturation.MACRO_LABELS)):
            for midi in (0, 32, 64, 96, 127):
                positions.append(("macro %d MIDI %d" % (index, midi),
                                  {"macro": (index, midi)}))
        for patch in sorted(Saturation.PATCHES):
            positions.append(("patch %d" % patch, {"patch": patch}))
        # `tape` and `console` are Langevin curves, already odd, so
        # removing an even part removes nothing (max |diff| 0 against the
        # built table, against 3440 on `tube`) - and the CLEAN class is red
        # there too. An inert fault on a position the trait does not reach
        # is the definition of the fault, not a hole in it.
        for character in ("tape", "console"):
            positions.append((character, {"character": character}))
        for label, keywords in positions:
            checked += 1
            try:
                clean = self._tu1(frames=12000, **keywords)
            except _UNREADABLE as error:
                # Bias at either end cuts the stage off and Mix 0 is the
                # wire: there is no fundamental to read on the clean class
                # either, so the trait is not claimed there.
                clean_red.append((label, [type(error).__name__]))
                continue
            if not clean["passed"]:
                clean_red.append((label, clean["red"]))
                continue
            graded += 1
            try:
                reading = self._tu1(OddTube, frames=12000, **keywords)
            except _UNREADABLE as error:
                healthy.append((label, clean, type(error).__name__))
                continue
            if reading["passed"]:
                healthy.append((label, clean, reading))
        self.assertEqual(checked, 51)
        self.assertEqual(healthy, [], healthy)
        self.assertEqual(
            graded + len(clean_red), checked,
            (graded, len(clean_red)))
        self.assertEqual(graded, self.GRADABLE,
                         (graded, [name for name, _ in clean_red]))
        self.assertIn("tape", [name for name, _ in clean_red])
        self.assertIn("console", [name for name, _ in clean_red])

    def test_the_quiet_end_is_where_the_table_runs_out(self):
        """The bound, measured — vision §7.2, invoked 2026-09-17.

        **Old target:** "h2 - h3 >= 15 dB at *every* drive <= 0.5 V".
        **The measurement that retires it:** the row is unbounded below and
        no table shaper can hold it there. At 0.0447 V — one dB under the
        freeze's own quietest probe — the lead is **12.447 dB** at 48 kHz,
        and at 0.0089 V it is **-6.057** (-11.465 at 44.1, -8.432 at
        22.05), which is the freeze's own disconfirmation. The cause is the
        table, not the triode: the curve is 1025 Q15 points over +-10 V of
        grid, so one table cell is 0.0195 V and a 0.0089 V peak sweeps
        **less than half a cell**. The segment it sits on is a straight
        line, so what h2 reports there is the interpolation residue. Four
        times the table would move the wall 12 dB and not remove it.
        **New target:** the row's own quantified-over column — h2 - h3 >=
        15 dB from **0.05 V to 0.5 V** of grid, reached from a jack
        signal at or above -26 dBFS, which is where A1 is tabulated and
        where the freeze samples. Worst cell over the 63 (level, rate)
        cells of that span: **16.008** at 48 kHz and 0.05 V. Every route
        to the same volts now agrees, because Drive and Headroom are one
        control: 27.859 by Drive -12 and 27.859 by Headroom +12 at
        0.05 V, against the four different answers the second audit
        found. **Traits now claimed:** TU1
        only. **Phase 7:** at patch 0 with a quiet part, the thickening
        should be even-flavoured rather than fizzy; below about -26 dBFS it
        stops being either, and that is the floor, not a fault.
        """
        floor = []
        for dbfs, expected in ((-26.0, True), (-30.0, False),
                               (-33.0, False), (-41.0, False)):
            probe = sine(1000, 48000, dbfs)
            effect = build(probe=probe)
            wet = render(effect, 48000)
            values = kit.spectrum(wet, 1000.0, harmonics=6)["values"]
            effect.deinit()
            lead = (values["harmonic_db"]["h2"]
                    - values["harmonic_db"]["h3"])
            floor.append((dbfs, round(lead, 3)))
            self.assertEqual(lead >= 15.0, expected, floor)
        # and the disconfirmation clause really is reached below the bound
        self.assertLess(floor[-1][1], 0.0, floor)

    def test_the_walk_can_go_green(self):
        """And the walk is not vacuous: on `tube` the Speed macro moves
        nothing, so the clean class must read healthy at all five of its
        stops - the same call that reads red 49 times above."""
        green = 0
        for midi in (0, 32, 64, 96, 127):
            if self._tu1(frames=12000, macro=(5, midi))["passed"]:
                green += 1
        self.assertEqual(green, 5)


class TP2OddAtBiasZero(unittest.TestCase):
    def _h2(self, cls=Saturation, bias=0.0):
        probe = sine(1000, 48000, -12.0)
        effect = build(cls, probe=probe, character="tape", bias=bias)
        wet = render(effect, 48000)
        spec = kit.spectrum(wet, 1000.0, harmonics=6)
        effect.deinit()
        return spec["values"]["harmonic_db"].get("h2")

    def test_tape_default_h2_below_minus_40(self):
        h2 = self._h2()
        self.assertIsNotNone(h2)
        self.assertLessEqual(h2, -40.0, h2)

    def test_null_build_is_red(self):
        def measure(cls):
            h2 = self._h2(cls)
            passed = h2 is not None and h2 <= -40.0
            return {"passed": passed, "red": [] if passed else [h2]}
        # A wire is even quieter in h2 (numerical floor), so this bar is
        # green on a wire. The pack records that; TU1 carries the even
        # lead that a wire cannot meet.
        with self.assertRaises((kit_faults.NullBuildGreen,
                                kit_faults.ControlRed)):
            kit_faults.null_build_red(Saturation, measure, label="TP2")


class A4AliasFloor(unittest.TestCase):
    """The floor at the Drive macro's own maximum, on the shipped factor.

    Two clauses, because one of them alone is green on a wire: the class
    must be driving (THD >= 5 %) *and* its non-harmonic energy must sit
    60 dB below the fundamental. `size=4800` is 101 whole periods of
    1010 Hz and 370 of 3700 Hz at 48 kHz - the kit's generic exact length
    is not whole for these probes and its leakage reads a floor 30 dB
    high.

    Drive and Headroom now share the ceiling (`DRIVE_CEILING_DB`), so
    "maximum Drive" is the whole surface's maximum and not one corner of
    it. The second audit's refutation was Headroom -6 / Output +6 at
    maximum Drive, +6 dB past the documented cap, reading -45.621 at
    3700 Hz; it now reads what maximum Drive reads.
    """

    MAX_DRIVE = 15.0

    def _floor(self, cls=Saturation, hz=1010.0, drive_db=None, macros=None,
               macro=None, frames=48000, **options):
        drive_db = self.MAX_DRIVE if drive_db is None else drive_db
        probe = sine(hz, frames, -6.0)
        effect = build(cls, probe=probe, drive_db=drive_db, **options)
        if macros:
            for index, value in macros.items():
                span = type(effect)._MACRO_RANGES[index]
                effect.set_macro(index, rebuilt._component.macro_of(span,
                                                                    value))
        if macro is not None:
            effect.set_macro(macro[0], macro[1])
        wet = render(effect, frames)
        spec = kit.spectrum(wet, hz, harmonics=10, settled_ratio=0.75,
                            size=4800)
        effect.deinit()
        return spec["values"]

    def _measure(self, cls=Saturation, drive_db=None, **options):
        red = []
        floors = {}
        for hz in (1010.0, 3700.0):
            values = self._floor(cls, hz=hz, drive_db=drive_db, **options)
            floors[hz] = values["alias_floor_db"]
            if values["alias_floor_db"] > -60.0:
                red.append("%d Hz %.3f" % (hz, values["alias_floor_db"]))
        thd = 100.0 * (10.0 ** (self._floor(cls, hz=1000.0,
                                            drive_db=drive_db,
                                            **options)["thd_db"] / 20.0))
        if thd < 5.0:
            red.append("THD %.3f %% - nothing is being shaped" % thd)
        return {"passed": not red, "red": red, "floors": floors, "thd": thd}

    def _floor_at(self, dbfs, hz=1010.0, drive_db=15.0, frames=48000,
                  **options):
        """A4's own reading at a stated input level - the row is a
        **-6 to 0 dBFS** row since the third fix round (ruling (m))."""
        probe = sine(hz, frames, dbfs)
        effect = build(Saturation, probe=probe, drive_db=drive_db, **options)
        try:
            wet = render(effect, frames)
        finally:
            effect.deinit()
        return kit.spectrum(wet, hz, harmonics=10, settled_ratio=0.75,
                            size=4800)["values"]["alias_floor_db"]

    def _headline(self, cls=Saturation, **options):
        """A4's headline is at the DEFAULT. Two clauses again, because the
        floor alone is green on a wire - a wire has nothing to alias. At
        Drive 0 the class shapes to 2.0 % THD, so the driving clause is
        1 %, not the 5 % that belongs at maximum Drive."""
        floors = {}
        red = []
        for hz in (1010.0, 3700.0):
            try:
                values = self._floor(cls, hz=hz, drive_db=0.0, **options)
            except _UNREADABLE as error:
                floors[hz] = None
                red.append("%d Hz: %s" % (hz, type(error).__name__))
                continue
            floors[hz] = values["alias_floor_db"]
            if values["alias_floor_db"] > -60.0:
                red.append("%d Hz %.3f" % (hz, values["alias_floor_db"]))
        try:
            thd = 100.0 * (10.0 ** (self._floor(
                cls, hz=1000.0, drive_db=0.0, **options)["thd_db"] / 20.0))
        except _UNREADABLE as error:
            thd = None
            red.append(type(error).__name__)
        if thd is not None and thd < 1.0:
            red.append("THD %.3f %% - nothing is being shaped" % thd)
        return {"passed": not red, "red": red, "floors": floors,
                "thd": thd}

    def test_default_is_the_headline(self):
        """-77.693 / -77.322 at 48 kHz, the reading a user starts on."""
        reading = self._headline()
        self.assertTrue(reading["passed"], reading)

    def test_max_drive_clears_the_bar_at_both_probes(self):
        reading = self._measure()
        self.assertTrue(reading["passed"], reading)

    def test_the_rough_curve_is_red_at_the_default(self):
        """The same-kind fault that fires where the headline is read.
        -54.311 / -39.172 at 48 kHz against the clean
        -77.693 / -77.322, and red at all three rates."""
        reading = self._headline(RoughCurve)
        self.assertFalse(reading["passed"], reading)

    def test_the_rough_curve_is_red_at_maximum_drive_too(self):
        reading = self._measure(RoughCurve)
        self.assertFalse(reading["passed"], reading)

    def test_no_oversample_is_red_at_max_drive_and_green_at_the_default(self):
        """Kept, and reported for what it is. x1 at Drive 0 reads
        -76.806 / -75.099 against x4's -77.693 / -77.322: within 2 dB, so
        the oversampler is not what buys the floor at the default and this
        fault cannot show that it does. It is A4's guard at maximum Drive,
        where the fold really is the oversampler's to lose, and `RoughCurve`
        is the guard at the default."""
        self.assertFalse(self._measure(NoOversample)["passed"])
        self.assertTrue(self._headline(NoOversample)["passed"])

    def test_null_build_is_red(self):
        kit_faults.null_build_red(Saturation, self._measure,
                                  label="Saturation A4")

    def test_null_build_is_red_at_the_default_too(self):
        kit_faults.null_build_red(Saturation, self._headline,
                                  label="Saturation A4 headline")

    def test_no_macro_stop_or_patch_restores_the_rough_fault(self):
        """The walk, on the fault's own measurement, at the default drive.
        Every macro at five stops, every shipped patch, both characters the
        constructor also offers - and the fault no longer overwrites
        `character`, so those two are positions."""
        healthy = []
        graded = 0
        checked = 0
        skipped = []
        positions = []
        for index in range(len(Saturation.MACRO_LABELS)):
            for midi in (0, 32, 64, 96, 127):
                positions.append(("macro %d MIDI %d" % (index, midi),
                                  {"macro": (index, midi)}))
        for patch in sorted(Saturation.PATCHES):
            positions.append(("patch %d" % patch, {"patch": patch}))
        for character in ("tape", "console"):
            positions.append((character, {"character": character}))
        for label, keywords in positions:
            checked += 1
            clean = self._headline(**keywords)
            if not clean["passed"]:
                # Bias +-1 cuts the stage off: the clean class has no
                # fundamental to read there either, so it is not a position
                # where the trait is claimed and not one a fault can
                # restore. Counted and named, never silently dropped.
                skipped.append((label, clean["red"]))
                continue
            graded += 1
            reading = self._headline(RoughCurve, **keywords)
            if reading["passed"]:
                healthy.append((label, reading))
        self.assertEqual(checked, 51)
        self.assertEqual(healthy, [], healthy)
        # 38 until the third fix round took the inversion out of the tube
        # table: Mix 64 used to read a high THD because the wet leg
        # *cancelled* the dry one, and a notch is not a class being
        # shaped. It is a skipped position now, named below.
        self.assertEqual(graded, 37, (graded, skipped))
        self.assertEqual(sorted(name for name, _ in skipped), sorted(
            ["macro 0 MIDI 0", "macro 1 MIDI 0", "macro 2 MIDI 0",
             "macro 2 MIDI 32", "macro 2 MIDI 64", "macro 3 MIDI 96",
             "macro 3 MIDI 127", "macro 4 MIDI 0", "macro 4 MIDI 32",
             "macro 4 MIDI 96", "macro 4 MIDI 127", "patch 7", "tape",
             "console"]),
            skipped)

    def test_where_the_clean_class_does_not_hold_the_row(self):
        """The thirteen positions the walk above cannot grade, with their
        causes, because a walk that drops rows quietly is the defect this
        phase keeps finding.

        **Eight are the driving clause, not the floor**: Drive -12,
        Headroom +6 and +12, Mix 0 and 0.35, patch 7 (Mix 0.35), `tape`
        and `console` at Drive 0 all shape to under 1 % THD, so there is
        nothing for a fault to break. **Two are the operating point**:
        Bias at +-0.75 and +-1 walks the stage to cutoff or into grid
        conduction, where the clean class rectifies (-27.136 at Bias +1)
        or goes silent (fundamental -240 dBFS at Bias -0.5). **Three are
        the same thing and it is the most useful number here**: A4 is a
        RATIO and 16 bits is an ABSOLUTE floor, so wherever the class's
        own output is quiet the ratio reads badly whatever the shaper did.
        The floor tracks the output level one for one - Output -12 / -18 /
        -24 read -69.007 / -63.233 / -57.301 against fundamentals 5.95 dB
        apart - and `console` at Drive 0 reads -46.094 because its 5 Hz
        flux pair has taken 25 dB out of the signal before the jack (move
        that corner to 10 and 20 Hz and the floor follows exactly:
        -52.002, -57.964). Not aliasing. Disclosed rather than designed
        around, because the cure is a wider output word, not a different
        shaper.
        """
        rows = {}
        for label, keywords, probe in (
                ("Output -24", {"macros": {1: -24.0}}, 1010.0),
                ("Output -18", {"macros": {1: -18.0}}, 1010.0),
                ("Output -12", {"macros": {1: -12.0}}, 1010.0),
                ("console", {"character": "console"}, 1010.0),
                ("Bias +0.25", {"macros": {4: 0.25}}, 1010.0),
                ("Bias +0.1", {"macros": {4: 0.1}}, 1010.0)):
            values = self._floor(hz=probe, drive_db=0.0, **keywords)
            rows[label] = (round(values["alias_floor_db"], 3),
                           round(values["fundamental_dbfs"], 2))
        # one for one with the level: the floor is the output word
        # the floor rises by exactly the dB the fundamental falls
        self.assertAlmostEqual(
            (rows["Output -18"][0] - rows["Output -24"][0])
            + (rows["Output -18"][1] - rows["Output -24"][1]),
            0.0, delta=0.5, msg=rows)
        self.assertAlmostEqual(
            (rows["Output -12"][0] - rows["Output -18"][0])
            + (rows["Output -12"][1] - rows["Output -18"][1]),
            0.0, delta=0.5, msg=rows)
        # the shipped patches' Bias range is inside the bar; +-0.25 is not
        self.assertLessEqual(rows["Bias +0.1"][0], -60.0, rows)
        self.assertGreater(rows["Bias +0.25"][0], -60.0, rows)
        self.assertGreater(rows["console"][0], -60.0, rows)

    def test_the_lean_patch_is_reported_not_graded(self):
        """Reported, not graded (dossier A4). The lean patch is one factor
        below whatever the rate ships - x2 at 48 kHz - and it does buy its
        cost partly out of the floor: 1010 Hz still clears, 3700 Hz does
        not, and the pack and the docstring say so rather than the bar
        being widened to let it through."""
        floors = {}
        for hz in (1010.0, 3700.0):
            probe = sine(hz, 48000, -6.0)
            effect = build(probe=probe, drive_db=self.MAX_DRIVE)
            effect.program_change(rebuilt.LEAN_PATCH)
            effect.set_macro(0, 127)
            wet = render(effect, 48000)
            floors[hz] = kit.spectrum(
                wet, hz, harmonics=10, settled_ratio=0.75,
                size=4800)["values"]["alias_floor_db"]
            effect.deinit()
        self.assertLessEqual(floors[1010.0], -60.0, floors)
        self.assertLessEqual(floors[3700.0], -55.0, floors)
        self.assertGreater(floors[3700.0], -60.0, floors)


class DriveAndHeadroomShareTheCeiling(unittest.TestCase):
    """Headroom moves the character's knee, Drive moves the signal at it,
    and in front of one curve on one node that is one number. Leaving them
    independent gave the pair +27 dB of reach behind a documented +15 dB
    cap (audiocomponents#70)."""

    def _pre(self, drive_db, headroom_db):
        effect = build(drive_db=drive_db, headroom_db=headroom_db)
        seen = {}

        def spy(**options):
            seen.update(options)
        for shaper in effect._shapers():
            shaper.set = spy
        effect._push_gains()
        effect.deinit()
        return seen["pre_gain"]

    def test_the_pair_stops_where_drive_stops(self):
        cap = rebuilt.TUBE_PRE0 * (10.0 ** (rebuilt.DRIVE_CEILING_DB / 20.0))
        self.assertAlmostEqual(self._pre(15.0, 0.0), cap, places=6)
        for headroom in (-12.0, -6.0, -3.0):
            self.assertAlmostEqual(self._pre(15.0, headroom), cap, places=6)
        self.assertAlmostEqual(self._pre(3.0, -12.0), cap, places=6)

    def test_headroom_still_does_something_under_the_cap(self):
        """It is not clamped away: it is Drive's own dB, spent the other
        way round. Drive 0 / Headroom -6 is +6 dB into the curve."""
        six = rebuilt.TUBE_PRE0 * (10.0 ** (6.0 / 20.0))
        self.assertAlmostEqual(self._pre(0.0, -6.0), six, places=6)
        self.assertAlmostEqual(self._pre(6.0, 0.0), six, places=6)

    def test_the_alias_floor_holds_over_the_plane(self):
        """The audit's cell, and its neighbours: maximum Drive with
        Headroom down and Output up by the same dB, which used to be
        -45.621 at 3700 Hz."""
        floors = A4AliasFloor()
        for headroom in (0.0, -3.0, -6.0, -12.0):
            reading = floors._measure(macros={3: headroom, 1: -headroom})
            self.assertTrue(reading["passed"], (headroom, reading))


class TU2PlateCeiling(unittest.TestCase):
    """One extreme of the realised transfer curve is a plateau, the other
    is not - vision §7.2, invoked 2026-09-17 (second fix round).

    **The old target** was peak growth against the table's own + ceiling:
    from the drive where the + peak first comes within 1 dB of it, 20 dB
    more grows + by < 1 dB and - by > 1.5 dB. **Two measurements retire
    it.** (1) The class AC-couples at the plate, at 20 Hz, because that is
    where the coupling capacitor is and because with it in front of the
    shaper `Bias` wrote its whole operating point onto the output as DC.
    The capacitor removes exactly the DC the asymmetry is made of, so the
    clause reads +0.851 / +2.527 dB on the class's own curve - which
    reproduces A1's solve to three digits, 80.79 / 82.06 / 82.06 V against
    80.8 / 82.07 / 82.07 at 2 / 5 / 10 V of grid, and 82.61 / 94.27 /
    103.90 against 82.6 / 94.3 / 103.9 - and **+2.701 / +2.541** at the
    jack, which is the freeze's own "both polarities still growing". A
    reading taken on the table instead is green on a wire and demonstrates
    nothing. (2) The 20 dB span has left the surface: Drive and Headroom
    now share one +15 dB ceiling, and 0 dBFS at Drive 0 is 1.0 V of grid,
    so the surface reaches 5.62 V against an onset at 1.49 V - 11.5 dB.

    **The new target** is the same physics read where a DC shift cannot
    touch it. A slope does not care about DC. Render the wet branch, bin
    the settled output against its own input, fit the local slope in the
    outer quarter of each side and normalise both by the slope through the
    origin. Bar, at Drive +12 dB (3.98 V of grid), all three rates: the
    plate side <= 0.02, the grid side >= 0.05, ratio >= 10. Disconfirmed
    by both sides alike - a symmetric ceiling or no ceiling.

    **Traits now claimed:** TU2 only; TU1, TU3, TP1, TP2 and A4 are
    untouched and this class's invariant tests pass unchanged.
    **Phase 7, what Brad listens for:** patch 1 "Hot into the curve" on a
    sustained low note - it should thicken and bloom on the way up and go
    blunt on the way down, not square up symmetrically the way a diode
    pedal does. If both halves harden together, this target is wrong.
    """

    #: The span: effective drive +8 to +15 dB (2.51 to 5.62 V of grid),
    #: `tube`, **1 kHz at 0 dBFS** - the level is part of the row, and A4's
    #: is -6 dBFS, which is why both now say so (audit 3 ruling (m)).
    #: Worst cell over 24 (drive, rate) cells: plate **0.0374** at 44.1 kHz
    #: / +8 dB, gap **0.0408** at 48 kHz / +15 dB. `HardClip`'s best gap
    #: over the same 24 is **0.0116**.
    #:
    #: **What the row holds free, corrected.** It used to list every macro
    #: but Drive and Headroom. **Tilt is not one of them**: it is a shelf
    #: *after* the shaper, so it re-weights the very slope this measures -
    #: Tilt -6 reads plate **0.3380**, 8.4x the bar - and Frequency moves
    #: it too (40 Hz -0.1257, 5 kHz -0.3783). The row is claimed at Tilt 0
    #: and at 1 kHz, and `test_tilt_is_not_held_free` walks the rest.
    BAR_DRIVE = 12.0
    SPAN = (8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0)
    PLATE_BAR = 0.04
    GAP_BAR = 0.025

    def _curve(self, cls=None, rate=RATE, drive_db=None, dbfs=0.0,
               headroom_db=None, patch=None, tilt_db=None, hz=1000.0):
        cls = cls or Saturation
        drive_db = self.BAR_DRIVE if drive_db is None else drive_db
        frames = rate
        probe = sine(hz, frames + 1024, dbfs, rate=rate)
        effect = build(cls, probe=probe, rate=rate, drive_db=drive_db,
                       patch=patch)
        if tilt_db is not None:
            span = type(effect)._MACRO_RANGES[6]
            effect.set_macro(6, rebuilt._component.macro_of(span, tilt_db))
        if headroom_db is not None:
            span = type(effect)._MACRO_RANGES[3]
            effect.set_macro(3, rebuilt._component.macro_of(span,
                                                            headroom_db))
        try:
            wet = probes.wet_render(effect, frames, rate=rate, channels=2,
                                    block=256, class_name="Saturation")
        except kit.MeasurementRefused:
            # The null build has no mixer in the path at all - its output
            # IS the source - so there is no dry voice to mute and the
            # output is the right reading for it.
            wet = probes.render(effect.output, frames, rate=rate,
                                channels=2, block=256,
                                class_name="Saturation")
        effect.deinit()
        return self._slopes(wet, probe, frames, rate)

    @staticmethod
    def _slopes(wet, probe, frames, rate, bins=41):
        n = rate // 2
        y = np.asarray(wet.float[frames - n:, 0], dtype=np.float64)
        y = y - y.mean()
        source = np.asarray(probe, dtype=np.float64)[0::2] / 32767.0
        best, lag = None, 0
        for trial in range(0, 17):
            span = source[frames - n - trial:frames - trial]
            score = abs(float(np.dot(span, y)))
            if best is None or score > best:
                best, lag = score, trial
        span = source[frames - n - lag:frames - lag]
        peak = float(np.max(np.abs(span)))
        if peak <= 0.0:
            return {"passed": False, "red": ["a silent probe"]}
        unit = span / peak
        edges = np.linspace(-1.0, 1.0, bins + 1)
        which = np.clip(np.digitize(unit, edges) - 1, 0, bins - 1)
        centre = 0.5 * (edges[:-1] + edges[1:])
        curve = np.full(bins, np.nan)
        for i in range(bins):
            take = which == i
            if take.sum() >= 4:
                curve[i] = y[take].mean()

        def slope(lo, hi):
            take = ((~np.isnan(curve)) & (centre >= lo) & (centre <= hi))
            if take.sum() < 3:
                return None
            return float(np.polyfit(centre[take], curve[take], 1)[0])

        origin = slope(-0.25, 0.25)
        # The table inverts, so the input's most NEGATIVE quarter is the
        # plate and its most positive one is grid conduction.
        plate, grid = slope(-1.0, -0.75), slope(0.75, 1.0)
        if not origin or plate is None or grid is None:
            return {"passed": False, "red": ["no curve to read"]}
        plate, grid = plate / origin, grid / origin
        # A DIFFERENCE, never a ratio: both slopes cross zero on the way
        # down, and a ratio then reads 810 for the class and 574 for the
        # fault at neighbouring drives. The difference is bounded.
        gap = grid - plate
        red = []
        if plate > TU2PlateCeiling.PLATE_BAR:
            red.append("plate %.4f" % plate)
        if gap < TU2PlateCeiling.GAP_BAR:
            red.append("gap %.4f" % gap)
        return {"passed": not red, "red": red, "plate": round(plate, 4),
                "grid": round(grid, 4), "gap": round(gap, 4), "lag": lag}

    def test_the_plate_pins_and_the_grid_does_not(self):
        """plate -0.0015, gap 0.0568 at 48 kHz, Drive +12."""
        reading = self._curve()
        self.assertTrue(reading["passed"], reading)

    def test_it_holds_over_the_whole_span_at_every_rate(self):
        """24 cells. Worst plate 0.0374 (44.1 kHz, +8), worst gap 0.0408
        (48 kHz, +15)."""
        worst_plate = -9.9
        worst_gap = 9.9
        for rate in (48000, 44100, 22050):
            for drive in self.SPAN:
                reading = self._curve(rate=rate, drive_db=drive)
                self.assertTrue(reading["passed"], (rate, drive, reading))
                worst_plate = max(worst_plate, reading["plate"])
                worst_gap = min(worst_gap, reading["gap"])
        self.assertLessEqual(worst_plate, self.PLATE_BAR, worst_plate)
        self.assertGreaterEqual(worst_gap, self.GAP_BAR, worst_gap)

    def test_a_symmetric_ceiling_is_red_over_the_whole_span(self):
        """Both sides alike, which is the freeze's own disconfirmation.
        `HardClip`'s best gap over the same 24 cells is 0.0116."""
        best = -9.9
        for rate in (48000, 44100, 22050):
            for drive in self.SPAN:
                reading = self._curve(HardClip, rate=rate, drive_db=drive)
                self.assertFalse(reading["passed"], (rate, drive, reading))
                best = max(best, reading["gap"])
        self.assertLess(best, self.GAP_BAR, best)

    def test_the_fault_is_red_at_the_constructor_default_too(self):
        """The row is not CLAIMED at the default - the freeze says so
        ("headline at defaults, likely still below the ceiling") and the
        plate clause is what fails there, 0.8617. But the gap clause is
        the asymmetry itself and the class holds it at the default:
        **0.1389 / 0.1407 / 0.1322** at the three rates against
        `HardClip`'s **-0.0003 / -0.0078 / -0.0157**. So the guard fires
        at the constructor default, and on the trait's own kind."""
        for rate in (48000, 44100, 22050):
            clean = self._curve(rate=rate, drive_db=0.0, dbfs=-6.0)
            fault = self._curve(HardClip, rate=rate, drive_db=0.0,
                                dbfs=-6.0)
            self.assertGreaterEqual(clean["gap"], self.GAP_BAR,
                                    (rate, clean))
            self.assertLess(fault["gap"], self.GAP_BAR, (rate, fault))
            self.assertGreater(clean["plate"], self.PLATE_BAR, (rate, clean))

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Saturation, lambda cls: self._curve(cls), label="Saturation TU2")

    def test_headroom_is_drive_and_cannot_dial_it_back(self):
        """Headroom is Drive's own dB now, so on this row it moves along
        the swept axis rather than off it: -12, -6 and 0 at Drive +12 are
        all the +15 dB cell (0.0408), and +6 and +12 are +6 and +0 dB,
        below the plate's knee, where the row is not claimed and the pack
        says so."""
        for headroom in (-12.0, -6.0, 0.0):
            for rate in (48000, 44100, 22050):
                reading = self._curve(rate=rate, headroom_db=headroom)
                self.assertTrue(reading["passed"], (rate, headroom, reading))
                fault = self._curve(HardClip, rate=rate,
                                    headroom_db=headroom)
                self.assertFalse(fault["passed"], (rate, headroom, fault))
        for headroom in (6.0, 12.0):
            reading = self._curve(headroom_db=headroom)
            self.assertGreater(reading["plate"], self.PLATE_BAR,
                               (headroom, reading))

    def test_the_macros_the_row_holds_free_do_not_move_it(self):
        """Mix, Output, Speed and Hysteresis are not in the trait's path,
        and the measurement shows it rather than the pack asserting it:
        0.0735 / 0.0569 / 0.0568 across Mix, 0.0589 / 0.0570 / 0.0570
        across Output, 0.0571 / 0.0569 across Hysteresis, at 48 kHz."""
        for index, values in ((2, (0.01, 0.35, 1.0)),
                              (1, (-24.0, 6.0, 12.0)),
                              (5, (3.75, 30.0)),
                              (7, (0.5, 1.0))):
            for value in values:
                probe = sine(1000, RATE + 1024, 0.0)
                effect = build(probe=probe, drive_db=self.BAR_DRIVE)
                span = type(effect)._MACRO_RANGES[index]
                effect.set_macro(index,
                                 rebuilt._component.macro_of(span, value))
                wet = probes.wet_render(effect, RATE, rate=RATE, channels=2,
                                        block=256, class_name="Saturation")
                effect.deinit()
                reading = self._slopes(wet, probe, RATE, RATE)
                self.assertTrue(reading["passed"],
                                (index, value, reading))


class DriveCeilingAndLean(unittest.TestCase):
    def test_drive_tops_out_where_the_alias_floor_holds(self):
        effect = build()
        effect.set_macro(0, 127)
        self.assertAlmostEqual(effect.macro(0), 15.0, places=6)
        effect.deinit()

    def _lean_render(self, probe, **options):
        effect = build(probe=probe, **options)
        effect.program_change(rebuilt.LEAN_PATCH)
        latency = effect.latency_samples
        wet = render(effect, 48000)
        effect.deinit()
        return wet.float[24000:, 0], latency

    def test_mix_zero_is_the_borrowed_source_itself(self):
        """audioif#95: a mixer voice at level 1.0 scales by 32768/32767, so
        a wire through the mixer gains an LSB on every sample at or above
        32736. Mix 0 hands back the source, so the invariant is exact by
        construction rather than by luck."""
        effect = build(mix=0.0)
        self.assertIs(effect.output, effect._source)
        self.assertEqual(effect.latency_samples, 0)
        effect.set_macro(2, 127)
        self.assertIs(effect.output, effect._mix)
        self.assertEqual(effect.latency_samples,
                         rebuilt.CLICK_ONSET_SAMPLES[("tube", 4)])
        effect.set_macro(2, 0)
        self.assertIs(effect.output, effect._source)
        effect.deinit()

    def test_leaving_mix_zero_does_not_step(self):
        """The mixer's voices have been idle while Mix was 0, so the block
        the class hands back after the move must join the one before it."""
        probe = sine(1000, 8192, -6.0)
        effect = build(probe=probe, mix=0.0)
        before = render(effect, 2048)
        effect.set_macro(2, 127)
        after = render(effect, 2048)
        joined = np.concatenate([before.float[:, 0], after.float[:, 0]])
        step = float(abs(joined[2048] - joined[2047])) * 32768.0
        inside = float(np.abs(np.diff(joined[1536:2048])).max()) * 32768.0
        effect.deinit()
        self.assertLess(step, 2.0 * inside, (step, inside))

    def test_lean_patch_is_one_factor_down(self):
        """Not byte equality: the re-route lands in a block where the new
        shaper's history is zero, and the 5 Hz coupling filter carries that
        step for a fifth of a second and settles a couple of LSB from where
        the other build settled. In the tail it tracks an `oversample=4`
        build to 21 LSB on a 6697 LSB signal, where an x8 build is 515."""
        self.assertEqual(Saturation.PATCHES[rebuilt.LEAN_PATCH][0],
                         "Saturation - lean")
        probe = sine(1010, 48000, -6.0)
        lean, latency = self._lean_render(probe)
        self.assertEqual(latency, 2)
        plain = build(probe=probe, oversample=2, patch=0)
        two = render(plain, 48000).float[24000:, 0]
        plain.deinit()
        eight = build(probe=probe)
        wet = render(eight, 48000)
        eight.deinit()
        like_four = float(np.abs((lean - two) * 32768.0).max())
        like_eight = float(np.abs((lean - wet.float[24000:, 0])
                                  * 32768.0).max())
        self.assertLessEqual(like_four, 32.0, (like_four, like_eight))
        self.assertGreater(like_eight, 10.0 * like_four,
                           (like_four, like_eight))

    def test_leaving_the_lean_patch_restores_the_factor(self):
        effect = build()
        effect.program_change(rebuilt.LEAN_PATCH)
        effect.program_change(0)
        self.assertEqual(effect.latency_samples, 3)
        effect.deinit()

    def test_one_priming_path_for_every_interpreter(self):
        """audioif#85's cure is a two-frame silence, not a branch: a
        one-frame looped zero sample hangs `get_buffer` on a 1-channel
        native Mixer, and a class that asks which interpreter it is on is
        not testing on MicroPython what it tested on CPython
        (audiocomponents#70)."""
        with open(rebuilt.__file__.replace(".pyc", ".py")) as handle:
            source = handle.read()
        self.assertNotIn("implementation", source)
        self.assertIn('array("h", bytes(2 * 2 * channels))', source)


class TheClassHandsBackThePalettesOwnBlock(unittest.TestCase):
    """256 frames per pull, at either channel count.

    `Mixer._render_size` is `buffer_size // 2 // 4 * 4` BYTES, so the 1024
    this class shipped rendered **128 stereo frames** and every node behind
    it - the `Splitter`, whose own chunk is 256 frames, the oversampled
    shaper, the three biquads - was pulled twice per 256-frame block. That
    is the palette's block and the unit every audioif node works in, and an
    extra Python-level pull is worth about 0.18 ms on the P4 and 0.11 ms on
    the S3 off the board's own rows (audiocomponents#70, fifth fix round).
    """

    def _frames_per_pull(self, channels):
        import audiocore
        effect = build(channels=channels)
        try:
            lengths = []
            for _ in range(3):
                _result, buffer = audiocore.get_buffer(effect.output)
                lengths.append(len(buffer) // (2 * channels))
            return lengths
        finally:
            effect.deinit()

    def test_every_pull_is_one_palette_block(self):
        for channels in (2, 1):
            lengths = self._frames_per_pull(channels)
            self.assertEqual(lengths, [256, 256, 256],
                             "%d channel: %s frames per pull"
                             % (channels, lengths))

    def test_the_shipped_buffer_is_red(self):
        """The plant: the 1024 the class shipped, which reads 128."""
        kept = rebuilt.MIXER_BUFFER_BYTES
        rebuilt.MIXER_BUFFER_BYTES = 512
        try:
            lengths = self._frames_per_pull(2)
        finally:
            rebuilt.MIXER_BUFFER_BYTES = kept
        self.assertEqual(lengths, [128, 128, 128],
                         "the plant did not fire: %s" % (lengths,))

    def test_the_block_length_moves_no_sample(self):
        """The trim is a cost change and nothing else: the same 1 kHz
        render comes back byte for byte at either block length."""
        material = sine(1000.0, frames=24000, dbfs=-12.0)
        kept = rebuilt.MIXER_BUFFER_BYTES
        renders = []
        try:
            for size in (512, 1024):
                rebuilt.MIXER_BUFFER_BYTES = size
                effect = build(probe=material)
                renders.append(render(effect, 24000).pcm)
                effect.deinit()
        finally:
            rebuilt.MIXER_BUFFER_BYTES = kept
        self.assertEqual(renders[0], renders[1],
                         "128- and 256-frame blocks render different bytes")


class TheGenerator(unittest.TestCase):
    """TU3's instrument, run from the suite.

    The second-pass refuter found the generator reverted on the
    integration branch and `--check` red, while 143 tests were green,
    because nothing in this file ran it - `Fuzz` and `Distortion` both run
    theirs (audiocomponents#70). A table whose generator has drifted is a
    table nobody can reproduce, and A4, TU1's quiet end and the
    cross-interpreter digests all rest on this one.
    """

    def test_check_agrees_with_the_shipped_tables(self):
        import subprocess
        root = os.path.join(os.path.dirname(__file__), "..")
        script = os.path.join(root, "tools", "curves", "saturation_curve.py")
        if not os.path.isfile(script):
            self.skipTest("no generator in this checkout")
        environment = dict(os.environ)
        environment["PYTHONPATH"] = os.path.abspath(
            os.path.join(root, "lib"))
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        done = subprocess.run([sys.executable, script, "--check"],
                              capture_output=True, env=environment,
                              cwd=os.path.abspath(root))
        self.assertEqual(done.returncode, 0,
                         (done.stdout[-2000:], done.stderr[-2000:]))


class TheNodeIsNeverAskedPastItsRail(unittest.TestCase):
    """audioif#99, re-measured on this class's own curve.

    `audioshaper.Waveshaper` clamps its output at int16, so a `post_gain`
    that asks it for more than full scale clips at the BASE rate, behind
    the decimator, where no oversampling factor reaches. The tube table is
    smooth and does not ring the way a diode clipper does - the bare node
    reads -95.331 dB of inharmonic energy at an output peak of 0.98120 and
    -70.233 at 1.00000 - so the ceiling here is the rail itself, and the
    class holds 0.16 dB under it by splitting the level between the node
    and the wet mixer voice.
    """

    def _ask(self, effect):
        """What the node would put out for a full-scale input: post_gain
        times the largest magnitude the curve reaches at this pre_gain."""
        seen = {}

        def spy(**options):
            seen.update(options)
        for shaper in effect._shapers():
            shaper.set = spy
        effect._push_gains()
        return seen["post_gain"] * effect._reach(seen["pre_gain"])

    def test_no_shipped_position_asks_past_the_ceiling(self):
        worst = (0.0, None)
        checked = 0
        for character in rebuilt.CHARACTERS:
            for index in range(len(Saturation.MACRO_LABELS)):
                for midi in (0, 32, 64, 96, 127):
                    effect = build(character=character,
                                   probe=probes.silence(1024))
                    effect.set_macro(index, midi)
                    ask = self._ask(effect)
                    effect.deinit()
                    checked += 1
                    if ask > worst[0]:
                        worst = (ask, (character, index, midi))
            for patch in sorted(Saturation.PATCHES):
                effect = build(character=character,
                               probe=probes.silence(1024))
                effect.program_change(patch)
                ask = self._ask(effect)
                effect.deinit()
                checked += 1
                if ask > worst[0]:
                    worst = (ask, (character, "patch", patch))
            # the corner the survey found: Headroom up and Output up
            for headroom in (-12.0, -6.0, 0.0, 6.0, 12.0):
                for output in (-24.0, 0.0, 6.0, 12.0):
                    effect = build(character=character,
                                   probe=probes.silence(1024),
                                   drive_db=0.0, headroom_db=headroom,
                                   output_db=output)
                    ask = self._ask(effect)
                    effect.deinit()
                    checked += 1
                    if ask > worst[0]:
                        worst = (ask, (character, headroom, output))
        self.assertEqual(checked, 3 * (40 + 9 + 20))
        self.assertLessEqual(worst[0], rebuilt.NODE_CEILING + 1e-9, worst)

    def test_a_position_under_the_ceiling_keeps_its_exact_split(self):
        """The default asks 0.394 and must not move an LSB for this."""
        effect = build(probe=probes.silence(1024))
        seen = {}

        def spy(**options):
            seen.update(options)
        for shaper in effect._shapers():
            shaper.set = spy
        effect._push_gains()
        wet_level = effect._mix.voice[1].level
        effect.deinit()
        self.assertAlmostEqual(seen["post_gain"], rebuilt.TUBE_MAKEUP,
                               places=9)
        self.assertAlmostEqual(wet_level, 1.0, places=9)

    def rendered_db(self, output_db, dbfs=-12.0, hz=1000.0, rate=RATE,
                    **options):
        """The level the class actually puts out, rendered.

        The row this replaces multiplied `post_gain` by the mixer voice's
        level in Python and asserted the product - and a mixer voice
        **clamps at 1.0**, so the product was a number nobody could hear.
        Output +12 delivered +7.866 dB (audit 3 (p)1, ruling (o)).
        """
        frames = rate // 4
        effect = build(probe=sine(hz, frames + 2048, dbfs, rate=rate),
                       frames=frames, rate=rate, output_db=output_db,
                       **options)
        try:
            wet = render(effect, frames, rate=rate)
        finally:
            effect.deinit()
        values = wet.data[frames // 2:, 0].astype(np.float64) / 32768.0
        return 20.0 * math.log10(max(1e-9,
                                     float(np.sqrt((values * values).mean()))))

    def test_the_split_keeps_the_level_law(self):
        """Rendered, at both builds: Output is decibels out for decibels
        asked, and the makeup shelf is what carries what the node gave up.

        Output +12 asks the node for 1.581 of full scale at the tube's
        default drive, so the class holds the node at `NODE_CEILING` and
        puts 4.2 dB on `_makeup_shelf`. A mixer voice cannot carry it; a
        `HIGH_SHELF` at 10 Hz can.
        """
        for character in ("tube", "console"):
            base = self.rendered_db(0.0, character=character)
            for asked in (3.0, 6.0, 9.0, 12.0):
                got = self.rendered_db(asked, character=character)
                self.assertAlmostEqual(
                    got - base, asked, delta=0.25,
                    msg="%s: Output +%.0f delivered %+.3f dB"
                        % (character, asked, got - base))

    def test_the_makeup_shelf_is_what_moved(self):
        """And it is zero where the split does not fire, so 63 of the 75
        shipped positions do not move a byte."""
        quiet = build(probe=probes.silence(1024), output_db=0.0)
        loud = build(probe=probes.silence(1024), output_db=12.0)
        try:
            self.assertEqual(quiet._makeup_shelf.gain_db, 0.0)
            self.assertGreater(loud._makeup_shelf.gain_db, 3.0)
            self.assertLessEqual(loud._mix.voice[1].level, 1.0)
        finally:
            quiet.deinit()
            loud.deinit()


def effect_latency_of(effect_declared):
    """The declaration this class makes is the onset, and the sub-sample
    reading is always longer than it."""
    return effect_declared


def effect_level_moved(seen):
    """How much of the level the node gave up, as a ratio > 1 when the
    split fired."""
    return (rebuilt.TUBE_MAKEUP * rebuilt._component.db_to_gain(12.0)
            / seen["post_gain"])


class TP1SpeedSlide(unittest.TestCase):
    def test_fixed_loss_fault_is_not_a_knob(self):
        kit_faults.fault_reachability(
            Saturation, FixedLoss,
            lambda effect: (
                effect._loss.frequency if effect._loss is not None else -1.0),
            lambda subject: build(subject, probe=probes.silence(2048),
                                  character="tape", speed_ips=7.5),
            label="Saturation TP1")


class TheTierOneRowsAtEveryShippedPatch(unittest.TestCase):
    """audiocomponents#87.

    Tier 1's silence and tail rows were taken at the constructor default,
    and the default was the one state whose Bias was exactly 0: the 0-127
    grid had no centre, so MIDI 64 was +0.007874 and every shipped patch
    carried a bias the patch never asked for. Eight of the nine emitted
    109 to 9067 LSB into digital silence, and `program_change` thumped up
    to -11.2 dBFS out of nothing.

    So the rows walk the patches now. The centre detent is the fix; what
    stays red is the class's own, and is named rather than tolerated.
    """

    #: Empty since the third fix round. Patches 4 and 6 offset the tape on
    #: purpose -- Bias MIDI 58 and 70, -0.095 and +0.095 -- and an offset
    #: into an asymmetric transfer is a mean the plate's coupling pole has
    #: to hold. **The pole was there and started cold**, so those two put
    #: 8 489 and 7 044 LSB out of digital silence before they decayed
    #: (audit 3 (p)6). `_charge_coupling` settles it before the first
    #: block and both read 1 LSB now, which is `RESIDUAL_LSB`: a stated
    #: residual, bounded and tested, rather than a patch with a footnote.
    RED = {}

    RED_TAIL = {}

    #: The disclosed exception, under audit 3 ruling (n). +-1 LSB at the
    #: input of this much gain is what is left when the pole is charged;
    #: Bias +0.30 settles to -5 LSB and Bias +1.0 to -11, which the
    #: docstring states and `TheThirdFixRoundsRows` does not need to
    #: because no shipped patch goes there.
    RESIDUAL_LSB = 2

    def peaks(self):
        """`{patch: (silence_peak, tail_samples, residual, declared)}`."""
        rows = {}
        for patch in sorted(Saturation.PATCHES):
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
            with self.subTest(patch=patch):
                self.assertLessEqual(
                    row[0], self.RESIDUAL_LSB,
                    "patch %d emits %d LSB into digital silence, against a "
                    "stated residual of %d"
                    % (patch, row[0], self.RESIDUAL_LSB))

    def test_only_an_offset_patch_uses_any_of_the_stated_residual(self):
        for patch, row in sorted(self.peaks().items()):
            if patch in (4, 6):
                continue
            self.assertEqual(row[0], 0, (patch, row[0]))

    def test_the_declared_tail_holds_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            _quiet, tail_samples, residual, declared = row
            with self.subTest(patch=patch):
                self.assertLessEqual(
                    residual, self.RESIDUAL_LSB,
                    "patch %d leaves %d LSB, against a stated residual of "
                    "%d" % (patch, residual, self.RESIDUAL_LSB))
                if residual:
                    continue
                self.assertLessEqual(tail_samples or 0, declared,
                                     "patch %d rings %s samples against a "
                                     "declared %s"
                                     % (patch, tail_samples, declared))

    def test_program_change_onto_digital_silence_stays_silent(self):
        """A patch change is a wire message and can arrive between notes."""
        for patch in sorted(Saturation.PATCHES):
            effect = build(probe=probes.silence(RATE, 2), patch=0)
            before = render(effect, RATE // 2)
            effect.program_change(patch)
            after = render(effect, RATE // 2)
            effect.deinit()
            with self.subTest(patch=patch):
                self.assertEqual(int(np.abs(before.data).max()), 0)
                peak = int(np.abs(after.data).max())
                self.assertLessEqual(
                    peak, self.RESIDUAL_LSB,
                    "program_change(%d) on silence emitted %d LSB, against "
                    "a stated residual of %d - it was 8 489 before the "
                    "coupling pole was charged"
                    % (patch, peak, self.RESIDUAL_LSB))


if __name__ == "__main__":
    unittest.main()
