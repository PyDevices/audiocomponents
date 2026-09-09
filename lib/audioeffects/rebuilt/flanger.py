"""`Flanger` - a BBD swept comb informed by the Electric Mistress.

Rebuilt from scratch at Phase 3 against
`workspace docs/effects-internal/dossiers/Flanger.md`, whose trait table
was frozen at Station A on 2026-09-08 before this file existed. The old
class in `modulation.py` is not consulted except for the eight defects
the dossier's section 7 names, and it stays the class the library serves
until the auditor adopts this one.

**What it sounds like.** One interpolated delay line mixes with the dry
path at equal weight, so the comb's notches are true nulls. A triangle
on the *clock* becomes a hyperbola in milliseconds - that is the bucket
brigade law, not a triangle LFO on the delay. Color is regeneration:
peaks rise and the floor fills. Filter Matrix stops the LFO and leaves
Manual, Color and Mix live. Through Zero is off unless you turn it on,
and then the dry path is late by the sweep's maximum at Range max
(**10 ms / 480 samples at 48 kHz**).

**What the default gives up.** At the constructor default (Color 0.55,
Filter Matrix off) the comb floor is about −22 dB, not the Color-0
−37 dB null, and the −60 dB tail is about 0.1 s, not 2 s. Color 0→0.9
peak rise holds +15 dB at 48 / 44.1 / 22.05 kHz on noise (held 3 ms,
Matrix on). Color max (0.99, 3 ms, Matrix on) is the 2 s ring on a
200–440 Hz burst; the default is not, and a click is not that bar.

**Portability tier: audioif** (`REQUIRES = ("audioecho", "audioroute")`).
`audioroute` is only built when Through Zero is on. On a stock
CircuitPython board this module imports and construction raises
`ImportError`.

**Cost.** Reference patch 0 is one `audioecho.FeedbackDelay` with a
256-point `wow_shape` (inside the palette +options row; this class does
not add a looping `RawSample` carrier). Palette +options 0.434 / 0.752 ms
plus glue 0.0 ms: **P4 ≤ 9 %, S3 ≤ 15 %** of a 5.333 ms stereo block.
Measured at patch 0: 0.681 ms/block on the P4 (rt 7.84) and 1.073 ms on
the S3 (rt 4.97). Lean patch: no.

**Latency is zero at defaults.** Through Zero is the only latency-adding
option; it defaults off.

`capabilities = ("tempo_sync",)`: this class always reads
`self._transport()`.
"""

VENDOR = "PyDevices"

from array import array
import math

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None
try:
    import audioroute
except ImportError:
    audioroute = None
try:
    import audiomixer
except ImportError:
    audiomixer = None

from .. import _component


#: Line length. F5's 10 ms top plus Through Zero's dry copy of the same,
#: plus the node's two-frame clamp.
MAX_DELAY_MS = 20.0
SHORT_MS = 2.5
LONG_MS = 10.0
BBD_N = 1024
SHAPE_LEN = 256
# One cut cannot do Color-0 exact-zero and Color-max ≥2 s together:
# 20 Hz yields Color-max audio t60 1.63 s; 1 Hz yields 2.02 s at 440 Hz
# but a 200 Hz burst was 1.96 s (indep3). Color-max cut is 0.4 Hz so
# the 2 s bar has margin across those bursts. Color 0 stays 20 Hz.
# Same one-pole, not a second node.
CUT_HZ = 20.0
CUT_HZ_COLOR_MAX = 0.4
# Color 0.9 as raw feedback misses ≥15 dB at 44.1 / 22.05 kHz on some
# noise seeds (14.32–14.83 dB). A 0.03 lift at the 0.9 stop (0.90→0.93)
# is the same regeneration law, hotter by a trim — not a second node.
COLOR_EXPAND_AT_09 = 0.03
# Color 0 still has the 20 Hz pole: last non-zero 2356 frames / 48 kHz
# (0.049 s) after a burst. Declared tail at Color 0 must cover that.
COLOR0_SETTLE_S = 0.08
DELAY_SLEW = 1.0
MIX_UNITY_SNAP = 0.04
DIVISIONS = (4.0, 2.0, 1.0, 0.5, 1.0 / 3.0, 0.25, 0.125)
TONE_MAX_HZ = 16000.0


