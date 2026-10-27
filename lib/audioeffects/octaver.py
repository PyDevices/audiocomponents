"""`Octaver` - the analog octave-down.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests. How the graph works is told
where it is built, in `Octaver._build`.
"""

VENDOR = "PyDevices"

from array import array

import audiocore

from . import _component

try:
    import audiobiquad
    import audiomath
    import audiomixer
    import audioroute
    import audioshaper
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = audiomath = audiomixer = audioroute = audioshaper = None


DIRECT_I, OCTAVE1_I, OCTAVE2_I, TRACKING_I, TONE1_I, TONE2_I, SENS_I = \
    range(7)

#: The constructor defaults, which NaN falls back to (patch 0).
DEFAULTS = (1.0, 0.7, 0.0, 90.0, 324.0, 70.3, -80.0)

#: The comparator's table: 4097 points over the shaper's -1..1, exact zero
#: across |i - 2048| <= 7, a tick of +-TICK out to |i - 2048| = 63, and the
#: rails beyond. Interpolating between two points of a one-point step is a
#: gain stage, which leaks an octave up and DC below Sensitivity; a dead band
#: many points wide reads exact zero.
#:
#: The rails are Sensitivity: only they reach the octave. The ticks clock the
#: dividers 18 dB under it, so a clock whose peaks are unequal (a second
#: harmonic the tracking low-pass left, or the last few LSB of a quiet one)
#: has crossed both sides by the time either side reaches a rail. Clocked on
#: the rails alone, such a clock crossed one rail and not the other: the
#: divider never turned over, and the signal times its one-sided pulses was
#: the dry note itself.
CURVE_POINTS = 4097
DEAD_HALF = 63
TICK_HALF = 7
TICK = 2
#: The comparator reaches the rail where its input times `pre_gain` is
#: 64/2048, so `pre_gain = EDGE / 10^(Sensitivity/20)` puts the rail at the
#: clock's level of Sensitivity. 1/32 is exact in every float format.
EDGE = 0.03125

#: The clock filters' Q: two sections of 0.5 are four coincident real
#: poles, whose phase a two-stage first-order all-pass matches exactly.
CLOCK_Q = 0.5
TONE_Q = 0.7071

#: The clock's slow mean: three first-order low-passes at MEAN_HZ in a row,
#: which `_centre` takes out of the clock before the comparator. A direct
#: offset in the input passes the Tracking low-pass whole where a high
#: note's fundamental does not, so the comparator's zero sat outside the
#: clock; with the mean taken out the zero follows the clock's own centre.
#: Each pole is an all-pass at half mix, which is exactly 1 at DC however
#: low the corner (a low-pass biquad at 10 Hz is not: its coefficients
#: round in single precision and its DC gain reads 0.90 to 1.24). Three
#: poles make what is subtracted fall as the cube of the frequency, so the
#: clock's phase at the note moves by less than a degree (A2) and the square
#: still turns over on the signal's own crossings; a high-pass at the same
#: corner would lead by 10 degrees there and move the octave's level. The
#: corner is a trade between two rows: the mean forgets the attack's step
#: in about 50 ms at 20 Hz, where at 10 Hz a note above the range (E5) kept
#: a pulse in its clock past 125 ms and played for that long, and from
#: 30 Hz the A2 decay's spread and seed-7 level move.
MEAN_HZ = 20.0
MEAN_POLES = 3

#: The dividers turn over on the comparator's ticks: one LSB, under TICK.
CLOCK_THRESHOLD = 1.0 / 32768.0
CLOCK_HOLD_MS = 1.0

#: The table after each divider: the identity, with exact zero for
#: |x| < 16 LSB, which takes the ticks out of the square and leaves its rails
#: as they are.
GATE_HALF = 1

#: Frames a mixer pull hands out, and so what every node and tap takes per
#: pull: the palette's own block, so the Splitters' rings empty each pull.
BLOCK = 256

_CURVE = None
_GATE = None


def comparator_curve():
    """The comparator's table, built once and shared by every instance."""
    global _CURVE
    if _CURVE is None:
        rail = (CURVE_POINTS - 1) // 2 - DEAD_HALF
        tick = DEAD_HALF - TICK_HALF
        _CURVE = array("h", [-32767] * rail + [-TICK] * tick
                       + [0] * (2 * TICK_HALF + 1) + [TICK] * tick
                       + [32767] * rail)
    return _CURVE


