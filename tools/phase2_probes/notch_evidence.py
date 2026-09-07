"""Notch Station C: every number in `docs/effects/Notch-evidence.md`.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/notch_evidence.py

CPython only, with numpy, because the analysis is
(`docs/effects-kit-spec.md` section 1: the render is dual-runtime, the
analysis is not). The other two interpreters are reached through
`tools/render_effect.py`, whose digests the pack's section 3 carries --
byte-identical renders are what lets a Tier 1 row measured here stand for
all three.

Every Tier 2 trait is followed by a planted fault **of the same kind**: not
a different bug that happens to be red, but the specific thing the trait
denies. The clean run beside it is the control, because a battery with no
control only proves the checker always fails.

A note on settling, because the first version of this file got it wrong. A
notch's poles ring for about `2.2*Q/f0` seconds; at 60 Hz and Q 12 that is
440 ms, and a 0.35 s probe with a 0.15 s skip reads the transient rather
than the response (dossier A16, D3's two out-of-tolerance rows). Every
steady-tone read below sizes its own settling window from the section's own
Q and centre.
"""

import math
import os
import sys
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
sys.path.insert(0, ROOT)

import audiobiquad                                          # noqa: E402
import audiocore                                            # noqa: E402
import audiofilters                                         # noqa: E402
import numpy as np                                          # noqa: E402
import synthio                                              # noqa: E402
import kit_faults                                           # noqa: E402
from kit_probes import (ArraySource, SwitchableSource,       # noqa: E402
                        render, ramp_fs, quiet_chord,
                        click_stereo, noise_det)
from tools import effect_measurements as kit                # noqa: E402
from audioeffects.rebuilt.notch import Notch                # noqa: E402

#: The planted-fault subclasses below are `_component.Component`
#: subclasses, and the metadata check reads `VENDOR` off the module that
#: defines a class - so this file needs one exactly as a rebuilt module
#: does. It is a fixture module, not a provider: nothing here is in
#: `audioeffects.__all__`.
VENDOR = "PyDevices"

RATE = 48000
CHANNELS = 2
RATES = (48000, 44100, 22050)


# -------------------------------------------------------------- material --

def tone(hz, seconds, rate=RATE, channels=CHANNELS, peak=6000):
    frames = int(rate * seconds)
    data = array("h", bytes(2 * channels * frames))
    for index in range(frames):
        value = int(round(peak * math.sin(2.0 * math.pi * hz * index / rate)))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def burst_then_silence(hz, on_s, total_s, rate=RATE, peak=20000,
                       channels=CHANNELS):
    """The silence is inside the sample: a probe that lets the source *end*
    reads exact zeros for every build, clean or dirty (dossier A3)."""
    frames = int(rate * total_s)
    on = int(rate * on_s)
    data = array("h", bytes(2 * channels * frames))
    for index in range(on):
        value = int(round(peak * math.sin(2.0 * math.pi * hz * index / rate)))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data, on


def dc_then_zero(level, hold_s, total_s, rate=RATE, channels=CHANNELS):
    frames = int(rate * total_s)
    held = int(rate * hold_s)
    value = int(round(level * 32767))
    data = array("h", bytes(2 * channels * frames))
    for index in range(held):
        for channel in range(channels):
            data[index * channels + channel] = value
    return data, held


def settle_seconds(f0, q):
    """Long enough for the section's ring to be past -120 dB: the pole
    radius is sqrt((1-a)/(1+a)) with a = sin(w0)/2Q, so the envelope decays
    by e^-1 in about Q/(pi*f0) seconds."""
    return max(0.15, 9.0 * q / f0)


# ------------------------------------------------------------- rendering --

_DRY = {}


def dry_tone(hz, seconds, rate=RATE, channels=CHANNELS, peak=6000):
    key = (round(hz, 6), round(seconds, 6), rate, channels, peak)
    if key not in _DRY:
        data = tone(hz, seconds, rate, channels, peak)
        _DRY[key] = render(ArraySource(data, rate=rate, channels=channels),
                           int(rate * seconds), rate=rate, channels=channels,
                           probe="sine_%g" % hz)
    return _DRY[key]


def build(data, rate=RATE, channels=CHANNELS, macros=(), patch=None,
          cls=Notch, **options):
    source = ArraySource(data, rate=rate, channels=channels)
    effect = cls.create(source, rate, **options)
    if patch is not None:
        effect.program_change(patch)
    for index, value in macros:
        effect.set_macro(index, value)
    return effect


def run(data, frames, rate=RATE, channels=CHANNELS, probe=None, **kwargs):
    effect = build(data, rate=rate, channels=channels, **kwargs)
    try:
        audiocore.reset_buffer(effect.output)
        return render(effect.output, frames, rate=rate, channels=channels,
                      class_name="Notch", probe=probe,
                      class_version=Notch.VERSION,
                      latency_samples=effect.latency_samples)
    finally:
        effect.deinit()


def macro_code(index, value):
    """A setting in its own units as an unquantized MIDI code. `set_macro`
    takes floats, so the exact number asked for stays on the audio path."""
    from audioeffects._component import macro_position
    return macro_position(Notch._MACRO_RANGES[index], value) * 127.0


def settings(f0, q, harmonics=0, depth=1.0, trim_db=0.0):
    """The five macros as MIDI codes, unquantized (set_macro takes floats)."""
    return ((0, macro_code(0, f0)), (1, macro_code(1, q)),
            (2, 127.0 if harmonics else 0.0), (3, macro_code(3, depth)),
            (4, macro_code(4, trim_db)))


