"""`Vibrato` - a clock-modulated bucket-brigade line, wet alone.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests.
"""

# Design notes, from the rebuild.
#
# `Vibrato` — a clock-modulated bucket-brigade line, wet alone.
#
# Rebuilt from scratch for Phase 3 against a dossier whose trait table was
# frozen at Station A before this file existed. The old
# `modulation.py:Vibrato` is consulted only for the six defects that dossier's
# section 7 names.
#
# What it sounds like. There is no dry path when engaged: the output is
# the delayed signal, pitch-wobbled because a sine-family LFO moves the
# *clock* of the line, not an additive delay. Rate is 2–15 Hz. Depth is peak
# cents, held against Rate by solving the clock index m. Rise (150 ms–5 s)
# ramps that depth in when Engage turns on, and out when it turns off, in a
# straight line whose 10–90 % is Rise, on every interpreter: the ramp is the
# delay node's own (`wow_depth_ramp_ms`), so nothing in Python runs while it
# travels. Any other knob that moves the depth glides there over 20 ms, which
# also finishes an Engage ramp still under way. The audio path is never
# switched.
# Delay is the mean line, default 4 ms, and that number is
# `latency_samples`. Tone and Body are the wet reconstruction low-pass and
# high-pass (−3 dB at 17 kHz and 40 Hz at the published defaults). Level is
# an output trim.
#
# Portability tier: audiodsp (`REQUIRES = ("audioecho",)`). The stock
# `audiodelays.PitchShift` is a granular window resampler that sums dry+wet
# at mix 1. On a stock CircuitPython board this module imports cleanly and
# construction raises `ImportError`.
#
# Cost: FeedbackDelay at the default; Mixer only when Level leaves 0 dB.
# `audioecho.FeedbackDelay` with a shipped `wow_shape` clock-law table,
# `feedback=0`, `mix=2` (wet alone). No looping `RawSample` carrier — the
# 256-point table is borrowed by the delay node (already in the +options
# row). Patch 0 / constructor pull one node: +options 0.434 + glue 0.0
# → P4 ≤ 9 %, S3 ≤ 15 %. The Mixer (0.036 / 0.018 ms) is optioned. The
# 2026-09-08 extra-source row is not in this graph.
#
# Latency: the mean delay. Default 4.0 ms (192 samples at 48 kHz).
# Nothing looks ahead. The Delay macro is both the effect and the click
# delay, because there is no dry path. Delay is snapped to a whole sample
# so the interpolator does not eat 17 kHz; a 7-bit Delay that lands within
# two samples of 4.00 ms becomes the published 4.00 ms, so constructor and
# `program_change(0)` agree.
#
# At the constructor default, Level is 0 dB so the Mixer is not pulled.
# No-dry is no 1/d comb (200–800 Hz p-p under 1 dB); a 2 kHz window can tilt
# past 1 dB above 10 kHz at default Depth because Tone sits at −3 dB at
# 17 kHz (disconfirmed at 48 / 44.1 / 22.05 kHz). The 17 kHz −3 dB band is
# at 48 kHz with a whole-sample Delay (constructor and program_change(0)
# are 4.00 ms / 192 samples). T4 and T7 magnitude are Published defaults
# only. T7 quadrature is disconfirmed. Palette bar at patch 0 is 9/15
# (FeedbackDelay +options, no Mixer, no extra RawSample).
#
# T4 (smooth LFO, third harmonic ≥ 25 dB down) is stated at `Published
# defaults` only. Patch 4 `Deep slow` sits where the clock law's own third
# already fails that bar (dossier §8.5).
#
# `capabilities = ()`: the LFO is a free-running oscillator. This class
# never reads `self._transport()`.

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

#: FeedbackDelay's native block, which the Mixer's buffer matches.
BLOCK_FRAMES = 256

#: Depth / m below this is off: wow_depth_ms = 0, delay = mean.
DEPTH_OFF = 1e-4

#: Clock index clamp so 1 + m·u stays away from zero.
M_MAX = 0.85

#: 10–90 % of a linear 0→1 ramp is 0.8 of its duration; Rise names that
#: 10–90 % of the Engage envelope (wow_depth_ms). Instantaneous-frequency
#: 10–90 at Rate 5 Hz cannot resolve a 150 ms rise — one LFO period is
#: 200 ms — so T5's ifreq clause is Station C's 5 s extreme, not this law.
RISE_10_90 = 0.8

