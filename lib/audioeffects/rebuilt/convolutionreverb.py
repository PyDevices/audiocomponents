"""`ConvolutionReverb` - a room made by convolution, synthesized or loaded.

The player's text is the class docstring, and every sentence in it that
makes a claim is tied to a test by the `CLAIMS` table in the class's test
file. How it works, and why, is in the class's dossier in the workspace
repo (`docs/effects-internal/dossiers/ConvolutionReverb.md`).
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
    """A room behind your dry signal, made by convolution: synthesized from
    five knobs, or the room your own impulse was recorded in.

    With nothing loaded the class synthesizes a short room from noise.
    By default the room is 0.08 s long.

    **The controls.** Decay is how long the room rings, Damping darkens its
    tail, Predelay puts silence between the dry and the room, and Diffusion
    fades the room in instead of starting it as a burst.
    Room picks one of 64 rooms of the same size.
    Damping runs from 500 Hz at its bottom stop to out at its top stop.
    At 22.05 kHz its brightest positions below the top stop clamp and all
    make the same room.
    Mix runs from 0 to 2: the dry at unity up to 1, the room alone at 2.
    With Damping out, each of the 64 Rooms falls 60 dB within 3 % of the
    Decay time.
    With Damping in, the 64 Rooms fall 60 dB within 2 % of the Decay time on
    average.
    A single Room with Damping in can take more than 15 % longer.
    At Damping's 500 Hz stop, low material comes back louder than it went
    in.
    Each side of a stereo room is normalised on its own, so the room sits in
    the middle.

    **Your own impulse.** Hand it `impulse=`, int16 frames or the path to a
    16-bit PCM WAV at the graph's rate, and the room is that recording.
    The room is then your source convolved with the impulse at unit
    energy, within 1 LSB.
    `ir_gain_db` trims it from -24 to +12 dB, and `start_ms` cuts up to
    200 ms from its start.
    Only Mix is live then: the other five knobs raise `IndexError`.
    A WAV at another rate raises `ValueError`, and so does an impulse with
    no energy or a `start_ms` that trims away every frame.
    An empty impulse, `impulse=b""`, is an undelayed wire whose Mix does
    nothing and whose `reset()` silences nothing.

    **The allocation.** `seconds` is the longest room the instance can hold,
    carved once when you build it: from 0.06 s up to 131 072 frames, and
    outside that the constructor raises `ValueError`.

    **Latency and tail.** `latency_samples` reads 256 while an impulse is
    loaded and 0 on the empty impulse.
    Held at Mix 0, the output is your source, byte for byte,
    `latency_samples` late, while the source keeps feeding it and nothing
    resets it.
    `tail_samples` is `latency_samples` plus the loaded room rounded up to
    a whole block of 256 frames.
    More than `tail_samples` frames after your input's last non-zero frame,
    the output is exact zero.

    **Moving the knobs.** No frame of your dry signal drops or repeats when
    you move a room knob, at any Mix, however many moves you make.
    From the end of the block in flight, the output is that of an instance
    that always had the new settings.
    A Mix move acts from the end of the block in flight, so Mix 0 reaches
    the plain source up to 256 frames late.
    `reset()` empties the room and returns to patch 0.
    With an impulse loaded, `reset()` in the middle of a stream silences the
    block in flight, 256 frames, dry included, and with Mix set back to 0
    your source carries on on time after it.
    A host that calls `audiocore.reset_buffer` on the output silences the
    block in flight too, but also drops the frames the node holds from a
    source buffer it had not finished.

    **Limits shared by the family.**
    A control that jumps makes the output step: move it in small steps from
    the host if you need it smooth.
    The tail rings only while the source keeps feeding: feed silence to let
    it ring out. A tail cut short by a source that stopped carries on when
    the source comes back.
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
