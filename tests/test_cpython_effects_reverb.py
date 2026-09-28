"""`Reverb`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Reverb.md`; its
demonstrated Tier 2 rows are T1-T3 and T7-T11 (T4-T6 are the spring's and
park with it). Each row here is the measurement at one of its claimed
cells, the same measurement shown red on a fault of the same kind at the
constructor defaults, that fault shown unreachable from every macro
position and shipped patch, and the measurement shown red on the class
built as a wire. The measurements are the dossier's (App. E as Station A
restated them); the grids over Size, rate and channel count live in the
evidence pack, not in this file.
"""

import math
import os
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                            # noqa: E402
import kit_faults                                           # noqa: E402
import kit_probes as probes                                 # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import rebuilt                            # noqa: E402
from audioeffects.rebuilt import reverb as rv               # noqa: E402

VENDOR = "PyDevices"

Reverb = rv.Reverb
RATE = 48000
SEEDS = tuple(range(7, 15))
BURST_S = 2.0
NOISE_RMS = 8000.0

#: Every shipped patch in engineering units, the dossier's section 6 table.
PATCH_SETTINGS = (
    ("Steel Plate", dict(character="plate", decay=2.4, size=1.0,
                         predelay_ms=0.0, diffusion=0.75, damping_hz=1000.0,
                         bandwidth_hz=12000.0, low_cut_hz=40.0,
                         mod_depth_ms=0.27, mod_rate_hz=1.0, width=1.0,
                         tone_db=0.0, mix=0.35)),
    ("Short Plate", dict(character="plate", decay=1.2, size=1.0,
                         predelay_ms=0.0, diffusion=0.75, damping_hz=1500.0,
                         bandwidth_hz=14000.0, low_cut_hz=60.0,
                         mod_depth_ms=0.2, mod_rate_hz=1.2, width=0.9,
                         tone_db=2.0, mix=0.30)),
    ("Damped Plate", dict(character="plate", decay=1.0, size=1.25,
                          predelay_ms=0.0, diffusion=0.75, damping_hz=700.0,
                          bandwidth_hz=8000.0, low_cut_hz=80.0,
                          mod_depth_ms=0.2, mod_rate_hz=1.0, width=0.8,
                          tone_db=-3.0, mix=0.30)),
    ("Bass-Free Plate", dict(character="plate", decay=1.8, size=1.0,
                             predelay_ms=0.0, diffusion=0.75,
                             damping_hz=1000.0, bandwidth_hz=10000.0,
                             low_cut_hz=360.0, mod_depth_ms=0.27,
                             mod_rate_hz=1.0, width=0.8, tone_db=2.0,
                             mix=0.40)),
    ("Small Room", dict(character="room", decay=0.45, size=0.7,
                        predelay_ms=2.0, diffusion=0.6, damping_hz=6000.0,
                        bandwidth_hz=10000.0, low_cut_hz=60.0,
                        mod_depth_ms=0.2, mod_rate_hz=0.8, width=0.8,
                        tone_db=0.0, mix=0.25)),
    ("Live Room", dict(character="room", decay=1.0, size=1.25,
                       predelay_ms=4.0, diffusion=0.6, damping_hz=8000.0,
                       bandwidth_hz=12000.0, low_cut_hz=50.0,
                       mod_depth_ms=0.3, mod_rate_hz=0.7, width=0.9,
                       tone_db=2.0, mix=0.30)),
    ("Concert Hall", dict(character="hall", decay=3.2, size=1.25,
                          predelay_ms=25.0, diffusion=0.7, damping_hz=5000.0,
                          bandwidth_hz=9000.0, low_cut_hz=45.0,
                          mod_depth_ms=0.5, mod_rate_hz=0.6, width=1.0,
                          tone_db=0.0, mix=0.35)),
    ("Dark Chamber", dict(character="chamber", decay=1.8, size=1.0,
                          predelay_ms=8.0, diffusion=0.7, damping_hz=2500.0,
                          bandwidth_hz=6000.0, low_cut_hz=70.0,
                          mod_depth_ms=0.3, mod_rate_hz=0.9, width=0.8,
                          tone_db=-4.0, mix=0.32)),
    ("Bright Chamber", dict(character="chamber", decay=1.6, size=1.0,
                            predelay_ms=8.0, diffusion=0.7,
                            damping_hz=12000.0, bandwidth_hz=16000.0,
                            low_cut_hz=90.0, mod_depth_ms=0.3,
                            mod_rate_hz=0.9, width=0.8, tone_db=4.0,
                            mix=0.32)),
    ("Slow Bloom", dict(character="hall", decay=4.5, size=1.5,
                        predelay_ms=40.0, diffusion=0.8, damping_hz=4000.0,
                        bandwidth_hz=8000.0, low_cut_hz=45.0,
                        mod_depth_ms=1.0, mod_rate_hz=0.4, width=1.0,
                        tone_db=0.0, mix=0.45)),
)
SETTINGS = dict(PATCH_SETTINGS)

#: Each character's reference patch (T11).
REFERENCE = {"plate": "Steel Plate", "room": "Live Room",
             "chamber": "Dark Chamber", "hall": "Concert Hall"}

#: Clean measurements shared between a row's test and its null build's
#: control, so the eight-seed rows render once.
_MEMO = {}


# -- planted faults ----------------------------------------------------------

def _cut_with(sample_rate, index, size, ratios):
    lines = rv.line_set(index, size, sample_rate, ratios)
    return lines, rv.tap_table(index, size, sample_rate, ratios, lines)


class DattorroDiffuserPlate(Reverb):
    """T1: the plate on Dattorro's published input diffusers (ratio 1.0,
    not the class's 0.3)."""

    NAME = 'Reverb'

    def _cut(self, index, size):
        if index != rv.PLATE:
            return Reverb._cut(self, index, size)
        ratios = (1.0, 1.0, 1.0, 1.0) + rv.RATIOS[rv.PLATE][4:]
        return _cut_with(self._sample_rate, index, size, ratios)


class InvertedCut(Reverb):
    """T2: every line and tap cut with the rate ratio upside down,
    round(n x 29 761 / fs x Size x r)."""

    NAME = 'Reverb'

    def _cut(self, index, size):
        ratios = rv.RATIOS[index]
        k = rv.REF_RATE / self._sample_rate
        lines = [max(rv.MIN_LINE, int(round(n * k * size * r)))
                 for n, r in zip(rv.DATTORRO_LINES, ratios)]
        taps = []
        for ch, line, off, gain in rv.DATTORRO_TAPS:
            o = min(int(round(off * k * size * ratios[line])),
                    lines[line] - 1)
            taps.extend((ch, line, o, gain))
        return lines, taps


class FlatDamper(Reverb):
    """T3: the plate's corner held at the Damping value at every Decay (the
    damper law off; the Decay law still compensates 500 Hz)."""

    NAME = 'Reverb'

    def _loop_hz(self, index, decay_s, damping):
        return self._hz(damping)


class LowCutRadians(Reverb):
    """T7 wet: Low Cut handed divided by 2 pi (a rad/s slip)."""

    NAME = 'Reverb'

    def _low_cut_hz(self, value):
        return self._hz(value / (2.0 * math.pi))


class PlateDiffuserRooms(Reverb):
    """T8: room, chamber and hall on the plate's input diffusers."""

    NAME = 'Reverb'

    def _cut(self, index, size):
        if index == rv.PLATE:
            return Reverb._cut(self, index, size)
        ratios = rv.RATIOS[rv.PLATE][:4] + rv.RATIOS[index][4:]
        return _cut_with(self._sample_rate, index, size, ratios)


class HallOnRoomLines(Reverb):
    """T9 (M8's own): the hall built on the room's lines and taps."""

    NAME = 'Reverb'

    def _cut(self, index, size):
        if index == rv.HALL:
            return Reverb._cut(self, rv.ROOM, size)
        return Reverb._cut(self, index, size)


class RateReciprocal(Reverb):
    """T10 on-clause: Mod Rate handed as its reciprocal in ms."""

    NAME = 'Reverb'

    def _mod_rate_hz(self, value):
        return 1000.0 / value


class ToneDetentZero(Reverb):
    """Tier 1 silence: Tone's centre detent handed as exact 0 dB, which
    freezes the Tank's tilt one-pole (`audiodsp_tank.c:596-602`)."""

    NAME = 'Reverb'

    def _tone_db(self, value):
        return value


def depth_ceiling_ms(lines, sample_rate):
    """The node's own Mod Depth ceiling, half the shorter modulated line
    less a frame (`audiodsp_tank.c:328-336`)."""
    return min(lines[4] - 2, lines[8] - 2) * 0.5 * 1000.0 / sample_rate


