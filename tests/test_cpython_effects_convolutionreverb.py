"""`ConvolutionReverb`'s own invariant and planted-fault tests.

The dossier's Tier 2 rows are D1-D6. Each row here is the
measurement over a slice of the span the row quantifies over, the same
measurement red on the row's planted fault at the constructor defaults
(D1's at the measured-mode defaults), the fault shown out of reach of every
macro position and shipped patch, and the measurement red on the class
built as a wire (D2: on the class with its checks removed, since the wire
keeps the class's raise). Exhaustive spans and rates live in the evidence
pack, not in this file.

Every measurement here computes its reference itself - D1's direct sum and
its load gain, D5's Decay law from the seconds the test handed the
constructor - and never reads it back from the class. The M1 reference
uses numpy and runs on CPython only.

Fix round 1 (gate audit round 1, 2026-09-28) added four readings that can
fail where the frozen ones could not, each with a control that goes red on
it and passes the old reading: D1 at an interior trim where truncation and
rounding differ (`TrimRounded`), D2's allocation read as the node's
capacity through `load()` rather than `node.taps` (`ExtraPartition` in
measured mode), D5's law from the handed seconds (`AllocatedSeconds`), and
D6's absolute clause |wet/dry| <= 0.5 dB (`HotRoom`, a constant +3 dB).

Fix round 2 (gate audit round 2) took D5's law off the class's positions
too: the Decay and Predelay positions come from what the test handed the
instance (`handed_build`), with `DecayKeptSquared` and `DecayMidiSquared`
as the controls, red on the handed law at Decay 64/127 and green on the
law read back off `effect._macros`. It also pins two edges the docstring
now states: a negative `damping_hz` is out of circuit, and `impulse=b""`
holds one partition.

The re-audit's fix round 1 (gate audit round 3) added three checks, each
shown red on its plant: D5's Predelay control (`PredelayKeptSquared`, red
on the handed law at Predelay 64/127 and green read back), a NaN
`damping_hz` pinned out of circuit (`NanIsSpanBottom`), and `D6Balance`,
which pins the widest per-side balance the docstring prints to the room at
the cell the walk named (the fix-round-2 docstring, a figure 0.1 dB narrow
and `SideTilt` are red on it).

The re-audit's fix round 2 (gate audit, re-audit round 1) added three
more, each shown red: `D5SingleRoom`, which pins the single-Room figures
the docstring prints as floors to their named cells (the `1c9308b` words
"up to about 22 %" and a figure half a point off are red on it);
`D6OneSided`, which reads the one-sided example at the Rooms it names (red
with its seed 36 changed to 1); and a `set_macro` leg for D5's Predelay
control (`PredelayMidiSquared`, which passed the constructor-only test).
`D6Balance` now wants the class summary's floor with its rates.

The re-audit at audiodsp v0.6.3rc2 moved the class to the fixed
convolution node (audiodsp#165), and five tests that pinned a defect or a
figure of the old node went red there. Each is restated to assert the good
behaviour and shown red on a planted copy of the old one: the two room-move
tests on `ResetOnMove` (the node cleared after every re-synthesis, which
renders the v0.6.3rc1 node's bytes); `D6Balance` and `D6OneSided`, which
now pin each side's level (D6's clause 4, dossier section 3.6), on
`SideTilt`, `SideNudge` and the v0.6.2 words; and `D5SingleRoom` on the
v0.6.2 stereo figures. The reset test now covers the plain defaults too,
where `NoReset` was inert while the node emptied itself on a re-synthesis.

The re-audit's fix round 2 at v0.6.3rc2 pins the room-move paragraph to
the room (`RoomMoveWords`): the jump two moves before one pull make at the
cell the docstring names (red on `OneSynthesisPerBlock`, which gathers
them into one synthesis), the step one move takes on a low sine (red on the
figure moved), and a patch change held to the straight line (red on
`PatchPerKnob`, one synthesis a knob). The `1b3bb94` words, which printed
neither figure, are red on the first two.

The re-audit round 2 at v0.6.3rc2 parked the class on three of those
sentences, and re-audit fix round 1 after it restates the paragraph as a
rule with no mechanism in it: what holds after any number of moves, the two
conditions for the straight line (one room change between two pulls, and a
source that has not run dry part-way through a block since the last
`reset()`), and that anything else can jump. `RoomMoveWords` now reads each
of its sentences: the rule's legs (`OneSynthesisPerBlock` red on the pairs,
`RetryOnEmpty`, which never lets the node see the empty buffer, red on the
under-run), the dry wire after every pair and an under-run (`ResetOnMove`),
the Mix sentence (`MixOnePullLate`) and the reset sentence (`NoReset`). The
`cf17a88` words are red on all seven.

The audit after that round parked the class on four sentences that said
more than the node does with a source that comes up short, and re-audit
fix round 2 after the re-audit round 2 restates them, each read by a test
that is red on the `8a57282` words and on a plant: coming up short is an
empty buffer, one shorter than a frame or an error result
(`test_every_short_read_part_way_counts_as_coming_up_short`, `RetryOnShort`;
`RetryOnEmpty` is the clean class on the byte and error legs); a pull that
comes up short before it has a frame is 256 frames of silence and moves
the rest 256 frames later, and an error result's frames and a part frame
never reach the node (the dry test's source cases, `ResetOnMove` and
`KeepShortReads`); `reset()` silences `latency_samples` frames, none on the
empty impulse (`ResetSilentOnEmpty`, `NoReset`); and the tail is counted in
the frames the source hands (`test_the_tail_counts_the_frames_the_source_hands`,
`TailTwoShort`).

The trial of the second process (2026-09-29) made the class docstring the
player's text and tied each of its claims to a test through `CLAIMS`
(`TheClaims`). The module docstring no longer carries figures, so the tests
that parsed it hold their cells as constants here, and the two that pinned
struck figures (the jump two moves make, the step one move takes) are
gone; the fade, jump and short-read mechanisms stay pinned as tests, not
promises. New: a reset while the node holds part of a source buffer keeps
the whole frames it holds (`ReplugOnReset` red), the empty impulse's Mix
and reset do nothing (`ResetSilentOnEmpty` red), a host `reset_buffer`
drops what the node held, and what each knob does.
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


#: Each shipped patch's Decay and Predelay MIDI, copied from dossier
#: section 6's patch table, so a law over a patch never reads the class.
PATCH_DECAY_PREDELAY_MIDI = {
    0: (127, 0), 1: (38, 13), 2: (127, 76), 3: (102, 25),
    4: (102, 0), 5: (127, 38), 6: (0, 25), 7: (127, 0),
}


def handed_build(cls=None, rate=RATE, channels=2, **options):
    """`build`, keeping `effect.handed`: the [Decay, Predelay] positions
    this test handed the instance, from the constructor's arguments, every
    `set_macro` (MIDI / 127, both macros UNIPOLAR) and every
    `program_change` (the dossier's patch MIDI). D5's law takes these,
    never `effect._macros` or `get_macro` (fix round 2): a class that held
    a position other than the one it was handed would move a law read back
    from it (DecayKeptSquared, DecayMidiSquared, below)."""
    effect = build(cls, rate, channels, **options)
    handed = [float(options.get("decay", 1.0)),
              float(options.get("predelay", 0.0))]
    if options.get("patch") is not None:
        handed[:] = [m / 127.0 for m in
                     PATCH_DECAY_PREDELAY_MIDI[options["patch"]]]
    set_macro = effect.set_macro
    program_change = effect.program_change

    def spy_set(index, value, *args, **kwargs):
        set_macro(index, value, *args, **kwargs)
        if index == DECAY_I:
            handed[0] = value / 127.0
        elif index == PREDELAY_I:
            handed[1] = value / 127.0

    def spy_program(index, *args, **kwargs):
        program_change(index, *args, **kwargs)
        if index in PATCH_DECAY_PREDELAY_MIDI:
            handed[:] = [m / 127.0 for m in PATCH_DECAY_PREDELAY_MIDI[index]]

    effect.set_macro = spy_set
    effect.program_change = spy_program
    effect.handed = handed
    return effect


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


def balance(effect):
    """(L - R dB, pooled dB) of the room's own impulse: a 0 dBFS click at
    Mix 2, each side's energy summed over the loaded taps. It is what white
    noise reads per side in expectation (D6's Not claimed line; re-audit
    fix round 1). Mix is put back after."""
    taps = effect.node.taps
    out = at_mix(effect, 127, click(LATENCY + taps + 256, 2))
    ir = out[LATENCY:LATENCY + taps].astype(np.float64) / 32767.0
    energy = np.sum(ir * ir, axis=0)
    return (float(10 * np.log10(energy[0] / energy[1])),
            float(10 * np.log10(np.mean(energy))))


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


class TrimRounded(ConvolutionReverb):
    """D1's control for the truncation clause: the trim rounded to the
    nearest frame. At 0 and 10 ms the two agree, so only an interior trim
    (41.7 ms at 48 kHz, 3.3 ms at 44.1 and 22.05 kHz) can see it."""

    NAME = NAME

    def _trim_frames(self, start_ms):
        return int(round(start_ms * self._sample_rate / 1000.0))


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
    unnormalised room would have, which tracks the decay. The gain follows
    every re-synthesis, so a host walking Decay by `set_macro` sees it move
    (fix round 1: built once, it held the constructor's gain and a walk read
    a 0.010 dB spread)."""

    NAME = NAME

    def _gain_db(self):
        return 10.0 * np.log10(self._synthesis()[0] / 0.05)

    def _fault(self, node):
        return kit_faults.HiddenGain(node, self._gain_db())

    def _refresh(self):
        ConvolutionReverb._refresh(self)
        planted = getattr(self, "_planted", None)
        if planted is not None:
            planted.gain_db = self._gain_db()
            planted._gain = 10.0 ** (planted.gain_db / 20.0)


class HotRoom(_After):
    """D6's absolute clause: a room a constant +3 dB hot at every setting.
    The spread and rho clauses both pass it; only |wet/dry| <= 0.5 dB sees
    it."""

    NAME = NAME
    GAIN_DB = 3.0

    def _fault(self, node):
        return kit_faults.HiddenGain(node, self.GAIN_DB)


class _LeftGain(kit_faults.HiddenGain):
    """`kit_faults.HiddenGain` on the left channel only."""

    def _process(self, frames):
        out = frames.copy()
        out[0::self.channel_count] *= self._gain
        return out


class SideTilt(_After):
    """D6's balance disclosure: the left side 0.5 dB hot after the node, a
    balance fault the pooled clauses barely see (+0.25 dB)."""

    NAME = NAME
    GAIN_DB = 0.5

    def _fault(self, node):
        return _LeftGain(node, self.GAIN_DB)


class SideNudge(SideTilt):
    """D6 (4)'s fine control: the left side 0.05 dB hot after the node, ten
    times narrower than SideTilt and five times the 0.01 dB bar (re-audit
    fix round 1, audiodsp v0.6.3rc2)."""

    NAME = NAME
    GAIN_DB = 0.05


class ResetOnMove(ConvolutionReverb):
    """The v0.6.3rc1 node's room move, planted from the class side
    (re-audit fix round 1, audiodsp#163): the node cleared after every
    re-synthesis on a playing node, so the tail stops dead and the 256
    frames in flight come out as exact zero, dry included, at every Mix.
    `clear()` drops the history and the block in flight, which is what the
    old node's `synthesize()` ended in; the pack shows this plant renders
    the old node's bytes."""

    NAME = NAME

    def _refresh(self):
        before = self._loaded
        ConvolutionReverb._refresh(self)
        if before is not None and self._loaded != before:
            self._node.clear()


class AllocatedSeconds(ConvolutionReverb):
    """D5's control for a law that shares the class's inputs: the class
    keeps the allocation it holds (partitions x 256 / fs) as `seconds`, so
    every law over the allocation stretches to the partition edge. A law
    read from `effect.seconds` moves with it and stays green; a law from
    the seconds the test handed the constructor goes red (at 0.06 s: 64-Room
    mean +6.62 / +6.39 / +16.18 % at 48 / 44.1 / 22.05 kHz, audit round 1).
    It is inert at 0.08 s at 48 kHz, where 3 840 taps is a whole number of
    partitions."""

    NAME = NAME

    def _check_allocation(self, taps, seconds=None):
        ConvolutionReverb._check_allocation(self, taps, seconds)
        if seconds is not None:
            self._stretched = (self._partitions(taps) * 256
                               / float(self._sample_rate))

    def _refresh(self):
        stretched = getattr(self, "_stretched", None)
        if stretched is not None and not self._measured:
            self._seconds = stretched
        ConvolutionReverb._refresh(self)


class DecayKeptSquared(ConvolutionReverb):
    """D5's control for a law read back off the class's positions (fix
    round 2): the constructor's Decay kept squared. 0 and 1 are fixed
    points, so it is inert at Decay 1.0 and visible at 64/127: the
    re-refuter read 1.907 % on a law from `effect._macros` (green) and
    -12.781 % on the handed law at 48 kHz (-13.147 % at 22.05 kHz)."""

    NAME = NAME

    def _init_macros(self, values, patch=None):
        values = list(values)
        values[DECAY_I] = values[DECAY_I] ** 2
        ConvolutionReverb._init_macros(self, tuple(values), patch)


class DecayMidiSquared(ConvolutionReverb):
    """The same control through `set_macro`: a Decay move is kept
    squared."""

    NAME = NAME

    def set_macro(self, index, value, channel=0, note_id=-1,
                  sample_position=0):
        ConvolutionReverb.set_macro(self, index, value, channel, note_id,
                                    sample_position)
        if index == DECAY_I:
            self._macros[DECAY_I] = self._macros[DECAY_I] ** 2
            self._apply_macro(DECAY_I, self._macros[DECAY_I])


class PredelayKeptSquared(ConvolutionReverb):
    """D5's Predelay control (re-audit fix round 1, from the round-3
    audit's item 3): the constructor's Predelay kept squared. It is
    Predelay's shape of DecayKeptSquared, and it passed every D5 test
    before this one. At Predelay 64/127, Decay 127, Damping out, Diffusion
    0, at audiodsp v0.6.3rc2 (re-audit fix round 2 there), it reads worst
    +6.540 % (mean +5.194 %) on the handed law at 48 kHz and +7.214 %
    (+5.197 %) at 22.05 kHz, and +1.296 / -2.360 % on a law read back off
    the class; the clean class reads +1.376 / +2.322 %. (At v0.6.2, before
    each side of a stereo room was scaled on its own: +6.518 / +7.244 %,
    clean +1.375 / +2.347 %.)"""

    NAME = NAME

    def _init_macros(self, values, patch=None):
        values = list(values)
        values[PREDELAY_I] = values[PREDELAY_I] ** 2
        ConvolutionReverb._init_macros(self, tuple(values), patch)


class PredelayMidiSquared(ConvolutionReverb):
    """The same control through `set_macro` (re-audit fix round 2, from
    the re-audit round-1 audit's item 5): a Predelay move is kept squared,
    the constructor's Predelay held exactly. It passed the Predelay test
    while that test's clean leg went through the constructor. At
    `set_macro` Predelay 64, Decay 127, Damping out, Diffusion 0 it reads
    what PredelayKeptSquared does at audiodsp v0.6.3rc2: worst +6.540 % on
    the handed law at 48 kHz and +7.214 % at 22.05 kHz, clean +1.376 /
    +2.322 % by this route too (v0.6.2: +6.518 / +7.244 %)."""

    NAME = NAME

    def set_macro(self, index, value, channel=0, note_id=-1,
                  sample_position=0):
        ConvolutionReverb.set_macro(self, index, value, channel, note_id,
                                    sample_position)
        if index == PREDELAY_I:
            self._macros[PREDELAY_I] = self._macros[PREDELAY_I] ** 2
            self._apply_macro(PREDELAY_I, self._macros[PREDELAY_I])


class NanIsSpanBottom(ConvolutionReverb):
    """The damping pin's control: a NaN `damping_hz` taken as the 500 Hz
    stop instead of out of circuit, which is what the docstring said of
    NaN before it named it."""

    NAME = NAME

    def _build(self, *arguments, **options):
        hz = options.get("damping_hz", 6000.0)
        if hz != hz:
            options["damping_hz"] = 100.0
        ConvolutionReverb._build(self, *arguments, **options)


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


class _PullHook(kit_faults.HiddenGain):
    """A 0 dB `HiddenGain` (a gain of exactly 1.0, so every frame passes
    unchanged) that tells its owner a pull is about to happen."""

    def __init__(self, source, owner):
        kit_faults.HiddenGain.__init__(self, source, 0.0)
        self._owner = owner

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        self._owner._flush()
        return kit_faults.HiddenGain._get_buffer(
            self, single_channel_output, audio_channel)


class OneSynthesisPerBlock(ConvolutionReverb):
    """The two-move test's control (re-audit fix round 2 at audiodsp
    v0.6.3rc2): room moves that land between two pulls are gathered into
    one synthesis at the next pull. It is what the class would do with a
    hook at the block edge, and what a node that kept fading from the room
    that played would render (the node ask): the block starts on that
    room, not on the room before the last move, which is where the node at
    v0.6.3rc2 starts it. Two or more changes before one pull then read like
    one, on the straight line from the old room to the new, and the
    docstring's jump is gone (the rule test's pairs too)."""

    NAME = NAME

    def _build(self, *arguments, **options):
        self._hooked = False
        ConvolutionReverb._build(self, *arguments, **options)
        self._pending = False
        self._output = _PullHook(self._node, self)
        self._hooked = True

    def _refresh(self):
        if not self._hooked:
            ConvolutionReverb._refresh(self)
            return
        self._pending = True
        self._node.set(mix=self._value(MIX_I) * 0.5)

    def _flush(self):
        if self._pending:
            self._pending = False
            ConvolutionReverb._refresh(self)


class PatchPerKnob(ConvolutionReverb):
    """The patch-change test's control: a patch change after construction
    applied one knob at a time, one synthesis per room knob, as five moves
    before one pull."""

    NAME = NAME

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        patch = type(self).PATCHES.get(index)
        if patch is None or self._deferred:
            ConvolutionReverb.program_change(self, index, channel, note_id,
                                             sample_position)
            return
        for macro, value in enumerate(patch[1]):
            self.set_macro(macro, value)


class _RetrySource:
    """The class's source behind a proxy that never hands the node an
    empty buffer: an empty read is followed at once by another."""

    def __init__(self, inner):
        self.inner = inner
        for name in ("sample_rate", "channel_count", "bits_per_sample",
                     "samples_signed"):
            setattr(self, name, getattr(inner, name))

    def swap(self, source):
        self.inner.swap(source)

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self.inner._reset_buffer(single_channel_output, audio_channel)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        for _ in range(8):
            result, data = self.inner._get_buffer(single_channel_output,
                                                  audio_channel)
            if len(data):
                break
        return result, data


class RetryOnEmpty(ConvolutionReverb):
    """The under-run leg's control (re-audit fix round 1 after the re-audit
    round 2 at audiodsp v0.6.3rc2): the class pulls again when its source
    hands back an empty buffer, so the node never returns a short block and
    stays at its block edge. A move after an under-run then fades over the
    whole block, as if the source had never run dry."""

    NAME = NAME

    def _build(self, *arguments, **options):
        self._source = _RetrySource(self._source)
        ConvolutionReverb._build(self, *arguments, **options)


class _RetryShortSource(_RetrySource):
    """`_RetrySource` for every short read the binding stops on: an error
    result, or a buffer shorter than one frame."""

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        width = 2 * self.channel_count
        for _ in range(8):
            result, data = self.inner._get_buffer(single_channel_output,
                                                  audio_channel)
            if result != audiocore.GET_BUFFER_ERROR and len(data) >= width:
                break
        return result, data


class RetryOnShort(ConvolutionReverb):
    """The short-read legs' control (re-audit fix round 2 after the re-audit
    round 2 at audiodsp v0.6.3rc2): the class pulls again on every short
    read the binding stops on (`Convolver.c:278` at 0d35a90), an empty
    buffer, one shorter than a frame or an error result, so the node never
    returns a short block. A move after any of them then fades over the
    whole block. `RetryOnEmpty`, which tests only for an empty buffer, is
    the clean class on the byte and error legs."""

    NAME = NAME

    def _build(self, *arguments, **options):
        self._source = _RetryShortSource(self._source)
        ConvolutionReverb._build(self, *arguments, **options)


class _KeepShortSource(_RetrySource):
    """The class's source behind a proxy that hands the node what the
    binding would drop: an error result's frames as plain data, and a
    part frame at the end of a buffer padded with zero bytes to a whole
    frame."""

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        result, data = self.inner._get_buffer(single_channel_output,
                                              audio_channel)
        data = bytes(data)
        width = 2 * self.channel_count
        if len(data) > width and len(data) % width:
            data += bytes(width - len(data) % width)
        if result == audiocore.GET_BUFFER_ERROR:
            result = audiocore.GET_BUFFER_MORE_DATA
        return result, memoryview(data)


class KeepShortReads(ConvolutionReverb):
    """The whole-frames sentence's control: the part frame and the error
    result's frames reach the node (`_KeepShortSource`)."""

    NAME = NAME

    def _build(self, *arguments, **options):
        self._source = _KeepShortSource(self._source)
        ConvolutionReverb._build(self, *arguments, **options)


class _SilentBlock(kit_faults.HiddenGain):
    """A 0 dB pass-through that, once armed, answers one pull with a
    256-frame block of silence without pulling what is behind it."""

    def __init__(self, source):
        kit_faults.HiddenGain.__init__(self, source, 0.0)
        self.armed = False

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        if self.armed:
            self.armed = False
            return (audiocore.GET_BUFFER_MORE_DATA,
                    memoryview(bytes(256 * 2 * self.channel_count)))
        return kit_faults.HiddenGain._get_buffer(
            self, single_channel_output, audio_channel)


class ResetSilentOnEmpty(ConvolutionReverb):
    """The empty-impulse reset leg's control: on the empty impulse,
    `reset()` plays a 256-frame block of silence, which is what "the next
    256 frames come out as exact zero" (the `8a57282` words) promised
    there too. With a room loaded it is the clean class."""

    NAME = NAME

    def _build(self, *arguments, **options):
        ConvolutionReverb._build(self, *arguments, **options)
        self._silent = _SilentBlock(self._node)
        self._output = self._silent

    def reset(self):
        ConvolutionReverb.reset(self)
        self._silent.armed = not int(self._node.taps)


class TailTwoShort(ConvolutionReverb):
    """The tail leg's control: `tail_samples` two frames short."""

    NAME = NAME

    @property
    def tail_samples(self):
        self._check_live()
        taps = int(self._node.taps)
        return (self._latency() + taps if taps else 0) - 2


class MixOnePullLate(ConvolutionReverb):
    """The Mix sentence's control: a Mix move handed to the node one pull
    late, so 512 frames come out at the old Mix, not 256."""

    NAME = NAME

    def _build(self, *arguments, **options):
        self._hooked = False
        ConvolutionReverb._build(self, *arguments, **options)
        self._mix_wait = 0
        self._output = _PullHook(self._node, self)
        self._hooked = True

    def _apply_macro(self, index, position):
        if self._hooked and not self._deferred and index == MIX_I:
            self._mix_wait = 2
            return
        ConvolutionReverb._apply_macro(self, index, position)

    def _flush(self):
        if self._mix_wait:
            self._mix_wait -= 1
            if not self._mix_wait:
                self._node.set(mix=self._value(MIX_I) * 0.5)


class ReplugOnReset(ConvolutionReverb):
    """The reset-mid-buffer leg's control (the trial of the second process,
    2026-09-29): `reset()` plugs the source back into the node, which drops
    the frames the node held of a source buffer it had not finished."""

    NAME = NAME

    def reset(self):
        ConvolutionReverb.reset(self)
        self._node.play(self._source)


def reach(faulted, reading, tolerance=0.0, rate=RATE, channels=2,
          builder=build):
    return kit_faults.fault_reachability(
        ConvolutionReverb, faulted, reading,
        lambda cls: builder(cls, rate, channels), tolerance=tolerance)


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

    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-09-29, so `create()` serves this one. It was the
        reverse assertion while the class was parked; revert
        `rebuilt.ADOPTED` and this goes red."""
        import audioeffects
        from audioeffects import rebuilt as registry
        self.assertIs(registry.module_class(NAME), ConvolutionReverb)
        self.assertIn(NAME, registry.ADOPTED)
        self.assertNotIn(NAME, registry.parked())
        self.assertIs(audioeffects.ConvolutionReverb, ConvolutionReverb)
        served = audioeffects.create(NAME, switchable(), RATE)
        self.assertIsInstance(served, ConvolutionReverb)
        served.deinit()

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
        # 0.159 fs: at 22.05 kHz the default is the 3 506 Hz clamp, and
        # every position from 92 to 126 is that one room (the room's own
        # impulse, compared byte for byte); at 48 kHz no two positions are.
        effect = build(rate=22050)
        self.assertAlmostEqual(effect._synthesis()[1], 0.159 * 22050,
                               places=6)
        pulse = click(LATENCY + effect.node.taps + 256)
        rooms = {}
        for midi in range(88, 127):
            effect.set_macro(DAMPING_I, midi)
            rooms[midi] = digest(at_mix(effect, 127, pulse))
        effect.deinit()
        self.assertEqual(len(set(rooms[m] for m in range(92, 127))), 1)
        self.assertNotEqual(rooms[91], rooms[92])
        effect = build()
        pulse = click(LATENCY + effect.node.taps + 256)
        seen = set()
        for midi in range(0, 127):
            effect.set_macro(DAMPING_I, midi)
            seen.add(digest(at_mix(effect, 127, pulse)))
        effect.deinit()
        self.assertEqual(len(seen), 127)

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
            build(impulse=make_impulse().tobytes(), ir_gain_db=-24.5)
        with self.assertRaises(ValueError):
            build(impulse=make_impulse().tobytes(), start_ms=-0.5)
        for gain_db, start_ms in ((-24.0, 0.0), (12.0, 200.0)):
            build(impulse=make_impulse(12000).tobytes(), ir_gain_db=gain_db,
                  start_ms=start_ms).deinit()
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

    def test_a_two_dimensional_impulse_raises_naming_the_class(self):
        # It used to reach the trim's slice and raise Python's bare
        # NotImplementedError (surface refuter, item 9).
        for start_ms in (0.0, 5.0):
            with self.assertRaises(TypeError) as caught:
                build(impulse=make_impulse(1000, 2), impulse_channels=2,
                      start_ms=start_ms)
            self.assertIn(NAME, str(caught.exception))
            self.assertIn("one-dimensional", str(caught.exception))
        effect = build(impulse=make_impulse(1000, 2).reshape(-1),
                       impulse_channels=2)
        self.assertEqual(effect.node.taps, 1024)
        effect.deinit()

    def test_damping_under_the_span_is_the_span_bottom(self):
        # Disclosed in the docstring: no error, the 500 Hz stop.
        for hz in (100.0, 499.0, 500.0):
            effect = build(damping_hz=hz)
            self.assertAlmostEqual(effect._synthesis()[1], 500.0, places=6)
            effect.deinit()
        # Fix round 2 (gate audit round 2, item 7b): a negative damping_hz
        # is out of circuit, like 0, not the 500 Hz stop.
        # Re-audit fix round 1 (gate audit round 3, item 6): NaN is out of
        # circuit too, and the docstring now says so (NanIsSpanBottom is
        # the control, red here).
        for hz in (-100.0, 0.0, float("nan")):
            effect = build(damping_hz=hz)
            self.assertEqual(effect._synthesis()[1], 0.0, hz)
            self.assertEqual(effect.get_macro(DAMPING_I), 127, hz)
            effect.deinit()

    def test_an_empty_impulse_holds_one_partition(self):
        # Fix round 2 (item 7c): impulse=b"" reports taps 0 and latency 0
        # (D3's unloaded wire), and its node is built with one partition,
        # so it accepts a 256-frame load. Measured mode's allocation starts
        # at one frame; zero frames is this one partition.
        effect = build(impulse=b"")
        self.assertEqual(effect.node.taps, 0)
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(effect.tail_samples, 0)
        # Read directly, since `capacity()` starts at one partition.
        effect.node.load(bytes(2 * 256), 1, 1.0)
        with self.assertRaises(ValueError):
            effect.node.load(bytes(2 * 257), 1, 1.0)
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

    def pull(self, effect, pcm, action=None, block=256, blocks=40):
        """`blocks` output pulls over `pcm` from a source handing `block`
        frames a call; `action(effect)` runs before pull 10."""
        channels = effect.channel_count
        effect._source.swap(probes.ArraySource(
            pcm, rate=effect.sample_rate, channels=channels, block=block))
        audiocore.reset_buffer(effect.node)
        out = bytearray()
        for number in range(blocks):
            if number == 10 and action is not None:
                action(effect)
            out += bytes(audiocore.get_buffer(effect.output)[1])
        return np.frombuffer(bytes(out), dtype=np.int16).reshape(
            -1, channels)

    def test_a_room_move_keeps_the_room_ringing_and_lands_on_the_new_room(
            self, cls=None):
        # Restated at audiodsp v0.6.3rc2 (audiodsp#163; re-audit fix round
        # 1). Up to v0.6.3rc1 the node emptied itself on a re-synthesis, so
        # a tail ringing at a room-knob move stopped dead; this test pinned
        # that (13 561 LSB where it asserted 0 at the fix). Now: before the
        # block in flight the output is the old room's; the block in flight
        # (frames 2 560..2 815 for a move before pull 10) runs in a straight
        # line from the old room's frames to the new room's, within 1 LSB;
        # from the next block on it is, byte for byte, an instance that had
        # the new room from the start; and the tail rings on across the
        # move. ResetOnMove (the old node's behaviour, planted) is red.
        moves = ((DECAY_I, 64), (DAMPING_I, 30), (PREDELAY_I, 40),
                 (DIFFUSION_I, 100), (ROOM_I, 50))
        k = (np.arange(1, 257, dtype=np.float64) / 256.0)[:, None]
        for rate in RATES:
            for channels in (2, 1):
                burst = np.vstack([white(8 * 256 + 37, channels,
                                         peak_dbfs=-12.0),
                                   silence(32 * 256, channels)])
                for mix in (2.0, 0.6):
                    old = self.pull(build(cls, rate, channels, mix=mix),
                                    burst)
                    for index, value in moves:
                        fresh = build(cls, rate, channels, mix=mix)
                        fresh.set_macro(index, value)
                        new = self.pull(fresh, burst)
                        fresh.deinit()
                        effect = build(cls, rate, channels, mix=mix)
                        out = self.pull(effect, burst,
                                        lambda e: e.set_macro(index, value))
                        effect.deinit()
                        label = (rate, channels, mix, index)
                        self.assertEqual(digest(out[:2560]),
                                         digest(old[:2560]), label)
                        self.assertEqual(digest(out[2816:]),
                                         digest(new[2816:]), label)
                        line = old[2560:2816] + k * (
                            new[2560:2816].astype(np.float64)
                            - old[2560:2816])
                        # The node fades in float and clips after, so a
                        # sample at full scale in either room is off the
                        # line by design; at -12 dBFS none is.
                        self.assertLess(int(max(np.max(np.abs(old)),
                                                np.max(np.abs(new)))),
                                        32767, label)
                        self.assertLessEqual(
                            float(np.max(np.abs(out[2560:2816] - line))),
                            1.0, label)
                        self.assertGreater(
                            int(np.max(np.abs(out[2560:4096]))), 1000, label)

    def test_a_room_move_drops_no_dry_frame(self, cls=None):
        # Restated at audiodsp v0.6.3rc2 (audiodsp#163; re-audit fix round
        # 1). Up to v0.6.3rc1 the reset at the end of the node's
        # synthesize() zeroed the frames in flight too, so at Mix 0 the
        # source frames 2 304..2 559 came out as exact zero at a move
        # before pull 10, and this test pinned that gap. Now Mix 0 is the
        # source delayed by `latency_samples`, byte for byte, across every
        # room knob's move, at three rates, stereo and mono, from a source
        # in 256-frame blocks and from one in 100-frame blocks; so is a
        # move onto the room already loaded, and a Mix move that stays at
        # 0. ResetOnMove is red.
        frames = 40 * 256
        moves = ((DECAY_I, 64), (DAMPING_I, 30), (PREDELAY_I, 40),
                 (DIFFUSION_I, 100), (ROOM_I, 50), (DECAY_I, None),
                 (MIX_I, 0))
        for rate in RATES:
            for channels in (2, 1):
                pcm = ((np.arange(frames) * 7) % 20001 - 10000).astype(
                    np.int16)
                pcm = np.repeat(pcm[:, None], channels, axis=1)
                want = np.vstack([silence(LATENCY, channels),
                                  pcm[:frames - LATENCY]])
                self.assertTrue(np.any(pcm[2304:2560] != 0))
                for block in (256, 100):
                    for index, value in moves:
                        effect = build(cls, rate, channels, mix=0.0)
                        out = self.pull(
                            effect, pcm,
                            lambda e: e.set_macro(index, e.get_macro(index)
                                                  if value is None
                                                  else value),
                            block=block)
                        effect.deinit()
                        self.assertEqual(
                            digest(out), digest(want),
                            (rate, channels, block, index, value))

    def test_a_mix_move_lands_a_partition_late_and_reset_drops_one(self):
        # The docstring's mid-stream lines (fix round 1, audit item 7): a
        # Mix move before block 10 leaves the 256 frames in flight
        # (2 560..2 815) at the old Mix and the wire exact after; reset()
        # mid-stream zeroes that partition, dry included.
        frames = 32 * 256
        pcm = white(frames, peak_dbfs=-1.0)
        wire = np.vstack([silence(LATENCY), pcm[:frames - LATENCY]])

        def pull(effect, action):
            effect._source.swap(probes.ArraySource(pcm, rate=RATE,
                                                   channels=2))
            audiocore.reset_buffer(effect.node)
            out = bytearray()
            for block in range(32):
                if block == 10:
                    action(effect)
                out += bytes(audiocore.get_buffer(effect.output)[1])
            return np.frombuffer(bytes(out), dtype=np.int16).reshape(-1, 2)

        effect = build()
        out = pull(effect, lambda e: e.set_macro(MIX_I, 0))
        effect.deinit()
        late = np.any(out != wire, axis=1)
        self.assertEqual(int(np.sum(late[2560:])), 256)
        self.assertTrue(np.all(late[2560:2816]))
        effect = build(mix=0.0)

        def reset_then_wire(e):
            e.reset()
            e.set_macro(MIX_I, 0)

        out = pull(effect, reset_then_wire)
        effect.deinit()
        self.assertEqual(int(np.max(np.abs(out[2560:2816]))), 0)
        self.assertEqual(digest(out[2816:]), digest(wire[2816:]))


#: The pull the moves land before, and the block in flight it plays.
MOVE_AT = 10
BLOCK_IN_FLIGHT = slice(MOVE_AT * 256, MOVE_AT * 256 + 256)


def sine(frames, channels, hz, rate, peak):
    t = np.arange(frames) / float(rate)
    x = np.round(peak * np.sin(2 * np.pi * hz * t)).astype(np.int16)
    return np.repeat(x[:, None], channels, axis=1)


def pulled(effect, pcm, actions=None, blocks=40):
    """`blocks` pulls over `pcm` from a source in 256-frame blocks;
    `actions[n](effect)` runs just before pull n."""
    channels = effect.channel_count
    effect._source.swap(probes.ArraySource(pcm, rate=effect.sample_rate,
                                           channels=channels))
    audiocore.reset_buffer(effect.node)
    out = bytearray()
    for number in range(blocks):
        if actions and number in actions:
            actions[number](effect)
        out += bytes(audiocore.get_buffer(effect.output)[1])
    return np.frombuffer(bytes(out), dtype=np.int16).reshape(-1, channels)


def apply_moves(effect, moves):
    for index, value in moves:
        effect.set_macro(index, value)


def room_render(cls, rate, channels, moves, pcm, mix=2.0, actions=None):
    effect = build(cls, rate, channels, mix=mix)
    apply_moves(effect, moves)
    out = pulled(effect, pcm, actions)
    effect.deinit()
    return out


def fade_reading(old, new, moved, first=None, at=None):
    """The block in flight of `moved` (the 256 frames from frame `at`,
    default the block after MOVE_AT pulls) against the straight line from
    `old` to `new` (full-scale samples left out: the node clips after its
    fade), the jump into it, its largest step and the rooms' own largest
    step from the frame before it to the frame after it, how many frames
    before it are off `old` and after it off `new`, and how far its first
    frame sits from `first` (the room of a first move) and from `old`."""
    o, n, m = (x.astype(np.float64) for x in (old, new, moved))
    a = BLOCK_IN_FLIGHT.start if at is None else at
    b = a + 256
    k = (np.arange(1, 257, dtype=np.float64) / 256.0)[:, None]
    line = o[a:b] + k * (n[a:b] - o[a:b])
    full = (np.abs(o[a:b]) >= 32767) | (np.abs(n[a:b]) >= 32767)
    span = slice(a - 1, b + 1)
    reading = dict(
        pre=int(np.sum(np.any(moved[:a] != old[:a], axis=1))),
        post=int(np.sum(np.any(moved[b:] != new[b:], axis=1))),
        off_line=float(np.max(np.where(full, 0.0, np.abs(m[a:b] - line)))),
        jump=int(np.max(np.abs(m[a] - m[a - 1]))),
        step=float(np.max(np.abs(np.diff(m[span], axis=0)))),
        own=float(max(np.max(np.abs(np.diff(o[span], axis=0))),
                      np.max(np.abs(np.diff(n[span], axis=0))))),
        near_old=float(np.max(np.abs(m[a] - o[a]))))
    if first is not None:
        reading["near_first"] = float(np.max(np.abs(
            m[a] - first[a].astype(np.float64))))
    return reading


class DryOnce(probes.ArraySource):
    """int16 frames in 256-frame calls (or `size`-frame calls), except
    where `plan` maps a call number (from 1) to what that call hands: a
    number is that many frames of the material, 0 an empty buffer, the
    source running dry for one call and then going on; ("bytes", n) is n
    stray bytes of 0x11 that take nothing from the material; ("error", n)
    is `GET_BUFFER_ERROR` carrying the next n frames of the material."""

    def __init__(self, data, rate, channels, plan=None, size=None):
        probes.ArraySource.__init__(self, data, rate=rate, channels=channels)
        self.plan = dict(plan or {})
        self.size = size
        self.calls = 0

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        probes.ArraySource._reset_buffer(self)
        self.calls = 0

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        self.calls += 1
        take = self.plan.get(self.calls, self.size)
        if take is None:
            return probes.ArraySource._get_buffer(self)
        result = audiocore.GET_BUFFER_MORE_DATA
        if isinstance(take, tuple):
            kind, take = take
            if kind == "bytes":
                return result, memoryview(b"\x11" * take)
            result = audiocore.GET_BUFFER_ERROR
        stride = take * self.channel_count * 2
        chunk = bytes(self._pcm[self._position:self._position + stride])
        self._position += len(chunk)
        return result, memoryview(chunk)


#: The source hands 255 frames on its fourth call and an empty buffer on
#: its fifth, then goes on: the node's block phase is 255 from then on.
UNDERRUN = {4: 255, 5: 0}


def act(effect, moves):
    """Apply `moves`: (macro, MIDI), ("patch", index) or ("reset", None)."""
    for index, value in moves:
        if index == "patch":
            effect.program_change(value)
        elif index == "reset":
            effect.reset()
        else:
            effect.set_macro(index, value)


def dry_render(cls, rate, channels, start, pcm, plan=None, actions=None,
               mix=2.0, blocks=40, size=None, **options):
    """`blocks` host pulls over `pcm` from a DryOnce source (calls of `size`
    frames, default 256), `start` applied at construction and `actions[n]`
    just before pull n; `options` go to the constructor. Returns the output
    as (frames, channels) and the frame count of each pull."""
    effect = build(cls, rate, channels, mix=mix, **options)
    act(effect, start)
    effect._source.swap(DryOnce(pcm, rate, channels, plan, size))
    audiocore.reset_buffer(effect.node)
    out, sizes = [], []
    for number in range(blocks):
        if actions and number in actions:
            act(effect, actions[number])
        data = np.frombuffer(bytes(audiocore.get_buffer(effect.output)[1]),
                             dtype=np.int16).reshape(-1, channels)
        out.append(data)
        sizes.append(len(data))
    effect.deinit()
    return np.vstack(out), sizes


#: What the rule says breaks the line, each before one pull, on the dark
#: room (Damping 0) with Mix held at 2: (label, start, the changes).
DARK = ((DAMPING_I, 0),)
HOLD_MIX = ((MIX_I, 127),)
TWO_CHANGES = (
    ("two knobs", DARK, ((ROOM_I, 50), (PREDELAY_I, 40))),
    ("three knobs", DARK, ((ROOM_I, 50), (PREDELAY_I, 40), (DECAY_I, 30))),
    ("a knob, then a patch", (("patch", 1),) + DARK,
     ((PREDELAY_I, 40), ("patch", 3))),
    ("a patch, then a knob", (("patch", 1),), (("patch", 3), (ROOM_I, 50))),
    ("two patches", (("patch", 0),), (("patch", 1), ("patch", 3))),
)


class RoomMoveWords(unittest.TestCase):
    """What a move does while audio plays. Since the trial of the second
    process (2026-09-29) the docstring claims only what holds in every
    case: no dry frame drops or repeats, every move has landed from the end
    of the block in flight, a Mix move leaves that block at the old Mix, and
    a reset silences it. The straight-line fade, the jumps and the short
    reads these tests also pin are the node's mechanism, stated in the
    dossier, not promises in the docstring."""

    def test_a_patch_change_is_one_synthesis_on_the_line(self, cls=None):
        # "A patch change counts as one room change however many knobs it
        # moves": patch 1 -> 3 (every room knob moves, Mix does not) and
        # patch 1 -> 5 (Mix moves too, 44 -> 63) before one pull, at three
        # rates, stereo and mono, on white noise and on the low sine. The
        # block in flight is on the straight line from the old room to the
        # new at the Mix already in flight (patch 5's room at patch 1's
        # Mix), and after it the output is the new patch's exactly.
        # PatchPerKnob (one synthesis a knob) is red.
        for rate in RATES:
            for channels in (2, 1):
                for pcm in (white(40 * 256, channels, -6.0, seed=4242),
                            sine(40 * 256, channels, 40.0, rate, 2000.0)):
                    for target in (3, 5):
                        old_mix = ConvolutionReverb.PATCHES[1][1][MIX_I]
                        renders = []
                        for action in ("old", "line", "built", "moved"):
                            effect = build(cls, rate, channels, patch=1)
                            acts = None
                            if action in ("line", "built"):
                                effect.program_change(target)
                            if action == "line":
                                effect.set_macro(MIX_I, old_mix)
                            if action == "moved":
                                acts = {MOVE_AT: lambda e, t=target:
                                        e.program_change(t)}
                            renders.append(pulled(effect, pcm, acts))
                            effect.deinit()
                        old, line, built, moved = renders
                        r = fade_reading(old, line, moved)
                        post = fade_reading(old, built, moved)["post"]
                        label = (rate, channels, target, r)
                        self.assertEqual((r["pre"], post), (0, 0), label)
                        self.assertLessEqual(r["off_line"], 1.0, label)

    def test_every_move_has_landed_from_the_end_of_the_block_in_flight(
            self, cls=None):
        # The rule, read at three rates, stereo and mono, on a 40 Hz sine at
        # 2 000 LSB through the dark room, Mix held at 2:
        # - on the line within 1 LSB, frames before and after exact: one
        #   knob move; one knob a pull (Room, then Predelay the next pull);
        #   a move after an under-run and a reset();
        # - the audio untouched: a move onto the room already loaded (Room
        #   0 -> 1, both seed 1);
        # - frames before and after exact, but a step past ten times the
        #   rooms' own: every pair of changes before one pull the rule
        #   names (two knobs, three, a knob and a patch either way, two
        #   patches), and one knob move after the source ran dry 255
        #   frames into a block.
        # OneSynthesisPerBlock (changes gathered into one synthesis) is red
        # on the pairs, RetryOnEmpty (the class never lets the node see the
        # empty buffer) on the under-run, and the cf17a88 words on the
        # parse.
        for rate in RATES:
            for channels in (2, 1):
                pcm = sine(40 * 256, channels, 40.0, rate, 2000.0)

                def render(start, actions=None, plan=None):
                    return dry_render(cls, rate, channels, start + HOLD_MIX,
                                      pcm, plan, actions)

                def on_line(old, new, moved, at, label, post=True):
                    r = fade_reading(old, new, moved, at=at)
                    self.assertEqual(r["pre"], 0, (label, r))
                    if post:
                        self.assertEqual(r["post"], 0, (label, r))
                    self.assertLessEqual(r["off_line"], 1.0, (label, r))

                def jumps(old, new, moved, at, label):
                    r = fade_reading(old, new, moved, at=at)
                    self.assertEqual((r["pre"], r["post"]), (0, 0),
                                     (label, r))
                    self.assertGreater(r["step"], 10 * r["own"], (label, r))

                label = (rate, channels)
                a = MOVE_AT * 256
                room = ((ROOM_I, 50),)
                pre = ((PREDELAY_I, 40),)
                old = render(DARK)[0]
                one = render(DARK + room)[0]
                on_line(old, one, render(DARK, {MOVE_AT: room})[0], a,
                        label + ("one knob",))
                both = render(DARK + room + pre)[0]
                paced = render(DARK, {MOVE_AT: room, MOVE_AT + 1: pre})[0]
                on_line(old, one, paced, a, label + ("paced, first",),
                        post=False)
                first = render(DARK, {MOVE_AT: room})[0]
                on_line(first, both, paced, a + 256,
                        label + ("paced, second",))
                same = render(DARK, {MOVE_AT: ((ROOM_I, 1),)})[0]
                self.assertEqual(digest(same), digest(old),
                                 label + ("the room already loaded",))
                for name, start, changes in TWO_CHANGES:
                    changes = changes + HOLD_MIX
                    jumps(render(start)[0], render(start + changes)[0],
                          render(start, {MOVE_AT: changes})[0], a,
                          label + (name,))
                # The under-run: the move twenty pulls on, and the same move
                # after a reset() that follows the under-run.
                p0, p127 = ((PREDELAY_I, 0),), ((PREDELAY_I, 127),)
                old, sizes = render(DARK + p0, plan=UNDERRUN)
                new = render(DARK + p127, plan=UNDERRUN)[0]
                moved = render(DARK + p0, {20: p127}, UNDERRUN)[0]
                u = sum(sizes[:20])
                jumps(old, new, moved, u, label + ("under-run",))
                self.assertEqual(sizes[3], 255, label)
                # The block in flight is the one frame left of the node's
                # block; from its end the output is the new room's.
                self.assertEqual(digest(moved[u + 1:]), digest(new[u + 1:]),
                                 label)
                # An empty buffer at a block edge is not part-way through
                # one: the node plays 256 frames of silence and no phase
                # moves, and a move made before that pull fades, on the
                # line, over the block the node plays next.
                edge = {11: 0}
                old, sizes = render(DARK, plan=edge)
                self.assertEqual(sizes, [256] * 40, label)
                self.assertEqual(int(np.max(np.abs(old[a:a + 256]))), 0,
                                 label)
                on_line(old, render(DARK + room, plan=edge)[0],
                        render(DARK, {MOVE_AT: room}, edge)[0], a + 256,
                        label + ("an empty buffer at a block edge",))
                again = (("reset", None),) + DARK + HOLD_MIX + p0
                old, sizes = render(DARK + p0, {12: again}, UNDERRUN)
                new = render(DARK + p0, {12: again + p127}, UNDERRUN)[0]
                moved = render(DARK + p0, {12: again, 24: p127},
                               UNDERRUN)[0]
                on_line(old, new, moved, sum(sizes[:24]),
                        label + ("under-run, reset()",))

    def test_every_short_read_part_way_counts_as_coming_up_short(
            self, cls=None):
        # "comes up short (an empty buffer, one shorter than a frame, or an
        # error result)", and the rule's "has not come up short (above)
        # part-way through a block": the source hands 100 frames on its
        # fourth call and, on its fifth, an empty buffer, 1 stray byte, 3
        # stray bytes (stereo) or an error result carrying 7 frames. Each
        # returns a short block of 100 frames, and a Predelay 0 -> 127 move
        # twenty pulls on is off the new room over at most 155 frames, not
        # 255, and off the 256-frame line by far more than 1 LSB; a Mix
        # 0 -> 2 move there leaves 156 frames at the old Mix, not 256. The
        # controls, 3 whole frames and (stereo) 5 bytes, a frame and a
        # part, are not short: the node pulls again, the block is whole,
        # and the move is on the line (255 frames off the new room, 256 at
        # the old Mix). RetryOnShort (the class pulls again on every short
        # read) is red on the short legs; RetryOnEmpty is red only on the
        # empty one.
        start = DARK + HOLD_MIX
        move = ((PREDELAY_I, 127),)
        for rate in RATES:
            for channels in (2, 1):
                pcm = sine(44 * 256, channels, 40.0, rate, 2000.0)
                legs = [("empty", 0, True), ("1 byte", ("bytes", 1), True),
                        ("error, 7 frames", ("error", 7), True),
                        ("3 frames", 3, False)]
                if channels == 2:
                    legs += [("3 bytes", ("bytes", 3), True),
                             ("5 bytes", ("bytes", 5), False)]
                for name, what, short in legs:
                    plan = {4: 100, 5: what}
                    label = (rate, channels, name)
                    old, sizes = dry_render(cls, rate, channels, start, pcm,
                                            plan, blocks=44)
                    new = dry_render(cls, rate, channels, start + move, pcm,
                                     plan, blocks=44)[0]
                    moved = dry_render(cls, rate, channels, start, pcm, plan,
                                       {24: move}, blocks=44)[0]
                    a = sum(sizes[:24])
                    r = fade_reading(old, new, moved, at=a)
                    off = np.nonzero(np.any(moved[a:] != new[a:], axis=1))[0]
                    fade = int(off[-1]) + 1
                    m0 = dry_render(cls, rate, channels, (), pcm, plan,
                                    mix=0.0, blocks=44)[0]
                    m2 = dry_render(cls, rate, channels, (), pcm, plan,
                                    {24: ((MIX_I, 127),)}, mix=0.0,
                                    blocks=44)[0]
                    late = int(np.nonzero(np.any(m0[a:] != m2[a:],
                                                 axis=1))[0][0])
                    self.assertEqual(r["pre"], 0, (label, r))
                    if short:
                        self.assertEqual(sizes[3], 100, label)
                        self.assertLessEqual(fade, 155, (label, fade))
                        self.assertGreater(r["off_line"], 100.0, (label, r))
                        self.assertEqual(late, 156, label)
                    else:
                        self.assertEqual(sizes[3], 256, label)
                        self.assertEqual(fade, 255, label)
                        self.assertLessEqual(r["off_line"], 1.0, (label, r))
                        self.assertEqual(late, 256, label)

    def test_no_dry_frame_drops_after_any_number_of_changes(self, cls=None):
        # "No frame of your dry signal drops or repeats, at any Mix and
        # after any number of moves: at Mix 0 the output is byte for byte
        # what it would have been with no move", across every pair of
        # changes the rule names (Mix put back to 0 after a patch), across
        # moves after the source ran dry 100 and 255 frames into a block,
        # and across a move made before a pull the source leaves empty at
        # a block edge. And it reads the latency paragraph against the same
        # renders: Mix 0 is the source delayed by `latency_samples`, byte
        # for byte, from a source in 256-frame calls, in 100-frame calls and
        # in 1 000-frame calls, and after it comes up short part-way through
        # a block; a pull in which it comes up short before the pull has a
        # frame (an empty buffer, 1 stray byte or an error result at a block
        # edge, and two such pulls) comes out as 256 frames of silence with
        # everything after it 256 frames later; an error result's frames
        # never reach the node, and neither does the part frame at the end
        # of a buffer of a frame and a byte (its whole frame does). The
        # moves come before and after the starved pull. ResetOnMove is red,
        # and so are the 8a57282 words, whose one exception was the reset.
        wire_back = ((MIX_I, 0),)
        stray = np.frombuffer(b"\x11\x11", dtype=np.int16)[0]
        room = ((ROOM_I, 50),)
        for rate in RATES:
            for channels in (2, 1):
                frames = 40 * 256
                pcm = ((np.arange(frames) * 7) % 20001 - 10000).astype(
                    np.int16)
                pcm = np.repeat(pcm[:, None], channels, axis=1)

                def wire(source, silent=()):
                    """`source` delayed by `latency_samples`, with 256
                    frames of silence at each output frame in `silent`
                    (output frames, the earlier silences counted)."""
                    out = np.vstack([silence(LATENCY, channels), source])
                    for at in sorted(silent):
                        out = np.vstack([out[:at], silence(256, channels),
                                         out[at:]])
                    return out

                edge = MOVE_AT * 256       # the starved pull, call 11
                dropped = np.vstack([pcm[:edge], pcm[edge + 7:]])
                part = np.vstack([pcm[:edge],
                                  np.full((1, channels), stray, np.int16),
                                  pcm[edge:]])
                # (name, source plan, moves, the call size, what Mix 0 is)
                cases = [(name, None, {MOVE_AT: changes + wire_back}, None,
                          wire(pcm)) for name, _, changes in TWO_CHANGES]
                for p in (100, 255):
                    cases.append(("under-run %d" % p, {4: p, 5: 0}, {
                        20: room, 21: ((PREDELAY_I, 40), (DECAY_I, 30))},
                        None, wire(pcm)))
                cases += [
                    ("100-frame calls, one empty", {30: 0}, {20: room}, 100,
                     wire(pcm)),
                    ("1 000-frame calls, one empty", {5: 0}, {6: room}, 1000,
                     wire(pcm)),
                    ("empty at a block edge, a move before it", {11: 0},
                     {MOVE_AT: room}, None, wire(pcm, (edge,))),
                    ("empty at a block edge, a move after it", {11: 0},
                     {20: room}, None, wire(pcm, (edge,))),
                    ("1 byte at a block edge", {11: ("bytes", 1)},
                     {20: room}, None, wire(pcm, (edge,))),
                    ("an error with 7 frames at a block edge",
                     {11: ("error", 7)}, {20: room}, None,
                     wire(dropped, (edge,))),
                    ("two empty pulls", {11: 0, 15: 0}, {20: room}, None,
                     wire(pcm, (edge, 14 * 256))),
                    ("a frame and a byte at a block edge",
                     {11: ("bytes", 2 * channels + 1)}, {20: room}, None,
                     wire(part)),
                ]
                for name, plan, actions, size, want in cases:
                    label = (rate, channels, name)
                    out = dry_render(cls, rate, channels, (), pcm, plan,
                                     actions, mix=0.0, size=size)[0]
                    still = dry_render(cls, rate, channels, (), pcm, plan,
                                       mix=0.0, size=size)[0]
                    self.assertEqual(digest(out), digest(still), label)
                    self.assertEqual(digest(out), digest(want[:len(out)]),
                                     label)

    def test_a_mix_move_leaves_the_block_in_flight_at_the_old_mix(
            self, cls=None):
        # "A Mix move ... acts on the audio entering the node after it, so
        # the block already in flight, at most 256 frames, comes out at the
        # old Mix": Mix 0 -> 2 twenty pulls in.
        # The frames after the move at the old Mix are never more than the
        # printed count, and from the first one at the new Mix the output
        # is an instance that always had it; from a steady source the count
        # is the printed one exactly, and after the source ran dry 100
        # frames into a block it is 156. MixOnePullLate (512) is red, and
        # so are the cf17a88 words, which said the 256 frames in flight
        # come out at the old Mix.
        most = 256
        for rate in RATES:
            for channels in (2, 1):
                pcm = white(40 * 256, channels, -6.0, seed=4243)
                for plan, frames in ((None, most), ({4: 100, 5: 0}, 156)):
                    old, sizes = dry_render(cls, rate, channels, (), pcm,
                                            plan, mix=0.0)
                    new = dry_render(cls, rate, channels, (), pcm, plan,
                                     mix=2.0)[0]
                    moved = dry_render(cls, rate, channels, (), pcm, plan,
                                       {20: ((MIX_I, 127),)}, mix=0.0)[0]
                    a = sum(sizes[:20])
                    self.assertEqual(digest(moved[:a]), digest(old[:a]))
                    off = np.nonzero(np.any(moved[a:] != old[a:], axis=1))[0]
                    late = int(off[0])
                    label = (rate, channels, plan, late)
                    self.assertLessEqual(late, most, label)
                    self.assertEqual(late, frames, label)
                    self.assertEqual(digest(moved[a + late:]),
                                     digest(new[a + late:]), label)

    def test_reset_silences_the_next_256_frames(self, cls=None):
        # "`reset()` in the middle of a stream empties the room: the next
        # `latency_samples` frames come out as exact zero, dry included.
        # That is 256 with a room loaded": at Mix 0, 1.2 and 2, on the
        # synthesized room from a steady source and after one that ran dry
        # 100 frames into a block, and on a measured impulse of 1 000 taps,
        # the 256 frames after a reset() twenty pulls in are
        # exact zero and the frames either side of them are not; at Mix 0
        # the output is the source delayed by `latency_samples` but for
        # those 256 frames (the latency paragraph's first exception). On
        # the empty impulse (`latency_samples` 0) the reset silences
        # nothing: at Mix 0, 0.6, 1.2 and 2 no output frame is zero and the
        # output is the source, frame for frame. NoReset (a reset that
        # keeps the history) is red on the room, ResetSilentOnEmpty (a
        # reset that plays 256 frames of silence whatever the node holds)
        # on the empty impulse, and so are the 8a57282 words, which said
        # the next 256 frames at every Mix.
        for rate in RATES:
            for channels in (2, 1):
                pcm = white(40 * 256, channels, -6.0, seed=4244)
                pcm[pcm == 0] = 1
                want = np.vstack([silence(LATENCY, channels), pcm])
                rooms = ({}, dict(impulse=make_impulse(1000).tobytes()))
                for plan, room in ((None, rooms[0]), ({4: 100, 5: 0},
                                                     rooms[0]),
                                   (None, rooms[1])):
                    for midi in (0, 76, 127):
                        out, sizes = dry_render(
                            cls, rate, channels, ((MIX_I, midi),), pcm, plan,
                            {20: (("reset", None), (MIX_I, midi))}, mix=0.0,
                            **room)
                        a = sum(sizes[:20])
                        label = (rate, channels, plan, bool(room), midi)
                        self.assertEqual(
                            int(np.max(np.abs(out[a:a + 256]))), 0, label)
                        self.assertGreater(
                            int(np.max(np.abs(out[a - 256:a]))), 0, label)
                        self.assertGreater(
                            int(np.max(np.abs(out[a + 256:a + 512]))), 0,
                            label)
                        if midi == 0:
                            wire = want[:len(out)].copy()
                            wire[a:a + 256] = 0
                            self.assertEqual(digest(out), digest(wire),
                                             label)
                for midi in (0, 38, 76, 127):
                    label = (rate, channels, "empty impulse", midi)
                    out = dry_render(
                        cls, rate, channels, ((MIX_I, midi),), pcm, None,
                        {20: (("reset", None), (MIX_I, midi))}, mix=0.0,
                        impulse=b"")[0]
                    self.assertTrue(np.all(np.any(out != 0, axis=1)), label)
                    self.assertEqual(digest(out), digest(pcm[:len(out)]),
                                     label)

    def test_the_tail_counts_the_frames_the_source_hands(self, cls=None):
        # The Tail paragraph: white noise at -6 dBFS over frames 0..4999,
        # then zero frames, at Mix 1.2 and 2, on the synthesized room at
        # patch 0 and on the empty impulse, three rates, stereo and mono;
        # the source leaves no pull empty, one pull (call 23) empty inside
        # the tail, or three in a row (calls 21 to 23), which is a source
        # that stops handing frames mid-tail and then goes on. With the
        # starved pulls' output taken out (each exact zero, 256 frames),
        # the output is the no-starve render frame for frame, so the tail
        # waits and then goes on where it was; and every frame more than
        # `tail_samples` past the last non-zero input frame is exact zero,
        # counted in the frames the source hands, while the room's last
        # non-zero frame lands within one frame of that edge. TailTwoShort
        # (`tail_samples` two frames short) is red, and so are the 8a57282
        # words, which said only that the output is zero after the tail.
        burst = 5000
        for rate in RATES:
            for channels in (2, 1):
                pcm = silence(40 * 256, channels)
                pcm[:burst] = white(burst, channels, -6.0, seed=808)
                for options in ({}, dict(impulse=b"")):
                    probe = build(cls, rate, channels, **options)
                    tail = probe.tail_samples
                    probe.deinit()
                    for midi in (76, 127):
                        steady = None
                        for plan in (None, {23: 0}, {21: 0, 22: 0, 23: 0}):
                            label = (rate, channels, options, midi, plan)
                            out, sizes = dry_render(
                                cls, rate, channels, ((MIX_I, midi),), pcm,
                                plan, mix=0.0, **options)
                            self.assertEqual(sizes, [256] * 40, label)
                            handed = out
                            if plan:
                                starved = [call - 1 for call in plan]
                                for pull in starved:
                                    self.assertEqual(int(np.max(np.abs(
                                        out[pull * 256:pull * 256 + 256]))),
                                        0, label)
                                keep = np.ones(len(out), bool)
                                for pull in starved:
                                    keep[pull * 256:pull * 256 + 256] = False
                                handed = out[keep]
                                self.assertEqual(
                                    digest(handed),
                                    digest(steady[:len(handed)]), label)
                            else:
                                steady = out
                            edge = burst - 1 + tail
                            self.assertEqual(
                                int(np.max(np.abs(handed[edge + 1:]))), 0,
                                label)
                            last = int(np.nonzero(np.any(handed != 0,
                                                         axis=1))[0][-1])
                            self.assertGreaterEqual(last, edge - 1, label)


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

    def test_an_interior_trim_where_truncation_and_rounding_differ(self):
        # The row's trims 0 and 10 ms are whole-frame at every rate, where a
        # rounded trim equals a truncated one, so they cannot carry the
        # truncation clause (audit round 1). 41.7 ms at 48 kHz is 2 001.6
        # frames and 3.3 ms at 44.1 / 22.05 kHz is 145.53 / 72.765: the
        # class keeps 2 001 / 145 / 72, a rounded trim 2 002 / 146 / 73.
        h = make_impulse(3840)
        for rate, start_ms in ((48000, 41.7), (44100, 3.3), (22050, 3.3)):
            self.assertNotEqual(trim_frames(start_ms, rate),
                                int(round(start_ms * rate / 1000.0)))
            clean = m1_error(ConvolutionReverb, rate, 1, 2, "noise", 8000.0,
                             0.0, start_ms, h_full=h)
            planted = m1_error(TrimRounded, rate, 1, 2, "noise", 8000.0,
                               0.0, start_ms, h_full=h)
            self.assertLessEqual(clean, 1.0, (rate, start_ms))
            self.assertGreater(planted, 1000.0, (rate, start_ms))
        # And the control is invisible at the row's own trims.
        for start_ms in (0.0, 10.0):
            self.assertLessEqual(m1_error(TrimRounded, RATE, 1, 2, "noise",
                                          8000.0, 0.0, start_ms, h_full=h),
                                 1.0)

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

def capacity(node):
    """The node's allocation in taps, read as a board would: the longest
    impulse its `load()` accepts (the native binding refuses more,
    `Convolver.c:183-186` at 0d35a90; the twin at `audioconvolve.py:127`).
    `node.taps` cannot stand in for it: in measured mode it reports the
    loaded length rounded to a partition, which is the law whatever the
    allocation (audit round 1). Destructive - it replaces the room - so it
    is the last thing read off an instance."""
    taps = max(256, (int(node.taps) + 255) // 256 * 256)
    while taps <= 131072 + 256:
        try:
            node.load(bytes(2 * (taps + 1)), 1, 1.0)
        except ValueError:
            return taps
        taps += 256
    return taps


def m2(cls, cells, reading=None):
    """Red entries over (label, seconds, rate, impulse frames, expect).

    A build reads both `node.taps` and the capacity against the law;
    `reading="taps"` reads `node.taps` alone, the frozen reading, kept so
    the test can show what it missed."""
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
        held = got if reading == "taps" else capacity(effect.node)
        effect.deinit()
        if expect != "build":
            reds.append("%s: built" % label)
        elif got != law:
            reds.append("%s: %d taps, the law says %d" % (label, got, law))
        elif held != law:
            reds.append("%s: capacity %d taps, the law says %d"
                        % (label, held, law))
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
    cells += MEASURED_BELOW
    return cells


#: Measured mode below the ceiling (fix round 1): lengths off, on and one
#: past a partition edge, and a one-second room.
MEASURED_BELOW = [("measured %d" % frames, 0.0, RATE, frames, "build")
                  for frames in (1000, 3840, 3841, 48000)]


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

    def test_one_partition_too_many_is_red_in_measured_mode(self):
        # node.taps reads the law on the planted class too (1 024 / 3 840 /
        # 4 096 / 48 128), so the frozen reading is green there; the
        # capacity reads 1 280 / 4 096 / 4 352 / 48 384 and is red.
        self.assertEqual(m2(ExtraPartition, MEASURED_BELOW, reading="taps"),
                         [])
        reds = m2(ExtraPartition, MEASURED_BELOW)
        self.assertEqual(len(reds), 4, reds)
        for (label, _, _, frames, _), red in zip(MEASURED_BELOW, reds):
            law = (frames + 255) // 256 * 256
            self.assertIn("capacity %d taps" % (law + 256), red)
        self.assertEqual(m2(ConvolutionReverb, MEASURED_BELOW), [])

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
    def errors_over_rooms(self, cls=None, rate=RATE, moves=(),
                          read_back=False, **options):
        # The law takes the seconds and the Decay and Predelay positions
        # this test handed the instance, never `effect.seconds` or
        # `effect._macros`: a class that stretched its own allocation, or
        # held a position other than the one it was handed, would move a
        # law read back from it (AllocatedSeconds; DecayKeptSquared and
        # DecayMidiSquared, below). `moves` are (macro, MIDI) handed after
        # construction; `read_back=True` is the frozen reading, kept only
        # to show the hole the handed law closes.
        seconds = options.get("seconds", 0.08)
        effect = handed_build(cls, rate, **options)
        for index, midi in moves:
            effect.set_macro(index, midi)
        errors = []
        for room in range(0, 128, 2):
            effect.set_macro(ROOM_I, room)
            t60, floor = m5_cell(effect)
            self.assertTrue(floor, room)
            self.assertIsNotNone(t60, room)
            if read_back:
                decay, predelay = (effect._macros[DECAY_I],
                                   effect._macros[PREDELAY_I])
            else:
                decay, predelay = effect.handed
            errors.append(t60 / law_t60(decay, predelay, seconds) - 1.0)
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
            effect = handed_build(seconds=1.0, patch=patch)
            errors = []
            for room in range(0, 128, 8):
                effect.set_macro(ROOM_I, room)
                t60, floor = m5_cell(effect)
                self.assertTrue(floor)
                law = law_t60(effect.handed[0], effect.handed[1], 1.0)
                errors.append(t60 / law - 1.0)
            effect.deinit()
            self.assertLessEqual(abs(float(np.mean(errors))), 0.02, patch)

    def test_a_decay_5_percent_long_is_red_at_the_defaults(self):
        errors = self.errors_over_rooms(LongDecay)
        self.assertGreater(float(np.mean(errors)), 0.02)

    def test_a_stretched_allocation_is_red_on_the_handed_law(self):
        # At 0.06 s the allocation rounds up to a whole partition (2 880 ->
        # 3 072 taps at 48 kHz, 0.064 s; 0.0639 s at 44.1 kHz, 0.0697 s at
        # 22.05 kHz); a class keeping that as `seconds` puts every Room long
        # against the law of the seconds it was handed.
        for rate in RATES:
            errors = self.errors_over_rooms(AllocatedSeconds, rate,
                                            seconds=0.06, damping_hz=0.0,
                                            diffusion=0.0)
            self.assertGreater(float(np.max(np.abs(errors))), 0.03, rate)
            self.assertGreater(float(np.mean(errors)), 0.05, rate)
            clean = self.errors_over_rooms(rate=rate, seconds=0.06,
                                           damping_hz=0.0, diffusion=0.0)
            self.assertLessEqual(float(np.max(np.abs(clean))), 0.03, rate)
        # The frozen reading, the law from `effect.seconds`, stays green on
        # the plant: that is the hole the handed law closes.
        effect = build(AllocatedSeconds, RATE, seconds=0.06, damping_hz=0.0,
                       diffusion=0.0)
        self.assertAlmostEqual(effect.seconds, 0.064, places=12)
        read_back = []
        for room in range(0, 128, 2):
            effect.set_macro(ROOM_I, room)
            t60, _ = m5_cell(effect)
            read_back.append(t60 / law_t60(1.0, 0.0, effect.seconds) - 1.0)
        effect.deinit()
        self.assertLessEqual(float(np.max(np.abs(read_back))), 0.03)

    def test_a_decay_held_off_the_handed_position_is_red(self):
        # Fix round 2 (gate audit round 2, item 4). At Decay 64/127, where
        # squaring moves the position (0.504 -> 0.254), a class that keeps
        # the constructor's Decay squared, or a set_macro Decay squared,
        # is red on the law from the handed position and green on the law
        # read back off the class: that is the hole the handed law closes.
        for rate in (48000, 22050):
            planted = self.errors_over_rooms(DecayKeptSquared, rate,
                                             decay=64 / 127.0,
                                             damping_hz=0.0, diffusion=0.0)
            self.assertGreater(float(np.max(np.abs(planted))), 0.03, rate)
            held = self.errors_over_rooms(DecayKeptSquared, rate,
                                          read_back=True, decay=64 / 127.0,
                                          damping_hz=0.0, diffusion=0.0)
            self.assertLessEqual(float(np.max(np.abs(held))), 0.03, rate)
            moved = self.errors_over_rooms(DecayMidiSquared, rate,
                                           moves=((DECAY_I, 64),),
                                           damping_hz=0.0, diffusion=0.0)
            self.assertGreater(float(np.max(np.abs(moved))), 0.03, rate)
            held = self.errors_over_rooms(DecayMidiSquared, rate,
                                          moves=((DECAY_I, 64),),
                                          read_back=True, damping_hz=0.0,
                                          diffusion=0.0)
            self.assertLessEqual(float(np.max(np.abs(held))), 0.03, rate)
            clean = self.errors_over_rooms(rate=rate, moves=((DECAY_I, 64),),
                                           damping_hz=0.0, diffusion=0.0)
            self.assertLessEqual(float(np.max(np.abs(clean))), 0.03, rate)

    def test_a_predelay_held_off_the_handed_position_is_red(self):
        # Re-audit fix round 1 (gate audit round 3, item 3). The law takes
        # the Predelay position the test handed too, and until this test no
        # D5 cell sat at an interior Predelay at 0.08 s, where the law
        # depends on it most: PredelayKeptSquared passed every D5 test. At
        # Predelay 64/127, Decay 127, Damping out, Diffusion 0 it is red on
        # the handed law and green on the law read back off the class;
        # the clean class is green on the handed law.
        for rate in (48000, 22050):
            options = dict(predelay=64 / 127.0, decay=1.0, damping_hz=0.0,
                           diffusion=0.0)
            planted = self.errors_over_rooms(PredelayKeptSquared, rate,
                                             **options)
            self.assertGreater(float(np.max(np.abs(planted))), 0.03, rate)
            self.assertGreater(float(np.mean(planted)), 0.03, rate)
            held = self.errors_over_rooms(PredelayKeptSquared, rate,
                                          read_back=True, **options)
            self.assertLessEqual(float(np.max(np.abs(held))), 0.03, rate)
            clean = self.errors_over_rooms(rate=rate, **options)
            self.assertLessEqual(float(np.max(np.abs(clean))), 0.03, rate)
            # Re-audit fix round 2: the same by `set_macro`, Predelay 64
            # handed after construction, with PredelayMidiSquared as the
            # control. The clean leg goes through `set_macro` too, so a
            # class that held a moved Predelay wrong fails it.
            moved = dict(decay=1.0, damping_hz=0.0, diffusion=0.0)
            planted = self.errors_over_rooms(PredelayMidiSquared, rate,
                                             moves=((PREDELAY_I, 64),),
                                             **moved)
            self.assertGreater(float(np.max(np.abs(planted))), 0.03, rate)
            self.assertGreater(float(np.mean(planted)), 0.03, rate)
            held = self.errors_over_rooms(PredelayMidiSquared, rate,
                                          moves=((PREDELAY_I, 64),),
                                          read_back=True, **moved)
            self.assertLessEqual(float(np.max(np.abs(held))), 0.03, rate)
            clean = self.errors_over_rooms(rate=rate,
                                           moves=((PREDELAY_I, 64),),
                                           **moved)
            self.assertLessEqual(float(np.max(np.abs(clean))), 0.03, rate)

    def test_stuck_dc_turns_the_floor_red(self):
        effect = build(StuckDcAfter)
        t60, floor = m5_cell(effect)
        self.assertFalse(floor)
        effect.deinit()

    def test_the_plants_are_not_on_the_surface(self):
        def handed(effect):
            law = law_t60(effect.handed[0], effect.handed[1], 0.08)
            return effect._loaded[0] / law

        result = reach(LongDecay, handed, tolerance=0.01,
                       builder=handed_build)
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


#: The single Rooms the walks found furthest off the law, each with its
#: reading in % (the figures the docstring printed until the trial of the
#: second process, 2026-09-29): (rate, channels, click LSB, Decay MIDI,
#: Predelay MIDI, Diffusion MIDI, Room seed), all at Damping 500 Hz and
#: 0.08 s. The walk behind the mono cells is the
#: re-audit round-1 audit's (`convolutionreverb_reaudit1_audit.py mono
#: monowalk`); the stereo cells are its re-refuter's walk
#: (`convolutionreverb_reaudit1_refute.py single`) re-run on the fixed node
#: at audiodsp v0.6.3rc2, where every stereo room moved (re-audit fix round
#: 1: v0.6.2's +16.20 % cell reads otherwise there).
SINGLE_ROOM_CELLS = (
    ((44100, 1, 32767, 0, 0, 32, 43), 23.70),
    ((44100, 1, 3277, 0, 127, 28, 43), 24.02),
    ((48000, 1, 32767, 0, 0, 10, 43), 22.83),
    ((22050, 1, 32767, 0, 0, 46, 61), 21.00),
    ((48000, 2, 32767, 8, 0, 32, 43), 16.56),
    ((22050, 2, 3277, 127, 0, 0, 27), 16.05),
)


def single_room_error(cell, cls=None):
    """(% off the Decay law, floor clean) of one Room at `cell`: a click at
    Mix 2, the Schroeder fit on the sum of the channels' energy, the law
    from the positions this test hands the constructor."""
    rate, channels, value, decay, predelay, diffusion, seed = cell
    effect = build(cls, rate, channels, decay=decay / 127.0,
                   damping_hz=500.0, predelay=predelay / 127.0,
                   diffusion=diffusion / 127.0, room=seed)
    taps = effect.node.taps
    out = at_mix(effect, 127, click(LATENCY + taps + 1024, channels,
                                    value=value))
    effect.deinit()
    ir = out[LATENCY:LATENCY + taps].astype(np.float64)
    t60 = schroeder_t60(np.sum(ir ** 2, axis=1), rate)
    law = law_t60(decay / 127.0, predelay / 127.0, 0.08)
    return 100.0 * (t60 / law - 1.0), not np.any(out[LATENCY + taps:])


class D5SingleRoom(unittest.TestCase):
    """D5's Not claimed line, a single Room with Damping in: the docstring
    says only that one can take more than 15 % longer than the Decay time.
    Each cell the walks found is held to its reading, to the hundredth, and
    every one is past the 15 %."""

    def test_a_single_room_can_take_more_than_15_percent_longer(self):
        for cell, figure in SINGLE_ROOM_CELLS:
            error, floor_clean = single_room_error(cell)
            self.assertTrue(floor_clean, cell)
            self.assertLessEqual(abs(error - figure), 0.006,
                                 (cell, error, figure))
            self.assertGreater(error, 15.0, cell)


# --------------------------------------------------------------------------
# D6 - unit energy, not the source: no synthesis macro is a level control
# --------------------------------------------------------------------------

class D6UnitEnergy(unittest.TestCase):
    """Three clauses since fix round 1: the pooled wet/dry spread <= 0.5 dB,
    |wet/dry| <= 0.5 dB at every cell (the absolute level, which the null
    test already read), and rho < 0.5. Level is both channels pooled. Since
    audiodsp v0.6.3rc2 each side is normalised on its own, and D6's clause
    4 claims it (re-audit fix round 1): `D6Balance` and `D6OneSided`."""

    def spread(self, cls, index, rate=RATE, peak_dbfs=-12.0, grid=GRID):
        """(spread dB, worst |level| dB, worst rho), walking `index` by
        `set_macro` on one instance as a host would."""
        pcm = white(int(1.5 * rate), peak_dbfs=peak_dbfs)
        levels, rhos = [], []
        effect = build(cls, rate)
        for position in grid:
            effect.set_macro(index, position)
            level, r = m6_cell(effect, pcm)
            levels.append(level)
            rhos.append(r)
        effect.deinit()
        return (max(levels) - min(levels), max(abs(v) for v in levels),
                max(rhos))

    def assertGreen(self, reading, label):
        spread, level, worst = reading
        self.assertLessEqual(spread, 0.5, label)
        self.assertLessEqual(level, 0.5, label)
        self.assertLess(worst, 0.5, label)

    def test_decay_and_damping_at_two_levels(self):
        for peak in (-12.0, -30.0):
            for index in (DECAY_I, DAMPING_I):
                self.assertGreen(self.spread(ConvolutionReverb, index,
                                             peak_dbfs=peak), (index, peak))

    def test_predelay_diffusion_room_and_the_lower_rates(self):
        for index in (PREDELAY_I, DIFFUSION_I, ROOM_I):
            self.assertGreen(self.spread(ConvolutionReverb, index), index)
        for rate in (44100, 22050):
            self.assertGreen(self.spread(ConvolutionReverb, DECAY_I, rate),
                             rate)

    def test_an_unnormalised_room_is_red_at_the_defaults(self):
        # Walked by set_macro: the plant's gain follows each re-synthesis.
        spread, _, _ = self.spread(UnnormalisedAfter, DECAY_I)
        self.assertGreater(spread, 0.5)

    def test_a_constantly_hot_room_is_red_on_the_absolute_clause(self):
        # +3 dB at every setting: the spread and rho clauses pass it (the
        # frozen criterion's hole, audit round 1: spread 0.010 dB, rho
        # 0.118); the absolute clause does not.
        spread, level, worst = self.spread(HotRoom, DECAY_I)
        self.assertLessEqual(spread, 0.5)
        self.assertLess(worst, 0.5)
        self.assertGreater(level, 2.5)

    def test_the_hot_room_is_not_on_the_surface(self):
        pcm = white(RATE)
        result = reach(HotRoom, lambda e: m6_cell(e, pcm)[0], tolerance=1.0)
        self.assertGreater(result["target"], 2.5)
        self.assertLess(abs(result["clean"]), 0.5)
        self.assertEqual(result["checked"], WALKED)

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


#: D6 (4)'s bar: each side of a stereo room within 0.01 dB of the other on
#: the room's own impulse (dossier section 3.6).
BALANCE_BAR_DB = 0.01

#: Where v0.6.2's node leaned widest (re-audit fix round 1 at v0.6.2):
#: (Decay, Damping, Predelay, Diffusion, Room) as MIDI positions, 0.08 s;
#: the fixed node is held to the bar there too, and on a slice through it.
OLD_WIDEST_CELL = {
    48000: (0, 0, 0, 12, 70),
    44100: (0, 0, 0, 13, 70),
    22050: (0, 0, 0, 22, 70),
}
OLD_WIDEST_OTHER_CELL = (0, 0, 0, 0, 6)

#: The bound over the walk and the widest setting it found (re-audit fix
#: round 1 at v0.6.3rc2; printed in the docstring until the trial of the
#: second process): L - R +0.0005 dB at 44.1 kHz, Decay 66, Damping 18,
#: Predelay 34, Diffusion 62, Room seed 48.
BALANCE_BOUND_DB = 0.001
BALANCE_WIDEST = (0.0005, 44100, (66, 18, 34, 62), 48)


def build_at_cell(rate, cell, cls=None):
    effect = build(cls, rate=rate)
    for index, midi in zip((DECAY_I, DAMPING_I, PREDELAY_I, DIFFUSION_I,
                            ROOM_I), cell):
        effect.set_macro(index, midi)
    return effect


def room_midi(seed):
    """The Room MIDI position whose seed is `seed` (1 + round(m/127*63))."""
    for midi in range(128):
        if 1 + int(round(midi / 127.0 * 63)) == seed:
            return midi
    raise ValueError(seed)


class D6Balance(unittest.TestCase):
    """D6 (4), each side on its own (re-audit fix round 1, audiodsp
    v0.6.3rc2). Up to v0.6.3rc1 the node scaled a stereo room by the mean
    of its two sides' energies, so the left-right balance moved by at
    least 5.3 dB, and these tests pinned that disclosure. Since audiodsp#164
    each side is unit energy on its own. They now pin the docstring's
    bound and its widest setting to the room, hold v0.6.2's widest cells
    and a slice through them to the bar, and show a side tilted after the
    node red and out of reach of the surface (SideTilt, 0.5 dB; SideNudge,
    0.05 dB)."""

    def test_the_documented_balance_is_what_the_room_reads(self):
        bound = BALANCE_BOUND_DB
        widest, rate, cell, seed = BALANCE_WIDEST
        self.assertLessEqual(bound, BALANCE_BAR_DB)
        self.assertLessEqual(abs(widest), bound)
        effect = build_at_cell(rate, cell + (room_midi(seed),))
        side, pooled = balance(effect)
        effect.deinit()
        self.assertLessEqual(abs(side - widest), 0.00006, (rate, side))
        self.assertLessEqual(abs(pooled), 0.01, rate)
        for rate in RATES:
            for cell in (OLD_WIDEST_CELL[rate], OLD_WIDEST_OTHER_CELL):
                effect = build_at_cell(rate, cell)
                side, pooled = balance(effect)
                effect.deinit()
                self.assertLessEqual(abs(side), bound, (rate, cell, side))
                self.assertLessEqual(abs(pooled), 0.01, (rate, cell))

    def test_no_cell_of_the_slice_is_past_the_bound(self):
        bound = BALANCE_BOUND_DB
        for rate in RATES:
            diffusion = OLD_WIDEST_CELL[rate][3]
            effect = build_at_cell(rate, OLD_WIDEST_CELL[rate])
            readings = []
            for position in range(128):
                effect.set_macro(DIFFUSION_I, position)
                readings.append(balance(effect)[0])
            effect.set_macro(DIFFUSION_I, diffusion)
            for position in range(0, 128, 2):
                effect.set_macro(ROOM_I, position)
                readings.append(balance(effect)[0])
            effect.deinit()
            self.assertLessEqual(max(abs(v) for v in readings), bound, rate)

    def test_a_tilted_side_is_red_and_not_on_the_surface(self):
        for plant, gain in ((SideTilt, 0.5), (SideNudge, 0.05)):
            for rate in RATES:
                effect = build(plant, rate)
                side, _ = balance(effect)
                effect.deinit()
                self.assertGreater(abs(side), BALANCE_BAR_DB, (plant, rate))
                self.assertAlmostEqual(side, gain, delta=0.002)
        result = reach(SideNudge, lambda e: balance(e)[0], tolerance=0.02)
        self.assertAlmostEqual(result["target"], 0.05, delta=0.002)
        self.assertLessEqual(abs(result["clean"]), BALANCE_BAR_DB)
        self.assertEqual(result["checked"], WALKED)


def one_sided_level(side, cls=None, rate=RATE, **options):
    """Pooled wet/dry dB at Mix 2 of the kit's white noise (seed 12345,
    -12 dBFS peak, 3 s) on `side` alone, the other side silent, read after
    the room has built."""
    effect = build(cls, rate, predelay=0.0, **options)
    pcm = white(3 * rate)
    pcm[:, 1 - side] = 0
    out = at_mix(effect, 127, pcm)
    start = LATENCY + effect.node.taps
    effect.deinit()
    wet = out[start:].astype(np.float64)
    dry = pcm[start - LATENCY:len(pcm) - LATENCY].astype(np.float64)
    return float(10 * np.log10(np.mean(wet ** 2) / np.mean(dry ** 2)))


class D6OneSided(unittest.TestCase):
    """The one-sided example the docstring printed until the trial of the
    second process, read at its Rooms (re-audit fix round 1, audiodsp
    v0.6.3rc2). Up to v0.6.3rc1 white noise on
    one side came back up to 2.7 dB off its level, with a sign that turned
    with the Room; since each side is normalised on its own it comes back
    within a few tenths. Each printed figure is held to its printed
    hundredth, and each within D6's 0.5 dB."""

    def test_the_documented_one_sided_example_is_what_the_room_reads(self):
        corner = dict(decay=0.0, damping_hz=500.0, diffusion=0.0)
        cells = [(dict(corner, room=36), -0.06, 0.15),
                 (dict(corner, room=1), 0.02, -0.21)]
        for options, left, right in cells:
            for side, printed in ((0, left), (1, right)):
                level = one_sided_level(side, **options)
                self.assertLessEqual(abs(level - printed), 0.006,
                                     (options, side, level, printed))
                self.assertLessEqual(abs(level), 0.5, (options, side))


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
        # Built at patch 0, reset's program_change(0) finds the room it
        # holds and does not re-synthesize, so only the reset clears it.
        # Built from the plain defaults, whose exact Damping 6 000 Hz and
        # Mix 0.6 are not patch 0's grid values (6 059.8 Hz, 0.598), it
        # re-synthesizes. Up to audiodsp v0.6.3rc1 the node emptied itself
        # on that re-synthesis and NoReset was inert there (audit round 1:
        # peak 0 clean and planted); since v0.6.3rc2 (#163) a re-synthesis
        # keeps the history, so NoReset is red from both (re-audit fix
        # round 1).
        for options in (dict(patch=0), {}):
            for cls, silent in ((ConvolutionReverb, True), (NoReset, False)):
                effect = build(cls, **options)
                burst = np.vstack([white(1024), silence(8192)])
                effect._source.swap(probes.ArraySource(burst, rate=RATE,
                                                       channels=2))
                audiocore.reset_buffer(effect.node)
                for _ in range(6):
                    audiocore.get_buffer(effect.output)
                effect.reset()
                self.assertEqual(effect.patch_index, 0)
                out = bytearray()
                for _ in range(8):
                    out += bytes(audiocore.get_buffer(effect.output)[1])
                peak = int(np.max(np.abs(np.frombuffer(bytes(out),
                                                       dtype=np.int16))))
                if silent:
                    self.assertEqual(peak, 0, options)
                else:
                    self.assertGreater(peak, 0, options)
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

