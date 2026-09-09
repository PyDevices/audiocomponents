"""`Tremolo` — Fender bias-vary and optical characters on one Multiply.

Rebuilt from scratch for Phase 3 against
`workspace docs/effects-internal/dossiers/Tremolo.md`, whose trait table was
frozen at Station A before this file existed. The old
`modulation.py:Tremolo` is consulted only for the defects that dossier's
section 7 names (block-rate MixerVoice.level, CPython LFO freeze, Depth-1
mute, empty surface).

**What it sounds like.** Two characters, one LFO. *Bias* is a near-sine
gain wobble that flattens toward cutoff, never mutes, and gets shallower if
the idle is hot. *Optical* is a neon pulse into a photocell that falls
faster than it recovers, as a resistive divider, never a gate. Rate is
0.5–15 Hz (amp patches sit in 3–10 Hz). Depth 0 is a wire. Speed Link
makes depth fall as Rate falls, the way one pot moves one RC section.

**Portability tier: audioif** (`REQUIRES = ("audiomath",)`). On a stock
CircuitPython board this module imports cleanly and construction raises
`ImportError`.

**Cost: one Multiply plus a 1024-point synthio Note (not a period-length
RawSample).** The old Rate-5 Hz table was 9600 frames and pulled whole
every block (palette 2.468 / 9.591 ms). A 256-point waveform left L1's
−80 dB bar red on a 1 kHz square at the held-fixed cell (−78.967) and
on Rate 0.73 / 1.46 Hz staircase images (−61.9 / −60.8). 1024 points
clears those; `synthio` length does not scale like a looping RawSample
(palette 256-point extra **0.317 / 0.408**, 1500-point **0.263 / 0.472**).
Palette: Multiply **0.028 / 0.047** + extra synthio **0.317 / 0.408** +
glue **0.0** → **0.345 / 0.455 ms → P4 ≤ 7 %, S3 ≤ 9 %**. No `" - lean"`
patch.

**What the default surrenders:** Default is bias, Depth 0.5, Rate 5 Hz —
not the optical standout and not L1's Depth 1. Wet peak at the default
is −1.341 dB vs a 16000-LSB tone, not the ~6 dB `synthio` `>>16` ceiling;
Depth 0 is still a wire. At 22.05 kHz the default's L1 bar is measured
at the constructor, not assumed. Optical L1/L2 are disconfirmed; O1–O4
unmeasured at the constructor.

L1 holds on sine at every rate, and misses by 0.16 dB on SQUARE material at 44.1 kHz only (−79.844 against −80; 48 kHz holds at −82.01).

**Latency: zero samples, at every setting and every rate.** Nothing looks
ahead. Lag is table *shape*, not a delay line, so there is no latency to
default off and none to name in milliseconds. `tail_samples` is 0.

`capabilities = ("tempo_sync",)`: when Sync is on the class reads
`transport()` and snaps Rate to the nearest tempo division; with no BPM it
holds the Rate knob.
"""

VENDOR = "PyDevices"

from array import array
import math

from . import _component

try:
    import audiomath
except ImportError:                     # pragma: no cover - a stock board
    audiomath = None

import audiocore
import synthio

#: One LFO period as a short waveform. Multiply used to walk `fs/rate`
#: frames (9600 at 5 Hz / 48 kHz) on every pull. 256 points left L1's
#: bands on the table-step images (256·Rate ≈ 187 / 375 Hz). 1024 points
#: put those images at ≥ 512 Hz across 0.5–15 Hz.
TABLE_FRAMES = 1024


BIAS = 0
OPTICAL = 1

CHAR, RATE, DEPTH, SHAPE, LAG, BIAS_M, LINK, PHASE, SYNC = range(9)

DEPTH_WIRE = 1e-4
#: Photocell dark / source / intensity-max, ohms. Lit is the Depth ceiling
#: (dossier §8.3), not a Fender figure: Depth 1 trough lands in −15…−40 dB.
R_SRC = 220000.0
R_DARK = 2000000.0
R_LIT = 28000.0
R_INT_MAX = 50000.0
TAU_ON_S = 0.0008
Q15 = 32767


def _clamp(value, lo, hi):
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def kinked_sine(phase, shape):
    """Near-sine with a small kink at the bottom (S5). `phase` radians."""
    s = math.sin(phase)
    k = 0.10 * float(shape)
    if s < 0.0:
        s = s - k * s * s
    return _clamp(s, -1.0, 1.0)


