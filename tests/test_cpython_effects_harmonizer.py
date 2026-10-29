"""`Harmonizer`'s trait and planted-fault tests.

Six traits, T1 to T6, each with its measurement run over the span listed
with it and the same measurement shown red on a planted fault of the same
kind. `KIT_PLANTS` hands the plants to the kit, which shows each one
differs from the clean class and that no knob stop or patch reproduces it.
`CLAIMS` ties every claim sentence of the docstring to the tests that hold
it.

Every law a measurement checks against is written out here, never taken
from the class: the shifter's 1/256 steps, the splice spacing, the window
in frames, the Mixer's level and pan arithmetic, the Mix law.

Traits 2 to 4 read a ramp probe: the input rises one LSB per frame from
-16384 to +16383, so with one voice alone every output sample is the
position the shifter read. A splice is a burst of steps outside 0..4; a
clean stretch is 256 frames clear of one, across which the output rises by
exactly the node's step `k`.

Since audiodsp v0.6.6 (audiodsp#245) the node moves each splice's incoming
side, by up to a fiftieth of a second, to where its first channel matches
the outgoing side best, so a held note keeps its shifted pitch through the
crossfade. On a ramp the best match is always the farthest move, so the
splices crowd together. In stereo the probe therefore holds the first
channel silent, where the search finds a tie and the node splices exactly
where it always did, and reads the ramp in the second channel. A mono probe
has no quiet channel, so a mono cell is held to the stereo probe with the
ramp in both channels: its one channel is that render's first, byte for
byte. At a 60 ms Window every splice on the ramp makes the whole move, and
the gap is `(window - rate / 50) * 256 / |k - 256|`, stereo and mono.

The default run takes two of the card's eight seeds or ramp offsets per
cell; `HARMONIZER_FULL=1` runs all eight. The module is numpy-free and
imports on MicroPython and CircuitPython, where `unittest` is absent: the
kit reads `KIT_PLANTS` there.
"""

import math
import sys
from array import array

try:
    import unittest
    TestCase = unittest.TestCase
except ImportError:                     # a native interpreter
    unittest = None
    TestCase = object

try:
    import os
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_HERE, "support"))
    sys.path.insert(0, os.path.join(_HERE, "..", "lib"))
    FULL = bool(os.environ.get("HARMONIZER_FULL"))
except (ImportError, AttributeError, NameError):   # no os.path natively
    FULL = False

import kit_common as kc                                     # noqa: E402
import audioeffects                                         # noqa: E402

try:
    import synthio
except ImportError:                     # pragma: no cover
    synthio = None

VENDOR = "PyDevices"

RATES = (48000, 22050)
CHANNELS = (2, 1)
BLOCK = 256
PITCH = 0
VOICE = (1, 2, 3)
LEVEL = (4, 5, 6)
DETUNE = 7
SPREAD = 8
MIX = 9

Harmonizer = audioeffects.Harmonizer

SEEDS = tuple(range(1, 9)) if FULL else (1, 2)
OFFSETS = ((0, 37, 101, 173, 263, 389, 512, 777) if FULL else (0, 263))
#: Frames read after the Mixer's zero-crossing gates have settled.
SETTLE = 4096


# --------------------------------------------------------------------------
# The laws, written out


def step_of(semitones):
    """The shifter's nearest read-rate step, in 256ths of a frame."""
    return int(math.floor(256.0 * 2.0 ** (semitones / 12.0) + 0.5))


def step_cents(k):
    """Half the width of step `k`, in cents: how far a voice can sit from
    the interval it asked for."""
    return 1200.0 * math.log((k + 0.5) / k) / math.log(2.0)


def window_frames(ms, rate):
    return int(ms * rate / 1000.0 + 0.5)


def crossfade(frames):
    return frames // 16


def splice_gap(frames, k):
    """Frames between two splices: the read head gains or loses a whole
    window every `256 / |k - 256|` windows."""
    if k == 256:
        return None
    return frames * 256.0 / abs(k - 256)


def align_span(rate):
    """How far the node moves a splice's incoming side, at most: a
    fiftieth of a second (audiodsp's `audiodsp_pitchshift.c`)."""
    return rate // 50


def moved_gap(frames, k, rate):
    """Frames between two splices on a ramp in the first channel, at a
    Window longer than the move: every splice moves the whole span toward
    the outgoing side, so it regains the window less the span."""
    if k == 256:
        return None
    return (frames - align_span(rate)) * 256.0 / abs(k - 256)


#: The Window the moved law is read at: longer than the move at both rates.
MOVED_WINDOW_MS = 60.0


def semis_of_midi(m):
    """A Pitch or Voice MIDI step as the whole semitone it plays: a
    bipolar knob with its centre at 64, -12 to +12."""
    if m >= 64:
        value = 12.0 * (m - 64) / 63.0
    else:
        value = -12.0 * (64 - m) / 64.0
    return int(math.floor(value + 0.5))


def midi_of_semis(s):
    """The MIDI step a whole semitone sits on (the nearest)."""
    best = None
    for m in range(128):
        if semis_of_midi(m) == s:
            if m >= 64:
                exact = 64 + 63.0 * s / 12.0
            else:
                exact = 64 + 64.0 * s / 12.0
            if best is None or abs(m - exact) < abs(best - exact):
                best = m
    return best


def cents_of_midi(m):
    return 25.0 * m / 127.0


def db_of_midi(m):
    """A Level step in dB; MIDI 0 is off (None)."""
    if m <= 0:
        return None
    return -40.0 + 40.0 * (m - 1) / 126.0


def mix_of_midi(m):
    return 2.0 * m / 127.0


def gains(mix):
    """The house Mix law: (dry, voice)."""
    return (1.0 if mix <= 1.0 else 2.0 - mix), min(mix, 1.0)


def mixer_scale(x, mul):
    """One sample through the Mixer's voice multiply at integer level `mul`
    (32768 is unity): CircuitPython 11.0.0-alpha.2's integer kernel,
    (x * mul) >> 15, which rounds toward minus infinity, clamped."""
    return max(-32768, min(32767, (x * mul) >> 15))


def level_int(gain):
    return int(gain * 32768.0)


def pan_muls(level, pan):
    """(left, right) integer levels of a stereo voice at gain `level` and
    pan `pan`: a pan right of centre attenuates the left, by 32768 - pan in
    Q15, and the side that is not attenuated keeps the full level."""
    p = int(round(min(32767.0 / 32768, max(-32767.0 / 32768, pan))
                  * 32768.0))
    lvl = level_int(level)
    left, right = 32768, 32768
    if p >= 0:
        left = 32768 - p
    else:
        right = 32768 + p
    return (left * lvl) >> 15, (right * lvl) >> 15


# --------------------------------------------------------------------------
# Material


class Rng:
    """A 31-bit LCG: the same uniforms on every interpreter."""

    def __init__(self, seed):
        self.state = (seed * 2654435761 + 12345) & 0x7FFFFFFF

    def uniform(self, low, high):
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return low + (high - low) * (self.state / 2147483648.0)


def _clamp(v):
    return max(-32768, min(32767, int(round(v))))


def gauss(frames, channels, sigma, seed, lead=BLOCK):
    """Gaussian noise at `sigma` LSB, each channel its own, after `lead`
    frames of silence (a zero opens every level gate at once)."""
    rng = Rng(seed)
    out = array("h", bytes(2 * frames * channels))
    for i in range(lead * channels, frames * channels):
        u1 = rng.uniform(1e-9, 1.0)
        u2 = rng.uniform(0.0, 1.0)
        out[i] = _clamp(sigma * math.sqrt(-2.0 * math.log(u1))
                        * math.cos(2.0 * math.pi * u2))
    return out


