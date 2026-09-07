"""Worked example of the rebuilt-class shape - **audioif** portability tier.

The sibling of `examplestock.py`, and the same kind of fixture: not one of
the 46, absent from `audioeffects.__all__`, removed at Phase 7
(audiocomponents#36). It exists so `tests/test_portability_tier.py` has an
audioif-tier subject to hold to its documented `ImportError` from the day
the test is written.

The tier pattern is `CabinetSim`'s (`drive.py:29-32`, `:331-332`), in two
halves. The **guarded import** below keeps this module importable on a stock
CircuitPython board, so the other classes in a family module stay reachable.
The **construction-time raise** is the base class's `_require_modules()`,
driven by `REQUIRES`; it imports the module for itself rather than reading
the `None` above, so blocking a module after this file was imported still
raises - which is how the tier can be tested on CPython at all.
"""

VENDOR = "PyDevices"

from .. import _component

try:
    import audioecho
except ImportError:      # a stock CircuitPython board, or an old audioif
    audioecho = None


class ExampleAudioif(_component.Component):
    """A feedback delay on `audioecho.FeedbackDelay` - an audioif-own node,
    so this class needs audioif's build and says so."""

    NAME = 'ExampleAudioif'
    DISPLAY_NAME = 'Example (audioif tier)'
    CATEGORIES = ('Example',)
    VERSION = '0.0.1'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioecho",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    #: A feedback line's tail is not finitely bounded by construction.
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Time", "Feedback")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((20.0, 500.0, "log"), (0.0, 0.9))
    PATCHES = {
        0: ("Quarter", (100, 56)),
        1: ("Slap", (24, 12)),
    }

    MAX_DELAY_MS = 500.0

    def _build(self, delay_ms=250.0, feedback=0.4, patch=None):
        node = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_delay_ms=self.MAX_DELAY_MS,
            delay_ms=delay_ms, feedback=feedback, mix=0.5))
        node.play(self._source)
        self._node = node
        self._output = node
        self._init_macros((delay_ms, feedback), patch)

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index == 0:
            self._node.set(delay_ms=min(value, self.MAX_DELAY_MS))
        else:
            self._node.set(feedback=value)
