"""`Expander` - a downward expander in the Drawmer DS201's shape.

The dossier is `docs/effects/Expander.md`; the evidence pack that grades it
is `docs/effects/Expander-evidence.md`. What a reader needs here:

**What it is.** Below the threshold the output falls `ratio` dB for every
dB the input falls, down to a floor the Depth knob sets - so a quiet
passage gets quieter without the door-slam of a gate. Above the threshold
it is a wire. The side chain is a two-ended key band (12 dB/octave at each
end, `sidechain_poles=2`), the detector is true RMS by default, and an
external key stream may drive it instead of the audio.

**Portability tier: audioif.** `audiodynamics` is audioif's own module and
not a CircuitPython port (`audioif/docs/upstream-diff.md:661`), so the
import below is guarded and construction raises `ImportError` on a stock
CircuitPython board.

**Latency is zero, at every setting, and no option adds any.** Neither
source reached shows a delay element in the DS201's audio path, and
RaneNote 155 puts look-ahead in the *gate*'s block diagram rather than the
expander's - so this class ships no look-ahead option at all and there is
no latency-adding option to name a millisecond figure for.
`latency_samples` is 0; measured, an impulse comes back in the frame it
arrived in. One delay is worth naming and is *not* latency: narrowing the
key band slows the detector's response to a transient, which the DS201's
own manual warns about. That is a detector effect and is never reported in
`latency_samples`.

**The tail is zero, with one named exception.** The gain is a per-sample
multiply on the audio, so silence in is exactly zero out in the same frame
however the envelope stands - measured on the kit's `burst_silence` probe,
there is no non-zero sample after the burst at all, at any of the three
rates. Key Listen is the exception: it puts the *side chain's* signal on the
output instead of the audio, and the key high-pass has memory, measured on
that probe at 2373 / 2180 / 1089 frames at 48 / 44.1 / 22.05 kHz with Key Low
at its minimum. That is a diagnostic state, off in every patch, and it is
recorded rather than folded into `tail_samples`.

**Two wire states, both byte-identical to the source:** Ratio at 1.0, where
the gain computer's `over x (ratio - 1)` is zero, and Depth at 0 dB, where the
floor is zero. Measured, worst 0 LSB on a full-scale ramp.

**Three things the dossier asked for that this class does not do**, each
measured rather than assumed, each with its number in the evidence pack:

* **No Hold, and no one-shot envelope** (dossier E5). The node's
  closed/attack/hold/decay machine is gated on `mode ==
  AUDIOIF_DYNAMICS_GATE` (`audioif/src/shared/audioif_dynamics.c:452-453`)
  and *replaces* the gain computer with a binary open/floor
  (`:679-724`), so the ratio law and the one-shot envelope cannot both
  exist in one node. `hold_ms` in `DYN_EXPAND` is silently inert -
  measured, a 1 ms burst under a 200 ms attack renders the same trace with
  and without it. An expander is the continuous law; `NoiseGate` is the
  box with the trigger, and E5 is that class's to demonstrate.
* **The key band is 12 dB/octave, not a brick wall** (dossier E3). Two
  poles at each end reject about 25 dB two octaves outside the band, so a
  loud out-of-band tone *will* open the expander. E3 as the dossier states
  it - the gain held at its floor for an out-of-band tone all the way to
  0 dBFS - would need better than 40 dB an octave out, which is an
  eighth-order key filter no hardware gate carries.
* **The knob times are one-pole time constants** (dossier E6), not
  10-90 % times. `attack_ms` and `release_ms` are the follower's tau; the
  10-90 % time of the gain-in-dB trace depends on the size of the level
  step as well as on the setting.

**The detector's own window.** With `detector="rms"` the level is a
one-pole mean square over a fixed 10 ms window (the node's unset default,
`audioif_dynamics.c:77-82`). That window is what makes a sine and a square
of equal RMS get the same gain, and it also puts a floor of its own order
under the Attack knob. The Detector toggle's peak position removes both.
"""

VENDOR = "PyDevices"

from .. import _component

try:
    import audiodynamics
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiodynamics = None


