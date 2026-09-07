"""Probe material and a render loop for the measurement kit's fault battery.

Two things live here, both deliberately small:

**Sources.** `ArraySource` is the audiocore sample protocol over an int16
array, handing back `block` frames per `get_buffer` - which is section 1's
fourth axis, the one whose absence renders the whole split family silent
(`MultibandCompressor` A-M5). `SwitchableSource` is what STATE needs to swap
the borrowed source for a silent one without rebuilding the class.

**Probes.** The subset of `docs/effects-kit-spec.md` section 3 that the first
ten measurements' planted faults need: `ramp_fs`, `click_stereo`,
`burst_silence`, `dc_step`, `sine`, `staircase`, `alt_fs`, `noise_det`, and a
quiet chord-shaped stand-in. They are generated in process, per test, so no
stale artifact can be mistaken for a fresh one. The committed corpus under
`tools/effect_probes/` with its `probes.json` manifest is section 3's own
deliverable and is not this file.

`render()` is a **stand-in for `tools/render_effect.py`** (spec section 4),
which did not exist when this battery was written. It keeps that file's
stated contract - pull on block boundaries, stream the PCM, hash it with
FNV-1a, record the axes - and nothing else; when the renderer lands, this
function becomes a call into it and the tests do not change.
"""

import math
import os
import sys
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import audiocore  # noqa: E402
from tools.effect_measurements import Render  # noqa: E402

try:  # pragma: no cover - the renderer part A is writing
    from tools import render_effect as PART_A_RENDERER
except ImportError:
    PART_A_RENDERER = None


class ArraySource:
    """int16 frames, `block` of them per `get_buffer`."""

    def __init__(self, data, rate=48000, channels=2, block=256):
        self.sample_rate = int(rate)
        self.channel_count = int(channels)
        self.bits_per_sample = 16
        self.samples_signed = True
        self.block = int(block)
        payload = data.tobytes() if hasattr(data, "tobytes") else bytes(data)
        self._pcm = memoryview(payload)
        self._stride = self.block * self.channel_count * 2
        self._position = 0

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self._position = 0

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        chunk = bytes(self._pcm[self._position:self._position + self._stride])
        self._position += len(chunk)
        more = 1 if self._position < len(self._pcm) else 0
        return more, memoryview(chunk)


class SwitchableSource:
    """One source the class holds, with a different source behind it.

    STATE's third read swaps the borrowed source for a silent one; a class
    built around its source cannot be asked to let go of it, so the swap
    happens here.
    """

    def __init__(self, inner):
        self.inner = inner
        self.sample_rate = inner.sample_rate
        self.channel_count = inner.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True
        self.block = getattr(inner, "block", 256)

    def swap(self, source):
        self.inner = source
        self.inner._reset_buffer()

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self.inner._reset_buffer(single_channel_output, audio_channel)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        return self.inner._get_buffer(single_channel_output, audio_channel)


# --------------------------------------------------------------------------
# The probes (spec section 3, the subset these ten measurements need)
# --------------------------------------------------------------------------

def _interleave(values, channels):
    out = array("h")
    for value in values:
        for _ in range(channels):
            out.append(int(value))
    return out


def ramp_fs(frames=8192, channels=2):
    """Full-scale ramp. WIRE's required probe: its planted fault is
    invisible on anything peaking below -6.02 dBFS."""
    return _interleave(
        [max(-32768, min(32767, int(round(-32768 + 65535.0 * i
                                          / (frames - 1)))))
         for i in range(frames)], channels)


def sine(hz, seconds, dbfs, rate=48000, channels=2):
    frames = int(seconds * rate)
    amplitude = 10 ** (dbfs / 20.0) * 32767.0
    return _interleave(
        [int(round(amplitude * math.sin(2 * math.pi * hz * i / rate)))
         for i in range(frames)], channels)


def quiet_chord(seconds=0.25, rate=48000, channels=2, dbfs=-12.0):
    """A three-note chord at a level whose peak stays below -6.02 dBFS.

    It is here to be *green* under WIRE's planted fault: `chord` alone
    passes a one-LSB dry scaling, which is the material-cannot-reach-the-
    mechanism shape planted inside the kit's own control.
    """
    frames = int(seconds * rate)
    amplitude = 10 ** (dbfs / 20.0) * 32767.0 / 3.0
    values = []
    for i in range(frames):
        total = sum(math.sin(2 * math.pi * hz * i / rate)
                    for hz in (220.0, 277.18, 329.63))
        values.append(int(round(amplitude * total)))
    return _interleave(values, channels)


def click_stereo(frames=8192, offset=256, channels=2):
    """One full-scale sample at a known offset, identical in both
    channels."""
    return _interleave([32767 if i == offset else 0 for i in range(frames)],
                       channels)


