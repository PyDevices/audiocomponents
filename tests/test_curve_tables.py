"""Every int16 curve table in the library, held to three bars.

A `Waveshaper` curve is a lookup table, and a lookup table can be wrong in
ways nothing else in the suite reads. Phase 4's fix round found two of them
in one week: `Saturation`'s tube curve had **337 adjacent steps over 2000
counts** and was not even monotone, and `Overdrive`'s filled **35 %** of
int16, throwing away a bit and a half of resolution before the signal
reached it. Both render. Both sound like the effect. Neither shows up in a
trait test, because a trait test asks what the class does at a handful of
levels and a table is wrong between them.

So this file reads the tables themselves, and asks three things of each:

**Monotone.** A shaper curve maps input to output; a curve that turns back
on itself sends two inputs to the same output and a rising input to a
falling one. That is not a transfer characteristic, it is a fold.

**No adjacent step above 2000 counts.** Neighbouring entries are one LSB of
input apart. A jump between them is a discontinuity the interpolator cannot
smooth, and it is audible as a buzz riding the signal. 2000 counts is about
6 % of full scale.

**Fills at least 95 % of int16 on its larger side.** A table normalised to
something short of full scale costs resolution for nothing: the class scales
it back up afterwards, so the only thing the headroom buys is quantisation
noise. Measured on the larger side because an asymmetric curve - a tube
stage, a one-sided diode - is *meant* to be shorter on one side.

**Absence must not read as agreement.** A gate that finds nothing passes, so
this file asserts its own catch: every drive module that carries a table
must be seen to carry one, `cabinetsim` must be seen to carry none, and the
two discovery routes must agree with each other. The bars themselves are
shown red on a planted jumpy table and a planted 60 % table at the bottom of
the file.

**Two discovery routes, on purpose.** One imports each module and reads its
module-level values; the other parses the `# BEGIN <NAME>_CURVE` marker
blocks out of the source and executes them alone. A table moved inside a
function would vanish from the first and stay in the second; a table that
stops being generated into its marker block would vanish from the second and
stay in the first. They are cross-checked, so losing one is a failure and
not a quieter pass.
"""

import os
import re
import sys
import unittest
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

#: Shortest run of points this file calls a curve table. Below it a
#: sequence of int16 is as likely to be a coefficient set, a note map or a
#: window as a transfer curve, and the bars would not mean the same thing.
MIN_POINTS = 256

#: The largest step allowed between neighbouring entries, in int16 counts.
STEP_BAR = 2000

#: How much of int16 the larger side must reach.
FILL_BAR = 0.95

LIB = os.path.join(os.path.dirname(__file__), "..", "lib", "audioeffects")

#: `# BEGIN NAME_CURVE`, with or without the surrounding dashes - both
#: spellings are in the tree, and a generator that changes its mind about
#: the dashes must not silently drop a table out of this gate.
_MARKER = re.compile(r"^#\s*(?:-+\s*)?(BEGIN|END)\s+([A-Z0-9_]+_CURVE)"
                     r"\s*(?:-+\s*)?$")

#: The modules that must be seen to carry at least one table. This is the
#: list that makes an empty scan a failure rather than a pass. `phaser` is
#: not a drive class, but its Drive stage is a `Waveshaper` over a curve and
#: that curve is held to the same three bars - it was the last one in the
#: library using two thirds of the range (audiocomponents#77).
MUST_CARRY = ("bitcrusher", "distortion", "exciter", "fuzz", "overdrive",
              "phaser", "saturation")

#: And the one Phase 4 class that carries none, declared rather than
#: assumed: `CabinetSim`'s characters are a cascade of biquad sections, not
#: a shaper curve. If it ever grows a table, this gate says so.
MUST_NOT_CARRY = ("cabinetsim",)


def as_int16(value):
    """The points of `value` if it is an int16 table, else None.

    `bytes`, `bytearray` and `array('h')` all appear in the tree: a
    generated table is usually hex or a byte literal, a hand-built one is
    usually an `array`.
    """
    if isinstance(value, array) and value.typecode == "h":
        return list(value)
    if isinstance(value, (bytes, bytearray)) and len(value) >= 2 \
            and len(value) % 2 == 0:
        points = array("h")
        points.frombytes(bytes(value))
        return list(points)
    return None


def measure(points):
    """The three bars, as numbers, for one table."""
    steps = [points[i + 1] - points[i] for i in range(len(points) - 1)]
    rising = all(step >= 0 for step in steps)
    falling = all(step <= 0 for step in steps)
    over = [i for i, step in enumerate(steps) if abs(step) > STEP_BAR]
    return {
        "points": len(points),
        "monotone": rising or falling,
        "max_step": max((abs(step) for step in steps), default=0),
        "steps_over_bar": len(over),
        "first_step_over": over[0] if over else None,
        # The larger side, each against its own end of the range: int16 is
        # not symmetric and -32768 is a legal value.
        "fill": max(max(points) / 32767.0, -min(points) / 32768.0),
    }


