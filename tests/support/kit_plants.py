"""Plant validity: each planted fault a class's tests use differs from the
clean class at the defaults, and no knob position and no patch of the
clean class renders what the plant renders.

A plant that renders what the clean class renders proves nothing, and a
plant some knob reaches is a setting, not a fault: a test that goes red on
it would go red on a user turning that knob.

**Declaring plants.** A class's test module (the one its `CLAIMS` table is
read from, usually `tests/test_cpython_effects_<name>.py`) declares
`KIT_PLANTS = {"T1": PlantedSubclass, ...}`: a label (the trait or test
the plant serves) to a subclass of the class. A value may instead be
`(PlantedSubclass, patch)`: the plant is then judged against the clean
class at that patch instead of the defaults (a class with two characters
plants faults in the one the defaults do not use), and the walk below
still covers every patch and stop. `(PlantedSubclass, patch, settings)`
adds `rate`, `channels` and constructor `options` for a plant that only
shows at one setting (`patch` may be None). A module that does not import on an interpreter (one that needs
numpy, natively) prints `na(...)`; keep plants in a numpy-free module and
name it with `--plants-module` to check them natively.

**What is compared.** The digest of the render (an 8192-frame click and
noise train, then silence to the clean class's tail at the defaults,
between 16384 frames and 4 s) together with `tail_samples` and
`latency_samples`. The plant is rendered at its patch (or its defaults),
the clean class at its defaults, with each macro alone at each stop (0
and 127, and 64 for a bipolar macro), and at every patch, all at the
plant's settings.

    python tests/support/kit_plants.py SlapbackDelay
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import kit_common as kc
import lifecycle

CHECK = "plants"
PROBE_FRAMES = 8192
MIN_FRAMES = 16384
MAX_SECONDS = 4

_PROBE = {}


def probe(channels):
    if channels not in _PROBE:
        _PROBE[channels] = lifecycle.click_noise(PROBE_FRAMES, channels)
    return _PROBE[channels]


def load_plants(cls, module=None):
    """(KIT_PLANTS dict or None, why not). With no `module`, the class's
    test module is the one its CLAIMS table is read from."""
    name = module or "test module for %s" % cls.NAME
    try:
        if module:
            mod = __import__(module)
        else:
            # kit_claims reads source with ast, which only CPython has.
            import kit_claims
            mod, _ = kit_claims.module_for(cls)
    except Exception as exc:                              # noqa: BLE001
        return None, "%s does not import: %s" % (name, type(exc).__name__)
    if mod is None:
        return None, "%s has no test module" % cls.NAME
    name = mod.__name__
    plants = getattr(mod, "KIT_PLANTS", None)
    if plants is None:
        return None, "%s has no KIT_PLANTS" % name
    return plants, None


def _setting(value, options=None):
    """(plant, patch, rate, channels, options) for one KIT_PLANTS value."""
    patch = None
    settings = {}
    if isinstance(value, tuple):
        cls = value[0]
        if len(value) > 1:
            patch = value[1]
        if len(value) > 2:
            settings = value[2]
    else:
        cls = value
    merged = dict(options or {})
    merged.update(settings.get("options", {}))
    return (cls, patch, settings.get("rate", 48000),
            settings.get("channels", 2), merged)


def digest(cls, rate, channels, frames, options=None, patch=None,
           knob=None):
    values = probe(channels)
    feed = kc.feed(values, rate, channels)
    e = kc.build(cls, feed.port, rate, patch, options)
    try:
        if knob is not None:
            e.set_macro(knob[0], knob[1])
        data = kc.render(e, frames)
        state = "|%r|%r" % (e.tail_samples, e.latency_samples)
        return kc.crc(state.encode(), kc.crc_value(data))
    finally:
        e.deinit()


def frames_for(cls, rate, channels, options):
    feed = kc.feed(probe(channels), rate, channels)
    e = kc.build(cls, feed.port, rate, None, options)
    try:
        tail = e.tail_samples
        lat = e.latency_samples
    finally:
        e.deinit()
    if tail is None:
        extra = MAX_SECONDS * rate
    else:
        extra = min(tail + lat + kc.BLOCK, MAX_SECONDS * rate)
    return max(MIN_FRAMES, PROBE_FRAMES + extra)


def check_plant(clean, plant, rate, channels, options, patch=None):
    """(verdict, plant digest)."""
    frames = frames_for(clean, rate, channels, options)
    planted = digest(plant, rate, channels, frames, options, patch=patch)
    if digest(clean, rate, channels, frames, options, patch=patch) == \
            planted:
        return "RED(same as clean at %s)" % (
            "the defaults" if patch is None else "patch %d" % patch), planted
    if patch is not None and digest(clean, rate, channels, frames,
                                    options) == planted:
        return "RED(reproduced by the defaults)", planted
    for knob in kc.knob_positions(clean):
        if digest(clean, rate, channels, frames, options,
                  knob=knob) == planted:
            return "RED(reproduced by m%d=%d)" % knob, planted
    for patch in sorted(clean.PATCHES):
        if digest(clean, rate, channels, frames, options,
                  patch=patch) == planted:
            return "RED(reproduced by patch %d)" % patch, planted
    return "ok", planted


def run(cls, emit=print, module=None, plants=None, name=None, quick=False,
        options=None):
    """Every plant's cell for `cls`; returns the red count."""
    cells = kc.Cells(name or cls.NAME, CHECK, emit)
    if plants is None:
        plants, why = load_plants(cls, module)
        if plants is None:
            cells.cell("-", "na(%s)" % why)
            return cells.summary()
    for label in sorted(plants):
        plant, patch, rate, channels, opts = _setting(plants[label], options)
        key = "%s/%d/%d/%s" % (label, rate, channels, kc.pname(patch))
        try:
            verdict, dig = check_plant(cls, plant, rate, channels, opts,
                                       patch)
        except Exception as exc:                          # noqa: BLE001
            verdict, dig = "RED(raised %s: %s)" % (type(exc).__name__,
                                                  exc), None
        cells.cell(key, verdict, dig)
    return cells.summary()


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
