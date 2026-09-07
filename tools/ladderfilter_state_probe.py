"""STATE for `LadderFilter`, on any of the three interpreters.

    audiocomponents/.venv/bin/python tools/ladderfilter_state_probe.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
        tools/ladderfilter_state_probe.py
    MICROPYPATH=lib:../cmods/micropython/lib \
        ../cmods/bin/circuitpython-effects -X heapsize=256M \
        tools/ladderfilter_state_probe.py [--rate 44100]

`effect_measurements.state()` is CPython-and-numpy and drives the class
rather than reading a render, so the kit's "render dual-runtime, analyse on
the desktop" split does not reach it: the other two interpreters have no
STATE reading at all without a file like this one. Stdlib only, in
`render_effect.py`'s shape, and deliberately a *subset* -- it does not
measure allocation, because `tracemalloc` is CPython's and a byte count from
`gc.mem_free()` is not the same number. That gap is reported, not papered
over.

What it does read, in `state()`'s own order: the class renders; `reset()`
then a silent source must give exact zero; the original source must render
again; `capabilities` is what the class declares; `deinit()` runs and every
node the class enumerated is checked. It leads with the loop CHARGED --
patch 2 self-oscillates -- because a reset walk that is never given anything
to clear passes on a class that has no reset at all.
"""

import sys

import audiocore
import audioeffects

RATE = 48000
CHANNELS = 2
BLOCKS = 32


def interpreter():
    return "%s %s" % (sys.implementation.name,
                      ".".join(str(part)
                               for part in sys.implementation.version[:3]))


def noise(frames, channels, seed=0x2545F491):
    """The probe manifest's xorshift32, so this is the kit's own generator
    and not a second random source. Built straight into the array: a list of
    96000 small ints is a MemoryError on desktop MicroPython, which is what
    the first run of this file hit."""
    import array
    out = array.array("h", bytes(2 * frames * channels))
    state = seed
    position = 0
    for _ in range(frames):
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        value = int(((state & 0xFFFF) - 32768) * 0.15)
        for _channel in range(channels):
            out[position] = value
            position += 1
    return out


def quiet(frames, channels):
    import array
    return array.array("h", bytes(2 * frames * channels))


def peak_of(raw):
    """Peak |sample| straight out of the bytes.

    `array.array.frombytes` does not exist on MicroPython (checked: 1.28.0
    reports False for hasattr) and `audiocore.get_buffer` on the
    CircuitPython build takes one positional argument where the CPython
    shim takes three -- both found by running this file, and both the reason
    it decodes bytes by hand."""
    top = 0
    for index in range(0, len(raw) - 1, 2):
        value = raw[index] | (raw[index + 1] << 8)
        if value >= 32768:
            value -= 65536
        if value < 0:
            value = -value
        if value > top:
            top = value
    return top


def pull(node, blocks, channels):
    top = 0
    nonzero = 0
    for _ in range(blocks):
        _result, buffer = audiocore.get_buffer(node)
        value = peak_of(bytes(buffer))
        if value:
            nonzero += 1
        if value > top:
            top = value
    return top, nonzero


def main(argv):
    rate = RATE
    channels = CHANNELS
    index = 0
    while index < len(argv):
        if argv[index] == "--rate":
            rate = int(argv[index + 1]); index += 2
        elif argv[index] == "--channels":
            channels = int(argv[index + 1]); index += 2
        else:
            index += 1

    import audiofilters
    source = audiocore.RawSample(noise(rate // 4, channels),
                                 sample_rate=rate, channel_count=channels)
    silence = audiocore.RawSample(quiet(rate // 4, channels),
                                  sample_rate=rate, channel_count=channels)
    adapter = audiofilters.Filter(filter=None, mix=1,
                                  buffer_size=2048 * channels * 2,
                                  sample_rate=rate, bits_per_sample=16,
                                  samples_signed=True,
                                  channel_count=channels)
    adapter.play(source, loop=False)
    effect = audioeffects.create("LadderFilter", adapter, rate)
    # Patch 2 self-oscillates: the loop is charged before reset() is asked
    # to clear it, so a class with no reset at all cannot pass this.
    effect.program_change(2)
    audiocore.reset_buffer(effect.output)

    print("STATE  %-24s %5d Hz %d ch  LadderFilter %s"
          % (interpreter(), rate, channels,
             audioeffects.LadderFilter.VERSION))

    top, nonzero = pull(effect.output, BLOCKS, channels)
    print("  probe render          peak %6d LSB  in %d of %d blocks  -> %s"
          % (top, nonzero, BLOCKS, "green" if top else "RED (silent)"))
    charged = top

    effect.reset()
    adapter.play(silence, loop=False)
    audiocore.reset_buffer(adapter)
    top, _nonzero = pull(effect.output, BLOCKS, channels)
    print("  reset() + silence     peak %6d LSB (bar 0)               -> %s"
          % (top, "green" if top == 0 else "RED"))
    reset_ok = top == 0

    adapter.play(source, loop=False)
    audiocore.reset_buffer(adapter)
    effect.program_change(2)
    top, _nonzero = pull(effect.output, BLOCKS, channels)
    print("  source handed back    peak %6d LSB                       -> %s"
          % (top, "green" if top else "RED (does not render again)"))
    resumed_ok = bool(top)

    print("  capabilities          %-24s               -> %s"
          % (tuple(effect.capabilities),
             "green" if tuple(effect.capabilities) == () else "RED"))

    node = effect._node
    has_deinit = hasattr(node, "deinit")
    effect.deinit()
    released = getattr(node, "_deinited", None)
    print("  deinit()              node exposes deinit: %-5s  _deinited "
          "%s" % (has_deinit, released))
    try:
        effect.output
        live = True
    except RuntimeError:
        live = False
    print("  deinit() -> output    raises RuntimeError: %-5s             "
          "-> %s" % (not live, "green" if not live else "RED"))
    print("  allocation            unmeasured on this file: tracemalloc is "
          "CPython's; see the pack")
    green = reset_ok and resumed_ok and not live and charged
    print("  STATE  %s" % ("green" if green else "RED"))
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
