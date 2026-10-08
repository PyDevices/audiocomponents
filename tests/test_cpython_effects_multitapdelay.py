"""`MultiTapDelay`'s own invariant and planted-fault tests.

The dossier, frozen at the Station A revision, has Tier 2 rows
T1-T5. Each row here is the measurement at a few of the row's cells and the
same measurement shown red on a planted fault of the same kind, at the
constructor defaults. Every fault is shown unreachable from every macro
position and shipped patch, and every row's measurement is shown red on the
class built as a wire. The full spans, the three interpreters and the rates
live in the evidence pack, not in this file.

Every law a measurement checks against is written out here from the
dossier, never taken from the class: the whole-frame landing, the lap
clamp, S1's head sets, Tilt's line and the lap node's float32 hand-off.

The class is reached by `rebuilt.module_class("MultiTapDelay")`, which is also what
`audioeffects.MultiTapDelay` serves since its adoption on 2026-09-29.

Three plants are built for real here that Station A emulated: T4's
per-head 6 kHz low-pass (a second tap node for head 2 behind an
`audiofilters.Filter`), T5 clause 2's compose-first build (a front Filter
into the tap node's own decay) and, since fix round 2, T5 clause 1's
(`Head2OwnLoop`: head 2 read through its own, darker lap node, Station C's
plant ported to the fix round 1 graph). The dossier's emulation of clause
1's plant on the rendered windows stays beside it.

Re-audit fix round 1 (2026-09-28) moved the class to audiodsp v0.6.3rc1,
whose lap node lands a stalled loop low-pass (audiodsp#157): the Feedback is
handed as set, and `ReauditRoundOne` holds that beside the retired stepping.
Its route tests run one numpy-free script (`ROUTES_MODULE`) under CPython
and under the workspace's desktop MicroPython and CircuitPython where they
are present and current for `AUDIODSP_PIN`: a mono dry block lost after a
reset shows only on a native interpreter, whose mixer voice points into the
tap's own buffer where the CPython shim copies.

Re-audit fix round 2 (2026-09-28) adds `ReauditRoundTwo`: the same script
with `audiocore.get_buffer` withheld from the class (a stand-in module, so
it runs natively too), every route held to what the docstring says such a
build plays, beside a plant that moves the first block; and `NoTapLap`, a
tail bound one lap short, red on the tail reading at a cell where the tail
comes within a lap.
"""

import math
import os
import subprocess
import sys
import tempfile
import types
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                            # noqa: E402
import audiodelays                                          # noqa: E402
import audioecho                                            # noqa: E402
import audiofilters                                         # noqa: E402
import audiomixer                                           # noqa: E402
import audioroute                                           # noqa: E402
import synthio                                              # noqa: E402
import kit_faults                                           # noqa: E402
import kit_probes as probes                                 # noqa: E402
import audioeffects                                         # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import rebuilt                            # noqa: E402
from audioeffects.chorus import nominal_damping_hz          # noqa: E402
from audioeffects.rebuilt import multitapdelay as mtd       # noqa: E402
from audioeffects.rebuilt.digitaldelay import (             # noqa: E402
    clear_of_stalls, laps_to_zero)
from tools import effect_measurements as kit                # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
RATES = (48000, 44100, 22050)
BLOCK = 256
(TIME_I, PATTERN_I, HEADS_I, FEEDBACK_I, MIX_I, TILT_I, TONE_I, SYNC_I,
 DIVISION_I) = range(9)

MultiTapDelay = rebuilt.module_class("MultiTapDelay")


# --------------------------------------------------------------------------
# The dossier's laws, written out independently of the class

#: S1's table, modes 1-11 (section 6 row 1); mode 12 is every head 1 ... K.
S1 = ((1,), (2,), (3,), (1, 2), (2, 3), (1, 3), (1, 2, 3), (1, 4), (3, 4),
      (1, 3, 4), (1, 2, 4))


def law_heads(mode, heads):
    if mode == 12:
        return tuple(range(1, heads + 1))
    return tuple(k for k in S1[mode - 1] if k <= heads)


def law_frames(time_ms, rate):
    """Section 6 row 0: the nearest whole frame."""
    return int(math.floor(time_ms * rate / 1000.0 + 0.5))


def law_landed(time_ms, heads, rate, max_lap_ms=1600.0):
    """(n1, P): the base landed, clamped so K n1 fits max_lap_ms."""
    n1 = max(1, law_frames(time_ms, rate))
    n1 = min(n1, int(math.floor(max_lap_ms * rate / 1000.0)) // heads)
    return n1, heads * n1


#: Section 4 (revised in fix round 1): the tap node reads its input one
#: block after the dry has played it, so each head is handed k n1 - LAG
#: frames and sounds at k n1 against the dry.
LAW_LAG = 256


def law_time_ms(midi):
    """Section 6 row 0: 20-400 ms, log, on the 0-127 grid."""
    return 20.0 * 20.0 ** (midi / 127.0)


def law_pattern_midi(mode):
    """The MIDI position whose index floor(11 p + 0.5) is mode - 1."""
    return int(round((mode - 1) * 127.0 / 11.0))


def law_heads_midi(heads):
    return int(round((heads - 3) * 127.0 / 5.0))


def law_tilt_levels(selected, heads, tilt):
    """Section 6 row 5: 12 dB x Tilt from head 1 to head K, loudest
    sounding head at 1.0."""
    db = [12.0 * tilt * (k - 1) / (heads - 1) for k in selected]
    top = max(db)
    return [10.0 ** ((d - top) / 20.0) for d in db]


def f32(x):
    return array("f", (float(x),))[0]


def law_node_frames(value, rate):
    """The lap node's frames, `value * rate / 1000.0f`, in float32."""
    return f32(f32(f32(value) * f32(rate)) / f32(1000.0))


def law_lap_node_ms(lap, rate):
    """Section 4, the lap node's hand-off: the least float32 value, by
    one-unit steps from float32(P 1000 / fs), whose frames are >= P."""
    def step(v, up):
        raw = array("I", array("f", (v,)).tobytes())
        raw[0] += 1 if up else -1
        return array("f", raw.tobytes())[0]
    v = f32(lap * 1000.0 / rate)
    while law_node_frames(v, rate) < lap:
        v = step(v, True)
    while law_node_frames(v, rate) > lap:
        lower = step(v, False)
        if law_node_frames(lower, rate) < lap:
            break
        v = lower
    return v


#: Section 6's patch table in engineering units, which `macro_of` puts on
#: the grid: (Time ms, mode, Heads, Feedback, Mix, Tilt, Tone Hz, Sync,
#: Division index). Patch 1's Tone is its out stop, the span's top.
DOSSIER_PATCHES = (
    ("Three Heads, Even", (150.0, 7, 3, 0.45, 0.35, 0.0, 4000.0, 0, 3)),
    ("Three Heads, Even - lean",
     (150.0, 7, 3, 0.45, 0.35, 0.0, 16000.0, 0, 3)),
    ("Two Heads, Near Loudest", (180.0, 4, 4, 0.5, 0.35, -0.5, 4000.0, 0, 3)),
    ("Four Heads, Far Loudest", (74.0, 12, 4, 0.5, 0.35, 0.5, 5000.0, 0, 3)),
    ("Eight Heads, Dense", (40.0, 12, 8, 0.55, 0.3, 0.0, 3000.0, 0, 3)),
    ("One Head, Long Repeats", (120.0, 3, 3, 0.7, 0.35, 0.0, 2500.0, 0, 3)),
    ("Triplet Grid, Synced", (150.0, 7, 3, 0.45, 0.35, 0.0, 4000.0, 1, 4)),
)
SPANS = ((20.0, 400.0, "log"), (0.0, 11.0), (3.0, 8.0), (0.0, 0.95),
         (0.0, 2.0), (-1.0, 1.0), (800.0, 16000.0, "log"), (0.0, 1.0),
         (0.0, 15.0))
MODES = ("UNIPOLAR", "UNIPOLAR", "UNIPOLAR", "UNIPOLAR", "UNIPOLAR",
         "BIPOLAR", "UNIPOLAR", "TOGGLE", "UNIPOLAR")


# --------------------------------------------------------------------------
# Material and rendering


class Endless:
    """int16 frames, BLOCK per pull, then silence for ever: a finite probe
    would stop the lap node's line, which only advances on frames that
    arrive."""

    def __init__(self, data, rate=RATE, channels=2):
        self.sample_rate = int(rate)
        self.channel_count = int(channels)
        self.bits_per_sample = 16
        self.samples_signed = True
        self._pcm = bytes(data)
        self._stride = BLOCK * channels * 2
        self._position = 0

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self._position = 0

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        chunk = self._pcm[self._position:self._position + self._stride]
        self._position += self._stride
        if len(chunk) < self._stride:
            chunk += bytes(self._stride - len(chunk))
        return 1, memoryview(chunk)


def click(level=20000, channels=2, at=0):
    data = array("h", [0] * (BLOCK * 4 * channels))
    for ch in range(channels):
        data[at * channels + ch] = level
    return data


def silence(frames=BLOCK, channels=2):
    return array("h", [0] * (frames * channels))


def pull(effect, frames):
    channels = effect.channel_count
    want = frames * channels * 2
    pcm = bytearray()
    while len(pcm) < want:
        chunk = bytes(audiocore.get_buffer(effect.output)[1])
        if not chunk:
            pcm += bytes(want - len(pcm))
            break
        pcm += chunk
    return np.frombuffer(bytes(pcm[:want]), dtype="<i2").astype(
        np.int64).reshape(-1, channels)


def build(cls=None, data=None, rate=RATE, channels=2, midi=None, **options):
    """An instance with every setting applied before the first pull.

    Built at Mix 0, where the class wires nothing and pulls nothing; the
    MIDI positions in `midi` are then set, and Mix last (the position in
    `midi`, or the constructor's own), which wires the graph with the
    settings already in place.
    """
    cls = cls or MultiTapDelay
    if data is None:
        data = click(channels=channels)
    mix = options.pop("mix", 0.35)
    midi = dict(midi or {})
    effect = cls(Endless(data, rate, channels), sample_rate=rate, mix=0.0,
                 **options)
    mix_midi = midi.pop(MIX_I, None)
    for index in sorted(midi):
        effect.set_macro(index, midi[index])
    if mix_midi is None:
        effect.set_macro(MIX_I, _component.midi_of_position(
            "UNIPOLAR", _component.macro_position((0.0, 2.0), mix)))
    else:
        effect.set_macro(MIX_I, mix_midi)
    return effect


def nonzero(out, channel=0):
    return [int(i) for i in np.nonzero(out[:, channel])[0]]


# --------------------------------------------------------------------------
# The measurements


def first_lap(cls, rate=RATE, channels=2, tone=4000.0, midi=None, **opts):
    """T1's first-lap reading: (non-zero frames, their values, law set).
    Click 20 000, Feedback 0, Mix 2, Tilt 0, P + 512 frames. Lane 0's
    frames and values; a lane whose frames or values differ from lane 0's
    appends minus its number, so every lane is read."""
    midi = dict(midi or {})
    midi.setdefault(MIX_I, 127)
    opts.setdefault("feedback", 0.0)
    effect = build(cls, rate=rate, channels=channels, midi=midi,
                   tone_hz=tone, **opts)
    heads = effect._heads
    mode = effect._pattern_mode()
    n1, lap = law_landed(effect.macro(TIME_I), heads, rate,
                         effect._max_lap_ms)
    out = pull(effect, lap + 512)
    frames = nonzero(out, 0)
    values = [int(out[i, 0]) for i in frames]
    for lane in range(1, channels):
        if nonzero(out, lane) != frames or \
                [int(out[i, lane]) for i in frames] != values:
            frames = frames + [-lane]
    expected = [k * n1 for k in law_heads(mode, heads)]
    effect.deinit()
    return frames, values, expected


def first_lap_green(cls, **kw):
    frames, values, expected = first_lap(cls, **kw)
    return {"passed": frames == expected and values == [20000] * len(values),
            "frames": frames, "expected": expected}


def lap_arrivals(n1, lap, heads, laps, window):
    out = set()
    for n in range(1, laps + 1):
        for k in heads:
            a = (n - 1) * lap + k * n1
            if a < window:
                out.add(a)
    return sorted(out)


def laps_reading(cls, rate=RATE, tone=4000.0, feedback=0.45, midi=None,
                 channels=2, **opts):
    """T1's lap clause, every lane: lean, the non-zero set against every
    arrival inside 4P + 512, exact; full, the onset pair at every
    arrival. `late` lists every miss, lane by lane."""
    midi = dict(midi or {})
    midi.setdefault(MIX_I, 127)
    effect = build(cls, rate=rate, channels=channels, midi=midi,
                   tone_hz=tone, feedback=feedback, **opts)
    heads = law_heads(effect._pattern_mode(), effect._heads)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate,
                         effect._max_lap_ms)
    window = 4 * lap + 512
    out = pull(effect, window)
    effect.deinit()
    arrivals = lap_arrivals(n1, lap, heads, 5, window)
    lanes = range(out.shape[1])
    if tone <= 0.0:
        off = [(lane, sorted(set(nonzero(out, lane)) ^ set(arrivals)))
               for lane in lanes]
        off = [item for item in off if item[1]]
        return {"passed": not off and len(arrivals) > 0,
                "arrivals": len(arrivals), "late": off}
    late = [a for lane in lanes for a in arrivals
            if out[a, lane] == 0 or out[a - 1, lane] != 0]
    return {"passed": not late and len(arrivals) > 0, "late": late,
            "arrivals": len(arrivals)}


