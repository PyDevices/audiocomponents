"""`SlapbackDelay`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/SlapbackDelay.md`
(frozen at anchor 7a5a4cb, the Station A critique's re-freeze); its Tier 2
rows are T1-T5. Each row here is the measurement at a few of the row's
cells and the same measurement shown red on a planted fault of the same
kind, at the constructor defaults (or, for a clause the defaults do not
reach, at the row's own cell, said where it is). Every fault is shown
unreachable from every macro position and shipped patch, and every row's
measurement is shown red on the class built as a wire. The full spans, the
three interpreters and the rates live in the evidence pack, not in this
file.

Every law a measurement checks against is written out here from the
dossier, never taken from the class: the whole-frame landing, the Wow map,
the Time span.

The rebuild is parked (not in `rebuilt.ADOPTED`), so the class is reached by
`rebuilt.module_class("SlapbackDelay")`.
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
from audioeffects.chorus import nominal_damping_hz          # noqa: E402
from audioeffects.rebuilt import slapbackdelay as sd        # noqa: E402
from tools.effect_measurements import instantaneous_hz      # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
BLOCK = 256
RATES = (48000, 44100, 22050)
TIME_I, LEVEL_I, SATURATION_I, TONE_I, WOW_I, REPEATS_I = range(6)

SlapbackDelay = rebuilt.module_class("SlapbackDelay")


# --------------------------------------------------------------------------
# The dossier's laws, written out independently of the class


def law_frames(time_ms, rate):
    """Section 6: the nearest whole frame, floor(ms fs / 1000 + 0.5)."""
    return int(math.floor(time_ms * rate / 1000.0 + 0.5))


def law_time_ms(midi):
    """Section 6: Time is 40-250 ms, log, on the 0-127 grid."""
    return 40.0 * 6.25 ** (midi / 127.0)


def law_wow_ms(cents):
    """A4: the rising side of a 0.7 Hz wow reaches `cents` at this depth."""
    cents = min(max(cents, 0.0), 3.5)
    return (2.0 ** (cents / 1200.0) - 1.0) / (2.0 * math.pi * 0.7) * 1000.0


def law_wow_frames(cents, rate):
    return int(math.ceil(law_wow_ms(cents) * rate / 1000.0))


#: Section 6's patch table, in engineering units, which `macro_of` puts on
#: the grid: (Time ms, Level, Saturation, Tone Hz, Wow cents, Repeats).
DOSSIER_PATCHES = (
    ("Single Slap", (135.0, 0.35, 0.15, 20000.0, 1.0, 0.0)),
    ("Short Slap", (85.0, 0.35, 0.15, 20000.0, 1.0, 0.0)),
    ("Doubling", (40.0, 0.5, 0.15, 20000.0, 2.0, 0.0)),
    ("Hot Return", (135.0, 0.35, 0.7, 20000.0, 1.0, 0.0)),
    ("Two Repeats", (135.0, 0.35, 0.15, 20000.0, 1.0, 0.35)),
    ("Dark Slap", (135.0, 0.35, 0.15, 5000.0, 1.0, 0.0)),
)
DOSSIER_SPANS = ((40.0, 250.0, "log"), (0.0, 2.0), (0.0, 1.0),
                 (2000.0, 20000.0, "log"), (0.0, 3.5), (0.0, 0.6))


# --------------------------------------------------------------------------
# Planted faults, one or more per Tier 2 row, each of the row's own kind


class Frames441Slapback(SlapbackDelay):
    """T1's delay clause and T2: Time landed with 44.1 kHz frames at every
    rate. At the 48 kHz defaults the repeat lands at 5 954 frames (124.0 ms,
    8.8 % early); at 44.1 kHz it is the right count, so it is read at 48
    and 22.05 kHz only."""

    NAME = 'SlapbackDelay'

    def _node_time_ms(self, frames):
        del frames
        return law_frames(self._time_ms(), 44100) * 1000.0 / self._sample_rate


class FloorSlapback(SlapbackDelay):
    """T1's no-second-repeat clause: a floor on the loop gain, Repeats 0
    handing the node 0.05, so a second repeat comes back about 26 dB
    down."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if self._feedback <= 0.0:
            self._delay.set(feedback=0.05)