def chord(frames, channels, rate, seed, peak=6000.0, lead=BLOCK):
    """Three sines between 110 and 880 Hz, random phases per channel,
    normalised to `peak`, after `lead` frames of silence."""
    rng = Rng(seed + 1000)
    freqs = [rng.uniform(110.0, 880.0) for _ in range(3)]
    phases = [[rng.uniform(0.0, 2.0 * math.pi) for _ in range(3)]
              for _ in range(channels)]
    body = []
    for c in range(channels):
        y = [0.0] * frames
        for f, ph in zip(freqs, phases[c]):
            w = 2.0 * math.pi * f / rate
            for i in range(lead, frames):
                y[i] += math.sin(w * (i - lead) + ph)
        top = max(max(y), -min(y)) or 1.0
        body.append([peak * v / top for v in y])
    out = array("h", bytes(2 * frames * channels))
    for i in range(frames):
        for c in range(channels):
            out[i * channels + c] = _clamp(body[c][i])
    return out


def ramp(offset, channels, quiet_first=False):
    """The ramp probe: `offset` + 1 frames of silence (a zero opens every
    level gate at once), then one LSB per frame from -16384 to +16383, the
    same in every channel, or with `quiet_first` silent in the first."""
    lead = offset + 1
    frames = lead + 32768
    out = array("h", bytes(2 * frames * channels))
    first = 1 if (quiet_first and channels > 1) else 0
    for i in range(lead, frames):
        v = -16384 + i - lead
        for c in range(first, channels):
            out[i * channels + c] = v
    return out


def chan(values, channels, which=0):
    return [values[i] for i in range(which, len(values), channels)]


def rms(values):
    if not values:
        return 0.0
    return math.sqrt(sum(v * v for v in values) / len(values))


# --------------------------------------------------------------------------
# Rendering


def render(cls, values, rate, channels, frames=None, options=None,
           patch=None, macros=(), mute_dry=False, actions=None):
    """`cls` around `values`, then silence, as a list of int16 samples:
    `patch` first, then each `(macro, MIDI)` of `macros`."""
    if frames is None:
        frames = len(values) // channels
    feed = kc.feed(values, rate, channels)
    e = cls(feed.port, sample_rate=rate, **(options or {}))
    try:
        if patch is not None:
            e.program_change(patch)
        for index, value in macros:
            e.set_macro(index, value)
        if mute_dry:
            # The kit's mute_dry reading: the class's own output with the
            # dry voice at zero, every tap still pulled.
            e._mixer.voice[0].level = 0.0
        return list(kc.samples(kc.render(e, frames, actions)))
    finally:
        e.deinit()


def alone(k, level=127, mix=127):
    """Macros for voice `k` (0, 1, 2) alone: Mix 2, the others off."""
    return [(MIX, mix)] + [(LEVEL[j], level if j == k else 0)
                           for j in range(3)]


# --------------------------------------------------------------------------
# Reading the ramp


def jumps(y, start):
    """Frames whose step from the one before is outside 0..4."""
    out = []
    for i in range(max(1, start), len(y)):
        d = y[i] - y[i - 1]
        if d < 0 or d > 4:
            out.append(i)
    return out


def stretches(y, start, jl):
    """The rise across each clean stretch: 256 frames that start and end
    at least 4 frames from a jump, taken end to end."""
    import bisect
    rises = []
    a = start
    n = len(y)
    while a + 256 + 4 < n:
        j = bisect.bisect_left(jl, a - 4)
        if j < len(jl) and jl[j] <= a + 256 + 4:
            a = jl[j] + 5
            continue
        rises.append(y[a + 256] - y[a])
        a += 256
    return rises


def splices(jl, fade):
    """Jump frames clustered into splices: within one crossfade of each
    other they are one splice. Returns each splice's first frame."""
    starts = []
    last = None
    for j in jl:
        if last is None or j - last > max(fade, 1):
            starts.append(j)
        last = j
    return starts


def ramp_read(cls, rate, channels, k_voice, macros, offset, options=None,
              patch=None, quiet=False):
    """One voice alone on the ramp: (output channel, analysis start). With
    `quiet` a stereo probe holds its first channel silent and is read in
    the second, at Spread 0 so the voice reaches it at unity."""
    quiet = quiet and channels == 2
    values = ramp(offset, channels, quiet_first=quiet)
    extra = [(SPREAD, 0)] if quiet else []
    y = render(cls, values, rate, channels, options=options, patch=patch,
               macros=alone(k_voice) + list(macros) + extra)
    which = 1 if (channels == 2 and (quiet or k_voice == 1)) else 0
    ms = (options or {}).get("window_ms", 1024.0 / 48.0)
    w = window_frames(ms, rate)
    return chan(y, channels, which), offset + 1 + w + crossfade(w) + 8


def asked(pitch_m, voice_m, detune_m, k_voice):
    share = (-1.0, 1.0, 0.0)[k_voice] * cents_of_midi(detune_m) / 100.0
    return semis_of_midi(pitch_m) + semis_of_midi(voice_m) + share


def claimed_stretch(w, k):
    gap = splice_gap(w, k)
    return gap is None or gap >= 256 + crossfade(w) + 8


def mono_is_stereo(cls, rate, k_voice, macros, offset, options=None,
                   patch=None):
    """Whether one voice alone on a mono ramp renders, byte for byte, the
    first channel of the same voice on a stereo ramp (Spread 0, which a
    mono source ignores)."""
    plays = alone(k_voice) + list(macros) + [(SPREAD, 0)]
    mono = render(cls, ramp(offset, 1), rate, 1, options=options,
                  patch=patch, macros=plays)
    stereo = render(cls, ramp(offset, 2), rate, 2, options=options,
                    patch=patch, macros=plays)
    return mono == chan(stereo, 2)


# --------------------------------------------------------------------------
# The planted faults


class SharedShifter(Harmonizer):
    """T1: voices 1 and 2 share one PitchShift, pulled twice a block."""

    def _voice_source(self, k):
        return self._shifters[0 if k == 1 else k]


class DuckedDry(Harmonizer):
    """T1: the dry ducks by the number of voices that are on."""

    def _dry_level(self):
        on = sum(1 for k in range(3) if self._level(k) > 0.0)
        return Harmonizer._dry_level(self) / (1 + on)


class BareTapOff(Harmonizer):
    """T7: a voice that is off plays its bare tap, the dry, at level 0."""

    def _off_source(self, k):
        return self._taps[k + 1]


class Unrounded(Harmonizer):
    """T2: the node is handed the asked semitones, and floors them."""

    def _node_semitones(self, asked_semitones):
        return asked_semitones


class PitchOnVoice1(Harmonizer):
    """T2: Pitch moves voice 1 only."""

    def _semitones(self, k):
        value = Harmonizer._semitones(self, k)
        if k:
            value -= math.floor(self._value(PITCH) + 0.5)
        return value


class ChorusDetune(Harmonizer):
    """T3: voice 1's node takes a +-10 cent, 1.5 Hz LFO: a chorus."""

    def _refresh(self):
        Harmonizer._refresh(self)
        self._shifters[0].semitones = synthio.LFO(
            rate=1.5, scale=0.1,
            offset=self._node_semitones(self._semitones(0)))


class WindowInBytes(Harmonizer):
    """T4: the window sized in stereo bytes whatever the channel count."""

    def _shifter(self, frames, overlap):
        import audiodelays
        return audiodelays.PitchShift(
            semitones=0.0, mix=1.0, window=frames * 4, overlap=overlap * 4,
            **self._pcm(BLOCK * 2 * self._channel_count))


class WindowAt48k(Harmonizer):
    """T4: the window sized in frames at 48 kHz whatever the rate."""

    def _window_frames(self):
        return int(self._window_ms * 48.0 + 0.5)


