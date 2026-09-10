"""The Phase 2 construction module, held to what roadmap section 3 asks of it.

Every check that can go wrong quietly is paired with a **planted fault**: a
deliberately mis-built class of the same shape, asserted red by the same
read that asserts the correct build green. A battery with no fault beside it
only proves the checker never fires.

VENDOR is at module level because `_component` reads it there -- these test
classes are exercising the metadata rule, not exempt from it.
"""

import array
import gc
import sys
import tracemalloc
import unittest

import audiocore
import audioecho
import audiofilters
import synthio

from audioeffects import _component


VENDOR = "PyDevices"

RATE = 48000
CHANNELS = 2
#: Silence, then a short square burst, then silence to the end. The burst is
#: what fills a delay line; the silence after it is what makes the line's
#: leftover contents audible on their own.
#:
#: The silence **before** it is not decoration. A node whose pending buffer
#: is emptied re-reads its source, and `audiocore.RawSample` hands its
#: buffer back from the beginning, so a chain that has just been reset is
#: reading the head of this array. A burst at frame 0 would replay there and
#: read exactly like a delay line that was never cleared -- the confound
#: that failed the first draft of this file. `LEAD` frames of silence give
#: the measurement somewhere to stand.
LEAD = 8192
BURST = 512
FRAMES = 40000


def source(frames=FRAMES, channels=CHANNELS, rate=RATE):
    values = array.array("h")
    for frame in range(frames):
        value = 0
        if LEAD <= frame < LEAD + BURST:
            value = 12000 if (frame // 16) % 2 == 0 else -12000
        for _ in range(channels):
            values.append(value)
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def peak(sample, blocks=2):
    loudest = 0
    for _ in range(blocks):
        data = bytes(audiocore.get_buffer(sample)[1])
        for index in range(0, len(data) - 1, 2):
            value = data[index] | (data[index + 1] << 8)
            if value >= 32768:
                value -= 65536
            loudest = max(loudest, -value if value < 0 else value)
    return loudest


class TwoNodes(_component.Component):
    """A delay into a filter: two nodes, so `reset()` and `deinit()` have a
    list to walk rather than a tail to touch."""

    NAME = 'TwoNodes'
    TIER = _component.AUDIOIF
    REQUIRES = ("audioecho",)
    MACRO_LABELS = ("Feedback",)
    MACRO_MODES = {0: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 0.95),)
    PATCHES = {0: ("Default", (120,)), 1: ("Dry", (0,))}

    #: False on the planted-fault subclasses below, which own less than they
    #: built -- the defect roadmap section 3 names.
    OWN_THE_DELAY = True
    RELEASE_THE_DELAY = True

    def _build(self, feedback=0.9, patch=None):
        self.delay = audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=50.0, delay_ms=10.0, feedback=feedback, mix=1.0)
        self.delay.play(self._source)
        if self.OWN_THE_DELAY:
            self._own(self.delay, deinit=self.RELEASE_THE_DELAY)
        self.biquad = synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                     12000.0, Q=0.707)
        self.tail = self._own(audiofilters.Filter(
            filter=self.biquad, mix=1.0, **self._pcm()))
        self.tail.play(self.delay)
        self._output = self.tail
        self._init_macros((feedback,), patch)

    def _apply_macro(self, index, position):
        self.delay.set(feedback=_component.macro_value(
            self._MACRO_RANGES[0], position))


class OnlyOwnsTheTail(TwoNodes):
    """Planted fault: the class builds two nodes and enumerates one, which
    is what `_core.reset()` does to every chain today."""

    NAME = 'OnlyOwnsTheTail'
    OWN_THE_DELAY = False


class KeepsTheDelayLive(TwoNodes):
    """Planted fault: an intermediate node left live after `deinit()` --
    named as a fault by the kit spec's STATE measurement."""

    NAME = 'KeepsTheDelayLive'
    RELEASE_THE_DELAY = False


class Wire(_component.Component):
    """The smallest legal class: one stock-tier node, no macros."""

    NAME = 'Wire'
    TIER = _component.STOCK
    MACRO_LABELS = ()
    MACRO_MODES = {}
    _MACRO_RANGES = ()
    PATCHES = {0: ("Default", ())}

    def _build(self, cutoff_hz=1000.0):
        self.frequency = cutoff_hz
        self.biquad = synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                     self._hz(cutoff_hz), Q=0.707)
        node = self._own(audiofilters.Filter(filter=self.biquad, mix=1.0,
                                             **self._pcm()))
        node.play(self._source)
        self._output = node


