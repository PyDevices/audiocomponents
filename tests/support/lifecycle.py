"""The shared lifecycle matrix for audioeffects classes.

One fixed set of lifecycle EVENTS (reset, a host reset of the output,
deinit, macro stops, Mix to 0 and back, patch changes, a source that runs
dry or ends, odd source buffer sizes, moves before the first pull, several
moves before one pull), run the same way on every class, each cell judged by
the same PROPERTIES against a CONTROL instance that never met the event. No
model is in the loop: a cell is green or red by arithmetic on the bytes.

It is numpy-free and runs unchanged on CPython, MicroPython and
CircuitPython, so the three interpreters can be held to printing the same
line for every cell (P6, judged by `tests/test_lifecycle_matrix.py`).

    python tests/support/lifecycle.py DigitalDelay [--events E1,E5] [--quick]

`LIFECYCLE.md` beside this file says what each event and property is and
how a class declares an exception. `run_class()` is the entry point; the
planted faults at the bottom are the matrix's own proof that each property
can fail.
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")

import binascii

try:
    from array import array
except ImportError:                                   # pragma: no cover
    array = None

import audiocore
import audiofilters
import audiomixer

try:
    from audioroute import Port
except ImportError:                                   # pragma: no cover
    Port = None

try:
    from audioeffects import _component
except ImportError:                                   # pragma: no cover
    _component = None

#: `_component` reads VENDOR off the module a class is defined in, and the
#: planted classes are defined here.
VENDOR = "PyDevices"

BLOCK = 256
RATES = (48000, 22050)
CHANNELS = (2, 1)
#: The pull the mid-stream event lands before, and how many pulls later the
#: move comes back.
K0 = 12
GAP = 2
#: Frames compared (P4) or held to zero (P2) past each bound.
MARGIN = 2048
#: P5's factor, as a fraction: 3/2 = 1.5.
STEP_NUM = 3
STEP_DEN = 2
#: Frames of silence P3 waits for when a class reports no tail.
NO_TAIL_WAIT = 10 * 48000

#: The class's wet/dry control, by macro label. A class not named here uses
#: the macro labelled "Mix".
MIX_INDEX = {
    "SlapbackDelay": 1,        # "Level": the slap's level; 0 is the dry
}

#: Where a class cannot satisfy a property by design, it says so HERE, one
#: row per (class NAME, event name prefix, property): reason. A matching
#: cell prints `decl` instead of RED and is counted as a declared exception.
#: Nothing else skips a cell.
DECLARED = {
    ("AnalogDelay", "E", "P5"):
        "a control that jumps steps the output (family, audiocomponents#117);"
        " a Time move bends the pitch while the line walks, by design",
    ("AnalogDelay", "E8-dry", "P3"):
        "a tail cut short by a stopped source carries on when it comes back"
        " (family, audiodsp#180)",
    ("AnalogDelay", "E2-", "P4"):
        "reset_buffer restarts the modulation triangle (the node's"
        " state_init), so a modulated patch then matches a fresh instance,"
        " not the uninterrupted control",
    ("AnalogDelay", "E4-", "P4"):
        "a Mod Rate move shifts the free-running triangle; after a Time move"
        " and back, a 1-LSB rounding difference circulates in the feedback"
        " loop past tail_samples",
    ("AnalogDelay", "E6-", "P4"):
        "a patch change shifts the free-running triangle, or leaves a 1-LSB"
        " rounding difference circulating in the feedback loop past"
        " tail_samples",
    ("AnalogDelay", "E11-", "P4"):
        "a patch change shifts the free-running triangle, or leaves a 1-LSB"
        " rounding difference circulating in the feedback loop past"
        " tail_samples",
    ("TapeDelay", 'E1-', 'P4'):
        'reset() restarts the wow and flutter table, so the wobble is never in phase with a fresh instance again',
    ("TapeDelay", 'E2-', 'P4'):
        'a host reset_buffer restarts the wow and flutter table, so the wobble is never in phase with a fresh instance again',
    ("TapeDelay", 'E4-m0=0', 'P4'):
        "a Time move and back leaves other rounding in the loop than a fresh instance's; while material plays a 1 LSB difference can outlast tail_samples, which bounds silence",
    ("TapeDelay", 'E4-m0=', 'P5'):
        "varispeed bends the pitch on a Time move: a bend up past 1.5x steepens the triangle past P5's limit, and T1a's step clause holds (no click)",
    ("TapeDelay", 'E11-2macro', 'P5'):
        "varispeed bends the pitch on a Time move: a bend up past 1.5x steepens the triangle past P5's limit, and T1a's step clause holds (no click)",
    ("TapeDelay", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("TapeDelay", 'E4-m4=', 'P5'):
        "family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Wow: a balance move swaps the table's shape)",
    ("TapeDelay", 'E5-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("TapeDelay", 'E6-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("TapeDelay", 'E9-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("TapeDelay", 'E11-mix+patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix and a patch change)',
    ("TapeDelay", 'E11-2patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("TapeDelay", 'E11-3moves', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Time and a patch change)',
    ("TapeDelay", 'E8-dry', 'P3'):
        'family limit, disclosed (audiodsp#180): a tail cut short by a source that stopped carries on when the source comes back',
    # Reverb: the tank's int16 lines truncate on every write and its
    # filters run in float, so once two tanks have heard different material
    # they stay a few LSB apart under the same input for good (seen at Mod
    # Depth 0 too); a reset or a re-cut also restarts the modulation phase.
    ("Reverb", "E1-", "P4"): "a reset tank never re-converges byte for byte (int16 lines, free modulation phase)",
    ("Reverb", "E2-", "P4"): "a reset_buffer tank never re-converges byte for byte (int16 lines, free modulation phase)",
    ("Reverb", "E4-", "P4"): "a move that reaches the loop leaves the tank a few LSB off a fresh one for good",
    ("Reverb", "E6-", "P4"): "a patch move reaches the loop and leaves the tank a few LSB off a fresh one for good",
    ("Reverb", "E11-", "P4"): "moves that reach the loop leave the tank a few LSB off a fresh one for good",
    # The ruling of 2026-09-28, disclosed in the docstring's "Limits
    # shared by the family" (audiocomponents#117, audiodsp#180).
    ("Reverb", "E4-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E5-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E6-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E9-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E11-", "P5"): "family: a control that jumps makes the output step (#117)",
    ("Reverb", "E8-dry", "P3"): "family: the tail rings only while the source feeds (audiodsp#180)",
    ("DigitalDelay", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("DigitalDelay", 'E4-m6=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Repeat Tone)',
    ("DigitalDelay", 'E4-m7=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Repeat Cut)',
    ("DigitalDelay", 'E5-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("DigitalDelay", 'E6-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("DigitalDelay", 'E9-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("DigitalDelay", 'E11-mix+patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix and a patch change)',
    ("DigitalDelay", 'E11-2patch', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("DigitalDelay", 'E11-3moves', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (the patch change; the Time moves glide)',
    ("DigitalDelay", 'E8-dry', 'P3'):
        'family limit, disclosed (audiodsp#180): a tail cut short by a source that stopped carries on when the source comes back',
    ("SlapbackDelay", "E", "P5"):
        "a control that jumps steps the output (family, audiocomponents#117):"
        " Level, Tone and patch moves have no ramp",
    ("SlapbackDelay", "E8-dry", "P3"):
        "a tail cut short by a stopped source carries on when it comes back"
        " (family, audiodsp#180)",
    ("SlapbackDelay", "E1-", "P4"):
        "a reset restarts the Wow wobble where a fresh instance's starts;"
        " the control never stopped, so its wobble is further along and"
        " with Wow above 0 the two never line up again (ok at Wow 0)",
    ("SlapbackDelay", "E2-", "P4"):
        "reset_buffer restarts the Wow wobble where a fresh instance's"
        " starts; the control never stopped, so its wobble is further along"
        " and with Wow above 0 the two never line up again (ok at Wow 0)",
    ("MultiTapDelay", "E", "P5"):
        "family limit, disclosed (audiocomponents#117): a control that jumps"
        " makes the output step (Time and Heads move every head to a new"
        " grid, Mix, Tilt and a patch change jump a level)",
    ("MultiTapDelay", "E1-", "P4"):
        "reset() empties both lines where the control's hold older laps; they"
        " die to 1 LSB inside tail_samples, and a 1-LSB rounding difference"
        " then circulates in the loop past it (silence reaches zero inside"
        " it)",
    ("MultiTapDelay", "E5-", "P4"):
        "a return from Mix 0 starts both lines empty where the control's hold"
        " older laps; they die to 1 LSB inside tail_samples, and a 1-LSB"
        " rounding difference then circulates in the loop past it",
    ("MultiTapDelay", "E9-", "P4"):
        "a return from Mix 0 starts both lines empty where the control's hold"
        " older laps; they die to 1 LSB inside tail_samples, and a 1-LSB"
        " rounding difference then circulates in the loop past it",
    ("MultiTapDelay", "E4-m4=", "P4"):
        "a return from Mix 0 starts both lines empty where the control's hold"
        " older laps; they die to 1 LSB inside tail_samples, and a 1-LSB"
        " rounding difference then circulates in the loop past it",
    ("MultiTapDelay", "E4-m6=", "P4"):
        "crossing Repeat Tone's out stop swaps the loop that makes the laps"
        " and empties the lap node going in; the old laps die to 1 LSB inside"
        " tail_samples, and a 1-LSB rounding difference then circulates past"
        " it",
    ("MultiTapDelay", "E6-", "P4"):
        "a patch change that crosses Repeat Tone's out stop empties the lap"
        " node going in; the old laps die to 1 LSB inside tail_samples, and a"
        " 1-LSB rounding difference then circulates past it",
    ("MultiTapDelay", "E11-", "P4"):
        "Mix 0 or a crossing of Repeat Tone's out stop empties a line; the old"
        " laps die to 1 LSB inside tail_samples, and a 1-LSB rounding"
        " difference then circulates past it",
    ("MultiTapDelay", "E8-dry", "P4"):
        "the lines hold the gap the source left, where the control's hold"
        " audio; that dies to 1 LSB inside tail_samples, and a 1-LSB rounding"
        " difference then circulates in the loop past it, for good at some"
        " settings",
    ("MultiTapDelay", "E4-m0=", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a Time move and back replays it",
    ("MultiTapDelay", "E6-", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a patch change and back replays it",
    ("MultiTapDelay", "E11-2patch", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a patch change and back replays it",
    ("MultiTapDelay", "E11-3moves", "P3"):
        "CPython only, the node's twin (audiodsp#177): the CPython"
        " audiodelays.MultiTapDelay keeps the line past a shorter delay_ms"
        " that the C node zeroes, so a patch change and back replays it",
    ("ConvolutionReverb", 'E1-', 'P1'):
        'by design, disclosed: reset() empties the room, so the block in flight, 256 frames, comes out as exact zero, dry included',
    ("ConvolutionReverb", 'E2-', 'P1'):
        'by design, disclosed: a host reset_buffer resets the node, so the block in flight, 256 frames, comes out as exact zero, dry included',
    ("ConvolutionReverb", 'E4-m5=0', 'P1'):
        'by design, disclosed: Mix acts from the end of the block in flight, so the block after a move to Mix 0 comes out at the old Mix',
    ("ConvolutionReverb", 'E5-', 'P1'):
        'by design, disclosed: Mix acts from the end of the block in flight, so the block after a move to Mix 0 comes out at the old Mix',
    ("ConvolutionReverb", 'E4-m1=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Damping re-synthesizes the room)',
    ("ConvolutionReverb", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Predelay re-synthesizes the room)',
    ("ConvolutionReverb", 'E4-m4=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Room re-synthesizes the room)',
    ("ConvolutionReverb", 'E4-m5=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("ConvolutionReverb", 'E5-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("ConvolutionReverb", 'E6-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (a patch change)',
    ("ConvolutionReverb", 'E9-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
    ("ConvolutionReverb", 'E11-', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (two or three moves before one pull)',
    ("ConvolutionReverb", 'E8-dry', 'P3'):
        'family limit, disclosed (audiodsp#180): a tail cut short by a source that stopped carries on when the source comes back',
    ("PingPongDelay", 'E4-m2=', 'P5'):
        'family limit, disclosed (audiocomponents#117): a control that jumps makes the output step (Mix)',
}

SOURCE_KINDS = ("256", "100", "512", "1000", "raw")


# --------------------------------------------------------------------------
# Material


def _lcg(state):
    return (1103515245 * state + 12345) & 0x7FFFFFFF


def click_noise(frames, channels, spacing=64, seed=12345):
    """Clicks every `spacing` frames, each at its own amplitude (and the
    second channel at a different one), with an LCG noise burst in the
    middle eighth: a frame lost, repeated or swapped is visible."""
    values = array("h", bytes(2 * frames * channels))
    state = seed
    for frame in range(3, frames, spacing):
        state = _lcg(state)
        amp = 2000 + (state >> 8) % 24000
        if (state >> 4) & 1:
            amp = -amp
        values[frame * channels] = amp
        if channels == 2:
            values[frame * channels + 1] = -(amp // 2) - 7
    lo = frames // 2
    for frame in range(lo, lo + frames // 8):
        for channel in range(channels):
            state = _lcg(state)
            values[frame * channels + channel] = ((state >> 8) % 16001) - 8000
    return values


def triangle(frames, channels, rate, amp=12000, hz=100):
    """An integer triangle: the same bytes on every interpreter, and its
    largest step is small (4 * amp * hz / rate)."""
    values = array("h", bytes(2 * frames * channels))
    period = rate // hz
    for frame in range(frames):
        phase = (frame % period) * 4 * amp // period
        if phase < amp:
            value = phase
        elif phase < 3 * amp:
            value = 2 * amp - phase
        else:
            value = phase - 4 * amp
        for channel in range(channels):
            values[frame * channels + channel] = value
    return values


def _raw(values, rate, channels):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def _adapter(values, rate, channels, frames, loop):
    """A RawSample handed out `frames` at a time: the house re-blocker.
    With loop False it pads silence after the material, for ever."""
    block = audiofilters.Filter(filter=None, mix=1.0,
                                buffer_size=frames * channels * 2,
                                sample_rate=rate, channel_count=channels)
    block.play(_raw(values, rate, channels), loop=loop)
    return block


class Feed:
    """The source a class is built around: a Port the host re-points.

    `mat` is the material, `sil` silence, `empty` a sample that hands back
    an empty buffer (the only way a native source can run dry). A Port
    moves no bytes, so a class sees exactly what the source behind it
    hands."""

    def __init__(self, values, rate, channels, kind, loop):
        self.rate = rate
        self.channels = channels
        if kind == "raw":
            self.mat = _raw(values, rate, channels)
        else:
            self.mat = _adapter(values, rate, channels, int(kind), loop)
        self.sil = _adapter(array("h", bytes(4 * channels * BLOCK)), rate,
                            channels, BLOCK, True)
        # MicroPython's RawSample refuses an empty array but takes an
        # empty 16-bit memoryview.
        self.empty = _raw(memoryview(array("h", [0, 0]))[0:0], rate,
                          channels)
        self.port = Port(self.mat)
        self.current = self.mat
        self.sample_rate = rate
        self.channel_count = channels

    def point(self, node):
        self.current = node
        self.port.play(node)


# --------------------------------------------------------------------------
# Bytes


ZERO = bytes(BLOCK * 2 * 2 * 8)


def _is_zero(data):
    step = len(ZERO)
    for lo in range(0, len(data), step):
        chunk = data[lo:lo + step]
        if chunk != ZERO[:len(chunk)]:
            return False
    return True


def _samples(data):
    out = array("h")
    try:
        out.frombytes(bytes(data))
        return out
    except AttributeError:
        pass
    import struct
    out.extend(struct.unpack("<%dh" % (len(data) // 2), bytes(data)))
    return out


def _first_diff(a, b, lo, hi):
    """First byte index in [lo, hi) where a and b differ, or -1."""
    step = 4096
    pos = lo
    while pos < hi:
        end = min(hi, pos + step)
        if a[pos:end] != b[pos:end]:
            for i in range(pos, end):
                if a[i] != b[i]:
                    return i
        pos = end
    return -1


def _last_diff(a, b, lo, hi):
    """Last byte index in [lo, hi) where a and b differ, or -1."""
    step = 4096
    end = hi
    while end > lo:
        pos = max(lo, end - step)
        if a[pos:end] != b[pos:end]:
            for i in range(end - 1, pos - 1, -1):
                if a[i] != b[i]:
                    return i
        end = pos
    return -1


def _max_step(values, channels, lo, hi):
    top = 0
    for ch in range(channels):
        prev = None
        for i in range(lo * channels + ch, hi * channels, channels):
            v = values[i]
            if prev is not None:
                d = v - prev
                if d < 0:
                    d = -d
                if d > top:
                    top = d
            prev = v
    return top


# --------------------------------------------------------------------------
# The class under test


def _starts(text, prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False


def mix_index(cls):
    name = cls.NAME
    if name in MIX_INDEX:
        return MIX_INDEX[name]
    labels = cls.MACRO_LABELS
    for i in range(len(labels)):
        if labels[i] == "Mix":
            return i
    return None


def stops(cls, index):
    mode = cls.MACRO_MODES.get(index, "UNIPOLAR")
    if mode == "BIPOLAR":
        return (0, 64, 127)
    return (0, 127)


class Ctx:
    """What one instance needs to undo a move: the patch it was built at,
    or its macros' exact positions at the default."""

    def __init__(self, e, patch):
        self.patch = patch
        self.positions = list(e._macros)
        self.midi = [e.get_macro(i) for i in range(len(self.positions))]
        self.inexact = 0


