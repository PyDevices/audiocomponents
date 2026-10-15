"""Mix back up from 0 plays nothing from before (Phase 7, step 7f, F3).

At Mix 0 the host reads the source itself, so whatever the node at the head
of the graph still held is audio the host has read past. Six classes kept
it: a Splitter on the source holds the rest of a source buffer in its ring,
a Biquad or a MidSide the rest of the buffer it was reading, and the node
behind a Splitter's tap the rest of a tap's chunk. With a source whose
buffers are not 256 frames, bringing Mix back played up to 20 ms of what
was sounding when the bypass began, at full level, and the stream ran late
by as much. Each class now lets go of those frames as it rejoins
(`_component.let_go_of_source`).

The material stops while Mix is at 0, so anything the class plays once Mix
comes back is from before.

    python -m unittest tests.test_bypass_return
"""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "lib"))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))

import audioroute                                         # noqa: E402

import audioeffects                                       # noqa: E402
import kit_common as kc                                   # noqa: E402
import kit_options                                        # noqa: E402
import lifecycle                                          # noqa: E402

RATE = 48000

#: (class, extra options). The head the class lets go of, by case:
#: Distortion's MidSide and Fuzz's germanium Biquad, then the four
#: Splitters and cascade Fuzz's, which need `Splitter.clear()`.
PLAY_HEADS = (("Distortion", {}), ("Fuzz", {}))
SPLIT_HEADS = (("Bitcrusher", {}), ("Bitcrusher", {"patch": 3}),
               ("Compressor", {}), ("Exciter", {}),
               ("Saturation", {}), ("Fuzz", {"character": "cascade"}))

#: What the native Splitter needs to let go of its ring: audiodsp
#: 0.6.6rc7, which the pin carries, so the cases run everywhere.


def render_return(name, options, channels, kind):
    """What the class plays once Mix is back, after the material stopped
    under the bypass."""
    cls = getattr(audioeffects, name)
    mix = list(cls.MACRO_LABELS).index("Mix")
    values = kc.noise(4096, channels, 12000)
    feed = lifecycle.Feed(values, RATE, channels, kind, loop=False)
    opts = dict(kit_options.options_for(name))
    opts.update(options)
    e = kc.build(cls, feed.port, RATE, None, opts)
    try:
        kc.render(e, 2048)
        e.set_macro(mix, 0)
        # The host reads the source until well past the material's end.
        kc.render(e, 8192)
        e.set_macro(mix, 127)
        return kc.render(e, 4096)
    finally:
        e.deinit()


class MixBackFromZeroPlaysNothingFromBefore(unittest.TestCase):

    def check(self, cases):
        for name, options in cases:
            for channels in (2, 1):
                for kind in ("1000", "100", "512"):
                    with self.subTest(cls=name, options=options,
                                      channels=channels, kind=kind):
                        got = render_return(name, options, channels, kind)
                        loud = max(abs(v) for v in kc.samples(got)) \
                            if got.strip(b"\0") else 0
                        self.assertEqual(loud, 0,
                                         "peak %d from before the bypass"
                                         % loud)

    def test_a_head_that_re_plays(self):
        self.check(PLAY_HEADS)

    def test_a_splitter_head(self):
        self.assertTrue(hasattr(audioroute.Splitter, "clear"),
                        "audiodsp below the pin: no Splitter.clear()")
        self.check(SPLIT_HEADS)


if __name__ == "__main__":
    unittest.main()
