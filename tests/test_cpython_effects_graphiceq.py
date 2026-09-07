"""`GraphicEQ`, rebuilt: its Tier 1 invariants and its own planted faults.

The dossier is `docs/effects/GraphicEQ.md` and the evidence pack is
`docs/effects/GraphicEQ-evidence.md`; this file is the part of that pack that
has to keep passing after the run that wrote it. Every measurement here is
paired with a fault of the same kind, because a check nobody has seen fail is
not a check (`docs/effects-kit-spec.md` section 6).

The three old-surface `GraphicEQ` tests in
`test_cpython_effects_dynamics_eq.py` are retired in the same commit: they
assert `.biquads`, the all-flat class returning its own source, and the ISO
centres, all three of which the dossier's section 7 names as defects.
"""

import math
import os
import sys
import unittest
from array import array

import audiocore
import audiobiquad
import audioeffects

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from kit_probes import ArraySource, render  # noqa: E402

RATE = 48000
CHANNELS = 2
BANDS = 10

#: Every band macro at 64 is the detent. `_component` maps 64/127 onto
#: +0.094 dB, which is inside the class's 0.1 dB dead band and is why patch 0
#: is a wire rather than nearly one.
DETENT = 64


def noise(frames, peak=8000, seed=12345, channels=CHANNELS):
    data = array("h", bytes(2 * channels * frames))
    state = seed
    for index in range(frames):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        value = int(peak * (2.0 * (state / 0x7FFFFFFF) - 1.0))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def burst_then_silence(hz=200.0, on=4800, total=76800, peak=20000, rate=RATE,
                       channels=CHANNELS):
    """The burst and the silence are one array on purpose.

    A probe that lets the source *end* and then keeps pulling reads exact
    zeros for every configuration, including the ones known to be dirty: the
    ported biquad's residue only exists while the node is processing samples.
    The silence has to be inside the sample.
    """
    data = array("h", bytes(2 * channels * total))
    for index in range(on):
        value = int(peak * math.sin(2.0 * math.pi * hz * index / rate))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def tone(hz, frames, peak=6000, rate=RATE, channels=CHANNELS):
    data = array("h", bytes(2 * channels * frames))
    for index in range(frames):
        value = int(peak * math.sin(2.0 * math.pi * hz * index / rate))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def rms_db(values, channel=0, skip=4800):
    column = values.float[skip:, channel]
    if not column.size:
        return -999.0
    power = float((column * column).mean())
    return 10.0 * math.log10(power) if power > 0 else -999.0


def build(data, rate=RATE, channels=CHANNELS, **options):
    source = ArraySource(data, rate=rate, channels=channels)
    effect = audioeffects.create("GraphicEQ", source, rate, **options)
    return effect, source


def run(data, frames, macros=(), rate=RATE, channels=CHANNELS, **options):
    effect, source = build(data, rate=rate, channels=channels, **options)
    for index, value in macros:
        effect.set_macro(index, value)
    audiocore.reset_buffer(effect.output)
    try:
        return render(effect.output, frames, rate=rate, channels=channels,
                      class_name="GraphicEQ",
                      latency_samples=effect.latency_samples)
    finally:
        effect.deinit()


class TheDetentIsAWire(unittest.TestCase):
    """T4, and the Tier 1 bypass invariant, which are the same fact here."""

    def test_patch_zero_is_byte_identical_to_the_source(self):
        data = noise(24000)
        dry = render(ArraySource(data), 24000)
        wet = run(data, 24000)
        self.assertEqual(wet.digest, dry.digest,
                         "patch 0 is not a wire: %08x against %08x"
                         % (wet.digest, dry.digest))

    def test_a_band_at_the_detent_is_the_chain_built_without_it(self):
        # T4. Band 5 sits at the detent between two bands at the rails; the
        # comparison is against a bank whose fifth centre carries no boost
        # and no cut either way, built the same.
        data = noise(24000)
        rails = [(index, 127 if index % 2 else 0) for index in range(5)]
        rails += [(5, DETENT)]
        rails += [(index, 0 if index % 2 else 127) for index in range(6, 10)]
        with_flat = run(data, 24000, macros=rails)
        # The same setting reached the other way: a shorter `gains_db` leaves
        # band 5 at its detent without anyone touching its macro.
        other = [entry for entry in rails if entry[0] != 5]
        without = run(data, 24000, macros=other)
        self.assertEqual(with_flat.digest, without.digest)

    def test_planted_fault_a_detented_band_left_unmuted(self):
        # The fault of the same kind: a band at 0 dB with `mix = 1` instead
        # of `mix = 0`. It is not a wire at the bottom of this bank -- Direct
        # Form I in float32, poles that close to z = 1 -- and the dossier's
        # App. S(iv) measures 5 LSB at 31.25 Hz. The clean run above is the
        # control; this one must go red.
        data = noise(24000)
        dry = render(ArraySource(data), 24000)
        effect, _ = build(data)
        try:
            effect._sections[0].mix = 1.0        # the plant
            audiocore.reset_buffer(effect.output)
            faulted = render(effect.output, 24000)
        finally:
            effect.deinit()
        self.assertNotEqual(faulted.digest, dry.digest,
                            "the planted fault did not change the render, so "
                            "the byte check above proves nothing")


