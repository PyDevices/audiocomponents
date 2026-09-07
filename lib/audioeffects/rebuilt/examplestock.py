"""Worked example of the rebuilt-class shape - **stock** portability tier.

This is a fixture, not an effect. It is deliberately **not** one of the 46:
its `NAME` is absent from `audioeffects.__all__`, so it never enters
`audioeffects.ALL` and no host can reach it. It exists so that

* the registry rule has something to resolve before any real class is
  rebuilt (`tests/test_rebuilt_registry.py`), and
* the portability-tier test has a stock-tier subject on the day it is
  written, rather than a battery that passes because it has nothing to hold
  (`tests/test_portability_tier.py`).

Both fixtures here are removed at Phase 7 - audiocomponents#37.

Read it as the template for a real rebuild: module-level `VENDOR`, one class,
`_build` instead of `__init__`, every node handed to `self._own()`, macros
seeded through `_init_macros()` so the constructor and `set_macro` cannot
drift apart, and a `TIER` that says where it runs.
"""

VENDOR = "PyDevices"

import audiofilters
import synthio

from .. import _component


class ExampleStock(_component.Component):
    """A low-pass with a mix knob, built from CircuitPython-ported nodes
    only: `audiofilters.Filter` and a `synthio.Biquad`. Nothing here needs
    an audioif-own module, so it runs on a stock CircuitPython board."""

    NAME = 'ExampleStock'
    DISPLAY_NAME = 'Example (stock tier)'
    CATEGORIES = ('Example',)
    VERSION = '0.0.1'

    TIER = _component.STOCK
    REQUIRES = ()

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Cutoff", "Mix")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR"}
    _MACRO_RANGES = ((200.0, 12000.0, "log"), (0.0, 1.0))
    PATCHES = {
        0: ("Open", (93, 127)),
        1: ("Dark", (32, 127)),
    }

    def _build(self, cutoff_hz=4000.0, mix=1.0, patch=None):
        # A synthio block rather than a plain float, so a macro move
        # retunes the running filter instead of rebuilding it.
        self._frequency = synthio.Math(synthio.MathOperation.SUM,
                                       self._hz(cutoff_hz), 0.0, 0.0)
        self._biquad = synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                      self._frequency, Q=0.707)
        node = self._own(audiofilters.Filter(filter=self._biquad, mix=mix,
                                             **self._pcm()))
        node.play(self._source)
        self._node = node
        self._output = node
        self._init_macros((cutoff_hz, mix), patch)

    def _apply_macro(self, index, position):
        if index == 0:
            self._frequency.a = self._hz(
                _component.macro_value(self._MACRO_RANGES[0], position))
        else:
            self._node.mix = _component.macro_value(self._MACRO_RANGES[1],
                                                    position)