def burst_silence(hz=1000.0, on_ms=200.0, total_s=1.0, dbfs=-6.0,
                  rate=48000, channels=2):
    on = int(rate * on_ms / 1000.0)
    frames = int(rate * total_s)
    amplitude = 10 ** (dbfs / 20.0) * 32767.0
    values = [int(round(amplitude * math.sin(2 * math.pi * hz * i / rate)))
              if i < on else 0 for i in range(frames)]
    return _interleave(values, channels), on


def dc_step(level=0.5, hold_s=0.5, total_s=1.5, rate=48000, channels=2):
    """+-level FS held, then removed while the source still supplies
    frames - the audioif#23 shape."""
    held = int(rate * hold_s)
    frames = int(rate * total_s)
    value = int(round(level * 32767))
    values = [value if i < held else 0 for i in range(frames)]
    return _interleave(values, channels), held


def alt_fs(frames=4096, level=32767, channels=2):
    return _interleave([level if i % 2 == 0 else -level
                        for i in range(frames)], channels)


def noise_det(frames=8192, dbfs=-12.0, seed=12345, channels=2):
    """Deterministic PRNG, fixed seed - the same bytes on every
    interpreter, which `random` does not promise."""
    amplitude = 10 ** (dbfs / 20.0) * 32767.0
    state = seed
    values = []
    for _ in range(frames):
        state = (1103515245 * state + 12345) & 0x7fffffff
        values.append(int(round(amplitude * ((state / 0x3fffffff) - 1.0))))
    return _interleave(values, channels)


def staircase(levels_db, hz=1000.0, step_s=0.4, rate=48000, channels=2):
    """1 kHz sine in steps. Returned as one array plus the frame each step
    starts at, so CURVE can read the settled half of every step."""
    out = array("h")
    starts = []
    step = int(rate * step_s)
    for level in levels_db:
        starts.append(len(out) // channels)
        amplitude = 10 ** (level / 20.0) * 32767.0
        for i in range(step):
            value = int(round(amplitude
                              * math.sin(2 * math.pi * hz * i / rate)))
            for _ in range(channels):
                out.append(value)
    return out, starts



def step_tone(hz, stages, rate=48000, channels=2):
    """One continuous sine that changes level at stated times.

    `stages` is [(seconds, dBFS), ...]. The phase runs through the joins, so
    the level step is a level step and not a click - which matters for
    GAINTRACE, whose release must be read against an input that is still
    there. A burst into silence has no dry envelope to divide by, and the
    gain-reduction trace is undefined exactly where the release is.

    Returns the array and the frame each stage starts at.
    """
    out = array("h")
    starts = []
    frame = 0
    for seconds, dbfs in stages:
        starts.append(len(out) // channels)
        amplitude = 10 ** (dbfs / 20.0) * 32767.0
        for _ in range(int(seconds * rate)):
            value = int(round(amplitude
                              * math.sin(2 * math.pi * hz * frame / rate)))
            for _ in range(channels):
                out.append(value)
            frame += 1
    return out, starts


def silence(frames=48000, channels=2):
    return array("h", [0] * (frames * channels))


# --------------------------------------------------------------------------
# The render loop - a stand-in for tools/render_effect.py (spec section 4)
# --------------------------------------------------------------------------

def render(node, frames, *, rate=48000, channels=2, block=256, label=None,
           probe=None, class_name=None, class_version=None,
           latency_samples=None, path=None):
    """Pull `frames` frames from `node` and return them as a `Render`.

    The contract is section 4's: pulls are whole blocks, the PCM is hashed
    with FNV-1a excluding any header, and the axes travel with the numbers.
    A node that runs dry hands back an empty buffer; the render is padded
    with silence to the length asked for rather than being reported short,
    so a measurement reading a tail is reading the class's zeros and not the
    end of the array.
    """
    want = frames * channels * 2
    pcm = bytearray()
    while len(pcm) < want:
        _, data = audiocore.get_buffer(node)
        chunk = bytes(data)
        if not chunk:
            pcm += bytes(want - len(pcm))
            break
        pcm += chunk
    pcm = bytes(pcm[:want])
    if path is not None:
        _write_wav(path, pcm, rate, channels)
    return Render(pcm, rate, channels, block=block,
                  interpreter="cpython", label=label, probe=probe,
                  class_name=class_name, class_version=class_version,
                  latency_samples=latency_samples, path=path)


def _write_wav(path, pcm, rate, channels):
    byte_rate = rate * channels * 2
    header = (b"RIFF" + (36 + len(pcm)).to_bytes(4, "little")
              + b"WAVEfmt " + (16).to_bytes(4, "little")
              + (1).to_bytes(2, "little") + channels.to_bytes(2, "little")
              + rate.to_bytes(4, "little") + byte_rate.to_bytes(4, "little")
              + (channels * 2).to_bytes(2, "little") + (16).to_bytes(2, "little")
              + b"data" + len(pcm).to_bytes(4, "little"))
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(pcm)
