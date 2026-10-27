"""`PitchShifter` - a fixed-interval splice pitch shifter.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests.
"""

VENDOR = "PyDevices"

import math
from array import array

import audiocore

from . import _component

from .digitaldelay import laps_to_zero, whole_frames

try:
    import audiodelays
    import audioecho
    import audiomixer
    import audioroute
except ImportError:                     # pragma: no cover - a stock board
    audiodelays = audioecho = audiomixer = audioroute = None


PITCH_I, FINE_I, MIX_I, DELAY_I, FEEDBACK_I = range(5)

#: The Delay and Feedback spans' tops.
DELAY_MAX_MS = 112.5
FEEDBACK_MAX = 0.95

#: The shifter's window, in ms: the default and the clamp.
WINDOW_MS = 30.0
WINDOW_MIN_MS = 15.0
WINDOW_MAX_MS = 60.0

#: The line holds Delay's top and a little; the loop holds Delay's top, the
#: half window and crossfade it adds, and the window its splicer reads over.
LINE_MS = 120.0
LOOP_MS = 250.0

#: The frames one pull of the output hands out.
BLOCK = 256

#: The node's read rate is whole 256ths of unity (`PitchShift.c:121`).
STEPS = 256

#: The constructor defaults, which NaN falls back to.
DEFAULTS = (7.0, 0.0, 1.0, 0.0, 0.0)


def crossfade_frames(sample_rate):
    """The shifter's crossfade: 4/3 ms in whole frames, 64 at 48 kHz."""
    return (int(sample_rate) + 375) // 750


def window_frames(window_ms, sample_rate):
    """The shifter's window in whole frames at the running rate."""
    return whole_frames(window_ms, sample_rate)


def ratio_step(ratio):
    """The node's read rate nearest `ratio`, in 256ths."""
    return int(math.floor(ratio * STEPS + 0.5))


def step_centre_semitones(step):
    """Semitones that put the node on `step`: the centre of the step, so
    the node's truncation lands on it at any float width."""
    return 12.0 * math.log((step + 0.5) / STEPS) / math.log(2.0)


def step_semitones(step):
    """The step itself in semitones, for the loop; exactly 0 at unity."""
    if step == STEPS:
        return 0.0
    return 12.0 * math.log(float(step) / STEPS) / math.log(2.0)


def _option(value, default, low, high):
    """A constructor option as a float in [low, high]; NaN is the default."""
    value = float(value)
    if value != value:
        return default
    if value < low:
        return low
    if value > high:
        return high
    return value


def _rint(value):
    """Round half away from zero."""
    if value >= 0.0:
        return int(value + 0.5)
    return -int(-value + 0.5)


