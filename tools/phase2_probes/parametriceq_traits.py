"""ParametricEQ's Tier 2 traits, measured with the kit, each beside the
planted fault of the same kind that has to turn it red.

CPython with numpy, like the rest of `tools/effect_measurements.py`: the
excitation is a set of steady tones rendered one at a time through the class
and through a bare wire, and every number below comes from
`effect_measurements.response()` reading those renders. Nothing here is
computed from a re-derivation of RBJ.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_traits.py \
        [--rate 48000] [--traits T1,T2,...] [--level -20]
    ... --checks     the kit's two gatekeepers on every trait and every fault
    ... --prove      those two gatekeepers shown FAILING on the retired code
    ... --levels     the probe-level axis T3 and T5 left free
    ... --sweeps     the macro spans, through `effect_measurements.macro_sweep`

**What the gate audit changed here** (2026-09-07,
`docs/effects-phase2-gate-audit.md` sections 3 and 4.2). T2 read
*demonstrated* on a byte-flat wire, because `local_maximum_near` marked every
interior point of a plateau a maximum; T3 and T5 were measured at one probe
level and fail above -16 dBFS, where the class's int16 sections clip; T4's
planted fault was the class's own `Q Law` toggle, a position a player dials.
Each is answered below in the code that produced the number, not in prose:
the maximum is strict and carries a prominence, the level is an axis with its
own run, and every fault is checked against `kit_faults.fault_reachability`.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import audiobiquad                                       # noqa: E402
import effect_measurements as kit                        # noqa: E402
import kit_faults as faults                              # noqa: E402
import kit_probes as probes                              # noqa: E402

#: `ParametricEQ` has come home to `audioeffects/parametriceq.py`. This
#: probe names that module so a planted fault is a subclass of the class
#: the traits are about.
from audioeffects import parametriceq as _module  # noqa: E402

ParametricEQ = _module.ParametricEQ

SECONDS = 0.5
LEVEL_DBFS = -20.0

#: The level axis T3 and T5 never stated. The refutation pass walked
#: -40...-6 dBFS and both rows fall over inside it; these are the stops the
#: bound in the docstring and the catalogue row is read from.
LEVELS = (-40.0, -30.0, -24.0, -20.0, -18.0, -16.0, -15.0, -14.0, -13.0,
          -12.0, -10.0, -6.0)

#: T2's bell has to be a bell rather than a plateau: the peak must stand
#: this far above the response a third of an octave out, on the side it
#: stands least. The number is five times the class's own `FLAT_DB` (0.2 dB,
#: `parametriceq.py:61`), the gain under which it builds a section as a
#: wire - so a bump this check accepts is one the class itself would not
#: have called flat, and a build that does nothing reads exactly 0.000.
PROMINENCE_DB = 1.0

#: A third of an octave, T2's own unit for "near 10 kHz".
THIRD_OCTAVE = 2.0 ** (1.0 / 3.0)


def grid(low, high, points):
    return [low * (high / low) ** (index / (points - 1.0))
            for index in range(points)]


def render_tone(hz, rate, build=None, seconds=SECONDS, level=LEVEL_DBFS):
    frames = int(rate * seconds)
    material = probes.sine(hz, seconds, level, rate=rate, channels=2)
    source = probes.ArraySource(material, rate=rate, block=256)
    if build is None:
        return probes.render(source, frames, rate=rate, block=256,
                             probe="sine_%g" % hz, class_name="source"), None
    effect = build(source)
    render = probes.render(effect.output, frames, rate=rate, block=256,
                           probe="sine_%g" % hz, class_name="ParametricEQ",
                           latency_samples=effect.latency_samples)
    return render, effect


class Curve:
    """One RESPONSE measurement over a frequency grid."""

    def __init__(self, name, rate, frequencies, build, dry_cache,
                 level=LEVEL_DBFS):
        wet, dry = {}, {}
        for hz in frequencies:
            key = (hz, level)
            if key not in dry_cache:
                dry_cache[key] = render_tone(hz, rate, level=level)[0]
            dry[hz] = dry_cache[key]
            render, effect = render_tone(hz, rate, build, level=level)
            wet[hz] = render
            effect.deinit()
        self.name = name
        self.level = level
        self.result = kit.response(wet, dry)
        self.hz = [point["hz"] for point in self.result["values"]["grid"]]
        self.db = [point["magnitude_db"]
                   for point in self.result["values"]["grid"]]

    @classmethod
    def from_points(cls, hz, db, name="curve"):
        """A curve made of numbers rather than of renders.

        The readings below are what the gate audit broke, so they are held
        to a regression test in `tests/test_cpython_effects_parametriceq.py`;
        this is how that test reaches them without three minutes of audio.
        """
        curve = object.__new__(cls)
        curve.name = name
        curve.level = None
        curve.result = None
        curve.hz = list(hz)
        curve.db = list(db)
        return curve

    def at(self, hz):
        for index in range(1, len(self.hz)):
            if self.hz[index] >= hz:
                low, high = self.hz[index - 1], self.hz[index]
                share = math.log(hz / low) / math.log(high / low)
                return self.db[index - 1] + share * (self.db[index]
                                                     - self.db[index - 1])
        return self.db[-1]

    def minimum(self, low, high):
        window = [(g, f) for f, g in zip(self.hz, self.db) if low <= f <= high]
        return min(window)

    def maximum(self):
        best = max(zip(self.db, self.hz))
        return best[0], best[1]

    def flat_within(self):
        """The largest |dB| anywhere on the grid. A build that does nothing
        reads 0.000000, which is the reading every falsifiability check in
        this file is written against."""
        return max(abs(value) for value in self.db)

    def _interpolated(self, index):
        """The peak of the parabola through three log-spaced points.

        Without it, "the peak moved 0.000 oct" is a statement about the grid
        step (0.045 oct at T2's 97 points) and not about the class - which is
        what the refutation pass said about T2's third clause.
        """
        low, mid, high = (self.db[index - 1], self.db[index],
                          self.db[index + 1])
        denominator = low - 2.0 * mid + high
        offset = 0.0 if denominator == 0.0 else 0.5 * (low - high) / denominator
        offset = min(1.0, max(-1.0, offset))
        step = self.hz[index + 1] / self.hz[index]
        return self.hz[index] * (step ** offset)

    def local_maximum_near(self, hz, prominence_db=PROMINENCE_DB):
        """The interior local maximum closest to `hz`, or None.

        Three things this returns that the first version did not, each
        because the refutation pass showed that version green on a byte-flat
        wire (`docs/effects-phase2-pattern-revision.md` section 1.2):

        * the maximum is **strict on the left**, so a plateau - every
          interior point of which satisfied `>=` on both sides - is no longer
          a bell, and a flat build returns `None` here;
        * `prominence` is the peak minus the higher of the two responses a
          third of an octave out, so a bump the class did not build reads
          0.000 dB and misses `PROMINENCE_DB`;
        * the peak frequency is interpolated between grid points, so "the
          peak moved 0.000 oct" is a reading and not the grid step.

        Returns `(level, hz, distance_oct, prominence_db)`.
        """
        found = []
        for index in range(1, len(self.hz) - 1):
            if not (self.db[index] > self.db[index - 1]
                    and self.db[index] >= self.db[index + 1]):
                continue
            where = self._interpolated(index)
            distance = abs(math.log(where / hz) / math.log(2.0))
            shoulder = max(self.at(where / THIRD_OCTAVE),
                           self.at(where * THIRD_OCTAVE))
            found.append((distance, where, self.db[index],
                          self.db[index] - shoulder))
        found = [entry for entry in found if entry[3] >= prominence_db]
        if not found:
            return None
        distance, where, level, prominence = min(found)
        return level, where, distance, prominence

    def worst_above(self, hz):
        return max(abs(g) for f, g in zip(self.hz, self.db) if f >= hz)

    def width_3db(self):
        """Octaves between the two points 3 dB below the peak."""
        peak, where = self.maximum()
        target = peak - 3.0
        index = self.hz.index(where)
        left = right = None
        for step in range(index, -1, -1):
            if self.db[step] <= target:
                left = self.hz[step]
                break
        for step in range(index, len(self.hz)):
            if self.db[step] <= target:
                right = self.hz[step]
                break
        if left is None or right is None:
            return None
        return math.log(right / left) / math.log(2.0)

    def crossing_above(self, level, from_hz):
        for index in range(len(self.hz) - 1, 0, -1):
            if self.hz[index - 1] < from_hz:
                break
            if (self.db[index - 1] - level) * (self.db[index] - level) <= 0.0:
                span = self.db[index] - self.db[index - 1]
                share = (level - self.db[index - 1]) / (span or 1e-30)
                return self.hz[index - 1] * ((self.hz[index]
                                              / self.hz[index - 1]) ** share)
        return None

    def half_gain_width(self):
        """Octaves between the two points at half the peak gain in dB."""
        half = self.maximum()[0] / 2.0
        low = None
        for index in range(1, len(self.hz)):
            if (self.db[index - 1] - half) * (self.db[index] - half) <= 0.0:
                span = self.db[index] - self.db[index - 1]
                share = (half - self.db[index - 1]) / (span or 1e-30)
                edge = self.hz[index - 1] * ((self.hz[index]
                                              / self.hz[index - 1]) ** share)
                if low is None:
                    low = edge
                else:
                    return math.log(edge / low) / math.log(2.0)
        return None


def maker(rate, cls=None, fault=None, macros=None, **options):
    """A build closure: the class, the trait's settings, then the fault.

    `cls` is a parameter because `kit_faults.null_build_red` hands this file
    the class rebuilt as a wire and asks for the same measurement on it.
    `macros` is `{index: midi}`, applied after construction, which is how
    `macro_sweep` drives a span.
    """
    subject = cls or ParametricEQ

    def build(source):
        effect = subject.create(source, rate, **options)
        if macros:
            for index, position in macros.items():
                effect.set_macro(index, position)
        if fault is not None:
            fault(effect)
        return effect
    return build


def say(trait, verdict, detail):
    print("%-4s %-14s %s" % (trait, verdict, detail))


def result(values, red):
    return {"passed": not red, "red": red, "values": values}


# --- the settings each trait holds fixed, in one place ---------------------
#
# The evidence pack's "Held fixed" column is read from these dictionaries and
# the spans below are its "Quantified over" column, so a row cannot say one
# thing and the run do another.

T1_SETTINGS = dict(low_hz=60.0, low_boost=2.5, low_atten=2.5)
T2_SETTINGS = dict(high_hz=10000.0, high_boost=10.0, bandwidth=5.0,
                   atten_hz=5000.0, high_atten=10.0)
T3_SETTINGS = dict(high_hz=10000.0, high_boost=10.0)
T4_SETTINGS = dict(bell2_hz=1000.0)
T5_SETTINGS = dict(bell2_hz=1000.0)


def t1_points():
    points = grid(20.0, 20000.0, 45) + [30.0, 1000.0]
    return sorted(set(round(point, 4) for point in points))


def t2_points():
    #: 97 points over 1-20 kHz: 0.045 oct a step, half the 0.090 the first
    #: version used, and the peak is interpolated between them on top of that.
    return grid(1000.0, 20000.0, 97)


def t3_points(rate):
    return grid(2000.0, 22000.0 if rate > 44100 else rate * 0.45, 61)


def t4_points(centre=1000.0, rate=48000):
    low = max(20.0, centre / 5.0)
    high = min(rate * 0.45, centre * 8.0)
    return grid(low, high, 121)


def t5_points(rate):
    return grid(20.0, min(20000.0, rate * 0.45), 61)


# --- the faults, each of the kind its trait names --------------------------

def t1_shared_corner(effect):
    """T1's own first disconfirmation, and what the retired class builds."""
    effect._low_atten.frequency = effect._low_boost.frequency


def t2_a_shelf_not_a_bell(effect):
    """T2's first disconfirmation: the HF boost built as a shelf."""
    effect._high_boost.mode = audiobiquad.HIGH_SHELF


def t2_one_shared_selector(effect):
    """T2's *third* disconfirmation, which had no fault at all before this
    session: the HF boost's corner follows the attenuator's selector, so
    moving the cut moves the boost's peak. `_high_boost.frequency` cannot be
    driven to the attenuator's 20 kHz stop from any macro position - macro 10
    tops out at 16 kHz - which is what `fault_reachability` checks."""
    effect._high_boost.frequency = effect._high_atten.frequency


def t3_constant_gain_bandwidth(effect):
    """T3's named disconfirmation: a width-only knob, the sharp setting
    keeping the broad setting's gain."""
    effect._high_boost.gain_db = 9.0


def t4_gain_independent_law(effect):
    """T4's named disconfirmation - "a ratio near 1 is constant-Q outright" -
    planted as a law that reads one gain whatever the knob says.

    The fault this replaces was `set_macro(14, 127)`, the class's own `Q Law`
    toggle: a position a player dials, which `fault_reachability` rejects and
    the pattern revision calls "a disconfirmation waiting to be written
    down". The toggle is a setting T4 holds fixed, not a fault. Q(6 dB) is
    not `CONSTANT_Q`, so no macro position reaches the pair this forces.
    """
    effect._bells[1].Q = _module.proportional_q(6.0)


def t5_signed_gain_law(effect):
    """T5's named disconfirmation: a Q law reading the signed gain, so the
    cut is a different width from the boost while the peak still looks
    right."""
    effect._bells[1].Q = effect._bells[1].Q * 0.5


# --- the traits, as results a checker can read -----------------------------

def t1_result(rate, dry, cls=None, fault=None, level=LEVEL_DBFS, macros=None):
    clean = Curve("T1", rate, t1_points(),
                  maker(rate, cls=cls, fault=fault, macros=macros,
                        **T1_SETTINGS), dry, level=level)
    at30 = clean.at(30.0)
    floor, where = clean.minimum(100.0, 400.0)
    flat = clean.worst_above(1000.0)
    red = []
    if at30 < 2.0:
        red.append("30 Hz %+0.2f dB, bar +2.0" % at30)
    if floor > -1.0:
        red.append("minimum %+0.2f dB in 100-400 Hz, bar -1.0" % floor)
    if flat > 0.5:
        red.append("worst above 1 kHz %0.3f dB, bar 0.5" % flat)
    return result({"at_30_hz_db": at30, "minimum_db": floor,
                   "minimum_hz": where, "flat_above_1k_db": flat,
                   "flat_within_db": clean.flat_within()}, red)


def t2_bell(rate, dry, cls=None, fault=None, level=LEVEL_DBFS, macros=None,
            **overrides):
    """One curve's bell reading, which is what the third clause sweeps."""
    settings = dict(T2_SETTINGS, **overrides)
    curve = Curve("T2", rate, t2_points(),
                  maker(rate, cls=cls, fault=fault, macros=macros,
                        **settings), dry, level=level)
    bump = curve.local_maximum_near(10000.0)
    return curve, bump


def t2_result(rate, dry, cls=None, fault=None, level=LEVEL_DBFS, macros=None):
    curve, bump = t2_bell(rate, dry, cls=cls, fault=fault, level=level,
                          macros=macros)
    band = [(f, g) for f, g in zip(curve.hz, curve.db) if 3000.0 <= f <= 5000.0]
    monotonic = all(band[index + 1][1] <= band[index][1] + 0.05
                    for index in range(len(band) - 1))
    _high, other = t2_bell(rate, dry, cls=cls, fault=fault, level=level,
                           macros=macros, atten_hz=20000.0)
    moved = (abs(math.log(other[1] / bump[1]) / math.log(2.0))
             if bump and other else None)
    red = []
    if bump is None:
        red.append("no local maximum with %.1f dB of prominence anywhere on "
                   "the 1-20 kHz grid" % PROMINENCE_DB)
    elif bump[2] > 1.0 / 3.0:
        red.append("nearest bell %.0f Hz, %.3f oct from 10 kHz, bar 0.333"
                   % (bump[1], bump[2]))
    if not monotonic:
        red.append("the 3-5 kHz fall is not monotonic")
    if moved is None:
        red.append("the boost's peak cannot be found at one of the "
                   "selector's two stops, so the third clause has no reading")
    elif moved > 1.0 / 3.0:
        red.append("the peak moves %.3f oct when the cut selector moves, "
                   "bar 0.333" % moved)
    return result({"peak_db": bump[0] if bump else None,
                   "peak_hz": bump[1] if bump else None,
                   "distance_oct": bump[2] if bump else 99.0,
                   "prominence_db": bump[3] if bump else 0.0,
                   "peak_hz_at_20k": other[1] if other else None,
                   "monotonic": monotonic,
                   "band_from_db": band[0][1], "band_to_db": band[-1][1],
                   "moved_oct": moved,
                   "flat_within_db": curve.flat_within()}, red)


def t3_result(rate, dry, cls=None, fault=None, level=LEVEL_DBFS, macros=None,
              **overrides):
    """The fault is planted on the **sharp** build only: a width-only knob is
    the sharp setting keeping the broad setting's gain."""
    settings = dict(T3_SETTINGS, **overrides)
    points = t3_points(rate)
    broad = Curve("T3 broad", rate, points,
                  maker(rate, cls=cls, macros=macros, bandwidth=0.0,
                        **settings), dry, level=level)
    sharp = Curve("T3 sharp", rate, points,
                  maker(rate, cls=cls, fault=fault, macros=macros,
                        bandwidth=10.0, **settings), dry, level=level)
    gain = sharp.maximum()[0] - broad.maximum()[0]
    wide, narrow = broad.width_3db(), sharp.width_3db()
    red = []
    if not 6.0 <= gain <= 12.0:
        red.append("sharp minus broad %+0.2f dB, bar 6-12" % gain)
    if narrow is None or wide is None:
        red.append("no -3 dB width at one of the two stops: there is no bell "
                   "to measure")
    elif narrow > wide / 2.0:
        red.append("sharp width %.3f oct against broad %.3f oct, bar half"
                   % (narrow, wide))
    return result({"sharp_db": sharp.maximum()[0],
                   "broad_db": broad.maximum()[0],
                   "gain_difference_db": gain,
                   "sharp_width_oct": narrow, "broad_width_oct": wide},
                  red)


def t4_result(rate, dry, cls=None, fault=None, level=LEVEL_DBFS, macros=None,
              centre=1000.0):
    points = t4_points(centre, rate)
    crossings, widths, peaks = [], [], []
    for gain in (2.0, 6.0, 12.0):
        curve = Curve("T4 %+g" % gain, rate, points,
                      maker(rate, cls=cls, fault=fault, macros=macros,
                            bell2_hz=centre, bell2_db=gain), dry, level=level)
        crossings.append(curve.crossing_above(1.0, centre))
        widths.append(curve.half_gain_width())
        peaks.append(curve.maximum()[0])
    red = []
    if any(value is None for value in crossings):
        red.append("no +1 dB crossing above the centre at one of the three "
                   "gains: the bell is not there")
        spread = None
    else:
        spread = (max(crossings) - min(crossings)) / min(crossings) * 100.0
        if spread > 5.0:
            red.append("crossing spread %.2f %%, bar 5" % spread)
    if any(value is None for value in widths):
        red.append("no half-gain width at one of the three gains")
        ratio = None
    else:
        ratio = widths[0] / widths[-1]
        if ratio < 3.0:
            red.append("bandwidth ratio %.3fx, bar 3" % ratio)
    return result({"crossings_hz": crossings, "spread_pct": spread,
                   "widths_oct": widths, "bandwidth_ratio": ratio,
                   "peaks_db": peaks}, red)


def t5_result(rate, dry, cls=None, fault=None, level=LEVEL_DBFS, macros=None,
              gains=(6.0, 12.0, 16.0), centre=1000.0):
    """The fault is planted on the **cut** build only, which is what a signed
    Q law does. The presence clause is new this session: a flat build read
    0.0000 dB and passed, so the row could not tell a reciprocal bell from no
    bell (`docs/effects-phase2-gate-audit.md` section 1, T5)."""
    points = t5_points(rate)
    worst, presence = [], []
    for gain in gains:
        up = Curve("T5 +%g" % gain, rate, points,
                   maker(rate, cls=cls, macros=macros, bell2_hz=centre,
                         bell2_db=gain), dry, level=level)
        down = Curve("T5 -%g" % gain, rate, points,
                     maker(rate, cls=cls, fault=fault, macros=macros,
                           bell2_hz=centre, bell2_db=-gain), dry, level=level)
        product = [(abs(a + b), f) for a, b, f in zip(up.db, down.db, up.hz)]
        worst.append(max(product))
        presence.append(up.at(centre))
    red = []
    for gain, peak in zip(gains, presence):
        if peak < gain - 1.0:
            red.append("the +%g dB boost reads %+0.2f dB at the centre: "
                       "there is no bell to be the reciprocal of"
                       % (gain, peak))
    for gain, (value, where) in zip(gains, worst):
        if value > 0.1:
            red.append("G=%g: max |sum| %.4f dB at %.0f Hz, bar 0.1"
                       % (gain, value, where))
    return result({"worst_sum_db": max(value for value, _ in worst),
                   "worst_by_gain": [value for value, _ in worst],
                   "worst_hz": [where for _, where in worst],
                   "peaks_db": presence, "gains": list(gains)}, red)



def _where(hz):
    return "nowhere on the 1-20 kHz grid" if hz is None else "%.0f Hz" % hz


def _moved(value):
    """The third clause's reading, or the reason there is none. A sentinel
    printed as a number is a number nobody measured."""
    if value["moved_oct"] is None:
        return ("no reading: the bell is not on the grid at one of the "
                "selector's two stops")
    return "%.3f oct" % value["moved_oct"]


# --- the printed run ------------------------------------------------------

def _verdict(name, run, detail):
    say(name, "demonstrated" if run["passed"] else "MISSED", detail)
    return run["passed"]


def _fault(name, run, detail):
    say(name, "fault RED" if not run["passed"] else "FAULT NOT RED", detail)
    return not run["passed"]


def run_t1(rate, dry, level=LEVEL_DBFS):
    run = t1_result(rate, dry, level=level)
    value = run["values"]
    ok = _verdict("T1", run,
                  "30 Hz %+0.2f dB (bar +2.0) - minimum %+0.2f dB at %.1f Hz "
                  "(bar -1.0 in 100-400) - worst above 1 kHz %0.3f dB "
                  "(bar 0.5)"
                  % (value["at_30_hz_db"], value["minimum_db"],
                     value["minimum_hz"], value["flat_above_1k_db"]))
    red = t1_result(rate, dry, fault=t1_shared_corner, level=level)
    fault_value = red["values"]
    return ok, _fault("T1", red,
                      "one shared corner: minimum %+0.2f dB at %.1f Hz, "
                      "30 Hz %+0.2f dB"
                      % (fault_value["minimum_db"], fault_value["minimum_hz"],
                         fault_value["at_30_hz_db"]))


def run_t2(rate, dry, level=LEVEL_DBFS):
    run = t2_result(rate, dry, level=level)
    value = run["values"]
    ok = _verdict("T2", run,
                  "local maximum %s - 3->5 kHz monotonic fall %s "
                  "(%+0.2f -> %+0.2f dB) - that maximum moves %s when the "
                  "atten selector goes 5 -> 20 kHz - curve is %.6f dB from "
                  "flat"
                  % ("none with %.1f dB of prominence" % PROMINENCE_DB
                     if value["peak_hz"] is None else
                     "%+0.2f dB at %.0f Hz (%.3f oct from 10 kHz, bar 0.333, "
                     "prominence %.2f dB, bar %.1f)"
                     % (value["peak_db"], value["peak_hz"],
                        value["distance_oct"], value["prominence_db"],
                        PROMINENCE_DB),
                     value["monotonic"], value["band_from_db"],
                     value["band_to_db"], _moved(value),
                     value["flat_within_db"]))
    shelf = t2_result(rate, dry, fault=t2_a_shelf_not_a_bell, level=level)
    red_one = _fault("T2", shelf,
                     "HF boost built as a shelf: %s"
                     % ("no local maximum with %.1f dB of prominence on the "
                        "1-20 kHz grid" % PROMINENCE_DB
                        if shelf["values"]["peak_hz"] is None else
                        "nearest local maximum %+0.2f dB at %.0f Hz "
                        "(%.3f oct off)"
                        % (shelf["values"]["peak_db"],
                           shelf["values"]["peak_hz"],
                           shelf["values"]["distance_oct"])))
    shared = t2_result(rate, dry, fault=t2_one_shared_selector, level=level)
    red_two = _fault("T2", shared,
                     "one shared selector: the boost's peak is %s with the "
                     "cut at 5 kHz and %s with it at 20 kHz, %s (bar 0.333)"
                     % (_where(shared["values"]["peak_hz"]),
                        _where(shared["values"]["peak_hz_at_20k"]),
                        _moved(shared["values"])))
    return ok, red_one and red_two


def run_t3(rate, dry, level=LEVEL_DBFS):
    run = t3_result(rate, dry, level=level)
    value = run["values"]
    ok = _verdict("T3", run,
                  "sharp %+0.2f dB, broad %+0.2f dB, difference %+0.2f dB "
                  "(bar 6-12) - -3 dB width %.3f oct sharp against %.3f oct "
                  "broad (bar half) - probe %.0f dBFS"
                  % (value["sharp_db"], value["broad_db"],
                     value["gain_difference_db"],
                     value["sharp_width_oct"] or -1,
                     value["broad_width_oct"] or -1, level))
    red = t3_result(rate, dry, fault=t3_constant_gain_bandwidth, level=level)
    return ok, _fault("T3", red,
                      "constant-gain bandwidth: difference %+0.2f dB"
                      % red["values"]["gain_difference_db"])


def run_t4(rate, dry, level=LEVEL_DBFS):
    run = t4_result(rate, dry, level=level)
    value = run["values"]
    ok = _verdict("T4", run,
                  "+1 dB crossings %s Hz (spread %s %%, bar 5) - mid-gain "
                  "bandwidth %s oct, +2 -> +12 ratio %.3fx (bar 3)"
                  % (["%.1f" % point for point in value["crossings_hz"]],
                     "n/a" if value["spread_pct"] is None
                     else "%.2f" % value["spread_pct"],
                     ["%.3f" % width for width in value["widths_oct"]],
                     value["bandwidth_ratio"] or 0.0))
    red = t4_result(rate, dry, fault=t4_gain_independent_law, level=level)
    fault_value = red["values"]
    return ok, _fault("T4", red,
                      "a gain-independent Q law (Q(6 dB) at every gain): "
                      "crossings %s Hz (spread %s %%), bandwidth %s oct, "
                      "ratio %.3fx"
                      % (["%.1f" % point
                          for point in fault_value["crossings_hz"]],
                         "n/a" if fault_value["spread_pct"] is None
                         else "%.2f" % fault_value["spread_pct"],
                         ["%.3f" % width
                          for width in fault_value["widths_oct"]],
                         fault_value["bandwidth_ratio"] or 0.0))


def run_t5(rate, dry, level=LEVEL_DBFS):
    run = t5_result(rate, dry, level=level)
    value = run["values"]
    ok = _verdict("T5", run,
                  "max |sum| "
                  + ", ".join("%.4f dB at %.0f Hz (G=%g, peak %+0.2f dB)"
                              % (worst, where, gain, peak)
                              for worst, where, gain, peak
                              in zip(value["worst_by_gain"],
                                     value["worst_hz"], value["gains"],
                                     value["peaks_db"]))
                  + " - probe %.0f dBFS" % level)
    red = t5_result(rate, dry, fault=t5_signed_gain_law, level=level,
                    gains=(12.0,))
    fault_value = red["values"]
    return ok, _fault("T5", red,
                      "signed-gain Q law: max |sum| %.4f dB at %.0f Hz "
                      "(G=12), and the peak still reads %+0.2f dB - which is "
                      "what makes it sly"
                      % (fault_value["worst_sum_db"],
                         fault_value["worst_hz"][0],
                         fault_value["peaks_db"][0]))


TRAITS = {"T1": run_t1, "T2": run_t2, "T3": run_t3, "T4": run_t4,
          "T5": run_t5}
RESULTS = {"T1": t1_result, "T2": t2_result, "T3": t3_result,
           "T4": t4_result, "T5": t5_result}


# --- the two kit gatekeepers ----------------------------------------------

def quiet_source(rate, frames=512):
    """Something to build against when nothing is being rendered."""
    return probes.ArraySource(bytes(frames * 4), rate=rate, block=256)


#: One row per planted fault: the trait it serves, the fault, what to read off
#: a built instance, and the settings the reading is taken at. The reading
#: names the settings the trait **holds fixed** as well as the state the fault
#: forces, because a state read without them is reachable at some other
#: setting and the check would reject a fault that is sound: `_high_boost`
#: does read 9.0 dB at High Boost 5 - it is 9.0 dB *at full boost, sharp* that
#: no macro position reaches.
FAULT_CHECKS = (
    ("T1", t1_shared_corner,
     lambda e: (e._low_atten.mix,
                round(e._low_atten.frequency / e._low_boost.frequency, 6)),
     T1_SETTINGS),
    ("T2 shelf", t2_a_shelf_not_a_bell,
     lambda e: (e._high_boost.mix, e._high_boost.mode), T2_SETTINGS),
    ("T2 selector", t2_one_shared_selector,
     lambda e: round(e._high_boost.frequency, 6),
     dict(T2_SETTINGS, atten_hz=20000.0)),
    ("T3", t3_constant_gain_bandwidth,
     lambda e: (round(e.macro(11), 6), round(e._high_boost.Q, 6),
                round(e._high_boost.gain_db, 6)),
     dict(T3_SETTINGS, bandwidth=10.0)),
    ("T4", t4_gain_independent_law,
     lambda e: (round(e.macro(6), 6), round(e._bells[1].Q, 6)),
     dict(T4_SETTINGS, bell2_db=12.0)),
    ("T5", t5_signed_gain_law,
     lambda e: (round(e.macro(6), 6), round(e._bells[1].Q, 6)),
     dict(T5_SETTINGS, bell2_db=-12.0)),
)


def faulted_state(rate, fault, reading, settings):
    effect = ParametricEQ.create(quiet_source(rate), rate, **settings)
    try:
        fault(effect)
        return reading(effect)
    finally:
        effect.deinit()


def checks(rate, wanted):
    """`--checks`: the null-build red and the fault-reachability check, from
    `tests/support/kit_faults.py`, over every trait and every fault."""
    dry = {}
    bad = 0
    print("NULL-BUILD RED - the same measurement on the class built as a wire")
    for name in wanted:
        measure = RESULTS[name]

        def measure_with(cls, measure=measure):
            return measure(rate, dry, cls=cls)
        try:
            found = faults.null_build_red(ParametricEQ, measure_with,
                                          label="ParametricEQ %s" % name)
            say(name, "null red", "wire: %s"
                % "; ".join(found["null"]["red"]))
        except (faults.NullBuildGreen, faults.ControlRed) as error:
            bad += 1
            say(name, "CHECK FAILED", str(error))
    print("")
    print("FAULT REACHABILITY - a fault the surface can dial is not a fault")
    for name, fault, reading, settings in FAULT_CHECKS:
        if name.split()[0] not in wanted:
            continue
        target = faulted_state(rate, fault, reading, settings)

        def build(cls, settings=settings):
            return cls.create(quiet_source(rate), rate, **settings)
        try:
            found = faults.fault_reachability(
                ParametricEQ, target, reading, build,
                label="ParametricEQ %s" % name)
            say(name, "unreachable",
                "fault reads %r, class reads %r, %d macro positions and "
                "patches walked" % (found["target"], found["clean"],
                                    found["checked"]))
        except (faults.FaultReachable, faults.FaultInert) as error:
            bad += 1
            say(name, "CHECK FAILED", str(error))
    print("")
    print("%d checks failed" % bad)
    return bad


# --- the level axis T3 and T5 left free ------------------------------------

def levels(rate, wanted):
    """`--levels`: every trait at every probe level, so a row that holds at
    one level says where it stops. T3 and T5 are the two the gate audit
    disconfirmed above -16 dBFS; T1 and T4 are run beside them as the
    controls that do not move."""
    dry = {}
    bad = 0
    for name in wanted:
        print("%s over the probe level" % name)
        for level in LEVELS:
            run = RESULTS[name](rate, dry, level=level)
            value = run["values"]
            if name == "T3":
                figure = ("difference %+0.2f dB (bar 6-12)"
                          % value["gain_difference_db"])
            elif name == "T5":
                figure = ("max |sum| %s dB (bar 0.1), peaks %s dB"
                          % (["%.4f" % worst
                              for worst in value["worst_by_gain"]],
                             ["%+0.2f" % peak for peak in value["peaks_db"]]))
            elif name == "T1":
                figure = ("30 Hz %+0.2f dB, minimum %+0.2f dB, flat %0.3f dB"
                          % (value["at_30_hz_db"], value["minimum_db"],
                             value["flat_above_1k_db"]))
            elif name == "T4":
                figure = ("spread %s %%, ratio %.3fx"
                          % ("n/a" if value["spread_pct"] is None
                             else "%.2f" % value["spread_pct"],
                             value["bandwidth_ratio"] or 0.0))
            else:
                figure = ("distance %.3f oct, prominence %.2f dB, moved %s"
                          % (value["distance_oct"], value["prominence_db"],
                             _moved(value)))
            print("  %-6.1f dBFS  %-8s %s"
                  % (level, "holds" if run["passed"] else "MISSED", figure))
            bad += 0 if run["passed"] else 1
        print("")
    print("%d (trait, level) cells outside the bar" % bad)
    return bad


# --- the checks, shown failing ---------------------------------------------

def prove(rate):
    """`--prove`: the two gatekeepers shown **failing**, on the two
    measurements and the one fault this session retired.

    A check that has only ever passed has not been shown to work. `--checks`
    prints three green columns; this mode plants the retired code back and
    requires each check to raise. It is the workspace's own "prove a checker
    can fail" rule applied to the checkers themselves.
    """
    dry = {}
    bad = 0

    # 1. T2 under the retired plateau rule: `>=` on both sides, no
    #    prominence. Every interior point of a flat curve qualifies.
    original = Curve.local_maximum_near

    def plateau_rule(self, hz, prominence_db=PROMINENCE_DB):
        found = [(abs(math.log(self.hz[index] / hz) / math.log(2.0)),
                  self.hz[index], self.db[index], 0.0)
                 for index in range(1, len(self.hz) - 1)
                 if self.db[index] >= self.db[index - 1]
                 and self.db[index] >= self.db[index + 1]]
        if not found:
            return None
        distance, where, level, prominence = min(found)
        return level, where, distance, prominence

    Curve.local_maximum_near = plateau_rule
    try:
        faults.null_build_red(
            ParametricEQ, lambda cls: t2_result(rate, dry, cls=cls),
            label="ParametricEQ T2 (retired plateau rule)")
        say("T2", "NOT CAUGHT", "the retired rule read RED on a wire, which "
                                "is not what the refutation pass found")
        bad += 1
    except faults.NullBuildGreen as error:
        say("T2", "caught", str(error))
    finally:
        Curve.local_maximum_near = original

    # 2. T5 without the presence clause: a flat build reads 0.0000 dB and
    #    passes, which is what the independent pass found.
    def without_presence(cls):
        run = t5_result(rate, dry, cls=cls)
        return result(run["values"],
                      [entry for entry in run["red"]
                       if "reciprocal of" not in entry])

    try:
        faults.null_build_red(ParametricEQ, without_presence,
                              label="ParametricEQ T5 (no presence clause)")
        say("T5", "NOT CAUGHT", "the row read RED on a wire without its "
                                "presence clause")
        bad += 1
    except faults.NullBuildGreen as error:
        say("T5", "caught", str(error))

    # 3. T4's retired fault: the class's own `Q Law` toggle at 127.
    def toggle(effect):
        effect.set_macro(14, 127)

    def reading(effect):
        return (round(effect.macro(6), 6), round(effect._bells[1].Q, 6))

    settings = dict(T4_SETTINGS, bell2_db=12.0)
    target = faulted_state(rate, toggle, reading, settings)
    try:
        faults.fault_reachability(
            ParametricEQ, target, reading,
            lambda cls: cls.create(quiet_source(rate), rate, **settings),
            label="ParametricEQ T4 (retired Q Law fault)")
        say("T4", "NOT CAUGHT", "the toggle position was not found on the "
                                "macro grid, which cannot be right")
        bad += 1
    except (faults.FaultReachable, faults.FaultInert) as error:
        say("T4", "caught", str(error))

    print("")
    print("%d of 3 retired checks went uncaught" % bad)
    return bad


# --- the shipped patches ---------------------------------------------------

def patch_curve_points(rate):
    return grid(20.0, min(20000.0, rate * 0.45), 61)


def patches(rate, level=LEVEL_DBFS):
    """`--patches`: every shipped patch, read back off the instance, with the
    Tier 2 rows' own figures taken on the patch's own curve.

    The revised evidence template asks for this before any chosen operating
    point: a shipped patch is a setting the class's author published and
    expects a player to use, so a trait the class misses there is not a
    corner case. A patch that does not engage a mechanism is reported as not
    engaging it - which is a reading about the patch, not a miss by the
    trait.
    """
    dry = {}
    points = patch_curve_points(rate)
    bad = 0
    for index in sorted(ParametricEQ.PATCHES):
        name = ParametricEQ.PATCHES[index][0]
        subject = ParametricEQ.create(quiet_source(rate), rate)
        subject.program_change(index)
        settings = {label: round(subject.macro(number), 3)
                    for number, label
                    in enumerate(ParametricEQ.MACRO_LABELS)}
        live = [node_name for node_name, node
                in (("low_atten", subject._low_atten),
                    ("high_atten", subject._high_atten),
                    ("bell1", subject._bells[0]), ("bell2", subject._bells[1]),
                    ("bell3", subject._bells[2]),
                    ("low_boost", subject._low_boost),
                    ("high_boost", subject._high_boost),
                    ("output", subject._output_trim))
                if node.mix != 0.0]
        high_hz = settings["High Freq"]
        subject.deinit()
        curve = Curve("patch %d" % index, rate, points,
                      maker(rate, patch=index), dry, level=level)
        print("patch %d %-24s live: %s"
              % (index, name, ", ".join(live) or "none - this patch is a wire"))
        print("    curve %.3f dB from flat, peak %+0.2f dB at %.0f Hz"
              % (curve.flat_within(), curve.maximum()[0], curve.maximum()[1]))
        low_engaged = ("low_boost" in live) or ("low_atten" in live)
        if low_engaged:
            floor, where = curve.minimum(100.0, 400.0)
            print("    T1  30 Hz %+0.2f dB - minimum %+0.2f dB at %.1f Hz - "
                  "worst above 1 kHz %0.3f dB"
                  % (curve.at(30.0), floor, where, curve.worst_above(1000.0)))
        else:
            print("    T1  not engaged: Low Boost %.1f, Low Atten %.1f"
                  % (settings["Low Boost"], settings["Low Atten"]))
        if "high_boost" in live:
            # Read with no prominence bar as well, so a patch that misses it
            # reports the number it missed by rather than an absence.
            bump = curve.local_maximum_near(high_hz, prominence_db=0.0)
            if bump is None:
                print("    T2  no local maximum at all near %.0f Hz: the "
                      "lift is monotone through the corner" % high_hz)
                bad += 1
            else:
                print("    T2  bell %+0.2f dB at %.0f Hz, %.3f oct from this "
                      "patch's High Freq %.0f Hz, prominence %.2f dB (bar "
                      "%.1f)%s"
                      % (bump[0], bump[1], bump[2], high_hz, bump[3],
                         PROMINENCE_DB,
                         "" if bump[3] >= PROMINENCE_DB
                         else " - UNDER THE BAR"))
                if bump[2] > 1.0 / 3.0 or bump[3] < PROMINENCE_DB:
                    bad += 1
        else:
            print("    T2  not engaged: High Boost %.1f"
                  % settings["High Boost"])
        bells = [number for number in range(3)
                 if abs(settings["Bell %d Gain" % (number + 1)]) >= _module.FLAT_DB]
        print("    T4/T5 bells engaged: %s"
              % (", ".join("bell %d at %+0.1f dB, %.0f Hz"
                           % (number + 1,
                              settings["Bell %d Gain" % (number + 1)],
                              settings["Bell %d Freq" % (number + 1)])
                           for number in bells) or "none"))
        print("")
    print("%d shipped patches read a bell outside T2's bar" % bad)
    return bad


# --- the macro spans -------------------------------------------------------

#: `Bell 2 Freq` is a 20 Hz-20 kHz log macro and T4 and T5 read a bell's
#: skirts, so the sweep runs the part of its travel where both skirts are in
#: band at 48 kHz: MIDI 30 (100 Hz) to MIDI 105 (6 kHz). Outside it the
#: -3 dB points fall off the grid and the figure is the grid's, not the
#: class's - which is the defect this driver exists to catch, so the span is
#: named here rather than left to the reader.
BELL_SPAN = (30, 105)


def sweeps(rate, wanted):
    """`--sweeps`: each row's *Quantified over* column, run through
    `effect_measurements.macro_sweep`, worst cell reported."""
    dry = {}
    bad = 0

    if "T2" in wanted:
        subject = ParametricEQ.create(quiet_source(rate), rate, **T2_SETTINGS)

        def measure_t2(settings):
            _curve, bump = t2_bell(rate, dry, macros=settings)
            return {"values": {"distance_oct": 99.0 if bump is None
                               else bump[2],
                               "prominence_db": 0.0 if bump is None
                               else bump[3]}}
        found = kit.macro_sweep(subject, [kit.MacroSpan(12, midpoints=1)],
                                measure_t2, figure="distance_oct",
                                worst="max", bar=1.0 / 3.0,
                                name="T2 SWEEP Atten Freq")
        subject.deinit()
        bad += _sweep_line("T2", "Atten Freq 5-20 kHz, the cut selector's own "
                           "travel", found, "oct from 10 kHz")

    if "T3" in wanted:
        subject = ParametricEQ.create(quiet_source(rate), rate, **T3_SETTINGS)

        def measure_t3(settings):
            return t3_result(rate, dry, macros=settings)
        found = kit.macro_sweep(subject, [kit.MacroSpan(10, midpoints=1)],
                                measure_t3, figure="gain_difference_db",
                                worst="min", name="T3 SWEEP High Freq")
        subject.deinit()
        inside = all(6.0 <= cell["figure"] <= 12.0
                     for cell in found["values"]["cells"])
        bad += 0 if inside else 1
        print("T3   sweep %-9s High Freq 3-16 kHz, which T3 does not fix: "
              "worst %+0.2f dB at %s (bar 6-12), %d cells"
              % ("holds" if inside else "MISSED", found["values"]["worst"],
                 found["values"]["at_units"], found["values"]["points"]))

    if "T4" in wanted:
        subject = ParametricEQ.create(quiet_source(rate), rate, **T4_SETTINGS)

        def measure_t4(settings):
            centre = subject.macro(5)
            return t4_result(rate, dry, macros=settings, centre=centre)
        found = kit.macro_sweep(
            subject, [kit.MacroSpan(5, BELL_SPAN[0], BELL_SPAN[1],
                                    midpoints=2)],
            measure_t4, figure="bandwidth_ratio", worst="min",
            name="T4 SWEEP Bell 2 Freq")
        subject.deinit()
        worst = found["values"]["worst"]
        bad += 0 if worst >= 3.0 else 1
        print("T4   sweep %-9s Bell 2 Freq 100 Hz-6 kHz, which T4 fixes at "
              "1 kHz: worst ratio %.3fx at %s (bar 3), %d cells"
              % ("holds" if worst >= 3.0 else "MISSED", worst,
                 found["values"]["at_units"], found["values"]["points"]))

    if "T5" in wanted:
        subject = ParametricEQ.create(quiet_source(rate), rate, **T5_SETTINGS)

        def measure_t5(settings):
            centre = subject.macro(5)
            return t5_result(rate, dry, macros=settings, centre=centre,
                             gains=(16.0,))
        found = kit.macro_sweep(
            subject, [kit.MacroSpan(5, BELL_SPAN[0], BELL_SPAN[1],
                                    midpoints=2)],
            measure_t5, figure="worst_sum_db", worst="max", bar=0.1,
            name="T5 SWEEP Bell 2 Freq")
        subject.deinit()
        bad += _sweep_line("T5", "Bell 2 Freq 100 Hz-6 kHz at G=16, which T5 "
                           "fixes at 1 kHz", found, "dB max |sum|")

    print("")
    print("%d sweeps outside the bar" % bad)
    return bad


def _sweep_line(name, span, found, unit):
    value = found["values"]
    say(name, "sweep holds" if found["passed"] else "SWEEP MISSED",
        "%s: worst %.3f %s at %s, %d cells, spread %.3f"
        % (span, value["worst"], unit, value["at_units"], value["points"],
           value["spread"]))
    return 0 if found["passed"] else 1


def main(argv):
    rate = 48000
    level = LEVEL_DBFS
    wanted = ["T1", "T2", "T3", "T4", "T5"]
    if "--rate" in argv:
        rate = int(argv[argv.index("--rate") + 1])
    if "--level" in argv:
        level = float(argv[argv.index("--level") + 1])
    if "--traits" in argv:
        wanted = argv[argv.index("--traits") + 1].split(",")
    if "--checks" in argv:
        return 1 if checks(rate, wanted) else 0
    if "--levels" in argv:
        print("ParametricEQ Tier 2 over the probe level, %d Hz" % rate)
        return 1 if levels(rate, wanted) else 0
    if "--prove" in argv:
        print("ParametricEQ: the two kit checks shown failing, %d Hz" % rate)
        return 1 if prove(rate) else 0
    if "--patches" in argv:
        print("ParametricEQ over its seven shipped patches, %d Hz, %.0f dBFS"
              % (rate, level))
        return 1 if patches(rate, level=level) else 0
    if "--sweeps" in argv:
        print("ParametricEQ Tier 2 over its macro spans, %d Hz, %.0f dBFS"
              % (rate, level))
        return 1 if sweeps(rate, wanted) else 0
    print("ParametricEQ Tier 2 at %d Hz, %g s tones at %.0f dBFS"
          % (rate, SECONDS, level))
    dry = {}
    bad = 0
    for name in wanted:
        clean, red = TRAITS[name](rate, dry, level=level)
        bad += (0 if clean else 1) + (0 if red else 1)
        print("")
    print("%d of %d results off" % (bad, 2 * len(wanted)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
