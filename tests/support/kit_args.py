"""Readback and arguments: what the control surface does with the values a
host can hand it.

Cells, all on an 8192-frame click and noise train then silence:

- `rt-m<i>/<rate>/<patch>`: `set_macro(i, get_macro(i))` mid-stream
  changes no byte of the render, at the defaults and at every patch.
- `stops-m<i>`: 0, 64 and 127 are accepted and `get_macro` reads each
  back within 1e-4.
- `bad-m<i>`: NaN, +inf, -inf, -1 and 128. The contract does not say
  whether an out-of-range macro value raises or clamps, so either passes:
  a raise must be ValueError or TypeError and leave every macro where it
  was (`r`); a clamp must read back a finite value in 0..127 (0 below the
  range, 127 above it) and render exactly what `set_macro(i, readback)`
  renders (`c`).
- `patch-p<k>`: from a fresh instance, `program_change(k)` sets
  `patch_index` and reads back the patch's values within 1e-4, and
  `program_change(0)` reads back what the fresh instance read.
- `ctor-<option>`: each numeric option of `_build` at 0 and at NaN. A
  raise must be ValueError or TypeError (`r`). A build (`c`) must report
  readable latency and tail, finite macros in 0..127, render without
  raising and without sitting on a rail where the input did not (kit
  RAIL_RUN); and a NaN build must render exactly what the defaults or the
  option at 0 render.

A render that is silent throughout cannot show a difference; such a cell
prints `na(silent)`.

    python tests/support/kit_args.py DigitalDelay
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import kit_common as kc
import lifecycle

CHECK = "args"
PROBE_FRAMES = 8192
FRAMES = 16384
K_MOVE = 8
READBACK_TOL = 1e-4

NAN = float("nan")
INF = float("inf")
BAD = (("nan", NAN), ("inf", INF), ("-inf", -INF), ("-1", -1), ("128", 128))
REFUSALS = (ValueError, TypeError)

_PROBE = {}


def probe(channels):
    if channels not in _PROBE:
        _PROBE[channels] = lifecycle.click_noise(PROBE_FRAMES, channels)
    return _PROBE[channels]


#: The class's kit options (kit_options), under every build's own.
_BASE = {}


def fresh(cls, rate=48000, channels=2, patch=None, options=None):
    feed = kc.feed(probe(channels), rate, channels)
    merged = dict(_BASE)
    merged.update(options or {})
    return kc.build(cls, feed.port, rate, patch, merged)


def gets(e):
    return [e.get_macro(i) for i in range(len(type(e).MACRO_LABELS))]


def _silent(data):
    return lifecycle._is_zero(data)


def _close(e):
    try:
        e.deinit()
    except Exception:                                     # noqa: BLE001
        pass


# -- cells ---------------------------------------------------------------


def roundtrip(cls, index, rate, patch):
    a = fresh(cls, rate, 2, patch)
    b = fresh(cls, rate, 2, patch)
    try:
        ra = kc.render(a, FRAMES)
        rb = kc.render(b, FRAMES, {K_MOVE: lambda e: e.set_macro(
            index, e.get_macro(index))})
    finally:
        _close(a)
        _close(b)
    if _silent(ra) and _silent(rb):
        return "na(silent)", kc.crc(rb)
    if ra != rb:
        d = lifecycle._first_diff(ra, rb, 0, len(ra))
        return "RED(differs from frame %d)" % (d // 4 - K_MOVE * kc.BLOCK), \
            kc.crc(rb)
    return "ok", kc.crc(rb)


def stops_cell(cls, index):
    e = fresh(cls)
    try:
        for v in (0, 64, 127):
            try:
                e.set_macro(index, v)
            except Exception as exc:                      # noqa: BLE001
                return "RED(%d raised %s)" % (v, type(exc).__name__)
            r = e.get_macro(index)
            if not kc.finite(r) or abs(r - v) > READBACK_TOL:
                return "RED(%d reads back %s)" % (v, kc.num(r))
    finally:
        _close(e)
    return "ok"


def bad_cell(cls, index):
    codes = []
    for label, v in BAD:
        a = fresh(cls)
        b = None
        try:
            before = gets(a)
            try:
                a.set_macro(index, v)
            except REFUSALS:
                if gets(a) != before:
                    return "RED(%s raised and moved the macros)" % label
                codes.append("%s:r" % label)
                continue
            except Exception as exc:                      # noqa: BLE001
                return "RED(%s raised %s)" % (label, type(exc).__name__)
            r = a.get_macro(index)
            if not kc.finite(r) or r < 0 or r > 127:
                return "RED(%s reads back %s)" % (label, kc.num(r))
            want = 0 if v < 0 else (127 if v > 127 else None)
            if want is not None and abs(r - want) > READBACK_TOL:
                return "RED(%s reads back %s, not %d)" % (label, kc.num(r),
                                                          want)
            b = fresh(cls)
            b.set_macro(index, r)
            ra = kc.render(a, FRAMES)
            rb = kc.render(b, FRAMES)
            if ra != rb:
                return "RED(%s renders other than set_macro(%d, %s))" % (
                    label, index, kc.num(r))
            codes.append("%s:%s" % (label, "n" if _silent(ra) else "c"))
        finally:
            _close(a)
            if b is not None:
                _close(b)
    return "ok(%s)" % " ".join(codes)


def patch_cell(cls, patch):
    e = fresh(cls)
    try:
        start = gets(e)
        e.program_change(patch)
        if e.patch_index != patch:
            return "RED(patch_index reads %r)" % (e.patch_index,)
        got = gets(e)
        want = cls.PATCHES[patch][1]
        for i in range(len(want)):
            if abs(got[i] - want[i]) > READBACK_TOL:
                return "RED(m%d reads %s, the patch says %d)" % (
                    i, kc.num(got[i]), want[i])
        e.program_change(0)
        back = gets(e)
        for i in range(len(start)):
            if abs(back[i] - start[i]) > READBACK_TOL:
                return "RED(back at patch 0, m%d reads %s, fresh read %s)" \
                    % (i, kc.num(back[i]), kc.num(start[i]))
    finally:
        _close(e)
    return "ok"


# -- constructor options ---------------------------------------------------


def _defining(cls, attr):
    todo = [cls]
    while todo:
        c = todo.pop(0)
        if attr in c.__dict__:
            return c
        todo.extend(c.__bases__)
    return None


def _split_params(text):
    out = []
    depth = 0
    cur = ""
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [p.strip() for p in out if p.strip()]


def _number(text, module):
    if text in ("True", "False", "None") or text[:1] in ("'", '"'):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    value = getattr(module, text, None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def options_of(cls):
    """[(name, default)] for each numeric keyword of the class's `_build`,
    read from its source so every interpreter reads the same list."""
    owner = _defining(cls, "_build")
    if owner is None:
        return []
    module = sys.modules[owner.__module__]
    with open(module.__file__, "rb") as f:
        text = f.read().decode("utf-8")
    at = text.find("class %s(" % owner.__name__)
    at = text.find("def _build(", at if at >= 0 else 0)
    if at < 0:
        return []
    at += len("def _build(")
    depth = 1
    end = at
    while depth and end < len(text):
        if text[end] == "(":
            depth += 1
        elif text[end] == ")":
            depth -= 1
        end += 1
    out = []
    for param in _split_params(text[at:end - 1]):
        name, _sep, default = param.partition("=")
        name = name.strip()
        if name in ("self", "patch") or name.startswith("*") or not _sep:
            continue
        value = _number(default.strip(), module)
        if value is not None:
            out.append((name, value))
    return out


def _built(cls, options):
    """(instance or None, code, red or None)."""
    try:
        e = fresh(cls, options=options)
    except REFUSALS:
        return None, "r", None
    except Exception as exc:                              # noqa: BLE001
        return None, None, "raised %s" % type(exc).__name__
    try:
        e.tail_samples
        e.latency_samples
    except Exception as exc:                              # noqa: BLE001
        _close(e)
        return None, None, "tail or latency raised %s" % type(exc).__name__
    for i, r in enumerate(gets(e)):
        if not kc.finite(r) or r < 0 or r > 127:
            _close(e)
            return None, None, "m%d reads %s" % (i, kc.num(r))
    return e, "c", None


def _render_judged(e):
    """(bytes or None, red or None)."""
    try:
        data = kc.render(e, FRAMES)
    except Exception as exc:                              # noqa: BLE001
        return None, "render raised %s" % type(exc).__name__
    run, where = kc.rail_run(kc.samples(data), probe(2), 2,
                             e.latency_samples)
    if run > kc.RAIL_RUN:
        return data, "%d frames on a rail from %d" % (run, where)
    return data, None


def ctor_cell(cls, option):
    renders = {}
    codes = []
    for label, v in (("0", 0), ("nan", NAN)):
        e, code, red = _built(cls, {option: v})
        if red is not None:
            return "RED(%s: %s)" % (label, red)
        if e is not None:
            try:
                data, red = _render_judged(e)
            finally:
                _close(e)
            if red is not None:
                return "RED(%s: %s)" % (label, red)
            renders[label] = data
        codes.append("%s:%s" % (label, code))
    if "nan" in renders:
        d = fresh(cls)
        try:
            default = kc.render(d, FRAMES)
        finally:
            _close(d)
        if renders["nan"] not in (default, renders.get("0")):
            return "RED(nan renders neither the default nor 0)"
    return "ok(%s)" % " ".join(codes)


def run(cls, emit=print, quick=False, name=None, options=None):
    """Every args cell for `cls`; returns the red count."""
    global _BASE
    _BASE = dict(options or {})
    cells = kc.Cells(name or cls.NAME, CHECK, emit)
    n = len(cls.MACRO_LABELS)
    rates = (48000,) if quick else kc.RATES

    def cell(key, fn, *args):
        try:
            got = fn(*args)
        except Exception as exc:                          # noqa: BLE001
            got = "RED(raised %s: %s)" % (type(exc).__name__, exc)
        if isinstance(got, tuple):
            cells.cell(key, got[0], got[1])
        else:
            cells.cell(key, got)

    for i in range(n):
        for rate in rates:
            for patch in kc.patches(cls):
                cell("rt-m%d/%d/%s" % (i, rate, kc.pname(patch)), roundtrip,
                     cls, i, rate, patch)
    for i in range(n):
        cell("stops-m%d" % i, stops_cell, cls, i)
    for i in range(n):
        cell("bad-m%d" % i, bad_cell, cls, i)
    for patch in sorted(cls.PATCHES):
        cell("patch-p%d" % patch, patch_cell, cls, patch)
    for option, _default in options_of(cls):
        if option in _BASE:
            continue
        cell("ctor-%s" % option, ctor_cell, cls, option)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