#: How long a depth move other than Engage glides: the node's default.
DEPTH_GLIDE_MS = 20.0

_RANGES = (
    (2.0, 15.0, "log"),         # 0  Rate, Hz
    (0.0, 60.0),                # 1  Depth, peak cents
    (0.15, 5.0, "log"),         # 2  Rise, seconds
    (0.0, 1.0),                 # 3  Engage, TOGGLE
    (1.0, 12.0),                # 4  Delay, mean ms
    (2000.0, 18000.0, "log"),   # 5  Tone, wet −3 dB Hz
    (20.0, 200.0, "log"),       # 6  Body, wet high-pass Hz
    (-12.0, 0.0),               # 7  Level, dB
)


#: ln(65536): a one-pole state at full scale falls under half an int16 LSB
#: after this many time constants.
_RING_TIME_CONSTANTS = math.log(65536.0)


def one_pole_ring(hz, sample_rate):
    """Frames a `FeedbackDelay` loop filter at `hz` takes to fall from full
    scale to under half an LSB: the node's state falls by exp(-2 pi f / fs)
    a frame (`one_pole_coefficient`), plus one frame for the single
    precision it computes that in. 0 for a filter out of circuit."""
    if hz <= 0.0:
        return 0
    return int(math.ceil(_RING_TIME_CONSTANTS * sample_rate
                         / (2.0 * math.pi * hz))) + 1


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