def restore(e, ctx):
    if ctx.patch is not None:
        e.program_change(ctx.patch)
        return
    for i in range(len(ctx.midi)):
        e.set_macro(i, ctx.midi[i])
    # set_macro(get_macro()) is not always bit-exact at the constructor's
    # unquantised defaults; land exactly, so P4 measures the event and not
    # the width of a float, and count it.
    for i in range(len(ctx.positions)):
        if e._macros[i] != ctx.positions[i]:
            ctx.inexact += 1
            e._macros[i] = ctx.positions[i]
            e._apply_macro(i, ctx.positions[i])


def act(e, feed, ctx, actions):
    for a in actions:
        op = a[0]
        if op == "reset":
            e.reset()
        elif op == "rb":
            audiocore.reset_buffer(e.output)
        elif op == "macro":
            e.set_macro(a[1], a[2])
        elif op == "patch":
            e.program_change(a[1])
        elif op == "restore":
            restore(e, ctx)
        elif op == "dry":
            feed.port.play(feed.empty)
        elif op == "wet":
            feed.port.play(feed.current)
        elif op == "end":
            feed.point(feed.empty)
        else:
            raise ValueError(op)


class Event:
    """`away` before pull K0 (or before the first pull when `first`),
    `back` GAP pulls later (in the same gap when `first`)."""

    def __init__(self, name, away, back=None, kind="256", moves_mix=False,
                 control_move=True, post0=False, first=False, gap=GAP):
        self.name = name
        self.away = away
        self.back = back or []
        self.kind = kind
        self.moves_mix = moves_mix
        self.control_move = control_move
        self.post0 = post0
        self.first = first
        self.gap = gap