def spectra(out, n1, lap, heads, laps=4, size=4096, lane=0):
    win = np.hanning(size)
    res = {}
    for n in range(1, laps + 1):
        for k in heads:
            a = (n - 1) * lap + k * n1
            seg = out[a - size // 2:a + size // 2, lane].astype(float)
            peak = float(np.abs(seg).max())
            mag = np.abs(np.fft.rfft(seg * win))
            res[(n, k)] = (20.0 * np.log10(np.maximum(mag, 1e-9)), peak, seg)
    return res


def t45_reading(cls, rate=RATE, feedback=0.45, tone=4000.0, heads=3,
                mode=7, midi=None, emulate=None, data=None, time_ms=200.0):
    """T4 and T5 at one cell: click 24 000, Mix 2, Tilt 0, t1 200 ms,
    4096-point Hann windows at every arrival of laps 1-4, on every lane.
    Returns lane 0's worst pairwise T4 spread, worst clause-1 increment
    spread, corner and 8/5 kHz D2/D4 of head 1, whether every head sounded
    (every window non-zero) and the lap-1 peaks, with the same for every
    lane under "lanes"; `t4_green` and `t5_green` judge every lane."""
    midi = dict(midi or {})
    midi.setdefault(MIX_I, 127)
    size = 4096
    effect = build(cls, data=click(24000) if data is None else data,
                   rate=rate, midi=midi, time_ms=time_ms, heads=heads,
                   pattern=mode, feedback=feedback, tone_hz=tone)
    selected = law_heads(mode, heads)
    n1, lap = law_landed(time_ms, heads, rate)
    out = pull(effect, 4 * lap + size)
    effect.deinit()
    freqs = np.fft.rfftfreq(size, 1.0 / rate)
    band = (freqs >= 100.0) & (freqs <= 10000.0)
    i100 = int(np.argmin(np.abs(freqs - 100.0)))
    corner = min(tone, rate * 0.5 * _component.NYQUIST_MARGIN)
    top = 8000.0 if rate > 30000 else 5000.0
    lanes = []
    for lane in range(out.shape[1]):
        res = spectra(out, n1, lap, selected, size=size, lane=lane)
        if emulate is not None:
            res = emulate(res, rate)
        present = all(res[(n, k)][1] > 0 for n in range(1, 5)
                      for k in selected)
        t4 = 0.0
        t5 = 0.0
        for n in range(1, 5):
            norm = np.array([res[(n, k)][0] - 20.0 * math.log10(
                max(res[(n, k)][1], 1.0)) for k in selected])
            if len(selected) > 1:
                t4 = max(t4, float(np.max(np.ptp(norm[:, band], axis=0))))
            if n > 1 and len(selected) > 1:
                inc = np.array([res[(n, k)][0] - res[(1, k)][0]
                                for k in selected])
                t5 = max(t5, float(np.max(np.ptp(inc[:, band], axis=0))))
        h = selected[0]

        def dark(n, f, res=res, h=h):
            iq = int(np.argmin(np.abs(freqs - f)))
            inc = res[(n, h)][0] - res[(1, h)][0]
            return -float(inc[iq] - inc[i100])
        lanes.append({"t4": t4, "t5": t5, "present": present,
                      "lap1": [res[(1, k)][1] for k in selected],
                      "c2": dark(2, corner), "c4": dark(4, corner),
                      "q2": dark(2, top), "q4": dark(4, top)})
    result = dict(lanes[0])
    result["lanes"] = lanes
    return result


def one_pole(seg, hz, rate, passes=1):
    """A one-pole low-pass over a rendered window: the dossier's emulation
    of a per-head filter (T4's B4, T5 clause 1's B5)."""
    a = 1.0 - math.exp(-2.0 * math.pi * hz / rate)
    y = np.asarray(seg, dtype=float)
    for _ in range(passes):
        z = np.empty_like(y)
        s = 0.0
        for i, v in enumerate(y):
            s += a * (v - s)
            z[i] = s
        y = z
    return y


def darken_head2_per_lap(res, rate, size=4096):
    """T5 clause 1's plant, emulated as the dossier states it: head 2's
    window through n - 1 extra passes of a 6 kHz one-pole at lap n."""
    win = np.hanning(size)
    out = dict(res)
    for (n, k), (_db, _peak, seg) in res.items():
        if k != 2 or n == 1:
            continue
        y = one_pole(seg, 6000.0, rate, passes=n - 1)
        mag = np.abs(np.fft.rfft(y * win))
        out[(n, k)] = (20.0 * np.log10(np.maximum(mag, 1e-9)),
                       float(np.abs(y).max()), y)
    return out


# --------------------------------------------------------------------------
# Planted faults


class LateHeads(MultiTapDelay):
    """T1 (1): every head below K handed one frame late,
    (k n1 - LAG + 1.5) / P."""

    NAME = 'MultiTapDelay'

    def _tap_positions(self, selected, n1, lap):
        heads = lap // n1
        return tuple((k * n1 - LAW_LAG + (0.5 if k == heads else 1.5)) / lap
                     for k in selected)


class LongLap(MultiTapDelay):
    """T1 (2), the lap clause's own: the lap node handed P + 1 frames."""

    NAME = 'MultiTapDelay'

    def _lap_node_ms(self, lap):
        return law_lap_node_ms(lap + 1, self._sample_rate)


class ShortTapLap(MultiTapDelay):
    """T2 (a): the tap node's lap one frame short, heads still at
    (k n1 + 0.5) / P."""

    NAME = 'MultiTapDelay'

    def _tap_node_ms(self, lap):
        return (lap - 1 + 0.5) * 1000.0 / self._sample_rate


class NarrowTime(MultiTapDelay):
    """T2 (b): Time's span handed as 120-200 ms, log. The constructor's
    150 ms still lands on the same frame."""

    NAME = 'MultiTapDelay'
    _MACRO_RANGES = ((120.0, 200.0, "log"),) + \
        MultiTapDelay._MACRO_RANGES[1:]


class RotatedTable(MultiTapDelay):
    """T3: S1's table rotated by one position: position m sounds mode
    m + 1's set, position 12 mode 1's."""

    NAME = 'MultiTapDelay'

    def _head_set(self, mode, heads=None):
        return MultiTapDelay._head_set(self, mode % 12 + 1, heads)


class FilteredHead(MultiTapDelay):
    """T4: head 2 read by a second tap node behind a 6 kHz low-pass, built
    for real: the lap node's output split into two tap nodes, head 2's
    behind the filter, summed as a third voice of the output Mixer (a
    nested Mixer would reset the tap nodes' lines when it is played). Both
    tap nodes are wired the class's way, a block of zeros first and one
    block behind the dry. Full graph only; the plant is read at Tone in."""

    NAME = 'MultiTapDelay'
    CORNER_HZ = 6000.0

    def _wire(self, quiet=False):
        rate, channels = self._sample_rate, self._channel_count
        self._plant_filtered_head = True
        self._fd.play(self._tap1)
        split = audioroute.Splitter(self._fd, taps=2)
        self._filter = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                  type(self).CORNER_HZ),
            mix=1.0, buffer_size=BLOCK * channels * 2, sample_rate=rate,
            channel_count=channels)
        self._filter.play(split.tap(1))
        self._head2 = audiodelays.MultiTapDelay(
            max_delay_ms=1601, delay_ms=self._tap_ms, decay=0.0, mix=1.0,
            taps=self._head2_taps(), buffer_size=BLOCK * channels * 2,
            sample_rate=rate, channel_count=channels)
        self._feed2 = audioroute.Port(self._hush)
        self._head2.play(self._feed2)
        self._tapnode.taps = self._other_taps()
        self._feed.play(self._hush)
        self._tapnode.play(self._feed)
        mix = self._value(MIX_I)
        self._mixer = audiomixer.Mixer(
            voice_count=3, buffer_size=BLOCK * channels * 4,
            channel_count=channels, sample_rate=rate)
        self._mixer.voice[0].level = min(1.0, 2.0 - mix)
        self._mixer.voice[1].level = min(1.0, mix)
        self._mixer.voice[2].level = min(1.0, mix)
        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._mixer.voice[0].play(self._dry)
        self._mixer.voice[1].play(self._tapnode)
        self._mixer.voice[2].play(self._head2)
        self._feed.play(split.tap(0))
        self._feed2.play(self._filter)
        self._tail.play(self._mixer)
        self._plugged = False

    def _other_taps(self):
        return tuple(t for k, t in zip(self._selected, self._taps) if k != 2)

    def _head2_taps(self):
        return tuple(t for k, t in zip(self._selected, self._taps) if k == 2)

    def _refresh(self):
        MultiTapDelay._refresh(self)
        if getattr(self, "_head2", None) is not None:
            self._tapnode.taps = self._other_taps()
            self._mixer.voice[2].level = self._mixer.voice[1].level


class FrontFilter(MultiTapDelay):
    """T5 clause 2: the seed's compose-first build, built for real - a
    front `audiofilters.Filter` (low-pass at the Tone value) into the tap
    node, whose own decay makes the laps. It decays and never darkens. The
    filter holds the source's first block from its own prime, which is the
    one block the tap node runs behind the dry."""

    NAME = 'MultiTapDelay'

    def _wire(self, quiet=False):
        rate, channels = self._sample_rate, self._channel_count
        self._plant_front_filter = True
        self._filter = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                  self._hz(self._value(TONE_I))),
            mix=1.0, buffer_size=BLOCK * channels * 2, sample_rate=rate,
            channel_count=channels)
        self._filter.play(self._tap1)
        self._tapnode.decay = self._value(FEEDBACK_I)
        self._feed.play(self._hush)
        self._tapnode.play(self._feed)
        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._mixer.voice[0].play(self._dry)
        self._mixer.voice[1].play(self._tapnode)
        self._feed.play(self._filter)
        self._plugged = False

    def _refresh(self):
        MultiTapDelay._refresh(self)
        self._tapnode.decay = self._value(FEEDBACK_I)


class PrimingReset(MultiTapDelay):
    """Station B review's finding, planted: the base's `reset()`, which
    wires a never-wired graph by priming a block of the borrowed source
    and restores patch 0 without dropping the block tap 1 holds."""

    NAME = 'MultiTapDelay'

    def reset(self):
        _component.Component.reset(self)

    def _quiet_wiring(self):
        # The base's reset never sets `_resetting`, and before re-audit fix
        # round 1 a wiring outside `reset()` primed the source.
        return self._resetting


class StaleReset(MultiTapDelay):
    """Tier 1 STATE, planted: `reset()` empties both lines but leaves the
    one block tap 1 holds for the tap node, audio from before the reset."""

    NAME = 'MultiTapDelay'

    def _resync(self):
        self._fd.clear()
        audiocore.reset_buffer(self._tapnode)
        self._feed.play(self._target(self._lean))
        self._plugged = self._lean


class PrimedWire(MultiTapDelay):
    """Gate audit round 1, item 1, planted: Station B's wiring. The tap
    node primes the source's first block and renders it into its planar
    line for the wet voice's prime, level with the dry, heads handed at
    (k n1 + 0.5) / P with head K at 1.0, so a Time or Heads move before
    the first pull re-bases that block."""

    NAME = 'MultiTapDelay'

    def _tap_positions(self, selected, n1, lap):
        heads = lap // n1
        return tuple(1.0 if k == heads else (k * n1 + 0.5) / lap
                     for k in selected)

    def _wire(self, quiet=False):
        self._plant_primed_wire = True
        self._fd.play(self._tap1)
        self._feed.play(self._target(self._lean))
        self._tapnode.play(self._feed, loop=False)
        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._mixer.voice[0].play(self._dry, loop=False)
        self._mixer.voice[1].play(self._tapnode, loop=False)
        self._plugged = self._lean


class LateReset(MultiTapDelay):
    """Item 2, planted: a reset that puts a silent block in front of the
    source (fix round c80ca59's quiet prime did), so every later frame is
    a block late against a reported 0."""

    NAME = 'MultiTapDelay'
    _plant_late_reset = True

    def _resync(self):
        MultiTapDelay._resync(self)
        if self._resetting:
            self._adapter.play(self._hush)
            self._mixer.voice[0].play(self._dry, loop=False)
            self._adapter.play(self._source)


class MixerTail(MultiTapDelay):
    """Item 3, planted: the output port on the Mixer, as before the tail.
    A host's reset reaches the Mixer, whose voices re-prime from the
    Splitter's taps and drop the block they hold."""

    NAME = 'MultiTapDelay'

    def _route(self):
        MultiTapDelay._route(self)
        if self._ready and not self._at_source:
            self._plant_mixer_tail = True
            self._output = self._mixer


class PrimingPlug(MultiTapDelay):
    """Item 4, planted: a Repeat Tone crossing that re-plays the tap node
    (Station B's `_plug`), which primes a block from its new source; two
    crossings between pulls take two."""

    NAME = 'MultiTapDelay'
    _plant_priming_plug = True

    def _plug(self, lean):
        if not lean:
            self._fd.clear()
        self._feed.play(self._target(lean))
        self._tapnode.play(self._feed, loop=False)
        self._plugged = lean


class PannedLaps(MultiTapDelay):
    """Item 5, the lane-1 plant (the material refuter's): the lap node's
    input steered to the left line (`input_pan` -1), so the right lane
    keeps lap 1 (the lap node's dry pass) and loses every later lap."""

    NAME = 'MultiTapDelay'

    def _refresh(self):
        MultiTapDelay._refresh(self)
        self._plant_panned_laps = True
        self._fd.set(input_pan=-1.0)


class CrossedLaps(MultiTapDelay):
    """Item 5 (the material refuter's): the lap node's cross-feed at 1,
    so every lap swaps lanes."""

    NAME = 'MultiTapDelay'

    def _refresh(self):
        MultiTapDelay._refresh(self)
        self._plant_crossed_laps = True
        self._fd.set(cross_feed=1.0)


class LapMixOne(MultiTapDelay):
    """Item 6 (the material refuter's): the lap node's `mix` at 1.0, not
    the Feedback (dossier section 4's correction undone), so lap 2 is at
    unity against lap 1."""

    NAME = 'MultiTapDelay'

    def _refresh(self):
        MultiTapDelay._refresh(self)
        self._lap_mix = 1.0
        self._fd.set(mix=1.0)


class ToneHalf(MultiTapDelay):
    """Item 6 (the material refuter's): Repeat Tone's corner at half the
    knob, one pass about -7 dB at the knob's frequency, not -3."""

    NAME = 'MultiTapDelay'

    def _tone_damping(self):
        if self._macros[TONE_I] >= 1.0:
            return 0.0
        return nominal_damping_hz(0.5 * self._hz(self._value(TONE_I)),
                                  self._sample_rate)


class PullingResync(MultiTapDelay):
    """Gate audit round 2, item 1, planted: fix round 1's `_resync`
    (d419ac4), which drops tap 1's pending block with a pull and primes the
    tap node with zeros. A second call before the next pull takes a block
    of the source's future, and every later head sounds a block early."""

    NAME = 'MultiTapDelay'
    _plant_pulling_resync = True

    def _resync(self):
        pull = getattr(audiocore, "get_buffer", None)
        self._fd.clear()
        audiocore.reset_buffer(self._tapnode)
        if pull is not None:
            pull(self._tap1)
        self._feed.play(self._hush)
        self._tapnode.play(self._feed, loop=False)
        self._feed.play(self._target(self._lean))
        self._plugged = self._lean


class NoRateFloor(MultiTapDelay):
    """Gate audit round 2, item 2, planted: the class without its rate
    floor (d419ac4). At 12 800 Hz Time 20 ms lands on 256 frames, head 1 is
    handed an offset of 0, which reads a whole lap back, and every head
    sounds 256 frames late; below it the constructor's own Time raises
    from the node."""

    NAME = 'MultiTapDelay'

    def _check_rate(self, rate):
        del rate


class Head2OwnLoop(MultiTapDelay):
    """T5 clause 1, built for real (Station C's plant, ported to the fix
    round 1 graph): head 2 is read by a second tap node behind a second
    lap node whose loop low-pass sits at half Repeat Tone's corner
    (pre-warped the class's way), so on every lap after the first head 2
    darkens more than heads 1 and 3; lap 1, the lap nodes' dry pass, is the
    same for every head. Both lap nodes are fed from a second Splitter on
    tap 1, and head 2 is a third voice of the output Mixer. Both tap nodes
    are wired the class's way, a block of zeros first and one block behind
    the dry. Full graph only; read at Repeat Tone in."""

    NAME = 'MultiTapDelay'

    def _damping2(self):
        if self._macros[TONE_I] >= 1.0:
            return 0.0
        return nominal_damping_hz(0.5 * self._hz(self._value(TONE_I)),
                                  self._sample_rate)

    def _others(self):
        return tuple(t for k, t in zip(self._selected, self._taps) if k != 2)

    def _mine(self):
        return tuple(t for k, t in zip(self._selected, self._taps) if k == 2)

    def _wire(self, quiet=False):
        rate, channels = self._sample_rate, self._channel_count
        self._plant_head2_loop = True
        split = audioroute.Splitter(self._tap1, taps=2)
        self._fd.play(split.tap(0))
        self._fd2 = audioecho.FeedbackDelay(
            sample_rate=rate, channel_count=channels,
            max_delay_ms=self._max_lap_ms + 1.0, delay_ms=self._lap_ms,
            feedback=self._feedback, mix=self._feedback,
            damping_hz=self._damping2(), cut_hz=0.0, delay_slew=0.0)
        self._fd2.play(split.tap(1))
        self._head2 = audiodelays.MultiTapDelay(
            max_delay_ms=int(math.ceil(self._max_lap_ms)) + 1,
            delay_ms=self._tap_ms, decay=0.0, mix=1.0, taps=self._mine(),
            buffer_size=BLOCK * channels * 2, sample_rate=rate,
            channel_count=channels)
        self._feed2 = audioroute.Port(self._hush)
        self._head2.play(self._feed2)
        self._tapnode.taps = self._others()
        self._feed.play(self._hush)
        self._tapnode.play(self._feed)
        mix = self._value(MIX_I)
        self._mixer = audiomixer.Mixer(
            voice_count=3, buffer_size=BLOCK * channels * 4,
            channel_count=channels, sample_rate=rate)
        self._mixer.voice[0].level = min(1.0, 2.0 - mix)
        self._mixer.voice[1].level = min(1.0, mix)
        self._mixer.voice[2].level = min(1.0, mix)
        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._mixer.voice[0].play(self._dry)
        self._mixer.voice[1].play(self._tapnode)
        self._mixer.voice[2].play(self._head2)
        self._feed.play(self._fd)
        self._feed2.play(self._fd2)
        self._tail.play(self._mixer)
        self._plugged = False

    def _refresh(self):
        MultiTapDelay._refresh(self)
        if getattr(self, "_head2", None) is not None:
            self._tapnode.taps = self._others()
            self._head2.taps = self._mine()
            self._fd2.set(delay_ms=self._lap_ms, feedback=self._feedback,
                          mix=self._feedback, damping_hz=self._damping2(),
                          cut_hz=0.0, delay_slew=0.0)
            self._mixer.voice[2].level = self._mixer.voice[1].level


class Counting(Endless):
    """`Endless` that counts the blocks it has handed out."""

    pulls = 0

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        self.pulls += 1
        return Endless._get_buffer(self, single_channel_output,
                                   audio_channel)


def reset_pulls(cls, start, channels=2):
    """Blocks of the borrowed source `reset()` takes from each starting
    graph: patch 1 (lean), Repeat Tone at its out stop, and a class built
    at Mix 0 that has never wired."""
    source = Counting(probes.noise_det(4 * BLOCK, channels=channels),
                      RATE, channels)
    effect = cls(source, sample_rate=RATE,
                 mix=0.0 if start == "mix0" else 0.35)
    if start == "patch1":
        effect.program_change(1)
    elif start == "tone127":
        effect.set_macro(TONE_I, 127)
    pull(effect, 8 * BLOCK)
    before = source.pulls
    effect.reset()
    taken = source.pulls - before
    effect.deinit()
    return taken


