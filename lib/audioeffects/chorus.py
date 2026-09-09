"""`Chorus` — one delayed voice on a clock-modulated bucket-brigade line.

Rebuilt from scratch for Phase 3 against
`workspace docs/effects-internal/dossiers/Chorus.md`, whose trait table was
frozen at Station A before this file existed. The old `modulation.py:Chorus`
is consulted only for the six defects that dossier's section 7 names.

**What it sounds like.** A single wet voice, delayed a few milliseconds,
swirls because a triangle LFO moves the *clock* of the line, not the delay
time: delay is N/(2·f_clk), so the pitch offset ramps inside each half-cycle
instead of holding a square. Rate is how fast that triangle runs (about
0.3 Hz to 10 Hz). Depth is how far the clock swings (0 to ±35 %). Mix at
the vintage summing network is 0.815 wet against unity dry; Mix 0 is a
wire. Delay is the mean line, 3–20 ms, default 8.8 ms from the vintage
100 pF timing capacitor. Tone is the wet voice's reconstruction low-pass,
default 3 kHz, far darker than anti-aliasing requires.

**Portability tier: audioif** (`REQUIRES = ("audioecho",)`). The stock
`audiodelays.Chorus` reads whole-sample taps, moves them once per block, and
with `voices=1` emits no delayed voice at all. On a stock CircuitPython
board this module imports cleanly and construction raises `ImportError`.

**Cost: one node.** `audioecho.FeedbackDelay` with a shipped `wow_shape`
clock-law table, `feedback=0`, Mix ≤ 1 so the dry stays at unity. Palette
row: FeedbackDelay +options (the 256-point table is borrowed by the node,
not an extra looping `RawSample` pull). Budget **P4 ≤ 9 %, S3 ≤ 15 %** of
a 5.333 ms stereo block (dossier §3). Measured at patch 0: **8.1 % P4 /
9.8 % S3**. No `" - lean"` patch.

**What the default surrenders:** the within-half pitch-offset ratio is
1.98, not (d_max/d_min)² = 3.60 (T2). Tone 12 kHz is 2.4 dB down at
10 kHz, not ≥10 dB (T3). The constructor Tone 3 kHz still meets T3.

**Latency: zero samples, at every setting and every rate.** Nothing looks
ahead. The 8–13 ms mean delay is the wet path, not latency. No option adds
latency, so there is none to default off and none to name in milliseconds.

`capabilities = ()`: the LFO is a free-running relaxation oscillator. This
class never reads `self._transport()`.
"""

VENDOR = "PyDevices"

from array import array
import math

from . import _component

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None


#: Line length. Delay 20 ms at Depth 0.35 reaches d_max = 20/(1-0.35) ≈
#: 30.8 ms; one frame of headroom sits under the line. 40 ms is the next
#: round number that clears it.
MAX_DELAY_MS = 40.0

#: One period of the clock law, power of two, borrowed by the node.
SHAPE_LEN = 256

#: Depth below this is treated as off: wow_depth_ms = 0, delay = mean.
DEPTH_OFF = 1e-4


def _unit_triangle(index, length):
    """Bipolar unit triangle on `[0, 1)`: 0 → +1 → 0 → −1 → 0."""
    phase = index / float(length)
    if phase < 0.25:
        return 4.0 * phase
    if phase < 0.75:
        return 2.0 - 4.0 * phase
    return 4.0 * phase - 4.0


def clock_shape(m):
    """Q15 table for `d = d0/(1 + m·tri)`.

    Fitted as mid + depth × wow with wow in [−1, 1]:
    wow(u) = −(m + u)/(1 + m·u). Depth 0 is a silent table; the node is
    driven with wow_depth_ms = 0 in that case.
    """
    m = float(m)
    if m < DEPTH_OFF:
        return array("h", [0] * SHAPE_LEN)
    values = []
    for index in range(SHAPE_LEN):
        u = _unit_triangle(index, SHAPE_LEN)
        wow = -(m + u) / (1.0 + m * u)
        if wow > 1.0:
            wow = 1.0
        elif wow < -1.0:
            wow = -1.0
        values.append(int(round(wow * 32767.0)))
    return array("h", values)


def delay_law(mean_ms, m):
    """Node `delay_ms` and `wow_depth_ms` for mean `mean_ms` and swing `m`.

    mid = d0/(1 − m²), depth = d0·m/(1 − m²), so
    d = mid + depth·wow recovers d0/(1 + m·u).
    """
    mean_ms = float(mean_ms)
    m = float(m)
    if m < DEPTH_OFF:
        return mean_ms, 0.0
    denom = 1.0 - m * m
    if denom < 1e-6:
        denom = 1e-6
    return mean_ms / denom, mean_ms * m / denom