def events(cls, patch, quick=False):
    """Every event for `cls` at `patch` (None: the constructor defaults)."""
    mix = mix_index(cls)
    labels = cls.MACRO_LABELS
    npatch = len(cls.PATCHES)
    full = (not quick) or patch is None
    out = [
        Event("E1-reset@block", [("reset",)], kind="256",
              control_move=False, post0=True),
        Event("E1-reset@part", [("reset",)], kind="100",
              control_move=False, post0=True),
        Event("E2-reset_buffer", [("rb",)], control_move=False),
    ]
    if full:
        for i in range(len(labels)):
            for v in stops(cls, i):
                out.append(Event("E4-m%d=%d" % (i, v), [("macro", i, v)],
                                 [("restore",)], moves_mix=(i == mix)))
    if mix is not None:
        out.append(Event("E5-mix0", [("macro", mix, 0)], [("restore",)],
                         moves_mix=True, gap=6))
    targets = range(npatch) if full else (0, npatch - 1)
    for q in targets:
        if q == patch:
            continue
        out.append(Event("E6-p%d" % q, [("patch", q)], [("restore",)],
                         moves_mix=True))
    out.append(Event("E8-dry", [("dry",)], [("wet",)], kind="100",
                     control_move=False, gap=1))
    out.append(Event("E8-end", [("end",)], kind="100", control_move=False))
    for kind in SOURCE_KINDS:
        if mix is not None:
            out.append(Event("E9-src%s" % kind, [("macro", mix, 0)],
                             [("restore",)], kind=kind, moves_mix=True,
                             gap=6))
    out.append(Event("E10-reset", [("reset",)], control_move=False,
                     post0=True, first=True))
    if full:
        out.append(Event("E10-macros",
                         [("macro", i, 127) for i in range(len(labels))],
                         [("restore",)], moves_mix=True, first=True))
    if mix is not None:
        out.append(Event("E10-mix0", [("macro", mix, 0)], [("restore",)],
                         moves_mix=True, first=True))
    out.append(Event("E10-patch", [("patch", npatch - 1 if patch != npatch - 1
                                    else 0)], [("restore",)],
                     moves_mix=True, first=True))
    if full:
        out.append(Event("E11-2macro", [("macro", 0, 0), ("macro", 0, 127)],
                         [("restore",)], moves_mix=(mix == 0)))
        if mix is not None:
            out.append(Event("E11-mix+patch",
                             [("macro", mix, 0), ("patch", npatch - 1)],
                             [("restore",)], moves_mix=True))
        out.append(Event("E11-2patch", [("patch", npatch - 1), ("patch", 0)],
                         [("restore",)], moves_mix=True))
        out.append(Event("E11-3moves",
                         [("macro", 0, 0), ("macro", 0, 127),
                          ("patch", npatch - 1)],
                         [("restore",)], moves_mix=True))
    return out