class LevelAsAmplitude(Harmonizer):
    """T5 a: a Level read as an amplitude over the span (-6 dB is 0.85)."""

    def _level(self, k):
        db = self._value(LEVEL[k])
        if db < -40.0:
            return 0.0
        return (db + 40.0) / 40.0


class CrossfadeMix(Harmonizer):
    """T5 b: a crossfade Mix law, the dry at 1 - Mix / 2."""

    def _dry_level(self):
        return max(0.0, 1.0 - self._value(MIX) / 2.0)


class SwappedSpread(Harmonizer):
    """T5 c: voice 1 pans right and voice 2 left."""

    def _pans(self):
        pans = Harmonizer._pans(self)
        return (pans[0], pans[2], pans[1], pans[3])


class NoEmpty(Harmonizer):
    """T6: a voice coming back is not emptied."""

    def _empty(self, k):
        pass


class PulledWhileOff(Harmonizer):
    """T6: an off voice keeps its shifter pulled at level 0, and is not
    emptied on the way back."""

    def _off_source(self, k):
        return self._shifters[k]

    def _empty(self, k):
        pass


KIT_PLANTS = {
    "T1a": SharedShifter,
    "T1b": DuckedDry,
    "T2a": Unrounded,
    "T2b": (PitchOnVoice1, None, {"options": {"pitch": 5.0}}),
    "T3": ChorusDetune,
    "T4a": (WindowInBytes, None, {"channels": 1}),
    "T4b": (WindowAt48k, None, {"rate": 22050}),
    "T5a": LevelAsAmplitude,
    "T5b": CrossfadeMix,
    "T5c": (SwappedSpread, 3),
    # Both act only when a Level comes back from off, which the kit's
    # plant check never does; T6's own test shows them red on that move.
    "T6a": NoEmpty,
    "T6b": PulledWhileOff,
}


# --------------------------------------------------------------------------
# T1: each voice is its own machine


def t1_cell(cls, rate, channels, patch, mix_m, material, seed):
    """(all-on render, sum of the four solos, solo RMS problems: a
    channel more than 3 dB from the input's at the voice's gain and pan)."""
    frames = SETTLE + 2048 + BLOCK
    if material == "noise":
        values = gauss(frames, channels, 2000.0, seed)
    else:
        values = chord(frames, channels, rate, seed)
    on = [Harmonizer.PATCHES[patch][1][LEVEL[k]] for k in range(3)]
    base = [(MIX, mix_m)]
    full = render(cls, values, rate, channels, patch=patch, macros=base)
    total = render(cls, values, rate, channels, patch=patch,
                   macros=base + [(LEVEL[k], 0) for k in range(3)])
    problems = []
    x = list(values)
    lo = (SETTLE + BLOCK) * channels
    g_wet = gains(mix_of_midi(mix_m))[1]
    spread = Harmonizer.PATCHES[patch][1][SPREAD] / 127.0
    for k in range(3):
        if not on[k]:
            continue
        macros = base + [(LEVEL[j], 0) for j in range(3) if j != k]
        solo = render(cls, values, rate, channels, patch=patch,
                      macros=macros, mute_dry=True)
        gain = 10.0 ** (db_of_midi(on[k]) / 20.0) * g_wet
        # Each channel against the input's, at the voice's gain and its
        # pan: voice 1 sits left of centre and voice 2 right by Spread.
        pan = (-spread, spread, 0.0)[k] if channels == 2 else 0.0
        if channels == 2:
            sides = [m / 32768.0 for m in pan_muls(1.0, pan)]
        else:
            sides = [1.0]
        for c in range(channels):
            want = rms(chan(x[lo:], channels, c)) * gain * sides[c]
            got = rms(chan(solo[lo:], channels, c))
            if got <= 0.0 or abs(20.0 * math.log10(got / want)) > 3.0:
                problems.append((k, c, got, want))
        total = [a + b for a, b in zip(total, solo)]
    return full, total, problems


def t1_worst(cls, rate, channels, patch, mix_m, seeds):
    worst = 0
    problems = []
    for material in ("noise", "chord"):
        for seed in seeds:
            full, total, bad = t1_cell(cls, rate, channels, patch, mix_m,
                                       material, seed)
            worst = max(worst, max(abs(a - b) for a, b in
                                   zip(full, total)))
            problems.extend(bad)
    return worst, problems


class T1Independent(TestCase):
    """Turning one voice on or off never changes the dry or the other
    voices: the all-on render is the sum of four solos, sample for sample,
    and each voice solo carries its level."""

    def test_the_sum_of_the_solos(self):
        for rate in RATES:
            for channels in CHANNELS:
                for patch in (0, 3, 5):
                    for mix_m in (32, 64, 95):
                        worst, problems = t1_worst(
                            Harmonizer, rate, channels, patch, mix_m, SEEDS)
                        cell = (rate, channels, patch, mix_m)
                        self.assertEqual(worst, 0, cell)
                        self.assertEqual(problems, [], cell)

    def test_a_shared_shifter_is_red(self):
        worst, _ = t1_worst(SharedShifter, 48000, 2, 0, 64, (1,))
        self.assertGreater(worst, 100)

    def test_a_ducked_dry_is_red(self):
        worst, _ = t1_worst(DuckedDry, 48000, 2, 0, 64, (1,))
        self.assertGreater(worst, 100)


# --------------------------------------------------------------------------
# T2: the intervals


def t2_cell(cls, rate, channels, k_voice, pitch_m, voice_m, detune_m,
            patch=None, offsets=OFFSETS):
    """None if the cell is not claimed, else a list of failures."""
    if patch is not None:
        values = Harmonizer.PATCHES[patch][1]
        voice_m = values[VOICE[k_voice]]
        detune_m = values[DETUNE]
        pitch_m = values[PITCH]
    a = asked(pitch_m, voice_m, detune_m, k_voice)
    k = step_of(a)
    w = window_frames(1024.0 / 48.0, rate)
    if not claimed_stretch(w, k):
        return None
    bad = []
    macros = [(PITCH, pitch_m), (VOICE[k_voice], voice_m),
              (DETUNE, detune_m)]
    for offset in offsets:
        if channels == 1:
            if not mono_is_stereo(cls, rate, k_voice, macros, offset,
                                  patch=patch):
                bad.append((offset, "mono"))
            continue
        y, start = ramp_read(cls, rate, channels, k_voice, macros, offset,
                             patch=patch, quiet=True)
        rises = stretches(y, start, jumps(y, start))
        if len(rises) < 8 or any(r != k for r in rises):
            bad.append((offset, k, len(rises), sorted(set(rises))[:4]))
    return bad


