"""`AutoPan` - a pan law under an LFO, not a Mixer panning input.

Dossier: `workspace docs/effects-internal/dossiers/AutoPan.md`, traits frozen
2026-09-08 at Station A **before this file existed**; Rate span re-frozen
2026-09-08 in the fix round (vision §7.2). Grade *design*: the three published
centre-attenuation conventions (3.01 / 4.5 / 6.02 dB), a per-sample oscillator,
and a mono wire.

**One processing node:** `source -> audiomath.Multiply`. The modulator is a
`synthio.Synthesizer` with two `Note`s (left / right gain) whose waveform is
one 256-frame period of the pan law. Rate is the notes' frequency, so the
pull is one block of oscillator, not a whole-period `RawSample`. Depth 0 is
`mix = 0`, the bit-exact wire (`audioif_multiply.c` wet/dry pair). A mono
source gets **no node** - `output` is the borrowed source.

The Mixer + `synthio.LFO` route the old class used is rejected: it is not a
published pan law, it is block-rate, and on CPython it does not move at all.

**Latency is zero at every setting.** No option adds delay. `tail_samples`
is 0. `capabilities` is `("tempo_sync",)`: Sync on reads `self._transport()`
and snaps Rate to tempo divisions; with no host transport Rate stays free.

**Portability: audioif.** Needs `audiomath`. A stock CircuitPython board
raises `ImportError` at construction.

**What the default surrenders:** Rate starts at 2 Hz, not a slow 0.05 Hz
wander — a 256-frame hold at 0.05 Hz reads under −80 dB, so A3's plant cannot
fire on the old floor. The oscillator is two `synthio.Note`s, which top out
at half scale (P12): hard-over is −6 dB vs the source. A mono source is a
wire.

**Cost:** one Multiply plus a 1500-point synthio pair. Palette: Multiply
**0.028 / 0.047** + extra synthio 1500 **0.263 / 0.472** + glue **0.0** →
**0.291 / 0.519 ms → P4 ≤ 6 %, S3 ≤ 10 %**. The old **1 % / 1 %** bar
counted Multiply only: the palette could not price a `synthio` source.
Quoted class ROW **2.5 % / 4.5 %**. No `" - lean"` patch.
"""

VENDOR = "PyDevices"

import math
from array import array

from . import _component

try:
    import audiomath
except ImportError:
    audiomath = None

import synthio


