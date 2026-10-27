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
    ("Saturation", "ceiling", "sine/48000/2/all=127"):
        "every macro at its top is Output +12 dB on a 0 dBFS input, which"
        " the docstring says can clip at the rails",
    ("Saturation", "ceiling", "noise/48000/2/all=127"):
        "every macro at its top is Output +12 dB on a 0 dBFS input, which"
        " the docstring says can clip at the rails",
    ("Saturation", "ceiling", "sine/48000/2/m1=127"):
        "Output +12 dB on a 0 dBFS input, which the docstring says can"
        " clip at the rails",
    ("Saturation", "ceiling", "sine/48000/2/lv=127+m1=127"):
        "Output +12 dB on a 0 dBFS input, which the docstring says can"
        " clip at the rails",
    ("Octaver", "ceiling", "clicks/"):
        "with Direct at 0 only the octaves sound, and one-sample clicks"
        " through the clock's low-pass stay under Sensitivity, where the"
        " octaves are silent by design (trait T3 b)",
    ("Bitcrusher", "levels", "-24/48000/2/p6"):
        "Broken Converter keeps about 4 bits, a step of 4096 LSB, and a"
        " phrase peaking at 2068 (-24 dBFS) is under one step: a bit crusher"
        " silences it by design",
    ("Bitcrusher", "levels", "-24/22050/1/p6"):
        "Broken Converter keeps about 4 bits, a step of 4096 LSB, and a"
        " phrase peaking at 2068 (-24 dBFS) is under one step: a bit crusher"
        " silences it by design",
    ("Rack", "levels", ""):
        "ConvolutionReverb ends the probe chain and rails at its defaults"
        " whatever the level (its own ceiling cell, see Rack's ceiling row):"
        " a finding for that class, not a rack defect",
}

# Four classes rail on the plucked phrase at -3 dBFS on the patches that
# gain by design (a ringing comb, a resonant or driven ladder, an attack
# boost, a long hall), and say so in their docstrings with the level the
# phrase is clean to on every patch (audiocomponents#192). Chorus states
# `INPUT_CEILING_DBFS` instead and is held to it.
for _name, _patches, _why in (
        ("CombFilter", (1, 3, 4, 5),
         "the comb adds its line to the dry and gains 1/(1-Feedback) at its"
         " peaks"),
        ("LadderFilter", (4,),
         "the resonance peak and the drive gain by design"),
        ("TransientShaper", (1, 5),
         "Attack adds gain on the hit by design"),
        ("Reverb", (9,),
         "the tank's lines clamp at the rail and Slow Bloom builds the"
         " longest")):
    for _rate in RATES:
        for _ch in CHANNELS:
            for _patch in _patches:
                DECLARED[(_name, "levels", "-3/%d/%d/p%d" % (
                    _rate, _ch, _patch))] = (
                    "rails on the plucked phrase at -3 dBFS by design: %s;"
                    " the docstring gives the level it is clean to"
                    " (audiocomponents#192)" % _why)

# MultiTapDelay on CircuitPython: its audiodelays.MultiTapDelay is
# upstream's own, whose reset_buffer keeps the write heads where they were,
# so a Time 0 move after a reset keeps another stretch of the line than on
# a fresh node. audiodsp's node puts them at the top (docs/upstream-diff.md
# there); CPython and MicroPython keep the cells live.
for _ch in CHANNELS:
    for _rate in RATES:
        DECLARED[("MultiTapDelay", "fresh", "reset@8+m0=0/%d/%d/" % (
            _rate, _ch), "circuitpython")] = (
            "CircuitPython's own MultiTapDelay keeps its write heads across"
            " a reset, so a shorter Time after it keeps another stretch of"
            " the line; audiodsp's node resets them")

# The pitch shifters on CircuitPython: its audiodelays.PitchShift is
# upstream's own, whose reset keeps the read and write positions, so a
# reset does not start the splices where a new node starts them
# (audiodsp#240 fixed it in audiodsp's node; each class's docstring says
# so, and the lifecycle matrix declares the same cells there).
for _name in ("Harmonizer", "PitchShifter"):
    DECLARED[(_name, "fresh", "reset@", "circuitpython")] = (
        "CircuitPython's own PitchShift keeps its read and write positions"
        " across a reset, so the splices do not start where a new node's"
        " do; audiodsp's node resets them (audiodsp#240)")
DECLARED[("ShimmerHall", "fresh", "reset@8+m0=0/", "circuitpython")] = (
    "Octave Bloom, then Rise after a reset: CircuitPython's own PitchShift"
    " keeps its read and write positions across the reset (audiodsp#240)")