def verdict(name, reading):
    """The red lines for one table, empty if it meets every bar."""
    red = []
    if not reading["monotone"]:
        red.append("%s is not monotone" % name)
    if reading["steps_over_bar"]:
        red.append("%s has %d adjacent steps over %d counts (worst %d, first"
                   " at index %d)"
                   % (name, reading["steps_over_bar"], STEP_BAR,
                      reading["max_step"], reading["first_step_over"]))
    if reading["fill"] < FILL_BAR:
        red.append("%s fills %.1f %% of int16 on its larger side, under the"
                   " %.0f %% bar" % (name, 100.0 * reading["fill"],
                                     100.0 * FILL_BAR))
    return red


def modules():
    """Every module under `lib/audioeffects/` and its `rebuilt/`."""
    out = []
    for folder, prefix in ((LIB, "audioeffects."),
                           (os.path.join(LIB, "rebuilt"),
                            "audioeffects.rebuilt.")):
        for entry in sorted(os.listdir(folder)):
            if entry.endswith(".py") and not entry.startswith("__"):
                out.append((prefix + entry[:-3],
                            os.path.join(folder, entry)))
    return out


def tables_by_value():
    """Route one: import each module, read its module-level values."""
    import importlib
    found = {}
    for name, _path in modules():
        try:
            module = importlib.import_module(name)
        except Exception:
            # A module that will not import is another test's failure, not
            # this one's. It is reported by the coverage test below if it
            # was one that had to carry a table.
            continue
        for attribute in dir(module):
            if attribute.startswith("__"):
                continue
            points = as_int16(getattr(module, attribute, None))
            if points is not None and len(points) >= MIN_POINTS:
                found["%s.%s" % (name, attribute)] = points
    return found


def blocks_in(text):
    """The `# BEGIN <NAME>_CURVE` ... `# END <NAME>_CURVE` blocks of a file.

    Returns (name, source) pairs. An unterminated BEGIN is returned with
    whatever followed it, so a truncated generator run shows up as a table
    that will not execute rather than as no table at all.
    """
    out = []
    open_name, body = None, []
    for line in text.splitlines():
        match = _MARKER.match(line.strip())
        if match and match.group(1) == "BEGIN":
            open_name, body = match.group(2), []
            continue
        if match and match.group(1) == "END" and open_name:
            out.append((open_name, "\n".join(body)))
            open_name, body = None, []
            continue
        if open_name is not None:
            body.append(line)
    if open_name is not None:
        out.append((open_name, "\n".join(body)))
    return out


def tables_by_marker():
    """Route two: execute each marker block on its own and read what it binds.

    The block is run in a namespace holding only `array` and the builtins,
    which is all a generated table needs. A block that needs more than that
    is not a table any more, and it raises here.
    """
    found = {}
    for name, path in modules():
        with open(path) as handle:
            text = handle.read()
        for block_name, source in blocks_in(text):
            namespace = {"array": array}
            exec(compile(source, "%s:%s" % (path, block_name), "exec"),
                 namespace)
            for key, value in namespace.items():
                if key in ("array", "__builtins__"):
                    continue
                points = as_int16(value)
                if points is not None and len(points) >= MIN_POINTS:
                    found["%s[%s].%s" % (name, block_name, key)] = points
    return found


class TheTables(unittest.TestCase):

    def setUp(self):
        self.by_value = tables_by_value()
        self.by_marker = tables_by_marker()

    def test_every_table_meets_the_three_bars(self):
        """One subTest a table, so a red names the table and its numbers."""
        both = dict(self.by_value)
        both.update(self.by_marker)
        self.assertTrue(both, "no curve table found anywhere - the scan is"
                              " broken, not the library")
        for name in sorted(both):
            with self.subTest(table=name):
                reading = measure(both[name])
                red = verdict(name, reading)
                self.assertEqual(red, [], "%s: %s" % (name, "; ".join(red)))

    def test_the_scan_found_the_drive_tables(self):
        """Absence must not read as agreement.

        Every drive module that carries a curve has to be seen carrying one.
        Without this, deleting a table - or breaking the import that reaches
        it - turns this whole file green.
        """
        seen = set()
        for name in list(self.by_value) + list(self.by_marker):
            for module in MUST_CARRY:
                if (".%s." % module) in name or ("%s[" % module) in name:
                    seen.add(module)
        self.assertEqual(sorted(seen), sorted(MUST_CARRY),
                         "no curve table found for: %s"
                         % ", ".join(sorted(set(MUST_CARRY) - seen)))

    def test_cabinetsim_carries_no_table_and_that_is_declared(self):
        """The seventh drive class, and the reason it is not in the list.

        `CabinetSim` builds its characters out of biquad sections, so it has
        no shaper curve to hold to these bars. Declared here so its absence
        is a statement and not an oversight - and so a table appearing in it
        later has to be looked at rather than ignored.
        """
        for name in list(self.by_value) + list(self.by_marker):
            for module in MUST_NOT_CARRY:
                self.assertNotIn(".%s." % module, name,
                                 "%s has grown a curve table" % module)

    def test_the_two_routes_agree(self):
        """A marker block's table must also be a module-level value.

        Both routes exist so that losing one is loud. A table generated into
        a marker block but no longer bound at module level is dead code; a
        table bound at module level in a drive module but no longer inside a
        marker block is one the generator has stopped maintaining.
        """
        value_points = {tuple(points) for points in self.by_value.values()}
        for name, points in sorted(self.by_marker.items()):
            with self.subTest(table=name):
                self.assertIn(tuple(points), value_points,
                              "%s is in a marker block but is not a"
                              " module-level value" % name)


