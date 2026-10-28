"""The effects kit's own proof: every check goes red on a planted fault and
its control is green on the same cell, and a class that does nothing at
all is never read as a pass.

The plants are the tiny components in `tests/support/kit_planted.py`;
`KIT.md` beside the kit says what each check measures. The native half
runs the kit's render checks under MicroPython and CircuitPython and holds
them to CPython's lines, and shows that a plant whose output depends on
the interpreter is caught; it skips when a binary is missing.

    OMP_NUM_THREADS=1 python -m unittest tests.test_kit
"""

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "lib"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import kit_args                                           # noqa: E402
import kit_ceiling                                        # noqa: E402
import kit_claims                                         # noqa: E402
import kit_fresh                                          # noqa: E402
import kit_levels                                         # noqa: E402
import kit_common as kc                                   # noqa: E402
import kit_nogb                                           # noqa: E402
import kit_paperwork                                      # noqa: E402
import kit_planted as kp                                  # noqa: E402
import kit_plants                                         # noqa: E402
import kit_tail                                           # noqa: E402
import lifecycle                                          # noqa: E402

#: `_component` reads VENDOR off the module a class is defined in.
VENDOR = "PyDevices"


def cells_of(fn, *args, **kw):
    lines = []
    fn(*args, emit=lines.append, **kw)
    return kc.parse(lines)


def verdict(cells, name, check, key):
    return cells[(name, check, key)]["V"]


def tail_cell(cls, key="fs/48000/2/d/none", **kw):
    """One tail cell (material/rate/channels/patch/event)."""
    which, rate, ch, patch, event = key.split("/")[:5]
    cells = cells_of(kit_tail.run, cls, rates=(int(rate),),
                     channels=(int(ch),),
                     patches=[None if patch == "d" else int(patch[1:])],
                     materials=(which,), events=(event,), quick=True, **kw)
    return verdict(cells, cls.NAME, "tail", key)


def red(v):
    return v.startswith("RED")


class TestTail(unittest.TestCase):

    def test_a_short_tail_is_red_and_a_true_one_green(self):
        for key in ("fs/48000/2/d/none", "lsb3/22050/1/d/none",
                    "dc/48000/1/d/none"):
            with self.subTest(key=key):
                self.assertTrue(red(tail_cell(kp.ShortTail, key)))
                self.assertEqual(tail_cell(kp.EchoTail, key), "ok")

    def test_the_tail_is_read_after_every_event(self):
        # EventTail tells the truth until a control moves.
        self.assertEqual(tail_cell(kp.EventTail, "fs/48000/2/d/none"), "ok")
        for event in ("E4-m1=127", "E5-mix0", "E6-p1"):
            key = "fs/48000/2/d/" + event
            with self.subTest(event=event):
                self.assertTrue(red(tail_cell(kp.EventTail, key)))
                self.assertEqual(tail_cell(kp.EchoTail, key), "ok")

    def test_the_events_are_lifecycles(self):
        names = [n for n, _ev, _p in kit_tail.tail_events(kp.KitPlain, None,
                                                         False)]
        for ev in lifecycle.events(kp.KitPlain, None):
            if lifecycle._starts(ev.name, kit_tail.EVENT_PREFIXES):
                self.assertIn(ev.name, names)
        self.assertIn("none", names)

    def test_tail_none_must_never_fall_silent(self):
        self.assertTrue(tail_cell(kp.NoneSilent).startswith(
            "RED(tail None, silent"))
        self.assertEqual(tail_cell(kp.NoneDC), "na(tail None)")

    def test_a_silent_class_is_not_a_pass(self):
        self.assertEqual(tail_cell(kp.Silent), "na(silent)")

    def test_a_declared_cell_prints_decl(self):
        kc.DECLARED[("ShortTail", "tail", "fs/48000")] = "planted"
        try:
            self.assertEqual(tail_cell(kp.ShortTail), "decl")
        finally:
            del kc.DECLARED[("ShortTail", "tail", "fs/48000")]


class TestPlants(unittest.TestCase):

    def setUp(self):
        self.cells = cells_of(kit_plants.run, kp.KitPlain,
                              plants=kp.KIT_PLANTS)

    def v(self, key):
        return verdict(self.cells, "KitPlain", "plants", key)

    def test_an_inert_plant_is_red(self):
        self.assertEqual(self.v("inert/48000/2/d"),
                         "RED(same as clean at the defaults)")

    def test_a_plant_a_knob_reaches_is_red(self):
        self.assertEqual(self.v("knob/48000/2/d"),
                         "RED(reproduced by m1=0)")

    def test_a_real_plant_is_green(self):
        self.assertEqual(self.v("valid/48000/2/d"), "ok")

    def test_a_plant_judged_at_its_patch(self):
        # The same plant: invisible at the defaults, a fault at patch 1.
        self.assertEqual(self.v("soft-at-d/48000/2/d"),
                         "RED(same as clean at the defaults)")
        self.assertEqual(self.v("soft/48000/2/p1"), "ok")

    def test_a_patch_reproducing_a_plant_is_red(self):
        class AtSoft(kp.KitPlain):
            def _build(self, mix=1.0, gain=1.0, patch=None):
                kp.KitPlain._build(self, mix, gain, 1)
        cells = cells_of(kit_plants.run, kp.KitPlain,
                         plants={"soft": AtSoft})
        self.assertEqual(verdict(cells, "KitPlain", "plants",
                                 "soft/48000/2/d"),
                         "RED(reproduced by patch 1)")

    def test_a_missing_table_says_so(self):
        cells = cells_of(kit_plants.run, kp.KitPlain, module="kit_common")
        self.assertTrue(verdict(cells, "KitPlain", "plants", "-")
                        .startswith("na(kit_common has no KIT_PLANTS"))

    def test_plants_are_read_from_the_claims_module(self):
        # Two classes whose test file is not named after them.
        import audioeffects
        for cls in (audioeffects.NoiseGate,
                    audioeffects.MultibandCompressor):
            plants, why = kit_plants.load_plants(cls)
            self.assertIsNone(why, cls.NAME)
            self.assertTrue(plants, cls.NAME)