def gain_db(f0, q, probe_hz, rate=RATE, harmonics=0, depth=1.0, trim_db=0.0,
            cls=Notch, peak=6000, channels=CHANNELS):
    """Magnitude at `probe_hz`, single-bin DFT over the settled half of a
    tone that outlasts the section's own ring."""
    settle = settle_seconds(f0, q)
    seconds = settle * 2.0
    data = tone(probe_hz, seconds, rate, channels, peak)
    frames = int(rate * seconds)
    wet = run(data, frames, rate=rate, channels=channels, cls=cls,
              macros=settings(f0, q, harmonics, depth, trim_db),
              probe="sine_%g" % probe_hz)
    ref = dry_tone(probe_hz, seconds, rate, channels, peak)
    start = int(frames * 0.5)
    w = kit.tone_bin(wet.float[start:, 0], rate, probe_hz)
    d = kit.tone_bin(ref.float[start:, 0], rate, probe_hz)
    return kit.db(abs(w) / abs(d)) if abs(d) else float("nan")


def closed_form(probe_hz, f0, q, rate=RATE):
    """RBJ's notch, S1, evaluated at the running rate, in float64."""
    w0 = 2.0 * math.pi * f0 / rate
    alpha = math.sin(w0) / (2.0 * q)
    cw = math.cos(w0)
    b = (1.0, -2.0 * cw, 1.0)
    a = (1.0 + alpha, -2.0 * cw, 1.0 - alpha)
    z = complex(math.cos(-2.0 * math.pi * probe_hz / rate),
                math.sin(-2.0 * math.pi * probe_hz / rate))
    value = abs((b[0] + b[1] * z + b[2] * z * z)
                / (a[0] + a[1] * z + a[2] * z * z))
    return -240.0 if value <= 0.0 else 20.0 * math.log10(value)


def edges(f0, q):
    """S3/S1: the -3 dB points; their difference is exactly f0/q."""
    root = math.sqrt(1.0 + 1.0 / (4.0 * q * q))
    return f0 * (root - 1.0 / (2.0 * q)), f0 * (root + 1.0 / (2.0 * q))


def commensurate(f0, rate=RATE):
    """The nearest frequency to `f0` with a whole number of samples per
    cycle at `rate` - T1's probe, and the reason its clause is not a
    hedge."""
    period = max(2, int(round(rate / f0)))
    return rate / float(period)


# ------------------------------------------------------- planted faults ---

class DetunedZeros(Notch):
    """T1's fault: the zero pair moved off the probe's own frequency by
    0.1 %, which is what "the zeros sit exactly on the unit circle at
    +/-w0" denies. The DSP is otherwise this class's."""

    NAME = 'Notch'
    DETUNE = 1.001

    def _centre(self, hz):
        return Notch._centre(self, hz) * self.DETUNE


class BandPassNumerator(Notch):
    """T2's fault: the fundamental section built as a `BAND_PASS` instead
    of a `NOTCH`.

    That is precisely what T2's source says makes a notch unity outside its
    band - numerator and denominator summing alike at `z = +/-1`. RBJ's
    band-pass numerator `(alpha, 0, -alpha)` sums to zero at both, so DC and
    Nyquist stop passing while the class still reports itself a notch of the
    same f0 and Q.
    """

    NAME = 'Notch'

    def _build(self, *arguments, **keywords):
        Notch._build(self, *arguments, **keywords)
        self._fundamental.mode = audiobiquad.BAND_PASS


class NoCentreCeiling(Notch):
    """T2's fault: the centre ceiling removed, so Frequency reaches
    `_hz()`'s 0.49*Fs and the notch's own band covers T2's 0.48*Fs probe.
    This is the fault the ceiling exists to prevent."""

    NAME = 'Notch'

    def _centre(self, hz):
        return self._hz(hz)


class WidenedQ(Notch):
    """T3's fault: the section's Q is 1.5x the Width the class reports, so
    the -3 dB points stop sitting at f0*(sqrt(1+1/4Q^2) -+ 1/2Q)."""

    NAME = 'Notch'
    FACTOR = 1.5

    def _refresh(self):
        Notch._refresh(self)
        self._fundamental.Q = min(60.0, self._fundamental.Q * self.FACTOR)


class DepthIsWidth(Notch):
    """T5's fault: Depth implemented as a Q change rather than as a mix -
    literally the design error T5 forbids. The off-centre readings then stop
    matching the closed form at the reported Width."""

    NAME = 'Notch'

    def _refresh(self):
        Notch._refresh(self)
        depth = max(0.02, self._value(3))
        self._fundamental.Q = min(60.0, max(0.05,
                                            self._fundamental.Q * depth))
        self._fundamental.mix = 1.0


class RateBlind(Notch):
    """T6's fault: coefficients derived as if the graph always ran at
    48 kHz. At 48 kHz it is the shipped class; at 44.1 and 22.05 the centre
    lands somewhere else entirely."""

    NAME = 'Notch'

    def _centre(self, hz):
        return Notch._centre(self, hz * self._sample_rate / 48000.0)


class UnderReportedLatency(Notch):
    """CLICK's fault: `latency_samples` reported 256 short with the DSP
    untouched, so the audio digest does not move."""

    NAME = 'Notch'
    LATENCY_SAMPLES = 256


def ported_notch(source, f0, q, rate=RATE, channels=CHANNELS):
    """TAIL's fault: the same filter on the ported integer kernel, which is
    audioif#23 itself rather than a stand-in for it."""
    node = audiofilters.Filter(
        filter=synthio.Biquad(synthio.FilterMode.NOTCH, f0, Q=q), mix=1.0,
        sample_rate=rate, channel_count=channels, bits_per_sample=16,
        samples_signed=True, buffer_size=2048)
    node.play(source)
    return node


# ------------------------------------------------- 2. Tier 1 invariants ---