# --------------------------------------------------------------------------
# The claims (the trial of the second process, 2026-09-29)
# --------------------------------------------------------------------------

#: (sentence, word for word as the class docstring has it, and the test
#: that asserts it). Every sentence in the docstring that makes a claim is
#: here; one that could not be tied to a test was struck.
CLAIMS = (
    ("By default the room is 0.08 s long.", "test_the_laws_at_the_defaults"),
    ("Decay is how long the room rings, Damping darkens its tail, Predelay "
     "puts silence between the dry and the room, and Diffusion fades the "
     "room in instead of starting it as a burst.",
     "test_what_each_knob_does"),
    ("Room picks one of 64 rooms of the same size.",
     "test_room_picks_one_of_64_rooms"),
    ("Damping runs from 500 Hz at its bottom stop to out at its top stop.",
     "test_what_each_knob_does"),
    ("At 22.05 kHz its brightest positions below the top stop clamp and all "
     "make the same room.", "test_damping_clamps_at_the_rate"),
    ("Mix runs from 0 to 2: the dry at unity up to 1, the room alone at 2.",
     "test_the_mix_walk_never_reaches_the_plant"),
    ("With Damping out, each of the 64 Rooms falls 60 dB within 3 % of the "
     "Decay time.", "test_damping_out_every_room_within_3_percent"),
    ("With Damping in, the 64 Rooms fall 60 dB within 2 % of the Decay time "
     "on average.", "test_damping_in_the_64_room_mean_within_2_percent"),
    ("A single Room with Damping in can take more than 15 % longer.",
     "test_a_single_room_can_take_more_than_15_percent_longer"),
    ("At Damping's 500 Hz stop, low material comes back louder than it went "
     "in.", "test_a_dark_room_lifts_low_material"),
    ("Each side of a stereo room is normalised on its own, so the room sits "
     "in the middle.", "test_no_cell_of_the_slice_is_past_the_bound"),
    ("Hand it `impulse=`, int16 frames or the path to a 16-bit PCM WAV at "
     "the graph's rate, and the room is that recording.",
     "test_a_wav_loads_the_same_room_as_its_frames"),
    ("The room is then your source convolved with the impulse at unit "
     "energy, within 1 LSB.",
     "test_within_one_lsb_across_layouts_levels_gain_and_trim"),
    ("`ir_gain_db` trims it from -24 to +12 dB, and `start_ms` cuts up to "
     "200 ms from its start.", "test_impulse_level_and_shape_are_checked"),
    ("Only Mix is live then: the other five knobs raise `IndexError`.",
     "test_measured_mode_refuses_the_synthesis_macros"),
    ("A WAV at another rate raises `ValueError`, and so does an impulse with "
     "no energy or a `start_ms` that trims away every frame.",
     "test_what_measured_mode_refuses"),
    ("An empty impulse, `impulse=b\"\"`, is an undelayed wire whose Mix does "
     "nothing and whose `reset()` silences nothing.",
     "test_an_empty_impulse_is_a_wire_whatever_mix_and_reset"),
    ("`seconds` is the longest room the instance can hold, carved once when "
     "you build it: from 0.06 s up to 131 072 frames, and outside that the "
     "constructor raises `ValueError`.",
     "test_every_cell_builds_or_raises_by_the_law"),
    ("`latency_samples` reads 256 while an impulse is loaded and 0 on the "
     "empty impulse.", "test_loaded_every_patch_and_the_predelay_stop"),
    ("Held at Mix 0, the output is your source, byte for byte, "
     "`latency_samples` late, while the source keeps feeding it and nothing "
     "resets it.", "test_every_macro_stop_and_patch_with_mix_at_0"),
    ("`tail_samples` is `latency_samples` plus the loaded room rounded up to "
     "a whole block of 256 frames.",
     "test_tail_is_latency_plus_the_loaded_impulse"),
    ("More than `tail_samples` frames after your input's last non-zero "
     "frame, the output is exact zero.",
     "test_the_tail_counts_the_frames_the_source_hands"),
    ("No frame of your dry signal drops or repeats when you move a room "
     "knob, at any Mix, however many moves you make.",
     "test_no_dry_frame_drops_after_any_number_of_changes"),
    ("From the end of the block in flight, the output is that of an "
     "instance that always had the new settings.",
     "test_every_move_has_landed_from_the_end_of_the_block_in_flight"),
    ("A Mix move acts from the end of the block in flight, so Mix 0 reaches "
     "the plain source up to 256 frames late.",
     "test_a_mix_move_lands_a_partition_late_and_reset_drops_one"),
    ("`reset()` empties the room and returns to patch 0.",
     "test_reset_empties_the_room"),
    ("With an impulse loaded, `reset()` in the middle of a stream silences "
     "the block in flight, 256 frames, dry included, and with Mix set back "
     "to 0 your source carries on on time after it.",
     "test_a_reset_keeps_the_whole_frames_the_node_holds"),
    ("A host that calls `audiocore.reset_buffer` on the output silences the "
     "block in flight too, but also drops the frames the node holds from a "
     "source buffer it had not finished.",
     "test_a_host_reset_buffer_silences_the_block_and_drops_held_frames"),
)