class Vibrato(_component.Component):
    """A vibrato after the Boss VB-2: your signal comes out only through a
    short bucket-brigade line whose clock a sine sweeps, so the pitch
    wobbles and none of the dry is left to comb against it.

    **Controls.** Rate is the sweep's speed. Depth is the peak pitch swing,
    and stays that size wherever Rate and Delay sit. Engage turns the
    vibrato on and off without switching the audio: Rise is how long the
    depth takes to go from 10 % to 90 % of the way, in a straight line. Any
    other knob that moves the depth glides there over 20 ms rather than
    stepping. Delay is the line's average length. Tone is the wet voice's
    low-pass, and Body its high-pass; at the defaults the band is 3 dB down
    at 40 Hz and at 17 kHz. Level cuts the output by up to 12 dB; at the
    top of its travel the output is at the input's level. The Effect
    controls page lists what the knobs span.

    **The sound.** With no dry path there is no comb: from 200 Hz to 2 kHz
    the level stays within 1 dB at any Depth up to 60 cents. At the
    default patch the sweep is a smooth sine, its third harmonic more than
    25 dB down. The sweep runs free and does not follow a host's tempo;
    `reset()` starts it afresh.

    **Timing.** Latency is the Delay, snapped to a whole sample: 4 ms by
    default, which is 192 samples at 48 kHz and 176 at 44.1 kHz. Nothing
    looks ahead.

    **On a board.** The class needs audiodsp's `audioecho`, and on a board
    without it construction raises `ImportError`.
    """

    NAME = 'Vibrato'
    DISPLAY_NAME = 'Vibrato'
    CATEGORIES = ('Modulation',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
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
    _MACRO_UNITS = {
        0: "Hz", 1: "cents", 2: "s", 4: "ms", 5: "Hz", 6: "Hz", 7: "dB",
    }
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
        self._wow_full_ms = 0.0
        #: The mean `delay_ms` last written, so a move can glide from it.
        self._delay_written = None
        #: The clock index the shape last handed to the node was built for.
        self._m_written = 0.0
        #: Whether the depth last written was the engaged one, so an Engage
        #: move is told apart from a move of any other knob.
        self._engaged_written = None
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
        # The Engage envelope is the node's own depth ramp
        # (`wow_depth_ramp_ms`), so it runs on every interpreter and needs
        # nothing from Python while the output is pulled.
        self._delay.play(self._source)
        orig_reset = getattr(self._delay, "_reset_buffer", None)
        if orig_reset is not None:
            def _reset_delay(single_channel_output=False, audio_channel=0,
                             orig=orig_reset):
                orig(single_channel_output, audio_channel)
                if self._source is not None:
                    audiocore.reset_buffer(self._source,
                                           single_channel_output,
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
        self._output = self._delay
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
        # One grid step below the top is 0.09 dB, so only the top cell counts.
        return abs(self._value(7)) < 0.01

    def _route_output(self):
        if self._level_is_unity():
            self._output = self._delay
            return
        if not self._mixer_armed:
            self._arm_mixer_voice()
        self._output = self._mixer

    def _arm_mixer_voice(self):
        """Arm the Level mixer's voice on the delay, the lazy way, as a
        reset arms a mixer: the voice primes a block of silence, the mixer
        hands it up, and the voice's stand-in is then pointed at the delay,
        so the next pull fetches from where the delay was.

        A native voice's `play()` on the delay primed a block of the music
        there and then, and the output ran 256 frames ahead of it for good:
        5 ms skipped the first time Level left 0 dB, on a board only.
        CPython's voice was armed by hand without a pull, and started at
        level 0 until the music crossed zero, which the silence here opens.
        Both interpreters now arm the same way and render the same bytes.
        """
        voice = self._mixer.voice[0]
        self._mixer_armed = True
        if _component.PORT is None:
            if hasattr(voice, "_remaining"):
                voice._sample = self._delay
                voice._loop = False
                voice._remaining = b""
                voice._source_more = True
            else:
                voice.play(self._delay)
            return
        self._lazy_pending = []
        self._arming_lazily = True
        try:
            self._play_voice(voice, self._delay)
        finally:
            self._arming_lazily = False
        self._hand_up_lazy(getattr(audiocore, "get_buffer", None))

    def _reset_mixer(self):
        audiocore.reset_buffer(self._mixer)
        self._mixer_armed = False

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
        return self._macros[3] >= 0.5

    def _rise_ramp_ms(self):
        """The whole of the Engage envelope in ms: Rise is its 10-90 %, so
        the straight line takes Rise / 0.8."""
        return self._value(2) / RISE_10_90 * 1000.0

    def _write_wow(self):
        """Write the depth Engage asks for. An Engage move travels there over
        the envelope; any other move (Depth, Rate, Delay) over the node's
        20 ms, which also finishes an envelope still under way."""
        engaged = self._engaged()
        ramp_ms = DEPTH_GLIDE_MS
        if (self._engaged_written is not None
                and engaged != self._engaged_written):
            ramp_ms = self._rise_ramp_ms()
        self._engaged_written = engaged
        self._delay.set(wow_depth_ramp_ms=ramp_ms,
                        wow_depth_ms=self._wow_full_ms if engaged else 0.0)

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
        # A move of Rate, Depth or Delay moves the mean line and the clock
        # law at once, while the depth glides over 20 ms. Written as they
        # were, the read head jumped by the whole change on the next frame,
        # a tick each time one was turned. So the mean line walks there
        # over the same 20 ms (the node's `delay_slew`, delay-seconds per
        # second, set from the size of this move), and a new clock law goes
        # to the node, which ramps the depth to zero over the same 20 ms,
        # changes the table there and ramps back (audioecho's wow_shape
        # swap). Only a law that moved is handed over, so a Tone, Body,
        # Level or Engage move does not dip the swing. Depth 0 keeps the
        # last law while the depth glides out under it, as Engage off does.
        if m >= DEPTH_OFF and m != self._m_written:
            self._shape = clock_shape(m)
            self._m_written = m
        last = self._delay_written
        if last is not None and last != delay_ms:
            self._delay.set(
                delay_slew=abs(delay_ms - last) / DEPTH_GLIDE_MS)
        self._delay_written = delay_ms
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
        # The wet path's two one-pole filters ring after the line has
        # emptied: Tone's low-pass, then Body's high-pass, whose state can
        # hold up to full scale and falls by exp(-2 pi f / fs) a frame. Each
        # adds the frames it takes to fall from full scale to under half an
        # LSB (audiocomponents#114: Body alone rang 2 430 frames past the
        # line at 20 Hz, 48 kHz).
        # And a move keeps the read head travelling for up to two glides
        # after it: the mean line's 20 ms, or a new law's dip to zero depth
        # and back. What the wet filters hold from that travel rings out
        # behind it, so the count starts where the travel ends.
        glide = int(math.ceil(2.0 * DEPTH_GLIDE_MS * self._sample_rate
                              / 1000.0))
        self._tail = (int(math.ceil(d_max * self._sample_rate / 1000.0)) + 64
                      + glide
                      + one_pole_ring(damping, self._sample_rate)
                      + one_pole_ring(body, self._sample_rate))

    @property
    def latency_samples(self):
        self._check_live()
        return int(self._latency)

    @property
    def tail_samples(self):
        self._check_live()
        return int(self._tail)