def state_reading(cls, patch, channels=2):
    """The kit's STATE at `patch`, 48 kHz: reset with the probe still
    sounding, then a silent source must render exact zero."""
    data = probes.noise_det(RATE // 2, dbfs=-6.0, channels=channels)
    holder = probes.SwitchableSource(
        probes.ArraySource(data, rate=RATE, channels=channels, block=BLOCK))
    effect = cls.create(holder, RATE)
    effect.program_change(patch)
    silent = probes.ArraySource(probes.silence(2048, channels), rate=RATE,
                                channels=channels, block=BLOCK)

    def render(blocks):
        return probes.render(effect.output, blocks * BLOCK, rate=RATE,
                             channels=channels, block=BLOCK,
                             class_name="MultiTapDelay")

    return kit.state(effect, pull=render, swap=holder.swap,
                     probe_source=holder.inner, silent_source=silent,
                     blocks=64, alloc_pulls=50)


class NoClear(MultiTapDelay):
    """Tier 1's reset plant: `reset()` restores patch 0 and leaves both
    lines full."""

    NAME = 'MultiTapDelay'

    def reset(self):
        self._check_live()
        self.program_change(0)


def reach_build(cls):
    return cls(Endless(silence()), sample_rate=RATE)


def reach(faulted, reading, **kw):
    return kit_faults.fault_reachability(MultiTapDelay, faulted, reading,
                                         reach_build, **kw)


def head_offset_error(effect):
    """What the tap node does with what the class hands it: each sounding
    head's offset, the node's way (the lap truncated from `delay_ms`, the
    offset truncated from the position), less k n1 - LAG."""
    rate = effect._sample_rate
    lap = int(rate / 1000.0 * effect._tap_ms)
    return tuple(int(lap * position) - (k * effect._n1 - LAW_LAG)
                 for k, (position, _level) in zip(effect._selected,
                                                  effect._taps))


def lap_node_error(effect):
    """The lap node's frames, the node's way, less P, floored: 0 on the
    clean class at every setting."""
    return int(math.floor(law_node_frames(effect._lap_ms,
                                          effect._sample_rate))) - effect._lap


def tap_lap_error(effect):
    return int(effect._sample_rate / 1000.0 * effect._tap_ms) - effect._lap


def time_span_landed(effect):
    """The landed t1 in ms at Time's two stops, at the current Heads."""
    span = type(effect)._MACRO_RANGES[TIME_I]
    rate = effect._sample_rate
    out = []
    for position in (0.0, 1.0):
        n1, _lap = law_landed(_component.macro_value(span, position),
                              effect._heads, rate, effect._max_lap_ms)
        out.append(n1 * 1000.0 / rate)
    return tuple(out)


def head_table(effect):
    return tuple(effect._head_set(mode) for mode in range(1, 13))


def click_at(frame, channels=2, level=20000, tail=BLOCK * 4, lanes=None):
    """A click at `frame` (every lane, or the lanes named), then silence."""
    data = array("h", [0] * ((frame + tail) * channels))
    for ch in (range(channels) if lanes is None else lanes):
        data[frame * channels + ch] = level
    return data


def lane_hits(out):
    return [nonzero(out, lane) for lane in range(out.shape[1])]


def ctor_route(cls, move, rate=RATE, channels=2, at=0, pattern=None):
    """Gate audit round 1, item 1: the plain constructor (`mix=2.0,
    feedback=0.0`), then one setting before the first pull, a click at
    frame `at` of every lane; every lane's non-zero frames against the
    law for the knob positions."""
    opts = dict(sample_rate=rate, mix=2.0, feedback=0.0)
    if pattern is not None:
        opts["pattern"] = pattern
    effect = cls(Endless(click_at(at, channels), rate, channels), **opts)
    if move is not None:
        effect.set_macro(*move)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate,
                         effect._max_lap_ms)
    law = [at + k * n1 for k in law_heads(effect._pattern_mode(),
                                          effect._heads)]
    hits = lane_hits(pull(effect, at + lap + 512))
    effect.deinit()
    return {"passed": all(h == law for h in hits), "hits": hits,
            "law": law}


def patch_route(cls, patch, rate=RATE, channels=2):
    """Item 1's program_change route: the constructor's defaults,
    `program_change(patch)`, Feedback 0 and Mix 127 before the first pull.
    Read from frame 1: a Mix move after wiring leaves frame 0 at the old
    dry level in stereo (the surface record's item 4)."""
    effect = cls(Endless(click(channels=channels), rate, channels),
                 sample_rate=rate)
    effect.program_change(patch)
    effect.set_macro(FEEDBACK_I, 0)
    effect.set_macro(MIX_I, 127)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate,
                         effect._max_lap_ms)
    law = [k * n1 for k in law_heads(effect._pattern_mode(),
                                     effect._heads)]
    hits = [[f for f in h if f > 0]
            for h in lane_hits(pull(effect, lap + 512))]
    effect.deinit()
    return {"passed": all(h == law for h in hits), "hits": hits,
            "law": law}


RESET_ORIGIN = 60 * BLOCK + 101     # source frame 15 461


def reset_route(cls, start, rate=RATE, channels=2):
    """Item 2: 30 blocks from `start`, then `reset()`, Feedback 0 and Mix
    1.0 (MIDI 63.5), a click at source frame 15 461: where the dry click
    lands against the source, and the heads against the dry."""
    source = Endless(click_at(RESET_ORIGIN, channels), rate, channels)
    if start == "patch1":
        effect = cls(source, sample_rate=rate, patch=1)
    elif start == "mix0":
        effect = cls(source, sample_rate=rate, mix=0.0)
    else:
        effect = cls(source, sample_rate=rate)
        if start == "tone127":
            effect.set_macro(TONE_I, 127)
    head = pull(effect, 30 * BLOCK)
    effect.reset()
    effect.set_macro(FEEDBACK_I, 0)
    effect.set_macro(MIX_I, 63.5)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate)
    law = [k * n1 for k in law_heads(effect._pattern_mode(),
                                     effect._heads)]
    rest = pull(effect, RESET_ORIGIN - 30 * BLOCK + lap + 1024)
    reported = effect.latency_samples
    effect.deinit()
    out = np.concatenate([head, rest])
    hits = lane_hits(out)
    dry = hits[0][0] if hits[0] else None
    heads = [f - dry for f in hits[0][1:]] if hits[0] else []
    same = all(h == hits[0] for h in hits)
    return {"passed": dry == RESET_ORIGIN and heads == law and same
            and reported == 0, "dry": None if dry is None
            else dry - RESET_ORIGIN, "heads": heads, "law": law}


HOST_CLICKS = (0, 3000)


def host_reset_route(cls, patch=None, rate=RATE, channels=2):
    """Item 3: clicks at source frames 0 and 3 000, the host resets the
    output before its first pull (`tools/render_effect.py` does, and so
    does a mixer voice's `play()`), Feedback 0: each click's dry at its own
    frame and its heads at +k n1."""
    data = array("h", [0] * (12000 * channels))
    for at in HOST_CLICKS:
        for ch in range(channels):
            data[at * channels + ch] = 20000
    effect = cls(Endless(data, rate, channels), sample_rate=rate,
                 feedback=0.0, mix=1.0)
    if patch is not None:
        effect.program_change(patch)
        effect.set_macro(FEEDBACK_I, 0)
        effect.set_macro(MIX_I, 63.5)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate)
    audiocore.reset_buffer(effect.output)
    out = pull(effect, 3000 + lap + 512)
    effect.deinit()
    law = sorted(set(at + k * n1 for at in HOST_CLICKS
                     for k in (0,) + law_heads(effect._pattern_mode(),
                                               effect._heads)))
    hits = lane_hits(out)
    return {"passed": all(h == law for h in hits), "hits": hits,
            "law": law}


def host_reset_lines_route(cls, rate=RATE, channels=2):
    """Item 3 mid-stream (re-audit fix round 1): a click at source frame
    7 000, 30 blocks, the host resets the output, Feedback 0, Mix 1.0: the
    host's reset leaves the lines as they are, so the click's heads sound
    at +k n1 after it."""
    at = 7000
    data = array("h", [0] * (40000 * channels))
    for ch in range(channels):
        data[at * channels + ch] = 20000
    effect = cls(Endless(data, rate, channels), sample_rate=rate,
                 feedback=0.0, mix=1.0)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate)
    head = pull(effect, 30 * BLOCK)
    audiocore.reset_buffer(effect.output)
    rest = pull(effect, at + lap + 512 - 30 * BLOCK)
    effect.deinit()
    law = [at + k * n1 for k in (0,) + law_heads(effect._pattern_mode(),
                                                 effect._heads)]
    hits = lane_hits(np.concatenate([head, rest]))
    return {"passed": all(h == law for h in hits), "hits": hits,
            "law": law}


def crossing_route(cls, crossings, rate=RATE, channels=2):
    """Item 4: 40 blocks at Mix 1, Feedback 0, Time MIDI 64, then Repeat
    Tone across its out stop and back `crossings` times in one gap, then
    a click: the dry at its frame and the heads at +k n1 on every lane."""
    origin = 100 * BLOCK + 29
    effect = build(data=click_at(origin, channels), cls=cls, rate=rate,
                   channels=channels, midi={MIX_I: 63.5, TIME_I: 64},
                   feedback=0.0)
    head = pull(effect, 40 * BLOCK)
    lean = False
    for _ in range(crossings):
        lean = not lean
        effect.set_macro(TONE_I, 127 if lean else 68)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate)
    law = [origin + k * n1 for k in (0,) + law_heads(
        effect._pattern_mode(), effect._heads)]
    rest = pull(effect, origin - 40 * BLOCK + lap + 1024)
    effect.deinit()
    hits = lane_hits(np.concatenate([head, rest]))
    return {"passed": all(h == law for h in hits),
            "hits": [[f - origin for f in h] for h in hits],
            "law": [f - origin for f in law]}


#: Round 2, item 1: two clicks after an event made between two pulls at
#: 30 blocks, A in the first block after it and B in the second, at
#: different levels so their heads cannot be mistaken for each other.
RESYNC_CLICKS = ((30 * BLOCK + 10, 20000), (31 * BLOCK + 100, 10000))


def resync_route(cls, steps, start="full", rate=RATE, channels=2):
    """Gate audit round 2, item 1: 30 blocks from the defaults (the full
    graph) or patch 1 (the lean graph), then `steps` between two pulls
    ("reset" is `reset()`, "mix0" is Mix to 0 and back), then Feedback 0
    and Mix 1.0: every lane's non-zero frames against each click and its
    heads at +k n1, n1 and the heads from the dossier's laws at the knob
    positions."""
    total = 32 * BLOCK + 40000
    data = array("h", [0] * (total * channels))
    for at, level in RESYNC_CLICKS:
        for ch in range(channels):
            data[at * channels + ch] = level
    source = Endless(data, rate, channels)
    if start == "lean":
        effect = cls(source, sample_rate=rate, patch=1)
    else:
        effect = cls(source, sample_rate=rate)
    head = pull(effect, 30 * BLOCK)
    for step in steps:
        if step == "reset":
            effect.reset()
        else:
            effect.set_macro(MIX_I, 0)
            effect.set_macro(MIX_I, 63.5)
    effect.set_macro(FEEDBACK_I, 0)
    effect.set_macro(MIX_I, 63.5)
    heads = law_heads(effect._pattern_mode(), effect._heads)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate)
    rest = pull(effect, 2 * BLOCK + 100 + lap + 512)
    reported = effect.latency_samples
    effect.deinit()
    out = np.concatenate([head, rest])
    law = sorted(at + k * n1 for at, _level in RESYNC_CLICKS
                 for k in (0,) + heads)
    hits = lane_hits(out)
    return {"passed": all(h == law for h in hits) and reported == 0,
            "hits": hits, "law": law}


def low_rate_first_lap(cls, rate, how, channels=2):
    """Gate audit round 2, item 2: Time 20 ms by the constructor
    (`time_ms=20`) or by `set_macro(0, 0)`, Feedback 0, Mix 2, a 20 000
    click in frame 0: every lane's non-zero frames against {k n1}."""
    if how == "ctor":
        effect = cls(Endless(click(channels=channels), rate, channels),
                     sample_rate=rate, feedback=0.0, mix=2.0, time_ms=20.0)
    else:
        effect = cls(Endless(click(channels=channels), rate, channels),
                     sample_rate=rate, feedback=0.0, mix=2.0)
        effect.set_macro(TIME_I, 0)
    n1, lap = law_landed(20.0, 3, rate)
    law = [k * n1 for k in law_heads(7, 3)]
    hits = lane_hits(pull(effect, lap + 512))
    effect.deinit()
    return {"passed": all(h == law for h in hits), "hits": hits,
            "law": law}


def level_reading(cls, rate=RATE, tone=4000.0):
    """Item 6, section 6 row 3's Feedback law (the material refuter's
    reading): click 20 000, the defaults' cell (150 ms, mode 7, K 3),
    Feedback MIDI 60; on every lane head 1's lap-n response summed over
    one head spacing, against lap 1's, is the Feedback to the n - 1 within
    2 % (the loop low-pass has unity gain at DC); and at Feedback 0 nothing
    sounds after the first lap."""
    f = 0.95 * 60 / 127.0
    midi = {FEEDBACK_I: 60, MIX_I: 127}
    effect = build(cls, rate=rate, midi=midi, tone_hz=tone)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate)
    out = pull(effect, 4 * lap + 512)
    effect.deinit()
    ratios = []
    err = 0.0
    for lane in range(out.shape[1]):
        sums = [float(out[(n - 1) * lap + n1:(n - 1) * lap + 2 * n1,
                          lane].sum()) for n in range(1, 5)]
        if sums[0] == 0.0:
            return {"passed": False, "ratios": [], "err": 1.0, "after": 0}
        lane_ratios = [value / sums[0] for value in sums]
        ratios.append([round(value, 4) for value in lane_ratios])
        err = max([err] + [abs(lane_ratios[n] / f ** n - 1.0)
                           for n in range(1, 4)])
    zero = build(cls, rate=rate, midi={FEEDBACK_I: 0, MIX_I: 127},
                 tone_hz=tone)
    out = pull(zero, 2 * lap + n1 + 512)
    zero.deinit()
    after = int(np.count_nonzero(out[lap + 1:, :]))
    return {"passed": err <= 0.02 and after == 0, "ratios": ratios,
            "err": err, "after": after}


def corner_reading(cls, rate=RATE, tone=4000.0):
    """Item 6, section 6 row 6's corner (the material refuter's reading):
    one pass at Repeat Tone's corner, head 1's lap 2 against lap 1 there
    less the same at 100 Hz, is 3 dB within 0.5 dB on every lane."""
    result = t45_reading(cls, rate=rate, tone=tone)
    worst = max(abs(lane["c2"] - 3.0) for lane in result["lanes"])
    return {"passed": worst <= 0.5, "c2": [round(lane["c2"], 2)
                                           for lane in result["lanes"]]}


def left_only_reading(cls, rate=RATE):
    """Item 5, channel-different material: a click in the left lane only,
    the full graph at the defaults, Feedback 0.45: the right lane stays
    exactly zero, and the left lane has every lap's onset."""
    effect = build(cls, data=click_at(0, 2, lanes=(0,)), rate=rate,
                   midi={MIX_I: 127}, feedback=0.45)
    n1, lap = law_landed(effect.macro(TIME_I), effect._heads, rate)
    window = 4 * lap + 512
    out = pull(effect, window)
    effect.deinit()
    arrivals = lap_arrivals(n1, lap, (1, 2, 3), 5, window)
    late = [a for a in arrivals if out[a, 0] == 0 or out[a - 1, 0] != 0]
    right = int(np.count_nonzero(out[:, 1]))
    return {"passed": right == 0 and not late, "right": right,
            "right_peak": int(np.abs(out[:, 1]).max()), "late": late}


def damping_error(effect):
    """The lap node's corner against the knob's own pre-warped corner,
    as a ratio (1 on the clean class, 0 at the out stop)."""
    if effect._damping <= 0.0:
        return 0.0
    law = nominal_damping_hz(effect._hz(effect.macro(TONE_I)),
                             effect._sample_rate)
    return round(effect._damping / law, 6)


def lap_mix_error(effect):
    """The lap node's `mix` less its Feedback: 0 on the clean class."""
    return round(effect._lap_mix - effect._feedback, 6)


def flag(name):
    return lambda effect: getattr(effect, name, False)


# --------------------------------------------------------------------------
# The surface