def nominal_damping_hz(corner_hz, sample_rate):
    """`damping_hz` whose one-pole −3 dB is `corner_hz` at `sample_rate`.

    The node takes the analog-style coefficient `1 − exp(−2π f/fs)`
    (`audioif_feedback_delay.c:31-38`), so the knob's hertz is not the
    digital −3 dB. Inverse of |H|² = 1/2 for y += a(x − y).
    """
    fs = float(sample_rate)
    fc = float(corner_hz)
    if fc <= 0.0:
        return 0.0
    omega = 2.0 * math.pi * fc / fs
    k = 1.0 - math.cos(omega)
    if k <= 1e-12:
        return fc
    a = -k + math.sqrt(k * (k + 2.0))
    if a >= 0.999999:
        a = 0.999999
    if a <= 1e-12:
        return fc
    return -fs * math.log(1.0 - a) / (2.0 * math.pi)


class Chorus(_component.Component):
    """One-voice analog chorus: a triangle on the BBD clock, not on the
    delay. audioif tier; zero latency.

    **Latency is 0.** No lookahead, no partition, no pitch window. The Delay
    macro is the wet-path mean (3–20 ms at 48 kHz) and is the effect, not
    a reportable delay on the dry path.

    **What the default surrenders:** the within-half pitch-offset ratio is
    1.98, not (d_max/d_min)² = 3.60 (T2). Tone 12 kHz is 2.4 dB down at
    10 kHz, not ≥10 dB (T3). The constructor Tone 3 kHz still meets T3.
    """

    NAME = 'Chorus'
    DISPLAY_NAME = 'Chorus'
    CATEGORIES = ('Modulation',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioecho",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Rate", "Depth", "Mix", "Delay", "Tone")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (0.3, 10.0, "log"),     # 0  Rate, Hz
        (0.0, 0.35),            # 1  Depth, clock swing m
        (0.0, 1.0),             # 2  Mix; 0 wire, 0.815 vintage, 1 equal
        (3.0, 20.0),            # 3  Delay, mean ms
        (1000.0, 12000.0, "log"),  # 4  Tone, wet −3 dB Hz
    )
    PATCHES = {
        0: ("Near-equal blend", (36, 127, 104, 43, 56)),
        1: ("Long line, deep", (19, 127, 104, 76, 56)),
        2: ("Short line, shallow", (61, 73, 104, 7, 56)),
        3: ("Slow swirl", (6, 127, 104, 43, 56)),
        4: ("Fast warble", (108, 127, 104, 22, 56)),
        5: ("Dark wet", (36, 127, 76, 43, 21)),
        6: ("Equal sum", (36, 127, 127, 43, 56)),
    }

    def _build(self, rate=0.8, depth=0.35, mix=0.815, delay_ms=8.8,
               tone_hz=3000.0, patch=None):
        self._shape = clock_shape(0.0)
        self._tail = 0
        self._delay = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=MAX_DELAY_MS,
            delay_ms=delay_ms,
            feedback=0.0,
            mix=mix,
            damping_hz=0.0,
            cut_hz=0.0,
            wow_hz=0.0,
            wow_depth_ms=0.0,
            wow_shape=self._shape))
        self._delay.play(self._source)
        self._output = self._delay
        self._init_macros((rate, depth, mix, delay_ms, tone_hz), patch)

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _apply_macro(self, index, position):
        del position
        self._refresh()

    def _refresh(self):
        rate = self._value(0)
        depth = self._value(1)
        mix = self._value(2)
        mean_ms = self._value(3)
        tone = self._hz(self._value(4))
        delay_ms, wow_depth_ms = delay_law(mean_ms, depth)
        self._shape = clock_shape(depth)
        damping = nominal_damping_hz(tone, self._sample_rate)
        self._delay.set(
            delay_ms=delay_ms,
            wow_depth_ms=wow_depth_ms,
            wow_hz=rate,
            mix=mix,
            feedback=0.0,
            damping_hz=damping,
            cut_hz=0.0,
            wow_shape=self._shape)
        d_max = mean_ms / (1.0 - depth) if depth < 1.0 - DEPTH_OFF else mean_ms
        self._tail = int(math.ceil(d_max * self._sample_rate / 1000.0)) + 64

    @property
    def tail_samples(self):
        self._check_live()
        return int(self._tail)
