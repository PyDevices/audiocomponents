"""`ConvolutionReverb`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/ConvolutionReverb.md`
(frozen at anchor 85cc2bf); its Tier 2 rows are D1-D6. Each row here is the
measurement over a slice of the span the row quantifies over, the same
measurement red on the row's planted fault at the constructor defaults
(D1's at the measured-mode defaults), the fault shown out of reach of every
macro position and shipped patch, and the measurement red on the class
built as a wire (D2: on the class with its checks removed, since the wire
keeps the class's raise). Exhaustive spans and rates live in the evidence
pack, not in this file.

Every measurement here computes its reference itself - D1's direct sum and
its load gain, D5's Decay law - and never reads it back from the class.
The M1 reference uses numpy and runs on CPython only.
"""

import os
import sys
import tempfile
import unittest
import wave
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audioconvolve                                        # noqa: E402
import audiocore                                            # noqa: E402
import kit_faults                                           # noqa: E402
import kit_probes as probes                                 # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects.rebuilt import convolutionreverb as rebuilt  # noqa: E402

VENDOR = "PyDevices"

ConvolutionReverb = rebuilt.ConvolutionReverb
NAME = "ConvolutionReverb"
RATE = 48000
RATES = (48000, 44100, 22050)
LATENCY = 256
DECAY_I, DAMPING_I, PREDELAY_I, DIFFUSION_I, ROOM_I, MIX_I = range(6)
GRID = tuple(range(0, 128, 8)) + (127,)

#: The constructor's defaults as positions, computed here from section 6
#: (Damping 6 kHz on the 500 Hz-7.5 kHz log law).
DEFAULT_POS = (1.0, float(np.log(12.0) / np.log(15.0)), 0.0, 0.5, 0.0, 0.3)


# --------------------------------------------------------------------------
# Material, rendering, and the laws computed independently of the class
# --------------------------------------------------------------------------

def silence(frames, channels=2):
    return np.zeros((frames, channels), dtype=np.int16)


def click(frames, channels=2, value=32767, at=0):
    pcm = silence(frames, channels)
    pcm[at, :] = value
    return pcm


def white(frames, channels=2, peak_dbfs=-12.0, seed=12345):
    rng = np.random.RandomState(seed)
    peak = 32767.0 * 10 ** (peak_dbfs / 20.0)
    return np.round(rng.uniform(-1, 1, (frames, channels)) * peak).astype(
        np.int16)


def alt_fs(frames, channels=2):
    pcm = np.empty((frames, channels), dtype=np.int16)
    pcm[0::2] = 32767
    pcm[1::2] = -32768
    return pcm


def ramp_fs(channels=2):
    """Every int16 value in turn, in every channel."""
    values = (np.arange(65536) - 32768).astype(np.int16)
    return np.repeat(values[:, None], channels, axis=1)


def switchable(channels=2, rate=RATE):
    return probes.SwitchableSource(
        probes.ArraySource(silence(256, channels), rate=rate,
                           channels=channels))


def build(cls=None, rate=RATE, channels=2, **options):
    """`cls` around a SwitchableSource, so `run` can hand it any material."""
    cls = cls or ConvolutionReverb
    return cls(switchable(channels, rate), sample_rate=rate, **options)


def run(effect, pcm, frames=None):
    """Swap `pcm` in behind `effect`, empty the node, pull `frames` frames
    (default: len(pcm)) and return them as (frames, channels) int16."""
    channels = effect.channel_count
    pcm = np.asarray(pcm, dtype=np.int16).reshape(-1, channels)
    total = pcm.shape[0] if frames is None else frames
    if pcm.shape[0] < total:
        pcm = np.vstack([pcm, silence(total - pcm.shape[0], channels)])
    effect._source.swap(probes.ArraySource(pcm, rate=effect.sample_rate,
                                           channels=channels))
    audiocore.reset_buffer(effect.node)
    out = bytearray()
    want = total * channels * 2
    while len(out) < want:
        data = bytes(audiocore.get_buffer(effect.output)[1])
        if not data:
            break
        out += data
    return np.frombuffer(bytes(out[:want]), dtype=np.int16).reshape(
        -1, channels)


def at_mix(effect, midi, pcm, frames=None):
    """Render at Mix `midi`, then put Mix back where it was."""
    before = effect.get_macro(MIX_I)
    effect.set_macro(MIX_I, midi)
    try:
        return run(effect, pcm, frames)
    finally:
        effect.set_macro(MIX_I, before)


def digest(pcm):
    return np.asarray(pcm, dtype=np.int16).tobytes()


def first_arrival(out):
    hits = np.nonzero(np.any(out != 0, axis=1))[0]
    return int(hits[0]) if len(hits) else None


def law_t60(decay_pos, predelay_pos, seconds):
    """Section 6: T60 = 50 ms * ((S - P) / 50 ms) ** position."""
    predelay = predelay_pos * min(200.0, (seconds - 0.05) * 1000.0 / 2.0)
    room = seconds - predelay / 1000.0
    return 0.05 * (room / 0.05) ** decay_pos


def schroeder_t60(energy, rate):
    """T60 from the Schroeder curve of `energy`, fit over -5..-35 dB and
    extrapolated to -60 dB; None when the fit region is empty."""
    e = np.asarray(energy, dtype=np.float64)
    if not np.any(e):
        return None
    edc = np.cumsum(e[::-1])[::-1]
    edc_db = 10 * np.log10(edc / edc[0] + 1e-300)
    idx = np.where((edc_db <= -5.0) & (edc_db >= -35.0))[0]
    if len(idx) < 2:
        return None
    slope, _ = np.polyfit(idx / float(rate), edc_db[idx], 1)
    return -60.0 / slope


def m5_cell(effect):
    """(fitted T60 or None, floor clean): a 0 dBFS click at Mix 2, L^2+R^2."""
    taps = effect.node.taps
    out = at_mix(effect, 127, click(LATENCY + taps + 1024, 2))
    ir = out[LATENCY:LATENCY + taps].astype(np.float64)
    t60 = schroeder_t60(np.sum(ir ** 2, axis=1), effect.sample_rate)
    return t60, not np.any(out[LATENCY + taps:])


