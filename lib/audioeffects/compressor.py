"""`Compressor` - four compressor characters over one palette.

Rebuilt from scratch at Phase 2 against `workspace docs/effects-internal/dossiers/Compressor.md`, whose
trait table was frozen at Station A on 2026-09-07. The four characters are
the dossier's four standouts, and they differ in **detector law, release law,
ratio law and side-chain weighting** - not in three time constants, which is
all the class this replaces had (dossier §7.2).

* **`fet`** - the 1176. Peak detector, both time knobs live and *faster
  clockwise* across 800 to 20 microseconds and 1.1 seconds to 50
  milliseconds, threshold rising with ratio. Turn everything up and it
  distorts, which is the sound the panel's all-buttons-in trick is famous for.
* **`optical`** - the LA-2A, and the default. **Attack, Release, Release Slow
  and Memory do nothing here**, because the T4 cell sets both times and the
  unit has no time knobs: ten milliseconds of attack, half the recovery in the
  first sixty milliseconds and the rest over a couple of seconds, slower after
  a long or a deep passage. That inertness is trait O3 and is measured, not
  asserted.
* **`vca`** - the dbx 160. A true-RMS detector, so a square and a sine of the
  same RMS get the same gain where a peak detector is 3 dB apart on them, and
  a release that is a straight line in decibels rather than an exponential.
* **`varimu`** - the Fairchild 670. No ratio to speak of: the slope climbs
  with level, from gentle on small peaks to a hard limit on loud ones, and
  the six factory time-constant positions are patches 8 through 13.

**Two `Dynamics` in series**, fast then slow. The slow one is the *second
release stage*: its own attack runs in seconds, so its envelope is still
climbing after a short burst and settled after a long one, which is a memory
of how long the passage was without a new state variable. At `Memory` 0 it is
set to `ratio=1`, which is byte-identical to a wire, so a single-stage patch
pays the node and none of its sound.

**Latency is zero at every setting**, both rates, every patch: this class
builds no latency-adding option at all. `lookahead_ms` stays at its default 0
and is not on the surface - lookahead belongs to `Limiter`, where the latency
buys a brickwall. `tail_samples` is 0 for the same reason a compressor has no
tail: the gain multiplies the audio, so silence in is silence out on the same
sample.

**Two traits this palette cannot carry, recorded rather than hidden**
(dossier App. J.3, J.4):

* The side chain is **feed-forward on all four characters**. The node does
  have a `feedback_detector`, and the 1176, the LA-2A and the 670 are all
  feedback designs - but on this gain computer a feedback detector settles at
  half the overshoot, 2:1 effective, at *every* ratio setting, so a character
  that also has to make 4:1 through 20:1 cannot use it.
* On the `vca` character the RMS averaging window trait V3 needs floors the
  attack above the 3 ms trait V2 asks for at 30 dB over threshold. The
  shipped patch takes the RMS detector, which is the dbx's headline; V2's
  level-dependent attack law is demonstrated on the peak detector instead.

**What it does not do, and where.** Three of the dossier's claims did not
survive the Phase 2 refutation pass and its gate audit, and the class was
not edited to save them: the numbers below are this class's own behaviour
at settings a player dials, measured over the span each row quantifies
over rather than at one point
(`workspace docs/effects-internal/evidence/Compressor-evidence.md` section 1).

* **It is not clean on bass material with a fast release.** At 10 dB of
  gain reduction on a 50 Hz tone, patch 1 reads **0.021 %** THD at the
  Release knob's slow end and **3.89 %** at its fast end, against the
  dossier's 0.5 % bar, and **three of the four `fet` patches are over that
  bar at 50 Hz** (1.13 / 0.94 / 1.09 %) - the fourth is All-Button, which
  is meant to be dirty. Patch 0 `Level Ride`, the constructor's own
  defaults, reads 0.83 % on the same probe, on a character whose rows state
  no cleanliness bar at all. The bar holds under 0.5 % for a release slower
  than about 300 ms at 50 Hz, about 80 ms at 200 Hz, and at every Release
  position at 1 kHz (0.24 % at the fast end). That is the envelope
  following the waveform, which is what a fast peak compressor does to a
  bass note - the 1176 does it too - but traits F5 and V6 said "clean
  everywhere except All-Button", so they are **disconfirmed** and bounded
  here.
* **The true-RMS detector stops being level-honest below about 65 Hz.**
  Trait V3 is the dbx's: a square and a sine of the same RMS get the same
  gain where a peak detector is 3 dB apart on them. Measured on patch 3,
  they are 0.079 dB apart at 400 Hz, 0.322 at 100 Hz, **0.509 at 63 Hz and
  0.769 at 40 Hz** against a 0.5 dB bar, because the shipped 10 ms window
  cannot average a 50 Hz square. The fix is on the surface: at the `RMS
  Window` macro's 100 ms end the same reading is **0.086 dB** at 50 Hz.
* **The FET threshold tilt holds at Threshold −8 dB and below, not
  below −4.2 dB.** F2's rise is 6 dB per decade of ratio above 4:1 —
  4.18 dB at 20:1. The independent refutation of 2026-09-07 (commit
  `17a4cc9`) attacked inside the old bound: at Threshold −7 dB the
  fitted knee is 12.0 / 8.5 / 6.5 / 10.5 (20:1 widens), and at −6 dB
  and −5 dB both columns fail. At −12 / −10 / −8 and at the row's own
  −36 dB the threshold still rises and the knee still narrows. The
  0 dBFS curve window cannot finish a narrowing knee once the 20:1
  tilt has pushed the threshold near the ceiling; the 0 dB clamp then
  wrecks the 20:1 point from about −5.5 dB up. F2 is demonstrated at
  Threshold −8 dB and below.

`capabilities` is `()`: a compressor's timing is program-dependent, not
tempo-dependent, and nothing here reads the transport.
"""

