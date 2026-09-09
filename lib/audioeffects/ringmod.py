"""`RingMod` — Bode multiplier-type ring, with a switching character.

Rebuilt from scratch for Phase 3 against
`workspace docs/effects-internal/dossiers/RingMod.md`, whose trait table was
frozen at Station A before this file existed. The old `modulation.py:RingMod`
is consulted only for the defects that dossier's section 7 names.

**What it sounds like.** The program is multiplied by a carrier. At Depth 1
the originals vanish and only the sum and difference remain. Depth 0.5 is
textbook AM; Depth 0 is a wire. *Multiplier* (the default) is Bode's
square-law ring: two sidebands. *Switching* is his chopper: odd harmonics of
the carrier, truncated below Nyquist. Frequency is the oscillator the 6401
never owned.

**Portability tier: audioif** (`REQUIRES = ("audiomath",)`). On a stock
CircuitPython board this module imports cleanly and construction raises
`ImportError`.

**Cost: one Multiply plus a 256-point synthio Note (not a period-length
RawSample).** The 2026-09-08 extra-source row priced a 1964-frame looping
table (and the fix round then capped that table at 24000 frames for M4's
2 Hz pair). Frequency is now `Note.frequency`, so the low end of the range
does not allocate a longer buffer. Palette: Multiply **0.028 / 0.047** +
extra synthio 256-point **0.317 / 0.408** + glue **0.0** →
**0.345 / 0.455 ms → P4 ≤ 7 %, S3 ≤ 9 %**. The old **3 % / 5 %** bar
used a 256-frame RawSample stand-in: the palette could not price a
`synthio` source. The **18 % / 52 %** bar counted the 1964-frame pull.
This is a cheaper implementation of the same effect (brief shape b1),
not a §7.2 redefinition. No `" - lean"` patch.

**What the default surrenders:** Default is the multiplier at Frequency
220 Hz, Depth 1, Mix 1 — not the switching standout and not W1's Shape 1.
At that default, 3·f₂+f₁ sits at **−92.2 dB** (1 s rect, 48 kHz), not
in W1's −9.5±3 dB window, so W1 is disconfirmed at the constructor
default. Wet RMS is **−9.03 dB** vs the program (M2 disconfirmed): the
Q15 product is −3.01 dB and the `synthio` voice sum (`>> 16`, A1/P12)
takes another 6 dB. Squelch, Threshold and Release do not move the
audio (M5 disconfirmed). Shape is a byte no-op until Character is
flipped. Switching products at Character 1 Shape 1 are not a
demonstrated row. Carrier Low's 5 Hz HPF is **not a demonstrated
claim** (M4 disconfirmed): a same-kind plant moves the reading by
**0.0022 dB** at Frequency 220 and by **8.6 dB** only at 2 Hz.

**Latency: zero samples, at every setting and every rate.** Nothing looks
ahead. No option adds latency (none of Frequency, Depth, Mix, Shape,
Balance, Squelch, or Character delay the dry path). `tail_samples` is 0.

**Disconfirmed, not dropped.** M2 (unity RMS via +3.01 dB wet makeup): Q15
carrier cannot take ×√2 without clipping, which fails M1. W4 (switching
unity RMS): peak-normalizing the Gibbs square to fit Q15 drops RMS; restoring
it saturates and fails W2. M5 (squelch kills carrier leak): Balance is DC
on the modulator, so a silent program is still a multiply-by-zero; there is
no carrier residual to gate. W1 at the constructor default (Character 0):
the switching products are absent — the row is disconfirmed there, not
demonstrated at Character 1. M4 (Carrier Low 5 Hz: 2 Hz carrier
8.6±1.5 dB below 200 Hz): the same-kind plant is inert at Frequency
220 (**0.0022 dB**) and only fires when the carrier is turned down
to 2 Hz (**8.6 dB**). Not a claim.

`capabilities = ()`: the carrier is an audio-rate input on the standout.
This class never reads `self._transport()`.
"""

VENDOR = "PyDevices"

from array import array
import math

from . import _component

try:
    import audiomath
except ImportError:                     # pragma: no cover - a stock board
    audiomath = None

import synthio


FREQ, DEPTH, MIX, SHAPE, BAL, PBAL, SQUELCH, THRESH, RELEASE, CLOW, PHASE, CHAR = range(12)