class TheSurface(unittest.TestCase):
    def test_macros_patches_tier_latency(self):
        cls = MultiTapDelay
        self.assertEqual(cls.MACRO_LABELS,
                         ("Time", "Pattern", "Heads", "Feedback", "Mix",
                          "Tilt", "Repeat Tone", "Sync", "Division"))
        self.assertEqual(tuple(cls.MACRO_MODES[i] for i in range(9)), MODES)
        self.assertEqual(len(cls.PATCHES), 7)
        self.assertEqual(cls.CAPABILITIES, ("tempo_sync",))
        self.assertEqual(cls.LATENCY_SAMPLES, 0)
        self.assertEqual(cls.TIER, _component.AUDIODSP)
        self.assertEqual(cls.REQUIRES, ("audioecho", "audioroute"))
        effect = build()
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.patch_index, None)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)

    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-09-29, so `create()` serves this one. It was the
        reverse assertion while the class was parked; revert
        `rebuilt.ADOPTED` and this goes red."""
        self.assertIn("MultiTapDelay", rebuilt.ADOPTED)
        self.assertNotIn("MultiTapDelay", rebuilt.parked())
        self.assertIs(audioeffects.MultiTapDelay, MultiTapDelay)
        served = audioeffects.create(
            "MultiTapDelay", Endless(silence(), RATE, 2), RATE)
        self.assertIsInstance(served, MultiTapDelay)
        served.deinit()

    def test_patch_table_is_the_dossier_on_the_grid(self):
        for index, (name, values) in enumerate(DOSSIER_PATCHES):
            engineering = list(values)
            engineering[1] = engineering[1] - 1
            grid = tuple(_component.macro_of(span, value, mode)
                         for span, value, mode
                         in zip(SPANS, engineering, MODES))
            self.assertEqual(MultiTapDelay.PATCHES[index], (name, grid))

    def test_patch_0_is_the_constructor_grid(self):
        effect = MultiTapDelay(Endless(silence()), sample_rate=RATE)
        self.assertEqual(effect.patch_index, 0)
        for index, expected in enumerate(MultiTapDelay.PATCHES[0][1]):
            self.assertAlmostEqual(effect.get_macro(index), expected,
                                   delta=0.6)

    def test_constructor_options_clamp(self):
        effect = MultiTapDelay(Endless(silence()), sample_rate=RATE,
                               max_lap_ms=100.0, heads=8, time_ms=400.0)
        self.assertEqual(effect._max_lap_ms, 540.0)
        self.assertEqual(effect._n1, 25920 // 8)
        effect = MultiTapDelay(Endless(silence()), sample_rate=RATE,
                               max_lap_ms=float("nan"), time_ms=float("nan"),
                               tone_hz=0.0, pattern=40, heads=1)
        self.assertEqual(effect._max_lap_ms, 1600.0)
        self.assertEqual(effect._n1, 7200)
        self.assertEqual(effect.get_macro(TONE_I), 127.0)
        self.assertTrue(effect._lean)
        self.assertEqual(effect._pattern_mode(), 12)
        self.assertEqual(effect._heads, 3)

    def test_tilt_law(self):
        # A7.11: K 4 mode 12, Tilt -1 reads 20 000 / 12 619 / 7 962 / 5 023.
        frames, values, expected = first_lap(
            MultiTapDelay, tone=0.0, heads=4, pattern=12, time_ms=20.0,
            midi={TILT_I: 0})
        self.assertEqual(frames, expected)
        levels = law_tilt_levels((1, 2, 3, 4), 4, -1.0)
        self.assertEqual(values, [int(20000 * v) for v in levels])
        self.assertEqual(values, [20000, 12619, 7962, 5023])

    def test_sync_reads_the_transport_only_when_on(self):
        calls = []

        def transport():
            calls.append(1)
            return (True, 0.0, 120.0, 4, 4)
        effect = MultiTapDelay(Endless(silence()), sample_rate=RATE,
                               transport=transport)
        self.assertEqual(calls, [])
        effect.program_change(6)
        self.assertTrue(calls)
        # 1/8T at 120 bpm is 166.67 ms: 8000 frames.
        self.assertEqual(effect._n1, 8000)
        static = MultiTapDelay(Endless(silence()), sample_rate=RATE)
        static.program_change(6)
        self.assertEqual(static._n1, law_frames(law_time_ms(85), RATE))

    def test_the_lap_node_hand_off_is_the_law(self):
        # Section 4: never under P, at the 50 cells at 44.1 kHz where the
        # plain value would land under.
        effect = MultiTapDelay(Endless(silence(), rate=44100),
                               sample_rate=44100, mix=0.0)
        under_plain = 0
        for heads in range(3, 9):
            effect.set_macro(HEADS_I, law_heads_midi(heads))
            for time_midi in range(128):
                effect.set_macro(TIME_I, time_midi)
                lap = effect._lap
                self.assertEqual(effect._lap_ms, law_lap_node_ms(lap, 44100))
                self.assertGreaterEqual(
                    law_node_frames(effect._lap_ms, 44100), lap)
                if law_node_frames(lap * 1000.0 / 44100, 44100) < lap:
                    under_plain += 1
        self.assertEqual(under_plain, 50)


# --------------------------------------------------------------------------
# Tier 1


class Tier1(unittest.TestCase):
    def test_mix_zero_is_a_wire(self):
        for rate in RATES:
            for channels in (2, 1):
                for tone in (4000.0, 0.0):
                    data = probes.ramp_fs(8192, channels)
                    effect = MultiTapDelay(
                        Endless(data, rate, channels), sample_rate=rate,
                        mix=0.0, tone_hz=tone, feedback=0.95, pattern=12,
                        heads=8, time_ms=20.0)
                    out = pull(effect, 8192).reshape(-1)
                    self.assertTrue(np.array_equal(
                        out, np.array(data, dtype=np.int64)),
                        (rate, channels, tone))
                    self.assertEqual(effect.tail_samples, 0)

    def test_mix_back_from_zero_starts_from_empty_lines(self):
        effect = build(data=click(), mix=1.0, feedback=0.9, time_ms=20.0)
        pull(effect, 2000)
        effect.set_macro(MIX_I, 0)
        pull(effect, 256)
        effect.set_macro(MIX_I, 64)
        out = pull(effect, 12000)
        self.assertEqual(int(np.abs(out).max()), 0)

    def test_silence_stays_silence(self):
        for tone in (4000.0, 0.0):
            effect = build(data=silence(), tone_hz=tone, feedback=0.95)
            self.assertEqual(int(np.abs(pull(effect, 48000)).max()), 0)

    def test_click_latency_is_zero(self):
        effect = build(data=click(at=10), mix=1.0)
        out = pull(effect, 7000)
        self.assertEqual(nonzero(out), [10])
        self.assertEqual(int(out[10, 0]), 20000)
        self.assertEqual(effect.latency_samples, 0)

    def test_tail_ends_inside_tail_samples(self):
        for tone in (4000.0, 0.0):
            for feedback in (0.45, 0.85):
                probe = build(data=silence(), tone_hz=tone,
                              feedback=feedback, time_ms=20.0)
                lap = probe._lap
                burst = 4 * lap
                tail = probe.tail_samples
                probe.deinit()
                noise = probes.noise_det(burst, dbfs=0.0)
                effect = build(data=noise, mix=2.0, tone_hz=tone,
                               feedback=feedback, time_ms=20.0)
                self.assertEqual(effect.tail_samples, tail)
                out = pull(effect, burst + tail + 4 * lap)
                last = nonzero(out)[-1]
                self.assertLess(last - burst, tail, (tone, feedback))
                self.assertGreater(last - burst, 0)

    def test_tail_samples_is_finite_at_every_patch(self):
        effect = MultiTapDelay(Endless(silence()), sample_rate=RATE)
        for index in sorted(MultiTapDelay.PATCHES):
            effect.program_change(index)
            self.assertIsInstance(effect.tail_samples, int)
            self.assertGreater(effect.tail_samples, 0)
        effect.program_change(0)
        self.assertEqual(effect.tail_samples, 321435)

    def _after_reset(self, cls):
        effect = build(cls, data=click(), mix=1.0, feedback=0.9,
                       time_ms=20.0)
        pull(effect, 3000)
        effect.reset()
        return int(np.abs(pull(effect, 20000)).max())

    def test_reset_empties_both_lines(self):
        self.assertEqual(self._after_reset(MultiTapDelay), 0)

    def test_reset_plant_is_red(self):
        self.assertGreater(self._after_reset(NoClear), 0)

    def test_reset_takes_nothing_from_the_source(self):
        for start in ("patch1", "tone127", "mix0"):
            for channels in (2, 1):
                self.assertEqual(reset_pulls(MultiTapDelay, start,
                                             channels), 0,
                                 (start, channels))

    def test_reset_priming_plant_is_red(self):
        # The base's reset wires a never-wired class by priming the source.
        # From a wired class a re-plug is a store and takes nothing, so the
        # plant's other half is read by STATE below.
        self.assertGreater(reset_pulls(PrimingReset, "mix0"), 0)

    def test_state_from_the_lean_graph(self):
        for channels in (2, 1):
            result = state_reading(MultiTapDelay, 1, channels)
            self.assertEqual(result["values"]["reset_residual_lsb"], 0,
                             result["red"])
            self.assertTrue(result["values"]["resumed"])

    def test_state_priming_plant_is_red(self):
        result = state_reading(PrimingReset, 1)
        self.assertGreater(result["values"]["reset_residual_lsb"], 0)

    def test_state_stale_block_plant_is_red(self):
        for patch in (0, 1):
            result = state_reading(StaleReset, patch)
            self.assertGreater(result["values"]["reset_residual_lsb"], 0,
                               patch)
        result = state_reading(MultiTapDelay, 0)
        self.assertEqual(result["values"]["reset_residual_lsb"], 0)

    def test_deinit_leaves_the_source(self):
        source = probes.ArraySource(probes.sine(440.0, 0.1, -6.0),
                                    rate=RATE, channels=2)
        effect = MultiTapDelay(source, sample_rate=RATE)
        pull(effect, 512)
        effect.deinit()
        effect.deinit()
        data = memoryview(bytes(audiocore.get_buffer(source)[1])).cast("h")
        self.assertGreater(max(abs(int(v)) for v in data), 0)
        with self.assertRaises(RuntimeError):
            effect.output


# --------------------------------------------------------------------------
# T1 - taps on integer multiples of one base, exactly


class T1Grid(unittest.TestCase):
    def test_first_lap_at_the_defaults_three_rates_both_graphs(self):
        for rate in RATES:
            for tone in (4000.0, 0.0):
                result = first_lap_green(MultiTapDelay, rate=rate, tone=tone)
                self.assertTrue(result["passed"], (rate, tone, result))
        result = first_lap_green(MultiTapDelay, channels=1)
        self.assertTrue(result["passed"], result)

    def test_first_lap_over_modes_heads_and_time_stops(self):
        for mode in (1, 7, 9, 12):
            for heads in (3, 4, 8):
                for time_midi in (0, 127):
                    result = first_lap_green(
                        MultiTapDelay, tone=0.0,
                        midi={PATTERN_I: law_pattern_midi(mode),
                              HEADS_I: law_heads_midi(heads),
                              TIME_I: time_midi})
                    self.assertTrue(result["passed"],
                                    (mode, heads, time_midi, result))

    def test_laps_land_on_the_grid(self):
        for rate in RATES:
            lean = laps_reading(MultiTapDelay, rate=rate, tone=0.0)
            self.assertTrue(lean["passed"], (rate, lean))
            full = laps_reading(MultiTapDelay, rate=rate)
            self.assertTrue(full["passed"], (rate, full))
            self.assertEqual(full["arrivals"], 12)
        # A cell where the plain P 1000 / fs lands under P in float32 at
        # 44.1 kHz (K 3, Time MIDI 67, P 12 852): every onset on the grid.
        full = laps_reading(MultiTapDelay, rate=44100, feedback=0.6,
                            midi={TIME_I: 67})
        self.assertTrue(full["passed"], full)

    def test_late_heads_are_red_at_the_defaults(self):
        for rate in RATES:
            result = first_lap_green(LateHeads, rate=rate)
            self.assertFalse(result["passed"], rate)
        frames, _values, expected = first_lap(LateHeads)
        self.assertEqual(frames, [7201, 14401, 21600])
        self.assertEqual(expected, [7200, 14400, 21600])

    def test_long_lap_is_red_on_the_lap_clause(self):
        for rate in RATES:
            result = laps_reading(LongLap, rate=rate)
            self.assertFalse(result["passed"], rate)
            # Nine of twelve onsets late, in each lane.
            self.assertEqual(len(result["late"]), 18, rate)

    def test_the_t1_faults_are_not_on_the_surface(self):
        result = reach(LateHeads, head_offset_error)
        self.assertEqual(result["target"], (1, 1, 0))
        self.assertEqual(result["checked"], 9 * 17 + 7)
        result = reach(LongLap, lap_node_error)
        self.assertEqual(result["target"], 1)
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: first_lap_green(cls), label="T1")
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: laps_reading(cls), label="T1 laps")


# --------------------------------------------------------------------------
# T2 - one control moves the whole grid


def walk_reading(cls, heads, time_midis, rate=RATE):
    bad = []
    for midi in time_midis:
        frames, values, expected = first_lap(
            cls, rate=rate, tone=0.0, pattern=12,
            midi={HEADS_I: law_heads_midi(heads), TIME_I: midi})
        if frames != expected or values != [20000] * len(values):
            bad.append(midi)
    return {"passed": not bad, "bad": bad}


def span_reading(cls, heads, rate=RATE):
    landed = []
    for midi in (0, 127):
        frames, _values, _expected = first_lap(
            cls, rate=rate, tone=0.0, pattern=12,
            midi={HEADS_I: law_heads_midi(heads), TIME_I: midi})
        if not frames or frames[0] <= 0:
            return {"passed": False, "span": 0.0}
        landed.append(frames[0])
    span = landed[1] / float(landed[0])
    return {"passed": span >= 3.33, "span": span}


class T2OneControl(unittest.TestCase):
    TIMES = tuple(range(0, 128, 8)) + (127,)

    def test_time_walk_keeps_every_head_on_the_grid(self):
        for heads in (3, 8):
            result = walk_reading(MultiTapDelay, heads, self.TIMES)
            self.assertTrue(result["passed"], (heads, result))
        result = walk_reading(MultiTapDelay, 4, (0, 55, 127), rate=44100)
        self.assertTrue(result["passed"], result)

    def test_span_is_at_least_the_re201s(self):
        for heads, expected in ((3, 20.0), (8, 10.0)):
            result = span_reading(MultiTapDelay, heads)
            self.assertTrue(result["passed"], result)
            self.assertAlmostEqual(result["span"], expected, places=6)

    def test_short_tap_lap_is_red_at_the_defaults(self):
        for rate in RATES:
            self.assertFalse(first_lap_green(ShortTapLap, rate=rate)
                             ["passed"], rate)
        frames, _values, _expected = first_lap(ShortTapLap)
        self.assertEqual(frames, [7200, 14399, 21599])

    def test_narrow_time_span_is_red(self):
        for heads in (3, 8):
            result = span_reading(NarrowTime, heads)
            self.assertFalse(result["passed"], result)
            self.assertAlmostEqual(result["span"], 200.0 / 120.0, places=6)
        # The constructor's 150 ms still lands on the same frame.
        self.assertEqual(first_lap(NarrowTime)[0], [7200, 14400, 21600])

    def test_the_t2_faults_are_not_on_the_surface(self):
        result = reach(ShortTapLap, tap_lap_error)
        self.assertEqual(result["target"], -1)
        result = reach(NarrowTime, time_span_landed)
        self.assertEqual(result["target"], (120.0, 200.0))
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: walk_reading(cls, 3, (0, 64, 127)),
            label="T2 walk")
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: span_reading(cls, 3), label="T2 span")


# --------------------------------------------------------------------------
# T3 - a subset selector over the grid


def table_reading(cls, heads, modes=range(1, 13)):
    bad = []
    for mode in modes:
        frames, _values, _expected = first_lap(
            cls, tone=0.0, time_ms=20.0,
            midi={PATTERN_I: law_pattern_midi(mode),
                  HEADS_I: law_heads_midi(heads)})
        n1 = law_frames(20.0, RATE)
        sounded = tuple(f // n1 for f in frames if f > 0 and f % n1 == 0)
        if sounded != law_heads(mode, heads) or len(sounded) != len(frames):
            bad.append((mode, sounded))
    return {"passed": not bad, "bad": bad}


class T3Selector(unittest.TestCase):
    def test_s1_table_at_four_heads(self):
        result = table_reading(MultiTapDelay, 4)
        self.assertTrue(result["passed"], result)
        self.assertEqual(law_heads(10, 4), (1, 3, 4))

    def test_other_heads(self):
        result = table_reading(MultiTapDelay, 3, (8, 9, 10, 11, 12))
        self.assertTrue(result["passed"], result)
        self.assertEqual([law_heads(m, 3) for m in (8, 9, 10, 11)],
                         [(1,), (3,), (1, 3), (1, 2)])
        result = table_reading(MultiTapDelay, 8, (4, 12))
        self.assertTrue(result["passed"], result)

    def test_rotated_table_is_red_at_the_defaults(self):
        frames, _values, expected = first_lap(RotatedTable)
        self.assertEqual(frames, [7200])
        self.assertEqual(expected, [7200, 14400, 21600])
        for rate in RATES:
            self.assertFalse(first_lap_green(RotatedTable, rate=rate)
                             ["passed"], rate)

    def test_the_t3_fault_is_not_on_the_surface(self):
        result = reach(RotatedTable, head_table)
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: table_reading(cls, 4, (1, 7, 12)),
            label="T3")


# --------------------------------------------------------------------------
# T4 and T5 - one timbre per lap; darkening once per lap, and really there


def t4_green(result):
    return all(lane["present"] and lane["t4"] <= 0.5
               for lane in result.get("lanes", [result]))


def t5_green(result, tone, rate):
    top = 3620.0 if rate > 30000 else 2482.0
    for lane in result.get("lanes", [result]):
        clause1 = lane["present"] and lane["t5"] <= 0.5
        clause2a = lane["c2"] >= 1.0 and \
            abs(lane["c4"] - 3 * lane["c2"]) <= 2.0
        clause2b = tone > top + 1.0 or lane["q4"] >= 15.0
        if not (clause1 and clause2a and clause2b):
            return False
    return True


def tone_of(midi):
    return 800.0 * 20.0 ** (midi / 127.0)


def feedback_of(midi):
    return 0.95 * midi / 127.0


class T4T5Laps(unittest.TestCase):
    def test_at_the_row_cells(self):
        cells = [(RATE, fb, tone) for fb in (feedback_of(20), 0.45, 0.95)
                 for tone in (tone_of(0), tone_of(64), tone_of(126), 4000.0)]
        cells += [(44100, 0.45, 4000.0), (22050, 0.45, 4000.0),
                  (22050, 0.95, tone_of(0))]
        for rate, feedback, tone in cells:
            result = t45_reading(MultiTapDelay, rate=rate, feedback=feedback,
                                 tone=tone)
            self.assertTrue(t4_green(result), (rate, feedback, tone, result))
            self.assertTrue(t5_green(result, tone, rate),
                            (rate, feedback, tone, result))
            self.assertLess(result["t4"], 0.001)
            self.assertLess(result["t5"], 0.001)
            self.assertEqual(result["lap1"], [24000.0] * 3)

    def test_other_mode_and_heads_pairs(self):
        for heads, mode in ((4, 12), (4, 10), (8, 12)):
            result = t45_reading(MultiTapDelay, heads=heads, mode=mode)
            self.assertTrue(t4_green(result), (heads, mode, result))
            self.assertTrue(t5_green(result, 4000.0, RATE),
                            (heads, mode, result))

    def test_constructor_defaults_numbers(self):
        # A7.13 f: D2 3.00, D4 8.99 at the corner, D4 20.19 at 8 kHz.
        result = t45_reading(MultiTapDelay)
        self.assertAlmostEqual(result["c2"], 3.00, delta=0.05)
        self.assertAlmostEqual(result["c4"], 8.99, delta=0.05)
        self.assertAlmostEqual(result["q4"], 20.19, delta=0.05)

    def test_filtered_head_is_red_on_t4(self):
        clean = t45_reading(MultiTapDelay)
        result = t45_reading(FilteredHead)
        self.assertTrue(result["present"], result)
        self.assertGreater(result["t4"], 0.5, result)
        self.assertTrue(t4_green(clean))

    def test_front_filter_is_red_on_clause_2(self):
        result = t45_reading(FrontFilter)
        self.assertTrue(result["present"], result)
        self.assertLess(abs(result["c2"]), 0.5, result)
        self.assertLess(abs(result["q4"]), 0.5, result)
        self.assertFalse(t5_green(result, 4000.0, RATE))

    def test_emulated_per_head_darkening_is_red_on_clause_1(self):
        # Emulated on the rendered windows, as the dossier states it.
        result = t45_reading(MultiTapDelay, emulate=darken_head2_per_lap)
        self.assertGreater(result["t5"], 0.5, result)
        self.assertFalse(t5_green(result, 4000.0, RATE))

    def test_the_t4_t5_faults_are_not_on_the_surface(self):
        for faulted, flag in ((FilteredHead, "_plant_filtered_head"),
                              (FrontFilter, "_plant_front_filter")):
            result = reach(faulted,
                           lambda e, flag=flag: getattr(e, flag, False))
            self.assertIs(result["target"], True)
            self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: t4_green(t45_reading(cls)),
            label="T4")
        kit_faults.null_build_red(
            MultiTapDelay,
            lambda cls: t5_green(t45_reading(cls), 4000.0, RATE),
            label="T5")


# --------------------------------------------------------------------------
# Gate audit round 1: the routes the pack did not take, and both lanes


def reach_flag(faulted, name):
    return reach(faulted, flag(name))


class RoundOneRoutes(unittest.TestCase):
    """Items 1-4: a setting made on the wired instance before the first
    pull, a reset from the lean graph, a host's reset of the output, and
    several Repeat Tone crossings in one gap. Each is red on its plant,
    which reproduces the code of c80ca59."""

    def test_setting_before_the_first_pull_keeps_both_lanes_on_the_law(self):
        # Red on c80ca59: left [3 118, 9 241, 12 359, 18 482], right none.
        result = ctor_route(MultiTapDelay, (TIME_I, 96))
        self.assertEqual(result["law"], [9241, 18482, 27723])
        self.assertTrue(result["passed"], result)
        for rate in RATES:
            for move, pattern in (((TIME_I, 0), None), ((TIME_I, 127), None),
                                  ((HEADS_I, 127), 12)):
                result = ctor_route(MultiTapDelay, move, rate=rate,
                                    pattern=pattern)
                self.assertTrue(result["passed"], (rate, move, result))
        self.assertTrue(ctor_route(MultiTapDelay, (TIME_I, 96),
                                   channels=1)["passed"])

    def test_program_change_before_the_first_pull(self):
        for rate in RATES:
            for patch in (0, 2, 4):
                result = patch_route(MultiTapDelay, patch, rate=rate)
                self.assertTrue(result["passed"], (rate, patch, result))

    def test_primed_wire_plant_is_red_on_the_route_only(self):
        result = ctor_route(PrimedWire, (TIME_I, 96))
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["hits"][0][:4], [3118, 9241, 12359, 18482])
        self.assertEqual(result["hits"][1], [])
        self.assertFalse(patch_route(PrimedWire, 0)["passed"])
        # The control: from frame 256 the plant is on the law, as c80ca59
        # was, and so is the pack's build.
        self.assertTrue(ctor_route(PrimedWire, (TIME_I, 96),
                                   at=256)["passed"])
        self.assertTrue(ctor_route(MultiTapDelay, (TIME_I, 96),
                                   at=256)["passed"])
        self.assertTrue(first_lap_green(PrimedWire)["passed"])
        result = reach_flag(PrimedWire, "_plant_primed_wire")
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_reset_leaves_the_output_on_time(self):
        # Red on c80ca59 from patch 1, Tone at its out stop and a class
        # never wired: the dry at +256.
        for start in ("patch1", "tone127", "mix0", "full"):
            for rate, channels in ((RATE, 2), (RATE, 1), (44100, 2),
                                   (22050, 2)):
                result = reset_route(MultiTapDelay, start, rate, channels)
                self.assertTrue(result["passed"],
                                (start, rate, channels, result))

    def test_late_reset_plant_is_red(self):
        result = reset_route(LateReset, "patch1")
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["dry"], 256)
        result = reach_flag(LateReset, "_plant_late_reset")
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_a_host_reset_keeps_the_first_block(self):
        # Red on c80ca59: the 3 000 click at 2 744 on all three
        # interpreters (multitapdelay_stationC_hostreset.py).
        for rate in RATES:
            for channels in (2, 1):
                for patch in (None, 1):
                    result = host_reset_route(MultiTapDelay, patch, rate,
                                              channels)
                    self.assertTrue(result["passed"],
                                    (rate, channels, patch, result))
                result = host_reset_lines_route(MultiTapDelay, rate,
                                                channels)
                self.assertTrue(result["passed"], (rate, channels, result))

    def test_mixer_tail_plant_is_red(self):
        # Since re-audit fix round 1 every wiring is quiet, so no voice
        # holds the source's first block at construction and a host reset
        # that reaches the Mixer drops nothing there (c80ca59 put the 3 000
        # click at 2 744). Mid-stream it still empties both lines: the
        # click's heads are gone where the tail leaves them sounding.
        self.assertTrue(host_reset_route(MixerTail)["passed"])
        for channels in (2, 1):
            result = host_reset_lines_route(MixerTail, channels=channels)
            self.assertFalse(result["passed"], result)
            self.assertEqual(result["hits"], [[7000]] * channels)
        result = reach_flag(MixerTail, "_plant_mixer_tail")
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_tone_crossings_in_one_gap(self):
        # Red on c80ca59 at two crossings: heads at +4 088 for +4 344.
        for rate in RATES:
            for crossings in (1, 2, 3, 4):
                result = crossing_route(MultiTapDelay, crossings, rate)
                self.assertTrue(result["passed"], (rate, crossings, result))
        self.assertTrue(crossing_route(MultiTapDelay, 2,
                                       channels=1)["passed"])

    def test_priming_plug_plant_is_red(self):
        self.assertTrue(crossing_route(PrimingPlug, 1)["passed"])
        result = crossing_route(PrimingPlug, 2)
        self.assertFalse(result["passed"], result)
        self.assertEqual(result["hits"][0], [0, 4088, 8432, 12776])
        result = reach_flag(PrimingPlug, "_plant_priming_plug")
        self.assertEqual(result["checked"], 9 * 17 + 7)


class RoundOneLanes(unittest.TestCase):
    """Item 5: the lap and spectral readings read every lane, with a
    lane-1 plant and channel-different material."""

    def test_panned_laps_is_red_on_every_lane_reading(self):
        for rate in RATES:
            result = laps_reading(PannedLaps, rate=rate)
            self.assertFalse(result["passed"], (rate, result))
            self.assertEqual(len(result["late"]), 9, rate)
            self.assertFalse(t4_green(t45_reading(PannedLaps, rate=rate)))
            self.assertTrue(laps_reading(PannedLaps, rate=rate,
                                         channels=1)["passed"])
        result = reach_flag(PannedLaps, "_plant_panned_laps")
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_left_only_click(self):
        for rate in RATES:
            result = left_only_reading(MultiTapDelay, rate)
            self.assertTrue(result["passed"], (rate, result))
        result = left_only_reading(CrossedLaps)
        self.assertFalse(result["passed"], result)
        self.assertGreater(result["right"], 0)
        result = reach_flag(CrossedLaps, "_plant_crossed_laps")
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: left_only_reading(cls),
            label="left-only")


class RoundOneSurfaceLaws(unittest.TestCase):
    """Item 6: section 6's Feedback law and Repeat Tone's corner, each
    with a plant."""

    def test_lap_levels_follow_feedback(self):
        for rate in RATES:
            for tone in (4000.0, 0.0):
                result = level_reading(MultiTapDelay, rate, tone)
                self.assertTrue(result["passed"], (rate, tone, result))

    def test_lap_mix_one_is_red(self):
        for rate in RATES:
            result = level_reading(LapMixOne, rate)
            self.assertFalse(result["passed"], (rate, result))
            self.assertGreater(result["ratios"][0][1], 0.99)
        result = reach(LapMixOne, lap_mix_error)
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_repeat_tone_corner_is_3_db(self):
        for rate in RATES:
            for midi in (0, 64, 126):
                result = corner_reading(MultiTapDelay, rate, tone_of(midi))
                self.assertTrue(result["passed"], (rate, midi, result))
            self.assertTrue(corner_reading(MultiTapDelay, rate)["passed"])

    def test_tone_half_is_red(self):
        for rate in RATES:
            result = corner_reading(ToneHalf, rate)
            self.assertFalse(result["passed"], (rate, result))
            self.assertGreater(min(result["c2"]), 6.0)
        result = reach(ToneHalf, damping_error)
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_null_build_is_red(self):
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: level_reading(cls), label="levels")
        kit_faults.null_build_red(
            MultiTapDelay, lambda cls: corner_reading(cls), label="corner")


class RoundTwo(unittest.TestCase):
    """Gate audit round 2: a second `_resync` between two pulls, the rate
    floor, and T5 clause 1's plant built on the fix round 1 graph."""

    ROUTES = (("reset", "reset"), ("reset", "mix0"), ("mix0", "mix0"),
              ("reset", "reset", "reset"))

    def test_a_second_resync_in_one_gap_keeps_the_heads_on_time(self):
        # Red on d419ac4 (PullingResync below): click A's heads missing and
        # B's 256 frames early at two, 512 at three.
        for steps in self.ROUTES:
            for rate, channels in ((RATE, 2), (44100, 2), (22050, 2),
                                   (RATE, 1)):
                result = resync_route(MultiTapDelay, steps, rate=rate,
                                      channels=channels)
                self.assertTrue(result["passed"],
                                (steps, rate, channels, result))
            result = resync_route(MultiTapDelay, steps, start="lean")
            self.assertTrue(result["passed"], (steps, "lean", result))

    def test_pulling_resync_plant_is_red(self):
        # The control: one reset, and one return from Mix 0, are green on
        # the plant too; that is all fix round 1 tested.
        for steps in (("reset",), ("mix0",)):
            self.assertTrue(resync_route(PullingResync, steps)["passed"],
                            steps)
            self.assertTrue(resync_route(MultiTapDelay, steps)["passed"],
                            steps)
        for steps in self.ROUTES:
            for rate, channels in ((RATE, 2), (44100, 2), (22050, 2),
                                   (RATE, 1)):
                result = resync_route(PullingResync, steps, rate=rate,
                                      channels=channels)
                self.assertFalse(result["passed"],
                                 (steps, rate, channels, result))
        result = resync_route(PullingResync, ("reset", "reset"))
        # A (7 690) sounds dry only; B (8 036) and its heads 256 early.
        # reset() restores patch 0: Time MIDI 85, n1 7 129 at 48 kHz.
        n1 = law_landed(law_time_ms(85), 3, RATE)[0]
        self.assertEqual(n1, 7129)
        self.assertEqual(result["hits"][0],
                         [7690, 8036] + [8036 + k * n1 - 256
                                         for k in (1, 2, 3)])
        result = reach_flag(PullingResync, "_plant_pulling_resync")
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_rates_below_the_floor_are_refused(self):
        for rate in (8000, 11025, 12000, 12800, 12824):
            for channels in (2, 1):
                for options in ({}, {"time_ms": 20.0}):
                    with self.assertRaises(ValueError) as caught:
                        MultiTapDelay(Endless(silence(), rate, channels),
                                      sample_rate=rate, **options)
                    self.assertIn("12825 Hz", str(caught.exception))
            with self.assertRaises(ValueError):
                MultiTapDelay.create(Endless(silence(), rate, 2), rate)

    def test_time_20_ms_lands_on_the_grid_at_the_floor(self):
        for rate in (12825, 16000):
            for channels in (2, 1):
                for how in ("ctor", "macro"):
                    result = low_rate_first_lap(MultiTapDelay, rate, how,
                                                channels)
                    self.assertTrue(result["passed"],
                                    (rate, channels, how, result))
        self.assertEqual(low_rate_first_lap(MultiTapDelay, 12825, "ctor")
                         ["law"], [257, 514, 771])

    def test_no_rate_floor_plant_is_red(self):
        # d419ac4 at 12 800 Hz: heads at [512, 768, 1 024] for
        # [256, 512, 768]; at 12 000 Hz Time's low end raises from the node.
        for how in ("ctor", "macro"):
            result = low_rate_first_lap(NoRateFloor, 12800, how)
            self.assertFalse(result["passed"], (how, result))
            self.assertEqual(result["hits"], [[512, 768, 1024]] * 2)
            self.assertEqual(result["law"], [256, 512, 768])
            with self.assertRaises(ValueError) as caught:
                low_rate_first_lap(NoRateFloor, 12000, how)
            self.assertNotIn("12825 Hz", str(caught.exception))
        self.assertTrue(low_rate_first_lap(NoRateFloor, 16000,
                                           "ctor")["passed"])

    def test_head2_own_loop_is_red_on_clause_1(self):
        # Built, not emulated: lap 1 is the same for every head (the lap
        # nodes' dry pass), and head 2 darkens on its own after it.
        for rate in RATES:
            result = t45_reading(Head2OwnLoop, rate=rate)
            for lane in result["lanes"]:
                self.assertTrue(lane["present"], (rate, lane))
                self.assertEqual(lane["lap1"], [24000.0] * 3, rate)
                self.assertGreater(lane["t5"], 0.5, (rate, lane))
            self.assertFalse(t5_green(result, 4000.0, RATE), rate)
            self.assertTrue(t5_green(t45_reading(MultiTapDelay, rate=rate),
                                     4000.0, rate), rate)
        result = reach_flag(Head2OwnLoop, "_plant_head2_loop")
        self.assertIs(result["target"], True)
        self.assertEqual(result["checked"], 9 * 17 + 7)