class TheTailReachesZero(unittest.TestCase):
    def test_silence_in_gives_exact_zero_out(self):
        # The invariant this class was known to fail, at exactly its own
        # bands. `audiobiquad`'s float state is what changed.
        for label, macros in (
                ("31.25 Hz at +6", ((0, 95),)),
                ("all ten at +6", tuple((i, 95) for i in range(BANDS)))):
            with self.subTest(setting=label):
                result = run(burst_then_silence(), 76800, macros=macros)
                settled = result.data[-4800:]
                self.assertEqual(int(abs(settled).max()), 0,
                                 "%s holds %d LSB after silence"
                                 % (label, int(abs(settled).max())))

    def test_the_positive_control_the_ported_node_still_fails(self):
        # Without a control that must go red, "reaches zero" is a claim about
        # the probe and not about the class. The same probe through the
        # composition this class was rebuilt off -- one `audiofilters.Filter`
        # over `synthio.Biquad` -- holds a constant residue for ever
        # (audioif#23).
        import audiofilters
        import synthio
        centres = [31.25 * (2 ** n) for n in range(BANDS)]
        sections = [synthio.Biquad(synthio.FilterMode.PEAKING_EQ, hz, Q=1.4,
                                   A=10.0 ** (6.0 / 40.0)) for hz in centres]
        node = audiofilters.Filter(filter=tuple(sections), mix=1.0,
                                   sample_rate=RATE, channel_count=CHANNELS,
                                   bits_per_sample=16, samples_signed=True,
                                   buffer_size=2048)
        node.play(ArraySource(burst_then_silence()))
        try:
            audiocore.reset_buffer(node)
            result = render(node, 76800)
        finally:
            node.deinit()
        settled = result.data[-4800:]
        self.assertGreater(int(abs(settled).max()), 0,
                           "the ported bank reached zero, so this control no "
                           "longer separates the two nodes")

    def test_the_declared_tail_bounds_the_measured_one(self):
        for rate in (48000, 44100, 22050):
            with self.subTest(rate=rate):
                burst = int(rate * 0.25)
                total = burst + int(rate * 1.0)
                data = burst_then_silence(hz=40.0, on=burst, total=total,
                                          peak=24000, rate=rate)
                macros = tuple((index, 127) for index in range(BANDS))
                result = run(data, total, macros=macros, rate=rate)
                after = result.data[burst:]
                rows = [i for i in range(after.shape[0]) if after[i].any()]
                measured = (rows[-1] + 1) if rows else 0
                effect, _ = build(data, rate=rate)
                declared = effect.tail_samples
                effect.deinit()
                self.assertLessEqual(measured, declared,
                                     "%d Hz: measured %d frames of tail "
                                     "against a declared %d"
                                     % (rate, measured, declared))
                self.assertGreater(measured, declared // 2,
                                   "%d Hz: declared %d frames for a %d frame "
                                   "tail -- a bound that loose is not a "
                                   "report" % (rate, declared, measured))