# Flanger, the stock tier on a node that primes: an
# upstream effect node's `play()` takes its first block from the source at
# once, so a reset before the first pull still holds that block and plays
# it, the source's frames 0 to 255, where a fresh instance built at that
# moment primes the block after. Only another `play()` drops a held block,
# and `play()` resets the host's own source (a RawSample starts again from
# its first frame), so a reset mid-stream would restart the host's audio;
# the stock tier has no port to prime from instead. From the first pull on
# the reset is a fresh instance (`reset@8` is green). Waiting on a ruling.
for _name in ("Flanger",):
    DECLARED[(_name, "fresh", "reset@0/")] = (
        "a stock node primes its first block at play(): a reset before the"
        " first pull plays that block where a fresh build primes the next;"
        " dropping it takes a play(), which resets the host's source")

# Overdrive at patch 6, a patch moved and restored before the first pull:
# without get_buffer the pole charge runs all 64 blocks (`_pull_node` cannot read
# a block back), with it the charge stops at the first zero block, and P4
# reads that residue against the control only with get_buffer. Not audible.
# Since Overdrive builds lazily (Phase 7, lc-1) the same residue reads on
# the other E10 cells that land on a clipped bias before the first pull:
# a reset or a patch change at patch 6, and every macro at 127.
for _cell in ("E10-patch/48000/2/6", "E10-patch/48000/1/6",
              "E10-reset/48000/1/6", "E10-reset/48000/2/6",
              "E10-macros/48000/1/d", "E10-macros/48000/2/d"):
    DECLARED[("Overdrive", "nogb", _cell)] = (
        "the board path charges the pole 64 blocks where the get_buffer"
        " path stops at the first zero block; P4 differs only with"
        " get_buffer")

# The lazy re-arm (`Component._reset_rearmed`) without get_buffer: nothing
# can hand a silent primed block up, so a reset arms the voices from their
# sources, as a build does, and the first block after it is the source's
# own. A second reset, or a patch change, before the next pull finds that
# block already taken through patch 0's graph: the second reset drops it
# and takes the next, the patch change plays it at patch 0. One reset, and
# resets a block apart, match a run with get_buffer. Declared by the
# landing ruling of 2026-10-14.
for _name in ("Distortion", "MultibandCompressor"):
    for _scenario in ("reset-twice", "reset-first-twice", "reset-patch"):
        DECLARED[(_name, "nogb", "bytes-%s/" % _scenario)] = (
            "without get_buffer a reset primes the voices from the source,"
            " as a build does; a second reset or a patch change before the"
            " next pull meets that block already primed")

# DynamicEQ's, MultibandCompressor's and Phaser's input guard (an
# `audiofilters.Filter`) takes the source's first block at `play()`, so the
# source stands at 256 before anything is pulled. A reset before the first
# pull plays the material from frame 0, as a fresh build does
# (tests/test_first_pull.py); the fresh check reads where the source
# stands and expects 256.
for _name in ("DynamicEQ", "MultibandCompressor", "Phaser"):
    DECLARED[(_name, "fresh", "reset@0/")] = (
        "the input node holds the first block from play(), so the source"
        " stands at 256 while a reset before the first pull plays frame 0,"
        " which is a fresh build's frame 0 (test_first_pull)")

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

# A 50 Hz sine deep in a filter's stop band is silence by design: HighPass
# and BandPass with Frequency at its top leave the sine so far down that
# their float state, which writes a word below 1e-20 as exact zero, settles
# to zero. The docstrings say what passes: HighPass "decides where the
# bottom stops", and for BandPass "narrowing the band changes what gets
# through". These are the cells the ceiling check found silent at 48 kHz
# stereo, at every rate and channel count; every other cell stays live.
_STOP_BANDS = {
    "HighPass": ("m0=127", "all=127", "lv=127+m0=127") + tuple(
        "p%d+lv=127+m0=127" % _p for _p in range(6)),
    "BandPass": ("all=127", "p5+lv=127+m0=127"),
}
for _name, _cells in _STOP_BANDS.items():
    for _rate in RATES:
        for _channels in CHANNELS:
            for _cell in _cells:
                DECLARED[(_name, "ceiling", "sine/%d/%d/%s" % (
                    _rate, _channels, _cell))] = (
                    "the 50 Hz sine sits deep in the stop band, where the"
                    " docstring says the filter passes nothing, and its"
                    " float state settles to exact zero: silence by"
                    " design, not a fault")

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