class TestArgs(unittest.TestCase):

    CASES = (
        (kp.ReadbackOff, "rt-m1/48000/d", kit_args.roundtrip,
         (1, 48000, None)),
        (kp.StopRaises, "stops-m1", kit_args.stops_cell, (1,)),
        (kp.NanLevel, "bad-m1", kit_args.bad_cell, (1,)),
        (kp.PatchStale, "patch-p1", kit_args.patch_cell, (1,)),
        (kp.CtorNan, "ctor-gain", kit_args.ctor_cell, ("gain",)),
    )

    @staticmethod
    def call(fn, cls, args):
        got = fn(cls, *args)
        return got[0] if isinstance(got, tuple) else got

    def test_each_plant_is_red_and_the_control_green(self):
        for plant, key, fn, args in self.CASES:
            with self.subTest(cell=key):
                self.assertTrue(red(self.call(fn, plant, args)), plant.NAME)
                self.assertTrue(self.call(fn, kp.KitPlain, args)
                                .startswith("ok"), key)

    def test_a_refused_call_that_moves_something_is_red(self):
        # ClearsFirst zeroes the level before it validates (a render that
        # differs); ClearsMacro moves a macro, or drops the patch, first.
        for plant, label, variant in (
                (kp.ClearsFirst, "pc-negsp", "last"),
                (kp.ClearsFirst, "pc-true", "d"),
                (kp.ClearsMacro, "pc-0.0", "d"),
                (kp.ClearsMacro, "sm-index-n", "d"),
                (kp.ClearsMacro, "sm-m0-negsp", "last")):
            with self.subTest(plant=plant.NAME, label=label):
                self.assertTrue(red(self.call(
                    kit_args.refused_cell, plant, (label, variant))))
                self.assertTrue(self.call(
                    kit_args.refused_cell, kp.KitPlain,
                    (label, variant)).startswith("ok"))

    def test_every_refusal_is_green_on_the_control(self):
        cells = cells_of(kit_args.run, kp.KitPlain, quick=True)
        refused = [k for k in (key for (_n, _c, key) in cells)
                   if k.startswith("refused-")]
        self.assertEqual(len(refused),
                         3 * len(kit_args.refusals(kp.KitPlain)))
        for key in refused:
            self.assertTrue(verdict(cells, "KitPlain", "args", key)
                            .startswith("ok"), key)

    def test_a_refused_or_misplaced_value_is_red(self):
        # The contract clamps: a raise on NaN is red, and so is a NaN that
        # lands anywhere but the bottom stop. The control clamps them all.
        for plant in (kp.NanRaises, kp.NanTop):
            with self.subTest(plant=plant.NAME):
                self.assertTrue(red(kit_args.bad_cell(plant, 1)),
                                kit_args.bad_cell(plant, 1))

    def test_a_clamp_is_read_as_one(self):
        self.assertEqual(kit_args.bad_cell(kp.KitPlain, 1),
                         "ok(nan:c inf:c -inf:c -1:c 128:c 10**400:c "
                         "-10**400:c)")

    def test_a_silent_class_is_not_a_pass(self):
        self.assertEqual(kit_args.roundtrip(kp.Silent, 1, 48000, None)[0],
                         "na(silent)")

    def test_the_options_are_read_from_the_source(self):
        self.assertEqual(kit_args.options_of(kp.KitPlain),
                         [("mix", 1.0), ("gain", 1.0)])
        self.assertEqual(kit_args.options_of(kp.CtorNan),
                         [("mix", 1.0), ("gain", 1.0)])


def nogb_cells(cls):
    return cells_of(kit_nogb.run, cls, quick=True)


