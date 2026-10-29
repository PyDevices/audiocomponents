"""`AirSpace`'s own trait and planted-fault tests.

The card (frozen 2026-10-12) has five traits, T1-T5. Each is measured here
at a few of its cells, as the card words it, and the same measurement is
shown red on the card's planted fault; the measurements of T2-T5 are also
red on the class built as a wire. The full grids (every seed, both rates,
stereo and mono) are the evidence pack's, from the probe script beside it.

Every law a measurement checks against is written out here from the card,
never taken from the class. No numpy: plain sums, a radix-2 FFT and
Goertzel. The planted faults live in `airspace_plants.py`, which the kit
also runs natively.

The class is reached by `audioeffects.AirSpace`.
"""

import cmath
import math
import os
import sys
import unittest
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

import audiocore                                            # noqa: E402
import airspace_plants as plants                            # noqa: E402
import audioeffects                                         # noqa: E402
from audioeffects.digitaldelay import laps_to_zero          # noqa: E402
from audioeffects.tapedelay import tone_excess              # noqa: E402

VENDOR = "PyDevices"

AirSpace = audioeffects.AirSpace

BLOCK = 256
TIME_I, FEEDBACK_I, GLIDE_I, DRIVE_I, LOOP_TOP_I, LOOP_BASS_I, TOP_CUT_I, \
    LOW_CUT_I, DECAY_I, DAMPING_I, MIX_I = range(11)

#: The kit's plant table (KIT.md): one or two planted faults per trait.
KIT_PLANTS = plants.KIT_PLANTS


# --------------------------------------------------------------------------
# The card's laws, written out independently of the class


SPANS = {
    TIME_I: (20.0, 500.0, True),
    FEEDBACK_I: (0.0, 0.85, False),
    GLIDE_I: (1000.0, 10000.0, True),
    DRIVE_I: (0.0, 1.0, False),
    LOOP_TOP_I: (1000.0, 16000.0, True),
    LOOP_BASS_I: (20.0, 1000.0, True),
    TOP_CUT_I: (1000.0, 16000.0, True),
    LOW_CUT_I: (20.0, 500.0, True),
    DECAY_I: (0.3, 10.0, True),
    DAMPING_I: (500.0, 16000.0, True),
    MIX_I: (0.0, 2.0, False),
}

#: The card's section 3 defaults, in macro order.
CARD_DEFAULTS = (111.0, 0.375, 4000.0, 0.2, 6000.0, 100.0, 5000.0, 100.0,
                 1.8, 4000.0, 0.35)

PATCH_NAMES = ("Chamber Send", "Short Send", "Long Send", "Dark Loop",
               "Bright Chamber", "Driven Tape", "Plain Chamber")


def law_value(index, midi):
    low, high, log = SPANS[index]
    x = midi / 127.0
    if log:
        return low * (high / low) ** x
    return low + (high - low) * x


def law_midi(index, value):
    """The 0-127 position, unquantized, of `value` on macro `index`."""
    low, high, log = SPANS[index]
    if log:
        return 127.0 * math.log(value / low) / math.log(high / low)
    return 127.0 * (value - low) / (high - low)


def law_frames(ms, rate):
    """Time lands on the nearest whole frame."""
    return int(math.floor(ms * rate / 1000.0 + 0.5))


def law_slew(glide_ms):
    """Glide is how long a move across the whole 480 ms range takes."""
    return 480.0 / glide_ms


def law_levels(mix):
    """`audiodelays.Echo`'s Mix: (dry, wet)."""
    return (1.0 if mix <= 1.0 else 2.0 - mix, mix if mix < 1.0 else 1.0)


# --------------------------------------------------------------------------
# Material and rendering


class Feed:
    """int16 frames in 256-frame blocks, then silence for ever."""

    def __init__(self, data, rate, channels):
        self.sample_rate = rate
        self.channel_count = channels
        self.bits_per_sample = 16
        self.samples_signed = True
        self._data = data
        self._at = 0
        self._stride = BLOCK * channels

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        pass

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        chunk = self._data[self._at:self._at + self._stride]
        self._at += self._stride
        if len(chunk) < self._stride:
            chunk = chunk + array("h", bytes(2 * (self._stride - len(chunk))))
        return audiocore.GET_BUFFER_MORE_DATA, memoryview(chunk)


def lcg_noise(frames, channels, rms, seed):
    """Uniform noise at `rms` LSB, its own stream per seed."""
    amp = rms * math.sqrt(3.0)
    state = (seed * 7919 + 17) & 0x7FFFFFFF
    out = array("h", bytes(2 * frames * channels))
    for i in range(frames * channels):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out[i] = int(round((state / 2147483647.0 * 2.0 - 1.0) * amp))
    return out


def burst(on_frames, total_frames, channels, rms, seed):
    data = array("h", bytes(2 * total_frames * channels))
    data[0:on_frames * channels] = lcg_noise(on_frames, channels, rms, seed)
    return data


def tone(hz, frames, rate, channels, peak):
    out = array("h", bytes(2 * frames * channels))
    for n in range(frames):
        v = int(round(peak * math.sin(2.0 * math.pi * hz * n / rate)))
        for c in range(channels):
            out[n * channels + c] = v
    return out


def build(cls, data, rate, channels, patch=None, **options):
    return cls(Feed(data, rate, channels), patch=patch, **options)


def render(effect, frames, actions=None):
    """`frames` frames of the output, int16 interleaved. `actions` maps a
    pull index to a callable taken before that pull."""
    channels = effect.channel_count
    out = array("h")
    k = 0
    while len(out) < frames * channels:
        if actions and k in actions:
            actions[k](effect)
        _, data = audiocore.get_buffer(effect.output)
        out.extend(array("h", bytes(data)))
        k += 1
    return out[:frames * channels]


def mono(pcm, channels):
    """Stereo read as the mean of the two channels."""
    if channels == 1:
        return [float(v) for v in pcm]
    return [(pcm[i] + pcm[i + 1]) * 0.5 for i in range(0, len(pcm), 2)]


def set_value(effect, index, value):
    effect.set_macro(index, law_midi(index, value))


# --------------------------------------------------------------------------
# Readers