def m4_verdict(out, pcm, latency):
    head = not np.any(out[:latency])
    same = digest(out[latency:]) == digest(pcm[:len(pcm) - latency])
    return head and same


def m4(effect, pcm):
    return m4_verdict(at_mix(effect, 0, pcm), pcm, effect.latency_samples)


def fftconv(x, h):
    n = len(x) + len(h) - 1
    size = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size),
                        size)[:len(x)]


def rho(out, pcm, lags):
    worst = 0.0
    n = len(out)
    size = 1 << (2 * n - 1).bit_length()
    for c in range(out.shape[1]):
        y = out[:, c].astype(np.float64)
        x = pcm[:n, c].astype(np.float64)
        r = np.fft.irfft(np.fft.rfft(y, size) * np.conj(np.fft.rfft(x, size)),
                         size)[:lags + 1]
        den = np.sqrt(np.sum(y * y) * np.sum(x * x))
        worst = max(worst, float(np.max(np.abs(r)) / den) if den else 0.0)
    return worst


def m6_cell(effect, pcm):
    """(wet/dry dB after the room has built, rho) at Mix 2."""
    taps = effect.node.taps
    out = at_mix(effect, 127, pcm)
    start = LATENCY + taps
    wet = np.sqrt(np.mean(out[start:].astype(np.float64) ** 2))
    dry = np.sqrt(np.mean(pcm[start - LATENCY:len(pcm) - LATENCY].astype(
        np.float64) ** 2))
    level = 20 * np.log10(wet / dry) if wet > 0 else -np.inf
    return level, rho(out, pcm, LATENCY + taps)


# -- D1's impulse, trim and gain ------------------------------------------

def make_impulse(taps=3840, channels=1, seed=7):
    rng = np.random.RandomState(seed)
    env = 3000.0 * np.exp(-np.arange(taps) / (0.25 * taps))
    return np.round(env[:, None] * rng.uniform(-1, 1, (taps, channels))
                    ).astype(np.int16)


def trim_frames(start_ms, rate):
    return int(start_ms * rate / 1000.0)


def unit_gain(h, room_channels, gain_db):
    kept = h[:, :room_channels].astype(np.float64) / 32768.0
    return 10 ** (gain_db / 20.0) / np.sqrt(np.sum(kept ** 2)
                                            / room_channels)


def m1_error(cls, rate, ir_channels, channels, kind, target, gain_db=0.0,
             start_ms=0.0, mix_midi=127, h_full=None):
    """M1's peak error at Mix `mix_midi` through the Mix law, or None when
    the input would have to leave int16 to put the reference at `target`.
    At Mix 2 (127) this is M1 exactly."""
    if h_full is None:
        h_full = make_impulse(3840, ir_channels)
    h = h_full[trim_frames(start_ms, rate):]
    room = min(ir_channels, channels)
    g = unit_gain(h, room, gain_db)
    hf = h.astype(np.float64) * g / 32768.0
    frames = len(h) + rate // 4
    if kind == "sine":
        t = np.arange(frames) / float(rate)
        unit = np.repeat(np.sin(2 * np.pi * 997.0 * t)[:, None], channels, 1)
    else:
        unit = np.random.RandomState(12345).uniform(-1, 1, (frames, channels))
    mix = 2.0 * mix_midi / 127.0
    dry, wet = min(2.0 - mix, 1.0), min(mix, 1.0)

    def reference(x):
        return np.stack([dry * x[:, c] + wet * fftconv(
            x[:, c], hf[:, c if room == 2 else 0]) for c in range(channels)],
            axis=1)

    ref_unit = reference(unit)
    x = np.round(unit * target / np.max(np.abs(ref_unit)))
    if np.max(np.abs(x)) > 32767:
        return None
    x = x.astype(np.int16)
    ref = reference(x.astype(np.float64))
    assert np.max(np.abs(ref)) <= 32767
    effect = build(cls, rate, channels, impulse=h_full.reshape(-1).tobytes(),
                   impulse_channels=ir_channels, ir_gain_db=gain_db,
                   start_ms=start_ms, mix=mix)
    try:
        out = run(effect, x, frames + LATENCY)
    finally:
        effect.deinit()
    return float(np.max(np.abs(out[LATENCY:].astype(np.float64) - ref)))


# --------------------------------------------------------------------------
# The planted faults. Each is something the class or the kit can build;
# none reaches inside the C node.
# --------------------------------------------------------------------------

class TrimLate(ConvolutionReverb):
    """D1: the trim one frame late - at start_ms 0 it drops the first tap."""

    NAME = NAME

    def _trim_frames(self, start_ms):
        return ConvolutionReverb._trim_frames(self, start_ms) + 1


class ExtraPartition(ConvolutionReverb):
    """D2: one partition too many."""

    NAME = NAME

    def _partitions(self, taps):
        return ConvolutionReverb._partitions(self, taps) + 1


class NoChecks(ConvolutionReverb):
    """D2's null: the class with its allocation checks removed."""

    NAME = NAME

    def _check_allocation(self, taps, seconds=None):
        return None


class ZeroLatency(ConvolutionReverb):
    """D3: `latency_samples` hard-wired 0, the old class's own defect."""

    NAME = NAME

    @property
    def latency_samples(self):
        self._check_live()
        return 0


class _After(ConvolutionReverb):
    """A kit fault node after the convolver."""

    NAME = NAME

    def _fault(self, node):
        raise NotImplementedError

    def _build(self, *arguments, **options):
        ConvolutionReverb._build(self, *arguments, **options)
        self._planted = self._fault(self._node)
        self._output = self._planted


class OneLsbAfter(_After):
    """D4: `kit_faults.OneLsbScale` after the node."""

    NAME = NAME

    def _fault(self, node):
        return kit_faults.OneLsbScale(node)


class StuckDcAfter(_After):
    """D5 (2): `kit_faults.StuckDc` after the node."""

    NAME = NAME

    def _fault(self, node):
        return kit_faults.StuckDc(node)


class UnnormalisedAfter(_After):
    """D6: `kit_faults.HiddenGain` at 10 log10(T60 / 50 ms) dB, the level an
    unnormalised room would have, which tracks the decay."""

    NAME = NAME

    def _fault(self, node):
        return kit_faults.HiddenGain(
            node, 10.0 * np.log10(self._synthesis()[0] / 0.05))