class TestNoGetBuffer(unittest.TestCase):

    def test_the_control_is_green(self):
        for cls in (kp.KitPlain, kp.FlushKit):
            with self.subTest(cls=cls.NAME):
                cells = nogb_cells(cls)
                self.assertTrue(cells)
                for key in (k for (_n, _c, k) in cells):
                    self.assertEqual(verdict(cells, cls.NAME, "nogb", key),
                                     "ok", key)

    def test_a_flush_that_needs_get_buffer_is_red(self):
        cells = nogb_cells(kp.FlushOnly)
        bad = [k for (_n, _c, k) in cells
               if red(verdict(cells, "FlushOnly", "nogb", k))]
        self.assertTrue(any(k.startswith("E5-mix0") for k in bad), bad)
        self.assertTrue(any(k.startswith("bytes-reset-once") for k in bad),
                        bad)

    def test_a_second_reset_in_a_row_is_red(self):
        cells = nogb_cells(kp.DoubleReset)
        bad = sorted(k for (_n, _c, k) in cells
                     if red(verdict(cells, "DoubleReset", "nogb", k)))
        self.assertTrue(bad)
        for k in bad:
            self.assertTrue(k.startswith(("bytes-reset-first-twice",
                                          "bytes-resets-apart")), k)
        self.assertEqual(verdict(cells, "DoubleReset", "nogb",
                                 "bytes-reset-once/48000/2/d"), "ok")

    def test_every_patch_is_run(self):
        cells = nogb_cells(kp.MidPatchReset)
        key = "bytes-reset-first/48000/2/p1"
        self.assertTrue(red(verdict(cells, "MidPatchReset", "nogb", key)))
        for other in ("d", "p0", "p2"):
            self.assertEqual(verdict(cells, "MidPatchReset", "nogb",
                                     "bytes-reset-first/48000/2/" + other),
                             "ok", other)
        control = nogb_cells(kp.FlushKit3)
        self.assertEqual(verdict(control, "FlushKit3", "nogb", key), "ok")

    def test_a_patch_that_raises_is_its_own_cell(self):
        cells = nogb_cells(kp.PatchPulls)
        for ch in (2, 1):
            key = "run/48000/%d/p1" % ch
            self.assertIn("raised without get_buffer: AttributeError",
                          verdict(cells, "PatchPulls", "nogb", key))
            for other in ("p0", "p2"):
                self.assertEqual(verdict(cells, "PatchPulls", "nogb",
                                         "run/48000/%d/%s" % (ch, other)),
                                 "ok", other)
        # The patches that do not raise are still judged.
        self.assertEqual(verdict(cells, "PatchPulls", "nogb",
                                 "bytes-reset-once/48000/2/p2"), "ok")
        control = nogb_cells(kp.FlushKit3)
        self.assertEqual(verdict(control, "FlushKit3", "nogb",
                                 "run/48000/2/p1"), "ok")

    def test_a_native_only_flush_is_clean_here(self):
        # NativeFlush leans on get_buffer only off CPython; TestNative
        # holds it red on MicroPython and CircuitPython.
        cells = nogb_cells(kp.NativeFlush)
        for key in (k for (_n, _c, k) in cells):
            self.assertEqual(verdict(cells, "NativeFlush", "nogb", key),
                             "ok", key)

    def test_get_buffer_is_put_back(self):
        import audiocore
        import audioeffects._component as component
        real = audiocore.get_buffer
        with kit_nogb.hidden(kp.FlushOnly):
            self.assertIsNone(getattr(component.audiocore, "get_buffer",
                                      None))
            self.assertIsNone(getattr(kp.audiocore, "get_buffer", None))
            self.assertIs(audiocore.get_buffer, real)
            self.assertIs(lifecycle.audiocore, audiocore)
        self.assertIs(component.audiocore, audiocore)
        self.assertIs(kp.audiocore, audiocore)

    def test_red_numbers_are_not_compared(self):
        self.assertEqual(kit_nogb._kind("RED(differs at +1)"),
                         kit_nogb._kind("RED(differs at +9)"))
        self.assertNotEqual(kit_nogb._kind("ok"), kit_nogb._kind("RED(x)"))


def fresh_cells(cls):
    return cells_of(kit_fresh.run, cls, quick=True)


class TestLevels(unittest.TestCase):
    """The level pass plays real material at -24, -12 and -3 dBFS."""

    def v(self, cls, level, patch=None, wire=False):
        return kit_levels.measure(cls, 48000, 2, level, patch, wire)[0]

    def test_a_class_that_does_nothing_is_red_at_every_level(self):
        for level in kc.LEVELS_DBFS:
            with self.subTest(level=level):
                self.assertTrue(red(self.v(kp.Silent, level)))
                self.assertEqual(self.v(kp.KitPlain, level), "ok")

    def test_a_wrap_that_only_the_loud_level_reaches_is_red_there(self):
        # Twice the input wraps above 16383: the phrase at -3 dBFS peaks at
        # 23197, at -12 dBFS at 8231.
        self.assertTrue(self.v(kp.WrapKit, -3).startswith("RED(wrap"))
        self.assertEqual(self.v(kp.WrapKit, -12), "ok")
        self.assertEqual(self.v(kp.WrapKit, -24), "ok")

    def test_a_level_over_the_stated_ceiling_is_not_played(self):
        cells = cells_of(kit_levels.run, kp.WrapKitQuiet, quick=True)
        got = {k[2].split("/")[0]: v["V"] for k, v in cells.items()
               if k[2].endswith("/d")}
        self.assertEqual(got, {"-24": "ok", "-12": "ok",
                               "-3": "na(above ceiling)"})

    def test_a_leak_in_a_band_of_levels_is_red_where_the_phrase_reaches_it(
            self):
        self.assertEqual(self.v(kp.LeakBand, -24, wire=True), "ok")
        for level in (-12, -3):
            with self.subTest(level=level):
                self.assertTrue(self.v(kp.LeakBand, level, wire=True)
                                .startswith("RED(wire"))
                self.assertEqual(self.v(kp.KitPlain, level, wire=True),
                                 "ok")

    def test_a_tail_past_the_bound_is_red_at_every_level(self):
        for level in kc.LEVELS_DBFS:
            with self.subTest(level=level):
                self.assertIn("rings to", self.v(kp.ShortTail, level))
        # The control, where its dry and its repeat do not sum past the rail.
        for level in (-24, -12):
            self.assertEqual(self.v(kp.EchoTail, level), "ok")

    def test_a_class_with_no_wire_has_no_wire_cells(self):
        keys = [k for k, _p, _w in kit_levels.configs(kp.ClipKit, True)]
        self.assertEqual(keys, ["d", "wire@d", "p1", "wire@p1"])
        class NoWire(kp.KitPlain):
            NAME = "NoWire"
            MACRO_LABELS = ("Level", "Gain")
        keys = [k for k, _p, _w in kit_levels.configs(NoWire, True)]
        self.assertEqual(keys, ["d", "p1"])