class DepthMirrored(Reverb):
    """T10 off-clause: Mod Depth handed mirrored about the node's ceiling."""

    NAME = 'Reverb'

    def _mod_depth_ms(self, value, lines):
        return depth_ceiling_ms(lines, self._sample_rate) - value


class OneMultiply(Reverb):
    """T11: the law counting one decay multiply per half pass, not the
    node's two (`audiodsp_tank.c:537-538`, `:552`)."""

    NAME = 'Reverb'

    def _decay(self, index, lines, decay_s, loop_hz):
        d, capped, t_lf = Reverb._decay(self, index, lines, decay_s, loop_hz)
        return d * d, capped, 0.5 * t_lf


class LongDiffusers(Reverb):
    """The floor knee (dossier section 8.9): every character's four input
    diffusers at 1.5 x its own, the direction Station A tried and dropped
    because longer diffusers ring on their own and lift the floor under
    Decay (App. A8.8)."""

    NAME = 'Reverb'

    def _cut(self, index, size):
        ratios = tuple(1.5 * r for r in rv.RATIOS[index][:4]) + \
            rv.RATIOS[index][4:]
        return _cut_with(self._sample_rate, index, size, ratios)


def capped_law(kappa, lines, sample_rate, decay_s, loop_hz, cap):
    """The dossier's section 4 Decay law with its low-frequency cap at
    `cap` x Decay, written out here rather than read off the class."""
    a, b = rv.half_periods(lines)
    p = 0.5 * (a + b)
    fs = float(sample_rate)
    mag = rv.one_pole_mag(loop_hz, 500.0, fs)
    d = 10.0 ** (-3.0 * kappa * p / (2.0 * decay_s * fs)) / math.sqrt(mag)
    ceiling = 10.0 ** (-3.0 * kappa * p / (2.0 * cap * decay_s * fs))
    capped = d > ceiling
    d = min(d, ceiling, 0.999)
    return d, capped, -3.0 * kappa * p / (2.0 * fs * math.log10(d))


class LooseCeiling(Reverb):
    """The ceiling knee (dossier section 8.9): the law's low-frequency cap
    at 2 x Decay instead of 1.5 x, so every ceiling knee moves up."""

    NAME = 'Reverb'

    def _decay(self, index, lines, decay_s, loop_hz):
        return capped_law(rv.KAPPA[index], lines, self._sample_rate, decay_s,
                          loop_hz, 2.0)


# -- probes and rendering ----------------------------------------------------

def interleave(mono, channels, frames):
    """`mono` (int16) on every channel, padded with silence to `frames`:
    the Tank advances only for frames that arrive."""
    x = np.zeros(frames, dtype=np.int16)
    n = min(len(mono), frames)
    x[:n] = np.asarray(mono[:n], dtype=np.int16)
    return array("h", np.repeat(x, channels).tobytes())


def make(cls, name=None, rate=RATE, channels=2, mono=(), frames=512,
         **override):
    settings = dict(SETTINGS[name]) if name else {}
    settings.update(override)
    src = probes.ArraySource(interleave(np.asarray(mono), channels, frames),
                             rate=rate, channels=channels, block=256)
    return cls(src, sample_rate=rate, **settings)


def render(effect, frames):
    channels = effect.channel_count
    out = array("h")
    while len(out) < frames * channels:
        out.extend(memoryview(bytes(
            audiocore.get_buffer(effect.output)[1])).cast("h"))
    return np.array(out[:frames * channels], dtype=np.int32).reshape(
        -1, channels)


def noise_burst(rate, seed=7, rms=NOISE_RMS, seconds=BURST_S):
    rng = np.random.RandomState(seed)
    n = int(seconds * rate)
    return np.round(rng.uniform(-1, 1, n) * rms * math.sqrt(3)).astype(
        np.int16)


def impulse(level=30000):
    return np.array([level], dtype=np.int16)


def band(y, rate, centre, fraction=3):
    """Zero-phase fractional-octave band (FFT domain, raised-cosine skirts
    of a sixth of the band either side), the dossier's M3 filter."""
    n = len(y)
    size = 1 << int(math.ceil(math.log2(n + 1)))
    spec = np.fft.rfft(y.astype(np.float64), size)
    f = np.fft.rfftfreq(size, 1.0 / rate)
    lo = centre * 2 ** (-0.5 / fraction)
    hi = centre * 2 ** (0.5 / fraction)
    skirt = 2 ** (1.0 / (6 * fraction))
    g = np.zeros_like(f)
    g[(f >= lo) & (f <= hi)] = 1.0
    lower = (f >= lo / skirt) & (f < lo)
    g[lower] = 0.5 - 0.5 * np.cos(np.pi * np.log(f[lower] / (lo / skirt))
                                  / np.log(skirt))
    upper = (f > hi) & (f <= hi * skirt)
    g[upper] = 0.5 + 0.5 * np.cos(np.pi * np.log(f[upper] / hi)
                                  / np.log(skirt))
    return np.fft.irfft(spec * g, size)[:n]


def t60_slope(x, rate, hi_db=-5.0, lo_db=-35.0, win_ms=10.0):
    """M3: least-squares slope of the 10 ms log envelope over -5...-35 dB
    re its maximum, extrapolated to -60 dB; None where it cannot be fitted.
    Never a -60 dB crossing."""
    w = int(round(win_ms * rate / 1000.0))
    m = len(x) // w
    env = np.sqrt(np.mean(x[:m * w].reshape(m, w) ** 2, axis=1))
    env = 20.0 * np.log10(np.maximum(env, 1e-12))
    k = int(np.argmax(env))
    rel = env - env[k]
    after = rel[k:]
    below_hi = np.nonzero(after <= hi_db)[0]
    above_lo = np.nonzero(after >= lo_db)[0]
    if not len(below_hi) or not len(above_lo):
        return None
    s = k + int(below_hi[0])
    e = k + int(above_lo[-1])
    if e - s < 3:
        return None
    t = np.arange(s, e + 1) * w / rate
    slope, _ = np.polyfit(t, rel[s:e + 1], 1)
    return -60.0 / slope if slope < 0 else None


def band_t60s(cls, name, seed, centres, rate=RATE, channels=2, **override):
    """T60 per band by M3 on interrupted noise: 2 s of uniform noise at
    8 000 LSB RMS then silence, the mono sum, Mix 2."""
    settings = dict(SETTINGS[name])
    settings.update(override)
    t = settings["decay"]
    frames = int((BURST_S + 1.3 * max(t, 1.0) + 0.8) * rate)
    effect = make(cls, name, rate, channels, noise_burst(rate, seed), frames,
                  **dict(override, mix=2.0))
    try:
        y = render(effect, frames)
    finally:
        effect.deinit()
    m = y.astype(np.float64).sum(axis=1)
    cut = int(BURST_S * rate)
    return [t60_slope(band(m, rate, fc)[cut:], rate) for fc in centres]


def m1_profile(y, rate, onset, win_ms=10.0, floor_db=-40.0, upto_ms=260.0):
    """M1: local maxima of |y| per 10 ms window above -40 dB of the
    window's own RMS, windows from the channel's first non-zero sample."""
    a = np.abs(y.astype(np.float64))
    w = int(round(win_ms * rate / 1000.0))
    counts = []
    k = 0
    while True:
        s = onset + k * w
        e = s + w
        if (k * win_ms) > upto_ms or e + 1 >= len(a):
            break
        seg = a[max(0, s - 1):e + 1]
        body = seg[1:-1]
        rms = math.sqrt(float(np.mean(body ** 2))) if len(body) else 0.0
        if rms == 0.0:
            counts.append(0)
        else:
            thr = rms * 10 ** (floor_db / 20.0)
            peaks = (body > seg[:-2]) & (body >= seg[2:]) & (body > thr)
            counts.append(int(np.count_nonzero(peaks)))
        k += 1
    return counts


def density(cls, name, rate=RATE, channels=2, **override):
    """Per channel (count at 20 ms, count at 200 ms, lowest from 20 to
    200 ms) of M1 on an impulse of 30 000, Mix 2, 500 ms."""
    frames = int(0.5 * rate)
    effect = make(cls, name, rate, channels, impulse(), frames,
                  **dict(override, mix=2.0))
    try:
        y = render(effect, frames)
    finally:
        effect.deinit()
    out = []
    for c in range(channels):
        nz = np.nonzero(y[:, c])[0]
        if not len(nz):
            out.append((0, 0, 0))
            continue
        counts = m1_profile(y[:, c], rate, int(nz[0]))
        out.append((counts[2], counts[20], min(counts[2:21])))
    return out


def prominences(db):
    n = len(db)
    peaks = np.nonzero((db[1:-1] > db[:-2]) & (db[1:-1] >= db[2:]))[0] + 1
    out = {}
    for p in peaks:
        h = db[p]
        i = p - 1
        low_l = h
        while i >= 0 and db[i] <= h:
            low_l = min(low_l, db[i])
            i -= 1
        j = p + 1
        low_r = h
        while j < n and db[j] <= h:
            low_r = min(low_r, db[j])
            j += 1
        out[p] = h - max(low_l, low_r)
    return out


