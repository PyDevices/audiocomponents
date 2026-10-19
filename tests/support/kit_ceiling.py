"""The input ceiling: rendered at the level the class says it is clean at,
on the worst material, the output never wraps, never sits on a rail the
input was not on, and never goes silent while the input plays.

**The stated level.** A class states it as `INPUT_CEILING_DBFS`, a class
attribute in dBFS (0 or below). A class that states none is held to 0 dBFS,
full scale. The material's peak is round(32767 x 10^(dBFS/20)).

**The material**, 2 s at the rate: a 100 Hz square, a 50 Hz sine, one
-sample clicks of alternating sign every 97 frames, LCG noise, a DC step
(silence for the first eighth, then the peak held), and squares on the low
notes 41, 55, 82, 110 and 147 Hz (`sq41` ...), where a filter or a level
that rings on a long half-cycle shows.

**The settings**: the defaults, every patch, each macro alone at 0, 64 and
127, and two kinds of combination. `all=127` is every macro at 127
together. A macro whose label holds Level, Mix, Octave, Direct, Voice or
Gain is level-like; `lv=127+m<i>=<v>` holds every level-like macro at 127
and one other macro at each of its stops (0 and 127), the others where the
defaults put them. A docstring's own worst setting is usually one of these.
At 48 and 22.05 kHz, stereo and mono (`--quick`: 48 kHz stereo).

**The bars**, each its own clause in a RED verdict:

- `wrap`: two neighbouring samples of opposite sign more than 32768 apart,
  where the second, moved by 65536, lands within a quarter of the jump of
  the first, and the signal runs the same way on both sides of the jump
  (into it before, out of it after): an int16 sum that overflowed, and
  the input, `latency_samples` earlier, made no such jump. A square's edge
  is flat on both sides and a click's return lands far from its peak, so
  neither is one. Not judged on the noise, whose jumps run every way. A
  flat signal that wraps (a square at twice full scale) is not caught.
- `rail`: more than 8 frames in a row on a rail (|y| >= 32767) where the
  input, `latency_samples` earlier, was not.
- `silent`: the last second exactly zero while the input played through
  it. Not judged on the DC step, which a high-pass rightly takes to zero.

    python tests/support/kit_ceiling.py DigitalDelay [--quick]
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import kit_common as kc
import lifecycle

CHECK = "ceiling"
SECONDS = 2
#: The low notes a square is played on besides 100 Hz: E1, A1, E2, A2, D3,
#: and 163 Hz, between D3 and E3, where ConvolutionReverb's default room peaks
#: highest and none of the others reached (a full 1/8-octave walk from 40 to
#: 160 Hz would be 17 squares, near three times the cells).
LOW_NOTES = (41, 55, 82, 110, 147, 163)
MATERIALS = ("square", "sine", "clicks", "noise", "dc") + tuple(
    "sq%d" % hz for hz in LOW_NOTES)
#: A macro label holding one of these is level-like.
LEVEL_WORDS = ("Level", "Mix", "Octave", "Direct", "Voice", "Gain",
               "Volume")
WRAP_JUMP = 32768

_MAT = {}


def peak(cls):
    db = getattr(cls, "INPUT_CEILING_DBFS", 0)
    if db >= 0:
        return kc.RAIL
    return int(32767 * 10.0 ** (db / 20.0) + 0.5)


def material(which, rate, channels, amp):
    key = (which, rate, channels, amp)
    if key not in _MAT:
        frames = SECONDS * rate
        if which == "square":
            values = kc.square(frames, channels, amp, rate // 100)
        elif which == "sine":
            values = kc.sine(frames, channels, amp, rate // 50)
        elif which == "clicks":
            values = kc.clicks(frames, channels, amp)
        elif which == "noise":
            values = kc.noise(frames, channels, amp)
        elif which == "dc":
            values = kc.dc(frames, channels, amp, start=frames // 8)
        elif which.startswith("sq"):
            values = kc.square(frames, channels, amp, rate // int(which[2:]))
        else:
            raise ValueError(which)
        _MAT.clear()
        _MAT[key] = values
    return _MAT[key]


def wrap_at(out, values, channels, lat):
    """(frame, channel) of the first wrap, or None."""
    n = len(out) // channels
    nin = len(values) // channels
    for ch in range(channels):
        for f in range(2, n - 1):
            a = out[(f - 1) * channels + ch]
            b = out[f * channels + ch]
            if (a >= 0) == (b >= 0):
                continue
            jump = b - a
            if jump < WRAP_JUMP and -jump < WRAP_JUMP:
                continue
            # Unwrapped, b lands next to a: within a quarter of the jump.
            near = b + 65536 if jump < 0 else b - 65536
            if 4 * abs(near - a) > abs(jump):
                continue
            before = a - out[(f - 2) * channels + ch]
            after = out[(f + 1) * channels + ch] - b
            if jump < 0 and not (before > 0 and after > 0):
                continue
            if jump > 0 and not (before < 0 and after < 0):
                continue
            g = f - lat
            if 1 <= g < nin:
                x = values[g * channels + ch] - values[(g - 1) * channels + ch]
                if x >= WRAP_JUMP or -x >= WRAP_JUMP:
                    continue
            return f, ch
    return None


def judge(data, values, channels, rate, lat, which):
    out = kc.samples(data)
    reds = []
    if which != "noise":
        hit = wrap_at(out, values, channels, lat)
        if hit is not None:
            reds.append("wrap at %d ch %d" % hit)
    run, where = kc.rail_run(out, values, channels, lat)
    if run > kc.RAIL_RUN:
        reds.append("rail %d frames from %d" % (run, where))
    if which != "dc":
        lo = (SECONDS - 1) * rate * channels
        if lifecycle._is_zero(data[2 * lo:]):
            quiet = True
            for i in range(lo, len(values)):
                if values[i]:
                    quiet = False
                    break
            if not quiet:
                last = kc.last_nonzero_frame(out, channels)
                reds.append("silent from %d" % last)
    return reds


def level_like(cls):
    """The indexes of the macros whose label makes them level-like."""
    out = []
    for i in range(len(cls.MACRO_LABELS)):
        label = cls.MACRO_LABELS[i]
        for word in LEVEL_WORDS:
            if word in label:
                out.append(i)
                break
    return out


def configs(cls):
    """(key, patch, knobs) for the defaults, every patch, each macro at 0,
    64 and 127, every macro at 127, and the level-like macros at 127 with
    each other macro at each stop."""
    out = [("d", None, None)]
    for patch in sorted(cls.PATCHES):
        out.append(("p%d" % patch, patch, None))
    n = len(cls.MACRO_LABELS)
    for i in range(n):
        for v in (0, 64, 127):
            out.append(("m%d=%d" % (i, v), None, [(i, v)]))
    if n > 1:
        out.append(("all=127", None, [(i, 127) for i in range(n)]))
    levels = level_like(cls)
    if levels:
        for i in range(n):
            if i in levels:
                continue
            for v in (0, 127):
                knobs = [(j, 127) for j in levels] + [(i, v)]
                out.append(("lv=127+m%d=%d" % (i, v), None, knobs))
    return out


def measure(cls, rate, channels, which, patch, knobs, options=None):
    amp = peak(cls)
    values = material(which, rate, channels, amp)
    feed = kc.feed(values, rate, channels)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        for index, value in knobs or ():
            e.set_macro(index, value)
        data = kc.render(e, SECONDS * rate)
        reds = judge(data, values, channels, rate, e.latency_samples, which)
    finally:
        e.deinit()
    verdict = "RED(%s)" % "; ".join(reds) if reds else "ok"
    return verdict, kc.crc(data)


def run(cls, emit=print, quick=False, rates=None, channels=None,
        materials=MATERIALS, only=None, options=None, name=None):
    """Every ceiling cell for `cls`; returns the red count. `only` limits
    the configurations to keys in it ("d", "p0", "m1=127")."""
    cells = kc.Cells(name or cls.NAME, CHECK, emit)
    if rates is None:
        rates = (48000,) if quick else kc.RATES
    if channels is None:
        channels = (2,) if quick else kc.CHANNELS
    for rate in rates:
        for ch in channels:
            for which in materials:
                for key, patch, knobs in configs(cls):
                    if only is not None and key not in only:
                        continue
                    ckey = "%s/%d/%d/%s" % (which, rate, ch, key)
                    try:
                        verdict, digest = measure(cls, rate, ch, which,
                                                  patch, knobs, options)
                    except Exception as exc:              # noqa: BLE001
                        verdict, digest = "RED(raised %s: %s)" % (
                            type(exc).__name__, exc), None
                    cells.cell(ckey, verdict, digest)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
