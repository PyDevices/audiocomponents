"""The input ceiling: rendered at the level the class says it is clean at,
on the worst material, the output never wraps, never sits on a rail the
input was not on, and never goes silent while the input plays.

**The stated level.** A class states it as `INPUT_CEILING_DBFS`, a class
attribute in dBFS (0 or below). A class that states none is held to 0 dBFS,
full scale. The material's peak is round(32767 x 10^(dBFS/20)).
A class whose ceiling depends on where the knobs are states two more:
`SURFACE_CEILING_DBFS`, the level it is clean at anywhere on the surface,
and `DEFAULT_CEILING_DBFS`, the level at the constructor's defaults. A cell
that moves a macro is played at the surface's level; a patch alone at the
input ceiling, or the surface's when only that is stated; the defaults at
their own, else the input ceiling, else the surface's.

**The material**, 2 s at the rate (longer for a class with a long tail, see
**The window**): a 100 Hz square, a 50 Hz sine, one
-sample clicks of alternating sign every 97 frames, LCG noise, a DC step
(silence for the first eighth, then the peak held), and squares on the low
notes 41, 55, 82, 110, 147, 163 and 220 Hz (`sq41` ...), where a filter or a level
that rings on a long half-cycle shows.

**The settings**: the defaults, every patch, each macro alone at 0, 64 and
127, and two kinds of combination. `all=127` is every macro at 127
together. A macro whose label holds Level, Mix, Octave, Direct, Voice or
Gain is level-like; `lv=127+m<i>=<v>` holds every level-like macro at 127
and one other macro at each of its stops (0 and 127), the others where the
defaults put them, at the defaults and then on every patch
(`p<n>+lv=127+m<i>=<v>`, on the sine and the squares only). A docstring's own worst
setting is usually one of these.
At 48 and 22.05 kHz, stereo and mono (`--quick`: 48 kHz stereo).

**The window.** 2 s is enough for most classes and too short for a long
hall, whose worst case only builds up as the tail does (ShimmerHall peaks
near 11 s). A cell's window is the tail the instance reports once its
settings are in (`tail_samples`), rounded up to whole seconds, never under
2 s and never over `MAX_SECONDS` (12 s); a class that reports no tail gets
2 s. A `sq` or `dc` cell's material is as long as its window.

**The bars**, each its own clause in a RED verdict:

- `wrap`: two neighbouring samples of opposite sign more than 32768 apart,
  where the second, moved by 65536, lands within a quarter of the jump of
  the first, and the signal runs the same way on both sides of the jump
  (into it before, out of it after, each step under 32768): an int16 sum
  that overflowed, and the input made no such jump `latency_samples`
  earlier (half that, when it went the same way: a click's return and
  the undershoot of a filter it rang), nor, when the class reports any
  latency, the same way in the
  last `HOLD` frames up to the jump's own. A square's edge is flat on
  both sides, a click's return lands far from its peak, and a clipped
  ring at Nyquist leaps into the jump and out of it, so none is one. A
  sample-and-hold moves a square's edge by up to its hold, and a filter
  ahead of it by its rise time on top (Bitcrusher's patch 3 lands an edge
  5 to 14 frames late against a reported 8), so the edge lands in that
  span. An overshoot that overflows jumps the other way from the input's
  edge, so it is still read. Not judged on the noise, whose jumps run
  every way. A flat signal that wraps (a square at twice full scale) is
  not caught, nor a ring at Nyquist that wraps rather than clips.
- `rail`: more than 8 frames in a row on a rail (|y| >= 32767) where the
  input was on neither `latency_samples` earlier nor in the last
  min(`latency_samples`, `HOLD`) frames: a hold that latched a rail
  plays it for the length of the hold. Not judged where the class says
  the setting clips by design: `CLIPS_AT_TOP`, a tuple of macro indexes,
  excuses a cell whose knobs put one of them at 127 (Feedback at its top
  runs away), and `CLIPS_BY_DESIGN = True` excuses every cell (a fuzz
  clips at any level). A wrap is still judged there.
- `silent`: the last second exactly zero while the input played through
  it. Not judged on the DC step, which a high-pass rightly takes to zero,
  nor where a macro whose label holds Level or Volume is at 0: an output
  level turned all the way down is silence by design. A Gain at 0 is
  still judged, since a gain stage's bottom stop is rarely off.

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
#: The longest window a long tail can ask for, in seconds.
MAX_SECONDS = 12
#: The low notes a square is played on besides 100 Hz: E1, A1, E2, A2, D3,
#: and 163 Hz, between D3 and E3, where ConvolutionReverb's default room peaks
#: highest and none of the others reached (a full 1/8-octave walk from 40 to
#: 160 Hz would be 17 squares, near three times the cells).
LOW_NOTES = (41, 55, 82, 110, 147, 163, 220)
MATERIALS = ("square", "sine", "clicks", "noise", "dc") + tuple(
    "sq%d" % hz for hz in LOW_NOTES)
#: The materials the combinations on every patch (`p<n>+lv=...`) run on:
#: the slow ones, where the worst case sits. Every patch times every other
#: macro's stops times every material would be most of the check.
PATCH_COMBO_MATERIALS = ("sine", "square") + tuple(
    "sq%d" % hz for hz in LOW_NOTES)
#: A macro label holding one of these is level-like.
LEVEL_WORDS = ("Level", "Mix", "Octave", "Direct", "Voice", "Gain",
               "Volume")
#: A macro label holding one of these is an output level, whose 0 is
#: silence.
SILENT_AT_ZERO_WORDS = ("Level", "Volume")
WRAP_JUMP = 32768

#: A full-scale click falls 32767 on its return, one short of WRAP_JUMP,
#: and a filter that rings below zero falls with it on the same frame.
#: An output jump the same way as an input jump this big, on the frame
#: the input made it, follows the input and is not a wrap.
CLICK_JUMP = 16384
#: The furthest a class that reports latency may move an edge, in frames:
#: Bitcrusher's lowest Rate holds 47 frames at 48 kHz. A wrap the same way
#: as an input edge this far back, or a rail the input was on, is that
#: edge or that rail moved.
HOLD = 64

_MAT = {}


def stated_dbfs(cls, patch=None, knobs=None):
    """The level a cell is played at: see **The stated level**."""
    surface = getattr(cls, "SURFACE_CEILING_DBFS", None)
    stated = getattr(cls, "INPUT_CEILING_DBFS", None)
    if knobs:
        order = (surface, stated)
    elif patch is not None:
        order = (stated, surface)
    else:
        order = (getattr(cls, "DEFAULT_CEILING_DBFS", None), stated, surface)
    for db in order:
        if db is not None:
            return db
    return 0


def peak(cls, patch=None, knobs=None):
    db = stated_dbfs(cls, patch, knobs)
    if db >= 0:
        return kc.RAIL
    return int(32767 * 10.0 ** (db / 20.0) + 0.5)


def window(e, rate):
    """Seconds the cell renders: the instance's tail, rounded up, between
    SECONDS and MAX_SECONDS."""
    tail = e.tail_samples
    if not tail:
        return SECONDS
    seconds = (tail + rate - 1) // rate
    return max(SECONDS, min(MAX_SECONDS, seconds))


def material(which, rate, channels, amp, seconds=SECONDS):
    key = (which, rate, channels, amp, seconds)
    if key not in _MAT:
        frames = seconds * rate
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
            if before >= WRAP_JUMP or -before >= WRAP_JUMP or \
                    after >= WRAP_JUMP or -after >= WRAP_JUMP:
                continue
            if _input_jumped(values, channels, ch, nin, 0, [f - lat]) or \
                    _input_jumped(values, channels, ch, nin, jump, [f - lat],
                                  CLICK_JUMP) or \
                    (lat and _input_jumped(values, channels, ch, nin, jump,
                                           range(f - HOLD, f + 1))):
                continue
            return f, ch
    return None


def _input_jumped(values, channels, ch, nin, jump, frames,
                  size=WRAP_JUMP):
    """Whether the input made a jump of `size` or more at one of `frames`:
    the same way as `jump`, or either way when `jump` is 0."""
    for g in frames:
        if 1 <= g < nin:
            x = values[g * channels + ch] - values[(g - 1) * channels + ch]
            if (x >= size and jump >= 0) or (-x >= size and jump <= 0):
                return True
    return False


def turned_down(cls, knobs):
    """Whether `knobs` put an output level (SILENT_AT_ZERO_WORDS) at 0."""
    for index, value in knobs or ():
        if value == 0:
            for word in SILENT_AT_ZERO_WORDS:
                if word in cls.MACRO_LABELS[index]:
                    return True
    return False


def clips_by_design(cls, knobs):
    """Whether the class says this cell's knobs clip by design (see `rail`
    under **The bars**)."""
    if getattr(cls, "CLIPS_BY_DESIGN", False):
        return True
    top = getattr(cls, "CLIPS_AT_TOP", ())
    for index, value in knobs or ():
        if value == 127 and index in top:
            return True
    return False


def judge(data, values, channels, rate, lat, which, seconds=SECONDS,
          silent_ok=False, rail_ok=False):
    out = kc.samples(data)
    reds = []
    if which != "noise":
        hit = wrap_at(out, values, channels, lat)
        if hit is not None:
            reds.append("wrap at %d ch %d" % hit)
    run, where = kc.rail_run(out, values, channels, lat, HOLD)
    if run > kc.RAIL_RUN and not rail_ok:
        reds.append("rail %d frames from %d" % (run, where))
    if which != "dc" and not silent_ok:
        lo = (seconds - 1) * rate * channels
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
        # The level-like macros at 127 together (Mix at full: dry and wet
        # both at unity) with each other macro at its stops, at the
        # defaults and then on every patch.
        for patch in [None] + sorted(cls.PATCHES):
            lead = "" if patch is None else "p%d+" % patch
            for i in range(n):
                if i in levels:
                    continue
                for v in (0, 127):
                    knobs = [(j, 127) for j in levels] + [(i, v)]
                    out.append(("%slv=127+m%d=%d" % (lead, i, v), patch,
                                knobs))
    return out


def measure(cls, rate, channels, which, patch, knobs, options=None):
    amp = peak(cls, patch, knobs)
    # The window is read off the instance, so the material is made after it.
    probe = kc.feed(kc.square(1024, channels, amp, 100), rate, channels)
    e = kc.build(cls, probe.port, rate, patch, options)
    try:
        for index, value in knobs or ():
            e.set_macro(index, value)
        seconds = window(e, rate)
    finally:
        e.deinit()
    values = material(which, rate, channels, amp, seconds)
    feed = kc.feed(values, rate, channels)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        for index, value in knobs or ():
            e.set_macro(index, value)
        data = kc.render(e, seconds * rate)
        reds = judge(data, values, channels, rate, e.latency_samples, which,
                     seconds, turned_down(cls, knobs),
                     clips_by_design(cls, knobs))
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
                    if patch is not None and knobs and \
                            which not in PATCH_COMBO_MATERIALS:
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


def stated_level_reds(cls, material, db=None, keys=None):
    """The red cells on `material`, 48 kHz stereo, for the defaults and
    every patch (or just `keys`), played at the class's stated level, or at
    `db` to show the level above it is not clean. An effect's own test
    holds its stated level with this: clean there, red a step up."""
    if db is not None:
        cls = type(cls.__name__, (cls,), {"INPUT_CEILING_DBFS": db,
                                          "__module__": cls.__module__})
    if keys is None:
        keys = ["d"] + ["p%d" % p for p in sorted(cls.PATCHES)]
    lines = []
    run(cls, emit=lines.append, quick=True, materials=(material,),
        only=keys)
    return [line for line in lines
            if "|V:RED" in line and not line.startswith("SUMMARY")]


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
