"""The planted faults for the measurement kit's first ten measurements.

`docs/effects-kit-spec.md` section 6 is the discipline these are held to: a
fault that does not turn its own measurement red is not a planted fault, and
a battery without a control that must pass only proves the checker always
fails. Each fault below is the one the spec names for its measurement, and
each is the cheap version - a node in the path, a subclass, or a byte in the
render - never a change to a library file.

What is a shipped class and what is a stand-in, said plainly:

* WIRE, LEVEL, TAIL, SPECTRUM plant a **node** in a shipped class's path.
* CLICK, STATE, RESPONSE plant a **subclass** of a shipped class.
* CURVE plants nothing new: the shipped Compressor's own `knee_db` is the
  soft-knee-to-hard-knee change the spec names.
* DIGEST perturbs the **render bytes**, which is what its fault is.
* GAINTRACE's subject is a two-stage release, and **no shipped class has
  one** - the node has a single `release_ms`. Its control and its fault are
  therefore both this file's `TwoStageRelease`, built to the spec's shape:
  a fast stage down to a switch depth and a slow one below it, against the
  same class collapsed to the fast constant.
"""

import math

import numpy as np

import audioeffects

#: `ShiftedCornerLowPass` subclasses a rebuilt class, and `_component`
#: reads `VENDOR` off the module a class is *defined* in, not off the module
#: its base came from. Without this the metadata check refuses the fault
#: before it can be measured.
VENDOR = "PyDevices"
import audiofilters
import synthio
from audioeffects import _core

#: `_component` reads VENDOR off the module a class is defined in, and the
#: CLICK fault below is a subclass of a rebuilt class. Without this the fault
#: would refuse to construct, which is a fault that cannot fail.
VENDOR = "PyDevices"


class _Node:
    """A pure-Python audio node: the audiocore sample protocol, int16 in and
    int16 out, `deinit` and `_deinited` so STATE's node enumeration sees it
    the way it sees a native node."""

    def __init__(self, source):
        self._source = source
        self.sample_rate = source.sample_rate
        self.channel_count = source.channel_count
        self.bits_per_sample = 16
        self.samples_signed = True
        self._deinited = False

    def _process(self, frames):
        raise NotImplementedError

    def deinit(self):
        self._deinited = True
        self._source = None

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        if self._source is not None:
            self._source._reset_buffer(single_channel_output, audio_channel)

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        import audiocore
        if self._source is None:
            return 0, memoryview(b"")
        result, data = audiocore.get_buffer(self._source,
                                            single_channel_output,
                                            audio_channel)
        raw = bytes(data)
        if not raw:
            return result, memoryview(raw)
        frames = np.frombuffer(raw, dtype="<i2").astype(np.float64)
        out = np.clip(np.rint(self._process(frames)), -32768, 32767)
        return result, memoryview(out.astype("<i2").tobytes())


class OneLsbScale(_Node):
    """WIRE's fault: the dry path scaled by 32767/32768 - one LSB.

    Under round-half-to-even `v * 32767 / 32768` returns `v` for every
    |v| <= 16384, so this is byte-identical to the clean render on any
    material peaking below -6.02 dBFS. That is the point: it must go red on
    `ramp_fs` and green on a quiet chord, which is the
    material-cannot-reach-the-mechanism shape planted inside the kit's own
    control.
    """

    def _process(self, frames):
        return frames * (32767.0 / 32768.0)


class HiddenGain(_Node):
    """LEVEL's fault: a hidden gain on the path, +0.1 dB by default,
    against a 0.05 dB bar."""

    def __init__(self, source, gain_db=0.1):
        _Node.__init__(self, source)
        self.gain_db = gain_db
        self._gain = 10.0 ** (gain_db / 20.0)

    def _process(self, frames):
        return frames * self._gain


class StuckDc(_Node):
    """TAIL's fault: +1 LSB of DC left in the node's state once it has seen
    signal - the real audioif#23 residue (LowPass 100 Hz reads +1 LSB,
    40 Hz/q=8 reads -4 LSB).

    A state that never returns to zero has no last non-zero sample, so this
    turns the tail-length readout red as well as the residual one. The
    control is a separate unfaulted run, never a second readout of this.
    """

    def __init__(self, source, residue_lsb=1):
        _Node.__init__(self, source)
        self.residue_lsb = int(residue_lsb)
        self._settled = False

    def _process(self, frames):
        if not self._settled and np.abs(frames).max() > 0:
            self._settled = True
        return frames + (self.residue_lsb if self._settled else 0)


class H2Inject(_Node):
    """SPECTRUM's fault: a second harmonic injected at a stated level.

    `y = x + k x^2` with k = 2 * 10^(h2_db/20) / amplitude puts h2 at
    `h2_db` re the fundamental of a sine of that amplitude, and nothing
    anywhere else: the harmonic readout goes red and the alias readout, whose
    mask excludes every harmonic, stays green.
    """

    def __init__(self, source, h2_db=-35.0, amplitude=0.5):
        _Node.__init__(self, source)
        self.h2_db = h2_db
        self._k = 2.0 * 10 ** (h2_db / 20.0) / (amplitude * 32768.0)

    def _process(self, frames):
        return frames + self._k * frames * frames