def fft(values):
    """Radix-2 FFT of a list of complex numbers whose length is a power of
    two."""
    n = len(values)
    out = list(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            out[i], out[j] = out[j], out[i]
    size = 2
    while size <= n:
        step = cmath.exp(-2j * math.pi / size)
        half = size // 2
        for start in range(0, n, size):
            w = 1.0
            for k in range(half):
                a = out[start + k]
                b = out[start + k + half] * w
                out[start + k] = a + b
                out[start + k + half] = a - b
                w *= step
        size *= 2
    return out


def band_energies(x, rate, bands):
    """Energy of `x` in each (low, high) Hz band, zero-padded to a power
    of two."""
    n = 1
    while n < len(x):
        n *= 2
    spectrum = fft([complex(v) for v in x] + [0j] * (n - len(x)))
    out = []
    for low, high in bands:
        k0 = int(math.ceil(low * n / rate))
        k1 = int(math.floor(high * n / rate))
        out.append(sum(abs(spectrum[k]) ** 2 for k in range(k0, k1 + 1)))
    return out


def goertzel_power(x, hz, rate):
    """Goertzel under a Hann window, so a strong tone elsewhere does not
    leak into the bin read."""
    w = 2.0 * math.pi * hz / rate
    coeff = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    n = len(x)
    step = 2.0 * math.pi / (n - 1) if n > 1 else 0.0
    for i, v in enumerate(x):
        s0 = v * (0.5 - 0.5 * math.cos(step * i)) + coeff * s1 - s2
        s2 = s1
        s1 = s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


class Red(Exception):
    """A window held no energy, or was empty or too short: red, never a
    pass or a NaN."""


def db_ratio(num, den):
    if num <= 0.0 or den <= 0.0:
        raise Red("a window held no energy")
    return 10.0 * math.log10(num / den)


# --------------------------------------------------------------------------
# The traits' measurements


def t1_mismatches(cls, rate, channels, mix, seed, patch=None, **options):
    """T1: a noise burst 1 ms shorter than Time, output against input over
    frames 0 to Time; the count of frames that differ."""
    probe = cls(Feed(array("h", bytes(2 * channels * BLOCK)), rate,
                     channels), patch=patch, **options)
    time_ms = probe.macro(TIME_I)
    probe.deinit()
    frames = law_frames(time_ms, rate)
    on = frames - law_frames(1.0, rate)
    data = burst(on, frames + BLOCK, channels, 8000.0, seed)
    effect = build(cls, data, rate, channels, patch, **options)
    effect.set_macro(MIX_I, law_midi(MIX_I, mix))
    out = render(effect, frames)
    effect.deinit()
    if not any(out):
        raise Red("the output was silent")
    return sum(1 for i in range(frames * channels) if out[i] != data[i])


def t2_darkening(cls, rate, channels, seed, loop_top, top_cut):
    """T2: the 3.5-8 kHz over 200-1000 Hz energy ratio in dB, at 150-450
    ms minus at 1000-1300 ms, at Mix 2, Feedback 0.85, a 20 ms burst."""
    total = int(1.35 * rate)
    data = burst(law_frames(20.0, rate), total, channels, 4000.0, seed)
    effect = build(cls, data, rate, channels, mix=2.0, feedback=0.85,
                   loop_top_hz=loop_top, top_cut_hz=top_cut)
    x = mono(render(effect, total), channels)
    effect.deinit()
    bands = ((3500.0, 8000.0), (200.0, 1000.0))
    early = x[int(0.15 * rate):int(0.45 * rate)]
    late = x[int(1.0 * rate):int(1.3 * rate)]
    hi_e, lo_e = band_energies(early, rate, bands)
    hi_l, lo_l = band_energies(late, rate, bands)
    return db_ratio(hi_e, lo_e) - db_ratio(hi_l, lo_l)


def t2_added(cls, rate, channels, seed, loop_top=16000.0, top_cut=16000.0):
    """T2's reading: the darkening a setting adds over Loop Top and Top
    Cut at 16 kHz."""
    return (t2_darkening(cls, rate, channels, seed, loop_top, top_cut)
            - t2_darkening(cls, rate, channels, seed, 16000.0, 16000.0))


def envelope_db(x, frame):
    """Mean square in dB per non-overlapping frame of `frame` samples."""
    out = []
    for start in range(0, len(x) - frame + 1, frame):
        power = sum(v * v for v in x[start:start + frame]) / frame
        out.append(10.0 * math.log10(power) if power > 0.0 else -1e9)
    return out


def t3_tail_s(cls, rate, channels, seed, time_ms, feedback, seconds=12.0):
    """T3: the time until the 10 ms envelope last sits within 40 dB of
    its peak, at Mix 2, a 20 ms burst."""
    total = int(seconds * rate)
    data = burst(law_frames(20.0, rate), total, channels, 4000.0, seed)
    effect = build(cls, data, rate, channels, mix=2.0, time_ms=time_ms,
                   feedback=feedback)
    x = mono(render(effect, total), channels)
    effect.deinit()
    env = envelope_db(x, int(round(0.01 * rate)))
    peak = max(env)
    if peak <= -1e8:
        raise Red("the render held no energy")
    last = max(i for i, v in enumerate(env) if v >= peak - 40.0)
    if last >= len(env) - 50:
        raise Red("the tail ran to the end of the render")
    return (last + 1) * 0.01


def t3_ratio(cls, rate, channels, seed, time_ms, feedback):
    return (t3_tail_s(cls, rate, channels, seed, time_ms, feedback)
            / t3_tail_s(cls, rate, channels, seed, time_ms, 0.0))


def t4_reading(cls, rate, channels, seed, time_ms=111.0, feedback=0.375,
               seconds=8.0):
    """T4: the normalised autocorrelation, at a lag of one Time, of the
    clamped and detrended 5 ms envelope, at Mix 2, a 10 ms burst."""
    total = int(seconds * rate)
    data = burst(law_frames(10.0, rate), total, channels, 4000.0, seed)
    effect = build(cls, data, rate, channels, mix=2.0, time_ms=time_ms,
                   feedback=feedback)
    x = mono(render(effect, total), channels)
    effect.deinit()
    env = envelope_db(x, int(round(0.005 * rate)))
    peak = max(env)
    if peak <= -1e8:
        raise Red("the render held no energy")
    floor = peak - 40.0
    first = int(round((time_ms + 60.0) / 5.0))
    last = max(i for i, v in enumerate(env) if v >= floor)
    lag = int(round(time_ms / 5.0))
    window = [max(v, floor) for v in env[first:last + 1]]
    if len(window) < 2 * lag:
        raise Red("the window was shorter than two lags")
    n = len(window)
    mean_i = (n - 1) / 2.0
    mean_v = sum(window) / n
    sxx = sum((i - mean_i) ** 2 for i in range(n))
    slope = sum((i - mean_i) * (v - mean_v)
                for i, v in enumerate(window)) / sxx
    resid = [v - (mean_v + slope * (i - mean_i))
             for i, v in enumerate(window)]
    energy = sum(v * v for v in resid)
    if energy <= 0.0:
        raise Red("the window was flat")
    return sum(resid[i] * resid[i + lag] for i in range(n - lag)) / energy


def t5_bend_db(cls, rate, channels, glide_ms, from_ms, to_ms):
    """T5: the bent frequency's power over the held render's, from 50 ms
    into a Time move to 20 ms before its end (at most 1.6 s), on a held
    1 kHz tone at Mix 2. Returns dB."""
    slew = law_slew(glide_ms)
    move_at = int(round(rate / BLOCK))           # the pull nearest 1 s
    start = move_at * BLOCK
    travel_s = abs(to_ms - from_ms) / 1000.0 / slew
    begin = start + int(0.05 * rate)
    end = start + int(min(travel_s - 0.02, 1.6) * rate)
    if end <= begin:
        raise Red("the window was empty")
    bent = 1000.0 * (1.0 - slew if to_ms > from_ms else 1.0 + slew)
    data = tone(1000.0, end + BLOCK, rate, channels, 8000.0)
    powers = []
    for move in (True, False):
        effect = build(cls, data, rate, channels, mix=2.0, time_ms=from_ms,
                       glide_ms=glide_ms)
        actions = None
        if move:
            actions = {move_at: lambda e: set_value(e, TIME_I, to_ms)}
        x = mono(render(effect, end, actions), channels)
        effect.deinit()
        powers.append(goertzel_power(x[begin:end], bent, rate))
    return db_ratio(powers[0], powers[1])


class Wire(AirSpace):
    """Every measurement's control: the class built as a wire."""

    def _route(self):
        self._route_around(self._adapter)


# --------------------------------------------------------------------------
# T1


class T1DryIsUntouched(unittest.TestCase):

    def test_every_patch_stereo_48k(self):
        for patch in sorted(AirSpace.PATCHES):
            for mix in (0.5, 1.0):
                with self.subTest(patch=patch, mix=mix):
                    self.assertEqual(
                        t1_mismatches(AirSpace, 48000, 2, mix, 1, patch), 0)

    def test_the_times_and_the_hardest_settings(self):
        cells = [dict(time_ms=20.0), dict(time_ms=111.0),
                 dict(time_ms=500.0),
                 dict(top_cut_hz=1000.0, loop_top_hz=1000.0, drive=1.0)]
        for rate in (48000, 22050):
            for channels in (2, 1):
                for options in cells:
                    with self.subTest(rate=rate, channels=channels,
                                      **options):
                        self.assertEqual(t1_mismatches(
                            AirSpace, rate, channels, 1.0, 2, **options), 0)

    def test_red_on_the_top_cut_ahead_of_the_splitter(self):
        self.assertGreater(
            t1_mismatches(plants.SendFirst, 48000, 2, 1.0, 1), 0)


# --------------------------------------------------------------------------
# T2


class T2EachRepeatDarker(unittest.TestCase):

    CELLS = ((48000, 2), (22050, 1))

    def test_loop_top_darkens_each_repeat(self):
        for rate, channels in self.CELLS:
            for loop_top in (2000.0, 4000.0):
                with self.subTest(rate=rate, channels=channels,
                                  loop_top=loop_top):
                    added = t2_added(AirSpace, rate, channels, 1,
                                     loop_top=loop_top)
                    if loop_top == 2000.0:
                        self.assertGreaterEqual(added, 6.0)
                    else:
                        self.assertGreater(added, 0.0)

    def test_top_cut_darkens_once(self):
        for rate, channels in self.CELLS:
            for top_cut in (2000.0, 4000.0):
                with self.subTest(rate=rate, channels=channels,
                                  top_cut=top_cut):
                    self.assertLessEqual(
                        t2_added(AirSpace, rate, channels, 1,
                                 top_cut=top_cut), 1.0)

    def test_red_on_the_loop_filter_moved_onto_the_send(self):
        self.assertLess(t2_added(plants.LoopOnSend, 48000, 2, 1,
                                 loop_top=2000.0), 6.0)

    def test_red_on_top_cut_wired_into_the_loop(self):
        self.assertGreater(t2_added(plants.TopCutInLoop, 48000, 2, 1,
                                    top_cut=2000.0), 1.0)

    def test_red_on_a_wire(self):
        with self.assertRaises(Red):
            t2_added(Wire, 48000, 2, 1, loop_top=2000.0)


# --------------------------------------------------------------------------
# T3


class T3FeedbackLengthensTheTail(unittest.TestCase):

    #: (Time ms, Feedback, the card's bar).
    BARS = ((500.0, 0.375, 1.3), (500.0, 0.6, 2.0), (500.0, 0.85, 3.0),
            (111.0, 0.85, 1.6))

    def test_the_bars(self):
        for rate, channels in ((48000, 2), (22050, 1)):
            for time_ms, feedback, bar in self.BARS:
                with self.subTest(rate=rate, channels=channels,
                                  time_ms=time_ms, feedback=feedback):
                    self.assertGreaterEqual(
                        t3_ratio(AirSpace, rate, channels, 1, time_ms,
                                 feedback), bar)

    def test_the_default_adds_only_a_little(self):
        # Not one of the card's bars: its Limits sentence. The probe read
        # 1 to 6 %.
        ratio = t3_ratio(AirSpace, 48000, 2, 1, 111.0, 0.375)
        self.assertGreaterEqual(ratio, 1.0)
        self.assertLess(ratio, 1.1)

    def test_red_on_no_feedback(self):
        self.assertLess(t3_ratio(plants.NoFeedback, 48000, 2, 1, 500.0,
                                 0.85), 3.0)

    def test_red_on_a_wire(self):
        self.assertLess(t3_ratio(Wire, 48000, 2, 1, 500.0, 0.85), 3.0)


# --------------------------------------------------------------------------
# T4


class T4HeardAsAChamber(unittest.TestCase):

    def test_the_cells(self):
        cells = ((111.0, 0.375), (200.0, 0.375), (200.0, 0.6))
        for rate, channels in ((48000, 2), (22050, 1)):
            for time_ms, feedback in cells:
                with self.subTest(rate=rate, channels=channels,
                                  time_ms=time_ms, feedback=feedback):
                    self.assertLessEqual(
                        t4_reading(AirSpace, rate, channels, 1, time_ms,
                                   feedback), 0.6)

    def test_a_short_time_with_high_feedback_is_a_flutter(self):
        # The card's Limits sentence, the other side of the cells above:
        # at Time 20 to 60 ms and Feedback 0.85 the repeats keep their
        # rhythm (the reading stays above 0.6) instead of dissolving into
        # the chamber.
        for time_ms in (20.0, 40.0, 60.0):
            with self.subTest(time_ms=time_ms):
                self.assertGreater(
                    t4_reading(AirSpace, 48000, 2, 1, time_ms, 0.85), 0.6)

    def test_red_on_bare_repeats(self):
        self.assertGreater(t4_reading(plants.BareRepeats, 48000, 2, 1,
                                      200.0, 0.6), 0.6)

    def test_red_on_a_wire(self):
        with self.assertRaises(Red):
            t4_reading(Wire, 48000, 2, 1, 200.0, 0.6)


# --------------------------------------------------------------------------
# T5


class T5TimeBendsThePitch(unittest.TestCase):

    def test_the_bend_both_ways_at_every_glide(self):
        for rate, channels in ((48000, 2), (22050, 1)):
            for glide in (1000.0, 4000.0, 10000.0):
                for from_ms, to_ms in ((111.0, 222.0), (222.0, 111.0)):
                    with self.subTest(rate=rate, channels=channels,
                                      glide=glide, move=(from_ms, to_ms)):
                        self.assertGreaterEqual(
                            t5_bend_db(AirSpace, rate, channels, glide,
                                       from_ms, to_ms), 40.0)

    def test_red_on_a_jump(self):
        self.assertLess(t5_bend_db(plants.JumpTime, 48000, 2, 4000.0,
                                   111.0, 222.0), 40.0)

    def test_red_on_a_wire(self):
        self.assertLess(t5_bend_db(Wire, 48000, 2, 4000.0, 111.0, 222.0),
                        40.0)


# --------------------------------------------------------------------------
# The loop's filter (the Limits sentence on 6 dB per octave)


def tape_feed(effect, data, rate, channels):
    """Re-point the tape at `data`, so the tape alone can be read: the
    chamber and the dry are out of the picture, and what is read is what
    the class handed the tape."""
    effect._fd.play(Feed(data, rate, channels))


def tape_render(effect, frames):
    out = array("h")
    while len(out) < frames * effect.channel_count:
        _, data = audiocore.get_buffer(effect._fd)
        out.extend(array("h", bytes(data)))
    return out[:frames * effect.channel_count]


def loop_gain_db(hz, loop_top=1000.0, rate=48000, channels=2):
    """What one lap of the loop does to a tone of `hz`, in dB: the third
    repeat's level over the second's, whole periods, at Time 100 ms,
    Feedback 0.85 and Loop Bass at its lowest. It is the Feedback and the
    loop's filter at `hz`."""
    time_frames = law_frames(100.0, rate)
    on = law_frames(20.0, rate)
    data = tone(hz, on, rate, channels, 20000.0) + array(
        "h", bytes(2 * channels * 4 * time_frames))
    effect = build(AirSpace, data, rate, channels, time_ms=100.0,
                   feedback=0.85, drive=0.0, loop_top_hz=loop_top,
                   loop_bass_hz=20.0)
    tape_feed(effect, data, rate, channels)
    x = mono(tape_render(effect, 4 * time_frames), channels)
    effect.deinit()
    period = int(round(rate / hz))
    length = (480 // period) * period
    levels = []
    for repeat in (2, 3):
        start = repeat * time_frames + 240
        window = x[start:start + length]
        levels.append(sum(v * v for v in window) / len(window))
    return db_ratio(levels[1], levels[0])


class TheLoopFilter(unittest.TestCase):

    FREQS = (250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)

    def test_it_falls_6_db_per_octave(self):
        # Two octaves above the corner a one-pole falls 12.3 dB, three
        # 18.1: 5.8 dB between them; a two-pole falls 12.
        gain = {hz: loop_gain_db(hz) for hz in (4000.0, 8000.0)}
        octave = gain[4000.0] - gain[8000.0]
        self.assertGreater(octave, 4.5)
        self.assertLess(octave, 7.5)

    def test_it_has_no_bell_and_no_presence_peak(self):
        # The feedback alone is 20 log10 0.85 = -1.41 dB a lap; a bell or
        # a presence boost would read above it, and the response never
        # rises with frequency.
        feedback_db = 20.0 * math.log10(0.85)
        gains = [loop_gain_db(hz) for hz in self.FREQS]
        for hz, gain in zip(self.FREQS, gains):
            with self.subTest(hz=hz):
                self.assertLessEqual(gain, feedback_db + 0.1)
        for low, high in zip(gains, gains[1:]):
            self.assertLessEqual(high, low + 0.1)

    def test_the_top_cuts_is_steeper(self):
        # The Top Cut is a biquad on the send: read alone, it falls faster
        # per octave than the loop's one-pole does.
        rate, channels = 48000, 2
        levels = {}
        for hz in (4000.0, 8000.0):
            data = tone(hz, rate, rate, channels, 8000.0)
            effect = build(AirSpace, data, rate, channels, top_cut_hz=1000.0)
            effect._lp.play(Feed(data, rate, channels))
            out = array("h")
            while len(out) < rate * channels:
                _, block = audiocore.get_buffer(effect._lp)
                out.extend(array("h", bytes(block)))
            x = mono(out, channels)[24000:24000 + 4800]
            effect.deinit()
            levels[hz] = sum(v * v for v in x) / len(x)
        self.assertGreater(db_ratio(levels[4000.0], levels[8000.0]), 9.0)

    def test_a_held_tone_comes_back_at_its_own_pitch(self):
        # No wow: with Time held, the repeats are the tone, delayed. Their
        # energy sits in the tone's bin, not in sidebands.
        rate, channels = 48000, 2
        data = tone(1000.0, 3 * rate, rate, channels, 8000.0)
        effect = build(AirSpace, data, rate, channels, feedback=0.5,
                       drive=0.0)
        tape_feed(effect, data, rate, channels)
        x = mono(tape_render(effect, 2 * rate + 4800), channels)
        effect.deinit()
        # Late enough that every repeat's onset has died away.
        window = x[2 * rate:2 * rate + 4800]
        w = 2.0 * math.pi * 1000.0 / rate
        re = sum(v * math.cos(w * i) for i, v in enumerate(window))
        im = sum(v * math.sin(w * i) for i, v in enumerate(window))
        energy = sum(v * v for v in window)
        self.assertGreater(energy, 0.0)
        self.assertGreater(
            2.0 * (re * re + im * im) / (len(window) * energy), 0.9999)


# --------------------------------------------------------------------------
# The surface


def fresh(rate=48000, channels=2, patch=None, **options):
    data = array("h", bytes(2 * channels * BLOCK))
    return build(AirSpace, data, rate, channels, patch, **options)


class TheAdoption(unittest.TestCase):
    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-10-13, so `create()` serves this one. Serve another class under the name and this goes red."""
        import audiocore
        import audioeffects
        from array import array
        self.assertIs(audioeffects.AirSpace, AirSpace)
        served = audioeffects.create(
            "AirSpace",
            audiocore.RawSample(array("h", [0, 0] * 64), sample_rate=48000,
                                channel_count=2),
            48000)
        self.assertIsInstance(served, AirSpace)
        served.deinit()


class TheSurface(unittest.TestCase):

    def test_the_labels_and_modes(self):
        self.assertEqual(AirSpace.MACRO_LABELS, (
            "Time", "Feedback", "Glide", "Drive", "Loop Top", "Loop Bass",
            "Top Cut", "Low Cut", "Decay", "Damping", "Mix"))
        self.assertEqual(set(AirSpace.MACRO_MODES.values()), {"UNIPOLAR"})

    def test_time_lands_on_whole_frames(self):
        for rate in (48000, 44100, 22050):
            effect = fresh(rate)
            for ms in (20.0, 37.3, 111.0, 222.0, 499.9):
                with self.subTest(rate=rate, ms=ms):
                    set_value(effect, TIME_I, ms)
                    self.assertEqual(effect._handed["delay_frames"],
                                     law_frames(effect.macro(TIME_I), rate))
            effect.deinit()

    def test_what_the_tape_and_the_filter_are_handed(self):
        for rate in (48000, 22050):
            effect = fresh(rate)
            nyquist = rate * 0.5 * 0.98
            for midi in (0, 40, 127):
                with self.subTest(rate=rate, midi=midi):
                    effect.set_macro(FEEDBACK_I, midi)
                    effect.set_macro(DRIVE_I, midi)
                    effect.set_macro(LOOP_TOP_I, midi)
                    effect.set_macro(LOOP_BASS_I, midi)
                    effect.set_macro(TOP_CUT_I, midi)
                    handed = effect._handed
                    self.assertAlmostEqual(
                        handed["feedback"], law_value(FEEDBACK_I, midi))
                    self.assertAlmostEqual(
                        handed["loop_drive"], law_value(DRIVE_I, midi))
                    self.assertAlmostEqual(
                        handed["damping_hz"],
                        min(law_value(LOOP_TOP_I, midi), nyquist))
                    self.assertAlmostEqual(
                        handed["cut_hz"], law_value(LOOP_BASS_I, midi))
                    self.assertAlmostEqual(
                        handed["top_cut_hz"],
                        min(law_value(TOP_CUT_I, midi), nyquist))
            effect.deinit()

    def test_the_glide_law(self):
        effect = fresh()
        self.assertAlmostEqual(effect._handed["delay_slew"], 0.12)
        for midi in (0, 64, 127):
            with self.subTest(midi=midi):
                effect.set_macro(GLIDE_I, midi)
                self.assertAlmostEqual(effect._handed["delay_slew"],
                                       law_slew(law_value(GLIDE_I, midi)))
        effect.deinit()

    def test_the_chamber_follows(self):
        effect = fresh()
        chamber = effect._chamber
        pairs = ((LOW_CUT_I, 7), (DECAY_I, 1), (DAMPING_I, 5))
        for ours, theirs in pairs:
            self.assertAlmostEqual(chamber.macro(theirs),
                                   CARD_DEFAULTS[ours], places=9)
            for midi in (0, 127):
                with self.subTest(macro=ours, midi=midi):
                    effect.set_macro(ours, midi)
                    self.assertAlmostEqual(
                        chamber.macro(theirs), law_value(ours, midi),
                        delta=law_value(ours, midi) * 1e-9)
        # The rest of the chamber stays where the card fixes it.
        self.assertEqual(chamber._character(), 2)
        self.assertAlmostEqual(chamber.macro(2), 0.5 + 64 / 127.0)
        self.assertEqual(chamber.macro(3), 0.0)
        self.assertEqual(chamber.macro(12), 2.0)
        effect.deinit()

    def test_the_mix_law(self):
        for channels in (2, 1):
            effect = fresh(channels=channels)
            voices = effect._mixer.voice
            for mix in (0.35, 0.5, 1.0, 1.5, 2.0):
                with self.subTest(channels=channels, mix=mix):
                    set_value(effect, MIX_I, mix)
                    dry, wet = law_levels(mix)
                    self.assertAlmostEqual(voices[0].level, dry)
                    self.assertAlmostEqual(voices[1].level, wet)
            effect.deinit()

    def test_mix_two_is_the_chamber_alone(self):
        rate = 48000
        frames = law_frames(111.0, rate)
        data = burst(frames - 48, frames + BLOCK, 2, 8000.0, 3)
        effect = build(AirSpace, data, rate, 2, mix=2.0)
        out = render(effect, frames)
        effect.deinit()
        self.assertFalse(any(out))

    def test_mix_zero_is_a_wire(self):
        rate, channels = 48000, 2
        frames = 8192
        ramp = array("h", bytes(2 * frames * channels))
        for i in range(frames * channels):
            ramp[i] = ((i * 37) % 65536) - 32768
        effect = build(AirSpace, ramp, rate, channels, mix=0.0)
        self.assertEqual(render(effect, frames), ramp)
        effect.deinit()

    def test_the_tail_is_gone_when_mix_comes_back(self):
        rate, channels = 48000, 2
        data = burst(4800, rate * 3, channels, 8000.0, 4)
        effect = build(AirSpace, data, rate, channels, mix=1.0,
                       feedback=0.85, decay=10.0)
        pulls = int(0.5 * rate / BLOCK)
        actions = {pulls: lambda e: e.set_macro(MIX_I, 0),
                   pulls + 8: lambda e: e.set_macro(MIX_I, 127)}
        out = render(effect, pulls * BLOCK * 2, actions)
        effect.deinit()
        before = out[(pulls - 8) * BLOCK * channels:pulls * BLOCK * channels]
        after = out[(pulls + 8) * BLOCK * channels:]
        self.assertTrue(any(before))
        self.assertFalse(any(after))

    def test_latency_is_zero(self):
        effect = fresh()
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(AirSpace.LATENCY_SAMPLES, 0)
        effect.deinit()

    def test_patch_0_is_the_defaults_on_the_grid(self):
        steps = AirSpace.PATCHES[0][1]
        for index, value in enumerate(CARD_DEFAULTS):
            with self.subTest(index=index):
                self.assertEqual(steps[index],
                                 int(round(law_midi(index, value))))

    def test_a_fresh_instance_reads_patch_0_and_plays_the_defaults(self):
        effect = fresh()
        self.assertEqual([effect.get_macro(i) for i in range(11)],
                         [float(m) for m in AirSpace.PATCHES[0][1]])
        for index, value in enumerate(CARD_DEFAULTS):
            self.assertEqual(effect.macro(index), value)
        effect.deinit()

    def test_a_constructor_value_on_a_defaults_step_plays_as_given(self):
        # 112.08 ms is the grid step 68, which is also the step of the
        # default 111 ms: it plays 112.08, not 111, until it is moved.
        value = law_value(TIME_I, 68)
        self.assertNotEqual(value, CARD_DEFAULTS[TIME_I])
        effect = fresh(time_ms=value)
        self.assertAlmostEqual(effect.macro(TIME_I), value, places=9)
        self.assertEqual(effect._handed["delay_frames"],
                         law_frames(value, 48000))
        # A host echoing `get_macro` back does not move it.
        effect.set_macro(TIME_I, effect.get_macro(TIME_I))
        self.assertAlmostEqual(effect.macro(TIME_I), value, places=9)
        # A whole step that arrives plays the default there: set_macro,
        # a patch, and reset.
        effect.set_macro(TIME_I, 70)
        effect.set_macro(TIME_I, 68)
        self.assertEqual(effect.macro(TIME_I), 111.0)
        for arrive in (lambda: effect.program_change(0), effect.reset):
            effect.set_macro(TIME_I, 67.5)
            effect.set_macro(TIME_I, 68.5)
            self.assertNotEqual(effect.macro(TIME_I), 111.0)
            effect.set_macro(TIME_I, 70)
            arrive()
            self.assertEqual(effect.macro(TIME_I), 111.0)
        effect.deinit()

    def test_the_other_defaults_play_as_given_too(self):
        for index in range(11):
            if index == MIX_I:
                continue
            step = AirSpace.PATCHES[0][1][index]
            value = law_value(index, step)
            if value == CARD_DEFAULTS[index]:
                continue
            with self.subTest(index=index):
                options = dict(zip(
                    ("time_ms", "feedback", "glide_ms", "drive",
                     "loop_top_hz", "loop_bass_hz", "top_cut_hz",
                     "low_cut_hz", "decay", "damping_hz", "mix"),
                    (value if i == index else CARD_DEFAULTS[i]
                     for i in range(11))))
                effect = fresh(**options)
                self.assertAlmostEqual(effect.macro(index), value,
                                       delta=abs(value) * 1e-12)
                effect.deinit()

    def test_fixed_size_no_sync_and_mono_in_mono_out(self):
        self.assertNotIn("Size", AirSpace.MACRO_LABELS)
        self.assertEqual(AirSpace.CAPABILITIES, ())
        effect = fresh(channels=1)
        self.assertEqual(effect.channel_count, 1)
        self.assertEqual(effect.output.channel_count, 1)
        effect.deinit()

    def test_at_least_20_ms_before_the_chamber(self):
        # The shortest Time, the most Feedback, the chamber alone: nothing
        # reaches the output before 20 ms.
        rate = 48000
        frames = law_frames(20.0, rate)
        data = burst(frames, frames + BLOCK, 2, 8000.0, 5)
        effect = build(AirSpace, data, rate, 2, mix=2.0, time_ms=20.0,
                       feedback=0.85)
        self.assertEqual(effect.macro(TIME_I), 20.0)
        out = render(effect, frames)
        effect.deinit()
        self.assertFalse(any(out))


def square(hz, frames, rate, channels, peak):
    """A square at `peak`, its half period `rate / (2 hz)` frames."""
    half = int(round(rate / (2.0 * hz)))
    out = array("h", bytes(2 * frames * channels))
    for n in range(frames):
        v = int(round(peak)) if (n // half) % 2 == 0 else -int(round(peak))
        for c in range(channels):
            out[n * channels + c] = v
    return out


def rail_run(cls, rate, channels, dbfs, patch=None, seconds=2.0,
             macros=(), **options):
    """The longest run of frames at the rail, on a 100 Hz square at `dbfs`
    (the material the kit's ceiling check rails first on, here at Mix 1,
    where the dry and the chamber are both at unity). `macros` is a tuple of
    (index, MIDI) taken after the patch."""
    frames = int(seconds * rate)
    peak = 32767.0 * 10.0 ** (dbfs / 20.0)
    data = square(100.0, frames, rate, channels, peak)
    effect = build(cls, data, rate, channels, patch, **options)
    effect.set_macro(MIX_I, 64)
    for index, midi in macros:
        effect.set_macro(index, midi)
    out = render(effect, frames)
    effect.deinit()
    if not any(out[-rate * channels:]):
        raise Red("the output fell silent")
    longest = run = 0
    for i in range(frames):
        if any(abs(out[i * channels + c]) >= 32767 for c in range(channels)):
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return longest


#: The cells the ceiling was measured over: (label, patch, macros after the
#: patch, material). They are the worst of the sweep over every patch, every
#: other macro at its stops, all macros at 127, six low squares and noise,
#: at Mix 1 and 12 s: the chamber needs that long to fill. Decay 127 is the
#: worst (a 220 Hz square gains 16.47 dB); then Time 127 (15.18), Feedback
#: 127 (14.83), Short Send (13.99), Long Send (13.77), Dark Loop (12.50) and
#: the macros all open (12.39).
CEILING_CELLS = (
    ("Decay 127", None, ((DECAY_I, 127),), 220),
    ("Time 127", None, ((TIME_I, 127),), 220),
    ("Feedback 127", None, ((FEEDBACK_I, 127),), 147),
    ("Short Send", 1, (), 220),
    ("Long Send", 2, (), 220),
    ("Dark Loop", 3, (), 147),
    ("all macros 127", None, tuple((i, 127) for i in range(10)), "noise"),
)
CEILING_MARGIN_DB = 0.5
#: The gain the docstring quotes for two or more of Feedback, Decay and Time
#: open together, and the level it says to keep the input under there.
QUOTED_COMBINED_GAIN_DB = 25.0


def cell_peak(label, patch, macros, material, dbfs, seconds=12.0):
    """The highest |sample| of a 48 kHz stereo render of one cell at Mix 1."""
    rate, channels = 48000, 2
    frames = int(seconds * rate)
    peak = 32767.0 * 10.0 ** (dbfs / 20.0)
    if material == "noise":
        data = lcg_noise(frames, channels, peak / math.sqrt(3.0), 5)
    else:
        data = square(float(material), frames, rate, channels, peak)
    effect = build(AirSpace, data, rate, channels, patch)
    effect.set_macro(MIX_I, 64)
    for index, midi in macros:
        effect.set_macro(index, midi)
    out = render(effect, frames)
    effect.deinit()
    return max(max(out), -min(out))


class TheInputCeiling(unittest.TestCase):

    def test_the_ceiling_is_minus_17_dbfs(self):
        self.assertEqual(AirSpace.INPUT_CEILING_DBFS, -17.0)

    def test_the_ceiling_keeps_the_margin_to_the_rail_in_the_worst_cells(self):
        ceiling = AirSpace.INPUT_CEILING_DBFS
        limit = 32767.0 * 10.0 ** (-CEILING_MARGIN_DB / 20.0)
        for label, patch, macros, material in CEILING_CELLS:
            with self.subTest(cell=label, material=material):
                self.assertLess(
                    cell_peak(label, patch, macros, material, ceiling),
                    limit)

    def test_feedback_and_decay_together_gain_under_25_db(self):
        # The worst of the pairs and triples of Feedback, Decay and Time
        # at 127 on every patch, over 110, 147 and 220 Hz squares and 12 s:
        # Short Send with Feedback and Decay, 24.71 dB on a 220 Hz square.
        # Read at -40 dBFS, where nothing rails and the chamber is linear.
        rate, channels, frames = 48000, 2, 12 * 48000
        peak = 32767.0 * 10.0 ** (-40.0 / 20.0)
        data = square(220.0, frames, rate, channels, peak)
        effect = build(AirSpace, data, rate, channels, 1)
        effect.set_macro(MIX_I, 64)
        effect.set_macro(FEEDBACK_I, 127)
        effect.set_macro(DECAY_I, 127)
        out = render(effect, frames)
        effect.deinit()
        gain = 20.0 * math.log10(max(max(out), -min(out)) / peak)
        self.assertLess(gain, QUOTED_COMBINED_GAIN_DB)
        self.assertGreater(gain, 24.0)

    def test_the_ceiling_reaches_no_rail_at_mix_1_on_every_patch(self):
        ceiling = AirSpace.INPUT_CEILING_DBFS
        for rate, channels in ((48000, 2), (22050, 1)):
            for patch in sorted(AirSpace.PATCHES):
                with self.subTest(rate=rate, channels=channels, patch=patch):
                    self.assertLessEqual(
                        rail_run(AirSpace, rate, channels, ceiling, patch), 8)

    def test_the_ceiling_reaches_no_rail_with_each_macro_at_its_stops(self):
        ceiling = AirSpace.INPUT_CEILING_DBFS
        for index in range(11):
            if index == MIX_I:
                continue
            for midi in (0, 127):
                with self.subTest(macro=index, midi=midi):
                    self.assertLessEqual(
                        rail_run(AirSpace, 48000, 2, ceiling,
                                 macros=((index, midi),)), 8)

    def test_a_hotter_input_does(self):
        # The old ceiling: at Mix 1 with Feedback 0.85 a -6 dBFS square
        # rails, and so does full scale on the defaults.
        self.assertGreater(
            rail_run(AirSpace, 48000, 2, -6.0,
                     macros=((FEEDBACK_I, 127),)), 8)
        self.assertGreater(rail_run(AirSpace, 48000, 2, 0.0), 8)


# --------------------------------------------------------------------------
# reset() and patch changes


class StaleTape(AirSpace):
    """A reset that does not empty the tape, so its read head glides from
    where it was."""

    def _clear_tape(self):
        self._reach = self._frames


def after_reset(cls, rate, channels, data, from_ms=500.0):
    """Render `data` after a stretch of noise at `from_ms` and a reset."""
    frames = (rate // BLOCK) * BLOCK
    noise = lcg_noise(frames, channels, 4000.0, 9)
    feed = Feed(noise + data, rate, channels)
    effect = cls(feed, time_ms=from_ms)
    render(effect, frames)
    effect.reset()
    out = render(effect, len(data) // channels)
    effect.deinit()
    return out


class TheReset(unittest.TestCase):

    def burst(self, rate, channels):
        return burst(law_frames(20.0, rate), rate, channels, 4000.0, 6)

    def test_reset_renders_as_a_fresh_instance(self):
        for rate, channels in ((48000, 2), (22050, 1)):
            with self.subTest(rate=rate, channels=channels):
                data = self.burst(rate, channels)
                effect = build(AirSpace, data, rate, channels)
                want = render(effect, rate)
                effect.deinit()
                self.assertTrue(any(want))
                self.assertEqual(after_reset(AirSpace, rate, channels, data),
                                 want)

    def test_reset_restores_patch_0_and_the_chamber(self):
        effect = fresh(time_ms=500.0, patch=4)
        lines = fresh()._chamber._lines
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual([effect.get_macro(i) for i in range(11)],
                         [float(m) for m in AirSpace.PATCHES[0][1]])
        self.assertEqual(effect.macro(TIME_I), 111.0)
        self.assertEqual(effect._chamber._lines, lines)
        self.assertAlmostEqual(effect._chamber.macro(1), 1.8, places=12)
        effect.deinit()

    def test_red_on_a_reset_that_keeps_the_tape(self):
        rate, channels = 48000, 2
        data = self.burst(rate, channels)
        effect = build(AirSpace, data, rate, channels)
        want = render(effect, rate)
        effect.deinit()
        self.assertNotEqual(after_reset(StaleTape, rate, channels, data),
                            want)

    def test_a_patch_change_glides(self):
        # Long Send (300 ms) to Plain Chamber (20 ms): the repeats bend
        # up while the head travels.
        rate, channels = 48000, 2
        slew = law_slew(4000.0)
        at = int(round(rate / BLOCK))
        begin = at * BLOCK + int(0.05 * rate)
        end = at * BLOCK + int(0.5 * rate)
        data = tone(1000.0, end + BLOCK, rate, channels, 8000.0)
        powers = []
        for move in (True, False):
            effect = build(AirSpace, data, rate, channels, patch=2)
            effect.set_macro(MIX_I, 127)
            actions = {at: lambda e: e.program_change(6)} if move else None
            x = mono(render(effect, end, actions), channels)
            effect.deinit()
            powers.append(goertzel_power(x[begin:end], 1000.0 * (1 + slew),
                                         rate))
        self.assertGreaterEqual(db_ratio(powers[0], powers[1]), 40.0)


class _NoGetBuffer:
    """`audiocore` as a board's own build has it: no `get_buffer`."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        if name == "get_buffer":
            raise AttributeError(name)
        return getattr(self._module, name)


class HiddenGetBuffer:
    """Hide `audiocore.get_buffer` from the class and `_component` (the
    renders here keep their own reference to it)."""

    def __enter__(self):
        from audioeffects import _component
        self._modules = (sys.modules[AirSpace.__module__], _component)
        for module in self._modules:
            module.audiocore = _NoGetBuffer(audiocore)
        return self

    def __exit__(self, *exc):
        for module in self._modules:
            module.audiocore = audiocore
        return False


def moves_render(data, rate, channels, pulls, actions, hidden):
    if hidden:
        with HiddenGetBuffer():
            effect = build(AirSpace, data, rate, channels)
            out = render(effect, pulls * BLOCK, actions)
    else:
        effect = build(AirSpace, data, rate, channels)
        out = render(effect, pulls * BLOCK, actions)
    effect.deinit()
    return out


#: The scenarios the two wirings must render alike, by name: a pull index
#: maps to what the host does before that pull.
SCENARIOS = {
    "mix 0 before the first pull, reset at 4": {
        0: lambda e: e.set_macro(MIX_I, 0), 4: lambda e: e.reset()},
    "reset before the first pull": {0: lambda e: e.reset()},
    "reset twice before the first pull": {
        0: lambda e: (e.reset(), e.reset())},
    "mix 0 before the first pull, patch 1 at 4": {
        0: lambda e: e.set_macro(MIX_I, 0),
        4: lambda e: e.program_change(1)},
    "mix 0 before the first pull, back at 4": {
        0: lambda e: e.set_macro(MIX_I, 0),
        4: lambda e: e.set_macro(MIX_I, 22)},
    "mix 0 and back mid-stream": {
        10: lambda e: e.set_macro(MIX_I, 0),
        14: lambda e: e.set_macro(MIX_I, 22)},
    "reset twice mid-stream": {10: lambda e: (e.reset(), e.reset())},
    "untouched": {},
}

#: sha1 of `moves_render` at 48 kHz stereo, 40 pulls, LCG noise at 4000 rms
#: seed 11, with `get_buffer` present, per scenario in the order above:
#: what the class rendered before `_replay` was taken out (07bf68a).
#: Re-read once, when audiodsp took CircuitPython 11.0.0-alpha.2's integer
#: mixer ((x * level) >> 15 for x * level / 32767 truncated): the class's
#: code was the same on both sides, the old digests still reproduce on the
#: audiodsp commit before the change, and the new ones keep the same
#: scenarios equal to each other as the old ones did.
GET_BUFFER_RENDERS = (
    "ee269d59de182b592e1039d0285f5e27b3238b71",
    "34021bf776f3789e3813afc73094bb9bef3ecb58",
    "34021bf776f3789e3813afc73094bb9bef3ecb58",
    "6062fc883a56ca4767f0de40934c9f0accba8f55",
    "ee269d59de182b592e1039d0285f5e27b3238b71",
    "3621908f5c28db1295ffe8d2c3e2c0c9696d358a",
    "08b65156619b4852fa5c0be1ebffc68a1f117cc0",
    "34021bf776f3789e3813afc73094bb9bef3ecb58",
)


class WithoutGetBuffer(unittest.TestCase):
    """A board's own audiocore has no `get_buffer`, and the class then
    pulls its mixer through a one-voice mixer of its own (`_pull`): wired
    either way, no voice holds a block, and the renders are the same bytes."""

    def noise(self, rate, channels):
        return lcg_noise(rate, channels, 4000.0, 11)

    def test_every_scenario_renders_the_same_bytes(self):
        rate = 48000
        for channels in (2, 1):
            data = self.noise(rate, channels)
            for name, actions in SCENARIOS.items():
                with self.subTest(channels=channels, scenario=name):
                    want = moves_render(data, rate, channels, 40, actions,
                                        False)
                    got = moves_render(data, rate, channels, 40, actions,
                                       True)
                    self.assertEqual(got, want)

    def test_a_single_block_before_the_first_pull_renders_the_same_bytes(
            self):
        rate = 48000
        for channels in (2, 1):
            data = burst(BLOCK, rate, channels, 8000.0, 12)
            for name in list(SCENARIOS)[:5]:
                with self.subTest(channels=channels, scenario=name):
                    actions = SCENARIOS[name]
                    want = moves_render(data, rate, channels, 40, actions,
                                        False)
                    got = moves_render(data, rate, channels, 40, actions,
                                       True)
                    self.assertEqual(got, want)

    def test_mix_zero_and_back_mid_stream_from_the_first_block(self):
        rate, channels = 48000, 2
        data = self.noise(rate, channels)
        actions = SCENARIOS["mix 0 and back mid-stream"]
        want = moves_render(data, rate, channels, 120, actions, False)
        got = moves_render(data, rate, channels, 120, actions, True)
        self.assertEqual(got, want)

    def test_no_stale_block_after_mix_zero_before_the_first_pull(self):
        rate, channels = 48000, 2
        data = burst(BLOCK, rate, channels, 8000.0, 12)
        actions = {0: lambda e: e.set_macro(MIX_I, 0),
                   4: lambda e: e.set_macro(MIX_I, 22)}
        out = moves_render(data, rate, channels, 60, actions, True)
        self.assertFalse(any(out[4 * BLOCK * channels:]))

    def test_with_get_buffer_the_renders_are_unchanged(self):
        import hashlib
        rate, channels = 48000, 2
        data = self.noise(rate, channels)
        for (name, actions), want in zip(SCENARIOS.items(),
                                         GET_BUFFER_RENDERS):
            with self.subTest(scenario=name):
                out = moves_render(data, rate, channels, 40, actions, False)
                self.assertEqual(hashlib.sha1(bytes(out)).hexdigest(), want)

    def test_red_when_the_wiring_pulls_nothing(self):
        class NoPull(AirSpace):
            def _pull(self):
                pass

        rate, channels = 48000, 2
        data = self.noise(rate, channels)
        actions = SCENARIOS["mix 0 before the first pull, back at 4"]
        want = moves_render(data, rate, channels, 40, actions, False)
        with HiddenGetBuffer():
            effect = build(NoPull, data, rate, channels)
            got = render(effect, 40 * BLOCK, actions)
        effect.deinit()
        self.assertNotEqual(got, want)


# --------------------------------------------------------------------------
# The tail bound against Loop Bass (LOOP_BASS_LAP_FACTOR)


class TapeOut(AirSpace):
    """A measuring tap, not a fault: the wet voice plays the tape itself,
    past the Top Cut and the chamber, so at Mix 2 the output is the tape's
    own repeats, which `_repeats_bound` bounds."""

    def _wet_source(self):
        return self._fd


class SingleLapCount(TapeOut):
    """The repeats' bound before `LOOP_BASS_LAP_FACTOR`: `laps_to_zero`'s
    laps once, as if Loop Bass's high-pass could not lift a lap's peak
    above the last one's."""

    def _repeats_bound(self):
        rate = self._sample_rate
        top_memory, excess = tone_excess(self._handed["damping_hz"], rate)
        bass_memory, _bass = tone_excess(self._handed["cut_hz"], rate)
        laps = laps_to_zero(self._handed["feedback"], excess)
        return laps * (self._reach + 1 + top_memory + bass_memory)


def full_scale_signs(frames, channels, seed):
    """+32 767 or -32 767 per sample, at random from `seed`."""
    state = (seed * 7919 + 17) & 0x7FFFFFFF
    out = array("h", bytes(2 * frames * channels))
    for i in range(frames * channels):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out[i] = 32767 if state & 0x40000000 else -32767
    return out


def tape_tail(cls, rate, feedback, loop_bass_hz, time_ms=500.0, seed=0,
              rack=False):
    """(tail, bound): the frames from the input's end to the tape's last
    non-zero frame, and the bound for it read once the input has stopped,
    `_repeats_bound` on the tape alone or `tail_samples` on the whole rack
    (`rack`). Four laps of full-scale random signs, Loop Top 16 kHz (the
    least memory per lap), the chamber at its shortest Decay, Mix 2. The
    render runs a lap past the bound, so a tail that outlives the bound is
    seen."""
    channels = 2
    lap = law_frames(time_ms, rate)
    frames = 4 * lap
    data = full_scale_signs(frames, channels, seed)
    effect = build(cls, data, rate, channels, time_ms=time_ms,
                   feedback=feedback, loop_bass_hz=loop_bass_hz,
                   loop_top_hz=16000.0, decay=0.3, mix=2.0)
    bound = None
    last = -1
    at = 0
    while bound is None or at < frames + bound + lap:
        _, block = audiocore.get_buffer(effect.output)
        samples = array("h", bytes(block))
        if any(samples):
            i = len(samples) - 1
            while not samples[i]:
                i -= 1
            last = at + i // channels
        at += len(samples) // channels
        if bound is None and at >= frames:
            bound = effect.tail_samples if rack else effect._repeats_bound()
    effect.deinit()
    return last + 1 - frames, bound


class TheTailBound(unittest.TestCase):
    """Loop Bass's high-pass can lift a lap's peak above the last one's, so
    the repeats are counted `LOOP_BASS_LAP_FACTOR` times. The worst cells
    measured sit just under a step of `laps_to_zero`'s count, at long
    Times, where each lap's filter memory adds least."""

    #: (rate, Feedback, Loop Bass Hz): the tape's longest tails against the
    #: single count, 1.49 times it at Feedback 0.0039 (three laps against
    #: two) and 1.11 at 0.4999 (17 against 15).
    WORST = ((48000, 0.0039, 1000.0), (22050, 0.0039, 1000.0),
             (48000, 0.4999, 300.0), (48000, 0.3291, 300.0))

    def test_the_tape_reaches_exact_zero_inside_its_bound(self):
        for rate, feedback, bass in self.WORST:
            tail, bound = tape_tail(TapeOut, rate, feedback, bass)
            self.assertGreater(tail, 0, (rate, feedback, bass))
            self.assertLessEqual(tail, bound, (rate, feedback, bass, tail))

    def test_the_rack_reaches_exact_zero_inside_tail_samples(self):
        for rate, feedback, bass in self.WORST[:3]:
            tail, bound = tape_tail(AirSpace, rate, feedback, bass,
                                    rack=True)
            self.assertGreater(tail, 0, (rate, feedback, bass))
            self.assertLessEqual(tail, bound, (rate, feedback, bass, tail))

    def test_red_on_the_single_count(self):
        # Planted: the laps counted once. The tape outlives that bound at
        # every worst cell.
        for rate, feedback, bass in self.WORST:
            tail, bound = tape_tail(SingleLapCount, rate, feedback, bass)
            self.assertGreater(tail, bound, (rate, feedback, bass))


# --------------------------------------------------------------------------
# The docstring's claims, sentence by sentence (KIT.md, claims)


CLAIMS = (
    ("You send your signal to a tape echo whose repeats feed an echo "
     "chamber, and your dry signal comes back exactly as it went in: the "
     "filters, the drive and the tape act only on the send.",
     ("T1DryIsUntouched.test_every_patch_stereo_48k",
      "T1DryIsUntouched.test_the_times_and_the_hardest_settings",
      "T1DryIsUntouched.test_red_on_the_top_cut_ahead_of_the_splitter")),
    ("Time is the gap between repeats and Feedback how much of each "
     "repeat goes round again.",
     ("TheSurface.test_time_lands_on_whole_frames",
      "TheSurface.test_what_the_tape_and_the_filter_are_handed")),
    ("Loop Top and Loop Bass filter the loop, so each repeat is "
     "darker than the last, and Drive saturates it.",
     ("TheSurface.test_what_the_tape_and_the_filter_are_handed",
      "T2EachRepeatDarker.test_loop_top_darkens_each_repeat")),
    ("Top Cut darkens everything sent to the chamber, once.",
     ("T2EachRepeatDarker.test_top_cut_darkens_once",)),
    ("Low Cut, Decay and Damping set the chamber.",
     ("TheSurface.test_the_chamber_follows",)),
    ("Mix is `audiodelays.Echo`'s: the dry at unity up to 1, the "
     "chamber alone at 2.",
     ("TheSurface.test_the_mix_law",
      "TheSurface.test_mix_two_is_the_chamber_alone")),
    ("More Feedback makes the chamber's tail longer: at Time 500 ms, "
     "Feedback 0.85 at least triples it.",
     "T3FeedbackLengthensTheTail.test_the_bars"),
    ("At the defaults you hear the repeats as a longer chamber, not as a "
     "rhythm of echoes.",
     "T4HeardAsAChamber.test_the_cells"),
    ("Move Time while it plays and the repeats bend in pitch, the way tape "
     "does: down while it lengthens, up while it shortens.",
     "T5TimeBendsThePitch.test_the_bend_both_ways_at_every_glide"),
    ("Glide is how long a move across the whole Time range takes, so "
     "it sets how far they bend: 12 % at the default of 4 s.",
     ("TheSurface.test_the_glide_law",
      "T5TimeBendsThePitch.test_the_bend_both_ways_at_every_glide")),
    ("Keep your input at or under -17 dBFS: at Mix 1 the dry and the "
     "chamber are both at unity and add, so a hotter input can reach the "
     "rail.",
     ("TheInputCeiling.test_the_ceiling_is_minus_17_dbfs",
      "TheInputCeiling.test_the_ceiling_keeps_the_margin_to_the_rail_in_the_"
      "worst_cells",
      "TheInputCeiling.test_the_ceiling_reaches_no_rail_at_mix_1_on_every_"
      "patch",
      "TheInputCeiling.test_the_ceiling_reaches_no_rail_with_each_macro_at_"
      "its_stops",
      "TheInputCeiling.test_a_hotter_input_does")),
    ("That holds on every patch and with any one macro at either end.",
     ("TheInputCeiling.test_the_ceiling_reaches_no_rail_at_mix_1_on_every_"
      "patch",
      "TheInputCeiling.test_the_ceiling_reaches_no_rail_with_each_macro_at_"
      "its_stops")),
    ("Open two or more of Feedback, Decay and Time together and the chamber "
     "builds further, by up to 25 dB: keep your input at or under -26 dBFS "
     "there.",
     "TheInputCeiling.test_feedback_and_decay_together_gain_under_25_db"),
    ("Latency is zero.", "TheSurface.test_latency_is_zero"),
    ("`reset()` empties the tape and the chamber and restores patch 0, "
     "whose Time of 111 ms lands at once instead of gliding.",
     ("TheReset.test_reset_renders_as_a_fresh_instance",
      "TheReset.test_reset_restores_patch_0_and_the_chamber",
      "TheReset.test_red_on_a_reset_that_keeps_the_tape")),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     ("DECLARED:AirSpace,E5-,P5", "DECLARED:AirSpace,E4-m6=,P5")),
    ("Time is the exception: it glides.",
     "T5TimeBendsThePitch.test_the_bend_both_ways_at_every_glide"),
    ("A patch that changes Time glides there too, and the repeats bend "
     "while it travels.",
     "TheReset.test_a_patch_change_glides"),
    ("At the defaults the repeats add only a little length to the tail; "
     "the stretch comes with Feedback above about 0.6 or a long Time.",
     ("T3FeedbackLengthensTheTail.test_the_default_adds_only_a_little",
      "T3FeedbackLengthensTheTail.test_the_bars")),
    ("At a short Time with high Feedback the repeats are heard as a flutter, "
     "not a longer chamber.",
     "T4HeardAsAChamber.test_a_short_time_with_high_feedback_is_a_flutter"),
    ("The loop's filters are gentle, 6 dB per octave, and the Top Cut's is "
     "steeper: there is no loop bell, no presence EQ and no wow.",
     ("TheLoopFilter.test_it_falls_6_db_per_octave",
      "TheLoopFilter.test_the_top_cuts_is_steeper",
      "TheLoopFilter.test_it_has_no_bell_and_no_presence_peak",
      "TheLoopFilter.test_a_held_tone_comes_back_at_its_own_pitch")),
    ("There is always at least 20 ms between the dry and the chamber.",
     ("TheSurface.test_at_least_20_ms_before_the_chamber",
      "T1DryIsUntouched.test_the_times_and_the_hardest_settings")),
    ("The chamber's size is fixed, there is no tempo sync, and a mono "
     "source gets a mono rack.",
     "TheSurface.test_fixed_size_no_sync_and_mono_in_mono_out"),
    ("At Mix 0 the output is your input, byte for byte, and the tail that "
     "was ringing when Mix went to 0 is gone when it comes back.",
     ("TheSurface.test_mix_zero_is_a_wire",
      "TheSurface.test_the_tail_is_gone_when_mix_comes_back")),
)


class TestResetIsFresh(unittest.TestCase):
    """A reset comes back as a fresh instance at patch 0 (kit `fresh`)."""

    def test_the_tail_after_a_reset_from_a_longer_time(self):
        # The reset emptied the tape with the outgoing patch's Time as the
        # head's reach, then patch 0's shorter Time kept it: from patch 2
        # the tail read 361 384 frames where a fresh instance read 251 836
        # (both before the repeats were counted `LOOP_BASS_LAP_FACTOR` times).
        sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                        "support"))
        import kit_fresh
        for patch in sorted(AirSpace.PATCHES):
            for k in (0, kit_fresh.RESET_AT):
                self.assertEqual(kit_fresh.reset_cell(
                    AirSpace, 48000, 2, patch, {}, k), "ok", (patch, k))


if __name__ == "__main__":
    unittest.main()
