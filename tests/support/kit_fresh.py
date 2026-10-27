"""Reset equals fresh: after `reset()`, from every patch, a class renders
byte for byte what a fresh instance at patch 0 renders.

The contract says a reset clears every node and restores patch 0. So:

- `reset@<k>/<rate>/<ch>/<from>`: built at the defaults or at a patch,
  played for `k` pulls (0: before the first), then `reset()`. From that
  pull on it renders what a fresh instance built at patch 0 renders, fed
  the source from the frame the reset left it at, and reads back what the
  fresh one reads. No tail is forgiven: a block a voice still held, a line
  the reset kept or a filter's memory is red.
- `reset@8+m<i>=<v>/<rate>/<ch>/<from>`: the same, then the same macro
  move on both, four pulls later. A state the reset left that only a move
  wakes (an old line length, a write head the reset did not move) is red
  here and not in the cell before.
- `rpr<K>@8/<rate>/<ch>/d`: built at the defaults, played 8 pulls, then
  `reset()`, `program_change(K)` and `reset()` again. Held to the same
  fresh instance. A patch that builds part of the graph again between two
  resets must not leave the second reset reaching for a node the rebuild
  released (Distortion's scoop patches once raised here).
- `boot/<rate>/<ch>`, informational: whether a fresh instance at its
  defaults is patch 0 exactly. Patch values are integers and a declared
  default may sit off their grid (docs/reference/metadata.md), so a
  difference prints `na(info: ...)` and is never red.

Every cell compares `WINDOW_S` seconds from the reset, block by block,
stopping at the first difference. Numpy-free: the lines are the same on
CPython, MicroPython and CircuitPython.

    python tests/support/kit_fresh.py Saturation [--quick]
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import audiocore
import kit_common as kc
import lifecycle

CHECK = "fresh"
BLOCK = kc.BLOCK
#: The pull the mid-stream reset lands before, and how many pulls after it
#: the move comes.
RESET_AT = 8
MOVE_AFTER = 4
#: How long past the reset each cell compares, in seconds.
WINDOW_S = 2.0
#: The patch the fresh instance a reset is judged against is built at (the
#: constructor's `patch=`). Patch 0, where a reset lands.
FRESH_PATCH = 0


def _material(rate, channels):
    return lifecycle.material_for("once", rate, channels)


def _feed(values, rate, channels):
    return lifecycle.Feed(values, rate, channels, "256", loop=False)


def _readback(e):
    n = len(type(e).MACRO_LABELS)
    return ([e.get_macro(i) for i in range(n)], e.patch_index,
            e.tail_samples, e.latency_samples)


def _says(a, b):
    """What differs between two readbacks, or None."""
    names = ("macros", "patch_index", "tail_samples", "latency_samples")
    for name, x, y in zip(names, a, b):
        if x != y:
            return "%s %s, fresh %s" % (name, x, y)
    return None


def _lockstep(e, f, frames, fsize, actions):
    """Pull `e` and `f` in step, taking `actions` (pull index: callable on
    an instance) on both; the first frame they differ at, or -1."""
    a = bytearray()
    b = bytearray()
    k = 0
    base = 0
    total = frames * fsize
    while base < total:
        if k in actions:
            actions[k](e)
            actions[k](f)
        a.extend(kc.pull(e))
        b.extend(kc.pull(f))
        k += 1
        n = min(len(a), len(b))
        if a[:n] != b[:n]:
            return (base + lifecycle._first_diff(a, b, 0, n)) // fsize
        # MicroPython's bytearray takes no slice deletion.
        a = a[n:]
        b = b[n:]
        base += n
    return -1


def _fresh_at(cls, port, rate, options):
    """A fresh instance built at `FRESH_PATCH` by the constructor's own
    `patch=`, the way the lifecycle's PR builds one: a live
    `program_change` on a built instance may glide or wait for a zero
    crossing, and a reset is held to a build, not to a move."""
    keywords = dict(options)
    keywords["patch"] = FRESH_PATCH
    try:
        return cls(port, sample_rate=rate, **keywords)
    except TypeError:
        return kc.build(cls, port, rate, FRESH_PATCH, options)


def _between(e, between):
    """`reset()` then `program_change(between)`, the first reset of an
    `rpr` cell and the patch it lands between the two; nothing for None."""
    if between is not None:
        e.reset()
        e.program_change(between)


def _source_at(cls, rate, ch, patch, options, k, between=None):
    """The frame of the material the source stands at after `k` pulls of
    an instance built at `patch`, just before its reset, or -1.

    Before, not after: a fresh instance takes its first block from there,
    and so must a reset that re-primes a voice. A reset that took a block
    of its own and dropped it would start a block later and be red."""
    values = _material(rate, ch)
    feed = _feed(values, rate, ch)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        for _ in range(k):
            kc.pull(e)
        _between(e, between)
        block = bytes(audiocore.get_buffer(feed.mat)[1])
    finally:
        e.deinit()
    return lifecycle._locate(bytes(values), block, 2 * ch)


def reset_cell(cls, rate, ch, patch, options, k, move=None, between=None):
    """One reset cell's verdict. `between`, a patch: reset, that patch, and
    then the reset the cell judges."""
    fsize = 2 * ch
    values = _material(rate, ch)
    start = _source_at(cls, rate, ch, patch, options, k, between)
    if start < 0:
        return "na(source position not found)"
    feed = _feed(values, rate, ch)
    e = kc.build(cls, feed.port, rate, patch, options)
    f = None
    try:
        for _ in range(k):
            kc.pull(e)
        _between(e, between)
        e.reset()
        f = _fresh_at(cls, _feed(values[start * ch:], rate, ch).port,
                      rate, options)
        said = _says(_readback(e), _readback(f))
        if said:
            return "RED(after the reset: %s)" % said
        actions = {}
        if move is not None:
            index, value = move

            def act(x):
                x.set_macro(index, value)
            actions[MOVE_AFTER] = act
        d = _lockstep(e, f, int(WINDOW_S * rate), fsize, actions)
        if d >= 0:
            return "RED(differs from a fresh instance at +%d)" % d
        if move is not None:
            said = _says(_readback(e), _readback(f))
            if said:
                return "RED(after the move: %s)" % said
        return "ok"
    finally:
        e.deinit()
        if f is not None:
            f.deinit()


def boot_cell(cls, rate, ch, options):
    """Informational: a fresh instance against one handed patch 0 before
    its first pull. "ok", or "na(info: ...)" saying how they differ."""
    fsize = 2 * ch
    values = _material(rate, ch)
    e = kc.build(cls, _feed(values, rate, ch).port, rate, None, options)
    f = kc.build(cls, _feed(values, rate, ch).port, rate, 0, options)
    try:
        said = _says(_readback(f), _readback(e))
        if said:
            return "na(info: off patch 0, %s)" % said
        for i in range(len(e._macros)):
            if e._macros[i] != f._macros[i]:
                return ("na(info: macro %d sits at %r fresh, %r at patch 0)"
                        % (i, e._macros[i], f._macros[i]))
        d = _lockstep(f, e, int(WINDOW_S * rate), fsize, {})
        if d >= 0:
            return "na(info: patch 0 renders differently from fresh at +%d)" \
                % d
        return "ok"
    finally:
        e.deinit()
        f.deinit()


def run(cls, emit=print, quick=False, name=None, options=None):
    """Every fresh cell for `cls`; returns the red count."""
    options = options or {}
    cells = kc.Cells(name or cls.NAME, CHECK, emit)
    rates = (48000,) if quick else kc.RATES
    configs = kc.patches(cls)
    moving = configs if not quick else [None, configs[-1]]
    for rate in rates:
        for ch in kc.CHANNELS:
            where = "%d/%d" % (rate, ch)
            todo = [("boot/" + where, boot_cell, (cls, rate, ch, options))]
            for patch in configs:
                tail = "%s/%s" % (where, kc.pname(patch))
                for k in (0, RESET_AT):
                    todo.append(("reset@%d/%s" % (k, tail), reset_cell,
                                 (cls, rate, ch, patch, options, k)))
                if patch is None:
                    for between in sorted(cls.PATCHES):
                        todo.append(("rpr%d@%d/%s" % (
                            between, RESET_AT, tail), reset_cell,
                            (cls, rate, ch, patch, options, RESET_AT, None,
                             between)))
                if patch not in moving:
                    continue
                for index, value in kc.knob_positions(cls):
                    todo.append(("reset@%d+m%d=%d/%s" % (
                        RESET_AT, index, value, tail), reset_cell,
                        (cls, rate, ch, patch, options, RESET_AT,
                         (index, value))))
            for key, fn, args in todo:
                try:
                    verdict = fn(*args)
                except Exception as exc:                  # noqa: BLE001
                    verdict = "RED(raised %s: %s)" % (type(exc).__name__,
                                                      exc)
                cells.cell(key, verdict)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