class LongDecay(ConvolutionReverb):
    """D5 (1): the decay handed to the node 5 % long against the law."""

    NAME = NAME

    def _synthesis(self):
        room = ConvolutionReverb._synthesis(self)
        return (room[0] * 1.05,) + tuple(room[1:])


class NoReset(ConvolutionReverb):
    """Tier 1 reset: `reset()` that leaves the history in the node."""

    NAME = NAME

    def reset(self):
        self._check_live()
        self.program_change(0)


def reach(faulted, reading, tolerance=0.0, rate=RATE, channels=2):
    return kit_faults.fault_reachability(
        ConvolutionReverb, faulted, reading,
        lambda cls: build(cls, rate, channels), tolerance=tolerance)


WALKED = 6 * len(GRID) + 8


# --------------------------------------------------------------------------
# The surface
# --------------------------------------------------------------------------

class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_capabilities(self):
        cls = ConvolutionReverb
        self.assertEqual(cls.MACRO_LABELS, ("Decay", "Damping", "Predelay",
                                            "Diffusion", "Room", "Mix"))
        self.assertEqual(len(cls.PATCHES), 8)
        self.assertEqual(cls.CAPABILITIES, ())
        self.assertEqual(cls.TIER, _component.AUDIODSP)
        self.assertEqual(cls.REQUIRES, ("audioconvolve",))
        effect = build()
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(effect.live_macros, (0, 1, 2, 3, 4, 5))
        self.assertFalse(effect.measured)
        effect.set_macro(0, 64)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)
        effect.deinit()

    def test_the_module_is_what_the_registry_builds(self):
        from audioeffects import rebuilt as registry
        self.assertIs(registry.module_class(NAME), ConvolutionReverb)
        self.assertIn(NAME, registry.parked())

    def test_patch_0_is_the_constructor_grid(self):
        effect = build()
        grid = ConvolutionReverb.PATCHES[0][1]
        for index, expected in enumerate(grid):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)
        effect.deinit()

    def test_patch_table_is_macro_of_the_dossier_settings(self):
        spans = ConvolutionReverb._MACRO_RANGES
        settings = {
            0: (1.0, 6000.0, 0.0, 0.5, 1, 0.6),
            1: (0.3, 4000.0, 0.1, 0.5, 3, 0.7),
            2: (1.0, 7000.0, 0.6, 0.5, 7, 0.8),
            3: (0.8, 1500.0, 0.2, 0.5, 11, 0.7),
            4: (0.8, 7500.0, 0.0, 0.25, 5, 0.8),
            5: (1.0, 5000.0, 0.3, 1.0, 13, 0.99),
            6: (0.0, 7000.0, 0.2, 0.0, 2, 1.2),
            7: (1.0, 6000.0, 0.0, 0.5, 1, 2.0),
        }
        for index, values in settings.items():
            grid = tuple(_component.macro_of(span, value)
                         for span, value in zip(spans, values))
            self.assertEqual(ConvolutionReverb.PATCHES[index][1], grid,
                             index)

    def test_the_laws_at_the_defaults(self):
        effect = build()
        room = effect._synthesis()
        self.assertAlmostEqual(room[0], 0.08, places=12)       # T60
        self.assertAlmostEqual(room[1], 6000.0, places=6)      # Damping
        self.assertEqual(room[2], 0.0)                         # Predelay
        self.assertAlmostEqual(room[3], 10.0, places=9)        # Diffusion
        self.assertEqual(room[4], 1)                           # Room seed
        self.assertAlmostEqual(effect.decay_seconds, 0.08, places=12)
        self.assertEqual(effect.seconds, 0.08)
        self.assertAlmostEqual(effect.allocated_seconds, 0.08, places=12)
        effect.set_macro(DAMPING_I, 127)
        self.assertEqual(effect._synthesis()[1], 0.0)          # out
        effect.set_macro(DAMPING_I, 126)
        self.assertAlmostEqual(effect._synthesis()[1],
                               500.0 * 15.0 ** (126 / 127.0), places=6)
        effect.set_macro(PREDELAY_I, 127)
        self.assertAlmostEqual(effect._synthesis()[2], 15.0, places=9)
        effect.set_macro(ROOM_I, 127)
        self.assertEqual(effect._synthesis()[4], 64)
        effect.deinit()

    def test_damping_clamps_at_the_rate(self):
        # 0.159 fs: at 22.05 kHz the default is the 3 506 Hz clamp.
        effect = build(rate=22050)
        self.assertAlmostEqual(effect._synthesis()[1], 0.159 * 22050,
                               places=6)
        effect.deinit()

    def test_measured_mode_refuses_the_synthesis_macros(self):
        effect = build(impulse=make_impulse().tobytes())
        self.assertTrue(effect.measured)
        self.assertEqual(effect.live_macros, (5,))
        self.assertIsNone(effect.decay_seconds)
        for index in range(5):
            with self.assertRaises(IndexError) as caught:
                effect.set_macro(index, 10)
            self.assertIn(NAME, str(caught.exception))
            self.assertIn(ConvolutionReverb.MACRO_LABELS[index],
                          str(caught.exception))
            with self.assertRaises(IndexError):
                effect.get_macro(index)
        effect.set_macro(MIX_I, 127)
        self.assertEqual(effect.get_macro(MIX_I), 127)
        with self.assertRaises(IndexError):
            effect.set_macro(6, 0)
        # A patch sets Mix and leaves the synthesis positions inert.
        with mock.patch.object(audioconvolve.Convolver, "synthesize") as s:
            effect.program_change(6)
            self.assertEqual(s.call_count, 0)
        self.assertAlmostEqual(effect.get_macro(MIX_I), 76, places=9)
        self.assertEqual(effect.patch_index, 6)
        effect.deinit()

    def test_impulse_level_and_shape_are_checked(self):
        with self.assertRaises(ValueError):
            build(impulse=np.zeros(512, dtype=np.int16).tobytes())
        with self.assertRaises(ValueError):
            build(impulse=b"\x00\x00\x00")
        with self.assertRaises(ValueError):
            build(impulse=make_impulse().tobytes(), ir_gain_db=12.5)
        with self.assertRaises(ValueError):
            build(impulse=make_impulse().tobytes(), start_ms=200.5)

    def test_a_trim_past_the_impulse_raises(self):
        # A clamped trim would build the unloaded wire, whose Mix does
        # nothing, with no error (review probe
        # convolutionreverb_review_trimall.py; ruling (o)). 100 frames is
        # 2.083 ms at 48 kHz: 2.0 ms trims 96 and builds a 256-tap room.
        h = make_impulse(100).tobytes()
        effect = build(impulse=h, start_ms=2.0)
        self.assertEqual(effect.node.taps, 256)
        self.assertEqual(effect.latency_samples, LATENCY)
        effect.deinit()
        for start_ms, trim in ((2.1, 100), (10.0, 480)):
            with self.assertRaises(ValueError) as caught:
                build(impulse=h, start_ms=start_ms)
            text = str(caught.exception)
            for field in (NAME, "start_ms=%r" % start_ms, "%d frames" % trim,
                          "48000 Hz", "has 100"):
                self.assertIn(field, text)
        # The deliberate empty room stays the undelayed wire (D3).
        effect = build(impulse=b"", start_ms=10.0)
        self.assertEqual((effect.node.taps, effect.latency_samples), (0, 0))
        effect.deinit()

    def test_an_int16_array_is_trimmed_by_frames(self):
        from array import array
        h = make_impulse(1000, 2)
        as_array = array("h")
        as_array.frombytes(h.tobytes())
        one = build(impulse=h.tobytes(), impulse_channels=2, start_ms=5.0)
        two = build(impulse=as_array, impulse_channels=2, start_ms=5.0)
        pcm = white(4096)
        self.assertEqual(digest(run(one, pcm)), digest(run(two, pcm)))
        self.assertEqual(one.node.taps, 768)       # 1000 - 240 -> 3 x 256
        one.deinit()
        two.deinit()