class AutoPan(_component.Component):
    """Auto-panner: constant-power / 4.5 dB / 6 dB pan laws under a
    per-sample LFO. `audioif` tier (`audiomath.Multiply`).

    Macros: Rate (2-20 Hz), Depth (0 is a wire), Shape (triangle to sine),
    Law (3.01-6.02 dB centre attenuation), Centre, Phase, Sync. Latency is
    **0 ms** at every setting; nothing here looks ahead.

    What the default surrenders: Rate starts at 2 Hz, not a slow 0.05 Hz
    wander — a 256-frame hold at 0.05 Hz reads under −80 dB, so A3's plant
    cannot fire on the old floor. The oscillator is two `synthio.Note`s,
    which top out at half scale (P12): hard-over is −6 dB vs the source. A
    mono source is a wire.
    """

    NAME = 'AutoPan'
    DISPLAY_NAME = 'Auto Pan'
    CATEGORIES = ('Modulation',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiomath",)

    CAPABILITIES = ("tempo_sync",)
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    #: One LFO period as a short waveform. Rate is the note frequency, not
    #: this length over f_s. 1500 makes the synthio DDS exact at 2 / 5 / 20 Hz
    #: on 48 kHz (375 × 4; A6 extremes land on samples).
    TABLE_FRAMES = 1500

    #: Centre attenuation of the constant-power law, 10*log10(2) dB.
    LAW_POWER_DB = 10.0 * math.log10(2.0)
    #: Centre attenuation of the linear / mono-safe law, 20*log10(2) dB.
    LAW_LINEAR_DB = 20.0 * math.log10(2.0)

    #: Beats per pan cycle when Sync is on, longest first. At 120 BPM these
    #: are 2-16 Hz, covering the Rate span without leaving it.
    SYNC_BEATS = (1.0, 0.5, 0.25, 0.125)

    MACRO_LABELS = ("Rate", "Depth", "Shape", "Law", "Centre", "Phase", "Sync")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "BIPOLAR",
        5: "BIPOLAR",
        6: "TOGGLE",
    }
    _MACRO_RANGES = (
        (2.0, 20.0, "log"),
        (0.0, 1.0),
        (0.0, 1.0),
        (LAW_POWER_DB, LAW_LINEAR_DB),
        (-1.0, 1.0),
        (-180.0, 180.0),
        (0.0, 1.0),
    )
    PATCHES = {
        0: ("Slow Sweep", (0, 127, 127, 0, 64, 64, 0)),
        1: ("Quarter Note", (0, 102, 0, 0, 64, 64, 127)),
        2: ("Wide Triangle", (38, 127, 0, 0, 64, 64, 0)),
        3: ("Narrow Drift", (0, 44, 127, 0, 64, 64, 0)),
        4: ("Mono-Safe Sweep", (38, 127, 127, 127, 64, 64, 0)),
        5: ("Offset Left", (0, 64, 127, 0, 38, 64, 0)),
        6: ("Fast Flutter", (69, 89, 0, 0, 64, 64, 0)),
        7: ("Quarter Offset", (0, 127, 127, 0, 64, 95, 127)),
    }

    def _build(self, rate=2.0, depth=1.0, shape=1.0, law_db=None,
               centre=0.0, phase=0.0, sync=0.0, patch=None):
        """No latency-adding option exists; `latency_samples` is 0 ms at
        48 kHz at every setting."""
        if law_db is None:
            law_db = type(self).LAW_POWER_DB
        self._table = None
        self._q15 = None
        self._wave_l = None
        self._wave_r = None
        self._synth = None
        self._note_l = None
        self._note_r = None
        self._node = None
        if self._channel_count == 1:
            self._output = self._source
        else:
            node = audiomath.Multiply(
                sample_rate=self._sample_rate,
                channel_count=self._channel_count, mix=1.0)
            node.play(self._source)

            def _release():
                stop = getattr(node, "deinit", None)
                if stop is not None:
                    stop()
                synth = self._synth
                self._synth = None
                self._note_l = None
                self._note_r = None
                if synth is not None:
                    closer = getattr(synth, "deinit", None)
                    if closer is not None:
                        closer()
                table = self._table
                self._table = None
                if table is not None:
                    closer = getattr(table, "deinit", None)
                    if closer is not None:
                        closer()

            self._node = self._own(node, deinit=_release)
            self._output = node
        self._init_macros((rate, depth, shape, law_db, centre, phase, sync),
                          patch)

    def _apply_macro(self, index, position):
        del position
        if self._node is None:
            if index in (0, 6) and self._macros[6] >= 0.5:
                self._transport()
            return
        self._rebuild_table()

    def _synced_rate(self, rate_hz):
        if self._macros[6] < 0.5:
            return rate_hz
        transport = self._transport
        playing, _position, bpm, _num, _den = transport()
        del playing
        bpm = float(bpm) if bpm else 120.0
        if transport is _component.static_transport:
            return rate_hz
        beats = type(self).SYNC_BEATS
        candidates = [bpm / (60.0 * b) for b in beats]
        nearest = candidates[0]
        best = abs(nearest - rate_hz)
        for hz in candidates[1:]:
            error = abs(hz - rate_hz)
            if error < best:
                nearest, best = hz, error
        return nearest

    def _macro_engineering(self):
        cls = type(self)
        rate_hz = _component.macro_value(cls._MACRO_RANGES[0], self._macros[0])
        depth = _component.macro_value(cls._MACRO_RANGES[1], self._macros[1])
        shape = _component.macro_value(cls._MACRO_RANGES[2], self._macros[2])
        law_db = _component.macro_value(cls._MACRO_RANGES[3], self._macros[3])
        centre = _component.macro_value(cls._MACRO_RANGES[4], self._macros[4])
        phase_deg = _component.macro_value(cls._MACRO_RANGES[5], self._macros[5])
        # MIDI 64 on a bipolar ±1 / ±180 span is 0.008 / 1.4°, not 0. Snap
        # that one step so constructor Centre/Phase 0 and patch 0 are the
        # same table (A6's hard-over lands on a sample).
        if abs(centre) < 1.0 / 64.0:
            centre = 0.0
        if abs(phase_deg) < 180.0 / 64.0:
            phase_deg = 0.0
        return (self._synced_rate(rate_hz), depth, shape, law_db, centre,
                phase_deg)

    def _bake_period(self, frames, depth, shape, law_db, centre, phase_deg):
        cls = type(self)
        forced = getattr(cls, "FORCED_EXPONENT", None)
        exponent = (law_db / cls.LAW_POWER_DB) if forced is None else forced
        two_pi = 2.0 * math.pi
        phase0 = phase_deg / 360.0
        wave_l = array("h")
        wave_r = array("h")
        interleaved = array("h")
        append_l = wave_l.append
        append_r = wave_r.append
        append = interleaved.append
        cap = getattr(cls, "DEPTH_CAP", None)
        if cap is not None and depth > cap:
            depth = cap
        never_zero = bool(getattr(cls, "NEVER_ZERO", False))
        for index in range(frames):
            phase = (index / float(frames) + phase0) % 1.0
            triangle = 1.0 - 4.0 * abs(phase - 0.5)
            sine = -math.cos(two_pi * phase)
            lfo = triangle + shape * (sine - triangle)
            pan = centre + depth * lfo
            if getattr(cls, "FAULT", None) == "mixer":
                pan = max(-1.0, min(1.0, pan))
                if pan >= 0.0:
                    left, right = 1.0, 1.0 - pan
                else:
                    left, right = 1.0 + pan, 1.0
            elif pan <= -1.0:
                left, right = 1.0, 0.0
            elif pan >= 1.0:
                left, right = 0.0, 1.0
            else:
                theta = (pan + 1.0) * (math.pi * 0.25)
                left = math.cos(theta) ** exponent
                right = math.sin(theta) ** exponent
            q_l = _q15(left)
            q_r = _q15(right)
            if never_zero:
                # synthio notes top out at half scale (P12); 1 LSB in the
                # waveform is 0 in the PCM and the plant would go green.
                floor = int(getattr(cls, "NEVER_ZERO_LSB", 16))
                if q_l < floor:
                    q_l = floor
                if q_r < floor:
                    q_r = floor
            append_l(q_l)
            append_r(q_r)
            append(q_l)
            append(q_r)
        return wave_l, wave_r, interleaved

    def _rebuild_table(self):
        if self._node is None:
            return
        rate_hz, depth, shape, law_db, centre, phase_deg = (
            self._macro_engineering())
        if depth <= 0.0:
            self._node.set(mix=0.0)
            return
        self._node.set(mix=1.0)
        hold = getattr(type(self), "HOLD", None)
        if hold:
            frames = int(self._sample_rate / rate_hz)
            frames = max(4, frames - (frames % 4))
            _wave_l, _wave_r, raw = self._bake_period(
                frames, depth, shape, law_db, centre, phase_deg)
            held = array("h")
            period = len(raw) // 2
            for index in range(period):
                src = min((index // hold) * hold, period - 1)
                held.append(raw[src * 2])
                held.append(raw[src * 2 + 1])
            self._q15 = held
            self._modulate_raw(held)
            return
        frames = type(self).TABLE_FRAMES
        wave_l, wave_r, interleaved = self._bake_period(
            frames, depth, shape, law_db, centre, phase_deg)
        self._q15 = interleaved
        self._wave_l = wave_l
        self._wave_r = wave_r
        self._modulate_synth(rate_hz, wave_l, wave_r)

    def _modulate_raw(self, values):
        import audiocore
        sample = audiocore.RawSample(
            values, sample_rate=self._sample_rate, channel_count=2)
        previous = self._table
        self._table = sample
        self._node.modulate(sample)
        if previous is not None:
            closer = getattr(previous, "deinit", None)
            if closer is not None:
                closer()

    def _modulate_synth(self, rate_hz, wave_l, wave_r):
        synth = self._synth
        if synth is None:
            synth = synthio.Synthesizer(
                sample_rate=self._sample_rate, channel_count=2)
            # CPython synthio pans +1 to the left column and -1 to the right
            # (scaled panning in synthio.py). Native builds match that pair.
            note_l = synthio.Note(
                frequency=rate_hz, waveform=wave_l, panning=1.0)
            note_r = synthio.Note(
                frequency=rate_hz, waveform=wave_r, panning=-1.0)
            synth.press((note_l, note_r))
            self._synth = synth
            self._note_l = note_l
            self._note_r = note_r
            self._node.modulate(synth)
            return
        self._note_l.waveform = wave_l
        self._note_r.waveform = wave_r
        self._note_l.frequency = rate_hz
        self._note_r.frequency = rate_hz


def _q15(gain):
    if gain <= 0.0:
        return 0
    if gain >= 1.0:
        return 32767
    return int(gain * 32767.0 + 0.5)
