"""`ConvolutionReverb` - a room made by convolution, synthesized or loaded.

Rebuilt from scratch for Phase 5 against
`workspace docs/effects-internal/dossiers/ConvolutionReverb.md`, whose trait
table was frozen at Station A before this file existed (anchor commit
85cc2bfc9a5a3c34c6906fbf0c27b285ba1050d2, the Station A critique's
re-freeze, 2026-09-28). The old class in `reverb.py` is consulted only for
the six defects that dossier's section 7 names; it stays the class the
library serves until the board runner adopts this one. The dossier's dated
post-build revisions (2026-09-28) record what each audit round changed in
the words and tests; the audio did not change in any of them. Since the
re-audit at audiodsp v0.6.3rc2 the class stands on the fixed convolution
node (audiodsp#165): a room-knob move no longer drops the block in flight
or stops the tail (#163), and each side of a stereo room is normalised on
its own, so the room no longer leans (#164). The two sentences that
disclosed those defects are gone, and every stereo figure below was read
again on the fixed node.

**What it sounds like.** A short room behind your dry signal. With nothing
loaded the class synthesizes the room: noise under an exponential that
reaches -60 dB at the Decay time, a one-pole Damping roll-off on the tail,
a Predelay of silence before it, a Diffusion fade-in so it does not start
as a burst, and Room picks one of 64 noise seeds (two seeds are two rooms
of one size). Mix runs 0 to 2: dry at unity up to 1, the room alone at 2.
Hand it an impulse (`impulse=`, a bytes-like of int16 frames or a path to
a 16-bit PCM WAV at the graph's rate) and the room is that recording, and
only Mix is live.

**The allocation.** `seconds` (default **0.08 s**) is how long a room this
instance can ever hold, carved once at construction: 256-frame partitions,
`ceil(round(seconds * fs) / 256)` of them, from a floor of **0.06 s** to a
ceiling of **512 partitions = 131 072 taps**, which is 2.730 s at 48 kHz,
2.972 s at 44.1 kHz and 5.944 s at 22.05 kHz. Outside those, construction
raises `ValueError` naming this class, the taps, the rate and the limit.
On a desktop the product is taken in double precision and `round` sends a
half frame to even, so a `seconds` a hair over half a frame past a
partition edge builds one partition fewer than exact arithmetic would:
0.08001041666666667 s at 48 kHz is 3 840.5 + 7/2^48 frames exactly, and
builds 3 840 taps, not 4 096. No floor or ceiling cell moves. A board's
float is single precision, and there a few `seconds` land on the other
side of a partition edge: in a single-precision emulation (not a board
run) 0.685 s at 44.1 kHz and 1.370 s at 22.05 kHz build 118 partitions
where a desktop builds 119. No floor, ceiling or default cell moves.
Decay, Predelay and Diffusion are laws over what the allocation leaves
(section 6): Decay is the T60, log from the node's 50 ms floor to
`seconds - predelay`, so at its top the room reaches -60 dB exactly at the
allocation's end; Predelay runs to `min(200 ms, (seconds - 50 ms) / 2)`;
Diffusion to `min(500 ms, T60 / 4)`.

**Which allocations are desktop-only.** By the line through the cost
table's two Convolver rows (an interpolation, pending hardware), any
`seconds` above **0.091 s on an ESP32-S3** and above **0.219 s on an
ESP32-P4** is over Brad's 80 % real-time ceiling. The default is under
both. The old class's one-second room is a desktop or offline render, and
so is any measured room or hall impulse; a cabinet-length impulse fits.

**Portability tier: audiodsp** (`REQUIRES = ("audioconvolve",)`). The
convolver is audiodsp's own node. On a stock CircuitPython board this
module imports cleanly and construction raises `ImportError`.

**Cost: one node.** One `audioconvolve.Convolver`, no mixer, no glue. At
patch 0 on the default allocation (15 partitions at 48 kHz, stereo) the
palette line gives **P4 <= 34 %, S3 <= 72 %** of a 5.333 ms stereo block
(dossier Tier 3). The board measurement is pending hardware.

**Latency: 256 frames whenever an impulse is loaded** - 5.333 ms at
48 kHz, 5.805 ms at 44.1 kHz, 11.610 ms at 22.05 kHz - **and 0 when none
is.** It is the partition: a block cannot be transformed until it is
complete. `latency_samples` reads the node's own report, so it follows the
loaded state; the synthesized room is always loaded, and only an empty
impulse (`impulse=b""`) leaves the node a plain undelayed wire. Mix 0 is
the source delayed by exactly `latency_samples`, byte for byte, because the
node stays in the path at Mix 0 and a Mix move never jumps the timeline.
A room-knob move keeps it too; the one exception is the partition
`reset()` is called in (below).

**Tail.** `tail_samples` is `latency_samples` plus the loaded impulse
rounded up to a partition: 4 096 frames (85.3 ms) at the default at
48 kHz, 3 840 at 44.1 kHz, 2 048 at 22.05 kHz. After it the output is
exactly zero.

**RAM.** 141 800 B at the default at 48 kHz with a stereo room (8 224 B a
partition plus 18 440 B fixed), 110 960 B with a mono one; 133 576 B at
44.1 kHz and 76 008 B at 22.05 kHz. A measured impulse is read once at
construction, handed to the node and dropped; the class keeps no copy.

**Moving a room knob changes the room over the block in flight.** Decay,
Damping, Predelay, Diffusion and Room re-synthesize the impulse, and the
node keeps what it holds: no frame of your dry signal drops or repeats, at
any Mix (at Mix 0 the output stays the source delayed by
`latency_samples`, byte for byte, across the move), and a tail ringing at
that moment rings on into the new room. The old room fades into the new
one over the frames of the block in flight that have not played yet, in a
straight line, within 1 LSB (a sample at full scale in either room is
clipped after the fade); from the next block the output is exactly that
of an instance that always had the new room. From a host, whose moves land
between pulls, the fade is all 256 frames of the block (5.333 ms at
48 kHz). If the source ran dry part-way through a block and play went on
from another source without a `reset()`, it is only the frames left, down
to one, which is close to a hard switch. A straight line is not smooth,
so on low material the fade can step further from one frame to the next
than either room does on its own, and how much further is not known: at
48 kHz stereo with Damping 0 of 127 (500 Hz) and Mix 2, a 40 Hz sine at
2 000 LSB steps 1.97 times the larger room's own largest step when
Predelay moves from 0 to 127. A move that lands on the room already
loaded does nothing, and a patch change, the constructor and `reset()`
synthesize once, not once per knob. The synthesis itself runs on the
thread that moves the knob; on a board it can race the audio pump
(audiodsp#166, open), which a desktop cannot show. `reset()` in the middle
of a stream is a reset: it empties the room, and the 256 frames in flight
come out as exact zero, dry included. Mix moves never touch the room, but
a Mix move acts on the audio entering the node after it, so you hear it
one partition later: the 256 frames already in flight come out at the old
Mix.

**One room move per block.** The straight line is one move's. When a
second room move lands before the next pull (a host setting two knobs at
once, or one knob's controller stepping twice inside a block), the node
starts the block in flight on the room of the first move, which never
played, and fades from there to the second, so the output can jump at the
block's first frame: at 44.1 kHz stereo with Damping 0 of 127 (500 Hz)
and Mix 2, a 40 Hz sine at 2 000 LSB with Room moved to 50 and then
Predelay to 40 before one pull jumps 10 046 LSB into the block, where the
two rooms move at most 32 LSB a frame. Your dry is untouched (at Mix 0 the
output stays exact), and the frames before the block and after it are
exact. To avoid it, move one room knob per block, or change patch: a patch
change moves every knob in one synthesis and keeps the straight line. The
class cannot gather the moves for you, because nothing tells it where a
block ends; a node change that fades from the room that played is asked
for.

**What the default surrenders.** The room is normalised to unit energy
across the whole band, so with Damping in, low material comes back louder
than it went in: a 220 / 277 / 330 Hz chord (the three sines summed, at
an 8 000 LSB peak) +3.83 dB at the default 6 kHz Damping and +13.40 dB at
the 500 Hz stop, at 48 kHz. White-spectrum material comes back at its own
level, within 0.5 dB, at every setting measured, and that holds on each
side of a stereo room on its own, not only for the two together: each side is
normalised on its own, so the room sits in the middle. On the room's own
impulse the two sides read within 0.001 dB of each other at every setting
walked (the widest found, L - R +0.0005 dB at 44.1 kHz, Decay 66,
Damping 18, Predelay 34 and Diffusion 62 of 127, Room seed 48); what is
left is the rounding of the impulse to int16. So material on one side only comes back
at its own level too: at 48 kHz with Decay 0, Damping 500 Hz and
Diffusion 0, white noise hard left comes back at -0.06 dB and hard right
at +0.15 dB at Room seed 36, and at +0.02 and -0.21 dB at the default
Room, seed 1 (the kit's uniform noise, seed 12345, at -12 dBFS peak; the
tenths of a dB are that draw against that room). A mono room is one side
and holds. Damping clamps at 0.159 fs, under the point where the node's
one-pole coefficient stops moving, so at 48 kHz every one of its 128
positions is a room of its own, while at 22.05 kHz the positions from 92
up (the 6 kHz default among them) are one 3 506 Hz room.

A single Room's decay with Damping in is not held to the Decay law, and
how far one can read off it is not known: no walk covers every setting.
It reads at least about 24 % off on a mono room: +23.70 % at 44.1 kHz
(Decay 0, Damping 500 Hz, Predelay 0, Diffusion 32 of 127, Room seed 43),
+24.02 % there with a -20 dBFS click (Decay 0, Damping 500 Hz,
Predelay 127, Diffusion 28, seed 43), +22.83 % at 48 kHz (Decay 0,
Damping 500 Hz, Predelay 0, Diffusion 10, seed 43) and +21.00 % at
22.05 kHz (Decay 0, Damping 500 Hz, Predelay 0, Diffusion 46, seed 61).
On a stereo room it is at least about 16.5 %: +16.56 % at 48 kHz
(Decay 8, Damping 500 Hz, Predelay 0, Diffusion 32, seed 43) and
+16.05 % at 22.05 kHz with a -20 dBFS click (Decay 127, Damping 500 Hz,
Predelay 0, Diffusion 0, seed 27). The 64 Rooms' mean holds within 2 %.

**Measured mode.** The impulse is trimmed by `start_ms`
(int(start_ms * fs / 1000) frames, truncated) through a slice that copies
nothing on a board, then loaded at unit mean energy across the channels
the room holds, trimmed by `ir_gain_db` (-24 to +12 dB). A stereo impulse
over a mono source keeps its left channel. An impulse with frames but no
energy raises, and so does a `start_ms` that trims away every frame it
has: either would be a room whose Mix does nothing. Decay, Damping, Predelay, Diffusion and Room raise
`IndexError` from `set_macro` and `get_macro` in this mode: the loaded
impulse is the room. `live_macros` says which macros an instance has. No
impulse ships with this class; it loads yours and keeps no copy (Brad's
ruling, 2026-09-08). An impulse is one-dimensional: a 2-D array (numpy's
`(frames, channels)`) raises `TypeError`, so flatten it first.

An empty impulse (`impulse=b""`) reports no taps and no latency: it is an
undelayed wire, and its Mix does nothing. Its node is built with one
partition: measured mode's allocation starts at one frame, and zero frames
is that one partition. The class loads a measured impulse once, at
construction. Loading another into its node mid-stream (`node.load()`)
empties the room, because the node's `load()` resets.

**Two readbacks that are not what they look like.** A `damping_hz`
between 0 and 500 Hz is taken as 500 Hz, the span's bottom, with no
error; 0 or below, 7 500 Hz and up, or NaN, is out of circuit (-100 and
NaN hand the node 0 Hz and `get_macro` reads 127). And a fresh instance
reports `patch_index` 0, the family's convention, although the
constructor's exact
defaults (Damping 6 000 Hz, Mix 0.6) sit between grid steps and patch 0 is
those settings on the grid (6 059.8 Hz, Mix 0.598). Pass `patch=0` for
patch 0's room exactly. `reset()` restores patch 0, so an instance built
from the plain defaults moves onto the grid at its first reset.

`capabilities = ()`: nothing here reads a beat.
"""