class FormatComesFromTheFactory(unittest.TestCase):
    def test_the_factory_rate_must_match_the_source(self):
        with self.assertRaises(ValueError) as caught:
            Wire.create(source(), 44100)
        self.assertIn("does not resample", str(caught.exception))

    def test_the_factory_rate_is_a_positive_integer(self):
        for bad in (0, -48000, 48000.0, True):
            with self.subTest(rate=bad):
                with self.assertRaises(ValueError):
                    Wire.create(source(), bad)

    def test_direct_construction_takes_the_format_off_the_source(self):
        # No configure() anywhere: the source carries the format, and this
        # is the local-code path roadmap section 3 requires to keep working.
        effect = Wire(source(rate=22050), cutoff_hz=2000.0)
        self.addCleanup(effect.deinit)
        self.assertEqual(effect.sample_rate, 22050)
        self.assertEqual(effect.channel_count, CHANNELS)

    def test_a_mono_source_is_reported_as_mono(self):
        effect = Wire.create(source(channels=1), RATE)
        self.addCleanup(effect.deinit)
        self.assertEqual(effect.channel_count, 1)
        self.assertEqual(effect.output.channel_count, 1)

    def test_a_source_without_a_format_is_refused(self):
        with self.assertRaises(TypeError):
            Wire.create(object(), RATE)

    def test_hz_clamps_below_nyquist_rather_than_refusing(self):
        # Rate-honesty: a 12 kHz corner on a 22.05 kHz graph becomes the
        # highest corner that rate has, not an exception mid-piece.
        effect = Wire(source(rate=22050), cutoff_hz=12000.0)
        self.addCleanup(effect.deinit)
        self.assertAlmostEqual(effect._hz(12000.0),
                               22050 * 0.5 * _component.NYQUIST_MARGIN,
                               places=6)
        self.assertEqual(effect._hz(0.0), 1.0)


class ResetAndDeinitWalkTheNodeList(unittest.TestCase):
    def primed(self, cls):
        """A chain pulled past the end of its burst, so the delay line still
        holds audible repeats while the source itself is silent."""
        effect = cls.create(source(), RATE)
        self.addCleanup(effect.deinit)
        self.assertGreater(peak(effect.output, blocks=20), 0,
                           "the probe must reach the delay line at all")
        return effect

    def after_reset(self, effect):
        """What the chain renders once reset, past the one block of already
        pulled audio the tail still holds."""
        effect.reset()
        peak(effect.output, blocks=1)
        return peak(effect.output, blocks=4)

    def test_reset_clears_every_node_the_class_built(self):
        self.assertEqual(self.after_reset(self.primed(TwoNodes)), 0)

    def test_planted_fault_a_node_left_off_the_list_survives_reset(self):
        # The same read, on a class that enumerates its tail and not the
        # delay in front of it -- which is what `_core.reset()` does to
        # every chain today (roadmap section 3).
        self.assertGreater(
            self.after_reset(self.primed(OnlyOwnsTheTail)), 0,
            "the read must go red when a node is left off the list")

    def test_reset_walks_the_whole_list_tail_first(self):
        """The audio arm above shows one node's state surviving. This shows
        the walk itself: every node the class enumerated, in reverse of the
        order it was built, and nothing else."""
        effect = TwoNodes.create(source(), RATE)
        self.addCleanup(effect.deinit)
        seen = []
        original = audiocore.reset_buffer
        audiocore.reset_buffer = lambda node, *rest: seen.append(node)
        try:
            effect.reset()
        finally:
            audiocore.reset_buffer = original
        self.assertEqual(seen, [effect.tail, effect.delay])

    def test_planted_fault_the_walk_misses_an_unenumerated_node(self):
        effect = OnlyOwnsTheTail.create(source(), RATE)
        self.addCleanup(effect.deinit)
        seen = []
        original = audiocore.reset_buffer
        audiocore.reset_buffer = lambda node, *rest: seen.append(node)
        try:
            effect.reset()
        finally:
            audiocore.reset_buffer = original
        self.assertEqual(seen, [effect.tail])
        self.assertNotIn(effect.delay, seen)

    def test_the_walk_never_names_the_borrowed_source(self):
        signal = source()
        effect = TwoNodes.create(signal, RATE)
        self.addCleanup(effect.deinit)
        seen = []
        original = audiocore.reset_buffer
        audiocore.reset_buffer = lambda node, *rest: seen.append(node)
        try:
            effect.reset()
        finally:
            audiocore.reset_buffer = original
        self.assertNotIn(signal, seen)

    def test_reset_restores_patch_zero(self):
        effect = TwoNodes.create(source(), RATE)
        self.addCleanup(effect.deinit)
        effect.set_macro(0, 3)
        self.assertIsNone(effect.patch_index)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)

    def test_reset_leaves_the_borrowed_source_rendering(self):
        signal = source()
        effect = TwoNodes.create(signal, RATE)
        self.addCleanup(effect.deinit)
        peak(effect.output, blocks=4)
        effect.reset()
        # The source is a borrowed object: reset() may not touch it, and it
        # must still hand out audio afterwards.
        self.assertEqual(len(bytes(audiocore.get_buffer(signal)[1])) % 4, 0)

    def test_deinit_releases_every_node_the_class_built(self):
        effect = TwoNodes.create(source(), RATE)
        delay = effect.delay
        effect.deinit()
        with self.assertRaises(RuntimeError):
            audiocore.get_buffer(delay)

    def test_planted_fault_an_intermediate_node_left_live(self):
        effect = KeepsTheDelayLive.create(source(), RATE)
        delay = effect.delay
        effect.deinit()
        audiocore.get_buffer(delay)      # no RuntimeError: the fault

    def test_deinit_is_idempotent_and_spares_the_source(self):
        signal = source()
        effect = TwoNodes.create(signal, RATE)
        effect.deinit()
        effect.deinit()
        self.assertGreater(len(bytes(audiocore.get_buffer(signal)[1])), 0)
        with self.assertRaises(RuntimeError):
            effect.output

    def test_a_class_may_not_own_its_borrowed_source(self):
        class OwnsTheSource(Wire):
            NAME = 'OwnsTheSource'

            def _build(self, cutoff_hz=1000.0):
                self._own(self._source)

        with self.assertRaises(ValueError):
            OwnsTheSource.create(source(), RATE)


