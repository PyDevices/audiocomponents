"""`Octaver` - the analog octave-down.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests. How the graph works is told
where it is built, in `Octaver._build`.
"""

VENDOR = "PyDevices"

from array import array

import audiocore

from .. import _component

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
#: across |i - 2048| <= 63 and the rails beyond. Interpolating between two
#: points of a one-point step is a gain stage, which leaks an octave up and
#: DC below Sensitivity; a dead band many points wide reads exact zero.
CURVE_POINTS = 4097
DEAD_HALF = 63
#: The comparator reaches the rail where its input times `pre_gain` is
#: 64/2048, so `pre_gain = EDGE / 10^(Sensitivity/20)` puts the rail at the
#: clock's level of Sensitivity. 1/32 is exact in every float format.
EDGE = 0.03125

#: The clock filters' Q: two sections of 0.5 are four coincident real
#: poles, whose phase a two-stage first-order all-pass matches exactly.
CLOCK_Q = 0.5
TONE_Q = 0.7071

#: The divider of the clock leg: a +-1 square from the comparator's +-rail.
CLOCK_THRESHOLD = 0.5
CLOCK_HOLD_MS = 1.0

#: Frames a mixer pull hands out, and so what every node and tap takes per
#: pull: the palette's own block, so the Splitters' rings empty each pull.
BLOCK = 256

_CURVE = None


