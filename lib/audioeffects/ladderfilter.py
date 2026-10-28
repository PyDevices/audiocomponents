"""`LadderFilter` - the Moog transistor ladder, rebuilt on `audioladder`.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests.
"""

# Design notes.
#
# Portability tier: audiodsp (`REQUIRES = ("audioladder",)`). The linear
# half of this filter is reachable on stock CircuitPython biquads - two of
# them track the analytic ladder to 0.05 dB at every resonance short of
# oscillation - but a biquad cascade is linear, so it can never sustain a
# tone of its own however far the resonance is pushed, and it makes no
# harmonics for the growl to live in. That gap is not a matter of degree,
# which is why `audioladder.Ladder` exists.
#
# Oversample's resampler is a linear interpolation up and a two-tap average
# down, half a sample of group delay for the pair, which the node reports as
# none (`audiodsp/src/shared/audiodsp_ladder.c:302-311`). What it buys is
# small: a 5 kHz sine at 24 dB of Drive measured its non-harmonic energy
# 0.4 dB lower with it on (2026-10-27). It defaults on because half the cost
# is the wrong saving on the one node whose job is to distort.
#
# Cost: budgeted at 14 % of one stereo block on a 240 MHz ESP32-S3 and 8 %
# on a 400 MHz ESP32-P4 with Oversample on, 7 % on the S3 with the lean
# patch (dossier section 3, Tier 3). Measured 2026-09-07: 16.3 % of a block
# on the ESP32-P4 and 26.9 % on the ESP32-S3, over budget on both.
#
# The node starts from a zero state, so exact digital silence into a fresh
# instance stays silent even at k = 4.2; the sustained tone needs something,
# however small, to have arrived first.
#
# Two dossier traits are disconfirmed, with cause, in the evidence pack. T5's
# "a 20 dB input rise moves the resonant peak >= 3 dB" holds on one of the
# six 20 dB windows the surface offers (-20 -> 0 dBFS, -3.857 dB, and the
# peak falls). T1's stopband slope (-23...-27 dB/octave over 4->8 kHz) is
# -29.73 dB/oct at 22.05 kHz, because the bilinear map steepens toward
# Nyquist. Measured at 48 kHz: -12.055 dB at the cutoff, the passband
# 0.00 -> -13.90 dB across k = 0...4, self-oscillation at 999.82 Hz holding
# to +0.01 dB over two seconds, 0.068 % THD, every even harmonic below
# -131 dB re the first.

VENDOR = "PyDevices"

import math

from . import _component

try:
    import audioladder
except ImportError:      # a stock CircuitPython board, or an older audiodsp
    audioladder = None


#: The Resonance at which the loop sustains, and from which `tail_samples`
#: is `None`.
SELF_OSCILLATION = 4.0

#: `ring_frames`' envelope: the free response of the linear ladder, seen at
#: the output tap, is at most `RING_CONSTANT` times the largest integrator
#: state times rho^(`RING_RATE` n) after n frames, rho being the slowest
#: pole's radius per frame (or 1/2, `RING_FLOOR`, whichever is larger).
#: The rate is under 1 because near Resonance 0 the four poles nearly
#: coincide and the response is a cubic times rho^n, which no constant
#: covers at the full rate. The largest constant this needs, worked out
#: over cutoffs from 20 Hz to the clamp at 22.05, 44.1 and 48 kHz, every
#: Resonance from 0 to 3.969, every tap and both Oversample settings, is
#: 131 (Resonance 0, 20 Hz, four poles), and from 3.975 to 3.997 under 3;
#: 256 is the margin. Rendered, the longest ring at Resonance 0 comes to
#: 0.96 of the count, and near 4 to about half.
RING_CONSTANT = 256.0
RING_RATE = 0.875
RING_FLOOR = 0.5

#: The slowest decay per (oversampled) step for which `ring_frames` gives a
#: count, 2^-20, about eight single-precision rounding steps: the kernel
#: runs in single precision, and nearer Resonance 4 its rounding is as
#: large as the decay it would have to show. At a 20 Hz cutoff, 48 kHz,
#: Oversample on, that is Resonance 3.9884 and up.
RING_SLOWEST = 2.0 ** -20

