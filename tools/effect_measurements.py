"""The measurement kit's first ten measurements, over rendered audio.

`docs/effects-kit-spec.md` section 5 specifies twenty measurements. This
module implements the first ten - the six Tier 1 invariants and the first
four Tier 2 circuit traits:

    WIRE  TAIL  LEVEL  CLICK  STATE  DIGEST
    RESPONSE  SPECTRUM  CURVE  GAINTRACE

Each is one function of the same name. Every one of them takes renders and
returns a dict carrying the numbers with their units, the four axes of
section 1 (rate, channel count, interpreter, source block size), the criteria
it was judged against, and `passed` - so a class gate can cite the number and
not only the verdict.

**The render is dual-runtime; the analysis is not** (spec section 1). Nothing
here runs on a board: it is CPython with numpy, reading WAVs written by the
renderer. Two of the ten - STATE, and GAINTRACE's level search - drive the
class itself rather than reading a finished render, because their subject is
the class's behaviour between renders; they take the effect and a render
callable respectively.

**Written against an interface, not against the renderer.**
`tools/render_effect.py` (spec section 4) did not exist when this file was
written. The contract assumed here is exactly what section 4 states:

    render_effect.py <Class> <probe> <outdir> [--rate 48000] [--channels 2]
                     [--block 256] [--macro n=v ...] [--patch n]
                     [--events events.json] [--transport tempo.json]

    - built through `create(source, sample_rate, **options)`
    - PCM streamed to a WAV, header excluded from the digest
    - FNV-1a over the PCM bytes returned, and the axes recorded beside it

so a render reaches a measurement here as `Render.from_wav(path, rate=...,
channels=..., block=..., interpreter=...)`, or as `Render.from_pcm(...)` for
an in-process render. When the renderer lands, it should hand back a `Render`
(or the metadata `Render.from_wav` wants); no measurement below needs
changing for that.

**No measurement reads a silent render** (spec section 1). `require_signal()`
is called by every one of the ten. The two whose subject is an absence carry
their own floor instead: TAIL requires signal in the burst and measures the
silence after it, and DIGEST's `distinct` mode requires each side to be
non-silent before it will call two renders different.

**What is not implemented here, so nothing cites it by mistake.**
RESPONSE carries the *stepped-tone* excitation only: the swept excitation and
the STFT-per-frame excitation that fourteen Tier 2 cells name (`Phaser` P1,
`Flanger` F2, `AirSpace` AS7 and the rest) are not built, and neither is the
ratio mode that divides one render by another of the same class. CLICK reads
one render at a time - the re-run with each latency-adding option turned on
alone is the driver's loop, not this function's. STATE reports `tempo_sync`
as unmeasured unless it is handed the two transport digests, because the
renderer's `--transport` is section 4's. SPECTRUM's alias readout and CURVE's
fitted law are here; their *second* planted faults (the oversampler turned
off, the clamped drive control) are not in the battery. Measurements 11-20 -
ENVELOPE, IFREQ, TAPS, DECAY, STEREO, RESIDUAL, TRUEPEAK, NULL, COST,
ROUNDTRIP - are not in this file at all.

Reused rather than rebuilt (spec section 2):
`fnv1a` is `audioif/tests/parity/effects_component_probe.py:15` unchanged;
the tau -> T60 least-squares log-envelope fit and the WAV loader are
`tools/measure_hits.py`'s; the analysis primitives are the ones
`tests/test_cpython_effects_library.py` already had, rate-parameterised here
because that file's `spectrum()` hardcodes its bin width.
"""

import gc
import math
import wave

import numpy as np


# --------------------------------------------------------------------------
# The digest, and the silence rule
# --------------------------------------------------------------------------

def fnv1a(data):
    """FNV-1a over the bytes.

    `audioif/tests/parity/effects_component_probe.py:15`, unchanged and for
    the reason stated there: `sum(data)` is a sum over UNSIGNED BYTES, so it
    is invariant under any set of byte deltas that cancel - a +256 LSB error
    paid for by a single -1 LSB error moves it by exactly zero. DIGEST's
    planted fault is that exact pair.
    """
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def byte_sum(data):
    """The blind statistic, printed alongside so older per-architecture
    records stay comparable. Never the comparison."""
    return int(sum(data))


class SilentRenderError(AssertionError):
    """A measurement was handed a render whose digest is the digest of
    silence. Absence reading as agreement is this workspace's signature
    failure; every measurement refuses it rather than reporting a number."""


def silence_digest(byte_length):
    return fnv1a(b"\x00" * byte_length)


def require_signal(render, what="render"):
    """Spec section 1's rule, enforced. Raises rather than returning a
    verdict: a silent render is not a red measurement, it is a measurement
    that did not happen."""
    if render.is_silent:
        raise SilentRenderError(
            "%s %s is silence (%d frames, FNV %08x) - the measurement was "
            "not taken" % (what, render.label or "", render.frames,
                           render.digest))
    return render


# --------------------------------------------------------------------------
# What a render is
# --------------------------------------------------------------------------

class Render:
    """One rendered WAV plus the axes it was rendered on.

    `data` is (frames, channels) int16 - the PCM as written, not a float
    convenience copy, because WIRE and DIGEST are byte comparisons and a
    float round trip is exactly the kind of near-enough that hides an LSB.
    `.float` is derived when a measurement wants it.
    """

    def __init__(self, pcm, rate, channels, *, block=None, interpreter=None,
                 label=None, probe=None, class_name=None,
                 class_version=None, latency_samples=None, path=None):
        self.pcm = bytes(pcm)
        self.rate = int(rate)
        self.channels = int(channels)
        self.block = block
        self.interpreter = interpreter
        self.label = label
        self.probe = probe
        self.class_name = class_name
        self.class_version = class_version
        self.latency_samples = latency_samples
        self.path = path
        width = 2 * self.channels
        usable = len(self.pcm) - len(self.pcm) % width
        self.data = np.frombuffer(self.pcm[:usable],
                                  dtype="<i2").reshape(-1, self.channels)
        self.frames = self.data.shape[0]
        self.digest = fnv1a(self.pcm)
        self.byte_sum = byte_sum(self.pcm)

    @classmethod
    def from_wav(cls, path, **axes):
        """Load a WAV the renderer wrote. Rate and channel count come from
        the file; the other axes are the caller's to state, because a file
        cannot report the source block size it was pulled at."""
        with wave.open(str(path), "rb") as handle:
            if handle.getsampwidth() != 2:
                raise ValueError("the kit's renders are 16-bit PCM; %s is "
                                 "%d-bit" % (path, handle.getsampwidth() * 8))
            rate = handle.getframerate()
            channels = handle.getnchannels()
            pcm = handle.readframes(handle.getnframes())
        axes.setdefault("rate", rate)
        axes.setdefault("channels", channels)
        axes["path"] = str(path)
        return cls(pcm, axes.pop("rate"), axes.pop("channels"), **axes)

    @classmethod
    def from_pcm(cls, pcm, rate, channels, **axes):
        return cls(pcm, rate, channels, **axes)

    @property
    def is_silent(self):
        return not self.pcm or not self.data.any()

    @property
    def float(self):
        return self.data.astype(np.float64) / 32768.0

    def seconds(self):
        return self.frames / float(self.rate)

    def axes(self):
        return {"rate_hz": self.rate, "channel_count": self.channels,
                "block_frames": self.block, "interpreter": self.interpreter,
                "probe": self.probe, "class": self.class_name,
                "class_version": self.class_version,
                "render_fnv1a": "%08x" % self.digest}

    def __repr__(self):
        return ("Render(%s, %d frames, %d Hz, %d ch, block=%s, fnv=%08x)"
                % (self.label or self.probe or "-", self.frames, self.rate,
                   self.channels, self.block, self.digest))


def _result(name, unit, values, axes, criteria, red):
    return {"measurement": name, "unit": unit, "values": values,
            "axes": axes, "criteria": criteria, "red": list(red),
            "passed": not red}


# --------------------------------------------------------------------------
# Primitives (the ones test_cpython_effects_library.py already had,
# rate-parameterised, plus measure_hits.py's envelope and tau fit)
# --------------------------------------------------------------------------

def rms(x):
    x = np.asarray(x, dtype=np.float64)
    return float(np.sqrt((x * x).mean())) if x.size else 0.0


def db(value, floor=1e-12):
    return 20.0 * math.log10(max(float(value), floor))


def rms_db(x):
    return db(rms(x))


def peak_db(x):
    x = np.asarray(x, dtype=np.float64)
    return db(float(np.abs(x).max())) if x.size else -240.0


def envelope(x, rate, hop_ms=1.0):
    """RMS envelope at a stated hop. `tools/measure_hits.py:envelope`'s
    method, with the window stated in ms so it is comparable across rates."""
    x = np.asarray(x, dtype=np.float64)
    win = max(1, int(round(rate * hop_ms / 1000.0)))
    pad = (-len(x)) % win
    if pad:
        x = np.concatenate([x, np.zeros(pad)])
    seg = x.reshape(-1, win)
    return np.sqrt((seg ** 2).mean(axis=1)), win


def tau_t60(env, rate, win, start=0, floor_db=-50.0):
    """Least-squares fit of the log envelope -> tau (seconds to 1/e) and the
    extrapolated T60. `tools/measure_hits.py:measure`'s estimator."""
    tail = np.asarray(env[start:], dtype=np.float64)
    if tail.size < 3 or tail[0] <= 0:
        return None, None
    below = np.nonzero(tail <= tail[0] * 10 ** (floor_db / 20.0))[0]
    stop = int(below[0]) if below.size else len(tail)
    seg = tail[:max(stop, 3)]
    t = np.arange(len(seg)) * win / float(rate)
    slope = np.polyfit(t, np.log(np.maximum(seg, 1e-12)), 1)[0]
    if slope >= 0:
        return None, None
    tau = float(-1.0 / slope)
    return tau, float(tau * math.log(1000.0))


def tone_bin(x, rate, hz):
    """Complex amplitude of `hz` in `x` by a single-bin DFT over a whole
    number of periods - no window, no leakage, and no dependence on the FFT
    length landing the tone on a bin."""
    x = np.asarray(x, dtype=np.float64)
    period = rate / float(hz)
    periods = int(len(x) / period)
    if periods < 1:
        return 0.0 + 0.0j
    n = int(round(periods * period))
    n = min(n, len(x))
    seg = x[:n]
    k = np.arange(n)
    twiddle = np.exp(-2j * math.pi * hz * k / rate)
    return complex(2.0 * np.dot(seg, twiddle) / n)


def magnitude_spectrum(x, rate, size=None, window=None):
    """Magnitude spectrum and bin width, with the transform length and the
    window as stated parameters. The bin width is derived from the rate that
    is passed in - `test_cpython_effects_library.spectrum` hardcoded
    SAMPLE_RATE / size, which is wrong the moment a measurement takes its
    rate as an argument."""
    x = np.asarray(x, dtype=np.float64)
    if size is None:
        size = 1
        while size * 2 <= len(x):
            size *= 2
    seg = np.zeros(size)
    take = min(size, len(x))
    seg[:take] = x[:take]
    name = "rectangular"
    if window == "hann":
        seg = seg * np.hanning(size)
        name = "hann"
    elif window == "blackmanharris":
        k = np.arange(size)
        seg = seg * (0.35875 - 0.48829 * np.cos(2 * math.pi * k / size)
                     + 0.14128 * np.cos(4 * math.pi * k / size)
                     - 0.01168 * np.cos(6 * math.pi * k / size))
        name = "blackman-harris"
    spec = np.abs(np.fft.rfft(seg))
    return spec, rate / float(size), name, size



def exact_bin_size(frames, rate, hz):
    """Transform length that lands `hz` on (as close as arithmetic allows
    to) an exact bin, so no window is needed.

    A power-of-two length is the wrong default here and was the first thing
    this measurement got wrong in testing: at 48 kHz a 16384-point rectangular
    transform puts a 1 kHz tone at bin 341.33, and the leakage skirt of that
    third of a bin reads -55 dB at the second harmonic - a wire's THD
    reported as a class's. Choosing a whole number of periods instead drops
    the same reading below -90 dB.
    """
    period = rate / float(hz)
    periods = int(frames / period)
    if periods < 1:
        return None
    size = int(round(periods * period))
    return max(64, min(size, frames))