def modal_counts(cls, name="Steel Plate", rate=RATE, channels=2,
                 **override):
    """M2 restated: Decay 10 s, Mod Depth 0, Damping 16 kHz, the mono sum's
    8 s segment from 0.2 s after a 2 s noise burst, one Hann FFT; >= 6 dB
    prominence maxima per Hz in 200-400 Hz and 2-4 kHz."""
    frames = int((BURST_S + 8.3) * rate)
    effect = make(cls, name, rate, channels, noise_burst(rate), frames,
                  **dict(dict(decay=10.0, mod_depth_ms=0.0,
                              damping_hz=16000.0), mix=2.0, **override))
    try:
        y = render(effect, frames)
    finally:
        effect.deinit()
    seg = y.astype(np.float64).sum(axis=1)[int((BURST_S + 0.2) * rate):]
    n = 8 * rate
    spec = np.abs(np.fft.rfft(seg[:n] * np.hanning(n), n))
    db = 20 * np.log10(np.maximum(spec, 1e-9))
    f = np.fft.rfftfreq(n, 1.0 / rate)
    i0 = int(np.searchsorted(f, 150.0))
    i1 = int(np.searchsorted(f, 4200.0))
    sub, fsub = db[i0:i1], f[i0:i1]
    prom = prominences(sub)
    return [sum(1 for p, v in prom.items() if lo <= fsub[p] <= hi
                and v >= 6.0) / (hi - lo)
            for lo, hi in ((200.0, 400.0), (2000.0, 4000.0))]


def declared_density(character, size, rate=RATE):
    """The class's declared modal density: lines 4-11 of the character's
    own table at `size`, over fs (not the lines the Tank was handed)."""
    lines = rv.line_set(rv.CHARACTERS.index(character), size, rate)
    return sum(lines[4:12]) / float(rate)


def blackman_harris(n):
    k = np.arange(n) / (n - 1.0)
    return (0.35875 - 0.48829 * np.cos(2 * np.pi * k)
            + 0.14128 * np.cos(4 * np.pi * k)
            - 0.01168 * np.cos(6 * np.pi * k))


def sidebands_db(cls, name, hz, window_rate, rate=RATE, channels=2,
                 **override):
    """M6 restated for T10: a sine at 8 000 LSB, Mix 2, the mono sum; 4 s
    to settle, then L = max(6, 8 / rate) s under Blackman-Harris; the
    energy 4/L-20 Hz either side over the energy within 4/L Hz, in dB."""
    length = max(6.0, 8.0 / window_rate)
    n_total = int((4.0 + length) * rate)
    x = np.round(8000 * np.sin(2 * np.pi * hz * np.arange(n_total) / rate))
    effect = make(cls, name, rate, channels, x.astype(np.int16), n_total,
                  **dict(override, mix=2.0))
    try:
        y = render(effect, n_total)
    finally:
        effect.deinit()
    m = y.astype(np.float64).sum(axis=1)[n_total - int(length * rate):]
    p = np.abs(np.fft.rfft(m * blackman_harris(len(m)))) ** 2
    f = np.fft.rfftfreq(len(m), 1.0 / rate)
    d = np.abs(f - hz)
    edge = 4.0 / length
    carrier = p[d <= edge].sum()
    side = p[(d > edge) & (d <= 20.0)].sum()
    return 10 * math.log10(side / carrier) if side > 0 else -300.0


def twelfth_bands(lo=15.0, hi=4000.0):
    edges = []
    f = lo
    while f < hi:
        edges.append(f)
        f *= 2 ** (1.0 / 12)
    return [(a, b, math.sqrt(a * b)) for a, b in zip(edges, edges[1:])]


def band_power(x, rate, bands):
    n = 1 << int(math.ceil(math.log2(len(x))))
    p = np.abs(np.fft.rfft(x, n)) ** 2
    f = np.fft.rfftfreq(n, 1.0 / rate)
    return np.array([p[(f >= a) & (f < b)].sum() for a, b, _ in bands])


def at_hz(centres, db, f):
    return float(np.interp(math.log(f), np.log(centres), db))


def corner_hz(centres, db):
    target = at_hz(centres, db, 2000.0) - 3.0
    for i in range(len(db) - 1, 0, -1):
        if db[i - 1] < target <= db[i]:
            a, b = math.log(centres[i - 1]), math.log(centres[i])
            t = (target - db[i - 1]) / (db[i] - db[i - 1])
            return math.exp(a + t * (b - a))
    return None


def wet_sum(cls, name, rate, channels, reference=False, **override):
    frames = int(3.0 * rate)
    effect = make(cls, name, rate, channels, noise_burst(rate), frames,
                  **dict(override, mix=2.0))
    if reference and hasattr(effect, "_tank") and effect._tank is not None:
        # Not a class state (the macro stops at 20 Hz): the test sets the
        # class's own Tank's low_cut_hz to 0, the only difference.
        effect._tank.set(low_cut_hz=0.0)
    try:
        return render(effect, frames).astype(np.float64).sum(axis=1)
    finally:
        effect.deinit()


def low_cut_readings(cls, name="Bass-Free Plate", rate=RATE, channels=2,
                     **override):
    """M7 restated: the wet at Low Cut over the wet with the Tank's Low Cut
    at 0, 1/12-octave bands. (level at 362 Hz re 2 kHz, slope 90-180 Hz,
    1 kHz over 90 Hz, the -3 dB corner)."""
    bands = twelfth_bands()
    centres = np.array([c for _, _, c in bands])
    cut = band_power(wet_sum(cls, name, rate, channels, **override), rate,
                     bands)
    ref = band_power(wet_sum(cls, name, rate, channels, reference=True,
                             **override), rate, bands)
    db = 10 * np.log10(np.maximum(cut, 1e-30) / np.maximum(ref, 1e-30))
    return (at_hz(centres, db, 362.0) - at_hz(centres, db, 2000.0),
            at_hz(centres, db, 180.0) - at_hz(centres, db, 90.0),
            at_hz(centres, db, 1000.0) - at_hz(centres, db, 90.0),
            corner_hz(centres, db))


def low_cut_green(readings, low_cut):
    level, slope, depth, corner = readings
    return (-4.0 <= level <= -2.0 and 5.0 <= slope <= 7.0 and depth >= 11.0
            and corner is not None and abs(corner / low_cut - 1.0) <= 0.10)


def dry_deviation(name, mix, rate=RATE, channels=2, fault=False):
    """T7's dry clause: the output less min(Mix, 1) x the wet-only render,
    against the source x min(1, 2 - Mix), 1/12-octave bands over
    20 Hz-1 kHz, at 4 000 LSB RMS. `fault` moves the Low Cut into the dry
    path, emulated as the same one-pole on the source (the seed's plant)."""
    rng = np.random.RandomState(11)
    n = 2 * rate
    x = np.round(rng.uniform(-1, 1, n) * 4000.0 * math.sqrt(3)).astype(
        np.int16)
    effect = make(Reverb, name, rate, channels, x, n, mix=mix)
    out = render(effect, n).astype(np.float64)
    effect.deinit()
    effect = make(Reverb, name, rate, channels, x, n, mix=2.0)
    wet = render(effect, n).astype(np.float64)
    effect.deinit()
    dry = out - min(mix, 1.0) * wet
    if fault:
        a = 1.0 - math.exp(-2 * math.pi * SETTINGS[name]["low_cut_hz"] / rate)
        lp = 0.0
        hp = np.empty(n)
        for i in range(n):
            lp += a * (float(x[i]) - lp)
            hp[i] = float(x[i]) - lp
        dry = np.repeat(hp, channels).reshape(-1, channels)
    bands = twelfth_bands(18.0, 1100.0)
    level = min(1.0, 2.0 - mix)
    src = band_power(x.astype(np.float64) * level, rate, bands)
    d = band_power(dry[:, 0], rate, bands)
    dev = 10 * np.log10(d / src)
    sel = [i for i, (_, _, c) in enumerate(bands) if 20.0 <= c <= 1000.0]
    return float(np.max(np.abs(dev[sel])))


def first_arrival_ms(cls, name, rate=RATE, channels=2):
    """T9: the earlier channel's first non-zero wet sample of an impulse of
    30 000, less int(Predelay x fs / 1000) frames, in ms."""
    frames = int(0.2 * rate)
    effect = make(cls, name, rate, channels, impulse(), frames, mix=2.0)
    try:
        y = render(effect, frames)
    finally:
        effect.deinit()
    firsts = [np.nonzero(y[:, c])[0] for c in range(channels)]
    firsts = [int(f[0]) for f in firsts if len(f)]
    if not firsts:
        return None
    pre = int(SETTINGS[name]["predelay_ms"] * rate / 1000.0)
    return (min(firsts) - pre) * 1000.0 / rate