#: 1/sqrt(2): the analog ladder's poles sit at -1 + k^(1/4) e^(+-j pi/4)
#: and -1 + k^(1/4) e^(+-j 3 pi/4), in units of the cutoff.
_HALF_ROOT_TWO = 0.7071067811865476


def ring_frames(sample_rate, cutoff_hz, resonance, drive, poles=4,
                oversample=2, output_gain=1.0, mix=1.0):
    """Frames from the input's end until the ladder's output is exactly
    zero, as an upper bound, or `None` from Resonance 4 up and in the
    narrow band just below it where the slowest decay per step is under
    `RING_SLOWEST`. At Mix 0 the output is the input, so the count is 0 at
    any Resonance.

    Each stage is a bilinear one-pole, so the zero-delay loop's poles are
    the analog ladder's, mapped by z = (1 + t p) / (1 - t p), t being the
    prewarped tan(pi fc / rate). For a pole p, 1 - |z|^2 is
    -4 t Re(p) / |1 - t p|^2, and half of that is a per-step decay rate no
    faster than the true one. The slow pair's -Re(p) = 1 - k^(1/4)/sqrt(2)
    is worked out as (4 - k) / 4 over (1 + q/sqrt(2))(1 + q^2/2), q being
    k^(1/4), so it keeps its digits near 4 in single precision too.

    No integrator holds more than `drive` plus 2/3 of the Resonance (the
    saturator's ceiling) times max(1, t) times max(1, 2g)^3, and the output
    rounds to exact zero under 0.5 / (32768 gain mix). The envelope
    (`RING_CONSTANT`) then gives the count. This is the linear ladder's
    decay; the saturator only lowers the loop's gain, and that it does not
    slow the ring is measured, not derived."""
    scale = output_gain * mix
    if not scale > 0.0:
        return 0
    resonance = float(resonance)
    if not resonance < SELF_OSCILLATION:
        return None
    if resonance < 0.0:
        resonance = 0.0
    rate = float(sample_rate) * oversample
    cutoff = float(cutoff_hz)
    if cutoff > rate * 0.49:
        cutoff = rate * 0.49
    if cutoff < 1.0:
        cutoff = 1.0
    t = math.tan(math.pi * cutoff / rate)
    g = t / (1.0 + t)
    q = math.sqrt(math.sqrt(resonance))
    slow = ((SELF_OSCILLATION - resonance) / 4.0
            / ((1.0 + q * _HALF_ROOT_TWO) * (1.0 + 0.5 * q * q)))
    imag = q * _HALF_ROOT_TWO
    step = None
    for real in (-slow, -1.0 - imag):
        shrink = -4.0 * t * real / ((1.0 - t * real) ** 2 + (t * imag) ** 2)
        if step is None or shrink < step:
            step = shrink
    if not 0.5 * step >= RING_SLOWEST:
        return None
    per_frame = 0.5 * step * oversample
    if per_frame > math.log(1.0 / RING_FLOOR):
        per_frame = math.log(1.0 / RING_FLOOR)
    state = ((drive + resonance * (2.0 / 3.0)) * max(1.0, t)
             * max(1.0, 2.0 * g) ** 3)
    floor = 0.5 / (32768.0 * scale)
    return int(math.ceil(math.log(RING_CONSTANT * state / floor)
                         / (RING_RATE * per_frame))) + 1