def comparator_curve():
    """The comparator's table, built once and shared by every instance."""
    global _CURVE
    if _CURVE is None:
        rail = (CURVE_POINTS - 1) // 2 - DEAD_HALF
        _CURVE = array("h", [-32767] * rail + [0] * (2 * DEAD_HALF + 1)
                       + [32767] * rail)
    return _CURVE


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

    **The controls.** Direct, Octave 1 and Octave 2 are the three levels,
    each from 0 to 1.
    Tracking, from 40 to 400 Hz, moves the range of notes the divider
    follows.
    Tone 1 (100 to 2000 Hz) and Tone 2 (40 to 800 Hz) are two-pole
    low-passes at the hertz they show, on the first and second octave.
    Sensitivity, from -90 to -40 dBFS, is how quiet a note can get before
    the octaves stop.
    Constructor values land on the nearest of each knob's 128 steps.

    **What you hear.** The octave is exactly half your note and sounds
    within 2 ms of it.
    Octave 2 is Octave 1 divided again: two octaves down, not a fourth
    below the note.
    On low notes, to A2, the octave follows your note's decay within 1 dB:
    it has no envelope of its own.
    Below Sensitivity the octaves are silent, with no ghost and no hum.
    With the Tones open the octave carries a fifth above it 4.4 dB
    quieter, as the pedal's multiplication does, wherever Tracking is set.
    Turning Tone 1 down thins that fifth more on high notes than on low
    ones.

    **Its range.** At patch 0, on a mono source, every note from low E
    (E2) to A4 divides cleanly, even with a strong second harmonic.
    The Bass patch covers E1 to G3, and High on the neck covers D3 to E5.
    Below the range a low note's second harmonic clocks the divider and it
    skips; above it the clock is low-passed under Sensitivity and the
    octave goes silent.
    Between -90 and -84.5 dBFS Sensitivity changes nothing: that whole
    stretch is one step of the clock.

    **Limits.** It plays one note at a time: on a power chord (A2 and E3)
    about two fifths of the octave is intermodulation.
    A stereo source is clocked on its mid: with the right channel 45
    degrees ahead of the left, the fifth sits 3.2 dB under the octave
    instead of 4.4, on both channels.
    So near the top of the range a stereo note whose channels cancel each
    other's fundamental can drop out: one stereo A4 in eight did, at
    patch 0.
    The output can peak at 2.8 times the input (a square wave, with Octave
    2 at full), so keep the input under -9 dBFS.
    A control that jumps makes the output step: move it in small steps
    from the host if you need it smooth.

    **Wire, latency, tail.** With both octaves at 0 and Direct at 1 the
    output is the input, byte for byte.
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

    #: The worst peak gain over the kit's material, every patch and every
    #: stop, is 2.75 (a square, Octave 2 at full): -9 dBFS keeps it inside
    #: full scale.
    INPUT_CEILING_DBFS = -9.0

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

    #: `_component.macro_of` of the card's settings: 0.7 is 89, 0.8 is 102,
    #: 0.6 is 76; Tracking 90/50/200 Hz is 45/12/89; Tone 1 324/250/700 Hz
    #: is 50/39/82; Tone 2 70.3 Hz is 24; Sensitivity -80 dBFS is 25.
    PATCHES = {
        0: ("Octave down under the dry", (127, 89, 0, 45, 50, 24, 25)),
        1: ("Both octaves", (102, 89, 89, 45, 50, 24, 25)),
        2: ("Octaves alone, no dry", (0, 127, 76, 45, 50, 24, 25)),
        3: ("Bass guitar", (127, 102, 0, 12, 39, 24, 25)),
        4: ("High on the neck", (127, 89, 0, 89, 82, 24, 25)),
        5: ("Two octaves down alone", (0, 0, 127, 45, 50, 24, 25)),
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

        # One Splitter, three legs: the dry voice, the signal the octave is
        # made of, and the clock that says when to turn it over. The clock
        # and the signal are kept apart because `SubOctave` clocks on what
        # it divides, so a tracking filter in front of it would darken the
        # octave too (12 dB from E2 to G3, measured on the card's probes).
        split = self._own(audioroute.Splitter(self._source, taps=3),
                          reset=False)
        self._dry = split.tap(0)
        self._allpass = None
        self._clock = []
        signal = self._signal_leg(split.tap(1))
        square = self._clock_leg(split.tap(2))
        self._product = self._octave(signal, square)
        self._tone1 = self._own(audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=324.0, Q=TONE_Q, mix=1.0,
            sample_rate=rate, channel_count=channels))
        self._tone1.play(self._product)

        # Octave 2 divides Octave 1's filtered output, on that signal's own
        # crossings, as the pedal's second stage does.
        split2 = self._own(audioroute.Splitter(self._tone1, taps=2),
                           reset=False)
        self._octave1 = split2.tap(0)
        self._divider2 = self._second(split2.tap(1))
        self._tone2 = self._own(audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=70.3, Q=TONE_Q, mix=1.0,
            sample_rate=rate, channel_count=channels))
        self._tone2.play(self._divider2)

        # Not reset: the voices keep the source frames they have taken, and
        # a Mixer reset is no reset of anything this class holds.
        self._mixer = self._own(audiomixer.Mixer(
            voice_count=3, **self._pcm(BLOCK * channels * 2)), reset=False)
        self._output = self._mixer

        self._init_macros(tuple(
            _component.macro_value(self._MACRO_RANGES[i], grid[i] / 127.0)
            for i in range(7)))
        # Land each knob exactly on its step, as patch 0 does.
        for i in range(7):
            position = _component.position_of_midi("UNIPOLAR", grid[i])
            if self._macros[i] != position:
                self._macros[i] = position
                self._apply_macro(i, position)

        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._ready = True
        self._route()
        if patch is not None:
            self.program_change(patch)

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
        """Low-pass at Tracking, a comparator with a dead band, and a
        divider that hands out a +-1 square at half the note (zero while the
        comparator reads zero)."""
        clock = self._mid(tap)
        for _ in range(2):
            section = self._own(audiobiquad.Biquad(
                mode=audiobiquad.LOW_PASS, frequency=90.0, Q=CLOCK_Q,
                mix=1.0, sample_rate=self._sample_rate,
                channel_count=self._channel_count))
            section.play(clock)
            clock = section
            self._clock.append(section)
        self._comparator = self._own(audioshaper.Waveshaper(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, curve=self._curve(),
            oversample=1, mix=1.0, pre_gain=self._pre_gain(DEFAULTS[SENS_I]),
            post_gain=1.0))
        self._comparator.play(clock)
        self._divider = self._own(audiomath.SubOctave(
            self._comparator, order=1, mix=1.0, threshold=CLOCK_THRESHOLD,
            hold_ms=CLOCK_HOLD_MS, sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        return self._divider

    def _curve(self):
        return comparator_curve()

    def _pre_gain(self, sensitivity_db):
        return pre_gain(sensitivity_db)

    def _octave(self, signal, square):
        """The signal times the square: every other cycle turned over."""
        return self._own(audiomath.Multiply(
            signal, square, mix=1.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count))

    def _second(self, tap):
        """Octave 1's output divided again."""
        return self._own(audiomath.SubOctave(
            tap, order=1, mix=1.0, sample_rate=self._sample_rate,
            channel_count=self._channel_count))

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
            self._tone1.frequency = self._tone1_hz()
        elif index == TONE2_I:
            self._tone2.frequency = self._hz(self._value(TONE2_I))
        elif index == SENS_I:
            self._comparator.set(
                pre_gain=self._pre_gain(self._value(SENS_I)))
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
        """Direct at 1 with both octaves at 0 hands out the source itself;
        anything else plays the mixer, re-armed if the graph was left."""
        if self._is_wire():
            self._route_around(self._source)
            self._armed = False
            return
        if not self._ready:
            self._levels()
            return
        if self._rejoin() or not self._armed:
            # The nodes are clear; the voices still hold the blocks they
            # had queued. Armed as `_build` arms them: levels, gates,
            # voices, then the port.
            self._levels()
            _component.open_level_gates(self._mixer, self._mixer.voice,
                                        self._silence)
            voices = self._mixer.voice
            voices[0].play(self._dry, loop=True)
            voices[1].play(self._octave1, loop=True)
            voices[2].play(self._tone2, loop=True)
            self._armed = True
        self._output = self._mixer
        self._levels()

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
        tones = _component.cascade_ring((self._tone1, self._tone2))
        if ring is None or tones is None:
            return None
        return ring + tones