def _hyperbola_table(duty, length=SHAPE_LEN, ratio=4.0):
    """One period of delay wow in Q15: a linear clock ramp of `duty` is a
    hyperbola in milliseconds, mapped onto [-1, 1]."""
    duty = min(0.75, max(0.25, float(duty)))
    samples = []
    centre = (1.0 + ratio) / 2.0
    depth = (ratio - 1.0) / 2.0
    for index in range(length):
        phase = index / float(length)
        if phase < duty:
            clock = phase / duty
        else:
            clock = 1.0 - (phase - duty) / (1.0 - duty)
        delay = 1.0 / (1.0 / ratio + clock * (1.0 - 1.0 / ratio))
        wow = (delay - centre) / depth
        samples.append(int(max(-32767, min(32767, round(wow * 32767.0)))))
    return array("h", samples)


def _loop_cut_hz(color):
    """20 Hz at Color 0 (Tier 1 exact zero); 0.4 Hz at Color 0.99 (F8)."""
    travel = min(1.0, max(0.0, float(color) / 0.99))
    return CUT_HZ + travel * (CUT_HZ_COLOR_MAX - CUT_HZ)


def _color_to_feedback(color, ceiling=0.99, law="linear"):
    """Panel Color → node feedback. 0 stays 0; 0.9 is lifted so F3's
    +15 dB four-stop rise holds at 48 / 44.1 / 22.05 kHz."""
    value = min(ceiling, max(0.0, float(color)))
    if law == "squared":
        value = value * value
    if value > 0.0:
        value = min(ceiling, value + COLOR_EXPAND_AT_09 * (value / 0.9))
    return value


def _linear_ms_table(duty, length=SHAPE_LEN):
    """F1's null: a triangle in milliseconds, not in clock."""
    duty = min(0.75, max(0.25, float(duty)))
    samples = []
    for index in range(length):
        phase = index / float(length)
        if phase < duty:
            wow = 2.0 * (phase / duty) - 1.0
        else:
            wow = 1.0 - 2.0 * (phase - duty) / (1.0 - duty)
        samples.append(int(max(-32767, min(32767, round(wow * 32767.0)))))
    return array("h", samples)


