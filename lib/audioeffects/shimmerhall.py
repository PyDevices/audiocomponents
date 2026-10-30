"""`ShimmerHall` - a hall that rings an octave above what you play.

You play into a hall, and a pitch shifter beside it makes the tail ring at
the Interval you choose. Character picks how it is built. In Bloom the
shifted copy goes into the hall once, Bloom after you play, and the whole
hall waits for it. In Rise the shifter sits in a feedback loop: the hall
starts at once, and each pass comes back shifted again, so the tail climbs
while Damping darkens every pass until it fades.

Shimmer is how loud the shifted copy goes into the hall. Bloom is the wait
in Bloom and the time between passes in Rise. Rise is how strongly each
pass returns, in Rise only. Interval picks one of five shifts: -12, -5, +7,
+12 or +24 semitones. Decay, Size and Damping set the hall, and Damping
also darkens each pass of the loop. Mix is `audiodelays.Echo`'s: your dry
signal at unity up to 1, the hall alone at 2. The Effect controls page
lists what the knobs span and the patches.

In Bloom, move Bloom and the shifted copy moves by the same time, within 512
frames. Its energy centres within 2.5 semitones of the Interval. In Rise the
loop's short window spreads the first pass wider: within 2.5 semitones at -5
and +7, 3.5 at +12 and 6 at -12 and +24.

In Rise at +12 each octave arrives one Bloom after the one below, within
20 %. Moving Rise from 0.3 to 0.9 brings the third pass back 16 to 22 dB
stronger against the first, and in Bloom Rise changes nothing. With Damping
at 800 Hz the fourth pass is at least 12 dB weaker against the first than
at 16 kHz.

Up to Mix 1 your dry signal passes untouched, sample for sample: the
shimmer is only ever in the hall. At Mix 0 the output is your input, byte
for byte. Latency is zero. Keep your input at or under -24 dBFS: with
Decay, Size, Shimmer and Rise at the top, a steady loud input fills the
hall to the rail.

`tail_samples` bounds how long the output takes to reach exact zero once
your input stops: 82 s at Rise 0.9 and Bloom 800 ms. `reset()` empties the
hall, the line and the shifter, and restores patch 0. Octave Rise is Octave
Bloom in Rise at Rise 0: one octave, once, and the hall starts at once. On
an ESP32-S3 the Bloom patches (Octave Bloom, Short Stagger and Fifth Halo)
take longer than a block and cannot keep up; the defaults and every Rise
patch keep up.

**Limits**

A control that jumps makes the output step: move it in small steps from the
host if you need it smooth. Moving Character or Size empties the hall: the
tail drops and the dry carries on. If your host takes the output before it
loads a patch or moves Mix, the first 256 frames, 5 ms at 48 kHz, play at the
old level.

Interval is a fixed shift in semitones, with no key awareness. Both
shifters splice, so the shifted copy has a slight flutter. In Rise, a held
note's shimmer lands on the octave, a held G3 at +12 included. With Damping
high and Rise near the top, or at the widest intervals, the climb fades out
at the top of the band at 48 kHz; at 22.05 kHz a tone outside the series
can still fold back, 25 to 40 dB under the first pass. Keep Damping lower
for a clean climb. A mono source gets a mono rack. It needs a board with
PSRAM.

When your source ends, the tail rings out as it would on silence. On a
CircuitPython board, stop the rack from the host if your source can run
dry in Bloom: CircuitPython's own pitch shifter waits on a source that
comes back empty. Firmware built with micropython-pydevices' build_mp.py
carries the fix and returns.

A value outside a macro's span clamps to the nearer stop, and NaN takes the
default; an `interval` other than the five raises `ValueError`.
"""

VENDOR = "PyDevices"

import math
from array import array

import audiocore

from . import _component

from .digitaldelay import laps_to_zero, whole_frames
from .tapedelay import tone_excess
# The module, not the class, so this module holds one Component class.
from . import reverb as _reverb

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None
try:
    import audiodelays
except ImportError:                     # pragma: no cover - a stock board
    audiodelays = None
try:
    import audioroute
except ImportError:                     # pragma: no cover - a stock board
    audioroute = None
try:
    import audiomixer
except ImportError:                     # pragma: no cover - a stock board
    audiomixer = None