VENDOR = "PyDevices"

import math

from . import _component

try:
    import audiodynamics
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiodynamics = None

try:
    import audioroute
except ImportError:      # ditto
    audioroute = None

import audiomixer


#: Macro 0's four positions, in order.
FET = 0
OPTICAL = 1
VCA = 2
VARIMU = 3

#: The T4 cell's own times, in milliseconds. The `optical` character ignores
#: macros 3 through 6 and uses these instead (trait O3); they are also what
#: the optical rows of `_DEFAULTS` carry, so patch 0 round-trips.
OPTICAL_ATTACK_MS = 10.0
OPTICAL_RELEASE_MS = 60.0
OPTICAL_RELEASE_SLOW_MS = 2200.0
OPTICAL_MEMORY = 0.62

#: The time macros are labelled in the times a *measurement* reads, not in
#: the node's coefficients, because every trait that names a time names a
#: measured one: F1's 800 microseconds and 1.1 seconds, M2's six pairs. The
#: node's one-pole envelope stretches a coefficient into a 10-90 % attack by
#: 1.534 and shrinks it into a t63 release by 0.795 - both measured on this
#: build across the spans they are used over (attack 0.098 to 96 ms: 1.6416,
#: 1.5363, 1.5337, 1.5340, 1.5267; release 50 to 1100 ms: 0.7894, 0.7939,
#: 0.7995), so the class divides them out once, here.
ATTACK_MEASURED_PER_SET = 1.534
RELEASE_MEASURED_PER_SET = 0.795

#: The slow stage's attack, as a fraction of its release, and the range it is
#: held to. Long enough that a short burst leaves the slow envelope still
#: climbing - which is the memory - and short enough that a long one settles.
SLOW_ATTACK_FRACTION = 0.5
SLOW_ATTACK_MIN_MS = 50.0
SLOW_ATTACK_MAX_MS = 4000.0