class TestFresh(unittest.TestCase):
    """Reset equals fresh: each plant is red on its own cells and nowhere
    the fault does not reach, and the control is green on every cell."""

    def reds(self, cls):
        cells = fresh_cells(cls)
        return sorted(k for (name, check, k), v in cells.items()
                      if red(v["V"]))

    def test_the_control_is_green(self):
        cells = fresh_cells(kp.FreshKit)
        self.assertTrue(cells)
        for key, value in cells.items():
            self.assertEqual(value["V"], "ok", key)

    def test_a_default_off_patch_0_is_never_red(self):
        # Declared defaults may sit off patch 0's grid: boot only says so.
        cells = fresh_cells(kp.OffGrid)
        self.assertEqual(self.reds(kp.OffGrid), [])
        self.assertTrue(verdict(cells, "OffGrid", "fresh",
                                "boot/48000/2").startswith("na(info"))

    def test_a_reset_that_keeps_a_line_is_red_from_its_patch_only(self):
        reds = self.reds(kp.PatchLeak)
        self.assertIn("reset@8/48000/2/p1", reds)
        self.assertIn("reset@8/48000/1/p1", reds)
        for key in reds:
            self.assertTrue(key.endswith("/p1"), key)
        # Before the first pull the line holds nothing to keep.
        self.assertNotIn("reset@0/48000/2/p1", reds)

    def test_a_fault_only_a_move_wakes_is_red_on_the_move_cells(self):
        reds = self.reds(kp.MoveLeak)
        self.assertIn("reset@8+m1=0/48000/2/d", reds)
        for key in reds:
            self.assertIn("+m", key)


