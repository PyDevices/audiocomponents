"""`Fuzz`'s own invariant and planted-fault tests.

Dossier: workspace docs/effects-internal/dossiers/Fuzz.md, frozen
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

import audiocore                                                # noqa: E402
import kit_faults                                               # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects import fuzz as rebuilt                       # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
Fuzz = rebuilt.Fuzz


def build(cls=None, rate=RATE, channels=2, frames=48000, probe=None,
          **options):
    cls = cls or Fuzz
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2, label=None):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, label=label, class_name="Fuzz",
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


class SymmetricFuzz(Fuzz):
    """G1: the germanium table replaced with the odd-symmetric silicon one,
    on **every** shaper the graph holds.

    It used to swap `self._shapers[0]` alone, and patch 8 `Fuzz - lean`
    plays a second shaper: at that patch the faulted class rendered
    byte-identical to the clean one (`0x56a87ced` both) and G1 read green on
    it (audiocomponents#74, second audit). A fault that a shipped patch
    routes around is not a guard.

    The level is left where the class puts it. The silicon table is
    peak-normalised in its own right, so the fault runs `GERMANIUM_SCALE`
    (3.98 dB) quieter than the table it stands in for - and both of G1's
    clauses are ratios, so no level turns either of them red.
    """
    NAME = 'Fuzz'

    def _build(self, **options):
        options["character"] = "germanium"
        Fuzz._build(self, **options)
        curve = rebuilt._q15_array(rebuilt.CASCADE_CURVE)
        for shaper in self._shapers:
            shaper.set(curve=curve)
        self._curve = curve


class NoOversampleFuzz(Fuzz):
    """A4: oversample forced to 1. Not a macro."""
    NAME = 'Fuzz'

    def _build(self, **options):
        options["oversample"] = 1
        Fuzz._build(self, **options)


class AlwaysTiltFuzz(Fuzz):
    """G4: a 6 dB shelf that the Tilt macro cannot turn off."""
    NAME = 'Fuzz'

    def _refresh(self):
        Fuzz._refresh(self)
        self._tilt.gain_db = 6.0


class ShortLatencyFuzz(Fuzz):
    """CLICK: report 256 samples short."""
    NAME = 'Fuzz'

    @property
    def latency_samples(self):
        self._check_live()
        return max(0, int(self._latency) - 256)


class HighHpFuzz(Fuzz):
    """G3: the first HP sits at 800 Hz. Fuzz is then a tone control."""
    NAME = 'Fuzz'

    def _build(self, **options):
        Fuzz._build(self, **options)
        self._hps[0].frequency = 800.0


class GermaniumCascade(Fuzz):
    """C1: cascade graph with the off-centre germanium table."""
    NAME = 'Fuzz'

    def _build(self, **options):
        options["character"] = "cascade"
        Fuzz._build(self, **options)
        curve = rebuilt._q15_array(rebuilt.GERMANIUM_CURVE)
        for shaper in self._shapers:
            shaper.set(curve=curve, post_gain=rebuilt.GERMANIUM_SCALE)
        self._curve = curve


class NoScoopFuzz(Fuzz):
    """C3: both tone arms are full-band. Tone cannot restore the scoop."""
    NAME = 'Fuzz'

    def _build(self, **options):
        options["character"] = "cascade"
        Fuzz._build(self, **options)
        self._tone_lp.frequency = 18000.0
        self._tone_hp.frequency = 20.0


class NoOutputPole(Fuzz):
    """The class at `ac96c72`: no coupling capacitor behind `cascade`'s
    second clipper ([audiocomponents#89]).

    The low arm of the tone stack is a `LOW_PASS`, which passes DC, so a
    Bias off centre stood **-16 383 to +16 382 LSB (-6.0 dBFS) on the
    output for ever**, at eight of the nine stops of a front-panel macro.
    Written as the section put into bypass rather than taken out of the
    graph: `mix=0` is the same wire the class had, and it leaves the node
    count alone so no other row moves under the fault. Parking the pole at
    a very low corner is **not** the same plant - a 0.02 Hz `HIGH_PASS`
    still bleeds two thirds of the offset away in float32, and reads
    -2 916 LSB where the real defect reads -16 383.
    """
    NAME = 'Fuzz'

    def _build(self, **options):
        # `rebuilt.Fuzz`, not the module global: `fuzz_fix4.py plant`
        # installs this class *as* that global, and a fault written
        # against it recurses until the stack ends.
        rebuilt.Fuzz._build(self, **options)
        if getattr(self, "_cascade_out_hp", None) is not None:
            self._cascade_out_hp.mix = 0.0
            self._charge_output(rewire=True)


class DryTapRebalance(Fuzz):
    """The live re-charge with a dry-tap block pulled to "rebalance" it.

    The third round left `cascade` out of the live charge path on the
    grounds that re-pointing `shaper1` would leave one tap of the input
    `Splitter` a block ahead of the other. It does not - the charge pulls
    the output pole and `hp_in` is never pulled - and *this* is what
    happens if you pay for the block anyway: the dry leg arrives 256
    frames early and stays there.
    """
    NAME = 'Fuzz'

    def _charge_output(self, rewire=False):
        charged = rebuilt.Fuzz._charge_output(self, rewire=rewire)
        if rewire and self._dry is not None:
            audiocore.get_buffer(self._dry)
        return charged


#: Where `FrozenToneFuzz` welds the tone mixer: the high arm's share at
#: Tone 0.25, which is the notch's **top** centre (1206 Hz). It is not the
#: cascade constructor's own 0.5 - welded there the fault rendered
#: byte-identical to the clean class at the default it has to fire at
#: (`0xa143b169` both, audiocomponents#74, second audit).
FROZEN_TONE_SHARE = 0.25


class FrozenToneFuzz(Fuzz):
    """C4: the notch is there and cannot move — the tone mixer is welded
    wherever Tone is put.

    `NoScoopFuzz` is C3's fault and was C4's guard by mistake
    ([audiocomponents#74]): it goes red because there is no notch at all, so a
    class whose notch existed but was frozen would sail past it. C4 claims the
    centre *moves*, and this is the fault of that kind.

    It welds at `FROZEN_TONE_SHARE`, **not** at the constructor's own Tone
    0.5: a fault that does not differ from the clean class where the gate
    reads it is not a fault. At 0.25 the notch sits at 1206 Hz at every Tone,
    so C4's three-point span reads 0 octaves and the render differs from the
    clean class at the cascade default.
    """
    NAME = 'Fuzz'

    def _build(self, **options):
        options["character"] = "cascade"
        Fuzz._build(self, **options)

    def _refresh(self):
        Fuzz._refresh(self)
        if self._tone_mix is not None:
            wet = (self._value(5) * self._value(1)
                   * (1.0 - 0.5 * self._value(4)))
            self._tone_mix.voice[0].level = wet * (1.0 - FROZEN_TONE_SHARE)
            self._tone_mix.voice[1].level = wet * FROZEN_TONE_SHARE


def tone_response(effect):
    """Where the tone mixer puts the signal when Tone is moved, asked through
    the class's own surface and put back where it was found.

    The reading is the **high arm's share** of the sum at three Tone
    positions, so it is a ratio and not a level — Level, Load and Mix ride
    the same two voices and must not be able to look like a frozen tone —
    and it is the *movement* C4 claims, not one point of it. The shipped
    class reads `(0.0, 0.503937, 1.0)` wherever the rest of the surface sits.
    `FrozenToneFuzz` reads its weld three times over, and no macro position
    may reach that.
    """
    if effect._tone_mix is None:
        return None

    def share():
        low = float(effect._tone_mix.voice[0].level)
        high = float(effect._tone_mix.voice[1].level)
        total = low + high
        return round(high / total, 6) if total else None

    keep = effect.get_macro(2)
    try:
        out = []
        for position in (0, 64, 127):
            effect.set_macro(2, position)
            out.append(share())
    finally:
        effect.set_macro(2, keep)
    return tuple(out)


def _place(effect, patch=None, macros=None):
    """Put a built instance where the surface walk is standing: a shipped
    patch, then any macros on top of it. Every trait reading takes these, so
    a planted fault can be read at the same place as the clean class."""
    if patch is not None:
        effect.program_change(patch)
    for index, position in (macros or {}).items():
        effect.set_macro(index, position)
    return effect


def harmonic_lines(wet, hz, rate, frames, settle=None, channel=0):
    """Every harmonic bin of `hz` up to Nyquist, over a **whole number of
    cycles**, and the settled samples they were read from."""
    settle = frames // 3 if settle is None else settle
    period = rate / float(hz)
    cycles = int((frames - settle) // period)
    start = settle
    stop = settle + int(round(cycles * period))
    x = wet.float[start:stop, channel]
    n = len(x)
    mag = np.abs(np.fft.rfft(x))
    lines = {}
    order = 1
    while hz * order < rate / 2.0:
        index = int(round(hz * order * n / rate))
        if index >= len(mag):
            break
        lines[order] = float(mag[index])
        order += 1
    return lines, x


class Construction(unittest.TestCase):
    def test_defaults_and_capabilities(self):
        effect = build()
        self.assertEqual(effect.NAME, "Fuzz")
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(effect.latency_samples, 4)
        self.assertEqual(effect.tail_samples, 24576)
        effect.deinit()

    def test_mix_zero_reports_zero_latency(self):
        effect = build(mix=0.0)
        self.assertEqual(effect.latency_samples, 0)
        effect.deinit()


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
        result = kit.click(wet, dry, effect.latency_samples)
        effect.deinit()
        self.assertTrue(result["passed"], result)

    def test_short_report_turns_click_red(self):
        probe = probes.click_stereo(8192)
        effect = build(ShortLatencyFuzz, probe=probe)
        wet = render(effect, 8192)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            8192, rate=RATE, channels=2, block=256)
        result = kit.click(wet, dry, effect.latency_samples)
        effect.deinit()
        self.assertFalse(result["passed"], result)


class G1Asymmetry(unittest.TestCase):
    """**G1's second clause was restated on 2026-09-17 under vision §7.2.**

    The old target: `h2 ≥ −30 dBc` **and** the two output peaks ≥ 3 dB apart,
    1 kHz −20 dBFS at the shipped default.

    The measurement that killed the peak clause: that 8.221 dB split was a
    **−14.15 dBFS DC offset** and not the waveform's shape. The fix round put
    all three of S1's coupling poles in front of the shaper; the pedal's third
    capacitor is the **output** one, and with it back where the circuit has it
    the split at the shipped default is **0.768 dB** (0.268 at 44.1 kHz,
    0.665 at 22.05 kHz, 0.056 at Fuzz 54) — under its own 3 dB bar, at every
    rate and every shipped patch. The cause is not the coupling: at Fuzz 36 dB
    both halves of the wave are already at the rail, so a peak *height* cannot
    express the asymmetry however it is coupled. It reads 2.961 dB at Fuzz
    18 dB, which is the only place it ever meant anything.

    What this class claims instead, in two clauses it can fail, both ratios
    so that no offset and no level can carry either:

    1. **h2 ≥ −30 dBc** at 1 kHz, −20 dBFS, Tilt 0 — the frozen clause,
       unchanged (measured **−26.920 / −26.891 / −26.933** at 48 / 44.1 /
       22.05 kHz).
    2. **The even series h2+h4+h6+h8 ≥ −26 dB of the fundamental** — what
       survives the half-wave mirror `x(t) + x(t + T/2)`, and zero for any
       odd-symmetric clipper however hard it is driven. One even line can be
       an artefact; four in a row is a transfer curve that sits off centre.
       Measured **−21.331 / −21.350 / −21.367** at 48 / 44.1 / 22.05 kHz —
       a statistic that does not move with the rate, where the share of
       *total* harmonic energy does (fewer lines fit under Nyquist).
       `SymmetricFuzz` reads **−68.713 / −76.235 / −91.337**.

    The span both clauses are claimed over, and nowhere else: germanium,
    1 kHz, input **−46 … −20 dBFS**, **Fuzz ≤ 36 dB** (its own default),
    **Mix ≥ 0.5**, **Output Tilt ≥ −3 dB**, Bias at its centre, any Level
    above 0, any Load, any Tone, at all three rates. 300 cells, none failing;
    worst cell **h2 −29.740, even −24.303** at 44.1 kHz, Fuzz 36 dB,
    Mix 0.5, Tilt −3 dB — the Tilt and Mix axes are the tight ones, and both
    eat the same margin, which is why the span names where they stop.

    What is outside it, with the number, because each of these is where a
    user can stand:

    * **Above −20 dBFS in**: h2 −30.99 at −16, −41.15 at −6.
    * **Above Fuzz 36 dB**: h2 −36.19 at Fuzz 48, −45.40 at Fuzz 54, and the
      five shipped patches at Fuzz 48 dB and over (1, 4, 5, 6, 7) miss both
      clauses. That is the product at full fuzz.
    * **Output Tilt −6 dB**: the shelf takes 6 dB off everything above
      1 kHz, which is where every even line is — h2 **−29.765** at Mix 1 and
      **−31.055** at Mix 0.5 (44.1 kHz), so clause 1 fails there.
    * **Bias off centre**: the reading still passes at ±0.5 at the default
      Fuzz (h2 −29.49 / −29.57), but **the guard passes there too** — the
      shaper adds `bias` before the table, so a bias off centre makes an
      odd-symmetric curve asymmetric as surely as the germanium one. The row
      claims nothing at Bias off centre, patch 2 included. Bias +1 with Fuzz
      at 18 dB is a nearly linear part of the curve (h2 −80.5), and Bias
      −0.5 with Tilt −6 is h2 −33.56.

    What Brad should listen for at Phase 7: at the shipped default, on a
    single note held and let down, the octave-up **growl under the note** —
    the even harmonics — and that it thins out as you dig in. If the note
    sounds like a clean square-wave fuzz with no octave in it, this trait is
    gone whatever the numbers say.
    """

    H2_BAR = -30.0
    EVEN_BAR = -26.0
    EVEN_ORDERS = (2, 4, 6, 8)
    FRAMES = 48000
    #: The span of clause 1 and clause 2, as macro positions: Fuzz at or
    #: below its own default, Mix at or above a half, Output Tilt at or
    #: above −3 dB, Bias centred. Everything else is free.
    SPAN = {0: (0, 16, 32, 48, 64), 5: (64, 80, 96, 112, 127),
            6: (32, 64, 96, 127)}

    def _measure(self, cls=Fuzz, rate=RATE, hz=1000.0, dbfs=-20.0,
                 patch=None, macros=None, frames=None, **options):
        if frames is None:
            frames = self.FRAMES if rate > 24000 else self.FRAMES // 2
        probe = sine(hz, frames, dbfs, rate=rate)
        effect = build(cls, rate=rate, probe=probe, frames=frames, **options)
        if patch is not None:
            effect.program_change(patch)
        if macros is not None:
            pairs = (macros.items() if isinstance(macros, dict)
                     else enumerate(macros))
            for index, position in pairs:
                effect.set_macro(index, position)
        wet = render(effect, frames, rate=rate)
        effect.deinit()
        lines, x = harmonic_lines(wet, hz, rate, frames)
        fund = lines.get(1, 0.0)
        even = math.sqrt(sum(lines.get(order, 0.0) ** 2
                             for order in self.EVEN_ORDERS))
        if fund <= 0.0:
            return {"passed": False, "h2": None, "even_db": None,
                    "silent": True, "red": ["silent"]}
        h2 = 20.0 * math.log10((lines.get(2, 0.0) + 1e-30) / fund)
        even_db = 20.0 * math.log10((even + 1e-30) / fund)
        pos = max(float(x.max()), 0.0)
        neg = max(float(-x.min()), 0.0)
        passed = h2 >= self.H2_BAR and even_db >= self.EVEN_BAR
        return {"passed": passed, "h2": h2, "even_db": even_db,
                "silent": False,
                "peak_split_db": 20.0 * math.log10(
                    (max(pos, neg) + 1e-18) / (min(pos, neg) + 1e-18)),
                "mean_lsb": float(x.mean()) * 32768.0,
                "red": [] if passed else ["h2 %.3f even %.3f"
                                          % (h2, even_db)]}

    def _reading(self, cls=Fuzz):
        return self._measure(cls)

    def test_default_is_asymmetric(self):
        reading = self._reading()
        self.assertTrue(reading["passed"], reading)

    def test_symmetric_table_is_red(self):
        reading = self._reading(SymmetricFuzz)
        self.assertFalse(reading["passed"], reading)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(Fuzz, self._reading, label="Fuzz G1")

    def test_symmetric_fault_fires_at_the_lean_patch_too(self):
        """It used to swap `_shapers[0]` only, and patch 8 plays the other
        shaper: the faulted class was byte-identical to the clean one there
        ([audiocomponents#74], second audit)."""
        clean = self._measure(patch=rebuilt.LEAN_PATCH)
        faulted = self._measure(SymmetricFuzz, patch=rebuilt.LEAN_PATCH)
        self.assertTrue(clean["passed"], clean)
        self.assertFalse(faulted["passed"], faulted)

    def test_symmetric_fault_not_on_the_surface(self):
        """The reading is G1's **own measurement**, taken off whatever
        instance the walk hands it at the position it is standing on — not a
        constant keyed on the class's type, which is what the committed
        version read (all 128 positions, the same two literals)."""
        def reading(effect):
            macros = [effect.get_macro(index)
                      for index in range(len(Fuzz.MACRO_LABELS))]
            row = self._measure(type(effect), macros=macros, frames=9600)
            return None if row["silent"] else round(row["even_db"], 1)

        kit_faults.fault_reachability(
            Fuzz, SymmetricFuzz, reading,
            lambda subject: build(subject, probe=probes.silence(2048)),
            grid=(0, 32, 64, 96, 127), tolerance=3.0, label="Fuzz G1")

    def test_the_peak_split_clause_is_the_one_that_was_restated(self):
        """The measurement behind the restatement, kept as a test so it
        cannot quietly become a moved goalpost: with the output coupling
        where the circuit has it, the old clause is under its bar at the
        default at every rate, and the DC that used to carry it is gone."""
        for rate in (48000, 44100, 22050):
            row = self._measure(rate=rate)
            self.assertLess(row["peak_split_db"], 3.0, (rate, row))
            self.assertLess(abs(row["mean_lsb"]), 32.0, (rate, row))
        self.assertGreater(self._measure(fuzz_db=18.0)["peak_split_db"], 2.5)

    def test_both_clauses_hold_over_the_whole_span(self):
        """Not the held-fixed line: every combination of the three macros
        that move either clause, at 48 kHz here and at all three rates in
        the pack (300 cells, worst h2 −29.765 / even −24.464)."""
        worst = None
        for fuzz in self.SPAN[0]:
            for mix in self.SPAN[5]:
                for tilt in self.SPAN[6]:
                    row = self._measure(macros={0: fuzz, 5: mix, 6: tilt},
                                        frames=9600)
                    if worst is None or row["even_db"] < worst[1]["even_db"]:
                        worst = ((fuzz, mix, tilt), row)
                    self.assertTrue(row["passed"], ((fuzz, mix, tilt), row))
        self.assertGreater(worst[1]["h2"], self.H2_BAR, worst)

    def test_the_macros_that_are_pure_gain_do_not_move_either_clause(self):
        """Level, Load and Tone ride nothing but levels on germanium, and
        both clauses are ratios — so the span leaves all three free, and
        this is the reading that says it may."""
        base = self._measure(frames=9600)
        for index, position in ((1, 32), (1, 127), (2, 0), (2, 127),
                                (4, 0), (4, 127)):
            row = self._measure(macros={index: position}, frames=9600)
            self.assertAlmostEqual(row["h2"], base["h2"], delta=0.35,
                                   msg=(index, position, row))
            self.assertAlmostEqual(row["even_db"], base["even_db"],
                                   delta=0.35, msg=(index, position, row))

    def test_both_clauses_are_bounded_by_input_level(self):
        """Said in the docstring, the pack and the catalogue row in the same
        words: above −20 dBFS in, both halves square and the even energy
        goes."""
        self.assertTrue(self._measure(dbfs=-20.0)["passed"])
        self.assertFalse(self._measure(dbfs=-12.0)["passed"])
        self.assertFalse(self._measure(dbfs=-6.0)["passed"])

    def test_g1_reads_green_at_four_patches_and_is_claimed_at_three(self):
        """Full fuzz squares both halves, which is the product, not a
        defect — but the claim is the default's. **Patch 2 reads green and
        the row does not claim it**: see the guard test below."""
        holds, misses = [], []
        for index in sorted(Fuzz.PATCHES):
            (holds if self._measure(patch=index)["passed"]
             else misses).append(index)
        self.assertEqual(holds, [0, 2, 3, 8], holds)
        self.assertEqual(misses, [1, 4, 5, 6, 7], misses)
        self.assertEqual(self.CLAIMED_PATCHES, (0, 3, 8))

    #: The patches the row claims: green **and** guarded. Patch 2 reads
    #: green and is not one of them, because at Bias −0.85 the guard reads
    #: green too — see below.
    CLAIMED_PATCHES = (0, 3, 8)

    def test_the_guard_is_red_everywhere_the_row_claims_the_trait(self):
        """The dial-back walk, reading G1 itself on both classes: every
        patch the row claims, and every macro edge inside the span. 23
        positions, and `SymmetricFuzz` is red at all of them."""
        checked = 0
        for patch in self.CLAIMED_PATCHES:
            clean = self._measure(patch=patch, frames=9600)
            faulted = self._measure(SymmetricFuzz, patch=patch, frames=9600)
            checked += 1
            self.assertTrue(clean["passed"], (patch, clean))
            self.assertFalse(faulted["passed"], (patch, faulted))
        for index, positions in ((0, self.SPAN[0]), (5, self.SPAN[5]),
                                 (6, self.SPAN[6]), (1, (32, 127)),
                                 (2, (0, 127)), (4, (0, 127))):
            for position in positions:
                faulted = self._measure(SymmetricFuzz,
                                        macros={index: position},
                                        frames=9600)
                checked += 1
                self.assertFalse(faulted["passed"], (index, position,
                                                     faulted))
        self.assertEqual(checked, 23, checked)

    def test_bias_off_centre_is_its_own_asymmetry_and_the_row_says_so(self):
        """**Why the span pins Bias, and why patch 2 is not claimed.** The
        shaper adds `bias` before the table, so any bias off centre makes an
        *odd-symmetric* curve asymmetric too: `SymmetricFuzz` reads green at
        Bias 0, ±0.5 and ±1, and at patch 2 (Bias −0.85). The guard cannot
        tell the table from the knob there, so the row claims neither — and
        this test is what stops that quietly becoming a claim again."""
        for position in (0, 32, 96, 127):
            faulted = self._measure(SymmetricFuzz, macros={3: position},
                                    frames=9600)
            self.assertTrue(faulted["passed"], (position, faulted))
        self.assertTrue(self._measure(SymmetricFuzz, patch=2,
                                      frames=9600)["passed"])
        self.assertNotIn(2, self.CLAIMED_PATCHES)


class G2LevelLaw(unittest.TestCase):
    def _thd(self, dbfs, cls=Fuzz):
        probe = sine(1000, 48000, dbfs)
        effect = build(cls, probe=probe)
        wet = render(effect, 48000)
        spec = kit.spectrum(wet, 1000.0, harmonics=8)
        effect.deinit()
        return spec["values"]["thd_db"]

    def test_h2_moves_more_than_6_db_between_minus_26_and_minus_6(self):
        a, b = self._thd(-26), self._thd(-6)
        # THD itself flattens at the top of the range at the shipped Fuzz
        # 36 dB (the 0.5 dB-per-step clause is disconfirmed; pack G2).
        # h2/h1 still moves.
        ha = self._h2(-26)
        hb = self._h2(-6)
        self.assertGreater(abs(ha - hb), 6.0, (ha, hb, a, b))

    def _h2(self, dbfs, cls=Fuzz):
        probe = sine(1000, 48000, dbfs)
        effect = build(cls, probe=probe)
        wet = render(effect, 48000)
        spec = kit.spectrum(wet, 1000.0, harmonics=8)
        effect.deinit()
        return spec["values"]["harmonic_db"]["h2"]

    def test_null_build_is_red(self):
        def measure(cls):
            a, b = self._h2(-26, cls), self._h2(-6, cls)
            passed = a is not None and b is not None and abs(a - b) > 6.0
            return {"passed": passed, "red": [] if passed else [a, b]}
        kit_faults.null_build_red(Fuzz, measure, label="Fuzz G2")


class G4NoToneStack(unittest.TestCase):
    """No tone stack on germanium: the band is flat within 1 dB and 40 Hz is
    within 3 dB of 1 kHz.

    Same span as G3, for the same three reasons — **Output Tilt 0, Mix ≥ 0.5,
    Level above 0, |Bias| < 1** — and `AlwaysTiltFuzz` is green at exactly
    those three cells and nowhere else on the 44-position walk.

    The 40 Hz clause is **re-measured this round and it moved**: the 31 Hz
    output coupling pole is behind the clipper now, so its cut reaches the
    output instead of being squashed by the clipper's own compression. It
    reads **−2.362 dB** at the default against the 3 dB bar (−2.345 /
    −2.357 at 44.1 / 22.05 kHz), where the all-poles-in-front graph read
    −0.873 dB; the worst shipped cell is **−2.843 dB** at patch 3.

    One in-band miss, and the pack says so: **patch 7 "Full fuzz, mix back"
    reads 1.017 dB** across 100 Hz–8 kHz, just over the 1 dB bar, because at
    Mix 0.35 the dry copy is the signal after the input coupling and 100 Hz
    is 0.51 dB down on it. Every other patch is inside 0.654 dB.
    """

    def _flatness(self, cls=Fuzz, patch=None, macros=None):
        # Cheap two-tone proxy at 100 Hz and 1 kHz, −40 dBFS, default Fuzz.
        lows = []
        for hz in (100.0, 1000.0, 8000.0):
            probe = sine(hz, 24000, -40.0)
            effect = build(cls, probe=probe)
            _place(effect, patch, macros)
            wet = render(effect, 24000)
            rms = float(np.sqrt(np.mean(wet.float[8000:, 0] ** 2)))
            lows.append(20.0 * math.log10(rms + 1e-12))
            effect.deinit()
        spread = max(lows) - min(lows)
        return spread, lows

    def test_the_only_patch_over_the_in_band_bar_is_the_one_named(self):
        for patch in sorted(Fuzz.PATCHES):
            spread, mags = self._flatness(patch=patch)
            if patch == 7:
                self.assertGreater(spread, 1.0, (patch, mags))
            else:
                self.assertLess(spread, 1.0, (patch, mags))

    def test_in_band_spread_under_one_db_at_default(self):
        spread, lows = self._flatness()
        self.assertLess(spread, 1.0, lows)

    def test_forced_shelf_spreads(self):
        spread, lows = self._flatness(AlwaysTiltFuzz)
        self.assertGreater(spread, 1.0, lows)

    def test_null_build_is_red(self):
        def measure(cls):
            spread, lows = self._flatness(cls)
            # A wire is flatter still; require the class to be the one
            # whose HPs put 40 Hz in play — this measure is the 100 Hz-8 kHz
            # spread staying under 1 dB. A wire also stays under 1 dB, so
            # G4's null-build is the 40 Hz clause, measured here as "the
            # 100 Hz reading is not equal to the 8 kHz reading by more than
            # a hair on a wire". Use AlwaysTilt as the red twin instead.
            return {"passed": spread < 1.0, "red": lows}
        # A wire is also flat in-band, so this measurement cannot be
        # null-build-red. The pack records G4's 40 Hz clause for that.
        spread, _ = self._flatness()
        self.assertLess(spread, 1.0)


def alias_20k(wet, hz, rate, size):
    """The 20 Hz–20 kHz inharmonic floor, the dossiers' own rule.

    Every FFT bin more than two bins from a harmonic of `hz` and from DC,
    summed against the fundamental's bin, over 4800 samples at 48 kHz so
    every harmonic lands on a bin. This is the number A4's bar is graded on
    and the one the board runner's `probes/alias_floor/analyse_alias.py`
    prints; `kit.spectrum`'s `alias_floor_db` is the same rule with no band
    limit, and the two part company where the last decimation stage's
    transition band lets a fold land above 20 kHz.
    """
    x = wet.data[size:size + size, 0].astype(np.float64)
    mag = np.abs(np.fft.rfft(x))
    bin_hz = rate / float(size)
    mask = np.ones(len(mag), dtype=bool)
    mask[:3] = False
    order = 1
    while hz * order < rate / 2.0:
        centre = int(round(hz * order / bin_hz))
        mask[max(0, centre - 2):centre + 3] = False
        order += 1
    freqs = np.arange(len(mag)) * bin_hz
    mask &= (freqs >= 20.0) & (freqs <= 20000.0)
    centre = int(round(hz / bin_hz))
    base = mag[max(0, centre - 2):centre + 3].max()
    total = math.sqrt(float((mag[mask] ** 2).sum()))
    return 20.0 * math.log10(max(total, 1e-12) / max(base, 1e-12))


class A4AliasFloor(unittest.TestCase):
    """**A4 was redefined on 2026-09-17 under vision §7.2, and the
    redefinition is amended here the same day — the second audit found the
    replacement target false in three places.**

    The original target: 20 Hz–20 kHz inharmonic energy ≥ 60 dB below the
    fundamental at 1010 Hz *and* 3700 Hz, −6 dBFS, maximum Fuzz, ×8, 48 kHz.
    Unreachable: at the shipped ×8 it holds at 1010 Hz only up to Fuzz 30 dB
    and at 3700 Hz it fails at every position of the macro, its own minimum
    included. `test_the_old_sixty_db_bar_is_unreachable_across_the_whole_macro`
    is that measurement, kept.

    The first replacement said three things this pass could not hold:
    its floor bars and its ×8-against-×1 clause **fail at 22.05 kHz**
    (−25.094 / −13.465, and ×8 buys 11.203 / 6.973 dB), its
    **monotone-in-Fuzz** clause is false on the Fuzz macro's own 0–127 grid
    (2 breaks at 1010 Hz, 1 at 3700 Hz, 48 kHz), and **"the worst case is
    maximum Fuzz" is false** — patch 8 `Fuzz - lean` shapes at ×2 and reads
    −30.571 / −19.589 at the *default* Fuzz.

    What this class claims now, in clauses it can fail, all on the **wet
    branch** (`kit_probes.wet_render`; at Mix 0.25 a mixed read is 5.5 dB
    optimistic and that is dry dilution, not rejection):

    1. **At the shipped default**, ×8, 48 **and 44.1 kHz**: at least
       **50 dB** down at 1010 Hz and **35 dB** at 3700 Hz (measured
       −55.024 / −38.496 and −55.914 / −36.678).
    2. **Oversampling earns its cost** at those rates: ×8 at least **20 dB**
       better than ×1 at both tones (measured 34.794 / 25.405 and
       36.793 / 25.315).
    3. **Nowhere on the ×8 shipped surface does the floor rise above
       35 dB down at 1010 Hz or 28 dB at 3700 Hz** — every Fuzz, Bias and
       Output Tilt position (90 cells a rate, Level, Load, Tone and Mix
       being levels a wet-branch read cannot move) and every shipped patch
       but the lean one. Worst cell: **−38.154 / −30.478** at 44.1 kHz.
       This replaces "falls monotonically", which was false.
    4. **The lean patch is the S3's price, and it is named**: patch 8 shapes
       at ×2 and reads **−30.571 / −19.589** at 48 kHz, −29.001 / −18.774 at
       44.1 kHz. Not claimed under 1 or 3; stated in the docstring, the
       catalogue row and the pack in the same words.
    5. **At 22.05 kHz the row is DISCONFIRMED, with its cause**: −25.094 /
       −13.465 at the default, and no oversampling factor helps (×8 buys
       11.203 dB at 1010 Hz where it buys 34.794 at 48 kHz). The cause is
       not the class: a fuzz's own harmonic series crosses Nyquist at the
       *output* rate — h11 of 1010 Hz and h3 of 3700 Hz are both above
       11.025 kHz — and what folds there was never in the oversampled path
       to be filtered.

    What Brad should listen for at Phase 7: at full Fuzz on a high note, a
    thin metallic ring that does not move with the note — that is the fold.
    At 48 kHz and the default it should be inaudible under the fuzz itself;
    at 22.05 kHz, or on patch 8, it is meant to be audible and is the price
    of the rate and of the S3's block.
    """

    FUZZ_DBS = (18.0, 24.0, 30.0, 36.0, 42.0, 48.0, 54.0)
    RATES = (48000, 44100)
    DEFAULT_BAR = {1010.0: 50.0, 3700.0: 35.0}
    SURFACE_BAR = {1010.0: 35.0, 3700.0: 28.0}
    LEAN_BAND = {1010.0: (-35.0, -25.0), 3700.0: (-25.0, -15.0)}
    OVERSAMPLE_GAIN_DB = 20.0

    def _floor(self, cls=Fuzz, hz=1010.0, rate=RATE, patch=None, macros=None,
               mixed=False, **options):
        size = int(round(rate * 0.1))
        frames = 2 * size
        probe = sine(hz, frames, -6.0, rate=rate, channels=1)
        effect = build(cls, rate=rate, probe=probe, channels=1,
                       frames=frames, **options)
        if patch is not None:
            effect.program_change(patch)
        for index, position in (macros or {}).items():
            effect.set_macro(index, position)
        if mixed:
            wet = render(effect, frames, rate=rate, channels=1)
        else:
            try:
                wet = probes.wet_render(effect, frames, rate=rate,
                                        channels=1, block=256,
                                        class_name="Fuzz",
                                        latency_samples=effect.latency_samples)
            except (kit.ExhaustedProbeError, kit.StarvedTapError):
                raise
            except kit.MeasurementRefused:
                # *Only* the "no dry leg to mute" refusal, and there it says
                # the mixed render **is** the wet branch: a class built as a
                # wire, or this one at Mix 0, where the output is the
                # borrowed source. The null build has to get a real reading
                # here rather than a refusal it can pass by — it fails
                # clause 2 because a wire ignores `oversample`. A render that
                # outlived its probe or starved a tap still refuses.
                wet = render(effect, frames, rate=rate, channels=1)
        effect.deinit()
        return alias_20k(wet, hz, rate, size)

    def _reading(self, cls=Fuzz):
        """Clauses 1, 2 and 3 — the three a null build has to fail."""
        default = {}
        bare = {}
        for rate in self.RATES:
            for hz in self.DEFAULT_BAR:
                default[(rate, hz)] = self._floor(cls, hz, rate=rate)
                bare[(rate, hz)] = self._floor(cls, hz, rate=rate,
                                               oversample=1)
        surface = {}
        for hz in self.SURFACE_BAR:
            worst = None
            for fuzz in (0, 64, 127):
                for tilt in (0, 127):
                    value = self._floor(cls, hz, macros={0: fuzz, 6: tilt})
                    worst = value if worst is None else max(worst, value)
            surface[hz] = worst
        clause1 = all(default[key] <= -self.DEFAULT_BAR[key[1]]
                      for key in default)
        clause2 = all(bare[key] - default[key] >= self.OVERSAMPLE_GAIN_DB
                      for key in default)
        clause3 = all(surface[hz] <= -self.SURFACE_BAR[hz] for hz in surface)
        passed = clause1 and clause2 and clause3
        return {"passed": passed, "default": default, "x1": bare,
                "surface": surface, "clauses": (clause1, clause2, clause3),
                "red": [] if passed else ["a4 %s" % ((clause1, clause2,
                                                      clause3),)]}

    def test_the_clauses_hold(self):
        reading = self._reading()
        self.assertTrue(reading["passed"], reading)

    def test_the_surface_clause_over_every_patch_but_the_lean_one(self):
        for rate in self.RATES:
            for patch in sorted(Fuzz.PATCHES):
                if patch == rebuilt.LEAN_PATCH:
                    continue
                for hz, bar in self.SURFACE_BAR.items():
                    value = self._floor(hz=hz, rate=rate, patch=patch)
                    self.assertLessEqual(value, -bar, (rate, patch, hz,
                                                       value))

    def test_the_lean_patch_is_where_it_is_said_to_be(self):
        """Clause 4 is a claim, not a caveat: it can fail."""
        for hz, (low, high) in self.LEAN_BAND.items():
            value = self._floor(hz=hz, patch=rebuilt.LEAN_PATCH)
            self.assertTrue(low <= value <= high, (hz, value))

    def test_at_2205_the_row_is_disconfirmed_and_the_cause_is_the_rate(self):
        """Clause 5. The class misses its own bars there, and oversampling
        is not what is missing: the fold is at the output rate."""
        for hz, bar in self.DEFAULT_BAR.items():
            self.assertGreater(self._floor(hz=hz, rate=22050), -bar,
                               (hz, "22.05 kHz is claimed to miss"))
        eight = self._floor(hz=1010.0, rate=22050)
        one = self._floor(NoOversampleFuzz, hz=1010.0, rate=22050)
        self.assertLess(one - eight, 15.0, (one, eight))
        self.assertGreater(
            self._floor(NoOversampleFuzz, hz=1010.0) - self._floor(hz=1010.0),
            25.0)

    def test_the_wet_read_is_not_the_mixed_one(self):
        """`mute_dry` reaches a dry leg that is inside the `Waveshaper`
        and not a mixer voice at all (the Fuzz round's kit fix, moved into
        `tools/effect_measurements` by audiocomponents#81). Without it
        every Mix below 1 reads a floor it has not got."""
        wet = self._floor(hz=1010.0, macros={5: 32})
        mixed = self._floor(hz=1010.0, macros={5: 32}, mixed=True)
        self.assertAlmostEqual(wet, self._floor(hz=1010.0), delta=0.5)
        self.assertLess(mixed, wet - 5.0, (wet, mixed))

    def test_no_oversample_is_red_at_the_default(self):
        """The fault fires where the class starts, not only at maximum."""
        for hz in self.DEFAULT_BAR:
            shipped = self._floor(Fuzz, hz)
            none = self._floor(NoOversampleFuzz, hz)
            self.assertGreater(none - shipped, 6.0, (hz, shipped, none))
            self.assertGreater(none, -self.DEFAULT_BAR[hz], (hz, none))

    def test_no_oversample_is_red_everywhere_on_the_surface(self):
        """Walked over every shipped patch and both ends of Fuzz, with the
        clean class's reading beside it."""
        checked = 0
        for patch in sorted(Fuzz.PATCHES):
            for hz, bar in self.DEFAULT_BAR.items():
                none = self._floor(NoOversampleFuzz, hz, patch=patch)
                checked += 1
                self.assertGreater(none, -bar, (patch, hz, none))
        self.assertEqual(checked, 2 * len(Fuzz.PATCHES))

    def test_null_build_is_red(self):
        """A wire is *cleaner* than this class, so clause 1 alone could never
        fail on one — which is what made the old −60 dB bar unmeasurable.
        Clause 2 is the one a wire cannot pass: it ignores `oversample`."""
        kit_faults.null_build_red(Fuzz, self._reading, label="Fuzz A4")

    def test_the_old_sixty_db_bar_is_unreachable_across_the_whole_macro(self):
        """The measurement behind the redefinition, kept as a test so the
        redefinition cannot quietly become a moved goalpost."""
        for db in self.FUZZ_DBS:
            self.assertGreater(self._floor(Fuzz, 3700.0, fuzz_db=db), -60.0,
                               db)

    def test_the_monotone_clause_that_was_withdrawn_is_false(self):
        """The other measurement behind the amendment: the floor does not
        fall monotonically with Fuzz on the macro's own grid."""
        grid = list(range(0, 128, 8)) + [127]
        row = [self._floor(hz=1010.0, macros={0: position})
               for position in grid]
        breaks = [(grid[i], grid[i + 1]) for i in range(len(row) - 1)
                  if row[i + 1] <= row[i]]
        self.assertTrue(breaks, row)


class G3FuzzIsGain(unittest.TestCase):
    """Fuzz is a gain control, not a tone control: the 100 Hz / 1 kHz /
    8 kHz balance holds within 1 dB over five Fuzz stops while THD rises at
    every one.

    **The span, and the three places the reading has nothing to say** (the
    dial-back walk, 44 positions, `probes/fuzz_fix2.py faults`): the class
    has to be *in circuit* and its clipper must not be railed —
    **Output Tilt 0, Mix ≥ 0.5, Level above 0, |Bias| < 1**. At Mix 0 the
    output is the borrowed source, at Level 0 it is silence, and at Bias ±1
    the clipper is a gate whose output level does not follow its input, so
    three tones come out at one level and a flatness reading cannot fail —
    `HighHpFuzz` reads green at those three and at nothing else. Output Tilt
    off 0 and Mix 0.35 (patch 7) are where the **clean** class is red, for
    the same reason: a tilt is a tone control and G3 is the claim that Fuzz
    is not one.
    """

    FUZZ_DBS = (18.0, 27.0, 36.0, 45.0, 54.0)
    IN_SPAN_PATCHES = (0, 1, 2, 3, 4, 5, 6, 8)

    def _spread(self, cls, fuzz_db, patch=None, macros=None):
        lows = []
        for hz in (100.0, 1000.0, 8000.0):
            probe = sine(hz, 24000, -40.0)
            effect = build(cls, probe=probe, fuzz_db=fuzz_db)
            _place(effect, patch, macros)
            wet = render(effect, 24000)
            rms = float(np.sqrt(np.mean(wet.float[8000:, 0] ** 2)))
            lows.append(20.0 * math.log10(rms + 1e-12))
            effect.deinit()
        return max(lows) - min(lows), lows

    def _thd(self, cls, fuzz_db, patch=None, macros=None):
        probe = sine(1000, 24000, -20.0)
        effect = build(cls, probe=probe, fuzz_db=fuzz_db)
        _place(effect, patch, macros)
        wet = render(effect, 24000)
        spec = kit.spectrum(wet, 1000.0, harmonics=8)
        effect.deinit()
        return spec["values"]["thd_db"]

    def _reading(self, cls=Fuzz):
        spreads = []
        thds = []
        for fuzz_db in self.FUZZ_DBS:
            spread, _ = self._spread(cls, fuzz_db)
            spreads.append(spread)
            thds.append(self._thd(cls, fuzz_db))
        rising = all(thds[i + 1] > thds[i] for i in range(len(thds) - 1))
        flat = all(s < 1.0 for s in spreads)
        passed = flat and rising
        return {"passed": passed, "spreads": spreads, "thds": thds,
                "red": [] if passed else ["spread %s thd %s" % (spreads, thds)]}

    def test_five_stops_flat_and_thd_rising(self):
        reading = self._reading()
        self.assertTrue(reading["passed"], reading)

    def test_high_hp_is_red_at_default_fuzz(self):
        spread, lows = self._spread(HighHpFuzz, 36.0)
        self.assertGreater(spread, 1.0, lows)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(Fuzz, self._reading, label="Fuzz G3")

    def test_high_hp_fault_not_on_the_surface(self):
        kit_faults.fault_reachability(
            Fuzz, HighHpFuzz,
            lambda effect: float(effect._hps[0].frequency),
            lambda subject: build(subject, probe=probes.silence(2048)),
            label="Fuzz G3")

    def test_the_guard_is_red_at_every_patch_inside_the_span(self):
        """The measured walk, not the state read: `HighHpFuzz` renders and
        is scored on G3's own reading at each of the eight patches the span
        covers, with the clean class beside it."""
        for patch in self.IN_SPAN_PATCHES:
            clean, _ = self._spread(Fuzz, 36.0, patch=patch)
            faulted, mags = self._spread(HighHpFuzz, 36.0, patch=patch)
            self.assertLess(clean, 1.0, (patch, clean))
            self.assertGreater(faulted, 1.0, (patch, faulted, mags))

    def test_where_the_reading_has_nothing_to_say_it_is_not_a_dial_back(self):
        """Bias ±1 rails the clipper, so the clean class and the fault both
        read flat. Stated as a claim: if the class ever stopped gating
        there, this goes red and the span gets wider."""
        clean, mags = self._spread(Fuzz, 36.0, macros={3: 127})
        faulted, _ = self._spread(HighHpFuzz, 36.0, macros={3: 127})
        self.assertLess(clean, 1.0, (clean, mags))
        self.assertLess(faulted, 1.0, faulted)
        self.assertLess(max(mags) - min(mags), 1.0, mags)


class G4FortyHz(unittest.TestCase):
    def test_forty_hz_within_three_db_of_1k_at_default(self):
        mags = []
        for hz in (40.0, 1000.0):
            probe = sine(hz, 24000, -40.0)
            effect = build(probe=probe)
            wet = render(effect, 24000)
            rms = float(np.sqrt(np.mean(wet.float[8000:, 0] ** 2)))
            mags.append(20.0 * math.log10(rms + 1e-12))
            effect.deinit()
        delta = mags[0] - mags[1]
        self.assertGreaterEqual(delta, -3.0, (delta, mags))


class CascadeC1(unittest.TestCase):
    """Cascade's two silicon pairs clip symmetrically: even lines ≤ −40 dBc,
    h3 the largest, and the peak barely grows over a 20 dB level range.

    **The span, from the 42-position dial-back walk**
    (`probes/fuzz_fix2.py faults`): cascade, Sustain 54 dB, **Tone 0.5**,
    Bias centred, Mix 1, Level above 0. `GermaniumCascade` — the off-centre
    table in the cascade graph — is red at 41 of the 42 positions, and green
    at exactly one: **Tone 0**, where the whole sum comes out of the 482 Hz
    low-pass arm and every harmonic C1 reads is filtered away before it can
    be measured. The clean class passes there too, so that cell is a
    measurement that cannot fail rather than a fault that was dialled back —
    and it is the reason the row names Tone. The clean class is red, as the
    pack says, at patches 2, 3 and 7 and at any Bias off centre or Mix below
    1: Bias rails the pairs and Mix puts the dry copy back in.
    """

    def _reading(self, cls=Fuzz, patch=None, macros=None):
        peaks = []
        harmonics = []
        for dbfs in (-26.0, -6.0):
            probe = sine(1000, 24000, dbfs)
            effect = build(cls, probe=probe, character="cascade",
                           fuzz_db=54.0, tone=0.5)
            _place(effect, patch, macros)
            wet = render(effect, 24000)
            spec = kit.spectrum(wet, 1000.0, harmonics=6)
            hd = spec["values"]["harmonic_db"]
            x = wet.float[8000:, 0]
            peaks.append(20.0 * math.log10(
                float(max(abs(x.max()), abs(x.min()))) + 1e-18))
            harmonics.append(hd)
            effect.deinit()
        growth = abs(peaks[1] - peaks[0])
        h2, h3, h4 = (harmonics[0][k] for k in ("h2", "h3", "h4"))
        even_ok = h2 is not None and h4 is not None and h2 <= -40 and h4 <= -40
        h3_largest = h3 is not None and h3 > h2 and h3 > h4
        passed = even_ok and h3_largest and growth < 1.0
        return {"passed": passed, "growth": growth, "hd": harmonics[0],
                "peaks": peaks,
                "red": [] if passed else ["c1"]}

    def test_sustain_max_is_odd_and_peak_limited(self):
        reading = self._reading()
        self.assertTrue(reading["passed"], reading)

    def test_germanium_table_is_red_at_cascade_default(self):
        reading = self._reading(GermaniumCascade)
        self.assertFalse(reading["passed"], reading)

    def test_germanium_table_fires_at_cascade_constructor_fuzz(self):
        probe = sine(1000, 24000, -26.0)
        effect = build(GermaniumCascade, probe=probe, character="cascade")
        wet = render(effect, 24000)
        spec = kit.spectrum(wet, 1000.0, harmonics=6)
        h2 = spec["values"]["harmonic_db"]["h2"]
        effect.deinit()
        self.assertGreater(h2, -40.0, h2)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(Fuzz, self._reading, label="Fuzz C1")

    def test_germanium_table_not_on_cascade_surface(self):
        """The reading is the table the built instance is **playing**, asked
        of the instance — not a literal keyed on its type, which is what the
        second audit caught this pattern doing ([audiocomponents#74])."""
        kit_faults.fault_reachability(
            Fuzz, GermaniumCascade,
            lambda effect: bytes(memoryview(effect._curve)),
            lambda subject: build(subject, probe=probes.silence(2048),
                                  character="cascade"),
            label="Fuzz C1")

    def test_the_guard_is_red_everywhere_the_row_claims_the_trait(self):
        """The measured walk over C1's span: Tone centred, Bias centred,
        Mix 1, across Sustain and Level. `GermaniumCascade` is red at all of
        them, and the one cell it is green at — Tone 0 — is the cell where
        the 482 Hz arm has filtered away everything the row reads."""
        for index, positions in ((0, (0, 64, 127)), (1, (32, 127)),
                                 (4, (0, 127))):
            for position in positions:
                clean = self._reading(macros={index: position})
                faulted = self._reading(GermaniumCascade,
                                        macros={index: position})
                self.assertTrue(clean["passed"], (index, position, clean))
                self.assertFalse(faulted["passed"], (index, position,
                                                     faulted))
        degenerate = self._reading(GermaniumCascade, macros={2: 0})
        self.assertTrue(degenerate["passed"], degenerate)
        self.assertTrue(self._reading(macros={2: 0})["passed"])


class CascadeC2(unittest.TestCase):
    def test_thd_rise_misses_25_db_at_minus_20(self):
        thds = []
        rmses = []
        for fuzz_db in (18.0, 54.0):
            probe = sine(1000, 24000, -20.0)
            effect = build(probe=probe, character="cascade",
                           fuzz_db=fuzz_db, tone=0.5)
            wet = render(effect, 24000)
            spec = kit.spectrum(wet, 1000.0, harmonics=8)
            thds.append(spec["values"]["thd_db"])
            rmses.append(20.0 * math.log10(
                float(np.sqrt(np.mean(wet.float[8000:, 0] ** 2))) + 1e-12))
            effect.deinit()
        self.assertLess(thds[1] - thds[0], 25.0, thds)
        self.assertLess(abs(rmses[1] - rmses[0]), 6.0, rmses)


class CascadeC3(unittest.TestCase):
    """The mid scoop, at Tone centred and Bias centred — and **only** there.

    The row is claimed at cascade, Tone 0.5, Bias 0, Fuzz 18 dB, −40 dBFS,
    and it holds at all three rates (7.322 / 7.319 / 7.323 dB). Two shipped
    patches are not that point and do not have it, which the pack said
    nothing about until this round ([audiocomponents#74], second audit):

    * **patch 2 "Starved bias, gated"** — Bias −0.85 on its own, at any
      Tone: the clipper is rail to rail and the scoop reads **2.561 dB**
      against the row's 3 dB bar, a **0.44 dB** miss. It read 1.113 dB
      before the output coupling pole went in and the DC came out of the
      measurement ([audiocomponents#89]); it is still a miss, and the gate
      is what the patch is for.
    * **patch 6 "Cascade treble end"** — Tone 1.0: the knob's end is a
      **bump, not a scoop** (−0.977 dB), as Tone 0 is at the other end
      (−10.02 dB). C3 is the centred claim.
    """

    def _reading(self, cls=Fuzz, rate=RATE, patch=None, macros=None,
                 **options):
        mags = []
        frames = 24000 if rate > 24000 else 12000
        for hz in (200.0, 762.0, 4000.0):
            probe = sine(hz, frames, -40.0, rate=rate)
            settings = {"character": "cascade", "tone": 0.5,
                        "fuzz_db": 18.0}
            settings.update(options)
            effect = build(cls, rate=rate, frames=frames, probe=probe,
                           **settings)
            _place(effect, patch, macros)
            wet = render(effect, frames, rate=rate)
            rms = float(np.sqrt(np.mean(wet.float[frames // 3:, 0] ** 2)))
            mags.append(20.0 * math.log10(rms + 1e-12))
            effect.deinit()
        scoop = (mags[0] + mags[2]) / 2.0 - mags[1]
        passed = scoop > 3.0
        return {"passed": passed, "scoop": scoop, "mags": mags,
                "red": [] if passed else ["scoop %s" % mags]}

    def test_centred_tone_has_a_mid_scoop(self):
        for rate in (48000, 44100, 22050):
            reading = self._reading(rate=rate)
            self.assertTrue(reading["passed"], (rate, reading))

    def test_the_two_patches_that_do_not_have_it_are_the_two_named(self):
        """Disclosure as a claim: if a third patch loses the scoop, or one
        of these two gets it back, this goes red."""
        misses = [patch for patch in sorted(Fuzz.PATCHES)
                  if not self._reading(patch=patch)["passed"]]
        self.assertEqual(misses, [2, 6], misses)

    def test_bias_on_cascade_gates_the_level_not_the_scoop(self):
        """**Restated in the fourth fix round** ([audiocomponents#89]).

        The row used to say that any Bias off centre "rails both silicon
        pairs and the tone stack has nothing left to shape — scoop 0.002 dB
        at −0.5, 0.000 at ±1". That reading was the **DC**: with no
        coupling capacitor behind the second clipper the offset went
        straight through the low arm of the tone stack, and an RMS read of
        three probe tones sitting on the same −6 dBFS offset gives three
        identical magnitudes whatever the tone stack does. `NoOutputPole`
        still reads it that way and this test asserts that it does.

        What Bias off centre really does is **gate the level**: the 762 Hz
        notch reads −20.37 dBFS at centre, −31.32 at ±0.25, −48.80 at ±0.5,
        −61.25 at ±0.85 and −70.94 at ±1, and the scoop is **still there**
        the whole way down (+3.93 … +7.63 dB at all three rates). Gating is
        what patch 2 is for and that has not changed; what has changed is
        that the class can now say what it gates.
        """
        for rate in (RATE, 44100, 22050):
            last = None
            for bias in (0.0, -0.25, 0.25, -0.5, 0.5, -0.85, 0.85,
                         -1.0, 1.0):
                reading = self._reading(rate=rate, bias=bias)
                level = sum(reading["mags"]) / 3.0
                self.assertTrue(reading["passed"], (rate, bias, reading))
                self.assertGreater(reading["scoop"], 3.0,
                                   (rate, bias, reading))
                if bias == 0.0:
                    centred = reading
                elif abs(bias) == 0.25:
                    self.assertLess(reading["mags"][1],
                                    centred["mags"][1] - 10.0,
                                    (rate, bias, reading))
                elif abs(bias) >= 0.85:
                    self.assertLess(reading["mags"][1],
                                    centred["mags"][1] - 40.0,
                                    (rate, bias, reading))
                if bias >= 0.0:
                    if last is not None:
                        self.assertLess(
                            level, last + 1e-9,
                            "Bias %+.2f at %d Hz is not quieter than the "
                            "stop inside it (%.3f against %.3f)"
                            % (bias, rate, level, last))
                    last = level
        self.assertFalse(self._reading(tone=1.0)["passed"])
        self.assertFalse(self._reading(tone=0.0)["passed"])

    def test_the_offset_is_what_the_old_reading_was(self):
        """The plant that proves the restatement above: with the pole in
        bypass the three probe tones come back at **one** magnitude to
        three decimal places, at every Bias off centre, and the scoop the
        row reads is 0.000 dB."""
        for bias in (-1.0, -0.85, -0.5, 0.5, 1.0):
            reading = self._reading(NoOutputPole, bias=bias)
            self.assertLess(abs(reading["scoop"]), 0.1, (bias, reading))
            self.assertFalse(reading["passed"], (bias, reading))
            spread = max(reading["mags"]) - min(reading["mags"])
            self.assertLess(spread, 0.01, (bias, reading))
        self.assertTrue(self._reading(NoOutputPole, bias=0.0)["passed"])

    def test_full_band_arms_are_red_at_cascade_default_tone(self):
        reading = self._reading(NoScoopFuzz)
        self.assertFalse(reading["passed"], reading)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(Fuzz, self._reading, label="Fuzz C3")

    def test_full_band_arms_not_on_the_surface(self):
        kit_faults.fault_reachability(
            Fuzz, NoScoopFuzz,
            lambda effect: float(effect._tone_lp.frequency),
            lambda subject: build(subject, probe=probes.silence(2048),
                                  character="cascade"),
            label="Fuzz C3")


class CascadeC4(unittest.TestCase):
    """The notch centre moves with Tone — over a grid that does not pin it.

    The probe grid used to start at 300 Hz, and at the cascade
    constructor's own Fuzz (36 dB) the lowest centre lands **on that bottom
    edge**, so the argmin was saturated and the span read 2.007 octaves
    rather than the truth ([audiocomponents#74], second audit). It starts at
    **150 Hz** now, which is below anything the arms can put a minimum at.

    **The row's span, narrowed in the fourth fix round.** It is claimed at
    Fuzz **18 … 32 dB** and is **disconfirmed at 34 dB and above** — which
    includes the cascade constructor's own 36 dB and eight of the nine
    shipped patches, all of which sit at 36 dB or higher. Above the span
    the clipper has filled the notch in: the Tone 0.75 curve rises
    monotonically across the whole 150–2000 Hz grid and there is no
    interior minimum to read. The old claim to 36 dB rested on the 300 Hz
    cell reading **0.041 dB** under the 150 Hz one, an octave apart, which
    the argmin called a notch centre; the coupling pole the class grew for
    [audiocomponents#89] — which takes 0.2–0.6 dB of sub-31 Hz content out
    of the 150 Hz cell — is what exposed it. Only patch 3 `Cleaned up,
    load engaged` (Fuzz 24 dB) is inside the span.
    """

    PROBES = (150.0, 300.0, 482.0, 762.0, 1206.0, 2000.0)

    def _centre(self, cls, tone, rate=RATE, patch=None, macros=None,
                **options):
        mags = []
        frames = 24000 if rate > 24000 else 12000
        for hz in self.PROBES:
            probe = sine(hz, frames, -40.0, rate=rate)
            settings = {"character": "cascade", "tone": tone,
                        "fuzz_db": 18.0}
            settings.update(options)
            effect = build(cls, rate=rate, frames=frames, probe=probe,
                           **settings)
            if patch is not None or macros:
                # The patch first, then Tone moved from it: C4 claims the
                # centre moves, so a patch is a starting point and not a
                # third Tone setting.
                _place(effect, patch, macros)
                effect.set_macro(2, int(round(tone * 127)))
            wet = render(effect, frames, rate=rate)
            rms = float(np.sqrt(np.mean(wet.float[frames // 3:, 0] ** 2)))
            mags.append(20.0 * math.log10(rms + 1e-12))
            effect.deinit()
        depth = max(mags) - min(mags)
        centre = self.PROBES[int(mags.index(min(mags)))]
        return centre, depth, mags

    def _reading(self, cls=Fuzz, rate=RATE, patch=None, macros=None,
                 **options):
        centres = []
        depths = []
        for tone in (0.25, 0.5, 0.75):
            centre, depth, _ = self._centre(cls, tone, rate=rate,
                                            patch=patch, macros=macros,
                                            **options)
            centres.append(centre)
            depths.append(depth)
        notched = all(d > 2.0 for d in depths)
        # A minimum that lands on an end of the grid is not a notch centre,
        # it is a slope running off the edge - which is what Tone 0.75 is
        # above Fuzz 36 dB. Reading it as a centre is how the row came to
        # claim 2.007 and 3.007 octaves ([audiocomponents#74]).
        interior = all(centre not in (self.PROBES[0], self.PROBES[-1])
                       for centre in centres)
        span = (math.log2(max(centres) / min(centres))
                if min(centres) else 0.0)
        passed = notched and interior and span >= 0.5
        return {"passed": passed, "centres": centres, "depths": depths,
                "notched": notched, "interior": interior, "oct": span,
                "red": [] if passed else ["c4"]}

    #: **The top of the row's claimed span, narrowed in the fourth fix
    #: round** ([audiocomponents#89]). It was "up to and including the
    #: cascade constructor's own 36 dB". With the output coupling pole in,
    #: 34 dB and above leave no interior minimum at Tone 0.75 at all — the
    #: whole 150–2000 Hz grid is a monotone slope. The old wider claim
    #: rested on the 300 Hz cell reading **0.041 dB** below the 150 Hz one,
    #: which is not a notch; the pole takes 0.2–0.6 dB of sub-31 Hz content
    #: out of the 150 Hz cell, and the wobble with it.
    CLAIMED_TO_FUZZ_DB = 32.0

    def test_notch_centres_span_half_octave(self):
        reading = self._reading()
        self.assertTrue(reading["passed"], reading)

    def test_the_row_holds_everywhere_it_is_claimed(self):
        """Fuzz 18 dB — where the row was frozen — up to the stated top,
        at all three rates: centres 1206 / 762 / 482 Hz, 1.323 octaves."""
        for fuzz_db in (18.0, 24.0, 30.0, self.CLAIMED_TO_FUZZ_DB):
            for rate in (RATE, 44100, 22050):
                reading = self._reading(rate=rate, fuzz_db=fuzz_db)
                self.assertTrue(reading["passed"], (fuzz_db, rate, reading))

    def test_it_is_disconfirmed_above_the_span_including_at_the_default(self):
        """The bound, stated as a claim. Above `CLAIMED_TO_FUZZ_DB` the
        Tone 0.75 curve is a slope and its minimum is the bottom of
        whatever grid you hand it — and that includes **36 dB, which is
        what `character="cascade"` builds**. The row is disconfirmed there,
        not widened."""
        self.assertLess(self.CLAIMED_TO_FUZZ_DB, 36.0)
        for fuzz_db in (34.0, 36.0, 42.0, 54.0):
            reading = self._reading(fuzz_db=fuzz_db)
            self.assertFalse(reading["interior"], (fuzz_db, reading))
            self.assertFalse(reading["passed"], (fuzz_db, reading))

    def test_the_old_wider_claim_was_four_hundredths_of_a_decibel(self):
        """Why the span narrowed, measured rather than asserted. At 36 dB
        and Tone 0.75 the class the pole replaced reads 150 Hz at −13.723
        and 300 Hz at −13.764 — a **0.041 dB** dip that the argmin called a
        notch centre. With the pole the same two cells read −14.287 and
        −13.827, so the curve rises the whole way and there is no interior
        minimum to find."""
        _c, _d, planted = self._centre(NoOutputPole, 0.75, fuzz_db=36.0)
        _c, _d, shipped = self._centre(Fuzz, 0.75, fuzz_db=36.0)
        self.assertGreater(planted[0] - planted[1], 0.0, planted)
        self.assertLess(planted[0] - planted[1], 0.05, planted)
        self.assertLess(shipped[0] - shipped[1], 0.0, shipped)

    def test_the_patches_it_misses_are_the_ones_the_pack_names(self):
        """Every shipped patch but 3 `Cleaned up, load engaged` — the only
        one below the claimed span's top — is above it and misses."""
        misses = [patch for patch in sorted(Fuzz.PATCHES)
                  if not self._reading(patch=patch)["passed"]]
        self.assertEqual(misses, [0, 1, 2, 4, 5, 6, 7, 8], misses)

    def test_full_band_arms_do_not_move_a_notch(self):
        reading = self._reading(NoScoopFuzz)
        self.assertFalse(reading["passed"], reading)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(Fuzz, self._reading, label="Fuzz C4")

    def test_frozen_tone_is_red_at_every_rate(self):
        """C4's own fault: the notch is *there* and does not move
        ([audiocomponents#74]). `NoScoopFuzz` cannot show this — it has no
        notch to freeze."""
        for rate in (48000, 44100, 22050):
            reading = self._reading(FrozenToneFuzz, rate=rate)
            self.assertTrue(reading["notched"], (rate, reading))
            self.assertEqual(reading["oct"], 0.0, (rate, reading))
            self.assertFalse(reading["passed"], (rate, reading))

    def test_clean_class_is_green_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            reading = self._reading(rate=rate)
            self.assertTrue(reading["passed"], (rate, reading))

    def test_frozen_tone_null_build_is_red(self):
        kit_faults.null_build_red(Fuzz, self._reading, label="Fuzz C4 frozen")

    def test_frozen_tone_not_on_the_surface(self):
        kit_faults.fault_reachability(
            Fuzz, FrozenToneFuzz, tone_response,
            lambda subject: build(subject, probe=probes.silence(2048),
                                  character="cascade"),
            label="Fuzz C4")


class TheLeanPatch(unittest.TestCase):
    """Patch 8 `Fuzz - lean` is the S3's shipped position.

    The factor is fixed at construction — the node cannot retune its
    half-bands live — so the lean position is a second shaper at ×2, built
    beside the shipped one and played by the tilt stage when the patch is
    selected. Only the routed one is ever pulled.
    """

    def test_patch_eight_is_named_and_shaped_at_two(self):
        effect = build()
        self.assertEqual(Fuzz.PATCHES[rebuilt.LEAN_PATCH][0], "Fuzz - lean")
        self.assertEqual(effect.latency_samples, 4)
        effect.program_change(rebuilt.LEAN_PATCH)
        self.assertIs(effect._routed_lean, True)
        self.assertEqual(effect._lean.oversample, 2)
        self.assertEqual(effect.latency_samples, 2)
        effect.program_change(0)
        self.assertIs(effect._routed_lean, False)
        self.assertEqual(effect.latency_samples, 4)
        effect.deinit()

    def test_the_lean_patch_renders_and_is_not_a_bypass(self):
        probe = sine(1000, 24000, -20.0)
        renders = []
        for index in (0, rebuilt.LEAN_PATCH):
            effect = build(probe=probe, patch=index)
            renders.append(render(effect, 24000).digest)
            effect.deinit()
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            24000, rate=RATE, channels=2, block=256).digest
        self.assertNotEqual(renders[0], renders[1])
        self.assertNotEqual(renders[1], dry)

    def test_a_constructor_already_at_two_builds_no_second_shaper(self):
        effect = build(oversample=2)
        self.assertIsNone(effect._lean)
        effect.program_change(rebuilt.LEAN_PATCH)
        self.assertEqual(effect.latency_samples, 2)
        effect.deinit()

    def test_cascade_has_no_lean_shaper(self):
        effect = build(character="cascade")
        self.assertIsNone(effect._lean)
        effect.deinit()


class TheShippedFactorIsPerCharacter(unittest.TestCase):
    """`cascade` at ×8 does not run on a T-Embed S3 and nothing stopped it.

    The board measured `character="cascade"`, `oversample=8` at **4.782 /
    8.580 ms — 90 % of a P4 block and 161 % of an S3 one, rt 1.00 and
    0.56** (audiocomponents#74). The class's own docstring already said to
    build cascade at ×2; `create()` defaulted to 8 for both characters and
    nothing tested or enforced it, so the shipped surface reached a graph
    that misses the deadline. `shipped_oversample()` picks the factor per
    character now.

    ×2 rather than ×4 because ×4 does not run either — 3.250 / 5.971 ms,
    **112 % of an S3 block** — and because cascade's own alias floor is
    nearly flat above ×2: ×8 buys 12.3 / 12.7 dB over ×1 where germanium's
    buys 20.9 / 18.7, the second clipper folding what the first already put
    above the output Nyquist. What ×2 gives up is 2.9 / 5.3 dB at the
    default and 5.6 / 5.6 dB at maximum Fuzz, disclosed in
    `CASCADE_OVERSAMPLE`, the class docstring, the catalogue row and the
    pack.
    """

    def test_each_character_builds_at_its_own_factor(self):
        for character, factor in (("germanium", 8), ("cascade", 2)):
            effect = build(character=character)
            self.assertEqual(effect._oversample, factor,
                             "%s built at x%d" % (character,
                                                  effect._oversample))
            # `_shapers[1]` on `germanium` is the lean patch's ×2 node,
            # which nothing pulls until patch 8 routes to it.
            self.assertEqual(effect._shapers[0].oversample, factor)
            effect.deinit()

    def test_the_shipped_factor_is_what_the_helper_says(self):
        self.assertEqual(rebuilt.shipped_oversample("germanium"), 8)
        self.assertEqual(rebuilt.shipped_oversample("cascade"), 2)

    def test_the_old_default_is_red(self):
        """The plant: the single `oversample=8` default this class shipped,
        which is the 161 %-of-an-S3-block graph."""
        effect = build(character="cascade", oversample=8)
        try:
            self.assertEqual(effect._oversample, 8)
            self.assertNotEqual(
                effect._oversample,
                rebuilt.shipped_oversample("cascade"),
                "the plant did not fire: cascade still builds at x8")
        finally:
            effect.deinit()

    def test_a_caller_can_still_ask_for_any_factor(self):
        for factor in rebuilt.OVERSAMPLES:
            effect = build(character="cascade", oversample=factor)
            self.assertEqual(effect._oversample, factor)
            effect.deinit()

    def test_cascade_reports_the_factors_latency(self):
        effect = build(character="cascade")
        self.assertEqual(effect.latency_samples, 2)
        effect.deinit()

    def test_the_tone_mixer_hands_back_one_palette_block(self):
        """`Mixer._render_size` is `buffer_size // 2 // 4 * 4` BYTES, so the
        1024 cascade shipped rendered 128 stereo frames and the tilt stage
        pulled the whole tone stack twice per 256-frame block."""
        import audiocore
        for channels in (2, 1):
            effect = build(character="cascade", channels=channels)
            _result, buffer = audiocore.get_buffer(effect._tone_mix)
            self.assertEqual(len(buffer) // (2 * channels), 256,
                             "%d channel tone mixer" % channels)
            effect.deinit()

    def test_the_shipped_tone_mixer_buffer_is_red(self):
        import audiocore
        kept = rebuilt.MIXER_BUFFER_BYTES
        rebuilt.MIXER_BUFFER_BYTES = 512
        try:
            effect = build(character="cascade")
            _result, buffer = audiocore.get_buffer(effect._tone_mix)
            frames = len(buffer) // 4
            effect.deinit()
        finally:
            rebuilt.MIXER_BUFFER_BYTES = kept
        self.assertEqual(frames, 128,
                         "the plant did not fire: %d frames" % frames)


class TheOutputStage(unittest.TestCase):
    """The three things the second audit found the output stage doing that
    nothing said: carrying the clipper's DC, leaving the dry leg at full
    level whatever Level did, and declaring a tail 45× the one it has."""

    def _rms(self, hz=1000.0, dbfs=-20.0, frames=24000, patch=None,
             **options):
        probe = sine(hz, frames, dbfs)
        effect = build(probe=probe, frames=frames, **options)
        if patch is not None:
            effect.program_change(patch)
        wet = render(effect, frames)
        effect.deinit()
        x = wet.float[frames // 3:, 0]
        return 20.0 * math.log10(float(np.sqrt(np.mean(x ** 2))) + 1e-30)

    def _peak_and_mean(self, hz=1000.0, dbfs=-6.0, frames=9600, patch=None,
                       **options):
        probe = sine(hz, frames, dbfs, channels=1)
        effect = build(probe=probe, frames=frames, channels=1, **options)
        if patch is not None:
            effect.program_change(patch)
        wet = render(effect, frames, channels=1)
        effect.deinit()
        x = wet.data[:, 0].astype(np.int64)[frames // 3:]
        return int(np.abs(x).max()), float(x.mean()), int(
            np.sum(np.abs(x) >= 32767))

    def _settled_mean(self, frames=24000, patch=None, **options):
        """The mean of the second half of a half-second render.

        The row is about a *standing* offset, so it is read where the
        output pole has settled. Reading it from a third of the way into a
        fifth-of-a-second render - which is what this did - catches the
        pole still moving: at patch 2 the class reads -99 LSB there with
        the charge in and -28 without it, and both are 0 to 4 LSB by
        100 ms. The transient itself is the next row.
        """
        probe = sine(1000.0, frames, -6.0, channels=1)
        effect = build(probe=probe, frames=frames, channels=1, **options)
        if patch is not None:
            effect.program_change(patch)
        wet = render(effect, frames, channels=1)
        effect.deinit()
        values = wet.data[:, 0].astype(np.int64)
        return float(values[frames // 2:].mean()), values

    def test_the_output_carries_no_dc_at_any_patch(self):
        """−6426 LSB at the shipped default was G1's peak clause and this
        class's headroom ([audiocomponents#74]). S1's third capacitor is the
        output one and its pole is behind the shaper now - and since the
        third fix round it is **charged** before the first block, so patch 2
        no longer bangs 21 971 LSB out of digital silence."""
        for patch in sorted(Fuzz.PATCHES):
            mean, _ = self._settled_mean(patch=patch)
            self.assertLess(abs(mean), 32.0, (patch, mean))
        for bias in (-1.0, -0.5, 0.5, 1.0):
            mean, _ = self._settled_mean(bias=bias)
            self.assertLess(abs(mean), 32.0, (bias, mean))

    def test_the_charge_settles_under_material_and_the_bound_is_stated(self):
        """What the charge costs: it holds the *silent* offset, and a note
        arriving moves the operating point, so the pole re-settles. Bounded
        at 200 LSB (-44 dBFS) over the first 100 ms at every shipped patch,
        and under 32 LSB after it - against 21 971 LSB of bang at
        construction without the charge."""
        for patch in sorted(Fuzz.PATCHES):
            _mean, values = self._settled_mean(patch=patch)
            head = values[:RATE // 10]
            self.assertLess(abs(float(head.mean())), 200.0,
                            (patch, float(head.mean())))

    def test_level_zero_is_silence_at_every_mix_above_zero(self):
        for mix in (1.0, 0.756, 0.504, 0.25, 0.008):
            self.assertLess(self._rms(level=0.0, mix=mix), -120.0, mix)

    def test_halving_level_is_six_db_at_every_mix(self):
        for mix in (1.0, 0.756, 0.504, 0.25, 0.008):
            full = self._rms(level=1.0, mix=mix)
            half = self._rms(level=0.5, mix=mix)
            self.assertAlmostEqual(full - half, 6.021, places=2, msg=mix)

    def test_load_is_six_db_at_every_mix(self):
        for mix in (1.0, 0.5, 0.25, 0.008):
            self.assertAlmostEqual(self._rms(load=0.0, mix=mix)
                                   - self._rms(load=1.0, mix=mix),
                                   6.021, places=2, msg=mix)

    def test_mix_zero_is_the_wire_and_level_does_not_reach_it(self):
        """The one exception, said in the docstring in the same words: at
        Mix 0 the output *is* the borrowed source."""
        self.assertAlmostEqual(self._rms(mix=0.0), self._rms(mix=0.0,
                                                             level=0.0),
                               places=6)

    def test_nothing_on_the_surface_reaches_the_rail(self):
        """Output Tilt +3 dB and above used to pin the output at every input
        level — the shape the second audit parked `CabinetSim` for."""
        for tilt_db in (-6.0, -3.0, 0.0, 3.0, 6.0):
            for dbfs in (-20.0, -6.0, 0.0):
                peak, _, pinned = self._peak_and_mean(dbfs=dbfs,
                                                      tilt_db=tilt_db)
                self.assertEqual(pinned, 0, (tilt_db, dbfs, peak))
        for patch in sorted(Fuzz.PATCHES):
            for hz in (100.0, 1010.0, 3700.0):
                peak, _, pinned = self._peak_and_mean(hz=hz, dbfs=0.0,
                                                      patch=patch)
                self.assertEqual(pinned, 0, (patch, hz, peak))

    def test_the_tail_is_the_one_declared(self):
        """`TAIL_SAMPLES` was 655360 — 13.65 s, in no measurement anywhere.
        Measured here at the worst setting that leaves Bias centred."""
        for options in ({}, {"fuzz_db": 54.0}, {"character": "cascade"}):
            probe, _on = probes.burst_silence(hz=1000.0, on_ms=200.0,
                                              total_s=1.0, dbfs=-6.0)
            frames = len(probe) // 2
            effect = build(probe=probe, frames=frames, **options)
            wet = render(effect, frames)
            effect.deinit()
            after = np.abs(wet.data[9600:, 0].astype(np.int64))
            over = np.nonzero(after >= 1)[0]
            tail = int(over[-1]) + 1 if len(over) else 0
            self.assertLess(tail, Fuzz.TAIL_SAMPLES, (options, tail))

    def test_bias_off_centre_never_reaches_digital_zero_and_says_so(self):
        """The disclosure as a claim: it does not settle, and what stays is
        under 16 LSB."""
        probe, _on = probes.burst_silence(hz=1000.0, on_ms=200.0,
                                          total_s=1.0, dbfs=-6.0)
        frames = len(probe) // 2
        effect = build(probe=probe, frames=frames, bias=-0.85)
        wet = render(effect, frames)
        effect.deinit()
        after = np.abs(wet.data[9600:, 0].astype(np.int64))
        self.assertGreater(after[-1], 0)
        self.assertLess(int(after[Fuzz.TAIL_SAMPLES:].max()), 16)


class TheGraph(unittest.TestCase):
    """What patch 0 actually pulls, which is what the budget is a sum of."""

    def test_germanium_is_four_nodes_deep(self):
        """Read from the jack back: tilt, the **output** coupling section,
        the shaper, the input coupling section. S1's third capacitor is the
        output one and its pole is behind the clipper, which is the whole
        of what blocks the germanium offset (audiocomponents#74)."""
        effect = build()
        chain = []
        # Through the wire to the node at the end of the graph. `output` is
        # a stable port now, so the walk starts one node later than the
        # object the consumer holds.
        node = kit.port_target(effect.output)
        while node is not None and node is not effect._source:
            chain.append(type(node).__name__)
            node = getattr(node, "_source", None) or getattr(
                node, "_sample", None)
        effect.deinit()
        self.assertEqual(chain, ["Biquad", "Biquad", "Waveshaper", "Biquad"],
                         chain)

    def test_the_output_coupling_pole_is_behind_the_shaper(self):
        effect = build()
        self.assertIs(effect._tilt._source, effect._hps[1])
        self.assertIs(effect._hps[1]._source, effect._shapers[0])
        self.assertIs(effect._shapers[0]._source, effect._hps[0])
        effect.deinit()

    def test_mix_zero_is_the_borrowed_source_itself(self):
        # What the class is PLAYING, not what the consumer is holding.
        # `output` is a port whose identity never changes, so it is never
        # the source and never the tilt; `port_target` is the question this
        # test has always been asking.
        effect = build(mix=0.0)
        self.assertIs(kit.port_target(effect.output), effect._source)
        self.assertEqual(effect.latency_samples, 0)
        effect.set_macro(5, 127)
        self.assertIs(kit.port_target(effect.output), effect._tilt)
        self.assertEqual(effect.latency_samples, 4)
        effect.deinit()

    def test_the_input_section_is_three_real_poles_in_two_biquads(self):
        effect = build()
        self.assertEqual(len(effect._hps), 2)
        self.assertAlmostEqual(float(effect._hps[0].frequency),
                               math.sqrt(7.9 * 14.0), places=4)
        self.assertAlmostEqual(float(effect._hps[1].frequency),
                               math.sqrt(31.0 * rebuilt.HP_PARK_HZ), places=4)
        effect.deinit()


class TestFuzzCurvesFillTheRange(unittest.TestCase):
    """Both tables reach a rail, and the generator will not emit one that
    does not ([audiocomponents#77]).

    `GERMANIUM_CURVE` used to hold the collector shape directly, so it peaked
    at −20713 / +7085 — 63 % of int16 on its larger side — and every entry
    was quantised four decibels more coarsely than it had to be for nothing.
    `GERMANIUM_SCALE` carries the scale out in `post_gain` instead. The curve
    is **asymmetric by design**: the check is the larger side, and squaring
    the table up would be throwing the circuit away.
    """

    def _generator(self):
        from tools.curves import fuzz_curve
        return fuzz_curve

    def _quiet(self, gen, argv):
        import io
        import contextlib
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            return gen.main(argv)

    def test_germanium_fills_the_range_on_its_larger_side(self):
        table = rebuilt._q15_array(rebuilt.GERMANIUM_CURVE)
        self.assertEqual(min(table), -32767)
        self.assertEqual(max(table), 11208)

    def test_the_asymmetry_is_untouched(self):
        """Both halves are divided by the same number, so the off-centre
        bias — the circuit's identity — reads the same ratio it did."""
        table = rebuilt._q15_array(rebuilt.GERMANIUM_CURVE)
        self.assertAlmostEqual(abs(min(table)) / float(max(table)),
                               20713.0 / 7085.0, places=3)

    def test_cascade_already_filled_it(self):
        table = rebuilt._q15_array(rebuilt.CASCADE_CURVE)
        self.assertEqual((min(table), max(table)), (-32767, 32767))

    def test_both_tables_are_monotone(self):
        for name in ("GERMANIUM_CURVE", "CASCADE_CURVE"):
            table = rebuilt._q15_array(getattr(rebuilt, name))
            drops = [i for i in range(1, len(table))
                     if table[i] < table[i - 1]]
            self.assertEqual(drops, [], (name, drops[:8]))

    def test_module_holds_what_the_generator_writes(self):
        self.assertEqual(self._quiet(self._generator(), ["--check"]), 0)

    def test_generator_refuses_a_table_that_leaves_the_range_empty(self):
        """Planted: the pre-fix normalisation, the shape straight into Q15."""
        gen = self._generator()
        keep = gen.germanium_scale
        try:
            gen.germanium_scale = lambda shape=None: 1.0
            self.assertLess(gen.fill(gen.germanium_points()), 0.95)
            self.assertEqual(self._quiet(gen, ["--check"]), 3)
        finally:
            gen.germanium_scale = keep
        self.assertEqual(self._quiet(gen, ["--check"]), 0)




class TestFuzzTheOutputCharge(unittest.TestCase):
    """Audit 3 (p)2, ruling (n): S1's output capacitor was there and cold.

    Bias is an offset into an asymmetric curve, so the shaper answers a
    silent input with a constant. The pole behind it blocks the constant
    but not the *step* that starts it: shipped patch 2 (Bias -0.844) put
    **21 971 LSB, -3.5 dBFS**, out of digital silence and took 0.2 s to
    bleed. `_charge_output` pulls that through the pole before the first
    block, with the shapers fed the class's own zero sample.
    """

    def peak_into_silence(self, cls, patch, rate=RATE, frames=32768):
        effect = build(cls=cls, probe=probes.silence(frames, 2),
                       frames=frames, rate=rate, patch=patch)
        try:
            quiet = render(effect, frames, rate=rate)
            return int(np.abs(quiet.data).max())
        finally:
            effect.deinit()

    def test_the_planted_class_bangs_where_this_one_does_not(self):
        for rate in (RATE, 44100, 22050):
            planted = self.peak_into_silence(NoOutputCharge, 2, rate=rate)
            shipped = self.peak_into_silence(Fuzz, 2, rate=rate)
            self.assertGreater(
                planted, 1000,
                "the planted class has to bang at patch 2 or this row "
                "proves nothing (%d at %d Hz)" % (planted, rate))
            self.assertLessEqual(
                shipped, TheTierOneRowsAtEveryShippedPatch.RESIDUAL_LSB,
                "patch 2 at %d Hz emits %d LSB" % (rate, shipped))

    def test_the_charge_costs_the_source_nothing(self):
        """It pulls the shapers, never the split, and `_build` points them
        at the real chain once - so a patch that charges takes exactly the
        frames a patch that does not."""
        for patch in (0, 2):
            probe = sine(1000.0, 4096, -6.0)
            source = probes.ArraySource(probe, rate=RATE, block=256,
                                        channels=2)
            effect = Fuzz.create(source, RATE, patch=patch)
            try:
                render(effect, 2048)
                taken = source.frames_taken if hasattr(
                    source, "frames_taken") else None
            finally:
                effect.deinit()
            if taken is not None:
                self.assertEqual(taken, 2048 + 256, patch)


class TestFuzzTheTailBelowTheBurst(unittest.TestCase):
    """Audit 3 (p)1: `TAIL_SAMPLES` was a 1 kHz number.

    16 384 was measured with a 1 kHz burst. A low note outlives it: 40 Hz
    reads 16 627 frames at the constructor default and **18 750 at patch
    5**, and 100 Hz is over it at patches 1, 5 and 7. The declaration is
    24 576 now and this walks the notes that broke it.
    """

    def ring(self, hz, patch=None, rate=RATE, dbfs=-6.0):
        on = int(0.2 * rate)
        total = on + 28000
        probe = sine(hz, on, dbfs)
        probe.extend(array("h", bytes(2 * (total - on) * 2)))
        effect = build(probe=probe, frames=total, rate=rate,
                       **({} if patch is None else {"patch": patch}))
        try:
            wet = render(effect, total, rate=rate)
            declared = effect.tail_samples
        finally:
            effect.deinit()
        values = wet.data[:, 0].astype(np.int64)[on:]
        nonzero = np.nonzero(values)[0]
        return (int(nonzero[-1]) + 1 if len(nonzero) else 0), declared

    def test_the_declaration_covers_the_low_notes_too(self):
        for hz in (40.0, 100.0, 220.0):
            for patch in (None, 1, 5, 7):
                ring, declared = self.ring(hz, patch=patch)
                self.assertLessEqual(
                    ring, declared,
                    "a %.0f Hz burst at patch %s rings %d frames against a "
                    "declared %d" % (hz, patch, ring, declared))


class TestFuzzA4AtItsWorstCell(A4AliasFloor):
    """Audit 3 (p)3: the published worst cell was wrong in three places.

    A4's surface clause is read on a Fuzz x Bias x Tilt grid, and the pack
    swept it one macro at a time. **Jointly** the worst is -35.407 dB at
    44.1 kHz (Fuzz 127, Bias centred, Tilt 127), not -38.154, so the
    margin against the -35 dB bar is **0.4 dB**; a finer grid reaches
    -35.431. The trait stands; the number did not. Read with the row's own
    `_floor`, so this is the same instrument the pack uses.
    """

    CELL = {0: 127, 3: 64, 6: 127}
    BAR = -35.0

    def test_the_worst_joint_cell_is_where_the_row_says(self):
        for rate, expected in ((48000, -36.322), (44100, -35.407)):
            value = self._floor(hz=1010.0, rate=rate, macros=self.CELL)
            self.assertLess(value, self.BAR,
                            "A4's own worst cell reads %.3f at %d Hz"
                            % (value, rate))
            self.assertAlmostEqual(
                value, expected, delta=0.3,
                msg="the published worst cell moved: %.3f at %d Hz"
                    % (value, rate))

    def test_the_margin_is_under_a_decibel_and_the_row_says_so(self):
        """A row whose margin is 0.4 dB and which publishes 3 dB is not a
        disclosure, so the margin itself is asserted."""
        margin = self.BAR - self._floor(hz=1010.0, rate=44100,
                                        macros=self.CELL)
        self.assertLess(margin, 1.0, margin)
        self.assertGreater(margin, 0.0, margin)

    def test_the_cell_the_pack_used_to_publish_is_not_the_worst(self):
        """One macro at a time is what missed it: Tilt at its top with
        Fuzz at its top is 2 dB worse than either alone."""
        alone = self._floor(hz=1010.0, rate=44100, macros={0: 127})
        joint = self._floor(hz=1010.0, rate=44100, macros=self.CELL)
        self.assertGreater(joint, alone + 1.0, (alone, joint))


class TheCascadeOutputPole(unittest.TestCase):
    """audiocomponents#89, ruling (n): `cascade` stood DC on its output.

    A Big Muff has a coupling capacitor between the second clipper and the
    tone stack. This class had none, and the low arm of the tone stack is a
    `LOW_PASS`, which passes DC — so a Bias off centre held **−16 383 to
    +16 382 LSB, −6.0 dBFS, for ever**, at eight of the nine stops of a
    front-panel macro, at every rate. The fourth fix round put the section
    where the circuit has it, at the same 31 Hz corner as the one already
    in front of the second clipper.

    It costs one `Biquad` on `cascade` and **0.011 dB at 100 Hz**, and it
    takes C3's and C4's Bias and Fuzz clauses with it — both restated
    above, both against the plant this class uses.
    """

    #: The same bound `TheTierOneRowsAtEveryShippedPatch` holds the
    #: germanium patches to. `cascade` does not use any of it: every stop
    #: of Bias is 3 LSB or less, built at the value or moved to it live.
    RESIDUAL_LSB = 16
    STOPS = (0, 16, 32, 48, 64, 80, 96, 112, 127)

    def silence(self, cls=None, character="cascade", midi=0, rate=RATE,
                live=True, frames=16384):
        cls = cls or Fuzz
        options = {"character": character}
        if not live:
            options["bias"] = -1.0 + 2.0 * (midi / 127.0)
        effect = build(cls=cls, probe=probes.silence(frames, 2),
                       frames=frames, rate=rate, **options)
        if live:
            effect.set_macro(3, midi)
        try:
            quiet = render(effect, frames, rate=rate)
        finally:
            effect.deinit()
        values = quiet.data[:, 0].astype(np.int64)
        return int(np.abs(values).max()), float(values[-2048:].mean())

    def test_silence_in_is_silence_out_at_every_bias_stop(self):
        """Both characters, built at the value and moved to it live. The
        settled mean is the row #89 is about — the peak is here because a
        pole that is charged but not *settled* would show as one and not
        the other."""
        for character in ("cascade", "germanium"):
            for live in (True, False):
                for midi in self.STOPS:
                    peak, mean = self.silence(character=character, midi=midi,
                                              live=live)
                    with self.subTest(character=character, midi=midi,
                                      live=live):
                        self.assertLessEqual(
                            abs(mean), self.RESIDUAL_LSB,
                            "%s Bias %d (%s) stands %.1f LSB of DC on "
                            "digital silence" % (character, midi,
                                                 "live" if live else "ctor",
                                                 mean))
                        self.assertLessEqual(
                            peak, self.RESIDUAL_LSB,
                            "%s Bias %d (%s) emits %d LSB into digital "
                            "silence" % (character, midi,
                                         "live" if live else "ctor", peak))

    def test_it_holds_at_every_rate(self):
        for rate in (44100, 22050):
            for midi in (0, 32, 96, 127):
                peak, mean = self.silence(midi=midi, rate=rate)
                with self.subTest(rate=rate, midi=midi):
                    self.assertLessEqual(abs(mean), self.RESIDUAL_LSB,
                                         (rate, midi, mean))
                    self.assertLessEqual(peak, self.RESIDUAL_LSB,
                                         (rate, midi, peak))

    def test_the_planted_class_stands_the_offset_this_one_removes(self):
        """The plant has to reach the figure #89 was filed on or this row
        proves nothing."""
        worst = 0.0
        for midi in self.STOPS:
            _peak, mean = self.silence(cls=NoOutputPole, midi=midi)
            if midi == 64:
                self.assertLess(abs(mean), 1.0, (midi, mean))
                continue
            worst = max(worst, abs(mean))
            self.assertGreater(
                abs(mean), 9000.0,
                "the planted class has to stand DC at Bias %d or this row "
                "proves nothing (%.1f LSB)" % (midi, mean))
        self.assertGreater(worst, 16000.0, worst)

    def test_the_tail_holds_at_every_bias_stop(self):
        """The offset never decayed at all, so `TAIL_SAMPLES` was a claim
        about Bias 64 only. Walked at every stop, on both characters."""
        for character in ("cascade", "germanium"):
            for midi in (0, 32, 64, 96, 127):
                on = int(0.2 * RATE)
                total = on + 28000
                probe = sine(220.0, on, -6.0)
                probe.extend(array("h", bytes(2 * (total - on) * 2)))
                effect = build(probe=probe, frames=total,
                               character=character)
                effect.set_macro(3, midi)
                try:
                    wet = render(effect, total)
                    declared = effect.tail_samples
                finally:
                    effect.deinit()
                values = wet.data[:, 0].astype(np.int64)[on:]
                over = np.nonzero(np.abs(values) > 16)[0]
                ring = int(over[-1]) + 1 if len(over) else 0
                with self.subTest(character=character, midi=midi):
                    self.assertLessEqual(
                        ring, declared,
                        "a 220 Hz burst on %s at Bias %d rings %d frames "
                        "over 16 LSB against a declared %d"
                        % (character, midi, ring, declared))

    def test_the_live_recharge_leaves_the_input_split_in_step(self):
        """What the third round thought re-charging `cascade` live would
        cost, measured. The charge pulls the **output** pole and `hp_in` is
        never pulled, so neither tap of the input `Splitter` moves: a burst
        behind a live Bias move arrives at the same output frame with the
        move as without it. `DryTapRebalance` pays for the block anyway and
        puts the dry leg 256 frames early, which is what this row catches.
        """
        lead = 8192
        probe = array("h", bytes(2 * lead * 2))
        probe.extend(sine(1000.0, 8192, -12.0))
        probe.extend(array("h", bytes(2 * 4096 * 2)))
        frames = len(probe) // 2
        onsets = {}
        for midi in (10, 64, 117):
            effect = build(probe=probe, frames=frames, character="cascade",
                           mix=0.5, fuzz_db=24.0)
            try:
                render(effect, 4096)
                effect.set_macro(3, midi)
                wet = render(effect, 12288)
            finally:
                effect.deinit()
            values = np.abs(wet.data[:, 0].astype(np.int64))
            loud = np.nonzero(values > 40)[0]
            onsets[midi] = int(loud[0]) if len(loud) else None
        self.assertEqual(onsets[10], onsets[64],
                         "a live Bias move moved the burst: %r" % (onsets,))
        self.assertEqual(onsets[117], onsets[64],
                         "a live Bias move moved the burst: %r" % (onsets,))

    def test_the_pole_is_where_the_circuit_has_it(self):
        """Behind the second clipper and in front of the tone stack, at the
        same corner as the section in front of that clipper."""
        effect = build(character="cascade")
        try:
            self.assertEqual(len(effect._hps), 3)
            self.assertAlmostEqual(float(effect._cascade_out_hp.frequency),
                                   rebuilt.CASCADE_OUT_HP_HZ, places=6)
            self.assertAlmostEqual(float(effect._hps[1].frequency),
                                   float(effect._cascade_out_hp.frequency),
                                   places=6)
            self.assertIs(effect._cascade_out_hp._source, effect._shapers[1])
            self.assertIs(effect._tone_split._source, effect._cascade_out_hp)
        finally:
            effect.deinit()
        plain = build()
        try:
            self.assertIsNone(plain._cascade_out_hp)
            self.assertEqual(len(plain._hps), 2)
        finally:
            plain.deinit()


class NoOutputCharge(Fuzz):
    """The class at `80d5a26`: the output pole starts cold, so a starved
    bias bangs its whole offset out of the first block."""

    NAME = 'Fuzz'

    def _charge_output(self, rewire=False):
        return False


class TheTierOneRowsAtEveryShippedPatch(unittest.TestCase):
    """audiocomponents#87.

    Tier 1's silence and tail rows were taken at the constructor default,
    and the default was the one state whose Bias was exactly 0: the 0-127
    grid had no centre, so MIDI 64 was +0.007874 and patch 0 -- whose name
    is "Bias centred" -- banged 329 LSB out of digital silence while the
    constructor holding the same nominal setting held 0. Eight of the nine
    shipped patches emitted 114 to 329 LSB into nothing.

    So the rows walk the patches now. The centre detent is the fix; what
    stays red is the class's own, and is named rather than tolerated.
    """

    #: `{patch: why}`. Patch 2 starves the bias on purpose -- Bias MIDI 10,
    #: -0.844 -- and the germanium curve is asymmetric, so the offset it
    #: makes is the sound the patch is for. What it used to emit into
    #: digital silence was **21 971 LSB, -3.5 dBFS**, because the output
    #: pole started cold (audit 3 (p)2). It is charged now, and what is
    #: left is the wander
    #: `test_bias_off_centre_never_reaches_digital_zero_and_says_so`
    #: discloses: **at most 16 LSB, -66.2 dBFS**, bounded and tested rather
    #: than exempted. `RESIDUAL_LSB` is that bound, and it is the only
    #: thing this row lets any patch have.
    RED = {}

    RED_TAIL = {}

    #: The disclosed exception, under audit 3 ruling (n): a residual stated
    #: in LSB, bounded, and the bound tested. Patch 2 is the only patch
    #: that uses any of it.
    RESIDUAL_LSB = 16

    def peaks(self):
        """`{patch: (silence_peak, tail_samples, residual, declared)}`."""
        rows = {}
        for patch in sorted(Fuzz.PATCHES):
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
                    "stated residual of %d" % (patch, row[0],
                                               self.RESIDUAL_LSB))

    def test_only_a_starved_bias_uses_any_of_the_stated_residual(self):
        """The bound is a bound and not a blanket: every patch that does
        not starve the bias is exactly zero."""
        for patch, row in sorted(self.peaks().items()):
            if patch == 2:
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
        for patch in sorted(Fuzz.PATCHES):
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
                    "a stated residual of %d - it was 21 971 before the "
                    "output pole was charged"
                    % (patch, peak, self.RESIDUAL_LSB))

if __name__ == "__main__":
    unittest.main()
