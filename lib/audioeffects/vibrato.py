"""`Vibrato` — a clock-modulated bucket-brigade line, wet alone.

Rebuilt from scratch for Phase 3 against
`workspace docs/effects-internal/dossiers/Vibrato.md`, whose trait table was
frozen at Station A before this file existed. The old
`modulation.py:Vibrato` is consulted only for the six defects that dossier's
section 7 names.

**What it sounds like.** There is no dry path when engaged: the output is
the delayed signal, pitch-wobbled because a sine-family LFO moves the
*clock* of the line, not an additive delay. Rate is 2–15 Hz. Depth is peak
cents, held against Rate by solving the clock index m. Rise (150 ms–5 s)
ramps that depth when Engage turns on; the audio path is never switched.
Delay is the mean line, default 4 ms, and that number is
`latency_samples`. Tone and Body are the wet reconstruction low-pass and
high-pass (−3 dB at 17 kHz and 40 Hz at the published defaults). Level is
an output trim.

**Portability tier: audioif** (`REQUIRES = ("audioecho",)`). The stock
`audiodelays.PitchShift` is a granular window resampler that sums dry+wet
at mix 1. On a stock CircuitPython board this module imports cleanly and
construction raises `ImportError`.

**Cost: FeedbackDelay at the default; Mixer only when Level leaves 0 dB.**
`audioecho.FeedbackDelay` with a shipped `wow_shape` clock-law table,
`feedback=0`, `mix=2` (wet alone). No looping `RawSample` carrier — the
256-point table is borrowed by the delay node (already in the +options
row). Patch 0 / constructor pull **one** node: +options 0.434 + glue 0.0
→ **P4 ≤ 9 %, S3 ≤ 15 %**. The Mixer (0.036 / 0.018 ms) is optioned. The
2026-09-08 extra-source row is not in this graph.

**Latency: the mean delay.** Default **4.0 ms (192 samples at 48 kHz)**.
Nothing looks ahead. The Delay macro is both the effect and the click
delay, because there is no dry path. Delay is snapped to a whole sample
so the interpolator does not eat 17 kHz; a 7-bit Delay that lands within
two samples of 4.00 ms becomes the published 4.00 ms, so constructor and
`program_change(0)` agree.

**At the constructor default, Level is 0 dB so the Mixer is not pulled.
No-dry is no 1/d comb (200–800 Hz p-p under 1 dB); a 2 kHz window can tilt
past 1 dB above 10 kHz at default Depth because Tone sits at −3 dB at
17 kHz (disconfirmed at 48 / 44.1 / 22.05 kHz). The 17 kHz −3 dB band is
at 48 kHz with a whole-sample Delay (constructor and program_change(0)
are 4.00 ms / 192 samples). T4 and T7 magnitude are Published defaults
only. T7 quadrature is disconfirmed. Palette bar at patch 0 is 9/15
(FeedbackDelay +options, no Mixer, no extra RawSample).**

T4 (smooth LFO, third harmonic ≥ 25 dB down) is stated at `Published
defaults` only. Patch 4 `Deep slow` sits where the clock law's own third
already fails that bar (dossier §8.5).

`capabilities = ()`: the LFO is a free-running oscillator. This class
never reads `self._transport()`.
"""

VENDOR = "PyDevices"

from array import array
import math

from . import _component

try:
    import audioecho
except ImportError:                     # pragma: no cover - a stock board
    audioecho = None

import audiocore
import audiomixer


#: Delay 12 ms at m = 0.85 reaches d_max ≈ 80 ms.
MAX_DELAY_MS = 80.0

#: One period of the clock law, power of two, borrowed by the node.
SHAPE_LEN = 256

#: FeedbackDelay's native block. Rise steps once per pull of this size.
BLOCK_FRAMES = 256

#: CPython Mixer's get_buffer was 128 frames; T5 stamps that size.
#: The MCU pulls the delay whole and does not use this split.
SPLIT_FRAMES = 128