class T2Intervals(TestCase):
    """Each voice reads at `round(256 * 2^(asked / 12))`, the nearest step
    the shifter has to Pitch + Voice + its Detune share."""

    def _check(self, cls, rate, channels, cells):
        claimed = 0
        for cell in cells:
            bad = t2_cell(cls, rate, channels, *cell)
            if bad is None:
                continue
            claimed += 1
            self.assertEqual(bad, [], (rate, channels, cell))
        self.assertGreater(claimed, 0)

    def test_every_voice_1_position(self):
        seen = set()
        cells = []
        for m in range(128):
            s = semis_of_midi(m)
            if s not in seen:
                seen.add(s)
                cells.append((0, 64, m, 0))
        self.assertEqual(len(cells), 25)
        self._check(Harmonizer, 48000, 2, cells)

    def test_pitch_moves_every_voice(self):
        cells = []
        for pitch in (-12, 7, 12):
            for detune_m in (0, 127):
                for k in range(3):
                    voice_m = Harmonizer.PATCHES[0][1][VOICE[k]]
                    cells.append((k, midi_of_semis(pitch), voice_m,
                                  detune_m))
        self._check(Harmonizer, 48000, 2, cells)

    def test_every_patch(self):
        for rate in RATES:
            for channels in CHANNELS:
                cells = []
                for patch in sorted(Harmonizer.PATCHES):
                    levels = Harmonizer.PATCHES[patch][1][4:7]
                    for k in range(3):
                        if levels[k]:
                            cells.append((k, 0, 0, 0, patch))
                self._check(Harmonizer, rate, channels, cells)

    def test_plus_24_at_22050_is_not_claimed(self):
        w = window_frames(1024.0 / 48.0, 22050)
        self.assertLess(splice_gap(w, step_of(24.0)), 158)
        self.assertFalse(claimed_stretch(w, step_of(24.0)))

    def test_within_half_a_step(self):
        """Every interval a voice can ask for, at every Detune step, lands
        on its nearest step: the worst miss is 3.4 cents from unison up,
        6.8 down to an octave below and 13.7 below that."""
        worst = {"up": 0.0, "octave": 0.0, "low": 0.0}
        for s in range(-24, 25):
            for d in range(128):
                for share in (-1, 0, 1):
                    a = s + share * cents_of_midi(d) / 100.0
                    k = step_of(a)
                    exact = 256.0 * 2.0 ** (a / 12.0)
                    self.assertLessEqual(abs(exact - k), 0.5)
                    miss = abs(1200.0 * math.log(k / 256.0) / math.log(2.0)
                               - 100.0 * a)
                    region = ("up" if a >= 0 else
                              "octave" if a >= -12 else "low")
                    worst[region] = max(worst[region], miss)
        self.assertLessEqual(worst["up"], 3.4)
        self.assertLessEqual(worst["octave"], 6.8)
        self.assertLessEqual(worst["low"], 13.7)
        self.assertGreater(worst["low"], 13.5)

    def test_detune_moves_in_steps_of_about_7_cents_near_unison(self):
        width = 1200.0 * math.log(257.0 / 256.0) / math.log(2.0)
        self.assertAlmostEqual(width, 6.75, places=2)
        # So Detune 3 cents leaves both voices on the unison step.
        self.assertEqual(step_of(0.03), 256)
        self.assertEqual(step_of(-0.03), 256)

    def test_unrounded_semitones_are_red(self):
        bad = t2_cell(Unrounded, 48000, 2, 0, 64, 85, 0, offsets=(0,))
        self.assertTrue(bad)

    def test_pitch_on_voice_1_only_is_red(self):
        bad = t2_cell(PitchOnVoice1, 48000, 2, 1, midi_of_semis(7), 101, 0,
                      offsets=(0,))
        self.assertTrue(bad)


# --------------------------------------------------------------------------
# T3: Detune holds still


def t3_cell(cls, rate, channels, patch, detune_m, offsets=OFFSETS):
    """Failures for voices 1 and 2 at `patch` with Detune at `detune_m`."""
    values = Harmonizer.PATCHES[patch][1]
    bad = []
    interval = semis_of_midi(values[VOICE[0]])
    k0 = step_of(interval)
    cents = cents_of_midi(detune_m)
    # More than half a step either way: the lower half of a step is the
    # wider in cents.
    beyond = cents > 1200.0 * math.log(k0 / (k0 - 0.5)) / math.log(2.0)
    for offset in offsets:
        ks = []
        if channels == 1:
            for k_voice in (0, 1):
                if not mono_is_stereo(cls, rate, k_voice,
                                      [(DETUNE, detune_m)], offset,
                                      patch=patch):
                    bad.append((offset, k_voice, "mono"))
            continue
        for k_voice in (0, 1):
            y, start = ramp_read(cls, rate, channels, k_voice,
                                 [(DETUNE, detune_m)], offset, patch=patch,
                                 quiet=True)
            rises = stretches(y, start, jumps(y, start))
            if len(rises) < 8 or len(set(rises)) != 1:
                bad.append((offset, k_voice, len(rises),
                            sorted(set(rises))[:4]))
                ks.append(None)
            else:
                ks.append(rises[0])
        if None in ks:
            continue
        if beyond and not ks[0] < k0 < ks[1]:
            bad.append((offset, "order", ks, k0))
        if not ks[0] <= k0 <= ks[1]:
            bad.append((offset, "side", ks, k0))
    return bad


class T3SteadyDetune(TestCase):
    """Detune is a steady offset: every clean stretch of a detuned voice
    rises by the same step, voice 1 below the undetuned step and voice 2
    above it wherever Detune is more than half a step."""

    def test_every_eighth_position(self):
        positions = list(range(0, 128, 8)) + [127]
        for rate in RATES:
            for channels in CHANNELS:
                for patch in (1, 2):
                    for d in positions:
                        bad = t3_cell(Harmonizer, rate, channels, patch, d,
                                      offsets=OFFSETS[:1] if not FULL
                                      else OFFSETS)
                        self.assertEqual(bad, [],
                                         (rate, channels, patch, d))

    def test_a_chorus_is_red(self):
        for rate in RATES:
            bad = t3_cell(ChorusDetune, rate, 2, 1, 71, offsets=(0,))
            self.assertTrue(bad, rate)


# --------------------------------------------------------------------------
# T4: the splice spacing


T4_INTERVALS = (4, 7, 12, -5, -7, -12)
T4_WINDOWS = (5.0, 1024.0 / 48.0, 60.0)


def t4_cell(cls, rate, channels, window_ms, interval, offsets=OFFSETS,
            quiet=True):
    """None if not claimed, else [(offset, measured mean gap or None)].
    `quiet`: the stereo probe with its first channel silent, held to the
    plain law; otherwise the ramp in every channel, held to the moved
    law."""
    w = window_frames(window_ms, rate)
    k = step_of(interval)
    if quiet and channels == 2:
        gap = splice_gap(w, k)
    else:
        gap = moved_gap(w, k, rate)
    start = w + crossfade(w) + 8
    if gap <= 0 or 5 * gap > 32768 - start:
        return None
    out = []
    for offset in offsets:
        y, start = ramp_read(cls, rate, channels, 0,
                             [(VOICE[0], midi_of_semis(interval))], offset,
                             options={"window_ms": window_ms}, quiet=quiet)
        starts = splices(jumps(y, start), crossfade(w))
        if len(starts) < 5:
            out.append((offset, None, gap))
            continue
        mean = (starts[-1] - starts[0]) / float(len(starts) - 1)
        out.append((offset, mean, gap))
    return out


def t4_bad(cells):
    return [c for c in cells if c[1] is None or
            abs(c[1] - c[2]) > 0.01 * c[2]]


