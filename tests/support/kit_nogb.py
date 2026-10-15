"""A board build with no `audiocore.get_buffer`.

CircuitPython's default board builds compile `audiocore.get_buffer` out
(CIRCUITPY_AUDIOCORE_DEBUG), and a class that primes a voice at
construction and flushes the primed block by pulling it once is then left
holding that block. The first pull, or the first pull after a Mix move back
from a bypass, plays source frames from the start of the material at a
later point: the stale-block shape.

This check runs the lifecycle matrix's E1 (reset), E5 (Mix to 0 and back),
E6 (patches) and E10 (events before the first pull) at 48000 Hz, stereo and
mono, twice: once as it is, once with `get_buffer` hidden from the class's
module, from `audioeffects` (`_component` and the rebuilt classes) and from
the classes the class derives from. A cell is one lifecycle cell; it is red
when any of P1 to P4 reads other than it did with `get_buffer` present
(ok, na or RED: the frames a red verdict names are not compared).

Every patch, and the defaults, runs on its own: `run/48000/<ch>/<patch>`
is red when the class raises there (with `get_buffer` or without), and the
other patches are still judged.

`bytes-<scenario>` cells hold the whole render, every channel, to equal
the one with `get_buffer` present: a reset, two resets in a row, a reset
before the first pull, a patch change and a reset in one block, at the
defaults and at every patch, stereo and mono.

It runs on CPython, MicroPython and CircuitPython: it rebinds the
`audiocore` name those modules read to a stand-in that has everything but
`get_buffer`, and puts it back afterwards, so on a native build it is the
class's own Python that loses `get_buffer`, as on a board. The matrix's own
pulls (lifecycle, kit_common) keep the real one. A module that imports
`get_buffer` inside a function is not reached.

    python tests/support/kit_nogb.py StereoWidener
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import audiocore
import kit_common as kc
import lifecycle

CHECK = "nogb"
EVENTS = ("E1", "E5", "E6", "E10")
PROPS = ("P1", "P2", "P3", "P4")
#: Modules whose own pulls the matrix needs.
KEEP = ("lifecycle", "kit_common")


class _NoGetBuffer:
    """`audiocore` without `get_buffer`."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        if name == "get_buffer":
            raise AttributeError(name)
        return getattr(self._real, name)


def _bases(cls, out):
    """`cls` and every class it derives from (MicroPython has no
    `__mro__`)."""
    if cls in out:
        return out
    out.append(cls)
    for base in getattr(cls, "__bases__", ()):
        _bases(base, out)
    return out


def _modules(cls):
    names = set(["audioeffects._component"])
    for name in list(sys.modules):
        if name == "audioeffects" or name.startswith("audioeffects."):
            names.add(name)
    for base in _bases(cls, []):
        module = getattr(base, "__module__", None)
        if module is not None:
            names.add(module)
    return [sys.modules[n] for n in sorted(names)
            if n in sys.modules and n not in KEEP]


class hidden:
    """Hide `audiocore.get_buffer` from `cls`'s modules for a `with`."""

    def __init__(self, cls):
        self.cls = cls
        self.saved = []

    def __enter__(self):
        real = audiocore
        stand_in = _NoGetBuffer(real)
        pull = real.get_buffer
        for module in _modules(self.cls):
            for key, value in list(module.__dict__.items()):
                if value is real:
                    self.saved.append((module, key, value))
                    setattr(module, key, stand_in)
                elif value is pull:
                    self.saved.append((module, key, value))
                    delattr(module, key)
        return self

    def __exit__(self, *exc):
        for module, key, value in reversed(self.saved):
            setattr(module, key, value)
        self.saved = []
        return False


def _parse(lines):
    out = {}
    for line in lines:
        parts = line.split("|")
        if parts[0] == "SUMMARY" or len(parts) < 6:
            continue
        key = "%s/%s/%s/%s" % (parts[1], parts[2], parts[3], parts[4])
        got = {}
        for part in parts[5:]:
            prop, _sep, verdict = part.partition(":")
            got[prop] = verdict
        out[key] = got
    return out


def _kind(verdict):
    """ok, na, decl or RED: the numbers in a red verdict move with the
    frames a run happens to lose, and are not compared."""
    return (verdict or "none").split("(")[0]


