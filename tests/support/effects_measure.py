"""What the audioeffects test modules build and measure with.

The effects suite is split by what retires each part. The contract-level
tests over `audioeffects.ALL` live in `test_cpython_effects_library.py` and
are not retired at all; each family's old-surface trait tests live in a
module the family phase deletes when it rebuilds those classes
(`test_cpython_effects_dynamics_eq.py`, `..._modulation.py`, `..._drive.py`,
`..._time.py`, `..._pitch.py`, `..._racks.py`), and
`test_cpython_convolve_node.py` holds the audioconvolve node checks, which
belong to the palette and outlive every rewrite. The building and measuring
they have in common is here, so retiring one module disturbs no other.

Imported the way `tests/support/ulab` is - `tests/support` on `sys.path`,
then a plain import - so a module works both under `unittest discover` and
when it is named on its own.

The analysis primitives (`_fft`, `spectrum`, `harmonic_db`, `rms`, `peak`,
`tone_gain_db`, `tilt_db`, `sine`, `burst`, `channels`, `loudest_in`) are
numpy-free on purpose: they are what the measurement kit takes over, and the
kit runs where audioif builds (docs/effects-kit-spec.md section 2).
"""

import math
from array import array

import audiocore
import audioeffects

SAMPLE_RATE = 48000
audioeffects.configure(SAMPLE_RATE)

#: Arguments a class needs beyond a source. ConvolutionReverb's default
#: second of stereo impulse is 1.5 MB and the patch tests walk it once per
#: patch -- a quarter second proves the same things and keeps the suite quick.
#: `GraphicEQ`'s entry is gone with its rebuild: the old class had no
#: default curve, the rebuilt one is flat by default and flat is a
#: wire, and handing it a curve here made patch 0 stop matching the
#: constructor's own defaults.
EXTRA_ARGUMENTS = {
    "ConvolutionReverb": {"seconds": 0.25},
}


