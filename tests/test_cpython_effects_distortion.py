"""`Distortion`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Distortion.md`.
Exhaustive rate coverage lives in the evidence pack. This file stays at
48 kHz except where a test is about rate handling.

Every trait here is read at the **shipped default first** - `create()` with
no arguments, or for a `scoop` row `create(character=1.0)` - and every
planted fault is one that goes red there. A fault that only fires at a held
point demonstrates the held point, not the class anyone starts from.
"""

import array
import math
import os
import sys
import unittest

import audiocore
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))

from audioeffects import _component                            # noqa: E402
from audioeffects import distortion as rebuilt                 # noqa: E402
from tools import effect_measurements as kit                   # noqa: E402
import kit_faults as faults                                    # noqa: E402
import kit_probes                                              # noqa: E402

VENDOR = "PyDevices"

Distortion = rebuilt.Distortion
RATE = 48000
DIST, FILT, TONE, VOL, MIX, CHAR, CEIL, BOOST, ASYM, BODY = range(10)


def silence(frames=4096, channels=2, rate=RATE):
    return audiocore.RawSample(array.array("h", bytes(2 * channels * frames)),
                               sample_rate=rate, channel_count=channels)


def sine(hz, frames, rate=RATE, channels=2, peak=0.1):
    values = array.array("h")
    amp = int(round(peak * 32767.0))
    for index in range(frames):
        value = int(round(amp * math.sin(2.0 * math.pi * hz * index / rate)))
        for _ in range(channels):
            values.append(value)
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def pcm(node, frames, channels=2):
    want = frames * channels * 2
    out = bytearray()
    while len(out) < want:
        chunk = bytes(audiocore.get_buffer(node)[1])
        if not chunk:
            break
        out += chunk
    return bytes(out[:want])


def built(source=None, rate=RATE, cls=None, **options):
    return (cls or Distortion).create(source or silence(rate=rate), rate,
                                      **options)


def render(cls, hz, peak, frames=8192, rate=RATE, macros=None, **options):
    src = sine(hz, frames, rate=rate, peak=peak)
    effect = (cls or Distortion).create(src, rate, **options)
    for key, value in (macros or {}).items():
        effect.set_macro(key, value)
    data = pcm(effect.output, frames)
    effect.deinit()
    return kit.Render.from_pcm(data, rate, 2)