class PannedSlapback(SlapbackDelay):
    """T3: the node handed `input_pan` -0.2, so the repeat leans left."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        self._delay.set(input_pan=-0.2)


class OpenTopSlapback(SlapbackDelay):
    """T4's out clause: the top stop hands the node the pre-warped 20 kHz
    (13 095.11 Hz at 48 kHz) instead of exactly 0. Every in-circuit
    position hands less at 48 and 44.1 kHz; at 22.05 kHz grid 94-126 hand
    the same 6 183.68, so it is walked at 48 and 44.1 kHz only."""

    NAME = 'SlapbackDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return nominal_damping_hz(self._hz(20000.0), self._sample_rate)
        return SlapbackDelay._tone_damping(self, position)


class RawToneSlapback(SlapbackDelay):
    """T4's corner clauses: Tone handed raw, not pre-warped. Silent at the
    defaults (Tone out hands 0 either way) and on every shipped patch
    inside the bar; read at the 15 kHz cell, where the one-pole then has no
    half-power point below Nyquist."""

    NAME = 'SlapbackDelay'

    def _tone_damping(self, position):
        if position >= 1.0:
            return 0.0
        corner = _component.macro_value(self._MACRO_RANGES[TONE_I], position)
        return self._hz(corner)


class NoTwoPiSlapback(SlapbackDelay):
    """T5: the depth map without its 2 pi, a 6.3x deeper wobble."""

    NAME = 'SlapbackDelay'

    def _wow_depth_ms(self, cents):
        return sd.wow_depth_ms(cents) * 2.0 * math.pi


class NoWowTailSlapback(SlapbackDelay):
    """Tier 1's tail: the bound without the wow's depth, which the repeat
    of a burst outlives by the frames the wow moves it late."""

    NAME = 'SlapbackDelay'

    @property
    def tail_samples(self):
        memory, excess = sd.tone_excess(self._damping, self._sample_rate)
        laps = sd.laps_to_zero(self._feedback, excess)
        return int(laps * (self._reach + 1 + memory))


class RawFeedbackSlapback(SlapbackDelay):
    """Tier 1's tail with Tone in: Repeats handed to the node as set, inside
    the stall window at 0.5, where the loop low-pass holds 1 LSB for
    ever."""

    NAME = 'SlapbackDelay'

    def _loop_feedback(self, feedback, excess):
        return feedback


class FrozenToneSlapback(SlapbackDelay):
    """Tier 1's silence clause after a Tone move: the out stop hands the
    node exactly 0 even after Tone has been in, so the loop low-pass
    freezes on whatever it held and a later Tone move plays it out of
    silence (the review's stale-state defect)."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        if self._macros[TONE_I] >= 1.0:
            self._delay.set(damping_hz=0.0)


class TargetOnlyTailSlapback(SlapbackDelay):
    """Tier 1's tail after a falling move: the bound from the target Time
    alone, while the read head is still walking down from the old one."""

    NAME = 'SlapbackDelay'

    def _refresh(self):
        SlapbackDelay._refresh(self)
        self._reach = self._frames


# --------------------------------------------------------------------------
# Sources and pulls


def to_source(values, channels=2, rate=RATE):
    """A mono sequence, copied to every channel."""
    x = np.clip(np.round(np.asarray(values, dtype=np.float64)),
                -32768, 32767).astype(np.int16)
    data = array("h", np.repeat(x[:, None], channels, axis=1)
                 .reshape(-1).tobytes())
    return probes.ArraySource(data, rate=rate, channels=channels,
                              block=BLOCK), data


def silence_src(frames, channels=2, rate=RATE):
    return probes.ArraySource(array("h", [0] * (frames * channels)),
                              rate=rate, channels=channels, block=BLOCK)


def pull(effect, frames, channels=None, on_block=None):
    """(frames, channels) int16; `on_block(frame)` runs before each block."""
    channels = channels or effect.channel_count
    out = array("h")
    while len(out) < frames * channels:
        if on_block is not None:
            on_block(len(out) // channels)
        data = bytes(audiocore.get_buffer(effect.output)[1])
        if not data:
            out.extend([0] * (frames * channels - len(out)))
            break
        out.extend(memoryview(data).cast("h"))
    return np.array(out[:frames * channels],
                    dtype=np.int16).reshape(-1, channels)


def render(cls, values, rate=RATE, channels=2, macros=None, **options):
    """`values` through `cls` built with `options`, then `macros`
    ({index: MIDI}) set, so a macro can be held over a patch."""
    source, _ = to_source(values, channels, rate)
    effect = cls(source, sample_rate=rate, **options)
    for index in sorted(macros or {}):
        effect.set_macro(index, macros[index])
    return pull(effect, len(values), channels)


def cell_time_and_wow(options):
    """The cell's Time and Wow by the dossier's laws: a constructor value
    as given, a patch at its grid values."""
    if "patch" in options:
        midi = SlapbackDelay.PATCHES[options["patch"]][1]
        return law_time_ms(midi[TIME_I]), 3.5 * midi[WOW_I] / 127.0
    return options.get("time_ms", 135.0), options.get("wow_cents", 1.0)


# --------------------------------------------------------------------------
# T1: one repeat, and no second one


def t1_read(cls, rate=RATE, channels=2, click_lsb=32767, **options):
    """The click response at frame 0: energy in the windows
    +-k (ceil(wow) + 2) frames around kT (+64 with Tone in), k = 1..4, and
    the delay in ms by the centroid around the first non-zero sample after
    the click, wherever it lands."""
    time_ms, wow = cell_time_and_wow(options)
    T = law_frames(time_ms, rate)
    w = law_wow_frames(wow, rate)
    tone_in = options.get("tone_hz", 20000.0) < 20000.0
    tail = 64 if tone_in else 0
    n = int(4.6 * T) + 200
    x = np.zeros(n)
    x[0] = click_lsb
    y = render(cls, x, rate, channels, **options)[:, 0]
    energies = []
    for k in (1, 2, 3, 4):
        lo = max(0, k * T - k * (w + 2))
        hi = k * T + k * (w + 2) + tail + 1
        energies.append(float((y[lo:hi].astype(float) ** 2).sum()))
    nonzero = np.nonzero(y[1:])[0]
    if not len(nonzero):
        return energies, float("nan")
    lo = int(nonzero[0]) + 1
    seg = np.abs(y[lo:lo + 2 * (w + 2) + tail + 1].astype(float))
    centroid = lo + float((np.arange(len(seg)) * seg).sum() / seg.sum())
    return energies, centroid * 1000.0 / rate


def t1_measure(cls, rate=RATE, channels=2, click_lsb=32767, delay_bar=True,
               **options):
    """Repeats 0: a first repeat, exact zero in the 2T-4T windows, and (at
    the defaults) the delay in 130-140 ms."""
    energies, delay_ms = t1_read(cls, rate, channels, click_lsb, **options)
    red = []
    if energies[0] <= 0.0:
        red.append("no first repeat")
    if any(e > 0.0 for e in energies[1:]):
        red.append("a 2T-4T window is not exact zero")
    if delay_bar and not 130.0 <= delay_ms <= 140.0:
        red.append("delay %.3f ms" % delay_ms)
    second = (10.0 * math.log10(energies[1] / energies[0])
              if energies[0] > 0.0 and energies[1] > 0.0 else None)
    return {"passed": not red, "red": red, "delay_ms": delay_ms,
            "second_db": second}


def t1_control(cls, rate=RATE, **options):
    """At Repeats above 0 the 2T window carries more than -20 dB re the
    first."""
    energies, _ = t1_read(cls, rate, **options)
    if energies[0] <= 0.0 or energies[1] <= 0.0:
        return {"passed": False, "second_db": None}
    second = 10.0 * math.log10(energies[1] / energies[0])
    return {"passed": second > -20.0, "second_db": second}


# --------------------------------------------------------------------------
# T2: the comb's teeth are 1/T


PAD_S = 20.0


def comb_guess(mag, bin_hz, minimum_hz=1.0):
    """The spacing's first guess: an autocorrelation along frequency, by
    FFT, 1 Hz floor. It takes no law."""
    m = mag - mag.mean()
    size = 1 << int(math.ceil(math.log(2 * len(m), 2)))
    spec = np.fft.rfft(m, n=size)
    corr = np.fft.irfft(spec * np.conj(spec), n=size)[:len(m)]
    low = max(1, int(minimum_hz / bin_hz))
    peak = low + int(np.argmax(corr[low:]))
    y0, y1, y2 = corr[peak - 1], corr[peak], corr[peak + 1]
    den = y0 - 2 * y1 + y2
    off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
    return (peak + off) * bin_hz


def notch_spacing(mag, bin_hz, lo, hi, guess):
    """Notches as local minima (parabolic sub-bin), numbered by consecutive
    gaps, spacing by least squares. (nan, count) under three notches."""
    a, b = int(lo / bin_hz), int(hi / bin_hz)
    half = max(2, int(0.4 * guess / bin_hz))
    freqs = []
    k = a + half
    while k < b - half:
        seg = mag[k - half:k + half + 1]
        j = int(np.argmin(seg))
        if j == half and seg.max() - seg.min() > 1e-9 * max(seg.max(), 1):
            y0, y1, y2 = mag[k - 1], mag[k], mag[k + 1]
            den = y0 - 2 * y1 + y2
            off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
            freqs.append((k + off) * bin_hz)
            k += half
        else:
            k += 1
    if len(freqs) < 3:
        return float("nan"), len(freqs)
    freqs = np.array(freqs)
    index = np.concatenate([[0.0], np.cumsum(np.round(np.diff(freqs)
                                                      / guess))])
    return float(np.polyfit(index, freqs, 1)[0]), len(freqs)


def t2_measure(cls, rate=RATE, click_lsb=32767, click_at=100, **options):
    """The click response at Level 0.35, zero-padded to 20 s: the notch
    spacing over 200 Hz-2 kHz and 8-10 kHz, each within 0.5 % of 1/T and
    within 0.5 % of each other."""
    time_ms, _ = cell_time_and_wow(options)
    T = law_frames(time_ms, rate)
    law = rate / float(T)
    n = click_at + T + 400
    x = np.zeros(n)
    x[click_at] = click_lsb
    y = render(cls, x, rate, 2, **options)[:, 0].astype(float)
    size = int(PAD_S * rate)
    mag = np.abs(np.fft.rfft(y, n=size))
    bin_hz = rate / float(size)
    guess = comb_guess(mag, bin_hz)
    low, low_n = notch_spacing(mag, bin_hz, 200.0, 2000.0, guess)
    high, high_n = notch_spacing(mag, bin_hz, 8000.0, 10000.0, guess)
    deviations = (100.0 * (low - law) / law, 100.0 * (high - law) / law,
                  100.0 * (high - low) / low)
    passed = all(abs(d) <= 0.5 for d in deviations)   # NaN reads red
    return {"passed": passed, "deviations": deviations,
            "notches": (low_n, high_n)}


# --------------------------------------------------------------------------
# T3: mono, the dry's position, and present


def t3_measure(cls, rate=RATE, **options):
    """On the channel-identical full-scale ramp: max |L - R| is 0 LSB, the
    one-channel render is the stereo render's left channel sample for
    sample, and at Level 2 the output is exact zero before T - (ceil(wow)
    + 2) frames and carries the probe's energy, shifted by T, within
    4 dB."""
    time_ms, wow = cell_time_and_wow(options)
    T = law_frames(time_ms, rate)
    w = law_wow_frames(wow, rate) + 2
    frames = T + 4096
    ramp = probes.ramp_fs(frames=frames, channels=1)
    stereo = render(cls, ramp, rate, 2, **options)
    mono = render(cls, ramp, rate, 1, **options)[:, 0]
    lr = int(np.abs(stereo[:, 0].astype(np.int32)
                    - stereo[:, 1].astype(np.int32)).max())
    mono_diff = int(np.count_nonzero(mono != stereo[:, 0]))
    wet = render(cls, ramp, rate, 2, macros={LEVEL_I: 127}, **options)
    head = int(np.count_nonzero(wet[:T - w]))
    y = wet[T - w:, 0].astype(float)
    s = np.array(ramp, dtype=np.float64)[:frames - T + w]
    energy_db = 10.0 * math.log10(max((y ** 2).sum(), 1e-12)
                                  / (s ** 2).sum())
    wet_lr = int(np.abs(wet[:, 0].astype(np.int32)
                        - wet[:, 1].astype(np.int32)).max())
    passed = (lr == 0 and wet_lr == 0 and mono_diff == 0 and head == 0
              and abs(energy_db) <= 4.0)
    return {"passed": passed, "lr": max(lr, wet_lr), "mono_diff": mono_diff,
            "head": head, "energy_db": energy_db}


# --------------------------------------------------------------------------
# T4: Tone's number is the corner it achieves, and out is out


def t4_out_differing(cls, rate=RATE, channels=2):
    """The class at its defaults (Tone out) against a node given no
    `damping_hz`, at the dossier's settings for the defaults, on the
    full-scale ramp: the samples that differ."""
    frames = law_frames(135.0, rate) + 8192
    ramp = probes.ramp_fs(frames=frames, channels=channels)
    effect = cls(probes.ArraySource(ramp, rate=rate, channels=channels,
                                    block=BLOCK), sample_rate=rate)
    out = pull(effect, frames, channels).reshape(-1)
    reference = sd.audioecho.FeedbackDelay(
        sample_rate=rate, channel_count=channels, max_delay_ms=251.0,
        delay_ms=law_frames(135.0, rate) * 1000.0 / rate, feedback=0.0,
        mix=0.35, loop_drive=0.15, wow_hz=0.7, wow_depth_ms=law_wow_ms(1.0),
        delay_slew=0.1875)
    reference.play(probes.ArraySource(ramp, rate=rate, channels=channels,
                                      block=BLOCK))
    ref = array("h")
    while len(ref) < frames * channels:
        data = bytes(audiocore.get_buffer(reference)[1])
        if not data:
            break
        ref.extend(memoryview(data).cast("h"))
    ref = np.array(ref[:frames * channels], dtype=np.int16)
    return int(np.count_nonzero(out != ref))


def t4_ratio(cls, tone_hz, rate=RATE):
    """(freqs, dB): the click response at 8 192 LSB with Tone at `tone_hz`
    over the same class's Tone-out response, one pass, wet only,
    Saturation 0, Wow 0, Time 135 ms, a 65 536-point FFT."""
    T = law_frames(135.0, rate)
    size = 65536
    n = T + size
    x = np.zeros(n)
    x[0] = 8192
    common = {"time_ms": 135.0, "level": 2.0, "saturation": 0.0,
              "wow_cents": 0.0, "repeats": 0.0}
    y_in = render(cls, x, rate, 2, tone_hz=tone_hz, **common)[:, 0]
    y_out = render(cls, x, rate, 2, tone_hz=20000.0, **common)[:, 0]
    a = np.abs(np.fft.rfft(y_in[T - 32:T - 32 + size].astype(float)))
    b = np.abs(np.fft.rfft(y_out[T - 32:T - 32 + size].astype(float)))
    freqs = np.fft.rfftfreq(size, 1.0 / rate)
    return freqs, 20.0 * np.log10(np.maximum(a, 1e-12) / np.maximum(b, 1e-12))


def half_power_hz(freqs, db):
    """The first -3.01 dB crossing, interpolated; `None` below Nyquist
    never."""
    below = np.nonzero(db[1:] < -3.0103)[0]
    if not len(below):
        return None
    i = int(below[0]) + 1
    f0, f1, d0, d1 = freqs[i - 1], freqs[i], db[i - 1], db[i]
    return float(f0 + (f1 - f0) * (-3.0103 - d0) / (d1 - d0))


def t4_corner(cls, tone_hz, label, rate=RATE, passband=False):
    """The half-power point within +-10 % of the cell's `label`; with
    `passband`, 30 Hz within 0.05 dB, 1 kHz within 0.1 dB and nothing more
    than 3.1 dB down in 30 Hz-15 kHz."""
    freqs, db = t4_ratio(cls, tone_hz, rate)
    corner = half_power_hz(freqs, db)
    passed = corner is not None and abs(corner / label - 1.0) <= 0.10
    values = {"corner": corner}
    if passband:
        at = lambda hz: float(db[int(np.argmin(np.abs(freqs - hz)))])  # noqa: E731
        band = (freqs >= 30.0) & (freqs <= 15000.0)
        values.update(at30=at(30.0), at1k=at(1000.0),
                      worst=float(db[band].min()))
        passed = (passed and abs(values["at30"]) <= 0.05
                  and abs(values["at1k"]) <= 0.1 and values["worst"] >= -3.1)
    values["passed"] = passed
    return values


def t4_measure(cls, rate=RATE):
    """The out stop byte-identical to no `damping_hz`, and the 15 kHz and
    2 kHz corners."""
    differing = t4_out_differing(cls, rate)
    top = t4_corner(cls, 15000.0, 15000.0, rate, passband=True)
    bottom = t4_corner(cls, 2000.0, 2000.0, rate)
    return {"passed": differing == 0 and top["passed"] and bottom["passed"],
            "differing": differing, "top": top, "bottom": bottom}


# --------------------------------------------------------------------------
# T5: Wow's cents are real cents


def t5_cents(cls, rate=RATE, amp=12000, saturation=0.15, **options):
    """The repeat's pitch deviation at the 0.7 Hz wow rate, rising side, in
    cents: 440 Hz, Level 2, Repeats 0, Tone out, Time 135 ms, 2 s from the
    first repeat; the kit's `instantaneous_hz`, 5 % trimmed at each end,
    least squares on a constant plus a cosine and a sine at 0.7 Hz."""
    T = law_frames(135.0, rate)
    n = T + 2 * rate
    x = amp * np.sin(2.0 * math.pi * 440.0 * np.arange(n) / rate)
    options.setdefault("time_ms", 135.0)
    y = render(cls, x, rate, 2, macros={LEVEL_I: 127}, repeats=0.0,
               saturation=saturation, **options)[:, 0].astype(float)
    f = instantaneous_hz(y[T + 64:], rate)
    edge = int(0.05 * len(f))
    f = f[edge:len(f) - edge]
    t = (np.arange(len(f)) + edge) / float(rate)
    angle = 2.0 * math.pi * 0.7 * t
    design = np.vstack([np.ones(len(f)), np.cos(angle), np.sin(angle)]).T
    coef = np.linalg.lstsq(design, f, rcond=None)[0]
    return 1200.0 * math.log(1.0 + math.hypot(coef[1], coef[2]) / coef[0],
                             2.0)


def t5_measure(cls, rate=RATE):
    """1.0 +- 0.25 cents at the default, 3.5 +- 0.5 at the top, under 0.05
    at zero."""
    default = t5_cents(cls, rate)
    top = t5_cents(cls, rate, wow_cents=3.5)
    zero = t5_cents(cls, rate, wow_cents=0.0)
    passed = (abs(default - 1.0) <= 0.25 and abs(top - 3.5) <= 0.5
              and zero < 0.05)
    return {"passed": passed, "default": default, "top": top, "zero": zero}


# --------------------------------------------------------------------------
# Tier 1 helpers


def tail_measure(cls, rate=RATE, burst_ms=50.0, burst_lsb=32767,
                 **options):
    """A full-scale DC burst, then silence: the frames from the burst's end
    to the output's last non-zero frame, against the declared
    `tail_samples`."""
    probe = cls(silence_src(64, 2, rate), sample_rate=rate, **options)
    declared = probe.tail_samples
    probe.deinit()
    burst = int(burst_ms * rate / 1000.0)
    n = burst + declared + rate // 2
    x = np.zeros(n)
    x[:burst] = burst_lsb
    y = render(cls, x, rate, 2, **options)[:, 0]
    nonzero = np.nonzero(y[burst:])[0]
    last = int(nonzero[-1]) + 1 if len(nonzero) else 0
    return {"passed": 0 < last <= declared, "declared": declared,
            "last": last, "held": int(np.abs(y[-rate // 4:]).max())}


def railed_samples(cls, dbfs, seconds=4.0, rate=RATE, **options):
    """`noise_det` at `dbfs` peak, 48 kHz stereo: output samples on the
    int16 rail that are not on it in the source."""
    frames = int(seconds * rate)
    data = probes.noise_det(frames=frames, dbfs=dbfs, channels=2)
    effect = cls(probes.ArraySource(data, rate=rate, channels=2,
                                    block=BLOCK), sample_rate=rate, **options)
    out = pull(effect, frames, 2).reshape(-1).astype(np.int64)
    src = np.array(data, dtype=np.int64)
    rail = (out >= 32767) | (out <= -32768)
    return int(np.count_nonzero(rail & ~((src >= 32767) | (src <= -32768))))


# --------------------------------------------------------------------------
# Reachability: what the node is handed at the position walked


class NodeSpy:
    """While active, every `audioecho.FeedbackDelay.set` call records its
    options on the node as `_handed` (the latest value of each)."""

    def __enter__(self):
        node_class = sd.audioecho.FeedbackDelay
        original = node_class.set
        self._restore = (node_class, original)

        def watched(node, **options):
            if not hasattr(node, "_handed"):
                node._handed = {}
            node._handed.update(options)
            return original(node, **options)

        node_class.set = watched
        return self

    def __exit__(self, *exc):
        node_class, original = self._restore
        node_class.set = original
        return False


def read_landing_error(effect):
    """The handed delay's whole frames against the law's for the Time the
    knob (or the constructor) names."""
    rate = effect._sample_rate
    handed = effect._delay._handed["delay_ms"]
    return (int(math.floor(handed * rate / 1000.0 + 0.5))
            - law_frames(effect._time_ms(), rate))


def read_floor(effect):
    """(Repeats at its 0 stop, the handed feedback)."""
    return (effect._macros[REPEATS_I] <= 0.0,
            round(float(effect._delay._handed["feedback"]), 4))


def read_pan(effect):
    return float(effect._delay._handed.get("input_pan", 0.0))


def read_damping(effect):
    return round(float(effect._delay._handed["damping_hz"]), 2)


def read_wow_ratio(effect):
    """The handed `wow_depth_ms` against the law at the knob's cents."""
    handed = float(effect._delay._handed["wow_depth_ms"])
    law = law_wow_ms(3.5 * effect._macros[WOW_I])
    if law == 0.0:
        return 1.0 if handed == 0.0 else 0.0
    return round(handed / law, 4)


#: (name, fault, reading, rates, constructor options for both builds).
REACH_WALKS = (
    ("Frames441Slapback", Frames441Slapback, read_landing_error,
     (48000, 22050), {}),
    ("FloorSlapback", FloorSlapback, read_floor, RATES, {}),
    ("PannedSlapback", PannedSlapback, read_pan, RATES, {}),
    ("OpenTopSlapback", OpenTopSlapback, read_damping, (48000, 44100), {}),
    ("RawToneSlapback", RawToneSlapback, read_damping, RATES,
     {"tone_hz": 15000.0}),
    ("NoTwoPiSlapback", NoTwoPiSlapback, read_wow_ratio, RATES, {}),
)


def reach(faulted, reading, rate, ctor):
    def build(cls):
        return cls(silence_src(512, 2, rate), sample_rate=rate, **ctor)

    with NodeSpy():
        return kit_faults.fault_reachability(SlapbackDelay, faulted, reading,
                                             build)


# --------------------------------------------------------------------------
# The surface


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = SlapbackDelay
        self.assertEqual(cls.MACRO_LABELS,
                         ("Time", "Level", "Saturation", "Tone", "Wow",
                          "Repeats"))
        self.assertEqual(len(cls.PATCHES), 6)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TIER, _component.AUDIODSP)
        self.assertEqual(cls.REQUIRES, ("audioecho",))
        effect = cls(silence_src(512), sample_rate=RATE)
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(0, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)

    def test_parked_not_served(self):
        import audioeffects
        self.assertNotIn("SlapbackDelay", rebuilt.ADOPTED)
        self.assertIn("SlapbackDelay", rebuilt.parked())
        self.assertIsNot(audioeffects.SlapbackDelay, SlapbackDelay)

    def test_patches_are_the_dossier_settings_on_the_grid(self):
        for index, (name, values) in enumerate(DOSSIER_PATCHES):
            label, midi = SlapbackDelay.PATCHES[index]
            self.assertEqual(label, name)
            self.assertEqual(midi, tuple(_component.macro_of(span, value)
                                         for span, value in
                                         zip(DOSSIER_SPANS, values)))

    def test_patch_0_is_the_constructor_grid(self):
        effect = SlapbackDelay(silence_src(512), sample_rate=RATE)
        grid = SlapbackDelay.PATCHES[0][1]
        for index, expected in enumerate(grid):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_time_lands_on_a_whole_frame(self):
        # 135 ms is 6 480 / 5 954 / 2 977 frames (5 953.5 at 44.1 kHz lands
        # up); the stops 1 920 / 1 764 / 882 and 12 000 / 11 025 / 5 513.
        for rate, frames in ((48000, (6480, 1920, 12000)),
                             (44100, (5954, 1764, 11025)),
                             (22050, (2977, 882, 5513))):
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            got = [effect._frames]
            for midi in (0, 127):
                effect.set_macro(TIME_I, midi)
                got.append(effect._frames)
            self.assertEqual(tuple(got), frames, rate)
            for midi in range(128):
                effect.set_macro(TIME_I, midi)
                self.assertEqual(effect._frames,
                                 law_frames(law_time_ms(midi), rate))
                self.assertEqual(effect._node_ms,
                                 effect._frames * 1000.0 / rate)

    def test_the_wow_map_and_its_ceiling(self):
        self.assertAlmostEqual(sd.wow_depth_ms(1.0), 0.13137, places=5)
        self.assertAlmostEqual(sd.wow_depth_ms(3.5), 0.46012, places=5)
        self.assertEqual(sd.wow_depth_ms(0.0), 0.0)
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               wow_cents=10.0)
        self.assertAlmostEqual(effect._wow_ms, law_wow_ms(3.5), places=12)
        for midi in range(128):
            effect.set_macro(WOW_I, midi)
            self.assertAlmostEqual(effect._wow_ms,
                                   law_wow_ms(3.5 * midi / 127.0), places=12)

    def test_tone_stops_and_the_22k_clamp(self):
        for rate in RATES:
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            dampings = [effect._tone_damping(m / 127.0) for m in range(128)]
            self.assertEqual(dampings[127], 0.0)
            if rate == 22050:
                self.assertLess(dampings[93], dampings[94])
                self.assertEqual(len(set(dampings[94:127])), 1)
                self.assertAlmostEqual(dampings[94], 6183.68, places=2)
            else:
                self.assertTrue(all(b > a for a, b in
                                    zip(dampings[:126], dampings[1:127])))
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               tone_hz=15000.0)
        self.assertAlmostEqual(effect._damping, 11566.93, places=2)

    def test_tail_samples_follows_time_tone_wow_and_repeats(self):
        # laps x (reach + ceil(wow) + 1 + memory); one lap at Repeats 0.
        for rate, declared in ((48000, 6488), (44100, 5961), (22050, 2981)):
            effect = SlapbackDelay(silence_src(64, 2, rate), sample_rate=rate)
            self.assertEqual(effect.tail_samples, declared, rate)
            self.assertEqual(declared, law_frames(135.0, rate)
                             + law_wow_frames(1.0, rate) + 1)
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE)
        self.assertEqual(sd.laps_to_zero(0.35), 11)
        self.assertEqual(sd.laps_to_zero(0.6), 21)
        effect.set_macro(REPEATS_I, 127)
        self.assertEqual(effect.tail_samples, 21 * 6488)
        # A falling move walks from the old Time, so the old Time stays in
        # the bound; a reset lands the head on patch 0.
        effect.set_macro(TIME_I, 0)
        self.assertEqual(effect.tail_samples, 21 * 6488)
        effect.set_macro(TIME_I, 127)
        self.assertEqual(effect.tail_samples, 21 * (12000 + 7 + 1))
        effect.reset()
        self.assertEqual(effect.tail_samples,
                         law_frames(law_time_ms(84), RATE)
                         + law_wow_frames(3.5 * 36 / 127.0, RATE) + 1)
        # Tone in at Repeats 0.5: the node is handed the stall window's
        # nearer edge, and the bound is finite.
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               tone_hz=2000.0, repeats=0.5)
        self.assertLess(effect._feedback, 0.5)
        self.assertGreater(effect._feedback, 0.5 - 2.5e-5)
        self.assertAlmostEqual(effect.get_macro(REPEATS_I), 127 * 0.5 / 0.6)
        self.assertEqual(effect.tail_samples, 105184)

    def test_constructor_clamps_and_nan(self):
        nan = float("nan")
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               time_ms=nan, level=nan, saturation=nan,
                               tone_hz=nan, wow_cents=nan, repeats=nan)
        self.assertEqual([effect.macro(i) for i in (1, 2, 5)],
                         [0.35, 0.15, 0.0])
        self.assertEqual(effect._frames, 6480)
        self.assertEqual(effect._damping, 0.0)
        self.assertAlmostEqual(effect._wow_ms, law_wow_ms(1.0))
        for options, frames in (({"time_ms": 0.0, "tone_hz": 0.0}, 1920),
                                ({"time_ms": -5.0, "tone_hz": -1.0}, 1920),
                                ({"time_ms": 900.0, "tone_hz": 1e6}, 12000)):
            effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                                   **options)
            self.assertEqual(effect._frames, frames, options)
            self.assertEqual(effect._damping, 0.0, options)
        effect = SlapbackDelay(silence_src(64), sample_rate=RATE,
                               tone_hz=100.0, repeats=2.0, level=5.0)
        self.assertEqual(effect.get_macro(TONE_I), 0.0)
        self.assertEqual(effect.get_macro(REPEATS_I), 127.0)
        self.assertEqual(effect.get_macro(LEVEL_I), 127.0)


