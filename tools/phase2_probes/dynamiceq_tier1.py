"""Every Tier 1 invariant for `DynamicEQ`, on whichever interpreter runs it.

The class gate asks for the invariant block green **on CPython and
MicroPython at 48 kHz, 44.1 kHz and 22.05 kHz, and on the patched
CircuitPython build where its nodes exist**. The unittest battery
(`tests/test_cpython_effects_dynamiceq.py`) is CPython-only because it wants
`unittest`; this file is the same measurements in the subset all three
interpreters have, so the pack's per-interpreter table is filled from runs
and not from an assumption that one interpreter stands for the others.

    PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \\
        tools/phase2_probes/dynamiceq_tier1.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \\
        tools/phase2_probes/dynamiceq_tier1.py
    MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \\
        -X heapsize=256M tools/phase2_probes/dynamiceq_tier1.py

Exit status is non-zero if any row fails, and every row prints its number.
"""

import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])

import audiocore                         # noqa: E402

import dynamiceq_support as S            # noqa: E402

RATES = (48000, 44100, 22050)
FAILURES = []


def check(label, ok, detail):
    print("  %-4s %-46s %s" % ("pass" if ok else "FAIL", label, detail))
    if not ok:
        FAILURES.append(label)


def wire(rate, channels):
    """WIRE: Mix 0 is byte-identical to the source."""
    data = S.sine(1000.0, S.amp(-4.4), rate, rate, channels)
    effect, _ = S.build(rate=rate, channels=channels, data=data, mix=0.0)
    out = S.render(effect, rate, channels)
    same = True
    first = -1
    for index in range(len(data)):
        if out[index] != data[index]:
            same = False
            first = index
            break
    check("WIRE mix 0 byte-identical", same,
          "identical" if same else "first differing sample %d" % first)


def level(rate, channels):
    """LEVEL: a tone 10 dB under the threshold passes at unity."""
    data = S.sine(3000.0, S.amp(-41.0), rate, rate, channels)
    effect, _ = S.build(rate=rate, channels=channels, data=data)
    out = S.render(effect, rate, channels)
    skip = rate // 2
    moved = S.gain_db(S.rms(out, skip, channels), S.rms(data, skip, channels))
    check("LEVEL unity below threshold", abs(moved) < 0.05,
          "%+0.4f dB" % moved)


def tail(rate, channels):
    """TAIL: burst then silence, decay to exact zero, no held DC."""
    total = rate * 3
    data = S.burst(400.0, S.amp(-3.0), rate // 5, total, rate // 10,
                   rate, channels)
    effect, _ = S.build(rate=rate, channels=channels, data=data,
                        frequency=400.0, q=2.0, threshold_db=-60.0,
                        ratio=8.0)
    out = S.render(effect, total, channels)
    residual = S.peak(out, total - rate // 4, channels)
    check("TAIL reaches exact zero", residual == 0,
          "residual %d LSB over the last %d frames, declared tail %d"
          % (residual, rate // 4, effect.tail_samples))


def click(rate, channels):
    """CLICK: reported latency_samples against the measured delay."""
    total = rate // 2
    data = S.impulse_at(20000, 50, total, channels)
    effect, _ = S.build(rate=rate, channels=channels, data=data)
    out = S.render(effect, total, channels)
    top = S.peak(out, 0, channels)
    at = -1
    for index in range(len(out) // channels):
        value = out[index * channels]
        if value == top or value == -top:
            at = index
            break
    measured = at - 50
    check("CLICK latency reported == measured",
          top == 20000 and measured == effect.latency_samples,
          "peak %d at frame %d, measured %d, reported %d"
          % (top, at, measured, effect.latency_samples))


def state(rate, channels):
    """STATE: reset() clears the split while it is still ringing, deinit()
    releases the class's nodes, and the borrowed source keeps rendering."""
    total = rate * 2
    on = rate // 10
    lead = rate // 10
    data = S.burst(300.0, S.amp(-3.0), on, total, lead, rate, channels)
    effect, source = S.build(rate=rate, channels=channels, data=data,
                             frequency=300.0, q=12.0, threshold_db=-60.0,
                             ratio=8.0)
    S.render(effect, lead + on + 32, channels)
    effect.reset()
    residual = S.peak(S.render(effect, rate // 20, channels), 0, channels)
    check("STATE reset clears the split", residual < 100,
          "residual %d LSB, patch_index %r" % (residual, effect.patch_index))
    effect.deinit()
    effect.deinit()
    still = audiocore.get_buffer(source)[1] is not None
    check("STATE deinit leaves the source rendering", still,
          "source still answers get_buffer")


def capabilities(rate, channels):
    """The transport is handed in and must never be called."""
    calls = []

    def transport():
        calls.append(1)
        return (False, 0.0, 120.0, 4, 4)

    data = S.sine(1000.0, S.amp(-6.0), rate // 2, rate, channels)
    source = audiocore.RawSample(data, sample_rate=rate,
                                 channel_count=channels)
    import audioeffects
    effect = audioeffects.create('DynamicEQ', source, rate,
                                 transport=transport)
    S.render(effect, rate // 2, channels)
    for index in range(len(type(effect).MACRO_LABELS)):
        effect.set_macro(index, 64)
    ok = not calls and effect.capabilities == ()
    check("CAPS () and the transport is never read", ok,
          "read %d times, capabilities %r" % (len(calls), effect.capabilities))


def rate_honest(rate, channels):
    """A band above the running rate's usable span clamps, never refuses."""
    data = S.sine(1000.0, S.amp(-6.0), rate // 10, rate, channels)
    effect, _ = S.build(rate=rate, channels=channels, data=data)
    effect.set_macro(0, 127)
    applied = effect.frequency_hz
    # The span tops out at 16 kHz and the class clamps at 0.4 * rate, so the
    # honest expectation is the lower of the two - a clamp at 48 kHz would be
    # the class refusing a band the rate has room for.
    wanted = rate * 0.4 if rate * 0.4 < 16000.0 else 16000.0
    ok = abs(applied - wanted) < 1.0 and effect.macro(0) >= applied
    check("RESPONSE Hz spans clamp below Nyquist", ok,
          "asked %0.1f Hz, applied %0.1f Hz, expected %0.1f"
          % (effect.macro(0), applied, wanted))


def law(rate, channels):
    """The gain law at this rate: the Tier 2 anchor, run here so the
    per-interpreter table has one number that is about the DSP."""
    data = S.sine(3000.0, S.amp(-10.0), rate, rate, channels)
    effect, _ = S.build(rate=rate, channels=channels, data=data)
    out = S.render(effect, rate, channels)
    skip = rate // 2
    moved = S.gain_db(S.rms(out, skip, channels), S.rms(data, skip, channels))
    predicted = S.compressor_law(20.0, 4.0)
    check("LAW composite within 1 dB of the gain computer",
          abs(moved - predicted) < 1.0,
          "%+0.3f dB against %+0.3f" % (moved, predicted))


def main():
    print("interpreter: %s" % sys.implementation.name)
    for rate in RATES:
        for channels in (2, 1):
            print("\n== %d Hz, %d channel%s"
                  % (rate, channels, "" if channels == 1 else "s"))
            wire(rate, channels)
            level(rate, channels)
            tail(rate, channels)
            click(rate, channels)
            state(rate, channels)
            capabilities(rate, channels)
            rate_honest(rate, channels)
            law(rate, channels)
    print("\n%d failures" % len(FAILURES))
    for label in FAILURES:
        print("  %s" % label)
    sys.exit(1 if FAILURES else 0)


if __name__ == '__main__':
    main()