def tier1(rate=RATE, channels=CHANNELS):
    print("\n=== Tier 1, %d Hz, %d channel(s) ===" % (rate, channels))

    # WIRE - Depth 0, on ramp_fs, which is the probe the fault needs.
    ramp = ramp_fs(frames=8192, channels=channels)
    frames = len(ramp) // channels
    source = render(ArraySource(ramp, rate=rate, channels=channels), frames,
                    rate=rate, channels=channels, probe="ramp_fs")
    for label, macros in (("depth 0, patch 0 elsewhere",
                           settings(1000.0, 0.7071, 0, 0.0, 0.0)),
                          ("depth 0, hum 60 elsewhere",
                           settings(60.0, 12.0, 1, 0.0, 12.0))):
        wet = run(ramp, frames, rate=rate, channels=channels, macros=macros,
                  probe="ramp_fs")
        result = kit.wire(wet, source, latency_samples=0)
        print("  WIRE  %-26s %s  %d of %d samples differ  (fnv %s vs %s)"
              % (label, "pass" if result["passed"] else "FAIL",
                 result["values"]["differing_samples"],
                 result["values"]["compared_samples"],
                 result["values"]["render_fnv1a"],
                 result["values"]["source_fnv1a"]))

    # WIRE's planted fault, and its own control on quiet material.
    for probe_name, data in (("ramp_fs", ramp),
                             ("quiet_chord",
                              quiet_chord(seconds=0.17, rate=rate,
                                          channels=channels))):
        count = len(data) // channels
        clean = render(ArraySource(data, rate=rate, channels=channels),
                       count, rate=rate, channels=channels)
        faulted = render(
            kit_faults.OneLsbScale(ArraySource(data, rate=rate,
                                               channels=channels)),
            count, rate=rate, channels=channels)
        result = kit.wire(faulted, clean)
        print("  WIRE  planted 32767/32768 on %-12s -> %s, %d of %d differ"
              % (probe_name, "RED" if not result["passed"] else "green",
                 result["values"]["differing_samples"],
                 result["values"]["compared_samples"]))

    # TAIL - burst then silence inside the source, at the class's worst
    # reachable corner and at patch 0, plus the dc_step leg.
    for label, f0, q, harmonics in (("patch 0 (983 Hz Q 0.72)", 983.0, 0.717,
                                     0),
                                    ("hum 60, two notches", 60.4, 11.98, 1),
                                    ("20 Hz Q 32, two notches", 20.0, 32.0,
                                     1)):
        seconds = 6.0
        data, on = burst_then_silence(60.0, 0.2, seconds, rate=rate,
                                      peak=32767, channels=channels)
        wet = run(data, int(rate * seconds), rate=rate, channels=channels,
                  macros=settings(f0, q, harmonics, 1.0, 0.0),
                  probe="burst_silence")
        # The dc_step leg has to outlast the same ring the burst leg
        # does, or a 20 Hz Q 32 section reads red for the probe's length.
        dc_seconds = 0.5 + settle_seconds(f0, q) * 2.0 + 0.5
        dc, held = dc_then_zero(0.5, 0.5, dc_seconds, rate=rate,
                                channels=channels)
        dc_wet = run(dc, int(rate * dc_seconds), rate=rate,
                     channels=channels,
                     macros=settings(f0, q, harmonics, 1.0, 0.0),
                     probe="dc_step")
        result = kit.tail(wet, burst_end_frame=on,
                          declared_tail_samples=Notch.TAIL_SAMPLES,
                          dc_render=dc_wet, dc_removed_frame=held)
        values = result["values"]
        print("  TAIL  %-24s %s  tail %s samples (declared %d), residual "
              "%d LSB, dc residual %d LSB"
              % (label, "pass" if result["passed"] else "FAIL",
                 values["tail_samples"], Notch.TAIL_SAMPLES,
                 values["residual_lsb"], values.get("dc_residual_lsb", 0)))

    # TAIL's planted fault: the same filter on the ported integer kernel.
    seconds = 6.0
    data, on = burst_then_silence(440.0, 0.09, seconds, rate=rate,
                                  peak=12000, channels=channels)
    ported = ported_notch(ArraySource(data, rate=rate, channels=channels),
                          60.0, 8.0, rate=rate, channels=channels)
    faulted = render(ported, int(rate * seconds), rate=rate,
                     channels=channels)
    result = kit.tail(faulted, burst_end_frame=on)
    print("  TAIL  planted audioif#23 (synthio.Biquad 60 Hz q=8) -> %s, "
          "residual %d LSB, tail %s"
          % ("RED" if not result["passed"] else "green",
             result["values"]["residual_lsb"],
             result["values"]["tail_samples"]))

    # LEVEL - unity through the class at its unity setting.
    #
    # The probe matters here and the first draft of this file got it wrong.
    # A notch's job is to remove a band, so broadband noise through it at
    # Depth 1 reads *down* by however much of the band it took: 8 kHz at
    # Q 30 is 267 Hz of a 24 kHz spectrum, and the reading is -0.065 dB,
    # which is the class working and not a hidden gain. LEVEL's subject is
    # the path, so the Depth 1 leg uses a tone outside the band; the noise
    # leg is reported beside it with its own explanation.
    noise = noise_det(frames=16384, channels=channels)
    count = len(noise) // channels
    reference = render(ArraySource(noise, rate=rate, channels=channels),
                       count, rate=rate, channels=channels)
    centre = min(8000.0, rate * 0.35)
    wet = run(noise, count, rate=rate, channels=channels,
              macros=settings(1000.0, 0.7071, 0, 0.0, 0.0),
              probe="noise_det")
    result = kit.level(wet, reference, tolerance_db=0.05)
    print("  LEVEL %-30s %s  worst %+0.4f dB"
          % ("depth 0, noise_det", "pass" if result["passed"] else "FAIL",
             max(result["values"]["rms_db"], key=abs)))

    seconds = settle_seconds(centre, 30.0) * 2.0
    outside = tone(1000.0, seconds, rate, channels, 6000)
    frames = int(rate * seconds)
    wet = run(outside, frames, rate=rate, channels=channels,
              macros=settings(centre, 30.0, 0, 1.0, 0.0), probe="sine_1k")
    result = kit.level(wet, dry_tone(1000.0, seconds, rate, channels, 6000),
                       tolerance_db=0.05,
                       skip_frames=int(rate * settle_seconds(centre, 30.0)))
    print("  LEVEL %-30s %s  worst %+0.4f dB"
          % ("depth 1, 1 kHz tone, notch %.0f Hz Q 30" % centre,
             "pass" if result["passed"] else "FAIL",
             max(result["values"]["rms_db"], key=abs)))

    wet = run(noise, count, rate=rate, channels=channels,
              macros=settings(centre, 30.0, 0, 1.0, 0.0), probe="noise_det")
    result = kit.level(wet, reference, tolerance_db=0.05)
    print("  LEVEL %-30s %s  %+0.4f dB - the band it removed, not a gain"
          % ("depth 1, noise_det (note)",
             "reads down" if not result["passed"] else "pass",
             max(result["values"]["rms_db"], key=abs)))

    faulted = render(kit_faults.HiddenGain(
        ArraySource(noise, rate=rate, channels=channels), gain_db=0.1),
        count, rate=rate, channels=channels)
    result = kit.level(faulted, reference, tolerance_db=0.05)
    print("  LEVEL planted +0.1 dB hidden gain -> %s, %+0.4f dB"
          % ("RED" if not result["passed"] else "green",
             max(result["values"]["rms_db"], key=abs)))

    # CLICK - reported latency against measured, and the under-report.
    clicks = click_stereo(frames=8192, offset=1024, channels=channels)
    count = len(clicks) // channels
    dry = render(ArraySource(clicks, rate=rate, channels=channels), count,
                 rate=rate, channels=channels, probe="click_stereo")
    for label, cls, reported in (("shipped", Notch, 0),
                                 ("planted 256 short",
                                  UnderReportedLatency, 256)):
        wet = run(clicks, count, rate=rate, channels=channels, cls=cls,
                  macros=settings(1000.0, 0.717, 0, 1.0, 0.0),
                  probe="click_stereo")
        result = kit.click(wet, dry, reported, subsample=False)
        print("  CLICK %-18s %s  measured %s against reported %d  "
              "(digest %s)"
              % (label,
                 "pass" if result["passed"] else "RED",
                 result["values"]["measured_latency_samples"], reported,
                 result["values"]["render_fnv1a"]))

    # STATE - reset, deinit, capabilities, allocation.
    burst, _ = burst_then_silence(1000.0, 0.2, 1.0, rate=rate, peak=20000,
                                  channels=channels)
    inner = ArraySource(burst, rate=rate, channels=channels)
    silent = ArraySource(array("h", bytes(2 * channels * 48000)), rate=rate,
                         channels=channels)
    holder = SwitchableSource(inner)
    effect = Notch.create(holder, rate)
    effect.program_change(2)

    def pull(blocks):
        return render(effect.output, blocks * 256, rate=rate,
                      channels=channels)

    named = [("fundamental", effect._fundamental),
             ("harmonic", effect._harmonic), ("trim", effect._trim)]
    result = kit.state(effect, pull=pull, swap=holder.swap,
                       probe_source=inner, silent_source=silent,
                       nodes=named)
    values = result["values"]
    print("  STATE %s  reset residual %d LSB, resumed %s, nodes live after "
          "deinit %s, alloc %s bytes over 200 pulls, capabilities %s"
          % ("pass" if result["passed"] else "FAIL",
             values["reset_residual_lsb"], values["resumed"],
             values["live_nodes_after_deinit"] or "none",
             values["alloc_growth_bytes"], values["capabilities"]))
    if not result["passed"]:
        print("        red: %s" % result["red"])