def silent_build(cls, **options):
    src = probes.ArraySource(array("h", [0] * 1024), rate=RATE, channels=2)
    return cls(src, sample_rate=RATE, **options)


def reach(faulted, reading, **options):
    return kit_faults.fault_reachability(
        Reverb, faulted, reading, lambda cls: silent_build(cls, **options))


#: 13 macros x 17 grid positions, plus the 10 patches.
WALK = 13 * 17 + 10


def handed_cut(effect):
    return (effect._index, tuple(effect._lines))


# -- the surface -------------------------------------------------------------

class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        self.assertIs(rebuilt.module_class("Reverb"), Reverb)
        self.assertEqual(Reverb.MACRO_LABELS, (
            "Character", "Decay", "Size", "Predelay", "Diffusion",
            "Damping", "Bandwidth", "Low Cut", "Mod Depth", "Mod Rate",
            "Width", "Tone", "Mix"))
        self.assertEqual(Reverb.MACRO_MODES[rv.TONE_I], "BIPOLAR")
        self.assertEqual(len(Reverb.PATCHES), 10)
        self.assertEqual(Reverb.CAPABILITIES, ())
        self.assertEqual(Reverb.LATENCY_SAMPLES, 0)
        self.assertEqual(Reverb.TIER, _component.AUDIODSP)
        self.assertEqual(Reverb.REQUIRES, ("audioverb",))
        effect = silent_build(Reverb)
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(rv.MIX_I, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(6)
        self.assertEqual(effect.patch_index, 6)

    def test_patches_are_the_dossier_settings_on_the_grid(self):
        spans = Reverb._MACRO_RANGES
        keys = ("decay", "size", "predelay_ms", "diffusion", "damping_hz",
                "bandwidth_hz", "low_cut_hz", "mod_depth_ms", "mod_rate_hz",
                "width", "tone_db", "mix")
        for index, (name, settings) in enumerate(PATCH_SETTINGS):
            label, grid = Reverb.PATCHES[index]
            self.assertEqual(label, name)
            expected = [rv.CHARACTER_MIDI[
                rv.CHARACTERS.index(settings["character"])]]
            for macro, key in enumerate(keys, start=1):
                expected.append(_component.macro_of(
                    spans[macro], settings[key], Reverb.MACRO_MODES[macro]))
            self.assertEqual(tuple(expected), grid, name)

    def test_patch_read_backs(self):
        # dossier App. F: what the grid reads back.
        effect = silent_build(Reverb)
        effect.program_change(6)
        self.assertEqual(effect._index, rv.HALL)
        self.assertAlmostEqual(effect.macro(rv.DECAY_I), 3.224, places=3)
        self.assertAlmostEqual(effect.macro(rv.SIZE_I), 1.248, places=3)
        self.assertAlmostEqual(effect.macro(rv.PREDELAY_I), 25.2, places=1)
        effect.program_change(0)
        self.assertEqual(effect._index, rv.PLATE)
        self.assertAlmostEqual(effect.macro(rv.DECAY_I), 2.379, places=3)
        self.assertAlmostEqual(effect.macro(rv.DAMPING_I), 989.1, places=1)
        self.assertEqual(effect.macro(rv.TONE_I), 0.0)
        for index, zone in ((4, rv.ROOM), (7, rv.CHAMBER), (9, rv.HALL)):
            effect.program_change(index)
            self.assertEqual(effect._index, zone)

    def test_patch_0_is_the_constructor_grid(self):
        effect = silent_build(Reverb)
        for index, expected in enumerate(Reverb.PATCHES[0][1]):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_character_zones(self):
        effect = silent_build(Reverb)
        for midi, zone in ((0, 0), (31, 0), (32, 1), (63, 1), (64, 2),
                           (95, 2), (96, 3), (127, 3)):
            effect.set_macro(rv.CHARACTER_I, midi)
            self.assertEqual(effect._index, zone, midi)
        for name, zone in zip(rv.CHARACTERS, range(4)):
            self.assertEqual(silent_build(Reverb, character=name)._index,
                             zone)

    def test_options_clamp_default_and_refuse(self):
        with self.assertRaises(ValueError) as caught:
            silent_build(Reverb, character="spring")
        self.assertIn("parked", str(caught.exception))
        with self.assertRaises(ValueError):
            silent_build(Reverb, character="cathedral")
        nan = float("nan")
        effect = silent_build(Reverb, decay=nan, size=nan, low_cut_hz=nan)
        self.assertAlmostEqual(effect.macro(rv.DECAY_I), 2.4, places=9)
        self.assertAlmostEqual(effect.macro(rv.SIZE_I), 1.0, places=9)
        self.assertAlmostEqual(effect.macro(rv.LOW_CUT_I), 40.0, places=9)
        effect = silent_build(Reverb, decay=50.0, size=0.1, low_cut_hz=-5.0,
                              mix=3.0, tone_db=-40.0)
        self.assertAlmostEqual(effect.macro(rv.DECAY_I), 10.0, places=9)
        self.assertAlmostEqual(effect.macro(rv.SIZE_I), 0.5, places=9)
        self.assertAlmostEqual(effect.macro(rv.LOW_CUT_I), 20.0, places=9)
        self.assertAlmostEqual(effect.macro(rv.MIX_I), 2.0, places=9)
        self.assertAlmostEqual(effect.macro(rv.TONE_I), -12.0, places=9)

    def test_hz_clamps_below_nyquist_at_22050(self):
        src = probes.ArraySource(array("h", [0] * 1024), rate=22050,
                                 channels=2)
        effect = Reverb(src, sample_rate=22050, bandwidth_hz=20000.0,
                        character="room", damping_hz=16000.0)
        self.assertAlmostEqual(effect._handed["bandwidth_hz"], 10804.5)
        self.assertAlmostEqual(effect._handed["damping_hz"], 10804.5)


class TheCut(unittest.TestCase):
    def test_the_plate_tank_is_dattorros_at_48k(self):
        # dossier App. B: Dattorro's tank lines scaled to 48 kHz.
        lines = rv.line_set(rv.PLATE, 1.0, 48000)
        self.assertEqual(lines[4:], [1084, 7182, 2903, 6000,
                                     1464, 6801, 4284, 5101])
        self.assertEqual(lines[:4], [69, 52, 183, 134])

    def test_the_shortest_line_clears_the_node_floor(self):
        shortest = min(min(rv.line_set(i, 0.5, 22050)) for i in range(4))
        self.assertEqual(shortest, 12)

    def test_ram(self):
        # dossier Tier 3: the lines plus 200 ms of predelay, int16.
        def ram(index, size):
            return 2 * (sum(rv.line_set(index, size, 48000)) + 9600)
        self.assertEqual(ram(rv.PLATE, 1.0), 89714)
        self.assertEqual(ram(rv.HALL, 1.5), 146914)
        self.assertEqual(ram(rv.ROOM, 0.5), 38526)

    def test_the_law_never_reaches_the_node_clamp(self):
        largest = 0.0
        spans = Reverb._MACRO_RANGES
        for index in range(4):
            for size in (0.5, 1.0, 1.5):
                lines = rv.line_set(index, size, RATE)
                for dm in range(0, 128, 8):
                    damping = _component.macro_value(spans[rv.DAMPING_I],
                                                     dm / 127.0)
                    for de in list(range(0, 128, 8)) + [127]:
                        t = _component.macro_value(spans[rv.DECAY_I],
                                                   de / 127.0)
                        loop = (rv.damper_hz(t, damping, RATE)
                                if index == rv.PLATE else damping)
                        d = rv.decay_law(rv.KAPPA[index], lines, RATE, t,
                                         min(loop, 0.49 * RATE))[0]
                        largest = max(largest, d)
        self.assertLess(largest, 0.9829)
        self.assertGreater(largest, 0.98)

    def test_tail_samples_at_the_patches(self):
        # dossier section 6: the bound at each patch's settings, 48 kHz.
        for name, frames in (("Steel Plate", 222868), ("Small Room", 80736),
                             ("Slow Bloom", 419791),
                             ("Concert Hall", 297320)):
            self.assertEqual(make(Reverb, name).tail_samples, frames, name)


class Rebuilds(unittest.TestCase):
    def test_a_character_move_rebuilds_and_releases(self):
        effect = silent_build(Reverb)
        port = effect.output
        first = effect._tank
        effect.set_macro(rv.CHARACTER_I, 20)      # same zone: no rebuild
        self.assertIs(effect._tank, first)
        effect.set_macro(rv.CHARACTER_I, 42)      # room
        self.assertIsNot(effect._tank, first)
        self.assertIs(effect.output, port)
        self.assertEqual(effect._nodes, [effect._tank])
        with self.assertRaises(Exception):
            first.set(decay=0.5)                  # released
        second = effect._tank
        effect.set_macro(rv.DECAY_I, 100)
        self.assertIs(effect._tank, second)
        effect.set_macro(rv.SIZE_I, 100)
        self.assertIsNot(effect._tank, second)

    def test_a_patch_rebuilds_once(self):
        class Counting(Reverb):
            NAME = 'Reverb'
            count = 0

            def _rebuild(self, *arguments):
                type(self).count += 1
                Reverb._rebuild(self, *arguments)

        effect = silent_build(Counting)
        Counting.count = 0
        effect.program_change(9)                  # Character and Size move
        self.assertEqual(Counting.count, 1)

    def _wire_across_a_move(self, block, move):
        """Mix 0 over a ramp served `block` frames at a time, one move
        1536 frames in: (frames that differ from the source, how far the
        output runs ahead of it after the move)."""
        frames = 12288
        ramp = np.array([((i * 7) % 20001) - 10000 for i in range(frames)],
                        dtype=np.int16)
        src = probes.ArraySource(interleave(ramp, 2, frames), rate=RATE,
                                 channels=2, block=block)
        effect = Reverb(src, sample_rate=RATE, mix=0.0)
        head = render(effect, 1536)
        effect.set_macro(*move)
        out = np.concatenate([head, render(effect, frames - 2048)])[:, 0]
        differ = int(np.sum(out != ramp[:len(out)]))
        ahead = None
        if differ:
            for k in range(1, 4096):
                if np.array_equal(out[1536:1600], ramp[1536 + k:1600 + k]):
                    ahead = k
                    break
        return differ, ahead

    def test_a_rebuild_keeps_the_wire_on_a_256_frame_source(self):
        # the module docstring: a source whose buffers divide the Tank's
        # 256-frame block loses nothing across a rebuild
        for block in (256, 128):
            for move in ((rv.CHARACTER_I, 42), (rv.SIZE_I, 70)):
                self.assertEqual(self._wire_across_a_move(block, move),
                                 (0, None), (block, move))

    def test_a_rebuild_skips_what_the_old_tank_held(self):
        # the disclosed loss: on a 1024- or 2048-frame source the old
        # Tank's unplayed 512 frames go with it; a move that does not
        # rebuild keeps the wire
        for block in (1024, 2048):
            for move in ((rv.CHARACTER_I, 42), (rv.SIZE_I, 70)):
                differ, ahead = self._wire_across_a_move(block, move)
                self.assertEqual(ahead, 512, (block, move))
                self.assertGreater(differ, 0, (block, move))
            self.assertEqual(self._wire_across_a_move(block,
                                                      (rv.DECAY_I, 90)),
                             (0, None), block)

    def test_a_rebuild_cuts_the_tail(self):
        frames = RATE
        effect = make(Reverb, "Steel Plate", mono=noise_burst(RATE,
                                                              seconds=0.25),
                      frames=frames, mix=2.0)
        render(effect, int(0.5 * RATE))
        effect.set_macro(rv.CHARACTER_I, 127)
        after = render(effect, int(0.25 * RATE))
        self.assertEqual(int(np.max(np.abs(after))), 0)


# -- Tier 1 ------------------------------------------------------------------

class Tier1(unittest.TestCase):
    def test_mix_zero_is_a_wire_at_every_patch(self):
        frames = 4096
        ramp = [((i * 37) % 65536) - 32768 for i in range(frames)]
        for channels in (2, 1):
            for index in range(10):
                data = array("h", [v for v in ramp for _ in range(channels)])
                src = probes.ArraySource(data, rate=RATE, channels=channels)
                effect = Reverb(src, sample_rate=RATE)
                effect.program_change(index)
                effect.set_macro(rv.MIX_I, 0)
                out = render(effect, frames)
                self.assertTrue(np.array_equal(
                    out.reshape(-1), np.array(data, dtype=np.int32)),
                    (channels, index))

    def test_silence_stays_silence(self):
        for channels in (2, 1):
            effect = make(Reverb, frames=RATE, channels=channels, mix=2.0)
            for index in range(10):
                effect.program_change(index)
                self.assertEqual(int(np.max(np.abs(render(effect, 4096)))),
                                 0, index)

    def _tone_route(self, cls, channels):
        """Short Plate (Tone 74) over full-scale noise, Steel Plate (Tone
        64, the same lines, so no rebuild) for its last block, 6 s of
        silence, then Short Plate again: (peak over the last second before
        the move, peak over the 0.1 s after it), Mix 2."""
        noise = RATE // 2
        rng = np.random.RandomState(5)
        burst = np.round(rng.uniform(-1, 1, noise) * 32767).astype(np.int16)
        effect = make(cls, channels=channels, mono=burst,
                      frames=noise + 7 * RATE)
        effect.program_change(1)
        effect.set_macro(rv.MIX_I, 127)
        render(effect, noise - 256)
        first = effect._tank
        effect.program_change(0)
        effect.set_macro(rv.MIX_I, 127)
        self.assertIs(effect._tank, first)
        quiet = render(effect, 256 + 6 * RATE)
        effect.program_change(1)
        effect.set_macro(rv.MIX_I, 127)
        self.assertIs(effect._tank, first)
        after = render(effect, RATE // 10)
        return (int(np.max(np.abs(quiet[-RATE:]))),
                int(np.max(np.abs(after))))

    def test_a_tone_move_out_of_silence_stays_silent(self):
        for channels in (2, 1):
            self.assertEqual(self._tone_route(Reverb, channels), (0, 0),
                             channels)

    def test_tone_detent_as_exact_zero_is_red(self):
        for channels in (2, 1):
            before, after = self._tone_route(ToneDetentZero, channels)
            self.assertEqual(before, 0, channels)
            self.assertGreater(after, 100, channels)

    def test_click_delay_is_zero(self):
        for name in ("Steel Plate", "Concert Hall"):
            frames = 2048
            mono = np.zeros(frames, dtype=np.int16)
            mono[1000] = 20000
            effect = make(Reverb, name, mono=mono, frames=frames, mix=1.0)
            out = render(effect, frames)
            self.assertEqual(int(out[1000, 0]), 20000, name)
            self.assertEqual(int(np.max(np.abs(out[:1000]))), 0, name)

    def test_the_tail_reaches_exact_zero_inside_tail_samples(self):
        for name, channels in (("Steel Plate", 2), ("Small Room", 1)):
            rng = np.random.RandomState(3)
            burst = np.round(rng.uniform(-1, 1, RATE) * 32767).astype(
                np.int16)
            probe = make(Reverb, name, channels=channels)
            bound = probe.tail_samples
            frames = RATE + bound + RATE // 2
            effect = make(Reverb, name, channels=channels, mono=burst,
                          frames=frames, mix=2.0)
            y = render(effect, frames)
            nz = np.nonzero(np.any(y != 0, axis=1))[0]
            last = int(nz[-1]) - RATE
            self.assertLess(last, bound, name)
            self.assertGreater(last, bound // 4, name)

    def test_reset_clears_the_tail_and_restores_patch_0(self):
        effect = make(Reverb, "Concert Hall",
                      mono=np.concatenate([
                          np.zeros(4096, dtype=np.int16),
                          noise_burst(RATE, seconds=0.25)]),
                      frames=2 * RATE, mix=2.0)
        effect.program_change(6)
        render(effect, RATE // 2)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        # the borrowed source is not reset: it is past its burst, so what
        # comes out is the emptied tank and a silent dry
        self.assertEqual(int(np.max(np.abs(render(effect, 4096)))), 0)

    def test_deinit_releases_every_tank_and_leaves_the_source(self):
        src = probes.ArraySource(array("h", [9000] * 4096), rate=RATE,
                                 channels=2)
        effect = Reverb(src, sample_rate=RATE)
        first = effect._tank
        effect.set_macro(rv.CHARACTER_I, 127)
        second = effect._tank
        render(effect, 256)
        effect.deinit()
        for tank in (first, second):
            with self.assertRaises(Exception):
                tank.set(decay=0.5)
        data = memoryview(bytes(audiocore.get_buffer(src)[1])).cast("h")
        self.assertEqual(max(abs(int(v)) for v in data), 9000)

    def test_lower_rates_build_and_ring(self):
        for rate in (44100, 22050):
            for index in (0, 6):
                src = probes.ArraySource(
                    interleave(impulse(), 2, rate // 2), rate=rate,
                    channels=2)
                effect = Reverb(src, sample_rate=rate)
                effect.program_change(index)
                self.assertGreater(int(np.max(np.abs(
                    render(effect, rate // 2)[rate // 10:]))), 0)


# -- Tier 2 ------------------------------------------------------------------

def t1_verdict(profile):
    """T1: on every channel the 200 ms window is not empty and no window
    from 20 to 200 ms reads more than 20 % below it."""
    return all(c200 > 0 and low >= 0.80 * c200
               for _, c200, low in profile)


class T1PlateDensity(unittest.TestCase):
    def test_steel_plate_is_dense_from_20_ms(self):
        profile = density(Reverb, "Steel Plate")
        self.assertTrue(t1_verdict(profile), profile)
        for _, c200, low in profile:
            self.assertGreaterEqual(low / float(c200), 0.81)

    def test_dattorros_published_diffusers_are_red(self):
        profile = density(DattorroDiffuserPlate, "Steel Plate")
        self.assertFalse(t1_verdict(profile), profile)
        for _, c200, low in profile:
            self.assertLess(low / float(c200), 0.6)

    def test_the_fault_is_not_on_the_surface(self):
        result = reach(DattorroDiffuserPlate, handed_cut)
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": t1_verdict(
                density(cls, "Steel Plate"))}, label="Reverb T1")


def t2_verdict(counts, declared):
    lo, hi = counts
    if lo <= 0.0 or hi <= 0.0:
        return False
    return (abs(lo / declared - 1.0) <= 0.10
            and abs(hi / declared - 1.0) <= 0.10 and hi / lo <= 2.0)


class T2ModalDensity(unittest.TestCase):
    def test_resolved_modes_count_the_declared_table(self):
        declared = declared_density("plate", 1.0)
        self.assertAlmostEqual(declared, 0.725, places=3)
        counts = modal_counts(Reverb)
        self.assertTrue(t2_verdict(counts, declared), counts)

    def test_the_inverted_cut_is_red(self):
        declared = declared_density("plate", 1.0)
        counts = modal_counts(InvertedCut)
        self.assertFalse(t2_verdict(counts, declared), counts)
        self.assertLess(max(counts) / declared, 0.75)

    def test_the_fault_is_not_on_the_surface(self):
        result = reach(InvertedCut, handed_cut)
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        declared = declared_density("plate", 1.0)
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": t2_verdict(modal_counts(cls),
                                                      declared)},
            label="Reverb T2")


T3_STOPS = (8.0, 4.0, 2.0, 1.0)


def t3_ratios(cls):
    """R = T60(500 Hz) / T60(4 kHz) at Decay 8 / 4 / 2 / 1 s on Steel Plate
    as patched, each the mean over seeds 7-14; None where a fit fails."""
    key = ("T3", cls)
    if key not in _MEMO:
        rs = []
        for t in T3_STOPS:
            vals = [band_t60s(cls, "Steel Plate", seed, (500, 4000),
                              decay=t) for seed in SEEDS]
            if any(a is None or b is None for a, b in vals):
                rs = None
                break
            rs.append(float(np.mean([a / b for a, b in vals])))
        _MEMO[key] = rs
    return _MEMO[key]


def t3_verdict(rs):
    if rs is None:
        return False
    return (all(b >= a for a, b in zip(rs, rs[1:]))
            and rs[-1] / rs[0] - 1.0 >= 0.20)


class T3Damper(unittest.TestCase):
    def test_the_upper_band_shortens_more_as_decay_shortens(self):
        rs = t3_ratios(Reverb)
        self.assertTrue(t3_verdict(rs), rs)
        # dossier T3: 1.129 -> 1.214 -> 1.376 -> 1.627, +44.2 %
        self.assertAlmostEqual(rs[-1] / rs[0] - 1.0, 0.442, delta=0.05)

    def test_a_frequency_flat_damper_is_red(self):
        rs = t3_ratios(FlatDamper)
        self.assertFalse(t3_verdict(rs), rs)
        self.assertLess(rs[-1] / rs[0] - 1.0, -0.5)

    def test_the_fault_is_not_on_the_surface(self):
        # The character is part of the reading: the room, chamber and hall
        # hand the Damping value flat by design, and the fault is the
        # plate doing it.
        result = reach(FlatDamper, lambda e: (
            e._index, round(e.macro(rv.DECAY_I), 9),
            e._handed["damping_hz"]))
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": t3_verdict(t3_ratios(cls))},
            label="Reverb T3")


class T7LowCut(unittest.TestCase):
    def test_the_tank_sees_no_bass_on_bass_free_plate(self):
        readings = low_cut_readings(Reverb)
        self.assertTrue(low_cut_green(readings, 360.0), readings)

    def test_the_corner_follows_low_cut(self):
        for low_cut in (100.0, 500.0):
            readings = low_cut_readings(Reverb, low_cut_hz=low_cut)
            self.assertLessEqual(abs(readings[3] / low_cut - 1.0), 0.10,
                                 (low_cut, readings))

    def test_the_dry_is_flat(self):
        for name in ("Steel Plate", "Concert Hall"):
            for mix in (0.35, 1.0, 1.5, 1.9):
                self.assertLessEqual(dry_deviation(name, mix), 0.1,
                                     (name, mix))

    def test_low_cut_in_the_dry_is_red(self):
        self.assertGreater(dry_deviation("Bass-Free Plate", 0.4, fault=True),
                           10.0)

    def test_low_cut_in_radians_is_red(self):
        readings = low_cut_readings(LowCutRadians)
        self.assertFalse(low_cut_green(readings, 360.0), readings)
        self.assertLess(readings[3], 70.0)

    def test_the_fault_is_not_on_the_surface(self):
        result = reach(LowCutRadians, lambda e: e._handed["low_cut_hz"])
        self.assertAlmostEqual(result["target"], 40.0 / (2.0 * math.pi))
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": low_cut_green(
                low_cut_readings(cls), 360.0)}, label="Reverb T7")