def source(frames=4096, level=11000, rate=SAMPLE_RATE):
    """A stereo signal with content across the spectrum, loud enough to trip
    every threshold the library's defaults use."""
    values = array("h")
    for frame in range(frames):
        for channel in range(2):
            shape = ((frame * (61 + channel * 17)) % 401) - 200
            values.append(shape * level // 200)
    return audiocore.RawSample(values, sample_rate=rate, channel_count=2)


def build(name, **overrides):
    arguments = dict(EXTRA_ARGUMENTS.get(name, ()))
    arguments.update(overrides)
    return getattr(audioeffects, name)(source(), **arguments)


def peak(sample, blocks, skip=0):
    """Loudest sample over `blocks` buffers, after discarding `skip` of them.

    Skipping matters for anything with an envelope follower: the frames before
    its detector has risen pass through untouched, so a peak taken from the
    very start measures the attack transient rather than the effect.
    """
    loudest = 0
    for _ in range(skip):
        audiocore.get_buffer(sample)
    for _ in range(blocks):
        data = memoryview(bytes(audiocore.get_buffer(sample)[1])).cast("h")
        for value in data:
            loudest = max(loudest, -value if value < 0 else value)
    return loudest / 32768.0


def sine(hz, frames=40000, level=8000, rate=SAMPLE_RATE):
    """A stereo sine, long enough to outlast the skip in `rms`."""
    values = array("h")
    for frame in range(frames):
        value = int(level * math.sin(2.0 * math.pi * hz * frame / rate))
        values.append(value)
        values.append(value)
    return audiocore.RawSample(values, sample_rate=rate, channel_count=2)


def rms(sample, blocks=20, skip=8):
    total = 0
    count = 0
    for _ in range(skip):
        audiocore.get_buffer(sample)
    for _ in range(blocks):
        data = memoryview(bytes(audiocore.get_buffer(sample)[1])).cast("h")
        for value in data:
            total += value * value
            count += 1
    return math.sqrt(total / count) if count else 0.0


def tone_gain_db(hz, build_chain):
    """What `build_chain` does to a steady sine at `hz`, in dB. The dry
    reference is a second copy of the same sine measured the same way, so
    only the chain differs."""
    wet = rms(build_chain(sine(hz)))
    dry = rms(sine(hz))
    return 20.0 * math.log10(wet / dry)


def tilt_db(build_chain, high=16000.0, reference=1000.0):
    """How much darker or brighter `build_chain` leaves the top end, in dB
    relative to what it does at `reference`. A saturation curve costs a
    broadband decibel or so on its own, and that is level, not tone; the
    difference between the two frequencies is the tone."""
    return (tone_gain_db(high, build_chain)
            - tone_gain_db(reference, build_chain))


def spectrum(sample, blocks=20, skip=8):
    """Magnitude spectrum of the left channel, and the bin width, from a
    power-of-two window so no FFT padding is involved."""
    values = []
    for _ in range(skip):
        audiocore.get_buffer(sample)
    for _ in range(blocks):
        data = memoryview(bytes(audiocore.get_buffer(sample)[1])).cast("h")
        values.extend(data[0::2])
    size = 1
    while size * 2 <= len(values):
        size *= 2
    window = [0.5 - 0.5 * math.cos(2.0 * math.pi * i / size)
              for i in range(size)]
    real = [values[i] * window[i] for i in range(size)]
    imaginary = [0.0] * size
    _fft(real, imaginary)
    half = size // 2
    return ([math.hypot(real[i], imaginary[i]) for i in range(half)],
            SAMPLE_RATE / float(size))


def _fft(real, imaginary):
    """In-place radix-2 FFT. No numpy: these tests run wherever audioif
    builds, and the parity interpreters have no third-party packages."""
    size = len(real)
    j = 0
    for i in range(1, size):
        bit = size >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            real[i], real[j] = real[j], real[i]
            imaginary[i], imaginary[j] = imaginary[j], imaginary[i]
    length = 2
    while length <= size:
        angle = -2.0 * math.pi / length
        step_real, step_imaginary = math.cos(angle), math.sin(angle)
        for start in range(0, size, length):
            wr, wi = 1.0, 0.0
            for offset in range(length // 2):
                a, b = start + offset, start + offset + length // 2
                tr = real[b] * wr - imaginary[b] * wi
                ti = real[b] * wi + imaginary[b] * wr
                real[b], imaginary[b] = real[a] - tr, imaginary[a] - ti
                real[a], imaginary[a] = real[a] + tr, imaginary[a] + ti
                wr, wi = wr * step_real - wi * step_imaginary, \
                    wr * step_imaginary + wi * step_real
        length *= 2


def harmonic_db(build_chain, hz=1000.0, orders=(2, 3)):
    """Each named harmonic of `hz`, in dB relative to the fundamental."""
    magnitudes, bin_hz = spectrum(build_chain(sine(hz, frames=80000)))

    def peak_near(frequency):
        lo = max(0, int(frequency * 0.97 / bin_hz))
        hi = min(len(magnitudes), int(frequency * 1.03 / bin_hz) + 1)
        return max(magnitudes[lo:hi]) if hi > lo else 0.0

    base = peak_near(hz)
    out = []
    for order in orders:
        value = peak_near(hz * order)
        out.append(20.0 * math.log10(value / base)
                   if value > 0.0 and base > 0.0 else -200.0)
    return out


def burst(hz, on=2000, total=48000, level=9000, rate=SAMPLE_RATE):
    """A short tone and then silence, so a delay's repeats arrive one at a
    time and can be measured separately."""
    values = array("h")
    for frame in range(total):
        value = int(level * math.sin(2.0 * math.pi * hz * frame / rate)) \
            if frame < on else 0
        values.append(value)
        values.append(value)
    return audiocore.RawSample(values, sample_rate=rate, channel_count=2)


def channels(sample, blocks):
    """Both channels of `blocks` buffers, as two lists of samples."""
    left, right = [], []
    for _ in range(blocks):
        data = memoryview(bytes(audiocore.get_buffer(sample)[1])).cast("h")
        left.extend(data[0::2])
        right.extend(data[1::2])
    return left, right


def loudest_in(values, start, length):
    window = values[start:start + length]
    return max((-v if v < 0 else v) for v in window) if window else 0