def onset(x, *, threshold_ratio=1e-3, floor_lsb=2.0):
    """First sample of arrival, and a sub-sample refinement of it.

    The integer read is the first sample above a floor stated two ways -
    a fraction of this render's own peak, and an absolute LSB floor so a
    render whose peak is one LSB does not report an onset in its dither.
    The refinement is a parabola through the energy envelope either side of
    the first local energy maximum after that sample, which is what a
    fractional delay needs and an integer delay leaves untouched.
    """
    x = np.asarray(x, dtype=np.float64)
    if not x.size:
        return None, None
    peak = float(np.abs(x).max())
    if peak <= 0:
        return None, None
    level = max(peak * threshold_ratio, floor_lsb / 32768.0)
    above = np.nonzero(np.abs(x) >= level)[0]
    if not above.size:
        return None, None
    first = int(above[0])
    energy = x * x
    k = first
    while k + 1 < len(energy) and energy[k + 1] > energy[k]:
        k += 1
    if 0 < k < len(energy) - 1:
        a, b, c = energy[k - 1], energy[k], energy[k + 1]
        denominator = a - 2.0 * b + c
        delta = 0.5 * (a - c) / denominator if denominator else 0.0
    else:
        delta = 0.0
    return first, float(k + delta)


def enumerate_nodes(effect):
    """Every audio node the class hung off itself, by name.

    A node is an attribute implementing the audiocore sample protocol - the
    same duck type `audiocore.get_buffer` accepts - reached directly or
    through a list or tuple attribute. The class's source is excluded: it is
    the caller's node, not the class's, and deinitialising it is not this
    class's job.
    """
    found = []
    source = getattr(effect, "_source", None)
    output = getattr(effect, "_output", None)

    def looks_like_a_node(value):
        return (hasattr(value, "_get_buffer") and value is not source)

    for name, value in vars(effect).items():
        if name.startswith("_"):
            continue
        if looks_like_a_node(value):
            found.append((name, value))
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                if looks_like_a_node(item):
                    found.append(("%s[%d]" % (name, index), item))
                inner = getattr(item, "_output", None)
                if inner is not None and looks_like_a_node(inner):
                    found.append(("%s[%d]._output" % (name, index), inner))
    if output is not None and looks_like_a_node(output):
        if not any(node is output for _, node in found):
            found.append(("_output", output))
    return found


def _is_deinited(node):
    if getattr(node, "_deinited", False):
        return True
    try:
        namespace = object.__getattribute__(node, "__dict__")
    except AttributeError:
        return False
    return bool(namespace.get("_deinited", False))


# --------------------------------------------------------------------------
# Tier 1 - the invariants
# --------------------------------------------------------------------------

def wire(render, source, *, latency_samples=0, tolerance_samples=0):
    """WIRE - the bypass invariant (spec section 5).

    Byte compare of the render against the source, both channels, with the
    source delayed by the class's reported `latency_samples`: a class
    carrying a convolver partition or a lookahead is not a wire at sample
    zero, and a wrong report is CLICK's to catch, not WIRE's to absorb.

    Exports the differing sample count and the first differing offset. It is
    a byte compare and not an RMS or a dB check on purpose - the planted
    fault is one LSB on the dry path, which no summarising statistic sees.
    """
    require_signal(render, "wire render")
    require_signal(source, "wire source")
    if render.channels != source.channels:
        raise ValueError("WIRE compares like with like: %d channels against "
                         "%d" % (render.channels, source.channels))
    delay = int(latency_samples)
    count = min(render.frames - delay, source.frames)
    if count <= 0:
        raise ValueError("WIRE has nothing to compare: %d render frames, "
                         "%d source frames, %d samples of reported latency"
                         % (render.frames, source.frames, delay))
    left = render.data[delay:delay + count].astype(np.int32)
    right = source.data[:count].astype(np.int32)
    difference = left - right
    differing = int(np.count_nonzero(difference))
    where = np.nonzero(difference)
    first_frame = int(where[0][0]) if differing else None
    first_channel = int(where[1][0]) if differing else None
    values = {
        "compared_samples": int(count * render.channels),
        "compared_frames": int(count),
        "differing_samples": differing,
        "first_difference_frame": first_frame,
        "first_difference_channel": first_channel,
        "max_abs_difference_lsb": int(np.abs(difference).max()),
        "reported_latency_samples": delay,
        "render_fnv1a": "%08x" % render.digest,
        "source_fnv1a": "%08x" % source.digest,
    }
    criteria = {"differing_samples_max": int(tolerance_samples)}
    red = []
    if differing > tolerance_samples:
        red.append("%d of %d samples differ, first at frame %d channel %d "
                   "(max %d LSB)" % (differing, values["compared_samples"],
                                     first_frame, first_channel,
                                     values["max_abs_difference_lsb"]))
    return _result("WIRE", "samples", values, render.axes(), criteria, red)