#: Frames per pull: the palette's block.
BLOCK = 256

(CHARACTER_I, SHIMMER_I, RISE_I, BLOOM_I, INTERVAL_I, DECAY_I, SIZE_I,
 DAMPING_I, MIX_I) = range(9)

CHARACTERS = ("bloom", "rise")

#: Interval's five zones, in semitones, low to high on the 0-127 grid.
INTERVALS = (-12, -5, 7, 12, 24)

#: Where each zone sits on the grid when the constructor or a patch names it.
INTERVAL_MIDI = (0, 32, 64, 96, 127)

RISE_MAX = 0.9

#: Bloom's shifter: its window and crossfade, in ms.
WINDOW_MS = 40.0
OVERLAP_MS = 10.0

#: Rise's shifter: the loop's window. A shifted loop reads half of it late
#: (`docs/upstream-diff.md`, `loop_semitones`), so Rise's line is set that
#: much short of Bloom.
LOOP_WINDOW_MS = 25.0

#: The line: Bloom's top plus the loop window, the furthest a shifted tap
#: reads.
LINE_MS = 800.0 + LOOP_WINDOW_MS

#: `audiodelays.PitchShift` reads in whole 256ths of unity
#: (`PitchShift.c:121`), rounding down.
STEPS = 256

#: Each macro's patch-0 step; the constructor defaults are these steps'
#: values, so a fresh instance is patch 0.
DEFAULT_STEPS = (127, 89, 0, 90, 96, 94, 64, 91, 32)


def _default(index, span):
    return _component.macro_value(
        span, _component.position_of_midi("UNIPOLAR", DEFAULT_STEPS[index]))


#: The constructor defaults: each patch-0 step's value. NaN falls back to
#: these.
SHIMMER = _default(1, (0.0, 1.0))
RISE = _default(2, (0.0, RISE_MAX))
BLOOM_MS = _default(3, (20.0, 800.0, "log"))
DECAY = _default(5, (0.3, 10.0, "log"))
SIZE = _default(6, (0.5, 1.5))
DAMPING_HZ = _default(7, (500.0, 16000.0, "log"))
MIX = _default(8, (0.0, 2.0))
DEFAULTS = (1.0, SHIMMER, RISE, BLOOM_MS, _default(4, (0.0, 5.0)), DECAY,
            SIZE, DAMPING_HZ, MIX)

#: The hall's macros the rack drives, by `Reverb`'s labels.
_HALL_DECAY_I = _reverb.Reverb.MACRO_LABELS.index("Decay")
_HALL_SIZE_I = _reverb.Reverb.MACRO_LABELS.index("Size")
_HALL_DAMPING_I = _reverb.Reverb.MACRO_LABELS.index("Damping")

#: Which of the rack's macros drive which of the hall's.
_HALL_MACROS = ((DECAY_I, _HALL_DECAY_I), (SIZE_I, _HALL_SIZE_I),
                (DAMPING_I, _HALL_DAMPING_I))


def _hall_patch():
    """The hall at the rack's patch 0, on `Reverb`'s grid: Concert Hall's
    Diffusion, Bandwidth, Low Cut, Mod Depth, Mod Rate, Width and Tone, the
    hall character, no Predelay (Bloom is the predelay), the tail alone,
    and the rack's own Decay, Size and Damping steps."""
    concert = None
    for _index, (name, values) in _reverb.Reverb.PATCHES.items():
        if name == "Concert Hall":
            concert = list(values)
    labels = _reverb.Reverb.MACRO_LABELS
    concert[labels.index("Character")] = 127
    concert[labels.index("Predelay")] = 0
    concert[labels.index("Mix")] = 127
    for ours, theirs in _HALL_MACROS:
        concert[theirs] = DEFAULT_STEPS[ours]
    return tuple(concert)


HALL_PATCH = _hall_patch()


def _hall_options():
    """`Reverb`'s constructor options at `HALL_PATCH`'s grid values."""
    spans = _reverb.Reverb._MACRO_RANGES
    names = ("decay", "size", "predelay_ms", "diffusion", "damping_hz",
             "bandwidth_hz", "low_cut_hz", "mod_depth_ms", "mod_rate_hz",
             "width", "tone_db", "mix")
    options = {"character": "hall"}
    for index, name in zip(range(1, 13), names):
        mode = _reverb.Reverb.MACRO_MODES.get(index, "UNIPOLAR")
        position = _component.position_of_midi(mode, HALL_PATCH[index])
        options[name] = _component.macro_value(spans[index], position)
    return options