class TwoStageRelease(_core.Effect):
    """A compressor whose release has two stages: fast down to `switch_db`
    of remaining gain reduction, slow below it.

    This is GAINTRACE's subject and the kit's own reference class, because
    no shipped class has a two-stage release to perturb. `collapsed=True` is
    the planted fault - one stage at the fast constant - and it is meant to
    leave t63 where it was while moving t95, a fault that fires on part of
    the readout and not all of it.
    """

    NAME = 'TwoStageRelease'
    DISPLAY_NAME = 'Two Stage Release'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.0.1'
    MACRO_LABELS = ()
    MACRO_MODES = {}
    PATCHES = {0: ("Default", ())}

    def __init__(self, source, threshold_db=-24.0, ratio=4.0,
                 fast_ms=30.0, slow_ms=300.0, switch_db=4.5,
                 detector_ms=5.0, collapsed=False):
        self.node = _TwoStageNode(source, threshold_db, ratio, fast_ms,
                                  slow_ms, switch_db, detector_ms, collapsed)
        self._output = self.node


class _TwoStageNode(_Node):
    def __init__(self, source, threshold_db, ratio, fast_ms, slow_ms,
                 switch_db, detector_ms, collapsed):
        _Node.__init__(self, source)
        rate = float(source.sample_rate)
        self.threshold_db = threshold_db
        self.slope = 1.0 - 1.0 / ratio
        self.switch_db = switch_db
        self.collapsed = collapsed
        self._fast = math.exp(-1.0 / (fast_ms / 1000.0 * rate))
        self._slow = math.exp(-1.0 / (slow_ms / 1000.0 * rate))
        self._detector = math.exp(-1.0 / (detector_ms / 1000.0 * rate))
        self._level = 0.0
        self._gr = 0.0

    def _process(self, frames):
        channels = self.channel_count
        block = frames.reshape(-1, channels)
        out = np.empty_like(block)
        for index in range(block.shape[0]):
            magnitude = float(np.abs(block[index]).max()) / 32768.0
            self._level = max(magnitude, self._level * self._detector)
            level_db = 20.0 * math.log10(max(self._level, 1e-9))
            over = level_db - self.threshold_db
            target = over * self.slope if over > 0 else 0.0
            if target >= self._gr:
                self._gr = target                      # instant attack
            else:
                coefficient = (self._fast if self.collapsed
                               or self._gr > self.switch_db else self._slow)
                self._gr = target + (self._gr - target) * coefficient
            out[index] = block[index] * 10.0 ** (-self._gr / 20.0)
        return out.reshape(-1)


def under_reporting_limiter(samples):
    """CLICK's fault, and its control: a Limiter that declares its lookahead
    latency, and one that declares 256 samples less of it.

    The DSP is untouched in both - the two renders must be byte-identical -
    so a latency check that only fires when the sound also changes stays
    silent here, which is precisely what CLICK is for.

    `Limiter`'s latency is a macro, so the rebuilt class reports it from a
    property rather than from `LATENCY_SAMPLES`; overriding the class
    attribute alone would leave the fault inert, which is a fault that cannot
    fail. Both are overridden here.
    """
    def reported(self):
        self._check_live()
        return int(samples)

    return type("LimiterReporting%d" % samples, (audioeffects.Limiter,),
                {"LATENCY_SAMPLES": int(samples),
                 "latency_samples": property(reported)})


class NoResetDelay(audioeffects.DigitalDelay):
    """STATE's first fault: a delay line left full after `reset()`.

    The base class resets the node's buffer; this one keeps everything else
    and skips exactly that, which is the shape the vision names.
    """

    def reset(self):
        self._check_live()
        self.program_change(0)


class LiveIntermediateDelay(audioeffects.DigitalDelay):
    """STATE's second fault: an intermediate node left live after
    `deinit()`.

    `_core.Effect.deinit` deinitialises the chain tail. A class that builds a
    node *in front* of its tail has to deinitialise that one itself; this
    subclass builds one and does not.
    """

    def __init__(self, source, **options):
        self.pre = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.LOW_PASS, 8000.0,
                                  Q=0.707), **_core.pcm())
        self.pre.play(source)
        audioeffects.DigitalDelay.__init__(self, self.pre, **options)


class ShiftedCornerLowPass(audioeffects.LowPass):
    """RESPONSE's fault: one coefficient moved so the corner shifts 15 %.

    The class is asked for the same frequency as the control; the biquad it
    builds is 15 % away from it. The fitted corner must go red while the
    passband gain stays green.

    Every other keyword is passed through untouched - `sample_rate` and
    `transport` among them, which `create()` supplies - so this shifts the
    corner and changes nothing else about how the class is constructed.
    """

    SHIFT = 1.15

    def __init__(self, source, frequency=1000.0, **options):
        options["frequency"] = frequency * self.SHIFT
        audioeffects.LowPass.__init__(self, source, **options)


def corrupt_one_block(pcm, block_frames=256, channels=2):
    """DIGEST's fault: one sample +256 LSB and another in the same block
    -1 LSB.

    Computed rather than recalled: the +256 raises one sample's high byte by
    one and the -1 lowers another's low byte by one, so the unsigned-byte
    sum moves by **exactly zero** while FNV-1a must go red. The pair is
    chosen so neither byte carries or borrows, or the arithmetic would not
    hold.
    """
    data = bytearray(pcm)
    limit = min(len(data), block_frames * channels * 2)
    raised = lowered = None
    for offset in range(0, limit - 1, 2):
        low, high = data[offset], data[offset + 1]
        if raised is None and high != 0x7f and high != 0xff:
            data[offset + 1] = high + 1              # +256 LSB, no carry
            raised = offset
        elif lowered is None and low >= 1 and offset != raised:
            data[offset] = low - 1                   # -1 LSB, no borrow
            lowered = offset
        if raised is not None and lowered is not None:
            break
    if raised is None or lowered is None:
        raise ValueError("no pair in the first block can carry the +256/-1 "
                         "perturbation without a carry or a borrow")
    return bytes(data), raised, lowered