class TheClampIsReported(unittest.TestCase):
    def test_at_22_kHz_the_top_band_clamps_and_says_so(self):
        effect, _ = build(noise(4096, channels=CHANNELS), rate=22050)
        try:
            self.assertEqual(effect.clamped, (9,))
            self.assertAlmostEqual(effect.built_centres[9],
                                   22050 * 0.5 * 0.98, places=3)
            self.assertEqual(effect.centres[9], 16000.0)
        finally:
            effect.deinit()

    def test_at_48_and_44_kHz_nothing_clamps(self):
        for rate in (48000, 44100):
            with self.subTest(rate=rate):
                effect, _ = build(noise(4096), rate=rate)
                try:
                    self.assertEqual(effect.clamped, ())
                finally:
                    effect.deinit()

    def test_the_clamped_bank_passes_signal_rather_than_railing(self):
        # The check has to drive signal, not silence. On the *ported* biquad
        # a corner over Nyquist rails into a full-scale square at fs/4 while
        # raising nothing, and renders exact zeros on silence, so
        # construct-and-catch and silence-in-silence-out both pass it
        # (`GraphicEQ.md` App. E(iv)).
        data = tone(400.0, 8192, peak=6000, rate=22050)
        result = run(data, 8192, macros=((9, 127), (8, 127)), rate=22050)
        self.assertLess(int(abs(result.data).max()), 20000,
                        "the top of the bank is railing at 22.05 kHz")

    def test_planted_fault_a_centre_the_kernel_moves_and_nobody_reports(self):
        # The fault of the same kind is *not* railing -- `audiobiquad` does
        # not rail, because `audioif_filter_f32.c:94-95` clamps `frequency`
        # to 0.4999 x the rate for itself. It is the shape the old class had
        # and section 7 names: the band moves and nothing says so. Asked for
        # 16 kHz at 22.05 kHz the section runs at 11022.45 Hz and reads its
        # `frequency` back as 16000, so the report and the reality have
        # parted while every render still looks fine.
        rate = 22050
        asked = audiobiquad.Biquad(mode=audiobiquad.HIGH_SHELF,
                                   frequency=16000.0, Q=0.707, gain_db=12.0,
                                   sample_rate=rate, channel_count=CHANNELS)
        actual = audiobiquad.Biquad(mode=audiobiquad.HIGH_SHELF,
                                    frequency=rate * 0.4999, Q=0.707,
                                    gain_db=12.0, sample_rate=rate,
                                    channel_count=CHANNELS)
        try:
            self.assertEqual(asked.frequency, 16000.0)
            self.assertEqual(asked.coefficients, actual.coefficients,
                             "the kernel no longer moves an over-Nyquist "
                             "centre, so `clamped` reports nothing real")
        finally:
            asked.deinit()
            actual.deinit()
        # And the class, which does report it, disagrees with that silence.
        effect, _ = build(tone(400.0, 4096, peak=6000, rate=rate), rate=rate)
        try:
            self.assertEqual(effect.clamped, (9,))
            self.assertNotEqual(effect.built_centres[9], effect.centres[9])
        finally:
            effect.deinit()


class TheJumpDoesNotSlam(unittest.TestCase):
    """A patch change starts the bank clean; a knob move rides through."""

    TONE = 220.0

    def _transition(self, before, after, clear=True):
        data = tone(self.TONE, 96000, peak=11000)
        effect, _ = build(data)
        try:
            effect.program_change(before)
            audiocore.reset_buffer(effect.output)
            render(effect.output, 48000)
            if clear:
                effect.program_change(after)
            else:
                # The planted fault: the contract's own program_change,
                # which leaves every section holding the old curve.
                audioeffects._component.Component.program_change(
                    effect, after)
            post = render(effect.output, 48000)
        finally:
            effect.deinit()
        steady = int(abs(post.data[24000:]).max())
        peak = int(abs(post.data[:24000]).max())
        return steady, peak

    def test_a_patch_change_does_not_overshoot_its_own_steady_level(self):
        for before, after in ((5, 1), (1, 2), (0, 5), (2, 1)):
            with self.subTest(patch="%d->%d" % (before, after)):
                steady, peak = self._transition(before, after)
                self.assertLess(peak, steady * 2,
                                "patch %d -> %d peaks at %d against a steady "
                                "%d" % (before, after, peak, steady))
                self.assertLess(peak, 32767,
                                "patch %d -> %d clips" % (before, after))

    def test_planted_fault_the_jump_taken_on_the_old_curves_state(self):
        steady, peak = self._transition(5, 1, clear=False)
        self.assertGreater(peak, steady * 4,
                           "the base program_change no longer slams, so the "
                           "check above proves nothing (peak %d, steady %d)"
                           % (peak, steady))

    def test_a_knob_move_is_not_cleared(self):
        # The other half of the rule. A slider being pushed keeps its state,
        # so a sweep does not gate; if this ever starts clearing, the
        # transition below stops being continuous.
        data = tone(self.TONE, 96000, peak=11000)
        effect, _ = build(data)
        try:
            audiocore.reset_buffer(effect.output)
            render(effect.output, 24000)
            effect.set_macro(0, 127)
            first = render(effect.output, 512)
        finally:
            effect.deinit()
        # The first block after the move still carries the tone rather than
        # starting from zero.
        self.assertGreater(int(abs(first.data[:256]).max()), 1000)


