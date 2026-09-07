"""Cross-interpreter digests for `MultibandCompressor`, without the one line
of `render_effect.py` that this class cannot survive on the ported build.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_digest.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
        -X heapsize=512M tools/phase2_probes/multiband_digest.py
    MICROPYPATH=lib:../cmods/micropython/lib \
        ../cmods/bin/circuitpython-effects -X heapsize=512M \
        tools/phase2_probes/multiband_digest.py

**Why this file exists, measured rather than assumed.**
`render_effect.py:716` calls `audiocore.reset_buffer(effect.output)` before it
renders. This class's `output` is an `audiomixer.Mixer`, and **upstream
CircuitPython's `Mixer.reset_buffer` stops every voice rather than rewinding
it** -- a stopped voice never plays again (audioif's `docs/upstream-diff.md`,
"Resetting a Mixer silenced it, permanently", which is the deviation audioif
made in its own copy). So on `cmods/bin/circuitpython-effects` that one call
turns every render of this class into zeros, while the same call on audioif's
own `audiomixer` -- CPython and desktop MicroPython here, and every board
running audioif firmware -- rewinds and renders. Measured: `voice[0].playing`
is `False` after the reset on that build and `True` on the other two.

The class's own `reset()` is not affected: it re-plays the voices after
clearing the Mixer, exactly so that a board with the ported node behaves like
one with audioif's. What it cannot do is intercept a reset somebody else
performs on the node it handed out.

Everything else here is `render_effect.py`'s own code, imported rather than
copied: the same probe resolution, the same source route, the same block
adapter, the same FNV-1a.
"""

import sys

sys.path.insert(0, "tools")

import audiocore                                             # noqa: E402
import audioeffects                                          # noqa: E402
import render_effect as renderer                             # noqa: E402

CLASS = "MultibandCompressor"
BLOCK = 256
CASES = (("chord", 48000), ("noise_det", 48000), ("sweep_log", 48000),
         ("chord", 44100))


def digest_of(probe, rate, channels=2, block=BLOCK):
    path, expected, _entry = renderer.resolve_probe(probe, rate, channels)
    if expected is not None:
        actual = renderer.wav_pcm_digest(path)
        if actual != int(expected, 16):
            raise SystemExit("probe %s is stale (%08x against %s)"
                             % (path, actual, expected))
    source, holder, route, frames = renderer.probe_source(path, rate,
                                                          channels)
    adapter = renderer.block_adapter(source, rate, channels, block)
    effect = audioeffects.create(CLASS, adapter, rate)
    value = 2166136261
    written = 0
    non_zero = 0
    frame_bytes = channels * 2
    while written < frames:
        _result, buffer = audiocore.get_buffer(effect.output)
        data = bytes(buffer)
        if not data:
            break
        available = len(data) // frame_bytes
        if written + available > frames:
            data = data[:(frames - written) * frame_bytes]
            available = len(data) // frame_bytes
        value = renderer.checksum(data, value)
        for byte in data:
            if byte:
                non_zero += 1
        written += available
    effect.deinit()
    if holder is not None:
        holder.close()
    return value, written, non_zero, route


def main():
    print("%s digests - %s" % (CLASS, renderer.interpreter()))
    print("=" * 72)
    silent = 0
    for probe, rate in CASES:
        value, frames, non_zero, route = digest_of(probe, rate)
        if not non_zero:
            silent += 1
        print("  %-12s %5d Hz  block %5d  %8d frames  fnv %08x  %s  (%s)"
              % (probe, rate, BLOCK, frames, value,
                 "audio" if non_zero else "SILENT", route))
    print("%d silent renders" % silent)
    return 1 if silent else 0


if __name__ == "__main__":
    sys.exit(main())
