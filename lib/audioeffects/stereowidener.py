"""`StereoWidener` - a stereo widener with Haas and Mid/Side characters.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests.
"""

VENDOR = "PyDevices"

from array import array

import audiocore

from . import _component

from .digitaldelay import whole_frames

try:
    import audioecho
    import audiomath
    import audiomixer
    import audioroute
except ImportError:                     # pragma: no cover - a stock board
    audioecho = audiomath = audiomixer = audioroute = None


#: The Delay span, in ms, swept by ratio.
DELAY_MIN_MS = 1.0
DELAY_MAX_MS = 40.0

#: The line: Delay's top plus 1 ms, so the node never clamps the read.
LINE_MS = DELAY_MAX_MS + 1.0

#: How fast a Delay move walks the read head, in delay-seconds per second:
#: 3/16, exact in every float format, a pitch bend of x1.1875 while it moves.
SLEW = 0.1875

#: The hardest a Mixer voice pans. The integer mixer clamps any panning to
#: this, and its far channel keeps a scale of 1/32768: a voice at level 1
#: then hands that channel `x >> 15`, which is -1 for every negative sample
#: and 0 otherwise. `SIGN` and `NEGATE` build the +1 that cancels it.
HARD = 32767.0 / 32768.0

#: The two modulators the cancelling branch multiplies by, in
#: `audiomath.Multiply`'s Q15: 1 turns a sample into the far channel's
#: `x >> 15` (-1 below zero, else 0), and -32768 turns that into +1 or 0,
#: exactly.
SIGN = 1
NEGATE = -32768

#: Frames in each modulator table: more than one, so the native mixer and
#: Multiply never take a table shorter than the word they consume.
TABLE_FRAMES = 16

#: The frames a mixer pull hands out, and so the frames each voice and each
#: Splitter tap take per pull.
BLOCK = 256

#: How close, as a 0..1 knob position, a Delay write must come to the grid
#: step the constructor's `delay_ms` seeded to count as a host echoing it
#: back: 1e-6 is 1/7 874 of one MIDI step, and holds a single-precision
#: round trip.
ECHO_TOLERANCE = 1e-6

#: The patches' Delays, exactly, by MIDI step: Delay on one of these steps
#: plays the round number the patch table names (14 ms, not the step's
#: 14.06), whichever way it got there.
DELAY_STEPS = {62: 6.0, 91: 14.0, 111: 25.0}

#: How close, in MIDI steps, Delay must sit to a step in `DELAY_STEPS`.
STEP_TOLERANCE = 1e-4

WIDTH_I, DELAY_I, CHARACTER_I = range(3)

CHARACTERS = ("haas", "mid_side")

#: The constructor defaults, which NaN falls back to.
DEFAULT_WIDTH = 1.0
DEFAULT_DELAY_MS = 14.0


def _option(value, default):
    """A constructor option as a float; NaN is the option's default."""
    value = float(value)
    if value != value:
        return default
    return value