# --------------------------------------------------------------------------
# Rendering


def _build(cls, feed, rate, patch, options, post0=False):
    e = cls(feed.port, sample_rate=rate, **options)
    if patch is not None:
        e.program_change(patch)
    if post0:
        e.program_change(0)
    return e


def _pull(e, out):
    """One host pull, appended as the class handed it. An empty pull adds
    nothing; the caller counts them."""
    data = bytes(audiocore.get_buffer(e.output)[1])
    out.extend(data)
    return len(data)


def _pull_to(e, out, nbytes, fsize):
    """Pull until `out` holds `nbytes`. 64 empty pulls in a row is a source
    that has ended at Mix 0: silence from there, which is what a host
    playing it hears."""
    empties = 0
    while len(out) < nbytes:
        if _pull(e, out) == 0:
            empties += 1
            if empties >= 64:
                out.extend(bytes(nbytes - len(out)))
                return True
        else:
            empties = 0
    return False


def _tail(e):
    t = e.tail_samples
    return t


class Control:
    """A control instance per (kind, material, rate, channels, patch,
    post0), rendered lazily and shared by every cell that needs it."""

    def __init__(self, cls, rate, channels, patch, options, kind, material,
                 post0):
        values = material_for(material, rate, channels)
        self.feed = Feed(values, rate, channels, kind,
                         loop=(material == "loop"))
        self.e = _build(cls, self.feed, rate, patch, options, post0)
        self.out = bytearray()
        self.fsize = 2 * channels
        self.ended = False

    def upto(self, frames):
        nbytes = frames * self.fsize
        if len(self.out) < nbytes and not self.ended:
            self.ended = _pull_to(self.e, self.out, nbytes, self.fsize)
        return self.out

    def close(self):
        self.e.deinit()


_MATERIAL = {}


def material_for(which, rate, channels):
    key = (which, rate, channels)
    if key not in _MATERIAL:
        if which == "loop":
            _MATERIAL[key] = click_noise(2400, channels, spacing=150,
                                         seed=777)
        elif which == "once":
            _MATERIAL[key] = click_noise(8192, channels)
        elif which == "tri":
            _MATERIAL[key] = triangle(8192, channels, rate)
        else:
            raise ValueError(which)
    return _MATERIAL[key]


