"""`Flanger` - a swept comb on CircuitPython's own `audiodelays.Flanger`.

The player's text is the class docstring; the `CLAIMS` table in the class's
test file ties its claim sentences to tests. How the node behaves is told
where the class drives it, in `Flanger._build`.
"""

VENDOR = "PyDevices"

import math

import audiodelays

from . import _component


RATE_I, RANGE_I, MANUAL_I, COLOR_I, MIX_I, POLARITY_I, SYNC_I, DIVISION_I = \
    range(8)

#: The line, fixed: nothing re-allocates after construction.
MAX_DELAY_MS = 10

#: Frames a pull hands out: the palette's block.
BLOCK = 256

#: Sync's divisions in bars, Phaser's own (`phaser.py:DIVISION_BARS`).
DIVISION_BARS = (4.0, 2.0, 1.0, 0.5, 1.0 / 3.0, 0.25, 0.125)

POLARITIES = ("positive", "negative")

#: 20 log10(32768), rounded up: a peak this far under full scale is under
#: one LSB.
SILENCE_DB = 90.31

#: How far a knob may sit from the step its constructor value seeded and
#: still count as not moved (a host echoing `get_macro` back).
ECHO_TOLERANCE = 1e-6

_RANGES = (
    (0.05, 10.0, "log"),        # 0  Rate, Hz
    (0.0, 1.0),                 # 1  Range: Manual to 10 ms
    (0.25, 5.0, "log"),         # 2  Manual, ms
    (0.0, 0.95),                # 3  Color; the node stops at 0.95
    (0.0, 1.0),                 # 4  Mix
    (0.0, 1.0),                 # 5  Polarity (TOGGLE)
    (0.0, 1.0),                 # 6  Sync (TOGGLE)
    (0.0, 6.0),                 # 7  Division index into DIVISION_BARS
)


def _patch(rate, depth, manual, color, mix, negative, sync, bars):
    """A patch's MIDI steps from the card's engineering values."""
    division = DIVISION_BARS.index(bars)
    values = (rate, depth, manual, color, mix, 1.0 if negative else 0.0,
              1.0 if sync else 0.0, float(division))
    return tuple(_component.macro_of(span, value)
                 for span, value in zip(_RANGES, values))


#: Patch 0, "Slow jet", on the grid. Construction is patch 0 (the
#: contract), so each constructor default is the value of patch 0's step.
PATCH_0 = _patch(0.25, 0.6, 1.0, 0.7, 1.0, False, False, 1.0)

#: Each constructor keyword's default, which NaN falls back to: Rate about
#: 0.25 Hz, Range about 0.6, Manual about 1 ms, Color about 0.7, Mix 1.
DEFAULTS = tuple(_component.macro_value(_RANGES[i], PATCH_0[i] / 127.0)
                 for i in range(5))
RATE, RANGE, MANUAL_MS, COLOR, MIX = DEFAULTS


def _choice(choices, position):
    last = len(choices) - 1
    return choices[min(last, max(0, int(round(position * last))))]


def _option(value, default, span):
    """A constructor value: NaN is the default, past a stop is that stop."""
    value = float(value)
    if value != value:
        value = default
    return min(span[1], max(span[0], value))


