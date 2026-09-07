"""A noise gate after the Drawmer DS201, the box the trade calls the standard.

**What it sounds like.** Below the Threshold the signal is held down by the
*Range* you set - all the way out at -80 dB, or only 15 dB down, which is
what the DS201's own manual recommends: a gate that closes completely makes
the noise floor's coming and going more obvious than the noise ever was. A
crossing opens it over the *Attack*, holds it wide open for the *Hold*, and
only then lets it fall over the *Release*. That Hold is what makes the
gated-reverb snare: a long hold and a fast decay chop the tail off square.

**The key never touches the sound.** The detector listens through its own
band - *Key Low* and *Key High* - so a gate on a tom can be told to ignore
the hi-hat above it and the kick below it, and *Key Listen* puts that band on
the output so you can hear what you are tuning. Key Listen replaces the
audio; it is a listening position, not a mix. Give the class ``key=`` and
another stream drives the detector entirely, which is how one sound gates
another.

**Portability tier: audioif.** Built on ``audiodynamics.Dynamics``, which is
audioif's own module and not a CircuitPython port, so a stock CircuitPython
board raises ``ImportError`` at construction and says so. The default build
is **one node**: a per-sample peak detector, two key filters, a four-stage
envelope and a VCA, all in C, with Python computing coefficients only at
construction and on a macro move. There is no lean patch because there is
nothing to make lean.

**Latency is zero unless you ask for it.** ``lookahead_ms`` defaults to
``0.0`` and the class then reports ``latency_samples = 0``. Set it and the
detector reads ahead of the audio, so the gain is already up when the
transient arrives instead of a fraction of a millisecond after it -
**1.0 ms of look-ahead is 1.0 ms of latency**, 48 samples at 48 kHz, and the
cap is 50 ms. The knob buys low-frequency fidelity, not CPU: RaneNote 155
puts the smallest useful value at 16 samples (333 us at 48 kHz, enough for
750 Hz and above) and the live-sound limit "somewhere around" 2 ms.

**``duck=True`` inverts the whole sense**, for voice-overs: below threshold
the signal passes untouched, above it the signal is pushed down by Range.
It costs three more nodes - a ``Splitter``, a ``Multiply`` and a ``Mixer`` -
and with them a 32 KB splitter ring and a **source-block ceiling of 8192
frames**, so it is a construction option rather than a knob and a plain gate
pays none of it. Its depth is honest to about -40 dB; below that the
subtraction runs into int16's own floor (dossier G7).

**One thing the dossier asked for and this class does not do.** Its detector
is a peak detector, but the key band sits in front of it and never comes out
- the DS201's L.F. control bottoms at 25 Hz, it does not switch off - and a
one-pole high-pass overshoots a square wave's edges. So a square and a sine
of *equal peak* open the gate about 0.63 dB apart where the trait asks for
0.5, while the bare node with no key filters opens both at exactly the same
threshold. In practice: percussive, edgy material triggers this gate very
slightly earlier than a smooth tone of the same peak. Measured in
`docs/effects/NoiseGate-evidence.md` section 1, trait G6.

**And one setting that does less than the knob says.** In `duck=True` the
depth is honest to about -40 dB; past that the graph is subtracting two
nearly equal 16-bit streams and runs into their own quantisation - Range
-60 measures -59.5 dB and -80 measures -77.2. Plain gating has no such
limit: its depth is the node's own float.

The dossier is `docs/effects/NoiseGate.md` and the evidence pack that holds
this class to it is `docs/effects/NoiseGate-evidence.md`.
"""

import math

VENDOR = "PyDevices"

from .. import _component

try:
    import audiodynamics
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiodynamics = None
try:
    import audioroute
except ImportError:
    audioroute = None
try:
    import audiomath
except ImportError:
    audiomath = None

import array

import audiocore
import audiomixer


#: The gate machine in `audioif_dynamics.c:452` is on only when
#: `hold_frames != 0`, and below that the node is the memoryless computer
#: with its `over * 8.0f` slope, no hold and no one-shot. The Hold macro's
#: floor is what keeps it on: 2 ms is 96 frames at 48 kHz and 44 at
#: 22.05 kHz, so no rate reachable here rounds it to zero.
MINIMUM_HOLD_MS = 2.0

#: The one modulator value that inverts exactly: `(a * -32768) >> 15 == -a`
#: on signed int16 (`audioif_multiply.c:38`). +32767 does not - it is the
#: WIRE planted fault, 32767/32768 - which is why a built duck graph cannot
#: be switched back to a plain gate by levels alone.
INVERTING_LEVEL = -32768