def gate_curve():
    """The table after each divider, built once and shared."""
    global _GATE
    if _GATE is None:
        middle = (CURVE_POINTS - 1) // 2
        _GATE = array("h", [0] * CURVE_POINTS)
        for i in range(CURVE_POINTS):
            step = i - middle
            if abs(step) > GATE_HALF:
                _GATE[i] = max(-32767, min(32767, 16 * step))
        _GATE[1] = -32767
        _GATE[CURVE_POINTS - 2] = 32767
    return _GATE


def pre_gain(sensitivity_db):
    """The comparator's input gain for a Sensitivity in dBFS."""
    return EDGE / (10.0 ** (sensitivity_db / 20.0))


def _allpass_ring(coefficient):
    """Frames two first-order all-pass sections ring for, as an upper
    bound: the cascade is a repeated real pole at -coefficient, which
    `_component.biquad_ring` bounds as a biquad with that double pole."""
    a = -coefficient

    class _Pole:
        coefficients = (1.0, 0.0, 0.0, -2.0 * a, a * a)
    return _component.biquad_ring(_Pole)


class Octaver(_component.Component):
    """An octave down that is your own note: like the Boss OC-2, it turns
    every other cycle of what you play upside down, so the octave keeps
    your attack, your decay and your tone.

    **The controls.** Direct is your own note's level, and the Octave knobs
    set the octaves'. Tracking moves the range of notes the divider
    follows. Tone 1 and Tone 2 are two-pole low-passes at the hertz they
    show, on the first and second octave. Sensitivity is the level your
    note must keep after Tracking's low-pass for the octaves to play, not
    the level you play at. The higher the note, the more that low-pass
    takes, so a quiet high note stops before a quiet low one: at patch 0 a
    sine at -60 dBFS still has its octave on E2 and none on E4. Constructor
    values land on the nearest of each knob's 128 steps. The Effect
    controls page lists what the knobs span.

    **What you hear.** The octave is exactly half your note and sounds
    within 2 ms of it.
    Octave 2 is Octave 1 divided again: two octaves down, not a fourth
    below the note, until Octave 1 itself stops.
    On an A2 the octave follows your note's decay within 1 dB: it has no
    envelope of its own.
    Below Sensitivity the octaves are silent, with no ghost and no hum,
    and as a note fades into it the octave never turns into the note
    itself.
    With the Tones open the octave carries a fifth above it 4.4 dB
    quieter, as the pedal's multiplication does, wherever Tracking is set.
    Turning Tone 1 down thins that fifth more on high notes than on low
    ones.

    **Its range.** Played at -8.7 dBFS peak, every note at patch 0 from
    low E (E2) to A4 divides cleanly, even with a strong second harmonic.
    Played at -8.7 dBFS peak, the Bass patch covers E1 to G3, and High on
    the neck covers D3 to E5; played quieter, each range ends lower.
    Below the range a low note's second harmonic clocks the divider and it
    skips; above it the clock is low-passed under Sensitivity and the
    octave goes silent.
    Between -90 and -84.5 dBFS Sensitivity changes nothing: that whole
    stretch is one step of the clock.
    A direct offset in the input, as a plucked string rings round, does not
    take the top of the range from you: the divider turns over on the
    clock's own centre, not on zero.

    **Limits.** It plays one note at a time: on a power chord (A2 and E3)
    about two fifths of the octave is intermodulation.
    A stereo source is clocked on its mid: with the right channel 45
    degrees ahead of the left, the fifth sits 3.2 dB under the octave
    instead of 4.4, on both channels.
    The output can peak at about 5 times the input (a low square, all
    three levels at full with the Tones open), so keep the input under
    -15 dBFS.
    A control that jumps makes the output step: move it in small steps
    from the host if you need it smooth.

    **On an ESP32-S3, Both octaves can't keep up and the sound breaks up;
    play Both octaves - lean instead.** It has the same balance of your
    note and the two octaves, 2 dB louder: turn the level after it down
    2 dB and you hear Both octaves.

    **Wire, latency, tail.** With both octaves at 0 and Direct at 1 the
    output is the input, byte for byte, however the host's buffers are
    cut.
    There is no latency.
    `tail_samples` covers the all-pass and the two Tone filters ringing
    down.
    `reset()` clears the filters and the dividers and returns to patch 0.
    The class never reads the host's tempo.
    """

    NAME = 'Octaver'
    DISPLAY_NAME = 'Octaver'
    CATEGORIES = ('Pitch Shift',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioroute", "audiobiquad", "audioshaper", "audiomath")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    #: The worst peak gain is 5.03: a square near E2 with all three levels
    #: at full, the Tones open and Tracking at 40 Hz, over every semitone
    #: from E1 to A2 at both Tracking stops (the kit's own 100 Hz square
    #: reads 3.75). -15 dBFS keeps it 1 dB inside full scale.
    INPUT_CEILING_DBFS = -15.0

    MACRO_LABELS = ("Direct", "Octave 1", "Octave 2", "Tracking", "Tone 1",
                    "Tone 2", "Sensitivity")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR", 5: "UNIPOLAR",
                   6: "UNIPOLAR"}
    _MACRO_RANGES = (
        (0.0, 1.0),                     # 0  Direct
        (0.0, 1.0),                     # 1  Octave 1
        (0.0, 1.0),                     # 2  Octave 2
        (40.0, 400.0, "log"),           # 3  Tracking, Hz
        (100.0, 2000.0, "log"),         # 4  Tone 1, Hz
        (40.0, 800.0, "log"),           # 5  Tone 2, Hz
        (-90.0, -40.0),                 # 6  Sensitivity, dBFS
    )
    _MACRO_UNITS = {3: "Hz", 4: "Hz", 5: "Hz", 6: "dBFS"}

    #: `_component.macro_of` of the card's settings: 0.7 is 89, 0.8 is 102,
    #: 0.6 is 76; Tracking 90/50/200 Hz is 45/12/89; Tone 1 324/250/700 Hz
    #: is 50/39/82; Tone 2 70.3 Hz is 24; Sensitivity -80 dBFS is 25.
    #: Patch 6 is patch 1 with Direct at 1 and both octaves at 111 (0.874),
    #: the same balance 1.9 dB up. A mixer voice at exactly 1 passes its
    #: samples through with no multiply, which is the 0.07 ms an ESP32-S3
    #: lacks for patch 1, where all three levels are under 1.
    PATCHES = {
        0: ("Octave down under the dry", (127, 89, 0, 45, 50, 24, 25)),
        1: ("Both octaves", (102, 89, 89, 45, 50, 24, 25)),
        2: ("Octaves alone, no dry", (0, 127, 76, 45, 50, 24, 25)),
        3: ("Bass guitar", (127, 102, 0, 12, 39, 24, 25)),
        4: ("High on the neck", (127, 89, 0, 89, 82, 24, 25)),
        5: ("Two octaves down alone", (0, 0, 127, 45, 50, 24, 25)),
        6: ("Both octaves - lean", (127, 111, 111, 45, 50, 24, 25)),
    }

    def _build(self, direct=1.0, octave1=0.7, octave2=0.0, tracking_hz=90.0,
               tone1_hz=324.0, tone2_hz=70.3, sensitivity_db=-80.0,
               patch=None):
        grid = self._grid((direct, octave1, octave2, tracking_hz, tone1_hz,
                           tone2_hz, sensitivity_db))
        rate = self._sample_rate
        channels = self._channel_count
        self._ready = False
        self._armed = False

        self._silence = self._own(audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels), reset=False)

        # The input adapter: a width-1 MidSide, the identity byte for byte,
        # that hands the source on in the palette's 256-frame blocks. The
        # Splitter reads it, and the wire hands it out, so whatever part of
        # a source buffer it holds plays next whichever way the output
        # goes. Handing out the source itself skipped what the adapter, the
        # Splitter and the dry voice had read ahead whenever the host's
        # buffers were not 256 frames.
        self._adapter = self._own(audioroute.MidSide(
            width=1.0, sample_rate=rate, channel_count=channels),
            reset=False)
        self._adapter.play(self._source)

        # The graph reads the adapter through a Port. While the voices are
        # armed it plays a MidSide with no source instead, one block of
        # zeros per pull, which the arming pull drops (`_arm`): arming
        # takes nothing from the source, so no voice ever holds a block the
        # wire would skip.
        self._hush = self._own(audioroute.MidSide(
            width=1.0, sample_rate=rate, channel_count=channels),
            reset=False)
        self._in = self._own(audioroute.Port(self._hush), reset=False)

        # One Splitter, three legs: the dry voice, the signal the octaves
        # are made of, and the clock that says when to turn it over. The
        # clock and the signal are kept apart because `SubOctave` clocks on
        # what it divides, so a tracking filter in front of it would darken
        # the octave too (12 dB from E2 to G3, measured on the card's
        # probes).
        split = self._own(audioroute.Splitter(self._in, taps=3),
                          reset=False)
        self._dry = split.tap(0)
        self._allpass = None
        self._clock = []
        self._mean = []
        signal = self._own(audioroute.Splitter(
            self._signal_leg(split.tap(1)), taps=2), reset=False)
        ticks = self._own(audioroute.Splitter(
            self._clock_leg(split.tap(2)), taps=2), reset=False)
        self._divider = self._first(ticks.tap(0))
        self._product = self._octave(signal.tap(0), self._divider)
        self._tone1 = self._tone(self._product, 324.0)
        self._octave1 = self._tone1

        # Octave 2 is the pedal's second flip-flop, clocked by the first:
        # the signal times a square at a quarter of the note, made from the
        # same comparator, so it turns over on the crossings Octave 1 does.
        # Divided on Octave 1's own waveform instead, the divider also
        # counted the near-zero junctions where the multiplication's humps
        # meet, and on a decaying note it turned into a fourth below.
        self._product2 = self._second(signal.tap(1), ticks.tap(1))
        self._tone1b = self._tone(self._product2, 324.0)
        self._tone2 = self._tone(self._tone1b, 70.3)

        # Not reset: no voice holds a block between two pulls (`_arm`), and
        # a Mixer reset is no reset of anything this class holds. A Mixer
        # renders half its buffer per pull, so BLOCK frames take four bytes
        # a sample: with half that, every other pull left a voice holding
        # half a block, which a move into the wire then skipped.
        self._mixer = self._own(audiomixer.Mixer(
            voice_count=3, **self._pcm(BLOCK * channels * 4)), reset=False)
        # The mixer's output: a width-1 MidSide, byte for byte, whose reset
        # forwards nothing. A host's reset of the output (a mixer voice's
        # `play()` does one) would otherwise reach the Mixer, and
        # CircuitPython's own Mixer drops its voices' blocks on one.
        self._tail = self._own(audioroute.MidSide(
            self._mixer, width=1.0, sample_rate=rate,
            channel_count=channels), reset=False)
        #: Where `audiocore.get_buffer` is compiled out, the one-voice
        #: mixer `_pull` primes from `_tail`; built the first time it is
        #: needed.
        self._puller = None
        self._output = self._tail

        self._init_macros(tuple(
            _component.macro_value(self._MACRO_RANGES[i], grid[i] / 127.0)
            for i in range(7)))
        # Land each knob exactly on its step, as patch 0 does.
        for i in range(7):
            position = _component.position_of_midi("UNIPOLAR", grid[i])
            if self._macros[i] != position:
                self._macros[i] = position
                self._apply_macro(i, position)
        # The patch lands before the voices are armed, so the instance
        # starts at it: loaded after, the all-pass walked its first block
        # from patch 0's Tracking and each level waited for a crossing, and
        # `patch=` did not build what the patch's own values build.
        if patch is not None:
            self.program_change(patch)

        self._ready = True
        self._route()

    def _grid(self, asked):
        """Each constructor value as its knob's nearest MIDI step: NaN is
        the default, anything past a stop is that stop."""
        grid = []
        for i in range(7):
            value = float(asked[i])
            if value != value:
                value = DEFAULTS[i]
            span = self._MACRO_RANGES[i]
            value = min(span[1], max(span[0], value))
            grid.append(int(round(
                127.0 * _component.macro_position(span, value))))
        return grid

    # -- the legs; each a method, so a test can plant a fault in one ------

    def _signal_leg(self, tap):
        """Two first-order all-pass sections at Tracking. The clock's two
        Q 0.5 sections are four coincident real poles, whose phase is
        exactly this cascade's, so the square turns over on the signal's own
        zero crossings and the octave keeps the multiplication's balance."""
        self._allpass = self._own(audiobiquad.AllPass(
            stages=2, frequency=90.0, feedback=0.0, mix=1.0,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._allpass.play(tap)
        return self._allpass

    def _mid(self, tap):
        """A stereo clock runs on the mid, so both channels turn over on
        the same crossings; a mono one runs on the tap."""
        if self._channel_count != 2:
            return tap
        mid = self._own(audioroute.MidSide(
            width=0.0, sample_rate=self._sample_rate, channel_count=2))
        mid.play(tap)
        return mid

    def _clock_leg(self, tap):
        """Low-pass at Tracking and a comparator with a dead band: a
        +-rail square at the note, a tick of +-TICK while the clock is
        under Sensitivity and over 18 dB under it, zero below that."""
        clock = self._mid(tap)
        for _ in range(2):
            section = self._own(audiobiquad.Biquad(
                mode=audiobiquad.LOW_PASS, frequency=90.0, Q=CLOCK_Q,
                mix=1.0, sample_rate=self._sample_rate,
                channel_count=self._channel_count))
            section.play(clock)
            clock = section
            self._clock.append(section)
        clock = self._centre(clock)
        self._comparator = self._own(audioshaper.Waveshaper(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, curve=self._curve(),
            oversample=1, mix=1.0, pre_gain=self._pre_gain(DEFAULTS[SENS_I]),
            post_gain=1.0))
        self._comparator.play(clock)
        return self._comparator

    def _centre(self, clock):
        """The clock less its slow mean, for the comparator.

        The mean is `MEAN_POLES` first-order low-passes at `MEAN_HZ`,
        negated by a multiply and summed with the clock by a two-voice
        mixer, which adds sample by sample. The clock's waveform is
        otherwise untouched, so a decaying note reaches the comparator as
        before; what moves is where its zero sits, which follows the
        offset the clock carries."""
        rate = self._sample_rate
        channels = self._channel_count
        split = self._own(audioroute.Splitter(clock, taps=2), reset=False)
        mean = split.tap(1)
        for _ in range(MEAN_POLES):
            pole = self._own(audiobiquad.AllPass(
                stages=1, frequency=MEAN_HZ, feedback=0.0, mix=0.5,
                sample_rate=rate, channel_count=channels))
            pole.play(mean)
            mean = pole
            self._mean.append(pole)
        minus_one = self._own(audiocore.RawSample(
            array("h", [-32768] * (2 * channels)),
            sample_rate=rate, channel_count=channels), reset=False)
        negative = self._own(audiomath.Multiply(
            mean, minus_one, mix=1.0, sample_rate=rate,
            channel_count=channels))
        # Not reset, as the output mixer: no voice holds a block between
        # two pulls once the graph is armed (`_arm`).
        centred = self._own(audiomixer.Mixer(
            voice_count=2, **self._pcm(BLOCK * channels * 4)), reset=False)
        centred.voice[0].play(split.tap(0), loop=True)
        centred.voice[1].play(negative, loop=True)
        return centred

    def _divide(self, tap, order):
        """A divider on the comparator: a +-1 square at a half (order 1)
        or a quarter (order 2) of the note, zero while the comparator is
        off its rails. Both orders count the same crossings, so the quarter
        turns over only where the half does.

        The divider turns over on the ticks, and the gate after it takes
        them out, so what reaches the multiply is the divider's square on
        the rails and exact zero elsewhere."""
        divider = self._own(audiomath.SubOctave(
            tap, order=order, mix=1.0, threshold=CLOCK_THRESHOLD,
            hold_ms=CLOCK_HOLD_MS, sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        gate = self._own(audioshaper.Waveshaper(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, curve=gate_curve(),
            oversample=1, mix=1.0, pre_gain=1.0, post_gain=1.0))
        gate.play(divider)
        return gate

    def _first(self, tap):
        return self._divide(tap, 1)

    def _curve(self):
        return comparator_curve()

    def _pre_gain(self, sensitivity_db):
        return pre_gain(sensitivity_db)

    def _octave(self, signal, square):
        """The signal times the square: every other cycle turned over."""
        return self._multiply(signal, square)

    def _multiply(self, signal, square):
        return self._own(audiomath.Multiply(
            signal, square, mix=1.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count))

    def _second(self, signal, tick):
        """Octave 2: the signal times the quarter-note square, which is
        Octave 1 with every other cycle turned over."""
        return self._multiply(signal, self._divide(tick, 2))

    def _tone(self, source, hz):
        """A Tone low-pass on `source`."""
        node = self._own(audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=hz, Q=TONE_Q, mix=1.0,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        node.play(source)
        return node

    def _set_tracking(self, hz):
        if self._allpass is not None:
            self._allpass.frequency = hz
        for section in self._clock:
            section.frequency = hz

    def _tone1_hz(self):
        return self._hz(self._value(TONE1_I))

    # -- the controls ----------------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _apply_macro(self, index, position):
        del position
        if index == TRACKING_I:
            self._set_tracking(self._hz(self._value(TRACKING_I)))
        elif index == TONE1_I:
            hz = self._tone1_hz()
            self._tone1.frequency = hz
            self._tone1b.frequency = hz
        elif index == TONE2_I:
            self._tone2.frequency = self._hz(self._value(TONE2_I))
        elif index == SENS_I:
            sensitivity = self._value(SENS_I)
            self._comparator.set(pre_gain=self._pre_gain(sensitivity))
        else:
            self._route()

    def _is_wire(self):
        return (self._macros[DIRECT_I] >= 1.0
                and self._macros[OCTAVE1_I] <= 0.0
                and self._macros[OCTAVE2_I] <= 0.0)

    def _levels(self):
        voices = self._mixer.voice
        voices[0].level = self._value(DIRECT_I)
        voices[1].level = self._value(OCTAVE1_I)
        voices[2].level = self._value(OCTAVE2_I)

    def _route(self):
        """Direct at 1 with both octaves at 0 hands out the input adapter,
        the source byte for byte; anything else plays the mixer, armed the
        first time it is reached."""
        if self._is_wire():
            self._route_around(self._adapter)
            return
        if not self._ready:
            self._levels()
            return
        self._rejoin()
        if not self._armed:
            self._arm()
            self._armed = True
        self._output = self._tail
        self._levels()

    def _arm(self):
        """Play the voices, the first time the output reaches the mixer.

        Each voice first plays silence for one pull, which opens its level
        gate (as `_component.open_level_gates` does). A voice's `play()`
        then primes one block from its source: with the Port on `_hush`
        that block is zeros, and a second pull hands it out, so arming
        takes nothing from the source. Between two pulls after that no
        voice holds a block and every tap is caught up, because the adapter
        hands 256-frame blocks and the Mixer pulls 256 frames: a move into
        the wire hands out the adapter with nothing left behind, and the
        way back carries on from where the wire stopped."""
        voices = self._mixer.voice
        self._levels()
        for voice in voices:
            voice.play(self._silence, loop=True)
        self._pull()
        self._in.play(self._hush)
        voices[0].play(self._dry, loop=True)
        voices[1].play(self._octave1, loop=True)
        voices[2].play(self._tone2, loop=True)
        self._pull()
        self._in.play(self._adapter)
        # The all-pass glides a Tracking move over one block from the
        # coefficient it last played at. It has played only the arming's
        # zeros, so it holds nothing to keep: cleared, its first block of
        # the source starts at the Tracking then in force, as a rejoin's
        # does, and a move before the first pull lands at once.
        if self._allpass is not None:
            audiocore.reset_buffer(self._allpass)
        # The same for the clock's and the Tone legs' biquads, which also
        # heard only zeros. Since audiodsp v0.6.6rc9 a biquad that has run a
        # block walks a corner move over 20 ms (#162); cleared, it takes a
        # Tone or Tracking set before the first pull as it stands, as a
        # fresh build does (audiocomponents#164).
        for node in (self._clock + self._mean
                     + [self._tone1, self._tone1b, self._tone2]):
            audiocore.reset_buffer(node)

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
            # small: two stereo frames.
            self._puller = self._own(audiomixer.Mixer(
                voice_count=1, **self._pcm(16)), reset=False)
        voice = self._puller.voice[0]
        voice.play(self._tail)
        voice.stop()

    @property
    def tail_samples(self):
        """The all-pass and both Tone filters ringing down, end to end."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        if self._is_wire():
            return 0
        ring = 0
        if self._allpass is not None:
            ring = _allpass_ring(self._allpass.coefficient)
        tones = _component.cascade_ring((self._tone1b, self._tone2))
        if ring is None or tones is None:
            return None
        return ring + tones