# --------------------------------------------------------------------------
# Tier 2 rows


class T1OneRepeat(unittest.TestCase):
    def test_defaults_three_rates_stereo_and_mono(self):
        for rate in RATES:
            for channels in (2, 1):
                result = t1_measure(SlapbackDelay, rate, channels)
                self.assertTrue(result["passed"], (rate, channels, result))
        result = t1_measure(SlapbackDelay, RATE, 2, click_lsb=328)
        self.assertTrue(result["passed"], result)
        result = t1_measure(SlapbackDelay, RATE, patch=0)
        self.assertTrue(result["passed"], result)

    def test_no_second_repeat_at_the_stops_and_patches(self):
        for options in ({"time_ms": 40.0}, {"time_ms": 250.0},
                        {"saturation": 1.0}, {"tone_hz": 2000.0},
                        {"wow_cents": 3.5}, {"wow_cents": 0.0},
                        {"level": 2.0}, {"patch": 1}, {"patch": 2},
                        {"patch": 3}, {"patch": 5}):
            result = t1_measure(SlapbackDelay, RATE, delay_bar=False,
                                **options)
            self.assertTrue(result["passed"], (options, result))

    def test_the_control_moves(self):
        for options in ({"repeats": 0.35}, {"patch": 4}, {"repeats": 0.6}):
            result = t1_control(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))

    def test_frames_at_the_wrong_rate_are_red(self):
        result = t1_measure(Frames441Slapback, RATE)
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(result["delay_ms"], 124.11, delta=0.05)

    def test_a_loop_gain_floor_is_red(self):
        result = t1_measure(FloorSlapback, RATE)
        self.assertFalse(result["passed"])
        self.assertLess(result["second_db"], -20.0)
        self.assertGreater(result["second_db"], -30.0)


