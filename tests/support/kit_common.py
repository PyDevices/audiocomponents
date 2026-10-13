"""What the effects kit's checks share: material, rendering, the printed
cell and the table of declared exceptions.

Numpy-free, like `lifecycle.py`, so every render check runs unchanged on
CPython, MicroPython and CircuitPython and the three can be held to the
same printed lines. `KIT.md` beside this file says what each check
measures.
"""

import sys
import binascii

try:
    from array import array
except ImportError:                                   # pragma: no cover
    array = None

import audiocore

import lifecycle

BLOCK = lifecycle.BLOCK
RATES = lifecycle.RATES
CHANNELS = lifecycle.CHANNELS
RAIL = 32767

#: Where a class cannot satisfy a kit cell by design, it says so HERE, one
#: row per (class NAME, check, cell key prefix): reason. A matching RED
#: cell prints `decl` and is counted as a declared exception. Nothing else
#: skips a cell.
DECLARED = {
    ("StereoWidener", "plants", "H3/"):
        "delay_slew acts only while a Delay move walks the read head, and"
        " the kit's render never moves a control; H3's own test shows the"
        " plant red on a move, and no macro or patch sets the slew",
}

CPYTHON = sys.implementation.name == "cpython"


# --------------------------------------------------------------------------
# Material: integer arithmetic only, so every interpreter makes the same
# bytes.


def _blank(frames, channels):
    return array("h", bytes(2 * frames * channels))


def noise(frames, channels, amp, seed=4242):
    """LCG noise in [-amp, amp], each channel its own."""
    values = _blank(frames, channels)
    state = seed
    span = 2 * amp + 1
    for i in range(frames * channels):
        state = lifecycle._lcg(state)
        values[i] = ((state >> 8) % span) - amp
    return values


def dc(frames, channels, level, start=0):
    """Zero until `start`, then `level` held."""
    values = _blank(frames, channels)
    for i in range(start * channels, frames * channels):
        values[i] = level
    return values


def square(frames, channels, amp, period):
    values = _blank(frames, channels)
    half = period // 2
    for frame in range(frames):
        v = amp if (frame % period) < half else -amp
        for ch in range(channels):
            values[frame * channels + ch] = v
    return values


def sine(frames, channels, amp, period):
    """A parabolic sine: each half period is 4 amp q (h - q) / h^2, so the
    peak is `amp` and the bytes are the same everywhere."""
    values = _blank(frames, channels)
    half = period // 2
    hh = half * half
    for frame in range(frames):
        p = frame % period
        q = p % half
        v = 4 * amp * q * (half - q) // hh
        if p >= half:
            v = -v
        for ch in range(channels):
            values[frame * channels + ch] = v
    return values


def clicks(frames, channels, amp, spacing=97):
    """One-sample clicks every `spacing` frames, alternating in sign."""
    values = _blank(frames, channels)
    sign = 1
    for frame in range(3, frames, spacing):
        for ch in range(channels):
            values[frame * channels + ch] = sign * amp
        sign = -sign
    return values


def last_nonzero_frame(values, channels):
    """One past the last frame with a non-zero sample, or 0."""
    for i in range(len(values) - 1, -1, -1):
        if values[i]:
            return i // channels + 1
    return 0


def feed(values, rate, channels):
    """The material in 256-frame blocks, then silence for ever, behind a
    Port (lifecycle's Feed)."""
    return lifecycle.Feed(values, rate, channels, "256", loop=False)


# --------------------------------------------------------------------------
# Rendering


def pull(e):
    """One block from `e.output`; 64 empty pulls in a row are a block of
    silence (a source that has ended)."""
    for _ in range(64):
        data = bytes(audiocore.get_buffer(e.output)[1])
        if data:
            return data
    fsize = 2 * e.channel_count
    return bytes(BLOCK * fsize)


def render(e, frames, actions=None):
    """`frames` frames of `e.output` as bytes. `actions` maps a pull index
    to a callable taken before that pull."""
    fsize = 2 * e.channel_count
    out = bytearray()
    k = 0
    while len(out) < frames * fsize:
        if actions and k in actions:
            actions[k](e)
        out.extend(pull(e))
        k += 1
    return bytes(out[:frames * fsize])


class Stream:
    """Pulls without keeping the bytes: the CRC of everything handed, the
    frame count, and one past the last frame holding a non-zero sample."""

    def __init__(self, e):
        self.e = e
        self.fsize = 2 * e.channel_count
        self.frames = 0
        self.last = 0
        self.nonzero = False
        self.crc = 0
        self.pulls = 0

    def step(self):
        data = pull(self.e)
        self.crc = binascii.crc32(data, self.crc)
        n = len(data) // self.fsize
        if not lifecycle._is_zero(data):
            d = lifecycle._last_diff(data, bytes(len(data)), 0, len(data))
            self.last = self.frames + d // self.fsize + 1
            self.nonzero = True
        self.frames += n
        self.pulls += 1
        return data

    def to(self, frames):
        while self.frames < frames:
            self.step()