# --------------------------------------------------------------------------
# Re-audit fix round 1: the pin at v0.6.3rc1, and the first block, the
# source's own buffers and Mix 0 (audit round 3's items 1-4)


class SteppedLaps(MultiTapDelay):
    """The cure retired at audiodsp v0.6.3rc1: with Repeat Tone in, the lap
    node handed the nearer edge of the stall window its Feedback sits in
    (`clear_of_stalls`), a Feedback nobody set (0.95 played as 0.950016)."""

    NAME = 'MultiTapDelay'

    def _refresh(self):
        MultiTapDelay._refresh(self)
        if self._lean:
            return
        excess = mtd.tone_excess(self._damping, self._sample_rate)[1]
        stepped = clear_of_stalls(self._feedback, excess)
        if stepped != self._feedback:
            self._feedback = stepped
            self._lap_mix = stepped
            self._fd.set(feedback=stepped, mix=stepped)


class BareAdapter(MultiTapDelay):
    """Mix 0 on the input adapter itself, without `_through`: a host's
    reset of the output reaches the adapter and drops what it holds."""

    NAME = 'MultiTapDelay'

    def _bypass(self):
        return self._adapter


#: One numpy-free script, run under CPython, MicroPython and CircuitPython:
#: the class after a route of calls made before the first pull, and after
#: an event between two pulls with sources whose buffers are not 256 frames,
#: every lane against the source and the dossier's head law. Three plants
#: put back ac2181f's code for the three causes. Each output line is
#: `PART|plant|route|rate|channels|samples wrong`.
ROUTES_MODULE = """from array import array

import audiocore                                    # noqa: E402
from audioeffects import rebuilt                    # noqa: E402

VENDOR = "PyDevices"

M = rebuilt.module_class("MultiTapDelay")
BLOCK = 256
FB_I = 3
MIX_I = 4
RATES = (48000, 44100, 22050)


class OldWiring(M):
    '''ac2181f's wiring: quiet only inside reset(), so a class wired at
    construction or by a Mix move holds the source's first block in the dry
    voice and on tap 1 until the first pull.'''

    NAME = 'MultiTapDelay'

    def _quiet_wiring(self):
        return self._resetting


class AdapterReset(M):
    '''ac2181f's reset: the input adapter owned with a reset, which drops
    what it holds of a source buffer.'''

    NAME = 'MultiTapDelay'

    def _build(self, *args, **kwargs):
        M._build(self, *args, **kwargs)
        self._resets[self._nodes.index(self._adapter)] = True


class SourceBypass(M):
    '''ac2181f's Mix 0: the output port on the borrowed source itself, past
    whatever the input adapter holds.'''

    NAME = 'MultiTapDelay'

    def _bypass(self):
        return self._source


PLANTS = {"clean": M, "oldwiring": OldWiring, "adapterreset": AdapterReset,
          "sourcebypass": SourceBypass}


def noise(channels, total):
    values = array("h", bytes(2 * total * channels))
    state = 987654
    for i in range(total):
        for c in range(channels):
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            tri = (i * (37 + 29 * c)) % 16001 - 8000
            values[i * channels + c] = tri + (state >> 8) % 8001 - 4000
    return values


def clicks(channels, total, where):
    values = array("h", bytes(2 * total * channels))
    for s, v in where:
        for c in range(channels):
            values[s * channels + c] = v
    return values


def source(values, rate, channels, frames):
    raw = audiocore.RawSample(values, sample_rate=rate,
                              channel_count=channels)
    if frames is None:
        return raw
    import audiofilters
    block = audiofilters.Filter(filter=None, mix=1.0,
                                buffer_size=frames * channels * 2,
                                sample_rate=rate, channel_count=channels)
    block.play(raw)
    return block


def samples(data):
    out = array("h")
    try:
        out.extend(memoryview(data).cast("h"))
    except (AttributeError, TypeError):
        import struct
        out.extend(struct.unpack("<%dh" % (len(data) // 2), data))
    return out


def pull_frames(e, frames):
    ch = e.channel_count
    out = array("h")
    while len(out) < frames * ch:
        out.extend(samples(bytes(audiocore.get_buffer(e.output)[1])))
    return out


#: Routes between construction and the first pull. "mix0 up" is a class
#: built at Mix 0 and turned up, which wires it.
ROUTES = ("none", "program_change(1)", "reset", "reset x2",
          "Mix 0 and back", "reset, Mix 0 and back", "mix0 up, reset")


def build(cls, src, rate, name):
    if name.startswith("mix0 up"):
        e = cls(src, sample_rate=rate, mix=0.0)
        e.set_macro(MIX_I, 22)
    else:
        e = cls(src, sample_rate=rate)
    for step in name.split(", "):
        if step in ("none", "mix0 up"):
            continue
        if step == "reset":
            e.reset()
        elif step == "reset x2":
            e.reset()
            e.reset()
        elif step == "Mix 0 and back":
            e.set_macro(MIX_I, 0)
            e.set_macro(MIX_I, 22)
        elif step == "program_change(1)":
            e.program_change(1)
        else:
            raise ValueError(step)
    return e


def law(where, n1, heads, unfed_before=0):
    want = {}
    for s, v in where:
        want[s] = v
        if s < unfed_before:
            continue
        for k in heads:
            want[s + k * n1] = want.get(s + k * n1, 0) + v
    return want


def judge(out, channels, frames, want):
    '''Samples wrong, over every lane: missing or wrong law frames plus
    non-zero frames the law does not name.'''
    wrong = 0
    for c in range(channels):
        got = {}
        for f in range(frames):
            v = out[f * channels + c]
            if v:
                got[f] = v
        wrong += len([s for s in want if s < frames and got.get(s) != want[s]])
        wrong += len([s for s in got if s not in want])
    return wrong


def part_firstdry(cls, label):
    for rate in RATES:
        for channels in (2, 1):
            values = noise(channels, 8 * BLOCK)
            for name in ROUTES:
                e = build(cls, source(values, rate, channels, BLOCK), rate,
                          name)
                window = min(e._n1, 2 * BLOCK)
                out = pull_frames(e, window)
                e.deinit()
                diff = len([i for i in range(window * channels)
                            if out[i] != values[i]])
                print("FIRSTDRY|%s|%s|%d|%d|%d" % (label, name, rate,
                                                   channels, diff))


def part_firstheads(cls, label):
    where = ((10, 20000), (300, 10000), (700, 5000))
    for rate in RATES:
        for channels in (2, 1):
            for name in ROUTES:
                total = 700 + 3 * (rate * 150 // 1000 + 1) + 4 * BLOCK
                values = clicks(channels, total, where)
                e = build(cls, source(values, rate, channels, BLOCK), rate,
                          name)
                e.set_macro(FB_I, 0)
                e.set_macro(MIX_I, 63.5)
                n1 = e._n1
                frames = 700 + 3 * n1 + 2 * BLOCK
                out = pull_frames(e, frames)
                e.deinit()
                wrong = judge(out, channels, frames,
                              law(where, n1, (1, 2, 3)))
                print("FIRSTHEADS|%s|%s|%d|%d|%d" % (label, name, rate,
                                                     channels, wrong))


def part_blocks(cls, label):
    where = ((8400, 20000), (8900, 10000), (10100, 5000))
    for rate, channels in ((48000, 2), (48000, 1), (22050, 1)):
        for frames_in in (256, 512, 100, None):
            for pulls in (31, 32):
                for event in ("none", "reset", "Mix 0 and back",
                              "Mix-0 run"):
                    total = 10100 + 3 * (rate * 150 // 1000 + 1) + 6 * BLOCK
                    values = clicks(channels, total, where)
                    e = cls(source(values, rate, channels, frames_in),
                            sample_rate=rate)
                    out = pull_frames(e, pulls * BLOCK)
                    if event == "reset":
                        e.reset()
                    elif event == "Mix 0 and back":
                        e.set_macro(MIX_I, 0)
                        e.set_macro(MIX_I, 22)
                    elif event == "Mix-0 run":
                        e.set_macro(MIX_I, 0)
                        out.extend(pull_frames(e, 4 * BLOCK))
                    e.set_macro(FB_I, 0)
                    e.set_macro(MIX_I, 63.5)
                    n1 = e._n1
                    span = 10100 + 3 * n1 + BLOCK - len(out) // channels
                    out.extend(pull_frames(e, span))
                    e.deinit()
                    frames = len(out) // channels
                    unfed = (pulls + 4) * BLOCK if event == "Mix-0 run" else 0
                    wrong = judge(out, channels, frames,
                                  law(where, n1, (1, 2, 3), unfed))
                    print("BLOCKS|%s|%s %d %s|%d|%d|%d"
                          % (label, frames_in or "raw", pulls, event, rate,
                             channels, wrong))


class QuietAlways(M):
    '''A wiring that primes zeros on every build, get_buffer or not: where
    get_buffer is left out nothing hands the primed zeros out, so the
    output opens with a silent block. It moves the first block, which is
    what the no-get_buffer words describe.'''

    NAME = 'MultiTapDelay'

    def _quiet_wiring(self):
        return True


PLANTS["quietalways"] = QuietAlways


class NoGetBuffer:
    '''audiocore without get_buffer, every other name passed through: what
    a patched CircuitPython board build that leaves it out gives the class.
    Installed in the two modules that look it up; the pulls below keep the
    real one.'''

    def __getattr__(self, name):
        if name == "get_buffer":
            raise AttributeError(name)
        return getattr(audiocore, name)


def use_audiocore(module):
    from audioeffects import _component
    top = __import__("audioeffects.rebuilt.multitapdelay")
    _component.audiocore = module
    top.rebuilt.multitapdelay.audiocore = module


#: Clicks for the no-get_buffer routes: two in the first block, one in
#: block 23 (the block before an event at block 24), two after block 24.
NG_CLICKS = ((10, 20000), (700, 9000), (6000, 8000), (6500, 7000),
             (9000, 5000))
NG_AT = 24 * BLOCK
#: route -> (constructor Mix, {block: [actions]}).
NG_ROUTES = (
    ("constructed", 1.0, {}),
    ("Mix 0 first, back at 24", 1.0, {0: ["mix0"], 24: ["back"]}),
    ("Mix 0 first, reset at 24", 1.0, {0: ["mix0"], 24: ["reset"]}),
    ("Mix 0 and back first", 1.0, {0: ["mix0", "back"]}),
    ("built at Mix 0, reset first", 0.0, {0: ["reset"]}),
    ("reset at 24", 1.0, {24: ["reset"]}),
    ("Mix 0 at 24, back at 48", 1.0, {24: ["mix0"], 48: ["back"]}),
)


def ng_act(e, action):
    if action == "mix0":
        e.set_macro(MIX_I, 0)
    elif action == "back":
        e.set_macro(MIX_I, 63.5)
    else:
        e.reset()
        e.set_macro(FB_I, 0)
        e.set_macro(MIX_I, 63.5)


def ng_law(route, pulls, n1a, n1b, frames):
    '''What the docstring says each route plays, every lane: `pulls` False
    is a build without get_buffer. n1a is the base as built, n1b after the
    route's events (a reset restores patch 0's Time).'''
    want = {}

    def put(f, v):
        if f < frames:
            want[f] = want.get(f, 0) + v

    def heads(o, v, n1, stop=frames):
        for k in (1, 2, 3):
            if o + k * n1 < stop:
                put(o + k * n1, v)

    late = not pulls
    for s, v in NG_CLICKS:
        block = s // BLOCK
        if route in ("constructed", "Mix 0 and back first"):
            put(s, v)
            heads(s, v, n1a)
        elif route.startswith("Mix 0 first"):
            if not late:
                put(s, v)
                if s >= NG_AT:
                    heads(s, v, n1b)
            elif block == 0:
                # the first block, held in the dry, plays at the return
                put(s + NG_AT, v)
                heads(s + NG_AT, v, n1b)
            elif block <= 24:
                # the Mix-0 run: one block early, no heads
                put(s - BLOCK, v)
            else:
                put(s, v)
                heads(s, v, n1b)
        elif route == "built at Mix 0, reset first":
            o = s + BLOCK if late else s
            put(o, v)
            heads(o, v, n1b)
        elif route == "reset at 24":
            put(s, v)
            if s >= NG_AT or (late and block == 23):
                heads(s, v, n1b)
            else:
                heads(s, v, n1a, NG_AT)
        else:                   # Mix 0 at 24, back at 48
            put(s, v)
            if s < NG_AT:
                heads(s, v, n1a, NG_AT)
                if late and block == 23:
                    heads(s + NG_AT, v, n1a)
            elif s >= 2 * NG_AT:
                heads(s, v, n1a)
    return want


def ng_run(cls, route, mix, plan, rate, channels, pulls):
    n1 = (rate * 150 + 500) // 1000
    frames = 2 * NG_AT + 3 * n1 + 2 * BLOCK
    values = clicks(channels, frames + 16 * BLOCK, NG_CLICKS)
    use_audiocore(audiocore if pulls else NoGetBuffer())
    try:
        e = cls(source(values, rate, channels, BLOCK), sample_rate=rate,
                feedback=0.0, mix=mix)
        n1a = e._n1
        out = array("h")
        block = 0
        while len(out) < frames * channels:
            for action in plan.get(block, ()):
                ng_act(e, action)
            out.extend(samples(bytes(audiocore.get_buffer(e.output)[1])))
            block += 1
        n1b = e._n1
        e.deinit()
    finally:
        use_audiocore(audiocore)
    return judge(out, channels, frames,
                 ng_law(route, pulls, n1a, n1b, frames))


def part_ng(cls, label, pulls):
    for route, mix, plan in NG_ROUTES:
        for rate, channels in ((48000, 2), (48000, 1), (22050, 1)):
            wrong = ng_run(cls, route, mix, plan, rate, channels, pulls)
            print("%s|%s|%s|%d|%d|%d" % ("GB" if pulls else "NOGB", label,
                                         route, rate, channels, wrong))


def main(args):
    '''Each argument is `plant,plant=part,part`.'''
    parts = {"firstdry": part_firstdry, "firstheads": part_firstheads,
             "blocks": part_blocks,
             "gb": lambda cls, label: part_ng(cls, label, True),
             "nogb": lambda cls, label: part_ng(cls, label, False)}
    for group in args:
        plants, names = group.split("=")
        for plant in plants.split(","):
            for part in names.split(","):
                parts[part](PLANTS[plant], plant)
    print("DONE")
"""