def triangle(phase):
    """Unit triangle on a 2π period. Planted-fault LFO, not the class."""
    u = (phase / (2.0 * math.pi)) % 1.0
    if u < 0.25:
        return 4.0 * u
    if u < 0.75:
        return 2.0 - 4.0 * u
    return 4.0 * u - 4.0


def link_scale(rate_hz):
    """Speed-Link amplitude vs Rate. ~3 dB from 3 Hz to 8 Hz."""
    rate_hz = _clamp(float(rate_hz), 0.5, 15.0)
    n = math.log(rate_hz / 0.5) / math.log(15.0 / 0.5)
    return 0.28 + 0.72 * n


def depth_travel(depth):
    """Saturating Depth law (B2): first 20 % of travel adds more than last."""
    depth = _clamp(float(depth), 0.0, 1.0)
    return 1.0 - math.exp(-2.2 * depth)


def bias_gain(s, depth, idle, curve_p=1.8):
    """Concave stage gain vs a bipolar LFO sample `s` in [−1, 1]."""
    idle = _clamp(float(idle), 0.0, 1.0)
    swing = depth_travel(depth) * 0.55 * (1.0 - 0.75 * idle)
    center = 0.42 + 0.40 * idle
    u = center + swing * float(s)
    u = _clamp(u, 0.12, 1.20)
    p = float(curve_p)
    if p < 0.0:
        g = 1.0 - (1.0 - u / 1.20) ** (-p)
        return _clamp(g, 0.12, 1.0)
    return _clamp((u ** p) / (1.20 ** p), 0.12, 1.0)


def optical_gains(frames, _rate_hz, sample_rate, depth, shape, lag_ms,
                  neon=True, equal_tau=False, ignore_lag=False,
                  gate=False, force_taus=None):
    """One period of optical divider gain, already dark-normalised to 1."""
    fs = float(sample_rate)
    if force_taus is not None:
        tau_on, tau_off = force_taus
    else:
        tau_off = 0.005 if ignore_lag else max(0.005, float(lag_ms) / 1000.0)
        tau_on = tau_off if equal_tau else TAU_ON_S
    th = -0.30 + 1.10 * float(shape)
    depth = _clamp(float(depth), 0.0, 1.0)
    r_int = 0.0 if gate else R_INT_MAX * (1.0 - depth) * (1.0 - depth)
    g_dark = R_DARK / (R_SRC + R_DARK)
    a_on = 1.0 - math.exp(-1.0 / (tau_on * fs))
    a_off = 1.0 - math.exp(-1.0 / (tau_off * 10.0 * fs))
    g = 0.0
    out = array("f", bytes(4 * frames))
    total = frames * 3
    write = 0
    for index in range(total):
        phase = 2.0 * math.pi * (index % frames) / float(frames)
        s = math.sin(phase)
        if neon:
            lit = 1.0 if s > th else 0.0
        else:
            lit = 0.5 + 0.5 * s
        # Fast toward lit (low R, audio gain falls); slow toward dark.
        a = a_on if lit > g else a_off
        g = g + a * (lit - g)
        if index >= frames * 2:
            r_cell = R_DARK * (1.0 - g) + R_LIT * g
            if gate:
                r_cell = R_DARK * (1.0 - g)
            shunt = r_cell + r_int
            gain = (shunt / (R_SRC + shunt)) / g_dark
            out[write] = _clamp(gain, 0.0, 1.0)
            write += 1
    return out


def tempo_divisions(bpm):
    """Hz values for whole, half, quarter, eighth, sixteenth, 32nd."""
    beat = float(bpm) / 60.0
    if beat <= 0.0:
        return ()
    return (beat * 0.25, beat * 0.5, beat, beat * 2.0, beat * 4.0, beat * 8.0)


def snap_rate(rate_hz, bpm):
    choices = tempo_divisions(bpm)
    if not choices:
        return rate_hz
    best = choices[0]
    err = abs(rate_hz - best)
    for hz in choices[1:]:
        delta = abs(rate_hz - hz)
        if delta < err:
            best, err = hz, delta
    return best