def _schedule_run(e, feed, ctx, ev, out, fsize, upto_frames, mixfix=None):
    """Pull to `upto_frames`, taking `ev.away` before pull K0 (or before
    the first pull) and `ev.back` `ev.gap` pulls later. Returns the frame
    positions the actions landed at."""
    at = []
    ctx.lats = []
    k0 = 0 if ev.first else K0
    kb = k0 if ev.first else k0 + ev.gap
    k = 0
    nbytes = upto_frames * fsize
    empties = 0
    while len(out) < nbytes:
        if k == k0:
            at.append(len(out) // fsize)
            act(e, feed, ctx, ev.away)
            if mixfix:
                mixfix(e)
            ctx.lats.append(e.latency_samples)
        if k == kb and ev.back:
            if kb != k0:
                at.append(len(out) // fsize)
            act(e, feed, ctx, ev.back)
            if mixfix:
                mixfix(e)
            if kb != k0:
                ctx.lats.append(e.latency_samples)
        if _pull(e, out) == 0:
            empties += 1
            if empties >= 64:
                out.extend(bytes(nbytes - len(out)))
                break
        else:
            empties = 0
        k += 1
    ctx.pulls = k
    return at


# --------------------------------------------------------------------------
# The properties


def p1(cls, ev, rate, channels, patch, options):
    """At Mix 0 the output is the source, byte for byte, on time."""
    mix = mix_index(cls)
    if mix is None:
        return "na"
    if ev.name.startswith("E4-m%d=" % mix) and not ev.name.endswith("=0"):
        return "na"
    if ev.name.startswith("E10-mix"):
        return "na"
    values = material_for("once", rate, channels)
    feed = Feed(values, rate, channels, ev.kind, loop=False)
    e = _build(cls, feed, rate, patch, options, False)
    ctx = Ctx(e, patch)
    fsize = 2 * channels
    if _starts(ev.name, ("E5", "E4-m%d=0" % mix)):
        # The event itself takes Mix to 0: judge the stretch it holds it.
        mixfix = None
        window = None
    else:
        e.set_macro(mix, 0)

        def mixfix(effect):
            effect.set_macro(mix, 0)
        window = "all"
    if ev.name.startswith("E9"):
        # E9's P1 is the baseline: Mix 0 from the start, no move, this
        # source shape.
        ev = Event(ev.name, [], kind=ev.kind)
    out = bytearray()
    total = (K0 + 8 + 8) * BLOCK
    try:
        at = _schedule_run(e, feed, ctx, ev, out, fsize, total, mixfix)
        lat = e.latency_samples
    finally:
        e.deinit()
    expect = bytes(values)
    if ev.kind == "raw":
        total = min(total, len(values) // channels)
    if window == "all":
        lo, hi = 0, total
    else:
        if not at:
            return "na"
        lo = at[0]
        hi = at[1] if len(at) > 1 else total
        if ev.first:
            return "na"
        # Mix 0's own latency, read while the event holds it there.
        lat = ctx.lats[0]
    shifted = bytes(lat * fsize) + expect
    shifted = shifted + bytes(max(0, total * fsize - len(shifted)))
    d = _first_diff(out, shifted, lo * fsize, hi * fsize)
    if d < 0:
        return "ok"
    frame = d // fsize
    if ev.name.startswith("E8-end") and at and frame >= at[0]:
        # The source's frames up to where it ended (it may have handed
        # some past the pull it ended at), then silence.
        if _is_zero(out[d:hi * fsize]):
            return "ok"
    if ev.name.startswith("E8-dry"):
        # A starve may play as silence: zeros inserted, then the source
        # again from where it stopped, with nothing lost or repeated.
        z = frame
        while z < hi and out[z * fsize:(z + 1) * fsize] == bytes(fsize):
            z += 1
        gap = z - frame
        if gap and _first_diff(out[z * fsize:], shifted[frame * fsize:], 0,
                               (hi - z) * fsize) < 0:
            return "ok"
    return "RED(first wrong frame %d%s)" % (frame - lo, _diagnose(
        out, shifted, frame, fsize, hi))


def _diagnose(out, expect, frame, fsize, hi):
    """Where the wrong frame's run came from in the source."""
    want = out[frame * fsize:(frame + 16) * fsize]
    if want == bytes(len(want)):
        return ", silence"
    for off in range(1, 4097):
        for sign in (1, -1):
            src = frame + sign * off
            if src < 0:
                continue
            if expect[src * fsize:(src + 16) * fsize] == want:
                if sign > 0:
                    return ", %d frames of source lost" % off
                return ", %d frames of source repeated" % off
    return ", not the source near there"


def _decl(cls, ev, prop):
    for (name, prefix, p), reason in DECLARED.items():
        if name == cls.NAME and p == prop and ev.name.startswith(prefix):
            return True
    return False


def main_render(cls, ev, rate, channels, patch, options, controls):
    """P2, P3, P4 from one instance, against a shared control."""
    fsize = 2 * channels
    res = {}
    values = material_for("loop", rate, channels)
    feed = Feed(values, rate, channels, ev.kind, loop=True)
    e = _build(cls, feed, rate, patch, options, False)
    ctx = Ctx(e, patch)
    ctx.cls = cls
    ctx.options = options
    # The control is rendered in step with the instance, pull for pull,
    # and compared as it goes: nothing tail-long is kept.
    cfeed = Feed(values, rate, channels, ev.kind, loop=True)
    c = _build(cls, cfeed, rate, patch, options, ev.post0)
    try:
        out = bytearray()
        at = _schedule_run(e, feed, ctx, ev, out, fsize,
                           ((0 if ev.first else K0) + ev.gap + 1) * BLOCK)
        cout = bytearray()
        for k in range(ctx.pulls):
            if k == K0 and ev.name.startswith("E8-end"):
                # The control's source goes silent where the instance's
                # ended, and stays silent.
                cfeed.point(cfeed.sil)
            _pull(c, cout)
        last = at[-1] if at else 0
        tail = _tail(e)
        lat = e.latency_samples
        if tail is None:
            res["P4"] = "na(tail None)"
            bound = last + BLOCK + lat
        else:
            bound = last + tail + lat + BLOCK
        stop = bound + MARGIN
        verdict, crc, s0 = _p4_stream(e, c, out, cout, last, bound, stop,
                                      fsize, ev.name.startswith("E8-dry"))
        if "P4" not in res:
            res["P4"] = verdict
        out = None
        # P2: silence in, silence out after the tail.
        feed.point(feed.sil)
        tail = _tail(e)
        if ev.kind == "raw":
            # A whole RawSample is one buffer the class may still be
            # playing through: the input is not silent until it has.
            res["P2"] = "na(whole RawSample)"
            wait = (tail or NO_TAIL_WAIT) + lat + BLOCK + MARGIN
        elif tail is None:
            res["P2"] = "na(tail None)"
            wait = NO_TAIL_WAIT
        else:
            # Silence starts once the class has used the source buffer it
            # was handed last.
            b2 = s0 + tail + lat + BLOCK + int(ev.kind)
            # Streamed: only the frames P2 reads are kept.
            crc, left = _stream(e, (b2 - s0) * fsize, crc)
            out = bytearray(left)
            _pull_to(e, out, MARGIN * fsize, fsize)
            out = out[:MARGIN * fsize]
            crc = binascii.crc32(bytes(out), crc)
            res["P2"] = _zero_after(out, 0, MARGIN, fsize, s0 - b2)
            wait = tail + lat + BLOCK + MARGIN
        res["h"] = "%08x" % (crc & 0xFFFFFFFF)
        # P3: an event during silence plays nothing. Not for a whole
        # RawSample, whose one buffer the class may hold part of.
        if ev.kind == "raw":
            res["P3"] = "na(whole RawSample)"
        else:
            res["P3"] = _p3(e, feed, ctx, ev, fsize, wait)
    finally:
        e.deinit()
        c.deinit()
    return res


def _pull_some(x, fsize):
    """One pull that hands back bytes: 64 empty pulls in a row are a block
    of silence."""
    for _ in range(64):
        data = bytes(audiocore.get_buffer(x.output)[1])
        if data:
            return data
    return bytes(BLOCK * fsize)


def _p4_stream(e, c, out, cout, last, bound, stop, fsize, shifted):
    """P4, streamed: the instance's and the control's bytes compared as
    they are pulled, from the last move to `stop`. Returns the verdict,
    the CRC of every byte the instance handed, and its frame count."""
    crc = binascii.crc32(bytes(out))
    base = 0
    lo = last * fsize
    hi = stop * fsize
    lastdiff = -1
    win_e = bytearray()
    win_c = bytearray()
    lo_e = bound * fsize
    lo_c = (bound - BLOCK) * fsize
    while base < hi:
        if not out:
            data = _pull_some(e, fsize)
            crc = binascii.crc32(data, crc)
            out = bytearray(data)
        if not cout:
            cout = bytearray(_pull_some(c, fsize))
        n = min(len(out), len(cout), hi - base)
        a = out[:n]
        b = cout[:n]
        if base + n > lo and a != b:
            d = _last_diff(a, b, max(0, lo - base), n)
            if d >= 0:
                lastdiff = base + d
        if shifted:
            if base + n > lo_e:
                win_e.extend(a[max(0, lo_e - base):])
            if base + n > lo_c:
                win_c.extend(b[max(0, lo_c - base):])
        out = out[n:]
        cout = cout[n:]
        base += n
    s0 = (base + len(out)) // fsize
    if lastdiff < 0 or lastdiff // fsize < bound:
        return "ok", crc, s0
    if shifted:
        for s in range(1, BLOCK + 1):
            off = (BLOCK - s) * fsize
            if win_c[off:off + len(win_e)] == win_e:
                return "ok(shift %d)" % s, crc, s0
    return ("RED(differs at +%d, bound +%d)" % (lastdiff // fsize - last,
                                               bound - last), crc, s0)


def _stream(e, nbytes, crc):
    """Pull `nbytes` without keeping them, folded into `crc`. Returns the
    crc and the bytes the last pull handed past `nbytes`."""
    got = 0
    empties = 0
    while got < nbytes:
        data = bytes(audiocore.get_buffer(e.output)[1])
        if not data:
            empties += 1
            if empties >= 64:
                data = bytes(nbytes - got)
            else:
                continue
        empties = 0
        take = min(len(data), nbytes - got)
        crc = binascii.crc32(data[:take], crc)
        got += take
        if take < len(data):
            return crc, data[take:]
    return crc, b""


def _zero_after(out, lo, hi, fsize, s0):
    seg = out[lo * fsize:hi * fsize]
    if _is_zero(seg):
        return "ok"
    vals = _samples(seg)
    top = 0
    first = -1
    for i in range(len(vals)):
        v = vals[i]
        if v:
            if first < 0:
                first = i
            if v < 0:
                v = -v
            if v > top:
                top = v
    return "RED(peak %d at +%d after input end, bound +%d)" % (
        top, lo - s0 + first // (fsize // 2), lo - s0)


def _p3(e, feed, ctx, ev, fsize, wait):
    """Ring on the material, take the move away as the input stops, wait
    for the output to reach exact silence, take the move back: the four
    blocks after it are exactly zero. A single action is taken in the
    silence instead."""
    out = bytearray()
    if ev.first:
        if not ev.back:
            return "na"
        # The first-pull variant: the move away before anything is pulled,
        # a fresh instance, the material through it, then silence.
        e = _build(ctx.cls, feed, feed.rate, ctx.patch, ctx.options, False)
        ctx = Ctx(e, ctx.patch)
        act(e, feed, ctx, ev.away)
    feed.point(feed.mat)
    try:
        return _p3_body(e, feed, ctx, ev, fsize, wait, out)
    finally:
        if ev.first:
            e.deinit()


def _p3_body(e, feed, ctx, ev, fsize, wait, out):
    _pull_to(e, out, 8 * BLOCK * fsize, fsize)
    feed.point(feed.sil)
    if ev.back and not ev.first:
        act(e, feed, ctx, ev.away)
    blk = BLOCK * fsize
    # Wait the whole tail, not only for a quiet stretch: a delay is quiet
    # between the input and its first repeat.
    tail = _tail(e)
    hold = BLOCK if ev.kind == "raw" else int(ev.kind)
    if tail is None:
        need = max(wait, NO_TAIL_WAIT)
    else:
        need = max(wait, tail + e.latency_samples + BLOCK + hold + MARGIN)
    _crc, left = _stream(e, (need - 8 * BLOCK) * fsize, 0)
    seg = bytearray(left)
    _pull_to(e, seg, 8 * blk, fsize)
    if not _is_zero(seg):
        return "na(never silent)"
    if ev.back:
        act(e, feed, ctx, ev.back)
    else:
        act(e, feed, ctx, ev.away)
    seg = bytearray()
    _pull_to(e, seg, 4 * blk, fsize)
    if _is_zero(seg):
        return "ok"
    vals = _samples(seg)
    top = 0
    first = -1
    for i in range(len(vals)):
        v = vals[i]
        if v:
            if first < 0:
                first = i
            if v < 0:
                v = -v
            if v > top:
                top = v
    return "RED(peak %d from silence, first at +%d)" % (
        top, first // (fsize // 2))


def p5(cls, ev, rate, channels, patch, options, controls):
    """No step at the move larger than 1.5 x the larger of the material's
    and the control's own largest step, on a triangle."""
    if not ev.control_move or ev.first:
        return "na"
    fsize = 2 * channels
    values = material_for("tri", rate, channels)
    key = ("tri", ev.kind, rate, channels, patch)
    ctl = controls.get(key)
    if ctl is None:
        ctl = Control(cls, rate, channels, patch, options, ev.kind, "tri",
                      False)
        controls[key] = ctl
    total = (K0 + ev.gap + 6) * BLOCK
    feed = Feed(values, rate, channels, ev.kind, loop=False)
    e = _build(cls, feed, rate, patch, options, False)
    ctx = Ctx(e, patch)
    out = bytearray()
    try:
        at = _schedule_run(e, feed, ctx, ev, out, fsize, total)
    finally:
        e.deinit()
    ref = _samples(bytes(ctl.upto(total)[:total * fsize]))
    got = _samples(bytes(out[:total * fsize]))
    own = _max_step(values, channels, 0, total)
    base = max(own, _max_step(ref, channels, 0, total))
    limit = base * STEP_NUM // STEP_DEN
    worst = 0
    where = 0
    for a in at:
        lo = max(0, a - 1)
        hi = min(total, a + BLOCK + 64)
        s = _max_step(got, channels, lo, hi)
        if s > worst:
            worst = s
            where = a
    if worst <= limit:
        return "ok"
    return "RED(step %d at %d, limit %d)" % (worst, where, limit)


def e3(cls, rate, channels, patch, options):
    """deinit(): the source still renders, the surface raises, a second
    deinit is harmless."""
    fsize = 2 * channels
    values = material_for("loop", rate, channels)
    feed = Feed(values, rate, channels, "256", loop=True)
    e = _build(cls, feed, rate, patch, options, False)
    out = bytearray()
    _pull_to(e, out, K0 * BLOCK * fsize, fsize)
    e.deinit()
    res = {}
    try:
        got = bytes(audiocore.get_buffer(feed.port)[1])
        res["P1"] = "ok" if len(got) == BLOCK * fsize else (
            "RED(source handed %d bytes)" % len(got))
    except Exception as err:                        # noqa: BLE001
        res["P1"] = "RED(source: %s)" % type(err).__name__
    quiet = []
    for name in sorted(dir(type(e))):
        if name.startswith("_") or name.upper() == name or name in (
                "deinit", "create"):
            continue
        try:
            value = getattr(e, name)
            if callable(value):
                args = {"set_macro": (0, 64), "get_macro": (0,),
                        "program_change": (0,), "macro": (0,),
                        "pitch_bend": (8192,), "control_change": (1, 64),
                        "channel_pressure": (64,),
                        "poly_pressure": (60, 64)}.get(name, ())
                value(*args)
            quiet.append(name)
        except Exception:                           # noqa: BLE001
            pass
    try:
        e.deinit()
        second = ""
    except Exception as err:                        # noqa: BLE001
        second = "; second deinit raised %s" % type(err).__name__
    if quiet or second:
        res["PD"] = "RED(no raise after deinit: %s%s)" % (
            ",".join(quiet), second)
    else:
        res["PD"] = "ok"
    return res


PROPS = ("P1", "P2", "P3", "P4", "P5")


def run_cell(cls, ev, rate, channels, patch, options, controls):
    res = {}
    res["P1"] = p1(cls, ev, rate, channels, patch, options)
    res.update(main_render(cls, ev, rate, channels, patch, options,
                           controls))
    res["P5"] = p5(cls, ev, rate, channels, patch, options, controls)
    for prop in PROPS:
        if res[prop].startswith("RED") and _decl(cls, ev, prop):
            res[prop] = "decl"
    return res


def fmt(name, event, rate, channels, patch, res):
    parts = [name, event, str(rate), str(channels),
             "d" if patch is None else str(patch)]
    for prop in sorted(res):
        parts.append("%s:%s" % (prop, res[prop]))
    return "|".join(parts)


def run_class(cls, options=None, rates=RATES, channels=CHANNELS,
              patches=None, only=None, quick=False, emit=print, name=None):
    """Run the matrix on `cls`, emitting one line per cell and a summary
    line last. Returns (cells, red, declared)."""
    options = options or {}
    name = name or cls.NAME
    if patches is None:
        patches = [None] + sorted(cls.PATCHES)
    cells = red = decl = 0
    for rate in rates:
        for ch in channels:
            for patch in patches:
                controls = {}
                try:
                    if only is None or "E3" in only:
                        res = e3(cls, rate, ch, patch, options)
                        line = fmt(name, "E3-deinit", rate, ch, patch, res)
                        emit(line)
                        cells += 1
                        red += 1 if "RED" in line else 0
                    for ev in events(cls, patch, quick):
                        if only is not None and ev.name.split("-")[0] \
                                not in only:
                            continue
                        res = run_cell(cls, ev, rate, ch, patch, options,
                                       controls)
                        line = fmt(name, ev.name, rate, ch, patch, res)
                        emit(line)
                        cells += 1
                        red += 1 if "RED" in line else 0
                        decl += line.count(":decl")
                finally:
                    for ctl in controls.values():
                        ctl.close()
    emit("SUMMARY|%s|cells %d|red %d|declared %d" % (name, cells, red, decl))
    return cells, red, decl


# --------------------------------------------------------------------------
# Planted faults: the matrix's proof that each property can fail.
#
# `Plain` is the control for P1, P2, P4, P5 and PD: one mixer voice whose
# level is the dry/wet law (Mix 0 is level 1.0, the source bit for bit;
# Mix 1 is the Gain macro's level), so nothing is ever routed around.
# `Routed` is the control for P3: Mix 0 routes around to the source and the
# way back rejoins and re-arms, the house pattern. Each plant breaks exactly
# one thing.

_COMPONENT = _component.Component if _component is not None else object


class Plain(_COMPONENT):
    NAME = "LifecyclePlain"
    TIER = "audiodsp" if _component is None else _component.AUDIODSP
    REQUIRES = ("audioroute",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0
    MACRO_LABELS = ("Mix", "Gain")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0), (0.0, 1.0))
    PATCHES = {0: ("Unity", (127, 127)), 1: ("Soft", (127, 96))}

    def _build(self, mix=1.0, gain=1.0, patch=None):
        pcm = self._pcm(BLOCK * self._channel_count * 2)
        self._mixer = self._own(audiomixer.Mixer(voice_count=2, **pcm))
        self._dc = _raw(array("h", bytes(4 * self._channel_count)),
                        self._sample_rate, self._channel_count)
        self._arm()
        self._output = self._mixer
        self._macros = [mix, gain]
        self._init_macros((mix, gain), patch)

    def _arm(self):
        self._mixer.voice[0].play(self._source, loop=True)
        self._mixer.voice[1].play(self._dc, loop=True)

    def _level(self):
        mix = self._macros[0]
        return 1.0 - mix + mix * self._macros[1]

    def _apply_macro(self, index, position):
        self._mixer.voice[0].level = self._level()


class Routed(Plain):
    """Mix 0 routes around a 5 ms echo line to the source; the way back
    rejoins, clearing the line, and re-arms."""
    NAME = "LifecycleRouted"
    REQUIRES = ("audioroute",)
    TAIL_SAMPLES = 512

    def _build(self, mix=1.0, gain=1.0, patch=None):
        import audiodelays
        pcm = self._pcm(BLOCK * self._channel_count * 2)
        self._echo = self._own(audiodelays.Echo(
            max_delay_ms=10, delay_ms=5, decay=0.0, mix=1.0, **pcm))
        Plain._build(self, mix, gain, patch)

    def _arm(self):
        self._echo.play(self._source, loop=True)
        self._mixer.voice[0].play(self._echo, loop=True)
        self._mixer.voice[1].play(self._dc, loop=True)

    def _apply_macro(self, index, position):
        if index == 0 and position == 0.0:
            self._route_around(self._source)
            return
        if index == 0:
            if self._rejoin():
                self._arm()
            self._output = self._mixer
        self._mixer.voice[0].level = self._macros[1]


class DropOnReset(Plain):
    """P1: reset() swallows one block of the borrowed source."""

    def reset(self):
        Plain.reset(self)
        audiocore.get_buffer(self._source)


class HoldDC(Plain):
    """P2: after a reset the output sits on a DC offset for ever."""

    def reset(self):
        Plain.reset(self)
        ch = self._channel_count
        self._dc_on = _raw(array("h", [9] * (2 * ch)), self._sample_rate, ch)
        self._mixer.voice[1].play(self._dc_on, loop=True)


class StaleMix(Routed):
    """P3: Mix back from 0 takes the graph back untouched, so the echo line
    plays what it held out of silence (stale_blocks.StaleRejoin)."""

    def _rejoin(self, keep=()):
        self._stranded = False
        return False


class LateMove(Plain):
    """P4: a move is answered one move late, so away-and-back leaves the
    class where it went."""

    def _apply_macro(self, index, position):
        late = getattr(self, "_late", None)
        self._late = self._level()
        self._mixer.voice[0].level = self._late if late is None else late


class HardSwitch(Plain):
    """P5: Mix below half re-points the output to a primed silent mixer,
    mid-waveform, a hard switch."""

    def _build(self, mix=1.0, gain=1.0, patch=None):
        pcm = self._pcm(BLOCK * self._channel_count * 2)
        self._quiet = self._own(audiomixer.Mixer(voice_count=1, **pcm))
        self._quiet.voice[0].level = 0.0
        Plain._build(self, mix, gain, patch)

    def _arm(self):
        Plain._arm(self)
        self._quiet.voice[0].play(self._dc, loop=True)

    def _apply_macro(self, index, position):
        Plain._apply_macro(self, index, position)
        if self._constructing:
            return
        self._output = self._quiet if self._macros[0] < 0.5 else self._mixer


class ImplPlant(Plain):
    """P6: the level is a hair different off CPython, so the bytes differ
    between interpreters while every verdict stays the same."""

    def _level(self):
        level = Plain._level(self)
        if sys.implementation.name != "cpython":
            level = level * 0.99
        return level


class BusyDeinit(Plain):
    """PD: tail_samples still answers after deinit."""

    @property
    def tail_samples(self):
        return 0


PLANTS = {"plain": Plain, "routed": Routed, "droponreset": DropOnReset,
          "holddc": HoldDC,
          "stalemix": StaleMix, "latemove": LateMove,
          "hardswitch": HardSwitch, "busydeinit": BusyDeinit,
          "implplant": ImplPlant}


def _cli(argv):
    only = None
    quick = False
    names = []
    for arg in argv:
        if arg.startswith("--events="):
            only = arg.split("=", 1)[1].split(",")
        elif arg == "--quick":
            quick = True
        else:
            names.append(arg)
    for name in names:
        if name in PLANTS:
            cls = PLANTS[name]
        else:
            from audioeffects import rebuilt
            cls = rebuilt.module_class(name)
            if cls is None:
                print("MISSING|%s" % name)
                continue
        run_class(cls, only=only, quick=quick, name=name if name in PLANTS
                  else None)
    print("DONE")


if __name__ == "__main__":
    # Run as the module `lifecycle`, not `__main__`: `_component` reads
    # VENDOR off the module a planted class is defined in.
    sys.path.insert(0, "tests/support")
    import lifecycle
    lifecycle._cli(sys.argv[1:])