class T2Comb(unittest.TestCase):
    def test_the_defaults_and_the_stops(self):
        for rate in RATES:
            result = t2_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        for options in ({"time_ms": 40.0, "wow_cents": 0.0},
                        {"time_ms": 250.0, "wow_cents": 0.0},
                        {"time_ms": 137.0, "wow_cents": 0.0}, {"patch": 0}):
            result = t2_measure(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))
        result = t2_measure(SlapbackDelay, RATE, click_lsb=3277)
        self.assertTrue(result["passed"], result)

    def test_frames_at_the_wrong_rate_are_red(self):
        result = t2_measure(Frames441Slapback, RATE)
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(result["deviations"][0], 8.77, delta=0.05)


class T3Mono(unittest.TestCase):
    def test_the_defaults_the_corner_and_the_patches(self):
        for rate in RATES:
            result = t3_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        for options in ({"repeats": 0.6, "saturation": 1.0,
                         "tone_hz": 2000.0, "wow_cents": 3.5},
                        {"patch": 2}, {"patch": 4}, {"patch": 5},
                        {"time_ms": 40.0}, {"time_ms": 250.0}):
            result = t3_measure(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))

    def test_a_panned_repeat_is_red(self):
        result = t3_measure(PannedSlapback, RATE)
        self.assertFalse(result["passed"])
        self.assertGreater(result["lr"], 0)