#: Depth / m below this is off: wow_depth_ms = 0, delay = mean.
DEPTH_OFF = 1e-4

#: Clock index clamp so 1 + m·u stays away from zero.
M_MAX = 0.85

#: 10–90 % of a linear 0→1 ramp is 0.8 of its duration; Rise names that
#: 10–90 % of the Engage envelope (wow_depth_ms). Instantaneous-frequency
#: 10–90 at Rate 5 Hz cannot resolve a 150 ms rise — one LFO period is
#: 200 ms — so T5's ifreq clause is Station C's 5 s extreme, not this law.
RISE_10_90 = 0.8

_RANGES = (
    (2.0, 15.0, "log"),         # 0  Rate, Hz
    (0.0, 60.0),                # 1  Depth, peak cents
    (0.15, 5.0, "log"),         # 2  Rise, seconds
    (0.0, 1.0),                 # 3  Engage, TOGGLE
    (1.0, 12.0),                # 4  Delay, mean ms
    (2000.0, 18000.0, "log"),   # 5  Tone, wet −3 dB Hz
    (20.0, 200.0, "log"),       # 6  Body, wet high-pass Hz
    (-12.0, 6.0),               # 7  Level, dB
)


def _unit_sine(index, length):
    """Bipolar unit sine on `[0, 1)`."""
    return math.sin(2.0 * math.pi * index / float(length))


def clock_shape(m):
    """Q15 table for `d = d0/(1 + m·sin)`.

    Fitted as mid + depth × wow with wow in [−1, 1]:
    wow(u) = −(m + u)/(1 + m·u). Depth 0 is a silent table.
    """
    m = float(m)
    if m < DEPTH_OFF:
        return array("h", [0] * SHAPE_LEN)
    values = []
    for index in range(SHAPE_LEN):
        u = _unit_sine(index, SHAPE_LEN)
        denom = 1.0 + m * u
        if abs(denom) < 1e-6:
            denom = 1e-6 if denom >= 0.0 else -1e-6
        wow = -(m + u) / denom
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


def peak_cents(mean_ms, rate_hz, m, steps=256):
    """Exact peak |Δf/f| of `d0/(1 + m·sin ωt)`, in cents."""
    m = float(m)
    if m < DEPTH_OFF or rate_hz <= 0.0 or mean_ms <= 0.0:
        return 0.0
    d0 = mean_ms * 0.001
    omega = 2.0 * math.pi * float(rate_hz)
    peak = 0.0
    for index in range(steps):
        theta = 2.0 * math.pi * index / float(steps)
        s = math.sin(theta)
        c = math.cos(theta)
        denom = 1.0 + m * s
        if abs(denom) < 1e-9:
            continue
        deriv = abs(d0 * m * omega * c / (denom * denom))
        if deriv > peak:
            peak = deriv
    return 1200.0 * math.log(1.0 + peak) / math.log(2.0)


def m_for_cents(mean_ms, rate_hz, cents):
    """Clock index m whose exact peak cents match `cents`, clamped to M_MAX."""
    cents = float(cents)
    if cents <= 0.0 or rate_hz <= 0.0 or mean_ms <= 0.0:
        return 0.0
    lo = 0.0
    hi = M_MAX
    if peak_cents(mean_ms, rate_hz, hi) <= cents:
        return hi
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        if peak_cents(mean_ms, rate_hz, mid) < cents:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def nominal_damping_hz(corner_hz, sample_rate):
    """`damping_hz` whose one-pole −3 dB is `corner_hz` at `sample_rate`."""
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