# ------------------------------------------------ 1. Tier 2 circuit traits --

def t1_total_rejection(rate=RATE):
    print("\n=== T1  total rejection at the centre (%d Hz) ===" % rate)
    print("  commensurate on-centre probes; 'peak |y|' is over the settled")
    print("  half, level 6000, so 0 is the bit-exact zero the trait claims")
    for f0 in (60.0, 250.0, 1000.0, 4000.0):
        for q in (0.707, 2.0, 12.0, 32.0):
            probe = commensurate(f0, rate)
            settle = settle_seconds(probe, q)
            seconds = settle * 2.0
            frames = int(rate * seconds)
            wet = run(tone(probe, seconds, rate, CHANNELS, 6000), frames,
                      rate=rate, macros=settings(probe, q, 0, 1.0, 0.0),
                      probe="sine_%g" % probe)
            settled = wet.data[int(frames * 0.5):]
            peak = int(np.abs(settled).max())
            print("    f0=%-8.2f Q=%-6.3f samples/cycle %7.2f  peak |y| "
                  "%6d  %s"
                  % (probe, q, rate / probe, peak,
                     "bit-exact zero" if peak == 0
                     else "%.2f dB" % kit.db(peak / 6000.0)))
    print("  off-centre, f0*1.0005 at Q 2, against the closed form:")
    for f0 in (1000.0, 4000.0):
        probe = f0 * 1.0005
        got = gain_db(f0, 2.0, probe, rate=rate)
        ideal = closed_form(probe, f0, 2.0, rate)
        print("    f0=%-8.1f probe %10.3f Hz  measured %8.3f dB  ideal "
              "%8.3f dB  dev %+6.3f  (bar +/-0.5)" % (f0, probe, got, ideal,
                                                      got - ideal))
    print("  planted fault - the zeros moved 0.1 %% off the probe:")
    for f0, q in ((1000.0, 2.0), (4000.0, 12.0)):
        probe = commensurate(f0, rate)
        settle = settle_seconds(probe, q)
        seconds = settle * 2.0
        frames = int(rate * seconds)
        for label, cls in (("clean", Notch), ("detuned", DetunedZeros)):
            wet = run(tone(probe, seconds, rate, CHANNELS, 6000), frames,
                      rate=rate, cls=cls,
                      macros=settings(probe, q, 0, 1.0, 0.0))
            peak = int(np.abs(wet.data[int(frames * 0.5):]).max())
            print("    f0=%-8.2f Q=%-5.1f %-8s peak |y| %6d -> %s"
                  % (probe, q, label, peak,
                     "green (bit-exact zero)" if peak == 0 else "RED"))


