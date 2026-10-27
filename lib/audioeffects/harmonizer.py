"""`Harmonizer` - a harmony of pitch-shifted voices.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests. How the graph works is told
where it is built, in `Harmonizer._build`.
"""

VENDOR = "PyDevices"

import math

import audiocore

from . import _component

try:
    import audiodelays
    import audiomixer
    import audioroute
except ImportError:                     # pragma: no cover - a stock board
    audiodelays = audiomixer = audioroute = None


PITCH_I = 0
VOICE_I = (1, 2, 3)
LEVEL_I = (4, 5, 6)
DETUNE_I = 7
SPREAD_I = 8
MIX_I = 9

#: Frames a mixer pull hands out, and so what every node and tap takes per
#: pull.
BLOCK = 256

#: The Level span, in dB. MIDI 1 is -40 dB and 127 is 0 dB, 40/126 dB a
#: step; MIDI 0 sits one step below -40 and turns the voice off.
LEVEL_TOP_DB = 0.0
LEVEL_FLOOR_DB = -40.0
LEVEL_OFF_DB = LEVEL_FLOOR_DB - (LEVEL_TOP_DB - LEVEL_FLOOR_DB) / 126.0

DETUNE_MAX_CENTS = 25.0

WINDOW_MIN_MS = 5.0
WINDOW_MAX_MS = 60.0
#: 1024 frames at 48 kHz.
WINDOW_DEFAULT_MS = 1024.0 / 48.0

#: The constructor's macro defaults, which NaN falls back to (patch 0).
DEFAULTS = (0.0, 4.0, 7.0, -12.0, -6.0, -6.0, -9.0, 0.0, 0.0, 1.0)

#: The shifter reads its line at `floor(256 * 2^(semitones / 12))` 256ths
#: of a frame per frame.
STEPS = 256


def ratio_step(semitones):
    """The shifter's nearest read-rate step, in 256ths, to an interval."""
    return int(math.floor(STEPS * 2.0 ** (semitones / 12.0) + 0.5))


def step_semitones(step):
    """The interval at the centre of read-rate step `step`: the node's
    floor lands on `step` from it, with half a step to spare either way,
    in single precision as in double."""
    return 12.0 * math.log((step + 0.5) / STEPS) / math.log(2.0)


def whole(value):
    """A Pitch or Voice value as the whole semitone it plays."""
    return int(math.floor(value + 0.5))


def mix_gains(mix):
    """(dry, voice) gain at Mix `mix`: the dry at unity up to 1, then
    2 - Mix; each voice at Mix, capped at 1."""
    mix = min(2.0, max(0.0, mix))
    return (1.0 if mix <= 1.0 else 2.0 - mix), min(mix, 1.0)


def level_gain(db):
    """A Level in dB as a gain; 0 for the bottom step, which is off."""
    if db < LEVEL_FLOOR_DB:
        return 0.0
    return 10.0 ** (db / 20.0)


def _number(value, default):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("expected a number, not %r" % (value,))
    if value != value:
        return default
    return value