ROUTES_RUNNER = """import sys
sys.path.insert(0, "lib")
sys.path.insert(0, sys.argv[1])
import mtd_routes
mtd_routes.main(sys.argv[2:])
"""

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

#: The routes before the first pull that `_resync` or a wiring takes, and
#: the two that take neither (the controls).
RESYNC_ROUTES = ("reset", "reset x2", "Mix 0 and back",
                 "reset, Mix 0 and back", "mix0 up, reset")
ROUTE_CONTROLS = ("none", "program_change(1)")
ROUTE_RATES = (48000, 44100, 22050)
BLOCK_CASES = ((48000, 2), (48000, 1), (22050, 1))
#: Where a source's buffers leave the adapter holding frames at the event:
#: 512 after 31 blocks (256 held), 100 and one RawSample after 31 or 32.
HELD = (("512", 31), ("100", 31), ("100", 32), ("raw", 31), ("raw", 32))


def run_routes(binary, groups):
    """{(part, plant, route, rate, channels): samples wrong} from one run
    of `ROUTES_MODULE` under `binary`."""
    with tempfile.TemporaryDirectory() as directory:
        with open(os.path.join(directory, "mtd_routes.py"), "w") as handle:
            handle.write(ROUTES_MODULE)
        runner = os.path.join(directory, "run.py")
        with open(runner, "w") as handle:
            handle.write(ROUTES_RUNNER)
        env = dict(os.environ, MICROPYPATH="lib", GCOV_PREFIX=directory,
                   PYTHONDONTWRITEBYTECODE="1")
        argv = [binary] + ([] if binary == sys.executable
                           else ["-X", "heapsize=256M"])
        done = subprocess.run(argv + [runner, directory] + list(groups),
                              capture_output=True, text=True, cwd=ROOT,
                              env=env)
    lines = done.stdout.splitlines()
    if done.returncode != 0 or not lines or lines[-1] != "DONE":
        raise AssertionError("%s: %s" % (binary, done.stderr[-2000:]))
    out = {}
    for line in lines[:-1]:
        part, plant, name, rate, channels, wrong = line.split("|")
        out[(part, plant, name, int(rate), int(channels))] = int(wrong)
    return out