def tail(burst_render, *, burst_end_frame, declared_tail_samples=None,
         residual_tolerance_lsb=0, settle_frames=None, dc_render=None,
         dc_removed_frame=None, dc_settle_frames=None):
    """TAIL - silence in, silence out; decay to *exact* zero; the held-DC
    class of defect (audioif#23).

    This is one of the two measurements whose subject is an absence, so it
    does not call `require_signal` on the whole render: it requires signal
    in the burst and measures the silence after it. A render that is silent
    from the first sample has no tail to measure and is refused.

    Exports the tail length in samples and the residual in LSB. A state that
    never returns to zero has no last non-zero sample, so both readouts go
    red together on the planted fault - which is why the control is a
    separate unfaulted run and never a second readout of this one.
    """
    end = int(burst_end_frame)
    burst = burst_render.data[:end]
    if not burst.any():
        raise SilentRenderError(
            "TAIL's burst region (0..%d) is silent - there is no tail to "
            "measure" % end)
    after = burst_render.data[end:]
    non_zero = np.nonzero(after.any(axis=1))[0]
    last = int(non_zero[-1]) if non_zero.size else None
    tail_samples = None if last is None else last + 1
    window = int(settle_frames or max(1, after.shape[0] // 10))
    settle = after[-window:] if after.shape[0] else after
    residual_lsb = int(np.abs(settle).max()) if settle.size else 0
    returns_to_zero = residual_lsb == 0
    values = {
        "tail_samples": tail_samples,
        "tail_ms": (None if tail_samples is None
                    else 1000.0 * tail_samples / burst_render.rate),
        "residual_lsb": residual_lsb,
        "settle_window_frames": window,
        "returns_to_zero": returns_to_zero,
        "declared_tail_samples": declared_tail_samples,
    }
    criteria = {"residual_lsb_max": int(residual_tolerance_lsb),
                "declared_tail_samples": declared_tail_samples}
    red = []
    if residual_lsb > residual_tolerance_lsb:
        red.append("residual %d LSB in the last %d frames (bar %d LSB)"
                   % (residual_lsb, window, residual_tolerance_lsb))
    if not returns_to_zero:
        red.append("the state never returns to zero: no last non-zero "
                   "sample, so there is no tail length to report")
    elif (declared_tail_samples is not None
            and tail_samples is not None
            and tail_samples > declared_tail_samples):
        red.append("tail %d samples exceeds the declared %d"
                   % (tail_samples, declared_tail_samples))

    if dc_render is not None:
        if dc_removed_frame is None:
            raise ValueError("the dc_step leg needs dc_removed_frame")
        removed = int(dc_removed_frame)
        span = int(dc_settle_frames or max(1, removed // 10))
        supplied = dc_render.data[max(0, removed - span):removed]
        settled = dc_render.data[-span:]
        while_supplied = float(supplied.mean()) if supplied.size else 0.0
        after_removed = float(settled.mean()) if settled.size else 0.0
        values["dc_while_supplied_lsb"] = while_supplied
        values["dc_after_removed_lsb"] = after_removed
        values["dc_residual_lsb"] = int(np.abs(settled).max()) \
            if settled.size else 0
        if values["dc_residual_lsb"] > residual_tolerance_lsb:
            red.append("dc_step leaves %d LSB after the offset is removed "
                       "(bar %d LSB)" % (values["dc_residual_lsb"],
                                         residual_tolerance_lsb))
    return _result("TAIL", "samples, LSB", values, burst_render.axes(),
                   criteria, red)


def level(wet_render, dry_render, *, tolerance_db=0.05, skip_frames=0):
    """LEVEL - level honesty: unity through the path, no hidden gain.

    Wet:dry RMS and peak ratio per channel. At mix 0 this is strictly weaker
    than WIRE, which catches a one-LSB change where this bar is 0.05 dB; the
    mix-0 leg is kept as the readable number beside WIRE's offset, and the
    measurement's subject is the wet path at the class's unity setting.
    """
    require_signal(wet_render, "level wet render")
    require_signal(dry_render, "level dry render")
    count = min(wet_render.frames, dry_render.frames) - int(skip_frames)
    if count <= 0:
        raise ValueError("LEVEL has nothing to compare after %d skipped "
                         "frames" % skip_frames)
    wet = wet_render.float[skip_frames:skip_frames + count]
    dry = dry_render.float[skip_frames:skip_frames + count]
    rms_ratio, peak_ratio = [], []
    for channel in range(wet_render.channels):
        rms_ratio.append(rms_db(wet[:, channel]) - rms_db(dry[:, channel]))
        peak_ratio.append(peak_db(wet[:, channel]) - peak_db(dry[:, channel]))
    values = {"rms_db": [round(v, 4) for v in rms_ratio],
              "peak_db": [round(v, 4) for v in peak_ratio],
              "compared_frames": int(count)}
    criteria = {"abs_rms_db_max": float(tolerance_db)}
    red = []
    for channel, value in enumerate(rms_ratio):
        if abs(value) > tolerance_db:
            red.append("channel %d wet:dry RMS %+.3f dB (bar %.3f dB)"
                       % (channel, value, tolerance_db))
    return _result("LEVEL", "dB", values, wet_render.axes(), criteria, red)


def click(render, dry_render, reported_latency_samples, *,
          tolerance_samples=1.0, threshold_ratio=1e-3, subsample=True):
    """CLICK - reported `latency_samples` against measured (vision section
    9a), per channel, at whatever rate the render was taken at.

    Onset of the class's output against the onset of its dry path, to the
    sample, sub-sampled by parabolic interpolation on the energy envelope
    where a fractional delay exists. The audio digest is exported beside the
    number, because the planted fault leaves the DSP alone: a latency check
    that only fires when the sound also changes is not a latency check.

    **`subsample=False` reads the integer onset only, and the difference
    between the two readings is not cosmetic.** Measured here rather than
    assumed: the committed `click_stereo` probe through `LowPass` at 8 kHz
    reads 0 samples integer and +1.333 samples sub-sample, because a
    minimum-phase filter has group delay - which is a real property of the
    class and *not* the processing latency `latency_samples` declares. A
    class whose latency is a pure delay (a lookahead, a convolver partition)
    reads the same both ways. Say which reading a row wants; the default is
    the sub-sample one because a fractional delay is invisible without it.
    """
    require_signal(render, "click render")
    require_signal(dry_render, "click dry render")
    measured, per_channel = [], []
    for channel in range(render.channels):
        wet_first, wet_fine = onset(render.float[:, channel],
                                    threshold_ratio=threshold_ratio)
        dry_first, dry_fine = onset(dry_render.float[:, channel],
                                    threshold_ratio=threshold_ratio)
        if wet_fine is None or dry_fine is None:
            raise SilentRenderError("CLICK found no onset in channel %d"
                                    % channel)
        value = ((wet_fine - dry_fine) if subsample
                 else float(wet_first - dry_first))
        measured.append(value)
        per_channel.append({
            "channel": channel,
            "wet_onset_sample": wet_first,
            "dry_onset_sample": dry_first,
            "latency_samples": round(value, 3),
            "latency_ms": round(1000.0 * value / render.rate, 4),
        })
    worst = max(abs(v - reported_latency_samples) for v in measured)
    values = {
        "per_channel": per_channel,
        "subsample": bool(subsample),
        "measured_latency_samples": [round(v, 3) for v in measured],
        "measured_latency_ms": [round(1000.0 * v / render.rate, 4)
                                for v in measured],
        "reported_latency_samples": int(reported_latency_samples),
        "error_samples": round(worst, 3),
        "render_fnv1a": "%08x" % render.digest,
    }
    criteria = {"abs_error_samples_max": float(tolerance_samples)}
    red = []
    if worst > tolerance_samples:
        red.append("measured %s samples against a reported %d (%.1f samples "
                   "out, bar %.1f) at %d Hz"
                   % (values["measured_latency_samples"],
                      reported_latency_samples, worst, tolerance_samples,
                      render.rate))
    return _result("CLICK", "samples", values, render.axes(), criteria, red)


def state(effect, *, pull, swap, probe_source, silent_source, blocks=64,
          alloc_pulls=200, alloc_tolerance_bytes=8192,
          reset_tolerance_lsb=0, transport_digests=None, nodes=None):
    """STATE - `reset()`, `deinit()`, `capabilities`, and the no-allocation
    rule.

    This one drives the class rather than reading a finished render, and it
    reads in the order the spec's refutation pass settled:

      1. render the probe (and refuse a silent one);
      2. `reset()`;
      3. swap the borrowed source for a silent one and pull - the output
         must be exactly zero. (Asking for both at once - reset and a source
         that still has audio in it - is red on a correct build, and gets
         loosened by the first person to run it.)
      4. hand the original source back: it must render again;
      5. allocation flat across `alloc_pulls` pulls, on a render whose
         digest is not the digest of silence - a class that allocates
         nothing because nothing was pulled is flat too;
      6. `capabilities` declares "tempo_sync" iff a transport read changes
         the render (pass the two digests, or it is reported unmeasured);
      7. `deinit()`, then every node the class enumerated is deinitialised.

    `pull(blocks)` renders that many blocks and returns a Render;
    `swap(source)` puts a different source under the class.
    """
    values = {}
    red = []

    first = pull(blocks)
    require_signal(first, "state probe render")
    values["probe_fnv1a"] = "%08x" % first.digest

    effect.reset()
    swap(silent_source)
    after_reset = pull(blocks)
    residual = int(np.abs(after_reset.data).max()) if after_reset.frames else 0
    values["reset_residual_lsb"] = residual
    values["reset_residual_fnv1a"] = "%08x" % after_reset.digest
    if residual > reset_tolerance_lsb:
        red.append("after reset() and a silent source the output still "
                   "reaches %d LSB (bar %d)" % (residual,
                                                reset_tolerance_lsb))

    swap(probe_source)
    resumed = pull(blocks)
    values["resumed"] = not resumed.is_silent
    values["resumed_fnv1a"] = "%08x" % resumed.digest
    if resumed.is_silent:
        red.append("the class does not render again once the original "
                   "source is handed back")

    # The probe is handed back a second time so the allocation leg runs on
    # audio and not on the far end of a probe the reads above consumed: a
    # class that allocates nothing because nothing was pulled is flat too.
    swap(probe_source)
    gc.collect()
    import tracemalloc
    tracing = tracemalloc.is_tracing()
    if not tracing:
        tracemalloc.start()
    warm = pull(2)
    del warm
    gc.collect()
    before = tracemalloc.get_traced_memory()[0]
    heard = False
    last_digest = None
    for _ in range(int(alloc_pulls)):
        # One block at a time, and dropped: holding every render would
        # measure this loop's own buffers rather than the class's state.
        chunk = pull(1)
        heard = heard or not chunk.is_silent
        last_digest = chunk.digest
        del chunk
    gc.collect()
    after = tracemalloc.get_traced_memory()[0]
    if not tracing:
        tracemalloc.stop()
    growth = int(after - before)
    values["alloc_growth_bytes"] = growth
    values["alloc_pulls"] = int(alloc_pulls)
    values["alloc_last_fnv1a"] = None if last_digest is None \
        else "%08x" % last_digest
    if not heard:
        red.append("the allocation reading was taken on silence, which is "
                   "flat because nothing was pulled")
    elif growth > alloc_tolerance_bytes:
        red.append("%d bytes retained across %d single-block pulls (bar %d)"
                   % (growth, alloc_pulls, alloc_tolerance_bytes))

    declared = tuple(effect.capabilities)
    values["capabilities"] = list(declared)
    if transport_digests is None:
        values["tempo_sync_observed"] = None
    else:
        with_transport, without_transport = transport_digests
        observed = with_transport != without_transport
        values["tempo_sync_observed"] = observed
        if observed != ("tempo_sync" in declared):
            red.append("capabilities %s against a transport read that %s "
                       "the render" % (list(declared),
                                       "changes" if observed
                                       else "does not change"))

    found = enumerate_nodes(effect) if nodes is None else list(nodes)
    values["nodes"] = [name for name, _ in found]
    effect.deinit()
    live = [name for name, node in found if not _is_deinited(node)]
    values["live_nodes_after_deinit"] = live
    if live:
        red.append("deinit() left %s live" % (live,))

    criteria = {"reset_residual_lsb_max": int(reset_tolerance_lsb),
                "alloc_growth_bytes_max": int(alloc_tolerance_bytes),
                "live_nodes_after_deinit_max": 0}
    return _result("STATE", "LSB, bytes, nodes", values, first.axes(),
                   criteria, red)


def digest(renders, *, mode="identical", ordering=None):
    """DIGEST - FNV-1a over the PCM bytes, in the spec's three comparison
    modes.

      "identical" - cross-interpreter, cross-board, and the source
                    block-size ladder: every render must be byte-identical.
      "distinct"  - the paired build, where two renders must differ, and
                    where the comparison fails on an ordering rather than a
                    magnitude: pass `ordering` as [(label, value), ...] that
                    must be strictly increasing, and it is exported.

    `sum(data)` is printed alongside so older per-architecture records stay
    comparable. It is never the comparison: the planted fault moves it by
    exactly zero.
    """
    if len(renders) < 2:
        raise ValueError("DIGEST compares renders; %d given" % len(renders))
    values = {"renders": {}}
    for label, render in renders.items():
        require_signal(render, "digest render %s" % label)
        values["renders"][label] = {
            "fnv1a": "%08x" % render.digest,
            "byte_sum": render.byte_sum,
            "frames": render.frames,
            "rate_hz": render.rate,
            "channel_count": render.channels,
            "block_frames": render.block,
            "interpreter": render.interpreter,
        }
    labels = list(renders)
    red = []
    if mode == "identical":
        reference = renders[labels[0]]
        for label in labels[1:]:
            other = renders[label]
            if other.digest != reference.digest:
                offset = _first_difference(reference, other)
                red.append("%s and %s differ (FNV %08x against %08x), first "
                           "at PCM byte %s" % (labels[0], label,
                                               reference.digest,
                                               other.digest, offset))
    elif mode == "distinct":
        seen = {}
        for label in labels:
            key = renders[label].digest
            if key in seen:
                red.append("%s and %s are byte-identical (FNV %08x) where "
                           "the pair must differ" % (seen[key], label, key))
            seen[key] = label
    else:
        raise ValueError("DIGEST mode is 'identical' or 'distinct', not %r"
                         % (mode,))
    if ordering is not None:
        values["ordering"] = [list(pair) for pair in ordering]
        for (a_label, a), (b_label, b) in zip(ordering, ordering[1:]):
            if not a < b:
                red.append("the ordering the row names is broken: %s %s is "
                           "not below %s %s" % (a_label, a, b_label, b))
    criteria = {"mode": mode, "ordering_required": ordering is not None}
    axes = renders[labels[0]].axes()
    return _result("DIGEST", "FNV-1a", values, axes, criteria, red)


def _first_difference(one, other):
    limit = min(len(one.pcm), len(other.pcm))
    a = np.frombuffer(one.pcm[:limit], dtype=np.uint8)
    b = np.frombuffer(other.pcm[:limit], dtype=np.uint8)
    where = np.nonzero(a != b)[0]
    if where.size:
        return int(where[0])
    return "%d (length: %d against %d bytes)" % (limit, len(one.pcm),
                                                 len(other.pcm))


# --------------------------------------------------------------------------
# Tier 2 - the circuit traits
# --------------------------------------------------------------------------

def response(wet_by_hz, dry_by_hz, *, excitation="tones_step",
             reference_hz=None, corner_db=-3.0, settled_ratio=0.5,
             slope_octave=None, expected=None):
    """RESPONSE - magnitude, phase and group delay against frequency.

    `wet_by_hz` and `dry_by_hz` are {frequency: Render}: one steady tone at a
    time, which is the excitation the spec's selection rule names wherever
    the class holds a detector or a rotating source that a sweep would move
    while it measures. The magnitude at each point is read from a single-bin
    DFT over a whole number of periods of the settled portion, so a class's
    own harmonics do not land in its passband reading.

    Extractors on top of the curve: the interpolated `corner_db` crossing,
    the passband gain, a least-squares skirt slope over a named octave pair,
    and the local extrema.

    `excitation` is recorded, not chosen: this function reads a set of steady
    tones. The swept and STFT excitations the spec also names are not
    implemented, so a cell that needs one is not served by this function yet.
     `expected` is {"corner_hz": (value, tol_pct),
    "passband_db": (value, tol_db), "slope_db_per_octave": (value, tol)}.
    """
    frequencies = sorted(set(wet_by_hz) & set(dry_by_hz))
    if len(frequencies) < 3:
        raise ValueError("RESPONSE needs at least three tones; %d given"
                         % len(frequencies))
    points = []
    for hz in frequencies:
        wet, dry = wet_by_hz[hz], dry_by_hz[hz]
        require_signal(wet, "response wet render at %g Hz" % hz)
        require_signal(dry, "response dry render at %g Hz" % hz)
        start = int(wet.frames * settled_ratio)
        w = tone_bin(wet.float[start:, 0], wet.rate, hz)
        d = tone_bin(dry.float[start:, 0], dry.rate, hz)
        if abs(d) <= 0.0:
            raise SilentRenderError("RESPONSE's dry render at %g Hz has no "
                                    "tone in it" % hz)
        transfer = w / d
        points.append((float(hz), db(abs(transfer)),
                       math.degrees(math.atan2(transfer.imag,
                                               transfer.real))))
    grid_hz = [p[0] for p in points]
    grid_db = [p[1] for p in points]
    phases = np.unwrap(np.radians([p[2] for p in points]))
    group_delay_ms = []
    for index in range(len(points) - 1):
        d_omega = 2 * math.pi * (grid_hz[index + 1] - grid_hz[index])
        d_phase = phases[index + 1] - phases[index]
        group_delay_ms.append(round(-1000.0 * d_phase / d_omega, 4))

    if reference_hz is None:
        reference_hz = grid_hz[0]
    passband_db = _interpolate_log(grid_hz, grid_db, reference_hz)
    corner_hz = _crossing(grid_hz, grid_db, passband_db + corner_db)
    slope = None
    if slope_octave:
        low, high = slope_octave
        selected = [(math.log2(f), g) for f, g in zip(grid_hz, grid_db)
                    if low <= f <= high]
        if len(selected) >= 2:
            xs = np.array([s[0] for s in selected])
            ys = np.array([s[1] for s in selected])
            slope = float(np.polyfit(xs, ys, 1)[0])

    values = {
        "excitation": excitation,
        "grid": [{"hz": round(f, 4), "magnitude_db": round(g, 4),
                  "phase_deg": round(p, 3)} for f, g, p in points],
        "group_delay_ms": group_delay_ms,
        "passband_db": round(passband_db, 4),
        "reference_hz": reference_hz,
        "corner_hz": None if corner_hz is None else round(corner_hz, 3),
        "corner_db": corner_db,
        "slope_db_per_octave": None if slope is None else round(slope, 3),
        "extrema": _extrema(grid_hz, grid_db),
    }
    criteria = dict(expected or {})
    red = []
    if expected:
        if "corner_hz" in expected:
            want, tol_pct = expected["corner_hz"]
            if corner_hz is None:
                red.append("no %.1f dB crossing on the measured grid"
                           % corner_db)
            elif abs(corner_hz - want) / want * 100.0 > tol_pct:
                red.append("corner %.1f Hz against an expected %.1f Hz "
                           "(%.1f %% out, bar %.1f %%)"
                           % (corner_hz, want,
                              abs(corner_hz - want) / want * 100.0, tol_pct))
        if "passband_db" in expected:
            want, tol = expected["passband_db"]
            if abs(passband_db - want) > tol:
                red.append("passband %.3f dB at %g Hz against an expected "
                           "%.3f dB (bar %.3f dB)"
                           % (passband_db, reference_hz, want, tol))
        if "slope_db_per_octave" in expected and slope is not None:
            want, tol = expected["slope_db_per_octave"]
            if abs(slope - want) > tol:
                red.append("skirt %.2f dB/octave against an expected %.2f "
                           "(bar %.2f)" % (slope, want, tol))
    axes = wet_by_hz[frequencies[0]].axes()
    return _result("RESPONSE", "dB, degrees, Hz", values, axes, criteria, red)


def _interpolate_log(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for index in range(len(xs) - 1):
        if xs[index] <= x <= xs[index + 1]:
            span = math.log(xs[index + 1] / xs[index])
            weight = math.log(x / xs[index]) / span if span else 0.0
            return ys[index] + weight * (ys[index + 1] - ys[index])
    return ys[-1]


def _crossing(xs, ys, target):
    """Lowest frequency where the curve crosses `target`, interpolated on a
    log frequency axis."""
    for index in range(len(xs) - 1):
        a, b = ys[index], ys[index + 1]
        if (a - target) * (b - target) <= 0 and a != b:
            weight = (target - a) / (b - a)
            return math.exp(math.log(xs[index])
                            + weight * math.log(xs[index + 1] / xs[index]))
    return None


def _extrema(xs, ys):
    out = []
    for index in range(1, len(xs) - 1):
        if ys[index] > ys[index - 1] and ys[index] > ys[index + 1]:
            out.append({"hz": xs[index], "db": round(ys[index], 3),
                        "kind": "maximum"})
        if ys[index] < ys[index - 1] and ys[index] < ys[index + 1]:
            out.append({"hz": xs[index], "db": round(ys[index], 3),
                        "kind": "minimum"})
    return out


def spectrum(render, fundamental_hz, *, harmonics=10, window=None,
             size=None, settled_ratio=0.5, modulator_hz=None,
             block_frames=None, bars=None, channel=0):
    """SPECTRUM - one FFT, four readouts.

      harmonic    h2..hN re fundamental, and THD over the same N;
      inharmonic  the alias floor: every bin more than two bins from a
                  harmonic and from DC, summed against the fundamental;
      sideband    ring modulation and FM lines, when `modulator_hz` is given;
      block-rate  lines at multiples of the source block rate, which is
                  section 1's fourth axis showing up in the audio - pass
                  `block_frames` to read them.

    The window, the transform length and the harmonic count N are exported
    with the numbers: a THD figure without its N is not comparable to the
    source it is checked against.
    """
    require_signal(render, "spectrum render")
    start = int(render.frames * settled_ratio)
    x = render.float[start:, channel]
    if size is None and window is None:
        size = exact_bin_size(len(x), render.rate, fundamental_hz)
    magnitudes, bin_hz, window_name, length = magnitude_spectrum(
        x, render.rate, size=size, window=window)
    nyquist = render.rate / 2.0

    def peak_near(hz, span_bins=2):
        centre = int(round(hz / bin_hz))
        low = max(0, centre - span_bins)
        high = min(len(magnitudes), centre + span_bins + 1)
        return float(magnitudes[low:high].max()) if high > low else 0.0

    base = peak_near(fundamental_hz)
    if base <= 0:
        raise SilentRenderError("SPECTRUM found no fundamental at %g Hz"
                                % fundamental_hz)
    orders = list(range(2, int(harmonics) + 1))
    harmonic_db = {}
    power = 0.0
    for order in orders:
        hz = fundamental_hz * order
        if hz >= nyquist:
            harmonic_db["h%d" % order] = None
            continue
        value = peak_near(hz)
        harmonic_db["h%d" % order] = round(db(value / base), 3)
        power += value ** 2
    thd_db = round(db(math.sqrt(power) / base), 3)

    mask = np.ones(len(magnitudes), dtype=bool)
    mask[:3] = False
    order = 1
    while fundamental_hz * order < nyquist:
        centre = int(round(fundamental_hz * order / bin_hz))
        mask[max(0, centre - 2):centre + 3] = False
        order += 1
    alias_power = float((magnitudes[mask] ** 2).sum())
    alias_db = round(db(math.sqrt(alias_power) / base), 3)

    sidebands = None
    if modulator_hz:
        sidebands = {}
        for index in (1, 2, 3):
            for sign, name in ((1, "upper"), (-1, "lower")):
                hz = fundamental_hz + sign * index * modulator_hz
                if 0 < hz < nyquist:
                    sidebands["%s%d" % (name, index)] = round(
                        db(peak_near(hz) / base), 3)

    block_lines = None
    if block_frames:
        block_rate = render.rate / float(block_frames)
        block_lines = {}
        for index in (1, 2, 3):
            for sign, name in ((1, "upper"), (-1, "lower")):
                hz = fundamental_hz + sign * index * block_rate
                if 0 < hz < nyquist:
                    block_lines["%s%d" % (name, index)] = round(
                        db(peak_near(hz) / base), 3)
        block_lines["block_rate_hz"] = round(block_rate, 4)

    values = {
        "fundamental_hz": fundamental_hz,
        "fundamental_dbfs": round(db(base), 3),
        "harmonic_db": harmonic_db,
        "thd_db": thd_db,
        "harmonic_count": int(harmonics),
        "alias_floor_db": alias_db,
        "sideband_db": sidebands,
        "block_rate_db": block_lines,
        "window": window_name,
        "transform_length": length,
        "bin_hz": round(bin_hz, 4),
    }
    criteria = dict(bars or {})
    red = []
    for name, bar in (bars or {}).items():
        if name.startswith("h") and name[1:].isdigit():
            measured = harmonic_db.get(name)
            if measured is not None and measured > bar:
                red.append("%s at %.1f dB re fundamental, above its %.1f dB "
                           "bar" % (name, measured, bar))
        elif name == "thd_db" and thd_db > bar:
            red.append("THD (h2..h%d) at %.1f dB, above its %.1f dB bar"
                       % (harmonics, thd_db, bar))
        elif name == "alias_floor_db" and alias_db > bar:
            red.append("alias floor at %.1f dB, above its %.1f dB bar"
                       % (alias_db, bar))
    return _result("SPECTRUM", "dB re fundamental", values, render.axes(),
                   criteria, red)


def curve(wet_by_level_db, dry_by_level_db=None, *, detector="rms",
          settled_ratio=0.5, channel=0, knee_grid=None, expected=None):
    """CURVE - the static level-in/level-out law.

    `wet_by_level_db` is {input level dBFS: Render}. The reading per step is
    taken over the settled portion, and the curve is fitted to the standard
    soft-knee law

        out = in + makeup - (1 - 1/ratio) * f(in; threshold, knee)

    where f is zero below the knee, quadratic through it and linear above.
    For a fixed (threshold, knee) that is linear in (makeup, 1 - 1/ratio), so
    the fit is a grid over the two shape parameters with a least-squares
    solve inside it, and the residual is exported beside every fitted number:
    a knee point that moves by less than its own residual is not a finding.
    """
    levels = sorted(wet_by_level_db)
    if len(levels) < 4:
        raise ValueError("CURVE needs at least four steps; %d given"
                         % len(levels))
    points = []
    for level_db in levels:
        render = wet_by_level_db[level_db]
        require_signal(render, "curve render at %g dBFS" % level_db)
        start = int(render.frames * settled_ratio)
        x = render.float[start:, channel]
        out_db = peak_db(x) if detector == "peak" else rms_db(x)
        if dry_by_level_db is not None:
            dry = dry_by_level_db[level_db]
            dry_x = dry.float[int(dry.frames * settled_ratio):, channel]
            in_db = peak_db(dry_x) if detector == "peak" else rms_db(dry_x)
        else:
            in_db = float(level_db)
        points.append((in_db, out_db))
    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])

    best = None
    thresholds = np.arange(xs.min(), xs.max() + 0.25, 0.25)
    knees = np.arange(0.0, 30.5, 0.5) if knee_grid is None \
        else np.asarray(knee_grid, dtype=np.float64)
    for threshold in thresholds:
        for knee in knees:
            f = _knee_shape(xs, threshold, knee)
            design = np.stack([np.ones_like(xs), -f], axis=1)
            solution, *_ = np.linalg.lstsq(design, ys - xs, rcond=None)
            makeup, c = float(solution[0]), float(solution[1])
            residual = float(np.sqrt(((design @ solution) - (ys - xs)) ** 2
                                     ).mean())
            if best is None or residual < best[0]:
                best = (residual, threshold, knee, makeup, c)
    residual, threshold, knee, makeup, c = best
    ratio = float("inf") if c >= 1.0 else 1.0 / (1.0 - c)

    slopes = []
    for index in range(len(xs) - 1):
        rise = ys[index + 1] - ys[index]
        run = xs[index + 1] - xs[index]
        slopes.append({"in_db": round(float(xs[index]), 3),
                       "slope": round(float(rise / run), 4) if run else None})
    values = {
        "points": [{"in_db": round(float(a), 3), "out_db": round(float(b), 3),
                    "gain_db": round(float(b - a), 3)} for a, b in points],
        "local_slope": slopes,
        "threshold_db": round(float(threshold), 3),
        "knee_db": round(float(knee), 3),
        "ratio": round(ratio, 4) if math.isfinite(ratio) else None,
        "makeup_db": round(makeup, 3),
        "fit_residual_db": round(residual, 4),
        "detector": detector,
    }
    criteria = dict(expected or {})
    red = []
    for name, key in (("threshold_db", "threshold_db"),
                      ("knee_db", "knee_db"), ("ratio", "ratio"),
                      ("makeup_db", "makeup_db")):
        if expected and name in expected:
            want, tol = expected[name]
            got = values[key]
            if got is None or abs(got - want) > tol:
                red.append("%s fitted %s against an expected %s (bar %s, fit "
                           "residual %.3f dB)"
                           % (name, got, want, tol, residual))
    return _result("CURVE", "dB", values,
                   wet_by_level_db[levels[0]].axes(), criteria, red)


def _knee_shape(x, threshold, knee):
    """f(x) in the soft-knee law: 0 below the knee, quadratic through it,
    (x - threshold) above."""
    x = np.asarray(x, dtype=np.float64)
    if knee <= 0:
        return np.maximum(x - threshold, 0.0)
    low = threshold - knee / 2.0
    high = threshold + knee / 2.0
    out = np.zeros_like(x)
    inside = (x > low) & (x <= high)
    out[inside] = (x[inside] - low) ** 2 / (2.0 * knee)
    out[x > high] = x[x > high] - threshold
    return out


def gaintrace(wet_render, dry_render, *, hop_ms=1.0, channel=0,
              release_from_ms=None, attack_from_ms=None, floor_db=-90.0,
              expected=None):
    """GAINTRACE - gain reduction against time.

    Per-hop ratio of the output envelope to the input envelope, in dB. The
    named times are exported as t50, t63 *and* t95, because the rows this
    serves are not all stated in the same one - and because a fault that
    collapses a two-stage release to its fast stage moves t95 while leaving
    t63 where it was, which is a fault that fires on part of the readout and
    not all of it.

    `release_from_ms` is when the input steps down and `attack_from_ms` when
    it steps up; the probe knows both, so they are stated rather than
    guessed from the trace.
    """
    require_signal(wet_render, "gaintrace wet render")
    require_signal(dry_render, "gaintrace dry render")
    wet_env, win = envelope(wet_render.float[:, channel], wet_render.rate,
                            hop_ms)
    dry_env, _ = envelope(dry_render.float[:, channel], dry_render.rate,
                          hop_ms)
    count = min(len(wet_env), len(dry_env))
    wet_env, dry_env = wet_env[:count], dry_env[:count]
    floor = 10 ** (floor_db / 20.0)
    live = dry_env > floor
    trace = np.full(count, np.nan)
    trace[live] = 20.0 * np.log10(np.maximum(wet_env[live], 1e-12)
                                  / dry_env[live])
    times_ms = np.arange(count) * (win * 1000.0 / wet_render.rate)

    values = {
        "hop_ms": hop_ms,
        "hop_frames": int(win),
        "trace_ms": [round(float(t), 3) for t in times_ms],
        "trace_gr_db": [None if math.isnan(v) else round(float(v), 3)
                        for v in trace],
    }

    def window_after(start_ms):
        index = int(np.searchsorted(times_ms, start_ms))
        return index

    if attack_from_ms is not None:
        start = window_after(attack_from_ms)
        segment = trace[start:]
        segment = segment[~np.isnan(segment)]
        if segment.size:
            depth = float(np.nanmin(segment))
            values["attack_gr_depth_db"] = round(depth, 3)
            values["attack_t10_90_ms"] = _transition_ms(
                segment, times_ms[start:start + segment.size],
                segment[0], depth, (0.1, 0.9))
    if release_from_ms is not None:
        start = window_after(release_from_ms)
        segment = trace[start:]
        segment = segment[~np.isnan(segment)]
        if segment.size:
            begin = float(segment[0])
            end = float(segment[-1])
            times = times_ms[start:start + segment.size]
            values["release_from_gr_db"] = round(begin, 3)
            values["release_to_gr_db"] = round(end, 3)
            for fraction, name in ((0.5, "t50_ms"), (0.63, "t63_ms"),
                                   (0.95, "t95_ms")):
                values["release_" + name] = _fraction_ms(
                    segment, times, begin, end, fraction)
    steady = trace[~np.isnan(trace)]
    values["settled_gr_db"] = round(float(steady[-1]), 3) if steady.size \
        else None

    criteria = dict(expected or {})
    red = []
    for name, (want, tol) in (expected or {}).items():
        got = values.get(name)
        if got is None:
            red.append("%s was not measurable on this trace" % name)
        elif abs(got - want) > tol:
            red.append("%s measured %.2f against an expected %.2f (bar %.2f)"
                       % (name, got, want, tol))
    return _result("GAINTRACE", "dB, ms", values, wet_render.axes(),
                   criteria, red)


def _fraction_ms(segment, times, begin, end, fraction):
    """Time from the start of `segment` at which it has covered `fraction`
    of the way from `begin` to `end`, linearly interpolated between hops."""
    span = end - begin
    if span == 0:
        return None
    target = begin + fraction * span
    for index in range(1, len(segment)):
        a, b = segment[index - 1], segment[index]
        if (a - target) * (b - target) <= 0 and a != b:
            weight = (target - a) / (b - a)
            return round(float(times[index - 1] - times[0]
                               + weight * (times[index] - times[index - 1])),
                         3)
    return None


def _transition_ms(segment, times, begin, end, fractions):
    low = _fraction_ms(segment, times, begin, end, fractions[0])
    high = _fraction_ms(segment, times, begin, end, fractions[1])
    if low is None or high is None:
        return None
    return round(high - low, 3)


def gaintrace_level_search(render_pair, target_gr_db, *, low_db=-60.0,
                           high_db=0.0, tolerance_db=0.1, iterations=24,
                           **trace_options):
    """The level search GAINTRACE needs because many rows are stated at a
    gain-reduction depth rather than at an input level - "after a 10 s tone
    holding 10 dB of GR stops", "at 3, 10 and 20 dB of GR".

    `render_pair(level_db)` returns (wet, dry) renders at that input level.
    Bisects until the settled GR is within `tolerance_db` of the target and
    exports the level it found beside the trace. Without it those rows are
    not measurable at all.
    """
    found = None
    for _ in range(iterations):
        middle = 0.5 * (low_db + high_db)
        wet, dry = render_pair(middle)
        result = gaintrace(wet, dry, **trace_options)
        settled = result["values"]["settled_gr_db"]
        found = (middle, settled, result)
        if settled is None:
            break
        if abs(abs(settled) - target_gr_db) <= tolerance_db:
            break
        if abs(settled) < target_gr_db:
            low_db = middle
        else:
            high_db = middle
    level_db, settled, result = found
    result["values"]["level_search"] = {
        "target_gr_db": target_gr_db,
        "found_input_db": round(level_db, 4),
        "settled_gr_db": settled,
        "tolerance_db": tolerance_db,
    }
    return result


# --------------------------------------------------------------------------
# Measurements 11-20, appended to the ten above. Same contract: a `Render`
# (or two) in, a `_result` out, `red` naming the readout that fired.
#
# Two refusals live here that the first ten did not need. `require_signal`
# above covers the silence rule; the ones below are the same *shape* of bug
# arriving by a different door - a null with nothing to defeat, a cost figure
# for a class that idled, a round trip with no wire in the loop. Each returns
# a number that reads as an excellent result, which is why each raises
# instead.
# --------------------------------------------------------------------------

class MeasurementRefused(AssertionError):
    """A measurement declined to return a number at all.

    Distinct from `SilentRenderError`, which is the silence rule. This is
    every other way a measurement can be handed material it cannot measure
    but *could* put a plausible number on: two silences to null against, a
    muted or idling subject to time, a capture with nothing of the emitted
    signal in it. A refusal is loud; a plausible number is not.
    """


def arrivals(x, rate, *, threshold_db=-40.0, min_gap_ms=1.0, window=8):
    """Every arrival in a render, each with a sub-sample position.

    `onset()` above finds the first one, which is what WIRE and CLICK need.
    TAPS, DECAY and STEREO need all of them and need them ordered, so this
    walks the short-window energy envelope for local maxima above a floor
    stated re the render's own peak, separated by at least `min_gap_ms`, and
    refines each by the same parabola `onset()` uses.

    The smoothing window's own group delay, `(window - 1) / 2` samples, is
    taken back off every position. It has to be: CLICK reads a *difference*
    of two onsets and a constant bias cancels there, but TAPS reads an
    absolute delay time against the value a knob was set to, and at 48 kHz
    an uncompensated 8-sample window puts every arrival 0.073 ms late -
    which is a seventh of the tolerance a delay-time row is judged at.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return []
    kernel = np.ones(max(1, window)) / max(1, window)
    energy = np.sqrt(np.convolve(x * x, kernel, mode="same"))
    if energy.max() <= 0.0:
        return []
    floor = energy.max() * 10.0 ** (threshold_db / 20.0)
    gap = max(1, int(round(rate * min_gap_ms / 1000.0)))
    found, i = [], 1
    while i < len(energy) - 1:
        if (energy[i] >= floor and energy[i] >= energy[i - 1]
                and energy[i] > energy[i + 1]):
            fine = _parabola(energy, i) - 0.5 * (max(1, window) - 1)
            found.append({"sample": int(i), "fine_sample": fine,
                          "ms": 1000.0 * fine / rate,
                          "level_db": db(energy[i])})
            i += gap
        else:
            i += 1
    return found


def _parabola(values, index):
    """Sub-sample peak by a parabola through three points."""
    if index <= 0 or index >= len(values) - 1:
        return float(index)
    a, b, c = float(values[index - 1]), float(values[index]), \
        float(values[index + 1])
    denominator = a - 2.0 * b + c
    if denominator == 0.0:
        return float(index)
    return float(index) + 0.5 * (a - c) / denominator


def _lstsq(design, target):
    coefficients, *_ = np.linalg.lstsq(design, target, rcond=None)
    return coefficients


# --------------------------------------------------------------------------
# 11 ENVELOPE
# --------------------------------------------------------------------------

def envelope_record_seconds(rate_hz, tolerance_fraction):
    """How long a record ENVELOPE needs to resolve `rate_hz` to
    +/- `tolerance_fraction`, and the reason the rule exists.

    A fit over T seconds separates components about 1/T apart, so asking for
    half the tolerance gives T = 2 / (rate * tolerance). That reproduces the
    spec's worked figure - 2 / (0.667 * 0.025) = 120 s to hold 0.667 Hz to
    +/- 2.5 %. A 20 s record at that rate resolves 0.05 Hz, which is 7.5 % of
    the rate: it passes anything, which is why the record length is part of
    the measurement and not a convenience of the caller's.
    """
    if rate_hz <= 0 or tolerance_fraction <= 0:
        raise ValueError("rate and tolerance must be positive")
    return 2.0 / (float(rate_hz) * float(tolerance_fraction))


def _track(x, rate, hop_ms, how):
    """The envelope ENVELOPE reads. `peak` is the spec's word; `rms` is
    part B's `envelope()` primitive, which differs only by a constant for a
    carrier of at least one cycle per hop and so leaves every ratio here
    unchanged."""
    if how == "rms":
        env, win = envelope(x, rate, hop_ms)
        return env, rate / float(win)
    x = np.asarray(x, dtype=np.float64)
    hop = max(1, int(round(rate * hop_ms / 1000.0)))
    usable = len(x) - len(x) % hop
    return np.abs(x[:usable]).reshape(-1, hop).max(axis=1), rate / float(hop)


def _modulation_rate(env, env_rate, minimum_hz=0.05):
    signal = env - env.mean()
    spec = np.abs(np.fft.rfft(signal * np.hanning(len(signal))))
    freqs = np.fft.rfftfreq(len(signal), 1.0 / env_rate)
    low = int(np.searchsorted(freqs, minimum_hz))
    if low >= len(spec) - 1:
        raise MeasurementRefused(
            "ENVELOPE: %.3f s of envelope cannot carry a modulation rate"
            % (len(env) / env_rate))
    peak = low + int(np.argmax(spec[low:]))
    return _parabola(spec, peak) * env_rate / len(signal)


def envelope_shape(render, *, rate_hint=None, harmonics=8, hop_ms=1.0,
                   track="peak", channel=0, rate_tolerance=None,
                   expected=None, tolerances=None, max_harmonic_db=None):
    """ENVELOPE - the amplitude envelope of a carrier tone, and everything
    read off it: depth, duty, steepest slopes, harmonics of the modulation
    rate, the extracted rate itself, and inter-channel phase with its sign.

    Named `envelope_shape` because `envelope()` above is the per-hop RMS
    primitive this calls; the measurement is ENVELOPE.

    **Depth is the fitted fundamental, never max-minus-min**, which reads the
    noise floor. Duty and the slope ratio are read off the full
    reconstruction - fundamental plus `harmonics` - because that is where a
    shaped LFO differs from a sine at the same rate and depth, and that
    difference is this measurement's planted fault: replace the shaped LFO
    with a pure sine at the same rate and depth, and rate and depth stay
    green while duty, slope ratio and the rate harmonics all go red. The
    control and the fault come out of one run.

    `expected` is compared **two-sided**, the rate harmonics included: a
    trait that names a shaped LFO is missed as badly by an LFO with no
    harmonics as by one with too many, and a one-sided "harmonics below X"
    check is exactly what a pure sine walks through. `max_harmonic_db` is
    the one-sided form, for a trait that only asks for a clean modulator.

    `rate_tolerance` turns the record-length rule into a reported fact rather
    than a convention: a record too short to resolve the rate to that
    tolerance is red on `record_seconds`, whatever the rate readout says.
    """
    require_signal(render, "envelope render")
    signal = render.float
    per_channel = []
    for index in range(render.channels):
        env, env_rate = _track(signal[:, index], render.rate, hop_ms, track)
        rate_hz = (float(rate_hint) if rate_hint
                   else _modulation_rate(env, env_rate))
        times = np.arange(len(env)) / env_rate
        columns = [np.ones(len(env))]
        for order in range(1, harmonics + 1):
            angle = 2.0 * math.pi * rate_hz * order * times
            columns.append(np.cos(angle))
            columns.append(np.sin(angle))
        design = np.vstack(columns).T
        coefficients = _lstsq(design, env)
        shape = design @ coefficients
        offset = float(coefficients[0])
        amplitude, phase = [], []
        for order in range(1, harmonics + 1):
            cosine = float(coefficients[2 * order - 1])
            sine = float(coefficients[2 * order])
            amplitude.append(math.hypot(cosine, sine))
            phase.append(math.degrees(math.atan2(-sine, cosine)))
        fundamental = amplitude[0]
        depth_db = (db(offset + fundamental) - db(offset - fundamental)
                    if offset > fundamental else float("inf"))
        period = max(2, int(round(env_rate / rate_hz)))
        cycle = shape[:period]
        middle = 0.5 * (float(cycle.max()) + float(cycle.min()))
        slope = np.diff(cycle)
        rising = float(slope.max()) if slope.size else 0.0
        falling = float(-slope.min()) if slope.size else 0.0
        per_channel.append({
            "channel": index,
            "rate_hz": round(rate_hz, 6),
            "depth_db": round(depth_db, 4),
            "duty_pct": round(100.0 * float(np.mean(cycle > middle)), 3),
            "slope_ratio": (round(rising / falling, 4) if falling > 0
                            else float("inf")),
            "harmonic_db": [round(db(value) - db(fundamental), 3)
                            for value in amplitude[1:]],
            "phase_deg": round(phase[0], 3),
            "fit_residual": round(float(np.sqrt(
                np.mean((env - shape) ** 2))), 6),
            "envelope_rate_hz": env_rate,
        })

    read = per_channel[channel]
    seconds = render.seconds()
    required = (envelope_record_seconds(read["rate_hz"], rate_tolerance)
                if rate_tolerance else None)
    values = {
        "per_channel": per_channel,
        "track": track,
        "hop_ms": hop_ms,
        "harmonics_fitted": harmonics,
        "record_seconds": round(seconds, 4),
        "rate_resolution_hz": round(1.0 / seconds, 6) if seconds else None,
        "required_seconds": (round(required, 3) if required else None),
    }
    for key in ("rate_hz", "depth_db", "duty_pct", "slope_ratio",
                "harmonic_db", "phase_deg", "fit_residual"):
        values[key] = read[key]
    if render.channels == 2:
        difference = (per_channel[0]["phase_deg"]
                      - per_channel[1]["phase_deg"])
        values["phase_l_minus_r_deg"] = round(
            (difference + 180.0) % 360.0 - 180.0, 3)

    bars = {"rate_hz": 0.05, "depth_db": 0.5, "duty_pct": 3.0,
            "slope_ratio": 0.25, "harmonic_db": 3.0}
    bars.update(tolerances or {})
    criteria = {"tolerances": bars, "rate_tolerance": rate_tolerance,
                "record_rule": "T >= 2 / (rate * tolerance)"}
    red, failed = [], []
    if required is not None and seconds < required:
        failed.append("record_seconds")
        red.append("record_seconds: %.1f s of record cannot hold %.4f Hz to "
                   "+/-%.1f %%; the rule asks for %.1f s"
                   % (seconds, read["rate_hz"], 100.0 * rate_tolerance,
                      required))
    strongest = (max(values["harmonic_db"][:2]) if values["harmonic_db"]
                 else float("-inf"))
    values["strongest_rate_harmonic_db"] = strongest
    for key, want in (expected or {}).items():
        got = strongest if key == "harmonic_db" else values[key]
        if abs(float(got) - float(want)) > bars.get(key, 0.0):
            failed.append(key)
            red.append("%s: %s against an expected %s (bar %s)"
                       % (key, got, want, bars.get(key)))
    if max_harmonic_db is not None and strongest > float(max_harmonic_db):
        failed.append("harmonic_db")
        red.append("harmonic_db: strongest rate harmonic %.2f dB re the "
                   "fundamental, above the %.2f dB the trait names"
                   % (strongest, float(max_harmonic_db)))
    values["failed_readouts"] = failed
    return _result("ENVELOPE", "mixed", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 12 IFREQ
# --------------------------------------------------------------------------

def analytic(x):
    """The analytic signal, by FFT. No scipy: the analysis is offline."""
    x = np.asarray(x, dtype=np.float64)
    count = len(x)
    weights = np.zeros(count)
    if count % 2 == 0:
        weights[0] = weights[count // 2] = 1.0
        weights[1:count // 2] = 2.0
    else:
        weights[0] = 1.0
        weights[1:(count + 1) // 2] = 2.0
    return np.fft.ifft(np.fft.fft(x) * weights)


def instantaneous_hz(x, rate):
    """Unwrapped phase derivative of the analytic signal, in Hz."""
    return np.gradient(np.unwrap(np.angle(analytic(x)))) * rate \
        / (2.0 * math.pi)


def ifreq(render, rate_hz, *, carrier_hz=None, channel=0,
          splice_period_samples=None, guard_fraction=0.25,
          edge_fraction=0.05, expected_cents=None, tolerance_cents=5.0,
          residual_bar_cents=25.0):
    """IFREQ - instantaneous frequency from the analytic signal: doppler,
    wow and flutter, vibrato, pitch-shift ratio, per-repeat pitch.

    `splice_period_samples` applies the **splice-period correction**, and it
    is not optional where a granular shifter is in the path: the kernel's
    periodic splice leaves a phase discontinuity that is not a pitch
    deviation, and uncorrected it lands in the residual. That is this
    measurement's planted fault, and it is the unusual kind - omit the
    correction and a **correct** build reads red. The control that must pass
    beside it is the same uncorrected reading on a path with no shifter in
    it, which stays green. (The obvious fault - hold the modulation depth at
    zero while the class still reports it - is an inert modulator: it
    flattens every readout at once and proves only that the measurement
    notices nothing happening.)
    """
    require_signal(render, "ifreq render")
    signal = render.float[:, channel]
    frequency = instantaneous_hz(signal, render.rate)

    edge = int(len(frequency) * edge_fraction)
    mask = np.zeros(len(frequency), dtype=bool)
    mask[edge:len(frequency) - edge] = True
    corrected = splice_period_samples is not None
    if corrected:
        period = int(round(splice_period_samples))
        guard = max(1, int(round(period * guard_fraction)))
        for boundary in range(0, len(frequency), period):
            mask[max(0, boundary - guard):boundary + guard + 1] = False
    if int(mask.sum()) < 16:
        raise MeasurementRefused(
            "IFREQ: the splice correction left %d samples to fit"
            % int(mask.sum()))

    times = np.arange(len(frequency)) / render.rate
    angle = 2.0 * math.pi * rate_hz * times[mask]
    design = np.vstack([np.ones(int(mask.sum())), np.cos(angle),
                        np.sin(angle)]).T
    coefficients = _lstsq(design, frequency[mask])
    centre = float(coefficients[0])
    deviation_hz = math.hypot(float(coefficients[1]), float(coefficients[2]))
    leftover = frequency[mask] - design @ coefficients
    residual_hz = float(np.sqrt(np.mean(leftover ** 2)))

    reference = float(carrier_hz) if carrier_hz else centre
    to_cents = (lambda hz: 1200.0 * math.log2((reference + hz) / reference)
                if reference > 0 else 0.0)
    second = 2.0 * math.pi * 2.0 * rate_hz * times[mask]
    second_fit = _lstsq(np.vstack([np.cos(second), np.sin(second)]).T,
                        leftover)
    second_hz = math.hypot(float(second_fit[0]), float(second_fit[1]))

    values = {
        "centre_hz": round(centre, 4),
        "deviation_hz": round(deviation_hz, 5),
        "deviation_cents": round(to_cents(deviation_hz), 4),
        "residual_rms_hz": round(residual_hz, 5),
        "residual_rms_cents": round(to_cents(residual_hz), 4),
        "second_harmonic_db": round(db(second_hz) - db(deviation_hz), 2)
        if deviation_hz > 0 else float("inf"),
        "splice_corrected": corrected,
        "splice_period_samples": splice_period_samples,
        "fitted_samples": int(mask.sum()),
        "modulation_rate_hz": rate_hz,
    }
    criteria = {"tolerance_cents": tolerance_cents,
                "residual_bar_cents": residual_bar_cents,
                "expected_cents": expected_cents}
    red, failed = [], []
    if values["residual_rms_cents"] > residual_bar_cents:
        failed.append("residual_rms_cents")
        red.append("residual_rms_cents: %.2f cents left after the fit, above "
                   "the %.2f cent bar%s"
                   % (values["residual_rms_cents"], residual_bar_cents,
                      "" if corrected else
                      " - is there a granular shifter in this path with no "
                      "splice-period correction applied?"))
    if expected_cents is not None:
        error = abs(values["deviation_cents"] - float(expected_cents))
        if error > tolerance_cents:
            failed.append("deviation_cents")
            red.append("deviation_cents: %.2f against an expected %.2f "
                       "(%.2f cents out, bar %.2f)"
                       % (values["deviation_cents"], float(expected_cents),
                          error, tolerance_cents))
    values["failed_readouts"] = failed
    return _result("IFREQ", "cents", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 13 TAPS
# --------------------------------------------------------------------------

def comb_spacing_hz(x, rate, *, pad_seconds=2.0, minimum_hz=5.0):
    """Comb spacing fitted from a zero-padded magnitude spectrum.

    A comb's magnitude spectrum is periodic in frequency and its period is
    the spacing, so the read is an autocorrelation along the frequency axis.
    The padding is the resolution and is stated: 20 s gives 0.05 Hz bins,
    which is the spec's setting; the default here is 2 s because that is what
    the battery needs to separate the settings it compares.
    """
    x = np.asarray(x, dtype=np.float64)
    size = max(int(pad_seconds * rate), len(x))
    magnitude = np.abs(np.fft.rfft(x, n=size))
    magnitude = magnitude - magnitude.mean()
    correlation = np.correlate(magnitude, magnitude, mode="full")
    correlation = correlation[len(correlation) // 2:]
    bin_hz = rate / float(size)
    low = max(1, int(minimum_hz / bin_hz))
    if low >= len(correlation) - 1:
        raise MeasurementRefused("TAPS: not enough spectrum for a spacing")
    peak = low + int(np.argmax(correlation[low:]))
    return _parabola(correlation, peak) * bin_hz


def taps(render, *, expected_ms=None, tolerance_ms=0.5, threshold_db=-40.0,
         min_gap_ms=1.0, channel=0, spacing=False, pad_seconds=2.0,
         expected_spacing_ms=None):
    """TAPS - arrival structure: delay time against the mapped value,
    per-repeat arrival and level, inter-channel arrival difference, comb
    spacing, splice period.

    **The planted fault here is a measured one, not a hypothetical, and it is
    the model for the whole kit.** Build the line on
    `audiodelays.Echo(freq_shift=False)` at `_core.pcm()`'s 2048-byte buffer:
    the 1, 5 and 14 ms settings all deliver 21.33 ms and must go red, while
    30 and 40 ms stay green. The load-bearing detail is the flag - with the
    node's default `freq_shift=True` there is no floor, every setting lands
    within 0.02 ms, and a fault planted that way does not fire at all. A
    checker that cannot fail is not a checker.
    """
    require_signal(render, "taps render")
    per_channel = []
    for index in range(render.channels):
        per_channel.append({
            "channel": index,
            "taps": arrivals(render.float[:, index], render.rate,
                             threshold_db=threshold_db,
                             min_gap_ms=min_gap_ms),
        })
    found = per_channel[channel]["taps"]
    if not found:
        raise MeasurementRefused(
            "TAPS: no arrival above %.1f dB re the render's own peak"
            % threshold_db)

    values = {
        "first_tap_ms": round(found[0]["ms"], 5),
        "tap_count": len(found),
        "tap_ms": [round(tap["ms"], 5) for tap in found],
        "tap_level_db": [round(tap["level_db"], 3) for tap in found],
        "expected_ms": expected_ms,
        "per_channel": [
            {"channel": entry["channel"],
             "tap_ms": [round(tap["ms"], 5) for tap in entry["taps"]]}
            for entry in per_channel],
    }
    if len(found) > 1:
        gaps = np.diff([tap["ms"] for tap in found])
        values["repeat_spacing_ms"] = round(float(np.mean(gaps)), 5)
        values["repeat_spacing_spread_ms"] = round(float(np.ptp(gaps)), 5)
    if render.channels == 2 and per_channel[0]["taps"] \
            and per_channel[1]["taps"]:
        values["inter_channel_ms"] = round(
            per_channel[0]["taps"][0]["ms"] - per_channel[1]["taps"][0]["ms"],
            5)
    if spacing:
        values["comb_spacing_hz"] = round(comb_spacing_hz(
            render.float[:, channel], render.rate,
            pad_seconds=pad_seconds), 4)

    criteria = {"tolerance_ms": tolerance_ms, "threshold_db": threshold_db,
                "expected_ms": expected_ms,
                "expected_spacing_ms": expected_spacing_ms}
    red, failed = [], []
    if expected_ms is not None:
        error = values["first_tap_ms"] - float(expected_ms)
        values["error_ms"] = round(error, 5)
        if abs(error) > tolerance_ms:
            failed.append("first_tap_ms")
            red.append("first_tap_ms: %.3f ms against a mapped %.3f ms "
                       "(%.3f ms out, bar %.3f)"
                       % (values["first_tap_ms"], float(expected_ms), error,
                          tolerance_ms))
    if expected_spacing_ms is not None and "repeat_spacing_ms" in values:
        error = values["repeat_spacing_ms"] - float(expected_spacing_ms)
        if abs(error) > tolerance_ms:
            failed.append("repeat_spacing_ms")
            red.append("repeat_spacing_ms: %.3f ms against an expected "
                       "%.3f ms" % (values["repeat_spacing_ms"],
                                    float(expected_spacing_ms)))
    values["failed_readouts"] = failed
    return _result("TAPS", "ms", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 14 DECAY
# --------------------------------------------------------------------------

def band_limit(x, rate, low_hz, high_hz):
    """Zero-phase band limit by masking the spectrum. Offline analysis, so
    zero phase is free and no filter state can leak between bands."""
    x = np.asarray(x, dtype=np.float64)
    spectrum = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / rate)
    spectrum[(freqs < low_hz) | (freqs >= high_hz)] = 0.0
    return np.fft.irfft(spectrum, n=len(x))


def schroeder(x):
    """Backward-integrated energy decay, in dB re the total - the EDR
    curve."""
    x = np.asarray(x, dtype=np.float64)
    energy = np.cumsum((x ** 2)[::-1])[::-1]
    total = float(energy[0]) if energy.size and energy[0] > 0 else 1.0
    return 10.0 * np.log10(np.maximum(energy / total, 1e-30))


def decay(render, *, bands=((20.0, 300.0), (300.0, 3000.0),
                            (3000.0, 20000.0)),
          threshold_db=-40.0, min_gap_ms=5.0, channel=None,
          darkening_bar_db=None, hop_ms=1.0):
    """DECAY - how a tail evolves: RT60/EDR, per-pass darkening, echo
    density, per-repeat band energy.

    The finding is the **progression**, and that is deliberate. The planted
    fault - apply the darkening once at the input instead of inside the loop
    - leaves repeat one exactly right and flattens every repeat after it, so
    `darkening_slope_db_per_repeat` is the readout that fires and a
    single-repeat check sees a correct build.
    """
    require_signal(render, "decay render")
    signal = (render.float.mean(axis=1) if channel is None
              else render.float[:, channel])

    limited = [band_limit(signal, render.rate, low, high)
               for low, high in bands]
    t60, tau_per_band = [], []
    for band in limited:
        env, win = envelope(band, render.rate, hop_ms)
        peak = int(np.argmax(env))
        tau, sixty = tau_t60(env, render.rate, win, start=peak)
        tau_per_band.append(None if tau is None else round(tau, 5))
        t60.append(None if sixty is None else round(sixty, 5))

    found = arrivals(signal, render.rate, threshold_db=threshold_db,
                     min_gap_ms=min_gap_ms)
    repeats = []
    for index, arrival in enumerate(found):
        start = arrival["sample"]
        stop = (found[index + 1]["sample"] if index + 1 < len(found)
                else len(signal))
        if stop - start < 16:
            continue
        energies = [float(np.sum(band[start:stop] ** 2)) for band in limited]
        total = sum(energies) or 1e-30
        repeats.append({
            "repeat": index,
            "ms": round(arrival["ms"], 4),
            "level_db": round(arrival["level_db"], 3),
            "band_share_db": [round(10.0 * math.log10(max(v, 1e-30) / total),
                                    3) for v in energies],
        })

    high_share = [entry["band_share_db"][-1] for entry in repeats]
    slope = None
    if len(high_share) >= 2:
        slope = round(float(np.polyfit(np.arange(len(high_share)),
                                       high_share, 1)[0]), 4)

    seconds = render.seconds()
    values = {
        "bands_hz": [list(band) for band in bands],
        "t60_per_band_s": t60,
        "tau_per_band_s": tau_per_band,
        "repeats": repeats,
        "repeat_count": len(repeats),
        "high_band_share_db": high_share,
        "first_repeat_share_db": high_share[0] if high_share else None,
        "darkening_slope_db_per_repeat": slope,
        "echo_density_per_s": round(len(found) / seconds, 3) if seconds else 0,
        "edr_at_half_db": round(float(schroeder(signal)[len(signal) // 2]), 3),
    }
    criteria = {"darkening_bar_db_per_repeat": darkening_bar_db,
                "threshold_db": threshold_db}
    red, failed = [], []
    if darkening_bar_db is not None:
        if slope is None:
            failed.append("darkening_slope_db_per_repeat")
            red.append("darkening_slope_db_per_repeat: fewer than two "
                       "repeats found; the progression cannot be read")
        elif slope > darkening_bar_db:
            failed.append("darkening_slope_db_per_repeat")
            red.append("darkening_slope_db_per_repeat: %.3f dB per repeat "
                       "against a bar of %.3f - repeat one is right and the "
                       "progression is flat, which is what a darkening "
                       "applied once at the input looks like"
                       % (slope, darkening_bar_db))
    values["failed_readouts"] = failed
    return _result("DECAY", "dB, s", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 15 STEREO
# --------------------------------------------------------------------------

def require_identical_channels(probe_pcm, channels=2, tolerance_lsb=0):
    """STEREO's probe must be identical in both channels.

    Otherwise L-R is not silent at width zero and a correct endpoint reads as
    broken. A refusal rather than a note, because the number it protects -
    L-R in dBFS - is perfectly plausible either way.
    """
    data = np.frombuffer(bytes(probe_pcm), dtype="<i2")
    data = data[:len(data) - len(data) % channels].reshape(-1, channels)
    worst = int(np.max(np.abs(data[:, 0].astype(np.int32)
                              - data[:, 1].astype(np.int32))))
    if worst > tolerance_lsb:
        raise MeasurementRefused(
            "STEREO: the probe's channels differ by %d LSB - L-R cannot be "
            "read against it, and width zero would read as broken" % worst)
    return True


def stereo(render, *, source=None, threshold_db=-40.0, min_gap_ms=1.0,
           simultaneity_ms=0.5, require_alternation=False,
           lr_floor_db=None):
    """STEREO - the stereo field: L-R RMS, mono sum against the source,
    correlation, width, per-channel arrival and level.

    And the arrival order **across both channels**, which is the readout the
    seeds' own planted fault demands. Measure down one channel instead of
    across both and a ping-pong that is really two independent delays at half
    rate passes everything: each channel taken alone has the right spacing,
    the right decay and a plausible correlation. What separates them is the
    interleaving - a real ping-pong's arrivals alternate L, R, L, R in time,
    and two independent delays put both channels in the same cluster.
    `ping_pong_alternates` is that read.
    """
    require_signal(render, "stereo render")
    if render.channels != 2:
        raise ValueError("STEREO reads a stereo render; %d channels given"
                         % render.channels)
    signal = render.float
    left, right = signal[:, 0], signal[:, 1]
    difference = left - right
    mono = 0.5 * (left + right)

    values = {
        "l_minus_r_dbfs": round(rms_db(difference), 3),
        "left_rms_dbfs": round(rms_db(left), 3),
        "right_rms_dbfs": round(rms_db(right), 3),
        "mono_rms_dbfs": round(rms_db(mono), 3),
        "correlation": round(float(np.corrcoef(left, right)[0, 1]), 4)
        if left.std() > 0 and right.std() > 0 else 1.0,
        "width": round(float(rms(difference) / max(rms(mono), 1e-12)), 4),
    }
    if source is not None:
        source_mono = source.float.mean(axis=1)
        count = min(len(source_mono), len(mono))
        values["mono_sum_deviation_db"] = round(
            rms_db(mono[:count]) - rms_db(source_mono[:count]), 3)

    ordered = []
    for index, name in ((0, "L"), (1, "R")):
        for arrival in arrivals(signal[:, index], render.rate,
                                threshold_db=threshold_db,
                                min_gap_ms=min_gap_ms):
            ordered.append((arrival["ms"], name, arrival["level_db"]))
    ordered.sort()

    clusters = []
    for when, name, level in ordered:
        if clusters and when - clusters[-1]["ms"] <= simultaneity_ms:
            clusters[-1]["channels"].append(name)
            clusters[-1]["level_db"].append(level)
        else:
            clusters.append({"ms": when, "channels": [name],
                             "level_db": [level]})
    single = [c for c in clusters if len(c["channels"]) == 1]
    alternates = len(clusters) >= 2 and len(single) == len(clusters)
    if alternates:
        for one, other in zip(clusters, clusters[1:]):
            if one["channels"][0] == other["channels"][0]:
                alternates = False
                break

    values.update({
        "arrival_clusters": [
            {"ms": round(c["ms"], 4), "channels": "".join(c["channels"]),
             "level_db": round(max(c["level_db"]), 3)} for c in clusters],
        "cluster_count": len(clusters),
        "simultaneous_clusters": len(clusters) - len(single),
        "ping_pong_alternates": alternates,
        "left_arrival_ms": [round(w, 4) for w, n, _ in ordered if n == "L"],
        "right_arrival_ms": [round(w, 4) for w, n, _ in ordered if n == "R"],
    })

    criteria = {"require_alternation": require_alternation,
                "lr_floor_db": lr_floor_db,
                "simultaneity_ms": simultaneity_ms}
    red, failed = [], []
    if require_alternation and not alternates:
        failed.append("ping_pong_alternates")
        red.append("ping_pong_alternates: arrivals do not alternate across "
                   "the channels - %d of %d clusters carry both, which is "
                   "two independent delays at half rate, not a ping-pong"
                   % (values["simultaneous_clusters"], len(clusters)))
    if lr_floor_db is not None and values["l_minus_r_dbfs"] > lr_floor_db:
        failed.append("l_minus_r_dbfs")
        red.append("l_minus_r_dbfs: %.2f dBFS against a floor of %.2f"
                   % (values["l_minus_r_dbfs"], lr_floor_db))
    values["failed_readouts"] = failed
    return _result("STEREO", "dB", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 16 RESIDUAL
# --------------------------------------------------------------------------

def ideal_quantise(x, bits):
    """Round-to-nearest at `bits` - the reference every residual is taken
    against."""
    step = 2.0 ** -(bits - 1)
    return np.round(np.asarray(x, dtype=np.float64) / step) * step


def residual(render, reference_render, bits, *, channel=0,
             expect="truncation", mean_bar_lsb=0.25, rms_bar_lsb=1.0,
             require_dc_probe=True):
    """RESIDUAL - quantisation and decimation error: bit depth, sample-rate
    reduction, dither.

    The residual is the render minus an **ideally quantised** reference at
    the same word length, in LSB of that word length.

    The **mean** is the readout that fires, and that is the whole reason it
    is exported beside the RMS. The planted fault is truncation replaced by
    rounding at the same word length. Measured against the ideally quantised
    reference on the DC-offset probe at 8 bits, not recalled: floor
    truncation leaves a two-valued residual of {0, -1} LSB - **mean
    -0.4993 LSB, RMS 0.7066** - and round-to-nearest leaves **mean
    +0.0000 LSB, RMS 0.0365** (the int16 render grid, 256x finer than the
    word being measured, and nothing else). Both RMS figures sit inside any
    bar a residual RMS would be given, so the RMS does not fire; the mean
    goes to zero and does.

    (The textbook pair - uniform on [-1, 0) with RMS 0.577 against uniform
    on [-0.5, 0.5) with RMS 0.289 - is the error against the *unquantised*
    signal. This measurement's residual is against the ideally quantised
    reference, which is a different and larger quantity for truncation and a
    near-zero one for rounding. The conclusion is the same and the numbers
    are not, so the numbers here are the ones this code produces.)

    **The probe must carry a DC offset, and that is load-bearing.**
    Truncation *toward zero* has zero mean on material symmetric about zero,
    so on a sweep or on noise a rounding build and a truncate-toward-zero
    build read identically and the fault does not fire at all. On a
    half-scale-biased ramp every truncation mode leaves a mean and only
    round-to-nearest does not. `require_dc_probe` refuses the reading rather
    than taking it on material that cannot separate them.
    """
    require_signal(render, "residual render")
    out = render.float[:, channel]
    ref = reference_render.float[:, channel]
    count = min(len(out), len(ref))
    out, ref = out[:count], ref[:count]

    probe_mean = float(np.mean(ref))
    if require_dc_probe and abs(probe_mean) < 0.05:
        raise MeasurementRefused(
            "RESIDUAL: the probe's mean is %.4f of full scale. Truncation "
            "toward zero has zero mean on material symmetric about zero, so "
            "a rounding build and a truncating one read identically here - "
            "this measurement needs the DC-offset probe" % probe_mean)

    step = 2.0 ** -(bits - 1)
    error = (out - ideal_quantise(ref, bits)) / step

    held, runs = 1, []
    changes = np.nonzero(np.diff(out))[0]
    previous = -1
    for index in changes:
        runs.append(int(index) - previous)
        previous = int(index)
    runs.append(count - 1 - previous)
    held = max(runs) if runs else count

    spectrum = np.abs(np.fft.rfft(error * np.hanning(count)))[1:]
    median = float(np.median(spectrum)) or 1e-30

    values = {
        "bits": bits,
        "mean_lsb": round(float(np.mean(error)), 5),
        "rms_lsb": round(float(np.sqrt(np.mean(error ** 2))), 5),
        "peak_lsb": round(float(np.max(np.abs(error))), 5),
        "max_run_length": int(held),
        "mean_run_length": round(float(np.mean(runs)), 4) if runs else None,
        "probe_mean_fs": round(probe_mean, 5),
        "probe_has_dc": bool(abs(probe_mean) >= 0.05),
        "residual_peak_to_median_db": round(
            20.0 * math.log10(float(np.max(spectrum)) / median), 3),
        "expect": expect,
    }
    criteria = {"expect": expect, "mean_bar_lsb": mean_bar_lsb,
                "rms_bar_lsb": rms_bar_lsb}
    red, failed = [], []
    if expect == "truncation" and abs(values["mean_lsb"]) < mean_bar_lsb:
        failed.append("mean_lsb")
        red.append("mean_lsb: %.4f LSB. The trait says truncation, which "
                   "leaves a mean of about -0.5 LSB here; a mean at zero is "
                   "round-to-nearest wearing a truncating class's name. "
                   "(RMS %.3f LSB, inside its %.2f bar either way, so the "
                   "RMS does not fire.)"
                   % (values["mean_lsb"], values["rms_lsb"], rms_bar_lsb))
    if expect == "rounding" and abs(values["mean_lsb"]) >= mean_bar_lsb:
        failed.append("mean_lsb")
        red.append("mean_lsb: %.4f LSB where the trait says round-to-nearest"
                   % values["mean_lsb"])
    if values["rms_lsb"] > rms_bar_lsb:
        failed.append("rms_lsb")
        red.append("rms_lsb: %.3f LSB above the %.2f LSB bar"
                   % (values["rms_lsb"], rms_bar_lsb))
    values["failed_readouts"] = failed
    return _result("RESIDUAL", "LSB", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 17 TRUEPEAK
# --------------------------------------------------------------------------

def _interpolator(taps_per_phase=24, factor=4):
    length = taps_per_phase * factor
    index = np.arange(-length, length + 1)
    kernel = np.sinc(index / float(factor)) * np.blackman(2 * length + 1)
    return kernel / float(kernel[::factor].sum()), length


def oversample(x, factor=4, taps_per_phase=24, trim=True):
    """Zero-stuff and interpolate: the reconstructed waveform between the
    samples, which is where a limiter with no true-peak detection
    overshoots.

    `trim` drops the interpolator's own start-up and run-out from each end,
    and it is on by default because without it this measurement reports an
    overshoot the class never produced. Measured, on the worst-phase f_s/4
    tone whose true peak is exactly 3.0103 dB above its sample peak: read
    untrimmed, the peak of the reconstruction lands at **upsampled sample
    10** - inside the kernel's own transient - and the tone reads
    -2.8954 dB TP, an excess of 3.10 dB. Trimmed, it reads -2.9895 dB TP,
    an excess of 3.0101 dB, against a theoretical -2.9897. The error is
    0.09 dB of pure filter ringing, on every true-peak reading, and it lands
    on the wrong side: it would report a ceiling exceeded that was met.
    """
    x = np.asarray(x, dtype=np.float64)
    stuffed = np.zeros(len(x) * factor)
    stuffed[::factor] = x
    kernel, length = _interpolator(taps_per_phase, factor)
    out = np.convolve(stuffed, kernel, mode="same")
    if trim and len(out) > 4 * length:
        out = out[length:len(out) - length]
    return out


def truepeak(render, *, ceiling_dbfs=None, tolerance_db=0.5, factor=4,
             read="true_peak"):
    """TRUEPEAK - inter-sample peak, BS.1770's 4x oversampling, against the
    sample peak and against the ceiling.

    `read` exists so the battery can run the **faulted** measurement as well
    as the correct one: `read="sample_peak"` is the fault - judge the ceiling
    on the sample peak instead of the oversampled one - and it must certify a
    build the correct read fails.

    Worked against `Limiter.md:557-558`. With true-peak detection off the
    palette reads sample peak -6.00 dBFS / true peak -2.95 dB TP; with it on,
    -7.93 dBFS / -4.88 dB TP. The two sample peaks do **not** collapse to one
    number, so a faulted measurement does not return an obviously broken
    pair - it returns a different, entirely plausible one. What it certifies
    is the real fault: with the flag off the sample peak reads -6.00 dBFS,
    exactly its ceiling, so the faulted read calls the ceiling met while
    3.05 dB escapes in the reconstructed waveform. **The red is against the
    ceiling in dB TP, not against the other setting.**

    A probe set with no worst-phase f_s/4 tone in it reads green on a
    limiter with no true-peak detection at all - `Limiter` L1's own
    disconfirmation clause - so `tone_fs4` is required material here, not
    optional.
    """
    require_signal(render, "truepeak render")
    per_channel = []
    for index in range(render.channels):
        channel = render.float[:, index]
        per_channel.append({
            "channel": index,
            "sample_peak_dbfs": round(peak_db(channel), 3),
            "true_peak_dbtp": round(peak_db(oversample(channel, factor)), 3),
        })
    sample_peak = max(entry["sample_peak_dbfs"] for entry in per_channel)
    true_peak = max(entry["true_peak_dbtp"] for entry in per_channel)
    judged = true_peak if read == "true_peak" else sample_peak

    values = {
        "per_channel": per_channel,
        "sample_peak_dbfs": round(sample_peak, 3),
        "true_peak_dbtp": round(true_peak, 3),
        "inter_sample_excess_db": round(true_peak - sample_peak, 3),
        "oversampling_factor": factor,
        "read": read,
        "judged_dbfs": round(judged, 3),
    }
    criteria = {"ceiling_dbfs": ceiling_dbfs, "tolerance_db": tolerance_db,
                "read": read}
    red, failed = [], []
    if ceiling_dbfs is not None:
        over = judged - float(ceiling_dbfs)
        values["over_ceiling_db"] = round(over, 3)
        values["meets_ceiling"] = over <= tolerance_db
        if over > tolerance_db:
            failed.append("true_peak_dbtp" if read == "true_peak"
                          else "sample_peak_dbfs")
            red.append("%s: %.2f against a ceiling of %.2f (%.2f dB over, "
                       "bar %.2f)" % (read, judged, float(ceiling_dbfs), over,
                                      tolerance_db))
    values["failed_readouts"] = failed
    return _result("TRUEPEAK", "dB TP", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 18 NULL
# --------------------------------------------------------------------------

def null(one, other, *, floor_dbfs, reference=None, channel=None):
    """NULL - one path defeated, and what must then vanish.

    Sample-wise difference of two renders of the same class, reported as a
    level in dBFS against a **stated floor**. The floor is the measurement:
    two silences null perfectly, and a null with no floor is exactly the
    check `compare_rig.py:36` had to be repaired to stop passing. So the
    reference side - the render that carries what the defeated path was
    supposed to remove - is refused if it does not itself clear the floor.
    There must be something here to defeat.

    Exports the null depth, the first offset above the floor, and the digest
    of both sides. The planted fault is the seed's own: re-wire OCT2 from the
    dry tap and the null goes red; the control that must pass beside it is
    the unmodified build, which nulls below -80 dBFS.
    """
    a = one.float if channel is None else one.float[:, channel:channel + 1]
    b = other.float if channel is None else other.float[:, channel:channel + 1]
    count = min(len(a), len(b))
    a, b = a[:count], b[:count]
    witness = reference if reference is not None else one
    witness_db = rms_db(witness.float)
    if witness_db <= floor_dbfs:
        raise MeasurementRefused(
            "NULL: the reference render is at %.2f dBFS, at or below the "
            "stated floor of %.2f - there is nothing here to defeat, and "
            "two silences null perfectly"
            % (witness_db, floor_dbfs))

    difference = a - b
    depth = rms_db(difference)
    above = np.nonzero(np.abs(difference).max(axis=1)
                       > 10.0 ** (floor_dbfs / 20.0))[0]
    values = {
        "null_depth_dbfs": round(depth, 3),
        "peak_difference_dbfs": round(peak_db(difference), 3),
        "floor_dbfs": float(floor_dbfs),
        "reference_dbfs": round(witness_db, 3),
        "first_offset_above_floor": int(above[0]) if above.size else None,
        "samples_above_floor": int(above.size),
        "digest_a": "%08x" % one.digest,
        "digest_b": "%08x" % other.digest,
    }
    criteria = {"floor_dbfs": float(floor_dbfs)}
    red, failed = [], []
    if depth > floor_dbfs:
        failed.append("null_depth_dbfs")
        red.append("null_depth_dbfs: %.2f dBFS against a stated floor of "
                   "%.2f - the defeated path is still audible in the "
                   "difference, first at sample %s"
                   % (depth, floor_dbfs, values["first_offset_above_floor"]))
    values["failed_readouts"] = failed
    return _result("NULL", "dBFS", values, one.axes(), criteria, red)


# --------------------------------------------------------------------------
# 19 COST - the board's number, judged here
# --------------------------------------------------------------------------

def real_time_factor(audio_seconds, wall_seconds):
    """audio-seconds / wall-seconds. 1.0 is exactly keeping up, which is
    already too slow: an interrupt, a GC pause or a flash read pushes it
    under."""
    if float(wall_seconds) <= 0.0:
        raise ValueError("wall_seconds must be positive")
    return float(audio_seconds) / float(wall_seconds)


def cost(subject, render, *, audio_seconds, wall_seconds, blocks,
         board=None, ram_bytes=None, settings=None, gain_reduction_db=None,
         minimum_gain_reduction_db=1.0, rt_bar=None):
    """COST - CPU on the boards, as a real-time factor, judged on the
    desktop.

    The arithmetic is `measure_voice_headroom.py`'s and the run is the
    board's; this is the gate the row has to pass to enter the table, and it
    is where the two ways of ranking fast without being fast are refused.

      1. **A muted class ranks fastest.** A class whose output is never
         pulled, or whose source returns silence, is the cheapest entry in
         any cost table. The render is refused before the row exists -
         `require_signal`, spec section 1, and COST is where absence reading
         as agreement is most expensive.
      2. **An idling class costs what a wire costs.** A compressor below its
         threshold, a drive stage at Drive 0, a reverb at Mix 0. Where the
         caller states the gain reduction the probe actually produced, a row
         taken below `minimum_gain_reduction_db` is refused - and the
         settings and the measured gain reduction are exported beside the
         figure either way, so a reader can see the probe reached the
         expensive path.

    The caveat travels with the number, because it is part of it: no I2S
    device is opened, one subject is measured per run, so derate.
    """
    require_signal(render, "cost render for %s" % subject)
    if (gain_reduction_db is not None
            and float(gain_reduction_db) < float(minimum_gain_reduction_db)):
        raise MeasurementRefused(
            "COST: %s idled - the probe produced %.2f dB of gain reduction "
            "against the %.2f dB this row requires. This figure is a wire's, "
            "not the class's, and it would rank near the top of the table."
            % (subject, float(gain_reduction_db),
               float(minimum_gain_reduction_db)))

    factor = real_time_factor(audio_seconds, wall_seconds)
    values = {
        "subject": subject,
        "board": board,
        "blocks": int(blocks),
        "blocks_per_s": round(float(blocks) / float(wall_seconds), 3),
        "ms_per_block": round(1000.0 * float(wall_seconds) / float(blocks), 4),
        "rt_factor": round(factor, 4),
        "audio_seconds": float(audio_seconds),
        "wall_seconds": float(wall_seconds),
        "ram_bytes": ram_bytes,
        "render_fnv1a": "%08x" % render.digest,
        "render_byte_sum": render.byte_sum,
        "settings": dict(settings or {}),
        "gain_reduction_db": gain_reduction_db,
        "caveat": "no I2S device opened; one subject per run; derate",
    }
    criteria = {"rt_bar": rt_bar,
                "minimum_gain_reduction_db": minimum_gain_reduction_db}
    red, failed = [], []
    if rt_bar is not None and factor < float(rt_bar):
        failed.append("rt_factor")
        red.append("rt_factor: %.3f against a bar of %.3f on %s"
                   % (factor, float(rt_bar), board))
    values["failed_readouts"] = failed
    return _result("COST", "rt factor", values, render.axes(), criteria, red)


# --------------------------------------------------------------------------
# 20 ROUNDTRIP - the platform path, not the effect graph
# --------------------------------------------------------------------------

def roundtrip(emitted, captured, *, block_frames, correlation_floor=0.3,
              starvation_count=None, settings=None, channel=0,
              target_ms=None):
    """ROUNDTRIP - output looped back to input on the board (vision section
    9a), judged here.

    Three guards, because the cheapest way to get a beautiful round-trip
    figure is not to measure a round trip:

      1. **A correlation floor.** With the loopback wire out, the capture is
         whatever the converter hears; the cross-correlation peak collapses
         and the run is refused rather than reported as a fast round trip.
      2. **The analysed stream must not be the emitted one.** Guard 1 does
         not catch the second fault: correlating the emitted click against
         the *playback* buffer is correlating it with itself, which peaks
         perfectly at lag 0 and satisfies the floor while the reported
         latency collapses toward zero. The digests must differ.
      3. **The peak must sit at least one block out.** The same fault by a
         different door - a playback buffer that is not byte-identical to
         what was emitted still peaks inside a block, and a round trip
         cannot be shorter than the buffer it passes through.

    `starvation_count` is the caller's, and the spec is explicit that it is
    counted rather than guessed - wrap the transport's write and count
    buffer-empty events - so it travels with the number and is exported even
    when it is zero.
    """
    require_signal(emitted, "roundtrip emitted")
    require_signal(captured, "roundtrip captured")
    if emitted.digest == captured.digest:
        raise MeasurementRefused(
            "ROUNDTRIP: the analysed stream is byte-identical to the emitted "
            "one (FNV %08x). This is the playback buffer, not a capture - "
            "correlating it against the emitted click correlates the click "
            "with itself." % emitted.digest)

    out = emitted.float[:, channel]
    back = captured.float[:, min(channel, captured.channels - 1)]
    count = max(len(out), len(back))
    left, right = np.zeros(count), np.zeros(count)
    left[:len(out)] = out - out.mean()
    right[:len(back)] = back - back.mean()
    norm = math.sqrt(float(np.sum(left ** 2)) * float(np.sum(right ** 2)))
    if norm <= 0.0:
        raise MeasurementRefused("ROUNDTRIP: nothing to correlate")
    correlation = np.correlate(right, left, mode="full")[count - 1:] / norm
    lag = int(np.argmax(correlation))
    peak = float(correlation[lag])

    if peak < correlation_floor:
        raise MeasurementRefused(
            "ROUNDTRIP: the correlation peak is %.3f, below the %.3f floor - "
            "nothing that was emitted came back. Is the loopback wire in?"
            % (peak, correlation_floor))
    if lag < int(block_frames):
        raise MeasurementRefused(
            "ROUNDTRIP: the correlation peak is at lag %d, inside one block "
            "(%d frames). A round trip cannot be shorter than the buffer it "
            "passes through - this is the playback buffer, not a capture."
            % (lag, int(block_frames)))

    values = {
        "lag_samples": lag,
        "round_trip_ms": round(1000.0 * lag / float(emitted.rate), 4),
        "correlation_peak": round(peak, 4),
        "block_frames": int(block_frames),
        "starvation_count": starvation_count,
        "settings": dict(settings or {}),
        "emitted_fnv1a": "%08x" % emitted.digest,
        "captured_fnv1a": "%08x" % captured.digest,
    }
    criteria = {"correlation_floor": correlation_floor,
                "lag_floor_frames": int(block_frames),
                "target_ms": target_ms}
    red, failed = [], []
    if target_ms is not None and values["round_trip_ms"] > float(target_ms):
        failed.append("round_trip_ms")
        red.append("round_trip_ms: %.3f ms against a target of %.3f"
                   % (values["round_trip_ms"], float(target_ms)))
    if starvation_count:
        failed.append("starvation_count")
        red.append("starvation_count: %d buffer-empty events during the run; "
                   "this setting starves" % int(starvation_count))
    values["failed_readouts"] = failed
    return _result("ROUNDTRIP", "ms", values, emitted.axes(), criteria, red)