def t2_unity_outside(rate=RATE):
    print("\n=== T2  unity outside the band (%d Hz) ===" % rate)
    # The dossier's own Measurement cell for this row: "DC step settled
    # value; a +/-FS alternating sequence; a swept sine's endpoints". The
    # first two are *exactly* DC and exactly Nyquist, which is where the
    # numerator and the denominator sum alike; the third is a tone at
    # 0.48*Fs, which is near Nyquist and not at it. Both are run, because
    # they answer different questions and the seed asks for both.
    print("  DC step (settled) and +/-FS alternating (Nyquist), the two")
    print("  probes the trait's own measurement cell names:")
    for f0, q in ((60.0, 0.5), (60.0, 12.0), (1000.0, 2.0),
                  (min(16000.0, rate * 0.4), 0.5)):
        held = int(0.5 * 32767)
        # A step and a Nyquist square both strike the notch hard, so the
        # settling window here is twice the steady-tone one and the read is
        # the last 5 %% rather than the last quarter.
        frames = int(rate * (settle_seconds(f0, q) * 4.0))
        step = array("h", bytes(2 * CHANNELS * frames))
        for index in range(frames):
            for channel in range(CHANNELS):
                step[index * CHANNELS + channel] = held
        wet = run(step, frames, rate=rate,
                  macros=settings(f0, q, 0, 1.0, 0.0), probe="dc_step")
        settled = int(np.median(wet.data[int(frames * 0.95):]))
        alternating = array("h", bytes(2 * CHANNELS * frames))
        for index in range(frames):
            value = 32767 if index % 2 == 0 else -32767
            for channel in range(CHANNELS):
                alternating[index * CHANNELS + channel] = value
        wet = run(alternating, frames, rate=rate,
                  macros=settings(f0, q, 0, 1.0, 0.0), probe="alt_fs")
        # int64 before abs: `abs(-32768)` is -32768 in int16, and the
        # clamp at `audioif_filter_f32.c:47-48` really does emit -32768, so an
        # int16 mean of the magnitudes reads about zero on a filter passing
        # full scale.
        tail_block = wet.data[int(frames * 0.95):].astype(np.int64)
        nyquist = float(np.abs(tail_block).mean())
        print("    f0=%-9.1f Q=%-6.2f  DC in %6d out %6d (%+0.4f dB)   "
              "Nyquist |y| %9.2f of 32767 (%+0.4f dB)"
              % (f0, q, held, settled,
                 kit.db(abs(settled) / float(held)) if settled else -240.0,
                 nyquist, kit.db(nyquist / 32767.0)))
    print("  tones at 10 Hz and 0.48*Fs, which are near those two and not")
    print("  at them - so a wide band reaches them:")
    top = min(16000.0, rate * 0.4)
    for f0 in (60.0, 1000.0, top):
        for q in (0.5, 2.0, 32.0):
            low = gain_db(f0, q, 10.0, rate=rate)
            high = gain_db(f0, q, rate * 0.48, rate=rate)
            verdict = "pass" if max(abs(low), abs(high)) <= 0.1 else "FAIL"
            print("    f0=%-9.1f Q=%-6.2f  10 Hz %+8.4f dB   0.48*Fs "
                  "(%8.1f Hz) %+8.4f dB   %s"
                  % (f0, q, low, rate * 0.48, high, verdict))
    print("  planted fault - the numerator that no longer sums like the")
    print("  denominator at z = +/-1 (the section built as a BAND_PASS):")
    for cls, label in ((Notch, "clean"), (BandPassNumerator, "faulted")):
        low = gain_db(1000.0, 2.0, 10.0, rate=rate, cls=cls)
        high = gain_db(1000.0, 2.0, rate * 0.48, rate=rate, cls=cls)
        print("    f0=1000 Q=2  %-9s 10 Hz %+9.3f dB   0.48*Fs %+9.3f dB "
              "-> %s" % (label, low, high,
                         "green" if max(abs(low), abs(high)) <= 0.1
                         else "RED"))
    # A second plant on the same trait, recorded with its control's own
    # status stated. The 0.4*Fs centre ceiling only *acts* where the
    # Frequency span's top (16 kHz) is above it, which is 22.05 kHz alone;
    # and it only moves the reading at the bottom of the Width span, where
    # the clean build already misses T2's own bar (the 16 kHz Q 0.5 row
    # above). So this pair shows what the ceiling buys and is *not* cited
    # as T2's planted fault - its control is not green.
    print("  second plant, control not green - the 0.4*Fs ceiling removed "
          "at 22 050 Hz:")
    for cls, label in ((Notch, "clean (8820 Hz)"),
                       (NoCentreCeiling, "faulted (10804.5 Hz)")):
        got = gain_db(16000.0, 0.5, 22050 * 0.48, rate=22050, cls=cls)
        print("    asked for 16 000 Hz Q 0.5  %-24s 0.48*Fs %+8.4f dB"
              % (label, got))


def t3_width(rate=RATE):
    print("\n=== T3  width is f0/Q (%d Hz) ===" % rate)
    for f0, q in ((1000.0, 2.0), (1000.0, 8.0), (250.0, 0.5), (4000.0, 32.0)):
        low, high = edges(f0, q)
        got_low = gain_db(f0, q, low, rate=rate)
        got_high = gain_db(f0, q, high, rate=rate)
        worst = max(abs(got_low + 3.0), abs(got_high + 3.0))
        # The closed form at the same two frequencies, so a row that misses
        # -3.0 says whether the *class* or the *analog edge formula* is
        # what missed it: the bilinear transform warps the axis, so the
        # analog prediction stops landing on -3 dB as f0 climbs.
        ideal_low = closed_form(low, f0, q, rate)
        ideal_high = closed_form(high, f0, q, rate)
        print("    f0=%-8.1f Q=%-6.2f edges %9.2f / %9.2f Hz (width %8.2f "
              "= f0/Q %8.2f)  measured %7.3f / %7.3f dB  closed form "
              "%7.3f / %7.3f  %s"
              % (f0, q, low, high, high - low, f0 / q, got_low, got_high,
                 ideal_low, ideal_high,
                 "pass" if worst <= 0.15 else "FAIL"))
    print("  planted fault - the section's Q is 1.5x the reported Width:")
    f0, q = 1000.0, 2.0
    low, high = edges(f0, q)
    for cls, label in ((Notch, "clean"), (WidenedQ, "faulted")):
        got_low = gain_db(f0, q, low, rate=rate, cls=cls)
        got_high = gain_db(f0, q, high, rate=rate, cls=cls)
        worst = max(abs(got_low + 3.0), abs(got_high + 3.0))
        print("    %-10s edges read %7.3f / %7.3f dB -> %s"
              % (label, got_low, got_high,
                 "green" if worst <= 0.15 else "RED"))


