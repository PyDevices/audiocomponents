"""The input ceiling: rendered at the level the class says it is clean at,
on the worst material, the output never wraps, never sits on a rail the
input was not on, and never goes silent while the input plays.

**The stated level.** A class states it as `INPUT_CEILING_DBFS`, a class
attribute in dBFS (0 or below). A class that states none is held to 0 dBFS,
full scale. The material's peak is round(32767 x 10^(dBFS/20)).

**The material**, 2 s at the rate: a 100 Hz square, a 50 Hz sine, one
-sample clicks of alternating sign every 97 frames, LCG noise, and a DC
step (silence for the first eighth, then the peak held). Each at the
defaults, at every patch, and with each macro alone at each stop (0 and
127, and 64 for a bipolar macro); at 48 and 22.05 kHz, stereo and mono
(`--quick`: 48 kHz stereo).

**The bars**, each its own clause in a RED verdict:

- `wrap`: two neighbouring samples of opposite sign more than 32768 apart,
  with the signal running the same way on both sides of the jump (into it
  before, out of it after), as an int16 sum that overflowed runs, and the
  input, `latency_samples` earlier, made no such jump. A square's edge
  is flat on both sides, so it is not one. Not judged on the noise, whose
  jumps run every way.
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
MATERIALS = ("square", "sine", "clicks", "noise", "dc")
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


def configs(cls):
    """(key, patch, knob) for the defaults, every patch and every stop."""
    out = [("d", None, None)]
    for patch in sorted(cls.PATCHES):
        out.append(("p%d" % patch, patch, None))
    for knob in kc.knob_positions(cls):
        out.append(("m%d=%d" % knob, None, knob))
    return out


def measure(cls, rate, channels, which, patch, knob, options=None):
    amp = peak(cls)
    values = material(which, rate, channels, amp)
    feed = kc.feed(values, rate, channels)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        if knob is not None:
            e.set_macro(knob[0], knob[1])
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
                for key, patch, knob in configs(cls):
                    if only is not None and key not in only:
                        continue
                    ckey = "%s/%d/%d/%s" % (which, rate, ch, key)
                    try:
                        verdict, digest = measure(cls, rate, ch, which,
                                                  patch, knob, options)
                    except Exception as exc:              # noqa: BLE001
                        verdict, digest = "RED(raised %s: %s)" % (
                            type(exc).__name__, exc), None
                    cells.cell(ckey, verdict, digest)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