class T4Window(TestCase):
    """Where the first channel gives the splice nothing to match, the mean
    gap between splices is `window_frames * 256 / |k - 256|`, the same at
    every rate. Where it does, each splice moves up to a fiftieth of a
    second, and on a ramp at a 60 ms Window the gap is
    `(window_frames - rate / 50) * 256 / |k - 256|`, stereo and mono
    alike."""

    def test_the_gap(self):
        # Restated 2026-10-14 for audiodsp#245's splice fix: the plain law
        # is read on the stereo probe with a silent first channel (it held
        # on the ramp in every channel before the node moved its splices),
        # and a mono cell plays the stereo ramp's first channel.
        claimed = 0
        for rate in RATES:
            for ms in T4_WINDOWS:
                for interval in T4_INTERVALS:
                    cells = t4_cell(Harmonizer, rate, 2, ms, interval)
                    if cells is None:
                        continue
                    claimed += 1
                    self.assertEqual(
                        t4_bad(cells), [],
                        (rate, ms, interval, cells))
                    macros = [(VOICE[0], midi_of_semis(interval))]
                    for offset in OFFSETS:
                        self.assertTrue(mono_is_stereo(
                            Harmonizer, rate, 0, macros, offset,
                            options={"window_ms": ms}),
                            (rate, ms, interval, offset))
        self.assertGreater(claimed, 20)

    def test_a_splice_moves_toward_the_match(self):
        claimed = 0
        for rate in RATES:
            for channels in CHANNELS:
                for interval in T4_INTERVALS:
                    cells = t4_cell(Harmonizer, rate, channels,
                                    MOVED_WINDOW_MS, interval, quiet=False)
                    if cells is None:
                        continue
                    claimed += 1
                    self.assertEqual(
                        t4_bad(cells), [],
                        (rate, channels, interval, cells))
        self.assertGreaterEqual(claimed, 20)

    def test_a_fifth_up_splices_every_43_ms(self):
        for rate in RATES:
            cells = t4_cell(Harmonizer, rate, 2, 1024.0 / 48.0, 7,
                            offsets=(0,))
            mean_ms = 1000.0 * cells[0][1] / rate
            self.assertTrue(42.5 <= mean_ms <= 43.5, (rate, mean_ms))

    def test_unison_never_splices(self):
        for rate in RATES:
            for channels in CHANNELS:
                for ms in T4_WINDOWS:
                    y, start = ramp_read(
                        Harmonizer, rate, channels, 0,
                        [(VOICE[0], 64)], 0, options={"window_ms": ms})
                    self.assertEqual(jumps(y, start), [])
                    w = window_frames(ms, rate)
                    lag = [i - (y[i] + 16385)
                           for i in range(start, len(y))]
                    # A fixed delay, wherever the move to unison left the
                    # read head: between the crossfade and the window.
                    self.assertEqual(min(lag), max(lag))
                    self.assertTrue(crossfade(w) <= lag[0] <= w, lag[0])
                    # Built at unison, it is one crossfade.
                    y = render(Harmonizer, ramp(0, channels), rate,
                               channels, options={
                                   "window_ms": ms, "voice1": 0.0,
                                   "level1_db": 0.0, "level2_db": -99.0,
                                   "level3_db": -99.0, "mix": 2.0})
                    y = chan(y, channels)
                    lag = [i - (y[i] + 16385)
                           for i in range(start, len(y))]
                    self.assertEqual((min(lag), max(lag)),
                                     (crossfade(w), crossfade(w)))

    def test_a_shifted_voice_trails_by_the_crossfade_to_the_window(self):
        for rate in RATES:
            for interval in (-12, 7, 12):
                y, start = ramp_read(
                    Harmonizer, rate, 2, 0,
                    [(VOICE[0], midi_of_semis(interval))], 0)
                w = window_frames(1024.0 / 48.0, rate)
                lag = [i - (y[i] + 16385) for i in range(start, len(y))]
                self.assertGreaterEqual(min(lag), crossfade(w))
                self.assertLessEqual(max(lag), w)

    def test_a_window_in_bytes_is_red(self):
        cells = t4_cell(WindowInBytes, 48000, 1, MOVED_WINDOW_MS, 7,
                        offsets=(0,), quiet=False)
        self.assertTrue(t4_bad(cells))
        self.assertFalse(t4_bad(t4_cell(Harmonizer, 48000, 1,
                                        MOVED_WINDOW_MS, 7, offsets=(0,),
                                        quiet=False)))
        macros = [(VOICE[0], midi_of_semis(7))]
        self.assertFalse(mono_is_stereo(WindowInBytes, 48000, 0, macros, 0))

    def test_a_window_at_48k_is_red(self):
        cells = t4_cell(WindowAt48k, 22050, 2, 1024.0 / 48.0, 7,
                        offsets=(0,))
        self.assertTrue(t4_bad(cells))
        self.assertFalse(t4_bad(t4_cell(Harmonizer, 22050, 2,
                                        1024.0 / 48.0, 7, offsets=(0,))))


# --------------------------------------------------------------------------
# T5: the balance controls


T5_FRAMES = SETTLE + 2048 + BLOCK


def t5_noise(channels, seed):
    return gauss(T5_FRAMES, channels, 1000.0, seed)


def t5_level(cls, rate, channels, seed):
    """Worst |error| of each Level against the 0 dB solo scaled by the
    Mixer's own arithmetic."""
    values = t5_noise(channels, seed)
    worst = 0
    for k in (0, 2):
        ref = render(cls, values, rate, channels, macros=alone(k, 127))
        for m in (108, 64, 1):
            got = render(cls, values, rate, channels, macros=alone(k, m))
            gain = 10.0 ** (db_of_midi(m) / 20.0)
            if channels == 2:
                muls = pan_muls(gain, 0.0)
            else:
                muls = (level_int(gain),)
            for i in range(SETTLE * channels, len(got)):
                want = mixer_scale(ref[i], muls[i % channels])
                worst = max(worst, abs(got[i] - want))
    return worst


def t5_mix(cls, rate, channels, seed):
    values = t5_noise(channels, seed)
    levels = [(LEVEL[k], 127) for k in range(3)]
    dry = render(cls, values, rate, channels, macros=levels + [(MIX, 0)])
    wet = render(cls, values, rate, channels, macros=levels + [(MIX, 127)])
    worst = 0
    for m in (32, 64, 95, 127):
        got = render(cls, values, rate, channels,
                     macros=levels + [(MIX, m)])
        g_dry, g_wet = gains(mix_of_midi(m))
        for i in range(SETTLE * channels, len(got)):
            want = g_dry * dry[i] + g_wet * wet[i]
            worst = max(worst, abs(got[i] - want))
    return worst


def t5_spread(cls, rate, seed):
    """Worst |error| of voices 1 and 2 against their Spread-0 solos through
    the Mixer's pan arithmetic, and of the dry and voice 3 against their
    Spread-0 selves."""
    values = t5_noise(2, seed)
    worst = 0
    for s_m in (64, 114):
        spread = s_m / 127.0
        for k in (0, 1):
            ref = render(cls, values, rate, 2,
                         macros=alone(k) + [(SPREAD, 0)])
            got = render(cls, values, rate, 2,
                         macros=alone(k) + [(SPREAD, s_m)])
            pan = -spread if k == 0 else spread
            muls = pan_muls(1.0, pan)
            for i in range(SETTLE * 2, len(got)):
                # The Spread-0 solo is the voice itself: unity is a wire.
                want = mixer_scale(ref[i], muls[i % 2])
                worst = max(worst, abs(got[i] - want))
        for macros in (alone(2), [(LEVEL[j], 0) for j in range(3)]):
            ref = render(cls, values, rate, 2, macros=macros + [(SPREAD, 0)])
            got = render(cls, values, rate, 2,
                         macros=macros + [(SPREAD, s_m)])
            worst = max(worst, max(abs(a - b) for a, b in zip(ref, got)))
    return worst


class T5Balance(TestCase):
    """Level, Mix and Spread do what their labels say, read after the
    Mixer's level gates have settled."""

    def test_level(self):
        for rate in RATES:
            for channels in CHANNELS:
                for seed in SEEDS:
                    self.assertEqual(
                        t5_level(Harmonizer, rate, channels, seed), 0,
                        (rate, channels, seed))

    def test_mix(self):
        for rate in RATES:
            for channels in CHANNELS:
                for seed in SEEDS:
                    self.assertLess(
                        t5_mix(Harmonizer, rate, channels, seed), 4,
                        (rate, channels, seed))

    def test_spread(self):
        for rate in RATES:
            for seed in SEEDS:
                self.assertEqual(t5_spread(Harmonizer, rate, seed), 0,
                                 (rate, seed))

    def test_mono_spread_does_nothing(self):
        values = t5_noise(1, 1)
        for rate in RATES:
            ref = render(Harmonizer, values, rate, 1, patch=3,
                         macros=[(SPREAD, 0)])
            got = render(Harmonizer, values, rate, 1, patch=3,
                         macros=[(SPREAD, 127)])
            self.assertEqual(ref, got, rate)

    def test_level_as_amplitude_is_red(self):
        self.assertGreater(t5_level(LevelAsAmplitude, 48000, 2, 1), 100)

    def test_a_crossfade_mix_is_red(self):
        self.assertGreater(t5_mix(CrossfadeMix, 48000, 2, 1), 100)

    def test_swapped_spread_is_red(self):
        self.assertGreater(t5_spread(SwappedSpread, 48000, 1), 100)