class PlantedFaults(unittest.TestCase):
    """The bars shown red, through the same code the real tables go through.

    Each fault is written as a marker block and put through
    `blocks_in`/`exec`/`measure`/`verdict` - the whole route, not the
    arithmetic alone - so a discovery step that quietly stopped finding
    tables would fail here too.
    """

    def _through_the_route(self, source):
        blocks = blocks_in(source)
        self.assertEqual(len(blocks), 1, "the planted block was not found")
        name, body = blocks[0]
        namespace = {"array": array}
        exec(compile(body, "<planted>", "exec"), namespace)
        points = as_int16(namespace["PLANTED"])
        self.assertIsNotNone(points)
        self.assertGreaterEqual(len(points), MIN_POINTS)
        return measure(points), verdict(name, measure(points))

    def test_a_clean_table_is_green(self):
        """The control. Without it the two faults below prove nothing: a
        route that rejects everything would pass them both."""
        source = (
            "# --- BEGIN PLANTED_CURVE ---\n"
            "PLANTED = array('h', [\n"
            "    max(-32768, min(32767, int(round(\n"
            "        (-1.0 + 2.0 * i / 1023.0) * 32767.0))))\n"
            "    for i in range(1024)])\n"
            "# --- END PLANTED_CURVE ---\n")
        reading, red = self._through_the_route(source)
        self.assertEqual(red, [], red)
        self.assertTrue(reading["monotone"])
        self.assertGreaterEqual(reading["fill"], FILL_BAR)

    def test_a_jumpy_table_is_red(self):
        """Saturation's tube curve in miniature.

        The tail is lifted 6000 counts, so the curve is still monotone, still
        full scale, still smooth everywhere but one place - and that one
        neighbouring pair is the discontinuity. The other two bars are
        asserted green here on purpose: this fault has to be caught by the
        step bar and by nothing else, or it does not show that bar works.
        """
        source = (
            "# --- BEGIN PLANTED_CURVE ---\n"
            "_p = [max(-32768, min(32767, int(round(\n"
            "         (-1.0 + 2.0 * i / 1023.0) * 32767.0))))\n"
            "      for i in range(1024)]\n"
            "_p[512:] = [min(32767, v + 6000) for v in _p[512:]]\n"
            "PLANTED = array('h', _p)\n"
            "# --- END PLANTED_CURVE ---\n")
        reading, red = self._through_the_route(source)
        self.assertTrue(reading["monotone"])
        self.assertGreaterEqual(reading["fill"], FILL_BAR)
        self.assertEqual(reading["steps_over_bar"], 1)
        self.assertGreater(reading["max_step"], STEP_BAR)
        self.assertEqual(len(red), 1, red)
        self.assertIn("adjacent steps over", red[0])

    def test_a_sixty_percent_table_is_red(self):
        """Overdrive's curve before the fix round, in miniature: clean,
        monotone, smooth - and normalised to 60 % of full scale."""
        source = (
            "# --- BEGIN PLANTED_CURVE ---\n"
            "PLANTED = array('h', [\n"
            "    max(-32768, min(32767, int(round(\n"
            "        (-1.0 + 2.0 * i / 1023.0) * 0.60 * 32767.0))))\n"
            "    for i in range(1024)])\n"
            "# --- END PLANTED_CURVE ---\n")
        reading, red = self._through_the_route(source)
        self.assertTrue(reading["monotone"])
        self.assertEqual(reading["steps_over_bar"], 0)
        self.assertLess(reading["fill"], FILL_BAR)
        self.assertTrue(any("of int16 on its larger side" in line
                            for line in red), red)

    def test_a_folded_table_is_red(self):
        """The monotone bar's own fault: a curve that turns back."""
        source = (
            "# --- BEGIN PLANTED_CURVE ---\n"
            "_p = [max(-32768, min(32767, int(round(\n"
            "         (-1.0 + 2.0 * i / 1023.0) * 32767.0))))\n"
            "      for i in range(1024)]\n"
            "_p[700:800] = _p[700:800][::-1]\n"
            "PLANTED = array('h', _p)\n"
            "# --- END PLANTED_CURVE ---\n")
        reading, red = self._through_the_route(source)
        self.assertFalse(reading["monotone"])
        self.assertTrue(any("not monotone" in line for line in red), red)


if __name__ == "__main__":
    unittest.main()
