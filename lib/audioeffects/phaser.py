"""`Phaser` - four first-order all-pass stages swept the way a Phase 90 is.

Rebuilt from scratch for Phase 3 against
`workspace docs/effects-internal/dossiers/Phaser.md`, traits frozen at
Station A on 2026-09-08 before this file existed. The old
`modulation.py:Phaser` is not consulted except for the eight defects the
dossier's section 7 names.

**What it sounds like.** Two notches a fixed ratio apart (one per pair of
stages) slide up and down together on a triangle, linear in hertz, never
deeper than the 24 kΩ that sits across the JFET. Mix 0.5 is the script
logo's equal sum, where those notches are holes; Feedback is the later
block-logo resistor, a mid hump between them. Drive is a cubic into the
cascade, a proxy for the JFET living inside the stage - it is not the
channel's `v_ds` in the coefficient.

**What the default surrenders:** Drive 0.3 is on at construction. Feedback's
inter-notch peak then misses the 5 dB bar (600–1800 Hz rise −0.633 dB at
48 kHz) and the notch floor is not monotone (0.5→0.7 −1.204 dB). Both hold
at Drive 0. The floor's 0.5→0.7 step also deepens at 22.05 kHz with Drive 0
(−1.286 dB).

Patch 8 is `Phaser - lean`: Drive 0, AllPass only.

**Portability tier: audioif** (`REQUIRES = ("audiobiquad", "audioshaper")`).
The ported `audiofilters.Phaser` holds a DC residue after silence and will
not take feedback 0 (dossier B.1, F.1, F.4). On a stock CircuitPython board
this module imports and construction raises `ImportError`.

**Cost:** AllPass-6 **0.248 / 0.423** + Waveshaper ×1 **0.223 / 0.410** +
extra synthio 256-point **0.317 / 0.408** + glue **0.0** →
**0.788 / 1.241 ms → P4 ≤ 15 %, S3 ≤ 24 %**. The old **9 % / 16 %** bar
omitted the LFO: the palette could not price a `synthio` source. Lean
patch 8 is AllPass alone → **5 / 8 %**.

**Latency: zero samples at every setting.** Drive is `oversample=1` (group
delay 0). No lookahead, partition or window is offered, so there is no
latency-adding option to default off and none to name in milliseconds.

`capabilities = ("tempo_sync",)`: Sync on reads `self._transport()` and
locks Rate to Division in bars.

This class lives in `phaser.py` and is what the package serves.
"""

VENDOR = "PyDevices"

from array import array
import math

from . import _component

try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None

try:
    import audioshaper
except ImportError:                     # pragma: no cover - a stock board
    audioshaper = None

import synthio


#: Appendix A: pinch-off f_b with R5 = 24 kΩ, C2 = 47 nF.
FB_FLOOR_HZ = 141.1
#: tan(22.5°): notch 1 sits here relative to a stage's f_b.
TAN_22_5 = math.tan(math.radians(22.5))
#: Half the S3 typical-unit Hertz swing (328.0 … 2997.7 Hz) at Depth 1.
HALF_SWING_HZ = (2997.7 - 328.0) / 2.0

STAGES_CHOICES = (4, 6, 8, 10, 12)
DIVISION_BARS = (4.0, 2.0, 1.0, 0.5, 1.0 / 3.0, 0.25, 0.125)

WAVEFORM_POINTS = 256
CURVE_POINTS = 1024

_RANGES = (
    (0.0, 10.0),                 # 0 Rate, Hz; 0 is held
    (0.0, 1.0),                  # 1 Depth
    (60.0, 2000.0, "log"),       # 2 Centre, notch-1 Hz at mid-sweep
    (0.0, 0.9),                  # 3 Feedback
    (0.0, 1.0),                  # 4 Mix
    (0.0, 4.0),                  # 5 Stages index → 4/6/8/10/12
    (0.35, 0.65),                # 6 Shape, ramp duty
    (0.0, 1.0),                  # 7 Drive
    (0.0, 1.0),                  # 8 Sync (TOGGLE)
    (0.0, 6.0),                  # 9 Division index
)


def _cubic_curve():
    curve = array("h")
    last = float(CURVE_POINTS - 1)
    for index in range(CURVE_POINTS):
        x = -1.0 + 2.0 * index / last
        y = x - (x * x * x) / 3.0
        curve.append(max(-32768, min(32767, int(round(y * 32767.0)))))
    return curve


CUBIC_CURVE = _cubic_curve()