class TheSurface(unittest.TestCase):
    def test_fourteen_macros_and_six_patches(self):
        cls = audioeffects.GraphicEQ
        self.assertEqual(len(cls.MACRO_LABELS), 14)
        self.assertEqual(sorted(cls.PATCHES), list(range(6)))
        self.assertEqual(cls.PATCHES[0][0], "Flat")

    def test_patch_zero_is_the_constructors_defaults_on_the_grid(self):
        effect, _ = build(noise(4096))
        try:
            defaults = [effect.get_macro(index) for index in range(14)]
        finally:
            effect.deinit()
        effect, _ = build(noise(4096))
        try:
            effect.program_change(0)
            self.assertEqual([round(effect.get_macro(i)) for i in range(14)],
                             [round(v) for v in defaults])
        finally:
            effect.deinit()

    def test_capabilities_is_empty_and_the_transport_is_never_read(self):
        reads = []

        def transport():
            reads.append(1)
            return (False, 0.0, 120.0, 4, 4)

        source = ArraySource(noise(8192))
        effect = audioeffects.create("GraphicEQ", source, RATE,
                                     transport=transport)
        try:
            self.assertEqual(effect.capabilities, ())
            audiocore.reset_buffer(effect.output)
            render(effect.output, 8192)
            for index in range(14):
                effect.set_macro(index, 100)
            self.assertEqual(reads, [], "the transport was read %d times by "
                                        "a class declaring no tempo_sync"
                                        % len(reads))
        finally:
            effect.deinit()

    def test_latency_is_zero_and_no_option_adds_any(self):
        effect, _ = build(noise(4096))
        try:
            self.assertEqual(effect.latency_samples, 0)
            for index in range(14):
                effect.set_macro(index, 127)
                self.assertEqual(effect.latency_samples, 0)
        finally:
            effect.deinit()

    def test_centres_must_be_ten_and_ascending(self):
        for bad in ((100.0, 200.0), tuple(range(1, 12)),
                    (100.0, 90.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0,
                     900.0, 1000.0)):
            with self.subTest(centres=len(bad)):
                with self.assertRaises(ValueError):
                    build(noise(1024), centres=bad)

    def test_the_shelf_is_always_the_top_of_a_retuned_bank(self):
        centres = tuple(40.0 * (2 ** n) for n in range(BANDS))
        effect, _ = build(noise(4096), centres=centres)
        try:
            self.assertEqual(effect.centres, centres)
            self.assertEqual(effect._sections[9].mode, audiobiquad.HIGH_SHELF)
            for index in range(BANDS - 1):
                self.assertEqual(effect._sections[index].mode,
                                 audiobiquad.PEAKING_EQ)
        finally:
            effect.deinit()


class TheQLaw(unittest.TestCase):
    def test_q_narrows_as_the_slider_travels(self):
        # T2 in miniature: the widths themselves are Station C's swept
        # measurement, but the law that produces them is checked here.
        effect, _ = build(noise(1024))
        try:
            widths = []
            for value in (79, 95, 127):        # +3, +6, +12 dB
                effect.set_macro(5, value)
                widths.append(effect._sections[5].Q)
        finally:
            effect.deinit()
        self.assertLess(widths[0], widths[1])
        self.assertLess(widths[1], widths[2])
        self.assertAlmostEqual(widths[2], 2.0, places=3)

    def test_constant_q_pins_every_band_to_the_anchor(self):
        effect, _ = build(noise(1024), constant_q=True)
        try:
            for value in (79, 95, 127):
                effect.set_macro(5, value)
                self.assertAlmostEqual(effect._sections[5].Q, 2.0, places=3)
            effect.set_macro(12, 0)            # Band Q to 0.7
            effect.set_macro(5, 127)
            self.assertAlmostEqual(effect._sections[5].Q, 0.7, places=3)
        finally:
            effect.deinit()

    def test_the_band_q_macro_moves_every_bell_at_once(self):
        effect, _ = build(noise(1024))
        try:
            for index in range(BANDS - 1):
                effect.set_macro(index, 127)
            before = [effect._sections[i].Q for i in range(BANDS - 1)]
            effect.set_macro(12, 0)
            after = [effect._sections[i].Q for i in range(BANDS - 1)]
            self.assertTrue(all(b > a for a, b in zip(after, before)))
        finally:
            effect.deinit()


class TheLevelMacros(unittest.TestCase):
    def test_gain_and_volume_are_flat_broadband_trims(self):
        for index in (10, 11):
            for value, expected in ((127, 12.0), (0, -12.0)):
                with self.subTest(macro=index, midi=value):
                    row = []
                    for hz in (100.0, 1000.0, 8000.0):
                        data = tone(hz, 24000, peak=4000)
                        dry = render(ArraySource(data), 24000)
                        wet = run(data, 24000, macros=((index, value),))
                        row.append(rms_db(wet) - rms_db(dry))
                    for measured in row:
                        self.assertAlmostEqual(measured, expected, delta=0.15,
                                               msg="macro %d at %d: %s"
                                                   % (index, value, row))

    def test_mono_gets_the_same_curve_on_one_channel(self):
        data = tone(1000.0, 24000, peak=4000, channels=1)
        dry = render(ArraySource(data, channels=1), 24000, channels=1)
        wet = run(data, 24000, macros=((5, 127),), channels=1)
        self.assertEqual(wet.channels, 1)
        self.assertGreater(rms_db(wet) - rms_db(dry), 10.0)


if __name__ == "__main__":
    unittest.main()