#: The family's two limits, as ruled on 2026-09-28, word for word.
FAMILY = (
    "A control that jumps makes the output step: move it in small steps "
    "from the host if you need it smooth.",
    "The tail rings only while the source keeps feeding: feed silence to let "
    "it ring out. A tail cut short by a source that stopped carries on when "
    "the source comes back.",
)


def _flat(text):
    return " ".join((text or "").split())


def chord(rate, frames, channels):
    """220, 277 and 330 Hz summed, at an 8 000 LSB peak."""
    t = np.arange(frames) / float(rate)
    x = sum(np.sin(2 * np.pi * hz * t) for hz in (220.0, 277.0, 330.0))
    x = np.round(8000.0 * x / np.max(np.abs(x))).astype(np.int16)
    return np.repeat(x[:, None], channels, axis=1)


def wire_render(cls, rate, channels, pcm, size, at, action, blocks=40,
                **options):
    """`blocks` pulls at Mix 0 from a source in `size`-frame calls;
    `action(effect)` just before pull `at`, then Mix put back to 0. Returns
    the output and the frame where pull `at` starts."""
    effect = build(cls, rate, channels, mix=0.0, **options)
    effect._source.swap(DryOnce(pcm, rate, channels, None, size))
    audiocore.reset_buffer(effect.node)
    out = []
    for number in range(blocks):
        if number == at:
            action(effect)
            effect.set_macro(MIX_I, 0)
        out.append(np.frombuffer(bytes(audiocore.get_buffer(effect.output)[1]),
                                 dtype=np.int16).reshape(-1, channels))
    effect.deinit()
    return np.vstack(out), at * 256