def step_centre_semitones(step):
    """Semitones that put `audiodelays.PitchShift` on `step`: the centre of
    the step, so the node's truncation lands on it at any float width."""
    return 12.0 * math.log((step + 0.5) / STEPS) / math.log(2.0)


def interval_step(semitones):
    """The shifter's read rate nearest `semitones`, in 256ths."""
    return int(math.floor(2.0 ** (semitones / 12.0) * STEPS + 0.5))


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


class ShimmerHall(_component.Component):
    """A pitch shifter around a hall. The module docstring is the player's
    page."""

    NAME = 'ShimmerHall'
    #: NaN is this option's own stop, not the default (documented above).
    _NAN_OWN = ('interval',)
    DISPLAY_NAME = 'Shimmer Hall'
    CATEGORIES = ('Effect Rack', 'Reverb')
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioroute", "audioecho", "audioverb")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    INPUT_CEILING_DBFS = -24.0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Character", "Shimmer", "Rise", "Bloom", "Interval",
                    "Decay", "Size", "Damping", "Mix")
    MACRO_MODES = {
        0: "TOGGLE",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
        8: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (0.0, 1.0),                     # 0 Character: Bloom < 0.5 <= Rise
        (0.0, 1.0),                     # 1 Shimmer
        (0.0, RISE_MAX),                # 2 Rise, the loop's feedback
        (20.0, 800.0, "log"),           # 3 Bloom, ms
        (0.0, 5.0),                     # 4 Interval, zone min(4, int(v))
        (0.3, 10.0, "log"),             # 5 Decay, s (the hall's)
        (0.5, 1.5),                     # 6 Size (the hall's)
        (500.0, 16000.0, "log"),        # 7 Damping, Hz
        (0.0, 2.0),                     # 8 Mix; dry at unity to 1
    )
    _MACRO_UNITS = {3: "ms", 5: "s", 7: "Hz"}

    #: `_component.macro_of` of the card's settings.
    PATCHES = {
        0: ("Octave Rise", DEFAULT_STEPS),
        1: ("Short Stagger", (0, 76, 85, 38, 96, 77, 38, 102, 25)),
        2: ("Fifth Halo", (0, 102, 85, 103, 64, 108, 89, 84, 38)),
        # Damping step 86 (about 5.2 kHz), where the card had 102 (8 kHz):
        # at 8 kHz the sixth pass folded back past -30 dB at 22.05 kHz,
        # before the loop shifter's band limit (audiodsp v0.6.6).
        3: ("Slow Rise", (127, 89, 85, 103, 96, 108, 89, 86, 38)),
        4: ("Rise Damped", (127, 102, 113, 87, 96, 94, 64, 51, 32)),
        5: ("Falling Octaves", (127, 89, 85, 93, 0, 102, 64, 76, 32)),
        # Patch 0 in Bloom, at the card's Rise: every Bloom patch runs over
        # a block on an ESP32-S3, so the defaults are its Rise twin.
        6: ("Octave Bloom", (0, 89, 85, 90, 96, 94, 64, 91, 32)),
    }

    def _build(self, character="rise", shimmer=SHIMMER, rise=RISE,
               bloom_ms=BLOOM_MS, interval=12, decay=DECAY, size=SIZE,
               damping_hz=DAMPING_HZ, mix=MIX, patch=None):
        if character not in CHARACTERS:
            raise ValueError("character must be 'bloom' or 'rise', not %r"
                             % (character,))
        if isinstance(interval, bool) or interval not in INTERVALS:
            raise ValueError("interval must be one of %r semitones"
                             % (INTERVALS,))
        spans = self._MACRO_RANGES
        defaults = DEFAULTS
        options = (None, shimmer, rise, bloom_ms, None, decay, size,
                   damping_hz, mix)
        # A default lands on its own 0-127 step, so a fresh instance reads
        # patch 0 exactly. Any other value is kept as the knob's position,
        # between steps if it falls there, as a host with finer resolution
        # than MIDI would set it: it is the knob, not a value kept beside
        # it, so a patch or a move replaces it.
        positions = [1.0 if character == "rise" else 0.0]
        for index in range(1, len(spans)):
            if index == INTERVAL_I:
                positions.append(_component.position_of_midi(
                    "UNIPOLAR", INTERVAL_MIDI[INTERVALS.index(interval)]))
                continue
            span = spans[index]
            value = _between(_option(options[index], defaults[index]),
                             span[0], span[1])
            if value == defaults[index]:
                positions.append(_component.position_of_midi(
                    "UNIPOLAR", DEFAULT_STEPS[index]))
            else:
                positions.append(_component.macro_position(span, value))

        rate = self._sample_rate
        channels = self._channel_count
        width = 2 * channels
        #: True once the macros are seeded; until then nothing is pushed.
        self._ready = False
        #: True once the voices have been played (`_wire`).
        self._wired = False
        #: Whether the host has asked for the output yet. Until it has,
        #: nothing has been pulled, and a control that moves a voice's level
        #: re-arms the graph so the level holds from frame 0. A reset or a
        #: return from Mix 0 does not start that window again: the class
        #: cannot see a pull, and a host that keeps the node it took would
        #: have every later level move empty the hall.
        self._taken = False
        #: The two Mixer levels last handed to the voices.
        self._applied = None
        #: True while the wet chain is Rise's.
        self._rise = None
        #: What each node was last handed, by name.
        self._handed = {}
        self._feedback = 0.0
        self._delay = 1.0
        self._bloom = 1

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
        # A Splitter's taps are read in step, 256 frames a pull each, so it
        # holds nothing between pulls and is not reset.
        self._split = self._own(audioroute.Splitter(self._in, taps=2),
                                reset=False)
        self._dry_tap = self._split.tap(0)
        self._wet_tap = self._split.tap(1)
        # Bloom's shifter reads the wet tap through a port of its own. A
        # shifter's `play()` primes a block from its source and holds it,
        # so it is played on `_hush` and that block is pulled out at once
        # (`_drain`): the shifter then holds nothing, and whichever of the
        # two characters reads the wet tap reads it in step with the dry.
        self._shift_in = self._own(audioroute.Port(self._hush), reset=False)
        self._shift = self._own(audiodelays.PitchShift(
            semitones=0.0, mix=0.0,
            window=whole_frames(WINDOW_MS, rate) * width,
            overlap=whole_frames(OVERLAP_MS, rate) * width,
            **self._pcm(BLOCK * width)))
        self._shift.play(self._shift_in)
        self._fd = self._own(audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=channels, max_delay_ms=LINE_MS,
            delay_frames=1, feedback=0.0, mix=2.0, damping_hz=0.0,
            cut_hz=0.0, loop_drive=0.0, loop_window_ms=LOOP_WINDOW_MS),
            reset=self._clear_line)
        self._hall = self._Hall(self._fd)
        self._own(self._hall, reset=self._hall._clear,
                  deinit=self._hall.deinit)
        # Not reset by the walk: neither voice holds a block between two
        # pulls (`_wire`), so there is nothing of its own to clear, and a
        # Mixer's reset reaches its voices' sources.
        self._mixer = self._own(audiomixer.Mixer(
            voice_count=2, buffer_size=BLOCK * width * 2,
            channel_count=channels, bits_per_sample=16,
            samples_signed=True, sample_rate=rate), reset=False)
        # The output: a width-1 MidSide over the mixer, byte for byte, whose
        # reset forwards nothing. A host's reset of the output would
        # otherwise reach the Mixer, and CircuitPython's own Mixer handles
        # that differently from audiodsp's.
        self._tail = self._own(audioroute.MidSide(
            self._mixer, width=1.0, sample_rate=rate,
            channel_count=channels), reset=False)
        self._silence = audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)), sample_rate=rate,
            channel_count=channels)
        #: Where `audiocore.get_buffer` is compiled out, the one-voice
        #: mixer `_drain` primes from; built the first time it is needed.
        self._puller = None
        self._drain(self._shift)
        self._shift_in.play(self._wet_tap)
        self._output = self._head

        self._init_macros(tuple(defaults))
        self._macros = positions
        if patch is not None:
            self.program_change(patch)
        self._ready = True
        self._refresh()

    # -- the maps ------------------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _is_rise(self):
        return self._macros[CHARACTER_I] >= 0.5

    def _interval(self):
        """Interval in semitones: the zone its position sits in."""
        zone = int(self._value(INTERVAL_I))
        if zone > 4:
            zone = 4
        if zone < 0:
            zone = 0
        return INTERVALS[zone]

    def _mix(self):
        return _between(self._value(MIX_I), 0.0, 2.0)

    def macro(self, index):
        """What macro `index` currently stands for, in its own units; for
        Interval, the semitones it plays."""
        self._check_live()
        if index == INTERVAL_I:
            return float(self._interval())
        return _component.Component.macro(self, index)

    # -- hooks a planted fault overrides --------------------------------

    def _semitones(self):
        """The interval the shifters are handed."""
        return self._interval()

    def _stagger_frames(self, bloom_ms):
        """Bloom's stagger: the line's delay, in whole frames."""
        return max(1, whole_frames(bloom_ms, self._sample_rate))

    def _loop_frames(self, bloom_ms):
        """Rise's line: Bloom less the half window a shifted read adds, so
        the repeats fall Bloom apart."""
        frames = whole_frames(bloom_ms, self._sample_rate) \
            - LOOP_WINDOW_MS * 0.0005 * self._sample_rate
        return max(1.0, frames)

    def _loop_feedback(self):
        """What the line sends round: Rise in Rise, nothing in Bloom."""
        if self._is_rise():
            return _between(self._value(RISE_I), 0.0, RISE_MAX)
        return 0.0

    def _loop_damping(self):
        """The loop's low-pass: Damping in Rise, out in Bloom."""
        if self._is_rise():
            return self._hz(_between(self._value(DAMPING_I), 500.0,
                                     16000.0))
        return 0.0

    def _dry_source(self):
        """What the dry voice plays: the Splitter's dry tap."""
        return self._dry_tap

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        del index, position
        if self._ready:
            self._refresh()

    def _apply_positions(self, positions, patch_index):
        """Set the knobs whole, then refresh the graph once: a patch and a
        rack's put-back after a reset both land here, so neither passes
        through a Mix 0 or a half-moved Character on the way."""
        ready = self._ready
        self._ready = False
        try:
            _component.Component._apply_positions(self, positions,
                                                  patch_index)
        finally:
            self._ready = ready
        if ready:
            self._refresh()

    def _hand(self, node, key, **settings):
        """Hand `node` only the settings that changed since it was last
        handed them."""
        changed = {}
        for name, value in settings.items():
            tag = key + name
            if self._handed.get(tag) != value:
                self._handed[tag] = value
                changed[name] = value
        if changed:
            if node is self._fd:
                node.set(**changed)
            else:
                for name, value in changed.items():
                    setattr(node, name, value)

    def _refresh(self):
        rise = self._is_rise()
        bloom_ms = self._value(BLOOM_I)
        shimmer = _between(self._value(SHIMMER_I), 0.0, 1.0)
        semitones = self._semitones()
        recut = self._rise is not None and rise != self._rise
        self._feedback = self._loop_feedback()
        self._bloom = whole_frames(bloom_ms, self._sample_rate)
        if rise:
            self._delay = self._loop_frames(bloom_ms)
            if recut or self._rise is None:
                self._fd.play(self._wet_tap)
            self._hand(self._fd, "fd.", delay_frames=self._delay,
                       feedback=self._feedback, mix=shimmer,
                       damping_hz=self._loop_damping(),
                       loop_semitones=float(semitones))
        else:
            self._delay = float(self._stagger_frames(bloom_ms))
            if recut or self._rise is None:
                self._fd.play(self._shift)
            self._hand(self._shift, "ps.",
                       semitones=step_centre_semitones(
                           interval_step(semitones)),
                       mix=shimmer * 0.5)
            self._hand(self._fd, "fd.", delay_frames=self._delay,
                       feedback=self._feedback, mix=2.0,
                       damping_hz=self._loop_damping(), loop_semitones=0.0)
        self._rise = rise
        for ours, theirs in _HALL_MACROS:
            position = self._macros[ours]
            tag = "hall.%d" % theirs
            if self._handed.get(tag) != position:
                self._handed[tag] = position
                self._hall.set_macro(theirs, 127.0 * position)
        if recut:
            # The wet chain is re-cut: it renders as a fresh instance's.
            # The dry carries on.
            self._clear_nodes(only=(self._shift, self._fd, self._hall))
        self._route()

    def _level_pair(self):
        """The dry and the hall's Mixer levels at this Mix."""
        mix = self._mix()
        return (min(1.0, 2.0 - mix), min(1.0, mix))

    def _levels(self):
        voices = self._mixer.voice
        pair = self._level_pair()
        voices[0].level = pair[0]
        voices[1].level = pair[1]
        self._applied = pair

    def _route(self):
        """Point the output at the source's reader at Mix 0, or at the
        mixer, emptying the wet chain when it comes back."""
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
        """Empty the hall, the line and the shifter, return to patch 0, and
        play from there as a new instance does."""
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

    def _rearm(self):
        """Wire the graph again as the constructor does, once it has been
        cleared: a voice's new level is picked up at its next zero crossing
        unless the voice is played again, so a graph that is cleared while
        a level changes would otherwise carry the old level into the first
        frames. The input goes back to silence first, so no frame is taken
        from the borrowed source."""
        self._in.play(self._hush)
        self._wire()

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
        voices[0].play(self._dry_source())
        voices[1].play(self._hall.output)
        self._pull()
        self._in.play(self._head)
        self._clear_nodes(only=(self._shift, self._fd, self._hall))
        self._wired = True
        # A control touched at Mix 0 before the first wiring marked the
        # graph stranded; wiring is what that mark waits for.
        self._stranded = False

    def _pull(self):
        """Pull one block from the mixer and drop it. `_tail` forwards no
        reset, so pulling through it rewinds nothing behind it."""
        self._drain(self._tail)

    def _drain(self, node):
        """Pull one block from `node` and drop it.

        Where `audiocore.get_buffer` is compiled out (CircuitPython's
        default board builds), a voice of a one-voice mixer of our own
        plays `node` and stops: its `play()` primes one block, which pulls
        `node` once."""
        pull = getattr(audiocore, "get_buffer", None)
        if pull is not None:
            pull(node)
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
        voice.play(node)
        voice.stop()

    def _clear_line(self):
        """Empty the line. A shifted loop goes back to its single-tap read
        and starts its splice from where a new node does."""
        self._fd.clear()

    # -- the contract's reads ------------------------------------------

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`.

        Bloom: the stagger, then the shifter's window and crossfade (what
        it holds once its input stops), then the hall's own tail. Rise: the
        line goes round `laps_to_zero` laps at Rise (the node's stall rule
        ends it), each at most Bloom plus the loop window, the read between
        two frames and the low-pass's memory, and one more for what the line
        holds at Rise 0; then the hall's tail. 0 at Mix 0."""
        if self._mix() <= 0.0:
            return 0
        rate = self._sample_rate
        hall = self._hall.tail_samples
        if not self._rise:
            reach = self._bloom + whole_frames(WINDOW_MS, rate) \
                + whole_frames(OVERLAP_MS, rate) + 1
            return int(reach + hall)
        memory, excess = tone_excess(self._handed.get("fd.damping_hz", 0.0),
                                     rate)
        lap = self._bloom + int(math.ceil(LOOP_WINDOW_MS * rate / 1000.0)) \
            + 2 + memory
        laps = laps_to_zero(self._feedback, excess) + 1
        return int(laps * lap + hall)

    class _Hall(_reverb.Reverb):
        """The rack's hall: `Reverb` whose only patch is the hall at the
        rack's patch-0 settings, and whose constructor defaults are that
        patch, so its own `reset()` lands there. Nested, so the module holds
        one provider; last, so the rack's `_build` is the first in this
        source."""

        PATCHES = {0: ("Hall", HALL_PATCH)}

        def _build(self, patch=None, **options):
            settings = _hall_options()
            settings.update(options)
            _reverb.Reverb._build(self, patch=patch, **settings)

        def _clear(self):
            """Empty the tank and keep every macro: a reset without its
            patch 0."""
            self._clear_nodes()
