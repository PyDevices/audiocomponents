"""Every effect's knobs, their spans and its patches, built from the classes.

`docs/reference/effect-controls.md` publishes these tables so someone can
see what each knob covers before they build anything. Spans typed by hand
into a docstring go stale, so they are rendered here from the classes' own
`MACRO_LABELS`, `MACRO_MODES`, `_MACRO_RANGES`, `_MACRO_UNITS` and
`PATCHES`, and `test_metadata_contract.py` holds the page to it.

    python tests/support/controls_table.py > docs/reference/effect-controls.md
"""

import inspect
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                    "lib"))

import audioeffects                                             # noqa: E402
from audioeffects import _component                             # noqa: E402

HEADER = """# Effect controls

Every effect's knobs, what each one spans, and the patches it ships with.
The tables are rendered from the classes themselves, so they are always
the code's own answer. A knob turns on the 0 to 127 MIDI scale; "log" means
equal turns cover equal ratios, so the fine grain sits at the low end.
What each knob does is in the effect's own docstring.
"""


def classes():
    """The effects with knobs, by class name."""
    out = []
    for name in sorted(dir(audioeffects)):
        cls = getattr(audioeffects, name)
        if (inspect.isclass(cls) and issubclass(cls, _component.Component)
                and getattr(cls, "_MACRO_RANGES", None)):
            out.append(cls)
    return out


def number(value, unit):
    """`value` in `unit`, with kHz for a thousand hertz and over."""
    if unit == "Hz" and abs(value) >= 1000.0:
        value, unit = value / 1000.0, "kHz"
    text = "%g" % value
    if value > 0 and unit == "dB":
        text = "+" + text
    return text + (" " + unit if unit else "")


def span(cls, index):
    """What macro `index` covers, in words."""
    if cls.MACRO_MODES.get(index) == "TOGGLE":
        return "off or on"
    rng = cls._MACRO_RANGES[index]
    unit = getattr(cls, "_MACRO_UNITS", {}).get(index, "")
    text = "%s to %s" % (number(rng[0], unit), number(rng[1], unit))
    if len(rng) > 2 and rng[2] == "log":
        text += ", log"
    return text


def render_class(cls):
    lines = ["## %s" % getattr(cls, "DISPLAY_NAME", cls.NAME), "",
             "`%s`" % cls.NAME, "",
             "| Knob | Spans |", "|---|---|"]
    for index, label in enumerate(cls.MACRO_LABELS):
        lines.append("| %s | %s |" % (label, span(cls, index)))
    names = [cls.PATCHES[i][0] for i in sorted(cls.PATCHES)]
    lines += ["", "Patches: %s." % "; ".join(names), ""]
    return "\n".join(lines)


def render():
    """The page, exactly as the docs carry it."""
    return "\n".join([HEADER] + [render_class(c) for c in classes()])


if __name__ == "__main__":
    sys.stdout.write(render())