def _twice(*calls):
    def go(e):
        for call in calls:
            call(e)
    return go


def _reset(e):
    e.reset()


def _last_patch(e):
    e.program_change(max(type(e).PATCHES))


#: name: {pull index: action}. Resets that follow each other, a reset
#: before anything has been pulled, a patch change and a reset in one block.
SCENARIOS = (
    ("reset-once", {8: _reset}),
    ("reset-twice", {8: _twice(_reset, _reset)}),
    ("reset-first", {0: _reset}),
    ("reset-first-twice", {0: _twice(_reset, _reset)}),
    ("patch-reset", {8: _twice(_last_patch, _reset)}),
    ("reset-patch", {8: _twice(_reset, _last_patch)}),
    ("resets-apart", {8: _reset, 9: _reset}),
)
FRAMES = 16384


def _render(cls, options, rate, ch, patch, actions):
    import kit_args
    feed = kc.feed(kit_args.probe(ch), rate, ch)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        return kc.render(e, FRAMES, actions)
    finally:
        e.deinit()


def _bytes_cell(cls, options, rate, ch, patch, actions):
    want = _render(cls, options, rate, ch, patch, actions)
    with hidden(cls):
        got = _render(cls, options, rate, ch, patch, actions)
    if got == want:
        return "ok"
    d = lifecycle._first_diff(want, got, 0, len(want))
    return "RED(bytes differ without get_buffer from frame %d, channel %d)" \
        % (d // (2 * ch), (d // 2) % ch)


def _run(cls, options, quick, name, ch, patch):
    lines = []
    lifecycle.run_class(cls, options=options, rates=(48000,),
                        channels=(ch,), patches=[patch], only=EVENTS,
                        quick=quick, emit=lines.append, name=name)
    return _parse(lines)


def _raised(exc):
    return "%s: %s" % (type(exc).__name__, exc)


def run(cls, emit=print, quick=False, name=None, options=None,
        patches=None):
    """Every nogb cell for `cls`; returns the red count. `patches` limits
    the run to some of `[None] + sorted(cls.PATCHES)` (None the defaults),
    so a slow class can be run a patch at a time."""
    cells = kc.Cells(name or cls.NAME, CHECK, emit)
    present = {}
    absent = {}
    if patches is None:
        patches = [None] + sorted(cls.PATCHES)
    for patch in patches:
        for ch in (2, 1):
            # One lifecycle run per patch and layout, each in its own
            # cell, so a class that raises without get_buffer at one patch
            # says which, and the other patches are still judged.
            key = "run/48000/%d/%s" % (ch, "d" if patch is None
                                       else "p%d" % patch)
            try:
                want = _run(cls, options, quick, cells.name, ch, patch)
            except Exception as exc:                      # noqa: BLE001
                cells.cell(key, "RED(raised with get_buffer: %s)"
                           % _raised(exc))
                continue
            try:
                with hidden(cls):
                    got = _run(cls, options, quick, cells.name, ch, patch)
            except Exception as exc:                      # noqa: BLE001
                cells.cell(key, "RED(raised without get_buffer: %s)"
                           % _raised(exc))
                continue
            cells.cell(key, "ok")
            present.update(want)
            absent.update(got)
            for label, actions in SCENARIOS:
                key = "bytes-%s/48000/%d/%s" % (
                    label, ch, "d" if patch is None else "p%d" % patch)
                try:
                    cells.cell(key, _bytes_cell(cls, options or {}, 48000,
                                                ch, patch, actions))
                except Exception as exc:                  # noqa: BLE001
                    cells.cell(key, "RED(raised %s)" % _raised(exc))
    for key in sorted(present):
        want = present[key]
        got = absent.get(key)
        if got is None:
            cells.cell(key, "RED(no cell without get_buffer)")
            continue
        diff = [p for p in PROPS if _kind(want.get(p)) != _kind(got.get(p))]
        if diff:
            cells.cell(key, "RED(%s)" % "; ".join(
                "%s %s with get_buffer, %s without" % (
                    p, want.get(p), got.get(p)) for p in diff))
        else:
            cells.cell(key, "ok")
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