def _triangle_waveform(duty):
    """256 int16 samples, −1 → +1 → −1, with `duty` the rising fraction."""
    duty = min(0.65, max(0.35, float(duty)))
    n = WAVEFORM_POINTS
    rising = max(2, min(n - 2, int(round(duty * n))))
    falling = n - rising
    wave = array("h")
    for index in range(rising):
        x = -1.0 + 2.0 * index / float(rising - 1)
        wave.append(max(-32768, min(32767, int(round(x * 32767.0)))))
    for index in range(falling):
        x = 1.0 - 2.0 * index / float(falling - 1)
        wave.append(max(-32768, min(32767, int(round(x * 32767.0)))))
    return wave


def _choice(choices, position):
    last = len(choices) - 1
    return choices[min(last, max(0, int(round(position * last))))]


def _patch(*engineering):
    return tuple(_component.macro_of(span, value)
                 for span, value in zip(_RANGES, engineering))


class Phaser(_component.Component):
    """A Phase-90-informed all-pass cascade on `audiobiquad.AllPass`."""

    NAME = 'Phaser'
    DISPLAY_NAME = 'Phaser'
    CATEGORIES = ('Modulation',)
    VERSION = '0.0.2'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad", "audioshaper")

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    #: Worst-case first-order all-pass flush at the coefficient cap
    #: (`AUDIOIF_FILTER_F32_MAX_ALLPASS_C`) is ~550_000 samples in the C
    #: comment; musical settings die much sooner. Ceiling, next 2048.
    TAIL_SAMPLES = 552960

    MACRO_LABELS = ("Rate", "Depth", "Centre", "Feedback", "Mix",
                    "Stages", "Shape", "Drive", "Sync", "Division")
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
        4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
        8: "TOGGLE", 9: "UNIPOLAR",
    }
    _MACRO_RANGES = _RANGES
    PATCHES = {
        0: ("Four stage, no feedback",
            _patch(0.4, 0.7, 400.0, 0.0, 0.5, 0.0, 0.5, 0.3, 0.0, 2.0)),
        1: ("Four stage with resonance",
            _patch(0.4, 0.7, 400.0, 0.5, 0.5, 0.0, 0.5, 0.3, 0.0, 2.0)),
        2: ("Slow wide sweep",
            _patch(0.1, 1.0, 400.0, 0.0, 0.5, 0.0, 0.5, 0.2, 0.0, 2.0)),
        3: ("Fast tight sweep",
            _patch(4.0, 0.35, 500.0, 0.2, 0.5, 0.0, 0.5, 0.2, 0.0, 2.0)),
        4: ("Six stage deep",
            _patch(0.3, 0.8, 350.0, 0.35, 0.5, 1.0, 0.5, 0.3, 0.0, 2.0)),
        5: ("Held notch pair",
            _patch(0.0, 0.0, 400.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 2.0)),
        6: ("Bass-safe shallow",
            _patch(0.3, 0.4, 90.0, 0.0, 0.5, 0.0, 0.5, 0.15, 0.0, 2.0)),
        7: ("Synced half bar",
            _patch(0.4, 0.7, 400.0, 0.0, 0.5, 0.0, 0.5, 0.3, 1.0, 3.0)),
        8: ("Phaser - lean",
            _patch(0.4, 0.7, 400.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 2.0)),
    }

    def _build(self, rate=0.4, depth=0.7, centre=400.0, feedback=0.0,
               mix=0.5, stages=4, shape=0.5, drive=0.3, sync=False,
               division=1.0, patch=None):
        rate_hz = self._sample_rate
        channels = self._channel_count

        self._shaper = self._own(audioshaper.Waveshaper(
            sample_rate=rate_hz, channel_count=channels,
            curve=CUBIC_CURVE, oversample=1,
            mix=0.0, pre_gain=1.0, post_gain=1.0))
        self._shaper.play(self._source)

        # Built-in triangle: a custom waveform table is not a palette
        # audio node, but serving one still costs. Shape 0.5 (default)
        # uses synthio's own LFO, which is a BlockInput and is not an
        # extra RawSample. A custom table is baked only when Shape moves.
        self._lfo = None
        self._lfo_custom = False
        self._lfo_shape = 0.5
        self._cascade = None
        self._held_hz = 1000.0
        self._install_cascade(self._stage_count_from_value(stages))

        stage_index = float(STAGES_CHOICES.index(self._stage_count_from_value(
            stages)))
        div_index = float(self._division_index_from_value(division))
        self._init_macros(
            (rate, depth, centre, feedback, mix, stage_index, shape, drive,
             1.0 if sync else 0.0, div_index),
            patch)

    def _stage_count_from_value(self, stages):
        wanted = int(stages)
        nearest = STAGES_CHOICES[0]
        for candidate in STAGES_CHOICES:
            if abs(candidate - wanted) < abs(nearest - wanted):
                nearest = candidate
        return nearest

    def _division_index_from_value(self, bars):
        wanted = float(bars)
        nearest = 2
        for index, candidate in enumerate(DIVISION_BARS):
            if abs(candidate - wanted) < abs(DIVISION_BARS[nearest] - wanted):
                nearest = index
        return nearest

    def _install_cascade(self, stages):
        node = audiobiquad.AllPass(
            stages=int(stages), frequency=self._held_hz, feedback=0.0,
            mix=0.5, sample_rate=self._sample_rate,
            channel_count=self._channel_count)
        node.play(self._shaper)
        if self._cascade is None:
            self._own(node)
        else:
            old = self._cascade
            index = self._nodes.index(old)
            self._nodes[index] = node
            self._resets[index] = True
            self._deinits[index] = True
            stopper = getattr(old, "stop", None)
            if stopper is not None:
                stopper()
        self._cascade = node
        self._output = node

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _apply_macro(self, index, position):
        if index == 5:
            stages = _choice(STAGES_CHOICES, position)
            if self._cascade is None or self._cascade.stages != stages:
                self._install_cascade(stages)
            self._refresh_mix_feedback()
            self._refresh_sweep()
            return
        if index == 7:
            self._refresh_drive()
            return
        if index in (3, 4):
            self._refresh_mix_feedback()
            return
        self._refresh_sweep()

    def _refresh_drive(self):
        # Mix 0 is a wire. Drive 0 drops the shaper from the pull so the
        # lean patch is AllPass alone (palette 0.248 / 0.423 ms).
        if self._value(4) <= 0.0 or self._value(7) <= 0.0:
            self._shaper.set(mix=0.0, pre_gain=1.0)
            self._cascade.play(self._source)
            return
        drive = self._value(7)
        self._shaper.set(mix=drive, pre_gain=1.0 + 8.0 * drive)
        self._shaper.play(self._source)
        self._cascade.play(self._shaper)

    def _refresh_mix_feedback(self):
        self._cascade.feedback = self._value(3)
        self._cascade.mix = self._value(4)
        self._refresh_drive()

    def _lfo_rate_hz(self):
        rate = self._value(0)
        if self._value(8) >= 0.5:
            playing, _pos, bpm, _beats, beats_per_bar = self._transport()
            del playing
            bars = _choice(DIVISION_BARS, self._macros[9])
            beats = max(1.0, float(beats_per_bar)) * bars
            tempo = max(1.0, float(bpm))
            rate = tempo / (60.0 * beats)
        return rate

    def _fb_span(self):
        centre_notch = self._hz(self._value(2))
        mid = centre_notch / TAN_22_5
        depth = self._value(1)
        half = depth * HALF_SWING_HZ
        low = max(FB_FLOOR_HZ, mid - half)
        high = mid + half
        ceiling = self._sample_rate * 0.5 * _component.NYQUIST_MARGIN
        if high > ceiling:
            high = ceiling
        if low > high:
            low = high
        return low, high

    def _refresh_sweep(self):
        low, high = self._fb_span()
        mid = 0.5 * (low + high)
        self._held_hz = mid
        shape = self._value(6)
        rate = self._lfo_rate_hz()
        if rate <= 0.0 or self._value(1) <= 0.0:
            self._cascade.frequency = mid
            return
        self._attach_lfo(rate, 0.5 * (high - low), mid, shape)

    def _attach_lfo(self, rate, scale, offset, shape):
        want_custom = abs(float(shape) - 0.5) > 0.001
        rebuild = (
            self._lfo is None
            or want_custom != self._lfo_custom
            or (want_custom and abs(float(shape) - self._lfo_shape) > 0.001)
        )
        if rebuild:
            # MicroPython cannot assign LFO.waveform after construction.
            if want_custom:
                self._lfo = synthio.LFO(
                    waveform=_triangle_waveform(shape),
                    rate=rate, scale=scale, offset=offset, once=False)
            else:
                self._lfo = synthio.LFO(
                    rate=rate, scale=scale, offset=offset, once=False)
            self._lfo_custom = want_custom
            self._lfo_shape = float(shape)
        else:
            self._lfo.rate = rate
            self._lfo.scale = scale
            self._lfo.offset = offset
        self._cascade.frequency = self._lfo