def counting(frames, channels):
    """A source with no zero frame and no two frames alike nearby."""
    pcm = ((np.arange(frames) * 7) % 20001 - 10000).astype(np.int16)
    pcm[pcm == 0] = 1
    return np.repeat(pcm[:, None], channels, axis=1)


class TheClaims(unittest.TestCase):
    def test_every_claim_is_in_the_docstring_and_tested(self):
        doc = _flat(ConvolutionReverb.__doc__)
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
        for sentence in FAMILY:
            self.assertIn(sentence, doc, sentence)
        numbers = [w for w in rest.split() if any(c.isdigit() for c in w)]
        self.assertEqual(numbers, [])

    def test_what_each_knob_does(self):
        # On the room's own impulse (a click at Mix 2, 48 kHz): Decay 127
        # rings longer than Decay 0; Damping at its 500 Hz bottom stop
        # leaves under a fifth of the share of the tail's second half above
        # 4 kHz that its top stop leaves, which
        # hands the node no roll-off at all; Predelay 127 leaves 15 ms of
        # silence after the latency before the room, Predelay 0 none; and
        # Diffusion 127 starts the room at least 6 dB quieter over its first
        # 5 ms than Diffusion 0, with the same energy overall.
        def impulse(**options):
            effect = build(mix=2.0, **options)
            taps = effect.node.taps
            out = run(effect, click(LATENCY + taps + 256))
            synthesis = effect._synthesis()
            effect.deinit()
            return out[LATENCY:LATENCY + taps].astype(np.float64), synthesis

        long_room, _ = impulse(decay=1.0, damping_hz=0.0)
        short_room, _ = impulse(decay=0.0, damping_hz=0.0)
        self.assertGreater(schroeder_t60(np.sum(long_room ** 2, axis=1), RATE),
                           1.4 * schroeder_t60(np.sum(short_room ** 2, axis=1),
                                               RATE))

        def top(ir):
            ir = ir[len(ir) // 2:]              # the tail's second half
            spectrum = np.abs(np.fft.rfft(ir[:, 0])) ** 2
            hz = np.fft.rfftfreq(len(ir), 1.0 / RATE)
            return float(np.sum(spectrum[hz > 4000.0]) / np.sum(spectrum))

        dark, synthesis = impulse(damping_hz=500.0)
        self.assertAlmostEqual(synthesis[1], 500.0, places=6)
        effect = build()
        effect.set_macro(DAMPING_I, 0)
        self.assertAlmostEqual(effect._synthesis()[1], 500.0, places=6)
        effect.set_macro(DAMPING_I, 127)
        self.assertEqual(effect._synthesis()[1], 0.0)
        effect.deinit()
        bright, synthesis = impulse(damping_hz=0.0)
        self.assertEqual(synthesis[1], 0.0)
        self.assertLess(top(dark), 0.2 * top(bright))

        late, _ = impulse(predelay=1.0, diffusion=0.0)
        early, _ = impulse(predelay=0.0, diffusion=0.0)
        self.assertEqual(first_arrival(late), 720)
        self.assertEqual(first_arrival(early), 0)

        soft, _ = impulse(diffusion=1.0)
        hard, _ = impulse(diffusion=0.0)
        head = int(0.005 * RATE)
        self.assertLess(10 * np.log10(np.sum(soft[:head] ** 2)
                                      / np.sum(hard[:head] ** 2)), -6.0)

    def test_room_picks_one_of_64_rooms(self):
        # Walked by set_macro over every position: 64 seeds, 64 impulses no
        # two alike, all on one allocation, and each on the Decay law with
        # Damping out (D5 walks that within 3 %).
        effect = build(damping_hz=0.0)
        taps = effect.node.taps
        pulse = click(LATENCY + taps + 256)
        seeds, rooms = set(), set()
        for midi in range(128):
            effect.set_macro(ROOM_I, midi)
            seeds.add(effect._synthesis()[4])
            rooms.add(digest(at_mix(effect, 127, pulse)))
            self.assertEqual(effect.node.taps, taps)
        effect.deinit()
        self.assertEqual(seeds, set(range(1, 65)))
        self.assertEqual(len(rooms), 64)

    def test_a_dark_room_lifts_low_material(self):
        # A low chord at Mix 2, the level after the room has built, at
        # Damping's 500 Hz stop: louder than the dry at three rates, stereo
        # and mono, at 16 Rooms and three Decays (the least lift over that
        # walk is about 2 dB). No number is claimed: the lift turns with the
        # Room.
        least = None
        for rate in RATES:
            for channels in (2, 1):
                pcm = chord(rate, int(1.5 * rate), channels)
                for decay in (0.0, 0.5, 1.0):
                    effect = build(rate=rate, channels=channels, decay=decay,
                                   damping_hz=500.0)
                    for room in range(0, 128, 8):
                        effect.set_macro(ROOM_I, room)
                        level, _ = m6_cell(effect, pcm)
                        least = level if least is None else min(least, level)
                        self.assertGreater(level, 0.0,
                                           (rate, channels, decay, room))
                    effect.deinit()
        self.assertGreater(least, 1.0)

    def test_what_measured_mode_refuses(self):
        with tempfile.TemporaryDirectory() as folder:
            path = ImpulseFiles().write(folder, 44100, 1, 900)
            with self.assertRaises(ValueError):
                build(impulse=path)
        with self.assertRaises(ValueError):
            build(impulse=np.zeros(512, dtype=np.int16).tobytes())
        with self.assertRaises(ValueError):
            build(impulse=make_impulse(100).tobytes(), start_ms=2.1)

    def test_an_empty_impulse_is_a_wire_whatever_mix_and_reset(self):
        # `impulse=b""`: at Mix 0, 0.6, 1.2 and 2, across a reset() before
        # pull 20 (Mix put back after it) and a host `reset_buffer` on the
        # output before pull 25, the output is the source frame for frame,
        # with no latency and no frame silenced. ResetSilentOnEmpty (a
        # reset that plays 256 frames of silence) is red.
        for rate in (48000, 22050):
            for channels in (2, 1):
                pcm = counting(40 * 256, channels)
                for cls in (None, ResetSilentOnEmpty):
                    for midi in (0, 38, 76, 127):
                        effect = build(cls, rate, channels, impulse=b"")
                        effect.set_macro(MIX_I, midi)
                        effect._source.swap(probes.ArraySource(
                            pcm, rate=rate, channels=channels))
                        audiocore.reset_buffer(effect.node)
                        out = bytearray()
                        for number in range(40):
                            if number == 20:
                                effect.reset()
                                effect.set_macro(MIX_I, midi)
                            if number == 25:
                                audiocore.reset_buffer(effect.output)
                            out += bytes(audiocore.get_buffer(
                                effect.output)[1])
                        effect.deinit()
                        out = np.frombuffer(bytes(out), dtype=np.int16
                                            ).reshape(-1, channels)
                        label = (rate, channels, cls, midi)
                        if cls is None:
                            self.assertEqual(digest(out), digest(pcm), label)
                        else:
                            self.assertNotEqual(digest(out), digest(pcm),
                                                label)

    def test_a_reset_keeps_the_whole_frames_the_node_holds(self):
        # The re-audit's ask: a reset() while the node holds part of a
        # source buffer. From sources in 512-, 100- and 256-frame calls, at
        # Mix 0, the reset before pull 20 or 21 (with 512-frame calls pull
        # 21 finds the node holding half a buffer; with 100-frame calls
        # both do): the 256 frames after it are exact zero and every other
        # frame is the source on time. ReplugOnReset (the source plugged
        # back into the node on reset, which drops what the node held) is
        # red wherever the node held frames, and clean where it held none.
        for rate in (48000, 22050):
            for channels in (2, 1):
                pcm = counting(40 * 256, channels)
                wire = np.vstack([silence(LATENCY, channels), pcm])
                for size in (512, 100, 256):
                    for at in (20, 21):
                        held = (at * 256) % size != 0
                        for cls in (None, ReplugOnReset):
                            out, a = wire_render(cls, rate, channels, pcm,
                                                 size, at,
                                                 lambda e: e.reset())
                            want = wire[:len(out)].copy()
                            want[a:a + 256] = 0
                            label = (rate, channels, size, at, cls)
                            if cls is None or not held:
                                self.assertEqual(digest(out), digest(want),
                                                 label)
                            else:
                                self.assertNotEqual(digest(out),
                                                    digest(want), label)

    def test_a_host_reset_buffer_silences_the_block_and_drops_held_frames(
            self):
        # A host `audiocore.reset_buffer(effect.output)` before pull 21, at
        # Mix 0: the 256 frames after it are exact zero, and from then on
        # the output is the source moved on by the frames the node held of
        # its current buffer: none from 256-frame calls, 256 from 512-frame
        # calls, 24 from 100-frame calls (54 calls handed 5 400 frames and
        # the node had taken 5 376). audiodsp: the node's reset drops them.
        for rate in (48000, 22050):
            for channels in (2, 1):
                pcm = counting(44 * 256, channels)
                for size, dropped in ((256, 0), (512, 256), (100, 24)):
                    out, a = wire_render(
                        None, rate, channels, pcm, size, 21,
                        lambda e: audiocore.reset_buffer(e.output))
                    label = (rate, channels, size)
                    wire = np.vstack([silence(LATENCY, channels), pcm])
                    self.assertEqual(digest(out[:a]), digest(wire[:a]), label)
                    self.assertEqual(int(np.max(np.abs(out[a:a + 256]))), 0,
                                     label)
                    rest = out[a + 256:]
                    self.assertEqual(
                        digest(rest),
                        digest(pcm[a + dropped:a + dropped + len(rest)]),
                        label)


if __name__ == "__main__":
    unittest.main()
