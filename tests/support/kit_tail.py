"""The tail harness: the output reaches exact zero inside the tail the class
reports, read after every control event, on a DC step and on low bursts.

A cell plays 4096 frames of material and then silence. The event's move
lands 3072 frames in (pull 12, inside the material) and, for the `back`
placement, its way back 1536 frames after the input stops. `tail_samples`
is read after each action; the bound is the last reading + latency + one
block, counted from the input's last non-zero frame or from the last
action, whichever is later (lifecycle P2's bound). The output's last
non-zero frame must be inside it; 2048 frames past it are rendered to see.

A class whose `tail_samples` is None gives no bound, so it must never fall
silent: the cell renders 3 s past the input and prints `na(tail None)`
when the output is still non-zero in the last second, RED when it fell
silent before (then the class could have stated a bound). A cell whose
output was zero all along prints `na(silent)`: it shows nothing.

    python tests/support/kit_tail.py DigitalDelay [--quick]
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import kit_common as kc
import lifecycle

CHECK = "tail"
MAT_FRAMES = 16 * kc.BLOCK
K_AWAY = 12
K_BACK = 22
MARGIN = lifecycle.MARGIN
#: For a class with no bound: seconds rendered past the input, and the
#: closing stretch that must still hold a non-zero sample.
NONE_WINDOW_S = 3
NONE_LIVE_S = 1

MATERIALS = ("dc", "lsb3", "m60", "fs")
#: The lifecycle events the harness reads the tail after: a reset, a macro
#: to each stop, Mix to 0, a patch change.
EVENT_PREFIXES = ("E1-reset@block", "E4-", "E5-", "E6-")

_MAT = {}


def material(which, channels):
    """`dc` a DC step to -6 dBFS, `lsb3` noise at +-3 LSB, `m60` noise
    at -60 dBFS (+-33), `fs` full-scale noise; 4096 frames each."""
    key = (which, channels)
    if key not in _MAT:
        if which == "dc":
            values = kc.dc(MAT_FRAMES, channels, 16384)
        elif which == "lsb3":
            values = kc.noise(MAT_FRAMES, channels, 3)
        elif which == "m60":
            values = kc.noise(MAT_FRAMES, channels, 33)
        elif which == "fs":
            values = kc.noise(MAT_FRAMES, channels, 32767)
        else:
            raise ValueError(which)
        _MAT[key] = values
    return _MAT[key]


def tail_events(cls, patch, quick):
    """(name, lifecycle Event or None, placement) for one patch."""
    out = [("none", None, "held")]
    for ev in lifecycle.events(cls, patch, quick):
        if not lifecycle._starts(ev.name, EVENT_PREFIXES):
            continue
        out.append((ev.name, ev, "held"))
        if ev.back and not quick:
            out.append((ev.name, ev, "back"))
    return out


def measure(cls, rate, channels, patch, which, ev, placement, options=None):
    """(verdict, digest) for one cell."""
    values = material(which, channels)
    in_end = kc.last_nonzero_frame(values, channels)
    feed = kc.feed(values, rate, channels)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        ctx = lifecycle.Ctx(e, patch)
        s = kc.Stream(e)
        tail = e.tail_samples
        last_action = 0
        pulls = K_BACK + 1 if placement == "back" else K_AWAY + 1
        for k in range(pulls):
            if ev is not None and k == K_AWAY:
                lifecycle.act(e, feed, ctx, ev.away)
                last_action = s.frames
                tail = e.tail_samples
            if ev is not None and placement == "back" and k == K_BACK:
                lifecycle.act(e, feed, ctx, ev.back)
                last_action = s.frames
                tail = e.tail_samples
            s.step()
        lat = e.latency_samples
        start = max(in_end, last_action)
        if tail is None:
            window = start + NONE_WINDOW_S * rate
            s.to(window)
            if not s.nonzero:
                verdict = "na(silent)"
            elif s.last <= window - NONE_LIVE_S * rate:
                verdict = "RED(tail None, silent from +%d)" % (s.last - start)
            else:
                verdict = "na(tail None)"
        else:
            bound = start + tail + lat + kc.BLOCK
            s.to(bound + MARGIN)
            if not s.nonzero:
                verdict = "na(silent)"
            elif s.last <= bound:
                verdict = "ok"
            else:
                verdict = "RED(rings to +%d, bound +%d)" % (s.last - start,
                                                           bound - start)
        return verdict, "%08x" % (s.crc & 0xFFFFFFFF)
    finally:
        e.deinit()


def run(cls, emit=print, quick=False, rates=kc.RATES, channels=kc.CHANNELS,
        patches=None, materials=MATERIALS, events=None, options=None,
        name=None):
    """Every tail cell for `cls`; returns the red count. `events` limits the
    cells to event names starting with one of its prefixes."""
    cells = kc.Cells(name or cls.NAME, CHECK, emit)
    if patches is None:
        patches = kc.patches(cls)
    for rate in rates:
        for ch in channels:
            for patch in patches:
                for evname, ev, placement in tail_events(cls, patch, quick):
                    if events is not None and not lifecycle._starts(
                            evname, events):
                        continue
                    for which in materials:
                        key = "%s/%d/%d/%s/%s" % (which, rate, ch,
                                                  kc.pname(patch), evname)
                        if placement == "back":
                            key += "/back"
                        try:
                            verdict, digest = measure(
                                cls, rate, ch, patch, which, ev, placement,
                                options)
                        except Exception as exc:          # noqa: BLE001
                            verdict, digest = "RED(raised %s: %s)" % (
                                type(exc).__name__, exc), None
                        cells.cell(key, verdict, digest)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