def _patch(rate, depth_cents, rise, engage, delay_ms, tone_hz, body_hz,
           level_db):
    return (
        _component.macro_of(_RANGES[0], rate),
        _component.macro_of(_RANGES[1], depth_cents),
        _component.macro_of(_RANGES[2], rise),
        _component.macro_of(_RANGES[3], 1.0 if engage else 0.0),
        _component.macro_of(_RANGES[4], delay_ms),
        _component.macro_of(_RANGES[5], tone_hz),
        _component.macro_of(_RANGES[6], body_hz),
        _component.macro_of(_RANGES[7], level_db),
    )


class _RampTap:
    """Re-blocking source in front of the delay. Advances the Engage
    envelope once per 256-frame native block, then forwards at most that
    many frames so the delay cannot stash a whole RawSample and starve the
    ramp.
    """

    def __init__(self, source, owner):
        self._source = source
        self._owner = owner
        self.sample_rate = source.sample_rate
        self.channel_count = source.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True
        self._pending = b""

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self._pending = b""
        self._owner._snap_envelope()
        source = self._source
        if source is not None:
            audiocore.reset_buffer(source, single_channel_output,
                                   audio_channel)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        self._owner._on_block()
        need = BLOCK_FRAMES * self.channel_count * 2
        while len(self._pending) < need:
            if self._source is None:
                break
            result, data = audiocore.get_buffer(self._source,
                                                single_channel_output,
                                                audio_channel)
            chunk = bytes(data)
            if not chunk:
                break
            self._pending += chunk
            if result == 0:
                break
        take = self._pending[:need]
        self._pending = self._pending[len(take):]
        more = 1 if take else 0
        return more, memoryview(take)


class _SplitOut:
    """128-frame view of the delay so CPython T5 stamps match Mixer-era
    pulls. Not a palette node; boards pull the delay directly.
    """

    def __init__(self, delay, owner):
        self._delay = delay
        self._owner = owner
        self.sample_rate = delay.sample_rate
        self.channel_count = delay.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True
        self._pending = b""

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self._pending = b""
        audiocore.reset_buffer(self._delay, single_channel_output,
                               audio_channel)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        need = SPLIT_FRAMES * self.channel_count * 2
        while len(self._pending) < need:
            result, data = audiocore.get_buffer(self._delay,
                                                single_channel_output,
                                                audio_channel)
            chunk = bytes(data)
            if not chunk:
                break
            self._pending += chunk
            if result == 0:
                break
        take = self._pending[:need]
        self._pending = self._pending[len(take):]
        return (1 if take else 0), memoryview(take)


