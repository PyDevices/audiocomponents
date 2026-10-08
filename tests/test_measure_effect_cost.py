"""The cost tool's Phase 5 additions (housekeeping, 2026-09-28).

`tools/measure_effect_cost.py` is a board tool and its timings are not
desktop facts, so this checks only what the desktop can: the two new palette
rows render what the boards rendered, and an effect target finds the palette
row it is measured beside without importing anything to do it.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import measure_effect_cost as m                  # noqa: E402


def digest(key):
    probe = m.Probe()
    output, extras, keep = m.resolve("node:" + key)(probe)
    value = m._warm(output, extras, True)[0]
    del keep
    return value


class TheNewRows(unittest.TestCase):
    def test_feedback_09_is_the_row_the_boards_took(self):
        # Both boards and both desktop legs rendered this at audiodsp
        # v0.6.2; at v0.6.1 it
        # was d9fb49a51cd7379a, which is why the row exists.
        self.assertEqual(digest("audioecho.FeedbackDelay@fb0.9"),
                         "3b76320cb19450a8")
        # The 0.45 row renders other bytes; a 0.9 row that fell back to it
        # would be red here.
        self.assertEqual(digest("audioecho.FeedbackDelay"),
                         "a6abc903a9e8e073")

    def test_the_damping_row_turns_the_loop_low_pass_on(self):
        options = digest("audioecho.FeedbackDelay@options")
        self.assertEqual(options, "e7a07359012d7a8e")
        self.assertEqual(digest("audioecho.FeedbackDelay@options+damping"),
                         "9e06dd6c5d8a2f38")


class TheBesideRow(unittest.TestCase):
    def test_a_class_target_names_its_class(self):
        for target, name in (
                ("rebuilt:DigitalDelay@5", "DigitalDelay"),
                ("effect:SlapbackDelay#3", "SlapbackDelay"),
                ("rebuilt:Fuzz@ch-cascade@os2@4", "Fuzz"),
                ("DigitalDelay", "DigitalDelay"),
                ("source", None),
                ("node:audioecho.FeedbackDelay", None),
                ("audioecho.FeedbackDelay@options", None)):
            self.assertEqual(m._class_name(target), name, target)

    def test_every_named_row_is_a_node_row(self):
        for name, key in m.BESIDE.items():
            self.assertIn(key, m.NODES, name)
            self.assertIs(m.resolve("node:" + key), m.NODES[key])
        self.assertEqual(m.BESIDE["DigitalDelay"],
                         "audioecho.FeedbackDelay@options")
        self.assertEqual(m.BESIDE["SlapbackDelay"],
                         "audioecho.FeedbackDelay@options")
        with self.assertRaises(ValueError):
            m.resolve("node:audioecho.FeedbackDelay@nosuchrow")


if __name__ == "__main__":
    unittest.main()
