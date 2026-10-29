"""`AirSpace` - a tape echo sent into a chamber, with the dry beside it.

You send your signal to a tape echo whose repeats feed an echo chamber, and
your dry signal comes back exactly as it went in: the filters, the drive and
the tape act only on the send.

Time is the gap between repeats and Feedback how much of each repeat goes
round again. Loop Top and Loop Bass filter the loop, so each repeat is
darker than the last, and Drive saturates it. Top Cut darkens everything
sent to the chamber, once. Low Cut, Decay and Damping set the chamber. Mix
is `audiodelays.Echo`'s: the dry at unity up to 1, the chamber alone at 2.
The Effect controls page lists what the knobs span and the patches.

More Feedback makes the chamber's tail longer: at Time 500 ms, Feedback 0.85
at least triples it. At the defaults you hear the repeats as a longer
chamber, not as a rhythm of echoes.

Move Time while it plays and the repeats bend in pitch, the way tape does:
down while it lengthens, up while it shortens. Glide is how long a move
across the whole Time range takes, so it sets how far they bend: 12 % at
the default of 4 s.

Keep your input at or under -17 dBFS: at Mix 1 the dry and the chamber are
both at unity and add, so a hotter input can reach the rail. That holds on
every patch and with any one macro at either end. Open two or more of
Feedback, Decay and Time together and the chamber builds further, by up to
25 dB: keep your input at or under -26 dBFS there. Latency is zero. `reset()` empties the tape and the chamber and restores patch 0, whose
Time of 111 ms lands at once instead of gliding.

**Limits**

A control that jumps makes the output step: move it in small steps from the
host if you need it smooth. Time is the exception: it glides.

A patch that changes Time glides there too, and the repeats bend while it
travels.

At the defaults the repeats add only a little length to the tail; the
stretch comes with Feedback above about 0.6 or a long Time.

At a short Time with high Feedback the repeats are heard as a flutter, not a
longer chamber.

There is always at least 20 ms between the dry and the chamber.

The loop's filters are gentle, 6 dB per octave, and the Top Cut's is
steeper: there is no loop bell, no presence EQ and no wow. Drive's level is
not compensated. The chamber's size is fixed, there is no tempo sync, and a mono source gets a
mono rack.

At Mix 0 the output is your input, byte for byte, and the tail that was
ringing when Mix went to 0 is gone when it comes back.

When your source ends, the tail rings out as it would on silence.
"""

VENDOR = "PyDevices"

from array import array

import audiocore

from . import _component

from .digitaldelay import CUT_LAP_FACTOR, laps_to_zero, whole_frames
from .tapedelay import tone_excess
# The module, not the class, so this module holds one Component class.
from . import reverb as _reverb

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None
try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None
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

TIME_MIN_MS = 20.0
TIME_MAX_MS = 500.0

#: The tape's line: Time's top plus headroom for the node's two-frame clamp
#: (`audiodsp_feedback_delay.c:156-159`).
LINE_MS = 505.0

#: How far a move across the whole Time range runs, in ms: Glide is the
#: time it takes, so `delay_slew` is this over Glide.
FULL_RANGE_MS = TIME_MAX_MS - TIME_MIN_MS

FEEDBACK_MAX = 0.85

#: `tail_samples` counts this many times `laps_to_zero`'s laps, as
#: `DigitalDelay` does with Repeat Cut in (`CUT_LAP_FACTOR`). Loop Bass is a
#: high-pass in the loop, always in circuit: it sends a lap's value less the
#: mean the loop has been carrying, which can be larger than any value on the
#: line, so the per-lap argument (each lap's peak below the last) does not
#: hold, and the factor is measured. On the tape's own output, at Feedback
#: just under each step of `laps_to_zero`'s count from 0.004 to 0.85 and in
#: steps of 0.01 from 0.40, Loop Bass 20 to 1000 Hz, Time 20 to 500 ms, 48
#: and 22.05 kHz, on full-scale noise, random full-scale signs and clicks,
#: the longest tail took 1.49 times the count with each lap lengthened by
#: both one-poles' memory (Feedback 0.0039, Loop Bass 1 kHz, Loop Top
#: 16 kHz, Time 500 ms: three laps against two), 1.11 at Feedback 0.4999
#: (17 laps against 15) and 1.02 at 0.5312; the more laps the count
#: holds, the less the high-pass adds. Mono, Drive and a lower Loop Top
#: measured no longer. Twice the count leaves a third again over the worst.
LOOP_BASS_LAP_FACTOR = CUT_LAP_FACTOR

