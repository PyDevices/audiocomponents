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
    ("AirSpace", "plants", "T5/"): "the glide plant changes only how a"
    " Time move travels, and the plant check renders at fixed settings, so"
    " it reads as the clean class; the class's T5 tests move Time",
    ("Harmonizer", "plants", "T6a/"):
        "the plant acts only when a Level comes back from off, a move the"
        " plant check never makes; T6's own test shows it red on that move",
    ("Harmonizer", "plants", "T6b/"):
        "the plant acts only when a Level goes off and comes back, a move"
        " the plant check never makes; T6's own test shows it red on that"
        " move",
    ("PitchShifter", "paperwork", "surface-m2"):
        "Mix is BIPOLAR so MIDI 64 is exactly 1 (the dry at unity at the"
        " defaults); the card's section 3 says UNIPOLAR and is superseded"
        " on that point by a recorded ruling",
    ("StereoWidener", "plants", "H3/"):
        "delay_slew acts only while a Delay move walks the read head, and"
        " the kit's render never moves a control; H3's own test shows the"
        " plant red on a move, and no macro or patch sets the slew",
    ("Rack", "plants", "T1/"):
        "T1's faults are the empty rack's identity and its port, which a"
        " render at the probe chain cannot see; the trait test holds them red",
    ("Rack", "plants", "T4/"):
        "T4's faults live in reset() and patch 0, which the plant render"
        " never calls; the trait test holds them red",
    ("Rack", "plants", "T5/"):
        "T5's faults live in deinit() and a failed build, which the plant"
        " render never reaches; the trait test holds them red",
    ("Rack", "plants", "T6/"):
        "T6's faults need a host transport and a tempo change, which the"
        " plant render does not give; the trait test holds them red",
    ("Rack", "ceiling", "sine/48000/2/"):
        "ConvolutionReverb's own ceiling at its defaults: it rails this 0"
        " dBFS sine alone (its own ceiling cell sine/48000/2/d), a finding"
        " for that class and not a rack defect",
    ("Octaver", "ceiling", "clicks/"):
        "with Direct at 0 only the octaves sound, and one-sample clicks"
        " through the clock's low-pass stay under Sensitivity, where the"
        " octaves are silent by design (trait T3 b)",
}

# PitchShifter at Feedback's top: the repeats stack on the dry, up to 21
# times the input's peak on a DC, so the rail is reachable below any useful
# ceiling. The docstring says so ("Feedback stacks level too, far past the
# input: at Feedback 127, Delay 0 and Mix 2 a noise burst peaking at
# -10.3 dBFS reaches the rail at unison or an octave up, and comes within
# 4 dB of it at an octave down or a fourth or fifth either way"), and
# test_feedback_near_its_top_stacks_level_far_past_the_input holds it at each
# Pitch named. Every material (the square, sine and DC, and the squares at
# the wider periods) and each combination that puts Feedback at 127 (alone,
# with the levels at 127, and with every macro at 127), at every rate and
# channel count; the cells with Feedback below its top stay live.
for _material in ("square", "sine", "dc", "sq41", "sq55", "sq82", "sq110",
                  "sq147"):
    for _rate in RATES:
        for _channels in CHANNELS:
            for _cell in ("m4=127", "lv=127+m4=127", "all=127"):
                DECLARED[("PitchShifter", "ceiling", "%s/%d/%d/%s" % (
                    _material, _rate, _channels, _cell))] = (
                    "Feedback 0.95 stacks repeats on the dry, up to 21"
                    " times the input's peak: the class docstring says"
                    " Feedback stacks level far past the input, a -10.3"
                    " dBFS noise burst reaching the rail at Feedback 127,"
                    " Delay 0 and Mix 2 (test_feedback_near_its_top_stacks_"
                    "level_far_past_the_input)")

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