class TheLiveSurface(unittest.TestCase):
    def effect(self):
        built = TwoNodes.create(source(), RATE)
        self.addCleanup(built.deinit)
        return built

    def test_construction_applies_patch_zero(self):
        self.assertEqual(self.effect().patch_index, 0)

    def test_a_macro_move_enters_custom_state(self):
        effect = self.effect()
        effect.set_macro(0, 64)
        self.assertIsNone(effect.patch_index)
        self.assertAlmostEqual(effect.get_macro(0), 64.0, places=6)
        effect.program_change(1)
        self.assertEqual(effect.patch_index, 1)

    def test_an_unknown_program_is_ignored_not_an_error(self):
        effect = self.effect()
        effect.program_change(97)
        self.assertEqual(effect.patch_index, 0)

    def test_a_bad_macro_index_raises_index_error(self):
        effect = self.effect()
        for bad in (1, -1, True, "0"):
            with self.subTest(index=bad):
                with self.assertRaises(IndexError):
                    effect.get_macro(bad)
                with self.assertRaises(IndexError):
                    effect.set_macro(bad, 64)

    def test_the_four_non_note_midi_handlers_are_safe(self):
        effect = self.effect()
        effect.pitch_bend(8192)
        effect.control_change(74, 100)
        effect.channel_pressure(64)
        effect.poly_pressure(60, 64)
        with self.assertRaises(ValueError):
            effect.pitch_bend(70000)
        with self.assertRaises(ValueError):
            effect.control_change(200, 0)

    def test_static_reads_describe_the_build(self):
        effect = self.effect()
        self.assertEqual(effect.latency_samples, 0)
        self.assertIsNone(effect.tail_samples)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.sample_rate, RATE)
        self.assertEqual(effect.channel_count, CHANNELS)

    def test_reading_output_allocates_nothing(self):
        # The per-block no-allocation rule is the kit's STATE measurement on
        # MicroPython, where `audiocore.get_buffer` does not copy. What can
        # be shown here is the half this module owns: the property itself
        # puts no Python allocation between a host and the node.
        effect = self.effect()
        for _ in range(50):
            effect.output
        gc.collect()
        tracemalloc.start()
        first = tracemalloc.get_traced_memory()[0]
        for _ in range(200):
            effect.output
        second = tracemalloc.get_traced_memory()[0]
        for _ in range(200):
            effect.output
        third = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        # Two windows, not one: the first carries tracemalloc's own 56 bytes
        # of bookkeeping for the frame it starts in, which is not the
        # subject. The marginal cost of 200 more reads is the subject.
        #
        # The rule is that WE allocate nothing per read, and on 3.11+ that is
        # exactly measurable: the marginal cost is zero. Python 3.10 still
        # heap-allocates a frame object for each Python-to-Python call (3.11
        # inlined them), so `output` -> `_check_live` charges the interpreter's
        # own bookkeeping to this window -- 73 bytes across 200 reads when this
        # first appeared. That is not ours to remove, short of deleting the
        # liveness check the property exists to perform, so 3.10 gets the same
        # small tolerance the first window already uses. 3.11+ stays exact, and
        # would still catch a real per-read allocation.
        if sys.version_info >= (3, 11):
            self.assertEqual(third - second, 0)
        else:
            self.assertLess(third - second, 200)
        self.assertLess(second - first, 200)