def _sum_with_bandpass(f0, q, probe_hz, rate=RATE, detune=1.0):
    """T4's measurement: this class's output plus a band-pass of the same
    f0 and Q, summed in float64 - an int16 sum would measure the mixer's
    rounding rather than the identity."""
    settle = settle_seconds(f0, q)
    seconds = settle * 2.0
    frames = int(rate * seconds)
    data = tone(probe_hz, seconds, rate, CHANNELS, 6000)
    wet = run(data, frames, rate=rate, macros=settings(f0, q, 0, 1.0, 0.0),
              probe="sine_%g" % probe_hz)
    band = audiobiquad.Biquad(mode=audiobiquad.BAND_PASS,
                              frequency=f0 * detune, Q=q, mix=1.0,
                              sample_rate=rate, channel_count=CHANNELS)
    band.play(ArraySource(data, rate=rate, channels=CHANNELS))
    other = render(band, frames, rate=rate, channels=CHANNELS)
    reference = dry_tone(probe_hz, seconds, rate, CHANNELS, 6000)
    start = int(frames * 0.5)
    total = wet.float[start:, 0] + other.float[start:, 0]
    reconstructed = kit.tone_bin(total, rate, probe_hz)
    original = kit.tone_bin(reference.float[start:, 0], rate, probe_hz)
    return kit.db(abs(reconstructed) / abs(original))


def t4_identity(rate=RATE):
    print("\n=== T4  notch + band-pass = 1 (%d Hz) ===" % rate)
    f0, q = 3000.0, 2.0
    worst = 0.0
    for probe in (20.0, 100.0, 500.0, 1500.0, 3000.0, 6000.0,
                  min(12000.0, rate * 0.4)):
        got = _sum_with_bandpass(f0, q, probe, rate=rate)
        worst = max(worst, abs(got))
        print("    probe %9.1f Hz  reconstruction %+8.4f dB" % (probe, got))
    print("    worst %+0.4f dB over 20 Hz .. 0.4*Fs -> %s (bar 0.05)"
          % (worst, "pass" if worst <= 0.05 else "FAIL"))
    print("  planted fault - the band-pass branch detuned by 1 %%:")
    for detune, label in ((1.0, "clean"), (1.01, "faulted")):
        got = max(abs(_sum_with_bandpass(f0, q, probe, rate=rate,
                                         detune=detune))
                  for probe in (2800.0, 3000.0, 3200.0))
        print("    %-9s worst near f0 %+8.4f dB -> %s"
              % (label, got, "green" if got <= 0.05 else "RED"))


def t5_depth_is_a_mix(rate=RATE):
    print("\n=== T5  depth is a mix, not a width (%d Hz) ===" % rate)
    f0 = 1000.0
    print("  on-centre, commensurate, across Q - T1's column, repeated:")
    for q in (0.5, 2.0, 8.0, 32.0):
        probe = commensurate(f0, rate)
        settle = settle_seconds(probe, q)
        seconds = settle * 2.0
        frames = int(rate * seconds)
        wet = run(tone(probe, seconds, rate, CHANNELS, 6000), frames,
                  rate=rate, macros=settings(probe, q, 0, 1.0, 0.0))
        peak = int(np.abs(wet.data[int(frames * 0.5):]).max())
        print("    Q=%-6.2f peak |y| %6d  %s"
              % (q, peak, "bit-exact zero" if peak == 0 else "NOT zero"))
    print("  off-centre at f0*1.0005, each against its OWN closed form:")
    spread = []
    for q in (0.5, 2.0, 8.0, 32.0):
        probe = f0 * 1.0005
        got = gain_db(f0, q, probe, rate=rate)
        ideal = closed_form(probe, f0, q, rate)
        spread.append(got)
        print("    Q=%-6.2f measured %8.3f dB  ideal %8.3f dB  dev %+6.3f  "
              "%s" % (q, got, ideal, got - ideal,
                      "pass" if abs(got - ideal) <= 0.5 else "FAIL"))
    print("    spread on one fixed probe across Q: %.2f dB (the trait says "
          "a depth reading beside f0 is a width reading)"
          % (max(spread) - min(spread)))
    print("  the depth law: gain at f0 should be 1 - mix")
    for depth in (0.0, 0.25, 0.5, 1.0):
        probe = f0 * 1.0005
        got = gain_db(f0, 2.0, probe, rate=rate, depth=depth)
        blended = closed_form(probe, f0, 2.0, rate)
        mixed = abs((1.0 - depth) + depth * (10.0 ** (blended / 20.0)))
        print("    depth %4.2f  measured %8.3f dB  1-mix prediction %8.3f dB"
              % (depth, got, kit.db(mixed)))
    print("  planted fault - Depth implemented as a Q change:")
    for cls, label in ((Notch, "clean"), (DepthIsWidth, "faulted")):
        worst = 0.0
        for q in (0.5, 2.0, 8.0, 32.0):
            probe = f0 * 1.0005
            got = gain_db(f0, q, probe, rate=rate, depth=0.5, cls=cls)
            ideal = closed_form(probe, f0, q, rate)
            blended = abs(0.5 + 0.5 * (10.0 ** (ideal / 20.0)))
            worst = max(worst, abs(got - kit.db(blended)))
        print("    %-9s worst deviation from the 1-mix prediction %6.3f dB "
              "-> %s" % (label, worst, "green" if worst <= 0.5 else "RED"))