class Tremolo(_component.Component):
    """Bias-vary and optical tremolo on `audiomath.Multiply`. audioif tier.

    **Latency is 0.** No lookahead, no partition, no pitch window. Lag is a
    shape parameter (5–100 ms of photocell recovery) baked into the table,
    not a reportable delay.

    **What the default surrenders:** Default is bias, Depth 0.5, Rate 5 Hz —
    not the optical standout and not L1's Depth 1. Wet peak at the default
    is −1.341 dB vs a 16000-LSB tone, not the ~6 dB `synthio` `>>16` ceiling;
    Depth 0 is still a wire. At 22.05 kHz the default's L1 bar is measured
    at the constructor, not assumed. Optical L1/L2 are disconfirmed; O1–O4
    unmeasured at the constructor.

    L1 holds on sine at every rate, and misses by 0.16 dB on SQUARE material at 44.1 kHz only (−79.844 against −80; 48 kHz holds at −82.01).
    """

    NAME = 'Tremolo'
    DISPLAY_NAME = 'Tremolo'
    CATEGORIES = ('Modulation',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiomath",)

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    MACRO_LABELS = (
        "Character", "Rate", "Depth", "Shape", "Lag", "Bias",
        "Speed Link", "Stereo Phase", "Sync",
    )
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "TOGGLE",
        7: "BIPOLAR",
        8: "TOGGLE",
    }
    _MACRO_RANGES = (
        (0.0, 1.0),             # 0 Character
        (0.5, 15.0, "log"),      # 1 Rate, Hz
        (0.0, 1.0),              # 2 Depth
        (0.0, 1.0),              # 3 Shape
        (5.0, 100.0),            # 4 Lag, ms
        (0.0, 1.0),              # 5 Bias, cold…hot
        (0.0, 1.0),              # 6 Speed Link
        (-180.0, 180.0),         # 7 Stereo Phase, deg
        (0.0, 1.0),              # 8 Sync
    )
    PATCHES = {
        0: ("Bias Wobble", (0, 86, 64, 64, 40, 64, 127, 64, 0)),
        1: ("Bias Deep Slow", (0, 73, 114, 64, 40, 0, 127, 64, 0)),
        2: ("Bias Warm Fast", (0, 104, 51, 64, 40, 127, 127, 64, 0)),
        3: ("Opto Chop", (127, 93, 114, 89, 20, 64, 127, 64, 0)),
        4: ("Opto Soft", (127, 78, 64, 25, 114, 64, 127, 64, 0)),
        5: ("Opposed Pair", (127, 86, 102, 64, 40, 64, 127, 127, 0)),
        6: ("Helicopter", (127, 119, 127, 76, 0, 64, 0, 64, 0)),
        7: ("Slow Swell", (0, 40, 89, 64, 40, 64, 0, 64, 0)),
        8: ("Eighth Note Chop", (127, 78, 114, 89, 40, 64, 127, 64, 127)),
    }

    #: Fault hooks. Subclasses set these; no macro reaches them.
    BLOCK_HOLD = False
    FORCE_LINK_SCALE = None
    LFO_KIND = "kink"
    CURVE_P = 1.25
    ALLOW_MUTE = False
    IGNORE_BIAS = False
    BIAS_USE_OPTICAL_TRACKER = False
    EQUAL_TAU = False
    NEON = True
    GATE_AT_DEPTH1 = False
    IGNORE_LAG = False
    PLAIN_SINE = False
    SHALLOW_LINEAR = False
    #: L4 plant: multiply the table Rate so ENV fundamental ≠ Rate knob.
    RATE_PERIOD_SCALE = 1.0
    #: B5 plant taus (on, off) seconds. Ignores the Lag macro so Lag min
    #: and Helicopter cannot restore a <1.5 slope ratio.
    TRACKER_TAUS = (0.0004, 0.080)

    def _build(self, character=0.0, rate=5.0, depth=0.5, shape=0.5,
               lag_ms=35.0, bias=0.5, speed_link=1.0, stereo_phase=0.0,
               sync=0.0, patch=None):
        self._mod_sample = None
        self._synth = synthio.Synthesizer(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count)
        self._mul = self._own(
            audiomath.Multiply(
                None, None, mix=1.0,
                sample_rate=self._sample_rate,
                channel_count=self._channel_count),
            deinit=self._deinit_graph)
        self._mul.play(self._source)
        self._output = self._mul
        self._init_macros(
            (character, rate, depth, shape, lag_ms, bias,
             speed_link, stereo_phase, sync),
            patch)

    def _deinit_graph(self):
        if self._mod_sample is not None:
            deinit = getattr(self._mod_sample, "deinit", None)
            if deinit is not None:
                deinit()
            self._mod_sample = None
        synth = getattr(self, "_synth", None)
        if synth is not None:
            release = getattr(synth, "release_all", None)
            if release is not None:
                release()
            deinit = getattr(synth, "deinit", None)
            if deinit is not None:
                deinit()
            self._synth = None
        deinit = getattr(self._mul, "deinit", None)
        if deinit is not None:
            deinit()

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _apply_macro(self, index, position):
        del position
        self._refresh()

    def _refresh(self):
        cls = type(self)
        character = 1 if self._value(CHAR) >= 0.5 else 0
        rate = self._value(RATE)
        depth = self._value(DEPTH)
        shape = self._value(SHAPE)
        lag_ms = self._value(LAG)
        idle = 1.0 if cls.IGNORE_BIAS else self._value(BIAS_M)
        linked = self._value(LINK) >= 0.5
        phase_deg = self._value(PHASE)
        sync = self._value(SYNC) >= 0.5

        if sync:
            transport = self.transport()
            state = transport() if callable(transport) else transport
            bpm = 0.0
            if isinstance(state, (tuple, list)) and len(state) >= 3:
                bpm = float(state[2])
            if bpm > 0.0:
                rate = snap_rate(rate, bpm)

        if depth <= DEPTH_WIRE:
            self._mul.set(mix=0.0)
            return
        self._mul.set(mix=1.0)

        scale = 1.0
        if linked:
            if cls.FORCE_LINK_SCALE is not None:
                scale = float(cls.FORCE_LINK_SCALE)
            else:
                scale = link_scale(rate)
        depth_used = depth * scale if linked else depth

        fs = int(self._sample_rate)
        period_scale = float(cls.RATE_PERIOD_SCALE)
        if period_scale < 0.25:
            period_scale = 0.25
        played = float(rate) * period_scale
        if played < 0.25:
            played = 0.25
        channels = int(self._channel_count)
        phase_r = 0.0 if channels == 1 else (
            float(phase_deg) * math.pi / 180.0)

        # BLOCK_HOLD stays an audio-rate table so the 256-frame hold lands
        # in L1's bands. The healthy path is a 1024-point waveform at
        # Note.frequency — a short pull, not fs/rate frames.
        if cls.BLOCK_HOLD:
            frames = int(round(fs / played))
            if frames < 16:
                frames = 16
            table = self._law_pcm(
                frames, channels, fs, rate, depth_used, shape, lag_ms,
                idle, character, phase_r)
            table = self._hold_blocks(table, channels)
            self._modulate_raw(table, fs, channels)
            return

        frames = TABLE_FRAMES
        table_fs = frames * played
        table = self._law_pcm(
            frames, channels, table_fs, rate, depth_used, shape, lag_ms,
            idle, character, phase_r)
        self._modulate_synth(table, played, channels)

    def _law_pcm(self, frames, channels, table_fs, rate, depth, shape,
                 lag_ms, idle, character, phase_r):
        cls = type(self)
        if cls.PLAIN_SINE:
            return self._plain_sine_table(frames, channels, depth, phase_r)
        if character == OPTICAL and not cls.BIAS_USE_OPTICAL_TRACKER:
            gains = optical_gains(
                frames, rate, table_fs, depth, shape, lag_ms,
                neon=cls.NEON, equal_tau=cls.EQUAL_TAU,
                ignore_lag=cls.IGNORE_LAG, gate=cls.GATE_AT_DEPTH1)
            return self._stereo_from_period(gains, channels, phase_r)
        if cls.BIAS_USE_OPTICAL_TRACKER:
            gains = optical_gains(
                frames, rate, table_fs, depth, shape, lag_ms,
                neon=True, equal_tau=False, ignore_lag=False, gate=False,
                force_taus=cls.TRACKER_TAUS)
            return self._stereo_from_period(gains, channels, phase_r)
        return self._bias_table(
            frames, channels, depth, shape, idle, phase_r)

    def _modulate_raw(self, table, fs, channels):
        release = getattr(self._synth, "release_all", None)
        if release is not None:
            release()
        sample = audiocore.RawSample(
            table, sample_rate=fs, channel_count=channels)
        if self._mod_sample is not None:
            deinit = getattr(self._mod_sample, "deinit", None)
            if deinit is not None:
                deinit()
        self._mod_sample = sample
        self._mul.modulate(sample)

    def _modulate_synth(self, table, played, channels):
        if self._mod_sample is not None:
            deinit = getattr(self._mod_sample, "deinit", None)
            if deinit is not None:
                deinit()
            self._mod_sample = None
        left = self._channel_of(table, channels, 0)
        release = getattr(self._synth, "release_all", None)
        if release is not None:
            release()
        if channels == 1:
            self._synth.press(synthio.Note(frequency=played, waveform=left))
        else:
            right = self._channel_of(table, channels, 1)
            self._synth.press((
                synthio.Note(frequency=played, waveform=left, panning=-1.0),
                synthio.Note(frequency=played, waveform=right, panning=1.0),
            ))
        self._mul.modulate(self._synth)

    @staticmethod
    def _channel_of(table, channels, channel):
        if channels == 1:
            return table
        out = array("h", bytes(2 * (len(table) // channels)))
        for index in range(len(out)):
            out[index] = table[index * channels + channel]
        return out

    def _bias_table(self, frames, channels, depth, shape, idle, phase_r):
        cls = type(self)
        buf = array("h", bytes(2 * frames * channels))
        mute = cls.ALLOW_MUTE
        for index in range(frames):
            phase = 2.0 * math.pi * index / float(frames)
            if cls.LFO_KIND == "triangle":
                s = triangle(phase)
            else:
                s = kinked_sine(phase, shape)
            if mute:
                g = _clamp(0.5 + 0.5 * s, 0.0, 1.0) * depth
            elif cls.SHALLOW_LINEAR:
                g = _clamp(0.78 + 0.18 * s, 0.0, 1.0)
            else:
                g = bias_gain(s, depth, idle, cls.CURVE_P)
            q = int(round(g * Q15))
            if q < 0:
                q = 0
            elif q > Q15:
                q = Q15
            dest = index * channels
            buf[dest] = q
            if channels != 1:
                if cls.LFO_KIND == "triangle":
                    s2 = triangle(phase + phase_r)
                else:
                    s2 = kinked_sine(phase + phase_r, shape)
                if mute:
                    g2 = _clamp(0.5 + 0.5 * s2, 0.0, 1.0) * depth
                elif cls.SHALLOW_LINEAR:
                    g2 = _clamp(0.78 + 0.18 * s2, 0.0, 1.0)
                else:
                    g2 = bias_gain(s2, depth, idle, cls.CURVE_P)
                q2 = int(round(g2 * Q15))
                if q2 < 0:
                    q2 = 0
                elif q2 > Q15:
                    q2 = Q15
                buf[dest + 1] = q2
        return buf

    def _stereo_from_period(self, gains, channels, phase_r):
        frames = len(gains)
        shift = int(round(frames * phase_r / (2.0 * math.pi))) % frames
        buf = array("h", bytes(2 * frames * channels))
        for index in range(frames):
            q = int(round(gains[index] * Q15))
            if q < 0:
                q = 0
            elif q > Q15:
                q = Q15
            dest = index * channels
            buf[dest] = q
            if channels != 1:
                q2 = int(round(gains[(index + shift) % frames] * Q15))
                if q2 < 0:
                    q2 = 0
                elif q2 > Q15:
                    q2 = Q15
                buf[dest + 1] = q2
        return buf

    def _plain_sine_table(self, frames, channels, depth, phase_r):
        depth = _clamp(float(depth), 0.0, 1.0)
        buf = array("h", bytes(2 * frames * channels))
        for index in range(frames):
            phase = 2.0 * math.pi * index / float(frames)
            g = _clamp(1.0 - depth * 0.35 * (0.5 + 0.5 * math.sin(phase)),
                       0.0, 1.0)
            dest = index * channels
            buf[dest] = int(round(g * Q15))
            if channels != 1:
                g2 = _clamp(
                    1.0 - depth * 0.35 * (
                        0.5 + 0.5 * math.sin(phase + phase_r)),
                    0.0, 1.0)
                buf[dest + 1] = int(round(g2 * Q15))
        return buf

    @staticmethod
    def _hold_blocks(table, channels, block=256):
        held = array("h", table)
        width = channels
        frames = len(held) // width
        for start in range(0, frames, block):
            src = start * width
            for frame in range(start, min(start + block, frames)):
                dst = frame * width
                for ch in range(width):
                    held[dst + ch] = held[src + ch]
        return held