Q15 = 32767
#: One carrier period as a short waveform. Rate is Note.frequency, not
#: this length over f_s. 256 is one palette block (~0.10 ms on the P4 as
#: an extra source) and is why 2 Hz no longer asks for 24000 frames.
TABLE_FRAMES = 256
TARGET_FRAMES = TABLE_FRAMES
MAX_CARRIER_FRAMES = TABLE_FRAMES
MAKEUP_DB = 3.010299956639812
DEPTH_WIRE = 1e-4
NYQUIST_FRAC = 0.45


def _clamp(value, lo, hi):
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _q15(value):
    sample = int(round(value * Q15))
    if sample > Q15:
        return Q15
    if sample < -32768:
        return -32768
    return sample


def carrier_gain(freq_hz, corner_hz):
    """First-order high-pass amplitude at `freq_hz` for corner `corner_hz`."""
    freq_hz = abs(float(freq_hz))
    corner_hz = max(float(corner_hz), 0.0)
    if freq_hz < 1e-9:
        return 0.0
    return freq_hz / math.sqrt(freq_hz * freq_hz + corner_hz * corner_hz)


def bandlimited_odd(phase, freq_hz, sample_rate, shape):
    """Sine at `shape` 0; odd-harmonic chopper truncated below 0.45·f_s at 1."""
    sine = math.sin(phase)
    shape = _clamp(float(shape), 0.0, 1.0)
    if shape <= 1e-6:
        return sine
    nyquist = NYQUIST_FRAC * float(sample_rate)
    acc = 0.0
    harmonic = 1
    while harmonic * freq_hz < nyquist - 1e-9:
        acc += math.sin(harmonic * phase) / float(harmonic)
        harmonic += 2
    square = acc * 4.0 / math.pi
    return (1.0 - shape) * sine + shape * square


