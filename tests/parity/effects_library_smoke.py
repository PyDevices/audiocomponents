"""Every audioeffects class builds through the factory and renders, on
whichever interpreter runs this.

    <interpreter> tests/parity/effects_library_smoke.py

tests/test_cpython_effects_library.py holds the same catalogue to the whole
contract, but only under CPython -- it wants an FFT and unittest. This is the
coarse half of that check, in the subset of Python MicroPython and
CircuitPython both have, so the same catalogue can be walked on all three. It
is what catches a class that reaches for something only CPython has.

It walks `audioeffects.ALL` -- the package's own catalogue of provider names
-- through `audioeffects.create()`, which is the contract's construction
boundary. The source carries the format, `create` is handed the source's own
sample rate, and every patch is selected the way a host selects one, with
`program_change()`. Nothing here calls the module-level `configure()` or
passes a `patch=` constructor keyword, so this file keeps working through the
Phase 1 construction change that replaced
`_core`'s module state and its `__new__` format sniffing.

Exit status is non-zero if any class fails to build, disagrees with its
source's format, refuses a patch it declares, or renders silence, and every
failure is printed rather than only the first.
"""

import sys
from array import array

import audiocore
import audioeffects
import audiofilters

SAMPLE_RATE = 48000
CHANNEL_COUNT = 2

#: Arguments a class needs beyond a source. ConvolutionReverb's default
#: second of stereo impulse is 1.5 MB and this walks it once per patch -- a
#: quarter second proves the same thing on a board with a small heap.
#: `GraphicEQ`'s entry is gone with its rebuild: the old class had no
#: default curve, the rebuilt one is flat by default and flat is a
#: wire, and handing it a curve here made patch 0 stop matching the
#: constructor's own defaults.
EXTRA_ARGUMENTS = {
    "ConvolutionReverb": {"seconds": 0.25},
}


#: Frames the probe carries, and frames one patch is allowed to pull off it.
#: One instance is walked through all of its patches on one probe, so the
#: probe loops: since audiodsp#213 a node lets go of a source that has ended,
#: and a one-shot probe ran out under Reverb's tenth patch and TapeDelay's
#: ninth, which then read as silent (the old nodes replayed a finished
#: RawSample for ever, which is what had kept them fed). It loops through
#: `audiofilters.Filter`, the house re-blocker, so a class sees 256-frame
#: blocks rather than the whole array in one `get_buffer`: a whole array
#: longer than `audioroute.Splitter`'s 8192-frame ring
#: (`audiodsp/src/shared/audiodsp_splitter.h:20`) would render silence
#: through every unguarded Splitter class in the catalogue, the trap
#: `MultibandCompressor` M5 records. Capping the pull per patch keeps every
#: class on the same budget.
PROBE_FRAMES = 8000
FRAMES_PER_PATCH = 1024


def source(frames=PROBE_FRAMES, level=11000):
    values = array("h")
    for frame in range(frames):
        for channel in range(CHANNEL_COUNT):
            shape = ((frame * (61 + channel * 17)) % 401) - 200
            values.append(shape * level // 200)
    raw = audiocore.RawSample(values, sample_rate=SAMPLE_RATE,
                              channel_count=CHANNEL_COUNT)
    block = audiofilters.Filter(filter=None, mix=1.0,
                                buffer_size=256 * CHANNEL_COUNT * 2,
                                sample_rate=SAMPLE_RATE,
                                channel_count=CHANNEL_COUNT,
                                bits_per_sample=16, samples_signed=True)
    block.play(raw, loop=True)
    return block


def peak(sample, blocks=8, frames=FRAMES_PER_PATCH):
    """The loudest sample in the next few blocks - at most `blocks` of them
    and at most `frames` frames, whichever comes first."""
    loudest = 0
    pulled = 0
    for _ in range(blocks):
        if pulled >= frames:
            break
        data = bytes(audiocore.get_buffer(sample)[1])
        pulled += len(data) // (2 * CHANNEL_COUNT)
        for index in range(0, len(data) - 1, 2):
            value = data[index] | (data[index + 1] << 8)
            if value >= 32768:
                value -= 65536
            if value < 0:
                value = -value
            if value > loudest:
                loudest = value
    return loudest


#: What is walked: the catalogue. `served` is `None` for a catalogue name,
#: which means "through `audioeffects.create()`"; a class handed here instead
#: is built through its own `create()`.
subjects = [(name, name, None) for name in audioeffects.ALL]

failures = []
classes = 0
patches = 0
parked_classes = 0
parked_patches = 0
for label_name, name, served in subjects:
    signal = source()
    try:
        # The source owns the format: its rate is what `create` is asked
        # for, and the effect reports its source's channel count.
        if served is None:
            effect = audioeffects.create(name, signal, signal.sample_rate,
                                         **EXTRA_ARGUMENTS.get(name, {}))
        else:
            effect = served.create(signal, signal.sample_rate,
                                   **EXTRA_ARGUMENTS.get(name, {}))
    except Exception as error:  # noqa: BLE001 - the point is to report it
        failures.append("%s: %s: %s" % (label_name, type(error).__name__,
                                        error))
        print("FAIL %s" % label_name)
        continue
    if served is None:
        classes += 1
    else:
        parked_classes += 1
    if (effect.sample_rate != signal.sample_rate
            or effect.channel_count != signal.channel_count):
        failures.append("%s: built at %d Hz / %d channels, source is %d / %d"
                        % (label_name, effect.sample_rate,
                           effect.channel_count,
                           signal.sample_rate, signal.channel_count))
        print("FAIL %s (format)" % label_name)
        continue
    for index in sorted(type(effect).PATCHES):
        label = "%s patch %d" % (label_name, index)
        if served is None:
            patches += 1
        else:
            parked_patches += 1
        try:
            effect.program_change(index)
            selected = effect.patch_index
            level = peak(effect.output)
        except Exception as error:  # noqa: BLE001 - the point is to report it
            failures.append("%s: %s: %s" % (label, type(error).__name__,
                                            error))
            print("FAIL %s" % label)
            continue
        if selected != index:
            failures.append("%s: program_change left patch_index %s"
                            % (label, selected))
            print("FAIL %s (not selected)" % label)
        elif level < 32:
            failures.append("%s: renders silence" % label)
            print("FAIL %s (silent)" % label)
        else:
            print("ok   %-24s patch %-3d peak %d"
                  % (label_name, index, level))

print("\n%d classes, %d patches, %d failures"
      % (classes, patches, len(failures)))
# Every class lives in a module of its own name directly under the package;
# one served from anywhere else is a failure.
_served = sorted(
    name for name in audioeffects.ALL
    if getattr(audioeffects, name, None) is not None
    and getattr(audioeffects, name).__module__ == "audioeffects." + name.lower()
)
for name in audioeffects.ALL:
    if name not in _served:
        failures.append("%s: not served from audioeffects.%s"
                        % (name, name.lower()))
print("%d served from their own module" % len(_served))
for line in failures:
    print("  %s" % line)
sys.exit(1 if failures else 0)