def t8_verdict(cls, name):
    return all(c200 >= 1.5 * max(c20, 1)
               for c20, c200, _ in density(cls, name))


T8_PATCHES = ("Small Room", "Concert Hall", "Dark Chamber")


class T8TheyBuild(unittest.TestCase):
    def test_room_hall_and_chamber_build(self):
        for name in T8_PATCHES:
            profile = density(Reverb, name)
            self.assertTrue(t8_verdict(Reverb, name), (name, profile))

    def test_on_the_plates_diffusers_they_do_not(self):
        for name in T8_PATCHES:
            self.assertFalse(t8_verdict(PlateDiffuserRooms, name), name)

    def test_the_contrast_the_plate_does_not_build(self):
        self.assertFalse(t8_verdict(Reverb, "Steel Plate"))

    def test_the_fault_is_not_on_the_surface(self):
        result = reach(PlateDiffuserRooms, handed_cut, character="room")
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": t8_verdict(cls, "Small Room")},
            label="Reverb T8")


def t60_1k(cls, name):
    key = ("T9", cls, name)
    if key not in _MEMO:
        vals = [band_t60s(cls, name, seed, (1000,))[0]
                for seed in (7, 8, 9, 10)]
        _MEMO[key] = None if None in vals else float(np.mean(vals))
    return _MEMO[key]