class T4Tone(unittest.TestCase):
    def test_out_and_the_corners_at_48k_and_44k(self):
        for rate in (48000, 44100):
            result = t4_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))

    def test_the_grid_cells(self):
        for rate in (48000, 44100):
            for midi in (51, 111, 126):
                label = 2000.0 * 10.0 ** (midi / 127.0)
                result = t4_corner(SlapbackDelay, label, label, rate)
                self.assertTrue(result["passed"], (rate, midi, result))

    def test_the_22k_cells(self):
        self.assertEqual(t4_out_differing(SlapbackDelay, 22050), 0)
        for label in (2000.0, 2000.0 * 10.0 ** (51 / 127.0)):
            result = t4_corner(SlapbackDelay, label, label, 22050)
            self.assertTrue(result["passed"], (label, result))

    def test_an_open_top_stop_is_red_at_the_defaults(self):
        for rate in (48000, 44100):
            self.assertGreater(t4_out_differing(OpenTopSlapback, rate), 0)
            self.assertFalse(t4_measure(OpenTopSlapback, rate)["passed"])

    def test_a_raw_tone_is_red_at_the_15k_cell(self):
        for rate in (48000, 44100):
            result = t4_corner(RawToneSlapback, 15000.0, 15000.0, rate,
                               passband=True)
            self.assertFalse(result["passed"])
            self.assertIsNone(result["corner"])