class ResynthesisIsDeduplicated(unittest.TestCase):
    """Section 4 and 8.6: one synthesis per construction, patch and reset;
    none for a move that lands on the room already loaded, or for Mix."""

    def count(self, action):
        with mock.patch.object(audioconvolve.Convolver, "synthesize",
                               autospec=True,
                               side_effect=audioconvolve.Convolver.synthesize
                               ) as spy:
            result = action()
        return spy.call_count, result

    def test_construction_patch_and_moves(self):
        calls, effect = self.count(lambda: build(patch=3))
        self.assertEqual(calls, 1)
        self.assertEqual(effect.patch_index, 3)
        calls, _ = self.count(lambda: effect.set_macro(MIX_I, 90))
        self.assertEqual(calls, 0)
        # Patch 3's own Decay, written back: the room it already holds.
        calls, _ = self.count(lambda: effect.set_macro(
            DECAY_I, ConvolutionReverb.PATCHES[3][1][DECAY_I]))
        self.assertEqual(calls, 0)
        calls, _ = self.count(lambda: effect.set_macro(DECAY_I, 10))
        self.assertEqual(calls, 1)
        calls, _ = self.count(lambda: effect.program_change(1))
        self.assertEqual(calls, 1)
        calls, _ = self.count(lambda: effect.program_change(1))
        self.assertEqual(calls, 0)
        calls, _ = self.count(effect.reset)
        self.assertEqual(calls, 1)
        self.assertEqual(effect.patch_index, 0)
        effect.deinit()

    def test_a_room_move_starts_the_room_empty_and_a_mix_move_does_not(self):
        # The docstring's claim, measured: the node empties its history on
        # a re-synthesis (audiodsp_convolve.c:254).
        burst = np.vstack([white(2400), silence(20000)])
        clean = build(mix=2.0)
        ref = run(clean, burst)
        for move, expect_cut in (((DECAY_I, 100), True),
                                 ((MIX_I, 126), False)):
            effect = build(mix=2.0)
            channels = effect.channel_count
            effect._source.swap(probes.ArraySource(burst, rate=RATE,
                                                   channels=channels))
            audiocore.reset_buffer(effect.node)
            out = bytearray()
            for block in range(40):
                if block == 10:
                    effect.set_macro(*move)
                out += bytes(audiocore.get_buffer(effect.output)[1])
            out = np.frombuffer(bytes(out), dtype=np.int16).reshape(-1, 2)
            after = out[10 * 256:]
            if expect_cut:
                self.assertEqual(int(np.max(np.abs(after))), 0)
                self.assertGreater(int(np.max(np.abs(ref[2560:10240]))), 1000)
            else:
                self.assertGreater(int(np.max(np.abs(after))), 1000)
            effect.deinit()
        clean.deinit()

    def test_a_room_move_drops_the_partition_in_flight_dry_included(self):
        # The docstring's other half, measured: the reset at the end of
        # synthesize() (audiodsp_convolve.c:254) zeroes the pending and
        # output blocks too, so at Mix 0 the source frames in flight at the
        # move (2304..2559 for a move before block 10) come out as exact
        # zero, and every other frame is the source 256 late. A move onto
        # the room already loaded, and a Mix move that stays at 0, drop
        # nothing (review probe convolutionreverb_review_movedrop.py).
        frames = 40 * 256
        moves = ((DECAY_I, 64), (DAMPING_I, 30), (PREDELAY_I, 40),
                 (DIFFUSION_I, 100), (ROOM_I, 50), (DECAY_I, None),
                 (MIX_I, 0))
        for rate in RATES:
            for channels in (2, 1):
                pcm = ((np.arange(frames) * 7) % 20001 - 10000).astype(
                    np.int16)
                pcm = np.repeat(pcm[:, None], channels, axis=1)
                for index, value in moves:
                    effect = build(rate=rate, channels=channels, mix=0.0)
                    effect._source.swap(probes.ArraySource(
                        pcm, rate=rate, channels=channels))
                    audiocore.reset_buffer(effect.node)
                    out = bytearray()
                    for block in range(40):
                        if block == 10:
                            effect.set_macro(index, effect.get_macro(index)
                                             if value is None else value)
                        out += bytes(audiocore.get_buffer(effect.output)[1])
                    out = np.frombuffer(bytes(out), dtype=np.int16).reshape(
                        -1, channels)
                    want = np.vstack([silence(LATENCY, channels),
                                      pcm[:frames - LATENCY]])
                    cut = index != MIX_I and value is not None
                    if cut:
                        want[2560:2816] = 0
                    self.assertEqual(digest(out), digest(want),
                                     (rate, channels, index, value))
                    self.assertEqual(bool(np.any(pcm[2304:2560] != 0)), True)
                    effect.deinit()
        # At the constructor's Mix 0.6 the same partition reads exact zero.
        effect = build(channels=2)
        pcm = white(frames)
        effect._source.swap(probes.ArraySource(pcm, rate=RATE, channels=2))
        audiocore.reset_buffer(effect.node)
        out = bytearray()
        for block in range(40):
            if block == 10:
                effect.set_macro(DECAY_I, 64)
            out += bytes(audiocore.get_buffer(effect.output)[1])
        out = np.frombuffer(bytes(out), dtype=np.int16).reshape(-1, 2)
        self.assertGreater(int(np.max(np.abs(out[2304:2560]))), 1000)
        self.assertEqual(int(np.max(np.abs(out[2560:2816]))), 0)
        self.assertGreater(int(np.max(np.abs(out[2816:3072]))), 1000)
        effect.deinit()