def _between(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def haas_voices(width):
    """((lead level, lead panning), (copy level, copy panning)) for a Haas
    Width: up to 1 the lead keeps the left at unity and turns its right down
    by the Width while the copy comes up in the right; above 1 the copy
    stays at unity and the lead turns down to 1/Width."""
    if width <= 1.0:
        return (1.0, -min(width, HARD)), (width, HARD)
    return (1.0 / width, -HARD), (1.0, HARD)


class StereoWidener(_component.Component):
    """Widen a stereo part: Haas delays the right channel a few milliseconds
    behind the left, and Mid/Side scales the difference between the channels.

    **The controls.** Width sets how wide the part sounds. Delay is how
    late the Haas copy is, and only Haas uses it. Character picks Haas or
    Mid/Side. The Effect controls page lists what the knobs span.

    **Haas.** The ear places a sound by the first arrival and hears the late
    copy as width.
    At Width 1 the left channel passes untouched and the right channel is
    your right channel, exactly Delay late.
    Between Width 0 and 1 the right channel crossfades from itself to its
    late copy, which colours it most at 0.5.
    Width 0 is a wire.
    Above Width 1 the copy stays where it is and the left turns down, 6 dB
    at Width 2, to pull back the image the left's early arrival leans its
    way.
    Turning Delay glides the copy to the new time instead of clicking,
    bending its pitch while it moves.
    Haas folds to mono as a comb filter: at Width 1 with the default 14 ms,
    the mono sum has full-depth notches at 35.7, 107 and 179 Hz and on up.
    Use Mid/Side when the mix may be summed.

    **Mid/Side.** Summed to mono, the output is the same at every Width,
    within one LSB.
    Width 0 is mono, 1 is a wire and 2 doubles the sides.
    Above Width 1, a part panned hard left shows up inverted on the right.
    A part that is the same in both channels comes out unchanged.
    Peaks below half of full scale never clip at any Width.

    **Mono, latency, tail.** A one-channel source comes out exactly as it
    went in, whatever the controls say.
    To widen a mono part, make it stereo first (a stereo chorus, say) and
    put this after it.
    A click in the left comes out on the frame it went in: there is no
    latency.
    `tail_samples` is the copy's reach in Haas, and 0 in Mid/Side or at
    Width 0.
    `reset()` empties the line and returns to patch 0.
    The class never reads the host's tempo.

    **Limits shared by the family.**
    A control that jumps, Width or Character, makes the output step: move it
    in small steps from the host if you need it smooth.
    """

    NAME = 'StereoWidener'
    DISPLAY_NAME = 'Stereo Widener'
    CATEGORIES = ('Spatial',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho", "audiomath", "audioroute")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    #: Half of full scale, rounded down a step: Mid/Side at Width 2 doubles
    #: an anti-phase pair's side, and 2 x 16 383 still fits.
    INPUT_CEILING_DBFS = -6.03

    #: The constructor's Delay, exactly, which a rack's reset puts back
    #: with the knobs.
    _KEPT = ("_delay_exact",)

    MACRO_LABELS = ("Width", "Delay", "Character")
    MACRO_MODES = {
        0: "BIPOLAR",
        1: "UNIPOLAR",
        2: "TOGGLE",
    }
    _MACRO_RANGES = (
        (0.0, 2.0),                               # 0  Width; MIDI 64 is 1.0
        (DELAY_MIN_MS, DELAY_MAX_MS, "log"),      # 1  Delay, ms
        (0.0, 1.0),                               # 2  Character
    )
    _MACRO_UNITS = {1: "ms"}

    #: `_component.macro_of` of the card's patch settings.
    PATCHES = {
        0: ("Haas 14 ms", (64, 91, 0)),
        1: ("Haas Tight", (64, 62, 0)),
        2: ("Haas Wide", (64, 111, 0)),
        3: ("Haas Recentred", (96, 91, 0)),
        4: ("Mid/Side Wide", (96, 91, 127)),
        5: ("Mid/Side Narrow", (32, 91, 127)),
        6: ("Mono", (0, 91, 127)),
    }

    def _build(self, width=DEFAULT_WIDTH, delay_ms=DEFAULT_DELAY_MS,
               character="haas", patch=None):
        if character not in CHARACTERS:
            raise ValueError("character must be %r or %r, not %r"
                             % (CHARACTERS[0], CHARACTERS[1], character))
        width = _between(_option(width, DEFAULT_WIDTH), 0.0, 2.0)
        delay_ms = _between(_option(delay_ms, DEFAULT_DELAY_MS),
                            DELAY_MIN_MS, DELAY_MAX_MS)
        #: The constructor's Delay, exactly, and the grid step it seeds, so
        #: a fresh instance reads a whole MIDI step. The exact value plays
        #: until Delay moves (a host echoing `get_macro(1)` does not move
        #: it) or a patch is loaded.
        self._delay_exact = delay_ms
        span = self._MACRO_RANGES[DELAY_I]
        self._delay_seed = _component.position_of_midi(
            "UNIPOLAR", _component.macro_of(span, delay_ms))
        self._frames = 1
        #: The longest delay, in frames, the read head may still sit at: a
        #: falling move walks the head down, so the old Delay holds until
        #: the line is next emptied. None while the line is empty and no
        #: Delay has been set since: an emptied line snaps onto its Delay.
        self._reach = None
        self._wired = False
        self._ready = False
        self._ms = None
        if self._channel_count == 2:
            self._build_graph()
        else:
            # One channel has no width to work on: the output is the source.
            self._output = self._source
        values = (width, delay_ms,
                  1.0 if character == CHARACTERS[1] else 0.0)
        self._init_macros(values)
        self._macros[DELAY_I] = self._delay_seed
        # A constructor patch lands before the graph is first set up, so a
        # Mid/Side or Width 0 patch never wires the Haas voices (`_wire`).
        if patch is not None:
            self.program_change(patch)
        self._ready = True
        self._refresh()

    def _build_graph(self):
        rate = self._sample_rate
        # The borrowed source's only reader, at Width 1 in Haas and so the
        # source byte for byte: a switch between the characters re-points
        # the output and never skips or repeats a source frame.
        self._ms = self._own(audioroute.MidSide(
            self._source, width=1.0, sample_rate=rate, channel_count=2),
            reset=False)
        # A MidSide with no source: one block of zeros per pull, which the
        # voices prime from when they are wired (`_wire`).
        self._hush = self._own(audioroute.MidSide(
            width=1.0, sample_rate=rate, channel_count=2), reset=False)
        self._in = self._own(audioroute.Port(self._hush), reset=False)
        # Tap 0 is the lead, tap 1 what the line delays, tap 2 the
        # cancelling branch.
        self._split = self._own(audioroute.Splitter(self._in, taps=3),
                                reset=False)
        # The cancelling branch: +1 on each channel whose sample is below
        # zero, else 0. A hard-panned voice at level 1 leaves -1 in its far
        # channel on exactly those samples (`HARD`), and this puts it back.
        self._sign = self._own(audiomath.Multiply(
            self._split.tap(2), self._table(SIGN), mix=1.0,
            sample_rate=rate, channel_count=2), reset=False)
        self._negate = self._own(audiomath.Multiply(
            self._sign, self._table(NEGATE), mix=1.0,
            sample_rate=rate, channel_count=2), reset=False)
        self._fix = self._own(audioroute.Splitter(self._negate, taps=2),
                              reset=False)
        # What the line delays: the right channel, and an exact zero in the
        # left, so the copy's hard pan has nothing negative to leave there.
        self._feed = self._own(audiomixer.Mixer(
            voice_count=2, buffer_size=BLOCK * 2 * 4, channel_count=2,
            bits_per_sample=16, samples_signed=True, sample_rate=rate),
            reset=False)
        # The Mixer's own reset never reaches it, for the reason `_tail`
        # gives.
        self._fed = self._own(audioroute.MidSide(
            self._feed, width=1.0, sample_rate=rate, channel_count=2),
            reset=False)
        self._line = self._own(audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=2, max_delay_ms=LINE_MS,
            delay_frames=1, feedback=0.0, mix=2.0, damping_hz=0.0,
            cut_hz=0.0, delay_slew=SLEW), reset=self._clear)
        self._line.play(self._fed)
        # Not reset by the walk: neither voice holds a block between two
        # pulls (`_wire`), so there is nothing of its own to clear.
        self._mixer = self._own(audiomixer.Mixer(
            voice_count=3, buffer_size=BLOCK * 2 * 4, channel_count=2,
            bits_per_sample=16, samples_signed=True, sample_rate=rate),
            reset=False)
        # The Haas output: a width-1 MidSide, byte for byte, whose reset
        # forwards nothing. A host's reset of the output (a mixer voice's
        # `play()` does one) would otherwise reach the Mixer, and
        # CircuitPython's own Mixer handles that differently from
        # audiodsp's, so the interpreters would part ways.
        self._tail = self._own(audioroute.MidSide(
            self._mixer, width=1.0, sample_rate=rate, channel_count=2),
            reset=False)
        self._silence = audiocore.RawSample(
            array("h", bytes(2 * 2 * 2)), sample_rate=rate, channel_count=2)
        #: Where `audiocore.get_buffer` is compiled out, the one-voice
        #: mixer `_pull` primes from `_tail`; built the first time it is
        #: needed.
        self._puller = None
        self._output = self._ms

    def _table(self, value):
        """A looping stereo modulator that is `value` in both channels."""
        table = audiocore.RawSample(
            array("h", [value] * (2 * TABLE_FRAMES)),
            sample_rate=self._sample_rate, channel_count=2)
        self._tables = getattr(self, "_tables", ()) + (table,)
        return table

    def _wire(self):
        """Play the voices, the first time the output reaches the mixer.

        A voice's `play()` primes a block from its source. With the
        Splitter on `_hush` that block is zeros, and one pull of the mixer
        hands it out, so wiring takes nothing from the borrowed source and
        leaves no voice holding a block: whatever the MidSide has handed
        out, the output has played, at every Width and Character. So a
        reset or a return to Haas that empties the line never empties a
        block a voice is still waiting to play, and a voice never plays a
        block read at a Delay the line has since left. The level gates are
        opened first, as `_component.open_level_gates` opens them."""
        voices = self._mixer.voice
        feeds = self._feed.voice
        self._levels()
        # The line's voices: the source panned hard right, and the
        # cancelling branch's left, which together leave the left at 0.
        feeds[0].level, feeds[0].panning = 1.0, HARD
        feeds[1].level, feeds[1].panning = 1.0, -HARD
        for voice in voices + feeds:
            voice.play(self._silence, loop=True)
        self._pull()
        feeds[0].play(self._split.tap(1))
        feeds[1].play(self._fix.tap(0))
        voices[0].play(self._split.tap(0))
        voices[1].play(self._line)
        voices[2].play(self._fix.tap(1))
        self._pull()
        self._in.play(self._ms)
        self._clear()
        self._wired = True

    def _pull(self):
        """Pull one block from the mixer and drop it.

        Where `audiocore.get_buffer` is compiled out (CircuitPython's
        default board builds), a voice of a one-voice mixer of our own
        plays `_tail` and stops: its `play()` primes one block, which pulls
        the mixer once. `_tail` forwards no reset, so the play rewinds
        nothing behind it."""
        pull = getattr(audiocore, "get_buffer", None)
        if pull is not None:
            pull(self._mixer)
            return
        if self._puller is None:
            # Nothing ever pulls this mixer, so its own buffers are the
            # smallest that hold a stereo frame.
            self._puller = self._own(audiomixer.Mixer(
                voice_count=1, buffer_size=16, channel_count=2,
                bits_per_sample=16, samples_signed=True,
                sample_rate=self._sample_rate), reset=False)
        voice = self._puller.voice[0]
        voice.play(self._tail)
        voice.stop()

    def _clear(self):
        self._line.clear()
        self._reach = None

    # -- the maps ------------------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _width(self):
        return _between(self._value(WIDTH_I), 0.0, 2.0)

    def _mid_side(self):
        return self._macros[CHARACTER_I] >= 0.5

    def _delay_ms(self):
        if self._delay_exact is not None:
            return self._delay_exact
        midi = _component.midi_of_position("UNIPOLAR",
                                           self._macros[DELAY_I])
        step = int(midi + 0.5)
        if abs(midi - step) <= STEP_TOLERANCE and step in DELAY_STEPS:
            return DELAY_STEPS[step]
        return self._value(DELAY_I)

    def macro(self, index):
        """What macro `index` currently stands for, in its own units; for
        Delay, the milliseconds it plays."""
        self._check_live()
        if index == DELAY_I:
            return self._delay_ms()
        return _component.Component.macro(self, index)

    def _levels(self):
        lead, copy = haas_voices(self._width())
        voices = self._mixer.voice
        voices[0].level, voices[0].panning = lead
        voices[1].level, voices[1].panning = copy
        # The lead at unity panned hard left leaves -1 in the right on
        # every negative sample; the cancelling branch, panned hard right,
        # adds it back. Anywhere else the lead's right is a real level.
        voices[2].level = 1.0 if lead == (1.0, -HARD) else 0.0
        voices[2].panning = HARD

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        if index == DELAY_I and self._ready and not self._seeding and (
                abs(position - self._delay_seed) > ECHO_TOLERANCE):
            self._delay_exact = None
        if self._ready:
            self._refresh()

    def _apply_positions(self, positions, patch_index):
        """Apply a patch (or a rack's restore) whole, then refresh the graph
        once. A patch drops the constructor's Delay; a restore keeps the
        one it put back (`_KEPT`), so the two share this one path."""
        ready = self._ready
        self._ready = False
        try:
            _component.Component._apply_positions(self, positions,
                                                  patch_index)
        finally:
            self._ready = ready
        if not self._seeding:
            self._delay_exact = None
        if ready:
            self._refresh()

    def _refresh(self):
        if self._ms is None:
            return
        self._frames = max(1, whole_frames(self._delay_ms(),
                                           self._sample_rate))
        self._line.set(delay_frames=self._frames)
        self._route()
        if self._reach is None or self._frames > self._reach:
            self._reach = self._frames

    def _route(self):
        """Point the output at the MidSide (Mid/Side, or Haas Width 0) or
        at the Haas mixer, emptying the line when the mixer comes back."""
        width = self._width()
        if self._mid_side():
            self._ms.set(width=width)
            self._route_around(self._ms)
            return
        self._ms.set(width=1.0)
        if width <= 0.0:
            self._route_around(self._ms)
            return
        if not self._wired:
            self._wire()
        else:
            self._levels()
            self._rejoin(keep=(self._ms,))
        self._output = self._tail

    def _haas_live(self):
        return (self._ms is not None and not self._mid_side()
                and self._width() > 0.0)

    @property
    def tail_samples(self):
        """What this bound promises is in the class docstring."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        if not self._haas_live():
            return 0
        return (self._reach or self._frames) + 1
