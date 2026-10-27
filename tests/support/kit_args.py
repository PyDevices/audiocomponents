"""Readback and arguments: what the control surface does with the values a
host can hand it.

Cells, all on an 8192-frame click and noise train then silence:

- `rt-m<i>/<rate>/<patch>`: `set_macro(i, get_macro(i))` mid-stream
  changes no byte of the render, at the defaults and at every patch.
- `stops-m<i>`: 0, 64 and 127 are accepted and `get_macro` reads each
  back within 1e-4.
- `bad-m<i>`: NaN, +inf, -inf, -1, 128 and +-10**400 (an int past
  float's range). The contract (docs/reference/component-api.md, "Macro and patch
  state") clamps: NaN, -inf, -1 and -10**400 read back 0, +inf, 128 and
  10**400 read back 127, and each renders exactly
  what `set_macro(i, readback)` renders (`c`). A raise of any kind is
  red.
- `patch-p<k>`: from a fresh instance, `program_change(k)` sets
  `patch_index` and reads back the patch's values within 1e-4, and
  `program_change(0)` reads back what the fresh instance read.
- `ctor-<option>`: each numeric option of `_build` at 0 and at NaN. A
  raise must be ValueError or TypeError (`r`). A build (`c`) must report
  readable latency and tail, finite macros in 0..127, render without
  raising and without sitting on a rail where the input did not (kit
  RAIL_RUN); and a NaN build must render exactly what the defaults or the
  option at 0 render.

- `refused-<trigger>`: a call the contract's methods refuse (a negative,
  boolean or float `sample_position`, a `program_change` of 0.0, 1.0, True,
  -1, None or "0", a macro index or value of the wrong type, `channel=-1`)
  leaves the instance exactly as it was. Built at the defaults (`d`), at
  its last patch (`last`) and with every numeric constructor option moved
  off its default (`opt`), it takes the call before pull 8; a call that raises must raise ValueError,
  TypeError or IndexError, and either way (a call that raises, or one that
  is accepted or ignored as a no-op: `program_change` of an index past the
  last patch, a macro set to its own readback) every macro reads back the
  same on the 0-127 grid and as `macro()` plays it, `patch_index` is
  unchanged (after a raise, or any `program_change`) and the render equals
  one from an instance that never saw the call. A call not meant to be a no-op that is
  accepted is not judged (`a`).

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
BAD = (("nan", NAN), ("inf", INF), ("-inf", -INF), ("-1", -1), ("128", 128),
       ("10**400", 10 ** 400), ("-10**400", -10 ** 400))
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
            except Exception as exc:                      # noqa: BLE001
                moved = " and moved the macros" if gets(a) != before else ""
                return "RED(%s raised %s%s; the contract clamps)" % (
                    label, type(exc).__name__, moved)
            r = a.get_macro(index)
            if not kc.finite(r) or r < 0 or r > 127:
                return "RED(%s reads back %s)" % (label, kc.num(r))
            # The contract: NaN and below 0 are the bottom stop, above 127
            # the top.
            want = 127 if v > 127 else 0
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
        e.program_change(patch)
        if e.patch_index != patch:
            return "RED(patch_index reads %r)" % (e.patch_index,)
        got = gets(e)
        want = cls.PATCHES[patch][1]
        for i in range(len(want)):
            if abs(got[i] - want[i]) > READBACK_TOL:
                return "RED(m%d reads %s, the patch says %d)" % (
                    i, kc.num(got[i]), want[i])
        # Back at patch 0 it reads patch 0's values, not a fresh
        # instance's: a declared default may sit off patch 0's grid
        # (docs/reference/metadata.md; the kit holds reset-equals-fresh, not
        # fresh-equals-patch-0, ruled 2026-10-14).
        e.program_change(0)
        back = gets(e)
        zero = cls.PATCHES[0][1]
        for i in range(len(zero)):
            if abs(back[i] - zero[i]) > READBACK_TOL:
                return "RED(back at patch 0, m%d reads %s, patch 0 says %d)" \
                    % (i, kc.num(back[i]), zero[i])
    finally:
        _close(e)
    return "ok"


# -- refused calls ---------------------------------------------------------

#: The error classes a refusal may raise.
REFUSED_ERRORS = (ValueError, TypeError, IndexError)


def refusals(cls):
    """[(label, call, noop)]: each call takes the instance. `noop` is True
    for a call that must leave the instance as it was whether it raises or
    not; for the others only a raise is judged."""
    n = len(cls.MACRO_LABELS)
    past = max(cls.PATCHES) + 1
    out = [
        ("pc-negsp", lambda e: e.program_change(0, sample_position=-5),
         False),
        ("pc-boolsp", lambda e: e.program_change(0, sample_position=True),
         False),
        ("pc-floatsp", lambda e: e.program_change(0, sample_position=1.5),
         False),
        ("pc-0.0", lambda e: e.program_change(0.0), False),
        ("pc-1.0", lambda e: e.program_change(1.0), False),
        ("pc-true", lambda e: e.program_change(True), False),
        ("pc-neg", lambda e: e.program_change(-1), False),
        ("pc-none", lambda e: e.program_change(None), False),
        ("pc-str", lambda e: e.program_change("0"), False),
        ("pc-past", lambda e: e.program_change(past), True),
        ("pc-far", lambda e: e.program_change(1000000), True),
        ("sm-index-n", lambda e: e.set_macro(n, 5), False),
        ("sm-index-neg", lambda e: e.set_macro(-1, 5), False),
        ("sm-index-float", lambda e: e.set_macro(0.0, 5), False),
        ("sm-index-true", lambda e: e.set_macro(True, 5), False),
        ("sm-value-str", lambda e: e.set_macro(0, "x"), False),
        ("sm-value-none", lambda e: e.set_macro(0, None), False),
    ]
    for i in sorted(set((0, n - 1))):
        out += [
            ("sm-m%d-negchan" % i,
             lambda e, i=i: e.set_macro(i, e.get_macro(i), channel=-1),
             True),
            ("sm-m%d-negsp" % i,
             lambda e, i=i: e.set_macro(i, e.get_macro(i),
                                        sample_position=-5), False),
            ("sm-m%d-floatsp" % i,
             lambda e, i=i: e.set_macro(i, e.get_macro(i),
                                        sample_position=1.5), False),
            ("sm-m%d-nan" % i, lambda e, i=i: e.set_macro(i, NAN), False),
        ]
    return out


def _state(e):
    """What the instance reads back: each macro on the 0-127 grid and in
    its own units, and the patch."""
    return (gets(e), [e.macro(i) for i in range(len(type(e).MACRO_LABELS))],
            e.patch_index)


def _nudged(cls):
    """Candidate option sets with every numeric constructor option off its
    default (a constructor's exact value is state a refused call can
    drop)."""
    out = []
    for m in (0.73, 1.27):
        out.append(dict((name, d * m if d else 0.37)
                        for name, d in options_of(cls)
                        if name not in _BASE))
    return [o for o in out if o]


def refused_cell(cls, label, variant):
    patch = (max(cls.PATCHES) or None) if variant == "last" else None
    options = None
    if variant == "opt":
        for options in _nudged(cls):
            try:
                _close(fresh(cls, 48000, 2, None, options))
                break
            except REFUSALS:
                options = None
        if options is None:
            return "na(no option set builds)"
    call = None
    noop = False
    for lab, fn, nop in refusals(cls):
        if lab == label:
            call, noop = fn, nop
    if call is None:
        return "RED(no such trigger %s)" % label
    a = fresh(cls, 48000, 2, patch, options)
    b = fresh(cls, 48000, 2, patch, options)
    seen = {}

    def take(e):
        seen["before"] = _state(e)
        try:
            call(e)
            seen["code"] = "a"
        except REFUSED_ERRORS:
            seen["code"] = "r"
        except Exception as exc:                          # noqa: BLE001
            seen["code"] = "x"
            seen["exc"] = type(exc).__name__
        seen["after"] = _state(e)

    try:
        ra = kc.render(a, FRAMES)
        rb = kc.render(b, FRAMES, {K_MOVE: take})
    finally:
        _close(a)
        _close(b)
    code = seen["code"]
    if code == "x":
        return "RED(raised %s)" % seen["exc"]
    if code == "a" and not noop:
        return "ok(a)", kc.crc(rb)
    # An accepted set_macro rightly drops the patch; a refusal never does.
    if seen["after"][2] != seen["before"][2] and (
            code == "r" or label.startswith("pc-")):
        return "RED(%s moved patch_index to %r)" % (
            "a refusal" if code == "r" else "the call", seen["after"][2])
    for part, what in ((0, "read"), (1, "plays")):
        for i, (x, y) in enumerate(zip(seen["before"][part],
                                       seen["after"][part])):
            if x != y:
                return "RED(m%d %s %s, now %s)" % (i, what, kc.num(x),
                                                   kc.num(y))
    if ra != rb:
        d = lifecycle._first_diff(ra, rb, 0, len(ra))
        return "RED(renders differ from frame %d)" % (d // 4 - K_MOVE *
                                                      kc.BLOCK), kc.crc(rb)
    if _silent(ra) and _silent(rb):
        return "na(silent)", kc.crc(rb)
    return "ok(%s)" % code, kc.crc(rb)


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
        if value is None and default.strip() == "None":
            # An option whose default is "left out" (patch 0's step) names
            # the number it stands for in the class's `_OPTION_DEFAULTS`.
            value = getattr(owner, "_OPTION_DEFAULTS", {}).get(name)
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
    for label, _call, _noop in refusals(cls):
        for variant in ("d", "last", "opt"):
            cell("refused-%s/%s" % (label, variant), refused_cell, cls,
                 label, variant)
    for option, _default in options_of(cls):
        if option in _BASE:
            continue
        cell("ctor-%s" % option, ctor_cell, cls, option)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
