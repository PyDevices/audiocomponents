"""`LadderFilter` - the Moog transistor ladder, rebuilt on `audioladder`.

Four one-pole stages round one feedback loop, with a saturator *inside* the
loop. Turn `Resonance` up and the whole passband sinks while the cutoff
sharpens - that droop is the circuit's signature, not a bug, and it reaches
about 14 dB at the top. Push `Resonance` to the end stop and the filter sings
a sine of its own at the cutoff, out of silence, for as long as audio keeps
arriving; what stops that tone growing without bound is the saturator, which
is also where the growl comes from. `Drive` is the only warmth control the
circuit has: it is how hard that saturator is hit, so the character follows
the input level the way it does in the hardware.

**Portability tier: audioif** (`REQUIRES = ("audioladder",)`). The linear
half of this filter *is* reachable on stock CircuitPython biquads - two of
them track the analytic ladder to 0.05 dB at every resonance short of
oscillation - but a biquad cascade is linear, so from silence it stays
silent however far the resonance is pushed, and it makes no harmonics for
the growl to live in. That gap is not a matter of degree, which is why
`audioladder.Ladder` exists and why this class needs audioif's build.
Dossier: `docs/effects/LadderFilter.md` sections 4 and 5.

**Latency: 0 samples - 0.000 ms - at every setting, and there is no
latency-adding option on this class.** `Oversample` runs the loop at twice
the rate so the saturator's harmonics fold back less; its resampler is a
linear interpolation up and a two-tap average down, half a sample of group
delay for the pair, which the node reports as none
(`audioif/src/shared/audioif_ladder.c:302-311`). It defaults **on** because
half the cost is the wrong saving on the one node whose job is to distort;
patch 6, `Ladder - lean`, is patch 0 with it off for the S3.

**Cost:** budgeted at 14 % of one stereo block on a 240 MHz ESP32-S3 and 8 %
on a 400 MHz ESP32-P4 with `Oversample` on, 7 % on the S3 with the lean
patch (dossier section 3, Tier 3). Unmeasured on either board.

**One invariant this class does not hold, on purpose.** A self-oscillating
filter does not return to silence. At `Resonance` at or above k = 4 - macro
position 0.952 and up - the class holds its self-oscillation trait *instead
of* the silence-in-silence-out invariant. Everywhere below that the
invariant holds exactly, and `reset()` stops the tone at any setting.
Measured, at 48 kHz: a 0.29 ms tail at patch 0 and a **284.6 ms** tail at
patch 4 (k 3.9), both reaching **exact zero**; at patch 2 (k 4.2) it never
does.

**Measured** - `docs/effects/LadderFilter-evidence.md`: -12.055 dB at the
cutoff and -24.10 dB/octave; the passband 0.00 -> -13.90 dB across
k = 0...4; self-oscillation at 999.82 Hz holding to +0.01 dB over two
seconds, 0.068 % THD, every even harmonic below -131 dB re the first.
"""

VENDOR = "PyDevices"

from .. import _component

try:
    import audioladder
except ImportError:      # a stock CircuitPython board, or an older audioif
    audioladder = None