class PitchShifter(_component.Component):
    """Play your part again a fixed interval up or down, a little behind
    you, the way the first harmonizer boxes did.

    **The controls.** Pitch is the interval in whole semitones. Fine
    detunes it. The shifter reads in steps of 1/256 of the speed, so Fine
    moves in steps of about 7 cents near unity and 13.5 near the octave
    down, and the interval is within 0.5 % of the one Pitch and Fine name.
    Mix keeps your dry signal at unity up to its centre, 1, with the
    shifted voice coming up to unity beside it; at 2 you hear the shifted
    voice alone, and at 0 the output is your input. Delay holds the shifted
    voice back. Feedback sends the shifted voice round again, and every
    repeat is shifted once more: at a fifth up the repeats climb a fifth,
    then a ninth, then a thirteenth. The Effect controls page lists what
    the knobs span.

    **The splice.** The shifter keeps a short memory of what you play, the
    window, and reads it at the new speed, splicing back to the other end
    when it runs out.
    Off unity, each note comes back anywhere from straight away to one
    window and 1.3 ms late, plus Delay, the delay sweeping and jumping at
    every splice.
    At unity it sits still, 1.3 ms late, from a fresh start, a reset or a
    return from Mix 0; after a Pitch move it sits wherever the splice left
    it, up to one window and 1.3 ms late.
    On CircuitPython's own pitch shifter a reset or a return from Mix 0 does
    not restart the splice, so there it sits wherever the splice was.
    Shifting down drops slices of what you play; shifting up repeats them.
    The window is 30 ms unless you pass `window_ms`, 15 to 60, when you
    build it: a longer window splices less often and arrives later.

    **The dry.** Up to Mix 1 your dry signal passes untouched, sample for
    sample, with the shifted voice added on top, so a hot input can reach
    the rail.
    Feedback stacks level too, far past the input: at Feedback 127, Delay 0
    and Mix 2 a noise burst peaking at -10.3 dBFS reaches the rail at
    unison, and comes within 6 dB of it at an octave or a fourth or fifth
    either way.

    **Mono, latency, tail.** A one-channel source gets a one-channel
    shifter with the same window.
    Latency is zero samples: the dry is never delayed.
    `tail_samples` is an upper bound on how long the output takes to reach
    exact zero once your input stops, at every Feedback.
    `reset()` empties the shifter and both delay lines and returns to
    patch 0.
    The class never reads the host's tempo.
    If your host takes the output before it loads a patch or moves Mix, or
    loads a patch right after a reset, the first 256 frames, 5 ms at
    48 kHz, play at the old level.

    **Limits shared by the family.**
    A control that jumps makes the output step: move it in small steps from
    the host if you need it smooth.
    """

    NAME = 'PitchShifter'
    DISPLAY_NAME = 'Pitch Shifter'
    CATEGORIES = ('Pitch Shift',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho", "audioroute")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    #: Where no patch can reach the rail. At Mix 1 the dry and the shifted
    #: voice each reach the input's peak, and the repeats add Feedback^n of
    #: it: 1 + 1 / (1 - 0.5535) = 3.24 times the peak at patches 4 and 5,
    #: which -10.21 dBFS keeps under full scale. Feedback at its top stacks
    #: up to 21 times, and the kit declares those cells.
    INPUT_CEILING_DBFS = -10.5

    MACRO_LABELS = ("Pitch", "Fine", "Mix", "Delay", "Feedback")
    MACRO_MODES = {
        0: "BIPOLAR",
        1: "BIPOLAR",
        2: "BIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (-12.0, 12.0),                  # 0  Pitch, semitones; plays whole
        (-50.0, 50.0),                  # 1  Fine, cents
        (0.0, 2.0),                     # 2  Mix; MIDI 64 is 1.0
        (0.0, DELAY_MAX_MS),            # 3  Delay, ms
        (0.0, FEEDBACK_MAX),            # 4  Feedback
    )
    _MACRO_UNITS = {0: "semitones", 1: "cents", 3: "ms"}

    #: `_component.macro_of` of the card's patch settings.
    PATCHES = {
        0: ("Fifth Above", (101, 64, 64, 0, 0)),
        1: ("Octave Up", (127, 64, 64, 0, 0)),
        2: ("Octave Down", (0, 64, 64, 0, 0)),
        3: ("Doubler", (64, 75, 64, 17, 0)),
        4: ("Rising Fifths", (101, 64, 64, 102, 74)),
        5: ("Falling Fourths", (37, 64, 64, 113, 74)),
        6: ("Shifted Only", (101, 64, 127, 0, 0)),
    }

    def _build(self, pitch=7.0, fine=0.0, mix=1.0, delay_ms=0.0,
               feedback=0.0, window_ms=WINDOW_MS, patch=None):
        spans = self._MACRO_RANGES
        values = tuple(
            _option(value, DEFAULTS[index], spans[index][0], spans[index][1])
            for index, value in enumerate(
                (pitch, fine, mix, delay_ms, feedback)))
        window_ms = _option(window_ms, WINDOW_MS, WINDOW_MIN_MS,
                            WINDOW_MAX_MS)
        rate = self._sample_rate
        #: The window and the crossfade, in whole frames at this rate.
        self._window = self._window_frames(window_ms)
        self._overlap = crossfade_frames(rate)
        self._ready = False
        self._wired = False
        #: Whether the host has asked for the output yet. Until it has,
        #: nothing has been pulled, and a control that moves a voice's
        #: level re-arms the graph so the level holds from frame 0. A reset
        #: or a return from Mix 0 does not start that window again: the
        #: class cannot see a pull, and a host that keeps the node it took
        #: would have every later Mix move empty the repeats.
        self._taken = False
        #: The two Mixer levels last handed to the voices.
        self._applied = None
        #: Whether the loop's splicer has run since its line was last
        #: emptied: it then reads half a window later (`_loop_frames`).
        self._engaged = False
        self._step = STEPS
        self._loop_shift = 0.0
        self._delay_frames = 1
        self._feedback = 0.0
        self._build_graph()
        self._init_macros(values)
        # Every knob lands on its 0-127 step, as a host would set it, so a
        # fresh instance reads patch 0 exactly and no constructor value is
        # kept beside the grid.
        for index in range(len(values)):
            span = spans[index]
            mode = self._mode(index)
            self._macros[index] = _component.position_of_midi(
                mode, _component.macro_of(span, values[index], mode))
        if patch is not None:
            self.program_change(patch)
        self._ready = True
        self._refresh()

    def _build_graph(self):
        rate = self._sample_rate
        channels = self._channel_count
        width = 2 * channels
        # The borrowed source's only reader: a width-1 MidSide is the source
        # byte for byte in 256-frame blocks, and it is what Mix 0 hands
        # back, so a move to or from Mix 0 never skips or repeats a frame.
        self._head = self._own(audioroute.MidSide(
            self._source, width=1.0, sample_rate=rate,
            channel_count=channels), reset=False)
        # A MidSide with no source: one block of zeros per pull, which the
        # shifter and the voices prime from (`_wire`).
        self._hush = self._own(audioroute.MidSide(
            width=1.0, sample_rate=rate, channel_count=channels),
            reset=False)
        self._in = self._own(audioroute.Port(self._hush), reset=False)
        # A Splitter's ring cannot be rewound; its taps are read in step,
        # 256 frames a pull each, so it holds nothing between pulls.
        self._split = self._own(audioroute.Splitter(self._in, taps=2),
                                reset=False)
        self._shift = self._own(audiodelays.PitchShift(
            semitones=step_centre_semitones(STEPS), mix=1.0,
            window=self._window * width, overlap=self._overlap * width,
            **self._pcm(BLOCK * width)))
        self._shift.play(self._split.tap(1))
        self._line = self._own(audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=channels, max_delay_ms=LINE_MS,
            delay_frames=1, feedback=0.0, mix=2.0, damping_hz=0.0,
            cut_hz=0.0), reset=self._clear_line)
        self._line.play(self._shift)
        self._loop = self._own(audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=channels, max_delay_ms=LOOP_MS,
            delay_frames=self._loop_frames(), feedback=0.0, mix=0.0,
            damping_hz=0.0, cut_hz=0.0,
            loop_window_ms=self._window * 1000.0 / rate),
            reset=self._clear_loop)
        self._loop.play(self._line)
        # Not reset by the walk: neither voice holds a block between two
        # pulls (`_wire`), so there is nothing of its own to clear.
        self._mixer = self._own(audiomixer.Mixer(
            voice_count=2, buffer_size=BLOCK * width * 2,
            channel_count=channels, bits_per_sample=16,
            samples_signed=True, sample_rate=rate), reset=False)
        # The output: a width-1 MidSide, byte for byte, whose reset forwards
        # nothing. A host's reset of the output would otherwise reach the
        # Mixer, and CircuitPython's own Mixer handles that differently from
        # audiodsp's.
        self._tail = self._own(audioroute.MidSide(
            self._mixer, width=1.0, sample_rate=rate,
            channel_count=channels), reset=False)
        self._silence = audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)), sample_rate=rate,
            channel_count=channels)
        #: Where `audiocore.get_buffer` is compiled out, the one-voice
        #: mixer `_pull` primes from `_tail`; built the first time it is
        #: needed.
        self._puller = None
        self._output = self._head

    def _wire(self):
        """Play the voices, the first time the output reaches the mixer.

        A voice's `play()`, like the shifter's, primes a block from its
        source. With the Splitter on `_hush` that block is zeros, and one
        pull of the mixer hands it out, so wiring takes nothing from the
        borrowed source and leaves no voice holding a block: a reset or a
        return from Mix 0 never meets a block a voice is still waiting to
        play. The level gates are opened first, as
        `_component.open_level_gates` opens them."""
        voices = self._mixer.voice
        self._levels()
        for voice in voices:
            voice.play(self._silence, loop=True)
        self._pull()
        voices[0].play(self._split.tap(0))
        voices[1].play(self._loop)
        self._pull()
        self._in.play(self._head)
        self._clear_nodes(only=(self._shift, self._line, self._loop))
        self._wired = True
        # A control touched at Mix 0 before the first wiring marked the
        # graph stranded; wiring is what that mark waits for.
        self._stranded = False

    def _rearm(self):
        """Wire the graph again as the constructor does, once it has been
        cleared: a voice's new level is picked up at its next zero crossing
        unless the voice is played again, so a graph that is cleared while
        a level changes would otherwise carry the old level into the first
        frames. The input goes back to silence first, so no frame is taken
        from the borrowed source."""
        self._in.play(self._hush)
        self._wire()

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
            # smallest that hold a frame.
            self._puller = self._own(audiomixer.Mixer(
                voice_count=1, buffer_size=16,
                channel_count=self._channel_count, bits_per_sample=16,
                samples_signed=True, sample_rate=self._sample_rate),
                reset=False)
        voice = self._puller.voice[0]
        voice.play(self._tail)
        voice.stop()

    def _clear_line(self):
        self._line.clear()

    def _clear_loop(self):
        """Empty the loop. Its splicer goes back to the unshifted read, so
        its delay is set again for the read it will take."""
        self._loop.clear()
        self._engaged = self._loop_shift != 0.0
        self._loop.set(delay_frames=self._loop_frames())

    # -- the maps ------------------------------------------------------

    def _window_frames(self, window_ms):
        """The shifter's window in whole frames at the running rate."""
        return window_frames(window_ms, self._sample_rate)

    def _ratio(self, semitones):
        """The speed an interval of `semitones` reads at."""
        return 2.0 ** (semitones / 12.0)

    def _loop_semitones(self, step):
        """What the loop's splicer is handed: the shifter's own step."""
        return step_semitones(step)

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _pitch(self):
        """Pitch in whole semitones."""
        pitch = _rint(self._value(PITCH_I))
        return max(-12, min(12, pitch))

    def _mix(self):
        return max(0.0, min(2.0, self._value(MIX_I)))

    def macro(self, index):
        """What macro `index` currently stands for, in its own units; for
        Pitch, the whole semitones it plays."""
        self._check_live()
        if index == PITCH_I:
            return float(self._pitch())
        return _component.Component.macro(self, index)

    def _loop_frames(self):
        """The loop's delay: repeats fall every line delay plus half the
        window and crossfade, the first pass's mean. Once its splicer has
        run the loop reads half a window later of its own accord."""
        frames = self._delay_frames + (self._window + self._overlap) // 2
        if self._engaged:
            return frames - self._window * 0.5
        return frames

    def _level_pair(self):
        """The dry and the shifted voice's Mixer levels at this Mix."""
        mix = self._mix()
        return (min(1.0, 2.0 - mix), min(1.0, mix))

    def _levels(self):
        voices = self._mixer.voice
        pair = self._level_pair()
        voices[0].level = pair[0]
        voices[1].level = pair[1]
        self._applied = pair

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        if self._ready:
            self._refresh()

    def _apply_positions(self, positions, patch_index):
        """Set the knobs whole, then refresh the graph once: a patch and a
        rack's put-back after a reset both land here, so neither passes
        through a Mix 0 or a half-moved interval on the way."""
        ready = self._ready
        self._ready = False
        try:
            _component.Component._apply_positions(self, positions,
                                                  patch_index)
        finally:
            self._ready = ready
        if ready:
            self._refresh()

    def _refresh(self):
        rate = self._sample_rate
        cents = self._pitch() * 100.0 + self._value(FINE_I)
        step = ratio_step(self._ratio(cents / 100.0))
        self._step = step
        self._shift.semitones = step_centre_semitones(step)
        self._delay_frames = max(1, whole_frames(self._value(DELAY_I), rate))
        self._line.set(delay_frames=self._delay_frames)
        feedback = max(0.0, min(FEEDBACK_MAX, self._value(FEEDBACK_I)))
        self._feedback = feedback
        self._loop_shift = self._loop_semitones(step)
        if self._loop_shift != 0.0:
            self._engaged = True
        self._loop.set(loop_semitones=self._loop_shift,
                       delay_frames=self._loop_frames(),
                       feedback=feedback, mix=feedback)
        self._route()

    def _route(self):
        """Point the output at the source's reader at Mix 0, or at the
        mixer, emptying the shifter and both lines when it comes back."""
        if self._mix() <= 0.0:
            self._route_around(self._head)
            return
        if not self._wired:
            self._wire()
        elif self._rejoin():
            self._rearm()
        elif not self._taken and self._level_pair() != self._applied:
            # Not pulled yet: a level moved now would wait for its voice's
            # next zero crossing, a block of the old level, where an
            # instance built at this setting plays the new one from frame 0.
            # A move that leaves both levels alone has nothing to wait for.
            self._rearm()
        else:
            self._levels()
        self._output = self._tail

    @property
    def output(self):
        """The node the host plays. Asking for it is the host's first step
        to pulling, so from here a level that moves is an ordinary move."""
        self._check_live()
        self._taken = True
        return self._output

    def reset(self):
        """Empty the shifter and both lines, return to patch 0, and play
        from there as a new instance does."""
        wired = self._wired
        _component.Component.reset(self)
        if not wired:
            return
        if self._mix() > 0.0:
            self._rearm()
        else:
            # A rack's put-back can restore Mix 0: the output is the
            # source's reader, and the graph behind it waits to be armed
            # when Mix comes back up, as it does in a new instance.
            self._stranded = True

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops,
        as an upper bound.

        The shifter hands out what it holds for at most one window and
        crossfade after its input stops, the line adds its delay, and the
        loop then goes round `laps_to_zero(Feedback)` times, each lap at
        most its delay plus the window its splicer reads across, and a frame
        for the read between two. At Feedback 0 the loop is a wire."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        if self._mix() <= 0.0:
            return 0
        reach = self._delay_frames + self._window + self._overlap + 1
        if self._feedback <= 0.0:
            return reach
        lap = int(math.ceil(self._loop_frames())) + self._window + 2
        return reach + laps_to_zero(self._feedback) * lap
