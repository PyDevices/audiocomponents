"""The level pass: real material at three levels, so a trait measured on
sines at one level is read again where the input level moves it.

The material is `kit_common.phrase` after 1024 frames of silence: six
plucked strings one at a time, noisy at the attack and decaying through
every level under their peak, at -24, -12 and -3 dBFS
(`kit_common.LEVELS_DBFS`). A level over the class's
`INPUT_CEILING_DBFS` prints `na(above ceiling)`: the ceiling check owns what
the class says it cannot take.

Each cell renders the phrase and then silence, and judges the clauses that
apply:

- `wrap` and `rail`: as the ceiling check reads them, on this material.
- `live`: the output is not zero throughout while the phrase plays. A class
  that does nothing at all, or a gate that shuts on a phrase at -3 dBFS, is
  red. Not judged with the wire at 0, where the output is the input.
- `ring`: the output's last non-zero frame is inside `tail_samples` + latency
  + one block of the phrase's end (lifecycle P2's bound), where the tail is
  at most `MAX_TAIL_S` seconds; a longer tail prints `na(tail ...)` for the
  clause, and a class that reports no tail is not judged.
- `wire`: with the class's wet/dry control at 0 (`lifecycle.mix_index`; a
  depth too, outside the settings `lifecycle.DEPTH_NOT_A_WIRE` names) the
  output is the input, byte for byte, `latency_samples` later. A leak that
  only a quiet or only a loud note wakes shows at the level that plays it.

The cells: `<level>/<rate>/<channels>/<config>`, the config the defaults
(`d`), a patch (`p<k>`), or either with the wire at 0 (`wire@d`,
`wire@p<k>`, for a class that has a wire). 48 and 22.05 kHz, stereo and
mono, the defaults and every patch (`--quick`: 48 kHz stereo, the defaults
and the last patch).

    python tests/support/kit_levels.py DigitalDelay [--quick]
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import kit_ceiling
import kit_common as kc
import lifecycle

CHECK = "levels"
#: The longest tail the ring clause renders to, in seconds.
MAX_TAIL_S = 6
#: Frames past the bound that must hold nothing.
MARGIN = lifecycle.MARGIN

#: Frames of silence before the phrase, so a move made before the first pull
#: (the wire at 0) has finished walking when the first note starts.
LEAD = 1024

_MAT = {}


def material(rate, channels, level):
    key = (rate, channels, level)
    if key not in _MAT:
        _MAT.clear()
        phrase = kc.phrase(rate, channels, level)
        values = kc._blank(LEAD + len(phrase) // channels, channels)
        for i in range(len(phrase)):
            values[LEAD * channels + i] = phrase[i]
        _MAT[key] = values
    return _MAT[key]


def red_patches(cls, level, **kw):
    """The patches `cls` rails on at `level`: the numbers `k` of the red or
    declared `<level>/<rate>/<channels>/p<k>` cells, sorted, for a test that
    holds a class's stated clean level and the patches that go over it."""
    lines = []
    run(cls, emit=lines.append, levels=(level,), **kw)
    found = set()
    for line in lines:
        parts = line.split("|")
        if len(parts) > 3 and parts[3][:5] in ("V:RED", "V:dec"):
            config = parts[2].split("/")[-1]
            found.add(int(config[1:]) if config[0] == "p"
                      and config[1:].isdigit() else config)
    return sorted(found, key=str)


def above_ceiling(cls, level):
    return level > getattr(cls, "INPUT_CEILING_DBFS", 0)


def wire_index(cls, patch, options):
    """(macro index, why not) for the class's wet/dry control: index None
    for a class with none, `why` set where Mix 0 is not a byte compare by
    design."""
    mix = lifecycle.mix_index(cls)
    if mix is None:
        return None, None
    # The matrix's own ruling: a class that declares its P1 at Mix 0 for
    # this patch says the wire is not one there.
    if lifecycle._decl(cls, lifecycle.Event("E5-mix0", []), "P1", patch):
        return mix, "declared in the lifecycle matrix (P1 at Mix 0)"
    if lifecycle.is_depth(cls):
        move = lifecycle.Event("levels", [("macro", mix, 0)])
        return mix, lifecycle._not_a_wire(cls, move, patch, options)
    return mix, None


def measure(cls, rate, channels, level, patch, wire, options=None):
    """(verdict, digest) for one cell."""
    values = material(rate, channels, level)
    in_frames = len(values) // channels
    feed = kc.feed(values, rate, channels)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        mix = None
        if wire:
            mix, why = wire_index(cls, patch, options)
            if why is not None:
                return "na(not a wire: %s)" % why[:50], None
            e.set_macro(mix, 0)
        lat = e.latency_samples
        tail = e.tail_samples
        ring = tail is not None and tail <= MAX_TAIL_S * rate
        frames = in_frames + MARGIN + kc.BLOCK + lat
        if ring:
            frames += tail
        data = kc.render(e, frames)
    finally:
        e.deinit()
    fsize = 2 * channels
    out = kc.samples(data)
    reds = []
    if not wire:
        hit = kit_ceiling.wrap_at(out, values, channels, lat)
        if hit is not None:
            reds.append("wrap at %d ch %d" % hit)
        run, where = kc.rail_run(out, values, channels, lat)
        if run > kc.RAIL_RUN:
            reds.append("rail %d frames from %d" % (run, where))
        if lifecycle._is_zero(data[:in_frames * fsize]):
            reds.append("silent while the phrase plays")
        if ring:
            bound = in_frames + tail + lat + kc.BLOCK
            last = kc.last_nonzero_frame(out, channels)
            if last > bound:
                reds.append("rings to +%d, bound +%d" % (
                    last - in_frames, bound - in_frames))
    else:
        want = bytes(lat * fsize) + bytes(values)
        want = want[:in_frames * fsize]
        got = data[:len(want)]
        if got != want:
            d = lifecycle._first_diff(got, want, 0, len(want))
            reds.append("wire: first wrong frame %d" % (d // fsize))
    if reds:
        return "RED(%s)" % "; ".join(reds), kc.crc(data)
    return "ok", kc.crc(data)


def configs(cls, quick):
    """(key, patch, wire) for the defaults and the patches, each with the
    wire at 0 where the class has one."""
    patches = [None] + sorted(cls.PATCHES)
    if quick and len(patches) > 2:
        patches = [None, patches[-1]]
    has = lifecycle.mix_index(cls) is not None
    out = []
    for patch in patches:
        out.append((kc.pname(patch), patch, False))
        if has:
            out.append(("wire@" + kc.pname(patch), patch, True))
    return out


def run(cls, emit=print, quick=False, rates=None, channels=None,
        levels=kc.LEVELS_DBFS, options=None, name=None):
    """Every level cell for `cls`; returns the red count."""
    cells = kc.Cells(name or cls.NAME, CHECK, emit)
    if rates is None:
        rates = (48000,) if quick else kc.RATES
    if channels is None:
        channels = (2,) if quick else kc.CHANNELS
    for rate in rates:
        for ch in channels:
            for level in levels:
                for key, patch, wire in configs(cls, quick):
                    ckey = "%d/%d/%d/%s" % (level, rate, ch, key)
                    if above_ceiling(cls, level):
                        cells.cell(ckey, "na(above ceiling)")
                        continue
                    try:
                        verdict, digest = measure(cls, rate, ch, level,
                                                  patch, wire, options)
                    except Exception as exc:              # noqa: BLE001
                        verdict, digest = "RED(raised %s: %s)" % (
                            type(exc).__name__, exc), None
                    cells.cell(ckey, verdict, digest)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