VENDOR = "PyDevices"

from . import _component

try:
    import audioconvolve
except ImportError:                     # pragma: no cover - a stock board
    audioconvolve = None


#: One partition, in frames; the node's `FRAMES`.
PARTITION = 256

#: The node's ceiling in partitions (`audiodsp_convolve.h:58-60`), and in
#: taps. It is the same count of taps at every rate.
MAX_PARTITIONS = 512
CEILING_TAPS = MAX_PARTITIONS * PARTITION

#: The shortest allocation the class builds: under it Decay, which runs
#: from the node's 50 ms floor, would have no travel.
FLOOR_SECONDS = 0.06

#: The node's shortest decay (`audiodsp_convolve.c:183` at 0d35a90) and its
#: clamps on predelay and diffusion (`:184`, `:185`), in seconds and milliseconds.
NODE_DECAY_FLOOR = 0.05
PREDELAY_MAX_MS = 200.0
DIFFUSION_MAX_MS = 500.0

#: Damping's span, log, and the clamp as a fraction of the rate: just under
#: fs / (2 pi), where the node's `exp_small` stops moving the coefficient.
DAMPING_LOW_HZ = 500.0
DAMPING_HIGH_HZ = 7500.0
DAMPING_CLAMP = 0.159

#: `ir_gain_db` and `start_ms` spans, measured mode.
IR_GAIN_MIN_DB = -24.0
IR_GAIN_MAX_DB = 12.0
START_MAX_MS = 200.0