#: The levels the kit's multi-level pass plays real material at, in dBFS.
LEVELS_DBFS = (-24, -12, -3)
#: The phrase's notes, in Hz: A2, E2, D3, G3, B3, E4.
PHRASE_NOTES = (110, 82, 147, 196, 247, 330)
PHRASE_NOTE_MS = 300


def peak_for(dbfs):
    """The int16 peak a level in dBFS stands for."""
    return int(32767 * 10.0 ** (dbfs / 20.0) + 0.5)


def pluck(frames, period, seed, amp=16384, bright=False):
    """One Karplus-Strong string in integers. The loop starts as a string
    plucked a fifth of the way along it (a triangle, so the fundamental
    leads the partials above it as it does on a guitar) with an eighth of
    noise on top for the pick; `bright` starts it as noise alone, which has
    every partial as loud as the fundamental. Every pass the loop averages
    each sample with its neighbour, so the note rings down, high partials
    first. The same bytes on every interpreter."""
    line = [0] * period
    state = seed
    span = 2 * amp + 1
    knee = period // 5
    for i in range(period):
        state = lifecycle._lcg(state)
        hiss = ((state >> 8) % span) - amp
        if bright:
            line[i] = hiss
        else:
            ramp = amp * i // knee if i < knee else \
                amp * (period - i) // (period - knee)
            line[i] = ramp - amp // 2 + hiss // 8
    out = [0] * frames
    i = 0
    for n in range(frames):
        j = i + 1 if i + 1 < period else 0
        out[n] = line[i]
        line[i] = (line[i] + line[j]) >> 1
        i = j
    return out


def phrase(rate, channels, dbfs=-12, seed=2024, bright=False):
    """Real material for the level passes: six plucked strings, one at a
    time, 300 ms each (the last 500 ms), noisy at the attack and decaying
    through every level below their peak, each string stopped by a 10 ms
    fade, 2.0 s in all, each channel its own strings' noise. Scaled so the
    peak is `dbfs`. Integer arithmetic only."""
    note = PHRASE_NOTE_MS * rate // 1000
    fade = 10 * rate // 1000
    count = len(PHRASE_NOTES)
    total = (count - 1) * note + 5 * note // 3
    mix = [[0] * total for _ in range(channels)]
    for ch in range(channels):
        line = mix[ch]
        for k in range(count):
            length = note if k < count - 1 else total - k * note
            ring = pluck(length, rate // PHRASE_NOTES[k],
                         seed + 17 * k + 1000 * ch, bright=bright)
            for n in range(length):
                v = ring[n]
                if n >= length - fade:
                    v = v * (length - n) // fade
                line[k * note + n] = v
    top = 1
    for ch in range(channels):
        for v in mix[ch]:
            if v > top:
                top = v
            elif -v > top:
                top = -v
    peak = peak_for(dbfs)
    values = _blank(total, channels)
    for ch in range(channels):
        line = mix[ch]
        for n in range(total):
            values[n * channels + ch] = line[n] * peak // top
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
    """A class by provider name: a kit plant or a class `audioeffects`
    exports."""
    import kit_planted
    if name in kit_planted.PLANTS:
        return kit_planted.PLANTS[name]
    import audioeffects
    cls = getattr(audioeffects, name, None)
    return cls


# --------------------------------------------------------------------------
# Cells


def declared(name, check, key, impl=None):
    """A row of DECLARED covers the cell. A row with a fourth element names
    the one interpreter (`sys.implementation.name`) it holds on, so the
    cell stays live on the other two."""
    impl = impl or sys.implementation.name
    for row, _reason in DECLARED.items():
        cname, ccheck, prefix = row[:3]
        if len(row) > 3 and row[3] != impl:
            continue
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


def rail_run(out, values, channels, lat=0, hold=0):
    """(longest run of output frames on a rail where the input was not,
    the frame it starts at), over every channel. The input is read
    `lat` frames earlier and, with `hold`, anywhere in the last
    min(lat, hold) frames up to the output's own, where a sample-and-hold
    that reports its whole hold as latency plays an input frame."""
    best = 0
    where = -1
    n = len(out) // channels
    nin = len(values) // channels
    span = min(lat, hold)
    for ch in range(channels):
        run = 0
        for f in range(n):
            y = out[f * channels + ch]
            if y >= RAIL or y <= -RAIL:
                railed = False
                for g in [f - lat] + (list(range(f - span, f + 1))
                                      if span else []):
                    x = values[g * channels + ch] if 0 <= g < nin else 0
                    if x >= RAIL or x <= -RAIL:
                        railed = True
                        break
                if railed:
                    run = 0
                    continue
                run += 1
                if run > best:
                    best = run
                    where = f - run + 1
            else:
                run = 0
    return best, where