class TestCeiling(unittest.TestCase):

    def v(self, cls, which="sine", patch=None, knob=None):
        knobs = [knob] if isinstance(knob, tuple) else knob
        return kit_ceiling.measure(cls, 48000, 2, which, patch, knobs)[0]

    def window(self, cls):
        feed = kc.feed(kc.square(1024, 2, 3000, 100), 48000, 2)
        e = kc.build(cls, feed.port, 48000)
        try:
            return kit_ceiling.window(e, 48000)
        finally:
            e.deinit()

    def test_a_long_tail_sets_the_window(self):
        self.assertEqual(self.window(kp.KitPlain), 2)
        self.assertEqual(self.window(kp.LongTail), 5)
        self.assertEqual(self.window(kp.EndlessTail), kit_ceiling.MAX_SECONDS)

    def test_the_window_is_what_a_cell_renders(self):
        # Same signal path, different declared tail: the render is longer,
        # so its digest differs from the two-second one's.
        short = kit_ceiling.measure(kp.KitPlain, 48000, 2, "sine", None,
                                    None)
        long = kit_ceiling.measure(kp.LongTail, 48000, 2, "sine", None, None)
        self.assertEqual(short[0], "ok")
        self.assertEqual(long[0], "ok")
        self.assertNotEqual(short[1], long[1])

    def test_a_wrap_is_red(self):
        self.assertTrue(self.v(kp.WrapKit).startswith("RED(wrap"))
        self.assertEqual(self.v(kp.KitPlain), "ok")

    def test_the_stated_level_is_the_one_rendered(self):
        self.assertEqual(kit_ceiling.peak(kp.WrapKitQuiet), 14636)
        self.assertEqual(self.v(kp.WrapKitQuiet), "ok")

    def test_a_click_is_not_a_wrap(self):
        # A full-scale click, then the repeat starting: a jump of 34817
        # with the signal falling on both sides, which a delay plays.
        click = [0, 0, 0, -32767, 2050, 1661, 77, 0]
        self.assertIsNone(kit_ceiling.wrap_at(click, [0] * 8, 1, 0))
        wrapped = [32000, 32400, 32760, -32760, -32400, -32000]
        self.assertEqual(kit_ceiling.wrap_at(wrapped, [0] * 6, 1, 0),
                         (3, 0))

    def test_a_filter_ringing_under_a_click_is_not_a_wrap(self):
        # Notch's own output, Q at its top, under a full-scale click: the
        # click falls 32767 on its return, one short of WRAP_JUMP, and the
        # filter's undershoot falls with it on the same frame.
        values = [0, 0, 32767, 0, 0, 0, 0, 0]
        out = [0, 0, 32767, -20080, -16203, -12726, -9637, -6925]
        self.assertIsNone(kit_ceiling.wrap_at(out, values, 1, 0))
        # The same output with no click under it is a wrap...
        self.assertEqual(kit_ceiling.wrap_at(out, [0] * 8, 1, 0), (3, 0))
        # ...and so is one that jumps against the input's edge.
        rising = [0, 0, -32767, 0, 0, 0, 0, 0]
        self.assertEqual(kit_ceiling.wrap_at(out, rising, 1, 0), (3, 0))

    def test_a_ring_at_nyquist_is_not_a_wrap(self):
        # A boosted filter's ring after a click, clipped at the rails: it
        # leaps into each jump and out of it, where an overflow creeps up.
        ring = [0, 32767, -32768, 32767, -32768, 32767, 0, 0]
        self.assertIsNone(kit_ceiling.wrap_at(ring, [0] * 8, 1, 0))

    def test_an_edge_a_hold_moved_is_not_a_wrap(self):
        # A full-scale square's edge at input frame 2, played at frame 3
        # by a hold that reports a latency of 3, with dither on it.
        values = [32767] * 2 + [-32767] * 6
        out = [32700, 32740, 32767, -32767, -32700, -32740, -32767, -32700]
        self.assertIsNone(kit_ceiling.wrap_at(out, values, 1, 3))
        # The same jump with no edge in the input is a wrap...
        self.assertEqual(kit_ceiling.wrap_at(out, [0] * 8, 1, 3), (3, 0))
        # ...and so is one the input's edge cannot explain: the other way.
        flipped = [-v for v in values]
        self.assertEqual(kit_ceiling.wrap_at(out, flipped, 1, 3), (3, 0))

    def test_an_edge_a_filter_and_a_hold_moved_past_the_latency(self):
        # Bitcrusher's patch 3: the band limit's rise and the hold put a
        # square's edge 12 frames late against a reported latency of 8.
        values = [-32767] * 4 + [32767] * 16
        out = [-25600] * 15 + [-26112, 29952, 29696, 29440, 29440]
        self.assertIsNone(kit_ceiling.wrap_at(out, values, 1, 8))
        # A class that reports no latency gets no such span...
        self.assertEqual(kit_ceiling.wrap_at(out, values, 1, 0), (16, 0))
        # ...and an edge the other way does not explain it.
        flipped = [-v for v in values]
        self.assertEqual(kit_ceiling.wrap_at(out, flipped, 1, 8), (16, 0))

    def test_a_held_rail_is_read_over_the_hold(self):
        # The input sits on the rail from frame 0; a hold reporting 20
        # frames of latency plays it from frame 0 too.
        values = [32767] * 40
        out = [32767] * 40
        self.assertEqual(kc.rail_run(out, values, 1, 20), (20, 0))
        self.assertEqual(kc.rail_run(out, values, 1, 20,
                                     kit_ceiling.HOLD)[0], 0)
        self.assertEqual(kc.rail_run(out, [0] * 40, 1, 20,
                                     kit_ceiling.HOLD)[0], 40)

    def test_the_surface_and_the_defaults_take_their_own_levels(self):
        class Both:
            INPUT_CEILING_DBFS = -1.0
            SURFACE_CEILING_DBFS = -6.0

        class Cabinet:
            SURFACE_CEILING_DBFS = -14.0
            DEFAULT_CEILING_DBFS = -6.0

        level = kit_ceiling.stated_dbfs
        self.assertEqual(level(Both), -1.0)
        self.assertEqual(level(Both, 3), -1.0)
        self.assertEqual(level(Both, None, [(0, 127)]), -6.0)
        self.assertEqual(level(Both, 3, [(0, 127)]), -6.0)
        self.assertEqual(level(Cabinet), -6.0)
        self.assertEqual(level(Cabinet, 3), -14.0)
        self.assertEqual(level(Cabinet, None, [(0, 0)]), -14.0)
        self.assertEqual(level(kp.WrapKitQuiet, None, [(0, 0)]), -7)
        self.assertEqual(level(kp.KitPlain, 0, [(0, 0)]), 0)

    def test_an_output_level_at_zero_may_be_silent(self):
        class Labelled:
            MACRO_LABELS = ("Drive", "Level", "Volume", "Gain", "Mix")
        down = kit_ceiling.turned_down
        self.assertTrue(down(Labelled, [(1, 0)]))
        self.assertTrue(down(Labelled, [(4, 127), (2, 0)]))
        self.assertFalse(down(Labelled, [(1, 64)]))
        self.assertFalse(down(Labelled, [(3, 0)]))
        self.assertFalse(down(Labelled, [(4, 0)]))
        self.assertFalse(down(Labelled, None))

    def test_a_rail_is_red(self):
        self.assertTrue(self.v(kp.ClipKit).startswith("RED(rail"))
        # A square at full scale sits on the rail because the input does.
        self.assertEqual(self.v(kp.KitPlain, "square"), "ok")

    def test_a_rail_by_design_is_excused_where_declared(self):
        self.assertTrue(self.v(kp.ClipAtTop).startswith("RED(rail"))
        self.assertTrue(self.v(kp.ClipAtTop, knob=(0, 127)).startswith(
            "RED(rail"))
        self.assertEqual(self.v(kp.ClipAtTop, knob=(1, 127)), "ok")
        self.assertEqual(self.v(kp.ClipAtTop, knob=[(0, 127), (1, 127)]),
                         "ok")
        self.assertEqual(self.v(kp.ClipsAlways), "ok")
        # A wrap is still judged.
        self.assertTrue(self.v(kp.WrapsAlways).startswith("RED(wrap"))

    def test_a_stated_level_holds_and_the_level_above_does_not(self):
        self.assertEqual(
            kit_ceiling.stated_level_reds(kp.WrapKitQuiet, "sine"), [])
        reds = kit_ceiling.stated_level_reds(kp.WrapKitQuiet, "sine", db=0)
        self.assertEqual(len(reds), 3)          # the defaults, two patches
        self.assertIn("RED(wrap", reds[0])
        self.assertEqual(len(kit_ceiling.stated_level_reds(
            kp.WrapKitQuiet, "sine", db=0, keys=("p1",))), 1)

    def test_silence_at_a_stop_is_red(self):
        self.assertTrue(self.v(kp.DeadStop, knob=(1, 0)).startswith(
            "RED(silent"))
        self.assertEqual(self.v(kp.KitPlain, knob=(1, 0)), "ok")
        self.assertEqual(self.v(kp.DeadStop), "ok")

    def test_a_silent_class_is_red(self):
        self.assertTrue(self.v(kp.Silent).startswith("RED(silent"))

    def sine_cells(self, cls):
        lines = []
        kit_ceiling.run(cls, emit=lines.append, quick=True,
                        materials=("sine",))
        return dict((k[2], v["V"]) for k, v in kc.parse(lines).items())

    def test_every_macro_is_driven_at_64(self):
        got = self.sine_cells(kp.MidWrap)
        self.assertTrue(got["sine/48000/2/m1=64"].startswith("RED(wrap"))
        self.assertEqual([k for k in got if red(got[k])],
                         ["sine/48000/2/m1=64"])
        self.assertEqual(self.sine_cells(kp.CondKit)["sine/48000/2/m1=64"],
                         "ok")

    def test_a_volume_knob_is_level_like(self):
        class Labelled:
            MACRO_LABELS = ("Tone", "Volume", "Output Volume", "Drive")
        self.assertEqual(kit_ceiling.level_like(Labelled), [1, 2])

    def test_the_combined_settings_are_driven(self):
        self.assertEqual(kit_ceiling.level_like(kp.CondKit), [0, 1])
        combo = self.sine_cells(kp.ComboWrap)
        # The combination is bad at every patch: the defaults' cell and
        # each patch's.
        self.assertEqual(sorted(k for k in combo if red(combo[k])),
                         ["sine/48000/2/lv=127+m2=0",
                          "sine/48000/2/p0+lv=127+m2=0",
                          "sine/48000/2/p1+lv=127+m2=0"])
        every = self.sine_cells(kp.AllWrap)
        self.assertEqual(sorted(k for k in every if red(every[k])),
                         ["sine/48000/2/all=127",
                          "sine/48000/2/lv=127+m2=127",
                          "sine/48000/2/p0+lv=127+m2=127",
                          "sine/48000/2/p1+lv=127+m2=127"])
        control = self.sine_cells(kp.CondKit)
        self.assertEqual([k for k in control if red(control[k])], [])
        self.assertIn("sine/48000/2/lv=127+m2=0", control)

    def test_the_combined_settings_are_driven_on_every_patch(self):
        lines = []
        kit_ceiling.run(kp.PatchComboRail, emit=lines.append, quick=True,
                        materials=("sine", "noise"))
        got = dict((k[2], v["V"]) for k, v in kc.parse(lines).items())
        reds = [k for k in got if red(got[k])]
        self.assertEqual(reds, ["sine/48000/2/p1+lv=127+m2=0"])
        self.assertTrue(got[reds[0]].startswith("RED(rail"), got[reds[0]])
        self.assertIn("sine/48000/2/p0+lv=127+m2=0", got)
        # The default patch's combination is fine; so is every other
        # material's, which runs the defaults' combinations only.
        self.assertEqual(got["sine/48000/2/lv=127+m2=0"], "ok")
        self.assertNotIn("noise/48000/2/p1+lv=127+m2=0", got)

    def test_the_low_notes_are_played(self):
        for which in ("sq41", "sq55"):
            self.assertTrue(self.v(kp.LowWrap, which).startswith(
                "RED(wrap"), which)
            self.assertEqual(self.v(kp.KitPlain, which), "ok", which)
        for which in ("square", "sine", "clicks", "dc"):
            self.assertEqual(self.v(kp.LowWrap, which), "ok", which)