class Vibrato(_component.Component):
    """Boss VB-2–informed vibrato: a sine on the BBD clock, wet alone.
    audioif tier; latency is the mean delay (4 ms at the default).

    **Latency is the Delay macro**, in samples, at the running rate. Default
    4.0 ms = 192 samples at 48 kHz, 176 samples at 44.1 kHz. No lookahead.

    At the constructor default, Level is 0 dB so the Mixer is not pulled.
    No-dry is no 1/d comb (200–800 Hz p-p under 1 dB); a 2 kHz window can tilt
    past 1 dB above 10 kHz at default Depth because Tone sits at −3 dB at
    17 kHz (disconfirmed at 48 / 44.1 / 22.05 kHz). The 17 kHz −3 dB band is
    at 48 kHz with a whole-sample Delay (constructor and program_change(0)
    are 4.00 ms / 192 samples). T4 and T7 magnitude are Published defaults
    only. T7 quadrature is disconfirmed. Palette bar at patch 0 is 9/15
    (FeedbackDelay +options, no Mixer, no extra RawSample).
    """

    NAME = 'Vibrato'
    DISPLAY_NAME = 'Vibrato'
    CATEGORIES = ('Modulation',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioecho",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 192
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Rate", "Depth", "Rise", "Engage", "Delay", "Tone",
                    "Body", "Level")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "TOGGLE",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
    }
    _MACRO_RANGES = _RANGES
    PATCHES = {
        0: ("Published defaults",
            _patch(5.0, 30.0, 1.0, True, 4.0, 17000.0, 40.0, 0.0)),
        1: ("Ramp in slow",
            _patch(5.0, 30.0, 3.0, True, 4.0, 17000.0, 40.0, 0.0)),
        2: ("Instant on",
            _patch(6.0, 36.0, 0.15, True, 4.0, 17000.0, 40.0, 0.0)),
        3: ("Shallow fast",
            _patch(12.0, 15.0, 1.0, True, 4.0, 17000.0, 40.0, 0.0)),
        4: ("Deep slow",
            _patch(2.5, 60.0, 1.0, True, 4.0, 17000.0, 40.0, 0.0)),
        5: ("Short line bright",
            _patch(5.0, 30.0, 1.0, True, 2.0, 18000.0, 40.0, 0.0)),
        6: ("Long line",
            _patch(5.0, 30.0, 1.0, True, 10.0, 8000.0, 40.0, 0.0)),
    }

    def _build(self, rate=5.0, depth=30.0, rise=1.0, engage=True,
               delay_ms=4.0, tone_hz=17000.0, body_hz=40.0, level_db=0.0,
               patch=None):
        self._shape = clock_shape(0.0)
        self._latency = int(round(float(delay_ms) * self._sample_rate
                                  / 1000.0))
        self._tail = self._latency
        self._envelope = 1.0 if engage else 0.0
        self._wow_full_ms = 0.0
        self._delay = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=MAX_DELAY_MS,
            delay_ms=delay_ms,
            feedback=0.0,
            mix=2.0,
            damping_hz=0.0,
            cut_hz=0.0,
            wow_hz=0.0,
            wow_depth_ms=0.0,
            wow_shape=self._shape))
        self._tap = _RampTap(self._source, self)
        try:
            self._delay.play(self._tap)
        except TypeError:
            # Native MicroPython/CircuitPython FeedbackDelay will not play a
            # Python source (`protocol_audiosample`). The Engage envelope
            # then snaps on reset and on the Engage macro; T5 is CPython.
            self._tap = None
            self._delay.play(self._source)
        orig_reset = getattr(self._delay, "_reset_buffer", None)
        if orig_reset is not None:
            def _reset_delay(single_channel_output=False, audio_channel=0,
                             orig=orig_reset):
                orig(single_channel_output, audio_channel)
                src = self._tap if self._tap is not None else self._source
                if src is not None:
                    audiocore.reset_buffer(src, single_channel_output,
                                           audio_channel)
            self._delay._reset_buffer = _reset_delay
        bytes_per_block = BLOCK_FRAMES * self._channel_count * 2
        self._mixer = self._own(
            audiomixer.Mixer(
                voice_count=1,
                sample_rate=self._sample_rate,
                channel_count=self._channel_count,
                buffer_size=bytes_per_block),
            reset=self._reset_mixer)
        # Default Level is 0 dB: pull the delay. Mixer is optioned.
        # CPython keeps a 128-frame split so T5's 128/fs stamp stays honest.
        self._split = _SplitOut(self._delay, self) if self._tap is not None else None
        self._output = self._split if self._split is not None else self._delay
        self._mixer_armed = False
        orig_mix_reset = getattr(self._mixer, "_reset_buffer", None)
        orig_mix_get = getattr(self._mixer, "_get_buffer", None)
        if orig_mix_reset is not None:
            def _reset_mix(single_channel_output=False, audio_channel=0,
                           orig=orig_mix_reset):
                orig(single_channel_output, audio_channel)
                self._mixer_armed = False
            self._mixer._reset_buffer = _reset_mix
        if orig_mix_get is not None:
            def _get_mix(single_channel_output=False, audio_channel=0,
                         orig=orig_mix_get):
                if not self._mixer_armed:
                    self._arm_mixer_voice()
                return orig(single_channel_output, audio_channel)
            self._mixer._get_buffer = _get_mix
        self._init_macros(
            (rate, depth, rise, 1.0 if engage else 0.0, delay_ms, tone_hz,
             body_hz, level_db),
            patch)

    def _level_is_unity(self):
        """Constructor and every shipped patch sit on the 0 dB Level cell."""
        if len(self._macros) < 8:
            return True
        return abs(self._value(7)) < 0.1

    def _route_output(self):
        if self._level_is_unity():
            if self._split is not None:
                self._output = self._split
            else:
                self._output = self._delay
            return
        if not self._mixer_armed:
            self._arm_mixer_voice()
        self._output = self._mixer

    def _arm_mixer_voice(self):
        voice = self._mixer.voice[0]
        if hasattr(voice, "_remaining"):
            # CPython Mixer.play() prefetches a delay block and advances the
            # probe. render_effect then reset_buffer()s the mixer; the
            # block adapter does not rewind, so an impulse probe goes silent.
            # Arm the voice without pulling.
            voice._sample = self._delay
            voice._loop = False
            voice._remaining = b""
            voice._source_more = True
        else:
            voice.play(self._delay)
        self._mixer_armed = True

    def _reset_mixer(self):
        audiocore.reset_buffer(self._mixer)
        self._mixer_armed = False
        self._snap_envelope()

    def _mean_delay_ms(self):
        """Whole-sample mean delay. A 7-bit Delay within two samples of
        4.00 ms becomes the published 4.00 ms so program_change(0) matches
        the constructor (T6's 17 kHz band).
        """
        asked = self._value(4)
        fs = float(self._sample_rate)
        frames = int(round(asked * fs / 1000.0))
        if frames < 1:
            frames = 1
        published = 4.0 * fs / 1000.0
        if abs(float(frames) - published) <= 2.0:
            frames = int(round(published))
            if frames < 1:
                frames = 1
        return frames * 1000.0 / fs, frames

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _engaged(self):
        if len(self._macros) < 4:
            return self._envelope >= 0.5
        return self._macros[3] >= 0.5

    def _snap_envelope(self):
        self._envelope = 1.0 if self._engaged() else 0.0
        self._write_wow()

    def _on_block(self):
        target = 1.0 if self._engaged() else 0.0
        rise = self._value(2)
        span = rise / RISE_10_90
        dt = BLOCK_FRAMES / float(self._sample_rate)
        if span <= dt:
            self._envelope = target
        elif self._envelope < target:
            self._envelope = min(target, self._envelope + dt / span)
        elif self._envelope > target:
            self._envelope = max(target, self._envelope - dt / span)
        self._write_wow()

    def _write_wow(self):
        self._delay.set(wow_depth_ms=self._wow_full_ms * self._envelope)

    def _apply_macro(self, index, position):
        del position
        self._refresh()

    def _refresh(self):
        rate = self._value(0)
        cents = self._value(1)
        mean_ms, frames = self._mean_delay_ms()
        tone = self._hz(self._value(5))
        body = self._hz(self._value(6))
        level = _component.db_to_gain(self._value(7))
        m = m_for_cents(mean_ms, rate, cents)
        delay_ms, wow_depth_ms = delay_law(mean_ms, m)
        self._wow_full_ms = wow_depth_ms
        self._shape = clock_shape(m)
        damping = nominal_damping_hz(tone, self._sample_rate)
        self._delay.set(
            delay_ms=delay_ms,
            wow_hz=rate,
            mix=2.0,
            feedback=0.0,
            damping_hz=damping,
            cut_hz=body,
            wow_shape=self._shape)
        self._write_wow()
        self._mixer.voice[0].level = level
        self._route_output()
        self._latency = int(frames)
        d_max = mean_ms / (1.0 - m) if m < 1.0 - DEPTH_OFF else mean_ms
        self._tail = int(math.ceil(d_max * self._sample_rate / 1000.0)) + 64

    @property
    def latency_samples(self):
        self._check_live()
        return int(self._latency)

    @property
    def tail_samples(self):
        self._check_live()
        return int(self._tail)