class T5Wow(unittest.TestCase):
    def test_zero_default_and_top(self):
        for rate in RATES:
            result = t5_measure(SlapbackDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        for saturation in (0.0, 0.15):
            self.assertLess(abs(t5_cents(SlapbackDelay, RATE, amp=328,
                                         saturation=saturation) - 1.0), 0.25)
        cents = t5_cents(SlapbackDelay, RATE, patch=0)
        self.assertLess(abs(cents - 1.0), 0.25)

    def test_the_ceiling(self):
        cents = t5_cents(SlapbackDelay, RATE, wow_cents=10.0)
        self.assertLess(cents, 4.0)
        self.assertLess(abs(cents - 3.5), 0.5)

    def test_a_map_without_its_two_pi_is_red(self):
        result = t5_measure(NoTwoPiSlapback, RATE)
        self.assertFalse(result["passed"])
        self.assertGreater(result["default"], 5.0)


# --------------------------------------------------------------------------
# Tier 1, the fast half


class Tier1Fast(unittest.TestCase):
    def test_level_zero_is_a_wire_on_the_full_scale_ramp(self):
        corner = {"repeats": 0.6, "saturation": 1.0, "tone_hz": 2000.0,
                  "wow_cents": 3.5, "level": 0.0}
        for rate in RATES:
            for channels in (2, 1):
                for time_ms in (40.0, 250.0):
                    frames = law_frames(time_ms, rate) * 3
                    ramp = probes.ramp_fs(frames=frames, channels=channels)
                    effect = SlapbackDelay(
                        probes.ArraySource(ramp, rate=rate,
                                           channels=channels, block=BLOCK),
                        sample_rate=rate, time_ms=time_ms, **corner)
                    out = pull(effect, frames, channels).reshape(-1)
                    self.assertTrue(np.array_equal(
                        out, np.array(ramp, dtype=np.int16)),
                        (rate, channels, time_ms))

    def test_the_dry_is_unity_until_the_repeat(self):
        # Level 1.0 and grid 63 (0.992): the first T - 24 frames are the
        # source, byte for byte, with the wow at its top.
        for level in (1.0, 2.0 * 63 / 127.0):
            T = law_frames(40.0, RATE)
            ramp = probes.ramp_fs(frames=T * 2, channels=2)
            effect = SlapbackDelay(
                probes.ArraySource(ramp, rate=RATE, channels=2, block=BLOCK),
                sample_rate=RATE, time_ms=40.0, level=level, wow_cents=3.5,
                repeats=0.6, saturation=1.0)
            out = pull(effect, T * 2, 2).reshape(-1)
            window = (T - 24) * 2
            self.assertTrue(np.array_equal(
                out[:window], np.array(ramp, dtype=np.int16)[:window]))

    def test_silence_stays_silence(self):
        effect = SlapbackDelay(silence_src(RATE), sample_rate=RATE,
                               repeats=0.6, level=2.0, tone_hz=2000.0,
                               saturation=1.0, wow_cents=3.5)
        self.assertEqual(int(np.abs(pull(effect, RATE)).max()), 0)

    def test_the_tail_reaches_exact_zero_inside_tail_samples(self):
        for rate in RATES:
            for level in (0.35, 2.0):
                result = tail_measure(SlapbackDelay, rate, level=level)
                self.assertTrue(result["passed"], (rate, level, result))
        for options in ({"repeats": 0.35, "level": 2.0},
                        {"repeats": 0.6, "level": 2.0},
                        {"repeats": 0.6, "level": 2.0, "saturation": 1.0,
                         "tone_hz": 2000.0, "wow_cents": 3.5},
                        {"time_ms": 250.0, "wow_cents": 3.5,
                         "repeats": 0.6, "level": 2.0}):
            result = tail_measure(SlapbackDelay, RATE, **options)
            self.assertTrue(result["passed"], (options, result))

    def test_a_tail_without_the_wow_is_red(self):
        result = tail_measure(NoWowTailSlapback, RATE, level=2.0)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["last"], result["declared"])

    def _stall(self, cls):
        """Repeats 0.5, Tone 2 kHz, Level 2, Saturation 0: a 2 LSB DC for
        1 s, then 3 s of silence."""
        values = np.zeros(4 * RATE)
        values[:RATE] = 2.0
        source, _ = to_source(values)
        effect = cls(source, sample_rate=RATE, repeats=0.5, tone_hz=2000.0,
                     level=2.0, saturation=0.0)
        declared = effect.tail_samples
        y = pull(effect, len(values))[:, 0]
        nonzero = np.nonzero(y[RATE:])[0]
        last = int(nonzero[-1]) + 1 if len(nonzero) else 0
        return declared, last, int(np.abs(y[-RATE // 4:]).max())

    def test_the_stall_window_is_stepped_clear(self):
        declared, last, held = self._stall(SlapbackDelay)
        self.assertEqual(held, 0)
        self.assertLessEqual(last, declared)
        _declared, _last, held = self._stall(RawFeedbackSlapback)
        self.assertEqual(held, 1)

    def _tone_back_in(self, cls, rate=RATE, channels=2, level=2.0):
        """300 Hz at 30 000 LSB for 0.5 s with Tone 2 kHz, Tone out, 2 s of
        silence, then Tone to MIDI 0: the output's peak after that move."""
        loud = (rate // 2) // BLOCK * BLOCK
        back = (loud + 2 * rate) // BLOCK * BLOCK
        values = np.zeros(back + rate // 4)
        values[:loud] = 30000 * np.sin(2 * math.pi * 300.0
                                       * np.arange(loud) / rate)
        source, _ = to_source(values, channels, rate)
        effect = cls(source, sample_rate=rate, tone_hz=2000.0, level=level)

        def move(frame):
            if frame == loud:
                effect.set_macro(TONE_I, 127)
            elif frame == back:
                effect.set_macro(TONE_I, 0)

        y = pull(effect, len(values), channels, on_block=move)
        return int(np.abs(y[back:]).max())

    def test_tone_back_in_after_silence_stays_silent(self):
        for rate in RATES:
            for channels in (2, 1):
                self.assertEqual(self._tone_back_in(SlapbackDelay, rate,
                                                    channels), 0,
                                 (rate, channels))
        self.assertEqual(self._tone_back_in(SlapbackDelay, level=0.35), 0)
        # Planted: the out stop frozen at 0 plays the held state back.
        self.assertGreater(self._tone_back_in(FrozenToneSlapback), 20000)
        self.assertGreater(self._tone_back_in(FrozenToneSlapback,
                                              level=0.35), 5000)

    def test_tone_out_hands_no_filter_until_tone_has_been_in(self):
        with NodeSpy():
            for rate in RATES:
                effect = SlapbackDelay(silence_src(64, 2, rate),
                                       sample_rate=rate)
                self.assertEqual(effect._delay._handed["damping_hz"], 0.0)
                effect.set_macro(TONE_I, 0)
                effect.set_macro(TONE_I, 127)
                self.assertEqual(effect._delay._handed["damping_hz"],
                                 32.0 * rate)
                self.assertIsNotNone(effect.tail_samples)
                effect.reset()
                self.assertEqual(effect._delay._handed["damping_hz"], 0.0)
                effect = SlapbackDelay(silence_src(64, 2, rate),
                                       sample_rate=rate, patch=5)
                effect.program_change(0)
                self.assertEqual(effect._delay._handed["damping_hz"],
                                 32.0 * rate)

    def test_a_wow_move_steps_as_the_docstring_says(self):
        # The node takes a new wow depth at once; the docstring states the
        # step. 997 Hz at 12 000 LSB, Level 2, Wow 36 -> 73 at frame 15 616.
        at = 15616
        values = 12000 * np.sin(2 * math.pi * 997.0 * np.arange(RATE) / RATE)
        steps = []
        for target in (73, 127):
            source, _ = to_source(values)
            effect = SlapbackDelay(source, sample_rate=RATE, level=2.0)
            effect.set_macro(WOW_I, 36 if target == 73 else 0)

            def move(frame, target=target, effect=effect):
                if frame == at:
                    effect.set_macro(WOW_I, target)

            y = pull(effect, RATE, on_block=move)[:, 0].astype(int)
            steady = int(np.abs(np.diff(y[at - 3000:at - 1])).max())
            steps.append((steady, int(np.abs(y[at] - y[at - 1]))))
        self.assertEqual(steps[0], (1565, 7684))
        self.assertEqual(steps[1][1], 23037)

    def _walk_tail(self, cls):
        """250 ms of 997 Hz, then Time 250 -> 40 ms on the tone's last
        block, Repeats 0, Level 2."""
        tone = int(0.25 * RATE) // BLOCK * BLOCK
        values = np.zeros(tone + RATE)
        values[:tone] = 12000 * np.sin(2 * math.pi * 997.0
                                       * np.arange(tone) / RATE)
        source, _ = to_source(values)
        effect = cls(source, sample_rate=RATE, time_ms=250.0, level=2.0)
        seen = {}

        def move(frame):
            if frame == tone:
                effect.set_macro(TIME_I, 0)
                seen["declared"] = effect.tail_samples

        y = pull(effect, len(values), on_block=move)[:, 0]
        last = int(np.nonzero(y[tone:])[0][-1]) + 1
        return seen["declared"], last

    def test_a_falling_walk_keeps_the_old_time_in_the_tail(self):
        declared, last = self._walk_tail(SlapbackDelay)
        self.assertGreater(last, 4000)
        self.assertLessEqual(last, declared)
        declared, last = self._walk_tail(TargetOnlyTailSlapback)
        self.assertGreater(last, declared)

    def test_reset_empties_the_line(self):
        values = np.zeros(RATE)
        values[256:2304] = 12000 * np.sin(2 * math.pi * 997.0
                                          * np.arange(2048) / RATE)
        source, _ = to_source(values)
        effect = SlapbackDelay(source, sample_rate=RATE, repeats=0.6,
                               level=2.0)
        pull(effect, 2304)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(int(np.abs(pull(effect, RATE // 2)).max()), 0)

    def test_deinit_leaves_the_source(self):
        source, _ = to_source(8000 * np.sin(2 * math.pi * 440.0
                                            * np.arange(1024) / RATE))
        effect = SlapbackDelay(source, sample_rate=RATE)
        pull(effect, 256)
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(source)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)

    def test_click_delay_is_zero(self):
        for rate in (48000, 44100):
            values = np.zeros(2048)
            values[10] = 30000
            y = render(SlapbackDelay, values, rate)[:, 0]
            self.assertEqual(int(np.argmax(np.abs(y))), 10)
            self.assertEqual(int(y[10]), 30000)

    def test_the_transport_is_never_read(self):
        reads = []

        def transport():
            reads.append(1)
            return (True, 0.0, 120.0, 4, 4)
        effect = SlapbackDelay.create(silence_src(512), RATE,
                                      transport=transport)
        for index in range(6):
            effect.set_macro(index, 127)
        effect.program_change(4)
        effect.reset()
        pull(effect, 256)
        self.assertEqual(reads, [])


class InputCeiling(unittest.TestCase):
    """The docstring's ceiling on `noise_det`, 48 kHz stereo, 4 s: the
    defaults clean at -2.5 dBFS peak and not at -2.4, patch 2 (Doubling,
    the first shipped patch to rail) clean at -3.4 and not at -3.3."""

    def test_the_stated_ceiling_is_clean_and_just_over_is_not(self):
        for options, ceiling, over in (({}, -2.5, -2.4),
                                       ({"patch": 2}, -3.4, -3.3)):
            self.assertEqual(railed_samples(SlapbackDelay, ceiling,
                                            **options), 0, options)
            self.assertGreater(railed_samples(SlapbackDelay, over,
                                              **options), 0, options)


# --------------------------------------------------------------------------
# The two checks every planted fault and every row is held to


class FaultsAreUnreachable(unittest.TestCase):
    """Every fault's reachability walk, reading what the node is handed at
    each position, at the rates its docstring names."""

    CHECKED = 6 * 17 + 6

    def test_every_fault_is_off_the_surface(self):
        for name, faulted, reading, rates, ctor in REACH_WALKS:
            for rate in rates:
                with self.subTest(fault=name, rate=rate):
                    result = reach(faulted, reading, rate, ctor)
                    self.assertEqual(result["checked"], self.CHECKED)

    def test_the_rates_left_out_are_left_out_for_their_stated_reason(self):
        # At 44.1 kHz the 44.1 kHz landing is the right one: inert.
        with self.assertRaises(kit_faults.FaultInert):
            reach(Frames441Slapback, read_landing_error, 44100, {})
        # At 22.05 kHz grid 94-126 hand the pre-warped clamp too.
        with self.assertRaises(kit_faults.FaultReachable):
            reach(OpenTopSlapback, read_damping, 22050, {})
        # The raw Tone is silent at the defaults, where Tone is out.
        with self.assertRaises(kit_faults.FaultInert):
            reach(RawToneSlapback, read_damping, RATE, {})


class NullBuildRed(unittest.TestCase):
    """Every demonstrated row goes red on the class built as a wire, beside
    a control on the real class that must pass."""

    def test_every_row_is_red_on_a_wire(self):
        for name, measure in (("T1", t1_measure), ("T2", t2_measure),
                              ("T3", t3_measure), ("T4", t4_measure),
                              ("T5", t5_measure)):
            with self.subTest(row=name):
                result = kit_faults.null_build_red(
                    SlapbackDelay, measure, label="SlapbackDelay %s" % name)
                self.assertFalse(result["null"]["passed"], name)
                self.assertTrue(result["control"]["passed"], name)


if __name__ == "__main__":
    unittest.main()