def level_db(cls, hz, peak=0.005, frames=8192, rate=RATE, macros=None,
             **options):
    """Settled output peak against input peak, in dB."""
    rnd = render(cls, hz, peak, frames, rate, macros, **options)
    x = rnd.float[frames // 2:, 0]
    return 20.0 * math.log10(max(float(np.max(np.abs(x))), 1e-9) / peak)


#: F1's material. The row's held line says "level under 0.30 V pre-clip",
#: and at Distortion 10 % this input puts 0.213 V there (0.005, which the
#: first fix round used, puts **0.532 V** on it - outside the row's own
#: condition, which is why that reading sat 0.2 dB from the band edge).
F1_PEAK = 0.002


def tilt_db(cls, frames=8192, rate=RATE, macros=None, peak=F1_PEAK,
            **options):
    """100 Hz against 1 kHz - the Rat's feedback-leg tilt."""
    return (level_db(cls, 100.0, peak=peak, frames=frames, rate=rate,
                     macros=macros, **options)
            - level_db(cls, 1000.0, peak=peak, frames=frames, rate=rate,
                       macros=macros, **options))


def thd_db(cls, hz=1000.0, peak=0.1, frames=8192, rate=RATE, harmonics=8,
           macros=None, **options):
    rnd = render(cls, hz, peak, frames, rate, macros, **options)
    return kit.spectrum(rnd, hz, harmonics=harmonics)["values"]["thd_db"]


def alias_floor_db(cls, hz=1010.0, peak=0.1, size=4800, rate=RATE,
                   macros=None, **options):
    """Inharmonic energy, 20 Hz - 20 kHz, against the fundamental."""
    rnd = render(cls, hz, peak, 2 * size, rate, macros, **options)
    x = rnd.float[-size:, 0].astype(np.float64)
    spec = np.abs(np.fft.rfft(x[:size]))
    bin_hz = rate / float(size)
    mask = np.ones(len(spec), dtype=bool)
    mask[:3] = False
    order = 1
    while hz * order < rate / 2.0:
        centre = int(round(hz * order / bin_hz))
        mask[max(0, centre - 2):centre + 3] = False
        order += 1
    freqs = np.arange(len(spec)) * bin_hz
    mask &= (freqs >= 20.0) & (freqs <= 20000.0)
    centre = int(round(hz / bin_hz))
    base = float(spec[max(0, centre - 2):centre + 3].max())
    total = math.sqrt(float((spec[mask] ** 2).sum()))
    return 20.0 * math.log10(max(total, 1e-12) / max(base, 1e-12))


def one_volt(cls, frames=8192, macros=None, **options):
    """`(gain, peak, h2, h3, h4)` at 1 V of pre-clip signal.

    Pre-clip volts are the jack level times the path's small-signal gain at
    1 kHz, so the gain is measured first and the input set to 1/G. The gain
    is returned because it is the measurement's own calibration: a build
    whose curve is not the diode table has a tenth of it, and reading the
    ceiling without reading the gain is what went wrong the first time.
    """
    small = render(cls, 1000.0, 50.0 / 32767.0, frames, macros=macros,
                   **options)
    x = small.float[frames // 2:, 0]
    gain = float(np.max(np.abs(x))) / (50.0 / 32767.0)
    if gain <= 1e-6:
        return 0.0, 0.0, None, None, None
    rnd = render(cls, 1000.0, min(1.0 / gain, 0.999), frames, macros=macros,
                 **options)
    y = rnd.float[frames // 2:, 0]
    try:
        harmonic = kit.spectrum(rnd, 1000.0,
                                harmonics=8)["values"]["harmonic_db"]
    except kit.SilentRenderError:
        return gain, 0.0, None, None, None
    return (gain, float(np.max(np.abs(y))), harmonic.get("h2"),
            harmonic.get("h3"), harmonic.get("h4"))


# --------------------------------------------------------------------------
# What each row holds, as macro positions applied AFTER construction - so a
# shipped patch can be read with the row's own line on top of it, which is
# the only honest way to put a patch under a row that names a held setting.
# MIDI positions are floats on purpose: 10 % of the Distortion pot is 12.7,
# not 13.

D2 = {DIST: 0.02 * 127, FILT: 0, MIX: 127, VOL: 127}
D10 = {DIST: 0.10 * 127, FILT: 0, MIX: 127, VOL: 127}
D10_CEIL1 = {DIST: 0.10 * 127, FILT: 0, MIX: 127, VOL: 127,
             CEIL: (1.0 - 0.5) / 1.5 * 127}
DMAX = {DIST: 127, FILT: 0, MIX: 127, VOL: 127}
D0 = {DIST: 0, FILT: 0, MIX: 127, VOL: 127}
D0_CLOSED = {DIST: 0, FILT: 127, MIX: 127, VOL: 127}
SCOOP_HELD = {DIST: 0, TONE: 64, ASYM: 0}


def held(macros, line):
    """The caller's positions with the row's held line on top."""
    out = dict(macros or {})
    out.update(line)
    return out


# --------------------------------------------------------------------------
# The planted faults. Each one goes red at `create()`'s own settings.

class SwapLegs(Distortion):
    """F1's fault: the two feedback-leg corners change places.

    Same kind as the trait - it is the legs, and only the legs - and the
    560 ohm leg's 60 Hz corner is not a macro, so no surface position
    reaches it.
    """

    NAME = 'Distortion'

    def _push_filter(self):
        Distortion._push_filter(self)
        f0, q = rebuilt._fo_hp(self._hz(1539.0), self._sample_rate)
        self._leg_bass.frequency = f0
        self._leg_bass.Q = q
        f0, q = rebuilt._fo_hp(self._hz(60.0), self._sample_rate)
        self._leg_treble.frequency = f0
        self._leg_treble.Q = q
        self._swapped_legs = True


class NoGBW(Distortion):
    """F2's fault: the op-amp's bandwidth pole never engages."""

    NAME = 'Distortion'

    def _push_filter(self):
        Distortion._push_filter(self)
        f0, q = rebuilt._fo_lp(self._hz(20000.0), self._sample_rate)
        self._gbw.frequency = f0
        self._gbw.Q = q
        self._no_gbw = True


class LinearClipper(Distortion):
    """F3's fault: an identity table, so the diodes never conduct."""

    NAME = 'Distortion'

    def _push_filter(self):
        Distortion._push_filter(self)
        ident = array.array("h", [
            int(round(-32767 + 65534 * i / 1023.0)) for i in range(1024)])
        self._shaper.set(curve=ident)
        self._linear = True


class NoDrive(Distortion):
    """F4's fault: the Distortion knob is severed from the clipper."""

    NAME = 'Distortion'

    def _push_filter(self):
        Distortion._push_filter(self)
        self._shaper.set(pre_gain=1.0 / rebuilt.V_SCALE)
        self._no_drive = True


class AlwaysDriven(Distortion):
    """F4's other fault: Distortion 0 still drives the clipper."""

    NAME = 'Distortion'

    def _push_filter(self):
        Distortion._push_filter(self)
        self._shaper.set(pre_gain=8.0)
        self._forced_drive = 8.0


class SecondOrderFilter(Distortion):
    """F5's fault: the Filter is a Butterworth pair, 12 dB/oct."""

    NAME = 'Distortion'

    def _push_filter(self):
        Distortion._push_filter(self)
        pot = self.macro(FILT)
        corner = 1.0 / (2.0 * math.pi
                        * (rebuilt.FILTER_R0 + pot * rebuilt.FILTER_POT)
                        * rebuilt.FILTER_C)
        self._filt.Q = 0.707
        self._filt.frequency = self._hz(corner)


class BaseRateShaper(Distortion):
    """A1's fault: oversample 1, the alias floor the trait exists to catch."""

    NAME = 'Distortion'
    OVERSAMPLE = 1


class NoOutputCap(Distortion):
    """The DS-1 as it was built the first time, with no output coupling
    capacitor - the control for the DC test, not a trait's guard."""

    NAME = 'Distortion'

    def _install_graph(self, scoop):
        Distortion._install_graph(self, scoop)
        if scoop:
            self._out_hp.mix = 0.0


class BiasedScoop(NoOutputCap):
    """`Asymmetry` as the second fix round built it: a **bias into the
    symmetric table** rather than a blend towards the asymmetric one.

    `STOCK_ASYMMETRY * macro` is a 3.5 V offset at the top of the knob,
    into a table whose diodes clip at 0.62 V, so the operating point sits
    at 0.97 of full scale and a silent input comes out at -6.8 dBFS of DC.
    This is what proves the DC and tail rows below can fail.
    """

    NAME = 'Distortion'
    STOCK_ASYMMETRY = 0.35

    def _push_scoop(self, wet_level):
        Distortion._push_scoop(self, wet_level)
        self._shaper.set(curve=self._ds1_curve,
                         bias=self.STOCK_ASYMMETRY * self.macro(8))


class BiasedScoopWithCap(Distortion):
    """The bias model *with* the second round's coupling capacitor: the
    build audit 3 measured, where the standing offset is held back to the
    biquad's dead band and the step from silence to a note is not."""

    NAME = 'Distortion'
    STOCK_ASYMMETRY = 0.35

    def _push_scoop(self, wet_level):
        Distortion._push_scoop(self, wet_level)
        self._shaper.set(curve=self._ds1_curve,
                         bias=self.STOCK_ASYMMETRY * self.macro(8))


class NoBoost(Distortion):
    """SC3's fault: the DS-1's booster is out of circuit."""

    NAME = 'Distortion'

    def _push_scoop(self, wet_level):
        Distortion._push_scoop(self, wet_level)
        self._shaper.set(pre_gain=1.0 / rebuilt.V_SCALE)
        self._no_boost = True


# --------------------------------------------------------------------------
# The criteria. Each one is a closure over a class so `null_build_red` can
# run it against the same class built as a wire.

def f1_criterion(cls, rate=RATE, macros=None, frames=8192, **options):
    """The dossier's F1 row, and nothing else.

    The row claims the tilt at **Distortion 2 % and 10 %** with Filter 0,
    and says in as many words that patch 0's reading "is not this row's
    claim". The fix round graded it at the default against
    `|tilt - 1.1| <= 1.0`, a band that is in no dossier, is unsourced, and
    moves with the probe level (peak 0.002 reads -0.850, peak 0.001
    -4.076). That clause is gone; the default tilt is reported, because a
    reader wants it, and barred nowhere.
    """
    held10 = tilt_db(cls, rate=rate, frames=frames, macros=held(macros, D10),
                     **options)
    held2 = tilt_db(cls, rate=rate, frames=frames, macros=held(macros, D2),
                    **options)
    at_max = tilt_db(cls, rate=rate, frames=frames, macros=held(macros, DMAX),
                     **options)
    at_default = tilt_db(cls, rate=rate, frames=frames, macros=macros,
                         **options)
    passed = (-18.0 <= held10 <= -11.0 and -17.0 <= held2 <= -11.0
              and at_max >= held10 + 5.0)
    return {"passed": passed, "held10": held10, "held2": held2,
            "at_max": at_max, "default": at_default,
            "red": [] if passed else ["tilt"]}


#: F2's contour target: 0.298 V of output peak, which Appendix A puts at
#: 0.300 V of pre-clip drive. The class's volts are its normalised scale
#: (`V_SCALE` 10 at the input, 1 V = 1.0 at the output).
F2_TARGET_PEAK = 0.0298


def equal_drive_gain(cls, hz, rate=RATE, macros=None, frames=4096,
                     target=F2_TARGET_PEAK, steps=17, **options):
    """Appendix G's equal-drive contour, which the F2 row demands by name.

    At each frequency the input is bisected until the **output** peak
    reaches 0.298 V, and the gain is `20 log10(0.300 / input peak)`. The
    row says a plain sweep "cannot be used here, nothing survives the
    clipper at 67 dB" - a fixed-input sweep reads the clipper's ceiling and
    not the contour, which is why it also moved with the probe level
    (-36.76 dB at peak 0.002, -22.18 at 0.05, both at the same setting).
    """
    def out(lsb):
        rnd = render(cls, hz, lsb / 32767.0, frames, rate, macros, **options)
        return max(float(np.max(np.abs(rnd.float[frames // 2:, 0]))), 1e-9)

    # The source is int16, so the input this bisects onto is a whole number
    # of LSBs - and at 67 dB of pre-clip gain the answer is about 4 of them,
    # which would quantise the contour into 1 dB steps. So the bisection
    # brackets the target between two whole amplitudes and interpolates
    # between them in log-log, where the pre-clip path is a straight line.
    lo, hi = 1, int(0.9 * 32767)
    for _ in range(steps):
        if hi - lo <= 1:
            break
        mid = (lo + hi) // 2
        if out(mid) < target:
            lo = mid
        else:
            hi = mid
    p_lo, p_hi = out(lo), out(hi)
    amp = float(lo)
    if p_hi > p_lo and p_lo > 0.0:
        share = ((math.log(target) - math.log(p_lo))
                 / (math.log(p_hi) - math.log(p_lo)))
        share = min(1.0, max(0.0, share))
        amp = math.exp(math.log(lo) + share * (math.log(hi) - math.log(lo)))
    return 20.0 * math.log10(0.0300 / (amp / 32767.0))


F2_GRID = (100.0, 200.0, 400.0, 700.0, 1000.0, 1500.0, 2500.0, 5000.0,
           10000.0)


def f2_criterion(cls, rate=RATE, macros=None, grid=F2_GRID,
                 **options):
    """F2 at the row's own point: maximum Distortion, Filter 0."""
    rows = [(hz, equal_drive_gain(cls, hz, rate=rate,
                                  macros=held(macros, DMAX), **options))
            for hz in grid if hz < 0.45 * rate]
    peak_hz, peak_db = max(rows, key=lambda row: row[1])
    at10k = dict(rows).get(10000.0)
    down = None if at10k is None else at10k - peak_db
    passed = (peak_hz <= 1500.0
              and (down is not None and down <= -12.0))
    return {"passed": passed, "peak_hz": peak_hz, "peak_db": peak_db,
            "down_10k": down, "contour": rows,
            "red": [] if passed else ["contour"]}


#: The path gain at 1 kHz that defines 1 V of pre-clip, at the shipped
#: default: 89.1 / 91.0 / 93.0 at 48 / 44.1 / 22.05 kHz, and 102.0 / 103.0 /
#: 104.5 at F3's held point. A build running any curve but the diode table
#: reads a tenth of it.
F3_GAIN_FLOOR = 40.0


def f3_default_clause(cls, frames=8192, macros=None, **options):
    gain, peak = one_volt(cls, frames=frames, macros=macros, **options)[:2]
    passed = gain >= F3_GAIN_FLOOR and abs(peak - 0.403) <= 0.03
    return {"passed": passed, "gain": gain, "peak": peak,
            "red": [] if passed else ["ceiling"]}


def f3_criterion(cls, frames=8192, macros=None, **options):
    at_default = f3_default_clause(cls, frames=frames, macros=macros,
                                   **options)
    gain, hp, h2, h3, h4 = one_volt(cls, frames=frames,
                                    macros=held(macros, D10_CEIL1),
                                    **options)
    even = ((h2 is None or h2 <= -40.0) and (h4 is None or h4 <= -40.0))
    passed = (at_default["passed"] and gain >= F3_GAIN_FLOOR
              and 0.55 <= hp <= 0.60 and even
              and h3 is not None and h3 >= -20.0)
    return {"passed": passed, "default_gain": at_default["gain"],
            "default_peak": at_default["peak"], "held_gain": gain,
            "held_peak": hp, "h2": h2, "h3": h3, "h4": h4,
            "red": [] if passed else ["ceiling"]}


def f4_criterion(cls, macros=None, frames=8192, **options):
    at_default = thd_db(cls, frames=frames, macros=macros, **options)
    clean = thd_db(cls, frames=frames, macros=held(macros, D0), **options)
    quiet = thd_db(cls, peak=0.35, frames=frames, macros=held(macros, D0),
                   **options)
    passed = (-19.0 <= at_default <= -13.0 and clean <= -60.0
              and (at_default - clean) >= 50.0 and -52.0 <= quiet <= -41.0)
    return {"passed": passed, "default": at_default, "dist0": clean,
            "dist0_quiet": quiet, "lead": at_default - clean,
            "red": [] if passed else ["drive"]}


def f5_criterion(cls, rate=RATE, macros=None, **options):
    one = level_db(cls, 1000.0, peak=0.1, rate=rate, macros=macros, **options)
    five = level_db(cls, 5000.0, peak=0.1, rate=rate, macros=macros,
                    **options)
    closed = level_db(cls, 5000.0, peak=0.1, rate=rate,
                      macros=held(macros, D0_CLOSED), **options)
    passed = abs((five - one) + 11.7) <= 1.5 and closed <= -15.0
    return {"passed": passed, "default_fall": five - one, "closed_5k": closed,
            "red": [] if passed else ["filter"]}


def sc3_criterion(cls, frames=8192, macros=None, **options):
    keywords = dict(options)
    if "patch" not in keywords:
        keywords.setdefault("character", 1.0)
    rnd = render(cls, 1000.0, 20e-3, frames, macros=held(macros, SCOOP_HELD),
                 **keywords)
    try:
        values = kit.spectrum(rnd, 1000.0, harmonics=10)["values"]
    except kit.SilentRenderError:
        # A silent build is not a healthy one. Volume MIDI 0 is silence, not
        # a restore, and the sweep has to be able to say so.
        return {"passed": False, "thd_db": None, "h2": None, "h3": None,
                "red": ["silent"]}
    harmonic = values["harmonic_db"]
    h2 = harmonic.get("h2", -240.0)
    h3 = harmonic.get("h3", -240.0)
    thd = values["thd_db"]
    # 8-30 % THD at Distortion minimum, which is the whole row. The fix
    # round added `h3 >= h2 + 40` to keep `NoBoost` red at seven Asymmetry
    # positions, but that clause holds at Asymmetry 0 and nowhere else -
    # at the class's own STOCK_ASYMMETRY it is -5.4 dB, and all four
    # shipped scoop patches ship Asymmetry 96 or 127. A clause that is
    # false at every shipped patch is not a trait of this class. It is
    # gone; the row holds Asymmetry at the 0 its own line names, and the
    # sweep holds it there too.
    passed = -21.9 <= thd <= -10.5
    return {"passed": passed, "thd_db": thd, "h2": h2, "h3": h3,
            "red": [] if passed else ["scoop"]}


#: A1's clause 1 bar, and the bar for `filter` anywhere Boost is at the 0
#: it ships with (clause 2). See the dossier's 2026-09-17 revision.
A1_DEFAULT_DB = -60.0
A1_SURFACE_DB = -50.0


def a1_criterion(cls, rate=RATE, macros=None, patch=None):
    """A1 clause 1: the shipped default, 1010 Hz, -20 dBFS, <= -60 dB.

    The THD clause is not decoration - it is what makes a wire red. A
    class built as a wire has no inharmonic energy at all and would pass
    an upper bound on it; what it cannot do is distort. So the row claims
    both: the class distorts at the default, and what it adds off the
    harmonic grid stays 60 dB down.
    """
    keywords = {} if patch is None else {"patch": patch}
    floor = alias_floor_db(cls, size=rate // 10, rate=rate, macros=macros,
                           **keywords)
    thd = thd_db(cls, hz=1010.0, frames=4 * (rate // 10), rate=rate,
                 macros=macros, **keywords)
    passed = -25.0 <= thd <= -6.0 and floor <= A1_DEFAULT_DB
    return {"passed": passed, "floor": floor, "thd_db": thd,
            "red": [] if passed else ["alias"]}


def a1_surface_criterion(cls, rate=RATE, macros=None, patch=None):
    """A1 clause 2: `filter` with Boost at 0, anywhere else on the surface.

    The same reading against the surface bar. `Boost` and `Character` are
    the two macros the row names as held, because a booster in front of a
    hard clipper is clause 3's subject and not this one's.
    """
    keywords = {} if patch is None else {"patch": patch}
    floor = alias_floor_db(cls, size=rate // 10, rate=rate, macros=macros,
                           **keywords)
    thd = thd_db(cls, hz=1010.0, frames=4 * (rate // 10), rate=rate,
                 macros=macros, **keywords)
    passed = thd >= -40.0 and floor <= A1_SURFACE_DB
    return {"passed": passed, "floor": floor, "thd_db": thd,
            "red": [] if passed else ["alias"]}


class TestDistortionInvariants(unittest.TestCase):

    def test_mix_zero_is_a_wire(self):
        frames = 4096
        src = sine(440, frames, peak=0.2)
        dry = pcm(sine(440, frames, peak=0.2), frames)
        effect = built(src)
        effect.set_macro(MIX, 0)
        wet = pcm(effect.output, frames)
        self.assertEqual(effect.latency_samples, 0)
        result = kit.wire(kit.Render.from_pcm(wet, RATE, 2),
                          kit.Render.from_pcm(dry, RATE, 2),
                          latency_samples=0)
        self.assertFalse(result["red"], result)
        effect.deinit()

    def test_silence_tail_reaches_zero(self):
        frames = 24000
        values = array.array("h", bytes(2 * 2 * frames))
        for index in range(1000):
            value = int(round(20000 * math.sin(2.0 * math.pi * 440 * index
                                               / RATE)))
            values[index * 2] = value
            values[index * 2 + 1] = value
        src = audiocore.RawSample(values, sample_rate=RATE, channel_count=2)
        effect = built(src)
        data = pcm(effect.output, frames)
        tail = memoryview(data).cast("h")[-8000:]
        self.assertEqual(max(abs(int(v)) for v in tail), 0)
        effect.deinit()

    def _click(self, rate, channels, at=400, macros=None, cls=None,
               **options):
        frames = 8192
        values = array.array("h", bytes(2 * channels * frames))
        for channel in range(channels):
            values[at * channels + channel] = 32000
        src_a = audiocore.RawSample(array.array("h", values),
                                    sample_rate=rate, channel_count=channels)
        src_b = audiocore.RawSample(array.array("h", values),
                                    sample_rate=rate, channel_count=channels)
        effect = (cls or Distortion).create(src_a, rate, **options)
        for key, value in (macros or {}).items():
            effect.set_macro(key, value)
        wet = kit.Render.from_pcm(pcm(effect.output, frames, channels), rate,
                                  channels)
        dry = kit.Render.from_pcm(pcm(src_b, frames, channels), rate,
                                  channels)
        reported = effect.latency_samples
        # The integer onset, not the sub-sample one: every node but the
        # half-band is minimum phase, and what those add is group delay.
        result = kit.click(wet, dry, reported, subsample=False)
        effect.deinit()
        return reported, result

    def test_latency_matches_click_at_48k_and_44k1(self):
        for rate in (48000, 44100):
            for channels in (2, 1):
                reported, result = self._click(rate, channels)
                self.assertEqual(reported, 2)
                self.assertFalse(result["red"], (rate, channels, result))

    def test_latency_is_true_at_every_mix(self):
        """The wet leg is 2 late and the dry leg is not, so the class's own
        onset is the dry one at every Mix that lets any dry through. The
        fix round reported 2 across the axis and CLICK went red at Mix 1,
        16, 32, 64, 96, 112, 120, 124 and 126."""
        for rate in (48000, 44100, 22050):
            for mix in (0, 1, 32, 64, 96, 126, 127):
                reported, result = self._click(rate, 2, macros={MIX: mix})
                self.assertEqual(reported,
                                 rebuilt.CLICK_DELAY_SAMPLES[
                                     rebuilt.shipped_oversample(rate)]
                                 if mix == 127 else 0,
                                 (rate, mix, reported))
                self.assertFalse(result["red"], (rate, mix, result))

    def test_latency_does_not_depend_on_where_the_click_sits(self):
        """The graph used to lose its first block, so a click inside it read
        5.3 samples and one after it 15.0. Both characters, both rates."""
        readings = set()
        for at in (100, 256, 300, 700):
            for options in ({}, {"character": 1.0}):
                _reported, result = self._click(RATE, 2, at=at, **options)
                readings.add((tuple(options),
                              tuple(result["values"]
                                    ["measured_latency_samples"])))
        by_character = {}
        for options, measured in readings:
            by_character.setdefault(options, set()).add(measured)
        for options, values in by_character.items():
            self.assertEqual(len(values), 1, (options, values))

    def test_scoop_wet_path_does_not_run_ahead_of_its_dry(self):
        """A Mixer feeding a Mixer voice re-pulls the whole chain: the scoop
        graph used to consume 512 source frames where the dry tap took
        256, and led its own dry path by a block for the whole render."""
        for character in (0.0, 1.0):
            _reported, result = self._click(RATE, 2, character=character)
            measured = result["values"]["measured_latency_samples"]
            self.assertTrue(all(0.0 <= value <= 3.0 for value in measured),
                            (character, measured))

    def _silent_tail(self, cls=None, rate=RATE, **options):
        frames = rate
        effect = built(silence(frames=frames, rate=rate), rate=rate, cls=cls,
                       **options)
        data = pcm(effect.output, frames)
        effect.deinit()
        tail = memoryview(data).cast("h")[-8000:]
        return max(abs(int(value)) for value in tail)

    def test_scoop_patches_do_not_sit_on_dc(self):
        """A DS-1 answers a silent input with silence, and now so does this.

        Asymmetry used to be the shaper's `bias`, and a biased table
        answers a SILENT input with a constant: the four shipped scoop
        patches sat at +0.235, +0.056, +0.456 and +0.242 of full scale
        with nothing playing, patch 8 spending 46 % of its headroom on DC.
        The second fix round hung the DS-1's output coupling capacitor
        behind the clipper and pre-charged it, which took the standing
        offset down to the integer biquad's dead band - 6 to 13 LSB - and
        left the *step*: 0.45 of full scale whenever the input went from
        silence to a note, 86 ms of it (audit 3 (p)4).

        The third fix round took the offset out instead of holding it
        back. The DS-1's asymmetric clipping section is one diode one way
        and two in series the other, so Asymmetry blends
        `_CURVE_DS1_DIODE` into `_CURVE_DS1_ASYM` and **both answer zero
        with zero**. `BiasedScoop` is the old model, and it is what proves
        this row can fail.
        """
        for rate in (48000, 44100, 22050):
            for patch in (6, 7, 8, 9):
                self.assertEqual(
                    self._silent_tail(rate=rate, patch=patch), 0,
                    "scoop patch %d at %d Hz is not silent into silence"
                    % (patch, rate))
        for patch in (6, 8):
            self.assertGreater(
                self._silent_tail(cls=BiasedScoop, patch=patch), 1000,
                "the planted bias model has to stand DC at patch %d or "
                "this row proves nothing" % patch)
        self.assertEqual(self._silent_tail(character=1.0), 0)

    def test_the_coupling_capacitor_is_no_longer_load_bearing(self):
        """With the offset gone, taking the capacitor out changes nothing
        on silence - which is the difference between modelling the DS-1
        and holding a modelling error back with a pole."""
        for patch in (6, 8, 9):
            self.assertEqual(self._silent_tail(cls=NoOutputCap, patch=patch),
                             0, patch)

    def test_click_is_green_on_every_patch_now(self):
        """The four scoop patches could not be read at all while Asymmetry
        was a bias: the coupling capacitor left up to 16 LSB on the output,
        an onset detector answers 0 on a leg that is never exactly zero,
        and the click read -400 whatever the latency was. DISCONFIRMED was
        the honest word for it then. With the blend there is no offset, so
        every shipped patch reads its own latency."""
        for patch in sorted(Distortion.PATCHES):
            reported, result = self._click(RATE, 2, patch=patch)
            self.assertFalse(result["red"], (patch, reported, result))
        _reported, result = self._click(RATE, 2, character=1.0)
        self.assertFalse(result["red"], result)
        # And the old model is what could not be read.
        _reported, result = self._click(RATE, 2, cls=BiasedScoop, patch=6)
        self.assertTrue(result["red"], "the planted bias model reads a click")

    def test_capabilities_empty_and_no_transport(self):
        seen = []

        def transport():
            seen.append(1)
            return (True, 0.0, 120.0, 4, 4)

        effect = Distortion.create(silence(), RATE, transport=transport)
        self.assertEqual(effect.capabilities, ())
        effect.set_macro(DIST, 64)
        self.assertEqual(seen, [])
        effect.deinit()

    def test_rate_honest_construction(self):
        for rate in (44100, 22050):
            effect = built(silence(rate=rate), rate=rate)
            effect.set_macro(FILT, 0)
            self.assertLessEqual(effect._hz(32152.0),
                                 rate * 0.5 * _component.NYQUIST_MARGIN)
            effect.deinit()

    def test_patch_zero_round_trips(self):
        effect = built()
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(DIST, 0)
        self.assertIsNone(effect.patch_index)
        effect.program_change(0)
        self.assertEqual(effect.patch_index, 0)
        self.assertAlmostEqual(effect.macro(DIST), 64 / 127.0, places=2)
        effect.deinit()

    def test_scoop_starts_with_its_booster_in_circuit(self):
        """The DS-1's 35 dB stage is in the circuit, not on the panel."""
        scoop = built(character=1.0)
        self.assertAlmostEqual(scoop.macro(BOOST), 35.0, places=3)
        scoop.deinit()
        rat = built()
        self.assertAlmostEqual(rat.macro(BOOST), 0.0, places=3)
        rat.deinit()

    def test_adopted_is_what_the_package_serves(self):
        """Adopted on the boards 2026-09-18 and promoted the same day, so
        `create()` serves this one out of its own module.

        It was the reverse assertion while the class was parked, and it was
        `assertIn(..., ADOPTED)` for the hours between adoption and coming
        home. Both are the same visible consequence read at different
        stages, so it stays a test and not a comment: serve the old class
        again, from anywhere, and this goes red.
        """
        import audioeffects
        from audioeffects import rebuilt
        self.assertIs(audioeffects.Distortion, Distortion)
        self.assertEqual(Distortion.__module__, "audioeffects.distortion")
        # Left staging when it came home, and left `rebuilt/` with it:
        # there is no second copy for the registry to arbitrate over.
        self.assertNotIn("Distortion", rebuilt.ADOPTED)
        self.assertIsNone(rebuilt.module_class("Distortion"))
        served = audioeffects.create("Distortion", silence(), RATE)
        self.assertIsInstance(served, Distortion)
        served.deinit()


class TestDistortionTraits(unittest.TestCase):
    """Every row: the reading at `create()`'s own settings, a fault that goes
    red there, and the null build."""

    def test_f1_leg_tilt_and_null_build(self):
        out = faults.null_build_red(Distortion, f1_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(f1_criterion(SwapLegs)["passed"])

    def test_f2_equal_drive_contour_and_null_build(self):
        out = faults.null_build_red(Distortion, f2_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(f2_criterion(NoGBW)["passed"])

    def test_f2_is_unmeasurable_at_22k05(self):
        """The row reads 10 kHz against the contour's peak, and 10 kHz is
        above this class's Nyquist margin at 22.05 kHz. Unmeasured with its
        cause, not passed and not failed."""
        low = f2_criterion(Distortion, rate=22050)
        self.assertIsNone(low["down_10k"])
        self.assertFalse(low["passed"])
        self.assertTrue(f2_criterion(Distortion, rate=44100)["passed"])

    def test_f3_one_volt_ceiling_and_null_build(self):
        out = faults.null_build_red(Distortion, f3_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(f3_criterion(LinearClipper)["passed"])

    def test_f4_distortion_is_the_only_drive_and_null_build(self):
        out = faults.null_build_red(Distortion, f4_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(f4_criterion(NoDrive)["passed"])
        self.assertFalse(f4_criterion(AlwaysDriven)["passed"])

    def test_f5_filter_runs_backwards_and_null_build(self):
        out = faults.null_build_red(Distortion, f5_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(f5_criterion(SecondOrderFilter)["passed"])

    def test_f5_five_kilohertz_clause_is_false_at_22k05(self):
        """Disconfirmed, with its cause: `_fo_lp` parks its second pole at
        `min(40 kHz, 0.45 * rate)`, which is 9.9 kHz at 22.05 kHz, so the
        section is no longer first order where the dossier measured it."""
        self.assertTrue(f5_criterion(Distortion, rate=44100)["passed"])
        low = f5_criterion(Distortion, rate=22050)
        self.assertFalse(low["passed"], low)
        self.assertLess(low["default_fall"], -13.0)

    def test_sc3_never_clean_on_scoop_and_null_build(self):
        out = faults.null_build_red(Distortion, sc3_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(sc3_criterion(NoBoost)["passed"])

    def test_a1_alias_floor_at_the_shipped_default(self):
        out = faults.null_build_red(Distortion, a1_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(a1_criterion(BaseRateShaper)["passed"])

    def test_a1_surface_bar_and_null_build(self):
        out = faults.null_build_red(Distortion, a1_surface_criterion)
        self.assertTrue(out["control"]["passed"], out["control"])
        self.assertFalse(a1_surface_criterion(BaseRateShaper)["passed"])

    def test_a1_clause_3_is_disclosed_and_not_claimed(self):
        """A booster in front of a hard clipper sets the floor, and the
        class says so rather than claiming a number it does not hold. The
        shipped `scoop` reads far above clause 2's bar; so does `filter`
        with Boost raised, which is not a setting the Rat ships."""
        scoop = alias_floor_db(Distortion, size=RATE // 10, character=1.0)
        boosted = alias_floor_db(Distortion, size=RATE // 10,
                                 macros={BOOST: 127})
        self.assertGreater(scoop, A1_SURFACE_DB)
        self.assertGreater(boosted, A1_SURFACE_DB)
        self.assertLessEqual(scoop, -22.0)
        self.assertLessEqual(boosted, -22.0)

    def test_the_clipper_output_stays_inside_the_node(self):
        """The Ceiling headroom split, and the knee it exists for.

        `post_gain` above about 0.75 saturates the Waveshaper's own output
        on the decimator's ring: the same table, drive and rate reads
        -58.42 dB of inharmonic energy at 0.74 and -34.03 at 1.00. So the
        class never asks for more, and Ceiling at its top no longer trades
        13 dB of floor for 0.1 dB of level.
        """
        for ceiling in (0, 42, 64, 86, 108, 127):
            for volume in (100, 127):
                effect = built()
                effect.set_macro(CEIL, ceiling)
                effect.set_macro(VOL, volume)
                post, level = effect._headroom(
                    effect.macro(CEIL) * effect._curve_volts,
                    effect.macro(MIX) * effect.macro(VOL))
                effect.deinit()
                self.assertLessEqual(post, Distortion.CLIPPER_CEILING + 1e-9,
                                     (ceiling, volume, post))
                self.assertLessEqual(level, 1.0)
        floor = alias_floor_db(Distortion, size=RATE // 10,
                               macros={CEIL: 127, VOL: 127})
        self.assertLessEqual(floor, A1_SURFACE_DB, floor)

    def test_rate_picks_the_oversampling_factor(self):
        """x4 at 48 and 44.1 kHz, x8 at 22.05: one internal rate, and the
        rate that would otherwise read the decimator's fold instead of the
        class (-51.24 dB at x4 against -56.37 at x8, maximum Distortion)."""
        self.assertEqual(rebuilt.shipped_oversample(48000), 4)
        self.assertEqual(rebuilt.shipped_oversample(44100), 4)
        self.assertEqual(rebuilt.shipped_oversample(22050), 8)
        for rate, factor in ((48000, 4), (44100, 4), (22050, 8)):
            effect = built(silence(rate=rate), rate=rate)
            self.assertEqual(effect._oversample, factor)
            self.assertEqual(effect.latency_samples,
                             rebuilt.CLICK_DELAY_SAMPLES[factor])
            effect.deinit()
        effect = built(oversample=2)
        self.assertEqual(effect._oversample, 2)
        effect.deinit()


class TestDistortionGuardsAreNotOnTheSurface(unittest.TestCase):
    """The audit's rule: a fault green anywhere a user can stand is not a
    guard - and a position where the CLEAN class is red is not a position
    where the fault fired, so it is not in the denominator either.

    Every sweep here therefore reads both builds at every position, counts
    only the positions the clean class holds, and grades the fault on the
    **whole row**, not on one clause of it. Grading `AlwaysDriven` on F4's
    default clause alone is what made it look healthy at Body 64 and at
    shipped patch 5: the clause it fails is F4's Distortion-0 one, which
    the same row claims.
    """

    GRID = (0, 16, 32, 48, 64, 80, 96, 112, 127)

    def _sweep(self, criterion, faulted, held=(), patches=None,
               scoop=False):
        """Walk every macro the row does not hold, plus the patches.

        Returns `(restored, checked, claimed)`: positions where the fault
        passes the row **and** the clean class passes it, how many were
        visited, and how many of those the clean class holds.
        """
        restored, checked, claimed = [], 0, 0
        options = {"character": 1.0} if scoop else {}
        for index in range(10):
            if index in held:
                continue
            for position in self.GRID:
                checked += 1
                clean = _reading(criterion, Distortion,
                                 macros={index: position}, **options)
                if not clean["passed"]:
                    continue
                claimed += 1
                if _reading(criterion, faulted, macros={index: position},
                            **options)["passed"]:
                    restored.append((Distortion.MACRO_LABELS[index],
                                     position))
        for patch in (sorted(Distortion.PATCHES) if patches is None
                      else patches):
            checked += 1
            if not _reading(criterion, Distortion, patch=patch)["passed"]:
                continue
            claimed += 1
            if _reading(criterion, faulted, patch=patch)["passed"]:
                restored.append(("patch", patch))
        return restored, checked, claimed

    def test_swap_legs_is_red_everywhere_f1_is_claimed(self):
        """F1 holds Distortion and Filter by name, so the sweep walks the
        other eight and reads every patch with the row's own held line on
        top of it. The clean class is red at Boost 32 and above - the
        booster flattens the tilt to -1.3 dB - and a position the class
        itself fails is not one the guard can be judged at."""
        restored, checked, claimed = self._sweep(
            _f1_at, SwapLegs, held=(DIST, FILT))
        self.assertGreater(checked, 80)
        self.assertGreater(claimed, 40)
        self.assertEqual(restored, [])

    def test_linear_clipper_is_red_everywhere_f3_is_claimed(self):
        """All ten macros at nine positions each, plus all eleven shipped
        patches: 101 positions. Volume 56, Mix 80, Ceiling 8 and patch 2 all
        put the identity table's peak back on 0.40 - the output scaling
        moves the clipper's ceiling and the small-signal gain together - so
        the gain floor is part of the clause, and the fault's best gain
        anywhere on the surface is 9.3 against the class's 89."""
        restored, checked, claimed = self._sweep(_f3_at, LinearClipper)
        self.assertEqual(checked, 101)
        self.assertGreater(claimed, 40)
        self.assertEqual(restored, [])

    def test_always_driven_is_red_everywhere_f4_is_claimed(self):
        """The whole F4 row, not its default clause: `AlwaysDriven` pins
        `pre_gain` at 8.0, which Body 64 and shipped patch 5 reach from the
        panel - so the default clause cannot tell them apart there - but
        the row also says Distortion 0 is clean, and a forced drive is not
        clean at Distortion 0 anywhere."""
        restored, checked, claimed = self._sweep(_f4_at, AlwaysDriven)
        self.assertEqual(checked, 101)
        self.assertGreater(claimed, 40)
        self.assertEqual(restored, [])

    def test_no_drive_is_red_everywhere_f4_is_claimed(self):
        restored, _checked, claimed = self._sweep(_f4_at, NoDrive)
        self.assertGreater(claimed, 40)
        self.assertEqual(restored, [])

    def test_base_rate_shaper_is_red_everywhere_a1_is_claimed(self):
        """A1's row holds Character at `filter` and Boost at the 0 the Rat
        ships with - clause 3 is where a booster goes, and it claims
        nothing. Inside the two clauses that do claim, x1 is red at every
        position the class itself holds."""
        restored, checked, claimed = self._sweep(
            _a1_at, BaseRateShaper, held=(CHAR, BOOST),
            patches=(0, 1, 2, 3, 4, 5, 10))
        self.assertGreater(checked, 70)
        self.assertGreater(claimed, 30)
        self.assertEqual(restored, [])

    def test_no_boost_is_red_everywhere_sc3_is_claimed(self):
        """SC3 holds Character, Distortion and Asymmetry by name - its line
        reads "Distortion 0; Tone centre; Asymmetry 0" - so the sweep holds
        those three and walks the other seven, plus the four shipped scoop
        patches, which ship Asymmetry 96 and 127 and are therefore outside
        the row's line: the clean class is red at all four and they are
        counted as visited, not as claimed."""
        restored, checked, claimed = self._sweep(
            _sc3_at, NoBoost, held=(CHAR, DIST, ASYM), patches=(6, 7, 8, 9),
            scoop=True)
        self.assertGreater(checked, 60)
        self.assertGreater(claimed, 30)
        self.assertEqual(restored, [])


def _reading(criterion, cls, **keywords):
    """One cell of a sweep. A build that renders silence - Volume 0, Mix 0
    with a silent source - is not a healthy one and not a claimed one
    either; it is a position where nothing was measured, and it says so
    instead of raising through the sweep."""
    try:
        return criterion(cls, **keywords)
    except kit.SilentRenderError:
        return {"passed": False, "red": ["silent"]}


def _f1_at(cls, macros=None, patch=None, **options):
    if patch is not None:
        # A patch sets Distortion and Filter too, and F1 holds both. The
        # honest reading of a patch is its OTHER macros with the row's own
        # line on top, which is what this returns.
        options = dict(options)
        options["patch"] = patch
    return f1_criterion(cls, macros=macros, frames=4096, **options)


def _f3_at(cls, macros=None, patch=None, **options):
    keywords = dict(options)
    if patch is not None:
        keywords["patch"] = patch
    return f3_criterion(cls, frames=4096, macros=macros, **keywords)


def _f4_at(cls, macros=None, patch=None, **options):
    keywords = dict(options)
    if patch is not None:
        keywords["patch"] = patch
    return f4_criterion(cls, macros=macros, frames=4096, **keywords)


def _a1_at(cls, macros=None, patch=None, **options):
    if patch is not None:
        return a1_surface_criterion(cls, patch=patch)
    return a1_surface_criterion(cls, macros=macros)


def _sc3_at(cls, macros=None, patch=None, **options):
    keywords = dict(options)
    if patch is not None:
        keywords.pop("character", None)
        keywords["patch"] = patch
    return sc3_criterion(cls, frames=4096, macros=macros, **keywords)


def _reach_build(cls):
    return cls.create(silence(512), RATE)


class TestDistortionFaultReachability(unittest.TestCase):
    """0-127 walk (step 8) plus every shipped patch. Stashed flags, not
    knobs."""

    def test_swap_legs_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, SwapLegs,
            lambda e: bool(getattr(e, "_swapped_legs", False)),
            _reach_build, label="F1 SwapLegs")
        self.assertGreater(out["checked"], 100)

    def test_linear_clipper_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, LinearClipper,
            lambda e: bool(getattr(e, "_linear", False)),
            _reach_build, label="F3 LinearClipper")
        self.assertGreater(out["checked"], 100)

    def test_no_drive_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, NoDrive,
            lambda e: bool(getattr(e, "_no_drive", False)),
            _reach_build, label="F4 NoDrive")
        self.assertGreater(out["checked"], 100)

    def test_always_driven_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, AlwaysDriven,
            lambda e: float(getattr(e, "_forced_drive", 0.0)),
            _reach_build, label="F4 AlwaysDriven")
        self.assertGreater(out["checked"], 100)

    def test_second_order_filter_q_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, SecondOrderFilter,
            lambda e: float(e._filt.Q) if e._filt is not None else -1.0,
            _reach_build, label="F5 SecondOrderFilter", tolerance=0.02)
        self.assertGreater(out["checked"], 100)

    def test_no_gbw_flag_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, NoGBW,
            lambda e: bool(getattr(e, "_no_gbw", False)),
            _reach_build, label="F2 NoGBW")
        self.assertGreater(out["checked"], 100)

    def test_base_rate_oversample_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, BaseRateShaper,
            lambda e: int(e._oversample),
            _reach_build, label="A1 BaseRateShaper")
        self.assertGreater(out["checked"], 100)

    def test_no_boost_flag_not_on_the_surface(self):
        out = faults.fault_reachability(
            Distortion, NoBoost,
            lambda e: bool(getattr(e, "_no_boost", False)),
            lambda cls: cls.create(silence(512), RATE, character=1.0,
                                   distortion=0.0),
            label="SC3 NoBoost")
        self.assertGreater(out["checked"], 100)


class TestDistortionCurvesFillTheRange(unittest.TestCase):
    """Both tables reach the rails, and the generator will not emit one
    that does not ([audiocomponents#77]).

    They used to hold clipped volts directly, so the Rat peaked at ±21617
    and the DS-1 at ±20366 - 66 % and 62 % of int16 - and every entry was
    quantised more coarsely than it had to be for nothing.
    `_CURVE_<name>_VOLTS` carries the scale out in `post_gain` instead.
    """

    def _generator(self):
        from tools.curves import distortion_curve
        return distortion_curve

    def _quiet_check(self, gen):
        """`--check`, its report swallowed. Returns None, or the message
        of the `SystemExit` it raises."""
        import io
        import contextlib
        sink = io.StringIO()
        try:
            with contextlib.redirect_stdout(sink), \
                    contextlib.redirect_stderr(sink):
                gen.main(["--check"])
        except SystemExit as exc:
            return str(exc)
        return None

    def test_shipped_tables_reach_both_rails(self):
        for name in ("_CURVE_RAT_DIODE", "_CURVE_DS1_DIODE"):
            words = array.array("h", getattr(rebuilt, name))
            self.assertEqual((min(words), max(words)), (-32767, 32767), name)

    def test_module_holds_what_the_generator_writes(self):
        self.assertIsNone(self._quiet_check(self._generator()))

    def test_generator_refuses_a_table_that_leaves_the_range_empty(self):
        """Planted: the pre-fix normalisation, volts straight into Q15."""
        gen = self._generator()
        keep = gen.peak_volts
        try:
            gen.peak_volts = lambda resistance: 1.0
            self.assertLess(gen.fill(gen.table(gen.RAT_R)), 0.95)
            message = self._quiet_check(gen)
            self.assertIsNotNone(message)
            self.assertIn("of int16", message)
        finally:
            gen.peak_volts = keep
        self.assertIsNone(self._quiet_check(gen))

    def test_the_scale_follows_the_character(self):
        """Each character's own full-scale voltage, not one constant.

        `scoop`'s is the **blend's** volts since the third fix round -
        Asymmetry moves it between the two DS-1 tables - and it is rounded
        to single precision because it reaches `post_gain` and a board
        computes it in float32 (audiocomponents#75). At Asymmetry 0 it is
        the pair table's own number to seven places.
        """
        rat = built(character=0.0)
        scoop = built(character=1.0)
        try:
            self.assertEqual(rat._curve_volts, rebuilt._CURVE_RAT_DIODE_VOLTS)
            self.assertAlmostEqual(scoop._curve_volts,
                                   rebuilt._CURVE_DS1_DIODE_VOLTS, places=7)
            self.assertNotEqual(rat._curve_volts, scoop._curve_volts)
        finally:
            rat.deinit()
            scoop.deinit()


def burst_then_silence(hz=1000.0, on_frames=9600, total=48000, peak=0.5,
                       rate=RATE, channels=2):
    """A burst, then digital silence to the end. `kit_probes` is not on this
    file's path, so the probe is built the way `sine` above builds one."""
    values = array.array("h", bytes(2 * channels * total))
    amp = int(round(peak * 32767.0))
    for index in range(on_frames):
        value = int(round(amp * math.sin(2.0 * math.pi * hz * index / rate)))
        for channel in range(channels):
            values[index * channels + channel] = value
    return (audiocore.RawSample(values, sample_rate=rate,
                                channel_count=channels), on_frames)


class TestDistortionVolumeAndMixTravel(unittest.TestCase):
    """Audit 3 (p)2, ruling (o): a knob whose label promises travel it does
    not deliver is the Phase 2 Limiter shape seen from the other side.

    `Ceiling` scales the diode drop, and the clipper's own output is held
    at or below `CLIPPER_CEILING` of full scale, so above a knee the split
    in `_headroom` has nowhere left to put the level. `Volume` MIDI 84 to
    127 was one number at shipped patch 3 - 43 positions and 3.6 dB of
    label travel delivering 0.00 dB - and nothing said so.

    `wet_ceiling()` is the class's own answer to where that knee is, and
    these rows hold it to the render: live below it, flat above it, and
    the knee where the class says. **At the shipped Ceiling MIDI 42 there
    is no knee at all**: the whole travel works, which is why every patch
    but 3 was green and the defect sat unseen.
    """

    LEVELS = (0, 16, 32, 48, 64, 80, 96, 112, 127)

    def wet_db(self, ceiling, volume=127, mix=127, rate=RATE, dbfs=-20.0,
               **options):
        frames = rate // 4
        index = np.arange(frames)
        values = np.clip(
            np.round(10.0 ** (dbfs / 20.0)
                     * np.sin(2.0 * math.pi * 1000.0 * index / rate)
                     * 32767.0), -32768, 32767).astype(np.int64)
        data = array.array("h",
                           np.repeat(values[:, None], 2, axis=1)
                           .reshape(-1).tolist())
        effect = Distortion.create(
            audiocore.RawSample(data, sample_rate=rate, channel_count=2),
            rate, **options)
        try:
            effect.set_macro(6, ceiling)
            effect.set_macro(3, volume)
            effect.set_macro(4, mix)
            knee = effect.wet_ceiling()
            out = pcm(effect.output, frames, 2)
        finally:
            effect.deinit()
        wave = (np.frombuffer(out, dtype="<i2").reshape(-1, 2)[:, 0]
                .astype(np.float64) / 32768.0)[frames // 2:]
        rms = float(np.sqrt((wave * wave).mean()))
        return knee, 20.0 * math.log10(max(1e-9, rms))

    def test_volume_is_monotone_below_the_knee(self):
        for ceiling in (24, 42, 108):
            knee, _db = self.wet_db(ceiling)
            rows = [(midi, self.wet_db(ceiling, volume=midi)[1])
                    for midi in self.LEVELS if midi]
            live = [row for row in rows if row[0] / 127.0 <= knee]
            self.assertGreater(len(live), 3, (ceiling, knee, rows))
            for before, after in zip(live, live[1:]):
                self.assertGreater(
                    after[1], before[1] + 0.5,
                    "Ceiling %d: Volume %d -> %d moved %.3f dB, and the "
                    "class says the knee is at MIDI %.1f"
                    % (ceiling, before[0], after[0], after[1] - before[1],
                       127.0 * knee))

    def test_above_the_knee_volume_is_declared_inoperative_and_is(self):
        """The other half of the disclosure: where the class says the knob
        has stopped, it has - to 0.05 dB - rather than half-working."""
        for ceiling in (108, 127):
            knee, top = self.wet_db(ceiling)
            dead = [midi for midi in self.LEVELS if midi / 127.0 > knee]
            self.assertTrue(dead, (ceiling, knee))
            for midi in dead:
                self.assertAlmostEqual(
                    self.wet_db(ceiling, volume=midi)[1], top, delta=0.05,
                    msg="Ceiling %d, Volume %d" % (ceiling, midi))

    def test_the_shipped_ceiling_has_no_knee(self):
        knee, _db = self.wet_db(42)
        self.assertEqual(knee, 1.0)
        knee, _db = self.wet_db(42, character=1.0)
        self.assertEqual(knee, 1.0)

    def test_mix_is_a_crossfade_below_the_knee(self):
        for ceiling in (24, 42, 108):
            knee, _db = self.wet_db(ceiling)
            rows = [(midi, self.wet_db(ceiling, mix=midi)[1])
                    for midi in self.LEVELS if midi]
            live = [row for row in rows if row[0] / 127.0 <= knee]
            for before, after in zip(live, live[1:]):
                self.assertGreater(
                    after[1], before[1] + 0.5,
                    "Ceiling %d: Mix %d -> %d moved %.3f dB"
                    % (ceiling, before[0], after[0], after[1] - before[1]))


class TestDistortionTheCouplingCapacitorUnderMaterial(unittest.TestCase):
    """Audit 3 (p)4: the pre-charge was a thump under material.

    The second fix round charged the output capacitor on the *silent*
    input's DC, which is right for silence and wrong for a note: a
    -20 dBFS tone saw its first five cycles average **-0.2427 of full
    scale** at patch 8, against +0.0231 with the pre-charge off. Both
    numbers were the same defect - an operating point parked at 0.97 of
    full scale by a 3.5 V bias - and the third fix round took the bias out
    rather than arguing about which way to charge a capacitor that should
    not have had a step to hold.

    What is left is the note's own rectified offset settling through a
    20 Hz pole, which is what the hardware does.
    """

    def first_cycles(self, cls, patch, rate=RATE, dbfs=-20.0, cycles=5):
        frames = rate // 4
        index = np.arange(frames)
        values = np.clip(
            np.round(10.0 ** (dbfs / 20.0)
                     * np.sin(2.0 * math.pi * 1000.0 * index / rate)
                     * 32767.0), -32768, 32767).astype(np.int64)
        data = array.array("h",
                           np.repeat(values[:, None], 2, axis=1)
                           .reshape(-1).tolist())
        effect = cls.create(
            audiocore.RawSample(data, sample_rate=rate, channel_count=2),
            rate, patch=patch)
        try:
            out = pcm(effect.output, frames, 2)
        finally:
            effect.deinit()
        wave = (np.frombuffer(out, dtype="<i2").reshape(-1, 2)[:, 0]
                .astype(np.float64) / 32768.0)
        return float(wave[:int(cycles * rate / 1000.0)].mean())

    def test_the_first_note_does_not_arrive_on_an_offset(self):
        for patch in (6, 7, 8, 9):
            mean = self.first_cycles(Distortion, patch)
            self.assertLess(
                abs(mean), 0.10,
                "scoop patch %d starts a -20 dBFS note on %+.4f of full "
                "scale" % (patch, mean))

    def test_the_bias_model_is_what_fails_it(self):
        for patch in (6, 8, 9):
            mean = self.first_cycles(BiasedScoopWithCap, patch)
            self.assertGreater(
                abs(mean), 0.10,
                "the planted bias model has to start patch %d on an offset "
                "or the row above proves nothing (%+.4f)" % (patch, mean))


class TestDistortionA1AcrossItsLevelSpan(unittest.TestCase):
    """Audit 3 ruling (m): a demonstrated trait row carries the level it
    holds at, because a row that names no level is claimed at every level.

    A1's -60 dB bar is a **-20 dBFS** number. It holds over -22 to -16
    dBFS at all three rates and nowhere else: -58.6 at -24, -46.5 at -6,
    -43.8 at -0.9. The row, the docstring and the catalogue row all carry
    the span now, and this walks it at both ends and the middle.
    """

    SPAN = (-22.0, -19.0, -16.0)

    def alias(self, rate, dbfs, hz=1010.0):
        frames = rate // 10 * 2
        size = rate // 10
        index = np.arange(frames)
        values = np.clip(
            np.round(10.0 ** (dbfs / 20.0)
                     * np.sin(2.0 * math.pi * hz * index / rate) * 32767.0),
            -32768, 32767).astype(np.int64)
        data = array.array("h",
                           np.repeat(values[:, None], 2, axis=1)
                           .reshape(-1).tolist())
        effect = Distortion.create(
            audiocore.RawSample(data, sample_rate=rate, channel_count=2),
            rate)
        try:
            render = kit_probes.wet_render(
                effect, frames, allow_tail_frames=4, rate=rate, channels=2,
                block=256, class_name="Distortion",
                latency_samples=effect.latency_samples)
        finally:
            effect.deinit()
        return kit.spectrum(render, hz, harmonics=10,
                            size=size)["values"]["alias_floor_db"]

    def test_a1_holds_across_the_span_it_names(self):
        for rate in (48000, 44100, 22050):
            for dbfs in self.SPAN:
                floor = self.alias(rate, dbfs)
                self.assertLess(
                    floor, -60.0,
                    "A1 reads %.3f dB at %s dBFS, %d Hz" % (floor, dbfs, rate))

    def test_a1_does_not_hold_outside_it_and_the_row_says_so(self):
        """The other half of a level clause: if the bar held everywhere the
        span would be charity, and if it failed inside the span the row
        would be false."""
        for rate in (48000, 44100, 22050):
            self.assertGreater(self.alias(rate, -6.0), -60.0, rate)
            self.assertGreater(self.alias(rate, -12.0), -60.0, rate)


class TestDistortionTheScoopFilterMacro(unittest.TestCase):
    """Audit 3 (p)3: `max(fc, CLIP_LP_HZ)` made 120 of 128 positions one
    section and ran the first six backwards."""

    STOPS = (0, 2, 4, 8, 16, 32, 64, 96, 127)

    def corner(self, midi):
        effect = built(silence(frames=512), character=1.0)
        try:
            effect.set_macro(1, midi)
            return float(effect._clip_lp.frequency)
        finally:
            effect.deinit()

    def test_every_position_is_its_own_section(self):
        corners = [self.corner(midi) for midi in self.STOPS]
        self.assertEqual(len(set(corners)), len(corners), corners)
        for before, after in zip(corners, corners[1:]):
            self.assertLess(after, before,
                            "the Filter macro runs backwards: %r" % (corners,))

    def test_filter_zero_is_the_stock_ds1_corner(self):
        effect = built(silence(frames=512), character=1.0)
        try:
            effect.set_macro(1, 0)
            stock = float(effect._clip_lp.frequency)
        finally:
            effect.deinit()
        reference = rebuilt._fo_lp(rebuilt.CLIP_LP_HZ, RATE)[0]
        self.assertAlmostEqual(stock, reference, delta=1.0)


class TheTierOneRowsAtEveryShippedPatch(unittest.TestCase):
    """audiocomponents#87.

    Tier 1's silence and tail rows were taken at the constructor default.
    `Distortion`'s Tone is the BIPOLAR macro, and the centre detent moved
    the bytes of the four scoop patches that carry it - but not these rows,
    which were already what they are: this class's emission into silence
    comes from **Asymmetry**, which is UNIPOLAR over (0, 1) and whose "none
    of this" end is 0, a value the grid could always reach. The four scoop
    patches ask for 0.756 or 1.0 of it on purpose.

    Measured here anyway, per patch rather than at the default only, which
    is the guard #87 asks every drive class to carry.

    **Both exemptions are empty since the third fix round.** They named the
    four scoop patches, and the reason they named was Asymmetry: a bias
    into the symmetric table, which answers a silent input with a constant.
    Asymmetry is a blend towards `_CURVE_DS1_ASYM` now and both tables
    answer zero with zero, so there is nothing left to hold back and no
    patch of this class has a footnote instead of a row.
    `TestDistortionInvariants.test_scoop_patches_do_not_sit_on_dc` carries
    the planted bias model that proves it.
    """

    RED = {}

    RED_TAIL = {}

    def peaks(self):
        """`{patch: (silence_peak, tail_samples, residual, declared)}`."""
        rows = {}
        for patch in sorted(Distortion.PATCHES):
            effect = built(silence(frames=RATE), patch=patch)
            quiet = kit.Render.from_pcm(pcm(effect.output, RATE), RATE, 2)
            effect.deinit()
            probe, burst_end = burst_then_silence()
            effect = built(probe, patch=patch)
            declared = effect.tail_samples
            wet = kit.Render.from_pcm(pcm(effect.output, RATE), RATE, 2)
            effect.deinit()
            result = kit.tail(wet, burst_end_frame=burst_end,
                              declared_tail_samples=declared)
            rows[patch] = (int(np.abs(quiet.data).max()),
                           result["values"]["tail_samples"],
                           result["values"]["residual_lsb"], declared)
        return rows

    def test_silence_in_is_silence_out_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                if patch in self.RED:
                    self.assertGreater(row[0], 0, self.RED[patch])
                    continue
                self.assertEqual(row[0], 0,
                                 "patch %d emits %d LSB into digital "
                                 "silence" % (patch, row[0]))

    def test_the_declared_tail_holds_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            _quiet, tail_samples, residual, declared = row
            with self.subTest(patch=patch, why=self.RED_TAIL.get(patch)):
                if patch in self.RED_TAIL:
                    self.assertGreater(residual, 0, self.RED_TAIL[patch])
                    continue
                self.assertEqual(residual, 0,
                                 "patch %d never returns to zero (%d LSB "
                                 "left)" % (patch, residual))
                self.assertLessEqual(tail_samples or 0, declared,
                                     "patch %d rings %s samples against a "
                                     "declared %s"
                                     % (patch, tail_samples, declared))

    def test_program_change_onto_digital_silence_stays_silent(self):
        """A patch change is a wire message and can arrive between notes."""
        for patch in sorted(Distortion.PATCHES):
            effect = built(silence(frames=RATE), patch=0)
            before = kit.Render.from_pcm(pcm(effect.output, RATE // 2),
                                         RATE, 2)
            effect.program_change(patch)
            after = kit.Render.from_pcm(pcm(effect.output, RATE // 2),
                                        RATE, 2)
            effect.deinit()
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                self.assertEqual(int(np.abs(before.data).max()), 0)
                peak = int(np.abs(after.data).max())
                if patch in self.RED:
                    self.assertGreater(peak, 0, self.RED[patch])
                    continue
                self.assertEqual(peak, 0,
                                 "program_change(%d) on silence emitted %d "
                                 "LSB" % (patch, peak))


if __name__ == "__main__":
    unittest.main()