# --------------------------------------------------------------------------
# T6: a voice comes back from silence


def t6_run(cls, rate, channels, window_ms, seed):
    """(non-zero samples in the silence, dB of the return against before,
    voice 3's RMS before)."""
    def blocks(seconds):
        return int(seconds * rate / BLOCK + 0.5)
    n1, n2, n4, n5 = blocks(0.5), blocks(0.3), blocks(0.2), blocks(0.5)
    first = gauss((n1 + n2) * BLOCK, channels, 2000.0, seed, lead=0)
    second = gauss(n5 * BLOCK, channels, 2000.0, seed + 100, lead=0)
    silence = array("h", bytes(2 * (1 + n4) * BLOCK * channels))
    values = array("h", list(first) + list(silence) + list(second))
    level = Harmonizer.PATCHES[0][1][LEVEL[2]]
    off_at = n1
    on_at = n1 + n2 + 1

    def off(e):
        e.set_macro(LEVEL[2], 0)

    def on(e):
        e.set_macro(LEVEL[2], level)
    y = render(cls, values, rate, channels, options={"window_ms": window_ms},
               macros=alone(2, level), actions={off_at: off, on_at: on})
    quarter = blocks(0.25) * BLOCK * channels
    before = rms(y[off_at * BLOCK * channels - quarter:
                   off_at * BLOCK * channels])
    hush = y[on_at * BLOCK * channels:(on_at + n4) * BLOCK * channels]
    end = (on_at + n4 + n5) * BLOCK * channels
    after = rms(y[end - quarter:end])
    loud = sum(1 for v in hush if v)
    db = 20.0 * math.log10(after / before) if after and before else -999.0
    return loud, db, before


class T6Return(TestCase):
    """A voice turned back on plays exact silence over silence, and then
    comes back to its level."""

    def test_the_return(self):
        for rate in RATES:
            for channels in CHANNELS:
                for ms in (5.0, 60.0):
                    for seed in SEEDS:
                        loud, db, before = t6_run(Harmonizer, rate,
                                                  channels, ms, seed)
                        cell = (rate, channels, ms, seed)
                        self.assertGreater(before, 100.0, cell)
                        self.assertEqual(loud, 0, cell)
                        self.assertLessEqual(abs(db), 3.0, cell)

    def test_no_emptying_is_red(self):
        for rate in RATES:
            loud, _, _ = t6_run(NoEmpty, rate, 2, 60.0, 1)
            self.assertGreater(loud, 0, rate)

    def test_pulled_while_off_is_red(self):
        for rate in RATES:
            loud, _, _ = t6_run(PulledWhileOff, rate, 2, 60.0, 1)
            self.assertGreater(loud, 0, rate)


# --------------------------------------------------------------------------
# T7: a voice turned off plays nothing from the move on


def sine(frames, channels, amp, period, lead=BLOCK):
    """A sine of `period` frames after `lead` frames of silence."""
    out = array("h", bytes(2 * frames * channels))
    for i in range(lead, frames):
        v = int(round(amp * math.sin(2.0 * math.pi * (i - lead) / period)))
        for c in range(channels):
            out[i * channels + c] = v
    return out


def t7_leak(cls, rate, channels, hz, mix_m, k, how):
    """Frames, from the move on, where a render that turns voice `k` off
    mid-stream differs from an instance built with it off: the dry or a
    voice playing at an old level for want of the move."""
    n = 40
    at = 20
    values = sine(n * BLOCK, channels, 8000.0, rate / hz)
    base = [(MIX, mix_m), (SPREAD, 127)]
    if how == "level":
        def move(e):
            e.set_macro(LEVEL[k], 0)
        first = base
        built = base + [(LEVEL[k], 0)]
    else:
        # Patch 0 with Spread and Mix as asked, then patch 6 (patch 0
        # without voice 3); the reference is patch 0 with voice 3 off.
        assert k == 2

        def move(e):
            e.program_change(6)
            for index, value in base:
                e.set_macro(index, value)
        first = base
        built = base + [(LEVEL[2], 0)]
    y = render(cls, values, rate, channels, macros=first,
               actions={at: move})
    ref = render(cls, values, rate, channels, macros=built)
    start = at * BLOCK * channels
    return sorted(set(i // channels for i in range(start, len(y))
                      if y[i] != ref[i]))


class T7TurnOff(TestCase):
    """Turning a voice off never lets the dry through at the voice's old
    level and pan: from the move on, the render is the one of an instance
    built with the voice off, byte for byte."""

    def _cells(self, cls):
        for rate in RATES:
            for channels in CHANNELS:
                for hz in (41.2, 50.0):
                    for mix_m in (64, 127):
                        for k, how in ((0, "level"), (2, "level"),
                                       (2, "patch")):
                            yield ((rate, channels, hz, mix_m, k, how),
                                   t7_leak(cls, rate, channels, hz, mix_m,
                                           k, how))

    def test_off_plays_nothing(self):
        for cell, leaked in self._cells(Harmonizer):
            self.assertEqual(leaked, [], cell)

    def test_the_bare_tap_is_red(self):
        for cell, leaked in self._cells(BareTapOff):
            if cell[:3] == (48000, 2, 50.0) and cell[3] == 127:
                self.assertGreater(len(leaked), 0, cell)


# --------------------------------------------------------------------------
# The surface, the wire, the tail


