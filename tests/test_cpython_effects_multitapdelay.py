"""`MultiTapDelay`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/MultiTapDelay.md`
(frozen at anchor 02e7e0c, the Station A revision); its Tier 2 rows are
T1-T5. Each row here is the measurement at a few of the row's cells and the
same measurement shown red on a planted fault of the same kind, at the
constructor defaults. Every fault is shown unreachable from every macro
position and shipped patch, and every row's measurement is shown red on the
class built as a wire. The full spans, the three interpreters and the rates
live in the evidence pack, not in this file.

Every law a measurement checks against is written out here from the
dossier, never taken from the class: the whole-frame landing, the lap
clamp, S1's head sets, Tilt's line and the lap node's float32 hand-off.

The rebuild is parked (not in `rebuilt.ADOPTED`), so the class is reached by
`rebuilt.module_class("MultiTapDelay")`.

Two plants are built for real here that Station A emulated: T4's per-head
6 kHz low-pass (a second tap node for head 2 behind an
`audiofilters.Filter`) and T5 clause 2's compose-first build (a front
Filter into the tap node's own decay). T5 clause 1's plant, head 2
darkening on its own each lap, is still the dossier's emulation on the
rendered windows, said where it is.
"""

import math
import os
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                            # noqa: E402
import audiodelays                                          # noqa: E402
import audiofilters                                         # noqa: E402
import audiomixer                                           # noqa: E402
import audioroute                                           # noqa: E402
import synthio                                              # noqa: E402
import kit_faults                                           # noqa: E402
import kit_probes as probes                                 # noqa: E402
import audioeffects                                         # noqa: E402
from audioeffects import _component                         # noqa: E402
from audioeffects import rebuilt                            # noqa: E402
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
    Click 20 000, Feedback 0, Mix 2, Tilt 0, P + 512 frames."""
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
    if channels == 2 and nonzero(out, 1) != frames:
        frames = frames + [-1]
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
    """T1's lap clause: lean, the non-zero set against every arrival
    inside 4P + 512, exact; full, the onset pair at every arrival."""
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
    if tone <= 0.0:
        return {"passed": nonzero(out, 0) == arrivals,
                "arrivals": len(arrivals), "late": []}
    late = [a for a in arrivals
            if out[a, 0] == 0 or out[a - 1, 0] != 0]
    return {"passed": not late and len(arrivals) > 0, "late": late,
            "arrivals": len(arrivals)}


def spectra(out, n1, lap, heads, laps=4, size=4096):
    win = np.hanning(size)
    res = {}
    for n in range(1, laps + 1):
        for k in heads:
            a = (n - 1) * lap + k * n1
            seg = out[a - size // 2:a + size // 2, 0].astype(float)
            peak = float(np.abs(seg).max())
            mag = np.abs(np.fft.rfft(seg * win))
            res[(n, k)] = (20.0 * np.log10(np.maximum(mag, 1e-9)), peak, seg)
    return res


def t45_reading(cls, rate=RATE, feedback=0.45, tone=4000.0, heads=3,
                mode=7, midi=None, emulate=None):
    """T4 and T5 at one cell: click 24 000, Mix 2, Tilt 0, t1 200 ms,
    4096-point Hann windows at every arrival of laps 1-4. Returns the
    worst pairwise T4 spread, the worst clause-1 increment spread, the
    corner and 8/5 kHz D2/D4 of head 1, and whether every head sounded
    (every window non-zero), with the lap-1 peaks."""
    midi = dict(midi or {})
    midi.setdefault(MIX_I, 127)
    size = 4096
    effect = build(cls, data=click(24000), rate=rate, midi=midi,
                   time_ms=200.0, heads=heads, pattern=mode,
                   feedback=feedback, tone_hz=tone)
    selected = law_heads(mode, heads)
    n1, lap = law_landed(200.0, heads, rate)
    out = pull(effect, 4 * lap + size)
    effect.deinit()
    res = spectra(out, n1, lap, selected, size=size)
    if emulate is not None:
        res = emulate(res, rate)
    freqs = np.fft.rfftfreq(size, 1.0 / rate)
    band = (freqs >= 100.0) & (freqs <= 10000.0)
    i100 = int(np.argmin(np.abs(freqs - 100.0)))
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

    def dark(n, f):
        iq = int(np.argmin(np.abs(freqs - f)))
        inc = res[(n, h)][0] - res[(1, h)][0]
        return -float(inc[iq] - inc[i100])
    corner = min(tone, rate * 0.5 * _component.NYQUIST_MARGIN)
    top = 8000.0 if rate > 30000 else 5000.0
    return {"t4": t4, "t5": t5, "present": present,
            "lap1": [res[(1, k)][1] for k in selected],
            "c2": dark(2, corner), "c4": dark(4, corner),
            "q2": dark(2, top), "q4": dark(4, top)}


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
    (k n1 + 1.5) / P."""

    NAME = 'MultiTapDelay'

    def _tap_positions(self, selected, n1, lap):
        heads = lap // n1
        return tuple(1.0 if k == heads else (k * n1 + 1.5) / lap
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
    nested Mixer would reset the tap nodes' lines when it is played).
    Full graph only; the plant is read at Tone in."""

    NAME = 'MultiTapDelay'
    CORNER_HZ = 6000.0

    def _wire(self):
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
        self._head2.play(self._filter)
        self._tapnode.taps = self._other_taps()
        self._tapnode.play(split.tap(0))
        self._plugged = False
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
    node, whose own decay makes the laps. It decays and never darkens."""

    NAME = 'MultiTapDelay'

    def _wire(self):
        rate, channels = self._sample_rate, self._channel_count
        self._plant_front_filter = True
        self._filter = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                  self._hz(self._value(TONE_I))),
            mix=1.0, buffer_size=BLOCK * channels * 2, sample_rate=rate,
            channel_count=channels)
        self._filter.play(self._tap1)
        self._tapnode.decay = self._value(FEEDBACK_I)
        self._tapnode.play(self._filter)
        self._plugged = False
        _component.open_level_gates(self._mixer, self._mixer.voice,
                                    self._silence)
        self._mixer.voice[0].play(self._dry)
        self._mixer.voice[1].play(self._tapnode)

    def _refresh(self):
        MultiTapDelay._refresh(self)
        self._tapnode.decay = self._value(FEEDBACK_I)


