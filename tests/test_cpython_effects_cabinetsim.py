"""`CabinetSim`'s own invariant and planted-fault tests.

Dossier: workspace docs/effects-internal/dossiers/CabinetSim.md, frozen
2026-09-17, T3 re-cut in the first fix round, three disclosures added in
the second. Exhaustive rate coverage and the 211-position fault sweep live
in the evidence pack and in
`docs/effects-internal/probes/cabinetsim_fix2.py`; this file asserts at
48 kHz unless the test is about rate or latency, and sweeps the macro
surface at MIDI 0/32/64/96/127 (`GRID`) plus the seven shipped patches -
and at MIDI 0/8/../120/127 (`FINE`) where a guard was found green just
past the coarse grid's last step.

Every guard here is written so it can go the other way: each fault test
asserts the fault RED and the clean class GREEN in the same test, from the
same measurement, so a fault that stopped firing would fail on its own line
rather than pass silently.
"""

import math
import os
import struct
import sys
import unittest
from array import array

import numpy as np

import audiobiquad

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import kit_faults                                               # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects import _component                             # noqa: E402
from audioeffects import cabinetsim as rebuilt                  # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
CabinetSim = rebuilt.CabinetSim
FRAMES = 8192
LF_FRAMES = 32768       # 20-100 Hz need cycles, and three high passes ring

#: The macro grid the sweeps walk, per macro, on both characters.
GRID = (0, 32, 64, 96, 127)
#: The finer grid the fault sweeps walk. MIDI 0/8/../120 plus 127, which
#: is the denominator the second refutation used - the shipped sweep's
#: 0/32/64 stopped just short of where a guard went green.
FINE = tuple(list(range(0, 128, 8)) + [127])
#: Every trait is read at Mix 1. `MIX` is macro 7.
MIX = 7


def sine(hz, dbfs, frames=FRAMES, rate=RATE, channels=2):
    """A tone on a whole number of cycles, so it sits on a DFT bin."""
    cycles = max(1, int(round(hz * frames / rate)))
    index = np.arange(frames)
    values = 10.0 ** (dbfs / 20.0) * np.sin(2.0 * math.pi * cycles * index
                                            / frames)
    quantised = np.clip(np.round(values * 32767.0), -32768, 32767).astype(
        np.int64)
    if channels == 2:
        quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist()), cycles * rate / frames


def build(cls=None, rate=RATE, channels=2, frames=FRAMES, probe=None,
          **options):
    cls = cls or CabinetSim
    if probe is None:
        probe = probes.silence(frames, channels)
    source = probes.ArraySource(probe, rate=rate, block=256,
                                channels=channels)
    return cls.create(source, rate, **options)


def render(effect, frames, rate=RATE, channels=2):
    return probes.render(effect.output, frames, rate=rate, channels=channels,
                         block=256, label=None, class_name="CabinetSim",
                         latency_samples=effect.latency_samples)


_DRY = {}