# --------------------------------------------------------------------------
# D1 - measured mode is exactly convolution, within one output LSB
# --------------------------------------------------------------------------

class D1ExactConvolution(unittest.TestCase):
    def test_within_one_lsb_across_layouts_levels_gain_and_trim(self):
        worst = 0.0
        cells = 0
        for ir_channels, channels in ((1, 2), (2, 2), (1, 1), (2, 1)):
            for kind in ("sine", "noise"):
                for target in (2000.0, 8000.0, 30000.0):
                    for gain_db, start_ms in ((0.0, 0.0), (0.0, 10.0),
                                              (12.0, 10.0), (-24.0, 0.0)):
                        error = m1_error(ConvolutionReverb, RATE, ir_channels,
                                         channels, kind, target, gain_db,
                                         start_ms)
                        if error is None:
                            continue
                        cells += 1
                        worst = max(worst, error)
        self.assertGreater(cells, 50)
        self.assertLessEqual(worst, 1.0)

    def test_within_one_lsb_at_the_lower_rates(self):
        for rate in (44100, 22050):
            for start_ms in (0.0, 10.0):
                error = m1_error(ConvolutionReverb, rate, 2, 2, "noise",
                                 8000.0, 0.0, start_ms)
                self.assertLessEqual(error, 1.0, (rate, start_ms))

    def test_trim_one_frame_late_is_red_at_the_measured_defaults(self):
        # The measured-mode defaults: Mix 0.6 (grid 38), ir_gain_db 0,
        # start_ms 0. M1 through the Mix law, and at Mix 2.
        for mix_midi in (38, 127):
            clean = m1_error(ConvolutionReverb, RATE, 1, 2, "noise", 3000.0,
                             mix_midi=mix_midi)
            planted = m1_error(TrimLate, RATE, 1, 2, "noise", 3000.0,
                               mix_midi=mix_midi)
            self.assertLessEqual(clean, 1.0)
            self.assertGreater(planted, 1000.0, mix_midi)

    def test_the_mix_walk_never_reaches_the_plant(self):
        # fault_reachability walks every label, and in measured mode five of
        # them raise IndexError by design; the walk here is its positions
        # over the one live macro, Mix, and the 8 patches (which set only
        # Mix in this mode).
        h = make_impulse()
        planted = m1_error(TrimLate, RATE, 1, 2, "noise", 3000.0, h_full=h)
        readings = []
        mixes = list(GRID) + [p[1][MIX_I] for p in
                              ConvolutionReverb.PATCHES.values()]
        for mix_midi in mixes:
            readings.append(m1_error(ConvolutionReverb, RATE, 1, 2, "noise",
                                     3000.0, mix_midi=mix_midi, h_full=h))
        self.assertEqual(len(readings), 25)
        self.assertLessEqual(max(readings), 1.0)
        self.assertGreater(planted, 1000.0)

    def test_null_build_is_red(self):
        def measure(cls):
            error = m1_error(cls, RATE, 1, 2, "noise", 8000.0)
            return {"passed": error is not None and error <= 1.0}

        result = kit_faults.null_build_red(ConvolutionReverb, measure,
                                           label="ConvolutionReverb D1")
        self.assertFalse(result["null"]["passed"])


# --------------------------------------------------------------------------
# D2 - the allocation has a ceiling and a floor, and the class names both
# --------------------------------------------------------------------------