#: Room seeds: 1 + round(position * 63), 64 rooms.
ROOMS = 64

DECAY_I, DAMPING_I, PREDELAY_I, DIFFUSION_I, ROOM_I, MIX_I = range(6)
SYNTHESIS_MACROS = (DECAY_I, DAMPING_I, PREDELAY_I, DIFFUSION_I, ROOM_I)


def _floor3(value):
    """`value` floored to three decimal places, so the number a message
    names is one that builds (2.730 s is 131 040 taps; 2.731 s raises)."""
    return int(value * 1000.0) / 1000.0


def _u16(data, at):
    return data[at] | (data[at + 1] << 8)


def _u32(data, at):
    return _u16(data, at) | (_u16(data, at + 2) << 16)


def read_wav(path, sample_rate):
    """`(data, channels)` from a 16-bit PCM WAV at `sample_rate`.

    The file is read once; `data` is the `data` chunk's bytes. A WAV at
    another rate raises naming both rates: an effect does not resample.
    """
    with open(path, "rb") as handle:
        head = handle.read(12)
        if len(head) < 12 or head[0:4] != b"RIFF" or head[8:12] != b"WAVE":
            raise ValueError("ConvolutionReverb: %r is not a RIFF WAVE file"
                             % (path,))
        channels = None
        while True:
            chunk = handle.read(8)
            if len(chunk) < 8:
                break
            size = _u32(chunk, 4)
            name = chunk[0:4]
            if name == b"fmt ":
                body = handle.read(size)
                if size & 1:
                    handle.read(1)
                if len(body) < 16:
                    raise ValueError("ConvolutionReverb: %r has a short fmt "
                                     "chunk" % (path,))
                tag = _u16(body, 0)
                channels = _u16(body, 2)
                rate = _u32(body, 4)
                bits = _u16(body, 14)
                if tag not in (1, 0xFFFE) or bits != 16:
                    raise ValueError(
                        "ConvolutionReverb: %r is not 16-bit PCM (format %d, "
                        "%d bits)" % (path, tag, bits))
                if channels not in (1, 2):
                    raise ValueError(
                        "ConvolutionReverb: %r has %d channels; an impulse "
                        "is mono or stereo" % (path, channels))
                if rate != sample_rate:
                    raise ValueError(
                        "ConvolutionReverb: %r is a %d Hz impulse and the "
                        "graph runs at %d Hz; an effect does not resample"
                        % (path, rate, sample_rate))
            elif name == b"data":
                if channels is None:
                    raise ValueError("ConvolutionReverb: %r has its data "
                                     "before its fmt chunk" % (path,))
                return handle.read(size), channels
            else:
                handle.seek(size + (size & 1), 1)
    raise ValueError("ConvolutionReverb: %r has no data chunk" % (path,))


