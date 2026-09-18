"""`MultibandCompressor`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/MultibandCompressor.md`; its Tier 2 rows are
M1..M5 and each has a test here under its own number. The class gate asks two
things of every trait and this file carries both: the measurement, and the
*same* measurement shown red on a fault of the same kind. A green measurement
with no demonstrated red has never been shown able to fail.

The full Tier 2 sweeps live in `workspace docs/effects-internal/probes/phase2_probes/multiband_traits.py` --
fifty-seven tones a curve is a minute apiece and does not belong in a unit
suite. What is here is the short form of each, plus the decisions that have no
sweep: the surface, the clamp, the reset ordering and the guard.

The faults are the cheap kind -- a subclass or a macro at the wrong end --
never a change to a library file.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from array import array                                        # noqa: E402

import audiobiquad                                              # noqa: E402
import audiocore                                                # noqa: E402
from audioeffects import multibandcompressor           # noqa: E402
#: The subject is named directly. `MultibandCompressor` has come home to
#: `audioeffects/multibandcompressor.py`; `rebuilt.ADOPTED` no longer lists
#: it. These tests still import the home module so a planted-fault subclass
#: is measured against this file, not only `create()`.
import kit_probes as probes                                     # noqa: E402
from audioeffects import _component                             # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

#: `_component` reads VENDOR off the module a class is defined in, and the
#: faults below are subclasses of a rebuilt class. Without this they would
#: refuse to construct -- a fault that cannot fail.
VENDOR = "PyDevices"

RATE = 48000
CLASS = multibandcompressor.MultibandCompressor

(XLOW, XHIGH, LOW_T, MID_T, HIGH_T, LOW_R, MID_R, HIGH_R,
 LOW_G, MID_G, HIGH_G, ATTACK, RELEASE, MIX) = range(14)

#: The constructor's own defaults, in the macros' units, in macro order.
DEFAULTS = (200.0, 2000.0, -18.0, -18.0, -18.0, 3.0, 3.0, 3.0,
            0.0, 0.0, 0.0, 10.0, 150.0, 1.0)

UNITY = {"low_ratio": 1.0, "mid_ratio": 1.0, "high_ratio": 1.0, "mix": 1.0}


# --------------------------------------------------------------------------
# The planted faults


class NoGuard(CLASS):
    """The Splitter fed straight off the source.

    This *was* M5's fault. It is not one any more: at audioif `977ef26` a
    `Splitter` takes a call bigger than its ring in pieces instead of
    keeping only the tail (audioif#87), so the head it used to drop is
    delivered and the guard has nothing left to guard. Measured on this
    floor, `NoGuard` and the shipped class render the same bytes at every
    source block in the ladder - digest 3824975193 at 256, 8192, 16384,
    20000 and 32768 frames - and burst material survives unguarded.

    The fixture stays because that equality is worth asserting: it is the
    regression test for audioif#87, and it is what says the guard may now
    be dropped. M5's live fault moved to `OldRingSource` below.
    """

    def _build_input(self):
        self._guard = None
        return self._source


class ThroughTheDryVoice(CLASS):
    """The wiring this class shipped with before audioif#95: Mix 0 routed
    through the Mixer's dry voice at level 1.0 rather than handing back the
    head.

    Nothing else changes - the levels are the same numbers - so the only
    difference in the render is the mixer's own `level / 32767` multiply,
    which is what the WIRE row above is about.
    """

    def _refresh_output(self):
        if not self._ready:
            return
        if not self._primed:
            self._mix, mix = 1.0, self._mix
            try:
                self._play_voices()
            finally:
                self._mix = mix
        self._output = self._mixer


class NoLevelGates(CLASS):
    """The click fault: the voices take their sources on a Mix move off 0,
    but nothing opens their level gates first.

    Since CircuitPython 10.3.0 a freshly played voice starts at level 0 and
    takes its level only when its signal reaches or crosses zero, so on
    material that does nothing of the sort the render starts on silence.
    """

    def _play_voices(self):
        if self._mix <= 0.0:
            self._primed = False
            return
        self._mixer.play(self._taps[0], voice=0, loop=True)
        for band in range(self._bands):
            self._mixer.play(self._detectors[band], voice=band + 1,
                             loop=True)
        self._primed = True


class OldRingSource:
    """M5's fault at this floor: a source that keeps only its last ring.

    The `Splitter` before audioif#87, in Python, because the node no longer
    does it. A call bigger than 8192 frames arrives with its head gone, so
    the block ladder reads a different render at every block size and burst
    material that ends inside the dropped head disappears entirely.

    It sits at the source, ahead of the guard, which is the point: the
    guard never protected the class from a source that drops frames, only
    from the Splitter's own ring. Both the shipped class and `NoGuard` go
    red on it, and that is what keeps the ladder from being a measurement
    that cannot fail.
    """

    RING_FRAMES = 8192

    def __init__(self, inner):
        self._inner = inner
        self.sample_rate = inner.sample_rate
        self.channel_count = inner.channel_count
        self.bits_per_sample = getattr(inner, "bits_per_sample", 16)
        self.samples_signed = getattr(inner, "samples_signed", True)

    def _reset_buffer(self, *args, **kwargs):
        return self._inner._reset_buffer(*args, **kwargs)

    def _get_buffer(self, *args, **kwargs):
        state, data = self._inner._get_buffer(*args, **kwargs)
        raw = bytes(data)
        stride = 2 * self.channel_count
        frames = len(raw) // stride
        if frames > self.RING_FRAMES:
            raw = raw[(frames - self.RING_FRAMES) * stride:]
        return state, memoryview(bytearray(raw))


class LinkwitzRiley2(CLASS):
    """M2's fault: one Butterworth section a side instead of two."""

    def _band_modes(self, band):
        full = CLASS._band_modes(self, band)
        if len(full) == 2:
            return full[:1]
        return (audiobiquad.HIGH_PASS, audiobiquad.LOW_PASS)


class NoRatioClamp(CLASS):
    """M1's fault: the eight-to-one crossover clamp removed, both halves of
    it -- the push-up here and the 800 Hz floor on the macro's own span."""

    _MACRO_RANGES = (CLASS._MACRO_RANGES[:1] + ((200.0, 8000.0, "log"),)
                     + CLASS._MACRO_RANGES[2:])

    def _apply_crossovers(self):
        self._low_hz = self._hz(self.macro(XLOW))
        self._high_hz = self._hz(self.macro(XHIGH))
        self._tune(0, (self._low_hz, self._low_hz))
        self._tune(1, (self._low_hz, self._low_hz,
                       self._high_hz, self._high_hz))
        self._tune(2, (self._high_hz, self._high_hz))


class PlayBeforeMacros(CLASS):
    """The head-of-render fault: the voices played before the macros.

    `MixerVoice.play` resets its new source and pulls a chunk from it on the
    spot (`audiomixer/MixerVoice.c:75-79`), so a voice played before
    `_init_macros` holds 256 frames rendered through eight biquads still at
    their construction frequency of 1 kHz. This subclass puts the sections
    back to 1 kHz, re-plays, and then applies the crossover -- which is
    exactly what building in the other order did.
    """

    def _build(self, **options):
        CLASS._build(self, **options)
        for sections in self._sections:
            for section in sections:
                section.frequency = 1000.0
        self._mixer.play(self._taps[0], voice=0, loop=True)
        for band in range(self._bands):
            self._mixer.play(self._detectors[band], voice=band + 1,
                             loop=True)
        self._apply_crossovers()


class MixerResetTailFirst(CLASS):
    """The reset-order fault: the Mixer put back at the end of the walk,
    which is where owning it in build order would have put it."""

    def _build(self, **options):
        CLASS._build(self, **options)
        index = self._nodes.index(self._mixer)
        for walk in (self._nodes, self._resets, self._deinits):
            walk.append(walk.pop(index))


class PortedBiquads(CLASS):
    """The Tier 1 tail fault: the crossover on the ported fixed-point node.

    Not a subclass trick -- it is the topology the dossier's section 4
    mapped before App. P re-read the palette, and it is here so the reason
    for `audiobiquad` is a measurement in the suite rather than a sentence
    in a docstring.
    """

    def _band_chain(self, band):
        import audiofilters
        import synthio
        modes = {audiobiquad.LOW_PASS: synthio.FilterMode.LOW_PASS,
                 audiobiquad.HIGH_PASS: synthio.FilterMode.HIGH_PASS}
        sections = [synthio.Biquad(modes[mode], frequency=1000.0,
                                   Q=0.7071067811865475)
                    for mode in self._band_modes(band)]
        node = self._own(audiofilters.Filter(
            filter=sections, mix=1.0, buffer_size=2048,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            bits_per_sample=16, samples_signed=True))
        node.play(self._taps[band + 1], loop=False)
        self._sections.append(sections)
        return node


# --------------------------------------------------------------------------
# Plumbing


def build(cls=None, rate=RATE, channels=2, probe=None, block=256, **options):
    cls = cls or CLASS
    if probe is None:
        probe = probes.silence(48000, channels)
    source = probes.ArraySource(probe, rate=rate, block=block,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, class_name="MultibandCompressor",
                         latency_samples=effect.latency_samples)


def tone(hz, seconds, dbfs=-12.0, rate=RATE, channels=2):
    return probes.sine(hz, seconds, dbfs, rate=rate, channels=channels)


def two_bursts(hz=440.0, on_ms=40.0, gap_s=0.15, dbfs=-6.0):
    """Burst, silence, burst, silence -- and where each burst ends.

    What the "renders again after reset" row needs: a class that has been
    reset must be shown making sound again, and the source may not be
    rewound to arrange it.
    """
    one, on = probes.burst_silence(hz=hz, on_ms=on_ms,
                                   total_s=on_ms / 1000.0 + gap_s,
                                   dbfs=dbfs)
    both = array("h")
    both.extend(one)
    both.extend(one)
    return both, on, len(one) // 2


def tone_db(effect, hz, seconds=0.35, rate=RATE):
    """The class's output level at `hz`, in dB against the tone that went
    in, read off the settled half."""
    render_object = render(effect, int(seconds * rate), rate=rate)
    half = render_object.frames // 2
    return kit.db(abs(kit.tone_bin(render_object.float[half:, 0], rate, hz)))


def source_db(hz, seconds=0.35, dbfs=-12.0, rate=RATE):
    values = tone(hz, seconds, dbfs, rate=rate)
    render_object = kit.Render(bytes(memoryview(values).cast("B")), rate, 2)
    half = render_object.frames // 2
    return kit.db(abs(kit.tone_bin(render_object.float[half:, 0], rate, hz)))


def sum_db(hz, cls=None, seconds=0.35, rate=RATE, **options):
    settings = dict(UNITY)
    settings.update(options)
    effect = build(cls, rate=rate, probe=tone(hz, seconds, rate=rate),
                   **settings)
    try:
        return tone_db(effect, hz, seconds, rate) - source_db(hz, seconds,
                                                              rate=rate)
    finally:
        effect.deinit()


# --------------------------------------------------------------------------


class Surface(unittest.TestCase):

    def test_patch_zero_is_the_constructor_defaults_on_the_grid(self):
        # Held to the spans, not to a hand-copied list. The mode goes in
        # with the span because a BIPOLAR macro's MIDI law has a centre
        # detent and a UNIPOLAR one does not (audiocomponents#87); a BIPOLAR
        # 0 dB is MIDI 64 exactly, where it used to sit at 63.5.
        expected = tuple(
            _component.macro_of(span, value, CLASS.MACRO_MODES[index])
            for index, (span, value) in enumerate(
                zip(CLASS._MACRO_RANGES, DEFAULTS)))
        self.assertEqual(CLASS.PATCHES[0][1], expected)
        effect = build()
        try:
            self.assertEqual(effect.patch_index, 0)
            for index, value in enumerate(DEFAULTS):
                with self.subTest(macro=CLASS.MACRO_LABELS[index]):
                    self.assertAlmostEqual(effect.macro(index), value,
                                           delta=abs(value) * 0.02 + 0.2)
        finally:
            effect.deinit()

    def test_the_surface_is_fourteen_macros_and_five_patches(self):
        self.assertEqual(len(CLASS.MACRO_LABELS), 14)
        self.assertLessEqual(len(CLASS.MACRO_LABELS), _component.MAX_MACROS)
        self.assertEqual(len(CLASS.PATCHES), 5)
        self.assertEqual(CLASS.PATCHES[0][0], "Master Glue")

    def test_capabilities_is_empty_and_the_transport_is_never_read(self):
        calls = []

        def transport():
            calls.append(1)
            return _component.static_transport()

        source = probes.ArraySource(tone(440.0, 0.2), rate=RATE, block=256)
        effect = CLASS.create(source, RATE, transport=transport)
        try:
            render(effect, 8192)
            self.assertEqual(effect.capabilities, ())
            self.assertEqual(calls, [])
        finally:
            effect.deinit()

    def test_the_mid_macros_and_the_upper_corner_are_dead_at_two_bands(self):
        two = build(bands=2)
        three = build(bands=3)
        try:
            self.assertEqual([index for index in range(14)
                              if not two.macro_is_live(index)],
                             [XHIGH, MID_T, MID_R, MID_G])
            self.assertTrue(all(three.macro_is_live(index)
                                for index in range(14)))
            self.assertIsNone(two.crossover_high_hz)
        finally:
            two.deinit()
            three.deinit()

    def test_bands_is_two_or_three_and_nothing_else(self):
        for bad in (1, 4, 0, "3"):
            with self.subTest(bands=bad):
                self.assertRaises(ValueError, build, bands=bad)

    def test_the_clamp_pushes_the_upper_corner_up_and_never_refuses(self):
        effect = build()
        try:
            effect.set_macro(XLOW, 127)          # 800 Hz
            effect.set_macro(XHIGH, 0)           # asked for 800 Hz
            self.assertAlmostEqual(effect.crossover_low_hz, 800.0, delta=1.0)
            self.assertAlmostEqual(effect.crossover_high_hz, 6400.0,
                                   delta=10.0)
            # the macro still reports what was asked for, not what landed
            self.assertAlmostEqual(effect.macro(XHIGH), 800.0, delta=1.0)
        finally:
            effect.deinit()

    def test_a_corner_above_the_running_nyquist_clamps(self):
        effect = build(rate=22050)
        try:
            effect.set_macro(XHIGH, 127)
            ceiling = 22050 * 0.5 * _component.NYQUIST_MARGIN
            self.assertLessEqual(effect.crossover_high_hz, ceiling + 1e-6)
            self.assertGreater(effect.crossover_high_hz, 0.0)
        finally:
            effect.deinit()


class TierOne(unittest.TestCase):

    def test_mix_zero_is_a_wire(self):
        values = probes.ramp_fs(16384)
        effect = build(probe=values, mix=0.0)
        try:
            wet = render(effect, 16384)
        finally:
            effect.deinit()
        dry = kit.Render(bytes(memoryview(values).cast("B")), RATE, 2)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])

    def test_mix_zero_is_a_wire_at_every_rate_and_channel_count(self):
        """WIRE on a full-scale ramp, which is the only probe that can see
        the fault it is about.

        A mixer voice at level 1.0 scales by 32768/32767 (audioif#95), so
        the dry tap at unity lifted every sample from 32736 up by one LSB -
        15 of 32768 here, all in the right channel, because a stereo voice
        at pan 0 gets 32767 on the left and 32768 on the right. Mono gets
        the lifted multiplier on both. Nothing below -6.02 dBFS can reach
        the mechanism, which is why this is a ramp and not a tone.
        """
        for rate in (22050, 44100, 48000):
            for channels in (1, 2):
                with self.subTest(rate=rate, channels=channels):
                    values = probes.ramp_fs(8192, channels=channels)
                    effect = build(rate=rate, channels=channels,
                                   probe=values, mix=0.0)
                    try:
                        wet = render(effect, 8192, rate=rate,
                                     channels=channels)
                    finally:
                        effect.deinit()
                    dry = kit.Render(bytes(memoryview(values).cast("B")),
                                     rate, channels)
                    result = kit.wire(wet, dry, latency_samples=0)
                    self.assertTrue(result["passed"], result["red"])
                    self.assertEqual(
                        result["values"]["differing_samples"], 0)

    def test_the_dry_voice_at_unity_is_the_fault_the_wire_catches(self):
        """The planted fault, and it is the wiring this class used to have:
        Mix 0 routed through the mixer's dry voice at level 1.0.

        Without this the row above is a measurement nobody has shown able to
        fail - and the difference is one LSB on 15 samples of 32768, which
        no summarising statistic would have found either.
        """
        values = probes.ramp_fs(16384)
        effect = build(ThroughTheDryVoice, probe=values, mix=0.0)
        try:
            wet = render(effect, 16384)
        finally:
            effect.deinit()
        dry = kit.Render(bytes(memoryview(values).cast("B")), RATE, 2)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertFalse(result["passed"])
        self.assertEqual(result["values"]["max_abs_difference_lsb"], 1)
        self.assertGreater(result["values"]["differing_samples"], 0)

    def _move_off_zero(self, cls=None):
        """Bypass a full-scale ramp for 2048 frames, then ask for Mix 1.

        The ramp is the material this has to be measured on. At frame 2048
        it sits around -24580 and does not reach zero again for four
        thousand frames, so a voice waiting for a zero crossing waits - on a
        220 Hz sine the gate opens by itself within a few samples and the
        fault below cannot fire at all.
        """
        effect = build(cls, probe=probes.ramp_fs(16384), mix=0.0,
                       low_ratio=1.0, mid_ratio=1.0, high_ratio=1.0)
        try:
            before = render(effect, 2048)
            effect.set_macro(MIX, 127)
            after = render(effect, 2048)
        finally:
            effect.deinit()
        return before, after

    def test_a_mix_move_off_zero_does_not_click(self):
        """Leaving Mix 0 hands the voices their sources *and* opens their
        level gates, in that order, and the render is live from its first
        sample.

        What is asserted is the gate, not the bands: the eight biquads are
        cold at the moment of the move and their start-up is audible for a
        few hundred frames, which is what fading a filter bank in at Mix 1
        does and not a defect. The gate's own signature is a *hole* - a
        voice that starts at level 0 and waits for a zero crossing that this
        material does not offer - so the row is the count of zero samples
        where the source has none.
        """
        before, after = self._move_off_zero()
        self.assertLess(int(before.data[-1][0]), -20000)
        self.assertEqual(int((after.data[:256] == 0).sum()), 0)
        self.assertTrue(after.data.any())

    def test_without_the_gates_the_move_off_zero_starts_on_silence(self):
        """The planted fault: the same move with the level gates skipped.

        Two frames of nothing, on both channels, before the level steps in -
        which is a click, and it is exactly what `open_level_gates` is for.
        """
        _before, after = self._move_off_zero(NoLevelGates)
        self.assertGreater(int((after.data[:256] == 0).sum()), 0)
        self.assertEqual(int(after.data[0][0]), 0)

    def test_the_tail_reaches_exact_zero(self):
        values, held = probes.dc_step(level=0.6, hold_s=0.2, total_s=1.6)
        effect = build(probe=values, crossover_low_hz=40.0, **UNITY)
        try:
            declared = effect.tail_samples
            wet = render(effect, len(values) // 2)
        finally:
            effect.deinit()
        result = kit.tail(wet, burst_end_frame=held,
                          declared_tail_samples=declared)
        self.assertTrue(result["passed"], result["red"])
        self.assertEqual(result["values"]["residual_lsb"], 0)

    def test_the_ported_biquads_hold_dc_for_ever(self):
        # The planted fault for the row above, and the reason the crossover
        # is `audiobiquad`: the same probe through the fixed-point cascade
        # never arrives.
        values, held = probes.dc_step(level=0.6, hold_s=0.2, total_s=1.6)
        effect = build(PortedBiquads, probe=values, crossover_low_hz=40.0,
                       **UNITY)
        try:
            wet = render(effect, len(values) // 2)
        finally:
            effect.deinit()
        result = kit.tail(wet, burst_end_frame=held)
        self.assertFalse(result["passed"])
        self.assertGreater(result["values"]["residual_lsb"], 0)

    def test_reset_clears_every_node_and_leaves_the_source_alone(self):
        values, on = probes.burst_silence(hz=80.0, on_ms=40.0,
                                          total_s=0.3, dbfs=-2.0)
        source = probes.ArraySource(values, rate=RATE, block=256)
        effect = CLASS.create(source, RATE, **UNITY)
        # Primed to the end of the burst, not past it: reset a chain that
        # has already rung down and every walk looks alike.
        primed = render(effect, on + 64)
        self.assertTrue(primed.data.any())
        effect.reset()
        after = render(effect, 1024)
        self.assertEqual(int(abs(after.data).max()), 0)
        self.assertNotIn(source, effect._nodes)
        effect.deinit()
        audiocore.reset_buffer(source)
        still = probes.render(source, 4096)
        self.assertTrue(still.data.any())

    def test_the_class_renders_again_after_reset(self):
        # The row that catches a permanent silence. `audiomixer`'s reset
        # STOPS its voices on the ported CircuitPython node and rewinds them
        # on audioif's, and a stopped voice never plays again -- so "silent
        # after reset" is both what a clean reset looks like and what a dead
        # class looks like. The class re-plays its voices in `_reset_mixer`
        # so the two builds behave alike; this asserts the sound comes back.
        values, on, second = two_bursts()
        source = probes.ArraySource(values, rate=RATE, block=256)
        effect = CLASS.create(source, RATE, **UNITY)
        try:
            self.assertTrue(render(effect, on + 64).data.any())
            effect.reset()
            # The source is never rewound -- the invariant forbids touching
            # it -- so the probe carries a second burst instead.
            self.assertTrue(render(effect, second + 4096).data.any())
        finally:
            effect.deinit()

    def test_a_reset_that_only_cleared_the_mixer_would_be_silent(self):
        # The planted fault for the row above, and it is the ported node's
        # own behaviour rather than an invention: clear the Mixer and do not
        # hand its voices back their sources.
        class ClearOnly(CLASS):
            def _reset_mixer(self):
                audiocore.reset_buffer(self._mixer)
                for voice in self._mixer.voice:
                    voice.stop()

        values, on, second = two_bursts()
        source = probes.ArraySource(values, rate=RATE, block=256)
        effect = ClearOnly.create(source, RATE, **UNITY)
        try:
            self.assertTrue(render(effect, on + 64).data.any())
            effect.reset()
            self.assertFalse(render(effect, second + 4096).data.any())
        finally:
            effect.deinit()

    def test_resetting_the_mixer_first_leaves_the_ring_down_behind(self):
        # The planted fault for the row above. `audiomixer`'s reset resets
        # its voice's source and then pulls a chunk through it, so a walk
        # that reaches the Mixer before the biquads lands their tail in the
        # voice buffer, where nothing later in the walk can reach it.
        values, on = probes.burst_silence(hz=80.0, on_ms=40.0,
                                          total_s=0.3, dbfs=-2.0)
        effect = build(MixerResetTailFirst, probe=values, **UNITY)
        try:
            render(effect, on + 64)
            effect.reset()
            after = render(effect, 1024)
        finally:
            effect.deinit()
        self.assertGreater(int(abs(after.data).max()), 0)

    def test_the_head_of_the_render_uses_the_macros_crossover(self):
        # The voices are played after `_init_macros` for this reason: a
        # chunk taken at play() time is rendered through whatever the
        # biquads were set to then, and nothing later can reach it.
        values = probes.click_stereo(2048, offset=64)
        heads = {}
        for cls in (CLASS, PlayBeforeMacros):
            effect = build(cls, probe=values, crossover_low_hz=40.0,
                           crossover_high_hz=400.0, **UNITY)
            try:
                heads[cls] = render(effect, 256).digest
            finally:
                effect.deinit()
        self.assertNotEqual(heads[CLASS], heads[PlayBeforeMacros])

    def test_deinit_releases_the_nodes_and_leaves_the_source_rendering(self):
        source = probes.ArraySource(tone(440.0, 0.2), rate=RATE, block=256)
        effect = CLASS.create(source, RATE)
        nodes = list(effect._nodes)
        render(effect, 4096)
        effect.deinit()
        effect.deinit()                       # idempotent
        self.assertRaises(RuntimeError, getattr, effect, "output")
        refused = 0
        for node in nodes:
            try:
                audiocore.get_buffer(node)
            except Exception:                 # noqa: BLE001
                refused += 1
        self.assertGreater(refused, 0)
        audiocore.reset_buffer(source)
        self.assertTrue(probes.render(source, 4096).data.any())

    def test_every_invariant_also_holds_at_one_channel(self):
        values = probes.ramp_fs(8192, channels=1)
        effect = build(probe=values, channels=1, mix=0.0)
        try:
            self.assertEqual(effect.channel_count, 1)
            wet = render(effect, 8192, channels=1)
        finally:
            effect.deinit()
        dry = kit.Render(bytes(memoryview(values).cast("B")), RATE, 1)
        self.assertTrue(kit.wire(wet, dry)["passed"])


class Traits(unittest.TestCase):
    """M1..M5 in short form; the full sweeps are in
    `workspace docs/effects-internal/probes/phase2_probes/multiband_traits.py`."""

    M1_TONES = (30.0, 141.0, 283.0, 1000.0, 1414.0, 4000.0, 16000.0)

    def test_m1_the_bands_sum_flat_at_three_bands(self):
        for hz in self.M1_TONES:
            with self.subTest(hz=hz):
                self.assertLessEqual(
                    abs(sum_db(hz, crossover_low_hz=200.0,
                               crossover_high_hz=2000.0)), 0.25)

    def test_m1_the_bands_sum_flat_at_two_bands(self):
        for hz in self.M1_TONES:
            with self.subTest(hz=hz):
                self.assertLessEqual(
                    abs(sum_db(hz, bands=2, crossover_low_hz=800.0)), 0.25)

    def test_m1_without_the_clamp_a_two_to_one_split_is_eight_db_down(self):
        # The planted fault: the trait is stated *against* the clamp, so the
        # fault of the same kind is a build that accepts 200/400.
        worst = min(sum_db(hz, NoRatioClamp, crossover_low_hz=200.0,
                           crossover_high_hz=400.0)
                    for hz in (200.0, 283.0, 400.0))
        self.assertLess(worst, -1.0)

    def test_m2_each_corner_is_six_db_down_on_the_summed_halves(self):
        # Soloed, the low band at its own corner is -6 dB; summed with the
        # mid band it is unity, which is the in-phase half of the trait.
        effect = build(crossover_low_hz=200.0, crossover_high_hz=2000.0,
                       probe=tone(200.0, 0.35), **UNITY)
        try:
            for voice in range(4):
                effect._mixer.voice[voice].level = 1.0 if voice == 1 else 0.0
            soloed = tone_db(effect, 200.0) - source_db(200.0)
        finally:
            effect.deinit()
        self.assertAlmostEqual(soloed, -6.0, delta=0.5)
        self.assertLessEqual(abs(sum_db(200.0, crossover_low_hz=200.0,
                                        crossover_high_hz=2000.0)), 0.25)

    def test_m2_one_section_a_side_puts_the_corner_three_db_high(self):
        effect = build(LinkwitzRiley2, crossover_low_hz=200.0,
                       crossover_high_hz=2000.0, probe=tone(200.0, 0.35),
                       **UNITY)
        try:
            for voice in range(4):
                effect._mixer.voice[voice].level = 1.0 if voice == 1 else 0.0
            soloed = tone_db(effect, 200.0) - source_db(200.0)
        finally:
            effect.deinit()
        self.assertGreater(soloed, -5.5)

    def test_m3_a_driven_band_moves_and_the_others_do_not(self):
        level_db = -12.0 - 3.0103                      # a -12 dBFS peak sine
        ratio = 4.0
        threshold = level_db - 12.0 / (1.0 - 1.0 / ratio)
        settings = dict(UNITY)
        settings.update(crossover_low_hz=200.0, crossover_high_hz=2000.0)
        driving = dict(settings)
        driving.update(low_threshold_db=threshold, low_ratio=ratio)
        for hz, band, expected in ((63.0, 1, -12.0), (700.0, 2, 0.0),
                                   (8000.0, 3, 0.0)):
            with self.subTest(hz=hz):
                idle = build(probe=tone(hz, 0.35), **settings)
                driven = build(probe=tone(hz, 0.35), **driving)
                try:
                    for effect in (idle, driven):
                        for voice in range(4):
                            effect._mixer.voice[voice].level = (
                                1.0 if voice == band else 0.0)
                    moved = tone_db(driven, hz) - tone_db(idle, hz)
                finally:
                    idle.deinit()
                    driven.deinit()
                self.assertAlmostEqual(moved, expected, delta=0.5)

    def test_m4_latency_is_zero_and_the_click_agrees(self):
        for rate in (48000, 44100):
            with self.subTest(rate=rate):
                values = probes.click_stereo(int(0.2 * rate), offset=64)
                effect = build(probe=values, rate=rate, **UNITY)
                try:
                    reported = effect.latency_samples
                    wet = render(effect, len(values) // 2, rate=rate)
                finally:
                    effect.deinit()
                dry = kit.Render(bytes(memoryview(values).cast("B")), rate, 2)
                result = kit.click(wet, dry, reported, subsample=False,
                                   tolerance_samples=0.0)
                self.assertEqual(reported, 0)
                self.assertTrue(result["passed"], result["red"])

    def test_m4_a_misreported_latency_is_red(self):
        # The DSP is untouched: only the report moves, which is what makes
        # this a latency fault and not a sound one.
        class Late(CLASS):
            LATENCY_SAMPLES = 256
        values = probes.click_stereo(9600, offset=64)
        effect = build(Late, probe=values, **UNITY)
        try:
            wet = render(effect, len(values) // 2)
        finally:
            effect.deinit()
        dry = kit.Render(bytes(memoryview(values).cast("B")), RATE, 2)
        result = kit.click(wet, dry, 256, subsample=False,
                           tolerance_samples=0.0)
        self.assertFalse(result["passed"])

    def test_m5_the_render_is_the_same_at_every_source_block(self):
        digests = set()
        for block in (256, 8192, 16384, 20000, 32768):
            effect = build(probe=tone(220.0, 0.75, dbfs=-6.0), block=block,
                           **UNITY)
            try:
                wet = render(effect, 8192)
            finally:
                effect.deinit()
            self.assertTrue(wet.data.any(), "silent at block %d" % block)
            digests.add(wet.digest)
        self.assertEqual(len(digests), 1)

    def _ladder(self, cls, blocks=(256, 16384, 32768), old_ring=False):
        digests = set()
        for block in blocks:
            source = probes.ArraySource(tone(220.0, 0.75, dbfs=-6.0),
                                        rate=RATE, block=block, channels=2)
            if old_ring:
                source = OldRingSource(source)
            effect = cls.create(source, RATE, **UNITY)
            try:
                digests.add(render(effect, 8192).digest)
            finally:
                effect.deinit()
        return digests

    def test_m5_goes_red_on_a_source_that_keeps_only_its_ring(self):
        """M5's fault, rebuilt for audioif `977ef26`.

        The old fault was `NoGuard`, and it cannot fire any more: the
        Splitter takes an oversized call in pieces (audioif#87), so the
        class renders the same bytes with the guard and without it. The
        fault that still fires is a source that does what the Splitter used
        to - hand back only its last 8192 frames.
        """
        self.assertGreater(len(self._ladder(CLASS, old_ring=True)), 1)
        self.assertGreater(len(self._ladder(NoGuard, old_ring=True)), 1)

    def test_m5_the_guard_no_longer_changes_the_render(self):
        """The regression test for audioif#87, and what says the guard may go.

        `_build_input`'s `Filter` was there to stop the Splitter dropping
        the head of an oversized block. At this floor it is a copy that
        changes nothing: the ladder is one digest with it and the same one
        digest without it.
        """
        blocks = (256, 8192, 16384, 20000, 32768)
        guarded = self._ladder(CLASS, blocks)
        unguarded = self._ladder(NoGuard, blocks)
        self.assertEqual(len(guarded), 1)
        self.assertEqual(guarded, unguarded)

    def test_m5_burst_material_survives_an_oversized_block(self):
        """The dossier's A-M5, the other way up.

        It used to read: without the guard, the dropped head is the whole
        signal, so a 40 ms burst at the top of a long block renders
        silence. At this floor nothing is dropped, so the burst is there at
        every block size, guarded or not - and it disappears only on the
        old ring.
        """
        def nonzero(cls, block, old_ring=False):
            burst, _on = probes.burst_silence(hz=440.0, on_ms=40.0,
                                              total_s=0.6)
            source = probes.ArraySource(burst, rate=RATE, block=block,
                                        channels=2)
            if old_ring:
                source = OldRingSource(source)
            effect = cls.create(source, RATE, **UNITY)
            try:
                return int((render(effect, 8192).data != 0).sum())
            finally:
                effect.deinit()

        short = nonzero(CLASS, 256)
        self.assertGreater(short, 0)
        for cls in (CLASS, NoGuard):
            for block in (256, 16384):
                self.assertEqual(nonzero(cls, block), short)
        # The same material on the old ring is the silence A-M5 described.
        self.assertEqual(nonzero(CLASS, 16384, old_ring=True), 0)


if __name__ == "__main__":
    unittest.main()