(TIME_I, FEEDBACK_I, GLIDE_I, DRIVE_I, LOOP_TOP_I, LOOP_BASS_I, TOP_CUT_I,
 LOW_CUT_I, DECAY_I, DAMPING_I, MIX_I) = range(11)

#: The constructor defaults, in macro order; NaN falls back to these.
DEFAULTS = (111.0, 0.375, 4000.0, 0.2, 6000.0, 100.0, 5000.0, 100.0, 1.8,
            4000.0, 0.35)

#: Each default's step on the 0-127 grid (`_component.macro_of`): patch 0.
#: While a macro that arrived as a whole step (the seed, a patch, a whole
#: `set_macro`) sits on its default's step, the default itself plays, so a
#: fresh instance, patch 0 and a host echoing `get_macro` all play exactly
#: 111 ms, not the step's 112.08. A constructor value that is not the
#: default is not a step and plays as given, even where it lands on one.
DEFAULT_STEPS = (68, 56, 76, 25, 82, 52, 74, 64, 65, 76, 22)

#: How close a 0..1 position must come to a default's step to play the
#: default: far under one grid step (1/127), far over a float's rounding.
STEP_TOLERANCE = 1e-6

#: The chamber's indices in `Reverb`'s macro table that this rack drives.
REVERB_DECAY_I = 1
REVERB_DAMPING_I = 5
REVERB_LOW_CUT_I = 7

#: The chamber at this rack's defaults on `Reverb`'s grid: Character 85
#: (chamber), Decay 65, Size 64 (1.004), Predelay 0 (the tape is the
#: predelay), Diffusion 99 (0.70), Damping 76, Bandwidth 127 (Top Cut is the
#: band), Low Cut 64, Mod Depth 19 (0.30 ms), Mod Rate 71 (0.89 Hz), Width
#: 102 (0.80), Tone 64 (0 dB), Mix 127 (the tail alone).
CHAMBER_PATCH = (85, 65, 64, 0, 99, 76, 127, 64, 19, 71, 102, 64, 127)

#: Which of the rack's macros drive which of the chamber's.
_CHAMBER_MACROS = ((LOW_CUT_I, REVERB_LOW_CUT_I), (DECAY_I, REVERB_DECAY_I),
                   (DAMPING_I, REVERB_DAMPING_I))


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


def slew_of(glide_ms):
    """`delay_slew` for a Glide: the whole Time range over Glide."""
    return FULL_RANGE_MS / float(glide_ms)


def _chamber_options():
    """`Reverb`'s constructor options at `CHAMBER_PATCH`'s grid values, so
    the Tank is cut once, as the chamber, and patch 0 moves no line."""
    spans = _reverb.Reverb._MACRO_RANGES
    names = ("decay", "size", "predelay_ms", "diffusion", "damping_hz",
             "bandwidth_hz", "low_cut_hz", "mod_depth_ms", "mod_rate_hz",
             "width", "tone_db", "mix")
    options = {"character": "chamber", "patch": 0}
    for index, name in zip(range(1, 13), names):
        mode = _reverb.Reverb.MACRO_MODES.get(index, "UNIPOLAR")
        position = _component.position_of_midi(mode, CHAMBER_PATCH[index])
        options[name] = _component.macro_value(spans[index], position)
    return options