class LadderFilter(_component.Component):
    """A Moog transistor ladder: four filter stages round one feedback loop,
    with a saturator inside the loop.

    **Controls.** Cutoff is the filter's corner, held just under half the
    sample rate. Resonance is the loop's feedback. As it rises the cutoff
    sharpens and the whole passband sinks, about 14 dB by a Resonance of 4:
    that droop is the circuit's sound, not a fault. From 4 up, the filter
    sings a sine of its own at the cutoff, and once it has heard anything
    it keeps singing after your signal stops. Drive is how hard the
    saturator is hit, so the growl follows your input level the way it does
    in the hardware. Passband Comp puts the sunk passband back: at 1 the
    passband holds its level at any Resonance. Poles picks the output from
    one to four poles. Oversample runs the loop at twice the rate; it is on
    by default, and the Ladder - lean patch is Wide Open with it off, for
    slower boards. Mix at 0 is your dry signal. The Effect controls page
    lists what the knobs span.

    **Response.** At 48 kHz the four-pole output is 12 dB down at the cutoff
    and about 50 dB down two octaves above it, and each pole fewer takes
    about 12 dB off that.

    **Timing.** Latency is zero at every setting, Oversample included. Below
    a Resonance of 4, silence in is silence out once the filter rings down:
    Wide Open's tail is under a millisecond and Growl With Drive's about
    285 ms. `tail_samples` is an upper bound on that ring for the settings
    as they stand; at the slowest settings it is about twice the ring
    measured. From 4 up the tone does not stop by itself, so the class
    reports no tail bound, and none either in the hair below 4 where the
    ring outlasts what single precision can count (from Resonance 3.988 at
    a 20 Hz cutoff, nearer 4 above it). `reset()` stops it at any setting.

    **Levels.** The resonance peak and the drive both add gain, so no input
    level is clean on every setting. Keep the input under -15 dBFS and the
    defaults and patches stay off the rails. Drive at its top can still push
    the output onto the rails. Turn Drive, Resonance or your input down.

    **On a board.** The class needs audiodsp's `audioladder`, and on a board
    without it construction raises `ImportError`.
    """

    NAME = 'LadderFilter'
    DISPLAY_NAME = 'Ladder Filter'
    CATEGORIES = ('Filter',)
    VERSION = '0.0.2'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioladder",)

    #: No tempo-dependent behaviour anywhere in the class, so the transport
    #: is never read (dossier App. I, D10).
    CAPABILITIES = ()

    #: Zero at every setting; see the design notes. The 2x path's half a
    #: sample of group delay is what this rounds.
    LATENCY_SAMPLES = 0

    #: The class attribute is the self-oscillating case; below k = 4
    #: `tail_samples` is `ring_frames` for the settings in force.
    TAIL_SAMPLES = None

    #: The defaults and every patch play the ceiling kit's materials
    #: clean at this level; at -12 dBFS, patch 4 rails on
    #: a 100 Hz square.
    INPUT_CEILING_DBFS = -15
    #: Settings that clip by design: the rail check skips them.
    CLIPS_AT_TOP = (2,)

    MACRO_LABELS = ("Cutoff", "Resonance", "Drive", "Passband Comp",
                    "Poles", "Oversample", "Mix")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR", 5: "TOGGLE",
                   6: "UNIPOLAR"}
    #: `Resonance` spans past the self-oscillation threshold deliberately:
    #: k = 4 has to be a position *inside* the travel, or "sustains at 4 and
    #: not before" cannot be measured from the panel at all. The node clamps
    #: at the same 4.2 (`audiodsp_ladder.c:130`).
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
    _MACRO_UNITS = {0: "Hz", 2: "dB"}

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
            # refusing (`_component.py:487-496`, `audiodsp_ladder.c:79`).
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

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound for the settings as they stand, or `None` from a
        Resonance of 4 up, where the filter sustains, and just below it
        where single precision cannot show the decay (`ring_frames`)."""
        self._check_live()
        return self._tail_bound()

    def _tail_bound(self):
        """`tail_samples` without the liveness check: a plain method, so a
        subclass can reach it on MicroPython, whose `property` has no
        `fget`."""
        def value(index):
            return _component.macro_value(self._MACRO_RANGES[index],
                                          self._macros[index])
        resonance = value(1)
        return ring_frames(
            self._sample_rate, self._hz(value(0)), resonance,
            _component.db_to_gain(value(2)), int(round(value(4))),
            2 if self._macros[5] >= 0.5 else 1,
            1.0 + value(3) * resonance, value(6))