def t9_verdict(cls):
    hall, live, small = (t60_1k(cls, n) for n in
                         ("Concert Hall", "Live Room", "Small Room"))
    arrivals = [first_arrival_ms(cls, n) for n in
                ("Concert Hall", "Live Room", "Small Room")]
    if None in (hall, live, small) or None in arrivals:
        return False
    return (hall >= 2.0 * live and hall >= 4.0 * small
            and arrivals[0] >= 10.0 and arrivals[1] <= 6.0
            and arrivals[2] <= 6.0)


def construction_pairs(cls, rate=RATE):
    """(Character index, line set) at every Size grid position, read off
    built instances' handed state."""
    pairs = set()
    effect = silent_build(cls)
    for midi in rv.CHARACTER_MIDI:
        effect.set_macro(rv.CHARACTER_I, midi)
        for size in range(128):
            effect.set_macro(rv.SIZE_I, size)
            pairs.add(handed_cut(effect))
    effect.deinit()
    return pairs


class T9ThreeTunings(unittest.TestCase):
    def test_the_patches_are_three_tunings(self):
        self.assertTrue(t9_verdict(Reverb))
        self.assertGreaterEqual(first_arrival_ms(Reverb, "Concert Hall"),
                                12.9)

    def test_no_two_characters_share_a_line_set(self):
        for rate in (48000, 44100, 22050):
            owners = {}
            for index in range(4):
                for midi in range(128):
                    lines = tuple(rv.line_set(index, 0.5 + midi / 127.0,
                                              rate))
                    owners.setdefault(lines, set()).add(index)
            self.assertEqual([s for s in owners.values() if len(s) > 1], [],
                             rate)

    def test_the_hall_on_the_rooms_lines_is_red(self):
        self.assertFalse(t9_verdict(HallOnRoomLines))
        self.assertLess(first_arrival_ms(HallOnRoomLines, "Concert Hall"),
                        10.0)
        planted = silent_build(HallOnRoomLines, character="hall",
                               size=0.5 + 95 / 127.0)
        self.assertNotIn(handed_cut(planted), construction_pairs(Reverb))

    def test_the_fault_is_not_on_the_surface(self):
        result = reach(HallOnRoomLines, handed_cut, character="hall")
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": t9_verdict(cls)},
            label="Reverb T9")