class AirSpace(_component.Component):
    """A tape echo sent into a chamber. The module docstring is the
    player's page."""

    NAME = 'AirSpace'
    DISPLAY_NAME = 'Air Space'
    CATEGORIES = ('Effect Rack', 'Reverb')
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioecho", "audiobiquad", "audioroute", "audioverb")

    class _Chamber(_reverb.Reverb):
        """The rack's chamber: `Reverb` whose only patch is the chamber at
        the rack's settings, so its own `reset()` lands there without a
        re-cut. Nested, so the module holds one provider."""

        PATCHES = {0: ("Chamber", CHAMBER_PATCH)}

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    INPUT_CEILING_DBFS = -17.0
    TAIL_SAMPLES = None

    #: The exact-value flags, which a rack's reset puts back with the knobs.
    _KEPT = ("_snap",)

    MACRO_LABELS = ("Time", "Feedback", "Glide", "Drive", "Loop Top",
                    "Loop Bass", "Top Cut", "Low Cut", "Decay", "Damping",
                    "Mix")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
        8: "UNIPOLAR",
        9: "UNIPOLAR",
        10: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (TIME_MIN_MS, TIME_MAX_MS, "log"),  # 0  Time, ms
        (0.0, FEEDBACK_MAX),                # 1  Feedback
        (1000.0, 10000.0, "log"),           # 2  Glide, ms across the range
        (0.0, 1.0),                         # 3  Drive, the loop's soft clip
        (1000.0, 16000.0, "log"),           # 4  Loop Top, Hz
        (20.0, 1000.0, "log"),              # 5  Loop Bass, Hz
        (1000.0, 16000.0, "log"),           # 6  Top Cut, Hz
        (20.0, 500.0, "log"),               # 7  Low Cut, Hz
        (0.3, 10.0, "log"),                 # 8  Decay, s
        (500.0, 16000.0, "log"),            # 9  Damping, Hz
        (0.0, 2.0),                         # 10 Mix; dry at unity to 1
    )
    _MACRO_UNITS = {
        0: "ms", 2: "ms", 4: "Hz", 5: "Hz", 6: "Hz", 7: "Hz", 8: "s", 9: "Hz",
    }

    #: `_component.macro_of` of the card's settings; patch 0 is the
    #: constructor's defaults on the grid (`DEFAULT_STEPS`).
    PATCHES = {
        0: ("Chamber Send", DEFAULT_STEPS),
        1: ("Short Send", (43, 45, 76, 25, 82, 52, 82, 64, 50, 76, 22)),
        2: ("Long Send", (107, 90, 76, 25, 82, 52, 74, 64, 77, 76, 22)),
        3: ("Dark Loop", (68, 127, 76, 25, 32, 75, 74, 64, 65, 76, 22)),
        4: ("Bright Chamber",
            (68, 56, 76, 25, 82, 52, 114, 43, 72, 110, 22)),
        5: ("Driven Tape", (68, 75, 76, 102, 64, 52, 74, 64, 65, 76, 22)),
        6: ("Plain Chamber", (0, 0, 76, 25, 82, 52, 74, 64, 65, 76, 22)),
    }

    def _build(self, time_ms=111.0, feedback=0.375, glide_ms=4000.0,
               drive=0.2, loop_top_hz=6000.0, loop_bass_hz=100.0,
               top_cut_hz=5000.0, low_cut_hz=100.0, decay=1.8,
               damping_hz=4000.0, mix=0.35, patch=None):
        rate = self._sample_rate
        channels = self._channel_count
        options = (time_ms, feedback, glide_ms, drive, loop_top_hz,
                   loop_bass_hz, top_cut_hz, low_cut_hz, decay, damping_hz,
                   mix)
        values = []
        for index, value in enumerate(options):
            span = self._MACRO_RANGES[index]
            values.append(_between(_option(value, DEFAULTS[index]),
                                   span[0], span[1]))

        #: Per macro, whether its position arrived as a whole grid step and
        #: so plays the default on the default's step (`_value`). The
        #: constructor clears it for a value that is not the default.
        self._snap = [values[index] == DEFAULTS[index]
                      for index in range(len(values))]
        #: True once every macro has been seeded; before that a macro is
        #: stored and not pushed.
        self._ready = False
        #: True once the voices have been played (`_wire`).
        self._wired = False
        #: What the nodes were last handed, by name.
        self._handed = {}
        self._frames = 1
        #: The longest delay, in frames, the read head may still be at: a
        #: shorter Time walks the head down, so the old one holds until the
        #: tape is next emptied.
        self._reach = 1
        #: True from a tape clear to the next Time handed (`_clear_tape`).
        self._landing = False

        # The borrowed source's only reader: a width-1 MidSide passes it
        # byte for byte in the palette's blocks, and Mix 0 hands it out, so
        # whatever part of a source buffer it holds plays next whichever
        # way the output goes. Its reset forwards nothing.
        self._adapter = audioroute.MidSide(
            self._source, width=1.0, sample_rate=rate, channel_count=channels)
        # A MidSide with no source: a block of zeros per pull, which the
        # voices prime from when they are wired (`_wire`).
        self._hush = audioroute.MidSide(
            width=1.0, sample_rate=rate, channel_count=channels)
        self._in = audioroute.Port(self._hush)
        self._split = audioroute.Splitter(self._in, taps=2)
        self._fd = audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=channels, max_delay_ms=LINE_MS,
            delay_frames=whole_frames(DEFAULTS[TIME_I], rate),
            feedback=0.0, mix=2.0, damping_hz=0.0, cut_hz=0.0,
            loop_drive=0.0, delay_slew=0.0)
        self._fd.play(self._split.tap(1))
        self._lp = audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=self._hz(DEFAULTS[TOP_CUT_I]),
            sample_rate=rate, channel_count=channels)
        self._lp.play(self._fd)
        self._chamber = self._Chamber(self._lp, **_chamber_options())
        self._mixer = audiomixer.Mixer(
            voice_count=2, buffer_size=BLOCK * channels * 4,
            channel_count=channels, bits_per_sample=16, samples_signed=True,
            sample_rate=rate)
        # The output: a width-1 MidSide over the mixer, byte for byte, whose
        # reset forwards nothing. A host's reset of the output (a mixer
        # voice's `play()` does one) would otherwise reach the Mixer, and
        # CircuitPython's own Mixer drops frames there that audiodsp's
        # keeps.
        self._tail = audioroute.MidSide(
            self._mixer, width=1.0, sample_rate=rate, channel_count=channels)
        #: Where `audiocore.get_buffer` is compiled out, the one-voice
        #: mixer `_pull` primes from `_tail`; built the first time it is
        #: needed.
        self._puller = None
        self._silence = audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)), sample_rate=rate,
            channel_count=channels)

        # Walked tail first: the Mixer and the Splitter are not reset (a
        # voice resets its source, and neither voice holds a block between
        # two pulls), the chamber by its own reset, the filter and the tape
        # by their clears. Nothing here reaches the borrowed source.
        self._own(self._silence, reset=False)
        self._own(self._adapter, reset=False)
        self._own(self._hush, reset=False)
        self._own(self._in, reset=False)
        self._own(self._split, reset=False)
        self._own(self._fd, reset=self._clear_tape)
        self._own(self._lp, reset=self._lp.clear)
        self._own(self._chamber, reset=self._reset_chamber,
                  deinit=self._chamber.deinit)
        self._own(self._mixer, reset=False)
        self._own(self._tail, reset=False)
        self._output = self._adapter

        self._init_macros(tuple(values))
        # A default seeds its own step, so a fresh instance reads patch 0.
        for index in range(len(values)):
            if values[index] == DEFAULTS[index]:
                self._macros[index] = _component.position_of_midi(
                    "UNIPOLAR", DEFAULT_STEPS[index])
        self._ready = True
        for index in range(len(values)):
            self._apply_macro(index, self._macros[index])
        if patch is not None:
            self.program_change(patch)

    # -- the maps ------------------------------------------------------

    def _value(self, index):
        """Macro `index` in its own units: the default itself on the
        default's step when the position arrived as a step, the span's law
        elsewhere."""
        position = self._macros[index]
        step = DEFAULT_STEPS[index] / 127.0
        if self._snap[index] and abs(position - step) <= STEP_TOLERANCE:
            return DEFAULTS[index]
        return _component.macro_value(self._MACRO_RANGES[index], position)

    def macro(self, index):
        """What macro `index` currently stands for, in its own units: what
        plays, the default itself on the default's step."""
        self._check_live()
        return self._value(index)

    def set_macro(self, index, value, channel=0, note_id=-1,
                  sample_position=0):
        """Set macro `index` from the 0-127 scale. A whole step is a step
        and plays the default on the default's step; a fraction is a value
        of its own. A call that leaves the position where it is (a host
        echoing `get_macro`) changes neither."""
        self._check_live()
        self._macro_index(index)
        flags = list(self._snap)
        try:
            # Clamped first: an int past float's range (10**400) is the top
            # stop, and `%` on it would raise.
            value = _component.clamped_midi(value)
            position = _component.position_of_midi("UNIPOLAR", value)
            if abs(position - self._macros[index]) > STEP_TOLERANCE:
                fraction = value % 1.0
                limit = 127.0 * STEP_TOLERANCE
                self._snap[index] = (fraction <= limit
                                     or fraction >= 1.0 - limit)
            _component.Component.set_macro(
                self, index, value, channel, note_id, sample_position)
        except Exception:
            self._snap = flags
            raise

    def _apply_positions(self, positions, patch_index):
        """A patch lands every macro on a whole step, so every macro plays
        the default on the default's step again; a rack's restore (while
        `_seeding`) keeps the flags it put back (`_KEPT`). The one path a
        patch and a restore share."""
        flags = list(self._snap)
        if not self._seeding:
            self._snap = [True] * len(flags)
        try:
            _component.Component._apply_positions(self, positions,
                                                  patch_index)
        except Exception:
            self._snap = flags
            raise

    def _record(self):
        positions, patch_index, kept = _component.Component._record(self)
        return (positions, patch_index, (list(kept[0]),))

    def _restore(self, record):
        # Copy the flags: `set_macro` changes them in place, and the
        # rack's record must stay what the rack built.
        positions, patch_index, kept = record
        _component.Component._restore(
            self, (positions, patch_index, (list(kept[0]),)))

    def _dry_level(self, mix):
        """The dry voice's level, min(1, 2 - Mix). Unity is Q15 32768, which
        a Mixer voice passes through exactly on every lane
        (`MultiTapDelay._dry_level` has why)."""
        return 1.0 if mix <= 1.0 else 2.0 - mix

    def _levels(self):
        mix = self._value(MIX_I)
        voices = self._mixer.voice
        voices[0].level = self._dry_level(mix)
        voices[1].level = mix if mix < 1.0 else 1.0

    # -- hooks a planted fault overrides --------------------------------

    def _hand_tape(self, **settings):
        """Everything the tape node is handed goes through here."""
        self._handed.update(settings)
        self._fd.set(**settings)

    def _wet_source(self):
        """What the wet voice plays: the chamber."""
        return self._chamber.output

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        del position
        if not self._ready:
            return
        value = self._value(index)
        if index == TIME_I:
            frames = whole_frames(value, self._sample_rate)
            if frames < 1:
                frames = 1
            self._frames = frames
            if frames > self._reach or self._landing:
                # A tape just emptied lands its head on this Time, so the
                # head reaches no further than it (a reset from a longer
                # patch used to keep the longer Time in the tail).
                self._reach = frames
            self._landing = False
            self._hand_tape(delay_frames=frames)
        elif index == FEEDBACK_I:
            self._hand_tape(feedback=value)
        elif index == GLIDE_I:
            self._hand_tape(delay_slew=slew_of(value))
        elif index == DRIVE_I:
            self._hand_tape(loop_drive=value)
        elif index == LOOP_TOP_I:
            self._hand_tape(damping_hz=self._hz(value))
        elif index == LOOP_BASS_I:
            self._hand_tape(cut_hz=self._hz(value))
        elif index == TOP_CUT_I:
            frequency = self._hz(value)
            self._handed["top_cut_hz"] = frequency
            self._lp.frequency = frequency
        elif index == MIX_I:
            self._route()
        else:
            self._push_chamber(index)

    def _push_chamber(self, index):
        """Hand the chamber the rack's Low Cut, Decay or Damping, as the
        unquantized position of the value the rack plays."""
        for ours, theirs in _CHAMBER_MACROS:
            if ours == index:
                position = _component.macro_position(
                    self._MACRO_RANGES[ours], self._value(ours))
                self._chamber.set_macro(theirs, 127.0 * position)
                self._handed["chamber_%d" % theirs] = position

    def _route(self):
        """Mix 0 points the output at the input adapter (a wire); above 0 at
        the mixer, wiring it the first time and emptying what the graph
        held when it was routed around."""
        if self._value(MIX_I) <= 0.0:
            self._route_around(self._adapter)
            return
        self._levels()
        if not self._wired:
            self._wire()
        else:
            self._rejoin()
        self._output = self._tail

    def _wire(self):
        """Play the voices, the first time Mix is above 0.

        A voice's `play()` primes a block from its source. With the
        Splitter on `_hush` that block is zeros, and one pull of the mixer
        hands it out, so wiring takes nothing from the borrowed source and
        leaves no voice holding a block: whatever the adapter has handed
        out, the output has played. The graph is then emptied, so the
        chamber's modulation and the tape start where a `reset()` leaves
        them. The voices first play silence for one pull, which opens
        their level gates where `audiocore.get_buffer` exists
        (`_component.open_level_gates`)."""
        voices = self._mixer.voice
        for voice in voices:
            voice.play(self._silence, loop=True)
        self._pull()
        voices[0].play(self._split.tap(0))
        voices[1].play(self._wet_source())
        self._pull()
        self._in.play(self._adapter)
        self._clear_nodes()
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
            # smallest that hold a frame.
            self._puller = self._own(audiomixer.Mixer(
                voice_count=1, buffer_size=16,
                channel_count=self._channel_count, bits_per_sample=16,
                samples_signed=True, sample_rate=self._sample_rate),
                reset=False)
        voice = self._puller.voice[0]
        voice.play(self._tail)
        voice.stop()

    def _clear_tape(self):
        """Empty the tape. The node then lands its read head on the next
        Time it is handed instead of gliding there."""
        self._fd.clear()
        self._reach = self._frames
        self._landing = True

    def _reset_chamber(self):
        """The chamber's own reset lands on its one patch; the rack's three
        chamber macros then go back in."""
        self._chamber.reset()
        if self._ready:
            for ours, _theirs in _CHAMBER_MACROS:
                self._push_chamber(ours)

    # -- the contract's reads ------------------------------------------

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound: the tape's repeats, the Top Cut's ring and the
        chamber's own tail, end to end. The repeats are counted twice over
        (`LOOP_BASS_LAP_FACTOR`), a margin measured rather than derived."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`.

        The repeats (`_repeats_bound`); then `_component.biquad_ring` of
        the Top Cut; then the chamber's `tail_samples`. 0 at Mix 0, where
        the output is the input."""
        if self._value(MIX_I) <= 0.0:
            return 0
        ring = _component.biquad_ring(self._lp) or 0
        return int(self._repeats_bound() + ring + self._chamber.tail_samples)

    def _repeats_bound(self):
        """Frames until the tape's own output is exactly zero once the input
        stops: `LOOP_BASS_LAP_FACTOR` times `laps_to_zero`'s laps at the
        Feedback in force, each as long as the longest delay the read head
        may be at plus one frame for the interpolated read plus the memory
        of the loop's two one-poles."""
        rate = self._sample_rate
        top_memory, excess = tone_excess(self._handed["damping_hz"], rate)
        bass_memory, _bass = tone_excess(self._handed["cut_hz"], rate)
        laps = LOOP_BASS_LAP_FACTOR * laps_to_zero(self._handed["feedback"],
                                                   excess)
        return laps * (self._reach + 1 + top_memory + bass_memory)