#: How far below the fast stage's threshold the slow stage sits. The slow
#: stage reads the fast stage's output, which is already reduced.
SLOW_THRESHOLD_OFFSET_DB = -5.0

#: The 1176's ratio buttons move the threshold and the knee with them - the
#: manual's own line is that "higher Ratio settings also set the threshold
#: higher", and S3 reads the knee hardening off UREI's transfer plot (trait
#: F2). On the `fet` character the ratio therefore tilts both: the threshold
#: up by `FET_RATIO_TILT_DB` per decade of ratio above 4:1, and the knee down
#: by the square root of the same. No other character does this.
FET_RATIO_REFERENCE = 4.0
FET_RATIO_TILT_DB = 6.0

#: `Memory` 1.0 puts the slow stage at this ratio; 0.0 puts it at 1, a wire.
SLOW_RATIO_SPAN = 3.0

#: Per-character defaults, in the macros' own engineering units, one row per
#: character in macro order. Row 0 is also patch 0's source of truth.
_DEFAULTS = {
    #        char  thr   ratio  atk    rel     slow   mem   knee det  rms  emph  ehz  mkup mix
    FET:     (0.0, -20.0, 12.0,   0.4,  200.0, 2000.0, 0.0,  3.0, 0.0, 10.0, 0.0, 100.0, 0.0, 1.0),
    OPTICAL: (1.0, -20.0,  3.0,  10.0,   60.0, 2200.0, 0.62, 8.0, 0.0, 10.0, 0.0, 100.0, 0.0, 1.0),
    VCA:     (2.0, -20.0,  4.0,   1.0,   52.0, 2000.0, 0.0,  0.0, 1.0, 10.0, 0.0, 100.0, 0.0, 1.0),
    VARIMU:  (3.0, -24.0, 20.0,   0.4, 2000.0, 6000.0, 0.0, 30.0, 0.0, 10.0, 0.0, 100.0, 0.0, 1.0),
}