def t10_on(cls):
    return all(sidebands_db(cls, name, 1000.0, SETTINGS[name]["mod_rate_hz"])
               >= -20.0 for name in ("Steel Plate", "Concert Hall"))


def t10_off(cls):
    return all(sidebands_db(cls, name, 1000.0, 1.0e9, mod_depth_ms=0.0)
               <= -60.0 for name in ("Steel Plate", "Concert Hall"))


class T10Modulation(unittest.TestCase):
    def test_a_still_tank_is_one_line(self):
        self.assertTrue(t10_off(Reverb))

    def test_the_patches_modulation_spreads_it(self):
        self.assertTrue(t10_on(Reverb))

    def test_the_lowest_claimed_depth(self):
        v = sidebands_db(Reverb, "Steel Plate", 1000.0, 1.0,
                         mod_depth_ms=0.27, mod_rate_hz=1.0)
        self.assertGreaterEqual(v, -20.0)

    def test_0_1_ms_is_not_claimed_it_follows_the_line_set(self):
        # dossier section 8, R2: at Mod Depth 0.1 ms on Steel Plate the
        # reading depends on the exact lines; green at Size 1.0 (-18.4 dB),
        # red on patch 0's grid Size 64 = 1.0039 (-27.2 dB)
        at_1 = sidebands_db(Reverb, "Steel Plate", 1000.0, 1.0,
                            mod_depth_ms=0.1, mod_rate_hz=1.0)
        at_grid = sidebands_db(Reverb, "Steel Plate", 1000.0, 1.0,
                               mod_depth_ms=0.1, mod_rate_hz=1.0,
                               size=0.5 + 64 / 127.0)
        self.assertGreaterEqual(at_1, -20.0)
        self.assertLess(at_grid, -20.0)

    def test_mod_rate_as_its_reciprocal_is_red(self):
        self.assertFalse(t10_on(RateReciprocal))

    def test_mod_depth_mirrored_is_red(self):
        self.assertFalse(t10_off(DepthMirrored))

    def test_the_faults_are_not_on_the_surface(self):
        result = reach(RateReciprocal, lambda e: e._handed["mod_rate_hz"])
        self.assertAlmostEqual(result["target"], 1000.0, places=6)
        self.assertEqual(result["checked"], WALK)
        result = reach(DepthMirrored, lambda e: e._handed["mod_depth_ms"])
        self.assertGreater(result["target"], 2.0)
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": t10_on(cls)}, label="Reverb T10")


T11_STOPS = (2.0, 4.0, 8.0, 10.0)


def t11_errors(cls, character, stops=T11_STOPS):
    """(T60 at 500 Hz / Decay - 1) at each stop, the mean over seeds 7-14,
    at the character's reference patch with Size 1.0."""
    key = ("T11", cls, character, stops)
    if key not in _MEMO:
        errors = []
        for t in stops:
            vals = [band_t60s(cls, REFERENCE[character], seed, (500,),
                              decay=t, size=1.0)[0] for seed in SEEDS]
            if None in vals:
                errors = None
                break
            errors.append(float(np.mean(vals)) / t - 1.0)
        _MEMO[key] = errors
    return _MEMO[key]


def t11_verdict(errors):
    return errors is not None and all(abs(e) <= 0.12 for e in errors)


class T11DecayIsT60(unittest.TestCase):
    def test_every_character_lands_its_label(self):
        for character in rv.CHARACTERS:
            errors = t11_errors(Reverb, character)
            self.assertTrue(t11_verdict(errors), (character, errors))

    def test_one_multiply_per_half_pass_is_red(self):
        errors = t11_errors(OneMultiply, "plate")
        self.assertFalse(t11_verdict(errors), errors)
        self.assertTrue(all(e < -0.35 for e in errors), errors)

    def test_the_fault_is_not_on_the_surface(self):
        result = reach(OneMultiply, lambda e: (
            round(e.macro(rv.DECAY_I), 9), e._handed["decay"]))
        self.assertEqual(result["checked"], WALK)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            Reverb, lambda cls: {"passed": t11_verdict(
                t11_errors(cls, "plate"))}, label="Reverb T11")


# -- the Decay knees (dossier section 8.9, audit-3 ruling (o)) ----------------

def midi_for(index, value):
    """The fractional MIDI position that lands macro `index` on `value`."""
    return _component.midi_of_position(
        Reverb.MACRO_MODES.get(index, "UNIPOLAR"),
        _component.macro_position(Reverb._MACRO_RANGES[index], value))


PATCH_INDEX = {name: index for index, (name, _) in enumerate(PATCH_SETTINGS)}


def t500_mean(build, decay, seeds=SEEDS, rate=RATE, hint=None):
    """M3 at 500 Hz on interrupted noise (2 s at 8 000 LSB RMS, then
    silence), the mono sum, Mix 2, the mean over `seeds`; `build(src)`
    makes the instance. The render runs 1.3 x max(`hint` or Decay, 1 s)
    past the burst, which reaches past -35 dB at every cell here."""
    t = decay if hint is None else hint
    frames = int((BURST_S + 1.3 * max(t, 1.0) + 0.8) * rate)
    vals = []
    for seed in seeds:
        src = probes.ArraySource(interleave(noise_burst(rate, seed), 2,
                                            frames),
                                 rate=rate, channels=2, block=256)
        effect = build(src)
        try:
            y = render(effect, frames)
        finally:
            effect.deinit()
        m = y.astype(np.float64).sum(axis=1)
        vals.append(t60_slope(band(m, rate, 500)[int(BURST_S * rate):],
                              rate))
    return None if None in vals else float(np.mean(vals))


def knee_t500(cls, character, size, decay, seeds=SEEDS):
    """The floor-knee cell: the character's reference patch on the grid
    (`program_change`), Size and Decay set on the macros, Mix 2."""
    key = ("floor", cls, character, size, decay, seeds)
    if key not in _MEMO:
        def build(src):
            effect = cls(src, sample_rate=RATE)
            effect.program_change(PATCH_INDEX[REFERENCE[character]])
            effect.set_macro(rv.SIZE_I, midi_for(rv.SIZE_I, size))
            effect.set_macro(rv.DECAY_I, midi_for(rv.DECAY_I, decay))
            effect.set_macro(rv.MIX_I, 127)
            return effect
        _MEMO[key] = t500_mean(build, decay, seeds)
    return _MEMO[key]


FLOOR_STOPS = (0.3, 0.45, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0)
KNEE_SIZES = (0.5, 0.75, 1.0, 1.25, 1.5)

#: Section 8.9's floor knee as a band, as revised 2026-09-28 (R12): the
#: knee is the lowest Decay from which every position up to 2 s lands
#: within +/-12 % at 500 Hz, and the noise moves it, so each cell is the
#: (lowest, highest) knee read on four sets of eight seeds (7-14, 15-22,
#: 23-30, 31-38). The chamber at Size 1.5 has none at or under 2 s on one
#: set (its 2 s cell sits on the bar, T11, R7) and has its own test.
FLOOR_BANDS = {
    "plate": ((0.3, 1.0), (0.45, 1.0), (1.0, 1.0), (1.5, 2.0), (1.5, 1.5)),
    "room": ((0.45, 0.45), (0.8, 1.0), (0.8, 0.8), (1.0, 1.5), (1.0, 1.25)),
    "chamber": ((0.6, 0.6), (0.8, 0.8), (1.0, 1.25), (1.5, 1.5), None),
    "hall": ((0.45, 0.8), (1.0, 1.25), (1.25, 1.5), (1.25, 1.5),
             (2.0, 2.0)),
}


def predicted_t500(character, size, decay, damping=1000.0, rate=RATE,
                   cap=1.5):
    """T60 at 500 Hz the dossier's capped law gives on the room, chamber
    or hall (their loop corner is Damping): (seconds, capped)."""
    index = rv.CHARACTERS.index(character)
    lines = rv.line_set(index, size, rate)
    a, b = rv.half_periods(lines)
    p = 0.5 * (a + b)
    d, capped, _ = capped_law(rv.KAPPA[index], lines, rate, decay, damping,
                              cap)
    g = d * d * rv.one_pole_mag(damping, 500.0, rate)
    return 3.0 * rv.KAPPA[index] * p / (-rate * math.log10(g)), capped