class Expander(_component.Component):
    """Downward expander: below the threshold, quiet gets quieter, by a
    settable ratio and down to a settable floor."""

    NAME = 'Expander'
    DISPLAY_NAME = 'Expander'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiodynamics",)

    #: Nothing in an expander's law refers to tempo, and neither source's
    #: unit has a tempo input (dossier App. I, D10). The transport is never
    #: read, so nothing is declared.
    CAPABILITIES = ()

    #: No look-ahead, no delay line: the gain lands on the frame the
    #: detector read. Measured by CLICK at 48 kHz and 44.1 kHz.
    LATENCY_SAMPLES = 0

    #: The VCA is a per-sample multiply on the audio, so silence in is
    #: exactly zero out in the same frame however the envelope stands. The
    #: Key Listen diagnostic is the one path with memory of its own, and it
    #: is off in every patch.
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Threshold", "Ratio", "Depth", "Attack", "Release",
                    "Key Low", "Key High", "Key Listen", "Detector")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR", 5: "UNIPOLAR",
                   6: "UNIPOLAR", 7: "TOGGLE", 8: "TOGGLE"}
    _MACRO_RANGES = (
        (-80.0, 0.0),                 # Threshold, dBFS
        (1.0, 8.0, "log"),            # Ratio
        (0.0, -80.0),                 # Depth, dB of floor
        (0.01, 1000.0, "log"),        # Attack, ms
        (2.0, 4000.0, "log"),         # Release, ms
        (25.0, 4000.0, "log"),        # Key Low, Hz
        (250.0, 35000.0, "log"),      # Key High, Hz - clamped below Nyquist
        (0.0, 1.0),                   # Key Listen
        (0.0, 1.0),                   # Detector: 0 peak, 1 RMS
    )

    #: Patch 0 is the constructor's own defaults on the 0-127 grid.
    PATCHES = {
        # Threshold dB, Ratio, Depth dB, Attack ms, Release ms,
        # Key Low Hz, Key High Hz, Key Listen, Detector.
        0: ("Gentle Lift",      (70, 25, 32, 69, 77, 0, 127, 0, 127)),
        1: ("Noise Floor Trim", (40, 56, 48, 58, 84, 0, 127, 0, 127)),
        2: ("Snare Tighten",    (87, 109, 40, 43, 62, 45, 89, 0, 127)),
        3: ("Guitar Amp Hum",   (56, 85, 64, 69, 81, 62, 71, 0, 127)),
        4: ("Room Reduction",   (71, 67, 24, 78, 100, 0, 127, 0, 127)),
        5: ("Hard Downward",    (79, 127, 95, 51, 68, 0, 127, 0, 0)),
    }

    def _build(self, threshold_db=-36.0, ratio=1.5, depth_db=-20.0,
               attack_ms=5.0, release_ms=200.0, key_low_hz=25.0,
               key_high_hz=35000.0, key_listen=False, detector_rms=True,
               key=None, patch=None):
        """Build the one node this class owns.

        `key` is an optional second stream for the detector to read instead
        of the audio - the DS201's external Key input. It is borrowed, not
        owned: `reset()` and `deinit()` never touch it, exactly as they
        never touch `source`. A key that runs dry starves the node the way
        an absent source does (silence), which is the node's documented
        behaviour and not this class's.
        """
        node = audiodynamics.Dynamics(
            audiodynamics.DYN_EXPAND,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            # 12 dB/octave at each end of the key band, which is what the
            # node ask (dossier N-EXP-2) specified for it.
            sidechain_poles=2,
        )
        node.play(self._source)
        if key is not None:
            node.key(key)
        # `audiodynamics.Dynamics` has no `deinit`/`__enter__`/`__exit__` at
        # all (`audioif/docs/upstream-diff.md:711-714`), so the deinit walk
        # finds nothing to call on it; `reset` is `reset_buffer`, which
        # drops the detector envelopes and keeps the side-chain filter
        # memory on purpose (`:704`).
        self._own(node, reset=True, deinit=True)
        self._node = node
        self._output = node
        self._init_macros((threshold_db, ratio, depth_db, attack_ms,
                           release_ms, key_low_hz, key_high_hz,
                           1.0 if key_listen else 0.0,
                           1.0 if detector_rms else 0.0), patch)

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index == 0:
            self._node.set(threshold_db=value)
        elif index == 1:
            self._node.set(ratio=value)
        elif index == 2:
            self._node.set(depth_db=value)
        elif index == 3:
            self._node.set(attack_ms=value)
        elif index == 4:
            self._node.set(release_ms=value)
        elif index == 5:
            self._node.set(sidechain_hz=self._hz(value))
        elif index == 6:
            # Rate-honest: the DS201's key band runs to 35 kHz, which is
            # above Nyquist at every rate this library runs at, so the top
            # of the span clamps rather than refusing.
            self._node.set(sidechain_lp_hz=self._hz(value))
        elif index == 7:
            self._node.set(key_listen=1.0 if position >= 0.5 else 0.0)
        else:
            self._node.set(detector="rms" if position >= 0.5 else "peak")

    def gain_reduction_db(self):
        """What the gain computer applied on the last frame rendered, in dB.

        The node's own readout, forwarded. Not part of the component
        contract - a meter, and the measurement kit's GAINTRACE source.
        """
        self._check_live()
        return self._node.gain_reduction_db()
