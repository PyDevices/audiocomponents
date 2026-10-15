"""Settings changed between construction and the first pull land as a fresh
instance at those settings would (Phase 7, step 7f).

A class whose mixer voices primed a block of the source at construction
gave that block away before anything was played: a Mix 0 set next handed
out the source from frame 256, and a patch change played the block through
the old patch's filters. Construction now arms the voices on silence where
`get_buffer` can hand it up, as a reset does (`Component.LAZY_BUILD`). On
a build without `get_buffer` it cannot, and the old first block stays
(the kit's nogb rows say so).

    python -m unittest tests.test_first_pull
"""

import math
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "lib"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import audioeffects                                       # noqa: E402
import kit_common as kc                                   # noqa: E402
import kit_options                                        # noqa: E402

VENDOR = "PyDevices"
RATE = 48000

#: The classes whose Mix 0 lost the first block (`LAZY_BUILD`), and
#: Exciter, which shared the cause. DeEsser's bypass is Range 0. Phaser's
#: input guard primes at `play()` as DynamicEQ's does.
WIRES = ("Bitcrusher", "Compressor", "DeEsser", "Distortion", "DynamicEQ",
         "MultibandCompressor", "Saturation", "Exciter", "Phaser")


def _bypass_index(cls):
    label = "Range" if cls.NAME == "DeEsser" else "Mix"
    return list(cls.MACRO_LABELS).index(label)


class AMixZeroBeforeTheFirstPullIsTheWire(unittest.TestCase):

    def check(self, name, channels):
        cls = getattr(audioeffects, name)
        values = kc.noise(4096, channels, 8000)
        feed = kc.feed(values, RATE, channels)
        e = kc.build(cls, feed.port, RATE, None,
                     kit_options.options_for(name))
        try:
            e.set_macro(_bypass_index(cls), 0)
            got = kc.render(e, 2048)
        finally:
            e.deinit()
        want = bytes(values)[:len(got)]
        self.assertEqual(got, want, "%s, %d channels" % (name, channels))

    def test_every_class(self):
        for name in WIRES:
            for channels in (2, 1):
                with self.subTest(name=name, channels=channels):
                    self.check(name, channels)


class AResetBeforeTheFirstPullIsAFreshBuild(unittest.TestCase):
    """Built, reset, then played: the material from its first frame, as a
    fresh instance plays it. DynamicEQ's and MultibandCompressor's input
    node takes a block at `play()`, so the kit's fresh check, which reads
    where the source stands, expects frame 256 there (kit_common's rows)."""

    def test_every_class(self):
        import kit_fresh
        for name in WIRES:
            for channels in (2, 1):
                with self.subTest(name=name, channels=channels):
                    cls = getattr(audioeffects, name)
                    options = kit_options.options_for(name)
                    values = kit_fresh._material(RATE, channels)
                    feed = kit_fresh._feed(values, RATE, channels)
                    e = kc.build(cls, feed.port, RATE, None, options)
                    e.reset()
                    got = kc.render(e, 2048)
                    e.deinit()
                    feed = kit_fresh._feed(values, RATE, channels)
                    f = kit_fresh._fresh_at(cls, feed.port, RATE, options)
                    want = kc.render(f, 2048)
                    f.deinit()
                    self.assertEqual(got, want)


class AMixZeroAfterAMidStreamArmingIsTheWire(unittest.TestCase):
    """A re-arm mid-stream takes nothing from the source either: a Mix
    move off 0 and back, a reset, or a patch change (some build the graph
    again), with Mix 0 set in the same gap. The output from there on is the
    source, on time. Each primed a block eagerly, so the bypass after it
    handed out a source 256 frames short (5 ms of the song skipped)."""

    FRAMES = 4096
    TAIL = 1024

    def check(self, name, channels, move):
        cls = getattr(audioeffects, name)
        values = kc.noise(self.FRAMES, channels, 8000)
        feed = kc.feed(values, RATE, channels)
        e = kc.build(cls, feed.port, RATE, None,
                     kit_options.options_for(name))
        mix = _bypass_index(cls)

        def act(e):
            move(e)
            e.set_macro(mix, 0)
        try:
            got = kc.render(e, self.FRAMES, {6: act})
        finally:
            e.deinit()
        size = 2 * channels
        want = bytes(values)[(self.FRAMES - self.TAIL) * size:]
        self.assertEqual(got[(self.FRAMES - self.TAIL) * size:], want)

    def moves(self, cls):
        mix = _bypass_index(cls)
        out = [("rejoin", lambda e: (e.set_macro(mix, 0),
                                     e.set_macro(mix, 127))),
               ("reset", lambda e: e.reset())]
        for patch in sorted(cls.PATCHES):
            out.append(("patch %d" % patch,
                        lambda e, p=patch: e.program_change(p)))
        return out

    def test_every_class(self):
        # DeEsser's reset and HF-only patches replay its head node, a
        # cause of their own, not this one.
        for name in [n for n in WIRES if n != "DeEsser"] + ["Overdrive"]:
            cls = getattr(audioeffects, name)
            for label, move in self.moves(cls):
                for channels in (2, 1):
                    with self.subTest(name=name, move=label,
                                      channels=channels):
                        self.check(name, channels, move)