class TheMetadataShape(unittest.TestCase):
    """Every rule roadmap section 3 freezes, each with a class that breaks
    exactly it."""

    def build(self, **fields):
        namespace = {
            "NAME": "Broken%d" % len(_component._CHECKED),
            "TIER": _component.STOCK,
            "MACRO_LABELS": ("A",),
            "MACRO_MODES": {0: "UNIPOLAR"},
            "_MACRO_RANGES": ((0.0, 1.0),),
            "PATCHES": {0: ("Default", (0,))},
            "_build": lambda self, **options: None,
            "_apply_macro": lambda self, index, position: None,
        }
        namespace.update(fields)
        return type(namespace["NAME"], (_component.Component,), namespace)

    def refuse(self, message, **fields):
        cls = self.build(**fields)
        with self.assertRaises(_component.MetadataError) as caught:
            cls.create(source(), RATE)
        self.assertIn(message, str(caught.exception))

    def test_seventeen_macros_is_one_too_many(self):
        labels = tuple("M%d" % index for index in range(17))
        self.refuse("at most 16", MACRO_LABELS=labels,
                    MACRO_MODES={index: "UNIPOLAR" for index in range(17)},
                    _MACRO_RANGES=tuple((0.0, 1.0) for _ in range(17)),
                    PATCHES={0: ("Default", (0,) * 17)})

    def test_macro_labels_must_be_unique(self):
        self.refuse("must be unique", MACRO_LABELS=("A", "A"),
                    MACRO_MODES={0: "UNIPOLAR", 1: "UNIPOLAR"},
                    _MACRO_RANGES=((0.0, 1.0), (0.0, 1.0)),
                    PATCHES={0: ("Default", (0, 0))})

    def test_one_mode_per_label(self):
        self.refuse("one entry per label", MACRO_MODES={})

    def test_a_mode_must_be_one_of_the_three(self):
        self.refuse("must be one of", MACRO_MODES={0: "CONTINUOUS"})

    def test_one_span_per_label(self):
        self.refuse("one span per macro label", _MACRO_RANGES=())

    def test_patches_are_contiguous_from_zero(self):
        self.refuse("contiguous from 0",
                    PATCHES={0: ("A", (0,)), 2: ("B", (1,))})

    def test_patch_values_are_midi_integers(self):
        self.refuse("MIDI integers", PATCHES={0: ("Default", (128,))})

    def test_a_toggle_is_zero_or_127(self):
        self.refuse("TOGGLE values", MACRO_MODES={0: "TOGGLE"},
                    PATCHES={0: ("Default", (64,))})

    def test_patch_names_are_unique(self):
        self.refuse("patch names must be unique",
                    PATCHES={0: ("Same", (0,)), 1: ("Same", (1,))})

    def test_a_class_must_have_a_patch_zero(self):
        self.refuse("at least patch 0", PATCHES={})

    def test_the_tier_must_be_one_of_the_two(self):
        self.refuse("TIER must be", TIER="portable")

    def test_the_audioif_tier_names_its_modules(self):
        self.refuse("must name the modules", TIER=_component.AUDIOIF)

    def test_the_stock_tier_may_not_require_one(self):
        self.refuse("may not require", REQUIRES=("audioecho",))

    def test_requires_may_only_name_a_real_audioif_module(self):
        self.refuse("not an audioif-own module", TIER=_component.AUDIOIF,
                    REQUIRES=("audioecho2",))

    def test_vendor_is_read_from_the_defining_module(self):
        cls = self.build()
        module = __import__(cls.__module__, fromlist=["*"])
        vendor = module.VENDOR
        del module.VENDOR
        try:
            with self.assertRaises(_component.MetadataError) as caught:
                cls.create(source(), RATE)
            self.assertIn("VENDOR", str(caught.exception))
        finally:
            module.VENDOR = vendor

    def test_a_well_formed_class_passes(self):
        # The control beside the battery: the same shape, nothing broken.
        effect = Wire.create(source(), RATE)
        self.addCleanup(effect.deinit)
        self.assertEqual(effect.patch_index, 0)

    def test_build_must_seed_every_macro(self):
        class ForgetsItsMacros(Wire):
            NAME = 'ForgetsItsMacros'
            MACRO_LABELS = ("A",)
            MACRO_MODES = {0: "UNIPOLAR"}
            _MACRO_RANGES = ((0.0, 1.0),)
            PATCHES = {0: ("Default", (0,))}

            def _apply_macro(self, index, position):
                pass

        with self.assertRaises(TypeError) as caught:
            ForgetsItsMacros.create(source(), RATE)
        self.assertIn("_init_macros", str(caught.exception))

    def test_build_must_set_an_output(self):
        class BuildsNothing(Wire):
            NAME = 'BuildsNothing'

            def _build(self, cutoff_hz=1000.0):
                pass

        with self.assertRaises(TypeError) as caught:
            BuildsNothing.create(source(), RATE)
        self.assertIn("set no output", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