def capped_cells():
    """The constructor defaults (Damping 1 kHz) on the room, chamber and
    hall at Size 0.5 / 1.0 / 1.5 and Decay 2 / 4 / 8 / 10 s where the
    dossier's law caps the bass."""
    out = []
    for character in ("room", "chamber", "hall"):
        for size in (0.5, 1.0, 1.5):
            for t in (2.0, 4.0, 8.0, 10.0):
                pred, capped = predicted_t500(character, size, t)
                if capped:
                    out.append((character, size, t, pred))
    return out


def ceiling_t500(cls, character, size, decay, hint):
    key = ("ceiling", cls, character, size, decay)
    if key not in _MEMO:
        _MEMO[key] = t500_mean(
            lambda src: cls(src, sample_rate=RATE, character=character,
                            size=size, decay=decay, mix=2.0),
            decay, hint=hint)
    return _MEMO[key]


class DecayKnees(unittest.TestCase):
    """Section 8.9's promise: a test that fails if a knee moves."""

    def _floor(self, character, cls=None, seeds=SEEDS, sizes=KNEE_SIZES):
        """What holds on every seed set: every position from the band's
        top to 2 s inside +/-12 %, and the position under the band's
        bottom outside (none where the bottom is the first stop)."""
        cls = Reverb if cls is None else cls
        for size, band in zip(KNEE_SIZES, FLOOR_BANDS[character]):
            if band is None or size not in sizes:
                continue
            bottom, top = band
            for t in FLOOR_STOPS[FLOOR_STOPS.index(top):]:
                e = knee_t500(cls, character, size, t, seeds) / t - 1.0
                self.assertLessEqual(abs(e), 0.12, (character, size, t, e))
            i = FLOOR_STOPS.index(bottom)
            if i:
                t = FLOOR_STOPS[i - 1]
                e = knee_t500(cls, character, size, t, seeds) / t - 1.0
                self.assertGreater(abs(e), 0.12, (character, size, t, e))

    def test_the_plates_floor_knees(self):
        self._floor("plate")

    def test_the_rooms_floor_knees(self):
        self._floor("room")

    def test_the_chambers_floor_knees(self):
        self._floor("chamber")

    def test_the_halls_floor_knees(self):
        self._floor("hall")

    def test_the_plates_floor_bands_hold_on_another_seed_set(self):
        # the property the one-stop table lacked: the same assertions on
        # seeds 23-30, where that table failed at two plate cells
        self._floor("plate", seeds=tuple(range(23, 31)))

    def test_the_chamber_at_size_1_5_has_no_knee_under_2_s(self):
        # T11's cell, Not claimed (R7): 1.5 s is outside, and 2 s reads
        # inside on seeds 7-14 but outside on seeds 23-30
        e15 = knee_t500(Reverb, "chamber", 1.5, 1.5) / 1.5 - 1.0
        self.assertGreater(abs(e15), 0.12, e15)
        e2 = knee_t500(Reverb, "chamber", 1.5, 2.0) / 2.0 - 1.0
        self.assertTrue(0.08 <= e2 <= 0.12, e2)
        e2b = knee_t500(Reverb, "chamber", 1.5, 2.0,
                        tuple(range(23, 31))) / 2.0 - 1.0
        self.assertGreater(e2b, 0.12, e2b)

    def test_longer_diffusers_move_the_floor_knee(self):
        # the floor assertions at Size 1.0 fail on the plate, room and
        # chamber once their diffusers are 1.5 x longer: the band's top
        # reads +13.7 % (plate, 1 s), +21.9 % (room, 0.8 s) and +14.5 %
        # (chamber, 1.25 s). The hall's does not move (+7.3 % at its 1.5 s
        # top), and the plant is recorded as blind there.
        for character in ("plate", "room", "chamber"):
            with self.assertRaises(AssertionError, msg=character):
                self._floor(character, LongDiffusers, sizes=(1.0,))
            top = FLOOR_BANDS[character][KNEE_SIZES.index(1.0)][1]
            e = knee_t500(LongDiffusers, character, 1.0, top) / top - 1.0
            self.assertGreater(abs(e), 0.12, (character, top, e))

    def test_the_longer_diffusers_are_not_on_the_surface(self):
        result = reach(LongDiffusers, handed_cut)
        self.assertEqual(result["checked"], WALK)

    def test_the_ceiling_knees(self):
        cells = capped_cells()
        self.assertEqual(len(cells), 19)
        misses = []
        for character, size, t, pred in cells:
            got = ceiling_t500(Reverb, character, size, t, pred)
            # R13: on four seed sets the room at Size 0.5 lands 5.1 to
            # 12.9 % long of the prediction (2 s reads +12.9 % on seeds
            # 31-38), the other 15 cells within 6.7 %; the room's four
            # cells are held to 15 %, a margin that is ours
            bar = 0.15 if (character, size) == ("room", 0.5) else 0.12
            self.assertLessEqual(abs(got / pred - 1.0), bar,
                                 (character, size, t, got, pred))
            misses.append(1.0 - got / t)
        # while the label there misses by up to about 60 %
        self.assertGreater(max(misses), 0.5, misses)

    def test_a_loose_ceiling_is_red(self):
        # the two cells where a cap at 2.0 moves 500 Hz most (+14.6 and
        # +15.0 % measured); at most cells it moves under 12 %
        for character, size, t in (("chamber", 1.0, 8.0),
                                   ("room", 1.5, 8.0)):
            pred, capped = predicted_t500(character, size, t)
            self.assertTrue(capped)
            got = ceiling_t500(LooseCeiling, character, size, t, 1.4 * pred)
            self.assertGreater(abs(got / pred - 1.0), 0.12,
                               (character, size, t, got, pred))

    def test_the_loose_ceiling_is_not_on_the_surface(self):
        result = reach(LooseCeiling, lambda e: (
            e._index, tuple(e._lines), round(e.macro(rv.DECAY_I), 9),
            e._handed["decay"]), character="room", size=0.5, decay=10.0)
        self.assertEqual(result["checked"], WALK)


# -- the input ceiling (audit-3 rulings (m) and (o)) -------------------------

def railed(name, rms, rate=RATE, channels=2, mix=1.0, **override):
    """Samples on the int16 rail over 2 s of uniform noise at `rms` LSB RMS
    (seed 11) and 0.5 s after, at Mix 1 by default."""
    rng = np.random.RandomState(11)
    n = 2 * rate
    x = np.round(np.clip(rng.uniform(-1, 1, n) * rms * math.sqrt(3),
                         -32768, 32767)).astype(np.int16)
    frames = n + rate // 2
    effect = make(Reverb, name, rate, channels, x, frames, mix=mix,
                  **override)
    try:
        y = render(effect, frames)
    finally:
        effect.deinit()
    return int(np.count_nonzero(np.abs(y) >= 32767))


def sine_wet_gain(hz, rms, rate=RATE):
    """The wet's carrier gain on a steady sine at `rms` LSB RMS at the
    constructor defaults, Mix 2: the last 2 s of 6 s, one Hann FFT."""
    n = 6 * rate
    x = np.round(rms * math.sqrt(2) * np.sin(
        2 * np.pi * hz * np.arange(n) / rate)).astype(np.int16)
    effect = make(Reverb, None, rate, 2, x, n, mix=2.0)
    try:
        y = render(effect, n)
    finally:
        effect.deinit()
    seg = y.astype(np.float64).sum(axis=1)[-2 * rate:] / 2.0
    xin = x.astype(np.float64)[-2 * rate:]
    win = np.hanning(len(seg))
    f = np.fft.rfftfreq(len(seg), 1.0 / rate)
    k = int(np.argmin(np.abs(f - hz)))
    a = np.abs(np.fft.rfft(seg * win))[k - 2:k + 3].max()
    b = np.abs(np.fft.rfft(xin * win))[k - 2:k + 3].max()
    return 20 * math.log10(a / b)


class InputCeiling(unittest.TestCase):
    def test_no_patch_reaches_the_rail_at_4000_lsb_rms(self):
        for name, _ in PATCH_SETTINGS:
            self.assertEqual(railed(name, 4000.0), 0, name)

    def test_6_db_more_reaches_it(self):
        # the same reading, the input planted 6 dB hotter
        hot = [name for name, _ in PATCH_SETTINGS
               if railed(name, 8000.0) > 0]
        self.assertGreaterEqual(len(hot), 6, hot)

    def test_the_tanks_lines_compress_from_8000_lsb_rms(self):
        # the docstring: flat to 4 000 LSB RMS, about 1.3 dB down at 8 000
        # on a 362 Hz sine at the defaults, with the output under the rail
        g1, g4, g8 = (sine_wet_gain(362.0, r) for r in (1000.0, 4000.0,
                                                        8000.0))
        self.assertLessEqual(abs(g4 - g1), 0.1, (g1, g4))
        self.assertLess(g8 - g4, -1.0, (g4, g8))


if __name__ == "__main__":
    unittest.main()