def _blocks(data, channels):
    """(peak, largest sample-to-sample step) per 256-frame block."""
    s = kc.samples(data)
    n = 256 * channels
    out = []
    for b in range(len(s) // n):
        block = s[b * n:(b + 1) * n]
        step = max(abs(block[i] - block[i - channels])
                   for i in range(channels, len(block)))
        out.append((max(abs(x) for x in block), step))
    return out


class CleanEdgeDoesNotCrack(unittest.TestCase):
    """Distortion patch 10, "Clean Edge": its Filter 0 corner puts the
    post-clip section's poles near -1, and the section swung there with a
    darker corner's state rang rail to rail."""

    def render(self, amp, actions, frames=4096, patch=None):
        values = kc.sine(RATE // 4, 2, amp, RATE // 200)
        feed = kc.feed(values, RATE, 2)
        e = kc.build(audioeffects.Distortion, feed.port, RATE, patch)
        try:
            return _blocks(kc.render(e, frames, actions), 2)
        finally:
            e.deinit()

    def test_a_change_to_it_mid_stream(self):
        for amp in (327, 3277):                  # -40 and -20 dBFS
            with self.subTest(amp=amp):
                got = self.render(
                    amp, {8: lambda e: e.program_change(10)})
                peak, step = got[8]
                self.assertLess(peak, 20000, got[6:11])
                self.assertLess(step, 30000, got[6:11])
                self.assertLess(got[10][0], 2 * amp, got[6:11])

    def test_a_filter_move_to_its_open_end(self):
        for start in (127, 64, 10, 3):
            with self.subTest(start=start):
                values = kc.sine(RATE // 4, 2, 3277, RATE // 200)
                feed = kc.feed(values, RATE, 2)
                e = kc.build(audioeffects.Distortion, feed.port, RATE)
                try:
                    e.set_macro(1, start)
                    got = _blocks(kc.render(
                        e, 4096, {8: lambda e: e.set_macro(1, 0)}), 2)
                finally:
                    e.deinit()
                self.assertLess(got[8][0], 20000, got[6:11])

    def test_a_change_to_it_before_the_first_pull(self):
        for amp in (327, 3277):
            with self.subTest(amp=amp):
                got = self.render(amp, None, frames=2048, patch=10)
                for peak, step in got:
                    self.assertLessEqual(peak, amp, got)


class DeEsserOnsetDoesNotBump(unittest.TestCase):
    """audiocomponents#148: patches 3 and 4 (HF-only), set before the first
    pull, played the first block the voices had primed at patch 0 and came
    in up to 3 dB hot for the first 20 ms of a sustained note."""

    def test_hf_only_patches_set_before_the_first_pull(self):
        window = RATE // 50
        for amp in (32767, 3277):
            for patch in (3, 4):
                with self.subTest(amp=amp, patch=patch):
                    values = kc.sine(RATE, 2, amp, RATE // 50)
                    feed = kc.feed(values, RATE, 2)
                    e = kc.build(audioeffects.DeEsser, feed.port, RATE,
                                 patch)
                    try:
                        s = kc.samples(kc.render(e, RATE // 2))
                    finally:
                        e.deinit()

                    def rms(a, b):
                        t = 0
                        for i in range(2 * a, 2 * b):
                            t += s[i] * s[i]
                        return math.sqrt(t / (2.0 * (b - a)))
                    steady = rms(RATE // 4, RATE // 4 + 5 * window)
                    for k in range(2):
                        level = rms(k * window, (k + 1) * window)
                        self.assertLess(
                            20 * math.log10(level / steady), 0.2,
                            "window %d" % k)


if __name__ == "__main__":
    unittest.main()