def measured_centre(f0, q, rate=RATE, cls=Notch, span=0.4, steps=11):
    """The centre, located as the geometric mean of the two -3 dB
    crossings rather than as the minimum of a scan.

    The minimum is not usable as a locator on this class: at 60 Hz Q 12 the
    floor is -35 dB and flat over a wide neighbourhood, so a scan's
    "minimum" is the floor's shape and not the centre. S3 defines the
    centre against the bandwidth, and the two crossings bracket it.
    """
    ideal_low, ideal_high = edges(f0, q)

    def at(hz):
        return gain_db(f0, q, hz, rate=rate, cls=cls)

    # Lower edge: gain falls from 0 dB toward the centre, so bisect on
    # [well below, f0]. Upper edge: it rises again, so bisect on
    # [f0, well above].
    low, high = ideal_low * (1.0 - span), f0
    for _ in range(steps):
        middle = math.sqrt(low * high)
        if at(middle) > -3.0:
            low = middle
        else:
            high = middle
    lower = math.sqrt(low * high)

    low, high = f0, min(ideal_high * (1.0 + span), rate * 0.45)
    for _ in range(steps):
        middle = math.sqrt(low * high)
        if at(middle) < -3.0:
            low = middle
        else:
            high = middle
    upper = math.sqrt(low * high)
    return math.sqrt(lower * upper), (lower, upper)


def coefficient_expectation(f0, q, probe_hz, rate=RATE):
    """|H(probe)| from the shipped `float` coefficients the class's own
    section carries - the arithmetic actually running, not the algebra."""
    node = audiobiquad.Biquad(mode=audiobiquad.NOTCH, frequency=f0, Q=q,
                              sample_rate=rate, channel_count=CHANNELS)
    b0, b1, b2, a1, a2 = node.coefficients
    w = 2.0 * math.pi * probe_hz / rate
    z = complex(math.cos(-w), math.sin(-w))
    value = abs((b0 + b1 * z + b2 * z * z) / (1.0 + a1 * z + a2 * z * z))
    return -240.0 if value <= 0.0 else 20.0 * math.log10(value)


def t6_rate_honest():
    print("\n=== T6  rate-honest, against the closed form at each rate ===")
    for rate in RATES:
        worst_curve, worst_where = 0.0, None
        for f0, q in ((60.0, 12.0), (1000.0, 2.0),
                      (min(4000.0, rate * 0.3), 8.0)):
            low, high = edges(f0, q)
            for probe in (10.0, f0 * 0.5, low, high, f0 * 2.0,
                          rate * 0.45 * 0.99):
                if probe >= rate * 0.45 or probe < 5.0:
                    continue
                got = gain_db(f0, q, probe, rate=rate)
                ideal = closed_form(probe, f0, q, rate)
                if abs(got - ideal) > worst_curve:
                    worst_curve = abs(got - ideal)
                    worst_where = (f0, q, probe, got, ideal)
        expected = coefficient_expectation(worst_where[0], worst_where[1],
                                           worst_where[2], rate)
        centre, crossings = measured_centre(1000.0, 8.0, rate=rate)
        displaced = abs(centre - 1000.0) / 1000.0 * 100.0
        print("    %6d Hz  worst |measured - closed form| %6.3f dB (bar "
              "0.1) at f0=%.0f Q=%.1f probe %.1f Hz (%+.3f against %+.3f)"
              % (rate, worst_curve, worst_where[0], worst_where[1],
                 worst_where[2], worst_where[3], worst_where[4]))
        print("             the same point from the shipped float "
              "coefficients: %+.3f dB, so the gap is the coefficient set "
              "(%.3f dB left over)"
              % (expected, abs(worst_where[3] - expected)))
        print("             curve clause %s;  centre of the 1 kHz Q 8 "
              "notch found at %9.4f Hz from crossings %9.3f / %9.3f -> "
              "%6.4f %% out (bar 0.1) %s"
              % ("pass" if worst_curve <= 0.1 else "FAIL",
                 centre, crossings[0], crossings[1], displaced,
                 "pass" if displaced <= 0.1 else "FAIL"))
    print("  planted fault - coefficients derived as if always 48 kHz.")
    print("  At 48 kHz the faulted class *is* the shipped one, which is the")
    print("  control: a rate bug that fires at every rate would not be a")
    print("  rate bug.")
    # Read as the rejection at the frequency the class was *asked* for: a
    # bisection on the -3 dB crossings assumes the notch is near where it
    # was asked for, which is the thing this fault breaks, so it would
    # bracket a crossing that is not the notch's.
    for rate in (48000, 22050):
        for cls, label in ((Notch, "clean"), (RateBlind, "faulted")):
            probe = commensurate(1000.0, rate)
            got = gain_db(probe, 8.0, probe, rate=rate, cls=cls)
            print("    %6d Hz  %-9s rejection at the %8.3f Hz it was asked "
                  "for: %8.2f dB -> %s"
                  % (rate, label, probe, got,
                     "green" if got <= -40.0 else "RED"))


# --------------------------------------- 3. digests, and the block ladder --

def digest_ladder(rate=RATE, channels=CHANNELS):
    print("\n=== source block-size ladder (%d Hz, %d ch) ===" % (rate,
                                                                channels))
    print("  the same class and settings at five source block sizes; the")
    print("  spec's fourth axis, and the one that renders the split family")
    print("  silent when it is ignored")
    material = noise_det(frames=32768, channels=channels)
    frames = 32768
    renders = {}
    for block in (256, 8192, 16384, 20000, 32768):
        source = ArraySource(material, rate=rate, channels=channels,
                             block=block)
        effect = Notch.create(source, rate)
        effect.program_change(2)
        try:
            audiocore.reset_buffer(effect.output)
            renders["block %d" % block] = render(
                effect.output, frames, rate=rate, channels=channels,
                block=block, class_name="Notch", probe="noise_det")
        finally:
            effect.deinit()
    result = kit.digest(renders, mode="identical")
    for label in renders:
        print("    %-14s fnv %s  sum %d"
              % (label, "%08x" % renders[label].digest,
                 renders[label].byte_sum))
    print("    identical across the ladder: %s"
          % ("yes" if result["passed"] else "NO -- %s" % result["red"]))
    payload, raised, lowered = kit_faults.corrupt_one_block(
        renders["block 256"].pcm, channels=channels)
    corrupted = kit.Render(payload, rate, channels, block=256,
                           interpreter="cpython")
    print("    planted fault (+256 LSB at byte %d and -1 LSB at byte %d): "
          "fnv %08x against %08x -> %s;  byte sum %d against %d, moves by "
          "%d" % (raised, lowered, corrupted.digest,
                  renders["block 256"].digest,
                  "RED" if corrupted.digest != renders["block 256"].digest
                  else "green", corrupted.byte_sum,
                  renders["block 256"].byte_sum,
                  corrupted.byte_sum - renders["block 256"].byte_sum))