def tail_frames(color, top_ms, rate):
    """Frames until the ring is exact silence, for Color `color` and a
    sweep whose top is `top_ms`, at `rate` (the card's section 5).

    Interpolation never exceeds its two samples and the feedback truncates
    toward zero, so the line's peak falls by at least g each D + 1 frames,
    and is zero once it would fall under one LSB."""
    line = int(rate // 100)
    longest = min(line, int(math.ceil(top_ms * rate / 1000.0)))
    g = int(color * 32767) / 32767.0
    if g <= 0.0:
        return longest + 3
    trips = int(math.ceil(SILENCE_DB / (-20.0 * math.log10(g))))
    return (trips + 2) * (longest + 1) + 2


class Flanger(_component.Component):
    """A flanger: your signal plus a copy of itself a few milliseconds
    late, the delay swept up and down by a triangle, so the comb of notches
    the sum makes moves through the spectrum.

    **The controls.** Rate is the sweep's speed. Manual is the sweep's
    floor, and Range is how far it climbs from there towards 10 ms: at
    Range 0 the comb holds still at Manual. Color feeds the copy back into
    the line and raises the comb's peaks into a ring. Mix is the copy's
    level against a dry that never moves: 1 is equal weight and the deepest
    notches, 0 is a wire. Polarity minus turns the comb over and puts a
    notch at DC. With Sync on, one sweep lasts Division bars at the host's
    tempo and meter, and Rate is ignored. Constructor values play exactly
    until their knob first moves or a patch loads. The Effect controls page
    lists what the knobs span.

    **What you hear.** The copy is your signal exactly Manual late, added
    at Mix.
    At Color 0 and Mix 1 a tone on a notch comes out at least 40 dB down.
    Color raises the peaks by up to 26.4 dB over the input and fills the
    notches to 6 dB under it.
    The sweep is a triangle in milliseconds that starts at Manual and
    reaches its top once a sweep.
    The ring lasts about 0.4 s to -60 dB at 3 ms and full Color, and
    about 0.7 s at 5 ms; it grows as Range sweeps the delay longer, and it
    never oscillates on its own.

    **Limits.** It is linear only to about -28 dBFS on a resonant frequency
    at full Color, and -7.5 dBFS at Color 0: above that the output is
    squashed and gritty, not louder.
    Turning Mix up makes the output louder, by 6 dB on a comb peak at Mix 1:
    there is no wet-only setting.
    There is no tone control, no through-zero and no stereo spread: both
    channels sweep together.
    Sync sets the sweep's period, not its phase: the sweep starts at Manual
    when the class is built or reset, not on a bar line, and a synced sweep
    faster than 20 Hz runs at 20 Hz.
    A control that jumps makes the output step: move it in small steps from
    the host if you need it smooth.
    At 22.05 kHz the sweep's top is 9.977 ms, half a frame under 10 ms.
    Mix's first step above 0 is still a wire; the copy comes in at the
    second step, about 36 dB down.
    Keep the input under -6 dBFS.

    **Wire, latency, tail.** At Mix 0 the output is the input, byte for
    byte.
    There is no latency.
    `tail_samples` is the longest the ring can last at the controls in
    force, while the source keeps playing, silence included.
    If the source ends, the output stops dead; `reset()` clears what the
    line held and returns to patch 0.
    On a CircuitPython board, stop the flanger from the host if your source
    can run dry: CircuitPython's own flanger waits on a source that comes
    back empty. Firmware built with micropython-pydevices' build_mp.py
    carries the fix and returns.
    """

    NAME = 'Flanger'
    DISPLAY_NAME = 'Flanger'
    CATEGORIES = ('Modulation',)
    VERSION = '0.1.0'

    #: Upstream's own node: it runs on a stock CircuitPython board.
    TIER = _component.STOCK
    REQUIRES = ()

    CAPABILITIES = ("tempo_sync",)
    _SYNC_MACRO = SYNC_I
    LATENCY_SAMPLES = 0
    #: The worst case at 48 kHz: full Color and the sweep at the line's top
    #: (D = 480 frames). `tail_samples` is the bound at the controls in
    #: force.
    TAIL_SAMPLES = 98607

    #: On stock CircuitPython the wet's interpolation overflows int32 where
    #: two neighbouring line samples are more than 32768 apart at a
    #: fractional delay (audiodsp#76, widened in audiodsp's copy). At Color
    #: 0 the line is the input, so -6 dBFS keeps it safe there.
    INPUT_CEILING_DBFS = -6.0

    #: The constructor's exact values, which play until their knob moves.
    _KEPT = ("_exact",)

    MACRO_LABELS = ("Rate", "Range", "Manual", "Color", "Mix", "Polarity",
                    "Sync", "Division")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR", 5: "TOGGLE", 6: "TOGGLE",
                   7: "UNIPOLAR"}
    _MACRO_RANGES = _RANGES
    _MACRO_UNITS = {0: "Hz", 2: "ms"}

    PATCHES = {
        0: ("Slow jet", PATCH_0),
        1: ("Fast metallic",
            _patch(4.0, 0.15, 0.5, 0.85, 1.0, False, False, 1.0)),
        2: ("Held comb", _patch(0.25, 0.0, 2.0, 0.6, 1.0, False, False, 1.0)),
        3: ("Negative jet",
            _patch(0.2, 0.6, 1.0, 0.7, 1.0, True, False, 1.0)),
        4: ("Gentle", _patch(0.5, 0.3, 2.0, 0.0, 0.5, False, False, 1.0)),
        5: ("Synced one bar",
            _patch(0.25, 0.6, 1.0, 0.6, 1.0, False, True, 1.0)),
    }

    def _build(self, rate=RATE, depth=RANGE, manual_ms=MANUAL_MS,
               color=COLOR, mix=MIX, polarity="positive", sync=False, division=1.0,
               patch=None):
        if polarity not in POLARITIES:
            raise ValueError("polarity must be %r or %r, not %r"
                             % (POLARITIES[0], POLARITIES[1], polarity))
        asked = (rate, depth, manual_ms, color, mix)
        exact = tuple(_option(asked[i], DEFAULTS[i], _RANGES[i])
                      for i in range(5))
        #: The constructor's values, exactly, None for a knob that has
        #: moved since. A patch drops them all.
        self._exact = exact
        bars = float(division)
        index = 2
        if bars == bars:
            for k in range(len(DIVISION_BARS)):
                if (abs(DIVISION_BARS[k] - bars)
                        < abs(DIVISION_BARS[index] - bars)):
                    index = k
        self._ready = False

        # The whole graph is the node. Each frame its line is read at
        # Manual + Range * (10 ms - Manual) * tri(n), a 0-1-0 triangle whose
        # phase starts at 0 on construction and on a reset
        # (src/audiodelays/Flanger.c:94, `:172-183`) and advances by
        # rate / sample_rate a frame (`:280-281`); the line writes
        # x + wet * feedback and the output is x +- wet * mix through a soft
        # knee. Every control is read once a pull. A reset, the base's walk
        # over `_own`, clears the line, the write positions and the phase.
        self._node = self._own(audiodelays.Flanger(
            max_delay_ms=MAX_DELAY_MS, min_delay_ms=exact[MANUAL_I],
            rate=exact[RATE_I], depth=exact[RANGE_I],
            feedback=exact[COLOR_I], mix=exact[MIX_I], invert=False,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count, bits_per_sample=16,
            samples_signed=True,
            buffer_size=BLOCK * 2 * self._channel_count))
        self._node.play(self._source)
        self._output = self._node

        # Each knob seeds the step nearest its constructor value, so a
        # fresh instance reads whole MIDI steps; the exact value plays.
        values = exact + (1.0 if polarity == POLARITIES[1] else 0.0,
                          1.0 if sync else 0.0, float(index))
        self._seeds = [
            _component.position_of_midi(
                self._mode(i), _component.macro_of(_RANGES[i], values[i]))
            for i in range(8)]
        self._seeding = True
        try:
            self._init_macros(values)
            for i in range(8):
                self._macros[i] = self._seeds[i]
        finally:
            self._seeding = False
        if patch is not None:
            self.program_change(patch)
        self._ready = True
        self._refresh()

    # -- the maps ------------------------------------------------------

    def _value(self, index):
        exact = self._exact[index] if index < 5 else None
        if exact is not None:
            return exact
        return _component.macro_value(_RANGES[index], self._macros[index])

    def _negative(self):
        return self._macros[POLARITY_I] >= 0.5

    def _rate_hz(self):
        """The sweep's rate: Rate, or with Sync on, one sweep per Division
        bars at the host's tempo, a bar numerator x 4 / denominator quarter
        notes of its time signature (Phaser's rule)."""
        if self._macros[SYNC_I] < 0.5:
            return self._value(RATE_I)
        tempo, quarters = self._synced_beat()
        bars = _choice(DIVISION_BARS, self._macros[DIVISION_I])
        return tempo / (60.0 * quarters * bars)

    def _top_ms(self):
        manual = self._value(MANUAL_I)
        return manual + self._value(RANGE_I) * (MAX_DELAY_MS - manual)

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        if (index < 5 and self._exact[index] is not None
                and not self._seeding
                and abs(position - self._seeds[index]) > ECHO_TOLERANCE):
            exact = list(self._exact)
            exact[index] = None
            self._exact = tuple(exact)
        if self._ready:
            self._refresh()

    def _apply_positions(self, positions, patch_index):
        """A patch (or a rack's restore) applied whole, then the node set
        once. A patch drops the constructor's values; a restore keeps the
        ones it put back (`_KEPT`)."""
        ready = self._ready
        self._ready = False
        try:
            _component.Component._apply_positions(self, positions,
                                                  patch_index)
        finally:
            self._ready = ready
        if not self._seeding:
            self._exact = (None,) * 5
        if ready:
            self._refresh()

    def _refresh(self):
        node = self._node
        color = self._value(COLOR_I)
        negative = self._negative()
        node.min_delay_ms = self._value(MANUAL_I)
        node.depth = self._value(RANGE_I)
        node.rate = self._rate_hz()
        node.feedback = -color if negative else color
        node.invert = negative
        node.mix = self._value(MIX_I)

    def transport_changed(self):
        """With Sync on, follow the host's tempo and its meter: a move of
        either sets the sweep's rate again. The base follows the tempo
        alone, so a 4/4 to 3/4 change at one tempo would keep the old
        rate."""
        self._check_live()
        index = type(self)._SYNC_MACRO
        if index is None or self._macros[index] < 0.5:
            return
        # What the host got wrong (a tempo of None or NaN, a field missing,
        # a signature of 4/0 or 10**400/4) keeps the last good reading, so
        # it is no change and the sweep plays on as it was.
        followed = self._synced_beat()
        if followed == self._followed_bpm:
            return
        self._followed_bpm = followed
        # The base's own path: the Sync switch applied where it stands.
        self._apply_macro(index, self._macros[index])

    def macro(self, index):
        """What macro `index` currently stands for, in its own units; for
        the first five, the value that plays."""
        self._check_live()
        if isinstance(index, int) and 0 <= index < 5:
            return self._value(index)
        return _component.Component.macro(self, index)

    @property
    def tail_samples(self):
        """The bound at the controls in force; see the class docstring."""
        self._check_live()
        return tail_frames(self._value(COLOR_I), self._top_ms(),
                           self._sample_rate)
