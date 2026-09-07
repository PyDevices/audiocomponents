"""ParametricEQ's Tier 2 traits, measured with the kit, each beside the
planted fault of the same kind that has to turn it red.

CPython with numpy, like the rest of `tools/effect_measurements.py`: the
excitation is a set of steady tones rendered one at a time through the class
and through a bare wire, and every number below comes from
`effect_measurements.response()` reading those renders. Nothing here is
computed from a re-derivation of RBJ.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/parametriceq_traits.py \
        [--rate 48000] [--traits T1,T2,...]
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import audiobiquad                                       # noqa: E402
import audioeffects                                      # noqa: E402
import effect_measurements as kit                        # noqa: E402
import kit_probes as probes                              # noqa: E402

SECONDS = 0.5
LEVEL_DBFS = -20.0


def grid(low, high, points):
    return [low * (high / low) ** (index / (points - 1.0))
            for index in range(points)]


def render_tone(hz, rate, build=None, seconds=SECONDS):
    frames = int(rate * seconds)
    material = probes.sine(hz, seconds, LEVEL_DBFS, rate=rate, channels=2)
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

    def __init__(self, name, rate, frequencies, build, dry_cache):
        wet, dry = {}, {}
        for hz in frequencies:
            if hz not in dry_cache:
                dry_cache[hz] = render_tone(hz, rate)[0]
            dry[hz] = dry_cache[hz]
            render, effect = render_tone(hz, rate, build)
            wet[hz] = render
            effect.deinit()
        self.name = name
        self.result = kit.response(wet, dry)
        self.hz = [point["hz"] for point in self.result["values"]["grid"]]
        self.db = [point["magnitude_db"]
                   for point in self.result["values"]["grid"]]

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

    def local_maximum_near(self, hz):
        """The interior local maximum closest to `hz`, in octaves, or None.

        T2 asks for a *local* maximum, and the global one is somewhere else
        entirely: with the HF attenuator at full cut the whole top of the
        band sits 20 dB down, so the loudest point on a 1-20 kHz grid is its
        low end whether the boost is a bell or not. Reading the global peak
        would have called the trait missed on a build that meets it, and
        called the shelf fault red for the wrong reason.
        """
        found = [(abs(math.log(self.hz[i] / hz) / math.log(2.0)), self.hz[i],
                  self.db[i])
                 for i in range(1, len(self.hz) - 1)
                 if self.db[i] >= self.db[i - 1] and self.db[i] >= self.db[i + 1]]
        if not found:
            return None
        distance, where, level = min(found)
        return level, where, distance

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


def maker(rate, fault=None, **options):
    def build(source):
        effect = audioeffects.create('ParametricEQ', source, rate, **options)
        if fault is not None:
            fault(effect)
        return effect
    return build


def say(trait, verdict, detail):
    print("%-4s %-14s %s" % (trait, verdict, detail))


def t1(rate, dry):
    points = grid(20.0, 20000.0, 45) + [30.0, 1000.0]
    points = sorted(set(round(p, 4) for p in points))
    settings = dict(low_hz=60.0, low_boost=2.5, low_atten=2.5)
    clean = Curve("T1", rate, points, maker(rate, **settings), dry)
    at30 = clean.at(30.0)
    floor, where = clean.minimum(100.0, 400.0)
    flat = clean.worst_above(1000.0)
    ok = at30 >= 2.0 and floor <= -1.0 and 100.0 <= where <= 400.0 \
        and flat <= 0.5
    say("T1", "demonstrated" if ok else "MISSED",
        "30 Hz %+0.2f dB (bar +2.0) - minimum %+0.2f dB at %.1f Hz (bar "
        "-1.0 in 100-400) - worst above 1 kHz %0.3f dB (bar 0.5)"
        % (at30, floor, where, flat))

    def shared_corner(effect):
        effect._low_atten.frequency = effect._low_boost.frequency

    red = Curve("T1 fault", rate, points,
                maker(rate, fault=shared_corner, **settings), dry)
    floor_f, where_f = red.minimum(100.0, 400.0)
    say("T1", "fault RED" if floor_f > -1.0 else "FAULT NOT RED",
        "one shared corner: minimum %+0.2f dB at %.1f Hz, 30 Hz %+0.2f dB"
        % (floor_f, where_f, red.at(30.0)))
    return ok, floor_f > -1.0


def t2(rate, dry):
    points = grid(1000.0, 20000.0, 49)
    settings = dict(high_hz=10000.0, high_boost=10.0, bandwidth=5.0,
                    atten_hz=5000.0, high_atten=10.0)
    clean = Curve("T2", rate, points, maker(rate, **settings), dry)
    bump = clean.local_maximum_near(10000.0)
    near = bump is not None and bump[2] <= 1.0 / 3.0
    band = [(f, g) for f, g in zip(clean.hz, clean.db) if 3000.0 <= f <= 5000.0]
    monotonic = all(band[i + 1][1] <= band[i][1] + 0.05
                    for i in range(len(band) - 1))
    high = Curve("T2 atten 20k", rate, points,
                 maker(rate, **dict(settings, atten_hz=20000.0)), dry)
    other = high.local_maximum_near(10000.0)
    moved = (abs(math.log(other[1] / bump[1]) / math.log(2.0))
             if bump and other else 99.0)
    ok = near and monotonic and moved <= 1.0 / 3.0
    say("T2", "demonstrated" if ok else "MISSED",
        "local maximum %s - 3->5 kHz monotonic fall %s (%+0.2f -> %+0.2f dB) "
        "- that maximum moves %.3f oct when the atten selector goes 5 -> "
        "20 kHz"
        % ("none within reach of 10 kHz" if bump is None
           else "%+0.2f dB at %.0f Hz (%.3f oct from 10 kHz, bar 0.333)"
           % (bump[0], bump[1], bump[2]),
           monotonic, band[0][1], band[-1][1], moved))

    def a_shelf_not_a_bell(effect):
        effect._high_boost.mode = audiobiquad.HIGH_SHELF

    red = Curve("T2 fault", rate, points,
                maker(rate, fault=a_shelf_not_a_bell, **settings), dry)
    bump_f = red.local_maximum_near(10000.0)
    near_f = bump_f is not None and bump_f[2] <= 1.0 / 3.0
    say("T2", "fault RED" if not near_f else "FAULT NOT RED",
        "HF boost built as a shelf: %s"
        % ("no local maximum anywhere on the 1-20 kHz grid" if bump_f is None
           else "nearest local maximum %+0.2f dB at %.0f Hz (%.3f oct off)"
           % (bump_f[0], bump_f[1], bump_f[2])))
    return ok, not near_f


def t3(rate, dry):
    points = grid(2000.0, 22000.0 if rate > 44100 else rate * 0.45, 61)
    broad = Curve("T3 broad", rate, points,
                  maker(rate, high_hz=10000.0, high_boost=10.0,
                        bandwidth=0.0), dry)
    sharp = Curve("T3 sharp", rate, points,
                  maker(rate, high_hz=10000.0, high_boost=10.0,
                        bandwidth=10.0), dry)
    gain = sharp.maximum()[0] - broad.maximum()[0]
    wide, narrow = broad.width_3db(), sharp.width_3db()
    ok = 6.0 <= gain <= 12.0 and narrow is not None and wide is not None \
        and narrow <= wide / 2.0
    say("T3", "demonstrated" if ok else "MISSED",
        "sharp %+0.2f dB, broad %+0.2f dB, difference %+0.2f dB (bar 6-12) - "
        "-3 dB width %.3f oct sharp against %.3f oct broad (bar half)"
        % (sharp.maximum()[0], broad.maximum()[0], gain, narrow or -1,
           wide or -1))

    def width_only(effect):
        # A constant-gain Q knob: the sharp setting keeps the broad gain.
        effect._high_boost.gain_db = 9.0

    red = Curve("T3 fault", rate, points,
                maker(rate, fault=width_only, high_hz=10000.0,
                      high_boost=10.0, bandwidth=10.0), dry)
    gain_f = red.maximum()[0] - broad.maximum()[0]
    say("T3", "fault RED" if not 6.0 <= gain_f <= 12.0 else "FAULT NOT RED",
        "constant-gain bandwidth: difference %+0.2f dB" % gain_f)
    return ok, not 6.0 <= gain_f <= 12.0


def t4(rate, dry):
    points = grid(200.0, 8000.0, 121)
    crossings, widths = [], []
    for gain in (2.0, 6.0, 12.0):
        curve = Curve("T4 %+g" % gain, rate, points,
                      maker(rate, bell2_hz=1000.0, bell2_db=gain), dry)
        crossings.append(curve.crossing_above(1.0, 1000.0))
        half = curve.maximum()[0] / 2.0
        low = None
        for index in range(1, len(curve.hz)):
            if (curve.db[index - 1] - half) * (curve.db[index] - half) <= 0.0:
                span = curve.db[index] - curve.db[index - 1]
                share = (half - curve.db[index - 1]) / (span or 1e-30)
                edge = curve.hz[index - 1] * ((curve.hz[index]
                                               / curve.hz[index - 1]) ** share)
                if low is None:
                    low = edge
                else:
                    widths.append(math.log(edge / low) / math.log(2.0))
                    break
    spread = (max(crossings) - min(crossings)) / min(crossings) * 100.0
    ratio = widths[0] / widths[-1] if len(widths) >= 2 else 0.0
    ok = spread <= 5.0 and ratio >= 3.0
    say("T4", "demonstrated" if ok else "MISSED",
        "+1 dB crossings %s Hz (spread %.2f %%, bar 5) - mid-gain bandwidth "
        "%s oct, +2 -> +12 ratio %.3fx (bar 3)"
        % (["%.1f" % c for c in crossings], spread,
           ["%.3f" % w for w in widths], ratio))

    fault_crossings = []
    for gain in (2.0, 12.0):
        def constant(effect):
            effect.set_macro(14, 127)
        curve = Curve("T4 fault %+g" % gain, rate, points,
                      maker(rate, fault=constant, bell2_hz=1000.0,
                            bell2_db=gain), dry)
        fault_crossings.append(curve.crossing_above(1.0, 1000.0))
    spread_f = ((max(fault_crossings) - min(fault_crossings))
                / min(fault_crossings) * 100.0)
    say("T4", "fault RED" if spread_f > 5.0 else "FAULT NOT RED",
        "constant Q: crossings %s Hz, spread %.2f %%"
        % (["%.1f" % c for c in fault_crossings], spread_f))
    return ok, spread_f > 5.0


def t5(rate, dry):
    points = grid(20.0, 20000.0, 61)
    worst = []
    for gain in (6.0, 12.0, 16.0):
        up = Curve("T5 +%g" % gain, rate, points,
                   maker(rate, bell2_hz=1000.0, bell2_db=gain), dry)
        down = Curve("T5 -%g" % gain, rate, points,
                     maker(rate, bell2_hz=1000.0, bell2_db=-gain), dry)
        product = [(abs(a + b), f) for a, b, f in zip(up.db, down.db, up.hz)]
        worst.append(max(product))
    ok = all(value <= 0.1 for value, _ in worst)
    say("T5", "demonstrated" if ok else "MISSED",
        "max |sum| " + ", ".join("%.4f dB at %.0f Hz (G=%g)"
                                 % (v, f, g)
                                 for (v, f), g in zip(worst,
                                                      (6.0, 12.0, 16.0))))

    def signed(effect):
        # The named way T5 fails: a Q law that reads the signed gain, so the
        # cut is a different width from the boost while the peak still looks
        # right.
        effect._bells[1].Q = effect._bells[1].Q * 0.5

    up = Curve("T5 fault +12", rate, points,
               maker(rate, bell2_hz=1000.0, bell2_db=12.0), dry)
    down = Curve("T5 fault -12", rate, points,
                 maker(rate, fault=signed, bell2_hz=1000.0, bell2_db=-12.0),
                 dry)
    product = [(abs(a + b), f) for a, b, f in zip(up.db, down.db, up.hz)]
    peak_error = abs(up.at(1000.0) + down.at(1000.0))
    value, where = max(product)
    say("T5", "fault RED" if value > 0.1 else "FAULT NOT RED",
        "signed-gain Q law: max |sum| %.4f dB at %.0f Hz, and only %.4f dB "
        "at the peak - which is what makes it sly" % (value, where,
                                                      peak_error))
    return ok, value > 0.1


TRAITS = {"T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5}


def main(argv):
    rate = 48000
    wanted = list(TRAITS)
    if "--rate" in argv:
        rate = int(argv[argv.index("--rate") + 1])
    if "--traits" in argv:
        wanted = argv[argv.index("--traits") + 1].split(",")
    print("ParametricEQ Tier 2 at %d Hz, %g s tones at %.0f dBFS"
          % (rate, SECONDS, LEVEL_DBFS))
    dry = {}
    bad = 0
    for name in wanted:
        clean, red = TRAITS[name](rate, dry)
        bad += (0 if clean else 1) + (0 if red else 1)
        print("")
    print("%d of %d results off" % (bad, 2 * len(wanted)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