def m2(cls, cells):
    """Red entries over (label, seconds, rate, impulse frames, expect)."""
    reds = []
    for label, seconds, rate, frames, expect in cells:
        taps = int(round(seconds * rate)) if frames is None else frames
        law = max(1, (taps + 255) // 256) * 256
        options = {"seconds": seconds}
        if frames is not None:
            options = {"impulse": make_impulse(frames).tobytes()}
        try:
            effect = build(cls, rate, **options)
        except ValueError as exc:
            text = str(exc)
            if expect != "raise":
                reds.append("%s: raised %r" % (label, text))
                continue
            if taps > 131072:
                want = (NAME, str(taps), str(rate),
                        "%.3f s" % (int(131072.0 / rate * 1000) / 1000.0))
            else:
                want = (NAME, "0.060 s")
            missing = [w for w in want if w not in text]
            if missing:
                reds.append("%s: %r lacks %s" % (label, text, missing))
            continue
        got = effect.node.taps
        effect.deinit()
        if expect != "build":
            reds.append("%s: built" % label)
        elif got != law:
            reds.append("%s: %d taps, the law says %d" % (label, got, law))
    return reds


def d2_cells():
    cells = []
    for rate in RATES:
        ceiling = 131072.0 / rate
        printed = int(ceiling * 1000) / 1000.0
        cells += [("ceiling %d" % rate, ceiling, rate, None, "build"),
                  ("ceiling+256 %d" % rate, 131328.0 / rate, rate, None,
                   "raise"),
                  ("printed %.3f %d" % (printed, rate), printed, rate, None,
                   "build"),
                  ("floor 0.06 %d" % rate, 0.06, rate, None, "build"),
                  ("floor 0.0599 %d" % rate, 0.0599, rate, None, "raise"),
                  ("default 0.08 %d" % rate, 0.08, rate, None, "build")]
    cells += [("measured 131072", 0.0, RATE, 131072, "build"),
              ("measured 131073", 0.0, RATE, 131073, "raise")]
    return cells


class D2Allocation(unittest.TestCase):
    def test_every_cell_builds_or_raises_by_the_law(self):
        self.assertEqual(m2(ConvolutionReverb, d2_cells()), [])

    def test_the_message_at_three_seconds(self):
        with self.assertRaises(ValueError) as caught:
            build(seconds=3.0)
        self.assertEqual(
            str(caught.exception),
            "ConvolutionReverb: 144000 taps at 48000 Hz is over the ceiling "
            "of 131072 taps (512 partitions), 2.730 s at this rate")

    def test_the_default_allocation_at_three_rates(self):
        for rate, taps in ((48000, 3840), (44100, 3584), (22050, 1792)):
            effect = build(rate=rate)
            self.assertEqual(effect.node.taps, taps)
            effect.deinit()

    def test_null_with_the_checks_removed_is_red(self):
        reds = m2(NoChecks, d2_cells())
        self.assertGreaterEqual(len(reds), 7, reds)
        self.assertTrue(any("impulse is too long" in r for r in reds))
        self.assertTrue(any("0.0599" in r and "built" in r for r in reds))

    def test_one_partition_too_many_is_red_at_the_defaults(self):
        for rate, law in ((48000, 3840), (44100, 3584), (22050, 1792)):
            effect = build(ExtraPartition, rate)
            self.assertEqual(effect.node.taps, law + 256)
            effect.deinit()
        self.assertTrue(m2(ExtraPartition, d2_cells()))

    def test_the_plant_is_not_on_the_surface(self):
        result = reach(ExtraPartition, lambda e: e.node.taps)
        self.assertEqual(result["target"], 4096)
        self.assertEqual(result["clean"], 3840)
        self.assertEqual(result["checked"], WALKED)


# --------------------------------------------------------------------------
# D3 - latency is one partition loaded, zero unloaded, and reported so
# --------------------------------------------------------------------------

class D3Latency(unittest.TestCase):
    def test_loaded_every_patch_and_the_predelay_stop(self):
        for rate in RATES:
            for channels in ((2, 1) if rate == RATE else (2,)):
                effect = build(rate=rate, channels=channels)
                pulse = click(4096, channels)
                settings = [("patch", p) for p in sorted(
                    ConvolutionReverb.PATCHES)] + [("predelay", 127)]
                for kind, value in settings:
                    if kind == "patch":
                        effect.program_change(value)
                    else:
                        effect.program_change(0)
                        effect.set_macro(PREDELAY_I, value)
                    self.assertEqual(effect.latency_samples, 256)
                    for mix in (0, 63):
                        self.assertEqual(
                            first_arrival(at_mix(effect, mix, pulse)), 256,
                            (rate, channels, kind, value, mix))
                effect.deinit()

    def test_wet_arrives_at_the_partition_over_64_rooms(self):
        effect = build(diffusion=0.0, mix=2.0)
        pulse = click(4096)
        for room in range(0, 128, 2):
            effect.set_macro(ROOM_I, room)
            self.assertEqual(first_arrival(run(effect, pulse)), 256, room)
        effect.deinit()

    def test_unloaded_is_an_undelayed_wire(self):
        for rate in RATES:
            effect = build(rate=rate, impulse=b"")
            self.assertEqual(effect.latency_samples, 0)
            self.assertEqual(effect.tail_samples, 0)
            pcm = white(2048)
            for mix in (0, 63, 127):
                out = at_mix(effect, mix, pcm)
                self.assertEqual(digest(out), digest(pcm), (rate, mix))
                self.assertEqual(first_arrival(at_mix(effect, mix,
                                                      click(1024))), 0)
            effect.deinit()

    def test_tail_is_latency_plus_the_loaded_impulse(self):
        for rate, tail in ((48000, 4096), (44100, 3840), (22050, 2048)):
            effect = build(rate=rate)
            self.assertEqual(effect.tail_samples, tail)
            effect.deinit()
        effect = build(impulse=make_impulse(1000).tobytes())
        self.assertEqual(effect.tail_samples, 256 + 1024)
        effect.deinit()

    def test_zero_latency_is_red_at_the_defaults(self):
        effect = build(ZeroLatency)
        measured = first_arrival(at_mix(effect, 63, click(4096)))
        self.assertEqual(measured, 256)
        self.assertNotEqual(effect.latency_samples, measured)
        effect.deinit()

    def test_the_plant_is_not_on_the_surface(self):
        result = reach(ZeroLatency, lambda e: e.latency_samples)
        self.assertEqual(result["target"], 0)
        self.assertEqual(result["clean"], 256)
        self.assertEqual(result["checked"], WALKED)

    def test_null_build_is_red(self):
        def measure(cls):
            effect = build(cls)
            arrived = first_arrival(at_mix(effect, 63, click(4096)))
            reported = effect.latency_samples
            effect.deinit()
            return {"passed": arrived == reported == 256}

        result = kit_faults.null_build_red(ConvolutionReverb, measure,
                                           label="ConvolutionReverb D3")
        self.assertFalse(result["null"]["passed"])


# --------------------------------------------------------------------------
# D4 - Mix 0 is the source delayed by latency_samples, byte for byte
# --------------------------------------------------------------------------

class D4DelayedWire(unittest.TestCase):
    def test_full_scale_at_three_rates_stereo_and_mono(self):
        for rate in RATES:
            for channels in (2, 1):
                effect = build(rate=rate, channels=channels, mix=0.0)
                for pcm in (alt_fs(4096, channels), ramp_fs(channels)):
                    self.assertTrue(m4(effect, pcm), (rate, channels))
                effect.deinit()

    def test_every_macro_stop_and_patch_with_mix_at_0(self):
        effect = build()
        ramp = ramp_fs(2)
        for index in range(5):
            for stop in (0, 127):
                effect.program_change(0)
                effect.set_macro(index, stop)
                self.assertTrue(m4(effect, ramp), (index, stop))
        for patch in sorted(ConvolutionReverb.PATCHES):
            effect.program_change(patch)
            self.assertTrue(m4(effect, ramp), patch)
        effect.deinit()

    def test_measured_and_unloaded(self):
        measured = build(impulse=make_impulse().tobytes())
        self.assertTrue(m4(measured, ramp_fs(2)))
        measured.deinit()
        empty = build(impulse=b"")
        self.assertEqual(empty.latency_samples, 0)
        self.assertTrue(m4(empty, ramp_fs(2)))
        empty.deinit()

    def test_first_256_zero_is_not_redundant(self):
        # On alt_fs, whose period divides 256, a wire's out[256:] equals
        # in[:-256]: the digest alone reads green.
        pcm = alt_fs(4096)
        self.assertEqual(digest(pcm[256:]), digest(pcm[:-256]))
        self.assertFalse(m4_verdict(pcm, pcm, 256))

    def test_one_lsb_scale_is_red_at_the_defaults(self):
        for rate in RATES:
            for channels in (2, 1):
                effect = build(OneLsbAfter, rate, channels)
                for pcm in (alt_fs(4096, channels), ramp_fs(channels)):
                    self.assertFalse(m4(effect, pcm), (rate, channels))
                effect.deinit()

    def test_the_plant_is_not_on_the_surface(self):
        alt, ramp = alt_fs(2048), ramp_fs(2)
        result = reach(OneLsbAfter, lambda e: m4(e, alt) and m4(e, ramp))
        self.assertIs(result["target"], False)
        self.assertIs(result["clean"], True)
        self.assertEqual(result["checked"], WALKED)

    def test_null_build_is_red(self):
        def measure(cls):
            effect = build(cls)
            verdict = m4(effect, ramp_fs(2))
            effect.deinit()
            return {"passed": verdict}

        result = kit_faults.null_build_red(ConvolutionReverb, measure,
                                           label="ConvolutionReverb D4")
        self.assertFalse(result["null"]["passed"])


# --------------------------------------------------------------------------
# D5 - the synthesized room decays at the Decay law's T60, to exact zero
# --------------------------------------------------------------------------

class D5DecayLaw(unittest.TestCase):
    def errors_over_rooms(self, cls=None, rate=RATE, **options):
        effect = build(cls, rate, **options)
        errors = []
        for room in range(0, 128, 2):
            effect.set_macro(ROOM_I, room)
            t60, floor = m5_cell(effect)
            self.assertTrue(floor, room)
            self.assertIsNotNone(t60, room)
            law = law_t60(effect._macros[DECAY_I], effect._macros[PREDELAY_I],
                          effect.seconds)
            errors.append(t60 / law - 1.0)
        effect.deinit()
        return np.array(errors)

    def test_damping_out_every_room_within_3_percent(self):
        for rate, decays in ((48000, (0.0, 64 / 127.0, 1.0)),
                             (22050, (1.0,))):
            for decay in decays:
                errors = self.errors_over_rooms(rate=rate, decay=decay,
                                                damping_hz=0.0,
                                                diffusion=0.0)
                self.assertLessEqual(float(np.max(np.abs(errors))), 0.03,
                                     (rate, decay))

    def test_damping_in_the_64_room_mean_within_2_percent(self):
        for rate in RATES:
            errors = self.errors_over_rooms(rate=rate)
            self.assertLessEqual(abs(float(np.mean(errors))), 0.02, rate)
        errors = self.errors_over_rooms(decay=0.0, damping_hz=500.0,
                                        diffusion=0.0)
        self.assertLessEqual(abs(float(np.mean(errors))), 0.02)

    def test_every_patch_mean_within_2_percent_at_one_second(self):
        for patch in (1, 3, 5):
            effect = build(seconds=1.0, patch=patch)
            errors = []
            for room in range(0, 128, 8):
                effect.set_macro(ROOM_I, room)
                t60, floor = m5_cell(effect)
                self.assertTrue(floor)
                law = law_t60(effect._macros[DECAY_I],
                              effect._macros[PREDELAY_I], 1.0)
                errors.append(t60 / law - 1.0)
            effect.deinit()
            self.assertLessEqual(abs(float(np.mean(errors))), 0.02, patch)

    def test_a_decay_5_percent_long_is_red_at_the_defaults(self):
        errors = self.errors_over_rooms(LongDecay)
        self.assertGreater(float(np.mean(errors)), 0.02)

    def test_stuck_dc_turns_the_floor_red(self):
        effect = build(StuckDcAfter)
        t60, floor = m5_cell(effect)
        self.assertFalse(floor)
        effect.deinit()

    def test_the_plants_are_not_on_the_surface(self):
        def handed(effect):
            law = law_t60(effect._macros[DECAY_I],
                          effect._macros[PREDELAY_I], effect.seconds)
            return effect._loaded[0] / law

        result = reach(LongDecay, handed, tolerance=0.01)
        self.assertAlmostEqual(result["target"], 1.05, places=9)
        self.assertAlmostEqual(result["clean"], 1.0, places=9)
        self.assertEqual(result["checked"], WALKED)
        result = reach(StuckDcAfter, lambda e: m5_cell(e)[1])
        self.assertIs(result["target"], False)
        self.assertEqual(result["checked"], WALKED)

    def test_null_build_is_red(self):
        def measure(cls):
            effect = build(cls)
            t60, floor = m5_cell(effect)
            law = law_t60(1.0, 0.0, 0.08)
            effect.deinit()
            return {"passed": floor and t60 is not None
                    and abs(t60 / law - 1.0) <= 0.03}

        result = kit_faults.null_build_red(ConvolutionReverb, measure,
                                           label="ConvolutionReverb D5")
        self.assertFalse(result["null"]["passed"])


# --------------------------------------------------------------------------
# D6 - unit energy, not the source: no synthesis macro is a level control
# --------------------------------------------------------------------------

class D6UnitEnergy(unittest.TestCase):
    def spread(self, cls, index, rate=RATE, peak_dbfs=-12.0, grid=GRID):
        pcm = white(int(1.5 * rate), peak_dbfs=peak_dbfs)
        levels, rhos = [], []
        for position in grid:
            effect = build(cls, rate)
            effect.set_macro(index, position)
            if cls is UnnormalisedAfter:
                # The plant's gain follows the room it was built for.
                effect.deinit()
                options = {"decay": position / 127.0}
                effect = build(cls, rate, **options)
            level, r = m6_cell(effect, pcm)
            effect.deinit()
            levels.append(level)
            rhos.append(r)
        return max(levels) - min(levels), max(rhos)

    def test_decay_and_damping_at_two_levels(self):
        for peak in (-12.0, -30.0):
            for index in (DECAY_I, DAMPING_I):
                spread, worst = self.spread(ConvolutionReverb, index,
                                            peak_dbfs=peak)
                self.assertLessEqual(spread, 0.5, (index, peak))
                self.assertLess(worst, 0.5, (index, peak))

    def test_predelay_diffusion_room_and_the_lower_rates(self):
        for index in (PREDELAY_I, DIFFUSION_I, ROOM_I):
            spread, worst = self.spread(ConvolutionReverb, index)
            self.assertLessEqual(spread, 0.5, index)
            self.assertLess(worst, 0.5, index)
        for rate in (44100, 22050):
            spread, worst = self.spread(ConvolutionReverb, DECAY_I, rate)
            self.assertLessEqual(spread, 0.5, rate)
            self.assertLess(worst, 0.5, rate)

    def test_an_unnormalised_room_is_red_at_the_defaults(self):
        spread, _ = self.spread(UnnormalisedAfter, DECAY_I)
        self.assertGreater(spread, 0.5)

    def test_the_plant_is_not_on_the_surface(self):
        pcm = white(RATE)
        result = reach(UnnormalisedAfter, lambda e: m6_cell(e, pcm)[0],
                       tolerance=1.0)
        self.assertGreater(result["target"], 1.5)
        self.assertLess(abs(result["clean"]), 0.5)
        self.assertEqual(result["checked"], WALKED)

    def test_null_build_is_red(self):
        pcm = white(int(1.5 * RATE))

        def measure(cls):
            effect = build(cls)
            level, r = m6_cell(effect, pcm)
            effect.deinit()
            return {"passed": abs(level) <= 0.5 and r < 0.5}

        result = kit_faults.null_build_red(ConvolutionReverb, measure,
                                           label="ConvolutionReverb D6")
        self.assertFalse(result["null"]["passed"])


# --------------------------------------------------------------------------
# Tier 1, the fast half
# --------------------------------------------------------------------------

class Tier1Fast(unittest.TestCase):
    def test_silence_stays_silence(self):
        for channels in (2, 1):
            effect = build(channels=channels)
            for patch in sorted(ConvolutionReverb.PATCHES):
                effect.program_change(patch)
                out = run(effect, silence(8192, channels))
                self.assertEqual(int(np.max(np.abs(out))), 0, patch)
            effect.deinit()

    def test_reset_empties_the_room(self):
        # Built at patch 0, so reset's program_change(0) finds the room it
        # holds and does not re-synthesize: only the reset clears it.
        for cls, silent in ((ConvolutionReverb, True), (NoReset, False)):
            effect = build(cls, patch=0)
            burst = np.vstack([white(1024), silence(8192)])
            effect._source.swap(probes.ArraySource(burst, rate=RATE,
                                                   channels=2))
            audiocore.reset_buffer(effect.node)
            for _ in range(6):
                audiocore.get_buffer(effect.output)
            effect.reset()
            out = bytearray()
            for _ in range(8):
                out += bytes(audiocore.get_buffer(effect.output)[1])
            peak = int(np.max(np.abs(np.frombuffer(bytes(out),
                                                   dtype=np.int16))))
            if silent:
                self.assertEqual(peak, 0)
            else:
                self.assertGreater(peak, 0)
            effect.deinit()

    def test_deinit_leaves_the_source(self):
        pcm = white(2048)
        source = probes.ArraySource(pcm, rate=RATE, channels=2)
        effect = ConvolutionReverb(source)
        audiocore.get_buffer(effect.output)
        node = effect.node
        effect.deinit()
        effect.deinit()
        self.assertTrue(node._deinited)
        data = bytes(audiocore.get_buffer(source)[1])
        self.assertGreater(int(np.max(np.abs(np.frombuffer(
            data, dtype=np.int16)))), 0)
        with self.assertRaises(RuntimeError):
            effect.latency_samples

    def test_the_tail_reaches_exact_zero(self):
        effect = build(mix=1.2)
        burst = np.vstack([white(4096), silence(8192)])
        out = run(effect, burst)
        self.assertEqual(int(np.max(np.abs(out[4096 + effect.tail_samples:]))),
                         0)
        self.assertGreater(int(np.max(np.abs(
            out[4096 + effect.tail_samples - 512:
                4096 + effect.tail_samples]))), 0)
        effect.deinit()


class ImpulseFiles(unittest.TestCase):
    """The loader: a 16-bit WAV at the graph's rate, read once."""

    def write(self, folder, rate, channels, frames):
        path = os.path.join(folder, "ir_%d_%d.wav" % (rate, channels))
        with wave.open(path, "wb") as handle:
            handle.setnchannels(channels)
            handle.setsampwidth(2)
            handle.setframerate(rate)
            handle.writeframes(make_impulse(frames, channels).tobytes())
        return path

    def test_a_wav_loads_the_same_room_as_its_frames(self):
        with tempfile.TemporaryDirectory() as folder:
            for channels in (1, 2):
                path = self.write(folder, RATE, channels, 900)
                from_file = build(impulse=path)
                from_bytes = build(
                    impulse=make_impulse(900, channels).tobytes(),
                    impulse_channels=channels)
                pcm = white(4096)
                self.assertEqual(digest(run(from_file, pcm)),
                                 digest(run(from_bytes, pcm)))
                self.assertEqual(from_file.node.taps, 1024)
                from_file.deinit()
                from_bytes.deinit()

    def test_a_wav_at_another_rate_raises_naming_both(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, 44100, 1, 900)
            with self.assertRaises(ValueError) as caught:
                build(impulse=path)
            self.assertIn("44100", str(caught.exception))
            self.assertIn("48000", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