class TheAdoption(TestCase):
    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-10-13, so `create()` serves this one. Serve another class under the name and this goes red."""
        import audiocore
        import audioeffects
        from array import array
        self.assertIs(audioeffects.Harmonizer, Harmonizer)
        served = audioeffects.create(
            "Harmonizer",
            audiocore.RawSample(array("h", [0, 0] * 64), sample_rate=48000,
                                channel_count=2),
            48000)
        self.assertIsInstance(served, Harmonizer)
        served.deinit()


class TheSurface(TestCase):

    def _fresh(self, rate=48000, channels=2, **options):
        feed = kc.feed(array("h", bytes(4 * BLOCK * channels)), rate,
                       channels)
        return Harmonizer(feed.port, sample_rate=rate, **options)

    def test_constructor_values_land_on_the_grid(self):
        e = self._fresh(voice1=4.4, level1_db=-6.1, detune_cents=13.0,
                        spread=0.33, mix=1.3, pitch=-2.2)
        for i in range(10):
            midi = e.get_macro(i)
            self.assertAlmostEqual(midi, round(midi), places=9)
        self.assertEqual(semis_of_midi(int(round(e.get_macro(1)))), 4)
        self.assertEqual(semis_of_midi(int(round(e.get_macro(PITCH)))), -2)
        self.assertAlmostEqual(e.macro(PITCH), -2.25, places=9)
        e.deinit()
        e = self._fresh(level2_db=-50.0)
        self.assertEqual(e.get_macro(LEVEL[1]), 0)
        e.deinit()

    def test_a_fresh_instance_reads_patch_0(self):
        e = self._fresh()
        self.assertEqual(tuple(int(round(e.get_macro(i)))
                               for i in range(10)),
                         Harmonizer.PATCHES[0][1])
        self.assertEqual(e.patch_index, 0)
        e.deinit()

    def test_the_patches(self):
        want = {0: ((4, 7, -12), (-6, -6, -9), 0, 0, 1),
                1: ((-12, -12, 0), (-3, -3, None), 14, 0.5, 1),
                2: ((0, 0, 0), (-6, -6, None), 14, 1, 1),
                3: ((5, 7, 12), (-9, -9, -12), 0, 0.5, 1),
                4: ((12, -12, 0), (-6, -6, None), 0, 0.5, 1),
                5: ((3, 7, 0), (-6, -6, -6), 0, 0.5, 2),
                6: ((4, 7, -12), (-6, -6, None), 0, 0, 1)}
        for patch, (voices, levels, detune, spread, mix) in want.items():
            v = Harmonizer.PATCHES[patch][1]
            self.assertEqual(semis_of_midi(v[PITCH]), 0)
            self.assertEqual(tuple(semis_of_midi(v[i]) for i in VOICE),
                             voices)
            for k in range(3):
                db = db_of_midi(v[LEVEL[k]])
                if levels[k] is None:
                    self.assertIsNone(db)
                else:
                    self.assertLess(abs(db - levels[k]), 0.2)
            self.assertLess(abs(cents_of_midi(v[DETUNE]) - detune), 0.1)
            self.assertLess(abs(v[SPREAD] / 127.0 - spread), 0.01)
            self.assertLess(abs(mix_of_midi(v[MIX]) - mix), 0.01)

    def test_the_lean_patch(self):
        lean = Harmonizer.PATCHES[6][1]
        full = Harmonizer.PATCHES[0][1]
        self.assertEqual(lean[:6], full[:6])
        self.assertEqual(lean[LEVEL[2]], 0)
        self.assertEqual(semis_of_midi(full[VOICE[2]]), -12)
        self.assertEqual(lean[7:], full[7:])

    def test_the_window(self):
        for ms, want in ((0.0, 5.0), (4.0, 5.0), (30.0, 30.0),
                         (61.0, 60.0), (float("nan"), 1024.0 / 48.0)):
            e = self._fresh(window_ms=ms)
            self.assertEqual(e.window_ms, want)
            e.set_macro(MIX, 127)
            e.reset()
            self.assertEqual(e.window_ms, want)
            e.deinit()

    def _material(self, rate, channels):
        return gauss(8192, channels, 6000.0, 7, lead=0)

    def test_mix_0_is_the_input(self):
        for rate in RATES:
            for channels in CHANNELS:
                values = gauss(8192, channels, 12000.0, 3, lead=0)
                y = render(Harmonizer, values, rate, channels,
                           macros=[(MIX, 0)])
                self.assertEqual(y, list(values))
                y = render(Harmonizer, values, rate, channels,
                           options={"mix": 0.0}, patch=None)
                self.assertEqual(y, list(values))

    def test_no_latency(self):
        for rate in (48000, 44100, 22050):
            for channels in CHANNELS:
                values = array("h", bytes(2 * 4096 * channels))
                for c in range(channels):
                    values[1000 * channels + c] = 20000
                y = render(Harmonizer, values, rate, channels,
                           macros=[(LEVEL[k], 0) for k in range(3)])
                first = min(i for i in range(len(y)) if y[i]) // channels
                self.assertEqual(first, 1000)
                e = self._fresh(rate, channels)
                self.assertEqual(e.latency_samples, 0)
                e.deinit()

    def test_the_tail(self):
        for rate in RATES:
            for channels in CHANNELS:
                for ms in T4_WINDOWS:
                    for patch in sorted(Harmonizer.PATCHES):
                        values = gauss(4096, channels, 4000.0, patch,
                                       lead=0)
                        feed = kc.feed(values, rate, channels)
                        e = Harmonizer(feed.port, sample_rate=rate,
                                       window_ms=ms)
                        e.program_change(patch)
                        tail = e.tail_samples
                        w = window_frames(ms, rate)
                        self.assertEqual(tail, w + crossfade(w) + BLOCK)
                        y = kc.samples(kc.render(e, 4096 + tail + 4096))
                        last = kc.last_nonzero_frame(y, channels)
                        self.assertLess(last, 4096 + tail, (rate, ms))
                        e.set_macro(MIX, 0)
                        self.assertEqual(e.tail_samples, 0)
                        e.set_macro(MIX, 64)
                        for k in range(3):
                            e.set_macro(LEVEL[k], 0)
                        self.assertEqual(e.tail_samples, 0)
                        e.deinit()

    def test_reset_renders_as_fresh(self):
        """After `reset()` the output is a fresh instance's, fed the same
        material from that point, byte for byte; at every patch and from
        Mix 0."""
        for rate in RATES:
            for channels in CHANNELS:
                for patch, start in ((0, None), (3, None), (5, 0)):
                    values = gauss(16384, channels, 3000.0, 11, lead=0)
                    cut = 24 * BLOCK
                    feed = kc.feed(values, rate, channels)
                    e = Harmonizer(feed.port, sample_rate=rate)
                    e.program_change(patch)
                    if start is not None:
                        e.set_macro(MIX, start)
                    kc.render(e, cut)
                    e.reset()
                    got = kc.samples(kc.render(e, 16384 - cut))
                    e.deinit()
                    rest = values[cut * channels:]
                    fresh = render(Harmonizer, rest, rate, channels)
                    self.assertEqual(list(got), fresh,
                                     (rate, channels, patch))

    def test_a_rack_reset_renders_as_fresh(self):
        """A Rack holding a Harmonizer built with options, its knobs moved
        and a patch loaded, renders after `reset()` what a freshly built
        rack does, fed the same material from that point, and reads the
        built knobs back."""
        Rack = audioeffects.Rack
        chain = ((Harmonizer, {"voice1": 3.0, "mix": 0.5,
                               "window_ms": 80.0}),)
        for rate in RATES:
            for channels in CHANNELS:
                values = gauss(16384, channels, 3000.0, 11, lead=0)
                cut = 24 * BLOCK
                rest = values[cut * channels:]
                fresh = Rack.create(kc.feed(rest, rate, channels).port,
                                    rate, chain=chain)
                try:
                    want = bytes(kc.render(fresh, 16384 - cut))
                finally:
                    fresh.deinit()
                rack = Rack.create(kc.feed(values, rate, channels).port,
                                   rate, chain=chain)
                try:
                    inner = rack.effects[0]
                    built = [inner.macro(i) for i in range(10)]
                    inner.program_change(3)
                    inner.set_macro(VOICE[0], 100)
                    inner.set_macro(MIX, 127)
                    kc.render(rack, cut)
                    rack.reset()
                    got = bytes(kc.render(rack, 16384 - cut))
                    self.assertEqual(
                        [inner.macro(i) for i in range(10)], built)
                finally:
                    rack.deinit()
                self.assertEqual(got, want, (rate, channels))

    def test_never_reads_the_tempo(self):
        calls = []

        def transport():
            calls.append(1)
            return (True, 0.0, 140.0, 4, 4)
        feed = kc.feed(array("h", bytes(4 * BLOCK)), 48000, 1)
        e = Harmonizer.create(feed.port, 48000, transport=transport)
        for i in range(10):
            e.set_macro(i, 100)
        e.transport_changed()
        kc.render(e, 1024)
        e.reset()
        self.assertEqual(calls, [])
        self.assertEqual(e.capabilities, ())
        e.deinit()

    def test_peaks_round_off_above_the_knee(self):
        for rate in RATES:
            for amp in (27000, 32000):
                values = array("h", [int(amp * math.sin(
                    2.0 * math.pi * 440.0 * i / rate)) for i in range(8192)])
                y = render(Harmonizer, values, rate, 1, options={
                    "voice1": 0.0, "level1_db": 0.0, "level2_db": -99.0,
                    "level3_db": -99.0, "mix": 2.0})
                w = window_frames(1024.0 / 48.0, rate)
                lag = crossfade(w)
                if amp == 27000:
                    self.assertEqual(y[lag + 64:8192],
                                     list(values[64:8192 - lag]))
                else:
                    peak = max(abs(v) for v in y)
                    self.assertTrue(28000 < peak < 28600, peak)
                    self.assertEqual(round(20.0 * math.log10(
                        28000 / 32768.0), 1), -1.4)

    def test_patch_0_headroom(self):
        v = Harmonizer.PATCHES[0][1]
        g_dry, g_wet = gains(mix_of_midi(v[MIX]))
        total = g_dry + sum(g_wet * 10.0 ** (db_of_midi(v[LEVEL[k]]) / 20.0)
                            for k in range(3))
        bound = 32767.0 / total
        self.assertTrue(13900 <= bound < 14000, bound)
        self.assertEqual(round(20.0 * math.log10(13900 / 32768.0), 1), -7.4)
        for rate in RATES:
            for channels in CHANNELS:
                for material in (kc.square(16384, channels, 13900, 200),
                                 kc.clicks(16384, channels, 13900),
                                 kc.noise(16384, channels, 13900)):
                    y = render(Harmonizer, material, rate, channels)
                    self.assertLess(max(abs(s) for s in y), 32767)

    def test_the_stated_ceiling_covers_every_setting(self):
        """At `INPUT_CEILING_DBFS` the loudest settings reach no rail, not
        only the kit's own: all three Levels at 0 dB at Mix 1 sum to 4.0
        times the input, and patch 1 with Level 3 at 0 dB to 3.44."""
        peak = int(32767 * 10.0 ** (Harmonizer.INPUT_CEILING_DBFS / 20.0)
                   + 0.5)
        cells = (
            (None, [(LEVEL[k], 127) for k in range(3)] + [(MIX, 64)]),
            (1, [(LEVEL[2], 127)]),
        )
        for rate in RATES:
            for channels in CHANNELS:
                values = kc.square(16384, channels, peak, rate // 100)
                for patch, macros in cells:
                    y = render(Harmonizer, values, rate, channels,
                               patch=patch, macros=macros)
                    on = sum(1 for s in y if s >= 32767 or s <= -32767)
                    self.assertEqual(
                        on, 0, (rate, channels, patch, peak, max(y)))


CLAIMS = (
    ("Three pitch shifters, each a fixed interval from your note, blended "
     "under the dry: the rig of three Eventide H910s played from one "
     "keyboard, so one singer is three-part harmony.",
     ("T1Independent.test_the_sum_of_the_solos",
      "T2Intervals.test_pitch_moves_every_voice")),
    ("Voice 1 to Voice 3 set each voice's interval in whole "
     "semitones, and Pitch moves all three together.",
     ("T2Intervals.test_every_voice_1_position",
      "T2Intervals.test_pitch_moves_every_voice")),
    ("Level 1 to Level 3 set each voice's level, and the bottom step "
     "turns the voice off.",
     ("T5Balance.test_level", "T6Return.test_the_return",
      "TheSurface.test_the_tail")),
    ("Detune pulls voice 1 down and voice 2 up.",
     ("T3SteadyDetune.test_every_eighth_position",)),
    ("Spread pans voice 1 left and voice 2 right; the dry and voice 3 stay "
     "in the centre.",
     "T5Balance.test_spread"),
    ("Mix holds the dry at unity up to 1 while the voices rise to "
     "their Levels; from 1 to 2 the dry fades, and at 2 the voices "
     "play alone.",
     ("T5Balance.test_mix",)),
    ("Constructor values land on the nearest of each knob's 128 steps; "
     "`window_ms`, 5 to 60 ms (21.33 by default), is fixed for good.",
     ("TheSurface.test_constructor_values_land_on_the_grid",
      "TheSurface.test_a_fresh_instance_reads_patch_0",
      "TheSurface.test_the_window")),
    ("Each voice is its own machine: turning one on or off never changes "
     "the dry or the other voices.",
     ("T1Independent.test_the_sum_of_the_solos",
      "T7TurnOff.test_off_plays_nothing")),
    ("Each voice sits on the closest pitch its shifter can make: within 3.4 "
     "cents of its interval from unison up, 6.8 cents down to an octave "
     "below and 13.7 cents below that.",
     ("T2Intervals.test_within_half_a_step",
      "T2Intervals.test_every_voice_1_position",
      "T2Intervals.test_pitch_moves_every_voice",
      "T2Intervals.test_every_patch")),
    ("So Detune moves in steps of about 7 cents near unison, and voices 1 "
     "and 2 sit evenly apart only to within a step.",
     ("T2Intervals.test_detune_moves_in_steps_of_about_7_cents_near_unison",
      "T3SteadyDetune.test_every_eighth_position")),
    ("Detune is a steady offset, not a chorus: a voice holds its pitch.",
     "T3SteadyDetune.test_every_eighth_position"),
    ("Each voice glitches as it splices, more often the further it is "
     "shifted and the shorter the window: at the default window a fifth up "
     "splices every 43 ms, at any sample rate, where the first channel is "
     "silent.",
     ("T4Window.test_the_gap",
      "T4Window.test_a_fifth_up_splices_every_43_ms")),
    ("Where it is not, each splice moves by up to a fiftieth of a second to "
     "land in phase, so the splices come sooner.",
     "T4Window.test_a_splice_moves_toward_the_match"),
    ("A voice at exact unison never splices: it is a fixed short delay, and "
     "it combs with the dry.",
     "T4Window.test_unison_never_splices"),
    ("A voice you turn back on starts from silence, not with a scrap of "
     "what it played before.",
     "T6Return.test_the_return"),
    ("It moves notes by fixed intervals and does not listen for the key.",
     ("T2Intervals.test_every_voice_1_position",
      "T2Intervals.test_every_patch")),
    ("Each voice rounds off peaks above about -1.4 dBFS.",
     "TheSurface.test_peaks_round_off_above_the_knee"),
    ("The voices add to the dry: at patch 0 an input that peaks at or below "
     "13 900 (-7.4 dBFS) cannot reach full scale.",
     "TheSurface.test_patch_0_headroom"),
    ("Patch 6 is patch 0 without the octave below, for a board that cannot "
     "run three voices in time.",
     ("TheSurface.test_the_lean_patch", "TheSurface.test_the_patches")),
    ("On a mono source Spread does nothing.",
     "T5Balance.test_mono_spread_does_nothing"),
    ("An interval move leaves each voice's splice where it was.",
     "DECLARED:Harmonizer,E4-,P4"),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "DECLARED:Harmonizer,E5-,P5"),
    ("At Mix 0 the output is the input, byte for byte.",
     "TheSurface.test_mix_0_is_the_input"),
    ("There is no latency: the dry is a wire, and each shifted voice trails "
     "it by between the crossfade, a sixteenth of the window, and the whole "
     "window.",
     ("TheSurface.test_no_latency",
      "T4Window.test_a_shifted_voice_trails_by_the_crossfade_to_the_window")),
    ("`tail_samples` covers the window, the crossfade and one block, and is "
     "0 at Mix 0 or with every voice off.",
     "TheSurface.test_the_tail"),
    ("`reset()` empties the three lines, starts their splices where a new "
     "instance's start, and returns to patch 0.",
     "TheSurface.test_reset_renders_as_fresh"),
    ("On CircuitPython's own pitch shifter a reset does not restart the "
     "splices.",
     ("DECLARED:Harmonizer,E10-reset,P4,circuitpython",
      "DECLARED:Harmonizer,E10-mix0,P4,circuitpython")),
    ("The class never reads the host's tempo.",
     "TheSurface.test_never_reads_the_tempo"),
)


if __name__ == "__main__" and unittest is not None:
    unittest.main()