#: Range is a depth, and 0 dB of ducking is no ducking. `20*log10(0)` is not
#: a number, so the duck's blend gain floors here instead; -120 dB leaves the
#: dry path a wire to well under an LSB.
SILENT_DB = -120.0


class NoiseGate(_component.Component):
    """Downward gate with Range, Hold and a two-ended key band (Drawmer
    DS201). See the module docstring."""

    NAME = 'NoiseGate'
    DISPLAY_NAME = 'Noise Gate'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    #: `audiodynamics` first, because that is the one the default build
    #: needs and the one a stock board's ImportError should name.
    #: `audioroute` and `audiomath` are built only by `duck=True`.
    REQUIRES = ("audiodynamics", "audioroute", "audiomath")

    #: The DS201 has no tempo control and neither has this: nothing here
    #: reads `self._transport()` (dossier D10).
    CAPABILITIES = ()

    #: The default build. `lookahead_ms` moves both of these, and the
    #: properties below report the instance rather than the class.
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Threshold", "Attack", "Hold", "Release", "Range",
                    "Key Low", "Key High", "Key Listen")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR", 5: "UNIPOLAR",
                   6: "UNIPOLAR", 7: "TOGGLE"}
    #: Range descends on purpose: 0 dB at the bottom of the knob is a wire,
    #: and the top is the deepest cut, which is how the panel reads.
    _MACRO_RANGES = (
        (-80.0, 0.0),                # 0 Threshold, dBFS
        (0.01, 1000.0, "log"),       # 1 Attack, ms
        (MINIMUM_HOLD_MS, 2000.0, "log"),   # 2 Hold, ms
        (2.0, 4000.0, "log"),        # 3 Release, ms
        (0.0, -80.0),                # 4 Range, dB of attenuation when shut
        (25.0, 4000.0, "log"),       # 5 Key Low, Hz
        (250.0, 35000.0, "log"),     # 6 Key High, Hz (clamped by _hz)
        (0.0, 1.0),                  # 7 Key Listen
    )
    PATCHES = {
        0: ("Default", (64, 51, 59, 77, 127, 0, 113, 0)),
        1: ("Tom Tighten", (79, 43, 63, 68, 64, 29, 71, 0)),
        2: ("Gated Reverb", (87, 33, 97, 38, 127, 0, 113, 0)),
        3: ("Vocal Breath Trim", (56, 63, 75, 84, 19, 22, 99, 0)),
        4: ("Amp Hiss", (48, 58, 72, 89, 127, 110, 89, 0)),
        5: ("Drum Bleed", (76, 43, 50, 62, 79, 35, 36, 0)),
    }

    THRESHOLD, ATTACK, HOLD, RELEASE, RANGE, KEY_LOW, KEY_HIGH, \
        KEY_LISTEN = range(8)

    #: `audioif_dynamics.h:104`. The node clamps for itself; the class
    #: clamps too so `latency_samples` reports what the node will do.
    MAX_LOOKAHEAD_MS = 50.0

    def _build(self, threshold_db=-40.0, attack_ms=1.0, hold_ms=50.0,
               release_ms=200.0, range_db=-80.0, key_low_hz=25.0,
               key_high_hz=20000.0, key_listen=False, duck=False,
               lookahead_ms=0.0, key_poles=1, key=None, patch=None):
        """Build the gate.

        `duck` and `lookahead_ms` are construction options rather than
        macros, and the dossier's section 6 says why. `key` is a borrowed
        second source for the detector - the DS201's Ext jack - which this
        class never owns, resets or deinitialises; a key that runs dry
        before the audio does starves the node into silence
        (`audiodynamics/Dynamics.c:255-259`). `key_poles` is 1 or 2 poles on
        each end of the key band, measured upstream at 5.29 and
        10.31 dB/octave.
        """
        lookahead_ms = min(max(float(lookahead_ms), 0.0),
                           self.MAX_LOOKAHEAD_MS)
        #: The node's own conversion, `audioif_dynamics.c:126-127`, so the
        #: reported latency is the frame count the C will actually hold.
        self._latency = int(lookahead_ms * self._sample_rate / 1000.0)
        self._duck = bool(duck)

        if self._duck:
            self._split = self._own(
                audioroute.Splitter(source=self._source, taps=2),
                reset=False, deinit=False)
            gate_input = self._own(self._split.tap(0))
            dry = self._own(self._split.tap(1))
        else:
            self._split = None
            gate_input = self._source
            dry = None

        self._dyn = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_GATE,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            threshold_db=threshold_db,
            attack_ms=attack_ms,
            release_ms=release_ms,
            hold_ms=max(float(hold_ms), MINIMUM_HOLD_MS),
            depth_db=range_db if not self._duck else -80.0,
            sidechain_hz=self._hz(key_low_hz),
            sidechain_lp_hz=self._hz(key_high_hz),
            sidechain_poles=2 if int(key_poles) >= 2 else 1,
            lookahead_ms=lookahead_ms))
        self._dyn.play(gate_input)
        if key is not None:
            self._dyn.key(key)

        if self._duck:
            # x - b.g.x, with b in the node's own makeup_gain so the depth
            # is a float rather than the Mixer's Q15 voice level.
            self._modulator = self._own(audiocore.RawSample(
                array.array("h", [INVERTING_LEVEL] * self._channel_count),
                sample_rate=self._sample_rate,
                channel_count=self._channel_count))
            self._invert = self._own(audiomath.Multiply(
                mix=1.0, sample_rate=self._sample_rate,
                channel_count=self._channel_count))
            self._invert.play(self._dyn)
            self._invert.modulate(self._modulator)
            self._dry = dry
            self._mixer = self._own(audiomixer.Mixer(
                voice_count=2, **self._pcm()), reset=self._reset_mixer)
            self._wire_mixer()
            self._output = self._mixer
        else:
            self._dry = None
            self._modulator = self._invert = self._mixer = None
            self._output = self._dyn

        self._init_macros((threshold_db, attack_ms,
                           max(float(hold_ms), MINIMUM_HOLD_MS), release_ms,
                           range_db, key_low_hz, key_high_hz,
                           1.0 if key_listen else 0.0), patch)

    def _wire_mixer(self):
        self._mixer.voice[0].play(self._dry)
        self._mixer.voice[1].play(self._invert)

    def _reset_mixer(self):
        """Clear the duck's summing mixer and hand its voices back.

        Upstream CircuitPython's `Mixer.reset_buffer` **stops** its voices
        (`audioif/src/audiomixer/MixerVoice.c:91`, which says so in as many
        words), and the patched CircuitPython build carries the upstream
        one: measured on `cmods/bin/circuitpython-effects`, a mixer playing
        a sample reads 8000 LSB before `audiocore.reset_buffer` and 0 after
        it, for good. audioif's own `audiomixer` does not do that - the
        same probe reads 8000 both sides on CPython and on desktop
        MicroPython - so a duck build reset through the base class's walk
        would go silent on one interpreter of three and nowhere else.
        Re-playing the voices costs nothing on the builds that never
        needed it.
        """
        audiocore.reset_buffer(self._mixer)
        self._wire_mixer()

    # -- the live surface ---------------------------------------------

    @property
    def latency_samples(self):
        """The look-ahead, in frames, and nothing else.

        Overridden because `_component` keeps `LATENCY_SAMPLES` on the
        class, and `lookahead_ms` is a per-instance choice: two gates in one
        graph may legitimately report different figures.
        """
        self._check_live()
        return self._latency

    @property
    def tail_samples(self):
        """The same number: what is left to come out after the input goes
        quiet is exactly the audio held in the look-ahead buffer. Nothing
        here has a feedback path or a delay line."""
        self._check_live()
        return self._latency

    # -- macros -------------------------------------------------------

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index == self.THRESHOLD:
            self._dyn.set(threshold_db=value)
        elif index == self.ATTACK:
            self._dyn.set(attack_ms=value)
        elif index == self.HOLD:
            self._dyn.set(hold_ms=value)
        elif index == self.RELEASE:
            self._dyn.set(release_ms=value)
        elif index == self.RANGE:
            self._apply_range(value)
        elif index == self.KEY_LOW:
            self._dyn.set(sidechain_hz=self._hz(value))
        elif index == self.KEY_HIGH:
            self._dyn.set(sidechain_lp_hz=self._hz(value))
        else:
            self._apply_key_listen(value >= 0.5)

    def _apply_range(self, range_db):
        """Range is the node's own depth when gating, and the blend gain of
        the subtracted branch when ducking."""
        if not self._duck:
            self._dyn.set(depth_db=range_db)
            return
        blend = 1.0 - (10.0 ** (range_db / 20.0))
        self._dyn.set(makeup_db=(20.0 * math.log10(blend))
                      if blend > 1e-6 else SILENT_DB)

    def _apply_key_listen(self, listening):
        self._dyn.set(key_listen=1.0 if listening else 0.0)
        if self._duck:
            # Key Listen replaces the output, so the dry half of the duck
            # comes out of the sum; what is left is the key band with its
            # sign flipped, which is the band and not a mix.
            self._mixer.voice[0].level = 0.0 if listening else 1.0