class Harmonizer(_component.Component):
    """Three pitch shifters, each a fixed interval from your note, blended
    under the dry: the rig of three Eventide H910s played from one
    keyboard, so one singer is three-part harmony.

    **The controls.** Voice 1 to Voice 3 set each voice's interval in whole
    semitones, and Pitch moves all three together. Level 1 to Level 3 set
    each voice's level, and the bottom step turns the voice off. Detune
    pulls voice 1 down and voice 2 up. Spread pans voice 1 left and voice 2
    right; the dry and voice 3 stay in the centre. Mix holds the dry at
    unity up to 1 while the voices rise to their Levels; from 1 to 2 the
    dry fades, and at 2 the voices play alone. Constructor values land on
    the nearest of each knob's 128 steps; `window_ms`, 5 to 60 ms (21.33 by
    default), is fixed for good. The Effect controls page lists what the
    knobs span.

    **What you hear.** Each voice is its own machine: turning one on or
    off never changes the dry or the other voices.
    Each voice sits on the closest pitch its shifter can make: within 3.4
    cents of its interval from unison up, 6.8 cents down to an octave
    below and 13.7 cents below that.
    So Detune moves in steps of about 7 cents near unison, and voices 1
    and 2 sit evenly apart only to within a step.
    Detune is a steady offset, not a chorus: a voice holds its pitch.
    Each voice glitches as it splices, more often the further it is
    shifted and the shorter the window: at the default window a fifth up
    splices every 43 ms, at any sample rate, where the first channel is
    silent.
    Where it is not, each splice moves by up to a fiftieth of a second to
    land in phase, so the splices come sooner.
    A voice at exact unison never splices: it is a fixed short delay, and
    it combs with the dry.
    A voice you turn back on starts from silence, not with a scrap of what
    it played before.

    **Limits.** It moves notes by fixed intervals and does not listen for
    the key.
    Each voice rounds off peaks above about -1.4 dBFS.
    The voices add to the dry: at patch 0 an input that peaks at or below
    13 900 (-7.4 dBFS) cannot reach full scale.
    Patch 6 is patch 0 without the octave below, for a board that cannot
    run three voices in time.
    The shifter reads its line without interpolation, which you may hear
    as grit on a shifted voice.
    On a mono source Spread does nothing.
    An interval move leaves each voice's splice where it was.
    A control that jumps makes the output step: move it in small steps
    from the host if you need it smooth.

    **Wire, latency, tail.** At Mix 0 the output is the input, byte for
    byte.
    There is no latency: the dry is a wire, and each shifted voice trails
    it by between the crossfade, a sixteenth of the window, and the whole
    window.
    `tail_samples` covers the window, the crossfade and one block, and is
    0 at Mix 0 or with every voice off.
    `reset()` empties the three lines, starts their splices where a new
    instance's start, and returns to patch 0.
    On CircuitPython's own pitch shifter a reset does not restart the
    splices.
    The class never reads the host's tempo.
    """

    NAME = 'Harmonizer'
    DISPLAY_NAME = 'Harmonizer'
    CATEGORIES = ('Pitch Shift',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioroute",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    #: The loudest sum over every setting is the dry at unity and all three
    #: Levels at 0 dB at Mix 1: 4.0 times the input (patch 1 with Level 3
    #: at 0 dB sums 3.44), so -12.1 dBFS keeps it inside full scale
    #: (4.0 times is 12.04 dB, and -12.0 would leave the sum 0.5 % over).
    INPUT_CEILING_DBFS = -12.1

    MACRO_LABELS = ("Pitch", "Voice 1", "Voice 2", "Voice 3", "Level 1",
                    "Level 2", "Level 3", "Detune", "Spread", "Mix")
    MACRO_MODES = {0: "BIPOLAR", 1: "BIPOLAR", 2: "BIPOLAR", 3: "BIPOLAR",
                   4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR",
                   7: "UNIPOLAR", 8: "UNIPOLAR", 9: "UNIPOLAR"}
    _MACRO_RANGES = (
        (-12.0, 12.0),                      # 0  Pitch, semitones
        (-12.0, 12.0),                      # 1  Voice 1, semitones
        (-12.0, 12.0),                      # 2  Voice 2
        (-12.0, 12.0),                      # 3  Voice 3
        (LEVEL_OFF_DB, LEVEL_TOP_DB),       # 4  Level 1, dB; MIDI 0 = off
        (LEVEL_OFF_DB, LEVEL_TOP_DB),       # 5  Level 2
        (LEVEL_OFF_DB, LEVEL_TOP_DB),       # 6  Level 3
        (0.0, DETUNE_MAX_CENTS),            # 7  Detune, cents
        (0.0, 1.0),                         # 8  Spread
        (0.0, 2.0),                         # 9  Mix; dry at unity to 1
    )
    _MACRO_UNITS = {
        0: "semitones", 1: "semitones", 2: "semitones", 3: "semitones",
        4: "dB", 5: "dB", 6: "dB", 7: "cents",
    }

    #: `_component.macro_of` of the card's settings: +3/+4/+5/+7/+12 are
    #: 80/85/90/101/127 and -12 is 0; -3/-6/-9/-12 dB are 118/108/99/89 and
    #: off is 0; 14 cents is 71; Spread 0.5 and Mix 1 are 64.
    PATCHES = {
        0: ("Third and fifth above, octave below",
            (64, 85, 101, 0, 108, 108, 99, 0, 0, 64)),
        1: ("Octave below, doubled",
            (64, 0, 0, 64, 118, 118, 0, 71, 64, 64)),
        2: ("Wide unison",
            (64, 64, 64, 64, 108, 108, 0, 71, 127, 64)),
        3: ("Fourths and fifths",
            (64, 90, 101, 127, 99, 99, 89, 0, 64, 64)),
        4: ("Octave up and down",
            (64, 127, 0, 64, 108, 108, 0, 0, 64, 64)),
        5: ("Minor triad, voices alone",
            (64, 80, 101, 64, 108, 108, 108, 0, 64, 127)),
        6: ("Third and fifth - lean",
            (64, 85, 101, 0, 108, 108, 0, 0, 0, 64)),
    }

    def _build(self, pitch=0.0, voice1=4.0, voice2=7.0, voice3=-12.0,
               level1_db=-6.0, level2_db=-6.0, level3_db=-9.0,
               detune_cents=0.0, spread=0.0, mix=1.0,
               window_ms=WINDOW_DEFAULT_MS, patch=None):
        grid = self._grid((pitch, voice1, voice2, voice3, level1_db,
                           level2_db, level3_db, detune_cents, spread, mix))
        window_ms = _number(window_ms, WINDOW_DEFAULT_MS)
        self._window_ms = min(WINDOW_MAX_MS, max(WINDOW_MIN_MS, window_ms))
        rate = self._sample_rate
        channels = self._channel_count
        self._ready = False
        self._armed = False
        #: Which voices play their shifter; the others play their tap, silenced.
        self._on = [True, True, True]
        self._puller = None

        # The borrowed source's only reader: a width-1 MidSide is the source
        # byte for byte, in whole 256-frame blocks whatever buffers the
        # source hands out. At Mix 0 the output is this node, and the
        # Splitter reads it too, so routing around the graph and back never
        # skips or repeats a source frame.
        self._head = self._own(audioroute.MidSide(
            self._source, width=1.0, sample_rate=rate,
            channel_count=channels), reset=False)
        # A MidSide with no source hands out one block of zeros per pull.
        # The Splitter reads it while the voices are armed (`_arm`), so
        # arming takes nothing from the source.
        self._hush = self._own(audioroute.MidSide(
            width=1.0, sample_rate=rate, channel_count=channels),
            reset=False)
        self._in = self._own(audioroute.Port(self._hush), reset=False)
        split = self._own(audioroute.Splitter(self._in, taps=4),
                          reset=False)
        self._taps = [split.tap(i) for i in range(4)]

        # Three shifters, each on its own tap: each voice is its own
        # machine, with its own line and its own splice rate.
        frames = self._window_frames()
        self._frames = frames
        self._overlap = frames // 16
        self._shifters = []
        for k in range(3):
            shifter = self._own(self._shifter(frames, self._overlap))
            shifter.play(self._taps[k + 1], loop=True)
            self._shifters.append(shifter)

        # Each mixer voice plays a Port, so switching a voice between its
        # shifter and its silenced tap re-points the port and primes nothing.
        self._ports = [self._own(audioroute.Port(self._taps[0]),
                                 reset=False)]
        for k in range(3):
            self._ports.append(self._own(audioroute.Port(self._shifters[k]),
                                         reset=False))
        # What a voice that is off plays: its tap, held at level 0 for good.
        self._drains = []
        self._feeds = []
        for k in range(3):
            feed = self._own(audioroute.Port(self._hush), reset=False)
            drain = self._own(audiomixer.Mixer(
                voice_count=1, **self._pcm(1024 * channels)), reset=False)
            drain.voice[0].level = 0.0
            drain.voice[0].play(feed, loop=True)
            # Its play() primed a block of the hush; one pull drops it, so
            # the drain holds nothing when it first reads its tap.
            drop = audiomixer.Mixer(voice_count=1, **self._pcm(16))
            drop.voice[0].play(drain)
            drop.voice[0].stop()
            drop.deinit()
            self._feeds.append(feed)
            self._drains.append(drain)
        # Not reset by the walk: no voice holds a block between two pulls.
        self._mixer = self._own(audiomixer.Mixer(
            voice_count=4, **self._pcm(1024 * channels)), reset=False)
        # A voice's play() primes a block; with the Splitter on the hush it
        # is zeros, and one pull drops it.
        for i in range(4):
            self._mixer.voice[i].play(self._ports[i], loop=True)
        # The output: a width-1 MidSide, byte for byte, whose reset forwards
        # nothing, so a host's reset of the output never reaches the Mixer.
        self._tail = self._own(audioroute.MidSide(
            self._mixer, width=1.0, sample_rate=rate,
            channel_count=channels), reset=False)
        self._output = self._tail
        self._pull()

        self._init_macros(tuple(
            _component.macro_value(self._MACRO_RANGES[i],
                                   _component.position_of_midi(
                                       self._mode(i), grid[i]))
            for i in range(10)))
        # Land each knob exactly on its step, as patch 0 does.
        for i in range(10):
            self._macros[i] = _component.position_of_midi(self._mode(i),
                                                          grid[i])
        # A constructor patch lands before the voices are first armed, so
        # their level gates open at the patch's levels.
        if patch is not None:
            self.program_change(patch)
        self._ready = True
        self._refresh()

    def _grid(self, asked):
        """Each constructor value as its knob's nearest MIDI step: NaN is
        the default, anything past a stop is that stop, and a Level below
        -40 dB is off."""
        grid = []
        for i in range(10):
            value = _number(asked[i], DEFAULTS[i])
            span = self._MACRO_RANGES[i]
            if i in LEVEL_I and value < LEVEL_FLOOR_DB:
                grid.append(0)
                continue
            low = LEVEL_FLOOR_DB if i in LEVEL_I else span[0]
            value = min(span[1], max(low, value))
            grid.append(_component.macro_of(span, value, self._mode(i)))
        return grid

    # -- the parts; each a method, so a test can plant a fault in one -----

    def _window_frames(self):
        """The window in frames, from milliseconds at the running rate."""
        return max(1, int(self._window_ms * self._sample_rate / 1000.0
                          + 0.5))

    def _shifter(self, frames, overlap):
        width = 2 * self._channel_count
        return audiodelays.PitchShift(
            semitones=0.0, mix=1.0, window=frames * width,
            overlap=overlap * width, **self._pcm(BLOCK * width))

    def _voice_source(self, k):
        """What voice `k` (0, 1, 2) plays while it is on: its shifter."""
        return self._shifters[k]

    def _off_source(self, k):
        """What voice `k` plays while it is off: its tap through a
        one-voice mixer that has only ever been at level 0. The voice reads
        the tap, which keeps the split even and does not pull its shifter,
        and plays silence from the first frame; the bare tap would play the
        dry at the voice's old level until the voice's level gate closed.
        The mixer's own voice never plays again, so nothing is primed from
        the live tap when a voice goes off."""
        self._feeds[k].play(self._taps[k + 1])
        return self._drains[k]

    def _empty(self, k):
        """Empty voice `k`'s line before it comes back on."""
        audiocore.reset_buffer(self._shifters[k])

    def _semitones(self, k):
        """What voice `k` (0, 1, 2) asks for: Pitch + Voice + its share of
        Detune (voice 1 down, voice 2 up, voice 3 none)."""
        detune = self._value(DETUNE_I) / 100.0
        share = (-detune, detune, 0.0)[k]
        return (whole(self._value(PITCH_I))
                + whole(self._value(VOICE_I[k])) + share)

    def _node_semitones(self, asked):
        """The nearest step the node can play, handed over at its centre."""
        return step_semitones(ratio_step(asked))

    def _level(self, k):
        return level_gain(self._value(LEVEL_I[k]))

    def _dry_level(self):
        return mix_gains(self._value(MIX_I))[0]

    def _voice_level(self, k):
        return self._level(k) * mix_gains(self._value(MIX_I))[1]

    def _pans(self):
        spread = min(1.0, max(0.0, self._value(SPREAD_I)))
        return (0.0, -spread, spread, 0.0)

    # -- the controls ----------------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _apply_macro(self, index, position):
        del index, position
        if self._ready:
            self._refresh()

    def _apply_positions(self, positions, patch_index):
        """Apply a patch (or a rack's restore) whole, then set the graph
        once."""
        ready = self._ready
        self._ready = False
        try:
            _component.Component._apply_positions(self, positions,
                                                  patch_index)
        finally:
            self._ready = ready
        if ready:
            self._refresh()

    def reset(self):
        """Empty the three lines, return their splices to a new node's
        start, and restore patch 0 (or, under a rack, what the rack built
        this with)."""
        self._check_live()
        self._clear_nodes()
        self._stranded = False
        # The voices are armed again, as the constructor arms them, the
        # next time the output reaches the mixer.
        self._armed = False
        if self._reset_to is None:
            self.program_change(0)
        else:
            self._restore(self._reset_to)

    def _refresh(self):
        for k in range(3):
            self._shifters[k].semitones = self._node_semitones(
                self._semitones(k))
        self._route()

    def _wanted(self, k):
        return self._level(k) > 0.0

    def _levels(self):
        voices = self._mixer.voice
        pans = self._pans()
        voices[0].level = self._dry_level()
        for k in range(3):
            voices[k + 1].level = self._voice_level(k)
        if self._channel_count == 2:
            for i in range(4):
                voices[i].panning = pans[i]

    def _route(self):
        """Mix 0 hands out the source; anything else plays the mixer, armed
        again if the graph was left or reset."""
        if self._macros[MIX_I] <= 0.0:
            self._route_around(self._head)
            return
        if self._rejoin() or not self._armed:
            self._arm()
        else:
            self._switch()
        self._output = self._tail

    def _switch(self):
        """Turn voices on and off. A voice going off plays its tap through
        a mixer held at level 0, so the split stays even, its shifter is
        not pulled and the dry never leaks at the voice's old level; a
        voice coming back empties its shifter's line, plays it, then takes
        its level."""
        voices = self._mixer.voice
        for k in range(3):
            wanted = self._wanted(k)
            if wanted == self._on[k]:
                continue
            if wanted:
                self._empty(k)
                self._ports[k + 1].play(self._voice_source(k))
            else:
                voices[k + 1].level = 0.0
                self._ports[k + 1].play(self._off_source(k))
            self._on[k] = wanted
        self._levels()

    def _arm(self):
        """Arm the voices, the same way every time: with the Splitter on
        the hush and every voice on its shifter, one pull of the mixer opens
        the voices' level gates on zeros and leaves no voice and no shifter
        holding a block. Then every line is emptied, which also puts its
        splice where a new node's starts, the Splitter goes back to the
        source and the voices that are off go to their taps. So a reset, a
        return from Mix 0 and a voice turned back on all start their
        shifters exactly as the constructor does."""
        self._levels()
        self._in.play(self._hush)
        for k in range(3):
            self._ports[k + 1].play(self._voice_source(k))
        self._pull()
        for k in range(3):
            audiocore.reset_buffer(self._shifters[k])
        self._in.play(self._head)
        for k in range(3):
            self._on[k] = self._wanted(k)
            if not self._on[k]:
                self._ports[k + 1].play(self._off_source(k))
        self._armed = True

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
                voice_count=1, **self._pcm(16)), reset=False)
        voice = self._puller.voice[0]
        voice.play(self._tail)
        voice.stop()

    @property
    def tail_samples(self):
        """The shifters' lines, every one overwritten, and a block."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        if self._macros[MIX_I] <= 0.0:
            return 0
        if not (self._wanted(0) or self._wanted(1) or self._wanted(2)):
            return 0
        return self._frames + self._overlap + BLOCK

    @property
    def window_ms(self):
        """The window the instance was built with, in milliseconds."""
        self._check_live()
        return self._window_ms
