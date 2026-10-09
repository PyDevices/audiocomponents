"""How long a class rings after its input stops, against what it declares
(audiocomponents#114).

`ring()` plays a full-scale burst into a class, makes the given control
moves as the input stops, and then feeds silence. It returns the frames from
the input's last non-zero frame to the output's last non-zero frame, and the
bound the class declares once the moves are made: `tail_samples` plus
`latency_samples`, the reading the lifecycle matrix's P2 uses. A class keeps
its promise where the first is at most the second.

CPython only: it uses numpy for the material.
"""

import numpy as np

import audiocore
import audioeffects

VENDOR = "PyDevices"

BLOCK = 256


class Burst:
    """`pcm` in 256-frame blocks, then silence for ever."""

    def __init__(self, pcm, rate, channels):
        self.sample_rate = rate
        self.channel_count = channels
        self.bits_per_sample = 16
        self.samples_signed = True
        self._data = pcm.tobytes()
        self._position = 0
        self._stride = BLOCK * channels * 2

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        pass

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        chunk = self._data[self._position:self._position + self._stride]
        self._position += len(chunk)
        if len(chunk) < self._stride:
            chunk += bytes(self._stride - len(chunk))
        return 1, memoryview(chunk)


def burst(frames, channels, rate, kind="noise", peak=30000.0, seed=114):
    """Full-scale noise, or a sine at `kind` Hz."""
    if kind == "noise":
        rng = np.random.RandomState(seed)
        x = rng.uniform(-1, 1, (frames, channels)) * peak
    else:
        t = np.arange(frames) / float(rate)
        x = np.repeat((peak * np.sin(2 * np.pi * float(kind) * t))[:, None],
                      channels, axis=1)
    return np.round(x).astype(np.int16)


def ring(name, rate, channels, patch=None, start=(), moves=(), kind="noise",
         frames=8192, options=None, cls=None):
    """(frames rung, frames declared) for one cell, or None where the class
    declares no bound. `start` is (macro, MIDI) applied before the burst,
    `moves` the same as the input stops. `cls` builds a class directly
    instead of through `audioeffects.create`."""
    pcm = burst(frames, channels, rate, kind)
    last_in = int(np.nonzero(np.any(pcm != 0, axis=1))[0][-1])
    source = Burst(pcm, rate, channels)
    if cls is None:
        effect = audioeffects.create(name, source, rate, **(options or {}))
    else:
        effect = cls(source, sample_rate=rate, **(options or {}))
    if patch is not None:
        effect.program_change(patch)
    for index, value in start:
        effect.set_macro(index, value)
    out = []
    pulled = 0
    while pulled < frames:
        data = bytes(audiocore.get_buffer(effect.output)[1])
        out.append(data)
        pulled += len(data) // (2 * channels)
    for index, value in moves:
        effect.set_macro(index, value)
    tail = effect.tail_samples
    if tail is None:
        effect.deinit()
        return None
    bound = tail + effect.latency_samples
    while pulled < frames + 2 * bound + 8 * BLOCK:
        data = bytes(audiocore.get_buffer(effect.output)[1])
        out.append(data)
        pulled += len(data) // (2 * channels)
    effect.deinit()
    y = np.frombuffer(b"".join(out), dtype=np.int16).reshape(-1, channels)
    hits = np.nonzero(np.any(y != 0, axis=1))[0]
    last_out = int(hits[-1]) if len(hits) else -1
    return last_out - last_in, bound