class Flanger(_component.Component):
    """Electric Mistress-informed flanger: one `FeedbackDelay`, audioif
    tier, zero latency until Through Zero (10 ms at Range max / 48 kHz) is
    turned on.

    What the default gives up. At the constructor default (Color 0.55,
    Filter Matrix off) the comb floor is about −22 dB, not the Color-0
    −37 dB null, and the −60 dB tail is about 0.1 s, not 2 s. Color 0→0.9
    peak rise holds +15 dB at 48 / 44.1 / 22.05 kHz on noise (held 3 ms,
    Matrix on). Color max (0.99, 3 ms, Matrix on) is the 2 s ring on a
    200–440 Hz burst; the default is not, and a click is not that bar.
    """

    NAME = 'Flanger'
    DISPLAY_NAME = 'Flanger'
    CATEGORIES = ('Modulation',)
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioecho", "audioroute")

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = (
        "Rate", "Range", "Color", "Manual", "Filter Matrix", "Mix",
        "Shape", "Tone", "Spread", "Sync", "Division", "Through Zero",
    )
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
        4: "TOGGLE", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
        8: "UNIPOLAR", 9: "TOGGLE", 10: "UNIPOLAR", 11: "TOGGLE",
    }
    _MACRO_RANGES = (
        (0.02, 8.0, "log"),     # 0  Rate, Hz
        (0.0, 1.0),             # 1  Range
        (0.0, 0.99),            # 2  Color
        (0.4, 12.0, "log"),     # 3  Manual, ms
        (0.0, 1.0),             # 4  Filter Matrix
        (0.0, 2.0),             # 5  Mix; 1.0 equal weight, 2.0 wet only
        (0.25, 0.75),           # 6  Shape, ramp duty
        (2000.0, 16000.0, "log"),  # 7  Tone, Hz
        (0.0, 1.0),             # 8  Spread
        (0.0, 1.0),             # 9  Sync
        (0.0, 6.0),             # 10 Division index
        (0.0, 1.0),             # 11 Through Zero
    )

    #: Values are `macro_of` of the engineering settings in the comment.
    PATCHES = {
        0: ("Slow jet", (54, 108, 71, 75, 0, 64, 64, 127, 0, 0, 42, 0)),
        1: ("Fast metallic", (98, 89, 90, 60, 0, 64, 64, 85, 0, 0, 42, 0)),
        2: ("Held comb", (54, 64, 71, 75, 127, 64, 64, 127, 0, 0, 42, 0)),
        3: ("Wide sweep with resonance",
            (68, 127, 115, 75, 0, 64, 64, 67, 0, 0, 42, 0)),
        4: ("Shallow and short", (83, 19, 19, 34, 0, 64, 64, 127, 0, 0, 42, 0)),
        5: ("Deep and slow, no resonance",
            (29, 127, 0, 94, 0, 64, 64, 127, 0, 0, 42, 0)),
        6: ("Synced one bar", (54, 108, 71, 75, 0, 64, 64, 127, 0, 127, 42, 0)),
        7: ("Through zero, dry delayed",
            (54, 108, 38, 75, 0, 64, 64, 127, 0, 0, 42, 127)),
    }

    #: F1's law. Planted faults flip this without a macro that can.
    DELAY_LAW = "reciprocal"
    COLOR_LAW = "linear"
    DAMPING_HONOURED = True
    MATRIX_HONOURED = True
    RANGE_SCALE = 1.0
    COLOR_CEILING = 0.99
    DELAY_SLEW = DELAY_SLEW

    def _build(self, rate_hz=0.25, range_=0.85, color=0.55, manual_ms=3.0,
               filter_matrix=0.0, mix=1.0, shape=0.5, tone_hz=TONE_MAX_HZ,
               spread=0.0, sync=0.0, division=2.0, through_zero=0.0,
               patch=None):
        """`through_zero` defaults off (0 ms). On, Range max is 10 ms
        (480 samples at 48 kHz)."""
        self._latency = 0
        self._shape_table = _hyperbola_table(shape)
        self._wet = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=MAX_DELAY_MS,
            delay_ms=manual_ms, feedback=0.0, mix=0.0,
            cut_hz=CUT_HZ, delay_slew=type(self).DELAY_SLEW,
            wow_shape=self._shape_table),
            reset=lambda: self._wet.clear())
        self._wet.play(self._source)

        # Dry delay + mixer exist only for Through Zero. Attaching the mixer
        # to `_wet` at construction makes a pull of `_wet` come back at half
        # scale (the mixer and the live output sharing one node). So they
        # stay dark until the toggle is actually on.
        self._dry = None
        self._mixer = None
        self._output = self._wet
        self._tz = False

        self._init_macros(
            (rate_hz, range_, color, manual_ms, filter_matrix, mix, shape,
             tone_hz, spread, sync, division, through_zero), patch)

    @property
    def latency_samples(self):
        self._check_live()
        return self._latency

    @property
    def tail_samples(self):
        self._check_live()
        mix = self._value(5)
        if mix <= MIX_UNITY_SNAP:
            return 0
        delay_ms = self._held_ms()
        color = _color_to_feedback(
            self._value(2), type(self).COLOR_CEILING, type(self).COLOR_LAW)
        frames = int(delay_ms * self._sample_rate / 1000.0) + 2
        if color <= 0.0:
            return max(frames, int(COLOR0_SETTLE_S * self._sample_rate))
        tau = delay_ms / 1000.0
        t60 = tau * 60.0 / (-20.0 * math.log10(max(color, 1e-6)))
        return int(t60 * self._sample_rate) + frames

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _transport_tuple(self):
        raw = self._transport
        if callable(raw):
            raw = raw()
        return raw

    def _lfo_hz(self):
        """Always reads the transport so `tempo_sync` is honest."""
        playing, beat, bpm, num, den = self._transport_tuple()[:5]
        del playing, beat, den
        if self._value(9) >= 0.5:
            index = int(round(self._value(10)))
            index = min(len(DIVISIONS) - 1, max(0, index))
            bar_s = (60.0 / max(1.0, float(bpm))) * max(1.0, float(num))
            period = DIVISIONS[index] * bar_s
            if period <= 0.0:
                return self._value(0)
            return 1.0 / period
        return self._value(0)

    def _span_ms(self):
        depth = min(1.0, max(0.0, self._value(1))) * type(self).RANGE_SCALE
        t_long = SHORT_MS + (LONG_MS - SHORT_MS) * max(depth, 1e-6)
        t_short = t_long / (1.0 + 3.0 * depth) if depth > 0.0 else t_long
        return t_short, t_long

    def _held_ms(self):
        if (self._value(4) >= 0.5) and type(self).MATRIX_HONOURED:
            return self._value(3)
        t_short, t_long = self._span_ms()
        return 0.5 * (t_short + t_long)

    def _bake_shape(self):
        duty = self._value(6)
        if type(self).DELAY_LAW == "linear":
            self._shape_table = _linear_ms_table(duty)
        else:
            self._shape_table = _hyperbola_table(duty)

    def _ensure_tz_graph(self):
        if self._dry is not None:
            return
        split = self._own(audioroute.Splitter(self._source, taps=2),
                          reset=False, deinit=False)
        self._dry = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=MAX_DELAY_MS,
            delay_ms=LONG_MS, feedback=0.0, mix=2.0, delay_slew=0.0),
            reset=lambda: self._dry.clear())
        self._dry.play(split.tap(0))
        self._wet.play(split.tap(1))
        self._mixer = self._own(
            audiomixer.Mixer(voice_count=2, **self._pcm(1024)), reset=False)
        self._mixer.voice[0].play(self._dry)
        self._mixer.voice[1].play(self._wet)

    def _route_tz(self, on):
        on = bool(on)
        t_short, t_long = self._span_ms()
        del t_short
        if on:
            self._ensure_tz_graph()
            self._latency = int(round(t_long * self._sample_rate / 1000.0))
            self._dry.set(delay_ms=t_long, mix=2.0, feedback=0.0)
            self._output = self._mixer
        else:
            self._latency = 0
            self._output = self._wet
        self._tz = on

    def _refresh(self):
        self._bake_shape()
        t_short, t_long = self._span_ms()
        matrix = (self._value(4) >= 0.5) and type(self).MATRIX_HONOURED
        mix = self._value(5)
        if abs(mix - 1.0) <= MIX_UNITY_SNAP:
            mix = 1.0
        color = _color_to_feedback(
            self._value(2), type(self).COLOR_CEILING, type(self).COLOR_LAW)
        tone = self._hz(self._value(7))
        held = self._value(3) if matrix else 0.5 * (t_short + t_long)
        depth = 0.0 if matrix else 0.5 * (t_long - t_short)
        clock_hz = BBD_N / (2.0 * max(held, 0.1) * 0.001)
        damping = max(1.0, clock_hz / 3.0)
        if tone < TONE_MAX_HZ * 0.98:
            damping = min(damping, tone)
        wow_hz = 0.0 if matrix else self._lfo_hz()
        tz = self._value(11) >= 0.5
        wet_mix = 2.0 if tz else mix
        self._wet.set(
            delay_ms=held,
            wow_depth_ms=depth,
            wow_hz=wow_hz,
            wow_shape=self._shape_table,
            feedback=color,
            mix=wet_mix,
            damping_hz=damping,
            cut_hz=_loop_cut_hz(color),
            cross_feed=self._value(8),
            delay_slew=type(self).DELAY_SLEW)
        self._route_tz(tz)
        if tz and self._mixer is not None:
            dry_gain = 0.0 if mix >= 2.0 - MIX_UNITY_SNAP else (
                1.0 if mix <= 1.0 else 2.0 - mix)
            wet_gain = 0.0 if mix <= MIX_UNITY_SNAP else (
                mix if mix <= 1.0 else 1.0)
            self._mixer.voice[0].level = dry_gain
            self._mixer.voice[1].level = wet_gain

    def _apply_macro(self, index, position):
        del index, position
        self._refresh()