# ----------------------------------------------------- 5. latency, 6. mono --

def latency():
    print("\n=== 5. latency, reported against measured ===")
    for rate in (48000, 44100):
        for patch in range(6):
            clicks = click_stereo(frames=8192, offset=1024, channels=2)
            count = len(clicks) // 2
            dry = render(ArraySource(clicks, rate=rate, channels=2), count,
                         rate=rate, channels=2)
            wet = run(clicks, count, rate=rate, channels=2, patch=patch,
                      probe="click_stereo")
            result = kit.click(wet, dry, Notch.LATENCY_SAMPLES,
                               subsample=False)
            print("    %6d Hz  patch %d %-16s measured %s  reported %d  "
                  "%.4f ms  %s"
                  % (rate, patch, Notch.PATCHES[patch][0],
                     result["values"]["measured_latency_samples"],
                     Notch.LATENCY_SAMPLES,
                     result["values"]["measured_latency_ms"][0],
                     "pass" if result["passed"] else "FAIL"))


def mono():
    print("\n=== mono: the same filter on one channel ===")
    for rate in RATES:
        stereo_db = gain_db(1000.0, 8.0, 1000.0 * 1.0005, rate=rate,
                            channels=2)
        mono_db = gain_db(1000.0, 8.0, 1000.0 * 1.0005, rate=rate,
                          channels=1)
        print("    %6d Hz  f0*1.0005 at Q 8: stereo %8.3f dB, mono %8.3f "
              "dB, difference %+0.4f dB"
              % (rate, stereo_db, mono_db, mono_db - stereo_db))


def cost_anchor(rate=RATE, blocks=180, repeats=5):
    """An attempt at a desktop anchor, kept because its **spread** is the
    finding.

    Tier 3 is a board measurement (`tools/measure_effect_cost.py`). This
    tries the same arithmetic on the CPython target, and on this machine it
    does not produce a repeatable number: the same setting, same protocol,
    reads anywhere from about 110 to about 560 ns per stereo frame across
    invocations, because most of what is being timed is the twin's
    per-chunk Python work and the host's own scheduling, not the kernel a
    board would run. It prints every repeat rather than the minimum, so the
    spread is visible and nobody quotes the lucky one.
    """
    import gc
    import time
    print("\n=== Tier 3 desktop anchor (not the board run) ===")
    print("  real-time budget per stereo frame at %d Hz: %.1f ns"
          % (rate, 1e9 / rate))
    material = noise_det(frames=rate, channels=CHANNELS)

    def timed(patch, depth=None):
        source = ArraySource(material, rate=rate, channels=CHANNELS,
                             block=256)
        effect = Notch.create(source, rate)
        effect.program_change(patch)
        if depth is not None:
            effect.set_macro(3, depth * 127.0)
        audiocore.reset_buffer(effect.output)
        for _ in range(20):
            audiocore.get_buffer(effect.output)
        gc.collect()
        frames = 0
        start = time.perf_counter()
        for _ in range(blocks):
            _, data = audiocore.get_buffer(effect.output)
            frames += len(bytes(data)) // (2 * CHANNELS)
        wall = time.perf_counter() - start
        effect.deinit()
        return wall / frames * 1e9

    for patch, depth, label in ((0, None, "patch 0, one notch"),
                                (2, None, "patch 2, two notches"),
                                (2, 0.0, "patch 2 at Depth 0 (a wire)")):
        runs = sorted(timed(patch, depth) for _ in range(repeats))
        print("    %-30s min %7.1f  median %7.1f  max %7.1f ns/frame"
              % (label, runs[0], runs[len(runs) // 2], runs[-1]))
    source = ArraySource(material, rate=rate, channels=CHANNELS, block=256)
    audiocore.reset_buffer(source)
    for _ in range(20):
        audiocore.get_buffer(source)
    gc.collect()
    frames = 0
    start = time.perf_counter()
    for _ in range(blocks):
        _, data = audiocore.get_buffer(source)
        frames += len(bytes(data)) // (2 * CHANNELS)
    wall = time.perf_counter() - start
    print("    %-30s %8.1f ns/frame  (the pull loop and the source alone)"
          % ("bare source", wall / frames * 1e9))
    print("  Read the spread, not the minimum: this protocol is not")
    print("  repeatable on this machine, so no number above is quoted as")
    print("  an anchor. What does not depend on the timing is that all")
    print("  three sections are processed at every setting - the kernel")
    print("  runs the recursion and *then* blends, with no branch on `mix`")
    print("  (`audioif/src/shared/audioif_filter_f32.c:229-239`, reached on")
    print("  the CPython target through `_audioif.c:1205-1224`, which calls")
    print("  the same shared function). So `mix` 0 costs what `mix` 1 costs")
    print("  and one notch costs what two cost, and the dossier's split")
    print("  budget cannot be met one half at a time.")


def main():
    for rate in RATES:
        for channels in (2, 1):
            tier1(rate, channels)
    t1_total_rejection()
    t2_unity_outside()
    t3_width()
    t4_identity()
    t5_depth_is_a_mix()
    t6_rate_honest()
    digest_ladder()
    latency()
    mono()
    cost_anchor()


if __name__ == "__main__":
    main()