def _byte_width(impulse, view):
    """Bytes per item of `view`: 1 for bytes-likes, 2 for an int16 array."""
    width = getattr(view, "itemsize", None)
    if width is None:
        typecode = getattr(impulse, "typecode", None)
        width = 2 if typecode in ("h", "H") else 1
    if width not in (1, 2):
        raise TypeError("ConvolutionReverb: impulse must be bytes-like int16 "
                        "frames, or an int16 array")
    return width


def _sum_squares(view, width, frames, channels, lane):
    """sum_k (h[k, lane] / 32768)^2 over `frames` frames of `view`.

    Every term is an exact binary fraction and, on a desktop, so is the
    sum, so every interpreter computes the same number from the same file.
    """
    total = 0.0
    if width == 2:
        for index in range(lane, frames * channels, channels):
            value = view[index]
            if value >= 32768:
                value -= 65536
            value = value / 32768.0
            total += value * value
        return total
    step = 2 * channels
    for index in range(2 * lane, frames * step, step):
        value = view[index] | (view[index + 1] << 8)
        if value >= 32768:
            value -= 65536
        value = value / 32768.0
        total += value * value
    return total


class ConvolutionReverb(_component.Component):
    """A short synthesized room, or the room a loaded impulse was measured
    in. audiodsp tier; 256 frames of latency whenever an impulse is loaded.

    **What the default surrenders:** a dark room lifts low material (a low
    chord +3.83 dB at the default Damping, +13.40 dB at 500 Hz, 48 kHz),
    calling `reset()` mid-stream drops the 256 frames in flight, dry
    included, at every Mix, and anything longer than 0.091 s on an S3 or
    0.219 s on a P4 is a desktop room (pending hardware). A room-knob move
    drops nothing: the room changes over the block in flight. Two room
    moves before one pull can jump at the block's first frame; move one
    room knob a block, or change patch.
    """

    NAME = 'ConvolutionReverb'
    DISPLAY_NAME = 'Convolution Reverb'
    CATEGORIES = ('Reverb',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioconvolve",)

    CAPABILITIES = ()
    #: One partition, the loaded state. An instance reports what its node
    #: holds (`latency_samples` below): 0 on an empty impulse.
    LATENCY_SAMPLES = PARTITION
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Decay", "Damping", "Predelay", "Diffusion", "Room",
                    "Mix")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (0.0, 1.0),                               # 0  Decay, law position
        (DAMPING_LOW_HZ, DAMPING_HIGH_HZ, "log"),  # 1  Damping; top = out
        (0.0, 1.0),                               # 2  Predelay, position
        (0.0, 1.0),                               # 3  Diffusion, position
        (1.0, float(ROOMS)),                      # 4  Room, seed 1..64
        (0.0, 2.0),                               # 5  Mix; dry unity to 1
    )

    #: `_component.macro_of` of the dossier's section 6 settings; patch 0 is
    #: the constructor's defaults on the grid.
    PATCHES = {
        0: ("Full Room", (127, 117, 0, 64, 0, 38)),
        1: ("Short Room", (38, 98, 13, 64, 4, 44)),
        2: ("Late Room", (127, 124, 76, 64, 12, 51)),
        3: ("Dark Room", (102, 52, 25, 64, 20, 44)),
        4: ("Bright Room", (102, 127, 0, 32, 8, 51)),
        5: ("Soft Onset", (127, 108, 38, 127, 24, 63)),
        6: ("Tight Room", (0, 124, 25, 0, 2, 76)),
        7: ("Wet Only", (127, 117, 0, 64, 0, 127)),
    }

    def _build(self, decay=1.0, damping_hz=6000.0, predelay=0.0,
               diffusion=0.5, room=1, mix=0.6, seconds=0.08, impulse=None,
               impulse_channels=1, ir_gain_db=0.0, start_ms=0.0,
               patch=None):
        #: True while several macros are applied at once (the constructor,
        #: `program_change`, `reset`); the room is synthesized once, after.
        self._deferred = True
        #: The synthesis tuple the node holds, or None.
        self._loaded = None
        self._measured = impulse is not None
        rate = self._sample_rate
        if self._measured:
            self._node = self._load_impulse(impulse, impulse_channels,
                                            ir_gain_db, start_ms)
        else:
            seconds = float(seconds)
            taps = int(round(seconds * rate))
            self._check_allocation(taps, seconds)
            self._seconds = seconds
            self._node = audioconvolve.Convolver(
                max_taps=self._partitions(taps) * PARTITION,
                ir_channels=self._channel_count,
                sample_rate=rate,
                channel_count=self._channel_count)
        # `clear()` drops the history and the block in flight and keeps the
        # impulse (`Convolver.c:230` at 0d35a90): a reset empties the room,
        # it does not rebuild it.
        self._own(self._node, reset=self._node.clear)
        self._node.play(self._source)
        self._output = self._node
        damping_hz = float(damping_hz)
        if not 0.0 < damping_hz < DAMPING_HIGH_HZ:
            damping_hz = DAMPING_HIGH_HZ      # 0 (or the top) is out
        try:
            self._init_macros((decay, damping_hz, predelay, diffusion,
                               room, mix), patch)
        finally:
            self._deferred = False
        self._refresh()

    # -- the allocation (D2) -------------------------------------------

    def _partitions(self, taps):
        """Partitions for `taps`: the law, and never fewer than one."""
        return max(1, (taps + PARTITION - 1) // PARTITION)

    def _check_allocation(self, taps, seconds=None):
        """Raise, naming the class and the limit, over the ceiling or (in
        synthesized mode) under the floor. The node's own `impulse is too
        long` never reaches the caller."""
        rate = self._sample_rate
        if taps > CEILING_TAPS:
            raise ValueError(
                "%s: %d taps at %d Hz is over the ceiling of %d taps (%d "
                "partitions), %.3f s at this rate"
                % (self.NAME, taps, rate, CEILING_TAPS, MAX_PARTITIONS,
                   _floor3(CEILING_TAPS / float(rate))))
        if seconds is not None and not seconds >= FLOOR_SECONDS:
            raise ValueError(
                "%s: seconds=%r is under the floor of %.3f s, where Decay "
                "would have no travel" % (self.NAME, seconds, FLOOR_SECONDS))

    # -- measured mode (D1) --------------------------------------------

    def _trim_frames(self, start_ms):
        """Frames `start_ms` trims: int(start_ms * fs / 1000), truncated,
        with the product formed first so a whole-ms trim is exact."""
        return int(start_ms * self._sample_rate / 1000.0)

    def _load_impulse(self, impulse, impulse_channels, ir_gain_db,
                      start_ms):
        rate = self._sample_rate
        if isinstance(impulse, str):
            impulse, impulse_channels = read_wav(impulse, rate)
        if impulse_channels not in (1, 2):
            raise ValueError("%s: impulse_channels must be 1 or 2"
                             % self.NAME)
        ir_gain_db = float(ir_gain_db)
        if not IR_GAIN_MIN_DB <= ir_gain_db <= IR_GAIN_MAX_DB:
            raise ValueError("%s: ir_gain_db=%r is outside %.0f..%+.0f dB"
                             % (self.NAME, ir_gain_db, IR_GAIN_MIN_DB,
                                IR_GAIN_MAX_DB))
        start_ms = float(start_ms)
        if not 0.0 <= start_ms <= START_MAX_MS:
            raise ValueError("%s: start_ms=%r is outside 0..%.0f ms"
                             % (self.NAME, start_ms, START_MAX_MS))
        view = memoryview(impulse)
        if getattr(view, "ndim", 1) != 1:
            # A (frames, channels) array would otherwise fail at the trim's
            # slice with Python's bare NotImplementedError.
            raise TypeError("%s: impulse must be one-dimensional int16 "
                            "frames; flatten a (frames, channels) array "
                            "first" % self.NAME)
        width = _byte_width(impulse, view)
        size = len(view) * width
        if size % (2 * impulse_channels):
            raise ValueError("%s: impulse length must be whole int16 frames"
                             % self.NAME)
        frames = size // (2 * impulse_channels)
        trim = self._trim_frames(start_ms)
        if frames and trim >= frames:
            # Clamping would build the unloaded wire, a Mix that does
            # nothing, with no error (ruling (o)). Only `impulse=b""` is
            # the deliberate empty room.
            raise ValueError(
                "%s: start_ms=%r trims %d frames at %d Hz and the impulse "
                "has %d; the trim leaves no room, and a Mix that does "
                "nothing" % (self.NAME, start_ms, trim, rate, frames))
        if trim > frames:
            trim = frames
        frames -= trim
        per_frame = impulse_channels * (2 // width)
        view = view[trim * per_frame:]
        self._check_allocation(frames)
        self._seconds = frames / float(rate)
        room_channels = min(impulse_channels, self._channel_count)
        node = audioconvolve.Convolver(
            max_taps=self._partitions(frames) * PARTITION,
            ir_channels=room_channels,
            sample_rate=rate,
            channel_count=self._channel_count)
        if frames:
            energy = 0.0
            for lane in range(room_channels):
                energy += _sum_squares(view, width, frames,
                                       impulse_channels, lane)
            if not energy > 0.0:
                node.deinit()
                raise ValueError(
                    "%s: the impulse has %d frames and no energy; a silent "
                    "room is a dead Mix" % (self.NAME, frames))
            gain = (10.0 ** (ir_gain_db / 20.0)
                    / (energy / room_channels) ** 0.5)
            node.load(view, impulse_channels, gain)
        return node

    # -- the laws (section 6) ------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _predelay_ms(self):
        span = (self._seconds - NODE_DECAY_FLOOR) * 1000.0 / 2.0
        if span > PREDELAY_MAX_MS:
            span = PREDELAY_MAX_MS
        return self._macros[PREDELAY_I] * span

    def _decay_seconds(self, predelay_ms):
        room = self._seconds - predelay_ms / 1000.0
        return NODE_DECAY_FLOOR * (room / NODE_DECAY_FLOOR) ** \
            self._macros[DECAY_I]

    def _damping_hz(self):
        position = self._macros[DAMPING_I]
        if position >= 1.0:
            return 0.0
        hz = _component.macro_value(self._MACRO_RANGES[DAMPING_I], position)
        ceiling = DAMPING_CLAMP * self._sample_rate
        if hz > ceiling:
            hz = ceiling
        return self._hz(hz)

    def _seed(self):
        return 1 + int(round(self._macros[ROOM_I] * (ROOMS - 1)))

    def _synthesis(self):
        """(decay s, damping Hz, predelay ms, diffusion ms, seed): what the
        node is handed for the current positions."""
        predelay = self._predelay_ms()
        t60 = self._decay_seconds(predelay)
        span = t60 * 1000.0 / 4.0
        if span > DIFFUSION_MAX_MS:
            span = DIFFUSION_MAX_MS
        return (t60, self._damping_hz(), predelay,
                self._macros[DIFFUSION_I] * span, self._seed())

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        del position
        if self._deferred:
            return
        if index == MIX_I:
            self._node.set(mix=self._value(MIX_I) * 0.5)
            return
        self._refresh()

    def _refresh(self):
        """Hand the node the room and the Mix. The room is re-synthesized
        only when its tuple differs from the one it holds."""
        if not self._measured:
            room = self._synthesis()
            if room != self._loaded:
                self._node.synthesize(decay=room[0], damping_hz=room[1],
                                      predelay_ms=room[2],
                                      diffusion_ms=room[3], seed=room[4])
                self._loaded = room
        # The node takes 0..1 and doubles it (`audiodsp_convolve.c:88`);
        # halving is a power of two, so it adds no rounding of its own.
        self._node.set(mix=self._value(MIX_I) * 0.5)

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index` whole, then synthesize once. In measured
        mode only its Mix is audible; the synthesis positions are stored
        and inert. Inside the constructor the one synthesis is the
        constructor's own."""
        outer = self._deferred
        self._deferred = True
        try:
            _component.Component.program_change(
                self, index, channel, note_id, sample_position)
        finally:
            self._deferred = outer
        if not outer and type(self).PATCHES.get(index) is not None:
            self._refresh()

    def _macro_index(self, index):
        index = _component.Component._macro_index(self, index)
        if self._measured and index != MIX_I:
            raise IndexError(
                "%s holds a measured impulse, so macro %d %r is not live: the "
                "loaded impulse is the room, and only Mix (macro %d) is"
                % (self.NAME, index, self.MACRO_LABELS[index], MIX_I))
        return index

    # -- the reads -----------------------------------------------------

    @property
    def node(self):
        """The one `audioconvolve.Convolver` this class built."""
        self._check_live()
        return self._node

    @property
    def measured(self):
        """True when an impulse was given: the room is that impulse."""
        self._check_live()
        return self._measured

    @property
    def live_macros(self):
        """The macro indexes this instance has: all six synthesized, only
        Mix (5) in measured mode."""
        self._check_live()
        if self._measured:
            return (MIX_I,)
        return (DECAY_I, DAMPING_I, PREDELAY_I, DIFFUSION_I, ROOM_I, MIX_I)

    @property
    def seconds(self):
        """The allocation asked for; in measured mode, the trimmed
        impulse's own length."""
        self._check_live()
        return self._seconds

    @property
    def allocated_seconds(self):
        """The allocation actually held: partitions x 256 / fs."""
        self._check_live()
        taps = self._partitions(int(round(self._seconds
                                          * self._sample_rate)))
        return taps * PARTITION / float(self._sample_rate)

    @property
    def decay_seconds(self):
        """The room's T60 by the Decay law, or None in measured mode."""
        self._check_live()
        if self._measured:
            return None
        return self._synthesis()[0]

    @property
    def latency_samples(self):
        """256 whenever the node holds an impulse, 0 when it holds none,
        read from the node."""
        self._check_live()
        return self._latency()

    def _latency(self):
        """`latency_samples` as a plain method, so a subclass can reach it
        on MicroPython, whose `property` has no `fget`."""
        return int(self._node.latency)

    @property
    def tail_samples(self):
        """`latency_samples` plus the loaded impulse rounded up to a
        partition; 0 when nothing is loaded."""
        self._check_live()
        taps = int(self._node.taps)
        if not taps:
            return 0
        return self._latency() + taps