def red_cells(results, part, plant):
    return sorted(key[2:] for key, wrong in results.items()
                  if key[0] == part and key[1] == plant and wrong)


def current_native_interpreters():
    """{"micropython": path, "circuitpython": path} from the workspace's
    `bin/`, each the first whose provenance stamp contains `AUDIODSP_PIN`'s
    commit (None where no binary does), or None where there is no
    workspace `bin/` with its provenance tool above this checkout."""
    from tools import provenance_gate
    here = ROOT
    workspace = None
    for _up in range(5):
        here = os.path.dirname(here)
        if os.path.isdir(os.path.join(here, "bin")) and os.path.isfile(
                os.path.join(here, "tools", "provenance.py")):
            workspace = here
            break
    if workspace is None:
        return None
    bindir = os.path.join(workspace, "bin")
    tool = os.path.join(workspace, "tools", "provenance.py")
    pin = provenance_gate.audiodsp_pin()
    found = {}
    for family in ("micropython", "circuitpython"):
        found[family] = None
        names = sorted(name for name in os.listdir(bindir)
                       if name.startswith(family) and "." not in name)
        for name in names:
            path = os.path.join(bindir, name)
            done = subprocess.run(
                [sys.executable, tool, "check", path, "--source", "audiodsp",
                 "--contains", "audiodsp=%s" % pin], capture_output=True)
            if done.returncode == 0:
                found[family] = path
                break
    return found


def routes_module():
    """`ROUTES_MODULE` imported in this process, for its plants."""
    module = sys.modules.get("mtd_routes")
    if module is None:
        module = types.ModuleType("mtd_routes")
        sys.modules["mtd_routes"] = module
        exec(ROUTES_MODULE, module.__dict__)
    return module


def stall_cell(cls, rate=RATE, channels=2):
    """Feedback 0.5 by the constructor (Repeat Tone 800 Hz's k = 1 window),
    Time 20 ms, Mix 2, a 2 LSB DC for 1 s, then silence: (the Feedback the
    lap node is handed, the knob's own Feedback, tail_samples, frames from
    the input's end to the last non-zero sample, whether the last frame
    rendered is non-zero)."""
    frames = rate
    data = array("h", [2] * (frames * channels))
    effect = cls(Endless(data, rate, channels), sample_rate=rate,
                 feedback=0.5, tone_hz=800.0, time_ms=20.0, mix=2.0)
    declared = effect.tail_samples
    total = frames + declared + 8 * effect._lap
    out = pull(effect, total)
    handed = effect._feedback
    knob = effect.macro(FEEDBACK_I)
    effect.deinit()
    nz = np.nonzero(np.any(out != 0, axis=1))[0]
    last = int(nz[-1]) if len(nz) else -1
    return handed, knob, declared, last - frames + 1, last == total - 1


class ReauditRoundOne(unittest.TestCase):
    """Re-audit fix round 1 (2026-09-28): the class at audiodsp v0.6.3rc1,
    and the gate audit's round 3 items 1-4."""

    def test_the_feedback_is_handed_as_set(self):
        # Up to audiodsp v0.6.2 the lap node's loop low-pass could hold a
        # small value for ever a hair either side of 1 - 0.5 / k, and the
        # class handed it the nearer edge of the window instead: only
        # Feedback 127 (0.95, k = 10) ever moved, at every Repeat Tone
        # position and rate, to 0.950016. Since v0.6.3rc1 (#157) every
        # position is handed as set and the bound counts the landing's lap:
        # 167 laps at 0.95, Repeat Tone at the default (166 stepped).
        for rate in RATES:
            effect = MultiTapDelay(Endless(silence(), rate), sample_rate=rate)
            for midi in range(128):
                effect.set_macro(FEEDBACK_I, midi)
                want = min(0.95, effect.macro(FEEDBACK_I))
                self.assertEqual(effect._feedback, want, (rate, midi))
                self.assertEqual(effect._lap_mix, want, (rate, midi))
                self.assertIsInstance(effect.tail_samples, int)
            excess = mtd.tone_excess(effect._damping, rate)[1]
            self.assertEqual(effect._feedback, 0.95)
            self.assertEqual(laps_to_zero(0.95, excess), 167)
            # Planted: the retired stepping hands a Feedback nobody set.
            stepped = SteppedLaps(Endless(silence(), rate), sample_rate=rate)
            stepped.set_macro(FEEDBACK_I, 127)
            self.assertNotEqual(stepped._feedback, 0.95, rate)
            self.assertLess(abs(stepped._feedback - 0.95), 3e-5)
            self.assertEqual(laps_to_zero(stepped._feedback, excess), 166)
            memory = mtd.tone_excess(effect._damping, rate)[0]
            self.assertEqual(effect.tail_samples - stepped.tail_samples,
                             effect._lap + 1 + memory)

    def test_a_stall_window_cell_reaches_zero_at_the_feedback_set(self):
        # Feedback 0.5 with Repeat Tone at 800 Hz is inside a stall window
        # (the retired stepping moves it), and up to v0.6.2 the node held
        # this cell for ever there. Since v0.6.3rc1 it is handed as set and
        # the tail ends inside the bound. At v0.6.2 the same cell holds
        # past it (the pack's re-audit fix round 1 section, on
        # bin/micropython-062 and bin/circuitpython-062). SteppedLaps below
        # is red on the handed Feedback only: this cell's tail is far
        # inside the bound, and the tail reading's plant (NoTapLap) is in
        # ReauditRoundTwo, at a cell where the tail comes within a lap.
        for rate, channels in ((RATE, 2), (RATE, 1), (44100, 2),
                               (22050, 2)):
            handed, knob, declared, tail, held = stall_cell(
                MultiTapDelay, rate, channels)
            # The knob's 0.5 (0.49999999999999994 through the position) is
            # inside the window: the retired stepping moves it.
            self.assertLess(abs(knob - 0.5), 1e-15)
            self.assertNotEqual(clear_of_stalls(knob, mtd.tone_excess(
                nominal_damping_hz(800.0, rate), rate)[1]), knob)
            self.assertEqual(handed, knob, (rate, channels))
            self.assertFalse(held, (rate, channels))
            self.assertGreater(tail, 0, (rate, channels))
            self.assertLessEqual(tail, declared, (rate, channels))
        stepped = SteppedLaps(Endless(silence()), sample_rate=RATE,
                              feedback=0.5, tone_hz=800.0)
        self.assertNotEqual(stepped._feedback, stepped.macro(FEEDBACK_I))
        self.assertLess(abs(stepped._feedback - 0.5), 3e-5)

    def _judge_routes(self, results, native):
        """Items 1 and 2 on one interpreter's run."""
        for part in ("FIRSTDRY", "FIRSTHEADS"):
            self.assertEqual(red_cells(results, part, "clean"), [], part)
            cells = [key for key in results
                     if key[0] == part and key[1] == "clean"]
            self.assertEqual(len(cells), 7 * 3 * 2, part)
        # The plant: ac2181f's wiring. Every route that resyncs or wires
        # before the first pull loses the first block's heads, in every
        # lane; the controls stay green.
        self.assertEqual(
            red_cells(results, "FIRSTHEADS", "oldwiring"),
            sorted((name, rate, channels) for name in RESYNC_ROUTES
                   for rate in ROUTE_RATES for channels in (2, 1)))
        # And on a native interpreter, in mono, the dry's first block: all
        # 256 samples zero. The CPython shim copies the primed block, so
        # there the dry is kept (which is why this runs natively).
        dry = red_cells(results, "FIRSTDRY", "oldwiring")
        if native:
            self.assertEqual(dry, sorted(
                (name, rate, 1) for name in RESYNC_ROUTES
                for rate in ROUTE_RATES))
            for name, rate, channels in dry:
                self.assertEqual(results[("FIRSTDRY", "oldwiring", name,
                                          rate, channels)], 256)
        else:
            self.assertEqual(dry, [])

    def _judge_blocks(self, results):
        """Items 3 and 4 on one interpreter's run."""
        self.assertEqual(red_cells(results, "BLOCKS", "clean"), [])
        cells = [key for key in results
                 if key[0] == "BLOCKS" and key[1] == "clean"]
        self.assertEqual(len(cells), 3 * 4 * 2 * 4)
        # The adapter registered for a reset drops its frames at reset() and,
        # through the base's `_rejoin`, at every return from Mix 0 as well;
        # ac2181f, which had no `_rejoin`, lost them at reset() only. Mix 0
        # on the source itself skips them while Mix is 0. The 256-frame
        # control, which leaves the adapter holding nothing, stays green.
        for plant, events in (("adapterreset",
                               ("reset", "Mix 0 and back", "Mix-0 run")),
                              ("sourcebypass", ("Mix-0 run",))):
            want = sorted(("%s %d %s" % (buffers, pulls, event), rate,
                           channels)
                          for buffers, pulls in HELD for event in events
                          for rate, channels in BLOCK_CASES)
            self.assertEqual(red_cells(results, "BLOCKS", plant), want,
                             plant)

    def test_routes_before_the_first_pull_and_source_buffers_cpython(self):
        results = run_routes(sys.executable, (
            "clean,oldwiring=firstdry,firstheads",
            "clean,adapterreset,sourcebypass=blocks"))
        self._judge_routes(results, native=False)
        self._judge_blocks(results)

    def test_routes_before_the_first_pull_and_source_buffers_native(self):
        found = current_native_interpreters()
        if found is None:
            self.skipTest("no workspace bin/ above this checkout")
        for family, binary in sorted(found.items()):
            # A binary present but built before the pin renders a node the
            # pin does not name; that is a failure, not a skip.
            self.assertIsNotNone(binary, "no %s in the workspace bin/ "
                                 "contains AUDIODSP_PIN's audiodsp" % family)
            results = run_routes(binary, (
                "clean,oldwiring=firstdry,firstheads",
                "clean,adapterreset,sourcebypass=blocks"))
            self._judge_routes(results, native=True)
            self._judge_blocks(results)

    def test_the_route_plants_are_not_on_the_surface(self):
        module = routes_module()
        for faulted, reading, target in (
                (module.OldWiring, lambda e: e._quiet_wiring(), False),
                (module.AdapterReset,
                 lambda e: e._resets[e._nodes.index(e._adapter)], True),
                (module.SourceBypass, lambda e: e._bypass() is e._source,
                 True)):
            result = reach(faulted, reading)
            self.assertIs(result["target"], target, faulted.__name__)
            self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_mix_zero_hands_out_the_input_adapter(self):
        # A wire at Mix 0 through the adapter (behind `_through`): a bare
        # RawSample, byte for byte from the first frame, on the three rates
        # and both channel counts.
        for rate in RATES:
            for channels in (2, 1):
                data = probes.ramp_fs(4096, channels)
                raw = audiocore.RawSample(data, sample_rate=rate,
                                          channel_count=channels)
                effect = MultiTapDelay(raw, sample_rate=rate, mix=0.0)
                self.assertIs(_component.port_target(effect._output),
                              effect._through)
                out = pull(effect, 4096).reshape(-1)
                self.assertTrue(np.array_equal(
                    out, np.array(data, dtype=np.int64)), (rate, channels))
                effect.deinit()

    def test_a_host_reset_at_mix_zero_keeps_the_timeline(self):
        # 31 blocks at Mix 0 from a source in 512-frame buffers, so the
        # adapter holds 256 frames, then the host resets the output: the
        # click at 8 400 stays at 8 400 (the adapter itself as the port's
        # target puts it at 8 144).
        module = routes_module()
        for channels in (2, 1):
            values = module.clicks(channels, 20000, ((8400, 20000),))
            for cls, want in ((MultiTapDelay, 8400), (BareAdapter, 8144)):
                effect = cls(module.source(values, RATE, channels, 512),
                             sample_rate=RATE, mix=0.0)
                head = pull(effect, 31 * BLOCK)
                audiocore.reset_buffer(effect.output)
                out = np.concatenate([head, pull(effect, 2000)])
                effect.deinit()
                self.assertEqual(lane_hits(out), [[want]] * channels,
                                 (cls.__name__, channels))
        result = reach(BareAdapter, lambda e: e._bypass() is e._adapter)
        self.assertIs(result["target"], True)
        self.assertEqual(result["checked"], 9 * 17 + 7)


# --------------------------------------------------------------------------
# Re-audit fix round 2: the words for a build without get_buffer, and a
# plant for the tail reading


class NoTapLap(MultiTapDelay):
    """A tail bound one lap short: `tail_samples` leaves out the lap the
    tap node needs to read its line out (the re-refuter's plant)."""

    NAME = 'MultiTapDelay'

    def _tail_bound(self):
        bound = MultiTapDelay._tail_bound(self)
        return bound - self._lap if bound else bound