class Compressor(_component.Component):
    """Four compressor characters on two `audiodynamics.Dynamics` nodes."""

    NAME = 'Compressor'
    DISPLAY_NAME = 'Compressor'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiodynamics", "audioroute")

    CAPABILITIES = ()
    #: No latency-adding option is built, so this is 0 at every setting.
    LATENCY_SAMPLES = 0
    #: The gain multiplies the audio; silence in is silence out on the same
    #: sample, so there is no tail to declare.
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Character", "Threshold", "Ratio", "Attack", "Release",
                    "Release Slow", "Memory", "Knee", "Detector",
                    "RMS Window", "Emphasis", "Emphasis Freq", "Makeup",
                    "Mix")
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
        4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
        8: "TOGGLE", 9: "UNIPOLAR", 10: "UNIPOLAR", 11: "UNIPOLAR",
        12: "UNIPOLAR", 13: "UNIPOLAR",
    }
    #: Attack, Release and Release Slow run high-to-low on purpose: trait F1
    #: is that both time knobs get *faster* as the macro rises, which is the
    #: 1176's panel. `logmap` is monotone either way.
    _MACRO_RANGES = (
        (0.0, 3.0),                     # 0  Character
        (-60.0, 0.0),                   # 1  Threshold, dB
        (1.0, 1000.0, "log"),           # 2  Ratio
        (300.0, 0.02, "log"),           # 3  Attack, ms - faster clockwise
        (5000.0, 20.0, "log"),          # 4  Release, ms - faster clockwise
        (25000.0, 100.0, "log"),        # 5  Release Slow, ms
        (0.0, 1.0),                     # 6  Memory
        (0.0, 36.0),                    # 7  Knee, dB
        (0.0, 1.0),                     # 8  Detector: >= 0.5 is RMS
        (1.0, 100.0, "log"),            # 9  RMS Window, ms
        (0.0, 1.0),                     # 10 Emphasis
        (30.0, 2000.0, "log"),          # 11 Emphasis Freq, Hz
        (-12.0, 24.0),                  # 12 Makeup, dB
        (0.0, 1.0),                     # 13 Mix
    )

    #: Patches 8-13 are the Fairchild's six TIME CONSTANT positions, in the
    #: manual's order, and are the only patches traits M2 and M3 are read on.
    PATCHES = {
        0: ("Level Ride",
            (42, 85, 20, 45, 102, 56, 79, 28, 0, 64, 0, 36, 42, 127)),
        1: ("Fast Peak Catch",
            (0, 89, 46, 122, 95, 58, 0, 11, 0, 64, 0, 36, 53, 127)),
        2: ("Everything At Once",
            (0, 55, 55, 127, 127, 58, 0, 0, 0, 64, 0, 36, 71, 127)),
        3: ("Bus Glue",
            (85, 80, 25, 75, 105, 58, 0, 0, 127, 64, 0, 36, 56, 127)),
        4: ("Voice Ride",
            (42, 68, 38, 45, 102, 56, 79, 28, 0, 64, 102, 112, 56, 127)),
        5: ("Let The Stick Through",
            (0, 89, 38, 36, 102, 58, 0, 11, 0, 64, 0, 36, 56, 127)),
        6: ("Parallel Squash",
            (0, 55, 55, 127, 127, 58, 0, 0, 0, 64, 0, 36, 71, 51)),
        7: ("Wide Knee Glue",
            (85, 85, 13, 75, 74, 58, 0, 85, 127, 64, 0, 36, 49, 127)),
        8: ("Vari-Mu TC1",
            (127, 76, 55, 97, 65, 42, 0, 106, 0, 64, 0, 36, 42, 127)),
        9: ("Vari-Mu TC2",
            (127, 76, 55, 97, 42, 42, 0, 106, 0, 64, 0, 36, 42, 127)),
        10: ("Vari-Mu TC3",
             (127, 76, 55, 87, 21, 42, 0, 106, 0, 64, 0, 36, 42, 127)),
        11: ("Vari-Mu TC4",
             (127, 76, 55, 87, 0, 42, 0, 106, 0, 64, 0, 36, 42, 127)),
        12: ("Vari-Mu TC5",
             (127, 76, 55, 87, 21, 26, 95, 106, 0, 64, 0, 36, 42, 127)),
        13: ("Vari-Mu TC6",
             (127, 76, 55, 97, 65, 26, 95, 106, 0, 64, 0, 36, 42, 127)),
        # Patch 1's settings under the name the gate reads. Memory 0
        # lets this patch drop the slow stage from the pull chain.
        14: ("Compressor - lean",
             (0, 89, 46, 122, 95, 58, 0, 11, 0, 64, 0, 36, 53, 127)),
    }

    def _build(self, character="optical", patch=None, **overrides):
        """`character` names one of the four; anything else is a macro value
        in its own units - `threshold_db`, `ratio`, `attack_ms`,
        `release_ms`, `release_slow_ms`, `memory`, `knee_db`, `detector`,
        `rms_window_ms`, `emphasis`, `emphasis_hz`, `makeup_db`, `mix`."""
        index = _character_index(character)
        values = list(_DEFAULTS[index])
        for name, value in overrides.items():
            try:
                slot = _OVERRIDES[name]
            except KeyError:
                raise TypeError("Compressor got an unexpected option %r"
                                % (name,))
            values[slot] = float(value)

        # `audioroute.Splitter` exposes neither `reset` nor `deinit` (its
        # Python surface is `tap` alone), and a tap's `reset_buffer` is a
        # documented no-op - "the cursors belong to the Splitter and the
        # other taps are still reading from them"
        # (`audioif/src/audioroute/SplitterTap.c:47-55`). So the splitter is
        # enumerated but neither walk names it, and the two taps carry the
        # deinit. That is a palette gap, not a choice: see the evidence
        # pack's §11.
        split = self._own(audioroute.Splitter(self._source, taps=2),
                          reset=False, deinit=False)
        self._wet_tap = self._own(split.tap(0), reset=False)
        self._dry_tap = self._own(split.tap(1), reset=False)
        self._fast = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS, sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._slow = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS, sample_rate=self._sample_rate,
            channel_count=self._channel_count))
        self._fast.play(self._wet_tap)
        self._slow.play(self._fast)

        # `reset=False` on the mixer, measured rather than assumed:
        # `audiomixer_mixer_reset_buffer` (`audioif/src/audiomixer/Mixer.c:
        # 208-214`) does nothing of its own - it only resets its voices, and
        # a voice's reset re-fetches from whatever it plays. Through the
        # dry tap that reaches the borrowed source, and because the Splitter
        # ahead of it cannot be rewound the re-fetch *advances* the probe by
        # the ring's fill (measured: 12064 frames, 251 ms at 48 kHz) instead
        # of rewinding it. Tier 1 asks that `reset()` leave the borrowed
        # source untouched, so the walk stops here; the mixer has no state
        # of its own to clear, and the two Dynamics nodes below it do.
        mixer = self._own(audiomixer.Mixer(voice_count=2, **self._pcm(1024)),
                          reset=False)
        mixer.voice[0].play(self._slow)
        mixer.voice[1].play(self._dry_tap)
        self._mixer = mixer
        self._wet = mixer.voice[0]
        self._dry = mixer.voice[1]
        self._output = mixer

        self._character = index
        self._routed_lean = False
        self._init_macros(tuple(values), patch)

    # -- the macro surface --------------------------------------------

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index == 0:
            self._character = int(round(value))
            self._push_detector()
            self._push_gain_computer()
            self._push_times()
            self._push_slow()
        elif index in (1, 2, 7):
            self._push_gain_computer()
        elif index in (3, 4):
            self._push_times()
        elif index in (5, 6):
            self._push_slow()
        elif index in (8, 9):
            self._push_detector()
        elif index in (10, 11):
            self._push_emphasis()
        elif index == 12:
            if self._lean():
                self._fast.set(makeup_db=value)
            else:
                self._slow.set(makeup_db=value)
        else:
            self._wet.level = value
            self._dry.level = 1.0 - value

    def _push_gain_computer(self):
        """Threshold, ratio and knee together, because on the `fet`
        character the ratio moves the other two (F2)."""
        threshold_db = self.macro(1)
        ratio = self.macro(2)
        knee_db = self.macro(7)
        if self._character == FET and ratio > FET_RATIO_REFERENCE:
            decades = math.log(ratio / FET_RATIO_REFERENCE) / math.log(10.0)
            threshold_db += FET_RATIO_TILT_DB * decades
            if threshold_db > 0.0:
                threshold_db = 0.0
            knee_db *= math.sqrt(FET_RATIO_REFERENCE / ratio)
        self._fast.set(threshold_db=threshold_db)
        self._fast.set(ratio=ratio)
        self._fast.set(knee_db=knee_db)
        self._slow.set(threshold_db=threshold_db + SLOW_THRESHOLD_OFFSET_DB)

    def _push_times(self):
        """The fast stage's attack and release. `optical` ignores the macros:
        the T4 sets both times and the LA-2A has no time knobs (O3)."""
        if self._character == OPTICAL:
            attack_ms = OPTICAL_ATTACK_MS
            release_ms = OPTICAL_RELEASE_MS
        else:
            attack_ms = self.macro(3)
            release_ms = self.macro(4)
        self._fast.set(attack_ms=attack_ms / ATTACK_MEASURED_PER_SET)
        self._fast.set(release_ms=release_ms / RELEASE_MEASURED_PER_SET)

    def _push_slow(self):
        """The second release stage. At `Memory` 0 the stage is `ratio=1`,
        which renders byte-identical to its input (dossier App. J.2)."""
        if self._character == OPTICAL:
            release_ms = OPTICAL_RELEASE_SLOW_MS
            memory = OPTICAL_MEMORY
        else:
            release_ms = self.macro(5)
            memory = self.macro(6)
        attack_ms = release_ms * SLOW_ATTACK_FRACTION
        if attack_ms < SLOW_ATTACK_MIN_MS:
            attack_ms = SLOW_ATTACK_MIN_MS
        elif attack_ms > SLOW_ATTACK_MAX_MS:
            attack_ms = SLOW_ATTACK_MAX_MS
        self._slow.set(ratio=1.0 + SLOW_RATIO_SPAN * memory)
        self._slow.set(attack_ms=attack_ms)
        self._slow.set(release_ms=release_ms / RELEASE_MEASURED_PER_SET)

    def _push_detector(self):
        """Peak or true-RMS, and the RMS averaging window. `program_attack`
        rides with the character, not the macro: it is the dbx's detector law
        (V2), scaling the attack by the root of the overshoot."""
        if self._macros[8] >= 0.5:
            self._fast.set(detector="rms")
            self._fast.set(rms_ms=self.macro(9))
        else:
            self._fast.set(detector="peak")
        self._fast.set(program_attack=self._character == VCA)

    def _push_emphasis(self):
        """The side-chain high-pass. At `Emphasis` 0 the corner is 0, which
        the kernel reads as full band - so the default is exactly flat, which
        is the half of O4 the LA-2A's factory setting stands for."""
        emphasis = self.macro(10)
        if emphasis <= 0.0:
            self._fast.set(sidechain_hz=0.0)
        else:
            self._fast.set(sidechain_hz=self._hz(self.macro(11) * emphasis))

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        super().program_change(index, channel, note_id, sample_position)
        self._route()

    def _lean(self):
        """Patch 14 `Compressor - lean` is the only pull chain that
        drops the slow stage. Every other patch keeps both Dynamics."""
        return self._patch_index == 14

    def _route(self):
        """Rewire the mixer wet voice only when entering or leaving
        patch 14. `play()` on a Dynamics node re-inits it, so the
        Dynamics connections stay as `_build` left them."""
        lean = self._lean()
        if lean == self._routed_lean:
            return
        if lean:
            self._wet.play(self._fast)
            self._fast.set(makeup_db=self.macro(12))
            self._slow.set(makeup_db=0.0)
        else:
            self._wet.play(self._slow)
            self._fast.set(makeup_db=0.0)
            self._slow.set(makeup_db=self.macro(12))
        self._routed_lean = lean
        if self._output is not self._source:
            self._output = self._mixer

    # -- what the meters read -----------------------------------------

    @property
    def gain_reduction_db(self):
        """What the last processed block was reduced by, both stages summed.
        A meter reading, not part of the contract's surface."""
        self._check_live()
        return (self._fast.gain_reduction_db()
                + self._slow.gain_reduction_db())


#: Constructor `character=` names, in macro-0 order.
_CHARACTERS = ("fet", "optical", "vca", "varimu")

#: Constructor keywords that seed a macro, by macro index.
_OVERRIDES = {
    "threshold_db": 1, "ratio": 2, "attack_ms": 3, "release_ms": 4,
    "release_slow_ms": 5, "memory": 6, "knee_db": 7, "detector": 8,
    "rms_window_ms": 9, "emphasis": 10, "emphasis_hz": 11,
    "makeup_db": 12, "mix": 13,
}


def _character_index(character):
    if isinstance(character, str):
        try:
            return _CHARACTERS.index(character)
        except ValueError:
            raise ValueError("Compressor has no %r character; it has %s"
                             % (character, ", ".join(_CHARACTERS)))
    index = int(character)
    if not 0 <= index < len(_CHARACTERS):
        raise ValueError("character index must be 0..%d"
                         % (len(_CHARACTERS) - 1))
    return index