class LadderFilter(_component.Component):
    """A Moog transistor ladder: four poles, a resonance that droops the
    passband as it peaks, self-oscillation at the top of its travel, and a
    drive that is the only warmth control the circuit has."""

    NAME = 'LadderFilter'
    DISPLAY_NAME = 'Ladder Filter'
    CATEGORIES = ('Filter',)
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioladder",)

    #: No tempo-dependent behaviour anywhere in the class, so the transport
    #: is never read (dossier App. I, D10).
    CAPABILITIES = ()

    #: Zero at every setting; see the module docstring. The 2x path's half a
    #: sample of group delay is what this rounds.
    LATENCY_SAMPLES = 0

    #: Not finitely bounded. Below k = 4 no source reached in the dossier
    #: bounds the decay; at and above it the filter sustains by design.
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Cutoff", "Resonance", "Drive", "Passband Comp",
                    "Poles", "Oversample", "Mix")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR", 5: "TOGGLE",
                   6: "UNIPOLAR"}
    #: `Resonance` spans past the self-oscillation threshold deliberately:
    #: k = 4 has to be a position *inside* the travel, or "sustains at 4 and
    #: not before" cannot be measured from the panel at all. The node clamps
    #: at the same 4.2 (`audioif_ladder.c:130`).
    #: `Drive` is decibels here and a linear gain at the node, converted in
    #: `_apply_macro` rather than guessed at by the C.
    _MACRO_RANGES = (
        (20.0, 18000.0, "log"),   # 0 Cutoff
        (0.0, 4.2),               # 1 Resonance, the circuit's k
        (0.0, 24.0),              # 2 Drive, dB into the loop
        (0.0, 1.0),               # 3 Passband Comp
        (1.0, 4.0),               # 4 Poles, the output tap
        (0.0, 1.0),               # 5 Oversample, off / 2x
        (0.0, 1.0),               # 6 Mix, 0 is a wire
    )

    #: The 0-127 grid, computed with `_component.macro_of()` from the
    #: settings the dossier's section 6 names. Patch 0 is the constructor's
    #: defaults quantized onto that grid, which puts it at 11.73 kHz and
    #: k = 0.595 rather than the exact 12 kHz and 0.6 a fresh instance
    #: carries - `macro_position()` is unquantized on the construction path
    #: on purpose (`_component.py:190-198`).
    PATCHES = {
        0: ('Wide Open', (119, 18, 0, 0, 127, 127, 127)),
        1: ('Squelch At The Knee', (66, 109, 32, 0, 127, 127, 127)),
        2: ('Sustained Sine At Cutoff', (73, 127, 0, 0, 127, 127, 127)),
        3: ('Dark', (51, 45, 0, 0, 127, 127, 127)),
        4: ('Growl With Drive', (71, 118, 95, 0, 127, 127, 127)),
        5: ('Two Pole Soft', (90, 30, 0, 0, 42, 127, 127)),
        6: ('Ladder - lean', (119, 18, 0, 0, 127, 0, 127)),
    }

    def _build(self, cutoff_hz=12000.0, resonance=0.6, drive_db=0.0,
               passband_comp=0.0, poles=4, oversample=True, mix=1.0,
               patch=None):
        """One node. Every setting arrives through `_init_macros()`, so the
        constructor and a later `set_macro()` cannot mean different things.

        `resonance` is the circuit's feedback k, 0 to 4.2, not a 0..1 knob:
        the numbers the dossier's traits are stated in are k, and a class
        that renamed them would make its own gate unreadable.
        """
        node = audioladder.Ladder(sample_rate=self._sample_rate,
                                  channel_count=self._channel_count)
        node.play(self._source)
        # The node holds no external resource -- its output block is inline
        # in the object (`audioladder/Ladder.h`), so on the two native
        # builds, which expose no `deinit`, releasing it is dropping the
        # reference, which the base class's walk already does.
        self._own(node, reset=True, deinit=True)
        self._node = node
        self._output = node
        self._init_macros((cutoff_hz, resonance, float(drive_db),
                           passband_comp, float(poles),
                           1.0 if oversample else 0.0, mix), patch)

    def _apply_macro(self, index, position):
        span = self._MACRO_RANGES[index]
        value = _component.macro_value(span, position)
        if index == 0:
            # Clamped to 0.49 * sample_rate by `_hz()`, which is the node's
            # own clamp at `oversample = 1` and inside it at 2. Rate-honest:
            # at 22.05 kHz the top of this span becomes 10.8 kHz rather than
            # refusing (`_component.py:487-496`, `audioif_ladder.c:79`).
            self._node.set(cutoff_hz=self._hz(value))
        elif index == 1:
            self._node.set(resonance=value)
        elif index == 2:
            # Decibels on the panel, a linear gain at the node.
            self._node.set(drive=_component.db_to_gain(value))
        elif index == 3:
            self._node.set(passband_comp=value)
        elif index == 4:
            self._node.set(poles=int(round(value)))
        elif index == 5:
            self._node.set(oversample=2 if position >= 0.5 else 1)
        else:
            self._node.set(mix=value)