def tail_reading(cls, rate, channels, settings, level=32767):
    """DC at `level` for max(rate / 2, two laps), then silence: (tail_samples,
    frames from the input's end to the last non-zero sample, whether the
    last frame rendered is non-zero)."""
    probe = cls(Endless(silence(channels=channels), rate, channels),
                sample_rate=rate)
    for index, midi in settings:
        probe.set_macro(index, midi)
    hold = max(rate // 2, 2 * probe._lap)
    probe.deinit()
    effect = cls(Endless(array("h", [level] * (hold * channels)), rate,
                         channels), sample_rate=rate)
    for index, midi in settings:
        effect.set_macro(index, midi)
    declared = effect.tail_samples
    total = hold + declared + 3 * effect._lap + 2 * BLOCK
    out = pull(effect, total)
    effect.deinit()
    nz = np.nonzero(np.any(out != 0, axis=1))[0]
    last = int(nz[-1]) if len(nz) else -1
    return declared, max(0, last - hold + 1), last == total - 1


#: The route cells of `ROUTES_MODULE`'s gb / nogb parts.
NG_ROUTE_NAMES = ("constructed", "Mix 0 first, back at 24",
                  "Mix 0 first, reset at 24", "Mix 0 and back first",
                  "built at Mix 0, reset first", "reset at 24",
                  "Mix 0 at 24, back at 48")
NG_CASES = ((48000, 2), (48000, 1), (22050, 1))
NG_GROUPS = ("clean=gb,nogb", "oldwiring=gb", "quietalways=nogb")


class ReauditRoundTwo(unittest.TestCase):
    """Re-audit fix round 2 (2026-09-28): the gate audit's re-audit round 1
    items 1 and 2."""

    def _judge_ng(self, results):
        def cells(names):
            return sorted((name, rate, channels) for name in names
                          for rate, channels in NG_CASES)

        # The clean class plays what the docstring says, with get_buffer
        # and without it, on every route and in every lane.
        for part in ("GB", "NOGB"):
            self.assertEqual(len([key for key in results if key[0] == part
                                  and key[1] == "clean"]), 7 * 3, part)
            self.assertEqual(red_cells(results, part, "clean"), [], part)
        # With get_buffer the law is the source on time: ac2181f's wiring
        # breaks it wherever Mix goes to 0 before the first pull.
        self.assertEqual(red_cells(results, "GB", "oldwiring"), cells(
            ("Mix 0 first, back at 24", "Mix 0 first, reset at 24",
             "Mix 0 and back first")))
        # Without it the law is the one the words state (the Mix-0 run one
        # block early, the first block at the return with its heads, the
        # pending block's heads after a reset or a Mix-0 run): a wiring
        # that primes zeros on every build moves the first block, and is
        # red wherever the class was built above Mix 0.
        self.assertEqual(red_cells(results, "NOGB", "quietalways"), cells(
            name for name in NG_ROUTE_NAMES
            if name != "built at Mix 0, reset first"))

    def test_the_no_get_buffer_words_cpython(self):
        self._judge_ng(run_routes(sys.executable, NG_GROUPS))

    def test_the_no_get_buffer_words_native(self):
        found = current_native_interpreters()
        if found is None:
            self.skipTest("no workspace bin/ above this checkout")
        for family, binary in sorted(found.items()):
            self.assertIsNotNone(binary, "no %s in the workspace bin/ "
                                 "contains AUDIODSP_PIN's audiodsp" % family)
            self._judge_ng(run_routes(binary, NG_GROUPS))

    def test_quiet_always_is_not_on_the_surface(self):
        # Where get_buffer is left out, no macro position or patch makes
        # the clean class's wiring outside reset() quiet.
        module = routes_module()
        module.use_audiocore(module.NoGetBuffer())
        try:
            result = reach(module.QuietAlways, lambda e: e._quiet_wiring())
        finally:
            module.use_audiocore(audiocore)
        self.assertIs(result["target"], True)
        self.assertEqual(result["checked"], 9 * 17 + 7)

    def test_the_tail_reading_is_red_on_a_bound_one_lap_short(self):
        # The stall cell's tail sits far inside its bound, so the stall
        # test's tail half cannot see a bound one lap short. Full-scale DC
        # at the shortest lap, Feedback MIDI 96, Repeat Tone MIDI 126, comes
        # within one lap of it: inside the bound, and over it on NoTapLap.
        settings = ((TIME_I, 0), (FEEDBACK_I, 96), (MIX_I, 127),
                    (TONE_I, 126))
        for rate, channels in ((RATE, 2), (22050, 1)):
            declared, tail, held = tail_reading(MultiTapDelay, rate,
                                                channels, settings)
            self.assertFalse(held, (rate, channels))
            self.assertLessEqual(tail, declared, (rate, channels))
            short, planted, held = tail_reading(NoTapLap, rate, channels,
                                                settings)
            self.assertFalse(held, (rate, channels))
            self.assertEqual(planted, tail, (rate, channels))
            self.assertGreater(planted, short, (rate, channels))


# --------------------------------------------------------------------------
# The docstring's claims, each tied to the test that asserts it

#: (sentence, word for word as the class docstring has it, and the test
#: that asserts it). Every sentence in the class docstring that makes a
#: claim is here; one that could not be tied to a test was struck (the
#: trial fixer's dated note in the dossier lists them).
#: What the boards measured, marginal ms a block at 48 kHz stereo (audiodsp
#: v0.6.3). The budget is the G6 bar, 80 % of the block.
BOARD_COST = {
    "measured_at": "v0.6.3",
    "block_ms": 5.333,
    "budget_ms": 4.267,
    "S3": {3: 4.163, 4: 5.567},
    "P4": {3: 2.748, 4: 3.865},
}

CLAIMS = (
    ("Measured at v0.6.3, patch 4 costs 5.567 ms a block on the ESP32-S3, "
     "where a block lasts 5.333 ms, so it needs a P4-class board: the "
     "ESP32-P4 runs it in 3.865 ms.",
     "test_the_board_figures_are_the_table"),
    ("Patch 3 costs 4.163 ms on the ESP32-S3, inside the 4.267 ms budget, "
     "and may need a P4-class board too, especially when the board is "
     "running anything else.",
     "test_the_board_figures_are_the_table"),
    ("Time is the gap to head 1, landed on a whole frame, and head k sounds "
     "at exactly k times that gap.",
     "test_first_lap_over_modes_heads_and_time_stops"),
    ("Heads is how many heads the grid has, and the pattern repeats once per "
     "trip past the farthest of them.", "test_laps_land_on_the_grid"),
    ("Pattern picks which heads sound, from the twelve positions of the "
     "Roland RE-202's mode selector.", "test_s1_table_at_four_heads"),
    ("Its last position sounds every head on the grid, not the RE-202's "
     "unpublished positions.", "test_other_heads"),
    ("The lap is the farthest head on the grid, sounded or not, so heads "
     "past the ones a position sounds lengthen the lap without sounding.",
     "test_the_lap_is_the_farthest_head"),
    ("Feedback sends the pattern round again, each lap quieter.",
     "test_lap_levels_follow_feedback"),
    ("Repeat Tone darkens each lap a little more than the one before, once "
     "per lap, never once per head.", "test_at_the_row_cells"),
    ("Tilt leans the pattern's levels towards the near heads or the far "
     "ones.", "test_tilt_law"),
    ("Up to Mix 1 the dry passes at unity, and at Mix 2 the echoes play "
     "alone.", "test_the_mix_stops"),
    ("On CircuitPython alone, a stereo dry's right lane reads one LSB hot "
     "on source values within 32 LSB of the rails.",
     "test_the_right_lane_is_hot_only_on_circuitpython"),
    ("Mix 0 is a wire.", "test_mix_zero_is_a_wire"),
    ("Sync locks Time to Division of the host's beat, clamped to Time's "
     "span.", "test_sync_is_division_clamped_to_the_span"),
    ("With no host tempo, Time stays on the knob.",
     "test_sync_reads_the_transport_only_when_on"),
    ("Time runs from 20 to 400 ms, Heads from 3 to 8, Feedback from 0 to "
     "0.95 and Mix from 0 to 2.", "test_the_knob_spans"),
    ("`max_lap_ms` (1600 by default, 540 at least) caps the lap: where a "
     "grid would pass it, Time comes down to fit.",
     "test_constructor_options_clamp"),
    ("A click comes out on the frame it went in: there is no latency.",
     "test_click_latency_is_zero"),
    ("A one-channel source gets the same effect on its one channel.",
     "test_first_lap_at_the_defaults_three_rates_both_graphs"),
    ("The sample rate must be at least 12 825 Hz: below it the constructor "
     "raises `ValueError`.", "test_rates_below_the_floor_are_refused"),
    ("The lines are not fed while Mix is 0, so a return from Mix 0 starts "
     "both lines empty.", "test_mix_back_from_zero_starts_from_empty_lines"),
    ("`reset()` empties both lines and returns to patch 0.",
     "test_reset_empties_both_lines_and_returns_to_patch_0"),
    ("Neither a reset nor a trip to Mix 0 drops a frame of your source or "
     "plays one twice, whatever size of buffer it hands out.",
     "test_reset_and_mix_zero_keep_the_timeline"),
    ("`tail_samples` is an upper bound on how long the echoes take to reach "
     "exact zero once your input stops.", "test_tail_ends_inside_tail_samples"),
    ("The tail rings on while your source hands back nothing.",
     "test_the_tail_rings_on_while_the_source_is_dry"),
    ("A control that jumps makes the output step: move it in small steps "
     "from the host if you need it smooth.",
     "test_a_jumping_control_steps_the_output"),
)


#: Every source value within 64 LSB of either rail, and a few inside,
#: through the class at Mix 1 in one run of 256-frame blocks shorter than
#: the first head: prints `channels|left wrong|right wrong|worst|least |v|`.
HOT_SCRIPT = """
import audiocore
from array import array
from audioeffects.rebuilt.multitapdelay import MultiTapDelay
values = list(range(-32768, -32704)) + list(range(32704, 32768)) + [
    -20000, -1, 0, 1, 20000]
for channels in (2, 1):
    data = array("h", [0] * (len(values) * channels))
    for i in range(len(values)):
        for c in range(channels):
            data[i * channels + c] = values[i]
    source = audiocore.RawSample(data, sample_rate=48000,
                                 channel_count=channels)
    effect = MultiTapDelay(source, sample_rate=48000, mix=1.0)
    got = array("h")
    while len(got) < len(data):
        got.extend(memoryview(audiocore.get_buffer(effect.output)[1]).cast(
            "h") if hasattr(memoryview, "cast") else
            audiocore.get_buffer(effect.output)[1])
    lanes = [0, 0]
    worst = 0
    least = 99999
    for i in range(len(values)):
        for c in range(channels):
            d = got[i * channels + c] - values[i]
            if d:
                lanes[c] += 1
                worst = max(worst, abs(d))
                least = min(least, abs(values[i]))
    print("%d|%d|%d|%d|%d" % (channels, lanes[0], lanes[1], worst, least))
    effect.deinit()
print("DONE")
"""


def run_hot(binary):
    """{channels: (left wrong, right wrong, worst, least |v| wrong)}."""
    with tempfile.TemporaryDirectory() as directory:
        script = os.path.join(directory, "hot.py")
        with open(script, "w") as handle:
            handle.write(HOT_SCRIPT)
        env = dict(os.environ, MICROPYPATH="lib", GCOV_PREFIX=directory,
                   PYTHONDONTWRITEBYTECODE="1",
                   PYTHONPATH=os.path.join(ROOT, "lib"))
        argv = [binary] + ([] if binary == sys.executable
                           else ["-X", "heapsize=256M"])
        done = subprocess.run(argv + [script], capture_output=True,
                              text=True, cwd=ROOT, env=env)
    lines = done.stdout.splitlines()
    if done.returncode != 0 or not lines or lines[-1] != "DONE":
        raise AssertionError("%s: %s%s" % (binary, done.stdout[-1000:],
                                           done.stderr[-2000:]))
    out = {}
    for line in lines[:-1]:
        parts = [int(v) for v in line.split("|")]
        out[parts[0]] = tuple(parts[1:])
    return out


def _flat(text):
    return " ".join(text.split())


class TheClaims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        doc = _flat(MultiTapDelay.__doc__)
        tests = set()
        for value in globals().values():
            if isinstance(value, type) and issubclass(value,
                                                      unittest.TestCase):
                tests.update(n for n in dir(value) if n.startswith("test_"))
        rest = doc
        for sentence, test in CLAIMS:
            self.assertIn(sentence, doc, sentence)
            self.assertIn(test, tests, sentence)
            rest = rest.replace(sentence, " ")
        self.assertIn("**Limits shared by the family.**", doc)
        numbers = [w for w in rest.split() if any(c.isdigit() for c in w)]
        self.assertEqual(numbers, [])

    def test_the_board_figures_are_the_table(self):
        cost = BOARD_COST
        doc = _flat(MultiTapDelay.__doc__)
        dense = ("Measured at %s, patch 4 costs %.3f ms a block on the "
                 "ESP32-S3, where a block lasts %.3f ms, so it needs a "
                 "P4-class board: the ESP32-P4 runs it in %.3f ms." % (
                     cost["measured_at"], cost["S3"][4], cost["block_ms"],
                     cost["P4"][4]))
        far = ("Patch 3 costs %.3f ms on the ESP32-S3, inside the %.3f ms "
               "budget, and may need a P4-class board too, especially when "
               "the board is running anything else." % (
                   cost["S3"][3], cost["budget_ms"]))
        self.assertIn(dense, doc)
        self.assertIn(far, doc)
        # "needs", "runs it" and "inside" are what the table says.
        self.assertAlmostEqual(cost["budget_ms"], 0.8 * cost["block_ms"],
                               places=2)
        self.assertGreater(cost["S3"][4], cost["block_ms"])
        self.assertLess(cost["P4"][4], cost["budget_ms"])
        self.assertLess(cost["S3"][3], cost["budget_ms"])
        self.assertLess(cost["P4"][3], cost["budget_ms"])
        self.assertEqual(MultiTapDelay.PATCHES[4][0], "Eight Heads, Dense")
        self.assertEqual(MultiTapDelay.PATCHES[3][0],
                         "Four Heads, Far Loudest")

    def test_the_right_lane_is_hot_only_on_circuitpython(self):
        # The stock audiomixer's pan law: 32768 / 32767 on the right lane,
        # which moves the 63 values from 32 736 up (and down from -32 736,
        # the rail itself clipping) one LSB out. Mono and the left lane are
        # exact, and every other interpreter is exact.
        exact = {2: (0, 0, 0, 99999), 1: (0, 0, 0, 99999)}
        self.assertEqual(run_hot(sys.executable), exact)
        found = current_native_interpreters()
        if found is None:
            self.skipTest("no workspace bin/ above this checkout")
        for family, binary in sorted(found.items()):
            self.assertIsNotNone(binary, family)
            got = run_hot(binary)
            if family == "circuitpython":
                self.assertEqual(got[1], exact[1])
                left, right, worst, least = got[2]
                self.assertEqual((left, worst, least), (0, 1, 32736))
                self.assertEqual(right, 63)
            else:
                self.assertEqual(got, exact, family)

    def test_the_knob_spans(self):
        effect = MultiTapDelay(Endless(silence()), sample_rate=RATE)
        self.assertEqual(effect._max_lap_ms, 1600.0)
        for index, low, high in ((TIME_I, 20.0, 400.0),
                                 (FEEDBACK_I, 0.0, 0.95),
                                 (MIX_I, 0.0, 2.0)):
            effect.set_macro(index, 0)
            self.assertAlmostEqual(effect._value(index), low, places=9)
            effect.set_macro(index, 127)
            self.assertAlmostEqual(effect._value(index), high, places=9)
        effect.set_macro(HEADS_I, 0)
        self.assertEqual(effect._heads_count(), 3)
        effect.set_macro(HEADS_I, 127)
        self.assertEqual(effect._heads_count(), 8)

    def test_the_lap_is_the_farthest_head(self):
        # Mode 1 sounds head 1 alone. With Repeat Tone out (single-frame
        # laps) and the echoes alone, a click at frame 10 comes back at
        # 10 + n1 and then once per lap of K n1 (n1 = 960 at 20 ms), so the
        # heads it does not sound lengthen the lap.
        for heads, laps in ((3, (1, 4, 7)), (8, (1, 9))):
            effect = build(data=click(at=10), mix=2.0, feedback=0.5,
                           time_ms=20.0, tone_hz=0.0, pattern=1,
                           heads=heads)
            out = pull(effect, 10 + 960 * laps[-1] + 100)
            self.assertEqual(nonzero(out), [10 + 960 * k for k in laps],
                             heads)
            effect.deinit()

    def test_the_mix_stops(self):
        for channels in (2, 1):
            for mix in (0.35, 1.0):
                effect = build(data=click(at=10, channels=channels),
                               channels=channels, mix=mix)
                out = pull(effect, 7300)
                self.assertEqual(int(out[10, 0]), 20000, (channels, mix))
                effect.deinit()
            effect = build(data=click(at=10, channels=channels),
                           channels=channels, mix=2.0)
            out = pull(effect, 7300)
            self.assertEqual(nonzero(out)[0], 10 + 7200, channels)
            effect.deinit()

    def test_sync_is_division_clamped_to_the_span(self):
        # 1/1 at 30 bpm is 8 s, clamped to 400 ms; 1/32 at 600 bpm is
        # 12.5 ms, clamped to 20 ms; 1/4 at 120 bpm is 500 ms, over the top.
        for bpm, division, n1 in ((30.0, 15, 19200), (600.0, 0, 960),
                                  (120.0, 9, 19200), (100.0, 6, 14400)):
            effect = MultiTapDelay(
                Endless(silence()), sample_rate=RATE, division=division,
                transport=lambda bpm=bpm: (True, 0.0, bpm, 4, 4))
            effect.set_macro(SYNC_I, 127)
            self.assertEqual(effect._n1, n1, (bpm, division))
            effect.deinit()

    def test_reset_empties_both_lines_and_returns_to_patch_0(self):
        effect = build(data=click(), mix=1.0, feedback=0.9, time_ms=20.0)
        effect.program_change(3)
        pull(effect, 3000)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        self.assertEqual(int(np.abs(pull(effect, 20000)).max()), 0)

    def test_reset_and_mix_zero_keep_the_timeline(self):
        import lifecycle
        names = ("E1-reset@block", "E1-reset@part", "E5-mix0", "E9-src100",
                 "E9-src512", "E9-src1000", "E9-srcraw", "E10-reset",
                 "E10-mix0")
        for patch in (None, 1):
            events = dict((e.name, e) for e in
                          lifecycle.events(MultiTapDelay, patch))
            for channels in (2, 1):
                for name in names:
                    got = lifecycle.p1(MultiTapDelay, events[name], RATE,
                                       channels, patch, {})
                    self.assertIn(got, ("ok", "na"),
                                  (name, patch, channels))

    def test_the_tail_rings_on_while_the_source_is_dry(self):
        # The source hands back an empty buffer, done, from the third block
        # on; the heads and laps of a click it played before keep coming,
        # every pull a full block, on every lap of the lean graph.
        import lifecycle
        values = array("h", [0] * (BLOCK * 4))
        values[10] = 20000
        feed = lifecycle.Feed(values, RATE, 1, "256", loop=False)
        effect = MultiTapDelay(feed.port, sample_rate=RATE, time_ms=20.0,
                               mix=2.0, feedback=0.5, tone_hz=0.0)
        out = bytearray()
        for _ in range(2):
            out += bytes(audiocore.get_buffer(effect.output)[1])
        feed.port.play(feed.empty)
        for _ in range(40):
            chunk = bytes(audiocore.get_buffer(effect.output)[1])
            self.assertEqual(len(chunk), BLOCK * 2)
            out += chunk
        got = np.frombuffer(bytes(out), dtype="<i2")
        self.assertEqual([int(i) for i in np.nonzero(got)[0]],
                         [10 + 960 * k for k in range(1, 12)])
        effect.deinit()

    def test_a_jumping_control_steps_the_output(self):
        # The matrix's P5 at the defaults: Time to either stop, or a patch
        # change, steps the output past its bar within one block
        # (audiocomponents#117), where a control left alone does not.
        import lifecycle
        events = dict((e.name, e) for e in
                      lifecycle.events(MultiTapDelay, None))
        controls = {}
        try:
            for name in ("E4-m0=0", "E4-m0=127", "E6-p4"):
                got = lifecycle.p5(MultiTapDelay, events[name], RATE, 2,
                                   None, {}, controls)
                self.assertTrue(got.startswith("RED(step"), (name, got))
            self.assertEqual(lifecycle.p5(MultiTapDelay, events["E4-m7=0"],
                                          RATE, 2, None, {}, controls),
                             "ok")
        finally:
            for ctl in controls.values():
                ctl.close()


if __name__ == "__main__":
    unittest.main()
