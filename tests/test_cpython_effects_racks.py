"""The rack kind as it stands today: `Rack`, `ShimmerHall`, `AirSpace`.

Retired by the effects program's **phase 6 - pitch, stereo, racks**, which
rebuilds the three racks on their rebuilt children.
`test_a_preset_rack_macro_moves_its_child` reaches into `ShimmerHall`'s
internals by name and the two shipped presets are exactly what that phase
re-cuts, so this module goes when they do. A rack has exactly the effect
shape, so the contract-level tests over `audioeffects.ALL` already cover
these three the way they cover any other effect; what is here is the rack-
specific behavior. """

import os
import sys
import unittest

import audioeffects
from tools.validate_metadata import validate_component

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
from effects_measure import SAMPLE_RATE, peak, source  # noqa: E402


class RackTest(unittest.TestCase):
    """The rack kind: one component whose graph is several effects.

    Ported from micropython-vst3's soundtrack racks; the mechanism is
    `audioeffects.Rack` and the two shared presets are `ShimmerHall` and
    `AirSpace`. A rack has exactly the effect shape, so everything the
    catalogue-wide tests assert already covers these three classes - what
    is here is the rack-specific behavior.
    """

    CHAIN = (("Overdrive", {"drive": 0.3, "mix": 0.4}),
             ("Reverb", {"preset": "plate", "mix": 0.25}))

    def test_a_chain_spec_builds_children_in_order_and_renders(self):
        rack = audioeffects.create("Rack", source(), SAMPLE_RATE,
                                   chain=self.CHAIN)
        self.assertEqual([type(child).__name__ for child in rack.effects],
                         ["Overdrive", "Reverb"])
        # Each child is fed the previous one's output, and the rack's
        # output is the last child's.
        self.assertIs(rack.effects[1]._source, rack.effects[0].output)
        self.assertIs(rack.output, rack.effects[1].output)
        self.assertGreater(peak(rack.output, 8), 0.001)

    def test_a_bare_name_is_a_valid_chain_entry(self):
        rack = audioeffects.Rack(source(), chain=("Saturation", "Reverb"))
        self.assertEqual(len(rack.effects), 2)
        self.assertGreater(peak(rack.output, 8), 0.001)

    def test_an_empty_rack_is_a_wire(self):
        src = source()
        rack = audioeffects.create("Rack", src, SAMPLE_RATE)
        self.assertIs(rack.output, src)
        self.assertEqual(rack.latency_samples, 0)
        self.assertEqual(rack.tail_samples, 0)
        self.assertGreater(peak(rack.output, 8), 0.001)

    def test_a_malformed_chain_entry_is_refused(self):
        with self.assertRaises(ValueError):
            audioeffects.Rack(source(), chain=(42,))
        with self.assertRaises(ImportError):
            audioeffects.Rack(source(), chain=("NoSuchEffect",))

    def test_racks_nest(self):
        # "Racks may contain and be used by other racks" - both directions.
        inner = ("Rack", {"chain": (("Saturation", {"amount": 0.2}),)})
        outer = audioeffects.Rack(source(), chain=(
            inner, ("Reverb", {"preset": "room", "mix": 0.2})))
        self.assertEqual(type(outer.effects[0]).__name__, "Rack")
        self.assertGreater(peak(outer.output, 8), 0.001)

    def test_latency_and_tail_are_the_whole_graph(self):
        rack = audioeffects.Rack(source(), chain=self.CHAIN)
        self.assertEqual(rack.latency_samples,
                         sum(child.latency_samples
                             for child in rack.effects))
        # No shipped effect bounds its tail yet, so one unknown child tail
        # makes the graph's unknown; the empty-rack test pins the finite
        # case at zero.
        self.assertIsNone(rack.tail_samples)

    def test_deinit_releases_the_children_but_not_the_source(self):
        src = source()
        rack = audioeffects.Rack(src, chain=self.CHAIN)
        children = list(rack.effects)
        rack.deinit()
        rack.deinit()
        with self.assertRaises(RuntimeError):
            _ = rack.output
        for child in children:
            with self.assertRaises(RuntimeError):
                _ = child.output
        # The borrowed source is still a live sample.
        self.assertGreater(peak(src, 2), 0.001)

    def test_rack_metadata_is_valid_component_metadata(self):
        from audioeffects import rack as module
        for cls in (audioeffects.Rack, audioeffects.ShimmerHall,
                    audioeffects.AirSpace):
            validate_component(cls, kind="effect",
                               expected_name=cls.__name__,
                               vendor_owner=module)

    def test_a_preset_rack_macro_moves_its_child(self):
        rack = audioeffects.ShimmerHall(source())
        self.assertEqual(rack.patch_index, 0)
        rack.set_macro(0, 0)
        self.assertEqual(rack.octave.mixer.voice[1].level, 0.0)
        self.assertIsNone(rack.patch_index)
        rack.set_macro(2, 127)
        self.assertAlmostEqual(rack.hall.node.mix, 0.7, delta=1e-6)
        rack.program_change(0)
        self.assertEqual(rack.patch_index, 0)
        self.assertAlmostEqual(rack.octave.mixer.voice[1].level,
                               70 / 127, delta=1e-6)

    def test_the_preset_racks_chain_audio_through_their_children(self):
        for name in ("ShimmerHall", "AirSpace"):
            rack = getattr(audioeffects, name)(source())
            self.assertGreaterEqual(len(rack.effects), 3)
            self.assertGreater(peak(rack.output, 8), 0.001, name)


if __name__ == "__main__":
    unittest.main()