def crc_value(data, seed=0):
    return binascii.crc32(data, seed)


def crc(data, seed=0):
    return "%08x" % (binascii.crc32(data, seed) & 0xFFFFFFFF)


def samples(data):
    return lifecycle._samples(data)


def num(x):
    """A number as every interpreter prints it."""
    if isinstance(x, float):
        return "%.6g" % x
    return str(x)


def finite(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return False
    return x == x and x not in (float("inf"), float("-inf"))


# --------------------------------------------------------------------------
# The class under test


def build(cls, port, rate, patch=None, options=None):
    e = cls(port, sample_rate=rate, **(options or {}))
    if patch is not None:
        e.program_change(patch)
    return e


def patches(cls):
    return [None] + sorted(cls.PATCHES)


def pname(patch):
    return "d" if patch is None else "p%d" % patch


def stops(cls, index):
    return lifecycle.stops(cls, index)


def knob_positions(cls):
    """(index, value) for each macro at each of its stops, 64 included for
    a bipolar macro."""
    out = []
    for i in range(len(cls.MACRO_LABELS)):
        for v in stops(cls, i):
            out.append((i, v))
    return out


def resolve(name):
    """A class by provider name: a kit plant, a rebuilt class, or a class
    `audioeffects` exports."""
    import kit_planted
    if name in kit_planted.PLANTS:
        return kit_planted.PLANTS[name]
    from audioeffects import rebuilt
    cls = rebuilt.module_class(name)
    if cls is None:
        import audioeffects
        cls = getattr(audioeffects, name, None)
    return cls


# --------------------------------------------------------------------------
# Cells


def declared(name, check, key):
    for (cname, ccheck, prefix), _reason in DECLARED.items():
        if cname == name and ccheck == check and key.startswith(prefix):
            return True
    return False


class Cells:
    """Emits `name|check|key|V:verdict[|h:digest]` per cell and a SUMMARY
    line per check, counting red, declared and na cells."""

    def __init__(self, name, check, emit=print):
        self.name = name
        self.check = check
        self.emit = emit
        self.cells = self.red = self.decl = self.na = 0
        self.lines = []

    def cell(self, key, verdict, digest=None):
        verdict = verdict.replace("|", "/")
        if verdict.startswith("RED") and declared(self.name, self.check,
                                                  key):
            verdict = "decl"
        line = "%s|%s|%s|V:%s" % (self.name, self.check, key, verdict)
        if digest is not None:
            line += "|h:%s" % digest
        self.cells += 1
        if verdict.startswith("RED"):
            self.red += 1
        elif verdict == "decl":
            self.decl += 1
        elif verdict.startswith("na"):
            self.na += 1
        self.lines.append(line)
        self.emit(line)

    def summary(self):
        self.emit("SUMMARY|%s|%s|cells %d|red %d|declared %d|na %d" % (
            self.name, self.check, self.cells, self.red, self.decl,
            self.na))
        return self.red


def parse(lines):
    """{(name, check, key): {"V": verdict, "h": digest}} from printed
    lines."""
    out = {}
    for line in lines:
        parts = line.split("|")
        if len(parts) < 4 or parts[0] in ("SUMMARY", "DONE", "SKIP"):
            continue
        props = {}
        for p in parts[3:]:
            k, _sep, v = p.partition(":")
            props[k] = v
        out[(parts[0], parts[1], parts[2])] = props
    return out


# --------------------------------------------------------------------------
# Judging samples

#: The longest run of frames a channel may sit on a rail (|y| >= 32767)
#: where the input, `latency_samples` earlier, did not.
RAIL_RUN = 8


def rail_run(out, values, channels, lat=0):
    """(longest run of output frames on a rail where the input was not,
    the frame it starts at), over every channel."""
    best = 0
    where = -1
    n = len(out) // channels
    nin = len(values) // channels
    for ch in range(channels):
        run = 0
        for f in range(n):
            y = out[f * channels + ch]
            if y >= RAIL or y <= -RAIL:
                g = f - lat
                x = values[g * channels + ch] if 0 <= g < nin else 0
                if x >= RAIL or x <= -RAIL:
                    run = 0
                    continue
                run += 1
                if run > best:
                    best = run
                    where = f - run + 1
            else:
                run = 0
    return best, where