class PrimingReset(MultiTapDelay):
    """The review's finding, planted: the base's `reset()`, whose patch-0
    restore re-plugs (or wires) the graph by priming a block of the
    borrowed source into the Splitter."""

    NAME = 'MultiTapDelay'

    def reset(self):
        _component.Component.reset(self)


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
    offset truncated from the position), less k n1."""
    rate = effect._sample_rate
    lap = int(rate / 1000.0 * effect._tap_ms)
    return tuple(int(lap * position) - k * effect._n1
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

    def test_parked_not_served(self):
        self.assertNotIn("MultiTapDelay", rebuilt.ADOPTED)
        self.assertIsNot(audioeffects.MultiTapDelay, MultiTapDelay)

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
        for start in ("patch1", "tone127", "mix0"):
            self.assertGreater(reset_pulls(PrimingReset, start), 0, start)

    def test_state_from_the_lean_graph(self):
        for channels in (2, 1):
            result = state_reading(MultiTapDelay, 1, channels)
            self.assertEqual(result["values"]["reset_residual_lsb"], 0,
                             result["red"])
            self.assertTrue(result["values"]["resumed"])

    def test_state_priming_plant_is_red(self):
        result = state_reading(PrimingReset, 1)
        self.assertGreater(result["values"]["reset_residual_lsb"], 0)

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
            self.assertEqual(len(result["late"]), 9, rate)

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
    return result["present"] and result["t4"] <= 0.5


def t5_green(result, tone, rate):
    clause1 = result["present"] and result["t5"] <= 0.5
    clause2a = result["c2"] >= 1.0 and abs(result["c4"] - 3 * result["c2"]) \
        <= 2.0
    top = 3620.0 if rate > 30000 else 2482.0
    clause2b = tone > top + 1.0 or result["q4"] >= 15.0
    return clause1 and clause2a and clause2b


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


if __name__ == "__main__":
    unittest.main()