class RingMod(_component.Component):
    """Bode-style ring modulation. `audioif` tier: needs `audiomath`.

    **Latency is 0.** No lookahead. `tail_samples` is 0.

    Depth 0 and Mix 0 are a wire (`Multiply.mix = 0`), never a table held at
    32767. Frequency spans 0.1–8000 Hz and clamps below 0.45·f_s.

    **What the default surrenders:** Default is the multiplier at Frequency
    220 Hz, Depth 1, Mix 1 — not the switching standout and not W1's Shape 1.
    At that default, 3·f₂+f₁ sits at **−92.2 dB** (1 s rect, 48 kHz), not
    in W1's −9.5±3 dB window, so W1 is disconfirmed at the constructor
    default. Wet RMS is **−9.03 dB** vs the program (M2 disconfirmed): the
    Q15 product is −3.01 dB and the `synthio` voice sum (`>> 16`, A1/P12)
    takes another 6 dB. Squelch, Threshold and Release do not move the
    audio (M5 disconfirmed). Shape is a byte no-op until Character is
    flipped. Switching products at Character 1 Shape 1 are not a
    demonstrated row. Carrier Low's 5 Hz HPF is **not a demonstrated
    claim** (M4 disconfirmed): a same-kind plant moves the reading by
    **0.0022 dB** at Frequency 220 and by **8.6 dB** only at 2 Hz.
    """

    NAME = "RingMod"
    DISPLAY_NAME = "Ring Modulator"
    CATEGORIES = ("Modulation",)
    VERSION = "0.1.0"

    TIER = _component.AUDIOIF
    REQUIRES = ("audiomath",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    MACRO_LABELS = (
        "Frequency", "Depth", "Mix", "Shape", "Balance", "Program Bal",
        "Squelch", "Threshold", "Release", "Carrier Low", "Stereo Phase",
        "Character",
    )
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "BIPOLAR",
        5: "BIPOLAR",
        6: "TOGGLE",
        7: "UNIPOLAR",
        8: "UNIPOLAR",
        9: "UNIPOLAR",
        10: "BIPOLAR",
        11: "TOGGLE",
    }
    _MACRO_RANGES = (
        (0.1, 8000.0, "log"),
        (0.0, 1.0),
        (0.0, 1.0),
        (0.0, 1.0),
        (-1.0, 1.0),
        (-1.0, 1.0),
        (0.0, 1.0),
        (-72.0, 0.0),
        (5.0, 500.0, "log"),
        (2.0, 200.0, "log"),
        (-180.0, 180.0),
        (0.0, 1.0),
    )
    PATCHES = {
        0: ("Clean Ring", (87, 127, 127, 0, 64, 64, 127, 21, 64, 25, 64, 0)),
        1: ("Textbook AM", (46, 64, 127, 0, 64, 64, 127, 21, 64, 25, 64, 0)),
        2: ("Clangour", (108, 127, 127, 0, 64, 64, 127, 21, 64, 25, 64, 0)),
        3: ("Bell Strike", (117, 127, 89, 0, 64, 64, 127, 21, 64, 25, 64, 0)),
        4: ("Chopper", (108, 127, 127, 114, 64, 64, 127, 21, 64, 25, 64, 127)),
        5: ("Soft Chopper", (93, 127, 102, 44, 64, 64, 127, 21, 64, 25, 64, 127)),
        6: ("Detuned Ring", (87, 127, 127, 0, 73, 64, 0, 21, 64, 25, 64, 0)),
        7: ("Wide Ring", (77, 127, 127, 0, 64, 64, 127, 21, 64, 25, 95, 0)),
        8: ("Growl", (58, 76, 127, 0, 64, 64, 127, 21, 64, 25, 64, 0)),
    }

    FORCE_CHOPPER = False
    FORCE_SINE = False
    NO_MAKEUP = False
    FORCE_MAKEUP = False
    BYPASS_CARRIER_LOW = False
    OPEN_GATE = False
    ZERO_MOD = False
    HARD_CHOPPER = False
    SKIP_BALANCE = False

    def _build(self, frequency=220.0, depth=1.0, mix=1.0, shape=0.0,
               balance=0.0, program_bal=0.0, squelch=1.0, threshold_db=-60.0,
               release_ms=50.0, carrier_low_hz=5.0, stereo_phase=0.0,
               character=0.0, patch=None):
        self._synth = None
        self._note_l = None
        self._note_r = None
        self._carrier_frames = 0
        self._mul = self._own(
            audiomath.Multiply(
                mix=1.0,
                sample_rate=self._sample_rate,
                channel_count=self._channel_count),
            deinit=self._deinit_graph)
        self._mul.play(self._source)
        self._output = self._mul
        self._init_macros(
            (frequency, depth, mix, shape, balance, program_bal, squelch,
             threshold_db, release_ms, carrier_low_hz, stereo_phase,
             character),
            patch)

    def _deinit_graph(self):
        self._note_l = None
        self._note_r = None
        synth = getattr(self, "_synth", None)
        self._synth = None
        if synth is not None:
            release = getattr(synth, "release_all", None)
            if release is not None:
                release()
            closer = getattr(synth, "deinit", None)
            if closer is not None:
                closer()
        deinit = getattr(self._mul, "deinit", None)
        if deinit is not None:
            deinit()

    def _value(self, index):
        position = self._macros[index]
        # BIPOLAR 0–127 puts the panel centre at midi 64, which is 64/127
        # not 0.5. Without this snap, program_change(0) leaves Balance at
        # 0.007874 and M1's residuals rise to −36 dB on the frozen material.
        if index in (BAL, PBAL, PHASE) and abs(position * 127.0 - 64.0) < 0.51:
            position = 0.5
        return _component.macro_value(self._MACRO_RANGES[index], position)

    def _apply_macro(self, index, position):
        del position
        self._refresh()

    def _clamp_hz(self, freq):
        ceiling = float(self._sample_rate) * NYQUIST_FRAC
        freq = float(freq)
        if freq > ceiling:
            return ceiling
        if freq < 0.0:
            return 0.0
        return freq

    def _refresh(self):
        cls = type(self)
        freq = self._clamp_hz(self._value(FREQ))
        depth = self._value(DEPTH)
        mix = self._value(MIX)
        shape = self._value(SHAPE)
        balance = 0.0 if cls.SKIP_BALANCE else self._value(BAL)
        program_bal = self._value(PBAL)
        corner = self._value(CLOW)
        phase_deg = self._value(PHASE)
        switching = self._value(CHAR) >= 0.5
        if cls.FORCE_CHOPPER:
            switching = True
            shape = 1.0
        if cls.FORCE_SINE:
            switching = False
            shape = 0.0
        if not switching:
            shape = 0.0
        self._plant_chopper = bool(cls.FORCE_CHOPPER)
        self._plant_sine = bool(cls.FORCE_SINE)
        self._plant_flat_carrier = bool(cls.BYPASS_CARRIER_LOW)
        self._plant_hard_chopper = bool(cls.HARD_CHOPPER)
        self._plant_makeup = bool(cls.FORCE_MAKEUP)
        self._plant_zero_mod = bool(cls.ZERO_MOD)

        if depth <= DEPTH_WIRE or mix <= DEPTH_WIRE:
            self._mul.set(mix=0.0)
            return
        self._mul.set(mix=mix)
        self._rebuild_carrier(freq, depth, shape, program_bal, balance,
                              corner, phase_deg)

    def _rebuild_carrier(self, freq, depth, shape, program_bal, balance,
                         corner, phase_deg):
        cls = type(self)
        fs = int(self._sample_rate)
        channels = int(self._channel_count)
        frames = TABLE_FRAMES
        if cls.ZERO_MOD:
            zeros = array("h", [0] * frames)
            self._modulate_synth(max(freq, 1.0), zeros, zeros, channels)
            self._carrier_frames = frames
            return
        hpf = 1.0
        if freq >= 0.05 and not cls.BYPASS_CARRIER_LOW:
            hpf = carrier_gain(freq, corner)
        phase_r = 0.0 if channels == 1 else (
            float(phase_deg) * math.pi / 180.0)
        makeup = 1.0
        switching = self._value(CHAR) >= 0.5 or cls.FORCE_CHOPPER
        if cls.FORCE_SINE:
            switching = False
        if switching:
            if cls.FORCE_MAKEUP and not cls.NO_MAKEUP:
                makeup = 10.0 ** (MAKEUP_DB / 20.0)
        elif not cls.NO_MAKEUP:
            # Q15 product cannot exceed unity; FORCE_MAKEUP clips the table
            # (the M2 fault). The clean class leaves makeup at 1.
            if cls.FORCE_MAKEUP:
                makeup = 10.0 ** (MAKEUP_DB / 20.0)
        depth = _clamp(float(depth), 0.0, 1.0)
        dc = float(program_bal)
        bleed = float(balance)
        wave_l = array("h")
        wave_r = array("h")
        lefts = []
        rights = []
        peak = 1e-12
        for index in range(frames):
            if freq < 0.05:
                osc_l = 1.0
                osc_r = 1.0
            else:
                phase = 2.0 * math.pi * index / float(frames)
                if cls.HARD_CHOPPER:
                    osc_l = 1.0 if math.sin(phase) >= 0.0 else -1.0
                    osc_r = 1.0 if math.sin(phase + phase_r) >= 0.0 else -1.0
                else:
                    osc_l = bandlimited_odd(phase, freq, fs, shape)
                    osc_r = bandlimited_odd(phase + phase_r, freq, fs, shape)
                osc_l *= hpf
                osc_r *= hpf
            left = (1.0 - depth) + depth * osc_l
            lefts.append(left)
            if abs(left) > peak:
                peak = abs(left)
            if channels != 1:
                right = (1.0 - depth) + depth * osc_r
                rights.append(right)
                if abs(right) > peak:
                    peak = abs(right)
        scale = 1.0 / peak if peak > 1.0 else 1.0
        for left in lefts:
            wave_l.append(_q15(left * scale * makeup + dc + bleed))
        if channels != 1:
            for right in rights:
                wave_r.append(_q15(right * scale * makeup + dc + bleed))
        played = freq if freq >= 0.05 else 1.0
        self._modulate_synth(played, wave_l, wave_r, channels)
        self._carrier_frames = frames

    def _modulate_synth(self, freq, wave_l, wave_r, channels):
        synth = self._synth
        if synth is None:
            synth = synthio.Synthesizer(
                sample_rate=self._sample_rate, channel_count=channels)
            if channels == 1:
                note_l = synthio.Note(frequency=freq, waveform=wave_l)
                synth.press(note_l)
                self._note_l = note_l
                self._note_r = None
            else:
                # CPython synthio pans +1 to the left column and -1 to the
                # right (scaled panning in synthio.py). Native builds match.
                note_l = synthio.Note(
                    frequency=freq, waveform=wave_l, panning=1.0)
                note_r = synthio.Note(
                    frequency=freq, waveform=wave_r, panning=-1.0)
                synth.press((note_l, note_r))
                self._note_l = note_l
                self._note_r = note_r
            self._synth = synth
            self._mul.modulate(synth)
            return
        self._note_l.waveform = wave_l
        self._note_l.frequency = freq
        if self._note_r is not None:
            self._note_r.waveform = wave_r
            self._note_r.frequency = freq