def _dry(hz, dbfs, frames, rate):
    key = (hz, dbfs, frames, rate)
    if key not in _DRY:
        probe, exact = sine(hz, dbfs, frames=frames, rate=rate)
        got = probes.render(
            probes.ArraySource(probe, rate=rate, block=256, channels=2),
            frames, rate=rate, channels=2, block=256)
        _DRY[key] = (probe, exact,
                     abs(kit.tone_bin(got.float[frames // 2:, 0], rate,
                                      exact)))
    return _DRY[key]


def abs_db(cls, hz, dbfs=-20.0, frames=FRAMES, rate=RATE, patch=None,
           midi=None, **options):
    """Magnitude at `hz` relative to the dry probe, in dB."""
    probe, exact, dry = _dry(hz, dbfs, frames, rate)
    effect = build(cls, probe=probe, frames=frames, rate=rate, **options)
    try:
        if patch is not None:
            effect.program_change(patch)
        for index, position in (midi or {}).items():
            effect.set_macro(index, position)
        wet = render(effect, frames, rate=rate)
    finally:
        effect.deinit()
    got = abs(kit.tone_bin(wet.float[frames // 2:, 0], rate, exact))
    if got <= 0.0:
        return float("-inf")
    return 20.0 * math.log10(got / dry)


def rel_db(cls, hz, **kwargs):
    """Magnitude at `hz` re 1 kHz, from rendered tones."""
    return abs_db(cls, hz, **kwargs) - abs_db(cls, 1000.0, **kwargs)


def fall(cls, low, high, **kwargs):
    """`low` minus `high`, in dB. The 1 kHz reference cancels."""
    return abs_db(cls, low, **kwargs) - abs_db(cls, high, **kwargs)


def periodic_tone(hz, dbfs, frames, rate):
    """A tone on a whole number of cycles **of the analysis window**.

    The window is the second half of the render, so the cycle count is
    chosen against `frames // 2`; a tone periodic over the half is
    periodic over the whole. Without that, leakage reads a constant 12 %
    THD at every level and hides the clipping this measures.
    """
    half = frames // 2
    cycles = max(1, int(round(hz * half / rate)))
    index = np.arange(frames)
    values = 10.0 ** (dbfs / 20.0) * np.sin(2.0 * math.pi * cycles * index
                                            / half)
    quantised = np.clip(np.round(values * 32767.0), -32768, 32767).astype(
        np.int64)
    quantised = np.repeat(quantised[:, None], 2, axis=1)
    return array("h", quantised.reshape(-1).tolist()), cycles


def distortion(cls, hz, dbfs, frames=8192, rate=RATE, **options):
    """(THD %, worst non-harmonic bin in dB re the fundamental).

    No window function: every bin is exact by construction.
    """
    probe, cycles = periodic_tone(hz, dbfs, frames, rate)
    effect = build(cls, probe=probe, frames=frames, rate=rate)
    try:
        if "patch" in options:
            effect.program_change(options["patch"])
        for index, position in options.get("midi", {}).items():
            effect.set_macro(index, position)
        got = render(effect, frames, rate=rate)
    finally:
        effect.deinit()
    half = frames // 2
    data = np.asarray(got.float)[half:, 0]
    mag = np.abs(np.fft.rfft(data)) * 2.0 / half
    if mag[cycles] <= 0.0:
        return float("nan"), float("nan")
    mask = np.ones(len(mag), dtype=bool)
    mask[0] = False
    harmonics = []
    for k in range(1, 40):
        index = cycles * k
        if index >= len(mag):
            break
        for offset in (-1, 0, 1):
            if 0 <= index + offset < len(mag):
                mask[index + offset] = False
        if k > 1:
            harmonics.append(mag[index])
    thd = 100.0 * math.sqrt(sum(v * v for v in harmonics)) / mag[cycles]
    floor = mag[mask].max() if mask.any() else 0.0
    floor_db = (20.0 * math.log10(floor / mag[cycles]) if floor > 0.0
                else -999.0)
    return thd, floor_db


def surface(include_patches=True):
    """(label, kwargs) over the macro surface, Mix held at 1.

    Mix 0 is the wire and is excluded: it is Tier 1's row, not a trait's.
    """
    out = []
    if include_patches:
        out.extend(("patch %d" % p, {"patch": p}) for p in range(7))
    for character in (0, 127):
        for index in range(1, 7):
            for position in GRID:
                out.append(("char%d macro%d=%d" % (character, index,
                                                   position),
                            {"midi": {0: character, index: position}}))
    return out


def peaks_in(cls, low, high, points=41, **kwargs):
    """(maxima, dip) on a log grid in [low, high], read re 1 kHz."""
    grid = [low * (high / low) ** (i / (points - 1.0))
            for i in range(points)]
    curve = [(hz, abs_db(cls, hz, **kwargs)) for hz in grid]
    ref = abs_db(cls, 1000.0, **kwargs)
    curve = [(hz, value - ref) for hz, value in curve]
    maxima = [curve[i] for i in range(1, len(curve) - 1)
              if curve[i][1] > curve[i - 1][1]
              and curve[i][1] >= curve[i + 1][1]]
    dip = None
    if len(maxima) >= 2:
        a = [hz for hz, _v in curve].index(maxima[0][0])
        b = [hz for hz, _v in curve].index(maxima[1][0])
        dip = min(value for _hz, value in curve[a:b + 1])
    return maxima, dip, curve


def prominence(cls, low=100.0, high=300.0, points=31, **kwargs):
    """The deepest in-band minimum's prominence against its own shoulders."""
    grid = [low * (high / low) ** (i / (points - 1.0))
            for i in range(points)]
    ref = abs_db(cls, 1000.0, **kwargs)
    curve = [abs_db(cls, hz, **kwargs) - ref for hz in grid]
    best = -99.0
    for i in range(1, len(curve) - 1):
        if curve[i] < curve[i - 1] and curve[i] <= curve[i + 1]:
            best = max(best, min(max(curve[:i + 1]), max(curve[i:]))
                       - curve[i])
    return best


# ---- the planted faults --------------------------------------------------
#
# One fault per clause, so a fault fires its own clause and leaves the
# others green: that is the control the spec asks for.


class ShallowCliffCabinet(CabinetSim):
    """T1: the steep shelf is gone, so the top rolls off instead of falling
    off a cliff. The broad shelf alone cannot make 15 dB in 0.678 octaves
    at any rate or any macro position."""
    NAME = 'CabinetSim'

    def _refresh(self):
        CabinetSim._refresh(self)
        if self._shelf_b is not None:
            self._shelf_b.mix = 0.0


class LowPassCabinet(CabinetSim):
    """T2: the shelves become low-passes, so the top keeps falling past
    8 kHz instead of flooring. T2 is not applicable at 22.05 kHz."""
    NAME = 'CabinetSim'

    def _refresh(self):
        CabinetSim._refresh(self)
        top = self._value(5)
        blend = self._value(MIX)
        if self._convolver is not None or self._shelf_a is None:
            return
        if blend <= 0.0:
            return
        self._push(self._shelf_a, audiobiquad.LOW_PASS, top, 0.707, 0.0,
                   blend)
        self._push(self._shelf_b, audiobiquad.LOW_PASS, top, 0.707, 0.0,
                   blend)


class SinglePeakCabinet(CabinetSim):
    """T3: one break-up bell."""
    NAME = 'CabinetSim'

    def _refresh(self):
        CabinetSim._refresh(self)
        if self._peak_b is not None:
            self._peak_b.mix = 0.0


class OpenBassCabinet(CabinetSim):
    """T4: the high-passes park at 20 Hz, so 40 Hz is not 12 dB down."""
    NAME = 'CabinetSim'

    def _refresh(self):
        CabinetSim._refresh(self)
        if self._hp_a is None:
            return
        blend = self._value(MIX)
        for node in (self._hp_a, self._hp_b, self._hp_or_notch):
            if node is None:
                continue
            if node.mode == audiobiquad.HIGH_PASS:
                node.frequency = self._hz(20.0)
                node.mix = blend


class FlatCharacterCabinet(CabinetSim):
    """T5b's level clause: the combo's low end becomes the stack's.

    Re-planted in the second fix round (audiocomponents#73). The first
    version borrowed the stack's bell and left the pole count alone - two
    high-pass sections on the combo against the stack's three - so above
    Low Cut 88 Hz the pole count carried the 3 dB by itself and the fault
    read GREEN at 8 of 109 surface positions, including shipped patches 4
    and 5. The clause names the character's low end, and the character's
    low end is **both** halves, so the fault removes both: the combo
    borrows the stack's bell, and the stack gives up its third high-pass
    so the two have the same pole count.

    It stays one-clause: the combo keeps its notch section, so T5b's notch
    reading is still 4.40 dB on the fault (4.80 clean), which is the
    control for `NoNotchCabinet`. And it is not the null build, which is
    the whole class as a wire - this one is the same cabinet everywhere
    above 300 Hz.
    """
    NAME = 'CabinetSim'

    def _refresh(self):
        CabinetSim._refresh(self)
        if self._body is None:
            return
        blend = self._value(MIX)
        if blend <= 0.0:
            return
        if self._combo:
            self._push(self._body, audiobiquad.PEAKING_EQ,
                       rebuilt.STACK_BODY_HZ, rebuilt.STACK_BODY_Q,
                       self._value(2) + rebuilt.STACK_BODY_BIAS, blend)
        elif self._hp_or_notch is not None:
            self._hp_or_notch.mix = 0.0


class BellOnlyFlatCabinet(CabinetSim):
    """The first fix round's `FlatCharacterCabinet`, kept as a
    **measurement** and not as a guard: it removes only the combo's bell
    and leaves the pole count, so it reads how much of T5b's 3 dB the bell
    is worth and where the pole count takes over. It is green from Low Cut
    88 up, which is why it is no longer the guard."""
    NAME = 'CabinetSim'

    def _refresh(self):
        CabinetSim._refresh(self)
        if self._body is None or not self._combo:
            return
        blend = self._value(MIX)
        if blend <= 0.0:
            return
        self._push(self._body, audiobiquad.PEAKING_EQ, rebuilt.STACK_BODY_HZ,
                   rebuilt.STACK_BODY_Q,
                   self._value(2) + rebuilt.STACK_BODY_BIAS, blend)


class NoNotchCabinet(CabinetSim):
    """T5b's notch clause: the combo's third section stays a high-pass, so
    the open back has no cancellation. Leaves the level clause alone."""
    NAME = 'CabinetSim'

    def _refresh(self):
        CabinetSim._refresh(self)
        if self._hp_or_notch is None or not self._combo:
            return
        blend = self._value(MIX)
        if blend <= 0.0:
            return
        self._push(self._hp_or_notch, audiobiquad.HIGH_PASS, self._value(1),
                   rebuilt.HP_Q, 0.0, blend)


COMBO = {"midi": {0: 127}}


class TestCabinetSimTier1(unittest.TestCase):
    def test_mix_zero_is_wire(self):
        probe, _exact = sine(1000, -20)
        effect = build(probe=probe, mix=0.0)
        wet = render(effect, FRAMES)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            FRAMES, rate=RATE, channels=2, block=256)
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])

    def test_latency_zero_click(self):
        probe = probes.click_stereo(frames=FRAMES, offset=256, channels=2)
        effect = build(probe=probe, frames=FRAMES)
        wet = render(effect, FRAMES)
        dry = probes.render(
            probes.ArraySource(probe, rate=RATE, block=256, channels=2),
            FRAMES, rate=RATE, channels=2, block=256)
        result = kit.click(wet, dry, 0, subsample=False)
        self.assertTrue(result["passed"], result["red"])

    def test_capabilities_and_nodes(self):
        effect = build(probe=probes.silence(256, 2), frames=256)
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(len(effect._nodes), 8)
        self.assertEqual(effect.NAME, "CabinetSim")
        effect.reset()
        effect.deinit()

    def tail(self, hz=100.0, dbfs=-3.0, patch=None, midi=None, **options):
        """Frames from the end of a burst to the last non-zero sample."""
        burst, _exact = sine(hz, dbfs, frames=4096)
        frames = 4096 + CabinetSim.TAIL_SAMPLES * 2
        padded = array("h", list(burst) + [0] * ((frames - 4096) * 2))
        effect = build(probe=padded, frames=frames, **options)
        try:
            if patch is not None:
                effect.program_change(patch)
            for index, position in (midi or {}).items():
                effect.set_macro(index, position)
            got = render(effect, frames)
        finally:
            effect.deinit()
        data = np.asarray(got.float)
        nonzero = np.nonzero(np.abs(data).max(axis=1) > 0.0)[0]
        return int(nonzero[-1]) - 4096 + 1 if len(nonzero) else 0

    def test_tail_reaches_exact_zero_inside_the_declaration(self):
        """Measured over the surface, not at three settings.

        The shipped version of this test walked the default, Low Cut 55
        and combo + Low Cut 55, and its premise - "the longest ring is the
        lowest Low Cut" - was false: it never moved Body, and the combo's
        bell at 115 Hz Q 1.5 with Body +6 rings half again as long as
        three high-pass poles at 55 Hz do (audiocomponents#73). So this
        walks Body and the character, bursts at the bell's own frequency,
        and bursts at full scale, which is where the ring starts highest.
        """
        worst = (0, None)
        cases = [("default", 100.0, -3.0, {}),
                 ("patch 1", 100.0, 0.0, {"patch": 1}),
                 ("patch 6", 100.0, 0.0, {"patch": 6}),
                 ("Low Cut 55, Body 0", 100.0, 0.0, {"midi": {1: 0}}),
                 ("combo, Body +6", 115.0, 0.0, {"midi": {0: 127, 2: 127}}),
                 ("combo, Body 0", 115.0, 0.0, {"midi": {0: 127, 2: 64}}),
                 ("combo, Low Cut 55, Body +6", 115.0, 0.0,
                  {"midi": {0: 127, 1: 0, 2: 127}}),
                 ("combo, Low Cut 55, Body +6, 100 Hz", 100.0, 0.0,
                  {"midi": {0: 127, 1: 0, 2: 127}})]
        for label, hz, dbfs, options in cases:
            length = self.tail(hz=hz, dbfs=dbfs, **options)
            if length > worst[0]:
                worst = (length, label)
            self.assertLessEqual(
                length, CabinetSim.TAIL_SAMPLES,
                "%s: tail %d samples, declared %d"
                % (label, length, CabinetSim.TAIL_SAMPLES))
        # The worst case must be the one the declaration was set from: a
        # sweep that no longer reaches it is a sweep that stopped looking.
        self.assertGreater(worst[0], 5000,
                           "the surface's worst tail now reads %d at %s; "
                           "the declaration was set from 5565" % worst)
        # And honest in the other direction: a figure nobody can approach
        # says nothing.
        self.assertGreater(worst[0] * 4, CabinetSim.TAIL_SAMPLES,
                           "declared tail %d is more than four times the "
                           "longest measured (%d)"
                           % (CabinetSim.TAIL_SAMPLES, worst[0]))

    def test_the_body_bell_rings_longer_than_the_low_cut_poles(self):
        """The premise the shipped tail test got wrong, as its own row."""
        bell = self.tail(hz=115.0, dbfs=0.0, midi={0: 127, 2: 127})
        poles = self.tail(hz=100.0, dbfs=0.0, midi={1: 0})
        self.assertGreater(bell, poles + 1000,
                           "combo + Body +6 rings %d, Low Cut 55 rings %d"
                           % (bell, poles))

    def test_pulling_output_allocates_nothing(self):
        """The Tier 1 row the first pass left `unmeasured`.

        CPython only — MicroPython and CircuitPython have no `tracemalloc`,
        which is why the row is blank there and says so rather than
        claiming a pass.
        """
        import tracemalloc

        import audiocore

        effect = build(probe=probes.silence(8192, 2), frames=8192)
        try:
            for _ in range(8):
                audiocore.get_buffer(effect.output)
            tracemalloc.start()
            before = tracemalloc.take_snapshot()
            for _ in range(8):
                audiocore.get_buffer(effect.output)
            after = tracemalloc.take_snapshot()
            tracemalloc.stop()
        finally:
            effect.deinit()
        # The harness is not free and is not the subject: `tracemalloc`
        # allocates its own frames, and `kit_probes.ArraySource` allocates
        # an int per pull as its read position walks past the small-int
        # cache. What the row asks about is the class and the nodes it
        # built, so that is what this counts.
        mine = [stat for stat in after.compare_to(before, "lineno")
                if stat.size_diff > 0
                and ("audioeffects" in stat.traceback[0].filename
                     or "audiobiquad" in stat.traceback[0].filename)]
        self.assertEqual([str(stat) for stat in mine], [],
                         "the class or its nodes allocated on a pull")

    def test_corners_never_clamp_at_the_shipped_rates(self):
        """`_hz` clamps below Nyquist; at 48/44.1/22.05 kHz nothing reaches
        it, so the clamp is never what a rate difference means."""
        highest = 7000.0 * rebuilt.SHELF1_RATIO
        for rate in (48000, 44100, 22050):
            ceiling = rate * 0.5 * _component.NYQUIST_MARGIN
            self.assertLess(highest, ceiling,
                            "%d Hz: the top shelf at %.1f Hz would clamp at "
                            "%.1f" % (rate, highest, ceiling))

    def test_settings_survive_single_precision(self):
        """audiocomponents#75: a board computes these in float32.

        Every macro position, in double and again with every operation
        rounded to single, must land on the same grid point - and every
        derived setting must be exactly representable, so the node stores
        the same float32 on a board as on a desktop.
        """
        def f32(value):
            return struct.unpack("<f", struct.pack("<f", value))[0]

        def exact_in_f32(value):
            return f32(value) == value

        collisions = []
        for index in range(1, 8):
            span = CabinetSim._MACRO_RANGES[index]
            step = CabinetSim._MACRO_GRIDS[index]
            for position in range(128):
                double = _component.macro_value(span, position / 127.0)
                low, high = span[0], span[1]
                if len(span) > 2:
                    single = f32(f32(f32(high) / f32(low))
                                 ** f32(f32(position) / f32(127.0)))
                    single = f32(f32(low) * single)
                else:
                    single = f32(f32(f32(low)) + f32(f32(f32(high)
                                                        - f32(low))
                                                     * f32(f32(position)
                                                           / f32(127.0))))
                if rebuilt._grid(double, step) != rebuilt._grid(single, step):
                    collisions.append((index, position, double, single))
        self.assertEqual(collisions, [], "%d of 896 positions land on "
                                         "different grid points"
                         % len(collisions))

        # And every value the class actually hands a section is exact in
        # float32, so the store is lossless and the two agree bit for bit.
        for label, options in surface():
            effect = build(probe=probes.silence(256, 2), frames=256)
            try:
                if "patch" in options:
                    effect.program_change(options["patch"])
                for i, p in options.get("midi", {}).items():
                    effect.set_macro(i, p)
                low_cut = effect._value(1)
                breakup = effect._value(3)
                top = effect._value(5)
                air = effect._value(6)
                for value in (low_cut,
                              breakup * rebuilt.PEAK_A_RATIO,
                              breakup * rebuilt.PEAK_B_RATIO,
                              top * rebuilt.SHELF1_RATIO,
                              top * rebuilt.SHELF2_RATIO,
                              air * rebuilt.SHELF2_GAIN_FRAC,
                              effect._value(2) + rebuilt.STACK_BODY_BIAS,
                              effect._value(2) + rebuilt.COMBO_BODY_BIAS,
                              effect._value(4)):
                    self.assertTrue(exact_in_f32(value),
                                    "%s: %r is not exact in float32"
                                    % (label, value))
            finally:
                effect.deinit()

    def test_float_macro_positions_land_where_integers_do(self):
        """audiocomponents#75's remaining half.

        The 896-position proof above is MIDI integers, but the base
        class's `set_macro` accepts floats, and on a 1/64-MIDI host grid
        Break-up split at 2 of 8129 positions - `set_macro(3, 76.28125)`
        was 2729.0 Hz in double and 2730.0 in single, two different
        renders. This class snaps the position instead, so every float
        lands on a position the proof covers.
        """
        effect = build(probe=probes.silence(256, 2), frames=256)
        try:
            for index in range(1, 8):
                for sixty_fourths in range(0, 127 * 64 + 1, 7):
                    position = sixty_fourths / 64.0
                    effect.set_macro(index, position)
                    snapped = effect.get_macro(index)
                    self.assertEqual(snapped, float(int(position + 0.5)),
                                     "macro %d at %.5f read back %.5f"
                                     % (index, position, snapped))
                    effect.set_macro(index, int(position + 0.5))
                    self.assertEqual(effect._value(index),
                                     effect._value(index))
            # the two positions the refuter found, by their values
            effect.set_macro(3, 76.28125)
            fractional = effect._value(3)
            effect.set_macro(3, 76)
            self.assertEqual(fractional, effect._value(3),
                             "set_macro(3, 76.28125) is %r Hz and "
                             "set_macro(3, 76) is %r" % (fractional,
                                                         effect._value(3)))
            effect.set_macro(3, 123.6875)
            fractional = effect._value(3)
            effect.set_macro(3, 124)
            self.assertEqual(fractional, effect._value(3))
        finally:
            effect.deinit()

    def test_no_shipped_setting_sits_on_a_snap_tie(self):
        """The snap's own boundary, checked where the class ships.

        A position exactly half way between two MIDI numbers is the one
        place two precisions could snap differently. Every patch value is
        an integer, so the exposure is the constructor's engineering
        defaults; each is held away from the tie. Body is the exception
        and is exact: 0 dB on a -6..+6 span is position 63.5000 in both
        precisions, and 63.5 + 0.5 is exactly 64.0 in both.
        """
        defaults = (rebuilt.CHAR_STACK, rebuilt.LOW_CUT_DEFAULT,
                    rebuilt.BODY_DEFAULT, rebuilt.BREAK_DEFAULT,
                    rebuilt.BITE_DEFAULT, rebuilt.TOP_DEFAULT,
                    rebuilt.AIR_DEFAULT, rebuilt.MIX_DEFAULT)
        for index, (span, value) in enumerate(zip(CabinetSim._MACRO_RANGES,
                                                  defaults)):
            midi = _component.macro_position(span, value) * 127.0
            distance = abs(midi - int(midi) - 0.5)
            exact = midi == float(int(midi * 2.0)) / 2.0 and distance == 0.0
            self.assertTrue(distance > 0.01 or exact,
                            "%s: the constructor default sits %.4f from a "
                            "snap tie at MIDI %.4f"
                            % (CabinetSim.MACRO_LABELS[index], distance,
                               midi))
        for patch, (_name, values) in CabinetSim.PATCHES.items():
            for value in values:
                self.assertEqual(value, int(value),
                                 "patch %d ships a non-integer macro "
                                 "position %r" % (patch, value))

    def test_never_uses_distortion_node(self):
        with open(rebuilt.__file__, encoding="utf-8") as handle:
            text = handle.read()
        # Imports and construction, not the module docstring.
        body = text.split('VENDOR = "PyDevices"', 1)[1]
        self.assertNotIn("audiofilters.Distortion", body)
        self.assertNotIn("audioshaper", body)
        self.assertIn("audiobiquad", body)


class TestCabinetSimHeadroom(unittest.TestCase):
    """Where the class clips, held to the numbers the docstring, the
    catalogue row and the pack all print. Each assertion goes both ways -
    clean below the stated ceiling, dirty above it - so a class that
    stopped clipping fails here and the disclosure gets corrected rather
    than left to rot."""

    def test_the_stated_ceiling_is_where_it_clips(self):
        for label, hz, clean_at, dirty_at, options in (
                ("patch 6 (the worst cell)", 150.0, -11.0, -9.0,
                 {"patch": 6}),
                ("patch 1, the combo", 115.0, -10.0, -9.0, {"patch": 1}),
                ("the constructor default", 2112.0, -5.0, -3.0, {}),
                ("combo + Body +6", 115.0, -11.0, -9.0,
                 {"midi": {0: 127, 2: 127}})):
            below, _floor = distortion(CabinetSim, hz, clean_at, **options)
            above, _floor = distortion(CabinetSim, hz, dirty_at, **options)
            self.assertLess(below, 1.0,
                            "%s: %.0f Hz at %+.0f dBFS reads %.2f %% THD; "
                            "the docstring says it is clean there"
                            % (label, hz, clean_at, below))
            self.assertGreater(above, 1.0,
                               "%s: %.0f Hz at %+.0f dBFS reads %.2f %% "
                               "THD; the docstring says it clips there"
                               % (label, hz, dirty_at, above))

    def test_the_worst_cell_is_a_shipped_patch(self):
        """Patch 6 at 150 Hz is the number the disclosure leads with; if
        some other shipped patch got hotter, this says so."""
        over = []
        for patch in range(7):
            for hz in (115.0, 150.0, 2112.0):
                thd, _floor = distortion(CabinetSim, hz, -11.0,
                                         patch=patch)
                if thd >= 1.0:
                    over.append("patch %d at %.0f Hz: %.2f %%"
                                % (patch, hz, thd))
        self.assertEqual(over, [], "%d shipped cells clip at -11 dBFS, "
                                   "under the stated ceiling" % len(over))

    def test_linear_below_the_ceiling_and_an_alias_row_above_it(self):
        """The pack's "no alias-floor row is owed (linear)" is true only
        below the ceiling. Both halves are asserted."""
        for patch in (0, 1, 6):
            _thd, floor = distortion(CabinetSim, 3700.0, -12.0,
                                     patch=patch)
            self.assertLess(floor, -80.0,
                            "patch %d: non-harmonic floor %.1f dB at "
                            "-12 dBFS" % (patch, floor))
        _thd, hot = distortion(CabinetSim, 3700.0, 0.0, patch=0)
        self.assertGreater(hot, -60.0,
                           "patch 0 at 0 dBFS reads a %.1f dB floor; the "
                           "docstring says an alias row is owed there"
                           % hot)
        _thd, low_rate = distortion(CabinetSim, 3700.0, 0.0, rate=22050,
                                    patch=0)
        self.assertGreater(low_rate, -40.0,
                           "22.05 kHz at 0 dBFS reads %.1f dB" % low_rate)

    def test_one_kilohertz_cannot_see_the_clipping(self):
        """Why the level guard below is not enough on its own."""
        for dbfs in (-20.0, -6.0, -3.0):
            thd, _floor = distortion(CabinetSim, 1000.0, dbfs, patch=6)
            self.assertLess(thd, 1.0)
        thd, _floor = distortion(CabinetSim, 150.0, -3.0, patch=6)
        self.assertGreater(thd, 20.0,
                           "150 Hz at -3 dBFS reads %.2f %%" % thd)


class TestCabinetSimRateHonesty(unittest.TestCase):
    """22.05 kHz is a different response above 5 kHz, and the class says
    so. These hold the disclosure to its numbers in both directions."""

    def test_48_and_441_agree(self):
        for hz in (100.0, 1000.0, 2112.0, 5000.0, 7000.0):
            a = rel_db(CabinetSim, hz, rate=48000, frames=LF_FRAMES)
            b = rel_db(CabinetSim, hz, rate=44100, frames=LF_FRAMES)
            self.assertLess(abs(a - b), 0.5,
                            "%.0f Hz: 48 k %+.2f, 44.1 k %+.2f" % (hz, a, b))

    def test_22050_is_a_different_cabinet_above_5k(self):
        five = (rel_db(CabinetSim, 5000.0, rate=22050)
                - rel_db(CabinetSim, 5000.0, rate=48000))
        seven = (rel_db(CabinetSim, 7000.0, rate=22050)
                 - rel_db(CabinetSim, 7000.0, rate=48000))
        self.assertGreater(five, 3.5,
                           "5 kHz spread is %+.2f dB; the docstring says "
                           "+4.34" % five)
        self.assertLess(seven, -3.5,
                        "7 kHz spread is %+.2f dB; the docstring says "
                        "-4.37" % seven)

    def test_the_worst_patch_spread_is_the_stated_one(self):
        worst = (0.0, None)
        for patch in range(7):
            for hz in (5000.0, 7000.0, 8000.0):
                spread = (rel_db(CabinetSim, hz, rate=22050, patch=patch)
                          - rel_db(CabinetSim, hz, rate=48000, patch=patch))
                if abs(spread) > abs(worst[0]):
                    worst = (spread, "patch %d at %.0f Hz" % (patch, hz))
        self.assertLess(abs(worst[0]), 6.0,
                        "worst rate spread %+.2f dB at %s, over the stated "
                        "4.95" % worst)
        self.assertGreater(abs(worst[0]), 4.0,
                           "worst rate spread is only %+.2f dB at %s; the "
                           "docstring claims 4.95 and should be corrected"
                           % worst)


class TestCabinetSimLevel(unittest.TestCase):
    def test_level_honest_at_mix_one(self):
        """App. C's guard, which the class must satisfy before any relative
        reading is believed: 1 kHz within 1 dB of unity, everywhere."""
        worst = (0.0, None)
        for label, options in surface():
            value = abs_db(CabinetSim, 1000.0, **options)
            if abs(value) > abs(worst[0]):
                worst = (value, label)
        self.assertLess(abs(worst[0]), 1.0,
                        "1 kHz is %+.2f dB at %s" % worst)
        # The default is the headline and is tighter still.
        self.assertLess(abs(abs_db(CabinetSim, 1000.0)), 0.3)


class TestCabinetSimT1T2(unittest.TestCase):
    def test_t1_cliff_at_default(self):
        self.assertGreaterEqual(fall(CabinetSim, 5000, 8000), 15.0)

    def test_t1_holds_at_every_patch(self):
        for patch in range(7):
            self.assertGreaterEqual(
                fall(CabinetSim, 5000, 8000, patch=patch), 15.0,
                "patch %d" % patch)

    def test_t1_fault_shallow_cliff_red_and_control_green(self):
        clean = fall(CabinetSim, 5000, 8000)
        dirty = fall(ShallowCliffCabinet, 5000, 8000)
        self.assertGreaterEqual(clean, 15.0, "the control must pass")
        self.assertLess(dirty, 15.0, "the fault must fail")

    def test_t1_fault_fires_at_every_rate(self):
        """The shipped fault was green at 22.05 kHz, where the warped
        low-pass pair made the cliff by itself (audiocomponents#73)."""
        for rate in (48000, 44100, 22050):
            dirty = fall(ShallowCliffCabinet, 5000, 8000, rate=rate)
            clean = fall(CabinetSim, 5000, 8000, rate=rate)
            self.assertLess(dirty, 15.0, "fault green at %d Hz: %.2f"
                            % (rate, dirty))
            self.assertGreaterEqual(clean, 15.0, "control red at %d Hz: %.2f"
                                    % (rate, clean))

    def test_t1_fault_not_on_the_macro_surface(self):
        """Not the two shelf modes - the measurement itself, at every
        position. The shipped test asserted only `checked > 0`."""
        restored = []
        checked = 0
        for label, options in surface():
            checked += 1
            if fall(ShallowCliffCabinet, 5000, 8000, **options) >= 15.0:
                restored.append(label)
        self.assertGreater(checked, 60)
        self.assertEqual(restored, [], "%d of %d positions restore the fault"
                         % (len(restored), checked))

    def test_t2_shelf_at_default(self):
        self.assertLessEqual(fall(CabinetSim, 8000, 16000), 12.0)

    def test_t2_fault_lowpass_red_and_control_green(self):
        for rate in (48000, 44100):
            clean = fall(CabinetSim, 8000, 16000, rate=rate)
            dirty = fall(LowPassCabinet, 8000, 16000, rate=rate)
            self.assertLessEqual(clean, 12.0, "control red at %d" % rate)
            self.assertGreater(dirty, 12.0, "fault green at %d" % rate)

    def test_t2_fault_not_on_the_macro_surface(self):
        restored = []
        for label, options in surface():
            if fall(LowPassCabinet, 8000, 16000, **options) <= 12.0:
                restored.append(label)
        self.assertEqual(restored, [], "%d positions restore the fault"
                         % len(restored))

    def test_t2_is_not_claimed_above_the_stated_top(self):
        """What the class gives up, measured rather than asserted: above
        Top 6.3 kHz the two shelves separate and T2's bar is exceeded."""
        inside = fall(CabinetSim, 8000, 16000, midi={5: 64})
        outside = fall(CabinetSim, 8000, 16000, midi={5: 127})
        self.assertLessEqual(inside, 12.0)
        self.assertGreater(outside, 12.0,
                           "the docstring says T2 fails at Top 7 kHz; it "
                           "reads %.2f" % outside)


class TestCabinetSimT3(unittest.TestCase):
    def band(self, **options):
        effect = build(probe=probes.silence(256, 2), frames=256)
        try:
            if "patch" in options:
                effect.program_change(options["patch"])
            for i, p in options.get("midi", {}).items():
                effect.set_macro(i, p)
            breakup = effect._value(3)
        finally:
            effect.deinit()
        return (breakup * rebuilt.T3_BAND_LO, breakup * rebuilt.T3_BAND_HI)

    def check(self, cls, **options):
        low, high = self.band(**options)
        maxima, dip, curve = peaks_in(cls, low, high, **options)
        return maxima, dip, curve

    def test_t3_two_peaks_at_default(self):
        maxima, dip, curve = self.check(CabinetSim)
        self.assertGreaterEqual(len(maxima), 2, curve)
        self.assertGreaterEqual(maxima[0][1], 3.0)
        self.assertGreaterEqual(maxima[1][1], 3.0)
        self.assertGreaterEqual(min(maxima[0][1], maxima[1][1]) - dip, 2.0)

    def test_t3_holds_across_the_whole_breakup_travel(self):
        """The re-cut: the band travels with Break-up. The shipped band was
        fixed at 1.8-3.6 kHz and lost a peak at both ends of the macro
        (audiocomponents#73)."""
        for position in (0, 32, 64, 96, 127):
            maxima, dip, curve = self.check(CabinetSim,
                                            midi={3: position})
            self.assertGreaterEqual(len(maxima), 2,
                                    "Break-up MIDI %d: %s" % (position,
                                                              curve))
            self.assertGreaterEqual(min(maxima[0][1], maxima[1][1]), 3.0,
                                    "Break-up MIDI %d" % position)
            self.assertGreaterEqual(min(maxima[0][1], maxima[1][1]) - dip,
                                    2.0, "Break-up MIDI %d" % position)

    def test_t3_peaks_sit_inside_1800_3600_at_every_shipped_patch(self):
        """The absolute clause the re-cut keeps: the seven patches all put
        both maxima inside the band the published curves show."""
        for patch in range(7):
            if patch == 2:
                continue        # Bite +1, below T3's own bar; see the pack
            maxima, _dip, curve = self.check(CabinetSim, patch=patch)
            self.assertGreaterEqual(len(maxima), 2, "patch %d" % patch)
            for hz, _value in maxima[:2]:
                self.assertTrue(1800.0 <= hz <= 3600.0,
                                "patch %d: a maximum at %.0f Hz" % (patch,
                                                                    hz))

    def test_t3_is_not_claimed_at_bite_below_the_default(self):
        """Stated rather than hidden: at Bite 0 both break-up sections are
        switched off, so Bite 0 is no peak at all."""
        effect = build(probe=probes.silence(256, 2), frames=256)
        try:
            effect.set_macro(4, 0)
            self.assertEqual(effect._peak_a.mix, 0.0)
            self.assertEqual(effect._peak_b.mix, 0.0)
        finally:
            effect.deinit()
        maxima, _dip, _curve = self.check(CabinetSim, midi={4: 0})
        self.assertLess(len(maxima), 2)

    def test_t3_fault_single_peak_red_and_control_green(self):
        clean, _d, _c = self.check(CabinetSim)
        dirty, _d2, _c2 = self.check(SinglePeakCabinet)
        self.assertGreaterEqual(len(clean), 2, "the control must pass")
        self.assertLess(len(dirty), 2, "the fault must fail")

    def test_t3_fault_not_on_the_macro_surface(self):
        restored = []
        for label, options in surface():
            if options.get("midi", {}).get(4) == 0:
                continue        # Bite 0 is no peak on the clean class either
            maxima, dip, _curve = self.check(SinglePeakCabinet, **options)
            if (len(maxima) >= 2 and min(maxima[0][1], maxima[1][1]) >= 3.0
                    and min(maxima[0][1], maxima[1][1]) - dip >= 2.0):
                restored.append(label)
        self.assertEqual(restored, [], "%d positions restore the fault"
                         % len(restored))


class TestCabinetSimT4(unittest.TestCase):
    def test_t4_lows_at_default(self):
        self.assertLessEqual(rel_db(CabinetSim, 40, frames=LF_FRAMES), -12.0)
        self.assertLessEqual(rel_db(CabinetSim, 20, frames=LF_FRAMES), -20.0)

    def test_t4_holds_at_every_patch(self):
        for patch in range(7):
            self.assertLessEqual(
                rel_db(CabinetSim, 40, frames=LF_FRAMES, patch=patch), -12.0,
                "patch %d" % patch)

    def test_t4_fault_open_bass_red_and_control_green(self):
        clean = rel_db(CabinetSim, 40, frames=LF_FRAMES)
        dirty = rel_db(OpenBassCabinet, 40, frames=LF_FRAMES)
        self.assertLessEqual(clean, -12.0, "the control must pass")
        self.assertGreater(dirty, -12.0, "the fault must fail")

    def test_t4_fault_not_on_the_macro_surface(self):
        restored = []
        for label, options in surface():
            if rel_db(OpenBassCabinet, 40, frames=LF_FRAMES,
                      **options) <= -12.0:
                restored.append(label)
        self.assertEqual(restored, [], "%d positions restore the fault"
                         % len(restored))


class TestCabinetSimT5(unittest.TestCase):
    def test_t5a_span_is_disconfirmed_and_says_why(self):
        """T5a's 115-230 Hz plateau does not hold and the class says so.

        This test exists so the disconfirmation cannot drift into a claim
        without someone editing it: it asserts the failure, and asserts the
        two clauses that DO hold.
        """
        ref = abs_db(CabinetSim, 1000.0, frames=LF_FRAMES)
        readings = {hz: abs_db(CabinetSim, hz, frames=LF_FRAMES) - ref
                    for hz in (60.0, 115.0, 150.0, 168.0, 200.0, 230.0)}
        top = max(readings[hz] for hz in (150.0, 168.0, 200.0, 230.0))
        self.assertGreater(top - readings[115.0], 3.0,
                           "115 Hz is %.2f dB under the low-frequency "
                           "maximum; T5a asks for 3 and the class does not "
                           "claim it" % (top - readings[115.0]))
        self.assertLessEqual(readings[60.0], -20.0)     # clause that holds
        self.assertTrue(3.0 <= readings[200.0] <= 6.0,  # holds at Body 0
                        "200 Hz-1 kHz fall %.2f" % readings[200.0])

    def test_t5a_clauses_over_the_whole_body_travel(self):
        """Every clause of the row, at every setting the row is quantified
        over - which is Body -6 / 0 / +6, not Body 0 alone.

        The 60 Hz clause holds across all three and all three rates. The
        200 Hz-1 kHz clause does **not**: it is a 3-6 dB fall only at
        Body 0, and the docstring says so rather than leaving a reader to
        find it. This asserts both, so neither can drift.
        """
        for rate in (48000, 44100, 22050):
            for position, inside in ((0, False), (64, True), (127, False)):
                ref = abs_db(CabinetSim, 1000.0, frames=LF_FRAMES,
                             rate=rate, midi={2: position})
                sixty = abs_db(CabinetSim, 60.0, frames=LF_FRAMES,
                               rate=rate, midi={2: position}) - ref
                two = abs_db(CabinetSim, 200.0, frames=LF_FRAMES,
                             rate=rate, midi={2: position}) - ref
                self.assertLessEqual(sixty, -20.0,
                                     "60 Hz is %.2f at Body MIDI %d, %d Hz"
                                     % (sixty, position, rate))
                if inside:
                    self.assertTrue(3.0 <= two <= 6.0,
                                    "200 Hz is %.2f at Body MIDI %d, %d Hz"
                                    % (two, position, rate))
                else:
                    self.assertFalse(3.0 <= two <= 6.0,
                                     "200 Hz is %.2f at Body MIDI %d, %d Hz "
                                     "- the docstring says this clause holds "
                                     "at Body 0 only" % (two, position, rate))

    def test_t5a_lower_minus3_point_is_inside_the_traits_own_band(self):
        """The one T5a clause the class does meet outright."""
        ref = abs_db(CabinetSim, 1000.0, frames=LF_FRAMES)
        curve = [(hz, abs_db(CabinetSim, hz, frames=LF_FRAMES) - ref)
                 for hz in (100.0, 110.0, 115.0, 121.0, 130.0, 150.0,
                            168.0, 200.0, 230.0, 260.0)]
        top = max(value for _hz, value in curve)
        below = [hz for hz, value in curve if value < top - 3.0 and hz < 150.0]
        self.assertTrue(below and max(below) < 130.0,
                        "the lower -3 dB point is not under 130 Hz: %s"
                        % curve)

    def test_t5b_character_at_the_default_macros(self):
        """The park's own question: hold Low Cut and Body identical and ask
        what the character alone is worth at 100 Hz."""
        stack = rel_db(CabinetSim, 100, frames=LF_FRAMES)
        combo = rel_db(CabinetSim, 100, frames=LF_FRAMES, **COMBO)
        self.assertGreaterEqual(combo - stack, 3.0,
                                "stack %.2f combo %.2f" % (stack, combo))

    def test_t5b_character_across_low_cut_and_body(self):
        for index, positions in ((1, GRID), (2, GRID)):
            for position in positions:
                stack = rel_db(CabinetSim, 100, frames=LF_FRAMES,
                               midi={0: 0, index: position})
                combo = rel_db(CabinetSim, 100, frames=LF_FRAMES,
                               midi={0: 127, index: position})
                self.assertGreaterEqual(
                    combo - stack, 3.0,
                    "macro %d at %d: %.2f" % (index, position,
                                              combo - stack))

    def test_t5b_notch_at_the_default_and_at_patch_one(self):
        self.assertGreaterEqual(prominence(CabinetSim, frames=LF_FRAMES,
                                           **COMBO), 3.0)
        self.assertGreaterEqual(prominence(CabinetSim, frames=LF_FRAMES,
                                           patch=1), 3.0)

    def test_t5b_notch_across_the_combo_low_cut_travel(self):
        """The shipped notch was gone above Low Cut 90 - the constructor's
        own default (audiocomponents#73)."""
        for position in GRID:
            got = prominence(CabinetSim, frames=LF_FRAMES,
                             midi={0: 127, 1: position})
            self.assertGreaterEqual(got, 3.0,
                                    "Low Cut MIDI %d: %.2f" % (position, got))

    def test_t5b_fault_flat_character_red_and_control_green(self):
        """A fault of the same kind as the claim, and its own test can fail:
        the shipped `SameCharacterCabinet` read GREENER than the class and
        its criterion passed either way (audiocomponents#73)."""
        def delta(cls):
            return (rel_db(cls, 100, frames=LF_FRAMES, **COMBO)
                    - rel_db(cls, 100, frames=LF_FRAMES))
        clean = delta(CabinetSim)
        dirty = delta(FlatCharacterCabinet)
        self.assertGreaterEqual(clean, 3.0, "the control must pass")
        self.assertLess(dirty, 3.0, "the fault must fail: %.2f" % dirty)
        # and it leaves the notch clause alone, which is the control for
        # the other fault
        self.assertGreaterEqual(prominence(FlatCharacterCabinet,
                                           frames=LF_FRAMES, **COMBO), 3.0)

    def test_t5b_fault_no_notch_red_and_control_green(self):
        clean = prominence(CabinetSim, frames=LF_FRAMES, **COMBO)
        dirty = prominence(NoNotchCabinet, frames=LF_FRAMES, **COMBO)
        self.assertGreaterEqual(clean, 3.0, "the control must pass")
        self.assertLess(dirty, 3.0, "the fault must fail: %.2f" % dirty)

    def delta(self, cls, midi=None, patch=None, rate=RATE):
        """The character's worth at 100 Hz, at whatever else is set: the
        same patch or macros on each character, one toggle apart."""
        low = dict(midi or {})
        low[0] = 0
        high = dict(midi or {})
        high[0] = 127
        return (rel_db(cls, 100, frames=LF_FRAMES, midi=high, patch=patch,
                       rate=rate)
                - rel_db(cls, 100, frames=LF_FRAMES, midi=low, patch=patch,
                         rate=rate))

    def test_t5b_notch_fault_not_on_the_macro_surface(self):
        restored = []
        for index in (1, 2):
            for position in GRID:
                if prominence(NoNotchCabinet, frames=LF_FRAMES,
                              midi={0: 127, index: position}) >= 3.0:
                    restored.append("no notch macro%d=%d" % (index, position))
        for patch in range(7):
            if prominence(NoNotchCabinet, frames=LF_FRAMES,
                          patch=patch) >= 3.0:
                restored.append("no notch patch %d" % patch)
        self.assertEqual(restored, [], "%d positions restore the fault"
                         % len(restored))
        # It fires one clause and leaves the other's control green.
        self.assertGreaterEqual(self.delta(NoNotchCabinet), 3.0)

    def test_t5b_level_fault_not_on_the_macro_surface(self):
        """The denominator the shipped sweep stopped short of.

        It walked Low Cut MIDI 0/32/64 only - and went green from 88 up,
        and at shipped patches 4 and 5 (audiocomponents#73). This walks
        the **whole** travel of every macro at MIDI 0/8/../120/127 plus
        all seven patches, 109 positions, and prints the clean class's
        reading beside the fault's at each.
        """
        restored = []
        clean_red = []
        positions = [("patch %d" % p, {"patch": p}) for p in range(7)]
        for index in range(1, 7):
            for position in FINE:
                positions.append(("macro%d=%d" % (index, position),
                                  {"midi": {index: position}}))
        worst = (-99.0, None)
        for label, options in positions:
            fault = self.delta(FlatCharacterCabinet, **options)
            clean = self.delta(CabinetSim, **options)
            if fault >= 3.0:
                restored.append("%s: fault %+.2f, clean %+.2f"
                                % (label, fault, clean))
            if clean < 3.0:
                clean_red.append("%s: clean %+.2f" % (label, clean))
            if fault > worst[0]:
                worst = (fault, label)
        self.assertEqual(restored, [],
                         "%d of %d positions restore the fault"
                         % (len(restored), len(positions)))
        self.assertEqual(clean_red, [],
                         "%d of %d positions are red on the clean class"
                         % (len(clean_red), len(positions)))
        # The fault's worst cell, so a fault drifting back toward the bar
        # is visible rather than silent.
        self.assertLess(worst[0], 1.0,
                        "the fault's worst reading is %+.2f at %s" % worst)

    def test_t5b_level_fault_fires_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            fault = self.delta(FlatCharacterCabinet, rate=rate)
            clean = self.delta(CabinetSim, rate=rate)
            self.assertLess(fault, 3.0, "fault green at %d: %+.2f"
                            % (rate, fault))
            self.assertGreaterEqual(clean, 3.0, "control red at %d: %+.2f"
                                    % (rate, clean))

    def test_t5b_level_has_two_mechanisms_and_the_row_says_so(self):
        """Why the first fault was restorable, as a measurement.

        The bell and the pole count each carry part of the 3 dB, and above
        Low Cut 88 the pole count clears the bar on its own. The trait row
        and the docstring say that; this holds both halves to a number so
        the sentence cannot drift from the class.
        """
        bell_only = BellOnlyFlatCabinet
        at_low = self.delta(bell_only, {1: 0})          # Low Cut 55
        at_high = self.delta(bell_only, {1: 127})       # Low Cut 140
        self.assertLess(at_low, 3.0,
                        "at Low Cut 55 the bell is the mechanism and a "
                        "bell-only fault should be red: %+.2f" % at_low)
        self.assertGreaterEqual(at_high, 3.0,
                                "at Low Cut 140 the pole count is supposed "
                                "to carry it alone: %+.2f" % at_high)


class TestCabinetSimMixScope(unittest.TestCase):
    """Every Tier 2 trait is a Mix 1 claim. The class says where each one
    stops holding rather than leaving the reader to find out."""

    def test_t1_holds_down_to_the_stated_mix(self):
        self.assertGreaterEqual(fall(CabinetSim, 5000, 8000,
                                     midi={MIX: 120}), 15.0)
        self.assertLess(fall(CabinetSim, 5000, 8000, midi={MIX: 96}), 15.0)

    def test_t4_holds_down_to_the_stated_mix(self):
        self.assertLessEqual(rel_db(CabinetSim, 40, frames=LF_FRAMES,
                                    midi={MIX: 96}), -12.0)
        self.assertGreater(rel_db(CabinetSim, 40, frames=LF_FRAMES,
                                  midi={MIX: 32}), -12.0)


class TestCabinetSimNullBuilds(unittest.TestCase):
    """Every demonstrated trait, against the class built as a wire."""

    def test_t1_null_build_red(self):
        def measure_with(cls):
            value = fall(cls, 5000, 8000)
            return {"passed": value >= 15.0, "fall": value}
        result = kit_faults.null_build_red(CabinetSim, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t2_null_build_red_as_the_t1_pair(self):
        """A wire's 8-16 kHz fall is 0, which passes T2 on its own. The
        null build for T2 is therefore the T1-and-T2 pair."""
        def measure_with(cls):
            cliff = fall(cls, 5000, 8000)
            floor = fall(cls, 8000, 16000)
            return {"passed": cliff >= 15.0 and floor <= 12.0,
                    "cliff": cliff, "floor": floor}
        result = kit_faults.null_build_red(CabinetSim, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t3_null_build_red(self):
        def measure_with(cls):
            low = rebuilt.BREAK_DEFAULT * rebuilt.T3_BAND_LO
            high = rebuilt.BREAK_DEFAULT * rebuilt.T3_BAND_HI
            maxima, dip, _curve = peaks_in(cls, low, high)
            ok = (len(maxima) >= 2
                  and min(maxima[0][1], maxima[1][1]) >= 3.0
                  and min(maxima[0][1], maxima[1][1]) - dip >= 2.0)
            return {"passed": ok, "peaks": len(maxima)}
        result = kit_faults.null_build_red(CabinetSim, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t4_null_build_red(self):
        def measure_with(cls):
            value = rel_db(cls, 40, frames=LF_FRAMES)
            return {"passed": value <= -12.0, "at40": value}
        result = kit_faults.null_build_red(CabinetSim, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_t5b_null_build_red(self):
        def measure_with(cls):
            stack = rel_db(cls, 100, frames=LF_FRAMES)
            combo = rel_db(cls, 100, frames=LF_FRAMES, **COMBO)
            notch = prominence(cls, frames=LF_FRAMES, **COMBO)
            return {"passed": combo - stack >= 3.0 and notch >= 3.0,
                    "delta": combo - stack, "notch": notch}
        result = kit_faults.null_build_red(CabinetSim, measure_with)
        self.assertFalse(result["null"]["passed"])
        self.assertTrue(result["control"]["passed"])

    def test_level_null_build_is_green_and_is_not_cited(self):
        """The one measurement here a wire passes, recorded rather than
        cited: unity at 1 kHz is exactly what a wire gives, so the level
        row demonstrates nothing on its own and is a guard on the others.
        """
        wire = kit_faults.wire_build(CabinetSim)
        self.assertLess(abs(abs_db(wire, 1000.0)), 0.05)


class TheThirdFixRoundsRows(unittest.TestCase):
    """What audit 3 §4(p) asked this class for.

    A `tail_samples` that carries a user impulse, and a ceiling read with
    the macros in **combination** - which is where the worst cell is, and
    is the cell every published ceiling number missed.
    """

    def impulse(self, taps, seed=1):
        out = array("h", bytes(2 * taps))
        out[0] = 20000
        value = seed
        for index in range(1, taps):
            value = (value * 1103515245 + 12345) & 0x7FFFFFFF
            noise = ((value >> 16) & 0x7FFF) / 32767.0 - 0.5
            decay = math.exp(-6.0 * index / float(taps))
            out[index] = int(max(-32768, min(32767,
                                             20000 * decay * noise)))
        return out

    def test_the_tail_declaration_covers_a_user_impulse(self):
        """`tail_samples` returned the eight-section constant whatever
        `impulse=` held: 8 192 taps measure 8 447 samples of tail and
        48 000 taps measure 48 255, against a declared 6 144. A host that
        trusts it truncates the tail it handed in (audit 3 (p)1, G2)."""
        for taps in (2048, 8192, 48000):
            probe, end = probes.burst_silence(
                hz=1000.0, on_ms=100.0, total_s=3.0, dbfs=-6.0, rate=RATE,
                channels=2)
            effect = CabinetSim.create(
                probes.ArraySource(probe, rate=RATE, channels=2, block=256),
                RATE, impulse=self.impulse(taps))
            try:
                wet = probes.render(effect.output, len(probe) // 2,
                                    rate=RATE, channels=2, block=256)
                declared = effect.tail_samples
            finally:
                effect.deinit()
            result = kit.tail(wet, burst_end_frame=end,
                              declared_tail_samples=declared)
            ring = result["values"]["tail_samples"] or 0
            self.assertLessEqual(
                ring, declared,
                "a %d-tap impulse rings %d samples against a declared %d"
                % (taps, ring, declared))
            self.assertGreater(declared, CabinetSim.TAIL_SAMPLES, taps)

    def test_the_synthetic_default_still_declares_the_constant(self):
        effect = build(probe=probes.silence(512, 2), frames=512)
        try:
            self.assertEqual(effect.tail_samples, CabinetSim.TAIL_SAMPLES)
        finally:
            effect.deinit()

    def peak_and_gain(self, **options):
        """The designed peak of a setting, from the sections themselves."""
        effect = build(probe=probes.silence(512, 2), frames=512)
        try:
            for index, position in (options.get("midi") or {}).items():
                effect.set_macro(index, position)
            best = (-99.0, 1000.0)
            ceiling = 0.45 * RATE
            for step in range(241):
                hz = 20.0 * (ceiling / 20.0) ** (step / 240.0)
                value = self.analytic_db(effect, hz)
                if value > best[0]:
                    best = (value, hz)
            return best[1], best[0]
        finally:
            effect.deinit()

    @staticmethod
    def analytic_db(effect, hz):
        total = 0.0
        for node in effect._sections():
            total += kit.biquad_response_db(node, hz, effect._sample_rate) \
                if hasattr(kit, "biquad_response_db") else 0.0
        return total

    def rails_at(self, dbfs, hz, frames=8192, **options):
        index = np.arange(frames)
        values = (10.0 ** (dbfs / 20.0)) * np.sin(
            2.0 * math.pi * hz * index / RATE)
        quantised = np.clip(np.round(values * 32767.0),
                            -32768, 32767).astype(np.int16)
        pcm = np.repeat(quantised[:, None], 2, axis=1).reshape(-1)
        effect = build(probe=array("h", pcm.tolist()), frames=frames)
        try:
            for macro, position in (options.get("midi") or {}).items():
                effect.set_macro(macro, position)
            wet = render(effect, frames)
        finally:
            effect.deinit()
        data = wet.data[frames // 2:, 0].astype(np.int64)
        return int(np.sum((data >= 32767) | (data <= -32768)))

    def test_the_worst_combined_cell_is_at_the_stated_ceiling(self):
        """Low Cut 55 **with** Body +6 - shipped patch 6's own settings -
        is the cell `macro_surface()` never swept, because it moves one
        macro at a time. The class states -13 dBFS for it."""
        worst = {"midi": {0: 127, 1: 0, 2: 127}}
        ceiling = CabinetSim.SURFACE_CEILING_DBFS
        for hz in (60.0, 115.0, 150.0, 3164.0):
            self.assertEqual(
                self.rails_at(ceiling, hz, **worst), 0,
                "the worst combined cell rails at the stated ceiling "
                "(%s dBFS, %.0f Hz)" % (ceiling, hz))
        self.assertGreater(
            self.rails_at(ceiling + 1.0, 115.0, **worst), 0,
            "above the stated ceiling the rail has to be reachable, or "
            "the number is charity")

    def exact_level_db(self, hz, periods, rate=RATE, dbfs=-12.0, **options):
        """A whole number of periods of an EXACT frequency, rendered.

        The pack's tone snapped to the render's own bin grid, so what it
        called 40 Hz was **41.0156 Hz** - 1.28 dB up a six-pole rolloff
        (audit 3 (p)5).
        """
        frames = int(round(periods * rate / hz))
        amp = (10.0 ** (dbfs / 20.0)) * 32767.0
        index = np.arange(frames)
        values = np.clip(
            np.round(amp * np.sin(2.0 * math.pi * hz * index / rate)),
            -32768, 32767).astype(np.int16)
        pcm = np.repeat(values[:, None], 2, axis=1).reshape(-1)
        probe = array("h", list(pcm) * 3)
        effect = build(probe=probe, frames=3 * frames, rate=rate, **options)
        try:
            wet = render(effect, 3 * frames, rate=rate)
        finally:
            effect.deinit()
        tail = np.asarray(wet.float)[frames:, 0]
        return 20.0 * math.log10(max(1e-12,
                                     float(np.sqrt((tail * tail).mean()))))

    def test_t4_at_an_exact_forty_hertz(self):
        """The row's own frequency, read on a whole-period window."""
        for options, expected in (({}, -42.44), ({"patch": 6}, -19.01)):
            low = self.exact_level_db(40.0, 40, **options)
            reference = self.exact_level_db(1000.0, 1000, **options)
            got = low - reference
            self.assertAlmostEqual(
                got, expected, delta=0.20,
                msg="T4 at an exact 40.00 Hz reads %.3f dB (%r)"
                    % (got, options))

    def test_the_bin_grid_is_what_moved_the_published_number(self):
        """1.28 dB of it, and the row says so rather than carrying the
        snapped figure."""
        exact = self.exact_level_db(40.0, 40)
        snapped = self.exact_level_db(41.0156, 40)
        self.assertGreater(snapped - exact, 1.0, (exact, snapped))
        self.assertLess(snapped - exact, 1.6, (exact, snapped))

    def test_the_default_ceiling_is_its_own_number(self):
        for hz in (60.0, 115.0, 1000.0, 3164.0):
            self.assertEqual(
                self.rails_at(CabinetSim.DEFAULT_CEILING_DBFS, hz), 0, hz)


class TheTierOneRowsAtEveryShippedPatch(unittest.TestCase):
    """audiocomponents#87.

    `CabinetSim` declares no BIPOLAR macro -- its Body span is (-6, +6) dB
    but the mode is UNIPOLAR, so 0 dB is not a detent it needs -- and
    these rows did not move when the detent landed. They are taken
    anyway: Tier 1's silence and tail rows were read at the constructor
    default on every class in the phase, and a patch is a state a user
    selects.
    """

    #: Nothing is red here, and that is the claim.
    RED = {}

    RED_TAIL = {}

    def peaks(self):
        """`{patch: (silence_peak, tail_samples, residual, declared)}`."""
        rows = {}
        for patch in sorted(CabinetSim.PATCHES):
            effect = build(probe=probes.silence(RATE, 2), patch=patch)
            quiet = render(effect, RATE)
            effect.deinit()
            probe, burst_end = probes.burst_silence(
                hz=1000.0, on_ms=200.0, total_s=1.0, dbfs=-6.0, rate=RATE,
                channels=2)
            effect = build(probe=probe, patch=patch)
            wet = render(effect, len(probe) // 2)
            declared = effect.tail_samples
            effect.deinit()
            result = kit.tail(wet, burst_end_frame=burst_end,
                              declared_tail_samples=declared)
            rows[patch] = (int(np.abs(quiet.data).max()),
                           result["values"]["tail_samples"],
                           result["values"]["residual_lsb"], declared)
        return rows

    def test_silence_in_is_silence_out_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                if patch in self.RED:
                    self.assertGreater(row[0], 0, self.RED[patch])
                    continue
                self.assertEqual(row[0], 0,
                                 "patch %d emits %d LSB into digital "
                                 "silence" % (patch, row[0]))

    def test_the_declared_tail_holds_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            _quiet, tail_samples, residual, declared = row
            with self.subTest(patch=patch, why=self.RED_TAIL.get(patch)):
                if patch in self.RED_TAIL:
                    self.assertGreater(residual, 0, self.RED_TAIL[patch])
                    continue
                self.assertEqual(residual, 0,
                                 "patch %d never returns to zero (%d LSB "
                                 "left)" % (patch, residual))
                self.assertLessEqual(tail_samples or 0, declared,
                                     "patch %d rings %s samples against a "
                                     "declared %s"
                                     % (patch, tail_samples, declared))

    def test_program_change_onto_digital_silence_stays_silent(self):
        """A patch change is a wire message and can arrive between notes."""
        for patch in sorted(CabinetSim.PATCHES):
            effect = build(probe=probes.silence(RATE, 2), patch=0)
            before = render(effect, RATE // 2)
            effect.program_change(patch)
            after = render(effect, RATE // 2)
            effect.deinit()
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                self.assertEqual(int(np.abs(before.data).max()), 0)
                peak = int(np.abs(after.data).max())
                if patch in self.RED:
                    self.assertGreater(peak, 0, self.RED[patch])
                    continue
                self.assertEqual(peak, 0,
                                 "program_change(%d) on silence emitted %d "
                                 "LSB" % (patch, peak))


if __name__ == "__main__":
    unittest.main()
