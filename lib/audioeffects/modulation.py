"""Modulation effects still served from this family module: `Flanger`.

Phase 3's THROUGH classes and `RingMod` live one file per effect beside
this package. LFOs tick at the engine's block rate (about 187 Hz at 48 kHz),
which is ample for musical sweep rates. `Flanger` stays here until CircuitPython
10.3.0's own node lands in a later follow-up.
"""

VENDOR = "PyDevices"

import audiodelays
import synthio

from . import _core


class Flanger(_core.Effect):
    """A very short modulated delay with feedback and doppler - the real
    swept comb, jet engine included."""

    NAME = 'Flanger'
    DISPLAY_NAME = 'Flanger'
    CATEGORIES = ('Modulation',)
    VERSION = '0.0.1'
    MACRO_LABELS = ()
    MACRO_MODES = {}
    PATCHES = {0: ("Default", ())}

    def __init__(self, source, rate=0.25, depth_ms=2.5, feedback=0.6,
                 mix=0.5):
        self.motion = synthio.LFO(rate=rate, scale=depth_ms,
                                  offset=depth_ms + 1.0)
        self.node = audiodelays.Echo(
            max_delay_ms=int(depth_ms * 2 + 20), delay_ms=self.motion,
            decay=feedback, mix=mix, freq_shift=True, **_core.pcm())
        self.node.play(source)
        self._output = self.node