FIXTURE_TESTS = '''
import unittest

CLAIMS = %s


class Things(unittest.TestCase):
    def test_passes(self):
        pass

    def test_fails(self):
        self.fail("planted")

    @unittest.skip("planted")
    def test_skipped(self):
        pass
'''


class TestClaims(unittest.TestCase):

    DOC = ("A plain wire. **Controls.** Gain sets the level. The output is "
           "the input at Gain 1.")


    def test_a_short_test_file_name_is_found(self):
        class Gate:
            NAME = "NoiseGate"

        class Nobody:
            NAME = "NoSuchEffect"

        _, path = kit_claims.module_for(Gate)
        self.assertEqual(os.path.basename(path), "test_noisegate.py")
        _, path = kit_claims.module_for(Gate, "test_cpython_effects_x")
        self.assertIsNone(path)
        self.assertEqual(kit_claims.module_for(Nobody), (None, None))
    def run_claims(self, claims, doc=None):
        with tempfile.TemporaryDirectory() as scratch:
            name = "kitfixture_%d" % abs(hash((repr(claims), doc)))
            path = os.path.join(scratch, name + ".py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(textwrap.dedent(FIXTURE_TESTS % repr(claims)))
            sys.path.insert(0, scratch)
            try:
                module = __import__(name)
                lines = []
                kit_claims.check("Fixture", self.DOC if doc is None else doc,
                                 module, path, lines.append)
            finally:
                sys.path.remove(scratch)
                sys.modules.pop(name, None)
        cells = kc.parse(lines)
        return dict((k[2], v["V"]) for k, v in cells.items())

    def test_the_control_is_green(self):
        got = self.run_claims((("The output is the input at Gain 1.",
                                "test_passes"),))
        self.assertEqual(got, {"table": "ok", "row0": "ok"})

    def test_each_fault_is_red(self):
        cases = (
            ("not in the docstring", (("The output is twice the input.",
                                       "test_passes"),)),
            ("no test test_absent", (("The output is the input at Gain 1.",
                                      "test_absent"),)),
            ("Things.test_fails fails", ((
                "The output is the input at Gain 1.", "test_fails"),)),
            ("Things.test_skipped skipped", ((
                "The output is the input at Gain 1.",
                ("test_passes", "Things.test_skipped")),)),
            ("no lifecycle row", (("The output is the input at Gain 1.",
                                   "DECLARED:Fixture,E1-,P4"),)),
        )
        for why, claims in cases:
            with self.subTest(why=why):
                got = self.run_claims(claims)
                self.assertIn(why, got["row0"])

    def test_a_declared_row_counts(self):
        key = next(iter(lifecycle.DECLARED))
        got = self.run_claims((("The output is the input at Gain 1.",
                                "DECLARED:%s,%s,%s" % key),))
        self.assertEqual(got["row0"], "ok")

    def test_a_scoped_row_is_named_with_its_scope(self):
        rows = {("Fixture", "E10-reset", "P4", "circuitpython"): "planted",
                ("Fixture", "E5-", "P1", (1, None)): "planted"}
        lifecycle.DECLARED.update(rows)
        try:
            claim = "The output is the input at Gain 1."
            for target, want in (
                    ("DECLARED:Fixture,E10-reset,P4,circuitpython", "ok"),
                    ("DECLARED:Fixture,E5-,P1,patches=d/1", "ok"),
                    ("DECLARED:Fixture,E10-reset,P4", "RED"),
                    ("DECLARED:Fixture,E10-reset,P4,micropython", "RED"),
                    ("DECLARED:Fixture,E5-,P1,patches=1", "RED")):
                with self.subTest(target=target):
                    got = self.run_claims(((claim, target),))["row0"]
                    self.assertTrue(got.startswith(want), got)
        finally:
            for row in rows:
                del lifecycle.DECLARED[row]

    def test_a_claim_with_no_row_is_red(self):
        got = self.run_claims((), self.DOC + " It never clips.")
        self.assertEqual(sorted(got), ["loose0", "loose1", "table"])
        self.assertIn("at Gain 1", got["loose0"])
        self.assertIn("never clips", got["loose1"])

    def test_no_table_and_no_docstring(self):
        lines = []
        kit_claims.check("Fixture", self.DOC, None, None, lines.append)
        self.assertTrue(lines[0].endswith("V:RED(no CLAIMS table in the "
                                          "test module)"))
        lines = []
        kit_claims.check("Fixture", None, None, None, lines.append)
        self.assertTrue(lines[0].endswith("V:RED(no docstring)"))

    def test_the_claim_rule(self):
        for sentence in ("Time runs to 800 ms.", "It never clips.",
                         "Mix is at most unity.", "Two heads play."):
            self.assertTrue(kit_claims.is_claim(sentence), sentence)
        for sentence in ("Gain sets the level.", "The repeats get darker."):
            self.assertFalse(kit_claims.is_claim(sentence), sentence)


class TestPaperwork(unittest.TestCase):

    CHANGELOG = "## Unreleased\n\n- **`KitPlain` (rebuilt):** a wire.\n"

    def cells(self, text, pin, changelog=None):
        lines = []
        kit_paperwork.check("KitPlain", text, changelog or self.CHANGELOG,
                            pin, lines.append)
        return dict((k[2], v["V"]) for k, v in kc.parse(lines).items())

    def test_the_changelog_line(self):
        pin = kit_paperwork.Pin(None, None)
        self.assertEqual(self.cells("", pin)["changelog"], "ok")
        self.assertTrue(red(self.cells("", pin, "- **`Other`**")
                            ["changelog"]))

    def test_citations_against_the_pin(self):
        pin = kit_paperwork.Pin(kit_paperwork.find_checkout(),
                                kit_paperwork.pin_commit())
        if pin.files is None:
            self.skipTest("audiodsp at the pin: %s" % pin.why)
        got = self.cells("see `audiodsp_feedback_delay.c:157`, `:99999` "
                         "and nosuchfile.c:3", pin)
        self.assertEqual(got["cite:audiodsp_feedback_delay.c:157"], "ok")
        self.assertTrue(red(got["cite:audiodsp_feedback_delay.c:99999"]))
        self.assertTrue(red(got["cite:nosuchfile.c:3"]))

    def test_a_citation_may_name_the_audiodsp_directory(self):
        pin = kit_paperwork.Pin(None, None)
        pin.files = ["src/shared/audiodsp_filter_f32.c"]
        pin._lines = {"src/shared/audiodsp_filter_f32.c": 300}
        got = self.cells("(`audiodsp/src/shared/audiodsp_filter_f32.c:216-241`"
                         ", `audiodsp/src/shared/audiodsp_filter_f32.c:999`,"
                         " `audiodsp/src/shared/nosuch.c:3`)", pin)
        self.assertEqual(
            got["cite:audiodsp/src/shared/audiodsp_filter_f32.c:216-241"],
            "ok")
        self.assertTrue(red(
            got["cite:audiodsp/src/shared/audiodsp_filter_f32.c:999"]))
        self.assertTrue(red(got["cite:audiodsp/src/shared/nosuch.c:3"]))

    def test_citations_to_this_repository(self):
        pin = kit_paperwork.Pin(None, None)
        got = self.cells("(`_component.py:10`, `_component.py:999999`, "
                         "`audiodsp_tank.c:1`)", pin)
        self.assertEqual(got["cite:_component.py:10"], "ok")
        self.assertTrue(red(got["cite:_component.py:999999"]))
        self.assertEqual(got["cite:audiodsp_tank.c:1"],
                         "na(no audiodsp checkout)")

    CARD = """# Class card: `CondKit`

## 3. The surface

| # | Label | Mode | Span | Notes |
|---|---|---|---|---|
| 0 | `Mix` | UNIPOLAR | 0 … 1 | |
| 1 | `%s` | UNIPOLAR, log | 0.25 … 1 | a \\| in a cell |
| 2 | `Tone` | %s | 0 … 1 | |

| Patch | Name | Mix |
|---|---|---|
| 0 | Default | 1 |

## 4. Traits
"""

    def surface(self, card):
        pin = kit_paperwork.Pin(None, None)
        with tempfile.TemporaryDirectory() as cards:
            if card is not None:
                with open(os.path.join(cards, "CondKit.md"), "w",
                          encoding="utf-8") as f:
                    f.write(card)
            lines = []
            kit_paperwork.check("CondKit", "", "", pin, lines.append,
                                cls=kp.CondKit, cards=cards)
        return dict((k[2], v["V"]) for k, v in kc.parse(lines).items()
                    if k[2].startswith("surface"))

    def test_the_surface_against_the_card(self):
        self.assertEqual(self.surface(self.CARD % ("Level", "UNIPOLAR")),
                         {"surface-m0": "ok", "surface-m1": "ok",
                          "surface-m2": "ok"})
        got = self.surface(self.CARD % ("Volume", "BIPOLAR"))
        self.assertEqual(got["surface-m0"], "ok")
        self.assertEqual(got["surface-m1"],
                         "RED(class 'Level' UNIPOLAR, card 'Volume' "
                         "UNIPOLAR)")
        self.assertEqual(got["surface-m2"],
                         "RED(class 'Tone' UNIPOLAR, card 'Tone' BIPOLAR)")
        short = "\n".join(l for l in (self.CARD % ("Level", "UNIPOLAR"))
                          .splitlines() if not l.startswith("| 2 "))
        self.assertTrue(red(self.surface(short)["surface-m2"]))
        self.assertEqual(self.surface(None),
                         {"surface": "na(no card for CondKit)"})
        self.assertEqual(self.surface("# Card\n\n## 3. Traits\n\n"
                                      "| # | Trait |\n|---|---|\n"),
                         {"surface": "na(no surface table in section 3)"})

    def test_a_range_row_names_one_macro_per_index(self):
        rows = kit_paperwork.card_surface(
            "## 3. The surface\n\n| # | Label | Mode |\n|---|---|---|\n"
            "| 0 | `Pitch` | BIPOLAR |\n"
            "| 1\u20133 | `Voice 1` \u2026 `Voice 3` | BIPOLAR |\n"
            "| 4-5 | `Level 1` ... `Level 2` | UNIPOLAR |\n")
        self.assertEqual(rows, [(0, "Pitch", "BIPOLAR"),
                                (1, "Voice 1", "BIPOLAR"),
                                (2, "Voice 2", "BIPOLAR"),
                                (3, "Voice 3", "BIPOLAR"),
                                (4, "Level 1", "UNIPOLAR"),
                                (5, "Level 2", "UNIPOLAR")])

    def test_the_citation_forms(self):
        found = kit_paperwork.citations(
            "`src/shared/a.c:344`, called at :529 (`b.h:3-5`, `:7`); "
            "a ratio 3:2 and x[:10] are not citations")
        self.assertEqual(found, [("src/shared/a.c", 344, 344),
                                 ("src/shared/a.c", 529, 529),
                                 ("b.h", 3, 5), ("b.h", 7, 7)])


# --------------------------------------------------------------------------
# The native half


def native_binaries():
    """{"micropython": path or None, "circuitpython": path or None}: the
    LIFECYCLE_MICROPYTHON / LIFECYCLE_CIRCUITPYTHON binaries, or the
    workspace's `bin/`."""
    found = {}
    here = ROOT
    bindir = None
    for _up in range(5):
        here = os.path.dirname(here)
        if os.path.isfile(os.path.join(here, "bin", "micropython")):
            bindir = os.path.join(here, "bin")
            break
    for family in ("micropython", "circuitpython"):
        path = os.environ.get("LIFECYCLE_" + family.upper())
        if path is None and bindir is not None:
            path = os.path.join(bindir, family)
        found[family] = path if path and os.path.isfile(path) else None
    return found


def run_kit(binary, args):
    with tempfile.TemporaryDirectory() as scratch:
        env = dict(os.environ, MICROPYPATH="lib:tests/support",
                   GCOV_PREFIX=scratch, PYTHONDONTWRITEBYTECODE="1",
                   OMP_NUM_THREADS="1")
        cmd = [binary]
        if binary != sys.executable:
            cmd += ["-X", "heapsize=256M"]
        done = subprocess.run(cmd + ["tests/support/kit.py"] + args,
                              capture_output=True, text=True, cwd=ROOT,
                              env=env)
    lines = done.stdout.splitlines()
    if done.returncode != 0 or not lines or lines[-1] != "DONE":
        raise AssertionError("%s: %s%s" % (binary, done.stdout[-1500:],
                                           done.stderr[-1500:]))
    return lines


RENDER = ["--quick", "--plants-module=kit_planted",
          "--only=args,plants,ceiling,tail,fresh,levels"]


class TestNative(unittest.TestCase):
    """The render checks print the same lines on all three interpreters,
    and that agreement can fail."""

    def binary(self, family):
        path = native_binaries()[family]
        if path is None:
            self.skipTest("no %s binary: set LIFECYCLE_%s" % (
                family, family.upper()))
        return path

    def agree(self, family):
        theirs = run_kit(self.binary(family), ["KitPlain", "EventTail"]
                         + RENDER)
        ours = run_kit(sys.executable, ["KitPlain", "EventTail"] + RENDER)
        self.assertEqual(ours, theirs)

    def test_micropython_agrees(self):
        self.agree("micropython")

    def test_circuitpython_agrees(self):
        self.agree("circuitpython")

    def nogb_native(self, family):
        binary = self.binary(family)
        args = ["NativeFlush", "FlushKit", "--only=nogb", "--quick"]
        cells = kc.parse(run_kit(binary, args))
        bad = sorted(k for (n, _c, k), v in cells.items()
                     if n == "NativeFlush" and red(v["V"]))
        self.assertTrue(any(k.startswith("bytes-reset-once") for k in bad),
                        bad)
        self.assertTrue(any(k.startswith("E5-mix0") for k in bad), bad)
        for (n, _c, k), v in cells.items():
            if n == "FlushKit":
                self.assertEqual(v["V"], "ok", k)

    def test_nogb_runs_on_micropython(self):
        self.nogb_native("micropython")

    def test_nogb_runs_on_circuitpython(self):
        self.nogb_native("circuitpython")

    def test_agreement_can_fail(self):
        binary = self.binary("micropython")
        args = ["ImplKit", "--only=args", "--quick"]
        ours = kc.parse(run_kit(sys.executable, args))
        theirs = kc.parse(run_kit(binary, args))
        self.assertNotEqual(ours, theirs)
        # Every verdict is the same; the bytes are not.
        self.assertEqual(dict((k, v["V"]) for k, v in ours.items()),
                         dict((k, v["V"]) for k, v in theirs.items()))


if __name__ == "__main__":
    unittest.main()
